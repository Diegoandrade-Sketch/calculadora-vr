import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import urllib.parse
import os
import re

# ==========================================
# CONFIGURAÇÕES INICIAIS E CONTROLE DE VERSÃO
# ==========================================
st.set_page_config(page_title="VR Software | Sales Intelligence", layout="wide")

APP_VERSION = "v1.1.5 - Postgres Engine"
ADMIN_PASS_REQUIRED = "333666"

# Configuração de Conexão (Postgres)
try:
    DB_USER = st.secrets["DB_USER"]
    DB_PASS = st.secrets["DB_PASS"]
    DB_HOST = st.secrets["DB_HOST"]
    DB_PORT = st.secrets["DB_PORT"]
    DB_NAME = st.secrets["DB_NAME"]
    DB_PASS_ENCODED = urllib.parse.quote_plus(DB_PASS)
    CONN_STR = f"postgresql://{DB_USER}:{DB_PASS_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
except Exception:
    CONN_STR = None

# ==========================================
# BLOCO DE INTELIGÊNCIA: PROCESSAMENTO POSTGRES
# ==========================================
def motor_transformacao_vendas(df):
    """
    Trata os dados do Postgres para o formato esperado pelo layout estável.
    """
    # 1. Padronização de Colunas
    df.columns = [str(c).strip().lower() for c in df.columns]
    if 'title' in df.columns:
        df = df.rename(columns={'title': 'produto'})
    
    # Limpeza de duplicados pelo nome do produto
    df = df.drop_duplicates(subset=['produto'], keep='last')

    # 2. Inicialização de colunas de negócio
    df['tipo'] = ""
    df['horas_padrao'] = 0.0
    df['adesao_vinculada'] = 0.0
    df['valor_hora_implantacao'] = 125.0

    # 3. Classificação por IDs e Regras de Texto
    for idx, row in df.iterrows():
        tid = row.get('typeproductid', 0)
        nome = str(row['produto']).lower()
        
        # 604 = Sistemas
        if tid == 604:
            df.at[idx, 'tipo'] = 'sist'
            
        # 606 = Serviços ou Despesas
        elif tid == 606:
            if any(p in nome for p in ['despesa', 'km', 'hospedagem', 'deslocamento']):
                df.at[idx, 'tipo'] = 'desp'
            else:
                df.at[idx, 'tipo'] = 'serv'
                # Horas padrão vêm da coluna qtd_min
                df.at[idx, 'horas_padrao'] = float(row.get('qtd_min', 0))

    # 4. Vínculo de Adesão Automático
    mask_adesao = df['produto'].str.contains('Adesao|Adesão', case=False, na=False)
    adesoes = df[mask_adesao].copy()
    
    for _, ad_row in adesoes.iterrows():
        # Limpa o nome para encontrar o sistema pai
        chave = re.sub(r'ades[ãa]o', '', ad_row['produto'], flags=re.IGNORECASE).strip().lower()
        chave = re.sub(r'\s+', '', chave)
        
        for idx_s, sist_row in df[df['tipo'] == 'sist'].iterrows():
            nome_sist = re.sub(r'\s+', '', str(sist_row['produto']).lower())
            if chave in nome_sist or nome_sist in chave:
                df.at[idx_s, 'adesao_vinculada'] = float(ad_row.get('valor', 0))
                break

    # Remove as linhas de adesão para não aparecerem duplicadas na lista
    df = df[~mask_adesao]
    return df

# FUNÇÃO DE LIMPEZA (MANTIDA)
def limpar_valor(valor):
    if pd.isna(valor) or str(valor).strip() == "": return 0.0
    v = str(valor).replace('R$', '').replace(' ', '').strip()
    if ',' in v and '.' in v: v = v.replace('.', '').replace(',', '.')
    elif ',' in v: v = v.replace(',', '.')
    try: return float(v)
    except: return 0.0

# FUNÇÃO DE FORMATAÇÃO BRASILEIRA (MANTIDA)
def f_br(valor):
    if valor == 0: return "0,00"
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def f_pct(valor):
    return str(valor).replace('.', ',')

def sync_state(key_permanente, key_widget):
    st.session_state[key_permanente] = st.session_state[key_widget]

# ==========================================
# CONEXÃO E TELEMETRIA DE DADOS (ATUALIZADO)
# ==========================================
@st.cache_data(ttl=60)
def carregar_dados_vendas():
    status_msg = "🔴 Desconectado"
    status_cor = "#ef4444"
    df_raw = pd.DataFrame()
    
    try:
        if CONN_STR:
            engine = create_engine(CONN_STR)
            df_raw = pd.read_sql("SELECT * FROM product", engine)
            
            # Aplica o motor de inteligência
            df = motor_transformacao_vendas(df_raw)
            
            status_msg = "PostgreSQL Conectado"
            status_cor = "#22c55e"
            
            # Formatação de valores para garantir compatibilidade com o layout
            df['valor'] = df['valor'].apply(limpar_valor)

            full = df.set_index('produto').to_dict('index')
            sist = {k: v for k, v in full.items() if v['tipo'] == 'sist'}
            serv = {k: v for k, v in full.items() if v['tipo'] == 'serv'}
            desp = {k: v for k, v in full.items() if v['tipo'] == 'desp'}
            
            return sist, serv, desp, full, status_msg, status_cor, df_raw
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        
    return {}, {}, {}, {}, status_msg, status_cor, df_raw

sistemas_db, servicos_db, despesas_db, full_db, db_status, db_cor, df_raw = carregar_dados_vendas()

# ESTILIZAÇÃO CSS (EXATAMENTE COMO FORNECIDA)
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #ffffff 0%, #fff5ed 100%); }
    .hero-title { color: #262730; font-size: 4.5rem; font-weight: 900; margin: 0; line-height: 1; text-transform: uppercase; letter-spacing: -3px; }
    .mapeamento-container { background-color: #ffffff; border-left: 10px solid #ff6600; padding: 20px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .resumo-card { background-color: #ffffff; border: 1px solid #f0f0f0; border-top: 8px solid #ff6600; padding: 25px; border-radius: 8px; min-height: 450px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); display: flex; flex-direction: column; }
    .resumo-valor { color: #ff6600; font-size: 2.3rem; font-weight: 900; margin-bottom: 5px; }
    .item-detalhe { color: #333; font-size: 0.82rem; font-weight: 600; background-color: #fcfcfc; padding: 2px 8px; border-radius: 4px; border: 1px solid #eee; white-space: nowrap; }
    .section-header { background: linear-gradient(90deg, #ff6600 0%, #ff944d 100%); padding: 8px 15px; border-radius: 5px; margin-bottom: 15px; margin-top: 20px; }
    .section-title { color: #ffffff; font-size: 1.1rem; font-weight: bold; margin: 0; }
    .lista-itens { list-style-type: none; padding-left: 0; margin-top: 10px; flex-grow: 1; }
    .lista-itens li { padding: 8px 0; border-bottom: 1px dashed #e0e0e0; display: flex; justify-content: space-between; align-items: center; gap: 15px; }
    .lista-itens li span:first-child { font-weight: bold; font-size: 0.88rem; color: #444; }
    .item-incluso { padding-left: 20px !important; color: #777; font-size: 0.85rem; font-style: italic; border-bottom: none !important; }
    </style>
    """, unsafe_allow_html=True)

# ESTADO GLOBAL (EXATAMENTE COMO FORNECIDO)
init_state = {
    'm_combo': "Montar Manualmente", 'm_pdv_conv': 0, 'm_pdv_touch': 0, 'm_pdv_self': 0, 'm_semanas': 0, 'm_mobile': 0,
    'm_tef': "Não utiliza", 'm_migracao': False, 'm_ecommerce': False, 'm_app': False, 'm_connect': False,
    'm_erp
