import streamlit as st
import pandas as pd
import os

# 1. Configuracao da Pagina
st.set_page_config(page_title="VR Software | Sales Intelligence", layout="wide")

# 2. Estilizacao CSS (Focada em estabilidade)
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #ffffff 0%, #fff5ed 100%); }
    .hero-title { color: #262730; font-size: 4rem; font-weight: 900; margin: 0; line-height: 1; text-transform: uppercase; letter-spacing: -2px; }
    .sidebar-label { color: #ff6600; font-size: 0.85rem; font-weight: 800; text-transform: uppercase; margin-top: 15px; display: block; }
    
    .resumo-card {
        background-color: #ffffff; border: 1px solid #f0f0f0; border-top: 8px solid #ff6600;
        padding: 20px; border-radius: 10px; min-height: 480px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    }
    .resumo-valor { color: #ff6600; font-size: 2.2rem; font-weight: 900; }
    .resumo-label { color: #888; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; }
    
    .roi-box { background-color: #262730; color: white; padding: 15px; border-radius: 8px; margin-top: 15px; }
    .roi-linha { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #444; font-size: 0.9rem; }
    
    .section-header { background: linear-gradient(90deg, #ff6600 0%, #ff944d 100%); padding: 8px 12px; border-radius: 4px; margin: 15px 0; }
    .section-title { color: white; font-size: 0.95rem; font-weight: bold; margin: 0; }
    .lista-itens { list-style: none; padding: 0; margin-top: 10px; }
    .lista-itens li { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px dashed #eee; font-size: 0.85rem; }
    </style>
    """, unsafe_allow_html=True)

# 3. Base de Dados (Unificada com ROI VR)
db = {
    "VR ERP PRO": {"setup": 2415.60, "mensal": 1285.71, "cac": 3500.0, "margem": "Alta", "esforco": "Sênior", "desc": "Estratégico para retenção e LTV."},
    "VR PDV Convencional": {"setup": 201.30, "mensal": 185.71, "cac": 500.0, "margem": "Média", "esforco": "Pleno", "desc": "Baixo custo de manutenção."},
    "PDV Selfcheckout": {"setup": 500.00, "mensal": 290.44, "cac": 1200.0, "margem": "Alta", "esforco": "Especialista", "desc": "Tecnologia de alto impacto."},
    "SiTef Express": {"setup": 0.00, "mensal": 357.14, "cac": 150.0, "margem": "Altíssima", "esforco": "Baixo", "desc": "Escalabilidade imediata."},
    "VR TEF": {"setup": 0.00, "mensal": 417.04, "cac": 150.0, "margem": "Altíssima", "esforco": "Baixo", "desc": "Fidelização financeira."},
    "Gerenciador XML": {"setup": 0.00, "mensal": 163.84, "cac": 80.0, "margem": "Alta", "esforco": "Baixo", "desc": "Serviço essencial fiscal."},
    "VR Mobile": {"setup": 201.30, "mensal": 193.63, "cac": 400.0, "margem": "Média", "esforco": "Pleno", "desc": "Aumenta engajamento do cliente."},
    "Migração Banco de Dados": {"setup": 201.30, "mensal": 0.0, "cac": 300.0, "margem": "N/A", "esforco": "Técnico", "desc": "Serviço de entrada."},
    "Definição de Escopo": {"setup": 201.30, "mensal": 0.0, "cac": 100.0, "margem": "N/A", "esforco": "Consultor", "desc": "Mapeamento de processos."},
    "Implantação e Treinamento": {"setup": 201.30, "mensal": 0.0, "cac": 1500.0, "margem": "N/A", "esforco": "Sênior", "desc": "Sucesso da jornada."}
}
despesas_db = {"Alimentação": 49.00, "Hospedagem": 195.00, "Deslocamento (KM)": 2.12}

# --- 4. SIDEBAR ---
with st.sidebar:
    if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=180)
    st.write("---")
    nav = st.radio("Navegação:", ["Gerador de Proposta", "Consulta de Preço"])
    
    if nav == "Gerador de Proposta":
        st.markdown('<span class="sidebar-label">Configurações</span>', unsafe_allow_html=True)
        vendedor = st.selectbox("Perfil", ["Executivo", "CS"])
        modo_apres = st.toggle("Modo Apresentação")
        exibir_detalhe_desc = st.toggle("Exibir detalhe de desconto", value=True)
        
        st.markdown('<span class="sidebar-label">Negociação</span>', unsafe_allow_html=True)
        perc_desc = st.number_input("Desconto Mensal (%)", 0.0, 30.0, 0.0)
        parcelas_setup = st.selectbox("Parcelamento Setup", [1, 2, 3, 4, 5, 6], index=3)
        cond_fat = st.selectbox("Faturamento", ["Imediato", "30 Dias", "Pós Implantação"])

# --- 5. TELA DE CONSULTA DE PREÇO ---
if nav == "Consulta de Preço":
    st.markdown('<h1 class="hero-title">CONSULTA DE PREÇO</h1>', unsafe_allow_html=True)
    sel_prod = st.selectbox("Selecione o Produto:", list(db.keys()))
    item = db[sel_prod]
    
    # Cálculos ROI VR (24 Meses)
    faturamento_24m = (item["mensal"] * 24) + item["setup"]
    breakeven_mes = ((item["cac"] - item["setup"]) / item["mensal"]) if item["mensal"] > 0 else 0

    col1, col2 = st.columns([1.2, 1])
    with col1:
        st.markdown(f"""
            <div class="resumo-card">
                <span class="resumo-label">Setup (Venda)</span>
                <div class="resumo-valor">R$ {item['setup']:,.2f}</div>
                <br>
                <span class="resumo-label">Mensalidade (Venda)</span>
                <div class="resumo-valor" style="color:#2e7d32;">R$ {item['mensal']:,.2f}</div>
                
                <div class="section-header" style="background:#262730;"><span class="section-title">ROI INTERNO VR (24 MESES)</span></div>
                <div class="roi-box">
                    <div class="roi-linha"><span>LTV (Receita Total)</span><b>R$ {faturamento_24m:,.2f}</b></div>
                    <div class="roi-linha"><span>Custo CAC + Impl.</span><b>R$ {item['cac']:,.2f}</b></div>
                    <div class="roi-linha"><span>Ponto de Equilíbrio</span><b>{round(breakeven_mes, 1)} Meses</b></div>
                    <div class="roi-linha" style="border:none;"><span>Margem VR</span><b style="color:#ff6600;">{item['margem']}</b></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.info(f"**Estratégia:** {item['desc']}")
        st.write(f"**Nível de Esforço:** {item['esforco']}")
        st.write("---")
        st.write("Use estas informações para priorizar produtos de alta margem e baixo esforço técnico durante a negociação.")

# --- 6. TELA DE PROPOSTA ---
else:
    if not modo_apres:
        st.markdown('<h1 class="hero-title">GERADOR DE PROPOSTA</h1>', unsafe_allow_html=True)
        st.write("---")

    # Inclusão de itens
    if 'items_i' not in st.session_state: st.session_state.items_i = ["Migração Banco de Dados", "Implantação e Treinamento"]
    if 'items_m' not in st.session_state: st.session_state.items_m = ["VR ERP PRO"]

    if not modo_apres:
        ci, cm, cd = st.columns(3) if vendedor == "Executivo" else (*st.columns(2), None)
        
        with ci:
            st.markdown('<div class="section-header"><span class="section-title">IMPLANTAÇÃO</span></div>', unsafe_allow_html=True)
            st.session_state.items_i = st.multiselect("Serviços", list(db.keys())[7:], default=st.session_state.items_i)
            for i in st.session_state.items_i:
                st.number_input(f"Hrs: {i}", 0, 500, 12, key=f"h_{i}")

        with cm:
            st.markdown('<div class="section-header"><span class="section-title">MENSALIDADES</span></div>', unsafe_allow_html=True)
            st.session_state.items_m = st.multiselect("Produtos", list(db.keys())[0:7], default=st.session_state.items_m)
            for i in st.session_state.items_m:
                st.number_input(f"Qtd: {i}", 0, 100, 1, key=f"q_{i}")

        if cd:
            with cd:
                st.markdown('<div class="section-header"><span class="section-title">DESPESAS</span></div>', unsafe_allow_html=True)
                for d_n, d_v in despesas_db.items():
                    st.number_input(f"{d_n}", 0, 1000, 0, key=f"d_{d_n}")

    # Cálculos Finais
    v_setup, v_mensal_bruto, v_desp = 0, 0, 0
    res_i, res_m, res_d = [], [], []

    for i in st.session_state.items_i:
        val = db[i]["setup"]
        hrs = st.session_state.get(f"h_{i}", 0)
        v_setup += (hrs * val)
        if hrs > 0: res_i.append(f"<li>{i} <b>{hrs}h</b></li>")

    for i in st.session_state.items_m:
        val = db[i]["mensal"]
        qtd = st.session_state.get(f"q_{i}", 0)
        v_mensal_bruto += (qtd * val)
        if qtd > 0: res_m.append(f"<li>{i} <b>{qtd}un</b></li>")

    for d_n, d_v in despesas_db.items():
        qtd = st.session_state.get(f"d_{d_n}", 0)
        v_desp += (qtd * d_v)
        if qtd > 0: res_d.append(f"<li>{d_n} <b>{qtd}</b></li>")

    v_mensal_liq = v_mensal_bruto * (1 - (perc_desc/100))

    # Cards de Proposta Final
    st.markdown("<h2 style='text-align:center; font-weight:800;'>PROPOSTA FINAL</h2>", unsafe_allow_html=True)
    c_res = st.columns(3) if vendedor == "Executivo" else st.columns([1, 2, 2, 1])[1:3]

    with c_res[0]:
        st.markdown(f"""
            <div class="resumo-card">
                <span class="resumo-label">Setup Total</span>
                <div class="resumo-valor">R$ {v_setup:,.2f}</div>
                <div style="font-weight:bold;">{parcelas_setup}x de R$ {v_setup/parcelas_setup:,.2f}</div>
                <ul class="lista-itens">{"".join(res_i)}</ul>
            </div>
        """, unsafe_allow_html=True)

    with c_res[1]:
        desc_html = f"<div style='color:red; font-size:0.8rem;'>Desconto aplicado: {perc_desc}%</div>" if exibir_detalhe_desc and perc_desc > 0 else "<div style='height:19px;'></div>"
        st.markdown(f"""
            <div class="resumo-card" style="border-top-color:#2e7d32;">
                <span class="resumo-label">Mensalidade</span>
                <div class="resumo-valor" style="color:#2e7d32;">R$ {v_mensal_liq:,.2f}</div>
                {desc_html}
                <div style="font-weight:bold;">Fat: {cond_fat}</div>
                <ul class="lista-itens">{"".join(res_m)}</ul>
            </div>
        """, unsafe_allow_html=True)

    if vendedor == "Executivo":
        with c_res[2]:
            st.markdown(f"""
                <div class="resumo-card" style="border-top-color:#1976d2;">
                    <span class="resumo-label">Despesas</span>
                    <div class="resumo-valor" style="color:#1976d2;">R$ {v_desp:,.2f}</div>
                    <ul class="lista-itens">{"".join(res_d)}</ul>
                </div>
            """, unsafe_allow_html=True)
