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

def sync_state(key_permanente, key_widget):
    st.session_state[key_permanente] = st.session_state[key_widget]

@st.cache_data(ttl=60)
def carregar_dados_vendas():
    try:
        if os.path.exists(EXCEL_FILE):
            df = pd.read_excel(EXCEL_FILE)
            df.columns = [str(c).strip() for c in df.columns]
            df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
            
            col_tipo = next((c for c in df.columns if c.lower() == 'tipo'), 'Tipo')
            df['Tipo_Busca'] = df[col_tipo].astype(str).str.lower()
            df['Valor'] = df['Valor'].apply(limpar_valor)
            
            sist = df[df['Tipo_Busca'].str.contains('sist', na=False)].set_index('Produto').to_dict('index')
            serv = df[df['Tipo_Busca'].str.contains('serv', na=False)].set_index('Produto').to_dict('index')
            desp = df[df['Tipo_Busca'].str.contains('desp', na=False)].set_index('Produto').to_dict('index')
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

# --- 3. ESTADO ---
if 'sel_i' not in st.session_state: st.session_state.sel_i = []
if 'sel_m' not in st.session_state: st.session_state.sel_m = []

map_keys = ['m_pdv_conv', 'm_pdv_touch', 'm_pdv_self', 'm_tef', 'm_semanas', 'm_migracao', 'm_ecommerce', 'm_app', 'm_connect']
for k in map_keys:
    if k not in st.session_state:
        st.session_state[k] = 0 if any(x in k for x in ['pdv', 'semanas']) else "Não utiliza" if 'tef' in k else False

for nome in full_db.keys():
    if f"perm_val_{nome}" not in st.session_state:
        st.session_state[f"perm_val_{nome}"] = 0

def limpar_tudo():
    for k in map_keys:
        st.session_state[k] = 0 if any(x in k for x in ['pdv', 'semanas']) else "Não utiliza" if 'tef' in k else False
    st.session_state.sel_i, st.session_state.sel_m = [], []
    for nome in full_db.keys():
        st.session_state[f"perm_val_{nome}"] = 0

# --- 4. LÓGICA DE AUTOMATIZAÇÃO ---
def aplicar_mapeamento():
    pdv_map = {"VR PDV Convencional": st.session_state.m_pdv_conv, "PDV Touchscreen": st.session_state.m_pdv_touch, "PDV Selfcheckout": st.session_state.m_pdv_self}
    for p, qtd in pdv_map.items():
        if p in sistemas_db:
            st.session_state[f"perm_val_{p}"] = qtd
            if qtd > 0 and p not in st.session_state.sel_m: st.session_state.sel_m.append(p)
            elif qtd == 0 and p in st.session_state.sel_m: st.session_state.sel_m.remove(p)

    total_pdvs = sum(pdv_map.values())
    st.session_state.sel_m = [item for item in st.session_state.sel_m if "SiTef" not in item]
    if st.session_state.m_tef == "SiTef Express":
        tef_opcoes = ["SiTef Express até 3 PDVs", "SiTef Express até 6 PDVs", "SiTef Express até 8 PDVs", "SiTef Express acima de 8 PDVs"]
        escolhido = tef_opcoes[0] if total_pdvs <= 3 else tef_opcoes[1] if total_pdvs <= 6 else tef_opcoes[2] if total_pdvs <= 8 else tef_opcoes[3]
        if escolhido in sistemas_db:
            st.session_state[f"perm_val_{escolhido}"] = 1
            st.session_state.sel_m.append(escolhido)

    sem = st.session_state.m_semanas
    it = "Implantação e Treinamento"
    if it in servicos_db:
        st.session_state[f"perm_val_{it}"] = sem * 44
        if sem > 0 and it not in st.session_state.sel_i: st.session_state.sel_i.append(it)
        elif sem == 0 and it in st.session_state.sel_i: st.session_state.sel_i.remove(it)
    
    if "Alimentacao" in despesas_db: st.session_state[f"perm_val_Alimentacao"] = sem * 10
    if "Hospedagem" in despesas_db: st.session_state[f"perm_val_Hospedagem"] = sem * 4

# --- 5. MENU LATERAL ---
with st.sidebar:
    if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=180)
    tela = st.radio("Navegação:", ["Gerador de Proposta", "Consulta de Preço"])
    st.write("---")

    if tela == "Gerador de Proposta":
        st.markdown('**Configurações de Venda**')
        # MUDANÇA 1: Começa desativado
        mapeamento_ativo = st.toggle("Mapeamento Inteligente", value=False)
        modo_apresentacao = st.toggle("Modo Apresentação")
        perfil_venda = st.selectbox("Perfil do Cliente", ["Executivo (Rua)", "CS (Base)"])
        # MUDANÇA 2: Nome corrigido para Desconto
        desc = st.number_input("Desconto (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.5)
        exibir_detalhe_desc = st.toggle("Exibir Desconto na Tela", value=True)
        faturamento_sistema = st.selectbox("Início Mensalidade", ["Na assinatura", "30 dias", "60 dias", "Após implantação"])
        parcelas_setup = st.selectbox("Parcelas Setup", [1, 2, 3, 4, 5, 6], index=3)
        regra_logistica = st.selectbox("Faturamento Logística", ["Faturamento na assinatura do contrato", "Faturamento ao término da Implantação"])

# --- 6. TELA GERADOR ---
if tela == "Gerador de Proposta":
    if not modo_apresentacao:
        st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)
        if mapeamento_ativo:
            st.markdown('<div class="mapeamento-container"><h3 style="margin:0; color:#ff6600;">🛒 Mapeamento da Operação</h3></div>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.number_input("PDV Convencional", min_value=0, key="tmp_pdv_conv", value=st.session_state.m_pdv_conv, on_change=sync_state, args=("m_pdv_conv", "tmp_pdv_conv"))
                st.number_input("PDV Touchscreen", min_value=0, key="tmp_pdv_touch", value=st.session_state.m_pdv_touch, on_change=sync_state, args=("m_pdv_touch", "tmp_pdv_touch"))
            with c2:
                st.number_input("PDV Selfcheckout", min_value=0, key
