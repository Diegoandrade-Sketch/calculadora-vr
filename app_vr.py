import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import urllib.parse
import os

# ==========================================
# CONFIGURAÇÕES INICIAIS E SEGURANÇA
# ==========================================
st.set_page_config(page_title="VR Software | Sales Intelligence", layout="wide")

APP_VERSION = "v1.1.1 - Postgres Hotfix"
ADMIN_PASS_REQUIRED = "333666"

# Credenciais seguras (Puxa do st.secrets no Streamlit Cloud ou .streamlit/secrets.toml local)
try:
    DB_USER = st.secrets["DB_USER"]
    DB_PASS = st.secrets["DB_PASS"]
    DB_HOST = st.secrets["DB_HOST"]
    DB_PORT = st.secrets["DB_PORT"]
    DB_NAME = st.secrets["DB_NAME"]
    
    # Codifica a senha para aceitar o caractere '@' ou especiais sem quebrar a string
    DB_PASS_ENCODED = urllib.parse.quote_plus(DB_PASS)
    CONN_STR = f"postgresql://{DB_USER}:{DB_PASS_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
except:
    CONN_STR = None

# FUNÇÕES DE FORMATAÇÃO E LIMPEZA
def f_br(valor):
    if valor == 0: return "0,00"
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def f_pct(valor):
    return str(valor).replace('.', ',')

def limpar_valor(valor):
    if pd.isna(valor) or str(valor).strip() == "": return 0.0
    v = str(valor).replace('R$', '').replace(' ', '').strip()
    if ',' in v and '.' in v: v = v.replace('.', '').replace(',', '.')
    elif ',' in v: v = v.replace(',', '.')
    try: return float(v)
    except: return 0.0

def sync_state(key_permanente, key_widget):
    st.session_state[key_permanente] = st.session_state[key_widget]

# ==========================================
# CONEXÃO COM POSTGRESQL (COM BLINDAGEM DE DADOS)
# ==========================================
@st.cache_data(ttl=60)
def carregar_dados_vendas():
    status_msg = "🔴 Erro de Configuração"
    status_cor = "#ef4444"
    df = pd.DataFrame()
    
    try:
        if CONN_STR:
            engine = create_engine(CONN_STR)
            # Traz a coluna 'title' disfarçada de 'produto' para casar com nosso código
            query = "SELECT title AS produto, * FROM product"
            df = pd.read_sql(query, engine)
            status_msg = "PostgreSQL Conectado"
            status_cor = "#22c55e" # Verde
        else:
            raise Exception("Segredos não configurados")
            
        # Padroniza as colunas do banco para minúsculo
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # Elimina duplicatas pelo nome do produto, mantendo o mais recente (evita crash do index)
        if 'produto' in df.columns:
            df = df.drop_duplicates(subset=['produto'], keep='last')
        
        # Garantia de colunas financeiras (Evita KeyError se o banco não tiver as colunas)
        cols_financeiras = ['valor', 'horas_padrao', 'adesao_vinculada', 'valor_hora_implantacao']
        for col in cols_financeiras:
            if col not in df.columns: df[col] = 0.0
            else: df[col] = df[col].apply(limpar_valor)

        # Garantia da coluna tipo (para evitar crash na classificação)
        if 'tipo' not in df.columns: df['tipo'] = ''

        # Montagem dos Dicionários em Memória
        full = df.set_index('produto').to_dict('index')
        sist = {k: v for k, v in full.items() if 'sist' in str(v.get('tipo', '')).lower()}
        serv = {k: v for k, v in full.items() if 'serv' in str(v.get('tipo', '')).lower()}
        desp = {k: v for k, v in full.items() if 'desp' in str(v.get('tipo', '')).lower()}
        
        return sist, serv, desp, full, status_msg, status_cor, df
    
    except Exception as e:
        st.error(f"Falha na Conexão: {e}")
        return {}, {}, {}, {}, "🔴 Desconectado", "#ef4444", df

sistemas_db, servicos_db, despesas_db, full_db, db_status, db_cor, df_raw = carregar_dados_vendas()

# ==========================================
# ESTILIZAÇÃO CSS
# ==========================================
st.markdown("""
    <style>
    .stApp {
