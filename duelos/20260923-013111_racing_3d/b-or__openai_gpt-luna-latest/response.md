```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Velocity GP</title>
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; width: 100%; height: 100%; overflow: hidden; background: #91cbea; font-family: "Arial Narrow", "Trebuchet MS", sans-serif; }
  canvas { display: block; width: 100%; height: 100%; }
  #hud { position: fixed; inset: 0; color: white; pointer-events: none; text-transform: uppercase; }
  .panel {
    position: absolute; top: 22px; padding: 15px 20px;
    background: linear-gradient(135deg, rgba(7,19,31,.88), rgba(7,19,31,.57));
    border: 1px solid rgba(255,255,255,.23);
    box-shadow: 0 8px 30px rgba(0,0,0,.2);
    backdrop-filter: blur(6px);
  }
  #speedPanel { left: 22px; min-width: 190px; border-left: 4px solid #ff4c39; }
  #racePanel { right: 22px; min-width: 185px; text-align: right; border-right: 4px solid #ffcf39; }
  .eyebrow { font-size: 10px; letter-spacing: .24em; color: #b4cbd9; font-weight: bold; }
  #speed { margin-top: 1px; font-size: 48px; line-height: .98; font-weight: 900; letter-spacing: -.05em; font-variant-numeric: tabular-nums; }
  #speed small { font-size: 13px; letter-spacing: .16em; margin-left: 4px; color: #c9d7df; }
  #gear { color: #ffce45; font-size: 11px; letter-spacing: .17em; margin-top: 8px; }
  #lap { font-size: 27px; font-weight: 900; margin-top: 3px; letter-spacing: .02em; }
  #position { font-size: 14px; color: #ffda59; font-weight: 800; margin-top: 4px; letter-spacing: .12em; }
  #brand { position: absolute; top: 27px; left: 50%; transform: translateX(-50%); text-align: center; text-shadow: 0 2px 8px rgba(0,0,0,.25); }
  #brand strong { display: block; font-size: 17px; letter-spacing: .29em; }
  #brand span { display: block; margin-top: 4px; font-size: 9px; letter-spacing: .31em; color: #ecf7ff; }
  #bottomHud { position: absolute; left: 50%; bottom: 25px; transform: translateX(-50%); width: min(420px, 75vw); text-align: center; }
  #raceBar { display: flex; gap: 5px; height: 5px; margin: 0 0 10px; }
  #raceBar i { flex: 1; background: rgba(255,255,255,.35); transform: skewX(-22deg); }
  #raceBar i.active { background: #ffcf39; box-shadow: 0 0 10px rgba(255,207,57,.55); }
  #message { font-size: 10px; letter-spacing: .22em; text-shadow: 0 2px 5px rgba(0,0,0,.6); }
  #vignette { position: fixed; inset: 0; pointer-events: none; box-shadow: inset 0 0 130px rgba(7,26,42,.32); }
  @media (max-width: 600px) {
    .panel { top: 12px; padding: 11px 13px; }
    #speedPanel { left: 12px; min-width: 145px; }
    #racePanel { right: 12px; min-width: 140px; }
    #speed { font-size: 38px; }
    #lap { font-size: 21px; }
    #brand { top: 115px; }
  }
</style>
</head>
<body>
<div id="hud">
  <div id="speedPanel" class="panel">
    <div class="eyebrow">Velocity / kmh</div>
    <div id="speed">000<small>KM/H</small></div>
    <div id="gear">AUTO&nbsp;&nbsp; // &nbsp;&nbsp;RACE MODE</div>
  </div>
  <div id="brand"><strong>VELOCITY GP</strong><span>NEON COAST GRAND PRIX</span></div>
  <div id="racePanel" class="panel">
    <div class="eyebrow">Race progress</div>
    <div id="lap">LAP 1 / 3</div>
    <div id="position">1ST POSITION</div>
  </div>
  <div id="bottomHud">
    <div id="raceBar"><i class="active"></i><i></i><i></i></div>
    <div id="message">AUTOPILOT ENGAGED &nbsp; • &nbsp; FULL THROTTLE</div>
  </div>
</div>
<div id="vignette"></div>

<script type="module">
import * as THREE from 'three';

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x9ed8f2);
scene.fog = new THREE.Fog(0x9ed8f2, 260, 650);

const camera = new THREE.PerspectiveCamera(62, innerWidth / innerHeight, 0.1, 1200);
const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.08;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);

scene.add(new THREE.HemisphereLight(0xe4f7ff, 0x52713d, 2.0));
const sun = new THREE.DirectionalLight(0xfff1d0, 3.1);
sun.position.set(-100, 170, 80);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.camera.left = -230;
sun.shadow.camera.right = 230;
sun.shadow.camera.top = 230;
sun.shadow.camera.bottom = -230;
sun.shadow.bias = -0.00015;
scene.add(sun);

const mat = (color, roughness = 0.8, metalness = 0) =>
  new THREE.MeshStandardMaterial({ color, roughness, metalness });

const grassMat = mat(0x52943d);
const ground = new THREE.Mesh(new THREE.PlaneGeometry(1800, 1800), grassMat);
ground.rotation.x = -Math.PI / 2;
ground.position.y = -0.16;
ground.receiveShadow = true;
scene.add(ground);

// Gently rolling-looking fields, made from broad procedural patches.
const patchMat = [mat(0x5a9b42), mat(0x4e8e3a), mat(0x62a449)];
for (let i = 0; i < 48; i++) {
  const x = Math.sin(i * 12.7) * 210;
  const z = Math.cos(i * 8.31) * 185;
  const patch = new THREE.Mesh(new THREE.CircleGeometry(18 + (i % 5) * 5, 12), patchMat[i % patchMat.length]);
  patch.rotation.x = -Math.PI / 2;
  patch.position.set(x, -0.145, z);
  patch.scale.set(1.8, 1, 0.8 + (i % 3) * .25);
  scene.add(patch);
}

// Closed, smooth, procedurally built race circuit.
const controlPoints = [
  [0,-69], [35,-68], [70,-59], [103,-43], [116,-18],
  [111,7], [93,25], [69,31], [56,48], [34,66],
  [4,72], [-30,68], [-62,57], [-91,40], [-111,17],
  [-116,-10], [-102,-34], [-79,-49], [-53,-63], [-27,-70]
].map(([x,z]) => new THREE.Vector3(x, 0, z));
const trackCurve = new THREE.CatmullRomCurve3(controlPoints, true, 'centripetal');
const trackLength = trackCurve.getLength();
const SAMPLES = 640;
const HALF_ROAD = 7.1;

function frameAt(t) {
  const u = ((t % 1) + 1) % 1;
  const point = trackCurve.getPointAt(u);
  const tangent = trackCurve.getTangentAt(u).setY(0).normalize();
  const side = new THREE.Vector3(tangent.z, 0, -tangent.x).normalize();
  return { point, tangent, side };
}

function ribbonGeometry(leftOffset, rightOffset, y, colorFn = null) {
  const positions = [], colors = [], indices = [];
  const color = new THREE.Color();
  for (let i = 0; i <= SAMPLES; i++) {
    const f = frameAt(i / SAMPLES);
    for (const offset of [leftOffset, rightOffset]) {
      positions.push(
        f.point.x + f.side.x * offset, y,
        f.point.z + f.side.z * offset
      );
      if (colorFn) {
        color.set(colorFn(i));
        colors.push(color.r, color.g, color.b);
      }
    }
  }
  for (let i = 0; i < SAMPLES; i++) {
    const a = i * 2;
    indices.push(a, a + 1, a + 2, a + 1, a + 3, a + 2);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  if (colorFn) g.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
  g.setIndex(indices);
  g.computeVertexNormals();
  return g;
}

const asphaltMat = new THREE.MeshStandardMaterial({ color: 0x343a40, roughness: .91 });
const road = new THREE.Mesh(ribbonGeometry(-HALF_ROAD, HALF_ROAD, 0.005), asphaltMat);
road.receiveShadow = true;
road.position.y = 0.005;
scene.add(road);

// Narrow paved shoulders and crisp painted edge lines.
const shoulderMat = mat(0x777b79);
for (const sign of [-1, 1]) {
  const shoulder = new THREE.Mesh(ribbonGeometry(sign * (HALF_ROAD + 0.02), sign * (HALF_ROAD + 1.45), 0.012), shoulderMat);
  shoulder.material.side = THREE.DoubleSide;
  scene.add(shoulder);
  const line = new THREE.Mesh(ribbonGeometry(sign * (HALF_ROAD - .12), sign * (HALF_ROAD + .05), 0.024), mat(0xf2eee0, .6));
  line.material.side = THREE.DoubleSide;
  scene.add(line);
}

// Alternating red/white kerbs, built as colored procedural ribbon segments.
function makeKerbGeometry(sign) {
  const p = [], c = [], idx = [];
  const red = new THREE.Color(0xe83e37), white = new THREE.Color(0xf3eee1);
  const segments = 160;
  for (let s = 0; s < segments; s++) {
    const a = s / segments, b = (s + 1) / segments;
    const fa = frameAt(a), fb = frameAt(b);
    const tone = Math.floor(s / 2) % 2 ? white : red;
    const start = p.length / 3;
    for (const [f, offset] of [[fa, sign * (HALF_ROAD - .03)], [fa, sign * (HALF_ROAD + .92)], [fb, sign * (HALF_ROAD - .03)], [fb, sign * (HALF_ROAD + .92)]]) {
      p.push(f.point.x + f.side.x * offset, .04, f.point.z + f.side.z * offset);
      c.push(tone.r, tone.g, tone.b);
    }
    idx.push(start, start + 1, start + 2, start + 1, start + 3, start + 2);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(p, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(c, 3));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}
const kerbMat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: .8, side: THREE.DoubleSide });
for (const side of [-1, 1]) {
  const kerb = new THREE.Mesh(makeKerbGeometry(side), kerbMat);
  kerb.receiveShadow = true;
  scene.add(kerb);
}

// Start/finish checkerboard across the asphalt.
{
  const f = frameAt(0);
  const cols = 12, rows = 2, width = HALF_ROAD * 2, depth = 1.55;
  const positions = [], colors = [], indices = [];
  const c1 = new THREE.Color(0xfaf8ee), c2 = new THREE.Color(0x17191b);
  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      const s0 = -width / 2 + width * col / cols;
      const s1 = -width / 2 + width * (col + 1) / cols;
      const t0 = -depth / 2 + depth * row / rows;
      const t1 = -depth / 2 + depth * (row + 1) / rows;
      const start = positions.length / 3;
      for (const [s, t] of [[s0,t0],[s1,t0],[s0,t1],[s1,t1]]) {
        positions.push(f.point.x + f.side.x*s + f.tangent.x*t, .055, f.point.z + f.side.z*s + f.tangent.z*t);
        const c = (row + col) % 2 ? c1 : c2;
        colors.push(c.r, c.g, c.b);
      }
      indices.push(start,start+1,start+2,start+1,start+3,start+2);
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(positions,3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(colors,3));
  g.setIndex(indices);
  g.computeVertexNormals();
  scene.add(new THREE.Mesh(g, new THREE.MeshStandardMaterial({ vertexColors: true, side: THREE.DoubleSide })));
}

// Simple trackside scenery.
let seed = 87321;
function random() { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; }
const trunkGeo = new THREE.CylinderGeometry(.18, .28, 2.1, 7);
const leafGeo = new THREE.ConeGeometry(1.35, 3.6, 7);
const trunkMat = mat(0x72503a);
const leafMats = [mat(0x23613a), mat(0x2e7540), mat(0x397f45)];
const trackSamples = Array.from({length: 180}, (_, i) => trackCurve.getPointAt(i / 180));

for (let i = 0; i < 115; i++) {
  let x, z, tries = 0, clear = false;
  while (!clear && tries++ < 60) {
    x = (random() - .5) * 370;
    z = (random() - .5) * 330;
    let nearest = Infinity;
    for (let j = 0; j < trackSamples.length; j += 3) {
      const dx = x - trackSamples[j].x, dz = z - trackSamples[j].z;
      nearest = Math.min(nearest, dx*dx + dz*dz);
    }
    clear = nearest > 17 * 17;
  }
  if (!clear) continue;
  const scale = .72 + random() * .8;
  const tree = new THREE.Group();
  const trunk = new THREE.Mesh(trunkGeo, trunkMat);
  trunk.position.y = 1.05;
  trunk.castShadow = true;
  tree.add(trunk);
  const foliage = new THREE.Mesh(leafGeo, leafMats[i % leafMats.length]);
  foliage.position.y = 3.15;
  foliage.scale.set(.85 + random() * .35, .9 + random() * .45, .85 + random() * .35);
  foliage.castShadow = true;
  tree.add(foliage);
  const crown = new THREE.Mesh(new THREE.ConeGeometry(.91, 2.5, 7), leafMats[(i + 1) % leafMats.length]);
  crown.position.y = 4.25;
  crown.castShadow = true;
  tree.add(crown);
  tree.position.set(x, 0, z);
  tree.scale.setScalar(scale);
  scene.add(tree);
}

// Grandstand and paddock buildings add a little race-day atmosphere.
function addBuilding(x, z, w, h, d, color) {
  const box = new THREE.Mesh(new THREE.BoxGeometry(w,h,d), mat(color, .85));
  box.position.set(x, h/2 - .1, z);
  box.castShadow = true;
  box.receiveShadow = true;
  scene.add(box);
}
addBuilding(145, 10, 27, 10, 18, 0xb9c5c7);
addBuilding(150, 10, 28, 2, 20, 0xe54a3d);
addBuilding(-151, -5, 19, 7, 15, 0xd2d9d7);
addBuilding(-148, -5, 20, 1.5, 16, 0x353d43);
for (let i = 0; i < 9; i++) {
  const stand = new THREE.Mesh(new THREE.BoxGeometry(19, 1.1, 2.3), mat(i % 2 ? 0x246e9d : 0xe6e5dc));
  stand.position.set(137 + i * .7, 2 + i * .72, -24 - i * 2.0);
  stand.rotation.x = -.12;
  scene.add(stand);
}
const bannerMat = mat(0xffcb35, .45);
for (let i = 0; i < 7; i++) {
  const sign = new THREE.Mesh(new THREE.BoxGeometry(5.5, 1.4, .35), bannerMat);
  sign.position.set(-30 + i * 10, 1.4, -83);
  scene.add(sign);
}

// Soft, stylized clouds in the distance.
const cloudMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 1, transparent: true, opacity: .82 });
for (let i = 0; i < 14; i++) {
  const cloud = new THREE.Group();
  const cx = (random() - .5) * 520, cz = (random() - .5) * 460;
  for (let j = 0; j < 4; j++) {
    const puff = new THREE.Mesh(new THREE.SphereGeometry(1, 10, 8), cloudMat);
    puff.position.set(j * 3.1, (j % 2) * .8, (j % 2) * .5);
    puff.scale.set(4.2, 1.5, 2.0);
    cloud.add(puff);
  }
  cloud.position.set(cx, 62 + random() * 28, cz);
  scene.add(cloud);
}

// Primitive-built arcade sports car, with independently spinning wheels.
function makeCar(paintColor, accentColor, number) {
  const root = new THREE.Group();
  const paint = new THREE.MeshStandardMaterial({ color: paintColor, roughness: .28, metalness: .28 });
  const accent = new THREE.MeshStandardMaterial({ color: accentColor, roughness: .34, metalness: .2 });
  const glass = new THREE.MeshStandardMaterial({ color: 0x142d3d, roughness: .16, metalness: .25, transparent: true, opacity: .91 });
  const rubber = mat(0x141719, .92);
  const alloy = mat(0xb8c5c9, .3, .7);
  const dark = mat(0x10171b, .65, .2);
  const headlight = new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xd5f2ff, emissiveIntensity: 2.2 });
  const tailLight = new THREE.MeshStandardMaterial({ color: 0xff342b, emissive: 0xff1608, emissiveIntensity: 1.8 });

  function box(w,h,d, material, x,y,z, parent=root) {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w,h,d), material);
    m.position.set(x,y,z);
    m.castShadow = true;
    m.receiveShadow = true;
    parent.add(m);
    return m;
  }

  box(1.93,.55,4.05,paint,0,.69,0);
  box(1.83,.23,1.42,paint,0,.98,1.12);
  box(1.78,.25,1.05,paint,0,.96,-1.34);
  box(1.5,.55,1.72,paint,0,1.18,-.23);
  box(1.23,.42,1.44,glass,0,1.39,-.23);
  // Slanted windscreen and rear glass.
  const wind = box(1.52,.49,.075,glass,0,1.28,.66);
  wind.rotation.x = -.45;
  const rearGlass = box(1.48,.43,.07,glass,0,1.27,-1.08);
  rearGlass.rotation.x = .48;
  for (const s of [-1,1]) {
    const sideWindow = box(.06,.39,1.16,glass,s*.77,1.37,-.22);
    sideWindow.rotation.y = s * .08;
    box(.08,.12,2.9,accent,s*.79,.84,-.02);
    box(.035,.08,1.3,dark,s*.98,.62,-.12);
  }

  // Twin racing stripes.
  for (const x of [-.31,.31]) {
    box(.12,.018,1.35,accent,x,1.105,1.09);
    box(.12,.018,1.47,accent,x,1.47,-.23);
    box(.12,.018,.72,accent,x,1.105,-1.35);
  }

  box(1.45,.12,.19,dark,0,.57,2.02);
  box(1.28,.16,.18,dark,0,.62,-2.02);
  box(1.98,.12,.16,accent,0,1.42,-1.83);
  for (const s of [-1,1]) box(.12,.58,.12,dark,s*.68,1.15,-1.79);

  // Grille, front lights and rear lamps.
  box(.72,.22,.045,dark,0,.66,2.05);
  for (const s of [-1,1]) {
    box(.43,.19,.09,headlight,s*.62,.82,2.04);
    box(.38,.13,.08,tailLight,s*.64,.82,-2.04);
    box(.11,.2,.08,mat(0xffd548,.4),s*.86,.67,1.95);
  }

  // Number panel on the roof, plus mirrors.
  box(.48,.035,.52,accent,0,1.625,-.18);
  box(.36,.018,.37,mat(0xf5f1de),0,1.65,-.18);
  for (const s of [-1,1]) {
    box(.18,.12,.25,paint,s*1.02,1.17,.56);
    box(.12,.08,.15,glass,s*1.08,1.25,.56);
  }

  const wheels = [];
  const tireGeo = new THREE.CylinderGeometry(.43,.43,.34,16,1);
  const rimGeo = new THREE.CylinderGeometry(.245,.245,.36,12,1);
  const hubGeo = new THREE.CylinderGeometry(.105,.105,.375,12);
  for (const x of [-1.02,1.02]) {
    for (const z of [-1.28,1.28]) {
      const pivot = new THREE.Group();
      pivot.position.set(x,.43,z);
      root.add(pivot);
      const tire = new THREE.Mesh(tireGeo,rubber);
      tire.rotation.z = Math.PI/2;
      tire.castShadow = true;
      pivot.add(tire);
      const rim = new THREE.Mesh(rimGeo,alloy);
      rim.rotation.z = Math.PI/2;
      pivot.add(rim);
      const hub = new THREE.Mesh(hubGeo,dark);
      hub.rotation.z = Math.PI/2;
      pivot.add(hub);
      for (let k=0;k<5;k++) {
        const spoke = new THREE.Mesh(new THREE.BoxGeometry(.035,.31,.045),mat(0xd6e0e2,.32,.62));
        spoke.position.set(x > 0 ? .19 : -.19,0,0);
        spoke.rotation.x = k * Math.PI * 2/5;
        pivot.add(spoke);
      }
      wheels.push(pivot);
    }
  }

  // Small, legible racing number on both doors.
  const numberMat = new THREE.MeshStandardMaterial({ color: 0xf5f3e6, roughness: .7 });
  for (const s of [-1,1]) {
    box(.025,.39,.43,numberMat,s*1.005,.97,-.18);
  }

  root.userData = { wheels, number };
  return root;
}

const drivers = [
  { name: 'YOU', color: 0xf04432, accent: 0xffcf3c, start: 4, pace: 26.1, lane: 0 },
  { name: 'NOVA', color: 0x168be0, accent: 0xeaf7ff, start: 16, pace: 26.8, lane: -2.6 },
  { name: 'BOLT', color: 0xffbf20, accent: 0x20252a, start: -18, pace: 25.9, lane: 2.7 },
  { name: 'VANTA', color: 0x8d54d9, accent: 0x50f0d4, start: -41, pace: 27.2, lane: .6 }
];
for (const driver of drivers) {
  driver.car = makeCar(driver.color, driver.accent, driver.name);
  driver.progress = driver.start;
  scene.add(driver.car);
}

const speedEl = document.getElementById('speed');
const lapEl = document.getElementById('lap');
const positionEl = document.getElementById('position');
const barSegments = [...document.querySelectorAll('#raceBar i')];

function ordinal(n) {
  return n + (n % 100 >= 11 && n % 100 <= 13 ? 'TH' : ({1:'ST',2:'ND',3:'RD'}[n % 10] || 'TH'));
}

let elapsed = 0;
let lastTimestamp = 0;
const cameraTarget = new THREE.Vector3();
const desiredCamera = new THREE.Vector3();

function updateCar(driver, index, dt, time) {
  const wobble = Math.sin(time * .74 + index * 1.8) * .95 + Math.sin(time * .29 + index) * .4;
  const speed = driver.pace + wobble;
  driver.currentSpeed = speed;
  driver.progress += speed * dt;

  const fraction = driver.progress / trackLength;
  const frame = frameAt(fraction);
  const laneWave = Math.sin(time * .6 + index * 2.4) * .38;
  const lane = driver.lane + laneWave;
  driver.car.position.set(
    frame.point.x + frame.side.x * lane,
    .015 + Math.sin(time * 13 + index) * .012,
    frame.point.z + frame.side.z * lane
  );
  driver.car.rotation.y = Math.atan2(frame.tangent.x, frame.tangent.z);
  for (const wheel of driver.car.userData.wheels) wheel.rotation.x -= speed * dt / .43;
}

function animate(timestamp) {
  requestAnimationFrame(animate);
  const dt = lastTimestamp ? Math.min((timestamp - lastTimestamp) / 1000, .05) : 0;
  lastTimestamp = timestamp;
  elapsed = timestamp / 1000;

  drivers.forEach((driver, i) => updateCar(driver, i, dt, elapsed));

  const player = drivers[0];
  const pf = frameAt(player.progress / trackLength);
  const carPos = player.car.position;
  desiredCamera.set(
    carPos.x - pf.tangent.x * 12.8 + pf.side.x * 1.2,
    6.0 + Math.sin(elapsed * 2.1) * .09,
    carPos.z - pf.tangent.z * 12.8 + pf.side.z * 1.2
  );
  const smooth = 1 - Math.exp(-dt * 3.6);
  camera.position.lerp(desiredCamera, smooth);
  const lookAhead = frameAt((player.progress + 20) / trackLength);
  cameraTarget.set(lookAhead.point.x, 1.1, lookAhead.point.z);
  camera.lookAt(cameraTarget);
  camera.fov = 62 + Math.min(player.currentSpeed / 26, 1) * 4;
  camera.updateProjectionMatrix();

  const speedKmh = Math.round(player.currentSpeed * 3.6);
  speedEl.innerHTML = String(speedKmh).padStart(3, '0') + '<small>KM/H</small>';

  const lap = Math.min(3, Math.floor(Math.max(0, player.progress) / trackLength) + 1);
  lapEl.textContent = `LAP ${lap} / 3`;
  barSegments.forEach((segment, i) => segment.classList.toggle('active', i < lap));

  const standings = [...drivers].sort((a,b) => b.progress - a.progress);
  const place = standings.indexOf(player) + 1;
  positionEl.textContent = `${ordinal(place)} POSITION`;

  renderer.render(scene, camera);
}

requestAnimationFrame(animate);

addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
});
</script>
</body>
</html>
```