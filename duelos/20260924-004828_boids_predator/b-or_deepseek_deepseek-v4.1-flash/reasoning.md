Let me create a self-contained HTML file with a flocking simulation.

Key requirements:
- Full-window canvas
- At least 2000 boids
- Separation, alignment, cohesion
- 1-2 predators
- Flash-expansion effect
- Trails / motion blur
- Gradient background (deep sea or dusk)
- Lighting so swarm reads as single organism
- Small label with number of individuals
- Spatial grid for performance
- No interaction, runs from first second
- One HTML file, inline CSS/JS, no external resources

Let me think about implementation.

Performance: 2000 boids with spatial grid. Canvas 2D. Using fillRect for each boid might be OK but 2000 fillRect per frame plus trails... Better: use a single path with rects, or draw to an offscreen canvas and composite. Actually a common trick: draw boids as small rectangles into a path then fill once. Or use ImageData for speed.

Approach for performance and beauty:
- Main canvas with gradient background drawn once per frame (or use a persistent canvas with fade overlay for trails).
- Trails: instead of clearing, draw a semi-transparent background gradient rect each frame. That gives motion blur. But gradient background needs to be deep sea. I can draw a radial gradient with alpha each frame — that fades previous frame. Actually to keep the gradient background visible, draw the gradient with alpha ~0.15 each frame over the previous content. That fades the trails toward the background gradient color. That works nicely.

Hmm, but the gradient drawn with globalAlpha 0.15 repeatedly accumulates, converging to the gradient. Good.

- Boids: draw as small ellipses/rects. For "lighting so the swarm reads as a single organism", use additive blending ('lighter') with color based on... maybe density or speed. A nice trick: render boid glow into a low-res offscreen canvas, then blur it and composite with 'lighter' to give a bloom. But blurring per frame in JS is expensive. Could use canvas filter: 'blur(8px)' — supported in most browsers, might be slow but at low res it's fine.

Alternative simpler bloom: draw each boid as a small radial-gradient-free dot: draw into a low-res canvas (e.g., 1/4 resolution) with 'lighter', then draw that scaled up with globalAlpha and filter blur. Hmm.

Let me design:

Layer 1 (main visible canvas): 
- fade with gradient (alpha ~0.12)
- draw boids with 'lighter' composite as small dots with color depending on local density/speed → gives bright core.

Bloom: create a low-res canvas at 1/4 scale. Draw boids there as slightly larger dots with 'lighter'. Then on main canvas, drawImage(bloomCanvas, scaled up) with globalAlpha 0.5 and composite 'lighter'. Scaling up a small canvas with smoothing gives a natural blur. That's cheap-ish: one drawImage. And drawing 2000 dots on a 1/4 res canvas is fast.

Actually drawing 2000 dots twice is 4000 draw ops. That's probably fine at 60fps? Each fillRect is cheap-ish. Let's use fillRect for tiny squares on low-res, and arcs on... hmm arcs are slower. Use fillRect for both. At 1/4 res, a boid of size 1.5px radius → 3px rect.

Actually let's think about total: 2000 boids × 2 draws = 4000 fillRect per frame. Modern browsers handle ~10k fillRect fine at 60fps. Should be OK.

Better: batch into a single path per color? Colors vary per boid. Could quantize color into a few buckets (e.g., 4 buckets) and batch each bucket into one path with rects, then fill. That reduces to ~8 fill calls. Let's do that: compute color index from density/speed, add rect to path[bucket], then fill each path once. Path with 2000 rects — fine.

Hmm, but for 'lighter' compositing with paths it's the same.

Let's do: buckets = 5 colors. For each boid, ctx.fillStyle changes are the expensive part. Batching paths avoids style changes. Good.

Spatial grid: cell size ~ perception radius (e.g., 24px). Use typed arrays. Grid built each frame with counts and indices — standard approach:

- cols = ceil(w/cell), rows = ceil(h/cell)
- cellCount = Int32Array(cols*rows)
- Count pass, prefix sum, then fill boidIndices Int32Array.

Then for each boid, iterate 3x3 cells.

Perception radius: separation ~12, alignment/cohesion ~30. Use cell size = 30 for neighbor query, and separation handled within same query with smaller radius check. Fine.

2000 boids × 9 cells × ~avg boids per cell. With 2000 boids over say 1600×900 = 1.44M px, cell 30px → 48×30 = 1440 cells, ~1.4 boids/cell average. But flocking concentrates them, so cells in the flock could have many. Average neighbor checks maybe 30-60. 2000 × 50 = 100k distance checks per frame. Fine.

Predators: 2 predators. They steer toward the centroid of nearby boids (or nearest boid). Boids flee from predators within a radius (e.g., 120px) with strong force → flash expansion.

Predator rendering: larger, distinct color (e.g., warm orange/red against a cool blue swarm). Draw a triangle/arrow shape with a glow.

Also a "flash-expansion" — when predator is near, boids flee hard, creating a hole. Then they reform behind it (cohesion pulls them back).

To make it more dramatic, maybe also add a slight "flash" of brightness when the swarm bursts — boids near the predator turn brighter/whiter.

Background: deep sea gradient — dark navy at bottom to teal-ish at top, with a subtle radial vignette / light shafts. Let me do a vertical linear gradient from #04121f to #0a2b3d... plus a radial light from top.

Hmm, for the fade-overlay approach the gradient must be drawn with alpha. So:
```
ctx.globalCompositeOperation = 'source-over';
ctx.globalAlpha = 0.14;
ctx.fillStyle = bgGradient; // cached gradient object
ctx.fillRect(0,0,w,h);
ctx.globalAlpha = 1;
```
This fades trails. But repeated alpha compositing converges to the gradient — good. However the trail persists for a while; with alpha 0.14, trail decay time ~ 1/0.14 ≈ 7 frames. Reasonable motion blur. Maybe use 0.2 for shorter trails so it's not too smeary. Let's use ~0.18.

Hmm, one issue: with 'lighter' compositing on top of a faded background, brightness accumulates. Should be fine with small alpha values.

Also, add caustic light shafts? Could be static drawn into the fade. Might complicate. Let's add subtle vignette drawn with alpha as part of the fade — but the gradient object can include multiple stops.

Actually to get a nicer background, I'll build the background gradient as a linear gradient with several stops, and add a radial "sun" glow drawn with low alpha each frame in the fade step. Keep it simple: linear gradient + radial highlight.

Let me just use one cached canvas-size gradient (linear vertical) for the fade. Plus optionally draw radial glow with alpha*0.5. Fine.

Boid colors: deep sea → cyan/teal/white. Base color by speed: slow = deep blue, fast = bright cyan/white. Near-predator = white/amber flash.

Let's do color buckets:
- bucket 0: '#1f6f8b' dim
- bucket 1: '#3fb8c9'
- bucket 2: '#8fe8f0'
- bucket 3: '#e8fbff'
- bucket 4: '#ffd9a0' (panic/warm) — maybe not; keep it cool but bright. Actually a slight warm flash could look nice. Let's keep the flash white-cyan.

Compute brightness t = clamp(speed mapped) plus panic factor. Then pick bucket.

Boid size ~1.6-2.2 px radius → rect of 2-3 px. On low-res canvas at 0.5 scale... hmm.

Let me reconsider the bloom approach:
- bloomCanvas at scale 0.25 of main size. Draw each boid as a rect of size ~ (boidSize*2*0.25) ≈ 1-2 px. That's tiny; when upscaled it becomes a soft blob. Good for glow.
- Main canvas: draw boids as small rects (2-3px) crisp.

Actually maybe simpler and prettier: draw ONLY on the low-res canvas... no, main needs crisp dots.

Alternative: draw crisp dots on main canvas with 'lighter', then draw the bloom canvas scaled up with 'lighter' at alpha 0.6 with imageSmoothingEnabled=true. That gives glow.

Let's do it. The bloom canvas needs clearing each frame (clearRect) — 1/16 the pixels, cheap.

Hmm, but the bloom canvas draws with 'lighter' too, accumulating within the same frame — fine, that's the point.

Let me size: main canvas = window size (devicePixelRatio capped at 1.5 maybe for perf). Actually with 2000 boids and DPR, let's cap DPR at 1 for perf, or use 1.25. I'll cap at 1.5 but honestly 1 is safer for perf. Let's use `Math.min(devicePixelRatio, 1.5)`. Hmm, 2000 boids on a 4K canvas... The boid drawing is the same count regardless of resolution. The fill cost scales with area covered which is tiny. So DPR is fine. Use min(dpr, 2). Let's use 1.5 to be safe.

Actually, trails with alpha compositing: higher resolution = same cost roughly. OK.

Now the physics.

Boid:
- position px, py
- velocity vx, vy
- speed limits: min 1.2, max 3.2 (px/frame at 60fps) — need to think about scale. Let's use a time-step normalized: dt in units of 1/60s, clamped.

Let's set maxSpeed = 2.6, minSpeed = 1.4 (px per frame at 60fps). With 2000 boids in a 1600×900 area, that's a reasonable pace.

Forces:
- separation: radius 14, weight 1.6
- alignment: radius 34, weight 0.9
- cohesion: radius 34, weight 0.7
- predator flee: radius 130, weight 4.0 (strong)
- boundary: steer away from edges within 120px margin
- Also a gentle "wander" / noise to keep it alive.

Predator behavior:
- seeks nearest boid cluster: find nearest boid within some range, or steer toward local centroid.
- maxSpeed ~ 4.2, slightly faster than boids so it can catch up but not too fast.
- Turn rate limited.
- 2 predators, one roams.

For a nice "burst and reform behind it" effect, the predator should move through the flock. Boids flee radially → hole forms → swarm splits → predator passes → cohesion reforms.

Predator targeting: pick a target boid and chase. Re-pick when too close or every N frames. To make it look natural, target = centroid of boids within radius R (say 250) weighted... Or simply: find nearest boid using the grid (query cells within radius). Simpler: keep a target index; each frame, steer toward it; if distance < 20 or target too far, pick a new random boid from a random sample. Actually steering toward the local centroid of nearby boids is smoother. Let's do: accumulate centroid of boids within 300px (sampled), steer toward it; if none, wander toward center.

But grid query for predator with radius 300 = 10 cells radius → 21×21 cells = 441 cells. That's fine for 2 predators.

Actually simpler: maintain global centroid of flock and have predators steer toward a point that's the centroid of boids within a large radius using the grid. Let's just do the grid query with cell radius = ceil(300/cell).

Hmm, that's 441 cells × 2 = 882 cell lookups, each maybe 1-5 boids → few thousand ops. Fine.

Let me now write the code.

```js
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d', { alpha: false });
```

Wait — with alpha:false the canvas is opaque black initially. We fill gradient each frame anyway. Fine.

Bloom canvas:
```js
const bc = document.createElement('canvas');
const bx = bc.getContext('2d');
```
with alpha true, cleared each frame.

Resize handling: on resize, resize canvas and bloom canvas, rebuild gradients.

Boid data in typed arrays for perf:
```js
const N = 2200;
const px = new Float32Array(N), py = new Float32Array(N), vx = ..., vy = ...;
```

Actually objects are fine too but typed arrays are faster. Let's use typed arrays.

Grid:
```js
let cols, rows, cellSize;
let cellCount, cellStart, items; // Int32Array
```

Build:
```js
function buildGrid(){
  cellCount.fill(0);
  for (i...) { ci = cx + cy*cols; cellCount[ci]++; }
  // prefix
  cellStart[0]=0; for c: cellStart[c+1] = cellStart[c]+cellCount[c];
  // fill using a cursor copy
}
```
Need cellStart of length cols*rows+1.

Let me use a simpler approach: counts array + starts array + cursor array.

```js
const nCells = cols*rows;
counts = new Int32Array(nCells);
starts = new Int32Array(nCells+1);
cursor = new Int32Array(nCells);
items = new Int32Array(N);
```

Build:
```js
counts.fill(0);
for (let i=0;i<N;i++){
  let gx = (px[i]*invCell)|0; if(gx<0)gx=0; else if(gx>=cols)gx=cols-1;
  ...
  counts[gx + gy*cols]++;
}
let s=0;
for(let c=0;c<nCells;c++){ starts[c]=s; cursor[c]=s; s+=counts[c]; }
starts[nCells]=s;
for (let i=0;i<N;i++){ ... items[cursor[cell]++] = i; }
```

Then neighbor iteration for boid i: gx, gy; loop dy -1..1, dx -1..1, get cell, loop items.

Perception radius r2 = 34^2 = 1156. Cell size 34 → cells are 34px, so a 3x3 neighborhood covers 102px wide, which is > 2*34. Good, covers the full radius. Actually need cellSize >= perceptionRadius so 3x3 covers. Yes, cellSize = 34 works with perception radius 34? The boid could be at the corner of its cell; a neighbor at distance 34 could be up to 34+34=68 away in one axis... no wait. 3x3 cells span from the left edge of the left cell to the right edge of the right cell = 3*34 = 102. The boid is somewhere in the middle cell. Worst case, the boid is at the left edge of the middle cell, so it can reach 2*34=68 to the left. Since radius is 34 ≤ 68, all neighbors within 34 are within the 3x3 block. Yes, correct — 3x3 with cellSize >= r covers everything within r. Good.

Set cellSize = 34 (or 36).

For separation radius 14, it's covered.

Now let's compute forces.

```js
for (let i=0;i<N;i++){
  let x=px[i], y=py[i];
  let gx = ..., gy = ...;
  let sepX=0, sepY=0, aliX=0, aliY=0, cohX=0, cohY=0, count=0;
  let fleeX=0, fleeY=0;
  for cells...
    for each j:
      if (j===i) continue;
      dx = px[j]-x; dy = py[j]-y;
      d2 = dx*dx+dy*dy;
      if (d2 > R2 || d2 === 0) continue;
      d = sqrt(d2);
      // separation
      if (d < SEP_R) { const w = (SEP_R - d)/d... } 
```
Hmm, standard: separation force = -(dx/d) * (1 - d/sepR) / d ... Let's do: strength = (1/d - 1/sepR), force += -dx*strength... Actually classic: sep += (dx/d) * (sepR - d)/sepR → pushes away with magnitude proportional to closeness.

Let's use: `const inv = 1/d; const s = (sepR - d) * inv; sepX -= dx*inv*s; sepY -= dy*inv*s;` Hmm that gives magnitude (sepR-d)/d which blows up. Let's just do `sepX -= dx/d * (1 - d/sepR)`. Magnitude in [0,1]. Good.

Alignment: aliX += vx[j], aliY += vy[j]; count++.
Cohesion: cohX += px[j], cohY += py[j].

Then normalize.

Since we're doing sqrt per neighbor, that's ~100k sqrts per frame. Fine.

Actually we can avoid sqrt for alignment/cohesion (they're within R2 which we already have). Only separation needs d. Fine, keep sqrt only when d < sepR.

Let's restructure:
```js
if (d2 < R2) {
  count++;
  aliX += vx[j]; aliY += vy[j];
  cohX += px[j]; cohY += py[j];
  if (d2 < SEP2) {
    const d = Math.sqrt(d2) || 0.0001;
    const f = (1 - d/SEPR)/d; // ...
  }
}
```
Hmm, `(1 - d/sepR)/d` — at d=14 → 0, at d=0.1 → ~10/0.1... wait (1-0.007)/0.1 = 9.9. That's large but it's a force that gets normalized-ish later. Let's use `sepX -= (dx/d) * (1 - d/sepR)` which is bounded [0,1]. Then scale by weight. Good, bounded and stable.

Predator flee: for each predator p within FLEE_R (140):
```js
dx = x - ppx; dy = y - ppy; d = hypot;
f = (1 - d/FLEE_R); 
fleeX += (dx/d) * f * f * 3;  // quadratic for sharper near-field
```
Also add tangential component so the swarm "swirls" around the predator rather than just pure radial? Real shoals do a flash expansion radially. Keep radial but add a bit of tangential for beauty. Hmm, pure radial is more dramatic. Let's do mostly radial with slight tangential.

Actually a nice touch: when fleeing, boids also get a boost in max speed (panic speed). Let's allow speed limit to increase when fleeing.

Now forces application:
```js
ax = sepX*WSEP + aliX*WALI + cohX*WCOH + fleeX*WFLEE + boundary + wander
vx += ax*dt; vy += ay*dt;
```

Then clamp speed to [minSpeed, maxSpeed*(1+panic)].

Hmm, with dt normalization: use fixed dt = 1 (per frame at 60fps) and scale forces accordingly. Simpler. But on high-refresh monitors (120Hz), things run 2x fast. Let's do proper dt: `const dt = Math.min(delta/16.667, 2)`. And design forces per 60fps frame. Multiply accelerations by dt.

Actually for stability with dt scaling and clamped delta, fine.

Let's now think about the "flash expansion". Predator approaches → boids within 140px flee hard. With 2000 boids and a 140px radius, that's a lot of boids. Good.

Also the visual: boids near the predator get brighter (panic → white). That makes the burst read as a flash. 

Let's compute panic per boid: `panic = clamp(1 - d/FLEE_R)` max over predators. Use it for brightness and speed.

Now rendering with color buckets. Let's compute for each boid:
```js
sp = speed; t = (sp - MIN)/(MAX-MIN) clamped 0..1
bright = 0.35 + 0.65*t  // faster = brighter
bright = min(1, bright + panic*0.9)
```
Bucket = floor(bright*5) clamped.

Colors (deep sea bioluminescence):
0: 'rgba(30,90,140,0.55)'  — dim blue
1: 'rgba(60,160,200,0.7)'
2: 'rgba(110,220,235,0.85)'
3: 'rgba(190,250,255,0.95)'
4: 'rgba(255,255,255,1)'

With 'lighter' compositing, overlapping boids accumulate → the dense core of the flock glows. 

For the main canvas, draw small rects of size ~1.8px. Hmm, at DPR 1.5, we work in device pixels. Let's set the transform to scale by dpr so we can use CSS pixels in logic. Then boid rect = 2 CSS px → 3 device px. OK.

Actually using ctx.setTransform(dpr,0,0,dpr,0,0) makes all drawing in CSS px. Good.

Boid dot: use fillRect(x - s/2, y - s/2, s, s) with s ≈ 1.8-2.4 depending on speed. Let's vary size slightly: bigger when panicked.

Hmm, rects look blocky. With motion blur it's fine, reads as a dot. Alternatively use a pre-rendered sprite (small radial gradient) drawn with drawImage — 2000 drawImage calls with a tiny sprite is quite fast actually and looks much better. Let's consider: creating a 16×16 sprite canvas with a radial gradient, then drawImage(sprite, x-8, y-8, 16,16). 2000 drawImage calls per frame — that's typically ~2-4ms. Acceptable. And it looks way better (soft glowing dots).

But then color variation requires tinting. Could pre-render 5 sprites (one per bucket) with different colors. Then drawImage for each. That's great — 2000 drawImage calls with 5 different source canvases.

drawImage of a small canvas 2000 times... Let me estimate: modern browsers do maybe 10-50k small drawImage per frame at 60fps. Should be OK.

Hmm, but combined with the bloom pass, that's 4000 drawImage. Might be 6-8ms. Risky but probably OK. Alternatively use fillRect for the bloom (low-res, tiny) and drawImage for the main. Let's do: main canvas uses sprites (drawImage), bloom canvas uses fillRect (cheap, low-res).

Actually, let me reconsider: maybe just use fillRect everywhere with a soft glow achieved by the bloom layer. The crisp dots + the bloom glow could look great. Rects at 2px with motion blur... they'd look like little squares. Hmm, at 2px size, a square vs a circle is nearly indistinguishable, especially with blur. I'll go with sprites for main — better quality — but let's make the sprite 12×12 and scale to ~4-6 px on screen. Hmm, drawImage with downscaling from 12 to 5 is fine.

Actually simpler: pre-render sprite at exactly the size used, e.g., 8×8 device px... but DPR scaling. Let's just pre-render at 16×16 and draw at 6×6 CSS px (which is 9 device px at dpr 1.5). Slight downscale, smooth. Fine.

Hmm, wait. Let me reconsider the visual scale. With 2000 boids, if each is 6px, the flock covers a lot. Let's make them ~4px glow dots with a 1.5px bright core. The sprite: radial gradient from white-ish center to transparent at radius 8 (in a 16px sprite). Drawn at 8px CSS → the visible bright part is ~3px. Good.

OK let's go.

Sprite creation:
```js
function makeSprite(r,g,b){
  const s = 16;
  const c = document.createElement('canvas'); c.width=c.height=s;
  const g2 = c.getContext('2d');
  const grd = g2.createRadialGradient(s/2,s/2,0,s/2,s/2,s/2);
  grd.addColorStop(0, `rgba(${r},${g},${b},1)`);
  grd.addColorStop(0.25, `rgba(${r},${g},${b},0.55)`);
  grd.addColorStop(0.6, `rgba(${r},${g},${b},0.12)`);
  grd.addColorStop(1, `rgba(${r},${g},${b},0)`);
  g2.fillStyle = grd; g2.fillRect(0,0,s,s);
  return c;
}
```

Then `ctx.globalCompositeOperation='lighter'` and drawImage(sprite, x-4, y-4, 8, 8).

Colors per bucket:
0: [40,110,160]
1: [70,180,215]
2: [120,235,245]
3: [200,250,255]
4: [255,255,255]

With 'lighter', dense areas saturate to white — exactly the "single organism" look.

Bloom layer: draw the same sprites into the low-res canvas scaled? Or just fillRect. Let's draw the sprites into the bloom canvas too but at low res... Actually simplest: bloom canvas at 0.25 scale, draw sprite at 8*0.25=2px. Then upscale with drawImage to full size and smoothing → blur. Cost: 2000 more drawImage of a 16px sprite into a 2px target. Downscaling 16→2 is fine.

Hmm, 4000 drawImages. Let's just try. Actually, maybe I skip the separate bloom canvas and instead rely on drawing the sprites twice: once at large size with low alpha (halo) and once small bright. That's also 4000 draws. Same cost but no extra canvas resize/upscale.

I think the low-res bloom is better because it produces a genuine blur. Let's do it.

Actually, an even cheaper approach: draw everything into the low-res canvas only for bloom, and draw the crisp sprites on main. Both needed.

Hmm. Let me reconsider once more. Alternative: skip crisp layer, draw only on the low-res canvas (0.5 scale), then upscale the whole thing to the main canvas. At 0.5 scale with smoothing, boids are soft blobs. With motion blur trails, this looks like a soft glowing cloud. That's 2000 draws total. And upscaling 0.5 → 1.0 is cheap.

But then the trails need to be on the low-res canvas, and upscaling each frame means the trail resolution is halved. That's fine actually — it's a blurry glowing cloud anyway.

Hmm, but 0.5 scale upscaled looks noticeably soft/pixelated on text. The label is drawn on the main canvas separately (DOM element, so no problem).

Let me go with: everything rendered at a render scale of 0.75? Hmm.

Decision: Use a single offscreen canvas at scale S = 1 (full res) for the scene? No...

OK, final decision, keep it simple and robust:

- Main canvas at DPR capped to 1.5, but all logic in CSS px via transform.
- Trails: fade with gradient on main canvas.
- Boids: drawn on main canvas via sprites with 'lighter'.
- Bloom: separate canvas at 0.3 scale; boids drawn there as tiny rects with 'lighter'; then main draws it upscaled with 'lighter' and alpha ~0.55. The upscale with smoothing gives a nice blur.

Cost: 2000 sprite draws + 2000 tiny fillRects + 1 upscale drawImage. Should be fine.

Hmm, actually the tiny fillRects at 0.3 scale — a boid at 4px CSS → 1.2px rect. Rects smaller than 1px might not render well. Use Math.max(1, ...) size. OK.

Let's write it.

Also need a vignette / depth. Maybe add a subtle radial darkening at edges drawn in the fade step. Let's include a radial gradient overlay drawn each frame with low alpha in the fade. Hmm, that would accumulate darkness. Actually the fade draws the background gradient, and then we could draw a static vignette with alpha 0.05 each frame... it would accumulate to full vignette over ~20 frames. That's the same convergence behavior. But then the trails would also be darkened toward the vignette. That's fine, actually desirable.

Simplify: just one linear gradient for the fade. Add a separate radial "god ray" glow near the top for atmosphere — drawn with alpha 0.03 per frame. Hmm, it would wash out the trails in that region. Let's keep the fade as a single linear gradient (deep sea: dark at bottom #020a12, mid #06202e, top #0a3a4d). Then add a subtle vignette drawn on top with 'source-over' at low alpha... no, skip. Actually, a vignette makes it look more cinematic. I could draw the vignette as part of the fade using a radial gradient with alpha... but the fade uses a single fillStyle.

Alternative: use two fills in the fade step:
```js
ctx.globalAlpha = 0.16;
ctx.fillStyle = bgGrad; ctx.fillRect(...);
ctx.globalAlpha = 0.10;
ctx.fillStyle = vignetteGrad; ctx.fillRect(...);
```
where vignetteGrad is a radial gradient from transparent center to dark edges. This will converge to bg + vignette. Nice.

Hmm, but stacking two alpha fills: effective fade = 1-(1-0.16)(1-0.10) ≈ 0.244. Fine, tune.

Actually, simpler: just do the linear gradient with a radial light at the top-center baked... you can't easily bake a radial into a linear. Two fills it is. Or just draw the radial glow with 'lighter' for the light shaft and rely on the linear for the fade. Let's do:

fade step:
1. `globalCompositeOperation='source-over'; globalAlpha=0.18; fillStyle=bgGrad; fillRect(0,0,w,h);`

That's it. Keep it clean. The bg gradient itself will have a lighter region at top. I'll make the gradient stops: 
- 0: #0b3a4e (top, lighter teal)
- 0.35: #072434
- 0.7: #041420
- 1: #010a10

Good deep-sea look.

Hmm, but the top being lighter is like a "dusk sky" above. Fine either way.

Now, the label: a DOM div with "2,200 individuals" or similar. Position bottom-left, small monospace-ish font, subtle color. Also maybe show FPS? Not required. Just the count.

Let's use a div with CSS.

Also add a title? Not required. Just the count label.

Now predator rendering: draw as a sleek arrow/fish shape with a glowing trail. Use a path: triangle with concave back. Color: warm amber/orange (#ff9a3c) to contrast with cyan. Plus a glow via shadowBlur (expensive but only 2 predators).

Predators also leave trails because of the fade. Good.

Let me now write the code carefully.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Murmuration</title>
<style>
  html,body{margin:0;padding:0;height:100%;overflow:hidden;background:#010a10;}
  canvas{display:block;width:100vw;height:100vh;}
  #label{
    position:fixed;left:18px;bottom:16px;
    font:12px/1.4 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
    color:rgba(180,235,255,0.75);
    letter-spacing:0.08em;
    text-transform:uppercase;
    text-shadow:0 0 12px rgba(80,200,255,0.5);
    pointer-events:none;user-select:none;
  }
  #label b{color:rgba(230,250,255,0.95);font-weight:600;}
</style>
</head>
<body>
<canvas id="c"></canvas>
<div id="label"><b id="count">0</b> individuals</div>
<script> ... </script>
</body>
</html>
```

Now the JS.

```js
(() => {
'use strict';
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d', {alpha:false});
const countEl = document.getElementById('count');

const N = 2200;
const NUM_PRED = 2;

let W = 0, H = 0, DPR = 1;
```

Boid arrays: px, py, vx, vy.

Grid arrays: allocate on resize.

```js
const CELL = 36;
let cols=0, rows=0, counts, starts, cursor, items;
```

Note: N could exceed cell capacity? items length N. Fine.

Init:
```js
function initBoids(){
  for (let i=0;i<N;i++){
    px[i] = Math.random()*W;
    py[i] = Math.random()*H;
    const a = Math.random()*Math.PI*2;
    const s = 1.0 + Math.random()*1.5;
    vx[i] = Math.cos(a)*s;
    vy[i] = Math.sin(a)*s;
  }
}
```
But on resize we don't want to reinit. Just clamp positions.

Actually on resize, re-init grid arrays and clamp positions into the new bounds.

Let's write resize:
```js
function resize(){
  DPR = Math.min(window.devicePixelRatio || 1, 1.5);
  W = window.innerWidth; H = window.innerHeight;
  canvas.width = Math.floor(W*DPR);
  canvas.height = Math.floor(H*DPR);
  canvas.style.width = W+'px'; canvas.style.height = H+'px';
  ctx.setTransform(DPR,0,0,DPR,0,0);
  // bg gradient
  bgGrad = ctx.createLinearGradient(0,0,0,H);
  ...
  // bloom canvas
  BSCALE = 0.28;
  bloom.width = Math.max(1, Math.floor(W*BSCALE));
  bloom.height = Math.max(1, Math.floor(H*BSCALE));
  // grid
  cols = Math.ceil(W/CELL)+1; rows = Math.ceil(H/CELL)+1;
  const nCells = cols*rows;
  counts = new Int32Array(nCells);
  starts = new Int32Array(nCells+1);
  cursor = new Int32Array(nCells);
  items = new Int32Array(N);
}
```

Wait: bloom canvas drawn with drawImage scaled up — we need it in CSS px terms. The bloom canvas is W*BSCALE wide; drawing it to (0,0,W,H) upscales. Good. But the main ctx has a DPR transform, so drawing at (0,0,W,H) in CSS px → full device size. Good.

Note: ctx.setTransform with DPR means drawing coordinates in CSS px. The bloom canvas has its own resolution. Fine.

Now: the bloom canvas should also have a transform? We draw boids at (x*BSCALE, y*BSCALE). Let's set bx.setTransform(BSCALE,0,0,BSCALE,0,0) so we can use the same CSS-px coordinates. Then sprite sizes get scaled by BSCALE. Good.

Careful: if we set the transform, then clearRect(0,0,W,H) clears the whole thing. Fine.

Grid build function.

Main update loop:

```js
let last = performance.now();
function frame(now){
  let dt = (now - last)/16.6667;
  last = now;
  if (dt > 3) dt = 3;  // clamp
  if (!(dt > 0)) dt = 1;
  update(dt);
  render(dt);
  requestAnimationFrame(frame);
}
```

Hmm, clamping dt to 3 means at very low fps things slow down. That's acceptable.

Actually with dt clamp at 3 and physics tuned per-60fps-frame, at 30fps dt=2 → correct speed. Good.

Now update:

```js
function update(dt){
  buildGrid();
  // predators
  updatePredators(dt);
  // boids
  const R2 = 36*36;      // neighbor radius
  const SEP2 = 15*15;
  ...
}
```

Wait, CELL=36 and neighbor radius 36 → 3x3 covers radius up to 72 from center of middle cell... Let me re-verify: boid at position x in cell c. The 3x3 block spans cells c-1, c, c+1, covering [c*CELL - CELL, (c+1)*CELL + CELL) i.e., a window of 3*CELL=108 starting at c*CELL-36. The boid's x is in [c*36, (c+1)*36). The distance from the boid to the left edge of the block is at most x - (c*36-36) = (x - c*36) + 36 ∈ [36, 72). To the right: (c*36+72) - x ∈ (36, 72]. So the minimum guaranteed coverage in any direction is 36. So a neighbor radius of 36 is guaranteed covered. 

Set CELL = 40, neighbor R = 38 for safety. Let's use CELL=40, R=36.

Hmm, more cells = more overhead. 40 is fine.

Actually with larger cells, more boids per cell (avg 2000 cells... ). Screen 1600x900 → cols=41, rows=24 → 984 cells → ~2 boids/cell average, but the flock concentrates → maybe 20-50 per cell in the dense core. 9 cells × 50 = 450 neighbor checks for a boid in the core. × 2000 boids = 900k checks. Hmm, that's a lot but each is a few ops. Might be ~5-10ms. Risky.

Reduce: use CELL=28 with neighbor radius 26? Then a 3x3 covers radius 28... wait, min coverage = CELL. So CELL=28 → covers radius 28. Set R=26. More cells (57×32=1824) but fewer boids per cell in the core. 9 × ~20 = 180 checks per boid in the core → 360k. Better.

But the alignment radius should be similar to the perception radius. With R=26, alignment radius = 26, separation = 12. That's fine and gives tighter flocking. Actually, smaller alignment radius makes the flock more "local" and fluid — good for the twisting/splitting look.

Hmm, but with 2000 boids on a large screen, a 26px interaction radius means the flock behaves locally — good.

Let's use CELL = 30, R = 28, SEP = 13.

Let's estimate dense core: flock of 2000 boids in maybe 400×400 px area → 160000 px² / 900 px² per cell = 178 cells → ~11 boids/cell. 9 cells → ~100 neighbors. × 2000 = 200k checks. Good, ~2-4ms.

OK.

Now, we also need the "escape" to work. FLEE_R = 150.

Let me write the boid update:

```js
const R2 = 28*28, SEP2 = 13*13, SEPR = 13;
for (let i=0;i<N;i++){
  const x = px[i], y = py[i];
  let ax=0, ay=0;
  let sepX=0, sepY=0, aliX=0, aliY=0, cohX=0, cohY=0, cnt=0;

  let gx = (x*invCell)|0, gy = (y*invCell)|0;
  if (gx<0) gx=0; else if (gx>=cols) gx=cols-1;
  if (gy<0) gy=0; else if (gy>=rows) gy=rows-1;
  const gy0 = gy>0?gy-1:0, gy1 = gy<rows-1?gy+1:rows-1;
  const gx0 = gx>0?gx-1:0, gx1 = gx<cols-1?gx+1:cols-1;
  for (let cy=gy0; cy<=gy1; cy++){
    const rowBase = cy*cols;
    for (let cx=gx0; cx<=gx1; cx++){
      const c = rowBase + cx;
      const s = starts[c], e = starts[c+1];
      for (let k=s; k<e; k++){
        const j = items[k];
        if (j===i) continue;
        const dx = px[j]-x, dy = py[j]-y;
        const d2 = dx*dx+dy*dy;
        if (d2 > R2 || d2 < 1e-6) continue;
        cnt++;
        aliX += vx[j]; aliY += vy[j];
        cohX += px[j]; cohY += py[j];
        if (d2 < SEP2){
          const d = Math.sqrt(d2);
          const f = (1 - d/SEPR) / d;
          sepX -= dx*f; sepY -= dy*f;
        }
      }
    }
  }
  ...
}
```

Wait, `(1 - d/SEPR)/d` at small d explodes. With d >= 0.001... Actually since we skip d2 < 1e-6, d >= 0.001, so f up to 1000. That's a huge force. Then sepX would be huge and dominate. Let's cap: use `const f = (1 - d/SEPR);` and `sepX -= dx/d * f` — bounded by 1 in magnitude per neighbor, but then when d is tiny, dx/d is a unit vector (numerically unstable but fine). Total sep magnitude up to cnt. Then we normalize by dividing by cnt or clamping. Let's normalize by count and clamp to a max.

Let me do: 
```js
if (d2 < SEP2){
  const d = Math.sqrt(d2);
  const f = (1 - d/SEPR) / d;   // weight
  sepX -= dx*f*0.5; sepY -= dy*f*0.5;
}
```
Hmm.

Cleanest: accumulate a unit vector scaled by weight:
```js
const inv = 1/(Math.sqrt(d2)+0.0001);
const w = 1 - d/SEPR;  // 0..1
sepX -= dx*inv*w; sepY -= dy*inv*w;
```
Then after the loop, `sepX /= max(1,cnt)` and clamp magnitude to 1. Fine.

Then alignment: `aliX = aliX/cnt - vx[i]` → steer toward average velocity. Then normalize to a max of 1.

Cohesion: `cohX = cohX/cnt - x` → direction to center. Normalize.

Let's write helper inline.

Then:
```js
// normalize helpers
let sx=0, sy=0;
if (cnt>0){
  // separation
  let sepMag = Math.hypot(sepX, sepY);
  if (sepMag > 0.0001){ sx += sepX/sepMag * WSEP; sy += sepY/sepMag * WSEP; }
  // alignment
  aliX = aliX/cnt - vx[i]; aliY = aliY/cnt - vy[i];
  const am = Math.hypot(aliX,aliY);
  if (am>0.0001){ sx += aliX/am*WALI; sy += aliY/am*WALI; }
  // cohesion
  cohX = cohX/cnt - x; cohY = cohY/cnt - y;
  const cm = Math.hypot(cohX,cohY);
  if (cm>0.0001){ sx += cohX/cm*WCOH; sy += cohY/cm*WCOH; }
}
```
Math.hypot is slow-ish. Use Math.sqrt(dx*dx+dy*dy).

Weights: WSEP = 0.9, WALI = 0.55, WCOH = 0.35. Hmm, in force units where max speed is ~2.6 and dt=1. Acceleration of 0.9 per frame is a lot. Let's tune: these are accelerations added to velocity each frame. With maxSpeed 2.6, an acceleration of 0.15-0.3 per frame gives reasonable turning.

Let's set WSEP=0.28, WALI=0.18, WCOH=0.12. Hmm, but they need to overcome each other. Let's think: the sum of normalized directions × weights. Total accel magnitude ~0.5. Over ~10 frames, velocity changes by 5 — that's more than maxSpeed, so it'll be clamped constantly. That's OK, it means quick turning. Maybe slightly too twitchy.

Let's use WSEP=0.22, WALI=0.14, WCOH=0.10, and add a "smoothness" by limiting turn rate? Simpler: just clamp speed and let it be. Actually the classic Reynolds approach: steer = desired - velocity, clamped to maxForce. Let's do the "desired velocity" approach which is more stable:

- Desired alignment velocity = avgVel normalized × maxSpeed
- Desired cohesion velocity = direction to center × maxSpeed
- Desired separation velocity = away direction × maxSpeed
- Combine weighted → desired velocity
- steer = (desired - vel) × steerStrength

That's basically the same thing. Let's just go with the simple accumulation and tune empirically by reasoning.

Let's define:
```
MAXSPEED = 2.4
MINSPEED = 1.1
```
Accel per frame should be maybe 0.08-0.2 to give smooth motion.

Let's set:
- WSEP = 0.30 (separation needs to be strong to prevent clumping)
- WALI = 0.10
- WCOH = 0.06
- WFLEE = 0.9 (panic)
- boundary = 0.3

Hmm. With WFLEE=0.9 and multiple predators, could be large. Let's clamp the total acceleration magnitude to ~1.2.

Actually, let's do the force accumulation then clamp:
```js
const am = Math.sqrt(sx*sx+sy*sy);
const MAXA = 0.9;
if (am > MAXA){ sx = sx/am*MAXA; sy = sy/am*MAXA; }
vx[i] += sx*dt; vy[i] += sy*dt;
```
Wait, but if we clamp, the relative weights matter less. Fine.

Hmm, clamping the total accel means when panicking, the flee force dominates anyway.

Let's write it with the clamp at 0.85.

Then speed clamp:
```js
let sp = Math.sqrt(vx*vx+vy*vy);
const maxS = MAXSPEED * (1 + panic*0.8);
if (sp > maxS){ vx *= maxS/sp; vy *= maxS/sp; }
else if (sp < MINSPEED && sp > 0.001){ vx *= MINSPEED/sp; vy *= MINSPEED/sp; }
```

Panic computed from predator distance.

Boundary: 
```js
const M = 90;
if (x < M) sx += (1 - x/M)*0.6;
if (x > W-M) sx -= (1 - (W-x)/M)*0.6;
// same for y
```
Actually, add to sx before clamping. Let's compute boundary contribution separately and add.

Also, wrap-around vs bounce? Steering away from edges is nicer for a flock. But with 2000 boids and a strong flee, some may escape. The boundary force should be strong enough.

Alternatively, wrap around the screen edges (toroidal) — then the flock never gets stuck at edges. But then the "living cloud" would jump. Hmm. With soft steering it's fine. Let's use soft steering with a decent margin (120px) and moderate strength.

Hmm, but during a predator burst, boids could be pushed off-screen. The boundary force at 0.6 max accel vs flee at 0.9... They'd slow down but not escape permanently. Actually if a boid is outside the screen it would just come back. Since we draw only within the canvas, brief excursions are invisible but harmless. Actually, being off-screen for a while reduces the visual density. Let's make the boundary force ramp up strongly near the edge (up to 1.5 accel at the very edge).

Let's do: margin M=140, force = ((M - dist)/M)^2 * 1.6. At the edge, force = 1.6. Good.

Now predators.

```js
const ppx = new Float32Array(NUM_PRED), ppy = ..., pvx, pvy;
```
Init near the center-ish, moving.

Predator update:
1. Find local centroid of boids within PR=320 using the grid.
2. If found, desired direction = toward centroid. Else wander.
3. Also, if the centroid is very close (< 60), keep going (momentum) so it passes through.
4. Steer with limited turn rate.

Let me implement:
```js
function updatePredators(dt){
  for (let p=0;p<NUM_PRED;p++){
    // find centroid of boids within radius
    let cx=0, cy=0, n=0;
    const R = 300, R2 = R*R;
    // grid range
    const gx = clamp((ppx[p]/CELL)|0), gy=...
    const rad = Math.ceil(R/CELL);
    for (let yy=gy-rad; yy<=gy+rad; yy++){
      if (yy<0||yy>=rows) continue;
      for (let xx=gx-rad; xx<=gx+rad; xx++){
        if (xx<0||xx>=cols) continue;
        const c = yy*cols+xx;
        for (let k=starts[c]; k<starts[c+1]; k++){
          const j = items[k];
          const dx = px[j]-ppx[p], dy = py[j]-ppy[p];
          const d2 = dx*dx+dy*dy;
          if (d2 < R2){ cx+=px[j]; cy+=py[j]; n++; }
        }
      }
    }
```
rad = ceil(300/30) = 10 → 21×21 = 441 cells × 2 predators = 882 cells. Each cell ~2 boids → ~1800 distance checks. Fine.

Hmm, but the predator's own "reach" is 300px; using the centroid of all boids within 300px means the predator aims at the middle of the local mass. As it approaches, the centroid moves. That works — it chases into the flock.

But if the predator is inside the flock, the centroid is ~its own position, and it would slow/stop. Better: aim at the centroid of boids within a ring or the farthest? 

Common approach: the predator targets the nearest boid and chases. Let's do: track a target index. Each frame, find the nearest boid within 400px (using the grid). Steer toward it. If the distance < 25, the boid is "caught" → pick a new target (or the same one keeps fleeing). Actually just always chase the nearest — but the nearest is often the one right next to it, causing jitter.

Better: chase the local centroid but with a "prediction": aim ahead of the centroid along the predator's velocity. Or aim at the centroid but only consider boids in the forward hemisphere.

Alternative simple approach that looks great: predator steers toward the global flock centroid with a large radius, plus a bit of noise. Since the flock centroid is roughly the center of mass, the predator drives through the flock, boids scatter, and the flock's center reforms behind. Then the predator turns around and comes back. That creates a nice oscillation: chase, burst, turn, chase again.

Hmm, but if the predator always goes to the centroid, and the flock's centroid moves away from the predator, the predator follows — creating a continuous chase. Good.

But with a pure centroid chase, the predator will always aim at the densest point, which is nice.

Let's do the local centroid with R=260, and if n==0 use the global centroid. Plus aim ahead: target = centroid + centroidVel*... eh, keep it simple.

Actually, a nice trick for the "burst and reform behind it": make the predator fast enough (maxSpeed 3.6 vs boid 2.4) so it plows through.

Also, to prevent the predator from stopping in the middle: if the distance to the centroid is small (< 100), just keep the current heading (don't steer) for a bit. Let's implement a "commit" behavior: when the predator is within 150px of the centroid, it stops steering toward it and instead continues straight (with slight randomness) for ~40 frames. Then it re-engages.

Simpler: steer toward the centroid but with a minimum speed (predator never slows below 2.8). Since it always moves forward at a good clip, it will pass through the flock.

Let's do: desired direction = normalize(centroid - pos), desired speed = PMAX. steer = (desiredVel - vel) * 0.06, clamp. Plus a bit of noise. With a min speed enforced. That should be fine.

Actually, I want the predator to sometimes overshoot and loop back. Let's add a turn-rate limit: the heading can change by at most 0.035 rad per frame. That creates smooth arcs. Good.

Let me just implement:

```js
// desired
let dx = tx - ppx[p], dy = ty - ppy[p];
const dl = Math.hypot(dx,dy) || 1;
dx/=dl; dy/=dl;
// current heading
const ch = Math.atan2(pvy[p], pvx[p]);
const th = Math.atan2(dy, dx);
let diff = th - ch;
while (diff > Math.PI) diff -= 2*Math.PI;
while (diff < -Math.PI) diff += 2*Math.PI;
const maxTurn = 0.045*dt;
if (diff > maxTurn) diff = maxTurn; else if (diff < -maxTurn) diff = -maxTurn;
const nh = ch + diff;
const spd = PMAX * (0.85 + 0.15*Math.sin(t*0.7+p));
pvx[p] = Math.cos(nh)*spd;
pvy[p] = Math.sin(nh)*spd;
ppx[p] += pvx[p]*dt; ppy[p] += pvy[p]*dt;
```

And bounce the predator off the walls (steer back). Actually, since it chases the flock, it'll stay inside. But add boundary steering to the heading: if near an edge, add a turn toward the center. Simplest: after computing the desired direction, if the predator is within 120px of an edge, blend the desired direction with the direction to the screen center.

Let me do: compute desired direction as a weighted sum of (to centroid) and (to center, weighted by edge proximity). 

```js
let tx = cxc, ty = cyc;
// edge avoidance
let ex = 0, ey = 0;
const M2 = 150;
if (ppx[p] < M2) ex += (M2-ppx[p])/M2;
if (ppx[p] > W-M2) ex -= (M2-(W-ppx[p]))/M2;
if (ppy[p] < M2) ey += (M2-ppy[p])/M2;
if (ppy[p] > H-M2) ey -= (M2-(H-ppy[p]))/M2;
tx += ex*400; ty += ey*400;
```
That biases the target away from the edge. Good.

Now boids' flee force:
```js
for (let p=0;p<NUM_PRED;p++){
  const dx = x - ppx[p], dy = y - ppy[p];
  const d2 = dx*dx+dy*dy;
  if (d2 < FLEE2){
    const d = Math.sqrt(d2) || 0.001;
    const f = 1 - d/FLEER;
    const w = f*f*2.2;
    fleeX += dx/d*w; fleeY += dy/d*w;
    if (f > panic) panic = f;
  }
}
```
f*f gives a sharper near-field. Max w = 2.2 at d=0. Then the accel clamp at ~1.2 will limit it anyway. Let's set the clamp higher during panic, like 2.0.

Hmm, let's make MAXA dynamic: MAXA = 0.85 + panic*1.6.

OK. FLEER = 160.

Now rendering.

```js
function render(dt){
  // fade
  ctx.globalCompositeOperation = 'source-over';
  ctx.globalAlpha = FADE;
  ctx.fillStyle = bgGrad;
  ctx.fillRect(0,0,W,H);
  ctx.globalAlpha = 1;

  // bloom layer clear
  bx.setTransform(1,0,0,1,0,0);
  bx.clearRect(0,0,bloom.width,bloom.height);
  bx.setTransform(BSCALE,0,0,BSCALE,0,0);

  // draw boids
  ctx.globalCompositeOperation = 'lighter';
  bx.globalCompositeOperation = 'lighter';

  // per-bucket paths on bloom; sprite draws on main
  ...
}
```

For the main canvas, I'll use sprites: `ctx.drawImage(sprite[bucket], x-4, y-4, 8, 8)`.

For bloom, use fillRect on bx with size ~ 2.5 (in CSS px scaled by BSCALE = 0.7 device px). Hmm, at BSCALE=0.28, a 2.5 CSS px rect = 0.7 device px. Too small; the fillRect would be sub-pixel and anti-aliased to very faint. Let's use size 4 CSS px in the bloom → 1.12 device px. Still tiny but visible.

Actually, maybe just draw the sprites into the bloom canvas too: `bx.drawImage(sprite[b], x-8, y-8, 16, 16)` → 4.5 device px. That gives a soft blob. Then upscaling 1/0.28 = 3.6× gives a nice big glow.

Hmm, cost: 2000 more drawImage. Let's just accept it. Actually, to reduce cost, only draw every other boid into the bloom? That would halve the cost and the glow would still look fine. Let's do: draw every boid into the main, and every boid into bloom (keep it accurate for density).

Let me reconsider — maybe I should use fillRect for the main canvas too and skip sprites. 2000 fillRects is much cheaper than 2000 drawImages. And the bloom provides the soft glow, so crisp rects + glow = looks good.

Decision: main canvas uses fillRect with per-bucket batched paths (only 5 fill calls total!), bloom uses sprites (soft blobs).

Batched paths:
```js
// build paths
for (let b=0;b<5;b++) paths[b] = new Path2D();
```
Creating Path2D each frame — 5 objects, fine. Then `p.rect(x-1, y-1, 2, 2)`. Then fill each with its color.

Hmm, Path2D with 2000 rects — building the path is fast. Filling is one pass. 

Actually, `ctx.rect()` on the current path accumulates into a single path — same thing. Let's use Path2D for clarity.

Hmm, one concern: with 'lighter' compositing and a path fill, overlapping rects within the same path won't double-add (nonzero winding fill of a single path fills each pixel once). That's actually good — it prevents the dense core from over-saturating within a single bucket. But different buckets will still add. Fine.

Actually, for a nice glow in the dense core, we might WANT accumulation. But the bloom layer handles that.

OK let's write the render:

```js
const boidPaths = [new Path2D(), ...];  // recreate each frame? Path2D has no clear method.
```
We must recreate them each frame: `const p0 = new Path2D(), p1 = ...`. Or use an array and reassign.

Let's do:
```js
const paths = [new Path2D(), new Path2D(), new Path2D(), new Path2D(), new Path2D()];
```
recreated in render.

Then for each boid compute bucket and add rect.

Compute bucket cheaply: 
```js
const sp2 = vx[i]*vx[i]+vy[i]*vy[i];
let t = (Math.sqrt(sp2) - MINSPEED) * 0.42; // ~ (2.4-1.1)=1.3 → 0.55
```
Hmm, let's just do `t = (Math.sqrt(sp2) - 1.1) * 0.7` clamped to [0,1], plus panic*0.8.

Let's define bright = clamp(0.15 + t*0.85 + panic*0.9, 0, 1) then bucket = min(4, floor(bright*5)).

Colors array with alpha. With 'lighter', alpha matters.

Actually, let me store the boid brightness during the update loop to avoid recomputing. I'll store it in a Float32Array `bright` or compute in render. Computing in render is fine (one sqrt per boid).

Hmm, I need panic per boid for brightness. Let me store panic in a Float32Array during update. Yes, `panicArr`.

Let's do that.

Now the boid size: base 2.2 px, plus panic. `const sz = 2.0 + bright*1.2;` then rect(x - sz/2, y - sz/2, sz, sz).

Hmm, at DPR 1.5, a 2.2 CSS px rect = 3.3 device px. Fine.

Bloom: `bx.drawImage(sprite[b], x-6, y-6, 12, 12)` in CSS px → at BSCALE 0.28 → 3.4 device px. Good.

Then composite the bloom onto the main:
```js
ctx.globalCompositeOperation = 'lighter';
ctx.globalAlpha = 0.55;
ctx.imageSmoothingEnabled = true;
ctx.drawImage(bloom, 0, 0, W, H);
ctx.globalAlpha = 1;
```

Wait — but the main canvas already has trails from previous frames, and the bloom is only from the current frame. The bloom will be drawn over the trails, adding a fresh glow. That's fine and creates a nice "current frame glow over faded trails" look.

Hmm, but the bloom upscaled from 0.28 will have visible blockiness? With imageSmoothingEnabled=true (default) it's bilinear, which at 3.6× upscale gives a soft, slightly blocky look. For a glow, that's actually fine (it's blurry). But bilinear upscaling of a low-res image produces a "bilinear star" artifact. For soft glows, it's acceptable. Let's use BSCALE = 0.4 for a bit more fidelity → upscale 2.5×. Cost: bloom canvas is 0.16 of the pixels. Fine.

Hmm, with BSCALE=0.4 and sprite drawn at 12 CSS px → 4.8 device px in bloom. Then upscaled 2.5× → 12 CSS px of glow. Good.

Let's go with BSCALE = 0.4.

Now, the predator rendering. Draw with 'source-over' (not lighter) so it reads as a solid object. Or lighter with a bright color. Let's use 'lighter' with an amber color so it glows.

Predator shape: a sleek fish/arrow. Draw a path in local coords and rotate.

```js
ctx.save();
ctx.translate(ppx[p], ppy[p]);
ctx.rotate(Math.atan2(pvy[p], pvx[p]));
ctx.beginPath();
ctx.moveTo(16,0);
ctx.quadraticCurveTo(2, 7, -10, 6);
ctx.quadraticCurveTo(-6, 0, -10, -6);
ctx.quadraticCurveTo(2, -7, 16, 0);
ctx.closePath();
// glow
ctx.shadowBlur = 22; ctx.shadowColor = 'rgba(255,150,60,0.9)';
ctx.fillStyle = 'rgba(255,190,110,0.95)';
ctx.fill();
ctx.restore();
```

With shadowBlur and 'lighter'... shadowBlur works with lighter? The shadow is drawn as part of the fill operation, so it should composite with 'lighter' too. Let's set globalCompositeOperation='lighter' before. Should be fine. Actually, shadow rendering can be expensive, but only 2 per frame.

Hmm, also add a trailing glow: draw a few faded copies behind. The motion blur handles that.

Also the label. Update the count element once: `countEl.textContent = N.toLocaleString()`.

Now, initial conditions: I want the flock to look interesting immediately. Let's initialize boids in a few clusters so they merge into a cloud. Or distribute them in a big soft disc in the center.

Let's init: position = center + random gaussian-ish offset with radius ~ min(W,H)*0.35, velocity tangential (swirling). That gives an immediate vortex that then self-organizes. 

Actually, a tangential velocity field creates a nice initial swirl that then breaks into flocking. Let's do that.

```js
const cx0 = W*0.5, cy0 = H*0.5;
for (let i=0;i<N;i++){
  const a = Math.random()*Math.PI*2;
  const r = Math.sqrt(Math.random()) * Math.min(W,H)*0.36;
  const x = cx0 + Math.cos(a)*r, y = cy0 + Math.sin(a)*r*0.8;
  px[i]=x; py[i]=y;
  // tangential
  const tx = -(y-cy0), ty = (x-cx0);
  const tl = Math.hypot(tx,ty)||1;
  vx[i] = tx/tl*2 + (Math.random()-0.5)*0.6;
  vy[i] = ty/tl*2 + (Math.random()-0.5)*0.6;
}
```

Good.

Predators: start at opposite corners, heading toward the center.

Now let's handle the "first 30 seconds" requirement — everything important should show. The flock forms, predators attack, bursts happen. With 2 predators constantly hunting, bursts will happen every few seconds. Good.

Let's also make sure the simulation is visually dense from frame 1. Yes.

One more thing: "lighting so the swarm reads as a single organism". The additive blending + bloom + density-dependent brightness achieves this.

Maybe also add a subtle "depth" by making boids' brightness depend on... nah.

Let me now also handle: what if the flock all flies off one edge? The boundary steering should handle it.

Let me write the final code.

```js
(function(){
  'use strict';

  const canvas = document.getElementById('c');
  const ctx = canvas.getContext('2d', { alpha: false });
  const labelEl = document.getElementById('count');

  const N = 2200;
  const NUM_PRED = 2;

  const MAXSPEED = 2.45;
  const MINSPEED = 1.05;
  const CELL = 30;
  const NEI_R = 28;
  const NEI_R2 = NEI_R*NEI_R;
  const SEP_R = 12;
  const SEP_R2 = SEP_R*SEP_R;
  const FLEE_R = 165;
  const FLEE_R2 = FLEE_R*FLEE_R;

  let W = 1, H = 1, DPR = 1;
  let cols = 1, rows = 1;
  let counts, starts, cursor, items;
  let bgGrad = null;
  let bloom, bx;
  const BSCALE = 0.4;

  const px = new Float32Array(N), py = new Float32Array(N);
  const vx = new Float32Array(N), vy = new Float32Array(N);
  const pan = new Float32Array(N);

  const ppx = new Float32Array(NUM_PRED), ppy = new Float32Array(NUM_PRED);
  const pvx = new Float32Array(NUM_PRED), pvy = new Float32Array(NUM_PRED);

  // sprites
  const BUCKET_COLORS = [
    [ 36, 104, 168],
    [ 58, 168, 214],
    [110, 226, 244],
    [186, 248, 255],
    [255, 255, 255]
  ];
  const SPR = 20;
  const sprites = BUCKET_COLORS.map(c => makeSprite(c[0],c[1],c[2]));
  ...
})();
```

makeSprite:
```js
function makeSprite(r,g,b){
  const cv = document.createElement('canvas');
  cv.width = cv.height = SPR;
  const g2 = cv.getContext('2d');
  const grd = g2.createRadialGradient(SPR/2, SPR/2, 0, SPR/2, SPR/2, SPR/2);
  grd.addColorStop(0, 'rgba('+r+','+g+','+b+',0.95)');
  grd.addColorStop(0.35, 'rgba('+r+','+g+','+b+',0.35)');
  grd.addColorStop(0.7, 'rgba('+r+','+g+','+b+',0.08)');
  grd.addColorStop(1, 'rgba('+r+','+g+','+b+',0)');
  g2.fillStyle = grd;
  g2.fillRect(0,0,SPR,SPR);
  return cv;
}
```

Now the main loop.

Let me write the whole thing.

For the render, I want to draw boid rects with batched paths.

```js
const pathArr = [];
function render(){
  // fade
  ctx.globalCompositeOperation = 'source-over';
  ctx.globalAlpha = 0.20;
  ctx.fillStyle = bgGrad;
  ctx.fillRect(0, 0, W, H);
  ctx.globalAlpha = 1;

  // clear bloom
  bx.setTransform(1,0,0,1,0,0);
  bx.clearRect(0,0,bloom.width,bloom.height);
  bx.setTransform(BSCALE,0,0,BSCALE,0,0);

  for (let b=0;b<5;b++) pathArr[b] = new Path2D();

  for (let i=0;i<N;i++){
    const x = px[i], y = py[i];
    const sp = Math.sqrt(vx[i]*vx[i] + vy[i]*vy[i]);
    let t = (sp - MINSPEED) * 0.75;
    if (t < 0) t = 0; else if (t > 1) t = 1;
    let br = 0.12 + t*0.88 + pan[i]*1.0;
    if (br > 1) br = 1;
    let b = (br*5)|0; if (b>4) b=4;
    const s = 1.9 + br*1.6;
    pathArr[b].rect(x - s*0.5, y - s*0.5, s, s);
    bx.drawImage(sprites[b], x - 7, y - 7, 14, 14);
  }

  ctx.globalCompositeOperation = 'lighter';
  for (let b=0;b<5;b++){
    ctx.fillStyle = FILLS[b];
    ctx.fill(pathArr[b]);
  }
  ...
}
```

FILLS:
```js
const FILLS = [
  'rgba(36,104,168,0.55)',
  'rgba(58,168,214,0.6)',
  'rgba(110,226,244,0.7)',
  'rgba(186,248,255,0.85)',
  'rgba(255,255,255,0.95)'
];
```

Then bloom composite:
```js
ctx.globalCompositeOperation = 'lighter';
ctx.globalAlpha = 0.5;
ctx.drawImage(bloom, 0, 0, W, H);
ctx.globalAlpha = 1;
```
Note: drawing with the DPR transform applied, drawImage(bloom, 0,0,W,H) → destination in CSS px. Correct.

Then predators with 'lighter'.

Then reset to 'source-over'.

Hmm — one issue: drawing the bloom after the boids means the glow is drawn on top, which is fine with 'lighter'.

Now, the trail fade: 0.20 per frame means trails last ~5 frames. At 60fps that's ~85ms. A bit short but gives a nice motion blur streak. Let's use 0.16 → ~6 frames. Hmm, the fade accumulates: after n frames, the remaining fraction is (1-0.16)^n. After 10 frames: 0.84^10 = 0.17. So visible for ~10 frames. That's a nice subtle streak.

Let's use 0.15.

Hmm, but with 'lighter' boids accumulating over 10 frames, the total brightness is ~6× the per-frame brightness in a static area. That could blow out. But since boids move, it spreads out. Actually the per-boid fill alpha is 0.55-0.95, and 10 frames of accumulation at those alphas would saturate to white. Hmm.

Let's reduce the fill alphas: use ~0.35 max. And rely on the bloom for brightness.

Actually, let's reconsider. With the fade at 0.15, the steady-state accumulation factor is 1/0.15 ≈ 6.7. So each frame's contribution should be ~1/6.7 of the target. If I want a boid to appear at ~0.6 brightness in steady state, the per-frame alpha should be ~0.09. That's very low.

Hmm, that's the nature of trails. But boids move, so they don't stay in one place — a moving boid leaves a trail, and the peak brightness at the current position is roughly the per-frame alpha plus the faded trail. Actually, the trail behind is from previous positions, so the current position gets just the current frame's contribution (plus whatever was there before, which is small if it just arrived).

So per-frame alpha 0.55 is fine for the head; the trail behind is a decaying streak. But in dense areas where many boids overlap frame after frame, it will saturate. That's actually the "single organism" glow effect. OK, but it might blow out to a white blob.

Let's use moderate alphas: [0.25, 0.3, 0.38, 0.5, 0.6] and the bloom at 0.45. And fade 0.18. I'll tune by reasoning; can't test. Let's be conservative: fade 0.22 (trails ~5 frames), alphas [0.22,0.28,0.35,0.45,0.55], bloom alpha 0.4.

Hmm. With fade 0.22, the accumulation factor is 4.5. Dense core with 20 boids per pixel-area... it'll saturate. That's OK — that's the bright core of the swarm.

I think it'll look good. Let's go with fade 0.19.

Actually, one risk: with additive blending and trails, the whole screen could wash out to white over time if there's any residual. No — the fade brings everything back to the background gradient exponentially. Fine.

Let's also consider: the background gradient fill with alpha 0.19 over a bright trail — the trail color mixes toward the background color, which is dark blue. Good.

Now let's write the update function fully.

```js
function update(dt){
  buildGrid();
  updatePredators(dt);

  const invCell = 1/CELL;

  for (let i=0;i<N;i++){
    const x = px[i], y = py[i];
    const vxi = vx[i], vyi = vy[i];

    let sepX=0, sepY=0, aliX=0, aliY=0, cohX=0, cohY=0, cnt=0;

    let gx = (x*invCell)|0;
    let gy = (y*invCell)|0;
    if (gx<0) gx=0; else if (gx>=cols) gx=cols-1;
    if (gy<0) gy=0; else if (gy>=rows) gy=rows-1;

    const gx0 = gx>0?gx-1:0, gx1 = gx<cols-1?gx+1:cols-1;
    const gy0 = gy>0?gy-1:0, gy1 = gy<rows-1?gy+1:rows-1;

    for (let cy=gy0; cy<=gy1; cy++){
      const base = cy*cols;
      for (let cx=gx0; cx<=gx1; cx++){
        const c = base+cx;
        const e = starts[c+1];
        for (let k=starts[c]; k<e; k++){
          const j = items[k];
          if (j === i) continue;
          const dx = px[j]-x, dy = py[j]-y;
          const d2 = dx*dx + dy*dy;
          if (d2 > NEI_R2 || d2 < 1e-8) continue;
          cnt++;
          aliX += vx[j]; aliY += vy[j];
          cohX += px[j]; cohY += py[j];
          if (d2 < SEP_R2){
            const d = Math.sqrt(d2);
            const w = (1 - d/SEP_R) / d;
            sepX -= dx*w; sepY -= dy*w;
          }
        }
      }
    }

    let ax = 0, ay = 0;
    if (cnt > 0){
      const inv = 1/cnt;
      // separation
      let m = Math.sqrt(sepX*sepX + sepY*sepY);
      if (m > 1e-4){ ax += sepX/m * 0.42; ay += sepY/m * 0.42; }
      // alignment
      aliX = aliX*inv - vxi; aliY = aliY*inv - vyi;
      m = Math.sqrt(aliX*aliX + aliY*aliY);
      if (m > 1e-4){ ax += aliX/m * 0.16; ay += aliY/m * 0.16; }
      // cohesion
      cohX = cohX*inv - x; cohY = cohY*inv - y;
      m = Math.sqrt(cohX*cohX + cohY*cohY);
      if (m > 1e-4){ ax += cohX/m * 0.12; ay += cohY/m * 0.12; }
    }
    ...
```

Wait, separation with `w = (1-d/SEP_R)/d` blows up as d→0 (w up to 1000 at d=0.001... well, 1/0.001 = 1000). Then sepX could be huge, but we normalize by its magnitude, so it's fine — it's just a direction. Good, the normalization saves us.

Hmm, but if there's one very close neighbor, its direction dominates entirely. That's actually desirable for separation.

OK.

Then predators:
```js
    let pn = 0;
    for (let p=0;p<NUM_PRED;p++){
      const dx = x - ppx[p], dy = y - ppy[p];
      const d2 = dx*dx + dy*dy;
      if (d2 < FLEE_R2){
        const d = Math.sqrt(d2) + 0.001;
        const f = 1 - d/FLEE_R;
        const w = f*f*3.0;
        ax += dx/d*w; ay += dy/d*w;
        if (f > pn) pn = f;
      }
    }
    pan[i] = pn;
```

Hmm, `w = f*f*3.0` with ax being the acceleration. Max 3.0. Then the clamp.

Boundary:
```js
    const M = 150;
    if (x < M){ const f = (M-x)/M; ax += f*f*1.8; }
    else if (x > W-M){ const f = (M-(W-x))/M; ax -= f*f*1.8; }
    if (y < M){ const f = (M-y)/M; ay += f*f*1.8; }
    else if (y > H-M){ const f = (M-(H-y))/M; ay -= f*f*1.8; }
```

Then clamp and integrate:
```js
    const maxA = 0.9 + pn*2.4;
    let am = Math.sqrt(ax*ax+ay*ay);
    if (am > maxA){ const s = maxA/am; ax*=s; ay*=s; }

    let nvx = vxi + ax*dt;
    let nvy = vyi + ay*dt;

    let sp = Math.sqrt(nvx*nvx + nvy*nvy);
    const maxS = MAXSPEED * (1 + pn*0.85);
    if (sp > maxS){ const s = maxS/sp; nvx*=s; nvy*=s; }
    else if (sp < MINSPEED && sp > 1e-5){ const s = MINSPEED/sp; nvx*=s; nvy*=s; }
    else if (sp <= 1e-5){ nvx = MINSPEED; nvy = 0; }

    vx[i]=nvx; vy[i]=nvy;
    px[i] = x + nvx*dt;
    py[i] = y + nvy*dt;
```

Note: I'm writing px[i] inside the loop, but other boids read px[j] — reading partially updated positions is fine (Gauss-Seidel style), actually it can speed up convergence. Fine.

Hmm, but the grid was built with the old positions. Minor inconsistency, fine.

Wait, there's a subtle issue: I update px[i] immediately, but boid j>i reads the new px[i] while the grid cell assignment is based on the old position. The error is at most ~2.5px per frame, which is less than the cell size margin. Fine.

Now, `items` is Int32Array and `starts` etc. Good.

Now buildGrid:

```js
function buildGrid(){
  counts.fill(0);
  const invCell = 1/CELL;
  for (let i=0;i<N;i++){
    let gx = (px[i]*invCell)|0;
    let gy = (py[i]*invCell)|0;
    if (gx<0) gx=0; else if (gx>=cols) gx=cols-1;
    if (gy<0) gy=0; else if (gy>=rows) gy=rows-1;
    counts[gy*cols+gx]++;
  }
  let s = 0;
  for (let c=0, nc=cols*rows; c<nc; c++){
    starts[c] = s;
    cursor[c] = s;
    s += counts[c];
  }
  starts[cols*rows] = s;
  for (let i=0;i<N;i++){
    let gx = (px[i]*invCell)|0;
    let gy = (py[i]*invCell)|0;
    if (gx<0) gx=0; else if (gx>=cols) gx=cols-1;
    if (gy<0) gy=0; else if (gy>=rows) gy=rows-1;
    const c = gy*cols+gx;
    items[cursor[c]++] = i;
  }
}
```

`(px[i]*invCell)|0` — for negative px, `|0` truncates toward zero, giving 0 for -0.5. Then clamped to 0. Fine.

Note: px can be slightly negative or > W. Clamped. Good.

Now updatePredators. It needs the grid built. Yes, buildGrid is called first.

```js
function updatePredators(dt){
  const R = 300, R2 = R*R;
  const rad = Math.ceil(R/CELL);
  const invCell = 1/CELL;

  for (let p=0;p<NUM_PRED;p++){
    let cx=0, cy=0, n=0;
    let gx = (ppx[p]*invCell)|0;
    let gy = (ppy[p]*invCell)|0;
    if (gx<0) gx=0; else if (gx>=cols) gx=cols-1;
    if (gy<0) gy=0; else if (gy>=rows) gy=rows-1;

    const x0 = Math.max(0, gx-rad), x1 = Math.min(cols-1, gx+rad);
    const y0 = Math.max(0, gy-rad), y1 = Math.min(rows-1, gy+rad);
    for (let yy=y0; yy<=y1; yy++){
      const base = yy*cols;
      for (let xx=x0; xx<=x1; xx++){
        const c = base+xx;
        const e = starts[c+1];
        for (let k=starts[c]; k<e; k++){
          const j = items[k];
          const dx = px[j]-ppx[p], dy = py[j]-ppy[p];
          const d2 = dx*dx+dy*dy;
          if (d2 < R2){ cx += px[j]; cy += py[j]; n++; }
        }
      }
    }

    let tx, ty;
    if (n > 0){ tx = cx/n; ty = cy/n; }
    else { tx = W*0.5; ty = H*0.5; }

    // edge avoidance
    const M = 170;
    if (ppx[p] < M) tx += (M-ppx[p])*2.2;
    if (ppx[p] > W-M) tx -= (M-(W-ppx[p]))*2.2;
    if (ppy[p] < M) ty += (M-ppy[p])*2.2;
    if (ppy[p] > H-M) ty -= (M-(H-ppy[p]))*2.2;

    let dx = tx - ppx[p], dy = ty - ppy[p];
    const dl = Math.sqrt(dx*dx+dy*dy) || 1;
    dx /= dl; dy /= dl;

    const ch = Math.atan2(pvy[p], pvx[p]);
    const th = Math.atan2(dy, dx);
    let diff = th - ch;
    while (diff > Math.PI) diff -= 6.283185307;
    while (diff < -Math.PI) diff += 6.283185307;
    const maxTurn = 0.05*dt;
    if (diff > maxTurn) diff = maxTurn; else if (diff < -maxTurn) diff = -maxTurn;
    const nh = ch + diff;

    const spd = 3.5;
    pvx[p] = Math.cos(nh)*spd;
    pvy[p] = Math.sin(nh)*spd;
    ppx[p] += pvx[p]*dt;
    ppy[p] += pvy[p]*dt;
  }
}
```

Hmm, `maxTurn = 0.05*dt` — 0.05 rad/frame at 60fps = 3 rad/s. That's a fairly tight turn. Fine.

But wait — the predator's speed is constant 3.5 while boids max at 2.45. The predator will catch up. Good.

Also, if the flock centroid is far away (n=0), it heads to the screen center.

One issue: when the predator is right in the middle of the flock, the centroid ≈ its own position, so dl ≈ 0 and the direction is unstable. Let's add a minimum: if dl < 60, keep the current heading (with slight noise). Let's handle:

```js
if (dl < 50){
  // keep going straight-ish
  dx = Math.cos(ch); dy = Math.sin(ch);
}
```
Wait, but we compute dx,dy before ch. Let me reorder: compute ch first.

Let me restructure:
```js
const ch = Math.atan2(pvy[p], pvx[p]);
let dx = tx - ppx[p], dy = ty - ppy[p];
let dl = Math.sqrt(dx*dx+dy*dy);
let th;
if (dl < 60){ th = ch + (Math.random()-0.5)*0.3; }
else { th = Math.atan2(dy, dx); }
```
Hmm, adding randomness each frame to the target angle creates jitter but the turn rate limit smooths it. Fine. Actually let's use a smooth noise instead. Or just `th = ch` when close. Simple.

Actually, when the predator is inside the flock and the centroid is near, it should keep going straight through. `th = ch` does exactly that. 

But then it might circle... no, it goes straight until it exits, then the centroid is behind it... hmm, then it would turn around. Actually after passing through, the centroid of boids within 300px is behind it, so it turns around 180°, limited by the turn rate → it makes a big loop. That's nice.

Hmm, with maxTurn 0.05 rad/frame, a 180° turn takes 63 frames ≈ 1 second. That's a tight loop. Fine.

Let's make maxTurn a bit smaller for smoother arcs: 0.035.

OK.

Now, one thing to verify: the boids flee from the predator, so the flock's centroid moves away, and the predator chases. Continuous action. 

Let me now also handle the initial predator placement: place them at opposite edges heading inward.

```js
for (let p=0;p<NUM_PRED;p++){
  const a = p*Math.PI + Math.PI*0.25;
  ppx[p] = W*0.5 + Math.cos(a)*W*0.42;
  ppy[p] = H*0.5 + Math.sin(a)*H*0.42;
  pvx[p] = -Math.cos(a)*3.5;
  pvy[p] = -Math.sin(a)*3.5;
}
```

Hmm, but the flock is centered at W/2, H/2 initially. The predators start at the edges and charge in. Good.

Now let's put it all together. Also handle `window.addEventListener('resize', resize)`.

On resize, positions should be scaled or clamped. Let's just clamp them into the new bounds.

Also, the label: `labelEl.textContent = N.toLocaleString('en-US')`.

Let me write the final render with predators.

Predator drawing:
```js
ctx.globalCompositeOperation = 'lighter';
for (let p=0;p<NUM_PRED;p++){
  const ang = Math.atan2(pvy[p], pvx[p]);
  ctx.save();
  ctx.translate(ppx[p], ppy[p]);
  ctx.rotate(ang);
  ctx.beginPath();
  ctx.moveTo(18, 0);
  ctx.quadraticCurveTo(4, 8, -12, 7);
  ctx.quadraticCurveTo(-7, 0, -12, -7);
  ctx.quadraticCurveTo(4, -8, 18, 0);
  ctx.closePath();
  ctx.shadowColor = 'rgba(255,140,50,0.95)';
  ctx.shadowBlur = 24;
  ctx.fillStyle = 'rgba(255,196,120,0.85)';
  ctx.fill();
  ctx.restore();
}
```

Hmm, with 'lighter' and shadowBlur, the shadow is composited with 'lighter' too. Should look glowy.

Actually there might be an issue: shadowBlur with globalCompositeOperation='lighter' — the shadow is drawn as part of the shape drawing, so it uses the current composite op. Fine.

Let me also add an inner bright core.

Also — should the predator be drawn with 'lighter'? Over the dark background, an additive orange will look bright and glowy. Yes.

Now let me double-check the fade: `ctx.globalAlpha = 0.19; ctx.fillStyle = bgGrad; ctx.fillRect(0,0,W,H);` with 'source-over'. Yes.

But careful: the ctx transform is DPR-scaled, so fillRect(0,0,W,H) in CSS px covers the whole canvas. Good.

Let me now write the final code.

One more consideration for performance: `pathArr[b].rect(...)` — 2000 rect calls across 5 paths. Path2D.rect is a method call; 2000 calls/frame is fine.

And 2000 `bx.drawImage` calls. Hmm. Let me reduce by drawing bloom sprites at a lower rate — every boid, but maybe I should test-reason: drawImage of a 20×20 canvas onto a small target. Chrome does maybe 100k/s... no, way more. Typical: ~50,000 simple drawImage calls per frame is achievable at 60fps? Actually, benchmarks show ~10-20k drawImage per frame at 60fps in Chrome for small images. 2000 should be ~1-2ms. Fine.

OK, writing it.

Let me also double check: `bx.setTransform(BSCALE,0,0,BSCALE,0,0)` then `bx.drawImage(sprite, x-7, y-7, 14, 14)` → destination in CSS px scaled by BSCALE → 14*0.4 = 5.6 device px in the bloom canvas. Good.

And clearing: I set the transform to identity, clearRect(0,0,bloom.width,bloom.height), then set the transform back. Good.

Alright. Also I should ensure `imageSmoothingEnabled` is true for the upscale (default true).

Let me write out the full file now.

Also add a subtle "light shaft" for atmosphere? Skip — keep it clean.

Let me reconsider the label text: "2,200 individuals". The requirement says "Include a small label with the number of individuals." Good.

Let me finalize the numbers: N = 2200. MAXSPEED 2.45.

Hmm, at 2.45 px/frame, a boid crosses a 1600px screen in 650 frames ≈ 11 seconds. That's a reasonable, graceful pace.

Let me write it.

Final check on the dt handling: `dt = (now-last)/16.667`, clamped to [0.1?, 3]. Actually if the tab is backgrounded, now-last could be huge → clamp to 3. Fine.

Also, first frame: last = performance.now() set before rAF. Fine.

Let me write out.

One more: I want the swarm to look like it's "twisting and splitting". With alignment + cohesion, you get that naturally. To enhance, I could add a slight curl-noise-ish force. Let's add a simple global swirl: a very weak force perpendicular to the velocity, varying with position via a sine field. That adds organic twisting.

```js
// gentle curl
const t = time*0.0004;
const curl = Math.sin(x*0.004 + t) * Math.cos(y*0.004 - t*0.7);
ax += -vyi * curl * 0.05;
ay += vxi * curl * 0.05;
```
Hmm, that adds a perpendicular force proportional to speed. Magnitude ~0.05*speed ≈ 0.12. Small but adds nice curving. Let's include it, it makes the flock more alive.

Actually, careful — this could destabilize. Keep it weak: 0.04.

Let's include with a slowly varying field.

OK, writing the final code now.

Actually one thing: I should double-check `pan[i]` is used in render but computed in update. Yes, computed in the update loop. Good.

Also in render I recompute speed from vx,vy. Fine.

Let me write it out.

const FILLS with alpha values.

Let me finalize and write.

For the count label, also maybe add "· murmuration" text. Keep it minimal: `2,200 individuals`.

Writing the code now.

let me write the resize function to also rebuild the grid arrays and reinit if W/H changed drastically.

```js
function resize(){
  const newW = window.innerWidth, newH = window.innerHeight;
  const oldW = W, oldH = H;
  DPR = Math.min(window.devicePixelRatio || 1, 1.5);
  W = newW; H = newH;
  canvas.width = Math.max(1, Math.floor(W*DPR));
  canvas.height = Math.max(1, Math.floor(H*DPR));
  canvas.style.width = W+'px';
  canvas.style.height = H+'px';
  ctx.setTransform(DPR,0,0,DPR,0,0);

  bgGrad = ctx.createLinearGradient(0, 0, 0, H);
  bgGrad.addColorStop(0.0, '#0a3446');
  bgGrad.addColorStop(0.35, '#062432');
  bgGrad.addColorStop(0.7, '#031420');
  bgGrad.addColorStop(1.0, '#01080e');

  bloom.width = Math.max(1, Math.round(W*BSCALE));
  bloom.height = Math.max(1, Math.round(H*BSCALE));

  cols = Math.max(1, Math.ceil(W/CELL));
  rows = Math.max(1, Math.ceil(H/CELL));
  const nCells = cols*rows;
  counts = new Int32Array(nCells);
  starts = new Int32Array(nCells+1);
  cursor = new Int32Array(nCells);
  items = new Int32Array(N);

  if (oldW > 0 && oldH > 0){
    const sx = W/oldW, sy = H/oldH;
    for (let i=0;i<N;i++){ px[i]*=sx; py[i]*=sy; }
    for (let p=0;p<NUM_PRED;p++){ ppx[p]*=sx; ppy[p]*=sy; }
  }
}
```

Careful: the first call sets oldW=1 (initial W=1). Let's initialize W=0,H=0 and check `if (oldW > 0)`.

Hmm, but on first call, positions haven't been initialized yet. Order: resize() then initBoids(). But resize scales positions if oldW>0 — on first call oldW=0, so skip. Good.

Then after resize, if oldW was 0, we init boids. Actually let's do:

```js
resize();
initBoids();
```
And on subsequent resizes, positions get scaled. Good.

Hmm, but if oldW>0 and we scale positions, velocities stay the same. Fine.

Wait — the initial W=1, H=1. In resize, oldW=1 > 0, so it would scale. Let me init W=0, H=0 instead and guard `if (oldW > 0)`.

OK.

Now writing the final answer.

Also: `canvas.getContext('2d', {alpha: false})` — with alpha:false, the canvas starts black. Our gradient fill covers it. Good.

One last consideration on the bloom: since the main canvas has alpha:false and we draw the bloom with 'lighter', fine.

Let me write out the complete file.

For the predator glow, I might also add a faint radial aura. Skip.

Final code:

Actually, I realize I should double check the `starts` array indexing in the neighbor loop: `starts[c]` to `starts[c+1]`. With starts having length nCells+1 and starts[nCells] = N. Good.

Let me write.

Also, I want to make sure the simulation looks good immediately — the boids start in a swirl. Good.

Writing now.

Oh wait, one more thing about `pan` — I use it in render for brightness. But `pan` is set in the update. Good.

Also, I should ensure the boids near a predator get a visual "flash". pan near 1 → br = 0.12 + t*0.88 + 1.0 → clamped to 1 → bucket 4 (white). Good.

Let me write the final HTML.

Also let's add `will-change: transform` or nothing. Fine.

Final answer below.