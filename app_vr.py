# ==========================================
# BLOCO 1: MÓDULO DE LOGIN (DESIGN MODERNO E NATIVO)
# ==========================================
def tela_login():
    # CSS focado apenas em transformar o fundo e o formulário do Streamlit em um card moderno
    st.markdown("""
        <style>
        /* Fundo suave para dar destaque ao card */
        .stApp { 
            background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%); 
        }
        
        /* O Card principal (Formulário) */
        div[data-testid="stForm"] {
            background-color: #ffffff;
            border-radius: 16px;
            padding: 40px 30px;
            border: none;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.05), 0 5px 15px rgba(0, 0, 0, 0.03);
        }
        
        /* Estilização do Botão Primário */
        div[data-testid="stForm"] button {
            background: linear-gradient(90deg, #ff6600 0%, #ff8533 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
            margin-top: 15px;
        }
        div[data-testid="stForm"] button:hover {
            background: linear-gradient(90deg, #e65c00 0%, #ff6600 100%);
            box-shadow: 0 4px 15px rgba(255, 102, 0, 0.4);
            transform: translateY(-1px);
            color: white;
        }
        div[data-testid="stForm"] button p {
            font-size: 1.05rem;
        }
        
        /* Refinamento dos Inputs */
        div[data-testid="stTextInput"] input {
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            padding: 12px 15px;
            background-color: #fcfcfc;
        }
        div[data-testid="stTextInput"] input:focus {
            border-color: #ff6600;
            box-shadow: 0 0 0 1px #ff6600;
            background-color: #ffffff;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Sistema de colunas para centralizar o formulário na tela
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.write("")
        st.write("") # Espaçamento superior para descer o card no monitor
        
        # O st.form cria a caixa "física" onde os elementos não escapam
        with st.form("login_form", clear_on_submit=False):
            
            # Centralização da logo dentro do card
            col_img1, col_img2, col_img3 = st.columns([1, 2, 1])
            with col_img2:
                if os.path.exists("logo_vr.png"):
                    st.image("logo_vr.png", use_container_width=True)
                else:
                    st.markdown("<h2 style='text-align:center; color:#262730; margin-bottom:0;'>VR Software</h2>", unsafe_allow_html=True)
            
            st.markdown("<p style='text-align:center; color:#777; font-size:0.95rem; margin-bottom:25px;'>Acesso Restrito</p>", unsafe_allow_html=True)
            
            # Fluxo de Primeiro Acesso
            if st.session_state.primeiro_acesso:
                st.info("Identificamos seu primeiro acesso. Por favor, crie uma senha definitiva.")
                nova_senha = st.text_input("Nova Senha", type="password")
                confirma_senha = st.text_input("Confirme a Senha", type="password")
                
                submit = st.form_submit_button("Salvar e Acessar", use_container_width=True)
                if submit:
                    if nova_senha and nova_senha == confirma_senha:
                        try:
                            engine = create_engine(CONN_STR)
                            with engine.begin() as conn:
                                conn.execute(text("UPDATE usuarios SET senha = :s, primeiro_acesso = FALSE WHERE email = :e"), {"s": nova_senha, "e": st.session_state.user_email})
                            st.session_state.primeiro_acesso = False
                            st.session_state.logged_in = True
                            st.rerun()
                        except Exception as e: 
                            st.error("Erro de comunicação com o banco de dados.")
                    else: 
                        st.error("As senhas informadas não conferem.")
            
            # Fluxo Normal
            else:
                email = st.text_input("E-mail corporativo")
                senha = st.text_input("Senha", type="password")
                
                submit = st.form_submit_button("Autenticar", use_container_width=True)
                
                if submit:
                    if email == "admin" and senha == "333666":
                        st.session_state.logged_in = True
                        st.session_state.user_role = "admin"
                        st.session_state.user_name = "Administrador Master"
                        st.rerun()
                    elif not CONN_STR:
                        st.error("Conexão com o servidor falhou.")
                    else:
                        try:
                            engine = create_engine(CONN_STR)
                            with engine.connect() as conn:
                                resultado = pd.read_sql(text("SELECT * FROM usuarios WHERE email = :e AND ativo = TRUE"), conn, params={"e": email})
                            
                            if not resultado.empty:
                                user = resultado.iloc[0]
                                if user['senha'] == senha or user['primeiro_acesso']:
                                    st.session_state.user_email = email
                                    st.session_state.user_role = user['nivel_acesso']
                                    st.session_state.user_name = user['nome']
                                    
                                    if user['primeiro_acesso']:
                                        st.session_state.primeiro_acesso = True
                                        st.rerun()
                                    else:
                                        st.session_state.logged_in = True
                                        st.rerun()
                                else: 
                                    st.error("Senha incorreta.")
                            else: 
                                st.error("Usuário não cadastrado ou bloqueado.")
                        except Exception as e: 
                            st.error("Ocorreu um erro ao validar os dados.")
