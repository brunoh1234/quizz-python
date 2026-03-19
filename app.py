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
# CONFIGURAÇÃO DA PÁGINA
# ------------------------------

st.set_page_config(page_title="Quem Quer Ser Produtivo?", layout="wide")

# ------------------------------
# CSS — DESIGN QUEM QUER SER MILIONÁRIO
# ------------------------------

st.markdown("""
<style>

/* Fundo escuro tipo Milionário */
.stApp {
    background: radial-gradient(circle, #0d1b3e 0%, #02050a 100%);
    color: white;
}

#MainMenu, header, footer {visibility: hidden;}

/* Contentor da Pergunta (Hexágono Grande) */
.question-box {
    background: linear-gradient(180deg, #0a1a3c 0%, #000000 100%);
    border: 2px solid #1e90ff;
    padding: 40px;
    text-align: center;
    margin: 20px auto;
    width: 85%;
    clip-path: polygon(5% 0%, 95% 0%, 100% 50%, 95% 100%, 5% 100%, 0% 50%);
    box-shadow: 0 0 20px rgba(30, 144, 255, 0.6);
}

.question-text {
    font-size: 26px;
    font-weight: bold;
    color: #ffffff;
    text-shadow: 0 0 10px rgba(30,144,255,0.8);
    line-height: 1.5;
}

/* Número da pergunta */
.question-number {
    font-size: 16px;
    color: #7eb8ff;
    margin-bottom: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
}

/* Grelha 2x2 das respostas */
.answers-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    max-width: 900px;
    margin: 30px auto;
    padding: 0 20px;
}

/* Botão de resposta — hexágono alongado */
.answer-option {
    background: linear-gradient(135deg, #0a1a4a 0%, #001030 100%);
    border: 2px solid #1e90ff;
    clip-path: polygon(18px 0%, calc(100% - 18px) 0%, 100% 50%, calc(100% - 18px) 100%, 18px 100%, 0% 50%);
    padding: 18px 30px 18px 40px;
    display: flex;
    align-items: center;
    cursor: pointer;
    transition: all 0.2s ease;
    box-shadow: 0 0 12px rgba(30, 144, 255, 0.4);
    min-height: 64px;
}

.answer-option:hover {
    background: linear-gradient(135deg, #1a3a8a 0%, #0a2060 100%);
    box-shadow: 0 0 25px rgba(30, 144, 255, 0.9);
    transform: scale(1.02);
}

.answer-option.correct {
    background: linear-gradient(135deg, #0a4a1a 0%, #003010 100%);
    border-color: #00e676;
    box-shadow: 0 0 25px rgba(0, 230, 118, 0.8);
}

.answer-option.wrong {
    background: linear-gradient(135deg, #4a0a0a 0%, #300000 100%);
    border-color: #ff1744;
    box-shadow: 0 0 25px rgba(255, 23, 68, 0.8);
}

/* Letra da resposta (A, B, C, D) */
.answer-letter {
    font-size: 20px;
    font-weight: bold;
    color: #7eb8ff;
    min-width: 35px;
    margin-right: 12px;
}

/* Texto da resposta */
.answer-text {
    font-size: 18px;
    color: #e0eaff;
    font-weight: 500;
}

/* Barra de progresso */
.progress-container {
    width: 85%;
    margin: 10px auto;
    background: #0a1a3c;
    border: 1px solid #1e3a6e;
    border-radius: 10px;
    height: 14px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #1e90ff, #00bfff);
    border-radius: 10px;
    transition: width 0.5s ease;
    box-shadow: 0 0 8px rgba(30,144,255,0.7);
}

/* Título principal */
.main-title {
    font-size: 38px;
    font-weight: 900;
    text-align: center;
    color: #ffffff;
    text-shadow: 0 0 20px rgba(30,144,255,1), 0 0 40px rgba(30,144,255,0.5);
    letter-spacing: 3px;
    padding: 20px 0;
    font-family: 'Georgia', serif;
}

/* Ecrã de login */
.login-box {
    background: linear-gradient(180deg, #0a1a3c 0%, #000000 100%);
    border: 2px solid #1e90ff;
    border-radius: 16px;
    padding: 40px;
    max-width: 500px;
    margin: 40px auto;
    text-align: center;
    box-shadow: 0 0 30px rgba(30, 144, 255, 0.5);
}

/* Caixa do ranking */
.ranking-box {
    background: linear-gradient(135deg, #0a1a4a 0%, #001030 100%);
    border: 1px solid #1e90ff;
    border-radius: 10px;
    padding: 15px 25px;
    margin: 8px auto;
    max-width: 600px;
    box-shadow: 0 0 10px rgba(30, 144, 255, 0.3);
}

/* Ecrã final */
.final-box {
    background: linear-gradient(180deg, #0a1a3c 0%, #000000 100%);
    border: 2px solid #ffd700;
    border-radius: 16px;
    padding: 40px;
    max-width: 700px;
    margin: 20px auto;
    text-align: center;
    box-shadow: 0 0 40px rgba(255, 215, 0, 0.5);
}

/* Botões Streamlit */
.stButton > button {
    background: linear-gradient(135deg, #1e3a8a, #1e90ff) !important;
    color: white !important;
    border: 2px solid #1e90ff !important;
    border-radius: 8px !important;
    padding: 12px 28px !important;
    font-size: 18px !important;
    font-weight: bold !important;
    letter-spacing: 1px !important;
    box-shadow: 0 0 12px rgba(30,144,255,0.5) !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    box-shadow: 0 0 25px rgba(30,144,255,0.9) !important;
    transform: scale(1.03) !important;
}

/* Input */
.stTextInput > div > div > input {
    background: #0a1a3c !important;
    color: white !important;
    border: 2px solid #1e90ff !important;
    border-radius: 8px !important;
    font-size: 18px !important;
    padding: 10px !important;
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
if "resposta_dada" not in st.session_state:
    st.session_state.resposta_dada = None

resultados = carregar_resultados()

# Título principal
st.markdown('<div class="main-title">🎯 QUEM QUER SER PRODUTIVO?</div>', unsafe_allow_html=True)

# ------------------------------
# BOTÃO DE RESET
# ------------------------------

col_reset, _, _ = st.columns([1, 3, 1])
with col_reset:
    if st.button("🔄 Reset Histórico"):
        resetar_historico()
        st.success("Histórico apagado com sucesso.")

# ------------------------------
# LOGIN
# ------------------------------

if st.session_state.user_id is None:
    st.markdown("""
    <div class="login-box">
        <h2 style="color:#7eb8ff; margin-bottom:20px;">👤 Identificação</h2>
        <p style="color:#aac8ff; font-size:16px;">Insere o teu nome para começar o quiz</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        user_id = st.text_input("", placeholder="O teu nome ou ID...", label_visibility="collapsed")
        if st.button("▶️  COMEÇAR O QUIZ", use_container_width=True):
            if not user_id.strip():
                st.warning("Por favor insere um nome ou ID.")
            elif ja_jogou(user_id.strip(), resultados):
                dados = resultados[user_id.strip()]
                st.error("Este utilizador já jogou.")
                st.info(f"Pontuação anterior: {dados['score']}/20 — {dados['data']} às {dados['hora']}")
            else:
                st.session_state.user_id = user_id.strip()
                st.rerun()

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
        msg = "🏆 PERFEITO! Domínio total do tema!"
        cor = "#ffd700"
    elif score >= 15:
        msg = "🥇 Muito bom! Forte domínio do conteúdo."
        cor = "#00e676"
    elif score >= 10:
        msg = "🥈 Bom esforço! Ainda há espaço para melhorar."
        cor = "#1e90ff"
    else:
        msg = "🥉 Continua a praticar — estás no caminho certo!"
        cor = "#ff9800"

    st.markdown(f"""
<div class="final-box">
    <h2 style="color:#ffd700; font-size:32px; text-shadow: 0 0 20px rgba(255,215,0,0.8);">
        🎉 Quiz Concluído!
    </h2>
    <p style="font-size:22px; color:{cor}; font-weight:bold; margin:15px 0;">
        {st.session_state.user_id}
    </p>
    <p style="font-size:48px; font-weight:900; color:#ffffff; text-shadow: 0 0 20px gold;">
        {score} / 20
    </p>
    <p style="font-size:20px; color:#aac8ff;">{msg}</p>
</div>
    """, unsafe_allow_html=True)

    # Guardar resultado
    if st.session_state.user_id not in resultados:
        resultados[st.session_state.user_id] = {
            "score": score,
            "data": datetime.now().strftime("%d/%m/%Y"),
            "hora": datetime.now().strftime("%H:%M:%S")
        }
        guardar_resultados(resultados)

    # Ranking
    st.markdown('<h3 style="color:#7eb8ff; text-align:center; margin-top:30px; letter-spacing:2px;">🏅 RANKING</h3>', unsafe_allow_html=True)
    ranking = sorted(resultados.items(), key=lambda x: x[1]["score"], reverse=True)
    medalhas = ["🥇", "🥈", "🥉"]
    for pos, (uid, dados) in enumerate(ranking, start=1):
        medalha = medalhas[pos-1] if pos <= 3 else f"{pos}."
        destaque = "border: 2px solid #ffd700; box-shadow: 0 0 15px rgba(255,215,0,0.5);" if uid == st.session_state.user_id else ""
        st.markdown(f"""
<div class="ranking-box" style="{destaque}">
    <span style="font-size:22px;">{medalha}</span>
    <b style="color:#7eb8ff; font-size:18px; margin-left:10px;">{uid}</b>
    <span style="color:#e0eaff; float:right; font-size:18px;">{dados['score']}/20 pontos</span>
</div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Jogar Novamente", use_container_width=True):
            st.session_state.user_id = None
            st.session_state.pergunta = 0
            st.session_state.respostas = []
            st.session_state.terminou = False
            st.session_state.resposta_dada = None
            st.rerun()

    st.stop()

# ------------------------------
# ECRÃ DA PERGUNTA
# ------------------------------

idx = st.session_state.pergunta
pergunta, opcoes, correta = perguntas[idx]
letras = ["A", "B", "C", "D"]
progresso = int((idx / len(perguntas)) * 100)

# Barra de progresso
st.markdown(f"""
<div style="text-align:center; color:#7eb8ff; font-size:14px; margin-top:5px; letter-spacing:2px;">
    PERGUNTA {idx + 1} DE {len(perguntas)}
</div>
<div class="progress-container">
    <div class="progress-fill" style="width: {progresso}%"></div>
</div>
""", unsafe_allow_html=True)

# Caixa da pergunta
st.markdown(f"""
<div class="question-box">
    <div class="question-text">{pergunta}</div>
</div>
""", unsafe_allow_html=True)

# Grelha de respostas 2x2
resposta_dada = st.session_state.resposta_dada

col1, col2 = st.columns(2)
colunas = [col1, col2, col1, col2]

for i, (opcao, letra) in enumerate(zip(opcoes, letras)):
    with colunas[i]:
        if resposta_dada is None:
            # Antes de responder: só o botão clicável
            if st.button(f"{letra}: {opcao}", key=f"btn_{idx}_{i}", use_container_width=True):
                st.session_state.resposta_dada = i
                st.rerun()
        else:
            # Depois de responder: só o div estilizado (correto/errado)
            classe = "answer-option"
            if i == correta:
                classe += " correct"
            elif i == resposta_dada and i != correta:
                classe += " wrong"
            st.markdown(f"""
<div class="{classe}">
    <span class="answer-letter">{letra}:</span>
    <span class="answer-text">{opcao}</span>
</div>
            """, unsafe_allow_html=True)

# Botão "Próxima pergunta" após responder
if resposta_dada is not None:
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        btn_texto = "➡️ Próxima Pergunta" if idx < len(perguntas) - 1 else "🏁 Ver Resultado Final"
        if st.button(btn_texto, use_container_width=True):
            st.session_state.respostas.append(resposta_dada)
            st.session_state.resposta_dada = None
            if idx + 1 < len(perguntas):
                st.session_state.pergunta += 1
            else:
                st.session_state.terminou = True
            st.rerun()
