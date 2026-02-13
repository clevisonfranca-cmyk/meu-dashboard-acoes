import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Scanner Fundamentus Pro", layout="wide")

st.title("📊 Scanner Automático - Fundamentus")

@st.cache_data(ttl=3600)
def carregar_dados_fundamentus():
    url = "https://fundamentus.com.br/resultado.php"
    header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"}
    r = requests.get(url, headers=header)
    # Forçamos o pandas a ler a tabela e tratamos os decimais
    df = pd.read_html(r.text, decimal=',', thousands='.')[0]
    
    # --- MAPEAMENTO POR POSIÇÃO (Mais seguro que por nome) ---
    # No Fundamentus, a ordem das colunas costuma ser fixa.
    # Vamos renomear as colunas principais pela posição delas:
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
    
    # Limpeza de dados (Garantir que tudo vire número)
    cols_numericas = ['PL', 'PVP', 'ROE', 'ROIC', 'DIV_PATRIM', 'LIQUIDEZ', 'CRESCIMENTO']
    for col in cols_numericas:
        if col in df.columns:
            # Remove % e converte para número
            df[col] = df[col].astype(str).str.replace('%', '').str.replace('.', '', regex=False).str.replace(',', '.')
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Ajuste para percentuais (ROE, ROIC, Crescimento no Fundamentus vêm como 15.0 para 15%)
            # Não dividimos por 100 aqui pois seus filtros já usam a base 10 (ex: 10 para 10%)
            
    return df

# --- INTERFACE ---
st.sidebar.header("Ajuste os Filtros")
f_pl_max = st.sidebar.number_input("P/L Máximo", value=15.0)
f_roic_min = st.sidebar.number_input("ROIC Mínimo (%)", value=10.0)
f_roe_min = st.sidebar.number_input("ROE Mínimo (%)", value=10.0)
# Note: 500 milhões é MUITO alto para liquidez diária. Baixei o padrão para facilitar o teste.
f_liq_min = st.sidebar.number_input("Liq. Diária Mínima (R$)", value=1000000.0) 
f_div_max = st.sidebar.slider("Dív. Bruta/Patrimônio Máxima", 0.0, 5.0, 1.0)
f_cresc_min = st.sidebar.number_input("Crescimento 5a Mín (%)", value=1.0)
f_cresc_max = st.sidebar.number_input("Crescimento 5a Máx (%)", value=20.0)
f_graham_max = st.sidebar.number_input("Graham (P/L * P/VP) Máximo", value=22.5)

try:
    df_raw = carregar_dados_fundamentus()
    
    # Cálculo do Graham
    df_raw['Graham'] = df_raw['PL'] * df_raw['PVP']

    # Filtros
    mask = (
        (df_raw['PL'] > 0) & (df_raw['PL'] <= f_pl_max) &
        (df_raw['ROIC'] >= f_roic_min) &
        (df_raw['ROE'] >= f_roe_min) &
        (df_raw['LIQUIDEZ'] >= f_liq_min) &
        (df_raw['DIV_PATRIM'] >= 0) & (df_raw['DIV_PATRIM'] <= f_div_max) &
        (df_raw['CRESCIMENTO'] >= f_cresc_min) & (df_raw['CRESCIMENTO'] <= f_cresc_max) &
        (df_raw['Graham'] <= f_graham_max)
    )

    df_final = df_raw[mask].sort_values('Graham')

    # Resultados
    st.success(f"Busca finalizada! {len(df_final)} ações encontradas.")
    
    if not df_final.empty:
        st.dataframe(
            df_final[['Papel', 'PL', 'PVP', 'ROE', 'ROIC', 'DIV_PATRIM', 'LIQUIDEZ', 'Graham']], 
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.warning("Nenhuma ação encontrada com esses filtros. Tente relaxar os critérios (ex: baixar a Liquidez ou aumentar o P/L).")

except Exception as e:
    st.error(f"Erro ao processar os dados: {e}")
    st.info("Isso pode ocorrer se o Fundamentus mudar a ordem das colunas. Tente atualizar a página.")
