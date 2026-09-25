We need answer with complete HTML file in code block. Need build maze animation. Need think carefully. We need solve maze. Need draw exactly maze as given 21 rows x 21 columns? Need verify each row length. Need ensure rendering large centered, full window canvas/SVG. Need animate search algorithm step by step, visited cells light up, frontier visible. When exit found, animate SHORTEST path from S to E as glowing line/trail. Live counter explored cells, and at end length shortest path steps. Expose final path as window.solution array [row,column] from S to E inclusive 0-based. Animation starts automatically total 8-10 sec. One self-contained HTML.

Need choose BFS for shortest path. Could animate BFS: frontier queue, visited set. At each frame reveal next cell(s), maybe show frontier and visited. Need timing. Total 8-10 sec including exploring and path animation. Maze 21x21 with ~ maybe 180 open cells. Need manageable. Could animate with intervals maybe 30ms per step. Need ensure BFS finds shortest. Need path.

Need draw exact maze. Use canvas. Need parse string into grid. Need include walls. Need handle S/E. Need rows all 21 chars. Let's verify maze text. I'll copy rows. Need ensure no trailing newline? The code block in prompt has 21 rows maybe. Let's count. Row0 "#####################" length 21. Row1 "#S#.....#...........#" length? # S # ..... # ........... # =1+1+1+5+1+11+1=21? Let's count "..........." 11 yes, total 21. Row2 "#.###.#.#.#.#####.#.#" length? length 21 yes. Rows. Need use array of lines. We can embed as JS template with exact lines; ensure backslash? We can use array of strings in JS, with leading? Need no indentation inside strings? We can list each row.

Need solve maze.

Let's map grid coordinates. Need maybe BFS. We'll implement robustly.

Need visual design beautiful. Canvas full window, but maze 21x21. Need draw large and centered. Could compute cell size = min(window dims / (cols+something), etc). But "large and centered". Full window, maintain aspect ratio. Canvas maybe width/height, scale cell to max size with margin. Need maybe draw walls as rounded squares, background dark. Use canvas 2D.

Need animation sequence:

Option 1: Run BFS offline to get visited order and parent. Then animate step by step with setTimeout/requestAnimationFrame. Need display explored cells (visited count) and frontier. During exploration, reveal cells in BFS order. For each step: mark a cell as visited and reveal frontiers. But BFS algorithm can process queue: when popping node, increment explored counter, maybe mark visited. At each animation frame, pop one or multiple until schedule? Need keep within 8-10 sec. Need final path after exploration maybe delay 200ms then draw solution path.

Could animate visited cell light up as front expands. Use BFS where we enqueue S, mark visited? Need show S visited. When process cell, color it. Also draw frontier cells queued (not yet processed) with different color. Need live counter.

Detailed BFS exploration animation:
- Initialize visited boolean grid false; start S visited true, parent null; queue = [S].
- We can at each time step "explore next node": shift from queue; increment exploredCount (if not already? yes).
- Then color node as visited (visited color).
- For each neighbor open, not visited: mark visited, parent set to current, enqueue, color frontier.
- Pause maybe 30-50ms per node. BFS nodes count maybe around ~? Could be 100-200. 100*40=4 seconds. Need total 8-10 incl path. Fine. Use requestAnimationFrame with a time accumulator or recursive setTimeout.

Need perhaps process one node per frame at ~30 fps? Actually requestAnimationFrame ~60fps, if we process one node per frame, 200 frames ~3.3s. Good. But for 8-10 sec, maybe 1 node per 40ms => 200 nodes 8s. But if fewer nodes, path segment? Need use a speed based on open cells count? Alternatively schedule one node per 50ms. Explore maybe 2s? Need "about 8-10 sec total" including path. We can implement adaptive timing.

Could use BFS in generator. At each frame, do k steps? Need dynamic. Simpler: use setInterval every 50ms, one BFS step. But need final path animation. If every 50ms and ~200 nodes, 10 sec maybe too long, but okay? The prompt wants 8-10 sec total. 200*50=10sec plus path 1sec = 11s, slightly over. Use 40ms -> 8 sec plus path maybe 9.5. Need know node count. Let's calculate approximate open cells. 21x21=441, walls likely ~200, open ~240. BFS explores maybe 220. At 30ms/step => 6.6s. At 25ms =>5.5s. Then path 1.5s. Need total ~8. Maybe use 30ms per step. But JS setInterval minimum etc okay. Or use requestAnimationFrame with step interval 33ms. We can process 1 step per 2 frames? Hmm if rAF ~16.7ms, 2 frames=33ms. Could use timestamp-based: nextStepTime += interval; while? Actually if interval 33, each animation frame process accumulated. Could use setTimeout 30ms to draw one node. Might be okay. But if not visible? Need stable.

Alternative animate BFS expansion by cell with CSS? Canvas better.

Need implement "visited cells light up" and "visible frontier". We can draw:
- Walls dark gray.
- Floor with subtle grid/gradient.
- Visited cells maybe fill pale blue/cyan radial gradient.
- Frontier cells fill orange/yellow.
- Start/exit marked with special colors.
- Path: line/trail with glow, maybe gradient white to green/yellow.

Need draw walls exactly as given same walls; rows columns. Need no weird scaling. Use canvas transform to draw entire maze.

Need parse. Need define START and EXIT coordinates:
Row1 col1 = S? Row 1 "#S#.....#...........#": positions: 0 #, 1 S, 2 #, 3 '.', 4 '.', 5 '.', 6 '.', 7 '.', 8 #, 9 '.' ... okay. E row19? Last row has "#...#.......#......E#": Need find E row 19? Wait 21 rows index 0-20. Last row is row20? Let's count prompt rows are 21; row after row19? The line `#...#.......#......E#` is row20 (last). Let's index maybe 20. E at col? `#...#.......#......E#`: after # there are 3 dots cols1-3, # col4, 7 dots cols5-11, # col12, 6 dots cols13-18, E col19, # col20. So E at (20,19). We'll rely BFS finds.

Need expose window.solution array of [row,column] pairs from S to E inclusive. Important 0-based row 0 top line. We can compute final path via parent pointers after BFS. Need assign `window.solution = finalPath`. For animation path show finalPath maybe perhaps include start/end.

Need decide when to reveal path and solution variable. It says show at end length of shortest path in steps. Could path length is steps (number of moves) not cells. "length of shortest path in steps" = path array length - 1. We need display. Could display counter explored cells and final length. Perhaps a HUD overlay with counters.

Need maybe use BFS first to compute `solutionPath`, `visitedOrder`, `frontierAtStep`? We can compute parent. Then animation:
- Generate visited order as list of nodes popped from queue in BFS (excluding maybe start? include start).
- Need parent map for solution. But animation can use a precomputed list of states? Simpler: run BFS, collect `order` and parents. But frontiery changes; can also reconstruct path later. For animation of BFS, we can process queue steps from `order`, and maintain frontier set incrementally. Since `visitedOrder` is order nodes are popped; for each node popped, its unvisited neighbors are discovered and added to queue. To animate frontier as visual state, need maintain `frontier` set. During animation at step i:
  - current node = order[i]
  - It was discovered and placed in frontier at some earlier time (when its parent popped) or start. Remove it from frontier and mark as explored/visited.
  - For each neighbor not visited before discovery, we mark visited immediately (in visited set) and add to frontier. In actual BFS, "visited" prevents duplicates; for animation, if we mark visited when discovered, then when we later pop it, it is already visited. But visual "processing" differs from visited set. Need separate `discovered/visited` for preventing duplicates vs "expanded/explored" for animation. We can use:
    - `discovered` (or "inQueue") boolean true when enqueued, used to prevent duplicates.
    - `expanded` (processed) rendered as "visited cells light up"? But requirement "visited cells light up, with a visible frontier". In search animations, visited cells usually includes processed/discovered. We can color discovered queue cells as frontier, processed cells as visited. Good.
  - At each step: remove current from frontier (if start also); add current to closed/processed. Then for each neighbor, if floor and not discovered: mark discovered, parent = current, add to frontier, enqueue. If E discovered, we could stop? For shortest path, BFS stops when E discovered. Then no need to explore further. But we can still animate remaining frontier? We should stop at exit maybe and then draw path. It can save time. Need if E discovered, mark as frontier maybe then next step? If we stop when E discovered from neighbor, path can be reconstructed from parent pointers to E. But E not processed/expanded. It should be visible. We can process path immediately after current step? Wait if E discovered as neighbor, final path found. But maybe to animate "exit found", we want draw E highlighted and path from S to E. No need to pop E. Parent[E] known. The path includes E discovered. It doesn't require E processed. Good.
- Need if E is discovered at step, set found = true, break loop. The animation should stop exploring and after maybe a small delay draw path. But the requirement says "animate a search algorithm exploring the maze step by step... when exit is found, animate shortest path..." It might be okay to stop exploration when exit is found. But if E is discovered, the front has reach exit. Need path visible shorter? BFS shortest because queue order. We'll stop.

- Need ensure if E is start? Not.

Need live counter of explored cells. What counts explored? Could count number of popped/processed cells (expanded). At end, if E not processed? We can display explored cells as number processed; maybe plus E? Need if final path includes discovered E. "explored cells" likely visited. We can count cells that have been dequeued/processed. At end, when exit found, maybe explored cells count `processedOrder.length`. If E not processed, final path includes E but not counted. Could display +1? Maybe not crucial. Could call counter "Cells explored: N" = number of expanded cells (including S). If E discovered, maybe maybe not. We can decide to include exit in explored? Since in BFS search, you discover E but not expand it. For live counter, maybe count discovered/visited cells, which includes frontier. But "explored cells" ambiguous. Requirement says animate exploration step by step; visited cells light up. If a cell discovered but not expanded, it's frontier. Maybe we can count "explored" as cells popped/visited. Need perhaps display number of cells marked visited (discovered) not expanded? But if path found when E discovered, all frontier cells are discovered but not explored. Hmm.

Maybe design:
- During animation, maintain `exploredCount` = number of cells popped from queue (expanded) and colored as visited.
- Also display `frontierSize` maybe. At end, after path found, maybe add one to exploredCount for E? But if it would be less intuitive. Could instead count "visited" cells as those that have been discovered (including frontier). Then at the final it counts all cells discovered up to E. But animation can update counter as cells light visited/frontier. The prompt "explored cells" probably means visited cells; live counter can just be "cells explored: X" where X increments whenever we add a cell to visited/frontier. But in search, BFS discovers neighbors. The path is found when E discovered; at that time discovered count maybe number of cells explored + frontier. This is acceptable. But if we mark "visited" as discovered, then when popped, they're already colored visited; the visual "explored" doesn't change? Need differentiate.

Maybe implement frontier as "discovered cells", but when processing, change from frontier to explored. Counter maybe count expanded. We can show both "Explored: X" and "Frontier: Y". That's nice. Requirement only asks counter of explored cells, but can include frontier count too. But final path length.

Need maybe final overlay:
- During animation: top-left panel with maze title? Could draw HTML overlay. We can use CSS position fixed with font etc. Full window but no external fonts. Need "beautiful animated visualization" maybe use CSS UI with border, background. Since no external fonts, use monospace or sans-serif.
- At top left: "BFS Maze Solver" and `Explored: 0`, `Frontier: 1`, `Path length: —`. At end: `Explored: N`, `Path length: 42 steps`. Need "live counter of explored cells" maybe use DOM counter.

Need ensure canvas coordinates fit. Use devicePixelRatio for crisp? Yes. Need full window. Use canvas width = window.innerWidth, height = innerHeight. Compute cell = floor(min((width-padding*2)/COLS, (height-padding*2)/ROWS)); offsetX = (width - cell*COLS)/2; offsetY = (height - cell*ROWS)/2. Use square cells. If screen small? cell >= maybe. Use `cell = Math.max(12, Math.floor(...))`. But if tiny, center. Use transform.

Maybe draw animated maze each frame:
- clear background: dark gradient/radial.
- draw walls as filled rounded rectangles with subtle color (#3d4b5c maybe), maybe with inset shadow. Since "beautiful" but needs exact maze. Could draw wall cells as fillRect with a 0.1 gap to show grid. Maybe use `roundRect` if available; if not fillRect. Use `ctx.fillStyle`.
- Draw floors? Could draw all open floor as very dark fill (background). But if walls drawn only, floors represented by dark, not labels. Maybe for visual, draw all cells with dark theme:
  - background: #0f172a.
  - for floor cells, fill with #1e293b maybe and 1px grid? But many cells. With 21x21 = 441, okay. Use instead before walls, fill whole canvas with #0f172a; draw trail as cells; not need fill floor. But to show path movement, draw from center of cells.
  - maybe draw rounded wall blocks: `fillRect(x, y, cell, cell)` with dark slate.
- visited fill: use `rgba(56, 189, 248, 0.45)` maybe, with small inset? E.g., fill `x+1,y+1,w-2,h-2` rounded. Or draw radial gradient.
- frontier fill: `rgba(251, 191, 36, 0.8)` maybe.
- path: draw thick polyline with shadowBlur and color gradient maybe. Since path cells are open cells; use line through centers. Could draw line after visited animation. To create glowing line:
  - lineWidth = cell*0.45, strokeStyle = '#fde047', shadowColor = '#f59e0b', shadowBlur=15? Need maybe multiple passes: outer line wider alpha orange, middle line yellow, inner white.
  - Need draw path after all visited. Path from S to E. Use path array coordinates; convert center to pixel.
  - Maybe animate path growth along the precomputed path using incremental drawing. Requirement "when exit found, animate the SHORTEST path from S to E as a glowing line or trail". We can reveal path segment by segment over ~1.5 sec using `pathProgress` from 0 to 1. Use `requestAnimationFrame`. In final, maybe draw a glowing pulse moving? But not necessary. Maybe line appears gradually.

Need integration: three phases:
1. Exploration phase: a BFS step runs every `STEP_INTERVAL_MS` ms (maybe 28?); each step processes one frontier node; draws visited/frontier and increments explored. At end (when E discovered or queue empty), set `phase = 'path'`; call startPathAnimation().
2. Path animation: over `PATH_DURATION_MS = 1800`, draw path subarray from start to end progress. When done, update solution (already) and final path length, maybe add CSS class highlight.
3. Maybe after path animation, keep drawing. 

Need ensure total ~8-10 seconds. Need decide parameters. Let's estimate BFS explored count and timing. We can precompute `order.length` maybe includes processed cells until E discovered. We can choose `STEP_INTERVAL_MS = max(10, min(80, 6000/order.length))` but if order.length unknown before run? Could compute first. After BFS, know. We can adapt to fit exploration in 6.5 sec. This is nice. Use `explorationBudgetMs = 6500`; `stepInterval = Math.min(80, Math.max(16, explorationBudgetMs / order.length));` But if order.length small, stepInterval can be 80; total maybe 4s if 50 cells? 80*50=4s. Need path 1.8 => 5.8; okay. Use max 60 maybe. If order.length=150, interval=43ms. 150*43=6.45s. Good. If order.length=250, interval=26ms. Fine. Could draw at 60fps via `requestAnimationFrame`, each rAF maybe wait for interval. If interval<16, one step per frame (approx). If interval>=16, schedule with `setTimeout` or timestamp.

Given total 8-10 sec, maybe fixed exploration ~6500ms. Then path 1800ms, total 8300ms + small delay = 8.6. This satisfies. But if exploration interval < 16, rAF process one per frame (~16.7ms) -> 250 nodes = 4.2s not 6.5s. Still under. If interval 20ms, rAF process one ~16.7? with timestamp can ensure. But if interval <16, no need. Let's use `setTimeout` recursion for exploration? It can run in background but okay. Simpler:
```
function scheduleStep(){
  if(phase!=='explore') return;
  setTimeout(() => {
    stepBFS();
    if(stepIndex < order.length) scheduleStep();
    else startPath();
  }, stepIntervalMs);
}
```
Need if tab inactive, timeouts throttled but okay. But need live drawing same step. To draw, call draw at end. Good.
Need compute stepInterval after BFS:
```
const explorationMs = 6500;
const stepIntervalMs = Math.min(70, Math.max(12, explorationMs / order.length));
```
But if stepIntervalMs < 12 maybe set to 12? If order length >540 but maze max 441, min 12. Actually order length max 441, explorationMs/441=14.7; min 12 okay. At 441*14.7=6.48s. Good. If order.length small, max 70 -> 70*? For 70 nodes 4.9s. Fine. If order length 20, 1.4s; paths? Need path maybe 2s; total 3.4s. The prompt says about 8-10 seconds, but if search is tiny? Actually maze fixed, so order likely significant. Need maybe no need. Maybe total can be 8s. But to be safe, set exploration budget = 7000ms, path=2000ms, plus initial delay = 9s. If order.length ~200, interval=35ms => 7s. Good.
Could animate visited cells with "flash" delayed? Not necessary.

Need maybe if path found before exploring all, path immediately. But if explorationBudget formula based on full order until E? We'll compute order until E found. Good.

Need BFS algorithm details:
```
function findSolution() {
 const start = null, end = null;
 for...
 const rows=grid.length, cols=grid[0].length;
 const q = [[sr, sc]];
 const visited = Array.from({length: rows}, ()=>Array(cols).fill(false));
 const parent = Array.from({length: rows}, ()=>Array(cols).fill(null));
 visited[sr][sc] = true;
 const order = []; // processed/expanded order
 let head=0;
 let solution = null;
 while (head < q.length) {
   const [r,c]=q[head++];
   order.push([r,c]);
   if (r===er && c===ec) { solution = reconstruct?; break; } // But if E is start? no.
   for direction:
     nr,nc
     if inside && grid[nr][nc] !== '#' && !visited[nr][nc] {
        visited[nr][nc]=true;
        parent[nr][nc]=[r,c];
        if (nr===er && nc===ec) { // E discovered, maybe prepare
           // don't enqueue? Actually if enqueue then break, q contains E at end, order doesn't include. Need reconstruct.
        }
        q.push([nr,nc]);
     }
 }
 // Note if E discovered as neighbor, we need break immediately and not enqueue? But we already enqueue E. We can set solution and break outer. The order includes current node only. E not in order. The path can be reconstructed.
```
Need be careful with break on E detection. Better:
```
outer:
for (...) {
  const [r,c] = q[head++]; order.push([r,c]);
  ...
  for neighbors {
    if (grid[nr][nc] === '#') continue;
    if (visited[nr][nc]) continue;
    visited[nr][nc] = true;
    parent[nr][nc] = [r,c];
    if (nr===er && nc===ec) { solution = buildPath(parent, er,ec); found at (r,c) maybe; break outer; }
    q.push([nr,nc]);
  }
}
```
But if we set visited before check and don't push E, fine. Since we don't need E in queue. But if E is discovered, BFS doesn't need expand. Good. However for path reconstruction, parent E holds current. Great.
Potential issue: Because we mark visited and then break before adding E to queue, okay.
But what about other neighbors of current maybe order? No matter.
Need maybe `order` contains cells processed until parent of E is processed. Path found when E discovered. The actual discovered E not in order but in path. Good.

Need `parent` as 2D array; starting parent S = null. For path:
```
function buildPath(parent, er, ec) {
 const path = [];
 let cur = [er, ec];
 while (cur) {
  path.push(cur);
  cur = parent[cur[0]][cur[1]];
 }
 path.reverse();
 return path;
}
```
But parent uses arrays; if storing arrays, `parent[r][c] = [r,c]`; fine. Need make sure not to store references that mutate? Arrays okay. Since we never mutate.

But if E is discovered from a neighbor, `parent[E]` set. Path valid. Need `solutionPath` as `[[sr,sc], ..., [er,ec]]`.

Need `visited` in BFS separate from animation. During animation, use `expanded` boolean grid and `frontier` boolean grid? Could use data from BFS path? We can derive order and parent, but to animate frontier at each step, need reconstruct the queue/frontier states. Could precompute for each processed node: discoveredAt? Actually when processing node at order index i, the frontier after step can be replayed using BFS neighbor expansion. We can either compute animation on the fly from grid:
- Maintain `discovered` from BFS? We already need to know which cells are discovered and queued; at step i, process `order[i]`; then expand neighbors as in original BFS. But wait `order` contains all processed nodes until E found; when we process node order[i], we can determine its unexpanded neighbors by checking a `disc` array. We can replay exactly. But because BFS order queue is not stored, we can still expand neighbors for each processed node. At step i:
  - Mark current as expanded/closed.
  - For each neighbor, if open and not yet `disc`, mark disc true, parent set, enqueue, add to frontier. This will generate same order if using BFS. Need if we create order list beforehand with BFS, then when replaying, set `disc` to false and each step expand. But what about nodes already marked discovered by previous steps? Yes they are in `disc`; when popped, they remain disc but should be removed from frontier. We maintain frontier as array/set. Good.
  - At start, S is discovered and in frontier. The step for S: mark S expanded, remove from frontier, then enqueue open neighbors.
  - We need if a neighbor is E, parent set; but in replay, should we detect E and stop after current step? But since order list generated by original BFS and stops when E discovered, after processing order[i], if E got discovered, original broke without enqueuing E. During replay, E may be discovered; but if we stop after current step, order ends. Need if E is not in order. Good. We can simply continue for `order.length` steps. But our `order` includes all processed nodes up until parent of E; after final processed node, if we check its neighbors, we discover E. At this point, we should stop and start path. We don't need to enqueue E in frontier? But for visual, maybe mark E as discovered/frontier? Actually if we discover E as neighbor and then immediately end, the exit should be visible maybe as path origin. We can set `frontierSet.add(E)` only if we need show it as frontier before path. But if path starts immediately after, maybe not. We can leave E unvisited? But path line starts at E eventually. In final, E is drawn special. Need maybe no need.
  - To animate "exit found", we could set a flag and after a short delay draw path. If we add E to frontier, then it would appear as frontier during path animation. But path line will cover it. Could mark E discovered, but not process.
- We need precomputed `order`; on replay at step i, if we expand neighbors, parent arrays can be reconstructed. But we could also precompute `solution` to use for path. We don't need parent during animation except path. But to know E discovery during replay, we can use precomputed `solution` and maybe no need. Need know when to stop exploration. Stop after `order.length` nodes processed. The last expansion discovers E. Good.
- But if original BFS doesn't stop when E discovered? We need decide. It should stop. So order length = number of processed nodes until before E. The parent of E's parent is last processed node. Before processing last node, all earlier nodes processed; E not discovered. When last node processed, neighbors include E; discovered. Then stop. Good.
- Need ensure `order` includes last node before E. Yes.

Could we simplify by not replaying and just animate an array of "states" generated by original BFS including counts? Maybe do the replay with `expanded` state and `frontier`. But we need know at each animation step which cells to add to frontier. We can compute by expanding current node. However, if using precomputed BFS `order` list, we also need ensure neighbors discovered from current are processed later in original queue. The order list is the order of popped nodes; if we expand q sequentially from stored queue? Wait in original BFS, nodes are added to queue and eventually popped. When replaying, if we use only `order`, and expand each node, we will enqueue all neighbors in same order as original BFS. But when we process a node later, its `disc` is already true because previous processed nodes added it. So replay yields same `order`. Good. Need use `disc` grid to avoid duplicates. Need possibly not include all nodes in order? yes.

Let's outline:
```
const order = []; // process order from BFS until solution found
const solutionPath = [];
function runBFS() {
  const sr, sc, er, ec;
  const dr = [[1,0],[-1,0],[0,1],[0,-1]]; // order maybe right/down? Doesn't matter for actual path; shortest if BFS, but frontier visualization. Use up/down/left/right? Requirement no direction. Use directions maybe [up,right,down,left] to have nice pattern? If directions order arbitrary, path still valid. For BFS, path is shortest regardless. Use [up,right,down,left] or [right,down,left,up]? Here start at (1,1), E at bottom-right, so to discover path quicker need directions maybe right/down; but BFS explores all. Use mixed. For visual, a natural BFS might use `[0,1]` etc. Since E at bottom-right, using right/down can find E sooner but still BFS. We can choose directions `[right, down, left, up]`? Need path around walls. Doesn't matter. But if using replay and `order` from original, the `frontier` should match. Use coordinate directions.
  let q = [[sr,sc]];
  let visited = ...
  visited[sr][sc]=true;
  parent[sr][sc]=null;
  let head = 0;
  let found = false;
  while (head < q.length && !found) {
    const [r,c] = q[head++];
    order.push([r,c]);
    for directions {
      nr = r+dr, nc=c+dc;
      if in bounds && !visited[nr][nc] && grid[nr][nc] != '#' {
        visited[nr][nc] = true;
        parent[nr][nc] = [r,c];
        if (nr===er && nc===ec) { // found; no need push.
          found = true;
          break;
        }
        q.push([nr,nc]);
      }
    }
  }
  // reconstruct path from parent
}
```
Wait if using `found=true`, break out of direction loop, but we might have already processed some neighbors. E not pushed. Path parent E set. Then break while. Good. But because we break direction loop with `found` set, the current node's remaining neighbors after E are not explored. That's okay for path. For animation visual, order ends with current node. Replaying current node, we may explore all neighbors including E and maybe other neighbors after E if using same directions? But if we stop after processing order, we don't need to replicate direction loop break condition. If replay expands all neighbors of current node, it might discover extra nodes beyond E that original didn't. But if order ends, those extra may be ignored, but their parent maybe incorrectly if not added. However they remain `disc=false`? Wait in replay, if we expand all neighbors at the last node, we might discover E and maybe other nodes. We don't need process extra. But if we didn't add those extra to frontier due to original? It doesn't matter for visual because exploration stops. But if we don't add E to frontier, and perhaps color other frontier cells that would not have existed in original. But since no further animation, no issue. However, for frontier count at the moment before path, if replay expands all neighbors, it can add more frontier cells than original, which might be confusing. Need replicate exact BFS expansion until E discovery, including not exploring neighbors after E in the direction loop? But the animation likely processes all neighbors of current node at once, including E; if there are other unvisited neighbors after E in the order, they would be discovered too if we expand all. Original would not discover them if E occurred before them. But difference is visual only, path still. Could avoid by precomputing at each step the list of frontiers added? Or by using original BFS states. To be exact, we can run BFS and record events: for each processed node, record the nodes added to frontier (discovered) in that step. Since original stops when E discovered; after E discovered, no more events. At each animation step, use events[i] to add exactly those discovered cells. This is more controlled. Let's do that.

Define BFS with events:
- `events` = array of { expand: [r,c], discovered: [[r,c], ...] }? At each processed node, discovered nodes added (excluding E maybe? We can include E as discovered for visual? Let's include E discovered, maybe as frontier; but if path animation immediately after, okay. But if discovered list includes E and also maybe neighbors after E? We need stop exact.)
- To reconstruct path, if E discovered, we can set parent and stop. The events for current node should include only neighbors discovered before/until E? Let's implement by direction loop:
  - At node current, for each neighbor:
    - if open and not visited:
      - visited[nr][nc] = true
      - parent[nr][nc] = current
      - if E: found = true; break; // Do not enqueue E
      - q.push([nr,nc]); discoveredThisStep.push([nr,nc])
  - After loop, push event `{cell: current, discovered: discoveredThisStep}`. But if E discovered, E should be in discovered? Maybe if found true, we currently didn't push E. For visual, maybe we can add E to `discoveredThisStep` manually? But `events` is for frontier cells that are queued; E is not queued because stop. We could still include E in discovered so it lights up as found? But path animation will render from S to E, maybe not need. But for "visible frontier", after exit found, maybe show path not frontier. Could include E in discovered list; it won't have parent? It does. Then at path phase, E drawn. But if events include E, replay needs not enqueue. The frontier set during final step would include E if we add it; that might show E as frontier then path. Nice. But if we don't include E, E stays special color from static grid? We can draw E always in green; path line covers. Fine.
- Need `events` step order from BFS. If we store `discovered` excluding E, the frontier set after final event matches queue of processed+unprocessed nodes? Let's test:
  Start event? At initialization, S discovered and in queue. Need events[0] with expand S and discovered S's neighbors. But we need initial state before processing S: S is frontier. So set `initialFrontier = [[sr,sc]]`. Then each event expands one frontier node and discovers its unvisited neighbors, adding to frontier. Replaying:
  - Initialize frontier = new Set([S]).
  - For event i: 
    - remove event.expand from frontier.
    - add event.discovered cells to frontier.
    - increment explored.
  This yields at each step frontier after expansion.
  Need if `event.discovered` includes E, should we add? We can add E to frontier and stop; but then frontier at start of path includes E. Fine.
- But if we run BFS and break when E discovered, should we continue generating events? No. The exploration phase ends after the event where E was discovered. The `events` array length = number of processed nodes (order length). Good.
- Need if S is E? no.
- Need if E is discovered as neighbor of some node. Let's code:
```
  const events = [];
  const q = [[sr, sc]];
  const visited = ...;
  visited[sr][sc] = true;
  const parent = ...;
  let head = 0;
  let found = false;
  while (head < q.length && !found) {
    const [r,c] = q[head++];
    const discovered = [];
    for (dir of directions) {
      ...
      if (!visited[nr][nc] && grid[nr][nc] !== '#') {
        visited[nr][nc] = true;
        parent[nr][nc] = [r,c];
        if (nr === er && nc === ec) {
            discovered.push([nr,nc]); // include E in discovered visuals maybe but not queue
            found = true;
            break;
        }
        discovered.push([nr,nc]);
        q.push([nr,nc]);
      }
    }
    events.push({ cell: [r,c], discovered });
    // If found, break outer, but note events last includes discovered E maybe plus previous discovered.
  }
```
But if we include E in discovered list and `found` true, we don't enqueue E, but in replay, we will add E to frontier. Is that okay? If later steps no, so yes. But if we check for E and break before adding to queue, events last discovered might contain E and maybe also other neighbor after E? We break direction loop, so no. Before E maybe discovered other neighbors and pushed them. Fine.
Need reconstruct path: `parent[er][ec]` set; `buildPath(parent, er, ec)`.
Need maybe if E is never discovered? It is, maze solvable. If not, path null. But it is.

Need note BFS visited order and parent: Because we mark E visited and set parent, but do not enqueue. That's fine. Need ensure `parent[E]` set. But if we don't enqueue E, when reconstruct path from E, parent chain won't include E as queue. Fine.

Potential issue: If we stop BFS when E discovered as neighbor of current, is path definitely shortest? Yes, because BFS processes nodes in order of distance from S. When exploring current at distance d, E at distance d+1. Since queue contains nodes at distance d or d+1; any alternate path to E of length d+1? It is found when first discovering E. Good. Need if E is discovered from a node at distance d, all nodes at distance <d processed before, not discovered E? Since E was unvisited, no earlier path. okay.

Need `events` array length: It includes current node even if it discovered E. Number of explored cells = events.length (processed). The requirement asks live counter of explored cells; we can use explored = events processed count. The total explored maybe events.length. But we also discovered E (included in frontier) not processed. If final display shows "Explored: N" where N=events.length, it counts processed cells not E. But many people might consider E explored when path is found even if not processed. But okay? Maybe can define in UI as "BFS expanded" to avoid ambiguity. Requirement specifically "live counter of explored cells", not "expanded". We can count "explored cells" as cells that have been marked as frontier/visited (discovered), which includes both processed and frontier. But then "expanded" maybe different. We can display "Cells explored: N" and maintain count = discovered cells (visited set), including frontiers and E, because that's intuitive (all cells whose state is known). This count can be updated as we discover cells, not when popped. At the end, count = number of distinct cells discovered up to E. Since BFS doesn't process all discovered? Actually each discovered cell except E is eventually in queue; if E found early, many cells discovered are not processed. The UI counter would grow during exploration as frontier grows, which is more meaningful. But the phrase "live counter of explored cells" could be that. Maybe include also "Expanded: X" if wanted. But requirement only explored. To avoid mismatch with visited cells lighting up, we can count `discoveredVisual` as "explored" (discovered). Let's think: In exploration animation, cells become "frontier" as soon as they are discovered. If counter counts processed only, there's a delay: cell lights up as frontier but explored count doesn't increment; then later when popped, counter increments. That's fine. But at end, path found when E discovered but not processed; if counter only counts explored/processed, E's discovery not counted. But displayed final path length more important. Could define "explored" in UI as "cells visited/discovered". Requirement not super strict. Need decide.

Maybe use two counters:
- `Cells explored: <number of cells popped>`
- `Frontier: <number>`
- `Path: —`
At final, after E discovered, if we don't process E, maybe `explored` not include E. But we can choose not to include E because "explored cells" in search algorithms often means expanded from queue. The path length final okay.
But requirement says "show a live counter of explored cells and, at the end, the length of the shortest path in steps." It doesn't mention frontier counter but okay. We can display "Visited: N" maybe count of discovered cells to avoid "Expanded". Yet requirement "explored" maybe use that exact word? Use "Cells explored: N" and count each cell as it is enqueued/discovered. Then in final, N includes E and all frontier. Let's implement this; visually every cell that lights up (frontier or visited) increments count at the moment it's first added. That is easier to understand: "Cells explored" = distinct cells encountered. We can update counter when a cell is added to discovered list in an event. At start, set explored=1 (S). At each event, when replay adds discovered cells, increment explored. But if we process events after initialization, need explore count update accordingly. In draw, when frontier cells added, we can increment? Since `events` list known, in `applyStep`: for each new cell in discovered, if not already in frontier? Actually discovered cells are new; set counter++. This includes E. Good. But what about processing/popping? Counter doesn't increment then. So it counts discovered cells, not processed. We can still use "Explored" because they are explored/discovered. At end, path found, final counter equals distinct explored cells up to stopping condition. Great.
Need if we include E in discovered list, counter includes E. Good.

Need draw frontier counts:
- `frontier` set contains nodes discovered but not yet expanded (plus maybe S). At start, S in frontier, explored=1.
- At event i, we pop/expand `event.cell`: remove from frontier, add cell to `expandedSet` and color as visited. Then for each discovered cell in event.discovered: if not already received? They are new; add to frontier, explored++.
- This matches original: discovered cells become frontier. At next events, some are removed when processed. `frontier.size` is visible.

Need `expandedSet` at end: all events.cell. Does `discovered` include E? If yes, E is frontier at final. ExpandedSet doesn't include E. That's okay. If counter explored = discovered+start, final includes E.

Need path drawing: Use solutionPath. Since path contains S,E. Draw from center of S to E. If path length = N cells, `steps = N-1`. Display `Path: ${steps} steps`. Could animate path from start to end over 1.8s. Use `requestAnimationFrame` with timestamps. At each frame, compute `progress = min(1, (now-startTime)/duration)`. Use `pathLength = Math.floor(progress * (solutionPath.length - 1))` or draw along cumulative segment lengths by progress. Since path cells are adjacent; could increment segment by segment. For smooth line through cell centers, if just draw first `fraction` points with line segments between them, and then from last point to next partial. But for simplicity, can reveal whole cells? But "glowing line or trail" suggests line. We can draw all path with alpha=progress? Or draw polyline from start to current point:
  - Use `endIndex = Math.floor(progress * (solutionPath.length - 1))`; points from 0..endIndex. Draw line. But line jumps segment by segment (if 20 path cells and 60fps, ~33 frames, fine). More smooth: compute `points` from solution up to `endIndex` plus fractional position between endIndex and endIndex+1. Let's do robust:
```
function drawPath(ctx, progress) {
  const pts = solutionPath.map(([r,c]) => center(r,c));
  if (pts.length < 2) return;
  ctx.beginPath();
  ctx.moveTo(pts[0].x, pts[0].y);
  if (progress <= 0) return;
  const totalSegments = pts.length - 1;
  const floatIndex = progress * totalSegments; // e.g., 2.4 means draw segment 0->1,1->2, and 0.4 along 2->3
  const full = Math.floor(floatIndex);
  for (let i=1; i<=full; i++) ctx.lineTo(pts[i].x, pts[i].y);
  if (full < totalSegments) {
     const frac = floatIndex - full;
     const p1=pts[full], p2=pts[full+1];
     ctx.lineTo(p1.x+(p2.x-p1.x)*frac, p1.y+(p2.y-p1.y)*frac);
  }
  ctx.stroke();
}
```
But if full=0 and frac>0, path moves from start toward next. Good.
Need draw path with glow. Use `ctx.lineCap='round', lineJoin='round'`. Multiple passes:
```
ctx.save();
ctx.shadowColor = '#f59e0b'; ctx.shadowBlur = 20;
ctx.strokeStyle = 'rgba(251,191,36,0.9)'; ctx.lineWidth = cell*0.45;
drawPath(ctx, progress);
ctx.shadowBlur = 30; ctx.strokeStyle = '#fde047'; ctx.lineWidth = cell*0.25;
drawPath(ctx, progress);
ctx.shadowBlur = 0; ctx.strokeStyle = '#ffffff'; ctx.lineWidth = cell*0.1;
drawPath(ctx, progress);
ctx.restore();
```
Need not recalc multiple? Fine.

Need draw start/end markers:
- S: maybe at cell center draw `S` text or icon. Since path line covers, but before path, need show start. Use text "S" with dark green circle. End "E" with red/green. The prompt says draw maze as given, so should show S and E characters? It says '#' wall, '.' open, 'S' start, 'E' exit. Need render exact text? We can draw symbols in S/E cells. But if we use path, maybe S/E visible. We can draw letters centered with contrasting colors. The maze as given includes S/E. We should preserve them visually. Use text labels for S and E. Good.

Need exact row/col. Need parse:
```
const mazeText = [
 "#####################",
 ...
];
```
Need avoid special HTML? fine.
Could use template literal:
```
const MAZE = [
  "#####################",
  ...
];
```
Need verify each string has same length. We must be careful in code block: final code file may include backticks? We'll use template literal? Better use array of strings to avoid backtick issues. Also inside code block can contain `<` etc no issue.
Need include `window.solution = solutionPath;` before animation? It says expose final path as global variable `window.solution` array. We can set it right after BFS computes, before animation starts, or at end. It doesn't matter; maybe set `window.solution = null` initially? But expose final path. Should set after BFS, before path animation? It is final. We'll set `window.solution = solutionPath;` immediately. If someone inspects during exploration, final solution already there; okay. Could set after path complete to satisfy "final path"? But global variable always final; not harmful. To be safe, set once computed and mention. But if user wants final path at end, existing global still final. Use `Object.defineProperty(window,'solution',{value: solutionPath, configurable:true});` perhaps? Not needed. Use `window.solution = solutionPath;`.

Need final UI maybe:
HTML:
```
<div id="overlay">
 <div id="title">🌀 Maze BFS</div>
 <div class="stats">
  <span>Explored: <span id="explored">1</span></span>
  <span>Frontier: <span id="frontier">1</span></span>
  <span>Path: <span id="path">—</span></span>
 </div>
</div>
```
Need use emoji? The prompt no external; emoji fine but maybe fonts? It uses default. Could avoid emoji for clean. Use dot? CSS styles maybe no external fonts. Use system font stack.

Need "beautiful animated visualization" perhaps include gradient background, glowing visited cells. Let's plan draw functions:

`drawScene(now)`:
- clear canvas with CSS fill background: maybe background-color in CSS; canvas transparent? Use `ctx.fillStyle = '#0b0f19'; fillRect`.
- Optionally draw a subtle grid pattern background? We can just draw background.
- Calculate `cell`, `ox`, `oy`; if cell not set, draw.
- for each cell:
  - if wall: fill with rounded rect color '#334155', maybe inside a little darker '#1e293b'? Use `fillWall`:
      ```
      const pad = cell*0.08;
      roundRect(ctx, x+pad/2, y+pad/2, cell-pad, cell-pad, cell*0.18); fillStyle = '#3b4a63'
      ```
    But 21x21 wall cells maybe 221, okay.
  - else floor: maybe fill floor color? If not drawing floor, the background showing through; but S/E letters need background. If wall rounded, background dark. But for visited cells, fill with colors. Let's fill open floor with dark color:
      ```
      ctx.fillStyle = '#0f172a';
      ctx.fillRect(x, y, cell, cell);
      ```
      Then maybe draw inner cell border? Not needed.
- Need draw visited/frontier cells:
  - `expandedSet` (processed/visited cells) fill as `cellFill` rounded? Use `ctx.fillStyle='rgba(14,165,233,0.30)'`; draw rounded rect inset `cell*0.08`.
  - Maybe draw visited cell pulse: For all expanded, maybe no animation. Could add slight gradient: Use `createRadialGradient` per cell? That's 200 gradients per frame; okay but perhaps expensive. Simpler: fill with rgba and add inner highlight:
     ```
     ctx.fillStyle = 'rgba(14, 165, 233, 0.35)';
     ctx.beginPath(); roundRect(...); fill();
     ctx.fillStyle = 'rgba(255,255,255,0.06)'; // top highlight?
     ```
  - For frontier cells: fill `rgba(245, 158, 11, 0.75)` with maybe border; rounded. Draw border `strokeStyle='rgba(255,255,255,0.5)'`, lw=1.
  - For current? We can highlight the cell currently being processed as brighter. But if one event per step, the current cell after processing remains expanded. In animation events processed one per interval; perhaps cell is colored as visited at the moment processed. We might want to briefly flash current frontier white/orange. But not necessary. Could include `current` for current event when processed? For beautiful, processed cells light up. Maybe as each node pops, fill white flash then settle? But processing every frame; can't animate per cell over time. We can draw event.cell with a brighter color:
    - expanded colors for all visited
    - current drawing with white fill? If processing at step i, current is now expanded, but should be highlighted. Use `currentCell` variable set to event.cell. Draw current with `rgba(255,255,255,0.5)`.
  - In next step, it will become normal visited.

- Draw path after exploration; path line over visited. It should be after walls and cells. Good.
- Draw S/E labels after path? If path line crosses underlying, but text visible if drawn after path. Draw S/E after path. But if S/E are path endpoints, path line ends at center; drawing label after path will cover. Good.
- Draw labels:
  - For S cell: circle radial? We can draw `#22c55e` circle? But then letter S in same? Since start cell originally S. To preserve, perhaps draw a filled circle dark green at center, draw white S. But the original maze cell S should be visible; overlay circle might obscure. It's okay.
  - For E cell: maybe red/orange circle with white E.
  - But if we draw S and E labels while exploring, path line later maybe goes through. Good.
  - Use `ctx.font = `bold ${Math.max(12, Math.floor(cell*0.55))}px system-ui, sans-serif`; textAlign center, textBaseline middle`.

Need "draw the maze exactly as given (same walls, rows and columns)" Maybe if we draw letters S/E after path, maze still same. Good.

Need maybe HUD:
- `position: fixed; top: 16px; left: 50%; transform: translateX(-50%);` maybe center top, because maze large. Stats maybe top left? The maze centered; overlay top center. Let's design:
  - Top bar with translucent panel: "BFS Maze Solver" small, stats inline. This might cover maze top row? Maze centered and large, maybe top margin. Need not cover walls. Could place top left/right or bottom. Full window, no interaction. Use `top: 12px; left: 50%; transform translateX(-50%);` with flex. It may overlay wall row 0 if margin small. But if cell computed, top offset includes maybe 30px? Need ensure maze not under HUD. Use `paddingTop` when computing cell? If HUD height ~60, we can allocate margins. Or put stats at bottom. To avoid obstruction, compute canvas area with margin for HUD: `const maxW=window.innerWidth; const maxH=window.innerHeight;` use `const topMargin=70; const bottomMargin=40;`; cell = floor(min((maxW-80)/cols,(maxH-topMargin-bottomMargin)/rows)); offsetY = topMargin + (remainingH - cell*rows)/2. This leaves top for HUD. If small screen, still okay. Need HUD fixed top, canvas background. Or do not reserve? Better reserve.
  - Need if window resizes, recalc, redraw. Add resize listener.

Need no interaction except perhaps not needed. "No interaction needed" means auto starts. We don't need buttons. Could still add no clicks.

Need maybe if user loads, `window.solution` should be array of [row,col]. We'll compute.

Potential issue with row strings: Need ensure no trailing spaces. Let's verify each line from prompt. I'll write array carefully. We can count each string length 21. Let's copy list:

0 `"#####################"`
1 `"#S#.....#...........#"`
2 `"#.###.#.#.#.#####.#.#"`
3 `"#...#.#.#.#.....#.#.#"`
4 `"###.#.###...###.#.#.#"`
5 `"#.#.#...#.#...#.#...#"`
6 `"#.#.###.#.#.###.#####"`
7 `"#.#.......#...#.....#"`
8 `"#.#.#.#.#.###.#####.#"`
9 `"#.#.#.#.#.#...#.....#"`
10 `"#.#.#.###.#.###.###.#"`
11 `"#.#.#.#...#.#...#...#"`
12 `"#.#.#.#.###.#.###.###"`
13 `"#...#.......#.#...#.#"`
14 `"#.###.#######...###.#"`
15 `"#.#.....#.....#...#.#"`
16 `"#.#######.#######.#.#"`
17 `"#.#.....#...#...#.#.#"`
18 `"#.#.###.###.#.###.#.#"`
19 `"#...#.......#......E#"`
20 `"#####################"`

Need verify row lengths:
Let's count row1: #(0) S1 #2 .....(3-7) #8 ........... (9-19) #20 -> yes length 21. Wait "..........." after # is 11 dots, yes cols 9-19, so col20 #. Good.
Row4: `###.#.###...###.#.#.#`? Let's count: # # # . # . # # # . . . # # # . # . # . #? Need string `###.#.###...###.#.#.#` length? Positions: 0#,1#,2#,3.,4#,5.,6#,7#,8#,9.,10.,11.,12#,13#,14#,15.,16#,17.,18#,19.,20# => 21. Good.
Row6: `#.#.###.#.#.###.#####` length? # . # . # # # . # . # . # # # . # # # # #? Let's count "#####" at end =5. okay.
Row8: `#.#.#.#.#.###.#####.#` length? 1+1+1+1+1+1+1+1+1? Actually pattern # . # . # . # . # . # # # . # # # # # . # =21. Good.
Row12: `#.#.#.#.###.#.###.###` no trailing #? Wait last string has length? Let's count: #0, .1, #2, .3, #4, .5, #6, .7, #8, .9, #10, #11, #12, .13, #14, .15, #16, #17, #18, .19, #20? Wait `#.#.#.#.###.#.###.###` split: # . # . # . # . # . ### . # . ### . ###? Hmm let's count 21? Let's write indices:
`#.#.#.#.###.#.###.###`
Chars:
0 # 
1 .
2 #
3 .
4 #
5 .
6 #
7 .
8 #
9 .
10 #
11 #
12 #
13 .
14 #
15 .
16 #? Wait after # at 14 maybe? Let's parse carefully.
String: # . # . # . # . # . ### . # . ### . ###? Let's use groups: `#.#.#.#.###.#.###.###`
- "###" at 9-11? Actually pattern: `# . # . # . # . # . ### . # . ### . ###` => length 3+? Let's use indices:
0 #
1 .
2 #
3 .
4 #
5 .
6 #
7 .
8 #
9 .
10 #
11 #
12 #
13 .
14 #
15 .
16 #
17 #
18 #
19 .
20 #? Wait after `#.###.###` there are two `###` separated by dot, but the string ends with `###`? Let's see `#.#.#.#.###.#.###.###` after the second `.` there is `###`, yes. So length:
`#`(0) 
`.`1
`#`2
`.`3
`#`4
`.`5
`#`6
`.`7
`#`8
`.`9
`###` positions 10,11,12
`.`13
`#`14
`.`15
`###` positions 16,17,18
`.`19
`###` positions 20,21,22? That would be >21. Wait maybe there are only two # groups? Need check row12 from prompt: `#.#.#.#.###.#.###.###` perhaps contains 23 characters? But maze supposed 21 cols? Wait perhaps I misread; could be `#.#.#.#.###.#.###.###` length? Let's recount from text:
`#.#.#.#.###.#.###.###`
Maybe there is no dot between the last .? Let's use a method. The string:
# . # . # . # . # . # # # . # . # # # . # # #? No.
Actually BFS row from prompt:
`#.#.#.#.###.#.###.###`
It has 21? Let's count segments:
1. `#` length 1
2. `.` 1 ->2
3. `#` ->3
4. `.` ->4
5. `#` ->5
6. `.` ->6
7. `#` ->7
8. `.` ->8
9. `#` ->9
10. `.` ->10
11. `###` ->13
12. `.` ->14
13. `#` ->15
14. `.` ->16
15. `###` ->19
16. `.` ->20
17. `###` ->23.
But a 21x21 maze row should be 21. Did I copy extra dot? Let's re-read prompt row 12:
`#.#.#.#.###.#.###.###` (21 rows x 21 columns) Wait maybe row length is 21 if some groups are not as I think. Let's look at "###.#.###" maybe? Prompt line 12: `#.#.#.#.###.#.###.###`. There are 4 # groups after? Hmm.

Let's not rely; we need exact maze from prompt. Let's copy exactly each line as in prompt. But if line length >21, canvas maybe handles but row count still 21, columns maybe? Let's count actual characters in prompt raw perhaps? Need ensure all rows 21. Maybe the text formatting wraps? The prompt code block might have lines that appear 21? Let's try to use visible group counts from original:
Line 12 in prompt: `#.#.#.#.###.#.###.###`
Maybe count: 
`#.#.#.#.###.#.###.###`
Break: `#` `.#` repeated? Let's use character by character:
1 # 
2 .
3 #
4 .
5 #
6 .
7 #
8 .
9 #
10 .
11 #
12 #
13 #
14 .
15 #
16 .
17 #
18 #
19 #
20 .
21 #
22 #
23 #? Actually. Hmm.

Maybe the maze isn't 21 columns? But prompt says 21 rows x 21 columns. Need verify every line is exactly 21; maybe I copied row 12 with typo? It should be `#.#.#.#.###.#.###.###` maybe length 21? Let's count using grouping differently: `#.#.#.#.###.#.###.###` has 5 '#' separated by dots? At end `###` after dot. Let's count all '#' = 1+1+1+1+1+3? Wait:
- positions before first `###`: `#.#.#.#.` = 8 chars: # . # . # . # . (4#)
- `###` (3) -> total 11
- `.` ->12
- `#` ->13
- `.` ->14
- `###` ->17
- `.` ->18
- `###` ->21. Ah yes! I miscounted earlier: After `#.#.#.#.` (8 chars) + `###` (3) = 11, + `.` = 12, + `#` =13, + `.` =14, + `###` =17, + `.`=18, + `###`=21. Wait where are 3? Let's group as `#.#.#.#.###` (11 chars? # . # . # . # . # # #? No hold on `#.#.#.#.` ends with dot after 4th #. Then `###` at positions 9,10,11? Let's write indices:
String `#.#.#.#.###.#.###.###`
Take first 5 tokens separated by dots:
- `#`
- `.`
- `#`
- `.`
- `#`
- `.`
- `#`
- `.`
- `###` (??)
Wait because `#.#.#.#.###` are 8 dots? Let's count without quotes:
`# . # . # . # . ###`
Actually `#.#.#.#.###` contains `#` (1) `.` (2) `#` (3) `.` (4) `#` (5) `.` (6) `#` (7) `.` (8) `###` (9-11). Yes length 11. Then `.#.###.###` = `.`(12) `#`(13) `.`(14) `###`(15-17) `.`(18) `###`(19-21). Ah length 21. My previous grouping "###" as position 10-12 was wrong because # at index 9? Let's re-index entire string:
0 # 
1 .
2 #
3 .
4 #
5 .
6 #
7 .
8 #
9 .
10 #
11 #
12 #? Wait if `###` at positions 9-11, then after dot at 12? Let's map:
`#.#.#.#.###.#.###.###`
Let's segment using regex groups:
`#` + `.` + `#` + `.` + `#` + `.` + `#` + `.` + `###` + `.` + `#` + `.` + `###` + `.` + `###`
This is 1+1+1+1+1+1+1+1+3+1+1+1+3+1+3 =22? Let's sum: 1+1=2, +1=3,+1=4,+1=5,+1=6,+1=7,+1=8, +3=11, +1=12, +1=13, +1=14, +3=17, +1=18, +3=21. Ah yes 21! Good. There are 4 single # separated by dots (positions 0,2,4,6), then `###`, dot, single #, dot, `###`, dot, `###`. Good. Row length 21.

Need copy exact.

But wait row12 from prompt `#.#.#.#.###.#.###.###` includes after `###.` single # then `.` then `###` then `.` then `###`; length 21. Good.

Need verify row19 `#...#.......#......E#` length 21? Segment # (1) ... (3) # (1) ....... (7) # (1) ...... (6) E # => 1+3+1+7+1+6+2 =21? Count: #1 + ...3=4, #5, ....... 7 =>12, #13, ......6 =>19, E20, #21. Good.

Need parse each row with `grid[row].length` maybe 21.

Potential issue: The first row "#####..." all walls. Last row same. Good.

Need maybe if BFS events include start? Let's simulate BFS event indexing.

BFS run:
```
const sr=1, sc=1, er=19? Wait row 20, col19? Actually last row row20 E. Need find from grid.
```
In JS:
```
const start = {r:1,c:1}
const end = {r: grid.length-2? no maybe grid.findIndex? Use loop.
```
Need find E index. Last row is index 20; E at col19. But code loop.

Need events:
- visited[sr][sc]=true, parent[sr][sc]=null.
- head=0; q=[S]; while head<q.length:
  - cur=q[head++]; discovered=[];
  - for directions...
  - events.push({cell: cur, discovered});
  - if found break.
But if found E as neighbor of start? Then events include S discovered E. Could path length 2? But maze not.
Need if found E, current node may already have discovered some neighbors before E; they are in discovered and pushed. E in discovered too. Event discovered includes all. In replay, after processing current, we add all zeros, including E, to frontier, then stop. That's okay.
Need if found during direction loop, current's remaining neighbors not checked. Event.discovered won't include them; path stops. Good.
Need if found but no more events. Good.

Need buildSolutionPath:
```
function buildPath(parent, er, ec) {
  const path=[];
  let cur = [er, ec];
  while (cur) {
    path.push(cur);
    const p = parent[cur[0]][cur[1]];
    if (!p) break;
    cur = p;
  }
  path.reverse();
  return path;
}
```
Need parent of S should be null; path includes S if E reaches S. Good. Use while(cur) because parent arrays with [r,c] truthy, parent S null. Need ensure parent stored as array or null; `parent[cur[0]][cur[1]]` is null for S.
Need if using `parent[r][c] = [r,c]`; parent arrays are arrays; okay.

Need maybe if E is not discovered (shouldn't) path empty; but path found.

Now animation state variables:
```
const state = {
  phase: 'idle', // 'explore', 'path', 'done'
  stepIndex: 0,
  exploredCount: 0,
  frontier: new Set(),
  expanded: new Set(),
  current: null,
  pathStart: 0,
  rafId: null,
  timeoutId: null,
  stepIntervalMs: 0,
  solutionPath: [],
}
```
Use `Set` with key `${r},${c}` for frontier, expanded. Need store cell coordinates maybe events store cell arrays; use key helper.

At start:
- `state.explored = new Set()`? For counter, perhaps separate discovered set to avoid counting if duplicate. Use `state.discovered = new Set()`? Since event.discovered are all new, but S initial. Could use `state.frontier`, `state.expanded`, `state.encountered` set? Let's structure:
  - `state.frontier = new Set([S])`
  - `state.expanded = new Set()`
  - `state.exploredCount = 1` (S discovered)
  - `state.discovered = new Set([S])` maybe for adding. Since event.discovered new cells, no duplicates if BFS correct; but we can just increment. Need maybe if discovered includes E after S? no duplicates.
- `stepIndex=0`.
- `state.phase='explore'`.
- `scheduleNextStep()`.

At each event:
```
function applyNextStep() {
  if (state.stepIndex >= events.length) { startPathPhase(); return; }
  const ev = events[state.stepIndex];
  state.stepIndex++;
  // process current: expand cell ev.cell
  const key = cellKey(ev.cell[0], ev.cell[1]);
  if (state.frontier.has(key)) state.frontier.delete(key); else if (state.stepIndex===1? maybe S in frontier)...
  state.expanded.add(key);
  state.current = ev.cell;
  for (const cell of ev.discovered) {
    const k = cellKey(cell[0], cell[1]);
    if (!state.discovered.has(k)) { // safe
      state.discovered.add(k);
      state.frontier.add(k);
      state.exploredCount++;
    }
  }
  updateStats();
  draw();
  if (state.stepIndex >= events.length) {
     // exploration done, schedule path after brief pause
     setTimeout(startPathPhase, 300);
     return;
  }
  timeoutId = setTimeout(applyNextStep, state.stepIntervalMs);
}
```
Need initial exploredCount should include S. In `ev.discovered`, info doesn't include S. Starting count 1 good. But if S discovered then processed first event; state.exploredCount remains 1. At final, count distinct discovered cells incl E. Good.

Need if event.discovered includes E, E added to frontier. Then phase ends after event. Frontier might contain E and other cells. Then path animation; draw will show frontier cells and expanded visited; path line covers. At final done, could keep drawing frontier? Maybe after path done, we can stop updating timer but still draw. It might be okay to keep frontier visible behind path. But after path found, drawing path line covers a route through some frontier cells. We can continue drawing frontier cells that are not covered? They might distract. During path phase, maybe should keep current exploration state and draw; path line drawn on top. After path done, maybe no problem. Could clear frontier colors? Not necessary. But "search algorithm exploring; when exit found, animate path" It might be okay if frontier remains. But perhaps after exploration stops, we can leave path and dim frontier? To look better, as path animates, maybe frontier stays. Good.

Need step interval calculation based on `events.length`.
```
const explorationBudgetMs = 6500;
const stepIntervalMs = Math.max(12, Math.min(80, explorationBudgetMs / events.length));
state.stepIntervalMs = stepIntervalMs;
```
But if `explorationBudgetMs / events.length` > 80 and events small, min 80. Could make exploration > 6.5? maybe less. total maybe okay.
Need if events.length maybe 30, stepInterval=80 => 2.4s exploration, path 1.8 total 4.2. The prompt says about 8-10 seconds. The fixed maze maybe events ~150, stepInterval=43. If events small, maybe shorter. But maybe event count is around 160 -> 6.5s. Good.
Could increase min to 90 but total still maybe not 8 if events 100? 100*65=6.5. Fine. Since we want about 8-10, set `explorationBudgetMs = 6500`; path 2200; initial/end pauses 300 = 9.0. Step interval maybe less than actual due rAF? We'll use `setTimeout`, so okay. If events length 150, 43ms; 150*43=6.45s +0.3 +2.2 +0.3=9.25. If events length 200, 32.5*200=6.5 +2.8=9.3. Actually path=1.8, pause=0.3 total 8.9. Good.
Need `setTimeout` minimum maybe 12. If events length 400, 16.25ms; 400*16.25=6.5. Fine.
Could maybe if window not visible timeouts throttled; no concern.

Need canvas program:
```
const canvas = document.getElementById('maze');
const ctx = canvas.getContext('2d');
let cell=30, ox=0, oy=0;

function resize() {
  const top = 90, bottom = 40;
  const availH = window.innerHeight - top - bottom;
  const cellSize = Math.max(12, Math.floor(Math.min((window.innerWidth - 40)/COLS, availH/ROWS)));
  canvas.width = window.innerWidth * dpr? ... // Use CSS? We can set canvas.width = innerWidth, height=innerHeight, then no dpr? For crisp, use dpr.
}
```
Need set DPR:
```
function resize() {
  dpr = window.devicePixelRatio||1;
  canvas.width = window.innerWidth * dpr;
  canvas.height = window.innerHeight * dpr;
  canvas.style.width = window.innerWidth + 'px';
  canvas.style.height = window.innerHeight + 'px';
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  cell = Math.max(10, Math.floor(Math.min((window.innerWidth - 40)/COLS, (window.innerHeight - HUD_TOP - 30)/ROWS)));
  ox = (window.innerWidth - cell*COLS)/2;
  oy = HUD_TOP + (window.innerHeight - HUD_TOP - 30 - cell*ROWS)/2;
  draw();
}
```
But `canvas.height` resets context; setTransform after. Need if no `ctx`, etc.
Use `HUD_TOP` maybe 76. But if `availH` negative, Math.max(10). But okay.
`roundRect` function:
```
function roundRect(x,y,w,h,r) { 
 const rr = Math.min(r, w/2, h/2);
 ctx.beginPath();
 ctx.moveTo(x+rr, y);
 ctx.arcTo(x+w,y,x+w,y+h,rr);
 ...
 ctx.closePath();
}
```
But need pass `ctx`? Use global.

Draw walls:
```
function drawMaze() {
  for r rows for c:
   if grid[r][c]==='#':
     const x=ox+c*cell, y=oy+r*cell;
     ctx.fillStyle = '#1e2a3a';
     roundRect(x+1, y+1, cell-2, cell-2, Math.max(2, cell*0.12));
     ctx.fill();
     ctx.fillStyle = 'rgba(255,255,255,0.06)';
     roundRect(x+cell*0.18, y+cell*0.18, cell*0.62, cell*0.62, Math.max(1, cell*0.08));
     ctx.fill();
   } else {
     ctx.fillStyle = 'rgba(255,255,255,0.04)'; // subtle floor
     roundRect(x+1,y+1,cell-2,cell-2, cell*0.08);
     ctx.fill();
   }
}
```
But if floor fill with rgba on dark background, okay. We may not need fill all floor because background dark. But using subtle floor helps see cells.
Need if we draw floor fill before visited; visited on top.

Maybe define `drawCellFill(r,c,color,inset)`. Use rounded rect.

Visited: `roundRect(x+cell*0.12, y+cell*0.12, cell*0.76, cell*0.76, cell*0.18)` fill with rgba. Frontier: `roundRect(x+cell*0.08, y+cell*0.08, cell*0.84, cell*0.84, cell*0.2)` fill with orange; maybe add small pulse? Can animate using `now/300` to change alpha? Could create a "breathing" frontier:
```
const pulse = 0.75 + 0.25 * Math.sin(now/300);
ctx.fillStyle = `rgba(251, 191, 36, ${0.65+pulse*0.15})`;
```
Need not; but draw() called only on events/time, not continuous unless path. During exploration, draw at 30fps but not continuous between events. If `stepInterval` is 40ms, fine. Could use `requestAnimationFrame` for path phase only. Not needed.

Potential issue: During exploration, using `setTimeout` to draw, but if we also have `requestAnimationFrame` not running, canvas updates on each timeout. Good.
At path phase, startPathPhase:
```
state.phase='path';
state.pathStart = performance.now();
requestAnimationFrame(function drawPath(now){...});
```
During path, `draw` should include path progress.

Need `draw(now)`:
```
function draw(now) {
 if (!ctx) return;
 ctx.clearRect(0,0, innerWidth, innerHeight);
 // background gradient
 const bg = ctx.createLinearGradient(0,0,0, innerHeight);
 bg.addColorStop(0,'#0b1020'); bg.addColorStop(1,'#0f172a');
 ctx.fillStyle=bg; ctx.fillRect(0,0, innerWidth, innerHeight);
 drawMaze();
 // visited cells
 for (const key of state.expanded) { ... }
 // frontier cells
 for (const key of state.frontier) { ... }
 // maybe current cell white overlay
 if (state.current) { ... }
 // path if state.phase === 'path'||state.phase==='done' draw with progress
 if (state.solutionPath.length) { ... }
 drawStartEnd();
}
```
Need `drawMaze` should iterate all cells. Since 21x21, okay.
Need `drawCell` with string key; parse key to r,c:
```
function parseKey(k){ const [r,c]=k.split(',').map(Number); return [r,c]; }
```
Better iterate over Set entries arrays? Fine.

Need path drawing while exploration? `solutionPath` known from start. We shouldn't draw path during exploration. Could maybe not show path until phase path. If phase explore, path progress null; draw no path. Good.

Need draw S/E labels:
```
const sc = start; // maybe array [r,c]?
function cellCenter(r,c) {
 return {x: ox + (c + 0.5) * cell, y: oy + (r + 0.5) * cell};
}
function drawStartEnd() {
 ctx.font = `bold ${Math.max(10, Math.floor(cell*0.5))}px system-ui, sans-serif`;
 ctx.textAlign='center'; ctx.textBaseline='middle';
 // Start
 const s = cellCenter(sr,sc);
 ctx.fillStyle = 'rgba(34,197,94,0.15)'; ctx.beginPath(); ctx.arc(s.x,s.y, cell*0.38,0,2*PI); ctx.fill();
 ctx.fillStyle = '#4ade80'; ctx.font...; ctx.fillText('S', s.x, s.y+1);
 // End
 const e = cellCenter(er,ec);
 ctx.fillStyle = 'rgba(239,68,68,0.15)'; ctx.beginPath(); ctx.arc(e.x,e.y, cell*0.38,0,2*PI); ctx.fill();
 ctx.fillStyle = '#f87171'; ctx.fillText('E', e.x, e.y+1);
}
```
Maybe if cellSize small, text too big. Use `Math.max(10, cell*0.55)`. If cell 20, text 11. okay.
Potential problem: Path line drawn before S/E, so S/E visible.
Need maybe during path animation, path line passes under labels; good.

Need maybe after path done, show "Path: N steps" in stats. At final, maybe add class to `overlay`? no.

Need `updateStats()`:
```
function updateStats() {
 document.getElementById('explored').textContent = state.exploredCount;
 document.getElementById('frontier').textContent = state.frontier.size;
 if (state.phase==='path'||state.phase==='done') document.getElementById('path').textContent = state.solutionPath.length-1 + ' steps';
}
```
At path start, set path text to `${states}` immediately. If path length unknown until solution, but already computed. During exploration show `—`. At start path, update path. But requirement says at the end show length; could show while path draws. Fine.

Need final when path animation complete:
```
function finishPath() {
 state.phase='done';
 document.getElementById('path').textContent = `${steps} steps`;
 updateStats();
 draw(performance.now());
}
```
Need maybe `state.phase='done'` to avoid drawing path progress with staleness. In draw, if phase done, progress = 1.

Need `startPathPhase`:
```
state.phase='path';
state.pathStart=performance.now();
state.pathProgress=0;
function drawPathFrame(now) {
  const t = Math.min(1, (now - state.pathStart) / PATH_DURATION_MS);
  state.pathProgress = t;
  updateStats();
  draw(now);
  if (t < 1) {
    state.rafId=requestAnimationFrame(drawPathFrame);
  } else {
    state.pathProgress=1;
    state.phase='done';
    updateStats();
    draw(now);
  }
}
state.rafId=requestAnimationFrame(drawPathFrame);
```
Need maybe path line from start to end with progress. `draw` calls drawPath with state.pathProgress if phase path. If done, progress=1. Initially if to set state.pathProgress maybe 0.
Need if window resizes during path, no issue.

Need maybe if exploration phase had a `setTimeout` scheduled, and user resizes; okay. Need store timeout ID to avoid multiple. We'll use `state.timeoutId`.
Need maybe if `document.hidden` causes timeouts delayed and `performance.now` path start relative to state.pathStart; if hidden, path jumps when visible. Fine.

Need perhaps use `requestAnimationFrame` to drive exploration instead of `setTimeout` for smoother transitions. Could use timestamp and step accumulator; but `setTimeout` simpler. If stepInterval ~30ms, update stats and draw at that rate. Fine.

Need "live counter of explored cells" will update.

Need edge case `events.length === 0` if start is end, not; no.

Need if `state.exploredCount` uses `state.discovered.size`; initial S included. If `ev.discovered` includes cells already discovered due to bug, we check; maybe update.
Maybe include E in `frontier` then later path animation; frontier.size display includes E. If user sees `Frontier: 1` at final? Actually many frontier cells remain. The final frontier size is number of discovered but unprocessed cells at stop. This is correct; not all cells explored. If we want the maze to look fully explored before path, perhaps not. But BFS stops when E discovered; there may be many frontiers. That's standard. The UI "Frontier" may be non-zero. Fine.

Need maybe if we include E in frontier, path line draws over E and frontier orange remains. Could remove E from frontier before path? Since E is discovered but not to be processed. If leave, at end E letter + orange border maybe okay. Maybe better not include E in frontier because E is not really in queue; but if we want frontier count accurate to BFS queue, E would not be enqueued. However if we include E in frontier, it might imply queued, but not processed. Since no further processing, visual okay. To be safe with BFS correctness, perhaps don't include E in frontier. But then explored count should count E? It can count E as discovered though not queued. The frontier should represent queued but unprocessed nodes; E isn't queued because we stop. If path is found, no future processing, but many visualizations mark E as found. We can toggle a special flag. But not necessary.

Maybe better: Events discovered list excludes E; after exploration, maybe set a special `eFound=true`. The path animation starts from S to E. This is more faithful to BFS (E not enqueued). But `frontier` set then won't show E; The E cell stays static red/green. The path line will reveal it. This is fine. The counter can include E? If `discovered` excludes E, exploredCount maybe misses E. Is it okay? At final maybe explored count is number of cells enqueued (not including E). Hmm.

Alternative: Include E in `discovered` for counter but not in frontier set? Use separate discovered set and frontier set:
```
state.discovered.add(E) => exploredCount++
if E not push to frontier (since not enqueue)
```
Then final frontier doesn't include E. This seems good. How to implement? In BFS events, we need know which discovered cells are queued vs E. Could include a `queued` flag for each discovered? Simpler: In replay, if cell equals E, add to `state.discovered`, increment, but don't add to `state.frontier`. But if solution path found, path. Is there any need to add E to frontier? No. The path animation uses solution. Let's implement:
```
for (const cell of ev.discovered) {
  const k=cellKey(cell);
  if (state.discovered.has(k)) continue;
  state.discovered.add(k);
  state.exploredCount++;
  if (cell[0] !== end[0] || cell[1] !== end[1]) {
      state.frontier.add(k);
  }
  if (cell[0]===end[0]&&cell[1]===end[1]) state.endFound=true;
}
```
But if E not in frontier, `frontier.size` excludes E. Good. However if original BFS discovered other cells after E? It breaks, so none. Good.
Need if E is discovered, `ev.discovered` includes E and maybe other cells before it. Those before are added to frontier. E not.
But if E is in `discovered` and not added to frontier, then frontier count is exact to queue (E not queued). good.

Need how to make BFS events include E in discovered? In `runBFS`, in direction loop when found E:
```
if (nr===er && nc===ec) {
  discovered.push([nr,nc]); // include for counter
  found = true;
  break;
}
```
No q.push. Good.
Need if found before reaching end? yes.

Need in animation replay, when processing event, we iterate `ev.discovered`. Some of those cells may be E; we add to discovered count but not frontier.

But `state.discovered` includes E; if in a later event (there is none) discovered E no duplicate. okay.

Need `events` event.discovered includes all neighbors that were newly discovered for current event, not necessarily queued? Yes includes E if found. Need note if another new neighbor after E wasn't checked due to break, not included. good.

Need if E is adjacent to S and first direction order visits some neighbor before E; they will be discovered and queued before finding E. path still.

Need maybe if found E and discovered list includes E but also some neighbors before E; those are queued. Good.

Need if start is adjacent to end? no.

Need the BFS path: Because we break when E discovered as neighbor, did we set `parent` for E. Yes.
But note in BFS, we set `visited[nr][nc] = true` before checking E. If E found, not enqueued. That's okay; queue doesn't need E.
Need if multiple nodes can find E? Only first, because visited true. good.

Need maybe `events.push` after direction loop; if found, events includes current and E discovered. Good. However if E discovered from current, we don't push current to queue? current already was popped from q; q includes current. yes.

Need `order` events length = number of processed nodes, including current. Does the BFS while loop need process E? No. We stop after processing current, which found E. Actually we cannot know E until current processed. So order includes current. Good.

Need if E is found from S by checking neighbors, events length 1. Fine.

Need step interval formula should maybe based on events.length+? no.

Need `drawMaze` reads grid; maybe should draw S/E cells after all cell fills but before path? We will draw S/E labels at end. When exploring, S/E labels visible. Good.
Need maybe `drawMaze` fills floor for all open cells, including S/E. We can include `if grid[r][c]=='S'||'E'` but grid only has '#' and maybe '.'? Actually parse stores original char? We can store `grid` as strings, so `grid[r][c]` returns '#', '.', 'S', 'E'. We should treat S/E as open. In BFS, `grid[r][c] !== '#'` for S/E. In drawMaze, if `grid[r][c] !== '#'` fill floor. Good.
Need maybe we use original string grid; `grid[er][ec]` is E, `grid[sr][sc]` S. Good.

Need should we preserve `.`? We don't draw dots individually. Draw maze as symbols? The prompt says draw maze as given maybe means use cells; letters for S/E. Not needed to draw dots. Good.

Potential issue in `drawMaze`, if we fill all non-# cells with subtle white; S/E also. good.

Need maybe if visited/frontier drawn after floor before walls? We draw walls and floor together, then visited/frontier on top. That means wall cells are not visited. Fine.
Need if visited/frontier fill rounded rect but not cover entire cell, there is floor edge visible. Good.

Need maybe draw path with line under S/E labels but over visited/frontier. yes.

Need maybe if path goes through walls? It shouldn't; path line through open cells. Good.

Need maybe if path line across cell centers crosses walls diagonally? Since path moves between adjacent cell centers; if adjacent cells open, segment lies within open cells, no wall crossing. Fine. But if line segment from center to center crosses a wall between? They are adjacent open cells, so line through their shared edge, no wall. Good.

Need maybe if path line uses `lineWidth = cell*0.45`, it could cover walls if cell width large? It passes through centers of adjacent cells; the line stays mostly within cells. It may cover some wall corners, but okay.

Need maybe draw path before S/E labels but after frontier. yes.

Need maybe if state.phase='explore', pathProgress remains 0; draw doesn't call drawPath. Need if step phase set 'path' but pathProgress maybe 0. Good.

Need update stats at initialization:
```
updateStats(); draw();
```
Need if `events` computed synchronously, start animation after setting state. If grid parsing fast, no problem.

Need maybe overlay with title "Maze BFS" and stats. Use CSS:
```
body { margin:0; overflow:hidden; background:#0b0f19; font-family: ...; }
#maze { position: fixed; inset: 0; }
#hud { position: fixed; top: 14px; left: 50%; transform: translateX(-50%); display:flex; gap:12px; align-items:center; flex-wrap:wrap; background: rgba(10,15,30,0.75); border:1px solid rgba(255,255,255,0.08); padding:10px 18px; border-radius:16px; backdrop-filter: blur(8px); color:#e2e8f0; font-size:14px; z-index:10; box-shadow:0 8px 30px rgba(0,0,0,0.4);}
#hud .title { font-weight:700; letter-spacing:.5px; }
#hud .sep { width:1px; height:24px; background: rgba(255,255,255,0.15);}
#hud .stat {white-space:nowrap;}
#hud .stat b { color:#93c5fd; font-weight:600; }
```
Stats:
```
<div class="title">BFS Maze</div>
<div class="sep"></div>
<div class="stat">Explored <b id="explored">1</b></div>
<div class="stat">Frontier <b id="frontier">1</b></div>
<div class="stat">Path <b id="path">—</b></div>
```
Need no emoji. Good.
Maybe use `(max-width: 700px)` overlay small; but no need. Use flex-wrap.

Need if HUD at top, we reserved top margin. In resize, HUD_TOP = 70; okay.
Need maybe if screen very small, HUD wraps, but okay.

Need perhaps allow `draw()` update stats? no, separate.

Need maybe start path animation using `requestAnimationFrame`, but if we use `setTimeout` for exploration and then `requestAnimationFrame`, the `now` param in event draw perhaps. Good.

Need maybe after path done, no more animation, but if window resize, draw will draw with `state.pathProgress` maybe 1. Good.

Need perhaps `window.addEventListener('resize', resize);` but if drawing, `resize` inside. Fine.
Need maybe if state.phase === 'path', `resize` should not disrupt path animation? It just draws with current progress; path frame next frame will redraw. okay.

Need maybe if user calls `draw()` before grid parsed? no.

Potential issue: Because `events` contains discovered cells and E, but BFS not adding E to queue; however in replay, when it processes current event, if E is in discovered, it increments explored and marks endFound. But what about other events before final that discover E? none. Good.
Need maybe if a discovered cell is E but also if `frontier.add(k)` not happening, path phase starts. The current event may have also discovered other cells after? No break before after E? Wait if E discovered, we break out of direction loop. That means if it is the 2nd direction, cells after E in the direction order are not checked. So discovered only E and earlier directions. Good.

Need maybe for frontier count, at final, some cells are in frontier and expanded. Fine.

Need perhaps animate "cells explored" as distinct cells discovered. At start, explored=1. At event, discovered list may include E; counter increments. Good.
Need maybe if discovered cell E and also before E have other frontiers, counter increments. Good.

Need maybe path line should use `solutionPath` which is computed regardless; but during exploration we don't draw it. okay.

Need maybe `drawMaze` fill floor for S/E cells with rgba white; if we later draw S/E circle, okay. But if grid char is 'S' or 'E', drawMaze will draw floor; no grid letters except S/E labels. If `drawMaze` called before drawStartEnd, labels are after.
Need maybe if `drawMaze` fills floor with rounded rect for every '.' and 'S','E'. Good.
Need maybe if we have many rounded rects in draw called every frame; 21x21=441 cells, okay.

Need maybe if using `ctx.roundRect` not supported in all browsers; implement custom. We can use native if available:
```
function roundRectPath(x,y,w,h,r) { ... }
```
Use `ctx.arcTo`. Good.

Need maybe if cell = 10, rounded radius small; okay.

Need maybe if `ox`/`oy` not integer? Use Math.floor in resize to avoid blurry/alignment. Set `cell=Math.floor(...)`, `ox=Math.floor((width-cell*cols)/2)`, `oy=Math.floor(...)`. Since dpr set, coordinates in CSS pixels; okay.
Need `canvas.width = innerWidth * dpr` but in resize we set transform; draw uses CSS pixel coordinates. good.

Detailed draw code plan:

```
const PI = Math.PI;
function roundRect(x,y,w,h,r){
  r = Math.min(r, w/2, h/2);
  ctx.beginPath();
  ctx.moveTo(x+r, y);
  ctx.arcTo(x+w,y,x+w,y+h,r);
  ctx.arcTo(x+w,y+h,x,y+h,r);
  ctx.arcTo(x,y+h,x,y,r);
  ctx.arcTo(x,y,x+w,y,r);
  ctx.closePath();
}
function fillCell(r,c,color,pad=0.1){
  if (cell<2*pad) return;
  roundRect(ox+c*cell+pad, oy+r*cell+pad, cell-2*pad, cell-2*pad, Math.max(0, cell*0.2));
  ctx.fillStyle=color; ctx.fill();
}
function drawMaze(){
 for r...
  if (grid[r][c]==='#'){
    const x=ox+c*cell, y=oy+r*cell;
    roundRect(x+0.5,y+0.5,cell-1,cell-1, cell*0.15);
    ctx.fillStyle='#1d293d'; ctx.fill();
    roundRect(x+cell*0.22, y+cell*0.22, cell*0.56, cell*0.56, cell*0.12);
    ctx.fillStyle='rgba(255,255,255,0.05)'; ctx.fill();
  } else {
    roundRect(x+0.5, y+0.5, cell-1, cell-1, cell*0.12);
    ctx.fillStyle='rgba(255,255,255,0.035)'; ctx.fill();
  }
}
```
But if grid char is '#', line could be "####". Good.
Maybe draw a border around maze:
```
roundRect(ox-4, oy-4, cols*cell+8, rows*cell+8, 12); ctx.strokeStyle='rgba(255,255,255,0.08)'; lineWidth=1; stroke();
```
not needed.

Need draw visited/frontier:
```
function drawOverlay(now){
 const pulse = now? 1+0.3*Math.sin(now/400):1;
 for (const k of state.expanded) { const [r,c]=parseKey(k); fillCell(r,c,'rgba(2,132,199,0.4)', cell*0.12); }
 for (const k of state.frontier) { const [r,c]=parseKey(k); fillCell(r,c,'rgba(234,88,12,0.6)' , cell*0.08); }
 if (state.current) { const [r,c]=state.current; fillCell(r,c,'rgba(255,255,255,0.25)', cell*0.15); }
}
```
Need maybe frontier pulse:
```
if (now) {
 const a = 0.55 + 0.15*Math.sin(now/250);
 fillCell(r,c, `rgba(249,115,22,${a})`, cell*0.06);
} else ...
```
But if we redraw at path animation 60fps, frontier pulses. During exploration, now from timeout not passed? We can call `draw(performance.now())`. Good.

Need `drawPath(progress, now)`:
```
function drawSolution() {
 if (!solutionPath || solutionPath.length < 2) return;
 const t = state.phase === 'done' ? 1 : (state.phase === 'path' ? state.pathProgress : 0);
 if (t <= 0) return;
 ctx.save();
 ctx.lineCap='round'; ctx.lineJoin='round';
 const pts = solutionPath.map(([r,c])=>cellCenter(r,c));
 const total = pts.length - 1;
 const floatIdx = Math.max(0, Math.min(total, t * total));
 const full = Math.min(total, Math.floor(floatIdx));
 const frac = floatIdx - full;
 ctx.beginPath(); ctx.moveTo(pts[0].x, pts[0].y);
 for (let i=1; i<=full; i++) ctx.lineTo(pts[i].x, pts[i].y);
 if (full < total && frac > 0) {
   const p1=pts[full], p2=pts[full+1];
   ctx.lineTo(p1.x + (p2.x-p1.x)*frac, p1.y + (p2.y-p1.y)*frac);
 }
 ctx.shadowColor='rgba(250,204,21,0.9)';
 ctx.shadowBlur=16;
 ctx.strokeStyle='rgba(250,204,21,0.85)';
 ctx.lineWidth=Math.max(2, cell*0.42);
 ctx.stroke();
 ctx.shadowBlur=0;
 ctx.strokeStyle='rgba(255,255,255,0.9)';
 ctx.lineWidth=Math.max(1, cell*0.12);
 ctx.stroke();
 ctx.restore();
}
```
Need if `floatIdx == total` and full == total, frac=0, no partial.
Need if `full` currently is index of last full segment; `lineTo` from 0 to full. For t=0.6, total=10, floatIdx=6, full=6, frac=0; path draws 10? Actually 0 to 6 = 6 segments, leaving segments 7-10. Good.
Need if `full=0, frac>0`, path is from start to partial in segment 0-1.

Need perhaps draw a dot/marker at current partial endpoint? Not necessary.
Need maybe draw "head" circle at endpoint:
```
if (t<1) {
 const p = pointAlongPath(t)
 ctx.beginPath(); arc(p.x,p.y, cell*0.2, ...); fill('rgba(254,240,138,0.9)');
}
```
Could be nice but not needed. We can draw a white circle at the head to show search? maybe. Since glowing line already.

Need if path line drawn with shadowBlur and `ctx.stroke()` multiple times; if using `ctx.shadowBlur` and `stroke()` a path, okay.

Need maybe if state.phase === 'done', `state.pathProgress=1`; no animation.
Need maybe if `state.phase === 'path'`, draw with state.pathProgress. In path animation, `drawPathFrame(now)` sets state.pathProgress before draw. Good.

Need maybe if path animation complete, set `state.phase='done'`; in `draw`, pathProgress=1. no further draws unless resize. Good.

Need maybe if during exploration, `state.phase='explore'`, pathProgress maybe 0; `drawSolution` t=0. Good.

Need maybe if `grid[r][c]` for walls and draw path label; yes.

Need maybe if `ctx.font` with `bold` and size maybe, if cell too small but okay.

Need maybe if `window.devicePixelRatio` changes due zoom, resize.

Need maybe include `resize` call immediately:
```
resize();
```
But before that, parse grid and events? Draw needs events? We can compute grid, BFS before resize? It doesn't matter. However `drawMaze` uses `grid` global. Need define grid before first draw. We can compute after DOM loaded? script at end of body, so DOM ready. Good.
We'll place `<script>` before `</body>` but after HTML. The canvas element exists. Good.

Need maybe code structure:
```
const MAZE_TEXT = [...];
const GRID = MAZE_TEXT.map(row => row.split('')); // But then draw uses char? if split, can't use `grid[r][c]`? yes.
```
Actually if we store grid as array of strings, `grid[r].charAt(c)` maybe. Better store as array of strings, use `grid[r][c]` (string immutable but okay). But BFS checks char; if we use `grid[r].charAt(c)`, no issue. Use `const grid = MAZE_TEXT;` But for S/E find, use `grid[r][c]`.
If we use array of strings, `grid[r][c]` works in JS returns char (not assignment). Good.
Need maybe parse `const rows=grid.length, cols=grid[0].length`.
Need find start/end:
```
let start=null,end=null;
for r: for c:
 if(grid[r][c]==='S') start=[r,c];
 if(grid[r][c]==='E') end=[r,c];
```
Need `isOpen`:
```
function isOpen(r,c) {
 return r>=0 && r<rows && c>=0 && c<cols && grid[r][c] !== '#';
}
```
S/E not '#'. Good.

Need maybe set `window.solution = [];` initially? Not needed.
Need maybe if `document.getElementById('explored')` maybe path; okay.

Potential issue: The BFS events discovered list includes cells that are new; but if event.discovered includes E, `state.discovered` count includes E. But `state.frontier.size` from Set excludes E. Yet in `events` array, E discovered in event; if no future event processes E, and if there were another event? There isn't because phase stops. okay.
Need maybe `state.discovered` set includes start; if starting event discovered includes S? no. Good.
Need maybe if event.discovered includes a cell that is also in event.discovered twice? no.
Need maybe if a cell discovered in an event is E, but `state.discovered` includes it; if there are future events (there aren't) but if code were to process more, E would remain not in frontier. That's fine.
Need maybe update `state.exploredCount = state.discovered.size` rather than increment. We can just do `state.exploredCount = state.discovered.size`. Since state.discovered is Set. We can initialize with S:
```
state.discovered = new Set([key(S)]); state.exploredCount = 1;
...
state.discovered.add(k); state.exploredCount = state.discovered.size;
```
Use size as source of truth. That avoids miscount. Good.
Need if discovered E not added to frontier, still in discovered set. Great.

Need maybe if `state.frontier` uses cell keys; parse for drawing.

Need `applyNextStep`:
```
function applyNextStep(now) {
  if (state.phase !== 'explore') return;
  if (state.stepIndex >= events.length) { finishExplore(); return; }
  const ev = events[state.stepIndex];
  state.stepIndex++;
  const curKey = cellKey(ev.cell[0], ev.cell[1]);
  state.frontier.delete(curKey);
  state.expanded.add(curKey);
  state.current = ev.cell;
  for (const cell of ev.discovered) {
    const k = cellKey(cell[0], cell[1]);
    if (!state.discovered.has(k)) {
      state.discovered.add(k);
      if (cell[0] !== end[0] || cell[1] !== end[1]) state.frontier.add(k);
    }
  }
  state.exploredCount = state.discovered.size;
  updateStats();
  draw(now || performance.now());
  if (state.stepIndex >= events.length) {
    state.timeoutId = setTimeout(finishExplore, 350);
  } else {
    state.timeoutId = setTimeout(() => applyNextStep(performance.now()), stepIntervalMs);
  }
}
```
Need note if event.discovered includes E and we don't add E to frontier; but what about S start? state.frontier starts with S. At first event (which is likely S), it removes S and expands S, discovering neighbors. Good. If stepIndex=0, current key S in frontier, remove. Good.
Need if events[0].cell is not S? BFS events first event current = first q item = S. yes.
Need if `state.frontier.delete(curKey)` returns false maybe if key not in set? Shouldn't. If not, expanded still add. okay.
Need if current is E? No because events stops before processing E. Good.

Need if after final event, `state.frontier` doesn't include E (if E discovered final). But might include other cells. okay.
Need finishExplore:
```
function finishExplore() {
  state.phase='path';
  state.pathStart=performance.now();
  updateStats();
  state.rafId = requestAnimationFrame(drawPathFrame);
}
```
Need maybe if `requestAnimationFrame` not available? It is.
Need drawPathFrame:
```
function drawPathFrame(now) {
  const progress = Math.min(1, (now - state.pathStart)/PATH_DURATION);
  state.pathProgress = progress;
  updateStats();
  draw(now);
  if (progress < 1) {
    state.rafId = requestAnimationFrame(drawPathFrame);
  } else {
    state.phase='done';
    state.pathProgress=1;
    updateStats();
    draw(now);
  }
}
```
Need if user resizes, state.rafId maybe still previous; fine.
Need if path animation already running and resize calls draw, no issue.

Need maybe if finishExplore is called and state.rafId already existing? no.

Need maybe if user closes tab, okay.

Need maybe in HUD path text shows "—" during exploration, then at path start maybe `Path: N steps`. In drawPathFrame, updateStats only when phase path/done. At path phase first frame progress may 0, it sets path text. Actually `finishExplore` sets state.phase='path'; updateStats before first frame; path text set. Good.
Need updateStats:
```
function updateStats() {
  document.getElementById('explored').textContent = state.exploredCount;
  document.getElementById('frontier').textContent = state.frontier.size;
  if (state.phase === 'path' || state.phase === 'done') {
    document.getElementById('path').textContent = (solutionPath.length - 1) + ' steps';
  }
}
```
Need `solutionPath` defined before updateStats called. yes.
Need if path length < 2, maybe no. But maze path length >.

Need maybe if path animation done, path label maybe "N steps" not "—". good.

Potential issue: We use `performance.now()` for pathStart. The `requestAnimationFrame` callback's `now` is same time origin (DOMHighResTimeStamp). Good.
Use `let` for functions global. fine.

Need maybe if `state.phase==='done'`, `draw` should no longer update if raf not continuing. good.

Need maybe if `state.pathProgress` not defined before resize. It will default undefined; draw t uses `state.pathProgress || 0`. In draw, we can set `const t = state.phase==='done' ? 1 : (state.phase==='path' ? state.pathProgress : 0);` If undefined, 0.
Need maybe if state.phase === 'path' and state.pathProgress undefined at first path draw? finish sets before. okay.

Need perhaps `drawOverlay(now)` uses `now` maybe performance.now, but if undefined, use 0. For pulse:
```
function drawOverlay(now=0) {...}
```
Need maybe `draw()` call with no args from resize; `performance.now()` not passed, but for pulse use `now||0`.
Use `function draw(now) { const time = now || 0; }`.

Need maybe in drawPathFrame, after setting state.pathProgress, updateStats and draw(now). In draw, frontier pulse uses `now`; good.

Need perhaps if exploration uses `draw(performance.now())` and pulse changes even between events? yes.

Need maybe if `events` array large, start after BFS. Need compute stepInterval once:
```
const STEP_MS = Math.max(12, Math.min(90, 6500 / events.length));
```
Maybe add slight randomness? no.

Need maybe if events.length is 0, no path? but not.

Need maybe if path includes S/E, but BFS doesn't process E; path parent chain from E to S should be complete because when E discovered, parent set. We need in BFS when discovering neighbor E, set parent. But we also don't enqueue E. Since no need to enqueue. Good.
BFS neighbor loop:
```
for (const [dr,dc] of DIRS) {
 nr...
 if open && !visited[nr][nc]:
   visited...
   parent[nr][nc]=[r,c];
   if target E { found=true; discovered.push([nr,nc]); return? }
   discovered.push([nr,nc]);
   q.push([nr,nc]);
}
```
Need careful: We need `discovered` array for event includes all newly discovered neighbors, including E. If E found, break out of directions, but what about other neighbors after E in this same event? Since BFS order could matter? We can break, leaving some neighbors unexplored visually. But for BFS correctness, if we break early on finding E, we don't check remaining directions for this node. Since we don't need to continue BFS once E found, that's okay for path but the visualization event.discovered won't show those unexamined neighbors. But are those unexamined neighbors maybe the same as discovered from other nodes later? We stop BFS entirely. This is fine for a `BFS` that returns when E found. However if some directions after E in this node could discover E faster? E already found; no need. But if path length maybe; first discovered E is shortest because BFS processes nodes in order. If we skip remaining directions of current node, path to E remains E discovered from current; Is it possible current node reaches E in a direction after the first E check, and that direction was processed after? Actually we process directions in order; the first time we encounter an open unvisited neighbor that is E, we break. The remaining directions might contain another E neighbor? There's only one E cell, so no. They might contain other cells that are not needed for path. Since BFS stops, okay.
Need if E is discovered, should we still push earlier discovered neighbors to event.discovered before breaking? yes, they are in discovered array. Good.

Need if not found E, loop all directions, discovered includes all new open neighbors. Parent set.

Need in BFS, `found` variable must stop while loop. If found inside neighbor loop, set `found=true`, then break out of neighbor loop. But if we break out of neighbor loop manually using a label? We can use `let found=false; outer: while(q.length && !found) { ... for directions { if E { found=true; discovered.push(...); break outer; } ... } events.push(...); }` Needs to push event even if found? We should push after direction loop, but if found, direction loop breaks early. We still need to push event for current with `discovered` list. So structure:
```
while (q.length && !found) {
 const cur=q.shift();
 const discovered=[];
 for (dirs) {
   ...
   if (!visited[nr][nc]) {
      visited...
      parent...
      if (isEnd) { found=true; discovered.push([nr,nc]); break dirLoop? }
      discovered.push([nr,nc]);
      q.push([nr,nc]);
   }
 }
 events.push({cell: cur, discovered});
}
```
Need use a labeled block to break out of for-of but still after for execute events.push. Could use `let endDiscover = false;` and check in loop:
```
for (...) {
  ...
  if (isEnd) { discovered.push([nr,nc]); found = true; break; }
  ...
}
events.push(...);
```
Since break just breaks for loop, after break events.push executes. That works. After break, events.push still runs. Good.
Need no need to check `!found` in for after found? break exits for. Then events.push with discovered includes E. While condition `while(q.length && !found)` stops next iteration. Good.
Need if found E, we don't push E and don't enqueue. Good.

Need need to mark `parent[nr][nc]` before E check? We set for E; yes. But if E is target, we don't need parent? Actually path needs parent E. So set parent before if E. Good. But if E is target and we set `found=true`, we still should set visited and parent. In code:
```
if (!visited[nr][nc]) {
  visited[nr][nc]=true;
  parent[nr][nc]=cur;
  discovered.push([nr,nc]);
  if (isEnd) { found=true; break; }
  q.push([nr,nc]);
}
```
Need push E to discovered before break. Good.
Need parent for E set; path builds.

Need if found E, `events.push({cell:cur, discovered})` where discovered includes E and any prior neighbors of cur. E will be added to `state.discovered` but not to `state.frontier` because `isEnd`. Good.
Need if found E, we do not push E to q. Good.

Need if found E from start? events first has discovered includes E but start not added to frontier? Wait first event is S; state.frontier initially has S; applyNextStep deletes S from frontier and expands. In discovered list, if E found, E not in q; state.discovered add E; frontier doesn't add E. good.
Need if found E from non-start, similar.

Need maybe path length computed from parent includes E and starts at S. Since parent of E set to cur (discovered from cur). good.

Need maybe if BFS didn't find E (should not), solutionPath empty. But no.

Need maybe if grid char includes 'S' and 'E' in maze, drawMaze floors them; okay.

Need maybe if start/end global arrays:
```
const start = {r:...,c:...}? 
```
Use arrays? We can use arrays [row,col]. parent keys maybe. For simplicity:
```
let startCoords = [1,1]; let endCoords = [20,19];
```
But find dynamically:
```
let startRC=[], endRC=[];
...
```
Use `startRC[0]`, etc.

Need maybe if row counts. good.

Need maybe if no events? not.

Potential issue in BFS event discovered list contains only newly visited nodes, but we add current cell? no. In visualization, expanded includes current; discovered include new neighbors. Good.
Need maybe if a neighbor is already in queue but not yet expanded (visited true when enqueued), we don't add again. Good.

Need maybe if path line traces through cells that may still be in frontier (not expanded) because BFS stops when it discovers E, not when it expands E. The path is shortest from E to S via parents, which are all expanded or start. Good.

Potential issue with `state.discovered` includes E and other frontier cells; `state.frontier.size` doesn't include E. updateStats frontier maybe count less than if counted E; okay.
Need maybe `state.exploredCount` includes E even though E never dequeued, but "Explored" maybe "Discovered" more accurate. HUD label could be "Discovered" instead. The prompt no exact. Use "Seen" or "Visited". To avoid confusion, use "Seen" and "Queued". But "Explored" is okay. Maybe label "Discovered" to reflect count includes E. Use HUD stat "Discovered". Actually `state.exploredCount` counts distinct cells that have been discovered (enqueued or E). Good. HUD "Seen" more accurate. Use "Seen" and "Frontier". Let's label `Seen`. Good.
Need maybe path label "Path" okay.

Need maybe if path animation complete, maybe set `state.frontier` remains; HUD frontier size still shown. Good.

Need maybe "No interaction needed" perhaps after path done, still no controls. Good.

Let's consider if grid row 12 copy exact. Need ensure line 12: `#.#.#.#.###.#.###.###` yes. In code, remember there is `.` after `###` before `#`. Good.
Need maybe line 5 `#.#.#...#.#...#.#...#` yes? Prompt: `#.#.#...#.#...#.#...#` Wait row5 from prompt: `#.#.#...#.#...#.#...#`? Let's scroll: line 5 `#.#.#...#.#...#.#...#`? Actually prompt:
`#.#.#...#.#...#.#...#`? Let's re-read from prompt at top:
```
#.#.#...#.#...#.#...#
```
Wait no, line 5 in prompt: `#.#.#...#.#...#.#...#`? I copied as `#.#.#...#.#...#.#...#`? Let's look at code copy earlier:
5 `"#.#.#...#.#...#.#...#"`? I wrote `"#.#.#...#.#...#.#...#"` maybe? Wait line 5 from prompt: `#.#.#...#.#...#.#...#`? Need check. It might be `#.#.#...#.#...#.#...#` with 3 dots? Let's re-read the prompt from user:
```
#.#.#...#.#...#.#...#
```
Actually I need check. The full prompt lines:
```
#S#.....#...........#
#.###.#.#.#.#####.#.#
#...#.#.#.#.....#.#.#
###.#.###...###.#.#.#
#.#.#...#.#...#.#...#
#.#.###.#.#.###.#####
#.#.......#...#.....#
#.#.#.#.#.###.#####.#
...
```
Wait line 5 might be `#.#.#...#.#...#.#...#`? Let's not guess; I need ensure each line copied exactly from user. In the initial prompt, row5 is:
`#.#.#...#.#...#.#...#`? Actually I wrote in my initial code:
`"#.#.#...#.#...#.#...#"`? Let's scroll to my array at top:
`"#.#.#...#.#...#.#...#"`? I wrote `"#.#.#...#.#...#.#...#"`? Let's see my line 5 earlier: `#.#.#...#.#...#.#...#`? I copied: `#.#.#...#.#...#.#...#`? Wait I wrote:
5 `"#.#.#...#.#...#.#...#"`? The visible in my message from earlier: `"#.#.#...#.#...#.#...#"`? Let's scroll to my code block:
```
`#.#.#...#.#...#.#...#`
```
I see line 5: `#.#.#...#.#...#.#...#`? In code block earlier line 5 appears `#.#.#...#.#...#.#...#`? Not sure.

Let's revisit user's maze:
```
#.#.#...#.#...#.#...#
```
Wait the user line 5 from original:
`#.#.#...#.#...#.#...#`
Need count: 
- `#`
- `.`
- `#`
- `.`
- `#`
- `.`
- `#`
- `.`
- `.`
- `.`
- `#`
- `.`
- `#`
- `.`
- `.`
- `.`
- `#`
- `.`
- `#`
- `.`
- `.`
- `.`? Hmm.

Original prompt:
```
#.#.#...#.#...#.#...#
```
Let me copy from user message at top:
```
#.#.#...#.#...#.#...#
```
I see after `#.#.#` maybe `...#.#...#.#...#`? Let's just trust the code block I wrote? Wait I am an AI, I cannot see screen; I need ensure consistency. The user's maze is a 21x21 grid. My code should copy exactly. I wrote earlier line 5 as `#.#.#...#.#...#.#...#` maybe from memory. Let's inspect my earlier code block: In the array, line 5:
`"#.#.#...#.#...#.#...#"`? The actual text I typed at top is `"#.#.#...#.#...#.#...#"`? Scroll: `"#.#.#...#.#...#.#...#"`? It says line 5 `#.#.#...#.#...#.#...#`? I can't see, but I can infer from known maze? The row likely `#.#.#...#.#...#.#...#`? Let's count if length 21:
`#`1 `.`2 `#`3 `.`4 `#`5 `...`6-8? Wait the string `#.#.#...#.#...#.#...#` length maybe 21? Let's count with segments: # . # . # . . . # . # . . . # . # . . . #? That is 21? 1+1+1+1+1+3+1+1+1+3+1+1+1+3+1? Hmm. Let's actually reconstruct from original if row 5 was `#.#.#...#.#...#.#...#`. It has `#...#` maybe. Not crucial? Wait yes, if any row mismatched, maze display off but still BFS. User expects exact but maybe okay if copied. I want to ensure I use exactly the user's text. Since I can't visually inspect my own pasted code, maybe I should copy the original from the user into a code block now. Let's scroll to the top of the user message if I can in this conversation? The user message is:
```
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
#####################
```
Actually the original row 5 is `#.#.#...#.#...#.#...#`? Wait in the original quoted, line 5 is `#.#.#...#.#...#.#...#`? Let's look at the user message in the prompt: 
```
#.#.#...#.#...#.#...#
```
Hmm.

Let's use the text I just pasted from user message? The prompt at the beginning of this conversation contains:
```
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
#####################
```
Wait this is from the prompt at the top of the current message? I included it? Yes, user message block is:
```
#S#.....#...........#
#.###.#.#.#.#####.#.#
#...#.#.#.#.....#.#.#
###.#.###...###.#.#.#
#.#.#...#.#...#.#...#
...
```
So line 5 `#.#.#...#.#...#.#...#` maybe because the message shows `#.#.#...#.#...#.#...#`? Let's look at line in quote: `#.#.#...#.#...#.#...#`? The line in the prompt from user:
`#.#.#...#.#...#.#...#`? It says:
`#.#.#...#.#...#.#...#`? I can see from the beginning of this answer in the user text: 
`#.#.#...#.#...#.#...#` no.
Let's count with the string I see in the prompt (I am reading the text in the user's question that I quoted above):
Row 5: `#.#.#...#.#...#.#...#`? Actually the line as pasted in prompt:
`#.#.#...#.#...#.#...#` maybe 21? Could be.
I think my earlier code block from memory is correct enough. But for safety, I should use the exact lines from the user message. I can copy them into a `MAZE_TEXT` array in the code answer. Since I'm generating the final answer, I can copy from the visible initial user message. Let's use the exact text from the user message as I see it at top of this conversation and not my memory. But as an AI, I see the user message; I can reproduce it. Let me isolate the user message:
```
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
#####################
```
This list has 22 lines? Let's count: The first row `#S#...` is line 1, the second `#.###...` line2, etc. The row `###.#.###...###.#.#.#` is line4. Total lines in the user's block? It might be 21 rows if first/last walls. Let's count the lines above:
1 `#S#.....#...........#`
2 `#.###.#.#.#.#####.#.#`
3 `#...#.#.#.#.....#.#.#`
4 `###.#.###...###.#.#.#`
5 `#.#.#...#.#...#.#...#`
6 `#.#.###.#.#.###.#####`
7 `#.#.......#...#.....#`
8 `#.#.#.#.#.###.#####.#`
9 `#.#.#.#.#.#...#.....#`
10 `#.#.#.###.#.###.###.#`
11 `#.#.#.#...#.#...#...#`
12 `#.#.#.#.###.#.###.###`
13 `#...#.......#.#...#.#`
14 `#.###.#######...###.#`
15 `#.#.....#.....#...#.#`
16 `#.#######.#######.#.#`
17 `#.#.....#...#...#.#.#`
18 `#.#.###.###.#.###.#.#`
19 `#...#.......#......E#`
20 `#####################`
Only 20? Need 21 rows. Wait maybe the prompt says 21 rows, but this visible block has 20 rows because first row `#S#` maybe line 1, last row line 20 is all #. Hmm original actually has 21? Let's count carefully from the user message I see:
```
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
#####################
```
That's 20 rows. But the prompt says 21 rows x 21 columns. Did I omit a row? Let's count the lines in the original user prompt again: at the top of this answer, the user message code block contains:
```
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
#####################
```
Maybe there are 20 because row 0 `#S#` has 16? Let's count columns in first row `#S#.....#...........#`: # + S + # + 5 dots + # + 11 dots + #? That's 1+1+1+5+1+11+1=21. Yes row length 21. But 20 rows. Did the prompt originally have an extra row after line 12? Let's count rows from the original text in the prompt: maybe line `#.#.#.#.###.#.###.###` and line `#...#.......#.#...#.#` are rows 13 and 14, etc. 20 rows total? Let's count in prompt:
1 #S#...
2 #.###.
3 #...#.
4 ###.#.
5 #.#.#...
6 #.#.###.
7 #.#.....
8 #.#.#.#.
9 #.#.#.#.
10 #.#.#.##
11 #.#.#.#.
12 #.#.#.#.
13 #...#...
14 #.###.##
15 #.#.....
16 #.######
17 #.#.....
18 #.#.###.
19 #...#...
20 #########
This is 20, unless I omitted a row. But user says 21x21; maybe there's an extra row not visible? Wait maybe because I counted line `#.#.#.#.#.#...#.....#` etc. Let's look at last rows:
```
#.#.....#.....#...#.#
#.#######.#######.#.#
#.#.....#...#...#.#.#
#.#.###.###.#.###.#.#
#...#.......#......E#
#####################
```
That's 5 rows, and earlier 15 rows =20. Did the original 21x21 maze maybe had a row `#.#.#.#...#.#...#.....#` etc. Hmm.

Actually this is okay: If the user's grid has 20 rows, the code will still work for any size. The prompt said 21 rows but maybe there are actually 20 lines due to monospacing? Wait maybe row 1 `#S#.....#...........#` contains S at row 1 (index 1) if 0-based? yes. The bottom `#####################` row index 19. That's 20 rows. 21x21 would need another row. But maybe the first line "21x21" not in user text; user just provided the maze. Doesn't matter for algorithm. The code copies exactly; BFS adapts ROWS=20. But if expected 21, missing row perhaps? Let's inspect code block in the user message at the very top of this conversation: It is:
```
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
#####################
```
I count 20 lines. The prompt only provided 20 lines. So the maze is 20x21. But they said 21x21; maybe I miscounted and there are 21 lines because line `#S#.....#...........#` has 21 chars but maybe the first line at row 0 and the last all # at row 20 count 21? Let's count again using a script mentally:
1 `#S#.....#...........#`
2 `#.###.#.#.#.#####.#.#`
3 `#...#.#.#.#.....#.#.#`
4 `###.#.###...###.#.#.#`
5 `#.#.#...#.#...#.#...#`
6 `#.#.###.#.#.###.#####`
7 `#.#.......#...#.....#`
8 `#.#.#.#.#.###.#####.#`
9 `#.#.#.#.#.#...#.....#`
10 `#.#.#.###.#.###.###.#`
11 `#.#.#.#...#.#...#...#`
12 `#.#.#.#.###.#.###.###`
13 `#...#.......#.#...#.#`
14 `#.###.#######...###.#`
15 `#.#.....#.....#...#.#`
16 `#.#######.#######.#.#`
17 `#.#.....#...#...#.#.#`
18 `#.#.###.###.#.###.#.#`
19 `#...#.......#......E#`
20 `#####################`
That's 20 rows. The user's prompt maybe had 21 rows? Wait, maybe the first line `#S#.....#...........#` and the second line `#.###.#.#.#.#####.#.#` are 21 rows if I missed a line `#...#...#...#...#...#`? Not important; the code will handle any maze.

Need ensure the final answer includes the same maze text as the user, exactly. Since copying from earlier code block in this answer? I'll include the lines exactly as I see in the user message. If I include 20 rows, the code works with 20. If the user expected 21, but copied from prompt, okay.

But my previous code block at top of final answer maybe should mirror the user's visible lines. Let's use the lines from the user message as I can see:
```
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
```
This is 20 rows. Good.

Need maybe if `grid` is 20x21, start index S at row0 col1. `endCoords` at row18 col20? Let's find E: row18 (0-based) `#...#.......#......E#`; E at col? maybe 21. Good.

Need maybe if end row is last open row, path.

Need maybe if grid has no walls? no.

Need maybe if starting at row0, but typical start/end on borders; BFS expands. Good.

Potential issue: If start row is 0, `startCoords` at [0,1]. fine.
Need maybe if cell size = floor((innerHeight - 110)/20) maybe. Good.

Need maybe if the maze has 20 rows but window height small; okay.

Need maybe if HUD_TOP = 70, for 20 rows and cell maybe 30, oy. fine.

Need maybe if `document.body` margin 0, canvas position fixed. Good.

Need maybe if path maybe very long; path animation duration perhaps 2200 ms regardless. okay.

Need maybe if we use `state.discovered` / `state.frontier` Sets with string keys; parse in draw. To avoid parse every time, we can store `Map` key->[r,c], but Set okay.

Need maybe if `state.current` is array [r,c]. When drawing current, we could instead use key of expanded last, but okay.
Need maybe if `state.current` should remain at last expanded during path; yes.

Need maybe if frontier pulse uses `now`, but if `draw` called from resize with `undefined`, use 0.

Let's think about final answer structure: Provide full HTML with script. Need include comments maybe concise. Need make sure no unescaped HTML in JS? no.
Need maybe if using `<script>` inside HTML and includes `</script>`? no.
Need maybe if code block includes the maze strings exactly. Good.

Potential issue in `drawMaze`: It draws floor for every non-wall cell, including cells that are also filled by visited/frontier. But `fillCell` for visited/frontier also draws. Good.
Need maybe in `drawMaze`, if char is '#' or not, for grid char maybe `S` and `E`. Good.
Need maybe if `grid[r][c]` = 'S' or 'E'. yes.

Need maybe if `state.frontier` includes start key before first event. At first update, draw frontier includes S. Then first event deletes S. Good.

Need maybe if `events[0].discovered` includes neighbors but state.frontier also contains S until first event. okay.

Need maybe if path animation starts and `state.frontier` still includes some cells; path line drawn on top. Good.

Need maybe if all frontier cells are expanded? No because BFS stops early; some frontier. HUD shows.

Need maybe if we draw expanded cells with blue and frontier with orange; path line yellow; start/end green/red. Good.

Need maybe if `state.phase` after path done remains `'done'`; draw called on resize. Good.

Need maybe if after path done, updateStats path text already set. Good.

Need maybe if user scrolls? body overflow hidden, no scroll. okay.

Need maybe if in final answer, using "Seen" stat label, the HUD initial value 1. Good.

Let's refine draw code:

```
function draw(now) {
  resize? not call; draw assumes canvas sized. 
  ctx.clearRect(0,0,window.innerWidth,window.innerHeight);
  const time = now || 0;
  // background
  const grad = ctx.createLinearGradient(0,0,0,window.innerHeight);
  grad.addColorStop(0,'#0b1020');
  grad.addColorStop(1,'#0f172a');
  ctx.fillStyle=grad;
  ctx.fillRect(0,0,window.innerWidth,window.innerHeight);

  drawMaze();
  drawSearchOverlay(time);
  if (state.phase==='path'||state.phase==='done') drawSolution(state.phase==='done'?1:state.pathProgress||0);
  drawStartEnd();
}
```
Need if `drawSolution` uses `ctx.save`/restore.

Need `drawSearchOverlay` should draw expanded before frontier so frontier on top. Current maybe draw white on top of frontier? maybe draw current overlay last. If current is a cell that was expanded; draw current after expanded and frontier. okay. But current may be in expanded; draw current as white overlay on top, making it lighter. good.

Need `fillCell` uses `ctx.fillStyle` and fill; likely okay.

Need implement `drawMaze` using `ctx.strokeStyle` maybe for grid cell borders:
```
ctx.strokeStyle='rgba(255,255,255,0.04)';
for walls/floor? maybe no.
```
Not necessary.

Potential issue: In `drawMaze`, `roundRect` uses `ctx.arcTo`; if `x` etc float; fine.

Need maybe if canvas context is destroyed by resize; `ctx` variable remains object; after reset, setTransform. okay.

Need maybe if `resize()` called before `ctx` assigned? We'll define `const canvas`, `const ctx = canvas.getContext('2d')`; then `resize` uses ctx. can't be called before script defines. Script at end after canvas; okay.

Need maybe if `window.innerWidth` includes scrollbar? body overflow hidden, no scrollbar. Good.

Need maybe if `HUD_TOP` and `BOTTOM` are constants:
```
const TOP = 74;
const BOTTOM = 28;
```
In resize:
```
const availW = Math.max(100, window.innerWidth - 24);
const availH = Math.max(100, window.innerHeight - TOP - BOTTOM);
cell = Math.max(8, Math.floor(Math.min(availW/COLS, availH/ROWS)));
ox = Math.floor((window.innerWidth - COLS*cell)/2);
oy = Math.floor(TOP + (availH - ROWS*cell)/2);
```
Need maybe if cell=0? Math.max ensures 8 but if window too small, maybe maze overflows; okay.
Need maybe set `cell` before use in first draw. yes.

Need maybe if `drawMaze` uses `cell` variable declared `let cell=20;` globally. good.

Need maybe if path animation `drawPathFrame` uses `performance.now()` and sets state.pathProgress. In drawPathFrame, after `draw(now)`, if progress >=1, state.phase='done'; but draw was called with progress=1, good. If we set phase to done before draw, draw uses phase done; either.

Need maybe if path duration 2200; for long path maybe okay. Add `PATH_MS = 2400;`

Need perhaps if solution path very long, path line animation from start to end but "BFS" ended; okay.

Need maybe if start cell and end cell have walls between, path fine.

Let's write final code.

Before final, consider if `grid` row strings contain `#` and maybe `E`; in `drawMaze`, if grid char not '#', draw floor; but if grid char '#' for wall. good.
Need if `drawMaze` draws over path? no, before path. Good.
Need if `drawStartEnd` draws circles over path? yes after path. If path line extends under start/end circles labels, labels visible. Good.
Need if cell small, circles maybe big; fine.

Potential issue: In `drawSolution`, when `floatIdx` is a float and `full` = min(total, floor(floatIdx)); if floatIdx = 0, full=0 frac=0; if total=0, path just start. no.
Need if state.pathProgress = undefined when phase done? no.
Need if `lineWidth = Math.max(2, cell*0.4)`; good.
Need `ctx.shadowBlur=18` maybe high; okay.

Need maybe if `roundRect` uses `ctx.closePath` and then fill, okay.

Need maybe if `fillCell` with `pad = cell*0.08` when cell = 8, pad 0.64; okay.
Need maybe if cell very small, `cell*0.2` rounding; fine.

Let's include `state.pathProgress = 0` initial.

Need maybe if after `drawMaze`, `drawSearchOverlay` iterates over state.frontier. If state.frontier has start key and S is start; draw orange. good.

Need maybe if `state.current` initially null; `drawSearchOverlay` handles. good.

Need maybe if `events` discovered list includes start? no.
Need maybe if `state.discovered` uses Set and `state.exploredCount` maybe integer. Good.

Need maybe if `document.getElementById` values maybe; stats update after elements exist; script at end. good.

Let's now produce final answer with full HTML.