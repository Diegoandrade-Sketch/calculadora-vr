import streamlit as st
import pandas as pd

# Interface Profissional
st.set_page_config(page_title="VR Software | Simulador Maps", layout="wide")

# Estilização
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    h3 { color: #ff6600; border-bottom: 2px solid #ff6600; padding-bottom: 5px; }
    .stButton>button { background-color: #ff6600; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.image("https://vrsoft.com.br/wp-content/uploads/2022/07/Logo-VR-Software.png", width=220)
st.title("Simulador com Integração de Deslocamento")

# --- FUNÇÃO SIMULADA DO GOOGLE MAPS ---
def get_distancia_simulada(endereco_destino):
    # Aqui, no futuro, entrará a chamada real da API do Google
    # Por enquanto, vamos simular que qualquer endereço fora de Valinhos 
    # retorna uma distância padrão de 150km para teste.
    if "Valinhos" in endereco_destino:
        return 15.0
    return 150.0

# --- DADOS DE PREÇO (VALOR DO KM) ---
VALOR_KM = 2.12

# --- INTERFACE DE DESPESAS ---
st.subheader("Cálculo Automático de Deslocamento")

col_end, col_calc = st.columns([3, 1])

with col_end:
    endereco = st.text_input("Endereço Completo do Cliente", placeholder="Ex: Av. Paulista, 1000 - São Paulo, SP")

with col_calc:
    st.write(" ") # Alinhamento
    btn_calcular = st.button("Calcular Rota")

if endereco and btn_calcular:
    distancia = get_distancia_simulada(endereco)
    distancia_total = distancia * 2 # Ida e Volta
    custo_deslocamento = distancia_total * VALOR_KM
    
    st.success(f"Distância identificada: {distancia} km (Total ida/volta: {distancia_total} km)")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Distância Total", f"{distancia_total} KM")
    with c2:
        st.metric("Valor por KM", f"R$ {VALOR_KM}")
    with c3:
        st.metric("Custo Deslocamento", f"R$ {custo_deslocamento:,.2f}")

st.markdown("---")
st.info("Nota: Este cálculo utiliza o endereço da VR Software (Valinhos/SP) como ponto de partida oficial.")
