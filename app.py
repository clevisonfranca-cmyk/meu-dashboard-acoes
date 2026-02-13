import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Scanner Fundamentus Pro", layout="wide")

st.title("📊 Scanner Automático - Fundamentus")

def limpar_valor(valor):
    if pd.isna(valor): return 0.0
    s = str(valor).replace('%', '').replace('.', '').replace(',', '.')
    try: return float(s)
    except: return 0.0

@st.cache_data(ttl=3600)
def carregar_dados_fundamentus():
    url = "https://fundamentus.com.br/resultado.php"
    header = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=header)
    df = pd.read_html(r.text, decimal=',', thousands='.')[0]
    
    novas_colunas = {
        df.columns[0]: 'Papel', df.columns[1]: 'PL', df.columns[2]: 'PVP',
        df.columns[10]: 'ROE', df.columns[11]: 'ROIC', df.columns[12]: 'DIV_PATRIM',
        df.columns[14]: 'LIQUIDEZ', df.columns[15]: 'CRESCIMENTO'
    }
    df = df.rename(columns=novas_colunas)
    
    cols_para_limpar = ['PL', 'PVP', 'ROE', 'ROIC', 'DIV_PATRIM', 'LIQUIDEZ', 'CRESCIMENTO']
    for col in cols_para_limpar:
        df[col] = df[col].apply(limpar_valor)
            
    return df

# --- INTERFACE LATERAL ---
st.sidebar.header("⚙️ Ajuste os Filtros")
f_pl_max = st.sidebar.number_input("P/L Máximo", value=15.0)
f_roic_min = st.sidebar.number_input("ROIC Mínimo (%)", value=10.0)
f_roe_min = st.sidebar.number_input("ROE Mínimo (%)", value=10.0)
f_liq_min = st.sidebar.number_input("Liq. Diária Mínima (R$)", value=500000.0)
f_div_max = st.sidebar.slider("Dív. Bruta/Patrimônio Máxima", 0.0, 5.0, 1.0)
f_cresc_min = st.sidebar.number_input("Crescimento 5a Mín (%)", value=1.0)
f_cresc_max = st.sidebar.number_input("Crescimento 5a Máx (%)", value=20.0)
f_graham_max = st.sidebar.number_input("Graham (P/L * P/VP) Máximo", value=22.5)

try:
    # 1. Carregar
    df = carregar_dados_fundamentus()
    
    # 2. Filtrar Passo a Passo (Evita o erro de Ambiguidade)
    df = df[df['PL'] > 0]
    df = df[df['PL'] <= f_pl_max]
    df = df[df['ROIC'] >= f_roic_min]
    df = df[df['ROE'] >= f_roe_min]
    df = df[df['LIQUIDEZ'] >= f_liq_min]
    df = df[df['DIV_PATRIM'] >= 0]
    df = df[df['DIV_PATRIM'] <= f_div_max]
    df = df[df['CRESCIMENTO'] >= f_cresc_min]
    df = df[df['CRESCIMENTO'] <= f_cresc_max]
    
    # 3. Calcular Graham e filtrar final
    df['Graham'] = df['PL'] * df['PVP']
    df = df[df['Graham'] <= f_graham_max]

    # --- EXIBIÇÃO ---
    df_final = df.sort_values('Graham').copy()
    st.success(f"Busca finalizada! {len(df_final)} ações encontradas.")
    
    if not df_final.empty:
        colunas_exibicao = ['Papel', 'PL', 'PVP', 'ROE', 'ROIC', 'DIV_PATRIM', 'LIQUIDEZ', 'CRESCIMENTO', 'Graham']
        st.dataframe(df_final[colunas_exibicao].style.format(precision=2), use_container_width=True, hide_index=True)
        
        csv = df_final.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Resultados", csv, "analise.csv", "text/csv")
    else:
        st.warning("Nenhuma ação encontrada. Tente baixar o valor da Liquidez para 100.000 para testar.")

except Exception as e:
    st.error(f"Ocorreu um problema: {e}")
