import streamlit as st
import pandas as pd
import os

# 1. Configuracao da Pagina
st.set_page_config(page_title="VR Software | Proposta Comercial", layout="wide")

# 2. Estilizacao CSS (Fiel ao Original com Sombreamentos e Cores)
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #ffffff 0%, #fff5ed 100%); }
    .hero-title { color: #262730; font-size: 5.5rem; font-weight: 900; margin: 0; line-height: 1; text-transform: uppercase; letter-spacing: -3px; }
    .sidebar-label { color: #ff6600; font-size: 0.9rem; font-weight: 800; text-transform: uppercase; margin-top: 20px; margin-bottom: 10px; display: block; }
    
    div.stButton > button {
        width: 100%; background: linear-gradient(90deg, #ff6600 0%, #ff944d 100%);
        color: white; border: none; padding: 12px 20px; border-radius: 8px; font-weight: bold;
        box-shadow: 0 4px 15px rgba(255, 102, 0, 0.2);
    }

    .resumo-card {
        background-color: #ffffff; border: 1px solid #f0f0f0; border-top: 8px solid #ff6600;
        padding: 25px; border-radius: 8px; min-height: 480px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.1); 
        display: flex; flex-direction: column;
    }
    
    .resumo-valor { color: #ff6600; font-size: 2.5rem; font-weight: 900; margin-bottom: 5px; }
    .resumo-label { color: #888; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; display: block; }
    .resumo-subtitulo { font-size: 1.1rem; color: #333; font-weight: bold; margin-top: 20px; margin-bottom: 10px; border-bottom: 2px solid #ffefe5; padding-bottom: 5px; }
    
    .lista-itens { list-style-type: none; padding-left: 0; margin-top: 10px; }
    .lista-itens li { padding: 10px 0; border-bottom: 1px dashed #e0e0e0; display: flex; justify-content: space-between; align-items: center; }
    .item-detalhe { color: #333; font-size: 1.05rem; font-weight: 700; background-color: #fcfcfc; padding: 2px 8px; border-radius: 4px; }

    .tooltip { position: relative; display: inline-block; cursor: help; border-bottom: 1px dotted #ff6600; color: #222; font-weight: 600; }
    .tooltip .tooltiptext {
        visibility: hidden; width: 280px; background-color: #262730; color: #fff; text-align: left;
        border-radius: 8px; padding: 12px; position: absolute; z-index: 10; bottom: 135%; left: 50%;
        margin-left: -140px; opacity: 0; transition: opacity 0.3s; font-size: 0.85rem; line-height: 1.4;
    }
    .tooltip:hover .tooltiptext { visibility: visible; opacity: 1; }

    .section-header {
        display: flex; justify-content: space-between; align-items: center;
        background: linear-gradient(90deg, #ff6600 0%, #ff944d 100%);
        padding: 8px 15px; border-radius: 5px; margin-bottom: 15px; margin-top: 20px;
    }
    .section-title { color: #ffffff; font-size: 1.1rem; font-weight: bold; margin: 0; }
    .roi-box { background-color: #e8f5e9; border-left: 5px solid #2e7d32; padding: 15px; margin-top: 15px; border-radius: 4px; font-size: 0.9rem; }
    </style>
    """, unsafe_allow_html=True)

# 3. Base de Dados Centralizada
precos_tabela = {
    "VR ERP PRO": {"setup": 2415.60, "mensal": 1285.71, "desc": "Sistema de gestão completo para supermercados.", "roi": "Redução média de 15% em perdas de estoque."},
    "VR PDV Convencional": {"setup": 201.30, "mensal": 185.71, "desc": "Frente de caixa estável e rápido.", "roi": "Aumento de 20% na velocidade de passagem no caixa."},
    "PDV Touchscreen": {"setup": 201.30, "mensal": 185.71, "desc": "Interface moderna para telas de toque.", "roi": "Facilidade no treinamento de novos operadores."},
    "PDV Selfcheckout": {"setup": 500.00, "mensal": 290.44, "desc": "Autoatendimento para clientes.", "roi": "Redução de custos operacionais com frente de caixa."},
    "SiTef Express": {"setup": 0.00, "mensal": 357.14, "desc": "Integração de pagamentos em nuvem.", "roi": "Segurança total contra fraudes de cartão."},
    "VR TEF": {"setup": 0.00, "mensal": 417.04, "desc": "Transferência Eletrônica de Fundos VR.", "roi": "Conciliação bancária 100% automatizada."},
    "Gerenciador XML": {"setup": 0.00, "mensal": 163.84, "desc": "Gestão automática de notas fiscais.", "roi": "Economia de 5 horas/semana do setor fiscal."},
    "VR Mobile": {"setup": 201.30, "mensal": 193.63, "desc": "Gestão e vendas na palma da mão.", "roi": "Decisões baseadas em dados em tempo real."},
    "Migração Banco de Dados": {"setup": 201.30, "mensal": 0.00, "desc": "Cópia do cadastro do sistema anterior.", "roi": "Segurança na transição de dados."},
    "Definição de Escopo": {"setup": 201.30, "mensal": 0.00, "desc": "Mapeamento dos processos da empresa.", "roi": "Evita retrabalho e custos extras."},
    "Configuração Servidor / PDV Linux": {"setup": 201.30, "mensal": 0.00, "desc": "Preparação do ambiente Linux.", "roi": "Estabilidade e imunidade a vírus."},
    "Implantação e Treinamento": {"setup": 201.30, "mensal": 0.00, "desc": "Capacitação da equipe nos módulos.", "roi": "Equipe operando com máxima eficiência."}
}
itens_desp = {"Alimentação": 49.00, "Hospedagem": 195.00, "Deslocamento (KM)": 2.12}

# --- 4. MENU LATERAL ---
with st.sidebar:
    if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=200)
    tela = st.radio("Navegação:", ["Gerador de Proposta", "Consulta de Preços"])
    st.write("---")

    if tela == "Gerador de Proposta":
        st.markdown('<span class="sidebar-label">Configurações de Venda</span>', unsafe_allow_html=True)
        perfil_venda = st.selectbox("Perfil do Vendedor", ["Executivo (Rua)", "CS (Base)"])
        modo_apresentacao = st.toggle("Modo Apresentação")
        desc = st.number_input("Desconto Mensal (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.1)
        exibir_detalhe_desc = st.toggle("Exibir Desconto nos Cards", value=True)
        faturamento = st.selectbox("Faturamento", ["Imediato", "30 dias", "60 dias", "Apos a implantacao"])
        parcelas = st.selectbox("Parcelamento Setup", [1, 2, 3, 4, 5, 6], index=3)

# --- 5. TELA DE CONSULTA ---
if tela == "Consulta de Preços":
    st.markdown('<h1 class="hero-title">TABELA DE PREÇOS</h1>', unsafe_allow_html=True)
    prod_sel = st.selectbox("Selecione o Produto:", list(precos_tabela.keys()))
    d = precos_tabela[prod_sel]
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="resumo-card"><span class="resumo-label">Setup</span><div class="resumo-valor">R$ {d["setup"]:,.2f}</div><div class="resumo-subtitulo">ROI</div><div class="roi-box">{d["roi"]}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="resumo-card" style="border-top-color: #2e7d32;"><span class="resumo-label">Mensal</span><div class="resumo-valor" style="color: #2e7d32;">R$ {d["mensal"]:,.2f}</div></div>', unsafe_allow_html=True)

# --- 6. TELA DE PROPOSTA ---
else:
    if not modo_apresentacao:
        st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>')

    # INICIALIZAÇÃO DO ESTADO PARA NÃO PERDER DADOS
    if 'sel_i' not in st.session_state: st.session_state.sel_i = ["Migração Banco de Dados", "Definição de Escopo", "Configuração Servidor / PDV Linux", "Implantação e Treinamento"]
    if 'sel_m' not in st.session_state: st.session_state.sel_m = ["VR ERP PRO"]

    # ÁREA DE INPUTS (OCULTA NO MODO APRESENTAÇÃO)
    if not modo_apresentacao:
        st.markdown("---")
        col_i, col_m, col_d = st.columns(3) if perfil_venda == "Executivo (Rua)" else (*st.columns(2), None)
        
        with col_i:
            st.markdown('<div class="section-header"><span class="section-title">IMPLANTAÇÃO</span></div>', unsafe_allow_html=True)
            st.session_state.sel_i = st.multiselect("Serviços", list(precos_tabela.keys())[8:12], default=st.session_state.sel_i)
            for i in st.session_state.sel_i:
                vu = precos_tabela[i]["setup"]
                st.number_input(f"Horas: {i}", min_value=0, value=12 if "Treinamento" not in i else 120, key=f"v_h_{i}")

        with col_m:
            st.markdown('<div class="section-header"><span class="section-title">MENSALIDADES</span></div>', unsafe_allow_html=True)
            st.session_state.sel_m = st.multiselect("Produtos", list(precos_tabela.keys())[0:8], default=st.session_state.sel_m)
            for i in st.session_state.sel_m:
                vu = precos_tabela[i]["mensal"]
                st.number_input(f"Qtd: {i}", min_value=0, value=1, key=f"v_q_{i}")

        if col_d:
            with col_d:
                st.markdown('<div class="section-header"><span class="section-title">DESPESAS</span></div>', unsafe_allow_html=True)
                for i, p in itens_desp.items():
                    st.number_input(f"{i}", min_value=0, value=0, key=f"v_d_{i}")

    # CÁLCULOS (SEMPRE EXECUTADOS, INDEPENDENTE DO MODO)
    t_imp, t_men_bruto, t_desp = 0, 0, 0
    lista_i, lista_m, lista_d = [], [], []

    # Processa Implantação
    for i in st.session_state.sel_i:
        vu = precos_tabela[i]["setup"]
        h = st.session_state.get(f"v_h_{i}", 12 if "Treinamento" not in i else 120)
        t_imp += h * vu
        lista_i.append((i, h, vu))

    # Processa Mensalidades
    for i in st.session_state.sel_m:
        vu = precos_tabela[i]["mensal"]
        q = st.session_state.get(f"v_q_{i}", 1)
        t_men_bruto += q * vu
        lista_m.append((i, q, vu))

    # Processa Despesas
    for i, p in itens_desp.items():
        qd = st.session_state.get(f"v_d_{i}", 0)
        t_desp += qd * p
        if qd > 0: lista_d.append((i, qd, p))

    t_men_liq = t_men_bruto * (1 - (desc/100))

    # EXIBIÇÃO DOS CARDS (SEMPRE VISÍVEIS)
    st.markdown("<h2 style='text-align:center; font-weight:800; margin-top:30px;'>DETALHAMENTO DA PROPOSTA</h2>", unsafe_allow_html=True)
    res_cols = st.columns(3) if perfil_venda == "Executivo (Rua)" else st.columns([1, 2, 2, 1])[1:3]

    with res_cols[0]:
        html_i = "".join([f"<li><span><span class='tooltip'>{i}<span class='tooltiptext'>{precos_tabela[i]['desc']}</span></span></span><span class='item-detalhe'>{h}h x R$ {v:,.2f}</span></li>" for i, h, v in lista_i])
        st.markdown(f'<div class="resumo-card"><span class="resumo-label">Setup</span><div class="resumo-valor">R$ {t_imp:,.2f}</div><div style="font-weight:bold;">{parcelas}x R$ {t_imp/parcelas:,.2f}</div><div class="resumo-subtitulo">SERVIÇOS</div><ul class="lista-itens">{html_i}</ul></div>', unsafe_allow_html=True)

    with res_cols[1]:
        html_m = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{q} Un x R$ {v:,.2f}</span></li>" for i, q, v in lista_m])
        desc_info = f'<div style="color: #2e7d32; font-weight: bold;">Desconto: {desc:,.2f}%</div>' if exibir_detalhe_desc and desc > 0 else '<div style="height:21px"></div>'
        st.markdown(f'<div class="resumo-card" style="border-top-color: #2e7d32;"><span class="resumo-label">Mensalidade</span><div class="resumo-valor" style="color: #2e7d32;">R$ {t_men_liq:,.2f}</div>{desc_info}<div style="font-weight:bold; font-size: 0.9rem; margin-top:5px;">Faturamento: {faturamento}</div><div class="resumo-subtitulo">SISTEMAS</div><ul class="lista-itens">{html_m}</ul></div>', unsafe_allow_html=True)

    if perfil_venda == "Executivo (Rua)":
        with res_cols[2]:
            html_d = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{q} x R$ {v:,.2f}</span></li>" for i, q, v in lista_d])
            st.markdown(f'<div class="resumo-card" style="border-top-color: #1976d2;"><span class="resumo-label">Despesas</span><div class="resumo-valor" style="color: #1976d2;">R$ {t_desp:,.2f}</div><div style="color:#d32f2f; font-weight:bold; font-size:0.85rem;">Faturadas no término da implantação</div><div class="resumo-subtitulo">LOGÍSTICA</div><ul class="lista-itens">{html_d}</ul></div>', unsafe_allow_html=True)
