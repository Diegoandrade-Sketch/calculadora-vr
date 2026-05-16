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

# ==========================================
# CONFIGURAÇÕES INICIAIS E CONTROLE DE VERSÃO
# ==========================================
st.set_page_config(page_title="VR Software | Sales Intelligence", layout="wide")

APP_VERSION = "v3.1.1 - Form Shield & Persistence"
CACHE_FILE = "cache_vr.json"

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
# FUNÇÕES DE FORMATAÇÃO E BLINDAGEM DE DADOS
# ==========================================
def f_br(valor):
    if pd.isna(valor) or valor == 0: return "0,00"
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def f_pct(valor):
    return str(valor).replace('.', ',')

def sync_state(key_permanente, key_widget):
    st.session_state[key_permanente] = st.session_state[key_widget]

def get_logo_base64():
    if os.path.exists("logo_vr.png"):
        with open("logo_vr.png", "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    return ""

# Callbacks para blindar o formulário do Cliente
def atualiza_nome_cliente():
    st.session_state.in_nome_cliente = st.session_state.widget_nome

def atualiza_cnpj_cliente():
    raw = str(st.session_state.widget_cnpj)
    # Remove letras e símbolos
    apenas_numeros = re.sub(r'\D', '', raw)[:14]
    
    if len(apenas_numeros) == 14:
        # Aplica a máscara matemática se tiver 14 dígitos
        formatado = f"{apenas_numeros[:2]}.{apenas_numeros[2:5]}.{apenas_numeros[5:8]}/{apenas_numeros[8:12]}-{apenas_numeros[12:]}"
        st.session_state.widget_cnpj = formatado
        st.session_state.in_cnpj_cliente = formatado
    else:
        st.session_state.widget_cnpj = apenas_numeros
        st.session_state.in_cnpj_cliente = apenas_numeros

# ==========================================
# DATA LAYER (CACHE DE 1 HORA E CONTINGÊNCIA)
# ==========================================
@st.cache_data(ttl=3600)
def carregar_dados_vendas():
    status_msg, status_cor = "Desconectado", "#ef4444"
    try:
        if CONN_STR:
            engine = create_engine(CONN_STR)
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
        for col in ['valor', 'horas_padrao', 'adesao_vinculada', 'valor_hora_implantacao', 'typeproductid']:
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

# ==========================================
# ESTADO GLOBAL E AUTENTICAÇÃO
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_role' not in st.session_state: st.session_state.user_role = None
if 'primeiro_acesso' not in st.session_state: st.session_state.primeiro_acesso = False
if 'user_email' not in st.session_state: st.session_state.user_email = ""
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'unidade_nome' not in st.session_state: st.session_state.unidade_nome = "VR Software"

# Variáveis do cofre (para não perder os dados na tela)
if 'in_nome_cliente' not in st.session_state: st.session_state.in_nome_cliente = ""
if 'in_cnpj_cliente' not in st.session_state: st.session_state.in_cnpj_cliente = ""

init_state = {
    'm_combo': "Montar Manualmente", 'm_pdv_conv': 0.0, 'm_pdv_touch': 0.0, 'm_pdv_self': 0.0, 'm_semanas': 0.0, 'm_mobile': 0.0,
    'm_tef': "Nao utiliza", 'm_migracao': False, 'm_ecommerce': False, 'm_app': False, 'm_connect': False,
    'm_erp_pro': False, 'm_xml': False, 'm_escopo': False, 'm_controller': False, 'm_cartaz': False, 'm_masterfisco': False, 'm_backup': False,
    'auto_added': set(), 'sel_m': [], 'sel_i': [], 'sel_d': [], 'ui_sel_m': [], 'ui_sel_i': [], 'ui_sel_d': [],
    'show_digital_proposal': False 
}

for k, v in init_state.items():
    if k not in st.session_state: st.session_state[k] = v

for nome in full_db.keys():
    if f"perm_val_{nome}" not in st.session_state: st.session_state[f"perm_val_{nome}"] = 0.0

# ==========================================
# BLOCO 1: MÓDULO DE LOGIN
# ==========================================
def tela_login():
    st.markdown("""
        <style>
        .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%); }
        div[data-testid="stForm"] {
            background-color: #ffffff; border-radius: 16px; padding: 40px 30px;
            border: none; box-shadow: 0 15px 35px rgba(0, 0, 0, 0.05), 0 5px 15px rgba(0, 0, 0, 0.03);
        }
        div[data-testid="stForm"] button {
            background: linear-gradient(90deg, #ff6600 0%, #ff8533 100%); color: white;
            border: none; border-radius: 8px; font-weight: 600; padding: 0.5rem 1rem;
            transition: all 0.3s ease; margin-top: 15px;
        }
        div[data-testid="stForm"] button:hover {
            background: linear-gradient(90deg, #e65c00 0%, #ff6600 100%); box-shadow: 0 4px 15px rgba(255, 102, 0, 0.4); color: white;
        }
        div[data-testid="stTextInput"] input { border-radius: 8px; border: 1px solid #e0e0e0; padding: 12px 15px; background-color: #fcfcfc; }
        div[data-testid="stTextInput"] input:focus { border-color: #ff6600; box-shadow: 0 0 0 1px #ff6600; background-color: #ffffff; }
        </style>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.write(""); st.write("")
        with st.form("login_form", clear_on_submit=False):
            col_img1, col_img2, col_img3 = st.columns([1, 2, 1])
            with col_img2:
                if os.path.exists("logo_vr.png"): st.image("logo_vr.png", use_container_width=True)
                else: st.markdown("<h2 style='text-align:center; color:#262730; margin-bottom:0;'>VR Software</h2>", unsafe_allow_html=True)
            
            st.markdown("<p style='text-align:center; color:#777; font-size:0.95rem; margin-bottom:25px;'>Acesso Restrito</p>", unsafe_allow_html=True)
            
            if st.session_state.primeiro_acesso:
                st.info("Identificamos seu primeiro acesso. Por favor, crie uma senha definitiva.")
                nova_senha = st.text_input("Nova Senha", type="password")
                confirma_senha = st.text_input("Confirme a Senha", type="password")
                if st.form_submit_button("Salvar e Acessar", use_container_width=True):
                    if nova_senha and nova_senha == confirma_senha:
                        try:
                            engine = create_engine(CONN_STR)
                            with engine.begin() as conn:
                                conn.execute(text("UPDATE usuarios SET senha = :s, primeiro_acesso = FALSE WHERE email = :e"), {"s": nova_senha, "e": st.session_state.user_email})
                            st.session_state.primeiro_acesso = False; st.session_state.logged_in = True; st.rerun()
                        except Exception: st.error("Erro de comunicação com o banco de dados.")
                    else: st.error("As senhas informadas não conferem.")
            else:
                email = st.text_input("E-mail corporativo")
                senha = st.text_input("Senha", type="password")
                if st.form_submit_button("Autenticar", use_container_width=True):
                    if email == "admin" and senha == "333666":
                        st.session_state.logged_in = True; st.session_state.user_role = "admin"; st.session_state.user_name = "Administrador Master"; st.session_state.unidade_nome = "Matriz"
                        st.rerun()
                    elif not CONN_STR: st.error("Conexão com o servidor falhou.")
                    else:
                        try:
                            engine = create_engine(CONN_STR)
                            with engine.connect() as conn:
                                sql = """
                                    SELECT u.*, un.nome_fantasia as nome_unidade 
                                    FROM usuarios u 
                                    LEFT JOIN unidades un ON u.id_unidade = un.id 
                                    WHERE u.email = :e AND u.ativo = TRUE
                                """
                                resultado = pd.read_sql(text(sql), conn, params={"e": email})
                            if not resultado.empty:
                                user = resultado.iloc[0]
                                if user['senha'] == senha or user['primeiro_acesso']:
                                    st.session_state.user_email = email
                                    st.session_state.user_role = user['nivel_acesso']
                                    st.session_state.user_name = user['nome']
                                    st.session_state.unidade_nome = user['nome_unidade'] if pd.notna(user['nome_unidade']) else "VR Software"
                                    if user['primeiro_acesso']: st.session_state.primeiro_acesso = True; st.rerun()
                                    else: st.session_state.logged_in = True; st.rerun()
                                else: st.error("Senha incorreta.")
                            else: st.error("Usuário não cadastrado ou bloqueado.")
                        except Exception: st.error("Ocorreu um erro ao validar os dados.")

# ==========================================
# BLOCO 2: MÓDULO DA PROPOSTA DIGITAL HTML
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
            @media print {{
                body {{ background: #fff; padding: 0; }}
                .container {{ box-shadow: none; max-width: 100%; border-radius: 0; }}
                .no-print {{ display: none !important; }}
                .page-break {{ page-break-before: always; }}
            }}
            .print-btn {{ background: #ff6600; color: white; border: none; padding: 12px 24px; font-size: 16px; font-weight: bold; border-radius: 8px; cursor: pointer; display: flex; align-items: center; gap: 8px; margin: 20px auto; box-shadow: 0 4px 15px rgba(255,102,0,0.3); transition: 0.3s; }}
            .cover {{ background: #262730; color: white; padding: 60px 40px; position: relative; border-left: 15px solid #ff6600; }}
            .cover h1 {{ font-size: 48px; margin: 0; font-weight: 900; letter-spacing: -1px; }}
            .cover h2 {{ color: #ff6600; font-weight: 400; font-size: 24px; margin-top: 10px; }}
            .brand {{ font-size: 20px; font-weight: bold; color: #ff6600; margin-bottom: 40px; letter-spacing: 2px; }}
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
            .item-incluso {{ color: #888; font-style: italic; border: none !important; padding-top: 4px !important; padding-left: 15px !important; }}
            .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #888; font-size: 12px; }}
            .signatures {{ display: grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-top: 40px; }}
            .sig-line {{ border-top: 1px solid #333; padding-top: 10px; font-weight: bold; color: #333; }}
        </style>
    </head>
    <body>
        <div class="no-print" style="text-align: center;">
            <button class="print-btn" onclick="window.print()">🖨️ Salvar como PDF / Imprimir</button>
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
                        <div class="detail-value">{st.session_state.user_name}</div>
                        <div class="detail-sub" style="color: #ff6600;">{st.session_state.unidade_nome}</div>
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
        </style>
    """, unsafe_allow_html=True)

    def processar_regras_colaterais():
        novos_auto = set()
        for m_nome in st.session_state.sel_m:
            p_id = name_to_id.get(m_nome)
            if p_id and p_id in vinculos_db:
                for r in vinculos_db[p_id]:
                    if r['tipo'] in ['projeto', 'adesao']:
                        f_nome = id_to_name.get(r['id_filho'])
                        if f_nome:
                            novos_auto.add(f_nome)
                            st.session_state[f"perm_val_{f_nome}"] = float(r['qtd'])

        lista_servicos_atual = list(st.session_state.ui_sel_i)
        for item in st.session_state.auto_added - novos_auto:
            if item in lista_servicos_atual:
                lista_servicos_atual.remove(item)
                st.session_state[f"perm_val_{item}"] = 0.0
        for item in novos_auto:
            if item not in lista_servicos_atual: lista_servicos_atual.append(item)
        st.session_state.auto_added = novos_auto; st.session_state.ui_sel_i = lista_servicos_atual; st.session_state.sel_i = lista_servicos_atual

    def atualiza_sistemas_ui(): st.session_state.sel_m = st.session_state.ui_sel_m; processar_regras_colaterais()
    def atualiza_servicos_ui(): st.session_state.sel_i = st.session_state.ui_sel_i
    def atualiza_despesas_ui(): st.session_state.sel_d = st.session_state.ui_sel_d

    def limpar_tudo():
        for k, v in init_state.items(): 
            st.session_state[k] = v if not isinstance(v, list) else []
            if isinstance(v, set): st.session_state[k] = set()
        if 'tmp_combo' in st.session_state: st.session_state.tmp_combo = "Montar Manualmente"
        for t in ['tmp_pdv_conv', 'tmp_pdv_touch', 'tmp_pdv_self', 'tmp_semanas', 'tmp_mobile']:
            if t in st.session_state: st.session_state[t] = 0.0
        for t in ['tmp_erp_pro', 'tmp_xml', 'tmp_connect', 'tmp_backup', 'tmp_cartaz', 'tmp_ecommerce', 'tmp_controller', 'tmp_masterfisco', 'tmp_app', 'tmp_migracao', 'tmp_escopo']:
            if t in st.session_state: st.session_state[t] = False
        for nome in full_db.keys(): st.session_state[f"perm_val_{nome}"] = 0.0
        
        # Limpar os dados do cliente e os widgets
        st.session_state.in_nome_cliente = ""
        st.session_state.in_cnpj_cliente = ""
        if 'widget_nome' in st.session_state: st.session_state.widget_nome = ""
        if 'widget_cnpj' in st.session_state: st.session_state.widget_cnpj = ""
        st.session_state.show_digital_proposal = False

    def sync_combo():
        if st.session_state.tmp_combo == "Padrao Pequeno Porte":
            st.session_state.m_pdv_touch = 0.0; st.session_state.m_pdv_self = 0.0
            st.session_state.m_ecommerce = False; st.session_state.m_app = False; st.session_state.m_connect = False
            st.session_state.m_controller = False; st.session_state.m_cartaz = False; st.session_state.m_masterfisco = False; st.session_state.m_backup = False
            st.session_state.m_semanas = 0.0
            st.session_state.m_erp_pro = True; st.session_state.m_pdv_conv = 3.0; st.session_state.m_xml = True; st.session_state.m_mobile = 1.0
            st.session_state.m_tef = "SiTef Express"; st.session_state.m_migracao = True; st.session_state.m_escopo = True

    # SIDEBAR
    with st.sidebar:
        if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=180)
        st.markdown(f"<div style='background-color:#f0f0f0; padding:10px; border-radius:5px; margin-bottom:15px; border-left:4px solid #ff6600;'><span style='font-weight:bold; color:#333;'>👤 {st.session_state.user_name}</span></div>", unsafe_allow_html=True)
        abas_navegacao = ["Gerador de Proposta", "Consulta de Preco"]
        if st.session_state.user_role == "admin":
            if not st.toggle("Simular Visão Vendedor", value=False): abas_navegacao.append("Painel Admin")
        tela = st.radio("Navegação:", abas_navegacao)
        if tela == "Gerador de Proposta":
            st.write("---")
            mapeamento_ativo = st.toggle("Mapeamento Inteligente", value=False)
            modo_apresentacao = st.toggle("Modo Apresentação (Ocultar Menus)")
            perfil_venda = st.selectbox("Perfil do Cliente", ["Executivo (Rua)", "CS (Base)"])
            desc = st.number_input("Desconto Mensalidade (%)", 0.0, 30.0, 0.0, 0.5)
            exibir_detalhe_desc = st.toggle("Exibir Desconto na Tela", value=True)
            exibir_media_loja = st.toggle("Exibir Media por Loja", value=False)
            faturamento_sistema = st.selectbox("Início Mensalidade", ["Na assinatura", "30 dias", "60 dias", "Após implantação"])
            parcelas_setup = st.selectbox("Parcelas Setup", [1, 2, 3, 4, 5, 6, 10, 12], index=3)
            regra_despesas = st.selectbox("Faturamento Despesas", ["Faturamento na assinatura", "Faturamento pós Implantação"])
        st.write("---")
        if st.button("Sair (Logout)", use_container_width=True): st.session_state.clear(); st.rerun()
        st.markdown(f"""<hr><div style="font-size:0.8rem; color:{db_cor};">{db_status}</div><div style="font-size:0.7rem; color:#888;">{APP_VERSION}</div>""", unsafe_allow_html=True)

    # TELA 1: PAINEL ADMIN
    if tela == "Painel Admin":
        st.markdown("""<h1 class="hero-title">BACKOFFICE</h1>""", unsafe_allow_html=True)
        t_vinc, t_unid, t_user, t_sql, t_cat = st.tabs(["🔗 Vínculos Relacionais", "🏢 Unidades", "👥 Usuários", "💻 Terminal SQL", "📋 Catálogo"])
        with t_unid:
            st.markdown("<div class='section-header'><span class='section-title'>Cadastro de Escritórios e Unidades</span></div>", unsafe_allow_html=True)
            with st.form("form_unidades"):
                c1, c2, c3 = st.columns([2, 1, 1])
                n_fantasia = c1.text_input("Nome Fantasia (Ex: VR Recife)")
                v_cnpj = c2.text_input("CNPJ")
                v_cidade = c3.text_input("Cidade")
                v_end = st.text_input("Endereço Completo (Para cabeçalho de proposta)")
                if st.form_submit_button("Salvar Nova Unidade"):
                    try:
                        engine = create_engine(CONN_STR)
                        with engine.begin() as conn:
                            conn.execute(text("INSERT INTO unidades (nome_fantasia, cnpj, cidade, logradouro) VALUES (:n, :c, :ci, :e)"), {"n": n_fantasia, "c": v_cnpj, "ci": v_cidade, "e": v_end})
                        st.success("Unidade cadastrada com sucesso!")
                    except Exception as e: st.error(f"Erro: {e}")
            try:
                engine = create_engine(CONN_STR)
                st.dataframe(pd.read_sql("SELECT id, nome_fantasia, cnpj, cidade, ativo FROM unidades", engine), use_container_width=True)
            except Exception: pass
        with t_user:
            st.markdown("<div class='section-header'><span class='section-title'>Gestão da Equipe Comercial</span></div>", unsafe_allow_html=True)
            try:
                engine = create_engine(CONN_STR)
                df_unid_list = pd.read_sql("SELECT id, nome_fantasia FROM unidades WHERE ativo = TRUE", engine)
                if df_unid_list.empty: st.warning("Cadastre uma Unidade antes de criar usuários.")
                else:
                    unid_dict = dict(zip(df_unid_list['nome_fantasia'], df_unid_list['id']))
                    with st.form("form_usuarios"):
                        c1, c2 = st.columns(2)
                        u_nome, u_email = c1.text_input("Nome Completo"), c2.text_input("E-mail Corporativo")
                        c3, c4 = st.columns(2)
                        u_unid, u_role = c3.selectbox("Unidade Vinculada", list(unid_dict.keys())), c4.selectbox("Nível de Acesso", ["vendedor", "admin"])
                        if st.form_submit_button("Criar Usuário"):
                            with engine.begin() as conn:
                                conn.execute(text("INSERT INTO usuarios (nome, email, nivel_acesso, id_unidade, senha, primeiro_acesso) VALUES (:n, :e, :r, :id_u, '123456', TRUE)"), {"n": u_nome, "e": u_email, "r": u_role, "id_u": unid_dict[u_unid]})
                            st.success(f"Usuário {u_nome} criado! Senha provisória: 123456")
                    st.dataframe(pd.read_sql("SELECT u.id, u.nome, u.email, u.nivel_acesso, un.nome_fantasia as unidade, u.ativo FROM usuarios u LEFT JOIN unidades un ON u.id_unidade = un.id", engine), use_container_width=True)
            except Exception as e: st.error(f"Erro ao carregar dados: {e}")
        with t_vinc:
            with st.form("form_v"):
                c1, c2, c3, c4 = st.columns([2,2,1,1])
                pai, fil = c1.selectbox("Pai (SISTEMA):", sorted(list(sistemas_db.keys()))), c2.selectbox("Filho (ITEM):", sorted(list(full_db.keys())))
                tip, qtd = c3.selectbox("Tipo:", ["projeto", "adesao", "incluso"]), c4.number_input("Qtd:", min_value=0.0, value=1.0)
                if st.form_submit_button("Salvar Vínculo"):
                    try:
                        engine = create_engine(CONN_STR)
                        with engine.begin() as conn:
                            conn.execute(text("INSERT INTO product_vinculo (id_produto_pai, id_produto_filho, tipo_vinculo, quantidade_padrao) VALUES (:p, :f, :t, :q)"), {"p": name_to_id[pai], "f": name_to_id[fil], "t": tip, "q": qtd})
                        st.success("Vínculo Criado com Sucesso!"); st.cache_data.clear()
                    except Exception as e: st.error(e)
            st.dataframe(df_vinc, use_container_width=True)
        with t_sql:
            st.warning("Terminal Blindado")
            query = st.text_area("Digite o comando SQL:")
            if st.button("Executar SQL"):
                if any(p in query.lower() for p in ["drop ", "delete ", "truncate "]): st.error("Comando bloqueado.")
                else:
                    try:
                        engine = create_engine(CONN_STR)
                        if query.lower().strip().startswith("select"):
                            with engine.connect() as conn: res = pd.read_sql(text(query), conn)
                            st.success(f"{len(res)} linhas retornadas."); st.dataframe(res, use_container_width=True)
                        else:
                            with engine.begin() as conn: r = conn.execute(text(query))
                            st.success(f"Linhas afetadas: {r.rowcount}"); st.cache_data.clear()
                    except Exception as e: st.error(e)
        with t_cat: st.dataframe(df_raw, use_container_width=True)

    # TELA 2: GERADOR DE PROPOSTA
    elif tela == "Gerador de Proposta":
        
        def aplicar_mapeamento():
            _sel_m, _sel_i, _sel_d = [], [], []
            for k in full_db.keys(): st.session_state[f"perm_val_{k}"] = 0.0

            for p_name in sistemas_db.keys():
                qtd = 0.0
                if p_name == "VR PDV Convencional": qtd = st.session_state.m_pdv_conv
                elif p_name == "VR PDV Touchscreen": qtd = st.session_state.m_pdv_touch
                elif p_name == "VR PDV Self Checkout": qtd = st.session_state.m_pdv_self
                elif p_name == "VR ERP PRO" and st.session_state.m_erp_pro: qtd = 1.0
                elif p_name == "VR Gerenciador Xml" and st.session_state.m_xml: qtd = 1.0
                elif p_name == "VR Connect (Android/IOS)" and st.session_state.m_connect: qtd = 1.0
                elif p_name == "VR Backup 050 Gb" and st.session_state.m_backup: qtd = 1.0
                elif p_name == "VR Cartaz" and st.session_state.m_cartaz: qtd = 1.0
                elif p_name == "VR E-Commerce" and st.session_state.m_ecommerce: qtd = 1.0
                elif p_name == "VR Controller 360 ( 1 CNPJ )" and st.session_state.m_controller: qtd = 1.0
                elif p_name == "VR Masterfisco Brasil" and st.session_state.m_masterfisco: qtd = 1.0
                elif p_name == "VR M-Commerce" and st.session_state.m_app: qtd = 1.0
                elif p_name == "VR Mobile (Smartphone/Android)": qtd = float(st.session_state.m_mobile)

                if st.session_state.m_tef == "SiTef Express":
                    tot = st.session_state.m_pdv_conv + st.session_state.m_pdv_touch + st.session_state.m_pdv_self
                    if tot <= 3 and p_name == "VR Sitef Express ate 3 PDVs": qtd = 1.0
                    elif 3 < tot <= 6 and p_name == "VR Sitef Express ate 6 PDVs": qtd = 1.0
                    elif 6 < tot <= 8 and p_name == "VR Sitef Express ate 8 PDVs": qtd = 1.0
                    elif tot > 8 and p_name == "VR Sitef Express a partir 9 PDVs": qtd = 1.0
                elif st.session_state.m_tef == "VR TEF" and p_name.lower() == "vr tef": qtd = 1.0

                if qtd > 0: st.session_state[f"perm_val_{p_name}"] = qtd; _sel_m.append(p_name)

            sem = st.session_state.m_semanas
            for s_name in servicos_db.keys():
                s_low = s_name.lower()
                qtd = 0.0
                if "implanta" in s_low and "treinamento" in s_low: qtd = sem * 44.0
                elif st.session_state.m_escopo and "escopo" in s_low: qtd = 8.0
                elif st.session_state.m_migracao and s_name == "Migracao de Dados Padrao": qtd = 8.0
                if qtd > 0: st.session_state[f"perm_val_{s_name}"] = qtd; _sel_i.append(s_name)

            if sem > 0:
                for d_name in despesas_db.keys():
                    d_low = d_name.lower()
                    qtd = 0.0
                    if "alimenta" in d_low: qtd = sem * 10.0
                    elif "hospedagem" in d_low: qtd = sem * 4.0
                    if qtd > 0: st.session_state[f"perm_val_{d_name}"] = qtd; _sel_d.append(d_name)
                        
            st.session_state.ui_sel_m = _sel_m; st.session_state.sel_m = _sel_m
            st.session_state.ui_sel_i = _sel_i; st.session_state.sel_i = _sel_i
            st.session_state.ui_sel_d = _sel_d; st.session_state.sel_d = _sel_d
            processar_regras_colaterais()

        st.markdown("""<h1 class="hero-title">PROPOSTA COMERCIAL</h1>""", unsafe_allow_html=True)
        
        # --- DADOS DO CLIENTE (Com Blindagem e Máscara) ---
        if modo_apresentacao:
            # Apresentação do Cliente Fixa
            st.markdown(f"""
            <div style="background-color:#ffffff; border-left: 10px solid #262730; padding: 20px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                <span style="color:#ff6600; font-size:0.9rem; text-transform:uppercase; font-weight:bold;">Apresentação para o cliente:</span>
                <h2 style="margin:5px 0; color:#262730;">{st.session_state.in_nome_cliente or "Cliente Não Informado"}</h2>
                <span style="color:#777; font-size:1.1rem; font-weight:bold;">CNPJ: {st.session_state.in_cnpj_cliente if st.session_state.in_cnpj_cliente else "Não informado"}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Campos Editáveis
            st.markdown("""<div class="cliente-container"><h3 style="margin:0; color:#262730;">Dados do Cliente</h3></div>""", unsafe_allow_html=True)
            col_cli1, col_cli2 = st.columns([2, 1])
            with col_cli1:
                st.text_input("Razão Social / Nome Fantasia", value=st.session_state.in_nome_cliente, key="widget_nome", on_change=atualiza_nome_cliente, placeholder="Ex: Supermercados Dois Irmãos")
            with col_cli2:
                st.text_input("CNPJ (Apenas números)", value=st.session_state.in_cnpj_cliente, key="widget_cnpj", on_change=atualiza_cnpj_cliente, placeholder="00.000.000/0000-00", max_chars=18)
            st.write("---")

        if mapeamento_ativo and not modo_apresentacao:
            st.markdown("""<div class="mapeamento-container"><h3 style="margin:0; color:#ff6600;">Mapeamento da Operacao</h3></div>""", unsafe_allow_html=True)
            st.selectbox("Combo Rápido", ["Montar Manualmente", "Padrao Pequeno Porte"], key="tmp_combo", on_change=sync_combo)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.number_input("PDV Convencional", 0.0, step=1.0, key="tmp_pdv_conv", value=st.session_state.m_pdv_conv, on_change=sync_state, args=("m_pdv_conv", "tmp_pdv_conv"))
                st.number_input("PDV Touch", 0.0, step=1.0, key="tmp_pdv_touch", value=st.session_state.m_pdv_touch, on_change=sync_state, args=("m_pdv_touch", "tmp_pdv_touch"))
                st.number_input("PDV Selfcheckout", 0.0, step=1.0, key="tmp_pdv_self", value=st.session_state.m_pdv_self, on_change=sync_state, args=("m_pdv_self", "tmp_pdv_self"))
            with c2:
                st.selectbox("TEF", ["Nao utiliza", "SiTef Express", "VR TEF"], key="tmp_tef", index=["Nao utiliza", "SiTef Express", "VR TEF"].index(st.session_state.m_tef), on_change=sync_state, args=("m_tef", "tmp_tef"))
                st.number_input("Semanas", 0.0, step=1.0, key="tmp_semanas", value=st.session_state.m_semanas, on_change=sync_state, args=("m_semanas", "tmp_semanas"))
                st.checkbox("Migração?", key="tmp_migracao", value=st.session_state.m_migracao, on_change=sync_state, args=("m_migracao", "tmp_migracao"))
                st.checkbox("Escopo?", key="tmp_escopo", value=st.session_state.m_escopo, on_change=sync_state, args=("m_escopo", "tmp_escopo"))
            with c3:
                st.number_input("VR Mobile", 0.0, step=1.0, key="tmp_mobile", value=st.session_state.m_mobile, on_change=sync_state, args=("m_mobile", "tmp_mobile"))
                sc1, sc2, sc3 = st.columns(3)
                sc1.toggle("VR ERP PRO", key="tmp_erp_pro", value=st.session_state.m_erp_pro, on_change=sync_state, args=("m_erp_pro", "tmp_erp_pro"))
                sc1.toggle("G. XML", key="tmp_xml", value=st.session_state.m_xml, on_change=sync_state, args=("m_xml", "tmp_xml"))
                sc1.toggle("Connect", key="tmp_connect", value=st.session_state.m_connect, on_change=sync_state, args=("m_connect", "tmp_connect"))
                sc2.toggle("VR Backup", key="tmp_backup", value=st.session_state.m_backup, on_change=sync_state, args=("m_backup", "tmp_backup"))
                sc2.toggle("VR Cartaz", key="tmp_cartaz", value=st.session_state.m_cartaz, on_change=sync_state, args=("m_cartaz", "tmp_cartaz"))
                sc2.toggle("E-Commerce", key="tmp_ecommerce", value=st.session_state.m_ecommerce, on_change=sync_state, args=("m_ecommerce", "tmp_ecommerce"))
                sc3.toggle("C. 360", key="tmp_controller", value=st.session_state.m_controller, on_change=sync_state, args=("m_controller", "tmp_controller"))
                sc3.toggle("MasterFisco", key="tmp_masterfisco", value=st.session_state.m_masterfisco, on_change=sync_state, args=("m_masterfisco", "tmp_masterfisco"))
                sc3.toggle("M-Commerce", key="tmp_app", value=st.session_state.m_app, on_change=sync_state, args=("m_app", "tmp_app"))
                b1, b2 = st.columns(2)
                b1.button("Aplicar Inteligência", on_click=aplicar_mapeamento, use_container_width=True)
                b2.button("Limpar Tudo", on_click=limpar_tudo, use_container_width=True)
            st.write("---")

        processar_regras_colaterais()

        if not modo_apresentacao:
            c1, c2, c3 = st.columns(3) if perfil_venda == "Executivo (Rua)" else (*st.columns(2), None)
            with c1:
                st.markdown("""<div class="section-header"><span class="section-title">IMPLANTAÇÃO E SERVIÇOS</span></div>""", unsafe_allow_html=True)
                st.multiselect("Serviços", list(servicos_db.keys()), key="ui_sel_i", on_change=atualiza_servicos_ui)
                for i in st.session_state.sel_i:
                    v_u = servicos_db[i]['valor']
                    st.number_input(f"{i} (R$ {f_br(v_u)}/h)", 0.0, step=1.0, value=st.session_state[f"perm_val_{i}"], key=f"tmp_i_{i}", on_change=sync_state, args=(f"perm_val_{i}", f"tmp_i_{i}"))
            with c2:
                st.markdown("""<div class="section-header"><span class="section-title">MENSALIDADES SISTEMAS</span></div>""", unsafe_allow_html=True)
                st.multiselect("Sistemas", list(sistemas_db.keys()), key="ui_sel_m", on_change=atualiza_sistemas_ui)
                for i in st.session_state.sel_m:
                    v_u = sistemas_db[i]['valor']
                    st.number_input(f"{i} (R$ {f_br(v_u)}/un)", 0.0, step=1.0, value=st.session_state[f"perm_val_{i}"], key=f"tmp_m_{i}", on_change=sync_state, args=(f"perm_val_{i}", f"tmp_m_{i}"))
            if c3:
                with c3:
                    st.markdown("""<div class="section-header"><span class="section-title">DESPESAS DO PROJETO</span></div>""", unsafe_allow_html=True)
                    st.multiselect("Despesas", list(despesas_db.keys()), key="ui_sel_d", on_change=atualiza_despesas_ui)
                    for i in st.session_state.sel_d:
                        v_u = despesas_db[i]['valor']
                        st.number_input(f"{i} (R$ {f_br(v_u)}/un)", 0.0, step=1.0, value=st.session_state[f"perm_val_{i}"], key=f"tmp_d_{i}", on_change=sync_state, args=(f"perm_val_{i}", f"tmp_d_{i}"))

        st.markdown("""<h2 style='text-align:center; font-weight:800; margin-top:30px;'>RESUMO DO INVESTIMENTO</h2>""", unsafe_allow_html=True)
        res_cols = st.columns(3) if perfil_venda == "Executivo (Rua)" else st.columns([1, 2, 2, 1])[1:3]
        
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
        v_h_base = servicos_db.get("Implantação e Treinamento", {}).get("valor", 0.0)
        lista_setup_pre_ordenacao = []
        html_setup_digital = ""

        for n in st.session_state.sel_i:
            q = st.session_state[f"perm_val_{n}"]
            if q > 0:
                v_u = servicos_db.get(n, full_db.get(n, {'valor':0.0}))['valor']
                t_setup += (q * v_u)
                html_linha = f"<li><span class='item-name'>{n}</span><span class='item-detalhe'>{int(q)}h x R$ {f_br(v_u)} | Total: R$ {f_br(q*v_u)}</span></li>"
                html_digital = f"<li><strong>{n}</strong><span class='detail'>{int(q)}h x R$ {f_br(v_u)} | Total: R$ {f_br(q*v_u)}</span></li>"
                lista_setup_pre_ordenacao.append({'nome_exibicao': n, 'html': html_linha, 'html_dig': html_digital})
        
        itens_isentos_setup = ["VR Mobile (Smartphone/Android)", "VR PDV Touchscreen", "VR PDV Self Checkout"]

        for n in st.session_state.sel_m:
            if name_to_id.get(n) not in vinculos_db:
                if n in itens_isentos_setup: continue
                d = sistemas_db[n]; h = d.get('horas_padrao', 0.0); ads = d.get('adesao_vinculada', 0.0)
                if h > 0:
                    v_rate = (d.get('valor_hora_implantacao', 0.0) or v_h_base)
                    t_setup += (h * v_rate)
                    nome_exibicao = "Projeto ERP PRO" if n == "VR ERP PRO" else f"Implantacao {n}"
                    html_linha = f"<li><span class='item-name'>{nome_exibicao}</span><span class='item-detalhe'>{int(h)}h x R$ {f_br(v_rate)} | Total: R$ {f_br(h*v_rate)}</span></li>"
                    html_digital = f"<li><strong>{nome_exibicao}</strong><span class='detail'>{int(h)}h x R$ {f_br(v_rate)} | Total: R$ {f_br(h*v_rate)}</span></li>"
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
            st.markdown(f"""<div class="resumo-card"><span class="resumo-label">Investimento Implantação (Setup)</span><div class="resumo-valor">R$ {f_br(t_setup)}</div><div style="font-weight:bold;">{parcelas_setup}x de R$ {f_br(t_setup/parcelas_setup)}</div><div class="resumo-subtitulo">DETALHAMENTO SETUP</div><ul class="lista-itens">{h_setup if h_setup else "<li>Nenhum item</li>"}</ul></div>""", unsafe_allow_html=True)

        t_mensal, h_m = 0.0, ""
        html_mensal_digital = ""
        sistemas_ordenados = sorted(st.session_state.sel_m, key=get_prioridade_mensal)
        
        for n in sistemas_ordenados:
            q = st.session_state[f"perm_val_{n}"]
            if q > 0:
                v_u = sistemas_db[n]['valor']; v_liq_u = v_u * (1 - (desc/100))
                t_mensal += (q * v_liq_u)
                h_m += f"<li><span class='item-name'>{n}</span><span class='item-detalhe'>{int(q)} un x R$ {f_br(v_u)} | Total: R$ {f_br(q*v_liq_u)}</span></li>"
                html_mensal_digital += f"<li><strong>{n}</strong><span class='detail'>{int(q)} un x R$ {f_br(v_u)} | Total: R$ {f_br(q*v_liq_u)}</span></li>"
                
                vincs = [id_to_name.get(v['id_filho']) for v in vinculos_db.get(name_to_id.get(n), []) if v['tipo'] == 'incluso']
                for inc in vincs: 
                    h_m += f"<li class='item-incluso'>└ {inc} (Incluso)</li>"
                    html_mensal_digital += f"<li class='item-incluso'>└ {inc} (Incluso)</li>"
                if n == "VR ERP PRO" and not vincs:
                    for inc in ["VR Promo", "VR Carteira Digital", "VR Analytics"]: 
                        h_m += f"<li class='item-incluso'>└ {inc} (Incluso)</li>"
                        html_mensal_digital += f"<li class='item-incluso'>└ {inc} (Incluso)</li>"

        with res_cols[1]:
            d_h = f"""<div style="color:#2e7d32; font-weight:bold;">Desconto: {desc}%</div>""" if (exibir_detalhe_desc and desc > 0) else """<div style="height:21px"></div>"""
            st.markdown(f"""<div class="resumo-card" style="border-top-color:#2e7d32;"><span class="resumo-label">Manutenção Mensal</span><div class="resumo-valor" style="color:#2e7d32;">R$ {f_br(t_mensal)}</div>{d_h}<div style="font-weight:bold;">Início: {faturamento_sistema}</div><div class="resumo-subtitulo">SISTEMAS</div><ul class="lista-itens">{h_m if h_m else "<li>Nenhum</li>"}</ul></div>""", unsafe_allow_html=True)

        t_d, h_d = 0.0, ""
        html_desp_digital = ""
        if perfil_venda == "Executivo (Rua)":
            for n in st.session_state.sel_d:
                q = st.session_state[f"perm_val_{n}"]
                if q > 0:
                    v_u = despesas_db[n]['valor']; t_d += (q * v_u)
                    h_d += f"<li><span class='item-name'>{n}</span><span class='item-detalhe'>{int(q)} un x R$ {f_br(v_u)} | Total: R$ {f_br(q*v_u)}</span></li>"
                    html_desp_digital += f"<li><strong>{n}</strong><span class='detail'>{int(q)} un x R$ {f_br(v_u)} | Total: R$ {f_br(q*v_u)}</span></li>"
            with res_cols[2]:
                st.markdown(f"""<div class="resumo-card" style="border-top-color:#1976d2;"><span class="resumo-label">Despesas do Projeto</span><div class="resumo-valor" style="color:#1976d2;">R$ {f_br(t_d)}</div><div style="color:#d32f2f; font-weight:bold; font-size:0.8rem;">{regra_despesas}</div><div class="resumo-subtitulo">DETALHAMENTO</div><ul class="lista-itens">{h_d if h_d else "<li>Sem despesas</li>"}</ul></div>""", unsafe_allow_html=True)

        if exibir_media_loja:
            qtd_lojas = st.session_state.get("perm_val_VR ERP PRO", 0.0)
            if qtd_lojas > 0:
                st.markdown(f"""<h3 style='text-align:center; font-weight:800; margin-top:40px; color:#262730;'>DILUIÇÃO DO INVESTIMENTO ({int(qtd_lojas)} LOJAS)</h3>""", unsafe_allow_html=True)
                m_cols = st.columns(3) if perfil_venda == "Executivo (Rua)" else st.columns([1, 2, 2, 1])[1:3]
                with m_cols[0]: st.markdown(f"""<div style="background-color:#ffffff; border-left: 6px solid #ff6600; padding:15px; border-radius:5px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);"><span style="font-size:0.85rem; font-weight:bold; color:#777;">SETUP POR LOJA</span><br><span style="font-size:1.6rem; font-weight:900; color:#333;">R$ {f_br(t_setup / qtd_lojas)}</span></div>""", unsafe_allow_html=True)
                with m_cols[1]: st.markdown(f"""<div style="background-color:#ffffff; border-left: 6px solid #2e7d32; padding:15px; border-radius:5px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);"><span style="font-size:0.85rem; font-weight:bold; color:#777;">MENSALIDADE POR LOJA</span><br><span style="font-size:1.6rem; font-weight:900; color:#333;">R$ {f_br(t_mensal / qtd_lojas)}</span></div>""", unsafe_allow_html=True)
                if perfil_venda == "Executivo (Rua)":
                    with m_cols[2]: st.markdown(f"""<div style="background-color:#ffffff; border-left: 6px solid #1976d2; padding:15px; border-radius:5px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);"><span style="font-size:0.85rem; font-weight:bold; color:#777;">DESPESAS POR LOJA</span><br><span style="font-size:1.6rem; font-weight:900; color:#333;">R$ {f_br(t_d / qtd_lojas)}</span></div>""", unsafe_allow_html=True)

        # --- BOTÃO EXPORTAÇÃO WEB / DIGITAL (Escondido no Modo Apresentação) ---
        if not modo_apresentacao:
            st.write("---")
            st.markdown("<h3 style='text-align:center; color:#262730;'>Exportação e Formalização</h3>", unsafe_allow_html=True)
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            
            with col_btn2:
                if not st.session_state.in_nome_cliente:
                    st.info("👆 Preencha o campo 'Razão Social / Nome Fantasia' no topo da ecrã para liberar a proposta digital.")
                else:
                    if st.button("🌐 Gerar Proposta Digital (Pronta para PDF)", use_container_width=True):
                        dados_pdf = {
                            'nome_cliente': st.session_state.in_nome_cliente,
                            'cnpj': st.session_state.in_cnpj_cliente,
                            'html_setup': html_setup_digital,
                            'valor_setup': f_br(t_setup),
                            'parcelas': str(parcelas_setup),
                            'html_mensal': html_mensal_digital,
                            'valor_mensal': f_br(t_mensal),
                            'faturamento': faturamento_sistema,
                            'html_despesa': html_desp_digital if html_desp_digital else "<li>Sem despesas</li>",
                            'valor_despesa': f_br(t_d) if 't_d' in locals() else "0,00",
                            'regra_desp': regra_despesas
                        }
                        st.session_state.html_proposta = renderizar_proposta_digital(dados_pdf)
                        st.session_state.show_digital_proposal = True
                        st.rerun()
                        
        # Exibidor da Proposta Digital
        if st.session_state.get('show_digital_proposal', False) and not modo_apresentacao:
            st.markdown("---")
            st.markdown("<h2 style='text-align:center; color:#ff6600;'>📄 Visualização da Proposta Digital</h2>", unsafe_allow_html=True)
            st.info("Clique no botão laranja dentro do quadro abaixo para Imprimir ou Salvar como PDF.")
            components.html(st.session_state.html_proposta, height=1200, scrolling=True)
            
            col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
            if col_f2.button("Fechar Visualização", use_container_width=True):
                st.session_state.show_digital_proposal = False
                st.rerun()

    # TELA 3: CONSULTA DE PRECO 
    elif tela == "Consulta de Preco":
        st.markdown(f"""<h1 class="hero-title">ANÁLISE TÉCNICA</h1>""", unsafe_allow_html=True)
        st.markdown(f"""<div class="mapeamento-container"><h3 style="margin:0; color:#ff6600;">Simulador de Negociação Individual</h3></div>""", unsafe_allow_html=True)
        cb, cd = st.columns([2, 1])
        p_sel = cb.selectbox("Selecione o produto:", sorted(list(full_db.keys())))
        desc_s = cd.number_input("Simular Desconto (%)", 0.0, 30.0, 0.0, 0.5)
        
        v_h_base = servicos_db.get("Implantação e Treinamento", {}).get("valor", 0.0)
        
        if p_sel:
            d = full_db[p_sel]; v_b = d.get('valor', 0.0); v_l = v_b * (1 - (desc_s/100))
            p_id = name_to_id.get(p_sel)
            is_sistema = (d.get('typeproductid') == 604)
            
            t_s = 0.0
            h_s = ""
            
            if p_id in vinculos_db and any(v['tipo'] in ['projeto', 'adesao'] for v in vinculos_db[p_id]):
                for r in vinculos_db[p_id]:
                    if r['tipo'] in ['projeto', 'adesao']:
                        f_nm = id_to_name.get(r['id_filho'])
                        f_val = full_db.get(f_nm, {}).get('valor', 0.0)
                        f_q = r['qtd']
                        t_s += (f_q * f_val)
                        uni = "h" if r['tipo'] == 'projeto' else "un"
                        h_s += f"<li><span>{f_nm}</span><span class='item-detalhe'>{int(f_q)}{uni} x R$ {f_br(f_val)} | Total: R$ {f_br(f_q*f_val)}</span></li>"
            else:
                h_p, v_he, ads = d.get('horas_padrao', 0.0), d.get('valor_hora_implantacao', 0.0), d.get('adesao_vinculada', 0.0)
                rt = v_he if v_he > 0 else v_h_base
                t_s = (h_p * rt) + ads
                if h_p > 0: h_s += f"<li><span>Implantação</span><span class='item-detalhe'>{h_p}h x R$ {f_br(rt)} | Total: R$ {f_br(h_p*rt)}</span></li>"
                if ads > 0: h_s += f"<li><span>Taxa de Adesão</span><span class='item-detalhe'>1 un x R$ {f_br(ads)} | Total: R$ {f_br(ads)}</span></li>"
                
            if is_sistema:
                c1, c2, c3 = st.columns(3)
                with c1: st.markdown(f"""<div class="resumo-card"><span>Investimento de Setup</span><div class="resumo-valor">R$ {f_br(t_s)}</div><div class="resumo-subtitulo">COMPOSIÇÃO</div><ul class="lista-itens">{h_s if h_s else "<li>Isento</li>"}</ul></div>""", unsafe_allow_html=True)
                with c2:
                    html_b = f"""<span style="text-decoration: line-through; color: #777; font-size: 0.9rem;">R$ {f_br(v_b)}</span>""" if desc_s > 0 else ""
                    st.markdown(f"""<div class="resumo-card" style="border-top-color:#2e7d32;"><span>Investimento Mensal</span><div class="resumo-valor" style="color:#2e7d32;">R$ {f_br(v_l)}</div>{html_b}<div class="resumo-subtitulo">DETALHE</div><ul class="lista-itens"><li><span>Desconto Aplicado</span><span class="item-detalhe">{f_pct(desc_s)}%</span></li></ul></div>""", unsafe_allow_html=True)
                with c3:
                    st.markdown(f"""<div class="resumo-card" style="border-top-color:#262730; min-height: auto;"><span>Resumo Anual</span><div style="margin-top:15px;"><p><b>Economia Mensal:</b> R$ {f_br(v_b-v_l)}</p><p><b>Economia Anual:</b> R$ {f_br((v_b-v_l)*12)}</p></div></div>""", unsafe_allow_html=True)
            else:
                c1, c2 = st.columns(2)
                with c1:
                    html_b = f"""<span style="text-decoration: line-through; color: #777; font-size: 0.9rem;">R$ {f_br(v_b)}</span>""" if desc_s > 0 else ""
                    st.markdown(f"""<div class="resumo-card"><span>Setup / Serviço Único</span><div class="resumo-valor">R$ {f_br(v_l)}</div>{html_b}<div class="resumo-subtitulo">DETALHE</div><ul class="lista-itens"><li><span>Desconto Aplicado</span><span class="item-detalhe">{f_pct(desc_s)}%</span></li></ul></div>""", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"""<div class="resumo-card" style="border-top-color:#262730; min-height: auto;"><span>Resumo do Desconto</span><div style="margin-top:15px;"><p><b>Economia Total Gerada:</b> R$ {f_br(v_b-v_l)}</p><p style="color:#777; font-size:0.85rem;">*Este item não possui faturamento recorrente mensal.</p></div></div>""", unsafe_allow_html=True)

# ==========================================
# ROTEADOR DE SEGURANÇA
# ==========================================
if not st.session_state.logged_in:
    tela_login()
else:
    aplicativo_principal()
