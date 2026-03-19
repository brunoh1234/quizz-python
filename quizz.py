import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Quiz Trabalho Híbrido", page_icon="💻")

# --- ARQUIVO DE RESULTADOS ---
LOG_FILE = "resultados.csv"

def salvar_resultado(nome, score):
    novo_dado = pd.DataFrame({
        "Nome": [nome], 
        "Pontuação": [score], 
        "Data": [datetime.now().strftime("%d/%m/%Y %H:%M:%S")]
    })
    if not os.path.isfile(LOG_FILE):
        novo_dado.to_csv(LOG_FILE, index=False)
    else:
        novo_dado.to_csv(LOG_FILE, mode='a', index=False, header=False)

# --- PERGUNTAS ---
perguntas = [
    ("Quanto tempo os profissionais passam por ano em reuniões?", ["120h", "200h", "392h", "500h"], "392h"),
    ("Que percentagem das reuniões é considerada improdutiva?", ["20%", "40%", "67%", "90%"], "90%"),
    ("Quantos profissionais têm a caixa de entrada sempre aberta?", ["20%", "50%", "80%", "95%"], "95%"),
    ("O excesso de conectividade provoca:", ["Mais criatividade", "Melhor comunicação", "Perda de foco e bem‑estar", "Menos reuniões"], "Perda de foco e bem‑estar"),
    ("O Eixo Duplo da Produtividade combina:", ["Horas extra + multitasking", "Foco individual + colaboração eficiente", "Velocidade + pressão", "Automação + reuniões"], "Foco individual + colaboração eficiente"),
    # ... adicionei as 5 primeiras para exemplo, você pode completar o resto seguindo o padrão
]

st.title("🏆 Quiz Trabalho Híbrido")

# Início do Quiz
if 'user_name' not in st.session_state:
    nome = st.text_input("Insere o teu nome para começar:")
    if st.button("Começar"):
        if nome:
            st.session_state.user_name = nome
            st.session_state.indice = 0
            st.session_state.score = 0
            st.rerun()
else:
    if st.session_state.indice < len(perguntas):
        pergunta, opcoes, correta = perguntas[st.session_state.indice]
        
        st.subheader(f"Pergunta {st.session_state.indice + 1}")
        st.write(pergunta)
        
        resposta = st.radio("Escolha uma opção:", opcoes, key=f"p{st.session_state.indice}")
        
        if st.button("Confirmar Resposta"):
            if resposta == correta:
                st.session_state.score += 1
                st.success("Correto!")
            else:
                st.error(f"Incorreto. A resposta era: {correta}")
            
            st.session_state.indice += 1
            st.rerun()
    else:
        # FIM DO QUIZ
        st.balloons()
        score_final = st.session_state.score
        total = len(perguntas)
        st.header(f"Fim do Quiz, {st.session_state.user_name}!")
        st.write(f"Tiveste **{score_final}** de **{total}** acertos.")
        
        # Medalhas
        if score_final == total: medalha = "🥇 Ouro"
        elif score_final >= total*0.7: medalha = "🥈 Prata"
        else: medalha = "🥉 Bronze"
        
        st.subheader(f"Medalha: {medalha}")
        
        if st.button("Guardar e ver Ranking"):
            salvar_resultado(st.session_state.user_name, score_final)
            st.session_state.finalizado = True

        if 'finalizado' in st.session_state:
            st.divider()
            st.subheader("📊 Ranking dos Colegas")
            if os.path.exists(LOG_FILE):
                df = pd.read_csv(LOG_FILE)
                st.dataframe(df.sort_values(by="Pontuação", ascending=False))
