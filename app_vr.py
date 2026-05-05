import streamlit as st
import pandas as pd
import os

# 1. Configuracao da Pagina
st.set_page_config(page_title="VR Software | Proposta Comercial", layout="wide")

# 2. Estilizacao CSS - Foco total no alinhamento
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #ffffff 0%, #fff5ed 100%);
    }
    
    /* CONTAINER DO CABEÇALHO PARA ALINHAMENTO VERTICAL */
    [data-testid="stHorizontalBlock"] {
        align-items: center; /* Centraliza verticalmente logo e título */
        padding-top: 20px;
        margin-bottom: 20px;
    }
    
    .hero-title {
        color: #262730;
        font-size: 3.8rem; 
        font-weight: 900; 
        margin: 0; 
        line-height: 1; 
        letter-spacing: -1px; 
        text-transform: uppercase;
        text-align: left;
    }

    /* Estilos de interface mantidos para estabilidade */
    .section-header {
        display: flex; justify-content: space-between; align-items: center;
        background: linear-gradient(90deg, #ff6600 0%, #ff944d 100%);
        padding: 8px 15px; border-radius: 5px; margin-bottom: 15px; margin-top: 20px;
    }
    .section-title { color: #ffffff; font-size: 1.1rem; font-weight: bold; margin: 0; }

    .resumo-card {
        background-color: #ffffff; border: 1px solid #f0f0f0; border-top: 8px solid #ff6600;
        padding: 25 : 8px; min-height: 520px; box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    }
    .resumo-valor { color: #ff6600; font-size: 2.5rem; font-weight: 900; }
    
    .sidebar-label {
        color: #ff6600; font-size: 0.9rem; font-weight: 800; text-transform: uppercase;
        margin-top: 20px; display: block;
    }
    </style>
    """, unsafe_allow_html=True)

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("PAINEL DE CONTROLE")
    modo_apresentacao = st.toggle("Modo Apresentação 🖥️", value=False)
    desc = st.number_input("Desconto Mensal (%)", 0.0, 30.0, 0.0)
    parcelas = st.selectbox("Parcelamento Setup", [1, 2, 3, 4, 6, 10, 12], index=2)

# --- CABEÇALHO CORRIGIDO (Alinhado com a imagem) ---
# Usamos colunas nativas mas o CSS acima força o alinhamento central
head_col1, head_col2 = st.columns([1, 3])

with head_col1:
    if os.path.exists("logo_vr.png"):
        st.image("logo_vr.png", width=350)
    else:
        st.subheader("VR SOFTWARE")

with head_col2:
    if not modo_apresentacao:
        st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)

st.markdown("<hr style='margin-top: 0; margin-bottom: 30px; opacity: 0.2;'>", unsafe_allow_html=True)

# --- LOGICA DE DADOS (Simplificada para o exemplo, mantenha a sua original) ---
itens_imp = {"Migração Banco de Dados": 201.30, "Definição de Escopo": 201.30, "Configuração Servidor / PDV Linux": 201.30, "Implantação e Treinamento": 201.30}
itens_mensal = {"VR ERP PRO": 1285.71, "VR PDV Convencional": 185.71}
itens_desp = {"Alimentação": 49.00, "Hospedagem": 195.00}

# 5. Interface de Seleção
if not modo_apresentacao:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="section-header"><span class="section-title">SERVIÇOS DE IMPLANTAÇÃO</span></div>', unsafe_allow_html=True)
        imp_sel = st.multiselect("Itens", list(itens_imp.keys()), default=list(itens_imp.keys()))
        t_imp = sum([itens_imp[item] * 12 for item in imp_sel]) # Exemplo de calculo

    with col2:
        st.markdown('<div class="section-header"><span class="section-title">ITENS MENSAIS</span></div>', unsafe_allow_html=True)
        mensal_sel = st.multiselect("Produtos", list(itens_mensal.keys()), default=["VR ERP PRO"])
        t_men_liq = sum([itens_mensal[item] for item in mensal_sel]) * (1 - (desc/100))

    with col3:
        st.markdown('<div class="section-header"><span class="section-title">PREVISÃO DE DESPESAS</span></div>', unsafe_allow_html=True)
        t_desp = 0 # Valor base para exemplo

    st.session_state.update({'t_imp': t_imp, 't_men_liq': t_men_liq, 't_desp': t_desp})
else:
    t_imp = st.session_state.get('t_imp', 0)
    t_men_liq = st.session_state.get('t_men_liq', 0)
    t_desp = st.session_state.get('t_desp', 0)

# 6. RESUMO VISUAL
st.markdown("<h2 style='text-align: center; color: #333; font-weight: 800; margin-bottom: 30px;'>DETALHAMENTO DA PROPOSTA</h2>", unsafe_allow_html=True)
res_col1, res_col2, res_col3 = st.columns(3)

with res_col1:
    st.markdown(f'<div class="resumo-card">Investimento Setup<div class="resumo-valor">R$ {t_imp:,.2f}</div><div style="font-weight: bold;">{parcelas}x de R$ {t_imp/parcelas:,.2f}</div></div>', unsafe_allow_html=True)

with res_col2:
    st.markdown(f'<div class="resumo-card" style="border-top-color: #2e7d32;">Investimento Mensal<div class="resumo-valor">R$ {t_men_liq:,.2f}</div><div style="color: #2e7d32; font-weight: bold;">Desconto: {desc}%</div></div>', unsafe_allow_html=True)

with res_col3:
    st.markdown(f'<div class="resumo-card" style="border-top-color: #1976d2;">Previsão de Despesas<div class="resumo-valor">R$ {t_desp:,.2f}</div></div>', unsafe_allow_html=True)
