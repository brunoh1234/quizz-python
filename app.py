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
# CSS GAMING NEON
# ------------------------------
 
st.markdown("""
<style>
 
body {
    background-color: #0a0f1f;
    color: #e0e0ff;
}
 
/* Caixa neon */
.neon-box {
    padding: 25px;
    background: rgba(10, 15, 30, 0.85);
    border-radius: 12px;
    border: 2px solid #6a00ff;
    box-shadow: 0 0 20px #6a00ff, 0 0 40px #6a00ff inset;
    animation: fadeIn 0.6s ease;
}
 
/* Botões neon */
button[kind="primary"] {
    background: linear-gradient(90deg, #ff00cc, #3333ff) !important;
    color: white !important;
    border-radius: 10px !important;
    padding: 12px 20px !important;
    font-size: 18px !important;
    border: none !important;
    box-shadow: 0 0 12px #ff00cc;
    transition: 0.2s ease-in-out;
}
 
button[kind="primary"]:hover {
    transform: scale(1.05);
    box-shadow: 0 0 20px #ff00cc, 0 0 30px #3333ff;
}
 
/* Barra de energia */
.energy-bar {
    height: 20px;
    width: 100%;
    background: #1a1a2e;
    border-radius: 10px;
    margin-bottom: 15px;
    box-shadow: 0 0 10px #6a00ff inset;
}
 
.energy-fill {
    height: 100%;
    background: linear-gradient(90deg, #00eaff, #6a00ff);
    border-radius: 10px;
    box-shadow: 0 0 15px #00eaff;
    transition: width 0.5s ease;
}
 
/* Títulos neon */
.neon-title {
    font-size: 32px;
    font-weight: bold;
    color: #00eaff;
    text-shadow: 0 0 10px #00eaff, 0 0 20px #6a00ff;
}
 
/* Fade */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
 
</style>
""", unsafe_allow_html=True)
 
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
 
st.markdown('<h1 class="neon-title">Quiz — Trabalho Híbrido</h1>', unsafe_allow_html=True)
 
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
        medalha = "🥇"
        msg = "Excelente! Domínio total do tema."
    elif score >= 15:
        medalha = "🥈"
        msg = "Muito bom! Tens forte domínio do conteúdo."
    elif score >= 10:
        medalha = "🥉"
        msg = "Bom esforço! Ainda há espaço para melhorar."
    else:
        medalha = "🎗"
        msg = "Continua a praticar — estás no caminho certo."
 
    st.markdown(f"""
<div class="neon-box" style="text-align:center;">
<h2 class="neon-title">Pontuação final: {score}/20</h2>
<div style="font-size: 90px; margin-top: 10px; text-shadow: 0 0 25px #ff00cc;">
            {medalha}
</div>
<p style="font-size: 22px; color: #e0e0ff;">{msg}</p>
</div>
    """, unsafe_allow_html=True)
 
    resultados[st.session_state.user_id] = {
        "score": score,
        "data": datetime.now().strftime("%d/%m/%Y"),
        "hora": datetime.now().strftime("%H:%M:%S")
    }
    guardar_resultados(resultados)
 
    st.markdown('<h2 class="neon-title">Ranking dos Colegas</h2>', unsafe_allow_html=True)
 
    ranking = sorted(resultados.items(), key=lambda x: x[1]["score"], reverse=True)
    for pos, (uid, dados) in enumerate(ranking, start=1):
        st.markdown(f"""
<div style="padding:10px; margin-bottom:8px; border-radius:8px;
        background:rgba(20,20,40,0.8); border:1px solid #6a00ff;
        box-shadow:0 0 10px #6a00ff inset;">
<b style="color:#00eaff;">{pos}. {uid}</b> — {dados['score']} pontos
</div>
        """, unsafe_allow_html=True)
 
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
 
progresso = int((idx / len(perguntas)) * 100)
 
st.markdown(f"""
<div class="energy-bar">
<div class="energy-fill" style="width: {progresso}%"></div>
</div>
""", unsafe_allow_html=True)
 
st.markdown('<div class="neon-box">', unsafe_allow_html=True)
st.markdown(f'<h2 class="neon-title">Pergunta {idx+1} de {len(perguntas)}</h2>', unsafe_allow_html=True)
st.write(pergunta)
st.markdown('</div>', unsafe_allow_html=True)
 
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
