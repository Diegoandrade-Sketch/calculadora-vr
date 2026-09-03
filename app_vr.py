import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from sqlalchemy import create_engine, text
import urllib.parse
import os
import json
import re
import datetime
import base64
import calendar
import html
import hashlib

# ==========================================
# CONFIGURAÇÕES INICIAIS E CONTROLE DE ESTADO
# ==========================================
st.set_page_config(page_title="VR Software | Sales Intelligence", layout="wide")

APP_VERSION = "v6.3.1 - Security & Finance Hub"
CACHE_FILE = "cache_vr.json"

if 'form_rc' not in st.session_state: st.session_state.form_rc = 0

if 'data_vault' not in st.session_state:
    st.session_state.data_vault = {
        'sel_m': [], 'sel_i': [], 'sel_d': [], 'auto_added': [],
        'quantidades': {}, 'setup_sistemas': {}, 'descontos_itens': {},
        'despesas_valores': {}, 'negociar': {},
        'mapeamento': {
            'm_combo': "Montar Manualmente", 'm_pdv_conv': 0, 'm_pdv_touch': 0, 'm_pdv_self': 0, 'm_semanas': 0, 'm_mobile': 0,
            'm_tef': "Nao utiliza", 'm_migracao': False, 'm_ecommerce': False, 'm_app': False, 'm_connect': False,
            'm_erp_pro': False, 'm_xml': False, 'm_escopo': False, 'm_controller': False, 'm_cartaz': False, 'm_masterfisco': False, 'm_backup': False,
        }
    }

if 'perma_nome_cliente' not in st.session_state: st.session_state.perma_nome_cliente = ""
if 'perma_cnpj_cliente' not in st.session_state: st.session_state.perma_cnpj_cliente = ""
if 'aba_atual' not in st.session_state: st.session_state.aba_atual = "Início"
if 'proposta_carregada_id' not in st.session_state: st.session_state.proposta_carregada_id = None
if 'show_digital_proposal' not in st.session_state: st.session_state.show_digital_proposal = False
if 'show_welcome_pack' not in st.session_state: st.session_state.show_welcome_pack = False
if 'fin_sim_ativa' not in st.session_state: st.session_state.fin_sim_ativa = False
if 'has_unsaved_changes' not in st.session_state: st.session_state.has_unsaved_changes = False
if 'modo_apresentacao' not in st.session_state: st.session_state.modo_apresentacao = False

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
# MOTOR DE BANCO DE DADOS E SEGURANÇA
# ==========================================
@st.cache_resource
def get_db_engine():
    if CONN_STR:
        return create_engine(CONN_STR, pool_pre_ping=True, pool_size=10, max_overflow=20)
    return None

def get_senha_hash(senha):
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()

# ==========================================
# FUNÇÕES DE FORMATAÇÃO E PARSERS
# ==========================================
def f_br(valor):
    if pd.isna(valor) or valor == 0: return "0,00"
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def f_pct(valor):
    return str(valor).replace('.', ',')

def parse_currency(val_str):
    if not val_str: return 0.0
    v = str(val_str).upper().replace('R$', '').strip()
    if '.' in v and ',' in v: v = v.replace('.', '').replace(',', '.')
    elif ',' in v: v = v.replace(',', '.')
    v = re.sub(r'[^\d.]', '', v)
    try: return float(v)
    except: return 0.0

def mark_unsaved():
    st.session_state.has_unsaved_changes = True

def get_logo_base64():
    if os.path.exists("logo_vr.png"):
        with open("logo_vr.png", "rb") as img_file: return base64.b64encode(img_file.read()).decode("utf-8")
    return ""

def atualiza_nome_cliente(): 
    st.session_state.perma_nome_cliente = st.session_state.widget_nome
    mark_unsaved()

def atualiza_cnpj_cliente():
    raw = str(st.session_state.widget_cnpj)
    apenas_numeros = re.sub(r'\D', '', raw)[:14]
    if len(apenas_numeros) == 14:
        formatado = f"{apenas_numeros[:2]}.{apenas_numeros[2:5]}.{apenas_numeros[5:8]}/{apenas_numeros[8:12]}-{apenas_numeros[12:]}"
        st.session_state.perma_cnpj_cliente = formatado
    else:
        st.session_state.perma_cnpj_cliente = apenas_numeros
    mark_unsaved()

# ==========================================
# MÓDULOS DE CRM (LEITURA E ESCRITA DESACOPLADA)
# ==========================================
def empacotar_simulacao():
    payload = {
        'perma_nome_cliente': st.session_state.perma_nome_cliente,
        'perma_cnpj_cliente': st.session_state.perma_cnpj_cliente,
        'modo_desconto': st.session_state.get('modo_desconto', 'Total'),
        'g_desc_mensalidade': st.session_state.get('g_desc_mensalidade', 0.0),
        'g_parcelas_setup': st.session_state.get('g_parcelas_setup', 4),
        'g_faturamento': st.session_state.get('g_faturamento', "Na assinatura"),
        'g_regra_desp': st.session_state.get('g_regra_desp', "Faturamento na assinatura"),
        'data_vault': st.session_state.data_vault
    }
    return json.dumps(payload)

def desempacotar_simulacao(json_data, prop_id):
    try:
        for k in list(st.session_state.keys()):
            if k.startswith("ui_"):
                del st.session_state[k]

        st.session_state.form_rc += 1
        dados = json.loads(json_data) if isinstance(json_data, str) else json_data
        
        st.session_state.perma_nome_cliente = dados.get('perma_nome_cliente', '')
        st.session_state.perma_cnpj_cliente = dados.get('perma_cnpj_cliente', '')
        st.session_state.modo_desconto = dados.get('modo_desconto', 'Total').replace('Global', 'Total')
        st.session_state.g_desc_mensalidade = float(dados.get('g_desc_mensalidade', 0.0))
        st.session_state.g_parcelas_setup = int(dados.get('g_parcelas_setup', 4))
        st.session_state.g_faturamento = dados.get('g_faturamento', "Na assinatura")
        st.session_state.g_regra_desp = dados.get('g_regra_desp', "Faturamento na assinatura")
        
        if 'data_vault' in dados:
            st.session_state.data_vault = dados['data_vault']
        else:
            dv = {
                'sel_m': dados.get('sel_m', []), 'sel_i': dados.get('sel_i', []), 'sel_d': dados.get('sel_d', []),
                'auto_added': [], 'quantidades': {}, 'setup_sistemas': {}, 'descontos_itens': {}, 'despesas_valores': {}, 'negociar': {},
                'mapeamento': {
                    'm_combo': "Montar Manualmente", 'm_pdv_conv': 0, 'm_pdv_touch': 0, 'm_pdv_self': 0, 'm_semanas': 0, 'm_mobile': 0,
                    'm_tef': "Nao utiliza", 'm_migracao': False, 'm_ecommerce': False, 'm_app': False, 'm_connect': False,
                    'm_erp_pro': False, 'm_xml': False, 'm_escopo': False, 'm_controller': False, 'm_cartaz': False, 'm_masterfisco': False, 'm_backup': False,
                }
            }
            for k, v in dados.get('quantidades', {}).items(): dv['quantidades'][k.replace('perm_val_', '')] = int(float(v))
            for k, v in dados.get('setup_sistemas', {}).items(): dv['setup_sistemas'][k.replace('perm_val_setup_', '')] = int(float(v))
            for k, v in dados.get('descontos_itens', {}).items():
                nome = k.replace('perm_desc_', '')
                dv['descontos_itens'][nome] = float(v)
                if float(v) > 0: dv['negociar'][nome] = True
            for k, v in dados.get('despesas_valores', {}).items(): dv['despesas_valores'][k.replace('perm_val_desp_unit_', '')] = float(v)
            for k, v in dados.get('mapeamento', {}).items():
                if k in dv['mapeamento']: dv['mapeamento'][k] = v
            st.session_state.data_vault = dv
            
        st.session_state.proposta_carregada_id = prop_id
        st.session_state.show_digital_proposal = False
        st.session_state.has_unsaved_changes = False
        st.session_state.modo_apresentacao = False
        st.session_state.aba_atual = "Gerador de Proposta"
    except Exception as e:
        st.error("Falha interna ao carregar histórico.")

# ==========================================
# DATA LAYER (CARREGAMENTO DO BANCO)
# ==========================================
@st.cache_data(ttl=3600)
def carregar_dados_vendas():
    status_msg, status_cor = "Desconectado", "#ef4444"
    try:
        engine = get_db_engine()
        if engine:
            df = pd.read_sql("SELECT * FROM product", engine)
            df_vinc = pd.read_sql("SELECT * FROM product_vinculo", engine)
            try:
                cache_payload = {'df_raw': df.to_json(orient='records'), 'df_vinc': df_vinc.to_json(orient='records')}
                with open(CACHE_FILE, "w") as f: json.dump(cache_payload, f)
            except Exception: pass
            status_msg, status_cor = "PostgreSQL (Online)", "#22c55e"
    except Exception:
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r") as f: cache_payload = json.load(f)
                df = pd.read_json(cache_payload['df_raw'], orient='records')
                df_vinc = pd.read_json(cache_payload['df_vinc'], orient='records')
                status_msg, status_cor = "Modo Offline (Cache Local)", "#facc15"
            except Exception:
                return {}, {}, {}, {}, {}, {}, {}, "Erro de Cache", "#ef4444", pd.DataFrame(), pd.DataFrame()
        else:
            return {}, {}, {}, {}, {}, {}, {}, status_msg, status_cor, pd.DataFrame(), pd.DataFrame()

    try:
        df.columns = [str(c).strip().lower() for c in df.columns]
        df = df.drop_duplicates(subset=['produto'], keep='last')
        
        if 'preco' in df.columns: df['valor'] = pd.to_numeric(df['preco'], errors='coerce').fillna(0.0)
        elif 'valor' in df.columns: df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0.0)

        for col in ['horas_padrao', 'adesao_vinculada', 'valor_projeto', 'typeproductid']:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

        full = df.set_index('produto').to_dict('index')
        id_to_name = df.set_index('id')['produto'].to_dict() if 'id' in df.columns else {}
        name_to_id = {v: k for k, v in id_to_name.items()}

        sist = {k: v for k, v in full.items() if v.get('typeproductid') == 604}
        kw_desp = ['km', 'hospedagem', 'logistica', 'alimentacao', 'despesa', 'passagem', 'viagem', 'deslocamento', 'pedagio']
        serv = {k: v for k, v in full.items() if v.get('typeproductid') == 606 and not any(x in k.lower() for x in kw_desp)}
        desp = {k: v for k, v in full.items() if any(x in k.lower() for x in kw_desp)}
        
        vinculos_db = {}
        df_vinc.columns = [str(c).strip().lower() for c in df_vinc.columns]
        for _, row in df_vinc.iterrows():
            pai_id = int(row['id_produto_pai'])
            if pai_id not in vinculos_db: vinculos_db[pai_id] = []
            vinculos_db[pai_id].append({'id_filho': int(row['id_produto_filho']), 'tipo': row['tipo_vinculo'], 'qtd': float(row['quantidade_padrao'])})
            
        return sist, serv, desp, full, id_to_name, name_to_id, vinculos_db, status_msg, status_cor, df, df_vinc
    except Exception:
        return {}, {}, {}, {}, {}, {}, {}, "Erro de Processamento", "#ef4444", pd.DataFrame(), pd.DataFrame()

sistemas_db, servicos_db, despesas_db, full_db, id_to_name, name_to_id, vinculos_db, db_status, db_cor, df_raw, df_vinc = carregar_dados_vendas()

v_h_base_global = 161.60
for k_serv, v_serv in servicos_db.items():
    if "treinamento" in k_serv.lower():
        v_h_base_global = v_serv.get('valor_projeto', 0.0)
        if v_h_base_global <= 0: v_h_base_global = v_serv.get('valor', 0.0)
        if v_h_base_global > 0: break

# ==========================================
# ESTADO GLOBAL RESTANTE E SEGURANÇA
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_role' not in st.session_state: st.session_state.user_role = None
if 'primeiro_acesso' not in st.session_state: st.session_state.primeiro_acesso = False
if 'user_email' not in st.session_state: st.session_state.user_email = ""
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'unidade_nome' not in st.session_state: st.session_state.unidade_nome = "VR Software"
if 'user_cargo' not in st.session_state: st.session_state.user_cargo = "Executivo de Vendas"
if 'user_senioridade' not in st.session_state: st.session_state.user_senioridade = "Pleno"
if 'meta_regiao' not in st.session_state: st.session_state.meta_regiao = 0.0

if 'diag_pdv' not in st.session_state: st.session_state.diag_pdv = 0
if 'diag_fat_str' not in st.session_state: st.session_state.diag_fat_str = ""
if 'diag_area' not in st.session_state: st.session_state.diag_area = 0
if 'diag_func' not in st.session_state: st.session_state.diag_func = 0
if 'diag_sku' not in st.session_state: st.session_state.diag_sku = 0
if 'param_piso_pdv' not in st.session_state: st.session_state.param_piso_pdv = 150000.0
if 'param_piso_rh' not in st.session_state: st.session_state.param_piso_rh = 25000.0
if 'param_perda' not in st.session_state: st.session_state.param_perda = 4.0
if 'param_risco_trib' not in st.session_state: st.session_state.param_risco_trib = 18.0

# ==========================================
# BLOCO 1: LOGIN E LOGS
# ==========================================
def tela_login():
    st.markdown("""<style>.stApp { background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%); } div[data-testid="stForm"] { background-color: #ffffff; border-radius: 16px; padding: 40px 30px; border: none; box-shadow: 0 15px 35px rgba(0, 0, 0, 0.05), 0 5px 15px rgba(0, 0, 0, 0.03); } div[data-testid="stForm"] button { background: linear-gradient(90deg, #262730 0%, #3a3b45 100%); color: white; border: none; border-radius: 8px; font-weight: 600; padding: 0.5rem 1rem; transition: all 0.3s ease; margin-top: 15px; } div[data-testid="stForm"] button:hover { background: #000; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2); color: white; } div[data-testid="stTextInput"] input { border-radius: 8px; border: 1px solid #e0e0e0; padding: 12px 15px; background-color: #fcfcfc; } div[data-testid="stTextInput"] input:focus { border-color: #262730; box-shadow: 0 0 0 1px #262730; background-color: #ffffff; }</style>""", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.write(""); st.write("")
        with st.form("login_form", clear_on_submit=False):
            if os.path.exists("logo_vr.png"): st.image("logo_vr.png", use_container_width=True)
            else: st.markdown("<h2 style='text-align:center; color:#262730; margin-bottom:0;'>VR Software</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; color:#777; font-size:0.95rem; margin-bottom:25px;'>Acesso Restrito</p>", unsafe_allow_html=True)
            
            if st.session_state.primeiro_acesso:
                nova_senha = st.text_input("Nova Senha", type="password")
                confirma_senha = st.text_input("Confirme a Senha", type="password")
                if st.form_submit_button("Salvar e Acessar", use_container_width=True):
                    if nova_senha and nova_senha == confirma_senha:
                        try:
                            engine = get_db_engine()
                            with engine.begin() as conn: 
                                conn.execute(text("UPDATE usuarios SET senha = :s, primeiro_acesso = FALSE WHERE email = :e"), {"s": get_senha_hash(nova_senha), "e": st.session_state.user_email})
                            st.session_state.primeiro_acesso = False; st.session_state.logged_in = True; st.rerun()
                        except Exception: st.error("Erro interno. Tente novamente mais tarde.")
                    else: st.error("As senhas informadas não conferem.")
            else:
                email = st.text_input("E-mail corporativo")
                senha = st.text_input("Senha", type="password")
                if st.form_submit_button("Autenticar", use_container_width=True):
                    if not CONN_STR: st.error("Erro interno do servidor.")
                    else:
                        try:
                            engine = get_db_engine()
                            with engine.connect() as conn:
                                resultado = pd.read_sql(text("SELECT u.*, un.nome_fantasia as nome_unidade, un.meta_regiao FROM usuarios u LEFT JOIN unidades un ON u.id_unidade = un.id WHERE u.email = :e AND u.ativo = TRUE"), conn, params={"e": email})
                            if not resultado.empty:
                                user = resultado.iloc[0]
                                senha_hash = get_senha_hash(senha)
                                if user['senha'] == senha_hash or user['senha'] == senha or user['primeiro_acesso']:
                                    st.session_state.user_email = email; st.session_state.user_role = user['nivel_acesso']; st.session_state.user_name = user['nome']
                                    st.session_state.unidade_nome = user['nome_unidade'] if pd.notna(user['nome_unidade']) else "VR Software"
                                    st.session_state.user_cargo = user['cargo'] if 'cargo' in user and pd.notna(user['cargo']) else "Executivo de Vendas"
                                    st.session_state.user_senioridade = user['perfil_senioridade'] if 'perfil_senioridade' in user and pd.notna(user['perfil_senioridade']) else "Pleno"
                                    st.session_state.meta_regiao = float(user['meta_regiao']) if 'meta_regiao' in user and pd.notna(user['meta_regiao']) else 0.0
                                    
                                    if user['primeiro_acesso']: 
                                        st.session_state.primeiro_acesso = True; st.rerun()
                                    else: 
                                        try:
                                            with engine.begin() as conn_log: conn_log.execute(text("INSERT INTO logs_acesso (email_usuario) VALUES (:e)"), {"e": email})
                                        except Exception: pass
                                        st.session_state.logged_in = True; st.rerun()
                                else: st.error("Credenciais inválidas.")
                            else: st.error("Credenciais inválidas.")
                        except Exception as e: st.error("Erro técnico interno. Tente novamente.")

# ==========================================
# BLOCO 2: RENDERIZADORES HTML (PDFs)
# ==========================================
def renderizar_proposta_digital(dados):
    validade_str = (datetime.date.today() + datetime.timedelta(days=15)).strftime("%d/%m/%Y")
    logo_b64 = get_logo_base64()
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="max-width:180px; margin-bottom:20px;">' if logo_b64 else '<div class="brand">VR SOFTWARE</div>'

    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
            body {{ font-family: 'Inter', sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; color: #333; }}
            .container {{ max-width: 900px; margin: 0 auto; background: #fff; box-shadow: 0 10px 30px rgba(0,0,0,0.1); border-radius: 12px; overflow: hidden; }}
            @media print {{ body {{ background: #fff; padding: 0; }} .container {{ box-shadow: none; max-width: 100%; border-radius: 0; }} .no-print {{ display: none !important; }} .page-break {{ page-break-before: always; }} }}
            .print-btn {{ background: #ff6600; color: white; border: none; padding: 12px 24px; font-size: 16px; font-weight: bold; border-radius: 8px; cursor: pointer; display: flex; align-items: center; justify-content: center; margin: 20px auto; box-shadow: 0 4px 15px rgba(255,102,0,0.3); transition: 0.3s; }}
            .cover {{ background: #262730; color: white; padding: 60px 40px; position: relative; border-left: 15px solid #ff6600; }}
            .cover h1 {{ font-size: 48px; margin: 0; font-weight: 900; letter-spacing: -1px; }}
            .cover h2 {{ color: #ff6600; font-weight: 400; font-size: 24px; margin-top: 10px; }}
            .cover-details {{ margin-top: 60px; display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
            .detail-label {{ font-size: 12px; color: #aaa; text-transform: uppercase; margin-bottom: 5px; }}
            .detail-value {{ font-size: 18px; font-weight: bold; color: #fff; }}
            .detail-sub {{ font-size: 14px; color: #ccc; }}
            .content {{ padding: 40px; }}
            .header-content {{ border-bottom: 2px solid #ff6600; padding-bottom: 10px; margin-bottom: 30px; }}
            .header-content h3 {{ margin: 0; font-size: 22px; color: #262730; }}
            .cards {{ display: flex; flex-direction: column; gap: 25px; }}
            .card {{ border: 1px solid #eee; border-radius: 8px; padding: 25px; background: #fafafa; }}
            .card.setup {{ border-top: 6px solid #ff6600; }}
            .card.mensal {{ border-top: 6px solid #2e7d32; }}
            .card.despesa {{ border-top: 6px solid #1976d2; }}
            .card-title {{ font-size: 13px; color: #888; font-weight: bold; text-transform: uppercase; margin-bottom: 10px; }}
            .card-val {{ font-size: 28px; font-weight: 900; margin-bottom: 5px; }}
            .card.setup .card-val {{ color: #ff6600; }}
            .card.mensal .card-val {{ color: #2e7d32; }}
            .card.despesa .card-val {{ color: #1976d2; }}
            .card-sub {{ font-size: 14px; font-weight: bold; color: #444; margin-bottom: 20px; display: block; }}
            .card-list {{ list-style: none; padding: 0; margin: 0; }}
            .card-list li {{ font-size: 14px; border-bottom: 1px dashed #ddd; padding: 10px 0; color: #444; }}
            .card-list li strong {{ display: block; font-size: 15px; color: #222; margin-bottom: 4px; }}
            .card-list li .detail {{ background: #eee; padding: 4px 8px; border-radius: 4px; display: inline-block; font-size: 12px; }}
            .card-list li del {{ color: #999; font-size: 12px; margin-right: 5px; }}
            .item-incluso {{ color: #888; font-style: italic; border: none !important; padding-top: 4px !important; padding-left: 15px !important; }}
            .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #888; font-size: 12px; }}
            .signatures {{ display: grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-top: 40px; }}
            .sig-line {{ border-top: 1px solid #333; padding-top: 10px; font-weight: bold; color: #333; }}
        </style>
    </head>
    <body>
        <div class="no-print" style="text-align: center;">
            <button class="print-btn" onclick="window.print()">Salvar como PDF / Imprimir</button>
        </div>
        <div class="container">
            <div class="cover">
                {logo_html}
                <h1>PROPOSTA<br>COMERCIAL</h1>
                <h2>RESUMO DE INVESTIMENTO</h2>
                <div class="cover-details">
                    <div>
                        <div class="detail-label">Apresentado para</div>
                        <div class="detail-value">{dados.get('nome_cliente', 'Cliente')}</div>
                        <div class="detail-sub">CNPJ: {dados.get('cnpj', '')}</div>
                        <div class="detail-sub" style="margin-top: 10px;">Data: {datetime.date.today().strftime("%d/%m/%Y")}</div>
                    </div>
                    <div>
                        <div class="detail-label">Executivo de Vendas</div>
                        <div class="detail-value">{html.escape(st.session_state.user_name)}</div>
                        <div class="detail-sub" style="color: #ff6600;">{html.escape(st.session_state.unidade_nome)}</div>
                    </div>
                </div>
            </div>
            <div class="page-break"></div>
            <div class="content">
                <div class="header-content"><h3>RESUMO EXECUTIVO DE INVESTIMENTO</h3></div>
                <div class="cards">
                    <div class="card setup">
                        <div class="card-title">Implantação (Setup)</div>
                        <div class="card-val">R$ {dados.get('valor_setup', '0,00')}</div>
                        <span class="card-sub">{dados.get('parcelas', '1')}x parcelas</span>
                        <ul class="card-list">{dados.get('html_setup', '<li>Nenhum item</li>')}</ul>
                    </div>
                    <div class="card mensal">
                        <div class="card-title">Manutenção Mensal</div>
                        <div class="card-val">R$ {dados.get('valor_mensal', '0,00')}</div>
                        <span class="card-sub">Início: {dados.get('faturamento', '')}</span>
                        <ul class="card-list">{dados.get('html_mensal', '<li>Nenhum item</li>')}</ul>
                    </div>
                    <div class="card despesa">
                        <div class="card-title">Despesas Previstas</div>
                        <div class="card-val">R$ {dados.get('valor_despesa', '0,00')}</div>
                        <span class="card-sub">{dados.get('regra_desp', '')}</span>
                        <ul class="card-list">{dados.get('html_despesa', '<li>Sem despesas</li>')}</ul>
                    </div>
                </div>
                <div class="footer">
                    <p>Este documento é um resumo executivo da simulação. A contratação está sujeita à análise e aprovação. Condições comerciais válidas até {validade_str}.</p>
                    <div class="signatures">
                        <div class="sig-line">Assinatura do Cliente</div>
                        <div class="sig-line">VR Software - Autorizado</div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

def renderizar_welcome_pack(nome, cnpjs, val_setup, val_mensal, parcelas_html):
    logo_b64 = get_logo_base64()
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="max-width:180px; margin-bottom:20px;">' if logo_b64 else '<div class="brand" style="font-size:24px; font-weight:bold; color:#ff6600; margin-bottom:20px;">VR SOFTWARE</div>'
    
    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
            body {{ font-family: 'Inter', sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; color: #333; }}
            .container {{ max-width: 900px; margin: 0 auto; background: #fff; box-shadow: 0 10px 30px rgba(0,0,0,0.1); border-radius: 12px; overflow: hidden; padding: 50px; border-top: 15px solid #262730; }}
            @media print {{ body {{ background: #fff; padding: 0; }} .container {{ box-shadow: none; max-width: 100%; border-radius: 0; padding: 20px; border-top:none; }} .no-print {{ display: none !important; }} }}
            .print-btn {{ background: #ff6600; color: white; border: none; padding: 12px 24px; font-size: 16px; font-weight: bold; border-radius: 8px; cursor: pointer; display: flex; align-items: center; justify-content: center; margin: 20px auto; transition: 0.3s; }}
            h1 {{ color: #262730; font-size: 36px; margin-bottom: 5px; }}
            h2 {{ color: #ff6600; font-size: 18px; text-transform: uppercase; margin-top: 30px; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
            .info-box {{ background: #fafafa; border: 1px solid #eee; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 14px; }}
            th, td {{ border: 1px solid #e0e0e0; padding: 12px; text-align: center; }}
            th {{ background-color: #262730; color: white; text-transform: uppercase; font-size: 12px; }}
            td {{ background-color: #fff; color: #444; font-weight: bold; }}
            .highlight {{ color: #ff6600; }}
            .highlight-mensal {{ color: #2e7d32; font-weight: 900; background-color: #f1f8e9; }}
        </style>
    </head>
    <body>
        <div class="no-print" style="text-align: center;">
            <button class="print-btn" onclick="window.print()">Salvar PDF / Imprimir</button>
        </div>
        <div class="container">
            {logo_html}
            <h1>SEJA BEM-VINDO</h1>
            <p style="color:#555; font-size:16px; line-height: 1.6;">A VR Software tem o prazer de lhe dar as boas-vindas e lhe parabenizar pela sua recente inclusão em nosso portfólio de clientes.<br>Trabalharemos juntos para lhe oferecer a cada dia os melhores produtos e serviços.</p>
            
            <div class="info-box">
                <strong style="color:#262730;">Cliente:</strong> <span style="color:#555;">{nome}</span><br><br>
                <strong style="color:#262730;">CNPJ(s) do Contrato:</strong> <span style="color:#555;">{cnpjs}</span>
            </div>
            
            <h2>RESUMO DO FATURAMENTO</h2>
            <div style="display:flex; gap: 20px;">
                <div class="info-box" style="flex:1; text-align:center; border-top: 4px solid #ff6600;">
                    <span style="color:#777; font-size:12px; font-weight:bold;">INVESTIMENTO ERP (SETUP)</span><br>
                    <strong style="font-size:28px; color:#ff6600;">R$ {f_br(val_setup)}</strong>
                </div>
                <div class="info-box" style="flex:1; text-align:center; border-top: 4px solid #2e7d32;">
                    <span style="color:#777; font-size:12px; font-weight:bold;">MENSALIDADE ERP RECORRENTE</span><br>
                    <strong style="font-size:28px; color:#2e7d32;">R$ {f_br(val_mensal)}</strong>
                </div>
            </div>
            
            <h2>CRONOGRAMA DE FATURAMENTO</h2>
            <p style="color:#555; font-size:14px;">De acordo com os valores acordados em contrato, a cobrança será dividida entre a VR Recife e a VR Software Matriz (inovação tecnológica). Veja o detalhamento de faturamento abaixo:</p>
            <table>
                <thead>
                    <tr>
                        <th>Parcela</th>
                        <th>Cobrança VR Matriz</th>
                        <th>Cobrança VR Recife</th>
                        <th>Total do Mês</th>
                    </tr>
                </thead>
                <tbody>
                    {parcelas_html}
                </tbody>
            </table>
            
            <div style="margin-top: 50px; font-size: 12px; color: #888; text-align: center; border-top: 1px solid #eee; padding-top: 20px;">
                <strong>VR SOFTWARE</strong><br>
                É nosso dever e compromisso; transformar grandes, médias e pequenas empresas.
            </div>
        </div>
    </body>
    </html>
    """

# ==========================================
# NOVA TELA: COMISSIONAMENTO OTIMIZADA E VISÃO COMERCIAL
# ==========================================
MAPA_PROCESSOS = {
    "2726": "NOVOS NEGÓCIOS", "2806": "NOVOS PRODUTOS CLIENTE VR", "2728": "NOVAS LOJAS CLIENTE VR",
    "5968": "O3 CLOUD - NOVOS NEGÓCIOS", "2724": "O3 CLOUD - BASE DE CLIENTES",
    "5998": "SKY ONE - NOVOS NEGÓCIOS", "6000": "SKY ONE - BASE DE CLIENTES",
    "2816": "ATUALIZAÇÃO DE VALORES", "2730": "TROCA DE CNPJ", "2810": "CUSTOMIZAÇÃO/DESENVOLVIMENTO",
    "2818": "INSTALAÇÃO TÉCNICA", "2812": "DESPESA DE PROJETO", "2814": "ACESSO TEMPORÁRIO",
    "2820": "SERVIÇOS DE TREINAMENTO", "2718": "CONTROLLER 360 (DESATIVADO)",
    "2720": "MASTERFISCO (DESATIVADO)", "2722": "OMNICHANNEL (DESATIVADO)",
    "3626": "NOVOS NEGÓCIOS - CONTROLLER 360 (DESATIVADO)", "3632": "NOVOS NEGÓCIOS - OMNICHANNEL (DESATIVADO)",
    "3630": "NOVOS NEGÓCIOS - MASTERFISCO (DESATIVADO)"
}

@st.dialog("Extrato de Liquidação por Produto", width="large")
def modal_extrato_venda(proposta_id, nome_cliente, processo_id):
    nome_processo = MAPA_PROCESSOS.get(str(processo_id), "Processo Não Mapeado / Outros")
    st.markdown(f"<h3 style='color:#262730; margin-bottom: 5px;'>{nome_cliente}</h3>", unsafe_allow_html=True)
    st.markdown(f"<span style='color:#777; font-weight:bold;'>Negócio ID: #{proposta_id} | Origem: {nome_processo}</span><hr>", unsafe_allow_html=True)
    
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            query_itens = text("""
                SELECT io.title AS "Produto/Serviço", io.quantidade AS "Qtd", COALESCE(io.ufcrmvalorproduto::text, '0') AS "val_unit_str", io.ufcrmtipoproduto AS "Tipo ID"
                FROM itensorcamento_novo AS io JOIN orcamento_novo AS o ON o.id = io.parentid7 WHERE o.dealid = :pid
            """)
            df_itens = pd.read_sql(query_itens, conn, params={"pid": proposta_id})
            if df_itens.empty:
                st.warning("Nenhum item detalhado encontrado no banco para esta proposta.")
                return

            df_itens['Valor Unit. (R$)'] = df_itens['val_unit_str'].apply(parse_currency)
            df_itens['Qtd'] = pd.to_numeric(df_itens['Qtd'], errors='coerce').fillna(1)
            df_itens['Valor Total (R$)'] = df_itens['Qtd'] * df_itens['Valor Unit. (R$)']
            df_itens['% Comissão'] = 0.0
            df_itens['Tag'] = 'Não Classificado'
            
            for index, row in df_itens.iterrows():
                tipo = pd.to_numeric(row['Tipo ID'], errors='coerce')
                nome = str(row['Produto/Serviço']).lower()
                
                if str(processo_id) == '2812':
                    df_itens.at[index, '% Comissão'], df_itens.at[index, 'Tag'] = 0.0, 'Despesa de Projeto (Isento)'
                else:
                    if tipo == 604: df_itens.at[index, '% Comissão'], df_itens.at[index, 'Tag'] = 5.0, 'Mensalidade'
                    elif any(kw in nome for kw in ['despesa', 'km', 'hospedagem', 'alimentação', 'passagem', 'viagem']): df_itens.at[index, '% Comissão'], df_itens.at[index, 'Tag'] = 0.0, 'Despesa (Isento)'
                    elif tipo in [606, 608, 610]: df_itens.at[index, '% Comissão'], df_itens.at[index, 'Tag'] = 5.0, 'Setup/Serviço'

            df_itens['Comissão (R$)'] = df_itens['Valor Total (R$)'] * (df_itens['% Comissão'] / 100)
            colunas_monetarias = ['Valor Unit. (R$)', 'Valor Total (R$)', 'Comissão (R$)']
            for col in colunas_monetarias:
                df_itens[col] = df_itens[col].apply(lambda x: f"R$ {f_br(x)}" if pd.notnull(x) else "R$ 0,00")
            df_itens['% Comissão'] = df_itens['% Comissão'].apply(lambda x: f"{x}%")
            st.dataframe(df_itens[['Produto/Serviço', 'Tag', 'Qtd', 'Valor Unit. (R$)', 'Valor Total (R$)', '% Comissão', 'Comissão (R$)']], use_container_width=True, hide_index=True)
    except Exception as e:
        st.error("Falha ao carregar detalhamento. Tente novamente.")

def tela_visao_comercial():
    import datetime 
    import pandas as pd
    
# Motor Gráfico HTML/CSS - Arquitetura em TABELA (Inspirado na referência de In-cell Charts)
    def render_html_bar_chart(df_chart, col_label, col_value, cor_barra):
        if df_chart is None or df_chart.empty:
            return "<div style='color:#999; font-style:italic;'>Sem dados para exibir.</div>"
        
        df_chart = df_chart.sort_values(by=col_value, ascending=False)
        max_v = df_chart[col_value].max()
        if max_v <= 0: max_v = 1
        
        # Abertura da tabela com bordas sutis e colapso de espaços
        html = "<table style='width: 100%; border-collapse: collapse; margin-top: 15px; font-family: sans-serif;'>"
        
        for _, row in df_chart.iterrows():
            lbl = str(row[col_label])
            val = float(row[col_value])
            pct = (val / max_v) * 100 
            v_str = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
            # Linha da tabela (tr) com borda inferior muito clara ("grade clarinha")
            html += "<tr style='border-bottom: 1px solid #f0f2f6;'>"
            
            # Célula 1: Rótulo alinhado à esquerda
            html += f"<td style='width: 35%; padding: 10px 5px; text-align: left; font-size: 0.85rem; color: #444; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 150px;' title='{lbl}'>{lbl}</td>"
            
            # Célula 2: A barra com fundo cinza (estilo progresso)
            html += f"<td style='width: 45%; padding: 10px 15px; vertical-align: middle;'>"
            html += f"<div style='width: 100%; background-color: #e9ecef; height: 18px; border-radius: 10px; overflow: hidden;'>"
            html += f"<div style='width: {pct}%; background-color: {cor_barra}; height: 100%; border-radius: 10px 0 0 10px; min-width: 2px;'></div>"
            html += "</div></td>"
            
            # Célula 3: Valor alinhado à direita
            html += f"<td style='width: 20%; padding: 10px 5px; text-align: right; font-size: 0.85rem; font-weight: 700; color: #222; white-space: nowrap;'>R$ {v_str}</td>"
            
            html += "</tr>"
            
        html += "</table>"
        return html

    # Fragmento Isolado para Tabela de Fechados (Impede o pulo de rolagem)
    @st.fragment
    def render_extrato_fechados(df_vis, df_exib):
        edited_df = st.data_editor(
            df_vis, 
            key="grid_fechados",
            use_container_width=True, 
            hide_index=True, 
            column_config={"Ver Extrato": st.column_config.CheckboxColumn("Ver", default=False)}, 
            disabled=[col for col in df_vis.columns if col != "Ver Extrato"]
        )
        linhas_sel = edited_df[edited_df["Ver Extrato"] == True]
        if not linhas_sel.empty:
            prop_id = int(linhas_sel.iloc[0]["Proposta ID"])
            cli_nome = str(linhas_sel.iloc[0]["Cliente"])
            proc_id = str(df_exib.loc[df_exib["id"] == prop_id, "processovendaid"].values[0])
            modal_extrato_venda(prop_id, cli_nome, proc_id)

    # Fragmento Isolado para Tabela de Pipeline Ativo
    @st.fragment
    def render_extrato_abertos(df_vis_aberto, df_exib_aberto):
        edited_open_df = st.data_editor(
            df_vis_aberto, 
            key="grid_abertos",
            use_container_width=True, 
            hide_index=True, 
            column_config={
                "Ver Extrato": st.column_config.CheckboxColumn("Ver", default=False),
                "Status": st.column_config.TextColumn("Status", help="Temperatura com base nos dias na mesa:\n🔥 Quente: 0 a 7 dias\n⚠️ Morno: 8 a 14 dias\n❄️ Frio: 15+ dias"),
                "Setup": st.column_config.TextColumn("Setup", help="Valor Único de Implantação/Projeto"),
                "MRR": st.column_config.TextColumn("MRR", help="Valor Recorrente Mensal (Mensalidade)"),
                "Total Projetado": st.column_config.TextColumn("Total Projetado", help="Soma total de Setup + MRR desta proposta")
            }, 
            disabled=[col for col in df_vis_aberto.columns if col != "Ver Extrato"]
        )
        linhas_open_sel = edited_open_df[edited_open_df["Ver Extrato"] == True]
        if not linhas_open_sel.empty:
            prop_id = int(linhas_open_sel.iloc[0]["Proposta ID"])
            cli_nome = str(linhas_open_sel.iloc[0]["Cliente"])
            proc_id = str(df_exib_aberto.loc[df_exib_aberto["id"] == prop_id, "processovendaid"].values[0])
            modal_extrato_venda(prop_id, cli_nome, proc_id)

    st.markdown("<h1 class='hero-title'>VISÃO COMERCIAL</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#777; font-size:1.2rem; margin-bottom:30px;'>Dashboard Estratégico de Vendas e Performance</p>", unsafe_allow_html=True)
    
    try:
        hoje = datetime.date.today()
        c1, c2 = st.columns(2)
        data_inicio = c1.date_input("Período Início", hoje.replace(day=1), format="DD/MM/YYYY")
        data_fim = c2.date_input("Período Fim", hoje, format="DD/MM/YYYY")
        
        engine = get_db_engine()
        with engine.connect() as conn:
            
            try:
                query_dash = text("""
                    SELECT DISTINCT ON (n.id) n.id, 
                    COALESCE(o.ufcrmvalorprojeto::text, '0') AS setup_str, 
                    COALESCE(o.ufcrmvalorrecorrente::text, o.opportunity::text, '0') AS mrr_str,
                    TRIM(CONCAT(COALESCE(ab.name, ''), ' ', COALESCE(ab.lastname, ''))) AS "Vendedor",
                    o.closedate,
                    COALESCE(c.title, 'Cliente Não Informado') AS "Cliente",
                    COALESCE(c.ufcrmintegraoreceitauf, 'N/I') AS "Estado",
                    n.processovendaid
                    FROM orcamento_novo AS o 
                    JOIN negocio_novo AS n ON n.id = o.dealId
                    LEFT JOIN assignedby_novo AS ab ON ab.id = n.assignedById
                    LEFT JOIN company_novo AS c ON c.id = n.companyId
                    WHERE o.closedate >= :d_inicio AND o.closedate <= :d_fim 
                    AND n.closed = 'Y' AND n.stageid LIKE '%WON%'
                """)
                df_dash = pd.read_sql(query_dash, conn, params={"d_inicio": data_inicio, "d_fim": data_fim})
            except:
                query_fallback = text("""
                    SELECT DISTINCT ON (n.id) n.id, 
                    COALESCE(o.ufcrmvalorprojeto::text, '0') AS setup_str, 
                    COALESCE(o.ufcrmvalorrecorrente::text, o.opportunity::text, '0') AS mrr_str,
                    TRIM(CONCAT(COALESCE(ab.name, ''), ' ', COALESCE(ab.lastname, ''))) AS "Vendedor",
                    o.closedate,
                    COALESCE(c.title, 'Cliente Não Informado') AS "Cliente",
                    COALESCE(c.ufcrmintegraoreceitauf, 'N/I') AS "Estado",
                    n.processovendaid
                    FROM orcamento_novo AS o 
                    JOIN negocio_novo AS n ON n.id = o.dealId
                    LEFT JOIN assignedby_novo AS ab ON ab.id = n.assignedById
                    LEFT JOIN company_novo AS c ON c.id = n.companyId
                    WHERE o.closedate >= :d_inicio AND o.closedate <= :d_fim AND n.closed = 'Y'
                """)
                df_dash = pd.read_sql(query_fallback, conn, params={"d_inicio": data_inicio, "d_fim": data_fim})
                
            query_open = text("""
                SELECT DISTINCT ON (n.id) n.id, 
                COALESCE(o.ufcrmvalorprojeto::text, '0') AS setup_str, 
                COALESCE(o.ufcrmvalorrecorrente::text, o.opportunity::text, '0') AS mrr_str,
                TRIM(CONCAT(COALESCE(ab.name, ''), ' ', COALESCE(ab.lastname, ''))) AS "Vendedor",
                n.processovendaid,
                COALESCE(c.title, 'Cliente Não Informado') AS "Cliente",
                COALESCE(n.begindate, CURRENT_DATE) AS data_inicio_negocio,
                o.closedate AS data_prevista
                FROM orcamento_novo AS o 
                JOIN negocio_novo AS n ON n.id = o.dealId
                LEFT JOIN assignedby_novo AS ab ON ab.id = n.assignedById
                LEFT JOIN company_novo AS c ON c.id = n.companyId
                WHERE n.closed = 'N'
            """)
            df_open = pd.read_sql(query_open, conn)
            
            if not df_dash.empty: df_dash = df_dash[df_dash['processovendaid'].astype(str) != '2812']
            if not df_open.empty: df_open = df_open[df_open['processovendaid'].astype(str) != '2812']
            
            if not df_dash.empty: df_dash = df_dash[df_dash['processovendaid'].astype(str) != '2812']
            if not df_open.empty: df_open = df_open[df_open['processovendaid'].astype(str) != '2812']
            
            # --- CONTROLE DE ACESSO E FILTRO DE ESCOPO ---
            if st.session_state.user_role == "vendedor":
                nome_logado = str(st.session_state.user_name).strip().lower()
                if not df_dash.empty: df_dash = df_dash[df_dash['Vendedor'].str.lower().str.strip() == nome_logado]
                if not df_open.empty: df_open = df_open[df_open['Vendedor'].str.lower().str.strip() == nome_logado]
            else:
                lista_vendedores = []
                if not df_dash.empty: lista_vendedores.extend(df_dash['Vendedor'].dropna().unique().tolist())
                if not df_open.empty: lista_vendedores.extend(df_open['Vendedor'].dropna().unique().tolist())
                lista_vendedores = sorted(list(set([v for v in lista_vendedores if v.strip() != ''])))
                
                vendedor_sel = st.selectbox("Auditoria Estratégica por Executivo", ["Todos"] + lista_vendedores)
                
                if vendedor_sel != "Todos":
                    if not df_dash.empty: df_dash = df_dash[df_dash['Vendedor'] == vendedor_sel]
                    if not df_open.empty: df_open = df_open[df_open['Vendedor'] == vendedor_sel]
            # ---------------------------------------------
            
            # --- BUSCA DE PRODUTOS ---
            df_produtos = pd.DataFrame()
            if not df_dash.empty:
                ids_fechados = df_dash['id'].tolist()
                ids_str = ",".join(map(str, ids_fechados))
                
                query_prod = text(f"""
                    SELECT io.title AS "Produto", 
                           o.dealid AS deal_id,
                           COALESCE(io.ufcrmvalorprojeto::text, '0') AS setup_str,
                           COALESCE(io.opportunity::text, '0') AS mrr_str
                    FROM itensorcamento_novo io
                    JOIN orcamento_novo o ON o.id = io.parentid7
                    WHERE o.dealid IN ({ids_str})
                """)
                df_prod_raw = pd.read_sql(query_prod, conn)
                
                if not df_prod_raw.empty:
                    df_prod_raw['Setup Bruto'] = df_prod_raw['setup_str'].apply(parse_currency)
                    df_prod_raw['MRR Bruto'] = df_prod_raw['mrr_str'].apply(parse_currency)
                    
                    df_produtos = df_prod_raw.groupby('Produto').agg(
                        Adesao_Contratos=('deal_id', 'nunique'),
                        Setup_Bruto=('Setup Bruto', 'sum'),
                        MRR_Bruto=('MRR Bruto', 'sum')
                    ).reset_index()
                    
                    df_produtos = df_produtos.rename(columns={'Adesao_Contratos': 'Adesão (Contratos)', 'Setup_Bruto': 'Setup Bruto', 'MRR_Bruto': 'MRR Bruto'})
                    df_produtos['Total Bruto'] = df_produtos['Setup Bruto'] + df_produtos['MRR Bruto']
                    df_produtos = df_produtos.sort_values('Adesão (Contratos)', ascending=False)

            # --- CONTROLE DE VISÃO ---
            st.markdown("<br>", unsafe_allow_html=True)
            modo_exibicao = st.radio("Formato de Exibição", ["Visão Completa", "Visão Gráfica"], horizontal=True)
            st.markdown("<hr style='margin-top: 5px;'>", unsafe_allow_html=True)
                
            # === BLOCO 1: NEGÓCIOS FECHADOS ===
            if df_dash.empty:
                st.warning("Nenhum negócio de receita comercial classificado como ganho neste período para o filtro selecionado.")
            else:
                df_dash['Setup Bruto'] = df_dash['setup_str'].apply(parse_currency)
                df_dash['MRR Bruto'] = df_dash['mrr_str'].apply(parse_currency)
                df_dash['Total Bruto'] = df_dash['Setup Bruto'] + df_dash['MRR Bruto']
                df_dash['Data Fechamento'] = pd.to_datetime(df_dash['closedate']).dt.date
                df_dash['Origem'] = df_dash['processovendaid'].astype(str).map(MAPA_PROCESSOS).fillna("Outros Processos")
                
                t_setup = df_dash['Setup Bruto'].sum()
                t_mrr = df_dash['MRR Bruto'].sum()
                t_geral = df_dash['Total Bruto'].sum()
                
                qtd_geral = len(df_dash)
                qtd_mrr = len(df_dash[df_dash['MRR Bruto'] > 0])
                qtd_setup = len(df_dash[df_dash['Setup Bruto'] > 0])
                
                tk_medio = t_geral / qtd_geral if qtd_geral > 0 else 0
                tk_medio_mrr = t_mrr / qtd_mrr if qtd_mrr > 0 else 0
                tk_medio_setup = t_setup / qtd_setup if qtd_setup > 0 else 0
                
                with st.expander("💰 Receita Adquirida (Negócios Ganhos)", expanded=True):
                    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
                    with col_kpi1: st.markdown(f"""<div class="dash-card" title="Volume total de Receita Recorrente" style="border-top: 5px solid #1976d2;"><div class="dash-title">Total MRR</div><div style="font-size:1.5rem; font-weight:900;">R$ {f_br(t_mrr)}</div></div>""", unsafe_allow_html=True)
                    with col_kpi2: st.markdown(f"""<div class="dash-card" title="Volume total de Implantação/Projeto" style="border-top: 5px solid #ff6600;"><div class="dash-title">Total Setup</div><div style="font-size:1.5rem; font-weight:900;">R$ {f_br(t_setup)}</div></div>""", unsafe_allow_html=True)
                    with col_kpi3: st.markdown(f"""<div class="dash-card" title="Soma geral da Receita Adquirida (MRR + Setup)" style="border-top: 5px solid #2e7d32; background:#f4f6f9;"><div class="dash-title">Volume Fechado</div><div style="font-size:1.5rem; font-weight:900;">R$ {f_br(t_geral)}</div></div>""", unsafe_allow_html=True)
                    
                    col_kpi4, col_kpi5, col_kpi6 = st.columns(3)
                    with col_kpi4: st.markdown(f"""<div class="dash-card" title="Média de valor dos negócios que possuem MRR" style="border-top: 5px solid #1976d2; opacity: 0.9;"><div class="dash-title">Ticket Médio MRR</div><div style="font-size:1.3rem; font-weight:900;">R$ {f_br(tk_medio_mrr)}</div></div>""", unsafe_allow_html=True)
                    with col_kpi5: st.markdown(f"""<div class="dash-card" title="Média de valor dos negócios que possuem Setup" style="border-top: 5px solid #ff6600; opacity: 0.9;"><div class="dash-title">Ticket Médio Setup</div><div style="font-size:1.3rem; font-weight:900;">R$ {f_br(tk_medio_setup)}</div></div>""", unsafe_allow_html=True)
                    with col_kpi6: st.markdown(f"""<div class="dash-card" title="Média do volume total por cada negócio fechado" style="border-top: 5px solid #8e24aa;"><div class="dash-title">Ticket Médio Geral</div><div style="font-size:1.3rem; font-weight:900;">R$ {f_br(tk_medio)}</div></div>""", unsafe_allow_html=True)
                
                if modo_exibicao == "Visão Completa":
                    with st.expander("🗺️ Análise de Vendas e Origem", expanded=True):
                        def gerar_tabela_analitica(df, agrupador):
                            grp = df.groupby(agrupador).agg(
                                Setup_Soma=('Setup Bruto', 'sum'),
                                MRR_Soma=('MRR Bruto', 'sum'),
                                Total_Soma=('Total Bruto', 'sum'),
                                Qtd_Setup=('Setup Bruto', lambda x: (x > 0).sum()),
                                Qtd_MRR=('MRR Bruto', lambda x: (x > 0).sum())
                            ).reset_index()
                            
                            grp['TM_Setup'] = (grp['Setup_Soma'] / grp['Qtd_Setup'].replace(0, 1)).fillna(0)
                            grp['TM_MRR'] = (grp['MRR_Soma'] / grp['Qtd_MRR'].replace(0, 1)).fillna(0)
                            
                            grp = grp.sort_values(by='Total_Soma', ascending=False)
                            for col in ['Setup_Soma', 'TM_Setup', 'MRR_Soma', 'TM_MRR', 'Total_Soma']: 
                                grp[col] = grp[col].apply(lambda x: f"R$ {f_br(x)}")
                                
                            return grp[[agrupador, 'Setup_Soma', 'TM_Setup', 'MRR_Soma', 'TM_MRR', 'Total_Soma']].rename(
                                columns={'Setup_Soma': 'Setup', 'TM_Setup': 'T.M. Setup', 'MRR_Soma': 'MRR', 'TM_MRR': 'T.M. MRR', 'Total_Soma': 'Volume Total'}
                            )
                        
                        st.markdown("**Performance por Origem de Negócio**")
                        st.dataframe(gerar_tabela_analitica(df_dash, 'Origem'), use_container_width=True, hide_index=True)

                        c_tab1, c_tab2 = st.columns(2)
                        with c_tab1:
                            st.markdown("**Desempenho por Região (UF)**")
                            st.dataframe(gerar_tabela_analitica(df_dash, 'Estado'), use_container_width=True, hide_index=True)
                        with c_tab2:
                            st.markdown("**Desempenho por Executivo**")
                            st.dataframe(gerar_tabela_analitica(df_dash, 'Vendedor'), use_container_width=True, hide_index=True)

                        if not df_produtos.empty:
                            st.markdown("**Desempenho por Produto / Módulo**")
                            df_prod_show = df_produtos.copy()
                            for col in ['Setup Bruto', 'MRR Bruto', 'Total Bruto']:
                                df_prod_show[col] = df_prod_show[col].apply(lambda x: f"R$ {f_br(float(x))}")
                            df_prod_show = df_prod_show.rename(columns={'Setup Bruto': 'Total Setup', 'MRR Bruto': 'Total MRR', 'Total Bruto': 'Volume Final'})
                            st.dataframe(df_prod_show, use_container_width=True, hide_index=True)

                    # Bloco do Extrato mantido recolhido por padrão para otimizar espaço
                    with st.expander("📋 Extrato Analítico Interativo (Fechados)", expanded=True):
                        df_exibicao = df_dash[['Vendedor', 'id', 'Cliente', 'Origem', 'Data Fechamento', 'Setup Bruto', 'MRR Bruto', 'Total Bruto', 'processovendaid']].copy()
                        df_exibicao['Data Fechamento'] = pd.to_datetime(df_exibicao['Data Fechamento']).dt.strftime('%d/%m/%Y')
                        for col in ['Setup Bruto', 'MRR Bruto', 'Total Bruto']: df_exibicao[col] = df_exibicao[col].apply(lambda x: f"R$ {f_br(x)}")
                        
                        df_visual = df_exibicao[['Vendedor', 'id', 'Cliente', 'Origem', 'Data Fechamento', 'Setup Bruto', 'MRR Bruto', 'Total Bruto']].rename(columns={'id': 'Proposta ID'})
                        df_visual.insert(0, "Ver Extrato", False)
                        
                        render_extrato_fechados(df_visual, df_exibicao)
                else:
                    with st.expander("📊 Gráficos de Performance (Fechados)", expanded=True):
                        # Estilo do título com fundo branco e sombreamento suave
                        estilo_titulo = "<div style='background: #ffffff; padding: 10px 15px; border-radius: 6px; box-shadow: 0 2px 5px rgba(0,0,0,0.08); border: 1px solid #eaebf0; color: #262730; font-weight: 700; font-size: 0.95rem; margin-bottom: 5px;'>{}</div>"
                        
                        col_g1, col_g2 = st.columns(2)
                        with col_g1:
                            st.markdown(estilo_titulo.format("Volume Total por Região (UF)"), unsafe_allow_html=True)
                            df_uf_graf = df_dash.groupby('Estado', as_index=False)['Total Bruto'].sum()
                            st.markdown(render_html_bar_chart(df_uf_graf, 'Estado', 'Total Bruto', '#1976d2'), unsafe_allow_html=True)
                        with col_g2:
                            st.markdown(estilo_titulo.format("Volume Total por Executivo"), unsafe_allow_html=True)
                            df_exec_graf = df_dash.groupby('Vendedor', as_index=False)['Total Bruto'].sum()
                            st.markdown(render_html_bar_chart(df_exec_graf, 'Vendedor', 'Total Bruto', '#ff6600'), unsafe_allow_html=True)

                        col_g3, col_g4 = st.columns(2)
                        with col_g3:
                            st.markdown(estilo_titulo.format("Volume por Origem de Negócio"), unsafe_allow_html=True)
                            df_origem_graf = df_dash.groupby('Origem', as_index=False)['Total Bruto'].sum()
                            st.markdown(render_html_bar_chart(df_origem_graf, 'Origem', 'Total Bruto', '#2e7d32'), unsafe_allow_html=True)
                        with col_g4:
                            if not df_produtos.empty:
                                st.markdown(estilo_titulo.format("Top 10 Produtos por Volume"), unsafe_allow_html=True)
                                df_prod_graf = df_produtos.sort_values('Total Bruto', ascending=False).head(10)
                                st.markdown(render_html_bar_chart(df_prod_graf, 'Produto', 'Total Bruto', '#8e24aa'), unsafe_allow_html=True)

            # === BLOCO 2: PIPELINE ATIVO ===
            if not df_open.empty:
                df_open['Setup Bruto'] = df_open['setup_str'].apply(parse_currency)
                df_open['MRR Bruto'] = df_open['mrr_str'].apply(parse_currency)
                df_open['Total Projetado'] = df_open['Setup Bruto'] + df_open['MRR Bruto']
                df_open['Origem'] = df_open['processovendaid'].astype(str).map(MAPA_PROCESSOS).fillna("Outros Processos")
                
                hoje_pd = pd.to_datetime('today').normalize()
                df_open['Dias na Mesa'] = (hoje_pd - pd.to_datetime(df_open['data_inicio_negocio'], errors='coerce').dt.normalize()).dt.days
                df_open['Dias na Mesa'] = df_open['Dias na Mesa'].fillna(0).apply(lambda x: 0 if x < 0 else int(x))
                
                df_open['Data Criação'] = pd.to_datetime(df_open['data_inicio_negocio'], errors='coerce').dt.strftime('%d/%m/%Y')
                df_open['Data Prevista'] = pd.to_datetime(df_open['data_prevista'], errors='coerce').dt.strftime('%d/%m/%Y').fillna('Não informada')
                
                def classificar_temperatura(dias):
                    if dias <= 7: return "🔥 Quente"
                    elif dias <= 14: return "⚠️ Morno"
                    else: return "❄️ Frio"
                
                df_open['Status'] = df_open['Dias na Mesa'].apply(classificar_temperatura)
                
                t_open_setup = df_open['Setup Bruto'].sum()
                t_open_mrr = df_open['MRR Bruto'].sum()
                t_open_geral = df_open['Total Projetado'].sum()
                
                with st.expander("⏳ Pipeline Ativo (Negócios em Aberto)", expanded=True):
                    col_o1, col_o2, col_o3 = st.columns(3)
                    with col_o1: st.markdown(f"""<div class="dash-card" title="Receita Recorrente Mensal (Mensalidade) projetada de todas as propostas em andamento" style="border-top: 5px solid #888; background:#f9f9f9;"><div class="dash-title">MRR Projetado (Na Mesa)</div><div style="font-size:1.5rem; font-weight:900; color:#555;">R$ {f_br(t_open_mrr)}</div></div>""", unsafe_allow_html=True)
                    with col_o2: st.markdown(f"""<div class="dash-card" title="Valor de Implantação/Projeto projetado de todas as propostas em andamento" style="border-top: 5px solid #888; background:#f9f9f9;"><div class="dash-title">Setup Projetado (Na Mesa)</div><div style="font-size:1.5rem; font-weight:900; color:#555;">R$ {f_br(t_open_setup)}</div></div>""", unsafe_allow_html=True)
                    with col_o3: st.markdown(f"""<div class="dash-card" title="Soma total de Setup e MRR que ainda está na mesa de negociação" style="border-top: 5px solid #262730;"><div class="dash-title">Volume Total em Aberto</div><div style="font-size:1.5rem; font-weight:900; color:#262730;">R$ {f_br(t_open_geral)}</div></div>""", unsafe_allow_html=True)
                    
                    if modo_exibicao == "Visão Completa":
                        col_dest1, col_dest2 = st.columns(2)
                        maior_mrr_idx = df_open['MRR Bruto'].idxmax()
                        maior_mrr = df_open.loc[maior_mrr_idx] if df_open['MRR Bruto'].max() > 0 else None
                        maior_setup_idx = df_open['Setup Bruto'].idxmax()
                        maior_setup = df_open.loc[maior_setup_idx] if df_open['Setup Bruto'].max() > 0 else None
                        
                        with col_dest1:
                            if maior_mrr is not None:
                                st.markdown(f"""
                                    <div title="Oportunidade ativa com o maior valor de Recorrência (MRR)" style='background: #f4f8fb; border-left: 6px solid #1976d2; padding: 15px; border-radius: 5px; margin-bottom: 20px; cursor: help;'>
                                        <div style='font-size: 0.8rem; font-weight: 700; color: #1976d2; text-transform: uppercase;'>👑 Maior Contrato Recorrente</div>
                                        <div style='font-size: 1.4rem; font-weight: 900; color: #333;'>{maior_mrr['Cliente']}</div>
                                        <div style='margin-top: 10px; font-size: 0.9rem;'><strong>MRR:</strong> <span style='color:#1976d2; font-weight:bold;'>R$ {f_br(maior_mrr['MRR Bruto'])}</span></div>
                                        <div style='font-size: 0.9rem; color: #666;'>Executivo: {maior_mrr['Vendedor']} | {maior_mrr['Status']} ({maior_mrr['Dias na Mesa']} dias)</div>
                                    </div>
                                """, unsafe_allow_html=True)
                                
                        with col_dest2:
                            if maior_setup is not None:
                                st.markdown(f"""
                                    <div title="Oportunidade ativa com o maior valor de Implantação (Setup)" style='background: #fff8f3; border-left: 6px solid #ff6600; padding: 15px; border-radius: 5px; margin-bottom: 20px; cursor: help;'>
                                        <div style='font-size: 0.8rem; font-weight: 700; color: #ff6600; text-transform: uppercase;'>🚀 Maior Projeto (Setup)</div>
                                        <div style='font-size: 1.4rem; font-weight: 900; color: #333;'>{maior_setup['Cliente']}</div>
                                        <div style='margin-top: 10px; font-size: 0.9rem;'><strong>Setup:</strong> <span style='color:#ff6600; font-weight:bold;'>R$ {f_br(maior_setup['Setup Bruto'])}</span></div>
                                        <div style='font-size: 0.9rem; color: #666;'>Executivo: {maior_setup['Vendedor']} | {maior_setup['Status']} ({maior_setup['Dias na Mesa']} dias)</div>
                                    </div>
                                """, unsafe_allow_html=True)
                        
                        st.markdown("**Radar de Negociações Abertas (Interativo)**")
                        df_open_view = df_open[['id', 'Cliente', 'Status', 'Data Criação', 'Data Prevista', 'Vendedor', 'Setup Bruto', 'MRR Bruto', 'Total Projetado', 'processovendaid']].copy()
                        for col in ['Setup Bruto', 'MRR Bruto', 'Total Projetado']: df_open_view[col] = df_open_view[col].apply(lambda x: f"R$ {f_br(x)}")
                        
                        df_open_visual = df_open_view[['id', 'Cliente', 'Status', 'Data Criação', 'Data Prevista', 'Vendedor', 'Setup Bruto', 'MRR Bruto', 'Total Projetado']].rename(columns={'id': 'Proposta ID', 'Setup Bruto': 'Setup', 'MRR Bruto': 'MRR'})
                        df_open_visual.insert(0, "Ver Extrato", False)
                        
                        render_extrato_abertos(df_open_visual, df_open_view)
                    else:
                        st.markdown("<br>", unsafe_allow_html=True)
                        estilo_titulo = "<div style='background: #ffffff; padding: 10px 15px; border-radius: 6px; box-shadow: 0 2px 5px rgba(0,0,0,0.08); border: 1px solid #eaebf0; color: #262730; font-weight: 700; font-size: 0.95rem; margin-bottom: 5px;'>{}</div>"
                        
                        col_g5, col_g6 = st.columns(2)
                        with col_g5:
                            st.markdown(estilo_titulo.format("Volume Projetado por Temperatura (Status)"), unsafe_allow_html=True)
                            df_status_graf = df_open.groupby('Status', as_index=False)['Total Projetado'].sum()
                            st.markdown(render_html_bar_chart(df_status_graf, 'Status', 'Total Projetado', '#d32f2f'), unsafe_allow_html=True)
                        with col_g6:
                            st.markdown(estilo_titulo.format("Volume Projetado por Executivo"), unsafe_allow_html=True)
                            df_exec_aberto_graf = df_open.groupby('Vendedor', as_index=False)['Total Projetado'].sum()
                            st.markdown(render_html_bar_chart(df_exec_aberto_graf, 'Vendedor', 'Total Projetado', '#ed6c02'), unsafe_allow_html=True)
            else:
                st.info("Não há propostas ativas no funil no momento para o filtro selecionado.")

    except Exception as e:
        st.error(f"Ocorreu um erro interno na tela comercial. Detalhe técnico: {e}")
        
def tela_comissionamento():
    st.markdown("<h1 class='hero-title'>COMISSIONAMENTO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#777; font-size:1.2rem; margin-bottom:30px;'>Auditoria e Fechamento de Pagamentos Integrado ao Bitrix24</p>", unsafe_allow_html=True)
    st.markdown("""<div class="cliente-container"><h3 style="margin:0; color:#262730;">1. Filtros de Apuração de Pagamento</h3></div>""", unsafe_allow_html=True)
    
    hoje = datetime.date.today()
    c1, c2, c3 = st.columns(3)
    data_inicio = c1.date_input("Data Início (Corte)", hoje.replace(day=1), format="DD/MM/YYYY")
    data_fim = c2.date_input("Data Fim (Corte)", hoje, format="DD/MM/YYYY")
    cargo_sel = c3.selectbox("Cargo de Apuração", ["Todos", "Executivo de Vendas", "CS"])

    st.markdown("""<br><div class="mapeamento-container" style="border-left-color:#1976d2;"><h3 style="margin:0; color:#1976d2;">2. Matriz de Auditoria e Espelho de Vendas</h3></div>""", unsafe_allow_html=True)
    df_base = pd.DataFrame()
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            query_bitrix = text("""
                SELECT DISTINCT ON (n.id) n.id AS "Proposta ID", TRIM(CONCAT(COALESCE(ab.name, ''), ' ', COALESCE(ab.lastname, ''))) AS "Vendedor", e.title AS "Cliente", COALESCE(e.ufcrmintegraoreceitauf, 'N/I') AS "Estado", o.closedate AS data_bruta, n.processovendaid AS "Processo ID", COALESCE(o.ufcrmvalorprojeto::text, '0') AS setup_str, COALESCE(o.ufcrmvalorrecorrente::text, o.opportunity::text, '0') AS mrr_str
                FROM orcamento_novo AS o JOIN negocio_novo AS n ON n.id = o.dealId LEFT JOIN assignedby_novo AS ab ON ab.id = n.assignedById LEFT JOIN company_novo AS e ON e.id = n.companyId
                WHERE o.closedate >= :d_inicio AND o.closedate <= :d_fim AND n.closed = 'Y' ORDER BY n.id, o.closedate DESC
            """)
            df_base = pd.read_sql(query_bitrix, conn, params={"d_inicio": data_inicio, "d_fim": data_fim})
    except Exception as e:
        st.error("Falha ao comunicar com o banco de dados. Tente novamente mais tarde.")

    if df_base.empty:
        st.info("Nenhum fechamento encontrado no período selecionado.")
    else:
        df_base['Proposta ID'] = df_base['Proposta ID'].astype(str)
        cf1, cf2 = st.columns(2)
        vendedores_sel = cf1.multiselect("Filtrar por Vendedor(es):", sorted(df_base["Vendedor"].dropna().unique().tolist()), placeholder="Todos selecionados por padrão")
        if vendedores_sel: df_base = df_base[df_base['Vendedor'].isin(vendedores_sel)]
            
        estados_sel = cf2.multiselect("Filtrar por Região (UF):", sorted(df_base["Estado"].dropna().unique().tolist()), placeholder="Todas as regiões selecionadas por padrão")
        if estados_sel: df_base = df_base[df_base['Estado'].isin(estados_sel)]
            
        if df_base.empty:
            st.warning("Nenhum dado corresponde aos filtros selecionados.")
            return

        df_base['Data Venda'] = pd.to_datetime(df_base['data_bruta']).dt.strftime('%d/%m/%Y')
        df_base['Setup Bruto (R$)'] = df_base['setup_str'].apply(parse_currency)
        df_base['MRR Bruto (R$)'] = df_base['mrr_str'].apply(parse_currency)
        df_base['% Setup'] = 5.0 if cargo_sel != "CS" else 10.0
        df_base['% MRR'] = 5.0 if cargo_sel != "CS" else 10.0
        
        mask_despesa = df_base['Processo ID'].astype(str) == '2812'
        df_base.loc[mask_despesa, '% Setup'] = 0.0
        df_base.loc[mask_despesa, '% MRR'] = 0.0
        
        df_base['Comissão Setup (R$)'] = df_base['Setup Bruto (R$)'] * (df_base['% Setup'] / 100)
        df_base['Comissão MRR (R$)'] = df_base['MRR Bruto (R$)'] * (df_base['% MRR'] / 100)
        df_base['Total Líquido (R$)'] = df_base['Comissão Setup (R$)'] + df_base['Comissão MRR (R$)']

        t_setup_comis, t_mrr_comis, t_geral = df_base['Comissão Setup (R$)'].sum(), df_base['Comissão MRR (R$)'].sum(), df_base['Total Líquido (R$)'].sum()
        df_exibicao = df_base.copy()
        for col in ['Setup Bruto (R$)', 'MRR Bruto (R$)', 'Comissão Setup (R$)', 'Comissão MRR (R$)', 'Total Líquido (R$)']: df_exibicao[col] = df_exibicao[col].apply(lambda x: f"R$ {f_br(x)}")
            
        df_exibicao_limpa = df_exibicao[["Vendedor", "Proposta ID", "Cliente", "Estado", "Data Venda", "Setup Bruto (R$)", "MRR Bruto (R$)", "% Setup", "% MRR", "Comissão Setup (R$)", "Comissão MRR (R$)", "Total Líquido (R$)"]]
        df_exibicao_limpa.insert(0, "Ver Extrato", False)
        
        edited_df = st.data_editor(df_exibicao_limpa, use_container_width=True, hide_index=True, column_config={"Ver Extrato": st.column_config.CheckboxColumn("Ver Extrato", default=False)}, disabled=[col for col in df_exibicao_limpa.columns if col != "Ver Extrato"])
        linhas_selecionadas = edited_df[edited_df["Ver Extrato"] == True]
        
        if not linhas_selecionadas.empty:
            prop_id = linhas_selecionadas.iloc[0]["Proposta ID"]
            modal_extrato_venda(prop_id, linhas_selecionadas.iloc[0]["Cliente"], df_base[df_base["Proposta ID"].astype(str) == str(prop_id)]["Processo ID"].values[0])

        st.markdown("""<br><div class="cliente-container" style="border-left-color:#2e7d32;"><h3 style="margin:0; color:#2e7d32;">3. Consolidação e Fechamento</h3></div>""", unsafe_allow_html=True)
        col_tot1, col_tot2, col_tot4 = st.columns([1, 1, 2])
        with col_tot1: st.markdown(f"""<div class="dash-card" style="border-top: 5px solid #ff6600;"><div class="dash-title">Total Setup a Pagar</div><div style="font-size:1.8rem; font-weight:900; color:#262730;">R$ {f_br(t_setup_comis)}</div></div>""", unsafe_allow_html=True)
        with col_tot2: st.markdown(f"""<div class="dash-card" style="border-top: 5px solid #2e7d32;"><div class="dash-title">Total MRR a Pagar</div><div style="font-size:1.8rem; font-weight:900; color:#262730;">R$ {f_br(t_mrr_comis)}</div></div>""", unsafe_allow_html=True)
        with col_tot4: st.markdown(f"""<div class="dash-card" style="border-top: 5px solid #262730; background:#f4f6f9;"><div class="dash-title">TOTAL LÍQUIDO A PAGAR</div><div style="font-size:1.8rem; font-weight:900; color:#262730;">R$ {f_br(t_geral)}</div></div>""", unsafe_allow_html=True)

        st.write("---")
        c_btn1, c_btn2 = st.columns([1, 1])
        with c_btn1:
            st.download_button(label="📥 Exportar Relatório Contábil (CSV)", data=df_base.drop(columns=['setup_str', 'mrr_str']).to_csv(index=False, sep=';', decimal=',').encode('utf-8'), file_name=f"comissoes_fechamento.csv", mime="text/csv", use_container_width=True)
        with c_btn2:
            if st.button("🔒 Efetivar Lote de Pagamento", type="primary", use_container_width=True): st.success("Operação bloqueada com sucesso.")

# ==========================================
# BLOCO 3: APLICATIVO PRINCIPAL (UI E LÓGICA)
# ==========================================
def aplicativo_principal():
    st.markdown("""
        <style>
        .stApp { background: linear-gradient(135deg, #ffffff 0%, #fff5ed 100%); }
        .hero-title { color: #262730; font-size: 4.5rem; font-weight: 900; margin: 0; line-height: 1; text-transform: uppercase; letter-spacing: -3px; }
        .mapeamento-container { background-color: #ffffff; border-left: 10px solid #ff6600; padding: 20px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
        .cliente-container { background-color: #ffffff; border-left: 10px solid #262730; padding: 20px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
        .resumo-card { background-color: #ffffff; border: 1px solid #f0f0f0; border-top: 8px solid #ff6600; padding: 25px; border-radius: 8px; min-height: 450px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); display: flex; flex-direction: column; }
        .resumo-valor { color: #ff6600; font-size: 2.3rem; font-weight: 900; margin-bottom: 5px; }
        .item-detalhe { color: #333; font-size: 0.82rem; font-weight: 600; background-color: #fcfcfc; padding: 2px 8px; border-radius: 4px; border: 1px solid #eee; white-space: nowrap; }
        .section-header { background: linear-gradient(90deg, #ff6600 0%, #ff944d 100%); padding: 8px 15px; border-radius: 5px; margin-bottom: 15px; margin-top: 20px; }
        .section-title { color: #ffffff; font-size: 1.1rem; font-weight: bold; margin: 0; }
        .lista-itens { list-style-type: none; padding-left: 0; margin-top: 10px; flex-grow: 1; }
        .lista-itens li { padding: 8px 0; border-bottom: 1px dashed #e0e0e0; display: flex; justify-content: space-between; align-items: center; gap: 15px; }
        .lista-itens li span:first-child { font-weight: bold; font-size: 0.88rem; color: #444; }
        .item-incluso { padding-left: 20px !important; color: #777; font-size: 0.85rem; font-style: italic; border-bottom: none !important; }
        
        .dash-card { background: #fff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); text-align: center; }
        .dash-title { color: #888; font-size: 0.9rem; font-weight: bold; text-transform: uppercase; margin-bottom: 10px; }
        .dash-val { font-size: 2.2rem; font-weight: 900; color: #262730; margin-bottom: 5px; }
        .dash-progress-bg { background: #f0f0f0; height: 12px; border-radius: 6px; width: 100%; margin: 10px 0; overflow: hidden; }
        .dash-progress-fill { height: 100%; border-radius: 6px; transition: width 0.5s ease; }
        </style>
    """, unsafe_allow_html=True)

    def processar_regras_colaterais():
        dv = st.session_state.data_vault
        novos_auto = {}
        for m_nome in dv['sel_m']:
            qtd_pai = int(dv['quantidades'].get(m_nome, 0))
            p_id = name_to_id.get(m_nome)
            if p_id and p_id in vinculos_db and qtd_pai > 0:
                for r in vinculos_db[p_id]:
                    if r['tipo'] in ['projeto', 'adesao']:
                        f_nome = id_to_name.get(r['id_filho'])
                        if f_nome: 
                            qtd_filho = int(r['qtd'] * qtd_pai)
                            if f_nome not in novos_auto or qtd_filho > novos_auto[f_nome]:
                                novos_auto[f_nome] = qtd_filho

        lista_servicos_atual = list(dv['sel_i'])
        for item in list(dv['auto_added']):
            if item not in novos_auto:
                if item in lista_servicos_atual:
                    lista_servicos_atual.remove(item)
                    dv['quantidades'][item] = 0
                dv['auto_added'].remove(item)

        for item, qtd in novos_auto.items():
            if item not in lista_servicos_atual:
                lista_servicos_atual.append(item)
            dv['quantidades'][item] = qtd
            if item not in dv['auto_added']:
                dv['auto_added'].append(item)
            
        dv['sel_i'] = lista_servicos_atual

    def limpar_tudo():
        st.session_state.form_rc += 1 # Blindagem contra ui ghosting
        st.session_state.data_vault = {
            'sel_m': [], 'sel_i': [], 'sel_d': [], 'auto_added': [],
            'quantidades': {}, 'setup_sistemas': {}, 'descontos_itens': {},
            'despesas_valores': {}, 'negociar': {},
            'mapeamento': {
                'm_combo': "Montar Manualmente", 'm_pdv_conv': 0, 'm_pdv_touch': 0, 'm_pdv_self': 0, 'm_semanas': 0, 'm_mobile': 0,
                'm_tef': "Nao utiliza", 'm_migracao': False, 'm_ecommerce': False, 'm_app': False, 'm_connect': False,
                'm_erp_pro': False, 'm_xml': False, 'm_escopo': False, 'm_controller': False, 'm_cartaz': False, 'm_masterfisco': False, 'm_backup': False,
            }
        }
        st.session_state.perma_nome_cliente = ""
        st.session_state.perma_cnpj_cliente = ""
        st.session_state.proposta_carregada_id = None
        st.session_state.show_digital_proposal = False
        st.session_state.fin_sim_ativa = False
        st.session_state.has_unsaved_changes = False

    def sync_combo():
        mark_unsaved()
        rc = st.session_state.form_rc
        dv = st.session_state.data_vault
        n_combo = st.session_state.get(f"ui_m_combo_{rc}", "Montar Manualmente")
        dv['mapeamento']['m_combo'] = n_combo
        
        if n_combo == "Padrao Pequeno Porte":
            dv['mapeamento'].update({
                'm_pdv_touch': 0, 'm_pdv_self': 0, 'm_ecommerce': False, 'm_app': False, 'm_connect': False, 'm_controller': False, 'm_cartaz': False, 'm_masterfisco': False, 'm_backup': False, 'm_semanas': 0,
                'm_erp_pro': True, 'm_pdv_conv': 3, 'm_xml': True, 'm_mobile': 1, 'm_tef': "SiTef Express", 'm_migracao': True, 'm_escopo': True
            })
            st.session_state.form_rc += 1 # Força atualização visual blindada

    rc = st.session_state.form_rc

    # ==========================================
    # SIDEBAR E ROTEAMENTO (BLINDADO PARA FINANÇAS)
    # ==========================================
    with st.sidebar:
        if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=180)
        st.markdown(f"<div style='background-color:#f0f0f0; padding:10px; border-radius:5px; margin-bottom:15px; border-left:4px solid #ff6600;'><span style='font-weight:bold; color:#333;'>Usuário: {html.escape(st.session_state.user_name)}</span></div>", unsafe_allow_html=True)
        
        if st.session_state.has_unsaved_changes and st.session_state.perma_nome_cliente:
            st.markdown("<div style='background-color:#fff3cd; color:#856404; padding:8px; border-radius:4px; font-size:0.8rem; border-left:3px solid #ffeeba; margin-bottom:15px;'>Atenção: Alterações não salvas</div>", unsafe_allow_html=True)

        # Garantir valor inicial para evitar erros de renderização
        if 'aba_atual' not in st.session_state or not st.session_state.aba_atual:
            st.session_state.aba_atual = "Diagnóstico" if st.session_state.user_role == "consultor" else "Início"

        role = st.session_state.user_role
        
        # Motor de renderização dos botões limpos
        def render_nav_button(label):
            is_active = (st.session_state.get('aba_atual') == label)
            if st.button(label, type="primary" if is_active else "secondary", use_container_width=True):
                st.session_state.aba_atual = label
                st.rerun()

        # ---------------------------------------------
        # CONSTRUÇÃO DO MENU EM GAVETAS (EXPANDERS)
        # ---------------------------------------------
        if role == "consultor":
            with st.expander("Operação Comercial", expanded=True):
                render_nav_button("Diagnóstico")
                
        elif role == "financeiro":
            with st.expander("Financeiro", expanded=True):
                render_nav_button("Início")
                render_nav_button("Faturamento")
                render_nav_button("Comissionamento")
                
        else:
            simulando = st.toggle("Simular Visão Vendedor", key="toggle_simular_vendedor") if role in ["admin", "projetos"] else False
            
            with st.expander("Operação Comercial", expanded=True):
                render_nav_button("Início")
                render_nav_button("Diagnóstico")
                render_nav_button("Gerador de Proposta")
                render_nav_button("Minhas Propostas")
                render_nav_button("Consulta de Preco")
                
            with st.expander("Inteligência Estratégica", expanded=True):
                render_nav_button("Visão Comercial")
                
            if not simulando:
                if role == "admin":
                    # Gavetas gerenciais iniciam fechadas para não poluir a visão
                    with st.expander("Controladoria Financeira", expanded=False):
                        render_nav_button("Faturamento")
                        render_nav_button("Comissionamento")
                        
                    with st.expander("Backoffice e Gestão", expanded=False):
                        render_nav_button("Visão do Gestor")
                        render_nav_button("Painel Admin")
                        
                elif role == "projetos":
                    with st.expander("Backoffice e Gestão", expanded=False):
                        render_nav_button("Painel Admin")

        # Alimenta o motor central com a aba selecionada nas gavetas
        tela = st.session_state.aba_atual

        if tela == "Gerador de Proposta":
            st.write("---")
            mapeamento_ativo = st.toggle("Mapeamento Inteligente", value=False)
            st.toggle("Modo Apresentação", key="modo_apresentacao")
            perfil_venda = st.selectbox("Perfil do Cliente", ["Com Despesas", "Sem Despesas"])
            
            c_md = st.session_state.get('modo_desconto', 'Total')
            n_md = st.radio("Modo de Desconto", ["Total", "Item"], index=0 if c_md == "Total" else 1, key=f"ui_modo_desconto_{rc}", on_change=mark_unsaved)
            st.session_state.modo_desconto = n_md
            
            if st.session_state.modo_desconto == "Total":
                c_desc = float(st.session_state.get('g_desc_mensalidade', 0.0))
                n_desc = st.number_input("Desconto Total Mensalidade (%)", 0.0, 100.0, value=c_desc, step=0.5, key=f"ui_g_desc_mensalidade_{rc}", on_change=mark_unsaved)
                st.session_state.g_desc_mensalidade = n_desc
            else:
                st.info("Desconto Ativado por Item (Acesse as engrenagens na coluna de Sistemas).")
                st.session_state.g_desc_mensalidade = 0.0
                
            exibir_detalhe_desc = st.toggle("Exibir Desconto na Tela", value=True)
            exibir_media_loja = st.toggle("Exibir Media por Loja", value=False)
            
            c_fat = st.session_state.get('g_faturamento', "Na assinatura")
            op_fat = ["Na assinatura", "30 dias", "60 dias", "Após implantação"]
            n_fat = st.selectbox("Início Mensalidade", op_fat, index=op_fat.index(c_fat) if c_fat in op_fat else 0, key=f"ui_g_faturamento_{rc}", on_change=mark_unsaved)
            st.session_state.g_faturamento = n_fat
            
            c_parc = int(st.session_state.get('g_parcelas_setup', 4))
            op_parc = [1, 2, 3, 4, 5, 6, 10, 12]
            n_parc = st.selectbox("Parcelas Setup", op_parc, index=op_parc.index(c_parc) if c_parc in op_parc else 3, key=f"ui_g_parcelas_{rc}", on_change=mark_unsaved)
            st.session_state.g_parcelas_setup = n_parc
            
            c_reg = st.session_state.get('g_regra_desp', "Faturamento na assinatura")
            op_reg = ["Faturamento na assinatura", "Faturamento pós Implantação"]
            n_reg = st.selectbox("Faturamento Despesas", op_reg, index=op_reg.index(c_reg) if c_reg in op_reg else 0, key=f"ui_g_regra_desp_{rc}", on_change=mark_unsaved)
            st.session_state.g_regra_desp = n_reg
            
        st.write("---")
        if st.button("Sair (Logout)", use_container_width=True): st.session_state.clear(); st.rerun()
        st.markdown(f"""<hr><div style="font-size:0.8rem; color:{db_cor};">{db_status}</div><div style="font-size:0.7rem; color:#888;">{APP_VERSION}</div>""", unsafe_allow_html=True)

    # ==========================================
    # TELA 0: INÍCIO
    # ==========================================
    if tela == "Início":
        st.markdown(f"""<h1 class="hero-title">BEM-VINDO(A), {html.escape(str(st.session_state.user_name).split()[0].upper())}!</h1>""", unsafe_allow_html=True)
        
        if st.session_state.user_role == "financeiro":
            st.markdown(f"""<p style="color:#777; font-size:1.2rem; margin-bottom:30px;"><b>Controladoria e Faturamento</b> | VR Software</p>""", unsafe_allow_html=True)
            st.info("Utilize o menu lateral para acessar a Central de Faturamento e gerar os documentos financeiros para os clientes.")
            
        else:
            st.markdown(f"""<p style="color:#777; font-size:1.2rem; margin-bottom:30px;">Painel de Performance | <b>{st.session_state.user_cargo}</b> ({st.session_state.user_senioridade})</p>""", unsafe_allow_html=True)

            metas_matriz = {
                "Executivo de Vendas": {
                    "Júnior": {"proj": 80000.0, "rec": 14000.0, "premio": 2090.00},
                    "Pleno": {"proj": 88000.0, "rec": 18200.0, "premio": 2868.79},
                    "Sênior": {"proj": 98560.0, "rec": 22660.0, "premio": 3628.77},
                    "Junior": {"proj": 80000.0, "rec": 14000.0, "premio": 2090.00},
                    "Senior": {"proj": 98560.0, "rec": 22660.0, "premio": 3628.77},
                },
                "CS": {
                    "Júnior": {"proj": 17100.0, "rec": 18150.0, "premio": 1897.50},
                    "Pleno": {"proj": 21450.0, "rec": 21500.0, "premio": 2238.50},
                    "Sênior": {"proj": 24750.0, "rec": 26220.0, "premio": 2580.60},
                    "Junior": {"proj": 17100.0, "rec": 18150.0, "premio": 1897.50},
                    "Senior": {"proj": 24750.0, "rec": 26220.0, "premio": 2580.60},
                }
            }
            
            c = st.session_state.user_cargo if st.session_state.user_cargo in metas_matriz else "Executivo de Vendas"
            s = st.session_state.user_senioridade if st.session_state.user_senioridade in metas_matriz[c] else "Pleno"
            m_proj, m_rec, p_base = metas_matriz[c][s]["proj"], metas_matriz[c][s]["rec"], metas_matriz[c][s]["premio"]

            hoje = datetime.date.today()
            q = (hoje.month - 1) // 3 + 1
            mes_inicio = 3 * q - 2
            d_inicio_tri = datetime.date(hoje.year, mes_inicio, 1)
            if q == 4: d_fim_tri = datetime.date(hoje.year + 1, 1, 1) - datetime.timedelta(days=1)
            else: d_fim_tri = datetime.date(hoje.year, mes_inicio + 3, 1) - datetime.timedelta(days=1)
            
            t_proj_crm, t_rec_crm, t_proj_ext, t_rec_ext = 0.0, 0.0, 0.0, 0.0
            
            try:
                engine = get_db_engine()
                with engine.connect() as conn:
                    r_crm = pd.read_sql(text("SELECT SUM(valor_setup) as setup, SUM(valor_mensal) as mensal FROM propostas WHERE vendedor_email = :e AND status = 'Contrato Assinado' AND data_atualizacao >= :start AND data_atualizacao <= :end"), conn, params={"e": st.session_state.user_email, "start": d_inicio_tri, "end": d_fim_tri})
                    if not r_crm.empty: t_proj_crm, t_rec_crm = float(r_crm['setup'].iloc[0] or 0.0), float(r_crm['mensal'].iloc[0] or 0.0)
                    r_ext = pd.read_sql(text("SELECT SUM(valor_projeto) as setup, SUM(valor_recorrente) as mensal FROM vendas_externas WHERE vendedor_email = :e AND mes_referencia >= :start AND mes_referencia <= :end"), conn, params={"e": st.session_state.user_email, "start": d_inicio_tri, "end": d_fim_tri})
                    if not r_ext.empty: t_proj_ext, t_rec_ext = float(r_ext['setup'].iloc[0] or 0.0), float(r_ext['mensal'].iloc[0] or 0.0)
            except Exception: pass
                
            realizado_proj, realizado_rec = t_proj_crm + t_proj_ext, t_rec_crm + t_rec_ext
            pct_proj = realizado_proj / m_proj if m_proj > 0 else 0
            pct_rec = realizado_rec / m_rec if m_rec > 0 else 0
            pct_global = (pct_proj * 0.4) + (pct_rec * 0.6)
            premio_projetado = p_base * pct_global

            st.markdown(f"""<h3 style="color:#262730; margin-bottom:20px;">O Grande Alvo (Trimestre Q{q})</h3>""", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f"""<div class="dash-card" style="border-top: 5px solid #ff6600;"><div class="dash-title">Meta de Setup / Projeto (40%)</div><div class="dash-val">R$ {f_br(realizado_proj)}</div><div style="color:#777; font-size:0.85rem; margin-bottom:10px;">Alvo: R$ {f_br(m_proj)}</div><div class="dash-progress-bg"><div class="dash-progress-fill" style="width: {min(pct_proj*100, 100)}%; background-color: #ff6600;"></div></div><div style="font-weight:bold; color:#ff6600;">{pct_proj*100:.1f}% Atingido</div></div>""", unsafe_allow_html=True)
            with c2: st.markdown(f"""<div class="dash-card" style="border-top: 5px solid #2e7d32;"><div class="dash-title">Meta de MRR / Recorrente (60%)</div><div class="dash-val">R$ {f_br(realizado_rec)}</div><div style="color:#777; font-size:0.85rem; margin-bottom:10px;">Alvo: R$ {f_br(m_rec)}</div><div class="dash-progress-bg"><div class="dash-progress-fill" style="width: {min(pct_rec*100, 100)}%; background-color: #2e7d32;"></div></div><div style="font-weight:bold; color:#2e7d32;">{pct_rec*100:.1f}% Atingido</div></div>""", unsafe_allow_html=True)
            with c3: st.markdown(f"""<div class="dash-card" style="border-top: 5px solid #262730; background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);"><div class="dash-title">Premiação Projetada</div><div class="dash-val" style="color:#262730;">R$ {f_br(premio_projetado)}</div><div style="color:#777; font-size:0.85rem; margin-bottom:10px;">Prêmio Base 100%: R$ {f_br(p_base)}</div><div class="dash-progress-bg"><div class="dash-progress-fill" style="width: {min(pct_global*100, 100)}%; background-color: #262730;"></div></div><div style="font-weight:900; font-size:1.1rem; color:#262730;">Atingimento Global: {pct_global*100:.1f}%</div></div>""", unsafe_allow_html=True)

            st.markdown("<br><hr>", unsafe_allow_html=True)
            c_mes, c_act = st.columns([2, 1])
            with c_mes:
                st.markdown(f"""<h4 style="color:#262730; margin-bottom:15px;">Bússola Mensal (Alvo do Mês Atual)</h4><div style="background:#fff; padding:15px; border-radius:8px; border-left: 4px solid #1976d2; box-shadow: 0 2px 10px rgba(0,0,0,0.05);"><p style="margin:0; color:#444; font-size:1.05rem;">A sua meta fracionada para manter o ritmo este mês é de <b>R$ {f_br(m_proj/3)}</b> em Setup e <b>R$ {f_br(m_rec/3)}</b> em Recorrente.</p></div>""", unsafe_allow_html=True)
                if st.session_state.meta_regiao > 0:
                    st.markdown(f"""<h4 style="color:#262730; margin-top:25px; margin-bottom:15px;">Espírito de Equipe ({html.escape(st.session_state.unidade_nome)})</h4><div style="background:#fff; padding:15px; border-radius:8px; border-left: 4px solid #ffcc00; box-shadow: 0 2px 10px rgba(0,0,0,0.05);"><p style="margin:0; color:#444; font-size:1.05rem;">A meta global da sua unidade regional é de <b>R$ {f_br(st.session_state.meta_regiao)}</b>.</p></div>""", unsafe_allow_html=True)

            with c_act:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("➕ Criar Nova Proposta", use_container_width=True, type="primary"):
                    limpar_tudo()
                    st.session_state.aba_atual = "Gerador de Proposta"
                    st.rerun()
                if st.button("📂 Continuar Negociações", use_container_width=True):
                    st.session_state.aba_atual = "Minhas Propostas"
                    st.rerun()

    # ==========================================
    # TELA NOVA: MÓDULO FINANCEIRO (FATURAMENTO)
    # ==========================================
    elif tela == "Faturamento":
        st.markdown("<h1 class='hero-title'>CENTRAL DE FATURAMENTO</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#777; font-size:1.2rem; margin-bottom:30px;'>Geração do Documento Financeiro e Rateio Automático de Contratos</p>", unsafe_allow_html=True)

        st.markdown("""<div class="cliente-container"><h3 style="margin:0; color:#262730;">1. Dados da Operação</h3></div>""", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        nome_fin = c1.text_input("Nome do Cliente", placeholder="Ex: Supermercados Dois Irmãos")
        cnpj_fin = c2.text_area("CNPJs do Contrato", placeholder="Insira um ou mais CNPJs", height=68)

        c3, c4, c5 = st.columns(3)
        with c3:
            setup_str = st.text_input("Valor Total do Setup (R$)", value=st.session_state.get('fin_setup_str', ""), placeholder="Ex: 15000,00")
            st.session_state.fin_setup_str = setup_str
            val_setup_fin = parse_currency(setup_str)
            st.markdown(f"<div style='font-size:1rem; font-weight:bold; color:#ff6600; margin-top:-10px; margin-bottom:15px;'>R$ {f_br(val_setup_fin)}</div>", unsafe_allow_html=True)

        with c4:
            mensal_str = st.text_input("Valor Total da Mensalidade (R$)", value=st.session_state.get('fin_mensal_str', ""), placeholder="Ex: 2500,00")
            st.session_state.fin_mensal_str = mensal_str
            val_mensal_fin = parse_currency(mensal_str)
            st.markdown(f"<div style='font-size:1rem; font-weight:bold; color:#2e7d32; margin-top:-10px; margin-bottom:15px;'>R$ {f_br(val_mensal_fin)}</div>", unsafe_allow_html=True)

        with c5:
            qtd_parcelas_fin = st.number_input("Qtd. de Parcelas do Setup", min_value=1, max_value=36, value=6, step=1)

        st.markdown("""<br><div class="mapeamento-container"><h3 style="margin:0; color:#ff6600;">2. Parâmetros de Faturamento</h3></div>""", unsafe_allow_html=True)
        
        tipo_rateio = st.radio("Selecione a regra de divisão de faturamento:", ["Padrão da Unidade (Matriz 10% / VR Recife 90%)", "Ajuste Personalizado de Rateio"], horizontal=True)

        if "Padrão" in tipo_rateio:
            pct_matriz_setup = 10.0
            pct_filial_setup = 90.0
            pct_matriz_mensal = 10.0
            pct_filial_mensal = 90.0
            st.info("O sistema calculará automaticamente o repasse de 10% para a Matriz e 90% para a VR Recife.")
        else:
            st.markdown("<strong style='color:#262730;'>Composição do Setup (Implantação)</strong>", unsafe_allow_html=True)
            crs1, crs2 = st.columns(2)
            pct_matriz_setup = crs1.number_input("% Rateio Matriz (Setup)", min_value=0.0, max_value=100.0, value=10.0, step=1.0)
            pct_filial_setup = crs2.number_input("% Rateio VR Recife (Setup)", min_value=0.0, max_value=100.0, value=100.0 - pct_matriz_setup, step=1.0)
            
            st.markdown("<strong style='color:#262730;'>Composição da Mensalidade (Recorrente)</strong>", unsafe_allow_html=True)
            crm1, crm2 = st.columns(2)
            pct_matriz_mensal = crm1.number_input("% Rateio Matriz (Mensalidade)", min_value=0.0, max_value=100.0, value=10.0, step=1.0)
            pct_filial_mensal = crm2.number_input("% Rateio VR Recife (Mensalidade)", min_value=0.0, max_value=100.0, value=100.0 - pct_matriz_mensal, step=1.0)

            if round(pct_matriz_setup + pct_filial_setup, 2) != 100.0 or round(pct_matriz_mensal + pct_filial_mensal, 2) != 100.0:
                st.warning("Atenção: A soma dos percentuais deve fechar exatamente em 100%.")

        if st.button("Processar Composição Financeira", type="primary", use_container_width=True):
            if val_setup_fin == 0 and val_mensal_fin == 0:
                st.error("Insira o valor do Setup ou da Mensalidade para processar.")
            elif round(pct_matriz_setup + pct_filial_setup, 2) == 100.0 and round(pct_matriz_mensal + pct_filial_mensal, 2) == 100.0:
                st.session_state.fin_sim_ativa = True
                
        if st.session_state.get('fin_sim_ativa'):
            st.markdown("<hr><h2 style='text-align:center; color:#262730;'>ESPELHO DE FATURAMENTO</h2>", unsafe_allow_html=True)
            
            mensal_matriz = val_mensal_fin * (pct_matriz_mensal / 100.0)
            mensal_filial = val_mensal_fin * (pct_filial_mensal / 100.0)
            setup_matriz = val_setup_fin * (pct_matriz_setup / 100.0)
            setup_filial = val_setup_fin * (pct_filial_setup / 100.0)
            
            parcela_matriz_base = round(setup_matriz / qtd_parcelas_fin, 2) if qtd_parcelas_fin > 0 else 0.0
            parcela_filial_base = round(setup_filial / qtd_parcelas_fin, 2) if qtd_parcelas_fin > 0 else 0.0
            
            ultima_matriz = round(setup_matriz - (parcela_matriz_base * (qtd_parcelas_fin - 1)), 2) if qtd_parcelas_fin > 0 else 0.0
            ultima_filial = round(setup_filial - (parcela_filial_base * (qtd_parcelas_fin - 1)), 2) if qtd_parcelas_fin > 0 else 0.0

            col_res1, col_res2 = st.columns(2)
            with col_res1:
                st.markdown(f"""
                <div style="background-color:#ffffff; border-top: 6px solid #262730; padding:20px; border-radius:8px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
                    <h4 style="margin:0; color:#262730;">VR SOFTWARE MATRIZ</h4>
                    <hr>
                    <p style="margin:0; color:#777; font-size:0.9rem;">Mensalidade Recorrente ({pct_matriz_mensal}%):</p>
                    <h3 style="margin:0 0 15px 0; color:#2e7d32;">R$ {f_br(mensal_matriz)}</h3>
                    <p style="margin:0; color:#777; font-size:0.9rem;">Total Implantação Setup ({pct_matriz_setup}%):</p>
                    <h3 style="margin:0 0 15px 0; color:#ff6600;">R$ {f_br(setup_matriz)}</h3>
                </div>
                """, unsafe_allow_html=True)
                
            with col_res2:
                st.markdown(f"""
                <div style="background-color:#ffffff; border-top: 6px solid #ff6600; padding:20px; border-radius:8px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
                    <h4 style="margin:0; color:#ff6600;">VR RECIFE</h4>
                    <hr>
                    <p style="margin:0; color:#777; font-size:0.9rem;">Mensalidade Recorrente ({pct_filial_mensal}%):</p>
                    <h3 style="margin:0 0 15px 0; color:#2e7d32;">R$ {f_br(mensal_filial)}</h3>
                    <p style="margin:0; color:#777; font-size:0.9rem;">Total Implantação Setup ({pct_filial_setup}%):</p>
                    <h3 style="margin:0 0 15px 0; color:#ff6600;">R$ {f_br(setup_filial)}</h3>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br><h4 style='color:#262730;'>Cronograma de Faturamento</h4>", unsafe_allow_html=True)
            
            lista_parcelas = []
            html_linhas_tabela = ""
            
            if qtd_parcelas_fin > 0 and val_setup_fin > 0:
                for i in range(1, qtd_parcelas_fin + 1):
                    v_matriz = ultima_matriz if i == qtd_parcelas_fin else parcela_matriz_base
                    v_filial = ultima_filial if i == qtd_parcelas_fin else parcela_filial_base
                    lista_parcelas.append({
                        "Parcela": f"{i}/{qtd_parcelas_fin} (Setup)",
                        "Cobrança VR Matriz": f"R$ {f_br(v_matriz)}",
                        "Cobrança VR Recife": f"R$ {f_br(v_filial)}",
                        "Total Mês": f"R$ {f_br(v_matriz + v_filial)}"
                    })
                    html_linhas_tabela += f"<tr><td>{i}/{qtd_parcelas_fin}</td><td class='highlight'>R$ {f_br(v_matriz)}</td><td class='highlight'>R$ {f_br(v_filial)}</td><td>R$ {f_br(v_matriz + v_filial)}</td></tr>"
            
            if val_mensal_fin > 0:
                lista_parcelas.append({
                    "Parcela": "Mensalidade (Após Implantação)",
                    "Cobrança VR Matriz": f"R$ {f_br(mensal_matriz)}",
                    "Cobrança VR Recife": f"R$ {f_br(mensal_filial)}",
                    "Total Mês": f"R$ {f_br(mensal_matriz + mensal_filial)}"
                })
                html_linhas_tabela += f"<tr><td class='highlight-mensal'>Mensalidade (Recorrente)</td><td class='highlight-mensal'>R$ {f_br(mensal_matriz)}</td><td class='highlight-mensal'>R$ {f_br(mensal_filial)}</td><td class='highlight-mensal'>R$ {f_br(mensal_matriz + mensal_filial)}</td></tr>"
            
            st.dataframe(pd.DataFrame(lista_parcelas), use_container_width=True, hide_index=True)

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Gerar Documento de Boas-Vindas (PDF)", use_container_width=True):
                st.session_state.html_welcome_pack = renderizar_welcome_pack(
                    nome=html.escape(nome_fin), cnpjs=html.escape(cnpj_fin), val_setup=val_setup_fin, val_mensal=val_mensal_fin, parcelas_html=html_linhas_tabela
                )
                st.session_state.show_welcome_pack = True
                st.rerun()

        if st.session_state.get('show_welcome_pack', False):
            st.markdown("---")
            st.markdown("<h2 style='text-align:center; color:#ff6600;'>Visualização do Documento Digital</h2>", unsafe_allow_html=True)
            st.info("Clique no botão 'Salvar PDF / Imprimir' dentro do quadro abaixo.")
            components.html(st.session_state.html_welcome_pack, height=1000, scrolling=True)
            col_fw1, col_fw2, col_fw3 = st.columns([1, 1, 1])
            if col_fw2.button("Fechar Visualização", use_container_width=True): 
                st.session_state.show_welcome_pack = False
                st.rerun()

    # ==========================================
    # TELA GERADOR DE PROPOSTA
    # ==========================================
    elif tela == "Gerador de Proposta":
        dv = st.session_state.data_vault
        md = dv['mapeamento']

        def aplicar_mapeamento():
            _sel_m, _sel_i, _sel_d = [], [], []
            for k in full_db.keys(): dv['quantidades'][k] = 0

            for p_name in sistemas_db.keys():
                qtd = 0
                if p_name == "VR PDV Convencional": qtd = int(md.get('m_pdv_conv', 0))
                elif p_name == "VR PDV Touchscreen": qtd = int(md.get('m_pdv_touch', 0))
                elif p_name == "VR PDV Self Checkout": qtd = int(md.get('m_pdv_self', 0))
                elif p_name == "VR ERP PRO" and md.get('m_erp_pro'): qtd = 1
                elif p_name == "VR Gerenciador Xml" and md.get('m_xml'): qtd = 1
                elif p_name == "VR Connect (Android/IOS)" and md.get('m_connect'): qtd = 1
                elif p_name == "VR Backup 050 Gb" and md.get('m_backup'): qtd = 1
                elif p_name == "VR Cartaz" and md.get('m_cartaz'): qtd = 1
                elif p_name == "VR E-Commerce" and md.get('m_ecommerce'): qtd = 1
                elif p_name == "VR Controller 360 ( 1 CNPJ )" and md.get('m_controller'): qtd = 1
                elif p_name == "VR Masterfisco Brasil" and md.get('m_masterfisco'): qtd = 1
                elif p_name == "VR M-Commerce" and md.get('m_app'): qtd = 1
                elif p_name == "VR Mobile (Smartphone/Android)": qtd = int(md.get('m_mobile', 0))

                if md.get('m_tef') == "SiTef Express":
                    tot = int(md.get('m_pdv_conv',0)) + int(md.get('m_pdv_touch',0)) + int(md.get('m_pdv_self',0))
                    if tot <= 3 and p_name == "VR Sitef Express ate 3 PDVs": qtd = 1
                    elif 3 < tot <= 6 and p_name == "VR Sitef Express ate 6 PDVs": qtd = 1
                    elif 6 < tot <= 8 and p_name == "VR Sitef Express ate 8 PDVs": qtd = 1
                    elif tot > 8 and p_name == "VR Sitef Express a partir 9 PDVs": qtd = 1
                elif md.get('m_tef') == "VR TEF" and p_name.lower() == "vr tef": qtd = 1

                if qtd > 0: 
                    dv['quantidades'][p_name] = qtd
                    _sel_m.append(p_name)

            sem = int(md.get('m_semanas', 0))
            for s_name in servicos_db.keys():
                s_low = s_name.lower()
                qtd = 0
                if "implanta" in s_low and "treinamento" in s_low: qtd = sem * 44
                elif md.get('m_escopo') and "escopo" in s_low: qtd = 8
                elif md.get('m_migracao') and s_name == "Migracao de Dados Padrao": qtd = 8
                if qtd > 0: 
                    dv['quantidades'][s_name] = qtd
                    _sel_i.append(s_name)

            if sem > 0:
                for d_name in despesas_db.keys():
                    d_low = d_name.lower()
                    qtd = 0
                    if "alimenta" in d_low: qtd = sem * 10
                    elif "hospedagem" in d_low: qtd = sem * 4
                    if qtd > 0: 
                        dv['quantidades'][d_name] = qtd
                        _sel_d.append(d_name)
                        
            dv['sel_m'] = _sel_m
            dv['sel_i'] = _sel_i
            dv['sel_d'] = _sel_d
            processar_regras_colaterais()
            st.session_state.has_unsaved_changes = True
            st.session_state.form_rc += 1 # Sync forçado visual

        col_hdr1, col_hdr2, col_hdr3 = st.columns([2, 1, 1])
        with col_hdr1:
            st.markdown("""<h1 class="hero-title">PROPOSTA COMERCIAL</h1>""", unsafe_allow_html=True)
            if st.session_state.proposta_carregada_id:
                st.markdown(f"<span style='color:#ff6600; font-weight:bold;'>Editando a Proposta do CRM: #{st.session_state.proposta_carregada_id}</span>", unsafe_allow_html=True)
        
        with col_hdr2:
            st.write("")
            if not st.session_state.modo_apresentacao:
                if st.button("Salvar no CRM", use_container_width=True, type="primary"):
                    if not st.session_state.perma_nome_cliente:
                        st.error("Preencha o Nome do Cliente no cabeçalho.")
                    else:
                        try:
                            t_setup_b, t_mensal_b = 0.0, 0.0
                            for n in dv['sel_i']: 
                                q_i = int(dv['quantidades'].get(n, 0))
                                if q_i > 0 and n in servicos_db:
                                    d_serv = servicos_db.get(n, {})
                                    val_u = d_serv.get('valor_projeto', 0.0)
                                    if val_u <= 0: val_u = d_serv.get('valor', 0.0)
                                    t_setup_b += q_i * val_u
                                
                            for n in dv['sel_m']:
                                q_m = int(dv['quantidades'].get(n, 0))
                                if q_m > 0 and n in sistemas_db:
                                    desc_bd = st.session_state.g_desc_mensalidade if st.session_state.modo_desconto == "Total" else dv['descontos_itens'].get(n, 0.0)
                                    t_setup_b += sistemas_db[n].get('adesao_vinculada', 0.0)
                                    t_mensal_b += (q_m * sistemas_db[n].get('valor', 0.0)) * (1 - (desc_bd/100))
                                    if name_to_id.get(n) not in vinculos_db and n not in ["VR Mobile (Smartphone/Android)", "VR PDV Touchscreen", "VR PDV Self Checkout"]:
                                        h_sist = int(dv['setup_sistemas'].get(n, 0))
                                        if h_sist > 0: t_setup_b += (h_sist * (sistemas_db[n].get('valor_projeto', 0.0) or v_h_base_global))
                            
                            payload_json = empacotar_simulacao()
                            engine = get_db_engine()
                            with engine.begin() as conn:
                                if st.session_state.proposta_carregada_id:
                                    conn.execute(text("UPDATE propostas SET nome_cliente = :n, cnpj_cliente = :c, valor_setup = :vs, valor_mensal = :vm, dados_simulacao = :ds, data_atualizacao = CURRENT_TIMESTAMP WHERE id = :id"), {"n": st.session_state.perma_nome_cliente, "c": st.session_state.perma_cnpj_cliente, "vs": t_setup_b, "vm": t_mensal_b, "ds": payload_json, "id": st.session_state.proposta_carregada_id})
                                    st.success(f"Proposta #{st.session_state.proposta_carregada_id} atualizada com sucesso no CRM!")
                                else:
                                    res = conn.execute(text("INSERT INTO propostas (vendedor_email, nome_cliente, cnpj_cliente, valor_setup, valor_mensal, dados_simulacao) VALUES (:e, :n, :c, :vs, :vm, :ds) RETURNING id"), {"e": st.session_state.user_email, "n": st.session_state.perma_nome_cliente, "c": st.session_state.perma_cnpj_cliente, "vs": t_setup_b, "vm": t_mensal_b, "ds": payload_json})
                                    st.session_state.proposta_carregada_id = res.scalar()
                                    st.success(f"Nova proposta guardada! (ID: #{st.session_state.proposta_carregada_id})")
                            st.session_state.has_unsaved_changes = False
                        except Exception: st.error("Erro interno. Tente de novo.")
                        
        with col_hdr3:
            st.write("")
            if not st.session_state.modo_apresentacao and st.session_state.proposta_carregada_id:
                if st.button("Duplicar Nova", use_container_width=True):
                    if not st.session_state.perma_nome_cliente:
                        st.error("Preencha o Nome do Cliente.")
                    else:
                        try:
                            t_setup_b, t_mensal_b = 0.0, 0.0
                            for n in dv['sel_i']: 
                                q_i = int(dv['quantidades'].get(n, 0))
                                if q_i > 0 and n in servicos_db:
                                    d_serv = servicos_db.get(n, {})
                                    val_u = d_serv.get('valor_projeto', 0.0)
                                    if val_u <= 0: val_u = d_serv.get('valor', 0.0)
                                    t_setup_b += q_i * val_u
                            for n in dv['sel_m']:
                                q_m = int(dv['quantidades'].get(n, 0))
                                if q_m > 0 and n in sistemas_db:
                                    desc_bd = st.session_state.g_desc_mensalidade if st.session_state.modo_desconto == "Total" else dv['descontos_itens'].get(n, 0.0)
                                    t_setup_b += sistemas_db[n].get('adesao_vinculada', 0.0); t_mensal_b += (q_m * sistemas_db[n].get('valor', 0.0)) * (1 - (desc_bd/100))
                                    if name_to_id.get(n) not in vinculos_db and n not in ["VR Mobile (Smartphone/Android)", "VR PDV Touchscreen", "VR PDV Self Checkout"]:
                                        h_sist = int(dv['setup_sistemas'].get(n, 0))
                                        if h_sist > 0: t_setup_b += (h_sist * (sistemas_db[n].get('valor_projeto', 0.0) or v_h_base_global))
                            
                            payload_json = empacotar_simulacao()
                            engine = get_db_engine()
                            with engine.begin() as conn:
                                res = conn.execute(text("INSERT INTO propostas (vendedor_email, nome_cliente, cnpj_cliente, valor_setup, valor_mensal, dados_simulacao) VALUES (:e, :n, :c, :vs, :vm, :ds) RETURNING id"), {"e": st.session_state.user_email, "n": st.session_state.perma_nome_cliente, "c": st.session_state.perma_cnpj_cliente, "vs": t_setup_b, "vm": t_mensal_b, "ds": payload_json})
                                st.session_state.proposta_carregada_id = res.scalar()
                            st.session_state.has_unsaved_changes = False
                            st.success(f"Cópia criada! (ID: #{st.session_state.proposta_carregada_id})")
                        except Exception: st.error("Erro ao duplicar.")

        if st.session_state.modo_apresentacao:
            st.markdown(f"""
            <div style="background-color:#ffffff; border-left: 10px solid #262730; padding: 20px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                <span style="color:#ff6600; font-size:0.9rem; text-transform:uppercase; font-weight:bold;">Apresentação para o cliente:</span>
                <h2 style="margin:5px 0; color:#262730;">{html.escape(st.session_state.perma_nome_cliente or "Cliente Não Informado")}</h2>
                <span style="color:#777; font-size:1.1rem; font-weight:bold;">CNPJ: {html.escape(st.session_state.perma_cnpj_cliente) if st.session_state.perma_cnpj_cliente else "Não informado"}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""<div class="cliente-container"><h3 style="margin:0; color:#262730;">Dados do Cliente</h3></div>""", unsafe_allow_html=True)
            col_cli1, col_cli2 = st.columns([2, 1])
            with col_cli1: st.text_input("Razão Social / Nome Fantasia", value=st.session_state.perma_nome_cliente, key="widget_nome", on_change=atualiza_nome_cliente, placeholder="Ex: Supermercados Dois Irmãos")
            with col_cli2: st.text_input("CNPJ", value=st.session_state.perma_cnpj_cliente, key="widget_cnpj", on_change=atualiza_cnpj_cliente, placeholder="Apenas números", max_chars=18)
            st.write("---")

        if mapeamento_ativo and not st.session_state.modo_apresentacao:
            st.markdown("""<div class="mapeamento-container"><h3 style="margin:0; color:#ff6600;">Mapeamento da Operacao</h3></div>""", unsafe_allow_html=True)
            
            n_combo = st.selectbox("Combo Rápido", ["Montar Manualmente", "Padrao Pequeno Porte"], index=0 if md.get('m_combo') == "Montar Manualmente" else 1, key=f"ui_m_combo_{rc}", on_change=sync_combo)

            c1, c2, c3 = st.columns(3)
            with c1:
                md['m_pdv_conv'] = st.number_input("PDV Convencional", value=int(md.get('m_pdv_conv',0)), step=1, key=f"ui_m_pdv_conv_{rc}")
                md['m_pdv_touch'] = st.number_input("PDV Touch", value=int(md.get('m_pdv_touch',0)), step=1, key=f"ui_m_pdv_touch_{rc}")
                md['m_pdv_self'] = st.number_input("PDV Selfcheckout", value=int(md.get('m_pdv_self',0)), step=1, key=f"ui_m_pdv_self_{rc}")
            with c2:
                op_tef = ["Nao utiliza", "SiTef Express", "VR TEF"]
                c_tef = md.get('m_tef', "Nao utiliza")
                md['m_tef'] = st.selectbox("TEF", op_tef, index=op_tef.index(c_tef) if c_tef in op_tef else 0, key=f"ui_m_tef_{rc}")
                md['m_semanas'] = st.number_input("Semanas", value=int(md.get('m_semanas',0)), step=1, key=f"ui_m_semanas_{rc}")
                md['m_migracao'] = st.checkbox("Migração?", value=md.get('m_migracao', False), key=f"ui_m_migracao_{rc}")
                md['m_escopo'] = st.checkbox("Escopo?", value=md.get('m_escopo', False), key=f"ui_m_escopo_{rc}")
            with c3:
                md['m_mobile'] = st.number_input("VR Mobile", value=int(md.get('m_mobile',0)), step=1, key=f"ui_m_mobile_{rc}")
                sc1, sc2, sc3 = st.columns(3)
                md['m_erp_pro'] = sc1.toggle("VR ERP PRO", value=md.get('m_erp_pro', False), key=f"ui_m_erp_pro_{rc}")
                md['m_xml'] = sc1.toggle("G. XML", value=md.get('m_xml', False), key=f"ui_m_xml_{rc}")
                md['m_connect'] = sc1.toggle("Connect", value=md.get('m_connect', False), key=f"ui_m_connect_{rc}")
                md['m_backup'] = sc2.toggle("VR Backup", value=md.get('m_backup', False), key=f"ui_m_backup_{rc}")
                md['m_cartaz'] = sc2.toggle("VR Cartaz", value=md.get('m_cartaz', False), key=f"ui_m_cartaz_{rc}")
                md['m_ecommerce'] = sc2.toggle("E-Commerce", value=md.get('m_ecommerce', False), key=f"ui_m_ecommerce_{rc}")
                md['m_controller'] = sc3.toggle("C. 360", value=md.get('m_controller', False), key=f"ui_m_controller_{rc}")
                md['m_masterfisco'] = sc3.toggle("MasterFisco", value=md.get('m_masterfisco', False), key=f"ui_m_masterfisco_{rc}")
                md['m_app'] = sc3.toggle("M-Commerce", value=md.get('m_app', False), key=f"ui_m_app_{rc}")
                b1, b2 = st.columns(2)
                if b1.button("Aplicar Inteligência", use_container_width=True): aplicar_mapeamento(); st.rerun()
                if b2.button("Limpar Tudo", use_container_width=True): limpar_tudo(); st.rerun()
            st.write("---")

        if not st.session_state.modo_apresentacao:
            if perfil_venda == "Com Despesas":
                c1, c2, c3 = st.columns(3)
            else:
                c_cols = st.columns(2)
                c1, c2 = c_cols[0], c_cols[1]
                c3 = None
            
            with c1:
                st.markdown("""<div class="section-header"><span class="section-title">IMPLANTAÇÃO E SERVIÇOS</span></div>""", unsafe_allow_html=True)
                valid_i = [x for x in dv['sel_i'] if x in servicos_db]
                new_sel_i = st.multiselect("Serviços Manuais", list(servicos_db.keys()), default=valid_i, key=f"ui_sel_i_{rc}", on_change=mark_unsaved)
                dv['sel_i'] = new_sel_i
                
                for i in dv['sel_i']:
                    if i in servicos_db:
                        d_s = servicos_db[i]
                        v_u = d_s.get('valor_projeto', 0.0)
                        if v_u <= 0: v_u = d_s.get('valor', 0.0)
                        
                        c_qty = int(dv['quantidades'].get(i, 0))
                        n_qty = st.number_input(f"{i} (R$ {f_br(v_u)}/h)", min_value=0, step=1, value=c_qty, key=f"ui_qty_{i}_{rc}", on_change=mark_unsaved)
                        dv['quantidades'][i] = n_qty
                    
                has_sistemas_com_setup = any(
                    m in sistemas_db and
                    name_to_id.get(m) not in vinculos_db and 
                    m not in ["VR Mobile (Smartphone/Android)", "VR PDV Touchscreen", "VR PDV Self Checkout"] and 
                    int(sistemas_db[m].get('horas_padrao', 0)) > 0 and 
                    int(dv['quantidades'].get(m, 0)) > 0 
                    for m in dv['sel_m']
                )
                
                if has_sistemas_com_setup:
                    st.markdown("<div style='margin-top:15px; font-weight:bold; font-size:0.9rem; color:#ff6600; border-bottom:1px solid #eee; padding-bottom:5px;'>Setup Automático (Sistemas)</div>", unsafe_allow_html=True)
                    for m in dv['sel_m']:
                        if m in sistemas_db and int(dv['quantidades'].get(m, 0)) > 0: 
                            if name_to_id.get(m) not in vinculos_db and m not in ["VR Mobile (Smartphone/Android)", "VR PDV Touchscreen", "VR PDV Self Checkout"]:
                                d_sist = sistemas_db[m]
                                h_padrao = int(d_sist.get('horas_padrao', 0))
                                if h_padrao > 0:
                                    v_rate = d_sist.get('valor_projeto', 0.0) or v_h_base_global
                                    nome_exib = "Projeto ERP PRO" if m == "VR ERP PRO" else f"Implantação {m}"
                                    
                                    c_set = int(dv['setup_sistemas'].get(m, h_padrao))
                                    n_set = st.number_input(f"{nome_exib} (R$ {f_br(v_rate)}/h)", min_value=0, step=1, value=c_set, key=f"ui_setup_{m}_{rc}", on_change=mark_unsaved)
                                    dv['setup_sistemas'][m] = n_set

            with c2:
                st.markdown("""<div class="section-header"><span class="section-title">MENSALIDADES SISTEMAS</span></div>""", unsafe_allow_html=True)
                valid_m = [x for x in dv['sel_m'] if x in sistemas_db]
                new_sel_m = st.multiselect("Sistemas", list(sistemas_db.keys()), default=valid_m, key=f"ui_sel_m_{rc}", on_change=mark_unsaved)
                dv['sel_m'] = new_sel_m
                
                for i in dv['sel_m']:
                    if i in sistemas_db:
                        v_u = sistemas_db[i].get('valor', 0.0)
                        c_qty = int(dv['quantidades'].get(i, 0))
                        n_qty = st.number_input(f"**{i}** (R$ {f_br(v_u)}/un)", min_value=0, step=1, value=c_qty, key=f"ui_qty_{i}_{rc}", on_change=mark_unsaved)
                        dv['quantidades'][i] = n_qty
                        
                        if st.session_state.modo_desconto == "Item":
                            c_neg = dv['negociar'].get(i, False)
                            n_neg = st.checkbox(f"⚙️ Negociar Desconto", value=c_neg, key=f"ui_neg_{i}_{rc}")
                            dv['negociar'][i] = n_neg
                            if n_neg:
                                c_desc = float(dv['descontos_itens'].get(i, 0.0))
                                n_desc = st.number_input(f"↳ Desconto %", 0.0, 100.0, value=c_desc, key=f"ui_desc_{i}_{rc}", on_change=mark_unsaved)
                                dv['descontos_itens'][i] = n_desc
                            else:
                                dv['descontos_itens'][i] = 0.0
            
            if c3:
                with c3:
                    st.markdown("""<div class="section-header"><span class="section-title">DESPESAS DO PROJETO</span></div>""", unsafe_allow_html=True)
                    valid_d = [x for x in dv['sel_d'] if x in despesas_db]
                    new_sel_d = st.multiselect("Despesas", list(despesas_db.keys()), default=valid_d, key=f"ui_sel_d_{rc}", on_change=mark_unsaved)
                    dv['sel_d'] = new_sel_d
                    
                    if dv['sel_d']:
                        cd1, cd2 = st.columns([1, 1.2])
                        cd1.markdown("<span style='font-size:0.85rem; font-weight:bold; color:#777;'>Qtd</span>", unsafe_allow_html=True)
                        cd2.markdown("<span style='font-size:0.85rem; font-weight:bold; color:#777;'>R$ Unit.</span>", unsafe_allow_html=True)

                    for i in dv['sel_d']:
                        if i in despesas_db:
                            v_u_padrao = despesas_db[i].get('valor', 0.0)
                            c_qty = int(dv['quantidades'].get(i, 0))
                            c_unit = float(dv['despesas_valores'].get(i, v_u_padrao))
                            
                            st.markdown(f"<div style='font-size:0.85rem; font-weight:bold; color:#444; margin-bottom:2px;'>{i}</div>", unsafe_allow_html=True)
                            cd1, cd2 = st.columns([1, 1.2])
                            n_qty = cd1.number_input(f"Qtd_{i}", min_value=0, step=1, value=c_qty, key=f"ui_qty_{i}_{rc}", on_change=mark_unsaved, label_visibility="collapsed")
                            n_unit = cd2.number_input(f"R$_{i}", min_value=0.0, step=10.0, value=c_unit, key=f"ui_unit_{i}_{rc}", on_change=mark_unsaved, label_visibility="collapsed")
                            dv['quantidades'][i] = n_qty
                            dv['despesas_valores'][i] = n_unit
                            st.markdown("<div style='margin-bottom:10px;'></div>", unsafe_allow_html=True)

        st.markdown("""<h2 style='text-align:center; font-weight:800; margin-top:30px;'>RESUMO DO INVESTIMENTO</h2>""", unsafe_allow_html=True)
        res_cols = st.columns(3) if perfil_venda == "Com Despesas" else st.columns([1, 2, 2, 1])[1:3]
        
        def get_prioridade_mensal(item_name):
            if item_name == "VR ERP PRO": return 1
            if item_name == "VR PDV Convencional": return 2
            if "VR Sitef Express" in item_name: return 3
            if item_name == "VR Gerenciador Xml": return 4
            if "VR Mobile" in item_name: return 5
            return 99

        def get_prioridade_setup(obj_item):
            nome = obj_item['nome_exibicao']
            if "Projeto ERP PRO" in nome: return 1
            if "Migracao" in nome: return 2
            if "Escopo" in nome: return 3
            return 99

        t_setup = 0.0
        lista_setup_pre_ordenacao = []
        html_setup_digital = ""

        for n in dv['sel_i']:
            q = int(dv['quantidades'].get(n, 0))
            if q > 0 and n in servicos_db:
                d_serv = servicos_db[n]
                v_u = d_serv.get('valor_projeto', 0.0)
                if v_u <= 0: v_u = d_serv.get('valor', 0.0)
                
                t_setup += (q * v_u)
                html_linha = f"<li><span class='item-name'>{n}</span><span class='item-detalhe'>{q}h x R$ {f_br(v_u)} | Total: R$ {f_br(q*v_u)}</span></li>"
                html_digital = f"<li><strong>{n}</strong><span class='detail'>{q}h x R$ {f_br(v_u)} | Total: R$ {f_br(q*v_u)}</span></li>"
                lista_setup_pre_ordenacao.append({'nome_exibicao': n, 'html': html_linha, 'html_dig': html_digital})
        
        itens_isentos_setup = ["VR Mobile (Smartphone/Android)", "VR PDV Touchscreen", "VR PDV Self Checkout"]

        for n in dv['sel_m']:
            q_m = int(dv['quantidades'].get(n, 0))
            if q_m > 0 and n in sistemas_db:
                if name_to_id.get(n) not in vinculos_db:
                    if n in itens_isentos_setup: continue
                    d_s = sistemas_db[n]
                    h = int(dv['setup_sistemas'].get(n, 0))
                    ads = d_s.get('adesao_vinculada', 0.0)
                    if h > 0:
                        v_rate = (d_s.get('valor_projeto', 0.0) or v_h_base_global)
                        t_setup += (h * v_rate)
                        nome_exibicao = "Projeto ERP PRO" if n == "VR ERP PRO" else f"Implantacao {n}"
                        html_linha = f"<li><span class='item-name'>{nome_exibicao}</span><span class='item-detalhe'>{h}h x R$ {f_br(v_rate)} | Total: R$ {f_br(h*v_rate)}</span></li>"
                        html_digital = f"<li><strong>{nome_exibicao}</strong><span class='detail'>{h}h x R$ {f_br(v_rate)} | Total: R$ {f_br(h*v_rate)}</span></li>"
                        lista_setup_pre_ordenacao.append({'nome_exibicao': nome_exibicao, 'html': html_linha, 'html_dig': html_digital})
                    if ads > 0:
                        t_setup += ads
                        html_linha = f"<li><span class='item-name'>Taxa de Adesao {n}</span><span class='item-detalhe'>1 un x R$ {f_br(ads)} | Total: R$ {f_br(ads)}</span></li>"
                        html_digital = f"<li><strong>Taxa de Adesao {n}</strong><span class='detail'>1 un x R$ {f_br(ads)} | Total: R$ {f_br(ads)}</span></li>"
                        lista_setup_pre_ordenacao.append({'nome_exibicao': f"Taxa de Adesao {n}", 'html': html_linha, 'html_dig': html_digital})

        lista_setup_pre_ordenacao.sort(key=get_prioridade_setup)
        h_setup = "".join(item['html'] for item in lista_setup_pre_ordenacao)
        html_setup_digital = "".join(item['html_dig'] for item in lista_setup_pre_ordenacao)

        with res_cols[0]:
            parcelas_safe = st.session_state.g_parcelas_setup if st.session_state.g_parcelas_setup > 0 else 1
            st.markdown(f"""<div class="resumo-card"><span class="resumo-label" style="color:#ff6600; font-weight:bold;">Investimento Implantação (Setup)</span><div class="resumo-valor">R$ {f_br(t_setup)}</div><div style="font-weight:bold;">{st.session_state.g_parcelas_setup}x de R$ {f_br(t_setup/parcelas_safe)}</div><div class="resumo-subtitulo" style="margin-top:15px;">DETALHAMENTO SETUP</div><ul class="lista-itens">{h_setup if h_setup else "<li>Nenhum item</li>"}</ul></div>""", unsafe_allow_html=True)

        t_mensal, h_m = 0.0, ""
        html_mensal_digital = ""
        sistemas_ordenados = sorted(dv['sel_m'], key=get_prioridade_mensal)
        
        for n in sistemas_ordenados:
            q = int(dv['quantidades'].get(n, 0))
            if q > 0 and n in sistemas_db:
                v_u = sistemas_db[n].get('valor', 0.0)
                desc_aplicado = st.session_state.g_desc_mensalidade if st.session_state.modo_desconto == "Total" else dv['descontos_itens'].get(n, 0.0)
                v_liq_u = v_u * (1 - (desc_aplicado/100))
                t_mensal += (q * v_liq_u)
                
                str_orig = f"R$ {f_br(q * v_u)}"
                str_desc = f"R$ {f_br(q * v_liq_u)}"
                
                if desc_aplicado > 0:
                    h_m += f"<li><span class='item-name'>{n}</span><span class='item-detalhe'>{q} un x R$ {f_br(v_u)} | Total: <del style='color:#999; margin-right:5px;'>{str_orig}</del>{str_desc}</span></li>"
                    html_mensal_digital += f"<li><strong>{n}</strong><span class='detail'>{q} un x R$ {f_br(v_u)} | Total: <del>{str_orig}</del> {str_desc}</span></li>"
                else:
                    h_m += f"<li><span class='item-name'>{n}</span><span class='item-detalhe'>{q} un x R$ {f_br(v_u)} | Total: {str_orig}</span></li>"
                    html_mensal_digital += f"<li><strong>{n}</strong><span class='detail'>{q} un x R$ {f_br(v_u)} | Total: {str_orig}</span></li>"
                
                vincs = [id_to_name.get(v['id_filho']) for v in vinculos_db.get(name_to_id.get(n), []) if v['tipo'] == 'incluso']
                for inc in vincs: 
                    h_m += f"<li class='item-incluso'>└ {inc} (Incluso)</li>"
                    html_mensal_digital += f"<li class='item-incluso'>└ {inc} (Incluso)</li>"
                if n == "VR ERP PRO" and not vincs:
                    for inc in ["VR Promo", "VR Carteira Digital", "VR Analytics"]: 
                        h_m += f"<li class='item-incluso'>└ {inc} (Incluso)</li>"
                        html_mensal_digital += f"<li class='item-incluso'>└ {inc} (Incluso)</li>"

        with res_cols[1]:
            d_h = f"""<div style="color:#2e7d32; font-weight:bold;">Desconto: {st.session_state.g_desc_mensalidade}%</div>""" if (st.session_state.modo_desconto == "Total" and exibir_detalhe_desc and st.session_state.g_desc_mensalidade > 0) else """<div style="height:21px"></div>"""
            st.markdown(f"""<div class="resumo-card" style="border-top-color:#2e7d32;"><span class="resumo-label" style="color:#2e7d32; font-weight:bold;">Manutenção Mensal</span><div class="resumo-valor" style="color:#2e7d32;">R$ {f_br(t_mensal)}</div>{d_h}<div style="font-weight:bold;">Início: {st.session_state.g_faturamento}</div><div class="resumo-subtitulo" style="margin-top:15px;">SISTEMAS</div><ul class="lista-itens">{h_m if h_m else "<li>Nenhum</li>"}</ul></div>""", unsafe_allow_html=True)

        t_d, h_d = 0.0, ""
        html_desp_digital = ""
        if perfil_venda == "Com Despesas":
            for n in dv['sel_d']:
                q = int(dv['quantidades'].get(n, 0))
                if q > 0 and n in despesas_db:
                    v_u = float(dv['despesas_valores'].get(n, despesas_db[n].get('valor', 0.0)))
                    t_d += (q * v_u)
                    h_d += f"<li><span class='item-name'>{n}</span><span class='item-detalhe'>{q} un x R$ {f_br(v_u)} | Total: R$ {f_br(q*v_u)}</span></li>"
                    html_desp_digital += f"<li><strong>{n}</strong><span class='detail'>{q} un x R$ {f_br(v_u)} | Total: R$ {f_br(q*v_u)}</span></li>"
            with res_cols[2]:
                st.markdown(f"""<div class="resumo-card" style="border-top-color:#1976d2;"><span class="resumo-label" style="color:#1976d2; font-weight:bold;">Despesas do Projeto</span><div class="resumo-valor" style="color:#1976d2;">R$ {f_br(t_d)}</div><div style="color:#d32f2f; font-weight:bold; font-size:0.8rem;">{st.session_state.g_regra_desp}</div><div class="resumo-subtitulo" style="margin-top:15px;">DETALHAMENTO</div><ul class="lista-itens">{h_d if h_d else "<li>Sem despesas</li>"}</ul></div>""", unsafe_allow_html=True)

        if exibir_media_loja:
            qtd_lojas = int(dv['quantidades'].get("VR ERP PRO", 0))
            if qtd_lojas > 0:
                st.markdown(f"""<h3 style='text-align:center; font-weight:800; margin-top:40px; color:#262730;'>DILUIÇÃO DO INVESTIMENTO ({qtd_lojas} LOJAS)</h3>""", unsafe_allow_html=True)
                m_cols = st.columns(3) if perfil_venda == "Com Despesas" else st.columns([1, 2, 2, 1])[1:3]
                with m_cols[0]: st.markdown(f"""<div style="background-color:#ffffff; border-left: 6px solid #ff6600; padding:15px; border-radius:5px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);"><span style="font-size:0.85rem; font-weight:bold; color:#777;">SETUP POR LOJA</span><br><span style="font-size:1.6rem; font-weight:900; color:#333;">R$ {f_br(t_setup / qtd_lojas)}</span></div>""", unsafe_allow_html=True)
                with m_cols[1]: st.markdown(f"""<div style="background-color:#ffffff; border-left: 6px solid #2e7d32; padding:15px; border-radius:5px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);"><span style="font-size:0.85rem; font-weight:bold; color:#777;">MENSALIDADE POR LOJA</span><br><span style="font-size:1.6rem; font-weight:900; color:#333;">R$ {f_br(t_mensal / qtd_lojas)}</span></div>""", unsafe_allow_html=True)
                if perfil_venda == "Com Despesas":
                    with m_cols[2]: st.markdown(f"""<div style="background-color:#ffffff; border-left: 6px solid #1976d2; padding:15px; border-radius:5px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);"><span style="font-size:0.85rem; font-weight:bold; color:#777;">DESPESAS POR LOJA</span><br><span style="font-size:1.6rem; font-weight:900; color:#333;">R$ {f_br(t_d / qtd_lojas)}</span></div>""", unsafe_allow_html=True)

        if not st.session_state.modo_apresentacao:
            st.write("---")
            if not st.session_state.perma_nome_cliente:
                st.info("Preencha o nome do cliente no cabeçalho da página para liberar a emissão de proposta digital.")
            else:
                col_dig1, col_dig2, col_dig3 = st.columns([1, 2, 1])
                with col_dig2:
                    if st.button("Gerar Proposta Digital (PDF)", use_container_width=True):
                        dados_pdf = {
                            'nome_cliente': html.escape(st.session_state.perma_nome_cliente),
                            'cnpj': html.escape(st.session_state.perma_cnpj_cliente),
                            'html_setup': html_setup_digital,
                            'valor_setup': f_br(t_setup),
                            'parcelas': str(st.session_state.g_parcelas_setup),
                            'html_mensal': html_mensal_digital,
                            'valor_mensal': f_br(t_mensal),
                            'faturamento': st.session_state.g_faturamento,
                            'html_despesa': html_desp_digital if html_desp_digital else "<li>Sem despesas</li>",
                            'valor_despesa': f_br(t_d) if 't_d' in locals() else "0,00",
                            'regra_desp': st.session_state.g_regra_desp
                        }
                        st.session_state.html_proposta = renderizar_proposta_digital(dados_pdf)
                        st.session_state.show_digital_proposal = True
                        st.rerun()
                        
        if st.session_state.get('show_digital_proposal', False) and not st.session_state.modo_apresentacao:
            st.markdown("---")
            st.markdown("<h2 style='text-align:center; color:#ff6600;'>Visualização da Proposta Digital</h2>", unsafe_allow_html=True)
            st.info("Clique no botão laranja 'Salvar como PDF' dentro do quadro abaixo.")
            components.html(st.session_state.html_proposta, height=1200, scrolling=True)
            col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
            if col_f2.button("Fechar Visualização", use_container_width=True): 
                st.session_state.show_digital_proposal = False
                st.rerun()

    # ==========================================
    # TELA DIAGNÓSTICO
    # ==========================================
    elif tela == "Diagnóstico":
        st.markdown("<h1 class='hero-title'>DIAGNÓSTICO DE OPERAÇÃO</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#777; font-size:1.2rem; margin-bottom:30px;'>Sales Intelligence | Identificação de Gaps e Oportunidades</p>", unsafe_allow_html=True)

        with st.expander("⚙️ Parâmetros do Diagnóstico (Benchmarks da VR)"):
            st.markdown("Ajuste as réguas ideais para refletir a realidade do formato da loja.")
            cp1, cp2, cp3, cp4 = st.columns(4)
            st.session_state.param_piso_pdv = cp1.number_input("Piso Faturamento / PDV (R$)", value=float(st.session_state.get('param_piso_pdv', 150000.0)), step=10000.0)
            st.session_state.param_piso_rh = cp2.number_input("Piso Faturamento / Func (R$)", value=float(st.session_state.get('param_piso_rh', 25000.0)), step=1000.0)
            st.session_state.param_perda = cp3.number_input("Média de Perda Setor (%)", value=float(st.session_state.get('param_perda', 4.0)), step=0.5)
            st.session_state.param_risco_trib = cp4.number_input("Risco Tributário Base (%)", value=float(st.session_state.get('param_risco_trib', 18.0)), step=1.0)

        st.markdown("""<div class="cliente-container"><h3 style="margin:0; color:#262730;">Dados Estruturais do Supermercado</h3></div>""", unsafe_allow_html=True)
        c_in1, c_in2, c_in3, c_in4, c_in5 = st.columns(5)
        
        with c_in2: 
            fat_str = st.text_input("Faturamento Mensal", value=st.session_state.get('diag_fat_str', ""), placeholder="Ex: 1500000")
            fat_val = parse_currency(fat_str)
            st.session_state.diag_fat_str = fat_str
            st.markdown(f"<div style='font-size:1.1rem; font-weight:900; color:#2e7d32; margin-top:-15px; margin-bottom:15px;'>R$ {f_br(fat_val)}</div>", unsafe_allow_html=True)

        with c_in1: st.session_state.diag_pdv = st.number_input("Qtd Checkouts (PDVs)", min_value=0, step=1, value=st.session_state.get('diag_pdv', 0))
        with c_in3: st.session_state.diag_area = st.number_input("Área de Venda (m²)", min_value=0, step=50, value=st.session_state.get('diag_area', 0))
        with c_in4: st.session_state.diag_func = st.number_input("Qtd de Funcionários", min_value=0, step=1, value=st.session_state.get('diag_func', 0))
        with c_in5: st.session_state.diag_sku = st.number_input("Mix de Produtos (SKU)", min_value=0, step=1000, value=st.session_state.get('diag_sku', 0))

        st.write("---")
        pdvs, fat, area, func, sku = st.session_state.diag_pdv, fat_val, st.session_state.diag_area, st.session_state.diag_func, st.session_state.diag_sku
        piso_pdv, piso_rh, taxa_perda, taxa_risco = st.session_state.param_piso_pdv, st.session_state.param_piso_rh, st.session_state.param_perda / 100.0, st.session_state.param_risco_trib / 100.0

        def render_diag_card(title, value_text, subtitle, status_color, insight, recommendation=""):
            html_b = f"""<div style="background:#fff; border-top: 5px solid {status_color}; padding:25px; border-radius:10px; box-shadow:0 10px 25px rgba(0,0,0,0.08); height:100%; display:flex; flex-direction:column;"><div style="font-size:0.85rem; font-weight:bold; color:#777; text-transform:uppercase;">{title}</div><div style="font-size:1.9rem; font-weight:900; color:#262730; margin:10px 0;">{value_text}</div><div style="font-size:1rem; font-weight:bold; color:{status_color}; margin-bottom:15px;">{subtitle}</div><div style="font-size:0.95rem; color:#444; line-height:1.5; margin-bottom:20px; flex-grow:1;">{insight}</div>"""
            if recommendation: html_b += f"""<div style="background:#f8f9fa; border-left:4px solid {status_color}; padding:15px; font-size:0.9rem; font-style:italic; color:#262730; border-radius:4px;">💡 <b>Solução VR:</b> {recommendation}</div>"""
            return html_b + "</div>"

        if pdvs == 0 and fat == 0 and area == 0 and func == 0 and sku == 0:
            st.info("Preencha ao menos um dos campos estruturais acima para iniciar o mapeamento.")
        else:
            st.markdown("<h3 style='color:#262730; margin-bottom:20px;'>A Trinca de Ouro (Métricas de Saúde)</h3>", unsafe_allow_html=True)
            c_p1, c_p2, c_p3 = st.columns(3)
            with c_p1:
                if pdvs == 0: st.markdown(render_diag_card("Eficiência de Caixa", "Aguardando", "Dados Insuficientes", "#ccc", "Informe PDVs e/ou Faturamento."), unsafe_allow_html=True)
                elif pdvs > 0 and fat == 0: st.markdown(render_diag_card("Eficiência de Caixa", "Projeção", f"Potencial: R$ {f_br(pdvs*piso_pdv)}/mês", "#3b82f6", "Informe o faturamento atual."), unsafe_allow_html=True)
                else:
                    if (fat/pdvs) < piso_pdv: st.markdown(render_diag_card("Eficiência de Caixa", f"R$ {f_br(fat/pdvs)}", f"Abaixo do Ideal", "#ef4444", "Sua loja apresenta alta ociosidade de caixas.", "Implantação do <b>VR Controller 360</b>."), unsafe_allow_html=True)
                    else: st.markdown(render_diag_card("Eficiência de Caixa", f"R$ {f_br(fat/pdvs)}", "Operação Saudável", "#22c55e", "Seus checkouts possuem excelente giro.", "Mantenha o acompanhamento."), unsafe_allow_html=True)

            with c_p2:
                if func == 0: st.markdown(render_diag_card("Produtividade de RH", "Aguardando", "Dados Insuficientes", "#ccc", "Informe o número de Funcionários."), unsafe_allow_html=True)
                elif func > 0 and fat == 0: st.markdown(render_diag_card("Produtividade de RH", "Projeção", "Potencial de Equipe", "#3b82f6", f"Pela régua saudável, sua equipe atual deveria estar entregando pelo menos R$ {f_br(func*piso_rh)}."), unsafe_allow_html=True)
                else:
                    if (fat/func) < piso_rh: st.markdown(render_diag_card("Produtividade de RH", f"R$ {f_br(fat/func)}", f"Abaixo do Ideal", "#ef4444", "A folha de pagamento está pesada.", "Adoção de terminais de <b>VR PDV Self Checkout</b>."), unsafe_allow_html=True)
                    else: st.markdown(render_diag_card("Produtividade de RH", f"R$ {f_br(fat/func)}", "Eficiência Comprovada", "#22c55e", "A receita sustenta a folha perfeitamente.", "Utilize o Controller para reter talentos."), unsafe_allow_html=True)

            with c_p3:
                if sku == 0 and fat == 0: st.markdown(render_diag_card("Margem e Fisco", "Aguardando", "Dados Insuficientes", "#ccc", "Informe SKU e Faturamento."), unsafe_allow_html=True)
                else:
                    if fat > 0 and sku > 0: st.markdown(render_diag_card("Margem e Fisco", f"R$ {f_br(fat*taxa_perda)}", f"{int(sku*taxa_risco)} Itens Vulneráveis", "#ef4444", "Alta exposição a tributação dupla.", "<b>VR Masterfisco</b> para higienização."), unsafe_allow_html=True)
                    elif sku > 0: st.markdown(render_diag_card("Margem e Fisco", f"{int(sku*taxa_risco)} Itens", "Base Desatualizada", "#f59e0b", "Risco de impostos pagos a mais.", "<b>VR Masterfisco</b> para higienização."), unsafe_allow_html=True)
                    else: st.markdown(render_diag_card("Margem e Fisco", f"R$ {f_br(fat*taxa_perda)}", "Risco de Perda Mensal", "#ef4444", "Média de sangria do mercado.", "<b>VR Masterfisco</b> para higienização."), unsafe_allow_html=True)

    # ==========================================
    # TELA PAINEL ADMIN (SEM TERMINAL SQL)
    # ==========================================
    elif tela == "Painel Admin":
        st.markdown("""<h1 class="hero-title">BACKOFFICE</h1>""", unsafe_allow_html=True)
        if st.session_state.user_role != 'admin':
            st.error("Acesso Negado.")
        else:
            t_vinc, t_unid, t_user, t_ext, t_cat = st.tabs(["Vínculos Relacionais", "Unidades", "Usuários", "Lançar Vendas Externas", "Catálogo"])
            
            with t_unid:
                st.markdown("<div class='section-header'><span class='section-title'>Cadastro de Escritórios e Unidades</span></div>", unsafe_allow_html=True)
                with st.form("form_unidades"):
                    c1, c2, c3 = st.columns([2, 1, 1])
                    n_fantasia = c1.text_input("Nome Fantasia (Ex: VR Recife)")
                    v_cnpj = c2.text_input("CNPJ")
                    v_cidade = c3.text_input("Cidade")
                    c4, c5 = st.columns([3, 1])
                    v_end = c4.text_input("Endereço Completo")
                    m_reg = c5.number_input("Meta Global da Região (R$)", 0.0, step=1000.0)
                    if st.form_submit_button("Salvar Nova Unidade"):
                        try:
                            engine = get_db_engine()
                            with engine.begin() as conn: conn.execute(text("INSERT INTO unidades (nome_fantasia, cnpj, cidade, logradouro, meta_regiao) VALUES (:n, :c, :ci, :e, :m)"), {"n": html.escape(n_fantasia), "c": html.escape(v_cnpj), "ci": html.escape(v_cidade), "e": html.escape(v_end), "m": m_reg})
                            st.success("Unidade cadastrada!")
                        except Exception: st.error("Erro interno ao gravar dados.")
                try:
                    engine = get_db_engine()
                    st.dataframe(pd.read_sql("SELECT id, nome_fantasia, cidade, meta_regiao, ativo FROM unidades", engine), use_container_width=True)
                except Exception: pass
                
            with t_user:
                st.markdown("<div class='section-header'><span class='section-title'>Gestão da Equipe Comercial</span></div>", unsafe_allow_html=True)
                try:
                    engine = get_db_engine()
                    df_unid_list = pd.read_sql("SELECT id, nome_fantasia FROM unidades WHERE ativo = TRUE", engine)
                    if df_unid_list.empty: st.warning("Cadastre uma Unidade antes de criar usuários.")
                    else:
                        unid_dict = dict(zip(df_unid_list['nome_fantasia'], df_unid_list['id']))
                        with st.form("form_usuarios"):
                            c1, c2 = st.columns(2)
                            u_nome, u_email = c1.text_input("Nome Completo"), c2.text_input("E-mail Corporativo")
                            c3, c4, c5, c6 = st.columns(4)
                            u_unid = c3.selectbox("Unidade", list(unid_dict.keys()))
                            u_role = c4.selectbox("Nível do Sistema", ["vendedor", "admin", "financeiro", "projetos", "consultor"])
                            u_cargo = c5.selectbox("Cargo (Gamificação)", ["Executivo de Vendas", "CS"])
                            u_senioridade = c6.selectbox("Senioridade", ["Júnior", "Pleno", "Sênior"])
                            if st.form_submit_button("Criar Usuário"):
                                with engine.begin() as conn: conn.execute(text("INSERT INTO usuarios (nome, email, nivel_acesso, id_unidade, senha, primeiro_acesso, cargo, perfil_senioridade) VALUES (:n, :e, :r, :id_u, :s, TRUE, :cg, :ps)"), {"n": html.escape(u_nome), "e": html.escape(u_email), "r": u_role, "id_u": unid_dict[u_unid], "s": get_senha_hash("123456"), "cg": u_cargo, "ps": u_senioridade})
                                st.success(f"Usuário {u_nome} criado! Senha provisória: 123456")
                        st.dataframe(pd.read_sql("SELECT u.id, u.nome, u.email, u.cargo, u.perfil_senioridade as senioridade, un.nome_fantasia as unidade FROM usuarios u LEFT JOIN unidades un ON u.id_unidade = un.id", engine), use_container_width=True)
                except Exception: st.error("Erro interno de comunicação.")
                
            with t_ext:
                st.markdown("<div class='section-header'><span class='section-title'>Livro-Razão (Lançamento de Vendas Externas)</span></div>", unsafe_allow_html=True)
                try:
                    engine = get_db_engine()
                    usuarios_list = pd.read_sql("SELECT email, nome FROM usuarios WHERE ativo = TRUE", engine)
                    if not usuarios_list.empty:
                        usr_dict = dict(zip(usuarios_list['nome'], usuarios_list['email']))
                        with st.form("form_vendas_externas"):
                            st.info("Lance as vendas realizadas fora do sistema para corrigir a barra de progresso do vendedor na Tela Inicial.")
                            cx1, cx2 = st.columns(2)
                            usr_sel = cx1.selectbox("Selecione o Vendedor", list(usr_dict.keys()))
                            dt_ref = cx2.date_input("Mês de Referência da Venda")
                            
                            cy1, cy2 = st.columns(2)
                            v_proj_ext = cy1.number_input("Total Vendido em Projeto (R$)", min_value=0.0, step=100.0)
                            v_rec_ext = cy2.number_input("Total Vendido em Recorrente (R$)", min_value=0.0, step=100.0)
                            
                            if st.form_submit_button("Injetar Saldo na Gamificação", type="primary"):
                                data_formatada = datetime.date(dt_ref.year, dt_ref.month, 1)
                                with engine.begin() as conn:
                                    conn.execute(text("INSERT INTO vendas_externas (vendedor_email, mes_referencia, valor_projeto, valor_recorrente) VALUES (:e, :m, :p, :r)"), {"e": usr_dict[usr_sel], "m": data_formatada, "p": v_proj_ext, "r": v_rec_ext})
                                st.success(f"Saldo de R$ {f_br(v_proj_ext + v_rec_ext)} lançado com sucesso para {usr_sel}!")
                        
                        st.markdown("<br><b>Histórico de Lançamentos Manuais:</b>", unsafe_allow_html=True)
                        st.dataframe(pd.read_sql("SELECT * FROM vendas_externas ORDER BY data_lancamento DESC LIMIT 50", engine), use_container_width=True)
                    else:
                        st.warning("Não há utilizadores cadastrados.")
                except Exception:
                    st.error("Ocorreu um erro ao carregar informações de histórico.")
                
            with t_vinc:
                with st.form("form_v"):
                    c1, c2, c3, c4 = st.columns([2,2,1,1])
                    pai, fil = c1.selectbox("Pai (SISTEMA):", sorted(list(sistemas_db.keys()))), c2.selectbox("Filho (ITEM):", sorted(list(full_db.keys())))
                    tip, qtd = c3.selectbox("Tipo:", ["projeto", "adesao", "incluso"]), c4.number_input("Qtd:", min_value=0.0, value=1.0)
                    if st.form_submit_button("Salvar Vínculo"):
                        try:
                            engine = get_db_engine()
                            with engine.begin() as conn: conn.execute(text("INSERT INTO product_vinculo (id_produto_pai, id_produto_filho, tipo_vinculo, quantidade_padrao) VALUES (:p, :f, :t, :q)"), {"p": name_to_id[pai], "f": name_to_id[fil], "t": tip, "q": qtd})
                            st.success("Vínculo Criado com Sucesso!"); st.cache_data.clear()
                        except Exception: st.error("Falha técnica ao gravar.")
                st.dataframe(df_vinc, use_container_width=True)
                
            with t_cat: st.dataframe(df_raw, use_container_width=True)

    elif tela == "Minhas Propostas":
        st.markdown("""<h1 class="hero-title">MEU HISTÓRICO</h1>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        c_filt, c_vis = st.columns([3, 1])
        exibir_excluidas = c_filt.checkbox("Exibir propostas com status 'Excluída'", value=False)
        visao = c_vis.radio("Tipo de Visão", ["Lista", "Kanban"], horizontal=True, label_visibility="collapsed")
        
        try:
            engine = get_db_engine()
            with engine.connect() as conn:
                cond_status = "" if exibir_excluidas else "AND status != 'Excluída'"
                
                if st.session_state.user_role == 'admin':
                    q = text(f"SELECT id, nome_cliente, cnpj_cliente, valor_setup, valor_mensal, status, TO_CHAR(data_atualizacao, 'DD/MM/YYYY HH24:MI') as data_fmt, dados_simulacao FROM propostas WHERE 1=1 {cond_status} ORDER BY data_atualizacao DESC")
                    result = conn.execute(q)
                else:
                    q = text(f"SELECT id, nome_cliente, cnpj_cliente, valor_setup, valor_mensal, status, TO_CHAR(data_atualizacao, 'DD/MM/YYYY HH24:MI') as data_fmt, dados_simulacao FROM propostas WHERE vendedor_email = :e {cond_status} ORDER BY data_atualizacao DESC")
                    result = conn.execute(q, {"e": st.session_state.user_email})

                rows = result.fetchall()
                if rows:
                    df_hist = pd.DataFrame([dict(r._mapping) for r in rows])
                else:
                    df_hist = pd.DataFrame()
            
            if df_hist.empty:
                st.info("O seu histórico de propostas está vazio.")
            else:
                if visao == "Lista":
                    selecionados = []
                    for idx, row in df_hist.iterrows():
                        cor_status = "#22c55e" if row['status'] == "Contrato Assinado" else "#ef4444" if row['status'] == "Perdida" else "#888888" if row['status'] == "Excluída" else "#ff6600"
                        
                        col_chk, col_card = st.columns([0.3, 9.7])
                        with col_chk:
                            st.write("")
                            if st.checkbox(" ", key=f"chk_{row['id']}"): selecionados.append(row['id'])
                            
                        with col_card:
                            st.markdown(f"""
                            <div style="background:#fff; padding:15px; border-radius:8px; border-left:6px solid {cor_status}; margin-bottom:5px; box-shadow:0 2px 5px rgba(0,0,0,0.05);">
                                <div style="display:flex; justify-content:space-between;">
                                    <div>
                                        <strong style="font-size:1.1rem; color:#262730;">{html.escape(row['nome_cliente'])}</strong><br>
                                        <span style="color:#777; font-size:0.85rem;">Proposta #{row['id']} | CNPJ: {html.escape(row['cnpj_cliente'])} | Data: {row['data_fmt']}</span>
                                    </div>
                                    <div style="text-align:right;">
                                        <span style="background:{cor_status}22; color:{cor_status}; padding:3px 8px; border-radius:4px; font-size:0.8rem; font-weight:bold;">{row['status']}</span><br>
                                        <strong style="color:#333; font-size:0.9rem;">Setup: R$ {f_br(row['valor_setup'])} | Mensal: R$ {f_br(row['valor_mensal'])}</strong>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            c_b1, c_b2, _ = st.columns([2, 2, 6])
                            with c_b1:
                                if st.button("Carregar Proposta", key=f"load_{row['id']}", use_container_width=True):
                                    desempacotar_simulacao(row['dados_simulacao'], row['id'])
                                    st.rerun()
                            with c_b2:
                                novo_status = st.selectbox("Mudar Status", ["Em Negociação", "Contrato Assinado", "Perdida", "Excluída"], index=["Em Negociação", "Contrato Assinado", "Perdida", "Excluída"].index(row['status']) if row['status'] in ["Em Negociação", "Contrato Assinado", "Perdida", "Excluída"] else 0, key=f"stat_{row['id']}", label_visibility="collapsed")
                                if novo_status != row['status']:
                                    with engine.begin() as conn:
                                        conn.execute(text("UPDATE propostas SET status = :s, data_atualizacao = CURRENT_TIMESTAMP WHERE id = :id"), {"s": novo_status, "id": row['id']})
                                    st.rerun()
                                    
                    if selecionados:
                        st.markdown("---")
                        st.info(f"**{len(selecionados)}** propostas selecionadas para alteração em lote.")
                        c_l1, c_l2, _ = st.columns([3, 2, 5])
                        novo_status_lote = c_l1.selectbox("Selecione o novo status para aplicar a todos:", ["Em Negociação", "Contrato Assinado", "Perdida", "Excluída"])
                        if c_l2.button("Aplicar Alteração", type="primary", use_container_width=True):
                            with engine.begin() as conn:
                                conn.execute(text("UPDATE propostas SET status = :s, data_atualizacao = CURRENT_TIMESTAMP WHERE id = ANY(:ids)"), {"s": novo_status_lote, "ids": selecionados})
                            st.success("Status atualizados com sucesso.")
                            st.rerun()

                elif visao == "Kanban":
                    k_cols = st.columns(4)
                    status_map = {
                        "Em Negociação": (k_cols[0], "#ff6600"),
                        "Contrato Assinado": (k_cols[1], "#22c55e"),
                        "Perdida": (k_cols[2], "#ef4444"),
                        "Excluída": (k_cols[3], "#888888")
                    }
                    for status_nome, (col_obj, cor) in status_map.items():
                        with col_obj:
                            st.markdown(f"<div style='background-color:#fff; border-top:4px solid {cor}; padding:10px; border-radius:4px; text-align:center; font-weight:bold; margin-bottom:15px; color:#262730; box-shadow:0 1px 3px rgba(0,0,0,0.05);'>{status_nome}</div>", unsafe_allow_html=True)
                            df_filtrado = df_hist[df_hist['status'] == status_nome]
                            for _, row in df_filtrado.iterrows():
                                st.markdown(f"""
                                <div style="background:#fff; padding:15px; border:1px solid #e0e0e0; border-radius:8px; margin-bottom:10px; box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                                    <strong style="color:#262730; font-size:0.95rem; display:block; margin-bottom:5px;">{html.escape(row['nome_cliente'])}</strong>
                                    <span style="font-size:0.75rem; color:#888; display:block; margin-bottom:8px;">ID: #{row['id']} | {row['data_fmt'][:10]}</span>
                                    <div style="background:#f9f9f9; padding:5px; border-radius:4px;">
                                        <span style="font-size:0.8rem; color:#555; display:block;">Setup: R$ {f_br(row['valor_setup'])}</span>
                                        <span style="font-size:0.85rem; color:#262730; font-weight:bold; display:block;">Mensal: R$ {f_br(row['valor_mensal'])}</span>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                if st.button("Abrir", key=f"kb_load_{row['id']}", use_container_width=True):
                                    desempacotar_simulacao(row['dados_simulacao'], row['id'])
                                    st.rerun()

        except Exception: st.error("Serviço indisponível no momento.")

    elif tela == "Consulta de Preco":
        st.markdown(f"""<h1 class="hero-title">ANÁLISE TÉCNICA</h1>""", unsafe_allow_html=True)
        st.markdown(f"""<div class="mapeamento-container"><h3 style="margin:0; color:#ff6600;">Simulador de Negociação Individual</h3></div>""", unsafe_allow_html=True)
        cb, cd = st.columns([2, 1])
        p_sel = cb.selectbox("Selecione o produto:", sorted(list(full_db.keys())))
        desc_s = cd.number_input("Simular Desconto (%)", 0.0, 30.0, 0.0, 0.5)
        
        if p_sel:
            d = full_db[p_sel]
            v_b = d.get('valor_projeto', 0.0) if (d.get('typeproductid') == 606 and d.get('valor_projeto', 0.0) > 0) else d.get('valor', 0.0)
            v_l = v_b * (1 - (desc_s/100))
            p_id = name_to_id.get(p_sel)
            is_sistema = (d.get('typeproductid') == 604)
            t_s, h_s = 0.0, ""
            
            if p_id in vinculos_db and any(v['tipo'] in ['projeto', 'adesao'] for v in vinculos_db[p_id]):
                for r in vinculos_db[p_id]:
                    if r['tipo'] in ['projeto', 'adesao']:
                        f_nm = id_to_name.get(r['id_filho'])
                        d_f = full_db.get(f_nm, {})
                        f_val = d_f.get('valor_projeto', 0.0) if (d_f.get('typeproductid') == 606 and d_f.get('valor_projeto', 0.0) > 0) else d_f.get('valor', 0.0)
                        f_q = int(r['qtd'])
                        t_s += (f_q * f_val); uni = "h" if r['tipo'] == 'projeto' else "un"
                        h_s += f"<li><span class='item-name'>{f_nm}</span><span class='item-detalhe'>{f_q}{uni} x R$ {f_br(f_val)} | Total: R$ {f_br(f_q*f_val)}</span></li>"
            else:
                h_p, v_he, ads = int(d.get('horas_padrao', 0)), d.get('valor_projeto', 0.0), d.get('adesao_vinculada', 0.0)
                rt = v_he if v_he > 0 else v_h_base_global
                t_s = (h_p * rt) + ads
                if h_p > 0: h_s += f"<li><span class='item-name'>Implantação</span><span class='item-detalhe'>{h_p}h x R$ {f_br(rt)} | Total: R$ {f_br(h_p*rt)}</span></li>"
                if ads > 0: h_s += f"<li><span class='item-name'>Taxa de Adesão</span><span class='item-detalhe'>1 un x R$ {f_br(ads)} | Total: R$ {f_br(ads)}</span></li>"
                
            if is_sistema:
                c1, c2, c3 = st.columns(3)
                with c1: st.markdown(f"""<div class="resumo-card"><span class="resumo-label" style="font-size:0.8rem; font-weight:bold; color:#777;">Investimento de Setup</span><div class="resumo-valor">R$ {f_br(t_s)}</div><div class="resumo-subtitulo" style="font-weight:bold; color:#444; margin-top:10px;">COMPOSIÇÃO</div><ul class="lista-itens">{h_s if h_s else "<li>Isento</li>"}</ul></div>""", unsafe_allow_html=True)
                with c2:
                    html_b = f"""<span style="text-decoration: line-through; color: #777; font-size: 0.9rem;">R$ {f_br(v_b)}</span>""" if desc_s > 0 else ""
                    st.markdown(f"""<div class="resumo-card" style="border-top-color:#2e7d32;"><span class="resumo-label" style="font-size:0.8rem; font-weight:bold; color:#777;">Investimento Mensal</span><div class="resumo-valor" style="color:#2e7d32;">R$ {f_br(v_l)}</div>{html_b}<div class="resumo-subtitulo" style="font-weight:bold; color:#444; margin-top:10px;">DETALHE</div><ul class="lista-itens"><li><span class='item-name'>Desconto Aplicado</span><span class="item-detalhe">{f_pct(desc_s)}%</span></li></ul></div>""", unsafe_allow_html=True)
                with c3: st.markdown(f"""<div class="resumo-card" style="border-top-color:#262730; min-height: auto;"><span class="resumo-label" style="font-size:0.8rem; font-weight:bold; color:#777;">Resumo Anual</span><div style="margin-top:15px;"><p><b>Economia Mensal:</b> R$ {f_br(v_b-v_l)}</p><p><b>Economia Anual:</b> R$ {f_br((v_b-v_l)*12)}</p></div></div>""", unsafe_allow_html=True)
            else:
                c1, c2 = st.columns(2)
                with c1:
                    html_b = f"""<span style="text-decoration: line-through; color: #777; font-size: 0.9rem;">R$ {f_br(v_b)}</span>""" if desc_s > 0 else ""
                    st.markdown(f"""<div class="resumo-card"><span class="resumo-label" style="font-size:0.8rem; font-weight:bold; color:#777;">Setup / Serviço Único</span><div class="resumo-valor">R$ {f_br(v_l)}</div>{html_b}<div class="resumo-subtitulo" style="font-weight:bold; color:#444; margin-top:10px;">DETALHE</div><ul class="lista-itens"><li><span class='item-name'>Desconto Aplicado</span><span class="item-detalhe">{f_pct(desc_s)}%</span></li></ul></div>""", unsafe_allow_html=True)
                with c2: st.markdown(f"""<div class="resumo-card" style="border-top-color:#262730; min-height: auto;"><span class="resumo-label" style="font-size:0.8rem; font-weight:bold; color:#777;">Resumo do Desconto</span><div style="margin-top:15px;"><p><b>Economia Total Gerada:</b> R$ {f_br(v_b-v_l)}</p><p style="color:#777; font-size:0.85rem;">*Este item não possui faturamento recorrente mensal.</p></div></div>""", unsafe_allow_html=True)

    # ==========================================
    # TELA VISÃO DO GESTOR
    # ==========================================
    elif tela == "Visão do Gestor":
        st.markdown("""<h1 class="hero-title" style="margin-bottom:25px;">DASHBOARD COMERCIAL</h1>""", unsafe_allow_html=True)
        
        try:
            engine = get_db_engine()
            with engine.connect() as conn:
                df_dash = pd.read_sql("SELECT * FROM propostas WHERE status != 'Excluída'", conn)
                try: df_logs = pd.read_sql("SELECT email_usuario, DATE(data_acesso) as data FROM logs_acesso", conn)
                except: df_logs = pd.DataFrame()
            
            if df_dash.empty:
                st.info("O CRM ainda não possui propostas para gerar indicadores.")
            else:
                ganhas = df_dash[df_dash['status'] == 'Contrato Assinado']
                negociacao = df_dash[df_dash['status'] == 'Em Negociação']
                perdidas = df_dash[df_dash['status'] == 'Perdida']
                
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.markdown(f"""<div class="resumo-card" style="min-height:auto; border-top-color:#ff6600;"><span style="color:#777; font-weight:bold; font-size:0.8rem;">TOTAL EM NEGOCIAÇÃO</span><div style="font-size:2rem; font-weight:900; color:#262730;">{len(negociacao)}</div></div>""", unsafe_allow_html=True)
                with c2: st.markdown(f"""<div class="resumo-card" style="min-height:auto; border-top-color:#22c55e;"><span style="color:#777; font-weight:bold; font-size:0.8rem;">CONTRATOS ASSINADOS</span><div style="font-size:2rem; font-weight:900; color:#22c55e;">{len(ganhas)}</div></div>""", unsafe_allow_html=True)
                with c3: st.markdown(f"""<div class="resumo-card" style="min-height:auto; border-top-color:#1976d2;"><span style="color:#777; font-weight:bold; font-size:0.8rem;">RECEITA SETUP (GANHA)</span><div style="font-size:1.8rem; font-weight:900; color:#262730;">R$ {f_br(ganhas['valor_setup'].sum())}</div></div>""", unsafe_allow_html=True)
                with c4: st.markdown(f"""<div class="resumo-card" style="min-height:auto; border-top-color:#2e7d32;"><span style="color:#777; font-weight:bold; font-size:0.8rem;">MRR ADQUIRIDO (MENSAL)</span><div style="font-size:1.8rem; font-weight:900; color:#2e7d32;">R$ {f_br(ganhas['valor_mensal'].sum())}</div></div>""", unsafe_allow_html=True)
                
                st.write("---")
                col_dash1, col_dash2 = st.columns([2, 1])
                with col_dash1:
                    st.markdown("### Ranking de Vendedores (Financeiro)")
                    if not ganhas.empty:
                        rank = ganhas.groupby('vendedor_email').agg({'id':'count', 'valor_setup':'sum', 'valor_mensal':'sum'}).reset_index()
                        rank = rank.sort_values(by='valor_mensal', ascending=False)
                        rank.columns = ['Vendedor', 'Contratos', 'Setup Total', 'Mensalidade Total']
                        rank['Setup Total'] = rank['Setup Total'].apply(lambda x: f"R$ {f_br(x)}")
                        rank['Mensalidade Total'] = rank['Mensalidade Total'].apply(lambda x: f"R$ {f_br(x)}")
                        st.dataframe(rank, use_container_width=True, hide_index=True)
                    else: st.info("Ainda não há contratos assinados para gerar o ranking.")
                        
                with col_dash2:
                    st.markdown("### Resumo do Funil")
                    total_geral = len(df_dash)
                    taxa_conversao = (len(ganhas) / total_geral) * 100 if total_geral > 0 else 0
                    st.markdown(f"""
                    <div style="background:#fff; padding:20px; border-radius:8px; border:1px solid #eee; box-shadow:0 2px 5px rgba(0,0,0,0.05);">
                        <p style="margin-bottom:10px;"><strong style="color:#262730;">Taxa de Conversão:</strong> <span style="font-size:1.2rem; color:#22c55e; font-weight:bold;">{taxa_conversao:.1f}%</span></p>
                        <p style="margin-bottom:10px;"><strong style="color:#262730;">Propostas Perdidas:</strong> <span style="font-size:1.2rem; color:#ef4444; font-weight:bold;">{len(perdidas)}</span></p>
                        <p style="margin-bottom:10px;"><strong style="color:#262730;">Ticket Médio Mensal:</strong> <span style="font-size:1.2rem; color:#ff6600; font-weight:bold;">R$ {f_br(ganhas['valor_mensal'].mean()) if len(ganhas)>0 else '0,00'}</span></p>
                    </div>
                    """, unsafe_allow_html=True)

                st.write("---")
                st.markdown("### Engajamento e Cadência (Operacional)")
                col_op1, col_op2 = st.columns(2)
                
                with col_op1:
                    st.markdown("**Acessos ao Sistema (Logins)**")
                    if not df_logs.empty:
                        logs_agg = df_logs.groupby('email_usuario').size().reset_index(name='Total de Logins')
                        logs_agg = logs_agg.sort_values(by='Total de Logins', ascending=False)
                        st.dataframe(logs_agg, use_container_width=True, hide_index=True)
                    else: st.warning("Não há acessos registrados ainda.")
                
                with col_op2:
                    st.markdown("**Propostas Geradas por Dia**")
                    df_dash['data_curta'] = pd.to_datetime(df_dash['data_atualizacao']).dt.date
                    prop_dia = df_dash.groupby(['data_curta', 'vendedor_email']).size().reset_index(name='Propostas Movimentadas')
                    prop_dia = prop_dia.sort_values(by='data_curta', ascending=False).head(15)
                    prop_dia.columns = ['Data', 'Vendedor', 'Propostas Movimentadas']
                    st.dataframe(prop_dia, use_container_width=True, hide_index=True)

        except Exception:
            st.error("Falha técnica interna.")
            
    # ==========================================
    # ROTA INJETADA: COMERCIAL E COMISSIONAMENTO
    # ==========================================
    elif tela == "Visão Comercial":
        tela_visao_comercial()
    elif tela == "Comissionamento":
        tela_comissionamento()

# ==========================================
# ROTEADOR DE SEGURANÇA
# ==========================================
if not st.session_state.logged_in: 
    tela_login()
else: 
    aplicativo_principal()
