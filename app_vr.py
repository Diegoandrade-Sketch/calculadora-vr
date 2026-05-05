import streamlit as st
import pandas as pd
import os

# 1. Configuracao da Pagina
st.set_page_config(page_title="VR Software | Proposta Comercial", layout="wide")

# 2. Estilizacao CSS (Incluindo a logica do Balao/Tooltip)
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #ffffff 0%, #fff5ed 100%);
    }
    
    .hero-title {
        color: #262730; font-size: 5.5rem; font-weight: 900; margin: 0; padding: 0;
        line-height: 1; letter-spacing: -3px; text-transform: uppercase;
    }
    
    .section-header {
        display: flex; justify-content: space-between; align-items: center;
        background: linear-gradient(90deg, #ff6600 0%, #ff944d 100%);
        padding: 8px 15px; border-radius: 5px; margin-bottom: 15px; margin-top: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .section-title { color: #ffffff; font-size: 1.1rem; font-weight: bold; margin: 0; }

    .resumo-card {
        background-color: #ffffff; border: 1px solid #f0f0f0; border-top: 8px solid #ff6600;
        padding: 25px; border-radius: 8px; min-height: 450px; box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    }
    .resumo-label { color: #555; font-size: 1rem; text-transform: uppercase; font-weight: bold; margin-bottom: 10px; display: block; }
    .resumo-valor { color: #ff6600; font-size: 2.5rem; font-weight: 900; margin-bottom: 5px; }
    .resumo-subtitulo {
        font-size: 1.1rem; color: #333; font-weight: bold; margin-top: 20px;
        margin-bottom: 10px; border-bottom: 2px solid #ffefe5; padding-bottom: 5px;
    }
    .lista-itens { font-size: 1.05rem; color: #444; line-height: 1.6; list-style-type: none; padding-left: 0; }
    .lista-itens li { padding: 6px 0; border-bottom: 1px dashed #f0f0f0; display: flex; justify-content: space-between; }
    .item-detalhe { color: #777; font-size: 0.9rem; }

    /* LOGICA DO BALAO (TOOLTIP) */
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: help;
        border-bottom: 1px dotted #ff6600; /* Indica que ha info ao passar o mouse */
    }

    .tooltip .tooltiptext {
        visibility: hidden;
        width: 250px;
        background-color: #333;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 10px;
        position: absolute;
        z-index: 1;
        bottom: 125%; /* Aparece acima do texto */
        left: 50%;
        margin-left: -125px;
        opacity: 0;
        transition: opacity 0.3s;
        font-size: 0.85rem;
        line-height: 1.2;
        font-weight: normal;
    }

    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }

    /* Ajuste para o botao na Sidebar */
    .sidebar .stButton button {
        width: 100%;
        background-color: #ffffff;
        border: 1px solid #ff6600;
        color: #ff6600;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Cabecalho
head_col1, head_col2 = st.columns([1, 4])
with head_col1:
    if os.path.exists("logo_vr.png"):
        st.image("logo_vr.png", width=220)
    else:
        st.subheader("VR SOFTWARE")
with head_col2:
    st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)

st.markdown("---")

# 4. Dados de Preco e Descricoes (Tooltips)
itens_imp = {
    "Migracao Banco de Dados": 201.30, 
    "Definicao de Escopo": 201.30, 
    "Configuracao Servidor / PDV Linux": 201.30, 
    "Implantacao e Treinamento": 201.30
}

# Dicionario de descricoes para os baloes
descricoes = {
    "Migracao Banco de Dados": "Copia do Cadastro de produtos, cadastro de fornecedor e contas a receber em aberto."
}

itens_mensal = {
    "VR ERP PRO": 1285.71, "VR PDV Convencional": 185.71, "PDV Touchscreen": 185.71, 
    "PDV Selfcheckout": 290.44, "SiTef Express": 357.14, "VR TEF": 417.04, 
    "Gerenciador XML": 163.84, "VR Mobile": 193.63
}

itens_desp = {"Alimentacao": 49.00, "Hospedagem": 195.00, "Deslocamento (KM)": 2.12}

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("CONFIGURACAO")
    modo_apresentacao = st.toggle("Modo Apresentacao", value=False)
    st.write("---")
    st.subheader("Mensalidade")
    desc = st.number_input("Desconto (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.1)
    st.subheader("Implantacao")
    parcelas = st.selectbox("Parcelamento Setup", [1, 2, 3, 4, 5, 6, 10, 12], index=3)
    
    st.write("---")
    # BOTAO PARA WHATSAPP NA SIDEBAR
    if st.button("FORMATAR PARA WHATSAPP"):
        t_i = st.session_state.get('t_imp', 0)
        t_m = st.session_state.get('t_men_liq', 0)
        t_d = st.session_state.get('t_desp', 0)
        resumo_txt = f"PROPOSTA VR SOFTWARE\n\nIMPLANTACAO: R$ {t_i:,.2f} em {parcelas}x\nMENSALIDADE: R$ {t_m:,.2f}\nDESPESAS: R$ {t_d:,.2f}"
        st.code(resumo_txt, language="text")

# 5. Interface de Selecao (Ocultavel)
if not modo_apresentacao:
    col1, col2, col3 = st.columns(3)
    
    dados_imp_final = []
    with col1:
        st.markdown('<div class="section-header"><span class="section-title">ITENS DE IMPLANTACAO</span></div>', unsafe_allow_html=True)
        imp_sel = st.multiselect("Servicos", list(itens_imp.keys()), default=list(itens_imp.keys()))
        t_imp = 0
        for item in imp_sel:
            val_unit = itens_imp[item]
            h = st.number_input(f"Horas: {item}", min_value=0, value=12 if "Treinamento" not in item else 120, key=f"h_{item}")
            t_imp += h * val_unit
            dados_imp_final.append((item, h, val_unit))

    dados_mensal_final = []
    with col2:
        st.markdown('<div class="section-header"><span class="section-title">ITENS MENSAIS</span></div>', unsafe_allow_html=True)
        mensal_sel = st.multiselect("Produtos", list(itens_mensal.keys()), default=["VR ERP PRO"])
        t_men_bruto = 0
        for item in mensal_sel:
            val_unit = itens_mensal[item]
            q = st.number_input(f"Qtd: {item}", min_value=0, value=1, key=f"q_{item}")
            t_men_bruto += q * val_unit
            dados_mensal_final.append((item, q, val_unit))
        t_men_liq = t_men_bruto * (1 - (desc/100))

    dados_desp_final = []
    with col3:
        st.markdown('<div class="section-header"><span class="section-title">DESPESAS</span></div>', unsafe_allow_html=True)
        t_desp = 0
        for item, preco in itens_desp.items():
            qd = st.number_input(f"{item}", min_value=0, value=0, key=f"d_{item}")
            t_desp += qd * preco
            if qd > 0: dados_desp_final.append((item, qd, preco))

    st.session_state.update({'t_imp': t_imp, 'dados_imp': dados_imp_final, 't_men_liq': t_men_liq, 'dados_mensal': dados_mensal_final, 't_desp': t_desp, 'dados_desp': dados_desp_final})
else:
    t_imp = st.session_state.get('t_imp', 0)
    dados_imp_final = st.session_state.get('dados_imp', [])
    t_men_liq = st.session_state.get('t_men_liq', 0)
    dados_mensal_final = st.session_state.get('dados_mensal', [])
    t_desp = st.session_state.get('t_desp', 0)
    dados_desp_final = st.session_state.get('dados_desp', [])

# 6. SECAO DE RESUMO VISUAL
st.markdown("<h2 style='text-align: center; color: #333; font-weight: 800;'>DETALHAMENTO DA PROPOSTA</h2>", unsafe_allow_html=True)
res_col1, res_col2, res_col3 = st.columns(3)

with res_col1:
    # Geracao da lista com logica de Tooltip para itens que possuem descricao
    html_itens = ""
    for i, h, v in dados_imp_final:
        if i in descricoes:
            item_display = f'<span class="tooltip">{i}<span class="tooltiptext">{descricoes[i]}</span></span>'
        else:
            item_display = i
        html_itens += f"<li><span>{item_display}</span><span class='item-detalhe'>{h}h x R$ {v:,.2f}</span></li>"
        
    st.markdown(f"""
        <div class="resumo-card">
            <span class="resumo-label">Investimento Setup</span>
            <div class="resumo-valor">R$ {t_imp:,.2f}</div>
            <div style="font-size: 1.2rem; font-weight: bold;">{parcelas}x de R$ {t_imp/parcelas:,.2f}</div>
            <div class="resumo-subtitulo">SERVICOS INCLUSOS</div>
            <ul class="lista-itens">{html_itens if html_itens else "<li>Nenhum item selecionado</li>"}</ul>
        </div>
    """, unsafe_allow_html=True)

with res_col2:
    html_itens = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{q} Lic. x R$ {v:,.2f}</span></li>" for i, q, v in dados_mensal_final])
    st.markdown(f"""
        <div class="resumo-card" style="border-top-color: #2e7d32;">
            <span class="resumo-label">Investimento Mensal</span>
            <div class="resumo-valor">R$ {t_men_liq:,.2f}</div>
            <div style="font-size: 1.1rem; color: #2e7d32; font-weight: bold;">Desconto aplicado: {desc}%</div>
            <div class="resumo-subtitulo">SISTEMAS E LICENCAS</div>
            <ul class="lista-itens">{html_itens if html_itens else "<li>Nenhum item selecionado</li>"}</ul>
        </div>
    """, unsafe_allow_html=True)

with res_col3:
    html_itens = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{q} Qtd. x R$ {v:,.2f}</span></li>" for i, q, v in dados_desp_final])
    st.markdown(f"""
        <div class="resumo-card" style="border-top-color: #1976d2;">
            <span class="resumo-label">Previsao de Despesas</span>
            <div class="resumo-valor">R$ {t_desp:,.2f}</div>
            <div style="font-size: 1rem; color: #d32f2f; font-weight: bold; background: #fff5f5; padding: 5px; border-radius: 4px;">Faturadas ao termino da implantacao</div>
            <div class="resumo-subtitulo">DETALHAMENTO LOGISTICO</div>
            <ul class="lista-itens">{html_itens if html_itens else "<li>Nenhuma despesa selecionada</li>"}</ul>
        </div>
    """, unsafe_allow_html=True)
