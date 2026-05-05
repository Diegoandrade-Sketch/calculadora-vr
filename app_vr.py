import streamlit as st
import pandas as pd

# 1. Configuração da Página
st.set_page_config(page_title="VR Software | Configurador de Propostas", layout="wide")

# 2. Estilização Profissional (Laranja e Branco)
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    div[data-testid="stMetricValue"] { color: #ff6600; font-weight: 700; }
    [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #dee2e6; }
    .stButton>button { 
        background-color: #ff6600; color: white; border-radius: 4px; 
        font-weight: 600; border: none; width: 100%;
    }
    .stMetric { 
        background-color: #ffffff; padding: 20px; border-radius: 4px; 
        box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 5px solid #ff6600;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Inicialização do "Carrinho" na memória da sessão
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []

def adicionar_item(nome, preco, qtd):
    st.session_state.carrinho.append({
        "Produto": nome, 
        "Preço Unit.": preco, 
        "Quantidade": qtd, 
        "Subtotal": preco * qtd
    })

# 4. Cabeçalho
st.image("https://vrsoft.com.br/wp-content/uploads/2022/07/Logo-VR-Software.png", width=200)
st.title("Configurador de Propostas Comerciais")
st.markdown("---")

# 5. Barra Lateral: Seleção de Itens
st.sidebar.subheader("Seleção de Itens")

# Tabela de preços baseada na sua imagem/planilha
tabela_precos = {
    "VR ERP PRO": 1285.71,
    "PDV Convencional": 185.71,
    "PDV Touchscreen": 185.71,
    "PDV Self-Checkout": 290.44,
    "SiTef Express até 3 PDVs": 357.14,
    "SiTef Express até 6 PDVs": 428.57,
    "SiTef Express até 8 PDVs": 500.00,
    "SiTef Express a partir de 9 PDVs": 571.43,
    "Migração Banco de Dados (Hora)": 201.30,
    "Configuração Servidor / PDV Linux (Hora)": 201.30,
    "Implantação e Treinamento (Hora)": 201.30,
}

produto_sel = st.sidebar.selectbox("Escolha o Produto ou Serviço", list(tabela_precos.keys()))
qtd_sel = st.sidebar.number_input("Quantidade / Horas", min_value=1, value=1)

if st.sidebar.button("Adicionar à Proposta"):
    adicionar_item(produto_sel, tabela_precos[produto_sel], qtd_sel)
    st.sidebar.success("Item adicionado com sucesso.")

if st.sidebar.button("Limpar Proposta"):
    st.session_state.carrinho = []
    st.rerun()

# 6. Área Central: Visualização e Fechamento
if st.session_state.carrinho:
    df_carrinho = pd.DataFrame(st.session_state.carrinho)
    st.subheader("Itens Selecionados")
    st.table(df_carrinho.style.format({"Preço Unit.": "R$ {:.2f}", "Subtotal": "R$ {:.2f}"}))

    subtotal_geral = df_carrinho["Subtotal"].sum()

    st.markdown("---")
    col_desc, col_total = st.columns([1, 2])
    
    with col_desc:
        st.subheader("Negociação")
        # Campo de digitação conforme solicitado
        percentual_desconto = st.number_input("Percentual de Desconto (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
        
        if percentual_desconto > 15:
            st.error("Alerta: Percentual acima da alçada comercial.")
        
        valor_desconto = (subtotal_geral * percentual_desconto) / 100
        total_final = subtotal_geral - valor_desconto

    with col_total:
        st.write("") # Espaçamento
        st.markdown(f"""
            <div style="background-color: #ff6600; padding: 25px; border-radius: 4px; text-align: center;">
                <p style="color: white; margin: 0; font-size: 1.1em; font-weight: 300;">Investimento Final</p>
                <h1 style="color: white; margin: 0; font-size: 2.5em;">R$ {total_final:,.2f}</h1>
                <p style="color: white; margin: 0; font-size: 0.9em;">Desconto: R$ {valor_desconto:,.2f} ({percentual_desconto}%)</p>
            </div>
        """, unsafe_allow_html=True)

    # 7. Resumo para Compartilhamento
    st.markdown("---")
    if st.button("Gerar Sumário para Compartilhamento"):
        itens_resumo = ""
        for item in st.session_state.carrinho:
            itens_resumo += f"- {item['Produto']} (x{item['Quantidade']}): R$ {item['Subtotal']:,.2f}\n"

        resumo_final = f"""
PROPOSTA COMERCIAL - VR SOFTWARE 2026

Itens da Proposta:
{itens_resumo}
Condições Financeiras:
- Valor Bruto: R$ {subtotal_geral:,.2f}
- Desconto Aplicado: {percentual_desconto}%
- Investimento Final: R$ {total_final:,.2f}
        """
        st.code(resumo_final, language="text")

else:
    st.info("Utilize o menu lateral para selecionar os itens e montar a proposta.")
