import streamlit as st
import pandas as pd
import urllib.parse
import os

# 1. Configuracao da Pagina
st.set_page_config(page_title="VR Software | Proposta Comercial", layout="wide")

# 2. Estilizacao CSS Avançada (Mantendo a identidade visual validada)
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #ffffff 0%, #fff5ed 100%); }
    .hero-title { color: #262730; font-size: 5.5rem; font-weight: 900; margin: 0; line-height: 1; text-transform: uppercase; }
    .sidebar-label { color: #ff6600; font-size: 0.9rem; font-weight: 800; text-transform: uppercase; margin-top: 20px; margin-bottom: 10px; display: block; }
    
    div.stButton > button {
        width: 100%; background: linear-gradient(90deg, #ff6600 0%, #ff944d 100%);
        color: white; border: none; padding: 12px 20px; border-radius: 8px; font-weight: bold;
    }

    .resumo-card {
        background-color: #ffffff; border: 1px solid #f0f0f0; border-top: 8px solid #ff6600;
        padding: 25px; border-radius: 8px; min-height: 400px; box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    }
    .resumo-valor { color: #ff6600; font-size: 2.5rem; font-weight: 900; margin-bottom: 5px; }
    .resumo-label { color: #888; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; }
    
    .section-header {
        background: linear-gradient(90deg, #ff6600 0%, #ff944d 100%);
        padding: 8px 15px; border-radius: 5px; margin-bottom: 15px; color: white; font-weight: bold;
    }
    
    .lista-itens { list-style-type: none; padding-left: 0; }
    .lista-itens li { padding: 10px 0; border-bottom: 1px dashed #e0e0e0; display: flex; justify-content: space-between; }
    .item-detalhe { color: #333; font-weight: 700; background-color: #fcfcfc; padding: 2px 8px; border-radius: 4px; }

    /* Tooltip original */
    .tooltip { position: relative; display: inline-block; cursor: help; border-bottom: 1px dotted #ff6600; font-weight: 600; }
    .tooltip .tooltiptext {
        visibility: hidden; width: 280px; background-color: #262730; color: #fff;
        border-radius: 8px; padding: 12px; position: absolute; z-index: 10; bottom: 135%; left: 50%;
        margin-left: -140px; opacity: 0; transition: opacity 0.3s; font-size: 0.85rem;
    }
    .tooltip:hover .tooltiptext { visibility: visible; opacity: 1; }
    </style>
    """, unsafe_allow_html=True)

# 3. Dados de Tabela (Fonte única de verdade)
precos_tabela = {
    "VR ERP PRO": {"setup": 2415.60, "mensal": 1285.71},
    "VR PDV Convencional": {"setup": 201.30, "mensal": 185.71},
    "PDV Touchscreen": {"setup": 201.30, "mensal": 185.71},
    "PDV Selfcheckout": {"setup": 500.00, "mensal": 290.44},
    "SiTef Express": {"setup": 0.00, "mensal": 357.14},
    "VR TEF": {"setup": 0.00, "mensal": 417.04},
    "Gerenciador XML": {"setup": 0.00, "mensal": 163.84},
    "VR Mobile": {"setup": 201.30, "mensal": 193.63},
    "Migração Banco de Dados": {"setup": 201.30, "mensal": 0.00},
    "Definição de Escopo": {"setup": 201.30, "mensal": 0.00},
    "Configuração Servidor / PDV Linux": {"setup": 201.30, "mensal": 0.00}
}

# --- 4. BARRA LATERAL (NAVEGAÇÃO) ---
with st.sidebar:
    st.title("SISTEMA VR")
    # Alternador de Telas
    tela_selecionada = st.radio("Selecione o Modo:", ["Gerador de Proposta", "Consulta de Preços"])
    st.write("---")

    if tela_selecionada == "Gerador de Proposta":
        st.markdown('<span class="sidebar-label">Perfil da Venda</span>', unsafe_allow_html=True)
        perfil_venda = st.selectbox("Perfil", ["Executivo (Rua)", "CS (Base)"])
        modo_apresentacao = st.toggle("Modo Apresentação")
        
        st.markdown('<span class="sidebar-label">Negociação</span>', unsafe_allow_html=True)
        desc = st.number_input("Desconto Mensal (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.1)
        if desc > 15.0:
            st.warning("Desconto não autorizado. Necessária aprovação financeira.")
        
        exibir_detalhe_desc = st.toggle("Exibir detalhamento de desconto", value=True)
        faturamento = st.selectbox("Faturamento", ["Imediato", "30 dias", "60 dias", "Apos a implantacao"])
        parcelas = st.selectbox("Parcelas Setup", [1, 2, 3, 4, 5, 6], index=3)

# --- 5. TELA DE CONSULTA DE PREÇOS ---
if tela_selecionada == "Consulta de Preços":
    st.markdown('<h1 class="hero-title">CONSULTA DE TABELA</h1>', unsafe_allow_html=True)
    st.write("Visualize rapidamente o valor de prateleira dos produtos.")
    
    produto_busca = st.selectbox("Pesquisar Produto ou Serviço:", list(precos_tabela.keys()))
    
    dados = precos_tabela[produto_busca]
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown(f"""
            <div class="resumo-card">
                <span class="resumo-label">Tabela Setup (Unitário)</span>
                <div class="resumo-valor">R$ {dados['setup']:,.2f}</div>
                <div class="resumo-subtitulo">INVESTIMENTO INICIAL</div>
                <p>Valor por hora ou licença inicial conforme política comercial vigente.</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col_c2:
        st.markdown(f"""
            <div class="resumo-card" style="border-top-color: #2e7d32;">
                <span class="resumo-label">Tabela Mensal (Unitário)</span>
                <div class="resumo-valor" style="color: #2e7d32;">R$ {dados['mensal']:,.2f}</div>
                <div class="resumo-subtitulo">RECORRÊNCIA</div>
                <p>Valor mensal bruto sem aplicação de descontos ou pacotes.</p>
            </div>
        """, unsafe_allow_html=True)

# --- 6. TELA DE GERADOR DE PROPOSTA (Original Validada) ---
else:
    # Cabeçalho
    head_col1, head_col2 = st.columns([1, 4])
    with head_col1:
        if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=220)
        else: st.subheader("VR SOFTWARE")
    with head_col2:
        if not modo_apresentacao: st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)

    st.markdown("---")

    # Inputs (Lógica consolidada)
    col1, col2, col3 = st.columns(3) if perfil_venda == "Executivo (Rua)" else (*st.columns(2), None)
    
    # Processamento Simplificado para o Teste
    with col1:
        st.markdown('<div class="section-header">IMPLANTAÇÃO</div>', unsafe_allow_html=True)
        itens_i = ["Migração Banco de Dados", "Definição de Escopo", "Configuração Servidor / PDV Linux", "Implantação e Treinamento"]
        sel_i = st.multiselect("Serviços", itens_i, default=itens_i)
        t_setup = 0
        lista_i = []
        for i in sel_i:
            v_u = precos_tabela[i]["setup"]
            h = st.number_input(f"Horas: {i}", min_value=0, value=12 if "Treinamento" not in i else 120, key=f"p_h_{i}")
            t_setup += h * v_u
            lista_i.append((i, h, v_u))

    with col2:
        st.markdown('<div class="section-header">MENSALIDADES</div>', unsafe_allow_html=True)
        itens_m = ["VR ERP PRO", "VR PDV Convencional", "PDV Touchscreen", "PDV Selfcheckout", "SiTef Express", "VR TEF", "Gerenciador XML", "VR Mobile"]
        sel_m = st.multiselect("Produtos", itens_m, default=["VR ERP PRO"])
        t_mensal_bruto = 0
        lista_m = []
        for i in sel_m:
            v_u = precos_tabela[i]["mensal"]
            q = st.number_input(f"Qtd: {i}", min_value=0, value=1, key=f"p_q_{i}")
            t_mensal_bruto += q * v_u
            lista_m.append((i, q, v_u))

    # Cálculos Finais
    t_mensal_liq = t_mensal_bruto * (1 - (desc/100))

    # Exibição dos Cards
    st.markdown("<h2 style='text-align: center; font-weight: 800;'>DETALHAMENTO DA PROPOSTA</h2>", unsafe_allow_html=True)
    res_c1, res_c2 = st.columns(2) # Simplificado para o teste visual

    with res_c1:
        html_i = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{h}h x R$ {v:,.2f}</span></li>" for i, h, v in lista_i])
        st.markdown(f"""
            <div class="resumo-card">
                <span class="resumo-label">Setup</span>
                <div class="resumo-valor">R$ {t_setup:,.2f}</div>
                <div style="font-weight:bold;">{parcelas}x R$ {t_setup/parcelas:,.2f}</div>
                <ul class="lista-itens">{html_i}</ul>
            </div>
        """, unsafe_allow_html=True)

    with res_c2:
        html_m = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{q} Lic. x R$ {v:,.2f}</span></li>" for i, q, v in lista_m])
        desc_info = f'<div style="color: #2e7d32; font-weight: bold;">Desconto: {desc:,.2f}%</div>' if exibir_detalhe_desc and desc > 0 else '<div style="height:21px"></div>'
        st.markdown(f"""
            <div class="resumo-card" style="border-top-color: #2e7d32;">
                <span class="resumo-label">Mensalidade</span>
                <div class="resumo-valor" style="color: #2e7d32;">R$ {t_mensal_liq:,.2f}</div>
                {desc_info}
                <div style="font-weight:bold;">Faturamento: {faturamento}</div>
                <ul class="lista-itens">{html_m}</ul>
            </div>
        """, unsafe_allow_html=True)
