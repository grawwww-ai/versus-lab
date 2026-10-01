```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>Turbo Circuit</title>
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; width: 100%; height: 100%; overflow: hidden; background: #78b9d8; font-family: system-ui, -apple-system, Segoe UI, sans-serif; color: white; }
  canvas { display: block; }
  #hud { position: fixed; inset: 0; pointer-events: none; text-shadow: 0 2px 5px #15263ac9; }
  #brand { position: absolute; left: 22px; top: 16px; font-weight: 1000; font-style: italic; font-size: clamp(20px,3vw,34px); letter-spacing: 1px; }
  #brand span { color: #ffe23e; }
  #status { margin-top: 3px; font-size: 11px; letter-spacing: 1.5px; font-weight: 800; color: #d6f6ff; }
  #standings { position: absolute; top: 20px; right: 20px; width: 205px; padding: 12px; border: 1px solid #ffffff42; border-radius: 12px; background: #071626bb; backdrop-filter: blur(8px); }
  #standings h2 { margin: 0 0 8px; font-size: 12px; letter-spacing: 1.8px; color: #ffe23e; }
  .row { display: flex; align-items: center; gap: 8px; padding: 4px 0; font-weight: 800; font-size: 13px; }
  .row .rank { width: 22px; color: #a9c6d4; }
  .row .swatch { width: 9px; height: 9px; border-radius: 50%; }
  .row .name { flex: 1; }
  .row.player { color: #ffe23e; }
  #raceInfo { position: absolute; bottom: 20px; left: 22px; padding: 11px 16px; border-radius: 12px; background: #071626c9; border: 1px solid #ffffff40; min-width: 145px; }
  #lap { font-size: 22px; line-height: 1.1; font-weight: 1000; }
  #lap small { font-size: 12px; color: #c7dce7; }
  #speed { margin-top: 5px; color: #ffe23e; font-size: 12px; font-weight: 900; letter-spacing: 1px; }
  #help { position: absolute; left: 50%; transform: translateX(-50%); bottom: 18px; padding: 8px 13px; border-radius: 9px; background: #071626a8; color: #e6f4fa; font-size: 11px; text-align: center; white-space: nowrap; }
  kbd { display: inline-block; min-width: 21px; padding: 2px 5px; margin: 0 1px; border-radius: 4px; background: #ffffff22; border: 1px solid #ffffff52; color: white; font: 700 10px system-ui; }
  #countdown { position: absolute; left: 50%; top: 43%; transform: translate(-50%,-50%); font-size: clamp(60px,13vw,150px); font-weight: 1000; font-style: italic; color: #ffe23e; -webkit-text-stroke: 2px #fff; filter: drop-shadow(0 8px 8px #09121c88); }
  #cameraTag { position: absolute; right: 22px; bottom: 22px; font-size: 10px; letter-spacing: 1.4px; color: #d5eaf5; }
  #map { position:absolute; bottom: 85px; right: 20px; width: 140px; height: 105px; border-radius: 10px; background:#071626a8; border:1px solid #ffffff42; }
  #intro { position: fixed; left: 50%; top: 50%; transform: translate(-50%,-50%); width: min(470px, calc(100vw - 32px)); padding: 20px 22px; border-radius: 16px; background: #071626e8; border: 1px solid #ffffff55; text-align:center; box-shadow: 0 16px 55px #06111c80; pointer-events:none; transition: opacity .5s; }
  #intro h1 { margin: 0 0 5px; font-size: 25px; font-style: italic; color:#ffe23e; }
  #intro p { margin: 6px 0; color:#d6e9f1; font-size:13px; line-height:1.5; }
  #intro .go { margin-top: 11px; color:#fff; font-size:11px; letter-spacing:1.5px; font-weight:900; }
  @media (max-width:650px) {
    #standings { top: 12px; right: 10px; width: 160px; padding: 8px; }
    .row { font-size: 11px; padding: 3px 0; }
    #brand { left: 12px; top: 12px; }
    #help { bottom: 8px; font-size: 9px; }
    #raceInfo { left: 10px; bottom: 42px; }
    #map { width: 105px; height: 78px; right: 10px; bottom: 80px; }
  }
</style>
</head>
<body>
<div id="hud">
  <div id="brand">TURBO <span>CIRCUIT</span><div id="status">DEMO MODE · PRESS P TO TOGGLE</div></div>
  <div id="standings"><h2>RACE POSITIONS</h2><div id="list"></div></div>
  <div id="raceInfo"><div id="lap">LAP 1 <small>/ 2</small></div><div id="speed">0 km/h</div></div>
  <div id="help"><kbd>↑</kbd> ACCELERATE &nbsp; <kbd>↓</kbd> BRAKE &nbsp; <kbd>←</kbd><kbd>→</kbd> STEER &nbsp; <kbd>P</kbd> AUTOPILOT</div>
  <canvas id="map" width="280" height="210"></canvas>
  <div id="cameraTag">CHASE CAM</div>
  <div id="countdown">3</div>
</div>
<div id="intro">
  <h1>READY, RACER?</h1>
  <p>Arrow keys drive your kart. The race begins after the countdown and runs for at least two laps.</p>
  <p><b>P</b> toggles the autoplay demo. Press any driving key to take control immediately.</p>
  <div class="go">3 · 2 · 1 · GO!</div>
</div>

<script type="module">
import * as THREE from 'three';

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x86c9e8);
scene.fog = new THREE.Fog(0x86c9e8, 160, 430);

const camera = new THREE.PerspectiveCamera(62, innerWidth / innerHeight, 0.1, 700);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.8));
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.insertBefore(renderer.domElement, document.body.firstChild);

scene.add(new THREE.HemisphereLight(0xe5f8ff, 0x49644a, 2.15));
const sun = new THREE.DirectionalLight(0xfff2d6, 3.2);
sun.position.set(-90, 145, 65);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.camera.left = -160; sun.shadow.camera.right = 160;
sun.shadow.camera.top = 160; sun.shadow.camera.bottom = -160;
scene.add(sun);

const mat = (color, roughness=0.85) => new THREE.MeshStandardMaterial({ color, roughness });
const grassMat = mat(0x54a944), roadMat = new THREE.MeshStandardMaterial({ color:0x343a42, roughness:0.95, side:THREE.DoubleSide });
const whiteMat = mat(0xf2f0e6), redMat = mat(0xe83d36), darkMat = mat(0x25313b), tireMat = mat(0x171b20);
const ground = new THREE.Mesh(new THREE.PlaneGeometry(1000,1000), grassMat);
ground.rotation.x = -Math.PI/2; ground.position.y = -2; ground.receiveShadow = true; scene.add(ground);

// A smooth, hilly, closed circuit sampled by arc length.
const control = [
  [0,1,-100],[38,3,-91],[72,1,-66],[91,0,-27],[89,4,20],
  [68,8,61],[35,5,78],[5,1,62],[-21,0,84],[-58,5,76],
  [-87,2,47],[-94,0,5],[-77,5,-37],[-48,8,-72],[-18,4,-93]
].map(v => new THREE.Vector3(v[0],v[1],v[2]));
const curve = new THREE.CatmullRomCurve3(control, true, 'centripetal');
const N = 1500, trackWidth = 15.5;
const samples = [];
for (let i=0;i<N;i++) {
  const u=i/N, p=curve.getPointAt(u), t=curve.getTangentAt(u);
  t.y=0; t.normalize();
  samples.push({p,t});
}
function sampleAt(progress) {
  const u=((progress%1)+1)%1*N, i=Math.floor(u), f=u-i;
  const a=samples[i], b=samples[(i+1)%N];
  const p=a.p.clone().lerp(b.p,f);
  const t=a.t.clone().lerp(b.t,f).normalize();
  return {p,t,right:new THREE.Vector3(t.z,0,-t.x)};
}
function ribbonGeometry(halfWidth, yOffset=0) {
  const positions=[], indices=[];
  for(let i=0;i<N;i++) {
    const s=samples[i], right=new THREE.Vector3(s.t.z,0,-s.t.x);
    const l=s.p.clone().addScaledVector(right,-halfWidth); l.y+=yOffset;
    const r=s.p.clone().addScaledVector(right, halfWidth); r.y+=yOffset;
    positions.push(l.x,l.y,l.z,r.x,r.y,r.z);
    const j=i*2, k=((i+1)%N)*2;
    indices.push(j,k,j+1,j+1,k,k+1);
  }
  const g=new THREE.BufferGeometry();
  g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
  g.setIndex(indices); g.computeVertexNormals(); return g;
}
const road = new THREE.Mesh(ribbonGeometry(trackWidth/2,0.05),roadMat);
road.receiveShadow=true; road.castShadow=false; scene.add(road);

// Red-and-white kerb strips, built as alternating colored ribbon blocks.
function makeKerbs(side) {
  const positions=[], colors=[], indices=[];
  const red=new THREE.Color(0xe83c35), white=new THREE.Color(0xf4f0df);
  for(let i=0;i<N;i++) {
    const s=samples[i], r=new THREE.Vector3(s.t.z,0,-s.t.x);
    const inner=s.p.clone().addScaledVector(r,side*(trackWidth/2-0.25));
    const outer=s.p.clone().addScaledVector(r,side*(trackWidth/2+1.25));
    inner.y+=0.16; outer.y+=0.16;
    positions.push(inner.x,inner.y,inner.z,outer.x,outer.y,outer.z);
  }
  for(let i=0;i<N;i++) {
    const j=i*2,k=((i+1)%N)*2;
    indices.push(j,k,j+1,j+1,k,k+1);
    const c=Math.floor(i/11)%2?white:red;
    for(let v=0;v<2;v++) colors.push(c.r,c.g,c.b);
  }
  const g=new THREE.BufferGeometry();
  g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
  g.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));
  g.setIndex(indices); g.computeVertexNormals();
  const m=new THREE.Mesh(g,new THREE.MeshStandardMaterial({vertexColors:true,roughness:.8,side:THREE.DoubleSide}));
  m.receiveShadow=true; scene.add(m);
}
makeKerbs(-1); makeKerbs(1);

// Painted edge lines.
for (const side of [-1,1]) {
  const pts=[];
  for(let i=0;i<N;i++) {
    const s=samples[i], r=new THREE.Vector3(s.t.z,0,-s.t.x);
    const p=s.p.clone().addScaledVector(r,side*(trackWidth/2-0.48)); p.y+=0.18; pts.push(p);
  }
  const line=new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(pts),new THREE.LineBasicMaterial({color:0xffffff}));
  scene.add(line);
}

// Start/finish checker tiles and a simple starting gantry.
{
  const s=sampleAt(0), yaw=Math.atan2(s.t.x,s.t.z);
  const tileW=trackWidth/12, tileD=1.25;
  for(let row=0;row<2;row++) for(let col=0;col<12;col++) {
    const m=new THREE.Mesh(new THREE.BoxGeometry(tileW,0.045,tileD),((row+col)%2)?whiteMat:darkMat);
    const lateral=-trackWidth/2+tileW*(col+.5);
    const pos=s.p.clone().addScaledVector(s.right,lateral);
    pos.y+=0.2; pos.addScaledVector(s.t,(row-.5)*tileD);
    m.position.copy(pos); m.rotation.y=yaw; scene.add(m);
  }
  const postMat=mat(0xf3d33e), signMat=mat(0x183653);
  for(const side of [-1,1]) {
    const pos=s.p.clone().addScaledVector(s.right,side*10); pos.y+=3.5;
    const post=new THREE.Mesh(new THREE.BoxGeometry(.8,7,.8),postMat);
    post.position.copy(pos); post.castShadow=true; scene.add(post);
  }
  const beam=new THREE.Mesh(new THREE.BoxGeometry(21,1.5,1.2),signMat);
  beam.position.copy(s.p); beam.position.y+=7; beam.rotation.y=yaw; beam.castShadow=true; scene.add(beam);
  const sign=new THREE.Mesh(new THREE.BoxGeometry(11,.15,.3),mat(0xffe23e));
  sign.position.copy(s.p); sign.position.y+=7.82; sign.rotation.y=yaw; scene.add(sign);
}

// Scenic low-poly trees, banners, barriers and distant hills.
let seed=13917;
function rand(){seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;}
function tree(x,y,z,scale=1) {
  const g=new THREE.Group(); g.position.set(x,y,z); g.scale.setScalar(scale);
  const trunk=new THREE.Mesh(new THREE.CylinderGeometry(.2,.3,2.2,6),mat(0x79512c));
  trunk.position.y=1.1; trunk.castShadow=true; g.add(trunk);
  const colors=[0x267c45,0x328b48,0x559d45];
  for(let i=0;i<3;i++){
    const crown=new THREE.Mesh(new THREE.ConeGeometry(1.35-i*.13,2.4,7),mat(colors[i]));
    crown.position.y=2.4+i*1.12; crown.castShadow=true; g.add(crown);
  }
  scene.add(g);
}
for(let i=0;i<145;i++){
  const u=rand(), s=sampleAt(u), side=rand()<.5?-1:1, d=13+rand()*34;
  const pos=s.p.clone().addScaledVector(s.right,side*d);
  tree(pos.x, pos.y-0.3, pos.z, .75+rand()*.9);
}
const bannerColors=[0x39c6e5,0xffd938,0xef4d4d,0x9a61dc];
for(let i=0;i<30;i++){
  const u=i/30, s=sampleAt(u), side=i%2?1:-1;
  const pos=s.p.clone().addScaledVector(s.right,side*11.3); pos.y+=2.1;
  const pole=new THREE.Mesh(new THREE.CylinderGeometry(.07,.09,4.2,6),whiteMat);
  pole.position.copy(pos); pole.castShadow=true; scene.add(pole);
  const flag=new THREE.Mesh(new THREE.PlaneGeometry(2.1,1.15),mat(bannerColors[i%bannerColors.length]));
  flag.position.set(pos.x+0.85,pos.y+1.25,pos.z); flag.rotation.y=Math.atan2(s.t.x,s.t.z); scene.add(flag);
}
// Faraway soft hills.
for(let i=0;i<34;i++){
  const a=rand()*Math.PI*2, d=205+rand()*90, r=18+rand()*31;
  const h=new THREE.Mesh(new THREE.SphereGeometry(1,12,8),mat(i%3===0?0x6caa75:0x79b879));
  h.position.set(Math.cos(a)*d,-8,Math.sin(a)*d); h.scale.set(r,r*.65,r*1.2); scene.add(h);
}

// Kart constructor.
const kartColors=[0xe83c35,0x2585ee,0xffcf28,0x7c45d8,0x20b878,0xff7c24];
const names=['MARIO','LUIGI','PEACH','WARIO','YOSHI','TOAD'];
const racers=[];
function createKart(index) {
  const color=kartColors[index], group=new THREE.Group();
  const paint=mat(color,.48), white=mat(0xf8f1dc), glass=mat(0x8ed8ea,.35);
  const chassis=new THREE.Mesh(new THREE.BoxGeometry(1.75,.5,2.65),paint);
  chassis.position.y=.72; chassis.castShadow=true; group.add(chassis);
  const nose=new THREE.Mesh(new THREE.BoxGeometry(1.42,.24,.68),white);
  nose.position.set(0,.94,1.22); nose.castShadow=true; group.add(nose);
  const cockpit=new THREE.Mesh(new THREE.BoxGeometry(1.22,.58,1.05),paint);
  cockpit.position.set(0,1.16,-.08); cockpit.castShadow=true; group.add(cockpit);
  const windshield=new THREE.Mesh(new THREE.BoxGeometry(1.1,.36,.12),glass);
  windshield.position.set(0,1.3,.49); windshield.rotation.x=-.2; group.add(windshield);
  const spoiler=new THREE.Mesh(new THREE.BoxGeometry(1.9,.14,.38),darkMat);
  spoiler.position.set(0,1.22,-1.22); group.add(spoiler);
  const driver=new THREE.Group();
  const body=new THREE.Mesh(new THREE.CylinderGeometry(.25,.32,.7,8),mat(color));
  body.position.y=1.37; driver.add(body);
  const head=new THREE.Mesh(new THREE.SphereGeometry(.34,12,10),mat(index===2?0xffd1a4:0xffc99d));
  head.position.set(0,1.88,.05); head.castShadow=true; driver.add(head);
  const helmet=new THREE.Mesh(new THREE.SphereGeometry(.37,12,8,0,Math.PI*2,0,Math.PI*.55),mat([0xf33d35,0x24a2ed,0xffcf28,0x5428a8,0x50ba45,0xf6f0de][index]));
  helmet.position.set(0,2.0,.02); driver.add(helmet);
  const visor=new THREE.Mesh(new THREE.BoxGeometry(.48,.13,.12),darkMat);
  visor.position.set(0,1.94,.34); driver.add(visor);
  group.add(driver);
  const wheels=[];
  for(const x of [-.98,.98]) for(const z of [-.82,.84]) {
    const pivot=new THREE.Group(); pivot.position.set(x,.49,z); group.add(pivot);
    const wheel=new THREE.Mesh(new THREE.CylinderGeometry(.37,.37,.25,12),tireMat);
    wheel.rotation.z=Math.PI/2; wheel.castShadow=true; pivot.add(wheel);
    const hub=new THREE.Mesh(new THREE.CylinderGeometry(.16,.16,.27,10),index%2?white:paint);
    hub.rotation.z=Math.PI/2; pivot.add(hub);
    wheels.push({pivot,wheel,front:z>0});
  }
  group.traverse(o=>{if(o.isMesh)o.castShadow=true;});
  scene.add(group);
  return {index,name:names[index],group,wheels,progress:-index*.006,lat:(index%2?1:-1)*1.8,
    speed:0,steer:0,drift:0,base:.052+index*.00065,aiLane:(index%3-1)*1.5,lap:0};
}
for(let i=0;i<6;i++) racers.push(createKart(i));
racers[0].lat=0;

const particleMat=new THREE.MeshBasicMaterial({color:0xc8c7b8,transparent:true,opacity:.62});
const particles=[];
for(let i=0;i<130;i++){
  const mesh=new THREE.Mesh(new THREE.SphereGeometry(.11+rand()*.08,5,4),particleMat.clone());
  mesh.visible=false; scene.add(mesh);
  particles.push({mesh,vel:new THREE.Vector3(),life:0});
}
let particleCursor=0;
function puff(pos,skid=false){
  const q=particles[particleCursor++%particles.length];
  q.mesh.visible=true; q.mesh.position.copy(pos); q.mesh.scale.setScalar(skid?.65:1);
  q.vel.set((rand()-.5)*1.3,skid?.15:.45+rand()*.45,(rand()-.5)*1.3);
  q.life=skid?.45:.8+rand()*.4;
}

const keys={};
let demo=true, elapsed=0, raceStarted=false, last=performance.now(), standings=[];
const intro=document.getElementById('intro'), countdown=document.getElementById('countdown');
const statusEl=document.getElementById('status'), listEl=document.getElementById('list');
const lapEl=document.getElementById('lap'), speedEl=document.getElementById('speed');
const cameraTag=document.getElementById('cameraTag');
function drivingKey(code){return ['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','KeyW','KeyA','KeyS','KeyD'].includes(code);}
addEventListener('keydown',e=>{
  if(drivingKey(e.code)){
    e.preventDefault(); keys[e.code]=true;
    if(demo){demo=false;statusEl.textContent='MANUAL DRIVE · P FOR AUTOPILOT';}
  } else if(e.code==='KeyP'&&!e.repeat){
    demo=!demo; statusEl.textContent=demo?'DEMO MODE · PRESS P TO TOGGLE':'MANUAL DRIVE · P FOR AUTOPILOT';
  }
});
addEventListener('keyup',e=>{keys[e.code]=false;});
addEventListener('blur',()=>{for(const k in keys)keys[k]=false;});
addEventListener('resize',()=>{
  camera.aspect=innerWidth/innerHeight; camera.updateProjectionMatrix();
  renderer.setSize(innerWidth,innerHeight);
});

function getTurn(progress){
  const i=Math.floor((((progress%1)+1)%1)*N);
  const a=samples[(i-2+N)%N].t,b=samples[(i+2)%N].t;
  const cross=a.z*b.x-a.x*b.z;
  const dot=THREE.MathUtils.clamp(a.dot(b),-1,1);
  return Math.atan2(cross,dot)*N/4;
}
function rankRacers(){return [...racers].sort((a,b)=>b.progress-a.progress);}
function placeKart(r,dt){
  const s=sampleAt(r.progress), pos=s.p.clone().addScaledVector(s.right,r.lat);
  pos.y+=.32;
  const yaw=Math.atan2(s.t.x,s.t.z);
  r.drift=THREE.MathUtils.damp(r.drift,r.steer*Math.min(1,r.speed*18),5,dt);
  r.group.position.copy(pos);
  r.group.rotation.set(0,yaw+r.drift*.19,0);
  for(const w of r.wheels){
    w.pivot.rotation.y=w.front?r.steer*.38:0;
    w.wheel.rotation.x-=r.speed*34*dt;
  }
  if(Math.abs(r.drift)>.26&&Math.random()<dt*17){
    const rear=pos.clone().addScaledVector(s.t,-1.2).addScaledVector(s.right,(Math.random()-.5)*1.6);
    rear.y=.17; puff(rear,true);
  } else if(r.speed>.035&&Math.random()<dt*2.5){
    const rear=pos.clone().addScaledVector(s.t,-1.45); rear.y=.18; puff(rear,false);
  }
}
function updateRacer(r,dt){
  const turn=getTurn(r.progress), curveSlow=1-Math.min(.2,Math.abs(turn)*.026);
  if(r.index!==0){
    // AI follows a bend-aware line and varies pace to create believable overtakes.
    const weave=Math.sin(elapsed*.43+r.index*2.1)*.9;
    const desired=THREE.MathUtils.clamp(r.aiLane+weave-turn*.42,-4.5,4.5);
    r.lat=THREE.MathUtils.damp(r.lat,desired,1.8,dt);
    r.steer=THREE.MathUtils.clamp((desired-r.lat)*.4,-.7,.7);
    const pace=r.base*curveSlow*(1+.055*Math.sin(elapsed*.38+r.index*1.7));
    r.speed=pace;
  } else {
    const up=keys.ArrowUp||keys.KeyW, down=keys.ArrowDown||keys.KeyS;
    const left=keys.ArrowLeft||keys.KeyA, right=keys.ArrowRight||keys.KeyD;
    if(demo){
      const desired=THREE.MathUtils.clamp(-turn*.48+Math.sin(elapsed*.33)*.45,-3.6,3.6);
      r.steer=THREE.MathUtils.clamp((desired-r.lat)*.72,-.75,.75);
      r.lat=THREE.MathUtils.damp(r.lat,desired,2.3,dt);
      r.speed=THREE.MathUtils.damp(r.speed,r.base*1.04*curveSlow,1.9,dt);
    } else {
      r.steer=THREE.MathUtils.damp(r.steer,(left?-1:0)+(right?1:0),9,dt);
      r.lat+=r.steer*5.4*dt;
      r.lat=THREE.MathUtils.clamp(r.lat,-5.7,5.7);
      const target=down?.012:(up?.066:.038);
      r.speed=THREE.MathUtils.damp(r.speed,target*curveSlow,up?2.1:down?5:1.0,dt);
    }
  }
  r.progress+=r.speed*dt;
  placeKart(r,dt);
}
function drawMap(){
  const c=document.getElementById('map'),ctx=c.getContext('2d');
  ctx.clearRect(0,0,c.width,c.height);
  const points=samples;
  let minX=Infinity,maxX=-Infinity,minZ=Infinity,maxZ=-Infinity;
  for(const s of points){minX=Math.min(minX,s.p.x);maxX=Math.max(maxX,s.p.x);minZ=Math.min(minZ,s.p.z);maxZ=Math.max(maxZ,s.p.z);}
  const scale=Math.min((c.width-40)/(maxX-minX),(c.height-36)/(maxZ-minZ));
  const ox=(c.width-(maxX-minX)*scale)/2, oz=(c.height-(maxZ-minZ)*scale)/2;
  const xy=p=>[ox+(p.x-minX)*scale, c.height-(oz+(p.z-minZ)*scale)];
  ctx.beginPath();
  points.forEach((s,i)=>{const [x,y]=xy(s.p);if(!i)ctx.moveTo(x,y);else ctx.lineTo(x,y);});
  ctx.closePath();ctx.lineWidth=13;ctx.strokeStyle='#d2d4cc';ctx.stroke();
  ctx.lineWidth=8;ctx.strokeStyle='#373d45';ctx.stroke();
  for(const r of racers){
    const s=sampleAt(r.progress), [x,y]=xy(s.p);
    ctx.beginPath();ctx.arc(x,y,r.index===0?6:4,0,Math.PI*2);
    ctx.fillStyle='#'+kartColors[r.index].toString(16).padStart(6,'0');ctx.fill();
    if(r.index===0){ctx.strokeStyle='#fff';ctx.lineWidth=2;ctx.stroke();}
  }
}
function updateHUD(){
  standings=rankRacers();
  listEl.innerHTML=standings.map((r,i)=>`<div class="row ${r.index===0?'player':''}"><span class="rank">${i+1}${i===0?'ST':i===1?'ND':i===2?'RD':'TH'}</span><span class="swatch" style="background:#${kartColors[r.index].toString(16).padStart(6,'0')}"></span><span class="name">${r.name}${r.index===0?' · YOU':''}</span></div>`).join('');
  const completed=Math.max(0,Math.floor(racers[0].progress));
  lapEl.innerHTML=`LAP ${Math.min(completed+1,99)} <small>/ 2</small>`;
  speedEl.textContent=`${Math.round(racers[0].speed*2100)} km/h`;
  statusEl.textContent=demo?'DEMO MODE · PRESS P TO TOGGLE':'MANUAL DRIVE · P FOR AUTOPILOT';
  drawMap();
}
let camTrackside=false, nextCut=10, cutEnd=0, roadsidePoint=0;
const desiredCam=new THREE.Vector3(), lookTarget=new THREE.Vector3();
function updateCamera(dt){
  const leader=standings[0]||racers[0], s=sampleAt(leader.progress);
  if(elapsed>nextCut){
    camTrackside=true;cutEnd=elapsed+2.25;roadsidePoint=(leader.progress+.12+rand()*.12)%1;
    nextCut=elapsed+10+rand()*5;
  }
  if(camTrackside&&elapsed>cutEnd)camTrackside=false;
  if(camTrackside){
    const q=sampleAt(roadsidePoint), side=q.right;
    desiredCam.copy(q.p).addScaledVector(side,16).add(new THREE.Vector3(0,5,0));
    lookTarget.copy(leader.group.position).add(new THREE.Vector3(0,1,0));
    cameraTag.textContent='TRACKSIDE CAM';
  }else{
    desiredCam.copy(leader.group.position).addScaledVector(s.t,-13).add(new THREE.Vector3(0,6.4,0));
    lookTarget.copy(leader.group.position).addScaledVector(s.t,5).add(new THREE.Vector3(0,1.1,0));
    cameraTag.textContent='CHASE CAM';
  }
  camera.position.lerp(desiredCam,1-Math.exp(-dt*(camTrackside?2.6:3.8)));
  camera.lookAt(lookTarget);
}
function animate(now){
  requestAnimationFrame(animate);
  const dt=Math.min(.04,(now-last)/1000);last=now;elapsed+=dt;
  if(elapsed<3){
    const n=Math.ceil(3-elapsed);
    countdown.textContent=n;
    countdown.style.display='block';
  }else{
    if(!raceStarted){raceStarted=true;countdown.textContent='GO!';intro.style.opacity='0';setTimeout(()=>{countdown.style.display='none';},650);}
    else countdown.style.display='none';
    for(const r of racers) updateRacer(r,dt);
  }
  for(const p of particles){
    if(p.life>0){
      p.life-=dt;p.mesh.position.addScaledVector(p.vel,dt);p.vel.y-=.65*dt;
      p.mesh.material.opacity=Math.max(0,p.life);p.mesh.scale.multiplyScalar(1+dt*.6);
      if(p.life<=0)p.mesh.visible=false;
    }
  }
  updateHUD();updateCamera(dt);
  renderer.render(scene,camera);
}
updateHUD();
requestAnimationFrame(animate);
</script>
</body>
</html>
```