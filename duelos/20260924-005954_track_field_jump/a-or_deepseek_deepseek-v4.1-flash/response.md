Here's the complete HTML file for a NES-style long jump event. It runs entirely in the browser with procedurally drawn pixel art, an AI demo mode toggled with P, and a slow-motion replay.
```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TRACK &amp; FIELD — LONG JUMP</title>
<style>
  html,body{margin:0;padding:0;background:#04050a;height:100%;overflow:hidden;}
  body{display:flex;align-items:center;justify-content:center;}
  canvas{image-rendering:pixelated;image-rendering:crisp-edges;display:block;background:#04050a;}
</style>
</head>
<body>
<canvas id="c"></canvas>
<script>
(function(){
"use strict";

/* ============================================================
   CANVAS / SCALING
   ============================================================ */
const W = 480, H = 270;
const cv = document.getElementById('c');
cv.width = W; cv.height = H;
const ctx = cv.getContext('2d');
ctx.imageSmoothingEnabled = false;

function resize(){
  let s = Math.min(window.innerWidth / W, window.innerHeight / H);
  s = s >= 1 ? Math.floor(s) : s;
  cv.style.width  = (W * s) + 'px';
  cv.style.height = (H * s) + 'px';
}
window.addEventListener('resize', resize);
resize();

/* ============================================================
   PIXEL FONT (5x7)
   ============================================================ */
const FONT_DATA = {
'A':"01110,10001,10001,11111,10001,10001,10001",
'B':"11110,10001,10001,11110,10001,10001,11110",
'C':"01110,10001,10000,10000,10000,10001,01110",
'D':"11110,10001,10001,10001,10001,10001,11110",
'E':"11111,10000,10000,11110,10000,10000,11111",
'F':"11111,10000,10000,11110,10000,10000,10000",
'G':"01110,10001,10000,10111,10001,10001,01111",
'H':"10001,10001,10001,11111,10001,10001,10001",
'I':"11111,00100,00100,00100,00100,00100,11111",
'J':"00111,00010,00010,00010,00010,10010,01100",
'K':"10001,10010,10100,11000,10100,10010,10001",
'L':"10000,10000,10000,10000,10000,10000,11111",
'M':"10001,11011,10101,10101,10001,10001,10001",
'N':"10001,11001,10101,10011,10001,10001,10001",
'O':"01110,10001,10001,10001,10001,10001,01110",
'P':"11110,10001,10001,11110,10000,10000,10000",
'Q':"01110,10001,10001,10001,10101,10010,01101",
'R':"11110,10001,10001,11110,10100,10010,10001",
'S':"01111,10000,10000,01110,00001,00001,11110",
'T':"11111,00100,00100,00100,00100,00100,00100",
'U':"10001,10001,10001,10001,10001,10001,01110",
'V':"10001,10001,10001,10001,10001,01010,00100",
'W':"10001,10001,10001,10101,10101,11011,10001",
'X':"10001,10001,01010,00100,01010,10001,10001",
'Y':"10001,10001,01010,00100,00100,00100,00100",
'Z':"11111,00001,00010,00100,01000,10000,11111",
'0':"01110,10001,10011,10101,11001,10001,01110",
'1':"00100,01100,00100,00100,00100,00100,01110",
'2':"01110,10001,00001,00010,00100,01000,11111",
'3':"11111,00010,00100,00010,00001,10001,01110",
'4':"00010,00110,01010,10010,11111,00010,00010",
'5':"11111,10000,11110,00001,00001,10001,01110",
'6':"00110,01000,10000,11110,10001,10001,01110",
'7':"11111,00001,00010,00100,01000,01000,01000",
'8':"01110,10001,10001,01110,10001,10001,01110",
'9':"01110,10001,10001,01111,00001,00010,01100",
' ':"00000,00000,00000,00000,00000,00000,00000",
'.':"00000,00000,00000,00000,00000,01100,01100",
',':"00000,00000,00000,00000,00110,00100,01000",
':':"00000,01100,01100,00000,01100,01100,00000",
'-':"00000,00000,00000,11111,00000,00000,00000",
'!':"00100,00100,00100,00100,00100,00000,00100",
'?':"01110,10001,00001,00110,00100,00000,00100",
'/':"00001,00010,00010,00100,01000,01000,10000",
'%':"11001,11010,00010,00100,01000,01011,10011",
"'":"00100,00100,00000,00000,00000,00000,00000",
'(':"00010,00100,01000,01000,01000,00100,00010",
')':"01000,00100,00010,00010,00010,00100,01000",
'+':"00000,00100,00100,11111,00100,00100,00000",
'*':"00000,10101,01110,11111,01110,10101,00000",
'=':"00000,00000,11111,00000,11111,00000,00000",
'<':"01000,00100,00010,00001,00010,00100,01000",
'>':"00010,00100,01000,10000,01000,00100,00010"
};
const GLYPHS = {};
for (const ch in FONT_DATA){
  GLYPHS[ch] = FONT_DATA[ch].split(',').map(function(r){
    return r.split('').map(Number);
  });
}

function textOn(g, str, x, y, color, sc){
  sc = sc || 1;
  g.fillStyle = color;
  str = String(str).toUpperCase();
  let cx = Math.round(x);
  const cy = Math.round(y);
  for (let i = 0; i < str.length; i++){
    const gl = GLYPHS[str[i]];
    if (gl){
      for (let r = 0; r < 7; r++){
        const row = gl[r];
        let rs = -1;
        for (let c = 0; c < 5; c++){
          if (row[c]){ if (rs < 0) rs = c; }
          else if (rs >= 0){ g.fillRect(cx + rs*sc, cy + r*sc, (c-rs)*sc, sc); rs = -1; }
        }
        if (rs >= 0) g.fillRect(cx + rs*sc, cy + r*sc, (5-rs)*sc, sc);
      }
    }
    cx += 6*sc;
  }
}
function drawText(str,x,y,c,sc){ textOn(ctx,str,x,y,c,sc); }
function drawTextC(str,y,c,sc){
  const w = String(str).length*6*sc - sc;
  drawText(str, Math.round((W-w)/2), y, c, sc);
}

/* ============================================================
   HELPERS
   ============================================================ */
const RAD = Math.PI/180;
function wrap(v,m){ return ((v%m)+m)%m; }
function clamp(v,a,b){ return v<a?a:(v>b?b:v); }
function rndR(a,b){ return a + Math.random()*(b-a); }

function limb(x0,y0,x1,y1,t,col){
  x0=Math.round(x0); y0=Math.round(y0); x1=Math.round(x1); y1=Math.round(y1);
  let dx=Math.abs(x1-x0), sx = x0<x1?1:-1;
  let dy=-Math.abs(y1-y0), sy = y0<y1?1:-1;
  let err = dx+dy;
  const h = Math.floor(t/2);
  ctx.fillStyle = col;
  let guard = 0;
  while (guard++ < 220){
    ctx.fillRect(x0-h, y0-h, t, t);
    if (x0===x1 && y0===y1) break;
    const e2 = 2*err;
    if (e2 >= dy){ err += dy; x0 += sx; }
    if (e2 <= dx){ err += dx; y0 += sy; }
  }
}
function circle(cx,cy,r,col){
  ctx.fillStyle = col;
  cx = Math.round(cx); cy = Math.round(cy);
  for (let y = -r; y <= r; y++){
    const w = Math.floor(Math.sqrt(Math.max(0, r*r - y*y)));
    ctx.fillRect(cx-w, cy+y, w*2+1, 1);
  }
}

/* ============================================================
   WORLD CONSTANTS
   ============================================================ */
const PPM        = 18;                  // pixels per metre
const RUNWAY_M   = 38;
const BOARD_X    = RUNWAY_M * PPM;      // 684 — front edge (foul line)
const BOARD_W    = 22;
const PIT_START  = BOARD_X;
const PIT_LEN    = 12 * PPM;            // 216
const PIT_END    = PIT_START + PIT_LEN;
const GROUND_Y   = 214;

const MAX_SPEED  = 11.8;
const PRESS_GAIN = 0.85;
const SPD_DECAY  = 0.85;
const GRAV       = 15;
const ANGLE_PER  = 1.15;
const WR         = 8.95;

/* ============================================================
   PALETTE
   ============================================================ */
const P = {
  skin:'#f2c69c', skinD:'#c1926a',
  top:'#e04040',  topD:'#9e2626',
  short:'#26355c',shortD:'#182238',
  shoe:'#f8f8f8', shoeD:'#b8b8b8',
  hair:'#2a1c12'
};

/* ============================================================
   ASSETS — CROWD TILE
   ============================================================ */
const crowdTile = (function(){
  const c = document.createElement('canvas');
  c.width = 480; c.height = 112;
  const g = c.getContext('2d');
  g.imageSmoothingEnabled = false;

  // roof
  g.fillStyle = '#1b2030'; g.fillRect(0,0,480,11);
  g.fillStyle = '#2b3348'; g.fillRect(0,11,480,2);
  g.fillStyle = '#3d4763'; g.fillRect(0,11,480,1);
  g.fillStyle = '#0e1220'; g.fillRect(0,13,480,1);

  g.fillStyle = '#12172a'; g.fillRect(0,14,480,95);

  const skin   = ['#f0c8a0','#d8a878','#a87850','#f8e0c0','#8a5f3a'];
  const shirts = ['#e05050','#4a7fd8','#4fc060','#e8c040','#d060c0','#f0f0f0',
                  '#40c8d0','#e08030','#8050d0','#50a0e0','#b8b8b8','#70d070',
                  '#e8a0a0','#3060a0'];

  let seed = 987654321;
  function rnd(){ seed = (seed*1103515245 + 12345) & 0x7fffffff; return seed / 0x7fffffff; }

  const tiers = 4, tierH = 24;
  for (let t = 0; t < tiers; t++){
    const ty = 14 + t*tierH;
    g.fillStyle = (t % 2) ? '#20273a' : '#1a2032';
    g.fillRect(0, ty, 480, tierH);
    g.fillStyle = '#0c1020';
    g.fillRect(0, ty + tierH - 3, 480, 3);

    for (let row = 0; row < 2; row++){
      const ry = ty + 2 + row*10;
      for (let x = 0; x < 480; x += 5){
        if (rnd() < 0.13) continue;
        const px = x + ((rnd()*2)|0);
        const sh = shirts[(rnd()*shirts.length)|0];
        const sk = skin[(rnd()*skin.length)|0];
        g.fillStyle = sh;
        g.fillRect(px, ry+3, 4, 5);
        g.fillStyle = 'rgba(0,0,0,0.22)';
        g.fillRect(px, ry+7, 4, 1);
        g.fillStyle = sk;
        g.fillRect(px+1, ry, 2, 3);
      }
    }
  }
  // aisles
  g.fillStyle = 'rgba(0,0,0,0.35)';
  for (let i = 0; i < 480; i += 96){
    g.fillRect(i, 14, 3, 95);
    g.fillRect(i+1, 14, 1, 95);
  }
  // front railing
  g.fillStyle = '#39415c'; g.fillRect(0,106,480,6);
  g.fillStyle = '#5a6488'; g.fillRect(0,106,480,1);
  g.fillStyle = '#20263a'; g.fillRect(0,110,480,2);
  return c;
})();

// waving spectators (positions in tile space)
const WAVERS = [];
(function(){
  for (let t = 0; t < 4; t++){
    for (let i = 0; i < 7; i++){
      WAVERS.push({
        x: 18 + i*66 + ((t*17) % 23),
        y: 14 + t*24 + 2 + (i % 2)*10,
        ph: i*1.7 + t*0.9
      });
    }
  }
})();

const FLAG_POS = [
  { x:110, c1:'#e03030', c2:'#f8f8f8' },
  { x:340, c1:'#3070e0', c2:'#f8e040' }
];

const CLOUDS = [];
for (let i = 0; i < 9; i++){
  CLOUDS.push({
    x: Math.random()*760,
    y: 4 + Math.random()*36,
    w: 18 + Math.random()*28,
    h: 4 + Math.random()*4,
    s: 2 + Math.random()*5
  });
}

/* ============================================================
   ASSETS — SAND PIT
   ============================================================ */
const pitCanvas = (function(){
  const c = document.createElement('canvas');
  c.width = PIT_LEN; c.height = 44;
  const g = c.getContext('2d');
  g.imageSmoothingEnabled = false;

  g.fillStyle = '#e6c882'; g.fillRect(0,0,PIT_LEN,44);

  let seed = 424242;
  function rnd(){ seed = (seed*1103515245 + 12345) & 0x7fffffff; return seed / 0x7fffffff; }
  for (let i = 0; i < 1400; i++){
    const x = (rnd()*PIT_LEN)|0, y = (rnd()*44)|0;
    g.fillStyle = rnd() < 0.5 ? '#d6b274' : '#f5de9e';
    g.fillRect(x, y, 1, 1);
  }
  // rake lines
  g.fillStyle = 'rgba(160,125,70,0.13)';
  for (let i = 0; i < PIT_LEN; i += 7) g.fillRect(i, 0, 3, 44);

  g.fillStyle = 'rgba(130,100,55,0.55)';
  g.fillRect(0,0,PIT_LEN,1);
  g.fillRect(0,43,PIT_LEN,1);

  // metre lines
  for (let m = 1; m <= 12; m++){
    const x = m*PPM;
    if (x >= PIT_LEN) break;
    g.fillStyle = 'rgba(120,90,50,0.38)';
    g.fillRect(x, 3, 1, 30);
  }

  // tape strip
  g.fillStyle = '#f0d060'; g.fillRect(0, 33, PIT_LEN, 11);
  g.fillStyle = '#a08030'; g.fillRect(0, 33, PIT_LEN, 1);
  g.fillStyle = 'rgba(255,255,255,0.35)'; g.fillRect(0, 34, PIT_LEN, 1);

  for (let m = 0; m <= 12; m++){
    const x = m*PPM;
    if (x >= PIT_LEN) break;
    g.fillStyle = '#3a2a10';
    g.fillRect(x, 33, 1, 4);
    textOn(g, String(m), x + 2, 35, '#3a2a10', 1);
  }
  return c;
})();

/* ============================================================
   POSES
   ============================================================ */
const STAND_POSE = { tA:8, kA:6, tB:-8, kB:6, uA:10, uB:10, lean:4 };

function poseRun(phase, speedFrac){
  const a = phase * Math.PI * 2;
  const T = 36, K = 62;
  return {
    tA: T*Math.sin(a),
    kA: Math.max(0, K - K*Math.sin(a + 0.9)),
    tB: T*Math.sin(a + Math.PI),
    kB: Math.max(0, K - K*Math.sin(a + Math.PI + 0.9)),
    uA: 44*Math.sin(a + Math.PI),
    uB: 44*Math.sin(a),
    lean: 6 + 13*speedFrac + 3*Math.sin(a*2)
  };
}

const FLY_KEYS = [
  {t:0.00, tA:-45, kA:18, tB: 22, kB: 55, uA:145, uB:120, lean: 6},
  {t:0.16, tA:-18, kA:72, tB: 48, kB: 98, uA:120, uB:100, lean: 9},
  {t:0.40, tA: 48, kA:112,tB: 34, kB:122, uA: 72, uB: 52, lean:11},
  {t:0.65, tA: 70, kA:48, tB: 58, kB: 58, uA: 34, uB: 14, lean:13},
  {t:0.85, tA: 63, kA:12, tB: 56, kB: 14, uA: 12, uB: -8, lean:15},
  {t:1.00, tA: 56, kA: 6, tB: 52, kB: 10, uA: 22, uB:  2, lean:17}
];
const LAND_KEYS = [
  {t:0.00, tA:56, kA: 6, tB:52, kB:10, uA:22, uB: 2, lean:17},
  {t:0.35, tA:68, kA:62, tB:64, kB:66, uA:58, uB:38, lean:26},
  {t:1.00, tA:52, kA:88, tB:48, kB:92, uA:78, uB:58, lean:32}
];

function lerpPose(keys, t){
  t = clamp(t, 0, 1);
  let i = 0;
  while (i < keys.length-1 && t > keys[i+1].t) i++;
  const a = keys[i], b = keys[Math.min(i+1, keys.length-1)];
  const span = b.t - a.t;
  const f = span > 0 ? (t - a.t)/span : 0;
  const o = {};
  for (const k in a) if (k !== 't') o[k] = a[k] + (b[k]-a[k])*f;
  return o;
}

function footDepth(t, k){
  return 7*Math.cos(t*RAD) + 7*Math.cos((t-k)*RAD);
}

/* ============================================================
   ATHLETE DRAWING
   ============================================================ */
function drawLeg(hx,hy,tA,kA,dark){
  const kx = hx + Math.sin(tA*RAD)*7;
  const ky = hy + Math.cos(tA*RAD)*7;
  const sa = (tA - kA)*RAD;
  const fx = kx + Math.sin(sa)*7;
  const fy = ky + Math.cos(sa)*7;
  limb(hx,hy,kx,ky,4, dark ? P.skinD : P.skin);
  limb(kx,ky,fx,fy,3, dark ? P.skinD : P.skin);
  ctx.fillStyle = dark ? P.shoeD : P.shoe;
  ctx.fillRect(Math.round(fx)-2, Math.round(fy)-1, 5, 3);
  ctx.fillStyle = dark ? '#8a8a8a' : '#d0d0d0';
  ctx.fillRect(Math.round(fx)-2, Math.round(fy)+1, 5, 1);
}

function drawArm(nx,ny,uA,dark){
  const ex = nx + Math.sin(uA*RAD)*5;
  const ey = ny + Math.cos(uA*RAD)*5;
  const fa = (uA + 105)*RAD;
  const hx = ex + Math.sin(fa)*5;
  const hy = ey + Math.cos(fa)*5;
  limb(nx,ny,ex,ey,3, dark ? P.topD : P.top);
  limb(ex,ey,hx,hy,2, dark ? P.skinD : P.skin);
  ctx.fillStyle = dark ? P.skinD : P.skin;
  ctx.fillRect(Math.round(hx)-1, Math.round(hy)-1, 3, 3);
}

function drawAthlete(hipX, hipY, p){
  const hx = Math.round(hipX), hy = Math.round(hipY);
  const lean = p.lean * RAD;
  const nx = hx + Math.sin(lean)*11;
  const ny = hy - Math.cos(lean)*11;

  // far leg (A)
  drawLeg(hx,hy,p.tA,p.kA,true);
  // far arm (B)
  drawArm(nx,ny,p.uB,true);
  // torso
  limb(hx,hy,nx,ny,6,P.topD);
  ctx.fillStyle = P.top;
  limb(hx,hy,nx,ny,5,P.top);
  // shorts
  ctx.fillStyle = P.short;
  ctx.fillRect(hx-4, hy-3, 8, 7);
  ctx.fillStyle = P.shortD;
  ctx.fillRect(hx-4, hy+3, 8, 1);
  // head
  const hdx = Math.round(nx + Math.sin(lean)*2);
  const hdy = Math.round(ny - Math.cos(lean)*2);
  ctx.fillStyle = P.skin;
  ctx.fillRect(hdx-2, hdy-4, 5, 6);
  ctx.fillStyle = P.hair;
  ctx.fillRect(hdx-3, hdy-6, 6, 3);
  ctx.fillRect(hdx-3, hdy-4, 2, 4);
  ctx.fillStyle = '#2a1c12';
  ctx.fillRect(hdx+2, hdy-2, 1, 1);
  // near leg (B)
  drawLeg(hx,hy,p.tB,p.kB,false);
  // near arm (A)
  drawArm(nx,ny,p.uA,false);
}

/* ============================================================
   GAME STATE
   ============================================================ */
const G = {
  state:'ready',
  t:0,
  time:0,
  attempt:0,
  results:[],
  best:0,
  last:0,
  dist:0,
  speed:0,
  x:0, hm:0,
  vx:0, vy:0,
  flightTime:1,
  phase:0,
  angle:45,
  angleT:0,
  foul:false,
  takeoffX:0,
  mark:null,
  camX:-140,
  particles:[],
  rec:[],
  takeoffRecIdx:0,
  replayFrames:[],
  replayIdx:0,
  replayPose:null,
  autoplay:true,
  aiSide:'L',
  aiTimer:0,
  lastSide:null,
  resultShown:false
};

function startAttempt(){
  G.state = 'ready';
  G.t = 0;
  G.speed = 0;
  G.x = 0; G.hm = 0; G.vx = 0; G.vy = 0;
  G.phase = 0;
  G.angle = 45; G.angleT = 0;
  G.foul = false;
  G.mark = null;
  G.dist = 0;
  G.particles.length = 0;
  G.rec.length = 0;
  G.takeoffRecIdx = 0;
  G.replayFrames = [];
  G.replayIdx = 0;
  G.replayPose = null;
  G.lastSide = null;
  G.aiTimer = 0;
  G.aiSide = 'L';
  G.camX = -140;
  G.resultShown = false;
}

function restartGame(){
  G.attempt = 0;
  G.results = [];
  G.best = 0;
  G.last = 0;
  startAttempt();
}

function pressRun(side){
  if (G.state !== 'run') return;
  if (side === G.lastSide) return;
  G.lastSide = side;
  G.speed = Math.min(MAX_SPEED, G.speed + PRESS_GAIN);
  G.phase += 0.5;
  if (G.phase >= 1) G.phase -= 1;
}

function doJump(forced){
  if (G.state !== 'run') return;
  G.state = 'fly';
  G.t = 0;
  G.takeoffX = G.x;
  G.foul = !!forced || (G.x > BOARD_X);
  const spd = Math.max(1.5, G.speed);
  const th = G.angle * RAD;
  G.vx = spd * Math.cos(th);
  G.vy = spd * Math.sin(th);
  G.flightTime = Math.max(0.15, 2*G.vy/GRAV);
  G.hm = 0.0001;
  G.takeoffRecIdx = G.rec.length;
}

function spawnSand(worldX, n){
  for (let i = 0; i < n; i++){
    const a = -Math.PI/2 + (Math.random()-0.5)*2.4;
    const sp = 30 + Math.random()*175;
    G.particles.push({
      x: worldX + (Math.random()-0.5)*12,
      y: GROUND_Y - 2 + Math.random()*5,
      vx: Math.cos(a)*sp*0.9 + (Math.random()-0.3)*45,
      vy: Math.sin(a)*sp,
      life: 0.45 + Math.random()*0.85,
      c: Math.random() < 0.5 ? '#e8c87a' : (Math.random() < 0.5 ? '#d4b070' : '#f5de9e'),
      s: Math.random() < 0.65 ? 1 : 2
    });
  }
}

function doLand(){
  G.state = 'land';
  G.t = 0;
  const landingX = G.x;
  let d = (landingX - BOARD_X) / PPM;
  if (d < 0) d = 0;
  if (G.foul) d = 0;
  G.dist = Math.round(d*10)/10;
  G.mark = { x: landingX };
  spawnSand(landingX, 34);
}

function finishAttempt(){
  G.results.push({ d: G.dist, foul: G.foul });
  if (!G.foul && G.dist > G.best) G.best = G.dist;
  G.last = G.foul ? 0 : G.dist;
}

function startReplay(){
  const start = Math.max(0, G.takeoffRecIdx - 52);
  G.replayFrames = G.rec.slice(start);
  if (G.replayFrames.length < 2){
    G.replayFrames = G.rec.slice(-2);
  }
  G.replayIdx = 0;
  G.replayPose = G.replayFrames[0] || null;
  G.state = 'replay';
  G.t = 0;
}

function nextAttempt(){
  G.attempt++;
  if (G.attempt >= 3){
    G.state = 'over';
    G.t = 0;
  } else {
    startAttempt();
  }
}

/* ============================================================
   RECORDING
   ============================================================ */
function currentPose(){
  if (G.state === 'fly') return lerpPose(FLY_KEYS, clamp(G.t/Math.max(0.01,G.flightTime),0,1));
  if (G.state === 'land') return lerpPose(LAND_KEYS, clamp(G.t/0.9,0,1));
  if (G.state === 'ready') return STAND_POSE;
  if (G.state === 'result' || G.state === 'over') return lerpPose(LAND_KEYS, 1);
  return poseRun(G.phase, Math.min(1, G.speed/MAX_SPEED));
}

function recordFrame(){
  const p = currentPose();
  G.rec.push({
    x: G.x, hm: G.hm, mode: G.state,
    tA:p.tA, kA:p.kA, tB:p.tB, kB:p.kB,
    uA:p.uA, uB:p.uB, lean:p.lean
  });
  if (G.rec.length > 1400){
    G.rec.splice(0, 300);
    G.takeoffRecIdx = Math.max(0, G.takeoffRecIdx - 300);
  }
}

/* ============================================================
   AI (AUTOPLAY)
   ============================================================ */
const AI_RATE = 11.6;
function aiRun(dt){
  if (G.state !== 'run') return;

  // mash alternately
  G.aiTimer -= dt;
  let guard = 0;
  while (G.aiTimer <= 0 && guard++ < 6){
    G.aiTimer += 1/AI_RATE;
    pressRun(G.aiSide);
    G.aiSide = (G.aiSide === 'L') ? 'R' : 'L';
  }

  // choose take-off moment: last 45° crossing before the board
  const v = Math.max(G.speed, 2.5);
  const tToBoard = (BOARD_X - 1 - G.x) / v;

  const half = ANGLE_PER/2;
  let t45 = Math.ceil((G.angleT + 1e-9)/half)*half - G.angleT;
  if (t45 < 0) t45 += half;

  const tNext = t45 + half;

  if (t45 <= tToBoard && tNext > tToBoard){
    if (t45 < 0.008) doJump(false);
  }
  if (tToBoard < 0.02) doJump(false);
}

/* ============================================================
   INPUT
   ============================================================ */
const LEFT_KEYS  = ['ArrowLeft','KeyA','KeyZ'];
const RIGHT_KEYS = ['ArrowRight','KeyD','KeyX'];
const JUMP_KEYS  = ['Space','ArrowUp','Enter','KeyK'];

window.addEventListener('keydown', function(e){
  const k = e.code;

  if (k === 'KeyP'){
    G.autoplay = !G.autoplay;
    e.preventDefault();
    return;
  }
  if (k === 'KeyR'){
    restartGame();
    e.preventDefault();
    return;
  }

  const isRun = LEFT_KEYS.indexOf(k) >= 0 || RIGHT_KEYS.indexOf(k) >= 0;
  const isJump = JUMP_KEYS.indexOf(k) >= 0;

  if (isRun || isJump){
    if (G.autoplay) G.autoplay = false;
    e.preventDefault();
  }

  if (G.state === 'over' && (isJump || isRun)){ restartGame(); return; }

  if (LEFT_KEYS.indexOf(k) >= 0)  pressRun('L');
  if (RIGHT_KEYS.indexOf(k) >= 0) pressRun('R');
  if (isJump && G.state === 'run') doJump(false);
}, { passive:false });

/* ============================================================
   UPDATE
   ============================================================ */
function updateParticles(dt){
  for (let i = G.particles.length-1; i >= 0; i--){
    const p = G.particles[i];
    p.vy += 620*dt;
    p.x += p.vx*dt;
    p.y += p.vy*dt;
    p.life -= dt;
    if (p.life <= 0 || p.y > 285) G.particles.splice(i,1);
  }
}

function updateCamera(dt){
  let tx = G.x - 150;
  tx = clamp(tx, -140, 560);
  G.camX += (tx - G.camX) * Math.min(1, dt*9);
}

function update(dt){
  G.time += dt;

  for (const c of CLOUDS){
    c.x -= c.s*dt;
    if (c.x < -90) c.x += 780;
  }

  updateParticles(dt);

  switch (G.state){
    case 'ready':
      G.t += dt;
      if (G.t > 0.75){ G.state = 'run'; G.t = 0; }
      break;

    case 'run': {
      G.t += dt;
      G.speed = Math.max(0, G.speed - G.speed*SPD_DECAY*dt);
      G.x += G.speed*dt*PPM;
      G.angleT += dt;
      G.angle = 45 + 25*Math.sin(G.angleT*2*Math.PI/ANGLE_PER);
      if (G.autoplay) aiRun(dt);
      recordFrame();
      if (G.x > BOARD_X + 2) doJump(true);
      break;
    }

    case 'fly': {
      G.t += dt;
      G.vy -= GRAV*dt;
      G.x += G.vx*dt*PPM;
      G.hm += G.vy*dt;
      recordFrame();
      if (G.hm <= 0){ G.hm = 0; doLand(); }
      break;
    }

    case 'land': {
      G.t += dt;
      recordFrame();
      if (G.t > 1.05){
        finishAttempt();
        G.state = 'result';
        G.t = 0;
      }
      break;
    }

    case 'result': {
      G.t += dt;
      if (G.t > 2.1) startReplay();
      break;
    }

    case 'replay': {
      G.t += dt;
      G.replayIdx += dt*60*0.5;
      const idx = Math.min(G.replayFrames.length-1, Math.floor(G.replayIdx));
      const f = G.replayFrames[idx];
      if (f){
        G.replayPose = f;
        G.x = f.x;
        G.hm = f.hm;
      }
      if (G.replayIdx >= G.replayFrames.length-1){
        G.state = 'replayEnd';
        G.t = 0;
      }
      break;
    }

    case 'replayEnd': {
      G.t += dt;
      if (G.t > 0.7) nextAttempt();
      break;
    }

    case 'over': {
      G.t += dt;
      if (G.t > 6.5) restartGame();
      break;
    }
  }

  updateCamera(dt);
}

/* ============================================================
   RENDER — BACKGROUND
   ============================================================ */
const SKY = ['#0a1330','#122048','#1b2e5e','#274177','#35558f','#476da6','#5c88bd','#78a6d4'];

function drawSky(){
  for (let i = 0; i < 8; i++){
    ctx.fillStyle = SKY[i];
    ctx.fillRect(0, i*9, W, 9);
  }
  ctx.fillStyle = '#8fc0e0';
  ctx.fillRect(0, 71, W, 1);

  // sun
  circle(392, 20, 9, '#ffe9a8');
  circle(392, 20, 7, '#fff6d0');

  // clouds
  for (const c of CLOUDS){
    const x = Math.round(c.x), y = Math.round(c.y), w = Math.round(c.w), h = Math.round(c.h);
    if (x > W+40 || x < -80) continue;
    ctx.fillStyle = '#dceaf8';
    ctx.fillRect(x, y + Math.round(h*0.45), w, Math.round(h*0.6));
    ctx.fillRect(x + Math.round(w*0.14), y, Math.round(w*0.52), h);
    ctx.fillRect(x + Math.round(w*0.48), y + Math.round(h*0.2), Math.round(w*0.42), Math.round(h*0.8));
    ctx.fillStyle = '#b3cbe4';
    ctx.fillRect(x, y + h, w, 1);
  }
}

function drawFlags(off){
  const t = G.time;
  for (let copy = 0; copy < 2; copy++){
    const baseX = -off + copy*480;
    for (const f of FLAG_POS){
      const x = Math.round(baseX + f.x);
      if (x < -24 || x > W+8) continue;
      ctx.fillStyle = '#c8c8d0';
      ctx.fillRect(x, 18, 1, 42);
      ctx.fillStyle = '#8a8a98';
      ctx.fillRect(x+1, 18, 1, 42);
      for (let i = 0; i < 14; i++){
        const fy = 21 + Math.round(Math.sin(t*5 + i*0.5)*2);
        ctx.fillStyle = (i < 7) ? f.c1 : f.c2;
        ctx.fillRect(x+1+i, fy, 1, 8);
      }
    }
  }
}

function drawStands(){
  const off = wrap(G.camX*0.12, 480);
  ctx.drawImage(crowdTile, Math.round(-off), 58);
  ctx.drawImage(crowdTile, Math.round(-off + 480), 58);

  // animated waving
  const t = G.time;
  for (let copy = 0; copy < 2; copy++){
    const baseX = -off + copy*480;
    if (baseX > W+8 || baseX < -488) continue;
    for (const w of WAVERS){
      const x = Math.round(baseX + w.x);
      if (x < -6 || x > W+6) continue;
      const y = 58 + w.y;
      const s = Math.sin(t*6 + w.ph);
      const up1 = s > 0 ? 2 : 0;
      const up2 = s > 0 ? 0 : 2;
      ctx.fillStyle = '#f0c8a0';
      ctx.fillRect(x-1, y - 1 - up1, 1, 3 + up1);
      ctx.fillRect(x+4, y - 1 - up2, 1, 3 + up2);
    }
  }
}

function drawAds(cam){
  const scroll = cam*0.9;
  const off = wrap(scroll, 64);
  const base = Math.floor(scroll/64);
  const cols = ['#c23a3a','#3a5ac2','#e0c040','#3aa85a','#c23a9a','#d8d8d8'];
  for (let i = -1; i < 9; i++){
    const x = Math.round(i*64 - off);
    const idx = ((i + base) % 6 + 6) % 6;
    ctx.fillStyle = '#14182a';
    ctx.fillRect(x, 168, 64, 16);
    ctx.fillStyle = cols[idx];
    ctx.fillRect(x+1, 170, 62, 12);
    ctx.fillStyle = 'rgba(0,0,0,0.22)';
    ctx.fillRect(x+1, 178, 62, 4);
    ctx.fillStyle = 'rgba(255,255,255,0.4)';
    ctx.fillRect(x+1, 170, 62, 1);
    ctx.fillStyle = 'rgba(0,0,0,0.35)';
    ctx.fillRect(x+30, 170, 2, 12);
  }
}

function drawTrack(cam){
  // verge
  ctx.fillStyle = '#2a6a38';
  ctx.fillRect(0, 182, W, 12);
  ctx.fillStyle = '#37864a';
  ctx.fillRect(0, 182, W, 2);
  ctx.fillStyle = '#1e5029';
  ctx.fillRect(0, 192, W, 2);
  // grass tufts
  const gOff = wrap(cam, 24);
  for (let i = -1; i < 22; i++){
    const x = Math.round(i*24 - gOff);
    ctx.fillStyle = '#46965a';
    ctx.fillRect(x, 187, 2, 3);
    ctx.fillRect(x+7, 189, 2, 2);
  }

  // track base
  ctx.fillStyle = '#9c3f28';
  ctx.fillRect(0, 194, W, H-194);
  ctx.fillStyle = '#b8503a';
  ctx.fillRect(0, 202, W, 36);
  ctx.fillStyle = '#e8e0d8';
  ctx.fillRect(0, 202, W, 1);
  ctx.fillRect(0, 237, W, 1);
  ctx.fillStyle = 'rgba(0,0,0,0.14)';
  ctx.fillRect(0, 238, W, 3);

  // runway texture
  const rOff = wrap(cam, 36);
  ctx.fillStyle = 'rgba(0,0,0,0.06)';
  for (let i = -1; i < 16; i++){
    ctx.fillRect(Math.round(i*36 - rOff), 204, 2, 33);
  }

  // ---- take-off board ----
  const bx = Math.round(BOARD_X - cam);
  ctx.fillStyle = '#e8e8e8';
  ctx.fillRect(bx-BOARD_W, 200, BOARD_W, 42);
  ctx.fillStyle = '#c8c8c8';
  ctx.fillRect(bx-BOARD_W, 200, BOARD_W, 2);
  ctx.fillRect(bx-BOARD_W, 240, BOARD_W, 2);
  ctx.fillStyle = '#b0b0b0';
  ctx.fillRect(bx-BOARD_W, 218, BOARD_W, 1);
  // foul line
  ctx.fillStyle = '#e03030';
  ctx.fillRect(bx-3, 200, 3, 42);
  ctx.fillStyle = '#ff6060';
  ctx.fillRect(bx-3, 200, 1, 42);

  // ---- pit ----
  const px = Math.round(PIT_START - cam);
  ctx.drawImage(pitCanvas, px, 200);
  // pit rim
  ctx.fillStyle = '#8a6a3a';
  ctx.fillRect(px-2, 199, 2, 45);
  ctx.fillRect(px+PIT_LEN, 199, 2, 45);

  // ---- world record line ----
  const wrx = Math.round(BOARD_X + WR*PPM - cam);
  if (wrx > -10 && wrx < W+10){
    ctx.fillStyle = '#ff4040';
    for (let y = 196; y < 246; y += 3) ctx.fillRect(wrx, y, 1, 2);
    drawText('WR', wrx-6, 190, '#ff6060', 1);
  }

  // ---- best mark line ----
  if (G.best > 0.05){
    const bmx = Math.round(BOARD_X + G.best*PPM - cam);
    if (bmx > -10 && bmx < W+10){
      ctx.fillStyle = '#40e070';
      for (let y = 196; y < 246; y += 3) ctx.fillRect(bmx, y, 1, 2);
      drawText('PB', bmx-6, 183, '#60ff90', 1);
    }
  }

  // ---- landing mark ----
  if (G.mark){
    const mx = Math.round(G.mark.x - cam);
    ctx.fillStyle = '#d8b878';
    ctx.fillRect(mx-7, 202, 14, 2);
    ctx.fillStyle = '#b89050';
    ctx.fillRect(mx-5, 204, 10, 4);
    ctx.fillStyle = '#9c7840';
    ctx.fillRect(mx-4, 206, 8, 3);
    ctx.fillStyle = '#8c6838';
    ctx.fillRect(mx-4, 209, 3, 6);
    ctx.fillRect(mx+1, 209, 3, 6);
    ctx.fillStyle = '#c9a45c';
    ctx.fillRect(mx-8, 203, 4, 2);
    ctx.fillRect(mx+4, 203, 4, 2);
  }
}

function drawMeasureLine(){
  if (G.foul || !G.mark) return;
  if (G.state !== 'result' && G.state !== 'replay' && G.state !== 'replayEnd') return;
  const x0 = Math.round(BOARD_X - G.camX);
  const x1 = Math.round(G.mark.x - G.camX);
  if (x1 - x0 < 2) return;
  const y = 197;
  ctx.fillStyle = '#ffe060';
  ctx.fillRect(x0, y, x1-x0, 1);
  ctx.fillRect(x0, y-4, 1, 9);
  ctx.fillRect(x1, y-4, 1, 9);
  const mid = Math.round((x0+x1)/2);
  const label = G.dist.toFixed(1) + ' M';
  const lw = label.length*6 - 1;
  ctx.fillStyle = 'rgba(8,12,26,0.75)';
  ctx.fillRect(mid - lw/2 - 3, y-18, lw + 6, 11);
  drawText(label, mid - lw/2, y-16, '#ffe060', 1);
}

function drawParticles(){
  for (const p of G.particles){
    ctx.globalAlpha = Math.min(1, p.life*3.2);
    ctx.fillStyle = p.c;
    ctx.fillRect(Math.round(p.x - G.camX), Math.round(p.y), p.s, p.s);
  }
  ctx.globalAlpha = 1;
}

/* ============================================================
   RENDER — ATHLETE
   ============================================================ */
function renderAthlete(){
  let p, hipX, hipY, hm, mode;

  if (G.state === 'replay' && G.replayPose){
    const f = G.replayPose;
    p = { tA:f.tA, kA:f.kA, tB:f.tB, kB:f.kB, uA:f.uA, uB:f.uB, lean:f.lean };
    hipX = f.x - G.camX;
    hm = f.hm;
    mode = f.mode;
  } else {
    p = currentPose();
    hipX = G.x - G.camX;
    hm = G.hm;
    mode = G.state;
  }

  if (mode === 'fly'){
    hipY = GROUND_Y - 11 - hm*PPM;
  } else {
    const fy = Math.max(footDepth(p.tA,p.kA), footDepth(p.tB,p.kB));
    hipY = GROUND_Y - fy;
  }

  // shadow
  const shScale = clamp(1 - hm*0.22, 0.35, 1);
  ctx.fillStyle = 'rgba(0,0,0,0.22)';
  ctx.fillRect(Math.round(hipX - 6*shScale), GROUND_Y+1, Math.round(12*shScale), 2);

  drawAthlete(hipX, hipY, p);
}

/* ============================================================
   RENDER — HUD
   ============================================================ */
function drawHUD(){
  // ---- top panel ----
  ctx.fillStyle = 'rgba(6,10,24,0.86)';
  ctx.fillRect(0, 0, W, 24);
  ctx.fillStyle = '#2a3a60';
  ctx.fillRect(0, 24, W, 1);

  drawText('SPEED', 6, 6, '#8fb8ff', 1);

  const bx = 46, by = 6, bw = 128, bh = 11;
  ctx.fillStyle = '#0a1020';
  ctx.fillRect(bx, by, bw, bh);
  const f = clamp(G.speed/MAX_SPEED, 0, 1);
  const col = f < 0.5 ? '#38c860' : (f < 0.8 ? '#e0d040' : '#f05030');
  ctx.fillStyle = col;
  ctx.fillRect(bx+1, by+1, Math.floor((bw-2)*f), bh-2);
  ctx.fillStyle = 'rgba(255,255,255,0.25)';
  ctx.fillRect(bx+1, by+1, Math.floor((bw-2)*f), 2);
  ctx.fillStyle = '#2a3a60';
  for (let i = 1; i < 10; i++) ctx.fillRect(bx + Math.floor(bw*i/10), by+1, 1, bh-2);
  ctx.fillStyle = '#5a7aa8';
  ctx.fillRect(bx, by, bw, 1); ctx.fillRect(bx, by+bh-1, bw, 1);
  ctx.fillRect(bx, by, 1, bh); ctx.fillRect(bx+bw-1, by, 1, bh);

  drawText('ATT ' + (G.attempt+1) + '/3', 186, 6, '#ffffff', 1);
  drawText('LAST ' + (G.last > 0.05 ? G.last.toFixed(1) : '--'), 252, 6, '#8fd0ff', 1);
  drawText('BEST ' + (G.best > 0.05 ? G.best.toFixed(1) : '--'), 322, 6, '#ffe060', 1);
  drawText('WR ' + WR.toFixed(2), 400, 6, '#ff8080', 1);

  // ---- bottom panel ----
  ctx.fillStyle = 'rgba(6,10,24,0.82)';
  ctx.fillRect(0, 250, W, 20);
  ctx.fillStyle = '#2a3a60';
  ctx.fillRect(0, 250, W, 1);

  drawText('ANGLE', 6, 256, '#8fb8ff', 1);

  const gx = 46, gy = 255, gw = 120, gh = 11;
  ctx.fillStyle = '#0a1020';
  ctx.fillRect(gx, gy, gw, gh);
  // optimal zone 42-48 deg
  const z0 = (42-20)/50, z1 = (48-20)/50;
  ctx.fillStyle = 'rgba(60,220,110,0.35)';
  ctx.fillRect(gx + Math.floor(z0*gw), gy+1, Math.max(2,Math.floor((z1-z0)*gw)), gh-2);
  // ticks
  ctx.fillStyle = '#2a3a60';
  for (let i = 1; i < 10; i++) ctx.fillRect(gx + Math.floor(gw*i/10), gy+1, 1, gh-2);
  // marker
  const af = clamp((G.angle-20)/50, 0, 1);
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(gx + Math.floor(af*gw)-1, gy-2, 2, gh+4);
  ctx.fillStyle = '#ffe060';
  ctx.fillRect(gx + Math.floor(af*gw)-1, gy-2, 2, 1);
  ctx.fillStyle = '#5a7aa8';
  ctx.fillRect(gx, gy, gw, 1); ctx.fillRect(gx, gy+gh-1, gw, 1);
  ctx.fillRect(gx, gy, 1, gh); ctx.fillRect(gx+gw-1, gy, 1, gh);

  const angTxt = 'ANGLE ' + Math.round(G.angle);
  drawText(angTxt, gx+gw+8, 256, (G.angle > 42 && G.angle < 48) ? '#60ff90' : '#ffffff', 1);

  // speed numeric
  drawText('SPD ' + G.speed.toFixed(1) + ' M/S', 260, 256, '#a0c8ff', 1);

  // demo indicator
  if (G.autoplay){
    ctx.fillStyle = 'rgba(224,60,60,0.9)';
    ctx.fillRect(404, 253, 70, 14);
    drawText('DEMO  P', 408, 257, '#ffffff', 1);
  } else {
    drawText('P=DEMO', 408, 257, '#5a7aa8', 1);
  }
}

/* ============================================================
   RENDER — OVERLAYS
   ============================================================ */
function drawResultPanel(){
  if (G.state !== 'result' && G.state !== 'replay' && G.state !== 'replayEnd') return;

  const px = 150, py = 38, pw = 180, ph = 52;
  ctx.fillStyle = 'rgba(6,10,24,0.88)';
  ctx.fillRect(px, py, pw, ph);
  ctx.fillStyle = '#3a5a9a';
  ctx.fillRect(px, py, pw, 2);
  ctx.fillRect(px, py+ph-2, pw, 2);
  ctx.fillRect(px, py, 2, ph);
  ctx.fillRect(px+pw-2, py, 2, ph);

  drawTextC('DISTANCE', py+6, '#8fb8ff', 1);

  if (G.foul){
    drawTextC('FOUL!', py+20, '#ff5050', 3);
  } else {
    const s = G.dist.toFixed(1) + ' M';
    const w = s.length*6*3 - 3;
    drawText(s, Math.round((W-w)/2), py+18, '#ffe060', 3);
  }
}

function drawReplayBanner(){
  if (G.state !== 'replay' && G.state !== 'replayEnd') return;
  ctx.fillStyle = 'rgba(6,10,24,0.7)';
  ctx.fillRect(0, 30, W, 14);
  drawTextC('R E P L A Y   -   S L O W   M O T I O N', 33, '#ff8080', 1);
  // vignette
  ctx.fillStyle = 'rgba(0,0,0,0.18)';
  ctx.fillRect(0, 44, W, 4);
  ctx.fillRect(0, 246, W, 4);
}

function drawGoText(){
  if (G.state !== 'ready') return;
  const a = clamp(1 - G.t/0.75, 0, 1);
  ctx.globalAlpha = a;
  drawTextC('GO!', 90, '#ffe060', 4);
  ctx.globalAlpha = 1;
}

function drawResultsScreen(){
  if (G.state !== 'over') return;
  ctx.fillStyle = 'rgba(4,8,20,0.92)';
  ctx.fillRect(48, 38, 384, 194);
  ctx.fillStyle = '#3a5a9a';
  ctx.fillRect(48, 38, 384, 2);
  ctx.fillRect(48, 230, 384, 2);
  ctx.fillRect(48, 38, 2, 194);
  ctx.fillRect(430, 38, 2, 194);

  drawTextC('FINAL RESULTS', 52, '#ffe060', 2);

  for (let i = 0; i < 3; i++){
    const r = G.results[i];
    const y = 84 + i*26;
    drawText('ATTEMPT ' + (i+1), 76, y, '#8fb8ff', 2);
    if (r){
      if (r.foul) drawText('FOUL', 292, y, '#ff6060', 2);
      else        drawText(r.d.toFixed(1) + ' M', 292, y, '#ffffff', 2);
    } else {
      drawText('--', 292, y, '#4a5470', 2);
    }
  }

  drawText('BEST', 76, 168, '#8fb8ff', 2);
  drawText(G.best.toFixed(1) + ' M', 292, 168, '#60ff90', 2);

  if (G.best > WR){
    drawTextC('NEW WORLD RECORD!', 198, '#ffd040', 1);
  } else {
    drawTextC('WORLD RECORD ' + WR.toFixed(2) + ' M', 198, '#98a2c0', 1);
  }
}

/* ============================================================
   MAIN RENDER
   ============================================================ */
function render(){
  ctx.clearRect(0, 0, W, H);

  drawSky();

  const off = wrap(G.camX*0.12, 480);
  drawFlags(off);
  drawStands();

  drawAds(G.camX);
  drawTrack(G.camX);
  drawMeasureLine();

  renderAthlete();
  drawParticles();

  drawHUD();
  drawGoText();
  drawResultPanel();
  drawReplayBanner();
  drawResultsScreen();
}

/* ============================================================
   MAIN LOOP
   ============================================================ */
let lastT = performance.now();
function frame(now){
  let dt = (now - lastT)/1000;
  lastT = now;
  if (dt > 0.05) dt = 0.05;
  if (dt < 0) dt = 0;

  update(dt);
  render();

  requestAnimationFrame(frame);
}

/* ============================================================
   BOOT
   ============================================================ */
startAttempt();
requestAnimationFrame(function(t){
  lastT = t;
  requestAnimationFrame(frame);
});

})();
</script>
</body>
</html>
```
### Gameplay & Visual Feedback

A quick mash of alternating keys builds speed, a swinging angle meter sets your launch, and every landing is tracked with a visible mark.

- **Controls:** Tap left/right keys alternately to sprint; press Space, Up, or K to jump. The angle meter swings while you run — jump near 42–48° for a good arc.
- **Attempts & fouls:** You get three jumps. Cross the take-off board and it's a foul; the distance won't count. Your best mark and the world record line are shown on the runway.
- **Live feedback:** The HUD shows speed, angle, attempt count, last jump, and best. After landing, a puff of sand particles rises and the landing spot stays marked.
- **Replay & results:** A slow-motion replay of the jump plays automatically, then the results screen lists all three attempts with distances or fouls.
- **Demo mode:** Press P to toggle an AI that runs and jumps competently, so you can watch a good run without pressing anything.
---

**Optimization Tip:** You can adjust the game's difficulty by editing MAX_SPEED (maximum sprint speed), PRESS_GAIN (how much each alternating tap adds), and GRAV (jump gravity) near the top of the script. The WR constant sets the world record line's distance.