We need to create a self-contained HTML file with a 2D platformer. Must include:
- Canvas rendering
- Original hero drawn with code as colorful pixel art
- Side-scrolling level at least 6 screens long
- Ground, floating platforms, gaps, moving platforms
- Coins to collect
- Enemies that walk back and forth, defeat by jumping on them
- Goal flag at end
- Parallax background layers (sky, clouds, hills)
- Coin counter and score
- Particle effects for coin collection and enemy defeat
- Win screen when flag reached
- Controls: Arrow Left/Right, Space/Up to jump, R to restart
- Autoplay demo mode toggled with P key (AI controls player)
- No external assets, vanilla JS, inline CSS/JS
- Single HTML file

We need to write a fairly complex game in one file. Let's plan the architecture.

We'll create a Game class managing state, entities, camera, input, AI, rendering.

Canvas size: maybe 640x360 (16:9) scaled up via CSS.

Pixel art hero: we can define a small sprite as a 2D array of colors, draw via fillRect per pixel.

Similarly for enemies, coins, flag, particles.

Level design: we can procedurally generate a level of certain length (e.g., 6 screens * 640 = 3840px wide). We'll define platforms as rectangles, some moving.

Parallax: three layers: sky (static color), clouds (slow), hills (faster). Draw as shapes.

Entities: Player, Enemy, Coin, MovingPlatform, Flag, Particle.

Physics: simple platformer physics with gravity, velocity, collision with platforms.

Camera follows player horizontally, with some lerp.

Score: coins * 100, enemies * 200.

Win screen: overlay with "YOU WIN!" and score, press R to restart.

Autoplay AI: simple logic: move towards next platform/coin/enemy/flag, jump when needed. Could implement a basic pathfinding: look ahead for obstacles, decide to jump. Since level is static, we can precompute a sequence of actions? But easier: implement a simple reactive AI: if gap ahead, jump; if enemy ahead, jump on it; if coin above, jump; move right generally.

We'll need to handle input for both human and AI.

Let's start coding.

We'll write HTML with canvas, style to center and scale.

We'll use requestAnimationFrame loop.

We'll define constants: GRAVITY, PLAYER_SPEED, JUMP_FORCE, etc.

We'll create a Level class that holds platforms, coins, enemies, moving platforms, flag.

Platforms: static platforms (ground, floating). Moving platforms: have path (start, end, speed).

Enemies: walk back and forth on platforms.

Coins: static positions.

Flag: at end.

Player: position, velocity, size, state (onGround, facing), animation frame.

Particle system: array of particles with position, velocity, color, life.

Rendering: draw background layers, then platforms, coins, enemies, flag, player, particles, UI.

UI: coin count, score.

Win condition: player touches flag.

Restart: reset game state.

Autoplay: toggle with 'P'. When active, AI controls player input.

AI implementation: We'll simulate a simple decision each frame:
- Desired direction: right (towards flag)
- Check for ground ahead: if no ground within small distance and not on ground, maybe jump.
- If wall ahead, jump.
- If enemy ahead on same platform, jump to stomp.
- If coin above reachable, jump.
- If moving platform alignment, wait? Keep simple.

Given time, we can implement a basic AI that plays decently.

We'll need to handle collision detection for AI to sense environment.

Simplify: Since level is generated procedurally but deterministic, we could record a perfect run and replay? But requirement: AI controls player competently. Could do a simple state machine: move right, jump when needed.

Let's design level generation: We'll create a function generateLevel() that returns arrays of platforms, coins, enemies, movingPlatforms, flag.

We'll make ground as a series of blocks with gaps. Floating platforms at various heights. Moving platforms horizontal.

We'll ensure at least 6 screens width (6*640=3840). Let's make level width 4000.

We'll use a grid of 32x32 tiles for simplicity.

But drawing pixel art hero: we can define a 16x16 sprite with colors.

Let's define hero sprite as array of strings representing colors.

We'll write a function drawSprite(ctx, sprite, x, y, scale) that draws each pixel.

Similarly for enemy, coin, flag.

Coin: simple rotating? Just draw a yellow circle with pixel art.

Flag: pole and flag.

Particle: small squares.

Now, code structure:

- HTML skeleton with canvas.
- CSS: canvas { display:block; margin:auto; background:#000; image-rendering: pixelated; } body { margin:0; background:#222; overflow:hidden; } #ui { position:absolute; top:10px; left:10px; color:white; font-family:monospace; font-size:20px; pointer-events:none; } #winScreen { position:absolute; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); display:none; flex-direction:column; align-items:center; justify-content:center; color:white; font-family:monospace; font-size:40px; } etc.

- JS: main code.

We'll write everything in one script tag.

Let's start coding step by step.

We'll need to be careful with performance but it's okay.

We'll use classes for entities.

Let's outline the code:

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Pixel Platformer</title>
<style>
...css...
</style>
</head>
<body>
<canvas id="game" width="640" height="360"></canvas>
<div id="ui">Coins: 0 | Score: 0</div>
<div id="winScreen"><div id="winText">YOU WIN!</div><div id="finalScore">Score: 0</div><div style="font-size:20px;margin-top:20px;">Press R to restart</div></div>
<script>
...js...
</script>
</body>
</html>
```

Now JS:

Constants:
- CANVAS_WIDTH = 640, CANVAS_HEIGHT = 360
- GRAVITY = 0.5
- PLAYER_SPEED = 3
- JUMP_FORCE = -12
- TILE_SIZE = 32

Game state variables.

We'll create a Game object with init, update, draw, handleInput, etc.

We'll implement input handling: keys pressed set.

AI: if autoplay, compute input based on AI logic.

Let's write the code.

We'll need to generate level. We'll do it in init.

Level generation:

We'll create ground: from x=0 to levelWidth, with some gaps. We'll create platforms as rectangles {x, y, w, h}. Ground platforms at y = CANVAS_HEIGHT - 32 (bottom). But we have camera, so world coordinates.

We'll set world width = 4000.

Ground: create a series of ground blocks, each 32 wide, but randomly omit some to create gaps (but ensure passable). We'll make gaps of 2-3 tiles.

Floating platforms: place at various x, y.

Moving platforms: define startX, endX, y, speed.

Enemies: place on platforms, patrol between platform edges.

Coins: place on platforms or in air.

Flag: at worldWidth - 100, on ground.

We'll store all platforms in an array for collision.

Collision detection: player AABB vs platform AABB.

Moving platforms: they move horizontally, carry player if standing on them.

We'll need to update moving platforms each frame.

Enemies: update position, reverse at edges or walls.

Player update: apply gravity, handle input, move horizontally, check collisions, vertical collisions.

Coin collection: check distance.

Enemy stomp: if player falling and hits enemy top, bounce and kill enemy, add score, particles.

Flag touch: win.

Particles: update and draw.

Parallax: draw sky gradient, clouds (circles) moving slowly, hills (triangles) moving faster.

We'll implement drawBackground() with camera offset.

Now, AI:

We'll create a function getAIInput(player, level, camera) that returns {left, right, jump}.

Simple logic:
- Target: flag.x
- If player.x < flag.x, want to move right.
- Check for obstacles ahead: look at player.x + player.width + 20, see if there is ground at player.y + player.height (i.e., floor). If not, and player.onGround, jump.
- If there is a wall ahead (platform blocking at player's y level), jump.
- If enemy ahead on same platform, jump.
- If coin above within jump reach, jump.
- Also, if player is on moving platform, maybe wait? But keep moving right.

We'll need helper functions to query level geometry at a given x,y.

We can create a function getGroundHeightAt(x) that returns the y of the topmost platform at that x (within some range). But platforms are rectangles, so we can check.

Simplify: Since level is not too complex, we can precompute a "navigation mesh" but that's heavy. Instead, we can raycast: from player's feet forward, check if there is a platform within 50px horizontally at same y level. If not, jump.

Also check for ceiling? Not needed.

We'll implement a simple sensor: 
- frontSensorX = player.x + player.width + (player.facingRight ? 20 : -20)
- Check if there is a platform at (frontSensorX, player.y + player.height) (i.e., ground). If not, and player.onGround, jump.
- Also check for wall: at player's mid height, if platform at frontSensorX, then jump.

We'll also need to handle gaps: if there is a gap, the ground check will fail, so jump.

We'll also check for enemies: if enemy in front and on same platform, jump.

We'll also randomly jump sometimes to collect coins? But not necessary.

We'll also need to handle moving platforms: if player is on a moving platform, we might need to stay on it. But AI can just treat it as ground.

Given time, we'll implement a basic AI that can complete the level if level is not too tricky. We'll design level to be AI-friendly: no precise timing required, moving platforms slow, gaps not too wide.

We'll test mentally.

Now, let's write the code.

We'll need to be careful with variable scopes.

We'll write the entire JS in the script tag.

Let's start.