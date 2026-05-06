import streamlit as st
import pandas as pd
import os

# 1. Configuração da Página
st.set_page_config(page_title="VR Software | Sales Intelligence", layout="wide")

# --- LINK DO GOOGLE SHEETS (VERSÃO CSV) ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTgmdf_FgFd91dkm5zoD0l6l2ailLhCsEV-3pyFsQxRzoyNw2E96eQQoCYkfxHitA9oCIvfaI30-k-2/pub?output=csv"

# --- FUNÇÕES DE APOIO ---
def limpar_valor(valor):
    if pd.isna(valor) or str(valor).strip() == "":
        return 0.0
    try:
        v = str(valor).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        return float(v)
    except:
        return 0.0

def sync_state(key_permanente, key_widget):
    st.session_state[key_permanente] = st.session_state[key_widget]

# --- CARREGAMENTO DE DADOS ---
@st.cache_data(ttl=60)
def carregar_dados_vendas():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Compatibilidade com Pandas 2.1+
        df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
        
        col_tipo = next((c for c in df.columns if c.lower() == 'tipo'), 'Tipo')
        df['Tipo_Busca'] = df[col_tipo].astype(str).str.lower()
        df['Valor'] = df['Valor'].apply(limpar_valor)
        
        sistemas = df[df['Tipo_Busca'].str.startswith('sist')].set_index('Produto').to_dict('index')
        servicos = df[df['Tipo_Busca'].str.startswith('serv')].set_index('Produto').to_dict('index')
        despesas = df[df['Tipo_Busca'].str.startswith('desp')].set_index('Produto').to_dict('index')
        full_db = df.set_index('Produto').to_dict('index')
        
        return sistemas, servicos, despesas, full_db
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return {}, {}, {}, {}

sistemas_db, servicos_db, despesas_db, full_db = carregar_dados_vendas()

# 2. Estilização CSS (Branding VR)
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #ffffff 0%, #fff5ed 100%); }
    .hero-title { color: #262730; font-size: 5.5rem; font-weight: 900; margin: 0; line-height: 1; text-transform: uppercase; letter-spacing: -3px; }
    .sidebar-label { color: #ff6600; font-size: 0.9rem; font-weight: 800; text-transform: uppercase; margin-top: 20px; margin-bottom: 10px; display: block; }
    .resumo-card {
        background-color: #ffffff; border: 1px solid #f0f0f0; border-top: 8px solid #ff6600;
        padding: 25px; border-radius: 8px; min-height: 480px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.1); 
        display: flex; flex-direction: column;
    }
    .resumo-valor { color: #ff6600; font-size: 2.5rem; font-weight: 900; margin-bottom: 5px; }
    .resumo-label { color: #888; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; display: block; }
    .resumo-subtitulo { font-size: 1.1rem; color: #333; font-weight: bold; margin-top: 20px; margin-bottom: 10px; border-bottom: 2px solid #ffefe5; padding-bottom: 5px; }
    .item-detalhe { color: #333; font-size: 1.05rem; font-weight: 700; background-color: #fcfcfc; padding: 2px 8px; border-radius: 4px; }
    .section-header { background: linear-gradient(90deg, #ff6600 0%, #ff944d 100%); padding: 8px 15px; border-radius: 5px; margin-bottom: 15px; margin-top: 20px; }
    .section-title { color: #ffffff; font-size: 1.1rem; font-weight: bold; margin: 0; }
    .lista-itens { list-style-type: none; padding-left: 0; margin-top: 10px; flex-grow: 1; }
    .lista-itens li { padding: 10px 0; border-bottom: 1px dashed #e0e0e0; display: flex; justify-content: space-between; align-items: center; }
    
    .tooltip { position: relative; display: inline-block; cursor: help; border-bottom: 1px dotted #ff6600; color: #222; font-weight: 600; }
    .tooltip .tooltiptext {
        visibility: hidden; width: 250px; background-color: #262730; color: #fff; text-align: left;
        border-radius: 8px; padding: 12px; position: absolute; z-index: 10; bottom: 135%; left: 50%;
        margin-left: -125px; opacity: 0; transition: opacity 0.3s; font-size: 0.85rem; line-height: 1.4; font-weight: 400;
    }
    .tooltip:hover .tooltiptext { visibility: visible; opacity: 1; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. INICIALIZAÇÃO DO ESTADO ---
if 'sel_i' not in st.session_state: st.session_state.sel_i = []
if 'sel_m' not in st.session_state: st.session_state.sel_m = []

for nome in full_db.keys():
    if f"perm_val_{nome}" not in st.session_state:
        st.session_state[f"perm_val_{nome}"] = 120 if "Treinamento" in str(nome) else 1

# --- 4. MENU LATERAL ---
with st.sidebar:
    if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=200)
    tela = st.radio("Navegação:", ["Gerador de Proposta", "Consulta de Preço"])
    st.write("---")

    if tela == "Gerador de Proposta":
        st.markdown('<span class="sidebar-label">Configurações Gerais</span>', unsafe_allow_html=True)
        perfil_venda = st.selectbox("Perfil", ["Executivo (Rua)", "CS (Base)"])
        modo_apresentacao = st.toggle("Modo Apresentação")
        
        st.markdown('<span class="sidebar-label">Faturamento e Bonificação</span>', unsafe_allow_html=True)
        desc = st.number_input("Bonificação Mensal (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.1)
        exibir_detalhe_desc = st.toggle("Exibir Desconto na Tela", value=True)
        faturamento_sistema = st.selectbox("Início da Mensalidade", ["Na assinatura do contrato", "30 dias após assinatura", "60 dias após assinatura", "Após o sistema estar pronto"])
        parcelas_setup = st.selectbox("Parcelamento da Instalação", [1, 2, 3, 4, 5, 6], index=3)
        
        regra_logistica = st.selectbox("Pagamento dos Custos de Viagem", [
            "Junto com a instalação (No início)",
            "Após a conclusão (No final do serviço)"
        ])

# --- 5. TELA DE CONSULTA DE PREÇO ---
if tela == "Consulta de Preço":
    st.markdown('<h1 class="hero-title">ANÁLISE TÉCNICA</h1>', unsafe_allow_html=True)
    if full_db:
        prod_sel = st.selectbox("Selecione o Produto:", list(full_db.keys()))
        d = full_db[prod_sel]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
                <div class="resumo-card">
                    <span class="resumo-label">Valor Unitário</span>
                    <div class="resumo-valor">R$ {d['Valor']:,.2f}</div>
                    <div class="resumo-subtitulo">FICHA DO PRODUTO</div>
                    <p><b>Tipo:</b> {d['Tipo']}</p>
                    <div class="section-header"><span class="section-title">O QUE ESTÁ INCLUSO?</span></div>
                    <p style="color:#555; line-height:1.6;">{d['Descricao']}</p>
                </div>
            """, unsafe_allow_html=True)
        with c2:
            st.info("💡 **Dica:** Utilize a descrição oficial para reforçar o valor da solução.")

# --- 6. TELA GERADOR DE PROPOSTA ---
else:
    if not modo_apresentacao:
        st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)
        st.markdown("---")
        col_i, col_m, col_d = st.columns(3) if perfil_venda == "Executivo (Rua)" else (*st.columns(2), None)
        
        with col_i:
            st.markdown('<div class="section-header"><span class="section-title">INSTALAÇÃO E TREINAMENTO</span></div>', unsafe_allow_html=True)
            opcoes_i = list(servicos_db.keys())
            default_i = [s for s in st.session_state.sel_i if s in opcoes_i]
            st.session_state.sel_i = st.multiselect("Serviços", opcoes_i, default=default_i)
            for i in st.session_state.sel_i:
                st.number_input(f"Horas: {i}", min_value=0, value=st.session_state[f"perm_val_{i}"], key=f"tmp_val_{i}", on_change=sync_state, args=(f"perm_val_{i}", f"tmp_val_{i}"))

        with col_m:
            st.markdown('<div class="section-header"><span class="section-title">SISTEMAS</span></div>', unsafe_allow_html=True)
            opcoes_m = list(sistemas_db.keys())
            default_m = [s for s in st.session_state.sel_m if s in opcoes_m]
            st.session_state.sel_m = st.multiselect("Produtos", opcoes_m, default=default_m)
            for i in st.session_state.sel_m:
                st.number_input(f"Qtd: {i}", min_value=0, value=st.session_state[f"perm_val_{i}"], key=f"tmp_val_{i}", on_change=sync_state, args=(f"perm_val_{i}", f"tmp_val_{i}"))

        if col_d:
            with col_d:
                st.markdown('<div class="section-header"><span class="section-title">LOGÍSTICA</span></div>', unsafe_allow_html=True)
                for i in despesas_db.keys():
                    st.number_input(f"{i}", min_value=0, value=st.session_state[f"perm_val_{i}"], key=f"tmp_val_{i}", on_change=sync_state, args=(f"perm_val_{i}", f"tmp_val_{i}"))

    # --- CÁLCULOS ---
    t_imp, t_men_bruto, t_desp = 0.0, 0.0, 0.0
    lista_i, lista_m, lista_d = [], [], []

    for i in st.session_state.sel_i:
        if i in servicos_db:
            q, v = st.session_state[f"perm_val_{i}"], servicos_db[i]["Valor"]
            t_imp += q * v
            lista_i.append((i, q, v, servicos_db[i].get("Descricao", "")))

    for i in st.session_state.sel_m:
        if i in sistemas_db:
            q, v = st.session_state[f"perm_val_{i}"], sistemas_db[i]["Valor"]
            t_men_bruto += q * v
            lista_m.append((i, q, v, sistemas_db[i].get("Descricao", "")))

    for i in despesas_db.keys():
        q = st.session_state[f"perm_val_{i}"]
        if q > 0:
            v = despesas_db[i]["Valor"]
            t_desp += q * v
            lista_d.append((i, q, v, ""))

    t_men_liq = t_men_bruto * (1 - (desc/100))

    # --- EXIBIÇÃO ---
    st.markdown("<h2 style='text-align:center; font-weight:800; margin-top:30px;'>RESUMO DO INVESTIMENTO</h2>", unsafe_allow_html=True)
    res_cols = st.columns(3) if perfil_venda == "Executivo (Rua)" else st.columns([1, 2, 2, 1])[1:3]

    with res_cols[0]:
        html_i = "".join([f"<li><span><span class='tooltip'>{i}<span class='tooltiptext'>{d}</span></span></span><span class='item-detalhe'>{q}h</span></li>" for i, q, v, d in lista_i])
        st.markdown(f'<div class="resumo-card"><span class="resumo-label">Instalação e Treinamento</span><div class="resumo-valor">R$ {t_imp:,.2f}</div><div style="font-weight:bold;">{parcelas_setup}x de R$ {t_imp/parcelas_setup:,.2f}</div><div class="resumo-subtitulo">SERVIÇOS</div><ul class="lista-itens">{html_i if html_i else "<li>Nenhum selecionado</li>"}</ul></div>', unsafe_allow_html=True)

    with res_cols[1]:
        html_m = "".join([f"<li><span><span class='tooltip'>{i}<span class='tooltiptext'>{d}</span></span></span><span class='item-detalhe'>{q} un</span></li>" for i, q, v, d in lista_m])
        desc_txt = f'<div style="color: #2e7d32; font-weight: bold;">Bonificação: {desc:,.2f}%</div>' if exibir_detalhe_desc and desc > 0 else '<div style="height:21px"></div>'
        st.markdown(f'<div class="resumo-card" style="border-top-color: #2e7d32;"><span class="resumo-label">Manutenção Mensal</span><div class="resumo-valor" style="color: #2e7d32;">R$ {t_men_liq:,.2f}</div>{desc_txt}<div style="font-weight:bold; font-size: 0.9rem; margin-top:5px;">Início: {faturamento_sistema}</div><div class="resumo-subtitulo">SISTEMAS</div><ul class="lista-itens">{html_m if html_m else "<li>Nenhum selecionado</li>"}</ul></div>', unsafe_allow_html=True)

    if perfil_venda == "Executivo (Rua)":
        with res_cols[2]:
            html_d = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{q} un</span></li>" for i, q, v, d in lista_d])
            msg_cliente = "Cobrança no início do projeto" if "início" in regra_logistica else "Boleto emitido após o serviço pronto"
            st.markdown(f'<div class="resumo-card" style="border-top-color: #1976d2;"><span class="resumo-label">Custos de Viagem</span><div class="resumo-valor" style="color: #1976d2;">R$ {t_desp:,.2f}</div><div style="color:#d32f2f; font-weight:bold; font-size:0.85rem;">{msg_cliente}</div><div class="resumo-subtitulo">LOGÍSTICA</div><ul class="lista-itens">{html_d if html_d else "<li>Sem despesas previstas</li>"}</ul></div>', unsafe_allow_html=True)
