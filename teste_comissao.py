import streamlit as st
import pandas as pd
import datetime
from sqlalchemy import text, create_engine

# ==========================================
# FUNÇÕES AUXILIARES E CONEXÃO
# ==========================================

# Substitua pela sua URL de conexão real do banco de dados Bitrix/PostgreSQL
def get_db_engine():
    # Exemplo: return create_engine("postgresql://usuario:senha@localhost:5432/banco")
    # Coloque a sua conexão original aqui
    pass 

def parse_currency(value_str):
    """Converte texto financeiro (ex: R$ 1.500,00) para float (1500.00)"""
    if pd.isnull(value_str):
        return 0.0
    try:
        if isinstance(value_str, (int, float)):
            return float(value_str)
        clean_str = str(value_str).upper().replace('R$', '').replace(' ', '')
        if clean_str == '' or clean_str == 'NAN':
            return 0.0
        # Remove os pontos de milhar e troca a vírgula decimal por ponto
        clean_str = clean_str.replace('.', '').replace(',', '.')
        return float(clean_str)
    except:
        return 0.0

def f_br(valor):
    """Formata um float para o padrão brasileiro de moeda (1.500,00)"""
    if pd.isnull(valor):
        return "0,00"
    try:
        # Formata com 2 casas decimais e vírgula, ajustando o milhar
        return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0,00"

# ==========================================
# GESTÃO COMERCIAL E FINANCEIRA
# ==========================================

# Dicionário de Mapeamento dos Processos do Bitrix
MAPA_PROCESSOS = {
    "2726": "NOVOS NEGÓCIOS",
    "2806": "NOVOS PRODUTOS CLIENTE VR",
    "2728": "NOVAS LOJAS CLIENTE VR",
    "5968": "O3 CLOUD - NOVOS NEGÓCIOS",
    "2724": "O3 CLOUD - BASE DE CLIENTES",
    "5998": "SKY ONE - NOVOS NEGÓCIOS",
    "6000": "SKY ONE - BASE DE CLIENTES",
    "2816": "ATUALIZAÇÃO DE VALORES",
    "2730": "TROCA DE CNPJ",
    "2810": "CUSTOMIZAÇÃO/DESENVOLVIMENTO",
    "2818": "INSTALAÇÃO TÉCNICA",
    "2812": "DESPESA DE PROJETO",
    "2814": "ACESSO TEMPORÁRIO",
    "2820": "SERVIÇOS DE TREINAMENTO",
    "2718": "CONTROLLER 360 (DESATIVADO)",
    "2720": "MASTERFISCO (DESATIVADO)",
    "2722": "OMNICHANNEL (DESATIVADO)",
    "3626": "NOVOS NEGÓCIOS - CONTROLLER 360 (DESATIVADO)",
    "3632": "NOVOS NEGÓCIOS - OMNICHANNEL (DESATIVADO)",
    "3630": "NOVOS NEGÓCIOS - MASTERFISCO (DESATIVADO)"
}

@st.dialog("Extrato de Liquidação por Produto", width="large")
def modal_extrato_venda(proposta_id, nome_cliente, processo_id):
    nome_processo = MAPA_PROCESSOS.get(str(processo_id), "Processo Não Mapeado / Outros")
    
    st.markdown(f"<h3 style='color:#262730; margin-bottom: 5px;'>{nome_cliente}</h3>", unsafe_allow_html=True)
    st.markdown(f"<span style='color:#777; font-weight:bold;'>Negócio ID: #{proposta_id} | Origem: {nome_processo}</span><hr>", unsafe_allow_html=True)
    
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            query_itens = text("""
                SELECT 
                    io.title AS "Produto/Serviço",
                    io.quantidade AS "Qtd",
                    COALESCE(io.ufcrmvalorproduto::text, '0') AS "val_unit_str",
                    io.ufcrmtipoproduto AS "Tipo ID"
                FROM itensorcamento_novo AS io
                JOIN orcamento_novo AS o ON o.id = io.parentid7
                WHERE o.dealid = :pid
            """)
            df_itens = pd.read_sql(query_itens, conn, params={"pid": proposta_id})
            
            if df_itens.empty:
                st.warning("Nenhum item detalhado encontrado no banco para esta proposta.")
                return

            df_itens['Valor Unit. (R$)'] = df_itens['val_unit_str'].apply(parse_currency)
            df_itens['Qtd'] = pd.to_numeric(df_itens['Qtd'], errors='coerce').fillna(1)
            df_itens['Valor Total (R$)'] = df_itens['Qtd'] * df_itens['Valor Unit. (R$)']
            
            df_itens['% Comissão'] = 0.0
            df_itens['Tag'] = 'Não Classificado'
            
            for index, row in df_itens.iterrows():
                tipo = pd.to_numeric(row['Tipo ID'], errors='coerce')
                nome = str(row['Produto/Serviço']).lower()
                
                # Regra Absoluta de Isenção (Despesa de Projeto)
                if str(processo_id) == '2812':
                    df_itens.at[index, '% Comissão'] = 0.0
                    df_itens.at[index, 'Tag'] = 'Despesa de Projeto (Isento)'
                else:
                    if tipo == 604: 
                        df_itens.at[index, '% Comissão'] = 5.0
                        df_itens.at[index, 'Tag'] = 'Mensalidade'
                    elif any(kw in nome for kw in ['despesa', 'km', 'hospedagem', 'alimentação', 'passagem', 'viagem']):
                        df_itens.at[index, '% Comissão'] = 0.0
                        df_itens.at[index, 'Tag'] = 'Despesa (Isento)'
                    elif tipo in [606, 608, 610]: 
                        df_itens.at[index, '% Comissão'] = 5.0
                        df_itens.at[index, 'Tag'] = 'Setup/Serviço'

            df_itens['Comissão (R$)'] = df_itens['Valor Total (R$)'] * (df_itens['% Comissão'] / 100)
            
            colunas_monetarias = ['Valor Unit. (R$)', 'Valor Total (R$)', 'Comissão (R$)']
            for col in colunas_monetarias:
                df_itens[col] = df_itens[col].apply(lambda x: f"R$ {f_br(x)}" if pd.notnull(x) else "R$ 0,00")
            
            df_itens['% Comissão'] = df_itens['% Comissão'].apply(lambda x: f"{x}%")
            
            st.dataframe(df_itens[['Produto/Serviço', 'Tag', 'Qtd', 'Valor Unit. (R$)', 'Valor Total (R$)', '% Comissão', 'Comissão (R$)']], use_container_width=True, hide_index=True)
            
    except Exception as e:
        print(f"Erro no Modal: {e}")
        st.error("Falha ao carregar detalhamento. Tente novamente.")

def tela_visao_comercial():
    st.markdown("<h1 class='hero-title'>VISÃO COMERCIAL</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#777; font-size:1.2rem; margin-bottom:30px;'>Dashboard Estratégico de Vendas e Performance</p>", unsafe_allow_html=True)
    
    hoje = datetime.date.today()
    c1, c2 = st.columns(2)
    data_inicio = c1.date_input("Período Início", hoje.replace(day=1), format="DD/MM/YYYY")
    data_fim = c2.date_input("Período Fim", hoje, format="DD/MM/YYYY")
    
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            query_dash = text("""
                SELECT DISTINCT ON (n.id)
                    n.id,
                    COALESCE(o.ufcrmvalorprojeto::text, '0') AS setup_str,
                    COALESCE(o.ufcrmvalorrecorrente::text, o.opportunity::text, '0') AS mrr_str
                FROM orcamento_novo AS o
                JOIN negocio_novo AS n ON n.id = o.dealId
                WHERE o.closedate >= :d_inicio AND o.closedate <= :d_fim
                  AND n.closed = 'Y'
            """)
            df_dash = pd.read_sql(query_dash, conn, params={"d_inicio": data_inicio, "d_fim": data_fim})
            
            if df_dash.empty:
                st.warning("Nenhum negócio fechado neste período.")
                return
                
            df_dash['Setup Bruto'] = df_dash['setup_str'].apply(parse_currency)
            df_dash['MRR Bruto'] = df_dash['mrr_str'].apply(parse_currency)
            
            t_setup = df_dash['Setup Bruto'].sum()
            t_mrr = df_dash['MRR Bruto'].sum()
            
            st.markdown("### 💰 Receita Adquirida no Período (Negócios Ganhos)")
            col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
            with col_kpi1: st.markdown(f"""<div class="dash-card" style="border-top: 5px solid #1976d2; min-height:auto; padding:15px; border-radius:5px; box-shadow: 1px 1px 5px rgba(0,0,0,0.1);"><div class="dash-title" style="color:#777; font-size:14px;">Total de MRR (Mensalidade)</div><div style="font-size:1.8rem; font-weight:900; color:#262730;">R$ {f_br(t_mrr)}</div></div>""", unsafe_allow_html=True)
            with col_kpi2: st.markdown(f"""<div class="dash-card" style="border-top: 5px solid #ff6600; min-height:auto; padding:15px; border-radius:5px; box-shadow: 1px 1px 5px rgba(0,0,0,0.1);"><div class="dash-title" style="color:#777; font-size:14px;">Total de Setup (Serviços)</div><div style="font-size:1.8rem; font-weight:900; color:#262730;">R$ {f_br(t_setup)}</div></div>""", unsafe_allow_html=True)
            with col_kpi3: st.markdown(f"""<div class="dash-card" style="border-top: 5px solid #2e7d32; min-height:auto; background:#f4f6f9; padding:15px; border-radius:5px; box-shadow: 1px 1px 5px rgba(0,0,0,0.1);"><div class="dash-title" style="color:#777; font-size:14px;">Volume Total Fechado</div><div style="font-size:1.8rem; font-weight:900; color:#262730;">R$ {f_br(t_mrr + t_setup)}</div></div>""", unsafe_allow_html=True)
            
            st.info("💡 Próxima etapa: Construção dos gráficos de Produtos Mais Vendidos e Curva ABC de Executivos.")
            
    except Exception as e:
        st.error(f"Erro ao carregar dashboards: {e}")

def tela_comissionamento():
    st.markdown("<h1 class='hero-title'>COMISSIONAMENTO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#777; font-size:1.2rem; margin-bottom:30px;'>Auditoria e Fechamento de Pagamentos Integrado ao Bitrix24</p>", unsafe_allow_html=True)

    st.markdown("""<div class="cliente-container"><h3 style="margin:0; color:#262730;">1. Filtros de Apuração de Pagamento</h3></div>""", unsafe_allow_html=True)
    
    hoje = datetime.date.today()
    c1, c2, c3 = st.columns(3)
    data_inicio = c1.date_input("Data Início (Corte)", hoje.replace(day=1), format="DD/MM/YYYY")
    data_fim = c2.date_input("Data Fim (Corte)", hoje, format="DD/MM/YYYY")
    cargo_sel = c3.selectbox("Cargo de Apuração", ["Todos", "Executivo de Vendas", "CS"])

    st.markdown("""<br><div class="mapeamento-container" style="border-left-color:#1976d2;"><h3 style="margin:0; color:#1976d2;">2. Matriz de Auditoria e Espelho de Vendas</h3></div>""", unsafe_allow_html=True)

    df_base = pd.DataFrame()
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            # Filtro rigoroso AND n.closed = 'Y' implementado
            query_bitrix = text("""
                SELECT DISTINCT ON (n.id)
                    n.id AS "Proposta ID",
                    TRIM(CONCAT(COALESCE(ab.name, ''), ' ', COALESCE(ab.lastname, ''))) AS "Vendedor", 
                    e.title AS "Cliente",
                    COALESCE(e.ufcrmintegraoreceitauf, 'N/I') AS "Estado",
                    o.closedate AS data_bruta,
                    n.processovendaid AS "Processo ID",
                    COALESCE(o.ufcrmvalorprojeto::text, '0') AS setup_str,
                    COALESCE(o.ufcrmvalorrecorrente::text, o.opportunity::text, '0') AS mrr_str
                FROM orcamento_novo AS o
                JOIN negocio_novo AS n ON n.id = o.dealId
                LEFT JOIN assignedby_novo AS ab ON ab.id = n.assignedById
                LEFT JOIN company_novo AS e ON e.id = n.companyId
                WHERE o.closedate >= :d_inicio AND o.closedate <= :d_fim
                  AND n.closed = 'Y'
                ORDER BY n.id, o.closedate DESC
            """)
            
            df_base = pd.read_sql(query_bitrix, conn, params={"d_inicio": data_inicio, "d_fim": data_fim})
            
    except Exception as e:
        print(f"Erro técnico silencioso: {e}")
        st.error("Falha ao comunicar com o banco de dados. Tente novamente mais tarde.")

    if df_base.empty:
        st.info("Nenhum fechamento encontrado no período selecionado.")
    else:
        df_base['Proposta ID'] = df_base['Proposta ID'].astype(str)
        
        cf1, cf2 = st.columns(2)
        vendedores_unicos = sorted(df_base["Vendedor"].dropna().unique().tolist())
        vendedores_sel = cf1.multiselect("Filtrar por Vendedor(es):", vendedores_unicos, placeholder="Todos selecionados por padrão")
        
        if vendedores_sel:
            df_base = df_base[df_base['Vendedor'].isin(vendedores_sel)]
            
        estados_unicos = sorted(df_base["Estado"].dropna().unique().tolist())
        estados_sel = cf2.multiselect("Filtrar por Região (UF):", estados_unicos, placeholder="Todas as regiões selecionadas por padrão")

        if estados_sel:
            df_base = df_base[df_base['Estado'].isin(estados_sel)]
            
        if df_base.empty:
            st.warning("Nenhum dado corresponde aos filtros selecionados.")
            return

        df_base['Data Venda'] = pd.to_datetime(df_base['data_bruta']).dt.strftime('%d/%m/%Y')
        df_base['Setup Bruto (R$)'] = df_base['setup_str'].apply(parse_currency)
        df_base['MRR Bruto (R$)'] = df_base['mrr_str'].apply(parse_currency)
        
        df_base['% Setup'] = 5.0 if cargo_sel != "CS" else 10.0
        df_base['% MRR'] = 5.0 if cargo_sel != "CS" else 10.0
        
        mask_despesa = df_base['Processo ID'].astype(str) == '2812'
        df_base.loc[mask_despesa, '% Setup'] = 0.0
        df_base.loc[mask_despesa, '% MRR'] = 0.0
        
        df_base['Comissão Setup (R$)'] = df_base['Setup Bruto (R$)'] * (df_base['% Setup'] / 100)
        df_base['Comissão MRR (R$)'] = df_base['MRR Bruto (R$)'] * (df_base['% MRR'] / 100)
        df_base['Total Líquido (R$)'] = df_base['Comissão Setup (R$)'] + df_base['Comissão MRR (R$)']

        t_setup_comis = df_base['Comissão Setup (R$)'].sum()
        t_mrr_comis = df_base['Comissão MRR (R$)'].sum()
        t_geral = df_base['Total Líquido (R$)'].sum()

        df_exibicao = df_base.copy()
        colunas_monetarias = ['Setup Bruto (R$)', 'MRR Bruto (R$)', 'Comissão Setup (R$)', 'Comissão MRR (R$)', 'Total Líquido (R$)']
        for col in colunas_monetarias:
            df_exibicao[col] = df_exibicao[col].apply(lambda x: f"R$ {f_br(x)}")
            
        ordem_colunas = ["Vendedor", "Proposta ID", "Cliente", "Estado", "Data Venda", "Setup Bruto (R$)", "MRR Bruto (R$)", "% Setup", "% MRR", "Comissão Setup (R$)", "Comissão MRR (R$)", "Total Líquido (R$)"]
        df_exibicao_limpa = df_exibicao[ordem_colunas]

        df_exibicao_limpa.insert(0, "Ver Extrato", False)
        colunas_bloqueadas = [col for col in df_exibicao_limpa.columns if col != "Ver Extrato"]
        edited_df = st.data_editor(
            df_exibicao_limpa,
            use_container_width=True,
            hide_index=True,
            column_config={"Ver Extrato": st.column_config.CheckboxColumn("Ver Extrato", default=False)},
            disabled=colunas_bloqueadas
        )

        linhas_selecionadas = edited_df[edited_df["Ver Extrato"] == True]
        if not linhas_selecionadas.empty:
            prop_selecionada = linhas_selecionadas.iloc[0]["Proposta ID"]
            nome_cli_sel = linhas_selecionadas.iloc[0]["Cliente"]
            proc_id_sel = df_base[df_base["Proposta ID"].astype(str) == str(prop_selecionada)]["Processo ID"].values[0]
            
            modal_extrato_venda(prop_selecionada, nome_cli_sel, proc_id_sel)

        st.markdown("""<br><div class="cliente-container" style="border-left-color:#2e7d32;"><h3 style="margin:0; color:#2e7d32;">3. Consolidação e Fechamento</h3></div>""", unsafe_allow_html=True)
        
        col_tot1, col_tot2, col_tot4 = st.columns([1, 1, 2])
        with col_tot1: st.markdown(f"""<div class="dash-card" style="border-top: 5px solid #ff6600; min-height:auto; padding:15px; border-radius:5px; box-shadow: 1px 1px 5px rgba(0,0,0,0.1);"><div class="dash-title" style="color:#777; font-size:14px;">Total Setup a Pagar</div><div style="font-size:1.8rem; font-weight:900; color:#262730;">R$ {f_br(t_setup_comis)}</div></div>""", unsafe_allow_html=True)
        with col_tot2: st.markdown(f"""<div class="dash-card" style="border-top: 5px solid #2e7d32; min-height:auto; padding:15px; border-radius:5px; box-shadow: 1px 1px 5px rgba(0,0,0,0.1);"><div class="dash-title" style="color:#777; font-size:14px;">Total MRR a Pagar</div><div style="font-size:1.8rem; font-weight:900; color:#262730;">R$ {f_br(t_mrr_comis)}</div></div>""", unsafe_allow_html=True)
        with col_tot4: st.markdown(f"""<div class="dash-card" style="border-top: 5px solid #262730; min-height:auto; background:#f4f6f9; padding:15px; border-radius:5px; box-shadow: 1px 1px 5px rgba(0,0,0,0.1);"><div class="dash-title" style="color:#777; font-size:14px;">TOTAL LÍQUIDO A PAGAR (DO FILTRO)</div><div style="font-size:1.8rem; font-weight:900; color:#262730;">R$ {f_br(t_geral)}</div></div>""", unsafe_allow_html=True)

        st.write("---")
        c_btn1, c_btn2 = st.columns([1, 1])
        with c_btn1:
            csv = df_base.drop(columns=['setup_str', 'mrr_str']).to_csv(index=False, sep=';', decimal=',').encode('utf-8')
            st.download_button(label="📥 Exportar Relatório Contábil (CSV)", data=csv, file_name=f"comissoes_fechamento.csv", mime="text/csv", use_container_width=True)
        with c_btn2:
            if st.button("🔒 Efetivar Lote de Pagamento", type="primary", use_container_width=True):
                st.success("Operação bloqueada com sucesso.")

# ==========================================
# MOTOR PRINCIPAL DE NAVEGAÇÃO
# ==========================================

def aplicativo_principal():
    # Esconde o menu original do Streamlit e margens para visual mais limpo
    st.set_page_config(page_title="Gestão VR", layout="wide")
    
    st.sidebar.title("Módulos VR")
    
    # Navegação dividida conforme a estrutura simples que combinamos
    menu = st.sidebar.radio(
        "Navegação", 
        [
            "Mapeamento Operacional", 
            "Proposta Comercial", 
            "Resumo de Investimentos", 
            "Visão Comercial", 
            "Comissionamento"
        ]
    )

    if menu == "Mapeamento Operacional":
        st.info("Ambiente de Mapeamento Operacional. (Suas 2.000 linhas entram aqui)")
    elif menu == "Proposta Comercial":
        st.info("Ambiente de Proposta Comercial. (Suas 2.000 linhas entram aqui)")
    elif menu == "Resumo de Investimentos":
        st.info("Ambiente de Resumo de Investimentos. (Suas 2.000 linhas entram aqui)")
    elif menu == "Visão Comercial":
        tela_visao_comercial()
    elif menu == "Comissionamento":
        tela_comissionamento()

# Inicializador do App
if __name__ == "__main__":
    aplicativo_principal()
