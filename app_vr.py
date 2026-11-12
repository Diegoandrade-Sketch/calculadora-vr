import streamlit as st
import pandas as pd
import datetime

# ==========================================
# CONFIGURAÇÃO DA PÁGINA ISOLADA
# ==========================================
st.set_page_config(page_title="VR Software | Gestão de Atas", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%); }
    .hero-title { color: #262730; font-size: 2.5rem; font-weight: 900; margin: 0; text-transform: uppercase; letter-spacing: -1px; }
    .card-ata { background: #ffffff; padding: 20px; border-radius: 10px; border-left: 6px solid #ff6600; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# SIMULAÇÃO DE BANCO DE DADOS EM SESSION_STATE
# ==========================================
if 'lista_atas' not in st.session_state:
    st.session_state.lista_atas = [
        {
            "id": 1,
            "titulo": "Alinhamento de Metas Q1",
            "setor": "Comercial",
            "subgrupo": "Nordeste",
            "responsavel": "Diego Andrade",
            "envolvidos": "Equipe Comercial PE",
            "data": datetime.date.today(),
            "horario": "10:00",
            "pauta": "Revisão dos processos de vendas e metas trimestrais.",
            "pendencias": "Enviar relatório atualizado até sexta-feira."
        }
    ]

# ==========================================
# CABEÇALHO E NAVEGAÇÃO POR ABAS
# ==========================================
st.markdown("<h1 class='hero-title'>GESTÃO DE ATAS & REUNIÕES</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#777; font-size:1.1rem; margin-bottom:20px;'>Documentação interna, alinhamentos e controle de pendências por setor.</p>", unsafe_allow_html=True)

aba_vis, aba_cad = st.tabs(["📋 Consultar Atas & Calendário", "➕ Nova Reunião / Ata"])

# ==========================================
# ABA 1: CONSULTA, FILTROS E CALENDÁRIO
# ==========================================
with aba_vis:
    st.markdown("### Filtros de Busca")
    f1, f2, f3 = st.columns(3)
    
    setores_opcoes = ["Todos", "Comercial", "Projetos", "Gente e Gestão", "Financeiro", "Diretoria"]
    filtro_setor = f1.selectbox("Filtrar por Setor", setores_opcoes)
    
    filtro_resp = f2.text_input("Filtrar por Responsável")
    
    modo_exibicao = f3.radio("Modo de Exibição", ["Lista Detalhada", "Visão Calendário (Simulada)"], horizontal=True)

    st.markdown("---")

    # Aplicação de Filtros
    df_atas = pd.DataFrame(st.session_state.lista_atas)
    
    if not df_atas.empty:
        if filtro_setor != "Todos":
            df_atas = df_atas[df_atas['setor'] == filtro_setor]
        if filtro_resp:
            df_atas = df_atas[df_atas['responsavel'].str.contains(filtro_resp, case=False, na=False)]

        if modo_exibicao == "Lista Detalhada":
            if df_atas.empty:
                st.info("Nenhuma ata encontrada com os filtros selecionados.")
            else:
                for _, row in df_atas.iterrows():
                    sub_str = f" | Subgrupo: <b>{row['subgrupo']}</b>" if row['subgrupo'] else ""
                    st.markdown(f"""
                        <div class="card-ata">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <h3 style="margin:0; color:#262730;">{row['titulo']}</h3>
                                <span style="background:#262730; color:#fff; padding:4px 10px; border-radius:4px; font-size:0.8rem; font-weight:bold;">{row['setor']}{sub_str}</span>
                            </div>
                            <p style="margin:8px 0; color:#555; font-size:0.9rem;">
                                <b>Data:</b> {row['data'].strftime('%d/%m/%Y')} às {row['horario']} | 
                                <b>Responsável:</b> {row['responsavel']} | 
                                <b>Envolvidos:</b> {row['envolvidos']}
                            </p>
                            <hr style="margin:8px 0; border:0; border-top:1px solid #eee;">
                            <p style="margin:5px 0;"><b>Pauta / Discussão:</b> {row['pauta']}</p>
                            <p style="margin:5px 0; color:#d32f2f;"><b>Action Items / Pendências:</b> {row['pendencias']}</p>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            # Visão Calendário Agrupada por Data
            st.markdown("#### Agenda de Reuniões")
            if df_atas.empty:
                st.info("Nenhuma reunião agendada.")
            else:
                df_calendario = df_atas.sort_values(by="data")
                for data_reuniao, grupo in df_calendario.groupby("data"):
                    st.markdown(f"##### 📅 {data_reuniao.strftime('%d/%m/%Y')}")
                    for _, r in grupo.iterrows():
                        st.info(f"**{r['horario']}** - [{r['setor']}] **{r['titulo']}** (Conduzido por: *{r['responsavel']}*)")

# ==========================================
# ABA 2: FORMULÁRIO DE CADASTRO DE ATA
# ==========================================
with aba_cad:
    st.markdown("### Registrar Nova Ata de Reunião")
    
    with st.form("form_nova_ata", clear_on_submit=True):
        c1, c2 = st.columns(2)
        titulo = c1.text_input("Título da Reunião *", placeholder="Ex: Alinhamento de Implantação")
        responsavel = c2.text_input("Responsável pela Reunião *", placeholder="Ex: Nome de quem conduziu")
        
        c3, c4 = st.columns(2)
        setor = c3.selectbox("Setor Principal *", ["Comercial", "Projetos", "Gente e Gestão", "Financeiro", "Diretoria"])
        
        # Subgrupo Dinâmico com base no Setor
        subgrupo = ""
        if setor == "Comercial":
            subgrupo = c4.selectbox("Subgrupo", ["CS", "Nordeste", "Sul"])
        elif setor == "Projetos":
            subgrupo = c4.selectbox("Subgrupo", ["Projetos", "Implantação"])
        else:
            c4.info("Este setor não possui subgrupos.")
            subgrupo = "N/A"

        c5, c6, c7 = st.columns(3)
        data_reuniao = c5.date_input("Data da Reunião", datetime.date.today())
        horario_reuniao = c6.text_input("Horário", "14:00")
        envolvidos = c7.text_input("Demais Envolvidos / Participantes", placeholder="Nomes ou equipe")

        st.markdown("---")
        pauta = st.text_area("Pauta e Assuntos Tratados", placeholder="Descreva os principais tópicos debatidos na reunião...")
        pendencias = st.text_area("Deliberações e Pendências (Action Items)", placeholder="O que ficou decidido? Quem faz e até quando?")

        submitted = st.form_submit_button("💾 Salvar Ata de Reunião", use_container_width=True)
        
        if submitted:
            if not titulo or not responsavel or not pauta:
                st.error("Por favor, preencha os campos obrigatórios (Título, Responsável e Pauta).")
            else:
                nova_ata = {
                    "id": len(st.session_state.lista_atas) + 1,
                    "titulo": titulo,
                    "setor": setor,
                    "subgrupo": subgrupo,
                    "responsavel": responsavel,
                    "envolvidos": envolvidos,
                    "data": data_reuniao,
                    "horario": horario_reuniao,
                    "pauta": pauta,
                    "pendencias": pendencias if pendencias else "Nenhuma pendência registrada."
                }
                st.session_state.lista_atas.insert(0, nova_ata)
                st.success("Ata registrada com sucesso! Vá para a aba 'Consultar Atas' para visualizá-la.")
