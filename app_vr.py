import streamlit as st
import pandas as pd
import os
from PIL import Image, ImageDraw, ImageFont
import io

# 1. Configuracao da Pagina
st.set_page_config(page_title="VR Software | Proposta Comercial", layout="wide")

# 2. Estilizacao CSS
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #ffffff 0%, #fff5ed 100%);
    }
    
    .hero-title {
        color: #262730; font-size: 5.5rem; font-weight: 900; margin: 0; padding: 0;
        line-height: 1; letter-spacing: -3px; text-transform: uppercase;
    }
    
    .section-header {
        display: flex; justify-content: space-between; align-items: center;
        background: linear-gradient(90deg, #ff6600 0%, #ff944d 100%);
        padding: 8px 15px; border-radius: 5px; margin-bottom: 15px; margin-top: 20px;
    }
    .section-title { color: #ffffff; font-size: 1.1rem; font-weight: bold; margin: 0; }
    
    .resumo-card {
        background-color: #ffffff; border: 1px solid #f0f0f0; border-top: 8px solid #ff6600;
        padding: 25px; border-radius: 8px; min-height: 450px; box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    }
    .resumo-valor { color: #ff6600; font-size: 2.5rem; font-weight: 900; margin-bottom: 5px; }
    .resumo-subtitulo {
        font-size: 1.1rem; color: #333; font-weight: bold; margin-top: 20px;
        margin-bottom: 10px; border-bottom: 2px solid #ffefe5; padding-bottom: 5px;
    }
    .lista-itens { font-size: 1.05rem; color: #444; line-height: 1.6; list-style-type: none; padding-left: 0; }
    .lista-itens li { padding: 6px 0; border-bottom: 1px dashed #f0f0f0; display: flex; justify-content: space-between; }
    .item-detalhe { color: #777; font-size: 0.9rem; }

    [data-testid="stSidebar"] .stButton > button {
        width: 100%; border-radius: 5px; height: 3em; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# Funcao para Gerar Imagem de Resumo
def gerar_imagem_resumo(t_imp, p_imp, t_men, t_desp):
    img = Image.new('RGB', (800, 600), color='#ffffff')
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, 800, 100], fill='#ff6600')
    try:
        font_titulo = ImageFont.truetype("arialbd.ttf", 40)
        font_sub = ImageFont.truetype("arial.ttf", 25)
        font_valor = ImageFont.truetype("arialbd.ttf", 50)
    except:
        font_titulo = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_valor = ImageFont.load_default()
    
    draw.text((40, 25), "RESUMO DA PROPOSTA - VR SOFTWARE", fill="white", font=font_titulo)
    draw.text((40, 140), "IMPLANTACAO SETUP", fill="#666666", font=font_sub)
    draw.text((40, 175), f"R$ {t_imp:,.2f}", fill="#ff6600", font=font_valor)
    draw.text((40, 235), f"Condicao: {p_imp}x de R$ {t_imp/p_imp:,.2f}", fill="#333333", font=font_sub)
    draw.text((40, 300), "LICENCIAMENTO MENSAL", fill="#666666", font=font_sub)
    draw.text((40, 335), f"R$ {t_men:,.2f}", fill="#2e7d32", font=font_valor)
    draw.text((40, 460), "PREVISAO DE DESPESAS", fill="#666666", font=font_sub)
    draw.text((40, 495), f"R$ {t_desp:,.2f}", fill="#1976d2", font=font_valor)
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# 3. Cabecalho
head_col1, head_col2 = st.columns([1, 4])
with head_col1:
    if os.path.exists("logo_vr.png"):
        st.image("logo_vr.png", width=220)
    else:
        st.subheader("VR SOFTWARE")
with head_col2:
    st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)

st.markdown("---")

# 4. Dados de Preco Fixos
itens_imp = {"Migracao Banco de Dados": 201.30, "Definicao de Escopo": 201.30, "Configuracao Servidor PDV Linux": 201.30, "Implantacao e Treinamento": 201.30}
itens_mensal = {"VR ERP PRO": 1285.71, "VR PDV Convencional": 185.71, "PDV Touchscreen": 185.71, "PDV Selfcheckout": 290.44, "SiTef Express": 357.14, "VR TEF": 417.04, "Gerenciador XML": 163.84, "VR Mobile": 193.63}
itens_desp = {"Alimentacao": 49.00, "Hospedagem": 195.00, "Deslocamento KM": 2.12}

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("CONFIGURACOES")
    desc = st.number_input("Desconto Mensal Porcentagem", min_value=0.0, max_value=30.0, value=0.0, step=0.1)
    parcelas = st.selectbox("Parcelas Setup", [1, 2, 3, 4, 5, 6, 10, 12], index=3)
    
    st.write("---")
    
    if st.button("Gerar Texto para Whatsapp"):
        t_i = st.session_state.get('t_imp', 0)
        t_m = st.session_state.get('t_men_liq', 0)
        t_d = st.session_state.get('t_desp', 0)
        msg = f"PROPOSTA VR SOFTWARE\n\nSetup: R$ {t_i:,.2f} ({parcelas}x)\nMensal: R$ {t_m:,.2f}\nDespesas: R$ {t_d:,.2f}"
        st.code(msg, language="text")

    img_data = gerar_imagem_resumo(st.session_state.get('t_imp', 0), parcelas, st.session_state.get('t_men_liq', 0), st.session_state.get('t_desp', 0))
    st.download_button(label="Baixar Card da Proposta", data=img_data, file_name="proposta_vr.png", mime="image/png")

# 5. Interface de Selecao de Itens
col1, col2, col3 = st.columns(3)

dados_imp_final = []
with col1:
    st.markdown('<div class="section-header"><span class="section-title">SERVICOS</span></div>', unsafe_allow_html=True)
    imp_sel = st.multiselect("Itens de Implantacao", list(itens_imp.keys()), default=list(itens_imp.keys()))
    t_imp = 0
    for item in imp_sel:
        v_u = itens_imp[item]
        h = st.number_input(f"Horas {item}", min_value=0, value=12 if "Treinamento" not in item else 120, key=f"h_{item}")
        t_imp += h * v_u
        dados_imp_final.append((item, h, v_u))

dados_mensal_final = []
with col2:
    st.markdown('<div class="section-header"><span class="section-title">PRODUTOS</span></div>', unsafe_allow_html=True)
    mensal_sel = st.multiselect("Itens Mensais", list(itens_mensal.keys()), default=["VR ERP PRO"])
    t_men_bruto = 0
    for item in mensal_sel:
        v_u = itens_mensal[item]
        q = st.number_input(f"Qtd {item}", min_value=0, value=1, key=f"q_{item}")
        t_men_bruto += q * v_u
        dados_mensal_final.append((item, q, v_u))
    t_men_liq = t_men_bruto * (1 - (desc/100))

dados_desp_final = []
with col3:
    st.markdown('<div class="section-header"><span class="section-title">DESPESAS</span></div>', unsafe_allow_html=True)
    t_desp = 0
    for item, preco in itens_desp.items():
        qd = st.number_input(f"{item}", min_value=0, value=0, key=f"d_{item}")
        t_desp += qd * preco
        if qd > 0: dados_desp_final.append((item, qd, preco))

# Atualiza sessao para os botoes da sidebar
st.session_state.update({'t_imp': t_imp, 't_men_liq': t_men_liq, 't_desp': t_desp})

# 6. Detalhamento Final
st.markdown("<br><h2 style='text-align: center; color: #333; font-weight: 800;'>DETALHAMENTO DA PROPOSTA</h2>", unsafe_allow_html=True)
res_col1, res_col2, res_col3 = st.columns(3)

with res_col1:
    h_i = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{h}h x R$ {v:,.2f}</span></li>" for i, h, v in dados_imp_final])
    st.markdown(f'<div class="resumo-card"><span class="resumo-label">Investimento Setup</span><div class="resumo-valor">R$ {t_imp:,.2f}</div><div style="font-size: 1.2rem; font-weight: bold;">{parcelas}x de R$ {t_imp/parcelas:,.2f}</div><div class="resumo-subtitulo">SERVICOS DE IMPLANTACAO</div><ul class="lista-itens">{h_i if h_i else "<li>Nenhum item selecionado</li>"}</ul></div>', unsafe_allow_html=True)

with res_col2:
    h_m = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{q} Qtd x R$ {v:,.2f}</span></li>" for i, q, v in dados_mensal_final])
    st.markdown(f'<div class="resumo-card" style="border-top-color: #2e7d32;"><span class="resumo-label">Investimento Mensal</span><div class="resumo-valor">R$ {t_men_liq:,.2f}</div><div style="font-size: 1.1rem; color: #2e7d32; font-weight: bold;">Desconto: {desc}%</div><div class="resumo-subtitulo">SISTEMAS E LICENCAS</div><ul class="lista-itens">{h_m if h_m else "<li>Nenhum item selecionado</li>"}</ul></div>', unsafe_allow_html=True)

with res_col3:
    h_d = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{q} Un x R$ {v:,.2f}</span></li>" for i, q, v in dados_desp_final])
    st.markdown(f'<div class="resumo-card" style="border-top-color: #1976d2;"><span class="resumo-label">Previsao de Despesas</span><div class="resumo-valor">R$ {t_desp:,.2f}</div><div style="font-size: 1rem; color: #d32f2f; font-weight: bold;">Valores faturados pos-servico</div><div class="resumo-subtitulo">LOGISTICA E VIAGEM</div><ul class="lista-itens">{h_d if h_d else "<li>Nenhuma despesa lancada</li>"}</ul></div>', unsafe_allow_html=True)
