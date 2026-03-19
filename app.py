import streamlit as st
import json
import os
from datetime import datetime

# ------------------------------
# 1. CONFIGURAÇÃO E CSS HEXAGONAL (ESTILO MILIONÁRIO)
# ------------------------------
st.set_page_config(page_title="Quem Quer Ser Produtivo?", layout="centered")

st.markdown("""
    <style>
    .stApp {
        background: radial-gradient(circle, #0d1b3e 0%, #02050a 100%);
        color: white;
    }
    #MainMenu, header, footer {visibility: hidden;}

    /* Título */
    .m-title {
        font-family: 'Trebuchet MS', sans-serif;
        font-size: 40px;
        font-weight: bold;
        text-align: center;
        color: white;
        text-shadow: 0 0 15px #1e90ff;
        margin-bottom: 5px;
    }

    /* Contentor da Pergunta (Hexágono Longo) */
    .question-box {
        background: linear-gradient(180deg, #0a1a3c 0%, #000000 100%);
        border: 2px solid #1e90ff;
        padding: 20px 40px;
        text-align: center;
        margin: 20px auto;
        width: 90%;
        /* Efeito de pontas cortadas (Hexágono) */
        clip-path: polygon(5% 0%, 95% 0%, 100% 50%, 95% 100%, 5% 100%, 0% 50%);
        box-shadow: 0 0 15px rgba(30, 144, 255, 0.6);
    }

    /* Botões Customizados em CSS */
    div.stButton > button {
        background: linear-gradient(90deg, #0a1a3c 0%, #1a3a7a 50%, #0a1a3c 100%) !important;
        color: white !important;
        border: 1px solid #1e90ff !important;
        height: 55px !important;
        width: 100% !important;
        font-size: 18px !important;
        font-weight: bold !important;
        /* O segredo para o formato da imagem: */
        clip-path: polygon(10% 0%, 90% 0%, 100% 50%, 90% 100%, 10% 100%, 0% 50%);
        transition: 0.3s all !important;
        margin-bottom: 10px !important;
    }

    div.stButton > button:hover {
        background: linear-gradient(90deg, #ff8c00 0%, #ff4500 100%) !important;
        border: 1px solid white !important;
        color: white !important;
        transform: scale(1.05);
    }

    /* Linhas laterais decorativas (opcional, simula a conexão) */
    .connector-line {
        height: 2px;
        background: #1e90ff;
        width: 50px;
        position: absolute;
        top: 50%;
    }
    </style>
    """, unsafe_allow_html=True)

# ------------------------------
# 2. LÓGICA DE DADOS E PERGUNTAS
# ------------------------------
RESULTADOS_FICHEIRO = "resultados.json"

def carregar_resultados():
    if not os.path.exists(RESULTADOS_FICHEIRO): return {}
    try:
        with open(RESULTADOS_FICHEIRO, "r") as f: return json.load(f)
    except: return {}

def guardar_resultados(resultados):
    with open(RESULTADOS_FICHEIRO, "w") as f: json.dump(resultados, f, indent=4)

perguntas = [
    ("Quanto tempo os profissionais passam por ano em reuniões?", ["120h", "200h", "392h", "500h"], 3),
    ("Que percentagem das reuniões é considerada improdutiva?", ["20%", "40%", "67%", "90%"], 3),
    ("Quantos profissionais têm a caixa de entrada sempre aberta?", ["20%", "50%", "80%", "95%"], 3),
    ("O excesso de conectividade provoca:", ["Mais criatividade", "Melhor comunicação", "Perda de foco e bem-estar", "Menos reuniões"], 3),
    ("O Eixo Duplo da Produtividade combina:", ["Horas extra + multitasking", "Foco individual + colaboração eficiente", "Velocidade + pressão", "Automação + reuniões"], 2),
    ("Qual NÃO é um dos 5 pilares da gestão de tempo?", ["Expandir perceção", "Demarcar limites", "Erradicar esgotamento", "Trabalhar mais horas"], 4),
    ("O método Pomodoro usa ciclos de:", ["10/10", "25/5", "40/10", "60/15"], 2),
    ("Eat the Frog significa:", ["Fazer a tarefa mais fácil", "Fazer a mais difícil de manhã", "Fazer várias tarefas", "Evitar pausas"], 2),
    ("Pareto 80/20 sugere:", ["80 tarefas em 20 min", "Eliminar 80% em 20% do tempo", "Trabalhar 80% do dia", "Fazer 20% primeiro"], 2),
    ("O cérebro faz multitasking?", ["Sim", "Não, alterna rapidamente", "Apenas com treino", "Só com música"], 2),
    ("Quantos fazem multitasking em reuniões?", ["30%", "50%", "92%", "100%"], 3),
    ("Reuniões mal planeadas:", ["São curtas", "Destroem o foco individual", "Têm poucos participantes", "Ajudam a concentração"], 2),
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
# 3. ESTADO DO JOGO
# ------------------------------
if "user_id" not in st.session_state: st.session_state.user_id = None
if "pergunta" not in st.session_state: st.session_state.pergunta = 0
if "respostas" not in st.session_state: st.session_state.respostas = []
if "terminou" not in st.session_state: st.session_state.terminou = False

resultados = carregar_resultados()

# --- LOGIN ---
if st.session_state.user_id is None:
    st.markdown('<p class="m-title">QUEM QUER SER PRODUTIVO?</p>', unsafe_allow_html=True)
    name = st.text_input("Nome do Concorrente:")
    if st.button("JOGAR"):
        if name:
            st.session_state.user_id = name
            st.rerun()
    
    st.markdown("---")
    if st.button("Limpar Histórico de Classificações"):
        if os.path.exists(RESULTADOS_FICHEIRO): os.remove(RESULTADOS_FICHEIRO)
        st.rerun()
    st.stop()

# --- JOGO ---
if not st.session_state.terminou:
    idx = st.session_state.pergunta
    q, opts, correct = perguntas[idx]

    st.markdown(f'<p style="text-align:center; color:#1e90ff;">NÍVEL {idx+1} / 20</p>', unsafe_allow_html=True)
    
    # PERGUNTA HEXAGONAL
    st.markdown(f"""<div class="question-box"><h3 style="margin:0;">{q}</h3></div>""", unsafe_allow_html=True)

    # BOTÕES HEXAGONAIS EM GRELHA
    col1, col2 = st.columns(2)
    letras = ["A", "B", "C", "D"]
    
    for i, opt in enumerate(opts):
        col = col1 if i % 2 == 0 else col2
        if col.button(f"{letras[i]}: {opt}", key=f"btn_{idx}_{i}"):
            st.session_state.respostas.append(i + 1)
            if st.session_state.pergunta < 19:
                st.session_state.pergunta += 1
            else:
                st.session_state.terminou = True
            st.rerun()

# --- FINAL ---
else:
    score = sum(1 for i, r in enumerate(st.session_state.respostas) if r == perguntas[i][2])
    st.markdown(f'<p class="m-title">PONTUAÇÃO: {score}/20</p>', unsafe_allow_html=True)
    
    # Guardar
    resultados[st.session_state.user_id] = {"score": score}
    guardar_resultados(resultados)
    
    if st.button("NOVO JOGO"):
        st.session_state.user_id = None
        st.session_state.pergunta = 0
        st.session_state.respostas = []
        st.session_state.terminou = False
        st.rerun()
