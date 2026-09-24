The user wants a full-featured side-scrolling 2D platformer in a single HTML file. Let me carefully plan this out.

**Core Requirements:**
1. Canvas-based, 16-bit style
2. Original hero drawn with code (pixel art)
3. Side-scrolling, at least 6 screens long
4. Ground, floating platforms, gaps, moving platforms
5. Coins to collect
6. Enemies that walk back and forth, defeat by jumping
7. Goal flag at the end
8. Parallax background (sky, clouds, hills)
9. Coin counter and score
10. Particle effects (coins, enemies)
11. Win screen
12. Controls: Arrow Left/Right, Space/Up to jump, R to restart
13. Autoplay demo mode with P key (AI controls)
14. Vanilla JS, no external assets
15. Self-contained HTML file

**Architecture Plan:**

- **Game Loop:** requestAnimationFrame
- **Level Design:** Array of objects (platforms, enemies, coins) with tile size ~32px
- **Camera:** follows player horizontally
- **Physics:** gravity, velocity, collision detection (AABB)
- **Player:** position, velocity, state (idle, run, jump, dead), drawing as pixel art
- **Enemies:** walk back and forth, squishable
- **Particles:** simple particle system
- **AI for demo:** simple state machine - detect gaps, jump over enemies, collect coins

Let me design the level first. 6 screens minimum. Let's say screen width is 800px, so 4800px+ of level. I'll use a tile size of 32. Let's design with maybe 200 tiles wide = 6400px (8 screens).

**Level design concept:**
- Ground with gaps
- Floating platforms at various heights
- Moving platforms
- Coins placed in arcs/lines
- Enemies patrolling

Let me structure the level as a series of platforms and objects.

**Player pixel art:**
I'll draw the hero using fillRect calls at a small scale, using a color palette. Let me define a grid-based pixel art for the hero. A typical 16x16 or 24x24 pixel character.

Let me design a small hero - maybe a character with a blue tunic, red cap, etc. But I need original.

Let me make a simple character: a robot or a kid with a hoodie. I'll use a 12x16 grid for the sprite, scaled up.

**Enemies:** Something simple - mushroom-like or eye creatures.

**Design approach:**

1. Canvas setup: 800x450 or 960x540 (16:9). Let me use 960x540 for more detail. Or 800x450. Let me go with 960x540.

2. Tile size: 32px. So 30 tiles wide, ~17 tiles tall.

3. Level: 240 tiles wide = 7680px. That's 8 screens at 960px.

**Physics:**
- Gravity: 0.5px/frame²
- Jump velocity: -11
- Move speed: 4px/frame
- Max fall speed: 12

**Collision:**
AABB collision with tiles. But I want to use platform objects rather than a tilemap for simplicity. I'll define platforms as {x, y, w, h} rectangles. Ground segments and floating platforms.

Actually, using a tilemap gives a more classic feel. But for this game, object-based platforms are easier to manage. Let me use a hybrid: define platforms as rectangles for collision, and draw them with pixel-art style textures.

**Parallax:**
- Sky: gradient background
- Clouds: drawn in a few layers moving at different speeds
- Hills: a few hill shapes in the background

**Particles:**
- When collecting coins: yellow sparkles/puffs
- When defeating enemies: red/pink particles
- Maybe dust when landing

**Demo AI:**
- Move toward nearest coin/enemy?
- Actually a good AI would:
  - Move right generally
  - Jump when there's a gap ahead
  - Jump on enemies
  - Collect coins by moving toward them when possible
  - Stop at the flag

Let me design a simple reactive AI:
- If near a wall/gap ahead, jump
- If an enemy is ahead, jump to stomp it
- If a coin is above/ahead, try to move toward it and jump

For the moving platform, the AI needs to handle it - just keep moving right works since the platform moves.

Let me think about the AI more concretely:
- Compute a "desired direction" based on:
  - If there's a coin ahead/up, move toward it
  - If there's an enemy within stomping range ahead, keep moving (will jump anyway)
- Decision making:
  - Check the tile ahead at foot level for gaps. If gap ahead, jump.
  - Check for enemies in front. If enemy ahead and player is above, jump.
  - If a platform is above and the player wants coins up there, jump.

Actually, a simpler approach: the AI makes decisions at a low frequency (every 100-200ms):
- If horizontal distance to next coin < something, move toward it and jump if needed.
- If gap ahead, jump.
- If enemy ahead, move toward it and jump (stomp) if enemy is at same level.

Let me implement per-frame checks:
1. Determine if there is ground directly ahead (foot + a few px forward). If not, jump (set jump held).
2. Check for enemies ahead. If there's an enemy within 60px and same vertical level, and the enemy is not above the player, jump.
3. Otherwise, move right.
4. Also, if falling, press down? No, moving platforms can carry the player.

Actually, for a competent demo, let's combine:
- Move right most of the time.
- If an enemy is close in front, jump (timing so the stomp lands).
- If a gap is detected ahead, jump.
- Coins: if a coin is above and to the right, jump as well.

For the "competent" part: The AI should not attempt impossible jumps. I'll make the level design forgiving enough and the AI robust.

Let me code this step by step.

**Data structures:**

```js
const TILE_SIZE = 32;
const GAME_W = 960;
const GAME_H = 540;

let platforms = []; // {x, y, w, h, moving?: {baseX, baseY, range, speed, axis, offset}}
let enemies = []; // {x, y, w, h, vx, base...}
let coins = []; // {x, y, radius, collected}
let particles = [];
let player = {x, y, vx, vy, w, h, onGround, facing, state, animFrame...}
let camera = {x, y}
let keys = {};
let score = 0;
let coinCount = 0;
let gameState = 'playing'; // 'win', 'dead'
let demoMode = false;
let aiControl = false;
```

**Player drawing:**

I'll create a pixel-art hero using a 2D array for each frame. The hero is maybe 16x24 pixels. I can draw different frames for idle/walk. But that's a lot of code. Let me use a single 16x16 sprite + simple animation by flipping/offsetting.

Actually let me create a proper pixel-art hero with code. I'll define the hero sprite as a 3-color + transparent design.

Let me design a character: a kid with a green cap, blue jacket, orange shoes.

Grid 12x16 (width x height):

```
....RRRR....
...RRRRRR...
...BBBBBB...
...BBBBBB...
....BBBB....
..WWBBBBWW..
..WWBBBBWW..
..BBBBBBBB..
.BBBBBB..BB.
...BB....BB.
...RRRRRR...
..RRRRRRRR..
..R..RR..R..
..R..RR..R..
.........X..
```

Hmm, this is getting complicated. Let me use a simpler approach: draw the hero with a sequence of `fillRect` calls for a pixel-art look. I'll define a color palette and draw a 12x16 character.

Actually, let me make the hero more iconic:
- Red cap (like Mario but different color) - wait, must be original. Let me do a purple cap with a yellow star emblem.
- Orange shirt, blue pants.

I'll set up a `drawPlayer(ctx, player)` function that draws using scaled rects. I'll make the player 24x32 (i.e., 8x8 blocks scaled by 4? That's chunky). Let me do a 16x24 pixel character at scale 2 = 32x48. That's a bit large. TILE_SIZE=32, so the player is about 1 tile wide and 1.5 tiles tall. Good.

Let me define:
- Player hitbox: 24x40 (w=24, h=40). Drawn at 12px offset to the left for centering.

For pixel art, I'll use a function `drawPixel(ctx, x, y, color, scale)`.

**Level:**

I'll design a level from x=0 to x=240 tiles (7680px). Height: ground around y=480 (so from tile 15).

Let me lay out platforms as:
- Ground segments with gaps.
- Floating platforms.
- Moving platforms.

Plan the level:

Screen 1 (0-960): Flat ground, a few coins, one enemy.
Screen 2 (960-1920): Gap, floating platforms, enemies, coins.
Screen 3 (1920-2880): Moving platform over a pit, coins along the path.
Screen 4 (2880-3840): More platforms, enemies.
Screen 5 (3840-4800): Stepping stones, gaps.
Screen 6 (4800-5760, but we need 6 screens minimum so up to 5760 at least). Let me make the level 8000px long. Flag at the end.

I'll define platforms explicitly in world coordinates.

Let me write a level generator using helper functions to make it easier:

```js
function makeGround(x, w, y=GROUND_Y) {
    platforms.push({x, y, w, h: GAME_H - y});
}
```

For gaps, I simply don't place ground.

Moving platforms in the original games move horizontally or vertically. I'll add a `moving` property: `{axis: 'x'|'y', range, speed, baseX, baseY}`.

The collision for moving platforms: if the player stands on it, the platform moves and carries the player. To keep it simple, I'll recompute platform positions each frame and add their delta to the player's position if the player is standing on them.

Let me make a Platform class/object with an update method.

**Enemies:**
Enemies walk back and forth on platforms. They have a patrol range. If they hit a wall or fall, they turn around. When the player stomps (player's vy > 0 and collides from above), the enemy dies and the player bounces. Otherwise, the player dies (maybe play a death animation).

```js
let enemy = {
    x, y, w:32, h:24, vx: -1, dir: -1, baseX, range, alive:true, animFrame
}
```

When an enemy is stomped:
- Set alive = false
- Spawn particles
- Bounce player up
- Add 200 score

When player hits enemy from side:
- Player is dead, respawn at checkpoint / restart level.

For simplicity, player death = restart from the beginning. That's classic.

**Coins:**
25 points, or 50? Let me do 50 points and +1 coin.

**Scoring:**
- Coin: 50 points, +1 coin counter
- Enemy stomp: 100 points
- Reaching flag: 1000 + remaining time? No timer, just 1000.

**Win screen:**
Big "YOU WIN!" and score. Press R to restart. Also P toggles demo even on the win screen? Probably not needed.

**Demo mode AI:**

Let me implement a reactive AI.

Player has properties: `aiInput` = {left, right, jump}.

In demo mode, we override input each frame based on game state.

AI logic (pseudo):

```
function getAIInput(dt) {
    let left = false, right = false, jump = false;
    
    // Look ahead
    const probeDist = 60; // how far we look ahead
    let playerFeetY = player.y + player.h;
    let aheadX = player.x + (player.facing === 1 ? player.w/2 + 30 : player.w/2 + 10);
    
    // Gap detection: check if there is ground below ahead
    let groundAhead = hasGroundAt(aheadX, playerFeetY + 2);
    let groundBelowFront = hasGroundAt(aheadX + 10, playerFeetY + 2);
    
    // Enemy ahead
    let nearestEnemy = findEnemyInFront(200);
    
    // Move toward coins if any are near and reachable
    let coinNear = findNearestCoin();
    // This can be complex...
}
```

But a simpler competent AI for a side-scroller:

- Always press right unless there's a reason not to.
- If a gap is detected ahead (within the next few frames of horizontal travel), jump.
- If an enemy is in front (within 40-80px), jump (to stomp). But also don't jump too early or late. The AI should jump when the enemy is close but before making contact.
- Coins: If a coin is above and near ahead, jump; if below, maybe drop? In this game, coins are usually placed along the path.

I think a state machine approach:

States: Run, Jump (when jumping over gap/enemy), Wait (falling).

Actually, since we control jump with a variable `jumpPressed`, we can make the AI set `jumpPressed` with timing.

Let me make the AI perform a jump when:

1. Gap ahead: The platform ends within `lookahead = 40px` ahead of player's leading edge. Then set jump.
2. Enemy ahead: An enemy is within `enemyJumpRange = 50px` in front, on the same level or below. Then set jump.
3. Coin above: A coin is within a horizontal distance of 30px and above the player, and there's a platform above? Then set jump.

But we need to avoid infinite jumping. Once a jump is initiated, wait until the player is on the ground again before jumping again.

Also, for the moving platform: the player just rides it if they stand on it. The AI shouldn't try to jump off unless necessary.

To make the demo "good", I'll tune the AI parameters. Also, if the player gets stuck against a wall, the AI could change direction. But in a side-scroller, you don't usually have walls.

Let me also handle the case where the coin is behind the player in a pit - the AI shouldn't go back.

Let me code a simpler but effective AI:

```
updateAI() {
    // Stop if win
    if (gameState !== 'playing') { input.right = false; input.jump = false; return; }
    
    // Reset inputs
    input.left = false; input.right = false; input.jump = false;
    
    // Always press right as base
    input.right = true;
    
    // If there is a solid ground edge ahead, jump
    // gap detection
    let probeX = player.x + player.w/2 + 30 * player.facing; // ahead of player
    let probeY = player.y + player.h + 4;
    
    // Check ground ahead (forward and below)
    let groundAhead = this.hasGroundAt(probeX, probeY);
    // Also check if there is ground below the leading edge
    let frontX = player.facing > 0 ? player.x + player.w + 4 : player.x - 4;
    let frontGround = this.hasGroundAt(frontX, probeY);
    
    // Gap if no ground ahead and not too high to fall? Just check ahead.
    if (!groundAhead && player.onGround) {
        input.jump = true;
    }
    
    // Enemy avoidance/stomp:
    let enemy = this.findEnemyInFront(80);
    if (enemy && player.onGround && enemy.y + enemy.h > player.y + player.h - 10) {
        // Enemy is in front and around same height. Jump to stomp.
        input.jump = true;
    }
    
    // Coins: if a coin is just above and ahead, jump
    let coin = this.findCoinAheadUp(60);
    if (coin && player.onGround) {
        // if coin is above the player's head
        if (coin.y < player.y) {
            input.jump = true;
        }
    }
    
    // Edge case: if at a wall ahead (no gap, but wall), maybe jump? There are no walls in this game except maybe the end. Not needed.
}
```

The `hasGroundAt` function checks the platform array for a collision with a point. I'll implement `isSolidAt(x, y)` returning true if any platform covers that point.

But for the AI, I need to be careful with moving platforms. `hasGroundAt` should include moving platforms at their current positions.

Let me implement the game step by step.

**Frame loop:**

```js
let lastTime = 0;
function update(time) {
    let dt = Math.min((time - lastTime) / 16.666, 3); // normalize to 60fps
    lastTime = time;
    updateGame(dt);
    render();
    requestAnimationFrame(update);
}
```

Actually, let me use `requestAnimationFrame` and a fixed timestep or just delta in ms. The physics will use per-frame movement. Let me use `dt` in frames (60 fps base).

**Collision handling:**

For platform collision, I'll use `AABB` vs platform rects. The player moves in X and Y separately.

X movement:
```
player.x += player.vx * dt;
// check collisions
for each platform:
    if (aabb(player, plat)) {
        if (player.vx > 0) player.x = plat.x - player.w;
        else if (player.vx < 0) player.x = plat.x + plat.w;
        player.vx = 0;
    }
```

Y movement similarly.

But this can cause issues with one-way platforms (floating platforms where the player can jump up through from below). In classic platformers, floating platforms can be either solid or one-way.

Let me differentiate:
- Ground (large blocks): solid from all sides.
- Floating platforms: one-way - solid from above only. The player can jump up through them from below.

The collision logic for one-way:
- When moving down and the player's feet are above the platform top, and the player's previous Y (before move) is also above/below? Actually, simply: if `player.vy >= 0` (moving down) and `player.feet <= plat.y` (i.e., was above or on at the start of the move) and `player.feet + motion` reaches below plat.y, then land.

This is getting complex. Let me implement a simpler collision:

I'll use the `pos` and `prevPos` to detect crossing. But for the game's needs, a simpler approach works: process X collision first, then Y.

For each platform:
- Solid (regular platforms): AABB resolved.
- One-way (float platforms): only if the player is moving down (vy >= 0) and the player's previous bottom is <= plat.y + tolerance, and current bottom is > plat.y, then land.

Actually, for a good feel, let me make all floating platforms one-way and ground blocks. The ground blocks are solid from all sides, but since the player never needs to enter them, it's okay.

Let me define:
```js
function collideWithPlatforms(entity, dt) {
    // X axis
    entity.x += entity.vx * dt;
    for (let p of platforms) {
        if (entity.vx > 0 && entity.x + entity.w > p.x && entity.x < p.x + p.w && entity.y + entity.h > p.y && entity.y < p.y + p.h) {
            entity.x = p.x - entity.w;
            entity.vx = 0;
        } else if (entity.vx < 0 && entity.x < p.x + p.w && entity.x + entity.w > p.x && entity.y + entity.h > p.y && entity.y < p.y + p.h) {
            entity.x = p.x + p.w;
            entity.vx = 0;
        }
    }
    
    // Y axis
    entity.y += entity.vy * dt;
    entity.onGround = false;
    for (let p of platforms) {
        // Check if one-way or solid
        if (isOneWay(p)) {
            // Only land on top if falling and previous bottom is above the platform top
            if (entity.vy >= 0 && entity.prevY + entity.h <= p.y + 4 && entity.y + entity.h >= p.y && entity.x < p.x + p.w && entity.x + entity.w > p.x) {
                entity.y = p.y - entity.h;
                entity.vy = 0;
                entity.onGround = true;
            }
        } else {
            if (entity.vy > 0 && entity.prevY + entity.h <= p.y + 4 && entity.y + entity.h >= p.y && entity.x < p.x + p.w && entity.x + entity.w > p.x) {
                entity.y = p.y - entity.h;
                entity.vy = 0;
                entity.onGround = true;
            } else if (entity.vy < 0 && entity.y < p.y + p.h && entity.y + entity.h > p.y && entity.x < p.x + p.w && entity.x + entity.w > p.x) {
                entity.y = p.y + p.h;
                entity.vy = 0;
            }
        }
    }
}
```

Hmm, this is getting complicated. Let me simplify: for solid platforms (the ground), I'll check collisions from all sides. For one-way (floating platforms), only land on top when falling.

To avoid tunneling on floating platforms, use `prevY`:

```js
let wasAbove = prevY + entity.h <= p.y + 4;
let nowFalling = entity.vy >= 0;
if (wasAbove && nowFalling && entity.y + entity.h >= p.y && entity.x < p.x + p.w && entity.x + entity.w > p.x) {
    entity.y = p.y - entity.h;
    entity.vy = 0;
    entity.onGround = true;
}
```

This works well.

For solid platforms (ground), I need to handle side collisions. But the ground is very thick, and the player mostly lands on top. Side collisions with the ground edges (the sides of a gap) are important so the player doesn't get stuck in the wall. Let me handle all sides for solid platforms.

Actually, let me make all ground platforms solid, and floating platforms one-way. For solid, I'll do standard AABB resolution:

```js
// X axis
entity.x += entity.vx * dt;
for (p of platforms) {
    if (p.oneWay) continue;
    if (rectsOverlap(entity, p)) {
        if (entity.vx > 0) entity.x = p.x - entity.w;
        else if (entity.vx < 0) entity.x = p.x + p.w;
        else if (entity.x + entity.w < p.x + p.w) entity.x = p.x - entity.w;
        entity.vx = 0;
    }
}
```

For Y axis:
```js
entity.y += entity.vy * dt;
entity.onGround = false;
for (p of platforms) {
    if (p.oneWay) {
        // only land on top if falling and was above
        if (entity.vy >= 0 && entity.prevY + entity.h <= p.y + 4 && rectsOverlap(entity, p)) {
            entity.y = p.y - entity.h;
            entity.vy = 0;
            entity.onGround = true;
        }
    } else {
        if (rectsOverlap(entity, p)) {
            if (entity.vy > 0 && entity.prevY + entity.h <= p.y + 4) {
                entity.y = p.y - entity.h;
                entity.vy = 0;
                entity.onGround = true;
            } else if (entity.vy < 0 && entity.prevY >= p.y + p.h) {
                entity.y = p.y + p.h;
                entity.vy = 0;
            } else {
                // side collision
                if (entity.vx !== 0) {
                    // resolve horizontally based on direction
                    if (entity.vx > 0) entity.x = p.x - entity.w;
                    else entity.x = p.x + p.w;
                    entity.vx = 0;
                    // recheck X?
                }
            }
        }
    }
}
```

This is still complex, but manageable.

Actually, for the ground segments, they're huge rects that go up to y=480. The player walks on top. At the edges (gaps), the side collision will push the player back if they run into the side. But the player should be able to fall through the gap. Side collision from the ground edge will prevent the player from entering the gap if they're overlapping from the side. That's fine.

But there's a common issue: when standing on the ground and moving toward a gap, if the player is at the edge, the side of the next ground segment (across the gap) shouldn't push them; the player should fall into the gap. Since the gap is open, there's no ground there, so no collision. Good.

However, if the player walks into the side of a ground segment (e.g., a wall), the side collision works.

Let me adopt the approach:
1. Move X, then resolve X collisions with solid platforms only.
2. Move Y, then resolve Y collisions with all platforms (solid and one-way).
3. For one-way, only land on top.
4. For solid, handle top/bottom/side.

But resolving only on one axis at a time can produce bugs. A cleaner approach is to move in X, resolve, then move in Y, resolve. That's what I'll do.

I'll write a `collide()` function that takes the entity and dt. Store prevX/prevY before moving for the Y resolution.

**Moving Platforms:**

Moving platforms are special: they aren't static. They have update(dt) methods that move them. When a player is standing on one, the player should move with it.

I'll keep moving platforms in the `platforms` array as well. Each has:
```js
{
    x, y, w, h,
    moving: {
        fromX, toX, fromY, toY, speed, t // t goes 0->1->0
    }
}
```

But for collision detection to work, when the player stands on it, I need to consider the platform's movement. The simple way: after moving the platform, if the player was on it, the player's position changes by the platform's delta.

That requires knowing which platform the player is standing on. Let's add `player.currentPlatform = null`.

In the movement update:
- Save old platform positions.
- Move platforms.
- For each player, if `player.onGround` and `player.currentPlatform === platform`, then add the platform's delta to the player's x and y.

But this gets complicated with y delta. For simplicity, let's make moving platforms horizontal only. Then carrying the player is just `player.x += dx`.

Let me implement:
```js
this.platforms.forEach(p => {
    if (p.moving) {
        let prev = {x: p.x, y: p.y};
        p.x = p.moving.baseX + Math.sin(p.moving.phase + p.moving.time * p.moving.speed) * p.moving.range;
        p.dx = p.x - prev.x;
        p.dy = p.y - prev.y; // 0 for horizontal
    }
});
```

Then after moving platforms:
```js
if (player.currentPlatform) {
    let p = player.currentPlatform;
    player.x += p.dx;
    player.y += p.dy;
}
```

And when landing on a platform, set `player.currentPlatform = p`.

However, if we have vertical moving platforms, we'd need to handle the Y delta, which can cause the player to collide. Let me keep moving platforms horizontal to keep it manageable. Actually, original games had vertical moving platforms too. Let me support both x and y but carefully.

To keep it robust, let me implement moving platforms as kinematic objects:
- Update platform position.
- Compute delta.
- Move the player by the delta if they are standing on the platform.
- But also, if the platform moves up and the player is standing on it, the player should be lifted. So the delta adds to the player's position.

I'll handle this by:
1. Move platform.
2. If player.currentPlatform === p and player.onGround:
   - player.x += p.dx;
   - player.y += p.dy;
   - Update player collision? Since the platform moved, we need to re-check collisions. But the player was on top, and the platform moved, so the player should just follow. If the platform moved horizontally, side collisions aren't huge. If moved vertically up, no issue. If moved vertically down, the player might need to fall a bit. To keep it simple, I'll just add the delta and then run normal physics.

Actually, a better approach: don't use `currentPlatform` persistence. Instead, in the Y collision pass, when landing on a platform, set a flag. In the same frame, after moving platforms, if the player is on the platform, add the platform's delta. This is naturally handled if we check for standing each frame.

Let me do:
- Each frame, save `prevPlatforms`.
- Move platforms.
- Run physics with collision. When landing on a platform, set `standingOn = p`.
- After physics, if `standingOn === p`, the player got a delta from the platform. But we need to move the player by `p.dx`. We can do this after collision resolution but before drawing. However, this causes the player to lag behind.

Alternative: when landing on a moving platform, set the platform's delta into the player's velocity? No.

Let me look at how simple implementations do it:

The key is that the player's collision resolution against a moving platform should adjust the player's position opposite to the platform's movement *during the frame in which the platform moves*. Since we move platforms before the player, if the player is on top and the platform moves right, the collision check (which sees the overlapping platform) will push the player out to the left... That's wrong.

To fix this, after moving the platform, if it overlaps the player from above, move the player by the platform's delta. This is essentially what `player.y = p.y - player.h` does in the collision resolution. But if the platform moved right by dx, and the player was on top, the collision test AABB will see that the platform is now at a different x, and the player may be overlapping horizontally. We want the player to be at `p.x + player.midX`? Actually, for a horizontal platform, the player shouldn't be pushed horizontally. The player should simply remain in the same relative position horizontally (or ride along).

The easiest way: after moving platforms, for each platform, if the player is standing on it (i.e., `player.onGround && Math.abs((player.x + player.w/2) - (p.x + p.w/2)) < w/2 + p.w/2 && Math.abs(player.y + player.h - p.y) < 10`), then set `player.x += p.dx`, `player.y += p.dy`.

This should work well enough. Let me implement this.

**Enemy movement:**

Enemies move horizontally. They have a `vx`. They get affected by gravity? In classic games, enemies have gravity and can fall off platforms. Let me have enemies be affected by gravity and collide with the same platforms (but not one-way, maybe only solid). This makes them fall if they walk off a ledge, which is good for gameplay. To keep their patrol, if they fall off, they die or walk back? Actually, they should just fall and maybe die off-screen.

For simplicity: enemies have gravity and are solid-platform collides. They move at a constant speed horizontally. When they hit a solid platform from the side, they reverse direction. When they fall off a ledge, they keep falling (could be hazardous). In classic games, enemies turn around at ledges, but not all games. Let me make enemies turn at ledges so they don't all fall into pits. This requires checking if there's ground ahead of the enemy. If not, reverse.

But this is a lot. Since the level has gaps, it would be good for enemies to not fall into pits unless the player is supposed to beat them that way? Actually, if an enemy falls into a pit, the player gets nothing. That's fine. But for a polished feel, let me make enemies turn at ledges. I'll implement simple checks.

**Coins:**

Circle-based or AABB-based? AABB is easier for collision with the player box. Let me use circles for a nicer feel, but AABB is fine. I'll use a circle with radius 8. Draw a spinning coin (oval with varying width).

**Particles:**

Simple particles with position, velocity, lifetime, gravity, color, size. When triggered, spawn 8-10 particles with random velocities.

**Background Parallax:**

I'll draw:
1. Sky: vertical gradient from light blue to a bit darker.
2. Far clouds: slow scroll, semi-transparent white.
3. Far hills: dark blue/green silhouettes.
4. Near hills: lighter green.

These layers scroll at fractions of the camera x (e.g., 0.1x, 0.3x, 0.5x).

Clouds drawn as puffy rects/arcs.

Hills drawn as smooth curves (but we're using pixel art, so maybe stepped rectangles? Let me use `ctx.fillRect` with a staircase pattern, or simple polygons with a bit of noise. Since 16-bit style, polygon hills are fine.)

To avoid artifacts, I'll tile or repeat patterns.

**Tile rendering:**

The ground should look like grass/dirt. I'll draw each tile with a grass top (green) and dirt underneath. For performance, I'll only draw visible tiles.

Let me create a tilemap for the ground? The platforms list defines rectangles. I can fill a rect with dirt and draw grass on top. That's easy.

**HUD:**

Top-left: `COINS: 5  SCORE: 1234`
Top-right: can show `DEMO` when in demo mode.

Use `ctx.font = 'bold 20px monospace'`.

**Win Screen:**

Black overlay with "YOU WIN!" and "SCORE: x" and "R TO RESTART". Also maybe "P FOR DEMO".

**Restart:**

R resets the level.

**Demo Toggle:**

P toggles demo mode. When demo mode is On, the AI controls the player. When Off, human controls. At the beginning, demo mode could be off by default. On the win screen, P should not start a demo? Actually it can.

**Return to menu?** Not needed.

**Level Design in Detail:**

Let me lay out the level. I'll set `GROUND_Y = 480`. The screen is 960x540.

For each "screen" (960px wide sections), I'll place things.

Screen 1 (x:0-960):
- Ground from 0 to 960 (all ground)
- A few coins at y=440 in a line.
- One enemy patrolling from 200 to 800.
- A floating platform at x=500, y=400.
- Maybe a small platform for variety.

Screen 2 (x:960-1920):
- Ground from 960 to 1400, then gap from 1400 to 1500 (100px gap), then ground from 1500 to 1920.
- Floating platforms over the gap: at x=1400, y=440; x=1450, y=380.
- Coins above the gap.
- A couple enemies.
- More floating platforms over the ground.

Screen 3 (x:1920-2880):
- Ground from 1920 to 2880, but with a pit in the middle (maybe from 2400-2500).
- Moving platform over the pit: horizontally moving.
- Coins along the moving platform path.
- Enemies.

Screen 4 (x:2880-3840):
- Ground from 2880 to 3360, gap 3360-3480 (120px), ground 3480-3840.
- Stepping stone platforms (one-way) across the gap.
- Coins above.
- Enemies on the ground.

Screen 5 (x:3840-4800):
- Ground from 3840 to 4800.
- Some elevated platforms with coins.
- Enemies.

Screen 6 (x:4800-5760):
- Ground with gaps.
- Moving platforms vertically/horizontally over gaps.
- Flag at about 5600 (end of level).

Actually, let me make the level 7000px long to ensure at least 6 screens (5760). I'll put the flag at 6400.

Let me design using code. I'll create an array of platforms. I'll use helper functions:

```js
function ground(x, w) {
    platforms.push({x, y: GROUND_Y, w, h: GROUND_Y, solid:true, hor:true});
}
function plat(x, y, w, oneWay=true) {
    platforms.push({x, y, w, h: 16, oneWay});
}
function movingPlat(x, y, w, range, speed, axis='x') {
    platforms.push({
        x, y, w: w||64, h: 16, oneWay:true,
        moving: {baseX:x, baseY:y, range:range, speed:speed, axis:axis, angle:0}
    });
}
```

For moving platforms, in the update:
```js
p.x = p.moving.baseX + Math.sin(p.moving.time * p.moving.speed) * (p.moving.axis==='x' ? p.moving.range : 0);
p.y = p.moving.baseY + Math.sin(p.moving.time * p.moving.speed) * (p.moving.axis==='y' ? p.moving.range : 0);
p.moving.time += dt * 0.001; // dt in ms? Let's use frame-based.
```

Actually since I use dt for compatibility, let me use a global `frame` variable.

Let me define movement as:
```js
p.moving.t += 0.02 * dt;
p.moving.xOffset = Math.sin(p.moving.t) * p.moving.range;
p.moving.yOffset = Math.sin(p.moving.t * 0.7) * p.moving.range;
p.x = p.moving.baseX + (p.moving.axis === 'x' ? p.moving.x : p.moving.y);
```

Or something. I'll keep it simple.

**Starting over with the plan in more code-oriented form:**

HTML structure:
```html
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Platformer</title><style>...</style></head>
<body>
<canvas id="game" width="960" height="540"></canvas>
<script>
// game code
</script>
</body>
</html>
```

Canvas CSS: centered, image-rendering: pixelated.

**Variables:**

```js
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
const W = 960, H = 540, TILE = 32;
let camera = {x: 0, y: 0};
let keys = {};
let gameState = 'playing';
let score = 0, coinCount = 0;
let player, platforms, enemies, coins, particles;
let demoMode = false;
let demoAI = { /* state */ };
let lastTime = 0;
let frame = 0;
```

**Classes/Objects:**

I'll use plain objects and helper functions.

**Reset:**

```js
function resetGame() {
    platforms = [];
    enemies = [];
    coins = [];
    particles = [];
    score = 0;
    coinCount = 0;
    gameState = 'playing';
    player = {
        x: 100, y: 300, w: 24, h: 40,
        vx: 0, vy: 0, onGround: false, facing: 1,
        jumpHeld: false, jumpPressed: false,
        anim: 0, animFrame: 0, dead: false,
        currentPlatform: null, carryX: 0, carryY: 0
    };
    buildLevel();
    updateCamera(true);
}
```

**Level Building:**

I'll write a `buildLevel()` function with the layout.

Let me sketch it more concretely:

```js
function buildLevel() {
    const GY = H - 64; // ground top at y=476? Let me use GY = 480.
    const GROUND_Y = 480;
    
    // Screens...
    // Use helper functions
}
```

But I'll define `addGround(x, w)` and `addPlatform(x, y, w, oneWay)`, `addMovingPlatform(x, y, w, range, speed, axis)`, `addEnemy(x, y, minX, maxX)`, `addCoin(x, y)`.

And maybe convenience for a coin arc.

Let me lay out a level with a legend. I'll go with a tile size of 1? No, use pixels.

Let me define the level as an array of "sections". I'll just list out the calls.

I'll draw the ground as a series of rectangles to create gaps.

**Code for moving platform collision:**

For platform collision to work with moving platforms, I'll write:

```js
function updatePlayer(dt) {
    // Input
    let moveLeft = keys['ArrowLeft'] || keys['KeyA'];
    let moveRight = keys['ArrowRight'] || keys['KeyD'];
    let jump = keys['Space'] || keys['ArrowUp'] || keys['KeyW'];
    
    // Handle jump with edge detection
    if (jump && !player.jumpHeld && !player.jumpPressed) {
        player.jumpPressed = true;
    }
    player.jumpHeld = jump;
    
    // Apply horizontal movement
    let targetVx = 0;
    if (moveLeft) targetVx = -PLAYER_SPEED;
    if (moveRight) targetVx = PLAYER_SPEED;
    player.vx = targetVx; // instant acceleration? Classic platforms have acceleration, but let's use instant for tighter controls.
    
    // Jump
    if (player.jumpPressed && player.onGround) {
        player.vy = -JUMP_SPEED;
        player.onGround = false;
        player.jumpPressed = false;
        // spawn dust particles maybe
    } else {
        player.jumpPressed = false;
    }
    
    // Gravity
    player.vy = Math.min(player.vy + GRAVITY * dt, MAX_FALL);
    if (player.vy > MAX_FALL) player.vy = MAX_FALL;
    
    // Move & collide
    collidePlatforms(dt);
    
    // Clamp horizontal position? No, level scrolls.
    
    // Falling off the bottom of the world
    if (player.y > H + 200) {
        playerDie();
    }
}
```

**Collision Details:**

I'll write:

```js
function moveAndCollide(entity, dt) {
    // Save previous position for Y collision detection
    entity.prevY = entity.y;
    
    // X axis
    entity.x += entity.vx * dt;
    
    // X collision with solid platforms
    for (let p of platforms) {
        if (!p.oneWay && rectsOverlap(entity, p)) {
            if (entity.vx > 0) {
                entity.x = p.x - entity.w;
            } else if (entity.vx < 0) {
                entity.x = p.x + p.w;
            }
            entity.vx = 0;
        }
    }
    
    // Y axis
    entity.y += entity.vy * dt;
    entity.onGround = false;
    
    for (let p of platforms) {
        if (!rectsOverlap(entity, p)) continue;
        if (p.oneWay) {
            // one-way: only land if falling and previous bottom is above or equal to platform top
            if (entity.vy >= 0 && entity.prevY + entity.h <= p.y + 4) {
                entity.y = p.y - entity.h;
                entity.vy = 0;
                entity.onGround = true;
                entity.currentPlatform = p;
            }
        } else {
            // solid platform
            // top collision?
            if (entity.vy >= 0 && entity.prevY + entity.h <= p.y + 4) {
                entity.y = p.y - entity.h;
                entity.vy = 0;
                entity.onGround = true;
                entity.currentPlatform = p;
            } 
            // bottom collision?
            else if (entity.vy < 0 && entity.prevY >= p.y + p.h - 4) {
                entity.y = p.y + p.h;
                entity.vy = 0;
            }
            // side collision
            else {
                if (entity.vx > 0) entity.x = p.x - entity.w;
                else if (entity.vx < 0) entity.x = p.x + p.w;
                entity.vx = 0;
            }
        }
    }
    
    // After collision, if not onGround, clear currentPlatform
    if (!entity.onGround) {
        entity.currentPlatform = null;
    }
}
```

There is a problem: the side collision with solid platforms might happen even when the player is above but overlapping after moving downward by a small amount. The `entity.prevY + entity.h <= p.y + 4` check helps with top collision, but if the player moves fast and the prevY was also overlapping (e.g., fell through? not possible), it could false side-collide. Actually, `prevY + h <= p.y + 4` means the player was above the platform at the start of the frame. If the player was already overlapping (e.g., standing on the edge and moving horizontally into the wall), then `prevY + h` is `p.y` (since the player rests on top), so `p.y <= p.y + 4` is true, so top collision takes precedence, landing again. That's fine.

But if the player runs into the side of a solid platform while at the same height, `prevY + h` is > `p.y + 4`, so top collision won't fire, and it'll be a side collision. Good.

However, when the player stands on a platform and walks off a ledge, for the first frame they're not on the platform, and they start falling. `onGround` is set false. That's fine.

**Carrying by Moving Platform:**

In `updateMovingPlatforms(dt)`:
```js
for (let p of platforms) {
    if (p.moving) {
        let prevX = p.x, prevY = p.y;
        p.moving.t = (p.moving.t || 0) + 0.02 * dt;
        if (p.moving.axis === 'x') {
            p.x = p.moving.baseX + Math.sin(p.moving.t) * p.moving.range;
        } else {
            p.y = p.moving.baseY + Math.sin(p.moving.t) * p.moving.range;
        }
        p.dx = p.x - prevX;
        p.dy = p.y - prevY;
    }
}
```

Then in player update, after collision:
```js
if (player.onGround && player.currentPlatform && player.currentPlatform.moving) {
    let p = player.currentPlatform;
    player.x += p.dx;
    player.y += p.dy;
    // prevent falling off while riding? 
    // Re-check collision? The platform moved; the player might need to be pushed. 
    // We can just move the player: x += dx, y += dy.
}
```

But if `currentPlatform` was set in the collision pass, and then we move the platform before the player's `moveAndCollide`, the player sees the new platform position, so no need for carrying? Wait, the order matters.

If we move platforms first, then update player collision, the player will collide with the platform at its new position. If the player was on top, they would be at `p.y - h` in the new position. So the player doesn't need to be "carried"; the collision resolution naturally snaps them on top. But if the platform moves horizontally, the player won't be automatically moved horizontally because the platform's x changed, and the player's AABB no longer overlaps (they're maybe falling off or being pushed against the side).

So we do need the carrying. Let me do this:

1. Move platforms, save deltas.
2. Move player (with collision). During collision, platforms are at their current positions (the top-y, etc.). The player will stand on the platform if they land on it. But if the player was standing on the platform from the previous frame and the platform moved, the player doesn't start on the platform; they might be in the air and fall, landing on the new platform position. That's actually okay as long as the platform doesn't move too fast. For a 1px/frame movement, the player will still overlap slightly and land. Then `currentPlatform` will be set. But the player's x doesn't change unless friction is applied? If the player is not pressing left/right, vx=0, and they just stand there. The platform moves out from under them? No, the platform is under them, but if it moves right, the player's position doesn't change, so eventually the player falls off. To prevent this, we add `player.x += p.dx` if they're on the platform.

So the order should be:
1. Move platforms, save deltas.
2. Move player, with collision against platforms (now at new positions).
3. If `player.onGround && player.currentPlatform === p`, add `p.dx` and `p.dy` to player.

But in step 2, the player might not overlap the platform because it moved right. The player is now beside the platform, not on top. The collision won't detect it. So the player would be in the air. Step 3 then adds delta only if `currentPlatform` was set, but it wasn't.

Hmm. Let me use a different approach: before moving platforms, remember if the player was on a moving platform. Then after moving platforms, if the player was riding it, move the player by the delta. Then run collision.

Simpler: track `player.riding` as the platform object. At the start of the frame, before platform movement, also check if the player is standing on that platform (feet at platform top, horizontal overlap, etc.). If so, mark `riding`. After moving the platform, apply the delta to the player. Then run collision resolution.

Let me implement that:

```js
// At start of frame:
let riding = null;
if (player.onGround && player.currentPlatform) {
    let p = player.currentPlatform;
    if (p.moving && !gameState.startsWith('dead')) {
        // Check if still on top
        if (Math.abs(player.x + player.w/2 - (p.x + p.w/2)) < p.w/2 + player.w/2) {
            riding = p;
        }
    }
}
if (riding) {
    player.x += riding.dx;
    player.y += riding.dy;
    // Clear currentPlatform? The player will re-collide in the move.
    player.currentPlatform = riding;
}
```

Then move platforms, then run player movement and collision. During the collision, the player is at the new position and should land on the platform if it's solid. This is getting complicated.

Alternatively, implement vertical carrying only: if a moving platform moves up, it lifts the player. Horizontal carrying can be done by applying the delta after collision as described. Let me just go with the "after collision, if standing on a moving platform, add delta" and also do it before collision:

Actually, let me simplify the moving platform design: make moving platforms not require carry by making them "conveyor" style: they move, and if the player is on top, the player gets pushed by the platform's velocity. This is done by setting the player's `vx` to the platform's velocity when standing on it? Or adding to the player's position.

Let me implement it like this:

```js
function updatePlayer(dt) {
    // ... handle input ...
    
    // Save previous position
    let prevY = player.y;
    
    // Move and collide (player moves by vy, etc.)
    moveAndCollide(player, dt);
    
    // If standing on a moving platform, add its delta
    if (player.onGround && player.currentPlatform && player.currentPlatform.moving) {
        let p = player.currentPlatform;
        // Only if the horizontal overlap is still there
        player.x += p.dx;
        player.y += p.dy;
    }
}
```

But `p.dx` is the delta from the *simulated* movement in the previous frame? Let me ensure we compute deltas in `updateMovingPlatforms` every frame.

In `updateMovingPlatforms(dt)`:
```js
for (let p of platforms) {
    if (p.moving) {
        let prevX = p.x, prevY = p.y;
        p.moving.t += dt * 0.02 * 60; // something
        let nx = p.moving.baseX + Math.sin(p.moving.t) * p.moving.rangeX;
        let ny = p.moving.baseY + Math.sin(p.moving.t * p.moving.speed) * p.moving.rangeY;
        p.x = nx; p.y = ny;
        p.dx = p.x - prevX;
        p.dy = p.y - prevY;
    }
}
```

If we update platforms *before* the player, then `p.dx` is ready. In the player's collision, when standing on the platform, `currentPlatform` is set, and after collision we add `p.dx`. This works: the player rides.

But there's a subtlety: if the platform is moving left and the player is standing on it, the player's x stays the same after collision (since vx is 0), then `player.x += p.dx` moves them left. Good.

If the platform moves down, the player may lose contact and start falling. That's fine.

If the platform moves up, the player might be pushed up through the platform? Since we only apply `p.dy` after collision, and the player had already landed, it'll move them up. But if the platform moves up by 5px and the player was overlapping, the collision would have resolved the overlap in the move. Actually because the platform moved first, the player sees the platform at its new position, and the player might be overlapping. The collision resolution will place the player on top (if falling). But the player is already on the ground, so `vy=0` and `prevY+h <= p.y+4` is true, so it resets `y = p.y - h`. This effectively moves the player up by 5px. Good. Then adding `p.dy` would add another 5px! That's double-movement.

So we shouldn't add `p.dy` if the collision already handled the overlap. Hmm.

Let me handle this: when the player is on a moving platform, the platform's movement should only be applied if the collision didn't already move the player. The cleanest way is to NOT have the collision resolve vertical movement for moving platforms, and instead handle all movement through carrying. But that's complex.

Maybe a better approach for moving platforms: make them solid from all sides (not one-way) and handle the player's `y += p.dy` by resetting the feet. Many platformers use the concept of "platform velocity" - the platform has a velocity, and the player inherits it when standing on it.

Let me try this: Compute platform deltas. During collision, if the player lands on a platform, `player.y = p.y - player.h`, and also `player.vy = 0`. Additionally, if the platform is moving, the player should get the platform's velocity applied to their position. The simplest way is to add `p.dx` and `p.dy` after the full player movement, but then when the platform moves up, the player may still be on top due to the collision, and adding `p.dy` double-moves.

To avoid double-move, I can make the collision treat the moving platform's resulting position, and then after collision set `player.x += p.dx` but NOT `y += p.dy` for vertical moving platforms? But then vertical riding would break.

Alternatively, make collision resolution for moving platforms use the *previous* platform position. But that's complicated with all platforms.

Let me step back. For a game like this, I can implement moving platforms as follows: Moving platforms are safe to stand on but moving platforms never move upward into the player in a way that requires lift; they move horizontally or vertically within reach, and the player's collision with them is handled normally. For horizontal moving platforms, I can simply add a "platform friction" that moves the player by dx. For vertical moving platforms, the collision resolution will naturally move the player if the platform moves up because the player will be carried by the platform as it moves up: since the platform moves up first, the player is at the old position, then the vertical collision test sees the platform at the new position overlapping from below... Actually, if the platform moves up and the player is standing on it, the platform's top goes up into the player's feet. The player is being pushed up. The collision detection: `entity.vy=0`, `prevY+h = p.y` (old p.y) = new p.y - dy. Since the platform moved up, the new `p.y` is smaller (higher). `prevY+h` is `oldP.y`. `newP.y + 4` is `oldP.y - dy + 4`. If `dy <= 4`, this condition is true, so the player is placed on top at `newP.y - h`, which is exactly `oldP.y - dy - h`, moving the player up by `dy`. Then adding `p.dy` would move them up again. So we should NOT add p.dy for vertical movement if the collision already snapped them.

I think the correct way is: only add the horizontal delta (`p.dx`) after collision, and for vertical delta, rely on the collision resolution. This way, the player is always placed on top of the platform. If the platform moves down faster than gravity, the player might not keep up (they'd float for a few frames). But if the vertical speed is slow enough, it's fine. For horizontal, the collision doesn't naturally move the player, so we add `p.dx`.

Let me go with: add `p.dx` only.

But wait, if the platform is one-way and moves upward, the player might be lifted by the collision. Good. If the platform moves downward, the player might end up standing in the air briefly; then gravity will pull them down. This is acceptable. To make it more robust, I could set the player's `vy = p.dy/dt` (platform velocity) while standing on it. But that complicates things.

Let me try the simpler approach: moving platforms are horizontal only. This eliminates the vertical carry complexity entirely. The requirements just say "moving platforms" - horizontal is good enough. Let me make all moving platforms horizontal.

Then `p.dy = 0`. The collision naturally handles vertical (player stands on a platform that moves horizontally). The player's x doesn't change, so we add `p.dx`.

Great. I'll make moving platforms horizontal only.

**Player dimensions and speeds:**

- Player w = 24, h = 40.
- Speed = 4.5 px/frame (at 60fps). With dt normalized, vx = speed * dt * 60? Let me use `dt` as 1 at 60fps, so `vx = speed * dt`.

Actually, let me not overthink dt. I'll just use `dt` in milliseconds and scale: `let dt = Math.min((now - last)/16.666, 3)`. Then all speeds are per frame at 60fps. So `player.vx = speed * dt`. Collision uses `dt` on movement.

- Gravity: 0.5 * dt
- Max fall: 12 * dt
- Jump velocity: -12 * dt

Wait, that would make dt scale everything. Let me define speeds as "per frame at 60fps" and use `dt` as a multiplier, so:
```js
player.vx = 4.5 * dt;
player.vy += 0.5 * dt;
player.vy = Math.min(player.vy, 12 * dt);
player.x += player.vx;
player.y += player.vy;
```

This means at higher fps (if dt<1) everything moves slower? No, if fps > 60, dt < 1, so speeds are smaller, but the loop runs more frequently. The net speed per second is `speed * 60` regardless of fps. That's correct as long as dt is the frame time normalized to 16.666ms. So `dt = 1` at 60fps, `dt=2` at 30fps. Moving by `vx*dt` works.

So in code, `vx` is 4.5, and in movement, `x += vx * dt`. Similarly, gravity `0.5 * dt` per frame, and jump `-12 * dt`. Good.

**Collision Resolution with dt:**

When moving `x += vx*dt`, if vx*dt is large, we might overshoot. But at 4.5*dt and 60fps, it's fine.

**Enemy AI:**

Enemies have `vx` (e.g., -1). They have collisions with solid platforms? Do they fall off ledges? I'll make them fall due to gravity. They collide with the same solid platforms (not one-way) so they can walk on the ground. They turn around when hitting a wall or when they reach a ledge (to prevent falling off). Actually, if an enemy turns around at ledges, they won't fall into gaps. That's player-friendly because it means you can't defeat them by baiting them into pits (which is usually not rewarding anyway). Let me make enemies turn at ledges.

For enemies, I'll run a simple movement:
```js
function updateEnemy(e, dt) {
    e.prevX = e.x;
    e.vy = Math.min(e.vy + GRAVITY*dt, 12*dt);
    e.x += e.vx * dt;
    // collision with solid platforms for X
    for (p of platforms) if (!p.oneWay && rectsOverlap(e, p)) {
        // reverse
        e.vx *= -1;
        e.x = e.prevX;
    }
    e.y += e.vy * dt;
    // collision for Y
    e.onGround = false;
    for (p of platforms) {
        if ((p.oneWay && e.vy >= 0 && e.prevY+e.h <= p.y+4) || (!p.oneWay && e.vy >= 0 && e.prevY+e.h <= p.y+4)) {
            if (rectsOverlap(e, p)) {
                e.y = p.y - e.h;
                e.vy = 0;
                e.onGround = true;
                e.currentPlatform = p;
            }
        } else if (!p.oneWay && e.vy < 0 && rectsOverlap(e, p)) {
            e.y = p.y + p.h;
            e.vy = 0;
        }
    }
    // ledge check: if onGround and no ground ahead, reverse
    if (e.onGround) {
        let ahead = (e.vx > 0 ? e.x + e.w + 2 : e.x - 2);
        let footY = e.y + e.h + 2;
        let hasGround = platforms.some(p => !p.oneWay && footY >= p.y && footY <= p.y + p.h + 8 && ahead >= p.x && ahead <= p.x + p.w);
        if (!hasGround) e.vx *= -1;
    }
    // fall off screen
    if (e.y > H + 100) e.alive = false;
}
```

The ledge check uses `platforms.some`. For moving platforms, we might ignore one-ways.

**Coins:**

Coins have positions. I'll draw them as spinning (width=18, height=24) on a 24x24 base. Use a circle hitbox? AABB with the player. I'll use AABB.

Coin pickup:
```js
if (!c.collected && player.x < c.x+16 && player.x+player.w > c.x-16 && player.y < c.y+16 && player.y+player.h > c.y-16) {
    c.collected = true;
    coinCount++;
    score += 50;
    spawnCoinParticles(c.x, c.y);
}
```

**Particles:**

Particle struct: `{x, y, vx, vy, life, color, size, gravity}`.

Update: move by vx*dt, vy*dt; apply gravity; life decreases. Draw as `fillRect`.

When collecting coins, spawn 8 yellow particles.
When stomping enemies, spawn 8 red particles.
When player dies, spawn red particles? Let me add death by restarting.

**Camera:**

Camera follows player:
```ts
camera.x = Math.max(0, Math.min(levelWidth - W, player.x - W/2));
camera.y = Math.max(0, Math.min(levelHeight - H, player.y - H/2));
```

Set `levelWidth = 8000`, `levelHeight = 540`.

**Background Parallax:**

I'll draw in screen space, moving the camera x by a factor.

Sky: fill entire canvas with a vertical gradient.

Clouds: draw a few cloud sprites at `x = (cloudX * scrollFactor - camera.x * factor)`. I'll define a function `drawClouds(factor, y, scale, color)`.

I'll pre-create cloud positions randomly (e.g., 10 clouds spread across x 0-8000). In the draw, compute screen x = `(c.x * factor) % (W + 200) - 100 + cloud.x * factor`? Let me use the standard: for each cloud, `sx = cloud.x - camera.x * factor`. To have clouds spread across the level, I'll generate them at x positions from 0 to 8000. Then when the camera moves, they move at a fraction of the speed.

But if a cloud is behind the camera, it'll be off-screen; that's fine. For clouds, I want them far enough away that they don't pass by too quickly. Let me do:

```js
function drawBackground() {
    // Sky gradient
    let grad = ctx.createLinearGradient(0, 0, 0, H);
    grad.addColorStop(0, '#6ed0ff');
    grad.addColorStop(1, '#bfeaff');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, W, H);
    
    // Far clouds (slow)
    ctx.fillStyle = 'rgba(255,255,255,0.8)';
    for (let c of farClouds) {
        let sx = c.x - camera.x * 0.1;
        if (sx < -c.w) sx += 2000;
        if (sx > W + c.w) continue;
        drawCloud(sx, c.y, c.scale);
    }
    
    // Far hills
    ctx.fillStyle = '#a4d7f5'; or greenish
    for (...) ...
    
    // Near hills
}
```

Hmm, tiling clouds this way is tricky if the clouds are at fixed world positions. If I use world positions, I can just loop through all clouds and set `sx = cloud.x - camera.x * factor`. For 20 clouds, it's cheap. Let me generate clouds with `x` in world coords (e.g., 0-8000). For far layer, sx = cloud.x - camera.x * 0.2. If sx is far off-screen, skip.

For hills, I can use a repeating sine function or draw a few large hills based on a seed. Let me draw hills as triangles with a stepped pixel-art look:

```js
function drawHills(offset, factor, color) {
    ctx.fillStyle = color;
    for (let i=0; i<20; i++) {
        let x = i * 200 - (camera.x * factor) % 200;
        let h = 120 + Math.sin(i * 7.3) * 60;
        let y = H - 100;
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.quadraticCurveTo(x+50, y-h, x+100, y);
        ctx.lineTo(x+100, y); // does this make sense? 
    }
}
```

Actually, let me draw a series of rectangles on top of each other to give a pixelated hill silhouette:

```js
function drawHillGroup(baseX, baseY, height, width, color) {
    ctx.fillStyle = color;
    for (let i = 0; i < width; i++) {
        let y = baseY - height;
        // create a curve
        let t = i / width;
        let h = baseY - (Math.sin(t * Math.PI) * height);
        // draw a vertical line of pixels? 
    }
}
```

This is overkill. Let me use `ctx.arc` or `quadraticCurveTo` for hills; they look fine and not "pixel art" but classic games had smooth hills in the background (e.g., Sonic). I'll use semi-circles.

**Clouds:**

Draw a few overlapping circles/rects.

```js
function drawCloud(x, y, s) {
    ctx.fillStyle = '#fff';
    ctx.beginPath();
    ctx.arc(x, y, 20*s, 0, Math.PI*2);
    ctx.arc(x+20*s, y-10*s, 15*s, 0, Math.PI*2);
    ctx.arc(x+40*s, y, 18*s, 0, Math.PI*2);
    ctx.fill();
}
```

**Ground drawing:**

For each platform, if it's ground (goes down to bottom of screen), draw dirt and grass. If it's a floating platform, draw a stone/bricks.

Draw visible platforms only:

```js
for (let p of platforms) {
    if (p.x + p.w < camera.x - 100 || p.x > camera.x + W + 100) continue;
    let sx = p.x, sy = p.y;
    if (p.oneWay) {
        // draw floating platform
        ctx.fillStyle = '#8B5A2B';
        ctx.fillRect(sx, sy, p.w, p.h);
        ctx.fillStyle = '#5C3A1E';
        ctx.fillRect(sx, sy, p.w, 4);
    } else {
        // draw dirt
        ctx.fillStyle = '#B07350';
        ctx.fillRect(sx, sy, p.w, H - sy);
        // grass top
        ctx.fillStyle = '#5CBF3D';
        ctx.fillRect(sx, sy, p.w, 8);
        // grass tufts
        ctx.fillStyle = '#6EDB56';
        for (let x=0; x<p.w; x+=8) {
            if ((Math.floor((x+sx)/8)) % 2 === 0) ctx.fillRect(sx+x, sy-4, 4, 4);
        }
    }
}
```

But this will draw the ground texturing multiple times. It's fine.

**Player Drawing:**

I'll draw the player using pixel art. Let me define a 12x16 grid and scale by 2. The player's hitbox is 24x40, so the sprite is 24x32? Let me adjust: hitbox width 20, height 32; sprite 12x16 scaled by 2 = 24x32. Let me set hitbox 22x40 for a slightly larger sprite. Actually, let me set hitbox = 20x34 (w=20, h=34) and draw a 12x16 grid at scale 2 = 24x32. Hmm, mismatch. Better: use a 16x24 sprite at scale 2 = 32x48, and hitbox 28x44. That's a bit big but okay.

Let me simplify: player w=24, h=40. Draw pixel art as 3x5 tiles? No, `fillRect` calls with pixel size 2: a 12x20 sprite scaled by 2 = 24x40. Perfect.

So the hitbox covers the entire sprite (or almost). I'll draw the sprite using a color palette, with the feet at the bottom.

Let me create the sprite data for a run frame. Actually, I'll draw an animated character using simple shapes, not a pixel grid, to avoid too much code. But "16-bit style" and "pixel art" suggests a grid.

Let me define a `drawPlayerFrame(ctx, frame, tick)` function:

I'll draw:
- Cap: a red rectangle at the top, with a brim.
- Face: skin.
- Body: blue overalls/shirt.
- Legs: blue.
- Shoes: brown.

Using fillRect with sub-rect positions. For example:

```js
function drawPlayer(ctx, x, y, facing, frame) {
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(facing, 1); // flip for facing
    // draw the character relative to 0,0 at the top-left of the hitbox
    // Cap
    ctx.fillStyle = '#e33';
    ctx.fillRect(6,0, 12, 6);
    ctx.fillRect(18,2, 4, 3); // brim
    // Face
    ctx.fillStyle = '#f0c8a0';
    ctx.fillRect(10,6, 4, 4);
    // Eye
    ctx.fillStyle = '#000';
    ctx.fillRect(12,7, 2, 2);
    // Body
    ctx.fillStyle = '#38f';
    ctx.fillRect(4,10, 16, 6);
    // Arms
    ctx.fillStyle = '#38f';
    ctx.fillRect(0,10, 4, 4);
    ctx.fillRect(20,10, 4, 4);
    // Legs
    ctx.fillStyle = '#38f';
    if (!player.onGround) {
        // jump pose
        ctx.fillRect(4,16, 4, 8);
        ctx.fillRect(16,16, 4, 8);
    } else if (frame === 0) ...

    ctx.restore();
}
```

This is getting long but doable. I'll create a decent-looking little character.

Actually, for a cleaner pixel-art look, I'll use arrays. Let me define a sprite for the character (16x16) with a palette:

```js
const SPRITE = [
  "....RRRRRR......",
  "...RRRRRRRR.....",
   ...
];
```

But parsing strings adds code. I'll manually draw the rectangles. It's fine.

**Death:**

When the player touches an enemy from the side, `playerDie()` is called. For simplicity, `gameState='dead'`, show a death animation (maybe just a red flash), then respawn after 1 second. Or instantly reset. Classic games have death animation; I'll implement a brief death state.

Actually, to keep code short, when hit by an enemy, I'll make the player bounce up (if stomping) or die. On death, `gameState='dead'`, spawn a puff of particles, hide the player, and after a short delay reset the level from the beginning? Hmm, no "checkpoints" for now. Let me just reset immediately or show a death screen. I'll show `GAME OVER` then press R? Let me keep it simple: reset the level instantly when hit. It's arcade-like. Or add a 0.5s delay with timer.

Let me implement:
- `player.dead = true`, `player.vy = -8`, `player.vx = 0`.
- The player falls off screen. After a moment, reset level.

I'll have `respawnTimer` used in the update.

This is getting big. Let me focus on a playable, beatable game.

**Implementation plan in code order:**

1. Define constants and variables.
2. Input handlers.
3. Reset function.
4. Level building.
5. Update: input (or AI), player, AI, enemies, coins, particles, camera, game state.
6. Render: background, platforms, coins, enemies, player, particles, HUD, win screen.
7. Helper functions for collision.

Let me write the code now.

**Detailed Code:**

I'll write everything in one `<script>` tag.

**Collision Rects:**

Use `entity.x, entity.y, entity.w, entity.h`. For platforms, `p.x, p.y, p.w, p.h`.

**Precise movement:**

For one-way platforms, I need `prevY` before moving Y. I'll store it in `moveAndCollide`.

Let me define a `moveEntity(e, dt, isPlayer)` function:

```js
function moveEntity(e, dt, isPlayer) {
    const prevY = e.y;
    const prevX = e.x;
    
    // Move X
    e.x += e.vx * dt;
    
    // X collisions with solid platforms
    for (let p of platforms) {
        if (p.oneWay) continue;
        if (rectsOverlap(e, p)) {
            if (e.vx > 0) e.x = p.x - e.w;
            else if (e.vx < 0) e.x = p.x + p.w;
            e.vx = 0;
        }
    }
    
    // Move Y
    e.y += e.vy * dt;
    e.onGround = false;
    
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
        
        // solid platform
        if (e.vy >= 0 && prevY + e.h <= p.y + 4) {
            e.y = p.y - e.h;
            e.vy = 0;
            e.onGround = true;
            if (isPlayer) player.currentPlatform = p;
        } else if (e.vy < 0 && prevY >= p.y + p.h - 4) {
            e.y = p.y + p.h;
            e.vy = 0;
        } else {
            // side
            if (e.vx > 0) e.x = p.x - e.w;
            else if (e.vx < 0) e.x = p.x + p.w;
            else {
                // if no horizontal velocity, push out horizontally based on previous X
                e.x = (e.x + e.w/2 <= p.x + p.w/2) ? p.x - e.w : p.x + p.w;
            }
            e.vx = 0;
        }
    }
    
    if (!e.onGround) {
        if (isPlayer) player.currentPlatform = null;
    }
}
```

Notice for one-way platforms, the side collision is skipped, so the player can pass through them from below/side. Good.

But for solid platforms, if `e.vy` is 0 and the player is inside a platform (due to a fast fall), neither top nor bottom might trigger; the side branch will push out. That's okay.

Also, if a player runs into a platform from the side while falling, the side branch triggers and pushes horizontally. This can cause "snapping" if the player is also on the ground. But the `prevY + h <= p.y + 4` condition for top will be true if the player is walking on top, so side won't fire. Good.

**Coins:**

No need for a full physics class, just collision detection.

**Enemies:**

I'll use the same `moveEntity` for enemies? Enemies can pass through one-way platforms from below? They shouldn't stand on one-way so I'll make them collide with solid only. I can call `moveEntity` with `isPlayer=false`, but that function uses one-way landing. It would allow enemies to stand on one-way platforms too, which is fine for enemies placed on floating platforms. But in the level, there might be enemies on floating platforms. That's okay.

However, an enemy walking on a one-way platform will need the same logic. `moveEntity` will handle it.

For enemy movement, I need to update their horizontal velocity based on wall collisions. The side collision in `moveEntity` will reverse? Not automatically. I'll check if `e.prevX === e.x`? Actually, if the enemy runs into a wall, `e.vx` is set to 0 by the collision. I can then reverse it manually if `e.vx` becomes 0. But for a moving enemy, `e.vx` is updated each frame. On wall hit, it becomes 0. So:

```js
function updateEnemy(e, dt) {
    e.vy = Math.min(e.vy + GRAVITY*dt, 12*dt);
    e.vx = e.dir * ENEMY_SPEED * dt;
    let oldX = e.x;
    moveEntity(e, dt, false);
    if (e.x === oldX) { // hit a wall
        e.dir *= -1;
    }
    // ledge check
    if (e.onGround) {
        let aheadX = e.dir > 0 ? e.x + e.w + 2 : e.x - 2;
        let footY = e.y + e.h + 2;
        let hasGround = platforms.some(pl => !pl.oneWay && footY >= pl.y && footY <= pl.y + pl.h && aheadX >= pl.x && aheadX <= pl.x + pl.w);
        if (!hasGround) e.dir *= -1;
    }
}
```

But `e.vx` is set each frame to `dir * speed * dt`. When `moveEntity` sets `e.vx=0` on collision, the next frame sets it back to dir*speed. So detecting wall hit by `e.x===oldX` is better. But if the enemy is standing still due to being blocked, it might not trigger `e.x===oldX` if it didn't move. Since `e.vx` is positive, it moved by some amount, so `e.x !== oldX`. If it hits a wall, `moveEntity` moves in X, then collision sets x back to the platform edge. The final x might be the same as oldX? Let me test: oldX=50, vx=1, move to 51, collision with wall at x=40? Actually, if the enemy is to the left of a wall and moving right, it moves right a bit, then collision pushes it left so its right edge aligns with the wall's left. The final x = wall.x - e.w. If oldX was far less, final x > oldX (it moved right but less than attempted). So `e.x !== oldX` generally. But if the enemy is already overlapping the wall by 0 pixels? It won't be, because the collision resolved it last frame. So it could still move.

A safer approach: before moving, compare the direction. If there's a solid platform in the direction of movement ahead, reverse. I can use a simple check:

```js
let aheadX = e.dir > 0 ? e.x + e.w + 1 : e.x - 1;
let solidAhead = platforms.some(p => !p.oneWay && rectsOverlap({x:aheadX, y:e.y, w:e.w, h:e.h}, p));
```

If solidAhead, reverse. This avoids post-move checks. I'll use both for robustness.

**AI Implementation:**

Let me implement a simple `getAIInput()` function that sets `simulatedKeys`. I'll use variables like `ai.left`, `ai.right`, `ai.jump`.

At the start of the player input handling:

```js
if (demoMode) {
    updateAI();
    let left = aiAction.moveLeft, right = aiAction.moveRight, jump = aiAction.jump;
} else {
    keys from keyboard
}
```

I'll have global `input.left`, `input.right`, `input.jump` booleans in the player update.

**AI Algorithm details:**

The AI should:
- Walk right.
- Jump over gaps.
- Jump on enemies? Actually, for a "perfect" demo, the AI can avoid enemies by jumping over them or just kill them by stomping. Let's make it jump to stomp when an enemy is right in front; otherwise, it might jump to avoid.
- Collect coins when they're above (jump) and continue.

Using a small lookahead:

```js
function updateAI() {
    const PLAT = platforms;
    let pcx = player.x + player.w/2;
    let pcy = player.y + player.h;
    
    // Default to moving right
    aiAction.left = false;
    aiAction.right = true;
    aiAction.jump = false;
    aiAction.jumpPressed = false;
    
    // If we're in the air, keep holding jump if we need to (e.g., holding jump for higher)
    // For simplicity, set jump based on conditions only when on ground.
    
    let dist = 80; // lookahead distance in px
    
    if (player.onGround) {
        let aheadX = player.x + player.w + dist;
        let feetY = player.y + player.h + 4;
        // Gap detection: no ground at the leading edge
        let hasGroundAhead = platforms.some(p => !p.oneWay && aheadX >= p.x && aheadX <= p.x + p.w && feetY >= p.y && feetY <= p.y + p.h + 10);
        if (!hasGroundAhead) {
            aiAction.jump = true;
        }
        
        // Enemy ahead
        for (let e of enemies) {
            if (e.alive && e.x > player.x && e.x < aheadX + 40 && Math.abs(e.y - player.y) < 40) {
                aiAction.jump = true;
                break;
            }
        }
        
        // Coin above ahead
        for (let c of coins) {
            if (!c.collected && c.x > player.x && c.x < aheadX && c.y < player.y - 20) {
                aiAction.jump = true;
                break;
            }
        }
    }
    
    // Limit how often we jump to prevent constant jumping when the lookahead detects the edge while near a gap.
    // We can add a timer: after a jump, don't jump again until onGround and a short delay.
}
```

The gap detection might trigger when the player is near a gap but the platform is actually below the ground level? Let me tune.

The AI also needs to handle the end-of-level: when the flag is reached, the game is won. The AI should stop.

This AI might be too naive: it might jump at the enemy too early and land on its head. That's good. But it might jump off a ledge into a pit if the gap is at the edge but the player is a bit before the edge; the "hasGroundAhead" is true because the ground extends a bit ahead, so no jump. When the player is at the edge, it will jump. However, by the time the AI sees the gap, if the player is moving at 4.5px/frame, it needs a head start. The jump takes about 60 frames to clear 100px. So looking 80px ahead is a bit late. I'll set `dist = 60` for gaps, maybe 90.

To be safe, I'll increase the jump height for the AI? The player's jump is set by `JUMP_VELOCITY`. I can make the AI trigger a longer jump by holding jump. I'll set `player.jumpPressed` when on ground, and `player.jumpHeld` is `aiAction.jump`, so holding jump gives higher jumps in many games (variable jump height). My jump logic uses `jumpPressed` edge; `jumpHeld` is unused except for a potential variable height. I'll implement variable jump height: if the player releases jump while rising, the vy is halved (or stops rising). That gives more control. For the AI, holding jump will make it jump full-height if it continues to hold it.

**Variable Jump:**

In physics:
```js
if (!jumpHeld && player.vy < -4) player.vy = -4;
```

This affects jump arc. The AI should hold jump for a few frames to clear gaps.

**Let me get to coding.** I'll keep the AI somewhat simple.

**HUD:**

Use `ctx.font = 'bold 16px monospace'`, draw with a shadow for readability.

**Demo indicator:**

If `demoMode`, draw "AUTO PILOT" in the top right.

**Starting State:**

On page load, `resetGame()`, `demoMode = false`? Let me start with demo mode ON so people can see the game before playing. Actually, let's start with demo off, human control. But to make it easy for the reviewer to see the game, maybe start in demo mode? Hmm. The requirement says "Also maybe 'P FOR DEMO'." I'll start with demo off. But if the AI is perfect, it's nice to see. Let me start with demo on? Let me start with demo off, but if the user doesn't touch anything, after 3 seconds it starts demo? That's too much.

I'll set `demoMode = false` initially.

**Win Condition:**

When the player reaches the flag (x > 6300, y where flag is), `gameState = 'win'`. Show a win screen.

**Losing by falling:**

If `player.y > H + 200`, reset the level (or game over). I'll reset the level.

**Now write the code.**

Ok let me be careful with the code. I'll write it modularly. I might have to adjust positions.

**Level Layout Data:**

Let me define functions in `buildLevel()`:

```js
function addGround(x, w) { platforms.push({x, y: GROUND_TOP, w, h: H - GROUND_TOP, oneWay:false}); }

function addPlatform(x, y, w) { platforms.push({x, y, w: w||64, h: 14, oneWay:true}); }

function addMovingPlatform(x, y, w, range, speed) {
    platforms.push({x, y, w: w||64, h: 14, oneWay:true, moving:{baseX:x, baseY:y, range:range, speed:speed, t:0}});
}

function addEnemy(x, y, minX, maxX) {
    let e = {x, y, w:28, h:28, vx:0, vy:0, dir: -1, alive:true, minX: minX||0, maxX:maxX||9999, onGround:false, prevY:0, currentPlatform:null};
    enemies.push(e);
}
```

Wait, enemies should move within a range to avoid wandering too far. I'll include `minX` and `maxX` patrol bounds. When they reach these, reverse. Simpler than ledge detection.

But for enemies walking on platforms, the platform's edges should be the bounds. I can set these manually when placing enemies:

`addEnemy(300, GROUND_TOP - 28, 200, 800)`

**Coin:**

`addCoin(x, y)` with `c = {x: x, y: y, collected:false, phase: Math.random()*Math.PI*2}`.

**Player start:** `player = {x:100, y:GROUND_TOP-40, ...}`.

**Jump physics:**

Let's tune:
- `PLAYER_SPEED = 5.2`
- `GRAVITY = 0.55`
- `JUMP_VEL = -12.8`
- `MAX_FALL = 12`

With these, the jump height is `v^2/(2g) = 163.84 / 1.1 ≈ 149px`. The width of an 80px gap in terms of time: airtime `2*v/g ≈ 25.6/0.55 ≈ 46.5 frames`. At speed 5.2, that's 242px. So the player can clear gaps up to 200px. Good.

**Camera dead zone?**

Follow directly: `camera.x = player.midX - W/2`, clamped. This gives a lot of a lookahead but can cause jitter when turning. I'll smooth with `Math.max(0, Math.min(levelWidth - W, player.x - W/2))`. No smoothing for now.

**Level width:**

Let `LEVEL_WIDTH = 6600`. The flag at `x=6500`? Let me make the level end at 6400. The flag will be at x=6300, y=GROUND_TOP-80.

**Scenery:**

I'll add a few decorative elements like bushes and trees? Not necessary.

**Let me now write the full code in my head:**

```js
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
const W = 960, H = 540;
let camera = {x:0, y:0};
let keys = {};
let gameState = 'playing';
let score = 0, coinCount = 0;
let demoMode = false;
let lastTime = 0;
let frame = 0;
let player, platforms, enemies, coins, particles;
let levelWidth, levelHeight;
let farClouds = [], hillsFar = [], hillsNear = [];

const GROUND_TOP = 480;
const PLAYER_SPEED = 5.2;
const GRAVITY = 0.55;
const JUMP_VEL = -12.8;
const MAX_FALL = 12.0;

// Input setup
document.addEventListener('keydown', e => {
    keys[e.code] = true;
    if (['Space','ArrowUp','ArrowLeft','ArrowRight'].includes(e.code)) e.preventDefault();
});
document.addEventListener('keyup', e => keys[e.code] = false);

function resetGame() {
    platforms = []; enemies = []; coins = []; particles = [];
    score = 0; coinCount = 0; gameState = 'playing';
    player = {
        x: 100, y: GROUND_TOP - 40, w: 24, h: 40,
        vx:0, vy:0, onGround:false, facing:1,
        jumpHeld:false, jumpPressed:false, jumpHeldSpecial:false,
        currentPlatform:null, prevY:0, prevX:0
    };
    buildLevel();
    levelWidth = 6600;
    levelHeight = 560;
    camera.x = Math.max(0, Math.min(levelWidth - W, player.x - W/2));
    camera.y = 0;
}
```

Wait, `GROUND_TOP` is 480, but the screen height is 540. The player y=440 is at the bottom.

`buildLevel` uses `GROUND_TOP`. Let me lay out the level in `buildLevel`.

I'll create the level step by step:

```js
function buildLevel() {
    // Add ground segments
    // screen 1
    addGround(0, 960);
    addPlatform(500, 360, 100);
    addEnemy(300, GROUND_TOP - 28, 200, 800);
    addEnemy(600, GROUND_TOP - 28, 500, 900);
    addCoin(100, 320); addCoin(140, 320); addCoin(180, 320); addCoin(220, 320);
    // etc.
}
```

But I need GROUND_TOP defined before `buildLevel`, which it is.

I'll carefully lay out 6-7 screens:

**Screen 1 (0-960)**: ground all. Floating platform at 500,360. Coins at (100-220,320). One enemy.

**Screen 2 (960-1920)**: ground 960-1500, gap 1500-1590 (90px), ground 1590-1920. One-way platforms over gap at 1500,360 and 1545,300. Coins over gap at 1545,250. Enemy at 1200-1450.

**Screen 3 (1920-2880)**: ground 1920-2400, gap 2400-2520 (120px), ground 2520-2880. Moving platform at 2400,420, moving horizontally 60px. One-way above too. Coins. Enemies.

**Screen 4 (2880-3840)**: ground 2880-3840. Some elevated platforms at (3000, 300). Coins. Enemies.

**Screen 5 (3840-4800)**: ground 3840-4300, gap 4300-4390, ground 4390-4800. One-way platforms across gap.

**Screen 6 (4800-5760)**: ground 4800-5760, with pits? Maybe vertical moving platform across a vertical shaft? Actually, add a bigger pit at 5200-5320 with floating platforms.

**Screen 7 (5760-6600)**: ground, flag at 6400.

I'll write out the calls. Let me make a second ground segment overlapping? The `addGround` just creates a rect; its height is `H - GROUND_TOP = 60px`. That's a 60px high dirt block under the player's feet. Good.

**Moving platform representation:**

Add to `platforms` with `moving` property. In update:

```js
function updateMovingPlatforms(dt) {
    for (let p of platforms) {
        if (p.moving) {
            const prevX = p.x, prevY = p.y;
            p.moving.t += 0.02 * dt * p.moving.speed; // speed given in maybe 1
            let nx = p.moving.baseX + Math.sin(p.moving.t) * p.moving.range;
            p.x = nx;
            p.dx = p.x - prevX;
        }
    }
}
```

Add `p.dy = 0`.

**Player movement with moving platforms:**

In `moveEntity`, when the player lands on a platform, set `player.currentPlatform = p`. After calling `moveEntity`, if `player.currentPlatform && player.currentPlatform.moving`, do `player.x += p.dx`. But this only applies if they landed on the platform this frame. If they were standing on it from the previous frame, `player.currentPlatform` might have been cleared because `onGround` false? Actually, if the platform moves horizontally, the player might lose ground contact? No, they stay on top, so `onGround` true, `currentPlatform` set. Then we add `dx`.

But there's a timing issue: the platform moves in `updateMovingPlatforms`. I'll call it before `updatePlayer`. Then `p.dx` is ready.

When the player is standing on a moving platform and the platform moves right, the player doesn't automatically move right unless I add `p.dx`. But if the player's `vx` is 0, the player will not move horizontally relative to the screen, so after the platform moves right, the player is no longer on the platform. So we need to add `p.dx` regardless of whether they landed this frame. The collision in `moveEntity` would allow the player to be on top at the new position because the platform's `x` is used in collision. Wait, if the platform moved right by 2px, and the player didn't move, then in the collision pass, the horizontal overlap still exists (unless the platform moved out from under the player). The player sees the platform at its new x, and if the player's x is within the platform's horizontal range, the top collision triggers and places the player on top. But the player's x doesn't change, so the player would be "riding" with the same x coordinate; actually, the collision only sets `y`. It doesn't set `x`. So the player's x remains the same, and the platform is at a new x. The horizontal relative position changes. If the platform moved right by 2, the player is now 2px (closer to the left edge) relative. As long as the player's horizontal overlap exists, it's fine. But once the platform moves beyond the player's width, the player falls off. So to keep the player riding, we must add `p.dx`. So I'll add it.

I'll add after `moveEntity` for the player:

```js
let riding = player.currentPlatform;
if (riding && riding.moving) {
    player.x += riding.dx;
    // prevent being pushed into walls: re-run X collision? Rare. Maybe not needed.
}
```

But if the player is standing at the left edge of a moving platform and it moves left, the player might get pushed into a wall and stuck. It's fine.

**Enemy movement:**

Enemies use `moveEntity` but not for one-way? I'll let enemies collide with all platforms (one-way too) which is fine. They have gravity.

**Particles update:**

```js
for (let i=particles.length-1; i>=0; i--) {
    let p = particles[i];
    p.x += p.vx * dt;
    p.y += p.vy * dt;
    p.vy += p.gravity * dt;
    p.life -= dt;
    if (p.life <= 0) particles.splice(i,1);
}
```

**Coins animation:**

Use `Math.sin(time + phase)` to size.

**Player drawing with animation:**

I'll draw a simple character. For animation, use `frame` counter and `player.animPhase`.

```js
function drawPlayer() {
    let p = player;
    if (p.dead) return;
    let dx = Math.floor(p.x), dy = Math.floor(p.y);
    let w = 24, h = 40;
    ctx.save();
    ctx.translate(Math.floor(p.x + p.w/2), Math.floor(p.y + p.h));
    ctx.scale(p.facing, 1);
    // so x=0 is center, y=0 is feet
    // Draw a skinny character with cap
    // legs
    ctx.fillStyle = '#3366cc';
    ctx.fillRect(-6, -10, 5, 10);
    ctx.fillRect(1, -10, 5, 10);
    // body
    ctx.fillStyle = '#ff6633';
    ctx.fillRect(-8, -20, 16, 10);
    // arms
    ctx.fillStyle = '#3366cc';
    ctx.fillRect(-10, -18, 4, 10);
    ctx.fillRect(6, -18, 4, 10);
    // head
    ctx.fillStyle = '#ffcc99';
    ctx.fillRect(-5, -30, 10, 10);
    // cap
    ctx.fillStyle = '#e33';
    ctx.fillRect(-7, -32, 14, 5);
    ctx.fillRect(5, -30, 4, 2);
    // eye
    ctx.fillStyle = '#000';
    ctx.fillRect(0, -27, 2, 2);
    ctx.restore();
}
```

Coordinates: The player's hitbox is 24x40, so from y=-40 to 0. Looks fine with slight offsets.

**Enemy drawing:**

Draw a brown blob/Galega? I'll draw a simple goomba-like creature: width 28, height 28.

```js
function drawEnemy(e) {
    if (!e.alive) return;
    ctx.fillStyle = '#b5651d';
    ctx.fillRect(Math.floor(e.x), Math.floor(e.y), e.w, e.h);
    // eyes
    ctx.fillStyle = '#000';
    ctx.fillRect(e.x+6, e.y+8, 4, 4);
    ctx.fillRect(e.x+e.w-10, e.y+8, 4, 4);
}
```

Not great but okay.

**Player collisions with enemies:**

In the update, check overlap with alive enemies:

```js
for (let e of enemies) {
    if (!e.alive) continue;
    if (rectsOverlap(player, e)) {
        // stomping? if player's center y < enemy's center y (i.e., falling and previous bottom above enemy)
        if (player.vy > 0 && player.y + player.h - e.y < 15) {
            // stomp
            e.alive = false;
            player.vy = -8;
            score += 100;
            spawnParticles(e.x + e.w/2, e.y + e.h/2, '#8B5A2B');
        } else {
            // hurt
            playerHit();
        }
    }
}
```

`playerHit()` causes death for now.

**Win condition:**

If `player.x > 6350 && player.x < 6450`, set `gameState='win'`.

Actually, use a goal flag at x=6400. I'll draw a flagpole and if player.x > 6390, win.

**Win screen:**

Draw overlay.

**Respawn:**

When `player.y > H + 200`, reset.

**Now, let me write the actual full code.**

I realize there's a lot of nitpicking. Let me write it step by step and produce a working final code.

I'll update the AI gap detection: because the player moves at 5.2, and jump clears ~200px horizontal, the lookahead should be around 80px. But if the gap is 90px, the AI might detect no ground ahead 80px before the edge, jump, and clear it. It might not jump if the lookahead starts over the gap? I'll use:

```js
let aheadX = player.x + (player.facing > 0 ? 60 : -40); // use facing direction
```

Better: always move right in the demo. I'll check 90px ahead.

Also, in the gap detection, I should check for any ground at `footY + 4` in a rectangle ahead. If no ground (not even a one-way platform) at the point, jump.

Since the level has gaps wider than the character, this should work.

For coins above, the AI should jump only if there's a platform above? It might jump under a floating platform and bonk. But we're using one-way platforms, so no bonk. The AI can jump through. Good.

**Now, I need to handle variable jump height:**

In player update:
```js
// if jumpPressed and onGround, set vy
if (player.jumpPressed) {
    if (player.onGround) player.vy = JUMP_VEL;
    player.jumpPressed = false;
}
// Variable jump: reduce upward velocity when jump released
if (!keys['Space'] && !keys['ArrowUp'] && player.vy < -5) player.vy = -5;
```

I need to track whether the space was just pressed. I'll use `player.jumpPressed` set by edge detection.

Actually, for cleaner:
- `player.jumpHeld` = current key state.
- `player.jumpWasHeld` = previous frame's held.
- if `!player.jumpWasHeld && player.jumpHeld` then a new press -> set `player.jumpPressed = true`.
- At the end of the frame, `player.jumpWasHeld = player.jumpHeld`.

Let me code that.

**Input edge detection with AI:**

I'll create `let input = {left:false, right:false, jump:false}`. In the update:

```js
let heldLeft = keys['ArrowLeft'] || keys['KeyA'];
let heldRight = keys['ArrowRight'] || keys['KeyD'];
let heldJump = keys['Space'] || keys['ArrowUp'] || keys['KeyW'];
if (demoMode) {
    updateAI();
    heldLeft = aiAction.left;
    heldRight = aiAction.right;
    heldJump = aiAction.jump;
}

// Edge detection
if (heldJump && !player.jumpWasHeld) player.jumpPressed = true;
player.jumpWasHeld = heldJump;
```

For AI, I should set `aiAction.jumpPressed`? The AI can just hold `jump` for the desired frames. Since the variable jump uses `heldJump` for cut-off, the AI should hold jump while in the air to maximize height. I'll set `aiAction.jump` to true during a jump for 20 frames, then false. But the variable jump cut-off will immediately reduce vy if the AI releases. So the AI should hold jump for the full airtime to clear gaps. I'll make the AI hold jump if a jump was initiated until the next time it lands. Basically, once the AI decides to jump, keep `aiAction.jump = true` until `player.onGround` becomes true again. That gives a consistent full jump.

Let me implement in AI:
- `aiJumped` flag: if `aiAction.jump` and not onGround, keep holding.
- When onGround, set `aiAction.jump = false` (unless we want to jump again).

But the variable jump check in player code will always trigger if `heldJump` is true; that's fine.

**AI Function:**

```js
let aiAction = {left:false, right:false, jump:false};
function updateAI(dt) {
    // always move right
    aiAction.left = false;
    aiAction.right = true;
    
    // if the player is in the air, keep the jump held as long as we initiated it
    if (!player.onGround) {
        if (aiJumping) {
            aiAction.jump = true;
        }
    } else {
        aiJumping = false;
        aiAction.jump = false;
    }
    
    if (player.onGround && !player.jumpPressed) {
        // check for gaps/enemies/coins ahead
        let look = 80;
        let aheadX = player.x + player.w + look;
        let footY = player.y + player.h + 4;
        let hasGround = platforms.some(p => !p.oneWay && aheadX >= p.x && aheadX <= p.x + p.w && footY >= p.y && footY <= p.y + p.h);
        let shouldJump = false;
        if (!hasGround) shouldJump = true;
        // enemy ahead
        for (let e of enemies) {
            if (!e.alive) continue;
            if (e.x > player.x && e.x < aheadX + 40 && Math.abs(e.y - player.y) < 60) {
                shouldJump = true;
                break;
            }
        }
        // coin ahead and above
        for (let c of coins) {
            if (!c.collected && c.x > player.x && c.x < aheadX && c.y < player.y - 10) {
                shouldJump = true;
                break;
            }
        }
        if (shouldJump) {
            aiAction.jump = true;
            aiJumping = true;
        }
    }
}
let aiJumping = false;
```

This AI might jump at gaps too early (e.g., looking 80px ahead and jumping as soon as the ground ends, which is exactly at the edge). Since the gap is at the edge, `hasGround` is false when `aheadX` is just past the edge. So it jumps when the player is 80px before the edge. That's good timing. The player will jump at that point and clear the gap. The jump takes 46 frames, covers 240px, so jumping 80px early is perfect.

However, `aheadX` uses the right edge of the player plus 80. So the lookahead point is 80px ahead of the right edge. When the point is inside a gap, the player is 80px before the platform ends. At that point, the player's right edge is 80px from the edge. The jump will lift them 80px later as they move right; by the time they reach the edge, they're already 80px into the jump, so they have some height. Good.

**AI Edge Cases:**

- For a wide gap, it may need to jump exactly at the edge, not 80px before, because the jump has limited range. If the player jumps 80px before the edge, they travel the whole jump while the gap is ahead; the horizontal distance from the edge to the landing is `gap?`. Actually, if the gap is 120px, the player needs to travel from 80px before the gap to 120px past it = 200px. The max jump distance is ~240px, so it's fine. For larger gaps (200px), they might need to jump at the edge. I'll set lookahead to 60px to be safe. Or detect the gap and wait until closer. Let's not overcomplicate; with my level gaps they'll be <=150px.

**Now, let's write the final code.**

I'll put all constants at the top, then the helper functions, then the update/render loop.

Let me write it fully and carefully.

One more thing: the game canvas size. I'll make it 960x540 and fill using CSS. Use `ctx.imageSmoothingEnabled`? Not needed.

Let me now produce the final answer with the full HTML/JS code.

I'll structure it as:

```html
<!DOCTYPE html>
<html>
<head><style>...</style></head>
<body>
<canvas id="game" width="960" height="540"></canvas>
<script>
// ...
</script>
</body>
</html>
```

I'll make sure the code is complete and self-contained. Let me go ahead and write it.

Actually, before final, let me reason through a few tricky code parts.

**Issue: Platform collision with `prevY`**. In `moveEntity`, I store `const prevY = e.y` at the very start, before X movement. But if the X movement moves the player into a platform, then Y movement is later. For top collision, I compare `prevY + e.h <= p.y + 4`. Since `prevY` is from before Y movement, this is correct. But if the X movement moved the player horizontally, `prevY` is still the initial Y. That's fine.

**Issue: Moving platform collision**. The moving platform's `p.dx` is computed in `updateMovingPlatforms`. When a player stands on it, `player.currentPlatform` is set to `p`. After collision, `player.x += p.dx`. But what if the player is not standing on the platform but is standing on ground next to it? `currentPlatform` would be the ground, not the moving platform. Good.

**Issue: The player's `currentPlatform` gets cleared in `moveEntity` if `!e.onGround`. But if the player is standing on a moving platform and the platform moves such that the player is floating for a frame, `onGround` is false, so `currentPlatform` is cleared, and then the update after collision tries to add `p.dx`? Let me check the order:**

1. `moveEntity` clears `currentPlatform` if `!e.onGround`.
2. Then after `moveEntity`, I check `if (player.currentPlatform && player.currentPlatform.moving)` and add `dx`. But since it was cleared, it won't add. That's fine: if the player lost contact, no riding.

But the player might still be overlapping due to the platform moving; `moveEntity` usually catches it. Anyway, it's acceptable.

**Issue: X push-back when riding into a wall.** If we add `p.dx` to player.x and it pushes the player into a wall, the player might get stuck. We can prevent by clamping: after adding `p.dx`, run a quick X collision for solid platforms. That's extra work. For the demo, moving platforms are placed away from walls, so it's fine.

**Issue: Enemy drawing over the player.** Draw order: background -> platforms -> coins -> enemies -> player -> particles -> HUD. That's fine.

**Issue: HUD text.** Use `ctx.font = '15px monospace'`.

**Now, writing the code in full.**

Let me define the `addGround`, `addPlatform`, etc., as closures inside `buildLevel` using the global arrays.

I need `GROUND_TOP` at 470 maybe, leaving a bit more bottom area. Let me set `GROUND_TOP = 470`, so there's 70px of ground at the bottom. The background can have land at y=470 to 540. So the ground height is 70px.

`levelHeight = 540`.

For the camera Y, it stays at 0 because the level is only 540 tall and the ground is at the bottom; the player y is between GROUND_TOP-40=430 and 0. No need for vertical camera. I'll set `camera.y=0` always. The player can jump to a height of ~150px, so the top of the screen shows y>=0. The player may go above the top? With ground at 470, the player's top is at 430 and can jump to 280, so always on screen. Good. I'll not use vertical camera.

**Level layout with GROUND_TOP=470:**

Ground segments:
- 0-900
- 1000-1500
... I need to build without conflicting gaps at the same y. Let me just do:

```js
addGround(0, 1200);
addGround(1200, 100); // gap from 1200 to? Wait, 1200 to 1300 is the second ground. If I want a gap, I do 1200-1300 gap? Actually, first ground goes 0-900, gap 900-1000, then 1000-2000, etc.
```

So:
- `addGround(0, 900)` => x=0, w=900 (ends at 900)
- `addGround(1000, 900)` => x=1000, w=900 (ends at 1900) -> gap of 100px
- `addGround(2000, 800)` => gap from 1900 to 2000
etc.

But I also need ledges? Not needed; the ground is the main platform.

Let me make the level user-friendly: gaps not too large, and coins above them.

Let `addGround(x, w)`.

I'll place platforms (one-way) over the gaps sometimes.

**Now, specific layout:**

Let me write it:

```js
function buildLevel() {
    // screen 1
    addGround(0, 1000);
    addPlatform(500, 360, 100);
    addEnemy(300, GROUND_TOP - 28, 200, 800);
    addCoin(200, 360); addCoin(240, 360); addCoin(280, 360);
    // screen 2
    addGround(1100, 800); // 1100-1900
    // gap 1900-2000
    addPlatform(1900, 340, 80); addPlatform(1900, 380, 80); // floating platforms over the gap? Actually over the gap, the ground is absent. Put platforms at y=360, maybe.
    addGround(2000, 800); // 2000-2800
    // gap 2800-3000? Let me make bigger later.
}
```

This is getting messy. Maybe I should design the level more deliberately:

Let me create a list of platforms:

- Ground 0 - 850

- Ground 950 - 1850  (gap 850-950)

- Floating platforms at x=850, y=400 and x=950, y=340 to help cross the gap.

- Ground 1950 - 2850 (gap 1850-1950)

- Ground 2950 - 3850 (gap 2850-2950) -> Actually, let's alternate gap and platform? I want the level to have some challenge. Ok, let's just hardcode a list:

```
Ground segments:
[0, 1200]
[1300, 2300]
[2400, 3300]
[3400, 4300]
[4400, 5300]
[5400, 6600]
```
Gaps: 1200-1300 (100), 2300-2400 (100), 3300-3400 (100), 4300-4400 (100), 5300-5400 (100). All 100px gaps. The player can clear 150px with jump, so okay.

I'll also add moving platforms over some gaps:
- moving platform at x=1200, y=420, ranges 50 (so it goes from 1200 to 1250), bridging the gap.

Actually, since gaps are 100px and the player can jump them, moving platforms are more flavor than necessary.

Let me add one moving platform over a gap at 5300, because it's a big gap at 5300-5400 maybe 120px.

Let me place enemies along the ground:
- Enemy 1 at 500, ground 0-1200, dir left, range 150-700.
- Enemy 2 at 1600, on ground 1300-2300, range 1400-2200.
- etc.

Coins:
- A row at y=360 above some ground segments.
- Coins above the gaps to guide.

**Extended design:**

Let me just code the buildings and it will be fine.

For the goal: flag at x=6500, ground extends to 6600.

I'll add `addFlag(6500)`? I'll just check if `player.x > 6500-20`.

Now, let's write the code. I'll try to be thorough but not over-the-top.

**AI bug potential:** The AI looks for `platforms.some(p => !p.oneWay && ...)`. If the player is at y=470 and the gap is 100px, the lookahead point at 80px will be over the gap only when the player is 80px from the gap? Wait, if the platform ends at 1200 and the player is at 1120 (right edge + 80 = 1200), that's exactly at the platform end. So when the right edge + 80 = 1200, it's just at the edge. That means the player is at x=1196 (right edge = player.x + 24). So `aheadX = player.x + 24 + 80`. If `aheadX > 1200`, no ground at that point, the AI jumps. The player's right edge is 80px from the edge at the moment of the jump. That's good.

Actually, at that moment, the player's left edge is `player.x = 1200 - 104 = 1096`. The player is still mostly on the ground. The jump starts as they approach the edge. They'll take about `80/5.2 = 15` frames to reach the edge, during which they've already risen. So they cross the gap with some upward velocity, good.

**Jump discontinuity:** The variable jump cut-off: `if (!heldJump && player.vy < -5) player.vy = -5;` reduces upward speed. If the AI holds jump, it works. If not, the jump is truncated. Good.

**Vertical collision for one-way platforms:** The condition `prevY + e.h <= p.y + 4` allows passing through from below. This works because if the player's previous feet position was above the platform's top (within 4px tolerance). If the player is moving upward through it, `prevY + e.h <= p.y + 4` might be true if the player's feet are just below the platform's top (since y decreases upward). But the player's feet would be below the platform's bottom when coming from below. Actually, when moving up, `player.vy < 0` (negative, moving up). `prevY + e.h` is the old bottom. If the old bottom is just below the platform's top (`p.y + 4`), the player can pass through. For movement upward, the player's old bottom is below the platform's top? Wait, the player is below the platform moving up. The bottom is above? Actually, if the platform is above the player, the player's bottom is below the platform's top. `prevY + e.h = player's bottom old`. If `prevY + e.h <= p.y + 4`, it means the old bottom is above the platform's top? No, smaller y is higher. So if prevY + e.h is <= p.y + 4, the old bottom is above the platform's top (since screen y smaller = higher). But the player is below the platform, so their bottom is BELOW the platform's top, i.e., `prevY + e.h > p.y`. Therefore `prevY + e.h <= p.y + 4` is false, so no collision. Good. When moving down, `prevY + e.h` is the previous bottom, which is higher (smaller y) than the new bottom. If the player falls onto the platform, the previous bottom must be above the platform's top (or within 4px). Since the player is above the platform, `prevY + e.h <= p.y + 4` is true. So the player lands. This is the classic approach.

For solid platforms (not one-way), I use the same condition for top, but also bottom-side and side collision. The one-way continues even after landing, so if the player's feet are exactly at p.y + 1, it might work.

**Potential bug:** When the player is standing on a one-way platform and moves horizontally, the condition `prevY + e.h <= p.y + 4` may fail if the platform top is a bit below the player's feet (because the player is standing on it, prevY + h = p.y). Since `prevY + h == p.y`, the condition is true. So the collision works. Good.

**Now, I'll write the final code.**

It's long, but I'll include it. Let me code.

I'll adjust the enemy speed to 1.2, gravity for enemies = 0.6.

I'll add a `timer` for the death animation? For now, on `playerHit`, I'll simply reset the level. Since there are no checkpoints, it's a full reset. But that might be frustrating if the player dies near the end. Let me add one checkpoint at x=3000? Simpler: on hitting an enemy, the player becomes invincible for a moment and bounces back? Let me implement a simple health? Or just death and reset. I'll go with reset.

Wait, the player can stomp enemies. If the player hits an enemy from the side, a death reset is too harsh. But it's an arcade game; okay. I'll keep it.

**Let me write the code.** I'll combine everything.

After writing, I'll double-check for syntax errors.

Let me write `addCoin` to set x, y as the top-left? Or center? I'll store center and draw with `c.x - 8` etc.

The player hitbox top-left: (c.x, c.y). I'll store coins as `{x: x, y: y}` where (x,y) is the top-left of an 18x24 sprite? Actually, let me store the center for pickup drawing. I'll define `c.x = x`, `c.y = y`, and when drawing, draw at `c.x - 9, c.y - 12`. For pickup area, use center and half-size.

Similarly for enemies, top-left.

Ok. Let me finalize.

I'll produce the final answer.