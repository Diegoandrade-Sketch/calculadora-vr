import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import urllib.parse
import os

# ==========================================
# CONFIGURAÇÕES E CONEXÃO (DATA LAYER)
# ==========================================
st.set_page_config(page_title="VR Software | Sales Intelligence", layout="wide")

APP_VERSION = "v1.4.2 - Architect Stable"
ADMIN_PASS_REQUIRED = "333666"

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

# FUNÇÕES DE FORMATAÇÃO (GABARITO v1.0.0)
def f_br(valor):
    if valor == 0: return "0,00"
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def f_pct(valor):
    return str(valor).replace('.', ',')

def sync_state(key_permanente, key_widget):
    st.session_state[key_permanente] = st.session_state[key_widget]

# ==========================================
# MOTOR DE DADOS E CARREGAMENTO
# ==========================================
@st.cache_data(ttl=60)
def carregar_dados_vendas():
    status_msg, status_cor = "🔴 Desconectado", "#ef4444"
    try:
        if CONN_STR:
            engine = create_engine(CONN_STR)
            df = pd.read_sql("SELECT * FROM product", engine)
            status_msg, status_cor = "PostgreSQL (Online)", "#22c55e"
            
            df.columns = [str(c).strip().lower() for c in df.columns]
            df = df.drop_duplicates(subset=['produto'], keep='last')
            
            # Type Safety: Garantir decimais para evitar erros de Mixed Types
            cols_num = ['valor', 'horas_padrao', 'adesao_vinculada', 'valor_hora_implantacao', 'typeproductid']
            for col in cols_num:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
            # Prepara Dicionários de Busca
            full = df.set_index('produto').to_dict('index')
            # Também criamos um índice por ID para a lógica relacional futura
            full_by_id = df.set_index('id').to_dict('index') if 'id' in df.columns else {}
            
            sist = {k: v for k, v in full.items() if v.get('typeproductid') == 604}
            serv = {k: v for k, v in full.items() if v.get('typeproductid') == 606 and not any(x in k.lower() for x in ['km', 'hospedagem', 'logistica', 'alimentacao'])}
            desp = {k: v for k, v in full.items() if any(x in k.lower() for x in ['km', 'hospedagem', 'logistica', 'alimentacao'])}
            
            return sist, serv, desp, full, full_by_id, status_msg, status_cor, df
    except Exception as e:
        st.error(f"Erro ao carregar banco: {e}")
    return {}, {}, {}, {}, {}, status_msg, status_cor, pd.DataFrame()

sist_db, serv_db, desp_db, full_db, full_id_db, db_status, db_cor, df_raw = carregar_dados_vendas()

# ==========================================
# ESTILIZAÇÃO CSS (INTACTA v1.0.0)
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

# ESTADO GLOBAL (Tudo Float 0.0)
if 'sel_i' not in st.session_state: st.session_state.sel_i = []
if 'sel_m' not in st.session_state: st.session_state.sel_m = []
if 'sel_d' not in st.session_state: st.session_state.sel_d = []
for nome in full_db.keys():
    if f"perm_val_{nome}" not in st.session_state: st.session_state[f"perm_val_{nome}"] = 0.0

# ==========================================
# SIDEBAR (RESTAURADA v1.0.0 + ADMIN)
# ==========================================
with st.sidebar:
    if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=180)
    tela = st.radio("Navegação:", ["Gerador de Proposta", "Consulta de Preço", "Painel Admin"])
    if tela == "Gerador de Proposta":
        st.write("---")
        mapeamento_ativo = st.toggle("Mapeamento Inteligente", value=False)
        modo_apresentacao = st.toggle("Modo Apresentação")
        perfil_venda = st.selectbox("Perfil", ["Executivo (Rua)", "CS (Base)"])
        desc = st.number_input("Desconto (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.5)
        exibir_detalhe_desc = st.toggle("Exibir Desconto na Tela", value=True)
        parcelas_setup = st.selectbox("Parcelas Setup", [1, 2, 3, 4, 5, 6, 10, 12], index=3)
    st.markdown(f'''<hr><div style="font-size:0.8rem; color:{db_cor};">● {db_status}</div><div style="font-size:0.7rem; color:#888;">{APP_VERSION}</div>''', unsafe_allow_html=True)

# --- TELA 1: PAINEL ADMIN (COM FERRAMENTA DE MIGRAÇÃO) ---
if tela == "Painel Admin":
    st.markdown('<h1 class="hero-title">BACKOFFICE</h1>', unsafe_allow_html=True)
    if st.text_input("Senha Admin:", type="password") == ADMIN_PASS_REQUIRED:
        st.success("Acesso Autorizado")
        
        st.markdown("### 🛠️ Estrutura de Dados")
        if st.button("Executar Migração: Criar Colunas de Relacionamento"):
            try:
                engine = create_engine(CONN_STR)
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE product ADD COLUMN IF NOT EXISTS id_projeto_implantacao INTEGER DEFAULT NULL;"))
                    conn.execute(text("ALTER TABLE product ADD COLUMN IF NOT EXISTS id_taxa_adesao INTEGER DEFAULT NULL;"))
                st.balloons()
                st.success("Colunas id_projeto_implantacao e id_taxa_adesao criadas com sucesso!")
            except Exception as e:
                st.error(f"Erro na migração: {e}")
        
        st.write("---")
        st.dataframe(df_raw, use_container_width=True)

# --- TELA 2: CONSULTA (SIMULADOR v1.0.0) ---
elif tela == "Consulta de Preço":
    st.markdown('<h1 class="hero-title">ANÁLISE</h1>', unsafe_allow_html=True)
    p_sel = st.selectbox("Produto:", sorted(list(full_db.keys())))
    if p_sel:
        d = full_db[p_sel]
        st.markdown(f'<div class="resumo-card"><span>Preço de Tabela</span><div class="resumo-valor">R$ {f_br(d["valor"])}</div><ul class="lista-itens"><li><span>Carga Horária</span><span class="item-detalhe">{d.get("horas_padrao", 0)}h</span></li></ul></div>', unsafe_allow_html=True)

# --- TELA 3: GERADOR (ORQUESTRADOR SENIOR) ---
elif tela == "Gerador de Proposta":
    
    # RECONCILIAÇÃO RELACIONAL (A Mente do Arquiteto)
    # Aqui o sistema busca IDs reais, ignorando nomes parecidos.
    for m_nome in st.session_state.sel_m:
        dados_pai = sist_db.get(m_nome, {})
        id_proj = dados_pai.get('id_projeto_implantacao')
        id_ades = dados_pai.get('id_taxa_adesao')
        
        # Se o banco tem o ID do Projeto vinculado
        if id_proj and id_proj in full_id_db:
            p_vinc = full_id_db[id_proj]
            nome_p = p_vinc['produto']
            if nome_p not in st.session_state.sel_i:
                st.session_state.sel_i.append(nome_p)
                st.session_state[f"perm_val_{nome_p}"] = float(p_vinc.get('horas_padrao', 1.0))

        # Se o banco tem o ID da Adesão vinculada
        if id_ades and id_ades in full_id_db:
            a_vinc = full_id_db[id_ades]
            nome_a = a_vinc['produto']
            if nome_a not in st.session_state.sel_i:
                st.session_state.sel_i.append(nome_a)
                st.session_state[f"perm_val_{nome_a}"] = 1.0

    if not modo_apresentacao:
        st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)
        if mapeamento_ativo:
            st.markdown('<div class="mapeamento-container"><h3>🛒 Mapeamento da Operação</h3>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.number_input("PDV Convencional", 0.0, step=1.0, key="m_conv")
                st.number_input("PDV Touch", 0.0, step=1.0, key="m_touch")
                st.number_input("PDV Selfcheckout", 0.0, step=1.0, key="m_self")
            with c2:
                st.selectbox("TEF", ["Não", "SiTef", "VR TEF"], key="m_tef")
                st.number_input("Semanas", 0.0, step=1.0, key="m_sem")
                st.checkbox("Migração?")
            with c3:
                st.toggle("ERP PRO", key="t_erp")
                st.toggle("G. XML", key="t_xml")
                st.toggle("Connect", key="t_conn")
            st.markdown('</div>', unsafe_allow_html=True)

        st.write("---")
        col_i, col_m, col_d = st.columns(3)
        with col_i:
            st.markdown('<div class="section-header"><span class="section-title">PROJETOS E SETUP</span></div>', unsafe_allow_html=True)
            st.session_state.sel_i = st.multiselect("Itens", list(serv_db.keys()), default=st.session_state.sel_i)
            for x in st.session_state.sel_i:
                st.number_input(f"{x}", min_value=0.0, value=float(st.session_state[f"perm_val_{x}"]), key=f"tmp_i_{x}", on_change=sync_state, args=(f"perm_val_{x}", f"tmp_i_{x}"))
        with col_m:
            st.markdown('<div class="section-header"><span class="section-title">MENSALIDADES</span></div>', unsafe_allow_html=True)
            st.session_state.sel_m = st.multiselect("Sistemas", list(sist_db.keys()), default=st.session_state.sel_m)
            for x in st.session_state.sel_m:
                st.number_input(f"{x}", min_value=0.0, value=float(st.session_state[f"perm_val_{x}"]), key=f"tmp_m_{x}", on_change=sync_state, args=(f"perm_val_{x}", f"tmp_m_{x}"))
        with col_d:
            st.markdown('<div class="section-header"><span class="section-title">LOGÍSTICA</span></div>', unsafe_allow_html=True)
            st.session_state.sel_d = st.multiselect("Despesas", list(desp_db.keys()), default=st.session_state.sel_d)
            for x in st.session_state.sel_d:
                st.number_input(f"{x}", min_value=0.0, value=float(st.session_state[f"perm_val_{x}"]), key=f"tmp_d_{x}", on_change=sync_state, args=(f"perm_val_{x}", f"tmp_d_{x}"))

    # RESUMO (IDÊNTICO v1.0.0)
    st.markdown("<h2 style='text-align:center; font-weight:800; margin-top:30px;'>RESUMO DO INVESTIMENTO</h2>", unsafe_allow_html=True)
    r1, r2, r3 = st.columns(3)
    
    t_setup, h_setup = 0.0, ""
    for n in st.session_state.sel_i:
        v = st.session_state[f"perm_val_{n}"]
        if v > 0:
            total = v * serv_db.get(n, full_db.get(n, {'valor':0}))['valor']
            t_setup += total
            h_setup += f"<li><span>{n}</span><span class='item-detalhe'>R$ {f_br(total)}</span></li>"

    with r1:
        st.markdown(f'''<div class="resumo-card"><span>Setup Inicial</span><div class="resumo-valor">R$ {f_br(t_setup)}</div><div style="font-weight:bold;">{parcelas_setup}x de R$ {f_br(t_setup/parcelas_setup)}</div><ul class="lista-itens">{h_setup if h_setup else "<li>Nenhum item</li>"}</ul></div>''', unsafe_allow_html=True)

    t_maint, h_maint = 0.0, ""
    for n in st.session_state.sel_m:
        v = st.session_state[f"perm_val_{n}"]
        if v > 0:
            total = (v * sist_db[n]['valor']) * (1 - (desc/100))
            t_maint += total
            h_maint += f"<li><span>{n}</span><span class='item-detalhe'>R$ {f_br(total)}</span></li>"
            if "erp pro" in n.lower():
                for inc in ["VR Promo", "VR Analytics"]: h_maint += f"<li class='item-incluso'><span>+ {inc}</span><span>Incluso</span></li>"

    with r2:
        st.markdown(f'''<div class="resumo-card" style="border-top-color:#2e7d32;"><span>Mensalidade</span><div class="resumo-valor" style="color:#2e7d32;">R$ {f_br(t_maint)}</div><ul class="lista-itens">{h_maint if h_maint else "<li>Nenhum</li>"}</ul></div>''', unsafe_allow_html=True)

    t_log, h_log = 0.0, ""
    for n in st.session_state.sel_d:
        v = st.session_state[f"perm_val_{n}"]
        if v > 0:
            total = v * desp_db[n]['valor']
            t_log += total
            h_log += f"<li><span>{n}</span><span class='item-detalhe'>R$ {f_br(total)}</span></li>"

    with r3:
        st.markdown(f'''<div class="resumo-card" style="border-top-color:#1976d2;"><span>Logística</span><div class="resumo-valor" style="color:#1976d2;">R$ {f_br(t_log)}</div><ul class="lista-itens">{h_log if h_log else "<li>Sem despesas</li>"}</ul></div>''', unsafe_allow_html=True)
