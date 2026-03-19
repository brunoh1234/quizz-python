import streamlit as st
import pandas as pd
import os

# Configuração da página
st.set_page_config(page_title="Meu Quizz Python", page_icon="📝")

# --- FUNÇÕES PARA SIMULAR BANCO DE DADOS ---
LOG_FILE = "progresso_quizz.csv"

def salvar_progresso(nome, pergunta_atual, pontuacao):
    dados = {"Nome": [nome], "Ultima_Pergunta": [pergunta_atual], "Pontos": [pontuacao]}
    df = pd.DataFrame(dados)
    if not os.path.isfile(LOG_FILE):
        df.to_csv(LOG_FILE, index=False)
    else:
        # Atualiza ou adiciona novo usuário
        df_existente = pd.read_csv(LOG_FILE)
        if nome in df_existente['Nome'].values:
            df_existente.loc[df_existente['Nome'] == nome, ['Ultima_Pergunta', 'Pontos']] = [pergunta_atual, pontuacao]
            df_existente.to_csv(LOG_FILE, index=False)
        else:
            df.to_csv(LOG_FILE, mode='a', index=False, header=False)

# --- INTERFACE DO USUÁRIO ---
st.title("🏆 Quizz Interativo")

# Passo 1: Identificação
if 'usuario' not in st.session_state:
    nome_input = st.text_input("Qual é o seu nome?")
    if st.button("Começar Quizz"):
        if nome_input:
            st.session_state.usuario = nome_input
            st.session_state.pergunta = 1
            st.session_state.pontos = 0
            salvar_progresso(nome_input, "Iniciou", 0)
            st.rerun()
        else:
            st.warning("Por favor, digite seu nome.")
else:
    nome = st.session_state.usuario
    st.sidebar.write(f"Usuário: **{nome}**")
    st.sidebar.write(f"Pontuação: **{st.session_state.pontos}**")

    # Passo 2: As Perguntas
    if st.session_state.pergunta == 1:
        st.subheader("Pergunta 1: Qual dessas linguagens é famosa pela IA?")
        resp = st.radio("Escolha:", ["Java", "Python", "C++"], key="p1")
        if st.button("Confirmar"):
            if resp == "Python": st.session_state.pontos += 10
            st.session_state.pergunta = 2
            salvar_progresso(nome, "Respondeu P1", st.session_state.pontos)
            st.rerun()

    elif st.session_state.pergunta == 2:
        st.subheader("Pergunta 2: O Streamlit serve para quê?")
        resp = st.radio("Escolha:", ["Criar Apps Web", "Cozinhar", "Lavar Carros"], key="p2")
        if st.button("Finalizar"):
            if resp == "Criar Apps Web": st.session_state.pontos += 10
            st.session_state.pergunta = "Fim"
            salvar_progresso(nome, "Finalizou", st.session_state.pontos)
            st.rerun()

    else:
        st.balloons()
        st.success(f"Parabéns, {nome}! Você terminou com {st.session_state.pontos} pontos.")
        if st.button("Reiniciar"):
            del st.session_state.usuario
            st.rerun()

# --- ÁREA DO ADMINISTRADOR (SÓ VOCÊ VÊ) ---
st.divider()
with st.expander("📊 Painel de Controle (Admin)"):
    if os.path.isfile(LOG_FILE):
        df_monitor = pd.read_csv(LOG_FILE)
        st.write("Aqui você vê quem entrou e onde pararam:")
        st.dataframe(df_monitor)
    else:
        st.info("Nenhum dado registrado ainda.")