import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import urllib.parse
import os
import re

# ==========================================
# CONFIGURAÇÕES TÉCNICAS E CONEXÃO
# ==========================================
st.set_page_config(page_title="VR Software | Sales Intelligence", layout="wide")

APP_VERSION = "v1.2.8 - Production Stable"
ADMIN_PASS_REQUIRED = "333666"

try:
    DB_USER = st.secrets["DB_USER"]
    DB_PASS = st.secrets["DB_PASS"]
    DB_HOST = st.secrets["DB_HOST"]
    DB_PORT = st.secrets["DB_PORT"]
    DB_NAME = st.secrets["DB_NAME"]
    DB_PASS_ENCODED = urllib.parse.quote_plus(DB_PASS)
    CONN_STR = f"postgresql://{DB_USER}:{DB_PASS_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
except:
    CONN_STR = None

# ==========================================
# MOTOR DE DADOS (POSTGRESQL)
# ==========================================
def categorizar_base_vr(df):
    """Tratamento interno de IDs e Nomes conforme regras da VR"""
    df.columns = [str(c).strip().lower() for c in df.columns]
    df = df.drop_duplicates(subset=['produto'], keep='last')
    
    df['categoria_interna'] = ""
    for idx, row in df.iterrows():
        tid = row.get('typeproductid', 0)
        nome = str(row['produto']).lower()
        
        if tid == 604:
            df.at[idx, 'categoria_interna'] = 'sist'
        elif tid == 606:
            if any(x in nome for x in ['adesao', 'adesão']):
                df.at[idx, 'categoria_interna'] = 'adesao'
            elif any(x in nome for x in ['despesa', 'km', 'hospedagem', 'logistica', 'deslocamento']):
                df.at[idx, 'categoria_interna'] = 'desp'
            else:
                df.at[idx, 'categoria_interna'] = 'serv' # Projetos / Taxas
    return df

@st.cache_data(ttl=60)
def carregar_dados_producao():
    if not CONN_STR: return {}, {}, {}, {}, {}, "Desconectado", "#f00", pd.DataFrame()
    try:
        engine = create_engine(CONN_STR)
        df_raw = pd.read_sql("SELECT * FROM product", engine)
        df = categorizar_base_vr(df_raw)
        
        full = df.set_index('produto').to_dict('index')
        sist = {k: v for k, v in full.items() if v['categoria_interna'] == 'sist'}
        serv = {k: v for k, v in full.items() if v['categoria_interna'] == 'serv'}
        desp = {k: v for k, v in full.items() if v['categoria_interna'] == 'desp'}
        ades = {k: v for k, v in full.items() if v['categoria_interna'] == 'adesao'}
        
        return sist, serv, desp, ades, full, "Conectado", "#22c55e", df
    except Exception as e:
        return {}, {}, {}, {}, {}, f"Erro: {e}", "#f00", pd.DataFrame()

sist_db, serv_db, desp_db, ades_db, full_db, db_st, db_co, df_raw = carregar_dados_producao()

# ==========================================
# ESTILO VISUAL (RESTAURAÇÃO v1.0.0)
# ==========================================
st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(135deg, #ffffff 0%, #fff5ed 100%); }}
    .hero-title {{ color: #262730; font-size: 4.5rem; font-weight: 900; margin: 0; line-height: 1; text-transform: uppercase; letter-spacing: -3px; }}
    .mapeamento-container {{ background-color: #ffffff; border-left: 10px solid #ff6600; padding: 20px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
    .resumo-card {{ background-color: #ffffff; border: 1px solid #f0f0f0; border-top: 8px solid #ff6600; padding: 25px; border-radius: 8px; min-height: 450px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); display: flex; flex-direction: column; }}
    .resumo-valor {{ color: #ff6600; font-size: 2.3rem; font-weight: 900; margin-bottom: 5px; }}
    .item-detalhe {{ color: #333; font-size: 0.82rem; font-weight: 600; background-color: #fcfcfc; padding: 2px 8px; border-radius: 4px; border: 1px solid #eee; white-space: nowrap; }}
    .section-header {{ background: linear-gradient(90deg, #ff6600 0%, #ff944d 100%); padding: 8px 15px; border-radius: 5px; margin-bottom: 15px; margin-top: 20px; }}
    .section-title {{ color: #ffffff; font-size: 1.1rem; font-weight: bold; margin: 0; }}
    .lista-itens {{ list-style-type: none; padding-left: 0; margin-top: 10px; flex-grow: 1; }}
    .lista-itens li {{ padding: 8px 0; border-bottom: 1px dashed #e0e0e0; display: flex; justify-content: space-between; align-items: center; gap: 15px; }}
    .lista-itens li span:first-child {{ font-weight: bold; font-size: 0.88rem; color: #444; }}
    .item-incluso {{ padding-left: 20px !important; color: #777 !important; font-size: 0.82rem !important; font-style: italic; border-bottom: none !important; }}
    </style>
""", unsafe_allow_html=True)

# HELPERS
def f_br(v): return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def sync_v(kp, kw): st.session_state[kp] = st.session_state[kw]

# SESSION STATE (v1.0.0)
if 'init_done' not in st.session_state:
    st.session_state.init_done = True
    st.session_state.sel_i = []
    st.session_state.sel_m = []
    st.session_state.sel_d = []
    for k in full_db.keys(): st.session_state[f"v_{k}"] = 0

# SIDEBAR (RESTAURADA)
with st.sidebar:
    if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=180)
    tela = st.radio("Navegação:", ["Gerador de Proposta", "Consulta de Preço", "Admin"])
    if tela == "Gerador de Proposta":
        st.write("---")
        map_ativo = st.toggle("Mapeamento Inteligente", value=True)
        modo_apres = st.toggle("Modo Apresentação")
        perfil_venda = st.selectbox("Perfil do Cliente", ["Executivo (Rua)", "CS (Base)"])
        desc_global = st.number_input("Desconto (%)", 0.0, 30.0, 0.0, 0.5)
        exibir_detalhe_desc = st.toggle("Exibir Desconto na Tela", value=True)
        fat_mensal = st.selectbox("Início Mensalidade", ["Na assinatura", "30 dias", "Após implantação"])
        parcelas_setup = st.selectbox("Parcelas Setup", [1,2,3,4,5,6,10,12], index=3)
    st.markdown(f'<div style="font-size:0.75rem; margin-top:50px; color:#666;"><div style="display:flex; align-items:center; gap:5px;"><div style="width:8px; height:8px; border-radius:50%; background:{db_co};"></div>DB {db_st}</div>V {APP_VERSION}</div>', unsafe_allow_html=True)

# TELA: CONSULTA
if tela == "Consulta de Preço":
    st.markdown('<h1 class="hero-title">ANÁLISE</h1>', unsafe_allow_html=True)
    sel_cons = st.selectbox("Pesquisar Item:", sorted(list(full_db.keys())))
    if sel_cons: st.json(full_db[sel_cons])

# TELA: ADMIN
elif tela == "Admin":
    if st.text_input("Acesso", type="password") == ADMIN_PASS_REQUIRED: st.dataframe(df_raw)

# TELA: GERADOR (A TELA PRINCIPAL)
elif tela == "Gerador de Proposta":
    if not modo_apres:
        st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)
        
        # MAPEAMENTO INTELIGENTE (RESTAURAÇÃO TOTAL 3 COLUNAS)
        if map_ativo:
            st.markdown('<div class="mapeamento-container"><h3 style="margin:0 0 15px 0; color:#ff6600;">🛒 Mapeamento da Operação</h3>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.number_input("PDV Convencional", 0, key="m_conv")
                st.number_input("PDV Touch", 0, key="m_touch")
                st.number_input("PDV Selfcheckout", 0, key="m_self")
            with c2
