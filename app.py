import streamlit as st
import json
import os
from datetime import datetime

# ------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO MILIONÁRIO
# ------------------------------
st.set_page_config(page_title="Quem Quer Ser Produtivo?", layout="centered")

st.markdown("""
    <style>
    /* Esconder menus padrão */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Fundo Escuro e Gradiente */
    .stApp {
        background: radial-gradient(circle, #0d1b3e 0%, #02050a 100%);
        color: #ffffff;
    }

    /* Título Estilo Logo */
    .m-title {
        font-family: 'Trebuchet MS', sans-serif;
        font-size: 45px;
        font-weight: bold;
        text-align: center;
        color: #ffffff;
        text-transform: uppercase;
        letter-spacing: 4px;
        margin-top: 20px;
        text-shadow: 0 0 20px #1e90ff, 0 0 30px #1e90ff;
    }

    .m-subtitle {
        text-align: center;
        color: #ff8c00;
        font-size: 18px;
        letter-spacing: 8px;
        margin-bottom: 30px;
        font-weight: bold;
    }

    /* Caixa da Pergunta */
    .question-container {
        background: linear-gradient(180deg, #0a1a3c 0%, #000000 100%);
        border: 2px solid #5d8aa8;
        border-radius: 50px / 25px;
        padding: 25px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 0 15px rgba(30, 144, 255, 0.4);
    }

    /* BOTÕES DE RESPOSTA (O SEGREDO DO DESIGN) */
    div.stButton > button {
        background: linear-gradient(90deg, #0a1a3c 0%, #1a3a7a 50%, #0a1a3c 100%) !important;
        color: #ffffff !important;
        border: 2px solid #1e90ff !important;
        border-radius: 40px !important; /* Forma alongada/hexagonal */
        height: 65px !important;
        width: 100% !important;
        font-size: 20px !important;
        font-weight: bold !important;
        margin-bottom: 15px !important;
        transition: 0.3s all !important;
        box-shadow: 0 0 10px rgba(30, 144, 255, 0.3) !important;
    }

    div.stButton > button:hover {
        background: linear-gradient(90deg, #ff8c00 0%, #ff4500 100%) !important;
        border-color: #ffffff !important;
        transform: scale(1.05);
        box-shadow: 0 0 20px #ff8c00 !important;
        color: white !important;
    }

    /* Inputs de texto */
    .stTextInput input {
        background-color: #0a1a3c !important;
        color: white !important;
        border: 1px solid #1e90ff !important;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

RESULTADOS_FICHEIRO = "resultados.json"

# ------------------------------
# 2. FUNÇÕES AUXILIARES
# ------------------------------
def carregar_resultados():
    if not os.path.exists(RESULTADOS_FICHEIRO): return {}
    try:
        with open(RESULTADOS_FICHEIRO, "r") as f: return json.load(f)
    except: return {}

def guardar_resultados(resultados):
    with open(RESULTADOS_FICHEIRO, "w") as f: json.dump(resultados, f, indent=4)

def resetar_historico():
    if os.path.exists(RESULTADOS_FICHEIRO):
        os.remove(RESULTADOS_FICHEIRO)

# ------------------------------
# 3. BASE DE PERGUNTAS
# ------------------------------
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
# 4. ESTADO DO JOGO
# ------------------------------
if "user_id" not in st.session_state: st.session_state.user_id = None
if "pergunta" not in st.session_state: st.session_state.pergunta = 0
if "respostas" not in st.session_state: st.session_state.respostas = []
if "terminou" not in st.session_state: st.session_state.terminou = False

resultados = carregar_resultados()

# --- ECRÃ DE LOGIN ---
if st.session_state.user_id is None:
    st.markdown('<p class="m-title">QUEM QUER SER</p>', unsafe_allow_html=True)
    st.markdown('<p class="m-subtitle">PRODUTIVO?</p>', unsafe_allow_html=True)
    
    user_name = st.text_input("Introduza o seu nome para começar o concurso:", placeholder="O seu nome aqui...")
    
    if st.button("COMEÇAR O DESAFIO"):
        if not user_name.strip():
            st.warning("⚠️ Insere um nome para entrar no palco.")
        elif user_name.strip() in resultados:
            st.error("❌ Este utilizador já participou.")
        else:
            st.session_state.user_id = user_name.strip()
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.expander("🛠 GESTÃO (LIMPAR HISTÓRICO)"):
        if st.button("🗑 APAGAR TODA A BASE DE DADOS"):
            resetar_historico()
            st.success("Dados eliminados!")
            st.rerun()
    st.stop()

# --- ECRÃ DE PERGUNTAS ---
if not st.session_state.terminou:
    idx = st.session_state.pergunta
    txt_pergunta, opcoes, correta = perguntas[idx]

    st.markdown(f'<p style="text-align:center; color:#1e90ff;">NÍVEL {idx+1} DE 20</p>', unsafe_allow_html=True)
    st.progress((idx) / 20)

    # Caixa de Pergunta Estilo Milionário
    st.markdown(f"""
        <div class="question-container">
            <h3 style="color: white; font-size: 26px;">{txt_pergunta}</h3>
        </div>
    """, unsafe_allow_html=True)

    # Colunas de Resposta (A/B e C/D)
    col1, col2 = st.columns(2)
    letras = ["A", "B", "C", "D"]
    
    for i, opt in enumerate(opcoes):
        col_atual = col1 if i < 2 else col2
        if col_atual.button(f"{letras[i]}: {opt}", key=f"btn_{idx}_{i}"):
            st.session_state.respostas.append(i + 1)
            if st.session_state.pergunta < 19:
                st.session_state.pergunta += 1
            else:
                st.session_state.terminou = True
            st.rerun()

# --- ECRÃ FINAL ---
else:
    score = sum(1 for i, r in enumerate(st.session_state.respostas) if r == perguntas[i][2])
    
    st.markdown('<p class="m-title">RESULTADO FINAL</p>', unsafe_allow_html=True)
    st.markdown(f'<h1 style="text-align:center; color:#ff8c00; font-size: 60px;">{score} / 20</h1>', unsafe_allow_html=True)

    # Guardar no arquivo
    res = carregar_resultados()
    res[st.session_state.user_id] = {"score": score, "time": datetime.now().strftime("%d/%m/%Y %H:%M")}
    guardar_resultados(res)

    st.markdown("<br><h2 style='text-align:center; color:#1e90ff;'>TOP 5 CONCORRENTES</h2>", unsafe_allow_html=True)
    ranking = sorted(res.items(), key=lambda x: x[1]['score'], reverse=True)
    for p, (name, data) in enumerate(ranking[:5], 1):
        st.markdown(f"""
            <div style="background: rgba(30,144,255,0.1); padding:10px; border-radius:15px; margin-bottom:10px; border-left: 5px solid #ff8c00; padding-left:20px;">
                <b>{p}º {name}</b> — {data['score']} Pontos
            </div>
        """, unsafe_allow_html=True)

    if st.button("NOVO JOGADOR / SAIR"):
        st.session_state.user_id = None
        st.session_state.pergunta = 0
        st.session_state.respostas = []
        st.session_state.terminou = False
        st.rerun()
