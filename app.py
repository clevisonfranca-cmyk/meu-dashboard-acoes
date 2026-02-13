import streamlit as st
import pandas as pd
import requests

# Configuração da Página
st.set_page_config(page_title="Scanner Fundamentus Pro", layout="wide")

st.title("📊 Scanner Automático - Fundamentus")
st.markdown("Dados extraídos em tempo real do fundamentus.com.br")

# --- FUNÇÃO PARA PEGAR DADOS ---
@st.cache_data(ttl=3600) # Guarda os dados por 1 hora para ser rápido
def carregar_dados_fundamentus():
    url = "https://fundamentus.com.br/resultado.php"
    # O Fundamentus exige um 'User-Agent' para permitir o acesso via código
    header = {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"
    }
    r = requests.get(url, headers=header)
    # Lendo a tabela e tratando formatos brasileiros (vírgula para decimal e ponto para milhar)
    df = pd.read_html(r.text, decimal=',', thousands='.')[0]
    
    # Limpeza básica de nomes e tipos
    for col in ['Div.Yield', 'ROE', 'ROIC', 'Cresc. Rec.5a']:
        df[col] = df[col].str.replace('%', '').str.replace('.', '').str.replace(',', '.').astype(float)
    
    return df

# --- BARRA LATERAL (FILTROS INTERATIVOS) ---
st.sidebar.header("Configuração dos Filtros")

f_pl_max = st.sidebar.number_input("P/L Máximo", value=15.0)
f_roic_min = st.sidebar.number_input("ROIC Mínimo (%)", value=10.0)
f_roe_min = st.sidebar.number_input("ROE Mínimo (%)", value=10.0)
# Ajustado para o padrão do Fundamentus (Liquidez Diária)
f_liq_min = st.sidebar.number_input("Liq. Diária Mínima (R$)", value=500000.0, step=100000.0)
f_div_max = st.sidebar.slider("Dív. Bruta/Patrimônio Máxima", 0.0, 5.0, 1.0)
f_cresc_min = st.sidebar.number_input("Crescimento Rec. 5a Mín (%)", value=1.0)
f_cresc_max = st.sidebar.number_input("Crescimento Rec. 5a Máx (%)", value=20.0)
f_graham_max = st.sidebar.number_input("P/L * P/VP Máximo (Graham)", value=22.5)

# --- PROCESSAMENTO ---
try:
    df_raw = carregar_dados_fundamentus()
    
    # Cálculo do critério de Graham
    # O Fundamentus chama P/VP de 'P/VP'
    df_raw['Graham_Index'] = df_raw['P/L'] * df_raw['P/VP']

    # Aplicação dos Filtros conforme sua solicitação
    # Nota: No Fundamentus a coluna de liquidez é 'Liquidez 2 meses' mas o nome no HTML é 'Liq.2meses'
    filtro = (
        (df_raw['P/L'] > 0) & (df_raw['P/L'] <= f_pl_max) &
        (df_raw['ROIC'] >= f_roic_min) &
        (df_raw['ROE'] >= f_roe_min) &
        (df_raw['Liq.2meses'] >= f_liq_min) &
        (df_raw['Div.Brut/Patrim'] >= 0) & (df_raw['Div.Brut/Patrim'] <= f_div_max) &
        (df_raw['Cresc. Rec.5a'] >= f_cresc_min) & (df_raw['Cresc. Rec.5a'] <= f_cresc_max) &
        (df_raw['Graham_Index'] < f_graham_max)
    )

    df_final = df_raw[filtro].sort_values(by='Graham_Index')

    # --- EXIBIÇÃO ---
    col1, col2 = st.columns(2)
    col1.metric("Empresas Analisadas", len(df_raw))
    col2.metric("Empresas Selecionadas", len(df_final))

    st.subheader("🚀 Ações que atendem aos seus critérios")
    st.dataframe(df_final[['Papel', 'P/L', 'P/VP', 'ROE', 'ROIC', 'Div.Brut/Patrim', 'Liq.2meses', 'Cresc. Rec.5a', 'Graham_Index']], 
                 use_container_width=True, 
                 hide_index=True)

    # Botão de download
    csv = df_final.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar Tabela em CSV", csv, "resultado_fundamentus.csv", "text/csv")

except Exception as e:
    st.error(f"Erro ao conectar com o Fundamentus: {e}")
    st.info("Dica: Às vezes o site do Fundamentus bloqueia acessos automáticos temporariamente.")
