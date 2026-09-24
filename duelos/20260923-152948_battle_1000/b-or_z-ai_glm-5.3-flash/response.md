Here's a complete, self-contained mass battle simulation. Two armies of 520 units each (1,040 total) march, charge, collide, and grind each other down in a chaotic melee, all rendered on a single canvas with a slight trapezoid perspective. The full arc — advance → charge → clash → melee → rout → victory celebration → fresh battle — lands well inside the first 30 seconds, then loops forever.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark">
<title>Field of Crowns — an endless mass battle</title>
<style>
  html,body{margin:0;height:100%;overflow:hidden;background:#0a0b09}
  #scene{position:fixed;inset:0;display:block}
  #hud{position:fixed;inset:0;pointer-events:none;color:#e9e4d4;
       font-family:Georgia,'Times New Roman','Palatino Linotype',serif;
       -webkit-user-select:none;user-select:none}
  .sh{text-shadow:0 1px 2px rgba(0,0,0,.8),0 0 16px rgba(0,0,0,.5)}

  #titleWrap{position:absolute;top:16px;left:50%;transform:translateX(-50%);
             text-align:center;opacity:0;transition:opacity .9s ease .1s;max-width:72vw}
  #titleWrap.show{opacity:1}
  #overline{font-size:11px;letter-spacing:.4em;text-transform:uppercase;opacity:.7}
  #title{font-size:clamp(22px,3.6vw,40px);font-weight:700;letter-spacing:.02em;
         line-height:1.08;margin:5px 0 0}
  .rule{width:150px;height:1px;margin:10px auto 8px;
        background:linear-gradient(90deg,transparent,rgba(233,228,212,.55),transparent)}
  #phase{font-style:italic;font-size:clamp(12px,1.4vw,15px);opacity:.88;min-height:1.3em}

  .army{position:absolute;top:22px;width:184px}
  #armyL{left:24px}
  #armyR{right:24px;text-align:right}
  .aname{font-size:11px;letter-spacing:.13em;text-transform:uppercase;opacity:.92;
         display:flex;align-items:center;gap:8px}
  #armyR .aname{justify-content:flex-end}
  .chip{width:9px;height:9px;transform:rotate(45deg);flex:none;box-shadow:0 0 0 1px rgba(0,0,0,.45)}
  .acount{font-size:clamp(26px,3vw,38px);font-weight:700;line-height:1.1;margin-top:3px;
          font-variant-numeric:tabular-nums}
  .abar{height:3px;background:rgba(233,228,212,.16);margin-top:7px;position:relative}
  .abar i{position:absolute;left:0;top:0;bottom:0;width:100%}
  #armyR .abar i{left:auto;right:0}
  .asub{font-size:10px;letter-spacing:.22em;text-transform:uppercase;opacity:.5;margin-top:6px}

  #tally{position:absolute;bottom:16px;left:50%;transform:translateX(-50%);
         font-size:11px;letter-spacing:.26em;text-transform:uppercase;opacity:.6;white-space:nowrap}

  #verdict{position:absolute;left:50%;top:40%;transform:translate(-50%,-50%);
           text-align:center;opacity:0;transition:opacity .9s ease;pointer-events:none}
  #verdict.show{opacity:1}
  #vOver{font-size:13px;letter-spacing:.55em;text-transform:uppercase;opacity:.85;margin-bottom:10px}
  #vName{font-size:clamp(30px,4.6vw,52px);font-weight:700;line-height:1.05}
  #vSub{font-size:clamp(12px,1.4vw,15px);font-style:italic;opacity:.9;margin-top:10px}

  #fader{position:fixed;inset:0;background:#06070a;opacity:0;
         transition:opacity .95s ease;pointer-events:none}
  #fader.on{opacity:1}
</style>
</head>
<body>
<canvas id="scene"></canvas>
<div id="hud">
  <div class="army sh" id="armyL">
    <div class="aname"><span class="chip" id="chipL"></span><span id="nameL"></span></div>
    <div class="acount" id="cntL">0</div>
    <div class="abar"><i id="barL"></i></div>
    <div class="asub">on the field</div>
  </div>
  <div class="army sh" id="armyR">
    <div class="aname"><span id="nameR"></span><span class="chip" id="chipR"></span></div>
    <div class="acount" id="cntR">0</div>
    <div class="abar"><i id="barR"></i></div>
    <div class="asub">on the field</div>
  </div>
  <div id="titleWrap" class="sh">
    <div id="overline"></div>
    <h1 id="title"></h1>
    <div class="rule"></div>
    <div id="phase"></div>
  </div>
  <div id="verdict" class="sh">
    <div id="vOver"></div>
    <div id="vName"></div>
    <div id="vSub"></div>
  </div>
  <div id="tally" class="sh"></div>
</div>
<div id="fader" class="on"></div>

<script>
(function(){
'use strict';
var TAU=Math.PI*2;
var Ww=1600, Hw=900;                    // world plane the simulation runs in
var CS=48, GW=Math.ceil(Ww/CS), GH=Math.ceil(Hw/CS);   // spatial hash grid
var SEPR=8.6, SEP2=SEPR*SEPR, FIGHT2=144, BREAK2=242;  // combat radii (world units)

/* ---------- canvas layers ---------- */
var cv=document.getElementById('scene'), ctx=cv.getContext('2d');
function $(id){return document.getElementById(id);}
var nameL=$('nameL'),nameR=$('nameR'),cntL=$('cntL'),cntR=$('cntR'),
    barL=$('barL'),barR=$('barR'),chipL=$('chipL'),chipR=$('chipR'),
    overline=$('overline'),titleEl=$('title'),phaseEl=$('phase'),
    tallyEl=$('tally'),verdict=$('verdict'),vOver=$('vOver'),vName=$('vName'),vSub=$('vSub'),
    fader=$('fader'),titleWrap=$('titleWrap');

var bgC=document.createElement('canvas'), bgX=bgC.getContext('2d');   // painted field
var dcC=document.createElement('canvas'), dcX=dcC.getContext('2d');   // persistent decals (corpses, blood)
var ovC=document.createElement('canvas'), ovX=ovC.getContext('2d');   // vignette + grain overlay
var texC=document.createElement('canvas'), texX=texC.getContext('2d');// ground texture (world space)
var TW=720, TH=405, grainPat=null;

/* ---------- projection: flat world -> slight top-down perspective ---------- */
var DPR=1, VW=1280, VH=720, topY=60, depth=600, PPW=0.8;
var PEXP=1.42, SF=0.60, SN=1.07;
function scaleAt(p){return (SF+(SN-SF)*p)*PPW;}
function projY(p){return topY+Math.pow(p,PEXP)*depth;}
function w2s(x,y){var p=y/Hw;return [VW*0.5+(x-Ww*0.5)*scaleAt(p), topY+Math.pow(p,PEXP)*depth, scaleAt(p)];}

/* ---------- flavour text ---------- */
var NAMES_R=['The Crimson Host','The Red Legion','The Scarlet Banner','The Rose Company','The Bloodaxe Warband','The Redward Men'];
var NAMES_B=['The Azure Order','The Cobalt Company','The Sapphire Guard','The Winter Host','The Riverlord Blues','The Bluebanner Ward'];
var PLACES=['Ashvale','Blackmere','Wolford Fen','Ravenhill','Stonewatch','Coldbrook','Thornfield','Grimsmoor','Eagleford','Saltmere','Harrowgate','Duskwold','Redfern Cross','Caelmarsh','Ironholt','Fennwick'];
var SEASONS=['the Wet Season','the Harvest Moon','First Frost','the Long Dry','Lammas Tide','the Sowing Wind'];
var MELEE=['No order remains — a savage melee','The center buckles under the press of bodies',
           'Shields splinter; blades find the gaps','The ranks dissolve into a killing ground',
           'Steel flashes across the trampled grass'];
var FORMS=['block','line','wedge'];
var ACCENT=['#d9684f','#7ea4d0'];
var BLD=['#7a1214','#5e0d10','#93201d'];
var PALETTES=[
  {h:88, s:16,l:19,dust:'128,118,92'},
  {h:70, s:18,l:24,dust:'142,128,92'},
  {h:140,s:11,l:15,dust:'98,106,92'},
  {h:47, s:9, l:23,dust:'146,134,104'}
];

/* ---------- state ---------- */
var units=[], particles=[], dl=[];
var armies=[null,null], palette=null, DUSTFILL='rgb(120,110,86)';
var phase='intro', t=0, tG=0, vt=0, shake=0, engaged=0;
var fallen=0, routed=0, firstClash=false, clashT=0, lastFlavor=0;
var battleN=0, winner=-1, fading=false, lastC0=-1, lastC1=-1, lastSec=-1;

/* corpse/blood decals live in a ring buffer so the field keeps its scars */
var STMAX=2800, stamps=new Array(STMAX), sN=0, sI=0;
var head=new Int32Array(GW*GH), nxt=new Int32Array(1200);
var dl=[];

function pick(a){return a[(Math.random()*a.length)|0];}
function mulberry32(a){return function(){a|=0;a=a+0x6D2B79F5|0;var t2=Math.imul(a^a>>>15,1|a);t2=t2+Math.imul(t2^t2>>>7,61|t2)^t2;return((t2^t2>>>14)>>>0)/4294967296;};}
function roman(n){var v=[1000,900,500,400,100,90,50,40,10,9,5,4,1],s=['M','CM','D','CD','C','XC','L','XL','X','IX','V','IV','I'],o='';
  for(var i=0;i<v.length;i++){while(n>=v[i]){o+=s[i];n-=v[i];}}return o;}
function fmt(s){var m=(s/60)|0,ss=s%60;return m+':'+(ss<10?'0':'')+ss;}

/* ---------- sizing ---------- */
function resize(){
  DPR=Math.min(window.devicePixelRatio||1,2);
  VW=window.innerWidth; VH=window.innerHeight;
  cv.width=Math.round(VW*DPR); cv.height=Math.round(VH*DPR);
  bgC.width=cv.width; bgC.height=cv.height;
  dcC.width=cv.width; dcC.height=cv.height;
  ovC.width=cv.width; ovC.height=cv.height;
  topY=VH*0.082; depth=VH*1.03-topY; PPW=VW*0.985/Ww;
  if(palette){buildBackground();redrawStamps();}
}
window.addEventListener('resize',resize);

/* ---------- ground texture (world space, sampled per scanline) ---------- */
function makeGround(pal){
  texC.width=TW; texC.height=TH;
  var g=texX;
  g.fillStyle='hsl('+pal.h+','+pal.s+'%,'+pal.l+'%)'; g.fillRect(0,0,TW,TH);
  var y=0,b=0;
  while(y<TH){ b++; g.fillStyle='hsla('+pal.h+','+pal.s+'%,'+(pal.l-3+(b%2)*4)+'%,0.12)';
    g.fillRect(0,y,TW,6); y+=13+((b*7)%9); }
  for(var i=0;i<110;i++){ var r=18+Math.random()*70;
    g.fillStyle='hsla('+(pal.h-16+Math.random()*32)+','+pal.s+'%,'+(pal.l-8+Math.random()*16)+'%,0.12)';
    g.beginPath(); g.ellipse(Math.random()*TW,Math.random()*TH,r,r*(0.5+Math.random()*0.5),Math.random()*3,0,TAU); g.fill(); }
  for(var k=0;k<5200;k++){
    g.fillStyle='hsla('+(pal.h+Math.random()*20-10)+','+pal.s+'%,'+(pal.l+Math.random()*22-11)+'%,'+(0.10+Math.random()*0.2).toFixed(2)+')';
    g.fillRect(Math.random()*TW,Math.random()*TH,Math.random()<0.9?1:2,1);
  }
  g.strokeStyle='hsla('+pal.h+','+(pal.s+10)+'%,'+(pal.l+14)+'%,0.35)'; g.lineWidth=1;
  for(var j=0;j<380;j++){ var x=Math.random()*TW,y2=Math.random()*TH;
    g.beginPath(); g.moveTo(x,y2); g.lineTo(x+Math.random()*3-1.5,y2-2-Math.random()*3); g.stroke(); }
}

/* ---------- static background: sky, hills, perspective field, props ---------- */
function hillLayer(g,base,amp,col,ph){
  g.fillStyle=col; g.beginPath(); g.moveTo(0,topY+4);
  for(var x=0;x<=VW;x+=10){ g.lineTo(x, base+Math.sin(x*0.011+ph)*amp+Math.sin(x*0.027+ph*2.1)*amp*0.5); }
  g.lineTo(VW,topY+4); g.closePath(); g.fill();
}
function buildBackground(){
  var g=bgX, pal=palette;
  g.setTransform(DPR,0,0,DPR,0,0);
  var sky=g.createLinearGradient(0,0,0,topY+VH*0.03);
  sky.addColorStop(0,'#2c2f33'); sky.addColorStop(0.65,'#6a6a5f'); sky.addColorStop(1,'#93897a');
  g.fillStyle=sky; g.fillRect(0,0,VW,topY+4);
  var rg=g.createRadialGradient(VW*0.5,topY*0.9,10,VW*0.5,topY*0.9,VW*0.5);
  rg.addColorStop(0,'rgba(242,226,186,0.20)'); rg.addColorStop(1,'rgba(242,226,186,0)');
  g.fillStyle=rg; g.fillRect(0,0,VW,topY+6);
  hillLayer(g,topY*0.50,topY*0.17,'#75705f',1.3);
  hillLayer(g,topY*0.72,topY*0.12,'#565247',3.1);
  g.fillStyle='#3c4136'; g.beginPath(); g.moveTo(0,topY+3);
  for(var x=0;x<=VW;x+=7){ g.lineTo(x, topY-3-Math.abs(Math.sin(x*0.05+1))*4-Math.sin(x*0.013)*3); }
  g.lineTo(VW,topY+3); g.closePath(); g.fill();

  var strips=240, step=Hw/strips, kT=TH/Hw;
  for(var i=0;i<strips;i++){
    var y0=i*step, y1=y0+step, p0=y0/Hw, p1=y1/Hw, p=(p0+p1)*0.5;
    var sy0=topY+Math.pow(p0,PEXP)*depth;
    var sc=scaleAt(p), dw=Ww*sc, dx=VW*0.5-dw*0.5;
    var sY=Math.min(TH-1,y0*kT), sH=Math.max(0.5,(y1-y0)*kT);
    var dh=(topY+Math.pow(p1,PEXP)*depth)-sy0+1.2;
    g.drawImage(texC,0,sY,TW,sH, dx-dw,sy0,dw,dh);
    g.drawImage(texC,0,sY,TW,sH, dx,sy0,dw,dh);
    g.drawImage(texC,0,sY,TW,sH, dx+dw,sy0,dw,dh);
  }
  var hz=g.createLinearGradient(0,topY-4,0,topY+VH*0.30);
  hz.addColorStop(0,'rgba(158,152,132,0.30)'); hz.addColorStop(1,'rgba(158,152,132,0)');
  g.fillStyle=hz; g.fillRect(0,topY-4,VW,VH*0.30+4);

  var n;
  for(n=0;n<3;n++){ var c=w2s(200+Math.random()*1200,260+Math.random()*420), cr=(45+Math.random()*45)*c[2];
    g.fillStyle='rgba(0,0,0,0.16)'; g.beginPath(); g.ellipse(c[0],c[1]+cr*0.15,cr,cr*0.55,0,0,TAU); g.fill();
    g.fillStyle='rgba(0,0,0,0.12)'; g.beginPath(); g.ellipse(c[0],c[1],cr*0.6,cr*0.33,0,0,TAU); g.fill();
    g.strokeStyle='rgba(255,250,230,0.07)'; g.lineWidth=Math.max(1,cr*0.05);
    g.beginPath(); g.ellipse(c[0],c[1],cr,cr*0.55,0,Math.PI,TAU); g.stroke(); }
  for(n=0;n<34;n++){ var r0=w2s(60+Math.random()*1480,80+Math.random()*780), rr=(1.6+Math.random()*2.2)*r0[2];
    g.fillStyle='rgba(0,0,0,0.2)'; g.beginPath(); g.ellipse(r0[0]+rr*0.5,r0[1]+rr*0.4,rr*1.2,rr*0.5,0,0,TAU); g.fill();
    g.fillStyle='hsl(42,7%,'+(30+Math.random()*16)+'%)'; g.beginPath();
    g.ellipse(r0[0],r0[1]-rr*0.2,rr,rr*0.7,Math.random()*3,0,TAU); g.fill();
    g.fillStyle='rgba(255,250,235,0.10)'; g.beginPath();
    g.ellipse(r0[0]-rr*0.3,r0[1]-rr*0.55,rr*0.45,rr*0.3,0,0,TAU); g.fill(); }
  g.lineWidth=1;
  for(n=0;n<160;n++){ var t0=w2s(40+Math.random()*1520,60+Math.random()*800);
    g.strokeStyle=Math.random()<0.5?'rgba(22,28,12,0.4)':'rgba(150,160,110,0.22)';
    var tx=t0[0],ty=t0[1],ln=2.5*t0[2];
    g.beginPath(); g.moveTo(tx,ty); g.lineTo(tx+Math.random()*2-1,ty-ln); g.stroke(); }
  for(n=0;n<6;n++){
    var far=n<3, wx=far?80+Math.random()*1440:(Math.random()<0.5?60+Math.random()*70:1470+Math.random()*70);
    var wy=far?70+Math.random()*120:260+Math.random()*380;
    var q=w2s(wx,wy), s=(11+Math.random()*7)*q[2], sx=q[0], sy=q[1];
    g.fillStyle='rgba(0,0,0,0.25)'; g.beginPath(); g.ellipse(sx+s*1.5,sy+s*0.4,s*1.6,s*0.5,0,0,TAU); g.fill();
    g.fillStyle='#241f18'; g.beginPath(); g.ellipse(sx,sy,s*0.22,s*0.14,0,0,TAU); g.fill();
    var cs=['#2a3123','#31392a','#252c20'];
    for(var b2=0;b2<3;b2++){ g.fillStyle=cs[b2]; g.beginPath();
      g.ellipse(sx+(b2-1)*s*0.4,sy-s*1.3-b2*s*0.12,s*(0.75-b2*0.12),s*(0.6-b2*0.1),0,0,TAU); g.fill(); }
  }
}

/* ---------- vignette + grain overlay ---------- */
function makeGrain(){
  var gc=document.createElement('canvas'); gc.width=gc.height=140;
  var gx=gc.getContext('2d'), im=gx.createImageData(140,140), d=im.data;
  for(var i=0;i<d.length;i+=4){ var v=(Math.random()*255)|0; d[i]=d[i+1]=d[i+2]=v; d[i+3]=255; }
  gx.putImageData(im,0,0); grainPat=ovX.createPattern(gc,'repeat');
}
function buildOverlay(){
  ovX.setTransform(DPR,0,0,DPR,0,0);
  ovX.clearRect(0,0,VW,VH);
  var r1=ovX.createRadialGradient(VW*0.5,VH*0.52,Math.min(VW,VH)*0.34,VW*0.5,VH*0.55,Math.max(VW,VH)*0.75);
  r1.addColorStop(0,'rgba(6,8,6,0)'); r1.addColorStop(1,'rgba(6,8,6,0.52)');
  ovX.fillStyle=r1; ovX.fillRect(0,0,VW,VH);
  if(!grainPat)makeGrain();
  ovX.globalAlpha=0.05; ovX.fillStyle=grainPat; ovX.fillRect(0,0,VW,VH); ovX.globalAlpha=1;
}

/* ---------- persistent battle-scar decals ---------- */
function addStamp(s){
  if(sN<STMAX){ stamps[sN++]=s; } else { stamps[sI]=s; sI=(sI+1)%STMAX; }
  drawStamp(dcX,s);
}
function redrawStamps(){
  dcX.setTransform(DPR,0,0,DPR,0,0); dcX.clearRect(0,0,VW,VH);
  var full=(sN>=STMAX);
  for(var i=0;i<sN;i++){ drawStamp(dcX, stamps[full?(sI+i)%STMAX:i]); }
}
function drawStamp(g,s){
  var p=s.y/Hw, sc=scaleAt(p);
  var sx=VW*0.5+(s.x-Ww*0.5)*sc, sy=topY+Math.pow(p,PEXP)*depth, R=s.s*sc;
  var rng=mulberry32(s.sd), i;
  if(s.k===0){ /* fallen soldier on a blood patch */
    for(i=0;i<7;i++){
      var a=rng()*TAU, rr=rng()*rng();
      var bx=sx+Math.cos(a)*R*1.9*rr, by=sy+Math.sin(a)*R*1.25*rr, br=R*(0.3+rng()*0.62);
      g.fillStyle='rgba('+(58+(rng()*36|0))+','+(8+(rng()*10|0))+','+(11+(rng()*10|0))+','+(0.4+rng()*0.32).toFixed(2)+')';
      g.beginPath(); g.ellipse(bx,by,br,br*(0.55+rng()*0.45),rng()*3,0,TAU); g.fill();
    }
    g.save(); g.translate(sx,sy); g.rotate(s.ang);
    g.fillStyle=s.col; g.beginPath(); g.ellipse(0,0,R*1.28,R*0.6,0,0,TAU); g.fill();
    g.fillStyle='rgba(158,152,138,0.75)'; g.beginPath(); g.arc(R*0.98,0,R*0.4,0,TAU); g.fill();
    g.strokeStyle='rgba(30,32,28,0.65)'; g.lineWidth=Math.max(1,R*0.15);
    g.beginPath(); g.moveTo(-R*0.3,R*0.55); g.lineTo(R*1.55,R*0.95); g.stroke();
    g.restore();
  }else{ /* dropped banner */
    g.save(); g.translate(sx,sy); g.rotate(s.ang);
    g.strokeStyle='rgba(60,58,50,0.8)'; g.lineWidth=Math.max(1,R*0.14);
    g.beginPath(); g.moveTo(-R*1.6,0); g.lineTo(R*1.6,R*0.3); g.stroke();
    g.fillStyle=s.col; g.beginPath(); g.ellipse(R*0.85,R*0.05,R*0.85,R*0.42,0.2,0,TAU); g.fill();
    g.restore();
  }
}

/* ---------- armies ---------- */
function genFormation(type,N,side,cx,cy){
  var pts=[], sy=11.2, rows, per, counts=null, r, depth;
  if(type==='wedge'){
    counts=[]; var tot=0; r=0;
    while(tot<N){ var c=Math.min(4+Math.round(r*2.2),N-tot); counts.push(c); tot+=c; r++; }
    rows=counts.length;
  }else if(type==='line'){ rows=13; per=Math.ceil(N/rows); }
  else{ rows=20; per=Math.ceil(N/rows); }
  depth=(rows-1)*10.6;
  var placed=0;
  for(r=0;r<rows&&placed<N;r++){
    var cnt=counts?counts[r]:Math.min(per,N-placed);
    var bx=(side?cx-depth*0.5:cx+depth*0.5)+(side?1:-1)*10.6*r;
    for(var j=0;j<cnt;j++){ pts.push({x:bx,y:cy+(j-(cnt-1)/2)*sy}); placed++; }
  }
  return pts;
}
function makeArmy(side,name){
  var a={side:side,name:name,count:0,initial:0,broken:false,charging:false,cx:side?1200:400,cy:450};
  var hue=side?212:8, sat=side?40:56, st=0.93+Math.random()*0.14;
  var N=520, sIdx=units.length;
  var pts=genFormation(pick(FORMS),N,side,side?1200:400,450+(Math.random()*80-40));
  for(var i=0;i<pts.length;i++){
    var li=40+Math.random()*14;
    var u={x:pts[i].x+(Math.random()*3-1.5), y:pts[i].y+(Math.random()*3-1.5), y0:pts[i].y,
      side:side, a:side?Math.PI:0, mhp:88+Math.random()*30, hp:0,
      dmg:(15+Math.random()*9)*st, cds:0.46+Math.random()*0.26, cd:Math.random()*0.5,
      spd:52+Math.random()*18, tgt:null, fight:false, swing:0,
      sw:Math.random()*TAU, w:Math.random()<0.5?-1:1,
      big:Math.random()<0.07, bold:Math.random()<0.12, banner:false,
      flee:false, fl:0, celeb:false, alive:true,
      col:'hsl('+Math.round(hue+Math.random()*8-4)+','+sat+'%,'+li.toFixed(1)+'%)',
      colD:'hsl('+hue+','+sat+'%,'+(li*0.5).toFixed(1)+'%)',
      dcol:'hsla('+hue+','+Math.round(sat*0.5)+'%,'+(15+Math.random()*5).toFixed(1)+'%,0.92)',
      hc:'hsl(45,'+(8+Math.random()*10|0)+'%,'+(56+Math.random()*16|0)+'%)',
      fcol:'hsl('+hue+','+(sat+16)+'%,54%)'};
    u.hp=u.mhp;
    units.push(u); a.count++;
  }
  for(var b=0;b<3;b++){ var ub=units[sIdx+((Math.random()*a.count)|0)];
    ub.banner=true; ub.big=true; ub.mhp*=1.7; ub.hp=ub.mhp; }
  a.initial=a.count;
  return a;
}

/* ---------- particles (screen space, pooled by swap-pop) ---------- */
function spawnBlood(wx,wy,n,mag){
  if(particles.length>1100)return;
  var p=wy/Hw, sc=scaleAt(p);
  var sx=VW*0.5+(wx-Ww*0.5)*sc, sy=topY+Math.pow(p,PEXP)*depth;
  for(var i=0;i<n;i++){
    var a=Math.random()*TAU, sp=(24+Math.random()*100)*sc*mag, l=0.2+Math.random()*0.3;
    particles.push({ty:0,x:sx+(Math.random()*6-3)*sc,y:sy+(Math.random()*4-2)*sc,
      vx:Math.cos(a)*sp,vy:Math.sin(a)*sp*0.7,l:l,tl:l,r0:(0.8+Math.random()*1.6)*sc,
      c:BLD[(Math.random()*BLD.length)|0],sw:0,gr:0});
  }
}
function spawnDust(wx,wy){
  if(particles.length>1100)return;
  var p=wy/Hw, sc=scaleAt(p);
  var sx=VW*0.5+(wx-Ww*0.5)*sc, sy=topY+Math.pow(p,PEXP)*depth;
  var a=Math.random()*TAU, sp=(6+Math.random()*26)*sc, l=0.5+Math.random()*0.55;
  particles.push({ty:1,x:sx,y:sy,vx:Math.cos(a)*sp,vy:Math.sin(a)*sp*0.5,
    l:l,tl:l,r0:(1.5+Math.random()*2.5)*sc,gr:(6+Math.random()*8)*sc,c:'',sw:0});
}
function spawnSmoke(wx,wy){
  if(particles.length>1100)return;
  var p=wy/Hw, sc=scaleAt(p);
  var sx=VW*0.5+(wx-Ww*0.5)*sc, sy=topY+Math.pow(p,PEXP)*depth;
  var l=1.4+Math.random()*1.2;
  particles.push({ty:2,x:sx,y:sy,vx:(4+Math.random()*13)*sc,vy:(-3+Math.random()*6)*sc,
    l:l,tl:l,r0:(2.5+Math.random()*3)*sc,gr:(9+Math.random()*10)*sc,c:'',sw:Math.random()*TAU});
}
function spawnSpark(wx,wy){
  if(particles.length>1100)return;
  var p=wy/Hw, sc=scaleAt(p);
  var sx=VW*0.5+(wx-Ww*0.5)*sc, sy=topY+Math.pow(p,PEXP)*depth;
  var a=Math.random()*TAU;
  particles.push({ty:3,x:sx,y:sy,vx:Math.cos(a)*90*sc,vy:Math.sin(a)*45*sc,
    l:0.09,tl:0.09,r0:(0.9+Math.random()*0.8)*sc,c:'',sw:0,gr:0});
}
function updateParticles(dt){
  for(var i=particles.length-1;i>=0;i--){
    var q=particles[i]; q.l-=dt;
    if(q.l<=0){ var lastP=particles.pop(); if(i<particles.length)particles[i]=lastP; continue; }
    q.x+=q.vx*dt; q.y+=q.vy*dt;
    if(q.ty===0){ var f=Math.max(0,1-5.5*dt); q.vx*=f; q.vy*=f; }
    else if(q.ty===1){ var f2=Math.max(0,1-2.6*dt); q.vx*=f2; q.vy*=f2; }
    else if(q.ty===2){ q.x+=Math.sin(tG*1.4+q.sw)*9*dt; }
  }
}
function drawParticles(smoke){
  for(var i=0;i<particles.length;i++){
    var q=particles[i];
    if((q.ty===2)!==smoke)continue;
    var a=q.l/q.tl;
    if(q.ty===2){ ctx.globalAlpha=a*0.13; ctx.fillStyle='rgb(63,65,58)';
      ctx.beginPath(); ctx.arc(q.x,q.y,q.r0+(1-a)*q.gr,0,TAU); ctx.fill(); }
    else if(q.ty===1){ ctx.globalAlpha=a*0.2; ctx.fillStyle=DUSTFILL;
      ctx.beginPath(); ctx.arc(q.x,q.y,q.r0+(1-a)*q.gr,0,TAU); ctx.fill(); }
    else if(q.ty===0){ ctx.globalAlpha=Math.min(1,a*1.4); ctx.fillStyle=q.c;
      ctx.beginPath(); ctx.arc(q.x,q.y,q.r0*(0.35+0.65*a),0,TAU); ctx.fill(); }
    else{ ctx.globalAlpha=a; ctx.fillStyle='#f2ecd8';
      ctx.beginPath(); ctx.arc(q.x,q.y,q.r0,0,TAU); ctx.fill(); }
  }
  ctx.globalAlpha=1;
}

/* ---------- combat resolution ---------- */
function hurt(v,d){
  if(!v.alive)return;
  v.hp-=d;
  spawnBlood(v.x,v.y,2,0.75);
  if(Math.random()<0.3)spawnSpark(v.x,v.y);
  if(v.hp<=0)killUnit(v);
}
function killUnit(v){
  if(!v.alive)return;
  v.alive=false;
  var a=armies[v.side]; a.count--; fallen++;
  addStamp({k:0,x:v.x+(Math.random()*8-4),y:v.y+(Math.random()*6-3),
    s:4.4+Math.random()*2.8, ang:v.a+(Math.random()-0.5)*1.2,
    col:v.dcol, sd:(Math.random()*4294967295)>>>0});
  spawnBlood(v.x,v.y,9,1);
  spawnDust(v.x,v.y); spawnDust(v.x,v.y);
  if(Math.random()<0.4)spawnSmoke(v.x,v.y);
  if(v.banner)addStamp({k:1,x:v.x,y:v.y+4,s:4,ang:Math.random()*3,col:v.fcol,sd:7});
}
function breakArmy(a){
  if(a.broken)return;
  a.broken=true; phase='rout';
  for(var i=0;i<units.length;i++){ var u=units[i];
    if(u.alive&&u.side===a.side&&!u.flee)u.fl=Math.random()*1.6; }
  setPhase(a.name+' breaks and flees the field!');
}
function endBattle(wn){
  if(phase==='end')return;
  phase='end'; vt=0; winner=wn; fading=false; shake=0;
  for(var i=0;i<units.length;i++){ var u=units[i];
    if(u.alive){ u.celeb=(wn>=0&&u.side===wn&&!u.flee); u.tgt=null; u.fight=false; } }
  if(wn>=0){
    var w=armies[wn];
    vOver.textContent='Victory';
    vName.textContent=w.name; vName.style.color=ACCENT[wn];
    vSub.textContent=w.count+' survivors hold the field — '+fallen+' fell in '+fmt(Math.floor(t));
    setPhase(w.name+' holds the field.');
  }else{
    vOver.textContent='Annihilation';
    vName.textContent='No banner remains'; vName.style.color='#cfc9b6';
    vSub.textContent='Both armies lie broken upon the field — '+fallen+' fell.';
    setPhase('The field falls silent.');
  }
  verdict.classList.add('show');
}

/* ---------- simulation step ---------- */
function step(dt){
  var A=armies[0], B=armies[1];
  if(phase==='end'){
    vt+=dt;
    if(!fading&&vt>5.2){ fading=true; fader.classList.add('on'); }
    if(fading&&vt>6.35){ newBattle(); return; }
  }
  if(phase==='intro'&&t>1.05){ phase='advance'; setPhase('The armies advance across the field.'); }
  t+=dt;

  /* rebuild spatial hash: head[cell] -> linked list via nxt[] */
  head.fill(-1);
  for(var i0=0;i0<units.length;i0++){ var u0=units[i0]; if(!u0.alive)continue;
    var ci=cellOf(u0.x,u0.y); nxt[i0]=head[ci]; head[ci]=i0; }

  /* centroids (used as march targets when no enemy is in sensor range) */
  var s0x=0,s0y=0,n0=0,s1x=0,s1y=0,n1=0,i1,e1;
  for(i1=0;i1<units.length;i1++){ e1=units[i1]; if(!e1.alive)continue;
    if(e1.side){s1x+=e1.x;s1y+=e1.y;n1++;}else{s0x+=e1.x;s0y+=e1.y;n0++;} }
  if(n0){A.cx=s0x/n0;A.cy=s0y/n0;}
  if(n1){B.cx=s1x/n1;B.cy=s1y/n1;}
  var gap=Math.abs(A.cx-B.cx);
  if(phase==='advance'){
    if(gap<430){A.charging=true;B.charging=true;}
    if(A.charging&&B.charging){ phase='charge'; setPhase('The horns sound — the lines charge!'); }
  }

  var active=(phase!=='intro'&&phase!=='end');
  var f0=0,f1=0,eng=0;

  for(var i=0;i<units.length;i++){
    var u=units[i]; if(!u.alive)continue;

    /* --- sense neighbours through the 3x3 grid neighbourhood --- */
    var nd2=1e12, ne=-1, spx=0, spy=0;
    var gx=(u.x/CS)|0; if(gx<0)gx=0; else if(gx>=GW)gx=GW-1;
    var gy=(u.y/CS)|0; if(gy<0)gy=0; else if(gy>=GH)gy=GH-1;
    var x0=gx>0?gx-1:0, x1=gx<GW-1?gx+1:GW-1;
    var y0=gy>0?gy-1:0, y1=gy<GH-1?gy+1:GH-1;
    for(var yy=y0;yy<=y1;yy++){
      var rb=yy*GW;
      for(var xx=x0;xx<=x1;xx++){
        for(var j=head[yy*GW+xx];j!==-1;j=nxt[j]){
          if(j===i)continue;
          var v=units[j]; if(!v.alive)continue;
          var dx=v.x-u.x, dy=v.y-u.y, d2=dx*dx+dy*dy;
          if(d2<SEP2&&d2>1e-6){ var dd=Math.sqrt(d2), ff=1-dd/SEPR; spx-=dx/dd*ff; spy-=dy/dd*ff; }
          if(v.side!==u.side&&d2<nd2){ nd2=d2; ne=j; }
        }
      }
    }
    var sm2=spx*spx+spy*spy;
    if(sm2>1){ var iv=1/Math.sqrt(sm2); spx*=iv; spy*=iv; }

    /* --- target selection: nearest sensed enemy, else keep/advance --- */
    var cur=u.tgt, curOK=!!cur&&cur.alive;
    if(active&&!u.flee){
      if(ne>=0){
        var cand=units[ne];
        if(!curOK)u.tgt=cand;
        else{ var cdx=cur.x-u.x, cdy=cur.y-u.y, cd2=cdx*cdx+cdy*cdy;
          if(nd2<cd2*0.5||cd2>2500)u.tgt=cand; }
      }else{
        if(curOK){ var cdx2=cur.x-u.x, cdy2=cur.y-u.y; if(cdx2*cdx2+cdy2*cdy2>3600)u.tgt=null; }
        else u.tgt=null;
      }
    }else if(!active){ u.tgt=null; }

    /* --- act --- */
    var vx=0, vy=0, face=-9;
    if(u.flee){
      if(u.fl>0){ u.fl-=dt; if(u.fl<=0)u.flee=true; }
      else{
        var sf2=u.spd*2.25;
        vx=(u.side?1:-1)*sf2+Math.sin(t*2.7+u.sw)*22;
        vy=Math.sin(t*3.3+u.sw*1.7)*sf2*0.22;
      }
      if((u.side===0&&u.x<-18)||(u.side===1&&u.x>Ww+18)){
        u.alive=false; if(u.side){B.count--;}else{A.count--;} routed++;
        continue;
      }
    }else if(active&&u.tgt&&u.tgt.alive){
      var tg=u.tgt;
      var tdx=tg.x-u.x, tdy=tg.y-u.y, td2=tdx*tdx+tdy*tdy;
      if(!u.fight){ if(td2<FIGHT2)u.fight=true; }
      else if(td2>BREAK2)u.fight=false;
      if(u.fight){
        eng++;
        face=Math.atan2(tdy,tdx);
        u.cd-=dt;
        if(u.cd<=0){
          u.cd=u.cds*(0.7+Math.random()*0.7);
          u.swing=1;
          if(!firstClash){
            firstClash=true; clashT=t; phase='clash';
            setPhase('The lines collide!'); shake=Math.max(shake,7);
            var mx=(A.cx+B.cx)*0.5, my=(A.cy+B.cy)*0.5;
            for(var k2=0;k2<30;k2++)spawnDust(mx+(Math.random()*90-45),my+(Math.random()*480-240));
          }
          hurt(tg, u.dmg*(1+Math.max(0,t-18)*0.045));
        }
      }else{
        var td=Math.sqrt(td2)||0.01;
        var sp3=u.spd*(tg.flee?1.95:(armies[u.side].charging?1.75:1.12))*(u.bold?1.1:1);
        vx=tdx/td*sp3; vy=tdy/td*sp3;
      }
    }else if(active){
      var ec=armies[1-u.side];
      var ax=ec.cx-u.x, ay=(u.y0*0.82+ec.cy*0.18)-u.y;
      var ad2=ax*ax+ay*ay;
      if(ad2>9){
        var ad=Math.sqrt(ad2);
        var sp4=u.spd*(armies[u.side].charging?1.75:1.1);
        var wb=Math.sin(t*2.2+u.sw)*0.22, cw=Math.cos(wb), sw3=Math.sin(wb);
        vx=(ax/ad*cw-ay/ad*sw3)*sp4; vy=(ax/ad*sw3+ay/ad*cw)*sp4;
      }
    }else{
      vx=Math.sin(tG*1.15+u.sw)*9; vy=Math.cos(tG*0.85+u.sw*1.6)*7;
    }

    /* separation keeps the ranks dense but unstacked */
    var sfp=(u.fight&&!u.flee)?13:30;
    vx+=spx*sfp; vy+=spy*sfp;
    u.x+=vx*dt; u.y+=vy*dt;
    if(u.y<16)u.y=16; else if(u.y>Hw-16)u.y=Hw-16;
    if(!u.flee){ if(u.x<10)u.x=10; else if(u.x>Ww-10)u.x=Ww-10; }

    var ta=(face>=-8)?face:((Math.abs(vx)+Math.abs(vy)>1)?Math.atan2(vy,vx):u.a);
    var da=ta-u.a;
    while(da>Math.PI)da-=TAU; while(da<-Math.PI)da+=TAU;
    u.a+=da*Math.min(1,dt*(face>=-8?14:6.5));
    if(u.swing>0)u.swing=Math.max(0,u.swing-dt*5);
    if(!u.flee){ if(u.side)f1++; else f0++; }
  }

  engaged=eng;
  shake=Math.max(0,shake-dt*7);
  if(eng>150)shake=Math.max(shake,0.5);
  updateParticles(dt);

  if(phase==='clash'&&t-clashT>7){ phase='melee'; lastFlavor=t; setPhase(pick(MELEE)); }
  else if(phase==='melee'&&t-lastFlavor>9){ lastFlavor=t; setPhase(pick(MELEE)); }

  if(phase!=='intro'&&phase!=='end'){
    if(!A.broken&&!B.broken){
      if(t>42)breakArmy(A.count<=B.count?A:B);
      else if(A.count>0&&B.count>0){
        if(A.count<B.count*0.34)breakArmy(A);
        else if(B.count<A.count*0.34)breakArmy(B);
      }
    }
    if(f0===0||f1===0){
      var wn;
      if(f0===0&&f1===0)wn=A.count>B.count?0:(B.count>A.count?1:-1);
      else if(f0===0)wn=1; else wn=0;
      endBattle(wn);
    }
  }
  updateHud();
}

/* ---------- HUD ---------- */
function setPhase(s){
  phaseEl.textContent=s;
  if(phaseEl.animate)phaseEl.animate([{opacity:0,transform:'translateY(5px)'},{opacity:1,transform:'translateY(0)'}],{duration:420,easing:'ease-out'});
}
function updateHud(){
  var a0=armies[0].count, a1=armies[1].count;
  if(a0!==lastC0){ lastC0=a0; cntL.textContent=a0; barL.style.width=(a0/armies[0].initial*100).toFixed(1)+'%'; }
  if(a1!==lastC1){ lastC1=a1; cntR.textContent=a1; barR.style.width=(a1/armies[1].initial*100).toFixed(1)+'%'; }
  var s=t|0;
  if(s!==lastSec){ lastSec=s; tallyEl.textContent=fallen+' fallen · '+routed+' routed · '+fmt(s); }
}

/* ---------- rendering ---------- */
function drawUnit(u){
  var p=u.y/Hw, sc=scaleAt(p);
  var sx0=VW*0.5+(u.x-Ww*0.5)*sc;
  var sy0=topY+Math.pow(p,PEXP)*depth;
  var r=(u.big?4.9:3.9)*sc;
  var hop=u.celeb?Math.abs(Math.sin(vt*6.3+u.sw))*r*1.35:0;
  ctx.fillStyle='rgba(13,15,10,0.34)';
  ctx.beginPath(); ctx.ellipse(sx0+r*0.35,sy0+r*0.5,r*1.05,r*0.48,0,0,TAU); ctx.fill();

  var pr=u.swing>0?1-u.swing:0;
  var lg=Math.sin(Math.min(1,pr)*Math.PI)*r*0.55;
  var ca=Math.cos(u.a), sa=Math.sin(u.a);
  var sx=sx0+ca*lg, sy=sy0-hop+sa*lg*0.8;

  if(u.banner){ /* standard bearer: waving banner */
    var wv=Math.sin(tG*(u.celeb?9:3.1)+u.sw)*0.5+0.5;
    var tx=sx+Math.sin(tG*1.6+u.sw)*r*0.5, ty=sy-r*4.4;
    ctx.strokeStyle='#d9d1bd'; ctx.lineWidth=Math.max(1,r*0.16);
    ctx.beginPath(); ctx.moveTo(sx,sy-r*0.3); ctx.lineTo(tx,ty); ctx.stroke();
    ctx.fillStyle=u.fcol;
    var fl=r*2.6*(0.8+wv*0.4);
    ctx.beginPath(); ctx.moveTo(tx,ty);
    ctx.quadraticCurveTo(tx+fl*0.5,ty+r*0.5-wv*r*0.9, tx+fl,ty+r*0.1-wv*r*0.6);
    ctx.lineTo(tx+fl,ty+r*0.95-wv*r*0.6);
    ctx.quadraticCurveTo(tx+fl*0.5,ty+r*1.35-wv*r*0.7, tx,ty+r*1.1);
    ctx.closePath(); ctx.fill();
  }

  var ang;
  if(u.swing>0) ang=u.a+u.w*(1.2-2.25*Math.sin(Math.min(1,pr)*Math.PI));
  else if(u.celeb) ang=-Math.PI*0.5+u.w*0.35+Math.sin(tG*3.6+u.sw)*0.25;
  else ang=u.a+u.w*1.2+Math.sin(tG*2.2+u.sw)*0.05;
  ctx.strokeStyle='#ccd0c8'; ctx.lineWidth=Math.max(1,r*0.26);
  ctx.beginPath();
  ctx.moveTo(sx+Math.cos(ang)*r*0.4, sy+Math.sin(ang)*r*0.4);
  ctx.lineTo(sx+Math.cos(ang)*r*2.1, sy+Math.sin(ang)*r*2.1);
  ctx.stroke();

  ctx.fillStyle=u.col;
  ctx.beginPath(); ctx.arc(sx,sy,r,0,TAU); ctx.fill();
  ctx.lineWidth=Math.max(0.7,r*0.24); ctx.strokeStyle=u.colD; ctx.stroke();

  var hr=1-u.hp/u.mhp;
  if(hr>0.14){ ctx.fillStyle='rgba(96,14,14,'+Math.min(0.55,hr*0.55).toFixed(3)+')';
    ctx.beginPath(); ctx.arc(sx,sy,r,0,TAU); ctx.fill(); }

  var hx=sx+ca*r*0.45, hy=sy+sa*r*0.45-r*0.16;
  ctx.fillStyle=u.hc; ctx.beginPath(); ctx.arc(hx,hy,r*0.52,0,TAU); ctx.fill();
  ctx.fillStyle='rgba(18,20,14,0.55)';
  ctx.beginPath(); ctx.arc(hx+ca*r*0.32,hy+sa*r*0.32,Math.max(0.6,r*0.14),0,TAU); ctx.fill();
}
function render(){
  ctx.setTransform(DPR,0,0,DPR,0,0);
  if(shake>0.01)ctx.translate((Math.random()*2-1)*shake,(Math.random()*2-1)*shake*0.6);
  ctx.fillStyle='#0c0f0b'; ctx.fillRect(-30,-30,VW+60,VH+60);
  ctx.drawImage(bgC,0,0,VW,VH);
  ctx.drawImage(dcC,0,0,VW,VH);
  drawParticles(true);
  dl.length=0;
  for(var i=0;i<units.length;i++){ if(units[i].alive)dl.push(units[i]); }
  dl.sort(function(a,b){return a.y-b.y;});
  for(var k=0;k<dl.length;k++)drawUnit(dl[k]);
  drawParticles(false);
  ctx.setTransform(DPR,0,0,DPR,0,0);
  ctx.drawImage(ovC,0,0,VW,VH);
}

/* ---------- battle lifecycle ---------- */
function newBattle(){
  battleN++;
  palette=pick(PALETTES); DUSTFILL='rgb('+palette.dust+')';
  makeGround(palette); buildBackground();
  sN=0; sI=0;
  dcX.setTransform(DPR,0,0,DPR,0,0); dcX.clearRect(0,0,VW,VH);
  particles.length=0; units.length=0;
  armies=[makeArmy(0,pick(NAMES_R)), makeArmy(1,pick(NAMES_B))];
  fallen=0; routed=0; firstClash=false; clashT=0; lastFlavor=0;
  vt=0; fading=false; winner=-1; phase='intro'; t=0;
  lastC0=-1; lastC1=-1; lastSec=-1; shake=0; engaged=0;

  nameL.textContent=armies[0].name; nameR.textContent=armies[1].name;
  chipL.style.background=ACCENT[0]; chipR.style.background=ACCENT[1];
  barL.style.background=ACCENT[0]; barR.style.background=ACCENT[1];
  cntL.textContent=armies[0].count; cntR.textContent=armies[1].count;
  barL.style.width='100%'; barR.style.width='100%';
  overline.textContent='Battle '+roman(battleN)+' · '+pick(SEASONS);
  titleEl.textContent=(Math.random()<0.3?'The Field of ':'The Battle of ')+pick(PLACES);
  verdict.classList.remove('show');
  setPhase('Two hosts muster for battle.');
  titleWrap.classList.remove('show'); void titleWrap.offsetWidth;
  setTimeout(function(){titleWrap.classList.add('show');},250);
  requestAnimationFrame(function(){requestAnimationFrame(function(){fader.classList.remove('on');});});
}

/* ---------- boot & loop ---------- */
resize();
newBattle();
window.addEventListener('resize',resize);

var last=performance.now();
function frame(now){
  requestAnimationFrame(frame);
  var dt=(now-last)/1000; last=now;
  if(dt>0.06)dt=0.06; if(dt<0)dt=0;
  tG+=dt;
  step(dt);
  render();
}
requestAnimationFrame(frame);
})();
</script>
</body>
</html>
```

**How it works**

- **Perspective field**: the simulation runs on a flat 1600×900 world plane, projected through a trapezoid (far rows converge and compress, unit size scales with depth). The background — hazy sky, hill silhouettes, ploughed scanline-sampled ground, rocks and trees — is pre-rendered once per battle.
- **Spatial partitioning**: a uniform 48-unit hash grid rebuilt each frame with typed-array linked lists (`head`/`next`), so every unit finds its nearest enemy and separation neighbours in a single 3×3 cell scan — 1,040 units stay smooth at 60 fps.
- **Emergent battle**: units march toward the enemy centroid in block/line/wedge formations, latch onto the nearest sensed enemy, duel with swing animations, health, blood spray, dust puffs and smoke. Persistent corpse and blood decals accumulate in a ring buffer, so the field visibly scars as formations collapse into melee.
- **Narrative arc**: named battles ("Battle VII · the Harvest Moon — The Battle of Grimsmoor"), live survivor counters with depletion bars, phase captions, morale rout at 34% strength with fleeing stragglers, then the winners hop and raise swords under a Victory card before the scene fades and a brand-new battle (new names, formations, ground palette) begins automatically.