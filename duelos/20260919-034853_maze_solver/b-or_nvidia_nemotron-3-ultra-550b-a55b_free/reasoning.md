We need to create a single HTML file with an animated maze solver. The maze is given as 21x21 text. We must draw it exactly, large and centered. Use canvas or SVG. Animate a search algorithm (e.g., BFS) step by step, showing visited cells and frontier. When exit found, animate the shortest path as a glowing line/trail. Show live counter of explored cells, and at the end show length of shortest path in steps. Expose final path as window.solution array of [row, col] pairs (0-based). Animation starts automatically, takes about 8-10 seconds total. No external resources, inline CSS/JS.

We'll use HTML5 Canvas for performance and ease of animation. We'll parse the maze string. We'll implement BFS to find shortest path. But we need to animate the exploration step by step. BFS explores level by level. We can animate each step (visiting a cell) with a small delay. Total steps: number of visited cells until exit found. Maze is 21x21, max cells 441. BFS might visit many. To fit 8-10 seconds, we need to adjust speed. If we visit ~200 cells, each step ~40ms => 8 seconds. We'll set a delay per step, maybe 30ms. Also need to animate the final path drawing.

We'll draw maze: each cell is a square. We'll scale to fit window, centered. Use devicePixelRatio for crispness.

We'll maintain a queue for BFS. At each animation frame, we process one node (or a few) and draw visited cells. We'll also draw frontier (cells in queue) maybe with a different color.

When exit found, we reconstruct path by backtracking parents. Then animate drawing the path: maybe draw segments one by one with a glow effect.

We'll show counters: explored cells count (visited count), and at end path length.

We'll set window.solution = path array.

Implementation details:

- Parse maze lines: split by newline, each line length 21. Find S and E coordinates.
- Directions: up, down, left, right.
- BFS: queue holds {r,c}. visited set. parent map to reconstruct path.
- Animation loop: use requestAnimationFrame with time-based stepping. We'll have a variable `lastStepTime` and `stepInterval` (e.g., 30ms). At each frame, if enough time passed, process next BFS step.
- Drawing: clear canvas, draw walls, visited cells, frontier cells, start/end, path being drawn.
- Colors: walls dark, floor light. Visited: maybe light blue. Frontier: yellow. Path: glowing gold with gradient.
- For glow effect on path: we can draw a thick line with shadowBlur, or draw multiple fading circles along path.
- Path animation: after BFS completes, we have path array. We'll animate drawing it by incrementally adding points to a drawn path array, each frame add one point (or a few). Draw line connecting them with stroke style and shadow.

- Counters: DOM elements overlay on canvas? Or draw text on canvas. Simpler: overlay HTML divs positioned absolutely over canvas. But requirement: "show a live counter of explored cells and, at the end, the length of the shortest path in steps." Could be HTML elements on top. Since it's full window, we can put a fixed div at top left with counters. That's easier.

- Ensure canvas is full window, centered maze. We'll compute cell size based on min(windowWidth, windowHeight) * 0.9 / 21. Then offset to center.

- No external fonts: use system font.

- All in one HTML file.

Let's outline code structure:

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Maze Solver</title>
<style>
  body { margin:0; overflow:hidden; background:#111; font-family: monospace; }
  canvas { display:block; position:absolute; top:0; left:0; }
  #info { position:absolute; top:10px; left:10px; color:#fff; z-index:10; pointer-events:none; }
  #info div { margin:4px 0; }
</style>
</head>
<body>
<canvas id="canvas"></canvas>
<div id="info">
  <div>Explored: <span id="explored">0</span></div>
  <div>Path length: <span id="pathlen">-</span></div>
</div>
<script>
// Maze string
const mazeStr = `#####################
#S#.....#...........#
#.###.#.#.#.#####.#.#
#...#.#.#.#.....#.#.#
###.#.###...###.#.#.#
#.#.#...#.#...#.#...#
#.#.###.#.#.###.#####
#.#.......#...#.....#
#.#.#.#.#.###.#####.#
#.#.#.#.#.#...#.....#
#.#.#.###.#.###.###.#
#.#.#.#...#.#...#...#
#.#.#.#.###.#.###.###
#...#.......#.#...#.#
#.###.#######...###.#
#.#.....#.....#...#.#
#.#######.#######.#.#
#.#.....#...#...#.#.#
#.#.###.###.#.###.#.#
#...#.......#......E#
#####################`;

// Parse
const rows = mazeStr.trim().split('\n');
const H = rows.length;
const W = rows[0].length;
let start = null, end = null;
const grid = [];
for (let r=0; r<H; r++) {
  const row = [];
  for (let c=0; c<W; c++) {
    const ch = rows[r][c];
    row.push(ch);
    if (ch === 'S') start = {r,c};
    if (ch === 'E') end = {r,c};
  }
  grid.push(row);
}

// Canvas setup
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
let cellSize = 0;
let offsetX = 0, offsetY = 0;

function resize() {
  const dpr = window.devicePixelRatio || 1;
  const width = window.innerWidth;
  const height = window.innerHeight;
  canvas.width = width * dpr;
  canvas.height = height * dpr;
  canvas.style.width = width + 'px';
  canvas.style.height = height + 'px';
  ctx.scale(dpr, dpr);
  // Compute cell size to fit maze with padding
  const padding = 40;
  const maxCellWidth = (width - padding*2) / W;
  const maxCellHeight = (height - padding*2) / H;
  cellSize = Math.min(maxCellWidth, maxCellHeight);
  offsetX = (width - cellSize * W) / 2;
  offsetY = (height - cellSize * H) / 2;
}
window.addEventListener('resize', resize);
resize();

// BFS state
const queue = [start];
const visited = new Array(H).fill(0).map(() => new Array(W).fill(false));
const parent = new Array(H).fill(0).map(() => new Array(W).fill(null));
visited[start.r][start.c] = true;
let exploredCount = 0;
let found = false;
let path = [];
let pathAnimIndex = 0;
const directions = [[-1,0],[1,0],[0,-1],[0,1]];

// Animation timing
const stepInterval = 30; // ms per BFS step
let lastStepTime = 0;
const pathStepInterval = 50; // ms per path segment
let lastPathStepTime = 0;
let bfsComplete = false;

function bfsStep() {
  if (queue.length === 0) return;
  const current = queue.shift();
  exploredCount++;
  document.getElementById('explored').textContent = exploredCount;
  // Check if exit
  if (current.r === end.r && current.c === end.c) {
    found = true;
    // Reconstruct path
    let cur = current;
    while (cur) {
      path.unshift([cur.r, cur.c]);
      cur = parent[cur.r][cur.c];
    }
    bfsComplete = true;
    return;
  }
  // Explore neighbors
  for (const [dr, dc] of directions) {
    const nr = current.r + dr;
    const nc = current.c + dc;
    if (nr >= 0 && nr < H && nc >= 0 && nc < W && !visited[nr][nc] && grid[nr][nc] !== '#') {
      visited[nr][nc] = true;
      parent[nr][nc] = current;
      queue.push({r:nr, c:nc});
    }
  }
}

function animate(timestamp) {
  if (!lastStepTime) lastStepTime = timestamp;
  if (!lastPathStepTime) lastPathStepTime = timestamp;

  // BFS phase
  if (!bfsComplete) {
    if (timestamp - lastStepTime >= stepInterval) {
      bfsStep();
      lastStepTime = timestamp;
    }
  } else {
    // Path animation phase
    if (pathAnimIndex < path.length) {
      if (timestamp - lastPathStepTime >= pathStepInterval) {
        pathAnimIndex++;
        lastPathStepTime = timestamp;
        if (pathAnimIndex === path.length) {
          document.getElementById('pathlen').textContent = path.length - 1; // steps = edges count
        }
      }
    }
  }

  draw();
  requestAnimationFrame(animate);
}

function draw() {
  const w = canvas.width / (window.devicePixelRatio || 1);
  const h = canvas.height / (window.devicePixelRatio || 1);
  ctx.clearRect(0, 0, w, h);

  // Draw walls and floor
  for (let r=0; r<H; r++) {
    for (let c=0; c<W; c++) {
      const x = offsetX + c * cellSize;
      const y = offsetY + r * cellSize;
      if (grid[r][c] === '#') {
        ctx.fillStyle = '#222';
        ctx.fillRect(x, y, cellSize, cellSize);
      } else {
        ctx.fillStyle = '#1a1a2e';
        ctx.fillRect(x, y, cellSize, cellSize);
      }
    }
  }

  // Draw visited cells (excluding start/end maybe)
  ctx.fillStyle = 'rgba(0, 200, 255, 0.4)';
  for (let r=0; r<H; r++) {
    for (let c=0; c<W; c++) {
      if (visited[r][c] && !(r===start.r && c===start.c) && !(r===end.r && c===end.c)) {
        const x = offsetX + c * cellSize;
        const y = offsetY + r * cellSize;
        ctx.fillRect(x+1, y+1, cellSize-2, cellSize-2);
      }
    }
  }

  // Draw frontier (cells in queue)
  ctx.fillStyle = 'rgba(255, 255, 0, 0.6)';
  for (const cell of queue) {
    const x = offsetX + cell.c * cellSize;
    const y = offsetY + cell.r * cellSize;
    ctx.fillRect(x+1, y+1, cellSize-2, cellSize-2);
  }

  // Draw start and end
  const drawCell = (r,c,color) => {
    const x = offsetX + c * cellSize;
    const y = offsetY + r * cellSize;
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x + cellSize/2, y + cellSize/2, cellSize/3, 0, Math.PI*2);
    ctx.fill();
  };
  drawCell(start.r, start.c, '#0f0');
  drawCell(end.r, end.c, '#f00');

  // Draw path being animated
  if (pathAnimIndex > 1) {
    ctx.strokeStyle = 'gold';
    ctx.lineWidth = cellSize * 0.3;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.shadowColor = 'gold';
    ctx.shadowBlur = cellSize * 0.5;
    ctx.beginPath();
    const first = path[0];
    ctx.moveTo(offsetX + first[1]*cellSize + cellSize/2, offsetY + first[0]*cellSize + cellSize/2);
    for (let i=1; i<pathAnimIndex; i++) {
      const p = path[i];
      ctx.lineTo(offsetX + p[1]*cellSize + cellSize/2, offsetY + p[0]*cellSize + cellSize/2);
    }
    ctx.stroke();
    ctx.shadowBlur = 0;
  }
}

// Expose solution
window.solution = [];

// Start animation
requestAnimationFrame(animate);

// After BFS completes, set window.solution
// We'll set it when path is found.
const originalBfsStep = bfsStep;
bfsStep = function() {
  originalBfsStep();
  if (found && window.solution.length === 0) {
    window.solution = path.map(([r,c]) => [r,c]);
  }
};
</script>
</body>
</html>
```

But need to ensure the path length counter shows steps (edges). The problem says "length of the shortest path in steps". Usually steps = number of moves, which is path.length - 1. We'll display that.

Also need to ensure the animation takes about 8-10 seconds total. With stepInterval 30ms and maybe up to 200 visited cells, that's 6 seconds. Path animation with 50ms per step for maybe 50 steps = 2.5 seconds. Total ~8.5 seconds. Good.

We should also consider that BFS might visit many cells. The maze is 21x21, but walls reduce open cells. Let's count roughly: The maze has many walls. BFS will visit all reachable cells until exit. Could be up to ~200. 200*30ms = 6s. Path length maybe 50. 50*50ms = 2.5s. Total 8.5s. Good.

We need to ensure the maze is drawn exactly as given. We used the string directly.

Potential issues: The maze string includes spaces? No, it's lines of characters. We trimmed and split by newline. Ensure each line length is 21. The given maze lines have 21 chars each. Good.

We used `grid[nr][nc] !== '#'` for walkable. That includes 'S', 'E', '.'.

We set visited for start initially. Good.

We draw visited cells as semi-transparent blue. Frontier as yellow. Start green, end red.

Path animation: we draw a glowing line connecting centers of path cells. We use shadowBlur for glow. The line width is 0.3*cellSize. That should look nice.

We update explored counter each BFS step. At end, we set path length.

We expose window.solution as array of [row, col] pairs. We set it when found first time.

One nuance: The BFS step function is called multiple times per frame if timestamp difference large? We only call once per frame because we check `if (timestamp - lastStepTime >= stepInterval) { bfsStep(); lastStepTime = timestamp; }`. That's fine.

But we also need to ensure that the BFS doesn't run too fast if tab is in background? requestAnimationFrame pauses in background, so it's fine.

We should also handle the case where the maze is not solvable? But given it has E, it should be.

Now, we need to output the complete HTML file in a single code block.

Let's double-check the maze string: It has 21 lines, each 21 chars. The first line is all '#', last line all '#'. Good.

We'll produce the final HTML.

Potential improvements: Use a more beautiful visualization: maybe draw walls with 3D effect? But requirement: "beautiful animated visualization". Our simple colors with glow might be okay. Could add a subtle grid lines. But it's fine.

We'll also add a slight fade for visited cells? Not needed.

We'll ensure the canvas is full window and centered.

We'll also add a check to prevent multiple solution assignments.

Now, write the final HTML.