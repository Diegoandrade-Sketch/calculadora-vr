import streamlit as st
import pandas as pd
import urllib.parse
import os

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="VR Software | Proposta Comercial", layout="wide", initial_sidebar_state="expanded")

# 2. ESTILIZAÇÃO CSS (Ajustada para o visual da imagem sem quebrar funcionalidades)
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #ffffff 0%, #fff5ed 100%); }
    
    /* Cards de Resumo */
    .resumo-card {
        background-color: #ffffff; border: 1px solid #e0e0e0; border-top: 8px solid #ff6600;
        padding: 25px; border-radius: 12px; min-height: 520px; box-shadow: 0 10px 30px rgba(0,0,0,0.05);
    }
    .resumo-label { color: #888; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; display: block; }
    .resumo-valor { color: #ff6600; font-size: 3rem; font-weight: 900; margin-top: 5px; margin-bottom: 5px; line-height: 1; }
    
    .resumo-subtitulo {
        font-size: 0.95rem; color: #222; font-weight: 800; margin-top: 25px;
        margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 8px;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    
    /* Lista Alinhada conforme a imagem */
    .lista-itens { list-style: none; padding: 0; margin: 0; }
    .lista-itens li { 
        display: flex; 
        justify-content: space-between; 
        align-items: center;
        padding: 12px 0; 
        border-bottom: 1px dashed #eee;
    }
    .item-nome { color: #333; font-size: 0.95rem; font-weight: 700; flex: 1; }
    .item-detalhe { color: #000; font-size: 0.95rem; font-weight: 800; text-align: right; }

    /* Faixa de Alerta da Imagem */
    .alerta-despesa {
        font-size: 0.9rem; color: #d32f2f; font-weight: 700; 
        background: #fff0f0; padding: 6px 12px; border-radius: 4px;
        display: inline-block; margin-top: 5px;
    }
    
    /* Botão WhatsApp */
    .btn-whatsapp {
        background-color: #25d366; color: white !important; padding: 15px 30px;
        text-decoration: none; border-radius: 8px; font-weight: bold;
        display: inline-flex; align-items: center; gap: 10px; margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. BANCO DE DADOS E VARIÁVEIS
itens_imp = {
    "Migração Banco de Dados": 201.30, 
    "Definição de Escopo": 201.30, 
    "Configuração Servidor / PDV Linux": 201.30, 
    "Implantação e Treinamento": 201.30
}
itens_mensal = {
    "VR ERP PRO": 1285.71, "VR PDV Convencional": 185.71, "PDV Touchscreen": 185.71, 
    "PDV Selfcheckout": 290.44, "SiTef Express": 357.14, "VR TEF": 417.04, 
    "Gerenciador XML": 163.84, "VR Mobile": 193.63
}
itens_desp = {"Alimentação": 49.00, "Hospedagem": 195.00, "Deslocamento (KM)": 2.12}

# 4. SIDEBAR (CONTROLES)
with st.sidebar:
    st.title("⚙️ Painel de Controle")
    modo_edicao = st.checkbox("Habilitar Edição de Valores", value=True)
    st.markdown("---")
    desc = st.slider("Desconto Mensal (%)", 0.0, 50.0, 0.0)
    parcelas = st.number_input("Parcelas Setup", 1, 12, 4)
    cliente = st.text_input("Nome do Cliente", "Cliente Exemplo")

# 5. LÓGICA DE SELEÇÃO
if modo_edicao:
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.subheader("🛠️ Implantação")
        sel_imp = st.multiselect("Itens", list(itens_imp.keys()), default=list(itens_imp.keys()))
        dados_imp = []
        for i in sel_imp:
            h = st.number_input(f"Horas: {i}", 1, 200, 120 if "Treinamento" in i else 12)
            dados_imp.append({"item": i, "qtd": h, "valor": itens_imp[i], "total": h * itens_imp[i]})
            
    with col_b:
        st.subheader("💻 Mensalidade")
        sel_men = st.multiselect("Produtos", list(itens_mensal.keys()), default=["VR ERP PRO"])
        dados_men = []
        for i in sel_men:
            q = st.number_input(f"Qtd: {i}", 1, 100, 1)
            dados_men.append({"item": i, "qtd": q, "valor": itens_mensal[i], "total": q * itens_mensal[i]})
            
    with col_c:
        st.subheader("🚗 Despesas")
        dados_desp = []
        for d, v in itens_desp.items():
            qd = st.number_input(f"Qtd {d}", 0, 1000, 0)
            if qd > 0:
                dados_desp.append({"item": d, "qtd": qd, "valor": v, "total": qd * v})
    
    st.session_state['proposta'] = {'imp': dados_imp, 'men': dados_men, 'desp': dados_desp}

# Recuperação de dados
p = st.session_state.get('proposta', {'imp':[], 'men':[], 'desp':[]})
total_imp = sum(item['total'] for item in p['imp'])
total_men_bruto = sum(item['total'] for item in p['men'])
total_men_liq = total_men_bruto * (1 - (desc/100))
total_desp = sum(item['total'] for item in p['desp'])

# 6. EXIBIÇÃO DA PROPOSTA (IGUAL À IMAGEM)
st.markdown("<h1 style='text-align: center; color: #333; font-weight: 800;'>DETALHAMENTO DA PROPOSTA</h1>", unsafe_allow_html=True)

res_col1, res_col2, res_col3 = st.columns(3)

with res_col1:
    html_itens = "".join([f"<li><span class='item-nome'>{i['item']}</span><span class='item-detalhe'>{i['qtd']}h x R$ {i['valor']:,.2f}</span></li>" for i in p['imp']])
    st.markdown(f"""
        <div class="resumo-card">
            <span class="resumo-label">Investimento Setup</span>
            <div class="resumo-valor">R$ {total_imp:,.2f}</div>
            <div style="font-size: 1.2rem; font-weight: 800; color: #333;">{parcelas}x de R$ {total_imp/parcelas:,.2f}</div>
            <div class="resumo-subtitulo">SERVIÇOS DE IMPLANTAÇÃO</div>
            <ul class="lista-itens">{html_itens}</ul>
        </div>
    """, unsafe_allow_html=True)

with res_col2:
    html_itens = "".join([f"<li><span class='item-nome'>{i['item']}</span><span class='item-detalhe'>{i['qtd']} Lic. x R$ {i['valor']:,.2f}</span></li>" for i in p['men']])
    st.markdown(f"""
        <div class="resumo-card" style="border-top-color: #2e7d32;">
            <span class="resumo-label">Investimento Mensal</span>
            <div class="resumo-valor" style="color: #2e7d32;">R$ {total_men_liq:,.2f}</div>
            <div style="font-size: 1rem; color: #2e7d32; font-weight: 700;">Desconto aplicado: {desc}%</div>
            <div class="resumo-subtitulo">SISTEMAS E LICENÇAS</div>
            <ul class="lista-itens">{html_itens}</ul>
        </div>
    """, unsafe_allow_html=True)

with res_col3:
    html_itens = "".join([f"<li><span class='item-nome'>{i['item']}</span><span class='item-detalhe'>{i['qtd']} un. x R$ {i['valor']:,.2f}</span></li>" for i in p['desp']])
    st.markdown(f"""
        <div class="resumo-card" style="border-top-color: #1976d2;">
            <span class="resumo-label">Previsão de Despesas</span>
            <div class="resumo-valor" style="color: #1976d2;">R$ {total_desp:,.2f}</div>
            <div class="alerta-despesa">Faturadas ao término da implantação</div>
            <div class="resumo-subtitulo">DETALHAMENTO LOGÍSTICO</div>
            <ul class="lista-itens">{html_itens if html_itens else "<li style='color:#999'>Nenhuma despesa selecionada</li>"}</ul>
        </div>
    """, unsafe_allow_html=True)

# 7. BOTÃO WHATSAPP (RESTAURADO)
msg = f"Olá {cliente}, segue resumo da proposta:\n- Setup: R$ {total_imp:,.2f}\n- Mensal: R$ {total_men_liq:,.2f}"
msg_url = urllib.parse.quote(msg)
link_wa = f"https://wa.me/5581999999999?text={msg_url}"

st.markdown(f"""
    <div style="text-align: center; margin-top: 40px;">
        <a href="{link_wa}" target="_blank" class="btn-whatsapp">
            <span>Enviar Proposta via WhatsApp</span>
        </a>
    </div>
""", unsafe_allow_html=True)
