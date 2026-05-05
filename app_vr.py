import streamlit as st
import pandas as pd
import os

# 1. Configuração da Página
st.set_page_config(page_title="VR Software | Proposta Comercial", layout="wide")

# 2. Estilização CSS
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    
    .hero-title {
        color: #262730;
        font-size: 5.5rem;
        font-weight: 900;
        margin: 0;
        padding: 0;
        line-height: 1;
        letter-spacing: -3px;
    }
    
    .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 2px solid #ff6600;
        padding-bottom: 5px;
        margin-bottom: 15px;
        margin-top: 20px;
    }
    .section-title {
        color: #ff6600;
        font-size: 1.2rem;
        font-weight: bold;
        margin: 0;
    }
    .section-total {
        color: #333;
        font-size: 1.1rem;
        font-weight: bold;
        background-color: #fff2e6;
        padding: 2px 10px;
        border-radius: 5px;
    }

    [data-testid="stMetricValue"] { color: #ff6600; font-size: 2rem; }
    </style>
    """, unsafe_allow_html=True)

# 3. Cabeçalho
head_col1, head_col2 = st.columns([1, 4])

with head_col1:
    if os.path.exists("logo_vr.png"):
        st.image("logo_vr.png", width=220)
    else:
        st.subheader("VR SOFTWARE")

with head_col2:
    st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)

st.markdown("---")

# 4. Dados de Preço
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

# --- BARRA LATERAL: ÁREA DE NEGOCIAÇÃO FINANCEIRA ---
with st.sidebar:
    st.header("⚙️ Negociação Financeira")
    
    st.subheader("Mensalidade")
    desc = st.number_input("Desconto (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.1)
    
    st.write("---")
    
    st.subheader("Implantação")
    parcelas = st.selectbox("Parcelamento Setup", [1, 2, 3, 4, 5, 6, 10, 12], index=3)
    
    if desc > 15:
        st.error("⚠️ Desconto requer aprovação.")

# 5. Interface Principal em 3 Colunas
col1, col2, col3 = st.columns(3)

with col1:
    placeholder_imp = st.empty()
    with st.expander("Selecionar Itens de Implantação", expanded=True):
        imp_sel = st.multiselect("Serviços de Setup", list(itens_imp.keys()), default=list(itens_imp.keys()))
    
    t_imp = 0
    for item in imp_sel:
        val_unit = itens_imp[item]
        h = st.number_input(f"Horas: {item} (R$ {val_unit:,.2f}/h)", min_value=0, value=12 if "Treinamento" not in item else 120, key=f"h_{item}")
        t_imp += h * val_unit
    
    placeholder_imp.markdown(f'<div class="section-header"><span class="section-title">LICENÇA IMPLANTAÇÃO</span><span class="section-total">R$ {t_imp:,.2f}</span></div>', unsafe_allow_html=True)
    st.caption(f"Parcelado em {parcelas}x de R$ {t_imp/parcelas:,.2f}")

with col2:
    placeholder_men = st.empty()
    with st.expander("Selecionar Itens Mensais", expanded=True):
        mensal_sel = st.multiselect("Produtos e Licenças", list(itens_mensal.keys()), default=["VR ERP PRO"])
    
    t_men_bruto = 0
    for item in mensal_sel:
        val_unit = itens_mensal[item]
        q = st.number_input(f"Qtd: {item} (R$ {val_unit:,.2f} un)", min_value=0, value=1, key=f"q_{item}")
        t_men_bruto += q * val_unit
    
    t_men_liq = t_men_bruto * (1 - (desc/100))

    placeholder_men.markdown(f'<div class="section-header"><span class="section-title">LICENÇA MENSAL</span><span class="section-total">R$ {t_men_liq:,.2f}</span></div>', unsafe_allow_html=True)

with col3:
    placeholder_des = st.empty()
    t_desp = 0
    for item, preco in itens_desp.items():
        qd = st.number_input(f"{item} (R$ {preco:,.2f})", min_value=0, value=0, key=f"d_{item}")
        t_desp += qd * preco

    placeholder_des.markdown(f'<div class="section-header"><span class="section-title">DESPESAS DE PROJETO</span><span class="section-total">R$ {t_desp:,.2f}</span></div>', unsafe_allow_html=True)

st.markdown("---")

# 6. Resumo Final (Rodapé)
res1, res2, res3 = st.columns(3)
with res1:
    st.metric("Investimento Único", f"R$ {t_imp:,.2f}")
    st.write(f"Condição: {parcelas}x de R$ {t_imp/parcelas:,.2f}")
with res2:
    st.metric("Investimento Mensal", f"R$ {t_men_liq:,.2f}")
with res3:
    st.metric("Total Despesas", f"R$ {t_desp:,.2f}")

if st.button("Gerar Sumário Executivo"):
    resumo = f"""PROPOSTA COMERCIAL VR SOFTWARE

1. SETUP (ÚNICO): R$ {t_imp:,.2f} em {parcelas}x de R$ {t_imp/parcelas:,.2f}
2. MENSALIDADE: R$ {t_men_liq:,.2f}
3. DESPESAS PREVISTAS: R$ {t_desp:,.2f}"""
    st.code(resumo, language="text")
