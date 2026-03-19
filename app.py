import streamlit as st
import json
import os
from datetime import datetime

# ------------------------------
# Configuração da Página e Ocultação de Menus
# ------------------------------
st.set_page_config(page_title="Quiz Milionário — Trabalho Híbrido", layout="centered")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 2rem;}
    </style>
    """, unsafe_allow_html=True)

RESULTADOS_FICHEIRO = "resultados.json"

# ------------------------------
# Funções de armazenamento
# ------------------------------

def carregar_resultados():
    if not os.path.exists(RESULTADOS_FICHEIRO):
        return {}
    try:
        with open(RESULTADOS_FICHEIRO, "r") as f:
            return json.load(f)
    except:
        return {}

def guardar_resultados(resultados):
    with open(RESULTADOS_FICHEIRO, "w") as f:
        json.dump(resultados, f, indent=4)

def resetar_historico():
    if os.path.exists(RESULTADOS_FICHEIRO):
        os.remove(RESULTADOS_FICHEIRO)

def ja_jogou(user_id, resultados):
    return user_id in resultados

# ------------------------------
# Perguntas (Mantidas as originais)
# ------------------------------

perguntas = [
    ("Quanto tempo os profissionais passam por ano em reuniões?", ["120h", "200h", "392h", "500h"], 3), # Resposta correta 392h
    ("Que percentagem das reuniões é considerada improdutiva?", ["20%", "40%", "67%", "90%"], 3),
    ("Quantos profissionais têm a caixa de entrada sempre aberta?", ["20%", "50%", "80%", "95%"], 3),
    ("O excesso de conectividade provoca:", ["Mais criatividade", "Melhor comunicação", "Perda de foco e bem‑estar", "Menos reuniões"], 3),
    ("O Eixo Duplo da Produtividade combina:", ["Horas extra + multitasking", "Foco individual + colaboração eficiente", "Velocidade + pressão", "Automação + reuniões"], 2),
    ("Qual NÃO é um dos 5 pilares da gestão de tempo?", ["Expandir perceção", "Demarcar limites", "Erradicar esgotamento", "Trabalhar mais horas"], 4),
    ("O método Pomodoro usa ciclos de:", ["10/10", "25/5", "40/10", "60/15"], 2),
    ("Eat the Frog significa:", ["Fazer a tarefa mais fácil", "Fazer a mais difícil de manhã", "Fazer várias tarefas", "Evitar pausas"], 2),
    ("Pareto 80/20 sugere:", ["80 tarefas em 20 min", "Eliminar 80% em 20% do tempo", "Trabalhar 80% do dia", "Fazer 20% primeiro"], 2),
    ("O cérebro faz multitasking?", ["Sim", "Não, alterna rapidamente", "Apenas com treino", "Só com música"], 2),
    ("Quantos fazem multitasking em reuniões?", ["30%", "50%", "92%", "100%"], 3),
    ("Reuniões mal planeadas:", ["São curtas", "Destruem o foco individual", "Têm poucos participantes", "Ajudam a concentração"], 2),
    ("Primeira fase de uma reunião produtiva:", ["Durante", "Depois", "Antes", "Avaliação"], 3),
    ("Antes da reunião deve-se:", ["Improvisar agenda", "Convidar todos", "Clarificar objetivo", "Começar sem contexto"], 3),
    ("O 'Olhar Digital' implica:", ["Olhar para o teclado", "Câmara desligada", "Olhar para a lente", "Evitar olhar"], 3),
    ("O 'Silêncio Tático' significa:", ["Falar sempre", "Mute até falar", "Desligar câmara", "Não participar"], 2),
    ("Entrada Antecipada é:", ["20 min antes", "5 min antes", "No minuto exato", "Depois do moderador"], 2),
    ("Para reduzir Zoom Fatigue:", ["Reuniões longas", "Chamadas seguidas", "Encurtar reuniões e dar pausas", "Câmara sempre ligada"], 3),
    ("Órbita 1 (Videoconferência) é:", ["O cérebro", "O palco", "O arquivo", "O gestor"], 2),
    ("Fecho de Sistema inclui:", ["Responder emails", "Planear o dia seguinte", "Agendar reuniões", "Fazer multitasking"], 2)
]

# ------------------------------
# CSS ESTILO "QUEM QUER SER MILIONÁRIO"
# ------------------------------

st.markdown("""
<style>
    /* Fundo e Fonte Geral */
    .stApp {
        background: radial-gradient(circle, #0d1b3e 0%, #02050a 100%);
        color: #ffffff;
    }

    /* Título */
    .m-title {
        font-family: 'Trebuchet MS', sans-serif;
        font-size: 42px;
        font-weight: bold;
        text-align: center;
        color: #ffffff;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 30px;
        text-shadow: 0 0 15px #1e90ff;
    }

    /* Caixa da Pergunta (Hexagonal Style) */
    .question-box {
        background: linear-gradient(180deg, #0a1a3c 0%, #000000 100%);
        border: 2px solid #5d8aa8;
        border-radius: 50px / 15px;
        padding: 30px;
        text-align: center;
        margin-bottom: 40px;
        box-shadow: 0 0 20px rgba(30, 144, 255, 0.3);
    }

    .question-text {
        font-size: 24px;
        font-weight: 500;
        color: #ffffff;
    }

    /* Botões de Resposta (Estilo Milionário) */
    div.stButton > button {
        background: linear-gradient(90deg, #0a1a3c 0%, #1a3a7a 50%, #0a1a3c 100%) !important;
        color: #e5e7eb !important;
        border: 2px solid #1e90ff !important;
        border-radius: 30px !important;
        height: 60px !important;
        width: 100% !important;
        font-size: 20px !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
        text-align: left !important;
        padding-left: 25px !important;
        margin-bottom: 10px !important;
    }

    div.stButton > button:hover {
        background: linear-gradient(90deg, #ff8c00 0%, #ff4500 100%) !important; /* Cor laranja ao passar o rato */
        border-color: #ffffff !important;
        color: white !important;
        transform: scale(1.02);
        box-shadow: 0 0 15px #ff8c00;
    }

    /* Texto das letras (A, B, C, D) */
    .option-letter {
        color: #ff8c00;
        margin-right: 10px;
    }

    /* Barra de Progresso Custom */
    .stProgress > div > div > div > div {
        background-color: #1e90ff;
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

# ------------------------------
# LOGIN
# ------------------------------

if st.session_state.user_id is None:
    st.markdown('<h1 class="m-title">Quem Quer Ser Produtivo?</h1>', unsafe_allow_html=True)
    
    # Botão de Reset (Admin/Debug)
    with st.expander("⚙ Opções de Teste"):
        if st.button("Limpar Histórico de Classificações"):
            resetar_historico()
            st.success("Histórico limpo!")
            st.rerun()

    user_id_input = st.text_input("Identifica-te para começar:", placeholder="Ex: Jorge")

    if st.button("ENTRAR NO PALCO"):
        if not user_id_input.strip():
            st.warning("Insere o teu nome.")
        elif ja_jogou(user_id_input.strip(), resultados):
            dados = resultados[user_id_input.strip()]
            st.error(f"O utilizador '{user_id_input}' já participou.")
            st.info(f"Resultado anterior: {dados['score']}/20")
        else:
            st.session_state.user_id = user_id_input.strip()
            st.rerun()
    st.stop()

# ------------------------------
# ECRÃ FINAL
# ------------------------------

if st.session_state.terminou:
    score = sum(1 for idx, r in enumerate(st.session_state.respostas) if r == perguntas[idx][2])

    st.markdown('<h1 class="m-title">RESULTADO FINAL</h1>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="question-box">
        <h2 style="color:#ff8c00; font-size:40px;">{score} / 20</h2>
        <p style="font-size: 20px;">{st.session_state.user_id}, o teu desempenho foi avaliado!</p>
    </div>
    """, unsafe_allow_html=True)

    # Salvar resultados
    resultados = carregar_resultados()
    resultados[st.session_state.user_id] = {
        "score": score,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    guardar_resultados(resultados)

    st.markdown('<h2 style="text-align:center; color:#1e90ff;">QUADRO DE HONRA</h2>', unsafe_allow_html=True)
    
    ranking = sorted(resultados.items(), key=lambda x: x[1]["score"], reverse=True)
    for pos, (uid, dados) in enumerate(ranking[:5], start=1):
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.05); padding:10px; border-radius:10px; margin-bottom:5px; border-left: 4px solid #1e90ff;">
            <b>{pos}º {uid}</b> — {dados['score']} Pontos
        </div>
        """, unsafe_allow_html=True)

    if st.button("REPETIR DESAFIO"):
        st.session_state.user_id = None
        st.session_state.pergunta = 0
        st.session_state.respostas = []
        st.session_state.terminou = False
        st.rerun()
    st.stop()

# ------------------------------
# JOGO (PERGUNTAS)
# ------------------------------

idx = st.session_state.pergunta
pergunta_texto, opcoes, correta = perguntas[idx]

# Layout do Topo
st.markdown(f'<p style="text-align:center; color:#1e90ff; font-weight:bold;">NÍVEL {idx+1} / 20</p>', unsafe_allow_html=True)
st.progress((idx) / len(perguntas))

# Caixa da Pergunta
st.markdown(f"""
<div class="question-box">
    <div class="question-text">{pergunta_texto}</div>
</div>
""", unsafe_allow_html=True)

# Grelha de Respostas (A/B e C/D)
col1, col2 = st.columns(2)

for i, opcao in enumerate(opcoes, start=1):
    letra = chr(64 + i) # A, B, C, D
    target_col = col1 if i <= 2 else col2
    
    with target_col:
        # Usamos o botão do Streamlit mas o CSS acima transforma-o visualmente
        if st.button(f"{letra}: {opcao}", key=f"btn_{idx}_{i}"):
            st.session_state.respostas.append(i)
            st.session_state.pergunta += 1
            if st.session_state.pergunta >= len(perguntas):
                st.session_state.terminou = True
            st.rerun()
