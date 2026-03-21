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
        "var transVid='iahlZ4g6RQc';"
        "var quizVid='ren6rd9FfV8';"
        "var phase=isIntro?0:2;"
        "var d=p.document.createElement('div');"
        "d.id='_yt_persist';"
        "d.style.cssText='position:fixed;top:-9999px;left:-9999px;width:1px;height:1px;';"
        "p.document.body.appendChild(d);"
        "function build(){"
        "  var vid=phase===0?introVid:quizVid;"
        "  var pv={autoplay:1,controls:0,disablekb:1,fs:0,rel:0};"
        "  p._ytPlayer=new p.YT.Player('_yt_persist',{"
        "    width:'1',height:'1',videoId:vid,playerVars:pv,"
        "    events:{"
        "      onReady:function(e){e.target.setVolume(70);},"
        "      onStateChange:function(e){"
        "        if(e.data===0){"
        "          if(phase===0){phase=1;p._ytPlayer.loadVideoById(transVid);}"
        "          else if(phase===1){phase=2;p._ytPlayer.loadVideoById(quizVid);}"
        "          else if(phase===2){p._ytPlayer.playVideo();}"
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
# Toggle de Som persistente
# ------------------------------
def inject_sound_toggle():
    """
    Injeta um botao 🔊/🔇 fixo no ecra via window.parent (persiste entre reruns).
    O estado e guardado em window.parent._soundEnabled.
    """
    import html as _html
    script = (
        "(function(){"
        "var p=window.parent;"
        "if(p._soundToggleInit)return;"
        "p._soundToggleInit=true;"
        "if(p._soundEnabled===undefined)p._soundEnabled=true;"
        "var btn=p.document.createElement('button');"
        "btn.id='_sound_toggle_btn';"
        "btn.textContent=p._soundEnabled?'\U0001F50A':'\U0001F507';"
        "btn.title='Ligar/Desligar som';"
        "btn.style.cssText="
        "'position:fixed;top:60px;right:20px;z-index:99999;"
        "background:rgba(0,0,0,0.55);border:1px solid rgba(255,255,255,0.18);"
        "color:white;border-radius:50%;width:38px;height:38px;font-size:17px;"
        "cursor:pointer;transition:all 0.2s;box-shadow:0 2px 8px rgba(0,0,0,0.4);';"
        "btn.onmouseenter=function(){btn.style.background='rgba(80,80,80,0.75)';};"
        "btn.onmouseleave=function(){btn.style.background='rgba(0,0,0,0.55)';};"
        "btn.onclick=function(){"
        "  p._soundEnabled=!p._soundEnabled;"
        "  btn.textContent=p._soundEnabled?'\U0001F50A':'\U0001F507';"
        "};"
        "p.document.body.appendChild(btn);"
        "})();"
    )
    esc = _html.escape(script)
    st.markdown(
        '<iframe srcdoc="<!DOCTYPE html><html><body>'
        '<script>' + esc + '</script>'
        '</body></html>" '
        'style="display:none;position:absolute;width:0;height:0;" '
        'width="0" height="0"></iframe>',
        unsafe_allow_html=True,
    )


def play_sfx(sound_type: str, key: str):
    """
    Toca um som (correct / wrong / timeout) via components.html() que corre
    num iframe e acede a window.parent para Web Audio API + duck da musica.
    key  -- string unica (ex: "sfx_correct_gameid_3") para garantir execucao 1x.
    """
    import streamlit.components.v1 as _comp
    if sound_type == "correct":
        sound_js = """
      [523.25,659.25,783.99].forEach(function(freq,i){
        var o=ctx.createOscillator(),g=ctx.createGain();
        o.connect(g);g.connect(ctx.destination);
        o.frequency.value=freq;o.type='sine';
        var t=ctx.currentTime+i*0.14;
        g.gain.setValueAtTime(0,t);
        g.gain.linearRampToValueAtTime(0.45,t+0.03);
        g.gain.exponentialRampToValueAtTime(0.001,t+0.55);
        o.start(t);o.stop(t+0.55);
      });"""
    elif sound_type == "wrong":
        sound_js = """
      // Três notas descendentes suaves (Lá4 → Fá4 → Ré4) — estilo quiz clássico
      [
        {freq:440, delay:0.0},
        {freq:349, delay:0.22},
        {freq:293, delay:0.44}
      ].forEach(function(n){
        var o=ctx.createOscillator(),g=ctx.createGain();
        o.connect(g);g.connect(ctx.destination);
        o.type='sine';
        o.frequency.value=n.freq;
        var t=ctx.currentTime+n.delay;
        g.gain.setValueAtTime(0,t);
        g.gain.linearRampToValueAtTime(0.35,t+0.04);
        g.gain.setValueAtTime(0.35,t+0.16);
        g.gain.exponentialRampToValueAtTime(0.001,t+0.38);
        o.start(t);o.stop(t+0.4);
      });"""
    elif sound_type == "timeout":
        sound_js = """
      [0,0.4].forEach(function(delay){
        var o=ctx.createOscillator(),g=ctx.createGain();
        o.connect(g);g.connect(ctx.destination);
        o.type='square';o.frequency.value=130;
        var t=ctx.currentTime+delay;
        g.gain.setValueAtTime(0,t);
        g.gain.linearRampToValueAtTime(0.25,t+0.02);
        g.gain.exponentialRampToValueAtTime(0.001,t+0.3);
        o.start(t);o.stop(t+0.3);
      });"""
    else:
        return

    html_code = f"""<!DOCTYPE html><html><body><script>
(function(){{
  var p=window.parent;
  var k='{key}';
  if(localStorage.getItem(k))return;
  localStorage.setItem(k,'1');
  if(p._soundEnabled===false)return;
  if(p._ytPlayer&&p._ytPlayer.setVolume){{
    p._ytPlayer.setVolume(15);
    setTimeout(function(){{if(p._ytPlayer&&p._ytPlayer.setVolume)p._ytPlayer.setVolume(70);}},2800);
  }}
  try{{
    var ctx=new(p.AudioContext||p.webkitAudioContext)();
    {sound_js}
  }}catch(e){{console.log('sfx err:',e);}}
}})();
</script></body></html>"""
    _comp.html(html_code, height=0)



def play_confetti(key: str, mode: str = "burst"):
    """
    Dispara confetti na página pai via iframe.
    mode='burst'       — pequena explosão (resposta certa)
    mode='celebration' — chuva contínua 3s (fim com boa pontuação)
    key                — chave única para não repetir no mesmo rerun
    """
    import streamlit.components.v1 as _comp
    if mode == "burst":
        confetti_js = """
        p.confetti({particleCount:120,spread:80,origin:{y:0.55},
          colors:['#ffd700','#00e676','#1e90ff','#ff6b6b','#ffffff']});
        """
    else:  # celebration
        confetti_js = """
        var end=Date.now()+3200;
        (function frame(){
          p.confetti({particleCount:4,angle:60,spread:55,origin:{x:0},
            colors:['#ffd700','#1e90ff','#00e676']});
          p.confetti({particleCount:4,angle:120,spread:55,origin:{x:1},
            colors:['#ffd700','#ff6b6b','#ffffff']});
          if(Date.now()<end) requestAnimationFrame(frame);
        })();
        """

    html_code = f"""<!DOCTYPE html><html><body><script>
(function(){{
  var p=window.parent;
  var k='{key}';
  if(localStorage.getItem(k))return;
  localStorage.setItem(k,'1');
  function fire(){{
    try{{ {confetti_js} }}catch(e){{console.log('confetti err:',e);}}
  }}
  if(p.confetti){{
    fire();
  }}else{{
    var s=p.document.createElement('script');
    s.src='https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.3/dist/confetti.browser.min.js';
    s.onload=fire;
    p.document.head.appendChild(s);
  }}
}})();
</script></body></html>"""
    _comp.html(html_code, height=0)


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
    ("Quantas horas são gastas, em média, em reuniões por ano?",
     ["150 horas", "392 horas", "280 horas", "500 horas"], 1),
    ("Qual é a percentagem de reuniões que são consideradas ineficazes?",
     ["33%", "45%", "67%", "80%"], 2),
    ("O vídeo descreve o tempo gasto em reuniões como um 'autêntico imposto sobre o...':",
     ["Trabalho", "Rendimento", "Tempo", "Dinheiro"], 2),
    ("Qual é o 'filtro essencial' mencionado para evitar a perda de tempo?",
     ["Enviar uma agenda por e-mail", "Começar sempre com uma pergunta estratégica", "Limitar a reunião a 15 minutos", "Proibir o uso de telemóveis"], 1),
    ("Segundo o fluxograma apresentado, o que deve fazer se o objetivo for apenas 'informar'?",
     ["Marcar uma reunião curta", "Enviar um e-mail", "Fazer uma chamada telefónica", "Agendar uma apresentação"], 1),
    ("Em que situação é que o vídeo indica que 'faz sentido' marcar uma reunião?",
     ["Quando o objetivo é decidir", "Quando quer apresentar um relatório longo", "Todas as segundas-feiras por rotina", "Para fazer apresentações informais"], 0),
    ("Que tipo de reuniões o vídeo sugere explicitamente que devem ser deixadas para trás?",
     ["Reuniões presenciais", "Reuniões virtuais", "Reuniões tóxicas", "Reuniões de equipa"], 2),
    ("Qual é o objetivo das novas sessões propostas para substituir o modelo atual?",
     ["Ter mais participantes e opiniões", "Serem sessões mais longas e detalhadas", "Serem sessões de alto impacto com foco e decisões", "Substituírem todos os e-mails da empresa"], 2),
    ("O que significa a expressão 'respeitar a ecologia do dia'?",
     ["Reduzir o consumo de energia no escritório", "Proteger o que temos de mais valioso: o tempo", "Trabalhar apenas em ambientes sustentáveis", "Organizar a agenda por cores"], 1),
    ("Qual é considerado o nosso bem mais valioso no contexto da produtividade?",
     ["O dinheiro", "A tecnologia", "O nosso tempo", "A rede de contactos"], 2)
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

/* ── FADE IN entre perguntas ── */
@keyframes fadeInQuestion {
  from { opacity: 0; transform: translateY(18px); }
  to   { opacity: 1; transform: translateY(0); }
}
.question-box {
  animation: fadeInQuestion 0.45s cubic-bezier(0.22, 1, 0.36, 1);
}
.answer-btn-wrap, .stButton > button {
  animation: fadeInQuestion 0.45s cubic-bezier(0.22, 1, 0.36, 1);
}
.result-box {
  animation: fadeInQuestion 0.35s cubic-bezier(0.22, 1, 0.36, 1);
}


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
.answer-option.pending-selected {
    background: linear-gradient(135deg, #1a4a7a 0%, #0d2a4a 100%);
    border-color: #ffd700;
    box-shadow: 0 0 20px rgba(255,215,0,0.55), inset 0 0 12px rgba(255,215,0,0.12);
    animation: pulse-gold 1s ease-in-out infinite;
}
.answer-option.pending-dimmed {
    background: linear-gradient(135deg, #0d1520 0%, #080f18 100%);
    border-color: #1a2a50;
    opacity: 0.65;
}
@keyframes pulse-gold {
    0%, 100% { box-shadow: 0 0 20px rgba(255,215,0,0.55); }
    50%       { box-shadow: 0 0 36px rgba(255,215,0,0.90); }
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

# (reset handler removido — feito diretamente no botão)

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
if "pendente_resposta" not in st.session_state:
    st.session_state.pendente_resposta = None
if "mostrar_resultado_ts" not in st.session_state:
    st.session_state.mostrar_resultado_ts = None
if "quiz_completed" not in st.session_state:
    st.session_state.quiz_completed = False
if "tempos_pergunta" not in st.session_state:
    st.session_state.tempos_pergunta = []
if "historico_quiz" not in st.session_state:
    st.session_state.historico_quiz = []
if "ver_revisao" not in st.session_state:
    st.session_state.ver_revisao = False
if "splash_shown" not in st.session_state:
    st.session_state.splash_shown = False
if "game_id" not in st.session_state:
    import uuid as _uuid
    st.session_state.game_id = _uuid.uuid4().hex[:8]


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
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 260" width="220" height="180" style="animation:float 3s ease-in-out infinite;filter:drop-shadow(0 0 18px #1e90ff88);flex-shrink:0;">
  <defs>
    <!-- Skin gradient -->
    <radialGradient id="skin" cx="45%" cy="35%" r="55%">
      <stop offset="0%" stop-color="#FFCC99"/>
      <stop offset="100%" stop-color="#E8956E"/>
    </radialGradient>
    <!-- Shirt gradient -->
    <linearGradient id="shirt" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#2563EB"/>
      <stop offset="100%" stop-color="#1D4ED8"/>
    </linearGradient>
    <!-- Chair gradient -->
    <linearGradient id="chair" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#1e3a6e"/>
      <stop offset="100%" stop-color="#0d1f3c"/>
    </linearGradient>
    <!-- Desk gradient -->
    <linearGradient id="desk" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#1a2a50"/>
      <stop offset="100%" stop-color="#0f1830"/>
    </linearGradient>
    <!-- Monitor gradient -->
    <linearGradient id="monitor" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#0a1628"/>
      <stop offset="100%" stop-color="#050c18"/>
    </linearGradient>
    <!-- Screen glow -->
    <filter id="glow">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <!-- Screen glow strong -->
    <filter id="glowStrong">
      <feGaussianBlur stdDeviation="6" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <!-- Shadow -->
    <filter id="shadow">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#00000066"/>
    </filter>
    <!-- Face avatars on screen -->
    <radialGradient id="face1" cx="40%" cy="35%" r="60%">
      <stop offset="0%" stop-color="#FBBF8A"/>
      <stop offset="100%" stop-color="#D97706"/>
    </radialGradient>
    <radialGradient id="face2" cx="40%" cy="35%" r="60%">
      <stop offset="0%" stop-color="#93C5FD"/>
      <stop offset="100%" stop-color="#3B82F6"/>
    </radialGradient>
    <radialGradient id="face3" cx="40%" cy="35%" r="60%">
      <stop offset="0%" stop-color="#86EFAC"/>
      <stop offset="100%" stop-color="#22C55E"/>
    </radialGradient>
  </defs>

  <!-- ===== CHAIR ===== -->
  <rect x="100" y="195" width="80" height="10" rx="4" fill="url(#chair)" filter="url(#shadow)"/>
  <rect x="118" y="200" width="8" height="35" rx="3" fill="#132040"/>
  <rect x="154" y="200" width="8" height="35" rx="3" fill="#132040"/>
  <rect x="106" y="232" width="70" height="8" rx="4" fill="#0d1830"/>
  <!-- Chair back -->
  <rect x="115" y="145" width="10" height="55" rx="4" fill="#132040"/>
  <rect x="155" y="145" width="10" height="55" rx="4" fill="#132040"/>
  <rect x="108" y="143" width="64" height="45" rx="8" fill="url(#chair)" opacity="0.85"/>

  <!-- ===== DESK ===== -->
  <rect x="40" y="185" width="240" height="14" rx="6" fill="url(#desk)" filter="url(#shadow)"/>
  <rect x="52" y="196" width="10" height="40" rx="4" fill="#0d1830"/>
  <rect x="258" y="196" width="10" height="40" rx="4" fill="#0d1830"/>

  <!-- ===== PERSON BODY ===== -->
  <!-- Body/torso -->
  <rect x="121" y="130" width="38" height="58" rx="10" fill="url(#shirt)" filter="url(#shadow)"/>
  <!-- Collar/neck detail -->
  <rect x="136" y="128" width="8" height="14" rx="3" fill="url(#skin)"/>
  <!-- Shirt detail line -->
  <line x1="140" y1="138" x2="140" y2="168" stroke="#1e4db7" stroke-width="1.5" opacity="0.5"/>

  <!-- Left arm (down on desk) -->
  <rect x="100" y="145" width="22" height="42" rx="10" fill="url(#shirt)"/>
  <!-- Left hand on keyboard -->
  <ellipse cx="111" cy="187" rx="13" ry="7" fill="url(#skin)"/>
  <!-- Right arm (reaching keyboard) -->
  <rect x="158" y="148" width="22" height="40" rx="10" fill="url(#shirt)"/>
  <!-- Right hand on keyboard -->
  <ellipse cx="169" cy="188" rx="13" ry="7" fill="url(#skin)"/>

  <!-- ===== HEAD ===== -->
  <ellipse cx="140" cy="105" rx="28" ry="30" fill="url(#skin)" filter="url(#shadow)"/>
  <!-- Hair -->
  <ellipse cx="140" cy="82" rx="28" ry="16" fill="#1a0a00"/>
  <rect x="112" y="82" width="56" height="12" rx="0" fill="#1a0a00"/>
  <!-- Eyes -->
  <ellipse cx="130" cy="103" rx="4.5" ry="5" fill="white"/>
  <ellipse cx="150" cy="103" rx="4.5" ry="5" fill="white"/>
  <ellipse cx="131" cy="104" rx="3" ry="3.5" fill="#1a0a00"/>
  <ellipse cx="151" cy="104" rx="3" ry="3.5" fill="#1a0a00"/>
  <!-- Eye shine -->
  <circle cx="132" cy="102.5" r="1" fill="white"/>
  <circle cx="152" cy="102.5" r="1" fill="white"/>
  <!-- Eyebrows -->
  <path d="M126 96 Q130 93 134 96" stroke="#3D1500" stroke-width="2" fill="none" stroke-linecap="round"/>
  <path d="M146 96 Q150 93 154 96" stroke="#3D1500" stroke-width="2" fill="none" stroke-linecap="round"/>
  <!-- Smile -->
  <path d="M133 115 Q140 121 147 115" stroke="#C0654A" stroke-width="2" fill="none" stroke-linecap="round"/>
  <!-- Ears -->
  <ellipse cx="112" cy="107" rx="5" ry="8" fill="url(#skin)"/>
  <ellipse cx="168" cy="107" rx="5" ry="8" fill="url(#skin)"/>
  <!-- Headset -->
  <path d="M115 85 Q140 68 165 85" stroke="#1e90ff" stroke-width="3.5" fill="none"/>
  <rect x="109" y="101" width="9" height="13" rx="4" fill="#1a3a7a" stroke="#1e90ff" stroke-width="1.5"/>
  <rect x="162" y="101" width="9" height="13" rx="4" fill="#1a3a7a" stroke="#1e90ff" stroke-width="1.5"/>
  <!-- Mic boom -->
  <path d="M110 112 Q95 125 98 133" stroke="#1a3a7a" stroke-width="2.5" fill="none" stroke-linecap="round"/>
  <circle cx="98" cy="135" r="4" fill="#1e90ff" opacity="0.9"/>

  <!-- ===== MONITOR ===== -->
  <!-- Monitor stand -->
  <rect x="137" y="178" width="6" height="10" rx="2" fill="#0a1220"/>
  <rect x="127" y="184" width="26" height="4" rx="2" fill="#0a1220"/>
  <!-- Monitor frame -->
  <rect x="62" y="80" width="156" height="102" rx="10" fill="#0a1628" stroke="#1e3a70" stroke-width="2" filter="url(#shadow)"/>
  <!-- Screen area -->
  <rect x="68" y="86" width="144" height="90" rx="6" fill="url(#monitor)"/>
  <!-- Screen glow effect -->
  <rect x="68" y="86" width="144" height="90" rx="6" fill="none" stroke="#1e90ff" stroke-width="1" opacity="0.4"/>

  <!-- ===== VIDEO CALL TILES ON SCREEN ===== -->
  <!-- Tile 1 - top left -->
  <rect x="74" y="91" width="64" height="40" rx="5" fill="#0d1e40" stroke="#1e3a70" stroke-width="1"/>
  <!-- Person in tile 1 -->
  <circle cx="106" cy="104" r="10" fill="url(#face1)"/>
  <rect x="94" y="116" width="24" height="14" rx="4" fill="#c2410c"/>
  <!-- Face features tile 1 -->
  <circle cx="102" cy="102" r="2" fill="#5C2900"/>
  <circle cx="110" cy="102" r="2" fill="#5C2900"/>
  <path d="M102 108 Q106 112 110 108" stroke="#5C2900" stroke-width="1.5" fill="none" stroke-linecap="round"/>
  <!-- Name label tile 1 -->
  <rect x="74" y="123" width="64" height="8" rx="2" fill="#0a1628" opacity="0.8"/>
  <rect x="78" y="125" width="30" height="4" rx="2" fill="#3B82F6" opacity="0.7"/>

  <!-- Tile 2 - top right -->
  <rect x="144" y="91" width="62" height="40" rx="5" fill="#0d1e40" stroke="#1e3a70" stroke-width="1"/>
  <!-- Person in tile 2 -->
  <circle cx="175" cy="104" r="10" fill="url(#face2)"/>
  <rect x="163" y="116" width="24" height="14" rx="4" fill="#1D4ED8"/>
  <!-- Face features tile 2 -->
  <circle cx="171" cy="102" r="2" fill="#1a4a8a"/>
  <circle cx="179" cy="102" r="2" fill="#1a4a8a"/>
  <path d="M171 108 Q175 112 179 108" stroke="#1a4a8a" stroke-width="1.5" fill="none" stroke-linecap="round"/>
  <!-- Name label tile 2 -->
  <rect x="144" y="123" width="62" height="8" rx="2" fill="#0a1628" opacity="0.8"/>
  <rect x="148" y="125" width="28" height="4" rx="2" fill="#3B82F6" opacity="0.7"/>

  <!-- Tile 3 - bottom left -->
  <rect x="74" y="137" width="64" height="36" rx="5" fill="#0d1e40" stroke="#1e3a70" stroke-width="1"/>
  <!-- Person in tile 3 -->
  <circle cx="106" cy="150" r="9" fill="url(#face3)"/>
  <rect x="95" y="161" width="22" height="11" rx="4" fill="#166534"/>
  <!-- Face features tile 3 -->
  <circle cx="102" cy="148" r="2" fill="#14532d"/>
  <circle cx="110" cy="148" r="2" fill="#14532d"/>
  <path d="M102 154 Q106 158 110 154" stroke="#14532d" stroke-width="1.5" fill="none" stroke-linecap="round"/>
  <!-- Name label tile 3 -->
  <rect x="74" y="166" width="64" height="8" rx="2" fill="#0a1628" opacity="0.8"/>
  <rect x="78" y="168" width="25" height="4" rx="2" fill="#3B82F6" opacity="0.7"/>

  <!-- Tile 4 - bottom right (self view - highlighted) -->
  <rect x="144" y="137" width="62" height="36" rx="5" fill="#0a1a3a" stroke="#1e90ff" stroke-width="1.5"/>
  <!-- Camera off icon -->
  <text x="175" y="157" text-anchor="middle" font-size="16" fill="#1e90ff" opacity="0.5">📷</text>
  <!-- "Você" label -->
  <rect x="144" y="166" width="62" height="8" rx="2" fill="#0a1628" opacity="0.8"/>
  <text x="175" y="173" text-anchor="middle" font-size="6" fill="#1e90ff">Você</text>

  <!-- ===== KEYBOARD ===== -->
  <rect x="95" y="186" width="90" height="14" rx="4" fill="#0d1628" stroke="#1a2a50" stroke-width="1"/>
  <!-- Keyboard keys -->
  <rect x="99" y="188" width="6" height="4" rx="1" fill="#1a3060"/><rect x="107" y="188" width="6" height="4" rx="1" fill="#1a3060"/>
  <rect x="115" y="188" width="6" height="4" rx="1" fill="#1a3060"/><rect x="123" y="188" width="6" height="4" rx="1" fill="#1a3060"/>
  <rect x="131" y="188" width="6" height="4" rx="1" fill="#1a3060"/><rect x="139" y="188" width="6" height="4" rx="1" fill="#1a3060"/>
  <rect x="147" y="188" width="6" height="4" rx="1" fill="#1a3060"/><rect x="155" y="188" width="6" height="4" rx="1" fill="#1a3060"/>
  <rect x="163" y="188" width="6" height="4" rx="1" fill="#1a3060"/><rect x="171" y="188" width="6" height="4" rx="1" fill="#1a3060"/>
  <rect x="107" y="194" width="66" height="4" rx="1" fill="#1a3060"/>

  <!-- ===== FLOATING ELEMENTS ===== -->
  <!-- WiFi signal -->
  <g opacity="0.7" transform="translate(252, 82)">
    <path d="M0 12 Q10 2 20 12" stroke="#1e90ff" stroke-width="2.5" fill="none" stroke-linecap="round"/>
    <path d="M3 16 Q10 9 17 16" stroke="#1e90ff" stroke-width="2" fill="none" stroke-linecap="round"/>
    <circle cx="10" cy="19" r="2.5" fill="#1e90ff"/>
  </g>

  <!-- Chat bubble floating -->
  <g transform="translate(255, 120)">
    <rect x="0" y="0" width="38" height="24" rx="8" fill="#0d2060" stroke="#1e90ff" stroke-width="1.5" opacity="0.9"/>
    <polygon points="6,24 14,24 10,30" fill="#0d2060" stroke="#1e90ff" stroke-width="1" stroke-linejoin="round"/>
    <rect x="6" y="7" width="26" height="3" rx="1.5" fill="#3B82F6" opacity="0.8"/>
    <rect x="6" y="13" width="18" height="3" rx="1.5" fill="#3B82F6" opacity="0.5"/>
  </g>

  <!-- ===== CSS ANIMATIONS ===== -->
  <style>
    /* Typing animation on keyboard */
    @keyframes type {
      0%,100% { opacity:0.6; transform: translateY(0); }
      50% { opacity:1; transform: translateY(1px); }
    }
    /* Screen pulse -->
    @keyframes screenPulse {
      0%,100% { opacity:0.4; }
      50% { opacity:0.8; }
    }
    /* Head bob -->
    @keyframes headBob {
      0%,100% { transform: translateY(0) rotate(0deg); }
      25% { transform: translateY(-2px) rotate(-1.5deg); }
      75% { transform: translateY(-1px) rotate(1deg); }
    }
    /* Float chat bubble */
    @keyframes floatBubble {
      0%,100% { transform: translate(255px, 120px); }
      50% { transform: translate(255px, 114px); }
    }
    /* Mic pulse -->
    @keyframes micPulse {
      0%,100% { opacity:0.9; r:4; }
      50% { opacity:1; r:5.5; }
    }
    /* Typing dots on tile */
    @keyframes dot1 { 0%,100%{opacity:0.2} 20%{opacity:1} }
    @keyframes dot2 { 0%,100%{opacity:0.2} 40%{opacity:1} }
    @keyframes dot3 { 0%,100%{opacity:0.2} 60%{opacity:1} }
    /* Screen glow animation */
    @keyframes glowBorder {
      0%,100% { opacity:0.4; }
      50% { opacity:0.9; }
    }

    /* Apply animations -->
    .head-group { animation: headBob 3s ease-in-out infinite; transform-origin: 140px 130px; }
    .chat-bubble { animation: floatBubble 2.5s ease-in-out infinite; }
    .mic-circle { animation: micPulse 1.5s ease-in-out infinite; }
    .screen-border { animation: glowBorder 2s ease-in-out infinite; }
    .key1 { animation: type 1.2s ease-in-out infinite; transform-origin: 102px 190px; }
    .key2 { animation: type 1.2s ease-in-out infinite 0.1s; transform-origin: 110px 190px; }
    .key3 { animation: type 1.2s ease-in-out infinite 0.2s; transform-origin: 118px 190px; }
    .key4 { animation: type 1.2s ease-in-out infinite 0.15s; }
    .wifi-icon { animation: glowBorder 2s ease-in-out infinite; }
  </style>
</svg>
    <button class="enter-btn" onclick="enterQuiz()">&#128640; ENTRAR NO QUIZ</button>
</div>
<style>
#countdown-overlay {
    display:none; position:fixed; inset:0; z-index:9999;
    background:radial-gradient(circle at 50% 50%, #0d1b3e 0%, #02050a 100%);
    align-items:center; justify-content:center; flex-direction:column;
}
#countdown-overlay.active { display:flex; }
.cd-number {
    font-size:200px; font-weight:900; font-family:Georgia,serif;
    color:#fff; text-shadow:0 0 60px #1e90ff, 0 0 120px #1e90ff88;
    animation:cdPop 0.9s ease forwards;
    letter-spacing:-5px; line-height:1;
}
@keyframes cdPop {
    0%   { transform:scale(2.5); opacity:0; }
    30%  { transform:scale(1);   opacity:1; }
    70%  { transform:scale(1);   opacity:1; }
    100% { transform:scale(0.4); opacity:0; }
}
.cd-label {
    font-size:18px; letter-spacing:4px; color:#1e90ff;
    text-transform:uppercase; margin-top:10px;
    text-shadow:0 0 15px #1e90ff;
    animation:fadeLabel 0.5s ease 0.2s both;
}
@keyframes fadeLabel { from{opacity:0} to{opacity:1} }
.cd-ring {
    position:absolute; width:280px; height:280px;
    border:3px solid #1e90ff44; border-radius:50%;
    box-shadow:0 0 40px #1e90ff33;
    animation:ringPulse 0.9s ease forwards;
}
@keyframes ringPulse {
    0%   { transform:scale(0.3); opacity:0; }
    30%  { transform:scale(1);   opacity:1; }
    70%  { transform:scale(1);   opacity:0.6; }
    100% { transform:scale(1.8); opacity:0; }
}
.cd-word {
    font-size:72px; font-weight:700; font-family:Georgia,serif;
    color:#fff; letter-spacing:6px; text-align:center;
    text-shadow:0 0 30px #1e90ff, 0 0 60px #1e90ff44;
    animation:wordPop 0.85s ease forwards;
}
@keyframes wordPop {
    0%   { transform:translateY(30px) scale(0.8); opacity:0; }
    20%  { transform:translateY(0)    scale(1);   opacity:1; }
    70%  { transform:translateY(0)    scale(1);   opacity:1; }
    100% { transform:translateY(-30px) scale(0.8); opacity:0; }
}
.cd-go {
    font-size:100px; font-weight:900; font-family:Georgia,serif;
    letter-spacing:8px; color:#ffd700;
    text-shadow:0 0 60px #ffd700, 0 0 120px #ffa50088;
    animation:goAnim 0.8s ease forwards;
}
@keyframes goAnim {
    0%   { transform:scale(0.5); opacity:0; }
    50%  { transform:scale(1.15); opacity:1; }
    100% { transform:scale(1);   opacity:1; }
}
</style>
<div id="countdown-overlay">
    <div class="cd-ring" id="cd-ring" style="opacity:0"></div>
    <div id="cd-content" class="cd-word" style="opacity:0"></div>
    <div class="cd-label" id="cd-label" style="opacity:0"></div>
</div>
<script>
function enterQuiz() {
    var p = window.parent;

    // --- INICIAR MUSICA (gesto direto do utilizador = autoplay permitido) ---
    if (!p._ytMusicInit) {
        p._ytMusicInit = true;
        p._ytPhase = 1; // começa já na fase 1 (transição) — intro foi durante o splash
        var d = p.document.createElement('div');
        d.id = '_yt_persist';
        d.style.cssText = 'position:fixed;top:-9999px;left:-9999px;width:1px;height:1px;overflow:hidden;';
        p.document.body.appendChild(d);
        function buildPlayer() {
            var transVid = 'iahlZ4g6RQc';
            var quizVid  = 'ren6rd9FfV8';
            p._ytPlayer = new p.YT.Player('_yt_persist', {
                width:'1', height:'1', videoId: transVid,
                playerVars: { autoplay:1, controls:0, disablekb:1, fs:0, rel:0 },
                events: {
                    onReady: function(e) { e.target.setVolume(70); },
                    onStateChange: function(e) {
                        if (e.data === 0) {
                            if (p._ytPhase === 1) {
                                p._ytPhase = 2;
                                p._ytPlayer.loadVideoById(quizVid);
                            } else if (p._ytPhase === 2) {
                                p._ytPlayer.playVideo(); // loop
                            }
                        }
                    }
                }
            });
        }
        if (p.YT && p.YT.Player) { buildPlayer(); }
        else {
            p.onYouTubeIframeAPIReady = buildPlayer;
            var tag = p.document.createElement('script');
            tag.src = 'https://www.youtube.com/iframe_api';
            p.document.head.appendChild(tag);
        }
    }

    // --- COUNTDOWN SINCRONIZADO COM A MÚSICA ---
    var overlay = document.getElementById('countdown-overlay');
    var cdContent = document.getElementById('cd-content');
    var cdLabel   = document.getElementById('cd-label');
    var cdRing    = document.getElementById('cd-ring');
    overlay.classList.add('active');

    // Timestamps em segundos: palavras karaoke + números
    var steps = [
        { time: 1,  text:'WELCOME',    lbl:'', cls:'cd-word',   ring:false },
        { time: 2,  text:'LADIES',     lbl:'', cls:'cd-word',   ring:false },
        { time: 3,  text:'AND',        lbl:'', cls:'cd-word',   ring:false },
        { time: 4,  text:'GENTLEMEN',  lbl:'', cls:'cd-word',   ring:false },
        { time: 5,  text:'THE',        lbl:'', cls:'cd-word',   ring:false },
        { time: 6,  text:'SHOW',       lbl:'', cls:'cd-word',   ring:false },
        { time: 7,  text:'STARTS',     lbl:'', cls:'cd-word',   ring:false },
        { time: 8,  text:'IN',         lbl:'', cls:'cd-word',   ring:false },
        { time: 9,  text:'3',          lbl:'PREPARAR', cls:'cd-number', ring:true },
        { time: 11, text:'2',          lbl:'ATENÇÃO',  cls:'cd-number', ring:true },
        { time: 13, text:'1',          lbl:'JÁ!',      cls:'cd-number', ring:true },
        { time: 15, text:'GO!',        lbl:'',         cls:'cd-go',     ring:false }
    ];
    var stepShown = [false, false, false, false];
    var navigated = false;

    function showCdStep(s) {
        cdContent.className = s.cls;
        cdContent.style.animation = 'none';
        cdRing.style.animation = 'none';
        void cdContent.offsetWidth; // reflow
        cdContent.textContent = s.text;
        cdLabel.textContent   = s.lbl;
        cdContent.style.opacity = '1';
        cdLabel.style.opacity = s.lbl ? '1' : '0';
        cdContent.style.animation = '';
        if (s.ring) {
            cdRing.style.opacity = '1';
            cdRing.style.animation = '';
        } else {
            cdRing.style.opacity = '0';
            cdRing.style.animation = 'none';
        }
    }

    function showIntroVideo() {
        // ─── VÍDEO EM ECRÃ CHEIO (sem controlos YouTube visíveis) ───
        // Parar a música de transição no player pai
        try { p._ytPlayer.pauseVideo(); } catch(e) {}

        overlay.style.background = '#000';
        overlay.style.overflow = 'hidden';

        overlay.innerHTML =
        '<style>' +
        '.vf-wrap{position:absolute;inset:0;background:#000;overflow:hidden}' +
        // Truque para cobrir o ecrã todo: 177.78vh = 16/9 * 100vh
        '.vf-sizer{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);' +
        'width:177.78vh;height:100vh;min-width:100%;min-height:56.25vw}' +
        '@media(max-aspect-ratio:16/9){.vf-sizer{width:100vw;height:56.25vw;min-height:100vh}}' +
        '#vf-player-el{width:100%;height:100%;pointer-events:none}' +
        // Camada de fade para escurecer no fim
        '#vf-fade{position:absolute;inset:0;background:#000;opacity:0;pointer-events:none;z-index:30;transition:opacity 1.5s ease}' +
        // Mensagem a aparecer nos 5 segundos finais
        '#vf-msg{position:absolute;bottom:60px;left:50%;transform:translateX(-50%);' +
        'font-size:clamp(14px,2vw,22px);color:#8ab8ff;letter-spacing:4px;font-family:Georgia,serif;' +
        'text-transform:uppercase;opacity:0;transition:opacity 1s ease;z-index:40;text-align:center;' +
        'text-shadow:0 0 20px #1e90ff}' +
        '</style>' +
        '<div class="vf-wrap">' +
        '<div class="vf-sizer"><div id="vf-player-el"></div></div>' +
        '<div id="vf-fade"></div>' +
        '<div id="vf-msg">✦ A PREPARAR O QUIZ ✦</div>' +
        '</div>';

        function startVidPlayer() {
            new YT.Player('vf-player-el', {
                videoId: '2oPVdx3QaAM',
                playerVars: {
                    autoplay: 1,
                    controls: 0,
                    modestbranding: 1,
                    rel: 0,
                    showinfo: 0,
                    iv_load_policy: 3,
                    disablekb: 1,
                    fs: 0,
                    playsinline: 1,
                    cc_load_policy: 0
                },
                events: {
                    onReady: function(e) {
                        e.target.setVolume(90);
                    },
                    onStateChange: function(e) {
                        if (e.data === 0) {
                            // Vídeo terminou — fade para preto + mensagem
                            var fd = document.getElementById('vf-fade');
                            var msg = document.getElementById('vf-msg');
                            if (fd) fd.style.opacity = '1';
                            if (msg) msg.style.opacity = '1';
                            // 5 segundos depois: música quiz em loop + navegar para login
                            setTimeout(function() {
                                try {
                                    p._ytPlayer.loadVideoById({videoId: 'ren6rd9FfV8', startSeconds: 0});
                                    p._ytPhase = 2;
                                } catch(ex) {}
                                navigateToLogin();
                            }, 5000);
                        }
                    }
                }
            });
        }

        if (window.YT && window.YT.Player) {
            startVidPlayer();
        } else {
            window.onYouTubeIframeAPIReady = startVidPlayer;
            var tag = document.createElement('script');
            tag.src = 'https://www.youtube.com/iframe_api';
            document.head.appendChild(tag);
        }
    }

    function navigateToLogin() {
        var btns = p.document.querySelectorAll('button');
        for (var i = 0; i < btns.length; i++) {
            if (btns[i].textContent.trim() === 'SPLASH_NAV') {
                btns[i].click(); return;
            }
        }
        if (btns.length > 0) btns[0].click();
    }

    // Polling a cada 100ms para verificar o tempo atual da música
    var cdInterval = setInterval(function() {
        var player = p._ytPlayer;
        if (!player || typeof player.getCurrentTime !== 'function') return;
        var t = player.getCurrentTime();

        for (var i = 0; i < steps.length; i++) {
            if (!stepShown[i] && t >= steps[i].time) {
                stepShown[i] = true;
                showCdStep(steps[i]);
            }
        }

        // Após o GO! ao segundo 20 → mostrar vídeo 2oPVdx3QaAM
        if (!navigated && t >= 20) {
            navigated = true;
            clearInterval(cdInterval);
            showIntroVideo();
        }
    }, 100);
}
</script>
</body></html>"""

    _splash_html = _splash_html.replace("__STARS_CSS__", _stars)
    components.html(_splash_html, height=750, scrolling=False)
    st.stop()






# Título principal
st.markdown('<div class="main-title">🎯 QUEM QUER SER PRODUTIVO?</div>', unsafe_allow_html=True)

# ── Scroll-to-top após "Jogar Novamente" ─────────────────────────────────
if st.session_state.get("needs_scroll_top", False):
    st.session_state.needs_scroll_top = False
    import time as _t_scroll
    _scroll_nonce = int(_t_scroll.time() * 1000)
    components.html(f"""
<script>
(function(){{
    var _n = {_scroll_nonce};  // nonce para forçar novo iframe
    function doScroll() {{
        try {{
            var p = window.parent;
            var sel = [
                'section.main',
                '[data-testid="stMain"]',
                '[data-testid="stAppViewContainer"]',
                '.main',
                '.block-container'
            ];
            for (var i = 0; i < sel.length; i++) {{
                var el = p.document.querySelector(sel[i]);
                if (el) {{ el.scrollTop = 0; if(el.scrollTo) el.scrollTo({{top:0,behavior:'instant'}}); }}
            }}
            p.scrollTo(0, 0);
            p.document.documentElement.scrollTop = 0;
            p.document.body.scrollTop = 0;
        }} catch(e) {{}}
    }}
    doScroll();
    var count = 0;
    var iv = setInterval(function() {{
        doScroll();
        count++;
        if (count >= 30) clearInterval(iv);
    }}, 80);
}})();
</script>
""", height=50)

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
                st.info(f"Pontuação anterior: {dados['score']}/10 — {dados['data']} às {dados['hora']}")
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
            pct = int((score_val / 10) * 100)
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
        <span style="color:#ffffff; font-weight:900; font-size:17px; white-space:nowrap;">{score_val}/10</span>
    </div>
</div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center; margin-top:40px; color:#3a5a8a; font-size:16px; letter-spacing:1px;">
            Ainda não há participantes. Sê o primeiro! 🚀
        </div>
        """, unsafe_allow_html=True)

    # ── Auto-refresh de 30s via Python puro (sem pacotes externos) ──
    import time as _time_hist
    if 'hist_last_refresh' not in st.session_state:
        st.session_state.hist_last_refresh = _time_hist.time()
    _elapsed = _time_hist.time() - st.session_state.hist_last_refresh
    _remaining = max(0, 30 - int(_elapsed))
    _pct = int(_remaining / 30 * 100)
    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:center;gap:10px;padding:10px 0;">
        <span style="color:#7eb8ff;font-size:13px;">🔄 Atualiza em</span>
        <div style="width:120px;height:6px;background:#0a1a3c;border-radius:4px;overflow:hidden;border:1px solid #1e3a6e;">
            <div style="height:100%;width:{_pct}%;background:#1e90ff;border-radius:4px;transition:width 1s linear;"></div>
        </div>
        <span style="color:#fff;font-weight:bold;font-size:13px;">{_remaining}s</span>
    </div>
    """, unsafe_allow_html=True)
    if _remaining <= 0:
        st.session_state.hist_last_refresh = _time_hist.time()
        _time_hist.sleep(0.3)
        st.rerun()
    else:
        _time_hist.sleep(1)
        st.rerun()

    st.stop()

# Segurança: se user_id ainda for None, parar completamente
if st.session_state.user_id is None:
    st.stop()

# Música persistente — já inicializada no login, apenas garante continuidade
inject_persistent_music(is_intro=False)
inject_sound_toggle()

# ------------------------------
# ECRÃ FINAL
# ------------------------------

if st.session_state.terminou and st.session_state.get("user_id") is not None:
    hist  = st.session_state.historico_quiz
    score = sum(1 for h in hist if h["dada"] == h["correta"])
    total = len(perguntas)
    tempos = st.session_state.tempos_pergunta
    avg_t  = round(sum(tempos) / len(tempos), 1) if tempos else 0

    if score == total:
        msg = "🏆 PERFEITO! Domínio total do tema!"
        cor = "#ffd700"
    elif score >= total * 0.7:
        msg = "🥇 Muito bom! Forte domínio do conteúdo."
        cor = "#00e676"
    elif score >= total * 0.5:
        msg = "🥈 Bom esforço! Ainda há espaço para melhorar."
        cor = "#1e90ff"
    else:
        msg = "🥉 Continua a praticar — estás no caminho certo!"
        cor = "#ff9800"

    # ── Guardar resultado ────────────────────────────────────────────────────
    resultados = carregar_resultados()
    if st.session_state.user_id not in resultados:
        resultados[st.session_state.user_id] = {
            "score": score,
            "data": datetime.now().strftime("%d/%m/%Y"),
            "hora": datetime.now().strftime("%H:%M:%S")
        }
        guardar_resultados(resultados)
    st.session_state.quiz_completed = True
    if score >= total * 0.7:
        play_confetti(f"conf_end_{st.session_state.get('game_id','g')}", mode="celebration")

    # ── CSS extra para o ecrã de resultados ─────────────────────────────────
    st.markdown("""
<style>
.stats-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin: 22px 0;
}
.stat-card {
    background: linear-gradient(135deg, #0d1f4a 0%, #050e2a 100%);
    border: 1px solid #1e3a7a;
    border-radius: 14px;
    padding: 18px 10px;
    text-align: center;
}
.stat-card .stat-val  { font-size: 34px; font-weight: 900; color: #ffffff; }
.stat-card .stat-lbl  { font-size: 12px; color: #7eb8ff; letter-spacing: 1.5px; margin-top: 4px; }
.review-item {
    background: linear-gradient(135deg, #0a1a3a 0%, #040d20 100%);
    border-radius: 14px;
    padding: 18px 22px;
    margin-bottom: 16px;
    border-left: 5px solid #1e3a7a;
    animation: fadeInQuestion 0.4s ease;
}
.review-item.acertou  { border-left-color: #00e676; }
.review-item.errou    { border-left-color: #ff4444; }
.review-item.timeout  { border-left-color: #ff9800; }
.review-q   { font-size: 16px; color: #e0eaff; font-weight: 700; margin-bottom: 12px; }
.review-opt { font-size: 14px; padding: 7px 14px; border-radius: 8px; margin: 4px 0; }
.opt-correct { background: rgba(0,230,118,0.15); border: 1px solid #00e676; color: #00e676; }
.opt-wrong   { background: rgba(255,68,68,0.15);  border: 1px solid #ff4444; color: #ff4444; }
.opt-neutral { background: rgba(255,255,255,0.04); border: 1px solid #1e3a7a; color: #7eb8ff; }
.review-time { font-size: 12px; color: #5a7ab0; margin-top: 10px; }
.q-summary-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 14px;
    border-radius: 10px;
    margin: 4px 0;
    background: rgba(255,255,255,0.03);
}
</style>
    """, unsafe_allow_html=True)

    # ── Caixa principal ──────────────────────────────────────────────────────
    st.markdown(f"""
<div class="final-box">
    <h2 style="color:#ffd700; font-size:32px; text-shadow: 0 0 20px rgba(255,215,0,0.8);">
        🎉 Quiz Concluído!
    </h2>
    <p style="font-size:22px; color:{cor}; font-weight:bold; margin:15px 0;">
        {st.session_state.user_id}
    </p>
    <p style="font-size:52px; font-weight:900; color:#ffffff; text-shadow: 0 0 20px gold; margin:10px 0;">
        {score} / {total}
    </p>
    <p style="font-size:20px; color:#aac8ff;">{msg}</p>
</div>
    """, unsafe_allow_html=True)

    # ── Stats grid ───────────────────────────────────────────────────────────
    acertos  = score
    erros    = sum(1 for h in hist if h["dada"] != h["correta"] and h["dada"] != -1)
    timeouts = sum(1 for h in hist if h["dada"] == -1)
    pct      = round((score / total) * 100)

    st.markdown(f"""
<div class="stats-grid">
    <div class="stat-card">
        <div class="stat-val" style="color:#00e676;">✅ {acertos}</div>
        <div class="stat-lbl">CERTAS</div>
    </div>
    <div class="stat-card">
        <div class="stat-val" style="color:#ff4444;">❌ {erros}</div>
        <div class="stat-lbl">ERRADAS</div>
    </div>
    <div class="stat-card">
        <div class="stat-val" style="color:#ffd700;">{pct}%</div>
        <div class="stat-lbl">PRECISÃO</div>
    </div>
    <div class="stat-card">
        <div class="stat-val" style="color:#1e90ff;">{avg_t}s</div>
        <div class="stat-lbl">TEMPO MÉDIO</div>
    </div>
    <div class="stat-card">
        <div class="stat-val" style="color:#ff9800;">⏰ {timeouts}</div>
        <div class="stat-lbl">TEMPO ESGOTADO</div>
    </div>
    <div class="stat-card">
        <div class="stat-val" style="color:#c084fc;">{sum(tempos):.0f}s</div>
        <div class="stat-lbl">TEMPO TOTAL</div>
    </div>
</div>
    """, unsafe_allow_html=True)

    # ── Resumo rápido por pergunta ───────────────────────────────────────────
    st.markdown('<h3 style="color:#7eb8ff; text-align:center; margin:24px 0 12px; letter-spacing:2px;">📋 RESUMO</h3>', unsafe_allow_html=True)
    for i, h in enumerate(hist, 1):
        if h["dada"] == h["correta"]:
            icon, cor_r = "✅", "#00e676"
        elif h["dada"] == -1:
            icon, cor_r = "⏰", "#ff9800"
        else:
            icon, cor_r = "❌", "#ff4444"
        letras_rev = ["A","B","C","D"]
        resp_str = letras_rev[h["dada"]] if h["dada"] >= 0 else "—"
        st.markdown(f"""
<div class="q-summary-row">
    <span style="font-size:18px;">{icon}</span>
    <span style="color:#7eb8ff; font-weight:700; min-width:28px;">#{i}</span>
    <span style="color:#c8d8ff; flex:1; font-size:14px;">{h["pergunta"][:80]}{"..." if len(h["pergunta"])>80 else ""}</span>
    <span style="color:{cor_r}; font-size:13px; white-space:nowrap;">⏱ {h["tempo"]}s</span>
</div>
        """, unsafe_allow_html=True)

    # ── Botão ver revisão detalhada ──────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    col_r1, col_r2, col_r3 = st.columns([1, 2, 1])
    with col_r2:
        label_rev = "🙈 Esconder Revisão" if st.session_state.ver_revisao else "🔍 Ver Revisão Detalhada"
        if st.button(label_rev, key="btn_revisao", use_container_width=True):
            st.session_state.ver_revisao = not st.session_state.ver_revisao
            st.rerun()

    # ── Revisão detalhada ────────────────────────────────────────────────────
    if st.session_state.ver_revisao:
        st.markdown('<h3 style="color:#7eb8ff; text-align:center; margin:28px 0 16px; letter-spacing:2px;">🔍 REVISÃO DETALHADA</h3>', unsafe_allow_html=True)
        letras_rev = ["A","B","C","D"]
        for i, h in enumerate(hist, 1):
            if h["dada"] == h["correta"]:
                classe, titulo = "acertou", f"✅ Pergunta {i} — Certa!"
                t_cor = "#00e676"
            elif h["dada"] == -1:
                classe, titulo = "timeout", f"⏰ Pergunta {i} — Tempo Esgotado"
                t_cor = "#ff9800"
            else:
                classe, titulo = "errou", f"❌ Pergunta {i} — Errada"
                t_cor = "#ff4444"

            opts_html = ""
            for j, op in enumerate(h["opcoes"]):
                if j == h["correta"]:
                    css = "opt-correct"
                    prefix = "✅ "
                elif j == h["dada"] and h["dada"] != h["correta"]:
                    css = "opt-wrong"
                    prefix = "❌ "
                else:
                    css = "opt-neutral"
                    prefix = f"{letras_rev[j]}. "
                opts_html += f'<div class="review-opt {css}">{prefix}{op}</div>'

            st.markdown(f"""
<div class="review-item {classe}">
    <div style="color:{t_cor}; font-size:14px; font-weight:700; letter-spacing:1px; margin-bottom:8px;">{titulo}</div>
    <div class="review-q">{h["pergunta"]}</div>
    {opts_html}
    <div class="review-time">⏱ Respondido em {h["tempo"]}s</div>
</div>
            """, unsafe_allow_html=True)

    # ── Ranking ──────────────────────────────────────────────────────────────
    st.markdown('<h3 style="color:#7eb8ff; text-align:center; margin-top:30px; letter-spacing:2px;">🏅 RANKING</h3>', unsafe_allow_html=True)
    def score_seguro_final(item):
        try:
            return int(item[1].get("score", 0))
        except (ValueError, TypeError):
            return 0

    ranking = sorted(resultados.items(), key=score_seguro_final, reverse=True)
    medalhas = ["🥇", "🥈", "🥉"]
    for pos, (uid, dados) in enumerate(ranking, start=1):
        medalha   = medalhas[pos-1] if pos <= 3 else f"{pos}."
        destaque  = "border: 2px solid #ffd700; box-shadow: 0 0 15px rgba(255,215,0,0.5);" if uid == st.session_state.user_id else ""
        score_val = score_seguro_final((uid, dados))
        st.markdown(f"""
<div class="ranking-box" style="{destaque}">
    <span style="font-size:22px;">{medalha}</span>
    <b style="color:#7eb8ff; font-size:18px; margin-left:10px;">{uid}</b>
    <span style="color:#e0eaff; float:right; font-size:18px;">{score_val}/{total} pontos</span>
</div>
        """, unsafe_allow_html=True)

    # ── Botão jogar novamente ────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Jogar Novamente", use_container_width=True):
            # Limpar TODOS os estados para garantir página inicial limpa
            import uuid as _uuid2
            for _k in list(st.session_state.keys()):
                del st.session_state[_k]
            # Preservar: splash já visto → vai direto para identificação
            st.session_state.splash_shown     = True
            # Flag para forçar scroll-to-top na home page
            st.session_state.needs_scroll_top = True
            st.rerun()

    st.stop()

# ------------------------------
# ECRÃ DA PERGUNTA
# ------------------------------

idx = st.session_state.pergunta
pergunta, opcoes, correta = perguntas[idx]

# Inicializar timer_start_ms quando muda de pergunta ou primeira vez
import time as _time
_timer_key = f"timer_start_ms_{idx}"
if _timer_key not in st.session_state:
    # Limpar timers de perguntas anteriores
    for k in list(st.session_state.keys()):
        if k.startswith("timer_start_ms_") and k != _timer_key:
            del st.session_state[k]
    st.session_state[_timer_key] = int(_time.time() * 1000)
_timer_start_ms = st.session_state[_timer_key]
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

# ── TIMER CIRCULAR (60 segundos) ──────────────────────────────────────────────
# Botão oculto que o JavaScript clica quando o tempo expira
timer_expired = st.button("⏰", key=f"timer_exp_{idx}", help="timer")
if timer_expired:
    # Timeout: save 60s and question data
    st.session_state.tempos_pergunta.append(60.0)
    st.session_state.historico_quiz.append({
        "pergunta": pergunta,
        "opcoes": opcoes,
        "correta": correta,
        "dada": -1,
        "tempo": 60.0,
    })
    st.session_state.respostas.append(-1)
    st.session_state.resposta_dada = -1   # -1 = sem resposta (tempo esgotado)
    st.rerun()

# CSS para esconder o botão do timer e manter componente compacto
st.markdown("""
<style>
div[data-testid="stButton"] > button[title="timer"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# Timer circular via components.html — usa localStorage para persistir entre reruns
_is_paused  = False  # timer nunca pausa ao selecionar resposta — só para ao confirmar
_is_stopped = st.session_state.resposta_dada is not None  # resposta confirmada → congela timer
_timer_html = f"""
<style>
@keyframes timerPulse {{
  0%,100% {{ transform: scale(1); }}
  50%      {{ transform: scale(1.12); }}
}}
</style>
<div style="display:flex;justify-content:center;align-items:center;margin:0 0 8px 0;">
  <div id="timer-wrap" style="position:relative;width:110px;height:110px;">
    <svg width="110" height="110" viewBox="0 0 110 110">
      <!-- Fundo do anel -->
      <circle cx="55" cy="55" r="48" fill="#0a1220"
              stroke="#1a2a50" stroke-width="9"/>
      <!-- Arco animado do tempo restante -->
      <circle id="timer-arc" cx="55" cy="55" r="48"
              fill="none" stroke="#00e676" stroke-width="9"
              stroke-linecap="round"
              stroke-dasharray="301.6" stroke-dashoffset="0"
              transform="rotate(-90 55 55)"
              style="transition:stroke-dashoffset 0.5s linear, stroke 0.5s;"/>
      <!-- Número central -->
      <text id="timer-num" x="55" y="62"
            text-anchor="middle" dominant-baseline="middle"
            font-size="32" font-weight="900" fill="#ffffff"
            font-family="Arial Black, sans-serif">60</text>
    </svg>
  </div>
</div>
<script>
(function(){{
  var TOTAL      = 60;
  var FROZEN_KEY = "quiz_timer_frozen_{idx}";
  // startTs vem sempre do Python (session_state) — nunca do localStorage
  var startTs    = {_timer_start_ms};
  var IS_STOPPED = {'true' if _is_stopped else 'false'};

  var arc  = document.getElementById("timer-arc");
  var num  = document.getElementById("timer-num");
  var wrap = document.getElementById("timer-wrap");
  var CIRC = 2 * Math.PI * 48;

  // ── Paragem definitiva (resposta confirmada) ──────────────────────
  if (IS_STOPPED) {{
    var frozenRaw = localStorage.getItem(FROZEN_KEY);
    var frozenRem;
    if (frozenRaw) {{
      frozenRem = parseFloat(frozenRaw);
    }} else {{
      frozenRem = Math.max(0, TOTAL - (Date.now() - startTs) / 1000);
      localStorage.setItem(FROZEN_KEY, frozenRem.toString());
    }}
    var frozenSecs = Math.ceil(frozenRem);
    var frozenPct  = frozenRem / TOTAL;
    arc.style.transition = "none";
    arc.style.stroke = "#555555";
    arc.style.strokeDashoffset = CIRC * (1 - frozenPct);
    num.textContent = frozenSecs;
    num.style.fill  = "#555555";
    return;
  }}

  localStorage.removeItem(FROZEN_KEY);

  var timerDone = false;

  function getRemaining() {{
    return Math.max(0, TOTAL - (Date.now() - startTs) / 1000);
  }}

  function tick() {{
    var remaining = getRemaining();
    var secs = Math.ceil(remaining);
    num.textContent = secs;

    var pct = remaining / TOTAL;
    arc.style.strokeDashoffset = CIRC * (1 - pct);

    if (remaining > 20) {{
      arc.style.stroke = "#00e676";
      num.style.fill   = "#ffffff";
      wrap.style.animation = "none";
    }} else if (remaining > 10) {{
      arc.style.stroke = "#ffd700";
      num.style.fill   = "#ffd700";
      wrap.style.animation = "none";
    }} else {{
      arc.style.stroke = "#ff4444";
      num.style.fill   = "#ff4444";
      wrap.style.animation = remaining > 0 ? "timerPulse 0.55s ease-in-out infinite" : "none";
    }}

    if (remaining <= 0 && !timerDone) {{
      timerDone = true;
      var btns = window.parent.document.querySelectorAll("button");
      for (var b of btns) {{
        if (b.textContent.trim() === "⏰") {{ b.click(); break; }}
      }}
    }}
  }}

  tick();
  var iv = setInterval(function() {{
    tick();
    if (getRemaining() <= 0) clearInterval(iv);
  }}, 500);
}})();
</script>
"""

# Limpar o timer do localStorage quando a pergunta muda (nova pergunta = novo timer)
import streamlit.components.v1 as components
components.html(_timer_html, height=130, scrolling=False)

# ── TECLADO: A/B/C/D seleciona, Enter confirma ───────────────────────────────
_keyboard_html = f"""
<script>
(function() {{
  // Evitar duplicar listeners
  if (window._kbListenerActive) return;
  window._kbListenerActive = true;

  function getParentDoc() {{ return window.parent.document; }}

  function clickButtonByText(text) {{
    var btns = getParentDoc().querySelectorAll('button');
    for (var b of btns) {{
      if (b.textContent.trim() === text) {{ b.click(); return true; }}
    }}
    return false;
  }}

  function clickAnswerByLetter(letter) {{
    var btns = getParentDoc().querySelectorAll('button');
    for (var b of btns) {{
      if (b.textContent.trim().startsWith(letter + ':')) {{
        b.click(); return true;
      }}
    }}
    return false;
  }}

  window.parent.document.addEventListener('keydown', function(e) {{
    var key = e.key.toUpperCase();

    // Selecionar resposta com A/B/C/D (só quando não há pendente)
    if (['A','B','C','D'].includes(key)) {{
      // Só funciona se os botões de resposta estiverem visíveis
      clickAnswerByLetter(key);
    }}

    // Confirmar com Enter ou Espaço
    if (key === 'ENTER' || key === ' ') {{
      clickButtonByText('✅ Confirmar Resposta');
    }}
  }}, false);
}})();
</script>
"""
import streamlit.components.v1 as components
components.html(_keyboard_html, height=0, scrolling=False)

# ─────────────────────────────────────────────────────────────────────────────

# Caixa da pergunta
st.markdown(f"""
<div class="question-box">
    <div class="question-text">{pergunta}</div>
</div>
""", unsafe_allow_html=True)

# Grelha de respostas 2x2
resposta_dada = st.session_state.resposta_dada
pendente = st.session_state.pendente_resposta

# Dica de teclado (discreta, só aparece quando pode selecionar)
if resposta_dada is None:
    if pendente is None:
        hint_text = "⌨️ &nbsp; Pressione <b>A</b> · <b>B</b> · <b>C</b> · <b>D</b> para selecionar &nbsp;|&nbsp; <b>Enter</b> para confirmar"
    else:
        hint_text = "⌨️ &nbsp; Pressione <b>A</b> · <b>B</b> · <b>C</b> · <b>D</b> para mudar seleção &nbsp;|&nbsp; <b>Enter</b> para confirmar"
    st.markdown(f"""
<div style="text-align:center; color:rgba(100,160,255,0.55); font-size:12px; margin-bottom:4px; letter-spacing:1px;">
    {hint_text}
</div>
""", unsafe_allow_html=True)

import time as _time
# JS para ESTILIZAR (não esconder) os botões de resposta
_selected_text = f"{letras[pendente]}: {opcoes[pendente]}" if pendente is not None else ""
_has_pending = (pendente is not None and resposta_dada is None)
_style_ts = int(_time.time() * 1000)
components.html(f"""
<script>
// ts={_style_ts}
(function() {{
    var selectedText = {json.dumps(_selected_text)};
    var hasPending = {'true' if _has_pending else 'false'};
    var isConfirmed = {'true' if (st.session_state.resposta_dada is not None) else 'false'};

    function styleAnswerBtns() {{
        var btns = window.parent.document.querySelectorAll('button');
        btns.forEach(function(b) {{
            var t = b.textContent.trim();
            if (/^[ABCD]: /.test(t)) {{
                if (isConfirmed) {{
                    b.style.cssText = 'display:none!important';
                    return;
                }}
                var isSelected = hasPending && (t === selectedText);
                var isDimmed   = hasPending && !isSelected;
                b.style.cssText = [
                    'background:' + (isSelected
                        ? 'linear-gradient(135deg,#1a4a7a,#0d2a4a)'
                        : 'linear-gradient(135deg,#0d1f3c,#0a1628)') + '!important',
                    'border:' + (isSelected ? '2px solid #ffd700' : '1px solid #1e3a6a') + '!important',
                    'color:white!important',
                    'border-radius:8px!important',
                    'width:100%!important',
                    'padding:14px 20px!important',
                    'font-size:15px!important',
                    'text-align:left!important',
                    'cursor:pointer!important',
                    'display:block!important',
                    'box-shadow:' + (isSelected ? '0 0 20px rgba(255,215,0,0.55)' : 'none') + '!important',
                    'opacity:' + (isDimmed ? '0.65' : '1') + '!important',
                    'transition:all 0.2s!important'
                ].join(';');
            }}
            if (t.indexOf('CONFIRMAR') !== -1) {{
                b.style.cssText = [
                    'background:linear-gradient(135deg,#ffd700,#f0a800)!important',
                    'color:#0a1228!important',
                    'border:none!important',
                    'border-radius:10px!important',
                    'width:100%!important',
                    'padding:12px 32px!important',
                    'font-size:15px!important',
                    'font-weight:800!important',
                    'cursor:pointer!important',
                    'letter-spacing:1.5px!important',
                    'box-shadow:0 0 24px rgba(255,215,0,0.45)!important'
                ].join(';');
            }}
        }});
    }}

    styleAnswerBtns();
    setTimeout(styleAnswerBtns, 50);
    setTimeout(styleAnswerBtns, 200);
    setTimeout(styleAnswerBtns, 600);
    var obs = new MutationObserver(styleAnswerBtns);
    obs.observe(window.parent.document.body, {{childList: true, subtree: true}});
}})();
</script>
""", height=0)

col1, col2 = st.columns(2)
colunas = [col1, col2, col1, col2]

for i, (opcao, letra) in enumerate(zip(opcoes, letras)):
    with colunas[i]:
        if resposta_dada is not None:
            # Depois de responder (ou tempo esgotado): div estilizado sem botão
            classe = "answer-option"
            if i == correta:
                classe += " correct"
            elif resposta_dada != -1 and i == resposta_dada and i != correta:
                classe += " wrong"
            st.markdown(f"""
<div class="{classe}">
    <span class="answer-letter">{letra}:</span>
    <span class="answer-text">{opcao}</span>
</div>
            """, unsafe_allow_html=True)
        else:
            # Antes de responder: botão Streamlit normal (estilizado via JS acima)
            if st.button(f"{letra}: {opcao}", key=f"btn_{idx}_{i}", use_container_width=True):
                st.session_state.pendente_resposta = i
                st.rerun()

# ── BOTÃO CONFIRMAR (direto no layout Streamlit) ──────────────────────────
if pendente is not None and resposta_dada is None and st.session_state.get('mostrar_resultado_ts') is None:
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✅ CONFIRMAR RESPOSTA", key=f"confirmar_sim_{idx}", use_container_width=True):
            # Guarda a resposta mas NÃO avança ainda — mostra resultado primeiro
            _elapsed_s = round((_time.time()*1000 - _timer_start_ms) / 1000, 1)
            st.session_state.tempos_pergunta.append(min(_elapsed_s, 60.0))
            st.session_state.historico_quiz.append({
                "pergunta": pergunta,
                "opcoes": opcoes,
                "correta": correta,
                "dada": pendente,
                "tempo": min(_elapsed_s, 60.0),
            })
            st.session_state.respostas.append(pendente)
            st.session_state.resposta_dada = pendente  # mostra verde/vermelho
            st.session_state.pendente_resposta = None
            st.session_state.mostrar_resultado_ts = _time.time()
            st.rerun()

# ── ESCONDER BOTÃO CONFIRMAR via CSS após responder ─────────────────────────
if resposta_dada is not None:
    st.markdown("""
<style>
/* Esconder botão Confirmar após responder */
div[data-testid="stButton"] button[kind="secondary"],
div[data-testid="stButton"] button {
    /* só esconde se contiver CONFIRMAR — via JS abaixo */
}
</style>
<script>
(function hideConfirmar() {
    var btns = window.parent.document.querySelectorAll('button');
    btns.forEach(function(b) {
        if (b.innerText && b.innerText.indexOf('CONFIRMAR') !== -1) {
            b.style.setProperty('display', 'none', 'important');
            var p = b.parentElement;
            if (p) p.style.setProperty('display', 'none', 'important');
            var pp = p && p.parentElement;
            if (pp) pp.style.setProperty('display', 'none', 'important');
        }
    });
    setTimeout(hideConfirmar, 100);
})();
</script>
""", unsafe_allow_html=True)

# ── MOSTRAR RESULTADO após confirmar (verde/vermelho) + auto-avançar 5s ────
if resposta_dada is not None and resposta_dada != -1:
    acertou = (resposta_dada == correta)
    if acertou:
        st.markdown(f"""
<div style="text-align:center; color:#00e676; font-size:20px; font-weight:bold;
            margin:14px 0; text-shadow: 0 0 12px #00e676;">
    ✅ Correto! <span style="color:#00e676;">{opcoes[correta]}</span>
</div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
<div style="text-align:center; font-size:18px; font-weight:bold; margin:14px 0;">
    <span style="color:#ff4444;">❌ Errado!</span><br>
    <span style="color:#aaa; font-size:15px;">A tua resposta: </span>
    <span style="color:#ff4444;">{opcoes[resposta_dada]}</span><br>
    <span style="color:#aaa; font-size:15px;">Resposta correta: </span>
    <span style="color:#00e676;">{opcoes[correta]}</span>
</div>
        """, unsafe_allow_html=True)

    # ── SOM DE FEEDBACK (acerto/erro) + duck da música ────────────────────
    _game_id = st.session_state.get("game_id", "x")
    _sfx_type = "correct" if acertou else "wrong"
    play_sfx(_sfx_type, f"sfx_{_game_id}_{idx}")
    if acertou:
        play_confetti(f"conf_{_game_id}_{idx}", mode="burst")

    # Auto-avançar após 5 segundos
    _ts_res = st.session_state.get("mostrar_resultado_ts")
    elapsed = _time.time() - _ts_res if _ts_res is not None else 0
    segundos_restantes = max(0, 5 - int(elapsed))
    st.markdown(f"""
<div style="text-align:center; color:#888; font-size:13px; margin-top:8px;">
    A avançar em {segundos_restantes}s...
</div>
    """, unsafe_allow_html=True)

    if elapsed >= 5:
        st.session_state.resposta_dada = None
        st.session_state.mostrar_resultado_ts = None
        st.session_state.pendente_resposta = None
        if idx + 1 < len(perguntas):
            st.session_state.pergunta += 1
        else:
            st.session_state.terminou = True
        st.rerun()
    else:
        _time.sleep(1)
        st.rerun()

# ── TEMPO ESGOTADO ──────────────────────────────────────────────────────────
if resposta_dada == -1:
    st.markdown(f"""
<div style="text-align:center; color:#ff6b6b; font-size:18px; font-weight:bold;
            margin:12px 0; text-shadow: 0 0 10px #ff4444;">
    ⏰ Tempo esgotado! A resposta correta era: <span style="color:#00e676;">{opcoes[correta]}</span>
</div>
    """, unsafe_allow_html=True)


    # ── SOM DE TEMPO ESGOTADO ──────────────────────────────────────────────
    _game_id_exp = st.session_state.get("game_id", "x")
    play_sfx("timeout", f"sfx_timeout_{_game_id_exp}_{idx}")

    _ts_exp = st.session_state.get("mostrar_resultado_ts")
    if _ts_exp is None:
        st.session_state.mostrar_resultado_ts = _time.time()
        _ts_exp = st.session_state.mostrar_resultado_ts
        elapsed_exp = 0
    else:
        elapsed_exp = _time.time() - _ts_exp

    segundos_restantes_exp = max(0, 5 - int(elapsed_exp))
    st.markdown(f"""
<div style="text-align:center; color:#888; font-size:13px; margin-top:8px;">
    A avançar em {segundos_restantes_exp}s...
</div>
    """, unsafe_allow_html=True)

    if elapsed_exp >= 5:
        st.session_state.resposta_dada = None
        st.session_state.mostrar_resultado_ts = None
        st.session_state.pendente_resposta = None
        if idx + 1 < len(perguntas):
            st.session_state.pergunta += 1
        else:
            st.session_state.terminou = True
        st.rerun()
    else:
        _time.sleep(1)
        st.rerun()
