import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Scanner Fundamentus Pro", layout="wide")

st.title("📊 Scanner Automático - Fundamentus")

# Função auxiliar para limpar cada célula individualmente
def limpar_valor(valor):
    if pd.isna(valor):
        return 0.0
    # Transforma em string, remove símbolos e ajusta decimais
    s = str(valor).replace('%', '').replace('.', '').replace(',', '.')
    try:
        return float(s)
    except:
        return 0.0

@st.cache_data(ttl=3600)
def carregar_dados_fundamentus():
    url = "https://fundamentus.com.br/resultado.php"
    header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"}
    r = requests.get(url, headers=header)
    
    # Lendo a tabela
    df = pd.read_html(r.text, decimal=',', thousands='.')[0]
    
    # Renomeando colunas pela posição para evitar erros de nomes/caracteres
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
    
    # Lista de colunas para limpar
    cols_para_limpar = ['PL', 'PVP', 'ROE', 'ROIC', 'DIV_PATRIM', 'LIQUIDEZ', 'CRESCIMENTO']
    
    # Aplicando a limpeza individual em cada coluna
    for col in cols_para_limpar:
        df[col] = df[col].apply(limpar_valor)
            
    return df

# --- INTERFACE LATERAL ---
st.sidebar.header("⚙️ Ajuste os Filtros")
f_pl_max = st.sidebar.number_input("P/L Máximo", value=15.0)
f_roic_min = st.sidebar.number_input("ROIC Mínimo (%)", value=10.0)
f_roe_min = st.sidebar.number_input("ROE Mínimo (%)", value=10.0)

# Sugestão: 500.000.000 é muito raro no BR por dia. Mantive o padrão menor para você ver resultados.
f_liq_min = st.sidebar.number_input("Liq. Diária Mínima (R$)", value=1000000.0) 

f_div_max = st.sidebar.slider("Dív. Bruta/Patrimônio Máxima", 0.0, 5.0, 1.0)
f_cresc_min = st.sidebar.number_input("Crescimento 5a Mín (%)", value=1.0)
f_cresc_max = st.sidebar.number_input("Crescimento 5a Máx (%)", value=20.0)
f_graham_max = st.sidebar.number_input("Graham (P/L * P/VP) Máximo", value=22.5)

try:
    df_raw = carregar_dados_fundamentus()
    
    # Cálculo do Graham (P/L * P/VP)
    df_raw['Graham'] = df_raw['PL'] * df_raw['PVP']

    # Filtros conforme sua solicitação
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

    # Exibição
    st.success(f"Busca finalizada! {len(df_final)} ações encontradas.")
    
    if not df_final.empty:
        # Exibindo apenas o que importa
        colunas_exibicao = ['Papel', 'PL', 'PVP', 'ROE', 'ROIC', 'DIV_PATRIM', 'LIQUIDEZ', 'CRESCIMENTO', 'Graham']
        st.dataframe(df_final[colunas_exibicao], use_container_width=True, hide_index=True)
        
        csv = df_final.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Resultados", csv, "analise_investimento.csv", "text/csv")
    else:
        st.warning("Nenhuma ação encontrada com os filtros atuais. Experimente diminuir a Liquidez Diária na esquerda.")

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
