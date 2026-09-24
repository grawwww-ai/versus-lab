```html
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Breakout</title>
<style>
  html, body {
    margin: 0;
    padding: 0;
    background: #0b0b12;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: monospace;
    overflow: hidden;
  }
  #wrap {
    position: relative;
  }
  canvas {
    background: #0b0b12;
    border: 2px solid #333;
    box-shadow: 0 0 40px rgba(80,120,255,0.15);
    display: block;
  }
  #hud {
    position: absolute;
    top: 8px;
    left: 0;
    width: 100%;
    display: flex;
    justify-content: space-between;
    padding: 0 16px;
    box-sizing: border-box;
    color: #cfd8ff;
    font-size: 16px;
    pointer-events: none;
    letter-spacing: 1px;
    text-shadow: 0 0 8px rgba(120,150,255,.6);
  }
  #msg {
    position: absolute;
    top: 42%;
    width: 100%;
    text-align: center;
    color: #ffffff;
    font-size: 34px;
    letter-spacing: 4px;
    pointer-events: none;
    text-shadow: 0 0 16px rgba(120,150,255,.9);
    opacity: 0;
    transition: opacity .2s;
  }
  #aiBadge {
    position: absolute;
    top: 36px;
    right: 16px;
    color: #6f6;
    font-size: 13px;
    letter-spacing: 2px;
    opacity: .9;
    pointer-events: none;
    text-shadow: 0 0 8px rgba(80,255,120,.7);
  }
</style>
</head>
<body>
<div id="wrap">
  <canvas id="c" width="800" height="600"></canvas>
  <div id="hud">
    <span id="score">SCORE 0</span>
    <span id="lives">LIVES &hearts;&hearts;&hearts;</span>
  </div>
  <div id="aiBadge"></div>
  <div id="msg"></div>
</div>
<script>
(function(){
"use strict";

const cv = document.getElementById('c');
const ctx = cv.getContext('2d');
const W = cv.width, H = cv.height;

const scoreEl = document.getElementById('score');
const livesEl = document.getElementById('lives');
const msgEl   = document.getElementById('msg');
const aiBadge = document.getElementById('aiBadge');

// ---- config ----
const COLS = 10, ROWS = 5;
const BLOCK_W = 68, BLOCK_H = 22, BLOCK_PAD = 6;
const BLOCK_TOP = 70, BLOCK_LEFT = 14;
const PADDLE_W = 100, PADDLE_H = 14, PADDLE_Y = H - 40;
const PADDLE_SPEED = 7;
const BALL_R = 8;
const BASE_SPEED = 5;
const SPEED_GAIN = 0.12;
const MAX_SPEED = 11;

const ROW_COLORS = ['#ff5d5d','#ffb454','#ffe45e','#63e07a','#5ab8ff'];

// ---- state ----
let paddle, ball, blocks, score, lives;
let state;               // 'ready' | 'playing' | 'over' | 'won'
let msgTimer = 0;
let autoStartTimer = 0;  // seconds until auto-launch (autoplay / first start)
let autoplay = false;
let lastTime = 0;
let keyL = false, keyR = false;
let shake = 0;

// ---- input ----
addEventListener('keydown', function(e){
  if (e.code === 'ArrowLeft')  keyL = true;
  if (e.code === 'ArrowRight') keyR = true;
  if (e.code === 'KeyP') {
    autoplay = !autoplay;
    aiBadge.textContent = autoplay ? 'AUTOPLAY: ON' : '';
    if (autoplay && (state === 'ready' || state === 'over' || state === 'won')) {
      // nudge so AI can act promptly
      if (state === 'ready') autoStartTimer = Math.min(autoStartTimer, 0.3);
      else endGameTimer = Math.min(endGameTimer, 0.8);
    }
  }
  if (e.code === 'Space') {
    if (!autoplay) {
      if (state === 'ready') launch();
      else if (state === 'over' || state === 'won') resetGame();
    }
  }
  if (e.code.startsWith('Arrow') || e.code === 'Space') e.preventDefault();
});
addEventListener('keyup', function(e){
  if (e.code === 'ArrowLeft')  keyL = false;
  if (e.code === 'ArrowRight') keyR = false;
});

// ---- setup ----
let endGameTimer = -1; // seconds until auto-restart after game end

function makeBlocks(){
  const b = [];
  for (let r = 0; r < ROWS; r++){
    for (let c = 0; c < COLS; c++){
      b.push({
        x: BLOCK_LEFT + c*(BLOCK_W+BLOCK_PAD),
        y: BLOCK_TOP + r*(BLOCK_H+BLOCK_PAD),
        w: BLOCK_W, h: BLOCK_H,
        alive: true,
        color: ROW_COLORS[r]
      });
    }
  }
  return b;
}

function resetBall(){
  ball = {
    x: paddle.x + PADDLE_W/2,
    y: PADDLE_Y - BALL_R - 1,
    vx: (Math.random()<0.5?-1:1) * BASE_SPEED * 0.55,
    vy: -BASE_SPEED * 0.85,
    speed: BASE_SPEED
  };
}

function resetGame(){
  paddle = { x: W/2 - PADDLE_W/2 };
  blocks = makeBlocks();
  score = 0;
  lives = 3;
  state = 'ready';
  endGameTimer = -1;
  msgEl.textContent = '';
  msgEl.style.opacity = 0;
  if (autoplay) autoStartTimer = 0.4;
  else autoStartTimer = 1.0; // auto-start (still press Space to launch manually early)
  resetBall();
  updateHUD();
}

function launch(){
  if (state !== 'ready') return;
  // slight random upward angle
  const a = (-Math.PI/2) + (Math.random()*0.6 - 0.3);
  ball.vx = Math.cos(a) * ball.speed;
  ball.vy = Math.sin(a) * ball.speed;
  state = 'playing';
}

function loseLife(){
  lives--;
  shake = 8;
  if (lives <= 0){
    showEnd('GAME OVER');
  } else {
    state = 'ready';
    autoStartTimer = autoplay ? 0.6 : 9999; // wait for Space unless autoplay
    paddle.x = W/2 - PADDLE_W/2;
    resetBall();
    flash('BALL LOST');
  }
  updateHUD();
}

function allClear(){
  if (!blocks.some(b => b.alive)) showEnd('ALL CLEAR!');
}

function showEnd(text){
  state = (text === 'ALL CLEAR!') ? 'won' : 'over';
  endGameTimer = 1.6;
  flash(text, 1.6);
}

function flash(text, dur){
  msgEl.textContent = text;
  msgEl.style.opacity = 1;
  msgTimer = dur !== undefined ? dur : 0.8;
}

function updateHUD(){
  scoreEl.textContent = 'SCORE ' + score;
  livesEl.innerHTML = 'LIVES ' + (lives > 0 ? '&hearts;'.repeat(lives) : '—');
}

// ---- ball/block collision ----
function collideBlocks(){
  for (const b of blocks){
    if (!b.alive) continue;
    // closest point on block to ball center
    const cx = Math.max(b.x, Math.min(ball.x, b.x + b.w));
    const cy = Math.max(b.y, Math.min(ball.y, b.y + b.h));
    const dx = ball.x - cx, dy = ball.y - cy;
    if (dx*dx + dy*dy <= BALL_R*BALL_R){
      // determine push axis
      const overlapX = BALL_R - Math.abs(dx);
      const overlapY = BALL_R - Math.abs(dy);
      if (Math.abs(dx) > Math.abs(dy)){
        ball.vx = (dx > 0 ? 1 : -1) * Math.abs(ball.vx);
        ball.x += (dx > 0 ? overlapX : -overlapX);
      } else {
        ball.vy = (dy > 0 ? 1 : -1) * Math.abs(ball.vy);
        ball.y += (dy > 0 ? overlapY : -overlapY);
      }
      // avoid zero components
      if (Math.abs(ball.vx) < 0.6) ball.vx = (ball.vx >= 0 ? 1 : -1) * 0.6;
      if (Math.abs(ball.vy) < 0.6) ball.vy = (ball.vy >= 0 ? 1 : -1) * 0.6;
      b.alive = false;
      score += 10;
      bumpSpeed();
      updateHUD();
      allClear();
      break;
    }
  }
}

function bumpSpeed(){
  ball.speed = Math.min(MAX_SPEED, ball.speed + SPEED_GAIN);
  const m = Math.hypot(ball.vx, ball.vy) || 1;
  ball.vx *= ball.speed / m;
  ball.vy *= ball.speed / m;
  // keep vy meaningful to avoid flat trajectories
  if (Math.abs(ball.vy) < ball.speed*0.25){
    ball.vy = (ball.vy >= 0 ? 1 : -1) * ball.speed*0.25;
    const nx = Math.sqrt(Math.max(0, ball.speed*ball.speed - ball.vy*ball.vy));
    ball.vx = (ball.vx >= 0 ? 1 : -1) * nx;
  }
}

// ---- AI ----
function aiThink(dt){
  // predict x where ball crosses paddle line, mirroring at walls
  let target = W/2;
  if (state === 'playing' && ball.vy > 0){
    const t = (PADDLE_Y - BALL_R - ball.y) / ball.vy;
    let x = ball.x + ball.vx * t;
    const span = 2*(W - 2*BALL_R);
    // mirror
    x = ((x - BALL_R) % span + span) % span;
    if (x > W - 2*BALL_R) x = W - 2*BALL_R - (x - (W - 2*BALL_R));
    x = x + BALL_R;
    target = x;
  } else if (state === 'playing'){
    target = W/2; // drift toward center while ball going up
  } else {
    target = W/2;
  }
  const center = paddle.x + PADDLE_W/2;
  const err = target - center;
  const maxMove = PADDLE_SPEED * 1.15 * dt * 60; // a touch faster than player
  if (Math.abs(err) < 3) return;
  paddle.x += Math.max(-maxMove, Math.min(maxMove, err));
  paddle.x = Math.max(0, Math.min(W - PADDLE_W, paddle.x));
}

// ---- update ----
function update(dt){
  // timers
  if (msgTimer > 0){
    msgTimer -= dt;
    if (msgTimer <= 0) msgEl.style.opacity = 0;
  }
  if (shake > 0) shake = Math.max(0, shake - dt*40);

  if (state === 'ready'){
    autoStartTimer -= dt;
    if (autoplay && autoStartTimer <= 0) launch();
    ball.x = paddle.x + PADDLE_W/2;
    ball.y = PADDLE_Y - BALL_R - 1;
    if (autoplay) aiThink(dt);
    else {
      if (keyL) paddle.x -= PADDLE_SPEED * dt * 60;
      if (keyR) paddle.x += PADDLE_SPEED * dt * 60;
      paddle.x = Math.max(0, Math.min(W-PADDLE_W, paddle.x));
    }
    return;
  }

  if (state === 'over' || state === 'won'){
    if (endGameTimer > 0){
      endGameTimer -= dt;
      if (endGameTimer <= 0) resetGame();
    }
    // ball keeps drifting for flavor
    ball.y += ball.vy * dt * 60 * 0.4;
    return;
  }

  // ---- playing ----
  if (autoplay) aiThink(dt);
  else {
    if (keyL) paddle.x -= PADDLE_SPEED * dt * 60;
    if (keyR) paddle.x += PADDLE_SPEED * dt * 60;
    paddle.x = Math.max(0, Math.min(W-PADDLE_W, paddle.x));
  }

  const step = 2; // substeps for robust collision at higher speeds
  for (let i = 0; i < step; i++){
    ball.x += ball.vx * dt * 60 / step;
    ball.y += ball.vy * dt * 60 / step;

    // walls
    if (ball.x - BALL_R < 0){ ball.x = BALL_R; ball.vx = Math.abs(ball.vx); }
    if (ball.x + BALL_R > W){ ball.x = W - BALL_R; ball.vx = -Math.abs(ball.vx); }
    if (ball.y - BALL_R < 0){ ball.y = BALL_R; ball.vy = Math.abs(ball.vy); }

    // paddle
    if (ball.vy > 0 &&
        ball.y + BALL_R >= PADDLE_Y &&
        ball.y + BALL_R <= PADDLE_Y + PADDLE_H + 8 &&
        ball.x >= paddle.x - BALL_R &&
        ball.x <= paddle.x + PADDLE_W + BALL_R){
      // angle based on hit position
      const rel = ((ball.x - paddle.x) / PADDLE_W) * 2 - 1; // -1..1
      const ang = rel * (Math.PI/3); // max 60 deg from vertical
      ball.vx = Math.sin(ang) * ball.speed;
      ball.vy = -Math.cos(ang) * ball.speed;
      ball.y = PADDLE_Y - BALL_R;
      bumpSpeed();
    }

    collideBlocks();
    if (state !== 'playing') break; // block may have been cleared -> won
  }

  // fell below
  if (ball.y - BALL_R > H) loseLife();
}

// ---- render ----
function render(){
  ctx.save();
  if (shake > 0){
    ctx.translate((Math.random()-0.5)*shake, (Math.random()-0.5)*shake);
  }

  ctx.clearRect(-10,-10,W+20,H+20);

  // subtle backdrop grid
  ctx.strokeStyle = 'rgba(80,100,180,0.06)';
  ctx.lineWidth = 1;
  for (let gx = 0; gx <= W; gx += 40){ ctx.beginPath(); ctx.moveTo(gx,0); ctx.lineTo(gx,H); ctx.stroke(); }
  for (let gy = 0; gy <= H; gy += 40){ ctx.beginPath(); ctx.moveTo(0,gy); ctx.lineTo(W,gy); ctx.stroke(); }

  // blocks
  for (const b of blocks){
    if (!b.alive) continue;
    ctx.fillStyle = b.color;
    ctx.globalAlpha = 0.9;
    ctx.fillRect(b.x, b.y, b.w, b.h);
    ctx.globalAlpha = 1;
    ctx.fillStyle = 'rgba(255,255,255,0.25)';
    ctx.fillRect(b.x, b.y, b.w, 4);
    ctx.strokeStyle = 'rgba(0,0,0,0.35)';
    ctx.strokeRect(b.x+0.5, b.y+0.5, b.w-1, b.h-1);
  }

  // paddle
  const pg = ctx.createLinearGradient(0, PADDLE_Y, 0, PADDLE_Y+PADDLE_H);
  pg.addColorStop(0, '#9fb6ff');
  pg.addColorStop(1, '#3a56c9');
  ctx.fillStyle = pg;
  ctx.beginPath();
  ctx.roundRect(paddle.x, PADDLE_Y, PADDLE_W, PADDLE_H, 7);
  ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,0.4)';
  ctx.fillRect(paddle.x+6, PADDLE_Y+2, PADDLE_W-12, 2);

  // ball (with glow)
  const bg = ctx.createRadialGradient(ball.x, ball.y, 1, ball.x, ball.y, BALL_R*2.2);
  bg.addColorStop(0, '#ffffff');
  bg.addColorStop(0.4, '#bcd0ff');
  bg.addColorStop(1, 'rgba(120,150,255,0)');
  ctx.fillStyle = bg;
  ctx.beginPath();
  ctx.arc(ball.x, ball.y, BALL_R*2.2, 0, Math.PI*2);
  ctx.fill();
  ctx.fillStyle = '#ffffff';
  ctx.beginPath();
  ctx.arc(ball.x, ball.y, BALL_R, 0, Math.PI*2);
  ctx.fill();

  // ready hint
  if (state === 'ready' && !autoplay){
    ctx.fillStyle = 'rgba(255,255,255,' + (0.5 + 0.4*Math.sin(performance.now()/250)) + ')';
    ctx.font = '16px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('PRESS SPACE TO LAUNCH', W/2, H - 70);
  }

  ctx.restore();
}

// ---- main loop ----
function frame(t){
  if (!lastTime) lastTime = t;
  let dt = (t - lastTime) / 1000;
  lastTime = t;
  if (dt > 0.05) dt = 0.05; // clamp big frame gaps

  update(dt);
  render();
  requestAnimationFrame(frame);
}

resetGame();
requestAnimationFrame(frame);

})();
</script>
</body>
</html>
```