```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Neon City Flythrough</title>
<style>
  html, body {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
    background: #000;
  }
  canvas { display: block; }
</style>
</head>
<body>
<script type="module">
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { Reflector } from 'three/addons/objects/Reflector.js';

// ---------------------------------------------------------------
// Renderer / scene / camera
// ---------------------------------------------------------------
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x04050c);
// Volumetric-looking fog: dense exponential haze tinted deep blue
scene.fog = new THREE.FogExp2(0x070a18, 0.0052);

const camera = new THREE.PerspectiveCamera(62, window.innerWidth / window.innerHeight, 0.1, 1500);

// ---------------------------------------------------------------
// Lights
// ---------------------------------------------------------------
scene.add(new THREE.HemisphereLight(0x1c2246, 0x04050c, 0.55));
const moon = new THREE.DirectionalLight(0x3a4a8a, 0.5);
moon.position.set(-200, 300, -100);
scene.add(moon);

// ---------------------------------------------------------------
// Window textures (canvas generated, emissive)
// ---------------------------------------------------------------
function makeWindowTexture() {
  const c = document.createElement('canvas');
  c.width = 64; c.height = 128;
  const g = c.getContext('2d');
  g.fillStyle = '#05060c';
  g.fillRect(0, 0, 64, 128);
  const cols = 8, rows = 28;
  const cw = 64 / cols, ch = 128 / rows;
  const palette = ['#ffd9a0', '#cfe8ff', '#ffffff', '#9fd8ff', '#ffb3d9', '#e8fff2'];
  for (let i = 0; i < cols; i++) {
    for (let j = 0; j < rows; j++) {
      if (Math.random() < 0.34) {
        const col = palette[(Math.random() * palette.length) | 0];
        const a = 0.35 + Math.random() * 0.65;
        g.globalAlpha = a;
        g.fillStyle = col;
        g.fillRect(i * cw + 1.5, j * ch + 1.5, cw - 3, ch - 3);
      }
    }
  }
  g.globalAlpha = 1;
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  return tex;
}

const buildingMats = [];
for (let i = 0; i < 4; i++) {
  const t = makeWindowTexture();
  buildingMats.push(new THREE.MeshStandardMaterial({
    color: 0x0b0c14,
    roughness: 0.85,
    metalness: 0.15,
    emissive: 0xffffff,
    emissiveMap: t,
    emissiveIntensity: 1.15,
    map: t
  }));
}

// ---------------------------------------------------------------
// Camera path (defined early so buildings can avoid it)
// ---------------------------------------------------------------
const camCurve = new THREE.CatmullRomCurve3([
  new THREE.Vector3(-390, 55,   0),
  new THREE.Vector3(-260, 32,  38),
  new THREE.Vector3(-130, 95, -25),
  new THREE.Vector3(  20, 40,  34),
  new THREE.Vector3( 150, 105, -28),
  new THREE.Vector3( 300, 48,  42),
  new THREE.Vector3( 420, 85,   0),
], true, 'centripetal');

const camSamples = [];
for (let i = 0; i < 500; i++) camSamples.push(camCurve.getPointAt(i / 500));

function nearCamPath(x, z, r) {
  for (const p of camSamples) {
    const dx = p.x - x, dz = p.z - z;
    if (dx * dx + dz * dz < r * r) return true;
  }
  return false;
}

// ---------------------------------------------------------------
// Buildings + neon signs
// ---------------------------------------------------------------
const buildings = new THREE.Group();
scene.add(buildings);
const bBoxes = []; // AABB data for car collision
const pointLightSpots = [];

const NEON = [new THREE.Color(0xff2f9e), new THREE.Color(0x00e5ff), new THREE.Color(0xa14dff)];

function addNeon(mat, x, y, z, sx, sy, sz, color, rotY) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(sx, sy, sz), mat);
  m.position.set(x, y, z);
  if (rotY) m.rotation.y = rotY;
  buildings.add(m);
}

const neonMatCache = {};
function neonMat(color) {
  const key = color.getHexString();
  if (!neonMatCache[key]) {
    neonMatCache[key] = new THREE.MeshBasicMaterial({ color: color.clone().multiplyScalar(3.0) });
  }
  return neonMatCache[key];
}

const rnd = (a, b) => a + Math.random() * (b - a);

for (let gx = -440; gx <= 440; gx += 44) {
  for (let gz = -440; gz <= 440; gz += 44) {
    const x = gx + rnd(-12, 12);
    const z = gz + rnd(-12, 12);
    if (Math.abs(x) < 20 || Math.abs(z) < 20) continue;         // main streets
    if (nearCamPath(x, z, 30)) continue;                        // corridor for camera
    if (Math.random() < 0.06) continue;                         // occasional lots

    const w = rnd(12, 26);
    const d = rnd(12, 26);
    const h = 25 + Math.pow(Math.random(), 1.55) * 150;
    const mat = buildingMats[(Math.random() * buildingMats.length) | 0];
    const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
    b.position.set(x, h / 2, z);
    buildings.add(b);
    bBoxes.push({ x1: x - w / 2 - 3, x2: x + w / 2 + 3, y1: 0, y2: h + 3, z1: z - d / 2 - 3, z2: z + d / 2 + 3 });

    // ---- neon signage ----
    if (Math.random() < 0.5) {
      const col = NEON[(Math.random() * NEON.length) | 0];
      const nm = neonMat(col);
      const corner = Math.random() < 0.5 ? -1 : 1;
      if (Math.random() < 0.5) {
        // vertical corner strip
        const hs = rnd(10, Math.min(h * 0.7, 55));
        addNeon(nm, x + corner * (w / 2 + 0.15), rnd(h * 0.2, h - hs), z + rnd(-1, 1), 0.9, hs, 0.9);
      } else {
        // side billboard
        const sw = rnd(5, 13), sh = rnd(1.5, 4);
        const side = Math.random();
        if (side < 0.5)      addNeon(nm, x + corner * (w / 2 + 0.2), rnd(h * 0.3, h - 6), z, 0.5, sh, sw);
        else if (side < 0.9) addNeon(nm, x + rnd(-1, 1), rnd(h * 0.3, h - 6), z + corner * (d / 2 + 0.2), sw, sh, 0.5);
        else                 addNeon(nm, x, h + rnd(2, 6), z, sw, sh, 0.4); // roof sign
      }
      if (!nearCamPath(x, z, 90) && false) {} // (kept simple)
      if (!nearCamPath(x, z, 70)) pointLightSpots.push([x, rnd(h * 0.3, h * 0.7), z, col]);
    }
  }
}

// A handful of neon point lights to tint nearby geometry
const plCount = Math.min(12, pointLightSpots.length);
for (let i = 0; i < plCount; i++) {
  const [x, y, z, col] = pointLightSpots[i];
  const pl = new THREE.PointLight(col, 250, 140, 2);
  pl.position.set(x, y, z);
  scene.add(pl);
}

// ---------------------------------------------------------------
// Wet reflective street (Reflector + dimming overlay + glow lines)
// ---------------------------------------------------------------
const street = new Reflector(new THREE.PlaneGeometry(1100, 1100), {
  clipBias: 0.003,
  textureWidth: 1024,
  textureHeight: 1024,
  color: 0x8a92a8
});
street.rotation.x = -Math.PI / 2;
street.position.y = 0;
scene.add(street);

// Dark semi-transparent veil over the mirror to make it look wet, not glass
const veil = new THREE.Mesh(
  new THREE.PlaneGeometry(1100, 1100),
  new THREE.MeshBasicMaterial({ color: 0x04060e, transparent: true, opacity: 0.55, depthWrite: false })
);
veil.rotation.x = -Math.PI / 2;
veil.position.y = 0.03;
veil.renderOrder = 2;
scene.add(veil);

// Faint cyan street edge lines
const lineMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(0x00e5ff).multiplyScalar(0.7) });
for (const axis of ['x', 'z']) {
  const geo = new THREE.BoxGeometry(axis === 'x' ? 900 : 0.4, 0.05, axis === 'x' ? 0.4 : 900);
  for (const o of [-4, 4]) {
    const l = new THREE.Mesh(geo, lineMat);
    if (axis === 'x') l.position.set(0, 0.06, o); else l.position.set(o, 0.06, 0);
    scene.add(l);
  }
}

// ---------------------------------------------------------------
// Flying cars
// ---------------------------------------------------------------
const cars = [];

function curveHits(curve, padY) {
  let maxBlock = 0;
  const p = new THREE.Vector3();
  for (let i = 0; i < 110; i++) {
    curve.getPointAt(i / 110, p);
    for (const b of bBoxes) {
      if (p.x > b.x1 && p.x < b.x2 && p.y > b.y1 && p.y < b.y2 + padY && p.z > b.z1 && p.z < b.z2) {
        if (b.y2 > maxBlock) maxBlock = b.y2;
      }
    }
  }
  return maxBlock;
}

const carBodyMat = new THREE.MeshStandardMaterial({ color: 0x141826, metalness: 0.9, roughness: 0.3 });
const white = new THREE.MeshBasicMaterial({ color: new THREE.Color(0xffffff).multiplyScalar(4) });
const red   = new THREE.MeshBasicMaterial({ color: new THREE.Color(0xff2244).multiplyScalar(4) });

for (let ci = 0; ci < 8; ci++) {
  const cx = rnd(-150, 150), cz = rnd(-150, 150);
  const radius = rnd(160, 320);
  let alt = rnd(35, 130);
  let pts = [];
  const n = 6 + (Math.random() * 3 | 0);
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2;
    pts.push(new THREE.Vector3(
      cx + Math.cos(a) * radius + rnd(-60, 60),
      alt + rnd(-14, 14),
      cz + Math.sin(a) * radius + rnd(-60, 60)
    ));
  }
  let curve = new THREE.CatmullRomCurve3(pts, true, 'centripetal');
  for (let tries = 0; tries < 12; tries++) {
    const block = curveHits(curve, 0);
    if (block === 0) break;
    const lift = block + rnd(8, 16);
    for (const p of pts) if (p.y < lift) p.y = lift + rnd(0, 10);
    curve = new THREE.CatmullRomCurve3(pts, true, 'centripetal');
  }

  const g = new THREE.Group();
  const body = new THREE.Mesh(new THREE.BoxGeometry(3.4, 0.7, 1.4), carBodyMat);
  const lightbar = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.16, 1.2), white);
  lightbar.position.set(1.3, -0.28, 0);
  const tail = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.25, 1.2), red);
  tail.position.set(-1.7, 0.05, 0);
  g.add(body, lightbar, tail);
  scene.add(g);

  cars.push({
    group: g,
    curve,
    u: Math.random(),
    speed: rnd(0.008, 0.02) * (Math.random() < 0.5 ? -1 : 1),
    tmpPos: new THREE.Vector3(),
    tmpAhead: new THREE.Vector3()
  });
}

// ---------------------------------------------------------------
// Post-processing: bloom
// ---------------------------------------------------------------
const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const bloomPass = new UnrealBloomPass(
  new THREE.Vector2(window.innerWidth, window.innerHeight),
  1.15,  // strength
  0.75,  // radius
  0.18   // threshold
);
composer.addPass(bloomPass);
composer.addPass(new OutputPass());

// ---------------------------------------------------------------
// Animation (uses rAF timestamp)
// ---------------------------------------------------------------
const lookTarget = camCurve.getPointAt(0.02).clone();
let lastTime = 0;

function animate(time) {
  requestAnimationFrame(animate);
  const t = time * 0.001; // seconds
  const dt = Math.min(Math.max((time - lastTime) * 0.001, 0), 0.1);
  lastTime = time;

  // --- camera glide along closed path ---
  const u = (t * 0.011) % 1;
  const pos = camCurve.getPointAt(u);
  pos.y += Math.sin(t * 0.45) * 2.2; // gentle vertical bob
  camera.position.copy(pos);

  camCurve.getPointAt((u + 0.022) % 1, lookTarget);
  // frame-rate independent smoothing toward the ahead-point
  const k = 1 - Math.pow(0.0005, dt);
  const smooth = new THREE.Vector3().lerpVectors(camera.userData.lt || lookTarget.clone(), lookTarget, k);
  camera.userData.lt = smooth;
  camera.lookAt(smooth);
  camera.rotation.z += Math.sin(t * 0.21) * 0.012 + Math.sin(t * 0.53 + 1.7) * 0.006; // subtle roll

  // --- cars ---
  for (const c of cars) {
    c.u = (c.u + dt * c.speed) % 1;
    if (c.u < 0) c.u += 1;
    c.curve.getPointAt(c.u, c.tmpPos);
    c.curve.getPointAt(((c.u + 0.006) % 1), c.tmpAhead);
    c.group.position.copy(c.tmpPos);
    c.group.lookAt(c.tmpAhead);
    if (c.speed < 0) c.group.rotateY(Math.PI); // tail lights face rear
  }

  composer.render();
}
requestAnimationFrame(animate);

// ---------------------------------------------------------------
// Resize handling
// ---------------------------------------------------------------
window.addEventListener('resize', () => {
  const w = window.innerWidth, h = window.innerHeight;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
  composer.setSize(w, h);
});
</script>
</body>
</html>
```