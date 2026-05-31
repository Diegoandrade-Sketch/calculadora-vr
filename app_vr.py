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
# CONFIGURAÇÕES INICIAIS E CONTROLO DE ESTADO
# ==========================================
st.set_page_config(page_title="VR Software | Sales Intelligence", layout="wide")

APP_VERSION = "v3.5.0 - CRM Pro & Clean UI"
CACHE_FILE = "cache_vr.json"

# Inicialização de estados persistentes (O "Cofre" do CRM e da Tela)
if 'perma_nome_cliente' not in st.session_state: st.session_state.perma_nome_cliente = ""
if 'perma_cnpj_cliente' not in st.session_state: st.session_state.perma_cnpj_cliente = ""
if 'proposta_carregada_id' not in st.session_state: st.session_state.proposta_carregada_id = None
if 'show_digital_proposal' not in st.session_state: st.session_state.show_digital_proposal = False
if 'menu_nav' not in st.session_state: st.session_state.menu_nav = "Gerador de Proposta"

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
# FUNÇÕES DE FORMATAÇÃO E BLINDAGEM (UX/UI)
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
        with open("logo_vr.png", "rb") as img_file: return base64.b64encode(img_file.read()).decode("utf-8")
    return ""

def atualiza_nome_cliente(): 
    st.session_state.perma_nome_cliente = st.session_state.widget_nome

def atualiza_cnpj_cliente():
    raw = str(st.session_state.widget_cnpj)
    apenas_numeros = re.sub(r'\D', '', raw)[:14]
    if len(apenas_numeros) == 14:
        formatado = f"{apenas_numeros[:2]}.{apenas_numeros[2:5]}.{apenas_numeros[5:8]}/{apenas_numeros[8:12]}-{apenas_numeros[12:]}"
        st.session_state.perma_cnpj_cliente = formatado
    else:
        st.session_state.perma_cnpj_cliente = apenas_numeros

# ==========================================
# MÓDULOS DO CRM (EMPACOTAMENTO JSON)
# ==========================================
def empacotar_simulacao():
    payload = {
        'perma_nome_cliente': st.session_state.perma_nome_cliente,
        'perma_cnpj_cliente': st.session_state.perma_cnpj_cliente,
        'g_desc_mensalidade': st.session_state.g_desc_mensalidade,
        'g_parcelas_setup': st.session_state.g_parcelas_setup,
        'g_faturamento': st.session_state.g_faturamento,
        'g_regra_desp': st.session_state.g_regra_desp,
        'sel_m': st.session_state.sel_m,
        'sel_i': st.session_state.sel_i,
        'sel_d': st.session_state.sel_d,
        'mapeamento': {k: st.session_state[k] for k in st.session_state.keys() if k.startswith('m_')},
        'quantidades': {k: st.session_state[k] for k in st.session_state.keys() if k.startswith('perm_val_')}
    }
    return json.dumps(payload)

def desempacotar_simulacao(json_data, prop_id):
    try:
        # Correção Definitiva do Erro de JSON (Trava de Tipagem)
        dados = json.loads(json_data) if isinstance(json_data, str) else json_data
        
        st.session_state.perma_nome_cliente = dados.get('perma_nome_cliente', '')
        st.session_state.perma_cnpj_cliente = dados.get('perma_cnpj_cliente', '')
        st.session_state.g_desc_mensalidade = float(dados.get('g_desc_mensalidade', 0.0))
        st.session_state.g_parcelas_setup = int(dados.get('g_parcelas_setup', 4))
        st.session_state.g_faturamento = dados.get('g_faturamento', "Na assinatura")
        st.session_state.g_regra_desp = dados.get('g_regra_desp', "Faturamento na assinatura")
        st.session_state.sel_m = dados.get('sel_m', [])
        st.session_state.sel_i = dados.get('sel_i', [])
        st.session_state.sel_d = dados.get('sel_d', [])
        
        for k, v in dados.get('mapeamento', {}).items(): st.session_state[k] = v
        for k, v in dados.get('quantidades', {}).items(): st.session_state[k] = float(v)
        
        st.session_state.proposta_carregada_id = prop_id
        st.session_state.show_digital_proposal = False
        
        # Redirecionamento Automático
        st.session_state.menu_nav = "Gerador de Proposta"
    except Exception as e:
        st.error(f"Erro ao ler histórico: {e}")

# ==========================================
# DATA LAYER (CARREGAMENTO DA BASE DE DADOS)
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
# ESTADO GLOBAL (Calculadora e Utilizador)
# ==========================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_role' not in st.session_state: st.session_state.user_role = None
if 'primeiro_acesso' not in st.session_state: st.session_state.primeiro_acesso = False
if 'user_email' not in st.session_state: st.session_state.user_email = ""
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'unidade_nome' not in st.session_state: st.session_state.unidade_nome = "VR Software"

init_state = {
    'm_combo': "Montar Manualmente", 'm_pdv_conv': 0.0, 'm_pdv_touch': 0.0, 'm_pdv_self': 0.0, 'm_semanas': 0.0, 'm_mobile': 0.0,
    'm_tef': "Nao utiliza", 'm_migracao': False, 'm_ecommerce': False, 'm_app': False, 'm_connect': False,
    'm_erp_pro': False, 'm_xml': False, 'm_escopo': False, 'm_controller': False, 'm_cartaz': False, 'm_masterfisco': False, 'm_backup': False,
    'auto_added': set(), 'sel_m': [], 'sel_i': [], 'sel_d': [], 'ui_sel_m': [], 'ui_sel_i': [], 'ui_sel_d': [],
    'g_desc_mensalidade': 0.0, 'g_parcelas_setup': 4, 'g_faturamento': "Na assinatura", 'g_regra_desp': "Faturamento na assinatura"
}

for k, v in init_state.items():
    if k not in st.session_state: st.session_state[k] = v

for nome in full_db.keys():
    if f"perm_val_{nome}" not in st.session_state: st.session_state[f"perm_val_{nome}"] = 0.0

# ==========================================
# BLOCO 1: LOGIN (Visual Limpo e Profissional)
# ==========================================
def tela_login():
    st.markdown("""<style>.stApp { background: #f4f6f9; } div[data-testid="stForm"] { background-color: #ffffff; border-radius: 8px; padding: 40px; border: 1px solid #e0e0e0; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05); } div[data-testid="stForm"] button { background: #262730; color: white; border: none; border-radius: 4px; font-weight: 600; padding: 0.5rem 1rem; margin-top: 15px; } div[data-testid="stForm"] button:hover { background: #444; color: white; } div[data-testid="stTextInput"] input { border-radius: 4px; border: 1px solid #ccc; padding: 10px; }</style>""", unsafe_allow_html=True)
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
                            engine = create_engine(CONN_STR)
                            with engine.begin() as conn: conn.execute(text("UPDATE usuarios SET senha = :s, primeiro_acesso = FALSE WHERE email = :e"), {"s": nova_senha, "e": st.session_state.user_email})
                            st.session_state.primeiro_acesso = False; st.session_state.logged_in = True; st.rerun()
                        except Exception: st.error("Erro de comunicação com a base de dados.")
                    else: st.error("As senhas informadas não conferem.")
            else:
                email = st.text_input("E-mail corporativo")
                senha = st.text_input("Senha", type="password")
                if st.form_submit_button("Autenticar", use_container_width=True):
                    if email == "admin" and senha == "333666":
                        st.session_state.logged_in = True; st.session_state.user_role = "admin"; st.session_state.user_name = "Administrador Master"; st.session_state.unidade_nome = "Matriz"; st.rerun()
                    elif not CONN_STR: st.error("Conexão com o servidor falhou.")
                    else:
                        try:
                            engine = create_engine(CONN_STR)
                            with engine.connect() as conn:
                                resultado = pd.read_sql(text("SELECT u.*, un.nome_fantasia as nome_unidade FROM usuarios u LEFT JOIN unidades un ON u.id_unidade = un.id WHERE u.email = :e AND u.ativo = TRUE"), conn, params={"e": email})
                            if not resultado.empty:
                                user = resultado.iloc[0]
                                if user['senha'] == senha or user['primeiro_acesso']:
                                    st.session_state.user_email = email; st.session_state.user_role = user['nivel_acesso']; st.session_state.user_name = user['nome']
                                    st.session_state.unidade_nome = user['nome_unidade'] if pd.notna(user['nome_unidade']) else "VR Software"
                                    if user['primeiro_acesso']: st.session_state.primeiro_acesso = True; st.rerun()
                                    else: st.session_state.logged_in = True; st.rerun()
                                else: st.error("Senha incorreta.")
                            else: st.error("Utilizador não cadastrado ou bloqueado.")
                        except Exception: st.error("Ocorreu um erro ao validar os dados.")

# ==========================================
# BLOCO 2: RENDERIZADOR HTML (PROPOSTA DIGITAL)
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
            .container {{ max-width: 900px; margin: 0 auto; background: #fff; box-shadow: 0 10px 30px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden; }}
            @media print {{ body {{ background: #fff; padding: 0; }} .container {{ box-shadow: none; max-width: 100%; border-radius: 0; }} .no-print {{ display: none !important; }} .page-break {{ page-break-before: always; }} }}
            .print-btn {{ background: #262730; color: white; border: none; padding: 12px 24px; font-size: 16px; font-weight: bold; border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center; margin: 20px auto; transition: 0.3s; }}
            .cover {{ background: #262730; color: white; padding: 60px 40px; position: relative; border-left: 10px solid #ff6600; }}
            .cover h1 {{ font-size: 48px; margin: 0; font-weight: 900; letter-spacing: -1px; }}
            .cover h2 {{ color: #ff6600; font-weight: 400; font-size: 24px; margin-top: 10px; }}
            .cover-details {{ margin-top: 60px; display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
            .detail-label {{ font-size: 12px; color: #aaa; text-transform: uppercase; margin-bottom: 5px; }}
            .detail-value {{ font-size: 18px; font-weight: bold; color: #fff; }}
            .detail-sub {{ font-size: 14px; color: #ccc; }}
            .content {{ padding: 40px; }}
            .header-content {{ border-bottom: 2px solid #262730; padding-bottom: 10px; margin-bottom: 30px; }}
            .header-content h3 {{ margin: 0; font-size: 22px; color: #262730; }}
            .cards {{ display: flex; flex-direction: column; gap: 25px; }}
            .card {{ border: 1px solid #eee; border-radius: 6px; padding: 25px; background: #fafafa; }}
            .card.setup {{ border-top: 4px solid #ff6600; }}
            .card.mensal {{ border-top: 4px solid #2e7d32; }}
            .card.despesa {{ border-top: 4px solid #1976d2; }}
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
    # CSS Corporativo Clean (Fundo branco/cinza, sem gradientes intensos)
    st.markdown("""
        <style>
        .stApp { background-color: #f4f6f9; }
        .hero-title { color: #262730; font-size: 2.5rem; font-weight: 800; margin: 0; line-height: 1; text-transform: uppercase; letter-spacing: -1px; }
        .mapeamento-container { background-color: #ffffff; border-left: 6px solid #262730; padding: 20px; border-radius: 4px; margin-bottom: 15px; border: 1px solid #e0e0e0; box-shadow: 0 2px 5px rgba(0,0,0,0.02); }
        .cliente-container { background-color: #ffffff; border-left: 6px solid #262730; padding: 20px; border-radius: 4px; margin-bottom: 15px; border: 1px solid #e0e0e0; box-shadow: 0 2px 5px rgba(0,0,0,0.02); }
        .resumo-card { background-color: #ffffff; border: 1px solid #e0e0e0; border-top: 4px solid #262730; padding: 20px; border-radius: 4px; min-height: 450px; box-shadow: 0 4px 10px rgba(0,0,0,0.03); display: flex; flex-direction: column; }
        .resumo-valor { color: #262730; font-size: 2.2rem; font-weight: 800; margin-bottom: 5px; }
        .item-detalhe { color: #555; font-size: 0.82rem; font-weight: 600; background-color: #f9f9f9; padding: 2px 8px; border-radius: 4px; border: 1px solid #eee; white-space: nowrap; }
        .section-header { background-color: #262730; padding: 8px 15px; border-radius: 4px; margin-bottom: 15px; margin-top: 20px; }
        .section-title { color: #ffffff; font-size: 1.05rem; font-weight: bold; margin: 0; }
        .lista-itens { list-style-type: none; padding-left: 0; margin-top: 10px; flex-grow: 1; }
        .lista-itens li { padding: 8px 0; border-bottom: 1px dashed #e0e0e0; display: flex; justify-content: space-between; align-items: center; gap: 15px; }
        .lista-itens li span:first-child { font-weight: 600; font-size: 0.88rem; color: #444; }
        .item-incluso { padding-left: 20px !important; color: #888; font-size: 0.85rem; font-style: italic; border-bottom: none !important; }
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
                        if f_nome: novos_auto.add(f_nome); st.session_state[f"perm_val_{f_nome}"] = float(r['qtd'])

        lista_servicos_atual = list(st.session_state.ui_sel_i)
        for item in st.session_state.auto_added - novos_auto:
            if item in lista_servicos_atual:
                lista_servicos_atual.remove(item); st.session_state[f"perm_val_{item}"] = 0.0
        for item in novos_auto:
            if item not in lista_servicos_atual: lista_servicos_atual.append(item)
        st.session_state.auto_added = novos_auto; st.session_state.ui_sel_i = lista_servicos_atual; st.session_state.sel_i = lista_servicos_atual

    def atualiza_sistemas_ui(): st.session_state.sel_m = st.session_state.ui_sel_m; processar_regras_colaterais()
    def atualiza_servicos_ui(): st.session_state.sel_i = st.session_state.ui_sel_i
    def atualiza_despesas_ui(): st.session_state.sel_d = st.session_state.ui_sel_d

    def limpar_tudo():
        for k, v in init_state.items(): st.session_state[k] = v if not isinstance(v, list) else []
        for nome in full_db.keys(): st.session_state[f"perm_val_{nome}"] = 0.0
        st.session_state.perma_nome_cliente = ""; st.session_state.perma_cnpj_cliente = ""; st.session_state.proposta_carregada_id = None
        if 'widget_nome' in st.session_state: st.session_state.widget_nome = ""
        if 'widget_cnpj' in st.session_state: st.session_state.widget_cnpj = ""
        st.session_state.show_digital_proposal = False

    def sync_combo():
        if st.session_state.tmp_combo == "Padrão Pequeno Porte":
            st.session_state.m_pdv_touch = 0.0; st.session_state.m_pdv_self = 0.0; st.session_state.m_ecommerce = False; st.session_state.m_app = False; st.session_state.m_connect = False; st.session_state.m_controller = False; st.session_state.m_cartaz = False; st.session_state.m_masterfisco = False; st.session_state.m_backup = False; st.session_state.m_semanas = 0.0
            st.session_state.m_erp_pro = True; st.session_state.m_pdv_conv = 3.0; st.session_state.m_xml = True; st.session_state.m_mobile = 1.0; st.session_state.m_tef = "SiTef Express"; st.session_state.m_migracao = True; st.session_state.m_escopo = True

    # ==========================================
    # SIDEBAR (Sincronizada sem cliques fantasmas)
    # ==========================================
    with st.sidebar:
        if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=180)
        st.markdown(f"<div style='background-color:#fff; border: 1px solid #e0e0e0; padding:10px; border-radius:4px; margin-bottom:15px; border-left:4px solid #262730;'><span style='font-weight:bold; color:#333;'>{st.session_state.user_name}</span></div>", unsafe_allow_html=True)
        
        abas = ["Gerador de Proposta", "Minhas Propostas", "Consulta de Preço"]
        if st.session_state.user_role == "admin" and not st.toggle("Simular Visão Vendedor"): abas.append("Painel Admin")
        
        # O core da correção do duplo clique (ligado nativamente)
        tela = st.radio("Navegação:", abas, key="menu_nav")

        if tela == "Gerador de Proposta":
            st.write("---")
            mapeamento_ativo = st.toggle("Mapeamento Inteligente", value=False)
            modo_apresentacao = st.toggle("Modo Apresentação (Ocultar Menus)")
            
            perfil_venda = st.selectbox("Perfil do Cliente", ["Com Despesas", "Sem Despesas"])
            
            st.session_state.g_desc_mensalidade = st.number_input("Desconto Mensalidade (%)", 0.0, 30.0, st.session_state.g_desc_mensalidade, 0.5)
            exibir_detalhe_desc = st.toggle("Exibir Desconto na Tela", value=True)
            exibir_media_loja = st.toggle("Exibir Média por Loja", value=False)
            st.session_state.g_faturamento = st.selectbox("Início Mensalidade", ["Na assinatura", "30 dias", "60 dias", "Após implantação"], index=["Na assinatura", "30 dias", "60 dias", "Após implantação"].index(st.session_state.g_faturamento))
            st.session_state.g_parcelas_setup = st.selectbox("Parcelas Setup", [1, 2, 3, 4, 5, 6, 10, 12], index=[1, 2, 3, 4, 5, 6, 10, 12].index(st.session_state.g_parcelas_setup))
            st.session_state.g_regra_desp = st.selectbox("Faturamento Despesas", ["Faturamento na assinatura", "Faturamento pós Implantação"], index=["Faturamento na assinatura", "Faturamento pós Implantação"].index(st.session_state.g_regra_desp))
        
        st.write("---")
        if st.button("Sair da Sessão", use_container_width=True): st.session_state.clear(); st.rerun()
        st.markdown(f"""<hr><div style="font-size:0.8rem; color:{db_cor};">{db_status}</div><div style="font-size:0.7rem; color:#888;">{APP_VERSION}</div>""", unsafe_allow_html=True)

    # ==========================================
    # TELA 1: PAINEL ADMIN
    # ==========================================
    if tela == "Painel Admin":
        st.markdown("""<h1 class="hero-title">BACKOFFICE</h1>""", unsafe_allow_html=True)
        t_vinc, t_unid, t_user, t_sql, t_cat = st.tabs(["Vínculos Relacionais", "Unidades", "Usuários", "Terminal SQL", "Catálogo"])
        
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
                        with engine.begin() as conn: conn.execute(text("INSERT INTO unidades (nome_fantasia, cnpj, cidade, logradouro) VALUES (:n, :c, :ci, :e)"), {"n": n_fantasia, "c": v_cnpj, "ci": v_cidade, "e": v_end})
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
                            with engine.begin() as conn: conn.execute(text("INSERT INTO usuarios (nome, email, nivel_acesso, id_unidade, senha, primeiro_acesso) VALUES (:n, :e, :r, :id_u, '123456', TRUE)"), {"n": u_nome, "e": u_email, "r": u_role, "id_u": unid_dict[u_unid]})
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
                        with engine.begin() as conn: conn.execute(text("INSERT INTO product_vinculo (id_produto_pai, id_produto_filho, tipo_vinculo, quantidade_padrao) VALUES (:p, :f, :t, :q)"), {"p": name_to_id[pai], "f": name_to_id[fil], "t": tip, "q": qtd})
                        st.success("Vínculo Criado com Sucesso!"); st.cache_data.clear()
                    except Exception as e: st.error(e)
            st.dataframe(df_vinc, use_container_width=True)
            
        with t_sql:
            st.warning("Terminal Administrativo Restrito")
            query = st.text_area("Digite o comando SQL:")
            if st.button("Executar SQL"):
                if any(p in query.lower() for p in
