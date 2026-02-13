import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Scanner Fundamentus Pro", layout="wide")

st.title("📊 Scanner Automático - Fundamentus")

# Função para limpar cada célula individualmente
def limpar_valor(valor):
    if pd.isna(valor):
        return 0.0
    s = str(valor).replace('%', '').replace('.', '').replace(',', '.')
    try:
        return float(s)
    except:
        return 0.0

@st.cache_data(ttl=3600)
def carregar_dados_fundamentus():
    url = "https://fundamentus.com.br/resultado.php"
    header = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=header)
    
    # Lê a tabela do site
    df = pd.read_html(r.text, decimal=',', thousands='.')[0]
    
    # Renomeia as colunas por posição para não ter erro de nome
    novas_colunas = {
        df.columns[0]: 'Papel',
        df.columns[1]: 'PL',
        df.columns[2]: 'PVP',
        df.columns[10]: 'ROE',
        df.columns[11]: 'ROIC',
        df.columns[12]: 'DIV_PATRIM',
        df.columns[14]: 'LIQUIDEZ',
        df.columns[15]: 'CRESCIMENTO'
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
f_liq_min = st.sidebar.number_input("Liq. Diária Mínima (R$)", value=500000.0) # Começando com 500 mil para teste
f_div_max = st.sidebar.slider("Dív. Bruta/Patrimônio Máxima", 0.0, 5.0, 1.0)
f_cresc_min = st.sidebar.number_input("Crescimento 5a Mín (%)", value=1.0)
f_cresc_max = st.sidebar.number_input("Crescimento 5a Máx (%)", value=20.0)
f_graham_max = st.sidebar.number_input("Graham (P/L * P/VP) Máximo", value=22.5)

try:
    df_raw = carregar_dados_fundamentus()
    
    # Cálculo do Graham
    df_raw['Graham'] = df_raw['PL'] * df_raw['PVP']

    # --- FILTRO CORRIGIDO (Protegido por parênteses) ---
    mask = (
        (df_raw['PL'] > 0) & 
        (df_raw['PL'] <= f_pl_max) &
        (df_raw['ROIC'] >= f_roic_min) &
        (df_raw['ROE'] >= f_roe_min) &
        (df_raw['LIQUIDEZ'] >= f_liq_min) &
        (df_raw['DIV_PATRIM'] >= 0) & 
        (df_raw['DIV_PATRIM'] <= f_div_max) &
        (df_raw['CRESCIMENTO'] >= f_cresc_min) & 
        (df_raw['CRESCIMENTO'] <= f_cresc_max) &
        (df_raw['Graham'] <= f_graham_max)
    )

    df_final = df_raw[mask].copy()
    df_final = df_final.sort_values('Graham')

    st.success(f"Busca finalizada! {len(df_final)} ações encontradas.")
    
    if not df_final.empty:
        colunas_exibicao = ['Papel', 'PL', 'PVP', 'ROE', 'ROIC', 'DIV_PATRIM', 'LIQUIDEZ', 'CRESCIMENTO', 'Graham']
        st.dataframe(df_final[colunas_exibicao], use_container_width=True, hide_index=True)
        
        csv = df_final.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Resultados", csv, "analise.csv", "text/csv")
    else:
        st.warning("Nenhuma ação encontrada. Tente baixar o valor da 'Liq. Diária Mínima' para 100.000 para testar se os dados aparecem.")

except Exception as e:
    st.error(f"Erro ao processar filtros: {e}")
