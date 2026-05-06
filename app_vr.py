import streamlit as st
import pandas as pd
import os
import textwrap

# 1. Configuração da Página
st.set_page_config(page_title="VR Software | Sales Intelligence", layout="wide")

# --- LINK DO GOOGLE SHEETS (VERSÃO CSV) ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTgmdf_FgFd91dkm5zoD0l6l2ailLhCsEV-3pyFsQxRzoyNw2E96eQQoCYkfxHitA9oCIvfaI30-k-2/pub?output=csv"

# --- FUNÇÃO DE SINCRONIZAÇÃO (BLINDAGEM) ---
def sync_state(key_permanente, key_widget):
    st.session_state[key_permanente] = st.session_state[key_widget]

# --- CARREGAMENTO DE DADOS (APENAS 4 COLUNAS) ---
@st.cache_data(ttl=600)
def carregar_dados_vendas():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = [c.strip() for c in df.columns] # Limpa espaços nos títulos
        
        # Filtra os dados apenas pelas colunas que você criou
        # e separa pelos tipos para os cards
        sistemas = df[df['Tipo'] == 'Sistema'].set_index('Produto').to_dict('index')
        servicos = df[df['Tipo'] == 'Servico'].set_index('Produto').to_dict('index')
        despesas = df[df['Tipo'] == 'Despesa'].set_index('Produto').to_dict('index')
        
        return sistemas, servicos, despesas
    except Exception as e:
        st.error(f"Erro ao ler a planilha: {e}")
        return {}, {}, {}

sistemas_db, servicos_db, despesas_db = carregar_dados_vendas()

# 2. Estilização CSS
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
    .item-detalhe { color: #333; font-size: 1.05rem; font-weight: 700; background-color: #fcfcfc; padding: 2px 8px; border-radius: 4px; }
    .section-header { background: linear-gradient(90deg, #ff6600 0%, #ff944d 100%); padding: 8px 15px; border-radius: 5px; margin-bottom: 15px; margin-top: 20px; }
    .section-title { color: #ffffff; font-size: 1.1rem; font-weight: bold; margin: 0; }
    .lista-itens { list-style-type: none; padding-left: 0; margin-top: 10px; }
    .lista-itens li { padding: 10px 0; border-bottom: 1px dashed #e0e0e0; display: flex; justify-content: space-between; align-items: center; }
    .tooltip { position: relative; display: inline-block; cursor: help; border-bottom: 1px dotted #ff6600; }
    .tooltip .tooltiptext {
        visibility: hidden; width: 200px; background-color: #262730; color: #fff; text-align: center;
        border-radius: 6px; padding: 5px; position: absolute; z-index: 1; bottom: 125%; left: 50%;
        margin-left: -100px; opacity: 0; transition: opacity 0.3s; font-size: 0.8rem;
    }
    .tooltip:hover .tooltiptext { visibility: visible; opacity: 1; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. INICIALIZAÇÃO DO ESTADO PERMANENTE ---
if 'sel_i' not in st.session_state: st.session_state.sel_i = list(servicos_db.keys())
if 'sel_m' not in st.session_state: st.session_state.sel_m = [list(sistemas_db.keys())[0]] if sistemas_db else []

# Cria as chaves de blindagem para cada produto da planilha
for nome in {**sistemas_db, **servicos_db, **despesas_db}.keys():
    if f"perm_val_{nome}" not in st.session_state:
        st.session_state[f"perm_val_{nome}"] = 120 if "Treinamento" in nome else 1

# --- 4. MENU LATERAL ---
with st.sidebar:
    if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=200)
    st.markdown('<span class="sidebar-label">Configurações</span>', unsafe_allow_html=True)
    perfil_venda = st.selectbox("Perfil", ["Executivo (Rua)", "CS (Base)"])
    modo_apresentacao = st.toggle("Modo Apresentação")
    desc = st.number_input("Desconto Mensal (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.1)
    exibir_detalhe_desc = st.toggle("Exibir Desconto", value=True)
    faturamento = st.selectbox("Faturamento", ["Imediato", "30 dias", "60 dias", "Após a implantação"])
    parcelas = st.selectbox("Parcelamento Setup", [1, 2, 3, 4, 5, 6], index=3)

# --- 5. TELA GERADOR DE PROPOSTA ---
if not modo_apresentacao:
    st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)
    st.markdown("---")
    col_i, col_m, col_d = st.columns(3) if perfil_venda == "Executivo (Rua)" else (*st.columns(2), None)
    
    with col_i:
        st.markdown('<div class="section-header"><span class="section-title">IMPLANTAÇÃO</span></div>', unsafe_allow_html=True)
        st.session_state.sel_i = st.multiselect("Serviços", list(servicos_db.keys()), default=st.session_state.sel_i)
        for i in st.session_state.sel_i:
            vu = float(servicos_db[i]["Valor"])
            st.number_input(f"Horas: {i} (R$ {vu:,.2f}/h)", min_value=0, 
                            value=st.session_state[f"perm_val_{i}"], 
                            key=f"tmp_val_{i}", 
                            on_change=sync_state, args=(f"perm_val_{i}", f"tmp_val_{i}"))

    with col_m:
        st.markdown('<div class="section-header"><span class="section-title">MENSALIDADES</span></div>', unsafe_allow_html=True)
        st.session_state.sel_m = st.multiselect("Produtos", list(sistemas_db.keys()), default=st.session_state.sel_m)
        for i in st.session_state.sel_m:
            vu = float(sistemas_db[i]["Valor"])
            st.number_input(f"Qtd: {i} (R$ {vu:,.2f}/un)", min_value=0, 
                            value=st.session_state[f"perm_val_{i}"], 
                            key=f"tmp_val_{i}", 
                            on_change=sync_state, args=(f"perm_val_{i}", f"tmp_val_{i}"))

    if col_d:
        with col_d:
            st.markdown('<div class="section-header"><span class="section-title">DESPESAS</span></div>', unsafe_allow_html=True)
            for i in despesas_db.keys():
                vu = float(despesas_db[i]["Valor"])
                st.number_input(f"{i} (R$ {vu:,.2f}/un)", min_value=0, 
                                value=st.session_state[f"perm_val_{i}"], 
                                key=f"tmp_val_{i}", 
                                on_change=sync_state, args=(f"perm_val_{i}", f"tmp_val_{i}"))

# --- CÁLCULOS FINAIS ---
t_imp, t_men_bruto, t_desp = 0, 0, 0
lista_i, lista_m, lista_d = [], [], []

for i in st.session_state.sel_i:
    qtd = st.session_state[f"perm_val_{i}"]
    val = float(servicos_db[i]["Valor"])
    t_imp += qtd * val
    lista_i.append((i, qtd, val, servicos_db[i]["Descricao"]))

for i in st.session_state.sel_m:
    qtd = st.session_state[f"perm_val_{i}"]
    val = float(sistemas_db[i]["Valor"])
    t_men_bruto += qtd * val
    lista_m.append((i, qtd, val, sistemas_db[i]["Descricao"]))

for i in despesas_db.keys():
    qtd = st.session_state[f"perm_val_{i}"]
    if qtd > 0:
        val = float(despesas_db[i]["Valor"])
        t_desp += qtd * val
        lista_d.append((i, qtd, val, despesas_db[i]["Descricao"]))

t_men_liq = t_men_bruto * (1 - (desc/100))

# --- EXIBIÇÃO DO DETALHAMENTO ---
st.markdown("<h2 style='text-align:center; font-weight:800; margin-top:30px;'>DETALHAMENTO DA PROPOSTA</h2>", unsafe_allow_html=True)
res_cols = st.columns(3) if perfil_venda == "Executivo (Rua)" else st.columns([1, 2, 2, 1])[1:3]

with res_cols[0]:
    html_i = "".join([f"<li><span><span class='tooltip'>{i}<span class='tooltiptext'>{d}</span></span></span><span class='item-detalhe'>{q}h x R$ {v:,.2f}</span></li>" for i, q, v, d in lista_i])
    st.markdown(f'<div class="resumo-card"><span class="resumo-label">Setup</span><div class="resumo-valor">R$ {t_imp:,.2f}</div><div style="font-weight:bold;">{parcelas}x R$ {t_imp/parcelas:,.2f}</div><div class="resumo-subtitulo">SERVIÇOS</div><ul class="lista-itens">{html_i}</ul></div>', unsafe_allow_html=True)

with res_cols[1]:
    html_m = "".join([f"<li><span><span class='tooltip'>{i}<span class='tooltiptext'>{d}</span></span></span><span class='item-detalhe'>{q} Un x R$ {v:,.2f}</span></li>" for i, q, v, d in lista_m])
    desc_info = f'<div style="color: #2e7d32; font-weight: bold;">Desconto: {desc:,.2f}%</div>' if exibir_detalhe_desc and desc > 0 else '<div style="height:21px"></div>'
    st.markdown(f'<div class="resumo-card" style="border-top-color: #2e7d32;"><span class="resumo-label">Mensalidade</span><div class="resumo-valor" style="color: #2e7d32;">R$ {t_men_liq:,.2f}</div>{desc_info}<div style="font-weight:bold; font-size: 0.9rem; margin-top:5px;">Faturamento: {faturamento}</div><div class="resumo-subtitulo">SISTEMAS</div><ul class="lista-itens">{html_m}</ul></div>', unsafe_allow_html=True)

if perfil_venda == "Executivo (Rua)":
    with res_cols[2]:
        html_d = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{q} x R$ {v:,.2f}</span></li>" for i, q, v, d in lista_d])
        st.markdown(f'<div class="resumo-card" style="border-top-color: #1976d2;"><span class="resumo-label">Despesas</span><div class="resumo-valor" style="color: #1976d2;">R$ {t_desp:,.2f}</div><div style="color:#d32f2f; font-weight:bold; font-size:0.85rem;">Faturadas no término</div><div class="resumo-subtitulo">LOGÍSTICA</div><ul class="lista-itens">{html_d}</ul></div>', unsafe_allow_html=True)
