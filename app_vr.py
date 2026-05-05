import streamlit as st
import pandas as pd
import os

# 1. Configuracao da Pagina
st.set_page_config(page_title="VR Software | Proposta Comercial", layout="wide")

# 2. Estilizacao CSS Unificada
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #ffffff 0%, #fff5ed 100%); }
    .hero-title { color: #262730; font-size: 5.5rem; font-weight: 900; margin: 0; line-height: 1; text-transform: uppercase; letter-spacing: -3px; }
    .sidebar-label { color: #ff6600; font-size: 0.9rem; font-weight: 800; text-transform: uppercase; margin-top: 20px; margin-bottom: 10px; display: block; }
    
    div.stButton > button {
        width: 100%; background: linear-gradient(90deg, #ff6600 0%, #ff944d 100%);
        color: white; border: none; padding: 12px 20px; border-radius: 8px; font-weight: bold;
    }

    .resumo-card {
        background-color: #ffffff; border: 1px solid #f0f0f0; border-top: 8px solid #ff6600;
        padding: 25px; border-radius: 8px; min-height: 450px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.1); 
    }
    
    .resumo-valor { color: #ff6600; font-size: 2.5rem; font-weight: 900; margin-bottom: 5px; }
    .resumo-label { color: #888; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; display: block; }
    .resumo-subtitulo { font-size: 1.1rem; color: #333; font-weight: bold; margin-top: 20px; margin-bottom: 10px; border-bottom: 2px solid #ffefe5; padding-bottom: 5px; }
    
    .lista-itens { list-style-type: none; padding-left: 0; margin-top: 10px; }
    .lista-itens li { padding: 8px 0; border-bottom: 1px dashed #e0e0e0; display: flex; justify-content: space-between; align-items: center; font-size: 0.9rem; }
    .item-detalhe { color: #333; font-weight: 700; background-color: #fcfcfc; padding: 2px 8px; border-radius: 4px; }

    .roi-interno-box {
        background-color: #f8f9fa; border-left: 5px solid #262730;
        padding: 15px; margin-top: 10px; border-radius: 4px;
    }
    .roi-metrica { display: flex; justify-content: space-between; margin-bottom: 6px; border-bottom: 1px solid #eee; padding-bottom: 2px; }
    .roi-label { font-weight: bold; color: #555; font-size: 0.85rem; }
    .roi-num { font-weight: 800; color: #262730; font-size: 0.85rem; }

    .section-header {
        background: linear-gradient(90deg, #ff6600 0%, #ff944d 100%);
        padding: 8px 15px; border-radius: 5px; margin-bottom: 15px;
    }
    .section-title { color: #ffffff; font-size: 1.1rem; font-weight: bold; margin: 0; }
    </style>
    """, unsafe_allow_html=True)

# 3. Base de Dados Unificada (Preços + Métricas VR)
precos_tabela = {
    "VR ERP PRO": {"setup": 2415.60, "mensal": 1285.71, "cac": 3000.0, "margem": "Alta", "desc": "Sistema de gestão completo."},
    "VR PDV Convencional": {"setup": 201.30, "mensal": 185.71, "cac": 400.0, "margem": "Média", "desc": "Frente de caixa estável."},
    "PDV Touchscreen": {"setup": 201.30, "mensal": 185.71, "cac": 400.0, "margem": "Média", "desc": "Interface touch moderna."},
    "PDV Selfcheckout": {"setup": 500.00, "mensal": 290.44, "cac": 800.0, "margem": "Alta", "desc": "Autoatendimento."},
    "SiTef Express": {"setup": 0.00, "mensal": 357.14, "cac": 100.0, "margem": "Altíssima", "desc": "Pagamentos em nuvem."},
    "VR TEF": {"setup": 0.00, "mensal": 417.04, "cac": 150.0, "margem": "Altíssima", "desc": "TEF proprietário VR."},
    "Gerenciador XML": {"setup": 0.00, "mensal": 163.84, "cac": 50.0, "margem": "Alta", "desc": "Gestão de notas fiscais."},
    "VR Mobile": {"setup": 201.30, "mensal": 193.63, "cac": 300.0, "margem": "Média", "desc": "Gestão mobile."},
    "Migração Banco de Dados": {"setup": 201.30, "mensal": 0.00, "cac": 200.0, "margem": "Baixa", "desc": "Cópia de cadastros."},
    "Definição de Escopo": {"setup": 201.30, "mensal": 0.00, "cac": 100.0, "margem": "Média", "desc": "Mapeamento de processos."},
    "Configuração Servidor / PDV Linux": {"setup": 201.30, "mensal": 0.00, "cac": 150.0, "margem": "Média", "desc": "Ambiente Linux."},
    "Implantação e Treinamento": {"setup": 201.30, "mensal": 0.00, "cac": 1000.0, "margem": "Baixa", "desc": "Capacitação equipe."}
}
itens_desp = {"Alimentação": 49.00, "Hospedagem": 195.00, "Deslocamento (KM)": 2.12}

# --- 4. MENU LATERAL ---
with st.sidebar:
    if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=200)
    tela = st.radio("Navegação:", ["Gerador de Proposta", "Consulta de Preços"])
    st.write("---")
    
    if tela == "Gerador de Proposta":
        st.markdown('<span class="sidebar-label">Configurações</span>', unsafe_allow_html=True)
        perfil_venda = st.selectbox("Perfil", ["Executivo (Rua)", "CS (Base)"])
        modo_apresentacao = st.toggle("Modo Apresentação")
        desc_input = st.number_input("Desconto Mensal (%)", min_value=0.0, max_value=30.0, value=0.0)
        faturamento_op = st.selectbox("Faturamento", ["Imediato", "30 dias", "Apos a implantacao"])
        parcelas_op = st.selectbox("Parcelamento Setup", [1, 2, 3, 4, 5, 6], index=3)

# --- 5. TELA DE CONSULTA ---
if tela == "Consulta de Preços":
    st.markdown('<h1 class="hero-title">ANÁLISE DE PRODUTO</h1>', unsafe_allow_html=True)
    prod_sel = st.selectbox("Selecione o Produto:", list(precos_tabela.keys()))
    d = precos_tabela[prod_sel]
    
    # Calculos ROI Interno VR
    receita_24m = (d["mensal"] * 24) + d["setup"]
    payback = ((d["cac"] - d["setup"]) / d["mensal"]) if d["mensal"] > 0 else 0

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'''
            <div class="resumo-card">
                <span class="resumo-label">Setup de Venda</span>
                <div class="resumo-valor">R$ {d["setup"]:,.2f}</div>
                <span class="resumo-label">Mensalidade de Venda</span>
                <div class="resumo-valor" style="color:#2e7d32;">R$ {d["mensal"]:,.2f}</div>
                <div class="resumo-subtitulo">ROI INTERNO VR (24 MESES)</div>
                <div class="roi-interno-box">
                    <div class="roi-metrica"><span class="roi-label">LTV Bruto</span><span class="roi-num">R$ {receita_24m:,.2f}</span></div>
                    <div class="roi-metrica"><span class="roi-label">Breakeven</span><span class="roi-num">{round(payback, 1)} meses</span></div>
                    <div class="roi-metrica"><span class="roi-label">Margem VR</span><span class="roi-num">{d["margem"]}</span></div>
                </div>
            </div>
        ''', unsafe_allow_html=True)
    with c2:
        st.info(f"**Descrição:** {d['desc']}")
        st.write("---")
        st.markdown("**Nota Estratégica:** Este produto contribui para a retenção do cliente no ecossistema VR, garantindo recorrência estável.")

# --- 6. TELA DE PROPOSTA (RESTAURADA) ---
else:
    if not modo_apresentacao:
        st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)
        st.write("---")

    # Persistencia de selecao
    if 'sel_i' not in st.session_state: st.session_state.sel_i = ["Migração Banco de Dados", "Implantação e Treinamento"]
    if 'sel_m' not in st.session_state: st.session_state.sel_m = ["VR ERP PRO"]

    if not modo_apresentacao:
        col_i, col_m, col_d = st.columns(3) if perfil_venda == "Executivo (Rua)" else (*st.columns(2), None)
        
        with col_i:
            st.markdown('<div class="section-header"><span class="section-title">IMPLANTAÇÃO</span></div>', unsafe_allow_html=True)
            st.session_state.sel_i = st.multiselect("Serviços", list(precos_tabela.keys())[8:12], default=st.session_state.sel_i)
            for i in st.session_state.sel_i:
                st.number_input(f"{i} (R$ {precos_tabela[i]['setup']:,.2f}/h)", min_value=0, value=12 if "Treinamento" not in i else 100, key=f"h_{i}")

        with col_m:
            st.markdown('<div class="section-header"><span class="section-title">MENSALIDADES</span></div>', unsafe_allow_html=True)
            st.session_state.sel_m = st.multiselect("Produtos", list(precos_tabela.keys())[0:8], default=st.session_state.sel_m)
            for i in st.session_state.sel_m:
                st.number_input(f"{i} (R$ {precos_tabela[i]['mensal']:,.2f}/un)", min_value=0, value=1, key=f"q_{i}")

        if col_d:
            with col_d:
                st.markdown('<div class="section-header"><span class="section-title">DESPESAS</span></div>', unsafe_allow_html=True)
                for i, p in itens_desp.items():
                    st.number_input(f"{i} (R$ {p:,.2f})", min_value=0, value=0, key=f"d_{i}")

    # Processamento de Totais
    t_imp, t_men_bruto, t_desp = 0, 0, 0
    l_i, l_m, l_d = [], [], []

    for i in st.session_state.sel_i:
        vu = precos_tabela[i]["setup"]
        h = st.session_state.get(f"h_{i}", 0)
        t_imp += h * vu
        if h > 0: l_i.append((i, h, vu))

    for i in st.session_state.sel_m:
        vu = precos_tabela[i]["mensal"]
        q = st.session_state.get(f"q_{i}", 0)
        t_men_bruto += q * vu
        if q > 0: l_m.append((i, q, vu))

    for i, p in itens_desp.items():
        qd = st.session_state.get(f"d_{i}", 0)
        t_desp += qd * p
        if qd > 0: l_d.append((i, qd, p))

    t_men_liq = t_men_bruto * (1 - (desc_input/100))

    # Renderizacao do Resumo
    st.markdown("<h2 style='text-align:center; font-weight:800; margin-top:30px;'>DETALHAMENTO DA PROPOSTA</h2>", unsafe_allow_html=True)
    res_cols = st.columns(3) if perfil_venda == "Executivo (Rua)" else st.columns([1, 2, 2, 1])[1:3]

    with res_cols[0]:
        html_i = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{h}h x R$ {v:,.2f}</span></li>" for i, h, v in l_i])
        st.markdown(f'<div class="resumo-card"><span class="resumo-label">Setup</span><div class="resumo-valor">R$ {t_imp:,.2f}</div><div style="font-weight:bold;">{parcelas_op}x R$ {t_imp/parcelas_op:,.2f}</div><div class="resumo-subtitulo">SERVIÇOS</div><ul class="lista-itens">{html_i}</ul></div>', unsafe_allow_html=True)

    with res_cols[1]:
        html_m = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{q}un x R$ {v:,.2f}</span></li>" for i, q, v in l_m])
        st.markdown(f'<div class="resumo-card" style="border-top-color: #2e7d32;"><span class="resumo-label">Mensalidade</span><div class="resumo-valor" style="color: #2e7d32;">R$ {t_men_liq:,.2f}</div><div style="font-weight:bold;">Faturamento: {faturamento_op}</div><div class="resumo-subtitulo">SISTEMAS</div><ul class="lista-itens">{html_m}</ul></div>', unsafe_allow_html=True)

    if perfil_venda == "Executivo (Rua)":
        with res_cols[2]:
            html_d = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{q} x R$ {v:,.2f}</span></li>" for i, q, v in l_d])
            st.markdown(f'<div class="resumo-card" style="border-top-color: #1976d2;"><span class="resumo-label">Despesas</span><div class="resumo-valor" style="color: #1976d2;">R$ {t_desp:,.2f}</div><div class="resumo-subtitulo">LOGÍSTICA</div><ul class="lista-itens">{html_d}</ul></div>', unsafe_allow_html=True)
