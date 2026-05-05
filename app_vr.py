import streamlit as st
import pandas as pd
import os

# 1. Configuracao da Pagina
st.set_page_config(page_title="VR Software | Proposta Comercial", layout="wide")

# 2. Estilizacao CSS - Foco em Alinhamento e Rótulos Precisos
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #ffffff 0%, #fff5ed 100%); }
    
    .hero-title {
        color: #262730; font-size: 5.5rem; font-weight: 900; margin: 0; padding: 0;
        line-height: 1; letter-spacing: -3px; text-transform: uppercase;
    }

    /* --- ESTILO DOS CARDS DE RESUMO --- */
    .resumo-card {
        background-color: #ffffff; border: 1px solid #f0f0f0; border-top: 8px solid #ff6600;
        padding: 25px; border-radius: 10px; min-height: 500px; box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    }
    
    .resumo-label { color: #666; font-size: 0.9rem; font-weight: 700; margin-bottom: 8px; display: block; }
    .resumo-valor { color: #ff6600; font-size: 3rem; font-weight: 900; margin-bottom: 5px; line-height: 1; }
    
    .resumo-subtitulo {
        font-size: 1rem; color: #111; font-weight: 800; margin-top: 25px;
        margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 8px;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    
    /* Alinhamento da Lista: Nome à Esquerda, Detalhe à Direita */
    .lista-itens { list-style-type: none; padding: 0; margin: 0; }
    .lista-itens li { 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        padding: 12px 0; 
        border-bottom: 1px dashed #e0e0e0; 
    }

    .item-nome { color: #333; font-size: 1rem; font-weight: 700; flex: 1; }
    .item-detalhe { color: #000; font-size: 1rem; font-weight: 800; text-align: right; white-space: nowrap; }

    /* Alerta de Despesas conforme a Imagem */
    .alerta-despesa {
        font-size: 0.95rem; color: #d32f2f; font-weight: 700; 
        background: #fff5f5; padding: 8px 12px; border-radius: 4px;
        display: block; width: 100%; margin-top: 10px;
    }

    .tooltip { border-bottom: 1px dotted #ff6600; cursor: help; }
    </style>
    """, unsafe_allow_html=True)

# --- (Omitindo lógica de dados para focar na Seção 6 de Resumo) ---
# Simulando os dados conforme o seu código anterior para o exemplo:
t_imp = st.session_state.get('t_imp', 31402.80)
parcelas = st.session_state.get('parcelas', 4)
t_men_liq = st.session_state.get('t_men_liq', 1285.71)
desc = st.session_state.get('desc', 0.0)
t_desp = st.session_state.get('t_desp', 0.0)
dados_imp_final = st.session_state.get('dados_imp', [("Migração Banco de Dados", 12, 201.30), ("Definição de Escopo", 12, 201.30), ("Configuração Servidor / PDV Linux", 12, 201.30), ("Implantação e Treinamento", 120, 201.30)])
dados_mensal_final = st.session_state.get('dados_mensal', [("VR ERP PRO", 1, 1285.71)])
dados_desp_final = st.session_state.get('dados_desp', [])

# 6. SEÇÃO DE RESUMO VISUAL AJUSTADA
st.markdown("<h2 style='text-align: center; color: #333; font-weight: 800; margin: 40px 0;'>DETALHAMENTO DA PROPOSTA</h2>", unsafe_allow_html=True)
res_col1, res_col2, res_col3 = st.columns(3)

with res_col1:
    html_itens = "".join([f"<li><span class='item-nome'>{i}</span><span class='item-detalhe'>{h}h x R$ {v:,.2f}</span></li>" for i, h, v in dados_imp_final])
    st.markdown(f"""
        <div class="resumo-card">
            <span class="resumo-label">Investimento Setup</span>
            <div class="resumo-valor">R$ {t_imp:,.2f}</div>
            <div style="font-size: 1.2rem; font-weight: 800; color: #333;">{parcelas}x de R$ {t_imp/parcelas:,.2f}</div>
            <div class="resumo-subtitulo">SERVIÇOS DE IMPLANTAÇÃO</div>
            <ul class="lista-itens">{html_itens}</ul>
        </div>
    """, unsafe_allow_html=True)

with res_col2:
    html_itens = "".join([f"<li><span class='item-nome'>{i}</span><span class='item-detalhe'>{q} Lic. x R$ {v:,.2f}</span></li>" for i, q, v in dados_mensal_final])
    st.markdown(f"""
        <div class="resumo-card" style="border-top-color: #2e7d32;">
            <span class="resumo-label">Investimento Mensal</span>
            <div class="resumo-valor" style="color: #2e7d32;">R$ {t_men_liq:,.2f}</div>
            <div style="font-size: 1.1rem; color: #2e7d32; font-weight: 700;">Desconto aplicado: {desc}%</div>
            <div class="resumo-subtitulo">SISTEMAS E LICENÇAS</div>
            <ul class="lista-itens">{html_itens}</ul>
        </div>
    """, unsafe_allow_html=True)

with res_col3:
    html_itens = "".join([f"<li><span class='item-nome'>{i}</span><span class='item-detalhe'>{q} un. x R$ {v:,.2f}</span></li>" for i, q, v in dados_desp_final])
    st.markdown(f"""
        <div class="resumo-card" style="border-top-color: #1976d2;">
            <span class="resumo-label">Previsão de Despesas</span>
            <div class="resumo-valor" style="color: #1976d2;">R$ {t_desp:,.2f}</div>
            <div class="alerta-despesa">Faturadas ao término da implantação</div>
            <div class="resumo-subtitulo">DETALHAMENTO LOGÍSTICO</div>
            <ul class="lista-itens">{html_itens if html_itens else "<li>Nenhuma despesa selecionada</li>"}</ul>
        </div>
    """, unsafe_allow_html=True)
