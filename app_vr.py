import streamlit as st
import pandas as pd
import os

# 1. Configuracao da Pagina
st.set_page_config(page_title="VR Software | Proposta Comercial", layout="wide")

# 2. Estilizacao CSS (Versão Estável)
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #ffffff 0%, #fff5ed 100%);
    }
    
    .hero-title {
        color: #262730;
        font-size: 3.5rem; 
        font-weight: 900; 
        margin: 0; 
        padding-top: 25px; 
        line-height: 1; 
        letter-spacing: -1px; 
        text-transform: uppercase;
    }

    .sidebar-label {
        color: #ff6600; font-size: 0.9rem; font-weight: 800; text-transform: uppercase;
        margin-top: 20px; margin-bottom: 10px; display: block; letter-spacing: 1px;
    }

    div.stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #ff6600 0%, #ff944d 100%);
        color: white;
        border: none;
        padding: 12px 20px;
        border-radius: 8px;
        font-weight: bold;
        font-size: 1rem;
        transition: all 0.3s ease;
    }

    .section-header {
        display: flex; justify-content: space-between; align-items: center;
        background: linear-gradient(90deg, #ff6600 0%, #ff944d 100%);
        padding: 8px 15px; border-radius: 5px; margin-bottom: 15px; margin-top: 20px;
    }
    .section-title { color: #ffffff; font-size: 1.1rem; font-weight: bold; margin: 0; }

    .resumo-card {
        background-color: #ffffff; border: 1px solid #f0f0f0; border-top: 8px solid #ff6600;
        padding: 25px; border-radius: 8px; min-height: 520px; box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    }
    .resumo-valor { color: #ff6600; font-size: 2.5rem; font-weight: 900; margin-bottom: 5px; }
    
    .item-detalhe { 
        color: #222; 
        font-size: 1.1rem; 
        font-weight: 800;
        text-align: right;
    }

    .lista-itens li { 
        padding: 12px 0; 
        border-bottom: 1px dashed #e0e0e0; 
        display: flex; 
        justify-content: space-between; 
        align-items: center;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Cabeçalho (Voltou ao Original Seguro)
head_col1, head_col2 = st.columns([1, 2])

with head_col1:
    if os.path.exists("logo_vr.png"):
        st.image("logo_vr.png", width=300)
    else:
        st.subheader("VR SOFTWARE")

with head_col2:
    st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)

st.markdown("---")

# --- LÓGICA DE DADOS (Dicionários completos mantidos) ---
itens_imp = {"Migração Banco de Dados": 201.30, "Definição de Escopo": 201.30, "Configuração Servidor / PDV Linux": 201.30, "Implantação e Treinamento": 201.30}
itens_mensal = {"VR ERP PRO": 1285.71, "VR PDV Convencional": 185.71, "PDV Touchscreen": 185.71, "PDV Selfcheckout": 290.44, "SiTef Express": 357.14, "VR TEF": 417.04, "Gerenciador XML": 163.84, "VR Mobile": 193.63}
itens_desp = {"Alimentação": 49.00, "Hospedagem": 195.00, "Deslocamento (KM)": 2.12}

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("PAINEL DE CONTROLE")
    modo_apresentacao = st.toggle("Modo Apresentação", value=False)
    desc = st.number_input("Desconto Mensal (%)", 0.0, 30.0, 0.0)
    parcelas = st.selectbox("Parcelamento Setup", [1, 2, 3, 4, 6, 10, 12], index=2)

# 4. Interface de Seleção
if not modo_apresentacao:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="section-header"><span class="section-title">SERVIÇOS DE IMPLANTAÇÃO</span></div>', unsafe_allow_html=True)
        imp_sel = st.multiselect("Itens", list(itens_imp.keys()), default=list(itens_imp.keys()))
        t_imp = 0
        dados_imp_final = []
        for item in imp_sel:
            v_u = itens_imp[item]
            h = st.number_input(f"Hrs: {item}", 0, 200, 12, key=f"h_{item}")
            t_imp += h * v_u
            dados_imp_final.append((item, h, v_u))

    with col2:
        st.markdown('<div class="section-header"><span class="section-title">ITENS MENSAIS</span></div>', unsafe_allow_html=True)
        mensal_sel = st.multiselect("Produtos", list(itens_mensal.keys()), default=["VR ERP PRO"])
        t_men_bruto = 0
        dados_mensal_final = []
        for item in mensal_sel:
            v_u = itens_mensal[item]
            q = st.number_input(f"Qtd: {item}", 0, 50, 1, key=f"q_{item}")
            t_men_bruto += q * v_u
            dados_mensal_final.append((item, q, v_u))
        t_men_liq = t_men_bruto * (1 - (desc/100))

    with col3:
        st.markdown('<div class="section-header"><span class="section-title">PREVISÃO DE DESPESAS</span></div>', unsafe_allow_html=True)
        t_desp = 0
        dados_desp_final = []
        for item, preco in itens_desp.items():
            qd = st.number_input(f"{item}", 0, 1000, 0, key=f"d_{item}")
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

# 5. RESUMO VISUAL
st.markdown("<h2 style='text-align: center; color: #333; font-weight: 800; margin-bottom: 30px;'>DETALHAMENTO DA PROPOSTA</h2>", unsafe_allow_html=True)
res_col1, res_col2, res_col3 = st.columns(3)

with res_col1:
    html_itens = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{h}h x R$ {v:,.2f}</span></li>" for i, h, v in dados_imp_final])
    st.markdown(f'<div class="resumo-card">Investimento Setup<div class="resumo-valor">R$ {t_imp:,.2f}</div><div style="font-weight: bold;">{parcelas}x de R$ {t_imp/parcelas:,.2f}</div><ul class="lista-itens">{html_itens}</ul></div>', unsafe_allow_html=True)

with res_col2:
    html_itens = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{q} Lic. x R$ {v:,.2f}</span></li>" for i, q, v in dados_mensal_final])
    st.markdown(f'<div class="resumo-card" style="border-top-color: #2e7d32;">Investimento Mensal<div class="resumo-valor">R$ {t_men_liq:,.2f}</div><div style="color: #2e7d32; font-weight: bold;">Desconto: {desc}%</div><ul class="lista-itens">{html_itens}</ul></div>', unsafe_allow_html=True)

with res_col3:
    html_itens = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{q} Qtd. x R$ {v:,.2f}</span></li>" for i, q, v in dados_desp_final])
    st.markdown(f'<div class="resumo-card" style="border-top-color: #1976d2;">Previsão de Despesas<div class="resumo-valor">R$ {t_desp:,.2f}</div><ul class="lista-itens">{html_itens}</ul></div>', unsafe_allow_html=True)
