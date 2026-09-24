```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Flow Field — Generative</title>
<style>
  html, body {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
    background: #000;
  }
  canvas {
    display: block;
    width: 100vw;
    height: 100vh;
    background: #000;
  }
</style>
</head>
<body>
<canvas id="c"></canvas>
<script>
(function () {
  "use strict";

  const canvas = document.getElementById("c");
  const ctx = canvas.getContext("2d");

  let W = 0, H = 0;

  // ------------------------------------------------------------
  // Noise: hand-rolled 3D value noise (hash + smooth interpolation)
  // plus an fBm wrapper for layered detail.
  // ------------------------------------------------------------

  // Deterministic integer hash -> [0,1)
  function hash3(x, y, z) {
    let h = (x * 374761393 + y * 668265263 + z * 1274126177) | 0;
    h = (h ^ (h >>> 13)) | 0;
    h = (h * 1274126177) | 0;
    h = (h ^ (h >>> 16)) >>> 0;
    return h / 4294967296;
  }

  // Quintic smoothstep for C2 continuity
  function fade(t) {
    return t * t * t * (t * (t * 6 - 15) + 10);
  }

  // 3D value noise in [-1, 1]
  function valueNoise3(x, y, z) {
    const xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z);
    const xf = x - xi, yf = y - yi, zf = z - zi;
    const u = fade(xf), v = fade(yf), w = fade(zf);

    // 8 corners, each mapped to [-1,1]
    const n000 = hash3(xi,     yi,     zi)     * 2 - 1;
    const n100 = hash3(xi + 1, yi,     zi)     * 2 - 1;
    const n010 = hash3(xi,     yi + 1, zi)     * 2 - 1;
    const n110 = hash3(xi + 1, yi + 1, zi)     * 2 - 1;
    const n001 = hash3(xi,     yi,     zi + 1) * 2 - 1;
    const n101 = hash3(xi + 1, yi,     zi + 1) * 2 - 1;
    const n011 = hash3(xi,     yi + 1, zi + 1) * 2 - 1;
    const n111 = hash3(xi + 1, yi + 1, zi + 1) * 2 - 1;

    const nx00 = n000 + u * (n100 - n000);
    const nx10 = n010 + u * (n110 - n010);
    const nx01 = n001 + u * (n101 - n001);
    const nx11 = n011 + u * (n111 - n011);

    const nxy0 = nx00 + v * (nx10 - nx00);
    const nxy1 = nx01 + v * (nx11 - nx01);

    return (nxy0 + w * (nxy1 - nxy0)); // ~[-1,1]
  }

  // Fractal Brownian motion: layered octaves
  function fbm3(x, y, z, octaves) {
    let value = 0, amplitude = 1, frequency = 1, norm = 0;
    for (let i = 0; i < octaves; i++) {
      value += valueNoise3(x * frequency, y * frequency, z * frequency) * amplitude;
      norm += amplitude;
      amplitude *= 0.5;
      frequency *= 2.02; // slight detune to avoid axis artifacts
    }
    return value / norm;
  }

  // ------------------------------------------------------------
  // Palette: a curated set of hues that drifts slowly over time.
  // ------------------------------------------------------------

  const PALETTE = [
    // hue (deg), sat %, light %
    [ 195, 95, 60 ], // glacial cyan
    [ 225, 85, 62 ], // deep azure
    [ 285, 80, 64 ], // violet orchid
    [ 330, 90, 66 ], // magenta rose
    [  25, 95, 62 ], // ember amber
    [ 160, 85, 58 ]  // jade
  ];

  function paletteColor(t, idx, jitter) {
    // slow global hue drift + per-particle offset
    const drift = t * 0.004; // degrees per ms-scale factor
    const base = PALETTE[idx];
    const hue = (base[0] + drift + jitter) % 360;
    const sat = Math.min(100, Math.max(0, base[1] + Math.sin(t * 0.0003 + idx) * 8));
    const lig = base[2];
    return "hsl(" + hue.toFixed(1) + "," + sat.toFixed(1) + "%," + lig + "%)";
  }

  // ------------------------------------------------------------
  // Particles
  // ------------------------------------------------------------

  const COUNT = 4500;
  let particles = [];
  const NOISE_SCALE = 0.0016;   // spatial frequency
  const TIME_SCALE  = 0.00006;  // temporal evolution speed
  const MAX_SPEED   = 2.2;

  function makeParticle(x, y) {
    const idx = (Math.random() * PALETTE.length) | 0;
    return {
      x: x !== undefined ? x : Math.random() * W,
      y: y !== undefined ? y : Math.random() * H,
      px: 0, py: 0,
      idx: idx,
      jitter: (Math.random() - 0.5) * 40,
      speed: 0.6 + Math.random() * 1.0,
      life: 0,
      maxLife: 300 + Math.random() * 1400
    };
  }

  function respawn(p) {
    p.x = Math.random() * W;
    p.y = Math.random() * H;
    p.px = p.x;
    p.py = p.y;
    p.idx = (Math.random() * PALETTE.length) | 0;
    p.jitter = (Math.random() - 0.5) * 40;
    p.speed = 0.6 + Math.random() * 1.0;
    p.life = 0;
    p.maxLife = 300 + Math.random() * 1400;
  }

  function initParticles() {
    particles = [];
    for (let i = 0; i < COUNT; i++) {
      const p = makeParticle();
      p.px = p.x; p.py = p.y;
      p.life = Math.random() * p.maxLife * 0.5; // stagger
      particles.push(p);
    }
  }

  // ------------------------------------------------------------
  // "Reset wave": a gentle expanding ring that pushes particles
  // and briefly deepens the trail fade so the canvas breathes.
  // ------------------------------------------------------------

  const waves = [];
  let nextWaveTime = 0;

  function spawnWave(now) {
    const cx = W * (0.2 + Math.random() * 0.6);
    const cy = H * (0.2 + Math.random() * 0.6);
    waves.push({
      x: cx, y: cy,
      radius: 0,
      maxRadius: Math.hypot(W, H) * 0.9,
      speed: 5.5 + Math.random() * 2.5,
      born: now
    });
  }

  // ------------------------------------------------------------
  // Resize handling
  // ------------------------------------------------------------

  function resize() {
    W = window.innerWidth;
    H = window.innerHeight;
    canvas.width = W;
    canvas.height = H;
    ctx.fillStyle = "#000";
    ctx.fillRect(0, 0, W, H);
    initParticles();
    waves.length = 0;
  }

  let resizeQueued = false;
  window.addEventListener("resize", function () {
    if (!resizeQueued) {
      resizeQueued = true;
      requestAnimationFrame(function () {
        resizeQueued = false;
        resize();
      });
    }
  });

  // ------------------------------------------------------------
  // Main loop
  // ------------------------------------------------------------

  function frame(now) {
    // --- gentle background fade (source-over, low alpha) -------
    // fade slightly stronger while a wave is young => "breathing"
    let fade = 0.035;
    for (let i = 0; i < waves.length; i++) {
      const a = (now - waves[i].born) / 1200; // first 1.2s of life
      if (a >= 0 && a < 1) fade += (1 - a) * 0.05;
    }
    ctx.globalCompositeOperation = "source-over";
    ctx.fillStyle = "rgba(0, 0, 8, " + fade.toFixed(3) + ")";
    ctx.fillRect(0, 0, W, H);

    // --- advance / cull waves -----------------------------------
    for (let i = waves.length - 1; i >= 0; i--) {
      const wv = waves[i];
      wv.radius += wv.speed;
      if (wv.radius > wv.maxRadius) waves.splice(i, 1);
    }
    if (waves.length === 0 && now >= nextWaveTime) {
      spawnWave(now);
      nextWaveTime = now + 9000 + Math.random() * 9000; // every 9–18s
    }

    // --- additive glow ------------------------------------------
    ctx.globalCompositeOperation = "lighter";
    ctx.lineCap = "round";
    ctx.lineWidth = 1;

    const nt = now * TIME_SCALE;
    const ns = NOISE_SCALE;

    for (let i = 0; i < COUNT; i++) {
      const p = particles[i];

      // layered flow field angle (2 octaves of fBm -> angle)
      const n = fbm3(p.x * ns, p.y * ns, nt, 3);
      const n2 = fbm3(p.x * ns * 3.1 + 100, p.y * ns * 3.1 - 50, nt * 1.7, 2);
      const angle = n * Math.PI * 2 + n2 * Math.PI * 0.9;

      let vx = Math.cos(angle) * p.speed;
      let vy = Math.sin(angle) * p.speed;

      // wave push: gentle radial force near the ring front
      for (let k = 0; k < waves.length; k++) {
        const wv = waves[k];
        const dx = p.x - wv.x, dy = p.y - wv.y;
        const d = Math.sqrt(dx * dx + dy * dy) + 0.0001;
        const band = Math.abs(d - wv.radius);
        if (band < 140) {
          const fall = 1 - band / 140;
          const push = fall * fall * 1.4;
          vx += (dx / d) * push;
          vy += (dy / d) * push;
        }
      }

      // speed clamp
      const sp2 = vx * vx + vy * vy;
      const max2 = MAX_SPEED * MAX_SPEED;
      if (sp2 > max2) {
        const s = MAX_SPEED / Math.sqrt(sp2);
        vx *= s; vy *= s;
      }

      p.px = p.x; p.py = p.y;
      p.x += vx;
      p.y += vy;
      p.life++;

      // soft life fade near end
      let alpha = 0.16;
      const lifeT = p.life / p.maxLife;
      if (lifeT > 0.85) alpha *= Math.max(0, (1 - lifeT) / 0.15);
      else if (lifeT < 0.05) alpha *= lifeT / 0.05;

      ctx.strokeStyle = paletteColor(now, p.idx, p.jitter);
      ctx.globalAlpha = alpha;
      ctx.beginPath();
      ctx.moveTo(p.px, p.py);
      ctx.lineTo(p.x, p.y);
      ctx.stroke();

      // wrap or respawn
      if (p.x < -4 || p.x > W + 4 || p.y < -4 || p.y > H + 4 || p.life > p.maxLife) {
        respawn(p);
      }
    }

    ctx.globalAlpha = 1;
    ctx.globalCompositeOperation = "source-over";

    requestAnimationFrame(frame);
  }

  // ------------------------------------------------------------
  // Boot
  // ------------------------------------------------------------

  resize();
  // small delay so the first wave isn't immediate
  nextWaveTime = performance.now() + 5000;
  requestAnimationFrame(frame);
})();
</script>
</body>
</html>
```