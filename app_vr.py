import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import urllib.parse
import os
import re

# ==========================================
# CONFIGURAÇÕES E CONEXÃO
# ==========================================
st.set_page_config(page_title="VR Software | Sales Intelligence", layout="wide")

APP_VERSION = "v1.2.7 - Auditorada"
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
# MOTOR DE DADOS (POSTGRES)
# ==========================================
def processar_dados_vr(df):
    df.columns = [str(c).strip().lower() for c in df.columns]
    df = df.drop_duplicates(subset=['produto'], keep='last')
    
    df['tipo_fluxo'] = ""
    for idx, row in df.iterrows():
        tid = row.get('typeproductid', 0)
        nome = str(row['produto']).lower()
        
        if tid == 604:
            df.at[idx, 'tipo_fluxo'] = 'sist'
        elif tid == 606:
            if any(x in nome for x in ['adesao', 'adesão']):
                df.at[idx, 'tipo_fluxo'] = 'adesao'
            elif any(x in nome for x in ['despesa', 'km', 'hospedagem', 'logistica']):
                df.at[idx, 'tipo_fluxo'] = 'desp'
            else:
                df.at[idx, 'tipo_fluxo'] = 'serv' # Projeto / Taxa Implantação
    return df

@st.cache_data(ttl=60)
def fetch_data():
    if not CONN_STR: return {}, {}, {}, {}, {}, "🔴 Erro Config", "#f00", pd.DataFrame()
    try:
        engine = create_engine(CONN_STR)
        df = pd.read_sql("SELECT * FROM product", engine)
        df = processar_dados_vr(df)
        full = df.set_index('produto').to_dict('index')
        sist = {k: v for k, v in full.items() if v['tipo_fluxo'] == 'sist'}
        serv = {k: v for k, v in full.items() if v['tipo_fluxo'] == 'serv'}
        desp = {k: v for k, v in full.items() if v['tipo_fluxo'] == 'desp'}
        ades = {k: v for k, v in full.items() if v['tipo_fluxo'] == 'adesao'}
        return sist, serv, desp, ades, full, "🟢 Postgres Ativo", "#22c55e", df
    except Exception as e:
        return {}, {}, {}, {}, {}, f"🔴 Erro: {e}", "#f00", pd.DataFrame()

sist_db, serv_db, desp_db, ades_db, full_db, db_st, db_co, df_raw = fetch_data()

# ==========================================
# ESTILO VISUAL (BLINDAGEM v1.0.0)
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
    .item-incluso { padding-left: 20px !important; color: #777; font-size: 0.82rem; font-style: italic; border-bottom: none !important; }
    </style>
""", unsafe_allow_html=True)

# FORMATADORES
def f_br(v): return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def sync_s(kp, kw): st.session_state[kp] = st.session_state[kw]

# ESTADO
if 'sel_i' not in st.session_state: st.session_state.sel_i = []
if 'sel_m' not in st.session_state: st.session_state.sel_m = []
if 'sel_d' not in st.session_state: st.session_state.sel_d = []

for k in full_db.keys():
    if f"v_{k}" not in st.session_state: st.session_state[f"v_{k}"] = 0

# SIDEBAR
with st.sidebar:
    tela = st.radio("Navegação:", ["Gerador de Proposta", "Consulta de Preço", "Admin"])
    if tela == "Gerador de Proposta":
        st.write("---")
        map_on = st.toggle("Mapeamento Inteligente", value=True)
        modo_ap = st.toggle("Modo Apresentação")
        perfil = st.selectbox("Perfil", ["Executivo (Rua)", "CS (Base)"])
        desc = st.number_input("Desconto %", 0.0, 30.0, 0.0)
        parcelas = st.selectbox("Parcelas Setup", [1,2,3,4,5,6,10,12], index=3)
    st.markdown(f'<div style="font-size:0.8rem; margin-top:50px;"><div style="color:{db_co};">● {db_st}</div>V {APP_VERSION}</div>', unsafe_allow_html=True)

# TELA: CONSULTA
if tela == "Consulta de Preço":
    st.markdown('<h1 class="hero-title">CONSULTA</h1>', unsafe_allow_html=True)
    item_c = st.selectbox("Produto", sorted(list(full_db.keys())))
    if item_c:
        st.write(full_db[item_c])

# TELA: ADMIN
elif tela == "Admin":
    if st.text_input("Senha", type="password") == ADMIN_PASS_REQUIRED:
        st.dataframe(df_raw)

# TELA: GERADOR
elif tela == "Gerador de Proposta":
    if not modo_ap:
        st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)
        
        if map_on:
            st.markdown('<div class="mapeamento-container"><h3>🛒 Mapeamento da Operação</h3>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.number_input("PDV Convencional", 0, key="m_conv")
                st.number_input("PDV Touch", 0, key="m_touch")
                st.number_input("PDV Selfcheckout", 0, key="m_self")
            with c2:
                st.selectbox("TEF", ["Não", "SiTef", "VR TEF"], key="m_tef")
                st.number_input("Semanas", 0, key="m_sem")
                st.checkbox("Migração?", key="m_mig")
                st.checkbox("Escopo?", key="m_esc")
            with c3:
                st.number_input("VR Mobile", 0, key="m_mob")
                st.toggle("VR ERP PRO", key="m_erp")
                st.toggle("G. XML", key="m_xml")
                st.toggle("Controller 360", key="m_ctrl")
                st.toggle("MasterFisco", key="m_fisco")
                st.toggle("M-Commerce", key="m_mcom")
            st.markdown('</div>', unsafe_allow_html=True)

        # SELEÇÃO MANUAL
        st.write("---")
        ci, cm, cd = st.columns(3)
        with ci:
            st.markdown('<div class="section-header"><span class="section-title">PROJETOS E IMPLANTAÇÃO</span></div>', unsafe_allow_html=True)
            st.session_state.sel_i = st.multiselect("Itens", list(serv_db.keys()), default=st.session_state.sel_i)
            for x in st.session_state.sel_i:
                st.number_input(f"{x}", min_value=0, key=f"v_i_{x}", value=st.session_state[f"v_{x}"], on_change=sync_s, args=(f"v_{x}", f"v_i_{x}"))
        with cm:
            st.markdown('<div class="section-header"><span class="section-title">MENSALIDADES</span></div>', unsafe_allow_html=True)
            st.session_state.sel_m = st.multiselect("Sistemas", list(sist_db.keys()), default=st.session_state.sel_m)
            for x in st.session_state.sel_m:
                st.number_input(f"{x}", min_value=0, key=f"v_m_{x}", value=st.session_state[f"v_{x}"], on_change=sync_s, args=(f"v_{x}", f"v_m_{x}"))
        with cd:
            st.markdown('<div class="section-header"><span class="section-title">LOGÍSTICA</span></div>', unsafe_allow_html=True)
            st.session_state.sel_d = st.multiselect("Despesas", list(desp_db.keys()), default=st.session_state.sel_d)
            for x in st.session_state.sel_d:
                st.number_input(f"{x}", min_value=0, key=f"v_d_{x}", value=st.session_state[f"v_{x}"], on_change=sync_s, args=(f"v_{x}", f"v_d_{x}"))

    # ==========================================
    # MOTOR DE CÁLCULO E REGRAS AUTOMÁTICAS
    # ==========================================
    st.markdown("<h2 style='text-align:center; font-weight:800; margin-top:30px;'>RESUMO DO INVESTIMENTO</h2>", unsafe_allow_html=True)
    r1, r2, r3 = st.columns(3)
    
    # --- CARD 1: SETUP ---
    setup_total, html_setup = 0.0, ""
    
    # Regra Conciliador: Se selecionado na mensalidade, adiciona Projeto no Setup
    if any("conciliador" in s.lower() for s in st.session_state.sel_m):
        for p_nome, p_dados in serv_db.items():
            if "projeto" in p_nome.lower() and "conciliador" in p_nome.lower():
                if p_nome not in st.session_state.sel_i: st.session_state.sel_i.append(p_nome)

    # Itens Selecionados no Card 1
    for s_nome in st.session_state.sel_i:
        qtd = st.session_state[f"v_{s_nome}"]
        if qtd > 0:
            v_unit = serv_db[s_nome]['valor']
            v_total = qtd * v_unit
            setup_total += v_total
            html_setup += f"<li><span>{s_nome}</span><span class='item-detalhe'>R$ {f_br(v_total)}</span></li>"

    # Adesão Automática (Transparência)
    for m_nome in st.session_state.sel_m:
        if st.session_state[f"v_{m_nome}"] > 0:
            # Busca adesão correspondente no banco
            for a_nome, a_dados in ades_db.items():
                # Se o nome do sistema estiver contido no nome da adesão
                if m_nome.lower() in a_nome.lower():
                    v_ad = a_dados['valor']
                    setup_total += v_ad
                    html_setup += f"<li><span>Taxa Adesão {m_nome}</span><span class='item-detalhe'>R$ {f_br(v_ad)}</span></li>"

    with r1:
        st.markdown(f'''<div class="resumo-card"><span>Investimento Setup</span><div class="resumo-valor">R$ {f_br(setup_total)}</div><div style="font-weight:bold;">{parcelas}x de R$ {f_br(setup_total/parcelas)}</div><ul class="lista-itens">{html_setup if html_setup else "<li>Nenhum item</li>"}</ul></div>''', unsafe_allow_html=True)

    # --- CARD 2: MANUTENÇÃO ---
    maint_total, html_maint = 0.0, ""
    for m_nome in st.session_state.sel_m:
        qtd = st.session_state[f"v_{m_nome}"]
        if qtd > 0:
            v_unit = sist_db[m_nome]['valor']
            v_total = (qtd * v_unit) * (1 - (desc/100))
            maint_total += v_total
            html_maint += f"<li><span>{m_nome}</span><span class='item-detalhe'>R$ {f_br(v_total)}</span></li>"
            
            # REGRA VR ERP PRO: Itens Inclusos
            if "vr erp pro" in m_nome.lower():
                html_maint += '<li class="item-incluso"><span>+ VR Promo</span><span>Incluso</span></li>'
                html_maint += '<li class="item-incluso"><span>+ VR Analytics</span><span>Incluso</span></li>'
                html_maint += '<li class="item-incluso"><span>+ VR Carteira Digital</span><span>Incluso</span></li>'

    with r2:
        st.markdown(f'''<div class="resumo-card" style="border-top-color:#2e7d32;"><span>Mensalidade</span><div class="resumo-valor" style="color:#2e7d32;">R$ {f_br(maint_total)}</div><ul class="lista-itens">{html_maint if html_maint else "<li>Nenhum</li>"}</ul></div>''', unsafe_allow_html=True)

    # --- CARD 3: LOGÍSTICA ---
    log_total, html_log = 0.0, ""
    for d_nome in st.session_state.sel_d:
        qtd = st.session_state[f"v_{d_nome}"]
        if qtd > 0:
            v_total = qtd * desp_db[d_nome]['valor']
            log_total += v_total
            html_log += f"<li><span>{d_nome}</span><span class='item-detalhe'>R$ {f_br(v_total)}</span></li>"

    with r3:
        st.markdown(f'''<div class="resumo-card" style="border-top-color:#1976d2;"><span>Logística</span><div class="resumo-valor" style="color:#1976d2;">R$ {f_br(log_total)}</div><ul class="lista-itens">{html_log if html_log else "<li>Sem despesas</li>"}</ul></div>''', unsafe_allow_html=True)
