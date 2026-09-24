```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Murmuration — Flocking Simulation</title>
<style>
  html, body { margin: 0; padding: 0; height: 100%; overflow: hidden; background: #140f24; }
  canvas { display: block; position: fixed; inset: 0; width: 100vw; height: 100vh; }
  #label {
    position: fixed; left: 18px; bottom: 16px;
    font: 500 13px/1.4 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    color: rgba(255, 238, 220, 0.85);
    background: rgba(20, 12, 30, 0.35);
    padding: 7px 12px; border-radius: 8px;
    letter-spacing: 0.04em;
    backdrop-filter: blur(4px);
    border: 1px solid rgba(255, 220, 190, 0.12);
    pointer-events: none; user-select: none;
  }
  #label b { color: #fff3e6; font-weight: 650; }
  #label span { opacity: 0.6; font-size: 11px; }
</style>
</head>
<body>
<canvas id="c"></canvas>
<div id="label"></div>
<script>
(() => {
  const canvas = document.getElementById('c');
  const ctx = canvas.getContext('2d');
  const label = document.getElementById('label');

  // ---------- Parameters ----------
  const N = 2600;             // number of starlings
  const NP = 2;               // predators
  const R = 24;               // perception radius
  const R2 = R * R;
  const CELL = R;
  const MAXN = 36;            // neighbor cap for speed
  const MIN_S = 1.9, MAX_S = 3.4;
  const PRED_R = 135;         // predator fear radius

  let W = 0, H = 0, DPR = 1;
  let cols = 0, rows = 0, cellCount = 0;
  let cellStart, cellCounts, sorted;
  let bg = document.createElement('canvas');
  let bgctx = bg.getContext('2d');

  const px = new Float32Array(N), py = new Float32Array(N);
  const vx = new Float32Array(N), vy = new Float32Array(N);
  const pan = new Float32Array(N), phase = new Float32Array(N);
  const cellOf = new Int32Array(N);

  const BUCKETS = 7;
  const bucketIdx = [];
  const bucketLen = new Int32Array(BUCKETS);
  for (let b = 0; b < BUCKETS; b++) bucketIdx.push(new Int32Array(N));
  const bucketColors = [];
  for (let b = 0; b < BUCKETS; b++) {
    const t = b / (BUCKETS - 1);
    // silhouette tones: backlit (very dark) -> side-lit (warm dusky violet)
    const r = Math.round(10 + t * 62), g = Math.round(7 + t * 38), bl = Math.round(18 + t * 48);
    bucketColors.push(`rgb(${r},${g},${bl})`);
  }

  // light comes from the low sun (lower-left-ish)
  const LX = -0.55, LY = 0.83;

  function drawBackground() {
    bg.width = W * DPR; bg.height = H * DPR;
    bgctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    const g = bgctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0.00, '#141433');
    g.addColorStop(0.28, '#2e2552');
    g.addColorStop(0.52, '#6a3f6e');
    g.addColorStop(0.72, '#c0606a');
    g.addColorStop(0.86, '#f0935f');
    g.addColorStop(1.00, '#ffc978');
    bgctx.fillStyle = g; bgctx.fillRect(0, 0, W, H);

    // sun glow
    const sx = W * 0.3, sy = H * 0.9;
    const sg = bgctx.createRadialGradient(sx, sy, 0, sx, sy, Math.max(W, H) * 0.6);
    sg.addColorStop(0, 'rgba(255,230,170,0.85)');
    sg.addColorStop(0.08, 'rgba(255,200,130,0.45)');
    sg.addColorStop(0.35, 'rgba(255,150,110,0.12)');
    sg.addColorStop(1, 'rgba(255,120,120,0)');
    bgctx.fillStyle = sg; bgctx.fillRect(0, 0, W, H);

    // soft cloud streaks
    bgctx.save();
    for (let i = 0; i < 9; i++) {
      const cy = H * (0.35 + i * 0.055) + Math.sin(i * 7.1) * 20;
      const cx = W * ((i * 0.37) % 1);
      const cw = W * (0.25 + (i % 3) * 0.12);
      const cg = bgctx.createRadialGradient(cx, cy, 0, cx, cy, cw);
      cg.addColorStop(0, `rgba(255,${170 + i * 6},${150 + i * 4},0.10)`);
      cg.addColorStop(1, 'rgba(255,170,150,0)');
      bgctx.fillStyle = cg;
      bgctx.setTransform(DPR, 0, 0, DPR * 0.12, 0, cy * DPR * 0.88);
      bgctx.beginPath(); bgctx.arc(cx, cy, cw, 0, Math.PI * 2); bgctx.fill();
    }
    bgctx.restore();
    bgctx.setTransform(DPR, 0, 0, DPR, 0, 0);

    // tiny stars at the top
    for (let i = 0; i < 90; i++) {
      const x = (Math.sin(i * 12.9898) * 43758.5453 % 1 + 1) % 1 * W;
      const y = (Math.sin(i * 78.233) * 12543.123 % 1 + 1) % 1 * H * 0.3;
      bgctx.fillStyle = `rgba(255,255,255,${0.15 + (i % 5) * 0.08 * (1 - y / (H * 0.3))})`;
      bgctx.fillRect(x, y, 1.1, 1.1);
    }

    // distant hills + tree line silhouette
    bgctx.fillStyle = '#3a2238';
    bgctx.beginPath(); bgctx.moveTo(0, H);
    for (let x = 0; x <= W; x += 8) {
      const y = H * 0.9 - 18 * Math.sin(x * 0.004 + 1) - 10 * Math.sin(x * 0.011);
      bgctx.lineTo(x, y);
    }
    bgctx.lineTo(W, H); bgctx.fill();
    bgctx.fillStyle = '#1a0f1c';
    bgctx.beginPath(); bgctx.moveTo(0, H);
    for (let x = 0; x <= W; x += 4) {
      const n = Math.sin(x * 0.05) * 4 + Math.sin(x * 0.13) * 3 + Math.sin(x * 0.31) * 2 + Math.abs(Math.sin(x * 0.021)) * 12;
      bgctx.lineTo(x, H * 0.95 - n - 8 * Math.sin(x * 0.003));
    }
    bgctx.lineTo(W, H); bgctx.fill();

    // vignette
    const vg = bgctx.createRadialGradient(W / 2, H / 2, Math.min(W, H) * 0.3, W / 2, H / 2, Math.max(W, H) * 0.8);
    vg.addColorStop(0, 'rgba(0,0,0,0)');
    vg.addColorStop(1, 'rgba(8,4,18,0.45)');
    bgctx.fillStyle = vg; bgctx.fillRect(0, 0, W, H);
  }

  function resize() {
    DPR = Math.min(window.devicePixelRatio || 1, 2);
    W = window.innerWidth; H = window.innerHeight;
    canvas.width = W * DPR; canvas.height = H * DPR;
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    cols = Math.ceil(W / CELL) + 1; rows = Math.ceil(H / CELL) + 1;
    cellCount = cols * rows;
    cellStart = new Int32Array(cellCount + 1);
    cellCounts = new Int32Array(cellCount);
    sorted = new Int32Array(N);
    drawBackground();
    ctx.drawImage(bg, 0, 0, W, H);
  }
  window.addEventListener('resize', resize);
  resize();

  // ---------- Init flock ----------
  function gauss() { return (Math.random() + Math.random() + Math.random() - 1.5) / 1.5; }
  const baseAng = Math.random() * Math.PI * 2;
  for (let i = 0; i < N; i++) {
    px[i] = W * 0.5 + gauss() * Math.min(W, H) * 0.28;
    py[i] = H * 0.42 + gauss() * Math.min(W, H) * 0.16;
    const a = baseAng + gauss() * 0.9;
    const s = MIN_S + Math.random() * (MAX_S - MIN_S);
    vx[i] = Math.cos(a) * s; vy[i] = Math.sin(a) * s;
    phase[i] = Math.random() * Math.PI * 2;
  }

  // ---------- Predators ----------
  const preds = [];
  for (let k = 0; k < NP; k++) {
    preds.push({
      x: k === 0 ? -80 : W + 80,
      y: k === 0 ? H * 0.25 : H * 0.6,
      vx: k === 0 ? 4 : -4, vy: 0,
      target: (Math.random() * N) | 0,
      timer: 0,
      enter: k === 0 ? 90 : 420,   // frames before entering (1.5s, 7s)
      speed: 4.7 + k * 0.3,
      flap: Math.random() * 6
    });
  }

  function retarget(p) {
    // prefer a boid somewhat ahead to create dramatic passes through the cloud
    let best = (Math.random() * N) | 0, bestScore = -1e9;
    for (let t = 0; t < 12; t++) {
      const j = (Math.random() * N) | 0;
      const dx = px[j] - p.x, dy = py[j] - p.y;
      const d = Math.hypot(dx, dy) + 1;
      const sp = Math.hypot(p.vx, p.vy) + 0.01;
      const ahead = (dx * p.vx + dy * p.vy) / (d * sp);
      const score = ahead * 2 - Math.abs(d - 350) / 200;
      if (score > bestScore) { bestScore = score; best = j; }
    }
    p.target = best;
    p.timer = 180 + Math.random() * 160;
  }

  // ---------- Simulation ----------
  let time = 0;
  let frame = 0;

  function buildGrid() {
    cellCounts.fill(0);
    for (let i = 0; i < N; i++) {
      let gx = (px[i] / CELL) | 0, gy = (py[i] / CELL) | 0;
      if (gx < 0) gx = 0; else if (gx >= cols) gx = cols - 1;
      if (gy < 0) gy = 0; else if (gy >= rows) gy = rows - 1;
      const c = gy * cols + gx;
      cellOf[i] = c; cellCounts[c]++;
    }
    let acc = 0;
    for (let c = 0; c < cellCount; c++) { cellStart[c] = acc; acc += cellCounts[c]; }
    cellStart[cellCount] = acc;
    cellCounts.fill(0);
    for (let i = 0; i < N; i++) {
      const c = cellOf[i];
      sorted[cellStart[c] + cellCounts[c]++] = i;
    }
  }

  function step(dt) {
    time += dt;
    buildGrid();

    // wandering attractor (Lissajous) keeps the cloud swirling on screen
    const axp = W * (0.5 + 0.28 * Math.sin(time * 0.0041) + 0.08 * Math.sin(time * 0.0113));
    const ayp = H * (0.42 + 0.16 * Math.sin(time * 0.0067 + 1.3) + 0.05 * Math.cos(time * 0.017));
    const marginX = W * 0.1, marginTop = H * 0.08, marginBot = H * 0.22;

    const activePreds = preds.filter(p => time > p.enter);

    for (let i = 0; i < N; i++) {
      const x = px[i], y = py[i];
      let vxi = vx[i], vyi = vy[i];
      const p = pan[i];
      const sepR = 7.5 + p * 7;
      const S2 = sepR * sepR;

      let n = 0, cx = 0, cy = 0, ax = 0, ay = 0, sx = 0, sy = 0, pn = 0;
      const gx = (x / CELL) | 0, gy = (y / CELL) | 0;
      outer:
      for (let oy = -1; oy <= 1; oy++) {
        const yy = gy + oy; if (yy < 0 || yy >= rows) continue;
        for (let ox = -1; ox <= 1; ox++) {
          const xx = gx + ox; if (xx < 0 || xx >= cols) continue;
          const c = yy * cols + xx;
          const end = cellStart[c + 1];
          for (let k = cellStart[c]; k < end; k++) {
            const j = sorted[k];
            if (j === i) continue;
            const dx = px[j] - x, dy = py[j] - y;
            const d2 = dx * dx + dy * dy;
            if (d2 < R2) {
              n++;
              cx += dx; cy += dy;
              ax += vx[j]; ay += vy[j];
              pn += pan[j];
              if (d2 < S2) {
                const inv = 1 / (d2 + 0.5);
                sx -= dx * inv; sy -= dy * inv;
              }
              if (n >= MAXN) break outer;
            }
          }
        }
      }

      let fx = 0, fy = 0;
      if (n > 0) {
        const inv = 1 / n;
        fx += (ax * inv - vxi) * 0.055;
        fy += (ay * inv - vyi) * 0.055;
        const coh = 0.0035 * (1 - p * 0.85);
        fx += cx * inv * coh; fy += cy * inv * coh;
        const sepW = 0.55 + p * 0.9;
        fx += sx * sepW; fy += sy * sepW;
        // panic wave propagates through neighbours
        const spread = pn * inv * 0.93;
        if (spread > pan[i]) pan[i] = spread;
      }

      // weak pull toward attractor
      {
        const dx = axp - x, dy = ayp - y;
        const d = Math.sqrt(dx * dx + dy * dy) + 1;
        const w = 0.018 * (1 - p * 0.6) * Math.min(1, d / 250);
        fx += dx / d * w; fy += dy / d * w;
      }

      // soft boundaries
      if (x < marginX) fx += (marginX - x) * 0.0016;
      else if (x > W - marginX) fx -= (x - (W - marginX)) * 0.0016;
      if (y < marginTop) fy += (marginTop - y) * 0.0018;
      else if (y > H - marginBot) fy -= (y - (H - marginBot)) * 0.0022;

      // predators: flee + fountain split
      for (let q = 0; q < activePreds.length; q++) {
        const pr = activePreds[q];
        const dx = x - pr.x, dy = y - pr.y;
        const d2 = dx * dx + dy * dy;
        if (d2 < PRED_R * PRED_R) {
          const d = Math.sqrt(d2) + 0.01;
          const f = 1 - d / PRED_R;
          const ps = Math.hypot(pr.vx, pr.vy) + 0.01;
          const hx = pr.vx / ps, hy = pr.vy / ps;
          // side of predator path -> push perpendicular (fountain effect)
          const side = (dx * hy - dy * hx) > 0 ? 1 : -1;
          const perpX = hy * side, perpY = -hx * side;
          const strength = f * f * 1.6 + f * 0.25;
          fx += (dx / d * 0.6 + perpX * 0.7) * strength;
          fy += (dy / d * 0.6 + perpY * 0.7) * strength;
          if (f > 0.25 && pan[i] < 1) pan[i] = Math.min(1, pan[i] + f * 0.9);
        }
      }

      // gentle jitter for organic twist
      fx += (Math.random() - 0.5) * 0.04;
      fy += (Math.random() - 0.5) * 0.04;

      vxi += fx * dt; vyi += fy * dt;
      let s = Math.sqrt(vxi * vxi + vyi * vyi);
      const maxS = MAX_S * (1 + pan[i] * 0.75);
      if (s > maxS) { vxi *= maxS / s; vyi *= maxS / s; }
      else if (s < MIN_S) { const m = MIN_S / (s + 1e-4); vxi *= m; vyi *= m; }
      vx[i] = vxi; vy[i] = vyi;
      px[i] = x + vxi * dt; py[i] = y + vyi * dt;
      pan[i] *= Math.pow(0.965, dt);
    }

    // predators
    for (const p of preds) {
      p.flap += 0.18 * dt;
      if (time <= p.enter) continue;
      p.timer -= dt;
      const tx = px[p.target], ty = py[p.target];
      const dx = tx - p.x, dy = ty - p.y;
      const d = Math.hypot(dx, dy) + 0.01;
      if (p.timer <= 0 || d < 18) retarget(p);
      const dsx = dx / d * p.speed, dsy = dy / d * p.speed;
      const turn = 0.035;
      p.vx += (dsx - p.vx) * turn * dt;
      p.vy += (dsy - p.vy) * turn * dt;
      // stay roughly on screen
      if (p.x < -60) p.vx += 0.1 * dt; if (p.x > W + 60) p.vx -= 0.1 * dt;
      if (p.y < -60) p.vy += 0.1 * dt; if (p.y > H * 0.85) p.vy -= 0.12 * dt;
      const s = Math.hypot(p.vx, p.vy);
      const mx = p.speed * 1.15;
      if (s > mx) { p.vx *= mx / s; p.vy *= mx / s; }
      p.x += p.vx * dt; p.y += p.vy * dt;
    }
  }

  // ---------- Rendering ----------
  function render() {
    // trails: fade toward background
    ctx.globalAlpha = 0.34;
    ctx.drawImage(bg, 0, 0, W, H);
    ctx.globalAlpha = 1;

    bucketLen.fill(0);
    for (let i = 0; i < N; i++) {
      const s = Math.hypot(vx[i], vy[i]) + 1e-4;
      const h = (vx[i] * LX + vy[i] * LY) / s;        // heading vs light
      // turning birds catch the light differently -> shimmering waves
      let t = 0.5 + 0.5 * Math.sin(h * 2.2 + phase[i] * 0.15);
      t = t * 0.8 + pan[i] * 0.35;
      let b = (t * (BUCKETS - 1) + 0.5) | 0;
      if (b < 0) b = 0; else if (b >= BUCKETS) b = BUCKETS - 1;
      bucketIdx[b][bucketLen[b]++] = i;
    }

    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    const tflap = time * 0.35;
    for (let b = 0; b < BUCKETS; b++) {
      const arr = bucketIdx[b], len = bucketLen[b];
      if (!len) continue;
      ctx.strokeStyle = bucketColors[b];
      ctx.lineWidth = 1.35;
      ctx.beginPath();
      for (let k = 0; k < len; k++) {
        const i = arr[k];
        const x = px[i], y = py[i];
        const s = Math.hypot(vx[i], vy[i]) + 1e-4;
        const hx = vx[i] / s, hy = vy[i] / s;
        const pxp = -hy, pyp = hx;
        const flap = Math.sin(tflap * (1 + pan[i]) + phase[i]);
        const span = 1.6 + 1.3 * Math.abs(flap);
        const sweep = 0.8 + flap * 0.8;
        // wings (V shape)
        ctx.moveTo(x + pxp * span - hx * sweep, y + pyp * span - hy * sweep);
        ctx.lineTo(x + hx * 0.8, y + hy * 0.8);
        ctx.lineTo(x - pxp * span - hx * sweep, y - pyp * span - hy * sweep);
        // body/tail
        ctx.moveTo(x + hx * 1.4, y + hy * 1.4);
        ctx.lineTo(x - hx * 1.8, y - hy * 1.8);
      }
      ctx.stroke();
    }

    // predators
    for (const p of preds) {
      if (time <= p.enter) continue;
      const a = Math.atan2(p.vy, p.vx);
      const f = Math.sin(p.flap);
      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate(a);
      ctx.fillStyle = '#0b0610';
      ctx.beginPath();
      // body
      ctx.ellipse(0, 0, 9, 2.6, 0, 0, Math.PI * 2);
      ctx.fill();
      // wings
      const span = 13 + 5 * f;
      ctx.beginPath();
      ctx.moveTo(4, 0);
      ctx.quadraticCurveTo(-2, -span * 0.6, -7, -span);
      ctx.quadraticCurveTo(-4, -span * 0.4, -5, 0);
      ctx.quadraticCurveTo(-4, span * 0.4, -7, span);
      ctx.quadraticCurveTo(-2, span * 0.6, 4, 0);
      ctx.fill();
      // tail
      ctx.beginPath();
      ctx.moveTo(-7, 0); ctx.lineTo(-14, -3); ctx.lineTo(-14, 3); ctx.closePath();
      ctx.fill();
      ctx.restore();
    }
  }

  // ---------- Loop ----------
  let last = performance.now();
  let fps = 60, fpsAcc = 0, fpsFrames = 0;
  const countStr = N.toLocaleString('en-US');

  function loop(now) {
    let dt = (now - last) / 16.667;
    last = now;
    if (dt > 2.5) dt = 2.5;
    if (dt <= 0) dt = 1;
    step(dt);
    render();

    fpsAcc += dt * 16.667; fpsFrames++;
    if (fpsAcc > 500) {
      fps = Math.round(1000 * fpsFrames / fpsAcc);
      fpsAcc = 0; fpsFrames = 0;
      const hunting = preds.filter(p => time > p.enter).length;
      label.innerHTML = `<b>${countStr}</b> starlings &nbsp;·&nbsp; <b>${hunting}</b> falcon${hunting === 1 ? '' : 's'} hunting &nbsp;<span>${fps} fps</span>`;
    }
    frame++;
    requestAnimationFrame(loop);
  }
  label.innerHTML = `<b>${countStr}</b> starlings &nbsp;·&nbsp; <b>0</b> falcons hunting`;
  requestAnimationFrame((t) => { last = t; loop(t); });
})();
</script>
</body>
</html>
```