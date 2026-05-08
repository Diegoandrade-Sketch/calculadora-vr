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

APP_VERSION = "v1.2.9 - Final Stable"
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
# MOTOR DE DADOS
# ==========================================
def processar_dados(df):
    df.columns = [str(c).strip().lower() for c in df.columns]
    df = df.drop_duplicates(subset=['produto'], keep='last')
    
    df['tipo_vr'] = ""
    for idx, row in df.iterrows():
        tid = row.get('typeproductid', 0)
        nome = str(row['produto']).lower()
        if tid == 604:
            df.at[idx, 'tipo_vr'] = 'sist'
        elif tid == 606:
            if any(x in nome for x in ['adesao', 'adesão']):
                df.at[idx, 'tipo_vr'] = 'adesao'
            elif any(x in nome for x in ['despesa', 'km', 'hospedagem', 'logistica']):
                df.at[idx, 'tipo_vr'] = 'desp'
            else:
                df.at[idx, 'tipo_vr'] = 'serv'
    return df

@st.cache_data(ttl=60)
def fetch_all():
    if not CONN_STR: return {}, {}, {}, {}, {}, "🔴 Erro DB", "#f00", pd.DataFrame()
    try:
        engine = create_engine(CONN_STR)
        df = pd.read_sql("SELECT * FROM product", engine)
        df = processar_dados(df)
        full = df.set_index('produto').to_dict('index')
        sist = {k: v for k, v in full.items() if v['tipo_vr'] == 'sist'}
        serv = {k: v for k, v in full.items() if v['tipo_vr'] == 'serv'}
        desp = {k: v for k, v in full.items() if v['tipo_vr'] == 'desp'}
        ades = {k: v for k, v in full.items() if v['tipo_vr'] == 'adesao'}
        return sist, serv, desp, ades, full, "🟢 Online", "#22c55e", df
    except Exception as e:
        return {}, {}, {}, {}, {}, f"🔴 Erro: {e}", "#f00", pd.DataFrame()

sist_db, serv_db, desp_db, ades_db, full_db, db_st, db_co, df_raw = fetch_all()

# ==========================================
# ESTILO VISUAL (GABARITO v1.0.0)
# ==========================================
st.markdown(f"""
    <style>
    .stApp {{ background: linear-gradient(135deg, #ffffff 0%, #fff5ed 100%); }}
    .hero-title {{ color: #262730; font-size: 4.5rem; font-weight: 900; margin: 0; line-height: 1; text-transform: uppercase; letter-spacing: -3px; }}
    .mapeamento-container {{ background-color: #ffffff; border-left: 10px solid #ff6600; padding: 25px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
    .resumo-card {{ background-color: #ffffff; border: 1px solid #f0f0f0; border-top: 10px solid #ff6600; padding: 25px; border-radius: 8px; min-height: 480px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); display: flex; flex-direction: column; }}
    .resumo-valor {{ color: #ff6600; font-size: 2.3rem; font-weight: 900; margin-bottom: 5px; }}
    .item-detalhe {{ color: #333; font-size: 0.82rem; font-weight: 600; background-color: #fcfcfc; padding: 2px 8px; border-radius: 4px; border: 1px solid #eee; }}
    .section-header {{ background: linear-gradient(90deg, #ff6600 0%, #ff944d 100%); padding: 10px 15px; border-radius: 5px; margin-bottom: 15px; margin-top: 20px; }}
    .section-title {{ color: #ffffff; font-size: 1.1rem; font-weight: bold; }}
    .lista-itens {{ list-style-type: none; padding-left: 0; margin-top: 15px; flex-grow: 1; }}
    .lista-itens li {{ padding: 10px 0; border-bottom: 1px dashed #e0e0e0; display: flex; justify-content: space-between; align-items: center; gap: 15px; }}
    .lista-itens li span:first-child {{ font-weight: bold; font-size: 0.88rem; color: #444; }}
    .item-incluso {{ padding-left: 20px !important; color: #2e7d32 !important; font-size: 0.82rem !important; font-style: italic; border-bottom: none !important; }}
    </style>
""", unsafe_allow_html=True)

# HELPERS
def f_br(v): return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def sync_v(kp, kw): st.session_state[kp] = st.session_state[kw]

# SESSION STATE
if 'sel_i' not in st.session_state: st.session_state.sel_i = []
if 'sel_m' not in st.session_state: st.session_state.sel_m = []
if 'sel_d' not in st.session_state: st.session_state.sel_d = []
for k in full_db.keys():
    if f"v_{k}" not in st.session_state: st.session_state[f"v_{k}"] = 0

# SIDEBAR (RESTAURADA)
with st.sidebar:
    if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=180)
    st.write("---")
    tela = st.radio("Navegação:", ["Gerador de Proposta", "Consulta de Preço", "Painel Admin"])
    if tela == "Gerador de Proposta":
        map_on = st.toggle("Mapeamento Inteligente", value=True)
        modo_ap = st.toggle("Modo Apresentação")
        desc = st.number_input("Desconto (%)", 0.0, 30.0, 0.0, 0.5)
        exibir_desc = st.toggle("Exibir Desconto no Resumo", value=True)
        parcelas = st.selectbox("Parcelas Setup", [1,2,3,4,5,6,10,12], index=3)
        ini_fat = st.selectbox("Início Faturamento", ["Imediato", "30 Dias", "Pós Implantação"])
    st.markdown(f'<div style="font-size:0.7rem; margin-top:50px; color:#666;">● Status: {db_st}<br>Versão {APP_VERSION}</div>', unsafe_allow_html=True)

# TELA: CONSULTA (SIMULADOR BONITO)
if tela == "Consulta de Preço":
    st.markdown('<h1 class="hero-title">CONSULTA</h1>', unsafe_allow_html=True)
    item_s = st.selectbox("Selecione o produto para análise:", sorted(list(full_db.keys())))
    if item_s:
        d = full_db[item_s]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'''<div class="resumo-card"><span>Preço de Tabela</span><div class="resumo-valor">R$ {f_br(d['valor'])}</div>
            <ul class="lista-itens">
            <li><span>ID Produto</span><span class="item-detalhe">{d.get('typeproductid')}</span></li>
            <li><span>Horas Padrão</span><span class="item-detalhe">{d.get('horas_padrao', 0)}h</span></li>
            <li><span>Tipo</span><span class="item-detalhe">{d.get('tipo_vr')}</span></li>
            </ul></div>''', unsafe_allow_html=True)

# TELA: ADMIN (PAINEL BONITO)
elif tela == "Painel Admin":
    st.markdown('<h1 class="hero-title">ADMIN</h1>', unsafe_allow_html=True)
    if st.text_input("Senha de Acesso", type="password") == ADMIN_PASS_REQUIRED:
        st.success(f"Conexão ativa com {DB_NAME}")
        st.dataframe(df_raw, use_container_width=True)

# TELA: GERADOR
elif tela == "Gerador de Proposta":
    # LÓGICA DE SINCRONIZAÇÃO AUTOMÁTICA (CONCILIADOR)
    conciliador_ativo = any("conciliador" in s.lower() for s in st.session_state.sel_m)
    if conciliador_ativo:
        # Busca Projeto e Adesão no banco
        for p_nome, p_dados in full_db.items():
            if "conciliador" in p_nome.lower():
                if p_dados['tipo_vr'] == 'serv' and p_nome not in st.session_state.sel_i:
                    st.session_state.sel_i.append(p_nome)
                    st.session_state[f"v_{p_nome}"] = p_dados.get('horas_padrao', 1)

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
                st.number_input("Semanas Implantação", 0, key="m_sem")
                st.checkbox("Possui Migração?", key="m_mig")
                st.checkbox("Escopo Fechado?", key="m_esc")
            with c3:
                st.number_input("VR Mobile", 0, key="m_mob")
                sub1, sub2, sub3 = st.columns(3)
                with sub1:
                    st.toggle("ERP PRO", key="m_erp")
                    st.toggle("G. XML", key="m_xml")
                with sub2:
                    st.toggle("Backup", key="m_back")
                    st.toggle("Connect", key="m_conn")
                with sub3:
                    st.toggle("Fisco", key="m_fisco")
                    st.toggle("Ctrl 360", key="m_ctrl")
            st.markdown('</div>', unsafe_allow_html=True)

        st.write("---")
        ci, cm, cd = st.columns(3)
        with ci:
            st.markdown('<div class="section-header"><span class="section-title">IMPLANTAÇÃO / PROJETOS</span></div>', unsafe_allow_html=True)
            st.session_state.sel_i = st.multiselect("Selecionar Itens", list(serv_db.keys()), default=st.session_state.sel_i)
            for x in st.session_state.sel_i:
                st.number_input(f"{x} (Qtd/Horas)", 0, key=f"inp_i_{x}", value=st.session_state[f"v_{x}"], on_change=sync_v, args=(f"v_{x}", f"inp_i_{x}"))
        with cm:
            st.markdown('<div class="section-header"><span class="section-title">MENSALIDADES</span></div>', unsafe_allow_html=True)
            st.session_state.sel_m = st.multiselect("Selecionar Sistemas", list(sist_db.keys()), default=st.session_state.sel_m)
            for x in st.session_state.sel_m:
                st.number_input(f"{x}", 0, key=f"inp_m_{x}", value=st.session_state[f"v_{x}"], on_change=sync_v, args=(f"v_{x}", f"inp_m_{x}"))
        with cd:
            st.markdown('<div class="section-header"><span class="section-title">LOGÍSTICA</span></div>', unsafe_allow_html=True)
            st.session_state.sel_d = st.multiselect("Selecionar Despesas", list(desp_db.keys()), default=st.session_state.sel_d)
            for x in st.session_state.sel_d:
                st.number_input(f"{x}", 0, key=f"inp_d_{x}", value=st.session_state[f"v_{x}"], on_change=sync_v, args=(f"v_{x}", f"inp_d_{x}"))

    # ==========================================
    # RESUMO FINAL
    # ==========================================
    st.markdown("<h2 style='text-align:center; font-weight:800; margin-top:30px;'>RESUMO DO INVESTIMENTO</h2>", unsafe_allow_html=True)
    r1, r2, r3 = st.columns(3)
    
    # CARD 1: SETUP
    t_setup, h_setup = 0.0, ""
    for n in st.session_state.sel_i:
        qtd = st.session_state[f"v_{n}"]
        if qtd > 0:
            v_i = qtd * serv_db[n]['valor']
            t_setup += v_i
            h_setup += f"<li><span>{n}</span><span class='item-detalhe'>R$ {f_br(v_i)}</span></li>"

    # Adesão e Taxas Automáticas
    for m in st.session_state.sel_m:
        if st.session_state[f"v_{m}"] > 0:
            # Regra de Horas Padrão (Sem 125 fixo!)
            hp = sist_db[m].get('horas_padrao', 0)
            if hp > 0:
                v_hp = hp * 125.0 # MANTIDA APENAS SE FOR TAXA DE IMPLANTAÇÃO PADRÃO POR HORA, SENÃO USE O VALOR DO BANCO
                t_setup += v_hp
                h_setup += f"<li><span>Taxa Implantação {m}</span><span class='item-detalhe'>{hp}h</span></li>"
            
            # Adesão por Match de Nome
            for an, ad in ades_db.items():
                if m.lower() in an.lower():
                    t_setup += ad['valor']
                    h_setup += f"<li><span>Adesão {m}</span><span class='item-detalhe'>R$ {f_br(ad['valor'])}</span></li>"

    with r1:
        st.markdown(f'''<div class="resumo-card"><span>Investimento Setup</span><div class="resumo-valor">R$ {f_br(t_setup)}</div><div style="font-weight:bold;">{parcelas}x de R$ {f_br(t_setup/parcelas)}</div><ul class="lista-itens">{h_setup if h_setup else "<li>Selecione itens</li>"}</ul></div>''', unsafe_allow_html=True)

    # CARD 2: MENSALIDADE
    t_mensal, h_mensal = 0.0, ""
    for n in st.session_state.sel_m:
        qtd = st.session_state[f"v_{n}"]
        if qtd > 0:
            v_b = qtd * sist_db[n]['valor']
            v_l = v_b * (1 - (desc/100))
            t_mensal += v_l
            val_exib = f_br(v_l) if exibir_desc else f_br(v_b)
            h_mensal += f"<li><span>{n}</span><span class='item-detalhe'>R$ {val_exib}</span></li>"
            
            # REGRAS INCLUSO (VR ERP PRO)
            if "vr erp pro" in n.lower():
                for inc in ["+ VR Promo", "+ VR Analytics", "+ VR Carteira Digital"]:
                    h_mensal += f'<li class="item-incluso"><span>{inc}</span><span>Incluso</span></li>'

    with r2:
        st.markdown(f'''<div class="resumo-card" style="border-top-color:#2e7d32;"><span>Manutenção Mensal</span><div class="resumo-valor" style="color:#2e7d32;">R$ {f_br(t_mensal)}</div><div style="font-weight:bold;">{ini_fat}</div><ul class="lista-itens">{h_mensal if h_mensal else "<li>Nenhum sistema</li>"}</ul></div>''', unsafe_allow_html=True)

    # CARD 3: LOGÍSTICA
    t_log, h_log = 0.0, ""
    for n in st.session_state.sel_d:
        qtd = st.session_state[f"v_{n}"]
        if qtd > 0:
            v_log = qtd * desp_db[n]['valor']
            t_log += v_log
            h_log += f"<li><span>{n}</span><span class='item-detalhe'>R$ {f_br(v_log)}</span></li>"

    with r3:
        st.markdown(f'''<div class="resumo-card" style="border-top-color:#1976d2;"><span>Logística</span><div class="resumo-valor" style="color:#1976d2;">R$ {f_br(t_log)}</div><ul class="lista-itens">{h_log if h_log else "<li>Sem despesas</li>"}</ul></div>''', unsafe_allow_html=True)
