import streamlit as st
import os

# 1. CONFIGURAÇÃO DA PÁGINA (Sempre no topo)
st.set_page_config(page_title="VR Software | Proposta Comercial", layout="wide")

# 2. ESTILIZAÇÃO CSS COMPLETA
# Aqui definimos as cores, o alinhamento das listas e o visual dos cards
st.markdown("""
    <style>
    /* Fundo da página com degradê suave */
    .stApp { background: linear-gradient(135deg, #ffffff 0%, #fff5ed 100%); }
    
    /* Título Principal */
    .hero-title {
        color: #262730; font-size: 5.5rem; font-weight: 900; margin: 0; padding: 0;
        line-height: 1; letter-spacing: -3px; text-transform: uppercase;
    }

    /* Estilo dos Cards de Resumo */
    .resumo-card {
        background-color: #ffffff; 
        border: 1px solid #f0f0f0; 
        border-top: 8px solid #ff6600; /* Faixa laranja no topo */
        padding: 25px; 
        border-radius: 10px; 
        min-height: 500px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    }
    
    /* Rótulos superiores (Investimento Setup, etc) */
    .resumo-label { color: #666; font-size: 0.9rem; font-weight: 700; margin-bottom: 8px; display: block; }
    
    /* Valores em destaque (R$) */
    .resumo-valor { color: #ff6600; font-size: 3rem; font-weight: 900; margin-bottom: 5px; line-height: 1; }
    
    /* Títulos das Listas (SERVIÇOS DE IMPLANTAÇÃO, etc) */
    .resumo-subtitulo {
        font-size: 1rem; color: #111; font-weight: 800; margin-top: 25px;
        margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 8px;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    
    /* Configuração da Lista para alinhar Nome à Esquerda e Valor à Direita */
    .lista-itens { list-style-type: none; padding: 0; margin: 0; }
    .lista-itens li { 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        padding: 12px 0; 
        border-bottom: 1px dashed #e0e0e0; 
    }

    .item-nome { color: #333; font-size: 1rem; font-weight: 700; flex: 1; }
    .item-detalhe { color: #000; font-size: 1rem; font-weight: 800; text-align: right; white-space: nowrap; }

    /* Faixa de alerta para despesas (Faturadas ao término...) */
    .alerta-despesa {
        font-size: 0.95rem; color: #d32f2f; font-weight: 700; 
        background: #fff5f5; padding: 8px 12px; border-radius: 4px;
        display: block; width: 100%; margin-top: 10px;
    }

    /* Estilo do Painel Lateral */
    .sidebar-label {
        color: #ff6600; font-size: 0.9rem; font-weight: 800; text-transform: uppercase;
        margin-top: 20px; margin-bottom: 10px; display: block;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. CABEÇALHO COM LOGO E TÍTULO
head_col1, head_col2 = st.columns([1, 4])
with head_col1:
    if os.path.exists("logo_vr.png"): 
        st.image("logo_vr.png", width=220)
    else: 
        st.subheader("VR SOFTWARE")
with head_col2:
    st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)

st.markdown("---")

# 4. BANCO DE DADOS (Preços e Itens)
itens_imp = {
    "Migração Banco de Dados": 201.30, 
    "Definição de Escopo": 201.30, 
    "Configuração Servidor / PDV Linux": 201.30, 
    "Implantação e Treinamento": 201.30
}
itens_mensal = {
    "VR ERP PRO": 1285.71, 
    "VR PDV Convencional": 185.71, 
    "PDV Touchscreen": 185.71, 
    "PDV Selfcheckout": 290.44, 
    "SiTef Express": 357.14, 
    "VR TEF": 417.04, 
    "Gerenciador XML": 163.84, 
    "VR Mobile": 193.63
}
itens_desp = {"Alimentação": 49.00, "Hospedagem": 195.00, "Deslocamento (KM)": 2.12}

# 5. PAINEL LATERAL (Entrada de dados)
with st.sidebar:
    st.title("CONFIGURAÇÃO")
    modo_apresentacao = st.toggle("Modo Apresentação (Esconder edição)", value=False)
    
    st.markdown('<span class="sidebar-label">Negociação</span>', unsafe_allow_html=True)
    desc = st.number_input("Desconto Mensal (%)", min_value=0.0, max_value=50.0, value=0.0)
    parcelas = st.selectbox("Parcelas Setup", [1, 2, 3, 4, 5, 6, 10, 12], index=3)

# Lógica de seleção (Só aparece se o Modo Apresentação estiver desligado)
if not modo_apresentacao:
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.write("**Seleção de Implantação**")
        imp_sel = st.multiselect("Itens", list(itens_imp.keys()), default=list(itens_imp.keys()))
        dados_imp = []
        t_imp = 0
        for i in imp_sel:
            h = st.number_input(f"Horas: {i}", value=12 if "Treinamento" not in i else 120)
            t_imp += h * itens_imp[i]
            dados_imp.append((i, h, itens_imp[i]))
            
    with c2:
        st.write("**Seleção de Mensalidade**")
        men_sel = st.multiselect("Produtos", list(itens_mensal.keys()), default=["VR ERP PRO"])
        dados_men = []
        t_men_bruto = 0
        for i in men_sel:
            q = st.number_input(f"Qtd: {i}", value=1, min_value=1)
            t_men_bruto += q * itens_mensal[i]
            dados_men.append((i, q, itens_mensal[i]))
        t_men_liq = t_men_bruto * (1 - (desc/100))
        
    with c3:
        st.write("**Seleção de Despesas**")
        dados_desp = []
        t_desp = 0
        for item, preco in itens_desp.items():
            qd = st.number_input(f"{item}", value=0)
            if qd > 0:
                t_desp += qd * preco
                dados_desp.append((item, qd, preco))
    
    # Salva na memória para o modo apresentação
    st.session_state.update({'t_imp':t_imp, 'dados_imp':dados_imp, 't_men_liq':t_men_liq, 'dados_men':dados_men, 't_desp':t_desp, 'dados_desp':dados_desp, 'parcelas':parcelas, 'desc':desc})
else:
    # Carrega da memória
    t_imp = st.session_state.get('t_imp', 0)
    dados_imp = st.session_state.get('dados_imp', [])
    t_men_liq = st.session_state.get('t_men_liq', 0)
    dados_men = st.session_state.get('dados_men', [])
    t_desp = st.session_state.get('t_desp', 0)
    dados_desp = st.session_state.get('dados_desp', [])
    parcelas = st.session_state.get('parcelas', 1)
    desc = st.session_state.get('desc', 0)

# 6. SEÇÃO DE RESUMO (O CORAÇÃO DO CÓDIGO - IGUAL À IMAGEM)
st.markdown("<h2 style='text-align: center; color: #333; font-weight: 800; margin: 40px 0;'>DETALHAMENTO DA PROPOSTA</h2>", unsafe_allow_html=True)

res_col1, res_col2, res_col3 = st.columns(3)

# CARD 1: SETUP
with res_col1:
    html_itens = "".join([f"<li><span class='item-nome'>{i}</span><span class='item-detalhe'>{h}h x R$ {v:,.2f}</span></li>" for i, h, v in dados_imp])
    st.markdown(f"""
        <div class="resumo-card">
            <span class="resumo-label">Investimento Setup</span>
            <div class="resumo-valor">R$ {t_imp:,.2f}</div>
            <div style="font-size: 1.2rem; font-weight: 800; color: #333;">{parcelas}x de R$ {t_imp/parcelas:,.2f}</div>
            <div class="resumo-subtitulo">SERVIÇOS DE IMPLANTAÇÃO</div>
            <ul class="lista-itens">{html_itens if html_itens else "<li>Nenhum item selecionado</li>"}</ul>
        </div>
    """, unsafe_allow_html=True)

# CARD 2: MENSAL
with res_col2:
    html_itens = "".join([f"<li><span class='item-nome'>{i}</span><span class='item-detalhe'>{q} Lic. x R$ {v:,.2f}</span></li>" for i, q, v in dados_men])
    st.markdown(f"""
        <div class="resumo-card" style="border-top-color: #2e7d32;">
            <span class="resumo-label">Investimento Mensal</span>
            <div class="resumo-valor" style="color: #2e7d32;">R$ {t_men_liq:,.2f}</div>
            <div style="font-size: 1.1rem; color: #2e7d32; font-weight: 700;">Desconto aplicado: {desc}%</div>
            <div class="resumo-subtitulo">SISTEMAS E LICENÇAS</div>
            <ul class="lista-itens">{html_itens if html_itens else "<li>Nenhum item selecionado</li>"}</ul>
        </div>
    """, unsafe_allow_html=True)

# CARD 3: DESPESAS
with res_col3:
    html_itens = "".join([f"<li><span class='item-nome'>{i}</span><span class='item-detalhe'>{q} un. x R$ {v:,.2f}</span></li>" for i, q, v in dados_desp])
    st.markdown(f"""
        <div class="resumo-card" style="border-top-color: #1976d2;">
            <span class="resumo-label">Previsão de Despesas</span>
            <div class="resumo-valor" style="color: #1976d2;">R$ {t_desp:,.2f}</div>
            <div class="alerta-despesa">Faturadas ao término da implantação</div>
            <div class="resumo-subtitulo">DETALHAMENTO LOGÍSTICO</div>
            <ul class="lista-itens">{html_itens if html_itens else "<li>Nenhuma despesa selecionada</li>"}</ul>
        </div>
    """, unsafe_allow_html=True)
