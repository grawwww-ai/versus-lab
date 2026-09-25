Here is a self-contained HTML5 canvas that creates a mesmerizing flow field with thousands of particles, layered Perlin noise, and slowly shifting colors. It starts automatically and fills the window.
```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Flow Field Bloom</title>
<style>
  html, body {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    background: #05020c;
    overflow: hidden;
  }
  canvas {
    display: block;
    width: 100vw;
    height: 100vh;
  }
</style>
</head>
<body>
<canvas id="c"></canvas>
<script>
(function () {
  'use strict';

  /* =========================================================
     1.  Hand-rolled 3D Perlin noise (classic improved Perlin)
     ========================================================= */

  let _seed = 0x1a2b3c4d >>> 0;
  function srand() {
    _seed = (Math.imul(_seed, 1664525) + 1013904223) >>> 0;
    return _seed / 4294967296;
  }

  const PERM = new Uint8Array(512);
  (function buildPermutation() {
    const p = new Uint8Array(256);
    for (let i = 0; i < 256; i++) p[i] = i;
    for (let i = 255; i > 0; i--) {
      const j = (srand() * (i + 1)) | 0;
      const t = p[i]; p[i] = p[j]; p[j] = t;
    }
    for (let i = 0; i < 512; i++) PERM[i] = p[i & 255];
  })();

  function fadeCurve(t) { return t * t * t * (t * (t * 6 - 15) + 10); }
  function lerp(a, b, t) { return a + (b - a) * t; }

  function grad3(h, x, y, z) {
    switch (h & 15) {
      case 0:  return  x + y;
      case 1:  return -x + y;
      case 2:  return  x - y;
      case 3:  return -x - y;
      case 4:  return  x + z;
      case 5:  return -x + z;
      case 6:  return  x - z;
      case 7:  return -x - z;
      case 8:  return  y + z;
      case 9:  return -y + z;
      case 10: return  y - z;
      case 11: return -y - z;
      case 12: return  x + y;
      case 13: return -y + z;
      case 14: return -x + y;
      default: return -y - z;
    }
  }

  function noise3(x, y, z) {
    const fx = Math.floor(x), fy = Math.floor(y), fz = Math.floor(z);
    const X = fx & 255, Y = fy & 255, Z = fz & 255;
    x -= fx; y -= fy; z -= fz;

    const u = fadeCurve(x), v = fadeCurve(y), w = fadeCurve(z);

    const A  = PERM[X] + Y;
    const AA = PERM[A] + Z, AB = PERM[A + 1] + Z;
    const B  = PERM[X + 1] + Y;
    const BA = PERM[B] + Z, BB = PERM[B + 1] + Z;

    return lerp(
      lerp(
        lerp(grad3(PERM[AA],     x,     y,     z),
             grad3(PERM[BA],     x - 1, y,     z), u),
        lerp(grad3(PERM[AB],     x,     y - 1, z),
             grad3(PERM[BB],     x - 1, y - 1, z), u), v),
      lerp(
        lerp(grad3(PERM[AA + 1], x,     y,     z - 1),
             grad3(PERM[BA + 1], x - 1, y,     z - 1), u),
        lerp(grad3(PERM[AB + 1], x,     y - 1, z - 1),
             grad3(PERM[BB + 1], x - 1, y - 1, z - 1), u), v),
      w);
  }

  /* fractal brownian motion over the noise — the "layered" part */
  function fbm3(x, y, z, octaves) {
    let amp = 0.5, freq = 1, sum = 0, norm = 0;
    for (let i = 0; i < octaves; i++) {
      sum  += amp * noise3(x * freq, y * freq, z * freq);
      norm += amp;
      freq *= 2.02;
      amp  *= 0.5;
    }
    return sum / norm;
  }

  /* =========================================================
     2.  Curated palette (slowly rotating through it)
     ========================================================= */

  const PAL = [
    [255,  76, 132],  // rose
    [255, 138,  64],  // amber
    [255, 214, 112],  // gold
    [126, 236, 190],  // mint
    [ 86, 196, 255],  // sky
    [124, 130, 255],  // periwinkle
    [188, 108, 255],  // violet
    [255,  92, 214]   // magenta
  ];
  const PALN = PAL.length;

  function palColor(u, alpha) {
    u -= Math.floor(u);
    const f = u * PALN;
    let i = f | 0;
    if (i >= PALN) i = PALN - 1;
    const fr = f - i;
    const a = PAL[i];
    const b = PAL[(i + 1) % PALN];
    const r  = (a[0] + (b[0] - a[0]) * fr) | 0;
    const g  = (a[1] + (b[1] - a[1]) * fr) | 0;
    const bl = (a[2] + (b[2] - a[2]) * fr) | 0;
    return 'rgba(' + r + ',' + g + ',' + bl + ',' + alpha.toFixed(3) + ')';
  }

  /* =========================================================
     3.  Canvas / scene state
     ========================================================= */

  const canvas = document.getElementById('c');
  const ctx = canvas.getContext('2d');

  const bloomCanvas = document.createElement('canvas');
  const bloomCtx = bloomCanvas.getContext('2d');

  let W = window.innerWidth;
  let H = window.innerHeight;
  let SCALE = 0.003;          // world -> noise scale, set on resize

  const FADE_RGB = '5,2,12';
  const FADE_ALPHA = 0.042;   // trail persistence
  const BLOOM_ALPHA = 0.030;  // soft glow pass

  /* colour buckets: each particle keeps its bucket for life, the
     palette position of the bucket drifts with time             */
  const NBUCKET = 48;
  const buckets = new Array(NBUCKET);
  for (let i = 0; i < NBUCKET; i++) buckets[i] = [];
  const bucketWidth = new Float32Array(NBUCKET);
  const bucketAlpha = new Float32Array(NBUCKET);
  for (let i = 0; i < NBUCKET; i++) {
    bucketWidth[i] = 0.7 + 1.8 * Math.pow(Math.random(), 1.6);
    bucketAlpha[i] = 0.14 + 0.20 * Math.random();
  }

  const particles = [];

  /* =========================================================
     4.  Particles
     ========================================================= */

  function respawn(p) {
    p.x = Math.random() * W;
    p.y = Math.random() * H;
    p.px = p.x;
    p.py = p.y;
    p.vx = 0;
    p.vy = 0;
    p.speed = 45 + Math.random() * 115;      // px / second
    p.life = 0;
    p.lifeMax = 3 + Math.random() * 9;       // seconds
  }

  function createParticle() {
    const p = {
      x: 0, y: 0, px: 0, py: 0,
      vx: 0, vy: 0, speed: 0,
      life: 0, lifeMax: 0,
      bucket: (Math.random() * NBUCKET) | 0
    };
    respawn(p);
    buckets[p.bucket].push(p);
    particles.push(p);
    return p;
  }

  /* =========================================================
     5.  Evolving flow field (layered noise + domain warping)
     ========================================================= */

  function flowAngle(x, y, t) {
    const sx = x * SCALE;
    const sy = y * SCALE;

    // two low-frequency warp layers bend the main field
    const wa = noise3(sx * 0.6 + 11.3, sy * 0.6 -  4.7, t * 0.09);
    const wb = noise3(sx * 0.6 -  7.9, sy * 0.6 +  9.1, t * 0.09 + 23.1);

    // three octaves of the warped field
    const n = fbm3(sx + wa * 1.5, sy + wb * 1.5, t * 0.06, 3);

    return n * 6.2;
  }

  /* =========================================================
     6.  Gentle reset waves
     ========================================================= */

  const waves = [];
  let nextWaveAt = 5.0;

  function spawnWave() {
    const cx = W * (0.12 + 0.76 * Math.random());
    const cy = H * (0.12 + 0.76 * Math.random());
    waves.push({
      x: cx,
      y: cy,
      r: 0,
      speed: 210 + Math.random() * 260,
      maxR: Math.hypot(Math.max(cx, W - cx), Math.max(cy, H - cy)) + 140
    });
  }

  function updateWaves(dt) {
    for (let i = waves.length - 1; i >= 0; i--) {
      const w = waves[i];
      w.r += w.speed * dt;

      /* erase a soft ring out of the accumulated trail */
      const inner = Math.max(0, w.r - 40);
      const outer = w.r + 40;
      const g = ctx.createRadialGradient(w.x, w.y, inner, w.x, w.y, outer);
      g.addColorStop(0,   'rgba(0,0,0,0)');
      g.addColorStop(0.5, 'rgba(0,0,0,0.10)');
      g.addColorStop(1,   'rgba(0,0,0,0)');
      ctx.globalCompositeOperation = 'destination-out';
      ctx.fillStyle = g;
      ctx.fillRect(w.x - outer, w.y - outer, outer * 2, outer * 2);

      /* particles the ring sweeps over are reborn elsewhere */
      const rIn  = w.r - 22;
      const rOut = w.r + 22;
      const rin2 = rIn * rIn;
      const rout2 = rOut * rOut;
      for (let j = 0; j < particles.length; j++) {
        const p = particles[j];
        const dx = p.x - w.x;
        const dy = p.y - w.y;
        const d2 = dx * dx + dy * dy;
        if (d2 > rin2 && d2 < rout2) respawn(p);
      }

      if (w.r > w.maxR) waves.splice(i, 1);
    }
  }

  /* =========================================================
     7.  Sizing
     ========================================================= */

  function resize() {
    W = Math.max(1, window.innerWidth);
    H = Math.max(1, window.innerHeight);

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width  = Math.round(W * dpr);
    canvas.height = Math.round(H * dpr);
    canvas.style.width  = W + 'px';
    canvas.style.height = H + 'px';

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.globalCompositeOperation = 'source-over';
    ctx.globalAlpha = 1;
    ctx.fillStyle = 'rgb(' + FADE_RGB + ')';
    ctx.fillRect(0, 0, W, H);

    bloomCanvas.width  = Math.max(1, Math.round(canvas.width  / 4));
    bloomCanvas.height = Math.max(1, Math.round(canvas.height / 4));

    SCALE = 2.6 / Math.min(W, H);

    for (let i = 0; i < particles.length; i++) {
      const p = particles[i];
      if (p.x < 0 || p.y < 0 || p.x > W || p.y > H) respawn(p);
    }
  }

  window.addEventListener('resize', resize, { passive: true });

  /* =========================================================
     8.  Main loop
     ========================================================= */

  let lastT = 0;

  function render(now) {
    requestAnimationFrame(render);

    if (lastT === 0) lastT = now;
    let dt = (now - lastT) / 1000;
    lastT = now;
    if (dt <= 0) dt = 1 / 60;
    if (dt > 0.05) dt = 0.05;

    const t = now * 0.001;

    /* ---- fade the accumulated trails ---- */
    ctx.globalCompositeOperation = 'source-over';
    ctx.globalAlpha = 1;
    ctx.fillStyle = 'rgba(' + FADE_RGB + ',' + FADE_ALPHA + ')';
    ctx.fillRect(0, 0, W, H);

    /* ---- reset waves ---- */
    if (t >= nextWaveAt) {
      spawnWave();
      nextWaveAt = t + 6.5 + Math.random() * 5.5;
    }
    if (waves.length) updateWaves(dt);

    /* ---- advect particles through the flow field ---- */
    const n = particles.length;
    for (let i = 0; i < n; i++) {
      const p = particles[i];
      const ang = flowAngle(p.x, p.y, t);
      const tx = Math.cos(ang) * p.speed;
      const ty = Math.sin(ang) * p.speed;

      let k = dt * 3.2;
      if (k > 1) k = 1;

      p.vx += (tx - p.vx) * k;
      p.vy += (ty - p.vy) * k;

      p.px = p.x;
      p.py = p.y;
      p.x += p.vx * dt;
      p.y += p.vy * dt;

      p.life += dt;

      if (p.life > p.lifeMax ||
          p.x < -60 || p.x > W + 60 ||
          p.y < -60 || p.y > H + 60) {
        respawn(p);
      }
    }

    /* ---- draw additive glowing trails ---- */
    ctx.globalCompositeOperation = 'lighter';
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    const shift = t * 0.017;   // slow palette drift (full cycle ~60 s)

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
      const pulse = 0.78 + 0.42 * Math.sin(t * 0.8 + b * 0.618);
      const lw = bucketWidth[b];

      /* wide, faint halo */
      ctx.strokeStyle = palColor(u, 0.030 * pulse);
      ctx.lineWidth = lw * 4.5;
      ctx.stroke(path);

      /* narrow, brighter core */
      ctx.strokeStyle = palColor(u, bucketAlpha[b] * pulse);
      ctx.lineWidth = lw;
      ctx.stroke(path);
    }

    /* ---- cheap bloom: downsample, upsample, add ---- */
    bloomCtx.globalCompositeOperation = 'copy';
    bloomCtx.drawImage(canvas, 0, 0, bloomCanvas.width, bloomCanvas.height);

    ctx.globalCompositeOperation = 'lighter';
    ctx.globalAlpha = BLOOM_ALPHA;
    ctx.drawImage(bloomCanvas, 0, 0, W, H);
    ctx.globalAlpha = 1;
  }

  /* =========================================================
     9.  Boot
     ========================================================= */

  resize();

  const area = W * H;
  let count = Math.round(area / 700);
  if (count < 800)  count = 800;
  if (count > 3200) count = 3200;
  for (let i = 0; i < count; i++) createParticle();

  requestAnimationFrame(render);
})();
</script>
</body>
</html>
```
### Flow Field Mechanics & Visual Evolution

Particles drift through a layered noise field, leaving glowing trails that build into colorful patterns.

- **Flow field & motion:** Each particle samples a 3D Perlin noise function (hand-rolled, with domain warping and fractal octaves). The sampled angle steers the particle’s velocity smoothly, producing organic, ever-changing paths.
- **Palette & glow:** Particles are grouped into 48 color buckets, each mapped to a curated 8-color palette. The palette rotates slowly over time, while additive blending creates soft, luminous trails.
- **Reset waves:** Every several seconds, a gentle circular wave expands outward. It fades old trails and respawns particles caught in the ring, keeping the composition from saturating.
- **Responsive canvas:** The canvas fills the window at up to 2× device pixel ratio, and all particles are repositioned on resize.
- **Time-driven animation:** The `requestAnimationFrame` timestamp drives both particle movement and palette shifts, ensuring everything unfolds consistently during the first 30 seconds.
---

**Optimization Tip:** You can adjust the particle count by changing the `/ 700` divisor or the `3200` cap in the boot section. The trail persistence is controlled by `FADE_ALPHA`, and the reset wave frequency lives in `nextWaveAt`. For a different color mood, edit the RGB values in the `PAL` array.