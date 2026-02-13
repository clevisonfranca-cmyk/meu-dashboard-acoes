import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Scanner Fundamentus Pro", layout="wide")

st.title("📊 Scanner Automático - Fundamentus")

@st.cache_data(ttl=3600)
def carregar_dados_fundamentus():
    url = "https://fundamentus.com.br/resultado.php"
    header = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=header)
    df = pd.read_html(r.text, decimal=',', thousands='.')[0]
    
    # --- PADRONIZAÇÃO AUTOMÁTICA ---
    # Remove tudo que não é letra ou número para comparar
    def limpar_nome(nome):
        return "".join(filter(str.isalnum, nome)).upper()

    # Criamos um dicionário para mapear os nomes reais para nomes fáceis
    mapa_colunas = {}
    for col in df.columns:
        nome_limpo = limpar_nome(col)
        if 'PL' == nome_limpo: mapa_colunas[col] = 'PL'
        elif 'PVP' == nome_limpo: mapa_colunas[col] = 'PVP'
        elif 'ROIC' in nome_limpo: mapa_colunas[col] = 'ROIC'
        elif 'ROE' in nome_limpo: mapa_colunas[col] = 'ROE'
        elif 'DIVBRUT' in nome_limpo: mapa_colunas[col] = 'DIV_PATRIM'
        elif 'LIQ2MESES' in nome_limpo: mapa_colunas[col] = 'LIQUIDEZ'
        elif 'CRESC' in nome_limpo: mapa_colunas[col] = 'CRESCIMENTO'
    
    df = df.rename(columns=mapa_colunas)
    
    # Limpeza de strings para números
    for col in ['ROE', 'ROIC', 'CRESCIMENTO', 'DIV_PATRIM', 'PL', 'PVP']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace('%', '').str.replace('.', '').str.replace(',', '.'), errors='coerce')
    
    return df

# --- FILTROS ---
st.sidebar.header("Ajuste os Filtros")
f_pl_max = st.sidebar.number_input("P/L Máximo", value=15.0)
f_roic_min = st.sidebar.number_input("ROIC Mínimo (%)", value=10.0)
f_roe_min = st.sidebar.number_input("ROE Mínimo (%)", value=10.0)
f_liq_min = st.sidebar.number_input("Liq. Diária Mínima", value=500000.0)
f_div_max = st.sidebar.slider("Dív. Bruta/Patrimônio Máxima", 0.0, 5.0, 1.0)
f_cresc_min = st.sidebar.number_input("Crescimento Mínimo (%)", value=1.0)
f_cresc_max = st.sidebar.number_input("Crescimento Máximo (%)", value=20.0)
f_graham_max = st.sidebar.number_input("Graham (P/L * P/VP) Máximo", value=22.5)

try:
    df = carregar_dados_fundamentus()
    df['Graham'] = df['PL'] * df['PVP']

    filtro = (
        (df['PL'] > 0) & (df['PL'] <= f_pl_max) &
        (df['ROIC'] >= f_roic_min) &
        (df['ROE'] >= f_roe_min) &
        (df['LIQUIDEZ'] >= f_liq_min) &
        (df['DIV_PATRIM'] >= 0) & (df['DIV_PATRIM'] <= f_div_max) &
        (df['CRESCIMENTO'] >= f_cresc_min) & (df['CRESCIMENTO'] <= f_cresc_max) &
        (df['Graham'] <= f_graham_max)
    )

    df_final = df[filtro].sort_values('Graham')

    st.metric("Ações encontradas", len(df_final))
    st.dataframe(df_final[['Papel', 'PL', 'PVP', 'ROE', 'ROIC', 'DIV_PATRIM', 'LIQUIDEZ', 'Graham']], use_container_width=True)

except Exception as e:
    st.error(f"Erro detalhado: {e}")
