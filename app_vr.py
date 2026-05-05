import streamlit as st
import pandas as pd
import os

# 1. Configuração da Página
st.set_page_config(page_title="VR Software | Proposta Comercial", layout="wide")

# 2. Estilização CSS (Visual Corporativo, Sem Emojis, Fontes Grandes)
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
        text-transform: uppercase;
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
        font-size: 1.1rem;
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

    /* Cards de Detalhamento */
    .resumo-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-top: 10px solid #ff6600;
        padding: 30px;
        border-radius: 2px;
        min-height: 500px;
    }
    .resumo-label {
        color: #555;
        font-size: 1rem;
        text-transform: uppercase;
        font-weight: bold;
        display: block;
    }
    .resumo-valor {
        color: #000;
        font-size: 2.8rem;
        font-weight: 900;
        margin-bottom: 10px;
    }
    .resumo-subtitulo {
        font-size: 1.1rem;
        color: #000;
        font-weight: 800;
        margin-top: 25px;
        margin-bottom: 15px;
        border-bottom: 2px solid #333;
        padding-bottom: 5px;
    }
    .lista-itens {
        font-size: 1.05rem;
        color: #333;
        line-height: 1.8;
        list-style-type: none;
        padding-left: 0;
    }
    .lista-itens li {
        padding: 8px 0;
        border-bottom: 1px solid #f2f2f2;
        display: flex;
        justify-content: space-between;
    }
    .item-nome { font-weight: 500; }
    .item-detalhe { color: #666; font-size: 0.95rem; }
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

# --- BARRA LATERAL (NEGOCIAÇÃO) ---
with st.sidebar:
    st.markdown("### NEGOCIAÇÃO")
    desc = st.number_input("Desconto Mensalidade (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.1)
    st.write("---")
    parcelas = st.selectbox("Parcelas Implantação", [1, 2, 3, 4, 5, 6, 10, 12], index=3)

# 5. Interface Principal de Seleção e Coleta de Dados
col1, col2, col3 = st.columns(3)

dados_imp_vendedor = {}
with col1:
    st.markdown('<p class="section-title">ITENS DE IMPLANTAÇÃO</p>', unsafe_allow_html=True)
    imp_sel = st.multiselect("Serviços", list(itens_imp.keys()), default=list(itens_imp.keys()))
    t_imp = 0
    for item in imp_sel:
        val_unit = itens_imp[item]
        h = st.number_input(f"Horas: {item}", min_value=0, value=12 if "Treinamento" not in item else 120, key=f"h_{item}")
        t_imp += h * val_unit
        dados_imp_vendedor[item] = {"qtd": h, "unit": val_unit}

dados_mensal_vendedor = {}
with col2:
    st.markdown('<p class="section-title">ITENS MENSAIS</p>', unsafe_allow_html=True)
    mensal_sel = st.multiselect("Sistemas", list(itens_mensal.keys()), default=["VR ERP PRO"])
    t_men_bruto = 0
    for item in mensal_sel:
        val_unit = itens_mensal[item]
        q = st.number_input(f"Qtd: {item}", min_value=0, value=1, key=f"q_{item}")
        t_men_bruto += q * val_unit
        dados_mensal_vendedor[item] = {"qtd": q, "unit": val_unit}
    t_men_liq = t_men_bruto * (1 - (desc/100))

dados_desp_vendedor = {}
with col3:
    st.markdown('<p class="section-title">DESPESAS</p>', unsafe_allow_html=True)
    t_desp = 0
    for item, preco in itens_desp.items():
        qd = st.number_input(f"Qtd: {item}", min_value=0, value=0, key=f"d_{item}")
        t_desp += qd * preco
        if qd > 0:
            dados_desp_vendedor[item] = {"qtd": qd, "unit": preco}

st.markdown("<br><br>", unsafe_allow_html=True)

# 6. DETALHAMENTO DA PROPOSTA (TRANSPARENTE)
st.markdown("<h2 style='text-align: center; font-weight: 900;'>DETALHAMENTO PARA O CLIENTE</h2>", unsafe_allow_html=True)

res_col1, res_col2, res_col3 = st.columns(3)

with res_col1:
    itens_html = "".join([f"<li><span class='item-nome'>{k}</span> <span class='item-detalhe'>{v['qtd']}h x R$ {v['unit']:,.2f}</span></li>" for k, v in dados_imp_vendedor.items()])
    st.markdown(f"""
        <div class="resumo-card">
            <span class="resumo-label">Investimento Implantação</span>
            <div class="resumo-valor">R$ {t_imp:,.2f}</div>
            <div style="font-size: 1.3rem; font-weight: bold; color: #333;">{parcelas}x de R$ {t_imp/parcelas:,.2f}</div>
            <div class="resumo-subtitulo">SERVIÇOS PROFISSIONAIS</div>
            <ul class="lista-itens">
                {itens_html}
            </ul>
        </div>
    """, unsafe_allow_html=True)

with res_col2:
    itens_html = "".join([f"<li><span class='item-nome'>{k}</span> <span class='item-detalhe'>{v['qtd']} un x R$ {v['unit']:,.2f}</span></li>" for k, v in dados_mensal_vendedor.items()])
    st.markdown(f"""
        <div class="resumo-card" style="border-top-color: #333;">
            <span class="resumo-label">Licenciamento Mensal</span>
            <div class="resumo-valor">R$ {t_men_liq:,.2f}</div>
            <div style="font-size: 1.1rem; color: #666;">Desconto Comercial: {desc}%</div>
            <div class="resumo-subtitulo">SISTEMAS CONTRATADOS</div>
            <ul class="lista-itens">
                {itens_html}
            </ul>
        </div>
    """, unsafe_allow_html=True)

with res_col3:
    if not dados_desp_vendedor:
        desp_html = "<li>Nenhuma despesa prevista selecionada</li>"
    else:
        desp_html = "".join([f"<li><span class='item-nome'>{k}</span> <span class='item-detalhe'>{v['qtd']} un x R$ {v['unit']:,.2f}</span></li>" for k, v in dados_desp_vendedor.items()])
    
    st.markdown(f"""
        <div class="resumo-card" style="border-top-color: #999;">
            <span class="resumo-label">Estimativa de Despesas</span>
            <div class="resumo-valor">R$ {t_desp:,.2f}</div>
            <div style="font-size: 1.1rem; color: #d32f2f; font-weight: bold;">Faturamento ao término da implantação</div>
            <div class="resumo-subtitulo">DETALHAMENTO LOGÍSTICO</div>
            <ul class="lista-itens">
                {desp_html}
            </ul>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")
if st.button("GERAR FORMATO PARA WHATSAPP"):
    whatsapp = f"PROPOSTA COMERCIAL VR SOFTWARE\n\n"
    whatsapp += f"1. IMPLANTAÇÃO: R$ {t_imp:,.2f} ({parcelas}x)\n"
    whatsapp += f"2. MENSALIDADE: R$ {t_men_liq:,.2f}\n"
    whatsapp += f"3. DESPESAS (Faturadas ao fim): R$ {t_desp:,.2f}"
    st.code(whatsapp, language="text")
