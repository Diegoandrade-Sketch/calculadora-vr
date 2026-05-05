import streamlit as st
import pandas as pd

# Configuração da Página
st.set_page_config(page_title="VR Software | Configurador de Propostas", layout="wide")

# Estilização Profissional
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

# Inicialização do "Carrinho" na memória da sessão
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []

def adicionar_item(nome, preco, qtd):
    st.session_state.carrinho.append({"Produto": nome, "Preço Unit.": preco, "Qtd": qtd, "Subtotal": preco * qtd})

# Cabeçalho
st.image("https://vrsoft.com.br/wp-content/uploads/2022/07/Logo-VR-Software.png", width=200)
st.title("Configurador de Propostas Comerciais")
st.markdown("---")

# --- Sidebar: Adição de Produtos ---
st.sidebar.subheader("Seleção de Produtos")
tabela_precos = {
    "VR ERP PRO (Mensalidade Base)": 1090.91,
    "Licença PDV Comum": 165.00,
    "Licença PDV Touchscreen": 168.83,
    "Licença PDV Self-Checkout": 201.30,
    "VR Gerenciador XML": 0.00,
    "VR Mobile": 0.00,
    "Sintef Express (TEF)": 0.00 # Calculado automaticamente depois ou fixo
}

produto_sel = st.sidebar.selectbox("Selecione o Produto", list(tabela_precos.keys()))
qtd_sel = st.sidebar.number_input("Quantidade", min_value=1, value=1)

if st.sidebar.button("Adicionar à Proposta"):
    adicionar_item(produto_sel, tabela_precos[produto_sel], qtd_sel)
    st.sidebar.success("Item adicionado!")

if st.sidebar.button("Limpar Proposta"):
    st.session_state.carrinho = []
    st.rerun()

# --- Área Central: Visualização da Proposta ---
if st.session_state.carrinho:
    df_carrinho = pd.DataFrame(st.session_state.carrinho)
    st.subheader("Itens da Proposta")
    st.table(df_carrinho.style.format({"Preço Unit.": "R$ {:.2f}", "Subtotal": "R$ {:.2f}"}))

    # Cálculo do Total
    subtotal_geral = df_carrinho["Subtotal"].sum()

    st.markdown("---")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Negociação")
        percentual_desconto = st.number_input("Percentual de Desconto (%)", min_value=0.0, max_value=30.0, value=0.0, step=0.5)
        
        if percentual_desconto > 15:
            st.error("Atenção: Desconto acima de 15% requer aprovação financeira.")
        
        valor_desconto = (subtotal_geral * percentual_desconto) / 100
        total_final = subtotal_geral - valor_desconto

    with col2:
        st.write("") # Alinhamento
        st.markdown(f"""
            <div style="background-color: #ff6600; padding: 25px; border-radius: 4px; text-align: center;">
                <p style="color: white; margin: 0; font-size: 1.1em;">Investimento Mensal Final</p>
                <h1 style="color: white; margin: 0; font-size: 2.5em;">R$ {total_final:,.2f}</h1>
                <p style="color: white; margin: 0; font-size: 0.9em;">Desconto aplicado: R$ {valor_desconto:,.2f} ({percentual_desconto}%)</p>
            </div>
        """, unsafe_allow_html=True)

    # --- Resumo para Compartilhamento ---
    st.markdown("---")
    if st.button("Gerar Sumário Executivo"):
        status_financeiro = "REQUER APROVAÇÃO" if percentual_desconto > 15 else "APROVADO"
        
        itens_texto = ""
        for item in st.session_state.carrinho:
            itens_texto += f"- {item['Produto']} (x{item['Qtd']}): R$ {item['Subtotal']:,.2f}\n"

        resumo_final = f"""
PROPOSTA COMERCIAL - VR SOFTWARE 2026
Status: {status_financeiro}

Detalhamento dos Itens:
{itens_texto}

Condições de Pagamento:
- Subtotal: R$ {subtotal_geral:,.2f}
- Desconto: {percentual_desconto}% (R$ {valor_desconto:,.2f})
- Investimento Mensal: R$ {total_final:,.2f}
        """
        st.code(resumo_final, language="text")

else:
    st.info("Utilize o menu lateral para adicionar produtos e montar a proposta.")
