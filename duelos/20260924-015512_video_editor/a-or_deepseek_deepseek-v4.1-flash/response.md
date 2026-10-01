This is a self-contained HTML document that builds a small procedural video editor with a dark professional interface. It automatically plays a demo montage with transitions, titles, clip trimming, and moving.
```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NovaCut — Procedural Timeline Demo</title>
<style>
  :root{
    --bg:#080a0e; --panel:#10131a; --panel2:#151922; --line:#232936; --line2:#2b3342;
    --txt:#c7d0dd; --dim:#66738a; --accent:#38bdf8; --accent2:#a855f7;
  }
  *{box-sizing:border-box}
  html,body{margin:0;height:100%;overflow:hidden;background:var(--bg);color:var(--txt);
    font-family:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;font-size:13px;
    -webkit-font-smoothing:antialiased}
  .app{display:flex;flex-direction:column;height:100vh}

  /* ---------- toolbar ---------- */
  .toolbar{height:52px;flex:none;display:flex;align-items:center;gap:12px;padding:0 14px;
    background:linear-gradient(180deg,#161b25,#0e1117);border-bottom:1px solid var(--line);
    position:relative;z-index:6;box-shadow:0 1px 0 rgba(255,255,255,.03)}
  .brand{display:flex;align-items:center;gap:9px;font-weight:700;letter-spacing:.16em;font-size:12px;color:#e8eefc}
  .brand i{width:11px;height:11px;border-radius:3px;background:linear-gradient(135deg,#38bdf8,#a855f7);
    box-shadow:0 0 12px rgba(56,189,248,.7)}
  .brand small{font-weight:400;color:#5f6b80;letter-spacing:.08em;margin-left:1px}
  .tools{display:flex;gap:5px;padding-left:12px;border-left:1px solid var(--line2)}
  .spacer{flex:1}
  button{font:inherit;color:#c7d0dd;background:#1a1f2b;border:1px solid var(--line2);border-radius:6px;
    height:28px;min-width:32px;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;
    transition:background .15s,border-color .15s,color .15s;padding:0 8px}
  button:hover{background:#232a38;border-color:#3a4557}
  button.active{background:#123047;border-color:var(--accent);color:#dff2ff}
  .transport{display:flex;gap:5px}
  #btnPlay{min-width:42px;background:#153044;border-color:#2b5f85;color:#cdeeff;font-size:12px}
  #btnPlay:hover{background:#1b415c}
  .timecode{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:16px;font-weight:600;color:#eaf6ff;
    background:#0b0e14;border:1px solid var(--line2);border-radius:6px;padding:3px 11px;letter-spacing:.06em;
    box-shadow:inset 0 0 14px rgba(56,189,248,.09)}
  .io{display:flex;gap:6px}
  .chip{font-size:10px;letter-spacing:.12em;color:#77839a;background:#141924;border:1px solid var(--line);
    border-radius:5px;padding:3px 8px;display:flex;gap:6px;align-items:center}
  .chip b{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:11px;color:#b9c7da;letter-spacing:0}
  .chip:first-child b{color:#86efac}
  .chip:last-child b{color:#fcd34d}
  .zoomwrap{display:flex;align-items:center;gap:8px;font-size:10px;letter-spacing:.14em;color:#66738a}
  input[type=range]{-webkit-appearance:none;appearance:none;width:120px;height:4px;border-radius:3px;
    background:linear-gradient(90deg,#2b3342,#3a4557);outline:none;cursor:pointer}
  input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:13px;height:13px;border-radius:50%;
    background:radial-gradient(circle at 35% 35%,#bfe9ff,#38bdf8);border:1px solid #0b0e14;
    box-shadow:0 0 8px rgba(56,189,248,.8);cursor:pointer}
  input[type=range]::-moz-range-thumb{width:13px;height:13px;border-radius:50%;background:#38bdf8;border:none}

  /* ---------- stage ---------- */
  .stage{flex:1;min-height:0;display:flex;gap:10px;padding:10px}
  .preview-panel{flex:1;min-width:0;position:relative;background:
      radial-gradient(circle at 50% 40%,#151a24,#0b0d12 70%);
    border:1px solid var(--line);border-radius:9px;display:grid;place-items:center;padding:12px;overflow:hidden}
  #preview{max-width:100%;max-height:100%;display:block;border-radius:6px;background:#000;
    box-shadow:0 0 0 1px #232936, 0 20px 46px rgba(0,0,0,.65)}
  .badge{position:absolute;top:14px;right:16px;font-size:10.5px;font-weight:700;letter-spacing:.14em;
    padding:5px 10px;border-radius:5px;background:rgba(10,20,32,.78);border:1px solid rgba(56,189,248,.55);
    color:#bfe9ff;opacity:0;transition:opacity .18s;pointer-events:none;
    box-shadow:0 0 16px rgba(56,189,248,.25)}
  .hud{position:absolute;left:18px;top:14px;font-size:10.5px;letter-spacing:.14em;color:#8b98ad;
    background:rgba(10,13,19,.7);border:1px solid var(--line);padding:4px 9px;border-radius:5px;pointer-events:none}

  /* ---------- side ---------- */
  .side{width:262px;flex:none;background:var(--panel);border:1px solid var(--line);border-radius:9px;
    padding:11px;display:flex;flex-direction:column;gap:9px;overflow:hidden}
  .side h3{margin:0;font-size:9.5px;letter-spacing:.18em;color:#5f6b80;text-transform:uppercase;font-weight:700}
  .kv{display:flex;justify-content:space-between;align-items:center;font-size:12px;padding:5px 0;
    border-bottom:1px solid #191e28}
  .kv span{color:#77839a;letter-spacing:.04em}
  .kv b{color:#dbe6f5;font-weight:600;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:11.5px}
  .log{flex:1;min-height:0;overflow:hidden;display:flex;flex-direction:column;gap:5px;justify-content:flex-end}
  .log div{color:#9fb0c6;background:#151a24;border-left:2px solid var(--accent);padding:5px 8px;
    border-radius:4px;font-size:11.5px;animation:slideIn .32s ease}
  @keyframes slideIn{from{opacity:0;transform:translateX(10px)}to{opacity:1;transform:none}}

  /* ---------- timeline ---------- */
  .timeline{height:266px;flex:none;background:var(--panel);border-top:1px solid var(--line);
    display:flex;flex-direction:column;position:relative;z-index:4}
  .tl-toolbar{height:34px;flex:none;display:flex;align-items:center;gap:14px;padding:0 14px;
    border-bottom:1px solid var(--line);background:var(--panel2)}
  .tl-title{font-size:10px;letter-spacing:.2em;color:#66738a;font-weight:700}
  .tl-legend{display:flex;align-items:center;gap:6px;font-size:10.5px;color:#77839a}
  .lc{width:9px;height:9px;border-radius:2px;display:inline-block;margin-left:8px}
  .lc.v{background:#3b82f6}.lc.t{background:#f59e0b}.lc.a{background:#22c55e}
  .tl-hint{font-size:10.5px;color:#4e5a6d;letter-spacing:.04em}
  .tl-body{flex:1;min-height:0;display:flex}
  .tl-headers{width:112px;flex:none;background:var(--panel2);border-right:1px solid var(--line)}
  .h-spacer{height:26px;border-bottom:1px solid var(--line)}
  .h-track{display:flex;flex-direction:column;justify-content:center;padding:0 10px;border-bottom:1px solid var(--line);
    font-size:12px;font-weight:700;color:#aebbd0;letter-spacing:.08em}
  .h-track span{font-size:9px;color:#5f6b80;letter-spacing:.16em;font-weight:600;margin-top:1px}
  .h-video{height:62px;box-shadow:inset 3px 0 0 #3b82f6}
  .h-text{height:42px;box-shadow:inset 3px 0 0 #f59e0b}
  .h-audio{height:64px;box-shadow:inset 3px 0 0 #22c55e}
  .tl-scroll{flex:1;min-width:0;overflow-x:auto;overflow-y:hidden;position:relative;
    scrollbar-color:#2b3342 #101319;scrollbar-width:thin}
  .tl-scroll::-webkit-scrollbar{height:9px}
  .tl-scroll::-webkit-scrollbar-track{background:#0d1016}
  .tl-scroll::-webkit-scrollbar-thumb{background:#2b3342;border-radius:6px}
  .tl-content{position:relative;height:100%;min-width:100%}
  .ruler{height:26px;position:relative;border-bottom:1px solid var(--line);background:#0d1016;
    background-image:linear-gradient(180deg,#12161f,#0d1016)}
  .track{position:relative;border-bottom:1px solid var(--line);background:#0d1016}
  .track-video{height:62px;background:#0f131b}
  .track-text{height:42px;background:#0f1218}
  .track-audio{height:64px;background:#0e1319}

  .clip{position:absolute;top:3px;bottom:3px;border-radius:5px;overflow:hidden;cursor:grab;
    user-select:none;touch-action:none;z-index:3;
    border:1px solid rgba(255,255,255,.16);box-shadow:0 3px 10px rgba(0,0,0,.5);
    transition:box-shadow .18s,border-color .18s}
  .clip:active{cursor:grabbing}
  .clip.hot{border-color:#7dd3fc;box-shadow:0 0 0 1px #38bdf8,0 0 18px rgba(56,189,248,.55);z-index:4}
  .clip .label{position:absolute;left:7px;right:7px;top:3px;font-size:10.5px;font-weight:600;color:#eef6ff;
    text-shadow:0 1px 3px rgba(0,0,0,.95);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
    pointer-events:none;z-index:3;letter-spacing:.03em}
  .clip canvas.thumb{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.55;
    pointer-events:none}
  .clip .grad{position:absolute;inset:0;background:linear-gradient(180deg,rgba(6,10,18,.85),rgba(6,10,18,.15) 55%);
    pointer-events:none;z-index:2}
  .clip .handle{position:absolute;top:0;bottom:0;width:8px;cursor:ew-resize;z-index:5;
    background:linear-gradient(180deg,rgba(255,255,255,.22),rgba(255,255,255,.06))}
  .clip .handle.l{left:0;border-radius:5px 0 0 5px}
  .clip .handle.r{right:0;border-radius:0 5px 5px 0}
  .clip .handle:hover{background:rgba(125,211,252,.55)}
  .clip.video{background:linear-gradient(180deg,rgba(59,130,246,.42),rgba(30,64,120,.55))}
  .clip.textclip{background:linear-gradient(180deg,rgba(245,158,11,.42),rgba(120,53,15,.6));
    border-color:rgba(253,224,71,.4)}
  .clip.audio{background:linear-gradient(180deg,rgba(34,197,94,.22),rgba(6,50,30,.6));
    border-color:rgba(74,222,128,.4)}
  .clip canvas.wave{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;opacity:.95}

  .trans{position:absolute;top:3px;bottom:3px;z-index:4;pointer-events:none;border-radius:4px;
    display:flex;align-items:flex-end;justify-content:center;overflow:hidden}
  .trans.crossfade{background-image:repeating-linear-gradient(45deg,rgba(168,85,247,.55) 0 5px,
    rgba(168,85,247,.15) 5px 10px);border:1px solid rgba(192,132,252,.75)}
  .trans.wipe{background-image:repeating-linear-gradient(-45deg,rgba(56,189,248,.55) 0 5px,
    rgba(56,189,248,.15) 5px 10px);border:1px solid rgba(125,211,252,.8)}
  .trans span{font-size:8.5px;font-weight:700;letter-spacing:.08em;color:#f4f8ff;background:rgba(8,10,16,.72);
    padding:1px 4px;border-radius:3px;margin-bottom:2px;white-space:nowrap;text-transform:uppercase}

  .shade{position:absolute;top:0;bottom:0;background:rgba(4,6,10,.62);z-index:6;pointer-events:none;
    border-right:1px solid rgba(255,255,255,.05)}
  .marker{position:absolute;top:0;bottom:0;width:0;z-index:8;pointer-events:none}
  .marker span{position:absolute;top:2px;transform:translateX(-50%);font-size:8.5px;font-weight:800;
    letter-spacing:.1em;padding:1px 5px;border-radius:3px;white-space:nowrap}
  .marker.in{border-left:1px solid #22c55e}
  .marker.out{border-left:1px solid #f59e0b}
  .marker.in span{background:#0f3d24;color:#86efac;border:1px solid #22c55e}
  .marker.out span{background:#3d2a0d;color:#fcd34d;border:1px solid #f59e0b}

  .playhead{position:absolute;top:0;bottom:0;left:0;width:2px;background:#ff5d5d;z-index:20;
    pointer-events:none;will-change:transform;box-shadow:0 0 9px rgba(255,80,80,.85)}
  .playhead::before{content:"";position:absolute;top:0;left:-5px;border-left:6px solid transparent;
    border-right:6px solid transparent;border-top:9px solid #ff5d5d}

  .tick{position:absolute;bottom:0;width:1px;height:7px;background:#333c4b}
  .tick.major{height:12px;background:#4a566a}
  .ticklabel{position:absolute;top:3px;font-size:10px;color:#66738a;letter-spacing:.04em;
    font-family:ui-monospace,Menlo,Consolas,monospace}

  .ghost{position:fixed;left:0;top:0;width:20px;height:20px;margin:-10px 0 0 -10px;border-radius:50%;
    border:2px solid #e8f6ff;background:rgba(56,189,248,.35);pointer-events:none;z-index:999;
    opacity:0;transition:opacity .22s;box-shadow:0 0 16px rgba(56,189,248,.9);
    display:grid;place-items:center}
  .ghost::after{content:"";width:5px;height:5px;border-radius:50%;background:#eaf6ff}
</style>
</head>
<body>
<div class="app">

  <header class="toolbar">
    <div class="brand"><i></i>NOVACUT<small>v1.4</small></div>
    <div class="tools">
      <button class="tbtn active" title="Select">&#8598;</button>
      <button class="tbtn" title="Razor">&#9986;</button>
      <button class="tbtn" title="Text">T</button>
      <button class="tbtn" title="Transitions">&#8646;</button>
    </div>
    <div class="spacer"></div>
    <div class="transport">
      <button id="btnStart" title="Go to start">&#9198;</button>
      <button id="btnPlay" title="Play / Pause">&#10074;&#10074;</button>
      <button id="btnEnd" title="Go to end">&#9197;</button>
    </div>
    <div class="timecode" id="tc">00:00:00:00</div>
    <div class="io">
      <div class="chip">IN <b id="inTc">00:00:00:00</b></div>
      <div class="chip">OUT <b id="outTc">00:00:22:00</b></div>
    </div>
    <div class="zoomwrap">
      <span>ZOOM</span>
      <input id="zoom" type="range" min="0.55" max="2.6" step="0.01" value="1">
    </div>
  </header>

  <div class="stage">
    <div class="preview-panel">
      <canvas id="preview" width="960" height="540"></canvas>
      <div class="badge" id="transBadge">CROSSFADE</div>
      <div class="hud" id="hud">V1 &middot; &mdash;</div>
    </div>

    <aside class="side">
      <h3>Inspector</h3>
      <div class="kv"><span>Active clip</span><b id="inspClip">&mdash;</b></div>
      <div class="kv"><span>Transition</span><b id="inspTrans">&mdash;</b></div>
      <div class="kv"><span>Position</span><b id="inspPos">00:00:00:00</b></div>
      <div class="kv"><span>Timeline</span><b id="inspDur">00:00:22:00</b></div>
      <h3>Activity</h3>
      <div class="log" id="log"></div>
    </aside>
  </div>

  <div class="timeline">
    <div class="tl-toolbar">
      <span class="tl-title">TIMELINE</span>
      <div class="tl-legend"><i class="lc v"></i>Video<i class="lc t"></i>Text<i class="lc a"></i>Audio</div>
      <div class="spacer"></div>
      <span class="tl-hint">drag clips &amp; edges &middot; click ruler to seek</span>
    </div>
    <div class="tl-body">
      <div class="tl-headers">
        <div class="h-spacer"></div>
        <div class="h-track h-video">V1<span>VIDEO</span></div>
        <div class="h-track h-text">T1<span>TITLES</span></div>
        <div class="h-track h-audio">A1<span>AUDIO</span></div>
      </div>
      <div class="tl-scroll" id="tlScroll">
        <div class="tl-content" id="tlContent">
          <div class="ruler" id="ruler"></div>
          <div class="track track-video" id="trackVideo"></div>
          <div class="track track-text" id="trackText"></div>
          <div class="track track-audio" id="trackAudio"></div>
          <div class="shade" id="shadeL"></div>
          <div class="shade" id="shadeR"></div>
          <div class="marker in" id="inMarker"><span>IN</span></div>
          <div class="marker out" id="outMarker"><span>OUT</span></div>
          <div class="playhead" id="playhead"></div>
        </div>
      </div>
    </div>
  </div>

  <div class="ghost" id="ghost"></div>
</div>

<script>
(function(){
'use strict';

/* =========================================================
   Utilities
   ========================================================= */
const TAU = Math.PI * 2;
const clamp = (v,a,b) => v < a ? a : (v > b ? b : v);
const easeInOut = t => t < 0.5 ? 2*t*t : 1 - Math.pow(-2*t+2,2)/2;
const pad2 = n => (n<10?'0':'') + n;

const DUR = 22;            // timeline length in seconds
const BASE_PPS = 50;       // pixels per second at zoom = 1
const FPS = 30;

function fmt(t){
  t = Math.max(0, t);
  const total = Math.floor(t * FPS);
  const f = total % FPS;
  const s = Math.floor(total / FPS) % 60;
  const m = Math.floor(total / (FPS*60)) % 60;
  const h = Math.floor(total / (FPS*3600));
  return pad2(h)+':'+pad2(m)+':'+pad2(s)+':'+pad2(f);
}

/* =========================================================
   Procedural audio waveform data
   ========================================================= */
const AUDIO_N = 2400;
const audioData = (function(){
  const a = new Float32Array(AUDIO_N);
  for (let i=0;i<AUDIO_N;i++){
    const t = i / AUDIO_N * DUR;
    let v = 0.34*Math.abs(Math.sin(t*3.1))
          + 0.26*Math.abs(Math.sin(t*7.7 + 1.3))
          + 0.20*Math.abs(Math.sin(t*1.27 + 2.4))
          + 0.14*Math.abs(Math.sin(t*17.3 + 0.7));
    v *= 0.55 + 0.45*Math.sin(t*0.72 + 0.5);
    a[i] = clamp(v*1.15, 0, 1);
  }
  return a;
})();

function audioLevel(t){
  const i = clamp(Math.floor(t / DUR * AUDIO_N), 0, AUDIO_N-1);
  return audioData[i];
}

/* =========================================================
   Procedural scenes  (ctx, W, H, localTime, clip)
   ========================================================= */
const SCENES = {

  grid(ctx, W, H, t){
    const g = ctx.createLinearGradient(0,0,0,H);
    g.addColorStop(0,'#05060f');
    g.addColorStop(0.5,'#0b0f2c');
    g.addColorStop(1,'#1a0722');
    ctx.fillStyle = g; ctx.fillRect(0,0,W,H);

    const hz = H*0.58;

    // stars
    for (let i=0;i<70;i++){
      const x = (i*137.53) % W;
      const y = (i*79.31) % (hz-8);
      const tw = 0.35 + 0.65*Math.abs(Math.sin(t*2.1 + i*0.7));
      ctx.fillStyle = 'rgba(200,230,255,'+(0.10 + 0.42*tw)+')';
      ctx.fillRect(x, y, 1.7, 1.7);
    }

    // sun
    const sy = hz - 48 + Math.sin(t*0.9)*8;
    const rg = ctx.createRadialGradient(W/2, sy, 4, W/2, sy, H*0.46);
    rg.addColorStop(0,'rgba(255,160,225,0.95)');
    rg.addColorStop(0.35,'rgba(255,60,150,0.32)');
    rg.addColorStop(1,'rgba(255,0,110,0)');
    ctx.fillStyle = rg;
    ctx.beginPath(); ctx.arc(W/2, sy, H*0.46, 0, TAU); ctx.fill();

    ctx.fillStyle = 'rgba(255,220,242,0.95)';
    ctx.beginPath(); ctx.arc(W/2, sy, H*0.072, 0, TAU); ctx.fill();

    // horizon lines (perspective scroll)
    ctx.lineWidth = Math.max(1, H/540*1.5);
    for (let i=0;i<16;i++){
      const p = ((i/16) + (t*0.22)) % 1;
      const y = hz + Math.pow(p,2.2) * (H-hz) * 1.7;
      if (y > H+2) continue;
      ctx.strokeStyle = 'rgba(0,230,255,'+(0.14 + 0.6*p)+')';
      ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(W,y); ctx.stroke();
    }
    // vertical perspective lines
    for (let i=-12;i<=12;i++){
      ctx.strokeStyle = 'rgba(0,200,255,0.26)';
      ctx.beginPath();
      ctx.moveTo(W/2 + i*(W/16), hz);
      ctx.lineTo(W/2 + i*(W/1.05), H+40);
      ctx.stroke();
    }
    // horizon glow
    const hg = ctx.createLinearGradient(0, hz-16, 0, hz+16);
    hg.addColorStop(0,'rgba(0,255,255,0)');
    hg.addColorStop(0.5,'rgba(130,255,255,0.5)');
    hg.addColorStop(1,'rgba(0,255,255,0)');
    ctx.fillStyle = hg; ctx.fillRect(0, hz-16, W, 32);
  },

  orbit(ctx, W, H, t){
    const g = ctx.createRadialGradient(W/2,H/2,10,W/2,H/2,H*0.95);
    g.addColorStop(0,'#12193a');
    g.addColorStop(1,'#03040a');
    ctx.fillStyle = g; ctx.fillRect(0,0,W,H);

    const cx = W/2, cy = H/2;

    // core glow
    const core = ctx.createRadialGradient(cx,cy,2,cx,cy,H*0.24);
    core.addColorStop(0,'rgba(255,225,170,1)');
    core.addColorStop(0.4,'rgba(255,140,60,0.45)');
    core.addColorStop(1,'rgba(255,80,0,0)');
    ctx.fillStyle = core;
    ctx.beginPath(); ctx.arc(cx,cy,H*0.24,0,TAU); ctx.fill();

    // orbit paths
    for (let r=0;r<4;r++){
      const rr = H*(0.13 + r*0.085);
      ctx.strokeStyle = 'rgba(120,180,255,'+(0.13 - r*0.022)+')';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.ellipse(cx, cy, rr*1.4, rr*0.6, 0, 0, TAU);
      ctx.stroke();
    }

    // particles
    for (let i=0;i<54;i++){
      const ring = i % 4;
      const a = i*0.62 + t*(0.5 + ring*0.24);
      const rr = H*(0.13 + ring*0.085);
      const x = cx + Math.cos(a)*rr*1.4;
      const y = cy + Math.sin(a)*rr*0.6;
      const s = Math.max(1.2, 3.6 - ring*0.55);
      const hue = 26 + (i%18)*3;
      ctx.fillStyle = 'hsla('+hue+',95%,60%,0.16)';
      ctx.beginPath(); ctx.arc(x,y,s*3.2,0,TAU); ctx.fill();
      ctx.fillStyle = 'hsla('+hue+',96%,'+(64-ring*4)+'%,0.95)';
      ctx.beginPath(); ctx.arc(x,y,s,0,TAU); ctx.fill();
    }
  },

  bars(ctx, W, H, t){
    const g = ctx.createLinearGradient(0,0,0,H);
    g.addColorStop(0,'#04140f');
    g.addColorStop(1,'#061a2a');
    ctx.fillStyle = g; ctx.fillRect(0,0,W,H);

    const n = 40, bw = W/n, base = H*0.78;

    for (let i=0;i<n;i++){
      const v = Math.abs(Math.sin(t*3.2 + i*0.5) * Math.sin(t*1.1 + i*0.13));
      const h = H*0.07 + v*H*0.62;
      const x = i*bw + bw*0.16, w = bw*0.68;

      const grd = ctx.createLinearGradient(0, base-h, 0, base);
      grd.addColorStop(0,'hsla('+(155+i*3)+',92%,66%,0.95)');
      grd.addColorStop(1,'hsla('+(190+i*3)+',92%,44%,0.92)');
      ctx.fillStyle = grd;
      ctx.fillRect(x, base-h, w, h);

      ctx.globalAlpha = 0.16;
      ctx.fillRect(x, base, w, h*0.5);
      ctx.globalAlpha = 1;
    }

    ctx.fillStyle = 'rgba(0,255,200,0.35)';
    ctx.fillRect(0, base-1, W, 2);

    // soft top glow
    const tg = ctx.createLinearGradient(0,0,0,H*0.35);
    tg.addColorStop(0,'rgba(0,255,190,0.10)');
    tg.addColorStop(1,'rgba(0,255,190,0)');
    ctx.fillStyle = tg; ctx.fillRect(0,0,W,H*0.35);
  },

  rings(ctx, W, H, t){
    const g = ctx.createRadialGradient(W/2,H/2,20,W/2,H/2,H*1.05);
    g.addColorStop(0,'#1d1138');
    g.addColorStop(1,'#05030c');
    ctx.fillStyle = g; ctx.fillRect(0,0,W,H);

    ctx.save();
    ctx.translate(W/2, H/2);
    ctx.rotate(t*0.24);
    ctx.lineCap = 'round';
    for (let i=0;i<9;i++){
      const r = H*(0.075 + i*0.055) + Math.sin(t*1.4 + i*0.6)*7;
      const a0 = i*0.7 + t*0.65;
      ctx.beginPath();
      ctx.arc(0, 0, r, a0, a0 + 1.55 + (i%3)*0.6);
      ctx.strokeStyle = 'hsla('+(266+i*11)+',88%,'+(58 + (i%3)*7)+'%,0.88)';
      ctx.lineWidth = 2 + (i%4);
      ctx.stroke();
    }
    ctx.restore();

    // center pulse
    const pr = 6 + Math.sin(t*4)*2;
    const pg = ctx.createRadialGradient(W/2,H/2,1,W/2,H/2,pr*5);
    pg.addColorStop(0,'rgba(250,230,255,0.95)');
    pg.addColorStop(1,'rgba(200,120,255,0)');
    ctx.fillStyle = pg;
    ctx.beginPath(); ctx.arc(W/2,H/2,pr*5,0,TAU); ctx.fill();
    ctx.fillStyle = '#f6ecff';
    ctx.beginPath(); ctx.arc(W/2,H/2,pr*0.7,0,TAU); ctx.fill();
  }
};

/* =========================================================
   Data model
   ========================================================= */
const state = {
  playhead: 0,
  playing: true,
  zoom: 1,
  inPoint: 0,
  outPoint: DUR
};

const videoClips = [
  { id:'v1', name:'Neon Grid', scene:'grid',  start:0.0,  dur:5.5, transIn:null,                        color:'#3b82f6' },
  { id:'v2', name:'Orbit',     scene:'orbit', start:5.5,  dur:5.0, transIn:{type:'crossfade',dur:0.7},  color:'#f59e0b' },
  { id:'v3', name:'Spectrum',  scene:'bars',  start:10.5, dur:5.0, transIn:{type:'wipe',dur:0.8},       color:'#10b981' },
  { id:'v4', name:'Rings',     scene:'rings', start:15.5, dur:5.0, transIn:{type:'crossfade',dur:0.7},  color:'#a855f7' }
];

const textClips = [
  { id:'t1', text:'NEON DREAMS',   start:1.0,  dur:3.2 },
  { id:'t2', text:'ORBIT / SHOT 02', start:6.3,  dur:3.0 },
  { id:'t3', text:'SPECTRUM BARS',  start:11.2, dur:2.8 },
  { id:'t4', text:'RINGS // FINAL', start:16.2, dur:3.4 }
];

const audioClip = { id:'a1', name:'Ambient Pad', start:0, dur:DUR };

const INITIAL = videoClips.map(c => ({ start:c.start, dur:c.dur }));

/* =========================================================
   DOM references
   ========================================================= */
const preview   = document.getElementById('preview');
const pctx      = preview.getContext('2d');
const tlScroll  = document.getElementById('tlScroll');
const tlContent = document.getElementById('tlContent');
const rulerEl   = document.getElementById('ruler');
const playheadEl= document.getElementById('playhead');
const trackVideo= document.getElementById('trackVideo');
const trackText = document.getElementById('trackText');
const trackAudio= document.getElementById('trackAudio');
const shadeL    = document.getElementById('shadeL');
const shadeR    = document.getElementById('shadeR');
const inMarker  = document.getElementById('inMarker');
const outMarker = document.getElementById('outMarker');
const tcEl      = document.getElementById('tc');
const inTcEl    = document.getElementById('inTc');
const outTcEl   = document.getElementById('outTc');
const logEl     = document.getElementById('log');
const ghost     = document.getElementById('ghost');
const badge     = document.getElementById('transBadge');
const hud       = document.getElementById('hud');
const inspClip  = document.getElementById('inspClip');
const inspTrans = document.getElementById('inspTrans');
const inspPos   = document.getElementById('inspPos');
const inspDur   = document.getElementById('inspDur');

let ppsPx = BASE_PPS;

/* =========================================================
   Build clip DOM
   ========================================================= */
function makeThumb(clip){
  const cv = document.createElement('canvas');
  cv.width = 168; cv.height = 78;
  const c = cv.getContext('2d');
  (SCENES[clip.scene] || SCENES.grid)(c, 168, 78, 1.4, clip);
  cv.className = 'thumb';
  return cv;
}

videoClips.forEach((clip) => {
  const el = document.createElement('div');
  el.className = 'clip video';
  el.appendChild(makeThumb(clip));
  const grad = document.createElement('div');
  grad.className = 'grad';
  el.appendChild(grad);
  const lab = document.createElement('div');
  lab.className = 'label';
  lab.textContent = clip.name;
  el.appendChild(lab);
  const hl = document.createElement('div'); hl.className = 'handle l';
  const hr = document.createElement('div'); hr.className = 'handle r';
  el.appendChild(hl); el.appendChild(hr);
  clip.el = el;
  trackVideo.appendChild(el);
  attachDrag(el, clip);
});

const transEls = videoClips.map(clip => {
  if (!clip.transIn) return null;
  const el = document.createElement('div');
  el.className = 'trans ' + clip.transIn.type;
  const s = document.createElement('span');
  s.textContent = clip.transIn.type === 'crossfade' ? 'crossfade' : 'wipe';
  el.appendChild(s);
  trackVideo.appendChild(el);
  return el;
});

textClips.forEach(clip => {
  const el = document.createElement('div');
  el.className = 'clip textclip';
  const lab = document.createElement('div');
  lab.className = 'label';
  lab.textContent = clip.text;
  el.appendChild(lab);
  clip.el = el;
  trackText.appendChild(el);
  attachDrag(el, clip);
});

const audioEl = document.createElement('div');
audioEl.className = 'clip audio';
const waveCv = document.createElement('canvas');
waveCv.className = 'wave';
audioEl.appendChild(waveCv);
const audioLab = document.createElement('div');
audioLab.className = 'label';
audioLab.textContent = audioClip.name;
audioEl.appendChild(audioLab);
audioClip.el = audioEl;
trackAudio.appendChild(audioEl);
attachDrag(audioEl, audioClip);

/* =========================================================
   Ruler
   ========================================================= */
let rulerZoom = -1;
function buildRulerIfNeeded(){
  if (rulerZoom === state.zoom) return;
  rulerZoom = state.zoom;
  rulerEl.innerHTML = '';
  const px = ppsPx;
  const majorStep = px >= 110 ? 1 : (px >= 55 ? 2 : 5);
  const total = Math.round(DUR * 2);
  for (let i=0;i<=total;i++){
    const t = i/2;
    const isMajor = i % 2 === 0 && Math.abs(t - Math.round(t/majorStep)*majorStep) < 1e-6;
    const tick = document.createElement('div');
    tick.className = 'tick' + (isMajor ? ' major' : '');
    tick.style.left = (t*px) + 'px';
    rulerEl.appendChild(tick);
    if (isMajor){
      const lb = document.createElement('div');
      lb.className = 'ticklabel';
      lb.style.left = (t*px + 5) + 'px';
      const m = Math.floor(t/60), s = Math.floor(t%60);
      lb.textContent = m + ':' + pad2(s);
      rulerEl.appendChild(lb);
    }
  }
}

/* =========================================================
   Layout
   ========================================================= */
function layout(){
  ppsPx = BASE_PPS * state.zoom;
  tlContent.style.width = (DUR * ppsPx) + 'px';

  videoClips.forEach((c, i) => {
    c.el.style.left  = (c.start * ppsPx) + 'px';
    c.el.style.width = Math.max(8, c.dur * ppsPx) + 'px';
    const te = transEls[i];
    if (te){
      const tStart = c.start - c.transIn.dur;
      if (tStart >= -0.001){
        te.style.display = 'flex';
        te.style.left = (tStart * ppsPx) + 'px';
        te.style.width = Math.max(10, c.transIn.dur * ppsPx) + 'px';
      } else {
        te.style.display = 'none';
      }
    }
  });

  textClips.forEach(c => {
    c.el.style.left  = (c.start * ppsPx) + 'px';
    c.el.style.width = Math.max(8, c.dur * ppsPx) + 'px';
  });

  audioClip.el.style.left  = (audioClip.start * ppsPx) + 'px';
  audioClip.el.style.width = Math.max(8, audioClip.dur * ppsPx) + 'px';

  shadeL.style.left  = '0px';
  shadeL.style.width = (state.inPoint * ppsPx) + 'px';
  shadeR.style.left  = (state.outPoint * ppsPx) + 'px';
  shadeR.style.width = Math.max(0, (DUR - state.outPoint) * ppsPx) + 'px';

  inMarker.style.left  = (state.inPoint * ppsPx) + 'px';
  outMarker.style.left = (state.outPoint * ppsPx) + 'px';

  buildRulerIfNeeded();
  drawWaveform();
  updatePlayhead();
  updateInOutLabels();
}

function drawWaveform(){
  const w = Math.max(12, Math.round(audioClip.dur * ppsPx));
  const h = 58;
  if (waveCv.width !== w){ waveCv.width = w; }
  waveCv.height = h;
  const c = waveCv.getContext('2d');
  c.clearRect(0,0,w,h);

  const mid = h/2;
  c.fillStyle = 'rgba(74,222,128,0.85)';
  for (let x=0; x<w; x+=2){
    const t = clamp(x / w * audioClip.dur + audioClip.start, 0, DUR);
    const amp = audioLevel(t) * mid * 0.92;
    c.fillRect(x, mid-amp, 1.4, amp*2);
  }
  c.fillStyle = 'rgba(200,255,220,0.22)';
  c.fillRect(0, mid-0.5, w, 1);
}

function updatePlayhead(){
  playheadEl.style.transform = 'translateX(' + (state.playhead * ppsPx) + 'px)';
}

function updateInOutLabels(){
  inTcEl.textContent  = fmt(state.inPoint);
  outTcEl.textContent = fmt(state.outPoint);
}

/* =========================================================
   Dragging / trimming
   ========================================================= */
function round25(v){ return Math.round(v*20)/20; }

function attachDrag(el, clip){
  el.addEventListener('pointerdown', (e) => {
    if (e.button !== 0) return;
    e.preventDefault();
    e.stopPropagation();
    const tgt = e.target;
    let mode = 'move';
    if (tgt.classList && tgt.classList.contains('handle')){
      mode = tgt.classList.contains('l') ? 'l' : 'r';
    }
    startDrag(e, clip, mode);
  });
}

function startDrag(e, clip, mode){
  const startX = e.clientX;
  const s0 = clip.start, d0 = clip.dur;
  const el = clip.el;
  el.classList.add('hot');

  function onMove(ev){
    const dx = (ev.clientX - startX) / ppsPx;
    if (mode === 'move'){
      clip.start = clamp(round25(s0 + dx), 0, DUR - clip.dur);
    } else if (mode === 'l'){
      const ns = clamp(round25(s0 + dx), 0, s0 + d0 - 0.3);
      clip.start = ns;
      clip.dur = round25(d0 + (s0 - ns));
    } else {
      clip.dur = clamp(round25(d0 + dx), 0.3, DUR - clip.start);
    }
    layout();
  }
  function onUp(){
    window.removeEventListener('pointermove', onMove);
    window.removeEventListener('pointerup', onUp);
    el.classList.remove('hot');
  }
  window.addEventListener('pointermove', onMove);
  window.addEventListener('pointerup', onUp);
}

/* click ruler to seek */
rulerEl.addEventListener('pointerdown', (e) => {
  const rect = rulerEl.getBoundingClientRect();
  const t = clamp((e.clientX - rect.left) / ppsPx, 0, DUR);
  state.playhead = t;
  updatePlayhead();
});

/* =========================================================
   Transition / layer computation
   ========================================================= */
function computeLayers(t){
  const covering = videoClips
    .filter(c => t >= c.start && t < c.start + c.dur)
    .sort((a,b) => a.start - b.start);
  const cur = covering.length ? covering[covering.length-1] : null;

  let next = null, p = 0;

  if (cur){
    const cand = videoClips
      .filter(c => c.transIn && c.start > cur.start)
      .sort((a,b) => a.start - b.start)[0];
    if (cand){
      const d = cand.transIn.dur;
      if (t >= cand.start - d){
        next = cand;
        p = clamp((t - (cand.start - d)) / d, 0, 1);
      }
    }
  } else {
    const cand = videoClips
      .filter(c => c.transIn && t >= c.start - c.transIn.dur && t < c.start)
      .sort((a,b) => a.start - b.start)[0];
    if (cand){
      next = cand;
      p = clamp((t - (cand.start - cand.transIn.dur)) / cand.transIn.dur, 0, 1);
    }
  }
  return { cur, next, p };
}

/* =========================================================
   Preview rendering
   ========================================================= */
function drawScene(ctx, W, H, t, clip){
  ctx.save();
  const fn = SCENES[clip.scene] || SCENES.grid;
  fn(ctx, W, H, t - clip.start, clip);
  ctx.restore();
  ctx.globalAlpha = 1;
}

function drawTitle(ctx, W, H, text, alpha){
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';

  const fs = Math.round(H * 0.075);
  ctx.font = '700 ' + fs + 'px system-ui, -apple-system, Segoe UI, Roboto, sans-serif';
  const w = ctx.measureText(text).width;
  const y = H * 0.80;

  const bx = W/2 - w/2 - 30, bw = w + 60, bh = fs * 1.9, by = y - bh/2;
  const g = ctx.createLinearGradient(bx, 0, bx + bw, 0);
  g.addColorStop(0,'rgba(56,189,248,0)');
  g.addColorStop(0.5,'rgba(56,189,248,0.22)');
  g.addColorStop(1,'rgba(56,189,248,0)');
  ctx.fillStyle = g;
  ctx.fillRect(bx, by, bw, bh);

  ctx.fillStyle = 'rgba(56,189,248,0.85)';
  ctx.fillRect(bx + 8, by, 3, bh);
  ctx.fillRect(bx + bw - 11, by, 3, bh);

  ctx.shadowColor = 'rgba(120,220,255,0.9)';
  ctx.shadowBlur = 20;
  ctx.fillStyle = '#eaf6ff';
  ctx.fillText(text, W/2, y);
  ctx.restore();
}

function drawMeter(ctx, W, H, t){
  const v = audioLevel(t);
  const x0 = 22, y0 = H - 44;
  ctx.save();
  ctx.fillStyle = 'rgba(4,8,14,0.55)';
  ctx.fillRect(x0-6, y0-8, 168, 24);
  for (let i=0;i<24;i++){
    const on = (i/24) < v;
    let col = 'rgba(255,255,255,0.07)';
    if (on) col = i > 19 ? '#f87171' : (i > 15 ? '#fbbf24' : '#4ade80');
    ctx.fillStyle = col;
    ctx.fillRect(x0 + i*6.6, y0-2, 4.6, 12);
  }
  ctx.fillStyle = 'rgba(160,180,200,0.6)';
  ctx.font = '9px ui-monospace, Menlo, monospace';
  ctx.fillText('A1', x0-2, y0+20);
  ctx.restore();
}

function drawFrame(t){
  const W = preview.width, H = preview.height;
  const ctx = pctx;

  ctx.setTransform(1,0,0,1,0,0);
  ctx.globalAlpha = 1;
  ctx.fillStyle = '#04060a';
  ctx.fillRect(0,0,W,H);

  const L = computeLayers(t);

  if (L.cur){
    drawScene(ctx, W, H, t, L.cur);

    if (L.next){
      const type = L.next.transIn.type;
      if (type === 'crossfade'){
        ctx.globalAlpha = L.p;
        drawScene(ctx, W, H, t, L.next);
        ctx.globalAlpha = 1;
      } else {
        const w = W * L.p;
        ctx.save();
        ctx.beginPath();
        ctx.rect(0, 0, w, H);
        ctx.clip();
        drawScene(ctx, W, H, t, L.next);
        ctx.restore();

        const eg = ctx.createLinearGradient(w-30, 0, w+2, 0);
        eg.addColorStop(0,'rgba(120,220,255,0)');
        eg.addColorStop(1,'rgba(180,245,255,0.9)');
        ctx.fillStyle = eg;
        ctx.fillRect(w-30, 0, 32, H);
      }
    }
  } else if (L.next){
    // gap -> fade in from black
    ctx.globalAlpha = L.p;
    drawScene(ctx, W, H, t, L.next);
    ctx.globalAlpha = 1;
  }

  // text titles
  for (let i=0;i<textClips.length;i++){
    const tc = textClips[i];
    if (t >= tc.start && t < tc.start + tc.dur){
      const lt = t - tc.start;
      const fade = 0.45;
      const a = clamp(Math.min(lt/fade, (tc.dur - lt)/fade), 0, 1);
      drawTitle(ctx, W, H, tc.text, a);
    }
  }

  drawMeter(ctx, W, H, t);

  // subtle vignette
  const vg = ctx.createRadialGradient(W/2,H/2,H*0.35,W/2,H/2,H*0.95);
  vg.addColorStop(0,'rgba(0,0,0,0)');
  vg.addColorStop(1,'rgba(0,0,0,0.45)');
  ctx.fillStyle = vg;
  ctx.fillRect(0,0,W,H);
}

/* =========================================================
   HUD / inspector
   ========================================================= */
function updateHud(){
  const t = state.playhead;
  const covering = videoClips
    .filter(c => t >= c.start && t < c.start + c.dur)
    .sort((a,b) => a.start - b.start);
  const cur = covering.length ? covering[covering.length-1] : null;

  hud.textContent = cur ? ('V1 \u00B7 ' + cur.name.toUpperCase()) : 'V1 \u00B7 \u2014';
  inspClip.textContent = cur ? cur.name : '\u2014';

  const L = computeLayers(t);
  if (L.next){
    badge.style.opacity = 1;
    badge.textContent = (L.next.transIn.type === 'crossfade' ? '\u2715 CROSSFADE ' : '\u25A4 WIPE ')
      + Math.round(L.p*100) + '%';
    inspTrans.textContent = L.next.transIn.type.toUpperCase() + ' ' + Math.round(L.p*100) + '%';
  } else {
    badge.style.opacity = 0;
    inspTrans.textContent = '\u2014';
  }

  tcEl.textContent = fmt(t);
  inspPos.textContent = fmt(t);
  inspDur.textContent = fmt(DUR);
}

/* =========================================================
   Auto-scroll
   ========================================================= */
function autoScroll(){
  const px = state.playhead * ppsPx;
  const viewL = tlScroll.scrollLeft;
  const viewR = viewL + tlScroll.clientWidth;
  if (px > viewR - 130){
    tlScroll.scrollLeft = px - tlScroll.clientWidth + 190;
  } else if (px < viewL + 60){
    tlScroll.scrollLeft = Math.max(0, px - 110);
  }
}

/* =========================================================
   Toast log
   ========================================================= */
function toast(msg){
  const d = document.createElement('div');
  d.textContent = msg;
  logEl.appendChild(d);
  while (logEl.children.length > 6) logEl.removeChild(logEl.firstChild);
}

/* =========================================================
   Tweens
   ========================================================= */
const tweens = [];
function tween(from, to, dur, update, done){
  tweens.push({ t:0, dur, from, to, update, done });
}

let grabClip = null, grabMode = 'right';

function updateGhost(){
  if (!grabClip || !grabClip.el){
    ghost.style.opacity = 0;
    return;
  }
  const r = grabClip.el.getBoundingClientRect();
  const x = grabMode === 'right' ? r.right : (r.left + r.width/2);
  const y = r.top + r.height/2;
  ghost.style.opacity = 1;
  ghost.style.transform = 'translate(' + x + 'px,' + y + 'px)';
}

/* =========================================================
   Demo script
   ========================================================= */
const demo = {
  clock: 0,
  events: [
    { at:0.4, f(){
        toast('\u25B6 Auto-demo running \u2014 no interaction needed');
      }},
    { at:2.2, f(){
        toast('Marking IN point at 00:00:01:00');
        tween(state.inPoint, 1.0, 1.2, v => { state.inPoint = v; layout(); });
      }},
    { at:5.4, f(){
        toast('Trimming clip \u201CSpectrum\u201D \u2014 dragging out point');
        const c = videoClips[2];
        c.el.classList.add('hot');
        grabClip = c; grabMode = 'right';
        tween(c.dur, 3.6, 2.0,
          v => { c.dur = v; layout(); },
          () => { grabClip = null; c.el.classList.remove('hot'); }
        );
      }},
    { at:9.8, f(){
        toast('Moving clip \u201CRings\u201D to close the gap');
        const c = videoClips[3];
        c.el.classList.add('hot');
        grabClip = c; grabMode = 'center';
        tween(c.start, 14.1, 2.0,
          v => { c.start = v; layout(); },
          () => { grabClip = null; c.el.classList.remove('hot'); }
        );
      }},
    { at:14.3, f(){
        toast('Transitions active: crossfade + directional wipe');
      }},
    { at:17.8, f(){
        toast('Titles fade in/out on the text track');
      }},
    { at:21.6, f(){
        toast('Marking OUT point at 00:00:19:00');
        tween(state.outPoint, 19.0, 1.2, v => { state.outPoint = v; layout(); });
      }},
    { at:26.0, f(){
        toast('Looping demo\u2026');
      }}
  ]
};

function resetDemo(){
  demo.clock = 0;
  demo.events.forEach(e => e.done = false);
  tweens.length = 0;
  grabClip = null;
  videoClips.forEach((c,i) => {
    c.start = INITIAL[i].start;
    c.dur   = INITIAL[i].dur;
    c.el.classList.remove('hot');
  });
  state.inPoint = 0;
  state.outPoint = DUR;
  state.playhead = 0;
  logEl.innerHTML = '';
  layout();
}

function updateDemo(dt){
  demo.clock += dt;

  for (let i=0;i<demo.events.length;i++){
    const ev = demo.events[i];
    if (!ev.done && demo.clock >= ev.at){
      ev.done = true;
      ev.f();
    }
  }

  if (demo.clock > 28.5) resetDemo();

  for (let i=tweens.length-1;i>=0;i--){
    const tw = tweens[i];
    tw.t += dt;
    const p = clamp(tw.t / tw.dur, 0, 1);
    tw.update(tw.from + (tw.to - tw.from) * easeInOut(p));
    if (p >= 1){
      tweens.splice(i,1);
      if (tw.done) tw.done();
    }
  }
}

/* =========================================================
   Main loop
   ========================================================= */
let last = performance.now();

function frame(now){
  let dt = (now - last) / 1000;
  last = now;
  if (dt > 0.05) dt = 0.05;
  if (dt < 0) dt = 0;

  if (state.playing){
    state.playhead += dt;
    if (state.playhead >= DUR) state.playhead -= DUR;
  }

  updateDemo(dt);
  drawFrame(state.playhead);
  updatePlayhead();
  autoScroll();
  updateHud();
  updateGhost();

  requestAnimationFrame(frame);
}

/* =========================================================
   Controls
   ========================================================= */
const btnPlay = document.getElementById('btnPlay');
btnPlay.addEventListener('click', () => {
  state.playing = !state.playing;
  btnPlay.innerHTML = state.playing ? '&#10074;&#10074;' : '&#9654;';
});
document.getElementById('btnStart').addEventListener('click', () => {
  state.playhead = 0; updatePlayhead(); updateHud();
});
document.getElementById('btnEnd').addEventListener('click', () => {
  state.playhead = DUR - 0.05; updatePlayhead(); updateHud();
});

document.getElementById('zoom').addEventListener('input', (e) => {
  state.zoom = parseFloat(e.target.value);
  layout();
});

document.querySelectorAll('.tbtn').forEach(b => {
  b.addEventListener('click', () => {
    document.querySelectorAll('.tbtn').forEach(x => x.classList.remove('active'));
    b.classList.add('active');
  });
});

/* =========================================================
   Boot
   ========================================================= */
layout();
toast('NovaCut ready \u2014 demo starting');
requestAnimationFrame(frame);

})();
</script>
</body>
</html>
```
### Auto-Demo & Editor Mechanics

This page behaves like a tiny editing suite that runs itself, so you can just watch the timeline come alive.

- **Procedural scenes & transitions** – Four canvas clips (grid, orbit, bars, rings) animate entirely in code. Crossfade and wipe blend the outgoing and incoming scenes using an alpha ramp and a clipped wipe edge.
- **Text & audio tracks** – Titles fade in and out over the video, while a generated waveform is drawn inside the audio clip and a small level meter reacts in the preview.
- **Timeline interaction** – Video, text, and audio clips can be dragged horizontally; video clips also have edge handles for trimming. Clicking the ruler seeks the playhead, and the zoom slider changes the pixels-per-second scale.
- **Automated demo script** – Within the first 28 seconds, the playhead moves, the in/out points update, the “Spectrum” clip is trimmed, the “Rings” clip is moved, and a ghost cursor highlights the active edit. The HUD and activity log reflect each event.
---

**Optimization Tip:** The demo scripting values are hard-coded in the `demo.events` array and in `videoClips`/`textClips` definitions. You can edit the `at` timestamps, clip start/duration, and transition parameters to customize the auto-demo or timeline content.