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
            df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
            df['Valor'] = df['Valor'].apply(limpar_valor)
            
            sist = df[df['Tipo'].str.contains('Sist', case=False, na=False)].set_index('Produto').to_dict('index')
            serv = df[df['Tipo'].str.contains('Serv', case=False, na=False)].set_index('Produto').to_dict('index')
            desp = df[df['Tipo'].str.contains('Desp', case=False, na=False)].set_index('Produto').to_dict('index')
            full = df.set_index('Produto').to_dict('index')
            return sist, serv, desp, full
        return {}, {}, {}, {}
    except Exception as e:
        st.error(f"Erro ao carregar banco de dados: {e}")
        return {}, {}, {}, {}

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

# --- 4. LÓGICA DE INTELIGÊNCIA ---
def aplicar_mapeamento():
    # 1. PDVs
    pdv_map = {"VR PDV Convencional": st.session_state.m_pdv_conv, "PDV Touchscreen": st.session_state.m_pdv_touch, "PDV Selfcheckout": st.session_state.m_pdv_self}
    for p, qtd in pdv_map.items():
        if p in sistemas_db:
            st.session_state[f"perm_val_{p}"] = qtd
            if qtd > 0 and p not in st.session_state.sel_m: st.session_state.sel_m.append(p)
            elif qtd == 0 and p in st.session_state.sel_m: st.session_state.sel_m.remove(p)

    # 2. TEF Inteligente
    total = sum(pdv_map.values())
    st.session_state.sel_m = [i for i in st.session_state.sel_m if "SiTef" not in i]
    if st.session_state.m_tef == "SiTef Express":
        tef_key = "SiTef Express até 3 PDVs" if total <= 3 else "SiTef Express até 6 PDVs" if total <= 6 else "SiTef Express até 8 PDVs" if total <= 8 else "SiTef Express a partir de 9 PDVs"
        if tef_key in sistemas_db:
            st.session_state[f"perm_val_{tef_key}"] = 1
            st.session_state.sel_m.append(tef_key)

    # 3. Semanas (Serviços + Logística)
    sem = st.session_state.m_semanas
    it = "Implantação e Treinamento"
    if it in servicos_db:
        st.session_state[f"perm_val_{it}"] = sem * 44
        if sem > 0 and it not in st.session_state.sel_i: st.session_state.sel_i.append(it)
        elif sem == 0 and it in st.session_state.sel_i: st.session_state.sel_i.remove(it)

    ali, hos = "Alimentacao", "Hospedagem"
    if ali in despesas_db: st.session_state[f"perm_val_{ali}"] = sem * 10
    if hos in despesas_db: st.session_state[f"perm_val_{hos}"] = sem * 4

    #
