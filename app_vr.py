import streamlit as st
import pandas as pd

st.set_page_config(page_title="Simulador de Propostas VR", layout="wide")

# Estilização Profissional (Laranja e Branco)
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    h3 { color: #ff6600; border-bottom: 2px solid #ff6600; padding-bottom: 5px; }
    [data-testid="stMetricValue"] { color: #ff6600; font-size: 1.8rem; }
    .stNumberInput label { font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.image("https://vrsoft.com.br/wp-content/uploads/2022/07/Logo-VR-Software.png", width=220)
st.title("Simulador Comercial Profissional")

# --- CARREGAMENTO DE DADOS (Simulado para o exemplo) ---
# Substitua pela leitura real: pd.read_excel("precos.xlsx", sheet_name="...")
itens_imp = {"Migração": 201.30, "Escopo": 201.30, "Servidor": 201.30, "Treinamento": 201.30}
itens_mensal = {"VR ERP PRO": 1285.71, "PDV Convencional": 185.71, "PDV Touchscreen": 185.71, "SiTef Express": 357.14}
itens_desp = {"Alimentação": 49.00, "Hospedagem": 195.00, "Deslocamento (KM)": 2.12}

# --- INTERFACE DE MONTAGEM ---
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Licença Implantação")
    imp_selecionados = st.multiselect("Selecione os serviços", list(itens_imp.keys()), default=list(itens_imp.keys()))
    total_imp = 0
    for item in imp_selecionados:
        horas = st.number_input(f"Horas: {item}", min_value=0, value=10, key=f"h_{item}")
        total_imp += horas * itens_imp[item]
    st.markdown(f"**Total Implantação: R$ {total_imp:,.2f}**")

with col2:
    st.subheader("Licença Mensal")
    mensal_selecionados = st.multiselect("Selecione os produtos", list(itens_mensal.keys()), default=["VR ERP PRO"])
    total_mensal_bruto = 0
    for item in mensal_selecionados:
        qtd = st.number_input(f"Qtd: {item}", min_value=0, value=1, key=f"q_{item}")
        total_mensal_bruto += qtd * itens_mensal[item]
    
    st.write("---")
    desconto = st.number_input("Desconto na Mensalidade (%)", min_value=0.0, max_value=30.0, value=0.0)
    total_mensal_liquido = total_mensal_bruto * (1 - (desconto/100))
    
    if desconto > 15:
        st.error("Requer aprovação do financeiro.")

with col3:
    st.subheader("Despesas (Faturamento Posterior)")
    total_despesas = 0
    for item, preco in itens_desp.items():
        qtd_d = st.number_input(f"{item}", min_value=0, value=0, key=f"d_{item}")
        total_despesas += qtd_d * preco
    st.markdown(f"**Previsão de Despesas: R$ {total_despesas:,.2f}**")

st.markdown("---")

# --- RESUMO FINAL ---
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Setup Inicial (Total)", f"R$ {total_imp:,.2f}")
    parcelas = st.selectbox("Parcelamento Setup", [1, 2, 3, 4, 5, 6])
    st.caption(f"{parcelas}x de R$ {total_imp/parcelas:,.2f}")

with c2:
    st.metric("Mensalidade Recorrente", f"R$ {total_mensal_liquido:,.2f}")
    st.caption(f"Economia de R$ {total_mensal_bruto - total_mensal_liquido:,.2f} aplicada")

with c3:
    st.metric("Reembolso Despesas", f"R$ {total_despesas:,.2f}")
    st.caption("Faturado ao término do serviço")

if st.button("Gerar Proposta para WhatsApp"):
    texto = f"*PROPOSTA VR SOFTWARE*\n\n" \
            f"1. Setup: R$ {total_imp:,.2f} ({parcelas}x)\n" \
            f"2. Mensalidade: R$ {total_mensal_liquido:,.2f}\n" \
            f"3. Despesas previstas: R$ {total_despesas:,.2f}"
    st.code(texto)
