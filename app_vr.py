import streamlit as st
import pandas as pd
import os
import textwrap

# 1. Configuração da Página
st.set_page_config(page_title="VR Software | Sales Intelligence", layout="wide")

# --- LINK DO GOOGLE SHEETS (VERSÃO CSV) ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTgmdf_FgFd91dkm5zoD0l6l2ailLhCsEV-3pyFsQxRzoyNw2E96eQQoCYkfxHitA9oCIvfaI30-k-2/pub?output=csv"

# --- FUNÇÃO DE LIMPEZA DE NÚMEROS ---
def limpar_valor(valor):
    if pd.isna(valor) or str(valor).strip() == "":
        return 0.0
    try:
        v = str(valor).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        return float(v)
    except:
        return 0.0

# --- FUNÇÃO DE SINCRONIZAÇÃO ---
def sync_state(key_permanente, key_widget):
    st.session_state[key_permanente] = st.session_state[key_widget]

# --- CARREGAMENTO DE DADOS NORMALIZADO ---
@st.cache_data(ttl=60) # Reduzi para 1 minuto para você testar as mudanças rápido
def carregar_dados_vendas():
    try:
        df = pd.read_csv(SHEET_URL)
        # 1. Limpa nomes das colunas
        df.columns = [c.strip() for c in df.columns]
        
        # 2. Limpa e normaliza a coluna 'Tipo' (remove espaços e põe em minúsculo)
        if 'Tipo' in df.columns:
            df['Tipo_Norm'] = df['Tipo'].astype(str).str.strip().str.lower()
        
        # 3. Limpa valores numéricos
        df['Valor'] = df['Valor'].apply(limpar_valor)
        
        # 4. Filtros usando a versão normalizada (aceita 'sistema', 'Sistema', 'SISTEMA')
        # Também incluímos variações comuns para 'Servico'
        sistemas = df[df['Tipo_Norm'] == 'sistema'].set_index('Produto').to_dict('index')
        servicos = df[df['Tipo_Norm'].isin(['servico', 'serviço'])].set_index('Produto').to_dict('index')
        despesas = df[df['Tipo_Norm'] == 'despesa'].set_index('Produto').to_dict('index')
        
        return sistemas, servicos, despesas, df.set_index('Produto').to_dict('index'), df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return {}, {}, {}, {}, pd.DataFrame()

sistemas_db, servicos_db, despesas_db, full_db, df_bruto = carregar_dados_vendas()

# --- DIAGNÓSTICO (Caso esteja vazio) ---
if not sistemas_db and not servicos_db and not df_bruto.empty:
    st.warning("⚠️ Atenção: A planilha foi lida, mas nenhum item foi classificado como 'Sistema' ou 'Servico'.")
    with st.expander("Verificar nomes encontrados na coluna 'Tipo'"):
        st.write("Estes são os tipos que você escreveu na planilha:")
        st.write(df_bruto['Tipo'].unique().tolist())
        st.write("Certifique-se de usar: 'Sistema', 'Servico' ou 'Despesa'.")

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
    .item-detalhe { color: #333; font-size: 1.05rem; font-weight: 700; background-color: #fcfcfc; padding: 2px 8px; border-radius: 4px; }
    .section-header { background: linear-gradient(90deg, #ff6600 0%, #ff944d 100%); padding: 8px 15px; border-radius: 5px; margin-bottom: 15px; margin-top: 20px; }
    .section-title { color: #ffffff; font-size: 1.1rem; font-weight: bold; margin: 0; }
    .lista-itens { list-style-type: none; padding-left: 0; margin-top: 10px; }
    .lista-itens li { padding: 10px 0; border-bottom: 1px dashed #e0e0e0; display: flex; justify-content: space-between; align-items: center; }
    .tooltip { position: relative; display: inline-block; cursor: help; border-bottom: 1px dotted #ff6600; }
    .tooltip .tooltiptext {
        visibility: hidden; width: 250px; background-color: #262730; color: #fff; text-align: left;
        border-radius: 8px; padding: 10px; position: absolute; z-index: 10; bottom: 125%; left: 50%;
        margin-left: -125px; opacity: 0; transition: opacity 0.3s; font-size: 0.85rem; line-height: 1.4;
    }
    .tooltip:hover .tooltiptext { visibility: visible; opacity: 1; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. INICIALIZAÇÃO DO ESTADO ---
if 'sel_i' not in st.session_state: st.session_state.sel_i = []
if 'sel_m' not in st.session_state: st.session_state.sel_m = []

for nome in full_db.keys():
    if f"perm_val_{nome}" not in st.session_state:
        st.session_state[f"perm_val_{nome}"] = 120 if "Treinamento" in str(nome) else 1

# --- 4. MENU LATERAL ---
with st.sidebar:
    if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=200)
    tela = st.radio("Navegação:", ["Gerador de Proposta", "Consulta de Preço"])
    st.write("---")

    if tela == "Gerador de Proposta":
        st.markdown('<span class="sidebar-label">Configurações</span>', unsafe_allow_html=True)
        perfil_venda = st.selectbox("Perfil", ["Executivo (Rua)", "CS (Base)"])
        modo_apresentacao = st.toggle("Modo Apresentação")
        desc = st.number_input("Desconto Mensal (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.1)
        faturamento = st.selectbox("Faturamento", ["Imediato", "30 dias", "60 dias", "Após a implantação"])
        parcelas = st.selectbox("Parcelamento Setup", [1, 2, 3, 4, 5, 6], index=3)

# --- 5. TELA GERADOR DE PROPOSTA ---
if tela == "Gerador de Proposta":
    if not modo_apresentacao:
        st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)
        st.markdown("---")
        col_i, col_m, col_d = st.columns(3) if perfil_venda == "Executivo (Rua)" else (*st.columns(2), None)
        
        with col_i:
            st.markdown('<div class="section-header"><span class="section-title">IMPLANTAÇÃO</span></div>', unsafe_allow_html=True)
            opcoes_i = list(servicos_db.keys())
            default_i = [s for s in st.session_state.sel_i if s in opcoes_i]
            st.session_state.sel_i = st.multiselect("Selecione os Serviços:", opcoes_i, default=default_i)
            
            for i in st.session_state.sel_i:
                vu = servicos_db[i]["Valor"]
                st.number_input(f"Horas: {i} (R$ {vu:,.2f}/h)", min_value=0, 
                                value=st.session_state[f"perm_val_{i}"], 
                                key=f"tmp_val_{i}", 
                                on_change=sync_state, args=(f"perm_val_{i}", f"tmp_val_{i}"))

        with col_m:
            st.markdown('<div class="section-header"><span class="section-title">MENSALIDADES</span></div>', unsafe_allow_html=True)
            opcoes_m = list(sistemas_db.keys())
            default_m = [s for s in st.session_state.sel_m if s in opcoes_m]
            st.session_state.sel_m = st.multiselect("Selecione os Produtos:", opcoes_m, default=default_m)
            
            for i in st.session_state.sel_m:
                vu = sistemas_db[i]["Valor"]
                st.number_input(f"Qtd: {i} (R$ {vu:,.2f}/un)", min_value=0, 
                                value=st.session_state[f"perm_val_{i}"], 
                                key=f"tmp_val_{i}", 
                                on_change=sync_state, args=(f"perm_val_{i}", f"tmp_val_{i}"))

        if col_d:
            with col_d:
                st.markdown('<div class="section-header"><span class="section-title">DESPESAS</span></div>', unsafe_allow_html=True)
                for i in despesas_db.keys():
                    vu = despesas_db[i]["Valor"]
                    st.number_input(f"{i} (R$ {vu:,.2f}/un)", min_value=0, 
                                    value=st.session_state[f"perm_val_{i}"], 
                                    key=f"tmp_val_{i}", 
                                    on_change=sync_state, args=(f"perm_val_{i}", f"tmp_val_{i}"))

    # --- CÁLCULOS ---
    t_imp, t_men_bruto, t_desp = 0.0, 0.0, 0.0
    lista_i, lista_m, lista_d = [], [], []

    for i in st.session_state.sel_i:
        if i in servicos_db:
            qtd = st.session_state[f"perm_val_{i}"]
            val = servicos_db[i]["Valor"]
            t_imp += qtd * val
            lista_i.append((i, qtd, val, servicos_db[i].get("Descricao", "")))

    for i in st.session_state.sel_m:
        if i in sistemas_db:
            qtd = st.session_state[f"perm_val_{i}"]
            val = sistemas_db[i]["Valor"]
            t_men_bruto += qtd * val
            lista_m.append((i, qtd, val, sistemas_db[i].get("Descricao", "")))

    for i in despesas_db.keys():
        qtd = st.session_state[f"perm_val_{i}"]
        if qtd > 0:
            val = despesas_db[i]["Valor"]
            t_desp += qtd * val
            lista_d.append((i, qtd, val, ""))

    t_men_liq = t_men_bruto * (1 - (desc/100))

    # --- CARDS DE RESUMO ---
    st.markdown("<h2 style='text-align:center; font-weight:800; margin-top:30px;'>RESUMO DA PROPOSTA</h2>", unsafe_allow_html=True)
    res_cols = st.columns(3) if perfil_venda == "Executivo (Rua)" else st.columns([1, 2, 2, 1])[1:3]

    with res_cols[0]:
        html_i = "".join([f"<li><span><span class='tooltip'>{i}<span class='tooltiptext'>{d}</span></span></span><span class='item-detalhe'>{q}h x R$ {v:,.2f}</span></li>" for i, q, v, d in lista_i])
        st.markdown(f'<div class="resumo-card"><span class="resumo-label">Investimento Setup</span><div class="resumo-valor">R$ {t_imp:,.2f}</div><div style="font-weight:bold;">{parcelas}x de R$ {t_imp/parcelas:,.2f}</div><div class="resumo-subtitulo">SERVIÇOS</div><ul class="lista-itens">{html_i if html_i else "<li>Nenhum selecionado</li>"}</ul></div>', unsafe_allow_html=True)

    with res_cols[1]:
        html_m = "".join([f"<li><span><span class='tooltip'>{i}<span class='tooltiptext'>{d}</span></span></span><span class='item-detalhe'>{q} un x R$ {v:,.2f}</span></li>" for i, q, v, d in lista_m])
        st.markdown(f'<div class="resumo-card" style="border-top-color: #2e7d32;"><span class="resumo-label">Mensalidade Líquida</span><div class="resumo-valor" style="color: #2e7d32;">R$ {t_men_liq:,.2f}</div><div style="font-weight:bold; color:#555;">Faturamento: {faturamento}</div><div class="resumo-subtitulo">SISTEMAS</div><ul class="lista-itens">{html_m if html_m else "<li>Nenhum selecionado</li>"}</ul></div>', unsafe_allow_html=True)

    if perfil_venda == "Executivo (Rua)":
        with res_cols[2]:
            html_d = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{q} x R$ {v:,.2f}</span></li>" for i, q, v, d in lista_d])
            st.markdown(f'<div class="resumo-card" style="border-top-color: #1976d2;"><span class="resumo-label">Despesas Logísticas</span><div class="resumo-valor" style="color: #1976d2;">R$ {t_desp:,.2f}</div><div class="resumo-subtitulo">LOGÍSTICA</div><ul class="lista-itens">{html_d if html_d else "<li>Sem despesas</li>"}</ul></div>', unsafe_allow_html=True)

else:
    st.markdown('<h1 class="hero-title">ANÁLISE TÉCNICA</h1>', unsafe_allow_html=True)
    st.info("Utilize esta tela para consultar detalhes técnicos de cada produto da planilha.")
