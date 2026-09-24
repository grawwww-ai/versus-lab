```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Snake</title>
<style>
  html, body {
    margin: 0;
    padding: 0;
    background: #111;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: monospace;
    overflow: hidden;
  }
  #gameCanvas {
    background: #1a1a1a;
    border: 2px solid #444;
    display: block;
  }
</style>
</head>
<body>
<canvas id="gameCanvas" width="600" height="600"></canvas>
<script>
(function () {
  "use strict";

  const canvas = document.getElementById("gameCanvas");
  const ctx = canvas.getContext("2d");

  // Grid configuration
  const COLS = 30;
  const ROWS = 30;
  const TILE = canvas.width / COLS; // 20px
  const TICK_MS = 100;              // snake step interval

  // Game state
  let snake, dir, nextDir, food, score, gameOver, tickAccumulator;

  function reset() {
    const cx = Math.floor(COLS / 2);
    const cy = Math.floor(ROWS / 2);
    // Snake starts at center, moving right (head first, then body to the left)
    snake = [
      { x: cx, y: cy },
      { x: cx - 1, y: cy },
      { x: cx - 2, y: cy }
    ];
    dir = { x: 1, y: 0 };
    nextDir = { x: 1, y: 0 };
    score = 0;
    gameOver = false;
    tickAccumulator = 0;
    placeFood();
  }

  function placeFood() {
    // Choose a random free cell
    let cell;
    let free = COLS * ROWS - snake.length;
    do {
      cell = {
        x: Math.floor(Math.random() * COLS),
        y: Math.floor(Math.random() * ROWS)
      };
    } while (snake.some(s => s.x === cell.x && s.y === cell.y) || free < 0);
    food = cell;
  }

  function step() {
    dir = nextDir;
    const head = { x: snake[0].x + dir.x, y: snake[0].y + dir.y };

    // Wall collision
    if (head.x < 0 || head.x >= COLS || head.y < 0 || head.y >= ROWS) {
      gameOver = true;
      return;
    }

    const ate = (head.x === food.x && head.y === food.y);

    // Self collision (tail cell is OK if not growing, but check before move for simplicity
    // against current body excluding tail when not eating)
    const limit = ate ? snake.length : snake.length - 1;
    for (let i = 0; i < limit; i++) {
      if (snake[i].x === head.x && snake[i].y === head.y) {
        gameOver = true;
        return;
      }
    }

    snake.unshift(head);

    if (ate) {
      score += 10;
      if (snake.length >= COLS * ROWS) {
        gameOver = true; // win condition: board full
        return;
      }
      placeFood();
    } else {
      snake.pop();
    }
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Subtle grid
    ctx.strokeStyle = "rgba(255,255,255,0.04)";
    ctx.lineWidth = 1;
    for (let i = 1; i < COLS; i++) {
      ctx.beginPath();
      ctx.moveTo(i * TILE + 0.5, 0);
      ctx.lineTo(i * TILE + 0.5, canvas.height);
      ctx.stroke();
    }
    for (let i = 1; i < ROWS; i++) {
      ctx.beginPath();
      ctx.moveTo(0, i * TILE + 0.5);
      ctx.lineTo(canvas.width, i * TILE + 0.5);
      ctx.stroke();
    }

    // Food
    ctx.fillStyle = "#e74c3c";
    const fx = food.x * TILE, fy = food.y * TILE;
    ctx.beginPath();
    ctx.arc(fx + TILE / 2, fy + TILE / 2, TILE * 0.38, 0, Math.PI * 2);
    ctx.fill();

    // Snake
    for (let i = snake.length - 1; i >= 0; i--) {
      const s = snake[i];
      const isHead = i === 0;
      ctx.fillStyle = isHead ? "#7bed9f" : "#2ecc71";
      ctx.fillRect(s.x * TILE + 1, s.y * TILE + 1, TILE - 2, TILE - 2);
    }

    // Score at top center
    ctx.fillStyle = "#fff";
    ctx.font = "bold 20px monospace";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    ctx.fillText("SCORE: " + score, canvas.width / 2, 10);

    if (gameOver) {
      ctx.fillStyle = "rgba(0,0,0,0.6)";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = "#e74c3c";
      ctx.font = "bold 40px monospace";
      ctx.fillText("GAME OVER", canvas.width / 2, canvas.height / 2 - 40);
      ctx.fillStyle = "#fff";
      ctx.font = "bold 18px monospace";
      ctx.fillText("Final score: " + score, canvas.width / 2, canvas.height / 2 + 10);
      ctx.font = "16px monospace";
      ctx.fillText("Press SPACE to restart", canvas.width / 2, canvas.height / 2 + 45);
    }
  }

  // --- Input ---
  document.addEventListener("keydown", function (e) {
    const key = e.key;
    // Prevent page scroll on arrows/space
    if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", " "].includes(key)) {
      e.preventDefault();
    }

    if (gameOver) {
      if (key === " ") reset();
      return;
    }

    switch (key) {
      case "ArrowUp":
        if (dir.y !== 1) nextDir = { x: 0, y: -1 };
        break;
      case "ArrowDown":
        if (dir.y !== -1) nextDir = { x: 0, y: 1 };
        break;
      case "ArrowLeft":
        if (dir.x !== 1) nextDir = { x: -1, y: 0 };
        break;
      case "ArrowRight":
        if (dir.x !== -1) nextDir = { x: 1, y: 0 };
        break;
    }
  });

  // --- Main loop: fixed timestep updates, render every frame (~60fps) ---
  let lastTime = performance.now();

  function loop(now) {
    let frameTime = now - lastTime;
    lastTime = now;

    // Clamp to avoid spiral of death after tab switch
    if (frameTime > 250) frameTime = 250;

    if (!gameOver) {
      tickAccumulator += frameTime;
      while (tickAccumulator >= TICK_MS) {
        step();
        tickAccumulator -= TICK_MS;
        if (gameOver) { tickAccumulator = 0; break; }
      }
    }

    draw();
    requestAnimationFrame(loop);
  }

  reset();
  requestAnimationFrame(loop);
})();
</script>
</body>
</html>
```