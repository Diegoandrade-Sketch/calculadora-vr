import streamlit as st
import pandas as pd
import os

# ==========================================
# CONFIGURAÇÕES INICIAIS E CONTROLE DE VERSÃO
# ==========================================
st.set_page_config(page_title="VR Software | Sales Intelligence", layout="wide")

APP_VERSION = "v1.0.0 - Stable"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTgmdf_FgFd91dkm5zoD0l6l2ailLhCsEV-3pyFsQxRzoyNw2E96eQQoCYkfxHitA9oCIvfaI30-k-2/pub?output=csv"
EXCEL_FILE = "tabela_preco_chat.xlsx"

# FUNÇÃO DE LIMPEZA (EXCEL -> PYTHON)
def limpar_valor(valor):
    if pd.isna(valor) or str(valor).strip() == "": return 0.0
    v = str(valor).replace('R$', '').replace(' ', '').strip()
    if ',' in v and '.' in v: v = v.replace('.', '').replace(',', '.')
    elif ',' in v: v = v.replace(',', '.')
    try:
        return float(v)
    except: return 0.0

# FUNÇÃO DE FORMATAÇÃO BRASILEIRA (PYTHON -> TELA)
def f_br(valor):
    if valor == 0: return "0,00"
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# FUNÇÃO PARA FORMATAR PORCENTAGEM
def f_pct(valor):
    return str(valor).replace('.', ',')

def sync_state(key_permanente, key_widget):
    st.session_state[key_permanente] = st.session_state[key_widget]

# ==========================================
# CONEXÃO E TELEMETRIA DE DADOS
# ==========================================
@st.cache_data(ttl=60)
def carregar_dados_vendas():
    status_msg = "🔴 Desconectado / Erro"
    status_cor = "#ef4444" # Vermelho
    
    try:
        if os.path.exists(EXCEL_FILE):
            df = pd.read_excel(EXCEL_FILE)
            status_msg = "Excel Local (Fallback)"
            status_cor = "#3b82f6" # Azul
        else:
            df = pd.read_csv(SHEET_URL)
            status_msg = "Google Sheets (Online)"
            status_cor = "#f59e0b" # Amarelo/Laranja
        
        df.columns = [str(c).strip().lower() for c in df.columns]
        df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
        
        for col in ['horas_padrao', 'adesao_vinculada', 'valor_hora_implantacao']:
            if col not in df.columns: df[col] = 0.0

        df['valor'] = df['valor'].apply(limpar_valor)
        df['valor_hora_implantacao'] = df['valor_hora_implantacao'].apply(limpar_valor)
        df['adesao_vinculada'] = df['adesao_vinculada'].apply(limpar_valor)

        full = df.set_index('produto').to_dict('index')
        sist = {k: v for k, v in full.items() if 'sist' in str(v['tipo']).lower()}
        serv = {k: v for k, v in full.items() if 'serv' in str(v['tipo']).lower()}
        desp = {k: v for k, v in full.items() if 'desp' in str(v['tipo']).lower()}
        
        return sist, serv, desp, full, status_msg, status_cor
    
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return {}, {}, {}, {}, status_msg, status_cor

sistemas_db, servicos_db, despesas_db, full_db, db_status, db_cor = carregar_dados_vendas()

# ESTILIZAÇÃO CSS
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

# ESTADO GLOBAL
init_state = {
    'm_combo': "Montar Manualmente", 'm_pdv_conv': 0, 'm_pdv_touch': 0, 'm_pdv_self': 0, 'm_semanas': 0, 'm_mobile': 0,
    'm_tef': "Não utiliza", 'm_migracao': False, 'm_ecommerce': False, 'm_app': False, 'm_connect': False,
    'm_erp_pro': False, 'm_xml': False, 'm_escopo': False, 'm_controller': False, 'm_cartaz': False, 'm_masterfisco': False, 'm_backup': False
}
for k, v in init_state.items():
    if k not in st.session_state: st.session_state[k] = v
if 'sel_i' not in st.session_state: st.session_state.sel_i = []
if 'sel_m' not in st.session_state: st.session_state.sel_m = []
if 'sel_d' not in st.session_state: st.session_state.sel_d = []

for nome in full_db.keys():
    if f"perm_val_{nome}" not in st.session_state: st.session_state[f"perm_val_{nome}"] = 0

def limpar_tudo():
    for k
