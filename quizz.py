import streamlit as st

import json

import os

from datetime import datetime
 
RESULTADOS_FICHEIRO = "resultados.json"
 
# ------------------------------

# Funções de armazenamento

# ------------------------------
 
def carregar_resultados():

    if not os.path.exists(RESULTADOS_FICHEIRO):

        return {}

    with open(RESULTADOS_FICHEIRO, "r") as f:

        return json.load(f)
 
def guardar_resultados(resultados):

    with open(RESULTADOS_FICHEIRO, "w") as f:

        json.dump(resultados, f, indent=4)
 
def ja_jogou(user_id, resultados):

    return user_id in resultados
 
# ------------------------------

# Perguntas do quiz

# ------------------------------
 
perguntas = [

    ("Quanto tempo os profissionais passam por ano em reuniões?",

     ["120h", "200h", "392h", "500h"], 2),

    ("Que percentagem das reuniões é considerada improdutiva?",

     ["20%", "40%", "67%", "90%"], 2),

    ("Quantos profissionais têm a caixa de entrada sempre aberta?",

     ["20%", "50%", "80%", "95%"], 2),

    ("O excesso de conectividade provoca:",

     ["Mais criatividade", "Melhor comunicação", "Perda de foco e bem‑estar", "Menos reuniões"], 2),

    ("O Eixo Duplo da Produtividade combina:",

     ["Horas extra + multitasking", "Foco individual + colaboração eficiente", "Velocidade + pressão", "Automação + reuniões"], 1),

    ("Qual NÃO é um dos 5 pilares da gestão de tempo?",

     ["Expandir perceção", "Demarcar limites", "Erradicar esgotamento", "Trabalhar mais horas"], 3),

    ("O método Pomodoro usa ciclos de:",

     ["10/10", "25/5", "40/10", "60/15"], 1),

    ("Eat the Frog significa:",

     ["Fazer a tarefa mais fácil", "Fazer a mais difícil de manhã", "Fazer várias tarefas", "Evitar pausas"], 1),

    ("Pareto 80/20 sugere:",

     ["80 tarefas em 20 min", "Eliminar 80% em 20% do tempo", "Trabalhar 80% do dia", "Fazer 20% primeiro"], 1),

    ("O cérebro faz multitasking?",

     ["Sim", "Não, alterna rapidamente", "Apenas com treino", "Só com música"], 1),

    ("Quantos fazem multitasking em reuniões?",

     ["30%", "50%", "92%", "100%"], 2),

    ("Reuniões mal planeadas:",

     ["São curtas", "Destruem o foco individual", "Têm poucos participantes", "Ajudam a concentração"], 1),

    ("Primeira fase de uma reunião produtiva:",

     ["Durante", "Depois", "Antes", "Avaliação"], 2),

    ("Antes da reunião deve-se:",

     ["Improvisar agenda", "Convidar todos", "Clarificar objetivo", "Começar sem contexto"], 2),

    ("O 'Olhar Digital' implica:",

     ["Olhar para o teclado", "Câmara desligada", "Olhar para a lente", "Evitar olhar"], 2),

    ("O 'Silêncio Tático' significa:",

     ["Falar sempre", "Mute até falar", "Desligar câmara", "Não participar"], 1),

    ("Entrada Antecipada é:",

     ["20 min antes", "5 min antes", "No minuto exato", "Depois do moderador"], 1),

    ("Para reduzir Zoom Fatigue:",

     ["Reuniões longas", "Chamadas seguidas", "Encurtar reuniões e dar pausas", "Câmara sempre ligada"], 2),

    ("Órbita 1 (Videoconferência) é:",

     ["O cérebro", "O palco", "O arquivo", "O gestor"], 1),

    ("Fecho de Sistema inclui:",

     ["Responder emails", "Planear o dia seguinte", "Agendar reuniões", "Fazer multitasking"], 1)

]
 
# ------------------------------

# Estado inicial

# ------------------------------
 
if "user_id" not in st.session_state:

    st.session_state.user_id = ""

if "pergunta_idx" not in st.session_state:

    st.session_state.pergunta_idx = 0

if "respostas" not in st.session_state:

    st.session_state.respostas = []

if "terminou" not in st.session_state:

    st.session_state.terminou = False
 
resultados = carregar_resultados()
 
st.title("Quiz — Trabalho Híbrido")
 
# ------------------------------

# ID do utilizador

# ------------------------------
 
if st.session_state.user_id == "":

    user_id = st.text_input("Insere o teu ID de utilizador")

    if st.button("Começar"):

        if not user_id.strip():

            st.warning("Por favor, insere um ID.")

        elif ja_jogou(user_id.strip(), resultados):

            dados = resultados[user_id.strip()]

            st.error("Este utilizador já jogou.")

            st.info(f"Pontuação: {dados['score']} | Data: {dados['data']} {dados['hora']}")

        else:

            st.session_state.user_id = user_id.strip()

            st.experimental_rerun()

    st.stop()
 
# ------------------------------

# Se já terminou, mostrar resultados

# ------------------------------
 
if st.session_state.terminou:

    score = sum(

        1 for idx, r in enumerate(st.session_state.respostas)

        if r == perguntas[idx][2]

    )
 
    if score == 20:

        medalha = "🥇 Ouro"

        msg = "Excelente! Domínio total do tema."

    elif score >= 15:

        medalha = "🥈 Prata"

        msg = "Muito bom! Tens forte domínio do conteúdo."

    elif score >= 10:

        medalha = "🥉 Bronze"

        msg = "Bom esforço! Ainda há espaço para melhorar."

    else:

        medalha = "🎗 Participação"

        msg = "Continua a praticar — estás no caminho certo."
 
    st.subheader(f"Utilizador: {st.session_state.user_id}")

    st.write(f"Pontuação final: **{score}/20**")

    st.write(f"Medalha: {medalha}")

    st.info(msg)
 
    # guardar resultados

    resultados[st.session_state.user_id] = {

        "score": score,

        "data": datetime.now().strftime("%d/%m/%Y"),

        "hora": datetime.now().strftime("%H:%M:%S")

    }

    guardar_resultados(resultados)
 
    st.markdown("---")

    st.subheader("Ranking dos colegas")
 
    ranking = sorted(resultados.items(), key=lambda x: x[1]["score"], reverse=True)

    for pos, (uid, dados) in enumerate(ranking, start=1):

        st.write(f"{pos}. **{uid}** — {dados['score']} pontos ({dados['data']} {dados['hora']})")
 
    if st.button("Jogar novamente com outro ID"):

        for k in ["user_id", "pergunta_idx", "respostas", "terminou"]:

            st.session_state[k] = "" if k == "user_id" else (0 if k == "pergunta_idx" else ([] if k == "respostas" else False))

        st.experimental_rerun()
 
    st.stop()
 
# ------------------------------

# Perguntas

# ------------------------------
 
idx = st.session_state.pergunta_idx

pergunta, opcoes, correta = perguntas[idx]
 
st.progress((idx) / len(perguntas))

st.subheader(f"Pergunta {idx+1} de {len(perguntas)}")

st.write(pergunta)
 
escolha = st.radio("Escolhe uma opção:", range(1, len(opcoes)+1),

                   format_func=lambda x: f"{x}) {opcoes[x-1]}",

                   key=f"pergunta_{idx}")
 
if st.button("Seguinte"):

    st.session_state.respostas.append(escolha)

    st.session_state.pergunta_idx += 1
 
    if st.session_state.pergunta_idx >= len(perguntas):

        st.session_state.terminou = True
 
    st.experimental_rerun()
 
