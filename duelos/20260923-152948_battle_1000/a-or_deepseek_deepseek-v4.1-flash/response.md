Here’s a self-running mass battle simulation in a single HTML file. Two 500-unit armies charge, fight, and celebrate victory automatically, with live survivor counts and a fresh battle after each round.
```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
<title>Mass Battle Simulation</title>
<style>
  html,body{margin:0;padding:0;width:100%;height:100%;overflow:hidden;background:#0a0d08;}
  #cv{display:block;position:absolute;inset:0;width:100%;height:100%;}
  #hud{position:absolute;inset:0;pointer-events:none;
       font-family:"Trebuchet MS","Segoe UI",Helvetica,Arial,sans-serif;
       -webkit-user-select:none;user-select:none;}
  #title{position:absolute;top:12px;left:0;right:0;text-align:center;
         font-family:Georgia,"Times New Roman",serif;
         font-size:clamp(16px,2.5vw,32px);letter-spacing:.15em;text-transform:uppercase;
         color:#f3e9d2;text-shadow:0 2px 10px #000,0 0 32px rgba(255,170,60,.35);}
  #sub{position:absolute;top:calc(12px + clamp(21px,2.9vw,38px));left:0;right:0;text-align:center;
       font-size:clamp(9px,1.05vw,12px);letter-spacing:.42em;text-transform:uppercase;
       color:#a9986f;text-shadow:0 1px 6px #000;}
  .army{position:absolute;top:14px;width:180px;}
  .army.left{left:18px;text-align:left;}
  .army.right{right:18px;text-align:right;}
  .army .n{font-family:Georgia,serif;font-size:clamp(19px,3.1vw,38px);line-height:1;
           font-weight:bold;text-shadow:0 2px 10px #000;font-variant-numeric:tabular-nums;}
  .army .nm{font-size:clamp(8px,1vw,11px);letter-spacing:.2em;text-transform:uppercase;
            color:#cbbf9f;margin-top:3px;text-shadow:0 1px 5px #000;}
  .army .bar{height:5px;margin-top:6px;background:rgba(255,255,255,.13);
             border-radius:3px;overflow:hidden;}
  .army .bar i{display:block;height:100%;width:100%;border-radius:3px;
               transition:width .18s linear;}
  .army.right .bar i{margin-left:auto;}
  .red .n{color:#ff6a5a;} .red .bar i{background:linear-gradient(90deg,#8e1b12,#ff5a44);}
  .blue .n{color:#63a8ff;} .blue .bar i{background:linear-gradient(90deg,#1b4a9c,#5aa8ff);}
  #banner{position:absolute;top:43%;left:0;right:0;text-align:center;
          font-family:Georgia,"Times New Roman",serif;font-size:clamp(19px,4vw,52px);
          letter-spacing:.11em;text-transform:uppercase;opacity:0;
          transition:opacity .8s ease;
          text-shadow:0 3px 18px #000,0 0 50px rgba(0,0,0,.95);}
  #banner.show{opacity:1;}
</style>
</head>
<body>
<canvas id="cv"></canvas>
<div id="hud">
  <div id="title">&mdash;</div>
  <div id="sub">ENGAGEMENT I</div>
  <div class="army left red">
    <div class="n" id="redN">500</div>
    <div class="nm" id="redName">Crimson Host</div>
    <div class="bar"><i id="redBar"></i></div>
  </div>
  <div class="army right blue">
    <div class="n" id="blueN">500</div>
    <div class="nm" id="blueName">Azure Legion</div>
    <div class="bar"><i id="blueBar"></i></div>
  </div>
  <div id="banner"></div>
</div>
<script>
(function(){
'use strict';

/* ==================================================================
   CANVAS / VIEW
   ================================================================== */
const cv  = document.getElementById('cv');
const ctx = cv.getContext('2d', { alpha:false });

const FIELD_W = 4400, FIELD_D = 1600;      // world units
const S_FAR = 0.55, S_NEAR = 1.15, PERSP = 1.35;
const SPRITE_WORLD = 62;                   // world-size of one sprite quad

let W = 0, H = 0, DPR = 1;
const view = { cx:0, horizon:0, fieldH:0, k:1 };

/* depth lookup table : s = (y/D)^PERSP  */
const LUT_N = 512;
const lut = new Float32Array(LUT_N + 1);
const INV_STEP = LUT_N / FIELD_D;
for (let i = 0; i <= LUT_N; i++) lut[i] = Math.pow(i / LUT_N, PERSP);

function depthS(y){
  const f = y * INV_STEP;
  if (f <= 0) return 0;
  if (f >= LUT_N) return 1;
  const i = f | 0;
  return lut[i] + (lut[i+1] - lut[i]) * (f - i);
}

/* ==================================================================
   SPRITES (pre-rendered, 16 rotations per side + white hit-flash)
   ================================================================== */
const ROT_N = 16, SPR = 48;
let sprites = [];

const SIDES = [
  { name:'CRIMSON HOST', body:'#bf3327', mid:'#7d1c14', ui:'#ff5a44' },
  { name:'AZURE LEGION', body:'#2c68bf', mid:'#173f85', ui:'#5aa8ff' }
];

function drawSoldier(body, mid, head, weapon, ang, white){
  const c = document.createElement('canvas');
  c.width = SPR; c.height = SPR;
  const g = c.getContext('2d');
  g.translate(SPR/2, SPR/2);
  g.rotate(ang);

  if (!white){
    g.fillStyle = 'rgba(0,0,0,0.32)';
    g.beginPath(); g.ellipse(0.6, 2.8, 12.4, 9.4, 0, 0, 6.2832); g.fill();
  }
  /* coat / legs */
  g.fillStyle = white ? '#ffffff' : mid;
  g.beginPath(); g.ellipse(-2.6, 0, 10.4, 7.4, 0, 0, 6.2832); g.fill();
  /* torso */
  g.fillStyle = white ? '#ffffff' : body;
  g.beginPath(); g.ellipse(0.6, 0, 10.0, 7.8, 0, 0, 6.2832); g.fill();
  /* shoulder pads */
  g.fillStyle = white ? '#ffffff' : mid;
  g.beginPath(); g.ellipse(-0.6, -6.6, 4.6, 4.2, 0, 0, 6.2832); g.fill();
  g.beginPath(); g.ellipse(-0.6,  6.6, 4.6, 4.2, 0, 0, 6.2832); g.fill();
  /* helmet */
  g.fillStyle = white ? '#ffffff' : head;
  g.beginPath(); g.arc(3.6, 0, 4.9, 0, 6.2832); g.fill();
  /* weapon */
  if (!white){
    g.strokeStyle = weapon;
    g.lineWidth = 2.1;
    g.lineCap = 'round';
    g.beginPath(); g.moveTo(5, 6.2); g.lineTo(19.5, 2.2); g.stroke();
  }
  return c;
}

function buildSprites(){
  sprites = [];
  for (let si = 0; si < 2; si++){
    const col = SIDES[si], arr = [];
    for (let r = 0; r < ROT_N; r++){
      const a = r / ROT_N * Math.PI * 2;
      arr.push({
        n: drawSoldier(col.body, col.mid, '#ccd4dc', '#e6e6e6', a, false),
        w: drawSoldier('#fff','#fff','#fff','#fff', a, true)
      });
    }
    sprites.push(arr);
  }
}

/* ==================================================================
   BACKGROUND (static, pre-rendered once)
   ================================================================== */
let bgCanvas = null, bgCtx = null;
let tufts = [];

function makeTufts(){
  tufts = [];
  for (let i = 0; i < 1100; i++){
    tufts.push({
      x: Math.random()*FIELD_W,
      y: Math.random()*FIELD_D,
      l: 5 + Math.random()*11,
      h: Math.random()*0.35
    });
  }
}

function buildBackground(){
  bgCanvas = document.createElement('canvas');
  bgCanvas.width  = Math.max(1, Math.floor(W*DPR));
  bgCanvas.height = Math.max(1, Math.floor(H*DPR));
  bgCtx = bgCanvas.getContext('2d');
  bgCtx.setTransform(DPR,0,0,DPR,0,0);

  /* --- sky --- */
  const skyH = view.horizon + 26;
  const sky = bgCtx.createLinearGradient(0, 0, 0, skyH);
  sky.addColorStop(0.00, '#141b26');
  sky.addColorStop(0.55, '#4a5670');
  sky.addColorStop(1.00, '#9c9madd'.slice(0,7));
  bgCtx.fillStyle = sky;
  bgCtx.fillRect(0, 0, W, skyH);

  /* --- distant hills --- */
  bgCtx.fillStyle = '#2b3327';
  bgCtx.beginPath();
  bgCtx.moveTo(0, view.horizon + 3);
  for (let x = 0; x <= W; x += W/28){
    const h = view.horizon - 9 - Math.sin(x*0.011)*10 - Math.sin(x*0.037+2.1)*5;
    bgCtx.lineTo(x, h);
  }
  bgCtx.lineTo(W, view.horizon + 3);
  bgCtx.closePath();
  bgCtx.fill();

  /* --- field trapezoid --- */
  const yFar  = view.horizon;
  const yNear = view.horizon + view.fieldH;
  const halfFar  = FIELD_W*0.5*view.k*S_FAR;
  const halfNear = FIELD_W*0.5*view.k*S_NEAR;

  const fg = bgCtx.createLinearGradient(0, yFar, 0, yNear);
  fg.addColorStop(0.00, '#33402a');
  fg.addColorStop(0.30, '#4a5c33');
  fg.addColorStop(0.68, '#617a3e');
  fg.addColorStop(1.00, '#7d9750');

  bgCtx.beginPath();
  bgCtx.moveTo(view.cx - halfFar,  yFar);
  bgCtx.lineTo(view.cx + halfFar,  yFar);
  bgCtx.lineTo(view.cx + halfNear, yNear);
  bgCtx.lineTo(view.cx - halfNear, yNear);
  bgCtx.closePath();
  bgCtx.save();
  bgCtx.clip();
  bgCtx.fillStyle = fg;
  bgCtx.fillRect(0, yFar, W, yNear - yFar + 2);

  /* --- dirt patches --- */
  for (let i = 0; i < 26; i++){
    const wx = Math.random()*FIELD_W;
    const wy = Math.random()*FIELD_D;
    const s  = depthS(wy);
    const ps = S_FAR + (S_NEAR-S_FAR)*s;
    const sx = view.cx + (wx - FIELD_W*0.5)*view.k*ps;
    const sy = view.horizon + view.fieldH*s;
    const rr = (30 + Math.random()*70) * view.k * ps;
    bgCtx.fillStyle = 'rgba(90,74,48,' + (0.10 + Math.random()*0.13).toFixed(3) + ')';
    bgCtx.beginPath();
    bgCtx.ellipse(sx, sy, rr*1.7, rr*0.55, 0, 0, 6.2832);
    bgCtx.fill();
  }

  /* --- grass tufts --- */
  for (let i = 0; i < tufts.length; i++){
    const t  = tufts[i];
    const s  = depthS(t.y);
    const ps = S_FAR + (S_NEAR-S_FAR)*s;
    const sx = view.cx + (t.x - FIELD_W*0.5)*view.k*ps;
    const sy = view.horizon + view.fieldH*s;
    const ln = t.l * view.k * ps * 1.6;
    if (ln < 0.4) continue;
    const g2 = 0.30 + t.h;
    bgCtx.strokeStyle = 'rgba(' + ((70 + t.h*60)|0) + ',' + ((105 + t.h*70)|0) + ',' + ((50 + t.h*40)|0) + ',0.55)';
    bgCtx.lineWidth = Math.max(0.6, ln*0.22);
    bgCtx.beginPath();
    bgCtx.moveTo(sx, sy);
    bgCtx.lineTo(sx + ln*0.32, sy - ln);
    bgCtx.stroke();
  }
  bgCtx.restore();

  /* --- soft edge darkening --- */
  const vig = bgCtx.createLinearGradient(0, H*0.35, 0, H);
  vig.addColorStop(0, 'rgba(0,0,0,0)');
  vig.addColorStop(1, 'rgba(0,0,0,0.28)');
  bgCtx.fillStyle = vig;
  bgCtx.fillRect(0, H*0.35, W, H*0.65);
}

/* ==================================================================
   PARTICLE POOL
   ================================================================== */
const MAX_PARTS = 700;
const parts = [];
for (let i = 0; i < MAX_PARTS; i++){
  parts.push({life:0, maxLife:1, x:0, y:0, vx:0, vy:0, size:1, r:255, g:0, b:0, drag:0.9});
}
let pCursor = 0;

function emit(x, y, vx, vy, life, size, r, g, b, drag){
  const p = parts[pCursor];
  pCursor = (pCursor + 1) % MAX_PARTS;
  p.x = x; p.y = y; p.vx = vx; p.vy = vy;
  p.life = life; p.maxLife = life; p.size = size;
  p.r = r; p.g = g; p.b = b; p.drag = drag;
}

function spawnBlood(x, y){
  const n = 7 + ((Math.random()*6)|0);
  for (let i = 0; i < n; i++){
    const a = Math.random()*6.2832;
    const sp = 30 + Math.random()*110;
    emit(x, y, Math.cos(a)*sp, Math.sin(a)*sp*0.7,
         0.5 + Math.random()*0.6,
         1.2 + Math.random()*2.6,
         110 + Math.random()*90 | 0, 12 + Math.random()*20 | 0, 12 + Math.random()*18 | 0,
         0.86);
  }
  /* dust puff */
  for (let i = 0; i < 5; i++){
    const a = Math.random()*6.2832;
    const sp = 12 + Math.random()*40;
    emit(x, y, Math.cos(a)*sp, Math.sin(a)*sp*0.6,
         0.5 + Math.random()*0.5, 2 + Math.random()*3.5,
         150, 138, 104, 0.9);
  }
}

/* ==================================================================
   SIMULATION STATE
   ================================================================== */
const N_SIDE = 500;
const COLS = 50, ROWS = 10, SX = 34, SY = 64;
const ARMY_CX = [950, 3450], ARMY_CY = 800;

const units = [];
const rl = [];                 // render list
const counts = [N_SIDE, N_SIDE];

let time = 0, phaseT = 0, phase = 'charge', winner = -1, battleNo = 0;
let lastName = '';

/* spatial grid */
const CELL = 64;
const GW = Math.ceil(FIELD_W / CELL);
const GH = Math.ceil(FIELD_D / CELL);
const grid = new Array(GW*GH);
for (let i = 0; i < grid.length; i++) grid[i] = [];

const SEP = 30, SEP2 = SEP*SEP, REACH = 40;

/* ==================================================================
   SPAWN
   ================================================================== */
function makeUnit(side, x, y){
  return {
    side, x, y, vx:0, vy:0,
    hp: 100,
    speed: 128 + Math.random()*58,
    dmg: 17 + Math.random()*9,
    atkInt: 0.30 + Math.random()*0.17,
    cool: Math.random()*0.35,
    target: null,
    retargetT: Math.random()*0.45,
    engaged: false,
    flash: 0,
    alive: true,
    rot: side === 0 ? 0 : 8,
    seed: Math.random()*100,
    gx: 0, gy: 0
  };
}

function spawnArmies(){
  units.length = 0;
  for (let side = 0; side < 2; side++){
    const bx = ARMY_CX[side];
    for (let r = 0; r < ROWS; r++){
      for (let c = 0; c < COLS; c++){
        const x = bx + (c - (COLS-1)/2)*SX + (Math.random()-0.5)*7;
        const y = ARMY_CY + (r - (ROWS-1)/2)*SY + (Math.random()-0.5)*10;
        units.push(makeUnit(side, x, y));
      }
    }
  }
  /* initial targets: nearest enemy (one-time full scan, cheap) */
  for (let i = 0; i < units.length; i++){
    const u = units[i];
    let best = null, bd = Infinity;
    for (let j = 0; j < units.length; j++){
      const v = units[j];
      if (v.side === u.side) continue;
      const dx = v.x-u.x, dy = v.y-u.y;
      const d = dx*dx + dy*dy;
      if (d < bd){ bd = d; best = v; }
    }
    u.target = best;
  }
  counts[0] = N_SIDE; counts[1] = N_SIDE;
}

/* ==================================================================
   SPATIAL GRID
   ================================================================== */
function buildGrid(){
  for (let i = 0; i < grid.length; i++) grid[i].length = 0;
  for (let i = 0; i < units.length; i++){
    const u = units[i];
    let gx = (u.x / CELL) | 0;
    let gy = (u.y / CELL) | 0;
    if (gx < 0) gx = 0; else if (gx >= GW) gx = GW-1;
    if (gy < 0) gy = 0; else if (gy >= GH) gy = GH-1;
    u.gx = gx; u.gy = gy;
    grid[gy*GW + gx].push(u);
  }
}

function findTarget(u){
  const gx = u.gx, gy = u.gy;
  let best = null, bd = Infinity;

  for (let r = 0; r <= 10; r++){
    for (let dy = -r; dy <= r; dy++){
      const yy = gy + dy;
      if (yy < 0 || yy >= GH) continue;
      const rowBase = yy*GW;
      for (let dx = -r; dx <= r; dx++){
        const adx = dx < 0 ? -dx : dx;
        const ady = dy < 0 ? -dy : dy;
        if (adx !== r && ady !== r) continue;
        const xx = gx + dx;
        if (xx < 0 || xx >= GW) continue;
        const cell = grid[rowBase + xx];
        for (let i = 0; i < cell.length; i++){
          const v = cell[i];
          if (v.side === u.side || !v.alive) continue;
          const ddx = v.x - u.x, ddy = v.y - u.y;
          const d = ddx*ddx + ddy*ddy;
          if (d < bd){ bd = d; best = v; }
        }
      }
    }
    if (best) return best;
  }
  /* fallback: full scan */
  for (let i = 0; i < units.length; i++){
    const v = units[i];
    if (v.side === u.side || !v.alive) continue;
    const ddx = v.x - u.x, ddy = v.y - u.y;
    const d = ddx*ddx + ddy*ddy;
    if (d < bd){ bd = d; best = v; }
  }
  return best;
}

/* ==================================================================
   UNIT UPDATE
   ================================================================== */
function stepUnits(dt){
  for (let i = 0; i < units.length; i++){
    const u = units[i];
    if (!u.alive) continue;

    u.cool -= dt;
    if (u.flash > 0) u.flash -= dt*3.4;

    u.retargetT -= dt;
    let t = u.target;
    if (!t || !t.alive || u.retargetT <= 0){
      t = findTarget(u);
      u.target = t;
      u.retargetT = 0.40 + Math.random()*0.5;
    }

    let dx, dy, d;
    if (t){
      dx = t.x - u.x; dy = t.y - u.y;
      d = Math.sqrt(dx*dx + dy*dy) || 1;
      /* face the enemy */
      let a = Math.atan2(dy, dx);
      let r = Math.round(a / 6.2831853 * ROT_N) % ROT_N;
      if (r < 0) r += ROT_N;
      u.rot = r;
    } else {
      dx = u.side === 0 ? 1 : -1; dy = 0; d = 1;
    }

    let tx = 0, ty = 0;
    if (d > REACH*0.5){
      const sp = u.speed * (u.engaged ? 0.35 : 1);
      tx = dx/d*sp;
      ty = dy/d*sp;
      /* chaotic wobble */
      const w = Math.sin(time*3.4 + u.seed*7.1) * 16;
      tx += -dy/d * w * 0.35;
      ty +=  dx/d * w * 0.35;
    }

    const kk = Math.min(1, dt*7);
    u.vx += (tx - u.vx)*kk;
    u.vy += (ty - u.vy)*kk;
    u.x  += u.vx*dt;
    u.y  += u.vy*dt;

    /* keep inside the field */
    if (u.x < 8){ u.x = 8; u.vx *= -0.25; }
    else if (u.x > FIELD_W-8){ u.x = FIELD_W-8; u.vx *= -0.25; }
    if (u.y < 8){ u.y = 8; u.vy *= -0.25; }
    else if (u.y > FIELD_D-8){ u.y = FIELD_D-8; u.vy *= -0.25; }
  }
}

/* ==================================================================
   COMBAT
   ================================================================== */
function hit(u, amount){
  u.hp -= amount;
  u.flash = 1;
  if (u.hp <= 0 && u.alive) kill(u);
}

function kill(u){
  u.alive = false;
  counts[u.side]--;
  spawnBlood(u.x, u.y);
  addStain(u.x, u.y);
}

function addStain(x, y){
  if (!bgCtx) return;
  const s  = depthS(y);
  const ps = S_FAR + (S_NEAR-S_FAR)*s;
  const sx = view.cx + (x - FIELD_W*0.5)*view.k*ps;
  const sy = view.horizon + view.fieldH*s;
  const rr = (5 + Math.random()*8) * view.k * ps;
  bgCtx.globalAlpha = 0.38 + Math.random()*0.3;
  bgCtx.fillStyle = Math.random() < 0.5 ? '#3a0d0d' : '#2d1010';
  bgCtx.beginPath();
  bgCtx.ellipse(sx, sy, rr*1.6, rr*0.75, 0, 0, 6.2832);
  bgCtx.fill();
  bgCtx.globalAlpha = 1;
}

function interact(a, b, frenzy){
  const dx = b.x - a.x, dy = b.y - a.y;
  const d2 = dx*dx + dy*dy;
  if (d2 > SEP2) return;
  const d = Math.sqrt(d2) + 1e-6;
  const nx = dx/d, ny = dy/d;
  const overlap = SEP - d;

  if (a.side === b.side){
    const p = overlap * 0.10;
    a.x -= nx*p; a.y -= ny*p;
    b.x += nx*p; b.y += ny*p;
  } else {
    a.engaged = true; b.engaged = true;
    const p = overlap * 0.20;
    a.x -= nx*p; a.y -= ny*p;
    b.x += nx*p; b.y += ny*p;

    if (d < REACH && a.cool <= 0){
      a.cool = a.atkInt;
      hit(b, a.dmg * frenzy);
    }
    if (d < REACH && b.cool <= 0 && b.alive){
      b.cool = b.atkInt;
      hit(a, b.dmg * frenzy);
    }
  }
}

function stepCombat(dt){
  const frenzy = 1 + Math.max(0, time - 18) * 0.22;

  for (let i = 0; i < units.length; i++) units[i].engaged = false;

  for (let gy = 0; gy < GH; gy++){
    const rowBase = gy*GW;
    for (let gx = 0; gx < GW; gx++){
      const cell = grid[rowBase + gx];
      const n = cell.length;
      if (n === 0) continue;

      for (let i = 0; i < n; i++){
        const a = cell[i];
        if (!a.alive) continue;

        for (let j = i+1; j < n; j++){
          const b = cell[j];
          if (b.alive) interact(a, b, frenzy);
        }
        /* right neighbour */
        if (gx+1 < GW){
          const c2 = grid[rowBase + gx + 1];
          for (let j = 0; j < c2.length; j++){
            const b = c2[j];
            if (b.alive) interact(a, b, frenzy);
          }
        }
        /* down neighbour */
        if (gy+1 < GH){
          const c2 = grid[rowBase + GW + gx];
          for (let j = 0; j < c2.length; j++){
            const b = c2[j];
            if (b.alive) interact(a, b, frenzy);
          }
        }
        /* down-right */
        if (gy+1 < GH && gx+1 < GW){
          const c2 = grid[rowBase + GW + gx + 1];
          for (let j = 0; j < c2.length; j++){
            const b = c2[j];
            if (b.alive) interact(a, b, frenzy);
          }
        }
        /* down-left */
        if (gy+1 < GH && gx-1 >= 0){
          const c2 = grid[rowBase + GW + gx - 1];
          for (let j = 0; j < c2.length; j++){
            const b = c2[j];
            if (b.alive) interact(a, b, frenzy);
          }
        }
      }
    }
  }
}

function compactUnits(){
  let w = 0;
  for (let i = 0; i < units.length; i++){
    const u = units[i];
    if (u.alive) units[w++] = u;
  }
  units.length = w;
}

/* ==================================================================
   VICTORY PHASE
   ================================================================== */
function stepVictory(dt){
  const cxw = FIELD_W*0.5, cyw = FIELD_D*0.5;
  for (let i = 0; i < units.length; i++){
    const u = units[i];
    if (!u.alive) continue;

    if (u.side === winner){
      const dx = cxw - u.x, dy = cyw - u.y;
      const d = Math.sqrt(dx*dx + dy*dy) || 1;
      if (d > 140){
        u.x += dx/d * 58 * dt;
        u.y += dy/d * 58 * dt;
      }
      u.x += Math.sin(time*2.7 + u.seed*4.3) * 26 * dt;
      u.y += Math.cos(time*2.3 + u.seed*3.1) * 20 * dt;
      u.rot = u.side === 0 ? 7 : 9;
      if (Math.random() < 0.016){
        emit(u.x + (Math.random()-0.5)*18, u.y + (Math.random()-0.5)*18,
             (Math.random()-0.5)*24, -18 - Math.random()*22,
             0.7 + Math.random()*0.7, 1.6 + Math.random()*2.2,
             255, 205 + (Math.random()*40|0), 110 + (Math.random()*70|0), 0.93);
      }
    } else {
      /* survivors of the losing side flee */
      const sgn = u.x >= cxw ? 1 : -1;
      u.x += sgn * 300 * dt;
      u.y += (cyw - u.y) * 0.4 * dt;
      u.rot = sgn > 0 ? 0 : 8;
      if (u.x < -120 || u.x > FIELD_W + 120) u.alive = false;
    }
  }
  compactUnits();
}

/* ==================================================================
   PARTICLES
   ================================================================== */
function stepParticles(dt){
  for (let i = 0; i < MAX_PARTS; i++){
    const p = parts[i];
    if (p.life <= 0) continue;
    p.life -= dt;
    p.x += p.vx*dt;
    p.y += p.vy*dt;
    const dg = Math.pow(p.drag, dt*60);
    p.vx *= dg;
    p.vy *= dg;
    if (p.y < 0) p.y = 0;
    else if (p.y > FIELD_D) p.y = FIELD_D;
  }
}

/* ==================================================================
   PHASE LOGIC
   ================================================================== */
function checkPhase(){
  if (phase === 'victory'){
    if (phaseT > 5.2) resetBattle();
    return;
  }
  const a = counts[0], b = counts[1];
  const mn = Math.min(a, b), mx = Math.max(a, b);
  if (a <= 0 || b <= 0 || (mn <= 14 && mn*4 < mx)){
    winner = a > b ? 0 : 1;
    phase = 'victory';
    phaseT = 0;
    showBanner(winner);
  }
}

/* ==================================================================
   RENDER
   ================================================================== */
function render(){
  ctx.setTransform(1,0,0,1,0,0);
  ctx.drawImage(bgCanvas, 0, 0);
  ctx.setTransform(DPR,0,0,DPR,0,0);

  /* ---- build + sort render list (far units first) ---- */
  rl.length = 0;
  for (let i = 0; i < units.length; i++){
    const u = units[i];
    if (u.alive) rl.push(u);
  }
  rl.sort(function(a, b){ return a.y - b.y; });

  /* ---- particles (behind units if far, so just draw before for depth feel) ---- */
  /* draw dust/blood after units for punch */

  const WIN = (phase === 'victory');

  for (let i = 0; i < rl.length; i++){
    const u = rl[i];
    const s  = depthS(u.y);
    const ps = S_FAR + (S_NEAR - S_FAR)*s;
    const sx = view.cx + (u.x - FIELD_W*0.5)*view.k*ps;
    const sy = view.horizon + view.fieldH*s;
    const sz = SPRITE_WORLD * view.k * ps;
    if (sz < 1.5) continue;

    let bob = 0;
    if (WIN && u.side === winner){
      bob = Math.abs(Math.sin(time*6.5 + u.seed*5.7)) * 26 * view.k * ps;
    }

    const sp = sprites[u.side][u.rot];
    const px = sx - sz*0.5;
    const py = sy - sz*0.5 - bob;

    ctx.drawImage(sp.n, px, py, sz, sz);

    if (u.flash > 0.03){
      ctx.globalAlpha = Math.min(0.9, u.flash);
      ctx.drawImage(sp.w, px, py, sz, sz);
      ctx.globalAlpha = 1;
    }
  }

  /* ---- particles ---- */
  for (let i = 0; i < MAX_PARTS; i++){
    const p = parts[i];
    if (p.life <= 0) continue;
    const t  = p.life / p.maxLife;
    const s  = depthS(p.y);
    const ps = S_FAR + (S_NEAR - S_FAR)*s;
    const sx = view.cx + (p.x - FIELD_W*0.5)*view.k*ps;
    const sy = view.horizon + view.fieldH*s;
    const sz = Math.max(0.7, p.size * view.k * ps * 1.6);
    ctx.globalAlpha = t < 1 ? t : 1;
    ctx.fillStyle = 'rgb(' + p.r + ',' + p.g + ',' + p.b + ')';
    ctx.fillRect(sx - sz*0.5, sy - sz*0.5, sz, sz);
  }
  ctx.globalAlpha = 1;
}

/* ==================================================================
   HUD
   ================================================================== */
const elTitle = document.getElementById('title');
const elSub   = document.getElementById('sub');
const elRedN  = document.getElementById('redN');
const elBlueN = document.getElementById('blueN');
const elRedBar  = document.getElementById('redBar');
const elBlueBar = document.getElementById('blueBar');
const elBanner  = document.getElementById('banner');
let lastRed = -1, lastBlue = -1;

function updateHUD(){
  if (counts[0] !== lastRed){
    lastRed = counts[0];
    elRedN.textContent = lastRed;
    elRedBar.style.width = (lastRed / N_SIDE * 100).toFixed(1) + '%';
  }
  if (counts[1] !== lastBlue){
    lastBlue = counts[1];
    elBlueN.textContent = lastBlue;
    elBlueBar.style.width = (lastBlue / N_SIDE * 100).toFixed(1) + '%';
  }
}

function showBanner(side){
  elBanner.textContent = SIDES[side].name + ' STANDS VICTORIOUS';
  elBanner.style.color = side === 0 ? '#ff7a66' : '#79b6ff';
  elBanner.classList.add('show');
}
function hideBanner(){
  elBanner.classList.remove('show');
}

/* ==================================================================
   BATTLE NAMES & RESET
   ================================================================== */
const PLACES = ["Emberfield","Ashvale","Redmoor","Ironwood","Greyhollow",
                "Thornmere","Blackford","Stormgate","Duskdale","Karrowfen",
                "Bleakwater","Highmoor","Ravenmoor","Coldhollow","Stonewatch",
                "Fenmarch","Oakhollow","Wyrmrest","Gallowmere","Dreadfen",
                "Mourncrest","Saltreach","Ironfall","Witherdale"];
const PREFIX = ["The Battle of","The Fields of","The Clash at","The Siege of",
                "The Slaughter at","The Rout of","The Stand at"];

const ROMAN = ['I','II','III','IV','V','VI','VII','VIII','IX','X',
               'XI','XII','XIII','XIV','XV','XVI','XVII','XVIII','XIX','XX'];

function pickName(){
  let n = '';
  let guard = 0;
  do {
    n = PREFIX[(Math.random()*PREFIX.length)|0] + ' ' + PLACES[(Math.random()*PLACES.length)|0];
    guard++;
  } while (n === lastName && guard < 12);
  lastName = n;
  return n;
}

function resetBattle(){
  battleNo++;
  time = 0; phaseT = 0; phase = 'charge'; winner = -1;
  hideBanner();

  buildBackground();
  spawnArmies();
  buildGrid();

  elTitle.textContent = pickName();
  elSub.textContent = 'ENGAGEMENT ' + (ROMAN[battleNo % ROMAN.length]);

  lastRed = -1; lastBlue = -1;
  updateHUD();
}

/* ==================================================================
   MAIN STEP
   ================================================================== */
function step(dt){
  time += dt;
  phaseT += dt;

  if (phase === 'victory'){
    stepVictory(dt);
  } else {
    buildGrid();
    stepUnits(dt);
    stepCombat(dt);
    compactUnits();
  }

  stepParticles(dt);
  checkPhase();
}

/* ==================================================================
   RESIZE
   ================================================================== */
function resize(){
  DPR = Math.min(window.devicePixelRatio || 1, 2);
  W = Math.max(320, window.innerWidth);
  H = Math.max(240, window.innerHeight);
  cv.width  = Math.floor(W*DPR);
  cv.height = Math.floor(H*DPR);
  cv.style.width  = W + 'px';
  cv.style.height = H + 'px';
  ctx.setTransform(DPR,0,0,DPR,0,0);

  view.cx      = W*0.5;
  view.horizon = H*0.155;
  view.fieldH  = H*0.80;
  view.k       = W / (FIELD_W * S_NEAR);

  buildBackground();
}

/* ==================================================================
   BOOT / LOOP
   ================================================================== */
let lastT = 0, acc = 0;
const FIXED = 1/60;

function frame(now){
  requestAnimationFrame(frame);
  if (!lastT) lastT = now;
  let dt = (now - lastT) / 1000;
  lastT = now;
  if (dt > 0.25) dt = 0.25;

  acc += dt;
  let it = 0;
  while (acc >= FIXED && it < 4){
    step(FIXED);
    acc -= FIXED;
    it++;
  }
  if (it === 4) acc = 0;

  render();
  updateHUD();
}

/* ---- init ---- */
buildSprites();
makeTufts();
resize();
battleNo = 0;
resetBattle();
requestAnimationFrame(frame);

window.addEventListener('resize', function(){
  resize();
  buildGrid();
});

})();
</script>
</body>
</html>
```
### Battle Simulation: How It Works

The whole battle runs automatically from the moment the page loads, with a new engagement starting after each victory.

- **Army setup:** Each side begins with 500 units arranged in a 50×10 formation. They charge toward the nearest enemy, with a slight random wobble.
- **Combat loop:** A spatial grid keeps unit interactions fast. When opposing units touch, they exchange damage until one dies, leaving a blood stain and dust puff.
- **Battle flow:** The melee becomes chaotic as formations break apart. A side wins when the enemy is reduced below a threshold or fully wiped out. The winner celebrates while survivors of the losing side flee.
- **HUD & feedback:** Live survivor counts, health bars, and a title update in real time. The banner announces the victor, then the next battle resets with a new random name.
---

**Optimization Tip:** You can adjust `N_SIDE` (500) to change each army’s size, or tweak `speed`, `dmg`, and `atkInt` inside `makeUnit()` to alter pacing and lethality. `MAX_PARTS` controls the particle pool.