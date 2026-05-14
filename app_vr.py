import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import urllib.parse
import os
import json

# ==========================================
# CONFIGURACOES INICIAIS E CONTROLE DE VERSAO
# ==========================================
st.set_page_config(page_title="VR Software | Sales Intelligence", layout="wide")

APP_VERSION = "v1.9.0 - Enterprise Edition (Full Management)"
CACHE_FILE = "cache_vr.json"

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

# FUNCOES DE FORMATACAO
def f_br(valor):
    if pd.isna(valor) or valor == 0: return "0,00"
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def f_pct(valor):
    return str(valor).replace('.', ',')

def sync_state(key_permanente, key_widget):
    st.session_state[key_permanente] = st.session_state[key_widget]

# ==========================================
# DATA LAYER (OPTIMIZED CACHE)
# ==========================================
@st.cache_data(ttl=3600)
def carregar_dados_vendas():
    status_msg, status_cor = "Desconectado", "#ef4444"
    try:
        if CONN_STR:
            engine = create_engine(CONN_STR)
            df = pd.read_sql("SELECT * FROM product", engine)
            df_vinc = pd.read_sql("SELECT * FROM product_vinculo", engine)
            status_msg, status_cor = "PostgreSQL (Online)", "#22c55e"
            return df, df_vinc, status_msg, status_cor
    except Exception:
        return pd.DataFrame(), pd.DataFrame(), "Erro Conexao", "#ef4444"
    return pd.DataFrame(), pd.DataFrame(), status_msg, status_cor

df_raw, df_vinc_raw, db_status, db_cor = carregar_dados_vendas()

# Processamento de Dados
full_db = {}
id_to_name = {}
name_to_id = {}
vinculos_db = {}
sistemas_db = {}
servicos_db = {}
despesas_db = {}

if not df_raw.empty:
    df_raw.columns = [str(c).strip().lower() for c in df_raw.columns]
    df_raw = df_raw.drop_duplicates(subset=['produto'], keep='last')
    for col in ['valor', 'horas_padrao', 'adesao_vinculada', 'valor_hora_implantacao', 'typeproductid']:
        if col in df_raw.columns: df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce').fillna(0.0)
    
    full_db = df_raw.set_index('produto').to_dict('index')
    id_to_name = df_raw.set_index('id')['produto'].to_dict() if 'id' in df_raw.columns else {}
    name_to_id = {v: k for k, v in id_to_name.items()}
    sistemas_db = {k: v for k, v in full_db.items() if v.get('typeproductid') == 604}
    kw_desp = ['km', 'hospedagem', 'logistica', 'alimentacao', 'despesa', 'passagem', 'viagem', 'deslocamento', 'pedagio']
    servicos_db = {k: v for k, v in full_db.items() if v.get('typeproductid') == 606 and not any(x in k.lower() for x in kw_desp)}
    despesas_db = {k: v for k, v in full_db.items() if any(x in k.lower() for x in kw_desp)}

if not df_vinc_raw.empty:
    df_vinc_raw.columns = [str(c).strip().lower() for c in df_vinc_raw.columns]
    for _, row in df_vinc_raw.iterrows():
        pai_id = int(row['id_produto_pai'])
        if pai_id not in vinculos_db: vinculos_db[pai_id] = []
        vinculos_db[pai_id].append({'id_filho': int(row['id_produto_filho']), 'tipo': row['tipo_vinculo'], 'qtd': float(row['quantidade_padrao'])})

# ==========================================
# ESTADO GLOBAL E AUTENTICACAO
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_role' not in st.session_state: st.session_state.user_role = None
if 'primeiro_acesso' not in st.session_state: st.session_state.primeiro_acesso = False
if 'user_email' not in st.session_state: st.session_state.user_email = ""
if 'user_name' not in st.session_state: st.session_state.user_name = ""

init_state_app = {
    'm_combo': "Montar Manualmente", 'm_pdv_conv': 0.0, 'm_pdv_touch': 0.0, 'm_pdv_self': 0.0, 'm_semanas': 0.0, 'm_mobile': 0.0,
    'm_tef': "Nao utiliza", 'm_migracao': False, 'm_ecommerce': False, 'm_app': False, 'm_connect': False,
    'm_erp_pro': False, 'm_xml': False, 'm_escopo': False, 'm_controller': False, 'm_cartaz': False, 'm_masterfisco': False, 'm_backup': False,
    'auto_added': set(), 'sel_m': [], 'sel_i': [], 'sel_d': [], 'ui_sel_m': [], 'ui_sel_i': [], 'ui_sel_d': []
}
for k, v in init_state_app.items():
    if k not in st.session_state: st.session_state[k] = v

for nome in full_db.keys():
    if f"perm_val_{nome}" not in st.session_state: st.session_state[f"perm_val_{nome}"] = 0.0

# ==========================================
# BLOCO 1: TELA DE LOGIN (CLEAN DESIGN)
# ==========================================
def tela_login():
    st.markdown("""
        <style>
        .stApp { background: white; }
        .login-container { display: flex; flex-direction: column; align-items: center; justify-content: center; padding-top: 50px; }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        if os.path.exists("logo_vr.png"):
            st.image("logo_vr.png", width=250)
        else:
            st.title("VR Software")
        
        st.markdown("<h3 style='text-align:center; color:#444; margin-top:20px;'>Acesso Enterprise</h3>", unsafe_allow_html=True)
        
        if st.session_state.primeiro_acesso:
            st.info("Primeiro acesso! Por favor, crie sua senha definitiva.")
            ns = st.text_input("Nova Senha", type="password")
            nsc = st.text_input("Confirme a Senha", type="password")
            if st.button("Definir Senha e Entrar", use_container_width=True):
                if ns and ns == nsc:
                    try:
                        engine = create_engine(CONN_STR)
                        with engine.begin() as conn:
                            conn.execute(text("UPDATE usuarios SET senha = :s, primeiro_acesso = FALSE WHERE email = :e"), {"s": ns, "e": st.session_state.user_email})
                        st.session_state.primeiro_acesso = False
                        st.session_state.logged_in = True
                        st.rerun()
                    except: st.error("Erro no Banco de Dados.")
                else: st.error("Senhas incorretas.")
        else:
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            
            if email == "admin" and senha == "333666":
                st.session_state.logged_in = True
                st.session_state.user_role = "admin"
                st.session_state.user_name = "Administrador Master"
                st.rerun()

            if st.button("Entrar", use_container_width=True):
                try:
                    engine = create_engine(CONN_STR)
                    with engine.connect() as conn:
                        res = pd.read_sql(text("SELECT * FROM usuarios WHERE email = :e AND ativo = TRUE"), conn, params={"e": email})
                    if not res.empty:
                        u = res.iloc[0]
                        if u['senha'] == senha or u['primeiro_acesso']:
                            st.session_state.user_email = email
                            st.session_state.user_role = u['nivel_acesso']
                            st.session_state.user_name = u['nome']
                            if u['primeiro_acesso']:
                                st.session_state.primeiro_acesso = True
                            else:
                                st.session_state.logged_in = True
                            st.rerun()
                        else: st.error("Senha incorreta.")
                    else: st.error("Acesso negado.")
                except: st.error("Falha na conexão.")
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# BLOCO 2: APLICATIVO PRINCIPAL (ENCAPSULADO)
# ==========================================
def aplicativo_principal():
    st.markdown("""
        <style>
        .stApp { background: linear-gradient(135deg, #ffffff 0%, #fff5ed 100%); }
        .hero-title { color: #262730; font-size: 4rem; font-weight: 900; margin: 0; text-transform: uppercase; letter-spacing: -2px; }
        .resumo-card { background: white; border-top: 8px solid #ff6600; padding: 25px; border-radius: 8px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); min-height: 450px; }
        .item-detalhe { font-size: 0.82rem; font-weight: 600; background: #f9f9f9; padding: 2px 8px; border-radius: 4px; border: 1px solid #eee; }
        .section-header { background: #ff6600; color: white; padding: 8px 15px; border-radius: 5px; margin: 20px 0 15px 0; font-weight: bold; }
        .item-incluso { padding-left: 20px !important; color: #777; font-size: 0.85rem; font-style: italic; border-bottom: none !important; }
        </style>
    """, unsafe_allow_html=True)

    def processar_regras_colaterais():
        novos_auto = set()
        for m_nome in st.session_state.sel_m:
            p_id = name_to_id.get(m_nome)
            if p_id and p_id in vinculos_db:
                for r in vinculos_db[p_id]:
                    if r['tipo'] in ['projeto', 'adesao']:
                        f_nome = id_to_name.get(r['id_filho'])
                        if f_nome:
                            novos_auto.add(f_nome)
                            st.session_state[f"perm_val_{f_nome}"] = float(r['qtd'])
        lista_i = list(st.session_state.ui_sel_i)
        for item in st.session_state.auto_added - novos_auto:
            if item in lista_i: 
                lista_i.remove(item)
                st.session_state[f"perm_val_{item}"] = 0.0
        for item in novos_auto:
            if item not in lista_i: lista_i.append(item)
        st.session_state.auto_added = novos_auto
        st.session_state.ui_sel_i = lista_i
        st.session_state.sel_i = lista_i

    def sync_ui_sist():
        st.session_state.sel_m = st.session_state.ui_sel_m
        processar_regras_colaterais()

    def sync_ui_serv(): st.session_state.sel_i = st.session_state.ui_sel_i
    def sync_ui_desp(): st.session_state.sel_d = st.session_state.ui_sel_d

    def sync_combo_logic():
        if st.session_state.tmp_combo == "Padrao Pequeno Porte":
            st.session_state.m_pdv_conv, st.session_state.m_tef, st.session_state.m_mobile = 3.0, "SiTef Express", 1.0
            st.session_state.m_erp_pro, st.session_state.m_xml, st.session_state.m_migracao, st.session_state.m_escopo = True, True, True, True

    with st.sidebar:
        if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=180)
        st.markdown(f"**👤 {st.session_state.user_name}**")
        abas = ["Gerador de Proposta", "Consulta de Preco"]
        if st.session_state.user_role == "admin":
            if not st.toggle("Simular Visão Vendedor", value=False): abas.append("Painel Admin")
        tela = st.radio("Navegacao:", abas)
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    if tela == "Painel Admin":
        st.markdown("<h1 class='hero-title'>BACKOFFICE</h1>", unsafe_allow_html=True)
        t_unid, t_user = st.tabs(["🏢 Unidades", "👥 Usuarios"])
        with t_unid:
            with st.form("f_unid"):
                c1, c2, c3 = st.columns(3)
                n_fant, cnpj, cid = c1.text_input("Nome Fantasia"), c2.text_input("CNPJ"), c3.text_input("Cidade")
                end = st.text_input("Endereço Completo")
                if st.form_submit_button("Salvar Unidade"):
                    try:
                        engine = create_engine(CONN_STR)
                        with engine.begin() as conn:
                            conn.execute(text("INSERT INTO unidades (nome_fantasia, cnpj, cidade, logradouro) VALUES (:n, :c, :ci, :e)"), {"n": n_fant, "c": cnpj, "ci": cid, "e": end})
                        st.success("Salvo!")
                    except: st.error("Erro.")
            try:
                engine = create_engine(CONN_STR)
                st.dataframe(pd.read_sql("SELECT * FROM unidades", engine), use_container_width=True)
            except: pass
        with t_user:
            try:
                engine = create_engine(CONN_STR)
                df_u_l = pd.read_sql("SELECT id, nome_fantasia FROM unidades", engine)
                u_d = dict(zip(df_u_l['nome_fantasia'], df_u_l['id']))
                with st.form("f_user"):
                    unm, uem = st.text_input("Nome"), st.text_input("E-mail")
                    unid = st.selectbox("Unidade", list(u_d.keys()))
                    urol = st.selectbox("Nivel", ["vendedor", "admin"])
                    if st.form_submit_button("Criar"):
                        with engine.begin() as conn:
                            conn.execute(text("INSERT INTO usuarios (nome, email, nivel_acesso, id_unidade, senha, primeiro_acesso) VALUES (:n, :e, :r, :id_u, '123456', TRUE)"), {"n": unm, "e": uem, "r": urol, "id_u": u_d[unid]})
                        st.success("Criado!")
            except: st.warning("Crie unidades primeiro.")

    elif tela == "Gerador de Proposta":
        st.markdown("<h1 class='hero-title'>PROPOSTA</h1>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("<div class='section-header'>SERVICOS</div>", unsafe_allow_html=True)
            st.multiselect("Servicos", list(servicos_db.keys()), key="ui_sel_i", on_change=sync_ui_serv)
            for i in st.session_state.sel_i:
                st.number_input(f"{i}", 0.0, step=1.0, value=st.session_state[f"perm_val_{i}"], key=f"tmp_i_{i}", on_change=sync_state, args=(f"perm_val_{i}", f"tmp_i_{i}"))
        with c2:
            st.markdown("<div class='section-header'>SISTEMAS</div>", unsafe_allow_html=True)
            st.multiselect("Sistemas", list(sistemas_db.keys()), key="ui_sel_m", on_change=sync_ui_sist)
            for i in st.session_state.sel_m:
                st.number_input(f"{i}", 0.0, step=1.0, value=st.session_state[f"perm_val_{i}"], key=f"tmp_m_{i}", on_change=sync_state, args=(f"perm_val_{i}", f"tmp_m_{i}"))
        
        st.markdown("---")
        res_cols = st.columns(3)
        
        # Ordenação VIP
        def sort_m(item):
            prio = {"VR ERP PRO": 1, "VR PDV Convencional": 2, "VR Gerenciador Xml": 4, "VR Mobile (Smartphone/Android)": 5}
            if "VR Sitef Express" in item: return 3
            return 99
        def sort_s(item):
            if "Projeto ERP PRO" in item['n']: return 1
            if "Migracao" in item['n']: return 2
            if "Escopo" in item['n']: return 3
            return 99

        s_lines = []
        v_h_base = servicos_db.get("Implantação e Treinamento", {}).get("valor", 0.0)
        for n in st.session_state.sel_i:
            q = st.session_state[f"perm_val_{n}"]
            if q > 0:
                v = full_db.get(n, {}).get('valor', 0.0)
                s_lines.append({'n': n, 'h': f"<li>{n}: {f_br(q*v)}</li>", 'v': q*v})
        for n in st.session_state.sel_m:
            if n not in ["VR Mobile (Smartphone/Android)", "VR PDV Touchscreen", "VR PDV Self Checkout"]:
                d = sistemas_db[n]; h, ads = d.get('horas_padrao', 0.0), d.get('adesao_vinculada', 0.0)
                if h > 0:
                    rt = d.get('valor_hora_implantacao', 0.0) or v_h_base
                    nm = "Projeto ERP PRO" if n == "VR ERP PRO" else f"Implantacao {n}"
                    s_lines.append({'n': nm, 'h': f"<li>{nm}: {f_br(h*rt)}</li>", 'v': h*rt})
                if ads > 0: s_lines.append({'n': f"Adesao {n}", 'h': f"<li>Adesão {n}: {f_br(ads)}</li>", 'v': ads})
        
        s_lines.sort(key=sort_s)
        with res_cols[0]:
            st.markdown(f"<div class='resumo-card'><span>Setup</span><br>R$ {f_br(sum(x['v'] for x in s_lines))}<ul>{''.join(x['h'] for x in s_lines)}</ul></div>", unsafe_allow_html=True)

        m_html, total_m = "", 0.0
        for n in sorted(st.session_state.sel_m, key=sort_m):
            q = st.session_state[f"perm_val_{n}"]
            if q > 0:
                v = sistemas_db[n]['valor']
                total_m += (q * v)
                m_html += f"<li>{n}: {f_br(q*v)}</li>"
                if n == "VR ERP PRO":
                    for inc in ["VR Promo", "VR Carteira Digital", "VR Analytics"]: m_html += f"<li class='item-incluso'>└ {inc}</li>"
        
        with res_cols[1]:
            st.markdown(f"<div class='resumo-card'><span>Mensal</span><br>R$ {f_br(total_m)}<ul>{m_html}</ul></div>", unsafe_allow_html=True)

if not st.session_state.logged_in:
    tela_login()
else:
    aplicativo_principal()
