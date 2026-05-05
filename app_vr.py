import streamlit as st

# Configuração da Página com a identidade visual correta
st.set_page_config(page_title="VR Software | Propostas 2026", layout="wide")

# Estilização Personalizada (CSS) - Foco em Laranja e Branco
st.markdown("""
    <style>
    /* Fundo e áreas principais */
    .main { background-color: #ffffff; }
    div[data-testid="stMetricValue"] { color: #ff6600; } /* Laranja VR nos valores */
    
    /* Customização da Barra Lateral */
    [data-testid="stSidebar"] { background-color: #f0f2f6; border-right: 2px solid #ff6600; }
    
    /* Botões em Laranja */
    .stButton>button { 
        background-color: #ff6600; 
        color: white; 
        border-radius: 8px; 
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover { background-color: #e65c00; border: none; color: white; }
    
    /* Cartões de métricas */
    .stMetric { 
        background-color: #ffffff; 
        padding: 15px; 
        border-radius: 10px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-top: 4px solid #ff6600;
    }
    </style>
    """, unsafe_allow_html=True)

# Cabeçalho com Logo (Ajustado para o fundo branco)
# Usei a logo que aparece no topo do site oficial
st.image("https://vrsoft.com.br/wp-content/uploads/2022/07/Logo-VR-Software.png", width=220)
st.title("🚀 Gerador de Orçamentos Comercial")
st.markdown("---")

# --- Sidebar (Configurações) ---
st.sidebar.header("📋 Dados da Negociação")
tipo_venda = st.sidebar.selectbox("Tipo de Venda", ["Novo Cliente (VR ERP PRO)", "Loja Adicional (Expansão)"])
qtd_cnpj = st.sidebar.number_input("Quantidade de CNPJs", min_value=1, value=1)
qtd_pdv = st.sidebar.number_input("Quantidade de PDVs", min_value=1, value=1)
tipo_pdv = st.sidebar.selectbox("Modelo do PDV", ["Comum", "Touchscreen", "Self-Checkout"])

st.sidebar.markdown("---")
st.sidebar.header("🎁 Módulos & Bonificações")
bonificar_xml = st.sidebar.checkbox("Bonificar VR Gerenciador XML")
bonificar_mobile = st.sidebar.checkbox("Bonificar VR Mobile")

st.sidebar.markdown("---")
st.sidebar.header("📉 Negociação")
desconto = st.sidebar.slider("Percentual de Desconto", 0, 30, 0)

# Alerta de desconto com a lógica que você pediu
if desconto > 15:
    st.sidebar.error("⚠️ Desconto acima de 15%: Requer aprovação do Financeiro.")
elif desconto > 0:
    st.sidebar.warning(f"Desconto de {desconto}% aplicado.")
else:
    st.sidebar.info("Desconto máximo permitido: 15%")

# --- Lógica de Preços (Conforme seu arquivo Excel) ---
PRECO_BASE_PRO = 1090.91 
PRECO_PDV = {"Comum": 165.00, "Touchscreen": 168.83, "Self-Checkout": 201.30}

# Tabela progressiva de TEF (Sintef Express)
if qtd_pdv <= 3: preco_tef = 425.00
elif qtd_pdv <= 5: preco_tef = 510.00
elif qtd_pdv <= 8: preco_tef = 627.00
else: preco_tef = 803.00

# --- Cálculos Finais ---
valor_mensalidade_base = qtd_cnpj * PRECO_BASE_PRO
valor_total_pdvs = qtd_pdv * PRECO_PDV[tipo_pdv]

subtotal = valor_mensalidade_base + valor_total_pdvs + preco_tef
valor_final = subtotal * (1 - (desconto/100))

# --- Exibição Visual em Cartões ---
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("VR ERP PRO", f"R$ {valor_mensalidade_base:,.2f}")
    if bonificar_xml: st.caption("✅ XML Bonificado")
with c2:
    st.metric("Total PDVs", f"R$ {valor_total_pdvs:,.2f}")
    st.caption(f"{qtd_pdv} un. ({tipo_pdv})")
with c3:
    st.metric("TEF Express", f"R$ {preco_tef:,.2f}")
    if bonificar_mobile: st.caption("✅ Mobile Bonificado")

st.markdown("---")
# Destaque para o valor final em Laranja
st.markdown(f"""
    <div style="background-color: #ff6600; padding: 20px; border-radius: 10px; text-align: center;">
        <h2 style="color: white; margin: 0;">Total Mensal: R$ {valor_final:,.2f}</h2>
    </div>
""", unsafe_allow_html=True)

# --- Gerador de Resumo ---
st.write("")
if st.button("📱 Gerar Resumo para WhatsApp"):
    status = "⚠️ *Pendente Aprovação Financeira*" if desconto > 15 else "✅ *Proposta dentro da alçada*"
    resumo = f"""
*PROPOSTA COMERCIAL VR SOFTWARE*
{status}

📍 *Tipo:* {tipo_venda}
🏢 *CNPJs:* {qtd_cnpj}
💻 *PDVs:* {qtd_pdv} ({tipo_pdv})
🎁 *Bonificações:* {"XML " if bonificar_xml else ""}{"Mobile" if bonificar_mobile else "Nenhuma"}

📉 *Desconto:* {desconto}%
💵 *Total Mensal: R$ {valor_final:,.2f}*
    """
    st.code(resumo)
