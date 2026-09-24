<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Solar System Cinematic Tour</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { overflow: hidden; background: #000; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
  #canvas { display: block; }
  #planet-label {
    position: fixed;
    bottom: 80px;
    left: 50%;
    transform: translateX(-50%);
    color: #fff;
    font-size: 2.5rem;
    font-weight: 300;
    letter-spacing: 0.1em;
    text-shadow: 0 0 20px rgba(255,255,255,0.8), 0 0 40px rgba(255,200,100,0.6);
    opacity: 0;
    transition: opacity 1.5s ease, transform 1.5s ease;
    pointer-events: none;
    z-index: 10;
    text-align: center;
    max-width: 90vw;
  }
  #planet-label.visible { opacity: 1; }
  #planet-label .name { display: block; }
  #planet-label .detail { display: block; font-size: 1rem; font-weight: 200; letter-spacing: 0.05em; margin-top: 0.5rem; opacity: 0.8; }
</style>
</head>
<body>
<canvas id="canvas"></canvas>
<div id="planet-label"><span class="name"></span><span class="detail"></span></div>
<script type="module">
import * as THREE from 'three';

// ============ CONFIG ============
const PLANET_DATA = [
  { name: 'Mercury', distance: 8, size: 0.38, orbitSpeed: 4.15, rotationSpeed: 0.004, color: 0xb5b5b5, texture: 'mercury', moons: [] },
  { name: 'Venus',   distance: 11, size: 0.95, orbitSpeed: 1.62, rotationSpeed: -0.0004, color: 0xe6c87a, texture: 'venus', moons: [] },
  { name: 'Earth',   distance: 15, size: 1.0, orbitSpeed: 1.0, rotationSpeed: 0.01, color: 0x2b6cd4, texture: 'earth', moons: [
    { name: 'Moon', distance: 2.5, size: 0.27, orbitSpeed: 13.0, rotationSpeed: 0.001, color: 0xaaaaaa, texture: 'moon' }
  ]},
  { name: 'Mars',    distance: 20, size: 0.53, orbitSpeed: 0.53, rotationSpeed: 0.009, color: 0xd94a1b, texture: 'mars', moons: [] },
  { name: 'Jupiter', distance: 32, size: 4.0, orbitSpeed: 0.084, rotationSpeed: 0.04, color: 0xd4a574, texture: 'jupiter', moons: [] },
  { name: 'Saturn',  distance: 45, size: 3.4, orbitSpeed: 0.034, rotationSpeed: 0.038, color: 0xf4e4bc, texture: 'saturn', moons: [], hasRings: true },
  { name: 'Uranus',  distance: 55, size: 2.0, orbitSpeed: 0.012, rotationSpeed: -0.02, color: 0x7de3f4, texture: 'uranus', moons: [], tilt: Math.PI / 2 },
  { name: 'Neptune', distance: 65, size: 1.9, orbitSpeed: 0.006, rotationSpeed: 0.025, color: 0x4b70dd, texture: 'neptune', moons: [] }
];

const TOUR_SCHEDULE = [
  { target: 'sun', duration: 6, hold: 3, offset: new THREE.Vector3(0, 15, 30) },
  { target: 'Mercury', duration: 4, hold: 3, offset: new THREE.Vector3(0, 3, 8) },
  { target: 'Venus', duration: 4, hold: 3, offset: new THREE.Vector3(0, 4, 10) },
  { target: 'Earth', duration: 4, hold: 4, offset: new THREE.Vector3(0, 4, 12) },
  { target: 'Mars', duration: 4, hold: 3, offset: new THREE.Vector3(0, 3, 10) },
  { target: 'Jupiter', duration: 6, hold: 5, offset: new THREE.Vector3(0, 20, 60) },
  { target: 'Saturn', duration: 6, hold: 5, offset: new THREE.Vector3(0, 15, 50) },
  { target: 'Uranus', duration: 5, hold: 3, offset: new THREE.Vector3(15, 10, 30) },
  { target: 'Neptune', duration: 5, hold: 3, offset: new THREE.Vector3(-15, 10, 30) },
  { target: 'sun', duration: 8, hold: 4, offset: new THREE.Vector3(0, 40, 100) }
];

// ============ RENDERER & SCENE ============
const canvas = document.getElementById('canvas');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.2;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();

const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 2000);
camera.position.set(0, 80, 150);

const labelEl = document.getElementById('planet-label');
const labelName = labelEl.querySelector('.name');
const labelDetail = labelEl.querySelector('.detail');

// ============ STARFIELD ============
function createStarfield() {
  const starsGeometry = new THREE.BufferGeometry();
  const count = 15000;
  const positions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);
  const sizes = new Float32Array(count);
  const color = new THREE.Color();
  for (let i = 0; i < count; i++) {
    const r = 400 + Math.random() * 600;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    positions[i*3] = r * Math.sin(phi) * Math.cos(theta);
    positions[i*3+1] = r * Math.sin(phi) * Math.sin(theta);
    positions[i*3+2] = r * Math.cos(phi);
    const t = Math.random();
    color.setHSL(0.6 + t * 0.1, 0.3, 0.6 + t * 0.4);
    colors[i*3] = color.r; colors[i*3+1] = color.g; colors[i*3+2] = color.b;
    sizes[i] = 0.5 + Math.random() * 2;
  }
  starsGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  starsGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  starsGeometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
  const material = new THREE.PointsMaterial({ size: 1, vertexColors: true, transparent: true, opacity: 0.9, sizeAttenuation: true });
  const stars = new THREE.Points(starsGeometry, material);
  scene.add(stars);
  return stars;
}
const starfield = createStarfield();

// ============ PROCEDURAL TEXTURES ============
const textureCache = {};
function generateTexture(type, width = 512, height = 256) {
  if (textureCache[type]) return textureCache[type];
  const canvas = document.createElement('canvas');
  canvas.width = width; canvas.height = height;
  const ctx = canvas.getContext('2d');
  const imgData = ctx.createImageData(width, height);
  const data = imgData.data;

  switch(type) {
    case 'mercury': // cratered gray
      for (let y=0;y<height;y++) for(let x=0;x<width;x++) {
        const i=(y*width+x)*4;
        const n = noise(x/20,y/20,0)*0.5+noise(x/5,y/5,100)*0.3+noise(x/2,y/2,200)*0.2;
        const v = Math.floor(120 + n*60);
        data[i]=data[i+1]=data[i+2]=v; data[i+3]=255;
      }
      break;
    case 'venus': // thick clouds
      for (let y=0;y<height;y++) for(let x=0;x<width;x++) {
        const i=(y*width+x)*4;
        const n = fbm(x/30,y/30,4);
        const v = Math.floor(200 + n*40);
        data[i]=Math.floor(v*1.1); data[i+1]=Math.floor(v*1.0); data[i+2]=Math.floor(v*0.8); data[i+3]=255;
      }
      break;
    case 'earth': // continents/oceans
      for (let y=0;y<height;y++) for(let x=0;x<width;x++) {
        const i=(y*width+x)*4;
        const nx = x/width-0.5, ny = y/height-0.5;
        const n = fbm(nx*8, ny*8, 6) * 0.5 + 0.5;
        let r,g,b;
        if (n < 0.45) { r=10; g=30; b=Math.floor(80+n*100); }
        else if (n < 0.5) { r=Math.floor(80+n*100); g=Math.floor(120+n*80); b=40; }
        else if (n < 0.65) { r=Math.floor(30+n*150); g=Math.floor(100+n*100); b=30; }
        else { r=Math.floor(180+n*50); g=Math.floor(170+n*50); b=Math.floor(150+n*50); }
        data[i]=r; data[i+1]=g; data[i+2]=b; data[i+3]=255;
      }
      // clouds layer
      const cloudCanvas = document.createElement('canvas');
      cloudCanvas.width=width; cloudCanvas.height=height;
      const cctx = cloudCanvas.getContext('2d');
      const cdata = cctx.createImageData(width,height).data;
      for (let y=0;y<height;y++) for(let x=0;x<width;x++) {
        const i=(y*width+x)*4;
        const n = noise(x/40,y/40,500)*0.5+noise(x/10,y/10,600)*0.5;
        const a = Math.max(0, (n-0.3)*1.2)*255;
        cdata[i]=cdata[i+1]=cdata[i+2]=255; cdata[i+3]=a;
      }
      cctx.putImageData(new ImageData(cdata,width,height),0,0);
      ctx.drawImage(cloudCanvas,0,0);
      break;
    case 'moon':
      for (let y=0;y<height;y++) for(let x=0;x<width;x++) {
        const i=(y*width+x)*4;
        const n = noise(x/15,y/15,0)*0.6+noise(x/5,y/5,100)*0.4;
        const v = Math.floor(60 + n*80);
        data[i]=data[i+1]=data[i+2]=v; data[i+3]=255;
      }
      // craters
      for(let c=0;c<30;c++) {
        const cx=Math.random()*width, cy=Math.random()*height, cr=5+Math.random()*30;
        ctx.fillStyle=`rgba(40,40,40,${0.1+Math.random()*0.2})`;
        ctx.beginPath(); ctx.arc(cx,cy,cr,0,Math.PI*2); ctx.fill();
      }
      break;
    case 'mars':
      for (let y=0;y<height;y++) for(let x=0;x<width;x++) {
        const i=(y*width+x)*4;
        const n = fbm(x/25,y/25,5);
        const v = Math.floor(100 + n*100);
        data[i]=Math.floor(v*1.2); data[i+1]=Math.floor(v*0.4); data[i+2]=Math.floor(v*0.2); data[i+3]=255;
      }
      break;
    case 'jupiter': // bands
      for (let y=0;y<height;y++) for(let x=0;x<width;x++) {
        const i=(y*width+x)*4;
        const lat = (y/height-0.5)*Math.PI;
        const band = Math.sin(lat*12 + Math.sin(x/width*Math.PI*4)*0.5);
        const n = noise(x/40,y/40,0)*0.3;
        const b = band*0.5+0.5+n;
        let r,g,bc;
        if (b<0.3) { r=180; g=140; bc=100; }
        else if (b<0.6) { r=200; g=170; bc=120; }
        else { r=150; g=120; bc=90; }
        data[i]=Math.floor(r*(0.8+n)); data[i+1]=Math.floor(g*(0.8+n)); data[i+2]=Math.floor(bc*(0.8+n)); data[i+3]=255;
      }
      // great red spot
      const spotX = width*0.3, spotY = height*0.55, spotR = width*0.12;
      for (let y=0;y<height;y++) for(let x=0;x<width;x++) {
        const dx=x-spotX, dy=y-spotY;
        if (dx*dx+dy*dy < spotR*spotR) {
          const i=(y*width+x)*4;
          const d=Math.sqrt(dx*dx+dy*dy)/spotR;
          const f=1-d;
          data[i]=Math.min(255,data[i]+Math.floor(80*f));
          data[i+1]=Math.max(0,data[i+1]-Math.floor(40*f));
          data[i+2]=Math.max(0,data[i+2]-Math.floor(40*f));
        }
      }
      break;
    case 'saturn':
      for (let y=0;y<height;y++) for(let x=0;x<width;x++) {
        const i=(y*width+x)*4;
        const lat = (y/height-0.5)*Math.PI;
        const band = Math.sin(lat*10);
        const n = noise(x/50,y/50,0)*0.2;
        const b = band*0.4+0.5+n;
        let r,g,bc;
        if (b<0.4) { r=220; g=200; bc=160; }
        else { r=240; g=220; bc=180; }
        data[i]=Math.floor(r*(0.9+n)); data[i+1]=Math.floor(g*(0.9+n)); data[i+2]=Math.floor(bc*(0.9+n)); data[i+3]=255;
      }
      break;
    case 'uranus':
      for (let y=0;y<height;y++) for(let x=0;x<width;x++) {
        const i=(y*width+x)*4;
        const n = fbm(x/60,y/60,3);
        const v = 0.4 + n*0.3;
        data[i]=Math.floor(100*v); data[i+1]=Math.floor(220*v); data[i+2]=Math.floor(240*v); data[i+3]=255;
      }
      break;
    case 'neptune':
      for (let y=0;y<height;y++) for(let x=0;x<width;x++) {
        const i=(y*width+x)*4;
        const n = fbm(x/50,y/50,4);
        const v = 0.3 + n*0.4;
        data[i]=Math.floor(50*v); data[i+1]=Math.floor(100*v); data[i+2]=Math.floor(200*v); data[i+3]=255;
      }
      break;
    default:
      for (let i=0;i<data.length;i+=4) { data[i]=data[i+1]=data[i+2]=255; data[i+3]=255; }
  }
  ctx.putImageData(imgData,0,0);
  const tex = new THREE.CanvasTexture(canvas);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  textureCache[type] = tex;
  return tex;
}

// Noise helpers
function noise(x,y,z) {
  // simple 3D value noise
  const X = Math.floor(x)&255, Y = Math.floor(y)&255, Z = Math.floor(z)&255;
  x-=Math.floor(x); y-=Math.floor(y); z-=Math.floor(z);
  const u=fade(x), v=fade(y), w=fade(z);
  const A=perm[X]+Y, AA=perm[A]+Z, AB=perm[A+1]+Z, B=perm[X+1]+Y, BA=perm[B]+Z, BB=perm[B+1]+Z;
  return lerp(w, lerp(v, lerp(u, grad(perm[AA],x,y,z), grad(perm[BA],x-1,y,z)), lerp(u, grad(perm[AB],x,y-1,z), grad(perm[BB],x-1,y-1,z))), lerp(v, lerp(u, grad(perm[AA+1],x,y,z-1), grad(perm[BA+1],x-1,y,z-1)), lerp(u, grad(perm[AB+1],x,y-1,z-1), grad(perm[BB+1],x-1,y-1,z-1))));
}
function fade(t){return t*t*t*(t*(t*6-15)+10);}
function lerp(t,a,b){return a+t*(b-a);}
function grad(hash,x,y,z){const h=hash&15; const u=h<8?x:y; const v=h<4?y:h===12||h===14?x:z; return ((h&1)===0?u:-u)+((h&2)===0?v:-v);}
const perm = new Uint8Array(512);
const p = new Array(256).fill(0).map((_,i)=>i).sort(()=>Math.random()-0.5);
for(let i=0;i<256;i++) perm[i]=perm[i+256]=p[i];
function fbm(x,y,octaves){let v=0,a=1,f=1;for(let i=0;i<octaves;i++){v+=a*noise(x*f,y*f,0);a*=0.5;f*=2;}return v;}

// ============ SUN ============
function createSun() {
  const group = new THREE.Group();
  // Sun sphere
  const sunGeo = new THREE.SphereGeometry(6, 64, 64);
  const sunMat = new THREE.MeshBasicMaterial({
    color: 0xffcc00,
    transparent: true,
    opacity: 1,
    depthWrite: false
  });
  const sunMesh = new THREE.Mesh(sunGeo, sunMat);
  sunMesh.renderOrder = 1;
  group.add(sunMesh);

  // Emissive glow sprite
  const spriteMat = new THREE.SpriteMaterial({
    map: createGlowTexture(),
    color: 0xffdd00,
    transparent: true,
    opacity: 0.6,
    blending: THREE.AdditiveBlending,
    depthWrite: false
  });
  const glow = new THREE.Sprite(spriteMat);
  glow.scale.set(28, 28, 28);
  glow.renderOrder = 0;
  group.add(glow);

  // Corona particles
  const coronaGeo = new THREE.BufferGeometry();
  const coronaCount = 2000;
  const cPos = new Float32Array(coronaCount * 3);
  const cSize = new Float32Array(coronaCount);
  const cColor = new Float32Array(coronaCount * 3);
  const cSpeed = new Float32Array(coronaCount);
  for (let i=0;i<coronaCount;i++) {
    const r = 6.5 + Math.random() * 4;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2*Math.random()-1);
    cPos[i*3] = r * Math.sin(phi) * Math.cos(theta);
    cPos[i*3+1] = r * Math.sin(phi) * Math.sin(theta);
    cPos[i*3+2] = r * Math.cos(phi);
    cSize[i] = 0.1 + Math.random() * 0.3;
    const hue = 0.1 + Math.random() * 0.08;
    const col = new THREE.Color().setHSL(hue, 1, 0.6 + Math.random()*0.2);
    cColor[i*3]=col.r; cColor[i*3+1]=col.g; cColor[i*3+2]=col.b;
    cSpeed[i] = 0.0005 + Math.random() * 0.002;
  }
  coronaGeo.setAttribute('position', new THREE.BufferAttribute(cPos,3));
  coronaGeo.setAttribute('size', new THREE.BufferAttribute(cSize,1));
  coronaGeo.setAttribute('color', new THREE.BufferAttribute(cColor,3));
  coronaGeo.setAttribute('speed', new THREE.BufferAttribute(cSpeed,1));
  const coronaMat = new THREE.PointsMaterial({
    size: 1, vertexColors: true, transparent: true, opacity: 0.4,
    blending: THREE.AdditiveBlending, depthWrite: false, sizeAttenuation: true
  });
  const corona = new THREE.Points(coronaGeo, coronaMat);
  corona.renderOrder = 0;
  group.add(corona);
  group.userData.corona = corona;
  group.userData.glow = glow;
  group.userData.mesh = sunMesh;
  scene.add(group);
  return group;
}
function createGlowTexture() {
  const size = 256;
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = size;
  const ctx = canvas.getContext('2d');
  const grad = ctx.createRadialGradient(size/2,size/2,0,size/2,size/2,size/2);
  grad.addColorStop(0, 'rgba(255,255,255,1)');
  grad.addColorStop(0.2, 'rgba(255,230,100,0.8)');
  grad.addColorStop(0.5, 'rgba(255,180,0,0.4)');
  grad.addColorStop(1, 'rgba(255,100,0,0)');
  ctx.fillStyle = grad;
  ctx.fillRect(0,0,size,size);
  return new THREE.CanvasTexture(canvas);
}
const sun = createSun();

// Point light from sun
const sunLight = new THREE.PointLight(0xffffee, 2.5, 300, 2);
sunLight.position.set(0,0,0);
sunLight.castShadow = false;
scene.add(sunLight);

// Ambient for dark side
const ambient = new THREE.AmbientLight(0x222233, 0.3);
scene.add(ambient);

// ============ PLANETS ============
const planets = [];
const orbits = [];

function createPlanet(data) {
  const group = new THREE.Group();
  const geo = new THREE.SphereGeometry(data.size, 64, 64);
  const tex = generateTexture(data.texture);
  const mat = new THREE.MeshStandardMaterial({
    map: tex,
    roughness: 0.8,
    metalness: 0.1
  });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  mesh.rotation.y = Math.random() * Math.PI * 2;
  if (data.tilt) group.rotation.z = data.tilt;
  group.add(mesh);
  group.userData = { ...data, mesh, angle: Math.random() * Math.PI * 2 };

  // Rings for Saturn
  if (data.hasRings) {
    const ringGeo = new THREE.RingGeometry(data.size * 1.2, data.size * 2.2, 128);
    ringGeo.rotateX(-Math.PI/2);
    const ringTex = createRingTexture();
    const ringMat = new THREE.MeshBasicMaterial({
      map: ringTex, transparent: true, opacity: 0.7, side: THREE.DoubleSide, depthWrite: false
    });
    const ring = new THREE.Mesh(ringGeo, ringMat);
    if (data.tilt) ring.rotation.x = data.tilt;
    group.add(ring);
    group.userData.ring = ring;
  }

  // Moons
  data.moons.forEach(m => {
    const mGroup = new THREE.Group();
    const mGeo = new THREE.SphereGeometry(m.size, 32, 32);
    const mTex = generateTexture(m.texture);
    const mMat = new THREE.MeshStandardMaterial({ map: mTex, roughness: 0.9 });
    const mMesh = new THREE.Mesh(mGeo, mMat);
    mMesh.castShadow = true;
    mGroup.add(mMesh);
    mGroup.userData = { ...m, mesh: mMesh, angle: Math.random()*Math.PI*2 };
    group.add(mGroup);
    if (!group.userData.moons) group.userData.moons = [];
    group.userData.moons.push(mGroup);
  });

  // Orbit line
  const orbitGeo = new THREE.RingGeometry(data.distance - 0.05, data.distance + 0.05, 128);
  orbitGeo.rotateX(-Math.PI/2);
  const orbitMat = new THREE.MeshBasicMaterial({ color: 0x444466, side: THREE.DoubleSide, transparent: true, opacity: 0.15, depthWrite: false });
  const orbit = new THREE.Mesh(orbitGeo, orbitMat);
  orbit.renderOrder = -1;
  scene.add(orbit);
  orbits.push(orbit);

  scene.add(group);
  return group;
}
function createRingTexture() {
  const canvas = document.createElement('canvas');
  canvas.width = 512; canvas.height = 512;
  const ctx = canvas.getContext('2d');
  const img = ctx.createImageData(512,512);
  const d = img.data;
  for(let y=0;y<512;y++) for(let x=0;x<512;x++) {
    const i=(y*512+x)*4;
    const dx=x-256, dy=y-256;
    const r=Math.sqrt(dx*dx+dy*dy);
    if(r>120 && r<250) {
      const n = noise(x/30,y/30,0)*0.5+0.5;
      const a = Math.floor(n*200) * Math.max(0, 1 - (r-120)/130);
      d[i]=200; d[i+1]=190; d[i+2]=170; d[i+3]=a;
    } else { d[i+3]=0; }
  }
  ctx.putImageData(img,0,0);
  return new THREE.CanvasTexture(canvas);
}

PLANET_DATA.forEach(d => planets.push(createPlanet(d)));

// ============ CAMERA TOUR ============
let tourIndex = 0;
let tourStartTime = 0;
let tourPaused = false;
let currentTarget = null;
let currentOffset = new THREE.Vector3();

function getTargetObject(name) {
  if (name === 'sun') return sun;
  return planets.find(p => p.userData.name === name);
}

function startTour() {
  tourIndex = 0;
  tourStartTime = performance.now() / 1000;
}
startTour();

function updateCameraTour(time) {
  if (tourPaused) return;
  const step = TOUR_SCHEDULE[tourIndex];
  if (!step) return;
  const targetObj = getTargetObject(step.target);
  if (!targetObj) return;

  const elapsed = time - tourStartTime;
  const totalStepTime = step.duration + step.hold;
  const progress = Math.min(elapsed / totalStepTime, 1);

  // Compute target position
  let targetPos, lookAtPos;
  if (step.target === 'sun') {
    targetPos = new THREE.Vector3().copy(step.offset);
    lookAtPos = new THREE.Vector3(0,0,0);
  } else {
    // Planet position at current time
    const angle = targetObj.userData.angle; // already updated in animate
    targetObj.getWorldPosition(lookAtPos);
    targetPos = lookAtPos.clone().add(step.offset.clone().applyAxisAngle(new THREE.Vector3(0,1,0), angle));
  }

  if (progress < step.duration / totalStepTime) {
    // Traveling
    const t = progress / (step.duration / totalStepTime);
    const eased = easeInOutCubic(t);
    camera.position.lerp(targetPos, eased);
    camera.lookAt(lookAtPos);
    labelEl.classList.remove('visible');
  } else {
    // Holding
    camera.position.lerp(targetPos, 0.05);
    camera.lookAt(lookAtPos);
    labelEl.classList.add('visible');
    labelName.textContent = step.target;
    labelDetail.textContent = getPlanetDetail(step.target);
  }

  if (progress >= 1) {
    tourIndex = (tourIndex + 1) % TOUR_SCHEDULE.length;
    tourStartTime = time;
  }
}
function easeInOutCubic(t){return t<0.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;}
function getPlanetDetail(name) {
  if (name === 'sun') return 'Sol • G2V Star • 1.989 × 10³⁰ kg';
  const p = PLANET_DATA.find(d => d.name === name);
  if (!p) return '';
  const facts = {
    Mercury: '0.39 AU • 88 days • No atmosphere',
    Venus: '0.72 AU • 225 days • Runaway greenhouse',
    Earth: '1 AU • 365 days • Life bearing',
    Mars: '1.52 AU • 687 days • Red planet',
    Jupiter: '5.2 AU • 12 years • Gas giant',
    Saturn: '9.5 AU • 29 years • Ring system',
    Uranus: '19.2 AU • 84 years • Ice giant (tilted)',
    Neptune: '30 AU • 165 years • Windiest planet'
  };
  return facts[name] || '';
}

// ============ ANIMATION ============
let lastTime = 0;
function animate(timestamp) {
  const time = timestamp / 1000;
  const dt = time - lastTime;
  lastTime = time;

  // Update planets
  planets.forEach(p => {
    const d = p.userData;
    d.angle += d.orbitSpeed * dt * 0.02; // scaled for visual
    p.position.x = Math.cos(d.angle) * d.distance;
    p.position.z = Math.sin(d.angle) * d.distance;
    p.rotation.y += d.rotationSpeed * dt;
    d.mesh.rotation.y += d.rotationSpeed * dt;

    // Moons
    if (d.moons) {
      d.moons.forEach(m => {
        m.userData.angle += m.orbitSpeed * dt * 0.1;
        m.position.x = Math.cos(m.userData.angle) * m.distance;
        m.position.z = Math.sin(m.userData.angle) * m.distance;
        m.rotation.y += m.rotationSpeed * dt;
      });
    }
  });

  // Sun corona animation
  const corona = sun.userData.corona;
  if (corona) {
    const pos = corona.geometry.attributes.position.array;
    const speed = corona.geometry.attributes.speed.array;
    for (let i=0;i<pos.length;i+=3) {
      // subtle radial pulsation
      const r = Math.sqrt(pos[i]*pos[i]+pos[i+1]*pos[i+1]+pos[i+2]*pos[i+2]);
      const dirX = pos[i]/r, dirY = pos[i+1]/r, dirZ = pos[i+2]/r;
      pos[i] += dirX * speed[i/3] * dt * 50;
      pos[i+1] += dirY * speed[i/3] * dt * 50;
      pos[i+2] += dirZ * speed[i/3] * dt * 50;
      const newR = Math.sqrt(pos[i]*pos[i]+pos[i+1]*pos[i+1]+pos[i+2]*pos[i+2]);
      if (newR > 10 || newR < 6.5) {
        // reset
        const theta = Math.random()*Math.PI*2;
        const phi = Math.acos(2*Math.random()-1);
        const nr = 6.5 + Math.random()*4;
        pos[i] = nr * Math.sin(phi) * Math.cos(theta);
        pos[i+1] = nr * Math.sin(phi) * Math.sin(theta);
        pos[i+2] = nr * Math.cos(phi);
      }
    }
    corona.geometry.attributes.position.needsUpdate = true;
  }

  // Sun glow pulse
  const glow = sun.userData.glow;
  if (glow) {
    const s = 28 + Math.sin(time*0.5)*2;
    glow.scale.set(s,s,s);
    glow.material.opacity = 0.5 + Math.sin(time*0.7)*0.1;
  }

  // Starfield slow rotation
  starfield.rotation.y += dt * 0.0001;
  starfield.rotation.x += dt * 0.00005;

  // Camera tour
  updateCameraTour(time);

  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}
requestAnimationFrame(animate);

// ============ RESIZE ============
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

// ============ INTERACTION (optional pause) ============
window.addEventListener('keydown', e => {
  if (e.code === 'Space') { tourPaused = !tourPaused; }
  if (e.code === 'ArrowRight') { tourIndex = (tourIndex+1)%TOUR_SCHEDULE.length; tourStartTime = performance.now()/1000; }
  if (e.code === 'ArrowLeft') { tourIndex = (tourIndex-1+TOUR_SCHEDULE.length)%TOUR_SCHEDULE.length; tourStartTime = performance.now()/1000; }
});

</script>
</body>
</html>