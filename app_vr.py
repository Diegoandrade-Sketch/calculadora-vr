import streamlit as st
import pandas as pd
import os

# 1. Configuracao da Pagina
st.set_page_config(page_title="VR Software | Proposta Comercial", layout="wide")

# 2. Estilizacao CSS (Simplificada para o exemplo, mantenha a sua completa)
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #ffffff 0%, #fff5ed 100%); }
    .hero-title { color: #262730; font-size: 5.5rem; font-weight: 900; margin: 0; padding: 0; line-height: 1; letter-spacing: -3px; text-transform: uppercase; }
    .sidebar-label { color: #ff6600; font-size: 0.9rem; font-weight: 800; text-transform: uppercase; margin-top: 20px; margin-bottom: 10px; display: block; letter-spacing: 1px; }
    .section-header { display: flex; justify-content: space-between; align-items: center; background: linear-gradient(90deg, #ff6600 0%, #ff944d 100%); padding: 8px 15px; border-radius: 5px; margin-bottom: 15px; margin-top: 20px; }
    .section-title { color: #ffffff; font-size: 1.1rem; font-weight: bold; margin: 0; }
    .resumo-card { background-color: #ffffff; border: 1px solid #f0f0f0; border-top: 8px solid #ff6600; padding: 25px; border-radius: 8px; min-height: 480px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }
    .resumo-valor { color: #ff6600; font-size: 2.5rem; font-weight: 900; margin-bottom: 5px; }
    .resumo-subtitulo { font-size: 1.1rem; color: #333; font-weight: bold; margin-top: 20px; margin-bottom: 10px; border-bottom: 2px solid #ffefe5; padding-bottom: 5px; }
    .lista-itens { font-size: 1.05rem; color: #444; line-height: 1.6; list-style-type: none; padding-left: 0; }
    .lista-itens li { padding: 10px 0; border-bottom: 1px dashed #e0e0e0; display: flex; justify-content: space-between; align-items: center; }
    .item-detalhe { color: #333; font-size: 1.05rem; font-weight: 700; background-color: #fcfcfc; padding: 2px 8px; border-radius: 4px; }
    .tooltip { position: relative; display: inline-block; cursor: help; border-bottom: 1px dotted #ff6600; color: #222; font-weight: 600; }
    .tooltip .tooltiptext { visibility: hidden; width: 280px; background-color: #262730; color: #fff; text-align: left; border-radius: 8px; padding: 12px; position: absolute; z-index: 10; bottom: 135%; left: 50%; margin-left: -140px; opacity: 0; transition: opacity 0.3s, transform 0.3s; font-size: 0.85rem; line-height: 1.4; font-weight: 400; transform: translateY(10px); }
    .tooltip:hover .tooltiptext { visibility: visible; opacity: 1; transform: translateY(0px); }
    </style>
    """, unsafe_allow_html=True)

# 3. CARGA DE DADOS
@st.cache_data
def carregar_dados_excel():
    caminho = "precos.xlsx"
    if not os.path.exists(caminho): return {}, {}, {}, {}
    try:
        df = pd.read_excel(caminho)
        imp = df[df['Categoria'] == 'Implantação'].set_index('Item')['Valor'].to_dict()
        men = df[df['Categoria'] == 'Mensal'].set_index('Item')['Valor'].to_dict()
        des = df[df['Categoria'] == 'Despesa'].set_index('Item')['Valor'].to_dict()
        descricoes = df.set_index('Item')['Descricao'].to_dict()
        return imp, men, des, descricoes
    except: return {}, {}, {}, {}

itens_imp, itens_mensal, itens_desp, descricoes_imp = carregar_dados_excel()

# --- 4. BARRA LATERAL (COM AS NOVAS TRAVAS) ---
with st.sidebar:
    st.title("PAINEL DE CONTROLE")
    modo_apresentacao = st.toggle("Modo Apresentação", value=False)
    
    st.markdown('<span class="sidebar-label">Negociação</span>', unsafe_allow_html=True)
    
    # Alteração 1: Desconto com mensagem de aprovação
    desc = st.number_input("Desconto Mensal (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.1)
    if desc > 15.0:
        st.error("⚠️ Desconto não autorizado! Este valor precisará passar pela aprovação do financeiro.")
    elif desc > 0:
        st.success("✅ Desconto autorizado pelo comercial.")

    # Alteração 2: Parcelamento máximo de 6x
    parcelas = st.selectbox("Parcelamento Setup", [1, 2, 3, 4, 5, 6], index=0)
    
    st.write("---")
    if st.button("FORMATAR PARA WHATSAPP"):
        t_i = st.session_state.get('t_imp', 0)
        t_m = st.session_state.get('t_men_liq', 0)
        t_d = st.session_state.get('t_desp', 0)
        resumo_txt = f"*PROPOSTA VR SOFTWARE*\n\n*Setup:* R$ {t_i:,.2f} em {parcelas}x\n*Mensalidade:* R$ {t_m:,.2f} ({desc}% desc.)\n*Despesas:* R$ {t_d:,.2f}"
        st.code(resumo_txt, language="text")

# 5. Cabeçalho
head_col1, head_col2 = st.columns([1, 4])
with head_col1:
    if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=220)
    else: st.subheader("VR SOFTWARE")
with head_col2:
    if not modo_apresentacao: st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)

# 6. Lógica de Interface
if not modo_apresentacao:
    col1, col2, col3 = st.columns(3)
    
    dados_imp_final = []
    with col1:
        st.markdown('<div class="section-header"><span class="section-title">SERVIÇOS DE IMPLANTAÇÃO</span></div>', unsafe_allow_html=True)
        imp_sel = st.multiselect("Itens", list(itens_imp.keys()), default=list(itens_imp.keys()))
        t_imp = 0
        for item in imp_sel:
            h = st.number_input(f"Horas: {item}", min_value=0, value=12, key=f"h_{item}")
            t_imp += h * itens_imp[item]
            dados_imp_final.append((item, h, itens_imp[item]))

    dados_mensal_final = []
    with col2:
        st.markdown('<div class="section-header"><span class="section-title">ITENS MENSAIS</span></div>', unsafe_allow_html=True)
        mensal_sel = st.multiselect("Produtos", list(itens_mensal.keys()))
        t_men_bruto = 0
        for item in mensal_sel:
            q = st.number_input(f"Qtd: {item}", min_value=0, value=1, key=f"q_{item}")
            t_men_bruto += q * itens_mensal[item]
            dados_mensal_final.append((item, q, itens_mensal[item]))

    dados_desp_final = []
    with col3:
        st.markdown('<div class="section-header"><span class="section-title">PREVISÃO DE DESPESAS</span></div>', unsafe_allow_html=True)
        t_desp = 0
        for item, preco in itens_desp.items():
            qd = st.number_input(f"{item}", min_value=0, value=0, key=f"d_{item}")
            t_desp += qd * preco
            if qd > 0: dados_desp_final.append((item, qd, preco))

    st.session_state.update({'t_imp': t_imp, 'dados_imp': dados_imp_final, 't_men_bruto': t_men_bruto, 'dados_mensal': dados_mensal_final, 't_desp': t_desp, 'dados_desp': dados_desp_final})
else:
    t_imp = st.session_state.get('t_imp', 0); dados_imp_final = st.session_state.get('dados_imp', [])
    t_men_bruto = st.session_state.get('t_men_bruto', 0); dados_mensal_final = st.session_state.get('dados_mensal', [])
    t_desp = st.session_state.get('t_desp', 0); dados_desp_final = st.session_state.get('dados_desp', [])

t_men_liq = t_men_bruto * (1 - (desc/100))
st.session_state['t_men_liq'] = t_men_liq

# 7. Resumo Visual
st.markdown("<h2 style='text-align: center; color: #333; font-weight: 800;'>DETALHAMENTO DA PROPOSTA</h2>", unsafe_allow_html=True)
res_col1, res_col2, res_col3 = st.columns(3)

with res_col1:
    html_itens = "".join([f"<li><span><span class='tooltip'>{i}<span class='tooltiptext'>{descricoes_imp.get(i,'')}</span></span></span><span class='item-detalhe'>{h}h</span></li>" for i, h, v in dados_imp_final])
    st.markdown(f'<div class="resumo-card"><span class="resumo-label">Setup</span><div class="resumo-valor">R$ {t_imp:,.2f}</div><div style="font-weight:bold;">{parcelas}x de R$ {t_imp/parcelas:,.2f}</div><div class="resumo-subtitulo">SERVIÇOS</div><ul class="lista-itens">{html_itens}</ul></div>', unsafe_allow_html=True)

with res_col2:
    html_itens = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{q} un</span></li>" for i, q, v in dados_mensal_final])
    cor_desc = "#d32f2f" if desc > 15 else "#2e7d32"
    st.markdown(f'<div class="resumo-card" style="border-top-color: {cor_desc};"><span class="resumo-label">Mensal</span><div class="resumo-valor">R$ {t_men_liq:,.2f}</div><div style="color:{cor_desc}; font-weight:bold;">Desconto: {desc}%</div><div class="resumo-subtitulo">LICENÇAS</div><ul class="lista-itens">{html_itens}</ul></div>', unsafe_allow_html=True)

with res_col3:
    html_itens = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{q}</span></li>" for i, q, v in dados_desp_final])
    st.markdown(f'<div class="resumo-card" style="border-top-color: #1976d2;"><span class="resumo-label">Despesas</span><div class="resumo-valor">R$ {t_desp:,.2f}</div><div style="font-size:0.8rem;">Faturado após implantação</div><div class="resumo-subtitulo">LOGÍSTICA</div><ul class="lista-itens">{html_itens}</ul></div>', unsafe_allow_html=True)
