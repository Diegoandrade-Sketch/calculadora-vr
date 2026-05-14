import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import urllib.parse
import os
import json

# ==========================================
# CONFIGURAÇÕES INICIAIS E CONTROLE DE VERSÃO
# ==========================================
st.set_page_config(page_title="VR Software | Sales Intelligence", layout="wide")

APP_VERSION = "v1.6.5 - High Availability"
ADMIN_PASS_REQUIRED = "333666"
CACHE_FILE = "cache_vr.json"

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

# FUNÇÕES DE FORMATAÇÃO
def f_br(valor):
    if pd.isna(valor) or valor == 0: return "0,00"
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def f_pct(valor):
    return str(valor).replace('.', ',')

def sync_state(key_permanente, key_widget):
    st.session_state[key_permanente] = st.session_state[key_widget]

# ==========================================
# DATA LAYER (COM CONTINGÊNCIA OFFLINE)
# ==========================================
@st.cache_data(ttl=60)
def carregar_dados_vendas():
    status_msg, status_cor = "🔴 Desconectado", "#ef4444"
    
    # --- TENTATIVA A: CONEXÃO ONLINE ---
    try:
        if CONN_STR:
            engine = create_engine(CONN_STR)
            df = pd.read_sql("SELECT * FROM product", engine)
            df_vinc = pd.read_sql("SELECT * FROM product_vinculo", engine)
            
            # Salva o Cache de Segurança
            try:
                cache_payload = {
                    'df_raw': df.to_json(orient='records'),
                    'df_vinc': df_vinc.to_json(orient='records')
                }
                with open(CACHE_FILE, "w") as f:
                    json.dump(cache_payload, f)
            except Exception: pass

            status_msg, status_cor = "🟢 PostgreSQL (Online)", "#22c55e"
            
    except Exception:
        # --- TENTATIVA B: PARAQUEDAS (OFFLINE) ---
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r") as f:
                    cache_payload = json.load(f)
                df = pd.read_json(cache_payload['df_raw'], orient='records')
                df_vinc = pd.read_json(cache_payload['df_vinc'], orient='records')
                status_msg, status_cor = "🟡 Modo Offline (Cache Local)", "#facc15"
            except Exception:
                return {}, {}, {}, {}, {}, {}, {}, "🔴 Erro de Cache", "#ef4444", pd.DataFrame(), pd.DataFrame()
        else:
            return {}, {}, {}, {}, {}, {}, {}, status_msg, status_cor, pd.DataFrame(), pd.DataFrame()

    # --- PROCESSAMENTO DOS DADOS ---
    try:
        df.columns = [str(c).strip().lower() for c in df.columns]
        df = df.drop_duplicates(subset=['produto'], keep='last')
        
        for col in ['valor', 'horas_padrao', 'adesao_vinculada', 'valor_hora_implantacao', 'typeproductid']:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

        full = df.set_index('produto').to_dict('index')
        id_to_name = df.set_index('id')['produto'].to_dict() if 'id' in df.columns else {}
        name_to_id = {v: k for k, v in id_to_name.items()}

        sist = {k: v for k, v in full.items() if v.get('typeproductid') == 604}
        kw_desp = ['km', 'hospedagem', 'logistica', 'alimentacao', 'despesa', 'passagem', 'viagem', 'deslocamento', 'pedagio']
        serv = {k: v for k, v in full.items() if v.get('typeproductid') == 606 and not any(x in k.lower() for x in kw_desp)}
        desp = {k: v for k, v in full.items() if any(x in k.lower() for x in kw_desp)}
        
        vinculos_db = {}
        df_vinc.columns = [str(c).strip().lower() for c in df_vinc.columns]
        for _, row in df_vinc.iterrows():
            pai_id = int(row['id_produto_pai'])
            if pai_id not in vinculos_db: vinculos_db[pai_id] = []
            vinculos_db[pai_id].append({
                'id_filho': int(row['id_produto_filho']), 
                'tipo': row['tipo_vinculo'], 
                'qtd': float(row['quantidade_padrao'])
            })
            
        return sist, serv, desp, full, id_to_name, name_to_id, vinculos_db, status_msg, status_cor, df, df_vinc
    except Exception:
        return {}, {}, {}, {}, {}, {}, {}, "🔴 Erro de Processamento", "#ef4444", pd.DataFrame(), pd.DataFrame()

sistemas_db, servicos_db, despesas_db, full_db, id_to_name, name_to_id, vinculos_db, db_status, db_cor, df_raw, df_vinc = carregar_dados_vendas()

# ==========================================
# ESTILIZAÇÃO CSS
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
# ESTADO GLOBAL
# ==========================================
init_state = {
    'm_combo': "Montar Manualmente", 'm_pdv_conv': 0.0, 'm_pdv_touch': 0.0, 'm_pdv_self': 0.0, 'm_semanas': 0.0, 'm_mobile': 0.0,
    'm_tef': "Não utiliza", 'm_migracao': False, 'm_ecommerce': False, 'm_app': False, 'm_connect': False,
    'm_erp_pro': False, 'm_xml': False, 'm_escopo': False, 'm_controller': False, 'm_cartaz': False, 'm_masterfisco': False, 'm_backup': False,
    'auto_added': set()
}
for k, v in init_state.items():
    if k not in st.session_state: st.session_state[k] = v
for lst in ['sel_i', 'sel_m', 'sel_d']:
    if lst not in st.session_state: st.session_state[lst] = []
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
    if st.session_state.tmp_combo == "Padrão Pequeno Porte":
        st.session_state.m_pdv_conv, st.session_state.m_tef, st.session_state.m_semanas = 5.0, "SiTef Express", 3.0
        st.session_state.m_migracao, st.session_state.m_escopo, st.session_state.m_erp_pro, st.session_state.m_xml, st.session_state.m_mobile = True, True, True, True, 1.0

# MOTOR DE REGRAS RELACIONAIS (COM ANTI-FANTASMA)
def processar_regras_colaterais():
    novos_auto = set()
    for m_nome in st.session_state.sel_m:
        p_id = name_to_id.get(m_nome)
        if p_id and p_id in vinculos_db:
            for r in vinculos_db[p_id]:
                if r['tipo'] in ['projeto', 'adesao']:
                    f_nome = id_to_name.get(r['id_filho'])
                    if f_nome:
                        novos_auto.add(f_nome)
                        st.session_state[f"perm_val_{f_nome}"] = float(r['qtd'])

    # Remove os itens que perderam o vínculo do sistema pai
    for item in st.session_state.auto_added - novos_auto:
        if item in st.session_state.sel_i:
            st.session_state.sel_i.remove(item)
            st.session_state[f"perm_val_{item}"] = 0.0

    # Adiciona os novos
    for item in novos_auto:
        if item not in st.session_state.sel_i:
            st.session_state.sel_i.append(item)

    st.session_state.auto_added = novos_auto

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=180)
    tela = st.radio("Navegação:", ["Gerador de Proposta", "Consulta de Preço", "Painel Admin"])
    if tela == "Gerador de Proposta":
        st.write("---")
        mapeamento_ativo = st.toggle("Mapeamento Inteligente", value=False)
        modo_apresentacao = st.toggle("Modo Apresentação (Ocultar Menus)")
        perfil_venda = st.selectbox("Perfil do Cliente", ["Executivo (Rua)", "CS (Base)"])
        desc = st.number_input("Desconto Mensalidade (%)", 0.0, 30.0, 0.0, 0.5)
        exibir_detalhe_desc = st.toggle("Exibir Desconto na Tela", value=True)
        faturamento_sistema = st.selectbox("Início Mensalidade", ["Na assinatura", "30 dias", "60 dias", "Após implantação"])
        parcelas_setup = st.selectbox("Parcelas Setup", [1, 2, 3, 4, 5, 6, 10, 12], index=3)
        regra_despesas = st.selectbox("Faturamento Despesas", ["Faturamento na assinatura", "Faturamento pós Implantação"])
    st.markdown(f'''<hr><div style="font-size:0.8rem; color:{db_cor};">● {db_status}</div><div style="font-size:0.7rem; color:#888;">{APP_VERSION}</div>''', unsafe_allow_html=True)

# ==========================================
# TELA 1: PAINEL ADMIN
# ==========================================
if tela == "Painel Admin":
    st.markdown('<h1 class="hero-title">BACKOFFICE</h1>', unsafe_allow_html=True)
    if st.text_input("Senha de Autenticação:", type="password") == ADMIN_PASS_REQUIRED:
        if "Offline" in db_status:
            st.error("🚨 Você está no Modo Offline. O Painel Admin está bloqueado até a conexão com o banco ser reestabelecida.")
        else:
            t_vinc, t_sql, t_cat = st.tabs(["🔗 Vínculos Relacionais", "💻 Terminal SQL Seguro", "🗄️ Catálogo Completo"])
            with t_vinc:
                with st.form("form_v"):
                    c1, c2, c3, c4 = st.columns([2,2,1,1])
                    pai = c1.selectbox("Pai (SISTEMA):", sorted(list(sistemas_db.keys())))
                    fil = c2.selectbox("Filho (ITEM):", sorted(list(full_db.keys())))
                    tip = c3.selectbox("Tipo:", ["projeto", "adesao", "incluso"])
                    qtd = c4.number_input("Qtd:", min_value=0.0, value=1.0)
                    if st.form_submit_button("Salvar Vínculo"):
                        try:
                            engine = create_engine(CONN_STR)
                            with engine.begin() as conn:
                                conn.execute(text("INSERT INTO product_vinculo (id_produto_pai, id_produto_filho, tipo_vinculo, quantidade_padrao) VALUES (:p, :f, :t, :q)"), 
                                             {"p": name_to_id[pai], "f": name_to_id[fil], "t": tip, "q": qtd})
                            st.success("Vínculo Criado com Sucesso!"); st.cache_data.clear()
                        except Exception as e: st.error(e)
                st.dataframe(df_vinc, use_container_width=True)

            with t_sql:
                st.warning("⚠️ Terminal Blindado (DROP/DELETE/TRUNCATE bloqueados automaticamente)")
                query = st.text_area("Digite o comando SQL:")
                if st.button("▶️ Executar SQL"):
                    q_l = query.lower()
                    if any(p in q_l for p in ["drop ", "delete ", "truncate "]): st.error("🚨 Comando bloqueado por segurança.")
                    else:
                        try:
                            engine = create_engine(CONN_STR)
                            if q_l.strip().startswith("select"):
                                with engine.connect() as conn: res = pd.read_sql(text(query), conn)
                                st.success(f"{len(res)} linhas retornadas.")
                                st.dataframe(res, use_container_width=True)
                            else:
                                with engine.begin() as conn: r = conn.execute(text(query))
                                st.success(f"Comando executado. Linhas afetadas: {r.rowcount}"); st.cache_data.clear()
                        except Exception as e: st.error(e)
            with t_cat: st.dataframe(df_raw, use_container_width=True)

# ==========================================
# TELA 2: GERADOR DE PROPOSTA
# ==========================================
elif tela == "Gerador de Proposta":
    
    def aplicar_mapeamento():
        # Busca Flexível (Fuzzy Matching)
        for p_name in sistemas_db.keys():
            p_low = p_name.lower()
            qtd = 0.0
            if "pdv" in p_low and "convencional" in p_low: qtd = st.session_state.m_pdv_conv
            elif "touch" in p_low: qtd = st.session_state.m_pdv_touch
            elif "self" in p_low: qtd = st.session_state.m_pdv_self
            elif st.session_state.m_erp_pro and "erp pro" in p_low: qtd = 1.0
            elif st.session_state.m_xml and "xml" in p_low: qtd = 1.0
            elif st.session_state.m_connect and "connect" in p_low: qtd = 1.0
            elif st.session_state.m_backup and "backup" in p_low: qtd = 1.0
            elif st.session_state.m_cartaz and "cartaz" in p_low: qtd = 1.0
            elif st.session_state.m_ecommerce and "e-commerce" in p_low: qtd = 1.0
            elif st.session_state.m_controller and "360" in p_low: qtd = 1.0
            elif st.session_state.m_masterfisco and "masterfisco" in p_low: qtd = 1.0
            elif st.session_state.m_app and "m-commerce" in p_low: qtd = 1.0
            elif st.session_state.m_mobile > 0 and "mobile" in p_low: qtd = float(st.session_state.m_mobile)

            # TEF Flexível
            if st.session_state.m_tef == "SiTef Express" and "sitef" in p_low:
                tot = st.session_state.m_pdv_conv + st.session_state.m_pdv_touch + st.session_state.m_pdv_self
                if tot <= 3 and "3" in p_low: qtd = 1.0
                elif 3 < tot <= 6 and "6" in p_low: qtd = 1.0
                elif 6 < tot <= 8 and "8" in p_low: qtd = 1.0
                elif tot > 8 and ("acima" in p_low or "+" in p_low): qtd = 1.0
            elif st.session_state.m_tef == "VR TEF" and "vr tef" in p_low: qtd = 1.0

            if qtd > 0:
                st.session_state[f"perm_val_{p_name}"] = qtd
                if p_name not in st.session_state.sel_m: st.session_state.sel_m.append(p_name)

        sem = st.session_state.m_semanas
        for s_name in servicos_db.keys():
            s_low = s_name.lower()
            qtd = 0.0
            if "implanta" in s_low and "treinamento" in s_low: qtd = sem * 44.0
            elif st.session_state.m_migracao and "migra" in s_low: qtd = 8.0
            elif st.session_state.m_escopo and "escopo" in s_low: qtd = 8.0

            if qtd > 0:
                st.session_state[f"perm_val_{s_name}"] = qtd
                if s_name not in st.session_state.sel_i: st.session_state.sel_i.append(s_name)

        if sem > 0:
            for d_name in despesas_db.keys():
                d_low = d_name.lower()
                qtd = 0.0
                if "alimenta" in d_low: qtd = sem * 10.0
                elif "hospedagem" in d_low: qtd = sem * 4.0

                if qtd > 0:
                    st.session_state[f"perm_val_{d_name}"] = qtd
                    if d_name not in st.session_state.sel_d: st.session_state.sel_d.append(d_name)

    if not modo_apresentacao:
        st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)
        if mapeamento_ativo:
            st.markdown('<div class="mapeamento-container"><h3 style="margin:0; color:#ff6600;">🛒 Mapeamento da Operação</h3></div>', unsafe_allow_html=True)
            st.selectbox("Combo Rápido", ["Montar Manualmente", "Padrão Pequeno Porte"], key="tmp_combo", on_change=sync_combo)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.number_input("PDV Convencional", 0.0, step=1.0, key="tmp_pdv_conv", value=st.session_state.m_pdv_conv, on_change=sync_state, args=("m_pdv_conv", "tmp_pdv_conv"))
                st.number_input("PDV Touch", 0.0, step=1.0, key="tmp_pdv_touch", value=st.session_state.m_pdv_touch, on_change=sync_state, args=("m_pdv_touch", "tmp_pdv_touch"))
                st.number_input("PDV Selfcheckout", 0.0, step=1.0, key="tmp_pdv_self", value=st.session_state.m_pdv_self, on_change=sync_state, args=("m_pdv_self", "tmp_pdv_self"))
            with c2:
                st.selectbox("TEF", ["Não utiliza", "SiTef Express", "VR TEF"], key="tmp_tef", index=["Não utiliza", "SiTef Express", "VR TEF"].index(st.session_state.m_tef), on_change=sync_state, args=("m_tef", "tmp_tef"))
                st.number_input("Semanas", 0.0, step=1.0, key="tmp_semanas", value=st.session_state.m_semanas, on_change=sync_state, args=("m_semanas", "tmp_semanas"))
                st.checkbox("Migração?", key="tmp_migracao", value=st.session_state.m_migracao, on_change=sync_state, args=("m_migracao", "tmp_migracao"))
                st.checkbox("Escopo?", key="tmp_escopo", value=st.session_state.m_escopo, on_change=sync_state, args=("m_escopo", "tmp_escopo"))
            with c3:
                st.number_input("VR Mobile", 0.0, step=1.0, key="tmp_mobile", value=st.session_state.m_mobile, on_change=sync_state, args=("m_mobile", "tmp_mobile"))
                sc1, sc2, sc3 = st.columns(3)
                sc1.toggle("VR ERP PRO", key="tmp_erp_pro", value=st.session_state.m_erp_pro, on_change=sync_state, args=("m_erp_pro", "tmp_erp_pro"))
                sc1.toggle("G. XML", key="tmp_xml", value=st.session_state.m_xml, on_change=sync_state, args=("m_xml", "tmp_xml"))
                sc1.toggle("Connect", key="tmp_connect", value=st.session_state.m_connect, on_change=sync_state, args=("m_connect", "tmp_connect"))
                sc2.toggle("VR Backup", key="tmp_backup", value=st.session_state.m_backup, on_change=sync_state, args=("m_backup", "tmp_backup"))
                sc2.toggle("VR Cartaz", key="tmp_cartaz", value=st.session_state.m_cartaz, on_change=sync_state, args=("m_cartaz", "tmp_cartaz"))
                sc2.toggle("E-Commerce", key="tmp_ecommerce", value=st.session_state.m_ecommerce, on_change=sync_state, args=("m_ecommerce", "tmp_ecommerce"))
                sc3.toggle("C. 360", key="tmp_controller", value=st.session_state.m_controller, on_change=sync_state, args=("m_controller", "tmp_controller"))
                sc3.toggle("MasterFisco", key="tmp_masterfisco", value=st.session_state.m_masterfisco, on_change=sync_state, args=("m_masterfisco", "tmp_masterfisco"))
                sc3.toggle("M-Commerce", key="tmp_app", value=st.session_state.m_app, on_change=sync_state, args=("m_app", "tmp_app"))
                b1, b2 = st.columns(2)
                b1.button("✨ Aplicar Inteligência", on_click=aplicar_mapeamento, use_container_width=True)
                b2.button("🗑️ Limpar Tudo", on_click=limpar_tudo, use_container_width=True)
        st.write("---")

    # A Lógica Relacional Roda Fora da Restrição de Interface para Manter o Estado
    processar_regras_colaterais()

    # Modo Apresentação: Oculta as colunas de inclusão manual
    if not modo_apresentacao:
        c1, c2, c3 = st.columns(3) if perfil_venda == "Executivo (Rua)" else (*st.columns(2), None)
        with c1:
            st.markdown('<div class="section-header"><span class="section-title">IMPLANTAÇÃO E SERVIÇOS</span></div>', unsafe_allow_html=True)
            st.session_state.sel_i = st.multiselect("Serviços", list(servicos_db.keys()), default=st.session_state.sel_i)
            for i in st.session_state.sel_i:
                v_u = servicos_db[i]['valor']
                st.number_input(f"{i} (R$ {f_br(v_u)}/h)", 0.0, step=1.0, value=st.session_state[f"perm_val_{i}"], key=f"tmp_i_{i}", on_change=sync_state, args=(f"perm_val_{i}", f"tmp_i_{i}"))
        with c2:
            st.markdown('<div class="section-header"><span class="section-title">MENSALIDADES SISTEMAS</span></div>', unsafe_allow_html=True)
            st.session_state.sel_m = st.multiselect("Sistemas", list(sistemas_db.keys()), default=st.session_state.sel_m)
            for i in st.session_state.sel_m:
                v_u = sistemas_db[i]['valor']
                st.number_input(f"{i} (R$ {f_br(v_u)}/un)", 0.0, step=1.0, value=st.session_state[f"perm_val_{i}"], key=f"tmp_m_{i}", on_change=sync_state, args=(f"perm_val_{i}", f"tmp_m_{i}"))
        if c3:
            with c3:
                st.markdown('<div class="section-header"><span class="section-title">DESPESAS DO PROJETO</span></div>', unsafe_allow_html=True)
                st.session_state.sel_d = st.multiselect("Despesas", list(despesas_db.keys()), default=st.session_state.sel_d)
                for i in st.session_state.sel_d:
                    v_u = despesas_db[i]['valor']
                    st.number_input(f"{i} (R$ {f_br(v_u)}/un)", 0.0, step=1.0, value=st.session_state[f"perm_val_{i}"], key=f"tmp_d_{i}", on_change=sync_state, args=(f"perm_val_{i}", f"tmp_d_{i}"))

    # Os CARDS de Resumo (Aparecem mesmo no Modo Apresentação)
    st.markdown("<h2 style='text-align:center; font-weight:800; margin-top:30px;'>RESUMO DO INVESTIMENTO</h2>", unsafe_allow_html=True)
    res_cols = st.columns(3) if perfil_venda == "Executivo (Rua)" else st.columns([1, 2, 2, 1])[1:3]
    
    t_setup, h_setup = 0.0, ""
    v_h_base = servicos_db.get("Implantação e Treinamento", {}).get("valor", 0.0)

    for n in st.session_state.sel_i:
        q = st.session_state[f"perm_val_{n}"]
        if q > 0:
            v_u = servicos_db.get(n, full_db.get(n, {'valor':0.0}))['valor']
            t_setup += (q * v_u)
            h_setup += f"<li><span>{n}</span><span class='item-detalhe'>{int(q)}h x R$ {f_br(v_u)} | Total: R$ {f_br(q*v_u)}</span></li>"
    
    for n in st.session_state.sel_m:
        if name_to_id.get(n) not in vinculos_db:
            d = sistemas_db[n]; h = d.get('horas_padrao', 0.0); ads = d.get('adesao_vinculada', 0.0)
            if h > 0:
                v_rate = (d.get('valor_hora_implantacao', 0.0) or v_h_base)
                t_setup += (h * v_rate)
                h_setup += f"<li><span>Implantação {n}</span><span class='item-detalhe'>{int(h)}h x R$ {f_br(v_rate)} | Total: R$ {f_br(h*v_rate)}</span></li>"
            if ads > 0:
                t_setup += ads; h_setup += f"<li><span>Taxa de Adesão {n}</span><span class='item-detalhe'>1 un x R$ {f_br(ads)} | Total: R$ {f_br(ads)}</span></li>"

    with res_cols[0]:
        st.markdown(f'''<div class="resumo-card"><span class="resumo-label">Investimento Implantação (Setup)</span><div class="resumo-valor">R$ {f_br(t_setup)}</div><div style="font-weight:bold;">{parcelas_setup}x de R$ {f_br(t_setup/parcelas_setup)}</div><div class="resumo-subtitulo">DETALHAMENTO SETUP</div><ul class="lista-itens">{h_setup if h_setup else "<li>Nenhum item</li>"}</ul></div>''', unsafe_allow_html=True)

    t_mensal, h_m = 0.0, ""
    for n in sorted(st.session_state.sel_m):
        q = st.session_state[f"perm_val_{n}"]
        if q > 0:
            v_u = sistemas_db[n]['valor']; v_liq_u = v_u * (1 - (desc/100))
            t_mensal += (q * v_liq_u)
            h_m += f"<li><span>{n}</span><span class='item-detalhe'>{int(q)} un x R$ {f_br(v_u)} | Total: R$ {f_br(q*v_liq_u)}</span></li>"
            vincs = [id_to_name.get(v['id_filho']) for v in vinculos_db.get(name_to_id.get(n), []) if v['tipo'] == 'incluso']
            for inc in vincs: h_m += f"<li class='item-incluso'><span>└ {inc}</span><span>Incluso</span></li>"
            if n == "VR ERP PRO" and not vincs:
                for inc in ["VR Promo", "VR Carteira Digital", "VR Analytics"]: h_m += f"<li class='item-incluso'><span>└ {inc}</span><span>Incluso</span></li>"

    with res_cols[1]:
        d_h = f'<div style="color:#2e7d32; font-weight:bold;">Desconto: {desc}%</div>' if (exibir_detalhe_desc and desc > 0) else '<div style="height:21px"></div>'
        st.markdown(f'''<div class="resumo-card" style="border-top-color:#2e7d32;"><span class="resumo-label">Manutenção Mensal</span><div class="resumo-valor" style="color:#2e7d32;">R$ {f_br(t_mensal)}</div>{d_h}<div style="font-weight:bold;">Início: {faturamento_sistema}</div><div class="resumo-subtitulo">SISTEMAS</div><ul class="lista-itens">{h_m if h_m else "<li>Nenhum</li>"}</ul></div>''', unsafe_allow_html=True)

    if perfil_venda == "Executivo (Rua)":
        t_d, h_d = 0.0, ""
        for n in st.session_state.sel_d:
            q = st.session_state[f"perm_val_{n}"]
            if q > 0:
                v_u = despesas_db[n]['valor']; t_d += (q * v_u)
                h_d += f"<li><span>{n}</span><span class='item-detalhe'>{int(q)} un x R$ {f_br(v_u)} | Total: R$ {f_br(q*v_u)}</span></li>"
        with res_cols[2]:
            st.markdown(f'''<div class="resumo-card" style="border-top-color:#1976d2;"><span class="resumo-label">Despesas do Projeto</span><div class="resumo-valor" style="color:#1976d2;">R$ {f_br(t_d)}</div><div style="color:#d32f2f; font-weight:bold; font-size:0.8rem;">{regra_despesas}</div><div class="resumo-subtitulo">DETALHAMENTO</div><ul class="lista-itens">{h_d if h_d else "<li>Sem despesas</li>"}</ul></div>''', unsafe_allow_html=True)

# ==========================================
# TELA 3: CONSULTA DE PREÇO (SIMULADOR INTELIGENTE)
# ==========================================
elif tela == "Consulta de Preço":
    st.markdown('<h1 class="hero-title">ANÁLISE TÉCNICA</h1>', unsafe_allow_html=True)
    st.markdown('<div class="mapeamento-container"><h3 style="margin:0; color:#ff6600;">🔍 Simulador de Negociação Individual</h3></div>', unsafe_allow_html=True)
    cb, cd = st.columns([2, 1])
    p_sel = cb.selectbox("Selecione o produto:", sorted(list(full_db.keys())))
    desc_s = cd.number_input("Simular Desconto (%)", 0.0, 30.0, 0.0, 0.5)
    
    v_h_base = servicos_db.get("Implantação e Treinamento", {}).get("valor", 0.0)
    
    if p_sel:
        d = full_db[p_sel]; v_b = d.get('valor', 0.0); v_l = v_b * (1 - (desc_s/100))
        p_id = name_to_id.get(p_sel)
        is_sistema = (d.get('typeproductid') == 604)
        
        t_s = 0.0
        h_s = ""
        
        # Leitura da Tabela Relacional (Sincronizado com o Backoffice)
        if p_id in vinculos_db and any(v['tipo'] in ['projeto', 'adesao'] for v in vinculos_db[p_id]):
            for r in vinculos_db[p_id]:
                if r['tipo'] in ['projeto', 'adesao']:
                    f_nm = id_to_name.get(r['id_filho'])
                    f_val = full_db.get(f_nm, {}).get('valor', 0.0)
                    f_q = r['qtd']
                    t_s += (f_q * f_val)
                    uni = "h" if r['tipo'] == 'projeto' else "un"
                    h_s += f"<li><span>{f_nm}</span><span class='item-detalhe'>{int(f_q)}{uni} x R$ {f_br(f_val)} | Total: R$ {f_br(f_q*f_val)}</span></li>"
        else:
            # Fallback Antigo (Caso não existam vínculos criados)
            h_p, v_he, ads = d.get('horas_padrao', 0.0), d.get('valor_hora_implantacao', 0.0), d.get('adesao_vinculada', 0.0)
            rt = v_he if v_he > 0 else v_h_base
            t_s = (h_p * rt) + ads
            if h_p > 0: h_s += f"<li><span>Implantação</span><span class='item-detalhe'>{h_p}h x R$ {f_br(rt)} | Total: R$ {f_br(h_p*rt)}</span></li>"
            if ads > 0: h_s += f"<li><span>Taxa de Adesão</span><span class='item-detalhe'>1 un x R$ {f_br(ads)} | Total: R$ {f_br(ads)}</span></li>"
            
        if is_sistema:
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f'<div class="resumo-card"><span>Investimento de Setup</span><div class="resumo-valor">R$ {f_br(t_s)}</div><div class="resumo-subtitulo">COMPOSIÇÃO</div><ul class="lista-itens">{h_s if h_s else "<li>Isento</li>"}</ul></div>', unsafe_allow_html=True)
            with c2:
                html_b = f'<span style="text-decoration: line-through; color: #777; font-size: 0.9rem;">R$ {f_br(v_b)}</span>' if desc_s > 0 else ""
                st.markdown(f'<div class="resumo-card" style="border-top-color:#2e7d32;"><span>Investimento Mensal</span><div class="resumo-valor" style="color:#2e7d32;">R$ {f_br(v_l)}</div>{html_b}<div class="resumo-subtitulo">DETALHE</div><ul class="lista-itens"><li><span>Desconto Aplicado</span><span class="item-detalhe">{f_pct(desc_s)}%</span></li></ul></div>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div class="resumo-card" style="border-top-color:#262730; min-height: auto;"><span>Resumo Anual</span><div style="margin-top:15px;"><p><b>Economia Mensal:</b> R$ {f_br(v_b-v_l)}</p><p><b>Economia Anual:</b> R$ {f_br((v_b-v_l)*12)}</p></div></div>', unsafe_allow_html=True)
        else:
            # Inteligência de Serviços (Sem cálculo de mensalidade recorrente)
            c1, c2 = st.columns(2)
            with c1:
                html_b = f'<span style="text-decoration: line-through; color: #777; font-size: 0.9rem;">R$ {f_br(v_b)}</span>' if desc_s > 0 else ""
                st.markdown(f'<div class="resumo-card"><span>Setup / Serviço Único</span><div class="resumo-valor">R$ {f_br(v_l)}</div>{html_b}<div class="resumo-subtitulo">DETALHE</div><ul class="lista-itens"><li><span>Desconto Aplicado</span><span class="item-detalhe">{f_pct(desc_s)}%</span></li></ul></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="resumo-card" style="border-top-color:#262730; min-height: auto;"><span>Resumo do Desconto</span><div style="margin-top:15px;"><p><b>Economia Total Gerada:</b> R$ {f_br(v_b-v_l)}</p><p style="color:#777; font-size:0.85rem;">*Este item não possui faturamento recorrente mensal.</p></div></div>', unsafe_allow_html=True)
