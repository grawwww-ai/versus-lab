Here's a self-contained particle system editor. I went for an "instrument bench" aesthetic — warm near-black chrome, mono type, a draggable emitter reticle, additive-blended spark sprites with real motion trails, and a UI whose accent color re-tints itself to whatever particle color you pick:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Particle Bench · Canvas Emitter</title>
<style>
:root{
  --bg:#0d0c0a;
  --panel:#12100c;
  --line:rgba(236,227,208,.08);
  --line2:rgba(236,227,208,.17);
  --txt:#e9e2d4;
  --dim:#8a8272;
  --faint:#5b5443;
  --acc:hsl(35,80%,64%);
  --acc-soft:hsla(35,80%,64%,.45);
  --acc-faint:hsla(35,80%,64%,.13);
  --warn:#e0524f;
  --mono:"SF Mono","Cascadia Code","JetBrains Mono",Menlo,Consolas,"DejaVu Sans Mono","Liberation Mono",monospace;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{
  background:var(--bg);color:var(--txt);
  font-family:var(--mono);font-size:12px;
  display:grid;grid-template-rows:54px 1fr;
  overflow:hidden;-webkit-tap-highlight-color:transparent;
  -webkit-font-smoothing:antialiased;
}
button,input{font-family:inherit}

/* ---------- header ---------- */
header{
  display:flex;align-items:center;justify-content:space-between;
  padding:0 20px;border-bottom:1px solid var(--line);background:var(--panel);
  user-select:none;gap:12px;flex-wrap:wrap;
}
.brand{display:flex;align-items:center;gap:10px}
.pip{width:7px;height:7px;background:var(--acc);flex:none}
.name{font-size:12px;font-weight:700;letter-spacing:.24em}
.sub{font-size:10px;color:var(--faint);letter-spacing:.08em}
.stats{display:flex;align-items:center;gap:18px}
.vdiv{width:1px;height:26px;background:var(--line2)}
.stat{display:flex;flex-direction:column;align-items:flex-end;gap:3px}
.slab{font-size:9px;letter-spacing:.22em;color:var(--dim)}
.srow{display:flex;align-items:center;gap:9px}
.sval{font-size:21px;line-height:1;font-variant-numeric:tabular-nums;min-width:2ch;text-align:right}
#fpsVal{color:var(--acc)}
#fpsVal.low{color:var(--warn)}
#spark{width:64px;height:20px}

/* ---------- layout ---------- */
main{display:grid;grid-template-columns:266px 1fr;min-height:0}
#rail{
  border-right:1px solid var(--line);background:var(--panel);
  padding:20px 18px 14px;display:flex;flex-direction:column;gap:24px;
  overflow-y:auto;user-select:none;scrollbar-width:thin;scrollbar-color:#2a251c transparent;
}
#rail::-webkit-scrollbar{width:4px}
#rail::-webkit-scrollbar-thumb{background:#2a251c}
.grp{display:flex;flex-direction:column;gap:14px;flex:none}
.grp h2{
  font-size:9px;font-weight:600;letter-spacing:.26em;color:var(--dim);
  display:flex;align-items:center;gap:8px;
}
.grp h2::before{content:"";width:14px;height:1px;background:var(--acc-soft)}

/* ---------- sliders ---------- */
.ctl{display:flex;flex-direction:column;gap:5px}
.crow{display:flex;justify-content:space-between;align-items:baseline}
.lab{font-size:10px;letter-spacing:.16em;color:var(--dim)}
.val{font-size:12px;font-variant-numeric:tabular-nums}
.val b{font-weight:600;color:var(--acc)}
.val i{font-style:normal;color:var(--faint);font-size:10px;margin-left:3px}

input[type=range]{
  -webkit-appearance:none;appearance:none;
  width:100%;height:22px;background:transparent;cursor:ew-resize;--p:50%;
}
input[type=range]:focus{outline:none}
input[type=range]:focus-visible{outline:1px dashed var(--acc-soft);outline-offset:3px}
input[type=range]::-webkit-slider-runnable-track{
  height:2px;border-radius:1px;
  background:linear-gradient(90deg,var(--acc) var(--p),var(--line2) var(--p));
}
input[type=range]::-webkit-slider-thumb{
  -webkit-appearance:none;appearance:none;
  width:5px;height:16px;border-radius:1px;border:none;
  background:var(--acc);margin-top:-7px;transition:width .12s ease;
}
input[type=range]:hover::-webkit-slider-thumb,
input[type=range]:active::-webkit-slider-thumb{width:9px}
input[type=range]::-moz-range-track{height:2px;background:var(--line2);border-radius:1px}
input[type=range]::-moz-range-progress{height:2px;background:var(--acc);border-radius:1px}
input[type=range]::-moz-range-thumb{width:5px;height:16px;border:none;border-radius:1px;background:var(--acc);transition:width .12s ease}
input[type=range]:hover::-moz-range-thumb{width:9px}

/* ---------- color ---------- */
.colorrow{display:flex;align-items:center;gap:12px}
.swatch-wrap{position:relative;width:34px;height:34px;cursor:pointer;flex:none;display:block}
.swatch-wrap input{position:absolute;inset:0;opacity:0;cursor:pointer}
.swatch{
  position:absolute;inset:0;border-radius:3px;border:1px solid var(--line2);
  background:#ffb454;pointer-events:none;
}
.swatch::after{content:"";position:absolute;inset:3px;border-radius:2px;border:1px solid rgba(0,0,0,.3)}
.swatch-wrap:has(input:focus-visible) .swatch{outline:1px dashed var(--acc-soft);outline-offset:3px}
.hex{font-size:12px;letter-spacing:.08em}
.presets{display:flex;gap:9px}
.preset{
  width:15px;height:15px;border-radius:50%;border:1px solid rgba(0,0,0,.45);
  background:var(--c);cursor:pointer;position:relative;padding:0;flex:none;
  transition:transform .12s ease;
}
.preset:hover{transform:scale(1.3)}
.preset.on::after{content:"";position:absolute;inset:-4px;border-radius:50%;border:1px solid var(--acc-soft)}

/* ---------- gravity switch ---------- */
.forcerow{
  display:flex;align-items:center;gap:12px;width:100%;
  background:none;border:none;color:inherit;cursor:pointer;
  padding:3px 0;text-align:left;
}
.forcerow .lab{flex:1}
.state{font-size:10px;letter-spacing:.16em;color:var(--faint);min-width:3ch;text-align:right}
.switch{
  width:38px;height:20px;flex:none;border-radius:11px;position:relative;
  border:1px solid var(--line2);background:rgba(236,227,208,.04);
  transition:background .18s ease,border-color .18s ease;
}
.knob{
  position:absolute;top:3px;left:3px;width:12px;height:12px;border-radius:50%;
  background:var(--dim);transition:transform .18s ease,background .18s ease;
}
.forcerow:hover .switch{border-color:rgba(236,227,208,.3)}
.forcerow[aria-checked="true"] .switch{background:var(--acc-faint);border-color:var(--acc-soft)}
.forcerow[aria-checked="true"] .knob{transform:translateX(18px);background:var(--acc)}
.forcerow[aria-checked="true"] .state{color:var(--acc)}
.forcerow:focus-visible{outline:1px dashed var(--acc-soft);outline-offset:3px}
.meta{font-size:10px;color:var(--faint);letter-spacing:.08em}
.meta.off{opacity:.6}

/* ---------- hints ---------- */
.railfoot{
  margin-top:auto;padding-top:16px;border-top:1px solid var(--line);
  display:flex;flex-direction:column;gap:8px;flex:none;
}
.railfoot span{font-size:9px;letter-spacing:.14em;color:var(--faint)}
.railfoot b{font-weight:400;color:var(--dim);margin-right:9px}

/* ---------- stage ---------- */
#stage{position:relative;min-width:0;min-height:0;overflow:hidden}
#view{position:absolute;inset:0;width:100%;height:100%;display:block;cursor:crosshair;touch-action:none}
.corner{position:absolute;width:12px;height:12px;pointer-events:none;z-index:2}
.corner.tl{top:10px;left:10px;border-top:1px solid var(--line2);border-left:1px solid var(--line2)}
.corner.tr{top:10px;right:10px;border-top:1px solid var(--line2);border-right:1px solid var(--line2)}
.corner.bl{bottom:10px;left:10px;border-bottom:1px solid var(--line2);border-left:1px solid var(--line2)}
.corner.br{bottom:10px;right:10px;border-bottom:1px solid var(--line2);border-right:1px solid var(--line2)}
.srcinfo{
  position:absolute;left:30px;bottom:18px;pointer-events:none;z-index:2;
  font-size:9px;letter-spacing:.18em;color:var(--faint);font-variant-numeric:tabular-nums;
}

@media (max-width:760px){
  main{grid-template-columns:1fr;grid-template-rows:1fr auto}
  #rail{border-right:none;border-top:1px solid var(--line);flex-direction:row;flex-wrap:wrap;gap:18px;max-height:190px}
  .grp{flex:1;min-width:150px;gap:10px}
  .railfoot,.sub{display:none}
  .srcinfo{bottom:auto;top:30px}
}
</style>
</head>
<body>

<header>
  <div class="brand">
    <span class="pip"></span>
    <span class="name">PARTICLE BENCH</span>
    <span class="sub">/ canvas emitter console</span>
  </div>
  <div class="stats">
    <div class="stat">
      <span class="slab">FPS</span>
      <div class="srow">
        <span class="sval" id="fpsVal">—</span>
        <canvas id="spark" width="64" height="20" aria-label="Frame rate history"></canvas>
      </div>
    </div>
    <div class="vdiv"></div>
    <div class="stat">
      <span class="slab">PARTICLES</span>
      <div class="srow"><span class="sval" id="cntVal">0</span></div>
    </div>
  </div>
</header>

<main>
  <aside id="rail">
    <section class="grp">
      <h2>EMISSION</h2>
      <div class="ctl">
        <div class="crow">
          <label class="lab" for="rate">RATE</label>
          <span class="val"><b id="vRate">160</b><i>/s</i></span>
        </div>
        <input type="range" id="rate" min="10" max="600" step="5" value="160" aria-label="Emission rate">
      </div>
      <div class="ctl">
        <div class="crow">
          <label class="lab" for="speed">SPEED</label>
          <span class="val"><b id="vSpeed">260</b><i>px/s</i></span>
        </div>
        <input type="range" id="speed" min="20" max="500" step="5" value="260" aria-label="Particle speed">
      </div>
      <div class="ctl">
        <div class="crow">
          <label class="lab" for="life">LIFETIME</label>
          <span class="val"><b id="vLife">2.4</b><i>s</i></span>
        </div>
        <input type="range" id="life" min="0.4" max="6" step="0.1" value="2.4" aria-label="Particle lifetime">
      </div>
    </section>

    <section class="grp">
      <h2>COLOR</h2>
      <div class="colorrow">
        <label class="swatch-wrap" title="Pick particle color">
          <input type="color" id="colorPick" value="#ffb454" aria-label="Particle color">
          <span class="swatch" id="swatch"></span>
        </label>
        <span class="hex" id="hex">#FFB454</span>
      </div>
      <div class="presets" id="presets"></div>
    </section>

    <section class="grp">
      <h2>FORCES</h2>
      <button class="forcerow" id="gravBtn" role="switch" aria-checked="true">
        <span class="lab">GRAVITY</span>
        <span class="state" id="gravState">ON</span>
        <span class="switch"><span class="knob"></span></span>
      </button>
      <div class="meta" id="gravMeta">g = 520 px/s² · downward</div>
    </section>

    <footer class="railfoot">
      <span><b>01</b>DRAG THE SOURCE TO MOVE IT</span>
      <span><b>02</b>CLICK THE CANVAS FOR A BURST</span>
      <span><b>03</b>SPACE TOGGLES GRAVITY</span>
    </footer>
  </aside>

  <div id="stage">
    <canvas id="view"></canvas>
    <i class="corner tl" aria-hidden="true"></i>
    <i class="corner tr" aria-hidden="true"></i>
    <i class="corner bl" aria-hidden="true"></i>
    <i class="corner br" aria-hidden="true"></i>
    <div class="srcinfo" id="srcInfo">SRC — · —</div>
  </div>
</main>

<script>
(() => {
'use strict';

const $ = id => document.getElementById(id);
const canvas = $('view'), stage = $('stage'), spark = $('spark');
const ctx = canvas.getContext('2d');
const sctx = spark.getContext('2d');
const fpsVal = $('fpsVal'), cntVal = $('cntVal'), srcInfo = $('srcInfo');
const gravBtn = $('gravBtn'), gravState = $('gravState'), gravMeta = $('gravMeta');
const colorPick = $('colorPick'), swatch = $('swatch'), hexEl = $('hex');

const FONT = '"SF Mono","Cascadia Code","JetBrains Mono",Menlo,Consolas,monospace';
const BG_FADE = 'rgba(13,12,10,0.42)';
const TAU = Math.PI * 2;
const clamp = (v, a, b) => v < a ? a : (v > b ? b : v);

/* ---------------- live state ---------------- */
const S = { rate: 160, speed: 260, life: 2.4, gravity: true, g: 520, src: { x: 200, y: 200 } };
let accCss = 'hsl(35,80%,64%)';
let W = 0, H = 0, dpr = 1, srcInit = false;

/* ---------------- color helpers ---------------- */
const hexToRgb = h => { const n = parseInt(h.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; };
function rgbToHsl(r, g, b) {
  r /= 255; g /= 255; b /= 255;
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), l = (mx + mn) / 2;
  if (mx === mn) return { h: 36, s: 0, l: l * 100 };           // achromatic fallback hue
  const d = mx - mn, s = l > 0.5 ? d / (2 - mx - mn) : d / (mx + mn);
  let h;
  if (mx === r) h = (g - b) / d + (g < b ? 6 : 0);
  else if (mx === g) h = (b - r) / d + 2;
  else h = (r - g) / d + 4;
  return { h: h * 60, s: s * 100, l: l * 100 };
}

/* The whole chrome re-tints to match the particle color's hue. */
function setAccent(hex) {
  let { h, s } = rgbToHsl(...hexToRgb(hex));
  if (s < 8) h = 36;                       // near-gray picks keep a warm ember chrome
  s = Math.min(85, Math.max(40, s));
  const H0 = Math.round(h), S0 = Math.round(s);
  accCss = `hsl(${H0},${S0}%,64%)`;
  const rs = document.documentElement.style;
  rs.setProperty('--acc', accCss);
  rs.setProperty('--acc-soft', `hsla(${H0},${S0}%,64%,0.45)`);
  rs.setProperty('--acc-faint', `hsla(${H0},${S0}%,64%,0.13)`);
}

/* ---------------- particle sprite (cached, rebuilt only on color change) ---------------- */
const SPR = 48;
const sprite = document.createElement('canvas');
sprite.width = sprite.height = SPR;
function buildSprite(hex) {
  const c = sprite.getContext('2d');
  c.clearRect(0, 0, SPR, SPR);
  const { h, s, l } = rgbToHsl(...hexToRgb(hex));
  const g = c.createRadialGradient(SPR / 2, SPR / 2, 0, SPR / 2, SPR / 2, SPR / 2);
  g.addColorStop(0,    `hsla(${h},${s}%,${Math.min(97, l + (97 - l) * 0.8)}%,1)`);  // white-hot core
  g.addColorStop(0.22, `hsla(${h},${s}%,${l}%,0.9)`);
  g.addColorStop(1,    `hsla(${h},${s}%,${l}%,0)`);
  c.fillStyle = g;
  c.fillRect(0, 0, SPR, SPR);
}

/* ---------------- particles ---------------- */
const parts = [];
const MAX = 4500;

function spawn(x, y, burst) {
  if (parts.length >= MAX) return;
  const a = burst ? Math.random() * TAU
                  : -Math.PI / 2 + (Math.random() - 0.5) * 1.15;   // upward cone
  const mul = burst ? 0.45 + Math.random() * 0.85 : 0.55 + Math.random() * 0.6;
  const sp = S.speed * mul;
  parts.push({
    x, y,
    vx: Math.cos(a) * sp, vy: Math.sin(a) * sp,
    life: S.life * (burst ? 0.45 + Math.random() * 0.5 : 0.7 + Math.random() * 0.55),
    age: 0,
    size: (burst ? 6 : 7) + Math.random() * 7,
    ph: Math.random() * TAU
  });
}

/* ---------------- sizing ---------------- */
function resize() {
  dpr = Math.min(2, window.devicePixelRatio || 1);
  const r = stage.getBoundingClientRect();
  W = Math.max(1, Math.round(r.width));
  H = Math.max(1, Math.round(r.height));
  canvas.width = Math.round(W * dpr);
  canvas.height = Math.round(H * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  if (!srcInit) { S.src.x = W * 0.5; S.src.y = H * 0.6; srcInit = true; }
  S.src.x = clamp(S.src.x, 14, W - 14);
  S.src.y = clamp(S.src.y, 14, H - 14);
  spark.width = Math.round(64 * dpr);
  spark.height = Math.round(20 * dpr);
  sctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

/* ---------------- emitter reticle (draggable) ---------------- */
let dragging = false;
function drawReticle(t) {
  const x = S.src.x, y = S.src.y, r = dragging ? 11.5 : 8.5;
  ctx.strokeStyle = accCss;
  ctx.lineWidth = 1;
  ctx.globalAlpha = 0.95;
  ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.stroke();
  ctx.beginPath();
  for (let i = 0; i < 4; i++) {
    const a = i * Math.PI / 2, c = Math.cos(a), s2 = Math.sin(a);
    ctx.moveTo(x + c * (r + 2.5), y + s2 * (r + 2.5));
    ctx.lineTo(x + c * (r + 7.5), y + s2 * (r + 7.5));
  }
  ctx.stroke();
  ctx.globalAlpha = 0.55 + 0.45 * Math.sin(t * 7);   // flickers like a live feed
  ctx.fillStyle = accCss;
  ctx.beginPath(); ctx.arc(x, y, 1.8, 0, TAU); ctx.fill();
  ctx.globalAlpha = 1;
  ctx.font = '9px ' + FONT;
  ctx.fillStyle = 'rgba(233,226,212,0.45)';
  ctx.fillText('SOURCE', x + 17, y - 13);
}

/* ---------------- FPS sparkline ---------------- */
const fpsHist = new Float32Array(56);
let fpsIdx = 0, fpsEma = 60;
function drawSpark() {
  const w = 64, h = 20;
  sctx.clearRect(0, 0, w, h);
  sctx.strokeStyle = 'rgba(233,226,212,0.13)';      // 60 fps reference line
  sctx.lineWidth = 1;
  sctx.beginPath(); sctx.moveTo(0, h / 2 + 0.5); sctx.lineTo(w, h / 2 + 0.5); sctx.stroke();
  sctx.strokeStyle = accCss;
  sctx.beginPath();
  for (let i = 0; i < fpsHist.length; i++) {
    const v = fpsHist[(fpsIdx + i) % fpsHist.length];
    const x = (i / (fpsHist.length - 1)) * (w - 1) + 0.5;
    const y = h - 1.5 - clamp(v, 0, 120) / 120 * (h - 4);
    i ? sctx.lineTo(x, y) : sctx.moveTo(x, y);
  }
  sctx.stroke();
}

/* ---------------- main loop ---------------- */
let last = performance.now(), emitAcc = 0, uiT = 1;
function frame(now) {
  requestAnimationFrame(frame);
  let dt = (now - last) / 1000; last = now;
  if (dt <= 0) return;
  if (dt > 0.05) dt = 0.05;                        // clamp after tab switches

  const inst = 1 / dt;
  fpsEma += (inst - fpsEma) * 0.08;
  fpsHist[fpsIdx] = inst; fpsIdx = (fpsIdx + 1) % fpsHist.length;

  /* emission accumulator — fractional rates stay exact over time */
  emitAcc += S.rate * dt;
  let n = Math.floor(emitAcc);
  if (n > 60) { n = 60; emitAcc = 0; } else emitAcc -= n;
  for (let i = 0; i < n; i++) spawn(S.src.x, S.src.y, false);

  /* physics: semi-implicit Euler + light air drag + lateral shimmer */
  const g = S.gravity ? S.g : 0;
  const dr = Math.exp(-0.1 * dt);
  const t = now / 1000;
  for (let i = parts.length - 1; i >= 0; i--) {
    const p = parts[i];
    p.age += dt;
    if (p.age >= p.life) { parts[i] = parts[parts.length - 1]; parts.pop(); continue; }
    p.vx = p.vx * dr + Math.sin(t * 4.2 + p.ph) * 15 * dt;
    p.vy = p.vy * dr + g * dt;
    p.x += p.vx * dt; p.y += p.vy * dt;
    if (p.x < -90 || p.x > W + 90 || p.y > H + 90 || p.y < -170) {
      parts[i] = parts[parts.length - 1]; parts.pop();
    }
  }

  /* render: fade pass gives motion trails, additive pass gives glow */
  ctx.globalCompositeOperation = 'source-over';
  ctx.fillStyle = BG_FADE;
  ctx.fillRect(0, 0, W, H);
  ctx.globalCompositeOperation = 'lighter';
  for (let i = 0; i < parts.length; i++) {
    const p = parts[i], k = p.age / p.life;
    const a = Math.pow(1 - k, 1.6);                // fade out over lifetime
    if (a < 0.02) continue;
    const s = p.size * (1 - 0.35 * k);
    ctx.globalAlpha = a;
    ctx.drawImage(sprite, p.x - s / 2, p.y - s / 2, s, s);
  }
  ctx.globalAlpha = 1;
  drawReticle(t);
  drawSpark();

  /* throttled DOM readouts */
  uiT += dt;
  if (uiT > 0.25) {
    uiT = 0;
    fpsVal.textContent = String(Math.round(fpsEma));
    fpsVal.classList.toggle('low', fpsEma < 30);
    cntVal.textContent = parts.length.toLocaleString('en-US');
    srcInfo.textContent = 'SRC ' + Math.round(S.src.x) + ' · ' + Math.round(S.src.y);
  }
}

/* ---------------- canvas interaction ---------------- */
let overSrc = false;
const evPt = e => {
  const r = canvas.getBoundingClientRect();
  return { x: e.clientX - r.left, y: e.clientY - r.top };
};
canvas.addEventListener('pointerdown', e => {
  const p = evPt(e);
  if (Math.hypot(p.x - S.src.x, p.y - S.src.y) < 18) {
    dragging = true;
    canvas.setPointerCapture(e.pointerId);
    canvas.style.cursor = 'grabbing';
  } else {
    for (let i = 0; i < 42; i++) spawn(p.x, p.y, true);   // one-shot burst
  }
});
canvas.addEventListener('pointermove', e => {
  const p = evPt(e);
  if (dragging) {
    S.src.x = clamp(p.x, 14, W - 14);
    S.src.y = clamp(p.y, 14, H - 14);
  } else {
    const over = Math.hypot(p.x - S.src.x, p.y - S.src.y) < 18;
    if (over !== overSrc) {
      overSrc = over;
      canvas.style.cursor = over ? 'grab' : 'crosshair';
    }
  }
});
window.addEventListener('pointerup', () => {
  if (dragging) { dragging = false; canvas.style.cursor = overSrc ? 'grab' : 'crosshair'; }
});

/* ---------------- controls ---------------- */
function bindRange(id, key, out, fmt) {
  const el = $(id), val = $(out);
  const apply = () => {
    S[key] = parseFloat(el.value);
    val.textContent = fmt(S[key]);
    el.style.setProperty('--p', ((el.value - el.min) / (el.max - el.min) * 100) + '%');
  };
  el.addEventListener('input', apply);
  apply();
}
bindRange('rate',  'rate',  'vRate',  v => String(Math.round(v)));
bindRange('speed', 'speed', 'vSpeed', v => String(Math.round(v)));
bindRange('life',  'life',  'vLife',  v => v.toFixed(1));

function setGrav(on) {
  S.gravity = on;
  gravBtn.setAttribute('aria-checked', String(on));
  gravState.textContent = on ? 'ON' : 'OFF';
  gravMeta.textContent = on ? 'g = 520 px/s² · downward' : 'g = 0 · free float';
  gravMeta.classList.toggle('off', !on);
}
gravBtn.addEventListener('click', () => { setGrav(!S.gravity); gravBtn.blur(); });
window.addEventListener('keydown', e => {
  if (e.code !== 'Space' || e.repeat) return;
  const tag = e.target.tagName;
  if (tag === 'INPUT' || tag === 'BUTTON') return;
  e.preventDefault();
  setGrav(!S.gravity);
});

/* ---------------- color picker + presets ---------------- */
const PRESETS = ['#ffb454', '#ff5c38', '#ffe08a', '#8de0b8', '#7cc9ff', '#f2ede2'];
const presetWrap = $('presets');
PRESETS.forEach(c => {
  const b = document.createElement('button');
  b.type = 'button';
  b.className = 'preset';
  b.style.setProperty('--c', c);
  b.dataset.c = c;
  b.title = c.toUpperCase();
  b.setAttribute('aria-label', 'Use color ' + c);
  b.addEventListener('click', () => { colorPick.value = c; applyColor(c); });
  presetWrap.appendChild(b);
});
function applyColor(c) {
  swatch.style.background = c;
  hexEl.textContent = c.toUpperCase();
  buildSprite(c);          // rebuild the glow sprite in the new hue
  setAccent(c);            // re-tint the console chrome
  presetWrap.querySelectorAll('.preset').forEach(b =>
    b.classList.toggle('on', b.dataset.c === c.toLowerCase()));
}
colorPick.addEventListener('input', () => applyColor(colorPick.value));

/* ---------------- init ---------------- */
new ResizeObserver(resize).observe(stage);
window.addEventListener('resize', resize);
resize();
setGrav(true);
applyColor('#ffb454');
requestAnimationFrame(frame);
})();
</script>
</body>
</html>
```

**How it's built:**

- **Physics** — an accumulator emits `rate × dt` particles per frame (so fractional rates like 155/s stay exact), integrated with semi-implicit Euler, light exponential air drag, and a per-particle sinusoidal lateral shimmer so the plume feels alive. Particles die by lifetime, by leaving the stage, or at a 4 500 hard cap (swap-remove, no GC churn).
- **Rendering** — each color is baked once into a cached radial-gradient sprite (white-hot core → hue → transparent), then drawn per particle with `lighter` compositing and a `(1−t)^1.6` alpha fade plus slight shrink. A translucent background fill each frame instead of a hard clear produces real motion trails for free.
- **FPS** — an EMA of frame rate drives the big numeral (it turns warning-red under 30), a 56-sample sparkline with a 60 fps reference line, plus a live particle count and source coordinates, all DOM-throttled to 4 Hz.
- **The signature touch** — pick any particle color and the entire console chrome (slider fills, switch, ticks, sparkline, wordmark pip) re-derives its accent hue from your choice, so the instrument always matches the experiment.
- **Interactions** — three live sliders, a native color input behind a custom swatch with six quick presets, a gravity switch (also bound to Space), a draggable emitter reticle, and click-anywhere radial bursts. Everything auto-starts with the amber fountain already running.