import streamlit as st
import pandas as pd
import os

# ==========================================
# CONFIGURAÇÕES INICIAIS E BANCO DE DADOS
# ==========================================
st.set_page_config(page_title="VR Software | Sales Intelligence", layout="wide")

SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTgmdf_FgFd91dkm5zoD0l6l2ailLhCsEV-3pyFsQxRzoyNw2E96eQQoCYkfxHitA9oCIvfaI30-k-2/pub?output=csv"
EXCEL_FILE = "tabela_preco_chat.xlsx"

def limpar_valor(valor):
    if pd.isna(valor) or str(valor).strip() == "": return 0.0
    try:
        v = str(valor).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        return float(v)
    except: return 0.0

def sync_state(key_permanente, key_widget):
    st.session_state[key_permanente] = st.session_state[key_widget]

@st.cache_data(ttl=60)
def carregar_dados_vendas():
    try:
        if os.path.exists(EXCEL_FILE):
            df = pd.read_excel(EXCEL_FILE)
        else:
            df = pd.read_csv(SHEET_URL)
        
        df.columns = [str(c).strip() for c in df.columns]
        df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
        
        col_tipo = next((c for c in df.columns if c.lower() == 'tipo'), 'Tipo')
        df['Tipo_Busca'] = df[col_tipo].astype(str).str.lower()
        df['Valor'] = df['Valor'].apply(limpar_valor)
        
        sist = df[df['Tipo_Busca'].str.contains('sist', na=False)].set_index('Produto').to_dict('index')
        serv = df[df['Tipo_Busca'].str.contains('serv', na=False)].set_index('Produto').to_dict('index')
        desp = df[df['Tipo_Busca'].str.contains('desp', na=False)].set_index('Produto').to_dict('index')
        full = df.set_index('Produto').to_dict('index')
        return sist, serv, desp, full
    except: return {}, {}, {}, {}

sistemas_db, servicos_db, despesas_db, full_db = carregar_dados_vendas()

# ESTILIZAÇÃO CSS
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #ffffff 0%, #fff5ed 100%); }
    .hero-title { color: #262730; font-size: 4.5rem; font-weight: 900; margin: 0; line-height: 1; text-transform: uppercase; letter-spacing: -3px; }
    .mapeamento-container { background-color: #ffffff; border-left: 10px solid #ff6600; padding: 20px; border-radius: 8px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .resumo-card { background-color: #ffffff; border: 1px solid #f0f0f0; border-top: 8px solid #ff6600; padding: 25px; border-radius: 8px; min-height: 450px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); display: flex; flex-direction: column; }
    .resumo-valor { color: #ff6
