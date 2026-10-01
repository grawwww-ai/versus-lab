Let me build a single self-contained HTML file with a canvas-based pixel art boss fight.

Key requirements:
- Retro 16-bit pixel art, nearest-neighbour scaling (imageSmoothingEnabled = false, CSS image-rendering: pixelated).
- Hero sprite and big animated boss (>= 48x48 pixels) drawn procedurally frame by frame.
- Attack patterns: projectiles, slam, beam.
- Health bars top.
- Hit flashes, screen shake, particles.
- Parallax dungeon background with torches.
- Sprites drawn procedurally in code, frame by frame, with idle, run, attack, hurt animations.
- Autoplay demo ON by default; AI controls player; ends with boss exploding and VICTORY screen.
- P key toggles autoplay.
- No sound needed.
- Everything within first 30 seconds should show important stuff.

Design plan:

Internal resolution: 320x180 (16:9) or 256x224. Let's use 320x180 scaled to fit window with integer scaling. Pixel art at that res... boss 48x48 is quite big relative to 180 height — that's fine, big boss. Actually a 48x48 boss in a 320x180 screen is ~27% of height. Good.

Hmm, but hero sprite needs detail. Let's do internal 320x180. Hero ~ 16x20 pixels. Boss 64x64 maybe. Requirement is at least 48x48. Let's make boss 64x64.

Actually let's use 384x216 for a bit more space. Integer scale 3 => 1152x648. Fine. Let's do 320x180 scale 4 => 1280x720. That's nice. But 48x48 boss in 320x180... boss covers a lot. It's ok, "big boss".

Let's use 320x180.

Sprites drawn procedurally: I'll create a pixel grid helper: draw from string arrays with a palette. That's "drawn procedurally in code, frame by frame". I'll define pixel art via strings for each frame. That's a lot of manual work but gives nice results.

Alternative: draw with rectangles per frame programmatically (limbs, body). More "procedural" and easier to animate with parameters. I could do a hybrid: draw boss with shapes computed per frame (ellipses/rects) but at pixel resolution using a low-res offscreen canvas — which automatically gives pixel art look. Actually drawing on the low-res canvas with fillRect at integer coordinates IS pixel art.

I'll go with procedural drawing functions using rect/ellipse helpers on the low-res canvas, with pixel snapping. That guarantees crispness and is much more flexible for animation.

Let me plan:

**Palette** (16-bit-ish):
- Background dungeon: dark stone #1a1420, #2a2030, #3a2f45
- Torch flame: #ffd23f, #ff8c1a, #ff4d00
- Hero: armor blue #4a7fd4, #2a4a8c, skin #f0c090, cape red #d94a3a
- Boss: dark purple/green demon: body #4a2a5a, #6a3a7a, horns bone #e8e0c8, eyes #ff3f2f

**Screen layout**:
- 320x180. Ground at y=140ish. Boss occupies right side, hero left.
- Arena: floor from y=140 to 180.

Actually let's give more room: floor line y = 148. Boss stands on floor, 64x64 sprite → top at 84. Health bars at top y=4..12.

**Boss**:
- Position: x around 220, y bottom at floor.
- Size 64x64.
- Phases: idle, projectile (fires spread of orbs), slam (jumps and slams, shockwave), beam (charges then fires horizontal beam across floor at some height), hurt, death.
- Boss attack cycle with telegraphs.

**Hero**:
- 16x20-ish. Position x variable, y floor.
- Movement left/right, jump possible? Keep it simple: run left/right + dash. Dodging projectiles by moving. Slam shockwave: jump over? Let's give hero jump (why not) — dodge via jump for shockwaves and moving for projectiles. Beam: beam at mid height, must... hmm. Let's make beam sweep at a height, and the hero can dodge by being far / low. Simpler: beam fires at a horizontal band at chest height; hero must duck? Adding duck/crouch. Or beam is a vertical sweeping column.

Simplify: Beam is aimed at hero's y band. Actually let's do: boss charges a beam, then fires a horizontal beam at a fixed height (y=120, chest height). Hero must be grounded and... hmm, if grounded hero occupies y 128-148. Beam at 120 would miss. Let's instead make beam a floor-level sweep that the hero must jump over. Then slam shockwave also requires jump. Hmm, too similar.

Alternative: beam is a wide vertical/horizontal laser that the hero must avoid by not being in the column — beam tracks hero x, then fires downward column. Hero just runs away from column. That's fine and readable. Let's do: beam locks a vertical column across the whole arena height at hero's x, after telegraph hero can run out of the column. Nice and readable.

And slam: boss jumps to hero's x position, lands, creates shockwave rings on the ground both directions — hero must jump.

Projectiles: boss fires fan of 3-5 orbs that travel; hero dodges by moving/jumping.

Good — three distinct patterns requiring: move, jump, move.

**Autoplay AI**: 
- Compute threats; pick safest action.
- Simple: 
  - If beam telegraph active and hero x within column → run away from column.
  - If shockwave incoming → jump when close.
  - If projectiles near → move to a safe x, or jump if projectile is low.
  - Otherwise approach boss and attack when in range.

Let's design hero attack: sword slash in front. Range ~24px. Damage 1 per hit. Cooldown ~24 frames. Boss HP 100? At ~1 dmg per 24 frames = 2.5 dmg/sec... too slow. Let's do boss HP 60 and hero attack does 3 damage, cooldown 20 frames → 9 dmg/sec → ~7 seconds of pure hitting. With dodging, maybe 15-20 sec fight. Good for 30s window.

Actually we want the whole fight to fit in ~25 sec. Let's tune: boss HP 80, hero hit does 4 dmg, attack cooldown 22 frames (~0.37s) → ~10.8 dmg/s. Fight ~10-15 s of attacking. Good.

Boss also has hurt flash on hit and brief stun.

**Death**: boss explosion with lots of particles, screen shake, then VICTORY screen with text. Then maybe restart after some seconds (loop). Requirement says may loop or continue after that. I'll loop: after victory, wait ~4s, restart. And continue cycling so recording shows.

Hmm, but if it loops, the demo will show repeated fights. Fine.

**Rendering & scaling**: canvas at 320x180 with CSS scaled up. Use a wrapper that computes integer scale on resize, sets canvas style width/height, image-rendering: pixelated. Actually simpler: canvas width=320 height=180, CSS width = 320*scale px. Set via JS on resize.

Let's do dynamic integer scale.

**Screen shake**: offset the whole canvas draw by integer pixels (floor of shake amount), and draw background slightly larger or just accept edges. I'll fill background beyond edges — draw background covering 320+shake range. Simplest: translate by shake and draw bg from -8 to 328.

**Parallax background**: 
- Layer 1 (far): dark wall with arches, offset 0.2.
- Layer 2 (mid): columns/pillars with torches, offset 0.5.
- Layer 3 (near floor): offset 1.0.

Camera: mostly static since arena is one screen. Hmm, parallax needs camera movement to be visible. I'll add a slow automatic camera sway (sinusoidal) so parallax shows, plus screen shake. Camera x oscillates ±6 px. That gives visible parallax. Good.

Actually camera sway might be disorienting. Small amplitude ±5px, slow. It's fine and shows off parallax. Also camera follows hero slightly? Let's do camera = (hero.x - center)*0.15 clamped, plus subtle sway. That gives parallax with gameplay meaning.

Let's keep it: camX = clamp(hero.x*0.35 - 40, -20, 20) + sin(t)*3.

Hmm, simpler: camX = (hero.x - 160) * 0.12. Small parallax. Plus sway.

Fine.

**Torches**: on pillars, animated flame (procedural flicker with noise), light glow.

**Particles**: hit sparks, blood/energy, dust on landing, explosion.

**Hit flash**: when enemy hit, draw white silhouette overlay for a few frames. Implement: draw sprite, then draw again with all-white using globalCompositeOperation? Easier: draw the sprite function with a "flash" parameter that replaces palette colors with white.

I'll make drawing functions take a flash boolean, and each color goes through `col(c)` which returns '#fff' if flash.

For the boss, drawing with shapes — I'll pass flash to a color helper.

**Animation frames**: hero states: idle (2-3 frames bob), run (4 frames), attack (3 frames), hurt (1-2 frames), jump, duck. Boss: idle (2), cast/throw, slam windup/jump/land, beam charge/fire, hurt, death.

I'll drive animation with a frame counter and state timers.

Let me write the code.

Structure:

```js
const W=320, H=180;
const canvas, ctx;
ctx.imageSmoothingEnabled=false;

// palette helpers
function px(x,y,w,h,c){ctx.fillStyle=c;ctx.fillRect(x|0,y|0,w,h);}
```

Actually for pixel-perfect, ensure integer coords.

Let me define drawing at integer positions.

**Hero sprite drawing** (procedural, ~14x20):

Hero: knight with helmet, blue armor, red cape, sword.

Let me write function drawHero(x, y, state, frame, facing, flash) where (x,y) is bottom-center.

Body parts sizes:
- Head: 6x6 at top
- Torso: 8x8
- Legs: 4x6 each
- Arms

Let me lay out with hero height 20, width ~12.

Coordinates relative to bottom-center (x, y):
- legs: y-6..y
- torso: y-14..y-6
- head: y-20..y-14

Draw:

```
// legs
legOffset = run cycle
px(x-4, y-6, 3, 6, armorDark)
px(x+1, y-6, 3, 6, armorDark)
```
With run animation, legs swing: front leg forward, back leg back.

Let me do it more carefully with a helper that draws rectangles in local pixel coords where origin is bottom-left of the sprite bounding box.

I'll define hero draw with local coords: hx = x - 6 (left), hy = y - 20 (top). Then draw rects at hx+dx, hy+dy.

Hero pixels (14 wide, 20 tall):
- Head/helmet: helmet plume? Let's do: helmet at dx 3..10, dy 0..5. color steel #b8b8cc, visor dark #2a2a3a, eyes glow cyan.
- Torso: dx 3..10, dy 6..13 armor blue.
- Belt: dy 13..14.
- Legs: dx 3..5 and dx 8..10, dy 14..20.
- Arms: dx 1..3 and 10..12.
- Cape: behind, dx 0..2? red.

Sword: in attack, drawn in front.

OK, let me just write it with reasonable detail. I'll write helper `r(dx,dy,w,h,c)` inside a closure.

Let me write actual code.

```js
function drawHero(g, x, y, st){
  // x,y = bottom-center in world px (already camera-adjusted), st = {state, t, facing, flash}
  const fx = st.facing; // 1 or -1
  const c = (col)=> st.flash ? '#ffffff' : col;
  // helper that mirrors
  const R = (dx,dy,w,h,col)=>{
    let X = fx>0 ? dx : -dx-w;
    g.fillStyle = c(col);
    g.fillRect(Math.round(x+X), Math.round(y-20+dy), w, h);
  };
  ...
}
```

Hmm, mirroring: define local coords with x=0 at hero center-left... Let's define the sprite space as 16 wide: dx from 0..15 with center at 8. Then mirror: X = fx>0 ? dx-8 : 8-dx-... let's do: localX = dx - 8; mirrored localX = fx>0 ? localX : -localX - 1 (for pixel widths). Actually with widths: if facing left, rect at [dx, dx+w) maps to [-dx-w, -dx). Good.

So:
```js
const RX = (dx,w,fx) => fx>0 ? (dx-8) : (-(dx+w)+8);
```
Wait: local dx-8 for left edge; for mirrored, we want left edge = -( (dx+w) - 8 ) = 8-dx-w. Yes.

So `R(dx,dy,w,h,col)` uses `X = fx>0 ? dx-8 : 8-dx-w` then `g.fillRect(x+X, y-20+dy, w,h)`.

Good.

Now let's design hero pixel layout (16 wide, 20 tall, dy 0 at top):

- dy0-1: helmet top: dx5..11, w6 h2 color steel light
- dy2-5: helmet: dx4..12 (w8) steel; visor dx5..11 dy3..4 dark; eye glow dx6..7 and dx9..10? Simplify: visor dark band with two cyan eyes.
- dy6: neck/shoulder
- torso dy6..13: dx4..12 w8 armor blue; chest emblem dy8..10 dx7..9 gold.
- belt dy13: dx4..12 w8 dark.
- legs dy14..20: dx4..7 w4 dark blue; dx9..12 w4.
- arms: dx2..4 w2 at dy7..12; dx12..14 w2.

Cape: dx3..13 dy6..15 behind — draw first in red.

Hmm the sprite is 16x20 = 320 pixels. Fine.

Run animation: legs alternate — front leg forward, back leg back, with slight y offsets. Torso bob ±1.

Attack animation: sword arc. Sword drawn as a rotated-ish set of rects: for frames 0,1,2 — windup (sword up behind), slash (sword forward horizontal), follow-through (sword down). I'll draw sword as 2px thick line of length ~14 with pixel steps.

Let me write drawSword(x,y,angle-ish) manually per frame.

Frame 0 (windup): sword vertical above head, hilt at hand.
Frame 1 (slash): sword horizontal forward, length 16.
Frame 2 (recover): sword diagonal down-forward.

OK.

**Boss drawing** (64x64):

A demon: big body, horns, glowing eyes, arms, wings? Let's do: 
- Head with horns at top (dy 4..24)
- Eyes glowing red
- Torso dy 24..48
- Two arms with claws
- Legs / tail at bottom

Boss local space 64x64, origin bottom-center (x, y).

Colors: body #5a2f6e, dark #3a1b4a, light #7a4a92, bone #e0d8b8, eye #ff3a2a, glow #ff8a3a.

Let me draw:

- Legs: dx 18..28 and dx 36..46, dy 48..64.
- Torso: dx 16..48, dy 22..50 (w32 h28).
- Shoulders: dx 8..24 dy 22..34; dx 40..56 dy 22..34.
- Arms: dx 4..14 dy 30..52; dx 50..60 dy 30..52.
- Claws at ends.
- Neck: dx 26..38 dy 16..24.
- Head: dx 20..44 dy 4..24 (w24 h20).
- Horns: from head corners going up-out.
- Eyes: glowing red rects at dy 12..15, dx 25..29 and dx 35..39.
- Mouth: dark with teeth.
- Belly lighter.

Animation: idle breathing (whole body y offset ±1, torso width ±1), arm bob. Cast: arms raise, glow orb between hands. Slam: jumps up, then slams down with arms overhead → down. Beam: mouth opens, charge glow, then beam.

I'll parametrize with `st` state and `t`.

This is getting long but let's write it.

**Boss attack state machine**:

States: 'idle' (approach/regroup), 'proj', 'slam', 'beam', 'hurt', 'dead'.

Boss position: x fixed around 230? Boss can move a bit. Let's keep boss mostly stationary at x=240, but slam involves jumping to hero's x and back? That's complex with a big sprite. Let's have boss stay at x ~ 235 and slams create shockwaves. Simpler and still fun.

Actually for the "slam" pattern: boss rears up and slams the ground, creating two shockwave projectiles that travel along the ground in both directions. Hero must jump over them. Good.

Beam: boss charges, then fires a vertical column downward at hero's x (locked at telegraph start... or tracking). Let's lock at fire time based on hero x, with a telegraph line showing during charge. Hero runs out of the column.

Projectiles: boss raises arms, fires 3 orbs in a fan toward the hero's position; orbs travel with slight arc. Hero dodges by moving/jumping.

**Damage/HP**:
- Boss HP 80.
- Hero HP 10, but hero takes damage on contact with projectiles/shockwave/beam.
- If hero dies? Autoplay should avoid that, but add hero death → respawn/restart. Let's make hero HP 12 and give damage 2. If hero dies, restart the fight (reset) with a brief "DEFEAT" flash? Eh. Better: keep hero alive mostly; if dies, reset fight. I'll implement a reset.

Actually, to guarantee a good demo, I'll make the AI competent and hero HP generous (20). And on hero death, just reset the whole fight after 2s.

**Hit flash**: when boss is hit, set boss.flash = 6 frames. Same for hero.

**Screen shake**: shakeAmt decays; offset = random(-shakeAmt, shakeAmt) rounded.

**Particles**: array of {x,y,vx,vy,life,maxLife,color,size,gravity}.

**Health bars**: top-left hero bar (blue/green), top-right boss bar (red/purple) with pixel border. Show labels.

**VICTORY screen**: big pixel text drawn with rects, or just use ctx.font? The requirement is no external fonts, but canvas default fonts are fine? "no external resources, CDNs, fonts or images" — system fonts are OK but to be safe and keep pixel aesthetic, I'll draw text with a procedural pixel font (5x7 bitmap font). That's a chunk of work but doable and safe. Let me implement a small pixel font for A-Z, 0-9, and a few symbols.

Actually simpler: use ctx.font with monospace and small size on the low-res canvas — it'd look blurry/odd at 320x180. With imageSmoothingEnabled false, text rendering at 320x180 is still anti-aliased. Hmm. Pixel font is better. Let's do a 5x7 font encoded as strings.

I'll write a compact font map. Let me define characters needed: A-Z, 0-9, space, '!', ':', '-', '.', '%'. For "VICTORY", "DEMO", "BOSS", "HERO", "AUTOPLAY: ON/OFF (P)".

Let me write the font as an object of 7 strings of 5 chars each using '1'/'0'.

That's 26 letters × 7 rows. Let's write them.

A:
01110
10001
10001
11111
10001
10001
10001

B:
11110
10001
10001
11110
10001
10001
11110

C:
01110
10001
10000
10000
10000
10001
01110

D:
11110
10001
10001
10001
10001
10001
11110

E:
11111
10000
10000
11110
10000
10000
11111

F:
11111
10000
10000
11110
10000
10000
10000

G:
01110
10001
10000
10111
10001
10001
01111

H:
10001
10001
10001
11111
10001
10001
10001

I:
11111
00100
00100
00100
00100
00100
11111

J:
00111
00010
00010
00010
00010
10010
01100

K:
10001
10010
10100
11000
10100
10010
10001

L:
10000
10000
10000
10000
10000
10000
11111

M:
10001
11011
10101
10101
10001
10001
10001

N:
10001
11001
10101
10011
10001
10001
10001

O:
01110
10001
10001
10001
10001
10001
01110

P:
11110
10001
10001
11110
10000
10000
10000

Q:
01110
10001
10001
10001
10101
10010
01101

R:
11110
10001
10001
11110
10100
10010
10001

S:
01111
10000
10000
01110
00001
00001
11110

T:
11111
00100
00100
00100
00100
00100
00100

U:
10001
10001
10001
10001
10001
10001
01110

V:
10001
10001
10001
10001
10001
01010
00100

W:
10001
10001
10001
10101
10101
11011
10001

X:
10001
10001
01010
00100
01010
10001
10001

Y:
10001
10001
01010
00100
00100
00100
00100

Z:
11111
00001
00010
00100
01000
10000
11111

0:
01110
10001
10011
10101
11001
10001
01110

1:
00100
01100
00100
00100
00100
00100
01110

2:
01110
10001
00001
00110
01000
10000
11111

3:
11111
00010
00100
00010
00001
10001
01110

4:
00010
00110
01010
10010
11111
00010
00010

5:
11111
10000
11110
00001
00001
10001
01110

6:
00110
01000
10000
11110
10001
10001
01110

7:
11111
00001
00010
00100
01000
01000
01000

8:
01110
10001
10001
01110
10001
10001
01110

9:
01110
10001
10001
01111
00001
00010
01100

space: all zeros
!: 
00100
00100
00100
00100
00100
00000
00100

:
00000
00100
00100
00000
00100
00100
00000
Hmm for colon: rows: 
00000
00100
00100
00000
00100
00100
00000 — that's more like a colon with 2 dots. Fine.

-:
00000
00000
00000
11111
00000
00000
00000

.:
00000
00000
00000
00000
00000
00000
00100

/:
00001
00010
00010
00100
01000
01000
10000

%: skip.

OK.

drawText(str, x, y, color, scale=1).

**Now the AI.**

Let me think about the AI logic in detail.

Hero state: x, y (y is bottom), vy, onGround, hp, facing, action ('idle','run','jump','attack','hurt'), cooldown.

AI each frame:
1. Determine danger:
   - Beam telegraph: `boss.beamX` set, warning active. If |hero.x - beamX| < 14 (beam half width ~ 12), run away from beamX.
   - Shockwaves: array of ground waves with x, dir, speed, width. If one is within 50px and approaching → jump (if onGround). Predict: time to reach = (hero.x - wave.x)/speed; jump when time < ~0.35s (21 frames).
   - Projectiles: orbs with pos/vel. If an orb will be within 20 px in next ~15 frames → move away vertically? We can't move vertically except jump. So: if orb is at height near hero's head, dodge horizontally; if orb is low and near, jump.
   
   Simplify: compute a "danger score" for a set of candidate actions and pick the best? That may be overkill. Let's do a simpler priority list, which is what most of these do:

   - If beam warning and in column → run away from column (and it will work since beam locks).
   - Else if incoming shockwave close → jump.
   - Else if incoming projectile within 40px horizontally and roughly at hero's y → jump if low else move away.
   - Else if boss in an attack windup (proj/slam/beam), keep distance ~ maintain 50-70px from boss.
   - Else approach boss and attack when within range (|hero.x - boss.x| < 34).

2. Attack: if within range and cooldown ready → start attack.

Attack: hero swings; hitbox in front for a few frames; damage boss.

Let's define boss hitbox: x from boss.x-28 to boss.x+28 (boss 64 wide → ±32). Hero attack range 30 from hero center. So hero needs |dx| < 30+28 = 58... that's basically touching. Boss is huge so hero should stand at boss edge. Boss.x ≈ 240, boss half width 32 → left edge at 208. Hero at x=190 with range 30 → hits at 220. OK so hero must be around x 175-205 to hit. Fine.

Hero should stay at ~185-200 to attack, and retreat to ~150 to dodge. Arena is 320 wide, boss at 240, so hero has room from 20 to 210.

Let's set boss.x = 245.

Hero spawn x = 70.

**Fight pacing / timeline**:
- t=0: intro, boss idle, hero runs toward boss.
- Boss attacks every ~2.2s with a random pattern (cycling proj → slam → beam).
- Hero attacks between dodges.

Let's estimate: hero does 4 damage per hit, 30 frames cooldown = 0.5s. In 20s, if half the time attacking → 20 hits → 80 damage. Good with boss HP 80.

Let's set boss HP = 90 and hero damage 4. Fine-tune: damage 5, HP 100.

Hmm, let's do boss HP 100, hero dmg 6, cooldown 26 frames → ~13.8 dmg/s if constantly attacking. Realistically ~50% uptime → 7/s → 14s. Good.

Actually let's make the fight a bit more dynamic: boss HP 100, hero dmg 5, cooldown 24 frames (~0.4s) → 12.5/s. Fine.

**Victory**: when boss HP <= 0 → boss state 'dead', explosion sequence ~2.5s with many particles and shake, then VICTORY text appears, then after 4s reset.

**Timeline for first 30 seconds**: 
- 0-2s: intro, hero runs in
- 2s: boss first attack (projectiles)
- 5s: slam
- 8s: beam
- ... cycle
- ~18-22s: boss dies, explosion
- ~24s: VICTORY
- ~28s: reset, loop

Good, everything within 30s.

Let me make the boss attack cycle faster: interval ~2.5s including windup.

Let's define boss attack timings:
- PROJ: windup 30 frames, fire, recover 40 → total ~80 frames (1.33s) + idle 40 = 2s
- SLAM: windup 25, jump 20, land, shockwaves travel 90 frames, recover 30 → ~165 frames (2.75s). Hmm long. Shockwave travel: from boss.x=245 to x=0 at speed 2.5 px/frame → 98 frames. That's long. Speed 3.5 → 70 frames.

OK.

- BEAM: charge 45, fire 30, recover 30 → 105 frames (1.75s).

Let's just use a state machine with timers and let it be.

**Implementation details**:

Game loop with requestAnimationFrame, fixed timestep 60fps accumulator.

Let me write the code now.

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>BOSS FIGHT</title>
<style>
  html,body{margin:0;padding:0;background:#0a0810;height:100%;overflow:hidden;}
  #wrap{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;}
  canvas{image-rendering:pixelated;image-rendering:crisp-edges;display:block;}
</style>
</head>
<body>
<div id="wrap"><canvas id="c" width="320" height="180"></canvas></div>
<script>
...
</script>
</body>
</html>
```

Resize handler: compute scale = max(1, floor(min(innerW/320, innerH/180))). Set canvas.style.width = 320*scale+'px', height=180*scale+'px'.

Now the JS.

```js
const W=320,H=180;
const cv=document.getElementById('c');
const ctx=cv.getContext('2d');
ctx.imageSmoothingEnabled=false;

function resize(){
  const s=Math.max(1,Math.min(Math.floor(innerWidth/W), Math.floor(innerHeight/H)));
  cv.style.width=(W*s)+'px';
  cv.style.height=(H*s)+'px';
}
addEventListener('resize',resize);resize();
```

Utility:
```js
const rnd=(a,b)=>a+Math.random()*(b-a);
const clamp=(v,a,b)=>v<a?a:v>b?b:v;
```

Pixel font...

```js
const FONT={...};
function textW(s,sc=1){return s.length*6*sc - sc;}
function drawText(g,s,x,y,col,sc=1){
  g.fillStyle=col;
  let cx=x;
  for(const ch of s.toUpperCase()){
    const gl=FONT[ch];
    if(gl){
      for(let r=0;r<7;r++){
        const row=gl[r];
        for(let c2=0;c2<5;c2++){
          if(row[c2]==='1') g.fillRect(cx+c2*sc, y+r*sc, sc, sc);
        }
      }
    }
    cx+=6*sc;
  }
}
```

Now game state.

```js
const FLOOR=148; // ground y (hero feet)
```

Wait, the hero is 20 tall, so at y=148 the head is at 128. Boss 64 tall at FLOOR → head at 84. OK.

Let's set FLOOR = 150 so there's a bit of floor in front.

Arena: 320x180. Ground area from y=150 to 180 (30px of floor). Good.

World coordinates: the arena is the screen. Camera moves ±~10.

Let me define camera:
```js
cam.x = (hero.x-160)*0.15 + Math.sin(t*0.01)*4;
```
Hmm, that changes with hero. Fine.

Actually camera should shift everything including gameplay objects. Let's just apply camX as a translate for the whole scene render (except HUD). Objects' world coords are then in "arena space". The arena is 320 wide but with camera we can show a bit more or less. Since camera range is small (±15), we need the background drawn beyond edges. I'll draw background from -32 to W+32.

Hmm, but gameplay objects near edges could be cut off. Keep camera small: ±10.

Let's simply do: camX = clamp((hero.x - 160)*0.10, -12, 12) + Math.sin(time*0.0008)*3.

OK.

**Game object**:

```js
const game = {
  t:0, shake:0, flashScreen:0,
  hero: {...},
  boss: {...},
  orbs: [], waves: [], particles: [],
  beam: {active:false, x:0, charge:0, warn:false, t:0},
  state:'fight', // 'fight','death','victory'
  stateT:0,
};
```

Hero:
```js
hero = {
  x:70, y:FLOOR, vy:0, onGround:true,
  hp:20, maxHp:20,
  facing:1, state:'idle', anim:0, flash:0,
  atkCd:0, atkTimer:0, hurtTimer:0, invuln:0, dead:false,
  vx:0
};
```

Hero movement: run speed 1.6 px/frame. Jump vy = -4.2, gravity 0.24.

Let's check jump height: v²/(2g) = 17.6/0.48 = 36.7 px. That's plenty to clear shockwaves (which are ~14 tall). Good. Air time: 2*4.2/0.24 = 35 frames. Bit long but fine. Let's use vy=-3.8, g=0.3 → height 24, airtime 25 frames. Good.

Hero attack: atkTimer counts from 0; hitbox active frames 4..10; cooldown 24.

Actually let's define atkTimer as countdown from ATK_DUR=18 frames. Hit frame at timer==12 (i.e., 6 frames in).

Simplify: hero.atk = {active:false, t:0}. When triggered, t = 0, state 'attack'. Each frame t++. Hit check when t===6 and once (flag hitDone).

**Boss**:
```js
boss = {
  x:245, y:FLOOR, hp:100, maxHp:100,
  state:'idle', t:0, flash:0, facing:-1,
  anim:0, phase:0, dead:false,
  beamX:0, beamWarn:0, beamFire:0,
  attackIndex:0, nextAtk: 90,
};
```

Boss states: 'idle', 'proj', 'slam_up', 'slam_down', 'beam', 'hurt', 'dead'.

Let me handle with a single timer `t` and per-state logic.

- 'idle': t++; if t > idleDuration → choose next attack (cycle proj, slam, beam) → set state.
- 'proj': t 0..29 windup (arms raise, orb charging). At t==30 fire 3 orbs. t 30..70 recover. At t==70 → idle, t=0, idleDur=45.
- 'slam': t 0..24 windup (rise). t 25..44 jump up (visual y offset). At t==45 slam down → spawn 2 waves, shake 8, particles. t 45..100 recover. → idle.
   Actually let's make boss visual y offset during jump.
- 'beam': t 0..44 charging (lock beamX at t==40? Actually lock continuously tracking until t=40, then lock). t 40..44 warn flash. t 45..75 firing (beam active). t 75..105 recover → idle.

Hmm, beam needs a clear telegraph. Let's do: charge 0..50, during 0..40 the beam x tracks hero x slowly, at t=40 lock. Then t 50..80 → fire beam (column). Then recover to 110.

Hero must move out of the column between t=40 and t=50 — only 10 frames. Too short. Let's lock at t=30 and fire at t=60: 30 frames (0.5s) to escape. Column half-width 10, hero speed 1.6 → 30 frames = 48px. Enough.

OK:
- beam charge t=0..30: beamX tracks hero.
- t=30: lock, warning indicator flashes.
- t=60: fire, beam active for 35 frames (t 60..95).
- t=95..120 recover.

Total 120 frames = 2s. OK.

**Orbs** (projectiles): {x,y,vx,vy,r,life}. Fired from boss mouth/hands toward hero. Fan of 3 with different angles.

Orb speed ~2.2 px/frame. Aimed at hero position at fire time, with spread ±20°.

Orb radius 4 → hitbox.

**Waves** (shockwaves): {x, dir, speed, life, w:10, h:14}. Move along ground, both directions from boss. Hero must jump.

Actually if wave goes left from boss at x=245, it travels to hero. Hero jumps over it. But there are also waves going right (off-screen quickly). Fine.

Wave speed 3.0 → from 245 to 190 takes 18 frames. Hero needs to jump ~10 frames before. OK.

**Collision**: hero hitbox: x±5, y-18..y (approx). Use rect x-5..x+5, y-18..y.

Orb hits if distance from orb center to hero rect < r.

Wave hits if wave rect overlaps hero rect and hero.y (feet) >= FLOOR-4 (i.e., not jumping high). Actually wave height 14 from floor: from y=FLOOR-14 to FLOOR. Hero feet at y. If hero.y < FLOOR-14 → safe (jumped above). Let's just use rect overlap: wave rect = (x-w/2, FLOOR-14, w, 14); hero rect = (x-5, hero.y-18, 10, 18). Overlap check.

Beam: if beam active and |hero.x - beamX| < 11 and hero.y > 100 (anywhere on ground) → hit. Since beam is a column from top to bottom, it always hits if in column.

Damage: 2 per hit, with 60-frame invulnerability after hit.

Hero HP 20 → 10 hits. Good.

**Boss damage from hero**: boss.hp -= 5 on each sword hit; boss.flash = 8; small particles; screen shake 3; if hp<=0 → state 'dead'.

Boss 'dead' state: explosion sequence:
- t 0..150: spawn particles continuously, shake, flashes.
- At t==150: victory state, show VICTORY.
- At t==330: reset game.

Actually let's make death 90 frames (1.5s) of explosions, then victory screen with text and stats, then after ~180 frames reset.

Hmm, but we want the fight to loop nicely. Reset after 4s.

**Boss hurt stun**: brief flash but boss continues. Fine.

**Rendering order**:
1. Clear.
2. Save, translate(-camX, 0) with shake.
3. Background (parallax layers, drawn in screen space with camera offsets).
4. Torches.
5. Floor.
6. Boss, hero, projectiles, particles.
7. Restore.
8. HUD (health bars, text).

Background parallax: I'll draw each layer with its own camera multiplier.

Layer 0 (far wall): offset = camX*0.2. Draw repeating arches.
Layer 1 (columns + torches): offset = camX*0.5.
Layer 2 (floor): offset = camX*1.0.

Since camX is small (±12), offsets are tiny. To make parallax visible, I could amplify: use camX*1 for far, camX*2 for mid... no, that inverts. Standard: near moves more than far. Far = camX*0.2, mid = camX*0.55, near = camX*1.

With camX up to 12, difference between layers is up to ~7px. Visible enough given the slow sway.

Let's also add a subtle vertical bob? No.

Let's amplify camera movement: camX = clamp((hero.x-160)*0.22, -30, 30) + sin*6. Now range ±36. Layer offsets differ by up to 20px. Good, visible parallax. But then the arena edges need background drawn wide: draw from -60 to W+60. And gameplay objects might go off-screen when camera moves... with camera ±36 the visible world region shifts. Boss at 245 with camera +36 → screen x = 209. Hero at 70 with camera -30 → screen 100. Fine. Arena is 320 wide; when camera is -30, world x from 30 to 350 visible. Hmm, hero can go to x=20 → screen -10 (off). Let's clamp hero x to [40, 215]. Then camera range is clamp((40..215 -160)*0.22) = clamp(-26.4, 12.1). OK.

Actually camera should follow hero a bit but not too much since the arena is small. Let's use 0.18 factor and clamp ±20. Plus sway ±4.

Fine.

Let me now write drawing functions.

### Background

```js
function drawBackground(g, cam){
  // sky/dark
  g.fillStyle='#0d0a14'; g.fillRect(-80,0,W+160,H);
  
  // far wall
  const o0 = cam*0.18;
  g.fillStyle='#171226';
  g.fillRect(-80,0,W+160,150);  // wall
  // arches
  ...
}
```

Let's design:
- Wall region y 0..150.
- Far layer: repeating arch shapes (dark). Arch period 64px. Draw arch as a rectangle with a rounded top (approximate with rects).
- Bricks pattern: horizontal lines every 12px, offset.

Let me implement:

```js
// far bricks
for(let y=0;y<150;y+=10){
  for(let x=-80;x<W+80;x+=20){
    const bx = x + ((y/10)%2)*10 + o0;
    ...
  }
}
```
Hmm, drawing each brick individually = many rects but at 320x180 it's fine.

Simpler: draw wall color, then draw brick lines (darker) horizontally every 10px, and vertical seams staggered.

```js
g.fillStyle='#191329'; g.fillRect(-80,0,W+160,155);
g.fillStyle='#120e1f';
for(let y=8;y<150;y+=12){ g.fillRect(-80,y,W+160,2); }
// vertical seams
for(let y=8;y<150;y+=12){
  const off = ((y/12)|0)%2 ? 0 : 15;
  for(let x=-80+off; x<W+80; x+=30){
    g.fillRect(Math.round(x - o0), y, 2, 12);
  }
}
```
Hmm the offset should be applied so the seam pattern moves with parallax. `x - o0` where x is world position. But then the loop range needs care. Just use `x` from -100 to W+100 and subtract o0. Since o0 max ~4, fine.

Wait, o0 = cam*0.18, cam ≤ 20 → o0 ≤ 3.6. Tiny. The parallax difference between layers: layer0 0.18*20=3.6, layer1 0.55*20=11, layer2 1.0*20=20. So near layer moves 20px, far 3.6. That's decent.

OK good.

- Mid layer: columns/pillars. Period 80px. Each pillar 20 wide, from y=20 to 150. Plus a torch bracket and flame.
- Also add an arch shape behind.

Let me draw pillars at world x positions: 40, 120, 200, 280 (and beyond). With offset o1 = cam*0.55.

Torches on pillars at y=70. Flame animated.

Torch glow: radial gradient? On pixel art, use a few concentric translucent rects/circles. Let's use ctx.globalAlpha with circles. Hmm, canvas arcs will be anti-aliased. With imageSmoothingEnabled false, arcs still antialias. But we're drawing at low-res then upscaling — anti-aliased pixel at low-res becomes a big blocky pixel. That's fine actually, it'll look like a soft glow. Acceptable.

Actually to keep the crisp pixel look, I'll avoid arcs and just draw a few rects with alpha. Or draw glow as a diamond of a few squares with globalAlpha.

Let me do: for torch glow, draw 3 squares centered on the flame with decreasing alpha: 
- alpha 0.10, size 40
- alpha 0.12, size 26
- alpha 0.15, size 14
Using fillRect with integer coords. It'll look like a blocky glow. Good enough.

Flame: draw with 3 layers: outer orange, mid yellow, inner white, with per-frame random-ish flicker using deterministic noise based on time.

```js
function drawTorch(g,x,y,t){
  // bracket
  g.fillStyle='#3a3040'; g.fillRect(x-1,y,3,10);
  // flame
  const f = Math.sin(t*0.7+x)*0.5+Math.sin(t*1.3+x*2)*0.5;
  ...
}
```

Let's do flame of height 10 with wobble.

Colors: outer #ff6a1a, mid #ffb020, core #ffe87a.

Now the floor: y 150..180. Stone tiles.

```js
g.fillStyle='#2a2033'; g.fillRect(-80,150,W+160,30);
// tile lines
g.fillStyle='#1e1726';
for(let x=-80;x<W+80;x+=32) g.fillRect(x-o2, 150, 2, 30);
g.fillRect(-80,150,W+160,2);
```
Plus some highlights.

Also add a darker foreground vignette? Skip.

### Boss drawing

Let's write `drawBoss(g, x, y, st)` where st has {state, t, flash, dead}.

Local coords: sprite is 64 wide, 64 tall, anchor bottom-center.

Helper:
```js
const BX = dx => x - 32 + dx;  // facing is always left (-1) so no mirror
const BY = dy => y - 64 + dy;
function b(dx,dy,w,h,col){ g.fillStyle=flash?'#ffffff':col; g.fillRect(x-32+dx, y-64+dy, w, h); }
```

Wait, boss faces left (toward hero) always. Boss is on the right side. Yes, facing=-1, so the sprite should be drawn facing left. I'll design the sprite facing left natively (asymmetric bits like horns).

Actually let's keep it symmetric-ish so it doesn't matter much.

Boss parts (in 64x64 grid, dy from top):

Let me sketch:

```
        horns
      ___head___
     /          \
    |  eyes eyes |
     \___mouth__/
        neck
   shoulders|torso|shoulders
    arms          arms
      legs      legs
```

Coordinates:
- Head: dx 20..44 (w24), dy 8..30 (h22). Color body mid #6a3a86.
- Head top spikes: dx 22..26 dy 4..8; dx 30..34 dy 2..8; dx 38..42 dy 4..8.
- Horns: left horn from dx 14..22 dy 0..12, curving; right horn dx 42..50 dy 0..12.
- Eyes: dx 24..30 dy 16..20 (w6 h4) glowing; dx 36..42 dy 16..20. Color #ff3a1a, with brighter core.
- Mouth: dx 26..40 dy 24..28 dark, with teeth.
- Neck: dx 27..37 dy 30..36.
- Torso: dx 16..48 dy 32..56 (w32 h24).
- Chest plate: dx 22..42 dy 36..48 lighter.
- Shoulder pads: dx 8..22 dy 30..42; dx 42..56 dy 30..42.
- Arms: dx 6..18 dy 40..58; dx 46..58 dy 40..58.
- Claws: dx 4..16 dy 54..60.
- Legs: dx 18..30 dy 56..64; dx 34..46 dy 56..64.

Hmm, 64 tall total with dy 0..64. Let's make sure it looks like a demon. I'll add a tail maybe. Keep it simple.

Animation:
- idle: body bob dy offset = sin(t*0.08)*1; arms slight sway; eyes pulse.
- proj: arms raised (move arms up by 8), orb glowing between hands.
- slam: boss rises (whole sprite y -= jump), arms up during jump; on land, arms down + shake.
- beam: mouth opens wide, glow in mouth growing, then beam.
- hurt: flash white + slight offset.

I'll implement state-based offsets.

Let me write it with a `bob` variable and `armY` variable.

```js
function drawBoss(g, x, y, st){
  const flash = st.flash>0 && (st.flash%4<2);
  const white = flash;
  const C = c => white ? '#ffffff' : c;
  const bob = st.bob|0;
  const b=(dx,dy,w,h,col)=>{ g.fillStyle=C(col); g.fillRect(Math.round(x-32+dx), Math.round(y-64+dy+bob), w,h); };
  ...
}
```

Since boss is a big sprite, I'll write the parts.

Let me be pragmatic and write it out.

```js
// legs
b(16,52,14,12,'#3c1f52');   // left leg
b(34,52,14,12,'#3c1f52');
b(16,58,14,6,'#2a1440');
b(34,58,14,6,'#2a1440');
// feet
b(14,62,16,3,'#1e0e2e');
b(34,62,16,3,'#1e0e2e');
```

Hmm feet at dy 62..65 exceeds 64. Let's set legs dy 50..62 and feet dy 60..64.

Let me restructure the layout to fit 64:

- dy 0..14: horns/spikes
- dy 6..30: head
- dy 28..34: neck
- dy 32..52: torso
- dy 30..46: shoulders
- dy 42..60: arms
- dy 52..64: legs

Total 64. Good.

Detailed:

```
// Horns (bone)
b(12,4,8,10,'#c9c0a0'); b(10,2,6,8,'#e0d8b8');
b(44,4,8,10,'#c9c0a0'); b(48,2,6,8,'#e0d8b8');
// head spikes
b(22,2,4,6,'#c9c0a0'); b(30,0,4,8,'#e0d8b8'); b(38,2,4,6,'#c9c0a0');
```

Hmm, that overlaps horns and head spikes oddly. Let's simplify: 3 spikes on top of the head plus 2 side horns.

Head: dy 8..30, dx 20..44.

```
b(20,8,24,22,'#6a3a86');       // head base
b(20,8,24,6,'#7d4a9c');        // top highlight
b(18,14,4,12,'#5a2f74');       // left cheek
b(42,14,4,12,'#5a2f74');       // right cheek
```

Eyes dy 16..21:
```
b(23,16,7,5,'#ff3a1a');
b(34,16,7,5,'#ff3a1a');
b(25,17,3,3,'#ffd060'); // bright core
b(36,17,3,3,'#ffd060');
```
Hmm eyes facing left... boss faces left but it's a head-on-ish view. Fine, symmetric.

Mouth dy 24..29:
```
b(26,24,12,5,'#1a0a20');
// teeth
b(27,24,2,2,'#e0d8b8'); b(31,24,2,2,'#e0d8b8'); b(35,24,2,2,'#e0d8b8');
```

Neck dy 28..34: b(26,28,12,8,'#4a2660');

Torso dy 32..54:
```
b(16,32,32,22,'#6a3a86');
b(16,32,32,6,'#7d4a9c');
b(22,38,20,14,'#8a5aa6');  // chest
b(26,42,12,8,'#b070c0');   // core glow
```

Shoulders:
```
b(8,30,14,14,'#5a2f74');
b(42,30,14,14,'#5a2f74');
b(8,30,14,4,'#7d4a9c');
b(42,30,14,4,'#7d4a9c');
```

Arms (with vertical offset for animation):
```
b(6,44+armOff,12,16,'#5a2f74');
b(46,44+armOff,12,16,'#5a2f74');
// claws
b(4,58+armOff,10,6,'#7d4a9c');
b(50,58+armOff,10,6,'#7d4a9c');
```

Hmm this is getting big. Let's just be careful that nothing exceeds 64. Arms at dy 44..60, claws 58..64. OK.

Legs dy 52..64:
```
b(18,52,12,12,'#4a2660');
b(34,52,12,12,'#4a2660');
b(16,60,16,4,'#3a1b4a');
b(32,60,16,4,'#3a1b4a');
```

Hmm legs overlap torso bottom (torso ends at 54). Fine, legs drawn after? Draw legs before torso. Order: horns/spikes, legs, torso, shoulders, arms, head.

OK, order matters. Let's draw: horns, legs, torso, shoulders, arms, claws, neck, head, eyes, mouth.

Now for the "slam" animation, arms go up: armOff negative, e.g., -10 during windup and jump.

For "proj", arms raise and an orb charges between hands.

For "beam", mouth glows.

Fine.

### Hero drawing

`drawHero(g, x, y, st)` where st = {state, t, facing, flash, runPhase}.

Local 16x20 grid anchored at bottom-center: left = x-8, top = y-20.

```js
const HX = dx => fx>0 ? x-8+dx : x+8-dx-1;
```
Hmm, for mirroring with width w: if facing right, left edge = x-8+dx. If facing left, we want the rect at [dx, dx+w) mirrored → left edge = x+8-(dx+w). So:

```js
const hx = (dx,w) => fx>0 ? x-8+dx : x+8-dx-w;
const h = (dx,dy,w,hh,col)=>{ g.fillStyle=C(col); g.fillRect(hx(dx,w), y-20+dy, w, hh); };
```

Parts:
- Cape: dx 2..14? Let's draw cape behind: b(3,7,10,10,'#a02020') — actually the cape should be behind the body, so drawn first, and slightly larger.

Let me define:
- Cape: rect dx 3, dy 7, w 10, h 11, color '#b02a2a', with darker '#7a1a1a' at bottom.
- Legs: two 3-wide legs.
- Torso: dx 4..12 (w8), dy 6..14, armor blue '#3a6ec8'.
- Chest highlight '#5a92e8' at dy 7.
- Belt: dy 13, w8, '#2a2a3a'.
- Arms: dx 2..4 (w2) and dx 12..14 (w2), dy 8..13, '#2a4f9a'.
- Head: dx 4..12 (w8), dy 0..6. Helmet '#b8c0d8', visor '#1a1a2a' at dy 3..5, eyes cyan.
- Plume: dx 7..9, dy -2..1? Let's skip or add a small red plume at top: dx 6, dy -2, w4, h3, '#d04040'.

Hmm, going above y-20 makes total height 22. Let's just keep everything within 0..20 and put the plume at dy 0..2 as part of the helmet.

Helmet design:
- dy 0..2: top dome, dx 5..11, '#c8d0e8'
- dy 2..6: dx 4..12, '#9aa4c0'
- visor dy 3..5, dx 5..11, '#161622'
- eye glow: dx 6..7 dy 4, and dx 9..10 dy 4, '#40e0ff'

Hmm the head is 8 wide and 6 tall. OK.

Legs: dy 14..20.
- Left leg: dx 4, w 3
- Right leg: dx 9, w 3
Run cycle: swing dx and dy.

Let me write run: phase p in 0..3.
- p=0: left leg forward (dx 6), right leg back (dx 6?) ...

I'll do simpler: legs move horizontally ±2 and one lifts.

```js
const lp = Math.sin(runPhase)*2;
h(4+lp, 14, 3, 6, dark);
h(9-lp, 14, 3, 6, dark);
```
Plus feet.

For idle: subtle bob: bodyY offset = (frame%2).

OK. Let's also add a small shadow ellipse under the hero and boss (drawn as a dark rect with alpha).

### Sword

When attacking, draw sword in front of hero based on attack frame.

Sword: blade 14 long, 2 wide, color '#d8e0f0', hilt '#8a6a20'.

For the attack animation with 3 phases over 18 frames:
- frames 0-5: windup — sword raised behind/above
- frames 6-10: slash — sword extends forward horizontally
- frames 11-17: recover — sword lowers

Draw sword as a set of rects:
- Windup: sword vertical above-right of hero: rect at (x+6, y-30, 2, 12).
- Slash: horizontal: rect at (x+8, y-14, 16, 2) extending forward. Add a slash arc effect (translucent white arc).
- Recover: diagonal.

For facing left, mirror.

I'll compute sword rects in local coords too.

Let's define attack phase p = atkT (0..17):
- p<6: sword above head: local dx 10..12, dy -6..6 → above the sprite. Let's just use world coords with facing.
- 6<=p<11: sword forward at chest height: from x to x+facing*18, at y-13.
- p>=11: diagonal down.

Simplest with rects:
```js
function swordRects(hx, hy, facing, p){
  // returns array of rects
}
```
I'll just inline in drawHero.

Also add a slash effect: a white/cyan arc drawn as a few rects with alpha, during the hit frames.

### Particles

```js
function spawnParticles(x,y,n,opts)
```
Particle: {x,y,vx,vy,life,max,color,size,grav}

Draw as fillRect of size×size at rounded position.

### Now let's write the main update.

Let me carefully write everything.

```js
// ===== State =====
let hero, boss, orbs, waves, parts, beam, shake, camX, gameState, gsT, victoryT, autoplay, timeAcc, tSec;

function resetGame(){
  hero = {x:60,y:FLOOR,vy:0,onGround:true,hp:20,maxHp:20,facing:1,state:'idle',
          anim:0,flash:0,invuln:0,atkT:-1,atkCd:0,hurtT:0,runPhase:0,dead:false,
          speed:1.7};
  boss = {x:245,y:FLOOR,hp:100,maxHp:100,state:'idle',t:0,flash:0,anim:0,
          jumps:0, idleDur:70, atkIdx:0, dead:false, bobY:0, armOff:0};
  orbs=[]; waves=[]; parts=[];
  beam = {active:false, x:0, warn:false, t:0};
  shake=0; camX=0;
  gameState='fight'; gsT=0; victoryT=0;
  ...
}
```

Update loop at 60fps fixed:

```js
function update(){
  tSec++;
  if(gameState==='fight') updateFight();
  else if(gameState==='death') updateDeath();
  else if(gameState==='victory') { victoryT++; if(victoryT>240) resetGame(); }
  updateParticles();
  // camera
  const targetCam = clamp((hero.x-160)*0.20,-22,14);
  camX += (targetCam - camX)*0.06;
  camX += Math.sin(tSec*0.012)*0.5;  // hmm this accumulates
}
```

Careful: don't add sway to camX repeatedly. Use a separate variable.

```js
camX = camSmooth + Math.sin(tSec*0.008)*3;
```
where camSmooth is smoothed. Let's do:
```js
camTarget = clamp((hero.x-160)*0.20, -22, 14);
camSmooth += (camTarget-camSmooth)*0.05;
camX = camSmooth + Math.sin(tSec*0.008)*4;
```

Shake: decay shake *= 0.88 each frame, and render offset = (Math.random()-0.5)*shake.

Now the fight update.

**Hero AI (autoplay)**:

```js
function heroAI(){
  const h=hero;
  if(h.hurtT>0) return;
  let moveDir=0;
  let wantJump=false;
  let threat=false;
  
  // Beam
  if(beam.warn && Math.abs(h.x-beam.x)<24){
     moveDir = h.x < beam.x ? -1 : 1;
     // make sure not running into boss
     if (h.x + moveDir*20 > 215) moveDir = -1;
     threat=true;
  }
  // Waves
  if(!threat){
    for(const w of waves){
      const tta = Math.abs(w.x - h.x)/w.speed;
      if(tta < 12 && ((w.x>h.x && w.dir<0)||(w.x<h.x && w.dir>0))){
        if(h.onGround) wantJump=true;
        threat=true;
      }
    }
  }
  // Orbs
  if(!threat){
    for(const o of orbs){
      const dxr = o.x - h.x;
      const tta = dxr / (o.vx || 0.001);
      if(tta>0 && tta<16 && Math.abs(o.x-h.x)<60){
        // incoming
        const predY = o.y + o.vy*tta;
        if(predY > FLOOR-24 && predY < FLOOR+2){
          // low -> jump or move
          if(Math.abs(dxr)<30 && h.onGround) wantJump=true;
          else moveDir = dxr>0?-1:1;
        } else {
          // high -> stay low, maybe move
          moveDir = 0;
        }
        threat=true;
      }
    }
  }
  ...
}
```

Hmm this is getting complicated. Let me simplify with a "safe spot" approach.

Simpler AI:
1. Compute a danger value for the current position from orbs/waves/beam.
2. If danger, move away; also jump if wave is close.

Let's do the priority approach but simplified:

```
// 1. Beam warning: get out of the column.
if (beam.warn) { move away from beam.x }
// 2. Ground wave incoming: jump.
else if (waveNear) { jump }
// 3. Orb incoming along my row: dodge
else if (orbNear) { move away from orb's x, or jump if orb is low and I can't move }
// 4. Otherwise: if too close to boss, back off; else approach & attack.
```

And jumping over orbs: orbs travel mostly horizontally with slight gravity. If an orb is at height FLOOR-20 to FLOOR (low), the hero can jump over it. If it's higher, the hero can just stand still (orbs pass above).

Let's have the AI:
- For each orb, if it's within 50px and approaching and predicted to be within the hero's body band, then: if orb.y > FLOOR-14 (low), jump; else move away horizontally (or just stand).

Hmm, if the orb is at chest height and the hero is standing, moving horizontally might not help since orbs are aimed. Actually moving perpendicular... orbs move horizontally-ish, so moving horizontally away is not useful unless you outrun. Better: jump if the orb is low, and if the orb is mid-height, crouch? No crouch.

Let's make orbs travel with an arc such that they end up at various heights. To keep it dodgeable: orbs are aimed at the hero's position at fire time, so if the hero moves, the orbs miss. So simple horizontal movement dodges them. Good — that's the classic pattern.

So AI: if an orb is approaching within 60px, move perpendicular (away from the orb's predicted y? no, just move). Let's just move in the direction away from the boss (retreat) or toward. Actually if orbs are aimed at where you were, moving in any direction dodges. Moving away from the boss is safest (more time).

So: if orbs approaching and within 70px → move away from boss (dir = -1) or toward boss depending on position. Let's move away from the boss to gain distance, unless we're cornered (x<50), then move toward.

Combined with the "approach and attack" logic this creates a natural dodge-and-weave behavior.

Let's also add: hero attacks when within range and cooldown ready and no immediate threat.

Range check: `Math.abs(h.x - boss.x) < 62` (since boss half-width is 32 and sword reach is ~24 from hero center, plus hero half-width 6 → total reach 30; boss left edge at boss.x-32; hero needs h.x + 30 > boss.x - 32 → h.x > boss.x - 62 = 183). So attack when h.x > 180 and facing right.

And the hero shouldn't get too close: stop at h.x = 190.

OK.

Also the hero gets pushed back when hit (knockback).

Let's write:

```js
function updateHeroAI(){
  const h=hero;
  h.aiMove = 0;
  h.aiJump = false;
  h.aiAttack = false;

  let threat = false;

  // Beam
  if(beam.warn){
    const d = h.x - beam.x;
    if(Math.abs(d) < 26){
      h.aiMove = d < 0 ? -1 : 1;
      threat = true;
    }
  }

  // Waves
  if(!threat){
    for(const w of waves){
      const approaching = (w.dir<0 && w.x > h.x-6) || (w.dir>0 && w.x < h.x+6);
      const dist = Math.abs(w.x - h.x);
      if(approaching && dist < 42){
        if(h.onGround) h.aiJump = true;
        threat = true;
        break;
      }
    }
  }

  // Orbs
  if(!threat){
    for(const o of orbs){
      const dx = o.x - h.x;
      const approaching = (o.vx<0 && dx>0) || (o.vx>0 && dx<0);
      if(approaching && Math.abs(dx)<70){
        // move away from boss to dodge
        h.aiMove = h.x > 150 ? 1 : -1;   // hmm which way?
        threat = true;
        break;
      }
    }
  }
  ...
}
```

Hmm, moving away from the boss means moving left (toward decreasing x) since the boss is on the right. But if the hero is already at x=60, moving left hits the wall. So: `h.aiMove = h.x < 100 ? 1 : -1;` — i.e., if near the left wall, move toward the boss? That would move into the orbs. Hmm.

Actually, the orbs are aimed at the hero's position at fire time and travel toward it. If the hero just runs left continuously, the orbs (which travel toward where the hero was) will land behind him. Good. So running left works as long as there's space. If the hero is at the wall, he should jump or move right past the orbs (risky). 

Let's make the hero's neutral position around x=170 so there's room to retreat left to 60. When orbs come, retreat left. Then approach again. That's a nice rhythm.

But wait — if the boss is at 245 and the hero retreats to 60, then the hero has to run back 120px to attack, taking ~70 frames. That's fine, and it dodges.

Let's refine: hero neutral x ~ 185 (attack position). On orb threat, move left. After dodging, approach again.

OK reasonable.

For beams: the beam locks at hero's x at lock time. If the hero is at 185 and beam locks at 185, the hero runs left at 1.7px/frame for 30 frames = 51px → x=134. Safe (beam half-width 11). 

But if the hero is at the left wall (x=50) when the beam locks... it'll be at 50 and beam at 50 → can't escape. Need to handle: if beam locks and hero is near a wall, he should be able to move right. Beam half-width 11, hero needs to move 11+6=17px. 30 frames is plenty. So fine.

Waves: jump timing. Wave speed 3, spawn at boss.x=245, hero at 185 → distance 60 → 20 frames. AI jumps when dist < 42 → about 14 frames before impact. Jump airtime ~26 frames, height 24. The wave passes under. Good.

But there are waves going both directions. The right-going one is irrelevant.

**Now, what if the hero is jumping and a wave is coming?** Already airborne, fine.

OK.

**Boss AI / state machine**:

```js
function updateBoss(){
  const b=boss;
  if(b.dead) return;
  if(b.flash>0) b.flash--;
  b.t++;
  
  if(b.state==='idle'){
    b.bobY = Math.sin(tSec*0.06)*1;
    b.armOff = Math.sin(tSec*0.06)*1;
    if(b.t > b.idleDur){
      b.t=0;
      b.atkIdx = (b.atkIdx+1)%3;
      b.state = ['proj','slam','beam'][b.atkIdx];
      b.attackFired=false;
    }
  }
  else if(b.state==='proj'){
    // t 0..30 windup
    b.armOff = -Math.min(12, b.t*0.5);
    if(b.t===28){ /* spawn orb */ fireOrbs(); }
    if(b.t>70){ b.state='idle'; b.t=0; b.idleDur=50; b.armOff=0; }
  }
  ...
}
```

Hmm, `b.armOff` for arms raising. Since arms drawn at dy 44+armOff, armOff negative moves them up. But raising arms for casting should also move them outward. Let's just use armOff.

For slam:
```js
else if(b.state==='slam'){
  if(b.t<20){ b.armOff = -b.t*0.7; b.rise = b.t*0.5; }  // windup: rise a bit
  else if(b.t<40){ b.rise = 10 + Math.sin((b.t-20)/20*Math.PI)*20; b.armOff=-16; }
  else if(b.t===40){ 
     b.rise=0; shake=10; spawnWaves(); spawnDust();
  }
  else { ... }
}
```

Hmm let me simplify: boss "rise" offset applied to boss.y for drawing.

Slam timeline (t):
- 0..24: windup — arms raise, body crouches slightly.
- 25..45: jump — rise = sin curve up to 22px.
- 46: land — spawn waves, shake 12, dust particles.
- 47..90: recover.
- 91: back to idle.

OK.

Beam:
- 0..30: charge — mouth glow grows, beam.x tracks hero.x.
- 30: lock beamX, beam.warn = true.
- 30..60: warning flashes, charge grows.
- 60: beam.active = true, beam.t = 0.
- 60..95: firing.
- 96: beam.active=false, beam.warn=false.
- 96..120: recover → idle.

Let's put beamT in the beam object.

Now, during beam firing, the boss should have its mouth open with a bright core.

OK.

**Drawing the beam**: a vertical column from the boss's mouth (y ≈ boss.y-64+24 = 92) down to the floor and beyond. Actually let's make it from the top of the screen to the floor, like a laser. Hmm, a beam from the mouth going down at 245-ish... but the beam x is where the hero was, not the boss's x. So it's more like the boss fires a beam that sweeps down at that x. Visually, it's a vertical column of light. Fine — like a "meteor strike" or "lightning". 

Let's render it as a vertical column from y=0 to y=FLOOR+20 at beam.x, width ~22, with bright core. Plus a warning column (thin, translucent red) during the warn phase.

Good, and a bright impact at the floor.

**Orb drawing**: a glowing ball with a trail. Draw as a filled circle approximated by rects: 5x5 with corners cut. Colors: outer #ff6a2a, mid #ffb020, core #fff0a0.

Let's do a 7x7 pixel circle for radius 3.5. And a smaller inner.

Orb radius for collision ~5.

**Wave drawing**: a ground shockwave: a jagged rising arc. Draw as a triangle-ish shape with rock chunks. Simple: a series of vertical rects increasing then decreasing in height, in brown/orange.

```js
function drawWave(w){
  const x = w.x, y = FLOOR;
  const hgt = 14;
  for(let i=-8;i<=8;i++){
    const hh = Math.round(hgt * Math.cos(i/9 * 1.5));
    ...
  }
}
```
Let's do: for dx from -9 to 9 step 1, height = hgt*(1 - (dx/10)^2), draw a 1px column from FLOOR-hh to FLOOR with color depending on height.

Colors: outer '#8a4a1a', inner '#ff9a3a', plus white core for the top.

Good.

**HUD**:
Top: hero health bar left, boss health bar right.

Hero bar: x=8, y=8, w=120, h=8. Frame 1px dark. Fill green/blue proportional.
Boss bar: x=W-8-120=192, y=8, w=120, h=8. Fill red/purple, drawn right-to-left or left-to-right? Boss bars usually deplete from the right. Let's deplete from left to right... Standard: fill from left, decreasing width. I'll just do width proportional anchored at the right edge... Actually simplest: bar fills from left with boss hp fraction. It depletes from the right. Fine.

Labels: "HERO" and "BOSS" in tiny text above? Or below. With 5x7 font at scale 1, "HERO" is 4*6-1=23px wide. Put at y=17.

Hmm, tight. Let's do:
- Hero bar: x=8, y=6, w=110, h=7.
- Text "HERO" at x=8, y=15, scale 1 (7px tall) → occupies y 15..22. Then maxHp number.
- Boss bar: x=W-118=202, y=6, w=110, h=7.
- Text "BOSS" right-aligned at x=W-8-23=289.

That works.

In the bar, also draw a "damage lag" white segment that shrinks slowly. Nice touch.

**Autoplay indicator**: bottom-left text "AUTOPLAY: ON  [P]" in gray.

**VICTORY screen**: dark overlay + "VICTORY" big (scale 3) centered + "BOSS DEFEATED" small.

Big text: 7 letters * 6 * 3 = 126 px wide minus 3 = 123. Centered at (320-123)/2 = 98. y = 80.

Add a blinking "PRESS P FOR MANUAL" maybe. Since no interaction needed, just show "DEMO COMPLETE".

Also add stats: time taken.

OK let's write the code.

One more thing: **hit flash implementation**. `b.flash` counts down; while > 0, draw white. I'll make flash 6 frames, white during first 4.

**Particles on hit**: spawn 10 sparks at hit position with random velocities.

**Death explosion**: over 90 frames, spawn ~6 particles per frame at random positions within the boss, plus big shake, plus flash.

Let me now write out the full code.

```js
// ---------- Font ----------
const FONT = {
'A':['01110','10001','10001','11111','10001','10001','10001'],
...
};
```

I need to be careful with the string arrays.

Let me write the code in full now.

```js
const W=320, H=180, FLOOR=150;
```

Hero feet at FLOOR=150, hero is 20 tall → head at 130. Boss 64 tall → top at 86. Health bars at top 0..25. Good, no overlap.

Let me write.

```js
let hero, boss, orbs, waves, parts, beam, shake, camSmooth, camX, gameState, gsT, victoryT, autoplay, T;

function resetGame(){
  hero={x:60,y:FLOOR,vy:0,onGround:true,hp:20,maxHp:20,hpLag:20,facing:1,state:'idle',
        anim:0,flash:0,invuln:0,atkT:-1,atkCd:0,hurtT:0,runPhase:0,dead:false,
        aiMove:0,aiJump:false,aiAttack:false};
  boss={x:245,y:FLOOR,hp:100,maxHp:100,hpLag:100,state:'idle',t:0,flash:0,
        idleDur:60,atkIdx:-1,rise:0,armOff:0,dead:false,deathT:0};
  orbs=[]; waves=[]; parts=[];
  beam={active:false,x:160,warn:false,fire:0};
  shake=0; camSmooth=0; camX=0;
  gameState='fight'; gsT=0; victoryT=0; T=0;
  autoplay = true;
}
```

Hmm, `autoplay` should persist across resets. Let's set it outside resetGame, or keep it in reset. Keep it outside.

Actually initial autoplay = true. P toggles.

If autoplay is off, there's no input handling... The requirement says "No interaction required" and autoplay is on by default. P toggles autoplay. But if autoplay is off, we need manual controls to be meaningful. Let's add arrow keys/WASD + space/J for manual play as a bonus. That's fine.

Actually the spec says "No interaction required" - it doesn't forbid it. I'll add manual controls for completeness.

Let's implement: if autoplay off, use keyboard input.

OK.

Now writing the update.

```js
function update(){
  T++;
  if(gameState==='fight'){
    updateHero();
    updateBoss();
    updateOrbs();
    updateWaves();
    updateBeam();
    checkCollisions();
  } else if(gameState==='death'){
    gsT++;
    bossDeathUpdate();
  } else if(gameState==='victory'){
    victoryT++;
    if(victoryT>300) resetGame();
  }
  updateParticles();
  // camera
  const camTarget = clamp((hero.x-160)*0.22, -24, 16);
  camSmooth += (camTarget-camSmooth)*0.05;
  camX = camSmooth + Math.sin(T*0.009)*4;
  shake *= 0.88;
  if(shake<0.2) shake=0;
  // hp lag
  if(hero.hpLag>hero.hp) hero.hpLag=Math.max(hero.hp,hero.hpLag-0.5);
  if(boss.hpLag>boss.hp) boss.hpLag=Math.max(boss.hp,boss.hpLag-0.4);
}
```

Wait — hpLag should be for the "white" trailing bar. It should decrease slowly. But it's stored as a number. Fine.

Hero update:

```js
function updateHero(){
  const h=hero;
  if(h.flash>0)h.flash--;
  if(h.invuln>0)h.invuln--;
  if(h.hurtT>0){ h.hurtT--; }
  if(h.atkCd>0) h.atkCd--;
  
  if(h.hurtT>0){
    // knockback
    h.x += h.knock * 0.6;
    h.knock *= 0.85;
    h.state='hurt';
  } else if(h.atkT>=0){
    h.atkT++;
    if(h.atkT>18){ h.atkT=-1; h.state='idle'; }
    else h.state='attack';
  } else {
    // movement
    if(autoplay){ heroAI(); }
    else { readInput(); }
    let mv = h.aiMove;
    if(mv!==0){ h.x += mv*1.8; h.facing = mv>0?1:-1; h.state='run'; h.runPhase += 0.35; }
    else h.state = h.onGround?'idle':'jump';
    if(h.aiJump && h.onGround){ h.vy=-4.0; h.onGround=false; }
    if(h.aiAttack && h.atkCd<=0 && h.onGround){ startAttack(); }
  }
  
  // gravity
  if(!h.onGround){
    h.vy += 0.26;
    h.y += h.vy;
    if(h.y >= FLOOR){ h.y=FLOOR; h.vy=0; h.onGround=true; spawnDust(h.x, FLOOR, 5); }
  }
  h.x = clamp(h.x, 26, 214);
  h.anim++;
}
```

Hmm, `h.state` handling — if attacking, atkT>=0. OK.

Wait, there's an issue: when attacking, the hero shouldn't move. That's fine.

Also `h.facing` should be 1 (facing right toward boss) generally.

startAttack:
```js
function startAttack(){
  hero.atkT=0; hero.atkCd=26; hero.state='attack'; hero.hitDone=false;
}
```

Attack hit check in updateHero or in a separate function:
```js
if(h.atkT===6 && !h.hitDone){
  h.hitDone=true;
  // hitbox in front
  const hx = h.x + h.facing*20;
  if(boss.hp>0 && Math.abs(hx - boss.x) < 44 && Math.abs(h.y - boss.y) < 40){
     damageBoss(5);
  }
}
```

Hmm, boss hitbox: boss.x ± 30, so |hx - boss.x| < 30 + something. Let's use: the sword tip reaches h.x + 26. Hit if sword tip is within boss's body: |h.x + 26 - boss.x| < 32 → i.e., h.x > boss.x - 58 = 187. Let's use that.

```js
const tip = h.x + h.facing*26;
if(Math.abs(tip - boss.x) < 34) damageBoss(5);
```

With boss.x=245, that means h.x in [185, 253]. And the hero max x is 214. So attacking works from 185 to 214. Good.

damageBoss:
```js
function damageBoss(d){
  if(boss.dead) return;
  boss.hp -= d;
  boss.flash = 8;
  shake = Math.max(shake, 3);
  spawnHitSparks(boss.x + rnd(-16,16), boss.y - rnd(20,50));
  if(boss.hp<=0){ boss.hp=0; boss.dead=true; gameState='death'; gsT=0; shake=14; }
}
```

Hmm, but setting gameState='death' immediately stops the fight update. That's fine — we want the hero to stop and the boss to explode.

Boss death update:
```js
function bossDeathUpdate(){
  const b=boss;
  shake = Math.max(shake, 6);
  // spawn explosion particles
  for(let i=0;i<5;i++){
    parts.push({x:b.x+rnd(-28,28), y:b.y-rnd(0,64), vx:rnd(-2,2), vy:rnd(-3,1),
       life:rnd(20,50), max:50, col: pick(['#ffd24a','#ff7a1a','#ff3a1a','#ffffff']), size: rnd(1,3)|0, grav:0.08});
  }
  if(gsT%8===0) shake=10;
  if(gsT>70){ 
     gameState='victory'; victoryT=0; shake=18;
     for(let i=0;i<80;i++) parts.push({...big blast...});
  }
}
```

Boss visible until gsT > 70, then disappears. I'll draw the boss with flicker during death.

OK.

Now `updateOrbs`:
```js
function updateOrbs(){
  for(let i=orbs.length-1;i>=0;i--){
    const o=orbs[i];
    o.x += o.vx; o.y += o.vy; o.vy += 0.02;
    o.life--;
    if(o.life<=0 || o.x<-20 || o.x>W+20 || o.y>FLOOR+10){ orbs.splice(i,1); }
  }
}
```

Orbs shouldn't go through the floor — let them splash on the floor. If o.y > FLOOR → remove + dust particles.

`updateWaves`:
```js
for(...){ w.x += w.dir*w.speed; w.life--; if(w.life<=0||w.x<-30||w.x>W+30) remove; }
```

`updateBeam` handled in updateBoss.

Collision:
```js
function checkCollisions(){
  const h=hero;
  if(h.invuln>0 || h.hurtT>0) return;
  // orbs
  for(const o of orbs){
    if(Math.abs(o.x-h.x)<10 && o.y > h.y-18 && o.y < h.y+2){ hurtHero(2,-1); break; }
  }
  // waves
  for(const w of waves){
    if(Math.abs(w.x-h.x)<12 && h.y > FLOOR-15){ hurtHero(2, w.x>h.x?-1:1); break;}
  }
  // beam
  if(beam.active && Math.abs(beam.x-h.x)<12){ hurtHero(2, beam.x>h.x?-1:1); }
}
```

hurtHero:
```js
function hurtHero(d, dir){
  hero.hp-=d; hero.invuln=60; hero.hurtT=14; hero.flash=10;
  hero.knock = dir*2.5;
  shake=Math.max(shake,5);
  spawnHitSparks(hero.x, hero.y-12, '#ff6060');
  if(hero.hp<=0){ hero.hp=0; /* reset fight after a moment */ }
}
```

For hero death: let's just respawn the hero with full HP and reset the boss HP too (restart the fight). Simpler: if hero dies, resetGame() after a short delay. Let's set hero.dead and after 90 frames reset. But we also need to handle gameState. Let's add gameState='defeat' briefly... Actually let's just give the hero a lot of HP and make the AI good so it never dies. But to be safe, add a reset.

I'll add: if hero.hp<=0 → after 60 frames, resetGame(). Use a simple timer.

Let me handle: `if(hero.hp<=0){ hero.deadT = (hero.deadT||0)+1; ... }`. Simplify: give hero invuln 120 and hp = maxHp after "death"? Eh.

Let's just do: if hero.hp <= 0 → hero.hp = 0, gameState = 'defeat', gsT = 0; after 90 frames → resetGame(). And render "DEFEAT" text.

Fine, it's a rare fallback.

Now let's write the render function.

```js
function render(){
  ctx.setTransform(1,0,0,1,0,0);
  ctx.imageSmoothingEnabled=false;
  ctx.clearRect(0,0,W,H);
  ctx.fillStyle='#08060e';
  ctx.fillRect(0,0,W,H);
  
  const sx = Math.round((Math.random()-0.5)*shake*2);
  const sy = Math.round((Math.random()-0.5)*shake*2);
  ctx.save();
  ctx.translate(sx, sy);
  
  drawBackground();
  
  // entities with camera
  ctx.save();
  ctx.translate(-camX, 0);
  ... draw world ...
  ctx.restore();
  
  ctx.restore();
  
  drawHUD();
}
```

Wait — the background parallax needs the camera, but the shadow/shake translate should apply to everything. Let me restructure:

- translate(shake)
- drawBackground() — internally uses camX with per-layer multipliers, drawing from -80 to W+80.
- translate(-camX) → draw floor markers and entities... 

Hmm, but the floor should also be part of the world. Let me have:

- Parallax layers each draw with their own offset (bg uses -camX*0.18, mid uses -camX*0.55).
- Then ctx.translate(-camX) for the world (floor + entities).

But the floor moves with camX*1.0 and entities also move with camX. Good, consistent.

So:
```js
ctx.save();
ctx.translate(shakeX, shakeY);
drawBgParallax(-camX*0.18, -camX*0.55);
ctx.save();
ctx.translate(-camX,0);
drawFloor();
drawEntities();
ctx.restore();
ctx.restore();
```

Hmm, but the floor is drawn at world coords 0..320, and with translate(-camX) it shifts. The floor strip needs to extend beyond: draw from -80 to W+80.

Good.

Now `drawBgParallax(o0, o1)`.

Note: the wall should be drawn at y 0..150.

Let me write it.

```js
function drawBgParallax(o0,o1){
  // base wall
  ctx.fillStyle='#16112a';
  ctx.fillRect(-80,0,W+160,FLOOR);
  // far arches with o0
  for(let x=-100;x<W+100;x+=80){
    const ax = x + o0;
    ctx.fillStyle='#100d20';
    ctx.fillRect(ax+10, 30, 44, FLOOR-30);
    // arch top
    ctx.fillRect(ax+16, 22, 32, 10);
    ctx.fillRect(ax+22, 16, 20, 8);
    ctx.fillRect(ax+28, 12, 8, 6);
  }
  // brick seams
  ctx.fillStyle='#1d1735';
  for(let y=6;y<FLOOR;y+=14){ ctx.fillRect(-80,y,W+160,2); }
  ...
}
```

Hmm, the arches drawn as dark rectangles on a lighter wall. That works as a dungeon.

Then mid layer: pillars with o1.

```js
  for(let x=-100;x<W+100;x+=110){
    const px0 = Math.round(x + o1);
    ctx.fillStyle='#241b3d'; ctx.fillRect(px0, 10, 22, FLOOR-10);
    ctx.fillStyle='#2e2450'; ctx.fillRect(px0+2, 10, 18, FLOOR-10);
    ctx.fillStyle='#3a2e63'; ctx.fillRect(px0+2, 10, 4, FLOOR-10);
    // capital
    ctx.fillStyle='#3a2e63'; ctx.fillRect(px0-3, 6, 28, 8);
    ctx.fillStyle='#241b3d'; ctx.fillRect(px0-3, 14, 28, 3);
  }
```

Torches at pillar x + 11, y = 60.

But torch light should be in front. Let's draw the torch bracket and flame at y=64.

Also add a glow behind. Let's do a simple additive glow using globalCompositeOperation='lighter' with a few rects. Might be nice.

Actually let's keep it simple: draw glow rects with globalAlpha.

Now the floor:

```js
function drawFloor(){
  ctx.fillStyle='#2a2038'; ctx.fillRect(-80,FLOOR,W+160,H-FLOOR);
  ctx.fillStyle='#352a47'; ctx.fillRect(-80,FLOOR,W+160,3);
  // tiles
  ctx.fillStyle='#1e172c';
  for(let x=-80;x<W+80;x+=40){ ctx.fillRect(x, FLOOR+4, 2, H-FLOOR); }
  for(let y=FLOOR+14;y<H;y+=14){ ctx.fillRect(-80,y,W+160,2); }
  // highlights
  ctx.fillStyle='#3d3152';
  for(let x=-80;x<W+80;x+=40){ ctx.fillRect(x+2, FLOOR+4, 38, 2); }
}
```

Good enough.

Now let's write `drawEntities()`:

```js
function drawEntities(){
  // shadows
  drawShadow(hero.x, FLOOR, 12);
  if(!boss.dead || gameState!=='victory') drawShadow(boss.x, FLOOR, 34);
  
  // beam warning
  if(beam.warn) drawBeamWarn();
  
  // boss
  if(boss.hp>0 || gameState==='death') drawBoss();
  
  // waves
  for(const w of waves) drawWave(w);
  
  // hero
  drawHeroSprite();
  
  // orbs
  for(const o of orbs) drawOrb(o);
  
  // beam
  if(beam.active) drawBeam();
  
  // particles
  for(const p of parts) drawParticle(p);
}
```

Hmm, the beam should be drawn over the boss? It's a separate column, fine.

Order: shadows, boss, hero, waves, orbs, beam, particles.

Let's write each draw function.

**drawShadow(x, y, r)**: 
```js
ctx.globalAlpha=0.35; ctx.fillStyle='#000';
ctx.beginPath(); ctx.ellipse(x, y+2, r, r*0.3, 0,0,Math.PI*2); ctx.fill();
ctx.globalAlpha=1;
```
Ellipse is anti-aliased but at low res it's fine. Actually to be pixel-crisp, let's use rects:
```js
ctx.fillRect(x-r, y+1, r*2, 3);
ctx.fillRect(x-r+3, y-1, r*2-6, 5);  // hmm
```
Let's just do 3 nested rects:
```js
ctx.globalAlpha=0.30; ctx.fillStyle='#000';
ctx.fillRect(Math.round(x-r), Math.round(y), r*2, 4);
ctx.fillRect(Math.round(x-r*0.6), Math.round(y-2), Math.round(r*1.2), 6);
```
Fine.

**drawBoss**:

```js
function drawBoss(){
  const b=boss;
  const flash = b.flash>0 && (b.flash%6>2);
  const C = c => flash ? '#ffffff' : c;
  const X = Math.round(b.x - 32);
  const Y = Math.round(b.y - 64 - b.rise + (b.dead?0:0));
  // flicker during death
  if(gameState==='death' && Math.floor(gsT/3)%2===1) return;
  const P=(dx,dy,w,h,c)=>{ ctx.fillStyle=C(c); ctx.fillRect(X+dx, Y+dy, w, h); };
  ...
}
```

Hmm, the flicker during death — returning early would hide the boss entirely every other frame. Let's use a lower flicker rate: `if(gameState==='death' && gsT>50 && Math.floor(gsT/2)%2) return;` Actually let's make the boss shrink/fade. Simpler: during death, draw the boss normally but with white flashes increasing.

OK.

Boss body parts with `rise` offset applied to Y.

Also during slam, the boss's arms go up.

Let's write:

```js
  const armOff = Math.round(b.armOff);
  // horns
  P(12,6,10,10,'#cfc6a6'); P(8,2,8,8,'#e6dfc0');
  P(42,6,10,10,'#cfc6a6'); P(48,2,8,8,'#e6dfc0');
  // head spikes
  P(22,4,4,6,'#cfc6a6'); P(30,0,4,8,'#e6dfc0'); P(38,4,4,6,'#cfc6a6');
```

Hmm wait, the head is at dy 8..30 and x 20..44. Horns at x 12..22 and 42..52 — they're at the sides. OK but they'd float. Let's attach them: left horn base at (18,12)-(26,20) going up-left to (10,2). I'll just draw a few overlapping rects.

```js
  // left horn
  P(16,10,8,8,'#cfc6a6');
  P(12,6,8,8,'#d8d0b0');
  P(9,2,6,6,'#e6dfc0');
  // right horn
  P(40,10,8,8,'#cfc6a6');
  P(44,6,8,8,'#d8d0b0');
  P(49,2,6,6,'#e6dfc0');
```

Good.

Legs:
```js
  P(17,52,13,12,'#472162');
  P(34,52,13,12,'#472162');
  P(15,60,16,4,'#331545');
  P(33,60,16,4,'#331545');
```

Torso:
```js
  P(16,32,32,22,'#6a3a86');
  P(16,32,32,5,'#7d4a9c');
  P(21,38,22,14,'#8a5aa6');
  P(27,41,10,9,'#c07ad0');   // glowing core
```

Shoulders:
```js
  P(8,30,14,14,'#5a2f74'); P(8,30,14,4,'#7d4a9c');
  P(42,30,14,14,'#5a2f74'); P(42,30,14,4,'#7d4a9c');
```

Arms:
```js
  P(5,44+armOff,11,16,'#5a2f74');
  P(48,44+armOff,11,16,'#5a2f74');
  // claws
  P(3,57+armOff,10,7,'#7d4a9c');
  P(51,57+armOff,10,7,'#7d4a9c');
```

Hmm armOff can be -16, so arms at dy 28..44 and claws at 41..48. That would put claws at the shoulder level. Fine for "arms raised".

But the claws would overlap the head area. It's fine, arms raised in front.

Hmm, actually if armOff is -16, arms span dy 28..44 which is over the head region (dy 8..30) partially. OK visually acceptable.

Neck & head:
```js
  P(26,26,12,10,'#4a2660');
  P(20,8,24,22,'#6a3a86');
  P(20,8,24,5,'#7d4a9c');
  P(18,14,4,14,'#5a2f74');
  P(42,14,4,14,'#5a2f74');
```

Eyes:
```js
  const eg = (Math.sin(T*0.1)*0.5+0.5);
  P(23,16,8,5,'#ff3a1a'); P(33,16,8,5,'#ff3a1a');
  P(25,17,4,3,'#ffd060'); P(35,17,4,3,'#ffd060');
```

Hmm, x 33..41 for the right eye. Head is 20..44. OK.

Mouth:
```js
  P(26,24,12,5,'#180a22');
  P(27,24,2,2,'#e6dfc0'); P(31,24,2,2,'#e6dfc0'); P(35,24,2,2,'#e6dfc0');
```

Hmm, mouth at dy 24..29 and the head is 8..30. Good.

For beam charge, make the mouth glow: if state==='beam' and charging, draw a bright rect at the mouth that grows.

For proj, draw a charging orb between the raised hands: at (X+32, Y+30) with a growing radius.

OK.

**drawHeroSprite**:

```js
function drawHeroSprite(){
  const h=hero;
  const flash = h.flash>0 && (h.flash%6>3);
  const C = c => flash ? '#ffffff' : c;
  const fx = h.facing;
  const bx = Math.round(h.x), by = Math.round(h.y);
  const HX = (dx,w) => fx>0 ? bx-8+dx : bx+8-dx-w;
  const P=(dx,dy,w,hh,c)=>{ ctx.fillStyle=C(c); ctx.fillRect(HX(dx,w), by-20+dy, w, hh); };
  
  const st = h.state;
  let bob = 0;
  if(st==='idle') bob = (Math.floor(h.anim/24)%2);
  ...
}
```

Hmm the bob changes the whole body y — I'd need to apply it to all rects. Let's apply via `by` offset: `const by = Math.round(h.y) - bob;`. But then the legs would detach from the floor. It's fine for a 1px bob.

Actually let's skip the bob and just animate the arms/head. Simpler: no bob for idle, but add a subtle breathing via the chest rect.

Let's just do no bob, and add idle arm sway.

Run: legs swing.

Let me write:

```js
  // cape (behind)
  P(2, 6, 12, 12, '#8e2020');
  P(2, 14, 12, 5, '#6a1414');
  
  // legs
  let l1=0,l2=0, ly1=0, ly2=0;
  if(h.state==='run'){
    const p = h.runPhase;
    l1 = Math.sin(p)*2.5; l2 = Math.sin(p+Math.PI)*2.5;
    ly1 = Math.max(0, Math.sin(p)*2)|0;
  }
  P(4 - l1, 14, 3, 6, '#2c4a86');
  P(9 - l2, 14, 3, 6, '#2c4a86');
  // boots
  P(3-l1, 19, 5, 1, '#1a1a2c');
  P(8-l2, 19, 5, 1, '#1a1a2c');
```

Hmm `- l1` where l1 is a float → non-integer positions. Need rounding. Let me round inside P: `Math.round(HX(dx,w))`. Yes, P already uses HX which may be fractional. Let's round in P.

OK.

```js
  // torso
  P(4, 6, 8, 8, '#3a6ec8');
  P(4, 6, 8, 2, '#5a92e8');
  P(6, 9, 4, 3, '#ffd24a');   // chest emblem
  P(4, 13, 8, 1, '#232338');  // belt
  
  // arms
  const armSwing = h.state==='run' ? Math.sin(h.runPhase)*1.5 : 0;
  P(2, 7+armSwing, 3, 6, '#2c4a86');
  P(11, 7-armSwing, 3, 6, '#2c4a86');
  
  // head
  P(4, 0, 8, 6, '#9aa4c0');
  P(5, 0, 6, 2, '#c8d0e8');
  P(5, 3, 6, 2, '#141422');   // visor
  P(6, 3, 2, 2, '#40e0ff');
  P(9, 3, 2, 2, '#40e0ff');
```

Hmm, "P(5,0,6,2)" is the helmet top highlight. And "P(4,0,8,6)" is the whole head. But the visor is at dy 3..5 and the eyes at dy 3..5. Let's make the head 7 tall: dy 0..7? Then the torso at 6..14 overlaps. Let's do head dy 0..6, torso dy 6..14.

Actually head 6 tall is small but ok for a 16x20 sprite.

Hmm, let me reconsider: hero total 20 tall.
- dy 0..6: head (6)
- dy 6..14: torso (8)
- dy 14..20: legs (6)

Good.

Sword drawing when attacking:

```js
  if(h.atkT>=0){
    const p = h.atkT;
    const dir = fx;
    let sx0, sy0, sw, sh;
    if(p<6){ // windup: sword up
      // vertical blade above/behind
      P(11, -10, 2, 14, '#d8e0f0');  // hmm negative dy
    }
  }
```

Negative dy goes above the sprite. That's fine, P handles it (by-20+dy).

But HX with negative dy is fine.

Let me define the sword per phase:
- p 0..5 (windup): blade vertical at dx 11..13, dy -8..6. Plus hilt.
- p 6..11 (slash): blade horizontal at dx 12..28, dy 8..10. Plus a slash arc.
- p 12..17 (recover): blade diagonal down: a few rects stepping.

For horizontal blade with facing: use HX so it mirrors correctly. dx 12 with w 16 → for facing right, x from bx-8+12=bx+4 to bx+20. For facing left, mirrored to bx-20..bx-4. 

Slash arc effect: draw a few translucent white/cyan rects around the sword during p 6..11.

Let's write:
```js
  if(h.atkT>=0){
    const p=h.atkT;
    const white='#e8f0ff', steel='#c0cce0', gold='#d8a030';
    if(p<5){
      // raised
      P(10,-9,2,13,steel);
      P(10,-9,2,3,white);
      P(9,4,4,2,gold);
    } else if(p<12){
      const ext = Math.min(1,(p-5)/3);
      const bl = Math.round(16*ext)+6;
      P(10,7,bl,2,steel);
      P(10+bl-3,7,3,2,white);
      P(9,6,2,4,gold);
      // slash effect
      ctx.globalAlpha = 0.5*(1-(p-6)/8);
      ctx.fillStyle='#a0e8ff';
      const ax = HX(10, bl);
      ctx.fillRect(Math.round(ax), by-20+5, bl, 6);
      ctx.globalAlpha=1;
    } else {
      // recover diagonal
      for(let i=0;i<8;i++){
        P(11+i, 6+i, 2, 2, steel);
      }
    }
  }
```

Hmm the arc might be too subtle. Let's make it a proper arc of a few rects at different heights.

Actually let's simplify: draw the slash as 3 horizontal bars of decreasing alpha at dy 6, 8, 10.

Whatever, it'll look fine.

OK now the **beam drawing**.

```js
function drawBeamWarn(){
  const x = beam.x;
  ctx.globalAlpha = 0.25 + 0.2*Math.sin(T*0.6);
  ctx.fillStyle='#ff3040';
  ctx.fillRect(Math.round(x-11), 0, 22, FLOOR+10);
  ctx.globalAlpha=1;
  // edge lines
  ctx.fillStyle='#ff8090';
  ctx.fillRect(Math.round(x-11), 0, 1, FLOOR+10);
  ctx.fillRect(Math.round(x+10), 0, 1, FLOOR+10);
}
```

Beam active:
```js
function drawBeam(){
  const x=Math.round(beam.x);
  const t = beam.fire;
  const w = 11 + Math.sin(T*0.9)*1.5;
  ctx.fillStyle='#ff9a3a';
  ctx.fillRect(x-w, 0, w*2, FLOOR+12);
  ctx.fillStyle='#ffd24a';
  ctx.fillRect(x-w*0.6, 0, w*1.2, FLOOR+12);
  ctx.fillStyle='#fffbe0';
  ctx.fillRect(x-w*0.25, 0, w*0.5, FLOOR+12);
  // impact
  ctx.fillStyle='#fff';
  ctx.fillRect(x-14, FLOOR-6, 28, 8);
}
```

Add flicker widths.

Hmm, beam.fire is the timer.

OK.

**Orb drawing**:
```js
function drawOrb(o){
  const x=Math.round(o.x), y=Math.round(o.y);
  const s = Math.sin(T*0.5+o.seed)*1.5;
  const r = 5+s;
  ctx.fillStyle='#ff5a1a';
  ctx.fillRect(x-r, y-r+1, r*2, r*2-2);
  ctx.fillRect(x-r+1, y-r, r*2-2, r*2);
  ctx.fillStyle='#ffb020';
  ctx.fillRect(x-r+2, y-r+2, r*2-4, r*2-4);
  ctx.fillStyle='#fff4c0';
  ctx.fillRect(x-2, y-2, 4, 4);
}
```

Fine.

**Wave drawing**:
```js
function drawWave(w){
  const cx = Math.round(w.x);
  for(let i=-9;i<=9;i++){
    const t = 1 - Math.abs(i)/10;
    const hh = Math.round(16*t*t);
    ...
  }
}
```
Hmm, let me use a smoother shape: hh = round(15*Math.cos(i/10*1.4)).

Colors: 
- outer: '#8a3a10'
- main: '#ff8a2a'
- core: '#ffd24a'
- top: '#fff'

Draw each column with the color depending on height.

```js
for(let i=-9;i<=9;i++){
  const f = Math.cos(i/10*1.5);
  if(f<=0) continue;
  const hh = Math.round(15*f);
  const y0 = FLOOR - hh;
  ctx.fillStyle = hh>10 ? '#ffd24a' : (hh>5 ? '#ff8a2a' : '#8a3a10');
  ctx.fillRect(cx+i, y0, 1, hh);
  // darker base
  ctx.fillStyle='#5a2408';
  ctx.fillRect(cx+i, FLOOR-3, 1, 3);
}
```

Plus some debris particles.

Good enough.

OK, and the wave has a `dir` so it's symmetric anyway.

**Particles**:
```js
function drawParticle(p){
  const a = p.life/p.max;
  ctx.globalAlpha = Math.min(1, a*1.5);
  ctx.fillStyle = p.col;
  ctx.fillRect(Math.round(p.x), Math.round(p.y), p.size, p.size);
  ctx.globalAlpha=1;
}
```

Setting globalAlpha per particle is a bit slow but with a few hundred particles at 60fps it's fine.

**HUD**:

```js
function drawHUD(){
  // hero bar
  drawBar(8, 6, 110, 7, hero.hp/hero.maxHp, hero.hpLag/hero.maxHp, '#3ad06a', '#2a8a46');
  drawText('HERO', 8, 16, '#8aa0c0');
  // boss bar
  drawBar(W-118, 6, 110, 7, boss.hp/boss.maxHp, boss.hpLag/boss.maxHp, '#e0403a', '#7a1a1a', true);
  drawText('BOSS', W-8-23, 16, '#c08a8a');
  // autoplay
  drawText('P:AUTOPLAY '+(autoplay?'ON':'OFF'), 8, H-12, autoplay?'#40e0a0':'#808080');
}
```

Hmm, "P:AUTOPLAY ON" = 14 chars * 6 - 1 = 83px. Fits.

drawBar:
```js
function drawBar(x,y,w,h,frac,lagFrac,c1,c2,flip){
  ctx.fillStyle='#0a0810'; ctx.fillRect(x-1,y-1,w+2,h+2);
  ctx.fillStyle='#2a2438'; ctx.fillRect(x,y,w,h);
  const wl = Math.round(w*Math.max(0,lagFrac));
  ctx.fillStyle='#f0f0f0'; ctx.fillRect(x,y,wl,h);
  const wf = Math.round(w*Math.max(0,frac));
  ctx.fillStyle=c2; ctx.fillRect(x,y,wf,h);
  ctx.fillStyle=c1; ctx.fillRect(x,y,wf,Math.ceil(h/2));
  // segment ticks
  ctx.fillStyle='#0a0810';
  for(let i=0;i<w;i+=10) ctx.fillRect(x+i,y,1,h);
}
```

Hmm, if the boss bar should deplete from the right... Actually with fillRect anchored left, it depletes from the right which is standard for boss bars too (in reverse). Eh, fine. Let's keep it simple.

Actually for a boss bar on the right side, it's often anchored right so it depletes toward the right. Let's keep it anchored left for both. Simple.

Hmm, the tick marks over the white lag bar... order: bg, lag (white), fill, ticks. Actually ticks shouldn't cover the fill. Let's draw ticks before the fill. Let me reorder: bg, ticks, lag, fill.

Whatever, minor.

**Victory screen**:
```js
function drawVictory(){
  ctx.fillStyle='rgba(0,0,0,'+Math.min(0.75, victoryT/40)+')';
  ctx.fillRect(0,0,W,H);
  const scale = 3;
  const s = 'VICTORY';
  const w = s.length*6*scale - scale;
  drawText(s, Math.round((W-w)/2), 60, '#ffd24a', scale);
  // shadow
  drawText('BOSS DEFEATED', Math.round((W-13*6+1)/2), 100, '#e0e0e0', 1);
  if(Math.floor(victoryT/20)%2===0) drawText('DEMO LOOPS', Math.round((W-10*6+1)/2), 120, '#808090', 1);
}
```

Hmm, "BOSS DEFEATED" is 13 chars → 13*6-1 = 77px wide. Centered at (320-77)/2 = 121.

Let's also add a text shadow for the big text: draw it offset by 2 in dark first.

OK.

Now, the **main loop** with fixed timestep.

```js
let lastTime=0, acc=0;
function loop(ts){
  requestAnimationFrame(loop);
  if(!lastTime) lastTime=ts;
  let dt = ts-lastTime; lastTime=ts;
  if(dt>100) dt=100;
  acc += dt;
  while(acc >= 1000/60){ update(); acc -= 1000/60; }
  render();
}
```

Good.

Let me also handle the manual input.

```js
const keys={};
addEventListener('keydown', e=>{ 
  keys[e.code]=true;
  if(e.code==='KeyP'){ autoplay=!autoplay; }
  if(['ArrowLeft','ArrowRight','ArrowUp','Space','KeyA','KeyD','KeyW'].includes(e.code)) e.preventDefault();
});
addEventListener('keyup', e=>{ keys[e.code]=false; });
```

readInput:
```js
function readInput(){
  const h=hero;
  h.aiMove = (keys['ArrowRight']||keys['KeyD']?1:0) - (keys['ArrowLeft']||keys['KeyA']?1:0);
  h.aiJump = !!(keys['ArrowUp']||keys['KeyW']||keys['Space']);
  h.aiAttack = !!(keys['KeyJ']||keys['KeyK']||keys['KeyZ']||keys['Space']);
}
```

Hmm, Space for both jump and attack is bad. Let's use: Arrows = move, Z/Space = jump, X/J = attack.

OK.

Now let's write the hero AI properly.

```js
function heroAI(){
  const h=hero;
  h.aiMove=0; h.aiJump=false; h.aiAttack=false;
  
  let threat = false;
  
  // 1. Beam warning
  if(beam.warn){
    if(Math.abs(h.x - beam.x) < 28){
      h.aiMove = (h.x < beam.x) ? -1 : 1;
      h.x + h.aiMove*30 > 214 ? h.aiMove=-1 : 0;
      threat = true;
    }
  }
  
  // 2. Ground waves
  if(!threat){
    for(const w of waves){
      const dist = Math.abs(w.x - h.x);
      const incoming = (w.dir<0 && w.x > h.x) || (w.dir>0 && w.x < h.x);
      if(incoming && dist < 44){
        h.aiJump = true;
        threat = true;
        break;
      }
    }
  }
  
  // 3. Orbs
  if(!threat){
    for(const o of orbs){
      const dx = o.x - h.x;
      const incoming = (o.vx<0 && dx>0) || (o.vx>0 && dx<0);
      if(incoming && Math.abs(dx) < 78){
        // move away from projectile path
        h.aiMove = (o.vx<0) ? 1 : -1;  // hmm
        threat = true;
        break;
      }
    }
  }
```

Wait: if the orb travels left (vx<0) and is to the right of the hero, moving right (toward the orb) is bad. We want to move perpendicular... but in a 2D side view with only horizontal movement, the only way to dodge a horizontally-traveling orb is to jump over it or duck under... 

Hmm! Important: if the orb travels horizontally at chest height, the hero can't dodge it by moving horizontally — the orb will catch up or the hero runs into it.

BUT: the orbs are aimed (they have vy) and they travel in an arc. They're fired at the boss's position toward the hero's position at fire time. So if the hero moves, the orb lands where the hero was. So moving DOES dodge it — because the orb travels in a straight line (with slight gravity) toward a fixed point. If the hero moves off that line, the orb misses.

So the orb's trajectory passes through the hero's old position and continues. If the hero moves perpendicular (horizontally), the orb continues past. Yes, that works because the orb's velocity has both vx and vy.

So: the hero just needs to not be at the orb's arrival point. Moving is enough. And jumping helps too.

Given the orb has gravity applied, its path curves — it'll land on the floor. Let me not apply gravity, keep them straight-line so they're predictable, and remove them when they leave the screen or hit the floor.

Actually with vy aiming downward toward the hero at floor level, the orb will hit the floor near the hero's old position. So the hero should move away from that point.

For the AI, let's compute the orb's predicted impact x on the floor and move away from it.

Simpler: if an orb is incoming and close, move in the direction that increases the distance from the orb's path. Let's approximate: compute the orb's predicted y when it reaches the hero's x. If it's within the hero's body, then the hero is in danger → move perpendicular.

Honestly, moving away from the boss (left) is generally fine since the orbs are aimed at the hero's start position and the hero will have moved.

But if the hero is at the wall... Let's make the AI: if an orb is incoming within 80px, move left (retreat) unless x < 90, in which case move right.

And add a check: if the hero is at x>190 and orbs are incoming, retreat.

Hmm, but the hero also wants to attack. Let's do: retreat when orb threat, then approach when clear. Nice rhythm.

Actually wait: if the hero retreats to the left wall every time orbs come, and orbs come every ~2s, the hero spends a lot of time running. That's fine and looks dynamic.

Let's tune the retreat: move left only while the orb is within ~100px and incoming. Then the hero returns.

Let me instead compute the danger more precisely:

```js
for(const o of orbs){
  // predict where orb will be
  const tImpact = (FLOOR - o.y) / (o.vy || -0.001);
  ...
}
```

Simpler: project the orb forward 30 frames and check if it comes within 14px of the hero's current position (with the hero standing still).

```js
let dangerX = null;
for(const o of orbs){
  for(let t=0;t<40;t+=4){
    const px = o.x + o.vx*t, py = o.y + o.vy*t;
    if(Math.abs(px - h.x) < 16 && py > FLOOR-22 && py < FLOOR+4){
      dangerX = px; break;
    }
  }
  if(dangerX!==null) break;
}
if(dangerX!==null){
  h.aiMove = (dangerX > h.x) ? -1 : 1;   // move away from where it'll be
  if(h.aiMove>0 && h.x>200) h.aiMove=-1;
  if(h.aiMove<0 && h.x<70) h.aiMove=1;
  threat=true;
}
```

Hmm, but the orb is heading toward the hero; moving "away" means moving in the direction that the orb is heading, i.e., if the orb is to the right and moving left, running left keeps you ahead of it. Since the orb travels at ~2.5px/frame and the hero at 1.8, the orb catches up. Not good.

Better: run TOWARD the orb's origin, passing it before it arrives? Risky.

Best: JUMP over it. If the orb is at chest height, jumping... the orb is at chest height (y ~ FLOOR-25), and the hero jumping goes up 24px, so the hero's head goes to FLOOR-44. The orb at FLOOR-25 would still hit the hero's legs at apex... Hmm.

OK, let's rethink. Since the orbs are aimed at the hero's position at fire time, the correct dodge is to MOVE AWAY from the aim point (which is where the hero was standing). Since the orb was aimed at the hero's old position and the hero has moved, the orb will pass through the old position. So the hero should keep moving.

So the AI should just keep moving in one direction while orbs are in flight. Since the orbs are aimed where the hero was, and the hero keeps moving, the orbs miss.

So: if orbs incoming, move left (or a consistent direction) and keep moving. That's what I said. The problem is being cornered at the left wall.

Solution: make the arena wide enough / make the orbs fly past. Orb speed 2.6, hero speed 1.8. Distance 100px → orb catches up in 125 frames. The hero moves 225px in that time. So the hero can outrun it if there's room... no, the orb travels 325px. So the hero would need 225px of room. From x=200 that's x=-25. Not enough.

Hmm. But actually, the orb will hit the floor first! Let's give the orbs a downward vy so they hit the floor within ~60 frames.

If the orb is fired from the boss's hands at y ≈ 100, and the hero is at y=150 (feet), the orb needs to travel down 50px. If vy = 1.0, that takes 50 frames, and in that time it travels vx*distance. Hmm.

Let's aim the orbs so they hit the floor at the hero's position: given the horizontal distance D and Δy, choose the flight time Tf = 40 frames, then vx = D/Tf, vy = Δy/Tf.

Then the orbs always land on the floor at the hero's old position. If the hero moves 1.8*40 = 72px in that time, he dodges easily. 

But 40 frames is quite fast for the orbs (D=100 → vx=2.5). That's fine.

Actually, let's make the orbs travel along a line and just remove them when they hit the floor or leave the screen. Good.

So the orb threat is: it will land at the hero's old position. The hero needs to be > 15px away from that point when the orb arrives. Since the hero is constantly moving, fine.

For the AI, I'll do a simplified check: if any orb will pass within 16px of the hero's position in the next 25 frames, move perpendicular to the orb's direction... which is horizontal → move. So:

```js
h.aiMove = (o.vx < 0) ? -1 : 1;  // if the orb moves left, run left (ahead of it)? 
```
Hmm.

Let's think again: the orb moves left toward the hero. The hero at x=180. The orb is aimed at where the hero was, at x=200 (say the hero moved left). If the orb's target is x=200 and the hero is at 180 moving left, the orb lands at 200 → the hero is 20px away → safe.

So the hero just needs to keep moving left. And the AI moving left works.

But if the hero is at the left wall, he can't move further left. Then the orb (aimed at where he was, near the wall) would hit. Unless he moves right, passing under/behind the orb. Since the orb comes down at an angle, moving right toward the orb's origin... the orb is above and to the right, descending. Moving right means moving toward the orb's landing point. Bad.

Hmm. Actually, if the orb lands at x=50 (the hero's old position at the wall), the hero is still at x=50 (can't move left). He should move RIGHT to get away from x=50. Then the orb lands at 50 and the hero is at 70. Safe!

So the rule: move away from the orb's predicted landing point. That's `aimPoint`. The hero knows the aim point is where he was... but the AI can just compute the orb's predicted floor impact x.

```js
const impactX = o.x + o.vx * ((FLOOR+4 - o.y) / o.vy_pos);
```
where o.vy > 0 (moving down). If o.vy <= 0, the orb won't land soon.

Then move away from impactX: `h.aiMove = (h.x < impactX) ? -1 : 1;`

Wait, if the hero is at 50 and the impact is at 50, the sign is ambiguous. Use the direction from impactX to hero.x: move further that way. If they're nearly equal, pick the direction away from the boss (left) unless near the wall.

Let's compute:
```js
const impactX = ...;
h.aiMove = (h.x >= impactX) ? 1 : -1;
```
Hmm, if h.x >= impactX, move right (away from impact). If impactX is where the hero was, and the hero is now to the right of it... then move right. Hmm, but the orb is heading left toward impactX, and the hero is right of impactX, so the orb passes to the left of the hero. The hero is already safe! 

Ugh, this only triggers when the hero is in danger. Let's just do: if the orb's predicted path passes within 16px of the hero, then move away from impactX, clamped to the arena. That works in most cases.

Actually, the simplest robust approach for this game: make the orbs a fan (3 orbs at different angles) aimed at the hero's position, and have the AI JUMP over the low ones and move away for the high ones.

Hmm, I'm overcomplicating. Let me simplify the orb pattern to make dodging easy and readable:

**Orbs travel in a straight line at a fixed height** (no gravity), horizontally from the boss toward the left. Y varies per orb (3 orbs at 3 different heights). The hero must dodge by moving... no, they're horizontal, so moving doesn't help.

OK, alternative classic pattern: **the boss fires orbs in a fan that travel mostly horizontally but with slight vertical spread**, and the hero must jump/duck.

Or: **the orbs fall from above** (like meteors) at the hero's predicted position. Hero moves to dodge. That's very readable and easy for the AI.

Let's do: the boss raises its arms and summons 4-5 orbs that arc up and then rain down (like meteors) at positions near the hero. Hero dodges by moving away. That's a great, clear pattern.

Hmm, but "projectiles" is what's asked. Meteors are projectiles. But let's do a mixed thing: the boss fires a fan of 3 orbs that travel in an arc (parabola) landing at/near the hero's position. The arc makes them look like projectiles.

Implementation: for each orb, given the start (boss hand at bx, by) and the target (hero.x + offset, FLOOR), compute a parabolic path:
- Tf = 55 frames
- vx = (targetX - startX)/Tf
- vy = (targetY - startY)/Tf - 0.5*g*Tf, with g = 0.15

Then integrate: vy += g each frame. The orb arcs up then comes down, landing at the target at Tf.

That's a nice arc! With g=0.15, Tf=55: vy0 = (150-100)/55 - 0.5*0.15*55 = 0.909 - 4.125 = -3.2. So it goes up first. Apex at t = 3.2/0.15 = 21 frames, height 34px above start. Nice arc.

The orb lands at the hero's old position 55 frames later. The hero moves 1.8*55 = 99px. Easy dodge. Good — very dodgeable, and the AI can just keep moving.

But then the orbs are trivially easy. Let's add a second wave of orbs aimed at the predicted new position, or make the boss fire two volleys. Or reduce Tf to 40 and the hero's speed means 72px of movement. Fine.

Let's make the boss fire 5 orbs in a spread across a range of x positions around the hero, so the hero must move out of the danger zone. Spread: offsets -40, -20, 0, +20, +40. The hero needs to be more than ~10px from all impact points → move at least 50px. In 55 frames the hero moves 99px. Easy.

Hmm, or reduce Tf to 45 → 81px. Still easy.

Let's use Tf=50 and spread ±36. The hero needs to move ~46px. 90px available. It's fine — the AI will dodge.

But then it's not visually exciting. Let's add: the orbs also explode on impact creating small AoE. Nah.

Fine, keep it simple. The dodge looks good.

Actually, for extra visual interest, let's have the orbs leave fire trails (particles).

OK.

Now the AI for orbs: predict the impact points. If the hero is within 20px of any impact point, move away from the nearest impact point (or toward the biggest gap). Simple version: compute the average impact x, move away from it.

```js
let sumX=0, n=0;
for(const o of orbs){ if(o.landingX!==undefined){ sumX += o.landingX; n++; } }
if(n>0){
  const avg = sumX/n;
  if(Math.abs(h.x - avg) < 60){
    h.aiMove = (h.x < avg) ? -1 : 1;
  }
}
```

But if the hero is at the wall, that fails. Clamp: if aiMove would push past the wall, flip. Since the arena is 26..214 and the orb spread is ±36 around the hero's position at fire time, the hero might be at 26 and the impacts at 0..62. Then moving left is blocked. Moving right goes into the impacts. Hmm.

But the hero at x=26 — is that likely? The hero's neutral position is ~185 and it retreats to maybe 100. So x=26 is unlikely. Let's just clamp the hero to [30, 214] and have the AI avoid retreating below x=70.

Actually let's simplify: the hero retreats to about x=90-110 when dodging, and attacks from 185-200. So he's rarely at the wall. Good.

Let's set the AI movement:
- If orb threat: move left if x > 110, else move right.

Hmm, that's weird — the orbs land where the hero was. If the hero just keeps moving left, he outruns the impact zone. Since the impacts are centered on his position at fire time, and he's moved 90px left, he's out of the zone.

So: move left (dir = -1) when orbs are incoming, unless x < 100, in which case move right.

Hmm, if x < 100 and the hero moves right, he's moving back toward where he was at fire time, which is where the orbs land. Bad.

Let's just make the hero's minimum x = 70 and always dodge left. If the hero is at x=70 when the orbs are fired, the impacts are at 34..106, and the hero moves left to... 70-90 = -20, clamped at 30. Still inside the impact zone (34..106)! Hmm, 30 < 34, so barely outside. OK, cutting it close.

Let's set the arena min x = 24 and the hero's dodge target = keep moving left. With the impacts at x ∈ [fireX-36, fireX+36], the hero needs |x - impact| > 14 for all. If fireX = 70, impacts 34..106. Hero must be < 20 or > 120. Hero moves left 90px from 70 → -20 → clamped to 24. 24 is inside [34-14, 106+14] = [20,120]. So x=24 is within 10 of impact 34 → hit. 

To avoid this, let's make the hero NOT go below x=110 in normal play. The AI: if orbs are incoming and x < 120, move right instead — but then he runs into the impacts... 

OK, alternative: make the orbs' spread smaller (±24) and the number 3. Then the impacts are within 24 of the fire position. The hero needs to be 15+ away → move 39px. Easy from anywhere.

And set the arena min x = 40. If the hero is at 40 when fired, the impacts are 16..64 (clamped to the arena). The hero moves left to 40-45 = -5 → clamp 40. Stuck. Hmm.

OK, let's just make sure the hero never goes below x=90. Add to the AI: never move left below x=90 unless dodging a beam. And the beam dodge: if the beam locks at x=95, the hero needs to move right (to 95+17=112). Fine.

So: hero x range effectively [90, 214] except for beams. Actually the initial spawn is at x=60, and he runs right immediately. Fine.

Let's set the hero's hard clamp to [30, 214] but have the AI stay in [95, 210].

Impact zone at fireX=95: 71..119. Hero must be < 56 or > 134. Moving left from 95 → 95-90 = 5, clamped to 30. 30 < 56 → safe. 

OK so with the hero at 95 and a full-speed left run, he reaches 30 in ~36 frames, and the orbs land at 50 frames. Safe.

Alright. Let's go with: orb spread ±26 with 3 orbs, Tf = 50, hero speed 1.9.

Hmm, but the hero running left constantly means he has to run back to attack. That's fine, it looks active.

Let me simplify the AI to reduce risk:

```js
// Orb dodge
let orbThreat = false;
for(const o of orbs){
  if(o.landTarget !== undefined && Math.abs(o.landTarget - h.x) < 42 && (o.life > 0)){
    orbThreat = true; break;
  }
}
```
Hmm, o.landTarget is fixed at spawn. Then the hero should move away from it. Since the hero was there... 

Let me just do: when orbs spawn, the AI evaluates: if the hero's x is near the average landing zone, run left (or right if near the left wall).

I'll implement:
```js
if(orbThreat){
  let danger = Math.abs(h.x - orbAvgLand) < 40;
  if(danger){
    h.aiMove = (h.x > 110) ? -1 : 1;
  } else {
    h.aiMove = 0;
  }
}
```

And since the hero moves 90px in 50 frames, and the danger zone is ±40 (80 wide), running left from x>110 escapes. If x <= 110, the landed zone is 84..136 (if fired at 110), and moving left to 30 gives x=30, which is 54 away from 84 → safe.

Wait, if the hero is at x=110 and moves left at 1.9/frame for 50 frames → 95px → x=15, clamped to 30 (min). |30-84| = 54 > 40 → safe. Good.

But if the hero is at x=40 (near the wall) with the zone at 14..66, moving left is blocked. Moving right → into the zone. Hmm.

Let's just enforce that the hero's AI never goes below x=100. Then the danger zone is at worst 74..126, and moving left to 30 is safe. 

So: `h.x = clamp(h.x, 30, 214)` but the AI target min is 100.

Actually the simplest: just make the AI dodge by moving left and clamp the hero at x>=30, and make sure the AI never positions the hero below 100 in normal play. Let's have "approach" logic drive him to 185, and "retreat" to 110 max. Fine.

OK, let's write the AI:

```js
function heroAI(){
  const h = hero;
  h.aiMove = 0; h.aiJump = false; h.aiAttack = false;
  if(h.hurtT > 0) return;

  // ---- 1. Beam ----
  if(beam.warn && Math.abs(h.x - beam.x) < 26){
    h.aiMove = (h.x < beam.x) ? -1 : 1;
    if(h.x + h.aiMove*24 < 40) h.aiMove = 1;
    if(h.x + h.aiMove*24 > 210) h.aiMove = -1;
    return;
  }

  // ---- 2. Shockwaves ----
  for(const w of waves){
    const incoming = (w.dir < 0 && w.x > h.x) || (w.dir > 0 && w.x < h.x);
    const d = Math.abs(w.x - h.x);
    if(incoming && d < 46){
      h.aiJump = true;
      h.aiMove = (w.dir < 0) ? -1 : 1;  // step away while jumping? 
      return;
    }
  }

  // ---- 3. Orbs ----
  let landX = null;
  for(const o of orbs){
    if(o.landX !== undefined){
      if(landX === null || Math.abs(o.landX - h.x) < Math.abs(landX - h.x)) landX = o.landX;
    }
  }
  if(landX !== null && Math.abs(landX - h.x) < 44){
    h.aiMove = (h.x < landX) ? -1 : 1;
    if(h.x + h.aiMove*30 < 95) h.aiMove = 1;
    return;
  }
  ...
}
```

Hmm, `h.aiMove = (h.x < landX) ? -1 : 1` — if the hero is left of the landing point, move further left. If right, move further right. Good, that's "away from the impact".

But if the hero is exactly at landX, it moves right. Which might be toward other impacts. Whatever.

Hmm, but there's an issue: if the hero is at 110 and landX is 100, he moves right (to 140+), then landX is behind him. Fine.

But the "if below 95, move right" override could push him back into the zone. Let's remove the override and just let the clamp handle it. Actually if the hero is at 30 and landX is 40, he moves left → clamped at 30 → gets hit. Hmm.

I'll add: if aiMove is left and x would go below 40, then move right (accepting the risk, but landX is > x so moving right goes toward it... ). 

You know what, I'll just make sure the hero stays above x=95 with the "avoid low x" rule in the neutral behavior, and additionally make the beams and orbs never target x < 80. Since the hero never goes there, it's moot.

Let's just go with it. The probability of the hero being at x<95 when orbs land is low.

Actually, I realize there might be an issue: after dodging left, the hero returns right toward the boss. If the boss fires orbs while the hero is returning, the landX will be near the hero's position, and the hero is moving right → moving right toward landX... but the "away" rule makes him move left again. Fine.

OK, it'll work.

4. Otherwise (no threat):
```js
  // Approach and attack
  const dist = boss.x - h.x;
  if(dist > 52){
    h.aiMove = 1;
  } else if(dist < 40){
    h.aiMove = -1;  // too close
  } else {
    h.aiMove = 0;
    if(h.atkCd <= 0) h.aiAttack = true;
  }
```

Boss.x = 245. dist = 245 - h.x. Attack range: h.x in [185, 214] → dist in [31, 60]. Let's use: if dist > 60 → approach. If dist < 46 → back off. Else attack.

Hmm, but the hero should also attack while approaching if in range. Let's do:
```js
  if(dist > 58) h.aiMove = 1;
  else if(dist < 40) h.aiMove = -1;
  else h.aiMove = 0;
  if(dist < 62 && h.atkCd <= 0 && h.onGround) h.aiAttack = true;
```

With dist < 62 → h.x > 183. Attack tip reach: h.x + 26 vs boss.x ± 34 → 245-34=211. h.x+26 > 211 → h.x > 185. So attack when h.x in [185, 214]. dist = 31..60. So the condition `dist < 62` gives h.x > 183. Slight mismatch but close enough. Let's use `dist < 60` and the hit check with a bit of generosity: `Math.abs(tip - boss.x) < 36`.

At h.x = 186: tip = 212, |212-245| = 33 < 36 ✓.
At h.x = 183: tip = 209, dist 36 → not < 36. Borderline. OK, use range check `h.x > 184`.

Let's use `if(dist < 62) attack` and hit check `Math.abs(tip - boss.x) < 38`. At h.x = 183, tip = 209, |209-245| = 36 < 38 ✓. Good.

Now, there's a subtlety: the hero's approach should stop before colliding with the boss. The boss's left edge is at 245-32 = 213. The hero's clamp is 214. So the hero could overlap the boss. Let's clamp the hero's x to 205 max to avoid overlap. Then dist >= 40.

With h.x in [184, 205], the hero is at the boss's edge. Visually the hero's sword would reach the boss's body. Good.

Set hero clamp: [30, 205].

And approach: if dist > 58 → move right. dist = 245-205 = 40 at the max. So the hero stops at dist=58 → h.x = 187. Good, that's right in the attack range.

And "too close" (dist<40) never happens. Fine, keep the check anyway.

So the hero attacks from x≈187-205. 

Now let's also make the hero bob/fidget. Fine.

**Boss attack timing**: 
- idle duration 55 frames (~0.9s).
- At the start, idleDur = 90 so the hero can approach.

Let's write the boss update:

```js
function updateBoss(){
  const b = boss;
  if(b.flash > 0) b.flash--;
  b.t++;

  switch(b.state){
    case 'idle': {
      b.armOff = Math.sin(T*0.05)*1.5;
      b.rise = 0;
      if(b.t > b.idleDur){
        b.t = 0;
        b.atkIdx = (b.atkIdx + 1) % 3;
        b.state = ['proj','slam','beam'][b.atkIdx];
      }
      break;
    }
    case 'proj': {
      // t 0..34 windup
      if(b.t < 34){
        b.armOff = -Math.min(14, b.t*0.5);
      } else if(b.t === 34){
        fireOrbVolley();
        shake = Math.max(shake, 3);
      } else if(b.t < 80){
        b.armOff = -14 + (b.t-34)*0.4;
      } else {
        b.state='idle'; b.t=0; b.idleDur=50; b.armOff=0;
      }
      break;
    }
    case 'slam': {
      if(b.t < 26){
        b.armOff = -b.t*0.7;
        b.rise = 0;
      } else if(b.t < 46){
        const p = (b.t-26)/20;
        b.rise = Math.sin(p*Math.PI)*26;
        b.armOff = -18;
      } else if(b.t === 46){
        b.rise = 0; b.armOff = 0;
        shake = 14;
        spawnWaves();
        spawnDust(b.x, FLOOR, 24);
      } else if(b.t > 100){
        b.state='idle'; b.t=0; b.idleDur=45;
      }
      break;
    }
    case 'beam': {
      if(b.t < 34){
        b.charge = b.t/34;
        beam.x = hero.x;  // track
        b.armOff = -b.t*0.4;
      } else if(b.t === 34){
        beam.warn = true;
        b.charge = 1;
      } else if(b.t < 70){
        // warning
      } else if(b.t === 70){
        beam.active = true; beam.fire = 0;
      } else if(b.t < 105){
        beam.fire++;
        b.armOff = -14;
      } else if(b.t === 105){
        beam.active = false; beam.warn = false;
      } else if(b.t > 140){
        b.state='idle'; b.t=0; b.idleDur=50; b.armOff=0;
      }
      break;
    }
  }
}
```

Wait, the beam tracks hero.x during t<34 but the hero is moving. Then it locks at t=34. The warning shows from t=34 to t=70 (36 frames = 0.6s). The hero can move 68px. Beam half-width 12 + hero half-width 6 = 18 needed. Plenty.

Good.

But `beam.x = hero.x` — the beam column would move smoothly with the hero, then lock. Nice telegraph.

Total beam cycle: 140 frames = 2.33s + idle 50 = ~3.2s. A bit long. Let's shorten: 
- t<30: track
- t=30: lock+warn
- t=60: fire
- t=100: end fire
- t>125: idle

= 125 + 50 = 175 frames ≈ 2.9s. OK.

Similarly proj: 80 + 50 = 130 ≈ 2.2s.
slam: 100 + 45 = 145 ≈ 2.4s.

Total cycle ≈ 7.5s for all three. With ~14s of fighting, we'd see each attack about twice. Good.

Hmm, that's a bit slow. Let's speed up the idle: 35 frames. Then the cycle is ~6.5s. Good.

Let's also start with idleDur = 80 so the hero has time to approach and get a few hits in.

Now, `b.charge` needs to be initialized. Add it in resetGame.

**fireOrbVolley**:

```js
function fireOrbVolley(){
  const b = boss;
  const sx = b.x - 20, sy = b.y - 52;
  const targets = [-30, 0, 30];
  for(const off of targets){
    const tx = clamp(hero.x + off, 20, 300);
    const ty = FLOOR;
    const Tf = 52;
    const g = 0.16;
    const vx = (tx - sx)/Tf;
    const vy = (ty - sy)/Tf - 0.5*g*Tf;
    orbs.push({x:sx, y:sy, vx, vy, g, life:Tf+14, landX:tx, seed:Math.random()*6});
  }
}
```

Hmm wait, `vy = (ty - sy)/Tf - 0.5*g*Tf`. With g applied as `vy += g` per frame, the position after Tf frames is sy + vy0*Tf + 0.5*g*Tf². Setting that = ty: vy0 = (ty-sy)/Tf - 0.5*g*Tf. ✓.

With sy = 150-52 = 98, ty=150, Tf=52, g=0.16: vy0 = 1 - 0.5*0.16*52 = 1-4.16 = -3.16. Apex at t=19.75, rise = 3.16²/(2*0.16) = 31.2px. So the orb rises to y=67. Nice arc.

Speed vx = (tx - sx)/52. For tx = hero.x + 0 = 185, sx = 225 → vx = -0.77. That's slow. The orb takes 52 frames to cross 40px. Hmm, it'll look slow.

Let's shorten Tf to 38 and g to 0.22:
vy0 = 1 - 0.5*0.22*38 = 1 - 4.18 = -3.18. Apex at 14.5 frames, rise 23px.
vx = -40/38 = -1.05. Still slow.

The issue is the boss is close to the hero. Let's make the orbs faster: Tf = 30, g = 0.3.
vy0 = (52)/30 - 0.5*0.3*30 = 1.73 - 4.5 = -2.77. Apex at 9.2 frames, rise 12.8px. Arc is small.
vx = -40/30 = -1.33. Still slow-ish.

Hmm, the horizontal distance is small because the boss and hero are close. Let's fire the orbs from higher up and further right, and make them travel further.

Actually, let's not aim them at the floor near the hero. Let's make them travel in a long arc: fire them upward and to the left with a fixed speed, and they land wherever they land. Then the "aim" is less precise but the pattern is a spread of projectiles that the hero must dodge.

Better idea: make the projectiles a horizontal fan from the boss's hands that travels left at a good speed, but with vertical spread so the hero can dodge by jumping or ducking... no ducking.

Hmm.

OK here's a cleaner design: **the boss fires a fan of 3-5 orbs that travel left with a slight downward angle and hit the ground**, creating a "bullet hell" spread. The hero dodges by jumping over the low ones and standing between the high ones... but they're in a fan, so different heights at the hero's position.

Given only horizontal movement + jump, the hero can dodge a fan of orbs by:
- Jumping over the ones that are low.
- Standing (not jumping) for the ones that are high (they pass overhead).

So a fan where the orbs arrive at different heights, and the hero just needs to not jump when high orbs come, and jump when low orbs come. That's a real mechanic but tricky for the AI.

Simpler: make one volley of orbs all at the same mid-height, so the hero can jump under/over? If the orbs travel at y = FLOOR-20 (chest height) horizontally, the hero standing (body from FLOOR-18 to FLOOR) would be hit. Jumping lifts the hero above → feet at FLOOR-24 at apex → body from FLOOR-42 to FLOOR-24. The orbs at FLOOR-20 pass below. Yes! Jumping works.

So: orbs travel horizontally-ish at a fixed height band, and the hero jumps to dodge. But the orbs travel at 2.5px/frame and the hero jumps for ~28 frames, so he needs to time it. That's a classic pattern.

Let's do a mix:
- Volley A: 3 orbs at chest height (y ≈ FLOOR-22), horizontally. Hero jumps.
- Volley B (later): orbs that arc and land (meteor style). Hero moves.

Hmm, complexity.

Let's just pick the meteor style but make it dramatic: the boss summons orbs that appear above and rain down. Actually, let's do:

**Pattern "proj"**: The boss fires 4 orbs in a spread. Each orb has a parabolic arc from the boss's hand. But I'll compute the arc so they land across a wide spread around the hero (e.g., ±45). The orbs travel fairly fast.

Honestly, the simplest dodge is moving away, and the AI handles it. Let's just make it look good.

With Tf=45, g=0.25:
vy0 = (150-98)/45 - 0.5*0.25*45 = 1.156 - 5.625 = -4.47. Apex at 17.9 frames, rise 40px. Nice high arc.
vx = (tx - 225)/45. For tx=185: vx = -0.89. Slow horizontal.

The orbs will look like they lob slowly. With a 40px rise and 50px horizontal travel, that's a steep lob. Looks OK actually — like a mortar.

Let's make the boss's hand position further back: sx = b.x + 10 = 255 (right side). Then vx = (185-255)/45 = -1.56. Better.

Hmm, but the boss's hands are at its sides. Whatever, spawn from (b.x, b.y-50).

Let's use sx = b.x - 10 = 235. vx = -1.11.

Meh. Let's just increase the spread and accept. Actually, let's reduce the gravity so the arc is flatter and the orbs are faster:
Tf = 36, g = 0.12:
vy0 = 52/36 - 0.5*0.12*36 = 1.44 - 2.16 = -0.72. Apex at 6 frames, rise 2px. Almost flat.
vx = (185-235)/36 = -1.39.

Still slow.

The real issue: the horizontal distance is only ~50-100px, so any projectile takes a while or is slow.

Let's make the orbs overshoot — they travel past the hero and exit the screen. volley: fire orbs to the left with vy giving a downward angle, so they hit the floor further left.

Let me just make them fast and simple: orbs travel at a fixed speed of 2.2 px/frame in the direction of the hero (normalized), with a spread of ±15°. Then they're fast and the hero dodges by moving. They exit the screen after ~40-100 frames.

```js
const ang = Math.atan2((FLOOR-24) - sy, hero.x - sx);  // toward the hero's chest
for(let i=0;i<3;i++){
  const a = ang + (i-1)*0.18;
  const sp = 2.3;
  orbs.push({x:sx, y:sy, vx:Math.cos(a)*sp, vy:Math.sin(a)*sp, g:0, life:200});
}
```

The orbs travel in straight lines toward the hero's chest at fire time. The hero dodges by moving (they'll pass where he was) or jumping.

Speed 2.3 px/frame = 138 px/s. Crossing 100px takes 43 frames. Good.

And they'll hit the floor and vanish (add a floor check).

For the AI: since the orbs are aimed at where the hero was, the hero just needs to continuously move. The AI: if orbs exist and the hero is in the danger line, move.

Let me compute the AI dodge as: for each orb, project its position forward and see if it comes within 16px of the hero. If yes, move perpendicular — but perpendicular in 2D screen space for a horizontal-ish projectile means vertical (jump). Hmm.

OK: if the orb is low (near the hero's feet), jump. If the orb is at chest/head height, move horizontally (the orb will pass behind).

Actually no. If the orb is aimed at the hero's chest position at fire time, and the hero moves 20px left, the orb passes 20px to the right of the hero. So moving works for any orb aimed at the hero. 

So the AI: if any orb is incoming and within ~80px, move left (or right) consistently. The orbs will all miss since they were aimed at the old position.

But some orbs are spread ±0.18 rad ≈ ±10°, so at 100px distance that's ±18px lateral. The hero moving 40px in 43 frames at 1.9/frame... wait, 43 frames * 1.9 = 82px. Way more than the spread. So he's safe.

Good. So the AI moves and dodges.

But if the hero is at the max x (205) and moves left 82 → 123. Safe. If at 123 and orbs come aimed at 123, he moves to 41. Safe. If at 41... he can't move much further. But the AI keeps the hero at ≥95 normally. So after the previous dodge he's at 123 and then returns right. If orbs come when he's at 100, he moves to 30 (clamped). The impact zone is ±18 around 100 = 82..118. x=30 is safe.

Great. So always dodge left. And clamp min x to 30.

But then the hero drifts left over time. He returns right after the threat. Fine.

Actually, to make it more natural: dodge in the direction that has more room. If x > 160, dodge left; else dodge right. Hmm, but dodging right when the orbs are aimed at x=100 means moving to 182 — the impact zone is 82..118, so 182 is safe. Yes! Both directions work as long as he moves far enough. Moving right from 100 for 43 frames = +82 → 182. Safe.

So: dodge in the direction with more room. If x < 160, move right; else move left. 

But moving right goes toward the boss, which could be dangerous if the boss is attacking with something else. It's fine.

Hmm, but if the hero is at 190 and orbs are aimed at him, he moves left to 108. Fine.

Let's use: `h.aiMove = (h.x < 150) ? 1 : -1;` when orbs are incoming.

Wait, but the hero at 190 moving left to 108 while the boss is at 245 — he'd be far from the boss. Then he approaches again. Fine.

Hmm, but there's a subtlety: orbs fly from the boss toward the hero's position. If the hero moves RIGHT (toward the boss), he moves INTO the orb's path since the orbs travel leftward from the boss. He'd be moving upstream. Let's check: the orb at fire time is at (235, 98) heading toward (190, 126) [hero chest]. The hero moves right to 232. The orb travels left; at x=232 it's near its start. The hero at 232... the orb passes through x=232 at t≈1.3 frames at y≈98. The hero's body at 232 spans y 132..150. So the orb at y=98 passes above. Safe.

But as the orb continues, it descends. At x=210, t=11 frames, y = 98 + 11*vy. vy = (126-98)/|...|... Let's compute: direction from (235,98) to (190,126): dx=-45, dy=28, length 52.9. Normalized: (-0.85, 0.53). Speed 2.3 → vx=-1.96, vy=1.22. The orb hits the floor (y=150) at t = (150-98)/1.22 = 42.6 frames, at x = 235 - 83.5 = 151.5.

So the orb lands at x≈152 on the floor. If the hero is moving right and is at x=180 when the orb is at y=150... wait, the orb is at y=150 only at x=151.

At x=180, t = (235-180)/1.96 = 28 frames, y = 98 + 28*1.22 = 132. The hero's body spans 132..150 at x=180. So the orb at (180, 132) hits the hero's head! 

So if the hero moves right into the orb's path, he gets hit. So dodging toward the boss is bad.

Therefore: always dodge AWAY from the boss (left). And ensure there's room. Let's clamp the hero to x >= 40 and have the AI return to the right after.

Hmm, but then if the hero is at x=45 and orbs come aimed at 45, the orb lands at x ≈ 45-... let's see: the orb travels from (235,98) toward (45,126). dx=-190, dy=28, len=192. Normalized (-0.989, 0.146). Speed 2.3 → vx=-2.27, vy=0.335. The orb hits the floor at t = 52/0.335 = 155 frames, x = 235 - 352 = -117. It exits the screen left at x=0 at t=103 frames, y = 98+34 = 132.

So the orb passes through x=45 at t = (235-45)/2.27 = 84 frames, y = 98+28 = 126. The hero's body at 45 spans 132..150. The orb at y=126 passes just above the hero's head! Close call.

Hmm, so at long range the orbs fly nearly horizontally and pass over the hero's head. That means the hero doesn't even need to dodge at long range.

OK whatever. The pattern works at close range. Let's just also add a slight downward aim to the hero's feet? No, chest is fine.

Given the hero is usually at x≈190, the orbs are aimed at (190, 126) from (235, 98) and land at x=152 after 42 frames. The hero dodging left from 190 to 190-80 = 110 in 42 frames. The orb lands at 152. The hero at 110 is safe. And if the hero moves right into the orb's path... he'd be hit. So dodge left. Good.

Great, so: dodge left. And keep the hero's x ≥ 40.

Alright, let's set the hero's clamp to [40, 205].

And the AI's neutral position is 187-205. Dodging goes left.

If the hero is at 100 and orbs come, he moves to 40 — the impact zone is around 152 (since the orbs are aimed at his chest at 100... wait, the orb spawns from (235,98) and aims at (100,126)). dx = -135, dy = 28, len 138. (-0.978, 0.203). Speed 2.3 → vx = -2.25, vy = 0.467. Hits the floor at t = 52/0.467 = 111 frames, at x = 235 - 250 = -15.

At x=40 (hero's new position), t = (235-40)/2.25 = 87 frames, y = 98 + 40 = 138. The hero's body 132..150 → hit!

Hmm. So moving left from 100 to 40 doesn't dodge because the orb travels nearly horizontally.

Ugh. The problem: at longer ranges, the orbs are nearly horizontal, so horizontal movement doesn't dodge.

Solution: aim the orbs with a fixed downward angle regardless of range, OR make the hero dodge by JUMPING.

Actually, jumping dodges horizontal projectiles! If the orb is at y=138 (chest), the hero jumping lifts his feet to 150-24=126 and his head to 108. The orb at y=138 passes below. Safe!

So: jump to dodge orbs. That's the classic.

So the AI: when orbs are incoming and close, jump. 

Let's verify: the orb approaches at vy≈0.5, slow. The hero jumps: vy jumps -4.0, gravity 0.26 → apex 24px above in ~15 frames, and he's airborne for ~30 frames.

The orb at chest height y≈130-140 needs the hero to be above it. The hero's feet at 126 at apex. The orb at 138 passes below the hero's feet. 

But if the orb is higher (y=120), the hero's body at apex spans 102..126 → still hit.

Hmm. So the jump only works for low orbs.

OK. Let's make the orbs travel at a fixed low height (y around FLOOR-16 to FLOOR-24) and rely on jumps. The hero's jump clears them.

With the orb's y ≈ 134 (FLOOR-16), the hero jumping gets his feet to 126 → safe.

But the orbs are aimed at the hero's chest which is at y≈138 when standing (chest at FLOOR-12?). Let me define the hero's body: y-18 to y → 132..150. The center is 141.

If the orbs travel at y=135 constant (horizontal), the hero standing is hit (132..150 includes 135). Jumping: feet at 126 → body 108..126, doesn't include 135. Safe. 

So: make the orbs travel HORIZONTALLY at a fixed height (with a slight variation for a fan feel), and the hero jumps over them. That's super readable and easy for the AI: jump when an orb is within ~40px.

The fan: 3 orbs at heights 128, 136, 144? If the hero jumps, his body is 108..126 at apex, so all three (128,136,144) pass below. 

But at the start of the jump (feet at 145), he'd still be hit by the 144 orb. So the timing matters: he must be near the apex when the orb arrives. Airborne for 30 frames, apex at 15. The AI should jump when the orb is ~15 frames away. With the orb at 2.5px/frame, that's 37px.

OK, that works. Let's do it.

Actually, hmm: the orbs need to be dodgeable by jumping for their entire travel. If the hero jumps too early or too late, he gets hit. That's fine — that's gameplay.

But for autoplay reliability, let's make the orbs' vertical band narrow (y = 132..140, i.e., 8px tall) so a well-timed jump clears them.

Let's set the orbs at y ≈ FLOOR-14 = 136, half-height 5 → 131..141. The hero's feet must be above 131 → the hero's y < 131. The hero at apex has y = 126. So he's clear for a decent window around the apex.

Airborne from y=150 to y=126 and back, taking 30 frames. Above y=131 (i.e., y<131) from... y(t) = 150 - 4t + 0.13t². y=131 → 4t - 0.13t² = 19 → t = 15 ± sqrt(225 - 19/0.13)... let me just say the hero is above y=131 for about 16 frames around the apex. So the jump timing window is ~16 frames. With the orb at 2.5px/frame, that's a 40px window. The AI should jump when the orb is 30-40px away. Doable.

Let's make it a bit more forgiving: orb y band 131..141 (10px). Hero apex y=126. Fine.

Alright! Let's go with horizontal orbs.

Actually, let's make them travel horizontally but with a slight vertical wave (sinusoidal) for visual interest. No — keep them straight so the collision is predictable.

Final design:
- Boss fires 3 orbs from its hands at y = FLOOR-14 (136), traveling left at 2.4 px/frame, at slightly different heights (133, 136, 139) so they look like a fan. Actually, a fan should diverge vertically. Let's do heights 130, 136, 142 and slight vy of 0. Hmm, then they're parallel.

Let's give them a small vertical spread: vy of -0.15, 0, +0.15. Over 40 frames that's ±6px. Fine.

Spawn with a delay between orbs (e.g., 6 frames apart) so it's a stream.

Actually, let's do two waves: fire 3 orbs, wait 20 frames, fire 3 more. Nice.

Simpler: fire 3 orbs at t=34, then 3 more at t=52.

The AI: jump when the nearest incoming orb is within 34-42px and the hero is on the ground.

Let's give the AI a predicted jump: compute the time until the orb reaches the hero and jump when it's ~14 frames.

```js
for(const o of orbs){
  if(o.vx < 0 && o.x > h.x){
    const tta = (o.x - h.x) / (-o.vx);
    if(tta < 15 && tta > 0){ h.aiJump = true; break; }
  }
}
```

With vx = -2.4 and tta<15, the orb is within 36px. Good.

The hero's apex at 15 frames. 

But if the hero jumps and the orb is at y=136 with the hero's feet at 150-... at t=15 the feet are at 126. The orb at 136 → below the feet. Clear. At t=10, the feet are at 150-40+13 = 123. Already high. Good.

Hmm, actually at t=10: y = 150 - 4*10 + 0.13*100 = 150-40+13 = 123. So the hero is above 131 from about t=6 onward. Great, a wide window.

So jumping when tta < 15 works, and even tta<20.

Let's use tta < 18 and tta > 0.

Also, if the hero is in the air already, no jump.

Now the orb's y should be such that a standing hero is hit: the hero's body 132..150. The orb at 136 → hit. ✓.

And the hero's jump: apex feet at ~123.

Wait, let me recompute: vy0 = -4.0, g = 0.26. Apex height = 16/0.52 = 30.8px. Feet at 119. Even better.

Airtime = 2*4/0.26 = 30.8 frames.

Great.

Now, if the hero jumps at tta=15 and the orb arrives at tta=0 (15 frames later), the hero's feet are at 119 and he's descending... at t=15, y = 150-60+29 = 119. Yes, at the apex.

Perfect.

OK, let's finalize.

Oh wait, one more thing: the orbs are spawned at the boss's hands (x ≈ 235, y=136?). The boss's hands are at y ≈ FLOOR-64+50 = 136. Nice coincidence! So they spawn at hand height and travel horizontally.

Actually the boss's hands at dy 44..60 with y=150 → 150-64+44 = 130 to 150-64+60=146. Center 138. 

So the orbs spawn at (b.x - 24, 136) and travel left. 

Now, the beam pattern also needs to be dodgeable — the hero runs out of the column. Good.

And the slam's shockwaves — the hero jumps. The wave is 15px tall, and the hero's jump apex is 30px. Good.

Hmm, but if the hero is jumping over the wave and an orb arrives... unlikely to coincide.

Alright, let's write everything.

One more consideration: the hero's attack while the boss is doing a slam — the boss rises, so the sword might miss. The hit check uses boss.y which doesn't change (only rise changes). Fine, we check against the base x/y.

Let's finalize the code and write it out.

Let me also add a subtle "hitstop" when the boss is hit (freeze for 2 frames)? Skip.

Let me write the final code.

Also: I should double check the `drawText` function's centering and the font definitions.

Let me now write out everything carefully.

```js
const FONT = {
  'A':['01110','10001','10001','11111','10001','10001','10001'],
  'B':['11110','10001','10001','11110','10001','10001','11110'],
  'C':['01110','10001','10000','10000','10000','10001','01110'],
  'D':['11110','10001','10001','10001','10001','10001','11110'],
  'E':['11111','10000','10000','11110','10000','10000','11111'],
  'F':['11111','10000','10000','11110','10000','10000','10000'],
  'G':['01110','10001','10000','10111','10001','10001','01111'],
  'H':['10001','10001','10001','11111','10001','10001','10001'],
  'I':['11111','00100','00100','00100','00100','00100','11111'],
  'J':['00111','00010','00010','00010','00010','10010','01100'],
  'K':['10001','10010','10100','11000','10100','10010','10001'],
  'L':['10000','10000','10000','10000','10000','10000','11111'],
  'M':['10001','11011','10101','10101','10001','10001','10001'],
  'N':['10001','11001','10101','10011','10001','10001','10001'],
  'O':['01110','10001','10001','10001','10001','10001','01110'],
  'P':['11110','10001','10001','11110','10000','10000','10000'],
  'Q':['01110','10001','10001','10001','10101','10010','01101'],
  'R':['11110','10001','10001','11110','10100','10010','10001'],
  'S':['01111','10000','10000','01110','00001','00001','11110'],
  'T':['11111','00100','00100','00100','00100','00100','00100'],
  'U':['10001','10001','10001','10001','10001','10001','01110'],
  'V':['10001','10001','10001','10001','10001','01010','00100'],
  'W':['10001','10001','10001','10101','10101','11011','10001'],
  'X':['10001','10001','01010','00100','01010','10001','10001'],
  'Y':['10001','10001','01010','00100','00100','00100','00100'],
  'Z':['11111','00001','00010','00100','01000','10000','11111'],
  '0':['01110','10001','10011','10101','11001','10001','01110'],
  '1':['00100','01100','00100','00100','00100','00100','01110'],
  '2':['01110','10001','00001','00110','01000','10000','11111'],
  '3':['11111','00010','00100','00010','00001','10001','01110'],
  '4':['00010','00110','01010','10010','11111','00010','00010'],
  '5':['11111','10000','11110','00001','00001','10001','01110'],
  '6':['00110','01000','10000','11110','10001','10001','01110'],
  '7':['11111','00001','00010','00100','01000','01000','01000'],
  '8':['01110','10001','10001','01110','10001','10001','01110'],
  '9':['01110','10001','10001','01111','00001','00010','01100'],
  ' ':['00000','00000','00000','00000','00000','00000','00000'],
  ':':['00000','00100','00100','00000','00100','00100','00000'],
  '-':['00000','00000','00000','11111','00000','00000','00000'],
  '.':['00000','00000','00000','00000','00000','00000','00100'],
  '!':['00100','00100','00100','00100','00100','00000','00100'],
  '/':['00001','00010','00010','00100','01000','01000','10000'],
  '[':['01110','01000','01000','01000','01000','01000','01110'],
  ']':['01110','00010','00010','00010','00010','00010','01110'],
};
```

OK.

Now writing the whole file. Let me be careful and complete.

Let me reconsider the boss's arm animation offsets once more. The arms are drawn at dy 44+armOff. If armOff = -14, the arms are at dy 30..46 and claws at 43..50. That's raised. Good.

Now let me write.

Also, the boss's `charge` for the beam — draw a glowing orb in the mouth.

Let me write the final code.

For the death sequence, let me spawn particles and also draw expanding rings.

I'll add a `rings` array? Or just particles. Particles are fine.

Let's write it.

Also need to handle: when the boss dies, the orbs/waves/beam should be cleared so the hero doesn't get hit.

In `damageBoss`, if hp <= 0: set gameState='death', clear orbs/waves, beam.active=false, beam.warn=false.

Alright, writing now.

One more: the hero's `hurtT` knockback. When hit, the hero is knocked back and can't act for 14 frames. And invuln for 60 frames.

During invuln, the hero flashes (draw with alternating visibility).

Let's write the render for that: if `h.invuln > 0 && Math.floor(h.invuln/4)%2===0`, skip drawing the hero (or draw with alpha). I'll skip.

Hmm, but then the hero would be invisible half the time for 60 frames. That's 1 second. Standard for action games. Fine, but let's lower the invuln to 45 frames and use the flicker only when invuln < 45.

OK.

Writing the code now for real.

Let me think about the structure of `render()` again, particularly the background and floor.

```js
function render(){
  ctx.setTransform(1,0,0,1,0,0);
  ctx.imageSmoothingEnabled = false;
  ctx.fillStyle = '#07060d';
  ctx.fillRect(0,0,W,H);

  const shx = Math.round((Math.random()-0.5)*shake*2);
  const shy = Math.round((Math.random()-0.5)*shake*2);

  ctx.save();
  ctx.translate(shx, shy);

  // parallax bg
  drawBackground();
  // world
  ctx.save();
  ctx.translate(-Math.round(camX), 0);
  drawWorld();
  ctx.restore();
  // foreground vignette / torch flicker overlay
  ctx.restore();

  drawHUD();
  if(gameState==='victory') drawVictory();
}
```

`drawBackground()` handles its own parallax offsets using camX.

Inside `drawBackground`, the far layer uses `o0 = -camX*0.18`, and the mid uses `o1 = -camX*0.55`.

The torch flames also need to be in the mid layer.

OK.

And `drawWorld()` draws the floor and all entities with `-camX` translate.

Now the floor: drawn at y FLOOR..H. With camX up to 24, the floor shifts up to 24px. So the floor must be drawn from x=-80 to W+80. Since the floor is a full-width rect, that's automatic.

But the parallax background is drawn first; the floor covers y>=150. Good.

Also need to make sure the background wall extends to x=-80..W+80 so no gaps appear when the camera moves. Since I draw a full rect from -80 to W+80, and camX max is 24 → the visible world range is [-24, 344]. Hmm, the background is drawn in screen space with a small offset, so it just needs to cover 0..320 fully. It does.

But the floor is drawn with translate(-camX), so at camX=24 the visible world x is 24..344. The floor spans -80..W+80 = -80..400. Covers it. Good.

And the entities: the boss at 245 with camX=24 → screen 221. Fine.

OK, writing.

Let me make sure the background parallax doesn't leave gaps at the edges. Since the base wall rect covers -80..400 in screen space (a full rect from -80 with width W+160), no gaps.

Let's write the code!

Final check on the hero's attack visual: when `atkT >= 0`, the hero is in the attack state.

Let me write the code.

Actually one thing: `h.runPhase` should increment only when moving.

And `h.anim++` every frame for idle animation.

OK writing.

Let me write out the complete file now.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DUNGEON BOSS — 16-bit Demo</title>
<style>
  html,body{margin:0;padding:0;height:100%;background:#05040a;overflow:hidden;}
  body{display:flex;align-items:center;justify-content:center;}
  canvas{
    image-rendering:pixelated;
    image-rendering:-moz-crisp-edges;
    image-rendering:crisp-edges;
    display:block;
    box-shadow:0 0 40px rgba(120,60,200,0.25);
  }
</style>
</head>
<body>
<canvas id="c" width="320" height="180"></canvas>
<script>
(function(){
"use strict";
...
})();
</script>
</body>
</html>
```

Let me write the JS body.

I'll write it all out now, carefully.

For `spawnDust(x, y, n)` and `spawnHitSparks(x, y, col)`.

```js
function spawnParticle(x,y,vx,vy,life,col,size,grav){
  parts.push({x,y,vx,vy,life,max:life,col,size,grav:grav||0});
}
```

Let's write helpers:

```js
function dust(x,y,n){
  for(let i=0;i<n;i++){
    parts.push({x:x+ (Math.random()-0.5)*20, y:y-Math.random()*4, vx:(Math.random()-0.5)*2.2, vy:-Math.random()*1.6, life:18+Math.random()*18, max:36, col:'#6b5a7d', size:1+(Math.random()*2|0), grav:0.06});
  }
}
function sparks(x,y,n,col){
  for(let i=0;i<n;i++){
    const a = Math.random()*Math.PI*2;
    const s = 1+Math.random()*2.6;
    parts.push({x,y,vx:Math.cos(a)*s, vy:Math.sin(a)*s-0.8, life:14+Math.random()*16, max:30, col: col || (Math.random()<0.5?'#ffd24a':'#ff7a2a'), size:1+(Math.random()*2|0), grav:0.12});
  }
}
```

Particle update:
```js
for(let i=parts.length-1;i>=0;i--){
  const p=parts[i];
  p.x+=p.vx; p.y+=p.vy; p.vy+=p.grav; p.vx*=0.98;
  p.life--;
  if(p.life<=0) parts.splice(i,1);
}
```

Cap the particle count at ~600.

OK. Writing everything now.

For the victory screen, let's also show the elapsed time. Eh, skip. Show "VICTORY" and "BOSS DEFEATED".

Let me write.

Actually, I realize I should double-check the `P` helper in drawBoss with `flash`. The closure captures `flash` — fine.

Let me write the whole thing.

Also: `b.rise` should only be applied during the slam. And the shadow should stay on the ground.

OK. Writing the final answer now.

Let me write drawBoss in full:

```js
function drawBoss(){
  const b = boss;
  if(b.hp<=0 && gameState!=='death') return;
  const dying = gameState==='death';
  if(dying && Math.floor(gsT/4)%2===1 && gsT>30) return;

  const flash = b.flash>0 && (Math.floor(b.flash/2)%2===0);
  const C = c => flash ? '#ffffff' : c;
  const X = Math.round(b.x - 32);
  const Y = Math.round(b.y - 64 - b.rise);
  const P = (dx,dy,w,h,c)=>{ ctx.fillStyle=C(c); ctx.fillRect(X+dx, Y+dy, w, h); };
  const ao = Math.round(b.armOff);

  // horns
  P(14,10,9,9,'#cfc6a6');
  P(10,5,8,8,'#ddd5b6');
  P(7,1,6,6,'#eee7c8');
  P(41,10,9,9,'#cfc6a6');
  P(46,5,8,8,'#ddd5b6');
  P(51,1,6,6,'#eee7c8');
  // legs
  P(17,52,13,12,'#472162');
  P(34,52,13,12,'#472162');
  P(15,60,16,4,'#331545');
  P(33,60,16,4,'#331545');
  // torso
  P(16,32,32,22,'#6a3a86');
  P(16,32,32,5,'#7d4a9c');
  P(21,38,22,14,'#8a5aa6');
  P(26,41,12,9,'#b06ac8');
  P(28,43,8,5,'#e0a8f0');
  // shoulders
  P(8,30,14,14,'#5a2f74');  P(8,30,14,4,'#7d4a9c');
  P(42,30,14,14,'#5a2f74'); P(42,30,14,4,'#7d4a9c');
  // arms
  P(5,44+ao,11,17,'#5a2f74');
  P(48,44+ao,11,17,'#5a2f74');
  P(3,58+ao,10,7,'#7d4a9c');
  P(51,58+ao,10,7,'#7d4a9c');
  // neck
  P(26,26,12,10,'#4a2660');
  // head
  P(20,8,24,22,'#6a3a86');
  P(20,8,24,5,'#7d4a9c');
  P(18,14,4,14,'#5a2f74');
  P(42,14,4,14,'#5a2f74');
  // eyes
  const gl = 0.6+0.4*Math.sin(T*0.15);
  P(23,16,8,6, gl>0.7?'#ff6a2a':'#ff3a1a');
  P(33,16,8,6, gl>0.7?'#ff6a2a':'#ff3a1a');
  P(25,17,4,4,'#ffe08a');
  P(35,17,4,4,'#ffe08a');
  // mouth
  P(26,24,12,5,'#180a22');
  P(27,24,2,2,'#eee7c8'); P(31,24,2,2,'#eee7c8'); P(35,24,2,2,'#eee7c8');
  ...
}
```

Hmm the eyes at dx 23..31 and 33..41 — the head is 20..44. The gap between the eyes at 31..33 is 2px. That's small. Let's make the eyes 23..29 and 35..41. 

And the mouth at 26..38, dy 24..29.

OK. Also for the beam charge, add a glow at the mouth:
```js
  if(b.state==='beam' && b.charge>0 && beam.warn && !beam.active){
    const g = Math.round(b.charge*7);
    P(32-g, 24-g*0.4, g*2, Math.round(4+g*0.8), '#ffd24a');
  }
```
Hmm messy. Let's just draw a bright rect at the mouth that pulses.

And for proj, an orb charging between the hands:
```js
  if(b.state==='proj' && b.t<34){
    const r = Math.round(3 + b.t*0.25);
    ctx.fillStyle = '#ffb020';
    ctx.fillRect(X+32-r, Y+30-r, r*2, r*2);
    ctx.fillStyle = '#fff4c0';
    ctx.fillRect(X+32-r/2, Y+30-r/2, r, r);
  }
```
Hmm the hands are at Y+44+ao which during the windup goes to Y+30. So the orb between the hands at Y+30 is right. But the hands are at x 5..16 and 48..59, so the center is 32. Good.

OK.

Now writing the final file. Let me be thorough and produce it.

I need to double check: `P` uses `ctx.fillRect(X+dx, Y+dy, w, h)`. X = b.x - 32. So dx=0 → the boss's left edge. Good.

Let's write it all.

One last thing: the hero's attack should also have a "hit" sound... no sound required.

Writing.

Also, I should verify the `drawText` centering math and that the text doesn't go off-screen.

OK, final write-up.

For the manual-input fallback, `readInput` sets h.aiMove/h.aiJump/h.aiAttack.

Let me finalize `updateHero`:

```js
function updateHero(){
  const h = hero;
  if(h.flash>0) h.flash--;
  if(h.invuln>0) h.invuln--;
  if(h.atkCd>0) h.atkCd--;
  if(h.hurtT>0) h.hurtT--;
  h.anim++;

  if(h.hurtT>0){
    h.x += h.knock;
    h.knock *= 0.86;
    h.state = 'hurt';
  } else if(h.atkT >= 0){
    h.atkT++;
    h.state = 'attack';
    if(h.atkT===7 && !h.hitDone){
      h.hitDone = true;
      const tip = h.x + h.facing*26;
      if(!boss.dead && Math.abs(tip - boss.x) < 38){
        damageBoss(5);
      } else {
        sparks(tip, h.y-14, 4, '#9ad8ff');
      }
    }
    if(h.atkT >= 18){ h.atkT = -1; h.state='idle'; }
  } else {
    if(autoplay) heroAI(); else readInput();
    const mv = h.aiMove|0;
    if(mv !== 0){
      h.x += mv * 1.9;
      h.facing = mv>0?1:-1;
      h.state = 'run';
      h.runPhase += 0.42;
    } else {
      h.state = h.onGround ? 'idle' : 'jump';
    }
    if(h.aiJump && h.onGround){ h.vy = -4.0; h.onGround = false; h.y -= 0.01; }
    if(h.aiAttack && h.atkCd<=0 && h.onGround){ startAttack(); }
  }

  if(!h.onGround){
    h.vy += 0.26;
    h.y += h.vy;
    if(h.y >= FLOOR){
      h.y = FLOOR; h.vy = 0; h.onGround = true;
      dust(h.x, FLOOR, 5);
    }
  }
  h.x = clamp(h.x, 34, 205);
}
```

Hmm, `h.aiJump && h.onGround` — but the jump should also work while running. Yes, it works.

Note: the hero can't move while jumping in this code. Let's allow air control: move even when not on the ground. The code above allows movement regardless of onGround (the movement is in the else branch which runs when not attacking/hurt). Yes, air control works.

Good.

Now `heroAI` sets h.aiMove etc. every frame. And the hero moves.

Alright. Writing the final.

One more: the AI's `h.aiJump` needs to be reset each frame — yes, heroAI sets it.

But heroAI returns early in some branches. Need to make sure h.aiJump is reset at the top. Yes.

Also the orbs' jump check needs `h.onGround`.

OK writing!

For the boss's `t` counter, it increments every frame even in idle. Good.

Let me write the final code.

Actually, I want to double-check the beam dodge for the AI. `beam.warn` is set at t=30 and the beam fires at t=60. So there are 30 frames of warning. The hero needs to move 18px + safety. At 1.9/frame he moves 57px in 30 frames. Good.

But wait: during t<30, `beam.x = hero.x` — the beam tracks the hero. So the hero must stop tracking... no, the beam follows the hero until t=30, then locks. So the hero should keep moving after t=30. The AI sees beam.warn and moves away from beam.x. Since beam.x is locked at the hero's position at t=30, and the hero immediately starts moving away, he escapes in 30 frames. 

Alright, writing!

Let me also make sure that during the beam charge (t<30), the hero isn't standing in the beam — since it tracks, it doesn't matter until it locks.

Final code writing now.

I'll set `boss.idleDur` initial to 90.

Let me write.

Also `b.charge` should reset to 0 when not in the beam state.

Writing now — final.

Regarding performance: particles could number in the hundreds. Fine.

Let me produce the code.