import streamlit as st
import pandas as pd
import requests

# Configuração da Página
st.set_page_config(page_title="Scanner Fundamentus Pro", layout="wide")

st.title("📊 Scanner Automático - Fundamentus")
st.markdown("Dados extraídos em tempo real do fundamentus.com.br")

# --- FUNÇÃO PARA PEGAR DADOS ---
@st.cache_data(ttl=3600)
def carregar_dados_fundamentus():
    url = "https://fundamentus.com.br/resultado.php"
    header = {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"
    }
    r = requests.get(url, headers=header)
    # Lendo a tabela
    df = pd.read_html(r.text, decimal=',', thousands='.')[0]
    
    # --- LIMPEZA DE COLUNAS (Ajuste para evitar o erro que você viu) ---
    # Remove pontos e espaços extras dos nomes das colunas para facilitar a busca
    df.columns = [c.replace('.', '').strip() for c in df.columns]
    
    # Tratamento de dados percentuais e numéricos
    cols_para_limpar = ['Div Yield', 'ROE', 'ROIC', 'Cresc Rec 5a']
    for col in cols_para_limpar:
        if col in df.columns:
            df[col] = df[col].str.replace('%', '').str.replace('.', '').str.replace(',', '.').astype(float)
    
    return df

# --- BARRA LATERAL (FILTROS INTERATIVOS) ---
st.sidebar.header("Configuração dos Filtros")

f_pl_max = st.sidebar.number_input("P/L Máximo", value=15.0)
f_roic_min = st.sidebar.number_input("ROIC Mínimo (%)", value=10.0)
f_roe_min = st.sidebar.number_input("ROE Mínimo (%)", value=10.0)
f_liq_min = st.sidebar.number_input("Liq. Diária Mínima (R$)", value=500000.0, step=100000.0)
f_div_max = st.sidebar.slider("Dív. Bruta/Patrimônio Máxima", 0.0, 5.0, 1.0)
f_cresc_min = st.sidebar.number_input("Crescimento Rec. 5a Mín (%)", value=1.0)
f_cresc_max = st.sidebar.number_input("Crescimento Rec. 5a Máx (%)", value=20.0)
f_graham_max = st.sidebar.number_input("P/L * P/VP Máximo (Graham)", value=22.5)

# --- PROCESSAMENTO ---
try:
    df_raw = carregar_dados_fundamentus()
    
    # No código acima, removemos os pontos, então 'P/VP' continua 'P/VP' 
    # e 'Div.Brut/Patrim.' virou 'DivBrut/Patrim'
    df_raw['Graham_Index'] = df_raw['P/L'] * df_raw['P/VP']

    # Aplicação dos Filtros com os nomes normalizados
    filtro = (
        (df_raw['P/L'] > 0) & (df_raw['P/L'] <= f_pl_max) &
        (df_raw['ROIC'] >= f_roic_min) &
        (df_raw['ROE'] >= f_roe_min) &
        (df_raw['Liq2meses'] >= f_liq_min) &
        (df_raw['DivBrut/Patrim'] >= 0) & (df_raw['DivBrut/Patrim'] <= f_div_max) &
        (df_raw['Cresc Rec 5a'] >= f_cresc_min) & (df_raw['Cresc Rec 5a'] <= f_cresc_max) &
        (df_raw['Graham_Index'] < f_graham_max)
    )

    df_final = df_raw[filtro].sort_values(by='Graham_Index')

    # --- EXIBIÇÃO ---
    col1, col2 = st.columns(2)
    col1.metric("Empresas Analisadas", len(df_raw))
    col2.metric("Empresas Selecionadas", len(df_final))

    st.subheader("🚀 Ações que atendem aos seus critérios")
    
    # Selecionando colunas para mostrar (ajustadas sem o ponto)
    colunas_ver = ['Papel', 'P/L', 'P/VP', 'ROE', 'ROIC', 'DivBrut/Patrim', 'Liq2meses', 'Cresc Rec 5a', 'Graham_Index']
    st.dataframe(df_final[colunas_ver], use_container_width=True, hide_index=True)

    csv = df_final.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar Tabela em CSV", csv, "resultado_fundamentus.csv", "text/csv")

except Exception as e:
    st.error(f"Erro ao processar: {e}")
    st.info("Verifique se as colunas do Fundamentus mudaram ou se o site está fora do ar.")
