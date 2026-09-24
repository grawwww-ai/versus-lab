User wants a complete self-contained HTML file with a polished side-scrolling 2D platformer game. Let me break down all the requirements:

1. **Style**: 16-bit classics, colorful pixel art drawn with code
2. **Original hero**: NOT an existing character, drawn with code as pixel art
3. **Level design**: 
   - Horizontal scrolling
   - At least 6 screens long
   - Ground, floating platforms, gaps, moving platforms, coins, enemies, goal flag

4. **Enemies**: Walk back and forth, defeated by jumping on them

5. **Parallax background**: Sky, clouds, hills

6. **UI**: Coin counter, score

7. **Particle effects**: When collecting coins or defeating enemies

8. **Win screen**: When flag is reached

9. **Controls**: 
   - Arrow Left/Right to move
   - Space or Arrow Up to jump
   - R to restart

10. **Autoplay demo mode**: Toggle with P, AI plays the game

11. **No external assets**: All code-drawn

12. **Vanilla JS**: No libraries

13. **One self-contained HTML file**

Let me design this carefully:

**Hero**: A pixel art character - let me design a little robot or adventurer with a distinct look. I'll draw them pixel by pixel using fillRect calls or a pixel map.

**Level**: 6+ screens worth of platforms, gaps, coins, enemies.

**Camera**: Follows the player, scrolls right.

**Parallax**: 
- Sky: gradient background
- Clouds: slow-moving cloud shapes
- Hills: parallax hills at different depths

**Game mechanics**:
- Player has velocity, gravity
- Jump on enemies to defeat them
- Coins give points
- Moving platforms move vertically or horizontally

Let me plan the code structure:

```
- Game state
- Input handling
- Player object
- Camera
- Level data
- Enemy management
- Coin management
- Platform management
- Particle system
- Parallax background rendering
- UI rendering
- Win/lose conditions
- Autoplay AI
- Game loop
```

Let me think about the pixel art approach. Since we need pixel art with code, I'll use a function that draws a character based on a 2D array or use fillRect calls in a drawing function.

For the hero, let me create a little robot character. I'll use a pixel grid approach:

```javascript
const HERO_SPRITE = [
  "..RRRR..",
  ".RRRRRR.",
  ".RBBBBR.",
  ".RBRRBR.",
  ".RRRRRR.",
  "..RRRR..",
  ".RRRRRR.",
  "RRR..RRR",
  "RRR..RRR",
  "..R..R..",
  ".RR..RR.",
];

// R = red, B = blue, etc.
```

Actually, let me use a numeric/color-coded approach for the pixel art. Let me design a good hero.

Hero design - a little knight or adventurer:

```
"....RRRR....",
"..RRRRRRRR..",
".RRRRRRRRRR.",
".RRRRRRRRRR.",
".RRRBBBBRRR.",
".RRRBRRBRRR.",
".RRRBBBBRRR.",
"RRRRRRRRRRRR",
"RRRRRRRRRRRR",
"RRRRTTRRRRRR",
"RRRTTTTTRRRR",
"..RRRRRRRR..",
".RRRRRRRRRR.",
"RR..RRRR..RR",
"RR..RRRR..RR",
"RR..RRRR..RR",
"R....RR....R",
```

Hmm, this is getting complex. Let me simplify by creating a function that draws the hero using pixel data with specific colors.

Actually, let me think about this differently. I'll define sprites as arrays of strings, where each character represents a color:

```javascript
const HERO_SPRITE = [
  "..RRRR..",
  ".RRRRRR.",
  ".RBYWBR.",
  ".RBRWBR.",
  ".RBBBBR.",
  "..RRRR..",
  ".RRRRRR.",
  "RRR..RRR",
];
```

Each letter maps to a color. Let me define:
- R = red (hero body)
- B = blue (accents)
- Y = yellow (details)
- W = white (eyes)
- G = green
- etc.

Let me design the whole game now.

**Game constants**:
- Canvas size: 960x540 (16:9 aspect ratio)
- Tile size: 32px
- Gravity: 0.5
- Player speed: 4px/frame
- Jump velocity: -11

**Level design** (screen = 960px, so 6 screens = 5760px):
- Ground sections with gaps
- Floating platforms at various heights
- Coins placed on platforms and in the air
- Enemies patrolling

Let me plan the level layout. I'll use a ground array of booleans or heights.

Actually, for simplicity and to create a well-designed level, let me define the level as a series of objects:

```javascript
const platforms = [
  // Ground segments
  { x: 0, y: 500, w: 960, h: 40 },
  ...
];
```

But this is going to be huge with 6 screens. Let me think of a better approach.

I'll use a tile-based ground. The ground is at a fixed y, and there are gaps.

Let me think in terms of a tile map. Tile size = 32px. Canvas height = 540px. Ground at tile row 15 (y=480) to row 16 (y=512) or something.

Actually, let me simplify: Ground level at y=480, with gaps. Platforms are individual rectangles.

Level width: 6 * 960 = 5760px. Let me define the ground as segments.

Let me define the level programmatically or manually. For a polished look, manually designing the level is better.

I'll define the level as:

```javascript
const level = {
  ground: [
    // x, y, width, height
    { x: 0, y: 480, w: 900, h: 60 },  // Screen 1
    { x: 960, y: 480, w: 500, h: 60 }, // Screen 2 starts...
    // etc.
  ],
  platforms: [
    { x: 300, y: 400, w: 120, h: 16 },
    // etc.
  ],
  coins: [
    { x: 350, y: 360, },
    // etc.
  ],
  enemies: [
    { x: 200, y: 456, minX: 150, maxX: 300 },
    // etc.
  ],
  movingPlatforms: [
    { x: 500, y: 400, w: 80, h: 16, startX: 500, startY: 400, endX: 600, endY: 400, speed: 1 },
  ],
  flag: { x: 5600, y: 480 },
};
```

Actually, let me be more systematic. Let me design the level as a series of screen-sized chunks.

Screen width = 960px. I'll design 7 screens worth of content.

Actually, let me just design it with specific coordinates. Let me lay things out:

**Screen 0 (x: 0-960)**:
- Ground from 0 to 960, but with a gap at the end
- A few platforms
- Some coins
- 1-2 enemies

**Screen 1 (x: 960-1920)**:
- Ground with something...
- etc.

This is getting long. Let me just write the code now and design the level as I go.

Let me structure the code.

Actually, for a game like this, I'll use a more structured approach. Let me define:

1. **Player**: Position, velocity, size, onGround, etc.
2. **Camera**: x offset, follows player
3. **Entities**: Enemies, coins, platforms
4. **Particles**: For effects
5. **Level**: Defined data

Let me code this step by step:

```javascript
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
canvas.width = 960;
canvas.height = 540;

// Game state
let gameState = 'playing'; // 'playing', 'win', 'dead'
let score = 0;
let coinCount = 0;
let time = 0;
let lastTime = 0;
let deltaTime = 0;

// Input
const keys = {};

// Camera
let cameraX = 0;
let cameraY = 0;

// Player
const player = {
    x: 100, y: 400, w: 28, h: 40,
    vx: 0, vy: 0,
    onGround: false,
    facing: 1, // 1 = right, -1 = left
    isJumping: false,
};

// Constants
const GRAVITY = 0.5;
const MOVE_SPEED = 4.5;
const JUMP_FORCE = -11;
const MAX_FALL_SPEED = 12;
```

Alright, I need to be more deliberate about this. Let me write the complete file now.

Actually, let me reconsider the approach for the level. Instead of tile-based, I'll use entity-based level design:

- **Ground segments**: array of rectangles
- **Platforms**: array of rectangles (floating platforms)
- **Moving platforms**: have movement paths
- **Coins**: placed at positions
- **Enemies**: have patrol ranges
- **Flag**: one position

This gives me full flexibility.

Let me define the complete game now. I'll write a large, comprehensive HTML file.

Let me also think about the pixel art. For the hero, I'll define a sprite as a 2D array of color codes and draw it at the player's position, scaled by a factor. Since the player is about 28x40 pixels, I can draw each pixel of the sprite as a small rectangle.

Let me define the hero sprite more carefully. I want an original character. Let me make a little astronaut/robot with a distinctive look.

Hero: "Kai the Robot" - a small blue and white robot with glowing eyes.

```
Sprite (16x16 pixels, drawn at 2x scale = 32x32):
    
    "....BBBBBB....",
    "..BBBBBBBBBB..",
    ".BBBBBBBBBBBB.",
    ".BBWWWWWWWWBB.",
    ".BBWBBBBBBWBB.",
    ".BBWBBBBBBWBB.",
    ".BBWWWWWWWWBB.",
    ".BBBBBBBBBBBB.",
    "..BBBBBBBBBB..",
    "....BBBBBB....",
    "....BBBBBB....",
    "..BBBBBBBBBB..",
    "..BB..BB..BB..",
    "..BB..BB..BB..",
    "..BB......BB..",
    "..BB......BB..",
```

Hmm, that's a bit basic. Let me think of a better design.

Actually, let me use a simpler approach: draw the hero using canvas drawing commands (fillRect for each pixel of the sprite), but build the sprite from string data.

Let me define sprites as pixel maps:

```javascript
const HERO_SPRITE = [
    "....XXXX....",
    "..XXXXXXXX..",
    ".XXXXXXXXXX.",
    ".XOOOOOOXX..",
    ".XOXOOOXXX..",
    ".XOOOOOOXX..",
    ".XXXXXXXXXX.",
    "..XXXXXXXX..",
    "..XXXXXXXX..",
    "...XXXXXX...",
    "..XXXXXXXX..",
    ".XX....XX.XX",
    ".XX....XX.XX",
    ".X......X..X",
];
```

Actually, let me not overthink the pixel art. I'll create a clean, recognizable character using a 16x16 or 12x16 grid with a color mapping. Let me define:

Colors:
- `R` = red (or primary)
- `B` = blue (accent)
- `W` = white
- `K` = black (outline)
- `S` = skin
- etc.

Let me design a hero that's a little knight/robot:

```
".....RRRR.....",
"...RRRRRRRR...",
"..RRRRRRRRRR..",
"..RRBBBBBBRR..",
"..RRBWWWWBRR..",
"..RRBWWWWBRR..",
"..RRBBBBBBRR..",
"..RRRBBBBRRR..",
"..RRRRRRRRRR..",
"...RRRRRRRR...",
"....RRRRRR....",
"...RRRRRRRR...",
"..RRRRRRRRRR..",
"..RR......RR..",
".RRR......RRR.",
"................",
```

Okay let me just write the code. I'll create the sprite drawing as a function that draws a pixel map.

Actually, for clarity and simplicity, let me define the hero as a function that draws a colorful character using fillRect calls. It's not truly "pixel art" in the sense of being built from a sprite map, but it's drawn with code and looks pixelated.

Let me step back and think about what matters most:
1. Polish and visual appeal
2. Gameplay feel
3. Me having fun writing this

Let me write the full game now. I'll create a comprehensive file.

Here's my plan for the code:

```
<!DOCTYPE html>
<html>
<head>
<style>
  /* page styles */
</style>
</head>
<body>
<canvas id="game"></canvas>
<script>
// ====== GAME CODE ======
// ... all the code
</script>
</body>
</html>
```

Let me now write the complete game. This is going to be a large file, so let me be organized.

Actually, I realize there's going to be a LOT of code here. Let me be methodical.

**Constants and Setup:**
- Canvas dimensions
- Game constants
- Level definition

**Pixel Art:**
- Hero sprite map
- Enemy sprite map
- Coin sprite
- Flag sprite

**Game Objects:**
- Player
- Enemies
- Coins
- Platforms
- Moving platforms
- Particles

**Rendering:**
- Parallax background (sky, clouds, hills)
- Level rendering
- Sprite rendering
- UI rendering

**Game Logic:**
- Physics
- Collision detection
- Input handling
- Camera
- Win/lose
- Autoplay AI

Let me code this now. I'll focus on making it playable and polished.

For the level design, let me define the ground as segments with gaps, platforms, coins, enemies, and moving platforms across 6+ screens.

Here's my level plan (total width ~5760px):

**Screen 0 (x: 0-960):**
- Ground: x=0, w=960 (solid)
- Platform: {x: 350, y: 400, w: 120, h: 16}
- Coins: on platform
- Enemy: walking at ground level, x=200-600

**Screen 1 (x: 960-1920):**
- Ground: gap from 960 to 1050, then continues
- Platform: {x: 1200, y: 380, w: 100, h: 16}
- Moving platform: {x: 1500, y: 400, w: 80, h: 16, moves vertically}
- Enemies: two on ground

**Screen 2 (x: 1920-2880):**
- Ground: with a gap
- Floating platforms over the gap
- Coins
- Enemies

**And so on...**

Let me simplify by just creating a long array of objects. For a good level, I'll create:

```javascript
const GROUND_Y = 480; // Ground top at y=480
const GROUND_HEIGHT = 60;

const level = {
    width: 5760,
    ground: [
        { x: 0, w: 2400 },
        { x: 2560, w: 800 },
        // ... etc
    ],
    platforms: [
        { x: 300, y: 400, w: 120, h: 16 },
        // ...
    ],
    movingPlatforms: [
        { x: 0, y: 0, w: 80, h: 16, path: { type: 'horizontal', from: 500, to: 700, speed: 1 } },
        // ...
    ],
    coins: [
        { x: 320, y: 360 },
        // ...
    ],
    enemies: [
        { x: 200, minX: 100, maxX: 400 },
        // ...
    ],
    flag: { x: 5700, y: GROUND_Y },
};
```

Wait, I need to think about ground physics. If the ground is an array of rectangles {x, w}, then the player can stand on any of them. But I need to handle edges.

Actually, let me make the ground height high enough that we don't need to worry about the bottom (just y=480 to y=540, which is the bottom of the canvas).

For the player to stand on ground, I check if the player's bottom edge crosses the ground top and their x is within the ground's x range.

Let me also define the player size. I'll make the player 24x40 pixels (w x h), which is a reasonable size for a 16-bit style character.

Hmm, but for the pixel art to be visible, the player needs to be a reasonable size. Let me make the hero 32x48 pixels and use a 16x24 pixel sprite scaled by 2.

Actually, let me just use 32x48 and draw it with fillRect calls for each pixel at 2x scale.

Wait, I'm overcomplicating this. Let me define the hero sprite on a 16x24 grid, where each cell is drawn at 2x2 pixels on screen, giving a 32x48 pixel hero. That's good.

Let me define a simpler hero sprite map. I'll use characters to represent colors:

```
"................",
"................",
"....RRRRRRRR....",
"..RRRRRRRRRRRR..",
".RRRRRRRRRRRRRR.",
".RRBBBBBBBBBBRR.",
".RRBWWWWWWWWBRR.",
".RRBWWWWWWWWBRR.",
".RRBBBBBBBBBBRR.",
".RRRRRRRRRRRRRR.",
"..RRRRRRRRRRRR..",
"..RRRRRRRRRRRR..",
"...RRRRRRRRRR...",
"....RRRRRRRR....",
"....RRRRRRRR....",
"....RRRRRRRR....",
"..RRRRR..RRRRR..",
"..RRR......RRR..",
"..RR........RR..",
"................",
```

This is a 20x20 grid, but close enough. Actually, let me use a standard size.

Let me define the hero sprite more carefully. I'll use a 12x16 pixel grid and scale by 3.

Actually, you know what, I'm spending too much time on the sprite. Let me define a simple but effective character drawing with a function.

Here's my final approach for the hero: I'll define the sprite as a 2D array of color strings or characters, and draw it with `fillRect` calls.

```javascript
const HERO = [
    "....XXXX....",
    "..XXXXXXX...",
    ".XXXXXXXXX..",
    ".XWWWWWWXX..",
    ".XWWXWWXXX..",
    ".XWWWWWWXX..",
    ".XXXXXXXXX..",
    "..XXXXXXX...",
    "...XXXXX....",
    "..XXXXXXX...",
    ".XXXX.XXXX..",
    ".XXX...XXX..",
];
```

This is 12x12. Let me add more rows for legs.

Actually, let me just code it and iterate. I've been overthinking. The important thing is that it looks like a pixelated character and is original.

Let me now write the complete code. I'll be careful about:

1. **Parallax backgrounds**: Draw sky as gradient, clouds as simple rounded rects/blobs, hills as semicircles/polygons at different scroll speeds.

2. **Physics**: Clean collision detection.

3. **Controls**: Responsive movement.

4. **Autoplay AI**: Simple state machine: run, jump, sometimes wait. The AI needs to know where to go. I'll give it simple rules based on obstacles ahead.

Let me start coding. I'll create a complete, working game.

Actually, let me write the code now without overthinking.

Key concern: the AI for autoplay mode. How to make it play competently?

For autoplay, I can:
1. Have the AI look at what's ahead: platforms, gaps, enemies, coins.
2. Make decisions: if there's a gap ahead, jump. If there's an enemy, jump on it. If there's a wall, jump over it.

A simple approach: the AI checks what's a few pixels ahead:
- If there's no ground ahead (gap), jump.
- If there's an enemy ahead at ground level, jump.
- If there's a platform above, maybe jump.
- Otherwise, keep running right.

I'll also add some logic to collect coins: if there are coins above, jump to get them.

Let me write the AI as a simple reflex agent:

```javascript
function autoplay() {
    // Look ahead
    const aheadX = player.x + player.w + 5;
    const aheadY = player.y;
    
    // Check for gap
    const groundAhead = isGround(aheadX, player.y + player.h + 5);
    // Check for enemy ahead
    const enemyAhead = enemies.some(e => 
        e.x > player.x && e.x < player.x + player.w + 100 && 
        Math.abs(e.y - player.y) < 40 && !e.dead
    );
    
    // Check for coin above
    const coinAbove = coins.some(c => 
        Math.abs(c.x - player.x) < 80 &&
        c.y < player.y && c.y > player.y - 100 && !c.collected
    );
    
    if (!groundAhead) {
        // Jump if there's a gap
        pressJump();
    } else if (enemyAhead) {
        pressJump();
    } else if (coinAbove && player.onGround) {
        pressJump();
    } else {
        holdRight();
    }
}
```

This needs to be more sophisticated. For instance, if there's a gap that's too wide, the AI needs to jump earlier. And if there's an enemy, it needs to time the jump properly.

Let me make the AI look at a longer range and make decisions based on the next "obstacle". I'll precompute the next obstacle as:
- The next gap
- The next enemy
- The next elevated platform

And then the AI decides based on the closest obstacle.

Actually, for simplicity and effectiveness, let me give the AI more context:

```javascript
function autoplay() {
    const px = player.x;
    const py = player.y;
    const pw = player.w;
    const ph = player.h;
    
    // Find next gap
    let nextGapX = level.ground.find(g => g.x + g.w > px && g.x > px)?.x ?? Infinity;
    // Actually this won't work perfectly with multiple ground segments
    
    // Better: find the right edge of the current ground segment
    const currentGround = level.ground.find(g => px >= g.x - 10 && px <= g.x + g.w);
    let groundEnd = currentGround ? currentGround.x + currentGround.w : px + 200;
    let gapDistance = groundEnd - px;
    
    // Find next enemy
    let enemyNear = null;
    for (const e of enemies) {
        if (!e.dead && e.x - px > -20 && e.x - px < 150) {
            if (Math.abs(e.y - py) < 60) {
                enemyNear = e;
                break;
            }
        }
    }
    
    // Find next coin that's above
    let coinAbove = null;
    for (const c of coins) {
        if (!c.collected && Math.abs(c.x - px) < 100 && c.y < py - 10 && c.y > py - 120) {
            coinAbove = c;
            break;
        }
    }
    
    // Decision
    const shouldJump = gapDistance < 60 || (enemyNear && gapDistance > 20) || (coinAbove && player.onGround);
    
    if (shouldJump && player.onGround) {
        player.vy = JUMP_FORCE;
        player.onGround = false;
    }
    
    // Move toward target
    if (enemyNear && enemyNear.x > px) {
        // If enemy is close and to the right, jump
        if (Math.abs(enemyNear.x - px) < 50 && player.onGround) {
            player.vy = JUMP_FORCE;
            player.onGround = false;
        }
    }
    
    // Move right always
    player.vx = MOVE_SPEED;
    player.facing = 1;
}
```

This is getting complicated. Let me simplify. I'll make the AI:
1. Always hold right
2. Jump when there's a gap ahead
3. Jump when an enemy is close
4. Jump when there's a coin above and the player is on the ground

This should be enough to play the level, especially if the enemies are positioned so that jumping over them works.

Actually, I need to make the AI jump at the right time, not too early or late. Let me add a "jump buffer" so the AI presses jump a few frames before reaching the obstacle.

Let me use a simpler approach: the AI has a `wantsToJump` flag. When the flag is true and the player is on the ground, jump.

```javascript
let aiJumpRequested = false;

function autoplay() {
    const px = player.x;
    const py = player.y;
    
    // Check hazards ahead
    let shouldJump = false;
    
    // Check gap ahead
    const lookAheadX = px + player.w + 40;
    const groundAhead = isGroundAt(lookAheadX, py + player.h + 10);
    if (!groundAhead) shouldJump = true;
    
    // Check enemy ahead
    for (const e of enemies) {
        if (e.dead) continue;
        if (e.x + e.w > px && e.x < px + player.w + 80) {
            if (Math.abs(e.y - py) < 50) {
                shouldJump = true;
                break;
            }
        }
    }
    
    // Check coin above
    for (const c of coins) {
        if (c.collected) continue;
        if (Math.abs(c.x - px + player.w/2) < 60 && 
            c.y < py && c.y > py - 120) {
            shouldJump = true;
            break;
        }
    }
    
    // Apply input
    keys['ArrowRight'] = true;
    keys['D'] = true;
    player.vx = MOVE_SPEED;
    player.facing = 1;
    
    if (shouldJump && player.onGround) {
        player.vy = JUMP_FORCE;
        player.onGround = false;
    }
}
```

This is a reasonable autoplay. The AI will jump when there's a gap, an enemy, or a coin above. It'll keep moving right.

But I need to make sure the level is designed so that the AI can complete it. The gaps shouldn't be too wide (relative to the jump distance), and the platforms should be reachable.

The player's jump: horizontal speed = MOVE_SPEED = 4.5 px/frame. Jump time = 2*11/0.5 = 44 frames (up + down). So horizontal distance = 44*4.5 = 198px. So a gap of maybe 100-120px is comfortably jumpable. Let me keep gaps ≤ 100px. Max jump height = 11^2/(2*0.5) = 121px. So platforms shouldn't be more than 120px above ground.

Actually, with the AI always pressing right and using the same input, it should be able to clear gaps up to about 150px wide.

Let me design levels with gaps:
- Narrow gaps: 80-100px
- Medium gaps: 120px
- Platforms: max 100px above ground

Now let me plan the level more concretely.

**Level Layout (total width ~6000px):**

Screen 0 (0-960):
- Ground: (0, 480, 960, 60) - solid ground
- Platform: (350, 400, 120, 16) with 3 coins on top
- Coins: (370, 360), (390, 360), (410, 360)
- Enemy: (500, 456, patrol 400-600)

Screen 1 (960-1920):
- Ground: (960, 480, 400, 60) - gap from 1360 to 1440
- Ground: (1440, 480, 480, 60)
- Platform: (1200, 380, 100, 16) - above first ground segment
- Moving platform: (1700, 420, 80, 16, vertical path 400-460)
- Coins: (1220, 340), (1700, 380)
- Enemy: (1050, 456, patrol 1000-1200)
- Enemy: (1500, 456, patrol 1450-1650)

Screen 2 (1920-2880):
- Ground: (1920, 480, 960, 60) with gap at 2600-2700
- Actually let me make this more interesting.

Okay, I'm going to spend too long designing the level manually. Let me just create a script that generates a decent level automatically, or define it inline with enough detail.

Let me just code it as arrays and design it carefully.

I'll now write the full code. Let me be thorough.

Actually, one more thing about the hero sprite. Let me define it as a 2D color map and create a draw function. I'll make it simple.

Here's my plan for the full file organisation:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Pixel Quest</title>
    <style>
        /* styling */
    </style>
</head>
<body>
    <canvas id="gameCanvas" width="960" height="540"></canvas>
    <script>
        // Complete game code
    </script>
</body>
</html>
```

Let me now write it.

Important: the code needs to draw pixel art using `fillRect`. Each pixel in the sprite map corresponds to a small rectangle on screen, scaled.

For the hero sprite, I'll do something like:

```javascript
function drawHero(ctx, x, y, facing) {
    const sprite = HERO_SPRITE;
    const scale = 2;
    for (let row = 0; row < sprite.length; row++) {
        for (let col = 0; col < sprite[row].length; col++) {
            const color = COLOR_MAP[sprite[row][col]];
            if (color) {
                const px = x + col * scale;
                const py = y + row * scale;
                ctx.fillStyle = color;
                ctx.fillRect(px, py, scale, scale);
            }
        }
    }
}
```

This approach works well for pixel art.

Let me define the sprites now.

Hero (12x16 grid, scale 3 = 36x48):

```
"....BBBB....",
"..BBBBBBBB..",
".BBBBBBBBBB.",
".BBWWWWWWBB.",
".BBWWWWWWBB.",
".BBWDBBWWBB.",
".BBWWWWWWBB.",
".BBBBBBBBBB.",
"..BBBBBBBB..",
"...BBBBBB...",
"...BBBBBB...",
"..BBBBBBBB..",
".BBBB..BBBB.",
".BBB....BBB.",
"BBB......BBB",
"................" // whatever
```

Actually, this is hard to design without visual feedback. Let me use a simpler approach for the sprite and focus on making it look decent.

I'll use the following color codes:
- `R` = red (#E74C3C)
- `B` = blue (#3498DB)
- `W` = white (#FFFFFF)
- `K` = black (#2C3E50)
- `Y` = yellow (#F1C40F)
- `S` = skin (#F39C12)
- `D` = dark (#2C3E50)
- `.` = transparent

Hero: "A small adventure" - let me make a character with a red cap, blue overalls, and yellow boots.

HERO_SPRITE (16x22 grid):

```
"................",
"................",
".....RRRRRRR....",
"....RRRRRRRRR...",
"....RRR...RRR...",
"....RRR...RRR...",
"....RRWWWWRRR...",
"....RRWWWWRRR...",
".....RRRRRRR....",
"......RRRRR.....",
".....BBBBBBB....",
"....BBBBBBBBB...",
"....BBBBBBBBB...",
"....BBBBBBBBB...",
".....BBBBBBB....",
".....YBBBBBY....",
".....YBBBBBY....",
"......BBBBB.....",
".....BB...BB....",
".....BB...BB....",
".....BB...BB....",
".....BB...BB....",
```

Hmm, this is not great. Let me simplify to a hero with a clear silhouette.

Actually, you know what, let me just write a good-looking character without relying on a pixel grid. I'll draw a character using fillRect calls in a function. Here's a cleaner approach:

```javascript
function drawHero(ctx, x, y, facing) {
    ctx.save();
    ctx.translate(x + 18, y + 2); // center
    ctx.scale(facing, 1);
    ctx.translate(-18, 0);
    
    // Body (blue)
    ctx.fillStyle = '#4488FF';
    ctx.fillRect(6, 12, 24, 20);
    
    // Head (red cap)
    ctx.fillStyle = '#FF4444';
    ctx.fillRect(4, 4, 28, 14);
    
    // Face (skin)
    ctx.fillStyle = '#FFCC88';
    ctx.fillRect(8, 8, 20, 10);
    
    // Eyes
    ctx.fillStyle = '#222222';
    ctx.fillRect(12, 11, 4, 4);
    ctx.fillRect(20, 11, 4, 4);
    
    // Hat brim
    ctx.fillStyle = '#FF4444';
    ctx.fillRect(2, 16, 32, 3);
    
    // etc.
    
    ctx.restore();
}
```

Actually this is really clean. Let me do it this way. I'll draw the hero with code to create a polished 16-bit style character.

Let me define a nice character:

**Kai the Forest Sprite**:
- Green hat
- Tan face
- Blue tunic
- Brown boots

Or something distinguishable.

Actually, you know what, let me go with a classic but original little character. Let me draw with simple shapes:

Hero:
- Head: rounded, with a red bandana
- Eyes: white with black pupils
- Body: blue vest, white shirt
- Legs: brown pants
- Boots: dark brown

I'll write a `drawHero` function that uses fillRect aggressively to create a pixel-art look.

Let me write the code now. I'll be comprehensive but I need to actually code it.

Alright, let me write the complete game. This will be long. Let me be comprehensive.

I'll write this in one go. Here's the full game code:

For organisation, I'll put:
1. HTML + CSS
2. JS Setup
3. Sprite definitions
4. Level data
5. Game objects and logic
6. Rendering
7. Autoplay
8. Game loop

Let me code this now. I'll be methodical.

Actually, for the level design, rather than defining each platform etc. manually, let me create a level generator that creates a decent platformer level. This will be more maintainable and result in a better level.

Actually no, a manual level will be better for ensuring it's beatable and has good flow. Let me define it manually.

Let me think about the ground structure:

```
Ground segments (x, y, w):
(screen 1: 0 to 960)
(0, 480, 930) then gap (930-1010), then (1010, 480, 950)...

Hmm, let me use clean coordinates. Screen width is 960.
```

Let me just code it. The level data will be defined as arrays of objects. I'll design the level as I write the code.

Actually, I should really start coding now. I've thought about this enough. Here we go:

Let me write the complete HTML file. I'll make it comprehensive and well-crafted. Given the complexity, I'll be thorough.

For the platform physics and collision detection, I'll use axis-aligned bounding box (AABB). For each frame:
1. Move player by vx
2. Check horizontal collisions
3. Move player by vy
4. Check vertical collisions

For the ground, I'll have an array of ground rectangles. For each, check if the player's AABB overlaps.

For moving platforms, I need to update their positions based on time and move the player with them.

For coins/enemies, I'll check AABB overlap.

For the parallax background:
- Sky: gradient from light blue to darker blue
- Clouds: drawn at different positions, scrolling at 0.2x speed
- Hills: drawn at different positions, scrolling at 0.5x speed
- Maybe trees: scrolling at 0.8x speed

Let me define:
```javascript
// Parallax layers
const clouds = [];
for (let i = 0; i < 20; i++) {
    clouds.push({
        x: Math.random() * 2000,
        y: 50 + Math.random() * 150,
        w: 60 + Math.random() * 80,
        h: 20 + Math.random() * 30,
        speed: 0.1 + Math.random() * 0.2,
    });
}

const hills = [];
for (let i = 0; i < 30; i++) {
    hills.push({
        x: i * 300 + Math.random() * 100,
        h: 100 + Math.random() * 100,
        w: 200 + Math.random() * 150,
    });
}
```

Actually, let me simplify the parallax. I'll draw a layer of hills with different x positions based on the camera offset, multiplied by a factor.

For the sky, I'll use a gradient.

OK here we go. Writing the full code now. This is going to be a large HTML file.

I realize there's a lot to write. Let me focus on getting it done.

Let me think about the moving platform behavior. I'll have moving platforms that move back and forth between two points, with a sine or linear motion.

```
{ x: 1700, y: 400, w: 80, h: 16, 
  startX: 1700, startY: 400, endX: 1700, endY: 320,
  speed: 0.5, phase: 0 }
```

And I'll update them:
```javascript
platform.t = (Math.sin(time * speed + phase) + 1) / 2;
platform.x = startX + (endX - startX) * t;
platform.y = startY + (endY - startY) * t;
```

This gives smooth back-and-forth motion.

When the player is standing on a moving platform, the player should move with it. I check if the player's feet are on top of the platform and the player is not jumping, then translate the player by the platform's delta.

OK let me just write it now. I'll be comprehensive but I need to actually code.

Let me use a single HTML file with everything inlined. Here's my final structure:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Pixel Quest — A 16-bit Platformer</title>
<style>
  /* styles */
</style>
</head>
<body>
<canvas id="game" width="960" height="540"></canvas>
<script>
// ===== THE COMPLETE GAME =====
</script>
</body>
</html>
```

Let me carefully write this. I'll make sure:
- The hero looks good
- Controls feel responsive
- Level design is interesting
- Parallax is beautiful
- Autoplay works
- Particles add juice
- UI is clear

Here we go...

I'm going to write this code now. It's going to be long. Let me not stop until it's complete.

One thing: for the hero sprite, I'll define a `drawHero` function that draws a nice character using fillRect calls. Let me design it as follows:

```javascript
function drawHero(ctx, x, y, facing, frame) {
    ctx.save();
    ctx.translate(x + HERO_W/2, y + HERO_H);
    ctx.scale(facing, 1);
    ctx.translate(-(HERO_W/2), -HERO_H);
    
    // Draw from feet up...
    // Boots
    ctx.fillStyle = '#5D3A1A';
    ctx.fillRect(4, HERO_H-10, 10, 10);
    ctx.fillRect(HERO_W-14, HERO_H-10, 10, 10);
    
    // Legs
    ctx.fillStyle = '#5D4E37';
    ctx.fillRect(8, HERO_H-22, 8, 12);
    ctx.fillRect(HERO_W-16, HERO_H-22, 8, 12);
    
    // Body (tunic)
    ctx.fillStyle = '#3A7D44';
    ctx.fillRect(2, HERO_H-42, HERO_W-4, 22);
    
    // Belt
    ctx.fillStyle = '#8B4513';
    ctx.fillRect(2, HERO_H-24, HERO_W-4, 4);
    
    // Head
    ctx.fillStyle = '#F4A460';
    ctx.fillRect(6, HERO_H-58, HERO_W-12, 18);
    
    // Hat
    ctx.fillStyle = '#D4493B';
    ctx.fillRect(4, HERO_H-66, HERO_W-8, 10);
    ctx.fillRect(0, HERO_H-58, HERO_W, 4);
    
    // Eyes
    ctx.fillStyle = '#222';
    ctx.fillRect(10, HERO_H-50, 4, 4);
    ctx.fillRect(HERO_W-14, HERO_H-50, 4, 4);
    
    ctx.restore();
}
```

Where HERO_W=32, HERO_H=48.

Let me make this cleaner with actual pixel art-style drawing.

For the character, I want it to feel 16-bit. Using `ctx.imageSmoothingEnabled = false` and drawing at integer positions helps.

I'll also add an animation frame parameter to the hero drawing for walking cycles. When the player is moving, I'll vary the leg positions.

For simplicity, I might just draw the hero with a few frame variations:
- Standing: legs together
- Walk frame 1: legs apart
- Walk frame 2: legs together
- Jumping: legs tucked

Actually, for a platformer, we can just flip the sprite horizontally and have a small bounce when running. Let me keep it simple.

OK HERE IS THE COMPLETE GAME FILE. I'm writing it now.

Let me think quickly about one important thing: the level layout. Let me design a 7-screen-ish level:

Total width: 5760px (6 screens)
Ground at y=480, player's normal gravity.

I'll define ground segments as:
```
{x: 0, w: 900},
{x: 1000, w: 800},
{x: 1900, w: 500},
{x: 2500, w: 400},
{x: 3000, w: 700},
{x: 3800, w: 600},
{x: 4500, w: 1200}
```

With gaps between them. The last segment is the finale.

Wait, let me design more carefully. I want the player to navigate gaps, jump on enemies, use platforms, and reach the flag.

Here's my level plan:

**Segment 1 (0-960):** Full ground
- Two enemies walking
- A platform with coins above
- Ground at (0, 480, 960, 60)

**Segment 2 (960-1920):** 
- Ground: (960, 480, 350, 60), gap at 1310-1390, ground: (1390, 480, 530, 60)
- A moving platform over the gap
- One enemy on each ground piece
- Coins over the gap

**Segment 3 (1920-2880):**
- Ground: (1920, 480, 300, 60), gap at 2220-2320, ground: (2320, 480, 560, 60)
- Floating platforms: some higher up with coins
- Two enemies

**Segment 4 (2880-3840):**
- Ground: (2880, 480, 400, 60), gap at 3280-3380, ground: (3380, 480, 460, 60)
- Moving platform over gap
- Platforms at different heights with coins
- Enemies: 2-3

**Segment 5 (3840-4800):**
- Ground: (3840, 480, 960, 60) continuous
- But with platforms and enemies
- A small section where the ground goes down? No, let's keep it flat.

**Segment 6 (4800-5760):**
- Ground: (4800, 480, 960, 60) continuous
- More enemies
- The flag at the end
- Some platforms with coins

This gives us 6+ screens. Let me make the last part have the flag around x=5700.

Actually, let me design this more carefully with the moving platforms and floating platforms. Let me write levels data:

```javascript
const level = {
    width: 5760,
    ground: [
        { x: -100, w: 1100 },   // Screen 0 extra
        { x: 1100, w: 300 },     // Screen 1 early
        { x: 1500, w: 400 },     // Screen 1 mid
        { x: 2000, w: 300 },     // Screen 2 early
        { x: 2400, w: 500 },     // Screen 2 late
        { x: 3000, w: 350 },     // Screen 3 early
        { x: 3450, w: 400 },     // Screen 3 late
        { x: 3950, w: 500 },     // Screen 4
        { x: 4550, w: 400 },     // Screen 5
        { x: 5050, w: 700 },     // Final
    ],
    ...
};
```

Hmm, the gaps need to be jumpable. Let me calculate reasonable gap widths.

Gap width = distance from end of one ground segment to start of next.
For "ground: {x: -100, w: 1100}" that's -100 to 1000. Next starts at 1100. Gap = 100px. Good.

Let me not over-plan. I'll write the level data in the code and adjust while coding.

Let me just code it all now. This is my final approach. I'll put everything in place and deliver the complete HTML file.

Now, one more consideration: for movement, the player needs acceleration and friction for nice game feel. Let me include that.

```javascript
player.vx = player.vx * 0.8 + targetSpeed * 0.2;
```

Or use acceleration:
```javascript
const ACCEL = 0.5;
const FRICTION = 0.8;
if (right) player.vx = Math.min(player.vx + ACCEL, MOVE_SPEED);
```

This gives a smooth but responsive feel.

OK, coding now. Let me write it out completely.

Oh wait, I also need to handle the "R to restart" and win screens.

Restart: reset all state to initial.
Win screen: show "LEVEL COMPLETE" and prompt to press R.

Autoplay mode: toggle with P, show a "DEMO" indicator.

Alright, coding the whole thing now. I'm confident in my plan. Let me write it all out in one chunk.

One final thought on the enemy design: They walk back and forth. When the player jumps on them, they get flattened (maybe with a squash animation) and disappear with particles. If they touch the player from the side, the player loses a life or restarts.

For simplicity in a single-level game, let me say:
- If player touches enemy from above and is falling: enemy dies, player bounces
- If player touches enemy from side: player dies (restarts from beginning with all coins reset)

Actually, for score/coin persistence, let me make death reset the player to the start of the level (like a life system).

Let me implement it as:
- On death: reset player to start, reset coins and enemies.
- On win: show win screen.

Actually, let me be gentle: when the player dies, just reset the player to the start of the level (or a checkpoint), not the entire game state. For simplicity, reset everything.

Alright, let me code this! Final answer will be the complete HTML file.

I'll write the JavaScript with these sections:
1. Constants and setup
2. Input
3. Sprite drawing functions
4. Level definition
5. Player object and physics
6. Enemy logic
7. Coin logic
8. Platform logic (static and moving)
9. Particle system
10. Parallax background
11. Camera
12. Collision detection
13. UI rendering
14. Autoplay AI
15. Game loop / update
16. Game state management (start, play, win)

Let me use a clean architecture with a `Game` object or just toplevel functions.

Writing now... ooh boy this is going to be long.