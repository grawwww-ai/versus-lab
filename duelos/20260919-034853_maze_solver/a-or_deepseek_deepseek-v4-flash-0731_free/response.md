Here’s a complete, self-contained HTML page that runs a BFS animation on your maze and draws the solution path once the goal is found.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>BFS Maze Solver</title>
  <style>
    * {
      box-sizing: border-box;
    }
    body {
      margin: 0;
      overflow: hidden;
      background: #0b0f20;
      font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
      color: #e2e8f0;
    }
    #mazeCanvas {
      position: fixed;
      inset: 0;
      display: block;
    }

    #hud {
      position: fixed;
      top: 14px;
      left: 50%;
      transform: translateX(-50%);
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: center;
      gap: 14px;
      background: rgba(10, 15, 30, 0.78);
      border: 1px solid rgba(255, 255, 255, 0.08);
      padding: 10px 18px;
      border-radius: 16px;
      backdrop-filter: blur(8px);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45);
      z-index: 10;
      font-size: 14px;
      white-space: nowrap;
      letter-spacing: 0.3px;
    }
    #hud .title {
      font-weight: 700;
      letter-spacing: 0.6px;
      background: linear-gradient(90deg, #93c5fd, #fbbf24);
      -webkit-background-clip: text;
      background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .sep {
      width: 1px;
      height: 24px;
      background: rgba(255, 255, 255, 0.15);
    }
    .stat b {
      color: #fbbf24;
      font-weight: 600;
      font-variant-numeric: tabular-nums;
      margin-left: 4px;
    }
  </style>
</head>
<body>
  <canvas id="mazeCanvas"></canvas>

  <div id="hud">
    <div class="title">BFS Maze</div>
    <div class="sep"></div>
    <div class="stat">Seen <b id="seen">1</b></div>
    <div class="stat">Frontier <b id="frontier">1</b></div>
    <div class="sep"></div>
    <div class="stat">Path <b id="path">—</b></div>
  </div>

  <script>
    const maze = [
      "#S#.....#...........#",
      "#.###.#.#.#.#####.#.#",
      "#...#.#.#.#.....#.#.#",
      "###.#.###...###.#.#.#",
      "#.#.#...#.#...#.#...#",
      "#.#.###.#.#.###.#####",
      "#.#.......#...#.....#",
      "#.#.#.#.#.###.#####.#",
      "#.#.#.#.#.#...#.....#",
      "#.#.#.###.#.###.###.#",
      "#.#.#.#...#.#...#...#",
      "#.#.#.#.###.#.###.###",
      "#...#.......#.#...#.#",
      "#.###.#######...###.#",
      "#.#.....#.....#...#.#",
      "#.#######.#######.#.#",
      "#.#.....#...#...#.#.#",
      "#.#.###.###.#.###.#.#",
      "#...#.......#......E#",
      "#####################"
    ];

    const grid = maze;
    const ROWS = grid.length;
    const COLS = grid[0].length;

    let startRC = null;
    let endRC = null;

    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        if (grid[r][c] === "S") startRC = [r, c];
        if (grid[r][c] === "E") endRC = [r, c];
      }
    }

    const DIRS = [
      [-1, 0],
      [1, 0],
      [0, -1],
      [0, 1]
    ];

    // BFS
    function bfs() {
      const parent = Array.from({ length: ROWS }, () =>
        Array.from({ length: COLS }, () => null)
      );
      const visited = Array.from({ length: ROWS }, () =>
        Array.from({ length: COLS }, () => false)
      );

      const events = [];
      const q = [];
      let qIndex = 0;

      const [sr, sc] = startRC;
      const [er, ec] = endRC;

      visited[sr][sc] = true;
      q.push([sr, sc]);

      let found = false;

      while (qIndex < q.length && !found) {
        const cur = q[qIndex++];
        const [cr, cc] = cur;
        const discovered = [];

        for (const [dr, dc] of DIRS) {
          const nr = cr + dr;
          const nc = cc + dc;

          if (nr < 0 || nr >= ROWS || nc < 0 || nc >= COLS) continue;
          if (grid[nr][nc] === "#") continue;
          if (visited[nr][nc]) continue;

          visited[nr][nc] = true;
          parent[nr][nc] = cur;
          discovered.push([nr, nc]);

          if (nr === er && nc === ec) {
            found = true;
            break;
          }

          q.push([nr, nc]);
        }

        events.push({ cell: cur, discovered });
      }

      // Reconstruct path
      const path = [];
      let current = endRC;

      while (current && (current[0] !== startRC[0] || current[1] !== startRC[1])) {
        path.push(current);
        current = parent[current[0]] ? parent[current[0]][current[1]] : null;
      }

      path.push(startRC);
      path.reverse();

      return { events, path };
    }

    const { events, path } = bfs();

    // Canvas setup
    const canvas = document.getElementById("mazeCanvas");
    const ctx = canvas.getContext("2d");

    let cell = 24;
    let ox = 0;
    let oy = 0;
    const HUD_TOP = 72;
    const HUD_BOTTOM = 32;

    function resize() {
      const w = window.innerWidth;
      const h = window.innerHeight;

      const availW = w - 20;
      const availH = h - HUD_TOP - HUD_BOTTOM;

      cell = Math.max(8, Math.floor(Math.min(availW / COLS, availH / ROWS)));
      ox = Math.floor((w - COLS * cell) / 2);
      oy = Math.floor(HUD_TOP + (availH - ROWS * cell) / 2);

      canvas.width = w * window.devicePixelRatio;
      canvas.height = h * window.devicePixelRatio;
      canvas.style.width = w + "px";
      canvas.style.height = h + "px";

      ctx.setTransform(window.devicePixelRatio, 0, 0, window.devicePixelRatio, 0, 0);
    }

    // State
    const state = {
      phase: "explore", // explore -> path -> done
      stepIndex: 0,
      discovered: new Set([startRC[0] + "," + startRC[1]]),
      frontier: new Set([startRC[0] + "," + startRC[1]]),
      exploredCount: 1,
      current: startRC,
      pathProgress: 0,
      pathStartTime: 0
    };

    const SEEN = document.getElementById("seen");
    const FRONTIER = document.getElementById("frontier");
    const PATH = document.getElementById("path");

    function updateHUD() {
      SEEN.textContent = state.exploredCount;
      FRONTIER.textContent = state.frontier.size;

      if (state.phase === "path" || state.phase === "done") {
        PATH.textContent = (path.length - 1) + " steps";
      }
    }

    // Drawing helpers
    function roundRect(x, y, w, h, r) {
      r = Math.min(r, w / 2, h / 2);
      ctx.beginPath();
      ctx.moveTo(x + r, y);
      ctx.arcTo(x + w, y, x + w, y + h, r);
      ctx.arcTo(x + w, y + h, x, y + h, r);
      ctx.arcTo(x, y + h, x, y, r);
      ctx.arcTo(x, y, x + w, y, r);
      ctx.closePath();
    }

    function fillCell(r, c, color, padRatio = 0.1) {
      const pad = cell * padRatio;
      roundRect(
        ox + c * cell + pad,
        oy + r * cell + pad,
        cell - pad * 2,
        cell - pad * 2,
        cell * 0.22
      );
      ctx.fillStyle = color;
      ctx.fill();
    }

    function drawMaze() {
      for (let r = 0; r < ROWS; r++) {
        for (let c = 0; c < COLS; c++) {
          const x = ox + c * cell;
          const y = oy + r * cell;

          if (grid[r][c] === "#") {
            roundRect(x + 0.5, y + 0.5, cell - 1, cell - 1, cell * 0.18);
            ctx.fillStyle = "#1d293d";
            ctx.fill();

            roundRect(x + cell * 0.24, y + cell * 0.24, cell * 0.52, cell * 0.52, cell * 0.16);
            ctx.fillStyle = "rgba(255,255,255,0.045)";
            ctx.fill();
          } else {
            roundRect(x + 0.5, y + 0.5, cell - 1, cell - 1, cell * 0.14);
            ctx.fillStyle = "rgba(255,255,255,0.04)";
            ctx.fill();
          }
        }
      }
    }

    function drawOverlay(now) {
      const time = now || 0;

      // Expanded
      for (const key of state.discovered) {
        if (state.frontier.has(key)) continue;
        if (state.current && key === state.current[0] + "," + state.current[1]) continue;
        const [r, c] = key.split(",").map(Number);
        fillCell(r, c, "rgba(14,116,144,0.42)", 0.10);
      }

      // Frontier
      for (const key of state.frontier) {
        const [r, c] = key.split(",").map(Number);
        const pulse = 0.42 + 0.18 * (0.5 + 0.5 * Math.sin(time / 240));
        fillCell(r, c, `rgba(234,88,12,${pulse})`, 0.08);
      }

      // Current expanded head
      if (state.current) {
        const [r, c] = state.current;
        fillCell(r, c, "rgba(248,250,252,0.4)", 0.16);
      }
    }

    function drawSolution(progress) {
      if (!progress || progress <= 0 || path.length < 2) return;

      ctx.save();
      ctx.lineCap = "round";
      ctx.lineJoin = "round";

      const pts = path.map(([r, c]) => [
        ox + c * cell + cell / 2,
        oy + r * cell + cell / 2
      ]);

      const total = pts.length - 1;
      const floatIdx = Math.max(0, Math.min(total, progress * total));
      const full = Math.floor(floatIdx);
      const frac = floatIdx - full;

      ctx.beginPath();
      ctx.moveTo(pts[0][0], pts[0][1]);

      for (let i = 1; i <= full; i++) {
        ctx.lineTo(pts[i][0], pts[i][1]);
      }

      if (full < total && frac > 0) {
        const p1 = pts[full];
        const p2 = pts[full + 1];
        ctx.lineTo(
          p1[0] + (p2[0] - p1[0]) * frac,
          p1[1] + (p2[1] - p1[1]) * frac
        );
      }

      ctx.shadowColor = "rgba(250,204,21,0.9)";
      ctx.shadowBlur = 16;
      ctx.strokeStyle = "rgba(250,204,21,0.88)";
      ctx.lineWidth = Math.max(2, cell * 0.42);
      ctx.stroke();

      ctx.shadowBlur = 0;
      ctx.strokeStyle = "rgba(255,255,255,0.92)";
      ctx.lineWidth = Math.max(1, cell * 0.12);
      ctx.stroke();

      ctx.restore();
    }

    function drawStartEnd() {
      const [sr, sc] = startRC;
      const [er, ec] = endRC;

      roundRect(
        ox + sc * cell + cell * 0.18,
        oy + sr * cell + cell * 0.18,
        cell * 0.64,
        cell * 0.64,
        cell * 0.24
      );
      ctx.fillStyle = "rgba(16,185,129,0.82)";
      ctx.fill();

      roundRect(
        ox + ec * cell + cell * 0.18,
        oy + er * cell + cell * 0.18,
        cell * 0.64,
        cell * 0.64,
        cell * 0.24
      );
      ctx.fillStyle = "rgba(239,68,68,0.88)";
      ctx.fill();
    }

    function draw(now) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Background gradient
      const grad = ctx.createLinearGradient(0, 0, 0, window.innerHeight);
      grad.addColorStop(0, "#0b1020");
      grad.addColorStop(1, "#0f172a");
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, window.innerWidth, window.innerHeight);

      drawMaze();

      if (state.phase === "explore") {
        drawOverlay(now);
      } else {
        drawOverlay(now);
      }

      if (state.phase === "path" || state.phase === "done") {
        const progress = state.phase === "done" ? 1 : state.pathProgress;
        drawSolution(progress);
      }

      drawStartEnd();
    }

    // Step forward in BFS exploration
    function stepExplore(now) {
      if (state.phase !== "explore") return;

      if (state.stepIndex >= events.length) {
        finishExplore();
        return;
      }

      const ev = events[state.stepIndex];
      state.stepIndex++;

      const curKey = ev.cell[0] + "," + ev.cell[1];
      state.frontier.delete(curKey);
      state.discovered.add(curKey);
      state.current = ev.cell;

      const [er, ec] = endRC;

      for (const [nr, nc] of ev.discovered) {
        const key = nr + "," + nc;
        state.discovered.add(key);

        if (!(nr === er && nc === ec)) {
          state.frontier.add(key);
        }
      }

      state.exploredCount = state.discovered.size;
      updateHUD();
      draw(now);

      if (state.stepIndex >= events.length) {
        setTimeout(finishExplore, 400);
      } else {
        setTimeout(() => stepExplore(performance.now()), STEP_MS);
      }
    }

    const STEP_MS = Math.max(10, Math.min(90, 5600 / events.length));

    function finishExplore() {
      state.phase = "path";
      state.pathStartTime = performance.now();
      updateHUD();
      requestAnimationFrame(drawPathFrame);
    }

    function drawPathFrame(now) {
      const t = Math.min(1, (now - state.pathStartTime) / 2600);
      state.pathProgress = t;
      updateHUD();
      draw(now);

      if (t < 1) {
        requestAnimationFrame(drawPathFrame);
      } else {
        state.phase = "done";
        state.pathProgress = 1;
        updateHUD();
        draw(now);
      }
    }

    // Start everything
    window.addEventListener("resize", () => {
      resize();
      draw(performance.now());
    });

    resize();
    updateHUD();
    draw(performance.now());

    setTimeout(() => stepExplore(performance.now()), 600);
  </script>
</body>
</html>
```

### How it works

- The maze is read directly from your input.
- A standard BFS algorithm explores cells level by level.
- The interface shows:
  - **Blue cells** – already visited,
  - **Orange cells** – currently in the BFS frontier,
  - **Yellow path** – the final shortest route from `S` to `E`.
- The “Seen” counter shows how many cells have been discovered, “Frontier” is the BFS queue size, and the path length is displayed after the search finishes.

The animation starts automatically when the page is opened.