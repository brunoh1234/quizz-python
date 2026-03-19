import streamlit as st
import json
import os
from datetime import datetime

# ------------------------------
# 1. CONFIGURAÇÃO E CSS "RECTÂNGULOS LARGOS"
# ------------------------------
st.set_page_config(page_title="Quem Quer Ser Produtivo?", layout="wide") # Layout wide para maior largura

st.markdown("""
    <style>
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

    /* BOTÕES DE RESPOSTA - RECTÂNGULOS LARGOS E CENTRADOS */
    div.stButton > button {
        background: linear-gradient(90deg, #0a1a3c 0%, #1a3a7a 50%, #0a1a3c 100%) !important;
        color: #ffffff !important;
        border: 1px solid #1e90ff !important;
        
        /* Aumentar altura e garantir largura total na coluna */
        height: 80px !important;
        width: 100% !important;
        
        /* Formato Hexagonal Longo */
        clip-path: polygon(8% 0%, 92% 0%, 100% 50%, 92% 100%, 8% 100%, 0% 50%);
        
        /* Centrar Texto */
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        font-size: 22px !important;
        font-weight: bold !important;
        
        transition: 0.3s all !important;
        margin-bottom: 20px !important;
    }

    div.stButton > button:hover {
        background: linear-gradient(90deg, #ff8c00 0%, #ff4500 100%) !important;
        border: 1px solid #ffffff !important;
        transform: scale(1.02);
    }

    /* Ajuste para o texto dentro do botão no Streamlit */
    div.stButton > button p {
        margin-bottom: 0px !important;
        line-height: 1.2 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ------------------------------
# 2. LOGICA (Simplificada para o exemplo)
# ------------------------------
if "pergunta" not in st.session_state: st.session_state.pergunta = 0

perguntas = [
    ("Quanto tempo os profissionais passam por ano em reuniões?", ["120h", "200h", "392h", "500h"], 3),
    # Adicionar as outras 19 aqui...
]

# --- ECRÃ DE JOGO ---
idx = st.session_state.pergunta
txt_pergunta, opcoes, correta = perguntas[idx]

st.markdown(f'<p style="text-align:center; color:#1e90ff; font-size: 20px;">NÍVEL {idx+1} / 20</p>', unsafe_allow_html=True)

# Pergunta
st.markdown(f'<div class="question-box"><h2>{txt_pergunta}</h2></div>', unsafe_allow_html=True)

# Espaçador central para afastar os botões das bordas da página
_, center_col, _ = st.columns([1, 8, 1])

with center_col:
    col1, col2 = st.columns(2)
    letras = ["A", "B", "C", "D"]
    
    for i, opt in enumerate(opcoes):
        # Distribuição: A e B na esquerda, C e D na direita (conforme imagem d15da6.png)
        target_col = col1 if i % 2 == 0 else col2
        if target_col.button(f"{letras[i]}: {opt}", key=f"q_{i}"):
            # Lógica de resposta aqui
            pass
