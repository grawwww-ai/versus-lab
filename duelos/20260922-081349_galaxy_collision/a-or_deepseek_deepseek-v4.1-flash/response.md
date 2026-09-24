Here's a self-contained HTML document that renders two spiral galaxies colliding in a cinematic scientific visualization. It uses three.js to simulate 44,000 stars with GPU‑cheap gravity, automatic camera motion, and a time label in millions of years. Just open it and the encounter starts immediately.
```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Spiral Galaxy Collision</title>
<style>
  html, body { margin:0; padding:0; height:100%; background:#000; overflow:hidden; }
  canvas { display:block; }
  #hud {
    position:fixed; left:20px; bottom:18px;
    font:12px/1.5 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    letter-spacing:.16em; color:#c3d9ff;
    text-shadow:0 0 12px rgba(80,150,255,.85);
    opacity:.9; pointer-events:none; user-select:none; white-space:nowrap;
  }
  #title {
    position:fixed; left:20px; top:18px;
    font:10px/1.5 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    letter-spacing:.3em; text-transform:uppercase;
    color:#7fa6f0; opacity:.5; pointer-events:none; user-select:none; white-space:nowrap;
  }
</style>
</head>
<body>
<div id="title">Spiral Encounter &middot; N-body</div>
<div id="hud">T + 0 Myr</div>

<script type="module">
import * as THREE from 'three';

/* ==================================================================
   Cheap N-body model of two colliding spiral galaxies.

   Every star is a massless test particle that feels:
     - the Plummer potential of its OWN galactic core (keeps the disk
       together, gives the rotation curve)
     - the point-mass potential of the COMPANION core (drives the
       tides -> tails & bridges)
   The two massive cores are integrated with the same softened force.

   The whole thing is analytic (no O(N^2)) so 44 000 stars stay smooth.
   ================================================================== */

/* ------------------------ configuration ------------------------- */
const N_BULGE = 4200;
const N_DISK  = 17800;
const N_PER   = N_BULGE + N_DISK;       // 22 000 stars per galaxy
const N_TOT   = N_PER * 2;              // 44 000 stars total

const G         = 1.0;
const MASS      = 1.4;                  // mass of each galactic core
const GM        = G * MASS;
const EPS2_SELF = 0.60 * 0.60;          // softening of own potential
const EPS2_EXT  = 0.45 * 0.45;          // softening of companion core
const EPS2_CC   = 0.40 * 0.40;          // core <-> core softening

const SIM_SPEED    = 0.28;              // sim-time units per real second
const MYR_PER_UNIT = 45;                // million years per sim-time unit
const H_STEP       = 0.003;             // fixed integration step
const MAX_SUB      = 6;                 // max sub-steps per frame

/* --------------------------- state ------------------------------ */
const pos = new Float32Array(N_TOT * 3);
const vel = new Float32Array(N_TOT * 3);
const col = new Float32Array(N_TOT * 3);
const siz = new Float32Array(N_TOT);

// Two galaxies on a hyperbolic encounter: r_p ≈ 2.2, separated by 6 at t=0.
const corePos = new Float64Array([ -3, 0, 0,   3, 0, 0 ]);
const coreVel = new Float64Array([  0.65052, -0.35823, 0,   -0.65052, 0.35823, 0 ]);

/* ------------------------- tiny helpers ------------------------- */
function gauss() {
  let u = 0, v = 0;
  while (u === 0) u = Math.random();
  while (v === 0) v = Math.random();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}
// circular speed in the Plummer potential  v = r sqrt(GM) / (r²+eps²)^(3/4)
function vcirc(r) {
  return r * Math.sqrt(GM) / Math.pow(r * r + EPS2_SELF, 0.75);
}
function sampleRadius() {
  let r = -0.42 * Math.log(1 - Math.random());
  let guard = 0;
  while (r > 1.45 && guard++ < 8) r = -0.42 * Math.log(1 - Math.random());
  return Math.min(r, 1.45);
}

/* ------------------- build the two disk galaxies ---------------- */
function diskBasis(q) {
  return [
    new THREE.Vector3(1, 0, 0).applyQuaternion(q),
    new THREE.Vector3(0, 1, 0).applyQuaternion(q),
    new THREE.Vector3(0, 0, 1).applyQuaternion(q)
  ];
}
const qA = new THREE.Quaternion();                                   // disk in XY plane
const qB = new THREE.Quaternion().setFromAxisAngle(
  new THREE.Vector3(0.45, 0.89, 0.1).normalize(), 0.62);             // companion tilted ~35°

const GAL = [
  { c: [-3, 0, 0], v: [ 0.65052, -0.35823, 0], basis: diskBasis(qA) },
  { c: [ 3, 0, 0], v: [-0.65052,  0.35823, 0], basis: diskBasis(qB) }
];

const ARM_TWIST = -2.48;     // negative => trailing arms (counter-clockwise spin)

for (let g = 0; g < 2; g++) {
  const gal = GAL[g];
  const [E1, E2, E3] = gal.basis;
  const e1x = E1.x, e1y = E1.y, e1z = E1.z;
  const e2x = E2.x, e2y = E2.y, e2z = E2.z;
  const e3x = E3.x, e3y = E3.y, e3z = E3.z;
  const cx = gal.c[0], cy = gal.c[1], cz = gal.c[2];
  const bvx = gal.v[0], bvy = gal.v[1], bvz = gal.v[2];
  const base = g * N_PER;

  for (let i = 0; i < N_PER; i++) {
    const p3 = (base + i) * 3;
    let lx = 0, ly = 0, lz = 0;      // position in the galaxy's disk frame
    let vx = 0, vy = 0, vz = 0;      // velocity in the galaxy's disk frame

    if (i < N_BULGE) {
      /* ---- bulge / core stars: luminous, warm, roughly spheroidal ---- */
      const r  = 0.26 * Math.pow(Math.random(), 0.72);
      const u  = Math.random() * 2 - 1;
      const ph = Math.random() * Math.PI * 2;
      const s  = Math.sqrt(1 - u * u);
      lx = r * s * Math.cos(ph);
      ly = r * s * Math.sin(ph);
      lz = r * u;

      const sp = 0.62 * vcirc(Math.max(r, 0.05));
      const u2  = Math.random() * 2 - 1;
      const ph2 = Math.random() * Math.PI * 2;
      const s2  = Math.sqrt(1 - u2 * u2);
      vx = sp * s2 * Math.cos(ph2);
      vy = sp * s2 * Math.sin(ph2);
      vz = sp * u2;

      const br = 0.42 + 0.30 * Math.random();      // dimmer so the core does not clip to flat white
      col[p3]     = 1.00 * br;
      col[p3 + 1] = 0.74 * br;
      col[p3 + 2] = 0.38 * br;
      siz[base + i] = 0.055 + 0.05 * Math.random();

    } else {
      /* ------------------- disk / spiral-arm star ------------------- */
      const r = sampleRadius();
      const inArm = Math.random() < 0.65;

      let th;
      if (inArm) {
        const arm = Math.random() < 0.5 ? 0 : 1;
        th = arm * Math.PI + ARM_TWIST * Math.log(Math.max(r, 0.10) / 0.26) + gauss() * 0.28;
      } else {
        th = Math.random() * Math.PI * 2;            // smooth underlying disk
      }
      const ct = Math.cos(th), st = Math.sin(th);

      lx = r * ct;
      ly = r * st;
      lz = gauss() * 0.05;                           // thin disk

      const vc = vcirc(r);
      vx = -vc * st + gauss() * 0.045;
      vy =  vc * ct + gauss() * 0.045;
      vz =  gauss() * 0.025;

      /* colour: warm yellow core  ->  blue-white arms */
      const t = Math.min(1, r / 1.35);
      const w = Math.pow(t, 0.8);
      const cr = 1.00 * (1 - w) + 0.52 * w;
      const cg = 0.78 * (1 - w) + 0.70 * w;
      const cb = 0.40 * (1 - w) + 1.00 * w;
      const j  = 0.78 + 0.45 * Math.random();
      col[p3]     = Math.min(1.25, cr * j);
      col[p3 + 1] = Math.min(1.25, cg * j);
      col[p3 + 2] = Math.min(1.25, cb * j);

      siz[base + i] = 0.042 + 0.07 * Math.random() + (inArm ? 0.022 : 0);
    }

    /* -------- rotate the local frame into world space -------- */
    pos[p3]     = cx + lx * e1x + ly * e2x + lz * e3x;
    pos[p3 + 1] = cy + lx * e1y + ly * e2y + lz * e3y;
    pos[p3 + 2] = cz + lx * e1z + ly * e2z + lz * e3z;

    vel[p3]     = bvx + vx * e1x + vy * e2x + vz * e3x;
    vel[p3 + 1] = bvy + vx * e1y + vy * e2y + vz * e3y;
    vel[p3 + 2] = bvz + vx * e1z + vy * e2z + vz * e3z;
  }
}

/* ============================ renderer =========================== */
const renderer = new THREE.WebGLRenderer({ antialias: false, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setClearColor(0x01020a, 1);
document.body.appendChild(renderer.domElement);

const scene  = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 4000);

/* ------------------------ glow point shader ---------------------- */
const pointMat = new THREE.ShaderMaterial({
  uniforms: {
    uScale: { value: 330.0 },
    uPR:    { value: renderer.getPixelRatio() }
  },
  vertexShader: /* glsl */`
    attribute float aSize;
    attribute vec3  aColor;
    uniform float uScale;
    uniform float uPR;
    varying vec3 vColor;
    void main() {
      vColor = aColor;
      vec4 mv = modelViewMatrix * vec4(position, 1.0);
      float d = max(-mv.z, 0.05);
      gl_PointSize = clamp(aSize * uScale * uPR / d, 1.0, 64.0);
      gl_Position = projectionMatrix * mv;
    }`,
  fragmentShader: /* glsl */`
    varying vec3 vColor;
    void main() {
      vec2 q  = gl_PointCoord - vec2(0.5);
      float r2 = dot(q, q);
      float a = exp(-r2 * 14.0) - 0.0302;   // soft gaussian sprite
      if (a <= 0.0) discard;
      gl_FragColor = vec4(vColor, a);
    }`,
  blending: THREE.AdditiveBlending,
  transparent: true,
  depthTest: true,
  depthWrite: false
});

/* --------------------------- galaxy points ----------------------- */
const geo = new THREE.BufferGeometry();
geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
geo.setAttribute('aColor',   new THREE.BufferAttribute(col, 3));
geo.setAttribute('aSize',    new THREE.BufferAttribute(siz, 1));
geo.boundingSphere = new THREE.Sphere(new THREE.Vector3(), 1e4);

const stars = new THREE.Points(geo, pointMat);
stars.frustumCulled = false;
scene.add(stars);

/* ------------------------- dark starfield ------------------------ */
const BG = 5200;
const bgPos = new Float32Array(BG * 3);
const bgCol = new Float32Array(BG * 3);
const bgSiz = new Float32Array(BG);

for (let i = 0; i < BG; i++) {
  const u  = Math.random() * 2 - 1;
  const ph = Math.random() * Math.PI * 2;
  const s  = Math.sqrt(1 - u * u);
  const R  = 520 + Math.random() * 500;
  bgPos[i * 3]     = R * s * Math.cos(ph);
  bgPos[i * 3 + 1] = R * u;
  bgPos[i * 3 + 2] = R * s * Math.sin(ph);

  const warm = Math.random();
  let r = 0.85, gg = 0.90, b = 1.0;
  if (warm < 0.14) { r = 1.0; gg = 0.82; b = 0.62; }
  else if (warm < 0.35) { r = 1.0; gg = 1.0; b = 1.0; }
  const br = 0.20 + 0.80 * Math.pow(Math.random(), 2.2);
  bgCol[i * 3]     = r * br;
  bgCol[i * 3 + 1] = gg * br;
  bgCol[i * 3 + 2] = b * br;

  bgSiz[i] = 1.6 + Math.random() * 3.4;
}

const bgGeo = new THREE.BufferGeometry();
bgGeo.setAttribute('position', new THREE.BufferAttribute(bgPos, 3));
bgGeo.setAttribute('aColor',   new THREE.BufferAttribute(bgCol, 3));
bgGeo.setAttribute('aSize',    new THREE.BufferAttribute(bgSiz, 1));
bgGeo.boundingSphere = new THREE.Sphere(new THREE.Vector3(), 1e5);

const bgStars = new THREE.Points(bgGeo, pointMat);
bgStars.frustumCulled = false;
scene.add(bgStars);

/* ---------------------- bright core glows ------------------------ */
function glowTexture() {
  const S = 128;
  const cv = document.createElement('canvas');
  cv.width = cv.height = S;
  const ctx = cv.getContext('2d');
  const grd = ctx.createRadialGradient(S / 2, S / 2, 0, S / 2, S / 2, S / 2);
  grd.addColorStop(0.00, 'rgba(255,246,222,1.00)');
  grd.addColorStop(0.12, 'rgba(255,224,158,0.70)');
  grd.addColorStop(0.35, 'rgba(255,186,96,0.20)');
  grd.addColorStop(0.70, 'rgba(255,150,70,0.045)');
  grd.addColorStop(1.00, 'rgba(255,130,60,0.00)');
  ctx.fillStyle = grd;
  ctx.fillRect(0, 0, S, S);
  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}
const glowTex = glowTexture();
const glowMat = new THREE.SpriteMaterial({
  map: glowTex, color: 0xffffff, transparent: true, opacity: 0.55,
  blending: THREE.AdditiveBlending, depthWrite: false, depthTest: true
});
const glowA = new THREE.Sprite(glowMat);
const glowB = new THREE.Sprite(glowMat);
glowA.scale.setScalar(0.62);
glowB.scale.setScalar(0.62);
scene.add(glowA, glowB);

/* ============================ physics ============================ */
function physicsStep(h) {
  /* ---- the two massive cores ---- */
  let dx = corePos[3] - corePos[0];
  let dy = corePos[4] - corePos[1];
  let dz = corePos[5] - corePos[2];
  let r2 = dx * dx + dy * dy + dz * dz + EPS2_CC;
  let inv = 1 / Math.sqrt(r2);
  let f = -GM * inv * inv * inv;
  const ax = f * dx, ay = f * dy, az = f * dz;

  coreVel[0] += ax * h; coreVel[1] += ay * h; coreVel[2] += az * h;
  coreVel[3] -= ax * h; coreVel[4] -= ay * h; coreVel[5] -= az * h;

  for (let k = 0; k < 6; k++) corePos[k] += coreVel[k] * h;

  const c0x = corePos[0], c0y = corePos[1], c0z = corePos[2];
  const c1x = corePos[3], c1y = corePos[4], c1z = corePos[5];

  /* ---- stars (semi-implicit / symplectic Euler) ---- */
  for (let g = 0; g < 2; g++) {
    const ox = g === 0 ? c0x : c1x;
    const oy = g === 0 ? c0y : c1y;
    const oz = g === 0 ? c0z : c1z;
    const ex = g === 0 ? c1x : c0x;
    const ey = g === 0 ? c1y : c0y;
    const ez = g === 0 ? c1z : c0z;

    const start = g * N_PER * 3;
    const end   = start + N_PER * 3;

    for (let p = start; p < end; p += 3) {
      const px = pos[p], py = pos[p + 1], pz = pos[p + 2];

      // own galaxy (Plummer, spherical -> no frame transform needed)
      let d1x = px - ox, d1y = py - oy, d1z = pz - oz;
      let s2 = d1x * d1x + d1y * d1y + d1z * d1z + EPS2_SELF;
      let iv = 1 / Math.sqrt(s2);
      let fa = -GM * iv * iv * iv;
      let axx = fa * d1x, ayy = fa * d1y, azz = fa * d1z;

      // companion core (the tidal perturber)
      let d2x = px - ex, d2y = py - ey, d2z = pz - ez;
      let e2 = d2x * d2x + d2y * d2y + d2z * d2z + EPS2_EXT;
      let ie = 1 / Math.sqrt(e2);
      let fe = -GM * ie * ie * ie;
      axx += fe * d2x; ayy += fe * d2y; azz += fe * d2z;

      const vx = vel[p]     + axx * h;
      const vy = vel[p + 1] + ayy * h;
      const vz = vel[p + 2] + azz * h;
      vel[p] = vx; vel[p + 1] = vy; vel[p + 2] = vz;

      pos[p]     = px + vx * h;
      pos[p + 1] = py + vy * h;
      pos[p + 2] = pz + vz * h;
    }
  }
}

/* ============================ camera ============================= */
const CAM_AZ0 = 0.62;
function updateCamera(elapsed) {
  const az  = CAM_AZ0 + 0.077 * elapsed;                        // slow orbit
  const inc = 0.62 + 0.13 * Math.sin(elapsed * 0.11);           // gentle inclination drift
  const dist = 15.5 + 6.5 * Math.min(1, elapsed / 28);          // pull back as tails grow
  const ch = Math.cos(inc), sh = Math.sin(inc);
  camera.position.set(dist * ch * Math.cos(az), dist * sh, dist * ch * Math.sin(az));
  camera.lookAt(0, 0, 0);
}

/* ============================= loop ============================== */
const hud = document.getElementById('hud');

let t0 = null;
let prevT = null;
let acc = 0;
let simTime = 0;
let shownMyr = -1;

function frame(now) {
  requestAnimationFrame(frame);

  if (t0 === null) { t0 = now; prevT = now; }
  const elapsed = (now - t0) * 0.001;          // real seconds since start
  let dt = (now - prevT) * 0.001;
  prevT = now;
  if (!(dt > 0)) dt = 0;
  if (dt > 0.1) dt = 0.1;                      // avoid a huge catch-up burst

  /* fixed-step integration */
  acc += dt * SIM_SPEED;
  let steps = 0;
  while (acc >= H_STEP && steps < MAX_SUB) {
    physicsStep(H_STEP);
    acc -= H_STEP;
    simTime += H_STEP;
    steps++;
  }
  if (steps === MAX_SUB) acc = 0;

  /* move the bright cores */
  glowA.position.set(corePos[0], corePos[1], corePos[2]);
  glowB.position.set(corePos[3], corePos[4], corePos[5]);

  /* push fresh positions to the GPU */
  geo.attributes.position.needsUpdate = true;

  updateCamera(elapsed);
  renderer.render(scene, camera);

  /* simulated clock */
  const myr = simTime * MYR_PER_UNIT;
  const r = Math.round(myr);
  if (r !== shownMyr) {
    shownMyr = r;
    hud.textContent = 'T + ' + String(r).padStart(3, '0') + ' Myr';
  }
}
requestAnimationFrame(frame);

/* =========================== resizing ============================ */
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);
  pointMat.uniforms.uPR.value = renderer.getPixelRatio();
});
</script>
</body>
</html>
```
### Galaxy Encounter Mechanics & Visuals

- **Cheap gravity model:** Each star feels the Plummer potential of its own galaxy's core and the point-mass potential of the companion core. The two massive cores are integrated as particles, producing realistic tidal tails and bridges without expensive N-body force calculations.
- **Animated camera:** A slowly orbiting camera drifts in inclination and pulls back over time, keeping both galaxies and their growing tails framed within the window.
- **Particle rendering:** The 44,000 stars are drawn as additive-blended point sprites, with color shifting from warm yellow cores to blue-white spiral arms using a custom shader.
- **Time display:** A small HUD label shows simulated time in millions of years, updated from the requestAnimationFrame timestamp.
---

**Optimization Tip:** To customize the encounter's pacing, adjust `SIM_SPEED` (simulation units per real second) or `MYR_PER_UNIT` (million years per unit). Lowering `SIM_SPEED` slows the motion for a more gradual collision, while increasing it speeds up the interaction.