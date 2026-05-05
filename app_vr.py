import streamlit as st
import pandas as pd
import os

# 1. Configuracao da Pagina
st.set_page_config(page_title="VR Software | Proposta Comercial", layout="wide")

# 2. Estilizacao CSS
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #ffffff 0%, #fff5ed 100%); }
    .hero-title { color: #262730; font-size: 5.5rem; font-weight: 900; margin: 0; line-height: 1; text-transform: uppercase; letter-spacing: -3px; }
    
    .resumo-card {
        background-color: #ffffff; border: 1px solid #f0f0f0; border-top: 8px solid #ff6600;
        padding: 25px; border-radius: 8px; min-height: 400px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.1); 
    }
    
    .resumo-valor { color: #ff6600; font-size: 2.5rem; font-weight: 900; margin-bottom: 5px; }
    .resumo-label { color: #888; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; display: block; }
    
    .roi-interno-box {
        background-color: #f8f9fa; border-left: 5px solid #262730;
        padding: 20px; margin-top: 15px; border-radius: 4px;
    }
    .roi-metrica { display: flex; justify-content: space-between; margin-bottom: 8px; border-bottom: 1px solid #eee; padding-bottom: 4px; }
    .roi-label { font-weight: bold; color: #555; font-size: 0.9rem; }
    .roi-num { font-weight: 800; color: #262730; }
    
    .section-header {
        background: linear-gradient(90deg, #ff6600 0%, #ff944d 100%);
        padding: 8px 15px; border-radius: 5px; margin-bottom: 15px;
    }
    .section-title { color: #ffffff; font-size: 1.1rem; font-weight: bold; margin: 0; }
    </style>
    """, unsafe_allow_html=True)

# 3. Base de Dados com Metricas de ROI Interno (VR Software)
# Custos estimados para calculo de breakeven (CAC + Implantacao)
precos_tabela = {
    "VR ERP PRO": {"setup": 2415.60, "mensal": 1285.71, "cac_estimado": 3000.00, "margem": "Alta", "complexidade": "Alta"},
    "VR PDV Convencional": {"setup": 201.30, "mensal": 185.71, "cac_estimado": 400.00, "margem": "Media", "complexidade": "Media"},
    "PDV Touchscreen": {"setup": 201.30, "mensal": 185.71, "cac_estimado": 400.00, "margem": "Media", "complexidade": "Media"},
    "PDV Selfcheckout": {"setup": 500.00, "mensal": 290.44, "cac_estimado": 800.00, "margem": "Alta", "complexidade": "Alta"},
    "SiTef Express": {"setup": 0.00, "mensal": 357.14, "cac_estimado": 100.00, "margem": "Altissima", "complexidade": "Baixa"},
    "VR TEF": {"setup": 0.00, "mensal": 417.04, "cac_estimado": 150.00, "margem": "Altissima", "complexidade": "Baixa"},
    "Gerenciador XML": {"setup": 0.00, "mensal": 163.84, "cac_estimado": 50.00, "margem": "Alta", "complexidade": "Baixa"},
    "VR Mobile": {"setup": 201.30, "mensal": 193.63, "cac_estimado": 300.00, "margem": "Media", "complexidade": "Media"},
    "Migração Banco de Dados": {"setup": 201.30, "mensal": 0.00, "cac_estimado": 200.00, "margem": "Baixa", "complexidade": "Alta"},
    "Definição de Escopo": {"setup": 201.30, "mensal": 0.00, "cac_estimado": 100.00, "margem": "Media", "complexidade": "Media"},
    "Configuração Servidor / PDV Linux": {"setup": 201.30, "mensal": 0.00, "cac_estimado": 150.00, "margem": "Media", "complexidade": "Media"},
    "Implantação e Treinamento": {"setup": 201.30, "mensal": 0.00, "cac_estimado": 1000.00, "margem": "Baixa", "complexidade": "Alta"}
}

# --- 4. MENU LATERAL ---
with st.sidebar:
    if os.path.exists("logo_vr.png"): st.image("logo_vr.png", width=200)
    tela = st.radio("Navegação:", ["Consulta de Preços", "Gerador de Proposta"])
    st.write("---")

# --- 5. TELA DE CONSULTA (FOCO NO ROI INTERNO VR) ---
if tela == "Consulta de Preços":
    st.markdown('<h1 class="hero-title">ANÁLISE DE PRODUTO</h1>', unsafe_allow_html=True)
    
    prod_sel = st.selectbox("Selecione o Produto para Análise Técnica:", list(precos_tabela.keys()))
    d = precos_tabela[prod_sel]
    
    # Calculos de ROI Interno
    receita_24m = (d["mensal"] * 24) + d["setup"]
    investimento_inicial = d["cac_estimado"]
    
    # Breakeven: em quanto tempo o cliente se paga
    if d["mensal"] > 0:
        meses_payback = (investimento_inicial - d["setup"]) / d["mensal"]
        meses_payback = max(0, round(meses_payback, 1))
    else:
        meses_payback = "N/A (Serviço Avulso)"

    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown(f'''
            <div class="resumo-card">
                <span class="resumo-label">Preço de Tabela (Venda)</span>
                <div class="resumo-valor">R$ {d["mensal"]:,.2f} <small style="font-size:1rem; color:#888;">/mês</small></div>
                <div style="font-weight:bold; color:#555;">Setup: R$ {d["setup"]:,.2f}</div>
                <br>
                <div class="section-header"><span class="section-title">ROI ESTRATÉGICO (VR SOFTWARE)</span></div>
                <div class="roi-interno-box">
                    <div class="roi-metrica">
                        <span class="roi-label">LTV Bruto (24 Meses)</span>
                        <span class="roi-num">R$ {receita_24m:,.2f}</span>
                    </div>
                    <div class="roi-metrica">
                        <span class="roi-label">Ponto de Equilíbrio (Breakeven)</span>
                        <span class="roi-num">{meses_payback} meses</span>
                    </div>
                    <div class="roi-metrica">
                        <span class="roi-label">Margem de Contribuição</span>
                        <span class="roi-num">{d["margem"]}</span>
                    </div>
                    <div class="roi-metrica">
                        <span class="roi-label">Complexidade Técnica</span>
                        <span class="roi-num">{d["complexidade"]}</span>
                    </div>
                </div>
            </div>
        ''', unsafe_allow_html=True)
        
    with c2:
        st.markdown('<div class="section-header"><span class="section-title">NOTAS DE ENGENHARIA DE VALOR</span></div>', unsafe_allow_html=True)
        if d["mensal"] > 500:
            st.info("Produto de Alta Recorrência: Foco total na retenção (Churn Zero). O custo de implementação é diluído no primeiro semestre.")
        if d["complexidade"] == "Alta":
            st.warning("Atenção: Exige Senioridade na Implantação. O ROI interno depende da eficiência das horas técnicas.")
        if d["margem"] == "Altissima":
            st.success("Produto de Escalabilidade: Baixo custo de manutenção e alta margem líquida em 24 meses.")
        
        st.write("---")
        st.write("**Resumo do Ciclo de Vida do Contrato:**")
        st.write(f"Ao final de 2 anos, este módulo terá contribuído com R$ {receita_24m:,.2f} para o faturamento da unidade, considerando o cumprimento integral do contrato.")

# O restante do codigo (Gerador de Proposta) permanece o mesmo das versoes anteriores para manter a funcionalidade.
