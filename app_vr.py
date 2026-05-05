import streamlit as st

# Configuração da Página
st.set_page_config(page_title="Calculadora de Propostas VR 2026", layout="wide")

st.title("🚀 VR Software - Gerador de Propostas 2026")
st.markdown("---")

# --- Sidebar com Parâmetros de Entrada ---
st.sidebar.header("Configurações da Proposta")
tipo_negocio = st.sidebar.selectbox("Tipo de Negócio", ["Novo Negócio (VR ERP PRO)", "Loja Adicional"])
qtd_cnpj = st.sidebar.number_input("Quantidade de CNPJs", min_value=1, value=1)
qtd_pdv = st.sidebar.number_input("Quantidade de PDVs", min_value=1, value=1)
tipo_pdv = st.sidebar.radio("Tipo de PDV", ["Comum", "Touchscreen", "Self-Checkout"])

st.sidebar.markdown("---")
# --- NOVO CAMPO DE DESCONTO ---
st.sidebar.subheader("Negociação")
desconto_input = st.sidebar.number_input(
    "Digite o desconto (%)", 
    min_value=0, 
    max_value=30, 
    value=0,
    help="O desconto máximo padrão é 15%."
)

# Mensagem de orientação sobre o limite de desconto
if desconto_input > 15:
    st.sidebar.error("⚠️ Este desconto não será permitido, favor acionar o financeiro!")
elif desconto_input > 0:
    st.sidebar.info(f"Desconto de {desconto_input}% aplicado.")
else:
    st.sidebar.write("Seu desconto máximo é de 15%")

# --- Regras de Preço (Baseadas na Tabela Preço) ---
PRECO_CNPJ = 1090.91
PRECO_PDV_COMUM = 165.00
PRECO_PDV_TOUCH = 168.83
PRECO_PDV_SELF = 201.30

# Lógica de TEF (Sintef Express)
if qtd_pdv <= 3:
    preco_tef = 425.00
elif qtd_pdv <= 5:
    preco_tef = 510.00
elif qtd_pdv <= 8:
    preco_tef = 627.00
else:
    preco_tef = 803.00

# --- Cálculos ---
if tipo_pdv == "Comum":
    custo_pdvs = qtd_pdv * PRECO_PDV_COMUM
elif tipo_pdv == "Touchscreen":
    custo_pdvs = qtd_pdv * PRECO_PDV_TOUCH
else:
    custo_pdvs = qtd_pdv * PRECO_PDV_SELF

custo_base = qtd_cnpj * PRECO_CNPJ
subtotal_mensal = custo_base + custo_pdvs + preco_tef

# Aplicando o desconto (apenas visual, mas calcula o total)
valor_desconto = (subtotal_mensal * desconto_input) / 100
total_com_desconto = subtotal_mensal - valor_desconto

# --- Exibição dos Resultados ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Mensalidade Base", f"R$ {custo_base:,.2f}")

with col2:
    st.metric("Total PDVs", f"R$ {custo_pdvs:,.2f}")

with col3:
    st.metric("TEF", f"R$ {preco_tef:,.2f}")

with col4:
    # Exibe o desconto em vermelho se for alto
    cor_metrica = "normal" if desconto_input <= 15 else "inverse"
    st.metric("Desconto Aplicado", f"R$ {valor_desconto:,.2f}", f"-{desconto_input}%", delta_color=cor_metrica)

st.markdown("---")
st.subheader(f"💰 Valor Total Mensal: R$ {total_com_desconto:,.2f}")
if desconto_input > 0:
    st.write(f"*(Valor original sem desconto: R$ {subtotal_mensal:,.2f})*")

# --- Botão de Documentação ---
if st.button("Gerar Resumo para WhatsApp"):
    aviso_financeiro = "\n⚠️ *Pendente de aprovação financeira*" if desconto_input > 15 else ""
    texto_whats = f"*Proposta VR Software 2026*{aviso_financeiro}\n\n" \
                  f"📍 *Tipo:* {tipo_negocio}\n" \
                  f"🏢 *CNPJs:* {qtd_cnpj}\n" \
                  f"💻 *PDVs:* {qtd_pdv} ({tipo_pdv})\n" \
                  f"📉 *Desconto:* {desconto_input}%\n" \
                  f"--- \n" \
                  f"💵 *Total Mensal: R$ {total_com_desconto:,.2f}*"
    st.code(texto_whats)
