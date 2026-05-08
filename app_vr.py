import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import urllib.parse
import os

# ==========================================
# CONFIGURAÇÕES INICIAIS E SEGURANÇA
# ==========================================
st.set_page_config(page_title="VR Software | Sales Intelligence", layout="wide")

APP_VERSION = "v1.1.2 - Stable UI"
ADMIN_PASS_REQUIRED = "333666"

# Credenciais seguras 
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
# CONEXÃO COM POSTGRESQL 
# ==========================================
@st.cache_data(ttl=60)
def carregar_dados_vendas():
    status_msg = "🔴 Erro de Configuração"
    status_cor = "#ef4444"
    df = pd.DataFrame()
    
    try:
        if CONN_STR:
            engine = create_engine(CONN_STR)
            # Mantém a tradução simples para não quebrar a UI
            query = "SELECT title AS produto, * FROM product"
            df = pd.read_sql(query, engine)
            status_msg = "PostgreSQL Conectado"
            status_cor = "#22c55e"
        else:
            raise Exception("Segredos não configurados")
            
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        if 'produto' in df.columns:
            df = df.drop_duplicates(subset=['produto'], keep='last')
        
        cols_financeiras = ['valor', 'horas_padrao', 'adesao_vinculada', 'valor_hora_implantacao']
        for col in cols_financeiras:
            if col not in df.columns: df[col] = 0.0
            else: df[col] = df[col].apply(limpar_valor)

        if 'tipo' not in df.columns: df['tipo'] = ''

        full = df.set_index('produto').to_dict('index')
        sist = {k: v for k, v in full.items() if 'sist' in str(v.get('tipo', '')).lower()}
        serv = {k: v for k, v in full.items() if 'serv' in str(v.get('tipo', '')).lower()}
        desp = {k: v for k, v in full.items() if 'desp' in str(v.get('tipo', '')).lower()}
        
        return sist, serv, desp, full, status_msg, status_cor, df
    
    except Exception as e:
        return {}, {}, {}, {}, "🔴 Desconectado", "#ef4444", df

sistemas_db, servicos_db, despesas_db, full_db, db_status, db_cor, df_raw = carregar_dados_vendas()

# ==========================================
# ESTILIZAÇÃO CSS
# ==========================================
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

# ==========================================
# ESTADO GLOBAL
# ==========================================
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
    for k, v in init_state.items(): st.session_state[k] = v
    if 'tmp_combo' in st.session_state: st.session_state.tmp_combo = "Montar Manualmente"
    st.session_state.sel_i, st.session_state.sel_m, st.session_state.sel_d = [], [], []
    for nome in full_db.keys(): st.session_state[f"perm_val_{nome}"] = 0

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=180)
    tela = st.radio("Navegação:", ["Gerador de Proposta", "Consulta de Preço", "Painel Admin"])
    
    if tela == "Gerador de Proposta":
        st.write("---")
        mapeamento_ativo = st.toggle("Mapeamento Inteligente", value=False)
        perfil_venda = st.selectbox("Perfil do Cliente", ["Executivo (Rua)", "CS (Base)"])
        desc = st.number_input("Desconto (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.5)
        faturamento_sistema = st.selectbox("Início Mensalidade", ["Na assinatura", "30 dias", "60 dias", "Após implantação"])
        parcelas_setup = st.selectbox("Parcelas Setup", [1, 2, 3, 4, 5, 6], index=3)

    st.markdown("<br>" * 3, unsafe_allow_html=True)
    st.markdown(f'''
        <hr style="margin: 10px 0; border-color: #ddd;">
        <div style="font-size: 0.8rem; color: #555;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                <div style="width: 10px; height: 10px; border-radius: 50%; background-color: {db_cor};"></div>
                <b>DB:</b> {db_status}
            </div>
            <div><b>Versão:</b> {APP_VERSION}</div>
        </div>
    ''', unsafe_allow_html=True)

# ==========================================
# TELAS
# ==========================================
if tela == "Painel Admin":
    st.markdown('<h1 class="hero-title">BACKOFFICE</h1>', unsafe_allow_html=True)
    senha_admin = st.text_input("Introduza a senha de acesso:", type="password")
    if senha_admin == ADMIN_PASS_REQUIRED:
        st.success("Acesso Autorizado.")
        st.dataframe(df_raw, use_container_width=True)
    elif senha_admin != "": st.error("Senha Incorreta.")

elif tela == "Gerador de Proposta":
    st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)
    
    if mapeamento_ativo:
        st.markdown('<div class="mapeamento-container"><h4>🛒 Mapeamento da Operação</h4></div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.number_input("PDV Convencional", min_value=0, key="tmp_pdv_conv", value=st.session_state.m_pdv_conv, on_change=sync_state, args=("m_pdv_conv", "tmp_pdv_conv"))
            st.number_input("PDV Touch", min_value=0, key="tmp_pdv_touch", value=st.session_state.m_pdv_touch, on_change=sync_state, args=("m_pdv_touch", "tmp_pdv_touch"))
        with c2:
            st.number_input("Semanas", min_value=0, key="tmp_semanas", value=st.session_state.m_semanas, on_change=sync_state, args=("m_semanas", "tmp_semanas"))
            st.checkbox("Migração de Banco?", key="tmp_migracao", value=st.session_state.m_migracao, on_change=sync_state, args=("m_migracao", "tmp_migracao"))
        with c3:
            st.button("🗑️ Limpar Tudo", on_click=limpar_tudo, use_container_width=True)

    col_i, col_m, col_d = st.columns(3) if perfil_venda == "Executivo (Rua)" else (*st.columns(2), None)
    with col_i:
        st.markdown('<div class="section-header"><span class="section-title">IMPLANTAÇÃO E SERVIÇOS</span></div>', unsafe_allow_html=True)
        st.session_state.sel_i = st.multiselect("Serviços", list(servicos_db.keys()), default=[s for s in st.session_state.sel_i if s in servicos_db])
        for i in st.session_state.sel_i:
            st.number_input(f"{i}", min_value=0, key=f"tmp_i_{i}", value=st.session_state[f"perm_val_{i}"], on_change=sync_state, args=(f"perm_val_{i}", f"tmp_i_{i}"))
    with col_m:
        st.markdown('<div class="section-header"><span class="section-title">MENSALIDADES SISTEMAS</span></div>', unsafe_allow_html=True)
        st.session_state.sel_m = st.multiselect("Sistemas", list(sistemas_db.keys()), default=[s for s in st.session_state.sel_m if s in sistemas_db])
        for i in st.session_state.sel_m:
            st.number_input(f"{i}", min_value=0, key=f"tmp_m_{i}", value=st.session_state[f"perm_val_{i}"], on_change=sync_state, args=(f"perm_val_{i}", f"tmp_m_{i}"))

    st.markdown("<h2 style='text-align:center; font-weight:800; margin-top:30px;'>RESUMO DO INVESTIMENTO</h2>", unsafe_allow_html=True)
    res_cols = st.columns(3) if perfil_venda == "Executivo (Rua)" else st.columns([1, 2, 2, 1])[1:3]

    total_setup, html_setup = 0.0, ""
    for s_nome in st.session_state.sel_i:
        horas = st.session_state[f"perm_val_{s_nome}"]
        if horas > 0:
            v_item = horas * servicos_db[s_nome].get('valor', 0)
            total_setup += v_item
            html_setup += f"<li><span>{s_nome}</span><span class='item-detalhe'>{horas}h x R$ {f_br(servicos_db[s_nome].get('valor', 0))}</span></li>"

    with res_cols[0]:
        st.markdown(f'''<div class="resumo-card"><span class="resumo-label">Investimento Implantação (Setup)</span><div class="resumo-valor">R$ {f_br(total_setup)}</div><div style="font-weight:bold;">{parcelas_setup}x de R$ {f_br(total_setup/parcelas_setup)}</div><div class="resumo-subtitulo">DETALHAMENTO</div><ul class="lista-itens">{html_setup if html_setup else "<li>Nenhum item</li>"}</ul></div>''', unsafe_allow_html=True)

    with res_cols[1]:
        t_liq = sum(st.session_state[f"perm_val_{i}"] * sistemas_db[i].get("valor", 0) for i in st.session_state.sel_m if i in sistemas_db) * (1 - (desc/100))
        html_m = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{st.session_state[f'perm_val_{i}']} un x R$ {f_br(sistemas_db[i].get('valor', 0))}</span></li>" for i in st.session_state.sel_m if i in sistemas_db])
        st.markdown(f'''<div class="resumo-card" style="border-top-color:#2e7d32;"><span class="resumo-label">Manutenção Mensal</span><div class="resumo-valor" style="color:#2e7d32;">R$ {f_br(t_liq)}</div><div class="resumo-subtitulo">SISTEMAS</div><ul class="lista-itens">{html_m if html_m else "<li>Nenhum</li>"}</ul></div>''', unsafe_allow_html=True)

elif tela == "Consulta de Preço":
    st.markdown('<h1 class="hero-title">ANÁLISE TÉCNICA</h1>')
    if full_db:
        p_sel = st.selectbox("Produto:", sorted(list(full_db.keys())))
        if p_sel: st.json(full_db[p_sel])
