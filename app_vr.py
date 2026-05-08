import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import urllib.parse
import os
import re

# ==========================================
# CONFIGURAÇÕES INICIAIS E CONTROLE DE VERSÃO
# ==========================================
st.set_page_config(page_title="VR Software | Sales Intelligence", layout="wide")

APP_VERSION = "v1.1.7 - Full UI Restore"
ADMIN_PASS_REQUIRED = "333666"

# Configuração de Conexão (Postgres)
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

# ==========================================
# MOTOR DE TRATAMENTO (POSTGRES -> MEMÓRIA)
# ==========================================
def motor_transformacao_vendas(df):
    df.columns = [str(c).strip().lower() for c in df.columns]
    if 'title' in df.columns:
        df = df.rename(columns={'title': 'produto'})
    
    df = df.drop_duplicates(subset=['produto'], keep='last')
    df['tipo'] = ""
    df['horas_padrao'] = 0.0
    df['adesao_vinculada'] = 0.0
    df['valor_hora_implantacao'] = 125.0

    for idx, row in df.iterrows():
        tid = row.get('typeproductid', 0)
        nome = str(row['produto']).lower()
        if tid == 604:
            df.at[idx, 'tipo'] = 'sist'
        elif tid == 606:
            # Classifica como despesa se contiver palavras-chave
            if any(p in nome for p in ['despesa', 'km', 'hospedagem', 'deslocamento', 'logistica']):
                df.at[idx, 'tipo'] = 'desp'
            else:
                df.at[idx, 'tipo'] = 'serv'
                df.at[idx, 'horas_padrao'] = float(row.get('qtd_min', 0))

    # Vínculo automático de adesão
    mask_adesao = df['produto'].str.contains('Adesao|Adesão', case=False, na=False)
    adesoes = df[mask_adesao].copy()
    
    for _, ad_row in adesoes.iterrows():
        chave = re.sub(r'ades[ãa]o', '', ad_row['produto'], flags=re.IGNORECASE).strip().lower()
        chave = re.sub(r'\s+', '', chave)
        for idx_s, sist_row in df[df['tipo'] == 'sist'].iterrows():
            nome_sist = re.sub(r'\s+', '', str(sist_row['produto']).lower())
            if chave in nome_sist or nome_sist in chave:
                df.at[idx_s, 'adesao_vinculada'] = float(ad_row.get('valor', 0))
                break

    return df[~mask_adesao]

# FUNÇÕES DE SUPORTE
def limpar_valor(valor):
    if pd.isna(valor) or str(valor).strip() == "": return 0.0
    v = str(valor).replace('R$', '').replace(' ', '').strip()
    if ',' in v and '.' in v: v = v.replace('.', '').replace(',', '.')
    elif ',' in v: v = v.replace(',', '.')
    try: return float(v)
    except: return 0.0

def f_br(valor):
    if valor == 0: return "0,00"
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def f_pct(valor):
    return str(valor).replace('.', ',')

def sync_state(key_permanente, key_widget):
    st.session_state[key_permanente] = st.session_state[key_widget]

@st.cache_data(ttl=60)
def carregar_dados_vendas():
    status_msg, status_cor, df_raw = "🔴 Desconectado", "#ef4444", pd.DataFrame()
    try:
        if CONN_STR:
            engine = create_engine(CONN_STR)
            df_raw = pd.read_sql("SELECT * FROM product", engine)
            df = motor_transformacao_vendas(df_raw)
            status_msg, status_cor = "PostgreSQL Conectado", "#22c55e"
            df['valor'] = df['valor'].apply(limpar_valor)
            full = df.set_index('produto').to_dict('index')
            sist = {k: v for k, v in full.items() if v['tipo'] == 'sist'}
            serv = {k: v for k, v in full.items() if v['tipo'] == 'serv'}
            desp = {k: v for k, v in full.items() if v['tipo'] == 'desp'}
            return sist, serv, desp, full, status_msg, status_cor, df_raw
    except Exception as e:
        st.error(f"Erro: {e}")
    return {}, {}, {}, {}, status_msg, status_cor, df_raw

sistemas_db, servicos_db, despesas_db, full_db, db_status, db_cor, df_raw = carregar_dados_vendas()

# ==========================================
# ESTILIZAÇÃO CSS (RESTAURADA v1.0.0)
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
    if f"perm_val_{nome}" not in st.session_state: st.session_state[f"perm_val_{nome}"] = 0

def limpar_tudo():
    for k, v in init_state.items(): st.session_state[k] = v
    if 'tmp_combo' in st.session_state: st.session_state.tmp_combo = "Montar Manualmente"
    for t in ['tmp_pdv_conv', 'tmp_pdv_touch', 'tmp_pdv_self', 'tmp_semanas', 'tmp_mobile']:
        if t in st.session_state: st.session_state[t] = 0
    toggles = ['tmp_erp_pro', 'tmp_xml', 'tmp_connect', 'tmp_backup', 'tmp_cartaz', 'tmp_ecommerce', 'tmp_controller', 'tmp_masterfisco', 'tmp_app', 'tmp_migracao', 'tmp_escopo']
    for t in toggles:
        if t in st.session_state: st.session_state[t] = False
    st.session_state.sel_i, st.session_state.sel_m, st.session_state.sel_d = [], [], []
    for nome in full_db.keys(): st.session_state[f"perm_val_{nome}"] = 0

def sync_combo():
    combo = st.session_state.tmp_combo
    if combo == "Padrão Pequeno Porte":
        st.session_state.m_pdv_conv, st.session_state.m_tef, st.session_state.m_semanas = 5, "SiTef Express", 3
        st.session_state.m_migracao, st.session_state.m_escopo, st.session_state.m_erp_pro, st.session_state.m_xml, st.session_state.m_mobile = True, True, True, True, 1

# SIDEBAR
with st.sidebar:
    if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=180)
    tela = st.radio("Navegação:", ["Gerador de Proposta", "Consulta de Preço", "Painel Admin"])
    if tela == "Gerador de Proposta":
        st.write("---")
        mapeamento_ativo = st.toggle("Mapeamento Inteligente", value=False)
        modo_apresentacao = st.toggle("Modo Apresentação")
        perfil_venda = st.selectbox("Perfil do Cliente", ["Executivo (Rua)", "CS (Base)"])
        desc = st.number_input("Desconto (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.5)
        exibir_detalhe_desc = st.toggle("Exibir Desconto na Tela", value=True)
        faturamento_sistema = st.selectbox("Início Mensalidade", ["Na assinatura", "30 dias", "60 dias", "Após implantação"])
        parcelas_setup = st.selectbox("Parcelas Setup", [1, 2, 3, 4, 5, 6], index=3)
        regra_logistica = st.selectbox("Faturamento Logística", ["Faturamento na assinatura", "Faturamento pós Implantação"])
    
    st.markdown("<br>" * 5, unsafe_allow_html=True)
    st.markdown(f'''
        <hr style="margin: 10px 0; border-color: #ddd;">
        <div style="font-size: 0.8rem; color: #555;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                <div style="width: 10px; height: 10px; border-radius: 50%; background-color: {db_cor};"></div>
                <b>Base:</b> {db_status}
            </div>
            <div><b>App Version:</b> {APP_VERSION}</div>
        </div>
    ''', unsafe_allow_html=True)

# TELAS
if tela == "Painel Admin":
    st.markdown('<h1 class="hero-title">BACKOFFICE</h1>', unsafe_allow_html=True)
    senha_admin = st.text_input("Senha Admin:", type="password")
    if senha_admin == ADMIN_PASS_REQUIRED:
        st.success("Conectado ao Postgres")
        st.dataframe(df_raw, use_container_width=True)

elif tela == "Gerador de Proposta":
    def aplicar_mapeamento():
        pdv_map = {"VR PDV Convencional": st.session_state.m_pdv_conv, "PDV Touchscreen": st.session_state.m_pdv_touch, "PDV Selfcheckout": st.session_state.m_pdv_self}
        for p, qtd in pdv_map.items():
            if p in sistemas_db:
                st.session_state[f"perm_val_{p}"] = qtd
                if qtd > 0 and p not in st.session_state.sel_m: st.session_state.sel_m.append(p)
        
        total_pdvs = sum(pdv_map.values())
        st.session_state.sel_m = [item for item in st.session_state.sel_m if "SiTef" not in item]
        if st.session_state.m_tef == "SiTef Express":
            escolhido = "SiTef Express até 3 PDVs" if total_pdvs <= 3 else "SiTef Express até 6 PDVs" if total_pdvs <= 6 else "SiTef Express até 8 PDVs" if total_pdvs <= 8 else "SiTef Express acima de 8 PDVs"
            if escolhido in sistemas_db:
                st.session_state[f"perm_val_{escolhido}"] = 1
                if escolhido not in st.session_state.sel_m: st.session_state.sel_m.append(escolhido)

        exp_map = {"VR ERP PRO": st.session_state.m_erp_pro, "Gerenciador XML": st.session_state.m_xml, "VR Backup": st.session_state.m_backup, "VR Connect (Android/IOS)": st.session_state.m_connect, "VR Controller 360": st.session_state.m_controller, "VR Cartaz": st.session_state.m_cartaz, "E-Commerce": st.session_state.m_ecommerce, "M-Commerce": st.session_state.m_app, "VR MasterFisco Brasil": st.session_state.m_masterfisco}
        for item, ativo in exp_map.items():
            if item in sistemas_db:
                st.session_state[f"perm_val_{item}"] = 1 if ativo else 0
                if ativo and item not in st.session_state.sel_m: st.session_state.sel_m.append(item)

        sem = st.session_state.m_semanas
        serv_map = {"Implantação e Treinamento": sem * 44, "Migração Banco de Dados": 8 if st.session_state.m_migracao else 0, "Definição de Escopo": 8 if st.session_state.m_escopo else 0}
        for s_item, s_horas in serv_map.items():
            if s_item in servicos_db:
                st.session_state[f"perm_val_{s_item}"] = s_horas
                if s_horas > 0 and s_item not in st.session_state.sel_i: st.session_state.sel_i.append(s_item)

        if "Alimentacao" in despesas_db: 
            st.session_state[f"perm_val_Alimentacao"] = sem * 10
            if sem > 0 and "Alimentacao" not in st.session_state.sel_d: st.session_state.sel_d.append("Alimentacao")
        if "Hospedagem" in despesas_db: 
            st.session_state[f"perm_val_Hospedagem"] = sem * 4
            if sem > 0 and "Hospedagem" not in st.session_state.sel_d: st.session_state.sel_d.append("Hospedagem")

    if not modo_apresentacao:
        st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)
        if mapeamento_ativo:
            st.markdown('<div class="mapeamento-container"><h3 style="margin:0; color:#ff6600;">🛒 Mapeamento da Operação</h3></div>', unsafe_allow_html=True)
            st.selectbox("Combo Rápido", ["Montar Manualmente", "Padrão Pequeno Porte"], key="tmp_combo", on_change=sync_combo)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.number_input("PDV Convencional", min_value=0, key="tmp_pdv_conv", value=st.session_state.m_pdv_conv, on_change=sync_state, args=("m_pdv_conv", "tmp_pdv_conv"))
                st.number_input("PDV Touch", min_value=0, key="tmp_pdv_touch", value=st.session_state.m_pdv_touch, on_change=sync_state, args=("m_pdv_touch", "tmp_pdv_touch"))
                st.number_input("PDV Selfcheckout", min_value=0, key="tmp_pdv_self", value=st.session_state.m_pdv_self, on_change=sync_state, args=("m_pdv_self", "tmp_pdv_self"))
            with c2:
                st.selectbox("TEF", ["Não utiliza", "SiTef Express", "VR TEF"], key="tmp_tef", index=["Não utiliza", "SiTef Express", "VR TEF"].index(st.session_state.m_tef), on_change=sync_state, args=("m_tef", "tmp_tef"))
                st.number_input("Semanas", min_value=0, key="tmp_semanas", value=st.session_state.m_semanas, on_change=sync_state, args=("m_semanas", "tmp_semanas"))
                st.checkbox("Migração?", key="tmp_migracao", value=st.session_state.m_migracao, on_change=sync_state, args=("m_migracao", "tmp_migracao"))
                st.checkbox("Escopo?", key="tmp_escopo", value=st.session_state.m_escopo, on_change=sync_state, args=("m_escopo", "tmp_escopo"))
            with c3:
                st.number_input("VR Mobile", min_value=0, key="tmp_mobile", value=st.session_state.m_mobile, on_change=sync_state, args=("m_mobile", "tmp_mobile"))
