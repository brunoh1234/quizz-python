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


def render_avatar_mascot(avatar_emoji: str, mood: str, speech: str = ""):
    """Injeta avatar animado fixo no canto inferior direito."""
    import json as _json
    components.html(f"""
<script>
(function() {{
    var emoji = {_json.dumps(avatar_emoji)};
    var mood  = {_json.dumps(mood)};
    var speech = {_json.dumps(speech)};
    var pdoc = window.parent.document;

    if (!pdoc.getElementById('av-mascot-css')) {{
        var s = pdoc.createElement('style');
        s.id = 'av-mascot-css';
        s.textContent = `
            #av-mascot {{
                position:fixed; bottom:24px; right:24px;
                z-index:10000; display:flex; flex-direction:column;
                align-items:center; pointer-events:none;
            }}
            .av-speech {{
                background:rgba(10,26,74,0.95);
                border:2px solid #1e90ff;
                border-radius:16px 16px 0 16px;
                padding:5px 13px; font-size:12px;
                color:#7eb8ff; font-weight:bold;
                margin-bottom:5px; white-space:nowrap;
                animation:speechPop 0.3s cubic-bezier(0.175,0.885,0.32,1.275);
                box-shadow:0 0 10px rgba(30,144,255,0.4);
            }}
            .av-emoji {{
                font-size:54px; display:block;
                line-height:1;
                filter:drop-shadow(0 4px 8px rgba(0,0,0,0.5));
            }}
            @keyframes avFloat  {{ 0%,100%{{transform:translateY(0)}} 50%{{transform:translateY(-8px)}} }}
            @keyframes avBounce {{ 0%,100%{{transform:translateY(0) scale(1)}} 30%{{transform:translateY(-20px) scale(1.2)}} 60%{{transform:translateY(-8px) scale(1.05)}} }}
            @keyframes avShake  {{ 0%,100%{{transform:translateX(0)}} 20%{{transform:translateX(-8px) rotate(-5deg)}} 40%{{transform:translateX(8px) rotate(5deg)}} 60%{{transform:translateX(-5px) rotate(-3deg)}} 80%{{transform:translateX(5px) rotate(3deg)}} }}
            @keyframes avSpin   {{ 0%{{transform:rotate(0) scale(1)}} 25%{{transform:rotate(-15deg) scale(1.15)}} 50%{{transform:rotate(15deg) scale(1.2)}} 75%{{transform:rotate(-10deg) scale(1.1)}} 100%{{transform:rotate(0) scale(1)}} }}
            @keyframes avTremble{{ 0%,100%{{transform:translateX(0) rotate(0)}} 25%{{transform:translateX(-3px) rotate(-2deg)}} 75%{{transform:translateX(3px) rotate(2deg)}} }}
            @keyframes avShock  {{ 0%{{transform:scale(1)}} 20%{{transform:scale(1.35) rotate(-5deg)}} 40%{{transform:scale(0.9) rotate(5deg)}} 60%{{transform:scale(1.15) rotate(-3deg)}} 100%{{transform:scale(1) rotate(0)}} }}
            @keyframes speechPop{{ 0%{{transform:scale(0.5);opacity:0}} 100%{{transform:scale(1);opacity:1}} }}
            #av-mascot.av-idle    .av-emoji {{ animation:avFloat   2s ease-in-out infinite }}
            #av-mascot.av-happy   .av-emoji {{ animation:avBounce  0.7s cubic-bezier(0.36,0.07,0.19,0.97) 3 }}
            #av-mascot.av-sad     .av-emoji {{ animation:avShake   0.6s ease-in-out 2 }}
            #av-mascot.av-fire    .av-emoji {{ animation:avSpin    0.9s ease-in-out infinite }}
            #av-mascot.av-nervous .av-emoji {{ animation:avTremble 0.18s linear infinite }}
            #av-mascot.av-shocked .av-emoji {{ animation:avShock   0.5s ease-in-out 3 }}
            #av-mascot.av-pending .av-emoji {{ animation:avFloat   1s ease-in-out infinite }}
        `;
        pdoc.head.appendChild(s);
    }}

    var mascot = pdoc.getElementById('av-mascot');
    if (!mascot) {{
        mascot = pdoc.createElement('div');
        mascot.id = 'av-mascot';
        pdoc.body.appendChild(mascot);
    }}
    mascot.className = 'av-' + mood;
    mascot.innerHTML = (speech ? '<div class="av-speech">' + speech + '</div>' : '') +
                       '<span class="av-emoji">' + emoji + '</span>';

    // JS also watches the timer arc for nervous state
    if (mood === 'idle' || mood === 'pending') {{
        var watchTimer = setInterval(function() {{
            var numEl = pdoc.getElementById('timer-num');
            if (!numEl) {{ clearInterval(watchTimer); return; }}
            var remaining = parseInt(numEl.textContent, 10);
            var m = pdoc.getElementById('av-mascot');
            if (!m) {{ clearInterval(watchTimer); return; }}
            // Only override if still idle/pending (not confirmed)
            if (remaining <= 10 && remaining > 0 && (m.className === 'av-idle' || m.className === 'av-pending')) {{
                m.className = 'av-nervous';
                var sp = m.querySelector('.av-speech');
                if (!sp) {{
                    m.innerHTML = '<div class="av-speech">⚡ Depressa!</div>' + m.innerHTML;
                }} else {{
                    sp.textContent = '⚡ Depressa!';
                }}
            }} else if (remaining > 10 && (m.className === 'av-nervous')) {{
                m.className = 'av-' + mood;
            }}
        }}, 500);
    }}
}})();
</script>
""", height=0)


def remove_avatar_mascot():
    """Remove o avatar mascote da página (para usar fora do quiz)."""
    components.html("""<script>
(function(){
    var m = window.parent.document.getElementById('av-mascot');
    if (m) m.remove();
})();
</script>""", height=0)


def render_3d_avatar_preview(avatar_key: str):
    """Renders an animated 3D character preview using Three.js based on the selected avatar key."""
    import json as _json3d
    _key_js = _json3d.dumps(avatar_key if avatar_key else "")
    components.html(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  html,body{{margin:0;padding:0;background:transparent;overflow:hidden;display:flex;flex-direction:column;align-items:center;}}
  canvas{{display:block;border-radius:16px;box-shadow:0 0 30px rgba(30,100,255,0.35);}}
  #av3d-name{{text-align:center;color:#7eb8ff;font-size:15px;font-family:'Segoe UI',sans-serif;
    margin-top:8px;letter-spacing:2px;text-transform:uppercase;
    text-shadow:0 0 12px rgba(100,180,255,0.7);font-weight:600;}}
  #av3d-hint{{text-align:center;color:#446688;font-size:11px;font-family:'Segoe UI',sans-serif;margin-top:3px;}}
</style>
</head>
<body>
<canvas id="c" width="260" height="260"></canvas>
<div id="av3d-name">Seleciona um avatar</div>
<div id="av3d-hint">✋ acena contigo!</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
(function(){{
var AVATAR_KEY = {_key_js};

// ── Scene ──────────────────────────────────────────────────────────────────────
var W=260, H=260;
var scene = new THREE.Scene();
scene.background = new THREE.Color(0x060e1e);
var camera = new THREE.PerspectiveCamera(38, W/H, 0.1, 100);
camera.position.set(0, 0.25, 4.2);
var renderer = new THREE.WebGLRenderer({{canvas:document.getElementById('c'), antialias:true}});
renderer.setSize(W,H);
renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));

// ── Lights ─────────────────────────────────────────────────────────────────────
scene.add(new THREE.AmbientLight(0x304070, 0.9));
var dl = new THREE.DirectionalLight(0x88aaff, 1.6);
dl.position.set(2,3,3); scene.add(dl);
var rl = new THREE.DirectionalLight(0x003388, 0.6);
rl.position.set(-2,0,-1); scene.add(rl);
var pl = new THREE.PointLight(0x0066ff, 0.8, 8);
pl.position.set(0,2,2); scene.add(pl);

// ── Platform ──────────────────────────────────────────────────────────────────
var platMesh = new THREE.Mesh(
  new THREE.CylinderGeometry(0.9,0.9,0.06,48),
  new THREE.MeshPhongMaterial({{color:0x0a1a4a,emissive:0x002288,emissiveIntensity:0.4,shininess:120}})
);
platMesh.position.y = -1.42; scene.add(platMesh);
var ringMesh = new THREE.Mesh(
  new THREE.TorusGeometry(0.92,0.025,8,60),
  new THREE.MeshPhongMaterial({{color:0x1166ff,emissive:0x0088ff,emissiveIntensity:1.0}})
);
ringMesh.rotation.x=Math.PI/2; ringMesh.position.y=-1.39; scene.add(ringMesh);

// ── Particle stars ─────────────────────────────────────────────────────────────
var starGeo = new THREE.BufferGeometry();
var starsPos = [];
for(var i=0;i<80;i++){{
  starsPos.push((Math.random()-0.5)*8,(Math.random()-0.5)*6,(Math.random()*-4)-1);
}}
starGeo.setAttribute('position', new THREE.Float32BufferAttribute(starsPos,3));
var stars = new THREE.Points(starGeo, new THREE.PointsMaterial({{color:0x88aaff,size:0.04}}));
scene.add(stars);

// ── Avatar config ─────────────────────────────────────────────────────────────
var CONFIGS = {{
  '\uD83C\uDF99\uFE0F': {{
    name:'O Moderador', bodyCol:0x1a4a9f, legsCol:0x0d2560, skinCol:0xffcc99,
    extras:function(p){{
      // Headset arc
      var hsMat=new THREE.MeshPhongMaterial({{color:0x222222}});
      var hs=new THREE.Mesh(new THREE.TorusGeometry(0.3,0.04,8,24,Math.PI),hsMat);
      hs.position.set(0,0.82,0); hs.rotation.x=Math.PI; p.group.add(hs);
      // Earpads
      [-0.3,0.3].forEach(function(x){{
        var ep=new THREE.Mesh(new THREE.CylinderGeometry(0.07,0.07,0.04,12),hsMat);
        ep.position.set(x,0.82,0); ep.rotation.z=Math.PI/2; p.group.add(ep);
      }});
      // Mic arm
      var micArm=new THREE.Mesh(new THREE.CylinderGeometry(0.02,0.02,0.22,8),hsMat);
      micArm.position.set(0.28,0.68,0.1); micArm.rotation.z=-Math.PI/4; p.group.add(micArm);
      var micBall=new THREE.Mesh(new THREE.SphereGeometry(0.04,8,8),
        new THREE.MeshPhongMaterial({{color:0x111111,emissive:0xff3300,emissiveIntensity:0.8}}));
      micBall.position.set(0.38,0.58,0.14); p.group.add(micBall);
    }},
    animFn:function(p,t){{
      // Wave right arm
      p.armR.rotation.z = -0.7 + Math.sin(t*2.5)*0.55;
      p.armR.rotation.x = Math.sin(t*2.5)*0.15;
      p.armL.rotation.z = 0.15 + Math.sin(t*1.2)*0.08;
    }}
  }},
  '\u23F0': {{
    name:'O Pontual', bodyCol:0x186a32, legsCol:0x0d3d1a, skinCol:0xffbb88,
    extras:function(p){{
      // Watch on left wrist
      var watchMat=new THREE.MeshPhongMaterial({{color:0xccaa00,emissive:0x886600,emissiveIntensity:0.4}});
      var watch=new THREE.Mesh(new THREE.CylinderGeometry(0.06,0.06,0.04,12),watchMat);
      // Position on left arm (lower)
      var wg=new THREE.Group(); wg.position.set(0,-0.52,0); wg.add(watch); p.armL.add(wg);
      // Watch face details
      var face=new THREE.Mesh(new THREE.CylinderGeometry(0.055,0.055,0.01,12),
        new THREE.MeshPhongMaterial({{color:0xffffff,emissive:0x88ffff,emissiveIntensity:0.5}}));
      face.position.y=0.025; wg.add(face);
      // Checkmark badge above head
      var badgeMat=new THREE.MeshPhongMaterial({{color:0x00cc44,emissive:0x00aa33,emissiveIntensity:0.6}});
      var badge=new THREE.Mesh(new THREE.SphereGeometry(0.12,12,12),badgeMat);
      badge.position.set(0.4,1.15,0); p.group.add(badge);
      p._badge=badge;
    }},
    animFn:function(p,t){{
      // Left arm check watch
      p.armL.rotation.z = 0.2 + Math.sin(t*0.8)*0.15;
      p.armL.rotation.x = 0.4 + Math.sin(t*0.8)*0.1;
      // Right arm wave enthusiastically
      p.armR.rotation.z = -0.9 + Math.sin(t*3.0)*0.6;
      p.armR.rotation.x = Math.sin(t*3.0)*0.2;
      if(p._badge) p._badge.position.y = 1.15 + Math.sin(t*2)*0.05;
    }}
  }},
  '\uD83D\uDCCA': {{
    name:'O Apresentador', bodyCol:0x6a1a9f, legsCol:0x3d0d60, skinCol:0xffcc99,
    extras:function(p){{
      // Pointer stick in right hand
      var pMat=new THREE.MeshPhongMaterial({{color:0xdddddd}});
      var pointer=new THREE.Mesh(new THREE.CylinderGeometry(0.018,0.018,0.55,8),pMat);
      pointer.position.set(0,-0.85,0); pointer.rotation.z=-0.3; p.armR.add(pointer);
      var pTip=new THREE.Mesh(new THREE.SphereGeometry(0.035,8,8),
        new THREE.MeshPhongMaterial({{color:0xff2200,emissive:0xff0000,emissiveIntensity:1.0}}));
      pTip.position.set(0,-1.13,0); p.armR.add(pTip);
      // Mini slide board
      var board=new THREE.Mesh(new THREE.BoxGeometry(0.45,0.3,0.02),
        new THREE.MeshPhongMaterial({{color:0xffffff,emissive:0x8888ff,emissiveIntensity:0.2}}));
      board.position.set(-0.6,0.7,0.2); p.group.add(board);
      // Slide lines
      var lineMat=new THREE.MeshPhongMaterial({{color:0x0044ff,emissive:0x0022ff,emissiveIntensity:0.5}});
      [0.06,0,-.06].forEach(function(y,i){{
        var line=new THREE.Mesh(new THREE.BoxGeometry(0.3+i*0.05,0.025,0.025),lineMat);
        line.position.set(-0.6,0.7+y,0.22); p.group.add(line);
      }});
    }},
    animFn:function(p,t){{
      // Right arm points / gestures
      p.armR.rotation.z = -0.5 + Math.sin(t*1.5)*0.35;
      p.armR.rotation.x = -0.3 + Math.sin(t*1.5)*0.2;
      p.armL.rotation.z = 0.2+Math.sin(t*0.7)*0.1;
    }}
  }},
  '\uD83D\uDD07': {{
    name:'O Silenciado', bodyCol:0x9f3a1a, legsCol:0x601a0d, skinCol:0xffcc99,
    extras:function(p){{
      // Floating muted mic
      var micGroup=new THREE.Group();
      micGroup.position.set(0.5,0.4,0.3);
      var micBody=new THREE.Mesh(new THREE.CylinderGeometry(0.07,0.07,0.18,10),
        new THREE.MeshPhongMaterial({{color:0xaaaaaa}}));
      var micTop=new THREE.Mesh(new THREE.SphereGeometry(0.07,10,10),
        new THREE.MeshPhongMaterial({{color:0xaaaaaa}}));
      micTop.position.y=0.09; micGroup.add(micBody,micTop);
      // Red X / slash over mic
      var slashMat=new THREE.MeshPhongMaterial({{color:0xff2200,emissive:0xff0000,emissiveIntensity:0.8}});
      var slash=new THREE.Mesh(new THREE.BoxGeometry(0.04,0.35,0.04),slashMat);
      slash.rotation.z=Math.PI/4; micGroup.add(slash);
      p.group.add(micGroup);
      p._micGroup=micGroup;
      // Speech bubble hint
      var bubbleMat=new THREE.MeshPhongMaterial({{color:0xff8800,emissive:0xff6600,emissiveIntensity:0.3}});
      var bubble=new THREE.Mesh(new THREE.SphereGeometry(0.1,10,10),bubbleMat);
      bubble.position.set(-0.5,0.7,0.3); bubble.scale.set(1.5,0.8,0.5); p.group.add(bubble);
    }},
    animFn:function(p,t){{
      // Both arms gesturing "I'm talking!"
      p.armR.rotation.z = -0.4 + Math.sin(t*2.2)*0.5;
      p.armL.rotation.z = 0.4 + Math.sin(t*2.2+1)*0.4;
      p.armR.rotation.x = Math.sin(t*2.2)*0.2;
      // Mic floats
      if(p._micGroup) p._micGroup.position.y = 0.4 + Math.sin(t*1.5)*0.1;
      // Head "talking" nod
      p.head.rotation.x = Math.sin(t*3)*0.1;
    }}
  }},
  '\uD83D\uDCDD': {{
    name:'O Secret\u00e1rio', bodyCol:0x0f7a6a, legsCol:0x084d42, skinCol:0xffbb88,
    extras:function(p){{
      // Notepad in left hand
      var padMat=new THREE.MeshPhongMaterial({{color:0xffffff,emissive:0xaaaaff,emissiveIntensity:0.15}});
      var pad=new THREE.Mesh(new THREE.BoxGeometry(0.22,0.3,0.03),padMat);
      pad.position.set(0,-0.7,0.1); p.armL.add(pad);
      // Lines on notepad
      var lMat=new THREE.MeshPhongMaterial({{color:0x8888cc}});
      [-0.08,-0.02,0.04,0.1].forEach(function(y){{
        var l=new THREE.Mesh(new THREE.BoxGeometry(0.16,0.015,0.04),lMat);
        l.position.set(0,y+(-0.7),0.12); p.armL.add(l);
      }});
      // Pen in right hand
      var pen=new THREE.Mesh(new THREE.CylinderGeometry(0.015,0.015,0.3,8),
        new THREE.MeshPhongMaterial({{color:0x1188ff}}));
      pen.position.set(0,-0.75,0.1); pen.rotation.z=0.3; p.armR.add(pen);
    }},
    animFn:function(p,t){{
      // Writing motion
      p.armR.rotation.z = -0.15 + Math.sin(t*4)*0.25;
      p.armR.rotation.x = 0.4 + Math.sin(t*4)*0.15;
      // Left arm holds pad steady
      p.armL.rotation.z = 0.3;
      p.armL.rotation.x = 0.35;
    }}
  }},
  '\uD83D\uDCF6': {{
    name:'O T\u00e9cnico', bodyCol:0x4a4a5a, legsCol:0x2a2a3a, skinCol:0xffcc99,
    extras:function(p){{
      // Glasses
      var gMat=new THREE.MeshPhongMaterial({{color:0x111111}});
      var glassFrame=new THREE.Mesh(new THREE.TorusGeometry(0.09,0.015,8,20),gMat);
      glassFrame.position.set(0.1,0.84,0.27); p.group.add(glassFrame);
      var glassFrame2=new THREE.Mesh(new THREE.TorusGeometry(0.09,0.015,8,20),gMat);
      glassFrame2.position.set(-0.1,0.84,0.27); p.group.add(glassFrame2);
      var bridge=new THREE.Mesh(new THREE.BoxGeometry(0.04,0.015,0.015),gMat);
      bridge.position.set(0,0.84,0.27); p.group.add(bridge);
      // WiFi arcs above head
      var wMat=new THREE.MeshPhongMaterial({{color:0x00aaff,emissive:0x0088ff,emissiveIntensity:0.8}});
      [0.18,0.28,0.38].forEach(function(r,i){{
        var arc=new THREE.Mesh(new THREE.TorusGeometry(r,0.02,8,20,Math.PI),wMat.clone());
        arc.position.set(0,1.1+i*0.05,0); p.group.add(arc);
        arc._idx=i;
        if(!p._wifiArcs) p._wifiArcs=[];
        p._wifiArcs.push(arc);
      }});
      // Tool/wrench prop
      var toolMat=new THREE.MeshPhongMaterial({{color:0x888888}});
      var tool=new THREE.Mesh(new THREE.CylinderGeometry(0.025,0.025,0.35,8),toolMat);
      tool.position.set(0,-0.7,0); tool.rotation.z=0.3; p.armR.add(tool);
    }},
    animFn:function(p,t){{
      // Jitter / glitch effect
      var jitter = Math.random() < 0.03 ? (Math.random()-0.5)*0.15 : 0;
      p.group.position.x = jitter;
      // Right arm scratches head
      p.armR.rotation.z = -1.2 + Math.sin(t*3)*0.2;
      p.armR.rotation.x = -0.6 + Math.sin(t*3)*0.1;
      p.armL.rotation.z = 0.1 + Math.sin(t*1.1)*0.1;
      // WiFi arcs pulse
      if(p._wifiArcs) p._wifiArcs.forEach(function(arc,i){{
        arc.material.emissiveIntensity = 0.3 + Math.abs(Math.sin(t*2 - i*0.5))*1.0;
      }});
    }}
  }},
  '\uD83D\uDC54': {{
    name:'O Executivo', bodyCol:0x1a1a2e, legsCol:0x8899aa, skinCol:0xffcc99,
    extras:function(p){{
      // Tie
      var tieMat=new THREE.MeshPhongMaterial({{color:0xcc1122,emissive:0x880011,emissiveIntensity:0.3}});
      var tie=new THREE.Mesh(new THREE.BoxGeometry(0.08,0.35,0.035),tieMat);
      tie.position.set(0,0.18,0.16); p.group.add(tie);
      var tieTop=new THREE.Mesh(new THREE.BoxGeometry(0.1,0.07,0.04),tieMat);
      tieTop.position.set(0,0.38,0.16); p.group.add(tieTop);
      // Jacket lapels
      var lapelMat=new THREE.MeshPhongMaterial({{color:0x282838}});
      var lapelR=new THREE.Mesh(new THREE.BoxGeometry(0.12,0.25,0.035),lapelMat);
      lapelR.position.set(0.15,0.32,0.16); lapelR.rotation.z=-0.3; p.group.add(lapelR);
      var lapelL=new THREE.Mesh(new THREE.BoxGeometry(0.12,0.25,0.035),lapelMat);
      lapelL.position.set(-0.15,0.32,0.16); lapelL.rotation.z=0.3; p.group.add(lapelL);
      // Pajama stripes on legs (colorful)
      var stMat=new THREE.MeshPhongMaterial({{color:0xffcc00}});
      [-0.08,0,0.08].forEach(function(y){{
        var stripe=new THREE.Mesh(new THREE.BoxGeometry(0.42,0.04,0.2),stMat);
        stripe.position.set(0,-0.58+y,0); p.group.add(stripe);
      }});
    }},
    animFn:function(p,t){{
      // Professional wave + tie adjustment
      p.armR.rotation.z = -0.6 + Math.sin(t*2.0)*0.5;
      p.armR.rotation.x = Math.sin(t*2.0)*0.1;
      // Left arm adjusts tie occasionally
      var tiePhase = Math.sin(t*0.5);
      p.armL.rotation.z = 0.1 + (tiePhase > 0.7 ? 0.4 : 0.0);
      p.armL.rotation.x = tiePhase > 0.7 ? 0.35 : 0.0;
    }}
  }},
  '\uD83C\uDFE0': {{
    name:'O Remoto', bodyCol:0x3a1a6a, legsCol:0x888888, skinCol:0xffd0a0,
    extras:function(p){{
      // Hoodie pocket
      var pocketMat=new THREE.MeshPhongMaterial({{color:0x2a0a5a}});
      var pocket=new THREE.Mesh(new THREE.BoxGeometry(0.2,0.12,0.035),pocketMat);
      pocket.position.set(0,-0.08,0.15); p.group.add(pocket);
      // Headphones
      var hpMat=new THREE.MeshPhongMaterial({{color:0x222233}});
      var hpArc=new THREE.Mesh(new THREE.TorusGeometry(0.32,0.035,8,24,Math.PI),hpMat);
      hpArc.position.set(0,0.82,0); hpArc.rotation.x=Math.PI; p.group.add(hpArc);
      [-0.32,0.32].forEach(function(x){{
        var cup=new THREE.Mesh(new THREE.CylinderGeometry(0.09,0.09,0.05,12),hpMat);
        cup.position.set(x,0.82,0); cup.rotation.z=Math.PI/2; p.group.add(cup);
        var cushion=new THREE.Mesh(new THREE.CylinderGeometry(0.08,0.08,0.04,12),
          new THREE.MeshPhongMaterial({{color:0x4444ff,emissive:0x2222ff,emissiveIntensity:0.3}}));
        cushion.position.set(x+(x>0?0.04:-0.04),0.82,0); cushion.rotation.z=Math.PI/2; p.group.add(cushion);
      }});
      // Coffee mug in left hand
      var mugMat=new THREE.MeshPhongMaterial({{color:0xcc4400}});
      var mug=new THREE.Mesh(new THREE.CylinderGeometry(0.06,0.055,0.12,12),mugMat);
      mug.position.set(0,-0.68,0.05); p.armL.add(mug);
      var mugTop=new THREE.Mesh(new THREE.CylinderGeometry(0.06,0.06,0.01,12),
        new THREE.MeshPhongMaterial({{color:0x331100}}));
      mugTop.position.set(0,-0.62,0.05); p.armL.add(mugTop);
      // Steam particles (small spheres)
      for(var i=0;i<3;i++){{
        var steam=new THREE.Mesh(new THREE.SphereGeometry(0.02,6,6),
          new THREE.MeshPhongMaterial({{color:0xffffff,emissive:0xffffff,emissiveIntensity:0.5,transparent:true,opacity:0.6}}));
        steam.position.set(i*0.03-0.03,-0.55+i*0.06,0.05); p.armL.add(steam);
        steam._steamIdx=i;
        if(!p._steamParts) p._steamParts=[];
        p._steamParts.push(steam);
      }}
    }},
    animFn:function(p,t){{
      // Casual wave
      p.armR.rotation.z = -0.5 + Math.sin(t*2.0)*0.5;
      p.armR.rotation.x = Math.sin(t*2.0)*0.15;
      // Left arm holds coffee steady
      p.armL.rotation.z = 0.25;
      p.armL.rotation.x = 0.25;
      // Steam rises
      if(p._steamParts) p._steamParts.forEach(function(s){{
        s.position.y = -0.55 + s._steamIdx*0.06 + ((t*0.5+s._steamIdx*0.3) % 0.3);
        s.material.opacity = 0.6 - ((t*0.5+s._steamIdx*0.3) % 0.3)*2;
      }});
    }}
  }}
}};

// Emoji key normalization map (session_state stores these)
var KEY_MAP = {{
  '\uD83C\uDF99\uFE0F':'\uD83C\uDF99\uFE0F',
  '\uD83C\uDF99':'\uD83C\uDF99\uFE0F',
  '\u23F0':'\u23F0',
  '\uD83D\uDCCA':'\uD83D\uDCCA',
  '\uD83D\uDD07':'\uD83D\uDD07',
  '\uD83D\uDCDD':'\uD83D\uDCDD',
  '\uD83D\uDCF6':'\uD83D\uDCF6',
  '\uD83D\uDC54':'\uD83D\uDC54',
  '\uD83C\uDFE0':'\uD83C\uDFE0'
}};
AVATAR_KEY = KEY_MAP[AVATAR_KEY] || AVATAR_KEY;

var config = CONFIGS[AVATAR_KEY];
if(!config) {{
  document.getElementById('av3d-name').textContent = 'Seleciona um avatar';
  document.getElementById('av3d-hint').textContent = '\u2b06\ufe0f Escolhe acima';
  // Show a simple rotating question mark placeholder
  var qMat = new THREE.MeshPhongMaterial({{color:0x1155aa,emissive:0x0033aa,emissiveIntensity:0.5}});
  var qMesh = new THREE.Mesh(new THREE.TorusGeometry(0.5,0.12,12,40),qMat);
  qMesh.position.y=0; scene.add(qMesh);
  var animate0=function(){{
    requestAnimationFrame(animate0);
    qMesh.rotation.y+=0.02; qMesh.rotation.x+=0.01;
    ringMesh.material.emissiveIntensity=0.4+Math.sin(Date.now()*0.002)*0.3;
    renderer.render(scene,camera);
  }}; animate0(); return;
}}

document.getElementById('av3d-name').textContent = config.name;
document.getElementById('av3d-hint').textContent = '\u2728 clica e vai jogar!';

// ── Build base character ───────────────────────────────────────────────────────
function buildCharacter(cfg){{
  var g=new THREE.Group();
  var skinMat=new THREE.MeshPhongMaterial({{color:cfg.skinCol,shininess:40}});
  var bodyMat=new THREE.MeshPhongMaterial({{color:cfg.bodyCol,shininess:80}});
  var legsMat=new THREE.MeshPhongMaterial({{color:cfg.legsCol,shininess:60}});
  var shoesMat=new THREE.MeshPhongMaterial({{color:0x111111,shininess:120}});

  // HEAD
  var head=new THREE.Mesh(new THREE.SphereGeometry(0.28,16,16),skinMat);
  head.position.y=0.82; g.add(head);

  // Eyes (whites + pupils)
  [-0.1,0.1].forEach(function(x){{
    var ew=new THREE.Mesh(new THREE.SphereGeometry(0.075,10,10),
      new THREE.MeshPhongMaterial({{color:0xffffff}}));
    ew.position.set(x,0.84,0.23); g.add(ew);
    var ep=new THREE.Mesh(new THREE.SphereGeometry(0.04,10,10),
      new THREE.MeshPhongMaterial({{color:0x111111}}));
    ep.position.set(x,0.84,0.29); g.add(ep);
  }});

  // Smile
  var smileMat=new THREE.MeshPhongMaterial({{color:0x552200}});
  var smile=new THREE.Mesh(new THREE.TorusGeometry(0.09,0.018,8,16,Math.PI),smileMat);
  smile.position.set(0,0.72,0.26); smile.rotation.z=Math.PI; g.add(smile);

  // NECK
  var neck=new THREE.Mesh(new THREE.CylinderGeometry(0.1,0.12,0.14,10),skinMat);
  neck.position.y=0.57; g.add(neck);

  // BODY
  var body=new THREE.Mesh(new THREE.BoxGeometry(0.55,0.65,0.28),bodyMat);
  body.position.y=0.18; g.add(body);

  // ARM RIGHT (wave arm) — pivot at shoulder
  var armR=new THREE.Group(); armR.position.set(0.38,0.44,0);
  var armRM=new THREE.Mesh(new THREE.BoxGeometry(0.14,0.52,0.14),bodyMat);
  armRM.position.y=-0.26; armR.add(armRM);
  var handR=new THREE.Mesh(new THREE.SphereGeometry(0.09,10,10),skinMat);
  handR.position.y=-0.56; armR.add(handR);
  g.add(armR);

  // ARM LEFT — pivot at shoulder
  var armL=new THREE.Group(); armL.position.set(-0.38,0.44,0);
  var armLM=new THREE.Mesh(new THREE.BoxGeometry(0.14,0.52,0.14),bodyMat);
  armLM.position.y=-0.26; armL.add(armLM);
  var handL=new THREE.Mesh(new THREE.SphereGeometry(0.09,10,10),skinMat);
  handL.position.y=-0.56; armL.add(handL);
  g.add(armL);

  // LEGS
  var legR=new THREE.Mesh(new THREE.BoxGeometry(0.18,0.5,0.18),legsMat);
  legR.position.set(0.14,-0.56,0); g.add(legR);
  var legL=new THREE.Mesh(new THREE.BoxGeometry(0.18,0.5,0.18),legsMat);
  legL.position.set(-0.14,-0.56,0); g.add(legL);

  // FEET
  var footR=new THREE.Mesh(new THREE.BoxGeometry(0.2,0.09,0.28),shoesMat);
  footR.position.set(0.14,-0.84,0.05); g.add(footR);
  var footL=new THREE.Mesh(new THREE.BoxGeometry(0.2,0.09,0.28),shoesMat);
  footL.position.set(-0.14,-0.84,0.05); g.add(footL);

  return {{group:g, head:head, armR:armR, armL:armL, legR:legR, legL:legL}};
}}

var parts = buildCharacter(config);
config.extras(parts);
scene.add(parts.group);

// ── Animation loop ─────────────────────────────────────────────────────────────
var t=0;
function animate(){{
  requestAnimationFrame(animate);
  t += 0.016;

  // Float
  parts.group.position.y = Math.sin(t*1.1)*0.07;
  // Slow Y-axis sway for 3D showcase
  parts.group.rotation.y = Math.sin(t*0.38)*0.4;
  // Head sway
  parts.head.rotation.z = Math.sin(t*0.85)*0.07;
  parts.head.rotation.y = Math.sin(t*0.6)*0.1;

  // Ring glow pulse
  ringMesh.material.emissiveIntensity = 0.5+Math.sin(t*1.8)*0.5;

  // Star field slow rotation
  stars.rotation.y += 0.001;

  // Character-specific
  config.animFn(parts, t);

  renderer.render(scene, camera);
}}
animate();
}})();
</script>
</body>
</html>""", height=340)


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






# ── Countdown de entrada — página exclusiva, sem título nem formulário ────────
if st.session_state.get('show_countdown'):
    # Botão oculto que o JS clica após o countdown
    if st.button("▶", key="btn_start_quiz_hidden"):
        st.session_state.user_id = st.session_state.pending_user_id
        st.session_state.show_countdown = False
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

    // Após GO! — clicar o botão oculto com retry para garantir que é encontrado
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
        // Botão ainda não carregou — tentar novamente
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
    st.markdown("""
    <div class="login-box">
        <h2 style="color:#7eb8ff; margin-bottom:20px;">👤 Identificação</h2>
        <p style="color:#aac8ff; font-size:16px;">Insere o teu nome para começar o quiz</p>
    </div>
    """, unsafe_allow_html=True)

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

    _AVATARS = [
        ("🎙️", "Moderador"),   ("⏰", "Pontual"),
        ("📊", "Apresentador"), ("🔇", "Silenciado"),
        ("📝", "Secretário"),   ("📶", "Técnico"),
        ("👔", "Executivo"),    ("🏠", "Remoto"),
    ]

    st.markdown('<p style="color:#aac8ff; text-align:center; font-size:14px; margin:14px 0 6px 0;">🎭 Escolhe o teu avatar de reunião:</p>', unsafe_allow_html=True)

    _av_cols = st.columns(8)
    for _i, (_av_emoji, _av_name) in enumerate(_AVATARS):
        with _av_cols[_i]:
            if st.session_state.avatar == _av_emoji:
                _av_label = f"✅\n{_av_emoji}\n{_av_name}"
            else:
                _av_label = f"{_av_emoji}\n{_av_name}"
            if st.button(_av_label, key=f"av_btn_{_i}", use_container_width=True):
                st.session_state.avatar = _av_emoji
                st.rerun()

    # 3D avatar preview — shows animated 3D character for the selected avatar
    render_3d_avatar_preview(st.session_state.avatar or "")

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

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        user_id = st.text_input("", placeholder="O teu nome...", label_visibility="collapsed")
        if st.button("▶️  COMEÇAR O QUIZ", use_container_width=True):
            import re as _re
            if st.session_state.get('avatar') is None:
                st.warning("Por favor escolhe um avatar! 🎭")
            elif not user_id.strip():
                st.warning("Por favor insere o teu nome.")
            elif not _re.fullmatch(r"[A-Za-zÀ-ÿ\s]+", user_id.strip()):
                st.error("❌ Nome inválido — só são aceites letras.")
            elif ja_jogou(user_id.strip(), resultados):
                dados = resultados[user_id.strip()]
                st.error("Este utilizador já jogou.")
                st.info(f"Pontuação anterior: {dados['score']}/10 — {dados['data']} às {dados['hora']}")
            else:
                st.session_state.pending_user_id = user_id.strip()
                st.session_state.show_countdown = True
                st.rerun()

    # Música persistente — sobrevive a reruns via window.parent
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

# Música persistente — já inicializada no login, apenas garante continuidade
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

    # ── Ranking dos Participantes ─────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    _res_rank = carregar_resultados()
    if _res_rank:
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
        st.markdown(f"""
<div style="display:flex;justify-content:center;width:100%;">
  <div style="background:linear-gradient(135deg,#0d1f4a 0%,#050e2a 100%);
      border:1px solid #1e3a7a;border-radius:16px;
      padding:20px 24px;width:100%;max-width:560px;">
    <h3 style="color:#ffd700;text-align:center;margin:0 0 14px 0;font-size:18px;">
        🏆 Ranking dos Participantes
    </h3>
    {_rows_html}
  </div>
</div>""", unsafe_allow_html=True)

    # ── Desafiar Amigo ────────────────────────────────────────────────────────
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

    # ── Botão jogar novamente ────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Jogar Novamente", use_container_width=True, key="btn_jogar_nov"):
            reset_para_novo_jogo()
            st.rerun()

    # Auto-refresh do ranking a cada 30 segundos (mantém sessão e música)
    import time as _t_res
    _t_res.sleep(30)
    st.rerun()

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
    <span style="font-size: 22px;">{st.session_state.get('avatar', '👤')}</span>
    <span style="color: #7eb8ff; font-size: 15px; font-weight: bold; letter-spacing: 1px;">{st.session_state.user_id}</span>
</div>
""", unsafe_allow_html=True)

# ── Avatar mascot animado ─────────────────────────────────────────────────────
_avatar_emoji = st.session_state.get('avatar', '🧑‍💻')
_resp_dada_av = st.session_state.resposta_dada
_streak_av    = st.session_state.get('streak', 0)
_pending_av   = st.session_state.pendente_resposta

import time as _time
_elapsed_av   = (_time.time() * 1000 - _timer_start_ms) / 1000
_remaining_av = max(0, 60 - _elapsed_av)

if _resp_dada_av == -1:
    _av_mood = 'shocked';  _av_speech = '⏰ Tempo!'
elif _resp_dada_av is not None:
    if _resp_dada_av == correta:
        _av_mood = 'happy';  _av_speech = '🎉 Certo!'
    else:
        _av_mood = 'sad';    _av_speech = '😅 Quase!'
elif _streak_av >= 3:
    _av_mood = 'fire';    _av_speech = f'🔥 {_streak_av} seguidas!'
elif _remaining_av <= 10:
    _av_mood = 'nervous'; _av_speech = '⚡ Depressa!'
elif _pending_av is not None:
    _av_mood = 'pending'; _av_speech = '🤔 Confirma?'
else:
    _av_mood = 'idle';    _av_speech = ''

render_avatar_mascot(_avatar_emoji, _av_mood, _av_speech)

# ── Streak display ────────────────────────────────────────────────────────────
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
            # Atualizar streak
            if pendente == correta:
                st.session_state.streak = st.session_state.get('streak', 0) + 1
                st.session_state.max_streak = max(st.session_state.get('max_streak', 0), st.session_state.streak)
            else:
                st.session_state.streak = 0
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
