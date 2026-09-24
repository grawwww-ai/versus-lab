Let me write a single HTML file with a canvas particle system editor.

Features:
- Canvas centered
- Sliders: emission rate, particle speed, lifetime
- Color picker
- Gravity toggle button
- Particles fade over time
- FPS counter
- All vanilla, no external.

Let me design a nice dark UI with a control panel.

Implementation details:
- Canvas sized to container, handle resize with devicePixelRatio.
- Particle pool array.
- Emitter at center of canvas (or bottom center? "source point" — center is fine; maybe center-ish).
- Emission accumulator: rate particles per second.
- Particle: x, y, vx, vy, life, maxLife, color.
- Gravity toggle: apply ay = 300 px/s² maybe.
- Fade: alpha = life/maxLife.
- Draw with additive blending maybe, using globalCompositeOperation 'lighter' for glow.

Emission: random direction over full circle, or upward spread? Let's do full 360 with slight random. Speed = slider value ± spread.

Add a reset/clear button? Not required but fine. Keep to requirements.

FPS counter: compute running average over frames.

Let me write code.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Particle System Editor</title>
<style>...</style>
</head>
<body>
<div class="app">
  <header>...</header>
  <main>
    <div class="canvas-wrap"><canvas id="cv"></canvas><div class="fps" id="fps">FPS: --</div></div>
    <aside class="panel">...</aside>
  </main>
</div>
```

Layout: flex row, canvas area flex:1, panel width 280px. Responsive: on narrow, column.

Canvas sizing: use ResizeObserver on wrapper, set canvas.width = w*dpr etc, ctx.setTransform(dpr,0,0,dpr,0,0).

Coordinates in CSS pixels.

Emitter at (w/2, h/2) maybe. Let's do bottom-center-ish? "central canvas displays particles emitting from a source point" — I'll put source at center. Actually with gravity, emitting from center looks nice.

Particle update with dt clamping.

Fade: alpha = life / maxLife, and also size shrink maybe.

Emission rate slider: 0–500 particles/sec.

Speed slider: 20–500 px/s.

Lifetime slider: 0.2–5 s.

Color picker: use <input type="color">.

Gravity button toggles class active.

Also a "burst"? no.

Let's implement particle spawning: accumulate rate*dt, while acc>=1 spawn.

Speed variation: speed * (0.5 + Math.random()*0.7)? Let's do base speed with random factor 0.6–1.4, and direction random over 2π. Maybe slight upward bias... no, full circle.

Gravity value 400 px/s².

Also drag? Not needed. Keep simple.

Draw: for each particle, radial gradient is expensive; use plain fillRect/arc with globalAlpha and 'lighter'. Use arc with radius proportional. Let's use ctx.beginPath, arc, fill. With a few thousand particles that's OK-ish. Alternative: draw into trails using fade rect. Let's do a slight trail: fill canvas with rgba(background, 0.25) each frame instead of clearing, giving trails. But then particles fade... trails look nice though. Hmm, but requirement "particles fade out over time" — alpha fade is implemented anyway. Trails could muddy. I'll do full clear with a slight background.

Actually a nice look: clear with solid dark background, use 'lighter' composite for particles so overlapping glow.

Let me cap particle count to avoid perf death (e.g., max 5000).

FPS: use performance.now deltas, smoothed.

Let me write the JS.

```js
const cv = document.getElementById('cv');
const ctx = cv.getContext('2d');
let W=0,H=0,DPR=1;
function resize(){
  const rect = cv.parentElement.getBoundingClientRect();
  W = Math.max(1, rect.width);
  H = Math.max(1, rect.height);
  DPR = Math.min(window.devicePixelRatio||1, 2);
  cv.width = Math.round(W*DPR);
  cv.height = Math.round(H*DPR);
  cv.style.width = W+'px';
  cv.style.height = H+'px';
  ctx.setTransform(DPR,0,0,DPR,0,0);
}
window.addEventListener('resize', resize);
```

Use ResizeObserver on wrapper for robustness.

State:
```js
const state = {
  rate: 120,
  speed: 160,
  lifetime: 1.8,
  color: '#4fd1ff',
  gravity: true
};
```

Controls wiring: sliders with output labels.

Color parsing: hexToRgb for alpha rendering? With 'lighter' composite, using fillStyle with rgba and globalAlpha works: set ctx.globalAlpha = a; ctx.fillStyle = color; fine.

Particle object:
```js
{x,y,vx,vy,life,maxLife,size}
```

Size maybe 1.5–3.5.

Spawn:
```js
function spawn(){
  const a = Math.random()*Math.PI*2;
  const sp = state.speed * (0.55 + Math.random()*0.9);
  particles.push({
    x: ex + Math.cos(a)*2,
    y: ey + Math.sin(a)*2,
    vx: Math.cos(a)*sp,
    vy: Math.sin(a)*sp,
    life: state.lifetime * (0.7 + Math.random()*0.6),
    size: 1 + Math.random()*2.5
  });
}
```
Store maxLife = life at creation.

Update loop:
```js
let last = performance.now();
let acc = 0;
function frame(now){
  const dt = Math.min((now-last)/1000, 0.05);
  last = now;
  // fps
  ...
  acc += state.rate*dt;
  let n = Math.floor(acc);
  acc -= n;
  while(n-- > 0){ if(particles.length < MAX) spawn(); }
  // update
  ...
  render
}
```

FPS smoothing: fpsSmoothed += (1/dt - fpsSmoothed)*0.1.

Display FPS and particle count maybe. Requirement only FPS but particle count is a nice extra.

Render:
```js
ctx.clearRect(0,0,W,H);
// background grid or vignette? keep simple: fill dark
ctx.fillStyle = '#0b0f16'; // handled by CSS? canvas needs fill.
```
Actually let canvas be transparent and CSS background provides it; but trails... just clearRect and rely on CSS background of wrapper. Simpler: clearRect. The particles with 'lighter' composite blend against transparent — lighter on transparent canvas works fine but overlapping glow composites; then the canvas is composited over the black background. That's fine and looks good.

Hmm, with 'lighter' and transparent canvas, result colors add up on transparent black premultiplied... it works, glow accumulates. Fine.

Emitter glow: draw a radial gradient circle at source.

Let's draw source as a small bright dot with radial gradient.

Text: FPS in DOM element overlay.

Let me write everything carefully.

CSS: dark theme, panel with sliders styled.

Slider styling: accent-color: #4fd1ff for simplicity, plus custom track. Use accent-color — modern browsers support. Good enough and no external.

Let me write the full file.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Particle System Editor</title>
<style>
  :root{
    --bg:#0a0d13;
    --panel:#121824;
    --panel-2:#1a2233;
    --text:#e6edf7;
    --muted:#8b9ab3;
    --accent:#4fd1ff;
    --border:#243044;
  }
  *{box-sizing:border-box;}
  html,body{height:100%;}
  body{
    margin:0;
    background:radial-gradient(1200px 800px at 50% 0%, #101827 0%, var(--bg) 60%);
    color:var(--text);
    font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
    overflow:hidden;
  }
  .app{display:flex;flex-direction:column;height:100vh;height:100dvh;}
  header{...}
```

Let me lay out: header with title, main with flex row: stage (flex 1) and panel (300px).

Stage: position relative, margin, border-radius, overflow hidden, background #070a0f, border.

Canvas display block, width/height 100%.

FPS badge: absolute top-left with backdrop blur.

Panel: padding, gap, scroll if needed.

Control group: label row with name and value badge; input range full width.

Buttons: gravity toggle styled.

Let me write CSS thoroughly.

```css
.app{display:flex;flex-direction:column;height:100vh;height:100dvh;padding:16px;gap:14px;}
header{display:flex;align-items:baseline;gap:12px;flex:0 0 auto;}
h1{font-size:16px;margin:0;letter-spacing:.5px;font-weight:600;}
header .sub{font-size:12px;color:var(--muted);}
main{flex:1 1 auto;display:flex;gap:14px;min-height:0;}
.stage{position:relative;flex:1 1 auto;min-width:0;border-radius:14px;border:1px solid var(--border);background:#05070b;overflow:hidden;box-shadow:inset 0 0 60px rgba(0,0,0,.8);}
#cv{display:block;width:100%;height:100%;}
.hud{position:absolute;top:10px;left:12px;font-size:12px;font-variant-numeric:tabular-nums;color:var(--muted);background:rgba(10,14,22,.65);border:1px solid var(--border);border-radius:8px;padding:6px 10px;backdrop-filter:blur(6px);line-height:1.5;}
.hud b{color:var(--accent);font-weight:600;}
.panel{flex:0 0 290px;background:linear-gradient(180deg,var(--panel),#0f1420);border:1px solid var(--border);border-radius:14px;padding:16px;display:flex;flex-direction:column;gap:16px;overflow:auto;}
```

Controls:

```css
.control{display:flex;flex-direction:column;gap:8px;}
.control .row{display:flex;justify-content:space-between;align-items:center;font-size:12px;}
.control .name{color:var(--muted);letter-spacing:.4px;text-transform:uppercase;font-size:11px;}
.control .val{font-variant-numeric:tabular-nums;color:var(--accent);font-weight:600;font-size:12px;background:rgba(79,209,255,.08);border:1px solid rgba(79,209,255,.2);padding:2px 8px;border-radius:999px;}
input[type=range]{-webkit-appearance:none;appearance:none;width:100%;height:6px;border-radius:999px;background:linear-gradient(...);outline:none;}
```

Custom range thumb:
```css
input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;width:16px;height:16px;border-radius:50%;background:var(--accent);border:2px solid #071018;box-shadow:0 0 10px rgba(79,209,255,.7);cursor:pointer;}
input[type=range]::-moz-range-thumb{...}
```

Track background: I'll just set background: #1e2a3d and use a linear-gradient update via JS to show fill? That requires JS setting background. Simpler: static track color. But could do fill with JS on input. Let's keep it simple: static.

Color input:
```css
input[type=color]{-webkit-appearance:none;appearance:none;width:100%;height:38px;border:1px solid var(--border);border-radius:10px;background:transparent;cursor:pointer;padding:4px;}
input[type=color]::-webkit-color-swatch-wrapper{padding:0;}
input[type=color]::-webkit-color-swatch{border:none;border-radius:7px;}
input[type=color]::-moz-color-swatch{border:none;border-radius:7px;}
```

Button:
```css
.btn{width:100%;padding:11px 14px;border-radius:10px;border:1px solid var(--border);background:var(--panel-2);color:var(--text);font-size:13px;font-weight:600;letter-spacing:.3px;cursor:pointer;transition:.18s;display:flex;align-items:center;justify-content:space-between;gap:10px;}
.btn:hover{border-color:#3a4d6b;}
.btn .state{font-size:11px;padding:2px 8px;border-radius:999px;background:#233046;color:var(--muted);}
.btn.on{border-color:rgba(79,209,255,.55);box-shadow:0 0 0 1px rgba(79,209,255,.18), 0 0 18px rgba(79,209,255,.12) inset;background:linear-gradient(180deg,#16283a,#121b28);}
.btn.on .state{background:rgba(79,209,255,.18);color:var(--accent);}
```

Maybe also a "clear particles" button. Fine, extra.

Responsive: @media (max-width: 760px) { main{flex-direction:column;} .panel{flex:0 0 auto; max-height:45%;} }

Now JS.

```js
(function(){
  'use strict';
  const cv = document.getElementById('cv');
  const ctx = cv.getContext('2d', {alpha:true});
  const stage = document.getElementById('stage');
  const fpsEl = document.getElementById('fpsVal');
  const countEl = document.getElementById('countVal');

  const MAX_PARTICLES = 6000;
  const GRAVITY = 420; // px/s^2

  const state = {
    rate: 150,
    speed: 170,
    lifetime: 1.8,
    color: '#4fd1ff',
    gravity: true
  };

  let W=1,H=1;
  function resize(){
    const r = stage.getBoundingClientRect();
    W = Math.max(1, Math.round(r.width));
    H = Math.max(1, Math.round(r.height));
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    cv.width = Math.round(W*dpr);
    cv.height = Math.round(H*dpr);
    ctx.setTransform(dpr,0,0,dpr,0,0);
  }
```

Wait: canvas has CSS width 100% height 100%, so setting cv.width/height attributes and transform is fine. Stage size known.

Emitter position: center of stage: ex = W/2, ey = H*0.5.

Use ResizeObserver:
```js
if (window.ResizeObserver) new ResizeObserver(resize).observe(stage); else window.addEventListener('resize', resize);
resize();
```

Particles array.

Spawn function uses ex,ey computed on the fly.

Colors: store color as string for fillStyle. Use globalAlpha for fade.

Maybe vary particle color slightly? Use the picked color directly.

Render:
```js
function render(){
  ctx.clearRect(0,0,W,H);
  ctx.globalCompositeOperation = 'lighter';
  // glow at emitter
  const g = ctx.createRadialGradient(ex,ey,0,ex,ey,60);
  ...
```
Creating a gradient each frame is fine (once per frame).

Actually the emitter glow uses the picked color too — nice.

```js
  const c = hexToRgb(state.color);
  const grd = ctx.createRadialGradient(ex,ey,0,ex,ey,70);
  grd.addColorStop(0, `rgba(${c.r},${c.g},${c.b},0.25)`);
  grd.addColorStop(1, `rgba(${c.r},${c.g},${c.b},0)`);
  ctx.fillStyle = grd;
  ctx.beginPath(); ctx.arc(ex,ey,70,0,Math.PI*2); ctx.fill();
```

Then particles:
```js
  ctx.fillStyle = state.color;
  for (const p of particles){
    const t = p.life / p.maxLife;   // 1 -> 0
    ctx.globalAlpha = Math.max(0, t) * 0.9;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.size * (0.35 + 0.65*t), 0, Math.PI*2);
    ctx.fill();
  }
```
Arc per particle is somewhat slow with thousands. Could use a pre-rendered sprite: create offscreen canvas with a radial-gradient dot in white, then drawImage scaled with fillStyle... but tinting requires colored sprite. We can create a sprite recolored when color changes: an offscreen canvas of size 64 with radial gradient of current color. Then drawImage(sprite, x-r, y-r, 2r, 2r) with globalAlpha. That's much faster and gives nice soft glow.

Let's do the sprite approach.

```js
let sprite = null;
function buildSprite(){
  const size = 64;
  const c = document.createElement('canvas');
  c.width = c.height = size;
  const sctx = c.getContext('2d');
  const rgb = hexToRgb(state.color);
  const g = sctx.createRadialGradient(size/2,size/2,0,size/2,size/2,size/2);
  g.addColorStop(0, `rgba(${rgb.r},${rgb.g},${rgb.b},1)`);
  g.addColorStop(0.35, `rgba(${rgb.r},${rgb.g},${rgb.b},0.55)`);
  g.addColorStop(1, `rgba(${rgb.r},${rgb.g},${rgb.b},0)`);
  sctx.fillStyle = g;
  sctx.fillRect(0,0,size,size);
  sprite = c;
}
```
Then draw: radius = p.size*2.5 (glow), drawImage(sprite, p.x-r, p.y-r, 2r, 2r) with globalAlpha = t.

With 'lighter' this glows nicely. Particle size base ~2.2 => glow radius ~5.5. Good.

hexToRgb parse for #rrggbb.

But color input might be lowercase hex always; fine, handle both and short forms.

Update loop with fixed timestep? Just use dt clamp.

Particle update:
```js
for (let i = particles.length-1; i>=0; i--){
  const p = particles[i];
  p.life -= dt;
  if (p.life <= 0){ particles.splice(i,1); continue; }
  if (state.gravity) p.vy += GRAVITY*dt;
  p.vx *= drag? no
  p.x += p.vx*dt;
  p.y += p.vy*dt;
  // remove offscreen far away
  if (p.x < -50 || p.x > W+50 || p.y < -50 || p.y > H+50) ... 
```
Hmm, particles with gravity fall off bottom; removing them early is fine but they'd disappear abruptly. Since lifetime bounds it, maybe allow offscreen removal with margin 200. Actually keep them until life ends; they just won't render (still iterated). That's fine for perf since count is bounded by rate*lifetime. Rate 600/s * 5s = 3000. OK.

Actually let's cull when far offscreen (margin 100) to keep counts reasonable. With fade it's ok since they're outside view anyway.

splice in loop is O(n) each; better to use filter or swap-pop. Use swap-pop:
```js
particles[i] = particles[particles.length-1]; particles.pop();
```
Order doesn't matter.

Emission accumulator.

FPS:
```js
let fps = 60, lastT = performance.now(), fpsAccum=0, fpsFrames=0;
```
Update FPS text every ~250ms.

Let's write the loop:

```js
let last = performance.now();
let emitAcc = 0;

function loop(now){
  const dtRaw = (now - last)/1000;
  last = now;
  const dt = Math.min(dtRaw, 0.05);

  // fps
  if (dtRaw > 0){
    fpsSmoothed += ((1/dtRaw) - fpsSmoothed) * 0.08;
  }
  fpsTimer += dtRaw;
  if (fpsTimer >= 0.25){ fpsTimer = 0; fpsEl.textContent = Math.round(fpsSmoothed); countEl.textContent = particles.length; }

  // emit
  emitAcc += state.rate * dt;
  let toSpawn = Math.floor(emitAcc);
  emitAcc -= toSpawn;
  while (toSpawn-- > 0 && particles.length < MAX_PARTICLES) spawn();

  update(dt);
  render();
  requestAnimationFrame(loop);
}
```

Careful: if rate is huge and particles at max, emitAcc still drains — fine.

Emitter position ex, ey computed each frame: ex = W/2, ey = H*0.5.

Hmm — with gravity on, particles fall down and off the bottom quickly. Maybe put emitter at center. It's fine.

Controls wiring:

```js
const rateEl = document.getElementById('rate');
...
function bindSlider(el, key, fmt){
  const valEl = document.getElementById(el.id + 'Val');
  const update = () => { state[key] = parseFloat(el.value); valEl.textContent = fmt(state[key]); };
  el.addEventListener('input', update);
  update();
}
```

Labels: rate "150 /s", speed "170 px/s", lifetime "1.8 s".

Color: input event → state.color = el.value; buildSprite().

Gravity button: toggle class 'on', update state and the .state text.

Clear button: particles.length = 0.

Also keyboard? Not needed.

Now write the HTML controls markup:

```html
<aside class="panel">
  <div class="control">
    <div class="row"><span class="name">Emission Rate</span><span class="val" id="rateVal">150 /s</span></div>
    <input type="range" id="rate" min="0" max="600" step="1" value="150">
  </div>
  <div class="control">
    <div class="row"><span class="name">Particle Speed</span><span class="val" id="speedVal">170 px/s</span></div>
    <input type="range" id="speed" min="10" max="600" step="1" value="170">
  </div>
  <div class="control">
    <div class="row"><span class="name">Lifetime</span><span class="val" id="lifetimeVal">1.8 s</span></div>
    <input type="range" id="lifetime" min="0.2" max="6" step="0.1" value="1.8">
  </div>
  <div class="control">
    <div class="row"><span class="name">Particle Color</span><span class="val" id="colorVal">#4FD1FF</span></div>
    <input type="color" id="color" value="#4fd1ff">
  </div>
  <div class="control">
    <button class="btn on" id="gravityBtn"><span>Gravity</span><span class="state" id="gravityState">ON</span></button>
  </div>
  <div class="control">
    <button class="btn" id="clearBtn"><span>Clear Particles</span><span class="state" id="clearState">—</span></button>
  </div>
</aside>
```

Hmm the clear button state span is odd. Just make it a simple button with centered text. Let me make `.btn` flex with justify-content: space-between only when there are two children. For clear button, single span centered — use `justify-content:center` on a modifier class or just let it be. I'll add class "center".

Actually simpler: gravity button has text "Gravity: ON" and toggle. Let me do:

```html
<button class="btn" id="gravityBtn"><span class="dot"></span><span class="label">Gravity</span><span class="state">ON</span></button>
```
with dot indicator. Nice but let's keep simpler: label left, state right.

For clear: `<button class="btn center" id="clearBtn">Clear Particles</button>`.

Also maybe add a "burst" button? Not required. Skip.

Also info about shortcuts? Skip.

Let's also show particle count in the HUD: "FPS 60 · 421 particles".

Now finalize the render function.

```js
function render(){
  ctx.clearRect(0,0,W,H);
  ctx.globalCompositeOperation = 'lighter';

  const ex = W*0.5, ey = H*0.5;

  // emitter glow
  const gl = ctx.createRadialGradient(ex,ey,0,ex,ey,70);
  const rgb = hexToRgb(state.color);
  gl.addColorStop(0, `rgba(${rgb.r},${rgb.g},${rgb.b},0.30)`);
  gl.addColorStop(0.4, `rgba(${rgb.r},${rgb.g},${rgb.b},0.08)`);
  gl.addColorStop(1, `rgba(${rgb.r},${rgb.g},${rgb.b},0)`);
  ctx.globalAlpha = 1;
  ctx.fillStyle = gl;
  ctx.beginPath(); ctx.arc(ex,ey,70,0,TAU); ctx.fill();

  // particles
  for (let i=0;i<particles.length;i++){
    const p = particles[i];
    const t = p.life / p.maxLife;
    const a = t*t*(3-2*t); // smoothstep-ish fade? or just t
    ctx.globalAlpha = Math.min(1, a);
    const r = p.size * (0.4 + 0.9*t) * 3;
    ctx.drawImage(sprite, p.x-r, p.y-r, r*2, r*2);
  }
  ctx.globalAlpha = 1;
  ctx.globalCompositeOperation = 'source-over';
}
```

Wait sprite drawing with 'lighter' — with alpha applied via globalAlpha. Good.

Note: globalAlpha with drawImage and 'lighter' — works.

Fade: alpha = t (linear) is fine; multipled by sprite gradient. Let's use t^0.8 or smoothstep. Use `const a = t * t` for faster fade? Requirement: fade out over time. Use `a = t` but also shrinking radius. Let's do a = t (linear-ish) — but with 'lighter' accumulation at spawn it'll look bright. Fine.

Actually to avoid too-bright accumulation when many particles overlap, maybe scale alpha by 0.6. Let's use a = t*0.85.

Hmm, with 'lighter' and many particles the center becomes white. That's a nice bloom actually. Keep.

hexToRgb:
```js
function hexToRgb(hex){
  let h = hex.replace('#','').trim();
  if (h.length === 3) h = h.split('').map(c=>c+c).join('');
  const n = parseInt(h,16);
  return { r:(n>>16)&255, g:(n>>8)&255, b:n&255 };
}
```

Careful with NaN if invalid; default handled.

Now spawn:

```js
function spawn(){
  const ex = W*0.5, ey = H*0.5;
  const ang = Math.random()*TAU;
  const sp = state.speed * (0.4 + Math.random()*1.0);
  const life = state.lifetime * (0.65 + Math.random()*0.7);
  particles.push({
    x: ex + Math.cos(ang)*3,
    y: ey + Math.sin(ang)*3,
    vx: Math.cos(ang)*sp,
    vy: Math.sin(ang)*sp,
    life: life,
    maxLife: life,
    size: 0.6 + Math.random()*1.1
  });
}
```

size in CSS px of the "core" radius; drawn radius = size*(0.4+0.9t)*3 → roughly 1.8–5 px at spawn. OK.

Note W and H must be computed before spawn — yes after resize.

Also handle when canvas not yet sized at start (W=1). ResizeObserver fires immediately upon observe. Also call resize() explicitly.

Edge case: `stage` has flex:1 with min-height 0 to allow the canvas to shrink.

Now the update:

```js
function update(dt){
  const g = state.gravity ? GRAVITY : 0;
  for (let i = particles.length-1; i>=0; i--){
    const p = particles[i];
    p.life -= dt;
    if (p.life <= 0){ particles[i] = particles[particles.length-1]; particles.pop(); continue; }
    p.vy += g*dt;
    p.x += p.vx*dt;
    p.y += p.vy*dt;
    if (p.x < -120 || p.x > W+120 || p.y < -120 || p.y > H+120){
      particles[i] = particles[particles.length-1]; particles.pop();
    }
  }
}
```

Careful: swap-pop when i is last index, particles[particles.length-1] is itself — then pop removes it, fine.

Wait, bug: if i === particles.length-1, assigning particles[i] = particles[length-1] is a no-op then pop → correct.

Now, initial `last` time and starting loop.

Also handle visibility change to avoid giant dt — dt clamped to 0.05 anyway.

Also, the dt clamp of 0.05 means at 10fps sim slows; acceptable.

Now let's finalize HUD: `<div class="hud">FPS <b id="fpsVal">--</b> · <b id="countVal">0</b> particles</div>`.

Set fpsVal.textContent = Math.round(fps).

Let's write everything out properly now.

One more thing: the color input label showing hex uppercase — update on input.

Also the range inputs: value display element IDs. In bindSlider I referenced el.id + 'Val' — for rate → 'rateVal' ✓, speed → 'speedVal' ✓, lifetime → 'lifetimeVal' ✓.

Format functions:
- rate: v => v + ' /s'  (use Math.round)
- speed: v => v + ' px/s'
- lifetime: v => v.toFixed(1) + ' s'

Range step for rate 1, speed 1, lifetime 0.1.

Also, maybe rate max 600 is fine; default 150.

Let me also guard: if rate is 0, no spawn.

Write the final file.

For the canvas context: `getContext('2d')`. With alpha true (default). Background from CSS `.stage` background #05070b. Good.

Actually, `clearRect` leaves the canvas transparent, so the stage background shows. Good.

One concern: 'lighter' composite on a transparent canvas — the resulting alpha also adds, so the glow area is semi-transparent bright color; composited over dark bg it looks fine.

Let me write out the code now.

Also add `touch-action: none` maybe not needed.

Final check on panel scroll on small heights: `overflow:auto`.

Let me produce the file.