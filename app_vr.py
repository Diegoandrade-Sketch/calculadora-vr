import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import urllib.parse
import os

# ==========================================
# CONFIGURAÇÕES INICIAIS E CONTROLE DE VERSÃO
# ==========================================
st.set_page_config(page_title="VR Software | Sales Intelligence", layout="wide")

APP_VERSION = "v1.5.0 - Enterprise Relational"
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

# FUNÇÃO DE FORMATAÇÃO BRASILEIRA (PYTHON -> TELA)
def f_br(valor):
    if valor == 0: return "0,00"
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

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
    status_cor = "#ef4444"
    
    try:
        if CONN_STR:
            engine = create_engine(CONN_STR)
            
            # 1. Carrega Produtos
            df = pd.read_sql("SELECT * FROM product", engine)
            status_msg = "PostgreSQL (Online)"
            status_cor = "#22c55e"
            
            df.columns = [str(c).strip().lower() for c in df.columns]
            df = df.drop_duplicates(subset=['produto'], keep='last')
            
            # Type Safety rigoroso
            for col in ['horas_padrao', 'adesao_vinculada', 'valor_hora_implantacao', 'typeproductid', 'valor']:
                if col not in df.columns: df[col] = 0.0
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

            full = df.set_index('produto').to_dict('index')
            id_to_name = df.set_index('id')['produto'].to_dict() if 'id' in df.columns else {}
            name_to_id = {v: k for k, v in id_to_name.items()}

            sist = {k: v for k, v in full.items() if v.get('typeproductid') == 604}
            serv = {k: v for k, v in full.items() if v.get('typeproductid') == 606 and not any(x in k.lower() for x in ['km', 'hospedagem', 'logistica', 'alimentacao'])}
            desp = {k: v for k, v in full.items() if any(x in k.lower() for x in ['km', 'hospedagem', 'logistica', 'alimentacao'])}
            
            # 2. Carrega Vínculos Relacionais (Engine do BOM)
            vinculos_db = {}
            df_vinc = pd.DataFrame()
            try:
                df_vinc = pd.read_sql("SELECT * FROM product_vinculo", engine)
                for _, row in df_vinc.iterrows():
                    pai_id = row['id_produto_pai']
                    if pai_id not in vinculos_db: vinculos_db[pai_id] = []
                    vinculos_db[pai_id].append({
                        'id_filho': row['id_produto_filho'],
                        'tipo': row['tipo_vinculo'],
                        'qtd': float(row['quantidade_padrao'])
                    })
            except Exception:
                pass # Se a tabela não existir ainda, apenas segue o jogo vazio
            
            return sist, serv, desp, full, id_to_name, name_to_id, vinculos_db, status_msg, status_cor, df, df_vinc
        else:
            return {}, {}, {}, {}, {}, {}, {}, "Falta Credenciais DB", status_cor, pd.DataFrame(), pd.DataFrame()
            
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return {}, {}, {}, {}, {}, {}, {}, status_msg, status_cor, pd.DataFrame(), pd.DataFrame()

sistemas_db, servicos_db, despesas_db, full_db, id_to_name, name_to_id, vinculos_db, db_status, db_cor, df_raw, df_vinc = carregar_dados_vendas()

# ==========================================
# ESTILIZAÇÃO CSS (INTACTA DO GABARITO v1.0.0)
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

# ==========================================
# ESTADO GLOBAL (TYPE SAFETY - TUDO FLOAT)
# ==========================================
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
# SIDEBAR COM CONTROLE DE VERSÃO (v1.0.0)
# ==========================================
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

# ==========================================
# TELA 1: PAINEL ADMIN (BACKOFFICE RELACIONAL)
# ==========================================
if tela == "Painel Admin":
    st.markdown('<h1 class="hero-title">BACKOFFICE</h1>', unsafe_allow_html=True)
    senha = st.text_input("Senha de Acesso Admin:", type="password")
    
    if senha == ADMIN_PASS_REQUIRED:
        st.success("Autenticado com sucesso!")
        
        st.markdown('<div class="mapeamento-container"><h3 style="margin:0; color:#ff6600;">🔗 Gerenciador de Vínculos (Composição de Produtos)</h3></div>', unsafe_allow_html=True)
        st.write("Utilize esta interface para definir regras automáticas. Ex: O 'Sistema X' puxa a 'Taxa Y'.")
        
        with st.form("form_novo_vinculo"):
            c1, c2 = st.columns(2)
            with c1:
                lst_sist = sorted(list(sistemas_db.keys()))
                pai_sel = st.selectbox("1. Quando o vendedor selecionar este SISTEMA:", lst_sist if lst_sist else ["-"])
            with c2:
                lst_full = sorted(list(full_db.keys()))
                filho_sel = st.selectbox("2. O aplicativo deve incluir este ITEM junto:", lst_full if lst_full else ["-"])
            
            c3, c4 = st.columns(2)
            with c3:
                tipo_sel = st.selectbox("3. Qual o papel deste item na proposta?", ["projeto", "adesao", "incluso"])
            with c4:
                qtd_sel = st.number_input("4. Quantidade/Horas Padrão", min_value=0.0, value=1.0, step=1.0)
                
            submitted = st.form_submit_button("💾 Salvar Vínculo no Banco de Dados", use_container_width=True)
            
            if submitted:
                if CONN_STR and name_to_id:
                    try:
                        p_id = name_to_id[pai_sel]
                        f_id = name_to_id[filho_sel]
                        engine = create_engine(CONN_STR)
                        with engine.begin() as conn:
                            query = text("INSERT INTO product_vinculo (id_produto_pai, id_produto_filho, tipo_vinculo, quantidade_padrao) VALUES (:p, :f, :t, :q)")
                            conn.execute(query, {"p": p_id, "f": f_id, "t": tipo_sel, "q": qtd_sel})
                        st.success(f"Regra criada! O '{pai_sel}' agora puxa automaticamente o '{filho_sel}'.")
                        st.cache_data.clear() # Atualiza o cache do app
                    except Exception as e:
                        st.error(f"Erro ao salvar no banco: {e}")
        
        st.write("---")
        st.markdown("### 🗄️ Tabela Base (Catálogo)")
        st.dataframe(df_raw, use_container_width=True)
        st.markdown("### 🗄️ Tabela de Vínculos (Regras)")
        st.dataframe(df_vinc, use_container_width=True)

# ==========================================
# RECONCILIAÇÃO RELACIONAL ANTES DO RENDER
# ==========================================
def processar_regras_colaterais():
    """Lê a tabela product_vinculo e injeta os itens dependentes no estado do Streamlit"""
    for m_nome in st.session_state.sel_m:
        pai_id = name_to_id.get(m_nome)
        if pai_id and pai_id in vinculos_db:
            for regra in vinculos_db[pai_id]:
                filho_id = regra['id_filho']
                filho_nome = id_to_name.get(filho_id)
                if filho_nome:
                    if regra['tipo'] in ['projeto', 'adesao']:
                        if filho_nome not in st.session_state.sel_i:
                            st.session_state.sel_i.append(filho_nome)
                            # Injeta a quantidade ditada pelo banco
                            st.session_state[f"perm_val_{filho_nome}"] = float(regra['qtd'])

# ==========================================
# TELA 2: GERADOR DE PROPOSTA
# ==========================================
elif tela == "Gerador de Proposta":
    
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
            "VR Backup
