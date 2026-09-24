Here's a complete, self-contained HTML file that renders a cinematic 3D tour of the Solar System using Three.js. It includes procedural planet textures, a glowing sun, orbit lines, and a camera that automatically visits each planet while displaying its name.
```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>The Solar System — A Cinematic Tour</title>
<style>
  html, body {
    margin: 0; padding: 0; height: 100%; overflow: hidden; background: #000;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  }
  canvas { display: block; position: fixed; inset: 0; }
  #ui { position: fixed; inset: 0; pointer-events: none; }
  #vignette {
    position: absolute; inset: 0;
    background: radial-gradient(ellipse at 50% 45%,
      rgba(0,0,0,0) 28%, rgba(0,0,0,0.42) 70%, rgba(0,0,0,0.94) 100%);
  }
  #brand {
    position: absolute; top: 24px; left: 30px;
    font-size: 11px; letter-spacing: .42em; text-transform: uppercase;
    color: rgba(170,200,255,.5); white-space: nowrap;
  }
  #nameWrap {
    position: absolute; left: 0; right: 0; bottom: 11%;
    text-align: center; opacity: 0;
  }
  #pname {
    font-size: clamp(26px, 5.2vw, 62px); font-weight: 300;
    letter-spacing: .30em; padding-left: .30em; text-transform: uppercase;
    color: #fff;
    text-shadow: 0 0 22px rgba(140,190,255,.75), 0 0 70px rgba(70,130,255,.5);
  }
  #psub {
    margin-top: 14px; font-size: clamp(10px, 1.3vw, 13px);
    letter-spacing: .34em; padding-left: .34em; text-transform: uppercase;
    color: rgba(185,210,255,.72);
  }
</style>
</head>
<body>
<div id="ui">
  <div id="vignette"></div>
  <div id="brand">The Solar System · A Cinematic Tour</div>
  <div id="nameWrap"><div id="pname"></div><div id="psub"></div></div>
</div>

<script type="module">
import * as THREE from 'three';

/* ------------------------------------------------------------------ *
 *  Helpers
 * ------------------------------------------------------------------ */
const TAU = Math.PI * 2;
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const smoothstep = (a, b, x) => {
  const t = clamp((x - a) / (b - a), 0, 1);
  return t * t * (3 - 2 * t);
};
function rand(seed) {
  let a = seed >>> 0;
  return function () {
    a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/* ------------------------------------------------------------------ *
 *  Renderer / scene / camera
 * ------------------------------------------------------------------ */
const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.15;
document.body.appendChild(renderer.domElement);
const MAXA = renderer.capabilities.getMaxAnisotropy();

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.3, 9000);
camera.position.set(0, 200, 350);

/* ------------------------------------------------------------------ *
 *  Procedural texture toolkit
 * ------------------------------------------------------------------ */
function makeTexture(w, h, draw) {
  const cv = document.createElement('canvas');
  cv.width = w; cv.height = h;
  const ctx = cv.getContext('2d');
  draw(ctx, w, h);
  const t = new THREE.CanvasTexture(cv);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = MAXA;
  t.wrapS = THREE.RepeatWrapping;
  t.needsUpdate = true;
  return t;
}

/* soft blob, horizontally wrapped so sphere seams stay invisible */
function blob(ctx, w, h, x, y, r, rgb, a, sharp = 0.55) {
  const col = (al) => `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${al})`;
  for (let k = -1; k <= 1; k++) {
    const cx = x + k * w;
    if (cx < -r || cx > w + r) continue;
    const g = ctx.createRadialGradient(cx, y, 0, cx, y, r);
    g.addColorStop(0, col(a));
    g.addColorStop(sharp, col(a * 0.72));
    g.addColorStop(1, col(0));
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(cx, y, r, 0, TAU);
    ctx.fill();
  }
}

function crater(ctx, w, h, x, y, r, rnd) {
  for (let k = -1; k <= 1; k++) {
    const cx = x + k * w;
    if (cx < -r || cx > w + r) continue;
    ctx.globalAlpha = 0.22 + rnd() * 0.28;
    ctx.fillStyle = '#3b3b3f';
    ctx.beginPath(); ctx.arc(cx, y, r, 0, TAU); ctx.fill();

    ctx.globalAlpha = 0.30;
    ctx.strokeStyle = '#e9e9e9';
    ctx.lineWidth = Math.max(1, r * 0.16);
    ctx.beginPath(); ctx.arc(cx - r * 0.10, y - r * 0.10, r * 0.88, 0, TAU); ctx.stroke();

    if (r > 5) {
      ctx.globalAlpha = 0.16;
      ctx.fillStyle = '#ffffff';
      ctx.beginPath(); ctx.arc(cx - r * 0.25, y - r * 0.25, r * 0.34, 0, TAU); ctx.fill();
    }
  }
  ctx.globalAlpha = 1;
}

/* ---------------------------------------------------------------- */
function texSun() {
  return makeTexture(1024, 512, (ctx, w, h) => {
    ctx.fillStyle = '#ff9d1a';
    ctx.fillRect(0, 0, w, h);
    const rnd = rand(7);
    for (let i = 0; i < 150; i++) {
      const x = rnd() * w, y = rnd() * h, r = 25 + rnd() * 95;
      blob(ctx, w, h, x, y, r, rnd() > 0.5 ? [255, 238, 158] : [255, 96, 12], 0.35, 0.4);
    }
    for (let i = 0; i < 1400; i++) {
      const x = rnd() * w, y = rnd() * h, r = 2 + rnd() * 7;
      blob(ctx, w, h, x, y, r, rnd() > 0.5 ? [255, 250, 205] : [255, 122, 22], 0.20, 0.4);
    }
  });
}

function texGlow() {
  const cv = document.createElement('canvas');
  cv.width = cv.height = 256;
  const ctx = cv.getContext('2d');
  const g = ctx.createRadialGradient(128, 128, 0, 128, 128, 128);
  g.addColorStop(0.00, 'rgba(255,255,255,1.0)');
  g.addColorStop(0.12, 'rgba(255,245,215,0.72)');
  g.addColorStop(0.28, 'rgba(255,205,120,0.30)');
  g.addColorStop(0.50, 'rgba(255,150,60,0.10)');
  g.addColorStop(0.75, 'rgba(255,110,30,0.028)');
  g.addColorStop(1.00, 'rgba(255,90,20,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 256, 256);
  const t = new THREE.CanvasTexture(cv);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

function texStarSprite() {
  const cv = document.createElement('canvas');
  cv.width = cv.height = 64;
  const ctx = cv.getContext('2d');
  const g = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
  g.addColorStop(0.0, 'rgba(255,255,255,1)');
  g.addColorStop(0.25, 'rgba(255,255,255,0.85)');
  g.addColorStop(0.55, 'rgba(190,215,255,0.22)');
  g.addColorStop(1.0, 'rgba(140,180,255,0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 64, 64);
  const t = new THREE.CanvasTexture(cv);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

function texMercury() {
  return makeTexture(1024, 512, (ctx, w, h) => {
    ctx.fillStyle = '#8b8b8d';
    ctx.fillRect(0, 0, w, h);
    const rnd = rand(11);
    for (let i = 0; i < 70; i++) {
      blob(ctx, w, h, rnd() * w, rnd() * h, 45 + rnd() * 120,
        rnd() > 0.5 ? [118, 118, 122] : [168, 168, 166], 0.34, 0.6);
    }
    for (let i = 0; i < 200; i++) crater(ctx, w, h, rnd() * w, rnd() * h, 3 + rnd() * 15, rnd);
  });
}

function texVenus() {
  return makeTexture(1024, 512, (ctx, w, h) => {
    const g = ctx.createLinearGradient(0, 0, 0, h);
    g.addColorStop(0, '#d3b072');
    g.addColorStop(0.5, '#f1dba7');
    g.addColorStop(1, '#d3b072');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);
    const rnd = rand(23);
    for (let i = 0; i < 130; i++) {
      const y = rnd() * h;
      const x0 = rnd() * w;
      const len = 150 + rnd() * 420;
      const amp = 6 + rnd() * 22;
      ctx.beginPath();
      for (let x = 0; x <= len; x += 10) {
        const xx = x0 + x;
        const yy = y + Math.sin(x * 0.017 + i * 1.7) * amp;
        if (x === 0) ctx.moveTo(xx, yy); else ctx.lineTo(xx, yy);
      }
      ctx.strokeStyle = rnd() > 0.5 ? 'rgba(255,246,212,0.30)' : 'rgba(176,134,74,0.24)';
      ctx.lineWidth = 4 + rnd() * 16;
      ctx.stroke();
    }
    for (let i = 0; i < 90; i++) {
      blob(ctx, w, h, rnd() * w, rnd() * h, 40 + rnd() * 100, [255, 242, 205], 0.16, 0.5);
    }
  });
}

function texEarth() {
  return makeTexture(1024, 512, (ctx, w, h) => {
    const og = ctx.createLinearGradient(0, 0, 0, h);
    og.addColorStop(0.00, '#0a2a55');
    og.addColorStop(0.32, '#0d4384');
    og.addColorStop(0.50, '#1367b6');
    og.addColorStop(0.68, '#0d4384');
    og.addColorStop(1.00, '#0a2a55');
    ctx.fillStyle = og;
    ctx.fillRect(0, 0, w, h);

    const rnd = rand(101);
    const clusters = [
      [0.14, 0.30], [0.21, 0.64], [0.30, 0.44], [0.44, 0.30],
      [0.51, 0.64], [0.60, 0.40], [0.72, 0.29], [0.77, 0.70],
      [0.88, 0.46], [0.05, 0.52], [0.95, 0.30]
    ];
    for (const [cx, cy] of clusters) {
      const n = 7 + Math.floor(rnd() * 9);
      for (let i = 0; i < n; i++) {
        const x = (cx + (rnd() - 0.5) * 0.13) * w;
        const y = (cy + (rnd() - 0.5) * 0.17) * h;
        const r = 16 + rnd() * 68;
        const green = rnd() > 0.32;
        blob(ctx, w, h, x, y, r, green ? [56, 118, 58] : [152, 140, 82], 0.92, 0.78);
        blob(ctx, w, h, x, y, r * 0.6, green ? [110, 162, 80] : [184, 168, 106], 0.55, 0.7);
      }
    }
    /* polar ice */
    for (let i = 0; i < 150; i++) {
      const x = rnd() * w;
      const top = rnd() < 0.5;
      const y = top ? rnd() * h * 0.10 : h - rnd() * h * 0.10;
      blob(ctx, w, h, x, y, 28 + rnd() * 62, [255, 255, 255], 0.5, 0.4);
    }
    ctx.fillStyle = 'rgba(255,255,255,0.88)';
    ctx.fillRect(0, 0, w, h * 0.030);
    ctx.fillRect(0, h * 0.972, w, h * 0.028);
    /* clouds */
    for (let i = 0; i < 170; i++) {
      blob(ctx, w, h, rnd() * w, rnd() * h, 20 + rnd() * 78, [255, 255, 255], 0.13, 0.4);
    }
  });
}

function texMars() {
  return makeTexture(1024, 512, (ctx, w, h) => {
    ctx.fillStyle = '#b4461f';
    ctx.fillRect(0, 0, w, h);
    const rnd = rand(55);
    for (let i = 0; i < 95; i++) {
      blob(ctx, w, h, rnd() * w, rnd() * h, 45 + rnd() * 135,
        rnd() > 0.5 ? [122, 50, 28] : [216, 122, 70], 0.42, 0.62);
    }
    for (let i = 0; i < 45; i++) {
      blob(ctx, w, h, rnd() * w, rnd() * h, 22 + rnd() * 62, [88, 38, 24], 0.30, 0.65);
    }
    for (let i = 0; i < 80; i++) crater(ctx, w, h, rnd() * w, rnd() * h, 3 + rnd() * 13, rnd);
    for (let i = 0; i < 70; i++) {
      blob(ctx, w, h, rnd() * w, rnd() * h * 0.07, 20 + rnd() * 46, [255, 250, 245], 0.7, 0.45);
    }
    for (let i = 0; i < 45; i++) {
      blob(ctx, w, h, rnd() * w, h - rnd() * h * 0.06, 15 + rnd() * 36, [255, 250, 245], 0.6, 0.45);
    }
  });
}

function bandedTexture(w, h, palette, seed, opts) {
  const o = Object.assign({ streaks: 240, streakLight: '#fff3d8', streakDark: '#8a5a34', freq: 11, spot: false }, opts || {});
  return makeTexture(w, h, (ctx, W, H) => {
    const rnd = rand(seed);
    const n = palette.length;
    for (let y = 0; y < H; y += 2) {
      const t = y / H;
      const v = Math.sin(t * Math.PI * o.freq) * 0.50 +
                Math.sin(t * Math.PI * o.freq * 2.1 + 1.7) * 0.26 +
                Math.sin(t * Math.PI * 5.0 + 0.4) * 0.34 +
                Math.sin(t * Math.PI * 41.0 + 2.1) * 0.12;
      const idx = clamp((v + 1.22) / 2.44, 0, 0.999) * (n - 1);
      const i0 = Math.floor(idx);
      const i1 = Math.min(n - 1, i0 + 1);
      const f = idx - i0;
      const c = [0, 1, 2].map(k => palette[i0][k] * (1 - f) + palette[i1][k] * f);
      const pole = 1 - Math.pow(Math.abs(t - 0.5) * 2, 3) * 0.30;
      ctx.fillStyle = `rgb(${Math.round(c[0] * pole)},${Math.round(c[1] * pole)},${Math.round(c[2] * pole)})`;
      ctx.fillRect(0, y, W, 2);
    }
    for (let i = 0; i < o.streaks; i++) {
      const x = rnd() * W, y = rnd() * H;
      const ww = 40 + rnd() * 210, hh = 2.5 + rnd() * 9;
      ctx.globalAlpha = 0.08 + rnd() * 0.17;
      ctx.fillStyle = rnd() > 0.5 ? o.streakLight : o.streakDark;
      ctx.beginPath();
      ctx.ellipse(x, y, ww, hh, 0, 0, TAU);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
    if (o.spot) {
      const sx = W * 0.62, sy = H * 0.63, rx = 82, ry = 34;
      ctx.save();
      ctx.translate(sx, sy);
      ctx.scale(1, ry / rx);
      ctx.translate(-sx, -sy);
      const g = ctx.createRadialGradient(sx, sy, 0, sx, sy, rx);
      g.addColorStop(0.00, 'rgba(186,66,42,0.95)');
      g.addColorStop(0.50, 'rgba(202,104,72,0.72)');
      g.addColorStop(1.00, 'rgba(214,152,112,0)');
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(sx, sy, rx, 0, TAU); ctx.fill();
      ctx.restore();
    }
  });
}

function texJupiter() {
  return bandedTexture(1024, 512, [
    [196, 166, 124], [228, 206, 170], [166, 126, 90],
    [240, 224, 196], [184, 144, 104], [210, 184, 146]
  ], 777, { streaks: 280, spot: true, freq: 11 });
}

function texSaturn() {
  return bandedTexture(1024, 512, [
    [224, 204, 160], [240, 226, 190], [198, 172, 126],
    [232, 216, 178], [208, 184, 140], [246, 236, 208]
  ], 313, { streaks: 200, streakLight: '#fff8e2', streakDark: '#a98a58', freq: 8 });
}

function texUranus() {
  return bandedTexture(1024, 512, [
    [150, 220, 224], [172, 234, 236], [134, 204, 214],
    [186, 240, 240], [142, 212, 220]
  ], 91, { streaks: 120, streakLight: '#e8ffff', streakDark: '#6fa9be', freq: 6 });
}

function texNeptune() {
  return bandedTexture(1024, 512, [
    [40, 78, 206], [58, 102, 228], [28, 54, 168],
    [74, 124, 238], [34, 66, 190]
  ], 41, { streaks: 150, streakLight: '#cfe0ff', streakDark: '#0d1a58', freq: 7 });
}

function texMoon() {
  return makeTexture(512, 256, (ctx, w, h) => {
    ctx.fillStyle = '#9c9c9e';
    ctx.fillRect(0, 0, w, h);
    const rnd = rand(2024);
    for (let i = 0; i < 30; i++) {
      blob(ctx, w, h, rnd() * w, rnd() * h, 25 + rnd() * 70, [86, 86, 92], 0.42, 0.62);
    }
    for (let i = 0; i < 90; i++) crater(ctx, w, h, rnd() * w, rnd() * h, 2 + rnd() * 9, rnd);
    for (let i = 0; i < 40; i++) {
      blob(ctx, w, h, rnd() * w, rnd() * h, 15 + rnd() * 40, [200, 200, 200], 0.18, 0.5);
    }
  });
}

function texRings() {
  return makeTexture(512, 16, (ctx, w, h) => {
    ctx.clearRect(0, 0, w, h);
    for (let x = 0; x < w; x++) {
      const u = x / w;
      let n = Math.sin(u * 92) * 0.50 +
              Math.sin(u * 31 + 1.2) * 0.32 +
              Math.sin(u * 173 + 0.6) * 0.17 +
              Math.sin(u * 7.3) * 0.38;
      n = n * 0.5 + 0.5;
      let a = 0.10 + 0.86 * Math.pow(n, 1.25);
      if (u > 0.60 && u < 0.66) a *= 0.13;          /* Cassini division */
      if (u > 0.905) a *= Math.max(0, 1 - (u - 0.905) / 0.095);
      if (u < 0.055) a *= u / 0.055;
      const b = 0.72 + 0.38 * n;
      ctx.fillStyle = `rgba(${Math.round(233 * b)},${Math.round(215 * b)},${Math.round(181 * b)},${a})`;
      ctx.fillRect(x, 0, 1, h);
    }
  });
}

/* ------------------------------------------------------------------ *
 *  Stars
 * ------------------------------------------------------------------ */
const starSprite = texStarSprite();
function makeStarLayer(count, size, rMin, rMax, opacity, seed) {
  const positions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);
  const rnd = rand(seed);
  const col = new THREE.Color();
  for (let i = 0; i < count; i++) {
    const u = rnd() * 2 - 1;
    const th = rnd() * TAU;
    const s = Math.sqrt(Math.max(0, 1 - u * u));
    const r = rMin + rnd() * (rMax - rMin);
    positions[i * 3 + 0] = Math.cos(th) * s * r;
    positions[i * 3 + 1] = u * r;
    positions[i * 3 + 2] = Math.sin(th) * s * r;

    const t = rnd();
    if (t < 0.62) col.setHSL(0.58, 0.18 + rnd() * 0.30, 0.78 + rnd() * 0.22);
    else if (t < 0.86) col.setHSL(0.09, 0.22 + rnd() * 0.32, 0.74 + rnd() * 0.24);
    else col.setHSL(0.0, 0.0, 0.88 + rnd() * 0.12);

    colors[i * 3 + 0] = col.r;
    colors[i * 3 + 1] = col.g;
    colors[i * 3 + 2] = col.b;
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  const mat = new THREE.PointsMaterial({
    size, sizeAttenuation: false, vertexColors: true, map: starSprite,
    transparent: true, opacity, depthWrite: false,
    blending: THREE.AdditiveBlending, alphaTest: 0.01
  });
  const pts = new THREE.Points(geo, mat);
  pts.frustumCulled = false;
  scene.add(pts);
}
makeStarLayer(3200, 1.5, 1500, 3000, 0.80, 12345);
makeStarLayer(520, 3.1, 1300, 2800, 1.00, 54321);

/* ------------------------------------------------------------------ *
 *  Sun
 * ------------------------------------------------------------------ */
const sunRadius = 4.6;
const sunGroup = new THREE.Group();
scene.add(sunGroup);

const sunMesh = new THREE.Mesh(
  new THREE.SphereGeometry(sunRadius, 64, 48),
  new THREE.MeshBasicMaterial({ map: texSun(), toneMapped: false })
);
sunGroup.add(sunMesh);

const glowTex = texGlow();
[
  { s: 4.4, c: 0xfff2c8, o: 0.95 },
  { s: 9.0, c: 0xffb155, o: 0.50 },
  { s: 17.0, c: 0xff7a1c, o: 0.20 }
].forEach(gs => {
  const mat = new THREE.SpriteMaterial({
    map: glowTex, color: gs.c, transparent: true, opacity: gs.o,
    blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false
  });
  const sp = new THREE.Sprite(mat);
  const d = sunRadius * gs.s;
  sp.scale.set(d, d, 1);
  sunGroup.add(sp);
});

const sunLight = new THREE.PointLight(0xfff2d8, 3.6, 0, 0);
sunGroup.add(sunLight);
scene.add(new THREE.AmbientLight(0x2b3f6e, 1.05));

/* ------------------------------------------------------------------ *
 *  Planets
 * ------------------------------------------------------------------ */
const planetDefs = [
  { name: 'Mercury', r: 0.84, dist: 18, speed: 0.440, spin: 0.20, tilt: 0.001, phase: 0.6,
    cam: 3.7, camY: 0.18, dur: 2.9, sub: 'Closest to the Sun · 88-day year', tex: texMercury() },
  { name: 'Venus', r: 1.32, dist: 24, speed: 0.280, spin: 0.08, tilt: 0.05, phase: 2.2,
    cam: 5.5, camY: 0.16, dur: 2.9, sub: 'Veiled in sulphuric acid clouds', tex: texVenus() },
  { name: 'Earth', r: 1.35, dist: 31, speed: 0.210, spin: 0.60, tilt: 0.409, phase: 4.1,
    cam: 8.5, camY: 0.20, dur: 3.8, sub: 'The blue marble · one moon', tex: texEarth() },
  { name: 'Mars', r: 0.98, dist: 39, speed: 0.150, spin: 0.55, tilt: 0.440, phase: 5.4,
    cam: 4.5, camY: 0.18, dur: 2.9, sub: 'The red planet · polar ice caps', tex: texMars() },
  { name: 'Jupiter', r: 4.52, dist: 60, speed: 0.062, spin: 1.00, tilt: 0.05, phase: 1.2,
    cam: 18.5, camY: 0.16, dur: 3.5, sub: 'Largest world · the Great Red Spot', tex: texJupiter() },
  { name: 'Saturn', r: 4.15, dist: 80, speed: 0.040, spin: 0.90, tilt: 0.466, phase: 3.3,
    cam: 32.0, camY: 0.30, dur: 3.8, rings: true, sub: 'Jewel of the Solar System', tex: texSaturn() },
  { name: 'Uranus', r: 2.70, dist: 100, speed: 0.024, spin: 0.60, tilt: 1.700, phase: 5.7,
    cam: 12.5, camY: 0.18, dur: 2.9, sub: 'Tilted ice giant · 84-year orbit', tex: texUranus() },
  { name: 'Neptune', r: 2.66, dist: 118, speed: 0.017, spin: 0.60, tilt: 0.490, phase: 2.7,
    cam: 12.0, camY: 0.18, dur: 3.2, sub: 'Farthest planet · supersonic winds', tex: texNeptune() }
];

const ringTex = texRings();
const moonTex = texMoon();
const planetObjects = [];

for (const def of planetDefs) {
  const group = new THREE.Group();
  scene.add(group);

  const tiltGroup = new THREE.Group();
  tiltGroup.rotation.z = def.tilt;
  group.add(tiltGroup);

  const mesh = new THREE.Mesh(
    new THREE.SphereGeometry(def.r, 48, 32),
    new THREE.MeshStandardMaterial({ map: def.tex, roughness: 0.88, metalness: 0.02 })
  );
  tiltGroup.add(mesh);

  const obj = { def, group, mesh, moonPivot: null };

  /* Saturn's rings */
  if (def.rings) {
    const inner = def.r * 1.30;
    const outer = def.r * 2.32;
    const rg = new THREE.RingGeometry(inner, outer, 192, 1);
    const pos = rg.attributes.position;
    const uv = rg.attributes.uv;
    const v = new THREE.Vector3();
    for (let i = 0; i < pos.count; i++) {
      v.fromBufferAttribute(pos, i);
      const d = v.length();
      uv.setXY(i, clamp((d - inner) / (outer - inner), 0, 1), 0.5);
    }
    uv.needsUpdate = true;
    const rings = new THREE.Mesh(rg, new THREE.MeshBasicMaterial({
      map: ringTex, transparent: true, opacity: 0.95,
      side: THREE.DoubleSide, depthWrite: false
    }));
    rings.rotation.x = -Math.PI / 2;
    tiltGroup.add(rings);
  }

  /* Earth's moon */
  if (def.name === 'Earth') {
    const mTilt = new THREE.Group();
    mTilt.rotation.z = 0.09;
    group.add(mTilt);
    const pivot = new THREE.Group();
    mTilt.add(pivot);
    const moon = new THREE.Mesh(
      new THREE.SphereGeometry(0.37, 32, 24),
      new THREE.MeshStandardMaterial({ map: moonTex, roughness: 0.96, metalness: 0.0 })
    );
    moon.position.set(2.9, 0, 0);
    pivot.add(moon);
    obj.moonPivot = pivot;
  }

  planetObjects.push(obj);

  /* faint orbit line */
  const pts = [];
  for (let i = 0; i <= 200; i++) {
    const a = (i / 200) * TAU;
    pts.push(new THREE.Vector3(Math.cos(a) * def.dist, 0, Math.sin(a) * def.dist));
  }
  const line = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints(pts),
    new THREE.LineBasicMaterial({ color: 0x4d76ad, transparent: true, opacity: 0.17 })
  );
  scene.add(line);
}

/* ------------------------------------------------------------------ *
 *  Cinematic tour definition
 * ------------------------------------------------------------------ */
const tourKeys = [
  {
    label: 'The Solar System',
    sub: 'Eight planets · one star',
    target: sunGroup,
    off: new THREE.Vector3(0, 200, 350),
    drift: 0,
    dur: 3.2
  }
];

for (const obj of planetObjects) {
  const d = obj.def;
  tourKeys.push({
    label: d.name,
    sub: d.sub,
    target: obj.group,
    off: new THREE.Vector3(d.cam * 0.62, d.cam * d.camY, d.cam * 0.50),
    drift: 0.07,
    dur: d.dur
  });
}

let TOUR_TOTAL = 0;
for (const k of tourKeys) TOUR_TOTAL += k.dur;

/* ------------------------------------------------------------------ *
 *  UI refs
 * ------------------------------------------------------------------ */
const nameWrap = document.getElementById('nameWrap');
const pnameEl = document.getElementById('pname');
const psubEl = document.getElementById('psub');

/* ------------------------------------------------------------------ *
 *  Animation
 * ------------------------------------------------------------------ */
const YAXIS = new THREE.Vector3(0, 1, 0);
const vecA = new THREE.Vector3();
const vecB = new THREE.Vector3();
const lookTarget = new THREE.Vector3();

let startTs = null;
let lastKeyIndex = -1;

function frame(ts) {
  requestAnimationFrame(frame);

  if (startTs === null) startTs = ts;
  const time = (ts - startTs) * 0.001;   /* seconds from the rAF timestamp */

  /* ---- orbital mechanics ---- */
  for (const o of planetObjects) {
    const d = o.def;
    const a = d.phase + time * d.speed;
    o.group.position.set(Math.cos(a) * d.dist, 0, Math.sin(a) * d.dist);
    o.mesh.rotation.y = d.phase * 3.0 + time * d.spin;
    if (o.moonPivot) o.moonPivot.rotation.y = time * 0.6;
  }
  sunMesh.rotation.y = time * 0.02;

  /* ---- tour camera ---- */
  const lt = time % TOUR_TOTAL;
  let acc = 0;
  let ki = 0;
  while (ki < tourKeys.length - 1 && lt >= acc + tourKeys[ki].dur) {
    acc += tourKeys[ki].dur;
    ki++;
  }
  const key = tourKeys[ki];
  const next = tourKeys[(ki + 1) % tourKeys.length];
  const p = clamp((lt - acc) / key.dur, 0, 1);
  const blend = smoothstep(0.62, 1.0, p);

  vecA.copy(key.off).applyAxisAngle(YAXIS, time * key.drift).add(key.target.position);
  vecB.copy(next.off).applyAxisAngle(YAXIS, time * next.drift).add(next.target.position);

  camera.position.lerpVectors(vecA, vecB, blend);
  /* gentle arc during the fly-throughs so we never clip through the star */
  camera.position.y += Math.sin(Math.PI * blend) * vecA.distanceTo(vecB) * 0.085;

  lookTarget.lerpVectors(key.target.position, next.target.position, blend);
  camera.lookAt(lookTarget);

  /* ---- on-screen name ---- */
  if (ki !== lastKeyIndex) {
    lastKeyIndex = ki;
    pnameEl.textContent = key.label;
    psubEl.textContent = key.sub;
  }
  const op = smoothstep(0.0, 0.10, p) * (1 - smoothstep(0.60, 0.92, p));
  nameWrap.style.opacity = op.toFixed(3);

  renderer.render(scene, camera);
}

/* ------------------------------------------------------------------ *
 *  Resize
 * ------------------------------------------------------------------ */
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

/* ------------------------------------------------------------------ *
 *  Go
 * ------------------------------------------------------------------ */
requestAnimationFrame(frame);
</script>
</body>
</html>
```
### How the Tour and Visuals Work

The page runs automatically, no clicks needed. Here's what you'll see:

- **Tour sequence:** The camera starts with a wide view of the Sun, then flies to each planet from Mercury to Neptune, showing a close-up and the planet's name and a short subtitle on screen. The loop takes about 29 seconds and repeats seamlessly.
- **Procedural visuals:** Every planet uses a canvas-generated texture—Earth has oceans and continents, Mars is red with polar ice, Jupiter shows bands and a Great Red Spot, and Saturn has rings. The Sun has a bright halo made of layered sprites.
- **Orbital mechanics:** Each planet orbits at a different speed, the Moon circles Earth, and faint orbit lines mark each path. A starfield background and soft vignette complete the space scene.
- **Camera behavior:** The camera glides smoothly between planets with a gentle arc, and its motion follows the requestAnimationFrame timestamp for consistent timing.
---

**Optimization Tip:** If you'd like to adjust the tour pacing, each planet's close-up duration is set in the `planetDefs` array via the `dur` property; the Sun's initial wide shot duration lives in the first `tourKeys` entry. You can also tweak `camera.fov` to change how much of each planet fills the frame.