```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Night City — Cinematic Flythrough</title>
<style>
  html, body { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; background: #05030c; }
  #app { position: fixed; inset: 0; }
  canvas { display: block; }
</style>
</head>
<body>
<div id="app"></div>

<script type="module">
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

/* ------------------------------------------------------------------ */
/*  Renderer / scene / camera                                         */
/* ------------------------------------------------------------------ */
const scene = new THREE.Scene();
const FOG_COLOR = new THREE.Color(0x0b0718);
const FOG_DENSITY = 0.0072;
scene.background = FOG_COLOR.clone();
scene.fog = new THREE.FogExp2(FOG_COLOR, FOG_DENSITY);

const camera = new THREE.PerspectiveCamera(62, innerWidth / innerHeight, 0.1, 2500);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.15;
document.getElementById('app').appendChild(renderer.domElement);

/* ------------------------------------------------------------------ */
/*  Procedural environment map (reflections on wet streets)           */
/* ------------------------------------------------------------------ */
function makeEnvTexture() {
  const c = document.createElement('canvas');
  c.width = 256; c.height = 128;
  const g = c.getContext('2d');
  const grad = g.createLinearGradient(0, 0, 0, 128);
  grad.addColorStop(0.00, '#020106');
  grad.addColorStop(0.55, '#0a0618');
  grad.addColorStop(0.72, '#3a1450');
  grad.addColorStop(0.78, '#7a2090');   // horizon glow
  grad.addColorStop(0.84, '#101a30');
  grad.addColorStop(1.00, '#020308');
  g.fillStyle = grad; g.fillRect(0, 0, 256, 128);
  // fake neon city blobs near the horizon
  const cols = ['rgba(255,40,180,0.5)', 'rgba(40,220,255,0.5)', 'rgba(160,60,255,0.5)'];
  for (let i = 0; i < 90; i++) {
    g.fillStyle = cols[(Math.random() * 3) | 0];
    const x = Math.random() * 256;
    const y = 92 + Math.random() * 12;
    g.fillRect(x, y, 1 + Math.random() * 2, 1 + Math.random() * 4);
  }
  const tex = new THREE.CanvasTexture(c);
  tex.mapping = THREE.EquirectangularReflectionMapping;
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}
scene.environment = makeEnvTexture();

/* ------------------------------------------------------------------ */
/*  Ground — wet reflective street                                    */
/* ------------------------------------------------------------------ */
function makeRoadTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 256;
  const g = c.getContext('2d');
  g.fillStyle = '#05060d'; g.fillRect(0, 0, 256, 256);
  g.strokeStyle = 'rgba(0,190,255,0.30)'; g.lineWidth = 2;
  g.strokeRect(1, 1, 254, 254);
  g.strokeStyle = 'rgba(0,190,255,0.10)'; g.lineWidth = 1;
  for (let i = 1; i < 4; i++) {
    g.beginPath(); g.moveTo(i * 64, 0); g.lineTo(i * 64, 256);
    g.moveTo(0, i * 64); g.lineTo(256, i * 64); g.stroke();
  }
  g.strokeStyle = 'rgba(255,40,180,0.22)'; g.lineWidth = 2;
  g.beginPath(); g.moveTo(128, 0); g.lineTo(128, 256); g.stroke();
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(48, 48);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
const ground = new THREE.Mesh(
  new THREE.PlaneGeometry(3200, 3200),
  new THREE.MeshStandardMaterial({
    map: makeRoadTexture(),
    color: 0x111420,
    metalness: 0.95,
    roughness: 0.14,
    envMapIntensity: 1.4
  })
);
ground.rotation.x = -Math.PI / 2;
scene.add(ground);

/* ------------------------------------------------------------------ */
/*  Procedural skyscrapers (InstancedMesh + custom window shader)     */
/* ------------------------------------------------------------------ */
const buildingGeo = new THREE.BoxGeometry(1, 1, 1);
buildingGeo.translate(0, 0.5, 0);

const buildingMat = new THREE.ShaderMaterial({
  uniforms: {
    uTime:       { value: 0 },
    uFogColor:   { value: FOG_COLOR },
    uFogDensity: { value: FOG_DENSITY }
  },
  vertexShader: /* glsl */`
    varying vec2 vUv;
    varying vec3 vWorldPos;
    varying float vSeed;
    attribute float aSeed;
    void main() {
      vUv = uv;
      vSeed = aSeed;
      vec4 wp;
      #ifdef USE_INSTANCING
        wp = modelMatrix * instanceMatrix * vec4(position, 1.0);
      #else
        wp = modelMatrix * vec4(position, 1.0);
      #endif
      vWorldPos = wp.xyz;
      gl_Position = projectionMatrix * viewMatrix * wp;
    }`,
  fragmentShader: /* glsl */`
    uniform float uTime;
    uniform vec3  uFogColor;
    uniform float uFogDensity;
    varying vec2 vUv;
    varying vec3 vWorldPos;
    varying float vSeed;

    float hash(vec2 p) {
      p = fract(p * vec2(123.34, 345.45));
      p += dot(p, p + 3.5);
      return fract(p.x * p.y);
    }
    vec3 palette(float h) {
      if (h < 0.34) return vec3(1.00, 0.12, 0.72);   // pink
      if (h < 0.67) return vec3(0.10, 0.85, 1.00);   // cyan
      return vec3(0.62, 0.22, 1.00);                 // purple
    }
    void main() {
      float r = vSeed - floor(vSeed);
      vec3 body = vec3(0.010, 0.012, 0.028) + 0.012 * r;

      // ---- window grid ----
      vec2 grid = vec2(9.0, 26.0);
      vec2 f = vUv * grid;
      vec2 cell = floor(f);
      vec2 fr = fract(f);
      float h = hash(cell + vSeed);
      float inW = step(0.20, fr.x) * step(fr.x, 0.80)
                * step(0.18, fr.y) * step(fr.y, 0.82);
      float flicker = 0.80 + 0.20 * sin(uTime * 2.0 + h * 40.0 + vSeed * 40.0);
      vec3 wc = mix(palette(hash(cell * 1.7 + vSeed)), vec3(0.30, 0.45, 0.70), step(0.82, hash(cell + 9.1)));
      float lit = step(0.50, h) * inW;
      vec3 win = wc * lit * flicker * 1.7;

      // edge fade so roofs / bases stay dark
      float fade = smoothstep(0.0, 0.05, vUv.y) * smoothstep(1.0, 0.95, vUv.y);
      win *= fade;

      // ---- occasional vertical neon accent strip ----
      float stripX = 0.15 + 0.7 * fract(vSeed * 3.71);
      float strip = (1.0 - smoothstep(0.0, 0.012, abs(vUv.x - stripX))) * step(0.70, r);
      vec3 sCol = palette(r) * strip * 1.8 * (0.8 + 0.2 * sin(uTime * 1.3 + vSeed * 20.0));

      vec3 col = body + win + sCol;

      // ---- manual exp2 fog ----
      float d = length(vWorldPos - cameraPosition);
      float fogF = 1.0 - exp(-uFogDensity * uFogDensity * d * d);
      col = mix(col, uFogColor, fogF);

      gl_FragColor = vec4(col, 1.0);
    }`
});

const SPACING = 46;
const HALF = 8;
const bPositions = [];
{
  const pos = new THREE.Vector3();
  for (let gx = -HALF; gx <= HALF; gx++) {
    for (let gz = -HALF; gz <= HALF; gz++) {
      if (Math.random() < 0.16) continue;                 // empty lots
      const x = (gx + 0.5 + (Math.random() - 0.5) * 0.5) * SPACING;
      const z = (gz + 0.5 + (Math.random() - 0.5) * 0.5) * SPACING;
      const dist = Math.sqrt(x * x + z * z);
      const h = (22 + Math.random() * 60) * (1 + 1.4 * Math.exp(-dist * dist / 90000));
      pos.set(x, 0, z);
      bPositions.push({ pos, h });
    }
  }
}
const COUNT = bPositions.length;
const seeds = new Float32Array(COUNT);
const dummy = new THREE.Object3D();
const buildings = new THREE.InstancedMesh(buildingGeo, buildingMat, COUNT);
for (let i = 0; i < COUNT; i++) {
  const b = bPositions[i];
  const sx = 9 + Math.random() * 13;
  const sz = 9 + Math.random() * 13;
  dummy.position.copy(b.pos);
  dummy.scale.set(sx, b.h, sz);
  dummy.updateMatrix();
  buildings.setMatrixAt(i, dummy.matrix);
  seeds[i] = Math.random() * 100;
}
buildingGeo.setAttribute('aSeed', new THREE.InstancedBufferAttribute(seeds, 1));
scene.add(buildings);

/* ------------------------------------------------------------------ */
/*  Neon signs + glowing rooftop edges                                */
/* ------------------------------------------------------------------ */
const NEON = [0xff2cb4, 0x2ce6ff, 0xa03dff];
function makeSignTexture() {
  const c = document.createElement('canvas');
  c.width = 64; c.height = 96;
  const g = c.getContext('2d');
  g.clearRect(0, 0, 64, 96);
  const col = '#' + NEON[(Math.random() * 3) | 0].toString(16).padStart(6, '0');
  g.strokeStyle = col; g.fillStyle = col;
  g.lineWidth = 4 + Math.random() * 4;
  g.shadowColor = col; g.shadowBlur = 6;
  const n = 3 + ((Math.random() * 4) | 0);
  for (let i = 0; i < n; i++) {
    const kind = Math.random();
    const x = 8 + Math.random() * 48, y = 8 + Math.random() * 80;
    if (kind < 0.4) { g.fillRect(x, y, 3 + Math.random() * 5, 14 + Math.random() * 30); }
    else if (kind < 0.7) { g.fillRect(x, y, 12 + Math.random() * 30, 3 + Math.random() * 5); }
    else { g.beginPath(); g.arc(x, y, 5 + Math.random() * 8, 0, Math.PI * 2); g.stroke(); }
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
for (let i = 0; i < 46; i++) {
  const b = bPositions[(Math.random() * COUNT) | 0];
  const sign = new THREE.Mesh(
    new THREE.PlaneGeometry(6 + Math.random() * 5, 9 + Math.random() * 8),
    new THREE.MeshBasicMaterial({ map: makeSignTexture(), transparent: true, side: THREE.DoubleSide, toneMapped: false })
  );
  const face = (Math.random() * 4) | 0;
  const y = b.h * (0.5 + Math.random() * 0.4);
  const off = 14;
  if (face === 0) { sign.position.set(b.pos.x + off, y, b.pos.z); sign.rotation.y = Math.PI / 2; }
  else if (face === 1) { sign.position.set(b.pos.x - off, y, b.pos.z); sign.rotation.y = -Math.PI / 2; }
  else if (face === 2) { sign.position.set(b.pos.x, y, b.pos.z + off); }
  else { sign.position.set(b.pos.x, y, b.pos.z - off); }
  scene.add(sign);
}
// glowing rooftop trim
{
  const trimGeo = new THREE.BoxGeometry(1, 0.9, 1);
  const used = COUNT * 0.3 | 0;
  const trim = new THREE.InstancedMesh(trimGeo, new THREE.MeshBasicMaterial({ toneMapped: false }), used);
  for (let i = 0; i < used; i++) {
    const b = bPositions[(Math.random() * COUNT) | 0];
    dummy.position.set(b.pos.x, b.h + 0.45, b.pos.z);
    dummy.scale.set(11 + Math.random() * 12, 1, 11 + Math.random() * 12);
    dummy.rotation.set(0, 0, 0);
    dummy.updateMatrix();
    trim.setMatrixAt(i, dummy.matrix);
    trim.setColorAt(i, new THREE.Color(NEON[(Math.random() * 3) | 0]).multiplyScalar(1.6));
  }
  scene.add(trim);
}

/* ------------------------------------------------------------------ */
/*  Haze sprites — cheap "volumetric" fog                             */
/* ------------------------------------------------------------------ */
function makeRadialTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 256;
  const g = c.getContext('2d');
  const grad = g.createRadialGradient(128, 128, 0, 128, 128, 128);
  grad.addColorStop(0.0, 'rgba(255,255,255,1)');
  grad.addColorStop(0.4, 'rgba(255,255,255,0.35)');
  grad.addColorStop(1.0, 'rgba(255,255,255,0)');
  g.fillStyle = grad; g.fillRect(0, 0, 256, 256);
  return new THREE.CanvasTexture(c);
}
const hazeTex = makeRadialTexture();
const haze = [];
for (let i = 0; i < 12; i++) {
  const m = new THREE.SpriteMaterial({
    map: hazeTex,
    color: new THREE.Color().setHSL(0.72 + Math.random() * 0.1, 0.6, 0.35),
    transparent: true, opacity: 0.05 + Math.random() * 0.04,
    blending: THREE.AdditiveBlending, depthWrite: false, fog: false
  });
  const s = new THREE.Sprite(m);
  s.scale.set(380 + Math.random() * 320, 140 + Math.random() * 160, 1);
  s.userData = {
    bx: (Math.random() - 0.5) * 900,
    y: 30 + Math.random() * 130,
    bz: (Math.random() - 0.5) * 900,
    sp: 0.01 + Math.random() * 0.02,
    ph: Math.random() * Math.PI * 2
  };
  haze.push(s); scene.add(s);
}

/* ------------------------------------------------------------------ */
/*  Flying cars on looping spline paths                               */
/* ------------------------------------------------------------------ */
const cars = [];
function makeCar(color) {
  const grp = new THREE.Group();
  const body = new THREE.Mesh(
    new THREE.BoxGeometry(1.1, 0.5, 2.6),
    new THREE.MeshBasicMaterial({ color: 0x0c0e18 })
  );
  const nose = new THREE.Mesh(
    new THREE.BoxGeometry(0.7, 0.22, 0.2),
    new THREE.MeshBasicMaterial({ color: 0xffffff, toneMapped: false })
  );
  nose.position.set(0, 0.05, 1.35);
  const trail = new THREE.Mesh(
    new THREE.BoxGeometry(0.45, 0.28, 4.5),
    new THREE.MeshBasicMaterial({ color, toneMapped: false })
  );
  trail.position.set(0, 0.02, -3.2);
  grp.add(body, nose, trail);
  return grp;
}
for (let i = 0; i < 10; i++) {
  const pts = [];
  const baseH = 35 + Math.random() * 110;
  for (let k = 0; k < 8; k++) {
    const a = (k / 8) * Math.PI * 2 + Math.random() * 0.5;
    const rad = 90 + Math.random() * 330;
    pts.push(new THREE.Vector3(Math.cos(a) * rad, baseH + (Math.random() - 0.5) * 24, Math.sin(a) * rad));
  }
  const path = new THREE.CatmullRomCurve3(pts, true);
  const color = NEON[(Math.random() * 3) | 0];
  cars.push({
    group: makeCar(new THREE.Color(color).multiplyScalar(2.2)),
    path,
    off: Math.random(),
    speed: 0.004 + Math.random() * 0.006
  });
  scene.add(cars[i].group);
}

/* ------------------------------------------------------------------ */
/*  Camera flythrough path                                            */
/* ------------------------------------------------------------------ */
const camPts = [];
for (let i = 0; i < 10; i++) {
  const a = (i / 10) * Math.PI * 2;
  const rad = 190 + Math.sin(i * 2.7) * 130 + Math.cos(i * 1.3) * 60;
  camPts.push(new THREE.Vector3(Math.cos(a) * rad, 26 + (i * 53) % 62, Math.sin(a) * rad));
}
const camCurve = new THREE.CatmullRomCurve3(camPts, true);

/* ------------------------------------------------------------------ */
/*  Post-processing: bloom                                            */
/* ------------------------------------------------------------------ */
const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(innerWidth, innerHeight), 1.35, 0.75, 0.32);
composer.addPass(bloom);
composer.addPass(new OutputPass());

/* ------------------------------------------------------------------ */
/*  Resize                                                            */
/* ------------------------------------------------------------------ */
addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
  composer.setSize(innerWidth, innerHeight);
});

/* ------------------------------------------------------------------ */
/*  Animation loop (uses rAF timestamp)                               */
/* ------------------------------------------------------------------ */
const _pos = new THREE.Vector3();
const _look = new THREE.Vector3();
const _tan = new THREE.Vector3();

function animate(time) {
  requestAnimationFrame(animate);
  const t = time * 0.001;
  buildingMat.uniforms.uTime.value = t;

  // --- camera glides along its loop ---
  const ct = (time * 0.00002) % 1;                       // ~50 s full loop
  camCurve.getPointAt(ct, _pos);
  camCurve.getPointAt((ct + 0.035) % 1, _look);
  _pos.y += Math.sin(t * 0.37) * 1.6;
  _look.y += Math.sin(t * 0.5 + 1.3) * 2.2;
  camera.position.copy(_pos);
  camera.lookAt(_look);

  // --- cars ---
  for (const c of cars) {
    const u = (c.off + time * c.speed * 0.001) % 1;
    c.path.getPointAt(u, _pos);
    c.path.getTangentAt(u, _tan);
    c.group.position.copy(_pos);
    c.group.lookAt(_tan.x + _pos.x, _tan.y + _pos.y, _tan.z + _pos.z);
  }

  // --- drifting haze ---
  for (const s of haze) {
    const d = s.userData;
    s.position.set(d.bx + Math.sin(t * d.sp * 60 + d.ph) * 40, d.y, d.bz + Math.cos(t * d.sp * 40 + d.ph) * 40);
  }

  composer.render();
}
requestAnimationFrame(animate);
</script>
</body>
</html>
```