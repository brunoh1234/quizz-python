import streamlit as st
import json
import os
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIGURAÇÃO DA PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Quem Quer Ser Produtivo?",
    page_icon="🎯",
    layout="centered"
)

# ─────────────────────────────────────────────
# CSS GLOBAL — estilo "Quem Quer Ser Milionário?"
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@600;700&family=Open+Sans:wght@400;600&display=swap');

html, body, [class*="css"] {
    background-color: #0a0e1a !important;
    color: #FFFFFF;
    font-family: 'Open Sans', sans-serif;
}

.stApp {
    background: radial-gradient(ellipse at top, #0d1b3e 0%, #0a0e1a 70%);
    min-height: 100vh;
}

h1, h2, h3 {
    font-family: 'Rajdhani', sans-serif;
    letter-spacing: 0.05em;
}

/* Esconder elementos padrão do Streamlit */
#MainMenu, footer, header { visibility: hidden; }

/* Botões principais */
.stButton > button {
    background: linear-gradient(135deg, #1a3a6e, #2563eb);
    color: white;
    border: 1px solid #3b82f6;
    border-radius: 8px;
    font-weight: 700;
    font-size: 1rem;
    padding: 12px 24px;
    width: 100%;
    transition: all 0.2s ease;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #2563eb, #3b82f6);
    border-color: #60a5fa;
    box-shadow: 0 0 15px rgba(59,130,246,0.5);
    transform: translateY(-1px);
}

/* Input de texto */
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(59,130,246,0.5) !important;
    border-radius: 8px !important;
    color: white !important;
    font-size: 1rem !important;
    padding: 12px 16px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 10px rgba(59,130,246,0.3) !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PERGUNTAS DO QUIZ
# ─────────────────────────────────────────────
PERGUNTAS = [
    {
        "pergunta": "Qual é o princípio da técnica Pomodoro?",
        "opcoes": [
            "A) Trabalhar 25 minutos e descansar 5 minutos",
            "B) Trabalhar 50 minutos e descansar 10 minutos",
            "C) Trabalhar 90 minutos sem interrupções",
            "D) Fazer pausas apenas quando sentires cansaço"
        ],
        "correta": "A"
    },
    {
        "pergunta": "O que significa o Princípio de Pareto (regra 80/20) na produtividade?",
        "opcoes": [
            "A) 80% do trabalho deve ser feito de manhã",
            "B) 20% das tarefas geram 80% dos resultados",
            "C) Devemos descansar 20% do tempo total de trabalho",
            "D) 80% das reuniões são desnecessárias"
        ],
        "correta": "B"
    },
    {
        "pergunta": "O que é a técnica 'Eat the Frog'?",
        "opcoes": [
            "A) Comer bem antes de trabalhar para ter energia",
            "B) Fazer a tarefa mais difícil ou desagradável primeiro",
            "C) Dividir tarefas grandes em tarefas pequenas",
            "D) Terminar o dia com as tarefas mais simples"
        ],
        "correta": "B"
    },
    {
        "pergunta": "Qual é a duração ideal recomendada para a maioria das reuniões de equipa?",
        "opcoes": [
            "A) 2 horas",
            "B) 90 minutos",
            "C) 30 a 45 minutos",
            "D) Não tem limite, deve durar até resolver tudo"
        ],
        "correta": "C"
    },
    {
        "pergunta": "O que é o método GTD (Getting Things Done)?",
        "opcoes": [
            "A) Um sistema de gestão de e-mails",
            "B) Uma técnica para fazer exercício durante o trabalho",
            "C) Um sistema de organização de tarefas e compromissos criado por David Allen",
            "D) Um método de meditação para aumentar o foco"
        ],
        "correta": "C"
    },
    {
        "pergunta": "Qual destas opções é uma boa prática para gerir o e-mail profissional?",
        "opcoes": [
            "A) Verificar o e-mail a cada 5 minutos",
            "B) Manter o e-mail aberto em segundo plano sempre",
            "C) Definir horários específicos para verificar e responder e-mails",
            "D) Responder imediatamente a todos os e-mails recebidos"
        ],
        "correta": "C"
    },
    {
        "pergunta": "O que é o 'Deep Work' segundo Cal Newport?",
        "opcoes": [
            "A) Trabalhar em tarefas de baixo valor durante muito tempo",
            "B) Estado de concentração intensa sem distrações em tarefas cognitivamente exigentes",
            "C) Trabalhar em equipa de forma colaborativa e profunda",
            "D) Fazer horas extra além do horário laboral"
        ],
        "correta": "B"
    },
    {
        "pergunta": "Qual é o principal objetivo de uma reunião stand-up (daily)?",
        "opcoes": [
            "A) Resolver todos os problemas do projeto",
            "B) Apresentar relatórios detalhados de progresso",
            "C) Sincronização rápida da equipa sobre o que foi feito, o que vai ser feito e bloqueios",
            "D) Fazer formação e aprendizagem em equipa"
        ],
        "correta": "C"
    },
    {
        "pergunta": "O que é a Matriz de Eisenhower?",
        "opcoes": [
            "A) Uma ferramenta de planeamento financeiro",
            "B) Uma ferramenta que organiza tarefas por urgência e importância",
            "C) Um método de comunicação assertiva em reuniões",
            "D) Um sistema de avaliação de desempenho de equipas"
        ],
        "correta": "B"
    },
    {
        "pergunta": "Qual destes hábitos prejudica mais a produtividade?",
        "opcoes": [
            "A) Fazer pausas regulares",
            "B) Multitasking (fazer várias tarefas ao mesmo tempo)",
            "C) Planear o dia na véspera",
            "D) Delegar tarefas a outros"
        ],
        "correta": "B"
    },
    {
        "pergunta": "O que significa a sigla OKR na gestão de objetivos?",
        "opcoes": [
            "A) Operational Key Results",
            "B) Objectives and Key Results",
            "C) Organized Knowledge Review",
            "D) Output and Knowledge Rating"
        ],
        "correta": "B"
    },
    {
        "pergunta": "Quantas horas por dia uma pessoa consegue, em média, manter trabalho de foco profundo?",
        "opcoes": [
            "A) 8 a 10 horas",
            "B) 6 a 8 horas",
            "C) 4 a 6 horas",
            "D) 1 a 2 horas"
        ],
        "correta": "C"
    },
    {
        "pergunta": "Qual é a principal vantagem de criar uma agenda antes de uma reunião?",
        "opcoes": [
            "A) Garantir que a reunião dura mais tempo",
            "B) Permitir que mais pessoas participem",
            "C) Manter o foco, poupar tempo e preparar os participantes",
            "D) Evitar que sejam tiradas notas durante a reunião"
        ],
        "correta": "C"
    },
    {
        "pergunta": "O que é o método Kanban?",
        "opcoes": [
            "A) Uma técnica de respiração para reduzir o stress no trabalho",
            "B) Um sistema visual de gestão de fluxo de trabalho com colunas (ex: A fazer, Em curso, Feito)",
            "C) Um software de videoconferência para reuniões remotas",
            "D) Uma metodologia de avaliação de desempenho anual"
        ],
        "correta": "B"
    },
    {
        "pergunta": "Qual destas afirmações sobre notificações e produtividade é correta?",
        "opcoes": [
            "A) As notificações ajudam a manter-nos a par de tudo sem perder produtividade",
            "B) Desativar notificações durante períodos de foco pode aumentar significativamente a produtividade",
            "C) As notificações só afetam pessoas com pouca experiência profissional",
            "D) É impossível trabalhar com notificações desativadas"
        ],
        "correta": "B"
    },
    {
        "pergunta": "O que é o conceito de 'Time Blocking'?",
        "opcoes": [
            "A) Bloquear o acesso a redes sociais durante o trabalho",
            "B) Reservar blocos de tempo específicos no calendário para determinadas tarefas",
            "C) Limitar o número de tarefas numa lista de afazeres",
            "D) Usar um bloqueador de temporizador para contar o tempo de pausa"
        ],
        "correta": "B"
    },
    {
        "pergunta": "Qual é a principal razão pela qual as reuniões sem decisão são consideradas improdutivas?",
        "opcoes": [
            "A) São sempre muito longas",
            "B) Não geram resultados concretos nem avançam o trabalho",
            "C) Impedem que as pessoas usem o telemóvel",
            "D) São difíceis de agendar"
        ],
        "correta": "B"
    },
    {
        "pergunta": "O que é a 'Regra dos 2 Minutos' no contexto de produtividade?",
        "opcoes": [
            "A) Fazer pausas de 2 minutos a cada hora",
            "B) Se uma tarefa demora menos de 2 minutos, faz-a imediatamente",
            "C) Limitar as reuniões a 2 minutos por participante",
            "D) Responder a todos os e-mails em menos de 2 minutos"
        ],
        "correta": "B"
    },
    {
        "pergunta": "Qual é um sinal claro de que existe demasiadas reuniões numa organização?",
        "opcoes": [
            "A) As pessoas chegam sempre a horas às reuniões",
            "B) As reuniões têm sempre ata e próximos passos",
            "C) As pessoas não têm tempo para executar o trabalho entre reuniões",
            "D) As reuniões são sempre presenciais"
        ],
        "correta": "C"
    },
    {
        "pergunta": "Qual destas práticas contribui mais para um fim de dia de trabalho produtivo?",
        "opcoes": [
            "A) Deixar todas as tarefas para o dia seguinte",
            "B) Fazer uma revisão rápida do dia e preparar a lista de prioridades para amanhã",
            "C) Responder a todos os e-mails pendentes independentemente da hora",
            "D) Agendar reuniões para o final do dia para não interromper o trabalho"
        ],
        "correta": "B"
    },
]

TOTAL_PERGUNTAS = len(PERGUNTAS)
RESULTADOS_FILE = "resultados.json"

# ─────────────────────────────────────────────
# FUNÇÕES AUXILIARES
# ─────────────────────────────────────────────
def carregar_resultados():
    if os.path.exists(RESULTADOS_FILE):
        with open(RESULTADOS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def guardar_resultado(username, score):
    resultados = carregar_resultados()
    agora = datetime.now()
    resultados.append({
        "username": username,
        "score": score,
        "total": TOTAL_PERGUNTAS,
        "data": agora.strftime("%d/%m/%Y"),
        "hora": agora.strftime("%H:%M:%S")
    })
    with open(RESULTADOS_FILE, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

def reset_historico():
    if os.path.exists(RESULTADOS_FILE):
        os.remove(RESULTADOS_FILE)

def utilizador_ja_jogou(username):
    resultados = carregar_resultados()
    for r in resultados:
        if r.get("username", "").lower() == username.lower():
            return r
    return None

def init_state():
    defaults = {
        "pagina": "inicio",
        "username": "",
        "pergunta_atual": 0,
        "score": 0,
        "respondida": False,
        "opcao_escolhida": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ─────────────────────────────────────────────
# TÍTULO GLOBAL
# ─────────────────────────────────────────────
def render_titulo():
    st.markdown("""
        <h1 style='text-align:center; font-family:Rajdhani,sans-serif;
                   font-size:2.4rem; font-weight:800; color:#FFFFFF;
                   text-shadow:0 0 20px rgba(59,130,246,0.8);
                   letter-spacing:0.08em; margin-bottom:24px;'>
            🎯 QUEM QUER SER PRODUTIVO?
        </h1>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PÁGINA: INÍCIO
# ─────────────────────────────────────────────
def pagina_inicio():
    render_titulo()

    # Botão reset histórico (canto superior esquerdo)
    col_reset, _ = st.columns([1, 4])
    with col_reset:
        if st.button("🗑️ Reset Histórico"):
            reset_historico()
            st.rerun()

    # Card de identificação
    st.markdown("""
        <div style='
            background: rgba(13,27,62,0.8);
            border: 1px solid rgba(59,130,246,0.4);
            border-radius: 16px;
            padding: 32px;
            text-align: center;
            box-shadow: 0 0 30px rgba(59,130,246,0.15);
            margin: 0 auto 24px auto;
            max-width: 520px;
        '>
            <div style='font-size:2.5rem; margin-bottom:8px;'>👤</div>
            <h2 style='font-family:Rajdhani,sans-serif; color:#818cf8;
                       font-size:1.8rem; margin-bottom:8px;'>Identificação</h2>
            <p style='color:rgba(255,255,255,0.6); margin:0;'>
                Insere o teu nome para começar o quiz
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Formulário
    with st.container():
        nome_input = st.text_input("", placeholder="O teu nome...", label_visibility="collapsed")
        
        if st.button("▶️  COMEÇAR O QUIZ"):
            nome = nome_input.strip()
            if not nome:
                st.warning("⚠️ Insere o teu nome para continuar.")
            else:
                jogada_anterior = utilizador_ja_jogou(nome)
                if jogada_anterior:
                    st.markdown(f"""
                        <div style='background:rgba(220,38,38,0.15); border:1px solid rgba(220,38,38,0.4);
                                    border-radius:8px; padding:12px 16px; color:#f87171; margin-top:8px;'>
                            Este utilizador já jogou.
                        </div>
                        <div style='background:rgba(59,130,246,0.1); border:1px solid rgba(59,130,246,0.3);
                                    border-radius:8px; padding:12px 16px; color:#93c5fd; margin-top:6px;'>
                            Pontuação anterior: {jogada_anterior['score']}/{jogada_anterior['total']} 
                            — {jogada_anterior['data']} às {jogada_anterior['hora']}
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.session_state.username = nome
                    st.session_state.pagina = "quiz"
                    st.session_state.pergunta_atual = 0
                    st.session_state.score = 0
                    st.session_state.respondida = False
                    st.session_state.opcao_escolhida = None
                    st.rerun()

    # ── QUADRO DE LÍDERES ──────────────────────────────────────
    resultados = carregar_resultados()

    st.markdown("<div style='margin-top:40px;'></div>", unsafe_allow_html=True)

    if resultados:
        st.markdown("""
            <div style='text-align:center; margin-bottom:16px;'>
                <span style='font-size:1.6rem; font-weight:800; color:#FFD700;
                             text-shadow:0 0 10px #FFD700; font-family:Rajdhani,sans-serif;
                             letter-spacing:0.06em;'>
                    🏆 QUADRO DE LÍDERES
                </span>
            </div>
        """, unsafe_allow_html=True)

        # Ordenar: maior score → menor; em caso de empate, mais recente
        resultados_ord = sorted(
            resultados,
            key=lambda x: (-int(x.get("score", 0)), x.get("data", ""), x.get("hora", ""))
        )

        # Cabeçalho
        st.markdown("""
            <div style='display:grid; grid-template-columns:50px 1fr 120px 160px;
                        gap:8px; padding:8px 16px;
                        background:rgba(255,215,0,0.15); border-radius:8px;
                        margin-bottom:6px; font-weight:700; color:#FFD700;
                        font-size:0.82rem; text-transform:uppercase; letter-spacing:0.05em;'>
                <div>#</div><div>Jogador</div>
                <div style='text-align:center;'>Pontuação</div>
                <div style='text-align:center;'>Data / Hora</div>
            </div>
        """, unsafe_allow_html=True)

        medal = {0: "🥇", 1: "🥈", 2: "🥉"}

        for i, r in enumerate(resultados_ord):
            nome   = r.get("username", "—")
            score  = r.get("score", 0)
            total  = r.get("total", TOTAL_PERGUNTAS)
            data   = r.get("data", "—")
            hora   = r.get("hora", "—")
            pct    = (score / total * 100) if total > 0 else 0

            if i == 0:
                bg, cor_nome = "rgba(255,215,0,0.12)", "#FFD700"
            elif i == 1:
                bg, cor_nome = "rgba(192,192,192,0.10)", "#C0C0C0"
            elif i == 2:
                bg, cor_nome = "rgba(205,127,50,0.10)", "#CD7F32"
            else:
                bg, cor_nome = "rgba(255,255,255,0.04)", "#FFFFFF"

            bar_color = "#00FF88" if pct >= 70 else ("#FFD700" if pct >= 40 else "#FF4B4B")
            pos_label = medal.get(i, str(i + 1))

            st.markdown(f"""
                <div style='display:grid; grid-template-columns:50px 1fr 120px 160px;
                            gap:8px; padding:10px 16px; background:{bg};
                            border-radius:8px; margin-bottom:4px; align-items:center;
                            border:1px solid rgba(255,255,255,0.05);'>
                    <div style='font-size:1.2rem; text-align:center;'>{pos_label}</div>
                    <div style='font-weight:600; color:{cor_nome}; font-size:0.95rem;'>{nome}</div>
                    <div style='text-align:center;'>
                        <span style='font-size:1rem; font-weight:700; color:{bar_color};'>
                            {score}/{total}
                        </span>
                        <div style='background:rgba(255,255,255,0.1); border-radius:4px;
                                    height:6px; margin-top:4px;'>
                            <div style='width:{pct:.0f}%; background:{bar_color};
                                        height:6px; border-radius:4px;'></div>
                        </div>
                    </div>
                    <div style='text-align:center; font-size:0.8rem; color:rgba(255,255,255,0.55);'>
                        {data}<br>{hora}
                    </div>
                </div>
            """, unsafe_allow_html=True)

    else:
        st.markdown("""
            <div style='text-align:center; color:rgba(255,255,255,0.4); padding:24px;
                        border:1px dashed rgba(255,255,255,0.15); border-radius:10px;'>
                Ainda não há resultados. Sê o primeiro! 🚀
            </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# PÁGINA: QUIZ
# ─────────────────────────────────────────────
def pagina_quiz():
    render_titulo()

    idx   = st.session_state.pergunta_atual
    q     = PERGUNTAS[idx]
    total = TOTAL_PERGUNTAS

    # Barra de progresso
    progresso = (idx) / total
    st.markdown(f"""
        <div style='margin-bottom:8px; display:flex; justify-content:space-between;
                    font-size:0.85rem; color:rgba(255,255,255,0.5);'>
            <span>Pergunta {idx + 1} de {total}</span>
            <span>{st.session_state.score} corretas</span>
        </div>
        <div style='background:rgba(255,255,255,0.1); border-radius:6px; height:8px; margin-bottom:24px;'>
            <div style='width:{progresso*100:.0f}%;
                        background:linear-gradient(90deg,#3b82f6,#8b5cf6);
                        height:8px; border-radius:6px; transition:width 0.3s;'></div>
        </div>
    """, unsafe_allow_html=True)

    # Card da pergunta
    st.markdown(f"""
        <div style='
            background:rgba(13,27,62,0.9);
            border:1px solid rgba(59,130,246,0.4);
            border-radius:14px; padding:28px 32px;
            text-align:center; margin-bottom:24px;
            box-shadow:0 0 25px rgba(59,130,246,0.12);
        '>
            <p style='font-size:1.2rem; font-weight:600; color:#e2e8f0;
                      line-height:1.6; margin:0;'>
                {q['pergunta']}
            </p>
        </div>
    """, unsafe_allow_html=True)

    opcoes       = q["opcoes"]
    correta_letra = q["correta"]
    respondida   = st.session_state.respondida
    escolhida    = st.session_state.opcao_escolhida

    # ── ANTES DE RESPONDER: mostra botões ──
    if not respondida:
        for opcao in opcoes:
            if st.button(opcao, key=f"btn_{idx}_{opcao}"):
                letra = opcao[0]  # "A", "B", "C" ou "D"
                st.session_state.opcao_escolhida = letra
                st.session_state.respondida = True
                if letra == correta_letra:
                    st.session_state.score += 1
                st.rerun()

    # ── DEPOIS DE RESPONDER: mostra divs coloridos ──
    else:
        for opcao in opcoes:
            letra = opcao[0]
            is_correta  = (letra == correta_letra)
            is_escolhida = (letra == escolhida)

            if is_correta:
                bg     = "rgba(16,185,129,0.25)"
                border = "#10b981"
                icon   = "✅"
                cor    = "#6ee7b7"
            elif is_escolhida and not is_correta:
                bg     = "rgba(239,68,68,0.25)"
                border = "#ef4444"
                icon   = "❌"
                cor    = "#fca5a5"
            else:
                bg     = "rgba(255,255,255,0.04)"
                border = "rgba(255,255,255,0.1)"
                icon   = ""
                cor    = "rgba(255,255,255,0.5)"

            st.markdown(f"""
                <div style='
                    background:{bg}; border:1px solid {border};
                    border-radius:8px; padding:14px 18px; margin-bottom:8px;
                    color:{cor}; font-size:0.95rem; font-weight:600;
                    display:flex; align-items:center; gap:10px;
                '>
                    <span>{icon}</span> {opcao}
                </div>
            """, unsafe_allow_html=True)

        # Feedback e botão avançar
        acertou = (escolhida == correta_letra)
        if acertou:
            st.markdown("""
                <div style='text-align:center; color:#10b981; font-size:1.1rem;
                            font-weight:700; margin:16px 0;'>
                    🎉 Correto! Muito bem!
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div style='text-align:center; color:#f87171; font-size:1rem;
                            font-weight:600; margin:16px 0;'>
                    😬 Incorreto! A resposta certa era a opção <strong>{correta_letra}</strong>.
                </div>
            """, unsafe_allow_html=True)

        proxima_label = "PRÓXIMA PERGUNTA ▶️" if idx + 1 < total else "VER RESULTADO 🏁"
        if st.button(proxima_label):
            if idx + 1 < total:
                st.session_state.pergunta_atual += 1
                st.session_state.respondida = False
                st.session_state.opcao_escolhida = None
                st.rerun()
            else:
                guardar_resultado(st.session_state.username, st.session_state.score)
                st.session_state.pagina = "resultado"
                st.rerun()


# ─────────────────────────────────────────────
# PÁGINA: RESULTADO
# ─────────────────────────────────────────────
def pagina_resultado():
    render_titulo()

    score    = st.session_state.score
    total    = TOTAL_PERGUNTAS
    username = st.session_state.username
    pct      = round((score / total) * 100)

    # Classificação
    if pct == 100:
        emoji, titulo, cor = "🏆", "PERFEITO! Mestre da Produtividade!", "#FFD700"
    elif pct >= 80:
        emoji, titulo, cor = "🌟", "Excelente! Quase perfeito!", "#10b981"
    elif pct >= 60:
        emoji, titulo, cor = "👍", "Muito bom! Continua a aprender!", "#3b82f6"
    elif pct >= 40:
        emoji, titulo, cor = "📚", "Não está mau, mas há margem para melhorar!", "#f59e0b"
    else:
        emoji, titulo, cor = "💪", "Continua a tentar, vai conseguir!", "#ef4444"

    st.markdown(f"""
        <div style='
            background:rgba(13,27,62,0.9);
            border:2px solid {cor};
            border-radius:20px; padding:40px 32px;
            text-align:center;
            box-shadow:0 0 40px {cor}33;
            margin-bottom:24px;
        '>
            <div style='font-size:4rem; margin-bottom:12px;'>{emoji}</div>
            <h2 style='font-family:Rajdhani,sans-serif; color:{cor};
                       font-size:1.8rem; margin-bottom:8px;'>{titulo}</h2>
            <p style='color:rgba(255,255,255,0.7); font-size:1rem; margin-bottom:20px;'>
                {username}, obtiveste:
            </p>
            <div style='font-size:3.5rem; font-weight:800; color:{cor};
                        font-family:Rajdhani,sans-serif;
                        text-shadow:0 0 20px {cor};'>
                {score} / {total}
            </div>
            <div style='color:rgba(255,255,255,0.5); font-size:1rem; margin-top:8px;'>
                {pct}% de respostas corretas
            </div>
            <div style='background:rgba(255,255,255,0.1); border-radius:8px;
                        height:12px; margin-top:20px;'>
                <div style='width:{pct}%; background:{cor}; height:12px;
                            border-radius:8px; transition:width 0.5s;'></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 JOGAR NOVAMENTE"):
        for key in ["pagina", "username", "pergunta_atual", "score", "respondida", "opcao_escolhida"]:
            del st.session_state[key]
        st.rerun()


# ─────────────────────────────────────────────
# ROTEADOR PRINCIPAL
# ─────────────────────────────────────────────
def main():
    init_state()
    pagina = st.session_state.pagina

    if pagina == "inicio":
        pagina_inicio()
    elif pagina == "quiz":
        pagina_quiz()
    elif pagina == "resultado":
        pagina_resultado()

if __name__ == "__main__":
    main()
