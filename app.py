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
    
    # Mapeamento fixo por posição das colunas
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
    
    # Limpeza rigorosa
    cols_para_limpar = ['PL', 'PVP', 'ROE', 'ROIC', 'DIV_PATRIM', 'LIQUIDEZ', 'CRESCIMENTO']
    for col in cols_para_limpar:
        df[col] = df[col].apply(limpar_valor)
            
    return df

# --- INTERFACE LATERAL ---
st.sidebar.header("⚙️ Ajuste os Filtros")
f_pl_max = st.sidebar.number_input("P/L Máximo", value=15.0)
f_roic_min = st.sidebar.number_input("ROIC Mínimo (%)", value=10.0)
f_roe_min = st.sidebar.number_input("ROE Mínimo (%)", value=10.0)
f_liq_min = st.sidebar.number_input("Liq. Diária Mínima (R$)", value=1000000.0)
f_div_max = st.sidebar.slider("Dív. Bruta/Patrimônio Máxima", 0.0, 5.0, 1.0)
f_cresc_min = st.sidebar.number_input("Crescimento 5a Mín (%)", value=1.0)
f_cresc_max = st.sidebar.number_input("Crescimento 5a Máx (%)", value=20.0)
f_graham_max = st.sidebar.number_input("Graham (P/L * P/VP) Máximo", value=22.5)

try:
    # 1. Obter dados
    df_original = carregar_dados_fundamentus()
    
    # 2. Criar uma cópia para trabalhar
    df_f = df_original.copy()
    
    # 3. Calcular Graham antes de filtrar
    df_f['Graham'] = df_f['PL'] * df_f['PVP']

    # 4. Filtragem Robusta usando .query()
    # Este método evita o erro de "Truth value of a Series is ambiguous"
    query_string = (
        f"PL > 0 and PL <= {f_pl_max} and "
        f"ROIC >= {f_roic_min} and "
        f"ROE >= {f_roe_min} and "
        f"LIQUIDEZ >= {f_liq_min} and "
        f"DIV_PATRIM >= 0 and DIV_PATRIM <= {f_div_max} and "
        f"CRESCIMENTO >= {f_cresc_min} and CRESCIMENTO <= {f_cresc_max} and "
        f"Graham <= {f_graham_max}"
    )
    
    df_final = df_f.query(query_string).sort_values('Graham')

    # --- EXIBIÇÃO ---
    st.success(f"Busca finalizada! {len(df_final)} ações encontradas.")
    
    if not df_final.empty:
        colunas_exibicao = ['Papel', 'PL', 'PVP', 'ROE', 'ROIC', 'DIV_PATRIM', 'LIQUIDEZ', 'CRESCIMENTO', 'Graham']
        st.dataframe(df_final[colunas_exibicao].style.format(precision=2), use_container_width=True, hide_index=True)
        
        csv = df_final.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Resultados", csv, "minha_analise.csv", "text/csv")
    else:
        st.warning("Nenhuma ação encontrada. Tente reduzir a 'Liq. Diária Mínima' para 100.000 na barra lateral para testar.")

except Exception as e:
    st.error(f"Erro técnico: {e}")
    st.info("Dica: Se o erro persistir, pode haver um problema na leitura da tabela do Fundamentus.")
