We need to create a single HTML file with canvas, flow field particles, self-implemented noise, palette shifting, additive blending, reset waves, resize handling, requestAnimationFrame timestamp.

Let me design:

1. Noise: implement a 3D simplex-ish or value noise with gradient? Simpler: implement classic Perlin noise (3D) with permutation table, seeded. That's fine. Or implement a smooth value noise with cubic interpolation — easier and fast enough. But "layered noise" (fBm) — use Perlin 3D + fBm octaves.

Let me write a Perlin 3D noise implementation manually (classic improved Perlin with permutation array of 512).

2. Flow field: angle = fbm(x*scale, y*scale, t*0.05) * TAU * 2 maybe plus another layer. Use domain warping: angle from noise of (x,y) plus noise offset.

3. Particles: a few thousand (say 3000-6000 depending on device). Each particle has position, velocity, life. Each frame: sample flow field, steer velocity toward flow direction, move, draw line from prev to current with additive blending. Fade trails by drawing a translucent black rect each frame? With additive blending, a fade with 'source-over' black fill with low alpha will gradually darken. But also we want "reset waves" to prevent saturation.

Approach: use a trail buffer: draw fading rect each frame with globalCompositeOperation='source-over' and low alpha black (e.g. rgba(0,0,0,0.03)). That gives trails. Then draw particles with 'lighter'.

Actually with additive blending particles accumulate; fading with black alpha keeps balance. Reset waves: occasionally a radial wave emanating from a random point that kills/reseeds particles and clears the trail in a ring... Simpler: a "reset wave" is a growing circle that, when it passes over particles, respawns them at random positions, and also paints a subtle darkening in a ring on the canvas to clear accumulated saturation.

Implementation of reset wave clearing: draw a radial gradient stroke with 'destination-out'? Or with 'multiply'? Using composite 'destination-out' with a soft radial ring that reduces alpha. That works: draw ring gradient with rgba(0,0,0,alpha) using destination-out to erase partially. Nice.

Alternatively, simply fade more aggressively in a ring. Let's do destination-out ring.

4. Palette: curated palette of colors, slowly shifting over time. E.g. palette array of hues; color for particle based on its position in flow field or its index plus time shift. Slowly shift through palette with interpolated hue.

Let's define palette as a set of RGB colors:
- deep indigo #1a1f4b? Actually for additive glow, saturated bright colors work well: 
  e.g. palette: ['#ff2d95','#ff7a3d','#ffd166','#3ddc97','#3d9bff','#a24bff'].

Slowly shifts over time: rotate through palette entries over time, and lerp between adjacent entries.

Better: define a set of 6 key colors and use time to rotate a hue offset... Let's do: color index = (i/n + t*0.02) % 1, then sample palette gradient with smooth interpolation. That gives slow shift.

Maybe also make palette evolve by shifting the whole palette's hue slowly with time. Keep it simple: palette stops, sample with wrapping interpolation, offset by time.

5. Canvas filling window and resize: handle resize by setting canvas.width = innerWidth * dpr, etc. On resize, we should preserve drawing? Just reset trail with fill black. Keep particles scaled.

Let's think about scale: with dpr up to 2, and 4000 particles drawing lines each frame — fine.

Performance: 4000 particles * 1 noise call with 4 octaves each = 16000 noise evals per frame. Perlin 3D is fine, ~ maybe 0.5ms per 16k? Should be OK. Actually 3D perlin with 4 octaves = 4 noise calls → 64k noise calls per frame at 4000 particles. That might be ~5-10ms. Let's reduce octaves to 3 and particles to ~2500-3500 based on screen area. Also can cache noise field on a grid and bilinear interpolate — that's a nice optimization: precompute a coarse grid of angles (e.g. 64x64 cells covering canvas) each frame, then particles sample bilinearly. That's much faster and still smooth. But the flow field evolving with noise requires grid recompute each frame — 64*64=4096 * 4 octaves = 16k noise calls, fine, and particles just do lookups. Hmm but grid resolution limits detail; 64x64 with bilinear is smooth enough and cheap. But detail: "intricate" flow field — grid 96x96 is fine.

Actually simpler: just do direct noise per particle but with 3 octaves and ~3000 particles. Let's estimate: Perlin3D ~ maybe 100ns each. 3000*3 = 9000 calls = ~1ms. Fine. Direct is simpler and allows infinite field detail. Let's do direct with 3 octaves and fbm.

But also we want each particle to steer gently (smoothed velocity), so the flow field sampling per frame per particle is just 1.

Let's do direct noise.

Particle count: adapt to screen: min(4000, max(1500, area/500)). For 1920x1080 = 2M/500 = 4000. Good.

6. Timeline within 30s: We want the composition to look great quickly. Start with particles already distributed and trails building. Fade rate: alpha ~0.04 per frame at 60fps gives trails lasting ~1s. Good.

Reset waves: first one at ~t=8s, then every ~7-10s.

Also maybe a slow zoom/rotation of the flow field so it evolves.

Let's write the noise.

Perlin 3D improved:

```js
const perm = new Uint8Array(512);
(function(){
  const p = new Uint8Array(256);
  for (let i=0;i<256;i++) p[i]=i;
  // seeded shuffle
  let seed = 1337;
  const rnd = ()=> (seed = (seed*1664525+1013904223)>>>0) / 4294967296;
  for (let i=255;i>0;i--){ const j = Math.floor(rnd()*(i+1)); const t=p[i]; p[i]=p[j]; p[j]=t; }
  for (let i=0;i<512;i++) perm[i]=p[i&255];
})();

function fade(t){return t*t*t*(t*(t*6-15)+10);}
function lerp(a,b,t){return a+(b-a)*t;}
function grad(hash,x,y,z){
  const h = hash & 15;
  const u = h<8 ? x : y;
  const v = h<4 ? y : (h===12||h===14 ? x : z);
  return ((h&1)===0?u:-u) + ((h&2)===0?v:-v);
}
function noise3(x,y,z){
  const X = Math.floor(x)&255, Y = Math.floor(y)&255, Z = Math.floor(z)&255;
  x -= Math.floor(x); y -= Math.floor(y); z -= Math.floor(z);
  const u = fade(x), v = fade(y), w = fade(z);
  const A = perm[X]+Y, AA = perm[A]+Z, AB = perm[A+1]+Z;
  const B = perm[X+1]+Y, BA = perm[B]+Z, BB = perm[B+1]+Z;
  return lerp(
    lerp(lerp(grad(perm[AA],x,y,z), grad(perm[BA],x-1,y,z), u),
         lerp(grad(perm[AB],x,y-1,z), grad(perm[BB],x-1,y-1,z), u), v),
    lerp(lerp(grad(perm[AA+1],x,y,z-1), grad(perm[BA+1],x-1,y,z-1), u),
         lerp(grad(perm[AB+1],x,y-1,z-1), grad(perm[BB+1],x-1,y-1,z-1), u), v),
    w);
}
```

Note perm indices: perm[A+1] where A = perm[X]+Y can be up to 255+255=510, and AA = perm[A]+Z up to 255+255 = 510, AA+1 = 511 — within 512. Good.

fbm:
```js
function fbm(x,y,z){
  let s=0, a=0.5, f=1;
  for(let i=0;i<3;i++){ s += a*noise3(x*f, y*f, z*f); f*=2; a*=0.5; }
  return s;
}
```
Range roughly -1..1 (sum of amplitudes 0.875 -> ~ ±0.875).

Flow angle: 
```
const scale = 0.0018; // in device px
const t = time*0.05;
let n = fbm(x*scale, y*scale, t);
// domain warp
let n2 = fbm(x*scale*0.4 + 5.2, y*scale*0.4 - 3.1, t*0.7);
angle = n * Math.PI * 2.6 + n2 * Math.PI * 1.4;
```
Hmm, that's 6 noise calls per particle per frame (2 fbm × 3 octaves). 3000 particles → 18k noise calls. Still probably ~2-3ms. Acceptable. Maybe reduce to 2 octaves each? Let's keep 3 octaves for first fbm and 2 for warp. Or just one fbm plus a slow rotation based on position. Let's keep it moderate.

Alternative: compute a coarse vector field once per frame on a grid and bilinear sample. This gives clean performance and allows more octaves. Let me do this — it's more "flow field" authentic too.

Grid: cell size ~32 px in CSS pixels → for 1920 wide, 60x34 = 2040 cells. Each cell: 2 fbm calls with 3 octaves = 6 noise → 12k noise calls per frame. Then particles do 4 lookups + lerp. Cheap. And we can upsample smoothly.

But grid cell 32px means flow features vary over 32px — that's fine visually for particles; trails are smooth because of steering.

Hmm, but bilinear interpolation of angle is problematic (angle wrapping). Better: interpolate the vector components (cos, sin) — store cos and sin arrays, bilinear interpolate both. That's clean.

Let's do grid with cellSize = 24 css px, and grid dims = ceil(w/cs)+2. Recompute each frame. For a 1920x1080 screen: 80x45 = 3600 cells × 6 noise = 21.6k noise calls. OK.

Actually maybe simpler and sufficient: direct per-particle noise. Let me just weigh: per-particle with 2 fbm of 2 octaves = 4 noise calls × 3000 = 12k. That's actually fewer than the grid and simpler code. And gives infinite detail. Let's go direct.

Decision: direct noise per particle, fbm with 3 octaves for main and 2 for warp → 5 noise calls per particle. At 3000 particles = 15k noise calls/frame. Should be ~1-2 ms in modern JS. Fine.

Actually let's simplify: use one fbm (3 octaves) for angle, plus a large-scale rotation term:
```
let ang = fbm(x*s, y*s, z) * Math.PI * 2.4;
```
Plus slow global rotation with radius: ang += (something). Hmm, domain warp gives more interesting structure. Let's include warp with 2 octaves.

OK.

7. Particle update:
Each particle: x, y, vx, vy, speed, life, maxLife, color index, hue offset.

Steering: 
```
const a = flow(x,y,t);
const fx = Math.cos(a), fy = Math.sin(a);
vx += (fx*speed - vx) * 0.12;
vy += (fy*speed - vy) * 0.12;
x += vx * dt; y += vy*dt;
```
Use dt normalized to 60fps to be frame-rate independent: dt = min(frameDelta/16.667, 3).

Draw line from prev to new with color.

Life: particle has life decreasing; when it dies or goes off screen, respawn at random position (or at a random point near the field's high-flow regions). Respawn positions: random over canvas, maybe biased to a random point for bursts. Keep simple: random uniform over canvas, with a fraction spawning from random "seed points" to create structures.

Colors: each particle gets a palette position p (0..1) assigned at spawn, plus time-based offset. Compute color via palette sampling. To reduce per-particle cost, precompute a LUT of palette colors (say 256 entries) and update LUT each frame with the time shift. Then particle color = LUT[(idx + timeOffset) & 255]. That's efficient and gives slowly shifting palette.

Palette LUT: 256 entries, RGB strings? Building 256 rgba strings per frame is fine (256 string concatenations/frame). Or store as Float arrays and use `ctx.strokeStyle = 'rgba(...)'` per particle — that's expensive with 3000 particles building strings. Better: quantize colors—use a set of ~32 color strings and group particles by color? That would require sorting/batching. Hmm.

Alternative: batch strokes by color bucket. Each frame, for each of N color buckets, begin path, add all segments of particles in that bucket, stroke once. Requires bucketing particles each frame. With 3000 particles and 24 buckets, we can bucket by color index. Since color index changes with time offset (rotating), the bucket of a particle changes each frame. We can just compute bucket = (p.colorPos*BUCKETS + timeShift) | 0 modulo BUCKETS.

Then for each bucket: ctx.strokeStyle = colorStr[bucket]; ctx.beginPath(); loop over particles in that bucket... but that requires iterating particles once per bucket (BUCKETS × N). 24 × 3000 = 72k iterations, fine but we'd need to store per-particle segment. Alternative: build arrays of segments per bucket each frame — but arrays allocations.

Better approach: keep particles sorted? Simpler approach: just do per-particle stroke with cached color strings. Building a string per particle: 3000 string creations per frame — that's actually OK-ish but adds GC pressure. Hmm.

Alternative: use a precomputed palette array of, say, 64 rgb strings, and change strokeStyle only when the bucket changes. If we bucket particles by color at spawn and keep color mostly fixed... but we want palette to shift over time. We could instead shift the palette by rotating the LUT assignment slowly, and assign hues at spawn — but then strokes would be per-particle again.

Compromise: Assign each particle a fixed color index in [0, P) at spawn. The palette LUT of P colors slowly shifts over time (recomputed each frame, P = 48 strings). Then sort particles by color index? Particles don't change bucket, so we can maintain P arrays (buckets) of particles, and each frame iterate buckets and stroke each bucket's segments.

But wait — if colors are fixed per particle, the "palette slowly shifts over time" means the whole image's color mapping shifts: particle with index i shows LUT[(i + shift) % P]. If particles are bucketed by i, then bucket i uses color LUT[(i+shift)%P]. So we can still batch by fixed buckets! Each bucket i has a list of particle indices; strokeStyle = LUT[(i+shift)%P]. 

So: maintain P = 32 buckets, each bucket holding particle indices (particle has bucket i assigned at spawn, chosen based on position in field or randomly). Each frame, for bucket b: set strokeStyle to LUT[(b + shift) % P], begin path, for each particle in bucket, moveTo(prev), lineTo(cur), stroke.

Wait, but each particle has different alpha/width maybe. Keep uniform alpha per bucket, or vary line width slightly by bucket. Fine.

But the particle lists: particles get respawned but keep their bucket, so lists stay static. Good. However, we need to iterate buckets containing particle objects; the segment endpoints must be computed. We could precompute per particle prev/current, then loop.

Implementation: 
```
particles: array of objects {x,y,px,py,vx,vy,speed,life,maxLife,bucket}
buckets: array of arrays of particle indices (static assignment).
```
Each frame: update all particles (compute new x,y, store px,py). Then for each bucket, stroke paths.

Path building: for each particle, path.moveTo(px,py); path.lineTo(x,y); — separate subpaths so no connecting lines. Using moveTo/lineTo per particle within one path is fine.

Actually, for continuous trails, drawing a single line segment per frame per particle with the trail fade creates the ribbon look. Good.

Line width: 1.0-1.6 px scaled by dpr? Set ctx.lineWidth = baseW; with a few different widths per bucket maybe.

Alpha: use rgba colors with alpha ~0.35-0.6 for soft glow. With 'lighter' composite, overlapping builds up.

Also add a glow: draw with shadowBlur? Too expensive. Instead, rely on additive accumulation and maybe draw each segment twice: once thin bright, once wider dim. That doubles cost. Alternatively use ctx.lineWidth = 2 and low alpha with additive → soft glow look. I'll do lines with lineWidth ~1.8*dpr and alpha ~0.5, plus a second pass for a subset? Let's keep single pass but with rounded caps and a slightly larger blurred look achieved by... hmm.

A cheaper glow: draw the whole thing to the main canvas with 'lighter'; the trail persistence (fade) already creates glow halos. I think it'll look good.

Optionally, do a downsampled blur pass: draw the canvas onto itself scaled down and back with low alpha — that's a real bloom. Could be expensive but doable: create an offscreen canvas at 1/4 size, each frame draw main canvas into it (downscale), then draw it back onto main with 'lighter' and alpha 0.25 with imageSmoothing. That's 2 drawImage calls per frame — cheap and gives real bloom. Nice. Let's include a subtle bloom.

Hmm, but drawing the trail canvas into the bloom canvas includes the trails, yes. That amplifies glow. Let's do it with alpha ~0.18.

Careful: the downscale draw uses imageSmoothingEnabled true, which blurs. Good.

Order per frame:
1. Fade: ctx.globalCompositeOperation='source-over'; ctx.fillStyle='rgba(4,2,10,0.045)'; fillRect.
   Actually the background should be dark. Fading with a dark color instead of pure black gives a tinted background. Use rgba(6,3,14,0.05).
2. Reset wave handling: if active, apply destination-out ring.
3. Bloom pass: draw bloomCanvas onto main with 'lighter'.
   Wait: order matters. Bloom should be computed from the current state (with trails). Doing it before drawing new segments gives glow lagging by one frame — fine.
   Actually better order: fade → draw new particles (lighter) → bloom (downscale from main, draw back with lighter). Let's do: fade, draw particles, then bloom pass.
4. Reset waves.

For the fade + bloom, ensure alpha accumulation doesn't blow out — the fade handles it.

Reset wave: a ring expanding from a random point. Effect: 
- erase ring on canvas via destination-out with radial gradient (soft ring).
- particles whose distance from center is within the ring band get respawned (killed → respawned at random position with new velocity) — creating a "wave" of fresh particles.

Actually, a nicer effect: the wave pushes particles outward and respawns those it passes. Let's just respawn them and rely on the erase.

Wave timing: first wave at t≈7s, then every ~8-11s.

Also maybe multiple waves at once occasionally.

8. Time handling: use requestAnimationFrame timestamp. rAF gives ms. dt = (now - last)/1000. Clamp.

9. Sizing: 
```
function resize(){
  const dpr = Math.min(devicePixelRatio||1, 2);
  canvas.width = Math.floor(innerWidth*dpr);
  canvas.height = Math.floor(innerHeight*dpr);
  canvas.style.width = innerWidth+'px';
  ...
  ctx.setTransform(dpr,0,0,dpr,0,0); // work in CSS px
}
```
But width/height change resets canvas content. Fill with background.

Work in CSS px coordinates for particles: W = innerWidth, H = innerHeight. Flow field scale relative to min(W,H)? Use scale = 1/ (Math.min(W,H)*0.6)? Let's define scale = 1.6 / Math.min(W,H) * something. Let's think: noise coordinate = x * scale. We want features about 1/4 of the screen. scale ≈ 3/minDim. E.g. minDim=800 → scale 0.00375, features ~ 267px. Good.

Particle speed: ~1.2 px/frame in CSS px? For nice trails maybe 1.5-2.5 px/frame. Let's use speed 60-140 px/sec, dt in seconds → 1-2.3 px/frame at 60fps. Good.

Life: 4-12 seconds.

10. Seeding: initial particles distributed randomly, and they spread out. Fine.

Let's also add a subtle initial burst: particles start at random positions.

Number of colors P = 24 or 32 buckets.

Palette design: a curated palette, e.g.:
```
const PALETTE = [
  [255, 61, 129],   // pink
  [255, 138, 76],   // orange
  [255, 214, 102],  // gold
  [110, 231, 183],  // mint
  [56, 189, 248],   // sky
  [129, 140, 248],  // indigo
  [192, 132, 252],  // violet
  [244, 114, 182],  // rose
];
```
Then build LUT of 256 entries by interpolating around the loop (cyclic). Actually we need LUT size ≥ number of buckets (32) plus rotation. Use LUT of 48? Let's build a LUT of size 64 for buckets and rotate by shift. Hmm, rotating the LUT: LUT[(b + shift) % LUTN] where shift changes over time. If LUTN == buckets = 32, then it's a cyclic rotation of the palette. Good — that gives a slow hue drift and periodic cycling.

But we also want more than 32 buckets maybe for smoother color variety. Let's use 48 buckets and LUT of 48, cycling with time. Buckets of ~3000/48 = 62 particles each. Fine.

Rotation speed: shift advances by ~1 every 1.5 seconds? With 48 buckets, full cycle = 72 s. Hmm, "slowly shifts over time" — good. But also want to see color variety within first 30 seconds. Since the base palette is already colorful and bucket assignment spreads across the palette, we see all colors immediately. The rotation just shifts which particle has which color. Good.

Also we could slowly change the palette itself by modulating saturation/brightness with time. Maybe a slow hue rotation applied to the palette LUT: converting to HSL and rotating hue. Let's keep it simple: build LUT each frame from the palette with a global hue-ish rotation? That's 48 conversions per frame — cheap. Actually let's do: LUT[i] = mix(PALETTE, i/48) then apply a slow hue rotation of e.g. sin(time*0.05)*20 degrees. Converting RGB→HSL→RGB for 48 colors per frame × 60fps = 2880 conversions/sec. Fine.

Hmm, might be overkill. Simpler: just rotate the palette position by time (which we do via shift) — the shift itself is the slow palette shift. Plus a slow "warmth" modulation. Let's just do the shift plus a subtle brightness pulse. Keep it simple, less code.

Actually, to make colors "shift", I could also add the time-based shift in the LUT building: LUT[i] sampled at ((i/LUTN) + t*0.02) % 1 so colors drift smoothly and continuously rather than in discrete bucket steps. Combined with per-bucket assignment... no, that's the same as shifting the bucket's color. Let's just do: for each bucket b, color = samplePalette((b/NB + timeShift) % 1). timeShift = t*0.015. So a full cycle every 66s. Good — do it directly per bucket, no LUT needed (48 samples per frame).

samplePalette(u): u in [0,1) → find position in PALETTE array of length M: f = u*M; i = floor(f); frac = f-i; lerp between PALETTE[i%M] and PALETTE[(i+1)%M].

Good.

Now, alpha per bucket: vary a bit, e.g. alpha = 0.45 + 0.25*sin(b). Fine.

Also lineWidth per bucket: 1.2 + 1.2*((b%3)/2)? Slight variety.

Let's write code.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Flow Field Bloom</title>
<style>
  html,body{margin:0;padding:0;height:100%;background:#05030c;overflow:hidden;}
  canvas{display:block;width:100vw;height:100vh;}
</style>
</head>
<body>
<canvas id="c"></canvas>
<script>
(() => {
'use strict';
// ---------- Perlin noise (classic 3D, self-contained) ----------
...
})();
</script>
</body>
</html>
```

Now the JS details.

```js
// Seeded PRNG for permutation
let __s = 20240613;
function rand(){ __s = (__s*1664525 + 1013904223) >>> 0; return __s / 4294967296; }

const perm = new Uint8Array(512);
{
  const p = new Uint8Array(256);
  for (let i=0;i<256;i++) p[i]=i;
  for (let i=255;i>0;i--){ const j=(rand()*(i+1))|0; const t=p[i]; p[i]=p[j]; p[j]=t; }
  for (let i=0;i<512;i++) perm[i]=p[i&255];
}
```

Noise functions as above.

fbm:
```js
function fbm(x,y,z,oct,lac,gain){
  let a=0.5, f=1, s=0, n=0;
  for(let i=0;i<oct;i++){
    s += a*noise3(x*f, y*f, z*f);
    n += a;
    f *= lac; a *= gain;
  }
  return s/n; // normalized to about -1..1
}
```

Flow:
```js
function flowAngle(x, y, t){
  const s = SCALE; // dynamic
  const q = fbm(x*s + 11.3, y*s - 4.7, t*0.11, 2, 2, 0.5);
  const r = fbm(x*s - 7.1, y*s + 9.4, t*0.09 + 5, 2, 2, 0.5);
  const n = fbm(x*s + q*0.9, y*s + r*0.9, t*0.07, 3, 2.1, 0.5);
  return n * Math.PI * 2.6;
}
```
That's 2+2+3 = 7 noise calls per particle. At 3000 particles → 21k noise/frame. Might be ~2-4 ms. Hmm. Let's reduce: warp with 1 octave each (2 calls) + main 3 octaves = 5 calls. Or use scale-cached grid.

Let me consider capping particle count at ~2600 for large screens. Then 2600*7 = 18k noise calls. Each noise3 call in JS maybe ~150-250ns with Math.floor etc. 18k × 200ns = 3.6ms. Plus rendering. Might be ~8-10ms total. Acceptable at 60fps but tight on slower machines.

Alternative: precompute flow grid each frame. Grid of 1 cell per 20 CSS px: 1920/20=96, 1080/20=54 → 5184 cells × 7 noise = 36k noise calls. Worse.

Hmm, the grid only helps if particle count is much larger than cell count. Not our case. So direct per-particle is better.

Optimize noise3: avoid Math.floor for known ranges? Use `|0` when values are positive and within int range. Math.floor(x) where x can be negative... Use `Math.floor` — it's fast-ish.

Alternative: use a cheaper value-noise with a hash function and smoothstep. Value noise with smooth interpolation is much faster (no gradient dot products). fbm of value noise can look decent for flow fields since we only care about smooth direction. Actually for the flow direction, we need smooth, continuous, "organic" fields. Value noise trilinear with 3D hash could be fine and maybe 2x faster.

Let's implement a 3D value noise with a hash:
```js
function hash3(x,y,z){
  let n = x*374761393 + y*668265263 + z*1274126177;
  n = (n ^ (n >>> 13)) * 1274126177;
  return ((n ^ (n >>> 16)) >>> 0) / 4294967296;
}
```
Using Math.imul for multiplication to avoid float issues.

```js
function hash3(x,y,z){
  let n = Math.imul(x, 374761393) ^ Math.imul(y, 668265263) ^ Math.imul(z, 1274126177);
  n = Math.imul(n ^ (n >>> 13), 1274126177);
  return ((n ^ (n >>> 16)) >>> 0) / 4294967296;
}
```
Value noise:
```js
function vnoise(x,y,z){
  const xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z);
  const xf = x-xi, yf = y-yi, zf = z-zi;
  const u = xf*xf*(3-2*xf), v = yf*yf*(3-2*yf), w = zf*zf*(3-2*zf);
  const c000 = hash3(xi,yi,zi), c100 = hash3(xi+1,yi,zi), ...
  // trilinear
}
```
That's 8 hash calls per noise sample — worse than Perlin's 8 gradient lookups but hash is arithmetic heavy. Hmm, Perlin uses table lookups (fast). Perlin is probably fine.

Let's just use Perlin. It's classic and fast enough.

Actually, we can also reduce work: sample noise in 2D+time but that's what we're doing.

Let's just go with Perlin, 3 octaves main + 2 octaves warp with 1 octave each? Let me define:

```js
function field(x, y, z){
  const w1 = noise3(x*0.6 + 3.1, y*0.6 - 1.7, z*0.5);
  const w2 = noise3(x*0.6 - 8.3, y*0.6 + 5.9, z*0.5 + 13.7);
  return fbm(x + w1*1.2, y + w2*1.2, z, 3);  // 3 octaves
}
```
5 noise calls. Good. Where x,y are already scaled by SCALE.

Hmm, note fbm with 3 octaves where each octave multiplies frequency — fine.

Let me write `flowAt(x,y,t)` returning angle:
```js
function flowAngle(x, y, t){
  const sx = x*SCALE, sy = y*SCALE;
  const w1 = noise3(sx*0.7 + 3.1, sy*0.7 - 1.7, t*0.12);
  const w2 = noise3(sx*0.7 - 8.3, sy*0.7 + 5.9, t*0.12 + 13.7);
  const n = fbm(sx + w1*1.1, sy + w2*1.1, t*0.09, 3);
  return n * Math.PI * 3.0;
}
```
fbm returns normalized sum (divide by total amplitude) → range ±1 approx. Multiply by 3π gives ±540°, which wraps — a bit chaotic. Let's use Math.PI*2.2 ≈ 400°. Actually since angle wraps mod 2π, using a large multiplier creates discontinuities where the noise crosses the wrap boundary — those create sharp direction changes but the vector is still continuous in direction? No: angle jump of 2π is continuous in direction. Since direction is what matters, any multiple works as long as the angle is continuous. So n*Math.PI*2.5 is fine — direction varies smoothly.

Hmm but the steering interpolates velocity toward the target direction; a discontinuity would matter only if the angle jumps by something not a multiple of 2π, which doesn't happen. Good.

Now, particles.

```js
const NB = 48; // color buckets
let particles = [];
let buckets = []; // arrays of particles
```

Particle as a plain object or typed arrays? Objects are simpler; 3000 objects is fine.

```js
function makeParticle(p){
  p.x = Math.random()*W;
  p.y = Math.random()*H;
  p.vx = 0; p.vy = 0;
  p.speed = 45 + Math.random()*95;  // px per second
  p.life = 0;
  p.maxLife = 3 + Math.random()*9;
  p.px = p.x; p.py = p.y;
  return p;
}
```
Spawn: initial spawn positions should cover the canvas. But a nice effect is spawning along a few "seed" arcs. Let's just do uniform random for initial and respawns, with occasional spawn near a random point.

Actually to make the composition interesting, particles could spawn near the center or along lines. Uniform is fine with flow field organizing them.

Let's add: 25% of respawns near a random "focus point" that changes every few seconds, to create denser regions. Meh — keep it simpler: uniform random.

Hmm, but the flow field advects them, so structures emerge anyway.

Rendering loop:

```js
function frame(now){
  requestAnimationFrame(frame);
  ...
}
```

Note: "Use the requestAnimationFrame timestamp for time." So use `now` from rAF.

dt = (now - last)/1000, clamp to 0.05 (avoid huge jumps after tab switch). Also if the tab was hidden, dt clamp prevents explosion.

Time t = now/1000.

Update:
```js
const tsec = now * 0.001;
for (const p of particles){
  const a = flowAngle(p.x, p.y, tsec);
  const tx = Math.cos(a) * p.speed;
  const ty = Math.sin(a) * p.speed;
  const k = 1 - Math.pow(0.001, dt); // smoothing? 
```
Simpler: k = 0.12 * dt*60 clamped.
```js
  const k = Math.min(1, 3.2*dt);
  p.vx += (tx - p.vx)*k;
  p.vy += (ty - p.vy)*k;
  p.px = p.x; p.py = p.y;
  p.x += p.vx*dt;
  p.y += p.vy*dt;
  p.life += dt;
  if (p.life > p.maxLife || p.x < -50 || p.x > W+50 || p.y < -50 || p.y > H+50) respawn(p);
}
```
With k = 3.2*dt (dt≈0.0167 → k≈0.053) that's smooth steering. Good.

Hmm, initial velocity 0 → they accelerate. Fine.

Respawn resets px,py = x,y so no long line across.

Drawing:
```js
ctx.globalCompositeOperation = 'lighter';
ctx.lineCap = 'round';
ctx.lineJoin = 'round';
for (let b=0; b<NB; b++){
  const col = paletteColor((b/NB + tsec*0.017) % 1);
  ctx.strokeStyle = col;
  ctx.lineWidth = widths[b];
  ctx.beginPath();
  const list = buckets[b];
  for (let i=0;i<list.length;i++){
    const p = list[i];
    ctx.moveTo(p.px, p.py);
    ctx.lineTo(p.x, p.y);
  }
  ctx.stroke();
}
```
That's 48 stroke calls with ~60 segments each. Fine.

Wait — p.px/p.py for respawned particles is set to p.x/p.y so the line is degenerate (moveTo==lineTo) which draws nothing (or a dot with round cap? A zero-length line with round cap draws nothing in most browsers... actually with lineCap 'round', a zero-length subpath may render a dot in some implementations. Chrome: zero-length path with round linecap draws a circle? I believe per spec, a zero-length subpath with round caps does render a dot. That could be fine — a small dot.)

Color function:
```js
const PAL = [ [255,61,129], ... ];
function paletteColor(u){
  u = u - Math.floor(u);
  const f = u*PAL.length;
  const i = Math.floor(f);
  const fr = f - i;
  const a = PAL[i % PAL.length], b = PAL[(i+1)%PAL.length];
  const r = Math.round(a[0] + (b[0]-a[0])*fr);
  ...
  return `rgba(${r},${g},${b},${alpha})`;
}
```
Alpha per bucket: pass in.

Hmm — with 'lighter' and many overlapping strokes, alpha 0.5 gets bright quickly. Since the fade removes 4.5% per frame, steady state brightness ~ where addition = fade. Let's tune alpha ~0.35.

Actually let's think about the "glow" look. Additive blending of thin lines with a soft fade gives glowing filaments. Good.

Let's set alpha per bucket around 0.30-0.55 varying with bucket to add depth.

Line width: 1.0 to 2.4 CSS px. Slight variety.

Bloom: 
```js
bloomCtx.globalCompositeOperation = 'source-over';
bloomCtx.clearRect(0,0,bw,bh); // or just draw over with copy
bloomCtx.drawImage(canvas, 0,0, bw, bh);
// then
ctx.globalCompositeOperation = 'lighter';
ctx.globalAlpha = 0.22;
ctx.drawImage(bloomCanvas, 0,0, W, H);  // using transform in CSS px → but drawImage dest coords are in CSS px, source is the bloom canvas in device px. Fine.
ctx.globalAlpha = 1;
```
But careful: `ctx` has transform scale dpr. drawImage(canvas, 0,0,W,H) draws the full canvas scaled to W×H CSS px = device px, correct.

Bloom canvas size: Math.max(1, canvas.width>>2) x ... Let's use width/4, height/4.

Wait, drawing the main canvas down into the bloom canvas each frame, then drawing back, creates a feedback loop (bloom includes previous bloom). But since the fade reduces everything and bloom alpha is low, it should stabilize. Actually the bloom canvas is cleared each frame (drawImage with 'copy' or clearRect) so no accumulation there. But the main canvas receives bloom of itself → the bloom adds brightness which is then re-bloomed next frame. That's a feedback amplifier. With alpha 0.22 and fade 4.5%, could blow up. Let's set bloom alpha ~0.12 and rely on fade. Actually the fade multiplies by 0.955 each frame; bloom adds 0.12 of the current brightness: steady state B = 0.955B + 0.12B → 0.955+0.12 = 1.075 > 1 → unstable! It only converges if the sum of the retention factor and bloom factor < 1.

Hmm. 0.955 * (1+0.12) = 1.069 > 1. So bright areas grow unboundedly. Need to keep bloom small: alpha such that 0.955*(1+alpha) < 1 → alpha < 0.047. Let's use 0.035 or reduce fade retention.

Alternatively compute bloom from the particle layer only (before accumulation) — complex. Let's just use a small bloom alpha like 0.04 and increase fade slightly. Or skip bloom.

Hmm. Alternatively, use 'lighter' with bloom but subtract via a stronger fade. Let's compute: fade alpha per frame = 0.06 → retention 0.94. bloom 0.05 → 0.94*1.05 = 0.987 < 1. Converges. Good. Use fade 0.055 and bloom 0.045.

Trail persistence: retention 0.945 per frame → half-life ~12 frames (0.2s). That's a short trail. Hmm, that might be too short for "soft glowing trails that build up into intricate composition".

Let's reconsider: retention 0.94/frame → time constant ~16 frames → visible trail over ~0.5s. At speed 80px/s, that's a 40px trail. That's okay actually, but the "build up into intricate composition" wants longer persistence—like several seconds, where old trails linger dimly.

Alternative fade: use a lower alpha but with a nonlinear/quantized approach — e.g., fade only every other frame, or use a "fade pass" that multiplies by 0.99 but clamps... Can't easily do exponential decay without feedback.

Actually the issue: with retention 0.99, bright areas persist long, and additive lines saturate to white. To avoid white-out, use lower per-line alpha (like 0.15) and a shorter trail so the total accumulation balances. That's the standard approach: low alpha lines + moderate fade.

Let's use fade 0.035 (retention 0.965, half-life ~19 frames ~0.32s) and bloom 0.03 (0.965*1.03 = 0.994 < 1). Trail length at 80px/s ≈ 26px visible plus a fading tail. Hmm.

Honestly, the visual result is what matters: a fade of 0.03-0.05 per frame gives trails of a few hundred ms which look like flowing light streams. That reads as "soft glowing trails". Let's go with fade alpha 0.045 and skip the bloom feedback loop by computing the bloom from a separate "particle-only" render. Hmm, that would require rendering particles to an offscreen canvas and then compositing — doubles the drawing cost.

Alternative bloom without feedback: draw the bloom canvas from the main canvas BEFORE drawing new particles, then draw the particles. The bloom content is the faded trails (from the previous frame's accumulated state), and the bloom drawn back adds to the same buffer → still feedback.

Simplest: skip the extra bloom pass; instead achieve glow by drawing each particle segment twice: a wide, low-alpha pass and a narrow, higher-alpha pass. That's deterministic (no feedback) and gives a glow look. Cost: 2× path building. With 3000 segments, that's 6000 path ops — acceptable.

Actually we can do: for the glow pass, use lineWidth = 6 and alpha ~0.05; for the core pass, lineWidth = 1.6 and alpha ~0.3. Combined with additive accumulation this gives nice glow filaments.

Hmm, but doubling the stroke calls: 48 buckets × 2 = 96 strokes/frame with 3000 total segments each pass. Should be OK.

Let me reconsider — maybe just use a moderate bloom with tiny alpha (0.025) and fade 0.04: 0.96 * 1.025 = 0.984 < 1. That's stable and gives a soft overall glow. Plus the double-stroke approach for local glow. Maybe both is too much. Let's do: fade 0.04, double-stroke glow (width varies), and a subtle bloom pass with alpha 0.05 and the fade accounting: 0.96*1.05 = 1.008 > 1 — unstable. Use alpha 0.035: 0.96*1.035 = 0.9936. OK stable.

Hmm, but the bloom pass adds a broad soft glow that looks great. Let me include it with alpha 0.035. Actually, the bloom also blurs the dark background into... no, with 'lighter' it only adds brightness. Dark areas stay dark. Good.

But there's a subtlety: since the bloom is drawn with 'lighter' and the source includes the dark background (rgb ~ (6,3,14)), adding that at 3.5% alpha adds a tiny bit of brightness everywhere — negligible.

OK, let's finalize:
- fade: fillStyle 'rgba(5,2,12,0.045)' with source-over → retention 0.955 per channel... actually fillRect with alpha 0.045 of color (5,2,12) over the canvas: new = old*0.955 + 0.045*bgcolor. So retention 0.955 and it drifts toward bg color. Good.
- bloom alpha 0.03 → 0.955*1.03 = 0.984 < 1. Stable. 

Let's also make the fade slightly adaptive? No, keep constant.

Now reset waves: every ~9 seconds, spawn a wave at a random position. Wave expands at ~350 px/s. When it passes a particle (distance within [r-20, r+20]), respawn it. Also erase a ring on the canvas with 'destination-out' using a radial gradient ring with low alpha.

The destination-out ring: create a radial gradient centered at (cx,cy) from r-40 to r+40 with color stops:
- at 0: rgba(0,0,0,0)
- at 0.5: rgba(0,0,0,0.5)  (center of ring)
- at 1: rgba(0,0,0,0)
Draw with globalCompositeOperation='destination-out', filling an annulus region. Actually we can fill a rect covering the ring's bounding box with that gradient; the gradient is transparent outside [r-40, r+40]. Fill the whole canvas rect for simplicity (gradient fill of full rect is fine, cost is per-pixel but full canvas fill with a gradient each frame during a wave... acceptable, waves are brief).

Hmm, filling the whole canvas with a radial gradient each frame during a wave (about 2s) is fine.

But wait: with 'destination-out', a soft ring partially erases the trails, creating a visible clearing wave. Nice.

But if the wave erases too much, it looks like a hole. Alpha 0.5 at the ring center is strong; over multiple frames at the same pixel (ring passes quickly), it's about 1-2 frames of strong erasure. Fine.

Also, particles caught in the wave get respawned (teleported), so their trails break. Good.

Let's implement wave:
```js
class Wave { constructor(x,y,start){...} }
let waves = [];
function spawnWave(t){ waves.push({x: Math.random()*W, y: Math.random()*H, r: 0, t0:t, speed: 260 + Math.random()*220}); }
```
Update in frame:
```js
for (let i=waves.length-1;i>=0;i--){
  const w = waves[i];
  w.r += w.speed*dt;
  // erase ring
  ...
  // kill particles in the ring
  for (const p of particles){
    const d = Math.hypot(p.x-w.x, p.y-w.y);
    if (Math.abs(d - w.r) < 18) respawn(p);
  }
  if (w.r > Math.hypot(W,H)) waves.splice(i,1);
}
```
Hypot for every particle per frame per wave is expensive: 3000 × hypot per wave. Math.hypot is slow. Use dx*dx+dy*dy < r2 and > r2inner computed per particle. Let's precompute rIn = w.r-18, rOut = w.r+18, then compare squared distances. That's 3000 iterations per wave — cheap enough (only during active waves).

Actually, we can integrate this into the main particle loop: for each particle, check against active waves. Simpler to just do a separate loop when waves.length > 0.

Timing: first wave at t=6s, then every 7-10s.

Let's define wave schedule: nextWaveAt = 6; in frame: if (tsec > nextWaveAt) { spawnWave(); nextWaveAt = tsec + 7 + Math.random()*5; }

Maybe occasionally spawn 2 waves at once (when tsec > 25, every other wave spawns a pair). Keep simple: one sometimes two.

Now particle count and performance: choose N based on screen area and dpr:
```js
const area = W*H;
const N = Math.round(Math.min(3400, Math.max(1200, area/620)));
```
1920×1080 = 2,073,600 / 620 = 3345 → capped 3400. On a 3840×2160 screen → capped at 3400. Hmm, for larger screens maybe more particles but capped for perf. Fine.

Actually device pixels matter for fill rate, not just CSS. On a retina 1440p CSS (2880 device px), 3400 particles drawing lines... fine.

Let's set N = clamp(area/700, 1000, 3200).

On resize, keep particles; respawn out-of-bounds ones.

Now let's write the drawing of particle trails with the glow pass:
```js
for (let b=0;b<NB;b++){
  const list = buckets[b];
  if (!list.length) continue;
  const boost = 0.75 + 0.5*Math.sin(tsec*0.6 + b*0.7); // breathing
  // glow pass
  ctx.strokeStyle = paletteColor(((b/NB) + shift)%1, 0.06*boost);
  ctx.lineWidth = widths[b]*4;
  ctx.beginPath();
  for (...) { moveTo, lineTo }
  ctx.stroke();
  // core pass
  ctx.strokeStyle = paletteColor(..., 0.42*boost);
  ctx.lineWidth = widths[b];
  ctx.beginPath(); ...
  ctx.stroke();
}
```
Hmm, this doubles path building. The path building (moveTo/lineTo) is likely the most expensive part. Alternative: build the path once, stroke it twice? A Path2D object can be stroked multiple times! Use Path2D per bucket:

```js
const path = new Path2D();
for each particle: path.moveTo(...); path.lineTo(...);
ctx.lineWidth = w*4; ctx.strokeStyle = glowColor; ctx.stroke(path);
ctx.lineWidth = w; ctx.strokeStyle = coreColor; ctx.stroke(path);
```
Creating 48 Path2D per frame — allocation but OK. Path2D construction cost similar to context path building. And stroking twice re-rasterizes the path twice anyway (the expensive part is rasterization, not path construction). Hmm.

Rasterization cost: 3000 thin lines × 2 passes = 6000 line rasterizations. Plus wide glow lines = 4px wide × 3000 lines. At 60fps this could be heavy on large canvases. Let's reduce the glow width to 3× and only do the glow pass... Actually, let's think about total fill: 3000 segments × avg 2px length... wait, segments are the per-frame movement: ~1.3px at 80px/s and 60fps. So each line segment is ~1.3px long and 4px wide → ~5-6px² → 3000 × 6 = 18k px per pass. Tiny! Rasterization cost is dominated by per-segment setup, not pixel count. 6000 segments per pass... 12000 total segments per frame. That's fine for modern browsers (they handle ~100k+ segments/frame).

Hmm, but wait: very short segments with round caps → effectively dots. Good.

OK so double-stroke is fine.

Actually, there's a subtlety: consecutive frames' segments connect if the particle moves continuously, forming a smooth line. With round caps, the joints look fine.

Let's just go with Path2D? Or direct ctx path? Direct is fine: build path, stroke, then rebuild? No — we can't stroke twice without rebuilding unless Path2D. Let's use Path2D to avoid rebuilding. Actually rebuilding is just moveTo/lineTo calls, cheap-ish. But Path2D is cleaner. Let's use Path2D.

Memory churn: 48 Path2D per frame × 60fps = 2880 objects/s. Fine.

Hmm, actually building a Path2D and stroking it twice: does Chrome re-rasterize for each stroke? Yes. Same cost as two paths. OK.

Let's now write the whole thing.

Also there's the initial state: canvas filled with background color.

Let me also add a subtle vignette? Not necessary. Maybe a radial dark gradient overlay drawn occasionally? Skip.

One more consideration: "thousands of particles" — we have ~3000. Good.

"layered noise (implement the noise yourself)" — Perlin fbm with domain warping. Good.

Let's write the code carefully.

```js
(function(){
  'use strict';

  // ==== Seeded PRNG ====
  let seed = 987654321;
  function rnd(){ seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; }

  // ==== Perlin 3D ====
  const perm = new Uint8Array(512);
  (function(){
    const p = new Uint8Array(256);
    for (let i=0;i<256;i++) p[i]=i;
    for (let i=255;i>0;i--){ const j=(rnd()*(i+1))|0; const t=p[i];p[i]=p[j];p[j]=t; }
    for (let i=0;i<512;i++) perm[i]=p[i&255];
  })();

  function fade(t){ return t*t*t*(t*(t*6-15)+10); }
  function lerp(a,b,t){ return a+(b-a)*t; }
  function grad(h,x,y,z){
    switch(h & 15){
      case 0: return  x+y; case 1: return -x+y; case 2: return  x-y; case 3: return -x-y;
      case 4: return  x+z; case 5: return -x+z; case 6: return  x-z; case 7: return -x-z;
      case 8: return  y+z; case 9: return -y+z; case 10:return  y-z; case 11:return -y-z;
      case 12:return  x+y; case 13:return -y+z; case 14:return -x+y; default: return -y-z;
    }
  }
  function noise3(x,y,z){
    const X = Math.floor(x) & 255, Y = Math.floor(y) & 255, Z = Math.floor(z) & 255;
    x -= Math.floor(x); y -= Math.floor(y); z -= Math.floor(z);
    const u = fade(x), v = fade(y), w = fade(z);
    const A = perm[X] + Y, AA = perm[A] + Z, AB = perm[A+1] + Z;
    const B = perm[X+1] + Y, BA = perm[B] + Z, BB = perm[B+1] + Z;
    return lerp(
      lerp(lerp(grad(perm[AA],x,y,z), grad(perm[BA],x-1,y,z), u),
           lerp(grad(perm[AB],x,y-1,z), grad(perm[BB],x-1,y-1,z), u), v),
      lerp(lerp(grad(perm[AA+1],x,y,z-1), grad(perm[BA+1],x-1,y,z-1), u),
           lerp(grad(perm[AB+1],x,y-1,z-1), grad(perm[BB+1],x-1,y-1,z-1), u), v),
      w);
  }
```
Note: perm[A+1] where A can be up to 510 → A+1 = 511, ok. perm index up to 511. Good.

fbm:
```js
  function fbm(x,y,z,oct){
    let amp = 0.5, freq = 1, sum = 0, norm = 0;
    for (let i=0;i<oct;i++){
      sum += amp * noise3(x*freq, y*freq, z*freq);
      norm += amp;
      freq *= 2.03;
      amp *= 0.5;
    }
    return sum / norm;
  }
```

Field:
```js
  let SCALE = 0.0022;
  function flowAngle(x, y, t){
    const sx = x*SCALE, sy = y*SCALE;
    const w1 = noise3(sx*0.55 + 3.7, sy*0.55 - 2.3, t*0.10);
    const w2 = noise3(sx*0.55 - 9.1, sy*0.55 + 6.4, t*0.10 + 21.7);
    const n = fbm(sx + w1*1.4, sy + w2*1.4, t*0.075, 3);
    return n * 6.2;
  }
```
n in [-1,1] → angle in [-6.2, 6.2] rad ≈ ±355°. Fine.

Wait, careful: `t*0.075` as the z coordinate — z changes slowly, giving slow evolution. Good.

SCALE: 0.0022 with min dimension 800 → noise feature ~1/0.0022 = 454 px per noise unit. fbm's base octave varies over 1 unit → features of ~450px. Good.

But for small screens (mobile 375px wide), SCALE 0.0022 gives very large features relative to screen. Let's set SCALE = 2.2 / Math.min(W,H) ... For min=800: 0.00275. For min=375: 0.0059. Good — features scale with screen.

Hmm, but the z (time) coordinate should be scaled independently so it doesn't depend on screen size. Use t*0.09 constant.

Let's set `SCALE = 2.6 / Math.min(W,H)`.

Then for min=800 → 0.00325 → feature size ~300px. Good.

Now particles.

```js
  const canvas = document.getElementById('c');
  const ctx = canvas.getContext('2d', {alpha:false});
```
With alpha:false, the canvas is opaque and destination-out... will it work? With alpha:false, the canvas has no alpha channel; destination-out would make pixels black (transparent becomes black). Actually with alpha:false, compositing destination-out results in black. That works visually (erasing to black), since our background is dark. OK, but the fade fill would then... it's fine. Let's keep alpha:false for performance (avoids alpha compositing). Hmm, but the destination-out to black might look slightly different from the background color (5,2,12). Minor.

Actually let's just use the default (alpha true) to keep things predictable. Performance difference is minor. Use alpha: true (default) and fill background at start.

Wait, if alpha is true and we use 'destination-out' erasing, the canvas becomes transparent showing the page background (#05030c). That's consistent. But with 'lighter' blending on a transparent canvas, colors add onto transparent black. Then when composited over the page background, it looks fine. Hmm, but the bloom drawImage of a transparent canvas with 'lighter'... also fine.

Actually there's an issue: with a transparent canvas, the fade fillRect with rgba(5,2,12,0.045) accumulates alpha over time — after many frames the canvas alpha approaches 1 with color (5,2,12). Fine.

Let's use alpha: false for speed and simplicity, and set the fade color to the background. destination-out with alpha:false gives black — a slightly darker ring than bg (5,2,12). Barely noticeable. Hmm, but repeated waves would leave black smudges that never fully return to (5,2,12) — actually the fade fill pushes toward (5,2,12) over time, so it self-heals. Good.

I'll use alpha: false.

Hmm wait, one thing: with alpha:false, does 'lighter' work properly? Yes, additive on the RGB.

OK.

Bloom canvas: `document.createElement('canvas')` with ctx2. Its content: we drawImage the main canvas scaled down. Since the main canvas is opaque, the bloom is opaque dark. Drawing it back with 'lighter' at alpha 0.03 adds 3% of everything including the dark bg. Fine.

Let me reconsider whether the bloom is worth the complexity. It adds a nice soft glow. Keep it, it's ~6 lines.

Now, the main loop:

```js
  let last = 0, tsec = 0;
  let nextWaveAt = 5.5;
  const waves = [];

  function frame(now){
    requestAnimationFrame(frame);
    if (!last) last = now;
    let dt = (now - last) / 1000;
    last = now;
    if (dt > 0.05) dt = 0.05;
    if (dt <= 0) dt = 1/60;
    tsec = now / 1000;
    ...
  }
```

Note: `tsec` from rAF timestamp (which is relative to page load). Good.

Update particles, draw.

Then waves.

Then bloom.

Order:
1. Fade rect.
2. Waves update (erase rings + respawn particles near ring).
3. Particle update loop.
4. Draw buckets.
5. Bloom.

Wait, if we erase the ring before drawing particles, the new segments drawn after might immediately repaint over the erased ring — but the particles caught in the ring get respawned so they don't draw near the ring. Fine.

Let's write it.

Also the "shift" for the palette: `palShift = tsec * 0.02` → full palette cycle every 50s. Combined with bucket index.

Now alpha per bucket and width per bucket:
```js
const bucketWidth = new Float32Array(NB);
const bucketAlpha = new Float32Array(NB);
const bucketHue = ... 
for (let b=0;b<NB;b++){
  bucketWidth[b] = 0.9 + 1.5*Math.pow(Math.random(),2);  // 0.9..2.4
  bucketAlpha[b] = 0.28 + 0.3*Math.random();
}
```
Hmm, random per bucket — but the bucket color changes over time via shift, so widths/alphas are just style variety. Fine. Use deterministic-ish values from a hash.

Let's write palette sampling:

```js
  const PAL = [
    [255, 82, 130],
    [255, 140, 70],
    [255, 214, 110],
    [150, 240, 190],
    [90, 200, 255],
    [130, 130, 255],
    [190, 110, 255],
    [255, 90, 220]
  ];
  const PALN = PAL.length;

  function palColor(u, alpha){
    u = u - Math.floor(u);
    const f = u * PALN;
    const i = f | 0;
    const t = f - i;
    const a = PAL[i % PALN], b = PAL[(i+1) % PALN];
    const r = (a[0] + (b[0]-a[0])*t) | 0;
    const g = (a[1] + (b[1]-a[1])*t) | 0;
    const bl = (a[2] + (b[2]-a[2])*t) | 0;
    return 'rgba(' + r + ',' + g + ',' + bl + ',' + alpha.toFixed(3) + ')';
  }
```

Hmm, `i | 0` for f up to PALN — fine. When u is exactly 1... we normalize.

Also, we might want to bias palette sampling by particle position so the composition has color regions. Since buckets are assigned randomly, colors are spatially mixed. Alternatively assign bucket by spatial position at spawn (e.g., by y or by noise) — that creates color regions that flow. That looks nicer! E.g. bucket = floor(noise-based value * NB) using the particle's spawn position. But then the "slow shift" of the palette still applies.

Hmm, spawning particles at random positions with a spatially varying bucket gives color coherence in the initial layout, but particles move away from their spawn region, so it becomes mixed over time anyway. Random assignment is fine.

Let's do a mix: bucket = (Math.floor(paletteNoise(x,y) * NB) + randomOffset) % NB. Eh. Just use random.

OK, writing the full code now.

One more detail: the particle respawn should sometimes happen "in place" with a small chance of keeping position — no, uniform random across the canvas is fine.

Also, we could spawn particles in clusters to create denser filaments. Let's add: 15% of respawns pick a random point near a "hotspot" that drifts. Skip for simplicity.

Let me write the final loop:

```js
  function frame(now){
    requestAnimationFrame(frame);
    if (!lastT) lastT = now;
    let dt = (now - lastT) / 1000;
    lastT = now;
    if (dt <= 0) dt = 1/60;
    if (dt > 0.05) dt = 0.05;
    const t = now * 0.001;

    // ---- fade ----
    ctx.globalCompositeOperation = 'source-over';
    ctx.fillStyle = 'rgba(5,2,12,0.045)';
    ctx.fillRect(0, 0, W, H);

    // ---- reset waves ----
    if (t > nextWaveAt){
      spawnWave();
      nextWaveAt = t + 7 + Math.random()*5;
    }
    for (let i = waves.length-1; i>=0; i--){
      const w = waves[i];
      w.r += w.speed * dt;
      const rIn = w.r - 26, rOut = w.r + 26;
      // erase ring
      const g = ctx.createRadialGradient(w.x, w.y, Math.max(0, w.r-46), w.x, w.y, w.r+46);
      g.addColorStop(0, 'rgba(0,0,0,0)');
      g.addColorStop(0.5, 'rgba(0,0,0,0.55)');
      g.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.globalCompositeOperation = 'destination-out';
      ctx.fillStyle = g;
      ctx.fillRect(0,0,W,H);
      // respawn particles in the band
      ...
      if (w.r > w.maxR) waves.splice(i,1);
    }
```
Hmm, createRadialGradient per wave per frame — 1 or 2 per frame, fine. But the gradient is created with inner radius (w.r-46) and outer (w.r+46) — the color stop 0.5 is at radius w.r. Good.

The fillRect covers the whole canvas — with a gradient defined only over a small region, most of the fill is transparent. GPU/CPU handles it but it's a full-canvas fill each frame during a wave. Acceptable. Could restrict to the bounding box of the ring: fillRect(w.x-w.r-46, w.y-w.r-46, 2*(w.r+46), 2*(w.r+46)). Let's do that, clamped. Minor optimization, do it.

Particle respawn in the band:
```js
      const r2in = rIn*rIn, r2out = rOut*rOut;
      for (let j=0;j<particles.length;j++){
        const p = particles[j];
        const dx = p.x - w.x, dy = p.y - w.y;
        const d2 = dx*dx + dy*dy;
        if (d2 > r2in && d2 < r2out) respawn(p, t);
      }
```
Hmm, if rIn < 0 then r2in is positive and the condition d2 > r2in is true for all — correct behavior (everything inside the outer radius gets respawned). Good.

Now particle update:
```js
    for (let i=0;i<particles.length;i++){
      const p = particles[i];
      const a = flowAngle(p.x, p.y, t);
      const tx = Math.cos(a)*p.speed, ty = Math.sin(a)*p.speed;
      const k = Math.min(1, 3.0*dt);
      p.vx += (tx-p.vx)*k;
      p.vy += (ty-p.vy)*k;
      p.px = p.x; p.py = p.y;
      p.x += p.vx*dt;
      p.y += p.vy*dt;
      p.life += dt;
      if (p.life > p.lifeMax || p.x < -60 || p.x > W+60 || p.y < -60 || p.y > H+60){
        respawn(p);
      }
    }
```
Note: when respawning, p.px = p.x = new x — need to handle inside respawn.

Careful: respawn during the band check sets p.px/p.py = new position. Good.

Drawing:

```js
    ctx.globalCompositeOperation = 'lighter';
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    const shift = t * 0.018;

    for (let b=0;b<NB;b++){
      const list = buckets[b];
      if (list.length === 0) continue;
      const path = new Path2D();
      for (let i=0;i<list.length;i++){
        const p = list[i];
        path.moveTo(p.px, p.py);
        path.lineTo(p.x, p.y);
      }
      const u = (b / NB + shift);
      const pulse = 0.8 + 0.35*Math.sin(t*0.7 + b*0.5);
      const wdt = bucketW[b];
      // glow
      ctx.strokeStyle = palColor(u, 0.055 * pulse);
      ctx.lineWidth = wdt * 4.5;
      ctx.stroke(path);
      // core
      ctx.strokeStyle = palColor(u, 0.34 * pulse);
      ctx.lineWidth = wdt;
      ctx.stroke(path);
    }
```

Hmm — a potential issue with `new Path2D()` and `ctx.stroke(path)` when ctx has a transform. Path2D coordinates are in user space, transformed by the current transform at stroke time. Since our transform is dpr scaling, that's correct.

Bloom:
```js
    // bloom
    if (bloomCtx){
      bloomCtx.globalCompositeOperation = 'source-over';
      bloomCtx.drawImage(canvas, 0, 0, bloomCanvas.width, bloomCanvas.height);
      ctx.globalCompositeOperation = 'lighter';
      ctx.globalAlpha = 0.035;
      ctx.drawImage(bloomCanvas, 0, 0, W, H);
      ctx.globalAlpha = 1;
    }
```
Wait: `ctx.drawImage(bloomCanvas, 0, 0, W, H)` — with the transform set to scale(dpr), the destination rect W×H CSS px maps to the full device canvas. Good.

But bloomCanvas dimensions are device/4. Drawing a small image up to full size with smoothing gives a blur. Good.

Hmm, but the main canvas drawImage into bloomCanvas: source is the full canvas (device px) into a 1/4-size destination — downsampling with smoothing → blur. Good.

Note: drawImage of a canvas onto another canvas each frame is a GPU-friendly op. Fine.

Set `bloomCanvas.width = Math.max(1, Math.floor(canvas.width/4))`, similarly height. Update on resize.

Let's double check stability: retention from fade per frame = 1-0.045 = 0.955 (roughly, ignoring the added bg color). Bloom adds 0.035 of the previous state. Total factor 0.955*1.035 = 0.988 < 1. Stable. Good.

But wait: the bloom is drawn after the particles, so the sequence within a frame is: fade → draw particles → bloom(add 3.5% of current). Next frame: fade (×0.955) → ... So the effective multiplier per frame is 0.955 * 1.035 = 0.9884, plus new particle contributions. Stable. 

Now respawn function:

```js
  function respawn(p){
    p.x = Math.random()*W;
    p.y = Math.random()*H;
    p.px = p.x; p.py = p.y;
    p.vx = 0; p.vy = 0;
    p.speed = 45 + Math.random()*110;
    p.life = 0;
    p.lifeMax = 3 + Math.random()*9;
  }
```

Hmm, particles respawning with vx=0 causes a small "stall" — fine.

Spawn distribution: uniform. But particles at the edges will exit quickly. Fine.

Init: create N particles, each assigned a random bucket. Push into buckets.

`buckets[b].push(p)` where the buckets hold particle objects directly.

Resize handler: recompute W, H, SCALE, canvas size, bloom size, and respawn out-of-bounds particles (or just clamp). Also re-fill the background.

Note: on resize the canvas is cleared, so fill with bg.

```js
  function resize(){
    W = window.innerWidth;
    H = window.innerHeight;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.max(1, Math.floor(W*dpr));
    canvas.height = Math.max(1, Math.floor(H*dpr));
    canvas.style.width = W+'px';
    canvas.style.height = H+'px';
    ctx.setTransform(dpr,0,0,dpr,0,0);
    ctx.fillStyle = '#05020c';
    ctx.fillRect(0,0,W,H);
    SCALE = 2.6 / Math.min(W,H);
    bloomCanvas.width = Math.max(1, Math.floor(canvas.width/4));
    bloomCanvas.height = Math.max(1, Math.floor(canvas.height/4));
    // keep particles in bounds
    for (const p of particles){
      if (p.x > W || p.y > H) respawn(p);
    }
  }
```

Careful: setTransform then fillRect(0,0,W,H) — with the dpr transform, that fills the whole device canvas. Good. But also need to reset the composite op to source-over before filling. It is by default at init. During resize mid-animation, the composite op might be 'lighter'. Set it explicitly.

Also: `ctx.setTransform` after resizing canvas resets the context state — canvas.width assignment resets all context state including transform, strokeStyle, etc. So we must re-set lineCap etc. Let's set those in the draw loop each frame (we already set lineCap/lineJoin there). Good — but we set them inside the loop after the composite op change; fine.

Also note: assigning canvas.width resets the transform, so we must call setTransform after. Done.

Also the `ctx.fillRect` uses the transform.

Number of particles should adapt to the area on resize? Let's compute N once at init and keep it. Or recompute and add/remove. Keep it simple: compute at init only.

Hmm, but for a full-window canvas the user might resize. Fine, particles just spread over the new area (out-of-bounds ones respawn).

Now, the initial burst: at t=0, all particles are at random positions with zero velocity. Within a second they'll start flowing. Good.

To have something visible quickly, we could pre-warm by simulating a few hundred steps? No — "Everything important within the first 30 seconds"; the flow develops within a second or two. Fine.

Actually, for a nicer start, let's pre-warm the trail by running the particle simulation for ~120 frames without drawing, so at t=0 there are already established structures. Hmm, but then the canvas would be empty of trails. We could pre-warm and then draw the current positions... it'd be an instant snapshot. Not necessary.

I think it's fine to start from scratch. Within 2-3 seconds the trails build up beautifully.

Let's now also handle `visibilitychange` — when the tab is hidden, rAF stops, and on return `now` jumps. We clamp dt to 0.05, so it's fine. But `lastT` should be updated. We do `lastT = now` before clamping. Good. But the wave schedule uses absolute t; if the tab is hidden for 30s, several waves would be missed (only one spawns). Fine.

Hmm, actually if the tab is hidden, rAF doesn't fire, so no frames run. On return, t jumps by 30s, and one wave spawns. Fine.

Wait — dt is clamped to 0.05 but the particles' positions would jump only 0.05s worth. Good.

Now let me think about whether the fade alpha of 0.045 gives good trails. Retention per second = 0.955^60 = 0.063. So trails fade to 6% after 1 second. That's a fairly short trail. Particles move at ~80-150 px/s, so the visible trail is ~80-150px long. That's a decent ribbon.

Hmm, "leaving soft glowing trails that build up into an intricate, colorful composition". With 1 second persistence and 3000 particles, the canvas gets covered in flowing lines. Should look good.

Maybe use a slightly longer persistence: 0.03 retention 0.97 → 16% after 1s, 2.6% after 2s. Let's use 0.032. Then bloom alpha must satisfy 0.968*(1+a) < 1 → a < 0.033. Use a = 0.03. 0.968*1.03 = 0.997. Stable but very close to 1 — the decay is slow, so bright regions persist for ~30+ seconds. That could saturate... Actually with the fade at 3.2%/frame, an area receiving constant light settles at a value where input = 0.032*value. Input per frame per pixel from a line is small (alpha 0.34 × pulse × coverage). It self-regulates. The risk is white-out in dense areas. Hmm.

Let's think: a pixel covered by a line each frame with alpha 0.34 and color (255,80,130): adds ~0.34*255 = 87 to R. Steady state R = 87/0.032 = 2700 → saturates to 255 (white-ish). So dense areas will be white. That's actually typical for these artworks — the cores glow white and the edges are colorful. It's fine and looks good with additive blending.

But we want "intricate colorful composition" not a white blob. The particles are spread out; most pixels aren't covered every frame. It should be fine.

Let's use fade 0.04 and bloom 0.028: 0.96*1.028 = 0.987. Good margin.

Alright, let's settle: FADE = 0.04, BLOOM_ALPHA = 0.03.

Let's reconsider the alpha for the core stroke: 0.30. And the glow stroke: 0.05 with width ×5.

Hmm, with a very short segment (1.3px) and lineWidth 5×wdt (up to 12px), the glow dot is ~12px in diameter with alpha 0.05×0.8 = 0.04 → adds ~0.04×255 = 10 per frame → steady state 10/0.04 = 250. Hmm, that's bright! The glow pass would dominate. Let's reduce the glow alpha to 0.02 and width to 3.5×. Then per frame adds 0.02*0.8*255 = 4 → steady state 100. That's a soft halo. Good.

Actually, the glow accumulates over the same path each frame, so steady state ≈ (per-frame add)/(fade). Let's compute more carefully:
- Core: alpha 0.34 × pulse(0.8) = 0.27; color R=255 → add 69 per frame. Steady 69/0.04 = 1725 (saturates). But the core only covers a 1-2px wide strip, and the particle moves, so a given pixel isn't covered every frame. Coverage probability depends on density. With 3000 particles over 2M px, each drawing ~1.3px×2px = 2.6px² per frame → total 7800px² per frame out of 2M = 0.4% coverage. So a given pixel gets hit every ~250 frames. Steady state = 69 × (1 - 0.96^250)/0.04 ≈ 69 × 25 = 1725. Still saturating.

Hmm, that math says every pixel eventually saturates. But with the bloom and fade, the equilibrium is high. In practice, these flow-field pieces do have bright cores with white-pink and darker surroundings. It'll look good.

But to keep colors from washing to white, lower the core alpha to ~0.18 and increase the fade. Let's try: core alpha 0.2, fade 0.045.
Steady = 0.2*0.8*255/0.045 = 51/0.045 = 1133. Still saturates for heavily hit pixels. Only pixels hit multiple times saturate; most pixels are visited rarely.

Once a channel saturates at 255, the color becomes white-ish only if all channels saturate. Since the palette has varied hues, R saturates first for warm colors, then G, then B, creating bright warm cores with colored halos. That's actually the classic look and it's pretty.

OK, going with: core alpha 0.22, glow alpha 0.025, fade 0.045.

Let me just pick reasonable numbers and not over-engineer. The visual is likely to be fine either way.

Final values:
- FADE_ALPHA = 0.045, color (5,2,12)
- bloom alpha 0.03
- core stroke alpha 0.22 * pulse
- glow stroke alpha 0.03 * pulse, width ×4

Let me reconsider the bloom's contribution: 0.03 × the canvas content. In bright areas, adds 3% of 255 = 7.6 per frame, while the fade removes 4.5% — equilibrium at ~1.03× ... it's stable as computed.

OK.

Now let's write the wave erase: with alpha 0.55 at the ring center and 'destination-out', the ring erases 55% of the accumulated light in one frame. Since the ring sweeps past a pixel in maybe 3-5 frames (ring speed 300px/s, thickness 92px → 92/300 = 0.3s = 18 frames), the erasure would be 0.55^... no — the gradient is soft; a pixel far from the ring's instantaneous position gets little erase. But over the pass, total erasure could be significant, creating a clear "gap" ring. That's the intent. Maybe reduce to 0.35 to keep it subtle.

Actually, the erase happens every frame while the wave is active, but a given pixel only feels the gradient when it's within [r-46, r+46]. As r grows, the ring moves past. So the total erasure at a pixel: sum over frames of the gradient value at that pixel at that time. Roughly, the gradient peak is 0.55, and it passes over ~18 frames with an average of maybe 0.2 → the total erasure is like 1-(1-0.2)^18 ≈ 0.98. That's a full wipe! Too strong.

Let's reduce: peak 0.12. Then total ≈ 1-(1-0.04)^18 = 0.52. Half erased. Hmm, still a strong visible ring.

Maybe that's desirable — "reset waves" that clear accumulated saturation. Yes! The requirement says "occasional gentle 'reset waves' so the image keeps evolving instead of saturating". So a visible clearing wave is intended. Let's make it moderate: peak 0.10, and reduce the ring width to 30px. Also, the particles respawning in the band will redraw new lines there.

Let's use peak alpha 0.13 and a band width of 40px (gradient from r-40 to r+40). Total erasure ~ 50%. That will look like a subtle clearing pulse. Good.

Hmm, but there's a subtlety: erasing with destination-out on an opaque canvas (alpha:false) → the pixels become black (0,0,0) with full alpha? With alpha:false, the canvas has no alpha channel; destination-out makes the destination transparent, which then displays as... the canvas element has no alpha so it renders as black. Then the fade fill brings it back toward (5,2,12). OK.

Actually, let's use alpha:true for the canvas so destination-out produces real transparency, and the page background (#05020c) shows through. That's cleaner. The bloom drawImage of a partially transparent canvas with 'lighter'... source-over vs lighter: with 'lighter', the source's alpha multiplies its color contribution. Fine.

Let's just use the default alpha (don't specify), and set the body background to #05020c.

Hmm, but with alpha:true, the fade fillRect with rgba(5,2,12,0.045) accumulates alpha too, so that's fine.

OK, default context.

Wait, one issue: with alpha:true and 'lighter', drawing onto a transparent canvas: dst alpha 0, so the result = src (premultiplied add). Fine.

Let me finalize and write the code.

Also I should double check `Path2D` availability — supported everywhere modern. Fine.

Let me write out the code.

```js
(function () {
  'use strict';

  // ---------- tiny seeded PRNG ----------
  let _seed = 0x9e3779b9 >>> 0;
  function rnd() {
    _seed = (Math.imul(_seed, 1664525) + 1013904223) >>> 0;
    return _seed / 4294967296;
  }

  // ---------- classic Perlin noise (3D), implemented from scratch ----------
  const PERM = new Uint8Array(512);
  {
    const p = new Uint8Array(256);
    for (let i = 0; i < 256; i++) p[i] = i;
    for (let i = 255; i > 0; i--) {
      const j = (rnd() * (i + 1)) | 0;
      const tmp = p[i]; p[i] = p[j]; p[j] = tmp;
    }
    for (let i = 0; i < 512; i++) PERM[i] = p[i & 255];
  }

  function fadeCurve(t) { return t * t * t * (t * (t * 6 - 15) + 10); }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function grad3(h, x, y, z) {
    switch (h & 15) {
      case 0: return x + y;  case 1: return -x + y;
      case 2: return x - y;  case 3: return -x - y;
      case 4: return x + z;  case 5: return -x + z;
      case 6: return x - z;  case 7: return -x - z;
      case 8: return y + z;  case 9: return -y + z;
      case 10: return y - z; case 11: return -y - z;
      case 12: return x + y; case 13: return -y + z;
      case 14: return -x + y; default: return -y - z;
    }
  }
  function noise3(x, y, z) {
    const fx = Math.floor(x), fy = Math.floor(y), fz = Math.floor(z);
    const X = fx & 255, Y = fy & 255, Z = fz & 255;
    x -= fx; y -= fy; z -= fz;
    const u = fadeCurve(x), v = fadeCurve(y), w = fadeCurve(z);
    const A = PERM[X] + Y, AA = PERM[A] + Z, AB = PERM[A + 1] + Z;
    const B = PERM[X + 1] + Y, BA = PERM[B] + Z, BB = PERM[B + 1] + Z;
    return lerp(
      lerp(lerp(grad3(PERM[AA], x, y, z), grad3(PERM[BA], x - 1, y, z), u),
           lerp(grad3(PERM[AB], x, y - 1, z), grad3(PERM[BB], x - 1, y - 1, z), u), v),
      lerp(lerp(grad3(PERM[AA + 1], x, y, z - 1), grad3(PERM[BA + 1], x - 1, y, z - 1), u),
           lerp(grad3(PERM[AB + 1], x, y - 1, z - 1), grad3(PERM[BB + 1], x - 1, y - 1, z - 1), u), v),
      w);
  }
  function fbm3(x, y, z, octaves) {
    let amp = 0.5, freq = 1, sum = 0, norm = 0;
    for (let i = 0; i < octaves; i++) {
      sum += amp * noise3(x * freq, y * freq, z * freq);
      norm += amp;
      freq *= 2.02;
      amp *= 0.5;
    }
    return sum / norm;
  }
```

Careful: `PERM[A+1]` where A = PERM[X]+Y ≤ 255+255 = 510 → A+1 = 511 OK. AA = PERM[A]+Z ≤ 255+255 = 510 → AA+1 = 511 OK. Good.

Now the rest.

```js
  const canvas = document.getElementById('c');
  const ctx = canvas.getContext('2d');
  const bloomCanvas = document.createElement('canvas');
  const bloomCtx = bloomCanvas.getContext('2d');

  let W = 1, H = 1, DPX = 1, SCALE = 0.003;
  let particles = [];
  const NB = 48;
  const buckets = [];
  for (let i = 0; i < NB; i++) buckets.push([]);
  const bucketW = new Float32Array(NB);
  const bucketA = new Float32Array(NB);
  for (let i = 0; i < NB; i++) {
    bucketW[i] = 0.8 + 1.9 * rnd() * rnd();
    bucketA[i] = 0.16 + 0.2 * rnd();
  }
```
Hmm rnd()*rnd() biases toward small. Let's use 0.8 + 1.6*Math.pow(rnd(), 1.5).

```js
  function respawn(p) {
    p.x = rnd() * W;      // Math.random fine too
    p.y = rnd() * H;
    ...
  }
```
Using rnd() keeps the deterministic seed but it doesn't matter. Use Math.random for runtime variability? Since the permutation is seeded, and runtime randomness with Math.random is fine. I'll use Math.random for particles.

Let's write it all out now, and be careful with ordering (function hoisting works for function declarations).

Full code:

```js
(function () {
  'use strict';

  /* ---------- Seeded PRNG (only for the noise permutation) ---------- */
  let _seed = 0x1a2b3c4d >>> 0;
  function srand() {
    _seed = (Math.imul(_seed, 1664525) + 1013904223) >>> 0;
    return _seed / 4294967296;
  }

  /* ---------- 3D Perlin noise, hand-rolled ---------- */
  ... (as above)

  /* ---------- Canvas / state ---------- */
  const canvas = document.getElementById('c');
  const ctx = canvas.getContext('2d');
  const bloomCanvas = document.createElement('canvas');
  const bloomCtx = bloomCanvas.getContext('2d');

  let W = window.innerWidth, H = window.innerHeight;
  let SCALE = 0.003;

  const NBUCKET = 48;
  const buckets = new Array(NBUCKET);
  for (let i = 0; i < NBUCKET; i++) buckets[i] = [];
  const bucketWidth = new Float32Array(NBUCKET);
  const bucketAlpha = new Float32Array(NBUCKET);
  for (let i = 0; i < NBUCKET; i++) {
    bucketWidth[i] = 0.7 + 1.8 * Math.pow(Math.random(), 1.6);
    bucketAlpha[i] = 0.16 + 0.22 * Math.random();
  }

  const particles = [];

  /* ---------- Palette ---------- */
  const PAL = [...];
  function palColor(u, a) {...}

  /* ---------- particles ---------- */
  function spawn(p) {...}
  function makeParticle() {
    const p = { x:0,y:0,px:0,py:0,vx:0,vy:0,speed:0,life:0,lifeMax:0,bucket:0 };
    respawn(p);
    p.bucket = (Math.random()*NBUCKET)|0;
    buckets[p.bucket].push(p);
    return p;
  }
```

Wait: respawn sets the position, but at init W,H are known. Fine.

Careful: at init, if we push to buckets before knowing N... fine.

Let's write `initParticles(count)`.

Now, the resize function must be called before creating particles so W/H are set. Order: resize() → initParticles() → rAF.

But resize() references `particles` — it's an empty array initially. Fine.

Let me write the code in full now.

Also I want a subtle "focus" attractor? No.

Let me make sure the drawing loop handles the case where W or H is 0.

Let's write the final file.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Flow Field Bloom</title>
<style>
  html, body {
    margin: 0; padding: 0; width: 100%; height: 100%;
    background: #05020c; overflow: hidden;
  }
  canvas { display: block; width: 100vw; height: 100vh; }
</style>
</head>
<body>
<canvas id="c"></canvas>
<script>
(function () {
  'use strict';
  ...
})();
</script>
</body>
</html>
```

Now writing the JS in full detail.

```js
  /* ================= 1. Noise ================= */
  let _seed = 0x1a2b3c4d >>> 0;
  function srand() {
    _seed = (Math.imul(_seed, 1664525) + 1013904223) >>> 0;
    return _seed / 4294967296;
  }

  const PERM = new Uint8Array(512);
  (function buildPerm() {
    const p = new Uint8Array(256);
    for (let i = 0; i < 256; i++) p[i] = i;
    for (let i = 255; i > 0; i--) {
      const j = (srand() * (i + 1)) | 0;
      const t = p[i]; p[i] = p[j]; p[j] = t;
    }
    for (let i = 0; i < 512; i++) PERM[i] = p[i & 255];
  })();

  function fadeC(t) { return t * t * t * (t * (t * 6 - 15) + 10); }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function grad3(h, x, y, z) { ... }
  function noise3(x, y, z) { ... }
  function fbm3(x, y, z, oct) { ... }

  /* ================= 2. Canvas setup ================= */
  ...
```

Now writing everything concretely. I'll be careful.

One thought about performance: `new Path2D()` per bucket per frame and the two strokes. Also, the `path.moveTo/lineTo` calls. It's fine.

Another thought: Should I skip the glow pass for buckets with few particles? NAH.

Let me also consider that with the transform set (dpr scaling), the `drawImage(bloomCanvas, 0,0,W,H)` will stretch the small bloom canvas over the whole device canvas. Good.

Now writing the final answer.

Let me carefully write the render function.

```js
  function render(now) {
    requestAnimationFrame(render);

    if (lastT === 0) lastT = now;
    let dt = (now - lastT) / 1000;
    lastT = now;
    if (dt <= 0) dt = 1 / 60;
    if (dt > 0.05) dt = 0.05;

    const t = now * 0.001;

    /* ---- fade (trail persistence) ---- */
    ctx.globalCompositeOperation = 'source-over';
    ctx.fillStyle = 'rgba(5,2,12,0.042)';
    ctx.fillRect(0, 0, W, H);

    /* ---- reset waves ---- */
    if (t >= nextWaveAt) {
      spawnWave(t);
      nextWaveAt = t + 6.5 + Math.random() * 5.5;
    }
    updateWaves(dt);

    /* ---- advance particles ---- */
    for (let i = 0, n = particles.length; i < n; i++) {
      const p = particles[i];
      const ang = flowAngle(p.x, p.y, t);
      const tx = Math.cos(ang) * p.speed;
      const ty = Math.sin(ang) * p.speed;
      const k = dt * 3.2 > 1 ? 1 : dt * 3.2;
      p.vx += (tx - p.vx) * k;
      p.vy += (ty - p.vy) * k;
      p.px = p.x;
      p.py = p.y;
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      p.life += dt;
      if (p.life > p.lifeMax || p.x < -60 || p.x > W + 60 || p.y < -60 || p.y > H + 60) {
        respawn(p);
      }
    }

    /* ---- draw additive trails ---- */
    ctx.globalCompositeOperation = 'lighter';
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    const shift = t * 0.017;

    for (let b = 0; b < NBUCKET; b++) {
      const list = buckets[b];
      const len = list.length;
      if (len === 0) continue;

      const path = new Path2D();
      for (let i = 0; i < len; i++) {
        const p = list[i];
        path.moveTo(p.px, p.py);
        path.lineTo(p.x, p.y);
      }

      const u = b / NBUCKET + shift;
      const pulse = 0.75 + 0.45 * Math.sin(t * 0.8 + b * 0.618);
      const lw = bucketWidth[b];

      // soft halo
      ctx.strokeStyle = palColor(u, 0.030 * pulse);
      ctx.lineWidth = lw * 4.5;
      ctx.stroke(path);

      // bright core
      ctx.strokeStyle = palColor(u, bucketAlpha[b] * pulse * 1.6);
      ctx.lineWidth = lw;
      ctx.stroke(path);
    }
```

Hmm, bucketAlpha 0.16-0.38 times 1.6 → 0.26-0.61. Slightly high. Let's use bucketAlpha[b] directly and set bucketAlpha range 0.13-0.30.

Let's simplify: core alpha = bucketAlpha[b] * pulse (0.16..0.38 × 0.75..1.2 → 0.12..0.45). Fine.

```js
    /* ---- bloom ---- */
    bloomCtx.globalCompositeOperation = 'source-over';
    bloomCtx.clearRect(0, 0, bloomCanvas.width, bloomCanvas.height);
    bloomCtx.drawImage(canvas, 0, 0, bloomCanvas.width, bloomCanvas.height);

    ctx.globalCompositeOperation = 'lighter';
    ctx.globalAlpha = 0.03;
    ctx.drawImage(bloomCanvas, 0, 0, W, H);
    ctx.globalAlpha = 1;
  }
```

Note: `bloomCtx.clearRect` before drawing — since drawImage with source-over over the previous content would blend. We want a fresh copy. clearRect is fine (or use globalCompositeOperation='copy').

Now the waves:

```js
  const waves = [];
  let nextWaveAt = 5.0;

  function spawnWave(t) {
    const cx = W * (0.15 + 0.7 * Math.random());
    const cy = H * (0.15 + 0.7 * Math.random());
    waves.push({
      x: cx, y: cy, r: 0,
      speed: 220 + Math.random() * 260,
      maxR: Math.hypot(Math.max(cx, W - cx), Math.max(cy, H - cy)) + 120
    });
  }

  function updateWaves(dt) {
    for (let i = waves.length - 1; i >= 0; i--) {
      const w = waves[i];
      w.r += w.speed * dt;

      // erase a soft ring from the accumulated trail
      const inner = Math.max(0, w.r - 40);
      const outer = w.r + 40;
      const g = ctx.createRadialGradient(w.x, w.y, inner, w.x, w.y, outer);
      g.addColorStop(0, 'rgba(0,0,0,0)');
      g.addColorStop(0.5, 'rgba(0,0,0,0.14)');
      g.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.globalCompositeOperation = 'destination-out';
      ctx.fillStyle = g;
      ctx.fillRect(w.x - outer, w.y - outer, outer * 2, outer * 2);

      // respawn particles the ring sweeps over
      const rIn = w.r - 22, rOut = w.r + 22;
      const rin2 = rIn * rIn, rout2 = rOut * rOut;
      for (let j = 0; j < particles.length; j++) {
        const p = particles[j];
        const dx = p.x - w.x, dy = p.y - w.y;
        const d2 = dx * dx + dy * dy;
        if (d2 > rin2 && d2 < rout2) respawn(p);
      }

      if (w.r > w.maxR) waves.splice(i, 1);
    }
  }
```

Note: createRadialGradient requires inner radius >= 0, and if inner === outer it throws? If w.r < 40, inner = 0, outer = w.r+40 > 0. OK.  Never equal since outer = r+40 > inner = max(0, r-40).

Fill rect: from (w.x-outer, w.y-outer) with size 2*outer. If that extends outside the canvas, it's clipped. Fine.

Note: when rIn < 0, rin2 = rIn*rIn positive, and d2 > rin2 is true for everything inside rOut. Correct.

Hmm, but if w.r is small (say 10) and the wave starts, particles within 32px get respawned — that's fine.

The erase ring peak alpha 0.14 — over the ~0.3s the ring takes to pass a pixel (80px thick at 220-480px/s → 0.17-0.36 s → 10-22 frames), with an average gradient value of maybe 0.05 → total ~1-(0.95)^16 ≈ 0.56. Hmm, that's erasing half the brightness. Maybe that's still too much. Let's use 0.08 peak → total ~0.35 erased. That's a nice gentle clearing.

Actually, thinking about it more: the erase is compounded by the fact that particles in the ring get respawned so no new light is added there for a moment. The visual will be a subtle dark pulse ring traveling outward. That's a nice "reset wave". I'll use 0.10.

Now flowAngle:

```js
  function flowAngle(x, y, t) {
    const sx = x * SCALE, sy = y * SCALE;
    const wa = noise3(sx * 0.6 + 11.3, sy * 0.6 - 4.7, t * 0.09);
    const wb = noise3(sx * 0.6 - 7.9, sy * 0.6 + 9.1, t * 0.09 + 23.1);
    const n = fbm3(sx + wa * 1.5, sy + wb * 1.5, t * 0.06, 3);
    return n * 6.2;
  }
```

That's 5 noise3 calls per particle.

Hmm, t*0.06 as the z coordinate: over 30s, z changes by 1.8 units. Good evolution.

Note: SCALE changes with resize; the noise field would "jump" on resize. Acceptable.

Let's double check the fbm z-scaling: in fbm3, the z coordinate is multiplied by the octave frequency too (freq), so the time evolution speeds up for higher octaves. That's fine — it adds shimmer.

Now, initial particle count:

```js
  function particleCount() {
    const area = window.innerWidth * window.innerHeight;
    let n = Math.round(area / 700);
    if (n < 900) n = 900;
    if (n > 3200) n = 3200;
    return n;
  }
```
On a 1920×1080: 2073600/700 = 2962. Good, "thousands".

On a small phone (390×844): 329160/700 = 470 → clamped to 900. That might be too many for a phone but OK, it's a small canvas. Actually 900 particles on a small screen looks dense — fine.

Let's use area/900 with a min of 800 and max of 3000. 1920×1080 → 2304. Hmm, "thousands of particles" — 2304 is thousands. Let's use /700 with max 3200.

Fine.

Now let's assemble.

Also: initial `respawn` uses W and H which must be set. So call resize() first, then create particles.

But careful: resize() iterates `particles` (empty at that point) — fine.

Let me write `resize()`:

```js
  function resize() {
    W = Math.max(1, window.innerWidth);
    H = Math.max(1, window.innerHeight);
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(W * dpr);
    canvas.height = Math.round(H * dpr);
    canvas.style.width = W + 'px';
    canvas.style.height = H + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.globalCompositeOperation = 'source-over';
    ctx.globalAlpha = 1;
    ctx.fillStyle = '#05020c';
    ctx.fillRect(0, 0, W, H);

    bloomCanvas.width = Math.max(1, Math.round(canvas.width / 4));
    bloomCanvas.height = Math.max(1, Math.round(canvas.height / 4));

    SCALE = 2.6 / Math.min(W, H);

    for (let i = 0; i < particles.length; i++) {
      const p = particles[i];
      if (p.x > W || p.y > H || p.x < 0 || p.y < 0) respawn(p);
    }
  }
```

Note: canvas.width assignment resets the transform, so setTransform after. ✓.

Also, `ctx.imageSmoothingEnabled` default true. For the bloom upscale we want smoothing — default true. Good.

Now the full script. Let me also add `window.addEventListener('resize', resize)` and maybe a debounce. Direct is fine.

Also handle the case where `resize` is called and the canvas is cleared — the trails are lost. Acceptable.

Let's write the final code.

One more consideration: `ctx.stroke(path)` with a Path2D — is `new Path2D()` fast? Yes.

Actually, an alternative that avoids Path2D allocation: build the path with ctx.beginPath() and stroke twice by... no, can't. Use Path2D.

Hmm, one thing: with Path2D and ctx.setTransform, stroke respects the transform at stroke time. Good.

Let me now write out everything.

Double-check palColor:

```js
  const PAL = [
    [255, 76, 132],
    [255, 138, 64],
    [255, 214, 112],
    [126, 236, 190],
    [86, 196, 255],
    [124, 130, 255],
    [188, 108, 255],
    [255, 92, 214]
  ];
  const PALN = PAL.length;

  function palColor(u, alpha) {
    u -= Math.floor(u);
    const f = u * PALN;
    let i = f | 0;
    if (i >= PALN) i = PALN - 1;
    const fr = f - i;
    const a = PAL[i], b = PAL[(i + 1) % PALN];
    const r = (a[0] + (b[0] - a[0]) * fr) | 0;
    const g = (a[1] + (b[1] - a[1]) * fr) | 0;
    const bl = (a[2] + (b[2] - a[2]) * fr) | 0;
    return 'rgba(' + r + ',' + g + ',' + bl + ',' + alpha.toFixed(3) + ')';
  }
```

`alpha.toFixed(3)` allocates a string per call — 48×2 = 96 per frame. Fine.

Now writing out the final answer.

Actually, one more thought on the "pulse" — the per-bucket sin pulse at frequency 0.8 rad/s means a period of ~8s. Fine.

Also, should the palette shift be more noticeable? shift = t*0.017 → full cycle over 59s. Over the 30s recording, the palette rotates about half a cycle. Combined with the bucket colors already varying, the viewer sees colors shifting. Good.

Let me write the final file.

Also, I should double check: `Math.hypot` in spawnWave — fine.

Final check on the initial `lastT = 0` and `if (lastT === 0) lastT = now;`. On the first frame, dt = 0 → set to 1/60. Fine.

Let me write it.

One more: the fade color rgba(5,2,12,0.042) — the background is #05020c = rgb(5,2,12). ✓.

I'm also wondering about the wave erase with `destination-out` while the canvas is opaque... we're using the default (alpha:true), so it works properly.

But hold on: with alpha:true and the fade fill using rgba(...,0.042) with 'source-over', the canvas alpha accumulates toward 1 as discussed. After ~100 frames, alpha ≈ 1 - (1-0.042)^100 = 0.986. So after ~2 seconds, the canvas is effectively opaque everywhere. That's fine.

Now, `destination-out` on a high-alpha pixel removes alpha and color → transparent → shows the body background (#05020c). Same color. 

Writing final answer now.

Let me also verify the particle respawn keeps its bucket (it does, since we push to buckets only at creation).

Final code:

```js
(function () {
  'use strict';

  /* ============ 1. hand-rolled 3D Perlin noise ============ */
  ...
  /* ============ 2. palette ============ */
  ...
  /* ============ 3. canvas + state ============ */
  ...
  /* ============ 4. particles ============ */
  ...
  /* ============ 5. flow field ============ */
  ...
  /* ============ 6. waves ============ */
  ...
  /* ============ 7. main loop ============ */
  ...
  /* ============ 8. boot ============ */
  resize();
  ... create particles ...
  requestAnimationFrame(render);
})();
```

Order of function declarations doesn't matter due to hoisting (function declarations). But `const`/`let` declarations must be before use at runtime. I'll structure carefully: all top-level `let`/`const` state first, then function declarations, then the boot code at the bottom.

Careful: `bucketWidth` etc. are created before the functions run. Boot at the bottom calls resize() and creates particles.

But `palColor` uses `PAL` which is defined above. Fine.

Let's write it.

Also note: `respawn` uses W and H — set by resize() before particles are created. ✓

Writing now, final.