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

# FUNÇÕES DE FORMATAÇÃO (GABARITO v1.0.0)
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
            
            # Filtros por Regra de Negócio VR
            sist = {k: v for k, v in full.items() if v.get('typeproductid') == 604}
            serv = {k: v for k, v in full.items() if v.get('typeproductid') == 606 and not any(x in k.lower() for x in ['adesao', 'adesão', 'km', 'hospedagem', 'deslocamento', 'logistica', 'alimentacao'])}
            desp = {k: v for k, v in full.items() if any(x in k.lower() for x in ['km', 'hospedagem', 'deslocamento', 'logistica', 'alimentacao'])}
            ades = {k: v for k, v in full.items() if any(x in k.lower() for x in ['adesao', 'adesão'])}
            
            return sist, serv, desp, ades, full, status_msg, status_cor
    except Exception as e:
        st.error(f"Erro DB: {e}")
    return {}, {}, {}, {}, {}, status_msg, status_cor

sistemas_db, servicos_db, despesas_db, adesoes_db, full_db, db_status, db_cor = carregar_dados_vendas()

# ESTILIZAÇÃO CSS (RESTAURAÇÃO TOTAL v1.0.0)
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #ffffff 0%, #fff5ed 100%); }
    .hero-title { color: #262730; font-size: 4.5rem; font-weight: 900; margin: 0; line-height: 1; text-transform: uppercase; letter-spacing: -3px; }
    .mapeamento-container { background-color: #ffffff; border-left: 10px solid #ff6600; padding: 25px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .resumo-card { background-color: #ffffff; border: 1px solid #f0f0f0; border-top: 10px solid #ff6600; padding: 25px; border-radius: 8px; min-height: 480px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); display: flex; flex-direction: column; }
    .resumo-valor { color: #ff6600; font-size: 2.3rem; font-weight: 900; margin-bottom: 5px; }
    .resumo-label { color: #262730; font-size: 1rem; font-weight: 700; text-transform: uppercase; }
    .item-detalhe { color: #333; font-size: 0.82rem; font-weight: 600; background-color: #fcfcfc; padding: 2px 8px; border-radius: 4px; border: 1px solid #eee; white-space: nowrap; }
    .section-header { background: linear-gradient(90deg, #ff6600 0%, #ff944d 100%); padding: 10px 15px; border-radius: 5px; margin-bottom: 15px; margin-top: 20px; }
    .section-title { color: #ffffff; font-size: 1.1rem; font-weight: bold; margin: 0; }
    .lista-itens { list-style-type: none; padding-left: 0; margin-top: 10px; flex-grow: 1; }
    .lista-itens li { padding: 8px 0; border-bottom: 1px dashed #e0e0e0; display: flex; justify-content: space-between; align-items: center; gap: 15px; }
    .lista-itens li span:first-child { font-weight: bold; font-size: 0.88rem; color: #444; }
    .item-incluso { padding-left: 20px !important; color: #777; font-size: 0.85rem; font-style: italic; border-bottom: none !important; }
    </style>
    """, unsafe_allow_html=True)

# ESTADO GLOBAL
if 'sel_i' not in st.session_state: st.session_state.sel_i = []
if 'sel_m' not in st.session_state: st.session_state.sel_m = []
if 'sel_d' not in st.session_state: st.session_state.sel_d = []
for k in full_db.keys():
    if f"v_{k}" not in st.session_state: st.session_state[f"v_{k}"] = 0.0

# SIDEBAR (RESTAURADA TOTAL v1.0.0)
with st.sidebar:
    if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=180)
    tela = st.radio("Navegação:", ["Gerador de Proposta", "Consulta de Preço", "Admin"])
    if tela == "Gerador de Proposta":
        st.write("---")
        map_on = st.toggle("Mapeamento Inteligente", value=True)
        modo_ap = st.toggle("Modo Apresentação")
        perfil = st.selectbox("Perfil", ["Executivo (Rua)", "CS (Base)"])
        desc_global = st.number_input("Desconto (%)", 0.0, 30.0, 0.0, 0.5)
        exibir_detalhe_desc = st.toggle("Exibir Desconto na Tela", value=True)
        parcelas_setup = st.selectbox("Parcelas Setup", [1,2,3,4,5,6,10,12], index=3)
        fat_mensal = st.selectbox("Início Mensalidade", ["Na assinatura", "30 dias", "Após implantação"])
    st.markdown(f'''<hr style="margin: 50px 0 10px 0; border-color: #ddd;"><div style="font-size: 0.8rem; color: #555;"><div style="display: flex; align-items: center; gap: 8px;"><div style="width: 10px; height: 10px; border-radius: 50%; background-color: {db_cor};"></div><b>Base:</b> {db_status}</div><div><b>Versão:</b> {APP_VERSION}</div></div>''', unsafe_allow_html=True)

# TELA: ADMIN
if tela == "Admin":
    st.markdown('<h1 class="hero-title">ADMIN</h1>', unsafe_allow_html=True)
    if st.text_input("Acesso:", type="password") == ADMIN_PASS_REQUIRED:
        st.success(f"Conexão ativa com o banco. Total de itens: {len(df_raw)}")
        st.dataframe(df_raw, use_container_width=True)

# TELA: CONSULTA (SIMULADOR v1.0.0)
elif tela == "Consulta de Preço":
    st.markdown('<h1 class="hero-title">ANÁLISE</h1>', unsafe_allow_html=True)
    item_c = st.selectbox("Selecione o produto:", sorted(list(full_db.keys())))
    if item_c:
        d = full_db[item_c]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'''<div class="resumo-card"><span class="resumo-label">Dados de Tabela</span><div class="resumo-valor">R$ {f_br(d['valor'])}</div>
            <ul class="lista-itens">
            <li><span>ID Sistema</span><span class="item-detalhe">{d.get('typeproductid')}</span></li>
            <li><span>Horas Padrão</span><span class="item-detalhe">{d.get('horas_padrao', 0)}h</span></li>
            </ul></div>''', unsafe_allow_html=True)

# TELA: GERADOR
elif tela == "Gerador de Proposta":
    # --- SINCRONIZAÇÃO INTELIGENTE (REGRA CONCILIADOR) ---
    if any("conciliador" in s.lower() for s in st.session_state.sel_m):
        for nome_item, dados_item in full_db.items():
            if "conciliador" in nome_item.lower():
                # Adiciona Projeto (Serviço)
                if dados_item['typeproductid'] == 606 and "adesao" not in nome_item.lower():
                    if nome_item not in st.session_state.sel_i: 
                        st.session_state.sel_i.append(nome_item)
                        st.session_state[f"v_{nome_item}"] = float(dados_item.get('horas_padrao', 0))
                # Adiciona Adesão
                if "adesao" in nome_item.lower() and nome_item not in st.session_state.sel_i:
                    st.session_state.sel_i.append(nome_item)
                    st.session_state[f"v_{nome_item}"] = 1.0

    if not modo_ap:
        st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)
        
        if map_on:
            st.markdown('<div class="mapeamento-container"><h3>🛒 Mapeamento da Operação</h3>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.number_input("PDV Convencional", 0, key="tmp_conv", value=int(st.session_state[f"v_VR PDV Convencional"]) if "VR PDV Convencional" in full_db else 0)
                st.number_input("PDV Touch", 0, key="tmp_touch")
                st.number_input("PDV Selfcheckout", 0, key="tmp_self")
            with c2:
                st.selectbox("TEF", ["Não utiliza", "SiTef", "VR TEF"], key="tmp_tef")
                st.number_input("Semanas", 0, key="tmp_sem")
                st.checkbox("Migração?", key="tmp_mig")
                st.checkbox("Escopo?", key="tmp_esc")
            with c3:
                st.number_input("VR Mobile", 0, key="tmp_mob")
                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    st.toggle("ERP PRO", key="t_erp")
                    st.toggle("G. XML", key="t_xml")
                    st.toggle("Connect", key="t_conn")
                with sc2:
                    st.toggle("Backup", key="t_back")
                    st.toggle("Cartaz", key="t_cart")
                    st.toggle("E-Com", key="t_ecom")
                with sc3:
                    st.toggle("C. 360", key="t_ctrl")
                    st.toggle("Fisco", key="t_fisco")
                    st.toggle("M-Com", key="t_mcom")
            st.markdown('</div>', unsafe_allow_html=True)

        st.write("---")
        # --- COLUNAS DE SELEÇÃO MANUAL (FIX MixedNumericTypes) ---
        ci, cm, cd = st.columns(3)
        with ci:
            st.markdown('<div class="section-header"><span class="section-title">PROJETOS E SETUP</span></div>', unsafe_allow_html=True)
            st.session_state.sel_i = st.multiselect("Itens", list(servicos_db.keys()) + list(adesoes_db.keys()), default=st.session_state.sel_i)
            for x in st.session_state.sel_i:
                st.number_input(f"{x}", min_value=0.0, value=float(st.session_state[f"v_{x}"]), key=f"inp_i_{x}", on_change=sync_v, args=(f"v_{x}", f"inp_i_{x}"))
        with cm:
            st.markdown('<div class="section-header"><span class="section-title">MENSALIDADES</span></div>', unsafe_allow_html=True)
            st.session_state.sel_m = st.multiselect("Sistemas", list(sistemas_db.keys()), default=st.session_state.sel_m)
            for x in st.session_state.sel_m:
                st.number_input(f"{x}", min_value=0.0, value=float(st.session_state[f"v_{x}"]), key=f"inp_m_{x}", on_change=sync_v, args=(f"v_{x}", f"inp_m_{x}"))
        with cd:
            st.markdown('<div class="section-header"><span class="section-title">LOGÍSTICA</span></div>', unsafe_allow_html=True)
            st.session_state.sel_d = st.multiselect("Despesas", list(despesas_db.keys()), default=st.session_state.sel_d)
            for x in st.session_state.sel_d:
                st.number_input(f"{x}", min_value=0.0, value=float(st.session_state[f"v_{x}"]), key=f"inp_d_{x}", on_change=sync_v, args=(f"v_{x}", f"inp_d_{x}"))

    # ==========================================
    # RESUMO DO INVESTIMENTO (REGRAS REAIS)
    # ==========================================
    st.markdown("<h2 style='text-align:center; font-weight:800; margin-top:30px;'>RESUMO DO INVESTIMENTO</h2>", unsafe_allow_html=True)
    r1, r2, r3 = st.columns(3)
    
    # CARD 1: SETUP (SEM TAXAS INVENTADAS)
    t_setup, html_setup = 0.0, ""
    for n in st.session_state.sel_i:
        qtd = st.session_state[f"v_{n}"]
        if qtd > 0:
            # Puxa o valor real do banco (Ex: 193.92) e multiplica pela qtd (Ex: 12.0)
            valor_banco = full_db[n]['valor']
            total_item = qtd * valor_banco
            t_setup += total_item
            html_setup += f"<li><span>{n}</span><span class='item-detalhe'>R$ {f_br(total_item)}</span></li>"

    with r1:
        st.markdown(f'''<div class="resumo-card"><span class="resumo-label">Investimento Setup</span><div class="resumo-valor">R$ {f_br(t_setup)}</div><div style="font-weight:bold;">{parcelas_setup}x de R$ {f_br(t_setup/parcelas_setup)}</div><ul class="lista-itens">{html_setup if html_setup else "<li>Nenhum item</li>"}</ul></div>''', unsafe_allow_html=True)

    # CARD 2: MANUTENÇÃO (REGRAS INCLUSO VR ERP PRO)
    t_maint, html_maint = 0.0, ""
    for n in st.session_state.sel_m:
        qtd = st.session_state[f"v_{n}"]
        if qtd > 0:
            v_b = qtd * sistemas_db[n]['valor']
            v_l = v_b * (1 - (desc_global/100))
            t_maint += v_l
            detalhe = f_br(v_l) if exibir_detalhe_desc else f_br(v_b)
            html_maint += f"<li><span>{n}</span><span class='item-detalhe'>R$ {detalhe}</span></li>"
            
            if "vr erp pro" in n.lower():
                for inc in ["VR Promo", "VR Analytics", "VR Carteira Digital"]:
                    html_maint += f'<li class="item-incluso"><span>+ {inc}</span><span>Incluso</span></li>'

    with r2:
        st.markdown(f'''<div class="resumo-card" style="border-top-color:#2e7d32;"><span class="resumo-label">Mensalidade</span><div class="resumo-valor" style="color:#2e7d32;">R$ {f_br(t_maint)}</div><div style="font-weight:bold;">Início: {fat_mensal}</div><ul class="lista-itens">{html_maint if html_maint else "<li>Nenhum</li>"}</ul></div>''', unsafe_allow_html=True)

    # CARD 3: LOGÍSTICA
    t_log, html_log = 0.0, ""
    for n in st.session_state.sel_d:
        qtd = st.session_state[f"v_{n}"]
        if qtd > 0:
            v_l = qtd * despesas_db[n]['valor']
            t_log += v_l
            html_log += f"<li><span>{n}</span><span class='item-detalhe'>R$ {f_br(v_l)}</span></li>"

    with r3:
        st.markdown(f'''<div class="resumo-card" style="border-top-color:#1976d2;"><span class="resumo-label">Logística</span><div class="resumo-valor" style="color:#1976d2;">R$ {f_br(t_log)}</div><ul class="lista-itens">{html_log if html_log else "<li>Sem despesas</li>"}</ul></div>''', unsafe_allow_html=True)
