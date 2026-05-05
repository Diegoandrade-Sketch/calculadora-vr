import streamlit as st
import pandas as pd
import os

# 1. Configuracao da Pagina
st.set_page_config(page_title="VR Software | Proposta Comercial", layout="wide")

# 2. Estilizacao CSS Avançada (Focado nos Cards de Resumo)
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

    /* --- ESTILO DOS CARDS DE RESUMO --- */
    .resumo-card {
        background-color: #ffffff; border: 1px solid #f0f0f0; border-top: 8px solid #ff6600;
        padding: 25px; border-radius: 8px; min-height: 520px; box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    }
    .resumo-label { color: #666; font-size: 0.9rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
    .resumo-valor { color: #ff6600; font-size: 2.8rem; font-weight: 900; margin-bottom: 5px; line-height: 1.1; }
    .resumo-subtitulo {
        font-size: 1rem; color: #111; font-weight: 800; margin-top: 25px;
        margin-bottom: 12px; border-bottom: 2px solid #ffefe5; padding-bottom: 5px;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    
    .lista-itens { font-size: 0.95rem; color: #333; line-height: 1.5; list-style-type: none; padding-left: 0; }
    .lista-itens li { 
        padding: 12px 0; 
        border-bottom: 1px dashed #e5e5e5; 
        display: flex; 
        justify-content: space-between; 
        align-items: center;
    }

    .item-detalhe { 
        color: #000; 
        font-size: 0.9rem; 
        font-weight: 700;
        background-color: #f8f9fa;
        padding: 4px 10px;
        border-radius: 6px;
        border: 1px solid #eee;
        white-space: nowrap;
    }

    .tooltip {
        position: relative; display: inline-block; cursor: help;
        border-bottom: 1px dotted #ff6600; color: #222; font-weight: 600;
    }
    .tooltip .tooltiptext {
        visibility: hidden; width: 280px; background-color: #262730; color: #fff;
        text-align: left; border-radius: 8px; padding: 12px; position: absolute;
        z-index: 10; bottom: 135%; left: 50%; margin-left: -140px; opacity: 0;
        transition: opacity 0.3s, transform 0.3s; font-size: 0.85rem; font-weight: 400;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2); transform: translateY(10px);
    }
    .tooltip:hover .tooltiptext { visibility: visible; opacity: 1; transform: translateY(0px); }
    </style>
    """, unsafe_allow_html=True)

# 3. Cabeçalho
head_col1, head_col2 = st.columns([1, 4])
with head_col1:
    if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=220)
    else: st.subheader("VR SOFTWARE")
with head_col2:
    st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)

st.markdown("---")

# 4. Dados (Mantidos conforme seu código)
itens_imp = {"Migração Banco de Dados": 201.30, "Definição de Escopo": 201.30, "Configuração Servidor / PDV Linux": 201.30, "Implantação e Treinamento": 201.30}
descricoes_imp = {
    "Migração Banco de Dados": "Cópia do cadastro de produtos, fornecedores e contas a receber vindos do sistema anterior.",
    "Definição de Escopo": "Alinhamento estratégico para mapear os processos da sua empresa.",
    "Configuração Servidor / PDV Linux": "Preparação técnica do servidor e terminais com Linux.",
    "Implantação e Treinamento": "Capacitação da equipe em todos os módulos contratados."
}
itens_mensal = {"VR ERP PRO": 1285.71, "VR PDV Convencional": 185.71, "PDV Touchscreen": 185.71, "PDV Selfcheckout": 290.44, "SiTef Express": 357.14, "VR TEF": 417.04, "Gerenciador XML": 163.84, "VR Mobile": 193.63}
itens_desp = {"Alimentação": 49.00, "Hospedagem": 195.00, "Deslocamento (KM)": 2.12}

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("PAINEL DE CONTROLE")
    modo_apresentacao = st.toggle("Modo Apresentação", value=False)
    st.markdown('<span class="sidebar-label">Negociação</span>', unsafe_allow_html=True)
    desc = st.number_input("Desconto Mensal (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.01, format="%.2f")
    parcelas = st.selectbox("Parcelamento Setup", [1, 2, 3, 4, 5, 6, 10, 12], index=3)

# 5. Interface de Seleção
if not modo_apresentacao:
    col1, col2, col3 = st.columns(3)
    dados_imp_final = []
    with col1:
        st.markdown('<div class="section-header"><span class="section-title">IMPLANTAÇÃO</span></div>', unsafe_allow_html=True)
        imp_sel = st.multiselect("Selecione os itens", list(itens_imp.keys()), default=list(itens_imp.keys()))
        t_imp = 0
        for item in imp_sel:
            h = st.number_input(f"Horas: {item}", min_value=0, value=12 if "Treinamento" not in item else 120, key=f"h_{item}")
            t_imp += h * itens_imp[item]
            dados_imp_final.append((item, h, itens_imp[item]))

    dados_mensal_final = []
    with col2:
        st.markdown('<div class="section-header"><span class="section-title">MENSALIDADES</span></div>', unsafe_allow_html=True)
        mensal_sel = st.multiselect("Selecione os produtos", list(itens_mensal.keys()), default=["VR ERP PRO"])
        t_men_bruto = 0
        for item in mensal_sel:
            q = st.number_input(f"Qtd: {item}", min_value=0, value=1, key=f"q_{item}")
            t_men_bruto += q * itens_mensal[item]
            dados_mensal_final.append((item, q, itens_mensal[item]))
        t_men_liq = t_men_bruto * (1 - (desc/100))

    dados_desp_final = []
    with col3:
        st.markdown('<div class="section-header"><span class="section-title">DESPESAS</span></div>', unsafe_allow_html=True)
        t_desp = 0
        for item, preco in itens_desp.items():
            qd = st.number_input(f"{item}", min_value=0, value=0, key=f"d_{item}")
            t_desp += qd * preco
            if qd > 0: dados_desp_final.append((item, qd, preco))
    st.session_state.update({'t_imp': t_imp, 'dados_imp': dados_imp_final, 't_men_liq': t_men_liq, 'dados_mensal': dados_mensal_final, 't_desp': t_desp, 'dados_desp': dados_desp_final})
else:
    t_imp = st.session_state.get('t_imp', 0); dados_imp_final = st.session_state.get('dados_imp', [])
    t_men_liq = st.session_state.get('t_men_liq', 0); dados_mensal_final = st.session_state.get('dados_mensal', [])
    t_desp = st.session_state.get('t_desp', 0); dados_desp_final = st.session_state.get('dados_desp', [])

# 6. SEÇÃO DE RESUMO VISUAL (FONTES E TEXTOS AJUSTADOS)
st.markdown("<h2 style='text-align: center; color: #333; font-weight: 800; margin-top: 30px; margin-bottom: 20px;'>DETALHAMENTO DA PROPOSTA</h2>", unsafe_allow_html=True)
res_col1, res_col2, res_col3 = st.columns(3)

with res_col1:
    html_itens = "".join([f"<li><span><span class='tooltip'>{i}<span class='tooltiptext'>{descricoes_imp.get(i,'')}</span></span></span><span class='item-detalhe'>{h}h x R$ {v:,.2f}</span></li>" for i, h, v in dados_imp_final])
    st.markdown(f"""
        <div class="resumo-card">
            <span class="resumo-label">Investimento Setup</span>
            <div class="resumo-valor">R$ {t_imp:,.2f}</div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #444;">{parcelas}x de R$ {t_imp/parcelas:,.2f}</div>
            <div class="resumo-subtitulo">SERVIÇOS DE IMPLANTAÇÃO</div>
            <ul class="lista-itens">{html_itens if html_itens else "<li>Nenhum item selecionado</li>"}</ul>
        </div>
    """, unsafe_allow_html=True)

with res_col2:
    # AJUSTE: Termo "Lic." padronizado e cores de destaque para o desconto
    html_itens = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{q} Lic. x R$ {v:,.2f}</span></li>" for i, q, v in dados_mensal_final])
    cor_desc = "#d32f2f" if desc > 15.0 else "#2e7d32"
    st.markdown(f"""
        <div class="resumo-card" style="border-top-color: {cor_desc};">
            <span class="resumo-label">Investimento Mensal</span>
            <div class="resumo-valor">R$ {t_men_liq:,.2f}</div>
            <div style="font-size: 1.1rem; color: {cor_desc}; font-weight: 800;">Desconto: {desc:.2f}%</div>
            <div class="resumo-subtitulo">SISTEMAS E LICENÇAS</div>
            <ul class="lista-itens">{html_itens if html_itens else "<li>Nenhum item selecionado</li>"}</ul>
        </div>
    """, unsafe_allow_html=True)

with res_col3:
    html_itens = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{q} un. x R$ {v:,.2f}</span></li>" for i, q, v in dados_desp_final])
    st.markdown(f"""
        <div class="resumo-card" style="border-top-color: #1976d2;">
            <span class="resumo-label">Previsão de Despesas</span>
            <div class="resumo-valor">R$ {t_desp:,.2f}</div>
            <div style="font-size: 0.95rem; color: #d32f2f; font-weight: 700; background: #fff5f5; padding: 6px 10px; border-radius: 4px; display: inline-block;">Faturadas ao término</div>
            <div class="resumo-subtitulo">DETALHAMENTO LOGÍSTICO</div>
            <ul class="lista-itens">{html_itens if html_itens else "<li>Nenhuma despesa selecionada</li>"}</ul>
        </div>
    """, unsafe_allow_html=True)
