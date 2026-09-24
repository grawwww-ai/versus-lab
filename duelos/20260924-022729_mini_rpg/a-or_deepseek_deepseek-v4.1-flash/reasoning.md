We need to create a single HTML file game. Let me design carefully.

Key features:
- Pixel art drawn in code (canvas, procedural pixel art).
- Tiled world: village, forest, dungeon.
- NPCs with dialogue boxes.
- Hero with animated walk in 4 directions.
- Monsters patrol and chase.
- Combat with damage numbers.
- Experience and level-up.
- Inventory with items.
- Quest "find the amulet" with visible objective.
- Day-night tint.
- Sound (WebAudio, no music — "music-free sound" means sound effects without music).
- Minimap.
- Autoplay demo ON by default, AI controls hero: walks world, talks to NPC, fights monster, completes quest step.
- P toggles autoplay; any control key press stops autoplay and returns control.
- Controls shown on screen at start.

Let me write it.

Architecture:
- Canvas full window, scaled pixel art. Use an offscreen tile rendering approach: draw tiles as small pixel patterns.
- World: grid of tiles, e.g., 64x64 tiles of 16px each. Tile types: grass, path, water, tree, house wall, house roof, dungeon floor, dungeon wall, sand, flowers.
- Camera follows hero.

Let me plan the world generation deterministically with a seeded RNG.

World layout: 64x64.
- Village in the top-left region (x 4..20, y 4..20): houses, paths, NPCs.
- Forest in middle/right (trees scattered).
- Dungeon: an entrance in the north-east or south; inside, separate map? Simpler: one big map with dungeon area in the bottom-right corner with stone walls, and the amulet inside guarded by a boss monster.

Actually simplest: single map with three regions. Dungeon region: bottom-right quadrant with walls, floor tiles, torches, and the amulet chest at the end.

Quest: Talk to Elder NPC in village → get quest "Find the Amulet". Then find the amulet in the dungeon (pick up item). Return to elder → complete.

Demo AI: 
1. Walk to elder, talk (dialogue).
2. Then walk toward dungeon, fighting monsters along the way (attack when near).
3. Pick up amulet.
4. Return to elder, talk → quest complete.

That's a good demo loop.

To make sure it happens within 30 seconds, need decent speed. Let's make hero speed ~60 px/s at 16px tiles = ~3.75 tiles/sec. Distance from village to dungeon maybe 40 tiles = 640px → ~11s. With fights and dialogue, maybe 25-30s. Let's make the world a bit smaller: 48x48 tiles. Village at left, dungeon at bottom-right, forest between.

Let's design map 48x48 tiles, 16px tiles → 768x768 px world.

Layout:
- Village: x 2..16, y 2..16. Grass, houses at certain spots, path.
- Forest: x 16..40, y 0..32, trees scattered.
- Dungeon: x 30..46, y 30..46: stone walls forming rooms, entrance from forest.
- Water lake maybe at bottom-left.

Hmm, keep it manageable. Let's procedurally place but with fixed structure.

Let me define tile codes:
0 = grass
1 = grass2 (variant)
2 = path/dirt
3 = water
4 = tree (solid)
5 = wall (house wall, solid)
6 = roof (solid)
7 = door (walkable, decorative)
8 = stone floor (dungeon)
9 = stone wall (solid)
10 = sand
11 = flowers
12 = amulet pedestal (walkable-ish, item)
13 = bush (solid? walkable maybe not)
14 = torch

Collision: solid tiles: tree, wall, roof, water, stone wall, bush.

Rendering pixel art: For each tile, draw a 16x16 base color plus a few pixels detail. To be efficient, pre-render each tile type to an offscreen canvas 16x16 and blit. That's the way.

Actually to get nicer pixel art, I'll draw per-tile-type functions on a 16x16 offscreen canvas with deterministic detail.

Sprites: hero 16x24? Let's do 16x16 for simplicity but character drawn as ~12x16 within. Draw procedurally with per-direction frames.

Hero sprite: I'll draw a small character: head with hair, body tunic, legs. 4 directions, 4 frames each (2 walk frames + idle). Let's do 4-frame walk cycle.

Pre-render hero frames to offscreen canvases at 16x16 (scaled 1x), then draw scaled.

Let me write a generic function to make a sprite from a string art map with a palette. That's the cleanest for pixel art:

```js
const PAL = { '.':null, 'k':'#1a1a2e', 's':'#f2c49b', ... };
function makeSprite(rows, pal){ ... }
```

Yes! Use ASCII art with palette mapping. That gives real pixel art drawn in code.

Hero 16x16, drawn facing down, up, left, right with 2 walk frames each.

Let me design the hero as 12 wide x 16 tall roughly.

Hero down (frame 0):
```
................
................
.....kkkkk......
....kbbbbbk.....
...kbsssssbk....
...ksskssksk....  eyes
...ksssssssk....
...kksssskk.....
....kggggk......  tunic
...kggggggk.....
..ksggggggsk....  arms skin
..ksggggggsk....
....kppppk......  pants
....kppppk......
....kk..kk......
....kk..kk......
```
Hmm let me be careful with widths. Let's use 16 columns each row.

Actually let's simplify: I'll write a helper that draws sprites via code with rects rather than ASCII — but ASCII is more "pixel art drawn in code". I'll do ASCII; it's fine, just need to be careful.

Let me make hero 12x16 (width 12, height 16) and center it in a 16x16 canvas with offset 2.

Hero down frame A:
```
row0:  ............
row1:  ....kkkk....
row2:  ...khhhhk...
row3:  ..khhhhhhk..
row4:  ..khsssssk..
row5:  ..ksskskssk.   -> hmm width 12
```
Let me just carefully make 12-char rows.

Legend:
- `.` transparent
- `k` outline dark (#20182c)
- `h` hair (#6b3f1f) brown
- `s` skin (#f0c090)
- `e` eye (#202030)
- `g` tunic green (#3fa34d)
- `d` tunic dark (#2b7a36)
- `b` belt (#8a5a2b)
- `p` pants (#3b4a8a)
- `o` boots (#6b4a2b)

Hero down:
```
"....kkkk....",
"...khhhhk...",
"..khhhhhhk..",
"..khsssshk..",
"..ksesesk...",   hmm need 12
```
Let me count: "....kkkk...." = 4+4+4 = 12 ✓.
"...khhhhk..." = 3+1+4+1+3 = 12 ✓
"..khhhhhhk.." = 2+1+6+1+2 = 12 ✓
"..khsssshk.." = 2+1+1+4+1+1+2 = 12 ✓ (k h ssss h k)
"..kseeses k" hmm. Let's do "..ksesesk..." no.

Let me do face row: "..ks e s e s k" -> 2 + 1 + 1+1+1+1+1+1 + ... I need 12 total: `..k` (3) + `sese` ... 

Simpler: face row = "..kseesk...." no.

OK: characters: positions 0..11.
Row 4 (eyes): pos0 '.', 1 '.', 2 'k', 3 's', 4 'e', 5 's', 6 'e', 7 's', 8 'k', 9 '.', 10 '.', 11 '.' → "..ksesesk..." wait that's 12? ".." =2, "k"=3, "s"=4,"e"=5,"s"=6,"e"=7,"s"=8,"k"=9, then "..."=12. Yes: "..ksesesk..." has: . . k s e s e s k . . . = 12 ✓. Hmm but that's "ksesesk" - 7 chars from index 2 to 8. Good.

Row 5 (mouth/chin): "..ksssssk..." = . . k s s s s s k . . . = 12 ✓
Row 6 (neck/shoulders): "..kkggggkk.." = . . k k g g g g k k . . = 12 ✓
Row 7 (torso): ".kggggggggk." hmm width. Let's do ".kggggggggk." = . k g*8 k . = 12 ✓
Row 8 (torso w/ arms): "ksgggggggsk." hmm. Let's do "ksgggggggsk." = k s g g g g g g g s k . = 12 ✓ but asymmetric. Use "ksgggggggsk" is 11... k,s,7g,s,k = 11. Need 12. "k s ggggggg s k ." Let's just do: ".ksggggggsk." = . k s g g g g g g s k . = 12 ✓. Hmm arms outside at pos 2 and 9.
Row 9 (torso): ".kggggggggk." again? Let's do belt: ".kbbbbbbbbk." 
Row 10 (pants): "..kpppppp k.." → "..kppppppk.." = 2+1+6+1+2 = 12 ✓
Row 11: "..kppppppk.."
Row 12: "..kpp..ppk.." = 2+1+2+2+2+1+2 = 12 ✓
Row 13: "..kpp..ppk.."
Row 14: "..koo..ook.." = 12 ✓
Row 15: "..kkk..kkk.." = 2+3+2+3+2 = 12 ✓

Total 16 rows ✓.

Hmm row 14/15 boots. Fine.

Walk frame B: legs alternate — one leg forward. E.g. row 12: "..kpppp k..." Let's just shift: 
Row 12: "...kppppk..." hmm.

For frame B, make legs together-ish and add a slight body bob. Simpler: frame A = legs apart, frame B = legs together, plus body shifted down 1px on B. Actually classic: two frames alternate leg positions. I'll do:

Frame B rows 12-15:
"..kppppppk.."
"..kpp..ppk.."
"..koo..ook.."
"..kkk..kkk.."
and shift whole sprite down? Let's not shift; instead alternate:
Frame A legs: left leg forward, right leg back.
Frame B legs: right leg forward, left leg back.

I'll just make:
Frame A rows 12-15:
```
"..kppppppk..",
"..kpp..ppk..",
"..koo..ook..",
"...kk..kk..."
```
Frame B:
```
"..kppppppk..",
"..kpp..ppk..",
"..koo..ook..",
"..kk....kk.."
```
Eh, subtle. Good enough — with bob it'll read as walking. Let's also make frame B one row shorter at top (bob down): I'll draw frame B shifted down by 1 pixel in canvas... that changes total height. Alternative: draw the sprite at y+1 for frame B. I'll handle by drawing with an offset when rendering (bobOffset). Actually simpler: pre-render frames, and for frame B, draw into canvas at y offset 1. Fine.

Let me just do 4-frame walk cycle: [A, idle, B, idle]. Idle = frame A with legs together. Eh, I'll do frames: A, mid, B, mid.

I'll just generate: frames array with the leg rows varying:
frame0: legs apart
frame1: legs together (both centered)
frame2: legs apart (mirrored)
frame3: legs together

Simplify: I'll create for each direction a base body and 4 leg variants. That's a lot of ASCII. Let's just do 2 frames per direction and cycle [0,1,0,1] but with bob. Fine. Actually let's do 4 frames: [0, 1, 0, 2] where 2 is slightly different. Meh. 2 frames is fine for pixel art.

I'll define per direction: 2 frames. Down, Up, Left, Right. Right = mirrored Left. So I need Down x2, Up x2, Left x2 = 6 sprites, plus mirroring for right.

Left sprite: profile view.
```
"....kkkk....",
"...khhhhk...",
"..khhhhhhk..",
"..khsssshk..",
"..khesssk...",  eye on left
"..ksssssk...",
"...kggggk...",
"..kggggggk..",
"..kggggggk..",
"..kbbbbbbk..",
"..kppppppk..",
"..kppppppk..",
"...kppppk...",
"...kppppk...",
"...kooo k...",
```
Hmm need care with widths. I'll write them carefully in code.

Actually, maybe simpler and still good: define the sprite as a function drawing rects programmatically for each direction/frame. But ASCII is more fun and readable. Let's just be careful.

Alternatively: I can define ONE 12x16 down sprite and derive up/left by code transformations (up = down with no eyes, hair covering; left = narrower). That's hacky.

I'll write ASCII carefully. Let's do it.

Common palette:
```
'.': null
'k': '#1b1224'  outline
'h': '#7a4a21'  hair
's': '#f2c79a'  skin
'e': '#241a2e'  eye
'g': '#4fae55'  tunic
'd': '#2f7a3a'  tunic dark
'b': '#8a5a2b'  belt
'p': '#3b4a8a'  pants
'o': '#6b4a2b'  boots
```

DOWN frame 0 (12x16):
```
r0  "....kkkk...."
r1  "...khhhhk..."
r2  "..khhhhhhk.."
r3  "..khsssshk.."
r4  "..ksesesk..."   -> wait need 12: "..ksesesk..." is 12? count: . . k s e s e s k . . . = 12 ✓
r5  "..ksssssk..."   count: . . k s s s s s k . . . = 12 ✓
r6  "..kkggggkk.."   = 12 ✓
r7  ".kggggggggk."   = . k g g g g g g g g k . = 12 ✓
r8  "ksgggggggsk."   hmm arms: k s g g g g g g g s k . = 12 ✓ but left arm at x0. Let's use ".ksggggggsk." = . k s g g g g g g s k . = 12 ✓
r9  ".kggggggggk."   
r10 ".kbbbbbbbbk."   
r11 "..kppppppk.."   
r12 "..kppppppk.."   
r13 "..kpp..ppk.."   
r14 "..koo..ook.."   
r15 "..kkk..kkk.."   
```
Wait r11/r12 pants then r13 split legs. OK.

Hmm r7 ".kggggggggk." gives 10 wide with k at 1 and 10. r8 ".ksggggggsk." k at 1, s at 2, g 3-8, s at 9, k at 10. Good, arms outside tunic? Actually arms should be at sides: s at 2 and 9, tunic at 3-8. Fine.

DOWN frame 1 (walk): shift legs:
```
r13 "..kpp..ppk.." -> "...kppppk..." hmm
```
Let's do frame1 legs:
```
r11 "..kppppppk.."
r12 "..kppppppk.."
r13 "..kpp..ppk.."
r14 "..koo..ook.."
r15 "...kk..kk..."   (feet together - one lifted)
```
Meh. Let's do frame 1 with legs:
```
r13 "...kppppk..."
r14 "...kooo k..."  
```
Ugh widths.

Frame 1 legs (12 wide):
r13 "..kppppppk.." 
r14 "..kppppppk.." 
r15 "..kkkkkkkk.."  → hmm.

I'll just accept: frame1 = frame0 but with r14/r15 changed:
r14 "...kooo k..." no.

Let's do:
frame0 legs: r13 "..kpp..ppk..", r14 "..koo..ook..", r15 "..kkk..kkk.."
frame1 legs: r13 "..kppppppk..", r14 "..koooooook.." (12? . . k o o o o o o o k . . = 13, no).

frame1: r13 "..kppppppk.." (12 ✓), r14 "..koooook..." hmm . . k o o o o o k . . . = 12 ✓, r15 "...kkkkkk..." = . . . k k k k k k . . . = 12 ✓.

OK that works: frame1 legs together. Combined with bob (draw 1px lower) it reads as walking.

Actually for walking, alternate between legs apart and legs together is standard enough.

UP frame: same as down but hair covers face:
```
r0  "....kkkk...."
r1  "...khhhhk..."
r2  "..khhhhhhk.."
r3  "..khhhhhhk.."
r4  "..khhhhhhk.."
r5  "..khhhhhhk.."
r6  "..kkhhhhkk.."
r7  ".kggggggggk."
r8  ".ksggggggsk."
r9  ".kggggggggk."
r10 ".kbbbbbbbbk."
r11 "..kppppppk.."
r12 "..kppppppk.."
r13 "..kpp..ppk.."
r14 "..koo..ook.."
r15 "..kkk..kkk.."
```
Good.

LEFT frame:
```
r0  "....kkkk...."
r1  "...khhhhk..."
r2  "..khhhhhhk.."
r3  "..khhsssk..."   hmm
```
Let's do:
r0 "....kkkk...."
r1 "...khhhhk..."
r2 "..khhhhhhk.."
r3 "..khhsssk..."  = . . k h h s s s k . . . = 12 ✓
r4 "..khsessk..."  = . . k h s e s s k . . . = 12 ✓ hmm eye at pos 5
r5 "..khssssk..."  wait that's . . k h s s s s k . . . = 12 ✓
r6 "...kggggk..."  = 12? . . . k g g g g k . . . = 12 ✓
r7 "..kggggggk.."  = 12 ✓
r8 "..kggggggk.."  
r9 "..kggggggk.."
r10 "..kbbbbbbk.."
r11 "..kppppppk.."
r12 "..kppppppk.."
r13 "...kppppk..."
r14 "...kooo k..."  no → "...koook...." = . . . k o o o k . . . . = 12 ✓
r15 "...kkkkk...." = . . . k k k k k . . . . = 12 ✓

Frame1 for left: legs together variation:
r13 "...kppppk..."
r14 "..kooook...." hmm.

Let me just define left frame1 = left frame0 with r13-15 replaced:
r13 "...kppppk..."
r14 "...koooook.."  → . . . k o o o o o k . . = 12 ✓
r15 "...kkkkkk..." → 12 ✓

Hmm, inconsistent but fine.

Actually, to save effort: I'll define frames for down, up, left, and for frame1 I'll just programmatically alter: shift the whole sprite down by 1 and swap legs. Simpler: just use 2 frames where frame 1 is the same sprite but drawn 1px lower with legs modified... 

You know what, let me simplify: I'll write a function that builds sprite rows from a base with a "legs" parameter. Define base rows 0-12 (head+torso) and leg rows for 3 variants. Then compose.

Let me define:

```js
function buildChar(dir, frame) {
  const head = {...}
}
```

Hmm, overengineering. Let's just write out 8 sprite definitions (down0, down1, up0, up1, left0, left1) and mirror left for right. It's ~8*16 lines. That's fine, just tedious. Let me be careful and write them.

Actually I can reduce: frame1 = frame0 with legs replaced. So define leg sets:

legsApart = ["..kpp..ppk..","..koo..ook..","..kkk..kkk.."]  (rows 13,14,15)
legsTogether = ["..kppppppk..","..koooook...","...kkkkkk..."] 

Hmm "..koooook..." is 12? . . k o o o o o k . . . = 12 ✓
"...kkkkkk..." = . . . k k k k k k . . . = 12 ✓

Wait but rows 11,12 are "..kppppppk.." twice for both frames. OK so I'll define body rows 0..12 and then append legs.

Body rows for down (13 rows: 0-12):
```
"....kkkk....",
"...khhhhk...",
"..khhhhhhk..",
"..khsssshk..",
"..ksesesk...",
"..ksssssk...",
"..kkggggkk..",
".kggggggggk.",
".ksggggggsk.",
".kggggggggk.",
".kbbbbbbbbk.",
"..kppppppk..",
"..kppppppk.."
```
That's 13 rows ✓ (0-12).

Down legs apart (3 rows): ["..kpp..ppk..","..koo..ook..","..kkk..kkk.."] → total 16 ✓
Down legs together: ["..kppppppk..","..koooook...","...kkkkkk..."] → 16 ✓

Hmm "..koooook..." has boots 5 wide. ok.

Up body rows:
```
"....kkkk....",
"...khhhhk...",
"..khhhhhhk..",
"..khhhhhhk..",
"..khhhhhhk..",
"..khhhhhhk..",
"..kkhhhhkk..",
".kggggggggk.",
".ksggggggsk.",
".kggggggggk.",
".kbbbbbbbbk.",
"..kppppppk..",
"..kppppppk.."
```
Left body rows:
```
"....kkkk....",
"...khhhhk...",
"..khhhhhhk..",
"..khhsssk...",
"..khsessk...",
"..khssssk...",
"...kggggk...",
"..kggggggk..",
"..kggggggk..",
"..kggggggk..",
"..kbbbbbbk..",
"..kppppppk..",
"..kppppppk.."
```
Left legs apart: ["...kppppk...","...koook....","...kkkkk...."]
count: "...kppppk..." = . . . k p p p p k . . . = 12 ✓
"...koook...." = . . . k o o o k . . . . = 12 ✓
"...kkkkk...." = . . . k k k k k . . . . = 12 ✓

Left legs together: ["...kppppk...","..kooooook..","..kkkkkkkk.."]
"..kooooook.." = . . k o o o o o o k . . = 13 ✗. Let's use "..koooook..." = . . k o o o o o k . . . = 12 ✓
"..kkkkkk...." hmm. "...kkkkkk..." = 12 ✓.

Fine, use left legs together = ["...kppppk...","..koooook...","...kkkkkk..."].

OK good enough. Actually left legs apart and together are nearly identical. Whatever — the bob will sell it. Let me add a bob: for frame 1, draw the sprite 1px down? That would clip the bottom. Instead draw frame 1 at same y but the whole sprite shifted... eh. Let's just skip bob and rely on legs.

Hmm, actually, let me add a slight bob by making the walking frame's body 1px shorter at top: replace row 0 with transparent and shift... too complex. Skip.

Monsters: slime, bat, skeleton. Let's do:
- Slime (green) in forest.
- Bat in forest/dungeon.
- Skeleton in dungeon.
- Boss: dark knight guarding amulet? Maybe just a strong skeleton.

Monster sprites 16x16, 2 frames each. Simpler shapes.

Slime (12x10 within 16x16):
```
"............",
"............",
"............",
"............",
"....kkkk....",
"..kkggggkk..",
".kgggggggg k."  ...
```
Let me do 16 wide for monsters, easier.

Slime 16x12 (drawn at bottom of 16x16):
```
"................",
"................",
"................",
"................",
"................",
"................",
".....kkkkkk.....",
"...kkggggggkk...",
"..kgggggggggg k."  hmm
```
Let me carefully do 16-char rows.

Slime frame0:
```
r0  "................"
r1  "................"
r2  "................"
r3  "................"
r4  "................"
r5  ".....kkkkkk....."   5+6+5=16 ✓
r6  "...kkggggggkk..."   3+2+6+2+3=16 ✓
r7  "..kggggggggggk.."   2+1+10+1+2=16 ✓
r8  "..kggeggggeggk.."   2+1+2+1+4+1+2+1+2 = 16 ✓ (k g g e g g g g e g g k) → that's k + "ggeggggegg" + k = 1+10+1=12, plus 2+2 = 16 ✓. Let me verify "ggeggggegg" = g,g,e,g,g,g,g,e,g,g = 10 ✓
r9  ".kgggggggggggg k." hmm need 16. ".kggggggggggggk." = 1+1+12+1+1 = 16 ✓
r10 ".kggggggggggggk."
r11 ".kkkkkkkkkkkkkk." = 1+14+1 = 16 ✓
```
Good. Frame1: squashed — shift up? Just make it 1 row shorter and wider:
```
r6  "....kkkkkkkk...."
r7  "..kkggggggggkk.."
r8  ".kggggggggggggk."
r9  ".kggeggggegggk.."  hmm
```
Simplify frame1 = frame0 shifted down 1 row (squash). I'll just draw frame0 and for frame1 draw with 1px vertical offset. Easier: define one slime sprite, and animate by y-offset ±1. 

Yes! Animation via offset is fine and simple. Let me do that for monsters: single sprite, bobbing offset.

Bat: 
```
"................",
"................",
"..k..........k..",
".kk..........kk.",
".kbk...kk...kbk.",   
```
Hmm. Let's do:
```
r0 "................"
r1 "................"
r2 "................"
r3 ".kk..........kk."
r4 ".kbk..kkkk..kbk."
r5 ".kbbk.kbbk.kbbk."
r6 "..kbbkkbbkkbbk.."
r7 "...kbbbbbbbbk..."
r8 "....kbkbbkbk...."
r9 ".....kkkkkk....."
r10"................"
...
```
Eh, rough but okay. Let me refine later.

Skeleton:
```
r0 "................"
r1 "................"
r2 "....kkkkkk......"
r3 "...kwwwwwwk....."
r4 "...kwewwewk....."
r5 "...kwwwwwwk....."
r6 "....kwmmwk......"
r7 ".....kwwk......."
r8 "...kkwwwwkk....."
r9 "..kwwwwwwwwk...."
r10 "..kwkwwwwkwk...."
r11 "..kwwwwwwwwk...."
r12 "...kwwwwwwk....."
r13 "....kwkkwk......"
r14 "....kwk.kwk....."
r15 "....kk...kk....."
```
Rough. Widths: need 16 each. I'll count when writing.

This is getting long. Let me be pragmatic: I'll write sprites as arrays and validate by eye. Slight width mismatches would break rendering, so I'll add a helper that pads rows to the max width. That way minor width errors won't crash. 

Good idea: `makeSprite(rows, palette)` — compute width = max row length, height = rows.length, and pad. 

Now, rendering scale: canvas internal resolution, say 480x270 (16:9) then scale up. Tile 16px → 30x16.9 tiles visible. Good.

Actually for pixel art crispness, use canvas width = 480, height = 270, with CSS scaling to fit, image-rendering: pixelated.

Hmm, but with 16px tiles, hero is 16px tall, ~1/17 of screen height. That's a bit small but fine for top-down RPG. Let's use canvas 400x225 (scale 4 → 1600x900). Or 480x270 scale 3 = 1440x810. Let's do 480x270 and scale to fit window with integer-ish scaling via CSS.

Actually simpler: set canvas.width=480, height=270, and CSS width:100vw; height:100vh; object-fit... no, canvas doesn't do object-fit well. Use CSS `width:100%; height:100%` with `image-rendering:pixelated` — it stretches. Aspect ratio may distort. Use a container with aspect-ratio. Let's do:

```css
body{margin:0;background:#0a0a12;display:flex;align-items:center;justify-content:center;height:100vh;overflow:hidden}
canvas{image-rendering:pixelated;image-rendering:crisp-edges;max-width:100vw;max-height:100vh;aspect-ratio:16/9;}
```
With canvas width/height attributes 480x270 and CSS max-width/max-height, it will scale preserving aspect ratio? Not automatically. Let's use JS resize to set style width/height based on window and integer scale. That's most reliable.

```js
function resize(){
  const s = Math.max(1, Math.min(Math.floor(innerWidth/480), Math.floor(innerHeight/270)));
  canvas.style.width = (480*s)+'px';
  canvas.style.height = (270*s)+'px';
}
```
If window smaller than 480, s=1 and it overflows; acceptable. Actually use non-integer fallback: if s<1 use fraction. Let's do:
```js
let s = Math.min(innerWidth/480, innerHeight/270);
s = s >= 1 ? Math.floor(s) : s;
```
Fine.

Now game logic.

World gen: 48x48 tiles. Let me define regions.

Actually let me use a handcrafted-ish layout generated with helper functions:
- Fill all with grass.
- Village region: x in [2,16], y in [2,16] → dirt paths, houses.
- Lake: circle at (6, 34) radius 4 → water.
- Forest: trees scattered where x>18 or y>18 (outside village), using seeded RNG, plus a border of trees around the map.
- Dungeon: rectangle x in [30,46], y in [30,46] with stone walls border and floor inside, entrance at top-left corner of the dungeon area (x=30..31, y=30 open from outside? Actually make the dungeon entrance a gap in the wall).

Hmm, dungeon at bottom-right of a 48x48 map: x 28..47, y 28..47. That's 20x20. Rooms inside with walls.

Path from village to dungeon: draw a dirt path.

Let me write:

```js
const W=48,H=48;
const T={GRASS:0,GRASS2:1,DIRT:2,WATER:3,TREE:4,WALL:5,ROOF:6,DOOR:7,FLOOR:8,SWALL:9,SAND:10,FLOWER:11,BUSH:12,TORCH:13,RUG:14};
const SOLID = {3:1,4:1,5:1,6:1,9:1,12:1};
```

Map array `map[y][x]`.

Generation:
```js
for all: map = GRASS or GRASS2 based on noise
// border trees
for x,y on border (0 and W-1): TREE

// village
region x 3..17, y 3..17: 
  fill with DIRT? No, keep grass, put paths.
  paths: horizontal at y=10 from x=3..20, vertical at x=10 from y=3..20.
  houses: at (4,4) 4x3, (12,4) 4x3, (4,14) 4x3, (13,13) 4x3.
    House: roof rows on top (2 rows), wall rows below, door in middle bottom.
  Well/fountain maybe.
```

Houses as tiles: place WALL for the body, ROOF for the top rows. Solid.

Let me write a `placeHouse(x,y,w,h)`:
- for i in 0..w-1: map[y][x+i] = ROOF (top row), map[y+1][x+i] = ROOF
- for j in 2..h-1: map[y+j][x+i] = WALL
- door: map[y+h-1][x+floor(w/2)] = DOOR (walkable, decorative)

Actually door walkable would let you walk into the house which has no interior. Make door solid too? Let's make DOOR solid (it's a closed door). Actually make it walkable but the house is solid behind — no, door leads into wall. Just make DOOR solid.

Hmm, simpler: door tile is solid.

Trees in forest: random with density based on distance from village.

Path from village to dungeon: a dirt path going right and down.

Let me just do: for x from 18 to 30, map[10][x] = DIRT (horizontal path at y=10). Then for y from 10 to 36, map[y][30] = DIRT. Hmm but dungeon is at 28..47. Let's put dungeon x 32..46, y 30..46, and the entrance at (32, 30)... path along y=10 to x=34, then down x=34 to y=30. Hmm, but the dungeon's top wall is at y=30. Entrance gap at x=34,y=30.

Let's define dungeon rect: x0=32,y0=30,x1=46,y1=46.
- Border walls SWALL at perimeter.
- Interior FLOOR.
- Entrance gap: (34,30) and (34,31) → FLOOR (passage).
- Inner rooms: a few wall segments.
- Amulet at (44,44) with pedestal.

Path: DIRT from village to dungeon entrance: 
- horizontal at y=10 from x=16 to x=34
- vertical at x=34 from y=10 to y=30.

But the forest trees shouldn't block the path — generate trees first, then carve path. Order: terrain → forest trees → village → path → dungeon.

Also ensure path doesn't overwrite dungeon.

Torches inside dungeon: TORCH tiles on walls (decorative, non-solid? put on floor adjacent).

OK.

Monsters: spawn a few in forest and dungeon.
- 4 slimes in forest
- 3 bats in forest/dungeon
- 3 skeletons in dungeon
- 1 boss skeleton near amulet

Each monster: {x,y (pixel), type, hp, maxhp, speed, dmg, exp, state:'patrol'|'chase', patrol target, dir, frame, attackCD}.

NPCs: 
- Elder (in village near center) → gives quest.
- Merchant (sells? just dialogue).
- Kid (dialogue).

Quest states: 
0 = not started, 1 = seeking amulet, 2 = have amulet, 3 = done.

Objective text displayed in HUD: e.g. "Quest: Find the Amulet — Talk to the Elder" / "— Search the dungeon" / "— Return to the Elder" / "— Complete!".

Combat: action combat. Hero attacks with SPACE/J when near a monster, dealing damage; monsters deal contact damage with cooldown. Damage numbers float up.

Hero: hp, maxhp, level, exp, expNext, atk, inventory.

Items: 
- Health Potion (use with 1/2 keys? or from inventory)
- Sword (starting)
- Amulet (quest item)
- Gold coins? 

Inventory UI: press I to toggle. Show items with counts. Use potion with number keys or click.

Let's keep it simple: inventory panel toggled with I, shows items. Press 1 to use Health Potion.

Day-night: cycle over ~120 seconds, tint overlay with color+alpha. Also affect light radius in dungeon? Keep simple: global tint.

Minimap: top-right corner, small canvas drawn each frame showing explored tiles... just show the whole map at 1px per tile scaled. 48x48 → draw at 2px per tile = 96x96. Show hero dot, NPCs, monsters, amulet.

Sound: WebAudio oscillators for: attack (short noise/square blip), hit, level up, pickup, dialogue blip, footstep maybe.

Autoplay AI: 
State machine:
- If quest state 0: go to elder, when in range, press talk (advance dialogue).
- If quest state 1: go to dungeon amulet position; attack monsters in range; when reaching amulet, pick up (auto pickup).
- If quest state 2: go back to elder, talk.
- If quest state 3: wander/patrol, maybe fight monsters.

Also handle dialogue boxes: when dialogue is open, AI advances it after a delay.

Dialogue system: array of lines, shown one at a time, advance with SPACE/E/Enter or click.

Let's write the dialogue:
```js
let dialogue = {active:false, lines:[], index:0, speaker:''};
```
When active, game input for movement disabled (or allowed? typically disabled). AI advances.

Now the demo must stop as soon as player presses a control key. So on keydown of any control key (arrows, WASD, space, etc.), set autoplay=false. But P toggles it. So handle P separately.

Let's write the code.

Main loop with requestAnimationFrame, dt clamped.

Camera: centered on hero, clamped to world bounds. Since world is 48*16=768 px and canvas 480x270, camera clamps.

Hero pixel position: x,y center. Collision: AABB 10x10 against solid tiles.

Let's define hero hitbox as a rect of w=10,h=10 centered at (x, y+4) maybe. Simpler: hero position is the center of a 12x12 box, and sprite drawn at (x-6, y-8-... ). Let's do: hero.x, hero.y = center of feet area. Sprite drawn at (x-6, y-14) with sprite 12x16 → feet at y-14+16 = y+2. Hmm.

Let's just make: hero.x, hero.y is the center of the collision box (10x10). Sprite 12x16 drawn at (x-6, y-10) so the sprite's bottom is at y+6, slightly below the box. That's typical top-down.

Actually simpler: hero.x,y = top-left of collision box (10x10). Draw sprite at (x-1, y-6). Whatever, I'll tune.

Let me use: entity position = center of a 12x12 collision box. Draw sprite centered horizontally: sx = x - 6, sy = y + 6 - 16 = y - 10. So sprite bottom aligns with box bottom (y+6). Good.

Collision check: for a box (x-6,y-6,12,12), check tiles overlapping.

```js
function isSolid(px,py){ const tx=Math.floor(px/16), ty=Math.floor(py/16); if(tx<0||ty<0||tx>=W||ty>=H) return true; return SOLID[map[ty][tx]]===1; }
function canMove(x,y){ 
  const hw=6, hh=6;
  return !isSolid(x-hw,y-hh) && !isSolid(x+hw,y-hh) && !isSolid(x-hw,y+hh) && !isSolid(x+hw,y+hh);
}
```
Corner sampling is fine.

Movement: axis-separated.

Now rendering tiles: pre-render each tile type into a 16x16 canvas. Then draw visible tiles.

Tile drawing functions: I'll draw with a small pixel-art helper:

```js
function tileCanvas(drawFn){ const c=document.createElement('canvas'); c.width=16;c.height=16; const g=c.getContext('2d'); drawFn(g); return c; }
```

For grass: fill base #4a8a3c, then random darker/lighter pixels using deterministic RNG.
Actually to avoid tiling artifacts, make 4 variants of grass.

Let me create:
- grass: base '#4e9a45', speckles '#3f7d38' and '#5fae52'
- dirt: base '#b08a5a', speckles '#9a7648'
- water: base '#2f6fb0', waves '#4f92d4'
- tree: grass base + trunk + canopy circles
- wall: '#c8a878' with '#a08050' bricks
- roof: '#a04a3a' with '#8a3a2c' lines
- door: brown with knob
- floor (dungeon): '#5a5566' with darker specks
- swall: '#3a3548' bricks
- sand: '#d8c890'
- flower: grass + colored dots
- bush: green blob
- torch: floor + torch

Let me write drawing code using a helper `px(g,x,y,w,h,color)`.

For deterministic randomness in tiles, use a seeded RNG per tile type.

OK, let's write it.

```js
function rng(seed){ let s=seed>>>0; return ()=>{ s = (s*1664525 + 1013904223)>>>0; return s/4294967296; }; }
```

Tile drawing:

```js
function makeTile(fn){const c=document.createElement('canvas');c.width=16;c.height=16;const g=c.getContext('2d');fn(g);return c;}
```

Grass:
```js
function drawGrass(g,seed){
  const r=rng(seed);
  g.fillStyle='#4e9a45'; g.fillRect(0,0,16,16);
  for(let i=0;i<26;i++){ const x=(r()*16)|0, y=(r()*16)|0; g.fillStyle = r()<0.5?'#458a3d':'#57a84e'; g.fillRect(x,y,1,1);}
}
```
Make 4 grass variants with different seeds. And store in array.

Tree: grass base then trunk and canopy.
```js
function drawTree(g,seed){
  drawGrass(g,seed);
  g.fillStyle='#5a3a1e'; g.fillRect(7,10,2,5);
  // canopy
  g.fillStyle='#2f6b2a';
  g.fillRect(3,2,10,8); ... 
}
```
Let's do a rounded canopy:
```
rows: y=1: x 5..10
y=2: x 3..12
y=3..6: x 2..13
y=7: x 3..12
y=8: x 4..11
```
with a lighter top highlight.

I'll write a helper `blob(g, cx, cy, rx, ry, color)` drawing an ellipse in pixels. Or just fillRect rows.

Let me write:
```js
function drawTree(g,seed){
  drawGrass(g,seed);
  g.fillStyle='#5b3a1c'; g.fillRect(7,11,2,5);
  const dark='#245c22', mid='#2f7a2c', lite='#3f9a38';
  const rows=[[6,10,0],[4,12,1],[3,13,2],[2,14,3],[2,14,4],[2,14,5],[3,13,6],[4,12,7],[6,10,8]];
  ...
}
```
Simplify: draw three overlapping rects.

```js
g.fillStyle=dark; g.fillRect(2,3,12,7);
g.fillStyle=mid;  g.fillRect(3,2,10,7);
g.fillStyle=lite; g.fillRect(5,3,4,3);
```
Plus corner trimming:
```js
g.clearRect(2,3,1,1) etc.
```
Meh, just do rounded via drawing circles in pixel grid. Let's do:

```js
function pixCircle(g,cx,cy,r,color){
  g.fillStyle=color;
  for(let y=-r;y<=r;y++)for(let x=-r;x<=r;x++){
    if(x*x+y*y<=r*r+r*0.5) g.fillRect(cx+x,cy+y,1,1);
  }
}
```
That's fine for 16x16.

Tree: 
```js
drawGrass(g,seed);
g.fillStyle='#4a2f14'; g.fillRect(7,9,2,6);
pixCircle(g,8,7,5,'#1e5c1c');
pixCircle(g,8,6,4,'#2f7a2c');
pixCircle(g,6,5,2,'#4aa03a');
```
Good enough.

Wall (house): 
```js
g.fillStyle='#c9a26b'; g.fillRect(0,0,16,16);
g.fillStyle='#a8814f';
for(let y=0;y<16;y+=4) g.fillRect(0,y,16,1);
for(let y=0;y<16;y+=4) for(let x=(y/4%2)*4;x<16;x+=8) g.fillRect(x,y,1,4);
```
Roof:
```js
g.fillStyle='#b04a3a'; g.fillRect(0,0,16,16);
g.fillStyle='#8f382c';
for(let x=0;x<16;x+=4) g.fillRect(x,0,1,16);
for(let y=0;y<16;y+=4) g.fillRect(0,y,16,1);
```
Door:
```js
g.fillStyle='#c9a26b'; g.fillRect(0,0,16,16);  // wall bg
g.fillStyle='#5a3a1e'; g.fillRect(3,2,10,14);
g.fillStyle='#7a5228'; g.fillRect(4,3,8,13);
g.fillStyle='#e0c060'; g.fillRect(10,9,2,2); // knob
```
Water:
```js
g.fillStyle='#2a5fa8'; fillRect;
g.fillStyle='#3d7fd0'; some horizontal dashes
```
Floor (dungeon):
```js
g.fillStyle='#4a4556'; g.fillRect(0,0,16,16);
speckles '#3d3948','#565166'
```
Stone wall:
```js
g.fillStyle='#2e2a3d'; g.fillRect(0,0,16,16);
g.fillStyle='#3f3a52'; bricks
g.fillStyle='#4d4765' highlights
```
Path/dirt:
```js
g.fillStyle='#b39062'; speckles
```
Sand: similar lighter.

Flower: grass + flower pixels.

Bush: grass + green blob.

Torch: floor + torch stick + flame (animated? keep static, maybe animate flame with 2 frames). Keep static.

OK. Now let's think about the main draw order:
1. Clear.
2. Compute camera.
3. Draw tiles (visible range).
4. Draw entities sorted by y (hero, npcs, monsters, items).
5. Draw floating damage numbers.
6. Draw HUD: hearts/hp bar, exp bar, level, quest objective, minimap, controls hint, autoplay indicator.
7. Draw day-night tint overlay.
8. Draw dialogue box.

Tint should be over world but under HUD. So draw tint after entities, before HUD.

Day-night: t = (time % DAY_LEN)/DAY_LEN. Color from a gradient: dawn orange, day clear, dusk orange, night blue. Overlay with globalAlpha.

```js
function tintColor(t){
  // t 0..1, 0 = midnight
  // 0.0-0.2 night->dawn, 0.2-0.3 dawn, 0.3-0.7 day, 0.7-0.8 dusk, 0.8-1 night
}
```
Simple: compute a color and alpha:
- night: rgba(20,25,80,0.45)
- dawn/dusk: rgba(255,140,60,0.25)
- day: rgba(255,255,255,0) 

I'll interpolate.

Let's start day at t=0.35 (morning) so the demo looks bright.

Cycle length: 90 seconds.

Minimap: draw at top-right. 48x48 tiles at 2px = 96x96 px. In a 480x270 canvas that's big but ok. Let's do 1.5px? Use 2px per tile → 96x96. Place at x=480-100=380, y=6. Fine.

Actually 96px wide on a 480px screen is 20%. OK.

Minimap draws: for each tile, a color. Plus entities as dots.

Colors: grass #3a7a35, dirt #a8895c, water #2a5fa8, tree #1e4a1c, wall #c9a26b, roof #b04a3a, floor #4a4556, swall #2e2a3d.

Draw hero as white dot, npc yellow, monster red, amulet gold.

HUD: 
- Top-left: HP bar, EXP bar, Level.
- Quest objective below.
- Bottom-left: controls hint (fade after 15s? keep it, it's required to be shown at the start).
- Top-right: minimap.
- Autoplay indicator: "DEMO (P to play)" blinking.

Dialogue box: bottom center, dark panel with border, speaker name, text, "▼ SPACE".

Now input:
- Arrow keys / WASD: move
- SPACE / J: attack (and advance dialogue)
- E / ENTER: interact / talk
- I: inventory
- 1: use potion
- P: toggle autoplay

Any of these keys pressed → autoplay off (except P).

Let me now write the game.

Let's structure:

```js
const canvas=..., ctx=...;
const VW=480, VH=270;
```

World constants.

Let me write out the code.

```js
// ---------- utils
function rng(seed){let s=seed>>>0;return()=>{s=(s*1664525+1013904223)>>>0;return s/4294967296;};}
```

Sprite maker:
```js
function makeSprite(rows, pal){
  const w=Math.max(...rows.map(r=>r.length)), h=rows.length;
  const c=document.createElement('canvas'); c.width=w;c.height=h;
  const g=c.getContext('2d');
  for(let y=0;y<h;y++){const row=rows[y];
    for(let x=0;x<row.length;x++){const ch=row[x]; const col=pal[ch]; if(col){g.fillStyle=col;g.fillRect(x,y,1,1);} }}
  return c;
}
```

Mirror function:
```js
function mirrorSprite(src){
  const c=document.createElement('canvas');c.width=src.width;c.height=src.height;
  const g=c.getContext('2d'); g.translate(src.width,0); g.scale(-1,1); g.drawImage(src,0,0); return c;
}
```

Now sprites.

PAL:
```js
const CP={
 '.':null,
 'k':'#1b1224',
 'h':'#7a4a21',
 's':'#f2c79a',
 'e':'#241a2e',
 'g':'#4fae55',
 'd':'#2f7a3a',
 'b':'#8a5a2b',
 'p':'#3b4a8a',
 'o':'#5c3f22',
 'w':'#e8e8f0', // bone
 'r':'#d04040',
 'y':'#f0d060',
 'c':'#4a4a5a'
};
```

Hero bodies:

```js
const BODY_DOWN=[
"....kkkk....",
"...khhhhk...",
"..khhhhhhk..",
"..khsssshk..",
"..ksesesk...",
"..ksssssk...",
"..kkggggkk..",
".kggggggggk.",
".ksggggggsk.",
".kggggggggk.",
".kbbbbbbbbk.",
"..kppppppk..",
"..kppppppk.."
];
```
Wait "..ksesesk..." — count again: `..`(2) `k`(3) `s`(4) `e`(5) `s`(6) `e`(7) `s`(8) `k`(9) `...`(12). Yes 12. Hmm but that's "ksesesk" = k,s,e,s,e,s,k = 7 chars at indices 2-8. Good.

Hmm, but row 3 "..khsssshk.." = . . k h s s s s h k . . = 12 ✓
Row 5 "..ksssssk..." = . . k s s s s s k . . . = 12 ✓ — wait that's k at 2, s at 3-7 (5 s), k at 8. Good.

Row 6 "..kkggggkk.." = . . k k g g g g k k . . = 12 ✓
Row 7 ".kggggggggk." = . k g g g g g g g g k . = 12 ✓
Row 8 ".ksggggggsk." = . k s g g g g g g s k . = 12 ✓
Row 10 ".kbbbbbbbbk." = 12 ✓
Row 11 "..kppppppk.." = 12 ✓

Good.

BODY_UP:
```js
const BODY_UP=[
"....kkkk....",
"...khhhhk...",
"..khhhhhhk..",
"..khhhhhhk..",
"..khhhhhhk..",
"..khhhhhhk..",
"..kkhhhhkk..",
".kggggggggk.",
".ksggggggsk.",
".kggggggggk.",
".kbbbbbbbbk.",
"..kppppppk..",
"..kppppppk.."
];
```

BODY_LEFT:
```js
const BODY_LEFT=[
"....kkkk....",
"...khhhhk...",
"..khhhhhhk..",
"..khhsssk...",
"..khsessk...",
"..khssssk...",
"...kggggk...",
"..kggggggk..",
"..kggggggk..",
"..kggggggk..",
"..kbbbbbbk..",
"..kppppppk..",
"..kppppppk.."
];
```
Check "..khhsssk..." = . . k h h s s s k . . . = 12 ✓
"..khsessk..." = . . k h s e s s k . . . = 12 ✓
"...kggggk..." = . . . k g g g g k . . . = 12 ✓
"..kggggggk.." = 12 ✓
"..kbbbbbbk.." = 12 ✓

Legs:
```js
const LEGS_A=["..kpp..ppk..","..koo..ook..","..kkk..kkk.."];
const LEGS_B=["..kppppppk..","..koooook...","...kkkkkk..."];
```
Hmm for left-facing, legs should be narrower. Use same; acceptable.

Actually for LEFT, use:
LEGS_L_A=["...kppppk...","...koook....","...kkkkk...."]
LEGS_L_B=["...kppppk...","..koooook...","...kkkkkk..."]

Fine.

Build:
```js
const heroFrames={
  down:[makeSprite(BODY_DOWN.concat(LEGS_A),CP), makeSprite(BODY_DOWN.concat(LEGS_B),CP)],
  up:[...],
  left:[...],
};
heroFrames.right=[mirror(heroFrames.left[0]),mirror(heroFrames.left[1])];
```

Monsters sprites.

Slime:
```js
const SLIME=[
"................",
"................",
"................",
"................",
"................",
".....kkkkkk.....",
"...kkggggggkk...",
"..kggggggggggk..",
"..kggeggggeggk..",
".kggggggggggggk.",
".kggggggggggggk.",
".kkkkkkkkkkkkkk."
];
```
Check row 5: ".....kkkkkk....." = 5+6+5=16 ✓
row 6: "...kkggggggkk..." = 3+2+6+2+3=16 ✓
row 7: "..kggggggggggk.." = 2+1+10+1+2=16 ✓
row 8: "..kggeggggeggk.." = 2+1+ "ggeggggegg"(10) +1+2 = 16 ✓
row 9: ".kggggggggggggk." = 1+1+12+1+1=16 ✓
row 10: same ✓
row 11: ".kkkkkkkkkkkkkk." = 1+14+1=16 ✓

Height 12 rows. But sprite canvas is 16 tall, drawn at feet.

For slime palette use different greens: 'g':'#3fc060', 'k':'#1b1224', 'e':'#ffffff'? Let's use a separate palette with 'e' as eyes (dark).

Actually let's define SLIME_PAL = {'.':null,'k':'#12401e','g':'#4ad06a','e':'#0d2b14'}.

Bat:
```js
const BAT=[
"................",
"................",
"................",
"................",
".k............k.",
".kk..........kk.",
".kbk...kk...kbk.",
".kbbk.kbbk.kbbk.",
"..kbbkkbbkkbbk..",
"...kbbbbbbbbk...",
"....kbkbbkbk....",
".....kkkkkk.....",
"................",
"................",
"................",
"................"
];
```
Check row 4: ".k............k." = 1+1+12+1+1 = 16 ✓
row 5: ".kk..........kk." = 1+2+10+2+1 = 16 ✓
row 6: ".kbk...kk...kbk." = 1+3+3+2+3+3+1 = 16 ✓
row 7: ".kbbk.kbbk.kbbk." = 1+4+1+4+1+4+1 = 16 ✓
row 8: "..kbbkkbbkkbbk.." = 2+ "kbbkkbbkkbbk"(12) +2 = 16 ✓
row 9: "...kbbbbbbbbk..." = 3+ "kbbbbbbbbk"(10) +3 = 16 ✓
row 10: "....kbkbbkbk...." = 4+ "kbkbbkbk"(8) +4 = 16 ✓
row 11: ".....kkkkkk....." = 5+6+5 = 16 ✓

BAT_PAL = {'.':null,'k':'#241a2e','b':'#8a5ad0'} purple bat. Eyes maybe.

Skeleton:
```js
const SKEL=[
"................",
"................",
".....kkkkkk.....",
"....kwwwwwwk....",
"....kwewwewk....",
"....kwwwwwwk....",
".....kwwwwk.....",
"....kkwwwwkk....",
"...kwwwwwwwwk...",
"..kwkwwwwwwkwk..",
"..kwkwwwwwwkwk..",
"...kwwwwwwwwk...",
"....kwwwwwwk....",
"....kwk..kwk....",
"....kwk..kwk....",
"....kk....kk...."
];
```
Check row2: ".....kkkkkk....." = 16 ✓
row3: "....kwwwwwwk...." = 4+8+4 = 16 ✓
row4: "....kwewwewk...." = 4+8+4=16 ✓ ("kwewwewk" = 8)
row5: same as 3 ✓
row6: ".....kwwwwk....." = 5+6+5 = 16 ✓
row7: "....kkwwwwkk...." = 4+8+4 = 16 ✓
row8: "...kwwwwwwwwk..." = 3+10+3 = 16 ✓
row9: "..kwkwwwwwwkwk.." = 2+12+2 = 16 ✓ ("kwkwwwwwwkwk" = 12)
row10: same
row11: "...kwwwwwwwwk..." ✓
row12: "....kwwwwwwk...." ✓
row13: "....kwk..kwk...." = 4+3+2+3+4 = 16 ✓
row14: same
row15: "....kk....kk...." = 4+2+4+2+4=16 ✓

SKEL_PAL={'.':null,'k':'#2a2438','w':'#e6e6ee','e':'#d04040'}

Good.

Now the world map.

```js
const MW=48, MH=48;
let map = new Uint8Array(MW*MH);
function setT(x,y,t){ if(x>=0&&y>=0&&x<MW&&y<MH) map[y*MW+x]=t; }
function getT(x,y){ if(x<0||y<0||x>=MW||y>=MH) return T.TREE; return map[y*MW+x]; }
```

Generation with a seeded rng.

```js
function genWorld(){
  const r=rng(12345);
  for(let y=0;y<MH;y++)for(let x=0;x<MW;x++){
    let t = T.GRASS;
    if(r()<0.25) t=T.GRASS2;
    if(r()<0.04) t=T.FLOWER;
    setT(x,y,t);
  }
  // border trees
  for(let x=0;x<MW;x++){setT(x,0,T.TREE);setT(x,1,T.TREE);setT(x,MH-1,T.TREE);setT(x,MH-2,T.TREE);}
  for(let y=0;y<MH;y++){setT(0,y,T.TREE);setT(1,y,T.TREE);setT(MW-1,y,T.TREE);setT(MW-2,y,T.TREE);}
  
  // lake bottom-left
  for(let y=0;y<MH;y++)for(let x=0;x<MW;x++){
    const dx=x-8, dy=y-36;
    if(dx*dx+dy*dy<36) setT(x,y,T.WATER);
  }
  ...
}
```

Hmm, the village at top-left (x 3..17, y 3..17), lake at bottom-left (8,36). Dungeon bottom-right. Forest between.

Forest: trees scattered in the middle band. Let's define forest region as x from 18 to 46, y from 2 to 28 (excluding path and dungeon), plus region x 2..46, y 18..28.

Simpler: scatter trees everywhere outside village and dungeon with density function:
```js
for(let y=2;y<MH-2;y++)for(let x=2;x<MW-2;x++){
  if(inVillage(x,y)||inDungeon(x,y)) continue;
  const d = distance to village center;
  if(d>12 && r()<0.35) setT(x,y,T.TREE);
}
```
But the lake would be overwritten. Order: lake after trees.

Let me structure:
1. base grass
2. border trees
3. forest trees (with noise)
4. lake
5. village (clear + houses + paths)
6. main path
7. dungeon

For the main path, we want it clear of trees. Do path after trees.

Path: horizontal at y=10, x from 16 to 34; vertical at x=34, y from 10 to 30.
Hmm the village is at x 3..17, y 3..17. So path from village edge (x=17) at y=10 going east to x=34, then south to y=30 where dungeon entrance is.

Wait, dungeon x0=32..46, y0=30..46. Entrance at (34,30). Good.

Also add some dirt paths in the village.

Trees near the path: clear a 1-tile margin around the path so it doesn't look like trees grow on the path edge... Actually trees adjacent to the path is fine, they're just next to it.

Let's do the forest density: use a smooth noise-ish function. Simple approach:

```js
for(let y=2;y<MH-2;y++)for(let x=2;x<MW-2;x++){
  if(x>=2&&x<=18&&y>=2&&y<=18) continue; // village
  if(x>=30&&y>=28) continue; // dungeon area
  const n = r();
  const edge = (x<8||x>40||y<6||y>42)?0.55:0.3;
  if(n<edge) setT(x,y,T.TREE);
}
```
Hmm, that gives ~30% trees which is a lot but makes a forest. With collision, the hero might get stuck in the AI path. Need to ensure the path is clear (we carve it after).

But the AI walks along the path... Actually AI uses simple steering, might get stuck on trees. Let's add pathfinding-lite: the AI moves toward the target, and if blocked, tries perpendicular. Better: use a simple BFS on the tile grid to compute a path! That's robust. The map is 48x48 = 2304 tiles, BFS is cheap. Recompute path every ~0.5s or when target changes.

Yes, let's do BFS pathfinding for the AI. That guarantees it can navigate. And I'll make sure the path from village to dungeon exists by carving.

Actually, if BFS fails (target unreachable), fall back to direct movement.

Good. Let's implement `findPath(startX,startY,goalX,goalY)` returning array of tile coords. Use BFS with 4-neighbors over non-solid tiles. 2304 tiles — trivial.

For AI: follow waypoints, recompute path every 0.7s or when reaching a waypoint.

The hero moves at 60px/s → 3.75 tiles/s. Path from village (10,10) to dungeon (44,44) is ~50 tiles → 13s. Plus fights and dialogue. Should complete within ~25-30s. Let's speed up slightly: hero speed 72 px/s. And monsters slow.

Hmm, but the demo needs to show: walks world, talks to NPC, fights a monster, completes a quest step. All within 30s. Let's make sure the first monster encounter happens early. Put a slime near the path in the forest at around (22,10).

Also, make the AI take the shortest route which passes near monsters.

Let me place monsters deliberately:
- slime at (22,11) — near the path
- slime at (26,8)
- bat at (30,14)
- slime at (24,20)
- skeleton at (36,34), (40,40), (43,42) in dungeon
- boss skeleton at (44,44) guarding amulet? Then amulet pickup after killing it.

Actually, the amulet is at (44,44). Let's put the boss right next to it. AI must kill it. Might take a while. Let's make the boss not too tanky.

Hero: level 1, atk 5, hp 30. Monster hp: slime 12, bat 10, skeleton 18, boss 40. Damage: slime 2, bat 3, skeleton 4, boss 6.

Hero attack: 5 damage + level scaling. Attack cooldown 0.35s. Slime dies in 3 hits (~1s). Fine.

Hero takes damage from contact: monsters deal damage on touch with 1s cooldown each.

Hero heals? Let's give hero regen slowly or potions. Hero has 3 potions.

Let's also give exp: slime 8, bat 10, skeleton 15, boss 40. Level up at 20 exp * level.

Level up: +10 maxhp, +2 atk, full heal.

OK.

Now, the "quest step" completion: Talk to elder → quest starts (step 1). Get amulet (step 2). Return to elder (step 3 complete). The demo should complete at least one step. Actually the requirement: "completes a step of the quest by itself". Ideally the whole quest. Let's aim for the whole thing in ~30-45s. Since we have 30s window for recording... it says the animation should show everything important within the first 30 seconds. Let's make it fast.

Speed things up: hero speed 80 px/s = 5 tiles/s. Path from village to dungeon: from (10,10) to (44,44) ≈ 34+34 = 68 tiles... that's 13.6s at 5 tiles/s. Plus fights. Hmm, ~20-25s total. Then return trip 13s more → 40s total. Too long for full quest in 30s.

Options: make the dungeon closer, or make the amulet closer. Let's shrink the world to 40x40 and place the dungeon closer.

Alternative: Have the elder give the quest, then the amulet is in a small dungeon closer. Let's redesign:

World 40x40 tiles (640x640 px).
- Village: x 2..14, y 2..14.
- Forest: middle.
- Dungeon: x 24..37, y 24..37 (14x14).
- Amulet at (35,35).
- Path from village (14,8) east to (26,8), then south to (26,24) entrance.

Hmm, distance from (10,10) to (35,35) = 25+25=50 tiles. At 5 tiles/s = 10s each way. 20s round trip + fights + dialogue ≈ 28s. Tight but okay.

Let's make hero speed 90 px/s = 5.6 tiles/s. Round trip ~18s. Good.

Actually, we could also have the elder be closer to the dungeon side of the village. Elder at (12,8). Path leads from there.

Let's finalize:
- MW=40, MH=40, tile 16 → world 640x640.
- Canvas 480x270 → shows 30x16.9 tiles. Good.

Village: x 2..14, y 2..14.
Houses at: (3,3,4,4), (9,3,4,4), (3,10,4,4). Elder NPC at (12,7). Merchant at (7,12). Kid at (5,6).

Paths: y=7 horizontal from x=3..15; x=7 vertical from y=3..14.

Hmm, let me just do simple: a horizontal dirt path at y=8 from x=2 to x=26, and vertical dirt at x=26 from y=8 to y=24.

Then the village sits around it.

Dungeon: x0=24, y0=24, x1=37, y1=37.
- Perimeter walls (SWALL).
- Entrance at (26,24) — gap in top wall, connecting to the vertical path.
- Interior FLOOR with some SWALL pillars/rooms.
- Amulet at (35,35).

Let's make the dungeon interior interesting: a couple of wall blocks.

```
// inner walls
for x in 28..33: swall at (x, 28)
for y in 30..34: swall at (33, y)
```
Something like that, leaving a path.

Let me just make sure it's connected. I'll do a simple layout:

Dungeon interior x 25..36, y 25..36.
Walls:
- row y=28: x from 25 to 32
- row y=32: x from 29 to 36
- col x=29: y from 28 to 32  → hmm this would block.

Let's do:
- Horizontal wall at y=28, x=25..31
- Horizontal wall at y=32, x=29..36
- Vertical wall at x=32, y=25..28
- Vertical wall at x=28, y=32..36

Path: enter at (26,24)→(26,25). Go down... at y=28 there's a wall from x=25..31, so x=26 blocked. Go right to x=32? But x=32 has a wall y=25..28. Hmm.

Let me be careful. Entrance at (26,24). Interior from y=25.
Wall at y=28 spans x=25..31. So to pass y=28, need x>=32 or x<=24 (but 24 is the outer wall). At x=32, vertical wall y=25..28 blocks. So go to x=33..36 at y=28? Yes, pass at x=33..36.

But wait, vertical wall at x=32, y=25..28 means to get from x=26 to x=33 at y=25..27, we can walk along y=26 or 27 rightward until x=31, then at x=32 there's a wall for y=25..28. So we must pass x=32 at y>28 or y<25. Hmm. So we'd have to go around... 

Let's simplify: no vertical wall in the top area. Just:
- Horizontal wall at y=28, x=25..31 (gap at x=32..36)
- Horizontal wall at y=32, x=29..36 (gap at x=25..28)
- Vertical wall at x=33, y=33..36 (decorative)

Path: enter (26,24) → down to (26,27) → blocked at y=28 for x<=31 → move right along y=27 to x=32 → down through (32,28),(32,29) → continue down to (32,31) → blocked at y=32 for x>=29 → move left along y=31 to x=28 → down through (28,32),(28,33) → then right to (35,35)? 

Amulet at (35,35). From (28,33) go right along y=33 to x=35 → but vertical wall at x=33,y=33..36 blocks. Hmm.

Let me remove that vertical wall. Just two horizontal walls with gaps, and the amulet in the bottom-right.

Path: (26,24)→(26,27)→right to (32,27)→down to (32,31)→left to (28,31)→down to (28,35)→right to (35,35). 

That's a nice winding dungeon path. Total dungeon traversal ~20 tiles. Fine.

Torches along the way: at (26,25), (32,29), (28,33)... place TORCH tiles on floor (walkable, decorative).

OK.

Now monsters:
Forest: slime at (18,8) near path, slime at (22,6), bat at (20,12), slime at (16,10).
Dungeon: skeleton at (30,26), skeleton at (32,30), skeleton at (28,34), boss skeleton at (34,35) near amulet.

Hmm, the AI path passes (32,29)→(32,31), so skeleton at (32,30) is right on the path. Good for a fight.

Also the boss at (34,35) — the AI goes to (35,35) for the amulet, so it'll fight the boss.

Wait, but combat: AI needs to attack. Let's make AI: if a monster is within 40px, move toward it and attack when within 20px. Otherwise follow the path.

Actually simpler and more reliable: AI follows the path to the objective; if a monster is within 45px, target it, move to it and attack until dead, then resume path.

Now the elder: at (12,7)? Let's place NPCs on walkable tiles.

Let's lay out the village:
- Houses: 
  - House A: x=3..6, y=3..6 (4x4)
  - House B: x=9..12, y=3..6
  - House C: x=3..6, y=10..13
- Paths: horizontal dirt y=8 from x=2..26; vertical dirt x=26 from y=8..24.
- Also a village square: dirt at x=8..14, y=7..9.

Elder at (13,7) standing on dirt near the path. Good — close to the east path.

Hmm, the elder should be near the start. Hero starts at (10,9).

Actually let's start hero at (10,10).

Elder at (13,8) → hero walks 3 tiles → talk. Good, quick.

Then the AI heads east along y=8 path to x=26, then south.

Wait, but I set the path at y=8. The elder at (13,8) is ON the path. Fine, NPCs block? Let's make NPCs non-solid so the hero can pass through... Actually better to make them solid so you bump into them. But then the AI path could be blocked. Let's make NPCs non-solid (walk through) to avoid pathing issues. Or make the path 2 tiles wide.

Simplest: NPCs are not solid. Fine.

Now: the amulet tile. It's an item entity at (35,35) — a floating amulet sprite with glow. Picked up when hero is within 10px.

Let's now write the AI.

```js
const ai = {
  path: [], pathIdx: 0, repathTimer: 0, target: null, state: 'idle', talkTimer:0
};
```

AI update each frame (when autoplay on):
1. If dialogue active: wait ~0.9s then advance dialogue. Return (no movement).
2. Determine objective:
   - quest.stage===0 → target = elder position, and interact when close.
   - quest.stage===1 → target = amulet position.
   - quest.stage===2 → target = elder position.
   - quest.stage===3 → wander / fight monsters.
3. If a monster is within 60px and alive → target = monster (move & attack).
4. Move along path toward target.

For the interaction: when within 24px of the elder and quest stage is 0 or 2, trigger interact (same as pressing E).

Let's implement.

Dialogue handling in AI: when dialogue.active, set a timer; every 0.8s advance one line. When dialogue ends, resume.

Now, damage numbers: array of {x,y,text,color,life,vy}.

Combat:
- Hero attack: on SPACE press (with cooldown 0.35s), create a hitbox in front of the hero (facing direction) of size ~20x16, offset 14px. Any monster overlapping takes damage. Show slash effect.
- Monster attack: contact damage — if monster overlaps hero and monster.attackCd<=0 → damage hero, monster.attackCd=1.0, knockback hero slightly, damage number.

Hero invulnerability: 0.6s after being hit.

Hero death: respawn at village with half hp? Let's just revive at the village start with full hp and lose nothing (or lose some exp). Keep it simple: revive at village.

Now, sound. WebAudio.

```js
let actx=null;
function ensureAudio(){ if(!actx) actx = new (window.AudioContext||window.webkitAudioContext)(); }
function beep(freq, dur, type='square', vol=0.06, slide=0){ ... }
```

Sounds:
- attack: quick down-sweep square
- hit: noise burst
- hurt: low square
- pickup: two rising notes
- levelup: arpeggio
- talk: short blip
- step: soft click

Need to resume audio context on first user gesture. For autoplay demo, audio may be blocked until interaction. That's fine; we'll try and catch.

Let's implement a simple `sfx(name)`.

Now the HUD.

Let me write the render code.

Screen coordinates: world → screen by subtracting camera.

Camera:
```js
cam.x = clamp(hero.x - VW/2, 0, MW*16 - VW);
cam.y = clamp(hero.y - VH/2, 0, MH*16 - VH);
```
MW*16 = 640, VW=480 → cam.x in [0,160]. MH*16=640, VH=270 → cam.y in [0,370]. OK.

Hmm, 640-270 = 370. Good.

Since the world is 640x640 and the view is 480x270, the view is quite large relative to the world. The minimap is less needed but still required. Fine.

Actually maybe make the world bigger for a better feel: 56x56 = 896px. Hmm, but then travel takes longer. Let's keep 40x40 but... hmm, actually the view showing 30x17 tiles of a 40x40 world means you see most of it. The minimap would be redundant.

Let's increase the world to 56x56 and keep the same relative layout scaled. Travel distance increases though.

Alternative: reduce the view size. Canvas 320x180 (16:9), showing 20x11 tiles. Then the world 40x40 feels bigger. And scaling: 320*4=1280, 320*5=1600. Good for recording.

Let's use canvas 320x180, tile 16. Scale to fit window (integer scale, typically 4-6x).

With 320x180 view, the world 640x640 → cam.x in [0,320], cam.y in [0,460]. Good.

Minimap 40x40 at 2px = 80x80. On a 320x180 screen that's 25% width. A bit big. Use 1.5px... let's use 2px but 80x80 in the corner. Hmm, that's large. Let's do the minimap at 1.5 px/tile = 60x60. Or draw the minimap scaled with a factor and just use drawImage of a pre-rendered 40x40 minimap canvas scaled 1.5x with imageSmoothing off. 

Actually simplest: pre-render the whole map to a 40x40 canvas once (1px per tile), then drawImage scaled by 1.6 → 64x64. With imageSmoothingEnabled=false it'll look blocky but fine.

Let's do scale 1.5 → 60x60. OK.

Hmm, 320x180 with a 60x60 minimap is 19% width, 33% height. Acceptable.

Let's go with canvas 320x180.

Fonts: draw text with ctx.font = '8px monospace' or use a custom pixel font? Canvas text at small sizes is ugly. Let's use a bitmap font drawn from code... that's a lot of work.

Alternative: use ctx.font = '8px "Courier New", monospace' and it'll be okay-ish. Since we can't load external fonts, system monospace is fine.

Actually for pixel-art aesthetics, I could render text at 2x then... no.

Let's just use canvas text with a monospace font at 8px/10px. It'll be readable when scaled 5x. Actually no — the canvas is 320x180 and scaled 5x, so an 8px font becomes 40px tall on screen. Very readable. Good.

Hmm, but the text will be scaled with nearest-neighbor which makes it look pixelated/blocky. That's actually fine for the aesthetic.

Let's use `ctx.font = 'bold 8px monospace'`. And `textBaseline='top'`.

Alright.

Let me now write everything.

Detailed code:

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Amulet of the Vale</title>
<style>...</style>
</head>
<body>
<canvas id="c" width="320" height="180"></canvas>
<script>
... game ...
</script>
</body>
</html>
```

Let me write the JS.

```js
(() => {
'use strict';

const VW=320, VH=180;
const canvas=document.getElementById('c');
const ctx=canvas.getContext('2d');
ctx.imageSmoothingEnabled=false;

function resize(){
  const s = Math.max(1, Math.min(window.innerWidth/VW, window.innerHeight/VH));
  const si = s>=1? Math.floor(s) : s;
  canvas.style.width=(VW*si)+'px';
  canvas.style.height=(VH*si)+'px';
}
window.addEventListener('resize',resize); resize();
```

Hmm if the window is smaller than 320x180, s<1 and si=s (fractional). Fine.

Now the tile constants and world gen.

Let me write it all out.

```js
const TS=16;
const MW=40, MH=40;
const T={GRASS:0,GRASS2:1,FLOWER:2,DIRT:3,WATER:4,TREE:5,BUSH:6,WALL:7,ROOF:8,DOOR:9,FLOOR:10,SWALL:11,TORCH:12};
const SOLID=new Uint8Array(16);
SOLID[T.WATER]=1;SOLID[T.TREE]=1;SOLID[T.BUSH]=1;SOLID[T.WALL]=1;SOLID[T.ROOF]=1;SOLID[T.DOOR]=1;SOLID[T.SWALL]=1;
```

Map:
```js
const map=new Uint8Array(MW*MH);
const setT=(x,y,t)=>{ if(x>=0&&y>=0&&x<MW&&y<MH) map[y*MW+x]=t; };
const getT=(x,y)=> (x<0||y<0||x>=MW||y>=MH)?T.TREE:map[y*MW+x];
```

World gen function.

```js
function genWorld(){
  const r=rng(98765);
  for(let y=0;y<MH;y++)for(let x=0;x<MW;x++){
    let t=T.GRASS;
    const n=r();
    if(n<0.3) t=T.GRASS2; else if(n<0.34) t=T.FLOWER;
    setT(x,y,t);
  }
  // border
  for(let i=0;i<MW;i++){setT(i,0,T.TREE);setT(i,1,T.TREE);setT(i,MH-1,T.TREE);setT(i,MH-2,T.TREE);}
  for(let i=0;i<MH;i++){setT(0,i,T.TREE);setT(1,i,T.TREE);setT(MW-1,i,T.TREE);setT(MW-2,i,T.TREE);}
  
  // forest
  for(let y=2;y<MH-2;y++)for(let x=2;x<MW-2;x++){
    if(x<=16 && y<=16) continue;       // village
    if(x>=22 && y>=22) continue;        // dungeon area
    if(r()<0.30) setT(x,y,T.TREE);
  }
  
  // lake bottom-left
  for(let y=0;y<MH;y++)for(let x=0;x<MW;x++){
    const dx=x-7, dy=y-32;
    if(dx*dx+dy*dy<25) setT(x,y,T.WATER);
  }
  ...
}
```

Hmm, lake at (7,32) radius 5 → x 2..12, y 27..37. That overlaps the village? Village y<=16, so no. OK.

Then village: clear the area and add houses.

```js
  // village ground
  for(let y=2;y<=15;y++)for(let x=2;x<=16;x++){
    if(getT(x,y)===T.WATER) continue;
    setT(x,y, r()<0.15?T.FLOWER:T.GRASS);
  }
  // paths
  for(let x=2;x<=26;x++) setT(x,8,T.DIRT);
  for(let y=8;y<=24;y++) setT(26,y,T.DIRT);
  for(let x=8;x<=14;x++){ setT(x,7,T.DIRT); setT(x,9,T.DIRT); }
  for(let y=7;y<=9;y++){ setT(8,y,T.DIRT); setT(14,y,T.DIRT); }
```

Hmm, the vertical path at x=26 from y=8 to y=24 goes through the forest. And the dungeon entrance is at (26,24). Good.

Wait, but the dungeon is at x 22..37, y 22..37 (I excluded that from forest). Let's define the dungeon as x0=22,y0=22,x1=37,y1=37. Entrance at (26,22)? But the path goes to y=24. Let me set the dungeon top wall at y=22 and entrance gap at (26,22),(26,23) as FLOOR, and the path from y=8 to y=24... it would pass through the dungeon wall region.

Let me redo: Dungeon outer rect x 22..37, y 22..37. Wall perimeter. Entrance gap at x=26, y=22 and y=23 → FLOOR (corridor).

Path vertical at x=26 from y=8 to y=21 (outside), then the entrance.

Hmm, but the path is dirt and the dungeon entrance corridor is floor. Fine, they connect.

Wait, the dungeon perimeter at y=22 spans x=22..37 with a gap at x=26. So the path at (26,21) is dirt, and (26,22) is floor. Good.

Let me set:
```js
// dungeon
const DX0=22,DY0=22,DX1=37,DY1=37;
for(let y=DY0;y<=DY1;y++)for(let x=DX0;x<=DX1;x++){
  const border = (x===DX0||x===DX1||y===DY0||y===DY1);
  setT(x,y, border?T.SWALL:T.FLOOR);
}
// entrance
setT(26,DY0,T.FLOOR); setT(26,DY0+1,T.FLOOR);
```
Wait DY0+1 = 23. Interior starts at y=23. So setT(26,22,FLOOR) and setT(26,23,FLOOR) — but 23 is interior anyway.

Actually interior is y 23..36. So just setT(26,22,T.FLOOR).

Inner walls:
```js
for(let x=DX0+1;x<=DX0+7;x++) setT(x, DY0+5, T.SWALL);   // y=27, x=23..29
for(let x=DX0+6;x<=DX1-1;x++) setT(x, DY0+9, T.SWALL);   // y=31, x=28..36
```
Hmm let me recompute with DY0=22:
- Wall row at y=27, x=23..29 (gap at x=30..36).
- Wall row at y=31, x=28..36 (gap at x=23..27).

Path: enter (26,22) → down (26,23)...(26,26) → at y=27 blocked for x<=29 → move right along y=26 to x=30 → down (30,27),(30,28),(30,29),(30,30) → at y=31 blocked for x>=28 → move left along y=30 to x=27 → down (27,31),(27,32)...(27,35) → then right along y=35 to x=35 → amulet at (35,35).

Wait, but I need to check the interior is connected. Yes.

Also add a couple of pillars.

Amulet at (35,35). Boss at (34,35).

Hmm, but the corridor to the amulet: from (27,35) going right along y=35 to (35,35). Any walls? No. Good.

Torches: at (26,24), (30,29), (27,33), (33,35). Set as T.TORCH (walkable, decorative).

Hmm, TORCH should be walkable so it doesn't block. But then the path can go over it. Fine. Actually torch on a wall looks better. Let's put torches on the SWALL tiles adjacent... but then they'd replace walls. Let's just put them on floor tiles as standing torches — walkable. Actually let's make them solid so they look like braziers. Hmm, could block the path. I'll place them off the main path and make them solid.

Eh, let's make them non-solid floor decorations. Simple.

OK, now the houses.

```js
function house(x,y,w,h){
  for(let j=0;j<h;j++)for(let i=0;i<w;i++){
    let t=T.WALL;
    if(j<2) t=T.ROOF;
    setT(x+i,y+j,t);
  }
  // door
  setT(x+((w/2)|0), y+h-1, T.DOOR);
}
house(3,3,4,4);
house(9,3,4,4);
house(3,11,4,4);
```
Hmm, house(3,3,4,4) → x 3..6, y 3..6. Roof rows y=3,4. Wall rows y=5,6. Door at (5,6).

house(9,3,4,4) → x 9..12, y 3..6.
house(3,11,4,4) → x 3..6, y 11..14.

Also a well or something in the village square. Skip.

NPCs: Elder at (13,8)? The path is at y=8. Let's put the elder at (13,7) (just north of the path). And the kid at (6,8), merchant at (10,9).

Hmm, actually let's put the elder right at the path junction so the AI reaches quickly. Elder at (13,8). Hero starts at (8,8) on the path.

Wait, hero start: let's use (9,8). Elder at (13,8). Distance 4 tiles = 64px. Quick.

NPC positions must be on walkable tiles. (13,8) is DIRT. Good.

Kid at (5,7)? Path at y=7 for x=8..14. (5,7) is grass. Fine, walkable.

Merchant at (12,10).

Now, quest logic:

```js
const quest={stage:0};
// 0: talk to elder
// 1: find amulet in dungeon
// 2: return to elder
// 3: complete
```

Objective text:
```js
function questText(){
  switch(quest.stage){
    case 0: return 'Talk to the Elder in the village';
    case 1: return 'Find the Amulet in the dungeon';
    case 2: return 'Return the Amulet to the Elder';
    case 3: return 'Quest complete!';
  }
}
```

Dialogue for the elder:
- stage 0: ["Ah, a traveler! Our village is in peril.", "The Amulet of the Vale was stolen.", "It lies deep in the dungeon to the south-east.", "Bring it back, hero!"] then quest.stage=1.
- stage 1: ["The dungeon lies to the south-east. Be careful!"]
- stage 2: ["You found it! The Amulet of the Vale!", "You are a true hero. Take this reward!"] then quest.stage=3, give reward (potion + gold + exp).
- stage 3: ["Thank you, hero. The vale is safe."]

Kid: ["I saw a big monster near the dungeon!", "It had glowing eyes!"]
Merchant: ["Potions for sale... oh, you're broke? Take one anyway."] gives a potion once.

Let's implement a generic NPC talk function.

Now, the interact key: E. When pressed and near an NPC, start dialogue.

Now let's write the entity update.

Hero:
```js
const hero={x:9*16+8, y:8*16+8, dir:'down', frame:0, animT:0, moving:false, hp:30, maxhp:30, level:1, exp:0, expNext:20, atk:5, speed:90, attackCd:0, invuln:0, hurtFlash:0};
```

Wait, hero speed 90 px/s = 5.6 tiles/s. That's fast. Maybe 80. Let's use 85.

Hmm, with 16px tiles and the hero 12px wide, 5 tiles/s is like 80px/s. That feels fast but it's fine for a demo.

Let's use 78 px/s. = 4.9 tiles/s.

Actually for the demo to be quick, faster is better. 90 it is. Hmm, but for a human player, 90px/s in a 320px wide view means crossing the screen in 3.5s. That's reasonable.

OK, 88.

Monsters:
```js
const monsters=[];
function addMonster(type,tx,ty){...}
```

Types config:
```js
const MON={
  slime:{hp:12, dmg:2, speed:22, exp:8, sprite:SLIME_SPRITE, pal:SLIME_PAL, chaseRange:70, w:12,h:12, name:'Slime'},
  bat:{hp:10, dmg:3, speed:40, exp:10, ...},
  skel:{hp:18, dmg:4, speed:30, exp:15, ...},
  boss:{hp:45, dmg:6, speed:26, exp:45, ...}
};
```

Monster update:
- If distance to hero < chaseRange and hero alive → chase.
- Else patrol: move toward patrol target; when reached, pick a new one nearby.
- Move with collision (simple: if blocked, pick a new direction).

Damage to hero on contact.

Let's write monster movement with the same canMove check.

Monsters can walk through each other (fine).

Now the AI.

```js
let autoplay=true;
const ai={path:[],pi:0,repath:0,talkTimer:0,target:null,mode:'idle'};
```

AI update:
```js
function updateAI(dt){
  if(dialogue.active){
    ai.talkTimer-=dt;
    if(ai.talkTimer<=0){ advanceDialogue(); ai.talkTimer=0.85; }
    return;
  }
  // pick target
  let goal=null, wantInteract=false;
  // nearest monster within 70px
  let best=null,bd=1e9;
  for(const m of monsters){ if(m.hp<=0) continue; const d=Math.hypot(m.x-hero.x,m.y-hero.y); if(d<bd){bd=d;best=m;} }
  if(best && bd<90){ ... attack it }
  else {
    if(quest.stage===0||quest.stage===2){ goal = {x:elder.x, y:elder.y}; wantInteract = quest.stage===0||quest.stage===2; }
    else if(quest.stage===1){ goal = amulet pos }
    else { wander }
  }
}
```

Hmm, if stage 1 and the hero has the amulet, stage becomes 2. Good.

Interaction with the elder: if within 22px, press interact.

But careful: the elder dialogue advances automatically. After dialogue ends, quest stage changes.

Let me structure the AI more concretely:

```js
function updateAI(dt){
  if(dialogue.active){
    ai.talkTimer-=dt;
    if(ai.talkTimer<=0){ ai.talkTimer=0.8; advanceDialogue(); }
    ai.moveX=0; ai.moveY=0; ai.attack=false;
    return;
  }
  ai.moveX=0;ai.moveY=0;ai.attack=false;
  
  // 1) target monster if close
  let mon=null, md=999;
  for(const m of monsters){ if(m.hp>0){ const d=Math.hypot(m.x-hero.x,m.y-hero.y); if(d<md){md=d;mon=m;} } }
  
  if(mon && md<110){
    // approach and attack
    if(md>22){ moveToward(mon.x,mon.y); }
    else { ai.attack=true; if(md>18) moveToward(mon.x,mon.y); }
    // also face it
    return;
  }
  
  // 2) objective
  let goal=null;
  if(quest.stage===0 || quest.stage===2){ goal={x:elder.x,y:elder.y}; }
  else if(quest.stage===1){ goal={x:amulet.x,y:amulet.y}; }
  
  if(goal){
    const d=Math.hypot(goal.x-hero.x,goal.y-hero.y);
    if(d<26 && (quest.stage===0||quest.stage===2)){ ai.interact=true; return; }
    followPath(goal.x,goal.y,dt);
  } else {
    // wander
    ...
  }
}
```

Hmm, "return" after setting attack. Let me restructure with a helper that sets ai.moveX/moveY.

`moveToward(tx,ty)`: sets dir based on the delta; the actual movement is applied in the hero update using the same code path as the keyboard.

Let's make the input object:
```js
const input={up:false,down:false,left:false,right:false,attack:false,interact:false};
```
For AI, set these directly.

Hero update:
```js
let dx=0,dy=0;
if(input.left)dx--; if(input.right)dx++; if(input.up)dy--; if(input.down)dy++;
```
Normalize.

For AI, we set input.left/right/up/down based on direction to target, and input.attack.

That's clean! The AI just presses the buttons.

So:
```js
function aiPress(tx,ty){
  const dx=tx-hero.x, dy=ty-hero.y;
  input.left = dx<-6; input.right = dx>6;
  input.up = dy<-6; input.down = dy>6;
}
```
And for facing/attacking, the hero's facing comes from the movement direction. When attacking, we want to face the monster. Let's add: if attacking and not moving, face the target.

Hmm, the hero's direction updates when moving. When standing still and attacking, we keep the last direction. For the AI attacking a monster, it will be moving toward it, so the direction is right.

But if it's within 22px and stops moving, the direction stays. Since it approached, it should be facing the right way. Good enough.

Actually, let's always update the hero's facing toward the AI's target when attacking. I'll add `hero.faceTarget` optional. Meh — let's just make the AI keep pressing the direction toward the monster even when close (with a small deadzone), so it faces correctly. But then it might push into the monster. That's fine.

Let me set: if md > 16, press toward the monster. Otherwise don't press but set the facing manually.

Simplest: in `aiPress`, use a deadzone of 4px, so at md=18 it still presses. Then the hero moves into the monster. Contact damage. Hmm.

OK: attack range 22. AI presses toward the monster while md>20. At md<=20, it stops and attacks. Since it approached, the facing is correct.

Fine.

Now pathfinding for the AI. Let's implement BFS from the hero's tile to the goal tile.

```js
function findPath(sx,sy,gx,gy){
  if(sx===gx&&sy===gy) return [];
  const prev=new Int32Array(MW*MH).fill(-1);
  const q=[sy*MW+sx]; prev[sy*MW+sx]=-2;
  let head=0;
  while(head<q.length){
    const cur=q[head++];
    const cx=cur%MW, cy=(cur/MW)|0;
    if(cx===gx&&cy===gy){ // reconstruct
      const path=[]; let c=cur;
      while(c!==-2 && prev[c]!==-2){ path.push({x:c%MW,y:(c/MW)|0}); c=prev[c]; }
      path.reverse(); return path;
    }
    const dirs=[[1,0],[-1,0],[0,1],[0,-1]];
    for(const [ddx,ddy] of dirs){
      const nx=cx+ddx, ny=cy+ddy;
      if(nx<0||ny<0||nx>=MW||ny>=MH) continue;
      const ni=ny*MW+nx;
      if(prev[ni]!==-1) continue;
      if(SOLID[map[ni]]) continue;
      prev[ni]=cur; q.push(ni);
    }
  }
  return null;
}
```
Careful: `prev` initialized to -1 means unvisited. Start set to -2. When reconstructing, we walk back until prev[c] === -2.

Hmm, `while(c!==-2 && prev[c]!==-2)` — first iteration c=cur, prev[cur] might be -2 if cur is start. Then loop doesn't execute and path is empty. Good.

But careful with `new Int32Array(MW*MH).fill(-1)` — fill returns the array. OK.

BFS cost: 1600 tiles, fine. Recompute every 0.5s.

Then the AI follows waypoints: move toward path[ai.pi] center; when within 8px, pi++.

Actually, let's target a few waypoints ahead for smoother movement. Simple: target path[Math.min(pi+2, len-1)].

Hmm, with tile-based movement and 16px tiles, following waypoints exactly can cause jitter. Let's just target path[pi] and advance when within 10px. Then the hero moves in a straight line toward the waypoint, which may clip corners. Since we check collision, it might get stuck on corners.

Let's use a slightly more forgiving approach: advance to the next waypoint when within 12px, and target path[pi+1] for smoothing. And collision will slide.

Alternatively, make the hero's collision box smaller (10x10 = hw 5) so it fits through 16px corridors easily. With hw=5, the hero occupies 10px, leaving 3px on each side. Corner clipping is less likely.

Let's use hw=5, hh=5.

OK.

Also: the AI recomputes the path when the goal changes or every 0.6s. If the path is null (unreachable), move directly.

Let me also handle: the goal tile might be solid (e.g., the elder is standing on a walkable tile, fine; the amulet is on floor, fine).

Now, let's write the render.

```js
function draw(){
  ctx.fillStyle='#101018'; ctx.fillRect(0,0,VW,VH);
  const cx = Math.round(clamp(hero.x - VW/2, 0, MW*TS - VW));
  const cy = Math.round(clamp(hero.y - VH/2, 0, MH*TS - VH));
  cam.x=cx; cam.y=cy;
  
  // tiles
  const x0=Math.floor(cx/TS), y0=Math.floor(cy/TS);
  const x1=Math.ceil((cx+VW)/TS), y1=Math.ceil((cy+VH)/TS);
  for(let y=y0;y<=y1;y++)for(let x=x0;x<=x1;x++){
    const t=getT(x,y);
    const img=TILE_IMG[t];
    if(img) ctx.drawImage(img, x*TS-cx, y*TS-cy);
  }
  ...
}
```

Wait, `getT` returns TREE for out-of-bounds, which is fine.

TILE_IMG: an array of canvas elements indexed by tile type. For grass variants, we want randomness — use `(x*7+y*13)%4` to pick a variant. Let's make TILE_IMG an array of arrays.

Simpler: create 4 grass variants and store them in a separate array `GRASS_V`, and in the draw loop, if t is GRASS or GRASS2 or FLOWER use variants.

Let me just precompute a per-tile image index array `tileVar` at gen time. Or compute in the draw loop: `const v = (x*7+y*13)&3;` and use `GRASS_IMGS[v]`.

I'll do:
- TILE_IMG[T.GRASS] = array of 4 grass canvases
- TILE_IMG[T.GRASS2] = array of 4 grass canvases (darker)
- etc.

And a helper `getTileImg(t,x,y)`.

Let's simplify: build `TILE_IMGS` as an object mapping tile → array of canvases (1 or more variants).

```js
function tileImgFor(t,x,y){
  const arr=TILE_IMGS[t];
  if(!arr) return null;
  return arr[(x*7+y*13)%arr.length];
}
```

Good.

Now entity rendering with y-sorting:

```js
const drawables=[];
// hero
drawables.push({y:hero.y, fn:()=>drawHero(cx,cy)});
for(const n of npcs) drawables.push({y:n.y, fn:()=>drawNPC(n,cx,cy)});
for(const m of monsters) if(m.hp>0) drawables.push({y:m.y, fn:()=>drawMonster(m,cx,cy)});
if(!amulet.taken) drawables.push({y:amulet.y, fn:()=>drawAmulet(cx,cy)});
drawables.sort((a,b)=>a.y-b.y);
for(const d of drawables) d.fn();
```

Now the sprite drawing:

```js
function drawSprite(img, x, y){ ctx.drawImage(img, Math.round(x), Math.round(y)); }
```

Hero: sprite is 12x16. Draw at (hero.x - 6 - cx, hero.y + 6 - 16 - cy). Where hero.x,y is the center of the 10x10 collision box. Actually with hw=5, the box is 10x10, so the bottom is hero.y+5. Let's draw the sprite bottom at hero.y+5: sy = hero.y+5-16 = hero.y-11. sx = hero.x-6.

Monsters: sprites are 16x16 with the art at the bottom. Draw at (m.x-8-cx, m.y+6-16-cy).

Slime sprite is 12 rows tall in a 16x16 canvas, drawn at the bottom. Actually I made the slime rows 0-11 with content at rows 5-11. Hmm, that means the content is at the top of the 16-row canvas... Let me recheck.

SLIME array: rows 0-4 empty, rows 5-11 content, rows 12-15... I only wrote 12 rows. So the canvas is 16x12, content at rows 5-11 (bottom).

Hmm, that means when drawn at the entity position, the content sits at the bottom of the 12px canvas. If I draw at m.y+6-12 = m.y-6, the bottom of the sprite is at m.y+6. Good, aligns with the collision box bottom.

Let me just make all monster sprites 16 wide and 16 tall for consistency, with content at the bottom.

Let me redo the slime with 16 rows:
```
r0-r4 empty (5 rows)
r5-r11 content (7 rows)
r12-r15 empty? 
```
No — content should be at the bottom. So:
rows 0-8 empty, rows 9-15 content.

Let me rewrite SLIME with 16 rows:
```js
const SLIME=[
"................",  //0
"................",  //1
"................",  //2
"................",  //3
"................",  //4
"................",  //5
"................",  //6
"................",  //7
"................",  //8
".....kkkkkk.....",  //9
"...kkggggggkk...",  //10
"..kggggggggggk..",  //11
"..kggeggggeggk..",  //12
".kggggggggggggk.",  //13
".kggggggggggggk.",  //14
".kkkkkkkkkkkkkk."   //15
];
```
16 rows ✓.

BAT: I had 16 rows with content at rows 4-11. Let's shift to rows 6-15... Actually bats fly, so they can be higher. Let's keep the bat content at rows 4-11 and just draw it centered. Eh, for a flying enemy it's fine to have it higher.

Hmm, but the y-sort uses m.y. Let's just draw the bat at m.y-16+... whatever. Let's keep it simple: draw the bat sprite so its bottom is at m.y+6. With content at rows 4-11 of a 16-row canvas, the content bottom is at row 11, so drawing at m.y+6-16 = m.y-10 puts the content bottom at m.y-10+12 = m.y+2. Slightly above the feet. Fine for a flying bat.

OK, whatever. Let's move on.

SKEL: 16 rows with content rows 2-15. Bottom at row 15 → drawn at m.y+6-16 = m.y-10 → content bottom at m.y+6. 

Hero sprites are 12x16 with content rows 0-15. Drawn at hero.y-11 → bottom at hero.y+5. Good.

NPC sprites: reuse hero sprites with different palettes. Let's make an elder sprite (gray hair, blue robe) and a kid (small, green) and a merchant (red).

I'll create NPC sprites by recoloring the hero sprite: define additional palettes and rebuild the sprites.

Elder: hair white/gray, tunic blue.
Kid: smaller — use the hero sprite but scaled? Let's just use a different palette and draw at 0.75 scale... no, pixel art. Let's just make the kid with a distinct palette (bright colors).

Simplest: build 3 NPC sprite sets from the same ASCII with different palettes.

Elder palette: h:'#c8c8d0', g:'#3a5fa8', b:'#5a4a3a', p:'#2a3a6a'
Kid palette: h:'#e0a030', g:'#e0d040', p:'#4a4a6a'
Merchant palette: h:'#3a2a1a', g:'#c04a3a', p:'#4a3a2a'

Good, that's cheap and effective.

Now let me write the code for real.

Let me handle the dialogue box:

```js
const dialogue={active:false, lines:[], i:0, speaker:'', charT:0};
function startDialogue(speaker, lines){
  dialogue.active=true; dialogue.speaker=speaker; dialogue.lines=lines; dialogue.i=0; dialogue.charT=0;
  sfx('talk');
}
function advanceDialogue(){
  if(!dialogue.active) return;
  dialogue.i++;
  if(dialogue.i>=dialogue.lines.length){ dialogue.active=false; onDialogueEnd(); }
  else { sfx('talk'); }
}
```

`onDialogueEnd` handles quest transitions. Hmm, better to trigger the quest change when the dialogue starts or at a specific point.

Let's handle it: the elder's dialogue function returns lines and applies the quest change immediately when the dialogue is initiated (or when it ends).

Actually, let's apply the quest change at the start of the dialogue. So:

```js
function talkTo(npc){
  if(npc.id==='elder'){
    if(quest.stage===0){ quest.stage=1; startDialogue('Elder', [...]) }
    else if(quest.stage===1){ startDialogue('Elder',[...]) }
    else if(quest.stage===2){ quest.stage=3; grantReward(); startDialogue('Elder',[...]) }
    else startDialogue('Elder',[...]);
  }
  ...
}
```

Hmm, but then the objective updates before the dialogue is read. It's fine.

Actually, for the demo to look good, the quest stage should update after the dialogue is read. But it's a minor detail. Let's do it at the start — simpler and the objective HUD updates immediately.

Hmm, but for stage 2→3, the reward should be granted at the end. Eh, let's do it at the start too.

Wait — but there's a subtlety with the AI: if the dialogue ends and the quest stage is already updated, the AI will immediately head to the next objective. Good.

But there's a risk: if quest.stage becomes 1 immediately when talking to the elder, and the AI is still in dialogue, that's fine.

Now, an important detail: after talking to the elder (stage 0 → 1), the elder is at distance 0 from the hero, so if the AI's monster check... no monsters nearby. Good.

Another detail: the AI needs to not re-trigger the dialogue immediately. The dialogue is active, so it waits. After the dialogue ends, the quest stage is 1, so the goal becomes the amulet. Good.

For stage 2 → 3: after the dialogue, the quest is complete. The AI then wanders.

OK.

Now the reward: give a potion, some exp, maybe a "Vale Charm".

Inventory:
```js
const inv=[{id:'potion',name:'Health Potion',count:3,desc:'Restores 20 HP'},{id:'sword',...}];
```
Actually let's make the inventory a simple array of {name, count, desc, use}.

Items:
- Health Potion x3 (use: heal 20)
- Sword (passive, atk +0) — just a starting item for flavor
- Amulet of the Vale (quest item, obtained in the dungeon)
- Gold x0 (from rewards)

Let's include: potion, sword, gold, amulet.

Inventory UI: toggled with I, drawn as a panel listing items. Press 1 to use a potion.

Let's write it.

Now sound.

```js
let actx=null;
function initAudio(){
  if(!actx){ try{ actx=new (window.AudioContext||window.webkitAudioContext)(); }catch(e){} }
  if(actx && actx.state==='suspended') actx.resume();
}
function tone(freq, dur, type, vol, freqEnd){
  if(!actx) return;
  const o=actx.createOscillator(), g=actx.createGain();
  o.type=type||'square';
  o.frequency.setValueAtTime(freq, actx.currentTime);
  if(freqEnd) o.frequency.exponentialRampToValueAtTime(Math.max(20,freqEnd), actx.currentTime+dur);
  g.gain.setValueAtTime(vol||0.05, actx.currentTime);
  g.gain.exponentialRampToValueAtTime(0.0001, actx.currentTime+dur);
  o.connect(g); g.connect(actx.destination);
  o.start(); o.stop(actx.currentTime+dur+0.02);
}
```

sfx names: 'attack','hit','hurt','pickup','level','talk','step','quest'.

Now the day-night cycle.

```js
let dayT = 0.3; // 0..1, 0 = midnight
const DAY_LEN = 120; // seconds
```
Update: dayT += dt/DAY_LEN; wrap.

Tint:
```js
function nightTint(t){
  // returns [r,g,b,a]
  // keyframes
}
```
Let's define keyframes at t=0 (midnight, dark blue), 0.22 (dawn orange), 0.3 (day clear), 0.7 (day clear), 0.78 (dusk orange), 0.85 (night), 1.0 (midnight).

Interpolate.

```js
const SKY=[
 {t:0.00, c:[20,30,90], a:0.55},
 {t:0.20, c:[30,35,80], a:0.50},
 {t:0.26, c:[255,140,70], a:0.28},
 {t:0.34, c:[255,255,255], a:0.0},
 {t:0.66, c:[255,255,255], a:0.0},
 {t:0.74, c:[255,130,60], a:0.28},
 {t:0.82, c:[25,30,85], a:0.52},
 {t:1.00, c:[20,30,90], a:0.55}
];
```
Interpolate color and alpha.

Start dayT at 0.30 → morning. Good.

Draw the tint as a full-screen fillRect with the computed rgba over the world (before HUD).

Also, in the dungeon, add a darkness overlay? Skip — keep it simple. Maybe add a vignette.

Now the minimap.

Pre-render a 40x40 canvas with tile colors. Then draw it scaled.

```js
const mini=document.createElement('canvas'); mini.width=MW; mini.height=MH;
const mg=mini.getContext('2d');
function buildMini(){
  for(let y=0;y<MH;y++)for(let x=0;x<MW;x++){
    mg.fillStyle=MINI_COLORS[map[y*MW+x]]||'#000';
    mg.fillRect(x,y,1,1);
  }
}
```
Then each frame: `ctx.drawImage(mini, VW-64-4, 4, 64, 64)`. With imageSmoothing off.

Then draw dots: hero (white), npcs (yellow), monsters (red), amulet (gold).

Dot position: `mx = VW-64-4 + (x/TS)*(64/MW)`.

Let's compute: scale = 64/MW = 64/40 = 1.6. So dotX = mmx + (entity.x/TS)*1.6.

Draw a 2x2 rect.

Also draw a border around the minimap.

OK.

Now the HUD layout (320x180):

Top-left (4,4):
- HP bar: width 70, height 6. Background dark, fill red/green.
- Text "HP 30/30" at 8px... maybe just the bar.
- Level text "Lv 1" 
- EXP bar below: width 70, height 3, fill cyan.

Let's do:
```
x=4,y=4: HP bar 64x6
x=4,y=12: EXP bar 64x3
x=72,y=4: "Lv 1"
x=4,y=18: quest text (objective)
```

Quest text: "QUEST: Find the Amulet" at y=18, and the objective at y=27.

Bottom-left (4, 180-14): controls: "WASD/Arrows Move  SPACE Attack  E Talk  I Bag  P Demo"

That's a long string at 8px monospace ≈ 4.8px per char → 55 chars = 264px. Fits in 320. Good.

Let's split into two lines:
"WASD/Arrows: Move   SPACE: Attack   E: Talk"
"I: Inventory   1: Potion   P: Toggle Demo"

At y=180-20 and y=180-11.

Hmm, that might overlap with the dialogue box. The dialogue box will be at the bottom. Let's put the dialogue box at y=120..170 and move the controls to the top-left under the quest? Or just hide the controls while the dialogue is active.

Let's keep the controls at the bottom and hide them when the dialogue is active.

Autoplay indicator: top-center or bottom-right. Let's do top-right below the minimap: "▶ DEMO  (press any key)" blinking.

Hmm, the minimap is at the top-right (64x64 at x=252..316, y=4..68). So the demo indicator below it at y=70.

Actually let's put the demo indicator at the top-center: "DEMO MODE - P to take control". At 8px, ~31 chars = 150px. Centered at x=160-75=85, y=4. Hmm, might overlap with the HP bar area. The HP bar is at x=4..68. So x=85 is fine.

OK.

Now let's write the dialogue box:

```js
if(dialogue.active){
  const bx=8, by=VH-46, bw=VW-16, bh=40;
  ctx.fillStyle='rgba(10,10,20,0.9)'; ctx.fillRect(bx,by,bw,bh);
  ctx.strokeStyle='#e0d060'; ctx.lineWidth=1; ctx.strokeRect(bx+0.5,by+0.5,bw-1,bh-1);
  ctx.fillStyle='#f0d060'; ctx.font='bold 8px monospace'; ctx.fillText(dialogue.speaker, bx+6, by+5);
  ctx.fillStyle='#e8e8f0'; 
  // wrap text
  wrapText(dialogue.lines[dialogue.i], bx+6, by+17, bw-12, 9);
  ctx.fillStyle='#a0a0b0'; ctx.fillText('SPACE', bx+bw-40, by+bh-11);
}
```

wrapText: simple word wrap.

Now the typewriter effect? Optional. Let's add a simple reveal: show the full text. Keep it simple.

Actually a typewriter adds life. Let's do it with a char counter that increases over time. dialogue.charT += dt*40. Then substring.

OK.

Now let's write everything out. Let me be systematic.

```js
// ============ CONSTANTS ============
const VW=320, VH=180, TS=16;
const MW=40, MH=40;
```

Tile enum.

Then the sprite data.

Then the tile canvases.

Then world gen.

Then entities.

Then input.

Then update.

Then render.

Then the main loop.

Let me write the code.

```js
// ---- RNG
function rng(seed){let s=(seed>>>0)||1;return function(){s=(s*1664525+1013904223)>>>0;return s/4294967296;};}
const clamp=(v,a,b)=>v<a?a:v>b?b:v;
```

Sprite helper:
```js
function makeSprite(rows,pal){
  const w=rows.reduce((m,r)=>Math.max(m,r.length),0), h=rows.length;
  const c=document.createElement('canvas'); c.width=w; c.height=h;
  const g=c.getContext('2d');
  for(let y=0;y<h;y++){
    const row=rows[y];
    for(let x=0;x<row.length;x++){
      const col=pal[row[x]];
      if(col){ g.fillStyle=col; g.fillRect(x,y,1,1); }
    }
  }
  return c;
}
function flipSprite(src){
  const c=document.createElement('canvas'); c.width=src.width; c.height=src.height;
  const g=c.getContext('2d'); g.translate(src.width,0); g.scale(-1,1); g.drawImage(src,0,0);
  return c;
}
```

Now the hero body parts.

Then:
```js
function buildCharSet(pal){
  const down0=makeSprite(BODY_DOWN.concat(LEGS_A),pal);
  const down1=makeSprite(BODY_DOWN.concat(LEGS_B),pal);
  const up0=makeSprite(BODY_UP.concat(LEGS_A),pal);
  const up1=makeSprite(BODY_UP.concat(LEGS_B),pal);
  const left0=makeSprite(BODY_LEFT.concat(LEGS_LA),pal);
  const left1=makeSprite(BODY_LEFT.concat(LEGS_LB),pal);
  return {
    down:[down0,down1],
    up:[up0,up1],
    left:[left0,left1],
    right:[flipSprite(left0),flipSprite(left1)]
  };
}
```

Good.

Now, palettes.

HERO_PAL:
```js
{'.':null,'k':'#1b1224','h':'#7a4a21','s':'#f2c79a','e':'#241a2e','g':'#4fae55','b':'#8a5a2b','p':'#3b4a8a','o':'#5c3f22'}
```

Wait, in BODY_DOWN I used 'd'? No, I didn't use 'd'. OK, remove it or keep it unused.

ELDER_PAL: h white, g blue, p dark blue.
KID_PAL: h orange, g yellow, p brown.
MERCH_PAL: h brown-dark, g red, p brown.

Now tiles.

```js
function pixCircle(g,cx,cy,r,color){
  g.fillStyle=color;
  for(let y=-r;y<=r;y++)for(let x=-r;x<=r;x++){
    if(x*x+y*y<=r*r+r*0.6) g.fillRect(cx+x,cy+y,1,1);
  }
}
```

Grass:
```js
function mkGrass(seed,dark){
  return makeTile(g=>{
    const r=rng(seed);
    g.fillStyle=dark?'#3f7d38':'#4e9a45';
    g.fillRect(0,0,16,16);
    for(let i=0;i<30;i++){
      const x=(r()*16)|0,y=(r()*16)|0;
      g.fillStyle = r()<0.5 ? (dark?'#356b30':'#458a3d') : (dark?'#4a8f42':'#5aa851');
      g.fillRect(x,y,1,1);
    }
  });
}
```

Flower:
```js
function mkFlower(seed){
  return makeTile(g=>{
    const r=rng(seed);
    g.fillStyle='#4e9a45'; g.fillRect(0,0,16,16);
    for(let i=0;i<20;i++){ ... speckles }
    // flowers
    const cols=['#e8e060','#e06090','#e0e0f0'];
    for(let i=0;i<3;i++){
      const x=2+((r()*12)|0), y=2+((r()*12)|0);
      g.fillStyle=cols[(r()*3)|0]; g.fillRect(x,y,2,2);
      g.fillStyle='#f8f8a0'; g.fillRect(x,y,1,1);
    }
  });
}
```

Dirt:
```js
g.fillStyle='#b39062'; fill; speckles '#9c7a4e','#c7a476'
```

Water:
```js
g.fillStyle='#2a5fa8'; fill;
g.fillStyle='#3d7fd0'; a few horizontal 4px dashes
g.fillStyle='#1e4a85'; a few darker
```

Tree:
```js
drawGrass base, trunk, canopy circles
```

Bush:
```js
grass base + green blob
```

Wall (house):
```js
g.fillStyle='#c9a26b'; fillRect;
g.fillStyle='#a8814f';
for(y=0;y<16;y+=4) g.fillRect(0,y,16,1);
for(y=0;y<16;y+=4) for(x=(y/4%2)?0:4;x<16;x+=8) g.fillRect(x,y,1,4);
```

Hmm, let's simplify: draw horizontal lines every 4 rows, and vertical lines offset.

Roof:
```js
g.fillStyle='#b04a3a'; fillRect;
g.fillStyle='#8f382c'; vertical lines every 4; horizontal line at y=0
g.fillStyle='#c85a48'; highlight
```

Door:
```js
g.fillStyle='#c9a26b'; fillRect;  // wall
g.fillStyle='#5a3a1e'; g.fillRect(3,3,10,13);
g.fillStyle='#7a5228'; g.fillRect(4,4,8,12);
g.fillStyle='#e0c060'; g.fillRect(10,9,2,2);
```

Floor:
```js
g.fillStyle='#4a4556'; fillRect;
speckles '#3d3948','#565166'
```

Stone wall:
```js
g.fillStyle='#2e2a3d'; fillRect;
g.fillStyle='#3f3a52'; bricks: rows of 8x4 with 1px gaps
g.fillStyle='#4d4765'; top highlight
```

Torch:
```js
floor base + torch: brown stick + orange flame
```

OK, let's write it.

Now the main game state.

```js
const hero={x:9*16+8,y:8*16+8,dir:'down',frame:0,animT:0,moving:false,
  hp:30,maxhp:30,level:1,exp:0,expNext:20,atk:5,speed:88,
  atkCd:0,invuln:0,hitFlash:0};
```

NPCs:
```js
const npcs=[
  {id:'elder',name:'Elder',x:13*16+8,y:8*16+8,dir:'down',sprite:elderSet,frame:0},
  {id:'kid',name:'Kid',x:5*16+8,y:7*16+8,dir:'right',sprite:kidSet},
  {id:'merchant',name:'Merchant',x:11*16+8,y:11*16+8,dir:'down',sprite:merchSet}
];
```

Wait, (11,11) — is that walkable? The village is x 2..16, y 2..15. House at (3,11)-(6,14). So (11,11) is grass. Fine.

Hmm, but the merchant should be near the path. Let's put the merchant at (10,9). Path is at y=8 (x 2..26) and y=7,9 for x=8..14. So (10,9) is DIRT. Good.

Kid at (5,7)? y=7 dirt only for x=8..14. (5,7) is grass. Fine.

Elder at (13,8) — dirt. Good.

Hero start at (9,8) — dirt. Good.

Wait, the elder is at (13,8) which is on the horizontal path. The hero starts at (9,8). Fine.

Amulet:
```js
const amulet={x:35*16+8, y:35*16+8, taken:false, t:0};
```

Hmm, the dungeon interior is x 23..36, y 23..36. So (35,35) is interior floor. Good.

Wait, I need to double check the dungeon bounds. DX0=22, DY0=22, DX1=37, DY1=37. Border at x=22, x=37, y=22, y=37. Interior x 23..36, y 23..36. Good.

Amulet at (35,35). Boss at (34,35).

Now the inner walls:
- Row y=27, x=23..29 → SWALL
- Row y=31, x=28..36 → SWALL

Check the path from the entrance (26,22) down:
(26,23), (26,24), (26,25), (26,26), then (26,27) is SWALL. So go right: (27,26),(28,26),(29,26),(30,26), then down (30,27),(30,28),(30,29),(30,30), then (30,31) is SWALL. Go left: (29,30),(28,30), then down (28,31)? No, (28,31) is SWALL (x=28..36 at y=31). Hmm!

Let me redo: wall at y=31 spans x=28..36. So to pass y=31, need x<=27. So from (30,30) go left to (27,30), then down (27,31),(27,32)...(27,35), then right along y=35 to (35,35).

Wait, (27,31) — is x=27 in the wall range 28..36? No, 27 < 28. So (27,31) is floor. Good.

So: (27,30) → (27,31) → (27,32) → ... → (27,35) → right → (35,35).

But wait, at y=35 going right from x=27 to x=35, is there any wall? No. Good.

And the wall row at y=27 spans x=23..29, so x=30,31,...36 are open at y=27. Good.

Great, the path is connected.

Torches: (26,25), (30,29), (27,33), (34,35)... but (34,35) is where the boss is. Let's put torches at (24,26), (33,29), (24,34), (33,34). Those are floor tiles not on the main path. Fine.

Hmm, are they floor? x=24,y=26: interior, not a wall. Yes.
x=33,y=29: interior, not a wall (wall at y=27 is x 23..29; wall at y=31 is x 28..36). y=29 is between. So (33,29) is floor. Good.
x=24,y=34: floor. Good.
x=33,y=34: floor. Good.

OK.

Now let's also make sure the dungeon entrance from the outside path: the path is dirt at x=26, y from 8 to 21. Then (26,22) is FLOOR (entrance). Good.

Hmm wait, the dungeon border is at y=22 and I set (26,22) to FLOOR. But then the border at y=22 is broken at x=26. Good.

Also need to make sure the forest trees don't block the path — the path is carved after trees. Let's carve the path:
```js
for(let x=2;x<=26;x++) setT(x,8,T.DIRT);
for(let y=8;y<=21;y++) setT(26,y,T.DIRT);
```
Wait, but the village is at x 2..16. The path at y=8 goes from x=2 to x=26. Then the vertical path at x=26 from y=8 to y=21.

But we also need to clear trees around the path so it looks like a path. It's fine.

Hmm, but actually the trees were placed with `if(x<=16 && y<=16) continue;` for the village. So the village area has no trees. And the dungeon area (x>=22 && y>=22) has no trees. The path region (x 17..26, y 8) gets trees possibly, then carved.

OK.

Now, monsters:

```js
const monsters=[];
function spawn(type,tx,ty){
  const cfg=MON[type];
  monsters.push({type,x:tx*16+8,y:ty*16+8,hp:cfg.hp,maxhp:cfg.hp,dir:'down',
    frame:0,animT:0,atkCd:0,hitFlash:0,state:'patrol',
    px:tx*16+8,py:ty*16+8, patrolT:0, alive:true});
}
```

Positions:
- slime at (18,8) — on the path! Good, the AI will encounter it early. But wait, the path is at y=8, x=2..26. A slime at (18,8) is right on the path. 
- slime at (22,10)
- bat at (20,12)
- slime at (24,6)
- skeleton at (30,26) — hmm, is that floor? Wall at y=27 x=23..29. (30,26) is floor. Good. But the AI path goes (30,26) → (30,27). So it'll meet.
- skeleton at (30,30)
- skeleton at (27,34)
- boss at (34,35)

Hmm, the AI path: (26,23..26) → (27..30, 26) → (30,27..30) → (29,28... wait no.

Let me redo: from (26,26) go right to (30,26), then down to (30,30), then left to (27,30), then down to (27,35), then right to (35,35).

Hmm, at y=30 going left from x=30 to x=27. Then down from (27,30) to (27,35).

Skeleton at (30,30) is on the path. Skeleton at (27,34) is on the path. Boss at (34,35) near the amulet.

Good, three fights in the dungeon plus one slime in the forest.

Total: 1 slime (forest) + 3 skeletons + 1 boss = 5 fights. Each ~1-2s. That's ~8s of fighting. Plus travel ~20s. Plus dialogue ~5s. Total ~33s. Slightly over 30s but the "important stuff" (NPC talk, fight, quest step) happens in the first 15s.

Hmm, the requirement says the animation should show everything important within the first 30 seconds. The quest completion might be at ~33s. Let's speed it up.

Options: reduce the travel distance. Let's move the dungeon closer: DX0=20, DY0=20, DX1=35, DY1=35. And the path: horizontal y=8 from x=2 to x=24, vertical x=24 from y=8 to y=19.

Hmm, then the village is at x 2..16, y 2..15, and the dungeon at x 20..35, y 20..35. The distance from (9,8) to (33,33) is 24+25 = 49 tiles. At 5.5 tiles/s = 9s each way. 18s round trip.

Hmm, still.

Alternative: make the hero faster during autoplay? No, that's cheating.

Let's just make the hero speed 100 px/s (6.25 tiles/s). Then 49 tiles = 7.8s each way. 16s round trip. Plus 5 fights ~7s = 23s, plus dialogue 4s = 27s. 

But 100px/s in a 320px view is quite fast. It's fine for an action RPG.

Hmm, let's compromise: hero speed 95.

Also, reduce the number of monsters on the path: slime at (18,8), skeleton at (28,24), boss at (32,33). 3 fights.

Hmm, but "monsters that patrol and chase" — we need several monsters for the world to feel alive. We can have many monsters but the AI only fights the ones in its way.

Let's put monsters:
- slime (18,8) on the path
- slime (22,11), bat (16,13), slime (12,17) — off path
- skeleton (28,25), skeleton (26,30), skeleton (32,32) — in the dungeon, some on the path
- boss (32,33) — guarding the amulet at (33,33)

Let me recompute the dungeon layout with DX0=20, DY0=20, DX1=35, DY1=35.

Border: x=20, x=35, y=20, y=35.
Interior: x 21..34, y 21..34.
Entrance: (24,20) FLOOR.
Path outside: vertical dirt x=24, y=8..19.

Inner walls:
- y=25, x=21..27 (gap x=28..34)
- y=29, x=26..34 (gap x=21..25)

Path: (24,20)→(24,21..24)→ blocked at (24,25) → right along y=24 to x=28 → down (28,25),(28,26),(28,27),(28,28) → blocked at (28,29) → left along y=28 to x=25 → down (25,29),(25,30)...(25,33) → right along y=33 to x=33 → amulet at (33,33).

Check: wall at y=29 spans x=26..34, so x=25 is open. Good.
Wall at y=25 spans x=21..27, so x=28 is open. Good.

Amulet at (33,33). Boss at (32,33).

Skeletons: (28,26) on the path, (25,31) on the path.

Hmm, both on the path — the AI will fight them. That's 2 fights + the boss + the forest slime = 4 fights. OK.

Let's also add a couple more monsters off-path for flavor: bat at (30,22), slime at (22,33), skeleton at (33,28).

Now the amulet at (33,33) — is that interior? x 21..34, y 21..34. Yes.

Good.

Distance from (9,8) to (33,33) ≈ 24+25 = 49 tiles. Path length is longer due to the winding: roughly 4 + 4 + 4 + 4 + 5 + 8 = ~29 tiles in the dungeon plus 16 tiles outside = 45 tiles ≈ 720px. At 95px/s = 7.6s. Return trip the same → 15s. Plus fights ~6s, dialogue ~4s → 25s. 

Now let's finalize the world gen numbers.

MW=40, MH=40.

Village: x 2..16, y 2..15.
Lake: center (7,32), r=5.
Dungeon: x 20..35, y 20..35.

Forest: everywhere else (except paths).

Hmm, the lake at (7,32) r=5 covers x 2..12, y 27..37. The dungeon starts at x=20, so no overlap. Good.

Path: y=8, x=2..24; x=24, y=8..19.

Hmm, the path at y=8 from x=2..24 passes through the village (x 2..16) and then through the forest (x 17..24). Good.

Now, tree density: let's use 0.32 for a nice forest.

But we must ensure the hero can path from the village to the dungeon. The carved path guarantees it.

Also, we need to make sure the village houses don't block. They're placed at fixed positions.

Let me also add some bushes for variety.

OK, writing the final code now.

One more thing: the AI's pathfinding goal. When the goal is the amulet at (33,33) and the hero is at the village, the BFS will find a path through the carved path. Good. But BFS uses 4-neighbor movement, so the path will be Manhattan-style (staircase). That's fine.

Actually, the BFS shortest path might cut through the forest if there's an opening. That's fine and looks natural.

Hmm, but the hero might get stuck on tree corners. With hw=5, the hero's box is 10x10 and the corridor between trees is 16px if there's a 1-tile gap. Should be OK.

Actually, wait: BFS finds paths through 1-tile-wide corridors. If the hero's box is 10px and the corridor is 16px, the hero fits with 3px margin. When moving diagonally around corners... the hero moves axis-aligned toward the waypoint, so it should be fine.

Hmm, but there's a subtlety: the hero targets waypoint centers. If the path goes right then down, the hero moves right to the tile center, then down. Fine.

But I'm using "target path[pi+1]" for smoothing... let's not. Just target path[pi] and advance when within 6px. Since waypoints are tile centers 16px apart, the hero will move smoothly.

Actually, with a speed of 95px/s and dt~0.016, the hero moves ~1.5px per frame. Fine.

Let me use: advance when dist < 8.

Alright. Also, the AI should recompute the path if it's stuck. Let's add a stuck timer: if the hero's position hasn't changed much in 1s and it's trying to move, recompute.

Simple approach: recompute the path every 0.5s anyway (cheap enough). And if the hero is stuck, add a random perpendicular nudge.

Let's just recompute every 0.5s and also when the goal changes.

Hmm, recomputing resets pi, which could cause the hero to backtrack. Let's recompute only when the goal tile changes or every 1.2s, and when recomputing, find the closest waypoint to the hero and set pi there.

Let's implement:
```js
function repath(goalX,goalY){
  const sx=Math.floor(hero.x/TS), sy=Math.floor(hero.y/TS);
  const gx=Math.floor(goalX/TS), gy=Math.floor(goalY/TS);
  const p=findPath(sx,sy,gx,gy);
  ai.path=p||[];
  ai.pi=0;
  ai.goalKey=gx+','+gy;
}
```

And in the follow:
```js
function followPath(tx,ty,dt){
  const gx=Math.floor(tx/TS), gy=Math.floor(ty/TS);
  ai.repathT-=dt;
  if(ai.goalKey!==gx+','+gy || ai.repathT<=0 || ai.pi>=ai.path.length){
    repath(tx,ty); ai.repathT=0.8;
  }
  if(ai.path && ai.path.length){
    while(ai.pi<ai.path.length){
      const wp=ai.path[ai.pi];
      const wx=wp.x*TS+8, wy=wp.y*TS+8;
      if(Math.hypot(wx-hero.x,wy-hero.y)<8) ai.pi++;
      else break;
    }
    if(ai.pi<ai.path.length){
      const wp=ai.path[ai.pi];
      aiPress(wp.x*TS+8, wp.y*TS+8);
      return;
    }
  }
  aiPress(tx,ty);
}
```

Hmm, if pi >= length, we're at the goal → aiPress(tx,ty) which will press toward the goal. Fine.

But there's an issue: recomputing every 0.8s resets pi to 0, and the first waypoint is the hero's own tile (or the next). Actually findPath starts from the hero's tile, and the returned path excludes the start tile. So path[0] is the next tile. Good.

Hmm, in my findPath, I push nodes starting from `cur` (the goal) back to the start, then reverse. Let me re-check:

```js
if(cx===gx&&cy===gy){
  const path=[]; let c=cur;
  while(prev[c]!==-2){ path.push({x:c%MW,y:(c/MW)|0}); c=prev[c]; }
  path.reverse(); return path;
}
```
Starting at the goal, we push the goal, then move to prev. When prev[c] === -2, that means c is the start (prev[start] = -2). So we push the start too. Then reverse → [start, ..., goal].

Hmm, that includes the start tile. Let's exclude it: after reverse, `path.shift()`.

Actually, let's just leave it — the first waypoint is the start tile center, which the hero is near, so it advances immediately. Fine.

Hmm, but if the hero is at the edge of its tile, the distance to the tile center could be > 8, so it would move to the center first. That's fine.

OK, let's leave it.

Now, one problem: `findPath` uses `prev` as Int32Array filled with -1, and sets prev[start] = -2. Then in the reconstruction, `while(prev[c]!==-2)` — if c is the start, prev[c] = -2, loop exits. Good.

But what if the goal is unreachable? The BFS exhausts and returns null. Then ai.path = []. Then aiPress(tx,ty) direct. OK.

Now, let's write the attack.

```js
function heroAttack(){
  if(hero.atkCd>0) return;
  hero.atkCd=0.36;
  sfx('swing');
  // hitbox
  const range=22, w=20, h=20;
  let hx=hero.x, hy=hero.y;
  if(hero.dir==='left') hx-=14;
  else if(hero.dir==='right') hx+=14;
  else if(hero.dir==='up') hy-=14;
  else hy+=14;
  let hit=false;
  for(const m of monsters){
    if(m.hp<=0) continue;
    if(Math.abs(m.x-hx)<16 && Math.abs(m.y-hy)<16){
      damageMonster(m, hero.atk + ((Math.random()*3)|0));
      hit=true;
    }
  }
  if(hit) sfx('hit');
  // slash effect
  slashes.push({x:hx,y:hy,dir:hero.dir,t:0.15});
}
```

Hmm, using Math.random for damage is fine.

Actually let's make the damage deterministic-ish: `hero.atk + rand(0..2)`.

damageMonster:
```js
function damageMonster(m,dmg){
  m.hp-=dmg;
  m.hitFlash=0.15;
  addDamageNumber(m.x, m.y-10, dmg, '#ffe060');
  if(m.hp<=0){ onMonsterDeath(m); }
}
```

onMonsterDeath: exp gain, sfx, particles, remove.

```js
function onMonsterDeath(m){
  m.hp=0;
  sfx('kill');
  addDamageNumber(m.x, m.y-16, '+'+m.exp+' XP', '#80e0ff');
  gainExp(m.exp);
  // maybe drop potion
}
```

gainExp with level up.

```js
function gainExp(n){
  hero.exp+=n;
  while(hero.exp>=hero.expNext){
    hero.exp-=hero.expNext;
    hero.level++;
    hero.expNext=Math.floor(hero.expNext*1.6);
    hero.maxhp+=10; hero.hp=hero.maxhp; hero.atk+=2;
    sfx('level');
    addDamageNumber(hero.x, hero.y-20, 'LEVEL UP!', '#ffe060');
  }
}
```

Monster contact damage:
```js
for(const m of monsters){
  if(m.hp<=0) continue;
  const d=Math.hypot(m.x-hero.x,m.y-hero.y);
  if(d<14 && m.atkCd<=0 && hero.invuln<=0){
    m.atkCd=1.1;
    hero.hp-=m.dmg;
    hero.invuln=0.7;
    hero.hitFlash=0.3;
    addDamageNumber(hero.x, hero.y-14, m.dmg, '#ff6060');
    sfx('hurt');
    if(hero.hp<=0) heroDie();
  }
}
```

heroDie: respawn at the village, hp = maxhp/2, lose nothing.

Now the damage numbers:
```js
const dmgNums=[];
function addDamageNumber(x,y,text,color){
  dmgNums.push({x,y,text:String(text),color,t:1.0});
}
```
Update: t -= dt; y -= 18*dt.
Draw with alpha = min(1, t*2).

Now let's write the update loop.

```js
let last=0;
function loop(ts){
  requestAnimationFrame(loop);
  const dt=Math.min(0.05,(ts-last)/1000||0); last=ts;
  update(dt);
  render();
}
```

update(dt):
- dayT update
- if autoplay and not dialogue: updateAI(dt)
- handle input → hero movement
- update hero
- update monsters
- update npcs (idle animation)
- update amulet (bob)
- update damage numbers
- update dialogue typewriter
- check amulet pickup
- check quest triggers

Hero movement:
```js
let dx=0,dy=0;
if(input.left)dx--; if(input.right)dx++; if(input.up)dy--; if(input.down)dy++;
if(dx||dy){
  const len=Math.hypot(dx,dy);
  dx/=len; dy/=len;
  const sp=hero.speed*dt;
  const nx=hero.x+dx*sp;
  if(canMove(nx,hero.y)) hero.x=nx;
  const ny=hero.y+dy*sp;
  if(canMove(hero.x,ny)) hero.y=ny;
  hero.moving=true;
  // dir
  if(Math.abs(dx)>Math.abs(dy)) hero.dir = dx<0?'left':'right';
  else hero.dir = dy<0?'up':'down';
  hero.animT+=dt;
  if(hero.animT>0.16){hero.animT=0;hero.frame^=1;}
} else {
  hero.moving=false; hero.animT=0; hero.frame=0;
}
```

Hmm, when moving the frame should toggle. Let me use a walk cycle of 4: frames [0,1,0,1]... with 2 sprites it's just alternating. Fine.

Actually let's use a 4-step cycle with 2 sprites: frame index = (animT*8)%2.

Simple: `hero.frame = Math.floor(hero.animT/0.14)%2;` and keep animT accumulating. Reset on stop.

Let's do:
```js
if(dx||dy){ hero.animT += dt; } else { hero.animT=0; }
hero.frame = Math.floor(hero.animT/0.14)%2;
```

Good.

canMove:
```js
function canMove(x,y){
  const hw=5,hh=5;
  return !isSolid(x-hw,y-hh)&&!isSolid(x+hw,y-hh)&&!isSolid(x-hw,y+hh)&&!isSolid(x+hw,y+hh);
}
function isSolid(px,py){
  const tx=Math.floor(px/TS), ty=Math.floor(py/TS);
  if(tx<0||ty<0||tx>=MW||ty>=MH) return true;
  return SOLID[map[ty*MW+tx]]===1;
}
```

Now, monsters update:

```js
for(const m of monsters){
  if(m.hp<=0) continue;
  m.atkCd=Math.max(0,m.atkCd-dt);
  m.hitFlash=Math.max(0,m.hitFlash-dt);
  const d=Math.hypot(hero.x-m.x, hero.y-m.y);
  const cfg=MON[m.type];
  let tx,ty;
  if(d<cfg.chase){
    tx=hero.x; ty=hero.y;
    m.state='chase';
  } else {
    m.patrolT-=dt;
    if(m.patrolT<=0){
      m.patrolT=1.5+Math.random()*2;
      const ang=Math.random()*Math.PI*2;
      m.px=m.x+Math.cos(ang)*40;
      m.py=m.y+Math.sin(ang)*40;
      // clamp to walkable
    }
    tx=m.px; ty=m.py;
    m.state='patrol';
  }
  const ddx=tx-m.x, ddy=ty-m.y;
  const dd=Math.hypot(ddx,ddy);
  if(dd>4){
    const sp=cfg.speed*dt;
    const nx=m.x+ddx/dd*sp;
    const ny=m.y+ddy/dd*sp;
    if(canMove(nx,m.y)) m.x=nx;
    if(canMove(m.x,ny)) m.y=ny;
    m.animT+=dt;
  }
  m.frame=Math.floor(m.animT/0.2)%2;
}
```

Hmm, patrol targets might be inside walls. If the monster can't move toward it, it just presses against the wall. Then patrolT resets and picks a new target. Acceptable.

Also add: if the monster can't move at all for a while, pick a new patrol target.

Let's keep it simple.

Monster speed: slime 20, bat 45, skeleton 32, boss 28.

Chase range: 70-90.

Now the amulet pickup:
```js
if(!amulet.taken && Math.hypot(hero.x-amulet.x, hero.y-amulet.y)<14){
  amulet.taken=true;
  invAdd('Amulet of the Vale',1,'The stolen relic. Return it to the Elder.');
  if(quest.stage===1) quest.stage=2;
  sfx('pickup');
  addDamageNumber(amulet.x, amulet.y-16,'AMULET!','#ffe060');
}
```

Hmm, but the boss is at (32,33) right next to the amulet at (33,33). The AI will fight the boss first (monster within 110px). Good.

Actually, the boss might not be dead when the hero reaches the amulet. The AI attacks the nearest monster within 110px, so it will target the boss. Good.

But if the hero picks up the amulet while the boss is alive, that's fine too.

Now the NPC interaction:
```js
function tryInteract(){
  let best=null,bd=30;
  for(const n of npcs){
    const d=Math.hypot(n.x-hero.x,n.y-hero.y);
    if(d<bd){bd=d;best=n;}
  }
  if(best) talkTo(best);
}
```

Now the input handling.

```js
const keys={};
window.addEventListener('keydown',e=>{
  const k=e.key.toLowerCase();
  if(['arrowup','arrowdown','arrowleft','arrowright',' ','w','a','s','d','e','i','1','j','enter'].includes(k)) e.preventDefault();
  if(k==='p'){ autoplay=!autoplay; if(autoplay) resetAI(); return; }
  // any control key disables autoplay
  if(['arrowup','arrowdown','arrowleft','arrowright','w','a','s','d',' ','j','e','i','1','enter'].includes(k)){
    if(autoplay){ autoplay=false; }
  }
  ...
});
```

Hmm, but the demo needs to run by default. If a player presses a key, autoplay stops. Good.

But careful: on keydown, we also handle the action. If autoplay was on and the player presses a movement key, autoplay stops and the movement key takes effect. Good.

Also need initAudio() on the first key press.

Let's write:
```js
window.addEventListener('keydown', e=>{
  initAudio();
  const k=e.key.toLowerCase();
  const ctrl=['arrowup','arrowdown','arrowleft','arrowright','w','a','s','d',' ','j','e','i','1','enter'];
  if(k==='p'){ autoplay=!autoplay; resetAI(); e.preventDefault(); return; }
  if(ctrl.includes(k)){
    if(autoplay){ autoplay=false; }
    e.preventDefault();
  }
  keys[k]=true;
  if(k===' '||k==='j'){ /* attack handled in update */ }
  if(k==='e'||k==='enter'){ if(!dialogue.active) tryInteract(); else advanceDialogue(); }
  if(k==='i'){ invOpen=!invOpen; }
  if(k==='1'){ usePotion(); }
});
```

Hmm, but attack and dialogue advance should also work when the dialogue is active. Let's handle: if the dialogue is active, SPACE advances it.

Let's put the attack in the update loop based on the keys state, and handle the dialogue advance on keydown.

Actually simpler: handle the attack on keydown (with a cooldown check).

```js
if(k===' '||k==='j'){
  if(dialogue.active) advanceDialogue();
  else if(!autoplay) heroAttack();
}
```
But the AI attacks via a separate path. Hmm, the AI sets input.attack and the hero's attack is triggered in the update. Let's unify:

In update:
```js
if(input.attack && !dialogue.active) heroAttack();
```
And input.attack is set from the keys or by the AI.

For the keyboard, set input.attack on keydown and clear on keyup. Then the cooldown limits it.

Let's do:
```js
keys[' ']=true on keydown, false on keyup.
input.attack = keys[' ']||keys['j'] || aiAttack;
```

Hmm, but for dialogue advancing, we want a keydown event (not held).

Let's do: on keydown of space/j: if dialogue.active → advanceDialogue(); else → attackPressed=true (a one-shot flag). And in update, if attackPressed or input.attack held → heroAttack(); then reset attackPressed.

Actually simplest: in update, `if((keys[' ']||keys['j']||aiAttack) && hero.atkCd<=0) heroAttack();` — holding space auto-attacks with the cooldown. That's fine for an action game.

And for dialogue: on keydown of space/j/e/enter → advanceDialogue().

OK good.

Now, when the dialogue is active, the hero shouldn't move. Let's zero the movement input when dialogue.active.

Let's write the update:

```js
function update(dt){
  // day night
  dayT=(dayT+dt/DAY_LEN)%1;
  
  // dialogue
  if(dialogue.active){ dialogue.charT+=dt*45; }
  
  // AI
  aiAttack=false;
  if(autoplay && !dialogue.active) updateAI(dt);
  
  // input gather
  let ix=0, iy=0;
  if(!dialogue.active){
    if(keys['a']||keys['arrowleft']) ix--;
    if(keys['d']||keys['arrowright']) ix++;
    if(keys['w']||keys['arrowup']) iy--;
    if(keys['s']||keys['arrowdown']) iy++;
  }
  ...
}
```

But the AI sets input flags. Let me have the AI set `aiInput={left,right,up,down,attack}` and merge:

```js
if(!dialogue.active){
  if(keys['a']||keys['arrowleft']||aiInput.left) ix--;
  ...
}
```

And aiInput is reset each frame before updateAI.

OK.

Let me write updateAI to set aiInput.

```js
function updateAI(dt){
  aiInput.left=aiInput.right=aiInput.up=aiInput.down=aiInput.attack=false;
  
  if(dialogue.active) return;  // handled elsewhere
  
  // find nearest monster
  let mon=null, md=999;
  for(const m of monsters){
    if(m.hp<=0) continue;
    const d=Math.hypot(m.x-hero.x,m.y-hero.y);
    if(d<md){md=d;mon=m;}
  }
  
  if(mon && md<100){
    if(md>20) pressToward(mon.x,mon.y);
    else { faceToward(mon.x,mon.y); aiInput.attack=true; }
    return;
  }
  
  let goal=null, interact=false;
  if(quest.stage===0||quest.stage===2){ goal={x:elder.x,y:elder.y}; interact=true; }
  else if(quest.stage===1){ goal={x:amulet.x,y:amulet.y}; }
  
  if(goal){
    const d=Math.hypot(goal.x-hero.x,goal.y-hero.y);
    if(interact && d<26){ tryInteract(); return; }
    followPath(goal.x,goal.y,dt);
    return;
  }
  
  // wander
  ai.wanderT-=dt;
  if(ai.wanderT<=0){ ai.wanderT=2+Math.random()*2; ai.wx=hero.x+(Math.random()-0.5)*80; ai.wy=hero.y+(Math.random()-0.5)*80; }
  pressToward(ai.wx,ai.wy);
}
```

Wait, but `tryInteract` starts a dialogue, and then on the next frame dialogue.active is true so the AI returns early. Good.

But there's a subtlety: `tryInteract` is called every frame while d<26 until the dialogue starts. Since tryInteract starts the dialogue immediately, that's fine.

Hmm, but if the elder's dialogue ends and the quest stage is still 0 (shouldn't happen), it would loop. Fine.

Also, `aiInput.attack=true` — the attack triggers in the hero update.

`faceToward`: sets the hero's direction toward the target. Let's implement it directly:
```js
function faceToward(tx,ty){
  const dx=tx-hero.x, dy=ty-hero.y;
  if(Math.abs(dx)>Math.abs(dy)) hero.dir = dx<0?'left':'right';
  else hero.dir = dy<0?'up':'down';
}
```

Hmm, but if the hero is moving, the direction is set by movement. Let's just set it here and let movement override. Actually when attacking, we don't press movement, so the direction stays.

Hmm, but the direction is set in the movement code only when moving. So faceToward works.

Wait, but in the hero update, if no movement keys, we don't change hero.dir. So faceToward's setting persists. Good.

But the order matters: updateAI runs before the hero movement update. So if the AI presses movement, the movement update overrides the direction. When it doesn't press, faceToward's value holds. Good.

`pressToward`:
```js
function pressToward(tx,ty){
  const dx=tx-hero.x, dy=ty-hero.y;
  if(dx<-3) aiInput.left=true; else if(dx>3) aiInput.right=true;
  if(dy<-3) aiInput.up=true; else if(dy>3) aiInput.down=true;
}
```

Good.

Now, `resetAI` when toggling autoplay on: clear the path, reset timers.

Now the render function. Let me write it.

```js
function render(){
  const camX = clamp(Math.round(hero.x - VW/2), 0, MW*TS-VW);
  const camY = clamp(Math.round(hero.y - VH/2), 0, MH*TS-VH);
  
  ctx.fillStyle='#000'; ctx.fillRect(0,0,VW,VH);
  
  const x0=Math.floor(camX/TS), y0=Math.floor(camY/TS);
  const x1=x0+Math.ceil(VW/TS)+1, y1=y0+Math.ceil(VH/TS)+1;
  for(let y=y0;y<=y1;y++)for(let x=x0;x<=x1;x++){
    if(x<0||y<0||x>=MW||y>=MH) continue;
    const t=map[y*MW+x];
    const arr=TILE_IMGS[t];
    if(!arr) continue;
    const img=arr[(x*7+y*13)%arr.length];
    ctx.drawImage(img, x*TS-camX, y*TS-camY);
  }
  
  // entities sorted
  ...
  
  // day-night tint
  ...
  
  // HUD
  ...
}
```

Note: `MW*TS-VW = 640-320 = 320`. camX in [0,320]. Good.
`MH*TS-VH = 640-180 = 460`. camY in [0,460]. Good.

Now let me write the entity drawing.

drawHero:
```js
const set=heroSprites;
const img=set[hero.dir][hero.frame];
ctx.drawImage(img, Math.round(hero.x-6-camX), Math.round(hero.y-11-camY));
```
Sprite is 12x16. hero.y-11 is the top. Bottom at hero.y+5. Good.

Hmm, but I should add a shadow. Let's draw an ellipse shadow under each entity:
```js
ctx.fillStyle='rgba(0,0,0,0.25)';
ctx.beginPath(); ctx.ellipse(hero.x-camX, hero.y+5-camY, 6, 3, 0, 0, Math.PI*2); ctx.fill();
```
That's fine.

Hit flash: draw the sprite with a red overlay. Use a temp approach: draw the sprite, then draw it again with globalCompositeOperation='source-atop' and a red fill... complex. 

Alternative: when hitFlash>0, draw a white/red silhouette. Let's pre-render a white version of each sprite? That's a lot.

Simpler: use ctx.filter = 'brightness(2)' — but that's slow-ish and may not be pixel-perfect. Let's just draw the sprite normally and add a red flash overlay rect over the entity's bounding box with low alpha. Meh.

Alternative: use globalAlpha and draw a red rectangle. Let's just skip the hit flash or use a simple approach: draw the sprite, then draw a semi-transparent red rect over the sprite's bounding box with 'source-atop'? That would affect the whole canvas.

Actually, we can create a tinted copy of the sprite once per sprite (a white silhouette) using a temporary canvas. Let's do it lazily and cache.

Actually, simplest: for the hit flash, just scale the sprite slightly or draw it offset. Let's just draw the damage numbers and skip the flash. Or: when hitFlash>0, draw the sprite twice with a 1px offset in a bright color... no.

Let me do this: create a helper `tintSprite(src, color)` that returns a canvas with the sprite's non-transparent pixels replaced by the color. Do it once for each sprite and cache in a Map.

```js
const tintCache=new Map();
function tinted(src,color){
  const key=src.__id+color;  // need an id
  ...
}
```
Let's just assign an id to each sprite canvas when created.

Actually, simpler approach for the flash: draw the sprite normally, then set `ctx.globalCompositeOperation='lighter'` and draw a white-ish rect clipped to... no.

OK, let's do the tint cache properly. It's not much code:

```js
let spriteId=0;
const tintCache=new Map();
function tintOf(src,color){
  const key=src.__sid+color;
  let c=tintCache.get(key);
  if(c) return c;
  c=document.createElement('canvas'); c.width=src.width; c.height=src.height;
  const g=c.getContext('2d');
  g.drawImage(src,0,0);
  g.globalCompositeOperation='source-in';
  g.fillStyle=color; g.fillRect(0,0,c.width,c.height);
  tintCache.set(key,c);
  return c;
}
```
And assign `src.__sid = ++spriteId` in makeSprite and flipSprite.

That works nicely. Use 'rgba(255,80,80,0.8)' for the hit flash... but 'source-in' with alpha works.

Hmm, for the flash we want a partial overlay. Let's just draw the tinted version at full alpha for a few frames — that reads as a hit flash. Actually a full red silhouette is a classic hit flash. Good.

OK.

Now let's write everything. I'll be careful with the details.

Let me also handle the "controls shown on screen at the start" — show a controls panel for the first ~12 seconds, or always show a compact hint at the bottom. I'll show a full controls overlay for the first 8 seconds, and a compact hint line always.

Actually the requirement: "the controls are shown on screen at the start". Let's show a semi-transparent panel with the controls for the first 10 seconds (fading out), plus a permanent compact hint.

Hmm, but the demo mode is on at the start, and the panel would cover things. Let's make it a small panel at the bottom that fades after 10s.

OK.

Let me write the final code now.

One more consideration: the game must be playable. When the player presses a key, autoplay stops and they control the hero. Good.

Also, when autoplay is toggled back on with P, the AI resumes.

Let me write it all.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Amulet of the Vale</title>
<style>
  html,body{margin:0;padding:0;height:100%;background:#07070c;overflow:hidden;}
  body{display:flex;align-items:center;justify-content:center;}
  canvas{image-rendering:pixelated;image-rendering:crisp-edges;display:block;}
</style>
</head>
<body>
<canvas id="game" width="320" height="180"></canvas>
<script>
(function(){
'use strict';
...
})();
</script>
</body>
</html>
```

Let me write the JS now in full.

I'll write it carefully.

```js
// ---------- helpers ----------
const VW=320, VH=180, TS=16, MW=40, MH=40;
const clamp=(v,a,b)=>v<a?a:(v>b?b:v);
function rng(seed){let s=(seed>>>0)||1;return function(){s=(s*1664525+1013904223)>>>0;return s/4294967296;};}
```

Canvas setup:
```js
const canvas=document.getElementById('game');
const ctx=canvas.getContext('2d');
ctx.imageSmoothingEnabled=false;
function resize(){
  const s=Math.min(window.innerWidth/VW, window.innerHeight/VH);
  const si=s>=1?Math.floor(s):s;
  canvas.style.width=(VW*si)+'px';
  canvas.style.height=(VH*si)+'px';
}
window.addEventListener('resize',resize); resize();
```

Sprite helpers.

Tiles.

Let me write the tile maker:

```js
function makeTile(fn){const c=document.createElement('canvas');c.width=16;c.height=16;const g=c.getContext('2d');fn(g);return c;}
```

Grass variants:
```js
function grassTile(seed,base,spec1,spec2){
  return makeTile(g=>{
    const r=rng(seed);
    g.fillStyle=base; g.fillRect(0,0,16,16);
    for(let i=0;i<34;i++){
      const x=(r()*16)|0,y=(r()*16)|0;
      g.fillStyle=r()<0.5?spec1:spec2;
      g.fillRect(x,y,1,1);
    }
  });
}
```

Flower tile.

Dirt tile.

Water tile.

Tree tile.

Bush tile.

Wall, roof, door, floor, swall, torch.

Let me now write out the full TILE_IMGS array.

```js
const TILE_IMGS=[];
TILE_IMGS[T.GRASS]=[grassTile(1,'#4e9a45','#458a3d','#5aa851'),grassTile(2,'#4e9a45','#458a3d','#5aa851'),grassTile(3,'#4e9a45','#458a3d','#5aa851'),grassTile(4,'#4e9a45','#458a3d','#5aa851')];
TILE_IMGS[T.GRASS2]=[grassTile(5,'#458f3e','#3c7c36','#52a04a'),grassTile(6,'#458f3e','#3c7c36','#52a04a')];
TILE_IMGS[T.FLOWER]=[flowerTile(7),flowerTile(8)];
TILE_IMGS[T.DIRT]=[dirtTile(9),dirtTile(10),dirtTile(11)];
TILE_IMGS[T.WATER]=[waterTile(12),waterTile(13)];
TILE_IMGS[T.TREE]=[treeTile(14),treeTile(15)];
TILE_IMGS[T.BUSH]=[bushTile(16),bushTile(17)];
TILE_IMGS[T.WALL]=[wallTile()];
TILE_IMGS[T.ROOF]=[roofTile()];
TILE_IMGS[T.DOOR]=[doorTile()];
TILE_IMGS[T.FLOOR]=[floorTile(18),floorTile(19)];
TILE_IMGS[T.SWALL]=[swallTile()];
TILE_IMGS[T.TORCH]=[torchTile()];
```

OK.

Now let's write all the tile functions.

I'll write them inline.

Now, the full code. Let me write it out.

I need to be careful about the order of definitions (function declarations hoist, const doesn't). I'll use function declarations for the most part.

Let me write it.

Also: the `T` enum.

```js
const T={GRASS:0,GRASS2:1,FLOWER:2,DIRT:3,WATER:4,TREE:5,BUSH:6,WALL:7,ROOF:8,DOOR:9,FLOOR:10,SWALL:11,TORCH:12};
```

SOLID:
```js
const SOLID=new Uint8Array(16);
[4,5,6,7,8,9,11].forEach(i=>SOLID[i]=1);
```
T.WATER=4, T.TREE=5, T.BUSH=6, T.WALL=7, T.ROOF=8, T.DOOR=9, T.SWALL=11. Yes.

Now let me write the whole thing.

For the minimap colors:
```js
const MINI_COL={
 [T.GRASS]:'#3a6f33',[T.GRASS2]:'#356a2f',[T.FLOWER]:'#4a7f3a',[T.DIRT]:'#a8895c',
 [T.WATER]:'#2a5fa8',[T.TREE]:'#1d4a1b',[T.BUSH]:'#2a5a26',[T.WALL]:'#c9a26b',
 [T.ROOF]:'#a8453a',[T.DOOR]:'#7a5228',[T.FLOOR]:'#57516a',[T.SWALL]:'#2e2a3d',[T.TORCH]:'#e08a30'
};
```

Now let me write the game state.

I'll write it all out now in the final answer.

One more thought on the AI's first action: the hero starts at (9,8) and the elder is at (13,8). The AI will path to the elder and interact. Good.

But wait — there might be a monster within 100px of the start. The slime at (18,8) is 9 tiles away = 144px. So no. Good.

Then after the dialogue, quest.stage=1, and the AI heads to the amulet. It'll path through the forest and encounter the slime at (18,8) — within 100px. It'll fight it. 

Then continue to the dungeon.

Now, the AI's monster priority: it targets the nearest monster within 100px. In the dungeon, there could be multiple. It fights them one at a time. Fine.

Potential issue: the AI could get stuck fighting monsters forever if they respawn. Let's not respawn monsters. Or respawn them slowly after 30s. Let's not respawn — simpler, and the world becomes safer as you play.

Hmm, but then the demo after the quest completes would have nothing to fight. Let's add slow respawn (every 25s, respawn a random dead monster away from the hero). Actually, let's keep it simple and not respawn. The demo can wander.

Actually, for a "good run" demo, having monsters respawn keeps it interesting. Let's add respawn after 20s at their original spot if the hero is far away (>200px).

OK.

Now let me write the final code.

Let me write out the sprite data carefully.

Also I realize I should double-check the `BODY_DOWN` row 4: "..ksesesk..." — that has 'e' at index 4 and 6, 's' at 3,5,7. Eyes at 4 and 6. Good.

Wait, but the head is 6 wide (indices 2-8 → k,s,s,s,s,h,k... no). Let me re-examine.

BODY_DOWN:
```
r0  "....kkkk...."       k at 4,5,6,7
r1  "...khhhhk..."       k at 3, h 4-7, k 8
r2  "..khhhhhhk.."       k 2, h 3-8, k 9
r3  "..khsssshk.."       k 2, h 3, s 4-7, h 8, k 9
r4  "..ksesesk..."       k 2, s 3, e 4, s 5, e 6, s 7, k 8
r5  "..ksssssk..."       k 2, s 3-7, k 8
```
Hmm, r3 has the face at 4-7 and hair at 3 and 8. r4 has eyes at 4 and 6. The face is 6 wide in r3 (h at 3, s 4-7, h 8) and 5 wide in r4 (s 3-7). Slightly inconsistent but fine visually.

Actually r4: k at 2, s at 3, e at 4, s at 5, e at 6, s at 7, k at 8. That's a 5-wide face with eyes at 4 and 6. OK, and r3's face is 4-7 with hair at 3,8. So r4's face extends one pixel left. Minor. Fine.

Let me adjust r4 to "..khseshk..." → k 2, h 3, s 4, e 5, s 6, e 7, s 8... no that's wrong.

Let's make r4: "..ksesesk..." → the face is at 3-7. And r3: "..khssssk..." hmm then no hair on the right.

Honestly, at 12px wide, it'll look fine. Let me just go with it.

Actually let me fix r3 to "..khssshk..." → k2, h3, s4,5,6, h7, k8. And r4 "..ksesesk..." → k2, s3, e4, s5, e6, s7, k8. Hmm, the eyes at 4 and 6 with s at 3,5,7.

Eh. Let's simplify the face:
r3: "..khssshk..."  (h at 3, s at 4-6, h at 7)
r4: "..khseshk..."  (h3, s4, e5, s6, h7)... that gives eyes at 5 only. 

Let me do:
r3: "..khhhsssk.."  no.

OK, final decision:
```
r2  "..khhhhhhk.."
r3  "..khsssssk.."   k2 h3 s4-8 k9  -> wait that's 2+1+1+5+1+2 = 12? . . k h s s s s s k . . = 12 ✓
r4  "..kseesek..."   hmm
```
Hmm "..kseesek..." = . . k s e e s e k . . . = 12. Two eyes adjacent. Not great.

Let's just do:
```
r3  "..khssssk..."   → . . k h s s s s k . . . = 12 ✓ (h3, s4-7, k8)
r4  "..ksesesk..."   → . . k s e s e s k . . . = 12 ✓ (s3, e4, s5, e6, s7, k8)
```
Hmm, r3 ends with k at 8 and r4 ends with k at 8. r3 starts with k at 2, r4 with k at 2. The face in r3 is at 3-7 (h,s,s,s,s) and in r4 at 3-7 (s,e,s,e,s). Consistent width! Great.

Wait, r3 "..khssssk..." = indices: 0='.',1='.',2='k',3='h',4='s',5='s',6='s',7='s',8='k',9='.',10='.',11='.'. Yes, 3-7 is the face area.
r4 "..ksesesk..." = 0='.',1='.',2='k',3='s',4='e',5='s',6='e',7='s',8='k'. Yes, 3-7 face.

Hmm, but r3 has 'h' (hair) at 3 and r4 has 's' at 3. Slight mismatch but it reads as a sideburn. Fine.

r2 "..khhhhhhk.." = k2, h3-8, k9. That's 6 wide hair. And r3's face is 3-7 with k at 8. So r2 is 1 wider. Minor.

Let's change r2 to "..khhhhhk..." = k2, h3-7, k8. Consistent. 

And r1 "...khhhhk..." = k3, h4-7, k8. Good.
r0 "....kkkk...." = k4-7. Good.

Now r5 "..ksssssk..." = k2, s3-7, k8. Good, chin.

r6 "..kkggggkk.." = k2,k3, g4-7, k8,k9. Shoulders wider. Good.

OK, updated BODY_DOWN:
```
"....kkkk....",
"...khhhhk...",
"..khhhhhk...",
"..khssssk...",
"..ksesesk...",
"..ksssssk...",
"..kkggggkk..",
".kggggggggk.",
".ksggggggsk.",
".kggggggggk.",
".kbbbbbbbbk.",
"..kppppppk..",
"..kppppppk.."
```
13 rows. 

Wait, r2 "..khhhhhk..." = . . k h h h h h k . . . = 12 ✓ (k2, h3-7, k8)
r3 "..khssssk..." = k2, h3, s4-7, k8 = 12 ✓
r4 "..ksesesk..." = k2, s3, e4, s5, e6, s7, k8 = 12 ✓
r5 "..ksssssk..." = k2, s3-7, k8 = 12 ✓

Good.

BODY_UP:
```
"....kkkk....",
"...khhhhk...",
"..khhhhhk...",
"..khhhhhk...",
"..khhhhhk...",
"..khhhhhk...",
"..kkhhhhkk..",
".kggggggggk.",
".ksggggggsk.",
".kggggggggk.",
".kbbbbbbbbk.",
"..kppppppk..",
"..kppppppk.."
```
13 rows ✓

BODY_LEFT:
```
"....kkkk....",
"...khhhhk...",
"..khhhhhk...",
"..khhsssk...",
"..khsessk...",
"..khssssk...",
"...kggggk...",
"..kggggggk..",
"..kggggggk..",
"..kggggggk..",
"..kbbbbbbk..",
"..kppppppk..",
"..kppppppk.."
```
Check:
r3 "..khhsssk..." = k2, h3, h4, s5, s6, s7, k8 = 12 ✓
r4 "..khsessk..." = k2, h3, s4, e5, s6, s7, k8 = 12 ✓  hmm eye at 5.
r5 "..khssssk..." = k2, h3, s4-7, k8 = 12 ✓
r6 "...kggggk..." = k3, g4-7, k8 = 12 ✓
r7 "..kggggggk.." = k2, g3-8, k9 = 12 ✓

Hmm r6 is 10 wide (3..8) and r7 is 10 wide (2..9)? No: r6 = . . . k g g g g k . . . → k at 3, k at 8. r7 = . . k g g g g g g k . . → k at 2, k at 9. So r7 is wider. That's the shoulder. OK fine.

Hmm, for a left-facing sprite, the body should be narrower. r6 is the neck. OK.

Alright.

Legs:
```js
const LEGS_A=["..kpp..ppk..","..koo..ook..","..kkk..kkk.."];
```
Check "..kpp..ppk.." = . . k p p . . p p k . . = 12 ✓
"..koo..ook.." = 12 ✓
"..kkk..kkk.." = 12 ✓

```js
const LEGS_B=["..kppppppk..","..koooook...","...kkkkkk..."];
```
"..kppppppk.." = 12 ✓
"..koooook..." = . . k o o o o o k . . . = 12 ✓
"...kkkkkk..." = . . . k k k k k k . . . = 12 ✓

Left legs:
```js
const LEGS_LA=["...kppppk...","...koook....","...kkkkk...."];
const LEGS_LB=["...kppppk...","..koooook...","...kkkkkk..."];
```
"...kppppk..." = . . . k p p p p k . . . = 12 ✓
"...koook...." = . . . k o o o k . . . . = 12 ✓
"...kkkkk...." = . . . k k k k k . . . . = 12 ✓
"..koooook..." = . . k o o o o o k . . . = 12 ✓
"...kkkkkk..." = 12 ✓

Good.

Total height: 13 + 3 = 16 ✓

Now the monster sprites — already defined.

Let me finalize the palettes:

```js
const P_HERO={'.':null,'k':'#1b1224','h':'#7a4a21','s':'#f2c79a','e':'#241a2e','g':'#4fae55','b':'#8a5a2b','p':'#3b4a8a','o':'#5c3f22'};
const P_ELDER={'.':null,'k':'#1b1224','h':'#cfcfd8','s':'#e8c9a0','e':'#241a2e','g':'#3f6fc0','b':'#4a3a2a','p':'#2a3a6a','o':'#3a2a1a'};
const P_KID={'.':null,'k':'#1b1224','h':'#e0a030','s':'#f7d3a8','e':'#241a2e','g':'#e0d040','b':'#8a5a2b','p':'#4a6a8a','o':'#5c3f22'};
const P_MERCH={'.':null,'k':'#1b1224','h':'#3a2a1a','s':'#e8c090','e':'#241a2e','g':'#c04a3a','b':'#5a4a3a','p':'#4a3a2a','o':'#3a2a1a'};
```

OK.

Now, writing the final code. Let me be thorough.

I'll now produce the complete file.

Some final details on rendering the HUD bars:

```js
function bar(x,y,w,h,pct,col,bg){
  ctx.fillStyle=bg||'#22222e'; ctx.fillRect(x,y,w,h);
  ctx.fillStyle=col; ctx.fillRect(x+1,y+1,Math.max(0,Math.round((w-2)*pct)),h-2);
  ctx.strokeStyle='#000'; ctx.lineWidth=1; ctx.strokeRect(x+0.5,y+0.5,w-1,h-1);
}
```

HP bar: x=4,y=4,w=70,h=7.
EXP bar: x=4,y=13,w=70,h=4.

Level text: at x=78, y=4: "LV 1" in yellow.

Quest panel: at x=4, y=20:
"QUEST" in gold, then the objective in white.

Hmm, y=20 with 8px font. Let's do:
- y=21: "QUEST: Find the Amulet" (gold)
- y=30: objective (white)

Actually, let me make the quest box more visible:
```js
ctx.fillStyle='rgba(10,10,20,0.6)';
ctx.fillRect(2,19,150,20);
```
Hmm, that would cover the world. It's fine, it's a HUD.

Let's do a compact design:
- x=4,y=4: HP bar (70x7)
- x=4,y=13: EXP bar (70x4)
- x=78,y=4: "LV 1"
- x=4,y=21: "◆ Find the Amulet" (gold, 8px)
- x=4,y=30: objective (light gray, 8px)

Hmm, "◆" might not render in all fonts. Use ">".

OK.

Let me write the final code.

For the controls overlay at the start:
```js
if(startTime < 12){
  const a = startTime<10 ? 1 : (12-startTime)/2;
  ctx.globalAlpha=a;
  ctx.fillStyle='rgba(8,8,16,0.85)';
  ctx.fillRect(60, 120, 200, 46);
  ctx.strokeStyle='#e0d060'; ctx.strokeRect(60.5,120.5,199,45);
  ctx.fillStyle='#e0d060'; ctx.font='bold 8px monospace'; ctx.textAlign='center';
  ctx.fillText('CONTROLS', 160, 126);
  ctx.fillStyle='#e8e8f0'; ctx.font='8px monospace';
  ctx.fillText('WASD / Arrows  -  Move', 160, 138);
  ctx.fillText('SPACE / J  -  Attack', 160, 148);
  ctx.fillText('E / ENTER  -  Talk    I  -  Bag    1  -  Potion', 160, 158);
  ctx.textAlign='left';
  ctx.globalAlpha=1;
}
```

Hmm, that overlaps the dialogue box area. But dialogue is unlikely in the first 12s... actually the AI talks to the elder at ~4s. So they'd overlap.

Let's put the controls panel at the top-left instead, or make the dialogue box not overlap. 

Alternative: show the controls panel at the top-center, and the dialogue at the bottom.

The top area has the HP bar (x 4-74, y 4-17) and the minimap (x 252-316, y 4-68). So the center-top from x=80 to x=250 is free... but the quest text is at x=4, y=21-38.

Hmm. Let's put the controls panel in the middle of the screen, fading out after 8 seconds. During the first 8 seconds, the AI is walking to the elder (dialogue starts ~4s). Overlap.

OK, alternative: make the dialogue box appear at the bottom, and put the controls panel at the top-center, y=4..40, x=76..248.

Quest text at x=4, y=21 is fine (x 4..150 might overlap x=76). Hmm.

Let me restructure the HUD:
- Top-left: HP bar, EXP bar, level. (x 4..80, y 4..17)
- Below: quest objective at y=21, x=4. Width up to ~140.
- Top-right: minimap (x 252..316, y 4..68)
- Controls panel: center, y=100..145 — but the dialogue box is at y=134..174.

OK: dialogue box at y = VH-44 = 136 to VH-8 = 172.
Controls panel at y = 70..120. That's mid-screen. It's fine, it fades.

Actually, mid-screen overlay is fine for a "controls at start" screen. Let's do y=60..112.

Hmm, it covers the hero. Whatever, it fades after 8s.

Actually, let's make it smaller and put it at the bottom-left area, above the dialogue:
x=4, y=110, w=170, h=40.

The dialogue box spans x=8..312, y=136..172. So no overlap. 

But the permanent compact hint line at the bottom (y=172) would overlap the dialogue. Let's move the permanent hint to y=172 and hide it when the dialogue is active.

Hmm, VH=180. The dialogue box at y=136..172, and the hint at y=172..180. Tight.

Let's put the dialogue box at y=130..170 and the hint at y=172.

OK.

Final layout:
- Dialogue box: x=8, y=128, w=304, h=42. (128..170)
- Permanent hint: y=172, x=4. Hidden when dialogue active.
- Controls panel (start): x=4, y=86, w=180, h=38. Fades after 10s.

Hmm, x=4..184, y=86..124. That's in the middle-left. OK.

Actually, you know what — since autoplay is on by default, the "controls shown at start" could just be the permanent hint line plus a highlighted panel. Let's do the panel at the top-center-ish: x=76, y=4, w=172, h=40. And the quest text moves to below the HP bar.

Ugh. Let me just do:
- Controls panel: x=60, y=44, w=200, h=44. Fades after 10s. (Center-ish, doesn't overlap the minimap at x>=252 or the HP bar at y<=38.)

Wait, the quest text is at y=21..38, x=4..150. The panel at y=44..88, x=60..260. The minimap at x=252..316, y=4..68. Overlap at x 252..260, y 44..68. Minor. Let's set the panel to x=50..250.

OK: panel x=50, y=44, w=200, h=44.

Fine.

Now, let me write the code.

Also, I should double check: `ctx.font='8px monospace'` — the default monospace at 8px. Text will be about 4.8px wide per char. So a 50-char string is 240px. OK.

Let me use 'bold 8px monospace' for headers.

Alright, writing the final code.

Let me also add a subtle vignette / dungeon darkness. Skip.

Let me write it.

Actually, one more: the amulet sprite. Let's draw it procedurally with a glow.

```js
function drawAmulet(camX,camY){
  const t=performance.now()/1000;
  const bob=Math.sin(t*3)*2;
  const x=amulet.x-camX, y=amulet.y-camY+bob;
  // glow
  const g=ctx.createRadialGradient(x,y,0,x,y,14);
  g.addColorStop(0,'rgba(255,220,80,0.5)');
  g.addColorStop(1,'rgba(255,220,80,0)');
  ctx.fillStyle=g;
  ctx.fillRect(x-14,y-14,28,28);
  // amulet shape
  ctx.fillStyle='#ffe060';
  ctx.fillRect(x-4,y-6,8,8);
  ctx.fillStyle='#fff0a0';
  ctx.fillRect(x-2,y-4,4,4);
  ctx.fillStyle='#c0a020';
  ctx.fillRect(x-4,y-6,8,1);
  ctx.fillRect(x-4,y+1,8,1);
}
```

createRadialGradient every frame is a bit slow but OK.

Actually, let's pre-render the glow to a canvas. Meh, it's fine.

OK writing now.

For the slash effect:
```js
slashes.push({x,y,dir,t:0.15,max:0.15});
```
Draw as an arc or a few lines. Let's draw a white arc in the facing direction.

```js
for(const s of slashes){
  const a=s.t/s.max;
  ctx.globalAlpha=a;
  ctx.strokeStyle='#ffffff'; ctx.lineWidth=2;
  ctx.beginPath();
  const ang = s.dir==='right'?0 : s.dir==='left'?Math.PI : s.dir==='up'?-Math.PI/2 : Math.PI/2;
  ctx.arc(s.x-camX, s.y-camY, 12, ang-0.7, ang+0.7);
  ctx.stroke();
  ctx.globalAlpha=1;
}
```

Good.

Now let's write everything out.

Final concern: performance. Drawing ~21x13 = 273 tiles per frame with drawImage. Fine.

Let's write it.

Oh, also: `ctx.ellipse` for shadows — supported in modern browsers. Fine.

Let me write the final code.

I'll now write out the complete HTML.

One more: the `initAudio` needs to be called on a user gesture. For the autoplay demo, there's no gesture, so audio won't play. That's OK — but the requirement says "music-free sound". It'll work once the user interacts. Also, I can try to create the AudioContext on load; some browsers allow it but keep it suspended. We'll resume on the first interaction.

Also, when autoplay stops due to a key press, we call initAudio.

OK.

Writing now.

Let me handle the `keys` object with lowercase keys. Arrow keys give 'ArrowUp' → lowercase 'arrowup'. Space gives ' '. Good.

Also need to handle key repeat for space (attack). Using the keys state handles that.

For 'e' interact: on keydown only.

Let me write the code.

```js
window.addEventListener('keydown',e=>{
  const k=e.key.length===1?e.key.toLowerCase():e.key.toLowerCase();
  ...
});
```
Just `e.key.toLowerCase()`.

Handle 'p' first.

Then the control keys.

Then set keys[k]=true.

Special: if the dialogue is active and space/enter/e is pressed → advanceDialogue().

Let's write:
```js
if(k===' '||k==='j'||k==='enter'||k==='e'){
  if(dialogue.active){ advanceDialogue(); e.preventDefault(); return; }
}
```
Hmm, but 'e' when the dialogue is not active triggers tryInteract.

Let me do:
```js
if(dialogue.active){
  if(k===' '||k==='j'||k==='enter'||k==='e'){ advanceDialogue(); }
  e.preventDefault();
  return;
}
```
And then normal handling.

But we still want the keys state to be tracked for movement... while the dialogue is active, movement is blocked anyway. So it's fine to return early.

Hmm, but then on keyup, we need to clear. Since we return early on keydown, keys[k] might not be set. Let's just always set keys[k]=true and handle the dialogue separately.

OK, let me write:

```js
window.addEventListener('keydown',e=>{
  const k=e.key.toLowerCase();
  initAudio();
  if(k==='p'){ autoplay=!autoplay; if(autoplay) resetAI(); e.preventDefault(); return; }
  const ctrl=['arrowup','arrowdown','arrowleft','arrowright','w','a','s','d',' ','j','e','i','1','enter'];
  if(ctrl.includes(k)){
    if(autoplay) autoplay=false;
    e.preventDefault();
  }
  if(!keys[k]){
    // fresh press
    if(dialogue.active){
      if(k===' '||k==='j'||k==='enter'||k==='e') advanceDialogue();
    } else {
      if(k==='e'||k==='enter') tryInteract();
      if(k==='i') invOpen=!invOpen;
      if(k==='1') usePotion();
    }
  }
  keys[k]=true;
});
window.addEventListener('keyup',e=>{ keys[e.key.toLowerCase()]=false; });
```

Good.

Now, `if(autoplay) autoplay=false;` — but this happens on any control key, including 'i'. That's per the spec: "the demo must stop as soon as the player presses a control key".

OK.

Now let's write the whole thing.

I'll write the code now, final.

For the minimap dots, I need entity positions. Let me write:

```js
function drawMinimap(){
  const mx=VW-68, my=4, mw=64, mh=64;
  ctx.fillStyle='rgba(0,0,0,0.6)'; ctx.fillRect(mx-1,my-1,mw+2,mh+2);
  ctx.drawImage(miniCanvas, mx, my, mw, mh);
  ctx.strokeStyle='#8890a8'; ctx.lineWidth=1; ctx.strokeRect(mx-0.5,my-0.5,mw+1,mh+1);
  
  const sx=mw/MW, sy=mh/MH;
  const dot=(wx,wy,col,size)=>{
    ctx.fillStyle=col;
    ctx.fillRect(mx+wx/TS*sx-size/2, my+wy/TS*sy-size/2, size, size);
  };
  for(const n of npcs) dot(n.x,n.y,'#ffe060',2);
  for(const m of monsters) if(m.hp>0) dot(m.x,m.y,'#ff5050',2);
  if(!amulet.taken) dot(amulet.x,amulet.y,'#ffe060',3);
  dot(hero.x,hero.y,'#ffffff',3);
}
```

Good.

Now, writing everything out.

I think I'm ready. Let me produce the file.

One more check on the quest stage flow with the AI:

1. Start: quest.stage=0. AI targets the elder. Within 26px → tryInteract → talkTo(elder) → stage 0 → dialogue starts, quest.stage=1 immediately.
2. Dialogue active → AI waits, advancing every 0.8s. 4 lines → ~3.2s.
3. Dialogue ends. quest.stage=1. AI targets the amulet.
4. Path to the amulet. Encounters monsters → fights.
5. Reaches the amulet (33,33) → picks it up → quest.stage=2.
6. AI targets the elder. Walks back.
7. Within 26px → tryInteract → talkTo(elder) with stage 2 → dialogue, quest.stage=3, reward.
8. Dialogue ends. stage 3 → AI wanders.

The quest is complete. 

For the wander, the AI just moves randomly. Fine.

Let me make the wander more interesting: if stage 3, the AI hunts monsters. Let's set: if stage 3, find the nearest monster anywhere and go fight it. That makes a nice continuous demo.

Let's do: if stage===3, find the nearest monster within 400px and path to it. Otherwise wander.

OK.

Now writing.

Actually, one thing: `tryInteract` is called by the AI when within 26px. But `tryInteract` finds the nearest NPC within 30px. The elder is at (13,8). Fine.

But there's a risk: if the hero passes near the kid or merchant, tryInteract might target them. The AI only calls tryInteract when the goal is the elder and it's within 26px of the elder. So it's fine.

Let me write `tryInteract` to take an optional target.

OK, writing now for real.

Let me also make sure the hero doesn't start inside a wall. (9,8) is DIRT. Good.

Also, the elder at (13,8) — DIRT. Good.

Let me write.

Final code:

Also I want to make sure `MON` configs reference the right sprites.

```js
const MON={
  slime:{hp:14,dmg:2,speed:20,exp:9,chase:80,sprite:SPR_SLIME,w:12,h:12,name:'Slime',color:'#4ad06a'},
  bat:{hp:11,dmg:3,speed:46,exp:11,chase:110,sprite:SPR_BAT,w:12,h:10,name:'Bat',color:'#8a5ad0'},
  skel:{hp:20,dmg:4,speed:30,exp:16,chase:95,sprite:SPR_SKEL,w:12,h:14,name:'Skeleton',color:'#e6e6ee'},
  boss:{hp:50,dmg:6,speed:26,exp:50,chase:120,sprite:SPR_BOSS,w:14,h:14,name:'Bone Lord',color:'#ff6060'}
};
```

Boss sprite: use the skeleton sprite with a different palette (red eyes, dark armor). Let's make a boss palette:
```js
const P_BOSS={'.':null,'k':'#1a0e18','w':'#c8c0d8','e':'#ff3020'};
```
Good.

OK writing.

Let me handle `hero.dir` for the sprite set lookup: heroSprites[hero.dir][hero.frame].

Now writing the final answer.

Let me carefully compose the code.

Also, I need `miniCanvas` built after genWorld.

Let's go.

def the render order: tiles, shadows, entities, slashes, damage numbers, tint, HUD, dialogue, controls.

Actually the tint should be applied over the world but under the HUD. And the damage numbers should be under the tint too? Probably fine either way. Let's put the tint after the entities and damage numbers.

OK.

Writing.

I'll write `drawText` helpers to reduce verbosity.

Let me finalize.

For the HP bar color, use green when >50%, yellow when >25%, red below.

Let me write it.

Final code below.

Let me count the lines... it'll be long, maybe 800-1000 lines. That's fine.

Writing.

One thing about `makeSprite` with the palette: characters not in the palette → undefined → skipped. Good, so unused chars are transparent.

Let me write the code.

Also: `ctx.textBaseline='top'` and `ctx.textAlign='left'` set once at the start of render.

Let me write.

I also need to handle the case where the player kills all monsters and the AI has nothing to do. Fine.

Writing now.

Also: when the hero dies, respawn at (9,8) with half HP and set autoplay... keep autoplay on.

Let's write `heroDie`:
```js
function heroDie(){
  sfx('die');
  hero.hp=Math.floor(hero.maxhp/2);
  hero.x=9*TS+8; hero.y=8*TS+8;
  hero.invuln=1.5;
  addDamageNumber(hero.x,hero.y-20,'...','#ff8080');
  ai.path=[]; ai.pi=0;
}
```

OK.

Writing the final answer now.

Let me make sure the sfx function handles a null actx gracefully.

```js
function sfx(name){
  if(!actx) return;
  const t=actx.currentTime;
  switch(name){
    case 'swing': tone(420,0.08,'square',0.04,180); break;
    case 'hit': tone(180,0.09,'square',0.05,80); break;
    case 'hurt': tone(140,0.18,'sawtooth',0.06,70); break;
    case 'kill': tone(300,0.08,'square',0.05,600); setTimeout(()=>tone(600,0.1,'square',0.05,900),70); break;
    case 'pickup': tone(660,0.08,'square',0.05); setTimeout(()=>tone(990,0.12,'square',0.05),80); break;
    case 'level': [523,659,784,1047].forEach((f,i)=>setTimeout(()=>tone(f,0.12,'square',0.05),i*80)); break;
    case 'talk': tone(500+Math.random()*200,0.04,'square',0.025); break;
    case 'quest': [659,784,1047].forEach((f,i)=>setTimeout(()=>tone(f,0.15,'triangle',0.05),i*100)); break;
    case 'die': tone(300,0.5,'sawtooth',0.07,60); break;
  }
}
```

setTimeout with actx — fine.

OK, writing the final answer.

Let me write out the whole thing now, carefully.

Actually, for the `tone` function with `exponentialRampToValueAtTime`, the start value must be > 0. I set the gain to `vol` which is > 0. Good.

Let me write.

Also `o.frequency.exponentialRampToValueAtTime` requires the target > 0. I use Math.max(20, freqEnd). Good.

Final write.

Let me think about the AI stuck detection once more. The hero could get stuck on a tree corner. With hw=5 and 16px tiles, the hero's 10x10 box needs a 10px gap. A 1-tile corridor is 16px, so 3px clearance on each side. When moving diagonally toward a waypoint, the axis-separated movement will slide along walls. Should be OK.

But the BFS path goes through tile centers, so the hero moves axis-aligned mostly. Good.

Hmm, one issue: the hero targets the waypoint center. If the path goes right, right, down, the hero moves right to the first center, then right to the second, then down. Since it's axis-aligned, no corner clipping. Good.

But the `aiPress` uses a deadzone of 3px, so the hero might overshoot slightly and then correct. Fine.

Let me increase the waypoint advance threshold to 7px to avoid oscillation.

OK.

Writing.

Let me also add: when the AI is following a path and the hero hasn't moved in 1.5s, force a repath.

Simple: track hero.lastX/lastY and a stuck timer.

```js
if(Math.hypot(hero.x-ai.lastX, hero.y-ai.lastY) < 2) ai.stuck += dt; else ai.stuck = 0;
ai.lastX=hero.x; ai.lastY=hero.y;
if(ai.stuck>1.2){ ai.stuck=0; ai.repathT=0; }
```

Good.

Now writing for real.

I'll produce the final file.

Let me write out all the code.

```js
(function(){
'use strict';

// ============ SETUP ============
const VW=320, VH=180, TS=16, MW=40, MH=40;
const canvas=document.getElementById('game');
const ctx=canvas.getContext('2d');
ctx.imageSmoothingEnabled=false;
function resize(){
  const s=Math.min(window.innerWidth/VW, window.innerHeight/VH);
  const si=s>=1?Math.floor(s):s;
  canvas.style.width=(VW*si)+'px';
  canvas.style.height=(VH*si)+'px';
}
window.addEventListener('resize',resize); resize();

const clamp=(v,a,b)=>v<a?a:(v>b?b:v);
function rng(seed){let s=(seed>>>0)||1;return function(){s=(s*1664525+1013904223)>>>0;return s/4294967296;};}

// ============ SPRITES ============
let SPRITE_ID=0;
function makeSprite(rows,pal){
  const w=rows.reduce((m,r)=>Math.max(m,r.length),0), h=rows.length;
  const c=document.createElement('canvas'); c.width=w; c.height=h; c.__sid=++SPRITE_ID;
  const g=c.getContext('2d');
  for(let y=0;y<h;y++){
    const row=rows[y];
    for(let x=0;x<row.length;x++){
      const col=pal[row[x]];
      if(col){ g.fillStyle=col; g.fillRect(x,y,1,1); }
    }
  }
  return c;
}
function flipSprite(src){
  const c=document.createElement('canvas'); c.width=src.width; c.height=src.height; c.__sid=++SPRITE_ID;
  const g=c.getContext('2d'); g.translate(src.width,0); g.scale(-1,1); g.drawImage(src,0,0);
  return c;
}
const tintCache=new Map();
function tintOf(src,color){
  const key=src.__sid+'|'+color;
  let c=tintCache.get(key);
  if(c) return c;
  c=document.createElement('canvas'); c.width=src.width; c.height=src.height;
  const g=c.getContext('2d');
  g.drawImage(src,0,0);
  g.globalCompositeOperation='source-in';
  g.fillStyle=color; g.fillRect(0,0,c.width,c.height);
  tintCache.set(key,c);
  return c;
}
```

Good.

Now the body data and building.

Then tiles.

Then world.

I'll write it all out in the answer.

Let me now write the complete file.

I need to double check `ctx.font` sizes. 8px monospace. At 320x180 scaled 5x, that's 40px on screen. Fine.

Writing.

Final answer below.