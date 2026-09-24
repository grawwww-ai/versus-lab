```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Snake</title>
<style>
    html, body {
        margin: 0;
        padding: 0;
        height: 100%;
        background: #0d0d1a;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: monospace;
        overflow: hidden;
    }
    #gameContainer {
        position: relative;
    }
    canvas {
        display: block;
        background: #111122;
        border: 2px solid #333355;
        border-radius: 4px;
        box-shadow: 0 0 30px rgba(0, 255, 128, 0.15);
    }
    #hud {
        position: absolute;
        top: 10px;
        left: 0;
        width: 100%;
        text-align: center;
        color: #4dff9d;
        font-size: 22px;
        font-weight: bold;
        letter-spacing: 2px;
        pointer-events: none;
        text-shadow: 0 0 8px rgba(77, 255, 157, 0.6);
    }
    #overlay {
        position: absolute;
        inset: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        color: #ff5566;
        font-size: 34px;
        font-weight: bold;
        letter-spacing: 3px;
        pointer-events: none;
        background: rgba(10, 10, 20, 0.55);
        text-shadow: 0 0 12px rgba(255, 85, 102, 0.8);
    }
    #overlay small {
        font-size: 16px;
        color: #ccccdd;
        margin-top: 14px;
        letter-spacing: 1px;
        text-shadow: none;
    }
    .hidden { display: none !important; }
</style>
</head>
<body>
<div id="gameContainer">
    <canvas id="game" width="600" height="600"></canvas>
    <div id="hud">SCORE: <span id="score">0</span></div>
    <div id="overlay" class="hidden">GAME OVER <small>Press SPACE to restart</small></div>
</div>

<script>
(function () {
    "use strict";

    const canvas = document.getElementById("game");
    const ctx = canvas.getContext("2d");
    const scoreEl = document.getElementById("score");
    const overlayEl = document.getElementById("overlay");

    const GRID = 20;                       // cell size in px
    const COLS = canvas.width / GRID;      // 30
    const ROWS = canvas.height / GRID;     // 30
    const TICK_MS = 80;                    // snake logic step (~12.5 cells/s)

    let snake, dir, nextDir, food, score, alive, acc, lastTime;

    function reset() {
        const cx = Math.floor(COLS / 2);
        const cy = Math.floor(ROWS / 2);
        snake = [
            { x: cx, y: cy },
            { x: cx - 1, y: cy },
            { x: cx - 2, y: cy }
        ];
        dir = { x: 1, y: 0 };   // moving right
        nextDir = { x: 1, y: 0 };
        score = 0;
        alive = true;
        acc = 0;
        placeFood();
        scoreEl.textContent = "0";
        overlayEl.classList.add("hidden");
    }

    function placeFood() {
        // random cell not occupied by the snake
        while (true) {
            const f = {
                x: (Math.random() * COLS) | 0,
                y: (Math.random() * ROWS) | 0
            };
            if (!snake.some(s => s.x === f.x && s.y === f.y)) {
                food = f;
                return;
            }
        }
    }

    function step() {
        dir = nextDir;
        const head = snake[0];
        const nx = head.x + dir.x;
        const ny = head.y + dir.y;

        // wall collision
        if (nx < 0 || ny < 0 || nx >= COLS || ny >= ROWS) {
            return gameOver();
        }
        // self collision (tail cell about to move away is fine unless we grow)
        const willEat = (nx === food.x && ny === food.y);
        const len = willEat ? snake.length : snake.length - 1;
        for (let i = 0; i < len; i++) {
            if (snake[i].x === nx && snake[i].y === ny) {
                return gameOver();
            }
        }

        snake.unshift({ x: nx, y: ny });

        if (willEat) {
            score += 10;
            scoreEl.textContent = score;
            placeFood();
        } else {
            snake.pop();
        }
    }

    function gameOver() {
        alive = false;
        overlayEl.classList.remove("hidden");
    }

    function draw() {
        // background
        ctx.fillStyle = "#111122";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // subtle grid
        ctx.strokeStyle = "rgba(255,255,255,0.03)";
        ctx.lineWidth = 1;
        for (let i = 1; i < COLS; i++) {
            ctx.beginPath();
            ctx.moveTo(i * GRID + 0.5, 0);
            ctx.lineTo(i * GRID + 0.5, canvas.height);
            ctx.stroke();
        }
        for (let i = 1; i < ROWS; i++) {
            ctx.beginPath();
            ctx.moveTo(0, i * GRID + 0.5);
            ctx.lineTo(canvas.width, i * GRID + 0.5);
            ctx.stroke();
        }

        // food
        const fx = food.x * GRID + GRID / 2;
        const fy = food.y * GRID + GRID / 2;
        const pulse = 0.85 + 0.15 * Math.sin(performance.now() / 150);
        ctx.beginPath();
        ctx.arc(fx, fy, (GRID / 2 - 3) * pulse, 0, Math.PI * 2);
        ctx.fillStyle = "#ff4455";
        ctx.shadowColor = "#ff4455";
        ctx.shadowBlur = 12;
        ctx.fill();
        ctx.shadowBlur = 0;

        // snake
        for (let i = snake.length - 1; i >= 0; i--) {
            const s = snake[i];
            const t = i / Math.max(snake.length - 1, 1);
            const g = Math.round(255 - t * 130);
            ctx.fillStyle = i === 0 ? "#baffd9" : "rgb(60," + g + ",140)";
            ctx.fillRect(s.x * GRID + 1, s.y * GRID + 1, GRID - 2, GRID - 2);
            if (i === 0) {
                // eyes
                ctx.fillStyle = "#111122";
                const ex = s.x * GRID + GRID / 2;
                const ey = s.y * GRID + GRID / 2;
                const ox = dir.y !== 0 ? 4 : 0;
                const oy = dir.x !== 0 ? 4 : 0;
                const fxo = dir.x * 3, fyo = dir.y * 3;
                ctx.beginPath();
                ctx.arc(ex + fxo - ox, ey + fyo - oy, 2, 0, Math.PI * 2);
                ctx.arc(ex + fxo + ox, ey + fyo + oy, 2, 0, Math.PI * 2);
                ctx.fill();
            }
        }
    }

    // Fixed-timestep loop: logic at TICK_MS, rendering at display refresh (60fps+)
    function loop(now) {
        if (lastTime === undefined) lastTime = now;
        let dt = now - lastTime;
        lastTime = now;
        if (dt > 250) dt = 250; // avoid spiral after tab switch

        if (alive) {
            acc += dt;
            while (acc >= TICK_MS) {
                acc -= TICK_MS;
                step();
                if (!alive) break;
            }
        }
        draw();
        requestAnimationFrame(loop);
    }

    // input: arrow keys, no 180° reversal, one direction change queued per tick
    const keyMap = {
        ArrowUp:    { x: 0, y: -1 },
        ArrowDown:  { x: 0, y: 1 },
        ArrowLeft:  { x: -1, y: 0 },
        ArrowRight: { x: 1, y: 0 }
    };

    document.addEventListener("keydown", function (e) {
        const k = e.key;
        if (k in keyMap || k === " ") e.preventDefault();

        if (!alive) {
            if (k === " ") reset();
            return;
        }
        const nd = keyMap[k];
        if (!nd) return;
        // forbid direct reversal against the *current* movement direction
        if (nd.x === -dir.x && nd.y === -dir.y) return;
        nextDir = nd;
    });

    // auto-start
    reset();
    requestAnimationFrame(loop);
})();
</script>
</body>
</html>
```