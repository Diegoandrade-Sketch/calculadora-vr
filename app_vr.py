import streamlit as st
import pandas as pd
import os

# 1. Configuração da Página
st.set_page_config(page_title="VR Software | Proposta Comercial", layout="wide")

# 2. Estilização CSS Avançada
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    
    /* Títulos das Seções com Totalizadores */
    .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 2px solid #ff6600;
        padding-bottom: 5px;
        margin-bottom: 15px;
        margin-top: 10px;
    }
    .section-title {
        color: #ff6600;
        font-size: 1.1rem;
        font-weight: bold;
        margin: 0;
    }
    .section-total {
        color: #333;
        font-size: 1rem;
        font-weight: bold;
        background-color: #fff2e6;
        padding: 2px 8px;
        border-radius: 5px;
    }
    
    /* Título Principal de Grande Impacto */
    .main-title {
        color: #333;
        font-size: 3.5rem; /* Aumentado significativamente */
        font-weight: 900;
        margin: 0;
        line-height: 1;
        letter-spacing: -2px;
        text-transform: uppercase;
    }
    
    /* Estilização da Coluna de Desconto (Destaque) */
    .sidebar-negotiation {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #dee2e6;
    }

    [data-testid="stMetricValue"] { color: #ff6600; font-size: 2.2rem; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

# 3. Cabeçalho (Logo e Título Comercial)
head_col1, head_col2 = st.columns([1, 4])

with head_col1:
    if os.path.exists("logo_vr.png"):
        st.image("logo_vr.png", width=220)
    else:
        st.subheader("VR SOFTWARE")

with head_col2:
    st.markdown('<h1 class="main-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 4. Banco de Dados (Preços da Proposta Oficial)
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

itens_desp = {
    "Alimentação": 49.00, 
    "Hospedagem": 195.00, 
    "Deslocamento (KM)": 2.12
}

# 5. Interface Principal (Distribuída em 4 Colunas para incluir o Desconto lateral)
col1, col2, col3, col4 = st.columns([1, 1, 1, 0.8])

with col1:
    placeholder_imp = st.empty()
    imp_sel = st.multiselect("Itens de Implantação", list(itens_imp.keys()), default=list(itens_imp.keys()))
    t_imp = 0
    for item in imp_sel:
        h = st.number_input(f"Horas: {item}", min_value=0, value=12 if "Treinamento" not in item else 120, key=f"h_{item}")
        t_imp += h * itens_imp[item]
    
    placeholder_imp.markdown(f'<div class="section-header"><span class="section-title">LICENÇA IMPLANTAÇÃO</span><span class="section-total">R$ {t_imp:,.2f}</span></div>', unsafe_allow_html=True)

with col2:
    placeholder_men = st.empty()
    mensal_sel = st.multiselect("Itens Mensais", list(itens_mensal.keys()), default=["VR ERP PRO"])
    t_men_bruto = 0
    for item in mensal_sel:
        q = st.number_input(f"Qtd: {item}", min_value=0, value=1, key=f"q_{item}")
        t_men_bruto += q * itens_mensal[item]
    
    # O cálculo do líquido será feito com o valor da col4
    placeholder_men.markdown(f'<div class="section-header"><span class="section-title">LICENÇA MENSAL</span><span class="section-total">BRUTO: R$ {t_men_bruto:,.2f}</span></div>', unsafe_allow_html=True)

with col3:
    placeholder_des = st.empty()
    t_desp = 0
    for item, preco in itens_desp.items():
        qd = st.number_input(f"{item}", min_value=0, value=0, key=f"d_{item}")
        t_desp += qd * preco

    placeholder_des.markdown(f'<div class="section-header"><span class="section-title">DESPESAS DE PROJETO</span><span class="section-total">R$ {t_desp:,.2f}</span></div>', unsafe_allow_html=True)

# 6. Coluna 4: Área de Negociação Lateral (Desconto e Fechamento)
with col4:
    st.markdown('<div class="section-header"><span class="section-title">NEGOCIAÇÃO</span></div>', unsafe_allow_html=True)
    
    # Campo de Desconto isolado e visível
    desc = st.number_input("DESCONTO (%)", min_value=0.0, max_value=40.0, value=0.0, step=0.1, help="Aplicação exclusiva na licença mensal")
    
    t_men_liq = t_men_bruto * (1 - (desc/100))
    
    if desc > 15:
        st.error("⚠️ Alçada Financeira")
    elif desc > 0:
        st.warning(f"Economia: R$ {t_men_bruto - t_men_liq:,.2f}")

    st.write("---")
    st.metric("TOTAL MENSAL", f"R$ {t_men_liq:,.2f}")
    
    if st.button("GERAR TEXTO FINAL"):
        resumo = f"PROPOSTA VR SOFTWARE\n\n- Setup: R$ {t_imp:,.2f}\n- Mensalidade: R$ {t_men_liq:,.2f}\n- Despesas: R$ {t_desp:,.2f}"
        st.code(resumo, language="text")

st.markdown("---")

# 7. Rodapé com Resumo de Impacto
res1, res2, res3 = st.columns(3)
with res1:
    st.metric("Setup Inicial", f"R$ {t_imp:,.2f}")
with res2:
    st.metric("Investimento Mensal", f"R$ {t_men_liq:,.2f}")
with res3:
    st.metric("Previsão de Despesas", f"R$ {t_desp:,.2f}")
