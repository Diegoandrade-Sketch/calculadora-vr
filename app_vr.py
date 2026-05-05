# 6. Lógica de Interface e Cálculos
if not modo_apresentacao:
    col1, col2, col3 = st.columns(3)
    
    dados_imp_final = []
    with col1:
        st.markdown('<div class="section-header"><span class="section-title">SERVIÇOS DE IMPLANTAÇÃO</span></div>', unsafe_allow_html=True)
        imp_sel = st.multiselect("Selecione os itens", list(itens_imp.keys()), default=list(itens_imp.keys()))
        t_imp = 0
        for item in imp_sel:
            v_u = itens_imp[item]
            # ADICIONADO: Valor unitário no label (ex: Horas: Migração (R$ 201,30))
            h = st.number_input(f"{item} (R$ {v_u:,.2f}/h)", min_value=0, value=12 if "Treinamento" not in item else 120, key=f"h_{item}")
            t_imp += h * v_u
            dados_imp_final.append((item, h, v_u))

    dados_mensal_final = []
    with col2:
        st.markdown('<div class="section-header"><span class="section-title">ITENS MENSAIS</span></div>', unsafe_allow_html=True)
        mensal_sel = st.multiselect("Selecione os produtos", list(itens_mensal.keys()), default=["VR ERP PRO"])
        t_men_bruto = 0
        for item in mensal_sel:
            v_u = itens_mensal[item]
            # ADICIONADO: Valor unitário no label (ex: Qtd: VR ERP PRO (R$ 1.285,71))
            q = st.number_input(f"{item} (R$ {v_u:,.2f})", min_value=0, value=1, key=f"q_{item}")
            t_men_bruto += q * v_u
            dados_mensal_final.append((item, q, v_u))

    dados_desp_final = []
    with col3:
        st.markdown('<div class="section-header"><span class="section-title">PREVISÃO DE DESPESAS</span></div>', unsafe_allow_html=True)
        t_desp = 0
        for item, preco in itens_desp.items():
            # ADICIONADO: Valor unitário no label
            qd = st.number_input(f"{item} (R$ {preco:,.2f})", min_value=0, value=0, key=f"d_{item}")
            t_desp += qd * preco
            if qd > 0: dados_desp_final.append((item, qd, preco))

    st.session_state.update({
        't_imp': t_imp, 
        'dados_imp': dados_imp_final, 
        't_men_bruto': t_men_bruto, 
        'dados_mensal': dados_mensal_final, 
        't_desp': t_desp, 
        'dados_desp': dados_desp_final
    })
else:
    # Recupera os dados do state no modo apresentação
    t_imp = st.session_state.get('t_imp', 0)
    dados_imp_final = st.session_state.get('dados_imp', [])
    t_men_bruto = st.session_state.get('t_men_bruto', 0)
    dados_mensal_final = st.session_state.get('dados_mensal', [])
    t_desp = st.session_state.get('t_desp', 0)
    dados_desp_final = st.session_state.get('dados_desp', [])

# Cálculo do valor líquido (Desconto)
t_men_liq = t_men_bruto * (1 - (desc/100))
st.session_state['t_men_liq'] = t_men_liq
