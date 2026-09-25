Let me build a mini image editor in one HTML file.

Key components:
- Canvas with procedurally drawn landscape (sky gradient, sun, mountains, trees, lake reflection)
- Layers panel with 3+ layers: Background (landscape), Paint layer, Text layer, maybe a "Sun glow" layer. Each layer has visibility toggle and reorder (up/down buttons).
- Toolbar: brush, eraser, shapes (rect/ellipse), text
- Color picker (input type=color plus swatches)
- Opacity slider, blend mode select
- Filters: blur, brightness, contrast, sepia, invert — applied live via CSS filter on the canvas element (simplest, "live"). But filters should apply to the layer? Simpler: apply CSS filters to the canvas composite. Use filter sliders with checkboxes/toggles.
- Status bar showing active tool.

Architecture: Use separate offscreen canvases per layer, composite onto a main canvas each frame. That handles reorder/hide/opacity/blend modes properly.

Layers:
1. "Sky & Mountains" (base landscape drawn procedurally)
2. "Paint" — user strokes
3. "Sun Glow" — a radial glow element? Let's make layer 3 "Text" and layer 4 "Highlights"? Requirement: at least three layers.

Let's do 4 layers:
- L1: "Landscape" (background)
- L2: "Sun Glow" (procedural radial glow with 'screen' blend)
- L3: "Paint" (brush strokes)
- L4: "Label" (text)

Each layer: {name, canvas, visible, opacity, blend}

Render loop: clear main, for each layer in order (bottom first = index 0 renders first), if visible, ctx.globalAlpha = opacity, globalCompositeOperation = blend, drawImage.

Filters: applied as CSS filter on the canvas element: filter: blur(Xpx) brightness(X) contrast(X) sepia(X) invert(X). Live via sliders. That's easy and "applied live".

Demo script: a timeline of actions with a fake cursor. Since it must run from the first second, start immediately with a scheduled script.

Demo sequence (~30s, then loop):
- t=0: cursor appears, moves to toolbar, selects brush (tool highlight)
- t=2: draws strokes on paint layer (cursor moves along a path, brush paints)
- t=7: color picker changes color (swatch highlight), draws more strokes
- t=11: selects shape tool, draws a rectangle/ellipse
- t=14: selects text tool, clicks canvas, types text label on the Label layer (animated typing)
- t=19: adds a new layer (click "Add Layer" button), new layer selected
- t=21: draws on the new layer with eraser? Or draws then erases
- t=23: applies filter (moves slider — blur/brightness/sepia), live
- t=26: toggles a layer visibility off/on
- t=28: reorders layers (moves layer up)
- t=30: loop reset? Let's keep going and then loop to beginning at ~35s.

Actually easier: loop the demo with a reset that restores the initial state.

Let me implement the demo as a timeline array of steps with times and functions, using a clock. Use requestAnimationFrame with elapsed time, and a `demoTime` accumulator.

For animations, I'll need tweened cursor movement. Let me write a helper:

```js
function tween(from, to, dur, ease) -> returns progress function
```

Better approach: build a state machine with a list of "actions" that get scheduled. Each action has duration and an update(t) function; run sequentially.

```js
const script = [
  {dur: 1000, fn:(t)=>{ cursor move from A to B }},
  ...
]
```

Sequential execution: track currentIndex and currentElapsed. In each frame, advance elapsed by dt, call fn(progress), when elapsed > dur, move to next.

This is clean. Let me write it.

Cursor: an absolutely positioned div with a drawn SVG-ish arrow (CSS). Actually "readable icons drawn in code" — I can draw icons using inline SVG. That's code, not external resource. Fine.

Cursor: a div with a SVG arrow path, plus a "ring" pulse when clicking.

Let me design the layout:

```
+-------------------------------------------------------+
| Top bar: title + filter controls?                      |
+--------+------------------------------------+---------+
| Toolbar|            Canvas area              | Layers  |
| (left) |                                     | (right) |
+--------+------------------------------------+---------+
| Status bar: Active tool: Brush | ...                   |
+-------------------------------------------------------+
```

Left toolbar: vertical icon buttons: brush, eraser, shapes (rect, ellipse), text, plus maybe fill/picker. Under it, color picker + swatches.

Right panel: Layers list (top to bottom = topmost first visually), each with thumbnail? Thumbnails would be nice: small canvas rendered from layer canvas. Let's do thumbnail canvases updated periodically. Keep it simple: 36x24 canvas drawn each frame? Could be costly but fine — 4 layers, small canvases, update every ~10 frames.

Plus buttons: Add Layer, Delete, Move Up, Move Down. Opacity slider and blend mode select for the selected layer.

Bottom: filter sliders: Blur, Brightness, Contrast, Sepia, Invert. Plus "Reset filters".

Status bar: Active tool: Brush · Layer: Paint · Size · Position.

Now the procedural landscape. Draw on layer 0 canvas at size e.g. 720x450 (canvas internal resolution). Display size scaled with CSS to fit.

Let me pick canvas size 760 x 470.

Landscape drawing:
- Sky gradient: deep blue to orange near horizon.
- Sun: circle with glow.
- Mountains: layered polygons with jagged peaks, different colors, using a seeded random.
- Lake at bottom: reflection with gradient, horizontal light streaks.
- Trees: simple triangle pines silhouettes on the shore.
- Birds: small curves.

Since the sun glow is a separate layer, I'll draw only the sun disc in the landscape and glow in the glow layer. Actually let's have landscape include mountain + lake + trees, glow layer = radial gradient over the sun with 'screen'/'lighter' blend.

Paint layer starts transparent. Label layer starts transparent.

Eraser: on the paint layer, use destination-out composite operation.

Shapes: rect/ellipse outline or filled. Let's do filled with current color at current opacity.

Text tool: on click, place a text. For demo, we type it char by char on the Label layer with a font.

Now let me write the layer model.

```js
const W=760,H=470;
const layers = []; // index 0 = bottom
function makeLayer(name, opts){ const c=document.createElement('canvas'); c.width=W;c.height=H; return {name, canvas:c, ctx:c.getContext('2d'), visible:true, opacity:1, blend:'source-over', ...opts}; }
```

Render:
```js
function render(){
  mctx.clearRect(0,0,W,H);
  for(const L of layers){
    if(!L.visible) continue;
    mctx.globalAlpha = L.opacity;
    mctx.globalCompositeOperation = L.blend;
    mctx.drawImage(L.canvas,0,0);
  }
  mctx.globalAlpha=1; mctx.globalCompositeOperation='source-over';
}
```

Blend modes map from CSS values: 'normal'->'source-over', 'multiply', 'screen', 'overlay', 'lighten', 'darken', 'difference'.

Filters: apply to the canvas element style:
```js
function updateFilters(){
  const f=[];
  if(F.blur>0) f.push(`blur(${F.blur}px)`);
  ...
  canvas.style.filter = f.join(' ') || 'none';
}
```
Note: CSS blur on the canvas will make edges soft — fine, it's an artistic effect. Add slight padding? Whatever.

Demo script details. Need positions of UI elements. Since layout is fixed-ish, I can query element bounding rects with getBoundingClientRect at runtime and convert to cursor coordinates (viewport coordinates, cursor is position:fixed). That's robust to responsive layout. 

Cursor is `position:fixed; left/top` with transform translate. Move it with tween to target centers.

Actions:
```js
{ dur, label, run(p) }  // p from 0..1
```
But also need start/end instant actions. I'll allow `dur:0` for instant.

Let me define helper functions:

```js
let cur = {x: innerWidth/2, y: innerHeight/2};
function moveTo(x,y,dur, ease){ return {dur, run(p){ cur.x = lerp(sx,x,ease(p)); ... }} }
```
Problem: need start pos captured at action start. I'll have actions as objects with optional `begin()` and `run(p)`.

Simplify: action = {dur, onStart, onUpdate(p), onEnd}.

```js
function act(dur, onUpdate, onStart, onEnd){ return {dur, onUpdate, onStart, onEnd}; }
```

Cursor rendering: each frame set cursorEl.style.transform = `translate(${cur.x}px, ${cur.y}px)`.

Click animation: set a class for 200ms that shows ripple.

Now, painting: while the cursor moves, we paint points into the paint layer at the cursor position with the current brush. Need to convert viewport coords to canvas coords: use canvas.getBoundingClientRect() and scale.

```js
function toCanvas(x,y){ const r=canvas.getBoundingClientRect(); return {x:(x-r.left)*W/r.width, y:(y-r.top)*H/r.height}; }
```

Painting stroke: on each frame during the move, line from last canvas point to new point.

Let me write a Paint helper:
```js
function paintAt(cx,cy, prev){
  const L = activeLayer();
  L.ctx.globalCompositeOperation = tool==='eraser' ? 'destination-out':'source-over';
  L.ctx.strokeStyle = color;
  L.ctx.lineWidth = brushSize;
  L.ctx.lineCap='round'; L.ctx.lineJoin='round';
  if(prev){ L.ctx.beginPath(); L.ctx.moveTo(prev.x,prev.y); L.ctx.lineTo(cx,cy); L.ctx.stroke(); }
  else { L.ctx.beginPath(); L.ctx.arc(cx,cy,brushSize/2,0,7); L.ctx.fillStyle=color; L.ctx.fill(); }
  L.ctx.globalCompositeOperation='source-over';
}
```

Demo must target specific layers regardless of the user's selection? It's a demo; it should set the active layer too, so the UI reflects it.

Let me now write the timeline. I'll define steps with durations summing to ~30-34s.

Sequence plan (ms):
1. 0–900: cursor fades in at center-ish, moves to Brush tool button. Highlight tool button on hover.
2. 900–1100: click brush → tool = brush, status update. (instant click pulse)
3. 1100–1500: move to canvas start point.
4. 1500–4500: paint a stroke (sun rays / wave curves) — paint several strokes: I'll do a couple of segments in one action using a path function. Let's make the action move along a bezier path and paint continuously for 3000ms.
5. 4500–5200: move to color swatch, click (change color to warm orange).
6. 5200–5600: move back to canvas.
7. 5600–8000: paint another stroke with new color (e.g. a bird flock / highlights on the water).
8. 8000–8600: move to shape tool, click.
9. 8600–9200: move to canvas, then 9200–10400: drag to draw ellipse (a sun disc outline? an ellipse "cloud"?). Let's draw a rounded rect frame or an ellipse.
10. 10400–10900: move to Text tool, click.
11. 10900–11300: move to canvas text position, click (sets text caret).
12. 11300–13500: type "Golden Hour" char by char, rendering to Label layer.
13. 13500–14100: move to "Add Layer" button, click → new layer "Layer 5"/"Accents" added, becomes active.
14. 14100–14600: move to canvas.
15. 14600–17000: draw on the new layer (e.g., sparkles / stars in the sky) with a different color... but color is orange. Let's set color to a light cyan via swatch? Or just use current color. Let's click a swatch during the move. Simplify: paint with white-ish. I'll add a step to click the white swatch.
16. 17000–17600: move to Eraser tool, click.
17. 17600–18600: erase a bit on the new layer (shows eraser).
18. 18600–19200: select brush again? Not necessary. Move to Layers panel.
19. 19200–19800: click visibility toggle of "Sun Glow" layer → off; 19800–20400: on again? Better: toggle off and keep it off briefly then on.
20. 20400–21000: move to "Move Up" button, click (reorder).
21. 21000–21600: move to filter slider (Blur), then 21600–22800 drag the slider up (blur increases) — live filter.
22. 22800–23400: move to Sepia slider, drag up 23400–24400.
23. 24400–25000: move to Brightness, drag a bit.
24. 25000–26200: move through contrast/invert toggle? Let's click "Invert" checkbox on briefly then off. Hmm, invert full is dramatic. Maybe toggle invert for 1s and back.
25. 26200–27400: reset filters button click (filters return to 0).
26. 27400–29000: cursor moves to center, rest, "DEMO" badge.
27. 29000–30000: reset everything to initial state (fade?) and loop.

That's about 30s. Good.

Instead of perfect precision, I'll implement enough steps.

Loop: after the script ends, reset the document state (redraw landscape, clear paint layer, remove added layers, reset filters, reset cursor) and restart the script. Add a small "Replay" fade maybe. Keep simple: just restart.

Now let me think about the drag-slider interaction: for range inputs, setting value directly and calling updateFilters + moving cursor works visually. Also add a highlight class on the slider.

Cursor positions for sliders: compute from the slider rect: x = rect.left + rect.width * value/max. Good.

Let me write helper `rectOf(el)` returning center.

Now let's write the code.

HTML structure:

```html
<div id="app">
  <header id="topbar">
    <div class="logo">◆ PIXELFORGE</div>
    <div class="filters">... sliders ...</div>
  </header>
  <div id="main">
    <aside id="tools"> buttons </aside>
    <div id="stage"><canvas id="view"></canvas></div>
    <aside id="layersPanel"> ... </aside>
  </div>
  <footer id="status"> ... </footer>
</div>
<div id="cursor">...</div>
```

Filters in topbar might be cramped. Maybe put filters in the right panel below layers. Let's do:
- Left: toolbar (48px wide icons) + color section below.
- Right: panel 260px with Layers at top and Filters below.

Layout with flex.

CSS dark theme: background #1b1d21, panels #232629, borders #33373d, accent #4aa3ff or #ff9f43. Use accent #5b9dff.

Icons drawn as inline SVG. Let me create SVG strings.

Brush icon: a path. Simple:
```svg
<svg viewBox="0 0 24 24"><path d="M4 20c2 0 3-1 3-3 0-1-.5-2-2-2s-3 1-3 3c0 1 .5 2 2 2z"/><path d="M6.5 15.5 15 7l2 2-8.5 8.5z"/></svg>
```
Eh, let me just use simple recognizable shapes with stroke/fill.

I'll define icons as stroke-based line art:
- brush: `<path d="M3 21s2 0 3.5-1.5S9 16 9 16l-2-2s-1.5 1-2.5 2.5S3 21 3 21z"/><path d="M9 14l9-9 3 3-9 9"/>` — roughly.

Simpler: use a set of paths with `stroke="currentColor" fill="none" stroke-width="1.8"`.

brush: `<path d="M4 20c0-2 1-3 2.5-3S9 18 9 19s-2.5 1-5 1z" fill="currentColor"/><path d="M8.5 14.5 18 5l2 2-9.5 9.5z"/>`

eraser: `<path d="M7 20h12"/><path d="M4.5 15.5 12 8l5 5-4.5 4.5H7z"/>` hmm. Let's do rotated rect: `<rect x="3" y="11" width="13" height="7" rx="1.5" transform="rotate(-45 9.5 14.5)"/>` complicated. Alternative: `<path d="M6 18 L14 10 L20 16 L16 20 L8 20 Z"/>` fine-ish.

Let me just craft decent simple ones:

- brush: line from bottom-left to top-right with a tip triangle.
- eraser: parallelogram.
- shapes: square + circle overlapping.
- text: a "T" letter with serifs: `<path d="M5 5h14M12 5v14M9 19h6"/>`
- move/select: arrow.
- fill: bucket.

Text icon: `M6 5h12M12 5v14M9 19h6` — a T.

Shapes icon: `<rect x="3" y="8" width="10" height="10" rx="1"/><circle cx="16" cy="9" r="5"/>` overlapping.

Eraser icon: `<path d="M8 20h11M4 16l6-6 6 6-4 4H8z"/>` — hmm, "4 16" then "l6-6" → to (10,10), then "l6 6" → (16,16), then "l-4 4" → (12,20), then "H8" → (8,20), close → back to (4,16). That's a decent eraser shape. Plus baseline.

OK good enough.

Cursor: an arrow SVG, white with dark outline, position fixed, pointer-events none, transform translate.

```html
<div id="cursor"><svg width="22" height="22" viewBox="0 0 24 24"><path d="M5 3l14 8-6 1.5L10 19z" fill="#fff" stroke="#000" stroke-width="1.2"/></svg><span class="ripple"></span></div>
```
Add class 'click' to animate ripple.

Now layers panel rendering. Build DOM once and update. Each row:
```html
<div class="layer" data-i="3">
  <canvas class="thumb"></canvas>
  <div class="lname">Label</div>
  <button class="eye">👁</button>
</div>
```
Eye icon as SVG toggled by class.

Order: topmost layer displayed first. layers array index 0 = bottom, so display reversed.

Moving up means moving toward the end of the array (index+1). Let's implement moveLayer(i, +1) => toward top.

Selected layer gets highlight.

Thumbnails: draw layer canvas scaled into thumb canvas with a checkerboard? Just dark background. Update on demand (every frame at low rate, e.g., every 6 frames) — 4-5 layers × small canvas every 100ms is fine.

Actually drawing the full 760x470 canvas into a 44x28 thumb 60 times/sec might be okay but let's throttle to every 100ms.

Now the painting performance is fine.

Let's write the landscape drawing function.

```js
function drawLandscape(ctx){
  const W=..., H=...;
  // sky
  const sky = ctx.createLinearGradient(0,0,0,H*0.7);
  sky.addColorStop(0,'#0b1e3a');
  sky.addColorStop(0.35,'#2a4a7a');
  sky.addColorStop(0.6,'#d97b4a');
  sky.addColorStop(0.78,'#f2a65a');
  sky.addColorStop(1,'#ffd9a0');
  ctx.fillStyle=sky; ctx.fillRect(0,0,W,H);
  // sun
  ...
}
```

Horizon at H*0.62. Lake from H*0.62 to H.

Mountains: draw 3 ranges with decreasing darkness.

Use a seeded PRNG for reproducibility.

```js
function mulberry32(a){return function(){a|=0;a=a+0x6D2B79F5|0;var t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}}
```

Mountain range function:
```js
function ridge(ctx, rng, baseY, height, color, peaks){ ... }
```
Build a path from x=0 to W with random peaks.

Trees: pines along the shore at y≈horizon.

Lake: gradient from dark to warm, plus horizontal sun reflection streaks.

Let's write it:

```js
function drawLandscape(){
  const ctx = layers[0].ctx;
  const horizon = H*0.6;
  // sky
  ...
  // stars? nah
  // sun disc
  ctx.save();
  ctx.beginPath(); ctx.arc(W*0.72, horizon-70, 34, 0, 7);
  ctx.fillStyle='#fff3c4'; ctx.shadowColor='#ffcb6b'; ctx.shadowBlur=40; ctx.fill();
  ctx.restore();
  // mountain ranges
  ridge(ctx, rng, horizon+4, 150, '#3c4a63', 5);
  ridge(ctx, rng, horizon+4, 105, '#2b3550', 7);
  ridge(ctx, rng, horizon+4, 62, '#1c2438', 9);
  // lake
  const lake = ctx.createLinearGradient(0,horizon,0,H);
  lake.addColorStop(0,'#f0a868'); lake.addColorStop(0.25,'#8a5a55'); lake.addColorStop(1,'#141a2c');
  ctx.fillStyle=lake; ctx.fillRect(0,horizon,W,H-horizon);
  // reflection streaks
  ...
  // sun reflection column
  // trees silhouettes
  // birds
}
```

Order matters: draw sun before mountains so mountains overlap it. Good.

Sun glow layer: radial gradient centered at sun, blend 'screen' or 'lighter'. Drawn once.

Let's write the ridge function:

```js
function ridge(ctx, rng, baseY, h, color, n){
  ctx.beginPath();
  ctx.moveTo(0, baseY);
  const step = W/n;
  let x=0;
  for(let i=0;i<n;i++){
    const px = x + step*rng();
    ...
  }
}
```
Simpler: generate points at intervals with random heights and use lineTo.

```js
function ridge(ctx,rng,baseY,h,color,n){
  const pts=[[0, baseY - h*(0.3+rng()*0.7)]];
  for(let i=1;i<=n;i++){
    pts.push([ (i/n)*W, baseY - h*(0.25+rng()*0.85) ]);
  }
  ctx.beginPath();
  ctx.moveTo(0, baseY);
  for(const p of pts) ctx.lineTo(p[0], p[1]);
  ctx.lineTo(W, baseY);
  ctx.closePath();
  ctx.fillStyle=color; ctx.fill();
}
```
That gives sharp zigzag peaks. With large n it looks like mountains. Good. Maybe use quadratic smoothing? Sharp is fine for stylized.

Trees: draw pines at the shoreline.

```js
for(let i=0;i<14;i++){
  const x = rng()*W; const y = horizon + 6 + rng()*10; const s = 8+rng()*14;
  pine(ctx, x, y, s, '#0d1424');
}
```

pine: triangle stack.

Now the demo script. Let me write the code carefully.

```js
const script = [];
function step(dur, onUpdate, onStart, onEnd){ script.push({dur,onUpdate,onStart,onEnd}); }
```

Cursor movement helper:

```js
function moveTo(targetFn, dur, easing){
  let sx, sy, tx, ty;
  return {
    dur,
    onStart(){ const p = targetFn(); tx=p.x; ty=p.y; sx=cursor.x; sy=cursor.y; },
    onUpdate(p){ const e = easing? easing(p): easeInOut(p); cursor.x = sx+(tx-sx)*e; cursor.y = sy+(ty-sy)*e; }
  };
}
```
targetFn returns {x,y} in viewport coords.

Define targets:
```js
const elCenter = el => { const r = el.getBoundingClientRect(); return {x:r.left+r.width/2, y:r.top+r.height/2}; };
```

For the slider handle position:
```js
const sliderTarget = (el, v) => { const r=el.getBoundingClientRect(); return {x: r.left + 8 + (r.width-16)*(v/el.max), y: r.top+r.height/2}; };
```
Roughly.

Now writing the steps. I'll write a builder function `buildScript()` that appends steps. Since targets are computed at start time via functions, layout changes are handled.

Let me define actions:

```js
function clickAt(targetFn, dur=600){
  return [
    moveTo(targetFn, dur),
    { dur: 180, onStart(){ pulseClick(); }, onUpdate(){} }
  ];
}
```
But my step system is flat; I'll push both.

Let me structure:

```js
let script = [];
function push(o){ script.push(o); }

function hoverAndClick(targetFn, moveDur, onActivate){
  push(moveTo(targetFn, moveDur));
  push({dur:140, onStart(){ ripple(); }, onUpdate(){}});
  push({dur:0, onStart(){ onActivate && onActivate(); }});
}
```
dur:0 steps should complete immediately in one frame — need the runner to handle dur 0: run onStart, then finish.

Runner:
```js
let idx=0, el=0;
function updateDemo(dt){
  if(idx>=script.length){ restartDemo(); return; }
  const s = script[idx];
  if(!s.started){ s.started=true; s.onStart && s.onStart(); }
  el += dt;
  const p = s.dur>0 ? Math.min(1, el/s.dur) : 1;
  s.onUpdate && s.onUpdate(p);
  if(p>=1){ s.onEnd && s.onEnd(); idx++; el=0; }
}
```
Hmm, with dur 0, p=1 immediately, onUpdate called once. Fine.

Careful: onStart for a dur-0 step runs then onUpdate then end. OK.

Restart: reset everything and idx=0, el=0, and clear the `started` flags. Since steps are objects with started flag, reset them all.

Actually simpler: rebuild the script each loop. Since steps use closures, rebuilding is fine.

Let's structure the demo as a function `runDemo()` that sets up the script and resets the runner.

Now the paint-stroke steps. I need an action that moves the cursor along a path while painting.

```js
function strokeAction(pathFn, dur){
  // pathFn(t) -> canvas coords {x,y}
  let last=null;
  return {
    dur,
    onStart(){ last=null; setTool('brush'); },
    onUpdate(p){
      const c = pathFn(easeInOut(p));
      const v = canvasToViewport(c.x,c.y);
      cursor.x=v.x; cursor.y=v.y;
      const L=activeLayer();
      paintSegment(L, last, c);
      last=c;
    }
  };
}
```

canvasToViewport converts canvas coords to screen coords using the canvas rect.

paintSegment draws a line with the current color/size and layer's ctx.

Wait — for the demo we should also make sure the active layer is the paint layer. I'll set activeLayerIndex in onStart.

Let me define `setActiveByName(name)`.

Path functions: e.g., a sine wave across the water:
```js
t => ({x: 60 + t*640, y: 330 + Math.sin(t*Math.PI*3)*18})
```
But we should clip within canvas. Fine.

Note: the demo cursor moves in viewport coordinates; the canvas has CSS size maybe different from W,H. Handle by scaling.

Also the demo should paint while the cursor moves — that's exactly this.

Text typing: an action that types characters over time.

```js
{ dur: 2200, onStart(){ labelText=''; }, onUpdate(p){ 
   const target='Golden Hour';
   const n = Math.floor(p*target.length);
   if(n!==labelText.length){ labelText = target.slice(0,n); drawLabel(); }
}}
```

drawLabel clears the label layer and draws the text.

Text drawn with a nice font: 'Georgia, serif' — system fonts are fine (not external). Use italic serif. Add a subtle shadow.

Now for layer toggling: click the eye button of the "Sun Glow" layer.

Reorder: click the "up" button on the selected layer a couple times, or use a dedicated button.

Filter drag: 
```js
function dragSlider(el, from, to, dur){
  let start;
  return { dur, onStart(){ start = from; }, onUpdate(p){
    const v = start + (to-start)*easeInOut(p);
    el.value = v; updateFilters(); syncFilterUI();
    // move cursor to handle
    const r = el.getBoundingClientRect();
    const c = elCenter(el);
    cursor.x = r.left + (r.width-18)*(v/el.max) + 9;
    cursor.y = r.top + r.height/2;
  }};
}
```
Hmm, the slider handle offset. Range input thumb width ~16px. Approximate: x = r.left + 8 + (r.width-16)*(v/max). Good enough.

Now, the filters panel UI: for each filter a row: label, range input, value.

Filters: blur 0-10 (px), brightness 50-150 (%), contrast 50-150 (%), sepia 0-100 (%), invert 0-100 (%). Invert as a slider is easier for the demo (drag it up).

updateFilters builds the CSS filter string.

Now let's think about what "applied live" means — CSS filter on the canvas element applies to the whole composite, which is a legit "filter". Good.

Alright, also need a "status bar with the active tool". Bottom bar: `Tool: Brush · Layer: Paint · Size: 12 px · Pos: 420, 180` and maybe a hint "DEMO RUNNING".

Let's write the code now.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PixelForge — Mini Image Editor</title>
<style> ... </style>
</head>
<body>
<div class="app">
  <header class="topbar">
    <div class="brand"><span class="dot"></span> PIXELFORGE <span class="sub">mini image editor</span></div>
    <div class="topright">
      <span class="demo-badge" id="demoBadge">● DEMO</span>
    </div>
  </header>
  <div class="body">
    <aside class="toolbar" id="toolbar">
      <!-- tool buttons -->
      <div class="tool" data-tool="brush">svg</div>
      ...
      <div class="sep"></div>
      <div class="colors">
        <input type="color" id="colorInput" value="#ffd166">
        <div class="swatches">...</div>
      </div>
    </aside>
    <main class="stage"><div class="canvasWrap"><canvas id="view"></canvas></div></main>
    <aside class="panel"> layers + filters </aside>
  </div>
  <footer class="status"> ... </footer>
</div>
<div id="cursor">...</div>
```

Layout heights: use flex column, body flex:1 min-height 0, overflow hidden.

Canvas sizing: The canvas is W=760,H=470 internal; CSS max-width:100%, max-height:100%, object-fit contain... For canvas, set CSS width/height via aspect-ratio. Use:
```css
.canvasWrap{ position:relative; width:100%; height:100%; display:flex; align-items:center; justify-content:center; }
#view{ max-width:100%; max-height:100%; box-shadow: ...; border-radius:4px; }
```
With `max-width:100%; max-height:100%` on a canvas of intrinsic 760x470, the browser scales it preserving aspect ratio? For canvas, if only max-width is set, height auto scales... Actually canvas has intrinsic aspect ratio, and with max-width:100% and max-height:100%, the browser will shrink it preserving aspect ratio (like an image). Yes, replaced elements preserve aspect ratio. Good.

Then `getBoundingClientRect` gives the displayed size for coordinate conversion. 

Now let's write everything out.

CSS:

```css
*{box-sizing:border-box}
html,body{height:100%;margin:0}
body{
  background:#0e1013;
  color:#c9ced6;
  font:13px/1.4 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  overflow:hidden;
  user-select:none;
}
.app{display:flex;flex-direction:column;height:100vh;}
.topbar{height:44px;display:flex;align-items:center;justify-content:space-between;padding:0 14px;background:linear-gradient(#24272c,#1c1f23);border-bottom:1px solid #0a0c0e;}
.brand{font-weight:700;letter-spacing:2px;font-size:12px;color:#e8ecf1;display:flex;align-items:center;gap:8px}
.dot{width:9px;height:9px;border-radius:2px;background:linear-gradient(135deg,#5b9dff,#a06bff);display:inline-block}
.sub{font-weight:400;color:#5c646f;letter-spacing:0;margin-left:6px}
.demo-badge{font-size:11px;letter-spacing:1px;color:#7ee787;border:1px solid #2b4a30;background:#16241a;padding:3px 9px;border-radius:20px}
```

Body area:
```css
.body{flex:1;display:flex;min-height:0}
.toolbar{width:56px;background:#1a1d21;border-right:1px solid #0a0c0e;display:flex;flex-direction:column;align-items:center;padding:8px 0;gap:6px}
.tool{width:40px;height:40px;border-radius:8px;display:grid;place-items:center;color:#8b93a0;cursor:pointer;transition:.15s}
.tool:hover{background:#24282e;color:#dfe5ec}
.tool.active{background:#2b3b57;color:#8bbcff;box-shadow:inset 0 0 0 1px #3d6bb0}
.tool svg{width:22px;height:22px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}
```

Panel:
```css
.panel{width:264px;background:#1a1d21;border-left:1px solid #0a0c0e;display:flex;flex-direction:column;min-height:0}
```

Section headers.

Layer rows.

Status bar:
```css
.status{height:26px;background:#161a1e;border-top:1px solid #0a0c0e;display:flex;align-items:center;gap:16px;padding:0 12px;font-size:11.5px;color:#79828f}
.strong{color:#cfd6df}
```

Cursor:
```css
#cursor{position:fixed;left:0;top:0;width:22px;height:22px;pointer-events:none;z-index:9999;transform:translate(-100px,-100px);transition:opacity .4s;filter:drop-shadow(0 2px 3px rgba(0,0,0,.6))}
.ripple{position:absolute;left:2px;top:2px;width:8px;height:8px;border-radius:50%;border:2px solid #5b9dff;opacity:0;transform:translate(-50%,-50%)}
#cursor.click .ripple{animation:rip .45s ease-out}
@keyframes rip{0%{opacity:1;width:6px;height:6px}100%{opacity:0;width:44px;height:44px}}
```

Hmm, ripple positioning: cursor element is 22x22 with the arrow at the top-left. Place ripple at (4,4).

Let's do:
```css
.ripple{position:absolute;left:4px;top:4px;width:10px;height:10px;margin:-5px 0 0 -5px;border-radius:50%;border:2px solid #6ba8ff;opacity:0}
```
And the animation expands via width/height... easier with transform scale:
```css
@keyframes rip{0%{opacity:.9;transform:scale(.4)}100%{opacity:0;transform:scale(4)}}
```

OK.

Now filters UI:

```html
<div class="panel-section">
  <div class="sec-head">FILTERS <button id="resetFilters" class="mini">RESET</button></div>
  <div class="filter-row"><label>Blur</label><input type="range" id="f-blur" min="0" max="12" step="0.1" value="0"><span id="v-blur">0</span></div>
  ...
</div>
```

Layers section:
```html
<div class="panel-section layers">
  <div class="sec-head">LAYERS</div>
  <div id="layerList" class="layer-list"></div>
  <div class="layer-controls">
    <button id="btnAdd">+ Add</button>
    <button id="btnDel">Del</button>
    <button id="btnUp">▲</button>
    <button id="btnDown">▼</button>
  </div>
  <div class="layer-props">
    <div class="row"><label>Opacity</label><input id="opacity" type="range" min="0" max="100" value="100"><span id="opacityVal">100%</span></div>
    <div class="row"><label>Blend</label><select id="blend">...</select></div>
  </div>
</div>
```

Buttons need SVG-ish text; ▲▼ are text characters, acceptable? "readable icons drawn in code" — text arrows are fine but let's use SVG triangles for consistency. Meh, use small SVGs.

Actually to keep it manageable, I'll use SVG for the tool icons and simple text glyphs for the small control buttons, but let me use SVGs there too — it's cheap.

Let me write the layer list item HTML template:

```js
function renderLayers(){
  layerList.innerHTML='';
  for(let i=layers.length-1;i>=0;i--){
    const L=layers[i];
    const row=document.createElement('div');
    row.className='layer-row'+(i===activeLayer?' selected':'');
    row.dataset.i=i;
    row.innerHTML=`
      <button class="eye ${L.visible?'on':''}" data-act="eye" data-i="${i}">${eyeSVG}</button>
      <canvas class="thumb" width="52" height="32"></canvas>
      <div class="lname">${L.name}</div>
      <div class="lmeta">${L.blendLabel} · ${Math.round(L.opacity*100)}%</div>
    `;
    layerList.appendChild(row);
    // draw thumb
    ...
  }
}
```
Rendering the whole list on each change is fine, but doing it 60fps for thumbnails isn't. I'll render the list structure on changes, and update thumbnails every 120ms via a separate loop that queries existing thumb canvases.

Let's store references: after building rows, keep an array of thumb canvases paired with layer indices.

```js
let thumbRefs = [];
function renderLayers(){ ... thumbRefs=[]; ... thumbRefs.push({cv, layer:L}); }
function updateThumbs(){ for(const t of thumbRefs){ const c=t.cv.getContext('2d'); c.clearRect(0,0,52,32); c.fillStyle='#101317'; c.fillRect(0,0,52,32); c.drawImage(t.layer.canvas,0,0,52,32); } }
```
Thumbnails don't account for hidden state; add opacity if hidden. Fine.

Clicking a layer row selects it. Clicking the eye toggles visibility.

Now, the demo clicks the eye — I need to route through the same functions: `toggleVisible(i)`.

Also the demo's cursor click on a DOM element should visually highlight it. I'll add a temporary class.

Let me write the demo with direct function calls (not synthetic events) for reliability, while the cursor moves to the element.

Now let's write the code in full.

```js
const W=760,H=470;
const view=document.getElementById('view');
view.width=W; view.height=H;
const vctx=view.getContext('2d');

// ---- Layers ----
let layers=[];
let activeLayer=0;
let uid=0;

function newLayerCanvas(){ const c=document.createElement('canvas'); c.width=W; c.height=H; return c; }

function addLayer(name, opts={}){
  const c=newLayerCanvas();
  const L={id:++uid,name,canvas:c,ctx:c.getContext('2d'),visible:opts.visible!==false,opacity:opts.opacity??1,blend:opts.blend??'source-over',blendLabel:opts.blendLabel??'Normal'};
  layers.push(L);
  return L;
}
```

Wait, layers array order: index 0 = bottom. When we insert a new layer, we push it on top and set active.

Layer set:
```js
function initLayers(){
  layers=[];
  const bg = addLayer('Landscape');
  const glow = addLayer('Sun Glow',{blend:'screen',blendLabel:'Screen',opacity:0.85});
  const paint = addLayer('Paint');
  const text = addLayer('Text');
  drawLandscape(bg.ctx);
  drawGlow(glow.ctx);
  activeLayer = layers.indexOf(paint);
}
```

Hmm, but if the paint layer is above the Text layer... order: Landscape, Sun Glow, Paint, Text. Text on top. Good.

Wait, but the sun glow layer with screen blend sits above the landscape. When we toggle it, visible difference. Good.

drawGlow: radial gradient at sun position (W*0.72, horizon-70) with radius ~180, from rgba(255,200,120,0.55) to transparent.

Now the render loop:

```js
function render(){
  vctx.clearRect(0,0,W,H);
  for(const L of layers){
    if(!L.visible||L.opacity<=0) continue;
    vctx.globalAlpha=L.opacity;
    vctx.globalCompositeOperation=L.blend;
    vctx.drawImage(L.canvas,0,0);
  }
  vctx.globalAlpha=1;
  vctx.globalCompositeOperation='source-over';
}
```

Called every frame (rAF). Fine.

Filters applied via CSS.

Now let me write the demo script concretely.

Helper for cursor target of DOM elements by id.

```js
const $ = s=>document.querySelector(s);
const centerOf = el => { const r=el.getBoundingClientRect(); return {x:r.left+r.width/2,y:r.top+r.height/2}; };
```

Target for tool button: `() => centerOf(toolEls.brush)`.

Let me store tool buttons in a map: `toolButtons = {brush: el, eraser: el, shape: el, text: el}`.

Demo steps:

```js
function buildDemo(){
  const S=[];
  const push=(o)=>S.push(o);
  const ease = p => p<0.5?2*p*p:1-Math.pow(-2*p+2,2)/2;

  function moveTo(getTarget, dur){
    push({dur, onStart(){ const t=getTarget(); this.sx=cursor.x; this.sy=cursor.y; this.tx=t.x; this.ty=t.y; },
      onUpdate(p){ const e=ease(p); cursor.x=this.sx+(this.tx-this.sx)*e; cursor.y=this.sy+(this.ty-this.sy)*e; }});
  }
  function click(getTarget, dur, fn){
    moveTo(getTarget, dur);
    push({dur:120, onStart(){ ripple(); }, onUpdate(){}});
    push({dur:0, onStart(){ fn&&fn(); }});
  }
```

Wait — `moveTo` pushes; `click` calls moveTo then pushes click steps. Good.

Tool selection: `setTool('brush')` updates UI + status.

Stroke helper:
```js
function stroke(getPath, dur, layerName){
  push({dur, onStart(){ this.last=null; setActiveLayerByName(layerName); },
    onUpdate(p){ const c=getPath(ease(p)); const v=cv2vp(c.x,c.y); cursor.x=v.x; cursor.y=v.y; paintSeg(this.last,c); this.last=c; }});
}
```
But `this` inside onUpdate refers to the step object — I set this.last in onStart, and in onUpdate `this` is the step object too (since called as s.onUpdate(p)). Yes, in my runner I call `s.onUpdate(p)` so `this` is s. Good.

paintSeg(from,to) paints on the active layer:
```js
function paintSeg(a,b){
  const L=layers[activeLayer];
  const ctx=L.ctx;
  ctx.save();
  ctx.globalCompositeOperation = (tool==='eraser')?'destination-out':'source-over';
  ctx.strokeStyle=color; ctx.lineWidth=brushSize; ctx.lineCap='round'; ctx.lineJoin='round';
  ctx.beginPath();
  if(a) { ctx.moveTo(a.x,a.y); } else { ctx.moveTo(b.x-0.01,b.y); }
  ctx.lineTo(b.x,b.y);
  ctx.stroke();
  ctx.restore();
}
```

Now the actual timeline. Positions: canvas region — I'll compute canvas coords:

Canvas is 760x470. Landscape: horizon at 282 (0.6*470). Water from 282 to 470. Sky above.

Stroke 1: warm highlights on the water — a wavy horizontal line around y≈340. Path: `t => ({x: 90 + t*580, y: 345 + Math.sin(t*Math.PI*4)*14})`.

Stroke 2: after color change to a light blue, paint clouds? Or bird shapes. Let's paint a wave crest.

Let's finalize the timeline with times:

0.0–1.0s: cursor fades in, move to Brush button (from off-canvas start).
1.0–1.15: click → tool brush.
1.15–1.9: move to canvas start (canvas coord 90,345).
1.9–4.4: stroke 1 (2.5s).
4.4–5.0: move to orange swatch / color input? Use a swatch element. Click sets color.
5.0–5.2: click.
5.2–5.8: move back to canvas (coord 120, 400).
5.8–7.8: stroke 2 (a wave in the water).
7.8–8.4: move to shape tool.
8.4–8.6: click shape tool.
8.6–9.2: move to canvas (coord 560,180).
9.2–10.4: shape drag: cursor moves from (560,180) to (660,240) drawing an ellipse on the paint layer... Actually a shape tool drag creates a preview and commits on release. Let's implement: shape tool drag draws ellipse into a preview canvas (or just draws live on the layer clearing previous). Simpler: during the drag, draw the shape into the active layer, but store the layer's image data before the drag and restore each frame. With a 760x470 canvas, getImageData/putImageData each frame is ~1.4MB — that's fine at 60fps? Probably okay but let's use a separate preview overlay approach instead.

Alternative simpler approach: keep a `shapePreview` canvas (same size), render it on top in the composite when active. On drag, clear the preview and draw the ellipse. On release, commit to the layer.

That's clean. Add a module-level `previewCanvas` drawn in render() after the layers (always on top), then cleared on commit.

Actually simplest: draw shape preview into a transient canvas that's composited in render. Let me add:
```js
const previewC = document.createElement('canvas'); previewC.width=W;previewC.height=H;
const pctx = previewC.getContext('2d');
let previewActive=false;
```
In render: after layers, `if(previewActive){ vctx.globalAlpha=1; vctx.globalCompositeOperation='source-over'; vctx.drawImage(previewC,0,0); }`.

For the demo shape: onStart set shapeStart; onUpdate draw ellipse in preview; onEnd commit to layer.

Commit: `layers[activeLayer].ctx.drawImage(previewC,0,0)` with globalAlpha... just drawImage; then clear preview; previewActive=false.

Good.

10.4–10.8: click release (commit shape).
10.8–11.4: move to Text tool.
11.4–11.6: click text tool.
11.6–12.2: move to canvas (coord 380, 120).
12.2–12.4: click to place text → sets textPos, starts typing.
12.4–14.6: type "Golden Hour" (2.2s).
14.6–15.2: move to Add Layer button.
15.2–15.4: click → addLayer('Accents'), active = new layer.
15.4–16.0: move to a swatch (light cyan/white).
16.0–16.2: click → color = #bde0ff.
16.2–16.8: move to canvas.
16.8–18.6: stroke 3 (sparkles/stars) on the Accents layer.
18.6–19.2: move to Eraser tool.
19.2–19.4: click eraser.
19.4–20.2: move to canvas + erase drag 20.2–21.4 (erase part of the stroke).
21.4–22.0: move to the brush tool? Not needed. Move to the Sun Glow eye button.
22.0–22.2: click eye → toggle glow off.
22.2–23.0: pause (move slightly to layer name). Then 23.0–23.2: click eye again → on.
23.2–23.8: move to "Up" button.
23.8–24.0: click up → reorder active layer up. Hmm, active layer is Accents which is on top already; moving up does nothing. Let's select the "Paint" layer first then move it up above Accents. Or select Accents and move down. Let's do: click the "Paint" layer row (select), then click ▲ twice. That changes the composite order visually (paint above accents... wait, moving Paint up above Accents means paint strokes cover the sparkles). Subtle but visible.

Simpler and more visible: click the Landscape layer row and press ▲ — no, moving landscape up above the glow would cover the glow... but the glow is 'screen' blend; with landscape above it, the screen blend still applies to the composite. Hmm, order matters for the result.

Let's just do: select "Sun Glow" layer row, then click ▼ to move it below Landscape? Then it'd be hidden by the landscape (glow at bottom, landscape on top is opaque → glow invisible). That's a visible change but maybe confusing.

Let's do: select "Paint" layer, click ▲ (move up above Text) — the paint strokes then cover the text partially. Visible enough.

Alternatively move Accents (top) down one. Whatever. I'll do: select Paint layer, click ▲ once → order becomes Landscape, Glow, Text, Paint. The paint strokes now render above the text. Since strokes are on water and text is in the sky, no visual overlap... not visible.

OK: make the reorder visible by having the demo paint a stroke that overlaps the text region. Meh.

Alternative: reorder the Sun Glow layer. Select Sun Glow (index 1) and move it up to index 2 (above Paint). Then glow over paint. Barely visible.

Honestly, reordering is a UI action; the demo shows the button click and the panel rows animate/reorder. That's enough demonstration. I'll add a brief highlight flash on the moved row.

Let me do: select "Text" layer, click ▼ (move down below Paint). The text is drawn in the sky, and paint strokes... the second stroke is in the water — no overlap. Fine, the panel shows the change.

Actually, let's make the paint demo include a stroke that overlaps the text, e.g. stroke 2 sweeps across the sky near the text. Then moving Paint below Text makes the text appear on top of... no.

I'll keep it simple: the layer list visibly reorders. Good enough.

24.0–25.0: move to Blur slider, then drag 25.0–26.2: blur 0→7.
26.2–27.0: move to Sepia, drag 27.0–28.0: sepia 0→70.
28.0–28.6: move to Brightness, drag 28.6–29.6: brightness 100→128.
29.6–30.2: move to Invert, drag 30.2–31.0: invert 0→100 (dramatic!) — maybe skip invert or do a quick flash. Let's do invert to 100 for 0.4s then back to 0. Actually a full invert looks striking in a demo. Let's do it: 30.2–31.2 invert 0→100, hold, 31.4–32.4 invert 100→0.
32.4–33.2: move to Reset filters, click at 33.2.
33.2–34.0: everything back to normal.
34.0–35.0: cursor moves to center and fades out; then reset & loop.

Total ~35s. Within the 30s window we cover everything important (filters and reset happen around 24-33s... that's past 30s for the last bit). Let me compress a bit to fit the important stuff in 30s.

Let me tighten:

- 0–1.0 move to Brush, 1.0–1.2 click
- 1.2–1.8 move to canvas
- 1.8–4.0 stroke 1
- 4.0–4.6 move to swatch, 4.6–4.8 click
- 4.8–5.3 move to canvas
- 5.3–7.2 stroke 2
- 7.2–7.8 move to shape tool, 7.8–8.0 click
- 8.0–8.5 move to canvas, 8.5–9.7 shape drag, 9.7–9.9 commit
- 9.9–10.4 move to text tool, 10.4–10.6 click
- 10.6–11.1 move to canvas text pos, 11.1–11.3 click
- 11.3–13.3 type "Golden Hour"
- 13.3–13.9 move to Add Layer, 13.9–14.1 click
- 14.1–14.6 move to swatch, 14.6–14.8 click
- 14.8–15.3 move to canvas
- 15.3–17.0 stroke 3
- 17.0–17.5 move to eraser, 17.5–17.7 click
- 17.7–18.2 move to canvas, 18.2–19.2 erase drag
- 19.2–19.8 move to Sun Glow eye, 19.8–20.0 click (off)
- 20.0–20.8 pause/move to layer row, 20.8–21.0 click eye (on)
- 21.0–21.6 move to ▼, 21.6–21.8 click (reorder)
- 21.8–22.4 move to blur, 22.4–23.4 drag blur 0→7
- 23.4–24.0 move to sepia, 24.0–25.0 drag sepia 0→70
- 25.0–25.6 move to brightness, 25.6–26.4 drag brightness 100→130
- 26.4–27.0 move to invert, 27.0–27.8 drag invert 0→100
- 27.8–28.3 hold
- 28.3–29.1 drag invert 100→0
- 29.1–29.7 move to Reset, 29.7–29.9 click
- 29.9–31.0 move to center, fade out
- 31.0 → reset and loop

Great, everything within 30s.

Now, the reset function for looping: delete all layers, re-init, clear filters, reset tool to brush, reset color, clear text, rebuild the panel, and rebuild the script with all `started` flags cleared (rebuild creates new objects anyway).

Implementation: `restart(){ initLayers(); renderLayers(); resetFilters(); setTool('brush'); setColor('#ffd166'); buildScript(); idx=0; el=0; cursor fade in; }`

Let's be careful with `idx` and `el` as module-level vars.

Also, the demo should keep the cursor visible; the fade-out at the end then fade-in.

Now, writing `buildScript` — I'll write it as a function that returns the steps array, called at start and on each loop.

Careful: the targets (elements) are stable references since we don't rebuild the panel DOM except the layer list. But the layer rows get rebuilt! The eye button target must be re-queried at the time of the move (`getTarget` is a function called in onStart). So `() => centerOf(document.querySelector('#layerList .layer-row[data-i="1"] .eye'))`. That works since it's queried at runtime. 

For the blur slider etc., they're static elements.

Now let me write the code.

```js
// state
let tool='brush';
let color='#ffd166';
let brushSize=10;
let textValue='';
let textPos={x:380,y:120};
let shapeKind='ellipse';
```

setTool(t): update `tool`, update button active classes, update status.

Status bar update function `updateStatus()` called on changes and each frame for cursor position.

Status fields: `Tool: Brush | Layer: Paint | Size: 10px | Color swatch | Pos: x,y | FILTERS: ...

Let me build status as spans with ids.

Now writing render() and the main loop:

```js
let lastT=0, demoTime=0;
function loop(t){
  const dt = Math.min(50, t-lastT||16); lastT=t;
  updateDemo(dt);
  render();
  // cursor
  cursorEl.style.transform = `translate(${cursor.x}px,${cursor.y}px)`;
  // thumbs
  thumbAcc+=dt; if(thumbAcc>120){thumbAcc=0; updateThumbs();}
  updateStatusPos();
  requestAnimationFrame(loop);
}
```

Note the cursor element: `position:fixed; left:0; top:0; transform: translate(x,y)`. The arrow's hotspot is at top-left (0,0). Good, matches the click point.

Now `cv2vp`: canvas coords → viewport coords:
```js
function cv2vp(x,y){ const r=view.getBoundingClientRect(); return {x:r.left + x*r.width/W, y:r.top + y*r.height/H}; }
```

`vp2cv`: reverse.

Now write the demo step functions.

Let me write buildScript:

```js
function buildScript(){
  const S=[];
  const push=o=>S.push(o);
  const ease = p => p<0.5 ? 2*p*p : 1-Math.pow(-2*p+2,2)/2;

  const moveTo = (getT, dur) => push({
    dur,
    onStart(){ const t=getT(); this.sx=cursor.x; this.sy=cursor.y; this.tx=t.x; this.ty=t.y; },
    onUpdate(p){ const e=ease(p); cursor.x=this.sx+(this.tx-this.sx)*e; cursor.y=this.sy+(this.ty-this.sy)*e; }
  });

  const click = (getT, dur, fn) => {
    moveTo(getT, dur);
    push({dur:110, onStart(){ ripple(); }, onUpdate(){}});
    push({dur:0, onStart(){ fn&&fn(); }});
  };
  ...
}
```

Careful with `click`: after moveTo (dur), the click step, then the action step.

Targets:
```js
const T = {
  brush: () => centerOf(byTool('brush')),
  eraser: () => centerOf(byTool('eraser')),
  shape: () => centerOf(byTool('shape')),
  text: () => centerOf(byTool('text')),
  canvasPt: (x,y) => () => cv2vp(x,y),
  swatch: (i) => () => centerOf(swatchEls[i]),
  addLayer: () => centerOf(document.getElementById('btnAdd')),
  eye: (i) => () => centerOf(document.querySelector(`.layer-row[data-i="${i}"] .eye`)),
  layerRow: (i) => () => centerOf(document.querySelector(`.layer-row[data-i="${i}"] .lname`)),
  moveDown: () => centerOf(document.getElementById('btnDown')),
  slider: (id,v) => () => sliderPoint(document.getElementById(id), v),
};
```

Let me just define these inline for clarity.

Now the shape drag step:

```js
push({
  dur: 1200,
  onStart(){ previewActive=true; this.sx=560; this.sy=170; this.tx=660; this.ty=240; setActiveLayerByName('Paint'); },
  onUpdate(p){
    const e=ease(p);
    const x = this.sx+(this.tx-this.sx)*e;
    const y = this.sy+(this.ty-this.sy)*e;
    const v=cv2vp(x,y); cursor.x=v.x; cursor.y=v.y;
    pctx.clearRect(0,0,W,H);
    pctx.strokeStyle=color; pctx.lineWidth=3; pctx.globalAlpha=1;
    pctx.beginPath();
    pctx.ellipse((this.sx+x)/2,(this.sy+y)/2, Math.abs(x-this.sx)/2, Math.abs(y-this.sy)/2, 0,0,7);
    pctx.stroke();
  },
  onEnd(){ /* commit */ }
});
```
Hmm, but the ellipse grows from top-left to cursor. Fine.

Wait — the shape should be committed on mouse-up. In the demo, the commit happens at onEnd.

On end: draw previewC onto the active layer ctx, clear preview, previewActive=false.

But the shape is drawn on the Paint layer, which also has strokes. Fine.

Hmm, actually the shape at (560-660, 170-240) is in the sky near the sun. The sun is at (547, 212) with radius 34. So the ellipse would overlap the sun — nice, looks like a ring around the sun. Actually let's make it a bit bigger: from (480,140) to (640,280). Center (560,210) radius (80,70). Around the sun. 

Text typing step:

```js
push({
  dur: 2000,
  onStart(){ textValue=''; setActiveLayerByName('Text'); drawTextLayer(); },
  onUpdate(p){
    const full='GOLDEN HOUR';
    const n=Math.round(p*full.length);
    if(n!==textValue.length){ textValue=full.slice(0,n); drawTextLayer(); }
  }
});
```

Hmm, "GOLDEN HOUR" with letter spacing. drawTextLayer draws on the Text layer.

```js
function drawTextLayer(){
  const L = layers.find(l=>l.name==='Text');
  if(!L) return;
  const ctx=L.ctx;
  ctx.clearRect(0,0,W,H);
  if(!textValue) return;
  ctx.save();
  ctx.font='600 46px Georgia, "Times New Roman", serif';
  ctx.textAlign='center'; ctx.textBaseline='middle';
  ctx.shadowColor='rgba(0,0,0,0.55)'; ctx.shadowBlur=14; ctx.shadowOffsetY=3;
  ctx.fillStyle='#fff3d6';
  ctx.fillText(textValue, 380, 92);
  ctx.restore();
}
```
Wait, "letterspacing" isn't supported everywhere; fine without.

Hmm the text at y=92 in the sky. Good.

Stroke 3 on the Accents layer: sparkles in the sky.

```js
push({dur:1500, onStart(){ this.last=null; setActiveLayerByName('Accents'); },
  onUpdate(p){ const t=ease(p); const c={x: 120+t*600, y: 150 + Math.sin(t*Math.PI*6)*40}; ... }})
```
That paints a sine wave in the sky in light blue. Good.

Erase drag: same but with eraser tool on the Accents layer, erasing a horizontal line through the middle.

Actually the eraser tool erases the active layer (Accents), which is the sine wave. Good — visible partially.

Now filter drag helper:

```js
function dragFilter(id, from, to, dur){
  push({
    dur,
    onStart(){ this.el=document.getElementById(id); this.el.value=from; updateFilters(); },
    onUpdate(p){
      const v = from + (to-from)*ease(p);
      this.el.value = v;
      updateFilters();
      const r=this.el.getBoundingClientRect();
      const frac = (v - this.el.min)/(this.el.max-this.el.min);
      cursor.x = r.left + 9 + (r.width-18)*frac;
      cursor.y = r.top + r.height/2;
    },
    onEnd(){ this.el.classList.remove('flash'); }
  });
}
```
Hmm — `this.el.min` is a string; convert with Number().

Also add a `flash` class to the row while dragging for a visual cue.

Now `updateFilters()`:

```js
const F = {blur:0, brightness:100, contrast:100, sepia:0, invert:0};
function updateFilters(){
  F.blur = +document.getElementById('f-blur').value;
  ...
  const parts=[];
  if(F.blur) parts.push(`blur(${F.blur}px)`);
  if(F.brightness!==100) parts.push(`brightness(${F.brightness}%)`);
  ...
  view.style.filter = parts.join(' ') || 'none';
  // update value labels
}
```

Also update filter value labels.

Now `resetFilters()` sets all inputs to defaults and calls updateFilters.

Now the layer row click handlers and buttons.

Let me write `renderLayers()`:

```js
const layerList = document.getElementById('layerList');
let thumbRefs=[];
function renderLayers(){
  layerList.innerHTML='';
  thumbRefs=[];
  for(let i=layers.length-1;i>=0;i--){
    const L=layers[i];
    const row=document.createElement('div');
    row.className='layer-row'+(i===activeLayer?' selected':'');
    row.dataset.i=i;
    row.innerHTML=`
      <button class="eye${L.visible?' on':''}" title="Toggle visibility">${EYE_SVG}</button>
      <canvas class="thumb" width="56" height="34"></canvas>
      <div class="linfo">
        <div class="lname">${L.name}</div>
        <div class="lmeta">${L.blendLabel} · ${Math.round(L.opacity*100)}%</div>
      </div>`;
    const cv=row.querySelector('.thumb');
    thumbRefs.push({cv,layer:L});
    row.addEventListener('click', e=>{
      if(e.target.closest('.eye')) return;
      activeLayer=i; renderLayers(); syncLayerProps(); updateStatus();
    });
    row.querySelector('.eye').addEventListener('click', e=>{
      e.stopPropagation();
      L.visible=!L.visible; renderLayers(); updateStatus();
    });
    layerList.appendChild(row);
  }
  updateThumbs();
  syncLayerProps();
}
```

Careful: `activeLayer=i` captured with `let i` in the loop — fine since it's `let` in a for loop.

syncLayerProps updates the opacity slider and blend select to match the active layer.

```js
function syncLayerProps(){
  const L=layers[activeLayer]; if(!L) return;
  document.getElementById('opacity').value = Math.round(L.opacity*100);
  document.getElementById('opacityVal').textContent = Math.round(L.opacity*100)+'%';
  document.getElementById('blend').value = L.blend;
}
```

Wait, but the blend select values must match: 'source-over','multiply','screen','overlay','lighten','darken','difference'.

And the blend label: derive from the select's option text.

On opacity input: `L.opacity = v/100; syncProps; updateStatus;` — note this doesn't require renderLayers (which would lose focus), but the lmeta needs updating. I'll just update the lmeta text directly, or call renderLayers (which is a bit heavy on every input event but ok... it re-creates DOM on every slider move — could feel janky while dragging but works). Let's update just the label text:

```js
function updateLayerMeta(i){
  const row = layerList.querySelector(`.layer-row[data-i="${i}"]`);
  if(row) row.querySelector('.lmeta').textContent = `${layers[i].blendLabel} · ${Math.round(layers[i].opacity*100)}%`;
}
```

OK.

Now the tool buttons. HTML:

```html
<div class="tool" data-tool="brush" title="Brush (B)">svg</div>
<div class="tool" data-tool="eraser" title="Eraser (E)">svg</div>
<div class="tool" data-tool="shape" title="Shapes (U)">svg</div>
<div class="tool" data-tool="text" title="Text (T)">svg</div>
```

Then a color section:
```html
<div class="tsep"></div>
<div class="colorbox">
  <input id="colorInput" type="color" value="#ffd166">
</div>
<div class="swatches" id="swatches">
  <button data-c="#ffd166" style="background:#ffd166"></button>
  ...
</div>
```

Six swatches.

Swatch click → setColor(c).

setColor updates `color`, the colorInput value, and the active swatch highlight.

Now sizes: maybe add a size slider in the toolbar bottom? The status shows size. Let's add a small size slider in the toolbar for completeness. Eh, keep the toolbar as tools + color. Add size to the layer props panel? I'll add a "Brush size" slider under the filters or in the toolbar. Let's put it in the toolbar bottom, vertical space permitting.

Actually the toolbar is 56px wide and full height; tools take ~4*46=184px. Then color. Fine, no size slider — or put a small one. I'll skip it and keep brushSize fixed at 10 (the demo doesn't change it). Actually the status bar says "Size: 10px". Fine.

Hmm, but a real editor needs size. Let's add a compact size slider at the bottom of the left toolbar (rotated? no). I'll widen the left toolbar to 64px and put the slider horizontally at the bottom. Fine.

Actually let's keep it simple: skip the size control, or add it to the right panel under "Brush". I'll add a small row in the Filters panel? No. Skip.

Hmm, requirement says "a toolbar with brush, eraser, shapes and text, a colour picker, opacity and blend modes, and filters". Size isn't required. Good.

Now, canvas interactions for a real user (not required but nice): mouse events on the canvas for brush/eraser painting, shape drag, text placement. Let's implement basic pointer handlers so it actually works if someone touches it. It's a nice bonus, and the demo functions are separate.

Implement:
```js
view.addEventListener('pointerdown', e=>{ ... });
```
But the demo doesn't use these. It's fine.

Keep it reasonably simple:
- brush/eraser: pointerdown → start stroke, pointermove → draw, pointerup → end.
- shape: pointerdown start, move → preview, up → commit.
- text: pointerdown → set textPos and draw existing textValue.

OK.

Now let's write the CSS for the whole thing carefully.

I'll write the final code now, mentally checking.

One thing: the `previewC` must be cleared when switching tools or on commit.

Another: the render loop draws layers each frame; with 5 layers of 760x470 that's 5 drawImage per frame — fine.

Let me write out the landscape drawing.

```js
function drawLandscape(ctx){
  const horizon = H*0.62;
  // sky gradient
  const sky=ctx.createLinearGradient(0,0,0,horizon);
  sky.addColorStop(0,'#0a1230');
  sky.addColorStop(0.32,'#1d2f5c');
  sky.addColorStop(0.58,'#7a4a72');
  sky.addColorStop(0.78,'#e07a4e');
  sky.addColorStop(1,'#ffc978');
  ctx.fillStyle=sky; ctx.fillRect(0,0,W,horizon);

  // stars
  const rng=mulberry32(7);
  for(let i=0;i<70;i++){
    const x=rng()*W, y=rng()*horizon*0.5;
    const a=0.15+rng()*0.5;
    ctx.fillStyle=`rgba(255,255,255,${a*(1-y/(horizon*0.6))})`;
    ctx.fillRect(x,y,1.4,1.4);
  }

  // sun
  const sunX=W*0.72, sunY=horizon-72, sunR=36;
  ctx.save();
  ctx.shadowColor='rgba(255,190,110,0.9)'; ctx.shadowBlur=60;
  ctx.beginPath(); ctx.arc(sunX,sunY,sunR,0,Math.PI*2);
  ctx.fillStyle='#ffe9b0'; ctx.fill();
  ctx.restore();

  // mountain ridges
  ridge(ctx,mulberry32(3),horizon+6,190,'#4a4a6e',6);
  ridge(ctx,mulberry32(11),horizon+6,130,'#33355a',9);
  ridge(ctx,mulberry32(23),horizon+6,80,'#20223c',13);

  // water
  const wat=ctx.createLinearGradient(0,horizon,0,H);
  wat.addColorStop(0,'#e79a5b');
  wat.addColorStop(0.12,'#a5685a');
  wat.addColorStop(0.45,'#3b3355');
  wat.addColorStop(1,'#101426');
  ctx.fillStyle=wat; ctx.fillRect(0,horizon,W,H-horizon);

  // sun reflection
  ctx.save();
  ctx.globalCompositeOperation='lighter';
  for(let i=0;i<40;i++){
    const y=horizon+4+i*2.4;
    const w=(1-i/40)*90*(0.6+Math.random()*0.8);
    ...
  }
  ctx.restore();
```
Using Math.random inside makes it non-deterministic across resets; use a seeded rng.

Let's write reflection with rng2:
```js
const r2=mulberry32(99);
for(let i=0;i<44;i++){
  const y=horizon+2+i*2.6;
  const spread=18+i*1.6;
  const w=spread*(0.5+r2()*0.9);
  ctx.fillStyle=`rgba(255,214,150,${0.30*(1-i/44)})`;
  ctx.fillRect(sunX-w/2, y, w, 1.6);
}
```

Also add horizontal wave lines across the water.

Trees: pines at the shoreline.
```js
for(let i=0;i<16;i++){
  const x = 40+i*46 + (r2()-0.5)*20;
  const y = horizon+4;
  const s = 14+r2()*20;
  pine(ctx,x,y,s,'#141a2e');
}
```
16 trees across 760 → spacing 46. Good.

pine:
```js
function pine(ctx,x,y,s,col){
  ctx.fillStyle=col;
  ctx.beginPath();
  ctx.moveTo(x, y-s*2);
  ctx.lineTo(x-s*0.55, y);
  ctx.lineTo(x+s*0.55, y);
  ctx.closePath(); ctx.fill();
  // second tier
  ctx.beginPath();
  ctx.moveTo(x, y-s*1.3);
  ctx.lineTo(x-s*0.72, y-s*0.5);
  ctx.lineTo(x+s*0.72, y-s*0.5);
  ctx.closePath(); ctx.fill();
}
```
Hmm, ordering: draw the trunk? Keep it simple.

Wait, trees at the horizon line y=horizon+4 = 295 area, on the water edge. Their bases are at the shore. Fine.

Birds:
```js
ctx.strokeStyle='rgba(20,25,45,0.8)'; ctx.lineWidth=1.6;
for(let i=0;i<5;i++){ ... small arcs ... }
```

Draw 5 birds in the sky at around (150-350, 100-160).

Bird: two arcs.
```js
ctx.beginPath();
ctx.moveTo(x-6,y); ctx.quadraticCurveTo(x-3,y-4,x,y);
ctx.quadraticCurveTo(x+3,y-4,x+6,y);
ctx.stroke();
```

Good.

drawGlow:
```js
function drawGlow(ctx){
  const sunX=W*0.72, sunY=H*0.62-72;
  const g=ctx.createRadialGradient(sunX,sunY,10,sunX,sunY,240);
  g.addColorStop(0,'rgba(255,214,140,0.85)');
  g.addColorStop(0.35,'rgba(255,150,80,0.28)');
  g.addColorStop(0.7,'rgba(255,110,70,0.06)');
  g.addColorStop(1,'rgba(255,110,70,0)');
  ctx.fillStyle=g; ctx.fillRect(0,0,W,H);
}
```

With 'screen' blend, this brightens the sky around the sun. Nice.

Now, the layer order at init: Landscape, Sun Glow, Paint, Text. Glow above landscape with screen blend — good.

Now let me make sure the demo's stroke on the Paint layer is visible: color #ffd166 warm yellow on the water — visible.

Stroke 1 path: water highlights: `t => ({x: 80 + t*600, y: 330 + Math.sin(t*Math.PI*3.2)*16})`. That's below the horizon (291) so it's in the water. Good.

Stroke 2: after color change to #7fd8ff (light blue) — paint a long wave. Actually let's change the swatch color to something like #ff6b6b? On water, a bright cyan looks like foam. Let's use #8ee6ff.

Stroke 2 path: `t => ({x: 120+t*560, y: 390 + Math.sin(t*Math.PI*2.5)*22})`.

Stroke 3 (Accents layer, sparkles in the sky): color white-ish #ffffff with size maybe smaller. The brush size is global; set brushSize temporarily? I'll set brushSize=6 in that step's onStart and restore later. Actually the status bar shows size; changing it is fine. Let's set size 6 for stroke 3 and back to 10 for the erase.

Hmm, the eraser width should be larger, like 24. Set brushSize=24 for the erase step.

Fine — status bar updates live.

Now let me handle `setActiveLayerByName`:
```js
function setActiveLayerByName(name){ const i=layers.findIndex(l=>l.name===name); if(i>=0){ activeLayer=i; renderLayers(); } }
```
Note: renderLayers rebuilds DOM — called during the demo, fine.

But calling renderLayers on each stroke start also resets thumbRefs etc. Fine.

Now — careful — `renderLayers()` being called inside a step's onStart will rebuild the layer rows; the eye button target for a later step is re-queried at that step's start, so it's fine.

Now the status bar. Elements:
```html
<footer class="status">
  <span>TOOL <b id="stTool">Brush</b></span>
  <span>LAYER <b id="stLayer">Paint</b></span>
  <span>SIZE <b id="stSize">10 px</b></span>
  <span>COLOR <i id="stColor"></i></span>
  <span>POS <b id="stPos">—</b></span>
  <span class="grow"></span>
  <span id="stMsg">DEMO · automated walkthrough running</span>
</footer>
```

Now the demo badge in the topbar.

OK, writing the final code.

One more consideration: `updateDemo` runs even before the first render — fine.

Also, the cursor starts off-screen; the first step moves it in. Let's set the cursor initial position to the center of the stage and fade in with opacity 1.

Let's write:
```js
const cursor = {x: innerWidth*0.5, y: innerHeight*0.5};
```
And the first step moves it to the Brush tool.

Let me now write everything.

For `ripple()`:
```js
function ripple(){ cursorEl.classList.remove('click'); void cursorEl.offsetWidth; cursorEl.classList.add('click'); }
```

Now writing the final HTML.

Also add keyboard shortcuts? Not necessary.

Let me write the pointer interaction for real users:

```js
let drawing=false, lastPt=null, shapeStart=null;

view.addEventListener('pointerdown', e=>{
  const p=vp2cv(e.clientX,e.clientY);
  if(tool==='brush'||tool==='eraser'){
    drawing=true; lastPt=null; paintSeg(null,p); lastPt=p;
    view.setPointerCapture(e.pointerId);
  } else if(tool==='shape'){
    drawing=true; shapeStart=p; previewActive=true;
  } else if(tool==='text'){
    textPos=p; drawTextLayer();
  }
});
view.addEventListener('pointermove', e=>{
  const p=vp2cv(e.clientX,e.clientY);
  if(!drawing) return;
  if(tool==='brush'||tool==='eraser'){ paintSeg(lastPt,p); lastPt=p; }
  else if(tool==='shape'){ drawShapePreview(shapeStart,p); }
});
view.addEventListener('pointerup', e=>{
  if(!drawing) return;
  drawing=false;
  if(tool==='shape'){ commitPreview(); }
});
```

paintSeg uses the active layer.

Fine.

Now careful: `paintSeg` uses `tool` to decide erase mode. During the demo, tool is set appropriately. For stroke 3, tool is 'brush' (after the eraser step? no, stroke 3 happens before the eraser step — tool is 'brush' at that time since shape/text don't matter... wait, after the text tool, tool='text'. If we then paint stroke 3 with tool='text', paintSeg would use 'source-over' (since tool!=='eraser'), which is correct, but conceptually the tool should be brush. In the demo step for stroke 3, I'll call setTool('brush') in onStart. Good — also updates the UI.

Similarly for the shape drag step, setTool('shape') is already active from the earlier step.

And for the erase step, setTool('eraser') is active.

OK.

Now, painting during a stroke: `paintSeg(null, p)` on the first point draws a dot (moveTo(b.x-0.01) lineTo(b.x)). Fine.

Let me write the final code now. I'll be thorough.

One more: `updateStatus()` should show the active layer name, tool name, size, and color. And position updated each frame.

```js
function updateStatus(){
  stTool.textContent = TOOL_NAMES[tool];
  const L=layers[activeLayer];
  stLayer.textContent = L? L.name : '—';
  stSize.textContent = brushSize+' px';
  stColor.style.background = color;
}
```

Position updated in the loop:
```js
const cp = vp2cv(cursor.x, cursor.y);
stPos.textContent = `${Math.round(cp.x)}, ${Math.round(cp.y)}`;
```
Only if within canvas bounds.

Alright. Writing it all out now.

Also, the filter sliders should have labels and value readouts.

CSS for range inputs: style them minimally.

```css
input[type=range]{ -webkit-appearance:none; appearance:none; height:4px; background:#2c3138; border-radius:3px; outline:none; flex:1; }
input[type=range]::-webkit-slider-thumb{ -webkit-appearance:none; width:13px;height:13px;border-radius:50%;background:#8bbcff;border:2px solid #1a1d21; cursor:pointer; }
input[type=range]::-moz-range-thumb{...}
```

Also `.flash` for the slider row: add a background highlight.

Let me write the CSS for the filter row:
```css
.frow{display:flex;align-items:center;gap:8px;padding:4px 10px;border-radius:6px}
.frow label{width:64px;font-size:11px;color:#8b93a0;text-transform:uppercase;letter-spacing:.5px}
.frow .val{width:34px;text-align:right;font-size:11px;color:#6f7a87;font-variant-numeric:tabular-nums}
.frow.flash{background:#232a36}
```

Also `input[type=color]` styling: small.

Let's write it all.

Final check on the demo loop restart: at the end, call `restart()`. Set idx=0 and el=0, plus a flag so the current frame doesn't double-run.

```js
function updateDemo(dt){
  if(idx>=script.length){ restartDemo(); return; }
  ...
}
```
restartDemo rebuilds `script` and sets idx=0, el=0. Then next frame it starts from the beginning.

Careful: `script` is reassigned, so the runner must read the global `script`.

Now the end-of-demo step: fade the cursor out, then reset. Let's add:
```js
push({dur:600, onStart(){ cursorEl.style.opacity='0'; }, onUpdate(){}});
push({dur:0, onStart(){ restartDemo(); }});
push({dur:800, onStart(){ resetDoc(); cursorEl.style.opacity='1'; }, onUpdate(){}});
```
Hmm, restartDemo would loop back into the script. Let's structure:

At the end of the script:
- step: fade cursor out over 500ms
- step: resetDoc() (instant) — clears everything
- step: fade cursor in over 500ms while moving to the center
- then the script ends → restartDemo() rebuilds and restarts.

That works: when the script ends, restartDemo rebuilds the script with new step objects (started flags cleared) and idx=0.

So:
```js
push({dur:500, onStart(){}, onUpdate(p){ cursorEl.style.opacity = String(1-p); }});
push({dur:0, onStart(){ resetDoc(); cursor.x=innerWidth/2; cursor.y=innerHeight/2; }});
push({dur:600, onUpdate(p){ cursorEl.style.opacity=String(p); }});
```

And restartDemo(): `script = buildScript(); idx=0; el=0;`

But buildScript uses closures over `cursor` etc. — fine.

Note: buildScript must be called once initially.

resetDoc(): initLayers(); renderLayers(); resetFilters(); setTool('brush'); setColor('#ffd166'); brushSize=10; textValue=''; previewActive=false; pctx.clearRect(...); updateStatus();

Good.

Now writing it out for real.

For the "Add Layer" button handler:
```js
btnAdd.onclick = ()=>{
  const L=addLayer('Layer '+(++layerCounter));
  activeLayer=layers.length-1;
  renderLayers(); updateStatus();
};
```
For the demo, the added layer is named 'Accents' so the demo can find it by name. But a user clicking would get 'Layer 5'. For the demo I'll call addLayer('Accents') directly. But then setActiveLayerByName('Accents') works.

Hmm, but if the user clicks Add during the demo... whatever. Actually the demo clicks the Add button visually but calls the function directly with the name 'Accents'. Let me make the demo's click handler call a function `addLayerNamed('Accents')`. Fine.

Hmm, but consistency: after reset, the layer counter resets.

Let me name it 'Accents' and for user clicks use `'Layer ' + (layers.length+1)`.

OK writing.

Also the delete button — implement quickly.

Let me write the complete file.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>PixelForge — Mini Image Editor</title>
<style>
/* ... */
</style>
</head>
<body>
...
<script>
/* ... */
</script>
</body>
</html>
```

Let me write the SVG icons.

Brush:
```html
<svg viewBox="0 0 24 24"><path d="M4.5 19.5c0-2 1.2-3.2 2.8-3.2 1.3 0 2.2.9 2.2 2.2 0 1.6-1.6 2.5-5 3z" fill="currentColor" stroke="none"/><path d="M9.8 15.2 19 6l-1.8-1.8-9.2 9.2z"/></svg>
```
Hmm the second path is a thin brush handle. Let me just do:
```html
<path d="M4 20c0-1.9 1-3 2.5-3s2.3.9 2.3 2.1C8.8 20.7 6.5 21 4 20z" fill="currentColor" stroke="none"/>
<path d="M9.5 15.8 19.5 5.8a1.4 1.4 0 0 1 2 2L11.5 17.8z" />
```
Hmm, the second path with fill none and stroke looks like a thin blade. OK.

Actually simpler: a diagonal line with a thick end:
```html
<path d="M8.5 15.5 20 4"/>
<path d="M4 20c0-2 1.2-3.2 2.8-3.2L9 19c0 1.6-1.6 3-5 3z" fill="currentColor" stroke="none"/>
```
Hmm, the geometry is off but it reads as a brush. Let me make it a bristle triangle:
```html
<path d="M3.5 20.5c0-2.5 1.5-4 3.5-4 1.4 0 2.5 1.1 2.5 2.5 0 2-2 3-6 3z" fill="currentColor" stroke="none"/>
<path d="M9.5 15.5 20 5"/>
<path d="M16 3.5 20.5 8" />
```
Eh, the last two lines form a handle. Fine. Actually just `M9.5 15.5 20 5` alone is enough, plus maybe a second parallel line. Let's keep it minimal — it'll look like a brush.

Eraser:
```html
<path d="M4 16.5 10.5 10l6.5 6.5-4 4H8z"/>
<path d="M3 20.5h18"/>
```
Hmm, path 1: M4 16.5 → L10.5 10 → L17 16.5 → L13 20.5 → H8 → Z back to (4,16.5). Wait, "H8" from (13,20.5) goes to (8,20.5), then Z closes to (4,16.5). Yes, that's a nice eraser shape. Good.

Shapes:
```html
<rect x="3" y="9" width="11" height="11" rx="1.5"/>
<circle cx="16" cy="8" r="5.5"/>
```

Text:
```html
<path d="M5 6.5V4.5h14v2"/><path d="M12 4.5v15"/><path d="M8.5 19.5h7"/>
```

Eye:
```html
<path d="M2 12s3.6-6 10-6 10 6 10 6-3.6 6-10 6-10-6-10-6z"/><circle cx="12" cy="12" r="2.6"/>
```

Plus/minus/up/down for buttons:
- Add: `<path d="M12 5v14M5 12h14"/>`
- Del: `<path d="M5 12h14"/>` or a trash can. Use `<path d="M4 7h16M9 7V5h6v2M6 7l1 13h10l1-13"/>`.
- Up: `<path d="M12 19V5M6 11l6-6 6 6"/>`
- Down: `<path d="M12 5v14M6 13l6 6 6-6"/>`

Fine.

Now writing everything out. Let me produce the final code.

Regarding `sliderPoint`:
```js
function sliderPoint(el, v){
  const r = el.getBoundingClientRect();
  const min=+el.min, max=+el.max;
  const frac = (v-min)/(max-min);
  return {x: r.left + 10 + (r.width-20)*frac, y: r.top + r.height/2};
}
```

OK. Writing the final answer now.

One thing about `render()` being called each frame with `previewActive` — include it.

Also, the demo's `dragFilter` needs to set the value and update the labels. `updateFilters()` reads all inputs and updates the labels.

Let me write `updateFilters`:
```js
const filterDefs = [
  {id:'f-blur', key:'blur', unit:'px', def:0},
  {id:'f-brightness', key:'brightness', unit:'%', def:100},
  {id:'f-contrast', key:'contrast', unit:'%', def:100},
  {id:'f-sepia', key:'sepia', unit:'%', def:0},
  {id:'f-invert', key:'invert', unit:'%', def:0},
];
function updateFilters(){
  const parts=[];
  for(const d of filterDefs){
    const el=document.getElementById(d.id);
    const v=+el.value;
    document.getElementById('v-'+d.id.slice(2)).textContent = (d.unit==='px'? v.toFixed(0): Math.round(v)) + (d.unit==='%'?'%':'');
    if(v!==d.def){
      parts.push(`${d.key}(${v}${d.unit})`);
    }
  }
  view.style.filter = parts.length? parts.join(' ') : 'none';
}
```
Blur unit px, others %.

Value display id: for 'f-blur' → 'v-blur'. Good with slice(2).

Now writing it all out.

Let me double check the CSS filter on the canvas doesn't kill performance with blur — it's fine for a demo.

Let me write the final file.

Also I should double-check: drawImage of a canvas onto the main canvas each frame is fine.

Let me now think about the initial layout height. `.app` height 100vh, topbar 44, status 26, body flex 1. Canvas area gets the rest. On a 900px tall viewport, body ≈ 830px, canvas centered with max-height 100%. Good.

Writing.

For the layer thumbnails, I want them to look nice: dark background, and the image scaled. `ctx.drawImage(layer.canvas, 0,0,56,34)`.

Also for hidden layers, dim the thumbnail.

OK, final code:

I'll write it now in full, carefully.

```js
// ===== helpers =====
const $ = id => document.getElementById(id);
function mulberry32(a){ return function(){ a|=0; a=a+0x6D2B79F5|0; let t=Math.imul(a^a>>>15,1|a); t=t+Math.imul(t^t>>>7,61|t)^t; return ((t^t>>>14)>>>0)/4294967296; }; }
```

Then everything else.

Let me write the whole script in order:

1. Constants & elements
2. PRNG
3. Layer model & init
4. Landscape drawing
5. Rendering
6. UI building (layers panel, tools, filters)
7. Status
8. Demo script
9. Animation loop
10. Pointer interactions

Let me write it.

Note about `paintSeg` requiring `activeLayer` — during the demo I set the active layer via setActiveLayerByName which calls renderLayers. Good.

Writing the final code now.

One more detail: when the demo paints, the cursor position must also update `lastPt`. Handled in the step.

Also the demo's stroke step: `onUpdate(p)` uses `ease(p)`; but `getPath` is defined over t∈[0,1].

Final check on the shape preview commit: 

```js
function commitPreview(){
  if(!previewActive) return;
  const L=layers[activeLayer];
  L.ctx.drawImage(previewC,0,0);
  pctx.clearRect(0,0,W,H);
  previewActive=false;
}
```

But the preview canvas was drawn with strokeStyle=color and lineWidth=3. Fine.

Alright, write it.

Also, I should ensure that during the demo the shape preview is drawn on the preview canvas AND the ellipse grows from the start point. Yes.

Let me write out everything now — final answer.

Wait, one thing: in `render()`, the preview canvas is drawn on top of everything, ignoring layer order. Acceptable.

Also during the demo, after committing the shape, previewActive=false.

Let me write the code.

Final: make sure `updateDemo` is called with dt in ms and the script durations are in ms. Yes.

Writing now.