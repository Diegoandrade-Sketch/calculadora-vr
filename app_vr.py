import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import urllib.parse
import os
import re

# ==========================================
# CONFIGURAÇÕES INICIAIS E SEGURANÇA
# ==========================================
st.set_page_config(page_title="VR Software | Sales Intelligence", layout="wide")

APP_VERSION = "v1.1.3 - Intel Engine Active"
ADMIN_PASS_REQUIRED = "333666"

try:
    DB_USER = st.secrets["DB_USER"]
    DB_PASS = st.secrets["DB_PASS"]
    DB_HOST = st.secrets["DB_HOST"]
    DB_PORT = st.secrets["DB_PORT"]
    DB_NAME = st.secrets["DB_NAME"]
    DB_PASS_ENCODED = urllib.parse.quote_plus(DB_PASS)
    CONN_STR = f"postgresql://{DB_USER}:{DB_PASS_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
except Exception:
    CONN_STR = None

# ==========================================
# BLOCO ESPECÍFICO: LOGÍCA DE TRANSFORMAÇÃO (NOVO)
# ==========================================
def processar_inteligencia_vendas(df):
    """
    Transforma os dados brutos do Bitrix nas regras de negócio da VR Software.
    """
    # 1. Normalização de Colunas e Duplicatas
    df.columns = [str(c).strip().lower() for c in df.columns]
    if 'title' in df.columns:
        df = df.rename(columns={'title': 'produto'})
    df = df.drop_duplicates(subset=['produto'], keep='last')

    # 2. Inicialização de colunas de suporte
    df['tipo'] = ""
    df['horas_padrao'] = 0.0
    df['adesao_vinculada'] = 0.0
    df['valor_hora_implantacao'] = 125.0  # Valor padrão sugerido

    # 3. Classificação por typeproductid e Regras de Texto
    # 604 = Sistemas | 606 = Serviços/Despesas
    for idx, row in df.iterrows():
        tid = row.get('typeproductid', 0)
        nome = str(row['produto']).lower()
        
        # Regra de Sistemas (Recorrentes)
        if tid == 604:
            df.at[idx, 'tipo'] = 'sist'
            
        # Regra de Serviços e Despesas
        elif tid == 606:
            if any(palavra in nome for palavra in ['despesa', 'km', 'hospedagem', 'deslocamento']):
                df.at[idx, 'tipo'] = 'desp'
            else:
                df.at[idx, 'tipo'] = 'serv'
                # Extração de Horas: pega da coluna qtd_min do banco
                df.at[idx, 'horas_padrao'] = float(row.get('qtd_min', 0))

    # 4. Motor de Vínculo de Adesão (Match Inteligente)
    # Identifica linhas de adesão e as "teletransporta" para dentro do sistema pai
    adesoes = df[df['produto'].str.contains('Adesao|Adesão', case=False, na=False)].copy()
    
    for _, ad_row in adesoes.iterrows():
        # Limpa o nome para achar o pai (Ex: "Adesão VR ERP" -> "vrerp")
        chave_adesao = re.sub(r'ades[ãa]o', '', ad_row['produto'], flags=re.IGNORECASE).strip().lower()
        chave_adesao = re.sub(r'\s+', '', chave_adesao)
        
        # Procura nos sistemas (sist) quem combina com essa chave
        for idx, sist_row in df[df['tipo'] == 'sist'].iterrows():
            chave_sistema = str(sist_row['produto']).strip().lower()
            chave_sistema = re.sub(r'\s+', '', chave_sistema)
            
            if chave_adesao in chave_sistema or chave_sistema in chave_adesao:
                df.at[idx, 'adesao_vinculada'] = float(ad_row['valor'])
                break

    # 5. Limpeza Final: Remove as linhas de Adesão isoladas para não poluir a tela
    df = df[~df['produto'].str.contains('Adesao|Adesão', case=False, na=False)]
    
    return df

# ==========================================
# FUNÇÕES DE UI E FORMATAÇÃO (MANTIDAS v1.1.2)
# ==========================================
def f_br(valor):
    if valor == 0: return "0,00"
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def f_pct(valor):
    return str(valor).replace('.', ',')

def limpar_valor(valor):
    if pd.isna(valor) or str(valor).strip() == "": return 0.0
    v = str(valor).replace('R$', '').replace(' ', '').strip()
    if ',' in v and '.' in v: v = v.replace('.', '').replace(',', '.')
    elif ',' in v: v = v.replace(',', '.')
    try: return float(v)
    except: return 0.0

def sync_state(key_permanente, key_widget):
    st.session_state[key_permanente] = st.session_state[key_widget]

@st.cache_data(ttl=60)
def carregar_dados_vendas():
    status_msg, status_cor, df_raw = "🔴 Desconectado", "#ef4444", pd.DataFrame()
    try:
        if CONN_STR:
            engine = create_engine(CONN_STR)
            df_raw = pd.read_sql("SELECT * FROM product", engine)
            
            # CHAMA O BLOCO DE INTELIGÊNCIA ISOLADO
            df_tratado = processar_inteligencia_vendas(df_raw)
            
            status_msg, status_cor = "PostgreSQL Conectado", "#22c55e"
            
            full = df_tratado.set_index('produto').to_dict('index')
            sist = {k: v for k, v in full.items() if v['tipo'] == 'sist'}
            serv = {k: v for k, v in full.items() if v['tipo'] == 'serv'}
            desp = {k: v for k, v in full.items() if v['tipo'] == 'desp'}
            
            return sist, serv, desp, full, status_msg, status_cor, df_raw
    except Exception as e:
        st.error(f"Erro: {e}")
    return {}, {}, {}, {}, status_msg, status_cor, df_raw

sistemas_db, servicos_db, despesas_db, full_db, db_status, db_cor, df_raw = carregar_dados_vendas()

# ==========================================
# ESTILIZAÇÃO CSS (MANTIDA v1.1.2)
# ==========================================
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #ffffff 0%, #fff5ed 100%); }
    .hero-title { color: #262730; font-size: 4.5rem; font-weight: 900; margin: 0; line-height: 1; text-transform: uppercase; letter-spacing: -3px; }
    .mapeamento-container { background-color: #ffffff; border-left: 10px solid #ff6600; padding: 20px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .resumo-card { background-color: #ffffff; border: 1px solid #f0f0f0; border-top: 8px solid #ff6600; padding: 25px; border-radius: 8px; min-height: 450px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); display: flex; flex-direction: column; }
    .resumo-valor { color: #ff6600; font-size: 2.3rem; font-weight: 900; margin-bottom: 5px; }
    .item-detalhe { color: #333; font-size: 0.82rem; font-weight: 600; background-color: #fcfcfc; padding: 2px 8px; border-radius: 4px; border: 1px solid #eee; white-space: nowrap; }
    .section-header { background: linear-gradient(90deg, #ff6600 0%, #ff944d 100%); padding: 8px 15px; border-radius: 5px; margin-bottom: 15px; margin-top: 20px; }
    .section-title { color: #ffffff; font-size: 1.1rem; font-weight: bold; margin: 0; }
    .lista-itens { list-style-type: none; padding-left: 0; margin-top: 10px; flex-grow: 1; }
    .lista-itens li { padding: 8px 0; border-bottom: 1px dashed #e0e0e0; display: flex; justify-content: space-between; align-items: center; gap: 15px; }
    .lista-itens li span:first-child { font-weight: bold; font-size: 0.88rem; color: #444; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# ESTADO GLOBAL E SIDEBAR (MANTIDOS v1.1.2)
# ==========================================
init_state = {
    'm_combo': "Montar Manualmente", 'm_pdv_conv': 0, 'm_pdv_touch': 0, 'm_pdv_self': 0, 'm_semanas': 0, 'm_mobile': 0,
    'm_tef': "Não utiliza", 'm_migracao': False, 'm_ecommerce': False, 'm_app': False, 'm_connect': False,
    'm_erp_pro': False, 'm_xml': False, 'm_escopo': False, 'm_controller': False, 'm_cartaz': False, 'm_masterfisco': False, 'm_backup': False
}
for k, v in init_state.items():
    if k not in st.session_state: st.session_state[k] = v
if 'sel_i' not in st.session_state: st.session_state.sel_i = []
if 'sel_m' not in st.session_state: st.session_state.sel_m = []
if 'sel_d' not in st.session_state: st.session_state.sel_d = []

for nome in full_db.keys():
    if f"perm_val_{nome}" not in st.session_state: st.session_state[f"perm_val_{nome}"] = 0

def limpar_tudo():
    for k, v in init_state.items(): st.session_state[k] = v
    st.session_state.sel_i, st.session_state.sel_m, st.session_state.sel_d = [], [], []
    for nome in full_db.keys(): st.session_state[f"perm_val_{nome}"] = 0

with st.sidebar:
    if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=180)
    tela = st.radio("Navegação:", ["Gerador de Proposta", "Consulta de Preço", "Painel Admin"])
    
    if tela == "Gerador de Proposta":
        st.write("---")
        mapeamento_ativo = st.toggle("Mapeamento Inteligente", value=False)
        perfil_venda = st.selectbox("Perfil do Cliente", ["Executivo (Rua)", "CS (Base)"])
        desc = st.number_input("Desconto (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.5)
        faturamento_sistema = st.selectbox("Início Mensalidade", ["Na assinatura", "30 dias", "60 dias", "Após implantação"])
        parcelas_setup = st.selectbox("Parcelas Setup", [1, 2, 3, 4, 5, 6], index=3)

    st.markdown("<br>" * 3, unsafe_allow_html=True)
    st.markdown(f'''
        <hr style="margin: 10px 0; border-color: #ddd;">
        <div style="font-size: 0.8rem; color: #555;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                <div style="width: 10px; height: 10px; border-radius: 50%; background-color: {db_cor};"></div>
                <b>DB:</b> {db_status}
            </div>
            <div><b>Versão:</b> {APP_VERSION}</div>
        </div>
    ''', unsafe_allow_html=True)

# ==========================================
# TELAS (LÓGICA MANTIDA v1.1.2)
# ==========================================
if tela == "Painel Admin":
    st.markdown('<h1 class="hero-title">BACKOFFICE</h1>', unsafe_allow_html=True)
    senha_admin = st.text_input("Introduza a senha de acesso:", type="password")
    if senha_admin == ADMIN_PASS_REQUIRED:
        st.success("Acesso Autorizado.")
        if not df_raw.empty:
            st.write("Dados Crus do Bitrix (Sem tratamento):")
            st.dataframe(df_raw, use_container_width=True)
    elif senha_admin != "": st.error("Senha Incorreta.")

elif tela == "Gerador de Proposta":
    def aplicar_mapeamento():
        pdv_map = {"VR PDV Convencional": st.session_state.m_pdv_conv, "PDV Touchscreen": st.session_state.m_pdv_touch, "PDV Selfcheckout": st.session_state.m_pdv_self}
        for p, qtd in pdv_map.items():
            if p in sistemas_db:
                st.session_state[f"perm_val_{p}"] = qtd
                if qtd > 0 and p not in st.session_state.sel_m: st.session_state.sel_m.append(p)
        
        sem = st.session_state.m_semanas
        serv_map = {"Implantação e Treinamento": sem * 44, "Migração Banco de Dados": 8 if st.session_state.m_migracao else 0}
        for s_item, s_horas in serv_map.items():
            if s_item in servicos_db:
                st.session_state[f"perm_val_{s_item}"] = s_horas
                if s_horas > 0 and s_item not in st.session_state.sel_i: st.session_state.sel_i.append(s_item)

    st.markdown('<h1 class="hero-title">PROPOSTA COMERCIAL</h1>', unsafe_allow_html=True)
    if mapeamento_ativo:
        st.markdown('<div class="mapeamento-container"><h4>🛒 Mapeamento da Operação</h4></div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.number_input("PDV Convencional", min_value=0, key="tmp_pdv_conv", value=st.session_state.m_pdv_conv, on_change=sync_state, args=("m_pdv_conv", "tmp_pdv_conv"))
            st.number_input("PDV Touch", min_value=0, key="tmp_pdv_touch", value=st.session_state.m_pdv_touch, on_change=sync_state, args=("m_pdv_touch", "tmp_pdv_touch"))
        with c2:
            st.number_input("Semanas", min_value=0, key="tmp_semanas", value=st.session_state.m_semanas, on_change=sync_state, args=("m_semanas", "tmp_semanas"))
            st.checkbox("Migração de Banco?", key="tmp_migracao", value=st.session_state.m_migracao, on_change=sync_state, args=("m_migracao", "tmp_migracao"))
        with c3:
            st.button("✨ Aplicar Inteligência", on_click=aplicar_mapeamento, use_container_width=True)
            st.button("🗑️ Limpar Tudo", on_click=limpar_tudo, use_container_width=True)
    
    col_i, col_m, col_d = st.columns(3) if perfil_venda == "Executivo (Rua)" else (*st.columns(2), None)
    with col_i:
        st.markdown('<div class="section-header"><span class="section-title">IMPLANTAÇÃO E SERVIÇOS</span></div>', unsafe_allow_html=True)
        st.session_state.sel_i = st.multiselect("Serviços", list(servicos_db.keys()), default=[s for s in st.session_state.sel_i if s in servicos_db])
        for i in st.session_state.sel_i:
            st.number_input(f"{i}", min_value=0, key=f"tmp_i_{i}", value=st.session_state[f"perm_val_{i}"], on_change=sync_state, args=(f"perm_val_{i}", f"tmp_i_{i}"))
    with col_m:
        st.markdown('<div class="section-header"><span class="section-title">MENSALIDADES SISTEMAS</span></div>', unsafe_allow_html=True)
        st.session_state.sel_m = st.multiselect("Sistemas", list(sistemas_db.keys()), default=[s for s in st.session_state.sel_m if s in sistemas_db])
        for i in st.session_state.sel_m:
            st.number_input(f"{i}", min_value=0, key=f"tmp_m_{i}", value=st.session_state[f"perm_val_{i}"], on_change=sync_state, args=(f"perm_val_{i}", f"tmp_m_{i}"))

    st.markdown("<h2 style='text-align:center; font-weight:800; margin-top:30px;'>RESUMO DO INVESTIMENTO</h2>", unsafe_allow_html=True)
    res_cols = st.columns(3) if perfil_venda == "Executivo (Rua)" else st.columns([1, 2, 2, 1])[1:3]
    
    total_setup, html_setup = 0.0, ""
    v_hora_base = servicos_db.get("Implantação e Treinamento", {}).get("valor", 125.0)

    for s_nome in st.session_state.sel_i:
        horas = st.session_state[f"perm_val_{s_nome}"]
        if horas > 0:
            v_item = horas * servicos_db[s_nome].get('valor', 0)
            total_setup += v_item
            html_setup += f"<li><span>{s_nome}</span><span class='item-detalhe'>{horas}h x R$ {f_br(servicos_db[s_nome].get('valor', 0))}</span></li>"

    for m_nome in st.session_state.sel_m:
        d = full_db.get(m_nome, {})
        h_pad, val_ads = d.get('horas_padrao', 0), d.get('adesao_vinculada', 0.0)
        if h_pad > 0:
            total_setup += (h_pad * v_hora_base)
            html_setup += f"<li><span>Implantação {m_nome}</span><span class='item-detalhe'>{h_pad}h x R$ {f_br(v_hora_base)}</span></li>"
        if val_ads > 0:
            total_setup += val_ads
            html_setup += f"<li><span>Taxa de Adesão {m_nome}</span><span class='item-detalhe'>R$ {f_br(val_ads)}</span></li>"

    with res_cols[0]:
        st.markdown(f'''<div class="resumo-card"><span class="resumo-label">Investimento Implantação (Setup)</span><div class="resumo-valor">R$ {f_br(total_setup)}</div><div style="font-weight:bold;">{parcelas_setup}x de R$ {f_br(total_setup/parcelas_setup)}</div><div class="resumo-subtitulo">DETALHAMENTO SETUP</div><ul class="lista-itens">{html_setup if html_setup else "<li>Nenhum item</li>"}</ul></div>''', unsafe_allow_html=True)
    with res_cols[1]:
        t_liq = sum(st.session_state[f"perm_val_{i}"] * sistemas_db[i].get("valor", 0) for i in st.session_state.sel_m if i in sistemas_db) * (1 - (desc/100))
        html_m = "".join([f"<li><span>{i}</span><span class='item-detalhe'>{st.session_state[f'perm_val_{i}']} un x R$ {f_br(sistemas_db[i].get('valor', 0))}</span></li>" for i in st.session_state.sel_m if i in sistemas_db])
        st.markdown(f'''<div class="resumo-card" style="border-top-color:#2e7d32;"><span class="resumo-label">Manutenção Mensal</span><div class="resumo-valor" style="color:#2e7d32;">R$ {f_br(t_liq)}</div><div style="font-weight:bold; font-size: 0.9rem;">Início: {faturamento_sistema}</div><div class="resumo-subtitulo">SISTEMAS</div><ul class="lista-itens">{html_m if html_m else "<li>Nenhum</li>"}</ul></div>''', unsafe_allow_html=True)

elif tela == "Consulta de Preço":
    st.markdown('<h1 class="hero-title">ANÁLISE TÉCNICA</h1>')
    if full_db:
        p_sel = st.selectbox("Selecione o produto:", sorted(list(full_db.keys())))
        if p_sel:
            d = full_db[p_sel]
            st.json(d)
