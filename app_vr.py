import streamlit as st
import pandas as pd
import os

# 1. Configuracao da Pagina
st.set_page_config(page_title="VR Software | Sales Intelligence", layout="wide")

# 2. Estilizacao CSS Avancada
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #ffffff 0%, #fff5ed 100%); }
    .hero-title { color: #262730; font-size: 4.5rem; font-weight: 900; margin: 0; line-height: 1; text-transform: uppercase; letter-spacing: -2px; }
    .sidebar-label { color: #ff6600; font-size: 0.85rem; font-weight: 800; text-transform: uppercase; margin-top: 15px; margin-bottom: 5px; display: block; }
    
    /* Card Design */
    .resumo-card {
        background-color: #ffffff; border: 1px solid #f0f0f0; border-top: 8px solid #ff6600;
        padding: 20px; border-radius: 12px; min-height: 500px; 
        box-shadow: 0 12px 30px rgba(0,0,0,0.08); display: flex; flex-direction: column;
    }
    .resumo-valor { color: #ff6600; font-size: 2.2rem; font-weight: 900; line-height: 1; }
    .resumo-label { color: #888; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; }
    
    /* ROI Interno Styling */
    .roi-container { background-color: #262730; color: white; padding: 20px; border-radius: 8px; margin-top: 15px; }
    .roi-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #444; }
    .roi-tag { font-size: 0.75rem; font-weight: 800; padding: 2px 8px; border-radius: 4px; text-transform: uppercase; }
    
    /* Utils */
    .section-header { background: linear-gradient(90deg, #ff6600 0%, #ff944d 100%); padding: 10px 15px; border-radius: 6px; margin-bottom: 15px; }
    .section-title { color: white; font-size: 1rem; font-weight: bold; margin: 0; }
    .lista-itens { list-style: none; padding: 0; margin: 15px 0; }
    .lista-itens li { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px dashed #eee; font-size: 0.9rem; }
    .badge-valor { background: #f8f9fa; padding: 2px 6px; border-radius: 4px; font-weight: bold; color: #333; }
    </style>
    """, unsafe_allow_html=True)

# 3. Base de Dados Estrategica (VR Software)
# Custos baseados em operacao real: suporte, infra e implementacao
db = {
    "VR ERP PRO": {
        "setup": 2415.60, "mensal": 1285.71, "cac": 3500.0, "margem": "Alta", 
        "esforco": "Senior", "upsell": "Módulos Fiscais e Mobile", 
        "desc": "Coração do ecossistema. Garante a retenção de longo prazo."
    },
    "VR PDV Convencional": {
        "setup": 201.30, "mensal": 185.71, "cac": 500.0, "margem": "Média", 
        "esforco": "Pleno", "upsell": "TEF e Selfcheckout", 
        "desc": "Estabilidade de frente de loja. Baixo churn técnico."
    },
    "PDV Selfcheckout": {
        "setup": 500.00, "mensal": 290.44, "cac": 1200.0, "margem": "Alta", 
        "esforco": "Especialista", "upsell": "Monitoramento Remoto", 
        "desc": "Tecnologia de ponta. Eleva o posicionamento de marca da VR."
    },
    "SiTef Express": {
        "setup": 0.00, "mensal": 357.14, "cac": 150.0, "margem": "Altíssima", 
        "esforco": "Baixo", "upsell": "Conciliação Bancária", 
        "desc": "Alta escalabilidade. Lucro líquido imediato."
    },
    "VR TEF": {
        "setup": 0.00, "mensal": 417.04, "cac": 150.0, "margem": "Altíssima", 
        "esforco": "Baixo", "upsell": "VR ERP", 
        "desc": "Fidelização financeira. Dificulta a troca de software."
    },
    "Gerenciador XML": {
        "setup": 0.00, "mensal": 163.84, "cac": 80.0, "margem": "Altíssima", 
        "esforco": "Baixo", "upsell": "Módulo Contábil", 
        "desc": "Essencial para o setor fiscal. Produto 'ganha tempo'."
    },
    "VR Mobile": {
        "setup": 201.30, "mensal": 193.63, "cac": 400.0, "margem": "Média", 
        "esforco": "Pleno", "upsell": "BI Dashboard", 
        "desc": "Ferramenta de decisão. Aumenta o uso diário do sistema."
    },
    "Migração Banco de Dados": {"setup": 201.30, "mensal": 0.0, "cac": 300.0, "margem": "Baixa", "esforco": "Técnico", "upsell": "N/A", "desc": "Custo de entrada necessário."},
    "Definição de Escopo": {"setup": 201.30, "mensal": 0.0, "cac": 100.0, "margem": "Média", "esforco": "Consultor", "upsell": "N/A", "desc": "Garante sucesso do projeto."},
    "Implantação e Treinamento": {"setup": 201.30, "mensal": 0.0, "cac": 1500.0, "margem": "Baixa", "esforco": "Sênior", "upsell": "N/A", "desc": "Momento crítico da jornada."}
}
despesas_db = {"Alimentação": 49.00, "Hospedagem": 195.00, "Deslocamento (KM)": 2.12}

# --- 4. SIDEBAR ---
with st.sidebar:
    if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=180)
    st.write("---")
    nav = st.radio("Módulo de Trabalho:", ["Gerador de Proposta", "Consulta Estratégica"])
    
    if nav == "Gerador de Proposta":
        st.markdown('<span class="sidebar-label">Regras de Negócio</span>', unsafe_allow_html=True)
        vendedor_perfil = st.selectbox("Perfil de Venda", ["Rua (Executivo)", "Base (CS)"])
        apresentacao = st.toggle("Modo Apresentação")
        exibir_desc = st.toggle("Exibir Detalhe de Desconto", value=True)
        
        st.markdown('<span class="sidebar-label">Financeiro</span>', unsafe_allow_html=True)
        desconto_perc = st.number_input("Desconto Mensal (%)", 0.0, 30.0, 0.0)
        parcelas = st.slider("Parcelamento Setup", 1, 6, 4)
        faturamento = st.selectbox("Condição Faturamento", ["Imediato", "30 Dias", "Pós Implantação"])

# --- 5. TELA DE CONSULTA ESTRATÉGICA (RICA EM DETALHES) ---
if nav == "Consulta Estratégica":
    st.markdown('<h1 class="hero-title">ANÁLISE DE PRODUTO</h1>', unsafe_allow_html=True)
    st.write("Visão Interna VR Software: LTV, ROI e Estratégia de Contrato (24 Meses).")
    
    prod = st.selectbox("Selecione o Produto para Diagnóstico:", list(db.keys()))
    info = db[prod]
    
    # Cálculos Avançados
    ltv_bruto = (info["mensal"] * 24) + info["setup"]
    lucro_estimado = ltv_bruto - info["cac"]
    breakeven = ((info["cac"] - info["setup"]) / info["mensal"]) if info["mensal"] > 0 else 0

    c1, c2 = st.columns([1.5, 1])
    
    with c1:
        st.markdown(f"""
            <div class="resumo-card">
                <div class="section-header"><span class="section-title">INDICADORES DE MERCADO (VENDA)</span></div>
                <div style="display:flex; justify-content:space-around; margin-bottom:20px;">
                    <div><span class="resumo-label">Valor Setup</span><div class="resumo-valor">R$ {info['setup']:,.2f}</div></div>
                    <div><span class="resumo-label">Mensalidade</span><div class="resumo-valor" style="color:#2e7d32;">R$ {info['mensal']:,.2f}</div></div>
                </div>
                
                <div class="section-header" style="background:#262730;"><span class="section-title">INTELIGÊNCIA DE CONTRATO (24 MESES)</span></div>
                <div class="roi-container">
                    <div class="roi-row"><span class="roi-label">LTV Bruto (Faturamento Total)</span><span class="roi-num">R$ {ltv_bruto:,.2f}</span></div>
                    <div class="roi-row"><span class="roi-label">Custo de Aquisição (CAC + Impl.)</span><span class="roi-num">R$ {info['cac']:,.2f}</span></div>
                    <div class="roi-row"><span class="roi-label">Ponto de Equilíbrio (Breakeven)</span><span class="roi-num">{round(breakeven, 1)} Meses</span></div>
                    <div class="roi-row" style="border:none;"><span class="roi-label">Margem Contribuição VR</span><span class="roi-tag" style="background:#ff6600;">{info['margem']}</span></div>
                </div>
                <p style="margin-top:15px; color:#666; font-size:0.9rem;"><i>*Cálculos baseados no ciclo de vida padrão de 24 meses de contrato.</i></p>
            </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown('<div class="section-header"><span class="section-title">ENGENHARIA DE VALOR</span></div>', unsafe_allow_html=True)
        st.write(f"**Estratégia:** {info['desc']}")
        st.write(f"**Esforço Técnico:** {info['esforco']}")
        st.write(f"**Potencial Cross-sell:** {info['upsell']}")
        st.write("---")
        st.success(f"**Projeção de Lucro:** Este produto gera uma margem aproximada de R$ {lucro_estimado:,.2f} por cliente ao final de 2 anos.")

# --- 6. TELA DE PROPOSTA (COMPLETA E CORRIGIDA) ---
else:
    if not apresentacao:
        st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)

    # Estado de Sessao para persistência total
    if 's_i' not in st.session_state: st.session_state.s_i = ["Migração Banco de Dados", "Implantação e Treinamento"]
    if 's_m' not in st.session_state: st.session_state.s_m = ["VR ERP PRO"]

    if not apresentacao:
        st.markdown("---")
        cols_input = st.columns(3) if vendedor_perfil == "Rua (Executivo)" else st.columns(2)
        
        with cols_input[0]:
            st.markdown('<div class="section-header"><span class="section-title">IMPLANTAÇÃO</span></div>', unsafe_allow_html=True)
            st.session_state.s_i = st.multiselect("Serviços", list(db.keys())[7:10], default=st.session_state.s_i)
            for i in st.session_state.s_i:
                st.number_input(f"Horas: {i} (R$ {db[i]['setup']:,.2f}/h)", 0, 500, 12, key=f"inp_h_{i}")

        with cols_input[1]:
            st.markdown('<div class="section-header"><span class="section-title">MENSALIDADES</span></div>', unsafe_allow_html=True)
            st.session_state.s_m = st.multiselect("Produtos", list(db.keys())[0:7], default=st.session_state.s_m)
            for i in st.session_state.s_m:
                st.number_input(f"Qtd: {i} (R$ {db[i]['mensal']:,.2f}/un)", 0, 100, 1, key=f"inp_q_{i}")

        if len(cols_input) > 2:
            with cols_input[2]:
                st.markdown('<div class="section-header"><span class="section-title">DESPESAS</span></div>', unsafe_allow_html=True)
                for d_nome, d_valor in despesas_db.items():
                    st.number_input(f"{d_nome} (R$ {d_valor:,.2f})", 0, 1000, 0, key=f"inp_d_{d_nome}")

    # Processamento Financeiro
    total_setup, total_mensal_bruto, total_desp = 0, 0, 0
    list_i, list_m, list_d = [], [], []

    for i in st.session_state.s_i:
        v_u = db[i]["setup"]
        h = st.session_state.get(f"inp_h_{i}", 0)
        total_setup += (h * v_u)
        if h > 0: list_i.append((i, h, v_u))

    for i in st.session_state.s_m:
        v_u = db[i]["mensal"]
        q = st.session_state.get(f"inp_q_{i}", 0)
        total_mensal_bruto += (q * v_u)
        if q > 0: list_m.append((i, q, v_u))

    for d_nome, d_valor in despesas_db.items():
        q_d = st.session_state.get(f"inp_d_{d_nome}", 0)
        total_desp += (q_d * d_valor)
        if q_d > 0: list_d.append((d_nome, q_d, d_valor))

    total_mensal_liq = total_mensal_bruto * (1 - (desconto_perc/100))

    # Cards de Resultado
    st.markdown("<h2 style='text-align:center; font-weight:800; margin-top:30px;'>PROPOSTA FINAL</h2>", unsafe_allow_html=True)
    res_cols = st.columns(3) if vendedor_perfil == "Rua (Executivo)" else st.columns([1, 2, 2, 1])[1:3]

    with res_cols[0]:
        itens_i_html = "".join([f"<li><span>{n}</span><span class='badge-valor'>{h}h</span></li>" for n, h, v in list_i])
        st.markdown(f"""
            <div class="resumo-card">
                <span class="resumo-label">Investimento Setup</span>
                <div class="resumo-valor">R$ {total_setup:,.2f}</div>
                <div style="font-weight:bold; margin-top:5px;">{parcelas}x de R$ {total_setup/parcelas:,.2f}</div>
                <ul class="lista-itens">{itens_i_html}</ul>
            </div>
        """, unsafe_allow_html=True)

    with res_cols[1]:
        itens_m_html = "".join([f"<li><span>{n}</span><span class='badge-valor'>{q}un</span></li>" for n, q, v in list_m])
        # Logica do Botao de Desconto
        desc_box = f'<div style="color:#d32f2f; font-size:0.9rem; font-weight:bold;">Desconto aplicado: {desconto_perc}%</div>' if exibir_desc and desconto_perc > 0 else '<div style="height:21px;"></div>'
        st.markdown(f"""
            <div class="resumo-card" style="border-top-color:#2e7d32;">
                <span class="resumo-label">Assinatura Mensal</span>
                <div class="resumo-valor" style="color:#2e7d32;">R$ {total_mensal_liq:,.2f}</div>
                {desc_box}
                <div style="font-weight:bold; margin-top:5px;">Faturamento: {faturamento}</div>
                <ul class="lista-itens">{itens_m_html}</ul>
            </div>
        """, unsafe_allow_html=True)

    if vendedor_perfil == "Rua (Executivo)":
        with res_cols[2]:
            itens_d_html = "".join([f"<li><span>{n}</span><span class='badge-valor'>{q}</span></li>" for n, q, v in list_d])
            st.markdown(f"""
                <div class="resumo-card" style="border-top-color:#1976d2;">
                    <span class="resumo-label">Despesas Logísticas</span>
                    <div class="resumo-valor" style="color:#1976d2;">R$ {total_desp:,.2f}</div>
                    <div style="font-size:0.8rem; color:#666; margin-top:5px;">Cobradas no encerramento da implantação.</div>
                    <ul class="lista-itens">{itens_d_html}</ul>
                </div>
            """, unsafe_allow_html=True)
