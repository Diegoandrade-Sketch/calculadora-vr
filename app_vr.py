import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import urllib.parse
import os
import re

# ==========================================
# CONFIGURAÇÕES E CONEXÃO POSTGRES
# ==========================================
st.set_page_config(page_title="VR Software | Sales Intelligence", layout="wide")

APP_VERSION = "v1.3.0 - Postgres Stable"
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

# FUNÇÕES DE FORMATAÇÃO (IDÊNTICAS v1.0.0)
def f_br(valor):
    if valor == 0: return "0,00"
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def f_pct(valor):
    return str(valor).replace('.', ',')

def sync_state(key_permanente, key_widget):
    st.session_state[key_permanente] = st.session_state[key_widget]

# ==========================================
# CARREGAMENTO DE DADOS (POSTGRES)
# ==========================================
@st.cache_data(ttl=60)
def carregar_dados_vendas():
    status_msg, status_cor = "🔴 Desconectado", "#ef4444"
    try:
        if CONN_STR:
            engine = create_engine(CONN_STR)
            df = pd.read_sql("SELECT * FROM product", engine)
            status_msg, status_cor = "PostgreSQL Online", "#22c55e"
            
            df.columns = [str(c).strip().lower() for c in df.columns]
            df = df.drop_duplicates(subset=['produto'], keep='last')
            
            full = df.set_index('produto').to_dict('index')
            # Classificação por typeproductid
            sist = {k: v for k, v in full.items() if v.get('typeproductid') == 604}
            # Serviços (Projetos/Implantação) e Despesas (Logística)
            serv = {k: v for k, v in full.items() if v.get('typeproductid') == 606 and not any(x in k.lower() for x in ['adesao', 'adesão', 'km', 'hospedagem', 'deslocamento', 'logistica'])}
            desp = {k: v for k, v in full.items() if any(x in k.lower() for x in ['km', 'hospedagem', 'deslocamento', 'logistica'])}
            ades = {k: v for k, v in full.items() if any(x in k.lower() for x in ['adesao', 'adesão'])}
            
            return sist, serv, desp, ades, full, status_msg, status_cor
    except Exception as e:
        st.error(f"Erro DB: {e}")
    return {}, {}, {}, {}, {}, status_msg, status_cor

sistemas_db, servicos_db, despesas_db, adesoes_db, full_db, db_status, db_cor = carregar_dados_vendas()

# ESTILIZAÇÃO CSS (EXATA v1.0.0)
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
    if f"perm_val_{nome}" not in st.session_state: st.session_state[f"perm_val_{nome}"] = 0.0

def sync_combo():
    combo = st.session_state.tmp_combo
    if combo == "Padrão Pequeno Porte":
        st.session_state.m_pdv_conv, st.session_state.m_tef, st.session_state.m_semanas = 5, "SiTef Express", 3
        st.session_state.m_migracao, st.session_state.m_escopo, st.session_state.m_erp_pro, st.session_state.m_xml, st.session_state.m_mobile = True, True, True, True, 1

# SIDEBAR (RESTAURADA v1.0.0)
with st.sidebar:
    if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=180)
    tela = st.radio("Navegação:", ["Gerador de Proposta", "Consulta de Preço", "Admin"])
    if tela == "Gerador de Proposta":
        st.write("---")
        mapeamento_ativo = st.toggle("Mapeamento Inteligente", value=False)
        modo_apresentacao = st.toggle("Modo Apresentação")
        perfil_venda = st.selectbox("Perfil do Cliente", ["Executivo (Rua)", "CS (Base)"])
        desc = st.number_input("Desconto (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.5)
        exibir_detalhe_desc = st.toggle("Exibir Desconto na Tela", value=True)
        faturamento_sistema = st.selectbox("Início Mensalidade", ["Na assinatura", "30 dias", "60 dias", "Após implantação"])
        parcelas_setup = st.selectbox("Parcelas Setup", [1, 2, 3, 4, 5, 6, 10, 12], index=3)
        regra_logistica = st.selectbox("Faturamento Logística", ["Faturamento na assinatura", "Faturamento pós Implantação"])
    
    st.markdown("<br>" * 5, unsafe_allow_html=True)
    st.markdown(f'''<hr style="margin: 10px 0; border-color: #ddd;"><div style="font-size: 0.8rem; color: #555;"><div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;"><div style="width: 10px; height: 10px; border-radius: 50%; background-color: {db_cor};"></div><b>Base:</b> {db_status}</div><div><b>App Version:</b> {APP_VERSION}</div></div>''', unsafe_allow_html=True)

# TELA: ADMIN
if tela == "Admin":
    st.markdown('<h1 class="hero-title">ADMIN</h1>', unsafe_allow_html=True)
    if st.text_input("Acesso:", type="password") == ADMIN_PASS_REQUIRED:
        st.dataframe(df_raw, use_container_width=True)

# TELA: CONSULTA (SIMULADOR BONITO v1.0.0)
elif tela == "Consulta de Preço":
    st.markdown('<h1 class="hero-title">ANÁLISE TÉCNICA</h1>', unsafe_allow_html=True)
    p_sel = st.selectbox("Selecione o produto:", sorted(list(full_db.keys())))
    if p_sel:
        d = full_db[p_sel]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="resumo-card"><span>Dados de Tabela</span><div class="resumo-valor">R$ {f_br(d["valor"])}</div><ul class="lista-itens"><li><span>Tipo</span><span class="item-detalhe">{d.get("tipo", "N/A")}</span></li><li><span>Horas Padrão</span><span class="item-detalhe">{d.get("horas_padrao", 0)}h</span></li></ul></div>', unsafe_allow_html=True)

# TELA: GERADOR
elif tela == "Gerador de Proposta":
    
    # --- SINCRONIZAÇÃO CONCILIADOR (REGRA DE NEGÓCIO) ---
    if any("conciliador" in s.lower() for s in st.session_state.sel_m):
        for p_nome, p_dados in full_db.items():
            if "conciliador" in p_nome.lower():
                if p_nome in servicos_db and p_nome not in st.session_state.sel_i:
                    st.session_state.sel_i.append(p_nome)
                    st.session_state[f"perm_val_{p_nome}"] = float(p_dados.get('horas_padrao', 0))

    def aplicar_mapeamento():
        pdv_map = {"VR PDV Convencional": st.session_state.m_pdv_conv, "PDV Touchscreen": st.session_state.m_pdv_touch, "PDV Selfcheckout": st.session_state.m_pdv_self}
        for p, qtd in pdv_map.items():
            if p in sistemas_db:
                st.session_state[f"perm_val_{p}"] = float(qtd)
                if qtd > 0 and p not in st.session_state.sel_m: st.session_state.sel_m.append(p)
        
        exp_map = {"VR ERP PRO": st.session_state.m_erp_pro, "Gerenciador XML": st.session_state.m_xml, "VR Backup": st.session_state.m_backup, "VR Connect (Android/IOS)": st.session_state.m_connect, "VR Controller 360": st.session_state.m_controller, "VR Cartaz": st.session_state.m_cartaz, "E-Commerce": st.session_state.m_ecommerce, "VR MasterFisco Brasil": st.session_state.m_masterfisco, "M-Commerce": st.session_state.m_app}
        for item, ativo in exp_map.items():
            if item in sistemas_db:
                st.session_state[f"perm_val_{item}"] = 1.0 if ativo else 0.0
                if ativo and item not in st.session_state.sel_m: st.session_state.sel_m.append(item)

    if not modo_apresentacao:
        st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)
        if mapeamento_ativo:
            st.markdown('<div class="mapeamento-container"><h3 style="margin:0; color:#ff6600;">🛒 Mapeamento da Operação</h3></div>', unsafe_allow_html=True)
            st.selectbox("Combo Rápido", ["Montar Manualmente", "Padrão Pequeno Porte"], key="tmp_combo", on_change=sync_combo)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.number_input("PDV Convencional", min_value=0, key="tmp_pdv_conv", value=int(st.session_state.m_pdv_conv), on_change=sync_state, args=("m_pdv_conv", "tmp_pdv_conv"))
                st.number_input("PDV Touch", min_value=0, key="tmp_pdv_touch", value=int(st.session_state.m_pdv_touch), on_change=sync_state, args=("m_pdv_touch", "tmp_pdv_touch"))
                st.number_input("PDV Selfcheckout", min_value=0, key="tmp_pdv_self", value=int(st.session_state.m_pdv_self), on_change=sync_state, args=("m_pdv_self", "tmp_pdv_self"))
            with c2:
                st.selectbox("TEF", ["Não utiliza", "SiTef Express", "VR TEF"], key="tmp_tef", index=["Não utiliza", "SiTef Express", "VR TEF"].index(st.session_state.m_tef), on_change=sync_state, args=("m_tef", "tmp_tef"))
                st.number_input("Semanas", min_value=0, key="tmp_semanas", value=int(st.session_state.m_semanas), on_change=sync_state, args=("m_semanas", "tmp_semanas"))
                st.checkbox("Migração?", key="tmp_migracao", value=st.session_state.m_migracao, on_change=sync_state, args=("m_migracao", "tmp_migracao"))
                st.checkbox("Escopo?", key="tmp_escopo", value=st.session_state.m_escopo, on_change=sync_state, args=("m_escopo", "tmp_escopo"))
            with c3:
                st.number_input("VR Mobile", min_value=0, key="tmp_mobile", value=int(st.session_state.m_mobile), on_change=sync_state, args=("m_mobile", "tmp_mobile"))
                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    st.toggle("ERP PRO", key="tmp_erp_pro", value=st.session_state.m_erp_pro, on_change=sync_state, args=("m_erp_pro", "tmp_erp_pro"))
                    st.toggle("G. XML", key="tmp_xml", value=st.session_state.m_xml, on_change=sync_state, args=("m_xml", "tmp_xml"))
                    st.toggle("Connect", key="tmp_connect", value=st.session_state.m_connect, on_change=sync_state, args=("m_connect", "tmp_connect"))
                with sc2:
                    st.toggle("Backup", key="tmp_backup", value=st.session_state.m_backup, on_change=sync_state, args=("m_backup", "tmp_backup"))
                    st.toggle("Cartaz", key="tmp_cartaz", value=st.session_state.m_cartaz, on_change=sync_state, args=("m_cartaz", "tmp_cartaz"))
                    st.toggle("E-Com", key="tmp_ecommerce", value=st.session_state.m_ecommerce, on_change=sync_state, args=("m_ecommerce", "tmp_ecommerce"))
                with sc3:
                    st.toggle("C. 360", key="tmp_controller", value=st.session_state.m_controller, on_change=sync_state, args=("m_controller", "tmp_controller"))
                    st.toggle("Fisco", key="tmp_masterfisco", value=st.session_state.m_masterfisco, on_change=sync_state, args=("m_masterfisco", "tmp_masterfisco"))
                    st.toggle("M-Com", key="tmp_app", value=st.session_state.m_app, on_change=sync_state, args=("m_app", "tmp_app"))
                st.button("✨ Aplicar Inteligência", on_click=aplicar_mapeamento, use_container_width=True)
            st.markdown("---")

        # --- PARTE 2: INCLUSÃO MANUAL (FIX MixedNumericTypes) ---
        col_i, col_m, col_d = st.columns(3) if perfil_venda == "Executivo (Rua)" else (*st.columns(2), None)
        with col_i:
            st.markdown('<div class="section-header"><span class="section-title">PROJETOS E SETUP</span></div>', unsafe_allow_html=True)
            st.session_state.sel_i = st.multiselect("Itens", list(servicos_db.keys()), default=[s for s in st.session_state.sel_i if s in servicos_db])
            for i in st.session_state.sel_i:
                st.number_input(f"{i}", min_value=0.0, value=float(st.session_state[f"perm_val_{i}"]), key=f"tmp_i_{i}", on_change=sync_state, args=(f"perm_val_{i}", f"tmp_i_{i}"))
        with col_m:
            st.markdown('<div class="section-header"><span class="section-title">MENSALIDADES</span></div>', unsafe_allow_html=True)
            st.session_state.sel_m = st.multiselect("Sistemas", list(sistemas_db.keys()), default=[s for s in st.session_state.sel_m if s in sistemas_db])
            for i in st.session_state.sel_m:
                st.number_input(f"{i}", min_value=0.0, value=float(st.session_state[f"perm_val_{i}"]), key=f"tmp_m_{i}", on_change=sync_state, args=(f"perm_val_{i}", f"tmp_m_{i}"))
        if col_d:
            with col_d:
                st.markdown('<div class="section-header"><span class="section-title">LOGÍSTICA</span></div>', unsafe_allow_html=True)
                st.session_state.sel_d = st.multiselect("Despesas", list(despesas_db.keys()), default=[s for s in st.session_state.sel_d if s in despesas_db])
                for i in st.session_state.sel_d:
                    st.number_input(f"{i}", min_value=0.0, value=float(st.session_state[f"perm_val_{i}"]), key=f"tmp_d_{i}", on_change=sync_state, args=(f"perm_val_{i}", f"tmp_d_{i}"))

    # --- PARTE 3: CARD DE RESUMO ---
    st.markdown("<h2 style='text-align:center; font-weight:800; margin-top:30px;'>RESUMO DO INVESTIMENTO</h2>", unsafe_allow_html=True)
    res_cols = st.columns(3) if perfil_venda == "Executivo (Rua)" else st.columns([1, 2, 2, 1])[1:3]

    total_setup, html_setup = 0.0, ""
    for s_nome in st.session_state.sel_i:
        qtd = st.session_state[f"perm_val_{s_nome}"]
        if qtd > 0:
            v_item = qtd * servicos_db[s_nome]['valor']
            total_setup += v_item
            html_setup += f"<li><span>{s_nome}</span><span class='item-detalhe'>R$ {f_br(v_item)}</span></li>"

    # Regras de Adesão e Horas Padrão (Transparentes)
    for m_nome in st.session_state.sel_m:
        if st.session_state[f"perm_val_{m_nome}"] > 0:
            d = sistemas_db[m_nome]
            h_pad = d.get('horas_padrao', 0)
            if h_pad > 0:
                v_h = h_pad * 125.0 # Taxa padrão VR
                total_setup += v_h
                html_setup += f"<li><span>Taxa Implantação {m_nome}</span><span class='item-detalhe'>{h_pad}h x R$ 125,00</span></li>"
            
            # Busca Adesão correspondente
            for a_nome, a_dados in adesoes_db.items():
                if m_nome.lower() in a_nome.lower():
                    total_setup += a_dados['valor']
                    html_setup += f"<li><span>Adesão {m_nome}</span><span class='item-detalhe'>R$ {f_br(a_dados['valor'])}</span></li>"

    with res_cols[0]:
        st.markdown(f'<div class="resumo-card"><span>Investimento Setup</span><div class="resumo-valor">R$ {f_br(total_setup)}</div><div style="font-weight:bold;">{parcelas_setup}x de R$ {f_br(total_setup/parcelas_setup)}</div><ul class="lista-itens">{html_setup if html_setup else "<li>Nenhum item</li>"}</ul></div>', unsafe_allow_html=True)

    with res_cols[1]:
        t_bruto = sum(st.session_state[f"perm_val_{i}"] * sistemas_db[i]["valor"] for i in st.session_state.sel_m if i in sistemas_db)
        t_liq = t_bruto * (1 - (desc/100))
        html_m = ""
        for i in st.session_state.sel_m:
            v_total_m = st.session_state[f"perm_val_{i}"] * sistemas_db[i]["valor"]
            detalhe = f_br(v_total_m * (1 - (desc/100))) if exibir_detalhe_desc else f_br(v_total_m)
            html_m += f"<li><span>{i}</span><span class='item-detalhe'>R$ {detalhe}</span></li>"
            if "erp pro" in i.lower():
                for ex in ["VR Promo", "VR Analytics", "VR Carteira Digital"]:
                    html_m += f"<li class='item-incluso'><span>+ {ex}</span><span>Incluso</span></li>"
        st.markdown(f'<div class="resumo-card" style="border-top-color:#2e7d32;"><span>Manutenção Mensal</span><div class="resumo-valor" style="color:#2e7d32;">R$ {f_br(t_liq)}</div><div style="font-weight:bold;">Início: {faturamento_sistema}</div><ul class="lista-itens">{html_m if html_m else "<li>Nenhum</li>"}</ul></div>', unsafe_allow_html=True)

    if perfil_venda == "Executivo (Rua)":
        with res_cols[2]:
            t_log = sum(st.session_state[f"perm_val_{i}"] * despesas_db[i]["valor"] for i in st.session_state.sel_d if i in despesas_db)
            html_d = "".join([f"<li><span>{i}</span><span class='item-detalhe'>R$ {f_br(st.session_state[f'perm_val_{i}'] * despesas_db[i]['valor'])}</span></li>" for i in st.session_state.sel_d if i in despesas_db])
            st.markdown(f'<div class="resumo-card" style="border-top-color:#1976d2;"><span>Logística</span><div class="resumo-valor" style="color:#1976d2;">R$ {f_br(t_log)}</div><ul class="lista-itens">{html_d if html_d else "<li>Sem despesas</li>"}</ul></div>', unsafe_allow_html=True)
