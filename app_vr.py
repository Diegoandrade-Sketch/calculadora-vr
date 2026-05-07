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
        
        # Padronização de colunas
        df.columns = [str(c).strip().lower() for c in df.columns]
        df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
        
        # Garantir existência das novas colunas de inteligência
        if 'horas_padrao' not in df.columns: df['horas_padrao'] = 0
        if 'adesao_vinculada' not in df.columns: df['adesao_vinculada'] = ""
        if 'valor_hora_implantacao' not in df.columns: df['valor_hora_implantacao'] = 0

        df['valor'] = df['valor'].apply(limpar_valor)
        df['valor_hora_implantacao'] = df['valor_hora_implantacao'].apply(limpar_valor)

        full = df.set_index('produto').to_dict('index')
        sist = {k: v for k, v in full.items() if 'sist' in str(v['tipo']).lower()}
        serv = {k: v for k, v in full.items() if 'serv' in str(v['tipo']).lower()}
        desp = {k: v for k, v in full.items() if 'desp' in str(v['tipo']).lower()}
        
        return sist, serv, desp, full
    except Exception as e:
        st.error(f"Erro ao carregar colunas do Excel: {e}")
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
    if tela == "Gerador de Proposta":
        mapeamento_ativo = st.toggle("Mapeamento Inteligente", value=False)
        modo_apresentacao = st.toggle("Modo Apresentação")
        perfil_venda = st.selectbox("Perfil do Cliente", ["Executivo (Rua)", "CS (Base)"])
        desc = st.number_input("Desconto (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.5)
        faturamento_sistema = st.selectbox("Início Mensalidade", ["Na assinatura", "30 dias", "60 dias", "Após implantação"])
        parcelas_setup = st.selectbox("Parcelas Setup", [1, 2, 3, 4, 5, 6], index=3)
        regra_logistica = st.selectbox("Faturamento Logística", ["Faturamento na assinatura", "Faturamento pós Implantação"])

# ==========================================
# GERADOR DE PROPOSTA (PARTES 1, 2, 3)
# ==========================================
if tela == "Gerador de Proposta":
    
    def aplicar_mapeamento():
        pdv_map = {"VR PDV Convencional": st.session_state.m_pdv_conv, "PDV Touchscreen": st.session_state.m_pdv_touch, "PDV Selfcheckout": st.session_state.m_pdv_self}
        for p, qtd in pdv_map.items():
            if p in sistemas_db:
                st.session_state[f"perm_val_{p}"] = qtd
                st.session_state[f"tmp_m_{p}"] = qtd
                if qtd > 0 and p not in st.session_state.sel_m: st.session_state.sel_m.append(p)
        
        total_pdvs = sum(pdv_map.values())
        st.session_state.sel_m = [item for item in st.session_state.sel_m if "SiTef" not in item]
        if st.session_state.m_tef == "SiTef Express":
            escolhido = "SiTef Express até 3 PDVs" if total_pdvs <= 3 else "SiTef Express até 6 PDVs" if total_pdvs <= 6 else "SiTef Express até 8 PDVs" if total_pdvs <= 8 else "SiTef Express acima de 8 PDVs"
            if escolhido in sistemas_db:
                st.session_state[f"perm_val_{escolhido}"] = 1
                st.session_state[f"tmp_m_{escolhido}"] = 1
                st.session_state.sel_m.append(escolhido)

        exp_map = {"E-Commerce": st.session_state.m_ecommerce, "M-Commerce": st.session_state.m_app, "VR Connect (Android/IOS)": st.session_state.m_connect, "VR ERP PRO": st.session_state.m_erp_pro, "Gerenciador XML": st.session_state.m_xml, "VR Controller 360": st.session_state.m_controller, "VR Cartaz": st.session_state.m_cartaz, "VR MasterFisco Brasil": st.session_state.m_masterfisco, "VR Backup": st.session_state.m_backup}
        for item, ativo in exp_map.items():
            if item in sistemas_db:
                st.session_state[f"perm_val_{item}"] = 1 if ativo else 0
                st.session_state[f"tmp_m_{item}"] = 1 if ativo else 0
                if ativo and item not in st.session_state.sel_m: st.session_state.sel_m.append(item)

        if "VR Mobile" in sistemas_db and st.session_state.m_mobile > 0:
            if "VR Mobile" not in st.session_state.sel_m: st.session_state.sel_m.append("VR Mobile")
            st.session_state[f"perm_val_VR Mobile"] += st.session_state.m_mobile
            st.session_state[f"tmp_m_VR Mobile"] = st.session_state[f"perm_val_VR Mobile"]
            st.session_state.m_mobile = 0
            if 'tmp_mobile' in st.session_state: st.session_state.tmp_mobile = 0

        sem = st.session_state.m_semanas
        serv_map = {"Implantação e Treinamento": sem * 44, "Migração Banco de Dados": 8 if st.session_state.m_migracao else 0, "Definição de Escopo": 8 if st.session_state.m_escopo else 0}
        for s_item, s_horas in serv_map.items():
            if s_item in servicos_db:
                st.session_state[f"perm_val_{s_item}"] = s_horas
                st.session_state[f"tmp_i_{s_item}"] = s_horas
                if s_horas > 0 and s_item not in st.session_state.sel_i: st.session_state.sel_i.append(s_item)

    if not modo_apresentacao:
        st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)
        if mapeamento_ativo:
            st.markdown('<div class="mapeamento-container"><h3 style="margin:0; color:#ff6600;">🛒 Mapeamento da Operação</h3></div>', unsafe_allow_html=True)
            st.selectbox("Combo Rápido", ["Montar Manualmente", "Padrão Pequeno Porte"], key="tmp_combo", on_change=sync_combo)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.number_input("PDV Convencional", min_value=0, key="tmp_pdv_conv", value=st.session_state.m_pdv_conv, on_change=sync_state, args=("m_pdv_conv", "tmp_pdv_conv"))
                st.number_input("PDV Touch", min_value=0, key="tmp_pdv_touch", value=st.session_state.m_pdv_touch, on_change=sync_state, args=("m_pdv_touch", "tmp_pdv_touch"))
            with c2:
                st.selectbox("TEF", ["Não utiliza", "SiTef Express", "VR TEF"], key="tmp_tef", index=["Não utiliza", "SiTef Express", "VR TEF"].index(st.session_state.m_tef), on_change=sync_state, args=("m_tef", "tmp_tef"))
                st.number_input("Semanas", min_value=0, key="tmp_semanas", value=st.session_state.m_semanas, on_change=sync_state, args=("m_semanas", "tmp_semanas"))
            with c3:
                st.number_input("VR Mobile", min_value=0, key="tmp_mobile", value=st.session_state.m_mobile, on_change=sync_state, args=("m_mobile", "tmp_mobile"))
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

    # --- PARTE 3: CARD DE RESUMO (TRANSPARÊNCIA E VENDA CASADA) ---
    st.markdown("<h2 style='text-align:center; font-weight:800; margin-top:30px;'>RESUMO DO INVESTIMENTO</h2>", unsafe_allow_html=True)
    res_cols = st.columns(3) if perfil_venda == "Executivo (Rua)" else st.columns([1, 2, 2, 1])[1:3]

    total_setup, html_setup = 0.0, ""
    # Valor da hora técnica padrão
    v_hora_base = servicos_db.get("Implantação e Treinamento", {}).get("valor", 0.0)

    # 1. Serviços Manuais
    for s_nome in st.session_state.sel_i:
        horas = st.session_state[f"perm_val_{s_nome}"]
        if horas > 0:
            v_item = horas * servicos_db[s_nome]['valor']
            total_setup += v_item
            html_setup += f"<li><span>{s_nome}</span><span class='item-detalhe'>{horas}h x R$ {servicos_db[s_nome]['valor']:,.2f}</span></li>"

    # 2. Inteligência de Venda Casada (Horas Específicas e Adesão)
    for m_nome in st.session_state.sel_m:
        dados = full_db.get(m_nome, {})
        h_padrao = dados.get('horas_padrao', 0)
        v_hora_especifico = dados.get('valor_hora_implantacao', 0)
        adesao_vinculada = str(dados.get('adesao_vinculada', "")).strip()

        # Calcula Horas do Produto
        if h_padrao > 0:
            rate = v_hora_especifico if v_hora_especifico > 0 else v_hora_base
            total_setup += (h_padrao * rate)
            html_setup += f"<li><span>Implantação {m_nome}</span><span class='item-detalhe'>{h_padrao}h x R$ {rate:,.2f}</span></li>"
        
        # Calcula Adesão
        if adesao_vinculada != "" and adesao_vinculada != "nan":
            if adesao_vinculada in full_db:
                v_adesao = full_db[adesao_vinculada]['valor']
                total_setup += v_adesao
                html_setup += f"<li><span>Taxa de Adesão {adesao_vinculada}</span><span class='item-detalhe'>QTD 1 x R$ {v_adesao:,.2f}</span></li>"

    with res_cols[0]:
        st.markdown(f'<div class="resumo-card"><span class="resumo-label">Investimento Implantação (Setup)</span><div class="resumo-valor">R$ {total_setup:,.2f}</div><div style="font-weight:bold;">{parcelas_setup}x de R$ {total_setup/parcelas_setup:,.2f}</div><div class="resumo-subtitulo">DETALHAMENTO SETUP</div><ul class="lista-itens">{html_setup if html_setup else "<li>Nenhum item</li>"}</ul></div>', unsafe_allow_html=True)

    with res_cols[1]:
        def get_peso(item):
            if item == "VR ERP PRO": return 1
            if item == "VR PDV Convencional": return 2
            if "SiTef" in item: return 3
            return 99
        lista_ordenada_m = sorted(st.session_state.sel_m, key=get_peso)
        t_men_bruto = sum(st.session_state[f"perm_val_{i}"] * sistemas_db[i]["valor"] for i in st.session_state.sel_m if i in sistemas_db)
        t_men_liq = t_men_bruto * (1 - (desc/100))
        html_m = ""
        for i in lista_ordenada_m:
            html_m += f"<li><span>{i}</span><span class='item-detalhe'>{st.session_state[f'perm_val_{i}']} un x R$ {sistemas_db[i]['valor']:,.2f}</span></li>"
            if i == "VR ERP PRO":
                for ex in ["VR Promo", "VR Carteira Digital", "VR Analytics"]: html_m += f"<li class='item-incluso'><span>└ {ex}</span><span>Incluso</span></li>"
        st.markdown(f'<div class="resumo-card" style="border-top-color: #2e7d32;"><span class="resumo-label">Mensalidade</span><div class="resumo-valor" style="color: #2e7d32;">R$ {t_men_liq:,.2f}</div><div class="resumo-subtitulo">SISTEMAS</div><ul class="lista-itens">{html_m if html_m else "<li>Nenhum</li>"}</ul></div>', unsafe_allow_html=True)

# --- PARTE 4: CONSULTA PREÇO ---
elif tela == "Consulta de Preço":
    st.markdown('<h1 class="hero-title">ANÁLISE TÉCNICA</h1>', unsafe_allow_html=True)
    if full_db:
        p_sel = st.selectbox("Produto:", sorted(list(full_db.keys())))
        if p_sel:
            d = full_db[p_sel]
            st.markdown(f'<div class="resumo-card" style="min-height:auto;"><div class="resumo-valor">R$ {d["valor"]:,.2f}</div><p><b>H. Padrão:</b> {d.get("horas_padrao",0)}h | <b>Hora Esp.:</b> R$ {d.get("valor_hora_implantacao",0):,.2f}</p><hr><p>{d["descricao"]}</p></div>', unsafe_allow_html=True)
