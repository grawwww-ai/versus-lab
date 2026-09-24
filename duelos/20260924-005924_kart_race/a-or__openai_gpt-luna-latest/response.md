```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rainbow Ridge Grand Prix</title>
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; width: 100%; height: 100%; overflow: hidden; background: #8fd7ef; font-family: Arial, Helvetica, sans-serif; }
  canvas { display: block; }
  #hud { position: fixed; inset: 0; pointer-events: none; color: white; text-shadow: 0 2px 4px #172b3bcc; }
  .panel { background: linear-gradient(145deg, #142947dc, #10203bd9); border: 2px solid #ffffffa6; border-radius: 13px; box-shadow: 0 5px 18px #12243b55; }
  #brand { position: absolute; left: 22px; top: 20px; padding: 12px 17px; }
  #brand b { display: block; font-size: 18px; letter-spacing: 1.7px; }
  #brand small { color: #aeeaff; font-weight: bold; letter-spacing: 2px; }
  #leaderboard { position: absolute; right: 22px; top: 20px; width: 224px; padding: 12px; }
  #leaderboard h2 { margin: 0 0 8px; font-size: 13px; letter-spacing: 2px; color: #9de9ff; }
  .row { display: flex; align-items: center; gap: 9px; padding: 5px 4px; border-top: 1px solid #ffffff24; font-weight: bold; font-size: 14px; }
  .row:first-of-type { border-top: 0; }
  .rank { width: 23px; color: #ffdc59; }
  .swatch { width: 12px; height: 12px; border: 1px solid #ffffffbd; border-radius: 3px; }
  .name { flex: 1; }
  .gap { color: #b8c8dc; font-size: 11px; }
  #raceinfo { position: absolute; left: 50%; bottom: 22px; transform: translateX(-50%); padding: 10px 21px; min-width: 215px; text-align: center; }
  #raceinfo strong { font-size: 20px; letter-spacing: 1px; }
  #raceinfo span { display: block; margin-top: 3px; color: #bceeff; font-size: 12px; font-weight: bold; letter-spacing: 2px; }
  #camera-label { position: absolute; left: 22px; bottom: 23px; padding: 8px 12px; color: #eafaff; font-size: 11px; letter-spacing: 1.5px; }
  #countdown { position: absolute; left: 50%; top: 43%; transform: translate(-50%, -50%); font-weight: 1000; font-size: clamp(72px, 14vw, 160px); color: #ffe64b; -webkit-text-stroke: 3px #c83e22; text-shadow: 0 7px 0 #812719, 0 12px 25px #14233e99; }
  #countdown.go { font-size: clamp(58px, 11vw, 118px); color: #8eff8d; -webkit-text-stroke-color: #168d59; }
  #hint { position: absolute; left: 50%; top: 20px; transform: translateX(-50%); color: #fff; font-size: 11px; letter-spacing: 2px; opacity: .8; }
</style>
</head>
<body>
<div id="hud">
  <div id="brand" class="panel"><b>RAINBOW RIDGE</b><small>GRAND PRIX</small></div>
  <div id="hint">AUTOPILOT GRAND PRIX · 6 RACERS</div>
  <div id="leaderboard" class="panel"><h2>RACE POSITIONS</h2><div id="rows"></div></div>
  <div id="camera-label" class="panel">CHASE CAM</div>
  <div id="raceinfo" class="panel"><strong id="lap">LAP 1 / 2</strong><span id="status">GRID READY</span></div>
  <div id="countdown">3</div>
</div>
<script type="module">
import * as THREE from 'three';

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x8bd8f2);
scene.fog = new THREE.Fog(0x9bdcf0, 170, 430);

const camera = new THREE.PerspectiveCamera(62, innerWidth / innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.7));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.12;
document.body.appendChild(renderer.domElement);

scene.add(new THREE.HemisphereLight(0xdaf5ff, 0x536b38, 2.0));
const sun = new THREE.DirectionalLight(0xfff1d1, 3.0);
sun.position.set(-100, 150, -55);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.camera.left = -180; sun.shadow.camera.right = 180;
sun.shadow.camera.top = 180; sun.shadow.camera.bottom = -180;
sun.shadow.camera.far = 420;
sun.shadow.bias = -0.00025;
scene.add(sun);

const ground = new THREE.Mesh(new THREE.PlaneGeometry(1800, 1800), new THREE.MeshStandardMaterial({ color: 0x65a94c, roughness: 1 }));
ground.rotation.x = -Math.PI / 2;
ground.position.y = -5;
ground.receiveShadow = true;
scene.add(ground);

const points = [
  [-62, 0, -43], [-28, 2, -70], [18, 5, -72], [57, 2, -48],
  [67, 4, -12], [48, 1, 17], [70, 7, 48], [39, 3, 70],
  [1, 1, 62], [-34, 7, 72], [-70, 2, 48], [-68, 5, 12],
  [-48, 1, -10], [-76, 4, -29]
].map(p => new THREE.Vector3(...p));
const curve = new THREE.CatmullRomCurve3(points, true, 'catmullrom', 0.45);
const trackLength = curve.getLength();
const ROAD_HALF = 9.1;
const UP = new THREE.Vector3(0, 1, 0);

function frameAt(u) {
  u = ((u % 1) + 1) % 1;
  const point = curve.getPointAt(u);
  const tangent = curve.getTangentAt(u).normalize();
  const right = new THREE.Vector3().crossVectors(UP, tangent).normalize();
  return { point, tangent, right };
}
function pointAtOffset(u, side, height = 0) {
  const f = frameAt(u);
  return f.point.clone().addScaledVector(f.right, side).add(new THREE.Vector3(0, height, 0));
}
function ribbonGeometry(inner, outer, steps = 600, lift = 0.12) {
  const positions = [], indices = [];
  for (let i = 0; i <= steps; i++) {
    const u = i / steps, f = frameAt(u);
    for (const side of [inner, outer]) {
      const p = f.point.clone().addScaledVector(f.right, side);
      p.y += lift;
      positions.push(p.x, p.y, p.z);
    }
  }
  for (let i = 0; i < steps; i++) {
    const a = i * 2, b = a + 1, c = a + 2, d = a + 3;
    indices.push(a, b, c, b, d, c);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  g.setIndex(indices);
  g.computeVertexNormals();
  return g;
}

const road = new THREE.Mesh(ribbonGeometry(-ROAD_HALF, ROAD_HALF), new THREE.MeshStandardMaterial({ color: 0x33383e, roughness: 0.94, side: THREE.DoubleSide }));
road.receiveShadow = true;
scene.add(road);

for (const side of [-1, 1]) {
  const shoulder = new THREE.Mesh(ribbonGeometry(side * 9.05, side * 10.2, 600, 0.08), new THREE.MeshStandardMaterial({ color: 0xbbb8a8, roughness: 1, side: THREE.DoubleSide }));
  shoulder.receiveShadow = true; scene.add(shoulder);

  const kerbPositions = [], kerbColors = [], kerbIndices = [];
  const segments = 280;
  for (let i = 0; i < segments; i++) {
    const u0 = i / segments, u1 = (i + 1) / segments;
    const a = pointAtOffset(u0, side * 7.85, 0.22);
    const b = pointAtOffset(u0, side * 9.2, 0.22);
    const c = pointAtOffset(u1, side * 7.85, 0.22);
    const d = pointAtOffset(u1, side * 9.2, 0.22);
    const base = kerbPositions.length / 3;
    for (const p of [a, b, c, d]) {
      kerbPositions.push(p.x, p.y, p.z);
      const col = (Math.floor(i / 3) % 2 === 0) ? new THREE.Color(0xe94436) : new THREE.Color(0xf4eee0);
      kerbColors.push(col.r, col.g, col.b);
    }
    kerbIndices.push(base, base + 1, base + 2, base + 1, base + 3, base + 2);
  }
  const kg = new THREE.BufferGeometry();
  kg.setAttribute('position', new THREE.Float32BufferAttribute(kerbPositions, 3));
  kg.setAttribute('color', new THREE.Float32BufferAttribute(kerbColors, 3));
  kg.setIndex(kerbIndices); kg.computeVertexNormals();
  const km = new THREE.Mesh(kg, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.85, side: THREE.DoubleSide }));
  km.receiveShadow = true; scene.add(km);

  const line = new THREE.Mesh(ribbonGeometry(side * 7.55, side * 7.72, 500, 0.23), new THREE.MeshStandardMaterial({ color: 0xf2f1e8, side: THREE.DoubleSide }));
  scene.add(line);
}

// Starting grid checkerboard, laid across the road.
{
  const group = new THREE.Group();
  const f = frameAt(0.004);
  const cols = 14, rows = 2;
  const tileW = ROAD_HALF * 2 / cols, tileL = 0.9;
  const mats = [
    new THREE.MeshStandardMaterial({ color: 0xf6f4e9, roughness: 1, side: THREE.DoubleSide }),
    new THREE.MeshStandardMaterial({ color: 0x20242a, roughness: 1, side: THREE.DoubleSide })
  ];
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const side0 = -ROAD_HALF + c * tileW, side1 = side0 + tileW;
    const u = 0.004 + (r - 0.5) * tileL / trackLength;
    const p1 = pointAtOffset(u, side0, 0.25), p2 = pointAtOffset(u, side1, 0.25);
    const p3 = pointAtOffset(u + tileL / trackLength, side0, 0.25), p4 = pointAtOffset(u + tileL / trackLength, side1, 0.25);
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute([
      p1.x,p1.y,p1.z, p2.x,p2.y,p2.z, p3.x,p3.y,p3.z, p4.x,p4.y,p4.z
    ], 3));
    geo.setIndex([0,1,2,1,3,2]); geo.computeVertexNormals();
    const tile = new THREE.Mesh(geo, mats[(c + r) % 2]); group.add(tile);
  }
  scene.add(group);
}

// Start/finish gantry.
{
  const f = frameAt(0.005);
  const mat = new THREE.MeshStandardMaterial({ color: 0xeff5f8, roughness: 0.5 });
  for (const side of [-1, 1]) {
    const p = f.point.clone().addScaledVector(f.right, side * 11.5);
    const post = new THREE.Mesh(new THREE.BoxGeometry(0.65, 8, 0.65), mat);
    post.position.set(p.x, p.y + 4, p.z); post.castShadow = true; scene.add(post);
  }
  const beam = new THREE.Mesh(new THREE.BoxGeometry(24, 1.1, 0.8), new THREE.MeshStandardMaterial({ color: 0x19a9ce, roughness: 0.4 }));
  beam.position.set(f.point.x, f.point.y + 8, f.point.z); beam.castShadow = true; scene.add(beam);
  const banner = new THREE.Mesh(new THREE.BoxGeometry(10.5, 1.1, 0.18), new THREE.MeshStandardMaterial({ color: 0xf6d23f, roughness: 0.6 }));
  banner.position.set(f.point.x, f.point.y + 8, f.point.z + 0.48); scene.add(banner);
}

// A little roadside color and handmade trackside advertising.
function makeSignTexture(text, color) {
  const c = document.createElement('canvas'); c.width = 512; c.height = 160;
  const x = c.getContext('2d');
  x.fillStyle = color; x.fillRect(0, 0, c.width, c.height);
  x.strokeStyle = '#fff3c4'; x.lineWidth = 12; x.strokeRect(8, 8, 496, 144);
  x.fillStyle = '#ffffff'; x.font = '900 62px Arial'; x.textAlign = 'center'; x.textBaseline = 'middle';
  x.fillText(text, 256, 82);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
const signTextures = [
  makeSignTexture('TURBO!', '#e84137'), makeSignTexture('MUSHROOM CUP', '#247dc5'),
  makeSignTexture('GO! GO! GO!', '#e88a19')
];
for (let i = 0; i < 9; i++) {
  const u = (i * 0.117 + 0.045) % 1, side = (i % 2 ? 1 : -1);
  const f = frameAt(u), pos = f.point.clone().addScaledVector(f.right, side * 15);
  const board = new THREE.Mesh(new THREE.BoxGeometry(8, 2.5, 0.35), new THREE.MeshStandardMaterial({ map: signTextures[i % 3], roughness: 0.7 }));
  board.position.set(pos.x, pos.y + 3.3, pos.z);
  board.rotation.y = Math.atan2(f.tangent.x, f.tangent.z);
  board.castShadow = true; scene.add(board);
  const legsMat = new THREE.MeshStandardMaterial({ color: 0xeeeeea });
  for (const dx of [-3.2, 3.2]) {
    const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.13, 0.17, 2.2, 8), legsMat);
    leg.position.copy(pos).add(new THREE.Vector3(0, 1, 0)).addScaledVector(f.right, dx);
    leg.castShadow = true; scene.add(leg);
  }
}

// Trees, pines, and candy-colored scenery.
let seed = 75842;
function rand() { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; }
const trunkMat = new THREE.MeshStandardMaterial({ color: 0x704a2a, roughness: 1 });
const leafMats = [0x237844, 0x2d9149, 0x4da64a, 0x176e4c].map(c => new THREE.MeshStandardMaterial({ color: c, roughness: 1 }));
const trunkGeo = new THREE.CylinderGeometry(0.27, 0.42, 2.5, 7);
const crownGeo = new THREE.ConeGeometry(2.25, 4.5, 7);
const crownGeo2 = new THREE.ConeGeometry(1.65, 3.7, 7);
for (let i = 0; i < 112; i++) {
  const u = rand(), side = rand() < 0.5 ? -1 : 1;
  const dist = 19 + rand() * 42;
  const p = pointAtOffset(u, side * dist, 0);
  const scale = 0.72 + rand() * 0.85;
  const tree = new THREE.Group();
  const trunk = new THREE.Mesh(trunkGeo, trunkMat); trunk.position.y = 1.2; trunk.castShadow = true; tree.add(trunk);
  const crown = new THREE.Mesh(crownGeo, leafMats[Math.floor(rand() * leafMats.length)]);
  crown.position.y = 4.0; crown.castShadow = true; tree.add(crown);
  const crown2 = new THREE.Mesh(crownGeo2, leafMats[Math.floor(rand() * leafMats.length)]);
  crown2.position.y = 5.8; crown2.castShadow = true; tree.add(crown2);
  tree.position.set(p.x, p.y, p.z); tree.scale.setScalar(scale); scene.add(tree);
}
const rockMat = new THREE.MeshStandardMaterial({ color: 0xb4aa8c, roughness: 1 });
for (let i = 0; i < 34; i++) {
  const u = rand(), side = rand() < .5 ? -1 : 1;
  const p = pointAtOffset(u, side * (13 + rand() * 9), 0);
  const rock = new THREE.Mesh(new THREE.DodecahedronGeometry(0.8 + rand() * 1.2, 0), rockMat);
  rock.position.set(p.x, p.y + 0.5, p.z); rock.scale.y = 0.65; rock.castShadow = true; scene.add(rock);
}

// Distant soft clouds.
const cloudMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 1 });
for (let i = 0; i < 16; i++) {
  const cloud = new THREE.Group();
  const x = (rand() - .5) * 440, y = 65 + rand() * 55, z = (rand() - .5) * 400;
  for (let j = 0; j < 5; j++) {
    const puff = new THREE.Mesh(new THREE.SphereGeometry(4 + rand() * 3, 10, 8), cloudMat);
    puff.position.set((j - 2) * 4.3, rand() * 2.2, rand() * 2);
    puff.scale.y = 0.58; cloud.add(puff);
  }
  cloud.position.set(x, y, z); scene.add(cloud);
}

// Karts and drivers.
const racers = [
  { name: 'PEACH', color: 0xff54a3, helmet: 0xff83bb },
  { name: 'MARIO', color: 0xe84135, helmet: 0xe9362c },
  { name: 'LUIGI', color: 0x48c95b, helmet: 0x39b84d },
  { name: 'YOSHI', color: 0x36c6d4, helmet: 0x32c8d5 },
  { name: 'BOWSER', color: 0xeba82e, helmet: 0xe79c23 },
  { name: 'TOAD', color: 0x9c68eb, helmet: 0x8e57e4 }
];
const kartMaterials = racers.map(r => new THREE.MeshStandardMaterial({ color: r.color, roughness: 0.42, metalness: 0.08 }));
const tireMat = new THREE.MeshStandardMaterial({ color: 0x17191c, roughness: 0.94 });
const hubMat = new THREE.MeshStandardMaterial({ color: 0xc9d2d7, metalness: 0.55, roughness: 0.32 });
const darkMat = new THREE.MeshStandardMaterial({ color: 0x252a31, roughness: 0.65 });
const racersData = [];

function buildKart(index) {
  const cfg = racers[index], root = new THREE.Group();
  const body = new THREE.Mesh(new THREE.BoxGeometry(1.9, 0.58, 3.15), kartMaterials[index]);
  body.position.y = 0.72; body.castShadow = true; root.add(body);
  const nose = new THREE.Mesh(new THREE.BoxGeometry(1.55, 0.34, 0.85), kartMaterials[index]);
  nose.position.set(0, 0.88, 1.5); nose.castShadow = true; root.add(nose);
  const bumper = new THREE.Mesh(new THREE.BoxGeometry(2.0, 0.18, 0.28), hubMat);
  bumper.position.set(0, 0.53, 1.92); root.add(bumper);
  const seat = new THREE.Mesh(new THREE.BoxGeometry(0.92, 0.72, 0.75), darkMat);
  seat.position.set(0, 1.1, -0.12); root.add(seat);

  // Simple seated driver, helmet, and visor.
  const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.37, 0.49, 0.83, 9), kartMaterials[index]);
  torso.position.set(0, 1.48, 0.02); torso.rotation.x = -0.16; torso.castShadow = true; root.add(torso);
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.48, 14, 11), new THREE.MeshStandardMaterial({ color: cfg.helmet, roughness: 0.36 }));
  head.position.set(0, 2.05, 0.24); head.castShadow = true; root.add(head);
  const visor = new THREE.Mesh(new THREE.BoxGeometry(0.62, 0.19, 0.12), new THREE.MeshStandardMaterial({ color: 0x25394b, metalness: 0.3, roughness: 0.25 }));
  visor.position.set(0, 2.08, 0.67); root.add(visor);
  const wheel = new THREE.Mesh(new THREE.TorusGeometry(0.38, 0.065, 7, 16), darkMat);
  wheel.position.set(0, 1.22, 0.76); wheel.rotation.x = Math.PI / 2.3; root.add(wheel);
  for (const x of [-0.82, 0.82]) {
    const arm = new THREE.Mesh(new THREE.CylinderGeometry(0.095, 0.095, 0.8, 7), kartMaterials[index]);
    arm.position.set(x * 0.52, 1.43, 0.3); arm.rotation.z = x < 0 ? -0.5 : 0.5; root.add(arm);
  }

  const wheels = [];
  for (const x of [-1.08, 1.08]) for (const z of [-1.02, 1.12]) {
    const pivot = new THREE.Group(); pivot.position.set(x, 0.48, z); root.add(pivot);
    const tire = new THREE.Mesh(new THREE.CylinderGeometry(0.48, 0.48, 0.38, 14), tireMat);
    tire.rotation.z = Math.PI / 2; tire.castShadow = true; pivot.add(tire);
    const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.23, 0.23, 0.405, 12), hubMat);
    hub.rotation.z = Math.PI / 2; pivot.add(hub);
    wheels.push({ pivot, tire, front: z > 0 });
  }
  const tail = new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.18, 0.17), new THREE.MeshStandardMaterial({ color: 0xff382c, emissive: 0x8b120a }));
  tail.position.set(0, 0.8, -1.67); root.add(tail);
  scene.add(root);
  return { root, wheels, drift: 0, lane: [-4.8, -2.5, 0.3, 2.8, 4.9, -0.2][index], startOffset: -index * 0.012 };
}
for (let i = 0; i < racers.length; i++) racersData.push({ ...racers[i], ...buildKart(i), progress: 0, speed: 0, laneNow: 0, particleTimer: 0 });

// Soft procedural dust puffs, recycled as a tiny sprite pool.
const dustCanvas = document.createElement('canvas'); dustCanvas.width = dustCanvas.height = 64;
const dctx = dustCanvas.getContext('2d');
const grad = dctx.createRadialGradient(32, 32, 2, 32, 32, 31);
grad.addColorStop(0, 'rgba(255,246,218,0.9)'); grad.addColorStop(0.38, 'rgba(224,216,194,0.55)'); grad.addColorStop(1, 'rgba(180,178,164,0)');
dctx.fillStyle = grad; dctx.fillRect(0, 0, 64, 64);
const dustTex = new THREE.CanvasTexture(dustCanvas);
const particles = [];
for (let i = 0; i < 90; i++) {
  const material = new THREE.SpriteMaterial({ map: dustTex, transparent: true, opacity: 0, depthWrite: false, color: i % 3 === 0 ? 0xe7d9b5 : 0xffffff });
  const sprite = new THREE.Sprite(material);
  sprite.visible = false; scene.add(sprite);
  particles.push({ sprite, velocity: new THREE.Vector3(), life: 0, maxLife: 1 });
}
let particleIndex = 0;
function emitDust(kart, tangent) {
  const p = particles[particleIndex++ % particles.length];
  const fwd = tangent;
  const side = new THREE.Vector3().crossVectors(UP, tangent).normalize();
  const sideSign = Math.random() < 0.5 ? -1 : 1;
  const pos = kart.root.position.clone().addScaledVector(fwd, -1.15).addScaledVector(side, sideSign * 0.85);
  pos.y += 0.35;
  p.sprite.position.copy(pos);
  p.sprite.scale.setScalar(1.2 + Math.random() * 0.8);
  p.sprite.material.opacity = 0.65;
  p.sprite.visible = true;
  p.life = p.maxLife = 0.55 + Math.random() * 0.5;
  p.velocity.set((Math.random() - .5) * 2.1, 1.2 + Math.random() * 1.3, (Math.random() - .5) * 2.1);
}

const rows = document.getElementById('rows');
const rowNodes = racersData.map((r, i) => {
  const el = document.createElement('div'); el.className = 'row';
  el.innerHTML = `<span class="rank">${i + 1}.</span><span class="swatch" style="background:#${r.color.toString(16).padStart(6,'0')}"></span><span class="name">${r.name}</span><span class="gap"></span>`;
  rows.appendChild(el); return el;
});
const countdownEl = document.getElementById('countdown');
const statusEl = document.getElementById('status');
const lapEl = document.getElementById('lap');
const cameraLabel = document.getElementById('camera-label');

const clock = new THREE.Clock();
let elapsed = 0;
let raceTime = 0;
let started = false;
let lastOrder = racersData.slice();
const chasePos = new THREE.Vector3();
const lookPos = new THREE.Vector3();
let cameraInitialized = false;
const tempVec = new THREE.Vector3();

function smoothstep(a, b, x) { const t = THREE.MathUtils.clamp((x-a)/(b-a), 0, 1); return t*t*(3-2*t); }

function animate() {
  requestAnimationFrame(animate);
  const dt = Math.min(clock.getDelta(), 0.045);
  elapsed += dt;

  if (!started) {
    const n = Math.ceil(3 - elapsed);
    if (elapsed < 3) {
      countdownEl.textContent = Math.max(1, n);
      statusEl.textContent = 'GRID READY';
    } else {
      started = true;
      raceTime = 0;
      countdownEl.textContent = 'GO!';
      countdownEl.classList.add('go');
      statusEl.textContent = 'RACE ON';
      setTimeout(() => { countdownEl.style.display = 'none'; }, 850);
    }
  }

  if (started) {
    raceTime += dt;
    for (let i = 0; i < racersData.length; i++) {
      const r = racersData[i];
      const phase = raceTime * 0.72 + i * 1.73;
      const physicalU = ((r.progress + r.startOffset) % 1 + 1) % 1;
      const ahead = racersData.some((other, j) => {
        if (j === i) return false;
        let gap = other.progress - r.progress;
        while (gap < 0) gap += 1;
        return gap > 0.002 && gap < 0.042;
      });
      const laneTarget = r.lane + Math.sin(phase * 0.63) * 0.85 + (ahead ? ((i % 2) ? -2.4 : 2.4) : 0);
      r.laneNow = THREE.MathUtils.damp(r.laneNow, laneTarget, 1.15, dt);
      const baseSpeed = 39 + 4.1 * Math.sin(phase) + 2.3 * Math.sin(phase * 0.47 + i);
      const catchup = Math.max(0, 0.13 - r.progress) * 11;
      r.speed = Math.max(29, baseSpeed + catchup + (ahead ? 1.8 : 0));
      r.progress += (r.speed / trackLength) * dt;

      const u = ((r.progress + r.startOffset) % 1 + 1) % 1;
      const f = frameAt(u);
      const target = f.point.clone().addScaledVector(f.right, r.laneNow);
      target.y += 0.55;
      r.root.position.lerp(target, 1 - Math.exp(-dt * 7));
      const heading = Math.atan2(f.tangent.x, f.tangent.z);
      const before = frameAt(u - 0.003).tangent, after = frameAt(u + 0.003).tangent;
      const turn = before.x * after.z - before.z * after.x;
      const corner = Math.abs(turn);
      const wantedDrift = THREE.MathUtils.clamp((corner - 0.025) * 14, 0, 1);
      r.drift = THREE.MathUtils.damp(r.drift, wantedDrift, 3.2, dt);
      r.root.rotation.y = heading + Math.sign(turn) * r.drift * 0.11;
      r.root.rotation.z = -Math.sign(turn) * r.drift * 0.035;
      for (const w of r.wheels) {
        if (w.front) w.pivot.rotation.y = Math.sin(phase) * 0.075 + Math.sign(turn) * r.drift * 0.14;
        w.tire.rotation.x += r.speed * dt * 0.8;
      }
      if (r.drift > 0.42) {
        r.particleTimer += dt;
        if (r.particleTimer > 0.055) { r.particleTimer = 0; emitDust(r, f.tangent); }
      } else r.particleTimer = 0;
    }

    lastOrder = racersData.slice().sort((a, b) => b.progress - a.progress);
    lastOrder.forEach((r, place) => {
      const original = racersData.indexOf(r);
      const rank = rowNodes[original].querySelector('.rank');
      rank.textContent = `${place + 1}.`;
      rowNodes[original].style.order = place;
      rowNodes[original].style.background = place === 0 ? '#ffdc5920' : '';
      const gapEl = rowNodes[original].querySelector('.gap');
      gapEl.textContent = place === 0 ? 'LEADER' : `+${Math.max(0, (lastOrder[0].progress - r.progress) * trackLength).toFixed(0)} m`;
    });

    const leader = lastOrder[0];
    const leaderLaps = Math.min(2, Math.floor(leader.progress) + 1);
    lapEl.textContent = `LAP ${leaderLaps} / 2`;
    statusEl.textContent = leader.progress >= 2 ? 'FINISH · GRAND PRIX' : 'RACE ON';

    const u = ((leader.progress + leader.startOffset) % 1 + 1) % 1;
    const f = frameAt(u);
    const chaseTarget = leader.root.position.clone().addScaledVector(f.tangent, -13).add(new THREE.Vector3(0, 7.5, 0));
    const aim = leader.root.position.clone().addScaledVector(f.tangent, 5).add(new THREE.Vector3(0, 1.6, 0));
    const cutPhase = raceTime % 12;
    const trackside = cutPhase > 8.4 && cutPhase < 10.7;
    if (trackside) {
      const side = frameAt(u).right;
      chasePos.copy(leader.root.position).addScaledVector(side, 24).addScaledVector(f.tangent, -5);
      chasePos.y += 10;
      lookPos.copy(leader.root.position).add(new THREE.Vector3(0, 1.5, 0));
      cameraLabel.textContent = 'TRACKSIDE CAM';
    } else {
      chasePos.copy(chaseTarget);
      lookPos.copy(aim);
      cameraLabel.textContent = 'CHASE CAM';
    }
    if (!cameraInitialized) {
      camera.position.copy(chasePos); cameraInitialized = true;
    }
    camera.position.lerp(chasePos, 1 - Math.exp(-dt * (trackside ? 2.6 : 4.2)));
    tempVec.copy(lookPos);
    camera.lookAt(tempVec);
    camera.fov = THREE.MathUtils.damp(camera.fov, trackside ? 56 : 62, 2.5, dt);
    camera.updateProjectionMatrix();
  }

  for (const p of particles) {
    if (!p.sprite.visible) continue;
    p.life -= dt;
    if (p.life <= 0) { p.sprite.visible = false; continue; }
    p.sprite.position.addScaledVector(p.velocity, dt);
    p.velocity.y += 0.55 * dt;
    const k = p.life / p.maxLife;
    p.sprite.material.opacity = 0.62 * k;
    const s = 1.0 + (1 - k) * 2.1;
    p.sprite.scale.set(s, s, 1);
  }
  renderer.render(scene, camera);
}
animate();

addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.7));
});
</script>
</body>
</html>
```