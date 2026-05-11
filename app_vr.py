import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import urllib.parse
import os

# ==========================================
# CONFIGURAÇÕES INICIAIS E CONTROLE DE VERSÃO
# ==========================================
st.set_page_config(page_title="VR Software | Sales Intelligence", layout="wide")

APP_VERSION = "v1.6.0 - Power User Stable"
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

# FUNÇÕES DE FORMATAÇÃO BRASILEIRA (PYTHON -> TELA)
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
    status_msg, status_cor = "🔴 Desconectado", "#ef4444"
    try:
        if CONN_STR:
            engine = create_engine(CONN_STR)
            df = pd.read_sql("SELECT * FROM product", engine)
            status_msg, status_cor = "PostgreSQL (Online)", "#22c55e"
            
            df.columns = [str(c).strip().lower() for c in df.columns]
            df = df.drop_duplicates(subset=['produto'], keep='last')
            
            # Type Safety rigoroso (Decimais/Floats)
            cols_num = ['valor', 'horas_padrao', 'adesao_vinculada', 'valor_hora_implantacao', 'typeproductid']
            for col in cols_num:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

            full = df.set_index('produto').to_dict('index')
            id_to_name = df.set_index('id')['produto'].to_dict() if 'id' in df.columns else {}
            name_to_id = {v: k for k, v in id_to_name.items()}

            sist = {k: v for k, v in full.items() if v.get('typeproductid') == 604}
            serv = {k: v for k, v in full.items() if v.get('typeproductid') == 606 and not any(x in k.lower() for x in ['km', 'hospedagem', 'logistica', 'alimentacao'])}
            desp = {k: v for k, v in full.items() if any(x in k.lower() for x in ['km', 'hospedagem', 'logistica', 'alimentacao'])}
            
            # Carrega Vínculos Relacionais (Tabela Nova)
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
            except Exception: pass 
            
            return sist, serv, desp, full, id_to_name, name_to_id, vinculos_db, status_msg, status_cor, df, df_vinc
    except Exception as e:
        st.error(f"Erro ao carregar banco: {e}")
    return {}, {}, {}, {}, {}, {}, {}, status_msg, status_cor, pd.DataFrame(), pd.DataFrame()

sist_db, serv_db, desp_db, full_db, id_to_name, name_to_id, vinculos_db, db_status, db_cor, df_raw, df_vinc = carregar_dados_vendas()

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

# ESTADO GLOBAL (TYPE SAFETY)
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
# LÓGICA DE NEGÓCIO (BACK-END)
# ==========================================
def processar_regras_colaterais():
    """Lê a tabela de vínculos e injeta no estado sem conflitos de nomes"""
    for m_nome in st.session_state.sel_m:
        p_id = name_to_id.get(m_nome)
        if p_id and p_id in vinculos_db:
            for r in vinculos_db[p_id]:
                f_nome = id_to_name.get(r['id_filho'])
                if f_nome and r['tipo'] in ['projeto', 'adesao']:
                    if f_nome not in st.session_state.sel_i:
                        st.session_state.sel_i.append(f_nome)
                        st.session_state[f"perm_val_{f_nome}"] = float(r['qtd'])

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=180)
    tela = st.radio("Navegação:", ["Gerador de Proposta", "Consulta de Preço", "Painel Admin"])
    if tela == "Gerador de Proposta":
        st.write("---")
        mapeamento_ativo = st.toggle("Mapeamento Inteligente", value=False)
        modo_apresentacao = st.toggle("Modo Apresentação")
        perfil_venda = st.selectbox("Perfil", ["Executivo (Rua)", "CS (Base)"])
        desc = st.number_input("Desconto (%)", 0.0, 30.0, 0.0, 0.5)
        exibir_detalhe_desc = st.toggle("Exibir Desconto", value=True)
        faturamento_sistema = st.selectbox("Início", ["Na assinatura", "30 dias", "60 dias", "Após implantação"])
        parcelas_setup = st.selectbox("Parcelas Setup", [1, 2, 3, 4, 5, 6, 10, 12], index=3)
    st.markdown(f'''<hr><div style="font-size:0.8rem; color:{db_cor};">● {db_status}</div><div style="font-size:0.7rem; color:#888;">{APP_VERSION}</div>''', unsafe_allow_html=True)

# ==========================================
# TELA 1: PAINEL ADMIN (TERMINAL SEGURO)
# ==========================================
if tela == "Painel Admin":
    st.markdown('<h1 class="hero-title">BACKOFFICE</h1>', unsafe_allow_html=True)
    if st.text_input("Senha Admin:", type="password") == ADMIN_PASS_REQUIRED:
        st.success("Acesso Autorizado")
        
        t_vinc, t_sql, t_cat = st.tabs(["🔗 Vínculos Relacionais", "💻 Terminal SQL Seguro", "🗄️ Catálogo Completo"])
        
        with t_vinc:
            st.markdown("### Criar Nova Regra de Vínculo")
            with st.form("form_vinc"):
                c1, c2, c3, c4 = st.columns([2,2,1,1])
                p_sel = c1.selectbox("Se o vendedor escolher:", sorted(list(sist_db.keys())))
                f_sel = c2.selectbox("Incluir este item:", sorted(list(full_db.keys())))
                tp_sel = c3.selectbox("Tipo:", ["projeto", "adesao", "incluso"])
                qt_sel = c4.number_input("Qtd/Horas:", min_value=0.0, value=1.0)
                if st.form_submit_button("Salvar Regra"):
                    try:
                        engine = create_engine(CONN_STR)
                        with engine.begin() as conn:
                            conn.execute(text("INSERT INTO product_vinculo (id_produto_pai, id_produto_filho, tipo_vinculo, quantidade_padrao) VALUES (:p, :f, :t, :q)"), 
                                         {"p": name_to_id[p_sel], "f": name_to_id[f_sel], "t": tp_sel, "q": qt_sel})
                        st.success("Regra Salva!"); st.cache_data.clear()
                    except Exception as e: st.error(e)
            st.dataframe(df_vinc, use_container_width=True)

        with t_sql:
            st.warning("⚠️ Terminal Blindado: DROP, DELETE e TRUNCATE são bloqueados automaticamente.")
            query = st.text_area("Comando SQL:", height=150, placeholder="SELECT * FROM product WHERE produto ILIKE '%conciliador%';")
            if st.button("▶️ Executar no Postgres"):
                q_low = query.lower()
                if any(p in q_low for p in ["drop ", "delete ", "truncate "]):
                    st.error("🚨 COMANDO BLOQUEADO: Operação não permitida por segurança.")
                else:
                    try:
                        engine = create_engine(CONN_STR)
                        if q_low.strip().startswith("select"):
                            res = pd.read_sql(query, engine)
                            st.success(f"{len(res)} linhas."); st.dataframe(res)
                        else:
                            with engine.begin() as conn: r = conn.execute(text(query))
                            st.success(f"Sucesso! Afetadas: {r.rowcount}"); st.cache_data.clear()
                    except Exception as e: st.error(f"Erro SQL: {e}")

        with t_cat: st.dataframe(df_raw, use_container_width=True)

# ==========================================
# TELA 2: GERADOR DE PROPOSTA (GABARITO v1.0.0)
# ==========================================
elif tela == "Gerador de Proposta":
    
    def aplicar_mapeamento():
        pdv_map = {"VR PDV Convencional": st.session_state.m_pdv_conv, "PDV Touchscreen": st.session_state.m_pdv_touch, "PDV Selfcheckout": st.session_state.m_pdv_self}
        for p, qtd in pdv_map.items():
            if p in sist_db:
                st.session_state[f"perm_val_{p}"] = float(qtd)
                if qtd > 0 and p not in st.session_state.sel_m: st.session_state.sel_m.append(p)
        
        if st.session_state.m_tef == "SiTef Express":
            total = sum(pdv_map.values())
            sk = "SiTef Express até 3 PDVs" if total <= 3 else "SiTef Express até 6 PDVs" if total <= 6 else "SiTef Express até 8 PDVs" if total <= 8 else "SiTef Express acima de 8 PDVs"
            if sk in sist_db:
                st.session_state[f"perm_val_{sk}"] = 1.0
                if sk not in st.session_state.sel_m: st.session_state.sel_m.append(sk)

        exp = {"E-Commerce": st.session_state.m_ecommerce, "VR ERP PRO": st.session_state.m_erp_pro, "Gerenciador XML": st.session_state.m_xml, "VR Backup": st.session_state.m_backup}
        for k, v in exp.items():
            if k in sist_db and v:
                st.session_state[f"perm_val_{k}"] = 1.0
                if k not in st.session_state.sel_m: st.session_state.sel_m.append(k)

    if not modo_apresentacao:
        st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)
        if mapeamento_ativo:
            st.markdown('<div class="mapeamento-container"><h3 style="margin:0; color:#ff6600;">🛒 Mapeamento da Operação</h3></div>', unsafe_allow_html=True)
            st.selectbox("Combo Rápido", ["Montar Manualmente", "Padrão Pequeno Porte"], key="tmp_combo", on_change=sync_combo)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.number_input("PDV Convencional", 0.0, step=1.0, key="tmp_pdv_conv", value=st.session_state.m_pdv_conv, on_change=sync_state, args=("m_pdv_conv", "tmp_pdv_conv"))
                st.number_input("PDV Touch", 0.0, step=1.0, key="tmp_pdv_touch", value=st.session_state.m_pdv_touch, on_change=sync_state, args=("m_pdv_touch", "tmp_pdv_touch"))
            with c2:
                st.selectbox("TEF", ["Não utiliza", "SiTef Express", "VR TEF"], key="tmp_tef", index=["Não utiliza", "SiTef Express", "VR TEF"].index(st.session_state.m_tef), on_change=sync_state, args=("m_tef", "tmp_tef"))
                st.number_input("Semanas", 0.0, step=1.0, key="tmp_semanas", value=st.session_state.m_semanas, on_change=sync_state, args=("m_semanas", "tmp_semanas"))
            with c3:
                sc1, sc2, sc3 = st.columns(3)
                sc1.toggle("ERP PRO", key="tmp_erp_pro", value=st.session_state.m_erp_pro, on_change=sync_state, args=("m_erp_pro", "tmp_erp_pro"))
                sc2.toggle("XML", key="tmp_xml", value=st.session_state.m_xml, on_change=sync_state, args=("m_xml", "tmp_xml"))
                sc3.toggle("Backup", key="tmp_backup", value=st.session_state.m_backup, on_change=sync_state, args=("m_backup", "tmp_backup"))
                b1, b2 = st.columns(2)
                b1.button("✨ Aplicar", on_click=aplicar_mapeamento, use_container_width=True)
                b2.button("🗑️ Limpar", on_click=limpar_tudo, use_container_width=True)
        st.write("---")

    processar_regras_colaterais()

    # INCLUSÃO MANUAL
    c1, c2, c3 = st.columns(3) if perfil_venda == "Executivo (Rua)" else (*st.columns(2), None)
    with c1:
        st.markdown('<div class="section-header"><span class="section-title">SETUP E SERVIÇOS</span></div>', unsafe_allow_html=True)
        st.session_state.sel_i = st.multiselect("Itens", list(serv_db.keys()), default=st.session_state.sel_i)
        for i in st.session_state.sel_i:
            st.number_input(f"{i}", 0.0, step=1.0, value=st.session_state[f"perm_val_{i}"], key=f"tmp_i_{i}", on_change=sync_state, args=(f"perm_val_{i}", f"tmp_i_{i}"))
    with c2:
        st.markdown('<div class="section-header"><span class="section-title">MENSALIDADES</span></div>', unsafe_allow_html=True)
        st.session_state.sel_m = st.multiselect("Sistemas", list(sist_db.keys()), default=st.session_state.sel_m)
        for i in st.session_state.sel_m:
            st.number_input(f"{i}", 0.0, step=1.0, value=st.session_state[f"perm_val_{i}"], key=f"tmp_m_{i}", on_change=sync_state, args=(f"perm_val_{i}", f"tmp_m_{i}"))
    if c3:
        with c3:
            st.markdown('<div class="section-header"><span class="section-title">LOGÍSTICA</span></div>', unsafe_allow_html=True)
            st.session_state.sel_d = st.multiselect("Despesas", list(desp_db.keys()), default=st.session_state.sel_d)
            for i in st.session_state.sel_d:
                st.number_input(f"{i}", 0.0, step=1.0, value=st.session_state[f"perm_val_{i}"], key=f"tmp_d_{i}", on_change=sync_state, args=(f"perm_val_{i}", f"tmp_d_{i}"))

    # CARDS DE RESUMO
    st.markdown("<h2 style='text-align:center; font-weight:800; margin-top:30px;'>RESUMO DO INVESTIMENTO</h2>", unsafe_allow_html=True)
    res_cols = st.columns(3) if perfil_venda == "Executivo (Rua)" else st.columns([1, 2, 2, 1])[1:3]
    
    total_setup, html_setup = 0.0, ""
    for n in st.session_state.sel_i:
        q = st.session_state[f"perm_val_{n}"]
        if q > 0:
            v_un = serv_db.get(n, full_db.get(n, {'valor':0.0}))['valor']
            total_setup += (q * v_un); html_setup += f"<li><span>{n}</span><span class='item-detalhe'>R$ {f_br(q*v_un)}</span></li>"
    
    # Fallback para sistemas sem vinculo no banco
    v_hora_base = serv_db.get("Implantação e Treinamento", {}).get("valor", 0.0)
    for n in st.session_state.sel_m:
        if name_to_id.get(n) not in vinculos_db:
            d = sist_db[n]; h = d.get('horas_padrao', 0.0); ads = d.get('adesao_vinculada', 0.0)
            if h > 0:
                v_imp = h * (d.get('valor_hora_implantacao', 0.0) or v_hora_base)
                total_setup += v_imp; html_setup += f"<li><span>Implantação {n}</span><span class='item-detalhe'>R$ {f_br(v_imp)}</span></li>"
            if ads > 0:
                total_setup += ads; html_setup += f"<li><span>Adesão {n}</span><span class='item-detalhe'>R$ {f_br(ads)}</span></li>"

    with res_cols[0]:
        st.markdown(f'''<div class="resumo-card"><span>Setup Inicial</span><div class="resumo-valor">R$ {f_br(total_setup)}</div><div style="font-weight:bold;">{parcelas_setup}x de R$ {f_br(total_setup/parcelas_setup)}</div><div class="resumo-subtitulo">DETALHAMENTO SETUP</div><ul class="lista-itens">{html_setup if html_setup else "<li>Vazio</li>"}</ul></div>''', unsafe_allow_html=True)

    t_mensal, html_m = 0.0, ""
    for n in sorted(st.session_state.sel_m):
        q = st.session_state[f"perm_val_{n}"]
        if q > 0:
            v_liq = (q * sist_db[n]['valor']) * (1 - (desc/100))
            t_mensal += v_liq; html_m += f"<li><span>{n}</span><span class='item-detalhe'>R$ {f_br(v_liq)}</span></li>"
            vincs = [id_to_name.get(v['id_filho']) for v in vinculos_db.get(name_to_id.get(n), []) if v['tipo'] == 'incluso']
            for inc in vincs: html_m += f"<li class='item-incluso'><span>└ {inc}</span><span>Incluso</span></li>"

    with res_cols[1]:
        st.markdown(f'''<div class="resumo-card" style="border-top-color:#2e7d32;"><span>Mensalidade</span><div class="resumo-valor" style="color:#2e7d32;">R$ {f_br(t_mensal)}</div><div style="font-weight:bold;">Início: {faturamento_sistema}</div><div class="resumo-subtitulo">SISTEMAS</div><ul class="lista-itens">{html_m if html_m else "<li>Vazio</li>"}</ul></div>''', unsafe_allow_html=True)

    if perfil_venda == "Executivo (Rua)":
        t_desp, html_d = 0.0, ""
        for n in st.session_state.sel_d:
            q = st.session_state[f"perm_val_{n}"]
            if q > 0:
                v_un = desp_db[n]['valor']; t_desp += (q * v_un)
                html_d += f"<li><span>{n}</span><span class='item-detalhe'>R$ {f_br(q*v_un)}</span></li>"
        with res_cols[2]:
            st.markdown(f'''<div class="resumo-card" style="border-top-color:#1976d2;"><span>Logística</span><div class="resumo-valor" style="color:#1976d2;">R$ {f_br(t_desp)}</div><div style="color:#d32f2f; font-weight:bold; font-size:0.8rem;">{regra_logistica}</div><div class="resumo-subtitulo">DETALHAMENTO</div><ul class="lista-itens">{html_d if html_d else "<li>Vazio</li>"}</ul></div>''', unsafe_allow_html=True)

# ==========================================
# TELA 3: CONSULTA DE PREÇO
# ==========================================
elif tela == "Consulta de Preço":
    st.markdown('<h1 class="hero-title">ANÁLISE</h1>', unsafe_allow_html=True)
    p_sel = st.selectbox("Selecione:", sorted(list(full_db.keys())))
    if p_sel:
        d = full_db[p_sel]
        st.markdown(f'<div class="resumo-card"><span>Preço Unitário</span><div class="resumo-valor">R$ {f_br(d["valor"])}</div></div>', unsafe_allow_html=True)
