import streamlit as st

# Configuração da Página para um ambiente corporativo
st.set_page_config(page_title="VR Software | Propostas Comerciais", layout="wide")

# Estilização Personalizada (CSS) - Foco em Clean Design
st.markdown("""
    <style>
    /* Estilização Geral */
    .main { background-color: #ffffff; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    /* Cores das métricas */
    div[data-testid="stMetricValue"] { color: #ff6600; font-weight: 700; }
    
    /* Barra Lateral Sóbria */
    [data-testid="stSidebar"] { 
        background-color: #f8f9fa; 
        border-right: 1px solid #dee2e6; 
    }
    
    /* Botões Profissionais */
    .stButton>button { 
        background-color: #ff6600; 
        color: white; 
        border-radius: 4px; 
        font-weight: 600;
        border: none;
        height: 3em;
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #cc5200; color: white; }
    
    /* Cartões de métricas refinados */
    .stMetric { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 4px; 
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border-left: 5px solid #ff6600;
    }

    /* Ajuste de títulos */
    h1, h2, h3 { color: #333333; }
    </style>
    """, unsafe_allow_html=True)

# Cabeçalho Institucional
st.image("https://vrsoft.com.br/wp-content/uploads/2022/07/Logo-VR-Software.png", width=200)
st.title("Simulador de Propostas Comerciais")
st.markdown("---")

# --- Sidebar (Parâmetros Técnicos) ---
st.sidebar.subheader("Parâmetros da Operação")
tipo_venda = st.sidebar.selectbox("Modelo de Negócio", ["Novo Cliente (VR ERP PRO)", "Loja Adicional (Expansão)"])
qtd_cnpj = st.sidebar.number_input("Quantidade de Unidades (CNPJ)", min_value=1, value=1)
qtd_pdv = st.sidebar.number_input("Quantidade de Pontos de Venda (PDV)", min_value=1, value=1)
tipo_pdv = st.sidebar.selectbox("Tecnologia de PDV", ["Comum", "Touchscreen", "Self-Checkout"])

st.sidebar.markdown("---")
st.sidebar.subheader("Módulos Adicionais")
bonificar_xml = st.sidebar.checkbox("Bonificar Gerenciador XML")
bonificar_mobile = st.sidebar.checkbox("Bonificar VR Mobile")

st.sidebar.markdown("---")
st.sidebar.subheader("Política de Descontos")
desconto = st.sidebar.slider("Percentual Aplicado", 0, 30, 0)

# Mensagens de validação sérias
if desconto > 15:
    st.sidebar.error("Atenção: Percentual acima da alçada comercial. Requer aprovação da gerência financeira.")
elif desconto > 0:
    st.sidebar.warning(f"Desconto de {desconto}% aplicado conforme negociação.")

# --- Lógica de Preços (Conforme Tabela 2026) ---
PRECO_BASE_PRO = 1090.91 
PRECO_PDV = {"Comum": 165.00, "Touchscreen": 168.83, "Self-Checkout": 201.30}

# Tabela progressiva de TEF (Sintef Express)
if qtd_pdv <= 3: preco_tef = 425.00
elif qtd_pdv <= 5: preco_tef = 510.00
elif qtd_pdv <= 8: preco_tef = 627.00
else: preco_tef = 803.00

# --- Processamento de Valores ---
valor_mensalidade_base = qtd_cnpj * PRECO_BASE_PRO
valor_total_pdvs = qtd_pdv * PRECO_PDV[tipo_pdv]

subtotal = valor_mensalidade_base + valor_total_pdvs + preco_tef
valor_final = subtotal * (1 - (desconto/100))

# --- Dashboard de Resultados ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Software (Mensalidade)", f"R$ {valor_mensalidade_base:,.2f}")
    if bonificar_xml: st.caption("Incluso: Gerenciador XML (Bonificado)")
with col2:
    st.metric("Licenciamento PDV", f"R$ {valor_total_pdvs:,.2f}")
    st.caption(f"Configuração: {qtd_pdv} unidade(s) {tipo_pdv}")
with col3:
    st.metric("TEF Express", f"R$ {preco_tef:,.2f}")
    if bonificar_mobile: st.caption("Incluso: VR Mobile (Bonificado)")

st.markdown("---")

# Quadro de Resumo Final
st.markdown(f"""
    <div style="background-color: #ff6600; padding: 25px; border-radius: 4px; text-align: center;">
        <p style="color: white; margin: 0; font-size: 1.1em; font-weight: 300;">Investimento Total Estimado</p>
        <h1 style="color: white; margin: 0; font-size: 2.5em;">R$ {valor_final:,.2f} / mês</h1>
    </div>
""", unsafe_allow_html=True)

# --- Formalização ---
st.write("")
if st.button("Gerar Sumário Executivo para Compartilhamento"):
    alçada = "Pendente de Aprovação Financeira" if desconto > 15 else "Dentro da Alçada Comercial"
    resumo = f"""
PROPOSTA COMERCIAL - VR SOFTWARE 2026
Status: {alçada}

Detalhamento da Operação:
- Modelo: {tipo_venda}
- Unidades (CNPJ): {qtd_cnpj}
- Pontos de Venda: {qtd_pdv} ({tipo_pdv})
- Módulos Adicionais: {"Gerenciador XML " if bonificar_xml else ""}{"VR Mobile" if bonificar_mobile else "Padrão"}

Condições Comerciais:
- Desconto Aplicado: {desconto}%
- Investimento Mensal: R$ {valor_final:,.2f}
    """
    st.code(resumo, language="text")
