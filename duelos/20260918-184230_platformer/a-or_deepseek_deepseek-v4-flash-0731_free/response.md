 ```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Auto-Runner Demo</title>
  <style>
    body {
      margin: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      background: #1a1e2f;
      font-family: monospace;
    }
    canvas {
      width: 960px;
      height: 540px;
      border: 4px solid #222;
      image-rendering: pixelated;
      background: #6ed0ff;
      box-shadow: 0 0 30px rgba(0,0,0,0.5);
    }
  </style>
</head>
<body>
<canvas id="game" width="960" height="540"></canvas>
<script>
  const canvas = document.getElementById('game');
  const ctx = canvas.getContext('2d');
  const W = 960, H = 540;

  // ---------- constants ----------
  const GROUND_TOP = 470;
  const PLAYER_SPEED = 5.2;
  const ENEMY_SPEED = 1.2;
  const GRAVITY = 0.55;
  const JUMP_VEL = -12.8;
  const MAX_FALL = 12;
  const LEVEL_WIDTH = 6600;
  const LEVEL_HEIGHT = 540;

  // ---------- global state ----------
  let camera = { x: 0, y: 0 };
  let keys = {};
  let gameState = 'playing';   // playing | win
  let score = 0;
  let coinCount = 0;
  let demoMode = false;
  let lastTime = 0;
  let frame = 0;

  let player;
  let platforms = [];
  let enemies = [];
  let coins = [];
  let particles = [];

  let aiAction = { left: false, right: false, jump: false };
  let aiJumping = false;

  // background data
  const farClouds = [];
  const nearClouds = [];

  // ---------- input ----------
  document.addEventListener('keydown', e => {
    keys[e.code] = true;
    if (['Space','ArrowUp','ArrowLeft','ArrowRight','KeyW','KeyA','KeyD'].includes(e.code)) e.preventDefault();
    if (e.code === 'KeyP') demoMode = !demoMode;
  });
  document.addEventListener('keyup', e => keys[e.code] = false);

  // ---------- helpers ----------
  function rectsOverlap(a, b) {
    return a.x < b.x + b.w && a.x + a.w > b.x &&
           a.y < b.y + b.h && a.y + a.h > b.y;
  }

  function addGround(x, w) {
    platforms.push({ x, y: GROUND_TOP, w, h: H - GROUND_TOP, oneWay: false });
  }

  function addPlatform(x, y, w) {
    platforms.push({ x, y, w: w || 64, h: 14, oneWay: true });
  }

  function addMovingPlatform(x, y, w, range, speed) {
    platforms.push({
      x, y, w: w || 64, h: 14, oneWay: true,
      moving: { baseX: x, range: range, speed: speed || 1.0, t: 0, dx: 0 }
    });
  }

  function addEnemy(x, y, minX, maxX) {
    enemies.push({
      x, y, w: 28, h: 28,
      vx: 0, vy: 0, dir: -1,
      minX, maxX,
      alive: true, onGround: false, prevY: 0, currentPlatform: null
    });
  }

  function addCoin(x, y) {
    coins.push({ x, y, w: 24, h: 24, collected: false, phase: Math.random() * Math.PI * 2 });
  }

  function addParticle(x, y, color) {
    for (let i = 0; i < 10; i++) {
      particles.push({
        x: x + (Math.random() - 0.5) * 20,
        y: y + (Math.random() - 0.5) * 20,
        vx: (Math.random() - 0.5) * 6,
        vy: -Math.random() * 4 - 1,
        gravity: 0.25,
        life: 1,
        color: color
      });
    }
  }

  // ---------- level design ----------
  function buildLevel() {
    platforms = [];
    enemies = [];
    coins = [];
    particles = [];

    // Main ground segments with small gaps
    addGround(0, 1200);
    addGround(1300, 1000);
    addGround(2400, 900);
    addGround(3400, 900);
    addGround(4400, 1000);
    addGround(5500, 1100);

    // Gaps -> place a moving platform over each gap
    addMovingPlatform(1200 - 40, GROUND_TOP - 70, 80, 60, 1.2);
    addMovingPlatform(2400 - 60, GROUND_TOP - 70, 90, 70, 1.0);
    addMovingPlatform(3400 - 50, GROUND_TOP - 60, 70, 50, 1.5);
    addMovingPlatform(4400 - 40, GROUND_TOP - 80, 90, 80, 1.1);
    addMovingPlatform(5500 - 40, GROUND_TOP - 70, 80, 60, 1.3);

    // Decorative floating platforms
    addPlatform(600, 360, 100);
    addPlatform(800, 300, 100);
    addPlatform(1500, 360, 120);
    addPlatform(2000, 300, 80);
    addPlatform(2700, 340, 90);
    addPlatform(4800, 320, 120);
    addPlatform(5200, 260, 100);

    // Enemies
    addEnemy(500, GROUND_TOP - 28, 100, 900);
    addEnemy(800, GROUND_TOP - 28, 200, 1000);
    addEnemy(1600, GROUND_TOP - 28, 1400, 2100);
    addEnemy(1800, GROUND_TOP - 28, 1600, 2200);
    addEnemy(3000, GROUND_TOP - 28, 2500, 3300);
    addEnemy(5000, GROUND_TOP - 28, 4400, 5200);
    addEnemy(6000, GROUND_TOP - 28, 5600, 6500);

    // Coins
    for (let i = 0; i < 8; i++) addCoin(150 + i * 25, 350);
    for (let i = 0; i < 6; i++) addCoin(1600 + i * 25, 360);
    for (let i = 0; i < 5; i++) addCoin(2500 + i * 25, 340);
    for (let i = 0; i < 6; i++) addCoin(3700 + i * 25, 350);
    for (let i = 0; i < 7; i++) addCoin(4800 + i * 25, 330);
    for (let i = 0; i < 5; i++) addCoin(6100 + i * 25, 360);

    // Background clouds
    farClouds.length = 0;
    nearClouds.length = 0;
    for (let i = 0; i < 12; i++) {
      farClouds.push({ x: Math.random() * LEVEL_WIDTH, y: 50 + Math.random() * 150, s: 0.8 + Math.random() * 0.7 });
    }
    for (let i = 0; i < 8; i++) {
      nearClouds.push({ x: Math.random() * LEVEL_WIDTH, y: 80 + Math.random() * 180, s: 1.2 + Math.random() * 0.8 });
    }
  }

  // ---------- reset ----------
  function resetGame() {
    gameState = 'playing';
    score = 0;
    coinCount = 0;
    particles = [];
    player = {
      x: 100,
      y: GROUND_TOP - 40,
      w: 24,
      h: 40,
      vx: 0,
      vy: 0,
      onGround: false,
      facing: 1,
      jumpPressed: false,
      jumpWasHeld: false,
      currentPlatform: null,
      prevY: 0
    };
    buildLevel();
    camera.x = 0;
    aiJumping = false;
  }

  resetGame();

  // ---------- AI ----------
  function updateAI() {
    aiAction.left = false;
    aiAction.right = true;
    aiAction.jump = false;

    if (!player.onGround) {
      if (aiJumping) aiAction.jump = true;
      return;
    }

    aiJumping = false;
    const lookAhead = 100;
    const aheadX = player.x + player.w + lookAhead;
    const footY = player.y + player.h + 4;

    let shouldJump = false;

    // Gap ahead
    const hasGround = platforms.some(p =>
      !p.oneWay &&
      aheadX >= p.x && aheadX <= p.x + p.w &&
      footY >= p.y && footY <= p.y + p.h + 8
    );
    if (!hasGround) shouldJump = true;

    // Enemy ahead
    for (let e of enemies) {
      if (e.alive && e.x > player.x && e.x < aheadX + 50 && Math.abs(e.y - player.y) < 70) {
        shouldJump = true;
        break;
      }
    }

    // Coin above
    for (let c of coins) {
      if (!c.collected && c.x > player.x && c.x < aheadX && c.y < player.y - 20) {
        shouldJump = true;
        break;
      }
    }

    if (shouldJump) {
      aiAction.jump = true;
      aiJumping = true;
    }
  }

  // ---------- physics / movement ----------
  function moveEntity(e, dt, isPlayer) {
    const prevY = e.y;
    const prevX = e.x;

    // X movement
    e.x += e.vx * dt;
    e.onGround = false;

    for (let p of platforms) {
      if (p.oneWay) continue;
      if (rectsOverlap(e, p)) {
        if (e.vx > 0) e.x = p.x - e.w;
        else if (e.vx < 0) e.x = p.x + p.w;
        else {
          e.x = (prevX + e.w / 2 <= p.x + p.w / 2) ? p.x - e.w : p.x + p.w;
        }
        e.vx = 0;
      }
    }

    // Y movement
    e.y += e.vy * dt;

    for (let p of platforms) {
      if (!rectsOverlap(e, p)) continue;

      if (p.oneWay) {
        if (e.vy >= 0 && prevY + e.h <= p.y + 4) {
          e.y = p.y - e.h;
          e.vy = 0;
          e.onGround = true;
          if (isPlayer) player.currentPlatform = p;
        }
        continue;
      }

      if (e.vy >= 0 && prevY + e.h <= p.y + 4) {
        e.y = p.y - e.h;
        e.vy = 0;
        e.onGround = true;
        if (isPlayer) player.currentPlatform = p;
      } else if (e.vy < 0 && prevY >= p.y + p.h - 4) {
        e.y = p.y + p.h;
        e.vy = 0;
      } else {
        if (e.vx > 0) e.x = p.x - e.w;
        else if (e.vx < 0) e.x = p.x + p.w;
        else {
          e.x = (e.x + e.w / 2 <= p.x + p.w / 2) ? p.x - e.w : p.x + p.w;
        }
        e.vx = 0;
      }
    }

    if (!e.onGround) {
      if (isPlayer) player.currentPlatform = null;
    }
  }

  // ---------- update moving platforms ----------
  function updateMovingPlatforms(dt) {
    for (let p of platforms) {
      if (p.moving) {
        const prevX = p.x;
        p.moving.t += 0.02 * dt * p.moving.speed;
        p.x = p.moving.baseX + Math.sin(p.moving.t) * p.moving.range;
        p.moving.dx = p.x - prevX;
      }
    }
  }

  // ---------- player death ----------
  function playerDie() {
    addParticle(player.x + player.w / 2, player.y + player.h / 2, '#ff3333');
    resetGame();
  }

  // ---------- update ----------
  function update(dt) {
    frame++;
    dt = Math.min(dt, 1.5);

    // Copy AI
    let heldLeft = keys['ArrowLeft'] || keys['KeyA'];
    let heldRight = keys['ArrowRight'] || keys['KeyD'];
    let heldJump = keys['Space'] || keys['ArrowUp'] || keys['KeyW'];

    if (demoMode) {
      updateAI();
      heldLeft = aiAction.left;
      heldRight = aiAction.right;
      heldJump = aiAction.jump;
    }

    // Jump edge detection
    if (heldJump && !player.jumpWasHeld) player.jumpPressed = true;
    player.jumpWasHeld = heldJump;

    // horizontal
    player.vx = 0;
    if (heldLeft) player.vx = -PLAYER_SPEED;
    if (heldRight) player.vx = PLAYER_SPEED;
    if (heldLeft && heldRight) player.vx = 0;

    // jump
    if (player.jumpPressed) {
      if (player.onGround) player.vy = JUMP_VEL;
      player.jumpPressed = false;
    }

    // variable jump height
    if (!heldJump && player.vy < -5) player.vy = -5;

    // gravity
    player.vy += GRAVITY * dt;
    if (player.vy > MAX_FALL) player.vy = MAX_FALL;

    // save prev for collision
    player.prevY = player.y;

    // update moving platforms before movement
    updateMovingPlatforms(dt);

    // move player
    const wasOnMoving = player.currentPlatform && player.currentPlatform.moving;
    const wasX = player.x;
    moveEntity(player, dt, true);

    // ride moving platforms
    if (player.onGround && player.currentPlatform && player.currentPlatform.moving && wasOnMoving) {
      const dx = player.currentPlatform.moving.dx;
      player.x += dx;
    }

    // facing
    if (player.vx > 0) player.facing = 1;
    if (player.vx < 0) player.facing = -1;

    // clamp left/right
    if (player.x < 0) player.x = 0;
    if (player.x + player.w > LEVEL_WIDTH) player.x = LEVEL_WIDTH - player.w;

    // kill if fallen
    if (player.y > H + 60) {
      resetGame();
      return;
    }

    // enemies
    for (let e of enemies) {
      if (!e.alive) continue;

      e.vy = Math.min(e.vy + GRAVITY * dt, 12 * dt);
      e.vx = e.dir * ENEMY_SPEED * dt;

      // horizontal patrol limits
      const