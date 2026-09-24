Let me build a single-file HTML canvas battle simulation.

Key requirements:
- 2 armies, ≥500 units each (1000 total)
- Red vs blue
- Charging at each other across a field, top-down with slight perspective
- Units move toward nearest enemy, fight on contact, lose health, die with blood/dust puff
- Formations break into chaos
- Live survivor counters per side
- Title with battle name
- Winner celebrates, then restart with new battle
- Smooth, spatial partitioning (uniform grid)
- Auto-start, no interaction
- Everything important within 30s

Design:

Canvas full window. Use a world coordinate system with perspective transform: y maps to screen with foreshortening. Let's define world as x in [0, W], y in [0, D] (depth). Screen: perspective scale = f(y) e.g. scale = 1 + (y/D)*0.6... Actually "slight perspective" from above — farther away (smaller y) appear smaller and higher on screen.

Let me map: worldY from 0 (far) to D (near). scale(y) = lerp(0.75, 1.25, y/D). screenX = cx + (x - W/2) * scale. screenY = horizon + ... Let's do a simple projection: 

screenY = topY + (y/D)^1.0 * fieldHeight ... with scale affecting things.

Simpler: use a projection where screen y depends on world y nonlinearly to give perspective: 
t = y / D (0 far, 1 near)
sy = horizonY + (1 - 1/(1 + k*t))/... hmm, keep it simple.

Let's use: scale = 1 / (1 + p*(1 - t)) something. Actually a classic: camera at height h above plane, looking down at angle. Points at depth y project as:

sy = horizon + C / (y + d0), scale = C' / (y + d0).

That gives proper perspective. Let's set world depth y ∈ [0, D] where y=0 is far (near horizon), y=D near. Then sy = horizonY + K/(y + y0), scale = K2/(y+y0).

Pick: horizonY = H*0.18. For y=0 (far edge): scale should be small, sy close to horizonY. For y=D: scale big, sy near bottom.

Let d = y + d0, with d0 = 600, D = 2400 → d from 600 to 3000.
scale = F/d with F chosen so scale at y=D (d=3000) = 1.25 → F = 3750. At y=0 (d=600) scale = 6.25. Too much variation. Let's reduce: d0 = 1800, D = 2400 → d 1800..4200. scale = F/d, F = 4200*1.25 = 5250 → at far, scale = 5250/1800 = 2.9. Still 2.3x variation. That's fine actually for "slight perspective"? Maybe too much. Let's use d0 = 3000, D = 2400 → d 3000..5400, ratio 1.8. scale far = F/3000, near = F/5400. Set near scale = 1.3 → F = 7020 → far scale = 2.34. Hmm, far things bigger? No — wait I inverted.

Let me redo. Far should be smaller. With sy = horizon + K/d, larger d → closer to horizon and smaller scale. So near (y=D) should have small d. So d = (D - y) + d0. y=D → d = d0 (small, near, large scale). y=0 → d = D + d0 (large, far, small scale).

So: d = (D - y) + d0. scale = F/d. Let's set d0 = 2000, D = 3000 → d from 2000 (near) to 5000 (far). ratio 2.5. Slight-ish. Let's do d0=2500, D=2500 → d 2500..5000, ratio 2.

scale = F/d, want near scale ~1.15 → F = 1.15*2500 = 2875. Far scale = 2875/5000 = 0.575. OK.

sy = horizon + K/d. Want: at d=2500 (near, y=D) → sy = H*0.92. At d=5000 → sy = H*0.30 (horizon-ish). Actually horizon should be where d→∞. sy→horizon. Let's set horizon = H*0.20.

K/2500 = 0.92H - 0.20H = 0.72H → K = 1800H. Then at d=5000: sy = 0.20H + 1800H/5000 = 0.20H+0.36H = 0.56H. Hmm, that's only 0.56, and far edge. So the field spans from y-screen 0.56H to 0.92H. That's a narrow band — actually fine, it's a "field seen from above in slight perspective". But maybe better to have more vertical spread.

Let's instead use gentler perspective. Honestly, a simpler approach: linear depth mapping with scale interpolation. It reads as perspective and is much easier to control.

t = y/D ∈ [0,1], 0 = far, 1 = near.
scale(t) = lerp(0.62, 1.0, t)  (far smaller)
screenY = lerp(H*0.30, H*0.94, t^1.25) maybe.

Actually nonlinear y helps: crowd compresses at distance. Use screenY = H*0.30 + (H*0.64) * t. Fine.

Hmm but with linear mapping, units far away look small — that's the perspective. Good enough. Let's use scale = 0.55 + 0.5*t maybe.

Units: 500 per side. Each unit needs position, target, health, etc. With 1000 units and O(n^2) nearest-enemy search each frame that's 1e6 ops — actually that's fine at 60fps? 1e6 simple distance computations per frame... ~ maybe 5-10ms. Risky. Better: use a uniform grid spatial hash, and find nearest enemy by searching expanding rings of cells. Or simpler: assign targets lazily and update a subset each frame.

Approach: build a spatial grid each frame (cell size ~ 30 world units). For target acquisition, do a ring search. Since the battle starts in two blocks, nearest enemy is roughly the one in front. But once melee forms, ring search works.

Alternative cheaper approach: recompute target for a fraction of units each frame (e.g., 1/8) staggered. Combined with grid, that's cheap.

Let me plan performance carefully:

1000 units. Per frame:
- Grid rebuild: 1000 inserts. Cheap.
- Movement: 1000 updates. Cheap.
- Target acquire: stagger, ~125 units/frame with ring search. Cheap.
- Combat: for each unit, check nearby enemies in same/adjacent cells. Since grid cell ~ unit diameter, check 9 cells. In dense melee, each cell might have ~5-10 units → 90 checks per unit → 90k checks per frame. That's fine.

Actually simpler: do combat within grid by iterating each cell and checking pairs within the cell (and right/down neighbors to avoid double). Still fine.

Let me simplify: each unit, each frame, queries grid for enemies within radius R (its attack range) using the cells it overlaps. With cell size ~ 2*R, only need to check its own cell (and maybe neighbors when near boundary). Let's just check the 3x3 neighborhood but only for the units that are in the "front" — nah, check for all. 1000 units * 9 cells * avg maybe 3 units = 27k distance checks. Fine.

Rendering: 1000 sprites. Drawing each as a small shape with perspective. Canvas 2D with 1000 fill operations per frame is OK-ish. To keep smooth, we can use simple shapes: a small ellipse/rect body + a little head, or just a filled triangle/circle. Let's draw each unit as 2 shapes max: body (rounded rect or ellipse) and maybe a helmet dot. That's 2000 path ops per frame — might be 5-10ms. Hmm.

Optimization: pre-render sprite atlases to offscreen canvases. For each side, create a few frames (walk animation) at several scales? Drawing a pre-rendered small canvas via drawImage is fast. Let's prerender unit sprites at a base size (e.g., 16x20 px) for each side, with maybe 4 walk poses, and then draw scaled with drawImage. 1000 drawImage calls per frame is quite fast (~2-3ms). Good.

Also use depth sorting: draw far units first. Sorting 1000 per frame is ~1000 log1000 ≈ 10k comparisons, fine. Actually we can just sort by y (depth) — use numeric sort on array copy. Or bucket by row. Let's just sort indices by worldY. Actually the render order: farther = smaller y = drawn first. Since our perspective maps far to top, sorting by y ascending works. Simple.

Hmm, but sorting 1000 each frame with Array.prototype.sort of objects with comparator... allocate an array of 1000 each frame — GC pressure. Could keep a persistent array and sort in place. Fine.

Alternatively, since grid is rebuilt each frame, we could iterate cells in depth order. Simpler: just sort.

Actually, we could avoid sorting entirely since units are mostly non-overlapping and small. But with perspective scaling, overlapping matters visually. Let's sort — it's fine.

Particles: blood/dust puffs. Limit to e.g. 600 particles, pooled.

Let me now think about the battle timeline:
- 0-2s: armies in formation, brief "charge" — actually let's start them already charging.
- Armies start as blocks: red on left, blue on right. They charge toward each other.

Hmm, "charging at each other across a field" — so left vs right, they meet in the middle. With perspective, the field is wider than deep. Let's set world width W = 3000, depth D = 1400 (so a wide field). Red army on the left (x from 100 to 700), blue on the right (x from 2300 to 2900). They charge horizontally.

Formation: 500 units each, arranged in a grid, e.g., 25 columns x 20 rows. Column spacing 24, row spacing 40 in depth. That's 25*24 = 600 wide, 20*40 = 800 deep. Depth D=1400, so rows from y=300 to y=1100.

Actually, for the "slight perspective" view we want more depth visible. Let's use D = 1600.

Camera: we render the whole field.

World-to-screen:
- t = y / D
- scale = 0.6 + 0.55*t  → far 0.6, near 1.15. Hmm, far units should be smaller. Let's use 0.62 to 1.18.
- screenY = topMargin + (H - topMargin - bottomMargin) * t... but that's linear. With perspective we want far rows closer together. Use t' = t^1.15? Actually with proper perspective, screenY ∝ 1/d. Let's just do screenY = horizonY + fieldH * (t^1.35)? Hmm, that compresses far more. Wait: far units (t small) should be compressed together near the horizon. t' = t^p with p>1 gives: at small t, t' even smaller → compressed near horizon. At t=1, t'=1. Yes, p = 1.3.

Hmm, but also screenY spread. Let's just do: 
horizon = H*0.16
fieldH = H*0.78
screenY = horizon + fieldH * pow(t, 1.4)

At t=0: horizon. At t=1: horizon+fieldH = 0.94H. Good.

scale = 0.5 + 0.7*t? With perspective scale ∝ 1/d and d ∝ ... eh. Let's just make scale = 0.55 + 0.65*t^1.4 too (consistent). At t=0: 0.55, t=1: 1.2. 

Actually to be consistent with the depth compression: screenY offset from horizon is proportional to scale roughly. Since screenY - horizon = fieldH * t^1.4 and scale = a + b*t^1.4, if a small then consistent. Let's use scale = 0.25 + 0.95 * s where s = t^1.4. At s=0 (horizon): 0.25 — very small. At s=1: 1.2. Hmm 0.25 is tiny; units would be 2px. That's realistic but hard to see.

Let's compromise: scale = 0.5 + 0.7*s. Fortnite-ish. Fine, "slight perspective".

Actually — canvas coordinate: screenX also needs scaling about center. screenX = W/2 + (x - W/2) * scale.

So the field's far edge is narrower on screen. Good, that's the perspective.

Also I want to draw a ground: sky/horizon? Top-down from above — maybe no sky, just a field. Let's draw a horizon band (distant hills / sky) at the top for context, and the field below with grass gradient. Plus some scattered texture (dirt patches, tufts) for motion reference. Keep it simple.

Ground rendering: fill the field region as a trapezoid (far edge narrower). Draw horizontal stripes with varying green to give depth cue. Plus some small grass tufts (pre-generated random positions) drawn with the projection, to show ground movement... but camera is static. Still nice for depth.

For performance, prerender the whole background to an offscreen canvas once (it's static). Yes! Background is static → render once to offscreen canvas at full size, then drawImage each frame. 

Now unit logic:

Each unit:
- side (0 red, 1 blue)
- x, y (world)
- vx, vy
- hp
- target: index of enemy unit
- state: advancing / fighting / dead
- speed
- attack cooldown
- facing/anim frame
- dead → replaced with corpse particle

Combat: when distance to nearest enemy < attackRange, stop and attack. Attack deals damage on cooldown. When hp <= 0, die: spawn blood particles, remove from arrays.

Removing units from arrays: use a "alive" flag and compact arrays, or use a swap-remove. Since we sort for rendering, we can just filter. Let's keep units in arrays and mark dead, then compact periodically (every frame is fine, 1000 elements).

Actually with swap-remove during iteration, need care. Let's do: iterate, mark dead, then at end of update compact arrays.

Spatial grid: rebuild each frame from alive units. Grid over world: cellSize = 60 (world units). W=3000, D=1600 → 50 x 27 = 1350 cells. Fine. Use flat arrays: cellStart/cellCount via counting sort, or array of arrays. Array of arrays with clearing (length=0) each frame is fine for 1350 cells.

Actually for 1000 units, cellSize 60 gives ~1 unit per cell in spread formation, more in melee. Let's use cellSize = 50.

Target acquisition: for unit u, search rings of cells outward from its cell until found enemies, then pick nearest among found in that ring (and maybe one more ring). Limit search radius to, say, 600 world units. If none found, move toward enemy army centroid.

Cost: stagger — recompute target for ~1/6 of units per frame, or recompute when current target is dead or too far. Let's do: each unit has a `retargetTimer`. Recompute every 0.5s + jitter, and immediately when target dies.

Actually to keep it robust and simple: every frame, for each unit, if target invalid (dead or null) → retarget now. Plus a slow periodic retarget (every 0.4s ± jitter) for maybe 20% chance per frame. Let's just do the timer approach: u.retarget -= dt; if (u.retarget <= 0) { findTarget(u); u.retarget = 0.3 + rand*0.4; }

With 1000 units and avg retarget every 0.5s, that's 2000 target acquisitions per second = ~33 per frame. Ring search over up to ~200 cells... each cell check is cheap (length check). Fine.

Movement: unit moves toward target's position at speed. Add slight separation force to avoid stacking? That's expensive. Instead, add small random jitter to velocity and prevent exact overlap by a cheap separation: check same cell for near units and push apart. In melee, this creates the chaotic look. But cost... Let's include a light separation using the grid: for each unit, check its own cell only (plus maybe neighbors), and apply push. With cell size 50 and unit radius ~10, checking own cell is enough for a rough separation.

Hmm, but combat also uses the grid. Let's combine: one pass per unit that does (a) separation and (b) combat checks over the 3x3 neighborhood. That's 9 cells per unit → 9000 cell lookups + distance checks. At maybe 3 units/cell avg → 27k distance checks. At 60fps that's 1.6M/s. Fine in JS.

Actually in melee, density will be much higher. If units pile up in a 50x50 cell... hmm, the front line. Let's estimate: front line length in world x is ~600-1000 units wide. With 1000 units on a line, that's maybe 3-5 units deep. So cells along the front would have ~3-5 units each. Fine.

Let me reduce the 3x3 to just own cell + 4 neighbors? Nah, 3x3 is fine.

Let's write it.

Actually — a cleaner and even faster combat approach: iterate over grid cells; for each cell, for each pair within the cell, check distance; if adjacent enemies within range, both attack. Then also check pairs between cell and right neighbor and down neighbor (and maybe diagonal). That gives each pair checked once. Cost: sum over cells of (n choose 2) + pairs with neighbors. That's efficient. But then attack cooldowns per unit need to be handled — each unit can attack multiple enemies in range? That's fine, a unit can hit anyone in range when its cooldown is up.

Hmm, but that changes semantics slightly. Let's do it: 
- For each pair (a,b) with opposing sides within attackRange: 
  - if a.cooldown <= 0: damage b; a.cooldown = attackInterval
  - if b.cooldown <= 0: damage a; b.cooldown = attackInterval

But then a unit with fast cooldown could hit several enemies in one frame. Since cooldown is set after first hit, it won't. Good.

But with a 3x3 neighbor check and pair dedup... Using the "each cell + right/down/diag-right neighbors" approach dedups properly.

Hmm, but attackRange ~ 22 world units, cellSize 50. Pairs within range could be in cells up to 1 away. Checking cell + 4 neighbors (right, down, down-left, down-right) covers all pairs with distance < cellSize. Good if cellSize >= attackRange. With cellSize=50 and range 22, fine.

Actually, unit separation radius ~ 16, so also covered.

Wait, but pairs within the same cell when the cell is 50 wide: max distance within cell is 70 > 50. Fine, we check distance anyway.

Total pairs: if front is dense, per cell with 5 units → 10 pairs, plus neighbor pairs. Fine.

OK, but there's a subtlety: for the "state" of a unit (fighting vs moving), we need to know if it's engaged. We can set u.engaged = true when it attacks or is attacked, reset each frame.

Movement: if engaged, reduce speed (or stop). Let's make engaged units still push forward slowly.

Now, target selection: nearest enemy. With the grid we can do a ring search. Let's implement:

function findTarget(u) {
  const cx = cellX(u.x), cy = cellY(u.y);
  for (let r = 0; r <= maxRing; r++) {
    let best = null, bestD = Infinity;
    // iterate cells in ring r
    for each cell (cx+dx, cy+dy) where max(|dx|,|dy|) === r:
       for each unit v in cell: if v.side !== u.side && v.alive: d = dist2; if d<bestD...
    if (best) return best;
  }
  return null;
}

This finds true nearest only if the nearest is in the first ring containing any enemy — which is approximately true. Good enough.

maxRing: need enough to find enemies. Armies start ~1600 apart in x. So rings needed: 1600/50 = 32 rings. Each ring has up to 8*32 = 256 cells. Total cells scanned ~ up to 32^2*4 ≈ 4000 worst case. That's a lot but only for initial target acquisition.

Better: for initial targets, just assign by index/formation. Actually, let's just do a full scan fallback: if ring search fails within maxRing=12 (600 units), fall back to searching the entire opposing army array (500 units) — 500 checks, done rarely. Actually even simpler: always do the fallback full scan if ring search fails. Since after the initial charge everything is in melee, the ring search succeeds quickly.

Hmm, initial: 1000 units each doing a full 500-enemy scan = 500k ops in the first frame — that's fine, one time. But they're staggered over frames... some units won't have a target for a few frames. Just give every unit a target at spawn via a cheap heuristic: target = enemy unit with nearest index-ish. Actually at spawn, formation is a grid; nearest enemy is roughly the same row. Let's just do: initially, target = the enemy unit at mirrored position (index mapping). That's instant and looks good.

Then retarget timers handle the rest.

Hmm, actually with a full-scan fallback of 500 checks per unit and 33 units/frame → 16.5k checks. Totally fine. Let's just always use ring search with escalating rings up to 10, then a full scan fallback. Simple and correct.

Let me reconsider: maybe skip the grid ring search entirely and just do full scans staggered? 1000 units retargeting every 0.5s = 2000 full scans/sec × 500 enemies = 1M distance checks/sec. That's actually fine! ~1M ops/sec is nothing. Hmm, but they'd be clustered. With staggered retargeting over frames: 2000/60 ≈ 33 scans per frame × 500 = 16.5k checks/frame. Very fine.

Oh nice — that's simpler. But the requirement says "Keep it smooth with simple spatial partitioning." So we should use spatial partitioning. Let's use the grid for BOTH combat pairs and target search. I'll implement ring search with full-scan fallback. Good, satisfies the requirement.

Let me now write the code.

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Battle</title>
<style>
  html,body { margin:0; padding:0; height:100%; overflow:hidden; background:#1a1f16; }
  canvas { display:block; width:100%; height:100%; }
  #ui { position:fixed; ... }
</style>
</head>
<body>
<canvas id="c"></canvas>
<script>
...
</script>
</body>
</html>
```

I'll draw UI on the canvas itself (counters, title) rather than DOM — simpler for scaling. Actually DOM is easier for text styling. But canvas text is fine too. Let's do canvas text so it scales with the canvas and no layout issues. Hmm, DOM text is crisper. Let's use DOM overlay for title and counters — it's simple and looks good.

Actually, canvas-drawn text with proper DPR scaling is also crisp. Let's use DOM for the HUD (title + counters) — less code, easier styling.

Let me write:

```html
<div id="hud">
  <div id="title">The Battle of Emberfield</div>
  <div id="sub">... </div>
  <div id="counters">
    <div class="cnt red"><span id="redN">500</span> <small>CRIMSON HOST</small></div>
    <div class="cnt blue"><span id="blueN">500</span> <small>AZURE LEGION</small></div>
  </div>
</div>
```

Hmm, layout: title at top center; counters at top-left and top-right. Let's do that.

Now, code structure:

```js
const cv = document.getElementById('c');
const ctx = cv.getContext('2d');
let W, H, DPR;

// World
const FIELD_W = 3400;   // world x
const FIELD_D = 1500;   // world depth (y)

// projection params
let view = { horizon: 0, fieldH: 0, cx: 0 };

function computeView() {
  view.horizon = H * 0.20;
  view.fieldH = H * 0.74;
  view.cx = W * 0.5;
}

function projScale(y) {  // y in world depth 0..FIELD_D
  const t = y / FIELD_D;
  const s = Math.pow(t, 1.35);
  return 0.5 + 0.75 * s;
}
function projY(y) {
  const t = y / FIELD_D;
  return view.horizon + view.fieldH * Math.pow(t, 1.35);
}
function projX(x, y) {
  const s = projScale(y);
  return view.cx + (x - FIELD_W/2) * s;
}
```

Wait — with this projection, the world x span at scale 0.5 (far) covers 3400*0.5 = 1700 px on screen, and at near scale 1.25 covers 4250 px. So on a 1600px-wide screen, both are wider than the screen. That means the field overflows horizontally. Hmm.

We need the field to fit. Field width on screen at near = FIELD_W * 1.25 must be ≤ W. So FIELD_W should be ~ W/1.25 in world terms... but then it's screen-dependent.

Alternative: scale the projection so that the near edge maps the full world width to the screen width. Let's define:

xScaleFactor = W / FIELD_W  (roughly), and then apply perspective scale relative to that.

Let me redefine: 
- basePx = W / FIELD_W  → world unit to px at scale 1.
- projX(x,y) = W/2 + (x - FIELD_W/2) * basePx * s(y), where s(y) ∈ [sFar, sNear].
- sNear = 1.0 at y = FIELD_D (near edge maps exactly to screen width).
- sFar = 0.6 at horizon.

Then the field at the near edge spans the full width W. Good.

But the aspect: FIELD_D should be chosen so the vertical extent looks right. With fieldH = 0.74*H, and FIELD_W = W/basePx... Let's just set FIELD_W = W (world units == px at scale 1) and FIELD_D = W * 0.45 (so the field is ~2.2:1 wide). Then basePx = 1.

So world coords are essentially pixels at the near plane. FIELD_W = W, FIELD_D = W*0.45.

Hmm, but W varies with window size. That's fine — recompute on resize and rescale the world? Simpler: keep a fixed world size and let basePx adapt.

Let's just fix: FIELD_W = 3200, FIELD_D = 1500. basePx = W / (FIELD_W * 1.0) — hmm, but we want the near row to fit. Actually with a perspective view, the near edge is closest to the camera and appears widest. Let's have the near edge span exactly W.

basePx = W / (FIELD_W * sNear) where sNear = s(1) = 1.25. So basePx = W / 4000.

And the vertical: fieldH = H*0.72. projY = horizon + fieldH * pow(t, 1.35).

Hmm, but the vertical mapping is independent of the horizontal scale factor, so the "perspective" isn't physically consistent — but it looks fine.

Wait, there's an issue: if basePx depends on W, and H is small, then units might be tiny. It's fine.

Actually, let me simplify further. Let me make the projection:

```
const S_FAR = 0.55, S_NEAR = 1.15;
function depthT(y){ return Math.pow(y/FIELD_D, 1.35); }
function projScale(y){ return S_FAR + (S_NEAR-S_FAR)*depthT(y); }
function projX(x,y){ return view.cx + (x - FIELD_W/2) * view.k * projScale(y); }
function projY(y){ return view.horizon + view.fieldH * depthT(y); }
```
where view.k = W / (FIELD_W * S_NEAR) — this makes the widest (near) edge span exactly W... times... let's check: at y=FIELD_D, projScale = S_NEAR, so projX range = FIELD_W * k * S_NEAR = W. Yes! The near edge spans the full canvas width, centered. 

And at the far edge, projScale = S_FAR, span = W * S_FAR/S_NEAR = W*0.478. Centered. Good trapezoid.

Now the horizon and field height: horizon = H*0.18, fieldH = H*0.76. So the field goes from y=0.18H to 0.94H.

Vertical world depth FIELD_D = 1500; the far edge is at screen y = 0.18H, near at 0.94H.

Now, unit size: base size, say a sprite 12 px wide at scale 1 (in "world px at scale 1"?). Hmm — I defined world coords such that at scale 1, 1 world unit = k px... wait no. projX = cx + (x - FW/2)*k*scale. So a world distance of 1 unit maps to k*scale px. k = W/(FIELD_W*S_NEAR) = W/3680.

For W=1600: k = 0.435. So at near edge, 1 world unit = 0.5 px. Hmm, so world units are ~2x screen px. FIELD_W=3200 world units → 1600 px at near. Right.

So a unit of world-radius 20 → 20*0.435*1.15 = 10 px at the near edge, and 20*0.435*0.55 = 4.8 px at the far edge. That's reasonable.

Let's define unit sprite base size in world units: width 40, height 44 (a little human figure seen from above at an angle). Hmm, from above, a person is roughly 40 world units wide? Let's see: people ~0.5m wide. If the field is 3200 world units ≈ 200 m wide, then 1 world unit = 6.25 cm, so a person is 8 units wide and ~30 units tall (from above, including shoulders/body length?). 

Hmm, this is getting complicated. Let's just tune visually: make units ~26 world units wide and 34 tall (in perspective, the vertical extent gets squashed... actually no, in our projection the vertical size should scale with projScale too).

Screen size of a unit at near edge: width = 26 * k * 1.15. With W=1600, k=0.435: 26*0.5 = 13 px. Good. At far edge: 26*0.435*0.55 = 6.2 px. Good.

Height on screen: same scale factor → 34*0.435*1.15 = 17px near. OK.

For an overhead-ish view, I'll draw the unit as an ellipse (body/shoulders) plus a small head, oriented toward facing. Since it's a battle from above at a slight angle, I'll just draw an ellipse body + head circle, plus a weapon line. Keep it simple: I'll pre-render sprites.

Pre-rendering: I'll create an offscreen canvas per side per pose, at a fixed high resolution, then drawImage scaled.

Sprite canvas: 32x40 px at "unit space". Let's render at 4x for quality: 128x160. Then drawImage with dest size = (worldW * k * scale) etc.

Actually simpler: render sprite at a base of, say, 64x80 px, and draw at dest size (unitW * k * scale, unitH * k * scale). Since dest is ~13x17 px, downscaling from 64x80 gives nice antialiasing. Good.

Sprite design (top-down-ish figure):
- Elliptical body (armor color)
- Head (helmet, lighter)
- Shoulders
- A small weapon (spear/sword) pointing in the facing direction

Since units face different directions, I'd need rotations. Rotating 1000 sprites per frame with ctx.save/rotate/restore is expensive. 

Alternative: don't rotate. Since the view is from above at a slight angle and units are small, I can just draw them as blobs that don't rotate but shift slightly. Hmm.

Compromise: pre-render 8 rotation variants per side per pose. 8 rotations × 4 poses × 2 sides = 64 sprites. Then drawImage with the appropriate rotation index. That's fast!

But rotating a top-down figure looks odd because the "head" should stay up-ish. Actually for a top-down view, rotation is correct — the head is at the center and the body/shoulders rotate.

Hmm, actually for a "seen from above in slight perspective" view, the units should be drawn as if slightly tilted. A simple approach: draw an ellipse for the body (which rotates), a circle for the head at the center, and a weapon.

Let me do: sprite drawn in a canvas where the unit faces "right" (angle 0). Then pre-render 12 angles. The sprite = 
- shadow ellipse (dark, below)
- body ellipse (armor color, offset slightly toward facing)
- head circle (helmet color) at center-ish
- weapon line from center forward
- maybe a shield

At the small final size (~13px), these details barely matter. What matters is the color and motion. Let's keep it simple: body ellipse + head + weapon.

Actually, you know what — let me simplify dramatically and just draw each unit per-frame with basic shapes but use a fast path. 1000 units × ~3 path ops... In canvas, fillRect/fill of small ellipses. Ellipse via ctx.ellipse requires beginPath + ellipse + fill. That's maybe 1-2 µs each → 1000 units × 3 = 3000 ops ≈ 3-6 ms. Borderline but probably OK at 60fps. Hmm.

Pre-rendered sprites via drawImage: ~0.5µs each → 1000 = 0.5-1ms. Much better. Let's do sprites.

I'll generate 16 rotation frames per side. Each frame is a 48x48 canvas at 2x = 96x96... Actually, let's make each sprite canvas 40x40 and draw the unit at the center, sized to fit (unit ~34px in sprite space). Then when drawing, dest width = 34 * (k*scale) ... let me define:

Unit's world-space "visual diameter" = UNIT_SIZE = 30 world units (used for both sprite scaling and body radius). 

screen diameter = UNIT_SIZE * k * projScale(y).

Sprite canvas is SPR = 48px with the unit drawn at diameter 44 (leaving margin). So dest size = screenD * (48/44).

Let's just make the sprite fill the whole canvas and dest size = screenD... simpler. Sprite canvas 48x48, unit drawn centered with diameter ~44 (small margin for the shadow and weapon).

Hmm, weapon extends forward — might clip. Let's keep the weapon within.

OK. Let's write the sprite generator.

```js
function makeSprite(color, accent, angle) {
  const S = 48;
  const c = document.createElement('canvas');
  c.width = S; c.height = S;
  const g = c.getContext('2d');
  g.translate(S/2, S/2);
  g.rotate(angle);
  // facing = +x after rotation
  // shadow
  g.fillStyle = 'rgba(0,0,0,0.28)';
  g.beginPath(); g.ellipse(1, 2, 11, 9, 0, 0, 7); g.fill();
  // body
  g.fillStyle = color;
  g.beginPath(); g.ellipse(0, 0, 10, 8.5, 0, 0, 7); g.fill();
  // shoulder highlight
  g.fillStyle = accent;
  g.beginPath(); g.ellipse(-1, 0, 7, 6, 0, 0, 7); g.fill();
  // helmet
  g.fillStyle = accent2;
  g.beginPath(); g.arc(-2, 0, 5, 0, 7); g.fill();
  // weapon
  g.strokeStyle = '#e8e2d0'; g.lineWidth = 2;
  g.beginPath(); g.moveTo(2, -4); g.lineTo(14, -6); g.stroke();
  ...
}
```

Hmm, careful with the layout. Fine.

Actually, maybe better: body along the facing direction, head at front third. From above, a person is elongated along the facing axis. Let's do:
- body ellipse: rx=11 (along facing), ry=8
- head: circle r=5 at (5,0)
- weapon: line from (6,7) to (18,4)? 

OK whatever. Let's just make it look like a little soldier blob. At 13px on screen it's a colored dot with a highlight. Fine.

Colors: Red side = crimson (#d33), accent darker (#8a1c1c), helmet = #eee or a lighter red. Blue side = #3a7bd5 / #1b3f7a / helmet light.

Now, blood/dust particles: small circles. Pre-render? Just use fillRect with globalAlpha — cheap. 600 particles × fillRect = fine.

Death puff: burst of 6-10 particles, red-ish (blood) plus a dark dust.

Corpses: when a unit dies, leave a dark stain on the ground. Draw stains? Accumulating 1000 stains... we could draw them into the background canvas! That's a neat trick: when a unit dies, draw a small dark ellipse into the offscreen background canvas (permanent). That gives a battlefield progressively staining. Nice. But the background is drawn each frame from the offscreen — so it persists. 

Careful: the background canvas is redrawn on resize. We'd lose the stains. Acceptable.

Let's do it: draw blood pool onto bg canvas at death position.

Now the simulation loop and phases:

Phase 1 - "CHARGE" (armies advance). 
Phase 2 - "MELEE".
Phase 3 - one side wins → "VICTORY": survivors celebrate (jump/cheer animation, maybe raise weapons), then after ~4s, fade and restart with a new battle name.

To keep within 30s: the battle should start immediately and resolve within ~20-25s. With 500 v 500 and combat, how long? Each unit attacks ~1/sec dealing ~34 damage, hp 100 → ~3 hits to kill. In melee, average lifetime maybe 5-8 seconds. The whole battle might take 30-60s. Too long!

Let's tune for a ~15-20 second battle:
- hp = 100
- attack interval = 0.28s
- damage = 22 (so 5 hits → 1.4s per kill if focused)

Hmm, but each unit only fights one or two enemies at a time. Let's think: in melee, fronts collide. The rate of killing depends on the number of engaged pairs. Roughly, each engaged unit kills an enemy in ~3-4 seconds. With ~200 engaged pairs early, that's 50 kills/sec → 500 units gone in 10s. Then it accelerates. 

Actually, let's just tune empirically-ish: I'll set attackInterval = 0.35, damage = 20 → 5 hits = 1.75s of continuous attacking per kill. But units often switch targets. Let's say ~3s per kill per engaged unit.

Early: the front line has maybe 100 units per side engaged → 100 kills per 3s per side... no wait. Each engaged pair: both fight. Kill rate ≈ (number of engaged units) / 3s. If 200 engaged units → 66 kills/s. After 5s, 330 dead. Then it keeps going. Should finish in ~15-20s. 

Also, important: only the front-line units engage initially. So the kill rate is limited by the contact perimeter. With 500 units per side in a 25-wide × 20-deep formation, the front is 25 wide → only ~25 units per side engaged initially. That's slow!

Hmm. So the battle would drag. Let's make the formation wider: 50 wide × 10 deep. Then 50 units per side engaged at first contact, escalating as the lines interpenetrate.

50 engaged units → ~17 kills/s → 500 units in 30s. Hmm still slowish but the melee becomes chaotic and more units engage.

Let's speed it up: attack interval 0.3s, damage 25 → 4 hits to kill = 1.2s. And units deal damage to all enemies in range? Let's make it so that when a unit attacks, it hits the nearest enemy only, but the attack is fast. In dense melee, many units are adjacent.

Alternatively: reduce hp so kills are fast. Let's do hp = 60, damage = 18, interval = 0.3 → 4 hits = 1.2s. Kill rate per engaged unit ≈ 1/1.2 but they may not always find a target in range... 

Realistically the battle will take ~15-25 seconds, which is what we want. I'll tune and also add a "hastening" mechanic: as time goes on, increase damage slightly (adrenaline) to ensure resolution. Actually, a simpler safety: if the battle exceeds 35s, increase damage multiplier gradually.

Let me also add: the losing side's units get surrounded, so it accelerates naturally.

Let me now think about the "formation breaks into chaotic melee". Initially, units are in neat rows/columns moving in the same direction. Once they engage, they should mill around. With target-following plus separation jitter, this happens naturally.

To keep the initial formation look: during the charge phase (no enemy within X), units move straight toward the enemy line, maintaining roughly their row. Add a small per-unit speed variation so the lines ripple.

Okay. Let's write.

Data layout: For performance, use typed arrays? With 1000 units, plain objects are fine. Let's use plain objects for clarity.

```js
class Unit {
  constructor(side, x, y) { ... }
}
```

Actually, let's use a flat object array.

```js
const units = [];      // alive units
const unitPool = [];   // for reuse
```

Let me write the code now.

```js
// ==== Globals ====
const cv = document.getElementById('c');
const ctx = cv.getContext('2d', { alpha: false });
let W = 0, H = 0, DPR = 1;

const FIELD_W = 3200;
const FIELD_D = 1500;
const S_FAR = 0.55, S_NEAR = 1.15;
const PERSP = 1.35;

let view = { cx: 0, horizon: 0, fieldH: 0, k: 1 };

function resize() {
  DPR = Math.min(window.devicePixelRatio || 1, 2);
  W = Math.floor(window.innerWidth);
  H = Math.floor(window.innerHeight);
  cv.width = Math.floor(W*DPR);
  cv.height = Math.floor(H*DPR);
  cv.style.width = W + 'px';
  cv.style.height = H + 'px';
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  view.cx = W/2;
  view.horizon = H*0.16;
  view.fieldH = H*0.78;
  view.k = W / (FIELD_W * S_NEAR);
  buildBackground();
}
```

Wait — if W is small, k is small and units get tiny. On a phone (W=400), units would be 1/4 the size. Acceptable but maybe hard to see. Could clamp k to a minimum. But then the field wouldn't fit. Let's not worry; assume a desktop-ish window. Actually, we should handle it. Let's set k = max(W/(FIELD_W*S_NEAR), H*0.00055)? Hmm, that would make the field overflow horizontally on narrow screens. It's fine — a slight crop.

Let's do: view.k = Math.max(W / (FIELD_W * S_NEAR), H / (FIELD_D * 1.6)); Hmm, that's arbitrary.

Let me just use k = W/(FIELD_W*S_NEAR) and also ensure unit screen size is decent by capping. Eh, keep it simple. Most viewers use a wide window.

Hmm, actually: with W=1600, H=900. k = 1600/3680 = 0.435. Unit diameter UNIT_SIZE=30 world → 30*0.435*1.15 = 15px near, 30*0.435*0.55 = 7px far. Good.

Background: pre-render.

```js
let bgCanvas, bgCtx;
function buildBackground() {
  bgCanvas = document.createElement('canvas');
  bgCanvas.width = cv.width; bgCanvas.height = cv.height;
  bgCtx = bgCanvas.getContext('2d');
  bgCtx.setTransform(DPR,0,0,DPR,0,0);
  // sky / distant
  const skyGrad = bgCtx.createLinearGradient(0,0,0,H*0.3);
  skyGrad.addColorStop(0,'#5b7a9e'); ... 
  // field
  ...
}
```

Let's make a nice looking scene:
- Sky gradient from dark blue-grey to pale at the horizon.
- Distant hills silhouette.
- Field: from the horizon down, a green gradient (darker far, lighter near) drawn as a trapezoid.
- Field texture: random tufts, drawn small, scaled by depth.

Actually, the field trapezoid: corners at (projX(0,0), projY(0)) = left-far, (projX(FW,0), projY(0)) = right-far, (projX(FW,FD), projY(FD)) = right-near, (projX(0,FD), projY(FD)) = left-near.

With view.k chosen so the near edge spans W exactly, the near corners are at x=0 and x=W. And the far corners at cx ± FW/2*k*S_FAR = cx ± (W/(2*S_NEAR))*S_FAR = cx ± W*0.478/2. Good.

Vertical gradient fill for the field: fill the trapezoid with a gradient from dark green at the top to lighter green at the bottom.

Then add horizontal "furrow" lines? Maybe subtle bands. And scatter grass tufts.

Let's write:
```js
const path = new Path2D();
path.moveTo(projX(0,0), projY(0));
path.lineTo(projX(FIELD_W,0), projY(0));
path.lineTo(projX(FIELD_W,FIELD_D), projY(FIELD_D));
path.lineTo(projX(0,FIELD_D), projY(FIELD_D));
path.closePath();
```
Then grad from projY(0) to projY(FIELD_D): '#3a4a2a' → '#6b8a45'.

Then clip and draw tufts.

Tufts: generate ~1200 random positions in world space at build time (persistent array), then draw them clipped to the field. Each tuft is a tiny short line. Since the background is static, this is drawn once. 

Also add some dirt patches.

Stains from blood: drawn into bgCtx later. But bgCtx has the clip? No, clip is reset. Fine — draw stains without clipping (they're on the field anyway).

OK.

Now the simulation.

```js
const SIDES = [
  { name:'CRIMSON HOST', color:'#d8383a', dark:'#7d1a1c', light:'#ff8a7a', accent:'#f2d0a0' },
  { name:'AZURE LEGION', color:'#3f7fd8', dark:'#16346f', light:'#8fc0ff', accent:'#dfe8f5' }
];
```

Units per side: 500.

Formation: For side 0 (red), they occupy the left. Let's define:
- COLS = 50, ROWS = 10 → 500.
- Column spacing along x: 34 world units. 50 cols → 1666 wide. Hmm, that's more than half the field. FIELD_W = 3200. Red occupies x from 200 to 1866? Too much.

Let's reduce spacing: colSpacing = 26 → 50 cols = 1275 wide. Red from x=150 to 1425. Blue from x=1775 to 3050. Gap between them = 350. Hmm, but then they're already close.

Actually, spacing 26 with UNIT_SIZE=30 means units are overlapping. Unit visual diameter 30 world units, so spacing should be ≥ 30.

Let's reconsider: 500 units at spacing 32 → a 22x22 block = 700x700. Hmm, that's a square. With FIELD_D=1500, that fits.

Let's do 25 cols × 20 rows, spacing x = 30, spacing y = 42 (rows need more spacing due to perspective compression... actually no, in world space uniform spacing is fine).

Block: 25*30 = 750 wide, 20*42 = 840 deep. Depth 840 out of 1500. Centered at y=750 ± 420 → 330 to 1170. Good.

Red block: x from 250 to 1000. Blue block: x from 2200 to 2950. Gap = 1200 world units. At near-edge scale, that's 1200*0.435 = 520 px. They charge at ~60 world units/sec → 10 seconds to close. Too slow. Need ~3-4 seconds.

Speed: let's say 110 world units/s. 1200 gap / 220 (closing speed both) = 5.5s. Hmm. Let's start them closer: red x 350-1100, blue x 2100-2850, gap = 1000 → 4.5s. Or increase speed to 150 → 3.3s.

Let's use speed ~140 and gap 900 → 3.2s to contact. Good.

Actually "charging" should look fast and dramatic. Let's go with speed 130-160 (with variation).

Let's finalize:
- COLS=25, ROWS=20, N=500
- Red center x = 700, Blue center x = 2500. 
- Red columns: x = 700 - 12*30 ... width = 24*30 = 720, so x from 340 to 1060.
- Blue: x from 2140 to 2860.
- Gap = 2140 - 1060 = 1080. Closing at 280/s → 3.9s. Good with speed 145.

Rows: y from FIELD_D/2 - 19*21 = 750 - 399 = 351 to 750+399 = 1149. Row spacing 42.

Wait, 20 rows with spacing 42 → 19*42 = 798 span. y from 351 to 1149. Good.

Depth-wise the units fill a good portion.

Hmm, but the perspective compresses the far part. Units near y=351 will be small. Fine.

Now the charge: each unit moves toward its target (nearest enemy). Since the formations face each other, the front rows engage first.

Let's add a slight forward-facing arrangement so the front row is a proper line.

Now, unit stats:
- hp: 100 * (0.85 + rand*0.3)
- speed: 130 + rand*40
- attackInterval: 0.30 + rand*0.12
- damage: 16 + rand*8
- range: 30 (world units, center to center)

Range 30 with unit diameter 30 → they touch. Good.

Separation: keep units from overlapping. Push apart if distance < 26.

Let's write the update:

```js
function step(dt) {
  // rebuild grid
  buildGrid();
  // update timers, retarget, move
  for (const u of units) { ... }
  // combat via grid pairs
  // particles
  // cleanup dead
}
```

Order: 
1. Clear engaged flags.
2. For each unit: cooldown -= dt; retarget if needed; move toward target.
3. Grid build (after movement? or before?). Let's build the grid after movement, then do combat. Actually target search uses the grid too. Let's build the grid first, do retargeting + movement, rebuild the grid, then combat. Rebuilding twice per frame is 2000 inserts — cheap. Or: build once at the start of the frame using last frame's positions. That's fine too and simpler. Slight staleness is imperceptible.

Let's do: build grid at the start (positions from end of last frame). Then retarget (uses grid), then move, then combat (uses grid — slightly stale positions, but movement per frame is ~2.4 world units at 145 speed and 60fps; negligible). Fine.

Hmm, but with varying dt, movement could be larger. Cap dt to 1/30.

Grid implementation:

```js
const CELL = 64;
const GW = Math.ceil(FIELD_W / CELL);   // 50
const GH = Math.ceil(FIELD_D / CELL);   // 24
const grid = new Array(GW*GH);
for (let i=0;i<grid.length;i++) grid[i] = [];
```

Clear: `for (const c of grid) c.length = 0;` — 1200 iterations, fine.

```js
function buildGrid() {
  for (let i=0;i<grid.length;i++) grid[i].length = 0;
  for (let i=0;i<units.length;i++) {
    const u = units[i];
    const gx = Math.min(GW-1, Math.max(0, (u.x / CELL)|0));
    const gy = Math.min(GH-1, Math.max(0, (u.y / CELL)|0));
    u.gx = gx; u.gy = gy;
    grid[gy*GW+gx].push(u);
  }
}
```

Note: `for (const c of grid)` with 1200 arrays — fine, but the index loop is similar.

Retarget with ring search:

```js
function findTarget(u) {
  const gx = u.gx, gy = u.gy;
  let best = null, bestD = Infinity;
  for (let r = 0; r <= 8; r++) {
    let found = false;
    for (let dy = -r; dy <= r; dy++) {
      const yy = gy + dy;
      if (yy < 0 || yy >= GH) continue;
      for (let dx = -r; dx <= r; dx++) {
        if (Math.max(Math.abs(dx),Math.abs(dy)) !== r) continue;
        const xx = gx + dx;
        if (xx < 0 || xx >= GW) continue;
        const cell = grid[yy*GW+xx];
        for (let i=0;i<cell.length;i++) {
          const v = cell[i];
          if (v.side === u.side || !v.alive) continue;
          const ddx = v.x-u.x, ddy = v.y-u.y;
          const d = ddx*ddx + ddy*ddy;
          if (d < bestD) { bestD = d; best = v; }
        }
        if (cell.length) found = true;  // hmm not exactly
      }
    }
    if (best) return best;
  }
  // fallback: full scan
  for (const v of units) { if (v.side!==u.side && v.alive) { ... } }
  return best;
}
```

The `found` variable isn't needed since we return as soon as best is set. But we should only return after finishing the full ring (to get the true nearest within that ring). The code above does that. Good.

Rings up to 8 → 8*64 = 512 world units. Fallback: full scan.

Full scan cost: 1000 iterations. Only for isolated units. Fine.

Actually, we should be careful: with 500 enemies, a full scan is 1000 iterations of the whole units array (which includes allies). 1000 iterations is nothing.

Hmm, but at the very start, if the ring search radius 512 is less than the gap (1080), every unit would need a full scan. During the initial charge, that's 1000 full scans over maybe the first 2-3 seconds (staggered retargets). Let's estimate: 1000 units retargeting every ~0.5s → 2000 scans/sec × 1000 iterations = 2M iterations/sec. That's fine actually. And it only happens for ~4 seconds.

But we can do better: give initial targets at spawn (mirrored index), and only retarget when the target dies or every 0.6s. Fine.

Actually, an even better fallback: scan the enemy side's array directly. Keep separate arrays `armies[0]` and `armies[1]`? But units list is a single array for simplicity. Eh, the fallback is fine.

Let me raise the ring cap to 12 (768 units) to reduce fallback usage.

Movement:

```js
const dx = t.x - u.x, dy = t.y - u.y;
const d = Math.hypot(dx,dy) || 1;
if (d > u.range*0.9) {
  // move toward
  let sp = u.speed;
  if (u.engaged) sp *= 0.15;   // pushing in melee
  u.vx = dx/d*sp; u.vy = dy/d*sp;
  // add slight jitter
} else {
  u.vx *= 0.6; u.vy *= 0.6;
}
u.x += (u.vx + u.jitterX) * dt;
...
```

Hmm, let's simplify: compute a desired velocity, then apply separation, then integrate.

Let me restructure the per-unit update:

```js
for each u:
  u.cool -= dt;
  u.retargetT -= dt;
  if (!u.target || !u.target.alive || u.retargetT <= 0) { u.target = findTarget(u); u.retargetT = 0.35 + Math.random()*0.35; }
  
  let ax = 0, ay = 0;
  const t = u.target;
  if (t) {
    const dx = t.x - u.x, dy = t.y - u.y;
    const d = Math.sqrt(dx*dx+dy*dy) || 1;
    if (d > u.reach) {
      const s = u.speed / d;
      ax = dx*s; ay = dy*s;
      // blend with current velocity for smooth accel
    }
  } else {
    // move toward the enemy center
  }
  // steering
  u.vx += (ax - u.vx) * Math.min(1, dt*8);
  u.vy += (ay - u.vy) * Math.min(1, dt*8);
  u.x += u.vx*dt; u.y += u.vy*dt;
  // clamp to field
```

Separation is applied in the combat pass (push apart).

Combat pass:

```js
for (let gy=0; gy<GH; gy++) {
  for (let gx=0; gx<GW; gx++) {
    const cell = grid[gy*GW+gx];
    const n = cell.length;
    if (!n) continue;
    // within cell
    for (let i=0;i<n;i++) {
      const a = cell[i];
      for (let j=i+1;j<n;j++) {
        interact(a, cell[j]);
      }
      // with right neighbor
      if (gx+1 < GW) { const c2 = grid[gy*GW+gx+1]; for (const b of c2) interact(a,b); }
      // with down neighbor
      if (gy+1 < GH) { const c2 = grid[(gy+1)*GW+gx]; for (const b of c2) interact(a,b); }
      // down-left and down-right
      if (gy+1 < GH && gx+1 < GW) { const c2 = grid[(gy+1)*GW+gx+1]; for (const b of c2) interact(a,b); }
      if (gy+1 < GH && gx-1 >= 0) { const c2 = grid[(gy+1)*GW+gx-1]; for (const b of c2) interact(a,b); }
    }
  }
}
```

Hmm, this checks pairs twice for the "down-left" and "down-right"? Let's verify: for cell (gx,gy), we check neighbors (gx+1,gy), (gx,gy+1), (gx+1,gy+1), (gx-1,gy+1). Consider the pair (cell A=(0,0), cell B=(1,1)). From A, we check (1,1) [down-right]. From B, we check (-1,-1)? We don't check up-left. So no duplicate. 

Consider (A=(1,0), B=(0,1)): From A, "down-left" checks (0,1). ✓. From B=(0,1), we check (1,1),(0,2),(1,2),(-1,2). Not (1,0). ✓ No duplicate.

Good, this covers all 8 neighbors exactly once.

But: this is per-cell iteration. The total work is proportional to the number of unit pairs within ~1 cell distance. Fine.

Hmm, but the loop `for (const b of c2)` allocates an iterator... For-of over arrays is generally fine in modern JS engines. Let's use indexed loops for safety.

interact(a,b):
```js
function interact(a,b) {
  const dx = b.x-a.x, dy = b.y-a.y;
  const d2 = dx*dx+dy*dy;
  if (d2 > SEP2) return;  // 40^2 = 1600
  const d = Math.sqrt(d2) || 0.0001;
  // separation
  const push = (SEP - d) * 0.5;
  const nx = dx/d, ny = dy/d;
  if (a.side === b.side) {
    // friendly: gentle separation
    a.x -= nx*push*0.5; a.y -= ny*push*0.5;
    b.x += nx*push*0.5; b.y += ny*push*0.5;
  } else {
    // enemy: hard stop + damage
    a.engaged = true; b.engaged = true;
    const sep = (SEP - d) * 0.5;
    a.x -= nx*sep; a.y -= ny*sep;
    b.x += nx*sep; b.y += ny*sep;
    if (d < a.reach && a.cool <= 0) { damage(b, a.dmg); a.cool = a.atkInt; a.swing = 1; }
    if (d < b.reach && b.cool <= 0) { damage(a, b.dmg); b.cool = b.atkInt; b.swing = 1; }
  }
}
```

Wait — modifying positions inside the pair loop while iterating could cause issues, but it's fine numerically.

Hmm, but separation inside the pair loop means each unit is pushed by many neighbors — could be jittery. With push*0.5 each and multiple neighbors, it should be okay but might oscillate. Let's use a smaller factor and also damp velocity.

Actually, a common approach: accumulate separation forces and apply after. But that requires a second pass. Let's just do direct positional correction with a small factor. It works in practice for boids.

Let me use: correction = (SEP - d) * 0.25 applied directly to positions. With SEP=34 and many neighbors, units will settle into a lattice.

Actually, if the density is too high, they can't all be satisfied. Fine, it'll just look crowded.

Hmm, one concern: units pushing each other could push them out of the field. Clamp positions to the field bounds.

Also, dealing damage: 
```js
function damage(u, amount) {
  u.hp -= amount;
  u.flash = 1;
  if (u.hp <= 0 && u.alive) { kill(u); }
}
```

kill(u): u.alive = false; spawn blood particles; add a stain to bg; u.deadTime = time.

Then after the combat pass, compact the units array.

Also the winner check: if one side has 0 alive → victory.

Victory handling: 
- Set phase = 'victory', record winner.
- Surviving winner units do a celebration: they move toward the center, jump up and down, spawn confetti/sparkle particles.
- After 5 seconds, reset with a new battle name.

Celebration animation: units bob (drawn with a vertical offset), maybe raise weapons. Since we're drawing sprites, a bob = offset the draw y by sin(t*8 + phase) * amount. Easy.

Also spawn "cheer" particles (dust/sparkles) from the winners.

Then restart: new battle name, new seed, reset positions.

Battle names: generate from lists: ["The Battle of ", "The Siege of ", "The Clash at ", "The Field of "] + ["Emberfield","Ashvale","Redmoor","Ironwood","Greyhollow","Thornmere","Blackford","Stormgate","Duskdale","Karrowfen"]. Plus maybe a battle number.

Title: main text + subtitle "Round II" etc.

Now let's also handle kills and the counter UI.

UI update: only update the DOM when the count changes.

Now particles:

```js
const particles = [];  // pooled
// {x,y,vx,vy,life,maxLife,size,color,type}
```
Max ~800. Draw with fillRect (square puffs look fine for dust) or arcs.

For blood: red circles that fly out and settle. For dust: grey-brown squares.

Let's draw particles as small rects with alpha, projected. Projecting each particle: projX/projY computes with Math.pow — expensive for 800 particles × 60fps = 48000 pow calls/sec. Fine actually. But let's precompute using a lookup table for depthT.

Yes! Build a LUT: for y in 0..FIELD_D step 8, store projY and projScale. Then interpolate. That's much faster.

```js
const LUT_N = 256;
const lutY = new Float32Array(LUT_N+1);
const lutS = new Float32Array(LUT_N+1);
function buildLUT() {
  for (let i=0;i<=LUT_N;i++) {
    const t = i/LUT_N;
    const s = Math.pow(t, PERSP);
    lutY[i] = view.horizon + view.fieldH * s;
    lutS[i] = S_FAR + (S_NEAR-S_FAR)*s;
  }
}
function projYF(y) {
  let f = y * (LUT_N/FIELD_D);
  if (f < 0) f = 0; if (f > LUT_N) f = LUT_N;
  const i = f|0;
  const fr = f - i;
  return lutY[i] + (lutY[Math.min(i+1,LUT_N)] - lutY[i]) * fr;
}
```

Hmm, linear interpolation between LUT entries. With 256 entries the error is tiny. Good.

But we also need projScale for the x mapping. Same LUT.

Actually, since scale and y are both derived from the same s = t^1.35, I could store s in a LUT and compute projY = horizon + fieldH*s and scale = S_FAR + (S_NEAR-S_FAR)*s. So just one LUT of s.

Let's do lutS[i] = s at t=i/N. Then interpolate s.

```js
function depthAt(y) {
  let f = y * INV_STEP;  // INV_STEP = LUT_N/FIELD_D
  ...
  return s;
}
```

Then:
```js
function toScreen(x, y) {
  const s = depthAt(y);
  const sc = S_FAR + (S_NEAR-S_FAR)*s;
  return [view.cx + (x - FIELD_W*0.5)*view.k*sc, view.horizon + view.fieldH*s];
}
```

Calling a function that returns an array allocates. Let's inline in hot loops.

Alright, let's write the render function.

```js
function render() {
  ctx.drawImage(bgCanvas, 0, 0, W, H);   // bgCanvas is in device px; scale
  ...
}
```
Wait, bgCanvas has width = W*DPR. If I drawImage with dest w=W, h=H, and ctx has the DPR transform, the result is correct. Yes: ctx.setTransform(DPR,0,0,DPR,0,0), then drawImage(bg, 0,0,W,H) maps the DPR-sized bitmap to W×H CSS px → correct.

Hmm, but that's a scaling operation each frame, which can be slower than a direct 1:1 blit. Alternative: set the transform to identity for the background blit and use drawImage(bg, 0, 0). Then restore the DPR transform. Let's do:

```js
ctx.setTransform(1,0,0,1,0,0);
ctx.drawImage(bgCanvas,0,0);
ctx.setTransform(DPR,0,0,DPR,0,0);
```

Good.

Now, drawing units. Sort by y ascending (far first).

```js
// build render list
renderList.length = 0;
for (const u of units) if (u.alive) renderList.push(u);
renderList.sort((a,b) => a.y - b.y);
```

Allocating a new array each frame — let's keep a persistent array and set length=0. Sort is in-place. Good.

Then:
```js
for (let i=0;i<renderList.length;i++) {
  const u = renderList[i];
  const s = depthAt(u.y);
  const sc = S_FAR + (S_NEAR-S_FAR)*s;
  const px = view.cx + (u.x - FIELD_W*0.5)*view.k*sc;
  const py = view.horizon + view.fieldH*s;
  const size = UNIT_PX * view.k * sc;   // UNIT_PX = 30 world units
  // sprite selection: rotation frame based on velocity angle, walk frame based on time
  ...
  ctx.drawImage(sprite, px - size*0.5, py - size*0.5 - bob, size, size);
}
```

The sprite canvas is 48x48 with the unit centered; drawing at `size` where size = the unit's world diameter in px. But the sprite includes margin. Let's make the sprite fill its canvas with the unit drawn to the edges... Let's just say the sprite covers a square of side D_world = 36 world units, so size = 36 * k * sc. The unit body itself is ~30 units within it.

Let's set SPRITE_WORLD = 36.

Rotation frames: 16 angles. Determine the facing angle from velocity, or from the vector to the target. Index = ((angle/(2π))*16 + 0.5) & 15.

Since units in a charge all face the same way, this is cheap. In melee, units rotate. Fine.

Sprite selection: sprites[side][rotFrame]. Precompute 2 × 16 sprites. Also maybe 2 walk poses → 64 sprites. Let's include a slight leg animation... at 13px, it won't be visible. Let's skip walk poses and instead add a subtle bob offset based on time and unit phase during the charge/celebration.

Actually, a bob would look like they're marching. Nice touch: bobAmount = |sin(time*10 + phase)| * 2 world units during the charge, and bigger during celebration.

But bobbing in a top-down view is a vertical jump in screen space. Since it's a "slight perspective" from above, a vertical jump translates to a screen-space y offset. Yes, apply as a screen offset.

OK. Also for the celebration, maybe raise weapons — just use a different sprite set (arms up). Let's skip; the bob + particles is enough.

Actually let's add a "cheer" sprite variant: a sprite with the weapon raised. Eh, keep it simple — bob + sparkles.

Hmm, let me add something to make the victory read clearly: winners converge toward the center and bob, with golden sparkles, and a big "VICTORY" banner on the canvas. Plus the losing side's corpses remain. That should read well.

Alright, let's also add the flash effect: when hit, draw the sprite tinted white. Tinting requires a second sprite or globalCompositeOperation. Simplest: draw the sprite, then draw a white ellipse over it with low alpha. Or: use a separate "hit" sprite that's white. Let's pre-render a white silhouette version for each rotation frame. Then if u.flash > 0, draw the white version on top with alpha = flash.

That's 16 more sprites per side = 32 more. Total 64 sprites. Fine.

Simplify: pre-render for each side and rotation: [normal, white]. So sprites[side][rot] = {n: canvas, w: canvas}.

OK, let's now write the sprite generator.

```js
const SPR_SIZE = 48;
const ROT_N = 16;

function makeUnitSprites(sideIdx) {
  const col = SIDES[sideIdx];
  const arr = [];
  for (let r=0;r<ROT_N;r++) {
    const ang = r/ROT_N * Math.PI*2;
    arr.push({
      n: drawSoldier(col.body, col.mid, col.head, col.weapon, ang, false),
      w: drawSoldier('#ffffff', '#ffffff', '#ffffff', '#ffffff', ang, true)
    });
  }
  return arr;
}
```

Hmm, drawing a white silhouette: just draw everything white with a slight alpha.

drawSoldier(bodyCol, midCol, headCol, weaponCol, ang, silhouette):

```js
function drawSoldier(bodyCol, midCol, headCol, weaponCol, ang, silhouette) {
  const S = SPR_SIZE;
  const c = document.createElement('canvas');
  c.width = S; c.height = S;
  const g = c.getContext('2d');
  g.translate(S/2, S/2);
  g.rotate(ang);
  // shadow
  if (!silhouette) {
    g.fillStyle = 'rgba(0,0,0,0.30)';
    g.beginPath(); g.ellipse(0.5, 2.5, 12, 9.5, 0, 0, 6.3); g.fill();
  }
  // body (torso) - elongated along facing
  g.fillStyle = bodyCol;
  g.beginPath(); g.ellipse(0, 0, 11, 8, 0, 0, 6.3); g.fill();
  // shoulders
  g.fillStyle = midCol;
  g.beginPath(); g.ellipse(-1.5, 0, 8, 6.5, 0, 0, 6.3); g.fill();
  // head/helmet
  g.fillStyle = headCol;
  g.beginPath(); g.arc(2.5, 0, 5, 0, 6.3); g.fill();
  // weapon (spear/sword)
  if (!silhouette) {
    g.strokeStyle = weaponCol;
    g.lineWidth = 2;
    g.beginPath(); g.moveTo(6, 5.5); g.lineTo(19, 2); g.stroke();
  } else {
    g.fillStyle = '#fff';
  }
  return c;
}
```

Hmm, the weapon line goes to x=19 which is within the 24 half-size. Good. The ellipse rx=11 fits within 24. Shadow ellipse rx=12 + offset 2.5 → 14.5 < 24. Good.

For the silhouette (hit flash), just draw everything white. But the shadow should not be white. Let's put the shadow only in the normal sprite, and in the white sprite, draw white shapes with no shadow. Then when flashing, draw the white sprite on top of the normal one with alpha. The shadow would still be visible underneath. Good.

Now, the sprite covers a world box of, say, 40 world units (since the drawing extends to ~19+ in a 48px canvas, where the "unit" is about 28px of the 48). Scale: if SPR_SIZE=48 canvas represents SPR_WORLD world units, then the unit's actual body (22px) represents 22/48 * SPR_WORLD world units. For the body to be ~30 world units, SPR_WORLD = 65. Hmm.

Let's define: the sprite canvas represents a world square of size SPR_WORLD = 60 world units. Body ellipse rx=11px → 11/48*60 = 13.75 world units radius → 27.5 diameter. Good, matches ~UNIT = 30.

So dest size in px = SPR_WORLD * view.k * sc = 60 * 0.435 * 1.15 = 30px at the near edge. And the body would be 27.5 * 0.435 * 1.15 = 13.75 px. Good.

At the far edge: 60*0.435*0.55 = 14px sprite, body 6.9px. Fine.

OK.

Now, particle rendering: simple circles. Let's use ctx.fillRect for speed — small squares look fine for dust/blood at that scale. Actually blood puffs as circles look better. 800 arcs/frame... it's ~2ms. Let's use fillRect for tiny ones. Meh, let's use arcs with a single path batch per color? Different alphas per particle make batching hard.

Alternative: use a pre-rendered soft dot sprite and drawImage with globalAlpha. drawImage + setting globalAlpha per particle is fast-ish.

Let's just use fillRect with per-particle alpha via... hmm, fillStyle changes per particle are the expensive part.

Simplify: use a fixed set of colors (blood red at 3 alpha levels, dust at 3 levels) — no, still per-particle.

Honestly, 400 particles with beginPath+arc+fill is fine (~2-3ms). Let's cap particles at 400. Or use fillRect without beginPath: ctx.fillStyle = color; ctx.fillRect(x,y,s,s); That's very fast. Small squares read as dust/blood at 3-6px. Let's use fillRect and accept the blocky look — it's a "puff" anyway. Actually for blood, let's use circles only for the stain (drawn once into bg).

Hmm, let me just do: particles drawn as small rects with rotation-free sizing. Should look fine.

Let's set particle sizes 1-3 px. With 400 particles, ~0.5ms. Good.

Wait, but the particles need to be projected. Let's compute s = depthAt(p.y) per particle.

OK, let's write the whole thing now.

One more thing: the blood stain on death. Draw into bgCtx:
```js
function addStain(x, y) {
  const s = depthAt(y);
  const sc = S_FAR + (S_NEAR-S_FAR)*s;
  const px = view.cx + (x - FIELD_W*0.5)*view.k*sc;
  const py = view.horizon + view.fieldH*s;
  const r = (5 + Math.random()*7) * view.k * sc;
  bgCtx.globalAlpha = 0.5 + Math.random()*0.3;
  bgCtx.fillStyle = '#3a0d0d';  // dark red
  bgCtx.beginPath();
  bgCtx.ellipse(px, py, r*1.4, r*0.7, 0, 0, 6.3);
  bgCtx.fill();
  bgCtx.globalAlpha = 1;
}
```
Note bgCtx has the DPR transform set, so coordinates are in CSS px. Good.

Hmm, one issue: this draws on top of the grass, and the grass tufts are drawn... it's fine.

But 1000 stains drawn over the course of the battle — each is a fill on the bg canvas, that's fine (they accumulate onto the bitmap, cheap).

Now, the main loop with fixed timestep or variable dt?

Use requestAnimationFrame with dt clamped to 1/30 max, and use a fixed sim step of 1/60 with accumulator for stability. Let's do:

```js
let last = performance.now();
let acc = 0;
const FIXED = 1/60;
function frame(now) {
  requestAnimationFrame(frame);
  let dt = (now - last)/1000; last = now;
  if (dt > 0.25) dt = 0.25;
  acc += dt;
  let steps = 0;
  while (acc >= FIXED && steps < 4) { step(FIXED); acc -= FIXED; steps++; }
  render();
}
```

Hmm, with the sim at 60Hz fixed, and rendering every frame. Good.

But if the display is 120Hz, we do 2 renders per sim step. Fine.

Performance: 1000 units, and step() runs possibly twice per frame. Should still be OK.

Let's consider making the sim step 1/60 and just stepping once per rAF. Simpler. Let's do the accumulator with max 2 steps.

Alright. Let's write the code.

Also, I want the units to be staggered in depth so the charge looks like a wave. Add a per-unit speed variation and starting y-offset.

Let me now handle phase timing:
- t = 0: battle starts, phase = 'charge'.
- When units engage, it becomes 'melee' automatically (we can detect when the total engaged count > some threshold).
- When one side is wiped (or below ~3% and the other has more), phase = 'victory'.
- Victory lasts 5.5s, then reset.

Battle duration estimate: ~15-25s. Then 5.5s victory → total cycle ~25-30s. The requirement says everything important within the first 30 seconds. So the first battle should resolve by ~20s and the victory should be visible by ~25s. Let's make sure the battle is fast enough.

Let me tune the combat for a ~14-18s battle:
- damage 20-28, interval 0.28-0.40, hp 100 → 4-5 hits.
- In melee, a unit is attacked by multiple enemies (up to 3-4 in contact). So it dies in ~1-2 seconds once fully engaged.

With 500 per side, the first contact has ~50 engaged per side (the front line, 25 wide × 2 deep?). Actually the front line is 25 wide, and with jostling, maybe 50-75 units per side get into contact within a second.

Kill rate ≈ engagedUnits / 1.5s. At 75 engaged → 50 kills/s. From 500 to 0 in 10s. Plus the 4s charge. Total ~14s. 

But as units die, the engagement stays high. So maybe 15-20s total. Good.

Hmm, but the survivors of the winning side still need to find the remaining enemies. Should be fine.

Let me add a safety: after 25s, scale damage up by (1 + (t-25)*0.3). This guarantees resolution.

Actually, better to make the "front" wider to get more engagement early. With 25 columns and the field being 3200 wide... the formations are only 720 wide. Let's make it 40 cols × 12.5 rows... 500 = 25×20 or 50×10 or 40×12.5. Let's use 50×10: 50 cols × 10 rows = 500. Width = 49*30 = 1470, depth = 9*42 = 378.

Hmm, width 1470 out of FIELD_W 3200. Red from x=175 to 1645? That's more than half. Let's place red centered at x=550, so from x=-185 to 1285... negative. Bad.

Let's use a narrower spacing: 50 cols × 24 spacing = 1176 wide. Still wide.

Alternative: make the field wider (FIELD_W = 4000) and units smaller. Hmm.

Let's reconsider. The visual: two armies facing each other across a field. A wide front line is dramatic. Let's do 500 units in a 50 wide × 10 deep formation with x-spacing 22 and y-spacing 34.

Width = 49*22 = 1078. Depth = 9*34 = 306.

Red center at x = 1000 → spans 461 to 1539. Blue center at x = 2400 → spans 1861 to 2939. With FIELD_W = 3400: red spans 461..1539, blue 1861..2939. Gap = 322. Hmm, too close.

Let's set FIELD_W = 4000, red center 1100 (spans 561..1639), blue center 2900 (spans 2361..3439). Gap = 722. Good.

But then the field is wider than the screen at near scale... With view.k = W/(FIELD_W*S_NEAR), the near edge spans the full width. So FIELD_W=4000 → k = W/(4000*1.15) = W/4600. For W=1600, k = 0.348. Unit screen size: 60 * 0.348 * 1.15 = 24 px near, 60*0.348*0.55 = 11.5 px far.

Body diameter: 27.5 world * 0.348 * 1.15 = 11 px near. Reasonable.

Spacing 22 world units → 22*0.348*1.15 = 8.8 px near. So units at 11px wide with 8.8px spacing → overlapping.

Hmm. Let's increase spacing to 34 and reduce columns. 

Let's try: 500 units, formation 25 wide × 20 deep, spacing 34 x 40.
Width = 24*34 = 816, depth = 19*40 = 760.

FIELD_W = 4000, FIELD_D = 1600.
Red center x = 900 → spans 492..1308
Blue center x = 3100 → spans 2692..3508
Gap = 2692 - 1308 = 1384. Closing speed ~280/s → 4.9s. A bit long but OK for a "charge". Let's increase speed to 170 → closing 340 → 4s. Good.

Front line width = 816 world units → 816*0.348*1.15 = 327 px at near. Visually a decent line.

Hmm, the two armies are 816 wide out of a 4000-wide field, so they occupy the middle. That's fine and looks like two blocks charging.

With only 25 units on the front line, the initial engagement is 25 pairs. Kill rate ~25/1.5 = 17/s. 500 kills in 30s. Too slow!

Hmm. Unless units behind can... no, only the front line fights.

Wait, actually with units 11px wide at 8.8px spacing... they're basically shoulder to shoulder. In a melee, the front line becomes a scrum. The units behind the front line target enemies too and push forward, and the separation forces spread them.

Hmm, but they can't reach the enemy through their own line.

Let me reconsider: make the formation deeper and narrower? No — the front width determines the engagement.

The key insight: the number of simultaneous engagements ≈ front width / unit width. To kill 1000 units in ~15s, we need ~67 kills/s, meaning ~100 engaged pairs at any time (at 1.5s per kill).

So the front needs to be ~100 units wide. With unit spacing ~22 world units, that's 2200 world units of front. FIELD_W = 4000 → the front spans over half the field. That's actually dramatic and fine!

Formation: 100 wide × 5 deep = 500. Width = 99*22 = 2178. Depth = 4*40 = 160. Hmm, very thin.

Or 100 wide × 5 deep with depth spacing 50 → 200 deep. Thin line.

Hmm, a thin line means the armies look like lines. That's actually how battles look from above! Two long battle lines.

But "formation breaks apart into chaotic melee" — a line breaking into a scrum is good.

Alternatively: it's fine if the battles take a bit longer and the front line widens as the melee spreads. Let's compromise: 

Formation: 50 wide × 10 deep, spacing x=26, y=36.
Width = 49*26 = 1274. Depth = 9*36 = 324.

Front engagement initially: 50 units. Kill rate: 50/1.5 = 33/s → 1000 units in 30s. Hmm.

But as the melee develops, the flanks wrap around and more units engage. Also, units at the front die and are replaced by the ones behind, so the engagement stays at ~50-70.

Let's boost the kill rate: reduce time-to-kill. If a unit dies in 0.7s of focused combat, then 50 engaged → 70 kills/s → 1000 in 14s. 

TTK = 0.7s means: with an attack interval of 0.35s and damage 40 with hp 100 → 3 hits = 1.05s. Or damage 50, 2 hits = 0.7s.

Hmm, 2 hits to kill feels too fast/arcadey, but visually it's fine — units fall quickly.

But actually, in a scrum, a unit is attacked by 2-3 enemies simultaneously, so it takes ~1/3 the time. So damage 25, hp 100, interval 0.3 → 4 hits each, but 3 attackers → dies in ~0.4s. 

Hmm, that might be too fast and the battle ends in 8 seconds.

Let's aim: TTK in the scrum ≈ 1.2s. Then 50 engaged pairs → 42 kills/s → 1000 units in 24s. Still slowish.

Ugh, let's just make the front line wider. Let's go with:

Formation: 40 wide × 12.5 → not integer. 50 wide × 10 deep.

And overlap: spacing x = 30, y = 34. Width = 49*30 = 1470. Depth = 9*34 = 306.

Front engagement = 50 units per side (the front row). Plus the second row can sometimes reach. Say 60.

With TTK ~1.0s in the scrum: 60 kills/s → 1000 in 16.7s. Plus 4s charge = 21s. Then victory at ~21-25s. Within 30s. 

But the losing side's last units take time to find. As one side shrinks, the other surrounds them and it accelerates. Should be fine.

Let's also add: after 20s, a "frenzy" multiplier that increases damage by 5%/s. This guarantees it ends.

And the victory phase: 5s. Total ~27s. Cutting it close to 30s.

Let's make the victory phase 4s and aim for the battle to end by ~20s. I'll tune: hp 100, damage 30, interval 0.32. That's 4 hits. With ~2 attackers on average → ~0.64s TTK. 60 engaged → 94 kills/s → too fast (10s).

Hmm, hard to predict. Let me just pick reasonable middle values and add the frenzy accelerator, and test mentally.

Actually let's think again about the front. In a scrum, the attacking units are those in contact. The front line is 50 wide, but the second row is right behind (34 world units back) and the third row behind that. In the melee, the lines interpenetrate. Realistically, 2-3 rows deep get involved on each side = 100-150 units per side engaged.

So kill rate ≈ 125 / TTK_per_unit. With TTK = 2s (multiple attackers, ~1.5s), kill rate ≈ 80/s. 1000 units → 12.5s.

OK, that's in the right ballpark. Let's go with:
- hp: 100
- damage: 18-26
- interval: 0.30-0.45
- So one attacker needs ~5 hits ≈ 2s. With 2 attackers, ~1s.

Front + reserves engaged: growing over time. I'll just tune by feel and add the frenzy.

I'll set the frenzy to start at t=15s: dmgMul = 1 + max(0, t-15)*0.15. At t=25, mul = 2.5. This ensures termination.

Also, I realize: to make the battle visually interesting, the melee should stay spread out. Fine.

Let me just write it and trust the tuning is roughly right.

Actually, one more consideration: rather than a strict front line, I could have units target the nearest enemy which, for back-row units, is a front-row enemy that's already engaged. They'll push in. The separation forces will make the back rows spread around the flanks. That creates the "chaos" we want.

Okay, writing the code for real now.

```js
// ============ Setup ============
const cv = document.getElementById('cv');
const ctx = cv.getContext('2d', {alpha:false});

const SIDES = [
  { name:'CRIMSON HOST', body:'#c0392b', mid:'#8e2a20', head:'#e8c9a0', weapon:'#d8d8d8', ui:'#ff6b5e' },
  { name:'AZURE LEGION', body:'#2f6fc4', mid:'#1d4a8c', head:'#e8c9a0', weapon:'#d8d8d8', ui:'#67a9ff' }
];
```

Wait, the head should be a helmet, not skin, for a distant view. Let's use a metallic helmet: '#cfd6de'. And a colored plume maybe. Keep it: helmet color light grey-blue for both.

Actually, to distinguish sides at a glance even at small sizes, the body color is the key. Red vs blue. Good.

Let's write it all out.

```js
const CFG = {
  FIELD_W: 4000,
  FIELD_D: 1600,
  S_FAR: 0.55,
  S_NEAR: 1.15,
  PERSP: 1.35,
  SPRITE_WORLD: 60,
  UNIT_HALF: 20,        // separation radius basis
  SEP: 34,
  REACH: 40,
  N_PER_SIDE: 500,
};
```

Hmm, COLLECT: separate constants.

Let me write it out linearly.

```js
// ---------- Canvas & view ----------
const cv = document.getElementById('cv');
const ctx = cv.getContext('2d', { alpha: false });
let W, H, DPR;

const FIELD_W = 4000, FIELD_D = 1600;
const S_FAR = 0.55, S_NEAR = 1.15, PERSP = 1.35;

const view = { cx:0, horizon:0, fieldH:0, k:1 };

// depth LUT
const LUT_N = 512;
const lut = new Float32Array(LUT_N+1);
const INV_STEP = LUT_N / FIELD_D;
function buildLUT() {
  for (let i=0;i<=LUT_N;i++) lut[i] = Math.pow(i/LUT_N, PERSP);
}
buildLUT();

function depthS(y) {
  let f = y * INV_STEP;
  if (f <= 0) return 0;
  if (f >= LUT_N) return 1;
  const i = f|0;
  return lut[i] + (lut[i+1]-lut[i])*(f-i);
}
```

Then:
```js
function pxOf(x,y,s) { return view.cx + (x - FIELD_W*0.5) * view.k * (S_FAR + (S_NEAR-S_FAR)*s); }
function pyOf(s) { return view.horizon + view.fieldH * s; }
```

OK. Let me write the full file now.

Also, HUD: I'll use DOM elements overlaid, with CSS.

Let me write out the HTML:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mass Battle</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  html, body { width:100%; height:100%; overflow:hidden; background:#0b0e0a; }
  canvas { display:block; position:absolute; inset:0; }
  #hud { position:absolute; inset:0; pointer-events:none; font-family: Georgia, 'Times New Roman', serif; }
  ...
</style>
```

Fonts: no external fonts, use system serif/sans.

HUD layout:
- Top center: title (battle name) with a subtitle.
- Top left: red counter; top right: blue counter.
- Center: big "VICTORY" text during the victory phase, fading in.

Let's write the CSS:

```css
#title { position:absolute; top:14px; left:0; right:0; text-align:center; color:#f0e6d2; font-size:clamp(18px,3vw,34px); letter-spacing:.18em; text-transform:uppercase; text-shadow:0 2px 12px #000, 0 0 30px rgba(255,180,80,.35); }
#sub { position:absolute; top:calc(14px + clamp(22px,3.4vw,40px)); left:0; right:0; text-align:center; color:#b9a882; font-size:clamp(10px,1.2vw,14px); letter-spacing:.35em; text-transform:uppercase; }
.counter { position:absolute; top:18px; ... }
```

Hmm, "top:18px" collides with the title. Let's put counters below the title, or in the corners at a lower position.

Layout: title at top center. Counters at top-left and top-right, aligned vertically with the title's baseline area but pushed to the sides.

Let's do: title at top ~16px centered. Counters at top ~16px, left 24px and right 24px. On wide screens no collision. On narrow screens they'd overlap. Acceptable.

Counter design:
```html
<div class="counter left">
  <div class="num" id="redN">500</div>
  <div class="lbl">CRIMSON HOST</div>
</div>
```
with a bar showing the proportion.

Let's include a health bar: a horizontal bar showing the fraction of the army remaining. Nice touch.

```html
<div class="army left">
  <div class="n"><span id="redN">500</span></div>
  <div class="nm">CRIMSON HOST</div>
  <div class="bar"><i id="redBar"></i></div>
</div>
```

CSS for the bar: width 140px, height 6px, background rgba(255,255,255,.15), inner bar colored.

OK.

Victory banner:
```html
<div id="banner"><span id="bannerText">VICTORY</span></div>
```
Centered, opacity 0 → 1.

Now the JS.

Let me write the whole thing carefully.

```js
(function(){
'use strict';

// ---------- Canvas ----------
const cv = document.getElementById('cv');
const ctx = cv.getContext('2d', { alpha:false });

const FIELD_W = 4000, FIELD_D = 1600;
const S_FAR = 0.55, S_NEAR = 1.15, PERSP = 1.35;
const SPRITE_WORLD = 62;

let W=0, H=0, DPR=1;
const view = { cx:0, horizon:0, fieldH:0, k:1 };

const LUT_N = 512;
const lut = new Float32Array(LUT_N+1);
const INV_STEP = LUT_N / FIELD_D;
for (let i=0;i<=LUT_N;i++) lut[i] = Math.pow(i/LUT_N, PERSP);

function depthS(y){
  const f = y * INV_STEP;
  if (f <= 0) return 0;
  if (f >= LUT_N) return 1;
  const i = f|0;
  return lut[i] + (lut[i+1]-lut[i])*(f-i);
}
```

Hmm, `lut[i+1]` when i = LUT_N-1 is fine. And f >= LUT_N returns 1. Good.

Actually, `f` could be exactly LUT_N-0.5 → i = LUT_N-1, i+1 = LUT_N. OK.

Now units.

```js
const units = [];
const renderList = [];
let time = 0;
let phase = 'charge';   // 'charge' | 'melee' | 'victory'
let phaseT = 0;
let winner = -1;
let battleNo = 0;
```

Battle name generator:

```js
const PLACES = ['Emberfield','Ashvale','Redmoor','Ironwood','Greyhollow','Thornmere','Blackford','Stormgate','Duskdale','Karrowfen','Bleakwater','Highmoor','Ravenmoor','Coldhollow','Grimsby Field','Stonewatch','Fenmarch','Duskwater','Oakhollow','Wyrm's Rest'];
const PREFIX = ['The Battle of','The Fields of','The Clash at','The Siege of','The Slaughter at','The Rout of'];
```

Careful with the apostrophe in 'Wyrm's Rest' inside a single-quoted string. Use double quotes or escape.

Let's write:
```js
const PLACES = ["Emberfield","Ashvale","Redmoor","Ironwood","Greyhollow","Thornmere","Blackford","Stormgate","Duskdale","Karrowfen","Bleakwater","Highmoor","Ravenmoor","Coldhollow","Stonewatch","Fenmarch","Oakhollow","Wyrmrest","Gallowmere","Dreadfen"];
const PREFIX = ["The Battle of","The Fields of","The Clash at","The Siege of","The Slaughter at","The Rout of"];
```

Battle name = prefix + place, chosen pseudo-randomly with the battle number, avoiding immediate repeats.

Now setting up the armies:

```js
const N_SIDE = 500;
const COLS = 50, ROWS = 10, SPACING_X = 30, SPACING_Y = 34;
```
Wait, 50*10 = 500. Width = 49*30 = 1470. Hmm, with FIELD_W=4000 and the near-edge x scale... at the near edge, 1470 * k * 1.15 where k = W/(4000*1.15) = W/4600. So 1470 * (W/4600) * 1.15 = 1470*W/4000 = 0.3675*W. So the formation is 37% of the screen width. Good.

Depth: 9*34 = 306 world units out of 1600. The vertical screen extent: from s(490) to s(796)... Let's compute: units at y from 650 to 956 (centered at 800). Hmm, FIELD_D = 1600, center y = 800.

s(y) = (y/1600)^1.35. At y=647: (0.404)^1.35 = e^(1.35*ln0.404) = e^(1.35*(-0.906)) = e^(-1.223) = 0.294. At y=953: (0.596)^1.35 = e^(1.35*(-0.517)) = e^(-0.698) = 0.497.

Screen y = horizon + fieldH*s. With horizon=0.16H, fieldH=0.78H: y1 = 0.16H+0.78H*0.294 = 0.389H; y2 = 0.16H+0.78H*0.497 = 0.548H. So the formation occupies vertical 0.389H to 0.548H — only 16% of the screen height. Too small vertically!

The whole field spans 0.16H to 0.94H = 78% of the height, but the units only occupy 16%. They'd look like a thin horizontal line.

Hmm. I need the armies to occupy more vertical space. Let's increase the depth spacing: ROWS=10, spacing_y = 90 → depth 810. Then y from 800-405=395 to 800+405=1205.

s(395) = (0.247)^1.35 = e^(1.35*(-1.398)) = e^(-1.887) = 0.152. Screen y = 0.16H + 0.78H*0.152 = 0.279H.
s(1205) = (0.753)^1.35 = e^(1.35*(-0.284)) = e^(-0.383) = 0.682. Screen y = 0.16H + 0.78H*0.682 = 0.692H.

So from 0.279H to 0.692H = 41% of the height. Better!

But spacing_y = 90 means the rows are far apart. That's fine — 10 rows spread over the field depth.

Hmm, but then the formation is 1470 wide × 810 deep. That's a proper block. 

Actually, maybe fewer rows and more depth spacing looks better. Let's do ROWS = 10, spacing 90. Or 12 rows × 42 = 462 deep. Hmm.

Let's go with COLS=50, ROWS=10, SPACING_X=30, SPACING_Y=88. Depth = 9*88 = 792.

Actually wait, I should double check the visual density. At the near edge, 30 world units of x-spacing maps to 30*k*1.15 px = 30*W/4000 = 0.0075W px. For W=1600, that's 12px. And the unit's screen width is ~11px. So they're just touching. Good.

At the far edge, s is smaller so everything scales down proportionally. Good.

Depth spacing 88 world units at s≈0.5 → screen spacing = (projY difference) ... row separation in screen = fieldH * (s2 - s1). For 88 world units around y=800: ds/dy = 1.35 * (y/1600)^0.35 / 1600. At y=800: (0.5)^0.35 = 0.785. ds/dy = 1.35*0.785/1600 = 0.000662. Times 88 = 0.0583. Times fieldH (0.78H) = 0.0455H. For H=900, that's 41px. And the unit's screen height at that depth: 62 * k * s = 62 * 0.348 * 0.5... wait k = W/4600 = 0.348 for W=1600. 62*0.348*0.51 = 11px. So rows are 41px apart with 11px units → very spread out.

Hmm, that's too spread out. The formation would look like a sparse grid.

Let's reduce spacing_y. The screen has to fit ~10 rows in a reasonable vertical band. Let's target the formation occupying ~35% of the screen height with rows visually adjacent (spacing ≈ 1.5× unit height in screen px).

At the near edge, unit screen height = 62*k*1.15 = 62*0.348*1.15 = 24.8px. Hmm wait, k = W/4600 = 1600/4600 = 0.348. So unit screen size = 62 * 0.348 * s.

At maximum s=1 (near edge): 21.6px.
At s=0.5: 10.8px.

For rows to look adjacent at s=0.5, spacing in screen should be ~14px. That means ds = 14/(0.78*900) = 0.02. dy = 0.02/0.000662 = 30 world units.

So spacing_y ≈ 30 world units near the middle. Then 10 rows = 270 world units deep. Screen extent: ds over 270 units ≈ 0.000662*270 = 0.179 (nonlinear, but roughly). Screen: 0.179*0.78H = 0.14H = 126px. That's a thin band.

So with a 50×10 formation and reasonable spacing, the army is a wide, shallow block. That's realistic for a battle line, but visually thin.

Alternative: make the armies deeper (more rows) and narrower (fewer columns), e.g., 25 cols × 20 rows. Width = 24*30 = 720, depth = 19*30 = 570.

Screen: width 720*0.348*1.15 = 288px at near. Depth: ~0.000662*570 = 0.377 ds → hmm let me compute properly.

y from 800-285=515 to 800+285=1085.
s(515) = (0.322)^1.35 = e^(1.35*(-1.133)) = e^(-1.530) = 0.2165
s(1085) = (0.678)^1.35 = e^(1.35*(-0.389)) = e^(-0.525) = 0.5916
Screen: 0.16H + 0.78H*0.2165 = 0.329H, and 0.16H + 0.78H*0.5916 = 0.621H.
Band = 0.292H = 263px for H=900. 

Width on screen: 720 * k * s. At s=0.4 (middle), 720*0.348*0.4 = 100px. Hmm, narrow.

So a 25×20 block is 100px wide × 263px tall on screen — a vertical column. Not great either.

The issue: the perspective compresses depth heavily. The field is 4000 wide × 1600 deep in world units, but on screen the depth maps to 78% of the height and the width maps to ~100% of the width. So world aspect 4000:1600 = 2.5:1 vs screen aspect ~ (1600px wide × 700px tall field) = 2.3:1. Actually similar!

Hmm, but the perspective compresses the far region. Let me reconsider: the field's screen dimensions: width varies from W*0.478 (far) to W (near); average ~0.74W. Height 0.78H. For W=1600, H=900: average width 1184, height 702. Aspect 1.69:1 on screen vs 2.5:1 in world. So the world is stretched vertically on screen by 1.48×.

So a formation that's 1470 wide × 792 deep in world will appear roughly 1470/4000*1184 = 435px wide and 792/1600*702 = 347px tall (roughly, ignoring nonlinearity). That's a decent block! 

Wait, I think I made an error before. Let me redo: the world depth of 792 units out of FIELD_D=1600 is 49.5% of the depth. On screen, that maps to... but the mapping is nonlinear (t^1.35), so a centered band of ±24.75% of t maps to s values 0.2165 to 0.5916, a span of 0.375 in s, i.e., 0.375*0.78H = 0.29H = 263px for H=900.

And the width: 1470 world out of 4000 → 36.75% of the width. At s≈0.4, screen width = 1470 * k * 0.4 = 1470*0.348*0.4 = 205px. Hmm, that's much less than 435.

I think I mixed things up. Let me redo: at s=0.4, the field's screen width = FIELD_W * k * s = 4000*0.348*0.4 = 557px. But the screen is 1600px wide. So at s=0.4 (y≈690, which is above the middle), the field only occupies 557px of the 1600px screen width?

That can't be right. At s=1 (near edge, y=1600), the field width = 4000*0.348*1.15 = 1600px = W. ✓.

At s=0.2165 (y=515): field width = 4000*0.348*(0.55+0.6*0.2165) = 4000*0.348*0.680 = 946px.

Ah I see, I forgot the S_FAR base. projScale = S_FAR + (S_NEAR-S_FAR)*s = 0.55 + 0.6*s. At s=0.2165 → 0.680. At s=0.5916 → 0.905.

So at the far edge of the army (y=515), the field is 946px wide, and the army (1470/4000 of it) is 348px wide. At the near edge (y=1085), the field is 4000*0.348*0.905 = 1260px, army = 463px wide.

OK so the army block is about 400px wide and 263px tall on a 1600×900 screen. That's a reasonable-looking block. 

And the depth spacing: I computed the row separation at y=800 as 41px, while the unit is 11px tall. So they're spaced out. Hmm, that means the 10 rows spread over 263px = ~29px average spacing. Unit height ~11-21px. So the rows are about 1.5-2 unit-heights apart. That's actually fine — like a loose formation.

Hmm, when I computed 41px earlier I used ds/dy = 0.000662 at y=800 giving 88 units → 0.0583 ds → 0.0583*0.78*900 = 41px. And the unit at y=800 has s=0.5, so its screen size = 62*0.348*(0.55+0.6*0.5) = 62*0.348*0.85 = 18px. Oh right, I forgot the S_FAR base again. So units are 18px and rows are 41px apart. Still spread.

Fine — a loose formation. Or reduce spacing_y to 60 → rows 28px apart with 18px units. Better.

Let's use spacing_y = 64, 10 rows → depth 576. Then y from 512 to 1088.

OK. Let me finalize: COLS=50, ROWS=10, SX=30, SY=64. Formation 1470 × 576.

Positions:
Red center: (900, 800). x from 900-735=165 to 900+735=1635.
Blue center: (3100, 800). x from 2365 to 3835.

Gap = 2365 - 1635 = 730. Closing speed 2*150 = 300 → 2.4s. Good, snappy.

Hmm, but the blue army's right edge is at 3835, near FIELD_W=4000. And red's left edge at 165. So they span nearly the whole field. Width on screen at the near edge: 1470/4000*1600 = 588px each. Two of them = 1176px + gap. Total used ≈ most of the screen. OK.

Hmm, actually let me shift them: red center 800, blue center 3200. Red spans 65..1535, blue 2465..3935. Gap = 930. Closing 300/s → 3.1s. Fine.

Now, ROWS=10 and the field depth 1600 with the army at y 512..1088. Good.

Wait, I should double check that the units at y=512 (far) aren't too small. s(512) = (0.32)^1.35 = 0.2165. projScale = 0.68. Unit screen size = 62 * k * 0.68 = 62*0.348*0.68 = 14.7px. Fine.

At y=1088: s = (0.68)^1.35 = 0.59. projScale = 0.905. Size = 62*0.348*0.905 = 19.5px. Good, a modest perspective variation (14.7 → 19.5). That's "slight perspective". 

Now the field spans y=0 (top, s=0, projScale=0.55, size=62*0.348*0.55=11.9px) to y=1600 (s=1, projScale=1.15, size=24.8px). So the perspective variation across the whole field is 2x. "Slight" enough.

OK, good. Let's write the code.

One more: the enemy armies face each other. Red is on the left, so red units face right; blue faces left.

Let me write the initialization:

```js
function spawnArmies() {
  units.length = 0;
  for (let side = 0; side < 2; side++) {
    const cx = side === 0 ? 800 : 3200;
    let idx = 0;
    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        const x = cx + (c - (COLS-1)/2) * SX;
        const y = 800 + (r - (ROWS-1)/2) * SY;
        const u = makeUnit(side, x + rand(-4,4), y + rand(-6,6));
        units.push(u);
      }
    }
  }
  // initial targets: nearest mirrored enemy
  ...
}
```

For initial targets, I'll just compute them with the ring search fallback. Or set target = null and let the retarget handle it on the first frame with a full-scan fallback. To avoid a hitch, let's do the initial target assignment via a mirror: for red unit at index i (0..499) in red's list, target = blue unit at index i. Since both are laid out identically, the mirrored index gives the nearest-ish enemy.

Actually simplest: after creating all units, for each unit, find the nearest enemy by a full scan — but that's 500*1000 = 500k operations, once. That's ~5ms. Acceptable as a one-time cost. But it happens on every restart. Fine, 5ms once.

Hmm, actually 500k distance computations is maybe 2-3ms. Fine.

Let's just do it once at spawn.

Now the code for the unit update. Let me write it.

```js
function step(dt) {
  time += dt;
  phaseT += dt;
  
  if (phase === 'victory') {
    updateVictory(dt);
  } else {
    buildGrid();
    updateUnits(dt);
    buildGrid();   // rebuild after movement for combat accuracy
    combat(dt);
    compact();
  }
  updateParticles(dt);
  checkEnd();
}
```

Hmm, building the grid twice per step is 2*1000 inserts + 2*1200 clears. ~4400 ops. Negligible.

Actually, let me just build once at the start and use it for both. The movement per step is small. But combat after movement with stale positions might miss contacts. With REACH=40 and movement of ~2.5 units/step, it's fine. Let's build once at the start for simplicity... no wait, at spawn units are 730 apart, then they move, and the grid needs to be reasonably current. Building once per step at the start of the step uses positions from the end of the previous step — that's fine and standard.

I'll build once at the start of each step.

updateUnits:

```js
function updateUnits(dt) {
  const frenzy = 1 + Math.max(0, time - 16) * 0.14;
  for (let i=0;i<units.length;i++) {
    const u = units[i];
    u.cool -= dt;
    u.flash = Math.max(0, u.flash - dt*3.5);
    u.retargetT -= dt;
    let t = u.target;
    if (!t || !t.alive || u.retargetT <= 0) {
      u.target = findTarget(u);
      u.retargetT = 0.4 + Math.random()*0.5;
      t = u.target;
    }
    let dx = 0, dy = 0, d = 0;
    if (t) {
      dx = t.x - u.x; dy = t.y - u.y;
      d = Math.sqrt(dx*dx + dy*dy) || 1;
    } else {
      dx = u.side === 0 ? 1 : -1; dy = 0; d = 1;
    }
    const wantReach = u.reach * 0.7;
    let tx = 0, ty = 0;
    if (d > wantReach) {
      const sp = u.speed * (u.engaged ? 0.35 : 1);
      tx = dx/d*sp; ty = dy/d*sp;
    }
    // steering
    const k = Math.min(1, dt*7);
    u.vx += (tx - u.vx) * k;
    u.vy += (ty - u.vy) * k;
    u.x += u.vx * dt;
    u.y += u.vy * dt;
    // clamp
    if (u.x < 20) { u.x = 20; u.vx *= -0.2; }
    ...
    u.facing = ... 
  }
  // reset engaged for next frame
}
```

Wait, `u.engaged` is set during combat, which happens after movement. So during movement it reflects the previous frame's combat. That's fine.

But I need to reset engaged at the start of combat, then set it. Let's reset engaged at the beginning of the step (before movement), and set it during combat. So the movement uses last frame's engaged state. Good.

Hmm, but if I reset before movement and then combat sets it, the movement uses... let me re-order:
1. Reset engaged.
2. Move (uses engaged from the previous frame — but we just reset it!). 

Bad. Let me keep a separate `engaged` that's reset at the END of combat, so during movement it holds the previous frame's value. 

Order in step:
1. buildGrid
2. updateUnits (reads u.engaged from last frame)
3. combat (reads/writes u.engaged)  → but we need to clear it first.

Let's do: in combat, first clear all engaged flags, then set them. And in updateUnits, we read them before the clear. So the order works: updateUnits reads previous frame's engaged, then combat clears and recomputes. 

Now, the `flash` for hit feedback.

findTarget as described.

combat():

```js
function combat(dt) {
  const frenzy = 1 + Math.max(0, time - 16) * 0.14;
  for (let i=0;i<units.length;i++) units[i].engaged = false;
  for (let gy=0; gy<GH; gy++) {
    const rowBase = gy*GW;
    for (let gx=0; gx<GW; gx++) {
      const cell = grid[rowBase+gx];
      const n = cell.length;
      if (n === 0) continue;
      for (let i=0;i<n;i++) {
        const a = cell[i];
        if (!a.alive) continue;
        for (let j=i+1;j<n;j++) {
          const b = cell[j];
          if (!b.alive) continue;
          interact(a,b,frenzy);
        }
        // neighbors
        if (gx+1 < GW) { const c2 = grid[rowBase+gx+1]; for (let j=0;j<c2.length;j++){ const b=c2[j]; if(b.alive) interact(a,b,frenzy); } }
        if (gy+1 < GH) { const c2 = grid[rowBase+GW+gx]; for (let j=0;j<c2.length;j++){ const b=c2[j]; if(b.alive) interact(a,b,frenzy); } }
        if (gy+1 < GH && gx+1 < GW) { const c2 = grid[rowBase+GW+gx+1]; for (let j=0;j<c2.length;j++){ const b=c2[j]; if(b.alive) interact(a,b,frenzy); } }
        if (gy+1 < GH && gx-1 >= 0) { const c2 = grid[rowBase+GW+gx-1]; for (let j=0;j<c2.length;j++){ const b=c2[j]; if(b.alive) interact(a,b,frenzy); } }
      }
    }
  }
}
```

interact:

```js
const SEP = 30, SEP2 = SEP*SEP;
function interact(a, b, frenzy) {
  const dx = b.x - a.x, dy = b.y - a.y;
  const d2 = dx*dx + dy*dy;
  if (d2 > SEP2) return;
  const d = Math.sqrt(d2) + 1e-6;
  const nx = dx/d, ny = dy/d;
  const overlap = SEP - d;
  if (a.side === b.side) {
    const p = overlap * 0.12;
    a.x -= nx*p; a.y -= ny*p;
    b.x += nx*p; b.y += ny*p;
  } else {
    a.engaged = true; b.engaged = true;
    const p = overlap * 0.22;
    a.x -= nx*p; a.y -= ny*p;
    b.x += nx*p; b.y += ny*p;
    // slow them
    if (d < a.reach && a.cool <= 0) {
      a.cool = a.atkInt;
      hit(b, a.dmg * frenzy);
    }
    if (d < b.reach && b.cool <= 0) {
      b.cool = b.atkInt;
      hit(a, b.dmg * frenzy);
    }
  }
}
```

Hmm, the separation factor for enemies is 0.22 — with multiple neighbors, this could push them apart too much. Let's keep it low.

Actually, there's a subtlety: the enemy separation is applied every frame to both units, but each pair only pushes them apart by 0.22*overlap. With overlap up to 30, that's 6.6 units per frame. Too much! Let's use a smaller factor like 0.08 and cap the push.

Actually, the correct approach for positional constraint relaxation is to push by overlap*0.5 (fully resolve), but that's per-pair and with many pairs it over-corrects. A relaxation factor of 0.1-0.2 per pair works reasonably.

Since SEP=30 and units are ~27 world units wide, the overlap will typically be small (a few units). overlap*0.15 = 0.5 units per pair. With 5 pairs, 2.5 units of push per frame. That's fine and keeps them from clumping.

OK.

Also, I should cap the total separation by limiting the number of interactions... nah, it's fine.

hit():
```js
function hit(u, amount) {
  u.hp -= amount;
  u.flash = 1;
  if (u.hp <= 0) kill(u);
}
```

kill():
```js
function kill(u) {
  if (!u.alive) return;
  u.alive = false;
  u.deathTime = time;
  spawnBlood(u.x, u.y);
  addStain(u.x, u.y);
  counts[u.side]--;
}
```

compact():
```js
let w = 0;
for (let i=0;i<units.length;i++) if (units[i].alive) units[w++] = units[i];
units.length = w;
```

Hmm, but if units are killed during the combat loop, `grid` still references dead units. We check `if (!a.alive) continue` and `if (!b.alive) continue`. Good.

But after compacting, the grid is stale for the rest of the step. We rebuild at the start of the next step. Fine.

Wait, but the render pass uses `units`, which is now compacted. Good.

checkEnd():
```js
function checkEnd() {
  if (phase === 'victory') {
    if (phaseT > 5.0) resetBattle();
    return;
  }
  if (counts[0] <= 0 || counts[1] <= 0) {
    winner = counts[0] > 0 ? 0 : (counts[1] > 0 ? 1 : -1);
    phase = 'victory';
    phaseT = 0;
    showBanner(...);
  } else if (time > 26 && Math.random() < 0.002) {
    // force end
    winner = counts[0] > counts[1] ? 0 : 1;
    ...
  }
}
```

Hmm, forcing an end is hacky. Let's rely on the frenzy damage multiplier instead, which will naturally resolve things.

Also, if both sides hit 0 simultaneously (unlikely), pick the one with more... whatever.

Victory update: winner units converge, bob, spawn sparkles.

```js
function updateVictory(dt) {
  for (const u of units) {
    // move toward the center
    const tx = FIELD_W * 0.5 + (u.x - FIELD_W*0.5) * 0.0 ...
  }
}
```

Simpler: winner units drift toward the battlefield center with a gentle speed, and bob. Add cheering particles.

Let's do:
```js
for (const u of units) {
  u.cheer = (u.cheer || 0) + dt;
  // drift toward center
  const dx = FIELD_W*0.5 - u.x;
  const dy = FIELD_D*0.5 - u.y;
  const d = Math.hypot(dx,dy) || 1;
  if (d > 60) {
    u.x += dx/d * 60 * dt;
    u.y += dy/d * 60 * dt;
  }
  // shuffle
  u.x += Math.sin(time*3 + u.seed) * 12 * dt;
  u.y += Math.cos(time*2.7 + u.seed*1.3) * 12 * dt;
  // sparkles
  if (Math.random() < 0.02) spawnSparkle(u.x, u.y - 6);
  u.vx = 0; u.vy = 0;
}
```

And the render applies a bob: during victory, py -= |sin(time*6 + seed)| * 6 * sc... something.

Also, during victory, add dust puffs at the feet.

OK.

Now particles.

```js
const parts = [];
const MAX_PARTS = 700;
function addParticle(x,y,vx,vy,life,size,color,kind) {
  if (parts.length >= MAX_PARTS) parts.shift();  // shift is O(n)... use a ring or just overwrite
  ...
}
```

`shift()` is O(n) but n=700 and it happens rarely. Actually it could happen a lot during heavy combat. Let's instead overwrite the oldest by keeping an index pointer.

Simpler: if full, replace a random/first element:
```js
if (parts.length >= MAX_PARTS) { parts[0] = p; /* still O(1) but unordered */ }
```
Hmm, we need to overwrite some existing slot. Let's just do `parts[parts.length-1] = p`? No.

Let's use a simple approach: if full, `parts[(Math.random()*MAX_PARTS)|0] = p;` — replaces a random particle. Fine.

Actually cleanest: use an index cursor that wraps:
```js
let pIdx = 0;
function addParticle(...) {
  if (parts.length < MAX_PARTS) { parts.push(p); }
  else { parts[pIdx] = p; pIdx = (pIdx+1) % MAX_PARTS; }
}
```
But then when counting active particles, we need to check p.life > 0. Use a fixed-size array of MAX_PARTS with life=0 for inactive. Let's do that.

```js
const MAX_PARTS = 800;
const parts = [];
for (let i=0;i<MAX_PARTS;i++) parts.push({life:0,x:0,y:0,vx:0,vy:0,size:1,r:200,g:60,b:50,a:1,drag:0.9});
let pCursor = 0;
function emit(x,y,vx,vy,life,size,r,g,b,drag) {
  const p = parts[pCursor];
  pCursor = (pCursor+1) % MAX_PARTS;
  p.x=x;p.y=y;p.vx=vx;p.vy=vy;p.life=life;p.maxLife=life;p.size=size;
  p.r=r;p.g=g;p.b=b;p.drag=drag;
}
```

Then update:
```js
for (const p of parts) {
  if (p.life <= 0) continue;
  p.life -= dt;
  p.x += p.vx*dt; p.y += p.vy*dt;
  p.vx *= p.drag; p.vy *= p.drag;  // drag^dt ideally
  ...
}
```
Using a fixed drag per step at a fixed timestep is fine.

Render: for each active particle, project and fillRect.

Note: p.y might go below 0 or above FIELD_D. Clamp or let it be.

Also `parts` iteration for 800 particles each frame, plus rendering. Fine.

Let me set MAX_PARTS = 600.

spawnBlood(x,y): emit 8-12 particles with red colors, upward-ish velocity, various sizes.
spawnDust(x,y): emit 5-8 grey-brown particles.

Ok. Let's also emit a dust puff when units move fast? Maybe during the charge, emit dust from the feet occasionally. That adds atmosphere. Let's do: during charge, each unit has a 1% chance per frame to emit a small dust particle. With 1000 units at 60fps, that's 600 particles/sec — too many. Let's use 0.2% → 120/sec. Still a lot but the pool recycles. Hmm, it'd look like a dust cloud, which is actually cool for a charging army. Let's do 0.15% → 90/sec with a life of 1.2s → ~110 active. OK, acceptable. Let's cap it.

Actually, let's skip charging dust for performance and only emit dust on death and during the celebration. Hmm, but a charging army kicking up dust is great. Let's do a low rate (0.1% per unit per frame ≈ 60/sec at 60fps).

Alright.

Now rendering the units with sprites.

```js
const sprites = [];  // sprites[side][rot] = {n, w}
```

Build at load.

Render:

```js
function render() {
  // background
  ctx.setTransform(1,0,0,1,0,0);
  ctx.drawImage(bgCanvas, 0, 0);
  ctx.setTransform(DPR,0,0,DPR,0,0);
  
  // particles behind units? Let's draw particles after units for blood, but dust behind.
  // Simpler: draw all particles after units.
  
  // build sorted render list
  rl.length = 0;
  for (let i=0;i<units.length;i++) { const u = units[i]; if (u.alive) rl.push(u); }
  rl.sort((a,b) => a.y - b.y);
  
  for (let i=0;i<rl.length;i++) {
    const u = rl[i];
    const s = depthS(u.y);
    const ps = S_FAR + (S_NEAR - S_FAR) * s;
    const sx = view.cx + (u.x - FIELD_W*0.5) * view.k * ps;
    const sy = view.horizon + view.fieldH * s;
    const sz = SPRITE_WORLD * view.k * ps;
    
    let rot = u.rot;
    const sp = sprites[u.side][rot];
    let bob = 0;
    if (phase === 'victory') bob = Math.abs(Math.sin(time*7 + u.seed)) * 9 * view.k * ps * 3;
    // hmm, scale
    
    ctx.drawImage(sp.n, sx - sz*0.5, sy - sz*0.5 - bob, sz, sz);
    if (u.flash > 0.02) {
      ctx.globalAlpha = u.flash * 0.85;
      ctx.drawImage(sp.w, sx - sz*0.5, sy - sz*0.5 - bob, sz, sz);
      ctx.globalAlpha = 1;
    }
  }
  
  // particles
  ...
}
```

The bob amount: in world terms, a jump of ~15 world units → screen = 15 * view.k * ps. For k=0.348, ps=0.9 → 4.7px. Let's make it 20 world units → 6px. Visible. Good.

Let's set bob = Math.abs(Math.sin(time*6 + u.seed*6)) * 22 * view.k * ps.

Rotation: compute from velocity or facing. Let's store u.rot as an index 0..15 updated when moving.

In updateUnits: 
```js
if (d > 5) {
  let ang = Math.atan2(dy, dx);
  u.rot = ((ang + Math.PI*2) % (Math.PI*2)) / (Math.PI*2) * ROT_N | 0;
}
```
Hmm, for the sprite drawn facing +x, an angle of 0 → rot 0. Good.

But updating `rot` every frame based on velocity causes flickering when the velocity is near zero. Let's only update when the speed is above a threshold, and smooth it.

Let's just compute the rotation from the direction to the target (if any), which is stable.

Actually, let's update the rot only when the unit moves significantly, with the angle computed from the movement direction, and keep the last value otherwise. Fine.

Now, thinking about `ctx.drawImage` with a 48x48 source scaled to ~15x15 → smooth downscaling. Canvas does bilinear by default. Good.

Hmm, but 1000 drawImage calls with scaling — might be ~2-4ms. Acceptable.

Let's also consider `imageSmoothingQuality = 'low'` for speed. Default is fine.

Now the background builder:

```js
let bgCanvas = null, bgCtx = null;
function buildBackground() {
  bgCanvas = document.createElement('canvas');
  bgCanvas.width = Math.max(1, Math.floor(W*DPR));
  bgCanvas.height = Math.max(1, Math.floor(H*DPR));
  bgCtx = bgCanvas.getContext('2d');
  bgCtx.setTransform(DPR,0,0,DPR,0,0);
  
  // sky
  const skyH = view.horizon + 20;
  const sky = bgCtx.createLinearGradient(0,0,0,skyH);
  sky.addColorStop(0, '#1c2430');
  sky.addColorStop(0.55, '#4a5566');
  sky.addColorStop(1, '#8a8574');
  bgCtx.fillStyle = sky;
  bgCtx.fillRect(0,0,W,skyH);
  
  // distant hills
  bgCtx.fillStyle = '#2e3629';
  bgCtx.beginPath();
  bgCtx.moveTo(0, view.horizon+2);
  for (let x=0;x<=W;x+=W/24) {
    const h = view.horizon - 8 - Math.sin(x*0.013)*9 - Math.sin(x*0.041+2)*5;
    bgCtx.lineTo(x, h);
  }
  bgCtx.lineTo(W, view.horizon+2);
  bgCtx.closePath();
  bgCtx.fill();
  
  // field
  const fg = bgCtx.createLinearGradient(0, view.horizon, 0, view.horizon+view.fieldH+10);
  fg.addColorStop(0, '#3d4a2c');
  fg.addColorStop(0.35, '#55683a');
  fg.addColorStop(1, '#7d9450');
  ...
}
```

Hmm, for the field I want a gradient that follows the perspective. A simple vertical linear gradient is fine.

Then the trapezoid path. Let me build it:

```js
const farS = 0, nearS = 1;
const yFar = view.horizon, yNear = view.horizon + view.fieldH;
const psFar = S_FAR, psNear = S_NEAR;
const halfWFar = FIELD_W*0.5*view.k*psFar;
const halfWNear = FIELD_W*0.5*view.k*psNear;
```
Since view.k = W/(FIELD_W*S_NEAR), halfWNear = FIELD_W*0.5*W/(FIELD_W*S_NEAR)*S_NEAR = W*0.5. ✓ 

So the near edge spans exactly [0, W]. And the far edge spans cx ± W*0.5*S_FAR/S_NEAR = cx ± W*0.239.

Good.

Then:
```js
bgCtx.beginPath();
bgCtx.moveTo(view.cx - halfWFar, yFar);
bgCtx.lineTo(view.cx + halfWFar, yFar);
bgCtx.lineTo(W, yNear);
bgCtx.lineTo(0, yNear);
bgCtx.closePath();
bgCtx.fill();  // with the gradient
```

Wait, but the far corners are at (cx ± halfWFar, yFar) — this is the field's far edge at depth y=0. And the near edge at y=yNear spans the full width. Good.

Then draw grass tufts inside the clip.

Tufts: pre-generate a list of world positions. To make them look natural, place them with a bias toward the near region? Random uniform is fine, but the far region is compressed so tufts would be denser visually there. That's actually correct for perspective.

Generate ~900 tufts. Each is a tiny line or dot:
```js
for (const t of tufts) {
  const s = depthS(t.y);
  const ps = S_FAR + (S_NEAR-S_FAR)*s;
  const sx = view.cx + (t.x - FIELD_W*0.5)*view.k*ps;
  const sy = view.horizon + view.fieldH*s;
  const len = (3 + t.r*4) * view.k * ps * 3;
  ...
}
```
Hmm, `view.k * ps * 3`? Let's think: a grass tuft is ~8 world units tall. Screen = 8 * view.k * ps. For k=0.348, ps=0.8 → 2.2px. Tiny. That's fine — it's texture.

Let's use length 6-14 world units → 1.7-3.9px. Good.

Draw as a short line with a slightly different green.

Also add some larger dirt patches (ellipses).

OK.

Actually, a simpler and better-looking approach: draw horizontal bands of slightly different green with perspective-correct spacing. Meh, the tufts are fine.

Let me also add a slight vignette/darkening at the edges. Optional.

Now the HUD.

```js
function updateHUD() {
  if (redN !== counts[0]) { redN = counts[0]; document.getElementById('redN').textContent = redN; }
  ...
}
```
Just set it every frame — DOM text updates are cheap-ish if the value doesn't change (browsers optimize). Actually setting textContent to the same value still triggers work. Let's cache.

Now, the banner.

```js
function showBanner(side) {
  const el = document.getElementById('banner');
  el.textContent = SIDES[side].name + ' STANDS VICTORIOUS';
  el.style.color = SIDES[side].ui;
  el.classList.add('show');
}
function hideBanner() { document.getElementById('banner').classList.remove('show'); }
```

With a CSS transition on opacity.

Also, let's add a "battle number" in the subtitle, like "ENGAGEMENT I".

Alright — reset:

```js
function resetBattle() {
  battleNo++;
  time = 0; phaseT = 0; phase = 'charge'; winner = -1;
  counts[0] = N_SIDE; counts[1] = N_SIDE;
  hideBanner();
  buildBackground();   // clears the stains
  spawnArmies();
  setTitle();
}
```

setTitle picks a new name.

Let's write the name picker:
```js
let lastName = '';
function pickName() {
  let n;
  do { n = PREFIX[(Math.random()*PREFIX.length)|0] + ' ' + PLACES[(Math.random()*PLACES.length)|0]; }
  while (n === lastName);
  lastName = n;
  return n;
}
```

Good.

Now, let's assemble. I also want a fade-in at the start of each battle. Optional — skip.

Let me write out the final code.

One thing about `counts`: I'll track survivors per side.

Let me write the whole file now.

Also, need `requestAnimationFrame` loop with `last` time.

Let me be careful with the initial `bgCanvas` — buildBackground is called from resize.

Let me handle resize: on window resize, rebuild the view, LUT, background, and reposition... units? Their world positions are independent of the view, so they stay. But the background stains would be lost. Acceptable.

Hmm, but resize also rebuilds the background which clears stains. Fine.

Actually, if resize happens mid-battle, the units keep their world positions and everything rescales. Good.

Let's write.

One more detail: the `rot` for sprites. Let me store `u.rot` as an integer index 0..15.

```js
const ROT_N = 16;
function angleToRot(a) {
  let r = Math.round(a / (Math.PI*2) * ROT_N) % ROT_N;
  if (r < 0) r += ROT_N;
  return r;
}
```

The sprite for rot r is drawn with `g.rotate(r/ROT_N * 2π)`. So rot 0 = facing +x. An angle of 0 rad = +x. ✓

In updateUnits:
```js
if (d > 1) {
  const a = Math.atan2(dy, dx);
  const r = angleToRot(a);
  // smooth: only change if different
  u.rot = r;
}
```
Actually, let's compute the angle from the direction to the target, which is stable even when stationary.

```js
if (t) { const a = Math.atan2(t.y - u.y, t.x - u.x); u.rot = angleToRot(a); }
```

Good, and it's stable.

Hmm, in a melee, the target changes and the rot might jump around. With retargeting every ~0.4s, the rot would flip. That's fine — it looks like they're turning to face their opponent.

OK. Also add per-unit seed for animation phases.

Let me write the code.

```js
function makeUnit(side, x, y) {
  return {
    side, x, y, vx:0, vy:0,
    hp: 100, maxHp: 100,
    speed: 130 + Math.random()*55,
    dmg: 17 + Math.random()*9,
    atkInt: 0.30 + Math.random()*0.16,
    cool: Math.random()*0.3,
    reach: 38,
    target: null,
    retargetT: Math.random()*0.4,
    engaged: false,
    flash: 0,
    alive: true,
    rot: side === 0 ? 0 : 8,
    seed: Math.random()*100,
    gx:0, gy:0
  };
}
```

Note: side 0 faces +x (right) → rot 0. Side 1 faces -x (left) → angle π → rot 8. ✓

Now the reach: units should attack when within 38 world units (center to center). Their bodies are ~27 wide, so at 38 apart they're nearly touching. Good. And SEP = 34 keeps them slightly apart... hmm, SEP is the min distance for separation. If SEP=34 and reach=38, then when they're at 34-38 apart, they can attack. But separation pushes them to 34 apart. So they'd always be at ~34 apart when in contact → within reach → attacking. 

Hmm, but if SEP pushes them apart, and the reach requires <38, then it works: they settle at 34 and attack. Good.

Actually, I realize separation-based pushing might make the melee too orderly (a crystal lattice). Adding jitter helps. Let's add small random velocity noise in updateUnits.

Let's add: `tx += (Math.random()-0.5)*20; ty += (Math.random()-0.5)*20;` to the desired velocity. Hmm, that adds noise every frame which is fine.

Better: give each unit a persistent `wobble` phase and add a sinusoidal lateral force.

Let's keep it simple: add `Math.sin(time*3 + u.seed*7) * 15` to the perpendicular component.

Eh, let's just add small random jitter to the position each frame in the melee: no, that causes drift.

I'll add a small sinusoidal velocity perturbation.

OK, writing now for real.

Let me also handle the case where a unit has no target (all enemies dead) — but then the battle is over.

Final structure:

```js
// ... setup
// ... classes / helpers
// ... background
// ... sprites
// ... simulation
// ... render
// ... loop
// ... init
```

Let me write it.

```js
const COLS = 50, ROWS = 10;
const SX = 30, SY = 64;
```
Wait, 50*10 = 500 ✓.

Formation width = 49*30 = 1470, height = 9*64 = 576.

Red center x = 800 → from 65 to 1535.
Blue center x = 3200 → from 2465 to 3935.

Field W = 4000. OK.

Hmm, red's left edge at x=65 is close to 0. Fine.

Center y = 800 → from 512 to 1088. Field D = 1600. OK.

Let's go.

Now writing the actual final code.

For the HUD counters, I'll compute the bar width as a percentage.

Let me write the HTML/CSS/JS.

I'll now produce the file.

One last check on performance: the render loop does 1000 drawImage + sorting. The sim does grid build (1000 inserts), update (1000 units with a few ops), combat (pairs). Should hit 60fps.

Let me write it.

Regarding `rl.sort((a,b)=>a.y-b.y)` — sorting 1000 elements 60 times/sec. V8's TimSort on nearly-sorted data is fast. Fine.

Actually, since units move slowly, the array is nearly sorted → very fast.

OK writing.

Also: I should double check `interact` is not called with the same pair twice due to the grid. I showed it's not. Good.

But wait — there's an issue with the neighbor iteration. I iterate cells (gx,gy) and check neighbors. But if a unit `a` is in cell (gx,gy) and unit `b` is in cell (gx+1, gy), the pair is checked when processing cell (gx,gy) via the "right neighbor" check. ✓. When processing cell (gx+1,gy), we check its right neighbor (gx+2,gy), down, down-right, down-left. We do NOT check its left neighbor. ✓ No duplicate.

Good.

Let me write it all out now.

For the victory phase, I also want the losers' remaining units... they're all dead, so nothing.

Actually, in a battle to the death, one side is fully wiped. That's a bit grim but fine. Alternatively, stop when one side drops below ~5% and declare victory. Let's do that: when a side's count drops below 4% of the original (20 units), declare the other side the winner. Hmm, but then there'd be stragglers. It's fine — actually it looks better if the last few survivors flee. Let's just go to the full wipe; it takes a few extra seconds. Hmm, chasing down 20 scattered units could take 10+ seconds.

Let's declare victory when one side has ≤ 15 units and the other has ≥ 3× that. Then the remaining losers "flee" (run off the field) during the victory phase. That's a nice touch!

Let's implement: in the victory phase, units of the losing side run away from the center and fade out (or just run off the edge and get removed).

Simpler: on victory, immediately remove the remaining losers with a blood puff? That's abrupt. Let's have them flee: they run toward the nearest edge and are removed when off-screen.

Hmm, adds complexity. Let's just set the victory condition at ≤ 8 units remaining on the losing side and let them flee. Actually, let's just let them die — with the frenzy multiplier they die fast anyway.

Compromise: victory triggers when a side reaches 0, OR when a side has ≤ 10 units and time > 20. Then in the victory phase, the surviving losers flee (move away and fade). Let's implement the flee as: losers get vx/vy away from the center at high speed; when their x leaves [0, FIELD_W], remove them. That's easy.

Let's do it.

OK. Writing now, for real.

Actually, one more thought about the "melee chaos" — to make formations visibly break, the initial charge should have units moving mostly straight, and once engaged, they mill about. The separation + target-following gives that. Good.

Let's write.

Also, I want a subtle directional light / shading on the units. The prerendered sprite can have a gradient. Fine.

Writing the code:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
<title>Mass Battle Simulation</title>
<style>
  html,body{margin:0;padding:0;width:100%;height:100%;overflow:hidden;background:#0a0d08;}
  #cv{display:block;position:absolute;inset:0;width:100%;height:100%;}
  #hud{position:absolute;inset:0;pointer-events:none;
       font-family:"Trebuchet MS","Segoe UI",Helvetica,Arial,sans-serif;
       -webkit-user-select:none;user-select:none;}
  #title{position:absolute;top:12px;left:0;right:0;text-align:center;
         font-family:Georgia,"Times New Roman",serif;
         font-size:clamp(17px,2.6vw,32px);letter-spacing:.16em;text-transform:uppercase;
         color:#f3e9d2;text-shadow:0 2px 10px #000,0 0 32px rgba(255,170,60,.35);}
  #sub{position:absolute;top:calc(12px + clamp(22px,3vw,38px));left:0;right:0;text-align:center;
       font-size:clamp(9px,1.05vw,12px);letter-spacing:.42em;text-transform:uppercase;
       color:#a9986f;text-shadow:0 1px 6px #000;}
  .army{position:absolute;top:14px;width:170px;}
  .army.left{left:18px;text-align:left;}
  .army.right{right:18px;text-align:right;}
  .army .n{font-family:Georgia,serif;font-size:clamp(20px,3.2vw,38px);line-height:1;
           font-weight:bold;text-shadow:0 2px 10px #000;}
  .army .nm{font-size:clamp(8px,1vw,11px);letter-spacing:.22em;text-transform:uppercase;
            color:#cbbf9f;margin-top:2px;text-shadow:0 1px 5px #000;}
  .army .bar{height:5px;margin-top:6px;background:rgba(255,255,255,.13);
             border-radius:3px;overflow:hidden;}
  .army.left .bar{ }
  .army.right .bar{ }
  .army .bar i{display:block;height:100%;width:100%;border-radius:3px;transition:width .2s linear;}
  .red .n{color:#ff6a5a;} .red .bar i{background:linear-gradient(90deg,#8e1b12,#ff5a44);}
  .blue .n{color:#63a8ff;} .blue .bar i{background:linear-gradient(90deg,#1b4a9c,#5aa8ff);}
  .army.right .bar i{float:right;}
  #banner{position:absolute;top:44%;left:0;right:0;text-align:center;
          font-family:Georgia,serif;font-size:clamp(20px,4.2vw,54px);
          letter-spacing:.12em;text-transform:uppercase;
          opacity:0;transition:opacity .7s ease;
          text-shadow:0 3px 18px #000,0 0 50px rgba(0,0,0,.9);}
  #banner.show{opacity:1;}
</style>
</head>
<body>
<canvas id="cv"></canvas>
<div id="hud">
  <div id="title">—</div>
  <div id="sub">ENGAGEMENT I</div>
  <div class="army left red">
    <div class="n" id="redN">500</div>
    <div class="nm" id="redName">Crimson Host</div>
    <div class="bar"><i id="redBar"></i></div>
  </div>
  <div class="army right blue">
    <div class="n" id="blueN">500</div>
    <div class="nm" id="blueName">Azure Legion</div>
    <div class="bar"><i id="blueBar"></i></div>
  </div>
  <div id="banner"></div>
</div>
<script>
...
</script>
</body>
</html>
```

Hmm, the army counters at top:14px will collide with the title for narrow windows. The title is centered and the armies are at the left/right edges with a width of 170px. On a 1600px screen, the title has ~1200px. Fine.

Now the JS.

Let me write it out.

```js
(function(){
'use strict';

// ---------------- Canvas / View ----------------
const cv = document.getElementById('cv');
const ctx = cv.getContext('2d', { alpha: false });

const FIELD_W = 4000, FIELD_D = 1600;
const S_FAR = 0.55, S_NEAR = 1.15, PERSP = 1.35;
const SPRITE_WORLD = 62;

let W = 0, H = 0, DPR = 1;
const view = { cx: 0, horizon: 0, fieldH: 0, k: 1 };

const LUT_N = 512;
const lut = new Float32Array(LUT_N + 1);
const INV_STEP = LUT_N / FIELD_D;
for (let i = 0; i <= LUT_N; i++) lut[i] = Math.pow(i / LUT_N, PERSP);

function depthS(y) {
  const f = y * INV_STEP;
  if (f <= 0) return 0;
  if (f >= LUT_N) return 1;
  const i = f | 0;
  return lut[i] + (lut[i + 1] - lut[i]) * (f - i);
}
```

Then resize, background, sprites, sim...

Let me write the rest carefully and completely.

I'll write `buildBackground()` with tufts. Tufts generated once per battle (or per resize). Let's generate them in `buildBackground` with a seeded random so they don't jump on resize. Eh, just Math.random.

Let me write the code in full now, being careful.

Also: I should make sure that on the first frame, `last` is set, and the loop starts.

Let me write the final answer.

Regarding the celebration sparkles: emit golden particles from winners. Colors r=255,g=210,b=110.

OK.

Also, add a "dust" color: r=150,g=135,b=100.

Blood: r=150,g=25,b=25 and variants.

Let's write it.

For `spawnBlood`, velocities are mostly horizontal + slight up. Since we're in a top-down-ish view, the blood should spray outward in the x/y plane. Yes.

Let's write.

Final concern: the `interact` function modifies positions during the grid iteration, which could push a unit into a different cell — but the grid isn't rebuilt, so it's just slightly inaccurate. Fine.

Writing now.

def render particle projection: same as units.

Let me write everything.

Also, I want a slight camera shake or flash on big events? Skip.

Let me write the code.

```js
function step(dt) {
  time += dt;
  phaseT += dt;

  if (phase === 'victory') {
    stepVictory(dt);
  } else {
    buildGrid();
    stepUnits(dt);
    stepCombat(dt);
    compactUnits();
  }
  stepParticles(dt);
  checkPhase();
}
```

`checkPhase` handles the transition to victory and the reset.

In stepVictory, the losers flee and the winners cheer.

```js
function stepVictory(dt) {
  for (let i = 0; i < units.length; i++) {
    const u = units[i];
    if (!u.alive) continue;
    if (u.side === winner) {
      // cheer
      const dx = FIELD_W * 0.5 - u.x, dy = FIELD_D * 0.5 - u.y;
      const d = Math.hypot(dx, dy) || 1;
      if (d > 120) { u.x += dx / d * 55 * dt; u.y += dy / d * 55 * dt; }
      u.x += Math.sin(time * 2.6 + u.seed * 5) * 22 * dt;
      u.y += Math.cos(time * 2.2 + u.seed * 3) * 16 * dt;
      if (Math.random() < 0.012) emit(u.x, u.y, 0, -10, 0.9, 2.4, 255, 215, 120, 0.94);
    } else {
      // flee
      const dx = u.x - FIELD_W * 0.5;
      const sgn = dx >= 0 ? 1 : -1;
      u.x += sgn * 260 * dt;
      u.rot = sgn > 0 ? 0 : 8;
      if (u.x < -80 || u.x > FIELD_W + 80) u.alive = false;
    }
  }
}
```

Hmm, `u.alive = false` inside the loop then compact in checkPhase or after. Let's compact at the end of stepVictory.

Also, the arrow particle velocity: let's give it a slight upward.

OK.

Let me finalize and write.

Note: `emit(x, y, vx, vy, life, size, r, g, b, drag)`.

Alright. Writing the final file.

Let me count the pieces and make sure I don't forget anything:
1. HTML shell ✓
2. CSS ✓
3. Canvas setup + view ✓
4. resize + buildBackground ✓
5. sprites ✓
6. units + spawn ✓
7. grid ✓
8. findTarget ✓
9. stepUnits ✓
10. stepCombat + interact + hit + kill ✓
11. particles ✓
12. render ✓
13. HUD ✓
14. loop ✓
15. init ✓

Go.

For the sprite generation, I need to be careful that the canvas creation happens before use.

Let me write `buildSprites()` at init.

Writing:

```js
const ROT_N = 16;
const SPR = 48;
let sprites = [];

function drawSoldier(body, mid, head, weapon, ang, white) {
  const c = document.createElement('canvas');
  c.width = SPR; c.height = SPR;
  const g = c.getContext('2d');
  g.translate(SPR / 2, SPR / 2);
  g.rotate(ang);
  if (!white) {
    g.fillStyle = 'rgba(0,0,0,0.32)';
    g.beginPath(); g.ellipse(0.6, 2.6, 12.5, 9.5, 0, 0, 6.2832); g.fill();
  }
  // legs / coat
  g.fillStyle = white ? '#ffffff' : mid;
  g.beginPath(); g.ellipse(-2.5, 0, 10.5, 7.5, 0, 0, 6.2832); g.fill();
  // torso
  g.fillStyle = white ? '#ffffff' : body;
  g.beginPath(); g.ellipse(0.5, 0, 10, 7.8, 0, 0, 6.2832); g.fill();
  // shoulders
  g.fillStyle = white ? '#ffffff' : mid;
  g.beginPath(); g.ellipse(-0.5, -6.5, 4.5, 4.2, 0, 0, 6.2832); g.fill();
  g.beginPath(); g.ellipse(-0.5, 6.5, 4.5, 4.2, 0, 0, 6.2832); g.fill();
  // helmet
  g.fillStyle = white ? '#ffffff' : head;
  g.beginPath(); g.arc(3.5, 0, 4.8, 0, 6.2832); g.fill();
  // weapon
  if (!white) {
    g.strokeStyle = weapon;
    g.lineWidth = 2.1;
    g.lineCap = 'round';
    g.beginPath(); g.moveTo(5, 6); g.lineTo(20, 2); g.stroke();
  }
  return c;
}
```

Hmm, the weapon line extends to x=20, and the canvas half-size is 24. So it fits.

But for the white silhouette, the weapon isn't drawn — that's fine (it's just a flash overlay).

Hmm, actually the shadow at (0.6, 2.6) with rx 12.5 — extends to 13.1 in x, fits.

OK.

Now, `makeSprites()`:
```js
function buildSprites() {
  sprites = [];
  for (let s = 0; s < 2; s++) {
    const arr = [];
    const col = SIDES[s];
    for (let r = 0; r < ROT_N; r++) {
      const a = r / ROT_N * Math.PI * 2;
      arr.push({
        n: drawSoldier(col.body, col.mid, '#cfd6dd', '#e2e2e2', a, false),
        w: drawSoldier('#fff', '#fff', '#fff', '#fff', a, true)
      });
    }
    sprites.push(arr);
  }
}
```

Note: `s` shadows the outer... it's a local. Fine, but I use `const s` inside... careful. Let me rename to `si`.

OK. Writing the final now.

One more: the flash overlay sprite is a full white silhouette, drawn on top of the normal sprite with alpha. Since both are the same shape, it looks like the unit turns white. Good.

Alright, final code.

I'll write it out now in full.

Let me double check `stepUnits` — with `u.reach * 0.7` as the stop distance, units stop ~26 units from the target. Then separation keeps them at 30-34. Hmm, so they'd stop just outside separation range and never fight?

Let's set: stop distance = u.reach * 0.55 = 21. So they always try to close to within 21, but separation keeps them at 30. So they keep pushing. That's good — they push into each other and fight.

Actually with reach=38 and they're at 34 (separation), they're within reach → they attack. 

And the "stop distance" of 21 means they always push forward into the enemy. Good, that creates the pressure of a melee.

So: `if (d > u.reach * 0.5) { move toward }`.

With engaged slowing them to 0.35x speed, they push slowly. Good.

Let me set reach = 40 and SEP = 32.

Then units attack when within 40 center-to-center. Their bodies are ~27 wide (radius 13.5 each, so touching at 27). At 32-40 apart they're close but not overlapping. Good.

Now, will the separation prevent them from ever getting within 40? SEP=32 pushes them to be at least 32 apart. So they'll be in the range [32, 40] → attacking. 

But wait: in a dense melee, a unit could be pushed by many neighbors to a distance >40 from its target. Then it moves closer. It'll oscillate. Fine.

OK. Writing.

Actually, one issue: `SEP = 32` and the separation applies to ALL pairs within 32, including allies. With a formation spacing of 30 in x, allies are at 30 apart < 32, so they'd push apart! That would destroy the formation immediately.

Hmm. Formation spacing SX=30, and SEP=32. That's a problem.

Let's set SX = 36 and SEP = 30. Then allies in a row are 36 apart (> SEP=30), no push. And depth spacing SY = 64 (> SEP). Good.

But then the formation width = 49*36 = 1764. Red center at x=900 → 18 to 1782. Blue center at 3100 → 2218 to 3982. Gap = 2218-1782 = 436. Too close.

Let's widen: red center x=850, blue center x=3150. Red: -32..1732. Hmm, negative.

Let's reduce COLS to 40 and ROWS to 12.5 → not integer. 

Use COLS=50, ROWS=10, SX=34 → width = 49*34 = 1666.
Red center 880 → 47..1713. Blue center 3120 → 2287..3953. Gap = 574.

Hmm, that's a short charge (2s at 300 closing speed). Let's use FIELD_W = 4400 and centers at 950 and 3450.

Red: 117..1783. Blue: 2617..4283. Gap = 834. Closing at 300 → 2.8s. Good.

k = W/(4400*1.15) = W/5060. For W=1600, k=0.316. Unit screen size at near: 62*0.316*1.15 = 22.5px. Body 27.5 world * 0.316 * 1.15 = 10px. Spacing 34 world → 12.4px at the near edge. OK, slight gaps between units. Good.

At mid-depth (ps=0.85): spacing = 34*0.316*0.85 = 9.1px, body = 7.4px. Gaps of 1.7px. Good.

Alright, let's go with:
- FIELD_W = 4400, FIELD_D = 1600
- COLS = 50, ROWS = 10, SX = 34, SY = 64
- Red center (950, 800), Blue center (3450, 800)
- SEP = 30, reach = 40

Formation width 1666, so red spans x 117..1783. Since the separation is 30 and SX=34, allies stay put initially. ✓

But diagonal neighbors: sqrt(34² + 64²) = 72 > 30. ✓

Good.

Now, hmm, with a 50-wide front and 10 rows, when they collide, the front line is 50 wide. 

Let's estimate the kill rate again. 50 units engaged per side initially. Each takes ~5 hits at 0.35s = 1.75s of combat. With ~1.5 attackers each, ~1.2s per kill. So 50/1.2 = 42 kills/s... but only counting one side's losses. Each side loses ~42/s? That would wipe 500 in 12s.

Hmm, that's both sides losing 42/s. Total 84/s. From 1000 to 0 in 12s. Plus 2.8s charge = 15s. 

But the rate increases as the melee spreads (more units engage). And the frenzy kicks in at 16s anyway.

Actually, the concern is the opposite: it might be too fast. But we want resolution within 30s. 15-20s is perfect.

Let's go.

Actually wait, I need to double check: the front line is 50 units wide, but each "unit" is only engaged with 1-2 enemies. So the total engaged per side ≈ 50-100. Kills per second per side ≈ 50/1.2 = 42. Total deaths 84/s. 1000/84 = 12s. Yes, ~12-15s battle. Good.

Let me add the frenzy at t=18 just in case: dmg *= 1 + max(0, time-18)*0.2.

OK, writing.

Also, the initial gap 834 with a closing speed of ~2*145 = 290 → 2.9s. During that time no deaths. Then ~13s of melee. Total ~16s, then 5s victory = 21s. Within 30s. 

Now let me write everything out.

For the counter display, I'll show the number of survivors.

Let me write the final code.

Also — the title. Let's make sure it's set at the start and on each reset.

Writing.

Final: I'll make sure `phase` starts as 'charge' and transitions to 'melee' when enough units are engaged (purely cosmetic, for the subtitle). Actually let's use the subtitle for "ENGAGEMENT I" / "ENGAGEMENT II" etc. And maybe show "CHARGE" / "MELEE" / "VICTORY". Hmm. Let's keep the subtitle as the engagement number.

OK writing now.

Let me write the code.

var lastTime = performance.now();

function loop(now) {
  requestAnimationFrame(loop);
  let dt = (now - lastTime) / 1000;
  lastTime = now;
  if (dt > 0.1) dt = 0.1;
  acc += dt;
  let iter = 0;
  while (acc >= FIXED && iter < 3) { step(FIXED); acc -= FIXED; iter++; }
  if (iter === 0 && dt > 0) { /* still render */ }
  render();
}

Hmm, if the frame rate is higher than 60, `acc` accumulates and steps happen occasionally. That's fine.

But if the display is 30Hz, dt=0.033, acc accumulates → 2 steps per frame. Good.

Alright. Let's write.

Let me finally write out the code in full.

Actually one more thing — `counts` array. Initialize to [500, 500].

And the HUD update reads from `counts`.

Let me write it.

I'm going to write the final code now.

```js
// ============ SIM ============
const N_SIDE = 500;
const COLS = 50, ROWS = 10, SX = 34, SY = 64;
const ARMY_CX = [950, 3450];
const ARMY_CY = 800;

const units = [];
const rl = [];
const counts = [N_SIDE, N_SIDE];

const CELL = 64;
const GW = Math.ceil(FIELD_W / CELL);
const GH = Math.ceil(FIELD_D / CELL);
const grid = new Array(GW * GH);
for (let i = 0; i < grid.length; i++) grid[i] = [];
```

Good.

Now writing everything.

Note FIELD_W=4400 → GW = ceil(4400/64) = 69. GH = ceil(1600/64) = 25. Total 1725 cells.

Clearing 1725 arrays per step, 60 times/sec = 103k ops/sec. Fine.

OK.

Writing out the final answer now.

Oh, and I should handle the possibility that `units.length` is 0 during the victory step — the loop just does nothing.

Also, if both counts hit zero... whatever.

Let me write.

For `checkPhase`, transitions:

```js
function checkPhase() {
  if (phase === 'victory') {
    if (phaseT > 5.2) resetBattle();
    return;
  }
  const a = counts[0], b = counts[1];
  if (a <= 0 || b <= 0 || (Math.min(a,b) <= 12 && Math.min(a,b) * 4 < Math.max(a,b))) {
    winner = a > b ? 0 : 1;
    phase = 'victory';
    phaseT = 0;
    showBanner(winner);
  }
}
```

Hmm, if a=0 and b=0, winner = 1. Whatever.

Also, if a=0, winner should be 1 (blue) since b>a... a>b is false → winner=1. ✓

OK.

Let me write it all.

Also, during the victory, the fleeing losers: I decrement counts? No, they're removed but the counter should show... hmm, the counter shows survivors. Fleeing losers are still alive. Let's leave the count as is — it shows the losers' remaining count frozen. That's fine, or I can count them as casualties when they flee. Let's leave them; the winner's count is what matters.

Actually let's just display the counts as they are.

OK writing.

Let me finally produce the file.

One last check on `findTarget` performance with the ring search. In the melee, enemies are within 1-2 rings, so it's fast. During the charge, the fallback full scan applies. With 500 units retargeting every ~0.4-0.9s, that's ~700-1250 retargets/sec → at 60fps, ~12-20 per frame → 12-20 × 1000 iterations = 20k iterations/frame. Fine.

Alright. Writing!

I'll be careful about the `d > u.reach*0.5` condition and the velocity steering.

Let me write out the final code.

Also, for the unit's `rot` when fleeing/celebrating — handled.

Final code below.