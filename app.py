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
 
def resetar_historico():
    with open(RESULTADOS_FICHEIRO, "w") as f:
        json.dump({}, f)
 
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
     ["São curtas", "Destroem o foco individual", "Têm poucos participantes", "Ajudam a concentração"], 2),
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
# CSS CORPORATE + CENTRADO + CAIXAS CLICÁVEIS
# ------------------------------
 
st.markdown("""
<style>
 
body {
    background-color: #1f2937;
    color: #e5e7eb;
    font-size: 20px;
}
 
/* Centrar toda a página */
.main > div {
    display: flex;
    flex-direction: column;
    align-items: center;
}
 
.block-container {
    max-width: 900px;
    margin-left: auto;
    margin-right: auto;
}
 
/* Caixa corporativa */
.corp-box {
    padding: 25px;
    background: #111827;
    border-radius: 12px;
    border: 1px solid #374151;
    box-shadow: 0 4px 12px rgba(0,0,0,0.25);
    width: 100%;
    text-align: center;
}
 
/* Títulos */
.corp-title {
    font-size: 34px;
    font-weight: 700;
    color: #60a5fa;
    text-align: center;
}
 
/* Subtítulos */
.corp-subtitle {
    font-size: 26px;
    font-weight: 600;
    color: #93c5fd;
    text-align: center;
}
 
/* Caixas clicáveis */
.answer-btn {
    background: #1f2937;
    border: 1px solid #374151;
    padding: 18px 22px;
    border-radius: 10px;
    margin: 12px auto;
    width: 100%;
    max-width: 350px;
    text-align: center;
    font-size: 22px;
    color: #e5e7eb;
    cursor: pointer;
    transition: 0.2s ease-in-out;
}
 
.answer-btn:hover {
    background: #2563eb33;
    border-color: #60a5fa;
    transform: scale(1.03);
}
 
/* Botões */
button[kind="primary"] {
    background-color: #2563eb !important;
    color: white !important;
    border-radius: 8px !important;
    padding: 12px 20px !important;
    font-size: 20px !important;
    border: none !important;
}
 
button[kind="primary"]:hover {
    background-color: #1e40af !important;
}
 
/* Barra de progresso */
.energy-bar {
    height: 22px;
    width: 100%;
    background: #374151;
    border-radius: 10px;
    margin-bottom: 15px;
}
 
.energy-fill {
    height: 100%;
    background: linear-gradient(90deg, #60a5fa, #2563eb);
    border-radius: 10px;
    transition: width 0.5s ease;
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
 
st.markdown('<h1 class="corp-title">Quiz — Trabalho Híbrido</h1>', unsafe_allow_html=True)
 
# ------------------------------
# BOTÃO DE RESET DO HISTÓRICO
# ------------------------------
 
if st.button("🔄 Reset ao Histórico de Classificações"):
    resetar_historico()
    st.success("Histórico apagado com sucesso.")
 
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
        msg = "Excelente! Domínio total do tema."
    elif score >= 15:
        msg = "Muito bom! Tens forte domínio do conteúdo."
    elif score >= 10:
        msg = "Bom esforço! Ainda há espaço para melhorar."
    else:
        msg = "Continua a praticar — estás no caminho certo."
 
    # imagem de sala de reunião
    st.markdown("""
<div style="text-align:center;">
<img src="https://images.unsplash.com/photo-1589820296156-2454bb8f1b0c"
             style="width:60%; border-radius:12px; margin-bottom:20px;">
</div>
    """, unsafe_allow_html=True)
 
    st.markdown(f"""
<div class="corp-box">
<h2 class="corp-title">Pontuação final: {score}/20</h2>
<p style="font-size: 22px; color: #e5e7eb;">{msg}</p>
</div>
    """, unsafe_allow_html=True)
 
    resultados[st.session_state.user_id] = {
        "score": score,
        "data": datetime.now().strftime("%d/%m/%Y"),
        "hora": datetime.now().strftime("%H:%M:%S")
    }
    guardar_resultados(resultados)
 
    st.markdown('<h2 class="corp-title">Ranking dos Colegas</h2>', unsafe_allow_html=True)
 
    ranking = sorted(resultados.items(), key=lambda x: x[1]["score"], reverse=True)
    for pos, (uid, dados) in enumerate(ranking, start=1):
        st.markdown(f"""
<div class="corp-box" style="margin-bottom:10px;">
<b style="color:#93c5fd;">{pos}. {uid}</b> — {dados['score']} pontos
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
 
st.markdown(f"""
<div class="corp-box">
<h2 class="corp-subtitle">Pergunta {idx+1} de {len(perguntas)}</h2>
<p style="font-size:22px; color:#e5e7eb;">{pergunta}</p>
</div>
""", unsafe_allow_html=True)
 
# ------------------------------
# RESPOSTAS — CAIXAS CLICÁVEIS EM DUAS COLUNAS
# ------------------------------
 
col1, col2 = st.columns(2)
 
for i, opcao in enumerate(opcoes, start=1):
 
    letra = chr(64 + i)  # A, B, C, D
 
    caixa_html = f"""
<div class='answer-btn'>{letra}) {opcao}</div>
    """
 
    # Primeiras duas respostas na coluna 1
    if i <= 2:
        with col1:
            if st.button(f"{letra}) {opcao}", key=f"btn_{idx}_{i}"):
                st.session_state.respostas.append(i)
                st.session_state.pergunta += 1
 
                if st.session_state.pergunta >= len(perguntas):
                    st.session_state.terminou = True
 
                st.rerun()
 
            st.markdown(caixa_html, unsafe_allow_html=True)
 
    # Últimas duas respostas na coluna 2
    else:
        with col2:
            if st.button(f"{letra}) {opcao}", key=f"btn_{idx}_{i}"):
                st.session_state.respostas.append(i)
                st.session_state.pergunta += 1
 
                if st.session_state.pergunta >= len(perguntas):
                    st.session_state.terminou = True
 
                st.rerun()
 
            st.markdown(caixa_html, unsafe_allow_html=True)
