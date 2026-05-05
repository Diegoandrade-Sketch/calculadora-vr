import streamlit as st
import pandas as pd  # <-- O erro estava aqui, faltava o 'pandas'
import urllib.parse
import os

# 1. Configuracao da Pagina
st.set_page_config(page_title="VR Software | Proposta Comercial", layout="wide")

# 2. Estilizacao CSS Avançada (Base mantida com novas classes para etiquetas)
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #ffffff 0%, #fff5ed 100%); }
    
    .hero-title {
        color: #262730; font-size: 5.5rem; font-weight: 900; margin: 0; padding: 0;
        line-height: 1; letter-spacing: -3px; text-transform: uppercase;
    }
    
    .sidebar-label {
        color: #ff6600; font-size: 0.9rem; font-weight: 800; text-transform: uppercase;
        margin-top: 20px; margin-bottom: 10px; display: block; letter-spacing: 1px;
    }

    div.stButton > button {
        width: 100%; background: linear-gradient(90deg, #ff6600 0%, #ff944d 100%);
        color: white; border: none; padding: 12px 20px; border-radius: 8px;
        font-weight: bold; font-size: 1rem; transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 102, 0, 0.2);
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
    .resumo-label { color: #888; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; display: block; }
    
    /* Etiqueta de Condição de Faturamento */
    .faturamento-tag {
        font-size: 0.85rem; color: #2e7d32; font-weight: 700; 
        background: #e8f5e9; padding: 4px 10px; border-radius: 4px;
        display: inline-block; margin-top: 8px; border: 1px solid #c8e6c9;
    }

    .resumo-subtitulo {
        font-size: 1.1rem; color: #333; font-weight: bold; margin-top: 20px;
        margin-bottom: 10px; border-bottom: 2px solid #ffefe5; padding-bottom: 5px;
    }
    
    .lista-itens { font-size: 1.05rem; color: #444; line-height: 1.6; list-style-type: none; padding-left: 0; }
    .lista-itens li { 
        padding: 10px 0; border-bottom: 1px dashed #e0e0e0; 
        display: flex; justify-content: space-between; align-items: center;
    }

    .item-detalhe { 
        color: #333; font-size: 1.05rem; font-weight: 700;
        background-color: #fcfcfc; padding: 2px 8px; border-radius: 4px;
    }

    .tooltip {
        position: relative; display: inline-block; cursor: help;
        border-bottom: 1px dotted #ff6600; color: #222; font-weight: 600;
    }

    .tooltip .tooltiptext {
        visibility: hidden; width: 280px; background-color: #262730; color: #fff;
        text-align: left; border-radius: 8px; padding: 12px; position: absolute;
        z-index: 10; bottom: 135%; left: 50%; margin-left: -140px; opacity: 0;
        transition: opacity 0.3s, transform 0.3s; font-size: 0.85rem; line-height: 1.4;
        font-weight: 400; box-shadow: 0 10px 20px rgba(0,0,0,0.2); transform: translateY(10px);
    }

    .tooltip:hover .tooltiptext { visibility: visible; opacity: 1; transform: translateY(0px); }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BARRA LATERAL ---
with st.sidebar:
    st.title("PAINEL DE CONTROLE")
    
    st.markdown('<span class="sidebar-label">Perfil da Venda</span>', unsafe_allow_html=True)
    perfil_venda = st.selectbox("Selecione o perfil", ["Executivo (Rua)", "CS (Base)"], index=0)
    
    modo_apresentacao = st.toggle("Modo Apresentação", value=False)
    
    st.markdown('<span class="sidebar-label">Negociação</span>', unsafe_allow_html=True)
    desc = st.number_input("Desconto Mensal (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.1)
    if desc > 15.0:
        st.warning("⚠️ Desconto não autorizado. Necessária aprovação financeira.")
    
    condicao_faturamento = st.selectbox(
        "Faturamento da Mensalidade", 
        ["Imediato", "Com 30 dias", "Com 60 dias", "Após a implantação"]
    )
    
    parcelas = st.selectbox("Parcelamento Setup", [1, 2, 3, 4, 5, 6], index=3)
    
    st.write("---")
    st.markdown('<span class="sidebar-label">Exportação</span>', unsafe_allow_html=True)
    if st.button("FORMATAR PARA WHATSAPP"):
        t_i = st.session_state.get('t_imp', 0)
        t_m = st.session_state.get('t_men_liq', 0)
        t_d = st.session_state.get('t_desp', 0)
        
        resumo_txt = (f"*PROPOSTA VR SOFTWARE*\n\n"
                      f"*Setup:* R$ {t_i:,.2f} em {parcelas}x\n"
                      f"*Mensalidade:* R$ {t_m:,.2f} ({condicao_faturamento})")
        if perfil_venda == "Executivo (Rua)":
            resumo_txt += f"\n*Despesas:* R$ {t_d:,.2f}"
            
        st.code(resumo_txt, language="text")

# 4. Cabeçalho e Dados Base (Mantidos conforme código principal)
head_col1, head_col2 = st.columns([1, 4])
with head_col1:
    st.subheader("VR SOFTWARE")

with head_col2:
    if not modo_apresentacao:
        st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)

if not modo_apresentacao:
    st.markdown("---")

itens_imp = {"Migração Banco de Dados": 201.30, "Definição de Escopo": 201.30, "Configuração Servidor / PDV Linux": 201.30, "Implantação e Treinamento": 201.30}
descricoes_imp = {"Migração Banco de Dados": "Cópia do cadastro de produtos e fornecedores.", "Definição de Escopo": "Mapeamento estratégico de processos.", "Configuração Servidor / PDV Linux": "Preparação técnica do ambiente Linux.", "Implantação e Treinamento": "Capacitação da equipe nos módulos."}
itens_mensal = {"VR ERP PRO": 1285.71, "VR PDV Convencional": 185.71, "PDV Touchscreen": 185.71, "PDV Selfcheckout": 290.44, "SiTef Express": 357.14, "VR TEF": 417.04, "Gerenciador XML": 163.84, "VR Mobile": 193.63}
itens_desp = {"Alimentação": 49.00, "Hospedagem": 195.00, "Deslocamento (KM)": 2.12}

# 6. Lógica de Interface
if not modo_apresentacao:
    if perfil_venda == "Executivo (Rua)":
        col1, col2, col3 = st.columns(3)
    else:
        col1, col2 = st.columns(2)
        col3 = None
    
    dados_imp_final = []
    with col1:
        st.markdown('<div class="section-header"><span class="section-title">SERVIÇOS DE IMPLANTAÇÃO</span></div>', unsafe_allow_html=True)
        imp_sel = st.multiselect("Selecione os itens", list(itens_imp.keys()), default=list(itens_imp.keys()))
        t_imp = sum([st.number_input(f"Horas: {i} (R$ {itens_imp[i]:,.2f})", 0, 200, 12 if "Treinamento" not in i else 120, key=f"h_{i}") * itens_imp[i] for i in imp_sel])
        dados_imp_final = [(i, st.session_state[f"h_{i}"], itens_imp[i]) for i in imp_sel]

    dados_mensal_final = []
    with col2:
        st.markdown('<div class="section-header"><span class="section-title">ITENS MENSAIS</span></div>', unsafe_allow_html=True)
        mensal_sel = st.multiselect("Selecione os produtos", list(itens_mensal.keys()), default=["VR ERP PRO"])
        t_men_bruto = sum([st.number_input(f"Qtd: {i} (R$ {itens_mensal[i]:,.2f})", 0, 100, 1, key=f"q_{i}") * itens_mensal[i] for i in mensal_sel])
        dados_mensal_final = [(i, st.session_state[f"q_{i}"], itens_mensal[i]) for i in mensal_sel]

    dados_desp_final = []
    t_desp = 0
    if col3:
        with col3:
            st.markdown('<div class="section-header"><span class="section-title">PREVISÃO DE DESPESAS</span></div>', unsafe_allow_html=True)
            for item, preco in itens_desp.items():
                qd = st.number_input(f"{item} (R$ {preco:,.2f})", 0, 1000, 0, key=f"d_{item}")
                t_desp += qd * preco
                if qd > 0: dados_desp_final.append((item, qd, preco))

    st.session_state.update({'t_imp': t_imp, 'dados_imp': dados_imp_final, 't_men_bruto': t_men_bruto, 'dados_mensal': dados_mensal_final, 't_desp': t_desp, 'dados_desp': dados_desp_final})
else:
    t_imp, dados_imp_final = st.session_state.get('t_imp', 0), st.session_state.get('dados_imp', [])
    t_men_bruto, dados_mensal_final = st.session_state.get('t_men_bruto', 0), st.session_state.get('dados_mensal', [])
    t_desp, dados_desp_final = (st.session_state.get('t_desp', 0) if perfil_venda == "Executivo (Rua)" else 0), st.session_state.get('dados_desp', [])

t_men_liq = t_men_bruto * (1 - (desc/100))
st.session_state['t_men_liq'] = t_men_liq

# 7. RESUMO VISUAL
st.markdown("<h2 style='text-align: center; color: #333; font-weight: 800; margin-bottom: 25px;'>DETALHAMENTO DA PROPOSTA</h2>", unsafe_allow_html=True)

if perfil_venda == "Executivo (Rua)":
    res_col1, res_col2, res_col3 = st.columns(3)
else:
    _, res_col1, res_col2, _ = st.columns([0.5, 2, 2, 0.5])
    res_col3 = None

with res_col1:
    html_itens = "".join([f"<li><span><span class='tooltip'>{i}<span class='tooltiptext'>{descricoes_imp.get(i)}</span></span></span><span class='item-detalhe'>{h}h x R$ {v:,.2f}</span></li>" for i, h, v in dados_imp_final])
    st.markdown(f'<div class="resumo-card"><span class="resumo-label">Investimento Setup</span><div class="resumo-valor">R$ {t_imp:,.2f}</div><div style="font-size: 1.2rem; font-weight: bold;">{parcelas}x de R$ {t_imp/parcelas:,.2f}</div><div class="resumo-subtitulo">SERVIÇOS DE IMPLANTAÇÃO</div><ul class="lista-itens">{html_itens}</ul></div>', unsafe_allow_html=True)

with res_col2:
    html_itens = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{q} Lic. x R$ {v:,.2f}</span></li>" for i, q, v in dados_mensal_final])
    st.markdown(f"""
        <div class="resumo-card" style="border-top-color: #2e7d32;">
            <span class="resumo-label">Investimento Mensal</span>
            <div class="resumo-valor" style="color: #2e7d32;">R$ {t_men_liq:,.2f}</div>
            <div style="font-size: 1.1rem; color: #2e7d32; font-weight: bold;">Desconto: {desc:,.2f}%</div>
            <div class="faturamento-tag">📅 Faturamento: {condicao_faturamento}</div>
            <div class="resumo-subtitulo">SISTEMAS E LICENÇAS</div>
            <ul class="lista-itens">{html_itens}</ul>
        </div>
    """, unsafe_allow_html=True)

if res_col3:
    html_itens = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{q} Qtd. x R$ {v:,.2f}</span></li>" for i, q, v in dados_desp_final])
    st.markdown(f'<div class="resumo-card" style="border-top-color: #1976d2;"><span class="resumo-label">Previsão de Despesas</span><div class="resumo-valor" style="color: #1976d2;">R$ {t_desp:,.2f}</div><div style="font-size: 1rem; color: #d32f2f; font-weight: bold; background: #fff5f5; padding: 5px; border-radius: 4px;">Faturadas ao término da implantação</div><div class="resumo-subtitulo">DETALHAMENTO LOGÍSTICO</div><ul class="lista-itens">{html_itens}</ul></div>', unsafe_allow_html=True)
