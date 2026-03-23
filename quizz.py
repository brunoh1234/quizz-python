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


def reset_para_novo_jogo():
    """Reseta o estado para um novo jogo sem recarregar a página (mantém música)."""
    import uuid as _uuid
    keys_to_delete = [
        'user_id', 'pergunta', 'respostas', 'terminou',
        'resposta_dada', 'pendente_resposta', 'mostrar_resultado_ts',
        'tempos_pergunta', 'historico_quiz', 'ver_revisao',
    ]
    for k in keys_to_delete:
        if k in st.session_state:
            del st.session_state[k]
    # Limpar chaves de timer e som por pergunta
    for k in list(st.session_state.keys()):
        if k.startswith('timer_start_ms_') or k.startswith('sfx_played_'):
            del st.session_state[k]
    st.session_state.quiz_completed = True   # mantém música quiz em loop
    st.session_state.splash_shown   = True   # salta o splash
    st.session_state.scroll_to_top  = True   # trigger scroll no próximo render
    st.session_state.game_id = _uuid.uuid4().hex[:8]
    st.session_state.streak = 0
    st.session_state.max_streak = 0
    st.session_state.show_countdown = False
    st.session_state.pending_user_id = None


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
      // Três notas descendentes suaves (Lá4 → Fá4 → Ré4) - estilo quiz clássico
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
    mode='burst'       - pequena explosão (resposta certa)
    mode='celebration' - chuva contínua 3s (fim com boa pontuação)
    key                - chave única para não repetir no mesmo rerun
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


def _build_avatar_svg(avatar_key: str, mood: str, width: int = 90, height: int = 104) -> str:
    """Returns a standalone SVG string for the given avatar key and mood."""
    _MINI_CFG = {
        'moderador':    ('#2a5ecf', '#2a1800',
            '<path d="M28 22 Q50 10 72 22" stroke="#333" stroke-width="3" fill="none"/>'
            '<rect x="21" y="19" width="9" height="12" rx="3" fill="#333"/>'
            '<rect x="70" y="19" width="9" height="12" rx="3" fill="#333"/>'),
        'pontual':      ('#22884a', '#5c3010',
            '<circle cx="80" cy="16" r="11" fill="#ccaa00" opacity="0.9"/>'
            '<circle cx="80" cy="16" r="9" fill="#ffffcc"/>'
            '<line x1="80" y1="10" x2="80" y2="16" stroke="#333" stroke-width="1.5"/>'
            '<line x1="80" y1="16" x2="86" y2="16" stroke="#333" stroke-width="1.5"/>'),
        'apresentador': ('#8833cc', '#2a1800',
            '<circle cx="18" cy="60" r="6" fill="#ff2200"/>'
            '<circle cx="18" cy="60" r="3.5" fill="#ff6644"/>'),
        'silenciado':   ('#cc4422', '#3a2008',
            '<rect x="74" y="32" width="11" height="18" rx="5" fill="#888"/>'
            '<ellipse cx="79" cy="28" rx="5" ry="5" fill="#aaa"/>'
            '<line x1="70" y1="26" x2="90" y2="54" stroke="#ff2200" stroke-width="2.5" stroke-linecap="round"/>'),
        'secretario':   ('#1a9a88', '#4a2808',
            '<rect x="72" y="50" width="21" height="28" rx="2" fill="#f0f0f0"/>'
            '<rect x="72" y="50" width="21" height="5" rx="2" fill="#ccc"/>'
            '<line x1="75" y1="60" x2="90" y2="60" stroke="#aaa" stroke-width="1.5"/>'
            '<line x1="75" y1="65" x2="90" y2="65" stroke="#aaa" stroke-width="1.5"/>'
            '<line x1="75" y1="70" x2="90" y2="70" stroke="#aaa" stroke-width="1.5"/>'),
        'tecnico':      ('#6a6a7a', '#3a2808',
            '<text x="72" y="28" font-size="18" fill="#6af">&#x1F4F6;</text>'),
        'executivo':    ('#1a1a2a', '#2a1800',
            '<polygon points="50,55 46,72 50,78 54,72" fill="#cc2200"/>'
            '<polygon points="47,55 53,55 52,63 48,63" fill="#aa1800"/>'),
        'remoto':       ('#cc7722', '#5c3010',
            '<polygon points="50,96 38,107 62,107" fill="#996611" opacity="0.8"/>'
            '<rect x="42" y="107" width="16" height="8" rx="2" fill="#774400"/>'),
    }
    _mouths = {
        'idle':    '<path d="M44 38 Q50 42 56 38" stroke="#cc5533" stroke-width="1.5" fill="none" stroke-linecap="round"/>',
        'happy':   '<path d="M43 36 Q50 44 57 36" stroke="#cc5533" stroke-width="2" fill="none" stroke-linecap="round"/>',
        'fire':    '<path d="M43 36 Q50 44 57 36" stroke="#cc5533" stroke-width="2" fill="none" stroke-linecap="round"/>',
        'sad':     '<path d="M44 42 Q50 37 56 42" stroke="#cc5533" stroke-width="1.5" fill="none" stroke-linecap="round"/>',
        'nervous': '<path d="M44 39 Q47 37 50 39 Q53 41 56 39" stroke="#cc5533" stroke-width="1.5" fill="none" stroke-linecap="round"/>',
        'shocked': '<ellipse cx="50" cy="41" rx="5" ry="5" fill="#cc5533" opacity="0.6"/>',
        'pending': '<path d="M44 39 Q50 42 56 39" stroke="#cc5533" stroke-width="1.5" fill="none" stroke-linecap="round"/>',
    }
    _cfg = _MINI_CFG.get(avatar_key, _MINI_CFG['moderador'])
    _body_color, _hair_color, _accessory = _cfg
    _mouth = _mouths.get(mood, _mouths['idle'])
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 115" width="{width}" height="{height}">'
        f'<defs><linearGradient id="sg_fin" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="#FFCC99"/><stop offset="100%" stop-color="#E8906A"/></linearGradient></defs>'
        f'<rect x="28" y="55" width="44" height="42" rx="8" fill="{_body_color}"/>'
        f'<rect x="44" y="48" width="12" height="10" rx="4" fill="url(#sg_fin)"/>'
        f'<ellipse cx="28" cy="33" rx="5" ry="7" fill="url(#sg_fin)"/>'
        f'<ellipse cx="72" cy="33" rx="5" ry="7" fill="url(#sg_fin)"/>'
        f'<ellipse cx="50" cy="30" rx="22" ry="24" fill="url(#sg_fin)"/>'
        f'<ellipse cx="50" cy="13" rx="22" ry="11" fill="{_hair_color}"/>'
        f'<rect x="28" y="13" width="44" height="11" fill="{_hair_color}"/>'
        f'<ellipse cx="34" cy="36" rx="7" ry="5" fill="#ff7777" opacity="0.2"/>'
        f'<ellipse cx="66" cy="36" rx="7" ry="5" fill="#ff7777" opacity="0.2"/>'
        f'<ellipse cx="41" cy="28" rx="5" ry="5" fill="white"/>'
        f'<circle cx="41" cy="28" r="3" fill="#1a1a33"/>'
        f'<circle cx="42" cy="27" r="1" fill="white"/>'
        f'<ellipse cx="59" cy="28" rx="5" ry="5" fill="white"/>'
        f'<circle cx="59" cy="28" r="3" fill="#1a1a33"/>'
        f'<circle cx="60" cy="27" r="1" fill="white"/>'
        + _mouth + _accessory
        + '</svg>'
    )


def render_avatar_mascot(avatar_key: str, mood: str, speech: str = ""):
    """Renders the character avatar inline as a card (visible in the iframe area)."""
    import json as _json

    # Mini SVG config per character: (body_color, hair_color, accessory_svg)
    _MINI_CFG = {
        'moderador':    ('#2a5ecf', '#2a1800',
            '<path d="M28 22 Q50 10 72 22" stroke="#333" stroke-width="3" fill="none"/>'
            '<rect x="21" y="19" width="9" height="12" rx="3" fill="#333"/>'
            '<rect x="70" y="19" width="9" height="12" rx="3" fill="#333"/>'),
        'pontual':      ('#22884a', '#5c3010',
            '<circle cx="80" cy="16" r="11" fill="#ccaa00" opacity="0.9"/>'
            '<circle cx="80" cy="16" r="9" fill="#ffffcc"/>'
            '<line x1="80" y1="10" x2="80" y2="16" stroke="#333" stroke-width="1.5"/>'
            '<line x1="80" y1="16" x2="86" y2="16" stroke="#333" stroke-width="1.5"/>'),
        'apresentador': ('#8833cc', '#2a1800',
            '<circle cx="18" cy="60" r="6" fill="#ff2200"/>'
            '<circle cx="18" cy="60" r="3.5" fill="#ff6644"/>'),
        'silenciado':   ('#cc4422', '#3a2008',
            '<rect x="74" y="32" width="11" height="18" rx="5" fill="#888"/>'
            '<ellipse cx="79" cy="28" rx="5" ry="5" fill="#aaa"/>'
            '<line x1="70" y1="26" x2="90" y2="54" stroke="#ff2200" stroke-width="2.5" stroke-linecap="round"/>'),
        'secretario':   ('#1a9a88', '#4a2808',
            '<rect x="72" y="50" width="21" height="28" rx="2" fill="#f0f0f0"/>'
            '<rect x="72" y="50" width="21" height="5" rx="2" fill="#ccc"/>'
            '<line x1="75" y1="60" x2="90" y2="60" stroke="#aaa" stroke-width="1.5"/>'
            '<line x1="75" y1="65" x2="90" y2="65" stroke="#aaa" stroke-width="1.5"/>'
            '<line x1="75" y1="70" x2="90" y2="70" stroke="#aaa" stroke-width="1.5"/>'),
        'tecnico':      ('#6a6a7a', '#3a2808',
            '<text x="72" y="28" font-size="18" fill="#6af">&#x1F4F6;</text>'),
        'executivo':    ('#1a1a2a', '#2a1800',
            '<polygon points="50,55 46,72 50,78 54,72" fill="#cc2200"/>'
            '<polygon points="47,55 53,55 52,63 48,63" fill="#aa1800"/>'),
        'remoto':       ('#cc7722', '#5c3010',
            '<polygon points="50,96 38,107 62,107" fill="#996611" opacity="0.8"/>'
            '<rect x="42" y="107" width="16" height="8" rx="2" fill="#774400"/>'),
    }

    # Fallback config
    _cfg = _MINI_CFG.get(avatar_key, _MINI_CFG['moderador'])
    _body_color, _hair_color, _accessory = _cfg

    # Mouth SVG per mood
    _mouths = {
        'idle':    '<path d="M44 38 Q50 42 56 38" stroke="#cc5533" stroke-width="1.5" fill="none" stroke-linecap="round"/>',
        'happy':   '<path d="M43 36 Q50 44 57 36" stroke="#cc5533" stroke-width="2" fill="none" stroke-linecap="round"/>',
        'fire':    '<path d="M43 36 Q50 44 57 36" stroke="#cc5533" stroke-width="2" fill="none" stroke-linecap="round"/>',
        'sad':     '<path d="M44 42 Q50 37 56 42" stroke="#cc5533" stroke-width="1.5" fill="none" stroke-linecap="round"/>',
        'nervous': '<path d="M44 39 Q47 37 50 39 Q53 41 56 39" stroke="#cc5533" stroke-width="1.5" fill="none" stroke-linecap="round"/>',
        'shocked': '<ellipse cx="50" cy="41" rx="5" ry="5" fill="#cc5533" opacity="0.6"/>',
        'pending': '<path d="M44 39 Q50 42 56 39" stroke="#cc5533" stroke-width="1.5" fill="none" stroke-linecap="round"/>',
    }
    _mouth = _mouths.get(mood, _mouths['idle'])

    # Build mini SVG
    _mini_svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 115" width="72" height="83" class="av-svg">'
        f'<defs>'
        f'<linearGradient id="msk_sg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="#FFCC99"/>'
        f'<stop offset="100%" stop-color="#E8906A"/>'
        f'</linearGradient>'
        f'</defs>'
        f'<rect x="28" y="55" width="44" height="42" rx="8" fill="{_body_color}"/>'
        f'<rect x="44" y="48" width="12" height="10" rx="4" fill="url(#msk_sg)"/>'
        f'<ellipse cx="28" cy="33" rx="5" ry="7" fill="url(#msk_sg)"/>'
        f'<ellipse cx="72" cy="33" rx="5" ry="7" fill="url(#msk_sg)"/>'
        f'<ellipse cx="50" cy="30" rx="22" ry="24" fill="url(#msk_sg)"/>'
        f'<ellipse cx="50" cy="13" rx="22" ry="11" fill="{_hair_color}"/>'
        f'<rect x="28" y="13" width="44" height="11" fill="{_hair_color}"/>'
        f'<ellipse cx="34" cy="36" rx="7" ry="5" fill="#ff7777" opacity="0.2"/>'
        f'<ellipse cx="66" cy="36" rx="7" ry="5" fill="#ff7777" opacity="0.2"/>'
        f'<ellipse cx="41" cy="28" rx="5" ry="5" fill="white"/>'
        f'<circle cx="41" cy="28" r="3" fill="#1a1a33"/>'
        f'<circle cx="42" cy="27" r="1" fill="white"/>'
        f'<ellipse cx="59" cy="28" rx="5" ry="5" fill="white"/>'
        f'<circle cx="59" cy="28" r="3" fill="#1a1a33"/>'
        f'<circle cx="60" cy="27" r="1" fill="white"/>'
        + _mouth
        + _accessory
        + f'</svg>'
    )
    _mini_svg_json = _json.dumps(_mini_svg)

    import json as _json2
    _av_key_js  = _json2.dumps(avatar_key)
    _mood_js    = _json2.dumps(mood)
    _speech_js  = _json2.dumps(speech)

    # Animation per mood
    _anim_map = {
        'idle':    'avFloat   2s ease-in-out infinite',
        'happy':   'avBounce  0.7s cubic-bezier(0.36,0.07,0.19,0.97) 3',
        'sad':     'avShake   0.6s ease-in-out 2',
        'fire':    'avSpin    0.9s ease-in-out infinite',
        'nervous': 'avTremble 0.18s linear infinite',
        'shocked': 'avShock   0.5s ease-in-out 3',
        'pending': 'avFloat   1s ease-in-out infinite',
    }
    _anim = _anim_map.get(mood, _anim_map['idle'])

    _inline_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  html, body {{
    margin: 0; padding: 0;
    background: transparent;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    height: 100%;
    overflow: hidden;
  }}
  .av-card {{
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    gap: 4px; padding: 6px 10px;
    background: rgba(6,14,30,0.82);
    border: 1.5px solid rgba(30,144,255,0.35);
    border-radius: 14px;
    box-shadow: 0 0 18px rgba(30,144,255,0.18);
  }}
  .av-speech-bubble {{
    background: rgba(10,26,74,0.96);
    border: 1.5px solid #1e90ff;
    border-radius: 12px 12px 0 12px;
    padding: 3px 10px;
    font-size: 10px;
    color: #7eb8ff;
    font-weight: bold;
    white-space: nowrap;
    font-family: Arial, sans-serif;
    max-width: 140px;
    text-align: center;
    box-shadow: 0 0 8px rgba(30,144,255,0.3);
    animation: speechPop 0.3s cubic-bezier(0.175,0.885,0.32,1.275);
  }}
  @keyframes speechPop  {{ 0%{{transform:scale(0.5);opacity:0}} 100%{{transform:scale(1);opacity:1}} }}
  @keyframes avFloat    {{ 0%,100%{{transform:translateY(0)}} 50%{{transform:translateY(-7px)}} }}
  @keyframes avBounce   {{ 0%,100%{{transform:translateY(0) scale(1)}} 30%{{transform:translateY(-18px) scale(1.12)}} 60%{{transform:translateY(-6px) scale(1.04)}} }}
  @keyframes avShake    {{ 0%,100%{{transform:translateX(0)}} 20%{{transform:translateX(-7px) rotate(-4deg)}} 40%{{transform:translateX(7px) rotate(4deg)}} 60%{{transform:translateX(-4px) rotate(-2deg)}} 80%{{transform:translateX(4px) rotate(2deg)}} }}
  @keyframes avSpin     {{ 0%{{transform:rotate(0) scale(1)}} 25%{{transform:rotate(-15deg) scale(1.12)}} 50%{{transform:rotate(15deg) scale(1.18)}} 75%{{transform:rotate(-8deg) scale(1.08)}} 100%{{transform:rotate(0) scale(1)}} }}
  @keyframes avTremble  {{ 0%,100%{{transform:translateX(0) rotate(0)}} 25%{{transform:translateX(-3px) rotate(-2deg)}} 75%{{transform:translateX(3px) rotate(2deg)}} }}
  @keyframes avShock    {{ 0%{{transform:scale(1)}} 20%{{transform:scale(1.3) rotate(-5deg)}} 40%{{transform:scale(0.9) rotate(5deg)}} 60%{{transform:scale(1.12) rotate(-3deg)}} 100%{{transform:scale(1) rotate(0)}} }}
  .av-svg {{ animation: {_anim}; display: block; }}
</style>
</head>
<body>
<div class="av-card">
  {'<div class="av-speech-bubble">' + speech + '</div>' if speech else ''}
  {_mini_svg}
</div>
<script>
(function() {{
  // Update badge icon in parent with mini SVG
  var pdoc = window.parent.document;
  var badgeIcon = pdoc.getElementById('av-badge-icon');
  if (badgeIcon) {{
    var miniSvg = {_json2.dumps(_mini_svg)};
    // Scale down for badge (28x28)
    var scaled = miniSvg.replace('width="72"', 'width="22"').replace('height="83"', 'height="26"');
    scaled = scaled.replace('style="animation', 'style="animation:none;');
    badgeIcon.innerHTML = scaled;
    badgeIcon.style.background = 'none';
    badgeIcon.style.border = 'none';
    badgeIcon.style.width = 'auto';
    badgeIcon.style.height = 'auto';
  }}

  // Nervous mode watcher
  var nervousSpeeches = {{
    moderador: "\u26a1 Ordem! Foco!",
    pontual: "\u26a1 O tempo conta!",
    apresentador: "\u26a1 Pointer a tremer!",
    silenciado: "\u26a1 *acena os bra\u00e7os*",
    secretario: "\u26a1 Escrever mais r\u00e1pido!",
    tecnico: "\u26a1 Buffer... buffer...",
    executivo: "\u26a1 Board meeting!",
    remoto: "\u26a1 Fundo a distrair!"
  }};
  var avatarKey = {_av_key_js};
  var mood = {_mood_js};
  var nervousMsg = nervousSpeeches[avatarKey] || "\u26a1 Depressa!";

  if (mood === 'idle' || mood === 'pending') {{
    var watchTimer = setInterval(function() {{
      var numEl = pdoc.getElementById('timer-num');
      if (!numEl) {{ clearInterval(watchTimer); return; }}
      var remaining = parseInt(numEl.textContent, 10);
      var card = document.querySelector('.av-card');
      var bubble = document.querySelector('.av-speech-bubble');
      var svg = document.querySelector('.av-svg');
      if (!card) {{ clearInterval(watchTimer); return; }}
      if (remaining <= 10 && remaining > 0) {{
        svg.style.animation = 'avTremble 0.18s linear infinite';
        if (!bubble) {{
          var nb = document.createElement('div');
          nb.className = 'av-speech-bubble';
          nb.textContent = nervousMsg;
          card.insertBefore(nb, card.firstChild);
        }} else {{
          bubble.textContent = nervousMsg;
        }}
      }} else if (remaining > 10) {{
        svg.style.animation = '';
        if (bubble) bubble.textContent = {_speech_js} || '';
      }}
    }}, 500);
  }}
}})();
</script>
</body>
</html>"""

    _inline_html_enc = _inline_html.encode('ascii', 'xmlcharrefreplace').decode('ascii')
    components.html(_inline_html_enc, height=145, scrolling=False)


def remove_avatar_mascot():
    """Remove o avatar mascote da página (para usar fora do quiz)."""
    components.html("""<script>
(function(){
    var m = window.parent.document.getElementById('av-mascot');
    if (m) m.remove();
})();
</script>""", height=0)



def render_3d_avatar_preview(avatar_key: str):
    """Renders an animated SVG character preview using inline SVG + CSS animations."""

    # ── shared SVG snippets (plain strings, no curly braces) ─────────────────────
    _sg = (
        '<linearGradient id="sg" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#FFCC99"/>'
        '<stop offset="100%" stop-color="#E8906A"/>'
        '</linearGradient>'
    )

    # ── per-avatar SVG (inner elements only, no <svg> wrapper) ───────────────────
    # Layout: viewBox 0 0 220 280
    #   head-center (110,72), body y=118-192, legs y=191-252
    #   left-shoulder (63,120), right-shoulder (157,120)
    # Arm structure: <g transform="translate(SX,120)"><g class="ARM_CLASS">
    #   <rect x="-9" y="0" width="18" height="52" rx="7"/>   ← arm
    #   <ellipse cx="0" cy="56" rx="9" ry="9"/>              ← hand
    # </g></g>
    # CSS rotation: rotate(+N) tilts arm tip LEFT, rotate(-N) tilts tip RIGHT

    # ── MODERADOR ─────────────────────────────────────────────────────────────────
    _mod = (
        '<defs>'
        + _sg +
        '<radialGradient id="bgl" cx="50%" cy="50%" r="50%">'
        '<stop offset="0%" stop-color="#2255bb" stop-opacity="0.5"/>'
        '<stop offset="100%" stop-color="#060e1e" stop-opacity="0"/>'
        '</radialGradient>'
        '<linearGradient id="bg2" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#2a5ecf"/><stop offset="100%" stop-color="#1a4a9f"/>'
        '</linearGradient>'
        '<linearGradient id="lg2" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#1a3a8a"/><stop offset="100%" stop-color="#0d2560"/>'
        '</linearGradient>'
        '</defs>'
        '<circle cx="110" cy="150" r="90" fill="url(#bgl)"/>'
        '<ellipse cx="110" cy="268" rx="65" ry="9" fill="#0a1a4a" stroke="#1166ff" stroke-width="2"/>'
        '<g class="char-float">'
        # legs
        '<rect x="87" y="191" width="22" height="58" rx="7" fill="url(#lg2)"/>'
        '<rect x="111" y="191" width="22" height="58" rx="7" fill="url(#lg2)"/>'
        # shoes
        '<rect x="82" y="244" width="28" height="13" rx="5" fill="#111122"/>'
        '<rect x="108" y="244" width="28" height="13" rx="5" fill="#111122"/>'
        # body - blue jacket
        '<rect x="76" y="118" width="68" height="74" rx="9" fill="url(#bg2)"/>'
        # lapels
        '<polygon points="110,118 98,142 108,135 110,130" fill="#1a2a5a" opacity="0.8"/>'
        '<polygon points="110,118 122,142 112,135 110,130" fill="#1a2a5a" opacity="0.8"/>'
        # white shirt front
        '<rect x="105" y="118" width="10" height="24" rx="3" fill="white" opacity="0.85"/>'
        # left arm
        '<g transform="translate(63,120)"><g class="arm-idle-l">'
        '<rect x="-9" y="0" width="18" height="52" rx="7" fill="url(#bg2)"/>'
        '<ellipse cx="0" cy="56" rx="9" ry="9" fill="url(#sg)"/>'
        '</g></g>'
        # right arm raised authoritatively
        '<g transform="translate(157,120)"><g class="arm-wave-r">'
        '<rect x="-9" y="0" width="18" height="52" rx="7" fill="url(#bg2)"/>'
        '<ellipse cx="0" cy="56" rx="9" ry="9" fill="url(#sg)"/>'
        '</g></g>'
        # neck
        '<rect x="104" y="105" width="12" height="16" rx="4" fill="url(#sg)"/>'
        # ears
        '<ellipse cx="77" cy="74" rx="7" ry="9" fill="url(#sg)"/>'
        '<ellipse cx="143" cy="74" rx="7" ry="9" fill="url(#sg)"/>'
        # head
        '<ellipse cx="110" cy="72" rx="33" ry="36" fill="url(#sg)"/>'
        # dark professional hair
        '<ellipse cx="110" cy="47" rx="33" ry="16" fill="#2a1800"/>'
        '<rect x="77" y="48" width="66" height="14" fill="#2a1800"/>'
        '<ellipse cx="110" cy="57" rx="28" ry="6" fill="#3d2400"/>'
        # cheeks
        '<ellipse cx="92" cy="80" rx="9" ry="6" fill="#ff7777" opacity="0.22"/>'
        '<ellipse cx="128" cy="80" rx="9" ry="6" fill="#ff7777" opacity="0.22"/>'
        # eyes
        '<ellipse cx="99" cy="68" rx="7.5" ry="7.5" fill="white"/>'
        '<circle cx="100" cy="68" r="4" fill="#1a1a33"/>'
        '<circle cx="102" cy="66" r="1.5" fill="white"/>'
        '<ellipse cx="121" cy="68" rx="7.5" ry="7.5" fill="white"/>'
        '<circle cx="120" cy="68" r="4" fill="#1a1a33"/>'
        '<circle cx="122" cy="66" r="1.5" fill="white"/>'
        # straight professional brows
        '<path d="M93 59 Q99 57 105 59" stroke="#2a1800" stroke-width="2.5"'
        ' fill="none" stroke-linecap="round"/>'
        '<path d="M115 59 Q121 57 127 59" stroke="#2a1800" stroke-width="2.5"'
        ' fill="none" stroke-linecap="round"/>'
        # nose
        '<ellipse cx="110" cy="77" rx="3" ry="2" fill="#cc7755"/>'
        # confident smile
        '<path d="M103 84 Q110 90 117 84" stroke="#cc5533" stroke-width="2"'
        ' fill="none" stroke-linecap="round"/>'
        # headset arc
        '<path d="M82 62 Q110 38 138 62" stroke="#222222" stroke-width="5"'
        ' fill="none" stroke-linecap="round"/>'
        # earpads
        '<rect x="74" y="57" width="13" height="17" rx="5" fill="#333333"/>'
        '<rect x="133" y="57" width="13" height="17" rx="5" fill="#333333"/>'
        # mic arm from right earpad
        '<path d="M146 66 Q153 74 152 84" stroke="#333333" stroke-width="3"'
        ' fill="none" stroke-linecap="round"/>'
        # mic ball (red)
        '<circle cx="152" cy="86" r="5" fill="#cc2200"/>'
        '<circle cx="152" cy="86" r="3" fill="#ff4400"/>'
        '</g>'
    )

    # ── PONTUAL ───────────────────────────────────────────────────────────────────
    _pon = (
        '<defs>'
        + _sg +
        '<radialGradient id="bgl" cx="50%" cy="50%" r="50%">'
        '<stop offset="0%" stop-color="#186a32" stop-opacity="0.5"/>'
        '<stop offset="100%" stop-color="#060e1e" stop-opacity="0"/>'
        '</radialGradient>'
        '<linearGradient id="bg2" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#22884a"/><stop offset="100%" stop-color="#186a32"/>'
        '</linearGradient>'
        '<linearGradient id="lg2" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#0d3d1a"/><stop offset="100%" stop-color="#0a2e14"/>'
        '</linearGradient>'
        '</defs>'
        '<circle cx="110" cy="150" r="90" fill="url(#bgl)"/>'
        '<ellipse cx="110" cy="268" rx="65" ry="9" fill="#0a1a4a" stroke="#1166ff" stroke-width="2"/>'
        '<g class="char-float">'
        '<rect x="87" y="191" width="22" height="58" rx="7" fill="url(#lg2)"/>'
        '<rect x="111" y="191" width="22" height="58" rx="7" fill="url(#lg2)"/>'
        '<rect x="82" y="244" width="28" height="13" rx="5" fill="#111122"/>'
        '<rect x="108" y="244" width="28" height="13" rx="5" fill="#111122"/>'
        '<rect x="76" y="118" width="68" height="74" rx="9" fill="url(#bg2)"/>'
        # left arm checking watch
        '<g transform="translate(63,120)"><g class="arm-watch-l">'
        '<rect x="-9" y="0" width="18" height="52" rx="7" fill="url(#bg2)"/>'
        '<ellipse cx="0" cy="56" rx="9" ry="9" fill="url(#sg)"/>'
        # gold watch on wrist
        '<rect x="-8" y="37" width="16" height="11" rx="4" fill="#ccaa00"/>'
        '<rect x="-6" y="38" width="12" height="9" rx="3" fill="#ffffcc"/>'
        '</g></g>'
        # right arm - thumbs up
        '<g transform="translate(157,120)"><g class="arm-thumbs-r">'
        '<rect x="-9" y="0" width="18" height="52" rx="7" fill="url(#bg2)"/>'
        # fist
        '<rect x="-9" y="50" width="18" height="14" rx="6" fill="url(#sg)"/>'
        # thumb pointing up
        '<ellipse cx="-1" cy="44" rx="5" ry="8" fill="url(#sg)"/>'
        '</g></g>'
        '<rect x="104" y="105" width="12" height="16" rx="4" fill="url(#sg)"/>'
        '<ellipse cx="77" cy="74" rx="7" ry="9" fill="url(#sg)"/>'
        '<ellipse cx="143" cy="74" rx="7" ry="9" fill="url(#sg)"/>'
        '<ellipse cx="110" cy="72" rx="33" ry="36" fill="url(#sg)"/>'
        # medium brown hair
        '<ellipse cx="110" cy="46" rx="33" ry="17" fill="#5c3010"/>'
        '<rect x="77" y="47" width="66" height="14" fill="#5c3010"/>'
        '<ellipse cx="110" cy="56" rx="30" ry="8" fill="#7a4420"/>'
        '<ellipse cx="92" cy="80" rx="9" ry="6" fill="#ff7777" opacity="0.22"/>'
        '<ellipse cx="128" cy="80" rx="9" ry="6" fill="#ff7777" opacity="0.22"/>'
        '<ellipse cx="99" cy="68" rx="7.5" ry="7.5" fill="white"/>'
        '<circle cx="100" cy="68" r="4" fill="#1a1a33"/>'
        '<circle cx="102" cy="66" r="1.5" fill="white"/>'
        '<ellipse cx="121" cy="68" rx="7.5" ry="7.5" fill="white"/>'
        '<circle cx="120" cy="68" r="4" fill="#1a1a33"/>'
        '<circle cx="122" cy="66" r="1.5" fill="white"/>'
        # raised energetic brows
        '<path d="M93 57 Q99 54 105 57" stroke="#5c3010" stroke-width="2.5"'
        ' fill="none" stroke-linecap="round"/>'
        '<path d="M115 57 Q121 54 127 57" stroke="#5c3010" stroke-width="2.5"'
        ' fill="none" stroke-linecap="round"/>'
        '<ellipse cx="110" cy="77" rx="3" ry="2" fill="#cc7755"/>'
        # big enthusiastic smile
        '<path d="M101 83 Q110 93 119 83" stroke="#cc5533" stroke-width="2"'
        ' fill="none" stroke-linecap="round"/>'
        # checkmark badge floating top-right
        '<g class="badge-float">'
        '<circle cx="162" cy="36" r="14" fill="#007722" opacity="0.9"/>'
        '<circle cx="162" cy="36" r="12" fill="#00cc44"/>'
        '<path d="M155 36 L161 43 L170 28" stroke="white" stroke-width="3"'
        ' fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        '</g>'
        '</g>'
    )

    # ── APRESENTADOR ──────────────────────────────────────────────────────────────
    _apr = (
        '<defs>'
        + _sg +
        '<radialGradient id="bgl" cx="50%" cy="50%" r="50%">'
        '<stop offset="0%" stop-color="#6a1a9f" stop-opacity="0.5"/>'
        '<stop offset="100%" stop-color="#060e1e" stop-opacity="0"/>'
        '</radialGradient>'
        '<linearGradient id="bg2" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#8833cc"/><stop offset="100%" stop-color="#6a1a9f"/>'
        '</linearGradient>'
        '<linearGradient id="lg2" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#4a0d70"/><stop offset="100%" stop-color="#3d0d60"/>'
        '</linearGradient>'
        '</defs>'
        '<circle cx="110" cy="150" r="90" fill="url(#bgl)"/>'
        '<ellipse cx="110" cy="268" rx="65" ry="9" fill="#0a1a4a" stroke="#1166ff" stroke-width="2"/>'
        '<g class="char-float">'
        '<rect x="87" y="191" width="22" height="58" rx="7" fill="url(#lg2)"/>'
        '<rect x="111" y="191" width="22" height="58" rx="7" fill="url(#lg2)"/>'
        '<rect x="82" y="244" width="28" height="13" rx="5" fill="#111122"/>'
        '<rect x="108" y="244" width="28" height="13" rx="5" fill="#111122"/>'
        # purple blazer body
        '<rect x="76" y="118" width="68" height="74" rx="9" fill="url(#bg2)"/>'
        # lapels
        '<polygon points="110,118 97,145 108,138 110,130" fill="#4a0d70" opacity="0.9"/>'
        '<polygon points="110,118 123,145 112,138 110,130" fill="#4a0d70" opacity="0.9"/>'
        '<rect x="105" y="118" width="10" height="22" rx="3" fill="#ddbbff" opacity="0.7"/>'
        # mini slide panel behind/left of character
        '<rect x="14" y="100" width="52" height="38" rx="4" fill="#223366" stroke="#4466aa" stroke-width="1.5"/>'
        '<rect x="19" y="106" width="32" height="4" rx="2" fill="#4488ff"/>'
        '<rect x="19" y="113" width="25" height="4" rx="2" fill="#ff6644"/>'
        '<rect x="19" y="120" width="38" height="4" rx="2" fill="#44cc88"/>'
        '<rect x="19" y="127" width="20" height="4" rx="2" fill="#ffcc22"/>'
        # left arm
        '<g transform="translate(63,120)"><g class="arm-idle-l">'
        '<rect x="-9" y="0" width="18" height="52" rx="7" fill="url(#bg2)"/>'
        '<ellipse cx="0" cy="56" rx="9" ry="9" fill="url(#sg)"/>'
        '</g></g>'
        # right arm pointing at slide
        '<g transform="translate(157,120)"><g class="arm-point-r">'
        '<rect x="-9" y="0" width="18" height="52" rx="7" fill="url(#bg2)"/>'
        '<ellipse cx="0" cy="56" rx="9" ry="9" fill="url(#sg)"/>'
        # laser pointer in hand
        '<rect x="-2" y="54" width="5" height="28" rx="2.5" fill="#dddddd"/>'
        '<circle cx="1" cy="83" r="4" fill="#ff2200"/>'
        '<circle cx="1" cy="83" r="2.5" fill="#ff6644"/>'
        '</g></g>'
        '<rect x="104" y="105" width="12" height="16" rx="4" fill="url(#sg)"/>'
        '<ellipse cx="77" cy="74" rx="7" ry="9" fill="url(#sg)"/>'
        '<ellipse cx="143" cy="74" rx="7" ry="9" fill="url(#sg)"/>'
        '<ellipse cx="110" cy="72" rx="33" ry="36" fill="url(#sg)"/>'
        # dark hair
        '<ellipse cx="110" cy="47" rx="33" ry="16" fill="#2a1800"/>'
        '<rect x="77" y="48" width="66" height="14" fill="#2a1800"/>'
        '<ellipse cx="110" cy="57" rx="28" ry="6" fill="#3d2400"/>'
        '<ellipse cx="92" cy="80" rx="9" ry="6" fill="#ff7777" opacity="0.22"/>'
        '<ellipse cx="128" cy="80" rx="9" ry="6" fill="#ff7777" opacity="0.22"/>'
        '<ellipse cx="99" cy="68" rx="7.5" ry="7.5" fill="white"/>'
        '<circle cx="100" cy="68" r="4" fill="#1a1a33"/>'
        '<circle cx="102" cy="66" r="1.5" fill="white"/>'
        '<ellipse cx="121" cy="68" rx="7.5" ry="7.5" fill="white"/>'
        '<circle cx="120" cy="68" r="4" fill="#1a1a33"/>'
        '<circle cx="122" cy="66" r="1.5" fill="white"/>'
        '<path d="M93 59 Q99 57 105 59" stroke="#2a1800" stroke-width="2.5"'
        ' fill="none" stroke-linecap="round"/>'
        '<path d="M115 59 Q121 57 127 59" stroke="#2a1800" stroke-width="2.5"'
        ' fill="none" stroke-linecap="round"/>'
        '<ellipse cx="110" cy="77" rx="3" ry="2" fill="#cc7755"/>'
        '<path d="M103 84 Q110 90 117 84" stroke="#cc5533" stroke-width="2"'
        ' fill="none" stroke-linecap="round"/>'
        '</g>'
    )

    # ── SILENCIADO ────────────────────────────────────────────────────────────────
    _sil = (
        '<defs>'
        + _sg +
        '<radialGradient id="bgl" cx="50%" cy="50%" r="50%">'
        '<stop offset="0%" stop-color="#9f3a1a" stop-opacity="0.5"/>'
        '<stop offset="100%" stop-color="#060e1e" stop-opacity="0"/>'
        '</radialGradient>'
        '<linearGradient id="bg2" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#cc4422"/><stop offset="100%" stop-color="#9f3a1a"/>'
        '</linearGradient>'
        '<linearGradient id="lg2" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#601a0d"/><stop offset="100%" stop-color="#4a1208"/>'
        '</linearGradient>'
        '</defs>'
        '<circle cx="110" cy="150" r="90" fill="url(#bgl)"/>'
        '<ellipse cx="110" cy="268" rx="65" ry="9" fill="#0a1a4a" stroke="#1166ff" stroke-width="2"/>'
        '<g class="char-float">'
        '<rect x="87" y="191" width="22" height="58" rx="7" fill="url(#lg2)"/>'
        '<rect x="111" y="191" width="22" height="58" rx="7" fill="url(#lg2)"/>'
        '<rect x="82" y="244" width="28" height="13" rx="5" fill="#111122"/>'
        '<rect x="108" y="244" width="28" height="13" rx="5" fill="#111122"/>'
        '<rect x="76" y="118" width="68" height="74" rx="9" fill="url(#bg2)"/>'
        # left arm raised
        '<g transform="translate(63,120)"><g class="arm-raise-l">'
        '<rect x="-9" y="0" width="18" height="52" rx="7" fill="url(#bg2)"/>'
        '<ellipse cx="0" cy="56" rx="9" ry="9" fill="url(#sg)"/>'
        '</g></g>'
        # right arm raised
        '<g transform="translate(157,120)"><g class="arm-raise-r">'
        '<rect x="-9" y="0" width="18" height="52" rx="7" fill="url(#bg2)"/>'
        '<ellipse cx="0" cy="56" rx="9" ry="9" fill="url(#sg)"/>'
        '</g></g>'
        '<rect x="104" y="105" width="12" height="16" rx="4" fill="url(#sg)"/>'
        '<ellipse cx="77" cy="74" rx="7" ry="9" fill="url(#sg)"/>'
        '<ellipse cx="143" cy="74" rx="7" ry="9" fill="url(#sg)"/>'
        '<ellipse cx="110" cy="72" rx="33" ry="36" fill="url(#sg)"/>'
        # medium dark hair - slightly messy
        '<ellipse cx="110" cy="46" rx="33" ry="17" fill="#3a2008"/>'
        '<rect x="77" y="47" width="66" height="14" fill="#3a2008"/>'
        '<path d="M88 47 Q92 38 97 45" stroke="#3a2008" stroke-width="6"'
        ' fill="none" stroke-linecap="round"/>'
        '<path d="M115 44 Q120 35 126 43" stroke="#3a2008" stroke-width="6"'
        ' fill="none" stroke-linecap="round"/>'
        '<ellipse cx="92" cy="80" rx="9" ry="6" fill="#ff7777" opacity="0.22"/>'
        '<ellipse cx="128" cy="80" rx="9" ry="6" fill="#ff7777" opacity="0.22"/>'
        '<ellipse cx="99" cy="68" rx="7.5" ry="7.5" fill="white"/>'
        '<circle cx="100" cy="68" r="4" fill="#1a1a33"/>'
        '<circle cx="102" cy="66" r="1.5" fill="white"/>'
        '<ellipse cx="121" cy="68" rx="7.5" ry="7.5" fill="white"/>'
        '<circle cx="120" cy="68" r="4" fill="#1a1a33"/>'
        '<circle cx="122" cy="66" r="1.5" fill="white"/>'
        # frustrated angled brows (inner corners down)
        '<path d="M93 61 Q99 57 105 60" stroke="#3a2008" stroke-width="2.8"'
        ' fill="none" stroke-linecap="round"/>'
        '<path d="M115 60 Q121 57 127 61" stroke="#3a2008" stroke-width="2.8"'
        ' fill="none" stroke-linecap="round"/>'
        '<ellipse cx="110" cy="77" rx="3" ry="2" fill="#cc7755"/>'
        # open frustrated mouth
        '<path d="M104 86 Q110 80 116 86" stroke="#cc5533" stroke-width="2"'
        ' fill="none" stroke-linecap="round"/>'
        '<ellipse cx="110" cy="88" rx="6" ry="4" fill="#cc5533" opacity="0.4"/>'
        # muted mic icon floating to the right - pulsing
        '<g class="badge-float">'
        '<rect x="168" y="80" width="18" height="28" rx="9" fill="#888888"/>'
        '<ellipse cx="177" cy="80" rx="9" ry="9" fill="#aaaaaa"/>'
        '<path d="M170 114 Q177 122 184 114" stroke="#888888" stroke-width="2.5"'
        ' fill="none" stroke-linecap="round"/>'
        '<line x1="177" y1="108" x2="177" y2="114" stroke="#888888" stroke-width="2.5"'
        ' stroke-linecap="round"/>'
        # red slash over mic
        '<line x1="164" y1="75" x2="190" y2="118" stroke="#ff2200" stroke-width="3"'
        ' stroke-linecap="round"/>'
        '</g>'
        '</g>'
    )

    # ── SECRETARIO ────────────────────────────────────────────────────────────────
    _sec = (
        '<defs>'
        + _sg +
        '<radialGradient id="bgl" cx="50%" cy="50%" r="50%">'
        '<stop offset="0%" stop-color="#0f7a6a" stop-opacity="0.5"/>'
        '<stop offset="100%" stop-color="#060e1e" stop-opacity="0"/>'
        '</radialGradient>'
        '<linearGradient id="bg2" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#1a9a88"/><stop offset="100%" stop-color="#0f7a6a"/>'
        '</linearGradient>'
        '<linearGradient id="lg2" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#084d42"/><stop offset="100%" stop-color="#063830"/>'
        '</linearGradient>'
        '</defs>'
        '<circle cx="110" cy="150" r="90" fill="url(#bgl)"/>'
        '<ellipse cx="110" cy="268" rx="65" ry="9" fill="#0a1a4a" stroke="#1166ff" stroke-width="2"/>'
        '<g class="char-float">'
        '<rect x="87" y="191" width="22" height="58" rx="7" fill="url(#lg2)"/>'
        '<rect x="111" y="191" width="22" height="58" rx="7" fill="url(#lg2)"/>'
        '<rect x="82" y="244" width="28" height="13" rx="5" fill="#111122"/>'
        '<rect x="108" y="244" width="28" height="13" rx="5" fill="#111122"/>'
        '<rect x="76" y="118" width="68" height="74" rx="9" fill="url(#bg2)"/>'
        # left arm holding notepad
        '<g transform="translate(63,120)"><g class="arm-pad-l">'
        '<rect x="-9" y="0" width="18" height="52" rx="7" fill="url(#bg2)"/>'
        '<ellipse cx="0" cy="56" rx="9" ry="9" fill="url(#sg)"/>'
        # notepad
        '<rect x="-14" y="42" width="28" height="36" rx="3" fill="#f0f0f0"/>'
        '<rect x="-14" y="42" width="28" height="5" rx="3" fill="#cccccc"/>'
        '<line x1="-10" y1="52" x2="10" y2="52" stroke="#aaaacc" stroke-width="1.5"/>'
        '<line x1="-10" y1="57" x2="10" y2="57" stroke="#aaaacc" stroke-width="1.5"/>'
        '<line x1="-10" y1="62" x2="10" y2="62" stroke="#aaaacc" stroke-width="1.5"/>'
        '<line x1="-10" y1="67" x2="10" y2="67" stroke="#aaaacc" stroke-width="1.5"/>'
        '</g></g>'
        # right arm writing
        '<g transform="translate(157,120)"><g class="arm-write-r">'
        '<rect x="-9" y="0" width="18" height="52" rx="7" fill="url(#bg2)"/>'
        '<ellipse cx="0" cy="56" rx="9" ry="9" fill="url(#sg)"/>'
        # pen in hand
        '<rect x="-2" y="50" width="4" height="22" rx="2" fill="#1188ff"/>'
        '<rect x="-2" y="72" width="4" height="5" rx="1" fill="#222222"/>'
        '</g></g>'
        '<rect x="104" y="105" width="12" height="16" rx="4" fill="url(#sg)"/>'
        '<ellipse cx="77" cy="74" rx="7" ry="9" fill="url(#sg)"/>'
        '<ellipse cx="143" cy="74" rx="7" ry="9" fill="url(#sg)"/>'
        '<ellipse cx="110" cy="72" rx="33" ry="36" fill="url(#sg)"/>'
        # tidy medium hair
        '<ellipse cx="110" cy="46" rx="33" ry="17" fill="#4a2808"/>'
        '<rect x="77" y="47" width="66" height="14" fill="#4a2808"/>'
        '<path d="M77 50 Q110 38 143 50" stroke="#5a3010" stroke-width="3" fill="none"/>'
        '<ellipse cx="92" cy="80" rx="9" ry="6" fill="#ff7777" opacity="0.22"/>'
        '<ellipse cx="128" cy="80" rx="9" ry="6" fill="#ff7777" opacity="0.22"/>'
        '<ellipse cx="99" cy="68" rx="7.5" ry="7.5" fill="white"/>'
        '<circle cx="100" cy="68" r="4" fill="#1a1a33"/>'
        '<circle cx="102" cy="66" r="1.5" fill="white"/>'
        '<ellipse cx="121" cy="68" rx="7.5" ry="7.5" fill="white"/>'
        '<circle cx="120" cy="68" r="4" fill="#1a1a33"/>'
        '<circle cx="122" cy="66" r="1.5" fill="white"/>'
        # focused neutral brows
        '<path d="M93 59 Q99 57 105 59" stroke="#4a2808" stroke-width="2.5"'
        ' fill="none" stroke-linecap="round"/>'
        '<path d="M115 59 Q121 57 127 59" stroke="#4a2808" stroke-width="2.5"'
        ' fill="none" stroke-linecap="round"/>'
        '<ellipse cx="110" cy="77" rx="3" ry="2" fill="#cc7755"/>'
        # focused slight smile
        '<path d="M104 85 Q110 89 116 85" stroke="#cc5533" stroke-width="2"'
        ' fill="none" stroke-linecap="round"/>'
        '</g>'
    )

    # ── TECNICO ───────────────────────────────────────────────────────────────────
    _tec = (
        '<defs>'
        + _sg +
        '<radialGradient id="bgl" cx="50%" cy="50%" r="50%">'
        '<stop offset="0%" stop-color="#4a4a5a" stop-opacity="0.5"/>'
        '<stop offset="100%" stop-color="#060e1e" stop-opacity="0"/>'
        '</radialGradient>'
        '<linearGradient id="bg2" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#6a6a7a"/><stop offset="100%" stop-color="#4a4a5a"/>'
        '</linearGradient>'
        '<linearGradient id="lg2" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#3a3a4a"/><stop offset="100%" stop-color="#2a2a3a"/>'
        '</linearGradient>'
        '</defs>'
        '<circle cx="110" cy="150" r="90" fill="url(#bgl)"/>'
        '<ellipse cx="110" cy="268" rx="65" ry="9" fill="#0a1a4a" stroke="#1166ff" stroke-width="2"/>'
        '<g class="char-float">'
        '<rect x="87" y="191" width="22" height="58" rx="7" fill="url(#lg2)"/>'
        '<rect x="111" y="191" width="22" height="58" rx="7" fill="url(#lg2)"/>'
        '<rect x="82" y="244" width="28" height="13" rx="5" fill="#111122"/>'
        '<rect x="108" y="244" width="28" height="13" rx="5" fill="#111122"/>'
        # gray hoodie body
        '<rect x="76" y="118" width="68" height="74" rx="9" fill="url(#bg2)"/>'
        # hoodie front pocket
        '<rect x="90" y="155" width="40" height="26" rx="6" fill="#3a3a4a"/>'
        # hoodie drawstring
        '<line x1="102" y1="118" x2="98" y2="140" stroke="#333344" stroke-width="2"'
        ' stroke-linecap="round"/>'
        '<line x1="118" y1="118" x2="122" y2="140" stroke="#333344" stroke-width="2"'
        ' stroke-linecap="round"/>'
        # left arm
        '<g transform="translate(63,120)"><g class="arm-idle-l">'
        '<rect x="-9" y="0" width="18" height="52" rx="7" fill="url(#bg2)"/>'
        '<ellipse cx="0" cy="56" rx="9" ry="9" fill="url(#sg)"/>'
        '</g></g>'
        # right arm scratching head
        '<g transform="translate(157,120)"><g class="arm-scratch-r">'
        '<rect x="-9" y="0" width="18" height="52" rx="7" fill="url(#bg2)"/>'
        '<ellipse cx="0" cy="56" rx="9" ry="9" fill="url(#sg)"/>'
        # wrench in hand
        '<rect x="-3" y="52" width="6" height="20" rx="3" fill="#888888"/>'
        '<ellipse cx="0" cy="50" rx="7" ry="5" fill="#777777"/>'
        '</g></g>'
        '<rect x="104" y="105" width="12" height="16" rx="4" fill="url(#sg)"/>'
        '<ellipse cx="77" cy="74" rx="7" ry="9" fill="url(#sg)"/>'
        '<ellipse cx="143" cy="74" rx="7" ry="9" fill="url(#sg)"/>'
        '<ellipse cx="110" cy="72" rx="33" ry="36" fill="url(#sg)"/>'
        # hoodie hood over hair
        '<ellipse cx="110" cy="48" rx="32" ry="14" fill="#4a4a5a"/>'
        '<rect x="78" y="48" width="64" height="14" fill="#4a4a5a"/>'
        '<path d="M78 52 Q76 70 77 98" stroke="#5a5a6a" stroke-width="9"'
        ' fill="none" stroke-linecap="round"/>'
        '<path d="M142 52 Q144 70 143 98" stroke="#5a5a6a" stroke-width="9"'
        ' fill="none" stroke-linecap="round"/>'
        # small dark hair visible below hood
        '<ellipse cx="110" cy="54" rx="24" ry="8" fill="#3a2808"/>'
        '<ellipse cx="92" cy="80" rx="9" ry="6" fill="#ff7777" opacity="0.22"/>'
        '<ellipse cx="128" cy="80" rx="9" ry="6" fill="#ff7777" opacity="0.22"/>'
        '<ellipse cx="99" cy="68" rx="7.5" ry="7.5" fill="white"/>'
        '<circle cx="100" cy="68" r="4" fill="#1a1a33"/>'
        '<circle cx="102" cy="66" r="1.5" fill="white"/>'
        '<ellipse cx="121" cy="68" rx="7.5" ry="7.5" fill="white"/>'
        '<circle cx="120" cy="68" r="4" fill="#1a1a33"/>'
        '<circle cx="122" cy="66" r="1.5" fill="white"/>'
        # one raised brow (confused) - left raised, right normal
        '<path d="M93 58 Q99 53 105 57" stroke="#3a2808" stroke-width="2.8"'
        ' fill="none" stroke-linecap="round"/>'
        '<path d="M115 59 Q121 57 127 59" stroke="#3a2808" stroke-width="2.5"'
        ' fill="none" stroke-linecap="round"/>'
        # round glasses
        '<circle cx="99" cy="69" r="11" fill="none" stroke="#222222" stroke-width="2.5"/>'
        '<circle cx="121" cy="69" r="11" fill="none" stroke="#222222" stroke-width="2.5"/>'
        '<line x1="110" y1="69" x2="112" y2="69" stroke="#222222" stroke-width="2"/>'
        # glass lens tint
        '<circle cx="99" cy="69" r="10" fill="#aaddff" opacity="0.15"/>'
        '<circle cx="121" cy="69" r="10" fill="#aaddff" opacity="0.15"/>'
        '<ellipse cx="110" cy="78" rx="3" ry="2" fill="#cc7755"/>'
        # confused half-smile
        '<path d="M104 86 Q107 89 112 87 Q116 86 117 88" stroke="#cc5533" stroke-width="2"'
        ' fill="none" stroke-linecap="round"/>'
        # WiFi arcs above head - pulsing
        '<g class="wifi-pulse">'
        '<path d="M97 31 Q110 19 123 31" stroke="#00aaff" stroke-width="2.5"'
        ' fill="none" stroke-linecap="round" opacity="0.5"/>'
        '<path d="M102 37 Q110 28 118 37" stroke="#00ccff" stroke-width="2.5"'
        ' fill="none" stroke-linecap="round" opacity="0.7"/>'
        '<path d="M106 43 Q110 38 114 43" stroke="#44ddff" stroke-width="2.5"'
        ' fill="none" stroke-linecap="round"/>'
        '<circle cx="110" cy="47" r="3" fill="#00aaff"/>'
        '</g>'
        '</g>'
    )

    # ── EXECUTIVO ─────────────────────────────────────────────────────────────────
    _exe = (
        '<defs>'
        + _sg +
        '<radialGradient id="bgl" cx="50%" cy="50%" r="50%">'
        '<stop offset="0%" stop-color="#1a1a2e" stop-opacity="0.6"/>'
        '<stop offset="100%" stop-color="#060e1e" stop-opacity="0"/>'
        '</radialGradient>'
        '<linearGradient id="bg2" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#2a2a40"/><stop offset="100%" stop-color="#1a1a2e"/>'
        '</linearGradient>'
        # pajama leg gradients (colorful stripes)
        '<linearGradient id="lg2" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#aabbcc"/><stop offset="100%" stop-color="#8899aa"/>'
        '</linearGradient>'
        '</defs>'
        '<circle cx="110" cy="150" r="90" fill="url(#bgl)"/>'
        '<ellipse cx="110" cy="268" rx="65" ry="9" fill="#0a1a4a" stroke="#1166ff" stroke-width="2"/>'
        '<g class="char-float">'
        # pajama pants - colorful stripes
        '<rect x="87" y="191" width="22" height="58" rx="7" fill="#aabbcc"/>'
        '<rect x="111" y="191" width="22" height="58" rx="7" fill="#aabbcc"/>'
        # stripe layers on legs
        '<rect x="87" y="197" width="22" height="8" rx="2" fill="#ffcc22" opacity="0.9"/>'
        '<rect x="111" y="197" width="22" height="8" rx="2" fill="#ffcc22" opacity="0.9"/>'
        '<rect x="87" y="211" width="22" height="8" rx="2" fill="#ff6699" opacity="0.9"/>'
        '<rect x="111" y="211" width="22" height="8" rx="2" fill="#ff6699" opacity="0.9"/>'
        '<rect x="87" y="225" width="22" height="8" rx="2" fill="#44aaff" opacity="0.9"/>'
        '<rect x="111" y="225" width="22" height="8" rx="2" fill="#44aaff" opacity="0.9"/>'
        '<rect x="87" y="239" width="22" height="8" rx="2" fill="#66dd88" opacity="0.9"/>'
        '<rect x="111" y="239" width="22" height="8" rx="2" fill="#66dd88" opacity="0.9"/>'
        # shoes
        '<rect x="82" y="244" width="28" height="13" rx="5" fill="#111122"/>'
        '<rect x="108" y="244" width="28" height="13" rx="5" fill="#111122"/>'
        # dark suit jacket
        '<rect x="76" y="118" width="68" height="74" rx="9" fill="url(#bg2)"/>'
        # lapels (suit)
        '<polygon points="110,118 97,146 108,139 110,128" fill="#111122" opacity="0.95"/>'
        '<polygon points="110,118 123,146 112,139 110,128" fill="#111122" opacity="0.95"/>'
        # white shirt
        '<rect x="105" y="118" width="10" height="22" rx="3" fill="white" opacity="0.9"/>'
        # red tie
        '<polygon points="107,122 113,122 115,148 110,154 105,148" fill="#cc1122"/>'
        '<polygon points="108,122 112,122 110,127" fill="#880011"/>'
        # left arm
        '<g transform="translate(63,120)"><g class="arm-idle-l">'
        '<rect x="-9" y="0" width="18" height="52" rx="7" fill="url(#bg2)"/>'
        '<ellipse cx="0" cy="56" rx="9" ry="9" fill="url(#sg)"/>'
        '</g></g>'
        # right arm - professional wave
        '<g transform="translate(157,120)"><g class="arm-wave-r">'
        '<rect x="-9" y="0" width="18" height="52" rx="7" fill="url(#bg2)"/>'
        '<ellipse cx="0" cy="56" rx="9" ry="9" fill="url(#sg)"/>'
        '</g></g>'
        '<rect x="104" y="105" width="12" height="16" rx="4" fill="url(#sg)"/>'
        '<ellipse cx="77" cy="74" rx="7" ry="9" fill="url(#sg)"/>'
        '<ellipse cx="143" cy="74" rx="7" ry="9" fill="url(#sg)"/>'
        '<ellipse cx="110" cy="72" rx="33" ry="36" fill="url(#sg)"/>'
        # slicked back dark hair
        '<ellipse cx="110" cy="45" rx="33" ry="15" fill="#111111"/>'
        '<rect x="77" y="46" width="66" height="14" fill="#111111"/>'
        '<path d="M77 50 Q100 40 143 50" stroke="#222222" stroke-width="3" fill="none"/>'
        '<path d="M82 55 Q110 44 138 55" stroke="#333333" stroke-width="2" fill="none"/>'
        '<ellipse cx="92" cy="80" rx="9" ry="6" fill="#ff7777" opacity="0.22"/>'
        '<ellipse cx="128" cy="80" rx="9" ry="6" fill="#ff7777" opacity="0.22"/>'
        '<ellipse cx="99" cy="68" rx="7.5" ry="7.5" fill="white"/>'
        '<circle cx="100" cy="68" r="4" fill="#1a1a33"/>'
        '<circle cx="102" cy="66" r="1.5" fill="white"/>'
        '<ellipse cx="121" cy="68" rx="7.5" ry="7.5" fill="white"/>'
        '<circle cx="120" cy="68" r="4" fill="#1a1a33"/>'
        '<circle cx="122" cy="66" r="1.5" fill="white"/>'
        # smug raised brow (right slightly higher)
        '<path d="M93 59 Q99 57 105 59" stroke="#111111" stroke-width="2.5"'
        ' fill="none" stroke-linecap="round"/>'
        '<path d="M115 57 Q121 55 127 58" stroke="#111111" stroke-width="2.5"'
        ' fill="none" stroke-linecap="round"/>'
        '<ellipse cx="110" cy="77" rx="3" ry="2" fill="#cc7755"/>'
        # smug slight smirk (asymmetric)
        '<path d="M104 85 Q109 89 116 84" stroke="#cc5533" stroke-width="2"'
        ' fill="none" stroke-linecap="round"/>'
        '</g>'
    )

    # ── REMOTO ────────────────────────────────────────────────────────────────────
    _rem = (
        '<defs>'
        + _sg +
        '<radialGradient id="bgl" cx="50%" cy="50%" r="50%">'
        '<stop offset="0%" stop-color="#3a1a6a" stop-opacity="0.5"/>'
        '<stop offset="100%" stop-color="#060e1e" stop-opacity="0"/>'
        '</radialGradient>'
        '<linearGradient id="bg2" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#5a2a8a"/><stop offset="100%" stop-color="#3a1a6a"/>'
        '</linearGradient>'
        '<linearGradient id="lg2" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#666688"/><stop offset="100%" stop-color="#555577"/>'
        '</linearGradient>'
        '</defs>'
        '<circle cx="110" cy="150" r="90" fill="url(#bgl)"/>'
        '<ellipse cx="110" cy="268" rx="65" ry="9" fill="#0a1a4a" stroke="#1166ff" stroke-width="2"/>'
        '<g class="char-float">'
        '<rect x="87" y="191" width="22" height="58" rx="7" fill="url(#lg2)"/>'
        '<rect x="111" y="191" width="22" height="58" rx="7" fill="url(#lg2)"/>'
        '<rect x="82" y="244" width="28" height="13" rx="5" fill="#111122"/>'
        '<rect x="108" y="244" width="28" height="13" rx="5" fill="#111122"/>'
        # purple hoodie body
        '<rect x="76" y="118" width="68" height="74" rx="9" fill="url(#bg2)"/>'
        # hoodie front pocket
        '<rect x="88" y="158" width="44" height="26" rx="7" fill="#2a0a5a"/>'
        # hoodie drawstrings
        '<line x1="104" y1="118" x2="101" y2="143" stroke="#2a0a5a" stroke-width="2.5"'
        ' stroke-linecap="round"/>'
        '<line x1="116" y1="118" x2="119" y2="143" stroke="#2a0a5a" stroke-width="2.5"'
        ' stroke-linecap="round"/>'
        # left arm holding coffee mug
        '<g transform="translate(63,120)"><g class="arm-mug-l">'
        '<rect x="-9" y="0" width="18" height="52" rx="7" fill="url(#bg2)"/>'
        '<ellipse cx="0" cy="56" rx="9" ry="9" fill="url(#sg)"/>'
        # orange coffee mug
        '<rect x="-10" y="50" width="20" height="22" rx="5" fill="#cc4400"/>'
        '<ellipse cx="0" cy="50" rx="10" ry="4" fill="#dd5500"/>'
        '<ellipse cx="0" cy="72" rx="10" ry="4" fill="#aa3300"/>'
        # mug handle
        '<path d="M10 54 Q17 62 10 70" stroke="#cc4400" stroke-width="3"'
        ' fill="none" stroke-linecap="round"/>'
        # steam lines (animated)
        '<g class="steam-rise">'
        '<path d="M-4 46 Q-2 40 -4 34" stroke="white" stroke-width="1.5"'
        ' fill="none" stroke-linecap="round" opacity="0.6"/>'
        '<path d="M1 44 Q3 37 1 31" stroke="white" stroke-width="1.5"'
        ' fill="none" stroke-linecap="round" opacity="0.5"/>'
        '<path d="M6 46 Q8 39 6 33" stroke="white" stroke-width="1.5"'
        ' fill="none" stroke-linecap="round" opacity="0.6"/>'
        '</g>'
        '</g></g>'
        # right arm casual wave
        '<g transform="translate(157,120)"><g class="arm-wave-r">'
        '<rect x="-9" y="0" width="18" height="52" rx="7" fill="url(#bg2)"/>'
        '<ellipse cx="0" cy="56" rx="9" ry="9" fill="url(#sg)"/>'
        '</g></g>'
        '<rect x="104" y="105" width="12" height="16" rx="4" fill="url(#sg)"/>'
        '<ellipse cx="77" cy="74" rx="7" ry="9" fill="url(#sg)"/>'
        '<ellipse cx="143" cy="74" rx="7" ry="9" fill="url(#sg)"/>'
        '<ellipse cx="110" cy="72" rx="33" ry="36" fill="url(#sg)"/>'
        # purple hoodie hood
        '<ellipse cx="110" cy="48" rx="32" ry="14" fill="#3a1a6a"/>'
        '<rect x="78" y="48" width="64" height="14" fill="#3a1a6a"/>'
        '<path d="M78 52 Q76 70 77 100" stroke="#4a2a7a" stroke-width="9"'
        ' fill="none" stroke-linecap="round"/>'
        '<path d="M142 52 Q144 70 143 100" stroke="#4a2a7a" stroke-width="9"'
        ' fill="none" stroke-linecap="round"/>'
        # dark hair under hood
        '<ellipse cx="110" cy="54" rx="24" ry="8" fill="#2a1808"/>'
        '<ellipse cx="92" cy="80" rx="9" ry="6" fill="#ff7777" opacity="0.22"/>'
        '<ellipse cx="128" cy="80" rx="9" ry="6" fill="#ff7777" opacity="0.22"/>'
        '<ellipse cx="99" cy="68" rx="7.5" ry="7.5" fill="white"/>'
        '<circle cx="100" cy="68" r="4" fill="#1a1a33"/>'
        '<circle cx="102" cy="66" r="1.5" fill="white"/>'
        '<ellipse cx="121" cy="68" rx="7.5" ry="7.5" fill="white"/>'
        '<circle cx="120" cy="68" r="4" fill="#1a1a33"/>'
        '<circle cx="122" cy="66" r="1.5" fill="white"/>'
        '<path d="M93 59 Q99 57 105 59" stroke="#2a1808" stroke-width="2.5"'
        ' fill="none" stroke-linecap="round"/>'
        '<path d="M115 59 Q121 57 127 59" stroke="#2a1808" stroke-width="2.5"'
        ' fill="none" stroke-linecap="round"/>'
        '<ellipse cx="110" cy="77" rx="3" ry="2" fill="#cc7755"/>'
        # relaxed smile
        '<path d="M104 85 Q110 91 116 85" stroke="#cc5533" stroke-width="2"'
        ' fill="none" stroke-linecap="round"/>'
        # headphones
        '<path d="M80 62 Q110 38 140 62" stroke="#222233" stroke-width="6"'
        ' fill="none" stroke-linecap="round"/>'
        # headphone cups
        '<ellipse cx="80" cy="68" rx="11" ry="12" fill="#222233"/>'
        '<ellipse cx="140" cy="68" rx="11" ry="12" fill="#222233"/>'
        '<ellipse cx="80" cy="68" rx="8" ry="9" fill="#4444bb"/>'
        '<ellipse cx="140" cy="68" rx="8" ry="9" fill="#4444bb"/>'
        '</g>'
    )

    # ── AVATAR_DATA ───────────────────────────────────────────────────────────────
    AVATAR_DATA = {
        "moderador":    {"name": "O Moderador",    "svg": _mod},
        "pontual":      {"name": "O Pontual",       "svg": _pon},
        "apresentador": {"name": "O Apresentador",  "svg": _apr},
        "silenciado":   {"name": "O Silenciado",    "svg": _sil},
        "secretario":   {"name": "O Secret&#225;rio", "svg": _sec},
        "tecnico":      {"name": "O T&#233;cnico",  "svg": _tec},
        "executivo":    {"name": "O Executivo",     "svg": _exe},
        "remoto":       {"name": "O Remoto",        "svg": _rem},
    }

    # ── PLACEHOLDER ───────────────────────────────────────────────────────────────
    if not avatar_key or avatar_key not in AVATAR_DATA:
        _placeholder_html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  html, body {
    margin: 0; padding: 0;
    background: #060e1e;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 360px;
    overflow: hidden;
    font-family: 'Segoe UI', sans-serif;
  }
  @keyframes spin {
    from { transform: rotate(0deg); }
    to   { transform: rotate(360deg); }
  }
  .ring { animation: spin 2s linear infinite; transform-origin: center; }
  .av-name { color: #446688; font-size: 14px; letter-spacing: 2px;
    text-transform: uppercase; margin-top: 12px; }
</style>
</head>
<body>
<svg width="120" height="120" viewBox="0 0 120 120">
  <circle cx="60" cy="60" r="44" fill="none" stroke="#0a1a4a" stroke-width="8"/>
  <circle cx="60" cy="60" r="44" fill="none" stroke="#1166ff" stroke-width="8"
    stroke-dasharray="80 196" stroke-linecap="round" class="ring"/>
  <circle cx="60" cy="60" r="28" fill="none" stroke="#0a2a5a" stroke-width="5"/>
  <circle cx="60" cy="60" r="28" fill="none" stroke="#0044cc" stroke-width="5"
    stroke-dasharray="50 126" stroke-linecap="round" class="ring"
    style="animation-duration:1.3s; animation-direction:reverse"/>
  <circle cx="60" cy="60" r="8" fill="#1166ff" opacity="0.6"/>
</svg>
<div class="av-name">Seleciona um avatar</div>
</body>
</html>"""
        components.html(
            _placeholder_html.encode('ascii', 'xmlcharrefreplace').decode('ascii'),
            height=360
        )
        return

    # ── RENDER SELECTED AVATAR ────────────────────────────────────────────────────
    av = AVATAR_DATA[avatar_key]
    _av_svg = av["svg"]
    _av_name = av["name"]

    _av_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  html, body {{
    margin: 0; padding: 0;
    background: #060e1e;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 360px;
    overflow: hidden;
    font-family: 'Segoe UI', sans-serif;
  }}
  /* ── baseline float ── */
  @keyframes float {{
    0%, 100% {{ transform: translateY(0px); }}
    50%       {{ transform: translateY(-8px); }}
  }}
  .char-float {{ animation: float 2.5s ease-in-out infinite; }}
  /* ── arm keyframes ── */
  @keyframes armIdleL {{
    0%, 100% {{ transform: rotate(8deg); }}
    50%       {{ transform: rotate(14deg); }}
  }}
  @keyframes armIdleR {{
    0%, 100% {{ transform: rotate(-8deg); }}
    50%       {{ transform: rotate(-14deg); }}
  }}
  @keyframes armWaveR {{
    0%, 100% {{ transform: rotate(-65deg); }}
    50%       {{ transform: rotate(-30deg); }}
  }}
  @keyframes armWatchL {{
    0%, 100% {{ transform: rotate(40deg); }}
    50%       {{ transform: rotate(55deg); }}
  }}
  @keyframes armThumbsR {{
    0%, 100% {{ transform: rotate(-80deg); }}
    50%       {{ transform: rotate(-60deg); }}
  }}
  @keyframes armPointR {{
    0%, 100% {{ transform: rotate(-55deg); }}
    50%       {{ transform: rotate(-40deg); }}
  }}
  @keyframes armRaiseL {{
    0%, 100% {{ transform: rotate(125deg); }}
    50%       {{ transform: rotate(110deg); }}
  }}
  @keyframes armRaiseR {{
    0%, 100% {{ transform: rotate(-125deg); }}
    50%       {{ transform: rotate(-110deg); }}
  }}
  @keyframes armWriteR {{
    0%, 100% {{ transform: rotate(-15deg); }}
    50%       {{ transform: rotate(-5deg) translateX(3px); }}
  }}
  @keyframes armPadL {{
    0%, 100% {{ transform: rotate(30deg); }}
    50%       {{ transform: rotate(35deg); }}
  }}
  @keyframes armScratchR {{
    0%, 100% {{ transform: rotate(-120deg); }}
    50%       {{ transform: rotate(-105deg); }}
  }}
  @keyframes armMugL {{
    0%, 100% {{ transform: rotate(30deg); }}
    50%       {{ transform: rotate(40deg); }}
  }}
  /* ── prop / badge animations ── */
  @keyframes badgeFloat {{
    0%, 100% {{ transform: translateY(0px); }}
    50%       {{ transform: translateY(-5px); }}
  }}
  @keyframes wifiPulse {{
    0%, 100% {{ opacity: 1; }}
    50%       {{ opacity: 0.35; }}
  }}
  @keyframes steamRise {{
    0%   {{ transform: translateY(0px); opacity: 0.7; }}
    100% {{ transform: translateY(-14px); opacity: 0; }}
  }}
  /* ── apply animations ── */
  .arm-idle-l  {{ transform-box: fill-box; transform-origin: top center;
                  animation: armIdleL  2.5s ease-in-out infinite; }}
  .arm-idle-r  {{ transform-box: fill-box; transform-origin: top center;
                  animation: armIdleR  2.5s ease-in-out infinite; }}
  .arm-wave-r  {{ transform-box: fill-box; transform-origin: top center;
                  animation: armWaveR  1.5s ease-in-out infinite; }}
  .arm-watch-l {{ transform-box: fill-box; transform-origin: top center;
                  animation: armWatchL 2.0s ease-in-out infinite; }}
  .arm-thumbs-r {{ transform-box: fill-box; transform-origin: top center;
                   animation: armThumbsR 1.8s ease-in-out infinite; }}
  .arm-point-r {{ transform-box: fill-box; transform-origin: top center;
                  animation: armPointR 2.0s ease-in-out infinite; }}
  .arm-raise-l {{ transform-box: fill-box; transform-origin: top center;
                  animation: armRaiseL 1.2s ease-in-out infinite; }}
  .arm-raise-r {{ transform-box: fill-box; transform-origin: top center;
                  animation: armRaiseR 1.2s ease-in-out infinite; }}
  .arm-write-r {{ transform-box: fill-box; transform-origin: top center;
                  animation: armWriteR 0.7s ease-in-out infinite; }}
  .arm-pad-l   {{ transform-box: fill-box; transform-origin: top center;
                  animation: armPadL   2.5s ease-in-out infinite; }}
  .arm-scratch-r {{ transform-box: fill-box; transform-origin: top center;
                    animation: armScratchR 1.0s ease-in-out infinite; }}
  .arm-mug-l   {{ transform-box: fill-box; transform-origin: top center;
                  animation: armMugL   2.5s ease-in-out infinite; }}
  .badge-float {{ animation: badgeFloat 2.0s ease-in-out infinite; }}
  .wifi-pulse  {{ animation: wifiPulse  1.5s ease-in-out infinite; }}
  .steam-rise  {{ animation: steamRise  1.8s ease-in-out infinite; }}
  /* ── labels ── */
  .av-name {{
    color: #7eb8ff;
    font-size: 15px;
    letter-spacing: 2px;
    text-transform: uppercase;
    text-shadow: 0 0 12px rgba(100,180,255,0.7);
    font-weight: 600;
    margin-top: 8px;
  }}
  .av-hint {{
    color: #446688;
    font-size: 11px;
    margin-top: 3px;
  }}
</style>
</head>
<body>
<svg width="220" height="280" viewBox="0 0 220 280">
{_av_svg}
</svg>
<div class="av-name">{_av_name}</div>
<div class="av-hint">&#10024; clica e vai jogar!</div>
</body>
</html>"""

    components.html(
        _av_html.encode('ascii', 'xmlcharrefreplace').decode('ascii'),
        height=360
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
# CSS - DESIGN QUEM QUER SER MILIONÁRIO
# ------------------------------

st.markdown("""
<style>

/* -- FADE IN entre perguntas -- */
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

/* Botão de resposta - hexágono alongado */
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
if "scroll_to_top" not in st.session_state:
    st.session_state.scroll_to_top = False
if "streak" not in st.session_state:
    st.session_state.streak = 0
if "max_streak" not in st.session_state:
    st.session_state.max_streak = 0
if "show_countdown" not in st.session_state:
    st.session_state.show_countdown = False
if "show_video" not in st.session_state:
    st.session_state.show_video = False
if "pending_user_id" not in st.session_state:
    st.session_state.pending_user_id = None
if "avatar" not in st.session_state:
    st.session_state.avatar = None
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
    /* Hide zero-height component iframes (used for JS injection) */
    iframe[width="0"], iframe[height="0"] {
        display: none !important;
        position: absolute !important;
        visibility: hidden !important;
    }

    /* Hide the JS-triggered hidden buttons */
    button[data-testid="baseButton-secondary"] { }

    </style>
    """, unsafe_allow_html=True)

    # Botão Streamlit escondido - clicado pelo JS dentro do iframe
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
        p._ytPhase = 1; // começa já na fase 1 (transição) - intro foi durante o splash
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

    function showTransitionVideo() {
        // Parar a musica de transicao
        try { p._ytPlayer.pauseVideo(); } catch(e) {}

        // Overlay negro + div para o player YouTube API
        overlay.style.background = '#000';
        overlay.style.overflow = 'hidden';
        overlay.innerHTML =
            '<style>' +
            '#yt-fw{position:fixed;inset:0;background:#000;z-index:9999;}' +
            '#yt-fw-player{width:100%;height:100%;}' +
            '</style>' +
            '<div id="yt-fw"><div id="yt-fw-player"></div></div>';

        var doneCalled = false;
        var safetyTimer = null;
        var pollTimer = null;

        function doAfterVideo() {
            if (doneCalled) return;
            doneCalled = true;
            if (safetyTimer) clearTimeout(safetyTimer);
            if (pollTimer) clearInterval(pollTimer);
            // Aguardar 5 segundos e avancar para o quiz
            setTimeout(function() {
                try {
                    p._ytPlayer.loadVideoById({videoId: 'ren6rd9FfV8', startSeconds: 0});
                    p._ytPhase = 2;
                } catch(ex) {}
                navigateToLogin();
            }, 5000);
        }

        // Safety timeout: video tem 55s, damos 80s de margem
        safetyTimer = setTimeout(doAfterVideo, 65000);

        function initPlayer() {
            var localPlayer = new YT.Player('yt-fw-player', {
                videoId: '0d8EXkgwYN4',
                playerVars: {
                    autoplay: 1,
                    controls: 0,
                    rel: 0,
                    modestbranding: 1,
                    iv_load_policy: 3,
                    playsinline: 1,
                    disablekb: 1,
                    fs: 0
                },
                events: {
                    onStateChange: function(e) {
                        if (e.data === 0) { doAfterVideo(); }
                    }
                }
            });
            // Polling de backup a cada segundo
            pollTimer = setInterval(function() {
                try { if (localPlayer.getPlayerState() === 0) { doAfterVideo(); } } catch(ex) {}
            }, 1000);
        }

        // Carregar YT IFrame API no contexto deste iframe (mais fiavel)
        if (typeof YT !== 'undefined' && YT.Player) {
            initPlayer();
        } else {
            window.onYouTubeIframeAPIReady = initPlayer;
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
        // Sem fallback - so clica se encontrar o botao certo
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

        // Após o GO! ao segundo 20 → mostrar vídeo de transição
        if (!navigated && t >= 20) {
            navigated = true;
            clearInterval(cdInterval);
            showTransitionVideo();
        }
    }, 100);
}
</script>
</body></html>"""

    _splash_html = _splash_html.replace("__STARS_CSS__", _stars)
    # Embed video transition
    import base64, os
    _video_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "video_transition.mp4")
    if os.path.exists(_video_path):
        with open(_video_path, "rb") as _vf:
            _video_b64 = base64.b64encode(_vf.read()).decode("ascii")
        _splash_html = _splash_html.replace("__VIDEO_B64__", _video_b64)
    else:
        _splash_html = _splash_html.replace("__VIDEO_B64__", "")
    components.html(_splash_html, height=750, scrolling=False)
    st.stop()






# -- Countdown de entrada - página exclusiva, sem título nem formulário --------
if st.session_state.get('show_countdown'):
    # Hide all visible Streamlit buttons during countdown
    st.markdown("""<style>
section[data-testid="stMain"] div[data-testid="stButton"] {
    position: absolute !important;
    width: 1px !important; height: 1px !important;
    overflow: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
}
</style>""", unsafe_allow_html=True)
    # Botão oculto que o JS clica após o countdown
    if st.button("▶", key="btn_start_quiz_hidden"):
        st.session_state.show_countdown = False
        # Transferir pending_user_id → user_id (antes feito pelo vídeo)
        if st.session_state.get('pending_user_id'):
            st.session_state.user_id = st.session_state.pending_user_id
            st.session_state.pending_user_id = None
        st.rerun()

    inject_persistent_music(is_intro=not st.session_state.quiz_completed)

    import streamlit.components.v1 as _comp_cd
    _comp_cd.html("""
<style>
html, body { margin:0; padding:0; background:#02050a; overflow:hidden; }
#simple-cd {
    position:fixed; inset:0; z-index:99999;
    background:radial-gradient(circle at 50% 50%, #0d1b3e 0%, #02050a 100%);
    display:flex; align-items:center; justify-content:center;
    flex-direction:column;
}
.scd-num {
    font-size:180px; font-weight:900; font-family:Georgia,serif;
    color:#fff; text-shadow:0 0 60px #1e90ff, 0 0 120px #1e90ff88;
    animation: scdPop 0.9s ease forwards;
    letter-spacing:-5px; line-height:1;
}
.scd-lbl {
    font-size:18px; letter-spacing:5px; color:#1e90ff;
    text-transform:uppercase; margin-top:12px;
    text-shadow:0 0 15px #1e90ff;
}
.scd-go {
    font-size:110px; font-weight:900; font-family:Georgia,serif;
    letter-spacing:8px; color:#ffd700;
    text-shadow:0 0 60px #ffd700, 0 0 120px #ffa50088;
    animation: scdGo 0.6s ease forwards;
}
@keyframes scdPop {
    0%   { transform:scale(2.5); opacity:0; }
    30%  { transform:scale(1);   opacity:1; }
    70%  { transform:scale(1);   opacity:1; }
    100% { transform:scale(0.4); opacity:0; }
}
@keyframes scdGo {
    0%   { transform:scale(0.5); opacity:0; }
    60%  { transform:scale(1.2); opacity:1; }
    100% { transform:scale(1);   opacity:1; }
}
</style>
<div id="simple-cd">
    <div id="scd-content" class="scd-num">3</div>
    <div id="scd-label" class="scd-lbl">PREPARAR</div>
</div>
<script>
(function(){
    var par = window.parent;

    // Esconder TODO o conteúdo da página pai incluindo o botão oculto
    var hideStyle = par.document.createElement('style');
    hideStyle.id = 'cd-hide-all';
    hideStyle.textContent = [
        'header[data-testid="stHeader"] { display:none!important; }',
        '[data-testid="stDecoration"] { display:none!important; }',
        '[data-testid="stAppViewContainer"] { background:#02050a!important; }',
        '.main .block-container { opacity:0!important; }',
        'iframe[title="st.components.v1.html"] { opacity:1!important; position:fixed!important; inset:0!important; width:100vw!important; height:100vh!important; border:none!important; z-index:99999!important; }'
    ].join('');
    par.document.head.appendChild(hideStyle);

    var steps = [
        {num:'3', lbl:'PREPARAR', cls:'scd-num', delay:0},
        {num:'2', lbl:'ATENÇÃO',  cls:'scd-num', delay:1000},
        {num:'1', lbl:'JÁ!',      cls:'scd-num', delay:2000},
        {num:'GO!', lbl:'',       cls:'scd-go',  delay:3000},
    ];
    var content = document.getElementById('scd-content');
    var label   = document.getElementById('scd-label');

    steps.forEach(function(s) {
        setTimeout(function(){
            content.className = s.cls;
            content.textContent = s.num;
            label.textContent = s.lbl;
            content.style.animation='none';
            void content.offsetWidth;
            content.style.animation='';
        }, s.delay);
    });

    // Após GO! - clicar o botão oculto com retry para garantir que é encontrado
    function clickHiddenBtn(attempts) {
        var btns = par.document.querySelectorAll('button');
        for (var b of btns) {
            if (b.innerText && b.innerText.trim() === '▶') {
                // Restaurar visibilidade antes de clicar
                var hs = par.document.getElementById('cd-hide-all');
                if (hs) hs.remove();
                b.click();
                return;
            }
        }
        // Botão ainda não carregou - tentar novamente
        if (attempts > 0) setTimeout(function(){ clickHiddenBtn(attempts-1); }, 150);
    }

    setTimeout(function(){ clickHiddenBtn(10); }, 3600);
})();
</script>
""", height=800)

    # Show avatar on countdown too
    _av = st.session_state.get('avatar', '🧑‍💻')
    render_avatar_mascot(_av, 'idle', '🎯 Vai!')
    st.stop()

# ------------------------------
# VÍDEO DE TRANSIÇÃO (YouTube)
# ------------------------------
if st.session_state.get('show_video'):
    import time as _vtime

    if 'video_start_time' not in st.session_state or st.session_state.video_start_time is None:
        st.session_state.video_start_time = _vtime.time()

    # Página preta enquanto vídeo toca
    st.markdown('<style>header[data-testid="stHeader"],footer,[data-testid="stToolbar"],[data-testid="stStatusWidget"]{display:none!important;}[data-testid="stAppViewContainer"],.main,.block-container{padding:0!important;margin:0!important;background:#000!important;max-width:100%!important;}</style>', unsafe_allow_html=True)

    # Botão hidden que o JS clica para avançar
    if st.button('VIDEO_DONE', key='btn_video_done_hidden'):
        st.session_state.show_video = False
        st.session_state.video_start_time = None
        st.session_state.user_id = st.session_state.pending_user_id
        st.session_state.pending_user_id = None
        st.rerun()

    # Esconder botão VIDEO_DONE
    st.markdown('<style>button p{} </style>', unsafe_allow_html=True)

    # Injetar JS que usa o p._ytPlayer existente
    _yt_video_js = '(function(){var p=window.parent;if(p._videoTransitionActive)return;p._videoTransitionActive=true;var el=p.document.getElementById(&#x27;_yt_persist&#x27;);if(el){el.style.cssText=&#x27;position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:99999;background:#000;&#x27;;}if(!p.document.getElementById(&#x27;_yt_overlay_bg&#x27;)){  var ov=p.document.createElement(&#x27;div&#x27;);  ov.id=&#x27;_yt_overlay_bg&#x27;;  ov.style.cssText=&#x27;position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:99998;background:#000;&#x27;;  p.document.body.appendChild(ov);}var doneCalled=false;function done(){  if(doneCalled)return;  doneCalled=true;  p._videoTransitionActive=false;  setTimeout(function(){    if(el){el.style.cssText=&#x27;position:fixed;top:-9999px;left:-9999px;width:1px;height:1px;&#x27;;}    var o=p.document.getElementById(&#x27;_yt_overlay_bg&#x27;);if(o)o.remove();    if(p._ytPlayer&amp;&amp;p._ytPlayer.loadVideoById){      p._ytPlayer.setVolume(70);      p._ytPlayer.loadVideoById({videoId:&#x27;ren6rd9FfV8&#x27;,startSeconds:0});    }    var btns=p.document.querySelectorAll(&#x27;button&#x27;);    for(var i=0;i&lt;btns.length;i++){      if(btns[i].innerText&amp;&amp;btns[i].innerText.indexOf(&#x27;VIDEO_DONE&#x27;)&gt;=0){btns[i].click();break;}    }  },5000);}function loadVid(){  if(p._ytPlayer&amp;&amp;p._ytPlayer.loadVideoById){    p._ytPlayer.setVolume(100);    p._ytPlayer.loadVideoById({videoId:&#x27;0d8EXkgwYN4&#x27;,startSeconds:0});    var poll=setInterval(function(){      try{if(p._ytPlayer.getPlayerState()===0){clearInterval(poll);done();}}catch(e){}    },1000);    p._ytPlayer.addEventListener(&#x27;onStateChange&#x27;,function(e){      if(e.data===0){clearInterval(poll);done();}    });  }else{    setTimeout(loadVid,500);  }}setTimeout(loadVid,500);})();'
    st.markdown(
        '<iframe srcdoc="<!DOCTYPE html><html><body><script>'
        + _yt_video_js +
        '</script></body></html>" style="display:none;position:absolute;width:0;height:0;" width="0" height="0"></iframe>',
        unsafe_allow_html=True,
    )

    # Timer Python fallback (70 segundos)
    elapsed = _vtime.time() - st.session_state.video_start_time
    remaining = 300 - elapsed
    if remaining > 0:
        _vtime.sleep(min(4, remaining))
        st.rerun()
    else:
        st.session_state.show_video = False
        st.session_state.video_start_time = None
        st.session_state.user_id = st.session_state.pending_user_id
        st.session_state.pending_user_id = None
        st.rerun()

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
    remove_avatar_mascot()

    # Avatar button CSS
    st.markdown("""
<style>
div[data-testid="column"] button {
    background: linear-gradient(135deg, #0d1f3c, #0a1628) !important;
    border: 2px solid #1e3a6a !important;
    border-radius: 12px !important;
    color: white !important;
    font-size: 13px !important;
    padding: 10px 4px !important;
    line-height: 1.3 !important;
}
</style>
""", unsafe_allow_html=True)

    # (emoji, ascii_key, display_name)
    _AVATARS = [
        ("\U0001f399\ufe0f", "moderador",    "Moderador"),
        ("\u23f0",           "pontual",      "Pontual"),
        ("\U0001f4ca",       "apresentador", "Apresentador"),
        ("\U0001f507",       "silenciado",   "Silenciado"),
        ("\U0001f4dd",       "secretario",   "Secret\u00e1rio"),
        ("\U0001f4f6",       "tecnico",      "T\u00e9cnico"),
        ("\U0001f454",       "executivo",    "Executivo"),
        ("\U0001f3e0",       "remoto",       "Remoto"),
    ]

    # --- Avatar selection buttons (top row) ---
    st.markdown('<p style="color:#aac8ff; text-align:center; font-size:14px; margin:10px 0 6px 0;">Escolhe o teu avatar de reuniao:</p>', unsafe_allow_html=True)
    _av_cols = st.columns(8)
    for _i, (_av_emoji, _av_key, _av_name) in enumerate(_AVATARS):
        with _av_cols[_i]:
            if st.session_state.avatar == _av_key:
                _av_label = f"OK {_av_emoji}\n{_av_name}"
            else:
                _av_label = f"{_av_emoji}\n{_av_name}"
            if st.button(_av_label, key=f"av_btn_{_i}", use_container_width=True):
                st.session_state.avatar = _av_key
                st.rerun()

    # --- Main card: avatar preview (left) + identification form (right) ---
    _col_av, _col_form = st.columns([1, 1.4])

    with _col_av:
        render_3d_avatar_preview(st.session_state.avatar or "")

    with _col_form:
        st.markdown("""
        <div class="login-box" style="margin-top:0; padding: 28px 28px 20px 28px;">
            <h2 style="color:#7eb8ff; margin-bottom:10px; font-size:22px;">&#128100; Identifica&#231;&#227;o</h2>
            <p style="color:#aac8ff; font-size:14px; margin-bottom:18px;">Insere o teu nome para come&#231;ar o quiz</p>
        </div>
        """, unsafe_allow_html=True)

        user_id = st.text_input("", placeholder="O teu nome...", label_visibility="collapsed")

        if st.button("\u25b6\ufe0f  COME\u00c7AR O QUIZ", use_container_width=True):
            import re as _re
            if st.session_state.get('avatar') is None:
                st.warning("Por favor escolhe um avatar! \U0001f3ad")
            elif not user_id.strip():
                st.warning("Por favor insere o teu nome.")
            elif not _re.fullmatch(r"[A-Za-z\u00C0-\u00FF\s]+", user_id.strip()):
                st.error("\u274c Nome inv\u00e1lido - s\u00f3 s\u00e3o aceites letras.")
            elif ja_jogou(user_id.strip(), resultados):
                dados = resultados[user_id.strip()]
                st.error("Este utilizador j\u00e1 jogou.")
                st.info(f"Pontua\u00e7\u00e3o anterior: {dados['score']}/10 - {dados['data']} \u00e0s {dados['hora']}")
            else:
                st.session_state.pending_user_id = user_id.strip()
                st.session_state.show_countdown = True
                st.rerun()

    # JS to highlight selected avatar button with gold border
    import json as _json_av
    _sel_json = _json_av.dumps(st.session_state.avatar or "")
    components.html(f"""<script>
(function() {{
    var sel = {_sel_json};
    function style() {{
        var btns = window.parent.document.querySelectorAll('button');
        btns.forEach(function(b) {{
            var t = b.textContent.trim();
            if (t.includes(sel) && sel !== '') {{
                b.style.border = '2px solid #ffd700 !important';
                b.style.boxShadow = '0 0 14px rgba(255,215,0,0.6)';
                b.style.background = 'linear-gradient(135deg,#1a3a0a,#0a2010) !important';
            }}
        }});
    }}
    setTimeout(style, 80);
    setTimeout(style, 250);
}})();
</script>""", height=0)

    # Música persistente - sobrevive a reruns via window.parent
    inject_persistent_music(is_intro=not st.session_state.quiz_completed)

    # Scroll to top após "Jogar Novamente" (sem reload de página)
    if st.session_state.get('scroll_to_top'):
        st.session_state.scroll_to_top = False
        components.html("""<script>
(function(){
    var n = 0;
    function up() {
        window.parent.scrollTo(0, 0);
        window.parent.document.documentElement.scrollTop = 0;
        window.parent.document.body.scrollTop = 0;
        if (++n < 30) setTimeout(up, 80);
    }
    up();
})();
</script>""", height=1)

    st.stop()

# Segurança: se user_id ainda for None, parar completamente
if st.session_state.user_id is None:
    st.stop()

# Música persistente - já inicializada no login, apenas garante continuidade
inject_persistent_music(is_intro=False)
inject_sound_toggle()

# ------------------------------
# ECRÃ FINAL
# ------------------------------

if st.session_state.terminou and st.session_state.get("user_id") is not None:
    remove_avatar_mascot()
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
        msg = "🥉 Continua a praticar - estás no caminho certo!"
        cor = "#ff9800"

    # -- Guardar resultado ----------------------------------------------------
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

    # -- CSS extra para o ecrã de resultados ---------------------------------
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

    # -- Caixa principal ------------------------------------------------------
    _av_fin_key = st.session_state.get('avatar', 'moderador')
    _av_fin_svg = _build_avatar_svg(_av_fin_key, 'happy', width=110, height=127)
    st.markdown(f"""
<div class="final-box">
  <div style="display:flex;align-items:center;justify-content:center;gap:24px;flex-wrap:wrap;">
    <div style="animation:avBounce 0.8s cubic-bezier(0.36,0.07,0.19,0.97) 3;filter:drop-shadow(0 0 14px gold);">
      {_av_fin_svg}
    </div>
    <div style="text-align:center;">
      <h2 style="color:#ffd700; font-size:30px; text-shadow: 0 0 20px rgba(255,215,0,0.8); margin:0 0 8px 0;">
          🎉 Quiz Concluído!
      </h2>
      <p style="font-size:20px; color:{cor}; font-weight:bold; margin:8px 0;">
          {st.session_state.user_id}
      </p>
      <p style="font-size:48px; font-weight:900; color:#ffffff; text-shadow: 0 0 20px gold; margin:6px 0;">
          {score} / {total}
      </p>
      <p style="font-size:18px; color:#aac8ff;">{msg}</p>
    </div>
  </div>
</div>
    """, unsafe_allow_html=True)

    # -- Stats grid -----------------------------------------------------------
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

    # -- Resumo rápido por pergunta -------------------------------------------
    st.markdown('<h3 style="color:#7eb8ff; text-align:center; margin:24px 0 12px; letter-spacing:2px;">📋 RESUMO</h3>', unsafe_allow_html=True)
    for i, h in enumerate(hist, 1):
        if h["dada"] == h["correta"]:
            icon, cor_r = "✅", "#00e676"
        elif h["dada"] == -1:
            icon, cor_r = "⏰", "#ff9800"
        else:
            icon, cor_r = "❌", "#ff4444"
        letras_rev = ["A","B","C","D"]
        resp_str = letras_rev[h["dada"]] if h["dada"] >= 0 else "-"
        st.markdown(f"""
<div class="q-summary-row">
    <span style="font-size:18px;">{icon}</span>
    <span style="color:#7eb8ff; font-weight:700; min-width:28px;">#{i}</span>
    <span style="color:#c8d8ff; flex:1; font-size:14px;">{h["pergunta"][:80]}{"..." if len(h["pergunta"])>80 else ""}</span>
    <span style="color:{cor_r}; font-size:13px; white-space:nowrap;">⏱ {h["tempo"]}s</span>
</div>
        """, unsafe_allow_html=True)

    # -- Botão ver revisão detalhada ------------------------------------------
    st.markdown("<br>", unsafe_allow_html=True)
    col_r1, col_r2, col_r3 = st.columns([1, 2, 1])
    with col_r2:
        label_rev = "🙈 Esconder Revisão" if st.session_state.ver_revisao else "🔍 Ver Revisão Detalhada"
        if st.button(label_rev, key="btn_revisao", use_container_width=True):
            st.session_state.ver_revisao = not st.session_state.ver_revisao
            st.rerun()

    # -- Revisão detalhada ----------------------------------------------------
    if st.session_state.ver_revisao:
        st.markdown('<h3 style="color:#7eb8ff; text-align:center; margin:28px 0 16px; letter-spacing:2px;">🔍 REVISÃO DETALHADA</h3>', unsafe_allow_html=True)
        letras_rev = ["A","B","C","D"]
        for i, h in enumerate(hist, 1):
            if h["dada"] == h["correta"]:
                classe, titulo = "acertou", f"✅ Pergunta {i} - Certa!"
                t_cor = "#00e676"
            elif h["dada"] == -1:
                classe, titulo = "timeout", f"⏰ Pergunta {i} - Tempo Esgotado"
                t_cor = "#ff9800"
            else:
                classe, titulo = "errou", f"❌ Pergunta {i} - Errada"
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

    # -- Ranking dos Participantes (atualiza a cada 15s sem recarregar a página) --
    st.markdown("<br>", unsafe_allow_html=True)

    @st.fragment(run_every=15)
    def mostrar_ranking():
        _res_rank = carregar_resultados()
        if not _res_rank:
            return
        _ranking = sorted(_res_rank.items(), key=lambda x: x[1]['score'], reverse=True)
        _rows_html = ""
        for _pos, (_nome, _dados) in enumerate(_ranking, start=1):
            _sv = _dados['score']
            _pct = round((_sv / 10) * 100)
            if _pos == 1:   _medal, _cp = "🥇", "#ffd700"
            elif _pos == 2: _medal, _cp = "🥈", "#c0c0c0"
            elif _pos == 3: _medal, _cp = "🥉", "#cd7f32"
            else:           _medal, _cp = f"#{_pos}", "#7eb8ff"
            _cs = "#00e676" if _pct >= 70 else ("#1e90ff" if _pct >= 50 else "#ff9800")
            _rows_html += f"""
<div style="display:flex;align-items:center;justify-content:space-between;
    padding:8px 14px;margin:5px 0;background:rgba(255,255,255,0.04);
    border-radius:10px;border:1px solid rgba(30,58,122,0.5);">
  <span style="color:{_cp};font-weight:bold;font-size:16px;min-width:36px;">{_medal}</span>
  <span style="color:#e0eaff;font-size:15px;flex:1;margin-left:10px;">{_nome}</span>
  <span style="color:{_cs};font-weight:bold;font-size:16px;">{_sv}/10</span>
  <span style="color:#5a7ab0;font-size:12px;margin-left:14px;">{_dados['data']} {_dados['hora']}</span>
</div>"""
        import streamlit.components.v1 as _comp_rank
        _rank_count = len(_ranking)
        _comp_rank.html(f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  html,body{{margin:0;padding:0;background:transparent;font-family:Arial,sans-serif;}}
  .rk-wrap{{display:flex;justify-content:center;width:100%;}}
  .rk-box{{background:linear-gradient(135deg,#0d1f4a 0%,#050e2a 100%);
    border:1px solid #1e3a7a;border-radius:16px;padding:20px 24px;width:100%;max-width:560px;}}
  .rk-title{{color:#ffd700;text-align:center;margin:0 0 14px 0;font-size:18px;font-weight:700;}}
  .rk-footer{{display:flex;justify-content:center;align-items:center;gap:8px;
    margin-top:12px;font-size:12px;color:#5a7ab0;}}
  .rk-countdown{{color:#1e90ff;font-weight:bold;min-width:18px;text-align:center;}}
  @keyframes spin{{from{{transform:rotate(0deg)}}to{{transform:rotate(360deg)}}}}
  .rk-spin{{display:inline-block;animation:spin 1s linear infinite;}}
</style>
</head>
<body>
<div class="rk-wrap">
  <div class="rk-box">
    <div class="rk-title">&#127942; Ranking dos Participantes</div>
    {_rows_html}
    <div class="rk-footer">
      <span class="rk-spin">&#8635;</span>
      <span>A atualizar em</span>
      <span class="rk-countdown" id="cd">15</span>
      <span>segundos</span>
    </div>
  </div>
</div>
<script>
(function(){{
  var t = 15;
  var el = document.getElementById('cd');
  var iv = setInterval(function(){{
    t--;
    if(el) el.textContent = t;
    if(t <= 0) {{ clearInterval(iv); if(el) el.textContent = '...'; }}
  }}, 1000);
}})();
</script>
</body></html>""", height=max(200, 54 + _rank_count * 46), scrolling=False)

    mostrar_ranking()

    # -- Desafiar Amigo --------------------------------------------------------
    st.markdown("<br>", unsafe_allow_html=True)
    _max_str = st.session_state.get('max_streak', 0)
    _streak_txt = f" | 🔥 Melhor série: {_max_str}" if _max_str >= 2 else ""
    import streamlit.components.v1 as _comp_chal
    _comp_chal.html(f"""
<style>
.challenge-box {{
    display:flex; flex-direction:column; align-items:center;
    background:linear-gradient(135deg,#0d1f4a 0%,#050e2a 100%);
    border:1px solid #1e3a7a; border-radius:16px;
    padding:20px 24px; max-width:560px; margin:0 auto;
}}
.challenge-title {{
    color:#ffd700; font-size:17px; font-weight:700;
    letter-spacing:1px; margin-bottom:12px;
}}
.challenge-msg {{
    background:rgba(255,255,255,0.06); border:1px solid #2a4a8a;
    border-radius:10px; padding:12px 18px; color:#c8d8ff;
    font-size:14px; line-height:1.6; width:100%; text-align:center;
    cursor:pointer; transition:background 0.2s;
    user-select:all;
}}
.challenge-msg:hover {{ background:rgba(255,255,255,0.1); }}
.copy-hint {{
    color:#5a7ab0; font-size:12px; margin-top:8px; letter-spacing:1px;
}}
.copy-ok {{ color:#00e676; font-size:13px; margin-top:6px; display:none; }}
</style>
<div class="challenge-box">
    <div class="challenge-title">🎯 Desafia um Amigo!</div>
    <div class="challenge-msg" id="chal-msg" onclick="copiarDesafio()">
        Consegues bater a minha pontuação? 🏆<br>
        Fiz <strong>{score}/{total}</strong> ({pct}%) no quiz "Quem Quer Ser Produtivo?"{_streak_txt}<br>
        <span id="chal-url" style="color:#7eb8ff;">A carregar link...</span>
    </div>
    <div class="copy-hint">👆 Clica para copiar</div>
    <div class="copy-ok" id="copy-ok">✅ Copiado para a área de transferência!</div>
</div>
<script>
(function(){{
    var urlEl = document.getElementById('chal-url');
    var url = window.parent.location.href.split('?')[0];
    urlEl.textContent = url;
}})();
function copiarDesafio(){{
    var url = window.parent.location.href.split('?')[0];
    var texto = 'Consegues bater a minha pontuação? 🏆\\n'
              + 'Fiz {score}/{total} ({pct}%) no quiz "Quem Quer Ser Produtivo?"{_streak_txt}\\n'
              + url;
    navigator.clipboard.writeText(texto).then(function(){{
        document.getElementById('copy-ok').style.display = 'block';
        setTimeout(function(){{ document.getElementById('copy-ok').style.display='none'; }}, 3000);
    }}).catch(function(){{
        window.prompt('Copia este texto:', texto);
    }});
}}
</script>
""", height=200)

    # -- Botão jogar novamente ------------------------------------------------
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Jogar Novamente", use_container_width=True, key="btn_jogar_nov"):
            reset_para_novo_jogo()
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
    <span id="av-badge-icon" style="font-size:16px; font-weight:bold; color:#1e90ff; background:rgba(30,144,255,0.15); border-radius:50%; width:28px; height:28px; display:inline-flex; align-items:center; justify-content:center;">&#128100;</span>
    <span style="color: #7eb8ff; font-size: 15px; font-weight: bold; letter-spacing: 1px;">{st.session_state.user_id}</span>
</div>
""", unsafe_allow_html=True)

# -- Avatar mascot animado (Phase 2 - character-specific reactions) -----------
_avatar_key_av = st.session_state.get('avatar', 'moderador') or 'moderador'
_resp_dada_av  = st.session_state.resposta_dada
_streak_av     = st.session_state.get('streak', 0)
_pending_av    = st.session_state.pendente_resposta

import time as _time
_elapsed_av    = (_time.time() * 1000 - _timer_start_ms) / 1000
_remaining_av  = max(0, 60 - _elapsed_av)

# Character-specific speech lines: {avatar_key: {mood: speech}}
_AV_SPEECHES = {
    'moderador': {
        'idle':    '🎙️ Atenção a todos!',
        'happy':   '✅ Excelente ponto!',
        'sad':     '😬 Temos de melhorar...',
        'fire':    '🔥 Reunião produtiva!',
        'nervous': '⚡ Ordem! Foco!',
        'shocked': '⏰ Agenda ultrapassada!',
        'pending': '🤔 A palavra está dada...',
    },
    'pontual': {
        'idle':    '⏰ Na hora certa!',
        'happy':   '✅ Pontualidade premiada!',
        'sad':     '😅 Recuperar terreno...',
        'fire':    '🔥 Série imparável!',
        'nervous': '⚡ O tempo conta!',
        'shocked': '⏰ Como o tempo voa!',
        'pending': '🤔 A cronometrar...',
    },
    'apresentador': {
        'idle':    '📊 Slide seguinte!',
        'happy':   '✅ Audiência conquistada!',
        'sad':     '😅 Próximo slide...',
        'fire':    '🔥 A audiência ama!',
        'nervous': '⚡ Pointer a tremer!',
        'shocked': '⏰ Projetor desligou!',
        'pending': '🤔 A preparar slide...',
    },
    'silenciado': {
        'idle':    '🔇 *murmura*',
        'happy':   '✅ *(ninguém ouviu)*',
        'sad':     '😅 *gesticula*',
        'fire':    '🔥 *grita em mudo*',
        'nervous': '⚡ *acena os braços*',
        'shocked': '⏰ Ainda em mudo!?',
        'pending': '🤔 *boca a mover*',
    },
    'secretario': {
        'idle':    '📝 A tomar notas...',
        'happy':   '✅ Registado!',
        'sad':     '😅 Anotei o erro...',
        'fire':    '🔥 Produtividade máx!',
        'nervous': '⚡ Escrever mais rápido!',
        'shocked': '⏰ Ata incompleta!',
        'pending': '🤔 A registar...',
    },
    'tecnico': {
        'idle':    '📶 Estão a ouvir-me?',
        'happy':   '✅ Tudo a funcionar!',
        'sad':     '😅 Falha de rede...',
        'fire':    '🔥 WiFi a 100%!',
        'nervous': '⚡ Buffer... buffer...',
        'shocked': '⏰ Ecrã congelado!',
        'pending': '🤔 Ligação instável...',
    },
    'executivo': {
        'idle':    '👔 Em reunião!',
        'happy':   '✅ Aprovado!',
        'sad':     '😅 Re-estrategizar...',
        'fire':    '🔥 KPIs em alta!',
        'nervous': '⚡ Board meeting!',
        'shocked': '⏰ Sem pijama na câmara!',
        'pending': '🤔 A deliberar...',
    },
    'remoto': {
        'idle':    '🏠 Home office!',
        'happy':   '✅ Do sofá, campeão!',
        'sad':     '😅 O gato saltou...',
        'fire':    '🔥 Remoto e produtivo!',
        'nervous': '⚡ Fundo a distrair!',
        'shocked': '⏰ Passou a hora!',
        'pending': '🤔 A ignorar filhos...',
    },
}

# Determine mood
if _resp_dada_av == -1:
    _av_mood = 'shocked'
elif _resp_dada_av is not None:
    _av_mood = 'happy' if _resp_dada_av == correta else 'sad'
elif _streak_av >= 3:
    _av_mood = 'fire'
elif _remaining_av <= 10:
    _av_mood = 'nervous'
elif _pending_av is not None:
    _av_mood = 'pending'
else:
    _av_mood = 'idle'

# Get character-specific speech
_char_speeches = _AV_SPEECHES.get(_avatar_key_av, _AV_SPEECHES['moderador'])
_av_speech = _char_speeches.get(_av_mood, '')

# For fire mood, append streak count
if _av_mood == 'fire' and _streak_av >= 3:
    _av_speech = f'🔥 {_streak_av} seguidas!'

# -- Streak display ------------------------------------------------------------
_streak = st.session_state.get('streak', 0)
if _streak >= 5:
    _streak_html = f'<div class="streak-badge streak-fire2">🔥🔥 Em chama! {_streak} seguidas!</div>'
elif _streak >= 3:
    _streak_html = f'<div class="streak-badge streak-fire">🔥 {_streak} seguidas!</div>'
elif _streak == 2:
    _streak_html = f'<div class="streak-badge streak-warm">⚡ 2 seguidas!</div>'
else:
    _streak_html = '<div style="height:36px;"></div>'

# Barra de progresso
st.markdown(f"""
<style>
.streak-badge {{
    display:inline-block;
    padding:6px 20px;
    border-radius:20px;
    font-size:15px;
    font-weight:700;
    letter-spacing:1px;
    animation: streakPop 0.4s cubic-bezier(0.175,0.885,0.32,1.275);
}}
.streak-fire2 {{
    background:linear-gradient(135deg,#ff4500,#ff8c00);
    color:#fff;
    box-shadow:0 0 18px rgba(255,100,0,0.7);
}}
.streak-fire {{
    background:linear-gradient(135deg,#ff6b00,#ffb300);
    color:#fff;
    box-shadow:0 0 14px rgba(255,150,0,0.6);
}}
.streak-warm {{
    background:linear-gradient(135deg,#1e90ff,#00c6ff);
    color:#fff;
    box-shadow:0 0 10px rgba(30,144,255,0.5);
}}
@keyframes streakPop {{
    0%   {{ transform:scale(0.6); opacity:0; }}
    80%  {{ transform:scale(1.1); opacity:1; }}
    100% {{ transform:scale(1);   opacity:1; }}
}}
</style>
<div style="text-align:center; margin-bottom:4px;">
    {_streak_html}
</div>
<div style="text-align:center; color:#7eb8ff; font-size:14px; margin-top:5px; letter-spacing:2px;">
    PERGUNTA {idx + 1} DE {len(perguntas)}
</div>
<div class="progress-container">
    <div class="progress-fill" style="width: {progresso}%"></div>
</div>
""", unsafe_allow_html=True)

# -- TIMER CIRCULAR (60 segundos) ----------------------------------------------
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
/* Hide the hidden quiz-start button */
div[data-testid="stButton"] > button p:only-child {
    /* hide ▶ button visually */
}
</style>
""", unsafe_allow_html=True)

# Timer circular via components.html - usa localStorage para persistir entre reruns
_is_paused  = False  # timer nunca pausa ao selecionar resposta - só para ao confirmar
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
  // startTs vem sempre do Python (session_state) - nunca do localStorage
  var startTs    = {_timer_start_ms};
  var IS_STOPPED = {'true' if _is_stopped else 'false'};

  var arc  = document.getElementById("timer-arc");
  var num  = document.getElementById("timer-num");
  var wrap = document.getElementById("timer-wrap");
  var CIRC = 2 * Math.PI * 48;

  // -- Paragem definitiva (resposta confirmada) ----------------------
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
_col_timer, _col_avatar = st.columns([1, 1])
with _col_timer:
    components.html(_timer_html, height=145, scrolling=False)
with _col_avatar:
    render_avatar_mascot(_avatar_key_av, _av_mood, _av_speech)

# -- TECLADO: A/B/C/D seleciona, Enter confirma -------------------------------
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

# -----------------------------------------------------------------------------

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

# -- BOTÃO CONFIRMAR (direto no layout Streamlit) --------------------------
if pendente is not None and resposta_dada is None and st.session_state.get('mostrar_resultado_ts') is None:
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✅ CONFIRMAR RESPOSTA", key=f"confirmar_sim_{idx}", use_container_width=True):
            # Guarda a resposta mas NÃO avança ainda - mostra resultado primeiro
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
            # Atualizar streak
            if pendente == correta:
                st.session_state.streak = st.session_state.get('streak', 0) + 1
                st.session_state.max_streak = max(st.session_state.get('max_streak', 0), st.session_state.streak)
            else:
                st.session_state.streak = 0
            st.rerun()

# -- ESCONDER BOTÃO CONFIRMAR via CSS após responder -------------------------
if resposta_dada is not None:
    st.markdown("""
<style>
/* Esconder botão Confirmar após responder */
div[data-testid="stButton"] button[kind="secondary"],
div[data-testid="stButton"] button {
    /* só esconde se contiver CONFIRMAR - via JS abaixo */
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

# -- MOSTRAR RESULTADO após confirmar (verde/vermelho) + auto-avançar 5s ----
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

    # -- SOM DE FEEDBACK (acerto/erro) + duck da música --------------------
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

# -- TEMPO ESGOTADO ----------------------------------------------------------
if resposta_dada == -1:
    st.markdown(f"""
<div style="text-align:center; color:#ff6b6b; font-size:18px; font-weight:bold;
            margin:12px 0; text-shadow: 0 0 10px #ff4444;">
    ⏰ Tempo esgotado! A resposta correta era: <span style="color:#00e676;">{opcoes[correta]}</span>
</div>
    """, unsafe_allow_html=True)


    # -- SOM DE TEMPO ESGOTADO ----------------------------------------------
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
