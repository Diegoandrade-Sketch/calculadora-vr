import streamlit as st
import pandas as pd
import os

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="VR Software | Sales Intelligence", layout="wide")

# --- DATA SOURCE ---
EXCEL_FILE = "tabela_preco_chat.xlsx"

# --- FUNÇÕES DE APOIO ---
def limpar_valor(valor):
    if pd.isna(valor) or str(valor).strip() == "": return 0.0
    try:
        v = str(valor).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        return float(v)
    except: return 0.0

@st.cache_data(ttl=60)
def carregar_dados_vendas():
    try:
        if os.path.exists(EXCEL_FILE):
            df = pd.read_excel(EXCEL_FILE)
            df.columns = [str(c).strip() for c in df.columns]
            df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
            df['Valor'] = df['Valor'].apply(limpar_valor)
            
            sist = df[df['Tipo'].str.contains('Sist', case=False, na=False)].set_index('Produto').to_dict('index')
            serv = df[df['Tipo'].str.contains('Serv', case=False, na=False)].set_index('Produto').to_dict('index')
            desp = df[df['Tipo'].str.contains('Desp', case=False, na=False)].set_index('Produto').to_dict('index')
            full = df.set_index('Produto').to_dict('index')
            return sist, serv, desp, full
        return {}, {}, {}, {}
    except: return {}, {}, {}, {}

sistemas_db, servicos_db, despesas_db, full_db = carregar_dados_vendas()

# 2. ESTILIZAÇÃO CSS
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #ffffff 0%, #fff5ed 100%); }
    .hero-title { color: #262730; font-size: 3.5rem; font-weight: 900; margin: 0; line-height: 1; text-transform: uppercase; letter-spacing: -3px; }
    .mapeamento-container { background-color: #ffffff; border-left: 10px solid #ff6600; padding: 20px; border-radius: 8px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .resumo-card { background-color: #ffffff; border: 1px solid #f0f0f0; border-top: 8px solid #ff6600; padding: 25px; border-radius: 8px; min-height: 450px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); display: flex; flex-direction: column; }
    .resumo-valor { color: #ff6600; font-size: 2.3rem; font-weight: 900; margin-bottom: 5px; }
    .item-detalhe { color: #333; font-size: 0.95rem; font-weight: 700; background-color: #fcfcfc; padding: 2px 8px; border-radius: 4px; border: 1px solid #eee; }
    .section-header { background: linear-gradient(90deg, #ff6600 0%, #ff944d 100%); padding: 8px 15px; border-radius: 5px; margin-bottom: 15px; margin-top: 20px; }
    .section-title { color: #ffffff; font-size: 1.1rem; font-weight: bold; margin: 0; }
    .lista-itens { list-style-type: none; padding-left: 0; margin-top: 10px; flex-grow: 1; }
    .lista-itens li { padding: 8px 0; border-bottom: 1px dashed #e0e0e0; display: flex; justify-content: space-between; align-items: center; gap: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. ESTADO GLOBAL ---
# Inicializa apenas se não existir para não causar "limpezas" acidentais
if 'sel_i' not in st.session_state: st.session_state.sel_i = []
if 'sel_m' not in st.session_state: st.session_state.sel_m = []

# Inicializa campos de mapeamento
map_fields = ['m_pdv_conv', 'm_pdv_touch', 'm_pdv_self', 'm_tef', 'm_semanas', 'm_migracao']
for k in map_fields:
    if k not in st.session_state:
        st.session_state[k] = 0 if 'pdv' in k or 'semanas' in k else "Não utiliza" if 'tef' in k else False

# Dicionário de quantidades manual
if 'quantidades' not in st.session_state:
    st.session_state.quantidades = {p: 0 for p in full_db.keys()}

# FUNÇÃO LIMPAR TUDO (RESTAURADA E SEGURA)
def limpar_tudo():
    st.session_state.sel_i = []
    st.session_state.sel_m = []
    for k in map_fields:
        st.session_state[k] = 0 if 'pdv' in k or 'semanas' in k else "Não utiliza" if 'tef' in k else False
    for p in full_db.keys():
        st.session_state.quantidades[p] = 0

# --- 4. LÓGICA DE INTELIGÊNCIA ---
def aplicar_mapeamento():
    # 1. Regra de PDVs
    pdvs = {"VR PDV Convencional": st.session_state.m_pdv_conv, "PDV Touchscreen": st.session_state.m_pdv_touch, "PDV Selfcheckout": st.session_state.m_pdv_self}
    for p, qtd in pdvs.items():
        if p in sistemas_db and qtd > 0:
            st.session_state.quantidades[p] = qtd
            if p not in st.session_state.sel_m: st.session_state.sel_m.append(p)

    # 2. TEF
    total = sum(pdvs.values())
    if st.session_state.m_tef == "SiTef Express":
        tef_key = "SiTef Express até 3 PDVs" if total <= 3 else "SiTef Express até 6 PDVs" if total <= 6 else "SiTef Express até 8 PDVs" if total <= 8 else "SiTef Express a partir de 9 PDVs"
        if tef_key in sistemas_db:
            st.session_state.quantidades[tef_key] = 1
            if tef_key not in st.session_state.sel_m: st.session_state.sel_m.append(tef_key)

    # 3. Semanas
    sem = st.session_state.m_semanas
    if sem > 0:
        if "Implantação e Treinamento" in servicos_db:
            st.session_state.quantidades["Implantação e Treinamento"] = sem * 44
            if "Implantação e Treinamento" not in st.session_state.sel_i: st.session_state.sel_i.append("Implantação e Treinamento")
        if "Alimentacao" in despesas_db: st.session_state.quantidades["Alimentacao"] = sem * 10
        if "Hospedagem" in despesas_db: st.session_state.quantidades["Hospedagem"] = sem * 4

# --- 5. MENU LATERAL ---
with st.sidebar:
    if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=180)
    tela = st.radio("Navegação:", ["Gerador de Proposta", "Consulta de Preço"])
    st.write("---")
    if tela == "Gerador de Proposta":
        st.markdown('**Configurações**')
        mapeamento_ativo = st.toggle("Mapeamento Inteligente", value=False)
        perfil_venda = st.selectbox("Perfil Cliente", ["Executivo (Rua)", "CS (Base)"])
        desc = st.number_input("Desconto (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.5)
        exibir_detalhe_desc = st.toggle("Exibir Desconto na Tela", value=True)
        parcelas_setup = st.selectbox("Parcelas Setup", [1, 2, 3, 4, 5, 6], index=3)

# --- 6. TELA PRINCIPAL ---
if tela == "Gerador de Proposta":
    st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)
    
    if mapeamento_ativo:
        st.markdown('<div class="mapeamento-container"><h3>🛒 Assistente de Mapeamento</h3></div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.number_input("Qtd PDV Convencional", min_value=0, key="m_pdv_conv")
            st.number_input("Qtd PDV Selfcheckout", min_value=0, key="m_pdv_self")
        with c2:
            st.selectbox("Solução de TEF", ["Não utiliza", "SiTef Express", "VR TEF"], key="m_tef")
            st.number_input("Semanas Implantação", min_value=0, key="m_semanas")
        with c3:
            st.checkbox("Migração de Banco?", key="m_migracao")
            st.button("✨ Aplicar ao Orçamento", on_click=aplicar_mapeamento, use_container_width=True)
            st.button("🗑️ Limpar Tudo", on_click=limpar_tudo, use_container_width=True)
        st.markdown("---")

    # SELEÇÃO MANUAL - TOTALMENTE DESBLOQUEADA
    col_i, col_m, col_d = st.columns(3) if perfil_venda == "Executivo (Rua)" else (*st.columns(2), None)
    
    with col_i:
        st.markdown('<div class="section-header"><span class="section-title">IMPLANTAÇÃO</span></div>', unsafe_allow_html=True)
        st.session_state.sel_i = st.multiselect("Selecione os Serviços:", list(servicos_db.keys()), key="ms_i")
        for i in st.session_state.sel_i:
            st.session_state.quantidades[i] = st.number_input(f"Horas: {i}", min_value=0, value=st.session_state.quantidades.get(i, 0), key=f"q_{i}")

    with col_m:
        st.markdown('<div class="section-header"><span class="section-title">MENSALIDADE</span></div>', unsafe_allow_html=True)
        st.session_state.sel_m = st.multiselect("Selecione os Sistemas:", list(sistemas_db.keys()), key="ms_m")
        for i in st.session_state.sel_m:
            st.session_state.quantidades[i] = st.number_input(f"Qtd: {i}", min_value=0, value=st.session_state.quantidades.get(i, 0), key=f"q_{i}")

    if col_d:
        with col_d:
            st.markdown('<div class="section-header"><span class="section-title">LOGÍSTICA</span></div>', unsafe_allow_html=True)
            for i in despesas_db.keys():
                st.session_state.quantidades[i] = st.number_input(f"{i} (un)", min_value=0, value=st.session_state.quantidades.get(i, 0), key=f"q_{i}")

    # CÁLCULOS FINAIS
    t_imp = sum(st.session_state.quantidades[i] * servicos_db[i]["Valor"] for i in st.session_state.sel_i if i in servicos_db)
    t_men_bruto = sum(st.session_state.quantidades[i] * sistemas_db[i]["Valor"] for i in st.session_state.sel_m if i in sistemas_db)
    t_desp = sum(st.session_state.quantidades[i] * despesas_db[i]["Valor"] for i in despesas_db.keys())
    t_men_liq = t_men_bruto * (1 - (desc/100))

    # RESUMO
    st.markdown("<h2 style='text-align:center; font-weight:800; margin-top:30px;'>INVESTIMENTO ESTIMADO</h2>", unsafe_allow_html=True)
    res_cols = st.columns(3) if perfil_venda == "Executivo (Rua)" else st.columns(2)

    with res_cols[0]:
        st.markdown(f'<div class="resumo-card"><span class="resumo-label">Implantação</span><div class="resumo-valor">R$ {t_imp:,.2f}</div><div style="font-weight:bold;">{parcelas_setup}x de R$ {t_imp/parcelas_setup:,.2f}</div></div>', unsafe_allow_html=True)
    with res_cols[1]:
        st.markdown(f'<div class="resumo-card" style="border-top-color: #2e7d32;"><span class="resumo-label">Mensalidade</span><div class="resumo-valor" style="color: #2e7d32;">R$ {t_men_liq:,.2f}</div></div>', unsafe_allow_html=True)
    if perfil_venda == "Executivo (Rua)" and len(res_cols) > 2:
        with res_cols[2]:
            st.markdown(f'<div class="resumo-card" style="border-top-color: #1976d2;"><span class="resumo-label">Logística</span><div class="resumo-valor" style="color: #1976d2;">R$ {t_desp:,.2f}</div></div>', unsafe_allow_html=True)
