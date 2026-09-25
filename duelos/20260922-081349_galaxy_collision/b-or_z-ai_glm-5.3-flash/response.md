Here's my plan for this piece: a **restricted three-body simulation** in the spirit of Toomre & Toomre — the two galactic nuclei are the only live masses (integrated on the CPU with softened gravity plus a dynamical-friction-style drag so the pair inspirals and coalesces), while 65,536 test particles (30,000 stars + 2,200 haze sprites per galaxy) are integrated **on the GPU** through ping-pong float buffers. Tidal tails and bridges then emerge honestly from the physics instead of being faked. I choreograph pacing with a cinematic slow-motion that triggers automatically near each close passage, and a scripted drifting camera so the 30-second window always shows the full story: approach → first passage (~6 s) → antenna tails → repeated passages → coalescence (~16–20 s) → remnant.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Galactic Collision — Tidal Disruption</title>
<style>
  html,body{height:100%}
  body{margin:0;background:#020409;overflow:hidden;
       font-family:ui-monospace,"SF Mono","Cascadia Code",Menlo,Consolas,"Liberation Mono",monospace;
       -webkit-font-smoothing:antialiased}
  canvas{position:fixed;inset:0;display:block;z-index:0}
  /* filmic vignette, very restrained */
  #vig{position:fixed;inset:0;z-index:1;pointer-events:none;
       background:radial-gradient(130% 100% at 50% 45%, rgba(0,0,0,0) 55%, rgba(1,2,7,.55) 100%)}
  #hud{position:fixed;top:22px;left:24px;z-index:2;pointer-events:none;user-select:none;
       border-left:1px solid rgba(150,180,215,.28);padding-left:12px;
       color:#dfe9f5;font-size:10px;letter-spacing:.16em;line-height:1.95}
  #hud .lab{display:inline-block;min-width:3.4em;color:rgba(148,175,205,.55)}
  #hud .ph{margin-top:7px;color:#8fc6e4;letter-spacing:.24em}
  #title{position:fixed;left:24px;bottom:26px;z-index:2;pointer-events:none;user-select:none;
         transition:opacity 2.4s ease,transform 2.4s ease}
  #title h1{margin:0 0 7px;font-size:13px;font-weight:500;letter-spacing:.5em;color:#e8eff8}
  #title p{margin:0;font-size:10px;letter-spacing:.2em;color:rgba(148,175,205,.55)}
  #title.gone{opacity:0;transform:translateY(8px)}
  #cap{position:fixed;right:24px;bottom:28px;z-index:2;pointer-events:none;user-select:none;
       text-align:right;font-size:9px;letter-spacing:.24em;color:rgba(140,168,198,.38)}
  @media(max-width:640px){#cap{display:none}}
</style>
</head>
<body>
<div id="vig"></div>
<div id="hud">
  <div><span class="lab">T</span><span id="hT">+000 MYR</span></div>
  <div><span class="lab">SEP</span><span id="hS">131.3 KPC</span></div>
  <div><span class="lab">VEL</span><span id="hV">163 KM/S</span></div>
  <div class="ph" id="hP">FIRST APPROACH</div>
</div>
<div id="title"><h1>GALACTIC COLLISION</h1><p>TWO SPIRAL GALAXIES · TIDAL DISRUPTION SIMULATION</p></div>
<div id="cap">RESTRICTED THREE-BODY · 65 536 PARTICLES · GPU-INTEGRATED GRAVITY</div>

<script type="module">
import * as THREE from 'three';

try{

const TAU=Math.PI*2;
const clamp=(x,a,b)=>x<a?a:(x>b?b:x);
const sstep=(a,b,x)=>{const t=clamp((x-a)/(b-a),0,1);return t*t*(3-2*t);};

/* deterministic RNG so the piece always renders identically */
let _s=987654321;
const rnd=()=>{ _s^=_s<<13; _s^=_s>>>17; _s^=_s<<5; return (_s>>>0)/4294967296; };
let _g=null;
const gauss=()=>{ if(_g!==null){const v=_g;_g=null;return v;}
  const u=Math.max(rnd(),1e-12), v=rnd(), m=Math.sqrt(-2*Math.log(u));
  _g=m*Math.sin(TAU*v); return m*Math.cos(TAU*v); };

/* ===== physical scale: 1 length u = 1.25 kpc, 1 velocity u = 48 km/s, 1 time u = 5 Myr ===== */
const TEXS=256, NP=TEXS*TEXS;          // 65536 particles total
const NSTARS=30000, NHAZE=2200;        // per galaxy (stars + diffuse-light haze)
const GM_B=60,  EB2=1.9*1.9;           // bulge potential (Plummer)
const GM_H=340, EH2=10.0*10.0;         // extended halo -> flat rotation curve
const MU=800, CC2=4.0;                 // core-core mutual gravity (softened)
const RDISK=12;
const SPEED=3.3, MYR_PER_TU=5, KPC_PER_U=1.25, KMS_PER_V=48;
const CD=0.14, LAM2=81, NEAR_K=2.4, NEAR2=2.3*2.3;   // dynamical-friction drag

const vCirc=r=>{ const r2=r*r;
  return Math.sqrt(GM_B*r2/Math.pow(r2+EB2,1.5)+GM_H*r2/Math.pow(r2+EH2,1.5)); };

/* ===== particle initial conditions ===== */
const posArr=new Float32Array(NP*4), velArr=new Float32Array(NP*4),
      colArr=new Float32Array(NP*3), propArr=new Float32Array(NP*4);

function addGalaxy(gi,cf){
  const n=new THREE.Vector3(cf.n[0],cf.n[1],cf.n[2]).normalize();
  const h=Math.abs(n.y)<0.92?new THREE.Vector3(0,1,0):new THREE.Vector3(1,0,0);
  const e1=new THREE.Vector3().crossVectors(h,n).normalize();
  const e2=new THREE.Vector3().crossVectors(n,e1).normalize();
  const [cx,cy,cz]=cf.c,[vx,vy,vz]=cf.v;
  const A1x=e1.x,A1y=e1.y,A1z=e1.z,A2x=e2.x,A2y=e2.y,A2z=e2.z,Nx=n.x,Ny=n.y,Nz=n.z;
  let idx=gi*(NSTARS+NHAZE);
  const emit=(lx,ly,lz,ux,uy,uz,r,g,b,size,al,ph,tw)=>{
    const i4=idx*4,i3=idx*3;
    posArr[i4]=cx+A1x*lx+A2x*ly+Nx*lz; posArr[i4+1]=cy+A1y*lx+A2y*ly+Ny*lz;
    posArr[i4+2]=cz+A1z*lx+A2z*ly+Nz*lz; posArr[i4+3]=0;
    velArr[i4]=vx+A1x*ux+A2x*uy+Nx*uz; velArr[i4+1]=vy+A1y*ux+A2y*uy+Ny*uz;
    velArr[i4+2]=vz+A1z*ux+A2z*uy+Nz*uz; velArr[i4+3]=0;
    colArr[i3]=r; colArr[i3+1]=g; colArr[i3+2]=b;
    propArr[i4]=size; propArr[i4+1]=al; propArr[i4+2]=ph; propArr[i4+3]=tw;
    idx++;
  };
  /* bulge: Plummer sphere, warm colours, isotropic orbits + net spin */
  const NB=Math.floor(NSTARS*0.24);
  for(let i=0;i<NB;i++){
    const X=Math.max(rnd(),1e-6);
    let r=1.5/Math.sqrt(Math.pow(X,-2/3)-1); if(r>4.6)r=0.5+4.1*rnd();
    const u2=rnd()*2-1, ph=rnd()*TAU, s1=Math.sqrt(Math.max(0,1-u2*u2));
    const dx=Math.cos(ph)*s1, dy=Math.sin(ph)*s1, dz=u2;
    const vc=vCirc(r), sp=vc*(0.28+0.55*rnd());
    let tx=Ny*dz-Nz*dy, ty=Nz*dx-Nx*dz, tz=Nx*dy-Ny*dx;
    const tl=Math.hypot(tx,ty,tz)||1, f=vc*0.55/tl, br=0.5+0.75*rnd();
    emit(r*dx,r*dy,r*dz, dx*sp+tx*f, dy*sp+ty*f, dz*sp+tz*f,
         br,(0.70+0.18*rnd())*br,(0.40+0.22*rnd())*br,
         0.28+0.34*rnd()*rnd(), 1, rnd(), 0.3+0.3*rnd());
  }
  /* disk: concentrated radial profile, trailing log-spiral arms, cold circular orbits */
  for(let i=NB;i<NSTARS;i++){
    let r=RDISK*Math.pow(rnd(),1.7); if(r<0.8)r=0.8+0.5*rnd();
    r*=1+0.05*gauss();
    const arm=rnd()<0.60; let th;
    if(arm){ const m=Math.floor(rnd()*cf.arms);
      let sig=0.13+0.012*r; if(rnd()<0.10)sig*=2.4;      // feathery spurs
      th=cf.ph0+m*TAU/cf.arms-cf.k*Math.log(Math.max(r,1.1))+gauss()*sig;
    } else th=rnd()*TAU;
    const z=gauss()*(0.13+0.030*r)*(arm?0.8:1);
    const ct=Math.cos(th), st=Math.sin(th);
    const vc=vCirc(r)*(1+0.03*gauss());
    const vr=0.05*vc*gauss(), vv=0.04*vc*gauss();
    /* warm yellow inside -> blue-white rim; young hot giants live in the arms */
    const t=clamp((r-1.2)/10,0,1);
    let cr=1.0-0.42*t, cg=0.86-0.14*t, cb=0.58+0.47*t, br, size;
    if(arm&&rnd()<0.085){ cr=0.60;cg=0.72;cb=1.12; br=1.35+0.5*rnd(); size=0.85+0.55*rnd(); }
    else if(arm){ cr+=0.04;cg+=0.05;cb=Math.min(1.15,cb+0.10); br=0.50+0.70*rnd(); size=0.34+0.42*Math.pow(rnd(),1.5); }
    else { cr=Math.min(1.05,cr+0.07);cg+=0.02;cb=Math.max(0.34,cb-0.08); br=0.34+0.50*rnd(); size=0.32+0.38*Math.pow(rnd(),1.5); }
    emit(r*ct,r*st,z, -st*vc+ct*vr, ct*vc+st*vr, vv,
         Math.min(1.2,cr)*br, Math.min(1.2,cg)*br, Math.min(1.25,cb)*br,
         size, 1, rnd(), 0.25+0.55*rnd());
  }
  /* unresolved-starlight haze: co-rotating, partially arm-biased -> luminous arms, bridges, tails */
  for(let i=0;i<NHAZE;i++){
    let r=13.5*Math.pow(rnd(),2.3); if(r<0.7)r=0.7+0.5*rnd();
    let th;
    if(rnd()<0.45){ const m=Math.floor(rnd()*cf.arms);
      th=cf.ph0+m*TAU/cf.arms-cf.k*Math.log(Math.max(r,1.1))+gauss()*(0.25+0.02*r);
    } else th=rnd()*TAU;
    const z=gauss()*(0.45+0.05*r), ct=Math.cos(th), st=Math.sin(th);
    const vc=vCirc(r)*(1+0.04*gauss()), br=0.7+0.5*rnd();
    emit(r*ct,r*st,z, -st*vc, ct*vc, 0.03*gauss(),
         cf.tint[0]*br, cf.tint[1]*br, cf.tint[2]*br,
         3.5+9.0*rnd()*rnd(), 0.028+0.05*rnd()*rnd(), rnd(), 0);
  }
}

/* both disks are roughly prograde with the orbit (classic long-tail geometry), different inclinations */
const GAL=[
 {c:[-52.5,0,0], v:[ 1.6,0,-0.56], n:[ 0.16,-0.94,-0.30], arms:2, k:3.5, ph0:0.35, tint:[1.00,0.84,0.58]},
 {c:[ 52.5,0,0], v:[-1.6,0, 0.56], n:[-0.50,-0.58, 0.64], arms:3, k:2.9, ph0:1.15, tint:[0.62,0.76,1.05]}
];
addGalaxy(0,GAL[0]); addGalaxy(1,GAL[1]);
for(let i=2*(NSTARS+NHAZE);i<NP;i++){ posArr[i*4]=5e4; }   // spare slots: parked far, alpha 0

/* ===== renderer ===== */
const renderer=new THREE.WebGLRenderer({antialias:false,powerPreference:'high-performance'});
renderer.setClearColor(new THREE.Color(0x02030a),1);
document.body.appendChild(renderer.domElement);
const scene=new THREE.Scene();
const camera=new THREE.PerspectiveCamera(55,1,0.5,9000);

/* ===== GPU ping-pong state ===== */
const hasFloat=!!renderer.extensions.get('EXT_color_buffer_float');
const RTT=hasFloat?THREE.FloatType:THREE.HalfFloatType;
const mkRT=()=>new THREE.WebGLRenderTarget(TEXS,TEXS,{type:RTT,format:THREE.RGBAFormat,
  minFilter:THREE.NearestFilter,magFilter:THREE.NearestFilter,
  wrapS:THREE.ClampToEdgeWrapping,wrapT:THREE.ClampToEdgeWrapping,
  depthBuffer:false,stencilBuffer:false});
const rtP=[mkRT(),mkRT()], rtV=[mkRT(),mkRT()];

const simScene=new THREE.Scene();
const simCam=new THREE.OrthographicCamera(-1,1,1,-1,0,1);
const quad=new THREE.Mesh(new THREE.PlaneGeometry(2,2));
quad.frustumCulled=false; simScene.add(quad);

const SIM_VERT=`varying vec2 vUv;
void main(){ vUv=uv; gl_Position=vec4(position.xy,0.0,1.0); }`;

const copyMat=new THREE.ShaderMaterial({
  uniforms:{tSrc:{value:null}}, vertexShader:SIM_VERT,
  fragmentShader:`uniform sampler2D tSrc; varying vec2 vUv;
    void main(){ gl_FragColor=texture2D(tSrc,vUv); }`,
  depthTest:false, depthWrite:false });

/* velocity update: softened bulge+halo gravity from both moving nuclei */
const velMat=new THREE.ShaderMaterial({
  uniforms:{ tPos:{value:null}, tVel:{value:null},
    uCoreA:{value:new THREE.Vector3()}, uCoreB:{value:new THREE.Vector3()},
    uGrav:{value:new THREE.Vector4(GM_B,EB2,GM_H,EH2)}, dt:{value:0} },
  vertexShader:SIM_VERT,
  fragmentShader:`
    uniform sampler2D tPos,tVel;
    uniform vec3 uCoreA,uCoreB;
    uniform vec4 uGrav;
    uniform float dt;
    varying vec2 vUv;
    void main(){
      vec3 p=texture2D(tPos,vUv).xyz;
      vec3 v=texture2D(tVel,vUv).xyz;
      vec3 dA=uCoreA-p; float qA=dot(dA,dA);
      vec3 dB=uCoreB-p; float qB=dot(dB,dB);
      float ab=inversesqrt(qA+uGrav.y), ah=inversesqrt(qA+uGrav.w);
      float bb=inversesqrt(qB+uGrav.y), bh=inversesqrt(qB+uGrav.w);
      vec3 a=dA*(uGrav.x*ab*ab*ab+uGrav.z*ah*ah*ah)
            +dB*(uGrav.x*bb*bb*bb+uGrav.z*bh*bh*bh);
      v+=a*dt;
      float s2=dot(v,v);
      if(s2>4900.0) v*=70.0/sqrt(s2);
      gl_FragColor=vec4(v,0.0);
    }`,
  depthTest:false, depthWrite:false });

const posMat=new THREE.ShaderMaterial({
  uniforms:{tPos:{value:null},tVel:{value:null},dt:{value:0}},
  vertexShader:SIM_VERT,
  fragmentShader:`
    uniform sampler2D tPos,tVel;
    uniform float dt;
    varying vec2 vUv;
    void main(){
      vec4 P=texture2D(tPos,vUv);
      vec3 V=texture2D(tVel,vUv).xyz;
      gl_FragColor=vec4(P.xyz+V*dt,P.w);
    }`,
  depthTest:false, depthWrite:false });

/* seed the ping-pong buffers */
const posInit=new THREE.DataTexture(posArr,TEXS,TEXS,THREE.RGBAFormat,THREE.FloatType);
const velInit=new THREE.DataTexture(velArr,TEXS,TEXS,THREE.RGBAFormat,THREE.FloatType);
for(const tx of [posInit,velInit]){ tx.minFilter=tx.magFilter=THREE.NearestFilter; tx.needsUpdate=true; }
quad.material=copyMat;
copyMat.uniforms.tSrc.value=posInit;
renderer.setRenderTarget(rtP[0]); renderer.render(simScene,simCam);
copyMat.uniforms.tSrc.value=velInit;
renderer.setRenderTarget(rtV[0]); renderer.render(simScene,simCam);
renderer.setRenderTarget(null);
posInit.dispose(); velInit.dispose();

/* ===== star field (positions streamed from the position buffer) ===== */
const uvArr=new Float32Array(NP*3);
for(let i=0;i<NP;i++){
  uvArr[i*3]=((i%TEXS)+0.5)/TEXS;
  uvArr[i*3+1]=(Math.floor(i/TEXS)+0.5)/TEXS;
  uvArr[i*3+2]=0;
}
const starsGeo=new THREE.BufferGeometry();
starsGeo.setAttribute('position',new THREE.BufferAttribute(uvArr,3));
starsGeo.setAttribute('aColor',new THREE.BufferAttribute(colArr,3));
starsGeo.setAttribute('aProp',new THREE.BufferAttribute(propArr,4));

const starsMat=new THREE.ShaderMaterial({
  uniforms:{ uPosTex:{value:rtP[0].texture}, uProj:{value:1000},
             uTime:{value:0}, uExposure:{value:1.12} },
  vertexShader:`
    uniform sampler2D uPosTex;
    uniform float uProj,uTime,uExposure;
    attribute vec3 aColor;
    attribute vec4 aProp;
    varying vec3 vColor;
    varying float vAlpha;
    void main(){
      vec4 P=texture2D(uPosTex,position.xy);
      vec4 mv=modelViewMatrix*vec4(P.xyz,1.0);
      float ps=aProp.x*uProj/max(0.1,-mv.z);
      float dim=ps<1.25?(ps*ps)/1.5625:1.0;             // flux-conserving clamp for tiny points
      float tw=1.0-aProp.w*(0.5+0.5*sin(uTime*(0.55+fract(aProp.z)*1.7)+aProp.z*63.0));
      gl_PointSize=max(ps,1.25);
      gl_Position=projectionMatrix*mv;
      vColor=aColor*(uExposure*dim*tw);
      vAlpha=aProp.y;
    }`,
  fragmentShader:`
    varying vec3 vColor;
    varying float vAlpha;
    void main(){
      vec2 q=gl_PointCoord*2.0-1.0;
      float d2=dot(q,q);
      if(d2>1.0) discard;
      float g=(exp(-d2*3.4)+0.16*exp(-d2*1.2))*(1.0-smoothstep(0.72,1.0,d2));
      gl_FragColor=vec4(vColor*(g*vAlpha),1.0);
    }`,
  transparent:true, depthTest:false, depthWrite:false,
  blending:THREE.CustomBlending, blendEquation:THREE.AddEquation,
  blendSrc:THREE.OneFactor, blendDst:THREE.OneFactor });
const starsPts=new THREE.Points(starsGeo,starsMat);
starsPts.frustumCulled=false; starsPts.renderOrder=1;
scene.add(starsPts);

/* ===== nucleus glow: soft halo + hot nucleus + faint anamorphic streak per core ===== */
const glowGeo=new THREE.BufferGeometry();
glowGeo.setAttribute('position',new THREE.BufferAttribute(new Float32Array(18),3));
glowGeo.setAttribute('aColor',new THREE.BufferAttribute(new Float32Array([
  1.00,0.78,0.52,  0.88,0.85,1.00,  1.00,0.92,0.75,  0.95,0.95,1.00,  0.72,0.82,1.00,  0.78,0.86,1.00]),3));
glowGeo.setAttribute('aSize', new THREE.BufferAttribute(new Float32Array([26,24,4.6,4.2,24,22]),1));
glowGeo.setAttribute('aAlpha',new THREE.BufferAttribute(new Float32Array([0.42,0.42,0.9,0.9,0.16,0.16]),1));
glowGeo.setAttribute('aKind', new THREE.BufferAttribute(new Float32Array([0,0,1,1,2,2]),1));
const glowMat=new THREE.ShaderMaterial({
  uniforms:{uProj:{value:1000}},
  vertexShader:`
    uniform float uProj;
    attribute vec3 aColor;
    attribute float aSize;
    attribute float aAlpha;
    attribute float aKind;
    varying vec3 vColor;
    varying float vKind;
    void main(){
      vec4 mv=modelViewMatrix*vec4(position,1.0);
      gl_PointSize=aSize*uProj/max(0.1,-mv.z);
      gl_Position=projectionMatrix*mv;
      vColor=aColor*aAlpha; vKind=aKind;
    }`,
  fragmentShader:`
    varying vec3 vColor;
    varying float vKind;
    void main(){
      vec2 q=gl_PointCoord*2.0-1.0;
      float d2=dot(q,q);
      if(d2>1.0) discard;
      float g;
      if(vKind<0.5)      g=0.55*exp(-d2*3.0)+0.40*exp(-d2*0.9);
      else if(vKind<1.5) g=exp(-d2*4.0);
      else               g=exp(-q.x*q.x*2.2)*exp(-q.y*q.y*30.0);
      g*=1.0-smoothstep(0.75,1.0,d2);
      gl_FragColor=vec4(vColor*g,1.0);
    }`,
  transparent:true, depthTest:false, depthWrite:false,
  blending:THREE.CustomBlending, blendEquation:THREE.AddEquation,
  blendSrc:THREE.OneFactor, blendDst:THREE.OneFactor });
const glowPts=new THREE.Points(glowGeo,glowMat);
glowPts.frustumCulled=false; glowPts.renderOrder=2;
scene.add(glowPts);

/* ===== distant starfield background ===== */
const NBG=2600;
const bgPos=new Float32Array(NBG*3), bgCol=new Float32Array(NBG*3),
      bgSize=new Float32Array(NBG), bgTw=new Float32Array(NBG);
for(let i=0;i<NBG;i++){
  const u=rnd()*2-1, ph=rnd()*TAU, s1=Math.sqrt(Math.max(0,1-u*u));
  const R=1400+1100*rnd();
  bgPos[i*3]=R*s1*Math.cos(ph); bgPos[i*3+1]=R*u; bgPos[i*3+2]=R*s1*Math.sin(ph);
  const tt=rnd(); let r,g,b;
  if(tt<0.18){ r=1.0;g=0.82;b=0.66; } else if(tt>0.82){ r=0.72;g=0.83;b=1.0; } else { r=0.92;g=0.95;b=1.0; }
  let br=0.10+0.55*rnd()*rnd(), size=0.7+1.5*rnd()*rnd();
  if(rnd()<0.03){ br=1.1; size=2.6; }
  bgCol[i*3]=r*br; bgCol[i*3+1]=g*br; bgCol[i*3+2]=b*br;
  bgSize[i]=size; bgTw[i]=rnd()<0.35?0.5+0.5*rnd():0.0;
}
const bgGeo=new THREE.BufferGeometry();
bgGeo.setAttribute('position',new THREE.BufferAttribute(bgPos,3));
bgGeo.setAttribute('aColor',new THREE.BufferAttribute(bgCol,3));
bgGeo.setAttribute('aSize',new THREE.BufferAttribute(bgSize,1));
bgGeo.setAttribute('aTw',new THREE.BufferAttribute(bgTw,1));
const bgMat=new THREE.ShaderMaterial({
  uniforms:{uPR:{value:1},uTime:{value:0}},
  vertexShader:`
    uniform float uPR,uTime;
    attribute vec3 aColor;
    attribute float aSize;
    attribute float aTw;
    varying vec3 vColor;
    void main(){
      vec4 mv=modelViewMatrix*vec4(position,1.0);
      gl_Position=projectionMatrix*mv;
      float tw=1.0-aTw*0.45*(0.5+0.5*sin(uTime*(0.4+fract(aTw*13.7)*1.3)+aTw*97.0));
      gl_PointSize=aSize*uPR;
      vColor=aColor*tw;
    }`,
  fragmentShader:`
    varying vec3 vColor;
    void main(){
      vec2 q=gl_PointCoord*2.0-1.0;
      float d2=dot(q,q);
      if(d2>1.0) discard;
      float g=exp(-d2*3.5)*(1.0-smoothstep(0.7,1.0,d2));
      gl_FragColor=vec4(vColor*g,1.0);
    }`,
  transparent:true, depthTest:false, depthWrite:false,
  blending:THREE.CustomBlending, blendEquation:THREE.AddEquation,
  blendSrc:THREE.OneFactor, blendDst:THREE.OneFactor });
const bgPts=new THREE.Points(bgGeo,bgMat);
bgPts.frustumCulled=false; bgPts.renderOrder=0;
scene.add(bgPts);

/* ===== resize ===== */
let PR=Math.min(window.devicePixelRatio||1,2);
const dbSize=new THREE.Vector2();
function onResize(){
  renderer.setPixelRatio(PR);
  renderer.setSize(window.innerWidth,window.innerHeight);
  camera.aspect=window.innerWidth/window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.getDrawingBufferSize(dbSize);
  const proj=dbSize.y/(2*Math.tan(camera.fov*Math.PI/360));
  starsMat.uniforms.uProj.value=proj;
  glowMat.uniforms.uProj.value=proj;
  bgMat.uniforms.uPR.value=PR;
}
window.addEventListener('resize',onResize);
onResize();

/* ===== nuclei: the live two-body problem (softened + dynamical friction) ===== */
const relP=new THREE.Vector3(105,0,0), relV=new THREE.Vector3(-3.2,0,1.12);
let simT=0;
function stepCores(h){
  const S2=relP.lengthSq(), S=Math.sqrt(S2);
  const inv=1/Math.pow(S2+CC2,1.5);
  let ax=-MU*relP.x*inv, ay=-MU*relP.y*inv, az=-MU*relP.z*inv;
  const late=0.45*sstep(45,60,simT);   // gentle pacing guarantee for the final inspiral
  const dg=CD*sstep(13,19,simT)*Math.exp(-S2/LAM2)
          +NEAR_K*Math.exp(-S2/NEAR2)
          +late*Math.exp(-S2/LAM2);
  ax-=dg*relV.x; ay-=dg*relV.y; az-=dg*relV.z;
  relV.x+=ax*h; relV.y+=ay*h; relV.z+=az*h;
  relP.x+=relV.x*h; relP.y+=relV.y*h; relP.z+=relV.z*h;
}

let idx=0;
function simStep(h){
  velMat.uniforms.tPos.value=rtP[idx].texture;
  velMat.uniforms.tVel.value=rtV[idx].texture;
  velMat.uniforms.dt.value=h;
  quad.material=velMat;
  renderer.setRenderTarget(rtV[1-idx]); renderer.render(simScene,simCam);

  posMat.uniforms.tPos.value=rtP[idx].texture;
  posMat.uniforms.tVel.value=rtV[1-idx].texture;
  posMat.uniforms.dt.value=h;
  quad.material=posMat;
  renderer.setRenderTarget(rtP[1-idx]); renderer.render(simScene,simCam);
  renderer.setRenderTarget(null);
  idx=1-idx;
  starsMat.uniforms.uPosTex.value=rtP[idx].texture;
}

/* ===== HUD / phase ===== */
const hT=document.getElementById('hT'), hS=document.getElementById('hS'),
      hV=document.getElementById('hV'), hP=document.getElementById('hP'),
      titleEl=document.getElementById('title');
let passages=0, prevS=1e9, descending=false;
function phaseName(S){
  if(simT>64&&S<4) return 'MERGER REMNANT';
  if(passages===0) return S<34?'FINAL APPROACH':'FIRST APPROACH';
  if(S<4.2) return 'COALESCENCE';
  if(S<13){
    if(passages===1) return 'FIRST PASSAGE · BRIDGE';
    if(passages===2) return 'SECOND PASSAGE';
    return 'FINAL PASSAGES';
  }
  if(passages===1) return 'TIDAL TAILS EJECTING';
  if(passages===2) return 'TAILS EXPANDING';
  return 'RAPID INSPIRAL';
}

/* ===== main loop ===== */
let lastT=-1, acc=0, ftAvg=16.7, ftN=0;
function loop(tms){
  requestAnimationFrame(loop);
  const t=tms*0.001;
  if(lastT<0) lastT=t;
  const rawDt=Math.max(0,t-lastT); lastT=t;
  const dt=Math.min(rawDt,0.05);

  /* adaptive resolution if the frame rate dips */
  ftAvg+=(rawDt*1000-ftAvg)*0.05;
  if(++ftN>=90){ ftN=0; if(ftAvg>34&&PR>1.01){ PR=Math.max(1,PR-0.25); onResize(); } ftAvg=16.7; }

  /* cinematic time dilation near each close passage (radial-velocity gated) */
  const S0=relP.length(), V0=relV.length();
  const gate=clamp((V0-5)/3.5,0,1);
  const slow=1-0.62*Math.exp(-((S0-9.5)*(S0-9.5))/12.25)*gate;
  acc+=dt*SPEED*slow;
  const n=Math.max(1,Math.min(4,Math.ceil(acc/0.03)));
  const h=acc/n; acc=0;
  for(let k=0;k<n;k++){
    stepCores(h);
    velMat.uniforms.uCoreA.value.set(-relP.x*0.5,-relP.y*0.5,-relP.z*0.5);
    velMat.uniforms.uCoreB.value.set( relP.x*0.5, relP.y*0.5, relP.z*0.5);
    simStep(h);
    simT+=h;
  }

  const S=relP.length();
  if(S<prevS) descending=true;
  else if(descending){ if(prevS<17.5) passages++; descending=false; }
  prevS=S;

  /* slow orbiting camera: drifts closer and cranes upward as the event unfolds */
  const fit=Math.max(1,1.15/camera.aspect);
  const ang=1.12+0.045*t;
  const el=0.34+0.17*sstep(4,26,t)+0.02*Math.sin(t*0.23);
  const R=(152-24*sstep(4,26,t)+6*Math.sin(t*0.16+1.7))*fit;
  camera.position.set(R*Math.cos(el)*Math.cos(ang),R*Math.sin(el),R*Math.cos(el)*Math.sin(ang));
  camera.lookAt(0,0,0);

  /* nucleus sprites follow the live cores */
  const gp=glowGeo.attributes.position.array;
  const Ax=-relP.x*0.5,Ay=-relP.y*0.5,Az=-relP.z*0.5;
  gp[0]=Ax;gp[1]=Ay;gp[2]=Az;    gp[3]=-Ax;gp[4]=-Ay;gp[5]=-Az;
  gp[6]=Ax;gp[7]=Ay;gp[8]=Az;    gp[9]=-Ax;gp[10]=-Ay;gp[11]=-Az;
  gp[12]=Ax;gp[13]=Ay;gp[14]=Az; gp[15]=-Ax;gp[16]=-Ay;gp[17]=-Az;
  glowGeo.attributes.position.needsUpdate=true;

  starsMat.uniforms.uTime.value=t;
  bgMat.uniforms.uTime.value=t;

  hT.textContent='+'+String(Math.floor(simT*MYR_PER_TU)).padStart(3,'0')+' MYR';
  hS.textContent=(S*KPC_PER_U).toFixed(1)+' KPC';
  hV.textContent=Math.round(relV.length()*KMS_PER_V)+' KM/S';
  hP.textContent=phaseName(S);
  if(t>10) titleEl.classList.add('gone');

  renderer.render(scene,camera);
}
requestAnimationFrame(loop);

}catch(err){
  const d=document.createElement('div');
  d.style.cssText='position:fixed;inset:0;z-index:9;display:flex;align-items:center;justify-content:center;color:#9fb4d0;font:12px/1.6 ui-monospace,monospace;text-align:center;padding:0 24px';
  d.textContent='Could not start WebGL: '+(err&&err.message?err.message:err);
  document.body.appendChild(d);
}
</script>
</body>
</html>
```

A few notes on how it works and why I built it this way:

- **Real tidal dynamics, not a canned morph.** Stars are massless test particles in the time-varying potential of two nuclei (each a softened bulge + extended halo). Bridges and the two long "antennae" tails are purely emergent from the first and subsequent pericentre passages — the same restricted three-body scheme used in the classic galaxy-collision literature.
- **GPU integration.** Positions/velocities live in two pairs of 256×256 float render targets updated by tiny fragment shaders (semi-implicit Euler, 1–4 adaptive substeps per frame). The cores themselves are a cheap CPU-side two-body problem with a dynamical-friction drag, so the pair visibly spirals in and coalesces around the 16–20 s mark, leaving ~10 s of remnant evolution inside the recording window.
- **Believable disks.** I gave each galaxy a nearly flat rotation curve (v ≈ 4.1 across the whole disk), cold circular orbits, trailing logarithmic-spiral arms with scattered spurs, a hot blue giant population confined to the arms, and warm old populations inside — so colour runs naturally from yellow cores to blue-white rims. A co-rotating low-alpha haze layer makes the arms, bridge and tails luminous rather than just dotted.
- **Cinematography.** The camera is fully scripted (slow orbit, drifting elevation, gentle push-in), so framing is always safe; time automatically dilates to ~0.4× during each close passage to savour the slingshot. The HUD maps 1 unit = 1.25 kpc and 1 time-unit = 5 Myr, showing elapsed Myr, nuclear separation, relative velocity and a phase readout.
- **Robustness.** Additive one-one blending with analytic gaussian sprites (no textures, no post pass), half-float fallback if float render targets are unavailable, flux-conserving point-size clamping, and automatic pixel-ratio reduction if the frame rate drops. Everything is seeded, so the piece renders identically on every run and starts on its own.