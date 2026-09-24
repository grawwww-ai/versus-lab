```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Kart Grand Prix – Auto Race</title>
<style>
html,body{margin:0;height:100%;overflow:hidden;background:#000;font-family:"Trebuchet MS",Arial,sans-serif}
canvas{display:block}
#hud{position:fixed;inset:0;pointer-events:none;color:#fff;user-select:none}
#lap{position:absolute;top:16px;right:24px;font-size:38px;font-weight:900;font-style:italic;text-shadow:3px 3px 0 #000,-1px -1px 0 #000}
#lap b{color:#ffd600}
#time{position:absolute;top:64px;right:24px;font-size:20px;font-weight:700;text-shadow:2px 2px 0 #000}
#pos{position:absolute;top:16px;left:16px;width:250px;height:240px}
.row{position:absolute;left:0;width:240px;height:33px;transition:top .45s ease,background .3s;display:flex;align-items:center;background:rgba(0,0,0,.5);border-radius:7px;border-left:7px solid #fff;box-sizing:border-box;padding:0 8px;font-weight:800;font-size:17px;text-shadow:1px 1px 0 #000}
.row .r{width:46px;font-style:italic;font-size:20px}
.row .sw{width:15px;height:15px;border-radius:50%;margin-right:8px;border:2px solid #fff}
.row .nm{flex:1}
.row .gap{font-size:13px;opacity:.9}
.row.lead{background:rgba(255,190,0,.6)}
#center{position:absolute;top:40%;left:0;right:0;text-align:center;font-size:160px;font-weight:900;font-style:italic;transform:translateY(-50%);text-shadow:7px 7px 0 #000}
#msg{position:absolute;top:17%;left:0;right:0;text-align:center;font-size:56px;font-weight:900;font-style:italic;color:#ffd600;text-shadow:4px 4px 0 #000;opacity:0;transition:opacity .3s}
#cam{position:absolute;bottom:16px;left:16px;font-size:15px;font-weight:700;background:rgba(0,0,0,.55);padding:6px 12px;border-radius:4px;letter-spacing:1px}
#cam i{color:#ff3b3b;font-style:normal}
#results{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);background:rgba(10,20,60,.85);border:4px solid #ffd600;border-radius:14px;padding:18px 34px;display:none;min-width:320px}
#results h2{margin:0 0 10px;text-align:center;font-style:italic;color:#ffd600;font-size:34px;text-shadow:3px 3px 0 #000}
#results div{font-size:22px;font-weight:800;padding:4px 0;text-shadow:2px 2px 0 #000}
</style>
</head>
<body>
<div id="hud">
  <div id="pos"></div>
  <div id="lap">LAP <b>1</b>/2</div>
  <div id="time">0:00.00</div>
  <div id="center"></div>
  <div id="msg"></div>
  <div id="cam"><i>●</i> LIVE</div>
  <div id="results"></div>
</div>
<script type="module">
import * as THREE from 'three';

// ---------- renderer / scene ----------
const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.setSize(innerWidth,innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0xbfe0ff, 150, 650);
const camera = new THREE.PerspectiveCamera(68, innerWidth/innerHeight, 0.1, 2000);

const hemi = new THREE.HemisphereLight(0xdcefff, 0x5a7a3a, 1.1); scene.add(hemi);
const sun = new THREE.DirectionalLight(0xfff1dc, 2.1);
sun.castShadow = true;
sun.shadow.mapSize.set(2048,2048);
Object.assign(sun.shadow.camera,{left:-70,right:70,top:70,bottom:-70,near:1,far:300});
sun.shadow.bias = -0.0005;
scene.add(sun); scene.add(sun.target);

// sky
const sky = new THREE.Mesh(new THREE.SphereGeometry(1200,32,16), new THREE.ShaderMaterial({
  side:THREE.BackSide, depthWrite:false, fog:false,
  vertexShader:`varying vec3 vW; void main(){ vW=normalize(position); gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,
  fragmentShader:`varying vec3 vW; void main(){ float h=max(vW.y,0.0); vec3 c=mix(vec3(0.75,0.878,1.0),vec3(0.22,0.5,0.95),pow(h,0.55)); gl_FragColor=vec4(c,1.0);}`
}));
scene.add(sky);

const V3 = THREE.Vector3, up = new V3(0,1,0);
const MU = THREE.MathUtils;
function canvasTex(w,h,draw){const c=document.createElement('canvas');c.width=w;c.height=h;const x=c.getContext('2d');draw(x,w,h);const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=8;return t;}
const sc = new THREE.Color();
function srgb(r,g,b){ sc.setRGB(r,g,b,THREE.SRGBColorSpace); return sc; }

// ---------- track ----------
const SC = 0.6, hw = 6.5, LAPS = 2;
const ctrl = [[-30,0,80],[20,0,80],[65,0.5,78],[110,2,58],[128,4,15],[112,7,-35],[70,9,-52],[35,7,-28],[5,4,-12],[-28,4,-40],[-62,6,-78],[-110,4,-72],[-132,1.5,-20],[-118,0,40],[-80,0,76]]
  .map(p=>new V3(p[0]*SC,p[1],p[2]*SC));
const curve = new THREE.CatmullRomCurve3(ctrl,true,'centripetal');
const L = curve.getLength();
const N = 900, ds = L/N;
const P=[],T=[],SD=[],NR=[];
for(let i=0;i<N;i++){
  const u=i/N; const p=curve.getPointAt(u), t=curve.getTangentAt(u).normalize();
  const s=new V3().crossVectors(t,up).normalize(); const n=new V3().crossVectors(s,t).normalize();
  P.push(p);T.push(t);SD.push(s);NR.push(n);
}
const Kraw=[];
for(let i=0;i<N;i++){const a=T[i],b=T[(i+1)%N];const cy=a.z*b.x-a.x*b.z;Kraw.push(-cy/(Math.hypot(a.x,a.z)*Math.hypot(b.x,b.z))/ds);}
const K=[];
for(let i=0;i<N;i++){let s=0;for(let j=-8;j<=8;j++)s+=Kraw[(i+j+N)%N];K.push(s/17);}
const wrap = s=>((s%L)+L)%L;
const idx = s=>Math.floor(wrap(s)/ds)%N;
function newF(){return {p:new V3(),t:new V3(),s:new V3(),n:new V3(),k:0};}
function frameAt(s,o){
  const f=wrap(s)/ds; const i=Math.floor(f)%N, j=(i+1)%N, a=f-Math.floor(f);
  o.p.lerpVectors(P[i],P[j],a); o.t.lerpVectors(T[i],T[j],a).normalize();
  o.s.lerpVectors(SD[i],SD[j],a).normalize(); o.n.lerpVectors(NR[i],NR[j],a).normalize();
  o.k=K[i]*(1-a)+K[j]*a; return o;
}
function curvAvg(s,a,b){let sum=0,c=0;for(let x=a;x<=b;x+=2){sum+=K[idx(s+x)];c++;}return sum/c;}
function curvAbsMax(s,a,b){let m=0;for(let x=a;x<=b;x+=2){m=Math.max(m,Math.abs(K[idx(s+x)]));}return m;}
const centroid=new V3(); P.forEach(p=>centroid.add(p)); centroid.divideScalar(N);
const outSign = SD[0].dot(new V3().subVectors(P[0],centroid))>0?1:-1;

// nearest track / ground
const TS=[]; for(let i=0;i<N;i+=2)TS.push(i);
function nearestTrack(x,z){let best=1e18,bi=0;for(const i of TS){const q=P[i];const dx=q.x-x,dz=q.z-z;const d=dx*dx+dz*dz;if(d<best){best=d;bi=i;}}return {dist:Math.sqrt(best),y:P[bi].y,i:bi};}
function natural(x,z){const r=Math.hypot(x,z);let h=2.5*Math.sin(x*0.031+0.5)*Math.cos(z*0.027)+1.4*Math.sin(x*0.071+z*0.053)+0.8*Math.cos(z*0.11-x*0.04);
  h+=MU.smoothstep(r,140,240)*(24+10*Math.sin(Math.atan2(z,x)*5));return h;}
function groundFrom(x,z,nt){const w=MU.smoothstep(nt.dist,hw+3,hw+28);const base=nt.y-0.12;return base+(natural(x,z)-base)*w;}
function groundHeight(x,z){return groundFrom(x,z,nearestTrack(x,z));}

// terrain
{
  const g=new THREE.PlaneGeometry(540,540,190,190); g.rotateX(-Math.PI/2);
  const pos=g.attributes.position; const cols=[];
  for(let i=0;i<pos.count;i++){
    const x=pos.getX(i), z=pos.getZ(i); const nt=nearestTrack(x,z); const h=groundFrom(x,z,nt);
    pos.setY(i,h);
    const nz=0.85+0.3*(0.5+0.5*Math.sin(x*0.21+Math.cos(z*0.17)*2));
    let c;
    if(h>26) c=srgb(0.95,0.96,1.0);
    else if(h>15) c=srgb(0.45*nz,0.5*nz,0.35*nz);
    else if(nt.dist<hw+5 && Math.abs(K[nt.i])>0.02) c=srgb(0.9,0.8,0.55);
    else if(nt.dist<hw+3.5) c=srgb(0.5,0.75,0.32);
    else c=srgb(0.3*nz,0.62*nz,0.22*nz);
    cols.push(c.r,c.g,c.b);
  }
  g.setAttribute('color',new THREE.Float32BufferAttribute(cols,3));
  g.computeVertexNormals();
  const m=new THREE.Mesh(g,new THREE.MeshLambertMaterial({vertexColors:true}));
  m.receiveShadow=true; scene.add(m);
}

// road
{
  const tex=canvasTex(256,256,(x,w,h)=>{
    x.fillStyle='#5a5a60';x.fillRect(0,0,w,h);
    for(let i=0;i<5000;i++){const v=70+Math.random()*50|0;x.fillStyle=`rgb(${v},${v},${v+4})`;x.fillRect(Math.random()*w,Math.random()*h,2,2);}
    x.fillStyle='#f4f4f4';x.fillRect(5,0,6,h);x.fillRect(w-11,0,6,h);
    x.fillStyle='#e8e8e8';x.fillRect(w/2-3,0,6,h/2);
  });
  tex.wrapS=tex.wrapT=THREE.RepeatWrapping;
  const pos=[],uv=[],ind=[];
  for(let i=0;i<=N;i++){const j=i%N,p=P[j],s=SD[j];
    pos.push(p.x-s.x*hw,p.y,p.z-s.z*hw, p.x+s.x*hw,p.y,p.z+s.z*hw);
    uv.push(0,i*ds/8,1,i*ds/8);
    if(i<N){const a=i*2;ind.push(a,a+1,a+2,a+1,a+3,a+2);}
  }
  const g=new THREE.BufferGeometry();
  g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));
  g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));
  g.setIndex(ind); g.computeVertexNormals();
  const m=new THREE.Mesh(g,new THREE.MeshLambertMaterial({map:tex}));
  m.receiveShadow=true; scene.add(m);

  // kerbs
  const kp=[],kc=[];
  const red=srgb(0.9,0.1,0.1).clone(), white=srgb(0.97,0.97,0.97).clone(), blue=srgb(0.15,0.35,0.9).clone();
  for(let i=0;i<N;i++){const j=(i+1)%N;
    const corner=Math.abs(K[i])>0.01;
    const col=(Math.floor(i*ds/2.2)%2)?white:(corner?red:blue);
    for(const sg of [-1,1]){
      const a=new V3().copy(P[i]).addScaledVector(SD[i],sg*hw), b=new V3().copy(P[i]).addScaledVector(SD[i],sg*(hw+1.3));
      const c=new V3().copy(P[j]).addScaledVector(SD[j],sg*hw), d=new V3().copy(P[j]).addScaledVector(SD[j],sg*(hw+1.3));
      a.y+=0.04;c.y+=0.04;b.y+=0.12;d.y+=0.12;
      for(const v of [a,b,c,b,d,c]){kp.push(v.x,v.y,v.z);kc.push(col.r,col.g,col.b);}
    }
  }
  const kg=new THREE.BufferGeometry();
  kg.setAttribute('position',new THREE.Float32BufferAttribute(kp,3));
  kg.setAttribute('color',new THREE.Float32BufferAttribute(kc,3));
  kg.computeVertexNormals();
  const km=new THREE.Mesh(kg,new THREE.MeshLambertMaterial({vertexColors:true,side:THREE.DoubleSide}));
  km.receiveShadow=true; scene.add(km);

  // start/finish checker
  const ct=canvasTex(128,16,(x,w,h)=>{for(let i=0;i<16;i++)for(let j=0;j<2;j++){x.fillStyle=(i+j)%2?'#111':'#fff';x.fillRect(i*8,j*8,8,8);}});
  const sl=new THREE.Mesh(new THREE.PlaneGeometry(2*hw,1.6).rotateX(-Math.PI/2),new THREE.MeshLambertMaterial({map:ct,polygonOffset:true,polygonOffsetFactor:-2}));
  const f=frameAt(0,newF()); orientBasis(sl,f.p,f.t,f.n); sl.position.y+=0.02; sl.receiveShadow=true; scene.add(sl);
}
function orientBasis(obj,p,t,n){const z=t.clone();const x=new V3().crossVectors(n,z).normalize();const y=new V3().crossVectors(z,x);obj.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(x,y,z));obj.position.copy(p);}

// ---------- scenery ----------
const dummy=new THREE.Object3D();
const lam=c=>new THREE.MeshLambertMaterial({color:c});
const startLights=[];
function makeGantry(s,text,lights,c1,c2){
  const f=frameAt(s,newF()); const g=new THREE.Group();
  const th=new V3(f.t.x,0,f.t.z).normalize(); orientBasis(g,f.p,th,up);
  const X=hw+1.6;
  for(const sg of [-1,1]){
    for(let k=0;k<5;k++){const b=new THREE.Mesh(new THREE.BoxGeometry(0.9,2,0.9),lam(k%2?c2:0xffffff));b.position.set(sg*X,-1+k*2,0);b.castShadow=true;g.add(b);}
  }
  const beam=new THREE.Mesh(new THREE.BoxGeometry(2*X+0.9,1.8,0.7),lam(c1));beam.position.y=8.4;beam.castShadow=true;g.add(beam);
  const tex=canvasTex(1024,128,(x,w,h)=>{
    x.fillStyle='#'+new THREE.Color(c1).getHexString();x.fillRect(0,0,w,h);
    for(let i=0;i<64;i++){x.fillStyle=i%2?'#111':'#fff';x.fillRect(i*16,0,16,12);x.fillRect(i*16+(i%2?-16:0)+16,h-12,16,12);}
    x.font='italic 900 84px Arial';x.textAlign='center';x.textBaseline='middle';
    x.lineWidth=10;x.strokeStyle='#000';x.strokeText(text,w/2,h/2+4);x.fillStyle='#ffe000';x.fillText(text,w/2,h/2+4);
  });
  for(const sg of [-1,1]){const pl=new THREE.Mesh(new THREE.PlaneGeometry(2*X,1.5),new THREE.MeshBasicMaterial({map:tex}));pl.position.set(0,8.4,sg*0.36);if(sg<0)pl.rotation.y=Math.PI;g.add(pl);}
  if(lights){
    const box=new THREE.Mesh(new THREE.BoxGeometry(4.2,1.2,0.5),lam(0x111111));box.position.set(0,6.9,-0.3);g.add(box);
    for(let i=0;i<3;i++){const m=new THREE.Mesh(new THREE.SphereGeometry(0.42,16,12),new THREE.MeshBasicMaterial({color:0x330000}));m.position.set(-1.3+i*1.3,6.9,-0.6);g.add(m);startLights.push(m);}
  }
  scene.add(g); return g;
}
makeGantry(0,'★ KART GRAND PRIX ★',true,0xd32f2f,0xd32f2f);
{let bi=0;for(let i=0;i<N;i++)if(P[i].y>P[bi].y)bi=i;makeGantry(bi*ds,'RAINBOW HILL',false,0x1565c0,0x7b1fa2);}
makeGantry(L*0.84,'MUSHROOM BEND',false,0x2e7d32,0xffa000);

// grandstand
const standF=frameAt(-14,newF());
const standCenter=standF.p.clone().addScaledVector(standF.s,outSign*(hw+13));
let crowd, crowdBase=[];
{
  const g=new THREE.Group(); const th=new V3(standF.t.x,0,standF.t.z).normalize();
  orientBasis(g,standCenter,th,up); g.position.y=groundHeight(standCenter.x,standCenter.z);
  const away=-outSign; const len=44;
  for(let r=0;r<6;r++){
    const b=new THREE.Mesh(new THREE.BoxGeometry(1.7,0.8+r*0.9,len),lam(r%2?0x90a4ae:0xb0bec5));
    b.position.set(away*r*1.7,(0.8+r*0.9)/2-0.5,0);b.castShadow=b.receiveShadow=true;g.add(b);
  }
  const back=new THREE.Mesh(new THREE.BoxGeometry(0.5,9,len),lam(0x37474f));back.position.set(away*10.4,3.5,0);g.add(back);
  const roof=new THREE.Mesh(new THREE.BoxGeometry(12,0.4,len+2),lam(0xd32f2f));roof.position.set(away*5,9.2,0);roof.rotation.z=away*0.12;roof.castShadow=true;g.add(roof);
  for(const zz of [-len/2,0,len/2]){const c=new THREE.Mesh(new THREE.BoxGeometry(0.4,9,0.4),lam(0xeeeeee));c.position.set(away*0.2,4,zz);g.add(c);}
  const n=6*55; crowd=new THREE.InstancedMesh(new THREE.BoxGeometry(0.5,0.75,0.4),lam(0xffffff),n);
  const pal=[0xe53935,0x1e88e5,0xfdd835,0x43a047,0xffffff,0xff7043,0x8e24aa,0x00acc1];
  let k=0;
  for(let r=0;r<6;r++)for(let i=0;i<55;i++){
    const x=away*r*1.7, y=0.8+r*0.9-0.5+0.38, z=-len/2+0.6+i*(len-1.2)/54+(Math.random()-0.5)*0.2;
    crowdBase.push({x,y,z,ph:Math.random()*6.28,sp:4+Math.random()*4});
    dummy.position.set(x,y,z);dummy.updateMatrix();crowd.setMatrixAt(k,dummy.matrix);
    crowd.setColorAt(k,new THREE.Color(pal[(Math.random()*pal.length)|0]));k++;
  }
  g.add(crowd); scene.add(g);
}

// flags along straight
const flags=[];
{
  const pal=[0xe53935,0xfdd835,0x1e88e5,0x43a047,0xff6f00,0x8e24aa];
  for(let j=0;j<10;j++){
    const s=-60+j*12; const f=frameAt(s,newF());
    for(const sg of [-1,1]){
      if(sg===outSign && s>-40 && s<10) continue;
      const p=f.p.clone().addScaledVector(f.s,sg*(hw+2.2)); const gy=groundHeight(p.x,p.z);
      const pole=new THREE.Mesh(new THREE.CylinderGeometry(0.07,0.07,5),lam(0xdddddd));pole.position.set(p.x,gy+2.5,p.z);scene.add(pole);
      const fl=new THREE.Mesh(new THREE.PlaneGeometry(1.6,1).translate(0.8,0,0),new THREE.MeshLambertMaterial({color:pal[(j+(sg>0?0:3))%6],side:THREE.DoubleSide}));
      fl.position.set(p.x,gy+4.4,p.z);scene.add(fl);flags.push(fl);
    }
  }
}

// trees & rocks
{
  const pts=[];let tries=0;
  while(pts.length<260&&tries<6000){tries++;
    const x=(Math.random()*2-1)*220,z=(Math.random()*2-1)*190;
    const nt=nearestTrack(x,z); if(nt.dist<hw+11)continue;
    if(Math.hypot(x-standCenter.x,z-standCenter.z)<34)continue;
    const y=groundFrom(x,z,nt); if(y>20)continue;
    pts.push({x,y,z,s:0.7+Math.random()*0.8,pine:Math.random()<0.55});
  }
  const trunk=new THREE.InstancedMesh(new THREE.CylinderGeometry(0.25,0.4,2.4,6).translate(0,1.2,0),lam(0x6d4c41),pts.length);
  const pines=pts.filter(p=>p.pine), rounds=pts.filter(p=>!p.pine);
  const pc=new THREE.InstancedMesh(new THREE.ConeGeometry(1.9,5.5,8).translate(0,4.6,0),lam(0xffffff),pines.length);
  const rc=new THREE.InstancedMesh(new THREE.IcosahedronGeometry(2.2,1).translate(0,4,0),lam(0xffffff),rounds.length);
  pts.forEach((p,i)=>{dummy.position.set(p.x,p.y-0.2,p.z);dummy.rotation.set(0,Math.random()*6,0);dummy.scale.setScalar(p.s);dummy.updateMatrix();trunk.setMatrixAt(i,dummy.matrix);});
  pines.forEach((p,i)=>{dummy.position.set(p.x,p.y-0.2,p.z);dummy.scale.setScalar(p.s);dummy.updateMatrix();pc.setMatrixAt(i,dummy.matrix);pc.setColorAt(i,new THREE.Color().setHSL(0.33+Math.random()*0.05,0.6,0.22+Math.random()*0.1));});
  rounds.forEach((p,i)=>{dummy.position.set(p.x,p.y-0.2,p.z);dummy.scale.setScalar(p.s);dummy.updateMatrix();rc.setMatrixAt(i,dummy.matrix);rc.setColorAt(i,new THREE.Color().setHSL(0.22+Math.random()*0.1,0.65,0.35+Math.random()*0.1));});
  for(const m of [trunk,pc,rc]){m.castShadow=true;scene.add(m);}
  const rn=70, rocks=new THREE.InstancedMesh(new THREE.DodecahedronGeometry(1,0),lam(0x9e9e9e),rn);
  for(let i=0;i<rn;i++){let x,z,nt;do{x=(Math.random()*2-1)*200;z=(Math.random()*2-1)*170;nt=nearestTrack(x,z);}while(nt.dist<hw+8);
    dummy.position.set(x,groundFrom(x,z,nt),z);dummy.rotation.set(Math.random()*3,Math.random()*3,0);dummy.scale.set(0.6+Math.random()*1.4,0.5+Math.random(),0.6+Math.random()*1.4);dummy.updateMatrix();rocks.setMatrixAt(i,dummy.matrix);}
  rocks.castShadow=true;scene.add(rocks);
}
// tyre stacks at corners
{
  const list=[];
  for(let i=0;i<N;i+=22){if(Math.abs(K[i])<0.02)continue;const sg=K[i]>0?-1:1;const p=P[i].clone().addScaledVector(SD[i],sg*(hw+3));list.push(p);}
  const tm=new THREE.InstancedMesh(new THREE.TorusGeometry(0.42,0.2,6,12).rotateX(Math.PI/2),lam(0xffffff),list.length*3);
  let k=0;
  list.forEach((p,j)=>{const gy=groundHeight(p.x,p.z);for(let h=0;h<3;h++){dummy.position.set(p.x,gy+0.2+h*0.38,p.z);dummy.rotation.set(0,0,0);dummy.scale.setScalar(1);dummy.updateMatrix();tm.setMatrixAt(k,dummy.matrix);tm.setColorAt(k,new THREE.Color((h+j)%2?0xeeeeee:0xd32f2f));k++;}});
  tm.castShadow=true;scene.add(tm);
}
// mountains
for(let i=0;i<18;i++){
  const a=i/18*Math.PI*2+Math.random()*0.2, r=300+Math.random()*60, h=70+Math.random()*60, rad=50+Math.random()*30;
  const m=new THREE.Mesh(new THREE.ConeGeometry(rad,h,7),lam(new THREE.Color().setHSL(0.28+Math.random()*0.06,0.3,0.35)));
  m.position.set(Math.cos(a)*r,h/2-5,Math.sin(a)*r);scene.add(m);
  const cap=new THREE.Mesh(new THREE.ConeGeometry(rad*0.32,h*0.32,7),lam(0xffffff));cap.position.set(m.position.x,h-5-h*0.16+0.5,m.position.z);scene.add(cap);
}
// clouds
const clouds=[];
for(let i=0;i<14;i++){
  const g=new THREE.Group();const n=4+(Math.random()*4|0);
  for(let j=0;j<n;j++){const s=new THREE.Mesh(new THREE.SphereGeometry(6+Math.random()*6,10,8),lam(0xffffff));s.position.set(j*8-n*4,Math.random()*4,Math.random()*6);g.add(s);}
  const a=Math.random()*6.28,r=120+Math.random()*200;g.position.set(Math.cos(a)*r,70+Math.random()*30,Math.sin(a)*r);scene.add(g);clouds.push(g);
}
// balloons
const balloons=[];
for(let i=0;i<6;i++){
  const g=new THREE.Group();
  const b=new THREE.Mesh(new THREE.SphereGeometry(2.5,16,12),lam(new THREE.Color().setHSL(i/6,0.8,0.55)));b.scale.y=1.2;g.add(b);
  const bs=new THREE.Mesh(new THREE.BoxGeometry(1,0.8,1),lam(0x8d6e63));bs.position.y=-4.2;g.add(bs);
  const a=i/6*6.28+0.4,r=40+Math.random()*50;g.position.set(Math.cos(a)*r,28+Math.random()*12,Math.sin(a)*r);g.userData.by=g.position.y;scene.add(g);balloons.push(g);
}
// item boxes
const itemBoxes=[];
{
  const tex=canvasTex(128,128,(x,w,h)=>{const gr=x.createLinearGradient(0,0,w,h);gr.addColorStop(0,'#ff4081');gr.addColorStop(0.35,'#ffd740');gr.addColorStop(0.65,'#69f0ae');gr.addColorStop(1,'#40c4ff');x.fillStyle=gr;x.fillRect(0,0,w,h);
    x.strokeStyle='#fff';x.lineWidth=8;x.strokeRect(4,4,w-8,h-8);x.font='900 90px Arial';x.textAlign='center';x.textBaseline='middle';x.lineWidth=6;x.strokeStyle='#333';x.strokeText('?',w/2,h/2+4);x.fillStyle='#fff';x.fillText('?',w/2,h/2+4);});
  const mat=new THREE.MeshLambertMaterial({map:tex,transparent:true,opacity:0.88,emissive:0x333333});
  const geo=new THREE.BoxGeometry(1.2,1.2,1.2);
  for(const fr of [0.27,0.55,0.73]){const f=frameAt(L*fr,newF());
    for(const d of [-4.5,-1.5,1.5,4.5]){const m=new THREE.Mesh(geo,mat);m.position.copy(f.p).addScaledVector(f.s,d);m.position.y+=1.3;m.castShadow=true;scene.add(m);itemBoxes.push({m,t:0});}}
}

// ---------- particles ----------
const PMAX=3500;
const pPos=new Float32Array(PMAX*3),pCol=new Float32Array(PMAX*3),pA=new Float32Array(PMAX),pS=new Float32Array(PMAX);
const pVel=new Float32Array(PMAX*3),pLife=new Float32Array(PMAX),pMax=new Float32Array(PMAX),pGrow=new Float32Array(PMAX),pBS=new Float32Array(PMAX),pBA=new Float32Array(PMAX),pGrav=new Float32Array(PMAX);
const pGeo=new THREE.BufferGeometry();
pGeo.setAttribute('position',new THREE.BufferAttribute(pPos,3));
pGeo.setAttribute('pcolor',new THREE.BufferAttribute(pCol,3));
pGeo.setAttribute('alpha',new THREE.BufferAttribute(pA,1));
pGeo.setAttribute('size',new THREE.BufferAttribute(pS,1));
const pMat=new THREE.ShaderMaterial({uniforms:{scale:{value:1}},transparent:true,depthWrite:false,
  vertexShader:`attribute float size;attribute float alpha;attribute vec3 pcolor;varying float vA;varying vec3 vC;
  void main(){vA=alpha;vC=pcolor;vec4 mv=modelViewMatrix*vec4(position,1.0);gl_PointSize=size*scale/max(-mv.z,0.1);gl_Position=projectionMatrix*mv;}`,
  fragmentShader:`varying float vA;varying vec3 vC;void main(){vec2 c=gl_PointCoord-0.5;float d=length(c);if(d>0.5||vA<0.004)discard;gl_FragColor=vec4(vC,smoothstep(0.5,0.1,d)*vA);}`});
const points=new THREE.Points(pGeo,pMat);points.frustumCulled=false;scene.add(points);
let pNext=0;
function emit(x,y,z,vx,vy,vz,r,g,b,size,grow,life,alpha,grav){
  const i=pNext;pNext=(pNext+1)%PMAX;
  pPos[i*3]=x;pPos[i*3+1]=y;pPos[i*3+2]=z;pVel[i*3]=vx;pVel[i*3+1]=vy;pVel[i*3+2]=vz;
  pCol[i*3]=r;pCol[i*3+1]=g;pCol[i*3+2]=b;pBS[i]=size;pGrow[i]=grow;pLife[i]=pMax[i]=life;pBA[i]=alpha;pGrav[i]=grav;
}
function updateParticles(dt){
  const drag=Math.exp(-dt*2.2);
  for(let i=0;i<PMAX;i++){
    if(pLife[i]>0){pLife[i]-=dt;const t=1-Math.max(pLife[i],0)/pMax[i];
      pVel[i*3]*=drag;pVel[i*3+2]*=drag;pVel[i*3+1]=pVel[i*3+1]*drag+pGrav[i]*dt;
      pPos[i*3]+=pVel[i*3]*dt;pPos[i*3+1]+=pVel[i*3+1]*dt;pPos[i*3+2]+=pVel[i*3+2]*dt;
      pA[i]=pBA[i]*(1-t);pS[i]=pBS[i]*(1+pGrow[i]*t);
    } else pA[i]=0;
  }
  pGeo.attributes.position.needsUpdate=pGeo.attributes.pcolor.needsUpdate=pGeo.attributes.alpha.needsUpdate=pGeo.attributes.size.needsUpdate=true;
}
function updatePScale(){pMat.uniforms.scale.value=innerHeight*renderer.getPixelRatio()/(2*Math.tan(MU.degToRad(camera.fov)/2));}

// ---------- karts ----------
const KDEF=[{n:'ROSSO',c:0xe53935},{n:'VERDE',c:0x43a047},{n:'AZZURRO',c:0x1e88e5},{n:'GIALLO',c:0xfdd835},{n:'VIOLA',c:0x8e24aa},{n:'ROSA',c:0xf06292}];
const tireMat=lam(0x1b1b1b), metal=lam(0xb0b0b0), darkM=lam(0x2a2a2a), skinM=lam(0xffcc99);
function makeWheel(r,w,col){
  const g=new THREE.Group();
  const t=new THREE.Mesh(new THREE.CylinderGeometry(r,r,w,18).rotateZ(Math.PI/2),tireMat);
  const h=new THREE.Mesh(new THREE.CylinderGeometry(r*0.55,r*0.55,w+0.03,10).rotateZ(Math.PI/2),lam(col));
  const sp=new THREE.Mesh(new THREE.BoxGeometry(w+0.06,r*1.6,0.1),metal);
  const sp2=sp.clone();sp2.rotation.x=Math.PI/2;
  g.add(t,h,sp,sp2);g.traverse(o=>{if(o.isMesh)o.castShadow=true;});return g;
}
function makeKart(def){
  const g=new THREE.Group(), ch=new THREE.Group(), drv=new THREE.Group(); g.add(ch); ch.add(drv);
  const cm=lam(def.c);
  const add=(geo,m,x,y,z,par=ch)=>{const o=new THREE.Mesh(geo,m);o.position.set(x,y,z);o.castShadow=true;par.add(o);return o;};
  add(new THREE.BoxGeometry(1.25,0.3,2.0),cm,0,0.38,0);
  add(new THREE.BoxGeometry(1.0,0.24,0.75),cm,0,0.36,1.25);
  add(new THREE.BoxGeometry(1.75,0.14,0.3),darkM,0,0.3,1.62);
  add(new THREE.BoxGeometry(1.6,0.12,0.9),darkM,0,0.3,0);
  add(new THREE.BoxGeometry(0.85,0.45,0.6),darkM,0,0.66,-0.85);
  for(const x of [-0.25,0.25]){const e=add(new THREE.CylinderGeometry(0.08,0.1,0.45,8).rotateX(Math.PI/2),metal,x,0.78,-1.25);}
  add(new THREE.BoxGeometry(0.7,0.55,0.16),darkM,0,0.8,-0.48);
  const num=add(new THREE.BoxGeometry(0.5,0.3,0.05),lam(0xffffff),0,0.55,1.63);
  const sw=add(new THREE.TorusGeometry(0.17,0.035,6,14),darkM,0,1.0,0.42);sw.rotation.x=-0.9;
  const suit=lam(new THREE.Color(def.c).lerp(new THREE.Color(0x2244aa),0.55));
  add(new THREE.CylinderGeometry(0.24,0.3,0.62,10),suit,0,0.9,-0.18,drv);
  for(const sg of [-1,1]){const a=add(new THREE.BoxGeometry(0.13,0.13,0.55),suit,sg*0.25,0.98,0.12,drv);a.rotation.x=0.4;}
  add(new THREE.SphereGeometry(0.27,16,12),skinM,0,1.4,-0.1,drv);
  add(new THREE.SphereGeometry(0.31,16,12,0,Math.PI*2,0,Math.PI*0.55),cm,0,1.42,-0.12,drv);
  add(new THREE.BoxGeometry(0.4,0.1,0.12),darkM,0,1.44,0.15,drv);
  add(new THREE.SphereGeometry(0.1,8,6),lam(0xffffff),0,1.74,-0.1,drv);
  const fp=[],rw=[];
  for(const sg of [-1,1]){
    const piv=new THREE.Group();piv.position.set(sg*0.78,0.28,0.8);const w=makeWheel(0.28,0.3,def.c);piv.add(w);g.add(piv);fp.push({piv,w});
    const r=makeWheel(0.34,0.4,def.c);r.position.set(sg*0.82,0.34,-0.72);g.add(r);rw.push(r);
  }
  scene.add(g);
  return {g,ch,drv,fp,rw,def,name:def.n,color:def.c};
}
const karts=KDEF.map((d,i)=>{const k=makeKart(d);k.idx=i;return k;});
const baseSpeed=L/10.2;

// ---------- race state ----------
let clockT=0, raceTime=0, state='countdown', resultsT=0, finishOrder=[], finalLapShown=false, winMsgShown=false;
const $=id=>document.getElementById(id);
const posDiv=$('pos'), rows={};
karts.forEach(k=>{const r=document.createElement('div');r.className='row';r.style.borderLeftColor='#'+new THREE.Color(k.color).getHexString();
  r.innerHTML=`<span class="r"></span><span class="sw" style="background:#${new THREE.Color(k.color).getHexString()}"></span><span class="nm">${k.name}</span><span class="gap"></span>`;
  posDiv.appendChild(r);rows[k.name]=r;});
function resetRace(){
  const order=[...karts].sort(()=>Math.random()-0.5);
  order.forEach((k,i)=>{const row=Math.floor(i/2),col=i%2;
    k.p=-5-row*6.5-col*3.2; k.d=col?2.6:-2.6; k.dv=0; k.v=0;
    k.skill=0.955+Math.random()*0.045; k.lane=(Math.random()*2-1)*1.4; k.phase=Math.random()*6.28;
    k.passTimer=0; k.passTarget=0; k.drift=0; k.driftTime=0; k.boost=0; k.hop=0; k.steer=0;
    k.finished=false; k.finishTime=0; k.spin=0; k.gridRank=i;
  });
  clockT=0;raceTime=0;state='countdown';finishOrder=[];finalLapShown=false;winMsgShown=false;
  $('results').style.display='none';camMode='';
}
function computeOrder(){return karts.slice().sort((a,b)=>{if(a.finished&&b.finished)return a.finishTime-b.finishTime;if(a.finished)return -1;if(b.finished)return 1;return b.p-a.p;});}

const F1=newF(), tv=new V3(), tv2=new V3(), m4=new THREE.Matrix4();
function sparkCol(t){return t<0.7?[1,0.8,0.3]:t<1.6?[0.35,0.65,1]:[1,0.45,0.95];}
function updateKart(k,dt,rank,racing){
  const s=k.p;
  const kNear=curvAvg(s,3,30), kMaxA=curvAbsMax(s,0,36), kHere=K[idx(s)];
  const lineAmt=MU.clamp(kNear*42,-1,1);
  let target=lineAmt*(hw-1.4)+k.lane*(1-Math.abs(lineAmt));
  let desired=baseSpeed*k.skill*(1-Math.min(0.42,kMaxA*6.5))*(1+0.03*Math.sin(clockT*0.6+k.phase))+rank*0.013*baseSpeed;
  if(k.boost>0){desired*=1.12;k.boost-=dt;}
  if(k.finished)desired=baseSpeed*0.5;
  if(racing&&!k.finished){
    let blk=null,bg=1e9;
    for(const o of karts){if(o===k)continue;const gap=o.p-k.p;if(gap>0&&gap<11&&Math.abs(o.d-k.d)<1.8&&gap<bg){bg=gap;blk=o;}}
    if(blk){
      if(desired>blk.v*1.003&&k.passTimer<=0){let sd=(k.d>=blk.d)?1:-1;let tg=blk.d+sd*2.5;if(Math.abs(tg)>hw-1.1){sd=-sd;tg=blk.d+sd*2.5;}k.passTarget=MU.clamp(tg,-(hw-1.1),hw-1.1);k.passTimer=1.4;}
      if(bg<3.4)desired=Math.min(desired,blk.v*0.97);
    }
  }
  if(k.passTimer>0){k.passTimer-=dt;target=k.passTarget;}
  if(racing){const rate=desired>k.v?1.0:2.5;k.v+=(desired-k.v)*Math.min(1,dt*rate);}
  else {k.v=0;target=k.d;}
  const dvT=MU.clamp((target-k.d)*2.6,-6,6);
  k.dv+=(dvT-k.dv)*Math.min(1,dt*6);k.d+=k.dv*dt;
  for(const o of karts){if(o!==k&&Math.abs(o.p-k.p)<2.4&&Math.abs(o.d-k.d)<1.55){k.d+=Math.sign((k.d-o.d)||(k.idx-o.idx))*dt*4;}}
  k.d=MU.clamp(k.d,-(hw-0.9),hw-0.9);
  const fac=MU.clamp(1/(1-kHere*k.d),0.85,1.18);
  k.p+=k.v*fac*dt;
  if(racing&&!k.finished&&k.p>=LAPS*L){k.finished=true;k.finishTime=raceTime;finishOrder.push(k);}
  // drift
  const want=racing&&Math.abs(kNear)>0.02&&k.v>baseSpeed*0.5;
  if(want){if(k.driftTime===0)k.hop=0.25;k.driftTime+=dt;}else{if(k.driftTime>1.0)k.boost=0.9;k.driftTime=0;}
  const dT=want?-Math.sign(kNear)*(0.33+Math.min(0.2,Math.abs(kNear)*3)):0;
  k.drift+=(dT-k.drift)*Math.min(1,dt*5);
  k.steer+=(MU.clamp(-kNear*14-k.dv*0.05,-0.5,0.5)-k.steer)*Math.min(1,dt*8);
  // pose
  const f=frameAt(k.p,F1);
  let hopY=0;if(k.hop>0){k.hop-=dt;hopY=Math.sin((1-k.hop/0.25)*Math.PI)*0.35;}
  k.g.position.copy(f.p).addScaledVector(f.s,k.d).addScaledVector(f.n,0.02+hopY);
  const fwd=tv.copy(f.t).applyAxisAngle(f.n,k.drift);
  const X=tv2.crossVectors(f.n,fwd).normalize();const Y=new V3().crossVectors(fwd,X);
  m4.makeBasis(X,Y,fwd);k.g.quaternion.setFromRotationMatrix(m4);
  k.ch.rotation.z=MU.clamp(-kNear*3,-0.08,0.08);
  k.ch.position.y=Math.sin(clockT*30+k.phase)*0.015*(k.v/baseSpeed);
  k.drv.rotation.z=MU.clamp(kNear*9,-0.3,0.3);
  k.spin+=k.v*dt;
  for(const w of k.fp){w.piv.rotation.y=k.steer;w.w.rotation.x=k.spin/0.28;}
  for(const w of k.rw)w.rotation.x=k.spin/0.34;
  k.g.updateMatrixWorld();
  // particles
  if(k.v>3){
    const back=tv.set(0,0,-1).transformDirection(k.g.matrixWorld);
    for(const sg of [-1,1]){
      const wp=new V3(sg*0.82,0.12,-0.95).applyMatrix4(k.g.matrixWorld);
      if(k.driftTime>0){
        emit(wp.x,wp.y+0.2,wp.z,back.x*2+(Math.random()-0.5),0.8+Math.random(),back.z*2+(Math.random()-0.5),0.88,0.88,0.9,0.8,2.6,0.9,0.45,0.3);
        const c=sparkCol(k.driftTime);
        for(let q=0;q<2;q++)emit(wp.x,wp.y,wp.z,back.x*5+(Math.random()-0.5)*4,1.5+Math.random()*3,back.z*5+(Math.random()-0.5)*4,c[0],c[1],c[2],0.28,-0.5,0.3,1,-12);
      } else if(Math.random()<(Math.abs(k.d)>hw-1.3?0.8:0.25)){
        emit(wp.x,wp.y,wp.z,back.x*1.5+(Math.random()-0.5),0.5+Math.random()*0.6,back.z*1.5+(Math.random()-0.5),0.72,0.62,0.46,0.5,2.2,0.6,0.35,0.2);
      }
    }
    if(k.boost>0){for(const sg of [-0.25,0.25]){const ep=new V3(sg,0.78,-1.5).applyMatrix4(k.g.matrixWorld);emit(ep.x,ep.y,ep.z,back.x*6,0.5,back.z*6,1,0.55+Math.random()*0.3,0.1,0.45,0.5,0.25,0.9,0);}}
  }
}

// ---------- camera ----------
let camMode='', trackCamN=0; const camLook=new V3(); const CF=newF();
function setFov(v){if(camera.fov!==v){camera.fov=v;camera.updateProjectionMatrix();updatePScale();}}
function placeTrackCam(sAt,sign,h,dist){
  const f=frameAt(sAt,CF);const p=f.p.clone().addScaledVector(f.s,sign*(hw+dist));
  p.y=Math.max(groundHeight(p.x,p.z),f.p.y)+h;camera.position.copy(p);
}
function chaseTarget(k,out){const f=frameAt(k.p,CF);return out.copy(k.g.position).addScaledVector(f.t,-7.5).addScaledVector(up,3.1);}
function updateCamera(dt,lead){
  let mode;
  if(clockT<3)mode='grid';
  else if(lead.p>LAPS*L-75&&lead.p<LAPS*L+28)mode='finish';
  else {const rt=raceTime%10;mode=(raceTime>5&&rt>=6.5&&!lead.finished)?'track':'chase';}
  const f=frameAt(lead.p,CF);
  if(mode!==camMode){
    camMode=mode;
    if(mode==='track'){trackCamN=trackCamN%4+1;const sAt=lead.p+42;const kk=K[idx(sAt)];const sign=Math.abs(kk)>0.004?(kk>0?-1:1):(trackCamN%2?1:-1);
      placeTrackCam(sAt,sign,2.2,6);setFov(48);camLook.copy(lead.g.position);$('cam').innerHTML=`<i>●</i> TRACKSIDE CAM ${trackCamN}`;}
    else if(mode==='finish'){placeTrackCam(LAPS*L+14,-outSign,2.6,5);setFov(55);camLook.copy(lead.g.position);$('cam').innerHTML='<i>●</i> FINISH LINE CAM';}
    else if(mode==='chase'){chaseTarget(lead,camera.position);setFov(68);const f2=frameAt(lead.p,CF);camLook.copy(lead.g.position).addScaledVector(f2.t,4).addScaledVector(up,1);$('cam').innerHTML='<i>●</i> CHASE CAM – LEADER';}
    else {setFov(60);$('cam').innerHTML='<i>●</i> STARTING GRID';}
  }
  if(mode==='grid'){
    const c=frameAt(-12,CF);const a=clockT*0.38;
    camera.position.copy(c.p).addScaledVector(c.t,17*Math.cos(a)).addScaledVector(c.s,17*Math.sin(a)*-outSign).addScaledVector(up,4.5);
    camera.lookAt(c.p.x,c.p.y+0.8,c.p.z);
  } else if(mode==='chase'){
    const f2=frameAt(lead.p,CF);
    camera.position.lerp(chaseTarget(lead,new V3()),1-Math.exp(-dt*6));
    camLook.lerp(new V3().copy(lead.g.position).addScaledVector(f2.t,4).addScaledVector(up,1),1-Math.exp(-dt*10));
    camera.lookAt(camLook);
  } else {
    camLook.lerp(new V3().copy(lead.g.position).addScaledVector(up,0.8),1-Math.exp(-dt*8));
    camera.lookAt(camLook);
  }
  sky.position.copy(camera.position);
  sun.position.copy(lead.g.position).add(new V3(50,90,35));sun.target.position.copy(lead.g.position);
}

// ---------- HUD ----------
const ords=['1st','2nd','3rd','4th','5th','6th'];
let hudAcc=0, msgTimer=0;
function showMsg(t,dur){const m=$('msg');m.textContent=t;m.style.opacity=1;msgTimer=dur;}
function fmt(t){const m=Math.floor(t/60),s=t-m*60;return m+':'+(s<10?'0':'')+s.toFixed(2);}
function updateHUD(dt,order,lead){
  hudAcc+=dt;
  order.forEach((k,i)=>{const r=rows[k.name];r.style.top=(i*37)+'px';r.children[0].textContent=ords[i];r.classList.toggle('lead',i===0);});
  if(hudAcc>0.2){hudAcc=0;order.forEach((k,i)=>{const g=rows[k.name].children[3];
    if(k.finished)g.textContent='FIN';else if(i===0)g.textContent=clockT<3?'':'LEADER';else g.textContent='+'+((order[0].p-k.p)/Math.max(k.v,8)).toFixed(1)+'s';});}
  const lap=MU.clamp(Math.floor(Math.max(lead.p,0)/L)+1,1,LAPS);
  $('lap').innerHTML=lead.finished?'<b>FINISH</b>':`LAP <b>${lap}</b>/${LAPS}`;
  if(lap===LAPS&&!finalLapShown&&clockT>3){finalLapShown=true;showMsg('FINAL LAP!',2.2);}
  if(finishOrder.length&&!winMsgShown){winMsgShown=true;showMsg('🏁 FINISH! '+finishOrder[0].name+' WINS! 🏁',4);}
  $('time').textContent=fmt(raceTime);
  const c=$('center');
  if(clockT<4){const n=Math.floor(clockT);const txt=['3','2','1','GO!'][n];const col=['#ff3d3d','#ff9d00','#ffe600','#3dff5a'][n];const fr=clockT-n;
    c.textContent=txt;c.style.color=col;c.style.opacity=n===3?1-fr:1;c.style.transform=`translateY(-50%) scale(${1.5-fr*0.5})`;}
  else c.textContent='';
  if(msgTimer>0){msgTimer-=dt;if(msgTimer<=0)$('msg').style.opacity=0;}
  // start lights
  startLights.forEach((m,i)=>{if(clockT<3)m.material.color.set(clockT>=i?0xff2020:0x330000);else m.material.color.set(clockT<9?0x20ff40:0x103010);});
}
function showResults(){
  const r=$('results');r.innerHTML='<h2>🏆 RESULTS 🏆</h2>'+computeOrder().map((k,i)=>`<div><span style="color:#ffd600">${ords[i]}</span> &nbsp;<span style="color:#${new THREE.Color(k.color).getHexString()}">■</span> ${k.name} <span style="float:right;opacity:.8">&nbsp;&nbsp;${k.finished?fmt(k.finishTime):'--'}</span></div>`).join('');
  r.style.display='block';
}

// ---------- loop ----------
resetRace(); updatePScale();
const clock=new THREE.Clock();
function animate(){
  requestAnimationFrame(animate);
  const dt=Math.min(clock.getDelta(),0.05);
  clockT+=dt;
  const racing=clockT>=3;
  if(racing&&state==='countdown')state='race';
  if(racing&&state!=='results')raceTime+=dt;
  let order=computeOrder();
  order.forEach((k,i)=>updateKart(k,dt,i,racing));
  order=computeOrder();
  const lead=finishOrder.length?finishOrder[0]:order[0];
  if(state==='race'&&finishOrder.length&&(finishOrder.length===karts.length||raceTime-finishOrder[0].finishTime>7)){state='results';resultsT=0;showResults();}
  if(state==='results'){resultsT+=dt;if(resultsT>6)resetRace();}
  // scenery animation
  crowdBase.forEach((c,i)=>{dummy.position.set(c.x,c.y+Math.abs(Math.sin(clockT*c.sp+c.ph))*0.25,c.z);dummy.rotation.set(0,0,0);dummy.scale.setScalar(1);dummy.updateMatrix();crowd.setMatrixAt(i,dummy.matrix);});
  crowd.instanceMatrix.needsUpdate=true;
  flags.forEach((f,i)=>{f.rotation.y=Math.sin(clockT*4+i)*0.5;});
  balloons.forEach((b,i)=>{b.position.y=b.userData.by+Math.sin(clockT*0.6+i)*1.5;});
  clouds.forEach(c=>{c.position.x+=dt*1.5;if(c.position.x>350)c.position.x=-350;});
  for(const ib of itemBoxes){
    if(ib.t>0){ib.t-=dt;if(ib.t<=0)ib.m.visible=true;continue;}
    ib.m.rotation.x+=dt*1.3;ib.m.rotation.y+=dt*1.7;
    for(const k of karts){if(k.g.position.distanceToSquared(ib.m.position)<3.2){ib.m.visible=false;ib.t=2.5;
      for(let q=0;q<25;q++){const c=new THREE.Color().setHSL(Math.random(),1,0.6);emit(ib.m.position.x,ib.m.position.y,ib.m.position.z,(Math.random()-0.5)*8,Math.random()*6,(Math.random()-0.5)*8,c.r,c.g,c.b,0.35,0,0.7,1,-9);}break;}}
  }
  updateParticles(dt);
  updateCamera(dt,lead);
  updateHUD(dt,order,lead);
  renderer.render(scene,camera);
}
animate();
addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);updatePScale();});
</script>
</body>
</html>
```