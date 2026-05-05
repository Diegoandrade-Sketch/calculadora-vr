import streamlit as st
from dataclasses import dataclass
from typing import Dict, List

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="VR Software | Sales Intelligence", layout="wide")

MAX_DESCONTO = 30.0


# ==============================
# DOMAIN
# ==============================
@dataclass
class Produto:
    nome: str
    setup: float
    mensal: float
    cac: float
    margem: str
    complexidade: str
    descricao: str
    roi: str


# ==============================
# DATA (ainda local, mas isolado)
# ==============================
def carregar_produtos() -> Dict[str, Produto]:
    return {
        "VR ERP PRO": Produto("VR ERP PRO", 2415.60, 1285.71, 3000.00, "Alta", "Alta",
                             "Sistema de gestão completo para supermercados.",
                             "Redução média de 15% em perdas de estoque."),
        "VR PDV Convencional": Produto("VR PDV Convencional", 201.30, 185.71, 400.00, "Média", "Média",
                                       "Frente de caixa estável e rápido.",
                                       "Aumento de 20% na velocidade de passagem no caixa."),
    }


# ==============================
# SERVICES (regras de negócio)
# ==============================
def calcular_ltv(produto: Produto, meses: int = 24) -> float:
    return (produto.mensal * meses) + produto.setup


def calcular_payback(produto: Produto) -> float:
    if produto.mensal <= 0:
        return 0
    return (produto.cac - produto.setup) / produto.mensal


def aplicar_desconto(valor: float, desconto: float) -> float:
    desconto = min(max(desconto, 0), MAX_DESCONTO)
    return valor * (1 - desconto / 100)


# ==============================
# UI HELPERS
# ==============================
def moeda(valor: float) -> str:
    return f"R$ {valor:,.2f}"


def render_produto_card(produto: Produto):
    ltv = calcular_ltv(produto)
    payback = calcular_payback(produto)

    st.subheader(produto.nome)
    st.metric("Mensalidade", moeda(produto.mensal))
    st.caption(f"Setup: {moeda(produto.setup)}")

    col1, col2 = st.columns(2)
    col1.metric("LTV (24m)", moeda(ltv))
    col2.metric("Payback", f"{round(payback,1)} meses" if produto.mensal > 0 else "N/A")

    st.write(f"**Margem:** {produto.margem}")
    st.write(f"**Complexidade:** {produto.complexidade}")

    st.info(produto.roi)
    st.caption(produto.descricao)


# ==============================
# STATE INIT
# ==============================
if "produtos" not in st.session_state:
    st.session_state.produtos = carregar_produtos()


# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    tela = st.radio("Navegação", ["Consulta", "Proposta"])

    desconto = st.number_input(
        "Desconto (%)",
        min_value=0.0,
        max_value=MAX_DESCONTO,
        value=0.0
    )


# ==============================
# TELA: CONSULTA
# ==============================
if tela == "Consulta":
    st.title("Análise de Produto")

    nomes = list(st.session_state.produtos.keys())
    selecionado = st.selectbox("Produto", nomes)

    produto = st.session_state.produtos[selecionado]

    render_produto_card(produto)


# ==============================
# TELA: PROPOSTA
# ==============================
else:
    st.title("Proposta Comercial")

    produtos = st.session_state.produtos

    selecionados = st.multiselect(
        "Selecione os produtos",
        list(produtos.keys())
    )

    total = 0.0

    for nome in selecionados:
        produto = produtos[nome]

        qtd = st.number_input(
            f"{nome} (R$ {produto.mensal:,.2f})",
            min_value=1,
            value=1,
            key=f"qtd_{nome}"
        )

        total += produto.mensal * qtd

    total_com_desconto = aplicar_desconto(total, desconto)

    st.divider()

    st.metric("Total Bruto", moeda(total))
    st.metric("Total com Desconto", moeda(total_com_desconto))

    if desconto > 20:
        st.warning("Desconto elevado — validar margem.")
