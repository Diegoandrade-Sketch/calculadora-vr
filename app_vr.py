import streamlit as st
import pandas as pd
import os

# 1. Configuração da Página
st.set_page_config(page_title="VR Software | Simulador Comercial", layout="wide")

# 2. Estilização Profissional (Laranja e Branco)
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    h3 { color: #ff6600; border-bottom: 2px solid #ff6600; padding-bottom: 5px; margin-top: 20px; }
    [data-testid="stMetricValue"] { color: #ff6600; font-size: 1.8rem; }
    .stNumberInput label { font-weight: bold; }
    /* Estilo para o bloco de resumo final */
    .resumo-container {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
        border-left: 5px solid #ff6600;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Cabeçalho com Logo Local
# Se o arquivo logo_vr.png existir na pasta, ele carrega. Se não, usa o título.
if os.path.exists("logo_vr.png"):
    st.image("logo_vr.png", width=250)
else:
    st.title("VR Software | Simulador Comercial")

st.markdown("---")

# 4. Dados de Preço (Baseados na sua Proposta)
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
    "SiTef Express até 3 PDVs": 357.14,
    "SiTef Express até 6 PDVs": 428.57,
    "SiTef Express até 8 PDVs": 500.00,
    "SiTef Express a partir de 9 PDVs": 571.43,
    "VR TEF": 417.04,
    "Gerenciador XML": 163.84,
    "VR Mobile": 193.63,
    "VR Carteira Digital": 275.54
}

itens_desp = {
    "Alimentação": 49.00, 
    "Hospedagem": 195.00, 
    "Deslocamento (KM)": 2.12
}

# 5. Interface de Montagem em 3 Colunas
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Licença Implantação")
    imp_sel = st.multiselect("Serviços de Setup", list(itens_imp.keys()), default=list(itens_imp.keys()))
    total_imp = 0
    for item in imp_sel:
        h = st.number_input(f"Horas: {item}", min_value=0, value=12 if "Treinamento" not in item else 120, key=f"h_{item}")
        total_imp += h * itens_imp[item]
    st.write(f"**Subtotal Implantação: R$ {total_imp:,.2f}**")

with col2:
    st.subheader("Licença Mensal")
    mensal_sel = st.multiselect("Produtos e Licenças", list(itens_mensal.keys()), default=["VR ERP PRO"])
    total_mensal_bruto = 0
    for item in mensal_sel:
        q = st.number_input(f"Qtd: {item}", min_value=0, value=1, key=f"q_{item}")
        total_mensal_bruto += q * itens_mensal[item]
    
    st.write("---")
    desconto = st.number_input("Desconto Comercial (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.1)
    total_mensal_liquido = total_mensal_bruto * (1 - (desconto/100))
    
    if desconto > 15:
        st.error("Alerta: Requer aprovação da gerência.")

with col3:
    st.subheader("Despesas")
    total_despesas = 0
    for item, preco in itens_desp.items():
        qd = st.number_input(f"{item} (Qtd/KM)", min_value=0, value=0, key=f"d_{item}")
        total_despesas += qd * preco
    st.write(f"**Previsão de Despesas: R$ {total_despesas:,.2f}**")

st.markdown("---")

# 6. Resumo Executivo
st.subheader("Resumo do Investimento")
c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Setup Total", f"R$ {total_imp:,.2f}")
    parc = st.selectbox("Parcelamento Sugerido", [1, 2, 3, 4, 5, 6, 10, 12], index=3)
    st.caption(f"Parcelas de R$ {total_imp/parc:,.2f}")

with c2:
    st.metric("Mensalidade Recorrente", f"R$ {total_mensal_liquido:,.2f}")
    st.caption(f"Valor bruto: R$ {total_mensal_bruto:,.2f}")

with c3:
    st.metric("Despesas Previstas", f"R$ {total_despesas:,.2f}")
    st.caption("Faturado pós-implantação")

# 7. Botão para Gerar Texto
if st.button("Gerar Sumário para Envio"):
    texto_resumo = f"""
PROPOSTA COMERCIAL - VR SOFTWARE

1. LICENÇA IMPLANTAÇÃO (INVESTIMENTO ÚNICO)
- Valor Total: R$ {total_imp:,.2f}
- Condição: {parc}x de R$ {total_imp/parc:,.2f}

2. LICENÇA MENSAL (RECORRENTE)
- Investimento Mensal: R$ {total_mensal_liquido:,.2f}
- Desconto aplicado: {desconto}%

3. DESPESAS DE VIAGEM (ESTIMATIVA)
- Valor Previsto: R$ {total_despesas:,.2f}
Obs: Valores referentes a deslocamento, hospedagem e alimentação serão faturados conforme realização.

---
Simulador de Vendas VR Software
"""
    st.code(texto_resumo, language="text")
