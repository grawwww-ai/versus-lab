```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
  <title>Flappy Bird Clone</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { 
      background: #1a1a2e; 
      display: flex; 
      justify-content: center; 
      align-items: center; 
      min-height: 100vh; 
      font-family: 'Courier New', Courier, monospace;
      overflow: hidden;
    }
    #gameCanvas { 
      display: block; 
      box-shadow: 0 0 30px rgba(0,0,0,0.5), inset 0 0 60px rgba(0,0,0,0.3);
      border-radius: 4px;
      background: #4ec0ca;
    }
    .overlay {
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      pointer-events: none;
      z-index: 10;
    }
    .overlay.hidden { display: none; }
    .title {
      font-size: 48px;
      font-weight: bold;
      color: #fff;
      text-shadow: 3px 3px 0 #2c3e50, 6px 6px 0 rgba(0,0,0,0.2);
      letter-spacing: 4px;
      margin-bottom: 20px;
      animation: bounce 2s ease-in-out infinite;
    }
    @keyframes bounce { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
    .subtitle { color: #ecf0f1; font-size: 16px; text-shadow: 1px 1px 2px #000; margin-bottom: 10px; }
    .controls { color: #bdc3c7; font-size: 14px; line-height: 1.8; text-align: center; text-shadow: 1px 1px 2px #000; }
    .demo-badge {
      position: fixed;
      top: 20px;
      right: 20px;
      background: linear-gradient(135deg, #e74c3c, #c0392b);
      color: white;
      padding: 8px 16px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: bold;
      letter-spacing: 1px;
      box-shadow: 0 4px 15px rgba(231,76,60,0.4);
      animation: pulse 1s ease-in-out infinite;
      z-index: 20;
    }
    .demo-badge.hidden { display: none; }
    @keyframes pulse { 0%,100% { transform: scale(1); } 50% { transform: scale(1.05); } }
    .score-display {
      position: fixed;
      top: 20px;
      left: 50%;
      transform: translateX(-50%);
      font-size: 60px;
      font-weight: bold;
      color: #fff;
      text-shadow: 
        3px 3px 0 #2c3e50,
        6px 6px 0 rgba(0,0,0,0.3);
      z-index: 15;
      pointer-events: none;
      transition: opacity 0.3s;
    }
    .game-over-overlay {
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0,0,0,0.75);
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      z-index: 30;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.3s;
    }
    .game-over-overlay.visible { opacity: 1; pointer-events: auto; }
    .game-over-text {
      font-size: 48px;
      font-weight: bold;
      color: #e74c3c;
      text-shadow: 3px 3px 0 #c0392b, 6px 6px 0 rgba(0,0,0,0.3);
      margin-bottom: 20px;
      animation: shake 0.5s ease-in-out;
    }
    @keyframes shake { 0%,100% { transform: translateX(0); } 25% { transform: translateX(-10px); } 75% { transform: translateX(10px); } }
    .final-score { font-size: 36px; color: #f1c40f; text-shadow: 2px 2px 0 #b7950b; margin-bottom: 30px; }
    .restart-text { color: #ecf0f1; font-size: 18px; text-shadow: 1px 1px 2px #000; animation: blink 1s ease-in-out infinite; }
    @keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }
  </style>
</head>
<body>
  <canvas id="gameCanvas" width="400" height="600"></canvas>
  
  <div class="overlay" id="startOverlay">
    <div class="title">FLAPPY BIRD</div>
    <div class="subtitle">Press SPACE or Click to Start</div>
    <div class="controls">
      SPACE / Click/Tap — Jump<br>
      P — Toggle Demo Mode (AI plays)
    </div>
  </div>

  <div class="demo-badge hidden" id="demoBadge">DEMO MODE</div>
  
  <div class="score-display" id="scoreDisplay">0</div>

  <div class="game-over-overlay" id="gameOverOverlay">
    <div class="game-over-text">GAME OVER</div>
    <div class="final-score" id="finalScore">Score: 0</div>
    <div class="restart-text">Press SPACE or Click to Restart</div>
  </div>

<script>
// ============ GAME CONSTANTS ============
const CANVAS_W = 400;
const CANVAS_H = 600;
const GRAVITY = 0.55;
const JUMP_FORCE = -9.5;
const PIPE_SPEED = 2.5;
const PIPE_GAP = 150;
const PIPE_WIDTH = 60;
const PIPE_SPAWN_INTERVAL = 1500;
const BIRD_RADIUS = 14;
const BIRD_X = 80;
const GROUND_HEIGHT = 80;
const SKY_COLOR_TOP = '#2c3e50';
const SKY_COLOR_BOTTOM = '#4ec0ca';

// ============ GAME STATE ============
let canvas, ctx;
let bird = { y: 0, vy: 0, rotation: 0, wingPhase: 0 };
let pipes = [];
let clouds = [];
let groundOffset = 0;
let score = 0;
let bestScore = 0;
let frameCount = 0;
let gameState = 'start'; // 'start', 'playing', 'gameover'
let demoMode = false;
let lastPipeSpawn = 0;
let passedPipeIndex = -1;

// ============ INITIALIZATION ============
function init() {
  canvas = document.getElementById('gameCanvas');
  ctx = canvas.getContext('2d');
  
  resetGame();
  spawnInitialClouds();
  
  window.addEventListener('keydown', handleKeydown);
  window.addEventListener('click', handleClick);
  canvas.addEventListener('touchstart', handleTouch, { passive: true });
  
  requestAnimationFrame(gameLoop);
}

function resetGame() {
  bird = { 
    y: CANVAS_H / 2, 
    vy: 0, 
    rotation: 0, 
    wingPhase: 0 
  };
  pipes = [];
  groundOffset = 0;
  score = 0;
  frameCount = 0;
  passedPipeIndex = -1;
  lastPipeSpawn = -PIPE_SPAWN_INTERVAL;
  gameState = demoMode ? 'playing' : 'start';
  
  updateScoreDisplay();
  updateOverlays();
}

function spawnInitialClouds() {
  clouds = [];
  for (let i = 0; i < 5; i++) {
    clouds.push({
      x: Math.random() * CANVAS_W,
      y: 50 + Math.random() * 200,
      speed: 0.2 + Math.random() * 0.3,
      scale: 0.5 + Math.random() * 0.8,
      opacity: 0.3 + Math.random() * 0.4
    });
  }
}

// ============ INPUT HANDLING ============
function handleKeydown(e) {
  if (e.code === 'Space') {
    e.preventDefault();
    if (gameState === 'start') {
      startGame();
    } else if (gameState === 'playing') {
      jump();
    } else if (gameState === 'gameover') {
      resetGame();
    }
  } else if (e.code === 'KeyP') {
    toggleDemoMode();
  }
}

function handleClick() {
  if (gameState === 'start') {
    startGame();
  } else if (gameState === 'playing' && !demoMode) {
    jump();
  } else if (gameState === 'gameover') {
    resetGame();
  }
}

function handleTouch(e) {
  if (gameState === 'start') {
    startGame();
  } else if (gameState === 'playing' && !demoMode) {
    jump();
  } else if (gameState === 'gameover') {
    resetGame();
  }
}

function startGame() {
  gameState = 'playing';
  updateOverlays();
}

function jump() {
  bird.vy = JUMP_FORCE;
  bird.rotation = -0.5;
}

function toggleDemoMode() {
  demoMode = !demoMode;
  const badge = document.getElementById('demoBadge');
  badge.classList.toggle('hidden', !demoMode);
  
  if (demoMode && gameState === 'start') {
    startGame();
  } else if (!demoMode && gameState === 'playing') {
    // Keep playing, just switch control to human
  }
  resetGame();
}

// ============ GAME LOOP ============
function gameLoop() {
  update();
  render();
  requestAnimationFrame(gameLoop);
}

function update() {
  frameCount++;
  
  if (gameState !== 'playing') return;
  
  // Demo AI
  if (demoMode) {
    updateDemoAI();
  }
  
  // Bird physics
  bird.vy += GRAVITY;
  bird.y += bird.vy;
  
  // Bird rotation based on velocity
  bird.rotation = Math.max(-0.5, Math.min(1.2, bird.vy * 0.08));
  
  // Wing animation
  bird.wingPhase += 0.3;
  
  // Ground scroll
  groundOffset = (groundOffset - PIPE_SPEED) % 40;
  
  // Spawn pipes
  if (frameCount - lastPipeSpawn >= PIPE_SPAWN_INTERVAL / (1000/60)) {
    spawnPipe();
    lastPipeSpawn = frameCount;
  }
  
  // Update pipes
  for (let i = pipes.length - 1; i >= 0; i--) {
    pipes[i].x -= PIPE_SPEED;
    
    // Check score
    if (i > passedPipeIndex && pipes[i].x + PIPE_WIDTH < BIRD_X) {
      score++;
      passedPipeIndex = i;
      updateScoreDisplay();
    }
    
    // Remove off-screen pipes
    if (pipes[i].x + PIPE_WIDTH < 0) {
      pipes.splice(i, 1);
      if (passedPipeIndex >= i) passedPipeIndex--;
    }
  }
  
  // Collision detection
  checkCollisions();
  
  // Update clouds
  for (let cloud of clouds) {
    cloud.x -= cloud.speed;
    if (cloud.x + 100 * cloud.scale < 0) {
      cloud.x = CANVAS_W + 50;
      cloud.y = 50 + Math.random() * 200;
    }
  }
}

function updateDemoAI() {
  // Find next pipe
  let nextPipe = null;
  for (let pipe of pipes) {
    if (pipe.x + PIPE_WIDTH > BIRD_X - BIRD_RADIUS) {
      nextPipe = pipe;
      break;
    }
  }
  
  if (nextPipe) {
    const gapCenter = nextPipe.gapY;
    const distanceToPipe = nextPipe.x - BIRD_X;
    const birdBottom = bird.y + BIRD_RADIUS;
    const birdTop = bird.y - BIRD_RADIUS;
    
    // Predict bird position when reaching pipe
    const framesToPipe = distanceToPipe / PIPE_SPEED;
    const predictedY = bird.y + bird.vy * framesToPipe + 0.5 * GRAVITY * framesToPipe * framesToPipe;
    
    // Jump if bird will be below gap center
    const targetY = gapCenter - 10; // Slight offset to stay in upper part of gap
    const shouldJump = predictedY > targetY && bird.vy > -2;
    
    // Also jump if currently too low
    if (bird.y > gapCenter + 20) {
      jump();
    } else if (shouldJump && distanceToPipe < 120) {
      jump();
    }
  }
}

function spawnPipe() {
  const minGapY = 120;
  const maxGapY = CANVAS_H - GROUND_HEIGHT - 120;
  const gapY = minGapY + Math.random() * (maxGapY - minGapY);
  
  pipes.push({
    x: CANVAS_W,
    gapY: gapY,
    scored: false
  });
}

function checkCollisions() {
  // Ground collision
  if (bird.y + BIRD_RADIUS >= CANVAS_H - GROUND_HEIGHT) {
    gameOver();
    return;
  }
  
  // Ceiling collision
  if (bird.y - BIRD_RADIUS <= 0) {
    gameOver();
    return;
  }
  
  // Pipe collisions
  for (let pipe of pipes) {
    const pipeLeft = pipe.x;
    const pipeRight = pipe.x + PIPE_WIDTH;
    const gapTop = pipe.gapY - PIPE_GAP / 2;
    const gapBottom = pipe.gapY + PIPE_GAP / 2;
    
    // Bird bounding box
    const birdLeft = BIRD_X - BIRD_RADIUS;
    const birdRight = BIRD_X + BIRD_RADIUS;
    const birdTop = bird.y - BIRD_RADIUS;
    const birdBottom = bird.y + BIRD_RADIUS;
    
    // Check horizontal overlap
    if (birdRight > pipeLeft && birdLeft < pipeRight) {
      // Check vertical collision with top pipe
      if (birdTop < gapTop) {
        gameOver();
        return;
      }
      // Check vertical collision with bottom pipe
      if (birdBottom > gapBottom) {
        gameOver();
        return;
      }
    }
  }
}

function gameOver() {
  gameState = 'gameover';
  bestScore = Math.max(bestScore, score);
  document.getElementById('finalScore').textContent = `Score: ${score}  |  Best: ${bestScore}`;
  updateOverlays();
  
  // Small screen shake effect
  canvas.style.animation = 'shake 0.3s ease-in-out';
  setTimeout(() => canvas.style.animation = '', 300);
}

function updateScoreDisplay() {
  document.getElementById('scoreDisplay').textContent = score;
}

function updateOverlays() {
  const startOverlay = document.getElementById('startOverlay');
  const gameOverOverlay = document.getElementById('gameOverOverlay');
  const scoreDisplay = document.getElementById('scoreDisplay');
  
  startOverlay.classList.toggle('hidden', gameState !== 'start');
  gameOverOverlay.classList.toggle('visible', gameState === 'gameover');
  scoreDisplay.style.opacity = gameState === 'playing' ? '1' : '0';
}

// ============ RENDERING ============
function render() {
  // Clear
  ctx.clearRect(0, 0, CANVAS_W, CANVAS_H);
  
  // Sky gradient
  drawSky();
  
  // Clouds
  drawClouds();
  
  // Pipes
  drawPipes();
  
  // Ground
  drawGround();
  
  // Bird
  drawBird();
  
  // Demo mode indicator on canvas
  if (demoMode && gameState === 'playing') {
    drawDemoIndicator();
  }
}

function drawSky() {
  const gradient = ctx.createLinearGradient(0, 0, 0, CANVAS_H);
  gradient.addColorStop(0, '#2c3e50');
  gradient.addColorStop(0.4, '#3498db');
  gradient.addColorStop(1, '#4ec0ca');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, CANVAS_W, CANVAS_H);
  
  // Sun/moon
  const time = frameCount * 0.002;
  const sunX = CANVAS_W - 60 + Math.sin(time) * 20;
  const sunY = 80 + Math.cos(time) * 15;
  const sunGradient = ctx.createRadialGradient(sunX, sunY, 0, sunX, sunY, 40);
  sunGradient.addColorStop(0, '#f1c40f');
  sunGradient.addColorStop(0.5, '#f39c12');
  sunGradient.addColorStop(1, 'rgba(241,196,15,0)');
  ctx.fillStyle = sunGradient;
  ctx.beginPath();
  ctx.arc(sunX, sunY, 40, 0, Math.PI * 2);
  ctx.fill();
}

function drawClouds() {
  for (let cloud of clouds) {
    ctx.save();
    ctx.globalAlpha = cloud.opacity;
    ctx.scale(cloud.scale, cloud.scale);
    
    drawCloudShape(cloud.x / cloud.scale, cloud.y / cloud.scale);
    
    ctx.restore();
  }
}

function drawCloudShape(x, y) {
  ctx.fillStyle = '#fff';
  ctx.beginPath();
  ctx.arc(x, y, 25, 0, Math.PI * 2);
  ctx.arc(x + 30, y - 10, 20, 0, Math.PI * 2);
  ctx.arc(x + 60, y, 25, 0, Math.PI * 2);
  ctx.arc(x + 30, y + 15, 18, 0, Math.PI * 2);
  ctx.fill();
}

function drawPipes() {
  for (let pipe of pipes) {
    const x = pipe.x;
    const gapTop = pipe.gapY - PIPE_GAP / 2;
    const gapBottom = pipe.gapY + PIPE_GAP / 2;
    const pipeRight = x + PIPE_WIDTH;
    
    // Top pipe
    drawPipeSegment(x, 0, PIPE_WIDTH, gapTop, true);
    
    // Bottom pipe
    drawPipeSegment(x, gapBottom, PIPE_WIDTH, CANVAS_H - GROUND_HEIGHT - gapBottom, false);
  }
}

function drawPipeSegment(x, y, w, h, isTop) {
  // Pipe body gradient
  const bodyGradient = ctx.createLinearGradient(x, 0, x + w, 0);
  bodyGradient.addColorStop(0, '#2ecc71');
  bodyGradient.addColorStop(0.3, '#27ae60');
  bodyGradient.addColorStop(0.7, '#27ae60');
  bodyGradient.addColorStop(1, '#1e824c');
  
  ctx.fillStyle = bodyGradient;
  ctx.fillRect(x, y, w, h);
  
  // Highlight
  ctx.fillStyle = 'rgba(255,255,255,0.15)';
  ctx.fillRect(x + 3, y, 8, h);
  
  // Dark edge
  ctx.fillStyle = 'rgba(0,0,0,0.2)';
  ctx.fillRect(x + w - 4, y, 4, h);
  
  // Pipe cap
  const capHeight = 25;
  const capWidth = w + 10;
  const capX = x - 5;
  const capY = isTop ? y + h - capHeight : y;
  
  const capGradient = ctx.createLinearGradient(capX, 0, capX + capWidth, 0);
  capGradient.addColorStop(0, '#2ecc71');
  capGradient.addColorStop(0.5, '#27ae60');
  capGradient.addColorStop(1, '#1e824c');
  
  ctx.fillStyle = capGradient;
  ctx.fillRect(capX, capY, capWidth, capHeight);
  
  // Cap highlight
  ctx.fillStyle = 'rgba(255,255,255,0_2)';
  ctx.fillRect(capX + 3, capY, 10, capHeight);
  
  // Cap dark edge
  ctx.fillStyle = 'rgba(0,0,0,0.2)';
  ctx.fillRect(capX + capWidth - 4, capY, 4, capHeight);
  
  // Cap border
  ctx.strokeStyle = 'rgba(0,0,0,0.3)';
  ctx.lineWidth = 2;
  ctx.strokeRect(capX, capY, capWidth, capHeight);
}

function drawGround() {
  const groundY = CANVAS_H - GROUND_HEIGHT;
  
  // Ground base
  const groundGradient = ctx.createLinearGradient(0, groundY, 0, CANVAS_H);
  groundGradient.addColorStop(0, '#e67e22');
  groundGradient.addColorStop(0.3, '#d35400');
  groundGradient.addColorStop(1, '#a04000');
  ctx.fillStyle = groundGradient;
  ctx.fillRect(0, groundY, CANVAS_W, GROUND_HEIGHT);
  
  // Grass pattern
  ctx.fillStyle = '#27ae60';
  for (let i = -20; i < CANVAS_W + 20; i += 40) {
    const x = (i - groundOffset) % (CANVAS_W + 40) - 20;
    drawGrassTuft(x, groundY + 5);
  }
  
  // Ground highlight line
  ctx.fillStyle = 'rgba(255,255,255,0.1)';
  ctx.fillRect(0, groundY, CANVAS_W, 3);
  
  // Dirt texture
  ctx.fillStyle = 'rgba(0,0,0,0.05)';
  for (let i = 0; i < 30; i++) {
    const x = (i * 137.5 + groundOffset * 2) % CANVAS_W;
    const y = groundY + 15 + (i * 73.3) % 40;
    const r = 2 + (i * 11) % 4;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
  }
}

function drawGrassTuft(x, y) {
  ctx.beginPath();
  ctx.moveTo(x, y + 15);
  ctx.lineTo(x - 5, y);
  ctx.lineTo(x + 5, y);
  ctx.closePath();
  ctx.fill();
  
  ctx.beginPath();
  ctx.moveTo(x + 8, y + 15);
  ctx.lineTo(x + 3, y - 2);
  ctx.lineTo(x + 13, y - 2);
  ctx.closePath();
  ctx.fill();
}

function drawBird() {
  ctx.save();
  ctx.translate(BIRD_X, bird.y);
  ctx.rotate(bird.rotation);
  
  // Bird body shadow
  ctx.fillStyle = 'rgba(0,0,0,0.2)';
  ctx.beginPath();
  ctx.ellipse(3, 3, BIRD_RADIUS * 0.9, BIRD_RADIUS * 0.7, 0, 0, Math.PI * 2);
  ctx.fill();
  
  // Bird body
  const bodyGradient = ctx.createRadialGradient(-3, -3, 0, 0, 0, BIRD_RADIUS);
  bodyGradient.addColorStop(0, '#f1c40f');
  bodyGradient.addColorStop(0.5, '#f39c12');
  bodyGradient.addColorStop(1, '#e67e22');
  ctx.fillStyle = bodyGradient;
  
  ctx.beginPath();
  ctx.ellipse(0, 0, BIRD_RADIUS, BIRD_RADIUS * 0.8, 0, 0, Math.PI * 2);
  ctx.fill();
  
  // Belly
  ctx.fillStyle = '#f1c40f';
  ctx.beginPath();
  ctx.ellipse(0, 3, BIRD_RADIUS * 0.6, BIRD_RADIUS * 0.4, 0, 0, Math.PI * 2);
  ctx.fill();
  
  // Wing
  const wingAngle = Math.sin(bird.wingPhase) * 0.5;
  ctx.fillStyle = '#e67e22';
  ctx.save();
  ctx.translate(2, 0);
  ctx.rotate(wingAngle);
  ctx.beginPath();
  ctx.ellipse(0, 0, BIRD_RADIUS * 0.7, BIRD_RADIUS * 0.35, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
  
  // Eye
  ctx.fillStyle = '#fff';
  ctx.beginPath();
  ctx.arc(BIRD_RADIUS * 0.3, -BIRD_RADIUS * 0.2, 6, 0, Math.PI * 2);
  ctx.fill();
  
  ctx.fillStyle = '#2c3e50';
  ctx.beginPath();
  ctx.arc(BIRD_RADIUS * 0.3 + 2, -BIRD_RADIUS * 0.2, 3, 0, Math.PI * 2);
  ctx.fill();
  
  // Eye highlight
  ctx.fillStyle = 'rgba(255,255,255,0.8)';
  ctx.beginPath();
  ctx.arc(BIRD_RADIUS * 0.3 + 3, -BIRD_RADIUS * 0.2 - 1, 1.5, 0, Math.PI * 2);
  ctx.fill();
  
  // Beak
  ctx.fillStyle = '#e67e22';
  ctx.beginPath();
  ctx.moveTo(BIRD_RADIUS, -2);
  ctx.lineTo(BIRD_RADIUS + 12, 0);
  ctx.lineTo(BIRD_RADIUS, 4);
  ctx.closePath();
  ctx.fill();
  
  // Beak highlight
  ctx.fillStyle = 'rgba(255,255,255,0.2)';
  ctx.beginPath();
  ctx.moveTo(BIRD_RADIUS, 0);
  ctx.lineTo(BIRD_RADIUS + 8, 1);
  ctx.lineTo(BIRD_RADIUS, 3);
  ctx.closePath();
  ctx.fill();
  
  ctx.restore();
}

function drawDemoIndicator() {
  ctx.save();
  ctx.font = 'bold 14px Courier New';
  ctx.fillStyle = 'rgba(231,76,60,0.9)';
  ctx.textAlign = 'right';
  ctx.fillText('AI CONTROL', CANVAS_W - 15, 30);
  ctx.restore();
}

// ============ START ============
init();
</script>
</body>
</html>
```