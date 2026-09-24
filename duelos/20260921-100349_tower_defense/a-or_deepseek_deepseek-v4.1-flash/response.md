Here's a self-contained HTML5 Canvas Tower Defense game. Enemies wind along a fixed path, and you place towers in eight slots to stop them before your base falls. It also includes an autoplay demo controlled by the P key.
```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Tower Defense</title>
<style>
  html, body {
    margin: 0; padding: 0; height: 100%;
    background: #05080c; overflow: hidden;
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  }
  #wrap {
    position: fixed; inset: 0;
    display: flex; align-items: center; justify-content: center;
  }
  canvas {
    background: #0e141c;
    border-radius: 10px;
    box-shadow: 0 0 80px rgba(40, 120, 200, 0.15), 0 0 0 1px rgba(80, 140, 200, 0.15);
    image-rendering: auto;
  }
</style>
</head>
<body>
<div id="wrap"><canvas id="c" width="960" height="600"></canvas></div>
<script>
(function () {
'use strict';

// ---------------------------------------------------------------- setup
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
const W = 960, H = 600;

function resize() {
  const s = Math.min(window.innerWidth / W, window.innerHeight / H);
  canvas.style.width = Math.floor(W * s) + 'px';
  canvas.style.height = Math.floor(H * s) + 'px';
}
window.addEventListener('resize', resize);
resize();

// ---------------------------------------------------------------- path
const PATH = [
  { x: -40, y: 130 }, { x: 150, y: 130 }, { x: 150, y: 320 }, { x: 340, y: 320 },
  { x: 340, y: 150 }, { x: 530, y: 150 }, { x: 530, y: 440 }, { x: 720, y: 440 },
  { x: 720, y: 260 }, { x: 890, y: 260 }
];

const SEGS = [];
let PATH_LEN = 0;
for (let i = 0; i < PATH.length - 1; i++) {
  const a = PATH[i], b = PATH[i + 1];
  const dx = b.x - a.x, dy = b.y - a.y, len = Math.hypot(dx, dy);
  SEGS.push({ a, dx: dx / len, dy: dy / len, len, start: PATH_LEN });
  PATH_LEN += len;
}

function posAt(d) {
  if (d <= 0) return { x: PATH[0].x, y: PATH[0].y };
  for (let i = 0; i < SEGS.length; i++) {
    const s = SEGS[i];
    if (d <= s.start + s.len) {
      const t = d - s.start;
      return { x: s.a.x + s.dx * t, y: s.a.y + s.dy * t };
    }
  }
  const l = PATH[PATH.length - 1];
  return { x: l.x, y: l.y };
}

// ---------------------------------------------------------------- slots
const SLOTS = [
  { x: 215, y: 220 }, { x: 275, y: 385 }, { x: 405, y: 235 }, { x: 465, y: 90 },
  { x: 600, y: 225 }, { x: 615, y: 510 }, { x: 790, y: 370 }, { x: 800, y: 175 }
];

// ---------------------------------------------------------------- tower types
const TOWER_TYPES = {
  cannon: { key: '1', name: 'Cannon', cost: 50,  color: '#ffb347', range: 138, damage: 16, cooldown: 0.55, speed: 430, kind: 'bullet' },
  frost:  { key: '2', name: 'Frost',  cost: 65,  color: '#6fd6ff', range: 128, damage: 6,  cooldown: 0.75, speed: 350, kind: 'frost'  },
  laser:  { key: '3', name: 'Laser',  cost: 90,  color: '#ff5c8a', range: 178, damage: 11, cooldown: 0.20, speed: 0,   kind: 'laser'  },
  splash: { key: '4', name: 'Splash', cost: 110, color: '#b07cff', range: 148, damage: 26, cooldown: 1.30, speed: 290, kind: 'splash', splashRadius: 58 }
};
const TOWER_ORDER = ['cannon', 'frost', 'laser', 'splash'];

// ---------------------------------------------------------------- enemy types
const ENEMY_TYPES = {
  grunt:  { hp: 22,  speed: 68,  reward: 8,  dmg: 1, radius: 11, color: '#5fd68a' },
  runner: { hp: 15,  speed: 116, reward: 9,  dmg: 1, radius: 9,  color: '#ffd166' },
  tank:   { hp: 62,  speed: 46,  reward: 17, dmg: 2, radius: 15, color: '#ff7b7b' },
  boss:   { hp: 300, speed: 42,  reward: 70, dmg: 6, radius: 21, color: '#c084fc' }
};

const BASE_MAX = 20;

// ---------------------------------------------------------------- state
let state = 'menu';           // menu | playing | gameover
let phase = 'wave';           // wave | between
let wave = 0;
let gold = 90;
let score = 0;
let baseHP = BASE_MAX;
let gameTime = 0;
let shake = 0;
let autoPlay = true;
let restartTimer = 0;

let towers = new Array(SLOTS.length).fill(null);
let enemies = [];
let projectiles = [];
let particles = [];
let beams = [];
let spawnQueue = [];
let spawnTimer = 0;
let spawnInterval = 1.2;
let betweenTimer = 0;

let toastMsg = '';
let toastTime = 0;

let aiTimer = 0;
const AI_ORDER = ['cannon', 'cannon', 'frost', 'laser', 'splash', 'laser', 'splash', 'laser'];

// ---------------------------------------------------------------- helpers
function makeTower(type, slot) {
  return { type, def: TOWER_TYPES[type], slot, cd: 0, angle: -Math.PI / 2, recoil: 0 };
}

function toast(msg, t) {
  toastMsg = msg;
  toastTime = t || 1.6;
}

function spawnParticles(x, y, color, n, spd, life) {
  for (let i = 0; i < n; i++) {
    const a = Math.random() * Math.PI * 2;
    const s = spd * (0.25 + Math.random() * 0.75);
    particles.push({
      x, y,
      vx: Math.cos(a) * s, vy: Math.sin(a) * s,
      life: life * (0.6 + Math.random() * 0.6), max: life,
      color, r: 1.5 + Math.random() * 2.5
    });
  }
}

function buildWave(n) {
  const list = [];
  const count = 5 + Math.floor(n * 1.7);
  for (let i = 0; i < count; i++) {
    let t = 'grunt';
    if (n >= 2 && i % 3 === 2) t = 'runner';
    if (n >= 3 && i % 5 === 4) t = 'tank';
    list.push(t);
  }
  if (n % 5 === 0) list.push('boss');
  return list;
}

// ---------------------------------------------------------------- game flow
function startGame() {
  state = 'playing';
  phase = 'wave';
  wave = 0;
  gold = 90;
  score = 0;
  baseHP = BASE_MAX;
  gameTime = 0;
  shake = 0;
  restartTimer = 0;
  enemies = [];
  projectiles = [];
  particles = [];
  beams = [];
  spawnQueue = [];
  towers = new Array(SLOTS.length).fill(null);
  towers[0] = makeTower('cannon', 0);
  aiTimer = 0.15;
  startWave(1);
}

function startWave(n) {
  wave = n;
  spawnInterval = Math.max(0.5, 1.3 - n * 0.055);
  spawnQueue = buildWave(n);
  spawnTimer = 0.35;
  phase = 'wave';
  toast('WAVE ' + n, 1.4);
}

function gameOver() {
  state = 'gameover';
  restartTimer = 3.5;
  shake = 22;
  spawnParticles(912, 260, '#ff5566', 44, 320, 1.1);
  spawnParticles(912, 260, '#ffaa55', 24, 220, 0.9);
}

// ---------------------------------------------------------------- enemies
function spawnEnemy(type) {
  const def = ENEMY_TYPES[type];
  const scale = Math.pow(1.15, wave - 1);
  const hp = Math.round(def.hp * scale);
  enemies.push({
    type,
    hp, maxHp: hp,
    d: 0,
    speed: def.speed,
    reward: def.reward,
    dmg: def.dmg,
    radius: def.radius,
    color: def.color,
    slow: 0,
    slowFactor: 1,
    x: PATH[0].x, y: PATH[0].y,
    dead: false,
    hitFlash: 0
  });
}

function damageEnemy(e, dmg) {
  if (e.dead) return;
  e.hp -= dmg;
  e.hitFlash = 0.1;
  if (e.hp <= 0) {
    e.dead = true;
    gold += e.reward;
    score += e.reward * 2;
    spawnParticles(e.x, e.y, e.color, 12, 170, 0.5);
  }
}

// ---------------------------------------------------------------- towers
function buyAt(type, idx) {
  const def = TOWER_TYPES[type];
  if (gold < def.cost) return false;
  gold -= def.cost;
  towers[idx] = makeTower(type, idx);
  spawnParticles(SLOTS[idx].x, SLOTS[idx].y, def.color, 14, 150, 0.5);
  return true;
}

function buy(type) {
  if (state !== 'playing') return;
  const idx = towers.findIndex(t => !t);
  if (idx < 0) { toast('NO FREE SLOTS', 1.1); return; }
  const def = TOWER_TYPES[type];
  if (gold < def.cost) { toast('NOT ENOUGH GOLD', 1.1); return; }
  buyAt(type, idx);
}

function fire(t, target) {
  const p = SLOTS[t.slot];
  const def = t.def;
  const ang = Math.atan2(target.y - p.y, target.x - p.x);
  const mx = p.x + Math.cos(ang) * 20;
  const my = p.y + Math.sin(ang) * 20;

  if (def.kind === 'laser') {
    damageEnemy(target, def.damage);
    beams.push({ x1: mx, y1: my, x2: target.x, y2: target.y, life: 0.08, max: 0.08, color: def.color });
    spawnParticles(target.x, target.y, def.color, 2, 70, 0.2);
    return;
  }

  projectiles.push({
    x: mx, y: my,
    tx: target.x, ty: target.y,
    target,
    speed: def.speed,
    damage: def.damage,
    kind: def.kind,
    color: def.color,
    splashRadius: def.splashRadius || 0,
    dead: false
  });
  spawnParticles(mx, my, def.color, 3, 90, 0.16);
}

function impact(pr) {
  if (pr.kind === 'splash') {
    for (let i = 0; i < enemies.length; i++) {
      const e = enemies[i];
      if (e.dead) continue;
      const d = Math.hypot(e.x - pr.x, e.y - pr.y);
      if (d <= pr.splashRadius) damageEnemy(e, pr.damage);
    }
    spawnParticles(pr.x, pr.y, pr.color, 16, 210, 0.45);
  } else {
    if (pr.target && !pr.target.dead) {
      damageEnemy(pr.target, pr.damage);
      if (pr.kind === 'frost') {
        pr.target.slow = 1.8;
        pr.target.slowFactor = 0.45;
      }
    }
    spawnParticles(pr.x, pr.y, pr.color, 5, 130, 0.3);
  }
}

// ---------------------------------------------------------------- AI
function aiUpdate(dt) {
  aiTimer -= dt;
  if (aiTimer > 0) return;
  aiTimer = 0.22;

  let count = 0;
  for (let i = 0; i < towers.length; i++) if (towers[i]) count++;

  const freeIdx = towers.findIndex(t => !t);
  if (freeIdx >= 0) {
    const want = AI_ORDER[Math.min(count, AI_ORDER.length - 1)];
    const cost = TOWER_TYPES[want].cost;
    if (gold >= cost) buyAt(want, freeIdx);
  }

  if (phase === 'between' && betweenTimer < 2.0) {
    startWave(wave + 1);
  }
}

// ---------------------------------------------------------------- update
function update(dt) {
  gameTime += dt;
  if (shake > 0) shake = Math.max(0, shake - dt * 60);
  if (toastTime > 0) toastTime -= dt;

  // particles
  for (let i = 0; i < particles.length; i++) {
    const p = particles[i];
    p.x += p.vx * dt;
    p.y += p.vy * dt;
    p.vx *= 0.94;
    p.vy *= 0.94;
    p.life -= dt;
  }
  particles = particles.filter(p => p.life > 0);

  // beams
  for (let i = 0; i < beams.length; i++) beams[i].life -= dt;
  beams = beams.filter(b => b.life > 0);

  if (state === 'menu' && autoPlay) startGame();

  if (state === 'playing') {
    if (autoPlay) aiUpdate(dt);

    // spawning
    if (spawnQueue.length > 0) {
      spawnTimer -= dt;
      while (spawnQueue.length > 0 && spawnTimer <= 0) {
        spawnEnemy(spawnQueue.shift());
        spawnTimer += spawnInterval;
      }
    }

    // enemies
    for (let i = 0; i < enemies.length; i++) {
      const e = enemies[i];
      if (e.dead) continue;
      if (e.slow > 0) e.slow -= dt;
      if (e.hitFlash > 0) e.hitFlash -= dt;

      const mult = e.slow > 0 ? e.slowFactor : 1;
      e.d += e.speed * mult * dt;

      if (e.d >= PATH_LEN) {
        e.dead = true;
        baseHP -= e.dmg;
        shake = Math.max(shake, 7);
        spawnParticles(e.x, e.y, '#ff5566', 14, 190, 0.55);
        if (baseHP <= 0) { baseHP = 0; gameOver(); }
      } else {
        const p = posAt(e.d);
        e.x = p.x; e.y = p.y;
      }
    }
    enemies = enemies.filter(e => !e.dead);

    // towers
    for (let i = 0; i < towers.length; i++) {
      const t = towers[i];
      if (!t) continue;
      t.cd -= dt;
      if (t.recoil > 0) t.recoil = Math.max(0, t.recoil - dt * 5);

      const tp = SLOTS[t.slot];
      let best = null, bestD = -1;
      for (let j = 0; j < enemies.length; j++) {
        const e = enemies[j];
        if (e.dead) continue;
        const dx = e.x - tp.x, dy = e.y - tp.y;
        if (dx * dx + dy * dy <= t.def.range * t.def.range) {
          if (e.d > bestD) { bestD = e.d; best = e; }
        }
      }
      if (best) {
        t.angle = Math.atan2(best.y - tp.y, best.x - tp.x);
        if (t.cd <= 0) {
          fire(t, best);
          t.cd = t.def.cooldown;
          t.recoil = 1;
        }
      }
    }

    // projectiles
    for (let i = 0; i < projectiles.length; i++) {
      const pr = projectiles[i];
      if (pr.target && !pr.target.dead) {
        pr.tx = pr.target.x;
        pr.ty = pr.target.y;
      }
      const dx = pr.tx - pr.x, dy = pr.ty - pr.y;
      const dist = Math.hypot(dx, dy);
      const step = pr.speed * dt;
      if (dist <= step + 7 || dist < 0.001) {
        impact(pr);
        pr.dead = true;
      } else {
        pr.x += (dx / dist) * step;
        pr.y += (dy / dist) * step;
      }
    }
    projectiles = projectiles.filter(p => !p.dead);

    // wave progression
    if (phase === 'between') {
      betweenTimer -= dt;
      if (betweenTimer <= 0) startWave(wave + 1);
    } else {
      if (spawnQueue.length === 0 && enemies.length === 0 && state === 'playing') {
        const bonus = 20 + wave * 6;
        gold += bonus;
        score += 50 + wave * 10;
        phase = 'between';
        betweenTimer = 4;
        toast('WAVE ' + wave + ' CLEARED   +' + bonus + 'g', 2.0);
      }
    }
  }

  if (state === 'gameover') {
    restartTimer -= dt;
    if (autoPlay && restartTimer <= 0) startGame();
  }
}

// ---------------------------------------------------------------- drawing: world
function drawPath() {
  ctx.lineJoin = 'round';
  ctx.lineCap = 'round';
  ctx.beginPath();
  ctx.moveTo(PATH[0].x, PATH[0].y);
  for (let i = 1; i < PATH.length; i++) ctx.lineTo(PATH[i].x, PATH[i].y);

  ctx.strokeStyle = 'rgba(60,120,180,0.14)';
  ctx.lineWidth = 48;
  ctx.stroke();

  ctx.strokeStyle = '#1a2532';
  ctx.lineWidth = 36;
  ctx.stroke();

  ctx.strokeStyle = '#233447';
  ctx.lineWidth = 27;
  ctx.stroke();

  ctx.save();
  ctx.setLineDash([12, 16]);
  ctx.lineDashOffset = -gameTime * 34;
  ctx.strokeStyle = 'rgba(120,180,240,0.28)';
  ctx.lineWidth = 3;
  ctx.stroke();
  ctx.restore();
}

function drawBase() {
  const bx = 912, by = 260;

  const g = ctx.createRadialGradient(bx, by, 8, bx, by, 100);
  g.addColorStop(0, 'rgba(90,200,255,0.22)');
  g.addColorStop(1, 'rgba(90,200,255,0)');
  ctx.fillStyle = g;
  ctx.beginPath(); ctx.arc(bx, by, 100, 0, Math.PI * 2); ctx.fill();

  ctx.fillStyle = '#182736';
  ctx.strokeStyle = '#3f6d94';
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(bx - 34, by - 48);
  ctx.lineTo(bx + 34, by - 48);
  ctx.lineTo(bx + 34, by + 48);
  ctx.lineTo(bx - 34, by + 48);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  ctx.strokeStyle = 'rgba(120,190,250,0.25)';
  ctx.lineWidth = 1;
  for (let i = -30; i <= 30; i += 15) {
    ctx.beginPath();
    ctx.moveTo(bx + i, by - 44);
    ctx.lineTo(bx + i, by + 44);
    ctx.stroke();
  }

  const pulse = 0.55 + 0.45 * Math.sin(gameTime * 4);
  ctx.save();
  ctx.shadowColor = '#5ac8ff';
  ctx.shadowBlur = 22 * pulse + 6;
  ctx.fillStyle = 'rgba(120,220,255,' + (0.55 + 0.45 * pulse) + ')';
  ctx.beginPath(); ctx.arc(bx, by, 14, 0, Math.PI * 2); ctx.fill();
  ctx.restore();

  ctx.fillStyle = 'rgba(255,255,255,0.75)';
  ctx.beginPath(); ctx.arc(bx - 4, by - 4, 4, 0, Math.PI * 2); ctx.fill();

  // small hp bar under base
  const w = 78, h = 7, hx = bx - w / 2, hy = by + 58;
  const frac = Math.max(0, baseHP / BASE_MAX);
  ctx.fillStyle = 'rgba(0,0,0,0.55)';
  ctx.fillRect(hx, hy, w, h);
  ctx.fillStyle = frac > 0.5 ? '#4ade80' : frac > 0.25 ? '#fbbf24' : '#f87171';
  ctx.fillRect(hx, hy, w * frac, h);
  ctx.strokeStyle = 'rgba(255,255,255,0.18)';
  ctx.lineWidth = 1;
  ctx.strokeRect(hx + 0.5, hy + 0.5, w - 1, h - 1);
}

function drawSlot(i) {
  const p = SLOTS[i];
  ctx.save();
  ctx.setLineDash([6, 6]);
  ctx.lineDashOffset = -gameTime * 14;
  ctx.beginPath();
  ctx.arc(p.x, p.y, 22, 0, Math.PI * 2);
  ctx.strokeStyle = 'rgba(110,165,215,0.32)';
  ctx.lineWidth = 2;
  ctx.stroke();
  ctx.restore();

  ctx.strokeStyle = 'rgba(110,165,215,0.22)';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(p.x - 7, p.y); ctx.lineTo(p.x + 7, p.y);
  ctx.moveTo(p.x, p.y - 7); ctx.lineTo(p.x, p.y + 7);
  ctx.stroke();
}

function drawTower(t) {
  const p = SLOTS[t.slot];
  const def = t.def;

  ctx.beginPath();
  ctx.arc(p.x, p.y, 22, 0, Math.PI * 2);
  ctx.fillStyle = '#152029';
  ctx.fill();
  ctx.lineWidth = 3;
  ctx.strokeStyle = 'rgba(70,115,155,0.75)';
  ctx.stroke();

  ctx.beginPath();
  ctx.arc(p.x, p.y, 16, 0, Math.PI * 2);
  ctx.strokeStyle = 'rgba(255,255,255,0.06)';
  ctx.lineWidth = 1;
  ctx.stroke();

  ctx.save();
  ctx.translate(p.x, p.y);
  ctx.rotate(t.angle);
  ctx.translate(-t.recoil * 4, 0);

  if (t.type === 'cannon') {
    ctx.fillStyle = '#3a4a5a';
    ctx.fillRect(-6, -5, 24, 10);
    ctx.fillStyle = '#5a6d80';
    ctx.fillRect(-6, -5, 24, 4);
    ctx.fillStyle = def.color;
    ctx.fillRect(16, -6, 8, 12);
  } else if (t.type === 'frost') {
    ctx.fillStyle = '#2d4a5c';
    ctx.fillRect(-6, -6, 22, 12);
    ctx.fillStyle = def.color;
    ctx.beginPath(); ctx.arc(17, 0, 7, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = '#e6fbff';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(17, -5); ctx.lineTo(17, 5);
    ctx.moveTo(13, -2.5); ctx.lineTo(21, 2.5);
    ctx.moveTo(21, -2.5); ctx.lineTo(13, 2.5);
    ctx.stroke();
  } else if (t.type === 'laser') {
    ctx.fillStyle = '#3a2a3a';
    ctx.fillRect(-6, -4, 28, 8);
    ctx.fillStyle = def.color;
    ctx.fillRect(22, -5, 6, 10);
    ctx.save();
    ctx.shadowColor = def.color;
    ctx.shadowBlur = 12;
    ctx.fillRect(26, -3, 5, 6);
    ctx.restore();
  } else if (t.type === 'splash') {
    ctx.fillStyle = '#3b2f52';
    ctx.fillRect(-8, -9, 24, 18);
    ctx.fillStyle = def.color;
    ctx.beginPath(); ctx.arc(18, 0, 9, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#1a1226';
    ctx.beginPath(); ctx.arc(18, 0, 5, 0, Math.PI * 2); ctx.fill();
  }
  ctx.restore();

  ctx.beginPath();
  ctx.arc(p.x, p.y, 9, 0, Math.PI * 2);
  ctx.fillStyle = def.color;
  ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,0.4)';
  ctx.beginPath();
  ctx.arc(p.x - 3, p.y - 3, 3.4, 0, Math.PI * 2);
  ctx.fill();
}

function drawEnemies() {
  for (let i = 0; i < enemies.length; i++) {
    const e = enemies[i];

    ctx.beginPath();
    ctx.arc(e.x, e.y + 3, e.radius, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(0,0,0,0.35)';
    ctx.fill();

    ctx.beginPath();
    ctx.arc(e.x, e.y, e.radius, 0, Math.PI * 2);
    ctx.fillStyle = e.hitFlash > 0 ? '#ffffff' : e.color;
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = 'rgba(0,0,0,0.45)';
    ctx.stroke();

    if (e.type === 'boss') {
      ctx.strokeStyle = 'rgba(255,255,255,0.55)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(e.x, e.y, e.radius + 4, 0, Math.PI * 2);
      ctx.stroke();
    }

    if (e.slow > 0) {
      ctx.beginPath();
      ctx.arc(e.x, e.y, e.radius + 3.5, 0, Math.PI * 2);
      ctx.strokeStyle = 'rgba(140,230,255,0.9)';
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    const w = e.radius * 2.3, h = 4;
    const hx = e.x - w / 2, hy = e.y - e.radius - 12;
    const frac = Math.max(0, e.hp / e.maxHp);
    ctx.fillStyle = 'rgba(0,0,0,0.62)';
    ctx.fillRect(hx, hy, w, h);
    ctx.fillStyle = frac > 0.5 ? '#4ade80' : frac > 0.25 ? '#fbbf24' : '#f87171';
    ctx.fillRect(hx, hy, w * frac, h);
  }
}

function drawProjectiles() {
  for (let i = 0; i < projectiles.length; i++) {
    const pr = projectiles[i];
    ctx.save();
    ctx.shadowColor = pr.color;
    ctx.shadowBlur = 12;
    ctx.fillStyle = pr.color;
    ctx.beginPath();
    ctx.arc(pr.x, pr.y, pr.kind === 'splash' ? 5.5 : 3.6, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }
}

function drawBeams() {
  for (let i = 0; i < beams.length; i++) {
    const b = beams[i];
    const a = Math.max(0, b.life / b.max);
    ctx.save();
    ctx.globalAlpha = a;
    ctx.strokeStyle = b.color;
    ctx.lineWidth = 4;
    ctx.shadowColor = b.color;
    ctx.shadowBlur = 16;
    ctx.beginPath();
    ctx.moveTo(b.x1, b.y1);
    ctx.lineTo(b.x2, b.y2);
    ctx.stroke();
    ctx.restore();
  }
}

function drawParticles() {
  for (let i = 0; i < particles.length; i++) {
    const p = particles[i];
    const a = Math.max(0, p.life / p.max);
    ctx.globalAlpha = a;
    ctx.fillStyle = p.color;
    ctx.beginPath();
    ctx.arc(p.x, p.y, Math.max(0.4, p.r * a), 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.globalAlpha = 1;
}

// ---------------------------------------------------------------- drawing: HUD
function drawHUD() {
  // top bar
  ctx.fillStyle = 'rgba(8,13,20,0.94)';
  ctx.fillRect(0, 0, W, 50);
  ctx.strokeStyle = 'rgba(90,150,210,0.3)';
  ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(0, 50); ctx.lineTo(W, 50); ctx.stroke();

  ctx.textBaseline = 'middle';

  // gold
  ctx.beginPath();
  ctx.arc(28, 25, 9, 0, Math.PI * 2);
  ctx.fillStyle = '#ffd166';
  ctx.fill();
  ctx.fillStyle = '#0e141c';
  ctx.font = 'bold 12px system-ui, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('$', 28, 26);
  ctx.textAlign = 'left';
  ctx.font = 'bold 21px system-ui, sans-serif';
  ctx.fillStyle = '#f2f6fb';
  ctx.fillText(String(gold), 46, 26);

  // wave
  ctx.font = 'bold 12px system-ui, sans-serif';
  ctx.fillStyle = '#6b8fb5';
  ctx.fillText('WAVE', 168, 16);
  ctx.font = 'bold 21px system-ui, sans-serif';
  ctx.fillStyle = '#8ab4f8';
  ctx.fillText(String(wave), 168, 35);

  // base hp
  ctx.font = 'bold 12px system-ui, sans-serif';
  ctx.fillStyle = '#6b8fb5';
  ctx.fillText('BASE HP', 250, 16);
  const bw = 210, bh = 17, bx = 250, by = 25;
  const frac = Math.max(0, baseHP / BASE_MAX);
  ctx.fillStyle = 'rgba(255,255,255,0.09)';
  ctx.fillRect(bx, by, bw, bh);
  ctx.fillStyle = frac > 0.5 ? '#4ade80' : frac > 0.25 ? '#fbbf24' : '#f87171';
  ctx.fillRect(bx, by, bw * frac, bh);
  ctx.strokeStyle = 'rgba(255,255,255,0.2)';
  ctx.lineWidth = 1;
  ctx.strokeRect(bx + 0.5, by + 0.5, bw - 1, bh - 1);
  ctx.fillStyle = '#e8eef5';
  ctx.font = 'bold 12px system-ui, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(baseHP + ' / ' + BASE_MAX, bx + bw / 2, by + bh / 2 + 1);
  ctx.textAlign = 'left';

  // score
  ctx.font = 'bold 12px system-ui, sans-serif';
  ctx.fillStyle = '#6b8fb5';
  ctx.fillText('SCORE', 505, 16);
  ctx.font = 'bold 21px system-ui, sans-serif';
  ctx.fillStyle = '#f2f6fb';
  ctx.fillText(String(score), 505, 35);

  // autoplay badge
  const badgeOn = autoPlay;
  const bxr = 760, byr = 12, bwr = 178, bhr = 26;
  ctx.fillStyle = badgeOn ? 'rgba(80,200,140,0.16)' : 'rgba(255,255,255,0.06)';
  ctx.fillRect(bxr, byr, bwr, bhr);
  ctx.strokeStyle = badgeOn ? 'rgba(90,220,150,0.7)' : 'rgba(255,255,255,0.15)';
  ctx.lineWidth = 1.5;
  ctx.strokeRect(bxr + 0.5, byr + 0.5, bwr - 1, bhr - 1);
  ctx.fillStyle = badgeOn ? '#7ff0b0' : 'rgba(220,230,240,0.5)';
  ctx.font = 'bold 12px system-ui, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(badgeOn ? 'P: AUTOPLAY DEMO' : 'P: MANUAL PLAY', bxr + bwr / 2, byr + bhr / 2 + 1);
  ctx.textAlign = 'left';

  // bottom shop bar
  ctx.fillStyle = 'rgba(8,13,20,0.94)';
  ctx.fillRect(0, 548, W, 52);
  ctx.strokeStyle = 'rgba(90,150,210,0.3)';
  ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(0, 548); ctx.lineTo(W, 548); ctx.stroke();

  const bwidth = 190, bheight = 38, gap = 16;
  const totalW = TOWER_ORDER.length * bwidth + (TOWER_ORDER.length - 1) * gap;
  let x = (W - totalW) / 2;
  const y = 555;

  for (let i = 0; i < TOWER_ORDER.length; i++) {
    const type = TOWER_ORDER[i];
    const def = TOWER_TYPES[type];
    const affordable = gold >= def.cost;

    ctx.fillStyle = affordable ? 'rgba(30,45,62,0.95)' : 'rgba(20,26,34,0.85)';
    ctx.fillRect(x, y, bwidth, bheight);
    ctx.strokeStyle = affordable ? def.color : 'rgba(255,255,255,0.12)';
    ctx.lineWidth = 2;
    ctx.strokeRect(x + 1, y + 1, bwidth - 2, bheight - 2);

    ctx.globalAlpha = affordable ? 1 : 0.35;
    ctx.beginPath();
    ctx.arc(x + 22, y + bheight / 2, 8, 0, Math.PI * 2);
    ctx.fillStyle = def.color;
    ctx.fill();
    ctx.globalAlpha = 1;

    ctx.textBaseline = 'middle';
    ctx.textAlign = 'left';
    ctx.font = 'bold 15px system-ui, sans-serif';
    ctx.fillStyle = affordable ? '#e8eef5' : 'rgba(230,238,245,0.4)';
    ctx.fillText('[' + def.key + '] ' + def.name, x + 40, y + bheight / 2 + 1);

    ctx.textAlign = 'right';
    ctx.fillStyle = affordable ? '#ffd166' : 'rgba(255,209,102,0.35)';
    ctx.fillText(def.cost + 'g', x + bwidth - 14, y + bheight / 2 + 1);

    x += bwidth + gap;
  }
}

function drawOverlays() {
  // toast
  if (toastTime > 0 && toastMsg) {
    ctx.save();
    ctx.globalAlpha = Math.min(1, toastTime * 2.2);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.font = 'bold 26px system-ui, sans-serif';
    ctx.fillStyle = 'rgba(0,0,0,0.5)';
    ctx.fillText(toastMsg, W / 2 + 2, 92);
    ctx.fillStyle = '#ffd166';
    ctx.fillText(toastMsg, W / 2, 90);
    ctx.restore();
  }

  if (state === 'menu') {
    ctx.fillStyle = 'rgba(5,9,14,0.84)';
    ctx.fillRect(0, 0, W, H);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    ctx.fillStyle = '#8ab4f8';
    ctx.font = 'bold 56px system-ui, sans-serif';
    ctx.fillText('TOWER DEFENSE', W / 2, 190);

    ctx.fillStyle = '#c9d6e4';
    ctx.font = '18px system-ui, sans-serif';
    ctx.fillText('Enemies march in from the left. Stop them before they reach your base.', W / 2, 258);
    ctx.fillText('Press 1-4 to buy a tower into the next free slot.', W / 2, 290);
    ctx.fillText('Space starts / restarts the game.   P toggles the autoplay demo.', W / 2, 322);

    ctx.fillStyle = '#6b8fb5';
    ctx.font = 'bold 20px system-ui, sans-serif';
    ctx.fillText('PRESS SPACE TO START', W / 2, 410);

    ctx.fillStyle = 'rgba(140,180,220,0.6)';
    ctx.font = '15px system-ui, sans-serif';
    ctx.fillText('Cannon · Frost · Laser · Splash', W / 2, 470);
  }

  if (state === 'gameover') {
    ctx.fillStyle = 'rgba(40,6,12,0.74)';
    ctx.fillRect(0, 0, W, H);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    ctx.fillStyle = '#ff6b7f';
    ctx.font = 'bold 58px system-ui, sans-serif';
    ctx.fillText('BASE DESTROYED', W / 2, 200);

    ctx.fillStyle = '#e8eef5';
    ctx.font = 'bold 26px system-ui, sans-serif';
    ctx.fillText('Reached wave ' + wave, W / 2, 285);
    ctx.fillText('Score: ' + score, W / 2, 325);

    ctx.fillStyle = '#ffd166';
    ctx.font = 'bold 22px system-ui, sans-serif';
    ctx.fillText('PRESS SPACE TO PLAY AGAIN', W / 2, 420);

    if (autoPlay) {
      ctx.fillStyle = 'rgba(200,220,240,0.55)';
      ctx.font = '16px system-ui, sans-serif';
      ctx.fillText('Autoplay demo restarting...', W / 2, 465);
    }
  }
}

// ---------------------------------------------------------------- render
function render() {
  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = '#0e141c';
  ctx.fillRect(0, 0, W, H);

  // subtle grid
  ctx.strokeStyle = 'rgba(80,140,200,0.045)';
  ctx.lineWidth = 1;
  for (let x = 0; x < W; x += 40) {
    ctx.beginPath(); ctx.moveTo(x + 0.5, 0); ctx.lineTo(x + 0.5, H); ctx.stroke();
  }
  for (let y = 0; y < H; y += 40) {
    ctx.beginPath(); ctx.moveTo(0, y + 0.5); ctx.lineTo(W, y + 0.5); ctx.stroke();
  }

  ctx.save();
  if (shake > 0.2) {
    ctx.translate((Math.random() - 0.5) * shake, (Math.random() - 0.5) * shake);
  }

  drawPath();
  drawBase();

  for (let i = 0; i < SLOTS.length; i++) {
    if (!towers[i]) drawSlot(i);
  }
  for (let i = 0; i < towers.length; i++) {
    if (towers[i]) drawTower(towers[i]);
  }

  drawEnemies();
  drawProjectiles();
  drawBeams();
  drawParticles();

  ctx.restore();

  drawHUD();
  drawOverlays();
}

// ---------------------------------------------------------------- input
window.addEventListener('keydown', function (e) {
  const k = e.key;

  if (k === ' ' || k === 'Spacebar') {
    e.preventDefault();
    if (state === 'menu') {
      startGame();
    } else if (state === 'gameover') {
      startGame();
    } else if (state === 'playing' && phase === 'between') {
      startWave(wave + 1);
    }
    return;
  }

  if (k === 'p' || k === 'P') {
    autoPlay = !autoPlay;
    if (autoPlay && state === 'gameover') restartTimer = 0.5;
    if (!autoPlay && state === 'menu') { /* stay in menu */ }
    return;
  }

  if (state === 'playing') {
    if (k === '1') buy('cannon');
    else if (k === '2') buy('frost');
    else if (k === '3') buy('laser');
    else if (k === '4') buy('splash');
  }
});

// ---------------------------------------------------------------- main loop
let last = performance.now();
function loop(now) {
  let dt = (now - last) / 1000;
  last = now;
  if (dt > 0.05) dt = 0.05;
  if (dt < 0) dt = 0;
  update(dt);
  render();
  requestAnimationFrame(loop);
}

requestAnimationFrame(loop);

})();
</script>
</body>
</html>
```
### Gameplay, Controls & Autoplay Demo

The game uses a fixed winding path and eight tower slots. Each tower type has distinct cost, range, damage, and cooldown, so you'll need to balance purchases against wave strength.

- **Buying towers:** Press 1-4 for cannon, frost, laser, or splash. Towers fill the next empty slot from left to right; if you have enough gold, the purchase happens instantly. One free cannon is placed in the first slot at the start.
- **Waves and gold:** Enemies spawn from the left, follow the path, and award gold when killed. Clearing a wave gives a bonus. Waves scale up in HP and count, with a boss every fifth wave.
- **Base and scoring:** Your base has 20 HP. Each enemy that reaches it deals damage. The game ends when HP hits zero, and your score is shown along with gold, wave, and base HP in the top bar.
- **Autoplay demo:** Press P to toggle AI control. The AI buys a preset sequence of towers, starts waves automatically, and keeps the run going. When you're watching, it will restart after a game over.
- **Restarting:** Press Space to start, restart, or begin the next wave early during the between-wave pause.
---

**Optimization Tip:** You can adjust the starting gold, base HP, or wave difficulty by changing the `gold = 90`, `BASE_MAX = 20`, and `buildWave` function values near the top of the script. The `AI_ORDER` array controls which towers the autoplay demo buys.