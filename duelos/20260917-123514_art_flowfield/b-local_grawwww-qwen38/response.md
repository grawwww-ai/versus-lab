```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Flow — Generative Field</title>
<style>
  html, body {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
    background: #05070d;
  }
  canvas {
    display: block;
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
  }
</style>
</head>
<body>
<canvas id="c"></canvas>
<script>
(function () {
  "use strict";

  var canvas = document.getElementById("c");
  var ctx = canvas.getContext("2d");

  var W = 0, H = 0;

  /* ---------------------------------------------------------------
     Self-made 3D value noise (hash + smooth interpolation),
     with an fBm (fractal Brownian motion) layering function.
     --------------------------------------------------------------- */

  function hash3(x, y, z) {
    // Deterministic pseudo-random integer hash -> float in [0,1)
    var n = Math.imul(x | 0, 374761393) ^
            Math.imul(y | 0, 668265263) ^
            Math.imul(z | 0, 1274126177);
    n = Math.imul(n ^ (n >>> 13), 1103515245);
    n = n ^ (n >>> 16);
    return (n >>> 0) / 4294967296;
  }

  function smooth(t) {
    // Quintic fade for C2-continuity
    return t * t * t * (t * (t * 6 - 15) + 10);
  }

  function noise3(x, y, z) {
    var xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z);
    var xf = x - xi, yf = y - yi, zf = z - zi;
    var u = smooth(xf), v = smooth(yf), w = smooth(zf);

    var n000 = hash3(xi,     yi,     zi);
    var n100 = hash3(xi + 1, yi,     zi);
    var n010 = hash3(xi,     yi + 1, zi);
    var n110 = hash3(xi + 1, yi + 1, zi);
    var n001 = hash3(xi,     yi,     zi + 1);
    var n101 = hash3(xi + 1, yi,     zi + 1);
    var n011 = hash3(xi,     yi + 1, zi + 1);
    var n111 = hash3(xi + 1, yi + 1, zi + 1);

    var x00 = n000 + u * (n100 - n000);
    var x10 = n010 + u * (n110 - n010);
    var x01 = n001 + u * (n101 - n001);
    var x11 = n011 + u * (n111 - n011);

    var y0 = x00 + v * (x10 - x00);
    var y1 = x01 + v * (x11 - x01);

    return y0 + w * (y1 - y0); // [0,1]
  }

  // Layered noise: 3 octaves of value noise, returned in [-1, 1]
  function fbm(x, y, z) {
    var a = 0, amp = 0.55, f = 1;
    for (var i = 0; i < 3; i++) {
      a += amp * noise3(x * f, y * f, z * f);
      f *= 2.13;
      amp *= 0.5;
    }
    return a * 2 - 1; // normalize roughly to [-1, 1]
  }

  /* ---------------------------------------------------------------
     Curated palette — hue anchors that drift slowly over time,
     so the composition's color mood rotates gently.
     --------------------------------------------------------------- */

  var PALETTE = [
    { h: 195, s: 90, l: 60 },  // ice cyan
    { h: 262, s: 80, l: 64 },  // violet
    { h: 322, s: 78, l: 62 },  // magenta rose
    { h:  42, s: 92, l: 60 },  // amber
    { h: 158, s: 70, l: 56 }   // teal green (rare accent)
  ];

  // Weights for picking a palette entry (last one is rare)
  var PICK_W = [0.30, 0.26, 0.22, 0.15, 0.07];

  var _pickIdx = 0, _pickW = 0;
  function pickPaletteIdx() {
    var r = Math.random();
    for (var i = 0; i < PICK_W.length; i++) {
      if (r < PICK_W[i]) return i;
      r -= PICK_W[i];
    }
    return 0;
  }

  function paletteColor(idx, t, jitter) {
    var p = PALETTE[idx];
    var hueShift = t * 3.2 + Math.sin(t * 0.11 + idx * 1.7) * 24; // slow drift
    var h = p.h + hueShift + jitter;
    var l = p.l + Math.sin(t * 0.07 + idx * 2.3) * 6;
    return h, p.s, l;
  }

  /* ---------------------------------------------------------------
     Particles
     --------------------------------------------------------------- */

  var particles = [];
  var COUNT = 0;

  var SCALE   = 0.0016;   // spatial frequency of the field
  var T_SPEED = 0.00006;  // temporal evolution speed of the field
  var ANGLE_M = 3.6;      // field angle multiplier
  var BASE_SP = 1.35;     // base speed px/frame

  function respawn(p, seed) {
    p.x = Math.random() * W;
    p.y = Math.random() * H;
    p.px = p.x;
    p.py = p.y;
    p.life = 200 + Math.random() * 600;
    p.speed = BASE_SP * (0.55 + Math.random() * 1.0);
    p.cidx = pickPaletteIdx();
    p.jit = (Math.random() - 0.5) * 14; // per-particle hue jitter
    if (!seed) { p.px = p.x; p.py = p.y; }
  }

  function buildParticles() {
    // Density scales with area, clamped
    var area = W * H;
    COUNT = Math.max(2500, Math.min(9000, Math.floor(area / 130)));
    particles.length = 0;
    for (var i = 0; i < COUNT; i++) {
      var p = { x: 0, y: 0, px: 0, py: 0, life: 0, speed: 0, cidx: 0, jit: 0 };
      respawn(p);
      // stagger initial life so respawns don't sync
      p.life *= (0.1 + Math.random() * 0.9);
      particles.push(p);
    }
  }

  /* ---------------------------------------------------------------
     Gentle "reset wave": an expanding soft ring that softly
     respawns particles it sweeps through, keeping the piece fresh.
     --------------------------------------------------------------- */

  var wave = { x: 0, y: 0, r: 0, max: 0, active: false };
  var nextWaveAt = 9; // seconds of simulated time

  function triggerWave(t) {
    wave.x = W * (0.2 + Math.random() * 0.6);
    wave.y = H * (0.2 + Math.random() * 0.6);
    wave.max = Math.sqrt(W * W + H * H) * 0.75;
    wave.r = 0;
    wave.active = true;
    nextWaveAt = t + 14 + Math.random() * 10;
  }

  /* ---------------------------------------------------------------
     Sizing / resize — preserve existing artwork across resizes
     --------------------------------------------------------------- */

  function resize(preserve) {
    var ow = W, oh = H;
    var old = null;
    if (preserve && W > 0 && H > 0) {
      old = document.createElement("canvas");
      old.width = W; old.height = H;
      old.getContext("2d").drawImage(canvas, 0, 0);
    }
    W = window.innerWidth;
    H = window.innerHeight;
    canvas.width = W;
    canvas.height = H;
    if (preserve && old) {
      ctx.drawImage(old, 0, 0);
    } else {
      ctx.fillStyle = "rgb(5,7,13)";
      ctx.fillRect(0, 0, W, H);
    }
    // keep particles in bounds after resize
    for (var i = 0; i < particles.length; i++) {
      var p = particles[i];
      if (p.x > W || p.y > H) respawn(p);
    }
  }

  /* ---------------------------------------------------------------
     Main loop — driven purely by rAF timestamp
     --------------------------------------------------------------- */

  var lastT = 0;

  function frame(ts) {
    var t = ts * T_SPEED; // continuous "noise time"
    var wall = ts * 0.001; // seconds

    // --- fade previous frame (dark veil => soft glowing trails) ---
    ctx.globalCompositeOperation = "source-over";
    ctx.fillStyle = "rgba(5, 7, 13, 0.055)";
    ctx.fillRect(0, 0, W, H);

    // --- reset wave ---
    if (!wave.active && wall > nextWaveAt) triggerWave(t);
    var bandW = 260;
    if (wave.active) {
      wave.r += 9;
      // extra soft fade at wave front to prevent saturation
      if (wave.r < wave.max + bandW) {
        ctx.globalCompositeOperation = "source-over";
        ctx.fillStyle = "rgba(5, 7, 13, 0.012)";
        ctx.fillRect(0, 0, W, H);
      }
      if (wave.r > wave.max + bandW) wave.active = false;
    }
    var wIn = wave.active ? wave.r - 90 : -1;
    var wOut = wave.active ? wave.r + bandW : -1;

    // --- field + particles (additive glow) ---
    ctx.globalCompositeOperation = "lighter";
    ctx.lineWidth = 1;
    ctx.lineCap = "round";

    var z = ts * 0.00006; // field time coordinate
    var maxDist = Math.sqrt(W * W + H * H);

    for (var i = 0; i < COUNT; i++) {
      var p = particles[i];

      // sample layered noise -> angle
      var n = fbm(p.x * SCALE, p.y * SCALE, z);
      var a = n * Math.PI * ANGLE_M;

      var dx = Math.cos(a) * p.speed;
      var dy = Math.sin(a) * p.speed;

      // remember previous, integrate
      p.px = p.x; p.py = p.y;
      p.x += dx;
      p.y += dy;
      p.life -= 1;

      // wave sweep: softly respawn a fraction of swept particles
      if (wave.active) {
        var ddx = p.x - wave.x, ddy = p.y - wave.y;
        var d2 = ddx * ddx + ddy * ddy;
        var d = Math.sqrt(d2);
        if (d > wIn && d < wOut) {
          if (Math.random() < 0.03) {
            respawn(p);
            continue;
          }
        }
      }

      // respawn on death / out of bounds (with soft edge)
      var m = 4;
      if (p.life <= 0 || p.x < -m || p.x > W + m || p.y < -m || p.y > H + m) {
        respawn(p);
        continue;
      }

      // color: slow palette drift + per-particle jitter
      var pc = PALETTE[p.cidx];
      var hueShift = t * 3.2 + Math.sin(t * 0.11 + p.cidx * 1.7) * 24;
      var h = pc.h + hueShift + p.jit;
      var l = pc.l + Math.sin(t * 0.07 + p.cidx * 2.3) * 6;

      // fade in near end of life to avoid popping
      var alpha = 0.16;
      if (p.life < 40) alpha *= p.life / 40;

      ctx.strokeStyle = "hsla(" + h.toFixed(1) + "," + pc.s + "%," +
                        l.toFixed(1) + "%," + alpha.toFixed(3) + ")";
      ctx.beginPath();
      ctx.moveTo(p.px, p.py);
      ctx.lineTo(p.x, p.y);
      ctx.stroke();
    }

    requestAnimationFrame(frame);
  }

  /* ---------------------------------------------------------------
     Boot
     --------------------------------------------------------------- */

  resize(false);
  buildParticles();
  window.addEventListener("resize", function () { resize(true); });
  requestAnimationFrame(frame);
})();
</script>
</body>
</html>
```