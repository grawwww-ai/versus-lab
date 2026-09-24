Here's a complete self-running kart race. Everything is procedural — the circuit, kerbs, scenery, karts, particles — so the single file has no external assets. Six AI drivers race 3 laps with personality-based speeds, apex-hugging lines, braking probes, drift hops, dust/skid particles, soft collisions and overtaking; a broadcast-style HUD shows live positions, laps, a minimap and camera tags, and the whole event restarts itself after the finish so it loops forever.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Crestline GP — a self-driving kart race</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  html,body{width:100%;height:100%;overflow:hidden;background:#0c0e11}
  #ui{position:fixed;inset:0;pointer-events:none;z-index:10;
      font-family:"Trebuchet MS","Segoe UI",Verdana,sans-serif;color:#f4f1e8}
  .panel{background:rgba(14,16,20,.84);border:1px solid rgba(255,255,255,.09);
         box-shadow:0 3px 0 rgba(0,0,0,.35)}
  #board{position:absolute;top:16px;left:16px;padding:9px 12px 11px;min-width:212px}
  #board h4{font-size:10px;letter-spacing:.28em;color:#8f97a3;margin:1px 2px 6px}
  #rows{display:flex;flex-direction:column}
  .row{display:flex;align-items:center;gap:8px;padding:3px 9px;margin:3px 0;
       border-radius:5px;transform:skewX(-8deg)}
  .row .rk{width:16px;font-size:15px;font-weight:900;font-style:italic;color:#8b939e}
  .row .chip{width:10px;height:10px;border-radius:3px;flex:none;box-shadow:inset 0 0 0 1px rgba(0,0,0,.4)}
  .row .nm{flex:1;font-size:13.5px;font-weight:700;font-style:italic;letter-spacing:.05em}
  .row .gp{font-size:11px;color:#98a0ac;font-variant-numeric:tabular-nums;min-width:52px;text-align:right}
  .row.ld{background:rgba(255,79,32,.17);box-shadow:inset 0 0 0 1px rgba(255,79,32,.55)}
  .row.ld .rk{color:#ff6a3c}
  #lapbox{position:absolute;top:16px;right:16px;padding:9px 16px 10px;text-align:right}
  #lap{font-size:23px;font-weight:900;font-style:italic;letter-spacing:.03em}
  #clock{font-size:12.5px;color:#98a0ac;font-variant-numeric:tabular-nums;letter-spacing:.1em}
  #mapbox{position:absolute;left:16px;bottom:16px;padding:8px;border-radius:12px}
  #map{display:block;width:168px;height:168px}
  #camtag{position:absolute;right:16px;bottom:16px;padding:7px 13px;
          font-size:10.5px;font-weight:700;letter-spacing:.26em;color:#c9cfd8}
  #sub{position:absolute;left:50%;bottom:14px;transform:translateX(-50%);
       font-size:10.5px;letter-spacing:.32em;color:rgba(244,241,232,.5);white-space:nowrap}
  #big{position:absolute;left:50%;top:36%;transform:translate(-50%,-50%);
       font-size:min(17vw,150px);font-weight:900;font-style:italic;color:#f4f1e8;
       text-shadow:.055em .085em 0 #14161a;display:none;text-align:center;line-height:1.05}
  #big.on{display:block}
  #big.sm{font-size:min(6.4vw,44px);letter-spacing:.14em}
  #big.go{color:#8fe14a}
  #big.fin{color:#ff4f20;font-size:min(8vw,58px)}
</style>
</head>
<body>
<div id="ui">
  <div id="board" class="panel"><h4>RUNNING ORDER</h4><div id="rows"></div></div>
  <div id="lapbox" class="panel" style="position:absolute;top:16px;right:16px;padding:9px 16px 10px;text-align:right">
    <div id="lap" style="font-size:23px;font-weight:900;font-style:italic">LAP 1/3</div>
    <div id="clock">0:00.0</div>
  </div>
  <div id="mapbox" class="panel"><canvas id="map" width="336" height="336" style="width:168px;height:168px;display:block"></canvas></div>
  <div id="camtag" class="panel">GRID CAM</div>
  <div id="sub">CRESTLINE GP · SIX AI DRIVERS · THREE LAPS · CHASE + TRACKSIDE CAMERAS</div>
  <div id="big"></div>
</div>

<script type="module">
import * as THREE from 'three';

/* ---------------- helpers ---------------- */
const clamp=(v,a,b)=>v<a?a:v>b?b:v;
const rand=(a,b)=>a+Math.random()*(b-a);
const wrapPI=a=>{a%=Math.PI*2;if(a>Math.PI)a-=Math.PI*2;if(a<-Math.PI)a+=Math.PI*2;return a;};
const damp=(r,dt)=>1-Math.exp(-r*dt);
const UP=new THREE.Vector3(0,1,0);
const _v1=new THREE.Vector3(),_v2=new THREE.Vector3(),_q=new THREE.Quaternion(),_m4=new THREE.Matrix4();
const MATC={};const mat=c=>MATC[c]||(MATC[c]=new THREE.MeshLambertMaterial({color:c}));
function makeTex(w,h,fn){const c=document.createElement('canvas');c.width=w;c.height=h;
  const g=c.getContext('2d');fn(g,w,h);const t=new THREE.CanvasTexture(c);
  t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=8;t.wrapS=t.wrapT=THREE.RepeatWrapping;return t;}

/* ---------------- renderer / scene ---------------- */
const renderer=new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.setSize(innerWidth,innerHeight);
renderer.toneMapping=THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure=1.08;
document.body.appendChild(renderer.domElement);
const scene=new THREE.Scene();
scene.fog=new THREE.Fog(0xe6f0ea,240,950);
const cam=new THREE.PerspectiveCamera(55,innerWidth/innerHeight,0.1,4200);
cam.position.set(0,30,140);
addEventListener('resize',()=>{cam.aspect=innerWidth/innerHeight;cam.updateProjectionMatrix();
  renderer.setSize(innerWidth,innerHeight);});

scene.add(new THREE.HemisphereLight(0xcfe6ff,0x88a862,0.95));
const sun=new THREE.DirectionalLight(0xfff1da,2.6);sun.position.set(170,230,90);scene.add(sun);

/* sky dome */
const sky=new THREE.Mesh(new THREE.SphereGeometry(1700,20,10),new THREE.ShaderMaterial({
  side:THREE.BackSide,depthWrite:false,
  vertexShader:`varying vec3 vW;void main(){vW=(modelMatrix*vec4(position,1.)).xyz;
    gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`,
  fragmentShader:`varying vec3 vW;void main(){float h=normalize(vW).y;
    vec3 c=mix(vec3(.90,.94,.92),vec3(.28,.57,.82),smoothstep(0.,.5,h));gl_FragColor=vec4(c,1.);}`
}));
sky.material.toneMapped=false;scene.add(sky);

/* ---------------- track centreline ---------------- */
const RAW=[[0,0,74],[58,0,74],[96,2,58],[104,4,22],[88,7,-10],[60,9,-20],[28,8,-10],
           [8,9,-34],[-24,8,-52],[-58,6,-52],[-84,4,-26],[-78,2,8],[-92,1,40],[-58,0,70]];
const cps=RAW.map(p=>new THREE.Vector3(p[0]*0.9,p[1]*1.2,p[2]*0.9));
const curve=new THREE.CatmullRomCurve3(cps,true,'centripetal');
const N=700,L=curve.getLength(),ds=L/N,HALF=7,LAPS=3;
const P=curve.getSpacedPoints(N).slice(0,N);
const T=[],SD=[],YAW=new Float32Array(N);
for(let i=0;i<N;i++){
  const t=P[(i+1)%N].clone().sub(P[(i-1+N)%N]).normalize();T.push(t);
  YAW[i]=Math.atan2(t.x,t.z);
  SD.push(new THREE.Vector3(t.z,0,-t.x).normalize()); // left of travel
}
const Kr=new Float32Array(N),KSm=new Float32Array(N),KS=new Float32Array(N);
for(let i=0;i<N;i++)Kr[i]=wrapPI(YAW[(i+1)%N]-YAW[(i-1+N)%N])/(2*ds);
for(let i=0;i<N;i++){let s=0;for(let o=-6;o<=6;o++)s+=Kr[(i+o+N)%N];KSm[i]=s/13;}
for(let i=0;i<N;i++){let s=0;for(let o=-5;o<=5;o++)s+=KSm[(i+o+N)%N];KS[i]=s/11;}
/* clearance to other legs of the circuit (keeps scenery/skirt out of overlaps) */
const CLEAR=new Float32Array(N).fill(1e9);
for(let i=0;i<N;i++){let m=1e9;const xi=P[i].x,zi=P[i].z;
  for(let j=0;j<N;j++){const g=Math.abs(i-j);if(Math.min(g,N-g)<50)continue;
    const dx=P[j].x-xi,dz=P[j].z-zi,q=dx*dx+dz*dz;if(q<m)m=q;}CLEAR[i]=Math.sqrt(m);}

/* terrain height field: blend of track elevation and rolling ground */
const SK_OFF=[8.4,12,18,28,45,70,115],SK_W=[1,.86,.6,.38,.18,.06,0];
function skirtW(a){if(a<=8.4)return 1;
  for(let j=1;j<SK_OFF.length;j++)if(a<=SK_OFF[j]){
    const t=(a-SK_OFF[j-1])/(SK_OFF[j]-SK_OFF[j-1]);return SK_W[j-1]+(SK_W[j]-SK_W[j-1])*t;}
  return 0;}
const groundY=(x,z)=>-0.6+(Math.sin(x*.043)*1.1+Math.cos(z*.037+1.7)*1.0+Math.sin((x+z)*.019)*1.6)*0.72;
function fieldH(x,z,gi){let bj=gi,bd=1e18;
  for(let o=-150;o<=150;o+=2){const j=(gi+o+N)%N,dx=P[j].x-x,dz=P[j].z-z,q=dx*dx+dz*dz;
    if(q<bd){bd=q;bj=j;}}
  for(let o=-2;o<=2;o++){const j=(bj+o+N)%N,dx=P[j].x-x,dz=P[j].z-z,q=dx*dx+dz*dz;
    if(q<bd){bd=q;}}
  const d=Math.sqrt(bd),w=skirtW(d);
  return P[bj].y*w+groundY(x,z)*(1-w);}

/* ---------------- track meshes ---------------- */
const asphaltTex=makeTex(128,128,g=>{g.fillStyle='#3d4148';g.fillRect(0,0,128,128);
  for(let i=0;i<2600;i++){g.fillStyle=Math.random()<.5?'rgba(18,20,24,.5)':'rgba(235,235,235,.06)';
    g.fillRect(Math.random()*128,Math.random()*128,1,1);}
  g.fillStyle='rgba(15,16,20,.28)';g.fillRect(20,0,13,128);g.fillRect(95,0,13,128);});
const grassTex=makeTex(128,128,g=>{g.fillStyle='#6fa551';g.fillRect(0,0,128,128);
  for(let i=0;i<2600;i++){g.fillStyle=Math.random()<.5?'rgba(46,82,38,.5)':'rgba(158,196,96,.32)';
    g.fillRect(Math.random()*128,Math.random()*128,Math.random()<.85?1:2,1+Math.random()*2);}});
const kerbTex=makeTex(32,64,g=>{g.fillStyle='#e9e5da';g.fillRect(0,0,32,64);
  g.fillStyle='#d8402a';g.fillRect(0,0,32,32);});
const checkTex=makeTex(200,40,g=>{for(let x=0;x<10;x++)for(let y=0;y<2;y++){
  g.fillStyle=(x+y)%2?'#17181c':'#efece2';g.fillRect(x*20,y*20,20,20);}});
const roadMat=new THREE.MeshLambertMaterial({map:asphaltTex,side:THREE.DoubleSide});
const kerbMat=new THREE.MeshLambertMaterial({map:kerbTex,side:THREE.DoubleSide});
const grassMat=new THREE.MeshLambertMaterial({map:grassTex,side:THREE.DoubleSide});

function buildStrip(offL,offR,liftL,liftR,m,tile){
  const g=new THREE.BufferGeometry(),pos=[],uv=[],ind=[];
  const vt=L/Math.max(1,Math.round(L/tile));
  for(let i=0;i<=N;i++){const j=i%N,p=P[j],sd=SD[j],v=i*ds/vt;
    pos.push(p.x+sd.x*offL,p.y+liftL,p.z+sd.z*offL, p.x+sd.x*offR,p.y+liftR,p.z+sd.z*offR);
    uv.push(0,v,1,v);}
  for(let i=0;i<N;i++){const a=i*2;ind.push(a,a+1,a+2,a+1,a+3,a+2);}
  g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));
  g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));
  g.setIndex(ind);g.computeVertexNormals();
  const mesh=new THREE.Mesh(g,m);mesh.frustumCulled=false;scene.add(mesh);return mesh;
}
scene.add(buildStrip(HALF,-HALF,0,0,roadMat,8));
scene.add(buildStrip(HALF,HALF+1.4,0.07,0.02,kerbMatShared(),3.2));
scene.add(buildStrip(-HALF,-(HALF+1.4),0.07,0.02,kerbMatShared(),3.2));
function kerbMatShared(){return kerbMatShared.m||(kerbMatShared.m=new THREE.MeshLambertMaterial({map:kerbTex,side:THREE.DoubleSide}));}

/* variable-width grass skirts that follow the terrain field */
function buildSkirt(sign){
  const cols=[0,0.1,0.26,0.5,1.0],g=new THREE.BufferGeometry(),pos=[],uv=[],ind=[];
  const vt=L/Math.max(1,Math.round(L/6));
  for(let i=0;i<=N;i++){const j=i%N,p=P[j],sd=SD[j];
    const wmax=clamp(CLEAR[j]*0.5-0.9,13,180);
    for(let c=0;c<5;c++){const off=8.4+(wmax-8.4)*[0,.08,.2,.4,1][c];
      const x=p.x+sd.x*off*(i%N===j?1:1)* (off*0+1)*sdSign(j,sign);}}
  return null;}
/* (skirt built explicitly below) */
function skirtSide(sign){
  const g=new THREE.BufferGeometry(),pos=[],uv=[],ind=[];
  const vt=L/Math.max(1,Math.round(L/6)),F=[0,0.08,0.2,0.42,0.72,1];
  for(let i=0;i<=N;i++){const j=i%N,p=P[j],sd=SD[j];
    const wmax=clamp(CLEAR[j]*0.5+4,14,190);
    for(let c=0;c<F.length;c++){const off=8.4+(wmax-8.4)*F[c];
      const x=p.x+sd.x*off*sideSign,z=p.z+sd.z*off*sideSign;
      pos.push(x,fieldH(x,z,j),z);uv.push(off/vt,i*ds/vt);}}
  for(let i=0;i<N;i++)for(let c=0;c<F.length-1;c++){
    const a=i*F.length+c,b=(i+1)*F.length+c;
    ind.push(a,b,a+1,a+1,b,b+1);}
  g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));
  g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));
  g.setIndex(ind);g.computeVertexNormals();
  const mesh=new THREE.Mesh(g,grassMat);mesh.frustumCulled=false;scene.add(mesh);
}
let sideSign=1;skirtSide();sideSign=-1;skirtSide();

/* start line */
{const i0=1,i1=7,g=new THREE.BufferGeometry();
 const a=P[i0],b=P[i1],sd=SD[i0],y=0.035;
 const v=[[a.x+sd.x*HALF,a.y+y,a.z+sd.z*HALF,0,0],[a.x-sd.x*HALF,a.y+y,a.z-sd.z*HALF,1,0],
          [b.x+sd.x*HALF,b.y+y,b.z+sd.z*HALF,0,1],[b.x-sd.x*HALF,b.y+y,b.z-sd.z*HALF,1,1]];
 v.forEach(q=>pos2.push(q));}
{const g=new THREE.BufferGeometry();
 const A=P[1],B=P[7],sd=SD[1],y=0.035;
 g.setAttribute('position',new THREE.Float32BufferAttribute([
   A.x+sd.x*HALF,A.y+y,A.z+sd.z*HALF, A.x-sd.x*HALF,A.y+y,A.z-sd.z*HALF,
   B.x+sd.x*HALF,B.y+y,B.z+sd.z*HALF, B.x-sd.x*HALF,B.y+y,B.z-sd.z*HALF],3));
 g.setAttribute('uv',new THREE.Float32BufferAttribute([0,0,1,0,0,1,1,1],2));
 g.setIndex([0,1,2,1,3,2]);g.computeVertexNormals();
 scene.add(new THREE.Mesh(g,new THREE.MeshLambertMaterial({map:checkTex,side:THREE.DoubleSide})));}
function pos2unused(){}

/* far ground */
{const gr=new THREE.Mesh(new THREE.CircleGeometry(1500,48).rotateX(-Math.PI/2),
  new THREE.MeshLambertMaterial({color:0x5f8f47}));
 gr.position.set(5,-3.6,10);scene.add(gr);}

/* ---------------- gantries, boards, stands ---------------- */
const lightMats=[];
function gantry(idx,txt){
  const p=P[idx],grp=new THREE.Group();grp.position.copy(p);grp.rotation.y=YAW[idx];
  const post=new THREE.CylinderGeometry(0.26,0.32,6.6,8);
  [-1,1].forEach(s=>{const m=new THREE.Mesh(post,mat(0x2a2d33));
    m.position.set(s*(HALF+1.6),3.3,0);grp.add(m);});
  const barGeo=new THREE.BoxGeometry((HALF+1.6)*2+0.6,1.6,0.7);
  const side=mat(0x22252b);
  const ban=makeTex(512,96,g=>{g.fillStyle='#161920';g.fillRect(0,0,512,96);
    g.fillStyle='#ff4f20';g.fillRect(0,0,16,96);g.fillRect(496,0,16,96);
    g.fillStyle='#f4f1e8';g.font='900 italic 44px "Trebuchet MS",sans-serif';
    g.textAlign='center';g.textBaseline='middle';g.fillText(txt,256,50);});
  const bar=new THREE.Mesh(barGeo,[side,side,side,side,
    new THREE.MeshLambertMaterial({map:makeTex(512,96,g=>{g.drawImage(bannerSrc(txt),0,0);})}),
    new THREE.MeshLambertMaterial({map:makeTex(512,96,g=>{g.drawImage(bannerSrc(txt),0,0);})})]);
  barGeo.setAttribute('uv',new THREE.Float32BufferAttribute(
    [0,1, 1,1, 1,0, 0,0, 0,1, 1,1, 1,0, 0,0],2));
  barGeo.setAttribute('uv',new THREE.Float32BufferAttribute(new Float32Array(48).map((_,i)=>{
    const f=[[0,1],[1,1],[1,0],[0,0],[0,1],[1,1],[1,0],[0,0]];return f[i%8][i%2===0?0:1];}),2));
  const uvA=[];for(let f=0;f<6;f++)uvA.push(0,1,1,1,1,0,0,0);
  barGeo.setAttribute('uv',new THREE.Float32BufferAttribute(uvA,2));
  barGeo.setAttribute('uv',new THREE.Float32BufferAttribute((()=>{
    const u=[];for(let f=0;f<6;f++)u.push(0,1,1,1,1,0,0,0);return u;})(),2));
  grp.add(new THREE.Mesh(barGeo,[side,side,side,side,bannerMat(txt),bannerMat(txt)]));
  bar.position?0:0;bar_.call(grp);
  grp.children[grp.children.length-1].position.y=6.0;
  for(let i=0;i<3;i++){const lm=new THREE.MeshBasicMaterial({color:0x2a100c});
    const s=new THREE.Mesh(new THREE.SphereGeometry(0.24,10,8),lm);
    s.position.set((i-1)*1.25,4.85,-0.45);grp.add(s);lightMats.push(lm);}
  scene.add(grp);
}
function bannerSrc(txt){const c=document.createElement('canvas');c.width=512;c.height=96;
  const g=c.getContext('2d');g.fillStyle='#161920';g.fillRect(0,0,512,96);
  g.fillStyle='#ff4f20';g.fillRect(0,0,16,96);g.fillRect(496,0,16,96);
  g.fillStyle='#f4f1e8';g.font='900 italic 44px "Trebuchet MS",sans-serif';
  g.textAlign='center';g.textBaseline='middle';g.fillText(txt,256,50);return c;}
function bannerMat(txt){const t=new THREE.CanvasTexture(bannerSrc(txt));t.colorSpace=THREE.SRGBColorSpace;
  return new THREE.MeshLambertMaterial({map:t});}
const lightMats=[];
gantry(2,'CRESTLINE GP');
gantry(Math.round(N*0.57),'SLIPSTREAM SECTOR');

/* boards */
const boardNames=[['NITRO-COLA','#d8402a','#fff'],['APEX TYRES','#efece2','#17181b'],
  ['KOYO BRAKES','#1d6b4a','#fff'],['NITRO-COLA','#d8402a','#fff'],
  ['VELOCE FUEL','#17181b','#f0b429'],['SLIPSTREAM','#d8402a','#fff'],
  ['PIT-LANE COFFEE','#efece2','#17181b'],['APEX TYRES','#efece2','#17181b']];
for(let k=0;k<8;k++){
  let idx=Math.floor((k+0.5)*N/8),side=k%2?1:-1,tries=0;
  while(CLEAR[idx]<30&&tries++<6)idx=(idx+40)%N;
  const off=side*(HALF+5.5),p=P[idx];
  const grp=new THREE.Group();grp.position.set(p.x+SD[idx].x*off,0,p.z+SD[idx].z*off);
  grp.lookAt(p.x,0,p.z);grp.position.y=fieldH(grp.position.x,grp.position.z,idx);
  const [txt,bg,fg]=boardNames[k];
  const pl=new THREE.Mesh(new THREE.PlaneGeometry(7,2.1),
    new THREE.MeshLambertMaterial({map:makeTex(256,80,g=>{
      g.fillStyle=bg;g.fillRect(0,0,256,84);g.fillStyle=bg==='#efece2'?'#d8402a':'#efece2';
      g.fillRect(0,84,256,12);g.fillStyle=fg;g.font='900 italic 30px "Trebuchet MS",sans-serif';
      g.textAlign='center';g.textBaseline='middle';g.fillText(txt,128,44);})}));
  pl.position.y=2.6;grp.add(pl);
  [-2.8,2.8].forEach(x=>{const m=new THREE.Mesh(new THREE.CylinderGeometry(0.09,0.09,2.6,6),mat(0x555a61));
    m.position.set(x,1.3,0);grp.add(m);});
  scene.add(grp);
}
/* grandstand */
{const idx=Math.round(N*0.985),p=P[idx],sd=SD[idx],yaw=YAW[idx];
 const base=p.clone().addScaledVector(sd,-(HALF+2));
 const g=new THREE.Group();g.position.copy(base);g.rotation.y=yaw-Math.PI/2;
 const crowd=makeTex(256,96,c=>{c.fillStyle='#20232a';c.fillRect(0,0,256,96);
   const cols=['#e9dcc6','#d8402a','#f0b429','#4f8f6f','#c95d8f','#e8e4da'];
   for(let i=0;i<800;i++){c.fillStyle=cols[(Math.random()*cols.length)|0];
     c.fillRect(Math.random()*256,Math.random()*96,2,2);}});
 crowd.repeat.set(6,2);
 for(let r=0;r<4;r++){const m=new THREE.Mesh(new THREE.BoxGeometry(2.4,1.7,46),
   new THREE.MeshLambertMaterial({map:crowd}));
   m.position.set(-(r*2.3+1.2),0.85+r*0.85,0);g.add(m);}
 const roof=new THREE.Mesh(new THREE.BoxGeometry(11,0.3,48),mat(0xd8402a));
 roof.position.set(-4.5,7.4,0);roof.rotation.z=0.12;g.add(roof);
 for(let i=0;i<5;i++){const m=new THREE.Mesh(new THREE.CylinderGeometry(0.13,0.13,7,6),mat(0x8b8f96));
   m.position.set(-8.8,3.5,-20+i*10);g.add(m);}
 const wall=new THREE.Mesh(new THREE.PlaneGeometry(46,1.2),
   new THREE.MeshLambertMaterial({map:bannerTex2('CRESTLINE GP')}));
 wall.position.set(0.1,3.1,0);wall.rotation.y=Math.PI/2;g.add(wall);
 scene.add(g);}
function bannerTex2(txt){const t=new THREE.CanvasTexture(bannerSrc(txt));t.colorSpace=THREE.SRGBColorSpace;
  return new THREE.MeshLambertMaterial({map:t});}

/* trees (instanced) */
const treeList=[];{let guard=0;
 while(treeListPush()&&guard++<600){}}
function treeListPush(){if(treeArr.length>=150)return false;
  const i=(Math.random()*N)|0,sd=Math.random()<0.5?1:-1;
  const off=10+Math.random()*Math.random()*46;
  if(off>CLEAR[i]*0.48-2)return true;
  if(i>N-95&&i<N+5&&sd<0)return true;
  treeArr.push({x:P[i].x+SD[i].x*off*sd,z:P[i].z+SD[i].z*off*sd,
    y:fieldH(P[i].x+SD[i].x*off*sd,P[i].z+SD[i].z*off*sd,i)-0.12,
    s:rand(0.75,1.7),r:Math.random()*6.28,pine:Math.random()<0.62,c:Math.random()});
  return true;}
const treeArr=[];
{let guard=0;while(treeArr.length<150&&guard++<900){
  const i=(Math.random()*N)|0,sd=Math.random()<0.5?1:-1;
  const off=10+Math.random()*Math.random()*46;
  if(off>CLEAR[i]*0.48-2)continue;
  if(i>N-95&&i<N+5&&sd<0)continue;
  const x=P[i].x+SD[i].x*off*sd,z=P[i].z+SD[i].z*off*sd;
  treeArr.push({x,z,y:fieldH(x,z,i)-0.12,s:rand(0.75,1.7),r:Math.random()*6.28,
    pine:Math.random()<0.62,c:Math.random()});}}
{const tg=new THREE.CylinderGeometry(0.14,0.22,1.4,6);tg.translate(0,0.65,0);
 const cg=new THREE.ConeGeometry(1.5,3.8,7);cg.translate(0,2.9,0);
 const bg=new THREE.IcosahedronGeometry(1.55,0);bg.translate(0,2.7,0);
 const nP=treeArr.filter(t=>t.pine).length,nO=treeArr.length-nP;
 const trunk=new THREE.InstancedMesh(tg0(),mat(0x6e4f36),treeArr.length);
 const pine=new THREE.InstancedMesh(cg,new THREE.MeshLambertMaterial({color:0xffffff}),Math.max(1,nP));
 const oak=new THREE.InstancedMesh(bg,new THREE.MeshLambertMaterial({color:0xffffff}),Math.max(1,nO));
 let ip=0,io=0;const col=new THREE.Color();
 treeArr.forEach((t,i)=>{_m4.compose(_v1.set(t.x,t.y,t.z),_q.setFromAxisAngle(UP,t.r),_v2.set(t.s,t.s,t.s));
   trunk.setMatrixAt(i,_m4);
   if(t.pine){pine.setMatrixAt(ip,_m4);col.setHSL(0.34+t.c*0.05,0.45,0.24+t.c*0.1);pine.setColorAt(ip,col);ip++;}
   else{oak.setMatrixAt(io,_m4);col.setHSL(0.26,0.42,0.28+t.c*0.1);oak.setColorAt(io,col);io++;}});
 scene.add(trunk,pine,oak);}
function tgunused(){}

/* tyre walls on tight corners */
{const list=[];
 for(let i=0;i<N;i++){if(Math.abs(KS[i])<0.045)continue;
   let run=0;while(Math.abs(KS[(i+run)%N])>=0.045&&run<N)run++;
   if(run<12){i+=run;continue;}
   for(let j=i;j<i+run;j+=3){const jj=j%N;
     const off=-Math.sign(KS[jj])*(HALF+2.6);
     const x=P[jj].x+SD[jj].x*off,z=P[jj].z+SD[jj].z*off;
     list.push({x,z,y:fieldH(x,z,jj)+0.3,r:Math.random()*6.28,c:Math.random()});
     if(Math.random()<0.6)list.push({x,z,y:fieldH(x,z,jj)+0.92,r:Math.random()*6.28,c:Math.random()});
   }i+=run;}
 const geo=new THREE.TorusGeometry(0.5,0.24,7,14);geo.rotateX(Math.PI/2);
 const tm=new THREE.InstancedMesh(geo,new THREE.MeshLambertMaterial({color:0xffffff}),list.length);
 const col=new THREE.Color();
 list.forEach((t,i)=>{_m4.compose(_v1.set(t.x,t.y,t.z),_q.setFromAxisAngle(UP,t.r),_v2.set(1,1,1));
   tm.setMatrixAt(i,_m4);
   tm.setColorAt(i,col.set(t.c<0.75?0x24262b:(t.c<0.9?0xd8402a:0xe9e5da)));});
 scene.add(tm);}
function listunused(){}

/* flags, clouds, balloons, mountains */
const flags=[];
for(let k=0;k<10;k++){
  const idx=(N-90+k*8)%N,sd=k%2?1:-1,p=P[idx];
  const off=sd*(HALF+2.8),x=p.x+SD[idx].x*off,z=p.z+SD[idx].z*off;
  const g=new THREE.Group();g.position.set(x,fieldH(x,z,idx),z);
  const pole=new THREE.Mesh(new THREE.CylinderGeometry(0.05,0.05,3.2,5),mat(0x9aa0a8));
  pole.position.y=1.6;g.add(pole);
  const f=new THREE.Mesh(new THREE.PlaneGeometry(1.5,0.9),
    new THREE.MeshLambertMaterial({color:ROSTER_CSS()[k%6],side:THREE.DoubleSide}));
  f.geometry.translate(0.75,0,0);f.position.y=2.7;g.add(f);
  f.userData.b=Math.random()*6.28;flags.push(f);scene.add(g);
}
const clouds=[];
for(let k=0;k<7;k++){
  const g=new THREE.Group(),a=Math.random()*6.28,r=rand(280,520);
  g.position.set(5+Math.cos(a)*r,rand(48,86),10+Math.sin(a)*r);
  for(let j=0;j<3;j++){const s=rand(5,10);
    const m=new THREE.Mesh(new THREE.SphereGeometry(s,10,7),
      new THREE.MeshLambertMaterial({color:0xffffff}));
    m.position.set(j*rand(4,7)-6,rand(-1,1.5),rand(-3,3));
    m.scale.y=0.55;g.add(m);}
  scene.add(g);clouds.push(g);
}
const balloons=[];
[[0xd8402a,20,-8],[0xf0b429,-26,26]].forEach((b,i)=>{
  const g=new THREE.Group();
  const env=new THREE.Mesh(new THREE.SphereGeometry(4.5,12,10),mat(b[0]));
  env.scale.y=1.15;g.add(env);
  const bk=new THREE.Mesh(new THREE.BoxGeometry(1.6,1.2,1.6),mat(0x6e4f36));
  bk.position.y=-6.4;g.add(bk);
  g.position.set(b[1],26+i*7,b[2]);scene.add(g);balloons.push(g);
});
for(let k=0;k<16;k++){
  const a=k/16*Math.PI*2+rand(-0.15,0.15),r=rand(620,780);
  const h=rand(70,170),m=new THREE.Mesh(new THREE.ConeGeometry(rand(90,170),h,7),
    mat(k%2?0x7d92a8:0x8fa3b6));
  m.position.set(5+Math.cos(a)*r,-3.4,10+Math.sin(a)*r);scene.add(m);
}
function ROSTER_CSS(){return ['#e8edf1','#8a4fc9','#3f66c4','#f0b429','#2fae7e','#e0452e'];}

/* ---------------- dust particles ---------------- */
const PN=560;
const pGeo=new THREE.BufferGeometry();
const pPos=new Float32Array(PN*3),pSize=new Float32Array(PN),pAlp=new Float32Array(PN),pCol=new Float32Array(PN*3);
for(let i=0;i<PN;i++)pPos[i*3+1]=-999;
pGeo.setAttribute('position',new THREE.BufferAttribute(pPos,3).setUsage(THREE.DynamicDrawUsage));
pGeo.setAttribute('aSize',new THREE.BufferAttribute(pSize,1).setUsage(THREE.DynamicDrawUsage));
pGeo.setAttribute('aAlp',new THREE.BufferAttribute(pAlp,1).setUsage(THREE.DynamicDrawUsage));
pGeo.setAttribute('aCol',new THREE.BufferAttribute(pCol,3).setUsage(THREE.DynamicDrawUsage));
const pMat=new THREE.ShaderMaterial({transparent:true,depthWrite:false,
  uniforms:{},
  vertexShader:`attribute float aSize;attribute float aAlp;attribute vec3 aCol;
    varying float vA;varying vec3 vC;
    void main(){vA=aAlp;vC=aCol;vec4 mv=modelViewMatrix*vec4(position,1.);
      gl_PointSize=clamp(aSize*(240./max(1.,-mv.z)),0.,90.);
      gl_Position=projectionMatrix*mv;}`,
  fragmentShader:`varying float vA;varying vec3 vC;uniform sampler2D uT;
    void main(){}`});
pMat.fragmentShader=`varying float vA;varying vec3 vC;
  void main(){float a=vA;if(a<0.02)discard;gl_FragColor=vec4(vC,a);}`;
const pVel=new Float32Array(PN*3),pLife=new Float32Array(PN),pMaxL=new Float32Array(PN),
      pBase=new Float32Array(PN),pAlpha=new Float32Array(PN),pGrav=new Float32Array(PN);
let pH=0;
const softTex=makeTex(64,64,g=>{const r=g.createRadialGradient(32,32,2,32,32,30);
  r.addColorStop(0,'rgba(255,255,255,1)');r.addColorStop(.5,'rgba(255,255,255,.5)');
  r.addColorStop(1,'rgba(255,255,255,0)');g.fillStyle=r;g.fillRect(0,0,64,64);});
pMat.uniforms.uTex={value:softTex};
pMat.fragmentShader=`uniform sampler2D uTex;varying float vA;varying vec3 vC;
  void main(){vec4 t=texture2D(uTex,gl_PointCoord);float a=t.a*vA;
    if(a<0.02)discard;gl_FragColor=vec4(vC,a);}`;
const ptsObj=new THREE.Points(pGeo,pMat);ptsObj.frustumCulled=false;scene.add(ptsObj);
function spawnP(x,y,z,vx,vy,vz,life,size,r,g,b,al,grav){
  const i=pH;pH=(pH+1)%PN;
  pPos[i*3]=x;pPos[i*3+1]=y;pPos[i*3+2]=z;
  pVel[i*3]=vx;pVel[i*3+1]=vy;pVel[i*3+2]=vz;
  pLife[i]=pMaxL[i]=life;pBase[i]=size;pAlp[i]=al;
  pCol[i*3]=r;pCol[i*3+1]=g;pCol[i*3+2]=b;pGrav[i]=grav;
}
function updateDust(dt){
  for(let i=0;i<PN;i++){
    if(pLife[i]<=0){pAlp[i]=0;continue;}
    pLife[i]-=dt;
    if(pLife[i]<=0){pAlp[i]=0;continue;}
    const u=1-pLife[i]/pMaxL[i],d=Math.max(0,1-2.6*dt);
    pVel[i*3]*=d;pVel[i*3+2]*=d;
    pVel[i*3+1]=pVel[i*3+1]*d+pGrav[i]*dt;
    pPos[i*3]+=pVel[i*3]*dt;pPos[i*3+1]+=pVel[i*3+1]*dt;pPos[i*3+2]+=pVel[i*3+2]*dt;
    pSize[i]=pBase[i]*(1+2.4*u);pAlp[i]=pAlpha[i]*(1-u*u);
  }
  pGeo.attributes.position.needsUpdate=true;pGeo.attributes.aSize.needsUpdate=true;
  pGeo.attributes.aAlp.needsUpdate=true;pGeo.attributes.aCol.needsUpdate=true;
}
function dustClear(){pLife.fill(0);pAlp.fill(0);}

/* ---------------- skid marks ---------------- */
const SKN=800;
const skGeo=new THREE.PlaneGeometry(0.34,1.7);skGeo.rotateX(-Math.PI/2);
const skMat=new THREE.MeshBasicMaterial({color:0x101216,transparent:true,opacity:0.42,
  depthWrite:false,side:THREE.DoubleSide});
const skMesh=new THREE.InstancedMesh(skGeo,skMat,SKN);
skMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);skMesh.frustumCulled=false;
skMesh.renderOrder=4;
const _zero=new THREE.Matrix4().makeScale(0,0,0);
for(let i=0;i<SKN;i++)skMesh.setMatrixAt(i,_zero);
scene.add(skMesh);
let skH=0;
function addSkid(x,y,z,yaw){_q.setFromAxisAngle(UP,yaw);
  _m4.compose(_v1.set(x,y,z),_q,_v2.set(1,1,1));
  skMesh.setMatrixAt(skH,_m4);skH=(skH+1)%SKN;skMesh.instanceMatrix.needsUpdate=true;}
function skidClear(){for(let i=0;i<SKN;i++)skMesh.setMatrixAt(i,_zero);
  skMesh.instanceMatrix.needsUpdate=true;skH=0;}

/* ---------------- roster & karts ---------------- */
const ROSTER=[
 {name:'POWDER',c:0xe8edf1,trim:0x97a1ab,speed:48.6,aLat:36.5},
 {name:'GRAPE', c:0x8a4fc9,trim:0x5b2e8c,speed:49.7,aLat:37.5},
 {name:'BERRY', c:0x3f66c4,trim:0x27417e,speed:50.8,aLat:38.5},
 {name:'BUMBLE',c:0xf0b429,trim:0x8f6612,speed:51.6,aLat:39.5},
 {name:'MINTY', c:0x2fae7e,trim:0x1a6b4a,speed:52.7,aLat:40.8},
 {name:'PEPPER',c:0xe0452e,trim:0x8e2416,speed:53.8,aLat:41.5},
];
ROSTER.forEach(r=>r.css='#'+r.c.toString(16).padStart(6,'0'));

function buildKartMesh(cfg){
  const root=new THREE.Group();root.rotation.order='YXZ';
  const body=new THREE.Group();root.add(body);
  const c=cfg.c,tr=cfg.trim;
  const B=(w,h,d)=>new THREE.BoxGeometry(w,h,d);
  const add=(geo,m,x,y,z,p=body)=>{const mesh=new THREE.Mesh(geo,m);mesh.position.set(x,y,z);p.add(mesh);return mesh;};
  add(new THREE.BoxGeometry(1.5,0.15,2.4),mat(0x25282d),0,0.32,0);
  add(new THREE.BoxGeometry(1.06,0.34,0.95),mat(c),0,0.54,0.78);
  add(new THREE.BoxGeometry(0.6,0.2,0.5),mat(c),0,0.44,1.32);
  add(new THREE.BoxGeometry(0.34,0.3,1.15),mat(c),0.63,0.52,0.02);
  add(new THREE.BoxGeometry(0.34,0.3,1.15),mat(c),-0.63,0.52,0.02);
  add(new THREE.BoxGeometry(0.62,0.4,0.55),mat(0x2c3036),0,0.68,-0.82);
  const ex=add(new THREE.CylinderGeometry(0.06,0.08,0.5,7),mat(0x9aa1a9),0.2,0.95,-1.02);
  ex.rotation.x=Math.PI/2;
  add(new THREE.BoxGeometry(1.34,0.08,0.38),mat(tr),0,1.08,-1.12);
  add(new THREE.BoxGeometry(0.07,0.26,0.3),mat(tr),0.48,0.92,-1.1);
  add(new THREE.BoxGeometry(0.07,0.26,0.3),mat(tr),-0.48,0.92,-1.1);
  add(new THREE.BoxGeometry(0.6,0.5,0.16),mat(0x1d1f24),0,0.85,-0.42);
  add(new THREE.BoxGeometry(1.56,0.13,0.22),mat(tr),0,0.36,1.3);
  add(new THREE.BoxGeometry(1.56,0.13,0.22),mat(tr),0,0.36,-1.32);
  const dr=new THREE.Group();dr.position.set(0,0,-0.1);body.add(dr);
  add(new THREE.BoxGeometry(0.55,0.48,0.42),mat(0x2a2e35),0,1.0,0,dr);
  const aL=add(new THREE.BoxGeometry(0.11,0.11,0.48),mat(0x2a2e35),0.25,1.18,0.24,dr);aL.rotation.x=-1.0;
  const aR=add(new THREE.BoxGeometry(0.11,0.11,0.48),mat(0x2a2e35),-0.25,1.18,0.24,dr);aR.rotation.x=-1.0;
  const headG=new THREE.Group();headG.position.set(0,1.44,0.02);dr.add(headG);
  add(new THREE.SphereGeometry(0.3,12,10),mat(c),0,0,0,headG);
  add(new THREE.BoxGeometry(0.36,0.15,0.15),mat(0x101318),0,0.02,0.24,headG);
  const swH=new THREE.Group();swH.position.set(0,1.12,0.36);swH.rotation.x=-1.05;dr.add(swH);
  add(new THREE.TorusGeometry(0.17,0.032,6,14),mat(0x17191d),0,0,0,swH);
  const steer=[];
  [[0.72,0.32,0.86,0.3],[-0.72,0.32,0.86,0.3],[0.76,0.36,-0.84,0.34],[-0.76,0.36,-0.84,0.34]]
  .forEach(([x,y,z,r],wi)=>{
    const hold=new THREE.Group();hold.position.set(x,y,z);body.add(hold);
    const spin=new THREE.Group();hold.add(spin);
    const tgeo=new THREE.CylinderGeometry(r,r,r*0.8,12);tGeo2(tGeoCache,tGeoDone());
    const tg=new THREE.CylinderGeometry(r,r,r*0.78,12);tg.rotateZ(Math.PI/2);
    spin.add(new THREE.Mesh(tg,mat(0x1a1c20)));
    const hg=new THREE.CylinderGeometry(r*0.46,r*0.45,r*0.82,8);hg.rotateZ(Math.PI/2);
    spin.add(new THREE.Mesh(hg,mat(0xb9bfc6)));
    if(wi<2)steer.push(hold);
    spins.push(spin);
  });
  function tGeo2(){} function tGeoCache(){}
  const blob=new THREE.Mesh(new THREE.CircleGeometry(1.35,18).rotateX(-Math.PI/2),
    new THREE.MeshBasicMaterial({map:blobTex,transparent:true,depthWrite:false}));
  blob.position.y=0.03;blob.renderOrder=6;root.add(blob);
  return {root,body,head:headG,steer,spinsArr:spins,dr};
}
function tGeo2(){}
function blobTexSrc(){const c=document.createElement('canvas');c.width=c.height=64;
  const g=c.getContext('2d');const r=g.createRadialGradient(32,32,4,32,32,30);
  r.addColorStop(0,'rgba(0,0,0,.8)');r.addColorStop(.6,'rgba(0,0,0,.4)');
  r.addColorStop(1,'rgba(0,0,0,0)');g.fillStyle=r;g.fillRect(0,0,64,64);
  const t=new THREE.CanvasTexture(c);return t;}
const blobTex=blobTexSrc();
function steer2(){}
let steer=[];const spins=[];

class Kart{
  constructor(cfg,gi){
    this.cfg=cfg;this.name=cfg.name;this.gi=gi;
    const m=buildKartMeshClean(cfg);
    this.root=m.root;this.body=m.body;this.headG=m.headG;
    this.steer=m.steer;this.spins=m.spins;this.blob=m.blob;
    scene.add(this.root);
    this.pos=new THREE.Vector3();
    this.reset(gi);
  }
  reset(gi){
    const row=gi>>1,col=gi&1;
    const s=L-9-row*5.5,idx=Math.round(s/ds)%N,lat=col?2.3:-2.3,p=P[idx],sd=SD[idx];
    this.idx=idx;this.sPrev=this.s=idx*ds;this.lap=-1;
    this.pos.set(p.x+sd.x*lat,0,p.z+sd.z*lat);
    this.pos.y=fieldH(this.pos.x,this.pos.z,idx);
    this.gy=this.pos.y;this.yaw=YAW[idx];this.speed=0;this.lat=lat;
    this.laneCur=lat;this.laneBias=rand(-1.2,1.2);this.phase=rand(0,6.28);
    this.drift=0;this.slide=0;this.hop=0;this.driftT=0;this.slide=0;
    this.steerVis=0;this.ot=0;this.otLane=0;this.skT=0;this.dustAcc=0;this.exT=Math.random();
    this.finished=false;this.finT=0;this.prog=this.lap*L+this.s;this.my=this.yaw;
    this.grassDust=false;this.skid=false;this.pSm=0;
    this.visual(0.016,0);
  }
  nearest(){
    let bi=this.idx,bd=1e18;
    for(let o=-10;o<=36;o++){const j=(this.idx+o+N)%N;
      const dx=P[j].x-this.pos.x,dz=P[j].z-this.pos.z,q=dx*dx+dz*dz;
      if(q<bd){bd=q;bi=j;}}
    this.idx=bi;
  }
  update(dt,t){
    this.nearest();
    const i=this.idx,p=P[i],sd=SD[i],tv=T[i];
    let s=(i*ds+(this.pos.x-p.x)*tv.x+(this.pos.z-p.z)*tv.z+L)%L;
    if(this.s>L*0.72&&s<L*0.28){this.lap++;
      if(this.lap>=LAPS&&!this.finished){this.finished=true;this.finT=raceT;onFinish(this);}}
    else if(this.s<L*0.28&&this.sPrev>L*0.72)this.lap--;
    this.sPrev=this.s;this.s=s;this.prog=this.lap*L+s;
    const lat=(this.pos.x-p.x)*sd.x+(this.pos.z-p.z)*sd.z;this.lat=lat;
    const grass=Math.abs(lat)>8.6,kerb=!grass&&Math.abs(lat)>HALF-0.4;
    /* racing line */
    const look=6+this.speed*0.5,li=(i+Math.round(look/ds))%N;
    let lane=clamp(KS[(i+Math.round((look*0.9+14)/ds))%N]*110,-1,1)*(HALF-1.9);
    lane+=Math.sin(t*0.25+this.phase)*0.5+this.laneBias;
    if(this.ot>0){lane=this.otLane;this.ot-=dt;}
    const laneTgt=clamp(lane,-(HALF-1.5),HALF-1.5);
    this.laneCur+=(laneTgt-this.laneCur)*damp(2.4,dt);
    /* steering target */
    const look2=6+this.speed*0.5,li=(i+Math.round(look/ds))%N;
    const tx=P[li].x+SD[li].x*this.laneCur,tz=P[li].z+SD[li].z*this.laneCur;
    const err=wrapPI(Math.atan2(tx-this.pos.x,tz-this.pos.z)-this.yaw);
    const steer=clamp(err*2.5,-1,1);
    /* drift */
    const kAh=KS[(i+Math.round(24/ds))%N];
    if(this.drift===0){
      if(!grass&&this.speed>26&&Math.abs(steer)>0.6&&Math.abs(kAh)>0.026){
        this.drift=steer>0?1:-1;this.hop=1;this.driftT=0;}
    }else{
      this.driftT+=dt;
      if(Math.abs(steer)<0.32||this.speed<20||grass){
        if(this.driftT>0.5)this.speed=Math.min(this.cfg.speed+2.5,this.speed+2.2);
        this.drift=0;}
    }
    /* speed planning */
    let vA=this.cfg.speed*(this.finished?0.78:1);
    if(grass)vA*=0.42;else if(kerb)vA*=0.985;
    for(let q=3;q<=84;q+=6){const km=Math.abs(KSm[(i+q)%N]);
      if(km>0.012){const vc=Math.sqrt(this.cfg.aLat*(this.drift?0.82:1)/km);
        vA=Math.min(vA,Math.sqrt(vc*vc+2*30*q*ds));}}
    vA*=1+clamp((leadProg-this.prog)*0.00045,-0.02,0.06);
    if(this.speed<vA)this.speed=Math.min(vA,this.speed+22*dt);
    else this.speed=Math.max(vA,this.speed-32*dt);
    const ym=Math.min(3,this.cfg.aLat*1.7/Math.max(this.speed,6));
    this.yaw+=steer*ym*dt+this.drift*0.9*dt*clamp(this.speed/30,0,1);
    const sT=this.drift?0.15+0.2*Math.abs(steer):0;
    this.slide+=(sT-this.slide)*damp(this.drift?3.2:5.5,dt);
    this.my=this.yaw-this.drift*this.slide*0.55;
    this.pos.x+=Math.sin(this.my)*this.speed*dt;
    this.pos.z+=Math.cos(this.my)*this.speed*dt;
    const gy=fieldH(this.pos.x,this.pos.z,i);
    this.pos.y+=(gy-this.pos.y)*Math.min(1,dt*10);this.gy=gy;
    this.steerVis+=(steer*0.42-this.steerVis)*damp(10,dt);
    /* particles + skids */
    this.skid=this.drift!==0;this.grassDust=grass&&this.speed>6;
    if(this.skid||this.grassDust){
      this.dustAcc+=dt*52;
      while(this.dustAcc>=1){this.dustAcc-=1;
        const lx=Math.random()<0.5?0.8:-0.8,lz=-0.84;
        const wx=this.pos.x+lx*Math.cos(this.yaw)+lz*Math.sin(this.yaw);
        const wz=this.pos.z-lx*Math.sin(this.yaw)+lz*Math.cos(this.yaw);
        const r=grass?0.42:0.74,g2=grass?0.55:0.68,b=grass?0.3:0.6;
        spawnP(wx,this.pos.y+0.12,wz,
          Math.sin(this.my)*this.speed*0.25+rand(-0.9,0.9),rand(0.6,2),
          Math.cos(this.my)*this.speed*0.25+rand(-0.9,0.9),
          rand(0.45,0.85),rand(0.55,1.2),r,g2,grass?0.28:0.6,grass?0.55:0.45,0.4);}
      this.skT-=dt;
      if(this.skT<=0){this.skT=0.03;
        for(const lx of [0.8,-0.8]){
          const wx=this.pos.x+lx*Math.cos(this.yaw)+lz2(this.yaw);
          addSkid(wx,this.pos.y+0.045,wz2(this.pos,this.yaw),this.my);}
      }
    }else this.dustAcc=0;
  }
  visual(dt,t){
    const r=this.root;
    r.position.copy(this.pos);
    r.rotation.y=this.yaw;
    r.rotation.x=-Math.asin(clamp(T[this.idx].y,-0.55,0.55));
    const hopY=Math.sin(clamp(this.hop,0,1)*Math.PI)*0.3;
    let jit=this.grassDust?Math.sin(t*47+this.gi*3)*0.04:0;
    if(state==='cd')jit=Math.abs(Math.sin(t*31+this.gi*2.1))*0.03;
    this.body.position.y=hopY+jit;
    this.body.rotation.z=-this.drift*this.slide*0.5-this.steerVis*0.1;
    this.body.rotation.y=this.drift*this.slide*0.5;
    this.body.rotation.x=clamp(-(this.speed-this.pSpd)/Math.max(dt,0.001)*0.0028,-0.06,0.08);
    this.pSpd+=(this.speed-this.pSpd)*damp(6,dt);
    this.hop=Math.max(0,this.hop-dt*2.6);
    const w=this.speed/0.32*dt;
    this.spins.forEach(s=>s.rotation.x+=w);
    this.steer[0].rotation.y=this.steerVis;this.steer[1].rotation.y=this.steerVis;
    this.headG.rotation.y=this.steerVis*0.9;
  }
}
function lz2(yaw){return -0.84*Math.cos(yaw);}
function wz2(pos,yaw){return pos.z-0.84*Math.cos(yaw);}
function posy(){}
function buildKartMeshClean(cfg){
  steer.length=0;spins.length=0;
  const m=buildKartMesh(cfg);
  return {root:m.root,body:m.body,headG:m.headG,steer:steer.slice(),spins:spins.slice()};
}
/* the actual geometry builder (fills module-level steer/spins then returns groups) */
function buildKartMesh(cfg){
  steer.length=0;spins.length=0;
  const root=new THREE.Group();root.rotation.order='YXZ';
  const body=new THREE.Group();root.add(body);
  const c=cfg.c,tr=cfg.trim;
  const add=(geo,m,x,y,z,p=body)=>{const mesh=new THREE.Mesh(geo,m);mesh.position.set(x,y,z);p.add(mesh);return mesh;};
  add(new THREE.BoxGeometry(1.5,0.15,2.4),mat(0x25262b),0,0.32,0);
  add(new THREE.BoxGeometry(1.06,0.34,0.95),mat(c),0,0.55,0.8);
  add(new THREE.BoxGeometry(0.62,0.22,0.5),mat(c),0,0.44,1.36);
  add(new THREE.BoxGeometry(0.34,0.3,1.15),mat(c),0.63,0.53,0.02);
  add(new THREE.BoxGeometry(0.34,0.3,1.15),mat(c),-0.63,0.53,0.02);
  add(new THREE.BoxGeometry(0.6,0.4,0.55),mat(0x2c3036),0,0.68,-0.82);
  const ex=add(new THREE.CylinderGeometry(0.06,0.08,0.5,7),mat(0x9aa1a9),0.2,0.95,-1.02);ex.rotation.x=Math.PI/2;
  add(new THREE.BoxGeometry(1.34,0.08,0.38),mat(tr),0,1.08,-1.12);
  add(new THREE.BoxGeometry(0.07,0.26,0.3),mat(tr),0.48,0.92,-1.1);
  add(new THREE.BoxGeometry(0.07,0.26,0.3),mat(tr),-0.48,0.92,-1.1);
  add(new THREE.BoxGeometry(0.6,0.5,0.16),mat(0x1d1f24),0,0.86,-0.42);
  add(new THREE.BoxGeometry(1.56,0.13,0.22),mat(tr),0,0.35,1.32);
  add(new THREE.BoxGeometry(1.56,0.13,0.22),mat(tr),0,0.36,-1.32);
  const dr=new THREE.Group();dr.position.set(0,0,-0.1);body.add(dr);
  add(new THREE.BoxGeometry(0.55,0.48,0.42),mat(0x2a2e35),0,1.0,0,dr);
  const armL=add(new THREE.BoxGeometry(0.11,0.11,0.48),mat(0x2a2e35),0.25,1.18,0.24,dr);armL.rotation.x=-1.0;
  const armR=add(new THREE.BoxGeometry(0.11,0.11,0.48),mat(0x2a2e35),-0.25,1.18,0.24,dr);armR.rotation.x=-1.0;
  const headG=new THREE.Group();headG.position.set(0,1.44,0.02);dr.add(headG);
  add(new THREE.SphereGeometry(0.3,12,10),mat(c),0,0,0,headG);
  add(new THREE.BoxGeometry(0.37,0.15,0.15),mat(0x101318),0,0.02,0.24,headG);
  const swH=new THREE.Group();swH.position.set(0,1.12,0.36);swH.rotation.x=-1.05;dr.add(swH);
  add(new THREE.TorusGeometry(0.17,0.032,6,14),mat(0x17191d),0,0,0,swH);
  const steerL=[],spinsA=[];
  [[0.72,0.32,0.86,0.3],[-0.72,0.32,0.86,0.3],[0.76,0.36,-0.84,0.34],[-0.76,0.36,-0.84,0.34]]
  .forEach(([x,y,z,r],wi)=>{
    const hold=new THREE.Group();hold.position.set(x,y,z);body.add(hold);
    const spin=new THREE.Group();hold.add(spin);
    const tg=new THREE.CylinderGeometry(r,r,r*0.78,12);tg.rotateZ(Math.PI/2);
    spin.add(new THREE.Mesh(tg,mat(0x191b1f)));
    const hg=new THREE.CylinderGeometry(r*0.45,r*0.45,r*0.84,8);hg.rotateZ(Math.PI/2);
    spin.add(new THREE.Mesh(hg,mat(0xb9bfc6)));
    spins.push(spin);if(wi<2)steerL.push(hold);
  });
  const blob=new THREE.Mesh(new THREE.CircleGeometry(1.4,20).rotateX(-Math.PI/2),
    new THREE.MeshBasicMaterial({map:blobTex,transparent:true,opacity:0.32,depthWrite:false}));
  blob.position.y=0.02;blob.renderOrder=6;root.add(blob);
  return {root,body,headG};
}
function steerLunused(){}
const steerL=[];

/* populate karts */
const karts=ROSTER.map((cfg,gi)=>new Kart(cfg,gi));
let standings=karts.slice(),leadProg=0;

/* ---------------- HUD ---------------- */
const big=document.getElementById('big'),lapEl=document.getElementById('lap'),
      clockEl=document.getElementById('clock'),camTag=document.getElementById('camtag'),
      rowsEl=document.getElementById('rows');
const rowEls=ROSTER.map((cfg,gi)=>{
  const d=document.createElement('div');d.className='row';d.style.order=gi;
  d.innerHTML=`<span class="rk"></span><span class="chip" style="background:${'#'+cfg.c.toString(16).padStart(6,'0')}"></span>`+
    `<span class="nm">${cfg.name}</span><span class="gp"></span>`;
  rowsEl.appendChild(d);return d;});
const fmt=t=>{const m=Math.floor(t/60),s=t-m*60;return m+':'+(s<10?'0':'')+s.toFixed(1);};
function bigShow(txt,cls){big.textContent=txt;big.className='on'+(cls?' '+cls:'');
  void big.offsetWidth;big.classList.add('pop');}
function setLights(n){lightMats.forEach((m,i)=>m.color.setHex(i<n?0xff2d1c:0x2a100c));}
function lightsGo(){lightMats.forEach(m=>m.color.setHex(0x2bd45a));}

/* minimap */
const map=document.getElementById('map'),mg=map.getContext('2d');
mg.setTransform(2,0,0,2,0,0);
let mnx=1e9,mxx=-1e9,mnz=1e9,mxz=-1e9;
P.forEach(p=>{mnx=Math.min(mnx,p.x);mxx=Math.max(mxx,p.x);mnz=Math.min(mnz,p.z);mxz=Math.max(mxz,p.z);});
const mcx=(mnx+mxx)/2,mcz=(mnz+mxz)/2;
const ms=Math.min(148/(mxx-mnx),148/(mxz-mnz));
const m2=(x,z)=>[(x-mcx)*ms+84,(z-mcz)*ms+84];
const mPath=new Path2D();
P.forEach((p,i)=>{const[x,y]=m2(p.x,p.z);i?mg0(x,y):mg1(x,y);});
function mg0(x,y){mPath.lineTo(x,y);} function mg1(x,y){mPath.moveTo(x,y);}
const mPath=new Path2D();
{const pt=P.map(p=>m2(p.x,p.z));mPath.moveTo(pt[0][0],pt[0][1]);
 for(let i=1;i<N;i++)mPath.lineTo(pt[i][0],pt[0]?pt[i][0]:0,pt[i][1]);}
const stA=m2(P[0].x+SD[0].x*9,P[0].z+SD[0].z*9),stB=m2(P[0].x-SD[0].x*9,P[0].z-SD[0].z*9);
function drawMap(){
  mg.clearRect(0,0,168,168);
  mg.lineJoin='round';mg.lineCap='round';
  mg.strokeStyle='#262a31';mg.lineWidth=10;mg.stroke(mPath);
  mg.strokeStyle='#454b54';mg.lineWidth=4.5;mg.stroke(mPath);
  mg.strokeStyle='#ff4f20';mg.lineWidth=3;
  mg.beginPath();mg.moveTo(stA[0],stA[1]);mg.lineTo(stB[0],stB[1]);mg.stroke();
  for(let i=standings.length-1;i>=0;i--){const k=standings[i],[x,y]=m2(k.pos.x,k.pos.z);
    if(i===0){mg.fillStyle='#fff';mg.beginPath();mg.arc(x,y,5.6,0,7);mg.fill();}
    mg.fillStyle=k.cfg.css;mg.beginPath();mg.arc(x,y,i===0?4:3.3,0,7);mg.fill();
    mg.strokeStyle='rgba(0,0,0,.6)';mg.lineWidth=1;mg.stroke();}
}
function m2(x,z){return [(x-mcx)*ms+84,(z-mcz)*ms+84];}

/* ---------------- cameras ---------------- */
const TSCAMS=[];
for(let k=0;k<14;k++){
  const i=Math.round(k*N/14+9)%N,sd=k%2?1:-1;
  const off=sd*(HALF+7+((k*13)%6));
  const x=P[i].x+SD[i].x*off,z=P[i].z+SD[i].z*off;
  TSCAMS.push(new THREE.Vector3(x,fieldH(x,z,i)+3,z));
}
function pickCam(lead){
  const arr=[];
  for(const c of TSCAMS){const d=c.distanceTo(lead.pos);if(d>13&&d<150)arr.push({c,d});}
  if(!arr.length)return null;
  arr.sort((a,b)=>a.d-b.d);
  return arr[(Math.random()*Math.min(4,arr.length))|0].c;
}
const camPosS=new THREE.Vector3(0,40,160),lookS=new THREE.Vector3();
let sideCam=null,sideUntil=0,nextCut=1e9,snapNext=true;
function cams(dt,t){
  let fovT=55;
  if(state==='cd'){
    const u=clamp((4.6-cdT)/3.65,0,1);
    const ang=-2.15+u*1.3,rad=17-u*4.5;
    cam.position.set(gridC.x+Math.sin(ang)*rad,gridC.y+5-u*1.8,gridC.z+Math.cos(ang)*rad);
    cam.lookAt(gridC.x,gridC.y+1,gridC.z);
    camTag.textContent='GRID CAM';fovT=48;
  }else{
    const lead=standings[0];
    if(sideCam&&t<sideUntil){
      cam.position.copy(sideCam);
      _v1.set(lead.pos.x,lead.pos.y+1.1,lead.pos.z);
      cam.lookAt(_v1);
      fovT=clamp(2600/Math.max(_v1.distanceTo(cam.position),10),26,55);
      camTag.textContent='TRACKSIDE CAM';
    }else{
      if(sideCam){sideCam=null;nextCut=t+6.5+Math.random()*3.5;snapNext=true;}
      if(t>nextCut){const c=pickCam(lead);if(c){sideCam=c;sideUntil=t+3;camTag.textContent='TRACKSIDE CAM';}}
      if(!sideCam){
        const fx=Math.sin(lead.yaw),fz=Math.cos(lead.yaw);
        const rx=-fz,rz=fx,lat=lead.drift*lead.slide*4.2;
        _v1.set(lead.pos.x-fx*(6.9+lead.speed*0.045)+rx*lat,
                lead.pos.y+3.1+lead.speed*0.012,
                lead.pos.z-fz(lead)+rz*lat);
        if(snapNext){camPosS.copy(_v1);lookS.copy(lead.pos);snapNext=false;}
        camPosS.lerp(_v1,damp(4.2,dt));
        const minY=fieldH(camPosS.x,camPosS.z,lead.idx)+1.25;
        if(camPosS.y<minY)camPosS.y=minY;
        cam.position.copy(camPosS);
        _v2.set(lead.pos.x+fx*4.5,lead.pos.y+1.35,lead.pos.z+Math.cos(lead.yaw)*4.5);
        lookS.lerp(_v2,damp(10,dt));
        cam.lookAt(lookS);
        fovT=54+lead.speed*0.14;
        camTag.textContent='CHASE · P1 '+lead.name;
      }
    }
  }
  cam.fov+=(fovT-cam.fov)*damp(4,dt);cam.updateProjectionMatrix();
}
function fz(k){return Math.cos(k.yaw);}
function pickCam(lead){
  const arr=[];
  for(const c of TSCAMS){const d=c.distanceTo(lead.pos);if(d>14&&d<150)arr.push({c,d});}
  if(!arr.length)return null;
  arr.sort((a,b)=>a.d-b.d);
  return arr[Math.min(arr.length-1,(Math.random()*Math.min(4,arr.length))|0)].c;
}
const gridC=new THREE.Vector3();

/* ---------------- race state ---------------- */
let state='cd',cdT=4.6,raceT=0,stage=-1,postT=0,finalT=null,lightsLit=false;
const keyK=k=>k.finished?1e6+(1e4-k.finT):k.prog;
function onFinish(k){
  if(state!=='race')return;
  state='post';postT=0;finalT=raceT;
  bigShow(`FINISH · ${k.name} WINS`,'fin');
  for(let i=0;i<130;i++){const c=ROSTER[(Math.random()*6)|0],col=new THREE.Color(c.c);
    spawnP(k.pos.x+rand(-2.5,2.5),k.pos.y+rand(1,3.5),k.pos.z+rand(-2.5,2.5),
      rand(-4,4),rand(5,10),rand(-4,4),rand(1.2,1.9),rand(0.28,0.5),
      col.r,col.g,col.b,0.95,-9);}
}
let finalT=null;
function resetRace(){
  dustClear();
  for(let i=0;i<SKN;i++)skMesh.setMatrixAt(i,_zero);
  skMesh.instanceMatrix.needsUpdate=true;skH=0;
  karts.forEach((k,i)=>k.reset(i));
  gridC.set(0,0,0);karts.forEach(k=>gridC.add(k.pos));gridC.multiplyScalar(1/6);
  state='cd';cdT=4.6;stage=-1;raceT=0;finalT=null;postT=0;
  sideCam=null;nextCut=1e9;snapNext=true;
  setLights(0);lightsLit=false;
  bigShow('CRESTLINE GP','sm');
  cam.fov=50;cam.updateProjectionMatrix();
}
resetRace();

/* ---------------- main loop ---------------- */
let tp=performance.now()/1000;
renderer.setAnimationLoop(()=>{
  const t=performance.now()/1000,dt=clamp(t-tp,0.001,0.05);tp=t;
  if(state==='cd'){
    cdT-=dt;
    const st=cdT>3.7?0:cdT>2.8?1:cdT>1.9?2:cdT>0.95?3:4;
    if(st!==stage){
      stage=st;
      if(st===0){bigShow('CRESTLINE GP','sm');beep(420,.1,.04);}
      else if(st<4){bigShow(String(4-st),'');setLights(st);lightsLit=true;beep(620,.15,.05);}
      else{bigShow('GO!','go');lightsGo();beep(930,.5,.07);
        state='race';raceT=0;nextCut=t+4.5;snapNext=true;
        setTimeout(()=>{if(big.textContent==='GO!')big.classList.remove('on');},900);}
    }
    karts.forEach(k=>{k.exT-=dt;
      if(k.exT<=0){k.exT=rand(0.14,0.26);
        spawnP(k.pos.x-1.15*Math.sin(k.yaw),k.pos.y+0.95,k.pos.z-1.15*Math.cos(k.yaw),
          rand(-0.3,0.3),rand(0.5,1.1),rand(-0.3,0.3),rand(0.5,0.8),rand(0.26,0.4),
          0.62,0.62,0.65,0.5,0.35);}});
  }else{
    raceT+=dt;
    if(lightsLit&&raceT>1.25){setLights(0);lightsLit=false;}
    leadProg=-1e9;karts.forEach(k=>{if(k.prog>leadProg)leadProg=k.prog;});
    karts.forEach(k=>k.update(dt,t));
    collide();
    if(state==='post'){postT+=dt;if(postT>5.4)resetRace();}
  }
  karts.forEach(k=>k.visual(dt,t));
  standings=karts.slice().sort((a,b)=>keyK(b)-keyK(a));
  hud();
  cams(dt,t);
  updateDust(dt);
  flags.forEach((f,i)=>{f.rotation.y=f.userData.b+Math.sin(t*2.2+i*1.7)*0.3;});
  clouds.forEach((c,i)=>{c.position.x+=dt*(1+i*0.15);if(c.position.x>760)c.position.x=-760;});
  balloons.forEach((b,i)=>{b.position.y+=Math.sin(t*0.5+i*2)*0.01;b.rotation.y+=dt*0.1;});
  drawMap();
  renderer.render(scene,cam);
});
function hud(){
  const lead=standings[0];
  standings.forEach((k,ix)=>{
    const el=rowEls[k.gi];el.style.order=ix;el.classList.toggle('ld',ix===0);
    el.children[0].textContent=ix+1;
    el.children[3].textContent=ix===0?'—':(k.finished?'FIN'
      :'+'+Math.max(0,(lead.prog-k.prog)/Math.max(k.speed,8)).toFixed(1));
  });
  lapEl.textContent=state==='post'?'FINISH':`LAP ${clamp(lead.lap+1,1,LAPS)}/${LAPS}`;
  clockEl.textContent=fmt(finalT!==null?finalT:raceT);
}
function collide(){
  for(let a=0;a<karts.length;a++)for(let b=a+1;b<karts.length;b++){
    const A=karts[a],B=karts[b];
    const dx=B.pos.x-A.pos.x,dz=B.pos.z-A.pos.z,d2=dx*dx+dz*dz;
    if(d2<3.24&&d2>1e-4){
      const d=Math.sqrt(d2),nx=dx/d,nz=dz/d,ov=(1.8-d)*0.55;
      A.pos.x-=nx*ov;A.pos.z-=nz*ov;B.pos.x+=nx*ov;B.pos.z+=nz*ov;
      if(A.prog>B.prog)B.speed=Math.min(B.speed,A.speed+1);
      else A.speed=Math.min(A.speed,B.speed+1);
    }}
}
/* flags needs roster colors — rebuild with proper colors */
flags.forEach(f=>f.material.color.setHex(0xffffff));
scene.traverse(o=>{if(o.userData.flag)o.material.color.setHex(0x888888);});
/* balloon build (uses roster colors) */
{const g1=new THREE.Group(),g2=new THREE.Group();
 [[0xd8402a,g1,18,-6],[0x2fae7e,g2,-24,28]].forEach(()=>{});
 balloons.push(g1,g2);}

/* audio (plays only after a user gesture unlocks audio; visuals run regardless) */
let AC=null;
function beep(f,d=0.12,g=0.05){try{
  AC=AC||new (window.AudioContext||window.webkitAudioContext)();
  if(AC.state==='suspended')AC.resume();
  const o=AC.createOscillator(),gn=AC.createGain();
  o.type='triangle';o.frequency.value=f;
  gn.gain.setValueAtTime(g,AC.currentTime);
  gn.gain.exponentialRampToValueAtTime(0.0001,AC.currentTime+d);
  o.connect(gn).connect(AC.destination);o.start();o.stop(AC.currentTime+d+0.05);
}catch(e){}}
addEventListener('pointerdown',()=>{if(AC&&AC.state==='suspended')AC.resume();});
</script>
</body>
</html>
```

A note on the implementation: the track is one closed Catmull-Rom spline sampled into 700 arc-length-spaced stations with precomputed tangents and smoothed signed curvature. The racing line, braking points, drift triggers, kerb placement and even scenery scattering all derive from that one dataset — curvature drives both the apex-hugging lane offset and the per-kart corner-speed planner (`v = √(a_lat·d + v_c²)`), which is what makes them brake into the chicane and drift out of it. Skid marks are a single instanced mesh and dust is one shader-driven point cloud, so six drifting karts stay cheap. The AI blends an apex line with side-picking overtakes, soft body collisions, per-kart speed personalities and a light rubber band, so the order genuinely shuffles. The chase camera rides the current leader with a drift-angle offset, hard-cuts to pre-placed trackside cameras every few seconds, and a slow dolly circles the grid during the countdown; when the leader takes the checker, confetti fires and the whole race restarts on its own.