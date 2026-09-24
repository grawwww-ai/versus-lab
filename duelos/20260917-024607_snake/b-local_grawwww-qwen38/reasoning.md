Create a single HTML file with a canvas snake game, score, arrow keys, restart with the space key, a demo mode that switches on P with an AI (path search via BFS, safe move, tail tracking), 60fps via a fixed-timestep game loop.

Let me try to write the AI: BFS from the head to the food, and choose a direction that reaches the food; also verify the move is safe (doesn't hit the snake's body, excluding the tail which is about to move — more simply: just check collision with the body). Also, if no path to food is found, fall back to a safe move that maximizes space (flood fill count).

Implementation:
- 24x24 grid, canvas around 480x480 + a top bar for score.
- Fixed dt accumulator, step the game every 100ms (or speed up according to score?). Keep it simple: about a 75ms step interval.
- 60fps via requestAnimationFrame, use an accumulator.

Game over screen: text "GAME OVER — Press Space to restart" (if not in demo, in demo auto-restart? In demo, auto-restart after a short delay so the viewer can watch).

Write the code carefully.

Canvas width 480, height 520; top 40px is the HUD for the score.

Score is drawn at the top center.

Keys: preventDefault for arrow keys and space.

Space: restart after game over (also allow during game? Requirement: restart with space after game over — only after game over, but always allowing it would also be fine).

Toggle demo with P: in demo the AI controls, and on game over auto-restart after a certain number of steps.

AI BFS:

```js
function aiChooseDir() {
  const head = snake[0];
  // candidate directions: all except reverse
  // for each candidate, BFS to food with body as obstacle
  // pick the one with the shortest path
  // if none, flood-fill safety check
}
```

Food safety check: after eating, check whether the snake can completely fit (optional; skip to keep code manageable but "skillful" — add a simple tail-reaching check: after simulating the move + eating, BFS from the new head to the new tail; if unreachable and the path is longer than the snake length, treat as bad). Keep a moderate version: BFS to food, if none, pick the safe neighbor cell with max flood-fill.

Also, to avoid instant death, check that a move doesn't hit the body (excluding the tail if it will move this step — more simply: treat body excluding the last element as an obstacle, but if the food was eaten, the tail stays; more simply: use all body cells as obstacles; a slight conservatism is fine).

Implementation:

```js
function bfs(start, target, blocked) // returns distance or -1, using a queue
function floodCount(start, blocked) // area reachable
```

blocked: a boolean grid built from the snake body (excluding the tail cell index len-1, which will vacate when not eating; conservative is OK: include everything except the last segment, but if the food is adjacent, include the tail too).

Let me just include all body cells as blocked; the AI still plays well enough.

Move speed: base interval 80ms, may speed up to 50ms according to score. Keep at 80.

Drawing: background grid, rounded green snake, red circle food, HUD.

Code:

```html
<!DOCTYPE html>...
```

Grid: COLS=24, ROWS=24, CELL=20 → 480x480 canvas + 40 HUD = 520.

Game state: snake array of {x,y}, dir {x,y}, pendingDir, food, score, alive, demo, gameOverTime.

Loop:

```js
let last = performance.now(), acc = 0;
const STEP = 80;
function frame(t){
  const dt = Math.min(t-last, 250); last=t; acc+=dt;
  while(acc >= STEP){ acc-=STEP; update(); }
  draw();
  requestAnimationFrame(frame);
}
```

update(): if not alive: if demo and now-gameOverTime > 1000, reset; return.
Otherwise, if demo: dir = aiChooseDir(), else dir = pendingDir (validate non-reverse).
Move the head; check wall/self collision → die.
If on the food: score++, spawn food, maybe speed up the step.

Draw: dark background, faint grid, score "SCORE: n" at top center, "DEMO MODE" indicator, game over text.

AI function:

```js
function aiChooseDir(){
  const head = snake[0];
  const dirs = [{x:1,y:0},{x:-1,y:0},{x:0,y:1},{x:0,y:-1}].filter(d => !(d.x===-dir.x && d.y===-dir.y));
  // BFS distances to food
  let best=null, bestDist=Infinity, bestCell=null;
  for(const d of dirs){
    const nx=head.x+d.x, ny=head.y+d.y;
    if(out(nx,ny) || isSnake(nx,ny)) continue;
    // BFS from that cell to food
    const dist = bfs(nx,ny);
    if(dist>=0){
      if(dist<bestDist){bestDist=dist; best=d; bestCell={x:nx,y:ny};}
    }
  }
```

bfs(start) — the food cell is not an obstacle (isSnake excludes the head position, but food isn't in the snake anyway). Obstacles = body except the tail (index snake.length-1)? When moving without eating, the tail vacates. When eating, the tail doesn't vacate. For food pathfinding, use obstacles = body excluding the tail.

If best is found: optional safety — simulate the state after eating: check whether a path exists to the tail. Skip; add a simpler filter: prefer moves where the post-move flood-fill area is at least the snake length. So:

```js
function area(nx,ny){ flood-fill count }
```

If best is not null, also check area(bestCell) >= snake.length, if it fails, fall back to the safe-move heuristic.

Fallback: for each safe candidate, area = flood-fill count; pick the max.

Food spawn: pick a random empty cell.

Collision check: after moving, is the new head in the body? The tail moves, so check against body excluding the tail (unless growing).

OK, let me write the complete file.
