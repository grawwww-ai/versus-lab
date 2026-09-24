Here's a self-running Mario Kart-style race built with three.js — a closed circuit, six AI-driven karts, live position list, lap counter, chase/trackside camera cuts, and a start countdown. No keyboard input needed; the race starts automatically and loops.
```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Kart GP — Auto Race</title>
<style>
  html, body { margin: 0; height: 100%; overflow: hidden; background: #8ec4ea; }
  canvas { display: block; }
  #ui {
    position: fixed; inset: 0; pointer-events: none;
    font-family: system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #fff; user-select: none;
  }
  .panel {
    position: absolute;
    background: rgba(8, 16, 30, 0.52);
    border: 1px solid rgba(255,255,255,0.16);
    border-radius: 12px;
    padding: 10px 14px;
    backdrop-filter: blur(6px);
    box-shadow: 0 8px 26px rgba(0,0,0,0.28);
  }
  #standings { top: 16px; left: 16px; min-width: 186px; }
  #standings .title {
    font-size: 11px; letter-spacing: 2.4px; opacity: 0.7; margin-bottom: 8px; font-weight: 700;
  }
  #list { display: flex; flex-direction: column; gap: 3px; }
  .row {
    display: flex; align-items: center; gap: 9px;
    font-size: 14px; font-weight: 600;
    padding: 3px 6px; border-radius: 6px;
    background: rgba(255,255,255,0.05);
    transition: background 0.2s;
  }
  .row.lead { background: rgba(255, 214, 102, 0.22); }
  .row .pos { width: 18px; text-align: right; opacity: 0.85; font-variant-numeric: tabular-nums; }
  .row .chip { width: 11px; height: 11px; border-radius: 3px; box-shadow: 0 0 0 1px rgba(0,0,0,0.4); }
  .row .name { letter-spacing: 0.6px; }

  #lapBox { top: 16px; right: 16px; text-align: right; min-width: 128px; }
  #lapBox .big { font-size: 22px; font-weight: 800; letter-spacing: 1px; }
  #lapBox .sub { font-size: 13px; opacity: 0.75; margin-top: 3px; font-variant-numeric: tabular-nums; }

  #countdown {
    position: absolute; left: 50%; top: 40%;
    transform: translate(-50%,-50%);
    font-size: clamp(80px, 16vw, 200px);
    font-weight: 900;
    letter-spacing: -4px;
    opacity: 0;
    text-shadow: 0 8px 34px rgba(0,0,0,0.55), 0 0 70px rgba(255,225,120,0.55);
  }
  #countdown.show { animation: pop 0.95s ease-out forwards; }
  #countdown.go { color: #8dff9b; }
  @keyframes pop {
    0%   { opacity: 0; transform: translate(-50%,-50%) scale(2.3); }
    18%  { opacity: 1; transform: translate(-50%,-50%) scale(1.0); }
    72%  { opacity: 1; }
    100% { opacity: 0; transform: translate(-50%,-50%) scale(0.86); }
  }

  #banner {
    position: absolute; left: 50%; top: 26%;
    transform: translate(-50%,-50%);
    text-align: center;
    font-size: clamp(26px, 5vw, 54px);
    font-weight: 900; letter-spacing: 4px;
    opacity: 0; transition: opacity 0.5s;
    text-shadow: 0 6px 24px rgba(0,0,0,0.6);
  }
  #banner.show { opacity: 1; }
  #banner .small { font-size: 0.42em; letter-spacing: 2px; font-weight: 700; opacity: 0.9; margin-top: 10px; }

  #hint {
    position: absolute; bottom: 14px; left: 50%; transform: translateX(-50%);
    font-size: 11px; letter-spacing: 2px; opacity: 0.45; font-weight: 600;
  }
</style>
</head>
<body>
<div id="ui">
  <div class="panel" id="standings">
    <div class="title">POSITIONS</div>
    <div id="list"></div>
  </div>
  <div class="panel" id="lapBox">
    <div class="big">LAP <span id="lapNum">1</span>/<span id="lapTot">2</span></div>
    <div class="sub" id="raceTime">0:00</div>
  </div>
  <div id="countdown"></div>
  <div id="banner"></div>
  <div id="hint">AUTOMATED RACE — NO INPUT REQUIRED</div>
</div>

<script type="module">
import * as THREE from 'three';

/* ============================================================
   CONSTANTS & HELPERS
   ============================================================ */
const UP = new THREE.Vector3(0, 1, 0);
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const mod = (a, n) => ((a % n) + n) % n;
const lerp = (a, b, t) => a + (b - a) * t;

const TOTAL_LAPS = 2;
const MAX_SPEED = 80;
const HW = 7;              // half road width
const KERB_W = 1.3;

/* ============================================================
   RENDERER / SCENE / CAMERA
   ============================================================ */
const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0xa9c9e8, 300, 850);

const camera = new THREE.PerspectiveCamera(65, window.innerWidth / window.innerHeight, 0.6, 2400);
camera.position.set(0, 40, 120);

/* --- sky dome --- */
{
  const skyMat = new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, fog: false,
    uniforms: {
      topCol: { value: new THREE.Color(0x2f6fb7) },
      midCol: { value: new THREE.Color(0x9cccf0) },
      botCol: { value: new THREE.Color(0xdcecf7) }
    },
    vertexShader: `
      varying vec3 vP;
      void main(){ vP = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
    fragmentShader: `
      uniform vec3 topCol; uniform vec3 midCol; uniform vec3 botCol;
      varying vec3 vP;
      void main(){
        float h = clamp(vP.y / 700.0, -1.0, 1.0);
        vec3 c = h > 0.0 ? mix(midCol, topCol, pow(h, 0.7)) : mix(midCol, botCol, -h);
        gl_FragColor = vec4(c, 1.0);
      }`
  });
  const sky = new THREE.Mesh(new THREE.SphereGeometry(1400, 32, 20), skyMat);
  scene.add(sky);
}

/* --- lights --- */
const hemi = new THREE.HemisphereLight(0xcfe8ff, 0x4a6b3a, 1.0);
scene.add(hemi);

const sun = new THREE.DirectionalLight(0xfff3da, 2.0);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.camera.left = -75;
sun.shadow.camera.right = 75;
sun.shadow.camera.top = 75;
sun.shadow.camera.bottom = -75;
sun.shadow.camera.near = 1;
sun.shadow.camera.far = 400;
sun.shadow.bias = -0.0012;
scene.add(sun);
scene.add(sun.target);

/* ============================================================
   PROCEDURAL TEXTURES
   ============================================================ */
function noiseTexture(baseHex, variance, size = 256, repeat = 1) {
  const c = document.createElement('canvas');
  c.width = c.height = size;
  const ctx = c.getContext('2d');
  ctx.fillStyle = baseHex;
  ctx.fillRect(0, 0, size, size);
  const img = ctx.getImageData(0, 0, size, size);
  const d = img.data;
  for (let i = 0; i < d.length; i += 4) {
    const n = (Math.random() - 0.5) * variance;
    d[i] = clamp(d[i] + n, 0, 255);
    d[i + 1] = clamp(d[i + 1] + n, 0, 255);
    d[i + 2] = clamp(d[i + 2] + n, 0, 255);
  }
  ctx.putImageData(img, 0, 0);
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(repeat, repeat);
  t.anisotropy = 4;
  return t;
}

function checkerTexture(cells = 8, size = 128) {
  const c = document.createElement('canvas');
  c.width = c.height = size;
  const ctx = c.getContext('2d');
  const s = size / cells;
  for (let y = 0; y < cells; y++) {
    for (let x = 0; x < cells; x++) {
      ctx.fillStyle = ((x + y) % 2 === 0) ? '#f5f5f5' : '#1b1b1f';
      ctx.fillRect(x * s, y * s, s, s);
    }
  }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  return t;
}

function crowdTexture(size = 128) {
  const c = document.createElement('canvas');
  c.width = c.height = size;
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#2a2f3a';
  ctx.fillRect(0, 0, size, size);
  const cols = ['#e05a5a', '#5a8ce0', '#e5c95a', '#63c47a', '#c56fe0', '#e08a4a', '#f0f0f0'];
  for (let i = 0; i < 900; i++) {
    ctx.fillStyle = cols[(Math.random() * cols.length) | 0];
    const x = Math.random() * size, y = Math.random() * size;
    ctx.fillRect(x, y, 2 + Math.random() * 2, 2 + Math.random() * 2);
  }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  return t;
}

const asphaltTex = noiseTexture('#3c3c42', 60, 256);
const grassTex = noiseTexture('#528c3d', 46, 256, 1);
const checkTex = checkerTexture(8, 128);
const crowdTex = crowdTexture(128);

/* ============================================================
   TRACK CURVE + SAMPLES
   ============================================================ */
const SCALE = 0.7;
const CTRL = [
  [   0,  2, -200], [ 110,  8, -190], [ 190, 12, -110], [ 175, 10,  -20],
  [ 210,  6,   60], [ 170,  2,  130], [  90,  1,  175], [   0,  4,  150],
  [ -80,  9,  185], [-165, 12,  140], [-205,  8,   60], [-175,  4,  -20],
  [-200,  6, -110], [-120, 10, -180], [ -50,  6, -205]
].map(a => new THREE.Vector3(a[0] * SCALE, a[1] * SCALE, a[2] * SCALE));

const CURVE = new THREE.CatmullRomCurve3(CTRL, true, 'catmullrom', 0.5);
const N = 900;
const TOTAL = CURVE.getLength();
const DS = TOTAL / N;

const pts = [];
const tans = [];
const rights = [];
for (let i = 0; i < N; i++) {
  const u = i / N;
  const p = CURVE.getPointAt(u);
  const t = CURVE.getTangentAt(u).normalize();
  pts.push(p);
  tans.push(t);
  rights.push(new THREE.Vector3().crossVectors(t, UP).normalize());
}

/* curvature (signed: + = turning to the track's right) */
const curv = new Float32Array(N);
{
  const dT = new THREE.Vector3();
  for (let i = 0; i < N; i++) {
    dT.subVectors(tans[(i + 1) % N], tans[i]);
    curv[i] = dT.dot(rights[i]) / DS;
  }
}

function smoothArr(arr, passes) {
  const n = arr.length;
  for (let p = 0; p < passes; p++) {
    const out = new Float32Array(n);
    for (let i = 0; i < n; i++) {
      out[i] = (arr[(i - 2 + n) % n] + 2 * arr[(i - 1 + n) % n] + 3 * arr[i] +
                2 * arr[(i + 1) % n] + arr[(i + 2) % n]) / 9;
    }
    arr.set(out);
  }
}
smoothArr(curv, 3);

/* racing line offset (toward the inside of the corner) */
const raceOff = new Float32Array(N);
for (let i = 0; i < N; i++) raceOff[i] = clamp(curv[i] * 170, -5, 5);
smoothArr(raceOff, 10);

/* corner speed map */
const speedAt = new Float32Array(N);
for (let i = 0; i < N; i++) {
  let mk = 0;
  for (let j = 0; j < 55; j++) mk = Math.max(mk, Math.abs(curv[(i + j) % N]));
  speedAt[i] = MAX_SPEED * clamp(1 - mk * 13.5, 0.42, 1.0);
}

/* ============================================================
   ROAD / KERBS / GRASS / GROUND
   ============================================================ */
{
  const pos = [], uv = [], idx = [];
  for (let i = 0; i <= N; i++) {
    const k = i % N, p = pts[k], r = rights[k];
    pos.push(p.x - r.x * HW, p.y, p.z - r.z * HW);
    pos.push(p.x + r.x * HW, p.y, p.z + r.z * HW);
    const v = (i / N) * (TOTAL / 10);
    uv.push(0, v, 1, v);
  }
  for (let i = 0; i < N; i++) {
    const a = i * 2, b = i * 2 + 1, c = i * 2 + 2, d = i * 2 + 3;
    idx.push(a, b, c, b, d, c);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  g.computeVertexNormals();
  const m = new THREE.MeshStandardMaterial({ map: asphaltTex, roughness: 0.96, metalness: 0.0 });
  const road = new THREE.Mesh(g, m);
  road.receiveShadow = true;
  scene.add(road);
}

/* kerbs */
function buildKerb(side) {
  const pos = [], col = [], idx = [];
  const RED = new THREE.Color(0xd33a3a), WHITE = new THREE.Color(0xf2f2f2);
  for (let i = 0; i <= N; i++) {
    const k = i % N, p = pts[k], r = rights[k];
    pos.push(p.x + r.x * side * HW, p.y + 0.02, p.z + r.z * side * HW);
    pos.push(p.x + r.x * side * (HW + KERB_W), p.y + 0.17, p.z + r.z * side * (HW + KERB_W));
    const c = (i % 2 === 0) ? RED : WHITE;
    col.push(c.r, c.g, c.b, c.r, c.g, c.b);
  }
  for (let i = 0; i < N; i++) {
    const a = i * 2, b = i * 2 + 1, c = i * 2 + 2, d = i * 2 + 3;
    if (side > 0) idx.push(a, c, b, b, c, d);
    else idx.push(a, b, c, b, d, c);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  g.setIndex(idx);
  g.computeVertexNormals();
  const m = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.8 });
  const mesh = new THREE.Mesh(g, m);
  mesh.receiveShadow = true;
  scene.add(mesh);
}
buildKerb(1);
buildKerb(-1);

/* grass verges */
function buildGrass(side) {
  const pos = [], uv = [], idx = [];
  const OUT = 62;
  for (let i = 0; i <= N; i++) {
    const k = i % N, p = pts[k], r = rights[k];
    const o0 = HW + KERB_W, o1 = OUT;
    pos.push(p.x + r.x * side * o0, p.y - 0.12, p.z + r.z * side * o0);
    pos.push(p.x + r.x * side * o1, -2.0, p.z + r.z * side * o1);
    const v = (i / N) * 46;
    uv.push(0, v, 1, v);
  }
  for (let i = 0; i < N; i++) {
    const a = i * 2, b = i * 2 + 1, c = i * 2 + 2, d = i * 2 + 3;
    if (side > 0) idx.push(a, c, b, b, c, d);
    else idx.push(a, b, c, b, d, c);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  g.computeVertexNormals();
  const m = new THREE.MeshLambertMaterial({ map: grassTex.clone(), color: 0x9fd08a });
  m.map.repeat.set(1, 1);
  const mesh = new THREE.Mesh(g, m);
  mesh.receiveShadow = true;
  scene.add(mesh);
}
buildGrass(1);
buildGrass(-1);

/* ground plane */
{
  const g = new THREE.PlaneGeometry(2600, 2600);
  g.rotateX(-Math.PI / 2);
  const t = grassTex.clone();
  t.repeat.set(160, 160);
  const m = new THREE.MeshLambertMaterial({ map: t, color: 0x86b877 });
  const mesh = new THREE.Mesh(g, m);
  mesh.position.y = -2.08;
  mesh.receiveShadow = true;
  scene.add(mesh);
}

/* ============================================================
   START LINE + GANTRY
   ============================================================ */
function yawAt(k) { return Math.atan2(tans[k].x, tans[k].z); }

{
  const g = new THREE.Group();
  g.position.copy(pts[0]);
  g.rotation.y = yawAt(0);

  const lineGeo = new THREE.PlaneGeometry(HW * 2, 2.6);
  lineGeo.rotateX(-Math.PI / 2);
  const lineMat = new THREE.MeshStandardMaterial({ map: checkTex, roughness: 0.85 });
  const line = new THREE.Mesh(lineGeo, lineMat);
  line.position.y = 0.03;
  line.receiveShadow = true;
  g.add(line);

  const postMat = new THREE.MeshStandardMaterial({ color: 0xdadada, roughness: 0.5, metalness: 0.3 });
  const postGeo = new THREE.BoxGeometry(0.55, 8.5, 0.55);
  for (const s of [-1, 1]) {
    const post = new THREE.Mesh(postGeo, postMat);
    post.position.set(s * (HW + 1.4), 4.25, 0);
    post.castShadow = true;
    g.add(post);
  }
  const beamGeo = new THREE.BoxGeometry((HW + 1.4) * 2 + 0.6, 1.7, 0.9);
  const beamMat = new THREE.MeshStandardMaterial({ map: checkTex.clone(), roughness: 0.7 });
  beamMat.map.repeat.set(9, 1);
  const beam = new THREE.Mesh(beamGeo, beamMat);
  beam.position.set(0, 8.6, 0);
  beam.castShadow = true;
  g.add(beam);

  scene.add(g);
}

/* ============================================================
   SCENERY
   ============================================================ */
function nearestIdx(x, z) {
  let best = 0, bd = 1e18;
  for (let i = 0; i < N; i += 3) {
    const dx = pts[i].x - x, dz = pts[i].z - z;
    const d = dx * dx + dz * dz;
    if (d < bd) { bd = d; best = i; }
  }
  return { i: best, d: Math.sqrt(bd) };
}
function terrainY(x, z) {
  const { i, d } = nearestIdx(x, z);
  const py = pts[i].y;
  if (d <= HW + KERB_W) return py;
  const t = Math.min(1, (d - (HW + KERB_W)) / 54);
  return py + (-2 - py) * t;
}

/* --- trees (instanced) --- */
{
  const mats = [];
  let guard = 0;
  while (mats.length < 240 && guard++ < 4000) {
    const x = (Math.random() - 0.5) * 700;
    const z = (Math.random() - 0.5) * 700;
    const { d } = nearestIdx(x, z);
    if (d < 15) continue;
    const y = terrainY(x, z);
    if (y < -2.5) continue;
    const s = 0.7 + Math.random() * 0.9;
    const m = new THREE.Matrix4();
    m.compose(
      new THREE.Vector3(x, y, z),
      new THREE.Quaternion().setFromAxisAngle(UP, Math.random() * Math.PI * 2),
      new THREE.Vector3(s, s * (0.85 + Math.random() * 0.45), s)
    );
    mats.push(m);
  }

  const trunkGeo = new THREE.CylinderGeometry(0.34, 0.5, 3.6, 6);
  trunkGeo.translate(0, 1.8, 0);
  const fol1 = new THREE.ConeGeometry(2.5, 4.6, 7);
  fol1.translate(0, 4.7, 0);
  const fol2 = new THREE.ConeGeometry(1.8, 3.6, 7);
  fol2.translate(0, 7.0, 0);

  const trunkMat = new THREE.MeshLambertMaterial({ color: 0x6b4a2c });
  const folMatA = new THREE.MeshLambertMaterial({ color: 0x2f6b34 });
  const folMatB = new THREE.MeshLambertMaterial({ color: 0x3d8040 });

  const make = (geo, mat) => {
    const im = new THREE.InstancedMesh(geo, mat, mats.length);
    im.castShadow = true;
    im.receiveShadow = true;
    for (let i = 0; i < mats.length; i++) im.setMatrixAt(i, mats[i]);
    im.instanceMatrix.needsUpdate = true;
    scene.add(im);
    return im;
  };
  make(trunkGeo, trunkMat);
  make(fol1, folMatA);
  make(fol2, folMatB);
}

/* --- rocks --- */
{
  const mats = [];
  for (let n = 0; n < 90; n++) {
    const x = (Math.random() - 0.5) * 620;
    const z = (Math.random() - 0.5) * 620;
    const { d } = nearestIdx(x, z);
    if (d < 12) continue;
    const y = terrainY(x, z);
    const s = 0.5 + Math.random() * 1.6;
    const m = new THREE.Matrix4();
    m.compose(
      new THREE.Vector3(x, y + s * 0.15, z),
      new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.random(), Math.random() * 6, Math.random())),
      new THREE.Vector3(s, s * 0.7, s)
    );
    mats.push(m);
  }
  const geo = new THREE.IcosahedronGeometry(1, 0);
  const mat = new THREE.MeshLambertMaterial({ color: 0x8a8a8f, flatShading: true });
  const im = new THREE.InstancedMesh(geo, mat, mats.length);
  im.castShadow = true;
  im.receiveShadow = true;
  for (let i = 0; i < mats.length; i++) im.setMatrixAt(i, mats[i]);
  im.instanceMatrix.needsUpdate = true;
  scene.add(im);
}

/* --- grandstands near the start --- */
{
  const standMat = new THREE.MeshStandardMaterial({ color: 0xb9c2cc, roughness: 0.8 });
  const crowdMat = new THREE.MeshStandardMaterial({ map: crowdTex, roughness: 0.9 });
  for (const k of [12, 40, 860]) {
    const p = pts[k], r = rights[k];
    const g = new THREE.Group();
    const base = p.clone().addScaledVector(r, HW + 13);
    g.position.set(base.x, Math.max(base.y - 0.6, -2), base.z);
    g.rotation.y = yawAt(k) + Math.PI / 2;

    const body = new THREE.Mesh(new THREE.BoxGeometry(26, 5, 11), standMat);
    body.position.y = 2.5;
    body.castShadow = true;
    body.receiveShadow = true;
    g.add(body);

    const crowd = new THREE.Mesh(new THREE.PlaneGeometry(25.4, 4.4), crowdMat);
    crowd.position.set(0, 2.8, 5.6);
    g.add(crowd);

    const roof = new THREE.Mesh(new THREE.BoxGeometry(27, 0.5, 12), new THREE.MeshStandardMaterial({ color: 0xdd4444, roughness: 0.7 }));
    roof.position.y = 5.6;
    roof.castShadow = true;
    g.add(roof);

    scene.add(g);
  }
}

/* --- advertising boards along the track --- */
{
  const palette = [0xe63946, 0x2f7ef2, 0xffcf33, 0x35c46a, 0xa855f7, 0xff8b3d, 0x00c2c7];
  for (let i = 0; i < 26; i++) {
    const k = Math.floor((i / 26) * N + 20) % N;
    const side = (i % 2 === 0) ? 1 : -1;
    const p = pts[k], r = rights[k];
    const g = new THREE.Group();
    const base = p.clone().addScaledVector(r, side * (HW + 3.4));
    g.position.set(base.x, p.y - 0.1, base.z);
    g.rotation.y = yawAt(k);
    const mat = new THREE.MeshStandardMaterial({ color: palette[i % palette.length], roughness: 0.6 });
    const board = new THREE.Mesh(new THREE.BoxGeometry(7, 1.7, 0.35), mat);
    board.position.y = 1.0;
    board.castShadow = true;
    g.add(board);
    const leg = new THREE.Mesh(new THREE.BoxGeometry(0.4, 1.2, 0.4), new THREE.MeshStandardMaterial({ color: 0x333338 }));
    leg.position.set(-2.6, 0.4, 0);
    g.add(leg);
    const leg2 = leg.clone();
    leg2.position.x = 2.6;
    g.add(leg2);
    scene.add(g);
  }
}

/* --- clouds --- */
{
  const cloudMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.85, fog: false });
  for (let i = 0; i < 22; i++) {
    const g = new THREE.Group();
    const n = 3 + ((Math.random() * 3) | 0);
    for (let j = 0; j < n; j++) {
      const s = 12 + Math.random() * 20;
      const m = new THREE.Mesh(new THREE.SphereGeometry(s, 8, 6), cloudMat);
      m.position.set((Math.random() - 0.5) * 55, (Math.random() - 0.5) * 9, (Math.random() - 0.5) * 40);
      m.scale.y = 0.55;
      g.add(m);
    }
    g.position.set((Math.random() - 0.5) * 1100, 130 + Math.random() * 90, (Math.random() - 0.5) * 1100);
    scene.add(g);
  }
}

/* ============================================================
   PARTICLE SYSTEM (dust / skid smoke)
   ============================================================ */
const MAXP = 1200;
const pPos = new Float32Array(MAXP * 3);
const pVel = new Float32Array(MAXP * 3);
const pCol = new Float32Array(MAXP * 3);
const pSize = new Float32Array(MAXP);
const pAlpha = new Float32Array(MAXP);
const pLife = new Float32Array(MAXP);
const pMaxLife = new Float32Array(MAXP);
let pCursor = 0;
for (let i = 0; i < MAXP; i++) { pPos[i * 3 + 1] = -9999; pAlpha[i] = 0; pSize[i] = 1; }

const pGeo = new THREE.BufferGeometry();
pGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
pGeo.setAttribute('color', new THREE.BufferAttribute(pCol, 3));
pGeo.setAttribute('size', new THREE.BufferAttribute(pSize, 1));
pGeo.setAttribute('alpha', new THREE.BufferAttribute(pAlpha, 1));

const pMat = new THREE.ShaderMaterial({
  transparent: true,
  depthWrite: false,
  vertexShader: `
    attribute float size;
    attribute float alpha;
    attribute vec3 color;
    varying float vAlpha;
    varying vec3 vColor;
    void main(){
      vAlpha = alpha;
      vColor = color;
      vec4 mv = modelViewMatrix * vec4(position, 1.0);
      gl_PointSize = size * (330.0 / max(-mv.z, 1.0));
      gl_Position = projectionMatrix * mv;
    }`,
  fragmentShader: `
    varying float vAlpha;
    varying vec3 vColor;
    void main(){
      vec2 c = gl_PointCoord - 0.5;
      float d = length(c);
      float a = smoothstep(0.5, 0.06, d) * vAlpha;
      if (a < 0.01) discard;
      gl_FragColor = vec4(vColor, a);
    }`
});
const points = new THREE.Points(pGeo, pMat);
points.frustumCulled = false;
scene.add(points);

function spawnParticle(px, py, pz, vx, vy, vz, size, life, r, g, b) {
  const i = pCursor;
  pCursor = (pCursor + 1) % MAXP;
  const i3 = i * 3;
  pPos[i3] = px; pPos[i3 + 1] = py; pPos[i3 + 2] = pz;
  pVel[i3] = vx; pVel[i3 + 1] = vy; pVel[i3 + 2] = vz;
  pCol[i3] = r; pCol[i3 + 1] = g; pCol[i3 + 2] = b;
  pSize[i] = size;
  pLife[i] = life;
  pMaxLife[i] = life;
  pAlpha[i] = 0.6;
}

function updateParticles(dt) {
  for (let i = 0; i < MAXP; i++) {
    if (pLife[i] <= 0) continue;
    const i3 = i * 3;
    pLife[i] -= dt;
    pPos[i3] += pVel[i3] * dt;
    pPos[i3 + 1] += pVel[i3 + 1] * dt;
    pPos[i3 + 2] += pVel[i3 + 2] * dt;
    pVel[i3 + 1] -= 3.2 * dt;
    const damp = Math.max(0, 1 - 1.9 * dt);
    pVel[i3] *= damp;
    pVel[i3 + 2] *= damp;
    const lt = Math.max(0, pLife[i] / pMaxLife[i]);
    pAlpha[i] = lt * 0.55;
    pSize[i] += dt * 2.6;
    if (pLife[i] <= 0) { pAlpha[i] = 0; pPos[i3 + 1] = -9999; }
  }
  pGeo.attributes.position.needsUpdate = true;
  pGeo.attributes.alpha.needsUpdate = true;
  pGeo.attributes.size.needsUpdate = true;
  pGeo.attributes.color.needsUpdate = true;
}

/* ============================================================
   KART MODEL
   ============================================================ */
const KART_COLORS = [0xe63946, 0x2f7ef2, 0xffcf33, 0x35c46a, 0xa855f7, 0xff8b3d];
const KART_HELMETS = [0xffffff, 0x111111, 0x1b1b1f, 0xffffff, 0xffe066, 0x1b1b1f];
const KART_NAMES = ['REX', 'BLAZE', 'KIWI', 'NITRO', 'VOLT', 'DASH'];

function makeKart(color, helmet) {
  const group = new THREE.Group();
  const bodyMat = new THREE.MeshStandardMaterial({ color, roughness: 0.42, metalness: 0.25 });
  const darkMat = new THREE.MeshStandardMaterial({ color: 0x23242b, roughness: 0.85 });
  const helmMat = new THREE.MeshStandardMaterial({ color: helmet, roughness: 0.3, metalness: 0.2 });
  const suitMat = new THREE.MeshStandardMaterial({ color, roughness: 0.85 });
  const glassMat = new THREE.MeshStandardMaterial({ color: 0x1b2a3a, roughness: 0.15, metalness: 0.7 });
  const rimMat = new THREE.MeshStandardMaterial({ color: 0xdcdce2, roughness: 0.35, metalness: 0.6 });

  const chassis = new THREE.Mesh(new THREE.BoxGeometry(1.85, 0.5, 3.2), bodyMat);
  chassis.position.y = 0.63;
  group.add(chassis);

  const nose = new THREE.Mesh(new THREE.BoxGeometry(1.15, 0.34, 1.2), bodyMat);
  nose.position.set(0, 0.55, 1.95);
  group.add(nose);

  const wing = new THREE.Mesh(new THREE.BoxGeometry(2.2, 0.11, 0.62), darkMat);
  wing.position.set(0, 0.38, 2.55);
  group.add(wing);

  for (const s of [-1, 1]) {
    const pod = new THREE.Mesh(new THREE.BoxGeometry(0.52, 0.42, 1.75), bodyMat);
    pod.position.set(s * 1.04, 0.63, -0.12);
    group.add(pod);
  }

  const engine = new THREE.Mesh(new THREE.BoxGeometry(1.05, 0.5, 0.65), darkMat);
  engine.position.set(0, 0.88, -1.5);
  group.add(engine);

  const seat = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.72, 0.32), darkMat);
  seat.position.set(0, 1.02, -0.52);
  group.add(seat);

  const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.4, 0.76, 10), suitMat);
  torso.position.set(0, 1.28, -0.34);
  group.add(torso);

  const head = new THREE.Mesh(new THREE.SphereGeometry(0.32, 14, 12), helmMat);
  head.position.set(0, 1.8, -0.3);
  group.add(head);

  const visor = new THREE.Mesh(new THREE.BoxGeometry(0.44, 0.15, 0.09), glassMat);
  visor.position.set(0, 1.83, -0.0);
  group.add(visor);

  for (const s of [-1, 1]) {
    const arm = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, 0.62, 6), suitMat);
    arm.position.set(s * 0.36, 1.18, 0.05);
    arm.rotation.x = -0.7;
    arm.rotation.z = s * 0.25;
    group.add(arm);
  }

  const wheels = [];
  for (const [sx, sz] of [[-1, 1], [1, 1], [-1, -1], [1, -1]]) {
    const pivot = new THREE.Group();
    pivot.position.set(sx * 1.0, 0.47, sz * 1.15);

    const spin = new THREE.Group();
    const tyre = new THREE.Mesh(new THREE.CylinderGeometry(0.47, 0.47, 0.36, 16), darkMat);
    tyre.rotation.z = Math.PI / 2;
    spin.add(tyre);
    const rim = new THREE.Mesh(new THREE.CylinderGeometry(0.23, 0.23, 0.38, 10), rimMat);
    rim.rotation.z = Math.PI / 2;
    spin.add(rim);

    pivot.add(spin);
    group.add(pivot);
    wheels.push({ pivot, spin, front: sz > 0 });
  }

  group.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = false; } });
  return { group, wheels };
}

/* ============================================================
   KART LOGIC
   ============================================================ */
const _v1 = new THREE.Vector3(), _v2 = new THREE.Vector3(), _v3 = new THREE.Vector3();
const _v4 = new THREE.Vector3(), _v5 = new THREE.Vector3(), _v6 = new THREE.Vector3();
const _q1 = new THREE.Quaternion(), _q2 = new THREE.Quaternion();
const _m1 = new THREE.Matrix4();

class Kart {
  constructor(i) {
    this.i = i;
    const model = makeKart(KART_COLORS[i], KART_HELMETS[i]);
    this.group = model.group;
    this.wheels = model.wheels;
    scene.add(this.group);

    const row = Math.floor(i / 2);
    const col = i % 2;

    this.s = mod(TOTAL - 9 - row * 9.5, TOTAL);
    this.x = col === 0 ? -3.3 : 3.3;
    this.speed = 0;
    this.lap = 0;
    this.finished = false;
    this.finishTime = 0;

    this.skill = 0.955 + Math.random() * 0.09;
    this.lineBias = (i % 2 === 0 ? 1 : -1) * (0.4 + Math.random() * 1.5);

    this.steer = 0;
    this.spin = 0;
    this.slip = 0;
    this.roll = 0;
    this.drift = 0;
    this.latVel = 0;
    this.dustTimer = 0;
    this.bump = 0;

    this.pos = new THREE.Vector3();
    this.forward = new THREE.Vector3(0, 0, 1);

    this.updateVisual(0);
  }

  progress() {
    if (this.finished) return 1e6 - this.finishTime;
    return (this.lap - 1) * TOTAL + this.s;
  }

  update(dt, karts, leaderProgress) {
    const i0 = Math.floor(mod(this.s, TOTAL) / TOTAL * N) % N;

    /* ---- target speed with braking-distance look-ahead ---- */
    let want = MAX_SPEED * this.skill;
    for (let j = 0; j < 130; j += 4) {
      const k = (i0 + j) % N;
      const d = j * DS;
      const v = Math.sqrt(speedAt[k] * speedAt[k] + 74 * d);
      if (v < want) want = v;
    }

    /* rubber-banding to keep the pack interesting */
    const gap = leaderProgress - this.progress();
    if (gap > 30) want *= 1 + Math.min(0.16, gap / 2600);

    /* ---- lateral target: racing line + personal bias ---- */
    let xWant = raceOff[i0] + this.lineBias;

    /* ---- overtaking / avoidance ---- */
    for (const o of karts) {
      if (o === this) continue;
      const g = mod(o.s - this.s, TOTAL);
      if (g > 0 && g < 18) {
        const dx = this.x - o.x;
        if (Math.abs(dx) < 3.7) {
          let side;
          if (o.x > 0.8) side = -1;
          else if (o.x < -0.8) side = 1;
          else side = (this.lineBias > 0 ? 1 : -1);
          xWant = o.x + side * 4.4;
          if (g < 7.5) want *= 0.88;
        }
      }
    }
    xWant = clamp(xWant, -5.7, 5.7);

    /* ---- lateral movement ---- */
    const rate = 11;
    let step = clamp(xWant - this.x, -rate * dt, rate * dt);
    this.x += step;
    this.x = clamp(this.x, -5.7, 5.7);
    const inst = dt > 0 ? step / dt : 0;
    this.latVel += (inst - this.latVel) * Math.min(1, dt * 8);

    /* ---- speed dynamics ---- */
    const accel = 46, brake = 82;
    if (this.speed < want) this.speed = Math.min(want, this.speed + accel * dt);
    else this.speed = Math.max(want, this.speed - brake * dt);
    this.speed = clamp(this.speed, 0, MAX_SPEED * 1.2);

    /* ---- advance along the track ---- */
    this.s += this.speed * dt;
    if (this.s >= TOTAL) { this.s -= TOTAL; this.lap++; }

    /* ---- drift / style values ---- */
    const kk = curv[i0];
    const corner = Math.min(1, Math.abs(kk) * this.speed * 0.42);
    const slide = Math.min(1, Math.abs(this.latVel) * 0.09);
    this.drift += (Math.max(corner, slide) - this.drift) * Math.min(1, dt * 6);

    const slipTarget = -Math.sign(kk || 1) * this.drift * 0.30;
    this.slip += (slipTarget - this.slip) * Math.min(1, dt * 6);

    const rollTarget = clamp(kk * 90 * (this.speed / MAX_SPEED), -0.17, 0.17);
    this.roll += (rollTarget - this.roll) * Math.min(1, dt * 5);

    const steerTarget = clamp(-kk * 19 - this.latVel * 0.035, -0.5, 0.5);
    this.steer += (steerTarget - this.steer) * Math.min(1, dt * 10);

    this.spin += this.speed * dt / 0.47;

    /* ---- dust from the rear wheels ---- */
    if (this.drift > 0.28 && this.speed > 22) {
      this.dustTimer -= dt;
      if (this.dustTimer <= 0) {
        this.dustTimer = 0.022;
        const side = _v2.crossVectors(UP, this.forward).normalize();
        const back = _v3.copy(this.pos).addScaledVector(this.forward, -1.25);
        const shade = 0.62 + Math.random() * 0.22;
        for (const sgn of [-1, 1]) {
          const p = back.clone().addScaledVector(side, sgn * 0.98);
          p.y += 0.22;
          const spd = 2 + Math.random() * 5;
          spawnParticle(
            p.x, p.y, p.z,
            -this.forward.x * spd + (Math.random() - 0.5) * 3 + side.x * sgn * 1.5,
            0.9 + Math.random() * 1.6,
            -this.forward.z * spd + (Math.random() - 0.5) * 3 + side.z * sgn * 1.5,
            0.7 + Math.random() * 0.7,
            0.7 + Math.random() * 0.5,
            shade, shade * 0.97, shade * 0.88
          );
        }
      }
    }
  }

  updateVisual(dt) {
    const fi = mod(this.s, TOTAL) / TOTAL * N;
    const i0 = Math.floor(fi) % N;
    const i1 = (i0 + 1) % N;
    const f = fi - Math.floor(fi);

    const p = _v1.lerpVectors(pts[i0], pts[i1], f);
    const r = _v2.lerpVectors(rights[i0], rights[i1], f).normalize();
    const t = _v3.lerpVectors(tans[i0], tans[i1], f).normalize();
    p.addScaledVector(r, this.x);

    this.pos.copy(p);
    this.forward.copy(t);

    const xk = _v4.crossVectors(UP, t).normalize();
    const upk = _v5.crossVectors(t, xk).normalize();
    const fwd = _v6.copy(t);

    _q1.setFromAxisAngle(upk, this.slip);
    xk.applyQuaternion(_q1);
    fwd.applyQuaternion(_q1);

    _q2.setFromAxisAngle(fwd, this.roll);
    xk.applyQuaternion(_q2);
    upk.applyQuaternion(_q2);

    _m1.makeBasis(xk, upk, fwd);
    this.group.quaternion.setFromRotationMatrix(_m1);

    this.bump += dt * 20;
    const bob = Math.sin(this.bump) * 0.012 * Math.min(1, this.speed / 40);
    this.group.position.set(p.x, p.y + bob, p.z);

    for (const w of this.wheels) {
      w.spin.rotation.x = -this.spin;
      if (w.front) w.pivot.rotation.y = this.steer;
    }
  }
}

/* ============================================================
   CREATE KARTS
   ============================================================ */
const KARTS = [];
for (let i = 0; i < 6; i++) KARTS.push(new Kart(i));

/* ============================================================
   HUD
   ============================================================ */
const listEl = document.getElementById('list');
const lapNumEl = document.getElementById('lapNum');
const lapTotEl = document.getElementById('lapTot');
const raceTimeEl = document.getElementById('raceTime');
const countdownEl = document.getElementById('countdown');
const bannerEl = document.getElementById('banner');
lapTotEl.textContent = TOTAL_LAPS;

const rows = KARTS.map((k, i) => {
  const d = document.createElement('div');
  d.className = 'row';
  const hex = '#' + KART_COLORS[i].toString(16).padStart(6, '0');
  d.innerHTML = `<span class="pos">${i + 1}</span><span class="chip" style="background:${hex}"></span><span class="name">${KART_NAMES[i]}</span>`;
  listEl.appendChild(d);
  return d;
});

let raceOrder = KARTS.slice();

function updateHUD() {
  for (let i = 0; i < raceOrder.length; i++) {
    const k = raceOrder[i];
    const row = rows[k.i];
    row.style.order = i;
    row.querySelector('.pos').textContent = (i + 1);
    row.classList.toggle('lead', i === 0);
  }
  const leader = raceOrder[0];
  lapNumEl.textContent = clamp(Math.max(1, leader.lap), 1, TOTAL_LAPS);

  const t = Math.max(0, raceTime);
  const mm = Math.floor(t / 60);
  const ss = Math.floor(t % 60);
  raceTimeEl.textContent = `${mm}:${ss.toString().padStart(2, '0')}`;
}

function showCountdown(text, isGo) {
  countdownEl.textContent = text;
  countdownEl.classList.remove('show', 'go');
  void countdownEl.offsetWidth;
  if (isGo) countdownEl.classList.add('go');
  countdownEl.classList.add('show');
}

/* ============================================================
   RACE STATE
   ============================================================ */
let state = 'countdown';
let stateTimer = 0;
let raceTime = 0;
let finishOrder = [];
let lastCountStep = -1;

const cam = {
  mode: 'grid',
  timer: 5,
  look: new THREE.Vector3(),
  sidePos: new THREE.Vector3(),
  initialized: false
};

function resetRace() {
  for (const k of KARTS) {
    const row = Math.floor(k.i / 2);
    const col = k.i % 2;
    k.s = mod(TOTAL - 9 - row * 9.5, TOTAL);
    k.x = col === 0 ? -3.3 : 3.3;
    k.speed = 0;
    k.lap = 0;
    k.finished = false;
    k.finishTime = 0;
    k.slip = 0;
    k.roll = 0;
    k.drift = 0;
    k.latVel = 0;
    k.steer = 0;
    k.skill = 0.955 + Math.random() * 0.09;
    k.lineBias = (k.i % 2 === 0 ? 1 : -1) * (0.4 + Math.random() * 1.5);
    k.updateVisual(0);
  }
  for (let i = 0; i < MAXP; i++) { pLife[i] = 0; pAlpha[i] = 0; pPos[i * 3 + 1] = -9999; }

  state = 'countdown';
  stateTimer = 0;
  raceTime = 0;
  finishOrder = [];
  lastCountStep = -1;
  cam.mode = 'grid';
  cam.timer = 5;
  cam.initialized = false;
  bannerEl.classList.remove('show');
  updateHUD();
}

/* ============================================================
   CAMERA
   ============================================================ */
function pickSideCam(leader) {
  const li = Math.floor(mod(leader.s, TOTAL) / TOTAL * N) % N;
  const ahead = 55 + Math.floor(Math.random() * 140);
  const k = (li + ahead) % N;
  const side = Math.random() < 0.5 ? 1 : -1;
  const off = HW + 9 + Math.random() * 13;
  const p = pts[k], r = rights[k];
  cam.sidePos.set(
    p.x + r.x * side * off,
    p.y + 3.4 + Math.random() * 5.2,
    p.z + r.z * side * off
  );
}

function updateCamera(dt) {
  const leader = raceOrder[0];

  if (state === 'countdown' || state === 'finished') {
    if (state === 'countdown') {
      const p = pts[0], r = rights[0], t = tans[0];
      const cp = p.clone().addScaledVector(r, 24).addScaledVector(t, -18);
      cp.y += 11;
      if (!cam.initialized) { camera.position.copy(cp); cam.initialized = true; }
      else camera.position.lerp(cp, 1 - Math.exp(-2.2 * dt));

      const look = KARTS[2].pos.clone().lerp(KARTS[5].pos, 0.35);
      look.y += 1.2;
      if (cam.initialized) cam.look.lerp(look, 1 - Math.exp(-4 * dt));
      else cam.look.copy(look);
      camera.lookAt(cam.look);
      camera.fov = 55;
      camera.updateProjectionMatrix();
      return;
    }
    /* finished: slow orbit around the leader */
    const ang = stateTimer * 0.55;
    const cp = leader.pos.clone().add(new THREE.Vector3(Math.cos(ang) * 16, 8, Math.sin(ang) * 16));
    camera.position.lerp(cp, 1 - Math.exp(-3 * dt));
    cam.look.lerp(leader.pos.clone().add(new THREE.Vector3(0, 1.2, 0)), 1 - Math.exp(-4 * dt));
    camera.lookAt(cam.look);
    camera.fov = 58;
    camera.updateProjectionMatrix();
    return;
  }

  /* --- racing --- */
  cam.timer -= dt;
  if (cam.timer <= 0) {
    if (cam.mode === 'chase') {
      cam.mode = 'side';
      cam.timer = 2.8 + Math.random() * 1.6;
      pickSideCam(leader);
    } else {
      cam.mode = 'chase';
      cam.timer = 6 + Math.random() * 3.5;
    }
  }

  if (cam.mode === 'chase') {
    const fwd = leader.forward;
    const desired = leader.pos.clone().addScaledVector(fwd, -11.5).add(new THREE.Vector3(0, 5.0, 0));
    desired.y = Math.max(desired.y, leader.pos.y + 3.2);
    camera.position.lerp(desired, 1 - Math.exp(-8 * dt));

    const look = leader.pos.clone().addScaledVector(fwd, 10).add(new THREE.Vector3(0, 1.7, 0));
    cam.look.lerp(look, 1 - Math.exp(-10 * dt));
    camera.lookAt(cam.look);

    const targetFov = 62 + Math.min(14, leader.speed * 0.16);
    camera.fov += (targetFov - camera.fov) * Math.min(1, dt * 3);
    camera.updateProjectionMatrix();
  } else {
    camera.position.copy(cam.sidePos);
    const look = leader.pos.clone().add(new THREE.Vector3(0, 1.1, 0));
    cam.look.lerp(look, 1 - Math.exp(-6 * dt));
    camera.lookAt(cam.look);
    camera.fov += (50 - camera.fov) * Math.min(1, dt * 5);
    camera.updateProjectionMatrix();
  }
}

/* ============================================================
   MAIN LOOP
   ============================================================ */
const clock = new THREE.Clock();

function animate() {
  const dt = Math.min(0.05, clock.getDelta());

  stateTimer += dt;

  /* ---- state machine ---- */
  if (state === 'countdown') {
    const step = Math.floor(stateTimer);
    if (step !== lastCountStep) {
      lastCountStep = step;
      if (step === 0) showCountdown('3', false);
      else if (step === 1) showCountdown('2', false);
      else if (step === 2) showCountdown('1', false);
      else if (step === 3) {
        showCountdown('GO!', true);
        state = 'racing';
        stateTimer = 0;
        cam.mode = 'chase';
        cam.timer = 5.5;
        cam.initialized = false;
      }
    }
  } else if (state === 'racing') {
    raceTime += dt;
  }

  /* ---- order ---- */
  raceOrder = KARTS.slice().sort((a, b) => b.progress() - a.progress());
  const leaderProgress = raceOrder[0].progress();

  /* ---- kart updates ---- */
  if (state === 'racing') {
    for (const k of KARTS) {
      if (!k.finished && k.lap > TOTAL_LAPS) {
        k.finished = true;
        k.finishTime = raceTime;
        finishOrder.push(k);
      }
    }
    for (const k of KARTS) {
      if (!k.finished) k.update(dt, KARTS, leaderProgress);
      else {
        /* finished: keep rolling gently */
        k.speed *= (1 - 0.7 * dt);
        k.s += k.speed * dt;
        if (k.s >= TOTAL) k.s -= TOTAL;
      }
    }

    /* ---- collisions ---- */
    for (let a = 0; a < KARTS.length; a++) {
      for (let b = a + 1; b < KARTS.length; b++) {
        const A = KARTS[a], B = KARTS[b];
        const g1 = mod(B.s - A.s, TOTAL);
        const dsA = Math.min(g1, TOTAL - g1);
        if (dsA > 4.2) continue;
        const dx = B.x - A.x;
        if (Math.abs(dx) > 2.7) continue;
        const dir = Math.abs(dx) < 0.001 ? (a % 2 === 0 ? 1 : -1) : Math.sign(dx);
        const push = (2.7 - Math.abs(dx)) * 0.5;
        A.x -= dir * push * 0.6;
        B.x += dir * push * 0.6;
        A.x = clamp(A.x, -5.8, 5.8);
        B.x = clamp(B.x, -5.8, 5.8);
        const avg = (A.speed + B.speed) * 0.5;
        A.speed = lerp(A.speed, avg, 0.08);
        B.speed = lerp(B.speed, avg, 0.08);
      }
    }
  } else if (state === 'countdown') {
    /* revving in place */
    for (const k of KARTS) {
      k.speed = 0;
      k.spin += dt * 2;
      k.drift = 0;
    }
  }

  /* ---- visuals ---- */
  for (const k of KARTS) k.updateVisual(dt);

  /* ---- race end ---- */
  if (state === 'racing') {
    const allDone = finishOrder.length === KARTS.length;
    const timeout = finishOrder.length > 0 && (raceTime - finishOrder[0].finishTime) > 7;
    if (allDone || timeout) {
      state = 'finished';
      stateTimer = 0;
      const top = finishOrder.slice(0, 3).map((k, i) => `${i + 1}. ${KART_NAMES[k.i]}`).join('   ');
      bannerEl.innerHTML = `RACE FINISHED<div class="small">${top}</div>`;
      bannerEl.classList.add('show');
      showCountdown('', false);
      countdownEl.classList.remove('show');
    }
  } else if (state === 'finished' && stateTimer > 6.0) {
    resetRace();
  }

  /* ---- particles ---- */
  updateParticles(dt);

  /* ---- hud ---- */
  updateHUD();

  /* ---- camera ---- */
  updateCamera(dt);

  /* ---- sun follows the leader for crisp shadows ---- */
  const L = raceOrder[0].pos;
  sun.target.position.set(Math.round(L.x), Math.round(L.y), Math.round(L.z));
  sun.position.set(L.x + 70, L.y + 110, L.z + 50);
  sun.target.updateMatrixWorld();

  renderer.render(scene, camera);
}

/* ============================================================
   RESIZE + START
   ============================================================ */
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

resetRace();
renderer.setAnimationLoop(animate);
</script>
</body>
</html>
```
### Race Mechanics & Camera Cuts

This whole thing is a self-contained racing simulation that runs on its own, so you can just watch it loop.

- **AI driving & overtaking** — Each kart picks a racing line with a small personal bias, checks the road ahead for corners, and eases off the throttle before turns. When another kart is close, it slides to the side to pass or tucks in behind.
- **Track & drift feedback** — The closed circuit includes elevation changes, kerbs, grass verges, and roadside objects. Karts lean into corners, turn their front wheels, and kick up dust particles from the rear tires when drifting.
- **Race flow & HUD** — A 3-2-1 countdown starts the race. A live position list orders all six karts from first to sixth, while the lap counter and race timer update as the leader progresses. The race lasts two laps and then resets automatically.
- **Cameras** — A chase camera follows the leading kart, then occasionally cuts to a fixed trackside angle before returning to the chase. The countdown and finish screens use centered overlays.
---

**Optimization Tip:** To adjust difficulty or race length, change `MAX_SPEED` or `TOTAL_LAPS` near the top of the script. You can also edit `KART_COLORS` and `KART_NAMES` to customize the grid.