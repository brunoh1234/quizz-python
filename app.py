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
# Perguntas
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
     ["São curtas", "Destruem o foco individual", "Têm poucos participantes", "Ajudam a concentração"], 2),
    ("Primeira fase de uma reunião produtiva:",
     ["Durante", "Depois", "Antes", "Avaliação"], 3),
    ("Antes da reunião deve-se:",
     ["Improvisar agenda", "Convidar todos", "Clarificar objetivo", "Começar sem contexto"], 3),
    ("O 'Olhar Digital' implica:",
     ["Olhar para o teclado", "Câmara desligada", "Olhar para a lente", "Evitar olhar"], 3),
    ("O 'Silêncio Tático' significa:",
     ["Falar sempre", "Mute até falar", "Desligar câmara", "Não participar"], 2),
    ("Entrada Antecipada é:",
     ["20 min antes", "5 min antes", "No minuto exato", "Depois do moderador"], 2),
    ("Para reduzir Zoom Fatigue:",
     ["Reuniões longas", "Chamadas seguidas", "Encurtar reuniões e dar pausas", "Câmara sempre ligada"], 3),
    ("Órbita 1 (Videoconferência) é:",
     ["O cérebro", "O palco", "O arquivo", "O gestor"], 2),
    ("Fecho de Sistema inclui:",
     ["Responder emails", "Planear o dia seguinte", "Agendar reuniões", "Fazer multitasking"], 2)
]
 
# ------------------------------
# Estado inicial
# ------------------------------
 
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "pergunta" not in st.session_state:
    st.session_state.pergunta = 0
if "respostas" not in st.session_state:
    st.session_state.respostas = []
if "terminou" not in st.session_state:
    st.session_state.terminou = False
 
resultados = carregar_resultados()
 
st.title("Quiz — Trabalho Híbrido")
 
# ------------------------------
# LOGIN
# ------------------------------
 
if st.session_state.user_id is None:
    user_id = st.text_input("Insere o teu ID de utilizador")
 
    if st.button("Começar"):
        if not user_id.strip():
            st.warning("Por favor insere um ID.")
        elif ja_jogou(user_id.strip(), resultados):
            dados = resultados[user_id.strip()]
            st.error("Este utilizador já jogou.")
            st.info(f"Pontuação: {dados['score']} | {dados['data']} {dados['hora']}")
        else:
            st.session_state.user_id = user_id.strip()
 
    st.stop()
 
# ------------------------------
# ECRÃ FINAL
# ------------------------------
 
if st.session_state.terminou:
    score = sum(
        1 for idx, r in enumerate(st.session_state.respostas)
        if r == perguntas[idx][2]
    )
 
    if score == 20:
        medalha = "🥇 Ouro"
    elif score >= 15:
        medalha = "🥈 Prata"
    elif score >= 10:
        medalha = "🥉 Bronze"
    else:
        medalha = "🎗 Participação"
 
    st.subheader(f"Utilizador: {st.session_state.user_id}")
    st.write(f"Pontuação final: **{score}/20**")
    st.write(f"Medalha: {medalha}")
 
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
        st.write(f"{pos}. **{uid}** — {dados['score']} pontos")
 
    if st.button("Jogar novamente"):
        st.session_state.user_id = None
        st.session_state.pergunta = 0
        st.session_state.respostas = []
        st.session_state.terminou = False
 
    st.stop()
 
# ------------------------------
# PERGUNTAS
# ------------------------------
 
idx = st.session_state.pergunta
pergunta, opcoes, correta = perguntas[idx]
 
st.progress(idx / len(perguntas))
st.subheader(f"Pergunta {idx+1} de {len(perguntas)}")
st.write(pergunta)
 
escolha = st.radio(
    "Escolhe uma opção:",
    list(range(1, len(opcoes)+1)),
    format_func=lambda x: f"{x}) {opcoes[x-1]}",
    key=f"q_{idx}"
)
 
if st.button("Seguinte"):
    st.session_state.respostas.append(escolha)
    st.session_state.pergunta += 1
 
    if st.session_state.pergunta >= len(perguntas):
        st.session_state.terminou = True
 
    st.rerun()
