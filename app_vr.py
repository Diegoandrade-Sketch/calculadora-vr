import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import urllib.parse # <--- ADICIONE ESTA LINHA AQUI
import os

# ==========================================
# CONFIGURAÇÕES INICIAIS E SEGURANÇA
# ==========================================
st.set_page_config(page_title="VR Software | Sales Intelligence", layout="wide")

# Credenciais seguras puxadas do Streamlit Cloud (ou secrets.toml local)
DB_USER = st.secrets["DB_USER"]
DB_PASS = st.secrets["DB_PASS"]
DB_HOST = st.secrets["DB_HOST"]
DB_PORT = st.secrets["DB_PORT"]
DB_NAME = st.secrets["DB_NAME"]

# Codifica a senha para evitar que caracteres especiais (como @, #, !) quebrem a string
DB_PASS_ENCODED = urllib.parse.quote_plus(DB_PASS)

# Monta a string usando a senha codificada
CONN_STR = f"postgresql://{DB_USER}:{DB_PASS_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ... O resto do código (funções f_br, carregar_dados_vendas_sql, etc) continua igualzinho ...

# FUNÇÕES DE FORMATAÇÃO E LIMPEZA
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

# ==========================================
# CONEXÃO COM O BANCO DE DADOS POSTGRESQL
# ==========================================
@st.cache_data(ttl=60)
def carregar_dados_vendas_sql():
    try:
        engine = create_engine(CONN_STR)
        query = "SELECT * FROM product"
        df = pd.read_sql(query, engine)
        
        df.columns = [str(c).strip().lower() for c in df.columns]
        df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
        
        for col in ['horas_padrao', 'adesao_vinculada', 'valor_hora_implantacao']:
            if col not in df.columns: df[col] = 0.0

        df['valor'] = df['valor'].apply(limpar_valor)
        df['valor_hora_implantacao'] = df['valor_hora_implantacao'].apply(limpar_valor)
        df['adesao_vinculada'] = df['adesao_vinculada'].apply(limpar_valor)

        full = df.set_index('produto').to_dict('index')
        sist = {k: v for k, v in full.items() if 'sist' in str(v.get('tipo', '')).lower()}
        serv = {k: v for k, v in full.items() if 'serv' in str(v.get('tipo', '')).lower()}
        desp = {k: v for k, v in full.items() if 'desp' in str(v.get('tipo', '')).lower()}
        
        return sist, serv, desp, full
    except Exception as e:
        st.error(f"Erro na conexão com PostgreSQL: {e}")
        return {}, {}, {}, {}

sistemas_db, servicos_db, despesas_db, full_db = carregar_dados_vendas_sql()

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
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# ESTADO GLOBAL
# ==========================================
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
    st.session_state.sel_i, st.session_state.sel_m, st.session_state.sel_d = [], [], []
    for nome in full_db.keys(): st.session_state[f"perm_val_{nome}"] = 0

def sync_combo():
    if st.session_state.tmp_combo == "Padrão Pequeno Porte":
        st.session_state.m_pdv_conv, st.session_state.m_tef, st.session_state.m_semanas = 5, "SiTef Express", 3
        st.session_state.m_migracao, st.session_state.m_escopo, st.session_state.m_erp_pro, st.session_state.m_xml, st.session_state.m_mobile = True, True, True, True, 1

# ==========================================
# SIDEBAR
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

# ==========================================
# TELA: GERADOR DE PROPOSTA
# ==========================================
if tela == "Gerador de Proposta":
    
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

        exp_map = {"VR ERP PRO": st.session_state.m_erp_pro, "Gerenciador XML": st.session_state.m_xml, "VR Backup": st.session_state.m_backup}
        for item, ativo in exp_map.items():
            if item in sistemas_db:
                st.session_state[f"perm_val_{item}"] = 1 if ativo else 0
                if ativo and item not in st.session_state.sel_m: st.session_state.sel_m.append(item)

        sem = st.session_state.m_semanas
        serv_map = {"Implantação e Treinamento": sem * 44, "Migração Banco de Dados": 8 if st.session_state.m_migracao else 0}
        for s_item, s_horas in serv_map.items():
            if s_item in servicos_db:
                st.session_state[f"perm_val_{s_item}"] = s_horas
                if s_horas > 0 and s_item not in st.session_state.sel_i: st.session_state.sel_i.append(s_item)

    if not modo_apresentacao:
        st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)
        
        if mapeamento_ativo:
            st.markdown('<div class="mapeamento-container"><h3 style="margin:0; color:#ff6600;">🛒 Mapeamento da Operação</h3></div>', unsafe_allow_html=True)
            st.selectbox("Combo Rápido", ["Montar Manualmente", "Padrão Pequeno Porte"], key="tmp_combo", on_change=sync_combo)
            st.button("✨ Aplicar Inteligência", on_click=aplicar_mapeamento)
            st.button("🗑️ Limpar Tudo", on_click=limpar_tudo)

        col_i, col_m, col_d = st.columns(3) if perfil_venda == "Executivo (Rua)" else (*st.columns(2), None)
        with col_i:
            st.markdown('<div class="section-header"><span class="section-title">IMPLANTAÇÃO E SERVIÇOS</span></div>', unsafe_allow_html=True)
            st.session_state.sel_i = st.multiselect("Serviços", list(servicos_db.keys()), default=[s for s in st.session_state.sel_i if s in servicos_db])
            for i in st.session_state.sel_i:
                st.number_input(f"{i}", min_value=0, key=f"tmp_i_{i}", value=st.session_state[f"perm_val_{i}"], on_change=sync_state, args=(f"perm_val_{i}", f"tmp_i_{i}"))
        with col_m:
            st.markdown('<div class="section-header"><span class="section-title">MENSALIDADES SISTEMAS</span></div>', unsafe_allow_html=True)
            st.session_state.sel_m = st.multiselect("Sistemas", list(sistemas_db.keys()), default=[s for s in st.session_state.sel_m if s in sistemas_db])
            for i in st.session_state.sel_m:
                st.number_input(f"{i}", min_value=0, key=f"tmp_m_{i}", value=st.session_state[f"perm_val_{i}"], on_change=sync_state, args=(f"perm_val_{i}", f"tmp_m_{i}"))

    # --- PARTE 3: RESUMO GERAL ---
    st.markdown("<h2 style='text-align:center; font-weight:800; margin-top:30px;'>RESUMO DO INVESTIMENTO</h2>", unsafe_allow_html=True)
    res_cols = st.columns(3) if perfil_venda == "Executivo (Rua)" else st.columns([1, 2, 2, 1])[1:3]

    total_setup, html_setup = 0.0, ""
    v_hora_base = servicos_db.get("Implantação e Treinamento", {}).get("valor", 0.0)

    for s_nome in st.session_state.sel_i:
        horas = st.session_state[f"perm_val_{s_nome}"]
        if horas > 0:
            v_item = horas * servicos_db[s_nome]['valor']
            total_setup += v_item
            html_setup += f"<li><span>{s_nome}</span><span class='item-detalhe'>{horas}h x R$ {f_br(servicos_db[s_nome]['valor'])} | Total: R$ {f_br(v_item)}</span></li>"

    for m_nome in st.session_state.sel_m:
        d = full_db.get(m_nome, {})
        h_pad, v_h_esp, val_ads = d.get('horas_padrao', 0), d.get('valor_hora_implantacao', 0), d.get('adesao_vinculada', 0.0)
        if h_pad > 0:
            rate = v_h_esp if v_h_esp > 0 else v_hora_base
            total_setup += (h_pad * rate)
            html_setup += f"<li><span>Implantação {m_nome}</span><span class='item-detalhe'>{h_pad}h x R$ {f_br(rate)} | Total: R$ {f_br(h_pad*rate)}</span></li>"
        if val_ads > 0:
            total_setup += val_ads
            html_setup += f"<li><span>Taxa de Adesão {m_nome}</span><span class='item-detalhe'>1 un x R$ {f_br(val_ads)} | Total: R$ {f_br(val_ads)}</span></li>"

    with res_cols[0]:
        st.markdown(f'<div class="resumo-card"><span class="resumo-label">Investimento Implantação (Setup)</span><div class="resumo-valor">R$ {f_br(total_setup)}</div><div style="font-weight:bold;">{parcelas_setup}x de R$ {f_br(total_setup/parcelas_setup)}</div><div class="resumo-subtitulo">DETALHAMENTO SETUP</div><ul class="lista-itens">{html_setup if html_setup else "<li>Nenhum item</li>"}</ul></div>', unsafe_allow_html=True)

    with res_cols[1]:
        t_liq = sum(st.session_state[f"perm_val_{i}"] * sistemas_db[i]["valor"] for i in st.session_state.sel_m if i in sistemas_db) * (1 - (desc/100))
        html_m = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{st.session_state[f'perm_val_{i}']} un x R$ {f_br(sistemas_db[i]['valor'])} | Total: R$ {f_br(st.session_state[f'perm_val_{i}']*sistemas_db[i]['valor'])}</span></li>" for i in st.session_state.sel_m if i in sistemas_db])
        st.markdown(f'<div class="resumo-card" style="border-top-color:#2e7d32;"><span class="resumo-label">Manutenção Mensal</span><div class="resumo-valor" style="color:#2e7d32;">R$ {f_br(t_liq)}</div><div style="font-weight:bold; font-size: 0.9rem;">Início: {faturamento_sistema}</div><div class="resumo-subtitulo">SISTEMAS</div><ul class="lista-itens">{html_m if html_m else "<li>Nenhum</li>"}</ul></div>', unsafe_allow_html=True)

# ==========================================
# TELA: CONSULTA DE PREÇO (SIMULADOR CLEAN)
# ==========================================
elif tela == "Consulta de Preço":
    st.markdown('<h1 class="hero-title">ANÁLISE TÉCNICA</h1>', unsafe_allow_html=True)
    st.markdown('<div class="mapeamento-container"><h3 style="margin:0; color:#ff6600;">🔍 Simulador de Negociação Individual</h3></div>', unsafe_allow_html=True)
    
    if full_db:
        col_busca, col_desc = st.columns([2, 1])
        with col_busca: p_sel = st.selectbox("Selecione o produto:", sorted(list(full_db.keys())))
        with col_desc: desc_simulacao = st.number_input("Simular Desconto (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.5, key="desc_sim")

        if p_sel:
            d = full_db[p_sel]
            v_mensal_bruto, v_hora_base = d.get('valor', 0.0), servicos_db.get("Implantação e Treinamento", {}).get("valor", 0.0)
            v_mensal_liq = v_mensal_bruto * (1 - (desc_simulacao / 100))
            h_pad, v_h_esp, v_ads = d.get('horas_padrao', 0), d.get('valor_hora_implantacao', 0), d.get('adesao_vinculada', 0.0)
            rate = v_h_esp if v_h_esp > 0 else v_hora_base
            v_setup_total = (h_pad * rate) + v_ads
            
            c1, c2, c3 = st.columns(3)
            with c1:
                html_sim_setup = ""
                if h_pad > 0: html_sim_setup += f"<li><span>Implantação</span><span class='item-detalhe'>{h_pad}h x R$ {f_br(rate)} | Total: R$ {f_br(h_pad*rate)}</span></li>"
                if v_ads > 0: html_sim_setup += f"<li><span>Taxa de Adesão {p_sel}</span><span class='item-detalhe'>1 un x R$ {f_br(v_ads)} | Total: R$ {f_br(v_ads)}</span></li>"
                bloco_setup = f'<div class="resumo-subtitulo">COMPOSIÇÃO</div><ul class="lista-itens">{html_sim_setup}</ul>' if html_sim_setup else ""
                st.markdown(f'<div class="resumo-card"><span class="resumo-label">Investimento de Setup</span><div class="resumo-valor">R$ {f_br(v_setup_total)}</div><div style="font-weight:bold;">Sugestão: 4x de R$ {f_br(v_setup_total/4)}</div>{bloco_setup}</div>', unsafe_allow_html=True)

            with c2:
                html_bruto = f'<span style="text-decoration: line-through; color: #777; font-size: 0.9rem;">R$ {f_br(v_mensal_bruto)}</span>' if desc_simulacao > 0 else ""
                bloco_mensal = f'<div class="resumo-subtitulo">DETALHE</div><ul class="lista-itens"><li><span>Desconto Aplicado</span><span class="item-detalhe">{f_pct(desc_simulacao)}% off</span></li><li><span>Valor Original</span><span class="item-detalhe">R$ {f_br(v_mensal_bruto)}</span></li></ul>' if desc_simulacao > 0 else ""
                st.markdown(f'<div class="resumo-card" style="border-top-color:#2e7d32;"><span class="resumo-label">Investimento Mensal</span><div class="resumo-valor" style="color:#2e7d32;">R$ {f_br(v_mensal_liq)}</div>{html_bruto}{bloco_mensal}</div>', unsafe_allow_html=True)

            with c3:
                st.markdown(f'<div class="resumo-card" style="border-top-color:#262730; min-height: auto;"><span class="resumo-label">Resumo da Negociação</span><div style="margin-top:15px; font-size:0.95rem; color:#444;"><p><b>Desconto:</b> {f_pct(desc_simulacao)}%</p><p><b>Economia Mensal:</b> R$ {f_br(v_mensal_bruto - v_mensal_liq)}</p><p><b>Economia Anual:</b> R$ {f_br((v_mensal_bruto - v_mensal_liq)*12)}</p><hr><p style="font-size: 0.85rem; color: #666;"><i>Interface otimizada para negociações individuais. O detalhamento se oculta automaticamente quando os valores base são 0.</i></p></div></div>', unsafe_allow_html=True)
