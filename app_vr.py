import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import urllib.parse
import os

# ==========================================
# CONFIGURAÇÕES INICIAIS E CONTROLE DE VERSÃO
# ==========================================
st.set_page_config(page_title="VR Software | Sales Intelligence", layout="wide")

APP_VERSION = "v1.4.0 - Architect Stable"

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

# FUNÇÃO DE FORMATAÇÃO BRASILEIRA (PYTHON -> TELA)
def f_br(valor):
    if valor == 0: return "0,00"
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# FUNÇÃO PARA FORMATAR PORCENTAGEM
def f_pct(valor):
    return str(valor).replace('.', ',')

def sync_state(key_permanente, key_widget):
    st.session_state[key_permanente] = st.session_state[key_widget]

# ==========================================
# CONEXÃO E TELEMETRIA DE DADOS (DATA LAYER)
# ==========================================
@st.cache_data(ttl=60)
def carregar_dados_vendas():
    status_msg = "🔴 Desconectado / Erro"
    status_cor = "#ef4444" # Vermelho
    
    try:
        if CONN_STR:
            engine = create_engine(CONN_STR)
            df = pd.read_sql("SELECT * FROM product", engine)
            status_msg = "PostgreSQL (Online)"
            status_cor = "#22c55e" # Verde
            
            # Padronização e Type Safety Rigoroso (Evita o MixedNumericTypes)
            df.columns = [str(c).strip().lower() for c in df.columns]
            
            # Garante que as colunas existam para não quebrar a lógica da v1.0.0
            for col in ['horas_padrao', 'adesao_vinculada', 'valor_hora_implantacao', 'typeproductid']:
                if col not in df.columns: df[col] = 0.0

            df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0.0)
            df['horas_padrao'] = pd.to_numeric(df['horas_padrao'], errors='coerce').fillna(0.0)
            df['valor_hora_implantacao'] = pd.to_numeric(df['valor_hora_implantacao'], errors='coerce').fillna(0.0)
            df['adesao_vinculada'] = pd.to_numeric(df['adesao_vinculada'], errors='coerce').fillna(0.0)

            full = df.set_index('produto').to_dict('index')
            
            # Regras de Negócio de Classificação VR
            sist = {k: v for k, v in full.items() if v.get('typeproductid') == 604}
            serv = {}
            desp = {}
            for k, v in full.items():
                if v.get('typeproductid') == 606:
                    nome_low = k.lower()
                    if any(x in nome_low for x in ['despesa', 'km', 'hospedagem', 'logistica', 'alimentacao']):
                        desp[k] = v
                    else:
                        serv[k] = v # Inclui serviços, projetos e adesões soltas
            
            return sist, serv, desp, full, status_msg, status_cor
        else:
            return {}, {}, {}, {}, "Falta Credenciais DB", status_cor
            
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return {}, {}, {}, {}, status_msg, status_cor

sistemas_db, servicos_db, despesas_db, full_db, db_status, db_cor = carregar_dados_vendas()

# ESTILIZAÇÃO CSS (INTACTA DA v1.0.0)
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

# ESTADO GLOBAL (STATE LAYER)
init_state = {
    'm_combo': "Montar Manualmente", 'm_pdv_conv': 0.0, 'm_pdv_touch': 0.0, 'm_pdv_self': 0.0, 'm_semanas': 0.0, 'm_mobile': 0.0,
    'm_tef': "Não utiliza", 'm_migracao': False, 'm_ecommerce': False, 'm_app': False, 'm_connect': False,
    'm_erp_pro': False, 'm_xml': False, 'm_escopo': False, 'm_controller': False, 'm_cartaz': False, 'm_masterfisco': False, 'm_backup': False
}
for k, v in init_state.items():
    if k not in st.session_state: st.session_state[k] = v
if 'sel_i' not in st.session_state: st.session_state.sel_i = []
if 'sel_m' not in st.session_state: st.session_state.sel_m = []
if 'sel_d' not in st.session_state: st.session_state.sel_d = []

# Tudo nasce como Float (0.0) para blindar a interface
for nome in full_db.keys():
    if f"perm_val_{nome}" not in st.session_state: st.session_state[f"perm_val_{nome}"] = 0.0

def limpar_tudo():
    for k, v in init_state.items(): st.session_state[k] = v
    if 'tmp_combo' in st.session_state: st.session_state.tmp_combo = "Montar Manualmente"
    for t in ['tmp_pdv_conv', 'tmp_pdv_touch', 'tmp_pdv_self', 'tmp_semanas', 'tmp_mobile']:
        if t in st.session_state: st.session_state[t] = 0.0
    toggles = ['tmp_erp_pro', 'tmp_xml', 'tmp_connect', 'tmp_backup', 'tmp_cartaz', 'tmp_ecommerce', 'tmp_controller', 'tmp_masterfisco', 'tmp_app', 'tmp_migracao', 'tmp_escopo']
    for t in toggles:
        if t in st.session_state: st.session_state[t] = False
    st.session_state.sel_i, st.session_state.sel_m, st.session_state.sel_d = [], [], []
    for nome in full_db.keys(): st.session_state[f"perm_val_{nome}"] = 0.0

def sync_combo():
    combo = st.session_state.tmp_combo
    st.session_state.m_combo = combo
    if combo == "Padrão Pequeno Porte":
        st.session_state.m_pdv_conv, st.session_state.m_tef, st.session_state.m_semanas = 5.0, "SiTef Express", 3.0
        st.session_state.m_migracao, st.session_state.m_escopo, st.session_state.m_erp_pro, st.session_state.m_xml, st.session_state.m_mobile = True, True, True, True, 1.0

# ==========================================
# SIDEBAR COM CONTROLE DE VERSÃO (INTACTA)
# ==========================================
with st.sidebar:
    if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=180)
    tela = st.radio("Navegação:", ["Gerador de Proposta", "Consulta de Preço"])
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
    
    # RODAPÉ DE TELEMETRIA
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

# ==========================================
# RECONCILIAÇÃO DE REGRAS DE NEGÓCIO (NOVIDADE ARQUITETURAL)
# ==========================================
def processar_regras_colaterais():
    """ Roda milissegundos antes da UI para garantir sincronia automática """
    if any("conciliador" in s.lower() for s in st.session_state.sel_m):
        for nome_banco, dados_banco in servicos_db.items():
            if "conciliador" in nome_banco.lower():
                # Injeta o Projeto e Adesão com as horas reais do banco
                if nome_banco not in st.session_state.sel_i:
                    st.session_state.sel_i.append(nome_banco)
                    h_padrao = dados_banco.get('horas_padrao', 1.0)
                    # Força para float no mínimo 1.0 para adesões e as 12.0 para projeto
                    st.session_state[f"perm_val_{nome_banco}"] = float(h_padrao) if h_padrao > 0 else 1.0

# ==========================================
# GERADOR DE PROPOSTA
# ==========================================
if tela == "Gerador de Proposta":
    
    def aplicar_mapeamento():
        pdv_map = {"VR PDV Convencional": st.session_state.m_pdv_conv, "PDV Touchscreen": st.session_state.m_pdv_touch, "PDV Selfcheckout": st.session_state.m_pdv_self}
        for p, qtd in pdv_map.items():
            if p in sistemas_db:
                st.session_state[f"perm_val_{p}"] = float(qtd)
                st.session_state[f"tmp_m_{p}"] = float(qtd)
                if qtd > 0 and p not in st.session_state.sel_m: st.session_state.sel_m.append(p)
        
        total_pdvs = sum(pdv_map.values())
        st.session_state.sel_m = [item for item in st.session_state.sel_m if "SiTef" not in item]
        if st.session_state.m_tef == "SiTef Express":
            escolhido = "SiTef Express até 3 PDVs" if total_pdvs <= 3 else "SiTef Express até 6 PDVs" if total_pdvs <= 6 else "SiTef Express até 8 PDVs" if total_pdvs <= 8 else "SiTef Express acima de 8 PDVs"
            if escolhido in sistemas_db:
                st.session_state[f"perm_val_{escolhido}"] = 1.0
                st.session_state[f"tmp_m_{escolhido}"] = 1.0
                st.session_state.sel_m.append(escolhido)

        exp_map = {
            "E-Commerce": st.session_state.m_ecommerce, "M-Commerce": st.session_state.m_app, 
            "VR Connect (Android/IOS)": st.session_state.m_connect, "VR ERP PRO": st.session_state.m_erp_pro, 
            "Gerenciador XML": st.session_state.m_xml, "VR Controller 360": st.session_state.m_controller, 
            "VR Cartaz": st.session_state.m_cartaz, "VR MasterFisco Brasil": st.session_state.m_masterfisco, 
            "VR Backup": st.session_state.m_backup
        }
        for item, ativo in exp_map.items():
            if item in sistemas_db:
                st.session_state[f"perm_val_{item}"] = 1.0 if ativo else 0.0
                st.session_state[f"tmp_m_{item}"] = 1.0 if ativo else 0.0
                if ativo and item not in st.session_state.sel_m: st.session_state.sel_m.append(item)

        if "VR Mobile" in sistemas_db and st.session_state.m_mobile > 0:
            if "VR Mobile" not in st.session_state.sel_m: st.session_state.sel_m.append("VR Mobile")
            st.session_state[f"perm_val_VR Mobile"] += st.session_state.m_mobile
            st.session_state[f"tmp_m_VR Mobile"] = st.session_state[f"perm_val_VR Mobile"]
            st.session_state.m_mobile = 0.0

        sem = st.session_state.m_semanas
        serv_map = {"Implantação e Treinamento": sem * 44.0, "Migração Banco de Dados": 8.0 if st.session_state.m_migracao else 0.0, "Definição de Escopo": 8.0 if st.session_state.m_escopo else 0.0}
        for s_item, s_horas in serv_map.items():
            if s_item in servicos_db:
                st.session_state[f"perm_val_{s_item}"] = float(s_horas)
                st.session_state[f"tmp_i_{s_item}"] = float(s_horas)
                if s_horas > 0 and s_item not in st.session_state.sel_i: st.session_state.sel_i.append(s_item)

        if "Alimentacao" in despesas_db: 
            st.session_state[f"perm_val_Alimentacao"] = sem * 10.0
            st.session_state[f"tmp_d_Alimentacao"] = sem * 10.0
            if sem > 0 and "Alimentacao" not in st.session_state.sel_d: st.session_state.sel_d.append("Alimentacao")
        if "Hospedagem" in despesas_db: 
            st.session_state[f"perm_val_Hospedagem"] = sem * 4.0
            st.session_state[f"tmp_d_Hospedagem"] = sem * 4.0
            if sem > 0 and "Hospedagem" not in st.session_state.sel_d: st.session_state.sel_d.append("Hospedagem")

    if not modo_apresentacao:
        st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)
        if mapeamento_ativo:
            st.markdown('<div class="mapeamento-container"><h3 style="margin:0; color:#ff6600;">🛒 Mapeamento da Operação</h3></div>', unsafe_allow_html=True)
            st.selectbox("Combo Rápido", ["Montar Manualmente", "Padrão Pequeno Porte"], key="tmp_combo", on_change=sync_combo)
            c1, c2, c3 = st.columns(3)
            with c1:
                # FLOAT FIX APLICADO NESTES INPUTS
                st.number_input("PDV Convencional", min_value=0.0, step=1.0, key="tmp_pdv_conv", value=float(st.session_state.m_pdv_conv), on_change=sync_state, args=("m_pdv_conv", "tmp_pdv_conv"))
                st.number_input("PDV Touch", min_value=0.0, step=1.0, key="tmp_pdv_touch", value=float(st.session_state.m_pdv_touch), on_change=sync_state, args=("m_pdv_touch", "tmp_pdv_touch"))
                st.number_input("PDV Selfcheckout", min_value=0.0, step=1.0, key="tmp_pdv_self", value=float(st.session_state.m_pdv_self), on_change=sync_state, args=("m_pdv_self", "tmp_pdv_self"))
            with c2:
                st.selectbox("TEF", ["Não utiliza", "SiTef Express", "VR TEF"], key="tmp_tef", index=["Não utiliza", "SiTef Express", "VR TEF"].index(st.session_state.m_tef), on_change=sync_state, args=("m_tef", "tmp_tef"))
                st.number_input("Semanas", min_value=0.0, step=1.0, key="tmp_semanas", value=float(st.session_state.m_semanas), on_change=sync_state, args=("m_semanas", "tmp_semanas"))
                st.checkbox("Migração?", key="tmp_migracao", value=st.session_state.m_migracao, on_change=sync_state, args=("m_migracao", "tmp_migracao"))
                st.checkbox("Escopo?", key="tmp_escopo", value=st.session_state.m_escopo, on_change=sync_state, args=("m_escopo", "tmp_escopo"))
            with c3:
                st.number_input("VR Mobile", min_value=0.0, step=1.0, key="tmp_mobile", value=float(st.session_state.m_mobile), on_change=sync_state, args=("m_mobile", "tmp_mobile"))
                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    st.toggle("VR ERP PRO", key="tmp_erp_pro", value=st.session_state.
