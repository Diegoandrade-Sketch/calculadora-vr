import streamlit as st
import pandas as pd
import datetime
import calendar

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
# ABA 1: CONSULTA, FILTROS E CALENDÁRIO REAL
# ==========================================
with aba_vis:
    st.markdown("### Filtros de Busca")
    f1, f2, f3 = st.columns(3)
    
    setores_opcoes = ["Todos", "Comercial", "Projetos", "Gente e Gestão", "Financeiro", "Diretoria"]
    filtro_setor = f1.selectbox("Filtrar por Setor", setores_opcoes)
    
    filtro_resp = f2.text_input("Filtrar por Responsável")
    
    modo_exibicao = f3.radio("Modo de Exibição", ["Lista Detalhada", "Visão Calendário (Mês a Mês)"], horizontal=True)

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
            # ==========================================
            # VISÃO CALENDÁRIO MÊS A MÊS
            # ==========================================
            st.markdown("#### 📅 Calendário de Reuniões")
            
            c_mes, c_ano = st.columns(2)
            meses_dict = {
                1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 
                5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 
                9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
            }
            hoje = datetime.date.today()
            
            mes_sel = c_mes.selectbox("Selecionar Mês", list(meses_dict.keys()), format_func=lambda x: meses_dict[x], index=hoje.month - 1)
            ano_sel = c_ano.number_input("Selecionar Ano", value=hoje.year, step=1)

            st.markdown("---")

            # Gerar matriz do calendário (Segunda a Domingo ou Domingo a Sábado)
            cal = calendar.monthcalendar(ano_sel, mes_sel)
            dias_semana = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]

            # Cabeçalho dos dias da semana
            cols_sem = st.columns(7)
            for i, d_nome in enumerate(dias_semana):
                cols_sem[i].markdown(f"<div style='text-align: center; font-weight: bold; color: #555; background: #e0e0e0; padding: 5px; border-radius: 4px;'>{d_nome}</div>", unsafe_allow_html=True)

            # Filtrar atas para o mês e ano selecionados
            df_mes = df_atas[
                (df_atas['data'].apply(lambda x: x.year) == ano_sel) & 
                (df_atas['data'].apply(lambda x: x.month) == mes_sel)
            ]

            # Mapear reuniões por dia do mês
            reunioes_por_dia = {}
            for _, r in df_mes.iterrows():
                dia_num = r['data'].day
                if dia_num not in reunioes_por_dia:
                    reunioes_por_dia[dia_num] = []
                reunioes_por_dia[dia_num].append(r)

            # Renderizar semanas do calendário
            for semana in cal:
                cols_dia = st.columns(7)
                for i, dia in enumerate(semana):
                    with cols_dia[i]:
                        if dia == 0:
                            st.markdown("<div style='padding: 15px; color: #ccc; text-align: center; height: 90px;'>-</div>", unsafe_allow_html=True)
                        else:
                            tem_evento = dia in reunioes_por_dia
                            bg = "#fff8f0" if tem_evento else "#ffffff"
                            borda = "#ff6600" if tem_evento else "#e0e0e0"
                            
                            st.markdown(f"""
                                <div style="background: {bg}; border: 1px solid {borda}; border-radius: 6px; padding: 6px; height: 95px; overflow-y: auto; margin-bottom: 8px;">
                                    <div style="font-weight: bold; font-size: 0.85rem; color: #333; margin-bottom: 4px;">{dia}</div>
                            """, unsafe_allow_html=True)
                            
                            if tem_evento:
                                for ev in reunioes_por_dia[dia]:
                                    st.markdown(f"""
                                        <div style="background: #ff6600; color: white; font-size: 0.7rem; padding: 2px 4px; border-radius: 3px; margin-bottom: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{ev['titulo']}">
                                            🕒 {ev['horario']} - {ev['titulo']}
                                        </div>
                                    """, unsafe_allow_html=True)
                                    
                            st.markdown("</div>", unsafe_allow_html=True)

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
