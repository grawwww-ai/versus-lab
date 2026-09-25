Let me build a complete single-file HTML5 tower defense game.

Key requirements:
- Canvas rendering
- Enemies spawn at left edge, follow winding path to base on right
- 8 fixed tower slots along path
- Keys 1-4 buy tower types: cannon, frost, laser, splash
- Placed in next free slot if enough gold
- Towers auto-shoot, enemies have health bars, give gold on kill
- Waves get harder
- Base has HP; game over at 0
- HUD: gold, wave, base HP, score
- Space starts/restarts
- One free cannon at start
- P toggles autoplay demo mode with competent AI
- Everything important visible within first 30 seconds

Let me design.

Canvas size: 960x540 maybe. Let's use a fixed logical size and scale to fit.

Path: winding from left edge to base on right. Define waypoints.

Let's make canvas 960 x 560.

Path waypoints (in canvas coords):
- (-20, 120) start off-screen left
- (140, 120)
- (140, 300)
- (330, 300)
- (330, 130)
- (520, 130)
- (520, 420)
- (700, 420)
- (700, 240)
- (850, 240)  -> base at right around (880, 240)

Hmm, base should be at right edge. Let's put base at (900, 240).

Tower slots: 8 fixed positions along the path, offset from path so they're near but not on it. Let's place them at reasonable spots.

Let me compute path segments and pick slot positions adjacent.

Waypoints:
P0 (-30, 120)
P1 (150, 120)
P2 (150, 310)
P3 (340, 310)
P4 (340, 140)
P5 (530, 140)
P6 (530, 430)
P7 (720, 430)
P8 (720, 250)
P9 (890, 250)

Base at (890, 250) roughly, maybe base drawn at right edge around x=905.

Tower slots — place them near path segments, offset perpendicular by ~45px:
1. (150, 60) — above horizontal segment near P1... Actually let's put near start: (80, 200)? Hmm let's think about coverage.

Let me pick slots:
S1: (75, 200) — near vertical segment x=150, left side. Distance from segment x=150: 75px. Hmm, a bit far. Let's do (85, 215) -> 65px from x=150 line. Fine, tower range ~110-140.

Actually simpler: place slots at fixed coordinates with reasonable spacing.

Path segments:
A: y=120, x from -30 to 150
B: x=150, y from 120 to 310
C: y=310, x from 150 to 340
D: x=340, y from 310 to 140
E: y=140, x from 340 to 530
F: x=530, y from 140 to 430
G: y=430, x from 530 to 720
H: x=720, y from 430 to 250
I: y=250, x from 720 to 890

Slots (offset ~55px from path, in open space):
1. (215, 215) — right of segment B (x=150), and below segment C? Segment C is y=310 at x 150-340; (215,215) is 95 above. OK. Distance to B: 65. Fine.
2. (275, 375) — below segment C (y=310), distance 65.
3. (415, 225) — right of segment D (x=340), distance 75. Hmm maybe 405,225 → 65.
4. (465, 75) — above segment E (y=140), distance 65.
5. (600, 215) — right of segment F (x=530)? distance 70. But also near E y=140 at x up to 530. Fine.
6. (600, 500)? Canvas height 560. Segment G is y=430, x 530-720. Slot below: (615, 500), distance 70. OK.
7. (790, 360) — right of segment H (x=720), distance 70.
8. (790, 165) — above segment I (y=250), distance 85. Hmm. Or (800, 165).

Let's check they don't overlap path. Should be fine.

Actually let me reconsider canvas height 560 and slot 6 at y=500 — ok.

Let me double check slot 5 (600,215): path segment F x=530 y 140-430, distance 70. Segment E y=140 x 340-530: distance from (600,215) to endpoint (530,140) = sqrt(70²+75²)=102. Fine.

Slot 8 (800,165): distance to segment I (y=250) = 85. Distance to segment H (x=720, y 430→250): nearest point (720,250), distance sqrt(80²+85²)=117. Fine. Range 110-140 towers, so it covers y=250 segment partially. Hmm, 85 distance means it can hit enemies on segment I if range >= 85. Yes.

OK.

Now tower types:
- Cannon (key 1): cost 50, moderate damage, moderate fire rate, single target, medium range. 
- Frost (key 2): cost 65, low damage, slows enemies, medium range.
- Laser (key 3): cost 90, continuous beam, dps, long range? Let's make laser: high fire rate, low damage per shot, long range, instant hit.
- Splash (key 4): cost 110, slow fire rate, area damage.

Balance for a good demo.

Let's define:
- cannon: cost 50, range 130, damage 14, cooldown 0.55s, projectile speed 380
- frost: cost 65, range 120, damage 5, cooldown 0.7s, slow 45% for 1.6s, projectile speed 320
- laser: cost 90, range 170, damage 9, cooldown 0.18s, instant beam (hitscan)
- splash: cost 110, range 140, damage 22, splash radius 55, cooldown 1.3s, projectile speed 260

Enemy types: normal, fast, tank, and maybe boss every 5 waves.

Enemy stats scale with wave.

Base HP: 20. Each enemy reaching base deals damage = its damage (1 for normal, 1 fast, 2 tank, 5 boss).

Gold: start with 120 (enough for 1-2 towers). Actually first free cannon given. Start gold 100.

Kill reward: based on enemy.

Waves: wave N has count = 5 + N*2, hp scaling = 20 * (1.18^(N-1))... let's tune.

Actually let's be careful: the game should be winnable-ish / show a good run. Waves get harder indefinitely. Let's have wave-based spawning with increasing HP.

Enemy HP: base 22 * (1.16^(wave-1)) plus flat +6*wave? Let's do hp = Math.round(20 * Math.pow(1.15, wave-1)).

Wave 1: 20 hp. Cannon damage 14 per 0.55s = 25 dps. Fine.

Speed: normal 55 px/s, fast 95, tank 38.

Path length: let's compute roughly. Segment lengths:
A: 180
B: 190
C: 190
D: 170
E: 190
F: 290
G: 190
H: 180
I: 170
Total ≈ 1750 px. At 55 px/s that's ~32 seconds to cross. That's a bit long for a 30-second window. Hmm. Maybe increase speeds: normal 75 px/s → 23s. Still long-ish. But first enemy spawns at start, so within 30s it may not reach base. That's fine — "everything important" = towers shooting, enemies dying, gold, etc.

Let's use speed normal 70, fast 110, tank 48.

Actually for the 30s window, we want to see: enemies spawn, towers shoot, enemies die, gold increases, wave counter. Good.

Let me set wave 1 to spawn 6 enemies over ~1.5s intervals. First wave starts on Space.

Autoplay: AI buys towers with a priority and places them. It should also handle starting waves.

Autoplay behavior:
- On game start (or when P pressed), AI plays.
- AI logic: each tick, if gold >= cost of a desired tower and there's a free slot, buy.
- Priority: build a mix. Start: cannon (free one given). Then save for splash/frost/laser mix.
- AI presses space to start next wave when previous wave cleared or when it has enough towers.

Simplest: AI calls startWave() whenever waveState is 'idle' (between waves) and there are no enemies alive... but actually we want continuous action. Let's have a short break between waves (e.g., 2.5s) then auto-start next wave in demo mode.

Let's design game states:
- 'menu' (before first start)
- 'playing'
- 'gameover'

Wave flow: when wave starts, spawn queue. When all spawned and all enemies dead → wave complete → gold bonus, short pause, then next wave auto-starts (with a countdown) or player presses space to start early.

Actually simpler: after wave cleared, set state 'between' with a timer of 3s, and space skips. In autoplay, AI presses space immediately (or waits a moment).

Hmm, but the requirement says "Space starts or restarts". So space starts the game from menu, restarts from gameover, and starts next wave early during 'between'.

Let me make it: Space:
- menu → start game (wave 1 begins)
- between → immediately start next wave
- gameover → reset to menu / restart

Let's just make gameover → space restarts fully.

Now rendering: nice look. Dark background, path drawn as thick rounded stroke, tower slots as circles, towers as shapes, enemies as circles with health bars, projectiles, particles.

Let's write the code.

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Tower Defense</title>
<style>
  html,body { margin:0; padding:0; background:#0b0f14; height:100%; overflow:hidden; font-family: system-ui, sans-serif;}
  #wrap { position:fixed; inset:0; display:flex; align-items:center; justify-content:center;}
  canvas { background:#111820; box-shadow:0 0 60px rgba(0,0,0,0.8); border-radius:8px; max-width:100%; max-height:100%; }
</style>
</head>
<body>
<div id="wrap"><canvas id="c" width="960" height="560"></canvas></div>
<script>
...
</script>
</body>
</html>
```

Scaling: use CSS max-width/max-height with aspect ratio preserved. Set canvas style width/height via JS on resize for crispness.

Let's do:
```js
function resize(){
  const scale = Math.min(window.innerWidth/W, window.innerHeight/H);
  canvas.style.width = (W*scale)+'px';
  canvas.style.height = (H*scale)+'px';
}
```

Now the code.

Constants:
```js
const W=960, H=560;
const PATH = [ {x:-40,y:120},{x:150,y:120},{x:150,y:310},{x:340,y:310},{x:340,y:140},{x:530,y:140},{x:530,y:430},{x:720,y:430},{x:720,y:250},{x:890,y:250} ];
```

Compute cumulative lengths for enemy positioning.

Enemy: has t (distance along path), position computed by lerping.

Let's precompute segments with start point, dir, length, cumulative.

```js
const segs=[];
let total=0;
for(let i=0;i<PATH.length-1;i++){
  const a=PATH[i], b=PATH[i+1];
  const dx=b.x-a.x, dy=b.y-a.y;
  const len=Math.hypot(dx,dy);
  segs.push({a,b,dx:dx/len,dy:dy/len,len,start:total});
  total+=len;
}
function posAt(d){
  if(d<=0) return {x:PATH[0].x, y:PATH[0].y};
  for(const s of segs){
    if(d <= s.start+s.len){
      const t=d-s.start;
      return {x:s.a.x+s.dx*t, y:s.a.y+s.dy*t};
    }
  }
  const last=segs[segs.length-1];
  return {x:last.b.x, y:last.b.y};
}
```

Base position: end of path (890,250). Draw base there.

Actually the base should be at the right edge; path ends at x=890 which is close to right edge (960). Good.

Tower slots:
```js
const SLOTS=[
 {x:215,y:215},{x:275,y:375},{x:405,y:225},{x:465,y:75},
 {x:600,y:215},{x:615,y:500},{x:790,y:360},{x:800,y:165}
];
```

Hmm slot 8 at (800,165) - is that near path? Segment I y=250 from x720 to 890. Distance 85. And segment H x=720 y 430→250: nearest point (720,250): dist sqrt(80²+85²)=117. OK, range 130+ towers can hit.

Slot 4 (465,75): segment E y=140 x 340-530 → distance 65. Good.

Slot 1 (215,215): segment B x=150 y120-310 → distance 65. Good. Also segment C y=310 x150-340 → distance 95.

Slot 3 (405,225): segment D x=340 y310→140: distance 65. Good.

Slot 7 (790,360): segment H x=720 y430→250: nearest point (720,360) → distance 70. Good.

Slot 6 (615,500): segment G y=430 x530-720 → distance 70. Good.

Slot 2 (275,375): segment C y=310 x150-340 → distance 65. Good.

Slot 5 (600,215): segment F x=530 y140-430 → distance 70. Good.

Great.

Tower types:
```js
const TOWER_TYPES = {
  cannon: {name:'Cannon', key:'1', cost:50, color:'#ffb347', range:135, damage:16, cooldown:0.55, speed:420, kind:'bullet'},
  frost:  {name:'Frost',  key:'2', cost:65, color:'#6fd6ff', range:125, damage:6,  cooldown:0.75, speed:340, kind:'frost'},
  laser:  {name:'Laser',  key:'3', cost:90, color:'#ff5c8a', range:175, damage:11, cooldown:0.2,  kind:'laser'},
  splash: {name:'Splash', key:'4', cost:110,color:'#b07cff', range:145, damage:26, cooldown:1.3,  speed:280, kind:'splash', splashRadius:58},
};
```

Order array: ['cannon','frost','laser','splash'].

Enemy types:
```js
function makeEnemy(type, wave) {
  const hpScale = Math.pow(1.17, wave-1);
  ...
}
```

Let's define:
- grunt: hp 22*scale, speed 68, reward 8, dmg 1, radius 11, color '#7ee081'
- runner: hp 14*scale, speed 112, reward 9, dmg 1, radius 9, color '#ffd166'
- tank: hp 60*scale, speed 46, reward 16, dmg 2, radius 15, color '#ff7b7b'
- boss: hp 260*scale, speed 40, reward 60, dmg 5, radius 20, color '#c084fc'

Wave composition function:
```js
function buildWave(wave){
  const list=[];
  const n = 5 + Math.floor(wave*1.6);
  for(let i=0;i<n;i++){
    let t='grunt';
    if(wave>=2 && i%3===2) t='runner';
    if(wave>=3 && i%5===4) t='tank';
    list.push(t);
  }
  if(wave%5===0){ list.push('boss'); }
  return list;
}
```
Hmm wave 1: n = 5+1 = 6 grunts. Good.

Wave 5: n=5+8=13, plus boss.

Gold reward per kill, plus wave completion bonus = 20 + wave*5.

Starting gold: 100. Free cannon at slot 0.

Hmm, actually maybe start gold 80 so player must earn. Let's do 90.

Economy check: wave 1: 6 grunts × 8 = 48 gold + bonus 25 = 73. Total 163. Enough for a couple towers.

Let's make sure enemies are killable. Wave 1 grunt hp 22. Free cannon: 16 dmg per 0.55s = 29 dps. Range 135 from slot 0 at (215,215) covers segment B (x=150, y 120-310) — distance 65 horizontally, so along that segment, covered y from 215-sqrt(135²-65²)=215-118=97 to 215+118=333. So covers most of segment B (190 long) plus a bit. Time in range ≈ 236px/68 = 3.5s → 100 damage. Plenty for one grunt. But 6 grunts come 1.4s apart... tower kills one every 0.55s*ceil(22/16)=2 shots = 1.1s. Roughly keeps up. Might leak a couple. That's fine — base has 20 HP.

Hmm, but the free cannon alone must handle wave 1 reasonably. Let's check total time: 6 grunts, spawn interval 1.4s → last spawns at 7s. Path length ~1750, speed 68 → 25.7s to traverse. Tower fires for the duration. Actually fine.

But the player also has 90 gold → can buy a cannon (50) immediately. Good.

Let's also consider that towers in slots 0 (215,215) — wait, slot index. The free cannon goes in slot 0.

"Place one free cannon at start so the first wave is playable." Yes.

Now autoplay AI.

AI strategy:
- Maintains a build order: cannon, cannon, frost, cannon, splash, laser, splash, laser... 
- Actually, smarter: pick tower based on gold and needs.

Let's write:
```js
const AI_BUILD_ORDER = ['cannon','frost','cannon','splash','laser','cannon','frost','splash'];
```
But with 8 slots, we want a good mix. Also the free cannon occupies slot 0.

AI logic each frame (throttled):
- If free slot exists and gold >= cost of next desired type → buy.
- Desired type from build order based on number of towers built.
- But also prefer saving for splash if we have lots of cannons.

Simple approach:
```js
function aiUpdate(dt){
  aiTimer -= dt;
  if(aiTimer>0) return;
  aiTimer = 0.35;
  const free = SLOTS.findIndex((s,i)=> !towers[i]);
  if(free>=0){
    // decide what to buy
    const counts = countTowers();
    let want = null;
    // early: cannons
    if(counts.cannon < 2) want='cannon';
    else if(counts.frost < 1) want='frost';
    else if(counts.splash < 2) want='splash';
    else if(counts.laser < 2) want='laser';
    else want = counts.cannon<3 ? 'cannon' : 'laser';
    ...
  }
}
```

Hmm, but we need to also handle that AI shouldn't waste all gold. Let's make it: if gold >= cost, buy. Else wait.

Also AI should start waves. In autoplay, when state is 'between', immediately start next wave after short delay. And when menu, start.

Also AI should maybe hold off starting a wave if it wants to buy a tower first. Let's do: in 'between', AI starts the wave when either it has spent available gold on a tower (can't afford anything useful) or the countdown is nearly done. Simpler: just start immediately — the between time is short anyway. Actually the between time gives gold from wave bonus. Let's have between-time of 4 seconds, and AI uses that to buy towers, then starts wave at ~2s in.

Let's simplify: betweenTimer counts down from 4. AI starts the wave when betweenTimer < 2.5 or when it can't afford any more.

Hmm, simpler still: AI starts next wave as soon as betweenTimer < 2.0. Let's just do that.

Actually even simpler: AI immediately starts wave when in 'between' state after a 1.5s delay. Let's do it via a small delay variable.

Let me structure:

```js
let state = 'menu'; // menu, playing, gameover
let wave = 0;
let gold = 90;
let baseHP = 20, baseMaxHP = 20;
let score = 0;
let enemies = [];
let towers = [null,null,null,null,null,null,null,null];
let projectiles = [];
let particles = [];
let spawnQueue = [];  // {type, time}
let waveTimer = 0;
let betweenTimer = 0;
let spawnTimer = 0;
let autoPlay = false;
let gameTime = 0;
```

Wave flow inside state 'playing':
- If spawnQueue.length > 0: spawnTimer decreases; when <=0, spawn next.
- If spawnQueue empty and enemies empty → wave complete: gold += bonus; score += ...; state stays 'playing' but betweenTimer set → 'between' mode.

Let me add a sub-state: `phase = 'wave' | 'between'`.

OK:

```js
function startGame(){
  reset();
  state='playing';
  startWave(1);
}
```

Hmm, but "Space starts or restarts" — from menu, space starts.

reset():
```js
function reset(){
  wave=0; gold=90; baseHP=20; score=0;
  enemies=[]; projectiles=[]; particles=[];
  towers = new Array(8).fill(null);
  // free cannon
  towers[0] = makeTower('cannon', 0);
  spawnQueue=[]; spawnTimer=0; betweenTimer=0; phase='wave'; gameTime=0;
}
```

Wait — but we want the free cannon placed at start. Yes.

startWave(n):
```js
function startWave(n){
  wave=n;
  const list = buildWave(n);
  spawnQueue = list.map((t,i)=>({type:t, at: i*spawnInterval(n)}));
  spawnTimer = 0;
  phase='wave';
}
```

spawnInterval: max(0.6, 1.5 - wave*0.05). Let's just use 1.3 for simplicity, or decreasing.

Actually let's use per-enemy spacing: 1.4 - min(0.8, wave*0.06).

Let's keep it simple: interval = Math.max(0.55, 1.3 - wave*0.06).

Wave 1: 1.24s. Wave 10: 0.7s.

Spawn logic: use a timer that decrements, and pop from queue.

```js
if(spawnQueue.length){
  spawnTimer -= dt;
  while(spawnQueue.length && spawnTimer<=0){
    spawnEnemy(spawnQueue.shift());
    spawnTimer += spawnInterval;
  }
}
```
Need spawnInterval stored. Let's store in a variable when starting the wave.

Hmm, careful with the while loop and spawnTimer going very negative. Use `spawnTimer += interval` which is fine.

Now, enemies:

```js
function spawnEnemy(type){
  const def = ENEMY_TYPES[type];
  const hp = Math.round(def.hp * Math.pow(1.16, wave-1));
  enemies.push({
    type, hp, maxHp: hp,
    d: -Math.random()*0, // distance along path
    speed: def.speed * (1 + Math.min(0.4, (wave-1)*0.02)),
    reward: def.reward, dmg: def.dmg, radius: def.radius,
    color: def.color, slow: 0, slowFactor: 1, x:0, y:0, dead:false, hitFlash:0
  });
}
```

Speed scaling might make things too fast; let's cap. Actually increasing HP is enough. Keep speed constant per type.

Enemy update:
```js
const sp = e.speed * (e.slow>0 ? e.slowFactor : 1);
e.d += sp*dt;
if(e.slow>0) e.slow -= dt;
const p = posAt(e.d); e.x=p.x; e.y=p.y;
if(e.d >= totalPathLength){ // reached base
  baseHP -= e.dmg; e.dead = true; ... particles
}
```

Actually base is at end of path. Let's check e.d >= total - small. Use total.

Towers:
```js
function makeTower(type, slotIndex){
  const def = TOWER_TYPES[type];
  return {type, def, slot: slotIndex, cd: 0, angle: -Math.PI/2, level:1, recoil:0};
}
```

Tower update:
```js
for each tower:
  t.cd -= dt;
  if(t.recoil>0) t.recoil -= dt*4;
  // find target
  const target = findTarget(t);
  if(target){
    t.angle = Math.atan2(target.y - pos.y, target.x - pos.x);
    if(t.cd <= 0){ fire(t, target); t.cd = t.def.cooldown; }
  }
```

findTarget: nearest enemy within range (or furthest along path — better for TD). Let's use "furthest along path within range" (i.e., max d) so towers prioritize the leading enemy. Actually for splash, targeting the densest cluster is better. Let's keep it simple: furthest along path.

Hmm, actually targeting the furthest along is standard. Let's do that.

But for laser with fast fire, whatever.

fire():
- 'bullet' (cannon): create projectile with speed, damage, target reference? Homing projectiles are nicer. Let's do homing: projectile stores target enemy; moves toward it; on hit, damage.
- 'frost': same but applies slow.
- 'laser': instant hitscan, draw beam for 0.08s, apply damage immediately.
- 'splash': projectile that travels to target's position (predictive or just homing), on impact deals AoE damage.

Let's implement homing projectiles with speed; if target dies, projectile continues toward last known position and expires / or just disappears. Simpler: store target, if target dead, projectile continues to last pos and fizzles.

Let's implement:
```js
function fire(tower, target){
  const p = SLOTS[tower.slot];
  const def = tower.def;
  if(def.kind==='laser'){
    damageEnemy(target, def.damage);
    beams.push({x1:p.x,y1:p.y,x2:target.x,y2:target.y,life:0.09,max:0.09,color:def.color});
    return;
  }
  projectiles.push({
    x:p.x, y:p.y, target, speed:def.speed, damage:def.damage,
    kind:def.kind, color:def.color, radius: def.kind==='splash'?5:3,
    splashRadius: def.splashRadius||0, dead:false, life:2.5
  });
}
```

Projectile update: move toward target position (or last known). If distance < 8 or target dead and reached last pos → hit.

Let's do:
```js
const tx = pr.target && !pr.target.dead ? pr.target.x : pr.tx;
```
Store pr.tx, pr.ty updated each frame when target alive.

```js
if(pr.target && !pr.target.dead){ pr.tx = pr.target.x; pr.ty = pr.target.y; }
const dx = pr.tx - pr.x, dy = pr.ty - pr.y;
const dist = Math.hypot(dx,dy);
const step = pr.speed*dt;
if(dist <= step + 6){ // hit
  impact(pr);
  pr.dead = true;
} else {
  pr.x += dx/dist*step; pr.y += dy/dist*step;
}
```

Hmm, with fast speed and small dt it's fine. But need to handle target moving — homing works.

Actually the "hit" condition dist <= step+6 means it will hit when close. With speed 420 and dt 1/60 = 7px per frame, so it hits within 13px. Fine.

impact(pr):
```js
if(pr.kind==='splash'){
  // AoE
  for(const e of enemies) if(!e.dead && dist(e, pr) <= pr.splashRadius) damageEnemy(e, pr.damage);
  explosion particles
} else {
  if(pr.target && !pr.target.dead){
    damageEnemy(pr.target, pr.damage);
    if(pr.kind==='frost'){ pr.target.slow = 1.6; pr.target.slowFactor = 0.5; }
  }
}
```

Hmm for frost, should apply slow even on... well it hits target only.

Actually let's make frost apply slow to target plus a small AoE? Keep simple: single target slow.

damageEnemy(e, dmg):
```js
e.hp -= dmg; e.hitFlash = 0.12;
if(e.hp <= 0 && !e.dead){ e.dead = true; gold += e.reward; score += e.reward*2; particles...}
```

Wait, but for the splash we iterate enemies and might damage a dead one. Check e.dead.

Also enemies killed should be removed after the frame.

Now the game loop.

Rendering:
- Background: dark with subtle grid.
- Path: draw thick stroke with rounded joins, color #2a3542, plus dashed center line.
- Base: a structure at path end.
- Slots: circles with dashed outline if empty; tower drawn if occupied.
- Enemies: circles with health bars.
- Projectiles, beams, particles.
- HUD: top bar with gold, wave, base HP, score.
- Menu overlay / gameover overlay.
- Autoplay indicator.

Let's write drawing code.

Path drawing:
```js
ctx.lineWidth = 34;
ctx.lineJoin='round'; ctx.lineCap='round';
ctx.strokeStyle='#243040';
ctx.beginPath();
ctx.moveTo(PATH[0].x,PATH[0].y);
for(let i=1;i<PATH.length;i++) ctx.lineTo(PATH[i].x,PATH[i].y);
ctx.stroke();
// inner
ctx.lineWidth = 26;
ctx.strokeStyle='#1a2430';
ctx.stroke();
// dashed
ctx.setLineDash([10,14]);
ctx.lineWidth=2;
ctx.strokeStyle='rgba(120,180,255,0.25)';
ctx.stroke();
ctx.setLineDash([]);
```

Base: draw at (890,250). A rectangle/pentagon with HP bar.

Let's draw base as a rounded square with a glow, at x=900, y=250. Actually path ends at 890. Let's place base center at (905, 250) and draw a 60x80 rounded rect. Hmm, canvas width 960, so x=905 with width 60 → goes to 935. Fine.

Hmm, but the path ends at 890,250 and the base is at 905. Enemies reach d=total → at (890,250). They'd visually be at the base's edge. Fine, let's put base at (905,250) with size ~70 wide.

Actually let's just extend the path end to (930, 250) and put the base there... but then enemies travel into the base. Let's keep path end at 890 and base drawn centered at (912, 250).

Base HP bar drawn above/below the base.

Tower rendering: draw a base circle (platform), then tower-specific shape rotating toward angle.

- cannon: dark barrel rectangle
- frost: hexagon with a snowflake-ish
- laser: thin long barrel with a glowing tip
- splash: fat barrel with a ring

Let's write a generic draw:
```js
function drawTower(t){
  const p = SLOTS[t.slot];
  // platform
  ctx.fillStyle = '#1b2733';
  ctx.beginPath(); ctx.arc(p.x,p.y,20,0,7); ctx.fill();
  ctx.strokeStyle = '#2f4257'; ctx.lineWidth=2; ctx.stroke();
  
  ctx.save();
  ctx.translate(p.x,p.y);
  ctx.rotate(t.angle);
  const def = t.def;
  // barrel
  ...
  ctx.restore();
  
  // center dome
  ctx.beginPath(); ctx.arc(p.x,p.y,10,0,7);
  ctx.fillStyle = def.color; ctx.fill();
}
```

Fine.

Let's now handle input.

```js
window.addEventListener('keydown', e=>{
  const k = e.key;
  if(k===' '){ e.preventDefault(); onSpace(); }
  if(k==='1') buy('cannon');
  if(k==='2') buy('frost');
  if(k==='3') buy('laser');
  if(k==='4') buy('splash');
  if(k==='p'||k==='P'){ autoPlay = !autoPlay; ... }
});
```

Note: in autoplay mode, the player's key presses for buying should probably still work? Let's disable manual buying when autoplay is on (or let it be; doesn't matter). Actually let's allow both but AI does its thing.

Hmm, actually P toggling autoplay mid-game should work. Let's make it so toggling P on during a game just lets the AI take over; toggling off returns control.

onSpace():
- if state==='menu': startGame()
- else if state==='gameover': reset to menu → startGame()? Requirement: "Space starts or restarts". Let's have space on gameover restart the game immediately.
- else if state==='playing' && phase==='between': startWave(wave+1)

buy(type):
- if state!=='playing' return
- find first empty slot index
- if none, flash message "No free slots"
- if gold < cost, flash "Not enough gold"
- else gold -= cost; towers[i] = makeTower(type, i); particles

Let's add a message toast.

Now the AI.

```js
let aiTimer = 0;
let aiStartDelay = 0;

function aiUpdate(dt){
  if(state==='menu'){ startGame(); return; }
  if(state==='gameover'){ /* restart after delay */ }
  
  aiTimer -= dt;
  if(aiTimer > 0) return;
  aiTimer = 0.3;
  
  // Buy
  const freeIdx = towers.findIndex(t=>!t);
  if(freeIdx >= 0){
    const counts = {};
    for(const t of towers) if(t) counts[t.type]=(counts[t.type]||0)+1;
    let want = null;
    const c = (n)=>counts[n]||0;
    if(c('cannon') < 2) want='cannon';
    else if(c('frost') < 1) want='frost';
    else if(c('splash') < 2) want='splash';
    else if(c('laser') < 2) want='laser';
    else if(c('cannon') < 3) want='cannon';
    else want='laser';
    
    const cost = TOWER_TYPES[want].cost;
    // don't buy if it would leave us broke before... just buy if affordable
    if(gold >= cost){
      buyAt(want, freeIdx);
    }
  }
  
  // Start waves
  if(phase==='between' && betweenTimer < 2.2){
    startWave(wave+1);
  }
}
```

Hmm, the between timer starts at e.g. 4. So AI waits until 2.2 remaining → 1.8s. Good.

But we should also make sure AI doesn't rush waves when it has no towers... whatever, it buys.

Actually, one issue: AI buys whenever gold >= cost, so it will spend everything constantly. That's fine and looks good.

But there's a subtlety: with 8 slots and 8 build slots, after filling all it just saves gold. Fine.

Also maybe AI should prioritize buying before starting the wave. Since aiTimer runs at 0.3s intervals and the between delay is 1.8s, it should buy first. Good.

Let's also make the AI place the best towers. Actually let's refine the build order to be more strategic. Slots near the start of the path get more use. Hmm, all slots are used in order.

Let's use build order: cannon, cannon, frost, splash, laser, cannon, splash, laser. That's 8.

Let me implement via an array and index:
```js
const AI_ORDER = ['cannon','cannon','frost','splash','laser','cannon','splash','laser'];
```
And AI takes AI_ORDER[towerCount] where towerCount = number of towers already placed (including free cannon). Since free cannon is placed at index 0, towerCount starts at 1 → next is 'cannon'.

But if the player toggles autoplay mid-game with different towers, this still works reasonably.

Actually if towerCount >= 8, no free slots anyway.

But we want it adaptive: if the player built 7 cannons then toggled autoplay... edge case, ignore.

Let's make it adaptive-ish: use the counts approach but ordered by AI_ORDER preference. Eh, I'll do:

```js
let want = AI_ORDER[Math.min(towerCount, AI_ORDER.length-1)];
```
Simple. But if the free cannon was sold... no selling. Fine.

Hmm, but if the player manually bought 3 lasers then turns on autoplay, towerCount=4 → want = 'laser'. Fine.

OK good.

Now game over: when baseHP <= 0, state='gameover', and in autoplay mode auto-restart after 3 seconds.

Let's add `restartTimer`.

Now let's write the full update loop.

```js
let last = performance.now();
function loop(now){
  let dt = (now-last)/1000; last = now;
  dt = Math.min(dt, 0.05);
  update(dt);
  render();
  requestAnimationFrame(loop);
}
```

update(dt):
```js
function update(dt){
  gameTime += dt;
  updateParticles(dt);
  
  if(state==='playing'){
    if(autoPlay) aiUpdate(dt);
    
    // spawning
    if(spawnQueue.length){
      spawnTimer -= dt;
      while(spawnQueue.length && spawnTimer <= 0){
        spawnEnemy(spawnQueue.shift());
        spawnTimer += spawnInterval;
      }
    }
    
    // enemies
    for(const e of enemies){
      if(e.dead) continue;
      if(e.slow > 0) e.slow -= dt;
      if(e.hitFlash > 0) e.hitFlash -= dt;
      const mult = e.slow > 0 ? 0.45 : 1;
      e.d += e.speed * mult * dt;
      if(e.d >= totalLen){
        e.dead = true;
        baseHP -= e.dmg;
        addExplosion(e.x, e.y, '#ff5566', 14);
        shake = 8;
        if(baseHP <= 0){ baseHP = 0; gameOver(); }
      } else {
        const p = posAt(e.d); e.x = p.x; e.y = p.y;
      }
    }
    enemies = enemies.filter(e=>!e.dead);
    
    // towers
    for(const t of towers){
      if(!t) continue;
      t.cd -= dt;
      if(t.recoil > 0) t.recoil = Math.max(0, t.recoil - dt*5);
      const tp = SLOTS[t.slot];
      let best = null, bestD = -1;
      for(const e of enemies){
        if(e.dead) continue;
        const dist = Math.hypot(e.x-tp.x, e.y-tp.y);
        if(dist <= t.def.range && e.d > bestD){ bestD = e.d; best = e; }
      }
      if(best){
        t.angle = Math.atan2(best.y - tp.y, best.x - tp.x);
        if(t.cd <= 0){
          fire(t, best);
          t.cd = t.def.cooldown;
          t.recoil = 1;
        }
      }
    }
    
    // projectiles
    updateProjectiles(dt);
    
    // between waves
    if(phase === 'between'){
      betweenTimer -= dt;
      if(betweenTimer <= 0) startWave(wave+1);
    } else if(spawnQueue.length === 0 && enemies.length === 0){
      // wave complete
      const bonus = 20 + wave*6;
      gold += bonus;
      score += 50 + wave*10;
      phase = 'between';
      betweenTimer = 4;
      toast('Wave ' + wave + ' cleared!  +' + bonus + ' gold');
    }
  }
  
  if(state==='gameover'){
    restartTimer -= dt;
    if(autoPlay && restartTimer <= 0){ startGame(); }
  }
  
  // beams
  for(const b of beams) b.life -= dt;
  beams = beams.filter(b=>b.life>0);
}
```

Wait — there's an issue with the wave-complete check: right after startWave, spawnQueue is non-empty. Fine. But between phase, spawnQueue is empty and enemies may be empty. The check is in `else if` so it won't trigger during 'between'. Good.

But careful: at the moment we call startWave(wave+1), phase becomes 'wave'. Good.

Hmm, but the order: `if(phase==='between')` block decrements timer and may start a wave. Then the `else if` won't run this frame. Fine.

One issue: when we call startWave, spawnQueue is filled but spawnTimer might be 0 → immediate spawn. Good.

Now, `fire` uses SLOTS[t.slot]. Fine.

Particles:
```js
function addParticles(x,y,color,count,speed){ ... }
```

Let's write a simple particle system.

```js
let particles = [];
function spawnParticles(x,y,color,n,spd=120,life=0.5){
  for(let i=0;i<n;i++){
    const a = Math.random()*Math.PI*2;
    const s = spd*(0.3+Math.random()*0.7);
    particles.push({x,y,vx:Math.cos(a)*s,vy:Math.sin(a)*s,life,max:life,color,r:2+Math.random()*2});
  }
}
```

Update: p.x += vx*dt; vy *= 0.96; life -= dt.

Render: alpha = life/max.

OK.

Screen shake: apply a translate in render.

Now the HUD. Draw a top bar with:
- Gold: 💰 icon (drawn) + number
- Wave: number
- Base HP: bar + number
- Score: number
- Tower shop: 4 boxes showing key, name, cost, colored

Let's draw the shop at the bottom or top-right. Since the canvas is 960x560, we have room.

Layout:
- Top bar: y 0..46, semi-transparent dark.
  - Left: "GOLD 120" 
  - "WAVE 3"
  - "BASE" + hp bar
  - Right: "SCORE 1240"
- Bottom bar: y 514..560, showing tower buttons.

Hmm, but the path starts at y=120 and slots go down to y=500. Bottom bar at 514 would overlap slot 6 at (615,500) with radius 20 → 480..520. Overlaps.

Let me shift things. Maybe put the shop in the top-right or as a vertical panel on the left.

Alternative: make the canvas taller: 960x600. Then bottom bar 560-600.

Let's set H=600 and shift the path down a bit? Or just add the shop bar at the bottom without moving the path, but ensure slots don't collide.

Slot 6 at (615,500), radius ~22 → down to 522. If the bottom bar starts at 540, fine. H=600 → bar from 548 to 600 (52px tall). OK.

Hmm, let's just use H=600 and keep everything. Path max y = 430. Slot at y=500. Bottom bar at y=548. Fine.

Actually, let me reduce: make H=580, bottom bar 532..580 (48px). Slot 6 at y=500 + 22 = 522. OK, 10px gap. Tight but fine.

Let's go with H=600 for comfort.

Canvas: 960 x 600.

Top bar: 0..50.
Bottom bar: 548..600.

Path region: y from 60 to 530.

Let me re-verify slots:
1. (215,215) ✓
2. (275,375) ✓
3. (405,225) ✓
4. (465,75) ✓  — top bar ends at 50, slot radius 22 → 53. OK tight. Let's move to (465, 85).
5. (600,215) ✓
6. (615,500) — bottom bar at 548, radius 22 → 522. ✓
7. (790,360) ✓
8. (800,165) ✓

Path y=120 top segment. Slot 4 at y=85, distance to y=120 is 35. That's too close — the tower would be on the path. Path half-width is 17. So 35 - 17 = 18px gap. Hmm, tight but visually OK? Let's move slot 4 to (465, 78). Distance 42. Still tight.

Alternatively move the top path segment down to y=140. Let's shift the whole path down a bit since we have 600 height.

New path:
P0 (-40, 130)
P1 (150, 130)
P2 (150, 320)
P3 (340, 320)
P4 (340, 150)
P5 (530, 150)
P6 (530, 440)
P7 (720, 440)
P8 (720, 260)
P9 (890, 260)

Slots:
1. (215, 220) — dist to x=150 segment: 65 ✓
2. (275, 385) — dist to y=320: 65 ✓
3. (405, 235) — dist to x=340: 65 ✓
4. (465, 90) — dist to y=150: 60 ✓
5. (600, 225) — dist to x=530: 70 ✓
6. (615, 510) — dist to y=440: 70 ✓
7. (790, 370) — dist to x=720: 70 ✓
8. (800, 175) — dist to y=260: 85 ✓

Bottom bar at 548; slot 6 at 510 + 22 = 532 ✓.

Top bar ends at 50; slot 4 at 90 - 22 = 68 ✓.

Great.

Base at end (890, 260). Draw base centered at (915, 260), width 70, height 90.

Hmm, canvas width 960. Base from 880 to 950. Enemies reach 890 and disappear. OK.

Let's now write the render function.

```js
function render(){
  ctx.save();
  ctx.clearRect(0,0,W,H);
  
  // background
  ctx.fillStyle = '#0e141c';
  ctx.fillRect(0,0,W,H);
  // grid
  ctx.strokeStyle = 'rgba(80,140,200,0.05)';
  ctx.lineWidth = 1;
  for(let x=0;x<W;x+=40){ ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,H); ctx.stroke(); }
  for(let y=0;y<H;y+=40){ ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(W,y); ctx.stroke(); }
  
  if(shake>0){ ctx.translate((Math.random()-0.5)*shake, (Math.random()-0.5)*shake); }
  
  drawPath();
  drawBase();
  drawSlots();
  drawEnemies();
  drawProjectiles();
  drawBeams();
  drawParticles();
  
  ctx.restore();
  
  drawHUD();
  drawOverlays();
}
```

Hmm, shake should decay. Add `shake = Math.max(0, shake - dt*40)` in update.

Let's write drawPath with glow.

drawSlots: for each slot, if empty draw a dashed circle; if occupied draw tower.

Tower drawing detail — let's make it look nice.

```js
function drawTower(t){
  const p = SLOTS[t.slot];
  const def = t.def;
  // range indicator when? maybe always faint. Skip for perf/clarity.
  
  // platform
  ctx.beginPath(); ctx.arc(p.x, p.y, 21, 0, Math.PI*2);
  ctx.fillStyle = '#16212c'; ctx.fill();
  ctx.lineWidth = 2.5; ctx.strokeStyle = '#2b3d50'; ctx.stroke();
  
  const rec = t.recoil * 3;
  ctx.save();
  ctx.translate(p.x, p.y);
  ctx.rotate(t.angle);
  ctx.translate(-rec, 0);
  
  if(def.kind === 'laser'){
    ctx.fillStyle = '#2a3a4a';
    ctx.fillRect(-4, -4, 26, 8);
    ctx.fillStyle = def.color;
    ctx.fillRect(18, -3, 8, 6);
    // glow
    ctx.shadowColor = def.color; ctx.shadowBlur = 12;
    ctx.fillRect(24,-2,4,4);
    ctx.shadowBlur = 0;
  } else if(def.kind === 'splash'){
    ctx.fillStyle = '#2a3a4a';
    ctx.beginPath(); ctx.roundRect(-8,-9,30,18,6); ctx.fill();
    ...
  }
  ...
}
```

`roundRect` might not exist in all browsers... it's widely supported now (Chrome 99+, Firefox 112+, Safari 16+). Should be fine, but let's avoid and use fillRect / arcs.

Let's keep it simpler with fillRect and arcs.

Cannon: dark gray barrel, orange tip.
Frost: light blue barrel, crystal.
Laser: thin pink barrel.
Splash: fat purple barrel with a ring.

I'll write a helper.

Now enemies. Draw as circles with a subtle inner shape, health bar above.

```js
function drawEnemies(){
  for(const e of enemies){
    // shadow
    ctx.beginPath(); ctx.arc(e.x, e.y, e.radius, 0, 7);
    ctx.fillStyle = e.hitFlash > 0 ? '#ffffff' : e.color;
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = 'rgba(0,0,0,0.5)';
    ctx.stroke();
    // slow indicator
    if(e.slow > 0){
      ctx.beginPath(); ctx.arc(e.x, e.y, e.radius+3, 0, 7);
      ctx.strokeStyle = 'rgba(120,220,255,0.9)'; ctx.lineWidth=2; ctx.stroke();
    }
    // hp bar
    const w = e.radius*2.2, h = 4;
    const hpFrac = Math.max(0, e.hp/e.maxHp);
    ctx.fillStyle = 'rgba(0,0,0,0.6)';
    ctx.fillRect(e.x-w/2, e.y-e.radius-11, w, h);
    ctx.fillStyle = hpFrac > 0.5 ? '#4ade80' : hpFrac > 0.25 ? '#fbbf24' : '#f87171';
    ctx.fillRect(e.x-w/2, e.y-e.radius-11, w*hpFrac, h);
  }
}
```

Boss should be bigger with a crown or something. It's fine.

Now HUD.

```js
function drawHUD(){
  // top bar
  ctx.fillStyle = 'rgba(10,16,24,0.9)';
  ctx.fillRect(0,0,W,50);
  ctx.strokeStyle = 'rgba(80,140,200,0.25)';
  ctx.beginPath(); ctx.moveTo(0,50); ctx.lineTo(W,50); ctx.stroke();
  
  ctx.font = 'bold 18px system-ui, sans-serif';
  ctx.textBaseline = 'middle';
  
  // gold
  ctx.fillStyle = '#ffd166';
  ctx.beginPath(); ctx.arc(30, 25, 9, 0, 7); ctx.fill();
  ctx.fillStyle = '#e8eef5';
  ctx.textAlign = 'left';
  ctx.fillText(String(gold), 48, 26);
  
  // wave
  ctx.fillStyle = '#8ab4f8';
  ctx.fillText('WAVE', 180, 26);
  ctx.fillStyle = '#e8eef5';
  ctx.fillText(String(wave), 245, 26);
  
  // base hp
  ...
}
```

Let's lay out:
- Gold at x=20
- Wave at x=180
- Base HP bar at x=320..560
- Score at x=600
- Autoplay indicator at right

Actually let's do:
- "GOLD" label + value at left (x 20-160)
- "WAVE" at x 190
- "BASE" bar at x 300 (bar 300..520)
- "SCORE" at x 560
- Right side: autoplay badge at x 780-940

Fine.

Bottom bar: 4 tower buttons.

Each button: width ~200, height 40, at y=556.
x positions: 40, 260, 480, 700. Width 200, gap 20. Total 40+200+20+200+20+200+20+200 = 920. Ends at 920. 

Let's compute: 4 buttons of 190 width with 15 gap, starting at 60: 60, 265, 470, 675, ends at 865. Add right margin. Fine.

Actually let's center: total width = 4*190 + 3*16 = 760+48 = 808. Start x = (960-808)/2 = 76.

Button at y=556, height 36. Bar from 548 to 600. So y=554, h=38 → 554..592. Good.

Each button shows: "[1] Cannon  50g" with color dot.

Also gray out if unaffordable.

Now overlays:
- menu: dark overlay with title, instructions, "Press SPACE to start", "Press P for autoplay demo".
- gameover: "GAME OVER", final score/wave, "Press SPACE to restart".

Let's write.

Now let's think about the 30-second window again. Requirements: "The animation should show everything important within the first 30 seconds".

With autoplay, at t=0 space is pressed (or P). Hmm — if the viewer loads the page and doesn't press anything, nothing happens. Should we auto-start? The requirement says the animation should show everything important within the first 30 seconds. That suggests the game should be visibly doing something quickly.

I think the safest: start in autoplay demo mode by default? But then "Space starts or restarts" and P toggles. Hmm.

Let's make it so the game starts in menu, but if the user does nothing for ~3 seconds, autoplay kicks in automatically? That's a nice touch but could be confusing.

Actually, let's just start with autoplay ON by default. The viewer sees a good run immediately. Pressing P turns it off. Pressing Space starts/restarts. Hmm, but if autoplay is on and it's in menu state, the AI will call startGame immediately. That works.

But "Space starts or restarts" — with autoplay on, space would restart. Fine.

Hmm, but a user might want to play manually. Press P to disable autoplay, then Space to start.

I think auto-starting the demo is the best for a recorded 30s window. Let's do: autoplay starts ON. The menu overlay shows briefly with "AUTOPLAY DEMO — press P to take control". Actually if autoplay is on, it starts the game immediately at t=0.

Let's do that: `autoPlay = true` initially, and in the first update, since state==='menu' and autoPlay, we call startGame().

Then the demo runs. 

But wait — should the menu show at all? Let's just skip the menu when autoplay is on. Actually, let's show a brief title flash? Nah.

Hmm, but the requirement says "Space starts or restarts". If autoplay is on from the start, then space restarts. That's still satisfied.

Let me make it: on load, autoplay = true → immediately starts the game and plays. Press P → autoplay off, and if state is 'playing' it just continues with the player in control. Press Space → start/restart.

Hmm, but if the player presses P while the demo is running, they take over mid-game. That's fine.

Actually, let me reconsider: maybe better to have the game start in menu with autoplay ON meaning the AI will press space after a short delay (0.6s). That shows the title briefly. Let's do that — a 0.8s delay so the viewer sees the title, then the demo begins. Actually the title would be gone by then... 

Simplest and best for recording: autoplay ON, starts immediately. And I'll draw a small "AUTOPLAY DEMO (P to toggle)" badge. And there's no menu at all in autoplay mode.

But then if a viewer presses P, they'd be in the middle of a game. That's OK.

Hmm, let me reconsider once more. Requirement: "Space starts or restarts." — must be implemented. It is. Fine.

Let me also add: when autoplay is toggled off during 'menu' state, show the menu.

OK, let's go with autoPlay = true initially and the game auto-starts.

Actually wait. There's a subtlety: if autoplay is on and the game ends, it auto-restarts after 3s. Good for looping.

Let's write it.

One more thing: the AI needs to handle the 'menu' state. If autoPlay and state==='menu', start the game.

Now let's also make sure the demo run is "competent". Let's tune numbers so the AI survives many waves.

Let's simulate mentally:
Wave 1: 6 grunts, hp 22. Free cannon at slot 0.
AI: gold 90. towerCount=1 → AI_ORDER[1]='cannon', cost 50. Buys at slot 1 (275,385). Hmm, slot 1 is near the start-ish. Gold left 40.

Wait, slots are filled in order 0..7. Slot 0 is free cannon (215,220). Slot 1 = (275,385).

Hmm, slot 1 at (275,385) covers segment C (y=320, x 150-340) at distance 65. Yes covers.

Wave 1 enemies: 22 hp, cannon does 16 → 2 shots. Two cannons → fine.

After wave 1: +48 gold + bonus 26 = 74, plus 40 = 114.

Wave 2: n = 5+3 = 8. Mixed. AI buys AI_ORDER[2] = 'frost' (65). Gold 114-65=49.
Wave 2: 8 enemies hp 22*1.16=26. Should be OK.

Wave 3: +... Let's estimate gold accumulation. Each grunt gives 8, runner 9, tank 16.

Wave 3: n=5+4=9. AI buys AI_ORDER[3]='splash' (110). Needs 110. Gold after wave 2 ≈ 49 + (8*~9=72) + 32 = 153. Buys splash → 43 left.

Wave 4: n=5+6=11. hp 22*1.16^3 = 34.3.
AI buys AI_ORDER[4]='laser' (90). 

Wave 5: n=5+8=13, plus boss. hp 22*1.16^4=39.8, boss hp 260*1.16^4=470.

Hmm, boss with 470 hp at wave 5. DPS available: 2 cannons (29 dps each = 58), frost (6/0.75=8 dps + slow), splash (26/1.3=20 dps AoE), laser (11/0.2=55 dps). Total ~140 dps but only when in range.

Boss speed 40 px/s, path 1750 → 44s traversal. Plenty of time. But is the boss in range of towers long enough? Each tower covers a segment of the path. With 5 towers spread along, the boss is covered maybe 60% of the time. ~84 dps * 26s = 2180 damage. Fine.

But there are 13 other enemies too. Should be OK.

Later waves: hp scaling 1.16^w. Wave 10: 22*1.16^9 = 22*3.8 = 84. Wave 15: 22*1.16^14 = 22*8.1 = 178. Wave 20: 22*1.16^19 = 22*17.4 = 383. Boss wave 20: 260*17.4 = 4524.

Tower DPS doesn't scale (no upgrades). So eventually the AI loses. That's fine — "waves get harder" and the game ends. But the demo should last a good while. With 8 towers at ~150-200 effective dps total and enemy counts growing... Let's see: wave 15 has n=5+24=29 enemies at 178 hp = 5162 total HP, spawning over 29*0.7=20s. Need ~260 dps sustained. Hmm, we'd have maybe 250 dps if all towers are in range simultaneously — but they're spread out.

Realistically the demo survives to maybe wave 12-16. That's ~2-3 minutes of good gameplay. 

Actually, maybe I should add slight tower scaling or reduce enemy HP scaling to 1.13. Let's use 1.14. Wave 20: 22*1.14^19 = 22*12.06 = 265. Boss: 260*12 = 3120.

Hmm. Let's also give the player more gold so more towers... but there are only 8 slots.

Alternatively, add tower upgrades? Not required. Let's not.

I'll use 1.15 scaling and let it end around wave 12-15. The 30s window is what matters, and it'll be action-packed.

Actually, one important thing: base HP = 20. With leaks, it'll drop. Let's give 20 HP and each grunt does 1. So it can absorb 20 leaks. Good.

Hmm, actually maybe make base HP 25 for a longer demo. Let's do 20, it's fine.

Let me reconsider the "score" — score += reward*2 on kill, + 50 + wave*10 on wave clear.

Now, let me write the actual code carefully.

Additional detail: `posAt` should be efficient. It's called per enemy per frame. 8 segments max, fine.

Let me write it all out.

```js
(function(){
'use strict';

const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
const W = 960, H = 600;

function resize(){
  const s = Math.min(window.innerWidth / W, window.innerHeight / H);
  canvas.style.width = Math.floor(W*s) + 'px';
  canvas.style.height = Math.floor(H*s) + 'px';
}
window.addEventListener('resize', resize);
resize();

// ---------- Path ----------
const PATH = [
  {x:-40,y:130},{x:150,y:130},{x:150,y:320},{x:340,y:320},{x:340,y:150},
  {x:530,y:150},{x:530,y:440},{x:720,y:440},{x:720,y:260},{x:890,y:260}
];
const SEGS = [];
let PATH_LEN = 0;
for(let i=0;i<PATH.length-1;i++){
  const a=PATH[i], b=PATH[i+1];
  const dx=b.x-a.x, dy=b.y-a.y, len=Math.hypot(dx,dy);
  SEGS.push({a, dx:dx/len, dy:dy/len, len, start:PATH_LEN});
  PATH_LEN += len;
}
function posAt(d){
  if(d<=0) return {x:PATH[0].x, y:PATH[0].y};
  for(let i=0;i<SEGS.length;i++){
    const s=SEGS[i];
    if(d <= s.start + s.len){
      const t = d - s.start;
      return {x: s.a.x + s.dx*t, y: s.a.y + s.dy*t};
    }
  }
  const l = PATH[PATH.length-1];
  return {x:l.x, y:l.y};
}
```

Wait, `d <= s.start + s.len` — for the last segment, if d == PATH_LEN, it returns the last point. Good.

Slots and types as above.

Now writing everything. Let me be thorough.

For the base drawing:

```js
function drawBase(){
  const bx = 912, by = 260;
  // glow
  const g = ctx.createRadialGradient(bx,by,10,bx,by,90);
  g.addColorStop(0,'rgba(90,200,255,0.25)');
  g.addColorStop(1,'rgba(90,200,255,0)');
  ctx.fillStyle=g;
  ctx.beginPath(); ctx.arc(bx,by,90,0,7); ctx.fill();
  
  // body
  ctx.fillStyle = '#1c2b3a';
  ctx.strokeStyle = '#3f6d94';
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(bx-34, by-46);
  ctx.lineTo(bx+34, by-46);
  ctx.lineTo(bx+34, by+46);
  ctx.lineTo(bx-34, by+46);
  ctx.closePath();
  ctx.fill(); ctx.stroke();
  
  // core
  const pulse = 0.6 + 0.4*Math.sin(gameTime*4);
  ctx.fillStyle = `rgba(90,200,255,${0.5+0.5*pulse})`;
  ctx.beginPath(); ctx.arc(bx, by, 14, 0, 7); ctx.fill();
  
  // HP bar
  ...
}
```

Hmm, the base at x=912 with half-width 34 → 878..946. Path ends at 890. Good.

Base HP bar: draw at top of the base? Or in the HUD. HUD has it. Also draw a small one above the base.

Let's draw a vertical HP bar to the left of the base? Simpler: draw it above the base at y = by - 60.

Actually the HUD already shows base HP. Let's also draw a small bar under the base.

OK.

Now the code for `fire` and projectiles.

Let me write the whole thing now.

One more consideration: the `beams` array for laser visuals.

Also: tower muzzle flash particles.

Let's write.

```js
function fire(t, target){
  const p = SLOTS[t.slot];
  const def = t.def;
  const ang = Math.atan2(target.y-p.y, target.x-p.x);
  const mx = p.x + Math.cos(ang)*20;
  const my = p.y + Math.sin(ang)*20;
  
  if(def.kind === 'laser'){
    damageEnemy(target, def.damage);
    beams.push({x1:mx,y1:my,x2:target.x,y2:target.y,life:0.08,max:0.08,color:def.color});
    spawnParticles(target.x, target.y, def.color, 2, 60, 0.2);
    return;
  }
  
  projectiles.push({
    x:mx, y:my, tx:target.x, ty:target.y, target,
    speed: def.speed, damage: def.damage, kind: def.kind,
    color: def.color, splashRadius: def.splashRadius||0,
    dead:false, angle: ang
  });
  spawnParticles(mx,my, def.color, 3, 80, 0.15);
}
```

Projectile update and impact.

Let me write `impact`:
```js
function impact(pr){
  if(pr.kind === 'splash'){
    for(const e of enemies){
      if(e.dead) continue;
      const d = Math.hypot(e.x-pr.x, e.y-pr.y);
      if(d <= pr.splashRadius) damageEnemy(e, pr.damage);
    }
    spawnParticles(pr.x, pr.y, pr.color, 14, 200, 0.45);
  } else {
    if(pr.target && !pr.target.dead){
      damageEnemy(pr.target, pr.damage);
      if(pr.kind === 'frost'){
        pr.target.slow = 1.8;
        pr.target.slowFactor = 0.45;
      }
    }
    spawnParticles(pr.x, pr.y, pr.color, 5, 120, 0.3);
  }
}
```

Hmm, for the splash, damage should maybe fall off. Keep it simple.

Also frost should slow even if it kills? Doesn't matter.

`damageEnemy`:
```js
function damageEnemy(e, dmg){
  if(e.dead) return;
  e.hp -= dmg;
  e.hitFlash = 0.1;
  if(e.hp <= 0){
    e.dead = true;
    gold += e.reward;
    score += e.reward * 2;
    spawnParticles(e.x, e.y, e.color, 12, 160, 0.5);
  }
}
```

Now the enemies get filtered after the loop.

Careful: `damageEnemy` during the tower loop sets e.dead, and the enemy filter happens before the tower loop. So dead enemies stay in the array until the next frame. The tower targeting loop checks `if(e.dead) continue;`. Good. And the projectile loop also checks.

Hmm, but the enemy update loop is before the tower loop, and the filter is right after. Then towers fire and mark enemies dead. Then projectiles update and may hit dead enemies — guarded.

OK.

Let's now write the between-wave logic more carefully. Also we need to handle the case where the wave is cleared but the player wants to start early with Space.

Now, the AI's wave starting: `if(phase==='between' && betweenTimer < 2.2) startWave(wave+1);`

But we also need `autoPlay` AI to handle the menu.

Let me write the full update:

```js
function update(dt){
  gameTime += dt;
  if(shake > 0) shake = Math.max(0, shake - dt*60);
  
  // particles
  for(const p of particles){
    p.x += p.vx*dt; p.y += p.vy*dt;
    p.vx *= 0.94; p.vy *= 0.94;
    p.life -= dt;
  }
  particles = particles.filter(p=>p.life>0);
  
  for(const b of beams) b.life -= dt;
  beams = beams.filter(b=>b.life>0);
  
  if(state === 'playing'){
    if(autoPlay) aiUpdate(dt);
    ...
  }
  
  if(state === 'menu' && autoPlay){
    startGame();
  }
  
  if(state === 'gameover'){
    restartTimer -= dt;
    if(autoPlay && restartTimer <= 0) startGame();
  }
}
```

Hmm, if autoplay is on at start, `state === 'menu'` triggers startGame immediately. Good.

But then if the player turns autoplay off in the menu, they see the menu. Good.

Now startGame():
```js
function startGame(){
  wave = 0; gold = 90; score = 0; baseHP = BASE_MAX;
  enemies = []; projectiles = []; particles = []; beams = [];
  towers = new Array(SLOTS.length).fill(null);
  towers[0] = makeTower('cannon', 0);
  spawnQueue = []; spawnTimer = 0; betweenTimer = 0; phase = 'wave';
  toastMsg = ''; toastTime = 0;
  state = 'playing';
  startWave(1);
  aiTimer = 0.2;
  aiWaveDelay = 0;
}
```

Wait, the free cannon is at slot 0. But then the AI's towerCount = 1 → AI_ORDER[1] = 'cannon'. Good.

Hmm, but the player might want to place the free cannon elsewhere. Requirement says "Place one free cannon at start". Slot 0 is fine.

Now, `startWave(n)`:
```js
function startWave(n){
  wave = n;
  const list = buildWave(n);
  spawnInterval = Math.max(0.5, 1.3 - n*0.055);
  spawnQueue = list.slice();
  spawnTimer = 0.4;
  phase = 'wave';
  toast('WAVE ' + n, 1.2);
}
```

Hmm, `toast` for wave start. Let's have a big centered wave announcement.

Let's use a separate variable `waveAnnounce = {text, time}`.

OK.

Now the toast function:
```js
function toast(msg, t){ toastMsg = msg; toastTime = t || 1.5; }
```

And decrement toastTime in update.

Now let me write buildWave:

```js
function buildWave(n){
  const list = [];
  const count = 5 + Math.floor(n * 1.7);
  for(let i=0;i<count;i++){
    let t = 'grunt';
    if(n >= 2 && i % 3 === 2) t = 'runner';
    if(n >= 3 && i % 5 === 4) t = 'tank';
    list.push(t);
  }
  if(n % 5 === 0) list.push('boss');
  return list;
}
```

Wave 1: count = 5+1 = 6 grunts.
Wave 2: 5+3 = 8: i=2,5 → runners. So 6 grunts, 2 runners.
Wave 5: 5+8=13 + boss.

Good.

Enemy defs:
```js
const ENEMY_TYPES = {
  grunt:  { hp: 22,  speed: 68,  reward: 8,  dmg: 1, radius: 11, color: '#5fd68a' },
  runner: { hp: 15,  speed: 115, reward: 9,  dmg: 1, radius: 9,  color: '#ffd166' },
  tank:   { hp: 62,  speed: 46,  reward: 17, dmg: 2, radius: 15, color: '#ff7b7b' },
  boss:   { hp: 300, speed: 42,  reward: 70, dmg: 6, radius: 21, color: '#c084fc' },
};
```

HP scale: `Math.pow(1.15, wave-1)`.

Wave 5 boss: 300 * 1.15^4 = 300*1.749 = 525.

Hmm. That might be tough but the AI should handle it.

Let's compute the AI's DPS at wave 5:
Towers: cannon, cannon, frost, splash, laser (5 towers) + maybe more.
- cannon: 16/0.55 = 29 dps × 2 = 58
- frost: 6/0.75 = 8 dps
- splash: 26/1.3 = 20 dps (AoE, so effectively more)
- laser: 11/0.2 = 55 dps

Total ~141 dps if all in range. Boss travels 1750px at 42px/s = 41s. Coverage: each tower covers ~200-300px of path → 5 towers cover maybe 1200px of the 1750 → 70%. So the boss is under fire ~70% of the time → 141*0.7*41 ≈ 4000 damage. Boss has 525 HP. Fine.

Later, wave 10: hp scale 1.15^9 = 3.52. grunt 77, tank 218, boss (wave 10) 300*3.52=1056. Count = 5+17=22 + boss. Total HP ≈ 22*~100 = 2200 + 1056 = 3256. Spawn time 22*0.75 = 16.5s. Need 200 dps sustained. We have ~141 base dps with 5 towers. Hmm, at wave 10 the AI would have 8 towers by then (it buys ~1 per wave).

8 towers: let's say AI_ORDER = cannon, cannon, frost, splash, laser, cannon, splash, laser → 3 cannons (87), 1 frost (8), 2 splash (40), 2 lasers (110) = 245 dps. That's better. Plus AoE splash hitting multiple.

OK, reasonable. The AI should survive to wave ~12-15.

Let's make the AI_ORDER a bit smarter: maybe more lasers since they're highest DPS. But lasers cost 90. Order: cannon, cannon, frost, laser, splash, laser, splash, laser.

Hmm, with 8 slots: 2 cannon, 1 frost, 1 splash, 4 laser? Let's do:
AI_ORDER = ['cannon','cannon','frost','laser','splash','laser','splash','laser'].

DPS: 2 cannons (58) + frost (8) + 3 lasers (165) + 2 splash (40) = 271 dps + AoE. 

Gold: 50+50+65+90+110+90+110+90 = 655. Plus the free cannon. Over ~8 waves that's achievable? Wave rewards: each wave gives roughly count*9 + 20+6w. Wave 1: 6*8=48+26=74. Wave 2: 8*9=72+32=104. Wave 3: 9*9=81+38=119. Wave 4: 11*10=110+44=154. Wave 5: 13*10+boss70=200+50=250. Wave 6: 15*10=150+56=206. Wave 7: 16*11=176+62=238. Wave 8: 18*11=198+68=266.

Cumulative: 74, 178, 297, 451, 701, 907, 1145, 1411. Plus starting 90 = 1501.

Total needed for 8 towers (7 bought + free) = 655 - 50 = 605. Easily affordable by wave 5-6. So by wave 8 the AI has all 8 towers. Then it just accumulates gold.

So the AI is strong. The challenge is the HP scaling.

Wave 12: scale 1.15^11 = 4.65. Count = 5+20 = 25. grunt 102, runner 70, tank 288. Total ≈ 25*120 = 3000 + boss (wave 10 was 1056, wave 15 would be 300*1.15^14=2124). Wave 12: no boss (12%5≠0). So 3000 HP over 25*0.64 = 16s spawn. Need 190 dps. We have 271. Should be OK.

Wave 15: scale 1.15^14 = 7.08. Count = 5+25 = 30, + boss 2124. grunt 156, tank 439. Total ≈ 30*180 = 5400 + 2124 = 7524. Spawn over 30*0.48 = 14.4s. Need 520 dps. We have 271. Fail.

So the game ends around wave 14-16. That's about 3-4 minutes. Good enough for a demo.

OK.

Now, let's also make sure that the first 30 seconds are interesting. At t=0, wave 1 starts, 6 grunts spawn over ~7s, they walk. The cannon at slot 0 starts shooting at ~t=2s. Kills happen. Gold increases. At ~t=10s wave 1 cleared, bonus. AI buys another cannon. Wave 2 starts at ~t=12s. More action. Good.

Wait, actually, will wave 1 be cleared by t=10s? Enemies spawn at 1.24s intervals, 6 enemies → last at 6.2s. Path traversal at 68px/s = 25.7s. So the last enemy reaches the base at t≈32s if not killed. The cannon kills them along the way.

Cannon at (215,220), range 135. Covers segment B (x=150, y=130-320) from y=130 (dist sqrt(65²+90²)=111) to y=320 (dist sqrt(65²+100²)=119). So the whole segment B is in range. Also segment A (y=130, x=-40..150): distance from (215,220) at x=150 is sqrt(65²+90²)=111, at x=100 is sqrt(115²+90²)=146 > 135. So partial.

Enemy enters range at around x=100 on segment A (t = 140/68 = 2.06s) and leaves at the end of segment B (x=150,y=320 → d = 180+190 = 370 → t = 5.4s). So ~3.4s in range → 29 dps * 3.4 = 98 damage. Enough for 22 HP. 

Enemy 1 spawned at t=0.4s, killed around t=3s. Enemy 2 spawned at 1.64s, killed at ~4.2s. Etc. The cannon fires every 0.55s, killing one per 1.1s (2 shots). Spawn interval 1.24s. So it roughly keeps up. Might leak 1-2.

Then the AI buys a second cannon at slot 1 (275,385) which covers segment C. That helps.

OK, good.

Now let's think about whether the second cannon at slot 1 (275,385) is useful. It covers segment C (y=320, x=150-340): distance from (275,385) is 65 at x=275, at x=150 → sqrt(125²+65²)=141 > 135, at x=340 → sqrt(65²+65²)=92. So covers x from ~200 to 340 on segment C. And segment D (x=340, y=320→150): at y=320 dist 92, at y=250 dist sqrt(65²+135²)=150. So covers a bit.

Fine.

Now let's write the rendering of everything.

Let me now write out the complete code.

Also need to handle `ctx.roundRect` fallback — I'll avoid it.

Let me write the HUD carefully.

```js
function drawHUD(){
  // top bar
  ctx.fillStyle = 'rgba(8,13,20,0.92)';
  ctx.fillRect(0,0,W,50);
  ctx.strokeStyle = 'rgba(90,150,210,0.3)';
  ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(0,50); ctx.lineTo(W,50); ctx.stroke();
  
  ctx.textBaseline = 'middle';
  ctx.textAlign = 'left';
  
  // GOLD
  ctx.fillStyle = '#ffd166';
  ctx.beginPath(); ctx.arc(28, 25, 9, 0, Math.PI*2); ctx.fill();
  ctx.fillStyle = '#0e141c'; ctx.font = 'bold 12px system-ui'; ctx.textAlign='center';
  ctx.fillText('$', 28, 26);
  ctx.textAlign='left';
  ctx.font = 'bold 20px system-ui';
  ctx.fillStyle = '#f2f6fb';
  ctx.fillText(String(gold), 46, 26);
  
  // WAVE
  ctx.font = 'bold 13px system-ui';
  ctx.fillStyle = '#6b8fb5';
  ctx.fillText('WAVE', 170, 18);
  ctx.font = 'bold 22px system-ui';
  ctx.fillStyle = '#8ab4f8';
  ctx.fillText(String(wave), 170, 36);
  
  // BASE HP
  ctx.font = 'bold 13px system-ui';
  ctx.fillStyle = '#6b8fb5';
  ctx.fillText('BASE', 260, 18);
  const bw = 200, bh = 16, bx = 260, by = 26;
  ctx.fillStyle = 'rgba(255,255,255,0.1)';
  ctx.fillRect(bx, by, bw, bh);
  const frac = Math.max(0, baseHP/BASE_MAX);
  const col = frac > 0.5 ? '#4ade80' : frac > 0.25 ? '#fbbf24' : '#f87171';
  ctx.fillStyle = col;
  ctx.fillRect(bx, by, bw*frac, bh);
  ctx.strokeStyle = 'rgba(255,255,255,0.2)'; ctx.lineWidth=1;
  ctx.strokeRect(bx+0.5, by+0.5, bw-1, bh-1);
  ctx.fillStyle = '#e8eef5';
  ctx.font = 'bold 13px system-ui';
  ctx.textAlign = 'center';
  ctx.fillText(baseHP + ' / ' + BASE_MAX, bx + bw/2, by + bh/2 + 1);
  ctx.textAlign = 'left';
  
  // SCORE
  ctx.font = 'bold 13px system-ui';
  ctx.fillStyle = '#6b8fb5';
  ctx.fillText('SCORE', 510, 18);
  ctx.font = 'bold 22px system-ui';
  ctx.fillStyle = '#f2f6fb';
  ctx.fillText(String(score), 510, 36);
  
  // autoplay badge
  ...
}
```

Hmm, wait. "BASE" label at y=18 and the bar at y=26 with height 16 → 26..42. And the bar text is centered at 34. OK.

Let me redo the layout: top bar 0-50. Labels at y=17, values at y=34.

- Gold: circle at (26,25) r=9, value text at 44, font 20px, baseline middle → y=25.
- WAVE label at x=170,y=15; value at x=170, y=34.
- BASE label at x=250, y=15; bar at x=250,y=24,w=200,h=18.
- SCORE label at x=490,y=15; value at x=490,y=34.
- Autoplay badge at right, x=760..940.

Hmm, "SCORE" value could be long. Let's give it room: x=490 to 620.

Autoplay badge: rounded rect at (790, 12, 150, 26) with text.

Actually, let's put the badge at x=770, width 170, y=12, height 26.

Text: "AUTOPLAY DEMO" or "MANUAL". Let's show "P: AUTOPLAY ON" / "P: AUTOPLAY OFF".

OK.

Bottom bar with shop buttons:

```js
function drawShop(){
  ctx.fillStyle = 'rgba(8,13,20,0.92)';
  ctx.fillRect(0, 548, W, 52);
  ctx.strokeStyle = 'rgba(90,150,210,0.3)';
  ctx.beginPath(); ctx.moveTo(0,548); ctx.lineTo(W,548); ctx.stroke();
  
  const order = ['cannon','frost','laser','splash'];
  const bw = 190, bh = 38, gap = 16;
  const totalW = order.length*bw + (order.length-1)*gap;
  let x = (W - totalW)/2;
  const y = 555;
  
  for(let i=0;i<order.length;i++){
    const type = order[i];
    const def = TOWER_TYPES[type];
    const affordable = gold >= def.cost;
    
    ctx.fillStyle = affordable ? 'rgba(30,45,62,0.95)' : 'rgba(22,28,36,0.8)';
    ctx.fillRect(x, y, bw, bh);
    ctx.strokeStyle = affordable ? def.color : 'rgba(255,255,255,0.12)';
    ctx.lineWidth = 2;
    ctx.strokeRect(x+1, y+1, bw-2, bh-2);
    
    // color dot
    ctx.beginPath(); ctx.arc(x+22, y+bh/2, 8, 0, Math.PI*2);
    ctx.fillStyle = def.color; ctx.globalAlpha = affordable?1:0.35; ctx.fill(); ctx.globalAlpha = 1;
    
    ctx.textAlign='left'; ctx.textBaseline='middle';
    ctx.font = 'bold 15px system-ui';
    ctx.fillStyle = affordable ? '#e8eef5' : 'rgba(230,238,245,0.4)';
    ctx.fillText('[' + def.key + '] ' + def.name, x+40, y+bh/2);
    
    ctx.textAlign='right';
    ctx.font = 'bold 15px system-ui';
    ctx.fillStyle = affordable ? '#ffd166' : 'rgba(255,209,102,0.35)';
    ctx.fillText(def.cost + 'g', x+bw-14, y+bh/2);
    
    x += bw + gap;
  }
}
```

Good.

Now overlays.

```js
function drawOverlay(){
  if(state === 'menu'){
    ctx.fillStyle='rgba(6,10,16,0.82)';
    ctx.fillRect(0,0,W,H);
    ctx.textAlign='center'; ctx.textBaseline='middle';
    ctx.fillStyle='#8ab4f8';
    ctx.font='bold 54px system-ui';
    ctx.fillText('TOWER DEFENSE', W/2, 200);
    ctx.fillStyle='#c9d6e4';
    ctx.font='18px system-ui';
    ctx.fillText('Enemies march from the left. Stop them before they reach your base.', W/2, 260);
    ctx.fillText('Press 1-4 to buy towers into the next free slot.', W/2, 292);
    ctx.fillText('Space starts / restarts.  P toggles the autoplay demo.', W/2, 324);
    ...
  }
}
```

Actually, since autoplay starts immediately, the menu is rarely seen. Fine, keep it.

Game over overlay:
```js
if(state === 'gameover'){
  ctx.fillStyle='rgba(40,6,10,0.72)';
  ctx.fillRect(0,0,W,H);
  ...
  ctx.fillText('BASE DESTROYED', W/2, 220);
  ctx.fillText('Waves survived: ' + (wave-1), W/2, 290);  // hmm, wave is the current one
  ctx.fillText('Score: ' + score, W/2, 330);
  ctx.fillText('Press SPACE to play again', W/2, 410);
}
```

Hmm, "Waves survived: wave-1" — if you die during wave 5, you survived 4. Let's just show "Wave reached: wave".

OK.

Now let's finalize the code. Let me write it out.

Also need to handle the case where the AI is on and the state is 'gameover' — auto restart.

Let me write the AI:

```js
let aiTimer = 0;
const AI_ORDER = ['cannon','cannon','frost','laser','splash','laser','splash','laser'];

function aiUpdate(dt){
  aiTimer -= dt;
  if(aiTimer > 0) return;
  aiTimer = 0.25;
  
  // Count towers
  let count = 0;
  for(const t of towers) if(t) count++;
  
  const freeIdx = towers.findIndex(t => !t);
  if(freeIdx >= 0){
    const want = AI_ORDER[Math.min(count, AI_ORDER.length-1)];
    const cost = TOWER_TYPES[want].cost;
    if(gold >= cost){
      buyAt(want, freeIdx);
    }
  }
  
  if(phase === 'between' && betweenTimer < 2.0){
    startWave(wave + 1);
  }
}
```

Hmm, `AI_ORDER[count]` where count includes the free cannon (count=1 → index 1 = 'cannon'). Good.

But wait: if the player manually places towers then toggles autoplay, count might not reflect the build. Fine.

Also, the AI should perhaps not start the wave if it's about to buy a tower. With the 0.25s timer and betweenTimer starting at 4, and the AI buying immediately when gold is available, it works out.

Hmm, one thing: betweenTimer < 2.0 means the AI waits ~2s. Let's use 2.5 so it starts after 1.5s. Actually let's make betweenTimer = 5 and AI starts at < 3.5, so 1.5s pause. Eh, let's just use betweenTimer = 4 and AI start threshold 2.5 → 1.5s wait.

Fine.

Let's also have the AI, when it has no free slots and lots of gold... nothing to do. Fine.

Now let's write `buyAt(type, idx)`:
```js
function buyAt(type, idx){
  const def = TOWER_TYPES[type];
  if(gold < def.cost) return false;
  gold -= def.cost;
  towers[idx] = makeTower(type, idx);
  spawnParticles(SLOTS[idx].x, SLOTS[idx].y, def.color, 14, 140, 0.5);
  return true;
}
```

And `buy(type)` for player:
```js
function buy(type){
  if(state !== 'playing') return;
  const idx = towers.findIndex(t => !t);
  if(idx < 0){ toast('No free slots!'); return; }
  const def = TOWER_TYPES[type];
  if(gold < def.cost){ toast('Not enough gold!'); return; }
  buyAt(type, idx);
}
```

Hmm, but in autoplay mode, should manual keys work? Let's allow them — it doesn't hurt.

Actually, it could confuse the AI's tower count. Minor. Let's allow.

Now `makeTower`:
```js
function makeTower(type, slot){
  const def = TOWER_TYPES[type];
  return { type, def, slot, cd: 0, angle: -Math.PI/2, recoil: 0 };
}
```

Now let me write the drawing for towers.

```js
function drawTower(t){
  const p = SLOTS[t.slot];
  const def = t.def;
  
  // base platform
  ctx.beginPath(); ctx.arc(p.x, p.y, 22, 0, Math.PI*2);
  ctx.fillStyle = '#152029';
  ctx.fill();
  ctx.lineWidth = 3;
  ctx.strokeStyle = 'rgba(70,110,150,0.7)';
  ctx.stroke();
  
  // inner ring
  ctx.beginPath(); ctx.arc(p.x, p.y, 16, 0, Math.PI*2);
  ctx.strokeStyle = 'rgba(255,255,255,0.06)';
  ctx.lineWidth = 1;
  ctx.stroke();
  
  ctx.save();
  ctx.translate(p.x, p.y);
  ctx.rotate(t.angle);
  ctx.translate(-t.recoil * 4, 0);
  
  if(t.type === 'cannon'){
    ctx.fillStyle = '#3a4a5a';
    ctx.fillRect(-6, -5, 24, 10);
    ctx.fillStyle = '#5a6d80';
    ctx.fillRect(-6, -5, 24, 4);
    ctx.fillStyle = def.color;
    ctx.fillRect(16, -6, 8, 12);
  } else if(t.type === 'frost'){
    ctx.fillStyle = '#2d4a5c';
    ctx.fillRect(-6, -6, 22, 12);
    ctx.fillStyle = def.color;
    ctx.beginPath(); ctx.arc(16, 0, 7, 0, Math.PI*2); ctx.fill();
    // crystal
    ctx.strokeStyle = '#dffaff'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(16, -5); ctx.lineTo(16, 5); ctx.moveTo(12,-2.5); ctx.lineTo(20,2.5); ctx.moveTo(20,-2.5); ctx.lineTo(12,2.5); ctx.stroke();
  } else if(t.type === 'laser'){
    ctx.fillStyle = '#3a2a3a';
    ctx.fillRect(-6, -4, 28, 8);
    ctx.fillStyle = def.color;
    ctx.fillRect(22, -5, 6, 10);
    ctx.shadowColor = def.color; ctx.shadowBlur = 10;
    ctx.fillRect(26, -3, 4, 6);
    ctx.shadowBlur = 0;
  } else if(t.type === 'splash'){
    ctx.fillStyle = '#3b2f52';
    ctx.fillRect(-8, -9, 24, 18);
    ctx.fillStyle = def.color;
    ctx.beginPath(); ctx.arc(18, 0, 9, 0, Math.PI*2); ctx.fill();
    ctx.fillStyle = '#1a1226';
    ctx.beginPath(); ctx.arc(18, 0, 5, 0, Math.PI*2); ctx.fill();
  }
  
  ctx.restore();
  
  // center dome
  ctx.beginPath(); ctx.arc(p.x, p.y, 9, 0, Math.PI*2);
  ctx.fillStyle = def.color;
  ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,0.35)';
  ctx.beginPath(); ctx.arc(p.x-3, p.y-3, 3.5, 0, Math.PI*2); ctx.fill();
}
```

Good enough.

Now, the empty slot:
```js
function drawSlot(i){
  const p = SLOTS[i];
  ctx.save();
  ctx.setLineDash([6,6]);
  ctx.lineDashOffset = -gameTime*12;
  ctx.beginPath(); ctx.arc(p.x, p.y, 22, 0, Math.PI*2);
  ctx.strokeStyle = 'rgba(110,160,210,0.35)';
  ctx.lineWidth = 2;
  ctx.stroke();
  ctx.restore();
  // plus sign
  ctx.strokeStyle = 'rgba(110,160,210,0.25)';
  ctx.beginPath(); ctx.moveTo(p.x-7,p.y); ctx.lineTo(p.x+7,p.y); ctx.moveTo(p.x,p.y-7); ctx.lineTo(p.x,p.y+7); ctx.stroke();
}
```

Good.

Now let's write everything out properly. I'll be careful with ordering of function declarations (function declarations are hoisted, so fine).

Let me also handle the `toast` display: centered text near the top of the play area.

```js
if(toastTime > 0){
  ctx.globalAlpha = Math.min(1, toastTime*2);
  ctx.textAlign='center';
  ctx.font = 'bold 22px system-ui';
  ctx.fillStyle = '#ffd166';
  ctx.fillText(toastMsg, W/2, 90);
  ctx.globalAlpha = 1;
}
```

And the wave announcement: bigger, centered.

Let's just use toast for both.

Now let me write the final code.

One more thing: `requestAnimationFrame` loop and initial `last = performance.now()`.

Also, prevent arrow/space scrolling: `e.preventDefault()` for space.

Let me write it.

Also, I should double check `posAt` for `d` beyond PATH_LEN returns the last point. Yes.

Let's also make sure enemies that reach the base are removed and base HP decreases.

Let me now also handle: what if baseHP hits 0 mid-frame? Set state='gameover', restartTimer=3.

```js
function gameOver(){
  state = 'gameover';
  restartTimer = 3.5;
  shake = 20;
  spawnParticles(912, 260, '#ff5566', 40, 300, 1);
}
```

OK.

Let me now write out the entire file.

Also I want a subtle "danger" vignette when base HP is low. Optional, skip.

One more consideration: the render function's `ctx.save()`/`restore()` for shake — I do `ctx.save()` at the start and `ctx.restore()` after drawing the world, then draw the HUD without shake. Good.

Let me write the code now.

Also: `spawnParticles` signature (x, y, color, n, spd, life).

Let me write.

```js
function spawnParticles(x,y,color,n,spd,life){
  for(let i=0;i<n;i++){
    const a = Math.random()*Math.PI*2;
    const s = spd*(0.25+Math.random()*0.75);
    particles.push({
      x, y, vx: Math.cos(a)*s, vy: Math.sin(a)*s,
      life: life*(0.6+Math.random()*0.6), max: life, color,
      r: 1.5 + Math.random()*2.5
    });
  }
}
```

And particle rendering:
```js
for(const p of particles){
  const a = Math.max(0, p.life / p.max);
  ctx.globalAlpha = a;
  ctx.fillStyle = p.color;
  ctx.beginPath(); ctx.arc(p.x, p.y, p.r*a, 0, Math.PI*2); ctx.fill();
}
ctx.globalAlpha = 1;
```

Good.

Now, writing out.

Let me handle the projectile rendering:
```js
for(const pr of projectiles){
  ctx.save();
  ctx.shadowColor = pr.color;
  ctx.shadowBlur = 10;
  ctx.fillStyle = pr.color;
  ctx.beginPath();
  ctx.arc(pr.x, pr.y, pr.kind === 'splash' ? 5 : 3.5, 0, Math.PI*2);
  ctx.fill();
  ctx.restore();
}
```

Beams:
```js
for(const b of beams){
  const a = b.life / b.max;
  ctx.globalAlpha = a;
  ctx.strokeStyle = b.color;
  ctx.lineWidth = 4;
  ctx.shadowColor = b.color;
  ctx.shadowBlur = 14;
  ctx.beginPath(); ctx.moveTo(b.x1,b.y1); ctx.lineTo(b.x2,b.y2); ctx.stroke();
  ctx.shadowBlur = 0;
  ctx.globalAlpha = 1;
}
```

OK.

Now, writing the whole file. Let me be careful and complete.

Actually, one thing about the laser: it fires every 0.2s, and each shot creates a beam with life 0.08. So beams are visible most of the time. Good.

Let me write out.

Final check on the `update` order and the between-wave logic. Let me restructure:

```js
if(state === 'playing'){
  if(autoPlay) aiUpdate(dt);
  
  // spawn
  if(spawnQueue.length > 0){
    spawnTimer -= dt;
    while(spawnQueue.length > 0 && spawnTimer <= 0){
      spawnEnemy(spawnQueue.shift());
      spawnTimer += spawnInterval;
    }
  }
  
  // enemies
  ...
  
  // towers
  ...
  
  // projectiles
  ...
  
  // wave state
  if(phase === 'between'){
    betweenTimer -= dt;
    if(betweenTimer <= 0){ startWave(wave+1); }
  } else {
    if(spawnQueue.length === 0 && enemies.length === 0){
      const bonus = 20 + wave*6;
      gold += bonus;
      score += 50 + wave*10;
      phase = 'between';
      betweenTimer = 4;
      toast('WAVE ' + wave + ' CLEARED   +' + bonus + 'g', 2);
    }
  }
}
```

Careful: `startWave` sets phase='wave'. Then next frame, if enemies is empty and spawnQueue is... it will be non-empty. Fine.

But there's a subtle bug: after `startWave(wave+1)` inside the between block, the `else` branch isn't executed this frame (it's an if/else). Next frame, phase==='wave' and spawnQueue has items → no clear. Good.

Another subtle issue: at the very start, startGame() calls startWave(1) which sets spawnQueue. Then in the first update, phase==='wave' and spawnQueue non-empty. Good.

OK.

Now `spawnInterval` is a global set in startWave.

Let me write it all out now.

Let me also double check the AI's wave starting doesn't conflict: aiUpdate is called at the top of the playing block, before the wave-state block. So if the AI calls startWave during 'between', phase becomes 'wave', and then the wave-state block's `if(phase === 'between')` is false, and the else branch checks spawnQueue.length===0 — it's not empty. Good.

Alright. Writing.

One more: `betweenTimer < 2.0` with betweenTimer starting at 4. So AI waits 2 seconds. Good.

Let me write the final code.

Also I realize I should double-check the enemy "hitFlash" rendering — `e.hitFlash > 0 ? '#ffffff' : e.color`.

OK.

Let me write out the complete HTML.

Actually, one more thought on making the demo look good in 30 seconds: the base HP should be visible and the gold should tick up. Good.

Let me write.

For the base HP bar in the HUD I use BASE_MAX = 20.

Let me finalize.

Also — `towers.findIndex(t => !t)` — towers is an array of 8 with nulls. Works.

Writing now.

Let me also add a small detail: draw the path with a glow so it looks nice.

```js
function drawPath(){
  ctx.lineJoin = 'round';
  ctx.lineCap = 'round';
  
  ctx.beginPath();
  ctx.moveTo(PATH[0].x, PATH[0].y);
  for(let i=1;i<PATH.length;i++) ctx.lineTo(PATH[i].x, PATH[i].y);
  
  ctx.strokeStyle = 'rgba(60,110,160,0.18)';
  ctx.lineWidth = 46;
  ctx.stroke();
  
  ctx.strokeStyle = '#1b2734';
  ctx.lineWidth = 36;
  ctx.stroke();
  
  ctx.strokeStyle = '#243447';
  ctx.lineWidth = 28;
  ctx.stroke();
  
  ctx.save();
  ctx.setLineDash([12,16]);
  ctx.lineDashOffset = -gameTime*30;
  ctx.strokeStyle = 'rgba(120,180,240,0.3)';
  ctx.lineWidth = 3;
  ctx.stroke();
  ctx.restore();
}
```

Note: I need to rebuild the path for each stroke? No, the path is retained in the current path state. Actually, calling stroke() multiple times with the same path works — the path stays until beginPath(). Yes, that's fine.

Good.

Now writing the final file.

Let me make sure about the order of drawing: path, then slots (towers on top), then enemies, projectiles, particles.

Actually towers should be drawn above the path but enemies above towers? Enemies walk on the path, towers are off the path. Draw order: path, slots/towers, enemies, projectiles, particles. Fine.

Let me write it.

Final code:

I'll write it now in full.

const BASE_MAX = 20;

Let me handle the initial `state = 'menu'`.

And in `update`, `if(state === 'menu' && autoPlay) startGame();`

But startGame sets state='playing'. Good.

Hmm, but the very first frame: `update(dt)` is called with state='menu' and autoPlay=true → startGame(). Then the rest of update runs with state='playing'. Actually no — the check `if(state === 'menu' && autoPlay)` should be placed before the `if(state === 'playing')` block. Let me put it at the top of update, right after the particle updates.

Actually, simpler: at the very start, just call startGame() and set state='playing' directly if autoPlay. Let's handle it in the update function:

```js
function update(dt){
  gameTime += dt;
  ...
  if(state === 'menu' && autoPlay){ startGame(); }
  
  if(state === 'playing'){ ... }
  else if(state === 'gameover'){ ... }
}
```

Good.

Now writing.

I think I'm ready. Let me produce the final file.

Let me count the total lines... it'll be long but that's fine.

One last thing — the `toast` function name might conflict. It's fine.

Writing now.