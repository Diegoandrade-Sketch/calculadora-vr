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
    except: return {}, {}, {}, {}

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
    </style>
    """, unsafe_allow_html=True)

# ESTADO GLOBAL DAS VARIÁVEIS
init_state = {
    'm_combo': "Montar Manualmente",
    'm_pdv_conv': 0, 'm_pdv_touch': 0, 'm_pdv_self': 0, 'm_semanas': 0, 'm_mobile': 0,
    'm_tef': "Não utiliza",
    'm_migracao': False, 'm_ecommerce': False, 'm_app': False, 'm_connect': False,
    'm_erp_pro': False, 'm_xml': False, 'm_escopo': False,
    'm_controller': False, 'm_cartaz': False, 'm_masterfisco': False, 'm_backup': False
}

if 'sel_i' not in st.session_state: st.session_state.sel_i = []
if 'sel_m' not in st.session_state: st.session_state.sel_m = []
if 'sel_d' not in st.session_state: st.session_state.sel_d = []

for k, v in init_state.items():
    if k not in st.session_state:
        st.session_state[k] = v

for nome in full_db.keys():
    if f"perm_val_{nome}" not in st.session_state:
        st.session_state[f"perm_val_{nome}"] = 0

def limpar_tudo():
    for k, v in init_state.items():
        st.session_state[k] = v
    # Resetar o gatilho visual do combo box
    if 'tmp_combo' in st.session_state:
        st.session_state.tmp_combo = "Montar Manualmente"
        
    st.session_state.sel_i = []
    st.session_state.sel_m = []
    st.session_state.sel_d = []
    for nome in full_db.keys():
        st.session_state[f"perm_val_{nome}"] = 0

def sync_combo():
    combo = st.session_state.tmp_combo
    st.session_state.m_combo = combo
    if combo == "Padrão Pequeno Porte":
        st.session_state.m_pdv_conv = 5
        st.session_state.m_tef = "SiTef Express"
        st.session_state.m_semanas = 3
        st.session_state.m_migracao = True
        st.session_state.m_escopo = True
        st.session_state.m_erp_pro = True
        st.session_state.m_xml = True
        st.session_state.m_mobile = 1

# MENU LATERAL (SIDEBAR)
with st.sidebar:
    if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=180)
    tela = st.radio("Navegação:", ["Gerador de Proposta", "Consulta de Preço"])
    st.write("---")

    if tela == "Gerador de Proposta":
        st.markdown('**Configurações de Venda**')
        mapeamento_ativo = st.toggle("Mapeamento Inteligente", value=False)
        modo_apresentacao = st.toggle("Modo Apresentação")
        perfil_venda = st.selectbox("Perfil do Cliente", ["Executivo (Rua)", "CS (Base)"])
        desc = st.number_input("Desconto (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.5)
        exibir_detalhe_desc = st.toggle("Exibir Desconto na Tela", value=True)
        faturamento_sistema = st.selectbox("Início Mensalidade", ["Na assinatura", "30 dias", "60 dias", "Após implantação"])
        parcelas_setup = st.selectbox("Parcelas Setup", [1, 2, 3, 4, 5, 6], index=3)
        regra_logistica = st.selectbox("Faturamento Logística", ["Faturamento na assinatura do contrato", "Faturamento ao término da Implantação"])

# ==========================================
# PARTE 1: MAPEAMENTO DA OPERAÇÃO (O Assistente)
# ==========================================
def aplicar_mapeamento():
    # PDVs
    pdv_map = {"VR PDV Convencional": st.session_state.m_pdv_conv, "PDV Touchscreen": st.session_state.m_pdv_touch, "PDV Selfcheckout": st.session_state.m_pdv_self}
    for p, qtd in pdv_map.items():
        if p in sistemas_db:
            st.session_state[f"perm_val_{p}"] = qtd
            if qtd > 0 and p not in st.session_state.sel_m: st.session_state.sel_m.append(p)
            elif qtd == 0 and p in st.session_state.sel_m: st.session_state.sel_m.remove(p)
    
    # TEF
    total_pdvs = sum(pdv_map.values())
    st.session_state.sel_m = [item for item in st.session_state.sel_m if "SiTef" not in item]
    if st.session_state.m_tef == "SiTef Express":
        tef_opcoes = ["SiTef Express até 3 PDVs", "SiTef Express até 6 PDVs", "SiTef Express até 8 PDVs", "SiTef Express acima de 8 PDVs"]
        escolhido = tef_opcoes[0] if total_pdvs <= 3 else tef_opcoes[1] if total_pdvs <= 6 else tef_opcoes[2] if total_pdvs <= 8 else tef_opcoes[3]
        if escolhido in sistemas_db:
            st.session_state[f"perm_val_{escolhido}"] = 1
            st.session_state.sel_m.append(escolhido)

    # Sistemas Extras (Toggles)
    exp_map = {
        "E-Commerce": st.session_state.m_ecommerce, 
        "M-Commerce": st.session_state.m_app, 
        "VR Connect (Android/IOS)": st.session_state.m_connect,
        "VR ERP PRO": st.session_state.m_erp_pro,
        "Gerenciador XML": st.session_state.m_xml,
        "VR Controller 360": st.session_state.m_controller,
        "VR Cartaz": st.session_state.m_cartaz,
        "VR MasterFisco Brasil": st.session_state.m_masterfisco,
        "VR Backup": st.session_state.m_backup
    }
    for item, ativo in exp_map.items():
        if item in sistemas_db:
            st.session_state[f"perm_val_{item}"] = 1 if ativo else 0
            if ativo and item not in st.session_state.sel_m: st.session_state.sel_m.append(item)
            elif not ativo and item in st.session_state.sel_m: st.session_state.sel_m.remove(item)

    # VR Mobile (Lógica de Adição)
    m_mobile_item = "VR Mobile"
    if m_mobile_item in sistemas_db and st.session_state.m_mobile > 0:
        if m_mobile_item not in st.session_state.sel_m:
            st.session_state.sel_m.append(m_mobile_item)
        # Acumula o valor e zera no assistente para evitar duplicação ao clicar novamente
        st.session_state[f"perm_val_{m_mobile_item}"] += st.session_state.m_mobile
        st.session_state.m_mobile = 0
        if 'tmp_mobile' in st.session_state:
            st.session_state.tmp_mobile = 0

    # Serviços 
    sem = st.session_state.m_semanas
    serv_map = {
        "Implantação e Treinamento": sem * 44,
        "Migração Banco de Dados": 8 if st.session_state.m_migracao else 0,
        "Definição de Escopo": 8 if st.session_state.m_escopo else 0
    }
    for s_item, s_horas in serv_map.items():
        if s_item in servicos_db:
            st.session_state[f"perm_val_{s_item}"] = s_horas
            if s_horas > 0 and s_item not in st.session_state.sel_i: st.session_state.sel_i.append(s_item)
            elif s_horas == 0 and s_item in st.session_state.sel_i: st.session_state.sel_i.remove(s_item)

    # Despesas 
    ali, hos = "Alimentacao", "Hospedagem"
    if ali in despesas_db: 
        st.session_state[f"perm_val_{ali}"] = sem * 10
        if sem > 0 and ali not in st.session_state.sel_d: st.session_state.sel_d.append(ali)
        elif sem == 0 and ali in st.session_state.sel_d: st.session_state.sel_d.remove(ali)
    if hos in despesas_db: 
        st.session_state[f"perm_val_{hos}"] = sem * 4
        if sem > 0 and hos not in st.session_state.sel_d: st.session_state.sel_d.append(hos)
        elif sem == 0 and hos in st.session_state.sel_d: st.session_state.sel_d.remove(hos)

if tela == "Gerador de Proposta":
    if not modo_apresentacao:
        st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)
        
        # VISUAL DO MAPEAMENTO
        if mapeamento_ativo:
            # Correção visual: A caixa fecha logo após o título
            st.markdown('<div class="mapeamento-container"><h3 style="margin:0; color:#ff6600;">🛒 Mapeamento da Operação</h3></div>', unsafe_allow_html=True)
            
            st.selectbox(
                "Carregar Combo Rápido", ["Montar Manualmente", "Padrão Pequeno Porte"], 
                key="tmp_combo", index=["Montar Manualmente", "Padrão Pequeno Porte"].index(st.session_state.m_combo), 
                on_change=sync_combo
            )
            st.markdown("<br>", unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("**PDVs e Ponto de Venda**")
                st.number_input("PDV Convencional", min_value=0, key="tmp_pdv_conv", value=st.session_state.m_pdv_conv, on_change=sync_state, args=("m_pdv_conv", "tmp_pdv_conv"))
                st.number_input("PDV Touchscreen", min_value=0, key="tmp_pdv_touch", value=st.session_state.m_pdv_touch, on_change=sync_state, args=("m_pdv_touch", "tmp_pdv_touch"))
                st.number_input("PDV Selfcheckout", min_value=0, key="tmp_pdv_self", value=st.session_state.m_pdv_self, on_change=sync_state, args=("m_pdv_self", "tmp_pdv_self"))
            with c2:
                st.markdown("**Serviços e Regras**")
                st.selectbox("Solução de TEF", ["Não utiliza", "SiTef Express", "VR TEF"], key="tmp_tef", index=["Não utiliza", "SiTef Express", "VR TEF"].index(st.session_state.m_tef), on_change=sync_state, args=("m_tef", "tmp_tef"))
                st.number_input("Semanas de Implantação", min_value=0, key="tmp_semanas", value=st.session_state.m_semanas, on_change=sync_state, args=("m_semanas", "tmp_semanas"))
                st.checkbox("Migração de Banco?", key="tmp_migracao", value=st.session_state.m_migracao, on_change=sync_state, args=("m_migracao", "tmp_migracao"))
                st.checkbox("Definição de Escopo?", key="tmp_escopo", value=st.session_state.m_escopo, on_change=sync_state, args=("m_escopo", "tmp_escopo"))
            with c3:
                st.markdown("**Sistemas Extras**")
                st.number_input("Licenças VR Mobile", min_value=0, key="tmp_mobile", value=st.session_state.m_mobile, on_change=sync_state, args=("m_mobile", "tmp_mobile"))
                
                # Divisão em subcolunas para ficar compacto
                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    st.toggle("VR ERP PRO", key="tmp_erp_pro", value=st.session_state.m_erp_pro, on_change=sync_state, args=("m_erp_pro", "tmp_erp_pro"))
                    st.toggle("G. XML", key="tmp_xml", value=st.session_state.m_xml, on_change=sync_state, args=("m_xml", "tmp_xml"))
                    st.toggle("VR Connect", key="tmp_connect", value=st.session_state.m_connect, on_change=sync_state, args=("m_connect", "tmp_connect"))
                with sc2:
                    st.toggle("VR Backup", key="tmp_backup", value=st.session_state.m_backup, on_change=sync_state, args=("m_backup", "tmp_backup"))
                    st.toggle("VR Cartaz", key="tmp_cartaz", value=st.session_state.m_cartaz, on_change=sync_state, args=("m_cartaz", "tmp_cartaz"))
                    st.toggle("E-Commerce", key="tmp_ecommerce", value=st.session_state.m_ecommerce, on_change=sync_state, args=("m_ecommerce", "tmp_ecommerce"))
                with sc3:
                    st.toggle("C. 360", key="tmp_controller", value=st.session_state.m_controller, on_change=sync_state, args=("m_controller", "tmp_controller"))
                    st.toggle("MasterFisco", key="tmp_masterfisco", value=st.session_state.m_masterfisco, on_change=sync_state, args=("m_masterfisco", "tmp_masterfisco"))
                    st.toggle("M-Commerce", key="tmp_app", value=st.session_state.m_app, on_change=sync_state, args=("m_app", "tmp_app"))
                
                b_col1, b_col2 = st.columns(2)
                with b_col1: st.button("✨ Aplicar Inteligência", on_click=aplicar_mapeamento, use_container_width=True)
                with b_col2: st.button("🗑️ Limpar Tudo", on_click=limpar_tudo, use_container_width=True)
            st.markdown("---")

        # ==========================================
        # PARTE 2: TELA DE VENDA (A Inclusão Manual)
        # ==========================================
        col_i, col_m, col_d = st.columns(3) if perfil_venda == "Executivo (Rua)" else (*st.columns(2), None)
        
        with col_i:
            st.markdown('<div class="section-header"><span class="section-title">IMPLANTAÇÃO E SERVIÇOS</span></div>', unsafe_allow_html=True)
            st.session_state.sel_i = st.multiselect("Serviços", list(servicos_db.keys()), default=[s for s in st.session_state.sel_i if s in servicos_db])
            for i in st.session_state.sel_i:
                st.number_input(
                    f"{i} (R$ {servicos_db[i]['Valor']:,.2f}/h)", min_value=0, 
                    value=st.session_state[f"perm_val_{i}"], key=f"tmp_i_{i}", on_change=sync_state, args=(f"perm_val_{i}", f"tmp_i_{i}")
                )
        
        with col_m:
            st.markdown('<div class="section-header"><span class="section-title">MENSALIDADES SISTEMAS</span></div>', unsafe_allow_html=True)
            st.session_state.sel_m = st.multiselect("Sistemas", list(sistemas_db.keys()), default=[s for s in st.session_state.sel_m if s in sistemas_db])
            for i in st.session_state.sel_m:
                st.number_input(
                    f"{i} (R$ {sistemas_db[i]['Valor']:,.2f}/un)", min_value=0, 
                    value=st.session_state[f"perm_val_{i}"], key=f"tmp_m_{i}", on_change=sync_state, args=(f"perm_val_{i}", f"tmp_m_{i}")
                )
        
        if col_d:
            with col_d:
                st.markdown('<div class="section-header"><span class="section-title">DESPESAS LOGÍSTICAS</span></div>', unsafe_allow_html=True)
                st.session_state.sel_d = st.multiselect("Despesas", list(despesas_db.keys()), default=[s for s in st.session_state.sel_d if s in despesas_db])
                for i in st.session_state.sel_d:
                    st.number_input(
                        f"{i} (R$ {despesas_db[i]['Valor']:,.2f}/un)", min_value=0, 
                        value=st.session_state[f"perm_val_{i}"], key=f"tmp_d_{i}", on_change=sync_state, args=(f"perm_val_{i}", f"tmp_d_{i}")
                    )

    # ==========================================
    # PARTE 3: CARDS DE RESUMO (O Resultado)
    # ==========================================
    t_imp = sum(st.session_state[f"perm_val_{i}"] * servicos_db[i]["Valor"] for i in st.session_state.sel_i if i in servicos_db)
    t_men_bruto = sum(st.session_state[f"perm_val_{i}"] * sistemas_db[i]["Valor"] for i in st.session_state.sel_m if i in sistemas_db)
    t_desp = sum(st.session_state[f"perm_val_{i}"] * despesas_db[i]["Valor"] for i in st.session_state.sel_d if i in despesas_db)
    t_men_liq = t_men_bruto * (1 - (desc/100))

    st.markdown("<h2 style='text-align:center; font-weight:800; margin-top:30px;'>RESUMO DO INVESTIMENTO</h2>", unsafe_allow_html=True)
    res_cols = st.columns(3) if perfil_venda == "Executivo (Rua)" else st.columns([1, 2, 2, 1])[1:3]

    with res_cols[0]:
        html_i = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{st.session_state[f'perm_val_{i}']}h x R$ {servicos_db[i]['Valor']:,.2f}</span></li>" for i in st.session_state.sel_i if i in servicos_db and st.session_state[f"perm_val_{i}"] > 0])
        st.markdown(f'<div class="resumo-card"><span class="resumo-label">Investimento Implantação</span><div class="resumo-valor">R$ {t_imp:,.2f}</div><div style="font-weight:bold;">{parcelas_setup}x de R$ {t_imp/parcelas_setup:,.2f}</div><div class="resumo-subtitulo">DETALHAMENTO SETUP</div><ul class="lista-itens">{html_i if html_i else "<li>Nenhum item com valor adicionado</li>"}</ul></div>', unsafe_allow_html=True)

    with res_cols[1]:
        html_m = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{st.session_state[f'perm_val_{i}']} un x R$ {sistemas_db[i]['Valor']:,.2f}</span></li>" for i in st.session_state.sel_m if i in sistemas_db and st.session_state[f"perm_val_{i}"] > 0])
        desc_txt = f'<div style="color: #2e7d32; font-weight: bold;">Desconto: {desc:,.2f}%</div>' if exibir_detalhe_desc and desc > 0 else '<div style="height:21px"></div>'
        st.markdown(f'<div class="resumo-card" style="border-top-color: #2e7d32;"><span class="resumo-label">Manutenção Mensal</span><div class="resumo-valor" style="color: #2e7d32;">R$ {t_men_liq:,.2f}</div>{desc_txt}<div style="font-weight:bold; font-size: 0.9rem; margin-top:5px;">Início: {faturamento_sistema}</div><div class="resumo-subtitulo">SISTEMAS</div><ul class="lista-itens">{html_m if html_m else "<li>Nenhum item com valor adicionado</li>"}</ul></div>', unsafe_allow_html=True)

    if perfil_venda == "Executivo (Rua)":
        with res_cols[2]:
            html_d = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{st.session_state[f'perm_val_{i}']} un x R$ {despesas_db[i]['Valor']:,.2f}</span></li>" for i in st.session_state.sel_d if i in despesas_db and st.session_state[f"perm_val_{i}"] > 0])
            st.markdown(f'<div class="resumo-card" style="border-top-color: #1976d2;"><span class="resumo-label">Despesas de Viagem e Logística</span><div class="resumo-valor" style="color: #1976d2;">R$ {t_desp:,.2f}</div><div style="color:#d32f2f; font-weight:bold; font-size:0.85rem;">{regra_logistica}</div><div class="resumo-subtitulo">DETALHAMENTO DE LOGÍSTICA</div><ul class="lista-itens">{html_d if html_d else "<li>Sem despesas previstas</li>"}</ul></div>', unsafe_allow_html=True)

# TELA 2 DE NAVEGAÇÃO
elif tela == "Consulta de Preço":
    st.markdown('<h1 class="hero-title">ANÁLISE TÉCNICA</h1>', unsafe_allow_html=True)
    if full_db:
        prod_sel = st.selectbox("Selecione o Produto:", list(full_db.keys()))
        d = full_db[prod_sel]
        st.markdown(f'<div class="resumo-card" style="min-height:auto;"><span class="resumo-label">Valor</span><div class="resumo-valor">R$ {d["Valor"]:,.2f}</div><p><b>Tipo:</b> {d["Tipo"]}</p><hr><p>{d["Descricao"]}</p></div>', unsafe_allow_html=True)
