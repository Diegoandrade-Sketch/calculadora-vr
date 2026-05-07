import streamlit as st
import pandas as pd
import os

# ==========================================
# CONFIGURAÇÕES INICIAIS E BANCO DE DADOS
# ==========================================
st.set_page_config(page_title="VR Software | Sales Intelligence", layout="wide")

SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTgmdf_FgFd91dkm5zoD0l6l2ailLhCsEV-3pyFsQxRzoyNw2E96eQQoCYkfxHitA9oCIvfaI30-k-2/pub?output=csv"
EXCEL_FILE = "tabela_preco_chat.xlsx"

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
        else:
            df = pd.read_csv(SHEET_URL)
        
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # Mapeamento de colunas dinâmico para suportar novas inteligências
        col_prod = 'produto'
        col_val = 'valor'
        col_tipo = 'tipo'
        col_desc = 'descricao'
        col_h_padrao = 'horas_padrão'
        col_adesao = 'adesão_vinculada'

        df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
        df[col_val] = df[col_val].apply(limpar_valor)
        
        # Garantir que colunas novas existam para não quebrar o código
        if col_h_padrao not in df.columns: df[col_h_padrao] = 0
        if col_adesao not in df.columns: df[col_adesao] = ""

        full = df.set_index(col_prod).to_dict('index')
        sist = {k: v for k, v in full.items() if 'sist' in str(v[col_tipo]).lower()}
        serv = {k: v for k, v in full.items() if 'serv' in str(v[col_tipo]).lower()}
        desp = {k: v for k, v in full.items() if 'desp' in str(v[col_tipo]).lower()}
        
        return sist, serv, desp, full
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return {}, {}, {}, {}

sistemas_db, servicos_db, despesas_db, full_db = carregar_dados_vendas()

# ESTILIZAÇÃO CSS
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #ffffff 0%, #fff5ed 100%); }
    .hero-title { color: #262730; font-size: 4.5rem; font-weight: 900; margin: 0; line-height: 1; text-transform: uppercase; letter-spacing: -3px; }
    .mapeamento-container { background-color: #ffffff; border-left: 10px solid #ff6600; padding: 20px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .resumo-card { background-color: #ffffff; border: 1px solid #f0f0f0; border-top: 8px solid #ff6600; padding: 25px; border-radius: 8px; min-height: 450px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); display: flex; flex-direction: column; }
    .resumo-valor { color: #ff6600; font-size: 2.3rem; font-weight: 900; margin-bottom: 5px; }
    .item-detalhe { color: #333; font-size: 0.95rem; font-weight: 700; background-color: #fcfcfc; padding: 2px 8px; border-radius: 4px; border: 1px solid #eee; }
    .section-header { background: linear-gradient(90deg, #ff6600 0%, #ff944d 100%); padding: 8px 15px; border-radius: 5px; margin-bottom: 15px; margin-top: 20px; }
    .section-title { color: #ffffff; font-size: 1.1rem; font-weight: bold; margin: 0; }
    .lista-itens { list-style-type: none; padding-left: 0; margin-top: 10px; flex-grow: 1; }
    .lista-itens li { padding: 8px 0; border-bottom: 1px dashed #e0e0e0; display: flex; justify-content: space-between; align-items: center; gap: 10px; }
    .item-incluso { padding-left: 20px !important; color: #777; font-size: 0.85rem; font-style: italic; border-bottom: none !important; }
    </style>
    """, unsafe_allow_html=True)

# ESTADO GLOBAL
init_state = {
    'm_combo': "Montar Manualmente", 'm_pdv_conv': 0, 'm_pdv_touch': 0, 'm_pdv_self': 0, 'm_semanas': 0, 'm_mobile': 0,
    'm_tef': "Não utiliza", 'm_migracao': False, 'm_ecommerce': False, 'm_app': False, 'm_connect': False,
    'm_erp_pro': False, 'm_xml': False, 'm_escopo': False, 'm_controller': False, 'm_cartaz': False, 'm_masterfisco': False, 'm_backup': False
}

if 'sel_i' not in st.session_state: st.session_state.sel_i = []
if 'sel_m' not in st.session_state: st.session_state.sel_m = []
if 'sel_d' not in st.session_state: st.session_state.sel_d = []

for k, v in init_state.items():
    if k not in st.session_state: st.session_state[k] = v

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
    st.session_state.m_combo = combo
    if combo == "Padrão Pequeno Porte":
        st.session_state.m_pdv_conv, st.session_state.m_tef, st.session_state.m_semanas = 5, "SiTef Express", 3
        st.session_state.m_migracao, st.session_state.m_escopo, st.session_state.m_erp_pro, st.session_state.m_xml, st.session_state.m_mobile = True, True, True, True, 1

# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=180)
    tela = st.radio("Navegação:", ["Gerador de Proposta", "Consulta de Preço"])
    st.write("---")
    if tela == "Gerador de Proposta":
        mapeamento_ativo = st.toggle("Mapeamento Inteligente", value=False)
        modo_apresentacao = st.toggle("Modo Apresentação")
        perfil_venda = st.selectbox("Perfil do Cliente", ["Executivo (Rua)", "CS (Base)"])
        desc = st.number_input("Desconto (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.5)
        exibir_detalhe_desc = st.toggle("Exibir Desconto na Tela", value=True)
        faturamento_sistema = st.selectbox("Início Mensalidade", ["Na assinatura", "30 dias", "60 dias", "Após implantação"])
        parcelas_setup = st.selectbox("Parcelas Setup", [1, 2, 3, 4, 5, 6], index=3)
        regra_logistica = st.selectbox("Faturamento Logística", ["Faturamento na assinatura do contrato", "Faturamento ao término da Implantação"])

# ==========================================
# PARTES 1, 2 e 3: GERADOR DE PROPOSTA
# ==========================================
if tela == "Gerador de Proposta":
    
    def aplicar_mapeamento():
        # PDVs
        pdv_map = {"VR PDV Convencional": st.session_state.m_pdv_conv, "PDV Touchscreen": st.session_state.m_pdv_touch, "PDV Selfcheckout": st.session_state.m_pdv_self}
        for p, qtd in pdv_map.items():
            if p in sistemas_db:
                st.session_state[f"perm_val_{p}"] = qtd
                st.session_state[f"tmp_m_{p}"] = qtd
                if qtd > 0 and p not in st.session_state.sel_m: st.session_state.sel_m.append(p)
                elif qtd == 0 and p in st.session_state.sel_m: st.session_state.sel_m.remove(p)
        
        # TEF
        total_pdvs = sum(pdv_map.values())
        st.session_state.sel_m = [item for item in st.session_state.sel_m if "SiTef" not in item]
        if st.session_state.m_tef == "SiTef Express":
            escolhido = "SiTef Express até 3 PDVs" if total_pdvs <= 3 else "SiTef Express até 6 PDVs" if total_pdvs <= 6 else "SiTef Express até 8 PDVs" if total_pdvs <= 8 else "SiTef Express acima de 8 PDVs"
            if escolhido in sistemas_db:
                st.session_state[f"perm_val_{escolhido}"] = 1
                st.session_state[f"tmp_m_{escolhido}"] = 1
                st.session_state.sel_m.append(escolhido)

        # Sistemas Extras
        exp_map = {"E-Commerce": st.session_state.m_ecommerce, "M-Commerce": st.session_state.m_app, "VR Connect (Android/IOS)": st.session_state.m_connect, "VR ERP PRO": st.session_state.m_erp_pro, "Gerenciador XML": st.session_state.m_xml, "VR Controller 360": st.session_state.m_controller, "VR Cartaz": st.session_state.m_cartaz, "VR MasterFisco Brasil": st.session_state.m_masterfisco, "VR Backup": st.session_state.m_backup}
        for item, ativo in exp_map.items():
            if item in sistemas_db:
                st.session_state[f"perm_val_{item}"] = 1 if ativo else 0
                st.session_state[f"tmp_m_{item}"] = 1 if ativo else 0
                if ativo and item not in st.session_state.sel_m: st.session_state.sel_m.append(item)
                elif not ativo and item in st.session_state.sel_m: st.session_state.sel_m.remove(item)

        # VR Mobile
        if "VR Mobile" in sistemas_db and st.session_state.m_mobile > 0:
            if "VR Mobile" not in st.session_state.sel_m: st.session_state.sel_m.append("VR Mobile")
            st.session_state[f"perm_val_VR Mobile"] += st.session_state.m_mobile
            st.session_state[f"tmp_m_VR Mobile"] = st.session_state[f"perm_val_VR Mobile"]
            st.session_state.m_mobile = 0
            if 'tmp_mobile' in st.session_state: st.session_state.tmp_mobile = 0

        # Serviços Base
        sem = st.session_state.m_semanas
        serv_map = {"Implantação e Treinamento": sem * 44, "Migração Banco de Dados": 8 if st.session_state.m_migracao else 0, "Definição de Escopo": 8 if st.session_state.m_escopo else 0}
        for s_item, s_horas in serv_map.items():
            if s_item in servicos_db:
                st.session_state[f"perm_val_{s_item}"] = s_horas
                st.session_state[f"tmp_i_{s_item}"] = s_horas
                if s_horas > 0 and s_item not in st.session_state.sel_i: st.session_state.sel_i.append(s_item)

        # Despesas
        if "Alimentacao" in despesas_db: 
            st.session_state[f"perm_val_Alimentacao"] = sem * 10
            st.session_state[f"tmp_d_Alimentacao"] = sem * 10
            if sem > 0: st.session_state.sel_d.append("Alimentacao")
        if "Hospedagem" in despesas_db: 
            st.session_state[f"perm_val_Hospedagem"] = sem * 4
            st.session_state[f"tmp_d_Hospedagem"] = sem * 4
            if sem > 0: st.session_state.sel_d.append("Hospedagem")

    if not modo_apresentacao:
        st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)
        if mapeamento_ativo:
            st.markdown('<div class="mapeamento-container"><h3 style="margin:0; color:#ff6600;">🛒 Mapeamento da Operação</h3></div>', unsafe_allow_html=True)
            st.selectbox("Combo Rápido", ["Montar Manualmente", "Padrão Pequeno Porte"], key="tmp_combo", on_change=sync_combo)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.number_input("PDV Convencional", min_value=0, key="tmp_pdv_conv", value=st.session_state.m_pdv_conv, on_change=sync_state, args=("m_pdv_conv", "tmp_pdv_conv"))
                st.number_input("PDV Touchscreen", min_value=0, key="tmp_pdv_touch", value=st.session_state.m_pdv_touch, on_change=sync_state, args=("m_pdv_touch", "tmp_pdv_touch"))
                st.number_input("PDV Selfcheckout", min_value=0, key="tmp_pdv_self", value=st.session_state.m_pdv_self, on_change=sync_state, args=("m_pdv_self", "tmp_pdv_self"))
            with c2:
                st.selectbox("Solução de TEF", ["Não utiliza", "SiTef Express", "VR TEF"], key="tmp_tef", index=["Não utiliza", "SiTef Express", "VR TEF"].index(st.session_state.m_tef), on_change=sync_state, args=("m_tef", "tmp_tef"))
                st.number_input("Semanas Implantação", min_value=0, key="tmp_semanas", value=st.session_state.m_semanas, on_change=sync_state, args=("m_semanas", "tmp_semanas"))
                st.checkbox("Migração?", key="tmp_migracao", value=st.session_state.m_migracao, on_change=sync_state, args=("m_migracao", "tmp_migracao"))
                st.checkbox("Escopo?", key="tmp_escopo", value=st.session_state.m_escopo, on_change=sync_state, args=("m_escopo", "tmp_escopo"))
            with c3:
                st.number_input("VR Mobile", min_value=0, key="tmp_mobile", value=st.session_state.m_mobile, on_change=sync_state, args=("m_mobile", "tmp_mobile"))
                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    st.toggle("VR ERP PRO", key="tmp_erp_pro", value=st.session_state.m_erp_pro, on_change=sync_state, args=("m_erp_pro", "tmp_erp_pro"))
                    st.toggle("G. XML", key="tmp_xml", value=st.session_state.m_xml, on_change=sync_state, args=("m_xml", "tmp_xml"))
                    st.toggle("Connect", key="tmp_connect", value=st.session_state.m_connect, on_change=sync_state, args=("m_connect", "tmp_connect"))
                with sc2:
                    st.toggle("VR Backup", key="tmp_backup", value=st.session_state.m_backup, on_change=sync_state, args=("m_backup", "tmp_backup"))
                    st.toggle("VR Cartaz", key="tmp_cartaz", value=st.session_state.m_cartaz, on_change=sync_state, args=("m_cartaz", "tmp_cartaz"))
                    st.toggle("E-Commerce", key="tmp_ecommerce", value=st.session_state.m_ecommerce, on_change=sync_state, args=("m_ecommerce", "tmp_ecommerce"))
                with sc3:
                    st.toggle("C. 360", key="tmp_controller", value=st.session_state.m_controller, on_change=sync_state, args=("m_controller", "tmp_controller"))
                    st.toggle("MasterFisco", key="tmp_masterfisco", value=st.session_state.m_masterfisco, on_change=sync_state, args=("m_masterfisco", "tmp_masterfisco"))
                    st.toggle("M-Commerce", key="tmp_app", value=st.session_state.m_app, on_change=sync_state, args=("m_app", "tmp_app"))
                b1, b2 = st.columns(2)
                with b1: st.button("✨ Aplicar Inteligência", on_click=aplicar_mapeamento, use_container_width=True)
                with b2: st.button("🗑️ Limpar Tudo", on_click=limpar_tudo, use_container_width=True)
            st.markdown("---")

        # --- PARTE 2: INCLUSÃO MANUAL ---
        col_i, col_m, col_d = st.columns(3) if perfil_venda == "Executivo (Rua)" else (*st.columns(2), None)
        with col_i:
            st.markdown('<div class="section-header"><span class="section-title">IMPLANTAÇÃO E SERVIÇOS</span></div>', unsafe_allow_html=True)
            st.session_state.sel_i = st.multiselect("Serviços", list(servicos_db.keys()), default=[s for s in st.session_state.sel_i if s in servicos_db])
            for i in st.session_state.sel_i:
                st.number_input(f"{i} (R$ {servicos_db[i]['valor']:,.2f}/h)", min_value=0, value=st.session_state[f"perm_val_{i}"], key=f"tmp_i_{i}", on_change=sync_state, args=(f"perm_val_{i}", f"tmp_i_{i}"))
        with col_m:
            st.markdown('<div class="section-header"><span class="section-title">MENSALIDADES SISTEMAS</span></div>', unsafe_allow_html=True)
            st.session_state.sel_m = st.multiselect("Sistemas", list(sistemas_db.keys()), default=[s for s in st.session_state.sel_m if s in sistemas_db])
            for i in st.session_state.sel_m:
                st.number_input(f"{i} (R$ {sistemas_db[i]['valor']:,.2f}/un)", min_value=0, value=st.session_state[f"perm_val_{i}"], key=f"tmp_m_{i}", on_change=sync_state, args=(f"perm_val_{i}", f"tmp_m_{i}"))
        if col_d:
            with col_d:
                st.markdown('<div class="section-header"><span class="section-title">DESPESAS LOGÍSTICAS</span></div>', unsafe_allow_html=True)
                st.session_state.sel_d = st.multiselect("Despesas", list(despesas_db.keys()), default=[s for s in st.session_state.sel_d if s in despesas_db])
                for i in st.session_state.sel_d:
                    st.number_input(f"{i} (R$ {despesas_db[i]['valor']:,.2f}/un)", min_value=0, value=st.session_state[f"perm_val_{i}"], key=f"tmp_d_{i}", on_change=sync_state, args=(f"perm_val_{i}", f"tmp_d_{i}"))

    # --- PARTE 3: CARD DE RESUMO (TRANSPARÊNCIA TOTAL) ---
    st.markdown("<h2 style='text-align:center; font-weight:800; margin-top:30px;'>RESUMO DO INVESTIMENTO</h2>", unsafe_allow_html=True)
    res_cols = st.columns(3) if perfil_venda == "Executivo (Rua)" else st.columns([1, 2, 2, 1])[1:3]

    # Cálculos dinâmicos de Setup
    total_setup = 0.0
    html_setup = ""
    valor_hora_base = servicos_db.get("Implantação e Treinamento", {}).get("valor", 0.0)

    # 1. Serviços Selecionados Manualmente (Ex: Treinamento Base)
    for s_nome in st.session_state.sel_i:
        horas = st.session_state[f"perm_val_{s_nome}"]
        if horas > 0:
            v_item = horas * servicos_db[s_nome]['valor']
            total_setup += v_item
            html_setup += f"<li><span>{s_nome}</span><span class='item-detalhe'>{horas}h x R$ {servicos_db[s_nome]['valor']:,.2f}</span></li>"

    # 2. Vendas Casadas (Inteligência das colunas novas)
    for m_nome in st.session_state.sel_m:
        h_padrao = full_db[m_nome].get('horas_padrão', 0)
        adesao_vinculada = str(full_db[m_nome].get('adesão_vinculada', "")).strip()

        # Adiciona Horas de Implantação Específicas do Produto
        if h_padrao > 0:
            v_hora_especifica = h_padrao * valor_hora_base
            total_setup += v_hora_especifica
            html_setup += f"<li><span>Implantação {m_nome}</span><span class='item-detalhe'>{h_padrao}h x R$ {valor_hora_base:,.2f}</span></li>"
        
        # Adiciona Taxa de Adesão Vinculada
        if adesao_vinculada != "" and adesao_vinculada != "nan":
            if adesao_vinculada in full_db:
                v_adesao = full_db[adesao_vinculada]['valor']
                total_setup += v_adesao
                html_setup += f"<li><span>Taxa de Adesão {adesao_vinculada}</span><span class='item-detalhe'>QTD 1 x R$ {v_adesao:,.2f}</span></li>"

    # Card 1: Setup
    with res_cols[0]:
        st.markdown(f'<div class="resumo-card"><span class="resumo-label">Investimento Implantação (Setup)</span><div class="resumo-valor">R$ {total_setup:,.2f}</div><div style="font-weight:bold;">{parcelas_setup}x de R$ {total_setup/parcelas_setup:,.2f}</div><div class="resumo-subtitulo">DETALHAMENTO SETUP</div><ul class="lista-itens">{html_setup if html_setup else "<li>Nenhum item adicionado</li>"}</ul></div>', unsafe_allow_html=True)

    # Card 2: Mensalidade (Com Ordenação VIP)
    with res_cols[1]:
        def get_peso(item):
            if item == "VR ERP PRO": return 1
            if item == "VR PDV Convencional": return 2
            if "SiTef" in item: return 3
            if item == "Gerenciador XML": return 4
            if item == "VR Mobile": return 5
            return 99
        lista_ordenada_m = sorted(st.session_state.sel_m, key=get_peso)
        t_men_bruto = sum(st.session_state[f"perm_val_{i}"] * sistemas_db[i]["valor"] for i in st.session_state.sel_m if i in sistemas_db)
        t_men_liq = t_men_bruto * (1 - (desc/100))
        html_m = ""
        for i in lista_ordenada_m:
            if st.session_state[f"perm_val_{i}"] > 0:
                html_m += f"<li><span>{i}</span><span class='item-detalhe'>{st.session_state[f'perm_val_{i}']} un x R$ {sistemas_db[i]['valor']:,.2f}</span></li>"
                if i == "VR ERP PRO":
                    for ex in ["VR Promo", "VR Carteira Digital", "VR Analytics"]: html_m += f"<li class='item-incluso'><span>└ {ex}</span><span>Incluso</span></li>"
        st.markdown(f'<div class="resumo-card" style="border-top-color: #2e7d32;"><span class="resumo-label">Manutenção Mensal</span><div class="resumo-valor" style="color: #2e7d32;">R$ {t_men_liq:,.2f}</div><div style="font-weight:bold; font-size: 0.9rem;">Início: {faturamento_sistema}</div><div class="resumo-subtitulo">SISTEMAS</div><ul class="lista-itens">{html_m if html_m else "<li>Nenhum sistema selecionado</li>"}</ul></div>', unsafe_allow_html=True)

    # Card 3: Logística
    if perfil_venda == "Executivo (Rua)":
        with res_cols[2]:
            t_desp = sum(st.session_state[f"perm_val_{i}"] * despesas_db[i]["valor"] for i in st.session_state.sel_d if i in despesas_db)
            html_d = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{st.session_state[f'perm_val_{i}']} un x R$ {despesas_db[i]['valor']:,.2f}</span></li>" for i in st.session_state.sel_d if i in despesas_db and st.session_state[f"perm_val_{i}"] > 0])
            st.markdown(f'<div class="resumo-card" style="border-top-color: #1976d2;"><span class="resumo-label">Logística</span><div class="resumo-valor" style="color: #1976d2;">R$ {t_desp:,.2f}</div><div style="color:#d32f2f; font-weight:bold; font-size:0.85rem;">{regra_logistica}</div><div class="resumo-subtitulo">DETALHAMENTO</div><ul class="lista-itens">{html_d if html_d else "<li>Sem despesas</li>"}</ul></div>', unsafe_allow_html=True)

# --- PARTE 4: CONSULTA TÉCNICA ---
elif tela == "Consulta de Preço":
    st.markdown('<h1 class="hero-title">ANÁLISE TÉCNICA</h1>', unsafe_allow_html=True)
    if full_db:
        prod_sel = st.selectbox("Produto:", sorted(list(full_db.keys())))
        if prod_sel:
            d = full_db[prod_sel]
            c1, c2 = st.columns([1, 2])
            with c1: st.markdown(f'<div class="resumo-card" style="min-height:auto;"><span class="resumo-label">Valor</span><div class="resumo-valor">R$ {d["valor"]:,.2f}</div><hr><p><b>Tipo:</b> {d["tipo"]}</p><p><b>H. Padrão:</b> {d.get("horas_padrão",0)}h</p></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="resumo-card" style="min-height:auto;"><span class="resumo-label">Descrição Técnica</span><div style="margin-top:15px;">{d["descricao"] if str(d["descricao"]) != "nan" else "Sem descrição."}</div></div>', unsafe_allow_html=True)
