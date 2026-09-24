```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Solar System — Cinematic Tour</title>
<style>
  html,body{margin:0;height:100%;overflow:hidden;background:#000;font-family:Georgia,'Times New Roman',serif}
  #c{display:block;width:100vw;height:100vh}
  #label{position:fixed;left:50%;bottom:12%;transform:translateX(-50%);
    color:#fff;font-size:42px;letter-spacing:0.35em;text-transform:uppercase;
    text-shadow:0 0 18px rgba(255,255,255,.6);opacity:0;transition:opacity .8s;
    pointer-events:none;white-space:nowrap}
  #sub{position:fixed;left:50%;bottom:8%;transform:translateX(-50%);
    color:rgba(255,255,255,.55);font-size:14px;letter-spacing:.2em;opacity:0;
    transition:opacity .8s;pointer-events:none}
</style>
</head>
<body>
<canvas id="c"></canvas>
<div id="label"></div>
<div id="sub"></div>
<script type="module">
import * as THREE from 'three';

/* ---------- renderer / scene / camera ---------- */
const renderer = new THREE.WebGLRenderer({canvas:document.getElementById('c'),antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(55, innerWidth/innerHeight, .1, 4000);
function resize(){camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);}
addEventListener('resize',resize); resize();

/* ---------- helpers ---------- */
function tex(w,h,fn){
  const c=document.createElement('canvas');c.width=w;c.height=h;
  fn(c.getContext('2d'),w,h);
  const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;return t;
}
let seed=7;const rnd=()=>{seed=(seed*16807)%2147483647;return seed/2147483647;};
function speckle(g,w,h,cols,n,rMin,rMax){for(let i=0;i<n;i++){g.fillStyle=cols[(rnd()*cols.length)|0];g.globalAlpha=.15+rnd()*.35;g.beginPath();g.arc(rnd()*w,rnd()*h,rMin+rnd()*(rMax-rMin),0,7);g.fill();}g.globalAlpha=1;}

/* ---------- textures ---------- */
const sunTex=tex(512,256,(g,w,h)=>{const gr=g.createLinearGradient(0,0,0,h);gr.addColorStop(0,'#ffcc44');gr.addColorStop(.5,'#ff9a22');gr.addColorStop(1,'#ffcc44');g.fillStyle=gr;g.fillRect(0,0,w,h);speckle(g,w,h,['#fff3b0','#ff7700','#ffe28a'],400,2,14);});
function rocky(base,dark,light){return tex(512,256,(g,w,h)=>{g.fillStyle=base;g.fillRect(0,0,w,h);speckle(g,w,h,dark,220,3,22);speckle(g,w,h,light,160,2,12);});}
const mercuryT=rocky('#8a8580',['#5c5751','#6e6963'],['#b3aea8','#c8c3bd']);
const venusT=tex(512,256,(g,w,h)=>{g.fillStyle='#d8a657';g.fillRect(0,0,w,h);for(let i=0;i<60;i++){g.strokeStyle=['#c08f3e','#e8bd77','#b07f33'][(rnd()*3)|0];g.globalAlpha=.25;g.lineWidth=4+rnd()*14;g.beginPath();const y=rnd()*h;g.moveTo(0,y);g.bezierCurveTo(w*.3,y+30-rnd()*60,w*.6,y+30-rnd()*60,w,y+(rnd()-.5)*40);g.stroke();}g.globalAlpha=1;});
const earthT=tex(512,256,(g,w,h)=>{g.fillStyle='#0d3f7a';g.fillRect(0,0,w,h);const gr=g.createLinearGradient(0,0,0,h);gr.addColorStop(0,'#0a305f');gr.addColorStop(.5,'#1565a8');gr.addColorStop(1,'#0a305f');g.fillStyle=gr;g.fillRect(0,0,w,h);
  for(let i=0;i<9;i++){ // continents = blob clusters
    const cx=rnd()*w,cy=h*.15+rnd()*h*.7;
    for(let j=0;j<40;j++){g.fillStyle=['#2e7d3a','#3c8f42','#8a6f3a','#c9be9a'][(rnd()*4)|0];g.globalAlpha=.85;
      const a=rnd()*7,d=rnd()*34;g.beginPath();
      g.ellipse(cx+Math.cos(a)*d*1.8,cy+Math.sin(a)*d*.8,4+rnd()*16,3+rnd()*10,a,0,7);g.fill();}
  }g.globalAlpha=1;
  g.fillStyle='rgba(255,255,255,.9)';g.fillRect(0,0,w,10);g.fillRect(0,h-10,w,10); // ice caps
  g.fillStyle='rgba(255,255,255,.25)';for(let i=0;i<25;i++){g.beginPath();g.arc(rnd()*w,rnd()*h*.4,2+rnd()*6,0,7);g.fill();} // clouds
});
const marsT=rocky('#b34a2a',['#7c2f18','#8f3a1f','#5f2412'],['#d97b4a','#e8a06a']);
const jupiterT=tex(512,256,(g,w,h)=>{const bands=['#c8a878','#a67c52','#e0cbaa','#8a5a34','#d9b98a','#b58a5c','#ead9bd','#96683e'];
  let y=0;while(y<h){const bh=8+rnd()*22;g.fillStyle=bands[(rnd()*bands.length)|0];g.fillRect(0,y,w,bh+1);
    g.strokeStyle='rgba(0,0,0,.12)';for(let i=0;i<3;i++){g.beginPath();const yy=y+rnd()*bh;g.moveTo(0,yy);g.bezierCurveTo(w*.3,yy+(rnd()-.5)*8,w*.6,yy+(rnd()-.5)*8,w,yy);g.lineWidth=1+rnd()*2;g.stroke();}y+=bh;}
  g.fillStyle='#c25434';g.beginPath();g.ellipse(w*.68,h*.62,26,14,0,0,7);g.fill();
  g.strokeStyle='#e8d5b5';g.lineWidth=3;g.stroke();});
const saturnT=tex(512,256,(g,w,h)=>{const bands=['#e0cfa0','#cdb880','#efe3c0','#c2a86e','#d8c494'];
  let y=0;while(y<h){const bh=10+rnd()*26;g.fillStyle=bands[(rnd()*bands.length)|0];g.fillRect(0,y,w,bh+1);y+=bh;}});
const uranusT=tex(256,128,(g,w,h)=>{const gr=g.createLinearGradient(0,0,0,h);gr.addColorStop(0,'#8fd1d8');gr.addColorStop(.5,'#6fc3ce');gr.addColorStop(1,'#8fd1d8');g.fillStyle=gr;g.fillRect(0,0,w,h);g.globalAlpha=.2;g.fillStyle='#bdeef2';for(let i=0;i<8;i++)g.fillRect(0,rnd()*h,w,3+rnd()*5);g.globalAlpha=1;});
const neptuneT=tex(256,128,(g,w,h)=>{const gr=g.createLinearGradient(0,0,0,h);gr.addColorStop(0,'#2a52b8');gr.addColorStop(.5,'#1e3f9e');gr.addColorStop(1,'#2a52b8');g.fillStyle=gr;g.fillRect(0,0,w,h);g.fillStyle='rgba(140,180,255,.35)';for(let i=0;i<10;i++)g.fillRect(0,rnd()*h,w,2+rnd()*4);g.fillStyle='rgba(10,20,60,.6)';g.beginPath();g.ellipse(w*.4,h*.55,20,9,0,0,7);g.fill();});
const ringT=tex(512,32,(g,w,h)=>{g.clearRect(0,0,w,h);for(let x=0;x<w;x++){const f=x/w;const a=Math.max(0,Math.sin(f*Math.PI))*(0.35+0.65*Math.abs(Math.sin(f*40)));
  g.fillStyle=`rgba(${210-f*60|0},${190-f*50|0},${150-f*40|0},${a*0.85})`;g.fillRect(x,0,1,h);}
  g.fillStyle='rgba(0,0,0,0)';g.fillRect(w*.55,0,w*.06,h);});
const glowT=tex(256,256,(g,w,h)=>{const gr=g.createRadialGradient(w/2,h/2,0,w/2,h/2,w/2);
  gr.addColorStop(0,'rgba(255,240,190,1)');gr.addColorStop(.25,'rgba(255,180,80,.55)');
  gr.addColorStop(.6,'rgba(255,120,30,.16)');gr.addColorStop(1,'rgba(255,100,20,0)');
  g.fillStyle=gr;g.fillRect(0,0,w,h);});

/* ---------- sun ---------- */
const sun=new THREE.Mesh(new THREE.SphereGeometry(5,48,32),new THREE.MeshBasicMaterial({map:sunTex}));
scene.add(sun);
const halo=new THREE.Sprite(new THREE.SpriteMaterial({map:glowT,blending:THREE.AdditiveBlending,depthWrite:false,transparent:true}));
halo.scale.set(34,34,1);scene.add(halo);
const sunLight=new THREE.PointLight(0xfff2d8,2600,0,1.8);scene.add(sunLight);
scene.add(new THREE.AmbientLight(0x223344,.5));

/* ---------- planets ---------- */
const PLANETS=[
 {name:'Mercury',r:.55,d:11, speed:.09, ph:1.2,tex:mercuryT,sub:'0.38 Earth radii · 88-day year'},
 {name:'Venus', r:.95,d:15.5,speed:.066,ph:2.6,tex:venusT, sub:'The morning star'},
 {name:'Earth', r:1.0,d:21, speed:.05, ph:4.1,tex:earthT, sub:'Home · one Moon'},
 {name:'Mars',  r:.72,d:26.5,speed:.04, ph:5.5,tex:marsT,  sub:'The red planet'},
 {name:'Jupiter',r:2.9,d:37, speed:.024,ph:.6,tex:jupiterT,sub:'King of the planets'},
 {name:'Saturn',r:2.4,d:49, speed:.018,ph:2.0,tex:saturnT,sub:'Lord of the rings'},
 {name:'Uranus',r:1.6,d:59, speed:.013,ph:3.4,tex:uranusT,sub:'The sideways giant'},
 {name:'Neptune',r:1.55,d:68,speed:.010,ph:4.8,tex:neptuneT,sub:'Edge of the giants'},
];
const earthIdx=2;
const orbitGroup=new THREE.Group();scene.add(orbitGroup);
PLANETS.forEach((p,i)=>{
  const pivot=new THREE.Group();
  const m=new THREE.Mesh(new THREE.SphereGeometry(p.r,40,26),
    new THREE.MeshStandardMaterial({map:p.tex,roughness:.85,metalness:.05}));
  m.rotation.z=.1+i*.05;
  pivot.add(m);orbitGroup.add(pivot);
  // orbit line
  const pts=[];for(let a=0;a<=128;a++){const t=a/128*Math.PI*2;pts.push(new THREE.Vector3(Math.cos(t)*p.d,0,Math.sin(t)*p.d));}
  const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),
    new THREE.LineBasicMaterial({color:0x8899bb,transparent:true,opacity:.14}));
  scene.add(line);
  p.pivot=pivot;p.mesh=m;
});
// Saturn rings
{const p=PLANETS[5];const rg=new THREE.RingGeometry(p.r*1.4,p.r*2.3,96,1);
 const pos=rg.attributes.position,uv=rg.attributes.uv,v=new THREE.Vector3();
 for(let i=0;i<pos.count;i++){v.fromBufferAttribute(pos,i);const f=(v.length()-p.r*1.4)/(p.r*.9);uv.setXY(i,f,.5);}
 rg.rotateX(Math.PI/2);
 const ring=new THREE.Mesh(rg,new THREE.MeshBasicMaterial({map:ringT,side:THREE.DoubleSide,transparent:true}));
 ring.rotation.x=.45;p.mesh.add(ring);}
// Moon
const moonPivot=new THREE.Group();PLANETS[earthIdx].mesh.add(moonPivot);
const moon=new THREE.Mesh(new THREE.SphereGeometry(.27,24,16),
  new THREE.MeshStandardMaterial({map:rocky('#b9b5ae',['#8a867f','#6f6b65'],['#d5d1ca']),roughness:1}));
moon.position.set(2.4,0.3,0);moonPivot.add(moon);

/* ---------- starfield ---------- */
{const n=3200,pos=new Float32Array(n*3),col=new Float32Array(n*3);
 for(let i=0;i<n;i++){const r=500+rnd()*1500,th=rnd()*Math.PI*2,ph=Math.acos(2*rnd()-1);
  pos[i*3]=r*Math.sin(ph)*Math.cos(th);pos[i*3+1]=r*Math.cos(ph);pos[i*3+2]=r*Math.sin(ph)*Math.sin(th);
  const c=.6+rnd()*.4,t=rnd();col[i*3]=c*(t<.7?1:.8);col[i*3+1]=c*(t<.7?.9:.85);col[i*3+2]=c;}
 const g=new THREE.BufferGeometry();
 g.setAttribute('position',new THREE.BufferAttribute(pos,3));
 g.setAttribute('color',new THREE.BufferAttribute(col,3));
 scene.add(new THREE.Points(g,new THREE.PointsMaterial({size:1.6,vertexColors:true,sizeAttenuation:false})));}

/* ---------- tour choreography ---------- */
const INTRO=3.2, SEG=3.55;
const TOTAL=INTRO+SEG*8+SEG; // ends with a pull-back to the whole system, then loops
const label=document.getElementById('label'),sub=document.getElementById('sub');
let shown=-1;
const smooth=x=>{x=Math.min(1,Math.max(0,x));return x*x*(3-2*x);};
const V=()=>new THREE.Vector3();
const tmpA=V(),tmpB=V(),tmpC=V(),tmpD=V();

function planetPos(i,t,out){const p=PLANETS[i],a=t*p.speed+p.ph;out.set(Math.cos(a)*p.d,0,Math.sin(a)*p.d);return out;}
function viewpoint(i,t,outPos,outTgt){
  if(i<8){const p=PLANETS[i];planetPos(i,t,outTgt);
    const a=t*p.speed+p.ph; // camera trails slightly behind, above
    const ang=a-0.9, h=p.r*1.6+p.r, dist=p.r*4.2+1.6;
    outPos.set(outTgt.x+Math.cos(ang)*dist, h, outTgt.z+Math.sin(ang)*dist);
  }else{ // wide shot
    outPos.set(0,62,95);outTgt.set(0,0,0);
  }
}
const camPos=V(),camTgt=V(),pA=V(),pB=V(),tA=V(),tB=V();

/* ---------- animation ---------- */
renderer.setAnimationLoop((ms)=>{
  const t=ms/1000;
  // orbital motion
  PLANETS.forEach((p)=>{const a=t*p.speed+p.ph;p.pivot.position.set(Math.cos(a)*p.d,0,Math.sin(a)*p.d);});
  moonPivot.rotation.y=t*1.1;
  sun.rotation.y=t*.05;halo.material.rotation=t*.02;
  const pulse=1+Math.sin(t*2)*.02;halo.scale.set(34*pulse,34*pulse,1 сексуал);

  let i;
  if(t<INTRO){ i=-1;
    const f=smooth(t/INTRO);
    camPos.set(60*(1-f)+14*f, 26*(1-f)+8*f, 60*(1-f)+30*f);
    camTgt.set(0,0,0);
    show(-1);
  }else{
    const u=t-INTRO, seg=Math.min(8,Math.floor(u/SEG)), f=smooth((u-seg*SEG)/SEG);
    viewpoint(seg,t,pA,tA); viewpoint(seg+1,t,pB,tB);
    camPos.lerpVectors(pA,pB,f); camTgt.lerpVectors(tA,tB,f);
    show(seg);
  }
  camera.position.copy(camPos);camera.lookAt(camTgt);
  renderer.render(scene,camera);
});
function show(i){
  if(i===shown)return;shown=i;
  if(i<0){label.style.opacity=0;sub.style.opacity=0;return;}
  label.textContent=PLANETS[i].name;sub.textContent=PLANETS[i].sub;
  label.style.opacity=1;sub.style.opacity=1;
}
</script>
</body>
</html>
```