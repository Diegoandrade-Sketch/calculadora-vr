import streamlit as st
import pandas as pd
import os
import textwrap

# 1. Configuracao da Pagina
st.set_page_config(page_title="VR Software | Sales Intelligence", layout="wide")

# 2. Estilizacao CSS
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #ffffff 0%, #fff5ed 100%); }
    .hero-title { color: #262730; font-size: 5.5rem; font-weight: 900; margin: 0; line-height: 1; text-transform: uppercase; letter-spacing: -3px; }
    .sidebar-label { color: #ff6600; font-size: 0.9rem; font-weight: 800; text-transform: uppercase; margin-top: 20px; margin-bottom: 10px; display: block; }
    
    .resumo-card {
        background-color: #ffffff; border: 1px solid #f0f0f0; border-top: 8px solid #ff6600;
        padding: 25px; border-radius: 8px; min-height: 480px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.1); 
        display: flex; flex-direction: column;
    }
    
    .resumo-valor { color: #ff6600; font-size: 2.5rem; font-weight: 900; margin-bottom: 5px; }
    .resumo-label { color: #888; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; display: block; }
    .resumo-subtitulo { font-size: 1.1rem; color: #333; font-weight: bold; margin-top: 20px; margin-bottom: 10px; border-bottom: 2px solid #ffefe5; padding-bottom: 5px; }
    
    .roi-interno-box {
        background-color: #f8f9fa; border-left: 5px solid #262730;
        padding: 15px; margin-top: 10px; border-radius: 4px;
    }
    .roi-metrica { display: flex; justify-content: space-between; margin-bottom: 8px; border-bottom: 1px solid #eee; padding-bottom: 4px; }
    .roi-label-int { font-weight: bold; color: #555; font-size: 0.85rem; }
    .roi-num-int { font-weight: 800; color: #262730; font-size: 0.85rem; }

    .lista-itens { list-style-type: none; padding-left: 0; margin-top: 10px; }
    .lista-itens li { padding: 10px 0; border-bottom: 1px dashed #e0e0e0; display: flex; justify-content: space-between; align-items: center; }
    .item-detalhe { color: #333; font-size: 1.05rem; font-weight: 700; background-color: #fcfcfc; padding: 2px 8px; border-radius: 4px; }

    .section-header {
        background: linear-gradient(90deg, #ff6600 0%, #ff944d 100%);
        padding: 8px 15px; border-radius: 5px; margin-bottom: 15px; margin-top: 20px;
    }
    .section-title { color: #ffffff; font-size: 1.1rem; font-weight: bold; margin: 0; }
    
    .tooltip { position: relative; display: inline-block; cursor: help; border-bottom: 1px dotted #ff6600; color: #222; font-weight: 600; }
    .tooltip .tooltiptext {
        visibility: hidden; width: 280px; background-color: #262730; color: #fff; text-align: left;
        border-radius: 8px; padding: 12px; position: absolute; z-index: 10; bottom: 135%; left: 50%;
        margin-left: -140px; opacity: 0; transition: opacity 0.3s; font-size: 0.85rem; line-height: 1.4;
    }
    .tooltip:hover .tooltiptext { visibility: visible; opacity: 1; }
    </style>
    """, unsafe_allow_html=True)

# 3. Base de Dados
precos_tabela = {
    "VR ERP PRO": {"setup": 2415.60, "mensal": 1285.71, "cac": 3000.00, "margem": "Alta", "comp": "Alta", "desc": "Sistema de gestão completo para supermercados.", "roi": "Redução média de 15% em perdas de estoque."},
    "VR PDV Convencional": {"setup": 201.30, "mensal": 185.71, "cac": 400.00, "margem": "Média", "comp": "Média", "desc": "Frente de caixa estável e rápido.", "roi": "Aumento de 20% na velocidade de passagem no caixa."},
    "PDV Touchscreen": {"setup": 201.30, "mensal": 185.71, "cac": 400.00, "margem": "Média", "comp": "Média", "desc": "Interface moderna para telas de toque.", "roi": "Facilidade no treinamento de novos operadores."},
    "PDV Selfcheckout": {"setup": 500.00, "mensal": 290.44, "cac": 800.00, "margem": "Alta", "comp": "Alta", "desc": "Autoatendimento para clientes.", "roi": "Redução de custos operacionais."},
    "SiTef Express": {"setup": 0.00, "mensal": 357.14, "cac": 100.00, "margem": "Altíssima", "comp": "Baixa", "desc": "Integração de pagamentos em nuvem.", "roi": "Segurança total contra fraudes."},
    "VR TEF": {"setup": 0.00, "mensal": 417.04, "cac": 150.00, "margem": "Altíssima", "comp": "Baixa", "desc": "Transferência Eletrônica de Fundos VR.", "roi": "Conciliação bancária automatizada."},
    "Gerenciador XML": {"setup": 0.00, "mensal": 163.84, "cac": 50.00, "margem": "Alta", "comp": "Baixa", "desc": "Gestão automática de notas fiscais.", "roi": "Economia de tempo no setor fiscal."},
    "VR Mobile": {"setup": 201.30, "mensal": 193.63, "cac": 300.00, "margem": "Média", "comp": "Média", "desc": "Gestão na palma da mão.", "roi": "Decisões baseadas em dados reais."},
    "Migração Banco de Dados": {"setup": 201.30, "mensal": 0.00, "cac": 200.00, "margem": "Baixa", "comp": "Alta", "desc": "Cópia do cadastro anterior.", "roi": "Segurança na transição."},
    "Definição de Escopo": {"setup": 201.30, "mensal": 0.00, "cac": 100.00, "margem": "Média", "comp": "Média", "desc": "Mapeamento de processos.", "roi": "Evita surpresas no projeto."},
    "Configuração Servidor / PDV Linux": {"setup": 201.30, "mensal": 0.00, "cac": 150.00, "margem": "Média", "comp": "Média", "desc": "Ambiente Linux estável.", "roi": "Imunidade a vírus."},
    "Implantação e Treinamento": {"setup": 201.30, "mensal": 0.00, "cac": 1000.00, "margem": "Baixa", "comp": "Alta", "desc": "Capacitação da equipe.", "roi": "Equipe 100% produtiva."}
}
itens_desp = {"Alimentação": 49.00, "Hospedagem": 195.00, "Deslocamento (KM)": 2.12}

# --- 4. INICIALIZAÇÃO DE ESTADO (CRÍTICO) ---
# Inicializamos tudo aqui no topo para que nenhum widget tente resetar os valores
if 'sel_i' not in st.session_state: st.session_state.sel_i = ["Migração Banco de Dados", "Definição de Escopo", "Configuração Servidor / PDV Linux", "Implantação e Treinamento"]
if 'sel_m' not in st.session_state: st.session_state.sel_m = ["VR ERP PRO"]

# Inicializa valores de despesas e quantidades se não existirem
for i in list(precos_tabela.keys()):
    if f"v_h_{i}" not in st.session_state:
        st.session_state[f"v_h_{i}"] = 120 if "Treinamento" in i else 12
    if f"v_q_{i}" not in st.session_state:
        st.session_state[f"v_q_{i}"] = 1

for i in itens_desp.keys():
    if f"v_d_{i}" not in st.session_state:
        st.session_state[f"v_d_{i}"] = 0

# --- 5. MENU LATERAL ---
with st.sidebar:
    if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=200)
    tela = st.radio("Navegação:", ["Gerador de Proposta", "Consulta de Preço"])
    st.write("---")

    if tela == "Gerador de Proposta":
        st.markdown('<span class="sidebar-label">Configurações</span>', unsafe_allow_html=True)
        perfil_venda = st.selectbox("Perfil", ["Executivo (Rua)", "CS (Base)"])
        modo_apresentacao = st.toggle("Modo Apresentação")
        desc = st.number_input("Desconto Mensal (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.1)
        exibir_detalhe_desc = st.toggle("Exibir Desconto", value=True)
        faturamento = st.selectbox("Faturamento", ["Imediato", "30 dias", "60 dias", "Após a implantação"])
        parcelas = st.selectbox("Parcelamento Setup", [1, 2, 3, 4, 5, 6], index=3)

# --- TELA DE CONSULTA (Sem alterações) ---
if tela == "Consulta de Preço":
    st.markdown('<h1 class="hero-title">ANÁLISE TÉCNICA</h1>', unsafe_allow_html=True)
    prod_sel = st.selectbox("Selecione o Produto:", list(precos_tabela.keys()))
    d = precos_tabela[prod_sel]
    ltv_24 = (d["mensal"] * 24) + d["setup"]
    payback = ((d["cac"] - d["setup"]) / d["mensal"]) if d["mensal"] > 0 else 0
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""<div class="resumo-card"><span class="resumo-label">Preço</span><div class="resumo-valor">R$ {d['mensal']:,.2f}</div><div class="section-header"><span class="section-title">ROI ESTRATÉGICO</span></div><div class="roi-interno-box"><div class="roi-metrica"><span class="roi-label-int">LTV</span><span class="roi-num-int">R$ {ltv_24:,.2f}</span></div><div class="roi-metrica"><span class="roi-label-int">Payback</span><span class="roi-num-int">{round(payback, 1)} meses</span></div></div></div>""", unsafe_allow_html=True)
    with c2:
        st.info(f"**{prod_sel}**: {d['desc']}")

# --- 6. TELA DE PROPOSTA CORRIGIDA ---
else:
    if not modo_apresentacao:
        st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)
        st.markdown("---")
        
        col_i, col_m, col_d = st.columns(3) if perfil_venda == "Executivo (Rua)" else (*st.columns(2), None)
        
        with col_i:
            st.markdown('<div class="section-header"><span class="section-title">IMPLANTAÇÃO</span></div>', unsafe_allow_html=True)
            st.session_state.sel_i = st.multiselect("Serviços", list(precos_tabela.keys())[8:12], default=st.session_state.sel_i)
            for i in st.session_state.sel_i:
                # Usamos key fixa e não passamos 'value' para deixar o Streamlit gerenciar o estado inicializado no topo
                st.number_input(f"Horas: {i}", min_value=0, key=f"v_h_{i}")

        with col_m:
            st.markdown('<div class="section-header"><span class="section-title">MENSALIDADES</span></div>', unsafe_allow_html=True)
            st.session_state.sel_m = st.multiselect("Produtos", list(precos_tabela.keys())[0:8], default=st.session_state.sel_m)
            for i in st.session_state.sel_m:
                st.number_input(f"Qtd: {i}", min_value=0, key=f"v_q_{i}")

        if col_d:
            with col_d:
                st.markdown('<div class="section-header"><span class="section-title">DESPESAS</span></div>', unsafe_allow_html=True)
                for i, p in itens_desp.items():
                    # Esta é a chave para não zerar: o widget está vinculado à chave que já existe no session_state
                    st.number_input(f"{i} (R$ {p:,.2f})", min_value=0, key=f"v_d_{i}")

    # --- CÁLCULOS FINAIS ---
    t_imp, t_men_bruto, t_desp = 0, 0, 0
    lista_i, lista_m, lista_d = [], [], []

    # Cálculo Implantação
    for i in st.session_state.sel_i:
        vu = precos_tabela[i]["setup"]
        h = st.session_state.get(f"v_h_{i}", 0)
        t_imp += h * vu
        lista_i.append((i, h, vu))

    # Cálculo Mensalidade
    for i in st.session_state.sel_m:
        vu = precos_tabela[i]["mensal"]
        q = st.session_state.get(f"v_q_{i}", 0)
        t_men_bruto += q * vu
        lista_m.append((i, q, vu))

    # Cálculo Despesas
    for i, p in itens_desp.items():
        qd = st.session_state.get(f"v_d_{i}", 0)
        if qd > 0:
            t_desp += qd * p
            lista_d.append((i, qd, p))

    t_men_liq = t_men_bruto * (1 - (desc/100))

    # --- EXIBIÇÃO DOS CARDS ---
    st.markdown("<h2 style='text-align:center; font-weight:800; margin-top:30px;'>DETALHAMENTO DA PROPOSTA</h2>", unsafe_allow_html=True)
    res_cols = st.columns(3) if perfil_venda == "Executivo (Rua)" else st.columns([1, 2, 2, 1])[1:3]

    with res_cols[0]:
        html_i = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{h}h x R$ {v:,.2f}</span></li>" for i, h, v in lista_i])
        st.markdown(f'<div class="resumo-card"><span class="resumo-label">Setup</span><div class="resumo-valor">R$ {t_imp:,.2f}</div><div style="font-weight:bold;">{parcelas}x R$ {t_imp/parcelas:,.2f}</div><div class="resumo-subtitulo">SERVIÇOS</div><ul class="lista-itens">{html_i}</ul></div>', unsafe_allow_html=True)

    with res_cols[1]:
        html_m = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{q} Un x R$ {v:,.2f}</span></li>" for i, q, v in lista_m])
        desc_info = f'<div style="color: #2e7d32; font-weight: bold;">Desconto Aplicado: {desc:,.2f}%</div>' if exibir_detalhe_desc and desc > 0 else '<div style="height:21px"></div>'
        st.markdown(f'<div class="resumo-card" style="border-top-color: #2e7d32;"><span class="resumo-label">Mensalidade</span><div class="resumo-valor" style="color: #2e7d32;">R$ {t_men_liq:,.2f}</div>{desc_info}<div style="font-weight:bold; font-size: 0.9rem; margin-top:5px;">Faturamento: {faturamento}</div><div class="resumo-subtitulo">SISTEMAS</div><ul class="lista-itens">{html_m}</ul></div>', unsafe_allow_html=True)

    if perfil_venda == "Executivo (Rua)":
        with res_cols[2]:
            html_d = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{q} x R$ {v:,.2f}</span></li>" for i, q, v in lista_d])
            st.markdown(f'<div class="resumo-card" style="border-top-color: #1976d2;"><span class="resumo-label">Despesas</span><div class="resumo-valor" style="color: #1976d2;">R$ {t_desp:,.2f}</div><div style="color:#d32f2f; font-weight:bold; font-size:0.85rem;">Logística e Deslocamento</div><div class="resumo-subtitulo">DETALHES</div><ul class="lista-itens">{html_d}</ul></div>', unsafe_allow_html=True)
