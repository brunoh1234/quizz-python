import streamlit as st
import streamlit.components.v1 as components
import json
import os
from datetime import datetime

RESULTADOS_FICHEIRO = "resultados.json"

# ------------------------------
# Música persistente (window.parent)
# ------------------------------
def inject_persistent_music(is_intro=False):
    """
    Injeta um player de YouTube em window.parent via iframe srcdoc (same-origin).
    O flag _ytMusicInit em window.parent garante que o player só é criado UMA VEZ,
    sobrevivendo a todos os st.rerun() do Streamlit sem quebrar a música.
    """
    import html as _html

    is_intro_js = "true" if is_intro else "false"

    script = (
        "(function(){"
        "var p=window.parent;"
        "if(p._ytMusicInit)return;"
        "p._ytMusicInit=true;"
        "var isIntro=" + is_intro_js + ";"
        "var introVid='2oPVdx3QaAM';"
        "var quizVid='ren6rd9FfV8';"
        "var d=p.document.createElement('div');"
        "d.id='_yt_persist';"
        "d.style.cssText='position:fixed;top:-9999px;left:-9999px;width:1px;height:1px;';"
        "p.document.body.appendChild(d);"
        "function build(){"
        "  var vid=isIntro?introVid:quizVid;"
        "  var pv={autoplay:1,controls:0,disablekb:1,fs:0,rel:0};"
        "  if(!isIntro){pv.loop=1;pv.playlist=quizVid;}"
        "  p._ytPlayer=new p.YT.Player('_yt_persist',{"
        "    width:'1',height:'1',videoId:vid,playerVars:pv,"
        "    events:{"
        "      onReady:function(e){e.target.setVolume(70);},"
        "      onStateChange:function(e){"
        "        if(e.data===0&&isIntro){"
        "          isIntro=false;"
        "          setTimeout(function(){"
        "            p._ytPlayer.loadVideoById(quizVid);"
        "            setTimeout(function(){p._ytPlayer.setLoop(true);},1500);"
        "          },3000);"
        "        }"
        "      }"
        "    }"
        "  });"
        "}"
        "if(p.YT&&p.YT.Player){build();}"
        "else{"
        "  p.onYouTubeIframeAPIReady=build;"
        "  var t=p.document.createElement('script');"
        "  t.src='https://www.youtube.com/iframe_api';"
        "  p.document.head.appendChild(t);"
        "}"
        "})();"
    )

    esc = _html.escape(script)
    st.markdown(
        f'<iframe srcdoc="<!DOCTYPE html><html><body>'
        f'<script>{esc}</script>'
        f'</body></html>" '
        f'style="display:none;position:absolute;width:0;height:0;" '
        f'width="0" height="0"></iframe>',
        unsafe_allow_html=True,
    )


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

/* Linha do histórico na página inicial */
.historico-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: linear-gradient(135deg, #0a1a4a 0%, #001030 100%);
    border: 1px solid #1e3a6e;
    border-radius: 10px;
    padding: 12px 20px;
    margin: 6px auto;
    max-width: 700px;
    box-shadow: 0 0 8px rgba(30, 144, 255, 0.2);
}

.historico-row.top1 { border-color: #ffd700; box-shadow: 0 0 12px rgba(255,215,0,0.4); }
.historico-row.top2 { border-color: #c0c0c0; box-shadow: 0 0 10px rgba(192,192,192,0.3); }
.historico-row.top3 { border-color: #cd7f32; box-shadow: 0 0 10px rgba(205,127,50,0.3); }

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
if "quiz_completed" not in st.session_state:
    st.session_state.quiz_completed = False
if "splash_shown" not in st.session_state:
    st.session_state.splash_shown = False


resultados = carregar_resultados()
# ------------------------------
# ECRÃ DE APRESENTAÇÃO (SPLASH)
# ------------------------------

if not st.session_state.splash_shown:

    import random as _rnd2
    _rnd2.seed(42)
    _stars = ', '.join(
        f'{_rnd2.randint(1,99)}vw {_rnd2.randint(1,99)}vh 1px 1px rgba(255,255,255,{_rnd2.uniform(0.4,1.0):.1f})'
        for _ in range(150)
    )

    # Esconde chrome do Streamlit e posiciona botão de nav fora do ecrã
    st.markdown("""
    <style>
    header[data-testid="stHeader"], [data-testid="stToolbar"], footer,
    [data-testid="stStatusWidget"], .stAppDeployButton { display: none !important; }
    [data-testid="stAppViewContainer"] > .main { background: #02050a !important; }
    .main .block-container { padding: 0 !important; max-width: 100% !important; }
    [data-testid="stButton"] {
        position: fixed !important; top: -9999px !important; left: -9999px !important;
        width: 1px !important; height: 1px !important; overflow: hidden !important; opacity: 0 !important;
    }
    iframe { border: none !important; }
    </style>
    """, unsafe_allow_html=True)

    # Botão Streamlit escondido — clicado pelo JS dentro do iframe
    if st.button("SPLASH_NAV", key="splash_nav"):
        st.session_state.splash_shown = True
        st.rerun()

    _splash_html = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
html, body {
    width:100vw; height:100vh; overflow:hidden;
    background: radial-gradient(circle at 50% 40%, #0d1b3e 0%, #02050a 100%);
    font-family: Georgia, serif;
}
.stars { position:fixed; inset:0; pointer-events:none; }
.stars::before {
    content:''; position:fixed; inset:0; width:1px; height:1px;
    background:transparent; border-radius:50%;
    box-shadow: __STARS_CSS__;
    animation: twinkle 3s infinite alternate;
}
@keyframes twinkle { from{opacity:0.3} to{opacity:1} }
.container {
    position:relative; z-index:10; display:flex; flex-direction:column;
    align-items:center; justify-content:center; height:100vh; gap:14px; padding:20px;
}
.title {
    font-size:26px; font-weight:900; letter-spacing:3px; color:#fff;
    text-shadow:0 0 20px #1e90ff, 0 0 40px #1e90ff88; text-align:center;
    animation: fadeD 0.8s ease both;
}
@keyframes fadeD { from{opacity:0;transform:translateY(-20px)} to{opacity:1;transform:translateY(0)} }
.bubble {
    background:linear-gradient(135deg,#0a1a4a,#001030); border:2px solid #1e90ff;
    border-radius:20px; padding:22px 30px; max-width:560px; width:90vw;
    text-align:center; box-shadow:0 0 30px #1e90ff55; animation: fadeS 0.8s ease 0.3s both;
}
@keyframes fadeS { from{opacity:0;transform:scale(0.95)} to{opacity:1;transform:scale(1)} }
.sl { font-size:14px; line-height:1.8; color:#d0e8ff; opacity:0; }
.sl.a1 { animation:lineIn 0.4s ease 0.8s both; }
.sl.a2 { animation:lineIn 0.4s ease 1.4s both; font-weight:bold; color:#fff; font-size:16px; }
.sl.a3 { animation:lineIn 0.4s ease 2.1s both; }
.sl.a4 { animation:lineIn 0.4s ease 2.8s both; }
.sl.a5 { animation:lineIn 0.4s ease 3.4s both; color:#ffd700; font-style:italic; font-size:13px; }
@keyframes lineIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
.char { position:relative; width:120px; height:180px; animation:float 3s ease-in-out infinite; flex-shrink:0; }
@keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-12px)} }
.ch { position:absolute; }
.head { width:60px;height:60px;top:0;left:30px;border-radius:50%;
    background:radial-gradient(circle at 40% 35%,#ffe0b2,#ffb74d);
    box-shadow:0 0 15px #1e90ff88; animation:bob 2s ease-in-out infinite; }
@keyframes bob { 0%,100%{transform:rotate(-3deg)} 50%{transform:rotate(3deg)} }
.eye { width:8px;height:8px;background:#222;border-radius:50%; }
.el { top:22px;left:14px; } .er { top:22px;left:34px; }
.mouth { width:22px;height:10px;border:3px solid #333;border-top:none;border-radius:0 0 20px 20px;top:36px;left:18px; }
.body-p { width:44px;height:70px;background:linear-gradient(180deg,#1e90ff,#0d4fa0);border-radius:8px;top:58px;left:38px; }
.arm { width:14px;height:55px;background:linear-gradient(180deg,#1e90ff,#0d4fa0);border-radius:7px; }
.al { top:60px;left:18px;transform-origin:top center;animation:wave 0.6s ease-in-out infinite alternate; }
.ar { top:60px;left:88px;transform:rotate(25deg); }
@keyframes wave { from{transform:rotate(-60deg)} to{transform:rotate(20deg)} }
.leg { width:16px;height:65px;background:linear-gradient(180deg,#0d4fa0,#082a5c);border-radius:8px;top:126px; }
.ll { left:38px;animation:legS 1.2s ease-in-out infinite alternate; }
.lr { left:66px;animation:legS 1.2s ease-in-out infinite alternate-reverse; }
@keyframes legS { from{transform:rotate(-8deg)} to{transform:rotate(8deg)} }
.enter-btn {
    margin-top:10px; padding:16px 52px; font-size:18px; font-weight:bold;
    letter-spacing:2px; color:#fff; border:2px solid #1e90ff; border-radius:14px;
    background:linear-gradient(135deg,#0a2a8a,#0d47a1);
    box-shadow:0 0 20px rgba(30,144,255,0.6), 0 0 40px rgba(30,144,255,0.3);
    cursor:pointer; font-family:Georgia,serif; transition:all 0.2s;
    animation:lineIn 0.5s ease 4.0s both;
}
.enter-btn:hover {
    background:linear-gradient(135deg,#1e90ff,#00bfff);
    box-shadow:0 0 35px rgba(30,144,255,0.9); transform:scale(1.04);
}
</style></head>
<body>
<div class="stars"></div>
<div class="container">
    <div class="title">&#127919; QUEM QUER SER PRODUTIVO?</div>
    <div class="bubble">
        <div class="sl a1">Bem-vindos ao Quiz sobre</div>
        <div class="sl a2">Boas Pr&#225;ticas em Reuni&#245;es Online Eficazes!</div>
        <div class="sl a3">Esperamos que apreciem o nosso quiz, onde poder&#227;o aprender, relaxar e descontrair.</div>
        <div class="sl a4">Um muito obrigado em nome do grupo:</div>
        <div class="sl a5">&#10024; Biljana Paiva &nbsp;&middot;&nbsp; Bruno Henriques &nbsp;&middot;&nbsp; Jorge Brito</div>
    </div>
    <div class="char">
        <div class="ch head">
            <div class="ch eye el"></div>
            <div class="ch eye er"></div>
            <div class="ch mouth"></div>
        </div>
        <div class="ch body-p"></div>
        <div class="ch arm al"></div>
        <div class="ch arm ar"></div>
        <div class="ch leg ll"></div>
        <div class="ch leg lr"></div>
    </div>
    <button class="enter-btn" onclick="enterQuiz()">&#128640; ENTRAR NO QUIZ</button>
</div>
<script>
function enterQuiz() {
    var p = window.parent;

    // Iniciar musica no parent (gesto do utilizador = browser permite autoplay)
    if (!p._ytMusicInit) {
        p._ytMusicInit = true;
        var d = p.document.createElement('div');
        d.id = '_yt_persist';
        d.style.cssText = 'position:fixed;top:-9999px;left:-9999px;width:1px;height:1px;overflow:hidden;';
        p.document.body.appendChild(d);
        var tag = p.document.createElement('script');
        tag.src = 'https://www.youtube.com/iframe_api';
        p.document.head.appendChild(tag);
        p.onYouTubeIframeAPIReady = function() {
            var isIntro = true;
            var introVid = '2oPVdx3QaAM';
            var quizVid  = 'ren6rd9FfV8';
            p._ytPlayer = new p.YT.Player('_yt_persist', {
                width: '1', height: '1', videoId: introVid,
                playerVars: { autoplay:1, controls:0, disablekb:1, fs:0, rel:0 },
                events: {
                    onReady: function(e) { e.target.setVolume(70); },
                    onStateChange: function(e) {
                        if (e.data === 0 && isIntro) {
                            isIntro = false;
                            setTimeout(function() {
                                p._ytPlayer.loadVideoById({ videoId: quizVid });
                                setTimeout(function() { p._ytPlayer.setLoop(true); }, 1000);
                            }, 500);
                        }
                    }
                }
            });
        };
    }

    // Clicar no botao de navegacao Streamlit escondido
    setTimeout(function() {
        var btns = p.document.querySelectorAll('button');
        for (var i = 0; i < btns.length; i++) {
            if (btns[i].textContent.trim() === 'SPLASH_NAV') {
                btns[i].click();
                return;
            }
        }
        if (btns.length > 0) btns[0].click();
    }, 150);
}
</script>
</body></html>"""

    _splash_html = _splash_html.replace("__STARS_CSS__", _stars)
    components.html(_splash_html, height=750, scrolling=False)
    st.stop()






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
        st.rerun()

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

        # Música persistente — sobrevive a reruns via window.parent
        inject_persistent_music(is_intro=not st.session_state.quiz_completed)

    # ------------------------------
    # HISTÓRICO DE PARTICIPANTES
    # ------------------------------

    # Recarregar para ter dados atualizados após reset
    resultados = carregar_resultados()

    if resultados:
        st.markdown("""
        <div style="text-align:center; margin-top:40px; margin-bottom:16px;">
            <span style="font-size:22px; font-weight:900; color:#7eb8ff; letter-spacing:3px; text-transform:uppercase;">
                🏅 Histórico de Participantes
            </span>
        </div>
        """, unsafe_allow_html=True)

        # Ordenar do maior para o menor score
        def score_seguro(item):
            try:
                return int(item[1].get("score", 0))
            except (ValueError, TypeError):
                return 0

        ranking = sorted(resultados.items(), key=score_seguro, reverse=True)
        medalhas = {1: "🥇", 2: "🥈", 3: "🥉"}
        classes_top = {1: "top1", 2: "top2", 3: "top3"}

        for pos, (uid, dados) in enumerate(ranking, start=1):
            medalha = medalhas.get(pos, f"#{pos}")
            classe_extra = classes_top.get(pos, "")
            score_val = score_seguro((uid, dados))
            data_val = dados.get("data", "—")
            hora_val = dados.get("hora", "—")

            # Barra de progresso
            pct = int((score_val / 20) * 100)
            if pct >= 70:
                cor_barra = "#00e676"
            elif pct >= 40:
                cor_barra = "#ffd700"
            else:
                cor_barra = "#ff5252"

            st.markdown(f"""
<div class="historico-row {classe_extra}">
    <span style="font-size:22px; min-width:40px;">{medalha}</span>
    <span style="color:#e0eaff; font-size:17px; font-weight:bold; flex:1; margin-left:12px;">{uid}</span>
    <span style="color:#aac8ff; font-size:13px; margin-right:20px;">{data_val} {hora_val}</span>
    <div style="display:flex; align-items:center; gap:10px; min-width:160px;">
        <div style="background:#0a1a3c; border-radius:6px; height:10px; width:100px; overflow:hidden; border:1px solid #1e3a6e;">
            <div style="width:{pct}%; height:100%; background:{cor_barra}; border-radius:6px;"></div>
        </div>
        <span style="color:#ffffff; font-weight:900; font-size:17px; white-space:nowrap;">{score_val}/20</span>
    </div>
</div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center; margin-top:40px; color:#3a5a8a; font-size:16px; letter-spacing:1px;">
            Ainda não há participantes. Sê o primeiro! 🚀
        </div>
        """, unsafe_allow_html=True)

    st.stop()

# Música persistente — já inicializada no login, apenas garante continuidade
inject_persistent_music(is_intro=False)

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
    st.session_state.quiz_completed = True

    # Ranking na página final
    st.markdown('<h3 style="color:#7eb8ff; text-align:center; margin-top:30px; letter-spacing:2px;">🏅 RANKING</h3>', unsafe_allow_html=True)

    def score_seguro_final(item):
        try:
            return int(item[1].get("score", 0))
        except (ValueError, TypeError):
            return 0

    ranking = sorted(resultados.items(), key=score_seguro_final, reverse=True)
    medalhas = ["🥇", "🥈", "🥉"]
    for pos, (uid, dados) in enumerate(ranking, start=1):
        medalha = medalhas[pos-1] if pos <= 3 else f"{pos}."
        destaque = "border: 2px solid #ffd700; box-shadow: 0 0 15px rgba(255,215,0,0.5);" if uid == st.session_state.user_id else ""
        score_val = score_seguro_final((uid, dados))
        st.markdown(f"""
<div class="ranking-box" style="{destaque}">
    <span style="font-size:22px;">{medalha}</span>
    <b style="color:#7eb8ff; font-size:18px; margin-left:10px;">{uid}</b>
    <span style="color:#e0eaff; float:right; font-size:18px;">{score_val}/20 pontos</span>
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

# Nome do jogador no canto superior direito
st.markdown(f"""
<div style="
    position: fixed;
    top: 16px;
    right: 20px;
    background: linear-gradient(135deg, #0a1a4a 0%, #001030 100%);
    border: 2px solid #1e90ff;
    border-radius: 10px;
    padding: 8px 18px;
    box-shadow: 0 0 15px rgba(30, 144, 255, 0.5);
    z-index: 9999;
    display: flex;
    align-items: center;
    gap: 8px;
">
    <span style="font-size: 18px;">👤</span>
    <span style="color: #7eb8ff; font-size: 15px; font-weight: bold; letter-spacing: 1px;">{st.session_state.user_id}</span>
</div>
""", unsafe_allow_html=True)

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
