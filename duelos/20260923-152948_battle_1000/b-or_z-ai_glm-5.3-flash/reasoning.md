Let me design this battle simulation carefully.

**Core requirements:**
- 1000+ units (500 per side), red vs blue
- Top-down field with slight perspective
- Units move toward nearest enemy, fight on contact, lose health, die with blood/dust puff
- Formations break into chaotic melee
- Live survivor counter per side
- Battle title
- Winner celebrates, then restart with a new battle
- Spatial partitioning for performance (uniform grid hash)
- Auto-starts, no interaction
- Single self-contained HTML file, no external resources

**First 30 seconds must show everything important:**
- Charge phase (formations advancing)
- Clash / melee
- Deaths with puffs
- Counters
- Ideally the battle concludes within ~30-45s so a winner celebration is captured. Let me tune combat so battles resolve in roughly 25-40 seconds. With 500 vs 500, units fighting 1v1 with ~3-5 hits to kill, attack rate ~2 hits/sec... Actually let me make combat fast: attack cooldown ~0.5s, damage 12-20, HP 100 → ~5-8 hits → 3-4 seconds per kill. With 1000 units in a front line clash, kills happen fast in aggregate. Battle of 1000 units could resolve in 20-40s. I can also speed up sim time slightly. Let me target battle duration ~25-35s.

To ensure the full arc fits in 30s window, I could make it so: charge (~3s), clash (~1s), melee grind (~20-25s), mop-up + celebration (~5s). Total ~30-35s. The recording window "shows everything important within the first 30 seconds" — the winner celebration might start right around 30s. To be safe, I'll tune numbers so battles conclude in ~22-28 seconds typically. Also I can add slight per-battle randomization but keep it controlled.

Actually, another approach: I can accelerate time — make the simulation run at a slight timescale (e.g., 1.15x) or tune units to be fragile. Let me tune:
- HP: 100, damage per hit: 18-26 → ~4-6 hits
- Attack cooldown: 0.45s → kill time ~2-2.7s per duel
- With flanking and multiple attackers, front-line units die in ~2-4s
- 500 units per side: units deeper in formation keep walking into combat, so overall battle is a continuous grind. Rate of deaths: maybe 30-50/sec during peak. 1000 deaths / 40 per sec ≈ 25s. 

Also add a "morale" mechanic: when a side drops below a fraction (say 25%) of the enemy count, remaining units rout/flee — this accelerates the ending and looks dramatic. Then winners celebrate (cheer animation: jumping, weapon raising), losers flee or get cut down. Rout makes end state clean: winners alive celebrate.

**Visual design:**

I want this to feel authored — a painterly top-down battlefield with slight perspective. Ideas:

- Field: dark, moody grass/dirt with subtle noise texture (pre-rendered to offscreen canvas), vignette, maybe battle-worn decals (scorch marks, craters) that accumulate during battle — nice touch: persistent scars on the field.
- Slight perspective: I'll fake it with a subtle vertical squash + scale gradient — units near the "top" (far) are smaller and closer together; near bottom larger. Simple approach: world coordinates in a plane, projected: screenY = horizonY + worldY * (1 + worldY*k) or use a scale factor that grows with worldY. Projection: scale(y) = lerp(0.72, 1.12, y/H) for both unit size and screenY spacing: screenY = topY + (y/H)^1.15 * drawHeight or something. Simplest: keep sim in world space (0..W, 0..H), project:
  - p = y / H (0 far, 1 near)
  - scale = 0.75 + 0.5*p
  - sy = horizon + p^1.25 * fieldDepth? Hmm, need invertibility? Not needed — sim is in world space, projection is display only. But movement speed appears different at different depths — that's fine and actually adds realism (far units move slower on screen).
  
  Actually let me do a proper trapezoid projection: world is a rectangle; screen shows a trapezoid (narrower at top). That gives genuine perspective feel:
  - screenX = cx + (x - W/2) * scale(p) + slightShake
  - screenY = f(p) where p = y/H: sy = topY + p^gamma * depth... For perspective, equal world steps in y should appear smaller near the top: sy = topY + depth * (something like p*(2-p*? )). Linear perspective: sy = topY + depth * (p * a / (1 + p*(a-1)))? Let's keep simple: sy = topY + depth * p^1.6? That compresses near top (far) — wait p^1.6 at small p is smaller than p, so spacing compressed at far — correct.
  
  Hmm wait: near = bottom = p=1. Perspective: distances near bottom appear larger. sy(p) with derivative increasing in p: p^1.6 has derivative 1.6*p^0.6 increasing — yes correct.
  
  - scale(p) = sFar + (sNear - sFar) * p, e.g., 0.7 → 1.25.
  - screenX = cx + (x - W/2) * scale(p). This makes far rows converge toward center — trapezoid. 

  Shadows: small ellipse under each unit, offset slightly — sells the "seen from above at an angle" look.

- Units: not plain squares — small shapes with character. Each unit: body (rounded/circle with darker outline), a helmet dot or shield, and a sword/weapon line that swings when attacking, facing direction. Maybe two faction shapes: e.g., red = round shields + sword, blue = kite shields. Keep them tiny (radius ~4-6px at scale 1) — with 1000 units they need to read as a mass. Draw order sorted by screenY for painter's order.

  Unit rendering: 
  - shadow ellipse
  - body: small circle with faction color, darker rim
  - shield: small lighter arc on facing side? Or a simple 2-tone: body circle + helmet (small lighter circle offset toward facing direction) + weapon line perpendicular.
  - Attack animation: weapon line rotates quickly (swing) — with maybe an arc flash.
  - Health: darken/fade when low? Blood tint as damaged. On death: puff + a corpse decal stamped into the ground texture (persistent bodies accumulating = great storytelling!). Corpse decals: draw a dark splat + a fallen unit shape (rotated ellipse in muted faction color) into an offscreen "ground" canvas. This makes the field progressively littered — signature detail.

- Puffs: blood particles (small red droplets) + dust puff (soft gray circle expanding & fading). Death: bigger puff + persistent stain.

- Banner/carries: Maybe each army has a few banner carriers (flag units) — nice flavor, 2-3 per side with waving flags. Adds signature visual. Flag waves via sine. If banner bearer dies, flag falls? Keep simple: banner carriers are just tougher units with a flag drawn; if they die, the flag decal drops (stamp a fallen flag on ground). Nice touch but adds complexity — I'll include a light version: 3 standard bearers per side, flags wave, when bearer dies a dropped flag decal is stamped.

- Camera: subtle slow drift / Ken Burns? Slight shake on big clashes? Maybe a gentle slow zoom drift. Keep subtle. Actually screen shake on initial clash impact (tiny, 2-3px, decaying) — nice.

**HUD:**
- Title: battle name, e.g., "The Battle of Ashen Ford" — generated from random name lists each restart ("Battle of Redmoor Crossing", etc.). Big serif-ish display. Since no external fonts, I'll use font stacks: Georgia/'Times New Roman' serif for the title gives a chronicle feel — that's fine (not Inter/Roboto/Arial as identity). Actually a strong choice: use a classic serif with letter-spacing, small caps feel via CSS text-transform + letterspacing. Chronicle/manuscript aesthetic: parchment-ish? Hmm, dark moody field + elegant serif overlay in off-white with thin rules — like a war chronicle. 
- Counters: top corners — left: RED army count with a small banner swatch; right: BLUE. Numbers in serif, with a thin bar showing relative strength. Also maybe elapsed time and phase label ("The armies advance", "Clash!", " melee", "Victory: Crimson Host"). Phase narrative line under title — nice storytelling.
- End: "VICTORY — The Crimson Host holds the field" big centered, with winner color; celebrate: winners jump/raise weapons, some wave; losers fled. Then fade to black → new battle with new name, reset.

**Simulation details:**

World: W=1600, H=900 (world units). Armies spawn in formation: left side red facing right, right side blue facing left. Formation: ranks & files — e.g., 500 per side: 25 files wide × 20 ranks? That's a block 25 wide. Hmm, better: blocks ~ 34 columns × 15 rows = 510. Column spacing ~14 world units, row spacing ~13 → block width ~476, depth ~195. World 1600 wide: red block centered x ~ 330, blue x ~1270. Gap ~800 world units to charge — at speed ~85 u/s that's ~9s of marching. Too long for 30s budget. Reduce gap: blocks at x=430 and 1170, gap ~ 500 between front lines (front edges at ~430+238=668? wait block width 476 centered at 430 → spans 192..668). Hmm let me shrink blocks: spacing 11 → width ~370, depth: rows 15 × spacing 12 = 180.

Let me set: cols=36, rows=14 → 504 units; use 500 (some variance per battle, 480-540). colSpacing=10.5, rowSpacing=11 → block ~378 × 143. Red center x=400, blue center x=1200. Front edges: 400+189=589 and 1200-189=1011 → gap 422 world units. Speed 70 u/s → ~6s to contact. March at 55, charge at 85 when within 300 → contact at ~4-5s. Good.

Actually the requirement says "charging at each other" — so initial approach then charge. Phase labels: "advancing" then "charge!" then "clash/melee".

**Movement AI:**
Each unit: find nearest enemy via spatial grid. Grid: cell size ~48 world units (a bit more than attack range + speed*dt). Query 3×3 neighborhood; if no enemy found in 3×3, expand search rings up to some radius or just move toward enemy army centroid (global target). To keep O(n), fallback: move toward enemy army center + jitter. Also add separation from allies so they don't clump into single points: separate from nearby allies within ~ unit diameter (use same grid; push apart). 

Combat: if nearest enemy within attackRange (~10-12 world units, i.e., ~1.6 radii), stop and attack on cooldown. Deal damage, spawn hit spark/blood. Take damage from enemies attacking us.

Target selection nuance: retarget every ~0.2-0.4s (staggered) or when target dies, to keep O(n) cheap: store target reference; if target dead or too far (> some distance), re-find nearest via grid; if grid search fails, use centroid fallback. Retarget throttle: each unit has retargetTimer random 0.15-0.35s.

Movement: desired velocity toward target; steer with some noise; separation force; clamp speed; facing = velocity direction (smoothed).

Morale/rout: track army counts. If side count < enemyCount * 0.28 and count < some threshold, trigger rout for that side: those units flee toward their home edge, can still be attacked, occasionally rally? Keep simple: they flee off-field; when off-field or dead they're removed from survivor count (count as "routed" — maybe display routed separately? Simpler: routed units are no longer "survivors" for victory purposes; winners remain). Actually for counters, I'll count "alive" as units still on field fighting; routed units count down as they flee off... Let me define: survivors = units with hp>0 and !routedOffField. Rout triggers when morale broken; fleeing units sprint to their edge and despawn (counted as routed, removed). This gives a clean chase ending — winners cutting down fleeing enemies — very battle-like.

Balance randomness: to vary winners, give each army random stats multipliers (attack cooldown, hp, damage slightly) per battle, plus per-unit variance. Also formation slight differences.

**Spatial partitioning:**
Uniform grid over world: cell = 40. Rebuild each frame: array of buckets (Map or typed arrays). With 1000 units, simple: `grid = new Map` keyed by cellIndex → array push. Or flat arrays with head/next linked list for zero allocation: cells: Int32Array head[cellCount], next: Int32Array per unit. That's fast and allocation-free. cellCount = ceil(W/40)*ceil(H/40) = 40*23 ≈ 920 cells. 

Neighbor query: iterate 3×3 (or 5×5 for nearest search radius 2 cells = 80 units — attack range small so 3×3 with cell 40 covers 40+ radius... nearest enemy might be 100 away in open field. For targeting, when no enemy in 3×3, expand to ring radius 2, 3, up to 4; if still none, fallback to enemy centroid. During approach phase, no enemies within any small radius → fallback centroid handles it (cheap). During melee, enemies are everywhere → 3×3 finds them. Good.

Separation: same 3×3 neighbor scan over allies — do both in one pass? For each unit, iterate neighbor cells once, examine all units in them, classify enemy vs ally. Compute nearest enemy (within scan) and accumulate separation from allies. That's one pass per unit per frame — 1000 units × ~average few units per 3×3 cells. In dense melee, 3×3 cells at cell 40 with ~1000 units packed in maybe 15×10 cells region → density ~7 per cell → 63 examined per unit → 63k pair checks/frame — fine.

But careful: full retarget nearest across whole army not needed; centroid fallback for far approach. When armies approach, each unit just runs at enemy centroid + small per-unit offset target (their "lane" target = mirrored position). Better initial behavior: during advance phase, each unit's target = mirrored x across center line at same y (so formations collide rank-to-rank), plus slight noise. Once enemies come within grid scan range, switch to nearest-enemy mode. This preserves formation look during charge — great: "formations break apart into chaotic melee" emerges naturally after contact.

**Combat:**
When dist < range (≈ 12): attack state. cooldown ~0.5s ± variance. On attack: swing anim timer, after short windup (0.15s) apply damage if still in range — simpler: apply immediately with a swing visual. Damage 16-24 → ~5 hits avg. HP 100 ± 15. DPS per duel ≈ 40 → duel ~2.5s. Multiple attackers common → faster. 

Kill credit → spawn blood particles + ground stain + corpse decal, remove unit (mark dead, remove from grid via alive flag).

Hit feedback: small blood spray particles (3-6), tiny white spark line maybe. Screen micro-shake on heavy events? Aggregate shake from deaths per frame (cap).

**Corpses & stains (ground layer):**
Offscreen canvas at world resolution (or half res for perf: 800×450, scaled ×2 when drawn... Actually draw ground layer once as background image sized to screen projection? The projection is non-linear (trapezoid), so stamping decals in world space then projecting is complex. Alternative: make ground canvas in *screen space* and compute projection inverse for stamps. Hmm.

Simpler alternative: skip trapezoid convergence for decals by drawing the whole battlefield in screen space with a static projected background, and simulate units in *screen-ish* space? Many top-down sims just use plain screen space with a scale gradient fudge. Let me reconsider projection complexity.

Option A: Simulate in world space, render with projection; decals drawn by projecting: for a stain at world (x,y) with radius r, compute screen pos and scaled radius, draw ellipse (scale(p) horizontally and also squash vertically by foreshortening factor ~0.82 + perspective). Since stains are blobs, projecting their center and scaling radius by scale(p) is fine — no need for exact projection of extents. Corpses: draw at projected center with scale(p), rotated — fine. So ground canvas could just be the *static background* (grass texture, terrain features), while dynamic decals (stains, corpses, dropped flags) are stored as a list (cap ~600) and drawn each frame in painter order? But corpses should be *under* living units — draw corpses/stains first each frame, then units sorted. 600 stamps × simple shapes per frame is okay but adds up with 1000 units.

Better: keep an offscreen "decal canvas" in screen space? Problem: decal canvas persists across frames; projecting a stamp to screen space is a one-time operation at stamp time — the projection is static (no camera motion... unless I add camera drift). If I avoid camera motion (or keep it minimal and accept decals bake at stamp time — imperceptible), I can stamp decals directly into a screen-space offscreen canvas at their projected position. That's O(1) per stamp, zero per-frame cost. Camera: I'll skip camera pan/zoom (or tiny shake only — shake applies to whole composite via ctx.translate when blitting, decal canvas stays consistent enough; shake is transient ±3px, fine).

But wait: screen-space decal canvas means far-field stamps get small and near-field big — correct automatically via projection. And stamping order: later stamps draw over earlier — fine for accumulating mess.

Also unit shadows drawn per frame. Corpse decal: muted/darkened unit shape lying flat (ellipse + a limb line), plus blood stain (dark red splat: several overlapping circles/ellipses with low alpha, random offsets). Dust stamp too.

Decal canvas must match main canvas size (device pixels — I'll render at fixed logical resolution scaled to fit? Let's keep canvas at viewport size with DPR handling; decal canvas same size). On resize, decal canvas content would need re-render — I can re-project all stored stamps? Simpler: store stamps minimally? To keep simple: on resize, just clear decals and continue (or re-blit from a stored list of up to N stamps — I'll keep the last ~700 stamps with their data and redraw them on resize). That's easy since stamps are cheap shapes. Actually storing stamps costs little; do it: `stamps` array (max ~800, FIFO). Redraw decal canvas from stamps on resize.

Hmm, but blood stains with soft alpha stacked hundreds of times per stamp — each stamp ~5-9 circles. Redrawing 800 stamps × 7 circles = 5600 arcs once on resize — fine.

**Background:**
Static: painted once to another offscreen canvas (or drawn as first thing each frame — it's cheap if pre-rendered): dark mossy field: base color #2f3527-ish? Let me choose palette: 
- Field: desaturated olive/umber dark ground: base #33392b, with noise speckles, patchy darker/lighter blobs, a dirt road or ford? "Battle of Ashen Ford" — could include a shallow river/ford strip! A river band across the field with banks would be gorgeous and justify names. But river affects sim? Just cosmetic, maybe units slow slightly crossing? Cosmetic only — nice but adds visual complexity; I'll add a subtle ford: a pale stony band with water glints. Hmm, vertical river between the armies? Armies charge across it — a horizontal strip (east-west) doesn't fit left-right charge. A north-south river between them with a ford (gap) — units funnel through the ford → dramatic! But pathing around river needs steering... units would need to avoid water. Could fake: river vertical strip at center x, with a ford gap in middle; units steer toward ford when blocked. That's real pathing complexity. Simpler cosmetic: a diagonal dirt track / scattered rocks, craters. Or skip water; add subtle terrain: patches, a few rocks/trees at edges (drawn with slight scale by depth), distant ridge at top with faint haze (since perspective, top = horizon — a horizon line! With slight perspective from above, at top of field we can show a hazy treeline/hills beyond the field edge — sells the perspective beautifully).

Horizon composition:
- Top ~8-12% of canvas: hazy sky/distant hills + treeline (muted, low contrast, atmospheric).
- Field trapezoid below.
- Vignette + film grain overlay (subtle) for mood.
- Edge fade.

Also flags/banners on HUD.

**Phases & timeline (target):**
- t=0-0.8s: title intro fade-in ("BATTLE I — The Field of Two Crowns"?). Battle name generated.
- Phase "advance" ~2s (they start moving immediately, gap 420 at speed... let me shorten: initial gap ~360, advance speed 60, then charge 95 within 260 of enemy centroid → contact at ~3.5-4s. First clash: "CLASH!" flash + shake burst.
- Melee grind ~15-20s: units interpenetrate, chaotic. To keep it readable and end by ~26s, deaths must accumulate ~35-45/s at peak. 
- Rout at side < ~30%: "The X breaks!" then flee. Mop-up few seconds: winners chase, but stop chasing once routed units despawn. Cap rout phase ~4s: fleeing units move fast (120) toward their edge and despawn at edge or after 3s — then survivors celebrate.
- Celebration ~4-5s: winners jump (bounce offset), weapons raised, flags wave, confetti? No confetti — maybe some raise swords, hop; a "VICTORY" banner overlays. Then fade out (0.8s) → new battle: reset ground decals? New battle = fresh field (new seed, new name, maybe slight palette variation — e.g., grass hue varies per battle: olive/steppe/heath). Nice: 3-4 field palettes cycle randomly: "Ashen Moor", "Redford Meadow", etc. Names: pick from lists: places ("Blackmere", "Wolf's Ford", "Stonewatch", "Ravenfield", "Ashvale", "Cold Harbor", "Thornfield", "Grimswold", "Eagle Crossing", "Saltmarsh") + army names per color from pools (Crimson Host / Red Legion / scarlet...). 

Army name pools:
Red: "The Crimson Host", "The Red Legion", "The Scarlet Banner", "The Rose Guard", "Bloodaxe Warband"
Blue: "The Azure Order", "The Bluecoat Regiment", "The Cobalt Guard", "The Winter Host", "The Iron Blues"... something flavorful: "The Sapphire Guard", "The Nightwatch Blues"? Keep it tasteful: "The Azure Order", "The Cobalt Company", "The Sapphire Host", "The Winter Guard", "The Blue Banner".

Battle names: "The Battle of {Place}", maybe with roman numeral battle count: "Battle XII — The Field of Ashvale". Chronicle vibe: "BATTLE XII · THE FIELD OF ASHVALE". 

**HUD layout:**
- Top center: small caps overline "BATTLE XII · YEAR OF THE RAVEN"? simpler: "BATTLE XII". Under it, big serif title "The Battle of Ashvale". Under: phase line in italic small ("The armies advance…", "They charge!", "Savage melee", "The Azure Order breaks!", "Victory: The Crimson Host").
- Top-left: red army block: small shield glyph (inline SVG or canvas-drawn? HUD in DOM is easier for crisp text: use DOM overlay for HUD with counts updated via textContent each ~100ms). Red left, blue right. Each: faction name small caps, big number, thin depletion bar. 
- Bottom center maybe: elapsed timer + casualty counters? Keep minimal: counts + bars + phase. Maybe small "fallen: n" under each? Nice: survivors big, fallen small.

DOM HUD: title block centered top; counters left/right top. Victory overlay center. All pointer-events none. Styling: off-white #e8e2d5 text, letterspaced small caps, thin hairlines, subtle text-shadow for legibility over field. Faction color chips: small square/diamond swatch.

Colors: Red army: crimson #c23a2f-ish with darker #7e2019 rim. Blue army: steel blue #3f6fa8? To avoid "default blue" feel, choose a deeper slate/indigo-leaning blue: #3a5f9e / steel #46689c... The prompt literally asks red vs blue armies — fine, but I'll pick tasteful tones: red = #b93a32 (crimson), blue = #3d6a9c (steel). Ground olive-dark. Blood: #6d1216 dark. Dust: warm gray.

**Rendering pipeline per frame:**
1. ctx.drawImage(bgCanvas) — pre-rendered field incl. horizon.
2. Draw decal canvas (offscreen screen-space) via drawImage.
3. Optional: subtle ground shadow layer? Draw shadows per unit before units (two passes over sorted list, or single pass drawing shadow then unit — but painter order: shadows can be drawn immediately under each unit in same pass since shadows are under the unit itself and units sorted by y; a later unit's shadow could overlap an earlier unit — acceptable).
4. Units sorted by world y ascending (far first). Sorting 1000/frame: keep an index array sorted with insertion-friendly approach — reuse array and sort with comparator on cached sy; Array.prototype.sort on 1000 elements each frame ~ fine (60fps, ~1000·log≈10k comparisons — negligible). Alternatively bucket sort by y into row buckets — but plain sort is fine.
5. Particles (blood/dust/sparks) drawn after units (they're above ground; blood in air). Draw after units is fine.
6. Effects: clash flash, banner draw.
7. Vignette/grain overlay: pre-rendered overlay canvas drawn on top (grain static might look like dirty screen; animate grain? static subtle vignette + very low alpha grain baked once, plus maybe animated flicker? Keep static vignette; grain skip or extremely subtle static. Actually a slight animated "atmosphere" like drifting haze bands over the far field — cheap: 2-3 translucent dark horizontal bands slowly moving — adds life. Optional; maybe skip for perf. I'll add subtle smoke wisps that rise during battle — big battle smoke! Accumulating smoke as melee progresses: spawn smoke puffs at death sites that drift and fade — gives epic haze. Cap particles.

Performance: 1000 units, each drawing: shadow (1 ellipse), body (circle), helmet, weapon, maybe outline → ~5 path ops × 1000 = 5k ops — fine at 60fps on modern browsers. Use `ctx.beginPath` minimal, avoid save/restore per unit where possible (use setTransform? For rotation per unit, save/restore is heavy-ish but 1000 is okay). I can draw units without save/restore by manual math (cos/sin for facing offsets). Let's do manual math — cheaper and I control it.

Shake: applied via ctx.translate before drawing everything (and reset).

DPR: canvas sized to viewport × min(dpr,2). All world→screen computed per unit per frame — 1000 projections cheap.

**Projection math (final):**
Let canvas logical size Wc×Hc (CSS px). Define margins: field occupies full width; horizon at hy = Hc*0.16? Let me define:
- topY = Hc * 0.10 (field far edge on screen)
- botY = Hc * 0.94 (field near edge)
- depth = botY - topY
- p = y / H_world (0 far → 1 near)
- Non-linear y: sy = topY + depth * p^1.55? Derivative at p=0 is 0 — too flat, units at far edge look super compressed. Use milder: sy = topY + depth * (p*(1.25 - 0.25p))? derivative = 1.25-0.5p ∈ [0.75,1.25] — mild compression at far. Hmm, but true perspective should strongly compress far. Compromise: exponent 1.35: derivative 1.35 p^0.35: at p=0.05 → 1.35*0.42=0.57; p=1 → 1.35. Nice progressive. Let me just use pow p^1.4. But note spawn blocks occupy y ranges; with exponent, far block compresses — good look.

- Horizontal: world x ∈ [0, Ww], Ww=1600. Perspective width scaling: scale(p) = kFar + (kNear-kFar)*p^0.9? Use linear scale(p) = lerp(0.62, 1.0, p)? Then screenX = Wc/2 + (x - Ww/2)/Ww * fieldWidthAtThatDepth, where fieldWidth = Wc * scale? Hmm — I want the world's full width to fit on screen at every depth? If world width maps exactly to screen width at all depths, no trapezoid convergence — no perspective horizontally. For trapezoid: field edges beyond world rect at near... Let me think: near edge (p=1) shows full world width across, say, 96% of screen width. Far edge (p=0) shows the same world width compressed to, say, 62% of screen width → beyond the far trapezoid edges (screen corners left/right of the far edge) we draw... the bg must fill the whole screen: outside the trapezoid sides, extend ground texture darker (like out-of-bounds terrain). That's fine — bg canvas: draw field plane across full canvas with per-row horizontal scale factor, so ground texture rows compress toward the top naturally. I can render the bg by drawing many horizontal strips: for each screen row from topY to botY, invert to find p, then draw a 1px-tall strip of a horizontally-tiled ground texture scaled by 1/scale(p)? That's per-row drawImage ~ 700 rows — one-time cost, fine, and gives genuine texture perspective (texture compresses with depth)! 

Let me define inverse: given sy, p = ((sy-topY)/depth)^(1/1.4). scale(p) = sFar+(sNear-sFar)*smooth? Use scale(p) = lerp(0.6, 1.06, p^0.85)? Hmm keep it simple: scale(p)=lerp(0.58, 1.05, p). screenX(x,p) = Wc/2 + (x - Ww/2) * (Wc*0.97/Ww) * scale(p). At p=1, world width spans 0.97*Wc*1.05 ≈ 1.02Wc — slightly wider than screen (near edge crops a bit — fine, feels close). At p=0 spans 0.58*0.97 ≈ 0.56 Wc — trapezoid. 

Bg rendering plan:
- Fill sky gradient (hazy, warm-dusk muted) above horizon... "slight perspective from above" — a horizon with distant hills. Sky area small: top 0-? topY=0.10*Hc. Distant treeline at topY.
- For rows topY..botY: p from pow inverse; draw strip from a pre-made ground texture canvas (gtex, e.g., 512×512 noise) using: drawImage(tex, 0, srcY, texW, srcH, dx, sy, dw, 1) where the source row corresponds to texture v = p*texH and dw = texW * (Wc/Ww) * scale(p) * (Ww/texW)... Let me simplify: for each strip, dw = Wc * (0.97) * scale(p) * something and center it. Texture sampling vertical coordinate: map world y (0..Ww?) Actually texture should tile with world coordinates: srcY within texture chosen so that world y maps continuously — but since we draw 1px strips, we can just sample a horizontal line of the texture at v = frac based on world y: srcY = (y/Ww)*texH? If texture is 512 tall and world 900 tall, srcH = texH * (1/Ww) * (dy/dp per strip)... this is getting complicated. 

Simpler robust approach: pre-render ground texture in *world space* into an offscreen canvas of, say, 800×450 (world 1600×900 half-res), then draw it to screen via per-strip column/row scaling? Non-linear both axes makes single drawImage impossible. Per-row strips: for row i at sy with height dSy, the world y-range covered is [y0,y1]; draw the corresponding horizontal slice of the world-space texture: drawImage(worldTex, 0, y0*s, texW, (y1-y0)*s, dx, sy, dw, dSy) where s = texW/Ww... horizontal scale differs per row: dw = texW_draw where the texture row already spans full world width 0..Ww, so dw = (0.97*Wc) * scale(p), centered. The vertical squish (y0..y1 → 1px) also compresses texture vertically — combined effect approximates perspective decently, and since I generate the world texture with isotropic noise, the vertical compression at far adds foreshortening. Good enough and one-time.

Actually even simpler: iterate p in fixed world steps (e.g., 180 strips, each covering worldY step = Ww/180), compute sy0 = proj(y0), sy1 = proj(y1), draw worldTex slice (0, y0*st, texW, step*st, cx - halfSpan, sy0, span, sy1-sy0+1) where halfSpan = 0.485*Wc*scale(pmid), span=2*halfSpan. 180 drawImages one-time — trivial. Above topY (p<0 region → sky) and beyond horizon: draw sky/hills. Also below botY (p>1)? botY at 0.94Hc; below that, extend near rows: draw the p=1 slice stretched a bit or just let vignette cover; I'll set botY=Hc (field fills to bottom) — near edge at screen bottom. topY = 0.09Hc maybe. Let me set topY=0.085*Hc, and sky occupies 0..topY: haze gradient + hill silhouettes + treeline. 

Wait — if botY = Hc and p^1.4 mapping, near rows (bottom) get large spacing — fine.

Also out-of-trapezoid left/right at far rows: strips span full canvas width? The texture slice spans world width; scaled span at p small is 0.56Wc — sides empty. Fill sides with same row's texture repeated (drawImage again offset) or darker edge fill. Easiest: for each strip, draw the slice twice (tiled horizontally) to cover full width: positions cx-span/2 and cx+span/2 (and maybe ±3/2 span for very far). With darker overlay for outside area? The out-of-field sides would look like the field continues — acceptable ("the field is bigger than the battle"). Add vignette darkening edges → looks natural. Also add subtle fog: overlay vertical gradient increasing toward horizon — atmospheric perspective. 

Sides tiling: draw slice at x offsets: cx±span/2, cx±3span/2 → covers. Cheap.

Bg features drawn after strips, in screen space but positioned via projection: 
- scattered darker patches (already in texture), 
- rocks/pebbles: ~40 small gray ellipses at random world pos, projected with scale — do this by drawing onto the bg canvas once using proj(). Same for grass tufts (tiny strokes), a few dead trees near edges? Trees at edges: 3-4 gnarly simple silhouettes with long shadows — adds composition anchor. Keep subtle, dark, so units remain focal.
- Craters/barrow mounds? A couple of shallow crater ellipses with rim — nice.
- Horizon: hills (2 layered wavy silhouettes, bluish-gray haze), treeline (bumpy dark strip), sky (muted dusk: pale amber-gray to smoky). Slight sun haze glow low contrast — avoid decorative gradient heaviness; a hazy horizon glow is scene-appropriate atmosphere, subtle.

Also a "sun" direction for shadows: shadows offset consistently (e.g., +2,+1.5 scaled) — consistent light.

**Corpses/stamps (screen-space decal canvas):**
stamp functions:
- bloodStain(sx,sy,s,seed): 5-8 dark red circles alpha 0.5-0.75 random offsets within s*1.5, sizes s*0.3-0.8; plus tiny speckles.
- corpse(sx,sy,s,ang,color): dark muted ellipse (body) with a lighter helmet dot and weapon line lying nearby, alpha ~0.85, very desaturated/darkened color.
- dustScorch(sx,sy,s): brownish smudge.
- fallenFlag(sx,sy,s,color): small flag lying.
Order: blood under corpse. Stamp with alpha and muted colors so field darkens with battle — narrative!

Cap: stamps array length cap 900; when exceeding, shift oldest (they fade from history — fine; or stop adding blood but keep corpses — simplest FIFO).

**Particles:**
Pool array; types: blood (red droplets with gravity? top-down — just outward scatter + fade, small 1-2px), dust (soft expanding circles, alpha low), sparks (tiny white-yellow, quick). Cap ~600, reuse via swap-pop. Smoke: bigger soft gray circles rising slightly (screen-space up? For top-down, smoke drifting with slight bias +x wind, expanding, alpha 0.08-0.18) — spawn on deaths during melee, cap. Smoke drawn under units? Over — atmospheric. Over units with low alpha is fine (haze). Maybe draw smoke after units but before vignette — yes.

Particle update in screen space or world? Project spawns to screen once and simulate in screen space with scale-based sizes — simpler and looks fine (particles are short-lived, no need to re-project). But far-field particles would move same speed as near — negligible.

**Units data:**
Typed-array-ish but JS objects are fine for 1000. Fields: x,y,vx,vy? Keep pos + heading + speed; hp, maxHp, cd (attack cooldown), target (ref), retargetT, side (0/1), elite?, banner (bool), alive, phaseOffset (anim), swingT, flee flag, wob (noise phase), size variance.

Update loop (dt clamped ≤ 0.033*? clamp dt to 1/30 to avoid spiral):
- rebuild grid (heads/next Int32Array)
- for each alive unit:
  - retargetT -= dt; if ≤0 or target invalid → find target:
    - scan grid rings r=1..R for nearest enemy (R up to 3 cells ~ cell 46 → 140 range). If found: target.
    - else: target = null → mode "advance": steer toward enemy centroid (precomputed each frame: avg of alive enemy positions — compute both centroids per frame cheaply in grid pass? compute after rebuild via a single pass over units).
  - if target: d = dist; if d < range: attack mode: stop movement (slight jitter), cd-=dt, if cd≤0 → strike: cd=cooldown*rand(0.8,1.3); swing anim; damage target (target.hp -= dmg; spawn blood at target; if dead → kill handling). Facing toward target.
    - else: move toward target (also if d > range*2.5 and retarget valid... keep target until dead or d > 260 → invalidate).
  - else advance: steer toward lane point (enemy centroid mirrored? During advance: destination = (mirrorX of own x across battlefield center? that aims at enemy front) plus noise; better: destination = enemyCentroid + perUnitOffset (small). Use pre-battle lane: dest.x = enemySide center x, dest.y = own y + small drift. Once enemies within 220 of centroid → state 'charge' → speed up 1.5x and slight horn? (no audio... audio via WebAudio possible! Auto-play muted policies: WebAudio needs gesture in some browsers; "no interaction" — I could attempt to start audio and silently fail. Skip audio to be safe? A battle without sound is fine for a recording. Skip.)
  - separation: accumulate push from allies within sepDist (≈ 7 world units): push ∝ overlap. Also mild separation from enemies (avoid full overlap): if enemy closer than 8, push apart too (so they don't stack into one point). Apply separation always.
  - flee mode (rout): dest = home edge x (red → x=-60, blue → Ww+60), speed 1.6x, ignore targets, can be attacked; despawn when x beyond edge (mark routed, remove).
  - integrate: vx toward desired with accel limit; heading = atan2 smoothed (lerp angle); speed cap.
  - slight per-unit speed variance and sine wobble for organic motion.

Formations breaking: separation + target nearest naturally creates melee. Also when lines clash, add "pressure": front ranks push — separation handles.

**Nearest-enemy via grid rings:** implement: 
```
function findNearest(u): 
  best=-1,bd=Infinity
  cx=floor(u.x/CS), cy=floor(u.y/CS)
  for r in 0..3:
    if r==0: check own cell only... standard expanding square ring scan:
    for cells in ring r: iterate units, enemy & dist2 < bd → best
    if best found and r>=1 → could early-exit (nearest in ring r means nothing closer in inner rings; but units in same ring farther cells could be closer — for our purpose approximate: accept best found in ring r if r>=1? Actually ring r contains all cells at Chebyshev distance r; a unit in ring r could be closer than one found earlier? No — we scan rings in order 0,1,2..., and all cells in ring r before concluding. A unit at Chebyshev r could be Euclidean closer than... no: any unit with Chebyshev distance ≤ r-1 was already checked. Units in ring r: their Euclidean distance ≥ ... hmm not bounded below by ring r-1. But since we check the entire ring r and take min over it, and inner rings had none, min over ring r is the global nearest? Not exactly: a unit in ring r+1 could be Euclidean-closer than a diagonal unit in ring r? Chebyshev distance r means max(|dx|,|dy|)=r; Euclid ≥ r*CS... unit in ring r+1 has Euclid ≥ (r+1)*CS? No: Chebyshev r+1 → Euclid ≥ (r+1)*CS? Euclid ≥ Chebyshev*CS when cells sized CS? Euclidean distance between units ≥ CS * (Chebyshev cell distance - 1)? Roughly. Taking min over full ring r then stopping is a good approximation; tiny inaccuracy harmless. I'll scan rings 0..2 (up to ~ (2+0.5)*CS range with CS=46 → ~115 units) and fallback to centroid beyond. Good enough.
```

Also enemy-vs-enemy separation: to prevent stacking, in the neighbor pass compute push from ALL nearby units (both sides) within radius; and attack range check uses nearest enemy found.

One pass per unit: iterate 3×3 cells once; collect: nearestEnemy (dist2), allies push, enemies push. This is the "sense" step. Retarget throttle: do full sense each frame anyway for separation — nearest enemy from sense is free! So retarget logic: target = nearestEnemy from sense if within engagement (say < 60) else keep target/centroid. Let me restructure:

Every frame per unit:
- sense pass over 3×3 neighborhood: nearest enemy + separation accumulation (from all units within sepR, only count same-cell-ish).
- if nearest enemy d < engageR (say 26): if current target is that enemy or valid and closer — just set target = nearestEnemy when within 30; else keep existing target if alive & d<... 

Simplify targeting: units always target the nearest enemy found by sensing when within range SENSE_R=CS*1.5; otherwise target = advance point (centroid-ish). Target invalidation handled naturally. Attack only when within range of target. This gives smooth transition: far → march to enemy centroid; near → lock nearest.

Edge case: two opposing front lines approaching: sensing range 70 — when gap < ~70 front ranks lock and fight; ranks behind keep advancing (their nearest enemy > engageR? They'll target nearest enemy (front enemy) and walk into range, then stop & fight → pile-up at front. To make melee spread along the line and wrap around flanks, targets naturally spread. Also add per-unit "aggression offset": target position = enemy pos + small persistent jitter so they don't all pick exact same point. Also once melee, units deepen: since behind units target front enemies and attack from behind — realistic pile. Fine.

Flanking: units at block edges will curve toward enemy centroid — outer units wrap → encirclement behavior emerges. 

**Battle pacing tuning:** front contact at t≈4s. Then grind. Kill rate depends on engagement density. Let me simulate mentally: front ranks ~36 units each side engaged; each duel kill ~2.5s → front rank swaps every ~2.5s but ranks behind step up... Death rate ≈ engaged units per side / kill time ≈ maybe 60-120 engaged per side eventually → deaths ~ 2 * engaged/2.5 ≈ 50-90/s?? That would end 1000 units in ~15s. Hmm — engagement self-limits: as units die, front shrinks. Also units stop to fight only within range; crowd pressure pushes more in. Average over battle maybe 30-45 deaths/s → ~25-30s to whittle to rout threshold (~30% → ~150 alive each? rout when one side < 32% of other...). With randomness, one side gains advantage; typical snowball: by t=20s maybe 400 vs 300; when loser hits threshold ~ 0.3 ratio... Let me set rout trigger: side.count < enemy.count * 0.30 && side.count < 160? And also hard timeout: if t > 40s force rout of smaller side (guarantee ending). And total battle target: expect end ~24-30s. Also I want first-30s to include victory — celebration starts maybe at 26-30s... risky. Let me push faster: contact ~3.2s; increase dmg slightly; rout threshold 0.35. Also "sudden death" ramp: after t=20s, damage +50% ramping — narratively "the melee turns savage" — ensures end by ~26-30s. Celebration visible by ~30s. I'll also make the whole thing slightly fast-paced: dt timescale 1.0 but speeds high.

Alternatively scale down armies? Requirement: at least 500 each. Keep 520 vs 520 (±random). Hmm "at least 500 each (1000 total)" — I'll do 520/520 typically.

Let me add a global battleSpeed = 1.12 multiplier maybe. And design so that: contact 3s, heavy grind, by t=22s one side clearly ahead (random initial per-unit stat variance + slight army-wide multiplier 0.95-1.05 decides winner), rout ~ at 24-27s, mop-up 3s, victory banner, celebrate 5s, fade 1s, restart. Loop period ~35-38s. First 30s captures: advance, charge, clash, melee carnage, rout begins, victory likely. Good enough — and "may loop or continue".

To bias winner timing tighter, I'll also implement "momentum": each kill slightly buffs nearby killer allies? Overkill. The timeout ramp suffices.

**Celebration:** winners: state 'victory' — they stop, face camera-ish (random), hop: bounce = |sin(t*6 + phase)| * 3 world units, weapon raised (draw sword pointing up with slight sway), some cheer pulses. Banner bearers wave flags vigorously. Maybe a few "huzzah" text? No — keep visuals. Victory overlay: big serif "VICTORY" + winner army name + survivors count; slow fade-in. Then after 4.5s, fade whole scene to dark 0.9s, regenerate.

**Restart:** rebuild armies with new seed: name, palette (ground hue variants: mossy green / dry steppe tan-green / dark heather), stats, formations maybe different shapes (block, wedge?, two lines?) — variation: formation types: "block" (default), "wedge" (triangle pointing at enemy), "broad line" (fewer ranks, wider), "column"? These change the look per battle. Nice touch: 2-3 formation variants random per battle per side. Wedge: rows with decreasing width. Implement simple: for row i, cols_i = base - i*step (wedge), or constant (block), or wide (cols= 46, rows=11). Keep within canvas world bounds.

**HUD counters:** update each frame is fine (textContent cheap) — but do it every frame only when changed. Bars: width % = count/initialCount.

Phase messages:
- "The armies advance" → when centroid gap < 300: "They charge!" (also flash) → contact: "The lines collide" → after 6s of melee: "Savage melee — the field runs red" variants → rout: "The {name} breaks!" → victory: "Victory — {name} holds the field".

Also elapsed clock small at bottom? Maybe bottom-center: "⏱"? no emoji. Small caps "ELAPSED 0:17" bottom center — subtle. Or skip. I'll add a tiny bottom line with casualties total? Keep HUD focused: two counters + title + phase. Maybe bottom-center shows battle number and "routed/fallen" tally: "FALLEN 312 · ROUTED 88" — nice stat. Light.

**Title intro:** Each battle starts: black overlay fades from 1 → 0 over 1.2s; title letters fade/slide slightly. Overline: "BATTLE XII — WESTERN REACHES"? Compose: overline "BATTLE " + roman(n) + " · " + season/year flavor? Keep: overline = "BATTLE " + roman; main = "The Battle of " + place (Title Case); subtitle = redName + "  ✕  " + blueName? Use "×" char? A small "versus" line: "The Crimson Host — against — The Cobalt Company". Nice chronicle flavor. Use middle dots and long dash.

Fonts: serif stack: Georgia, 'Iowan Old Style', 'Palatino Linotype', 'Times New Roman', serif. Big title with slight letterspacing, text-shadow subtle dark for legibility. Small caps via font-variant: small-caps or uppercase + letterspacing.

**Vignette/overlay:** pre-rendered radial vignette + top haze. Grain: skip or tiny static noise at 0.03 alpha baked into vignette canvas — static grain can look fine (like film). I'll bake subtle noise into vignette overlay.

**Shake:** shakeMag decays; on clash init set 6; on many deaths per frame add small. Apply translate(rand*mag).

**Flash:** on first clash: brief white flash alpha 0.25 fading 0.3s? Maybe skip flash; shake + phase text suffice. Small flash ok.

**Grid implementation:**
```
CS=48; GW=ceil(1600/CS)=34; GH=ceil(900/CS)=19; cells=646
head=Int32Array(cells).fill(-1); next=Int32Array(maxUnits)
rebuild: for each alive unit idx: c=..., next[i]=head[c]; head[c]=i
```
Sense: neighbor cells 3×3 (cell coords clamped).

With CS=48 and 3×3 → sensing radius ~ up to ~96 (accounting positions within cells). Units speed ~85*dt=1.4/frame — fine.

Separation radius ~9; separation pass same 3×3 cells. 

Attack range: 11 world units (units radius ~4.2). Melee spacing: separation target distance ~8.5 → dense ranks look.

**Unit drawing detail (size s = base 4.6 * scale(p) * unitSize):**
Facing angle a. cos/sin.
- shadow: ellipse at (sx+shOff.x*s?, sy+shOff) rx=s*1.15, ry=s*0.55, black alpha 0.28.
- weapon: sword: line from unit center offset perpendicular... draw weapon behind body when not swinging? Simplify: draw sword as short line rotated by swing phase: baseAngle = a + π/2 * side? Each unit has weaponSide ±1. Sword angle = a + (side * 0.9) + swing*? During swing (0.12s), sword sweeps from a-1.6*side to a+0.6*side — compute ang = lerp. Length s*1.9, color light steel #cfd4d8 with dark edge? Draw as line with round caps, width s*0.28, plus tiny hilt dot. When victory: sword raised = pointing up (screen -y) with sway.
- body: circle radius s, fill faction color (vary lightness per unit ±8%), stroke darker rim width s*0.35? Use two circles: fill body, then smaller highlight? Keep: fill body color; dark rim via stroke.
- shield: arc/ellipse offset toward facing side: small circle radius s*0.62 at offset (cos(a+side*1.1)*s*0.55, ...) with lighter faction tint + rim → suggests shield side. Hmm might read as two blobs; instead: helmet: smaller circle radius s*0.5 offset toward facing (cos a * s*0.35) in lighter gray/metal tone → reads as head/helmet. And shield: crescent on the weapon-opposite side: arc stroke? Let me not overdo; 1000 units tiny: body + helmet + sword + shadow is enough; plus damaged tint: when hp<50%, blend toward dark/bloodied (mix color toward #4a1512 by (1-hp%)) — nice.
- banner bearers: taller pole line upward (screen up) length s*3.2 with waving flag: flag = small triangle/quad with sine wave, faction color brighter + emblem dot. Draw pole before body (behind), flag above.
- Elite/knights: 6% of units slightly bigger, darker, +stat. Subtle.

Dead handling: hp≤0 → alive=false; stamp blood + corpse; particles; counts.

Counting: side.count computed on deaths (decrement). Routed units decrement when despawn (or count separately). Victory condition: count reaches 0 OR all remaining routed/fled, or enemy routed fully: victory when opposing alive==0. Since fleeing units despawn at edge, eventually alive==0 for loser. Also if winner... celebration starts when loser alive==0 (all dead or fled). Edge: both die simultaneously — pick higher count as winner; tie → "Mutual annihilation"? Fun rare case: handle draw: message "The field falls silent" — nice touch, celebrate none. Simple guard.

**Main loop structure:**
```
let state: 'intro'|'battle'|'victory'|'fade'
battle objects: units[], particles[], stamps[], armies[2] {count, initial, name, color...}
time, phase label management
```
requestAnimationFrame loop, dt = clamp(now-last, 0, 0.05)*speed? Keep dt real seconds capped 1/20.

**Perf considerations:** 
- Sorting: units.slice? Keep `drawList` array reused: push alive units, sort by y. 1000 elements sort — ok.
- Avoid per-frame allocations in hot loops: reuse arrays, minimal object creation (particles pooled-ish via swap-pop).
- Text updates: only when changed.
- All canvas ops straightforward.

Let me also consider: bodies per frame per unit: shadow ellipse (ctx.ellipse), body arc, helmet arc, sword line (moveTo/lineTo), maybe stroke rim → ~6 draw calls ×1000 = 6000/frame + particles. Should hold 60fps on desktop; acceptable.

Alpha and fillStyle changes per unit — fine.

**Charge phase details:**
- phase 'advance': speed 46; each unit dest = (enemyCx, y + drift) — they march horizontally toward center; formations hold due to separation & lane alignment.
- When dist(unit, nearestEnemy) < 240 OR centroid gap < 300 → army state 'charge': speed 92, slight accelerate; message "The lines charge!" maybe war horn? no audio.
- Contact: message "The lines collide!" + shake.
- Melee phase after 5s of contact: message rotating flavor lines.

Per-army charge trigger individually (nearest enemy distance per army centroid). Compute per frame: armyCentroids + nearest enemy distance approximations — compute during sense? Simple: compute both centroids; gap = distance between centroids; trigger charge when gap < 340. And message changes when any combat occurs (first attack event).

**Rout:** trigger: army.count < enemy.count*0.34 && army.count>0 && battle time > 12s; or battle time > 38s → smaller army routs. On rout: message "The {name} breaks and flees!"; units get flee=true with staggered delay (0-1.2s random) so it trickles — nicer. Fleeing units: speed 130, direction toward own home edge, wobble; they can be attacked (enemies target them — nearest enemy logic still finds them; they don't fight back: their attacks disabled). Despawn when off world (x<-40 or >Ww+40) or y out. count decrements on despawn — wait, then "alive count" drops as they flee — survivors counter decreasing while fleeing might read odd; but it's "on field" count. I'll display counts as "on the field". When flee begins, message covers narrative. Fine. Alternatively count them as removed at rout moment. I'll decrement when they despawn (they visibly vanish at edge).

Victory when enemy alive==0 && no fleeing remaining... Simply: when army.alive==0 → other side wins. Note during rout, winner units chase: they target fleeing enemies (nearest enemy still works) and pursue until enemies despawn — pursuit looks great. Winners stop chasing beyond? When no enemies in sense range, they advance toward centroid = last known... When all losers gone, state victory: units stop & celebrate.

Also during celebration, maybe winners gradually gather? Skip; hop in place.

**Numbers check (world):** Ww=1600, Hw=900. Red block: cols=34, rows=15 → 510. spacing x=10.5 → width 357, centered at x=380 → spans 201..559. Blue center 1220. Gap between blocks: 1220-559-357? Blue spans 1041..1399. Front gap = 1041-559 = 482. Advance 46 u/s both → closing 92 u/s → contact in ~5.2s. Too slow. Increase advance speed to 58 → closing 116 → 4.1s; then charge at gap<340 speeds to 95 each → closing 190 → remaining 340/190=1.8s → contact ~3.5s? Wait gap becomes <340 after (482-340)/116=1.22s, then 1.8s → contact at ~3.0s. 

Hmm rows 15 × y-spacing 12 → depth 168, centered vertically 450 → spans 366..534. Block depth fine.

520 units: cols 26 rows 20? Let me parametrize per formation:
- block: cols=26, rows=20 → 520. width 26*10.5=273, depth 20*11=220.
- line: cols=40, rows=13 → 520. width 420, depth 143.
- wedge: rows=16, row i width = 8+i*1.6? sums... simpler: generate positions: for i in 0..N: row = floor..., distribute. I'll write generator: given rows and per-row count function.

Front width matters for clash drama: line vs line = grand clash; block vs wedge asymmetric. Random per side.

Total ~1040 units. Fine.

**Also** "charging at each other across a field seen from above in a slight perspective" — done.

**Code size:** This will be a long file (~700-900 lines). That's fine.

Let me now write the code carefully.

---

### Detailed code plan

```html
<!DOCTYPE html>
<html><head><meta charset><meta viewport><title>...</title>
<style> ... HUD styles ... </style>
</head><body>
<canvas id="scene"></canvas>
<div id="hud">
  <div id="armyL" class="army left"> <div class="swatch"></div><div class="aname"></div><div class="count">0</div><div class="bar"><i></i></div><div class="sub">on the field</div></div>
  <div id="armyR" ...>
  <div id="titleWrap"><div id="overline"></div><h1 id="title"></h1><div id="phase"></div></div>
  <div id="bottom"> fallen/routed line </div>
  <div id="verdict"><div class="v-over">VICTORY</div><div class="v-name"></div><div class="v-sub"></div></div>
  <div id="fader"></div>
</div>
<script> ... </script>
```

CSS: body margin 0, overflow hidden, background #0c0d0a; canvas fullscreen. HUD absolutely positioned, pointer-events none, serif stack, color #ece5d3.

Title: top center: overline: 11px letterspacing 0.35em uppercase opacity .75; h1: 30-42px clamp(24px,4vw,44px), font-weight 600? Georgia bold; small caps? Use normal case "The Battle of Ashvale" with slight text-shadow 0 1px 8px rgba(0,0,0,.6), 0 0 1px. Phase: italic 14px, opacity .85, transitions when changed (fade swap: apply small CSS animation on change — I'll just re-trigger a class).

Counters: left/right top: name 11px uppercase letterspaced with color chip (a small diamond via inline-block rotated square? Or just colored text). count: 34px serif. bar: width 140px height 3px background rgba(255,255,255,.14), inner fill faction color, width %.

Verdict: center, hidden initially (opacity 0, translateY), shown with class. "VICTORY" letterspaced 0.5em large; name below; sub line "holds the field after N seconds · X fell". Fade via transition.

Fader: fullscreen black div, opacity transition 0.9s, used at battle transitions and initial.

Phase text change animation: on setPhase, replace textContent then restart CSS animation (remove/add class via reflow trick or Web Animations). Simple: phase.animate([{opacity:0, transform:'translateY(4px)'},{opacity:1, transform:'none'}], {duration:400}).

Now the JS.

```js
'use strict';
// ---------- setup ----------
const cv = document.getElementById('scene');
const ctx = cv.getContext('2d');
let DPR=1, VW=0, VH=0; // css px
const decal = document.createElement('canvas'); const dctx = decal.getContext('2d');
const bg = document.createElement('canvas'); const bgc = bg.getContext('2d');
const vign = ...; 
```

Projection:
```js
const Ww=1600, Hw=900;
let topY, depth, sFar=0.60, sNear=1.06, pw; // pw = pixels per world unit at scale 1 horizontally: (VW*0.98)/Ww
const PEXP=1.42;
function proj(x,y,out){ const p=y/Hw; const sc=(sFar+(sNear-sFar)*p)*pw; out.x=VW/2+(x-Ww/2)*sc; out.y=topY+Math.pow(p,PEXP)*depth; out.s=sc; }
```
Wait scale used for sizes should be a pure factor: sc = lerp(sFar,sNear,p) * pw where pw = VW*0.98/Ww. At p=1, horizontal span of world = Ww*pw*sNear = 0.98*VW*1.06 ≈ 1.04VW — near rows slightly overflow → near units bigger, cropped a touch at sides. Fine.

For strips I need inverse p from sy: p = ((sy-topY)/depth)^(1/PEXP).

resize():
```
VW=innerWidth; VH=innerHeight; DPR=min(devicePixelRatio||1,2);
cv.width=VW*DPR; cv.height=VH*DPR; cv.style.width=VW+'px'...
ctx.setTransform(DPR,0,0,DPR,0,0);
decal.width=VW*DPR... dctx.setTransform(DPR,0,0,DPR,0,0); // draw stamps in css px
redrawStamps(); // re-render decal from stored list
buildBackground();
```
topY = VH*0.085; depth = VH*0.935 (bottom at 1.02? Let me set bottom at VH*1.02 so field covers bottom: depth = VH*1.02 - topY... hmm at p=1 sy=bottom: VH*1.02 slightly below screen — near edge just off-screen: fine, gives full-bleed foreground.

Actually careful: units at p=1 (y=900) would be at sy=1.02VH — off bottom. Spawn blocks are y 366..534 (p .40-.59) — on screen comfortably. Routed fleeing off left/right stay in band. Fine.

Also handle topY region: sky above.

**Background build (bg canvas, css-size, drawn once):**
1. sky: fill rect 0..topY+~10: vertical gradient from #171a1c? Let me pick dusk-muted: top #23262b → horizon #8a7f6a (pale haze). Hmm want moody overcast: sky from #2a2d33 (slate) down to #9a8f78 (hazy light) near horizon — like late afternoon haze. Then distant hills: two silhouette layers with wavy tops: back hill color mix of haze (#7d7666 w/ alpha), front treeline darker #3c4034. Add subtle sun glow: radial at horizon center? Low alpha pale disc — atmospheric, acceptable (it's scene lighting, not UI gradient). Keep restrained.
2. field strips: for i in 0..NSTRIPS: y0=i*step, y1=y0+step (world), p=(y0+y1)/2/Hw... compute sy0=projY(y0), sy1=projY(y1); scale at mid; halfSpan = 0.49*VW*sc... wait horizontal span: full world width 1600 at scale sc maps to 1600*pw*sc px; draw slice from worldTex: worldTex is Ww×Hw*?; I'll create groundTex offscreen sized Wt=640, Ht=360 representing world (scale 0.4). Slice source rect: sx=0, sy=y0*(Ht/Hw), sw=Wt, sh=(y1-y0)*(Ht/Hw)+1. Dest: dx = VW/2 - (Ww*pw*sc)/2, dy=sy0-0.5, dw=Ww*pw*sc, dh=sy1-sy0+1. Also tile sides: draw again at dx±dw (only needed if dw<VW; cheap to always draw 3 tiles). 3×~160 draws = 480 one-time — fine.

Hmm wait: strips drawn far→near; each subsequent strip covers below; +1px overlap prevents seams. Also I should slightly blend strip edges — the +1 overlap ok.

3. Ground texture generation (groundTex): base fill olive-dark: hsl varying by palette. Add ~4000 speckles (1px rects, random light/dark), ~60 large soft patches (radial gradients dark/light alpha 0.05-0.1) for patchiness, some directional mowing lines? skip. Also faint track: a diagonal dirt path? Add subtle horizontal war-worn track near middle? Skip — battle scars will accumulate.

Palette variants (per battle): 
- P1 "moor": base h=88 s=18% l=21% (olive)
- P2 "steppe": h=75 s=16% l=26% (dry khaki)
- P3 "heath": h=140 s=10% l=17% (dark green-gray)
- P4 "ashen": h=45 s=8% l=24% (pale dry)
Blood on all: dark #5f1210 works.

4. Details drawn on bg after strips (using proj to place): rocks (n=26): gray ellipse with highlight & shadow; grass tufts (n=140): 2-3 short strokes darker green; craters: 2-3 big shallow ellipse darker with rim highlight; scattered bones? too much. Also edge trees: 3-5 at far y (y<150) and sides: draw simple trunk + blob canopy dark, with long shadow — at far depth they're small. Also draw a few standing stones? Rocks fine.

Also vignette canvas: radial dark edges alpha up to 0.5 at corners, plus stronger at top (horizon haze). Plus film grain: 1 pass: create noise on small canvas (128×128) alpha, pattern-fill at low alpha 0.05 — static grain. OK.

Wait: vignette must be drawn above units — pre-render overlay canvas (vign + grain) and drawImage last each frame (cheap). Also haze bands: dynamic smoke handled by particles.

**Army/unit generation:**

```js
const NAMES_R=['The Crimson Host','The Red Legion','The Scarlet Banner','The Rose Company','The Bloodaxe Warband','The Redward Kingsmen'];
const NAMES_B=['The Azure Order','The Cobalt Company','The Sapphire Guard','The Winter Host','The Riverlands Blues','The Bluebanner Revengers'?] hmm keep serious: 'The Bluebanner Wardens','The Ironblue Regulars'.
const PLACES=['Ashvale','Blackmere','Wolford','Ravenhill','Stonewatch','Coldbrook','Thornfield','Grimsmoor','Eagleford','Saltmere','Harrowgate','Duskwold','Redfern','Caelmarsh'];
```
Roman numeral helper for battle count.

Unit creation:
```js
function makeArmy(side){ // side 0 red left, 1 blue right
  const N=520+((Math.random()*5)|0)*4? // just N=520
  formation pick: type = randChoice(['block','line','wedge']);
  center cx = side? 1230:370; cy=Hw/2 + rand(-60,60);
  cols/rows: block: c=26,r=20; line: c=40,r=13; wedge: rows=18, row i (0 front..) width grows... wedge points toward enemy: front row narrow at front. For side0 (facing right): front = rightmost. Positions: for each row i (0=front), count = 3 + i*1.8 → total ≈ sum ≈ 3*18+1.8*153=54+275≈330 hmm need 520: count=4+i*2.6 → 4*18+2.6*153=72+398=470. Fine tune: rows=20, count_i=4+i*2.3 → 80+2.3*190=517 ✓.
  x spacing 10.5, y spacing 11.5.
  For side0: x = cx + (col - (cnt-1)/2)*sx + row offset backward: front row at largest x: x = cx + halfw - i*rowDepth? Let me define rows go backward from front: x = frontX - i*rowGap for side0 (rowDepth=11.5), for side1 front at leftmost: x = frontX + i*rowDepth.
  Within row: x same? A row is a column-line along y! Careful: ranks along y (depth of screen), files across x? Formation facing +x: the front line is a vertical line (constant x, varying y). So "row i" = i-th rank: x fixed; units spread along y. count_i = width of that rank in y. So: y = cy + (j - (cnt-1)/2)*sy. For wedge: width grows toward back → triangle pointing at enemy. ✓
}
```
Cap y within [60, Hw-60]; clamp width: if cnt*ys > 700 clamp ys.

Unit stats:
```
u = {x,y, a: facing (0 right for red, π for blue), hp: 88+rand*40, mhp, dmg: 15+rand*9, cd:0, cds: 0.42+rand*0.2, spd: 52+rand*14, side, tgt:null, rt: rand*0.3, swing:0, wsw: rand*6.28 (wobble), fl:0 (flee delay), flee:false, big: rand<0.07, banner: assigned later, tint: rand}
```
Army-wide modifier: str = 0.94+rand*0.12 → multiplies dmg and hp (decides winner bias + randomness).

Banner bearers: pick 3 random units per army → u.banner=true, u.hp*=1.6, dmg*=1.1.

**Spatial grid:**
```js
const CS=48, GW=Math.ceil(Ww/CS) (=34), GH=Math.ceil(Hw/CS)(=19), NC=GW*GH;
const head=new Int32Array(NC), unext=new Int32Array(MAXU);
```
Rebuild each frame before updates.

**Sense & update:**

```js
function update(dt){
  t += dt;
  // rebuild grid
  head.fill(-1);
  for i alive: c=cellIndex(x,y); unext[i]=head[c]; head[c]=i;
  // centroids
  for each side: sum alive non-fleeing? include fleeing? centroid for targeting: use alive units (all) of enemy side... For advance destination, use enemy centroid; when enemies flee, winners chase — chasing uses nearest-enemy sensing; centroid fallback fine.
  
  for each unit u (alive):
    // sense
    let ne=-1, nd2=1e9; let sepx=0, sepy=0;
    cx=..., cy=...;
    for gy in cy-1..cy+1, gx in cx-1..cx+1:
      for j=head[cell]; j!=-1; j=unext[j]:
        if j==i continue; v=units[j];
        dx=v.x-u.x, dy=v.y-u.y; d2=dx*dx+dy*dy;
        if d2 < seped2 (say 8.5^2=72): if d2>0.01: f=(1 - d2/72); inv=1/sqrt(d2); sepx -= dx*inv*f; sepy -= dy*inv*f; // push away
        wait: push away from v: direction away = -(dx,dy)/d. So sep += (-dx/d * f). Yes as written: sepx -= dx*inv*f ✓.
        if v.side != u.side && d2 < nd2: nd2=d2; ne=j;
    // targeting
    u.rt -= dt;
    if (ne>=0){ const d=Math.sqrt(nd2);
       if (!u.tgt || !u.tgt.alive || u.tgt... ) if d < 26 → u.tgt = units[ne];
       else keep u.tgt if alive and dist(u,tgt) < 40 else u.tgt=units[ne] (if d<... hmm)
    }
```
Simplify: target selection each frame: if ne exists and (no valid tgt or dist to ne < dist to tgt*0.8) → tgt=units[ne]. Valid tgt = alive && !? Also if tgt valid but farther than 60 and ne exists closer → switch. Since sense covers ~±72, nearest local enemy found each frame; just do: if ne>=0: if (!tgtValid || nd2 < d2tgt - small) tgt=units[ne]. If tgt invalid → tgt = units[ne] or null.

When tgt exists and dist > engage: move toward tgt.
If no tgt: advance toward advance point: ax = enemy centroid x biased: for side0: destX = enemyC.x, destY = u.y*0.9 + enemyC.y*0.1 + wobble → keeps lanes. Charge trigger: armyState per side: computed by centroid gap: gap = |rc.x - bc.x| basically distance. When gap < 340 → army.charging=true (latches). Speed = charging? u.spd*1.75 : u.spd*0.95.

Movement:
```
if tgt && dist < RANGE (11.5): 
  u.moving=false; face tgt; cd-=dt; if cd<=0: cd=cds*(0.75+rand*0.5); u.swing=1; 
    // damage applied after tiny delay? immediate:
    tgt.hp -= u.dmg*battleRage; bloodBurst(tgt); 
    if tgt.hp<=0 kill(tgt, u)
else if tgt: move toward tgt
else: move toward advance pt
fleeing: if u.flee: move toward home edge x, ignore fight (still take damage).
```
Also add wobble: desired dir rotated by sin(t*3+wsw)*0.25 when advancing (less when charging).

Separation applied always with weight; velocity:
```
vx = dirx*spd + sepx*SEP(≈40); vy = ...;
u.x += vx*dt; clamp to world [-30, Ww+30] (allow fleeing past edge → despawn).
u.a = angle lerp toward atan2(vy,vx) when moving; toward target when fighting.
```

Rout check each frame (after deaths): if !army.broken && army.count>0 && (army.count < enemy.count*0.34 || (t>36 && army.count<=enemy.count)) → break: army.broken=true; for each unit of army: u.fl = rand()*1.4 (delay), after delay u.flee=true; setPhase('breaks'); message with name.

Fleeing unit update: dir toward homeX (side0 → -1), y toward nearest edge? Just run left/right with slight up/down wobble; despawn when x<-30 or >Ww+30: alive=false, removed=true, army.count--, routedCount++.

Wait: count semantics — counters show "on the field". Fleeing units still shown until despawn; when they despawn count decreases. At victory: enemy count reaches 0. But units still fleeing are counted → victory triggers only when all gone. Mop-up: fleeing speed 130 vs chasers 91 — chasers won't catch easily in open field... They can attack fleeing units in range while both run — chasing units slightly slower → rarely catch. Hmm — dramaturgy: fleeing should be cut down somewhat. Options: fleeing speed 95 (≈ chaser charge speed), so chasers catch stragglers due to variance; plus fleeing units despawn at edge quickly. Battle ends within ~3-5s of rout because field width to edge from center ~ 800/95 ≈ 8s. Too long! Reduce: when army breaks, also victory can be declared when enemy has no fighting (non-fleeing) units — then celebration while last stragglers still fleeing off-screen — that's actually realistic: winners celebrate while routing enemy streams away. Let me define: victory when enemy.count_fighting==0 (all either dead or fleeing). Then: remaining fleeing units continue and despawn (counts keep ticking down during celebration — fine, counters show "on field"). Winner celebration begins; routed counter shows total. 

So conditions: army.fighting = count of alive && !flee. Victory when loser.fighting==0 && loser count... also if loser army fully broken. And winner determined at that moment.

Also possible: winner also broken earlier? Only one breaks (checked when counts relations). Once broken, no counter-break. Edge: simultaneous near-zero — handle order.

Timeout: at t>38: smaller side breaks. At t>52 (shouldn't happen): force end.

**Kills:**
```js
function kill(v, by){ v.alive=false; army[v.side].count--; fallen++;
  stampBlood(v); stampCorpse(v); puff particles; smoke maybe;
  if(v.banner) stampFlag(v);
  if(by) army[by.side].kills++? not needed.
}
```

**Particles:** array of {x,y,vx,vy,life,tl,type,r,seed}. Types: 0 blood drop (dark red, gravity none, friction, shrink), 1 dust puff (tan-gray expanding fading), 2 smoke (gray, slow drift, long life, grows), 3 spark (bright, tiny, fast fade). Spawn on hit: 3-5 blood + 1 small dust; on death: 8-12 blood, 2-3 dust, 1 smoke (30% chance), stamp.

Update in screen space? I said spawn projected. Positions of hit are unit positions — project each spawn (cheap). Particle sim: x+=vx*dt etc., vx*=0.9^, life-=dt. Draw: dust: soft circle via globalAlpha & fill (no gradient per particle — use radial? expensive; use plain circle with low alpha, two circles layered). Smoke: circle alpha 0.05-0.1 large. Blood: 1-2px squares/circles dark red. Sparks: 1px light.

Cap: if particles.length>700 splice oldest (shift ok occasionally or ring).

**Stamps list:** each stamp: {t:'b'|'c'|'f', x,y(world), s(scale world→ computed at draw), ang, side, seed}. Stored with world coords so resize re-projects. Cap 1000 FIFO via array shift (shift on array of ≤1000 occasionally fine — do splice(0, chunk) when over). redrawStamps iterates and draws each. Stamp draw:

blood: seeded RNG (mulberry32 from seed) → 6-9 blobs: dctx.fillStyle dark red rgba(70,10,10,0.55) varying; center + offsets within s*1.4; sizes s*(0.25..0.7); plus 4 speckles. Also slight darker core.

corpse: rotate ang; body ellipse (s*1.5, s*0.8) fill muted dark faction color (mix toward #2a2320 70%); helmet dot; weapon line nearby; alpha 0.9. Under: blood already stamped first (call order).

flag: pole line lying + small flag cloth.

Stamp s: world radius ~5 → pixel: s_world * scaleAt(p)*pw... define stampScale = sc (the same sc as proj returns: sc = lerp(sFar,sNear,p)*pw). Draw with size = base * sc.

**Draw units:**
Sort alive by y. For each: proj → sx,sy,sc. unit pixel radius r = (2.9 + big?0.7:0) * sc * ... let me calibrate: world spacing 10.5, so unit diameter ~7 world units → radius 3.5 world → pixels: sc = pw*scale; pw=VW*0.98/1600; for VW=1600: pw=0.98; scale mid 0.83 → sc≈0.81 → r≈2.8px. Hmm small. Screen density: 1000 units on 1600×900 canvas — units ~5-6px wide at mid — looks right for epic scale. But visibility for recording... maybe bump: radius world 3.6 (diameter 7.2 vs spacing 10.5 — gap ok). Let me set base r=3.4 world, sc factor as above; at VW=1280: pw=0.784, sc≈0.65 → r≈2.7px diameter 5.4 — small but massed armies read well. Maybe increase global zoom: make field not full width? The trapezoid uses full canvas. Alternatively scale unit visual ×1.25 relative to spacing (overlap slightly — armies look dense, good): r=4.2 world → near-screen ~ 6.6px diameter... units overlapping slightly when in ranks reads as packed formation. I'll try r=3.9, big=+0.9.

Draw:
```
// shadow
ctx.fillStyle='rgba(10,12,8,0.35)'; ellipse(sx+1.2*sc*?*, sy+r*0.55, r*1.05, r*0.5)
Hmm shadow offset consistent light from upper-left: offset (+r*0.25, +r*0.35)? For top-down slight perspective, shadows directly under with slight offset down-right: ellipse at (sx+r*0.3, sy+r*0.55) radii (r*1.1, r*0.55).
// banner pole behind (if banner): line from unit up: (sx, sy) to (sx - sway, sy - r*4.2) width 1; flag quad at top with wave.
// sword (behind or front depending swing? just draw after body): 
swing phase u.swing decays: u.swing -= dt*7 (from 1→0); sword angle: rest = a + side*0.9? Let me define weapon side per unit w=±1. restAng = a + w*1.25; swingAng = a + w*(1.25 - (1-swing... during swing sweep across front: ang = a + w*(1.25 - 2.2*easeOut(swingInv)) hmm. Simpler: ang = a + w*1.25 - w*2.3*Math.sin(min(1,1-u.swing)*π)? Let me define: progress p=1-u.swing (0→1); sweep = sin(p*π) * 1.9 * w; ang = a + w*(1.05 - 1.9*Math.sin(p*Math.PI))? At p=0: a+w*1.05; p=.5: a+w*(1.05-1.9)=a-w*0.85 (crosses front); p=1: back to rest. Good enough — a quick swish.
tip: hx = sx + cos(ang)*r*1.9, hy = sy + cos? plus vertical squash for perspective: unit's "up" — treat all in screen plane: fine.
sword draw: stroke width r*0.3, color '#d8d9d4' with slight shade; plus guard dot darker.
Actually order: draw sword BEFORE body when rest (looks held behind)? Simpler always after body — reads as raised weapon. OK.
// body
fill: faction base with tint variation: precompute per-unit color string (e.g., hsl(h, s%, l%) around base) — 1000 strings precomputed at creation (u.col, u.colD (dark rim), u.helm).
ctx.beginPath(); arc(sx, sy, r); fill u.col; lineWidth r*0.28; stroke u.colD? Stroke separate path... combine: after fill, stroke same path with u.colD.
// blood tint when hurt: if hp<mhp*0.55: overlay arc fill rgba(90,15,15, (1-hp/mhp)*0.55).
// helmet: small circle radius r*0.52 at (sx+cos(a)*r*0.42, sy+sin(a)*r*0.42 - r*0.1): fill u.helm (light steel #b9bcc0 or faction-tinted), tiny dark stroke.
Victory hop: y -= bounce (applied to sy and shadow stays) — hop offset hy = -|sin|*r*1.2; draw shadow smaller when airborne.
```
Facing: u.a smoothing: shortest-angle lerp.

Perf micro: set fillStyle per unit (necessary for variety). 3 fills + strokes per unit ~ 4-5k draw calls — ok.

**Particles draw** after units. Smoke under units? draw smoke first (background haze), then units, then blood/dust/sparks. Order: decals(bg composite) → smoke → units(sorted) → particles → weather overlays.

Hmm smoke above ground below units = ground fog; also nice above — pick below units for legibility, plus a few high wisps above? Keep below units + also spawn some "battle haze" large above? Simple: draw smoke AFTER units with alpha 0.06 — slight haze over melee, atmospheric. I'll draw smoke after units at low alpha; blood/dust after too. Fine.

**Clash detection for phase/shake:** track firstCombatTime when first kill or first attack happens → phase "The lines collide". Shake on clash: shake=5 decaying. Also periodic small shake pulses when many units engaged: shake = max(shake, min(2.2, engaged*0.004))? Subtle constant rumble during melee: shake base 0.6 while engaged>200. Implement: shake decays toward base rumble.

**HUD updates:** every frame: if counts changed update textContent & bar widths; casualty line "X fallen · Y routed" bottom-center; phase text on change with animation.

**Victory:**
```js
function endBattle(winner){ state='victory'; vt=0; winners units → u.celebrate=true;
 verdict DOM: over 'VICTORY' (or 'THE FIELD FALLS SILENT' draw), name = winner name colored chip, sub: 'holds the field — N fell in M seconds'? Show "survivors: n". Show with class.
}
```
During victory: celebrate units hop & raise swords; banner flags wave big. After 5.2s → fadeOut (fader opacity 1) over 0.9s → newBattle() → fader fade back.

Battle number increments; title text updates at battle start (while fader black).

**newBattle():**
```
seed randoms: names, palettes for ground? Ground regen costs ~ms — fine (one-time per battle ~30ms acceptable during black fade).
Actually regenerating bg each battle: strips+texture ~ maybe 20-40ms — acceptable hitch hidden by fader.
units regenerate; stamps cleared; particles cleared; counters; state='intro'; introT=0; fader transition back to 0.
```
Intro: title animates in (CSS class 'show' on titleWrap; re-trigger). Armies stand ~0.8s then advance (phase 'advance' message "The armies advance"). Start moving after 0.9s delay (u.hold=0.8+rand0.4).

**Winning-side celebration details:** u.celeb: bounce = |sin((t-vt0)*5.2 + u.wsw)|... hop only some units (random phase), swords up: draw sword pointing up-left/up-right with sway sin. Also occasionally cheer ring? skip.

**Names/colors:**
Red base: hue 6, sat 55%, light 47% → #b73f31-ish. col variation: l ±6, h ±4. colD: same h, l-18%. Blue: hue 210, sat 38%, light 46%. Ensure not "default blue" look: 210 with low sat and slightly desaturated steel — ok, it's the faction color the user explicitly wants (red vs blue). Banner flag brighter: l+12%.

HUD accent chips use same.

**Numbers formatting:** plain integers.

**Loop timing:** last=performance.now; dt=min(0.05,(now-last)/1000)*SPEED where SPEED=1.0. Cap units update fine.

Also handle document hidden — rAF pauses automatically; dt clamp handles resume.

**Draw order details & painter's algorithm:** corpse decals are baked so always under. Shadows under bodies drawn per-unit in sorted order — a near unit's shadow may paint over a farther unit's feet — actually shadow drawn just before its own body; overlap edge cases negligible.

**Testing potential pitfalls:**
- Grid indices for out-of-range coords: clamp cell coords.
- tgt references to dead units — check alive.
- units array grows? fixed MAXU = 2*560; reuse array each battle (create fresh, fine, GC ok).
- Routing while melee: fleeing units get attacked; their hp drop; they die fleeing → counts fine.
- Winner chase: after loser broken, winner units target fleeing enemies — sense finds them; dist<engage → chase; they'll attack when in range even while fleeing moves... fleeing units move fast; attacker stands (attack range stop) — chase dynamics: attacker moves toward tgt until range, then stops and swings; fleeing target escapes range → attacker moves again. Works.
- After all enemies gone (fighting==0 and count maybe >0 fleeing): trigger victory once: winner = other side; but what if both sides simultaneously have fighting==0 (mutual destruction)? Then compare alive counts (fleeing) or declare draw. Handle: check after deaths each frame: 
  ```
  f0=army0.fighting, f1=army1.fighting;
  if(state==='battle'){ if(f0===0&&f1===0) → draw/compare alive counts; else if f1===0 → winner 0 ...}
  ```
  Also loser army might break but keep few fighters? Break sets all to flee eventually (delays ≤1.4s) → fighting → 0 within 1.4s. But units mid-fight when break triggers: they get flee=true after delay; they'll disengage (movement toward home regardless of tgt). But they can still be attacked & die while fleeing. Fine.
- Victory condition check ALSO for count===0 (annihilation) — covered by fighting==0.
- Timeout t>42 → break smaller side (if not already); t>60 → force end (winner by count) safety.

**Charging ramp:** armies advance; trigger charge per army when centroid distance < 360 → set charging (speed up) — also individual units charge when their nearest enemy < 200: speed = base*(charging?1.8:1). During 'advance', units hold formation: destination = (enemyC.x + u.laneOffX? , u.homeY + drift). lane: destY = u.y0 (initial y) + small; destX = enemy centroid x. Since separation keeps spacing, formation maintains.

First clash detection: when any attack happens first time (kills>0 or attacks>0) → phase.

**Phase messages list:**
- intro: "Two hosts drew up in battle array" — hmm keep simple present tense lines:
  - advance: "The armies advance across the open field"
  - charge: "Drums beat — the lines charge!"
  - clash: "The lines collide — the slaughter begins"
  - melee (10s in): "No order remains — it is a savage melee" (random from 2-3 variants, set once)
  - rout: "{loser} breaks and flees the field!"
  - victory: "{winner} holds the field!"

Counter labels: army name small caps + count. Bars relative to initial.

**Title composition:** overline: `BATTLE ${roman}` — roman numerals up to whatever (function). Title: `The Battle of ${place}` maybe with suffix flavor: place list with occasional descriptors: 'the Ford of Wolves'? Keep simple: places list.

Also under counters: small label "ON THE FIELD". Bottom center: `☠`? no icon fonts... plain text: "1,247 fallen · 213 routed · 0:28" — elapsed. Include elapsed mm:ss ticking — nice. No emoji — plain text with middle dots. Good.

**Vignette + haze overlay:** build once per resize: radial gradient transparent center → rgba(8,10,8,0.42) corners; plus linear top gradient rgba(20,24,26,0.35)→0 over top 18%. Grain: 160×160 noise canvas, alpha ~0.04, drawImage as pattern over full screen once into overlay canvas.

**Smoke/haze accumulates:** fine.

Now, code writing. Let me write it thoroughly and carefully, watching for bugs.

Also remember: no external anything. All good.

Let me now also decide numbers:

- N per army: 520. World 1600×900.
- Formation gens:
  - block: cols(ranks along facing? I'll define rank = line perpendicular to facing, i.e., spread along y): widthUnits = 26 spread along y, ranks 20 along x. sx (y-spacing) = 11, rankDepth = 11. So block occupies y: 26*11=286 tall (fits in 900), x depth 220.
  - line: width 40 → 440 tall, ranks 13 → 143 deep.
  - wedge: 20 ranks, front width 5, +2.3 per rank → last 4+19*2.3≈47.7 → width ~ 47*11=517 tall — hmm tall. Use width_i = 5 + i*2.2 → sum=100+2.2*190=498 ✓ last width 46.7*11=514. Slightly large but ok (y from cy-257 to cy+257 → within 900 if cy=450 ✓ edges 193..707 fine).
- y positions: y = cy + (j - (w-1)/2)*ysp; j from 0..w-1.
- x: side0 (red, faces +x): frontX = cx + halfDepth; rank i: x = frontX - i*rankDepth (i=0 front). cx=370 → block frontX=370+ (20-1)*11/2=370+104.5=474.5; line frontX=370+72=442; wedge frontX=370 (front row at cx? define frontX = cx + ranks*rankDepth/2). Let me define formation occupies x∈[cx - ranks*rd/2, cx + ranks*rd/2], front at max for side0.
  - block ranks 20: cx=370 → x∈[260,480].
  - line ranks 13: x∈[298,441].
  - blue mirrored: cx=1230.
  Gap between fronts (block-block): 1220-104.5 - (370+104.5) = 1115.5-474.5=641. Advance speed: base u.spd 52-66 → avg 59, closing 118 → 5.4s to contact if they meet at midpoint. Too slow. Options: raise advance speed to ~72 (closing 144 → 4.4s), then charge at gap<380: speeds 1.75× (126 each, closing 252): after gap 360: ~1.5s → contact ≈ 3.4-3.8s ✓. Or start blocks closer: cx red 400, blue 1200 → gap 800 center-to-center → front gap ≈ 800-209=591. advance closing 118: gap 360 reached at t=1.95s; then charge 252 closing → contact +1.43s → t≈3.4s. ✓ Let me use cx=400/1200 and advance speed multiplier 1.15.

Also stagger: units have hold delay 0.6-1.3s before moving (so title reads) — contact ~4.2s. OK.

Combat pacing: dmg 15-24 avg ~19.5; hp 88-100 avg 94 → hits to kill ~4.8; cd ~0.55 avg with swing variance → kill ≈ 2.6s of sustained 1v1. But multiple attackers and density raise effective rate. Front width e.g. 286 (block front 26 units) — initial clash ~26 v 26 duels; each side kills a unit every ~2.6s → 20 deaths/sec? Death rate = both sides engaged count / 2.6 ≈ (26+26)/2.6 = 20/s initially; ranks behind fill in → engaged grows to maybe 150-250 total → deaths 60-100/s?? That seems too fast — but encirclement limited: units attack only within 11.5 range; pile-ups concentrate. Realistically the melee front expands around crescent. Overall I estimate end at 18-28s. Ramp: after t=24, dmg scale +60% → guaranteed end ~30s. Rout threshold 0.35 triggers earlier typically. Good; plus hard timeout.

Also to make winner more decisive (celebration with decent survivors ~150-250), snowball helps.

Alright — also "slight perspective" ✓ via trapezoid + scale + shadows.

**Performance of per-frame sorting:** create array each frame? Reuse `order=[]` push indices... I'll push unit refs into preallocated array and sort with comparator (a.y-b.y). Fine.

**Let me write the final code.**

```js
// ===== constants
const Ww=1600, Hw=900, CS=48, GW=34, GH=19;
```

Wait GW=ceil(1600/48)=34 (33.33→34), GH=ceil(900/48)=18.75→19. ✓

cell(x,y): cx=x/CS|0 clamp 0..GW-1.

**RNG:** mulberry32 for seeded per-battle; plus Math.random fine. Use simple rnd() wrapper.

**Seeded per-stamp randomness:** store seed; redrawStamps uses mulberry32(seed) per stamp → deterministic redraw on resize. 

**Text/labels DOM caching.**

Let me write all the code now, mentally compiling.

```js
(function(){
'use strict';
// DOM
const cv=document.getElementById('scene'), ctx=cv.getContext('2d');
const el = id=>document.getElementById(id);
const nameL=el('nameL'), nameR=el('nameR'), cntL=el('cntL'), cntR=el('cntR'), barL=el('barL'), barR=el('barR'),
 overline=el('overline'), titleEl=el('title'), phaseEl=el('phase'), tally=el('tally'),
 verdict=el('verdict'), vName=el('vName'), vSub=el('vSub'), fader=el('fader'), titleWrap=el('titleWrap');

let DPR=1,VW=960,VH=600;
let topY=0, depth=1, pw=1;
const PEXP=1.42, SFAR=0.60, SNEAR=1.07;

const bgC=document.createElement('canvas'), bgX=bgC.getContext('2d');
const dcC=document.createElement('canvas'), dcX=dcC.getContext('2d');
const ovC=document.createElement('canvas'), ovX=ovC.getContext('2d');
```

proj:
```js
function projX(x,p,sc){ return VW*0.5 + (x-Ww*0.5)*sc; }
function scaleAt(p){ return (SFAR+(SNEAR-SFAR)*p)*pw; }
function projY(y){ const p=y/Hw; return topY + Math.pow(p,PEXP)*depth; }
```
Per unit compute p=y/Hw, sc=scaleAt(p), sx=projX, sy=topY+p^PEXP*depth — compute pow per unit per frame: 1000 pows fine.

**resize:**
```js
function resize(){
 DPR=Math.min(window.devicePixelRatio||1,2);
 VW=window.innerWidth; VH=window.innerHeight;
 cv.width=Math.round(VW*DPR); cv.height=Math.round(VH*DPR);
 cv.style.width=VW+'px'; cv.style.height=VH+'px';
 ctx.setTransform(DPR,0,0,DPR,0,0);
 bgC.width=cv.width; bgC.height=cv.height; bgX.setTransform(DPR,0,0,DPR,0,0);
 dcC.width=...; dcX.setTransform(...);
 ovC...; 
 topY=VH*0.082; depth=VH*1.03-topY; pw=VW*0.985/Ww;
 buildOverlay();
 if(groundReady) buildBackground();
 redrawStamps();
}
```
bg needs current battle palette: store currentPalette; buildBackground uses it. On new battle: palette=pick; buildBackground().

**Ground texture:**
```js
let texC, texX; const TW=768, TH=432; // world 1600x900 → 0.45 scale? 1600*0.45=720; let TW=720,TH=405.
function makeGround(pal){ texC=document.createElement('canvas'); ... base fill hsl(pal.h, pal.s, pal.l);
 // patches: 90 radial-ish blobs: use arc fill with alpha colors: for i<70: x,y,r=30-90; fillStyle hsla(h+rand±14, s, l±7, .12); arc fill.
 // speckles: 5000 tiny: fillStyle random dark/light alpha .1-.25; fillRect 1x1 (at tex scale, 1px ≈ 2.2 world ≈ fine)
 // faint streak lines? skip
 // vignette-ish noise ok
}
```
Draw with imageSmoothing on.

**buildBackground:**
```js
function buildBackground(){
 const g=bgX; g.clearRect? fill sky:
 // sky gradient
 let sky=g.createLinearGradient(0,0,0,topY+VH*0.02);
 sky.addColorStop(0,'#31353c'); sky.addColorStop(0.7,'#6d6a63'); sky.addColorStop(1,'#a89a82');
 g.fillStyle=sky; g.fillRect(0,0,VW,topY+2);
 // sun haze: radial at (VW*0.5, topY) r VW*0.5: rgba(240,225,190,0.20)→0; fill rect top region.
 // far hills: path across at y=topY*0.55..: draw 2 layers with wavy sine silhouettes:
 hill(yBase, amp, color): begin at x=0..VW step 8: yy=yBase + sin(x*0.012+seed)*amp + sin(x*0.03)*amp*0.5; path down to topY+2 fill.
 hills colors: '#5c5c55'? more hazy: mix with sky: back '#8b8578' alpha? Use solid muted: back hill '#7a7568', front treeline '#4a4d42'.
 // treeline: darker with bumpy top (small arcs).
 // field strips
 const strips=170; const stepW=Hw/strips;
 g.save(); // clip field region? not needed.
 for(i=0;i<strips;i++){
   const y0=i*stepW, y1=y0+stepW+0.5;
   const p0=y0/Hw, p1=y1/Hw;
   const sy0=topY+Math.pow(p0,PEXP)*depth, sy1=topY+Math.pow(p1,PEXP)*depth;
   const pm=(p0+p1)/2, sc=scaleAt(pm);
   const dw=Ww*sc, dx=VW*0.5-dw*0.5, dh=sy1-sy0+1;
   const sY=y0*(TH/Hw), sH=(y1-y0)*(TH/Hw);
   // draw 3 tiles to cover sides
   g.drawImage(texC, 0, sY, TW, sH, dx, sy0, dw, dh);
   g.drawImage(texC, 0, sY, TW, sH, dx-dw, sy0, dw, dh);
   g.drawImage(texC, 0, sY, TW, sH, dx+dw, sy0, dw, dh);
 }
```
Wait tiles at dx-dw and dx+dw: covers left/right when dw<VW. When dw>VW near bottom, center covers all. ✓ But texture tiling: tex is not seamless; edges visible seams at tile joins — mitigate: draw mirrored? Or make texture wrap-ish by drawing with slight overlap and it's low-contrast noise → seams subtle. Alternatively side areas beyond world get darkened anyway (out of field). Actually only far rows have dw<VW; sides there are hazy anyway (distance fog overlay). Acceptable; also I can darken toward horizon with haze gradient overlay after strips: linear gradient from rgba(haze,0.5) at topY → 0 at topY+VH*0.35 — atmospheric perspective ✓ (this also hides seams).

Also side-fade: horizontal gradients darken left/right edges — vignette handles.

 // haze
 g.fillStyle=grad; g.fillRect(0,topY-1,VW,VH*0.30);

 // rocks/tufts/etc using proj:
 rocks: n=34: wx=rand(60,Ww-60), wy=rand(30,Hw-30): p,sc: draw shadow+ stone: gray ellipse rot random. Also 3 craters: ellipse darker + rim.
 trees: 4-6 at wy<160 or near edges: trunk line dark brown, canopy 2-3 dark green blobs; scale by sc; also long-ish shadow.
}

Wait drawImage source rect sY may exceed TH at last strip: clamp: sH = min(TH - sY, ...). Handle: const sH=Math.min(TH - sY, (y1-y0)*(TH/Hw)); ensure >0. Last strip y1=Hw → sY=y0*TH/Hw, sH=TH-sY ✓ if I clamp.

**Overlay (vignette+grain):**
```js
function buildOverlay(){
 o=ovX; clear; 
 radial gradient centered (VW/2, VH*0.55) inner r VH*0.35 alpha0 → outer max(VW,VH)*0.75 rgba(6,8,6,0.5). fillRect.
 top linear: 0→topY+VH*0.18: rgba(15,18,20,0.28)→transparent? Actually haze already in bg; skip top.
 grain: noise canvas 140×140 with random gray pixels alpha; create pattern, fill rect with globalAlpha 0.05.
}
```
Grain via ImageData: for pixels: v=rand*255, alpha 255; then pattern fill with globalAlpha 0.045 and gCO 'overlay'? keep normal, alpha 0.05 — subtle. Actually 'overlay' comp on canvas supported — keep simple normal low alpha.

**Stamps:**
```js
const stamps=[];
function stampBlood(x,y,s,seed){ stamps.push({k:0,x,y,s,seed}); trim(); }
function stampCorpse(x,y,s,ang,col,seed){...k:1}
function stampFlag(...k:2)
trim: while(stamps.length>1100) stamps.shift();
redrawStamps(): dcX.setTransform(DPR..); clearRect; for each s: drawStamp(dcX,s);
function drawStamp(g,s){
 const p=s.y/Hw, sc=scaleAt(p), sx=VW*0.5+(s.x-Ww*0.5)*sc, sy=topY+Math.pow(p,PEXP)*depth;
 const r=s.s*sc; const rng=mulberry32(s.seed);
 if k0 blood: g.fillStyle=... base 'rgba(66,10,12,0.6)': n=6+rng()*4 blobs: bx=sx+(rng()*2-1)*r*1.6, by=sy+(rng()*2-1)*r*1.15 (squash y), br=r*(0.25+rng()*0.55); fill circle alpha vary.
   plus darker core circle r*0.5 'rgba(40,6,8,0.6)'.
 if k1 corpse: g.save translate rotate: body ellipse fill s.colDead (precomputed muted), helmet circle '#8b8f93' at front, weapon line '#6a6d6a' angled, alpha handled by colors.
 if k2 flag: pole gray line angled on ground + flag rect/tri colored dead-ish.
}
```
Corpse needs colDead: compute at kill from unit's hue: darken a lot: I'll precompute per unit deadCol at creation: `hsl(h, s*0.5, l*0.42)` string.

**Units & armies:**

```js
const MAXU=1200;
const units=[];
let armies=[{...},{...}];
function newBattle(){
 battleN++; ...
 seedNames...
 palette = PALETTES[rand]
 makeGround(palette); buildBackground();
 stamps.length=0; particles.length=0;
 units.length=0;
 fallen=0; routedC=0; t=0; state='intro'; introT=0; shake=0;
 armies=[makeArmy(0), makeArmy(1)];
 setHudNames(); updateCounters(true);
 titleWrap class show retrigger; verdict hide; fader to 0 (css transition).
 setPhase('intro') → phase text "Two hosts prepare to meet" hmm during intro; after hold: 'advance'.
}
```

makeArmy(side):
```js
const nBase=520;
const name= side? pick(NAMES_B):pick(NAMES_R);
const hue= side?214:7, sat= side?40:56;
const str=0.93+Math.random()*0.14;
const form=pick(['block','line','wedge']);
army={side,name,hue,sat,count:0,fighting:0,initial:0,broken:false,charging:false, cx: side?1200:400, color css for hud}
positions per formation (as planned).
for each pos: u={x:x+jit, y:y+jit, y0:y, side, a: side?Math.PI:0, spd:54+rand*16, hp:86+rand*26, mhp:same, dmg:15+rand*10, cd:rand*0.6, cds:0.42+rand*0.24, tgt:null, rt:Math.random()*0.3, swing:0, sw:Math.random()*6.28, big:Math.random()<0.06, banner:false, flee:false, fl:0, col, colD, deadCol, w: ±1 weapon side}
army.count++; army.initial++;
after: assign banners: 3 random indices banner=true; hp*=1.7; mhp*=1.7;
```

Colors: 
```js
function shade(h,s,l,a=1){return `hsla(${h},${s}%,${l}%,${a})`}
u.col = shade(hue, sat, 44+rand*14); u.colD = shade(h,s, l*0.55); u.deadCol= shade(h, s*0.55, 20+rand*4);
```
Blue hue 214 sat 42 light 40-52. Red hue 6 sat 58 light 40-52.

Helmet color: '#a9adb3' with variation? shared constant fine + slight vary: precompute hCol = shade(210,8,66+rand*14).

**Grid:**
```js
const head=new Int32Array(GW*GH), nxt=new Int32Array(MAXU);
function cellOf(x,y){ let cx=(x/CS)|0; if(cx<0)cx=0; else if(cx>=GW)cx=GW-1; similarly cy; return cy*GW+cx; }
```

**update(dt):** as planned. Also handle 'intro' hold: u.hold -= dt; movement only when hold<=0 && state allows. state 'intro' short then auto to 'advance' when t>0.9 (setPhase advance, message). Charging: compute centroid gap: 
```
const gap=Math.abs(a0.cx0 - a1.cx0)? use current centroid: track sum each frame: cxSum per side.
if(!army.charging && gapX < 380) army.charging=true; if both charging first time → setPhase('charge').
```
Actually use centroids of alive: recompute per frame (sum x,y / count). When both charged → phase 'charge' once.

Contact phase: when first attack executed → if phase<clash: setPhase('clash'), shake=6.

Speeds: advance mult 1.0 (spd ~54-70); charge 1.8; flee: spd*2.4. During melee fighting speed 0.

Movement detail:
```
let dx,dy,dest...
if(u.flee){ dirx = side? 1 : -1 ... wait red(side0) home is left (x→-30): fleeDir = side0 ? -1 : +1.
  target point: x = side0? -40 : Ww+40; y = u.y + sin drift → just steer horizontal + wobble.
  desired speed = u.spd*2.35
  u.fl -= dt; if(u.fl>0) stand (panic jitter small) else flee-move.
  despawn when x out.
}
else if(tgt && dist<RANGE){ fight }
else { if(tgt) move to tgt else move to advance point: ax = enemyCentroid.x (per side), ay = u.y0*0.85 + enemyC.y*0.15 + wobble small... plus avoid drifting? fine.
 speed mult: army.charging?1.8: (state==='intro'?0:1.12) hmm advance speed multiplier 1.15 to reach contact ~3.5s: closing = 2*60*1.15=138 → gap 800→ (800-~180 front offsets)/138≈4.5s? Let me recompute: front gap initial ≈ 591 (block). Advance closing 138 → 360 gap at t≈1.7s (plus hold 0.6-1.3 → ~2.5s); charge closing 2*108=216 → contact at ~+1.7s → t≈4.2s. ✓
}
velocity = desired*speed + sep*55; cap; integrate; clamp x∈[-60, Ww+60] (fighting units shouldn't leave top/bottom: clamp y∈[20,Hw-20]).
heading update: if fighting → face target instantly-ish; else smooth toward vel dir: u.a += angDiff*min(1,dt*8).
swing decay: u.swing=max(0,u.swing-dt*6.5).
```

Attack:
```
u.cd-=dt; if(u.cd<=0){ u.cd=u.cds*(0.7+Math.random()*0.6)*armyCdScale; u.swing=1;
 const dScale = 1 + Math.max(0,(battleT-22))*0.06; // rage ramp after 22s up to +... cap 1.8
 tgt.hp -= u.dmg*dScale;
 spawn blood small at tgt proj; 
 if(!firstClash){firstClash=true; setPhase('clash'); shake=Math.max(shake,7);}
 if(tgt.hp<=0) killUnit(tgt);
}
```
killUnit: mark dead, counts, stamps, particles(bigger), smoke 35%, if banner stampFlag + maybe phase flavor? skip.

Retarget: implemented via sense each frame; tgt switching: 
```
if(ne>=0){
  const d2ne=nd2;
  let cur=u.tgt;
  if(!cur || !cur.alive || cur.flee&&?) ... if cur invalid → u.tgt=units[ne];
  else { dx=cur.x-u.x... d2c; if(d2ne < d2c*0.6) u.tgt=units[ne]; else if(d2c>50*50) u.tgt=units[ne]||advance }
} else {
  if(u.tgt && (!u.tgt.alive || distTo tgt > 70)) u.tgt=null;
}
```
Also don't target fleeing units? Winners SHOULD chase fleeing. But units breaking mid-melee: fleeing units become targets — attackers chase — fine. But if MY side is broken and fleeing, I shouldn't fight — flee overrides (movement flee branch). And sense targeting for fleeing unit: skip target logic (they just run).

Fighting stop condition: if tgt && d<RANGE && !u.flee → fight. Also multiple attackers fine.

Also add small "push forward when blocked": if unit wants to advance but ally in front, separation handles.

Rout check (in update after counts change or each frame):
```
if(state==='battle'){
 const a0=armies[0],a1=armies[1];
 if(!a0.broken&&!a1.broken){
   if(t>40){ smaller side break }
   else if(a0.count && a1.count){
     if(a0.count < a1.count*0.35) breakArmy(a0);
     else if(a1.count < a0.count*0.35) breakArmy(a1);
   }
 }
 // victory check
 const f0=a0.fighting, f1=a1.fighting; // computed as counts of alive&&!flee
 if(f0===0||f1===0){
   let win = f0===0&&f1===0 ? (a0.count>a1.count?0:(a1.count>a0.count?1:-1)) : (f1===0?0:1);
   endBattle(win);
 }
}
```
fighting counts: maintain arrays or compute each frame in unit loop (flag). Compute per frame: army.fighting++ when unit alive&&!flee during update loop reset at start.

Edge: at very start f could be 0 only if army dead. ok.

breakArmy(a): a.broken=true; for u of units if u.side===a.side&&u.alive&&!u.flee: u.fl=Math.random()*1.5; (they become flee after delay: in update: if(!u.flee && u.fl>0){u.fl-=dt; if(u.fl<=0) u.flee=true;} — set fl only for broken side units). Also setPhase(a.name+' breaks!'). Actually message: `${a.name} breaks and flees!`. routedPending tracked.

Also when broken, some units might be surrounded and keep fighting until fl elapses — fine, adds mop-up.

Despawn fleeing: in update after move: if(u.flee && (u.x<-25||u.x>Ww+25)){ u.alive=false; a.count--; routed++; } — but alive=false with unit still in array; skip in loops via alive check. Also fights: fleeing can be hit; killUnit handles count--. Ensure no double count: killUnit checks v.alive.

**endBattle(w):**
```
state='victory'; vt=0; winner=win;
for u alive side w: u.celeb=true (with random cheer offset) — store vicT=t.
loser fleeing continue.
verdict DOM: if win>=0: overline 'VICTORY', vName = army name, colored underline; vSub = `${armies[w].count} survivors hold the field`; else 'NO SURVIVORS' ... draw text 'The field falls silent — none survived.'? If both annihilated (rare): overline 'ANNIHILATION'.
show verdict (css class). phase: `${name} holds the field.`
shake=0.
```
Victory update: units celebrate: bounce in draw. After vt>5.6: fadeOut: fader.classList.add('on') (opacity 1, transition .9s); after vt>6.8 → newBattle() and fader remove 'on'.

Fader control: use two timeouts? Manage in loop with vt thresholds. newBattle sets verdict hidden, fader back to transparent (remove 'on') after small delay (need transition both ways: set transition 0.9s; when removing class it fades back — but we want battle visible under fade... sequence: fade to black → swap scene (bg, units, title) → fade from black. So: at vt=5.4 add 'on'; at 6.5 (black) call newBattle() which rebuilds everything and sets state='intro'; then requestAnimationFrame next tick remove 'on' → fades in over 0.9s while intro runs. Title 'show' class retrigger at newBattle+0.2s. Manage via flags: pendingRestart.

Actually simpler: in loop:
```
if(state==='victory'){ vt+=dt; if(!fading && vt>5.4){fading=true; fader on} if(fading&&vt>6.5){ newBattle(); } }
```
newBattle resets vt? state='intro'. In newBattle: after rebuilding, requestAnimationFrame(()=>fader.classList.remove('on')). Title show handled: titleWrap re-animate: remove 'show', void offsetWidth, add 'show'.

**Intro phase:** state 'intro': units stand (hold). At t>0.9: state='battle'; setPhase('advance'); Actually merge: keep state 'battle' with battlePhase var. Use `phase` enum: 'intro','advance','charge','clash','melee','rout','end'. Transitions:
- intro → advance at t>1.0 (units start moving when phase!=='intro').
- advance → charge when both armies.charging → 'charge' msg "The drums beat — the lines charge!"
- first attack → 'clash' "The lines collide!"
- clash → 'melee' at clashT>6: random flavor: ['No order remains — a savage melee','The center buckles — the ranks dissolve','Banners fall — the melee spreads'].
- rout → `${name} breaks!`
- victory.

setPhase(txt?) — phaseEl textContent + animate. Also phase changes update? Keep last.

Melee random flavor timer maybe change every 8s during melee — nice liveliness. Implement: if phase==='melee' && t-lastFlavor>9 → pick another.

**HUD count update:** cache last values; bar width via style.width = pct%. Also color chips static per battle (set on newBattle: nameL.textContent etc., chip colors via style).

Tally line: `${fallen} fallen · ${routed} routed · ${m:ss}` — update when second changes.

**Draw function:**

```
ctx.clearRect? draw bg: ctx.drawImage(bgC,0,0,VW,VH) — careful: bgC is DPR-sized; with ctx transform DPR set, drawImage(bgC,0,0,VW,VH) draws scaled correctly ✓.
// decals
ctx.drawImage(dcC,0,0,VW,VH);
// shake applied to world elements: apply ctx.save(); ctx.translate(shakeX,shakeY) around decals+units+particles? Decals baked... shake translating whole frame incl bg looks fine: apply translate to ALL (bg too) — simplest: ctx.save/translate at top after clearing. Vignette overlay unshaken (drawn after restore). ✓
// smoke (particles type 2) first? draw after units low alpha — decided draw smoke last with everything; simpler single particle pass after units.
// units sorted
// particles
// victory flash? none
ctx.restore();
ctx.drawImage(ovC,0,0,VW,VH);
```

Ordering: bg → decals → smoke? I'll include smoke in particle pass but draw smoke before units for grounding and blood after — two passes over particles: pass1 type smoke (before units), pass2 others (after). Particle count small — fine.

**Unit draw code:**

```js
function drawUnit(u){
 const p=u.y/Hw; const sc=scaleAt(p);
 const sx=VW*0.5+(u.x-Ww*0.5)*sc;
 let sy=topY+Math.pow(p,PEXP)*depth;
 const r=(u.big?4.3:3.5)*sc;
 // victory bounce
 let hop=0; if(u.celeb){ hop = Math.abs(Math.sin((vt)*6+u.sw))* r*1.5 * (u.big?1.2:1); }
 // shadow
 ctx.globalAlpha=1;
 ctx.fillStyle='rgba(12,14,10,0.33)';
 ctx.beginPath(); ctx.ellipse(sx+r*0.35, sy+r*0.55, r*1.05, r*0.5, 0,0,6.283); ctx.fill();
 sy-=hop;
 const ca=Math.cos(u.a), sa=Math.sin(u.a);
 // banner pole (behind): 
 if(u.banner){ ctx.strokeStyle='#d9d2c0'; ctx.lineWidth=Math.max(1,r*0.16);
   const wob=Math.sin(tGlobal*3+u.sw)*0.18;
   px=sx - sa*? pole points "up" screen: from unit top to (sx+ wob*r, sy - r*4.6):
   ctx.beginPath(); ctx.moveTo(sx, sy-r*0.2); ctx.lineTo(sx+wob*r*2, sy-r*4.8); ctx.stroke();
   flag: at top: draw wavy triangle: points around (fx=fy...) use path: 
   const fx=sx+wob*r*2, fy=sy-r*4.8;
   ctx.fillStyle=u.flagCol; ctx.beginPath();
   ctx.moveTo(fx,fy);
   ctx.quadraticCurveTo(fx+r*1.6, fy+r*0.4+w2, fx+r*2.4? , ...)
```
Flag: simpler: draw as a small flag: two curves forming waving pennant:
```
const w1=Math.sin(tGlobal*6+u.sw)*r*0.35;
ctx.beginPath(); ctx.moveTo(fx,fy);
ctx.quadraticCurveTo(fx+r*1.3, fy - r*0.5 + w1, fx+r*2.6, fy - r*0.2 + w1*0.6);
ctx.lineTo(fx+r*2.6, fy + r*0.5 + w1*0.6);
ctx.quadraticCurveTo(fx+r*1.3, fy + r*0.1 + w1, fx, fy+r*0.9);
ctx.closePath(); ctx.fill();
```
Rough waving banner — fine. During celebrate, wave faster (freq *1.6).

 // sword (draw before body so it appears behind? Let me draw sword after body but positioned from center — overlapping body slightly, reads as held. Actually behind looks better for rest. I'll draw sword first (behind body), then body over its base.
 sword: 
```
let ang;
if(u.swing>0){ const pr=1-u.swing; ang=u.a + u.w*(1.15 - 2.1*Math.sin(Math.min(1,pr)*Math.PI)); }
else if(u.celeb){ ang = -Math.PI/2 + Math.sin(tGlobal*4+u.sw)*0.22 + (u.w*0.25); } // raised up
else ang = u.a + u.w*1.15 + Math.sin(tGlobal*2+u.sw)*0.06;
const ex=sx+Math.cos(ang)*r*2.1, ey=sy+Math.sin(ang)*r*2.1;
ctx.strokeStyle='#cfd2cd'; ctx.lineWidth=Math.max(1,r*0.26);
ctx.beginPath(); ctx.moveTo(sx+Math.cos(ang)*r*0.4, sy+Math.sin(ang)*r*0.4); ctx.lineTo(ex,ey); ctx.stroke();
// guard
ctx.fillStyle='#7c7f78'; ctx.fillRect(sx+Math.cos(ang)*r*0.55-..., ...) skip guard, add pommel dot maybe skip.
```
 // body
```
ctx.fillStyle=u.col; ctx.beginPath(); ctx.arc(sx,sy,r,0,TAU); ctx.fill();
ctx.lineWidth=Math.max(0.6,r*0.22); ctx.strokeStyle=u.colD; ctx.stroke();
// damage tint
const hr=1-u.hp/u.mhp; if(hr>0.15){ ctx.fillStyle=`rgba(88,14,14,${(hr*0.55).toFixed(3)})`; ... arc fill }
// helmet
ctx.fillStyle=u.hcol; ctx.beginPath(); ctx.arc(sx+ca*r*0.42, sy+sa*r*0.42 - r*0.15, r*0.5,0,TAU); ctx.fill();
ctx.strokeStyle='rgba(20,22,18,0.5)'; ctx.lineWidth=1; stroke? adds cost; use stroke only for big? Keep stroke cheap: skip helmet stroke; add tiny dark visor dot: fillStyle 'rgba(15,17,14,.6)'; arc r*0.16 at +ca*r*0.62. maybe skip for perf... 1000 extra arcs ok honestly. I'll include visor dot for character.
```
Order fix: shadow → pole/banner → sword → body → helmet. Sword behind body means body covers base — good.

Dead units skipped (they're stamped as decals). 

**Particles:**
```js
function spawnBlood(wx,wy,s,n){ project once: p, sc, sx,sy; for n: particles.push({t:0,x:sx+..,y:sy+..,vx:rand±*sc*60?...}) 
```
Speeds in px/s scaled by sc: blood: vx=(r±)*rand(30..120)*sc, vy similarly with vertical bias smaller; life 0.25-0.5; r0 sc*(0.8-1.6). color dark red variants.
dust: life 0.5-0.9, grows: r=sc*(2..4) growing ×(1+ (1-life/tl)*1.6), alpha 0.22*(life/tl), color 'rgba(120,110,88,A)' or palette dust.
smoke: life 1.6-2.6, r grows from sc*4 → *14, alpha 0.10→0, drift vx 6-14, vy -4? top-down: drift with wind +x. color gray 'rgba(70,72,66,a)'.
spark: bright small: life 0.12, color '#ffe9b0', fast.
Cap: if(particles.length>700) particles.splice(0, particles.length-700).

Update: p.life-=dt; kill ≤0 (swap-pop). x+=vx*dt; vx*=Math.pow(0.001? use vx*= (1-3*dt) friction for blood; dust slows; smoke constant drift + slight turbulence sin.

Draw: blood: fillRect small (faster) with color per particle precomputed string? Creating color strings per particle spawn ok (spawn rate bounded). Draw: ctx.fillRect(p.x-r/2, ..., r, r) with fillStyle set per particle — many state changes; group: blood particles all similar dark red — use single fillStyle 'rgba(96,16,16,0.85)' and vary via alpha? Simplify: fixed two colors alternating by index. Perf fine.

Dust: arc fill.

**Kill puff:** spawnBlood 8-12, dust 2, smoke maybe, stamp blood+corpse. Corpse stamp uses unit's facing angle randomized.

**Shake update:** shake=max(0, shake - dt*6); during melee with engagement>120 keep floor 0.5: shake=max(shake, engaged? ...) compute engaged count during update (units fighting). offset: ox=(Math.random()*2-1)*shake, oy=... apply translate.

**Main loop:**
```js
let last=performance.now();
function frame(now){
 requestAnimationFrame(frame);
 let dt=(now-last)/1000; last=now; if(dt>0.05)dt=0.05; if(dt<=0)return? 
 tG+=dt; // global anim time
 if(state!=='idle'){ step(dt); render(); }
}
```
step: phase transitions + unit updates + particles + shake + HUD.

Ordering inside step:
```
// intro→advance
if(phase==='intro' && t>1.0){ phase='advance'; setPhase('The armies advance across the field'); }
// centroids
rebuild grid; 
let sums... loop units: if alive: sumX[side]+=x ... count
cx0=..., etc. gap=|cx0-cx1|;
if(!a0.charging && gap<380) a0.charging=true; same a1; if(phase==='advance'&&a0.charging&&a1.charging){phase='charge'; setPhase('The drums beat — the lines charge!');}
// unit loop (uses grid)
// after: rout checks & victory & phase melee timing
```

Unit update function detail — let me write it:

```js
function step(dt){
 t+=dt;
 if(phase==='intro'&&t>1.05){phase='advance';setPhase('The armies advance across the field');}
 // grid
 head.fill(-1);
 const n=units.length;
 for(let i=0;i<n;i++){const u=units[i]; if(!u.alive)continue; let c=cellOf(u.x,u.y); nxt[i]=head[c]; head[c]=i;}
 // centroids
 let s0x=0,s0y=0,c0=0,s1x=0,s1y=0,c1=0;
 for(...alive){ if(u.side){s1x+=u.x;s1y+=u.y;c1++;} else {...} }
 const ecx0=c0? s0x/c0: (armies[0].side? Ww:0)... just guard.
 armies[0].cx=c0?s0x/c0:0; etc.
 const gap=Math.abs(armies[0].cx-armies[1].cx);
 if(t>3){ if(!armies[0].charging&&gap<400)armies[0].charging=true; ...}
 if(phase==='advance'&&armies[0].charging&&armies[1].charging){phase='charge';setPhase('The drums beat — the lines charge!');}
 
 engaged=0;
 for(let i=0;i<n;i++){
   const u=units[i]; if(!u.alive) continue;
   // sense neighbors
   let nd2=1e9, ne=-1, spx=0, spy=0;
   const cx=(u.x/CS)|0 clamped, cy=...;
   for(let gy=max(0,cy-1); gy<=min(GH-1,cy+1); gy++)
    for(let gx=max(0,cx-1); gx<=min(GW-1,cx+1); gx++){
      for(let j=head[gy*GW+gx]; j!==-1; j=nxt[j]){
        if(j===i)continue; const v=units[j]; if(!v.alive)continue;
        const dx=v.x-u.x, dy=v.y-u.y, d2=dx*dx+dy*dy;
        if(d2<SEP2 && d2>0.0001){ const d=Math.sqrt(d2), f=1-d/SEP; spx-=dx/d*f; spy-=dy/d*f; }
        if(v.side!==u.side && d2<nd2){ nd2=d2; ne=j; }
      }
    }
   // targeting
   if(!u.flee){
     let cur=u.tgt;
     const curOK = cur && cur.alive;
     if(ne>=0){
       const cand=units[ne];
       if(!curOK) u.tgt=cand;
       else { const cdx=cur.x-u.x, cdy=cur.y-u.y; const cd2=cdx*cdx+cdy*cdy;
         if(nd2 < cd2*0.6 || cd2 > 3600) u.tgt=cand; }
     } else if(curOK){ const cdx..; if(cd2>4900) u.tgt=null; } else u.tgt=null;
   }
   // behavior
   let mvx=0,mvy=0, spd=u.spd, face=null;
   if(u.flee){
     if(u.fl>0){ u.fl-=dt; spd=0; } else spd=u.spd*2.3;
     mvx=(u.side?-1:1)... red side0 home left: dirx = u.side===0? -1: 1; wait side0=red left → flee left: dirx=-1; side1 → +1. dirx = u.side? 1 : -1; blue right side1 → flee right +1 ✓ (side0 falsy → -1 ✓).
     mvy=Math.sin(t*2.1+u.sw)*0.35;
     face=Math.atan2(mvy,mvx);
     if((u.side===0&&u.x<-22)||(u.side===1&&u.x>Ww+22)){ u.alive=false; armies[u.side].count--; routed++; continue; }
   } else {
     const tg=u.tgt;
     if(tg&&tg.alive){
       const dx=tg.x-u.x, dy=tg.y-u.y; const d=Math.sqrt(dx*dx+dy*dy)||0.001;
       if(d<FIGHT_R){ // fight
         engaged++;
         spd=0; face=Math.atan2(dy,dx);
         u.cd-=dt;
         if(u.cd<=0){
           u.cd=u.cds*(0.7+Math.random()*0.7);
           u.swing=1;
           const rage=1+Math.max(0,t-20)*0.05;
           hurt(tg, u.dmg*rage, u);
         }
       } else { mvx=dx/d; mvy=dy/d; spd=u.spd*(armies[u.side].charging?1.75:1.12); }
     } else {
       // advance
       const ec=armies[1-u.side];
       let ax=ec.cx - u.x, ay=(u.y0 + Math.sin(u.sw)*6) - u.y; hmm ay: destination y = u.y0 (initial) blended: ay = (u.y0*0.8 + ec.cy*0.2) - u.y;
       const d=Math.hypot(ax,ay)||1; mvx=ax/d; mvy=ay/d; spd=u.spd*(armies[u.side].charging?1.75:1.12);
       // wobble
       const w=Math.sin(t*2.6+u.sw)*0.18; const cA=Math.cos(w), sA=Math.sin(w); const nx=mvx*cA-mvy*sA, ny=mvx*sA+mvy*cA; mvx=nx;mvy=ny;
     }
   }
   // separation
   mvx+=spx*1.35; mvy+=spy*1.35;
   // integrate
   if(spd>0||sp||...){ u.x+=mvx*spd*dt; u.y+=mvy*spd*dt; }
   clamp y: if(u.y<18)u.y=18; if(u.y>Hw-18)u.y=Hw-18; x clamp [-26, Ww+26] for non-flee.
   // heading
   let ta = face!==null? face : (spd>0? Math.atan2(mvy,mvx): u.a);
   let da=ta-u.a; wrap to [-π,π]; u.a+=da*Math.min(1,dt*(face!==null?14:6));
   // swing cooldown visual
   if(u.swing>0)u.swing=Math.max(0,u.swing-dt*5.5);
 }
 engagedG=engaged;
 shake=Math.max(0,shake-dt*7);
 if(engaged>140) shake=Math.max(shake,0.5);
 // particles update
 ...
 // rout/victory checks (only when state==='battle' i.e., not intro)
 if(phase!=='intro'&&phase!=='end'){
   const A=armies[0],B=armies[1];
   // fighting counts recompute: count alive && !flee per side:
   ... compute in the loop above (f0,f1 counters).
   if(!A.broken&&!B.broken){
     if(t>40){ breakArmy(A.count<=B.count?A:B); }
     else if(A.count>0&&B.count>0){
       if(A.count<B.count*0.34)breakArmy(A);
       else if(B.count<A.count*0.34)breakArmy(B);
     }
   }
   if(f0===0||f1===0){
     let w; if(f0===0&&f1===0){ w = A.count>B.count?0:(B.count>A.count?1:-1);} else w=f1===0?0:1;
     endBattle(w);
   }
 }
 // melee flavor
 if(phase==='melee'&&t-lastFlavor>9){lastFlavor=t; setPhase(pick(MELEE_LINES));}
 if(phase==='clash'&&t-clashT>7){phase='melee';lastFlavor=t;setPhase(pick(MELEE_LINES));}
}
```

Careful: breakArmy triggers phase message; also once broken, army's units flee → fighting count drops → victory triggers when f(broken side)==0. But note: broken army's units may still be engaged until fl expires — they stop fighting immediately? A broken unit mid-combat: flee branch handles (ignores tgt) — with fl delay they keep fighting up to 1.5s. OK.

hurt(v,dmg,by):
```
if(!v.alive)return;
v.hp-=dmg;
spawnBloodHit(v.x,v.y, 2+ (dmg>20?2:0));
if(v.hp<=0) killUnit(v);
```
killUnit(v):
```
if(!v.alive)return; v.alive=false; const a=armies[v.side]; a.count--; fallen++;
stampBlood(v.x,v.y, bloodS(4.5..), seed);
stampCorpse(v.x+rand jitter, v.y+.., angle=u.a+rand0.4, v.deadCol, seed);
spawnDeathFx(v);
```
Death fx: blood n=9, dust 2-3, smoke if rnd<0.4.

spawnBlood(worldX, worldY, count, power): precompute sc at that world pos, particles px = proj coords, velocities px/s = dir*rand*sc*K.

Particle struct: {x,y,vx,vy,l,tl,ty,r, c?} ty: 0 blood,1 dust,2 smoke,3 spark.
Update:
```
for i from end: p.l-=dt; if<=0 swap-pop;
 p.x+=p.vx*dt; p.y+=p.vy*dt;
 if ty0: p.vx*=f1; p.vy*=f1 (f=Math.exp(-6dt)≈1-3dt)
 if ty1: slow: *=1-2.5dt; p.r+=dt*sc? store growth.
 if ty2: drift: vx small const + sin wobble; r+=dt*rate.
```
Draw:
```
blood: ctx.fillStyle='rgba(105,16,16,0.9)'... vary: p.c stored string at spawn: pick from 3 reds. fillRect(p.x-r/2,...,r,r) — squares rotated? tiny squares fine at 1-3px. Hmm "no plain small squares as particles" — that guidance was for 3D particle systems; still, blood as tiny circles looks better: use fillRect for perf but at r≤2.5px circles vs squares indistinguishable... I'd rather draw blood as small circles via arc — 1000 arcs extra maybe fine since particles bounded (~300). Use arcs for all: blood arc, dust arc (2 layered), smoke arc, spark arc.
```
Blood should also leave micro-stains: each blood particle on death of its life stamps a tiny dark dot into decal with prob 0.3 — extra flavor; cheap. Do: when blood particle expires, 25% chance stamp tiny blob via direct dctx draw (not full stamp list — but then resize loses them; acceptable? redrawStamps won't restore micro dots — minor inconsistency, acceptable... Actually simpler: skip micro stamps; initial blood stamp already covers.)

**HUD setHudNames:** nameL.textContent = armies[0].name; chip colors; also title: overline `BATTLE ${roman(battleN)}`; titleEl `The Battle of ${place}`; Also versus line? Put names in counters.

Also counter sub-label: "on the field". Bar fill: armies[i].count/initial.

**Roman numerals:** function roman(n) standard up to 3999.

**Verdict sub:** `${count} remain on the field · ${fallen} fell · ${fmt(t)} elapsed`.

**Fader CSS:** #fader {position:fixed;inset:0;background:#08090b;opacity:1;transition:opacity .9s ease; pointer-events:none} start opacity 1 → on load newBattle then remove... Initial page load: fader starts at 1 (black), newBattle() builds, then rAF remove 'on'? Manage: fader has class 'on' meaning opacity 1. Initial markup class="on". After first build, remove → fade in. 

TitleWrap show animation: css .title-wrap {opacity:0; transform:translateY(-6px); transition: opacity .8s ease, transform .8s ease} .show{opacity:1;transform:none}. Retrigger per battle: remove class, force reflow, add.

Verdict: similar with scale? subtle: opacity + letter-spacing animation (letter-spacing animates expensively; use transform none). Fine: fade+rise.

**Text shadow for legibility.**

**Counters positioning:** top-left / top-right with padding; on small screens stack? Media query: reduce title size. Keep simple responsive via clamp().

Edge: phase text under title centered; counters left/right — could overlap title on narrow screens; title top-center with max-width; acceptable.

**Now let me also double check "fighting" counters and count semantics:** army.count = alive (incl. fleeing). bar = count/initial — shows shrinking including routing drain. Tally "routed" increments at despawn. Also show "routed" count includes fled. Good.

**Potential issue — units clumping into one blob during melee:** separation strength: SEP radius 8.5 (SEP2=72), f=1-d/SEP linear, push multiplier 1.35, velocities px/s in world units: max push ~1.35 per unit overlapping → times spd? No — separation added to *direction* vector then multiplied by spd. mv = dir*spd + sep*1.35 then *spd*dt? In my integrate: `u.x += mvx*spd*dt` — separation added to mvx which is then multiplied by spd — wrong scale: separation should be velocity in world units/s. Fix: compute vel = dir*spd + sep*SEPVEL (SEPVEL≈34 world/s). Then u.x+=velx*dt. Let me restructure:

```
let vx=mvx*spd, vy=mvy*spd; // if spd>0
vx+=spx*34; vy+=spy*34;
u.x+=vx*dt; u.y+=vy*dt;
heading from (vx,vy) if speed.
```
When fighting (spd=0): still separation applies → jostling ✓. Cap vel magnitude ~ spd*1.6+40? fine without cap; sep bounded by neighbors count... dense pile could jitter; f capped at 1 each neighbor, many neighbors → strong push, but symmetric-ish; add clamp: sepMag cap 1.6.

Also avoid units sinking into each other when fighting: attack range 11.5 > sep distance 8.5 — they stop at range but separation pushes apart beyond range → oscillation: unit stops to fight at d=11, sep pushes away to d>11.5 → moves again... Combat stop condition: d<FIGHT_R where FIGHT_R=13.5 with sep radius 8.5 → max sep displacement keeps d maybe <13.5 if started at 12? Two fighting units both pushed apart — they'd drift apart and chase loop. Mitigation: fighting units get reduced separation from their current target only, or reduce separation strength when engaged (×0.35). Also ranged stop: chase until d<12; fight while d<14 (hysteresis). Implement: if(u.engaged boolean persist): enter when d<12, exit when d>15.

Simplify: 
```
const d = dist to tgt;
if(u.fight){ if(d>15||!tg.alive) u.fight=false; } else if(d<12) u.fight=true;
if(u.fight){ fight behavior; face tgt } else { move toward tgt }
```
Separation scale: global 30 for free movers; fighting units: 12 (light jostle). 

Also enemies pushing through each other: separation applies between enemies too (any unit) ✓ prevents overlap stacking.

**Advance lane wobble** may cause columns merging — separation handles.

**Charge trigger distance:** gap between centroids 400/1200 → but if formations 'line' (deep 143) front gap larger... trigger charging on centroid gap<430 to be safe. Also per-unit: they charge when army charging.

**Unit density on screen near clash:** fine.

**Numbers for count display:** big serif numbers.

**One more consideration: first 30 seconds show: title (0-2s), advance (0-2.5s), charge (2.5-4s), clash (4-5s), melee grind (5-25s) with deaths & stains & smoke, rout (~22-30s), victory banner.** I'm fairly confident battles end 22-32s with the rage ramp and 0.34 threshold. Let me maybe strengthen: dmg base 16+rand*10 (avg 21), hp 85+rand*25 (avg 97) → 4.5 hits; cd avg 0.42+0.12=0.54*randavg(1.05)≈0.57 → kill ~2.5s 1v1. Rage ramp from t=18: +5%/s → by 25s +35%. Rout threshold 0.34 typically hit ~18-26s. Mop-up ~2-4s. Victory ~20-30s. 

Let me also double-check the melee death-rate intuitively: initial clash front width ~26-46 units per side; behind-ranks press forward; fight radius 12-15 means roughly a band ~3 deep engages per side → ~80-140 engaged/side at peak; each kills a target every ~2.5s → deaths/s ≈ 2*120/2.5 ≈ 96/s?? That'd end in ~10s — too fast? Hmm, but engagement saturates: as one side thins, attackers outnumber → death rate of losing side spikes, winning side losses drop → snowball to rout quickly. Battles might end ~14-20s. That's still within 30s window ✓ (better safe than sorry). But too-fast feels rushed? 1000 units dying in 15s = epic-scale carnage — acceptable and dramatic. But I also want the charge phase readable. Contact at ~4s, carnage peak 5-14s, rout ~15-22s. OK — good for recording window. I could also slightly reduce dmg (14+rand*8, avg 18, hp 90+30 → 5.5 hits → duel 3s) → end ~18-26s. Let me use dmg 15+r*9, hp 88+r*30, cd 0.5+r*0.25 → kill ≈ (103/19.5)≈5.3 hits ×0.62s ≈ 3.3s per duel. Death rate ~70/s peak → end ~18-24s. Fine.

Hmm, but also many duels are 1v2, 1v3 → faster. Whatever — range 16-26s likely. 

**Rout chase behavior issue:** when loser breaks, winner units currently fighting corpses... they retarget nearest enemy (fleeing). Fleeing units run at 2.3×spd ≈ 130 u/s; chasers at 1.75×spd ≈ 100 — can't catch healthy runner; but runners start from melee center with 1.5s staggered delays, chasers adjacent → initial contact kills many; rest escape → counts drain as they despawn at edge. Meanwhile victory triggers when f_loser==0 — could be quick (~1.5s after break) → celebration while stragglers flee — good.

But wait: victory triggers on f_loser===0 — however chasers still have tgt refs to despawned units — handled by alive checks.

Also make some runners get cut down: chasers faster? Set chase speed: if enemy.flee → attacker speed ×2.0 (they hunt). Runners 2.3× — nearly equal; catches happen via variance and cornering at edge. Actually simpler: runners 2.0×, chasers vs fleeing 1.9× with per-unit variance → some caught. And runners despawn at edge regardless. Deaths during rout add drama ✓.

**Smoke drift:** wind +x slight.

**Blood color on ground:** deep maroon; on dark olive bg reads well.

**Dust color:** use palette-tinted dust: store palette dust rgb.

**Now HUD & CSS specifics.**

Palette (UI): ink #e9e4d4 (parchment), shadows. Faction colors for HUD accents: red #c04437? and blue #6b93c4? Derived from unit hues but lighter for text: red text accent #d4574a, blue #7fa8d8. Chips: small squares 8×8 rotated 45°? Just colored square inline-block.

Title serif stack: `Georgia, 'Times New Roman', 'Palatino Linotype', serif`.

CSS:

```css
:root{ --ink:#e9e4d4; }
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%;overflow:hidden;background:#0a0b09}
canvas#scene{position:fixed;inset:0;display:block}
#hud{position:fixed;inset:0;pointer-events:none;font-family:Georgia,'Times New Roman',serif;color:var(--ink)}
.hud-shadow{text-shadow:0 1px 2px rgba(0,0,0,.75),0 0 14px rgba(0,0,0,.45)}
#titleWrap{position:absolute;top:18px;left:50%;transform:translateX(-50%);text-align:center;opacity:0;transition:opacity .9s ease .15s, ...}
#titleWrap.show{opacity:1}
#overline{font-size:11px;letter-spacing:.42em;text-transform:uppercase;opacity:.72; margin-bottom:6px}
#title{font-size:clamp(22px,3.6vw,40px);font-weight:700;letter-spacing:.02em;line-height:1.05}
#titleRule: small ornament? A thin line with diamond: use pseudo elements: hr-like div width 120px height1 bg rgba ink .4 margin 8 auto. plus phase below.
#phase{font-style:italic;font-size:clamp(12px,1.4vw,15px);opacity:.85;margin-top:7px;min-height:1.2em}
.army{position:absolute;top:20px;width:172px}
#armyL{left:22px;text-align:left} #armyR{right:22px;text-align:right}
.aname{font-size:11px;letter-spacing:.14em;text-transform:uppercase;opacity:.9; display:flex; align-items:center; gap:8px}
#armyR .aname{justify-content:flex-end}
.chip{width:9px;height:9px;flex:none;transform:rotate(45deg);display:inline-block}
.acount{font-size:clamp(26px,3vw,36px);font-weight:700;margin-top:2px;font-variant-numeric:tabular-nums}
.abar{height:3px;background:rgba(233,228,212,.18);margin-top:6px;position:relative;overflow:hidden}
.abar i{position:absolute;left:0;top:0;bottom:0;display:block}
#armyR .abar i{left:auto;right:0}
.asub{font-size:10px;letter-spacing:.2em;text-transform:uppercase;opacity:.5;margin-top:5px}
#tally{position:absolute;bottom:14px;left:50%;transform:translateX(-50%);font-size:11px;letter-spacing:.24em;text-transform:uppercase;opacity:.6}
#verdict{position:absolute;left:50%;top:38%;transform:translate(-50%,-50%);text-align:center;opacity:0;transition:opacity .8s ease;}
#verdict.show{opacity:1}
.vover{font-size:13px;letter-spacing:.55em;text-transform:uppercase;opacity:.8; margin-bottom:10px}
#vName{font-size:clamp(30px,5vw,54px);font-weight:700}
#vSub{font-size:13px;font-style:italic;opacity:.85;margin-top:10px}
#fader{position:fixed;inset:0;background:#07080a;opacity:0;transition:opacity .9s ease;pointer-events:none}
#fader.on{opacity:1}
```

Hmm verdict at top 38% might overlap title — title at top ~90px tall; verdict at 38% of VH — for VH 800 → 304px — fine.

Verdict should probably appear lower-center-left? Center is dramatic — ok, but avoid clash with title: place at 42%? fine.

Also chips colored dynamically via js.

**Tally element** update.

Now — writing render():

```js
function render(){
 const ox=(Math.random()*2-1)*shake, oy=(Math.random()*2-1)*shake;
 ctx.setTransform(DPR,0,0,DPR,0,0); wait resize sets transform each frame? Just re-set at frame start: ctx.setTransform(DPR,0,0,DPR,ox*DPR? — translate in css px: setTransform(DPR,0,0,DPR,0,0) then ctx.translate(ox,oy).
 ctx.clearRect? Not needed since bg drawn fully opaque covering entire canvas (sky+field strips cover all? Strips cover only trapezoid+sides via 3 tiles; sky covers top; sides beyond tiles: tiles drawn at dx±dw — for near rows dw>VW so covered; far rows: 3 tiles cover 3*dw ≥ 0.56*3=1.68VW ✓ covered). But shake translate shifts → edges exposed! Draw bg with slight overscan: draw bgC at (-8,-8, VW+16, VH+16)? Scaling blur... simpler: clear with base dark color first: ctx.fillStyle='#101208'; fillRect(-20,-20,VW+40,VH+40) before bg? With translate, fill rect oversized covers. Or just draw bg image with drawImage(bgC, -ox? ...). Easiest: after translate, fillRect(-30,-30,VW+60,VH+60) with dark base, then drawImage(bgC,0,0,VW,VH). Exposure edges show dark — acceptable (vignette hides). ✓
 // decals
 ctx.drawImage(dcC,0,0,VW,VH);
 // smoke particles pass
 // units: build sorted list
 drawList.length=0; for alive push; sort (a,b)=>a.y-b.y; draw each.
 // particles others
 // restore
 ctx.drawImage(ovC,0,0,VW,VH) — after resetting transform to setTransform(DPR...) without translate.
}
```

Smoke before units: draw smoke pass before drawList. Blood after. OK two passes over particle array filtered by type.

**drawList sorting allocation:** reuse array.

**Cell coordinate clamp helper inline.**

**Performance check on sense loop:** neighbor iteration: for each unit iterate up to 9 cells × avg density. During melee, density ~ (1000 units)/(region maybe 500×300 → cells 10×6=60) → ~17/cell → 9 cells ≈ 150 checks × 1000 = 150k inner iterations/frame. Each ~10 ops → 1.5M ops — fine at 60fps.

**Now stamps cap:** stamps max 1200; each battle fresh.

**redrawStamps on resize** — iterate stamps drawStamp.

Also note: stamp drawing uses seeded rng per stamp — need mulberry32.

**Flag stamp:** small: pole line + colored pennant.

**Write stamp functions:**

```js
function mulberry32(a){return function(){a|=0;a=a+0x6D2B79F5|0;var t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}}
```

drawStamp(g,s):
```js
const p=s.y/Hw, sc=scaleAt(p), sx=VW*0.5+(s.x-Ww*0.5)*sc, sy=topY+Math.pow(p,PEXP)*depth;
const R=s.s*sc; // s.s = world radius base ~5
const rng=mulberry32(s.sd);
if(s.k===0){ // blood
 for(let i=0;i<8;i++){
   const a=rng()*TAU, rr=rng(); const bx=sx+Math.cos(a)*R*1.7*rr, by=sy+Math.sin(a)*R*1.1*rr;
   const br=R*(0.28+rng()*0.5);
   g.fillStyle = i? `rgba(${64+rng()*30|0},${8+rng()*8|0},${10+rng()*8|0},${0.42+rng()*0.3})` : 'rgba(46,6,8,0.6)';
   g.beginPath(); g.ellipse(bx,by,br,br*(0.6+rng()*0.4),rng()*3,0,TAU); g.fill();
 }
 // specks
 for(let i=0;i<5;i++){...small}
}else if(s.k===1){ // corpse
 g.save(); g.translate(sx,sy); g.rotate(s.ang);
 g.fillStyle=s.col; // deadCol hsla
 g.beginPath(); g.ellipse(0,0,R*1.35,R*0.62,0,0,TAU); g.fill();
 // helmet
 g.fillStyle='rgba(120,124,120,0.8)'; g.beginPath(); g.arc(R*1.05,0,R*0.42,0,TAU); g.fill();
 // weapon
 g.strokeStyle='rgba(28,30,26,0.7)'; g.lineWidth=Math.max(1,R*0.16); g.beginPath(); g.moveTo(-R*0.4,R*0.5); g.lineTo(R*1.6,R*0.9); g.stroke();
 g.restore();
}else{ // flag dropped
 g.save(); g.translate(sx,sy); g.rotate(s.ang);
 pole: stroke line (-R*1.4,0)-(R*1.6,0.2R) color '#8a8272';
 flag blob: fill s.col ellipse at (R*1.1, -R*0.1) rx R*0.8 ry R*0.45;
 g.restore();
}
```
corpse col stored as string at stamp time.

Note: stamps drawn onto dcC which is cleared/redrawn only on resize; during battle stamps accumulate by drawing directly to dcX as events happen — must also draw onto dcX immediately: drawStamp(dcX, s). ✓

**Blood stain under corpse order:** call stampBlood then stampCorpse. ✓

**Unit hp regen? no.**

**Ambient details:** floating dust motes? skip. Birds? skip. 

**Signature moment:** the charge→clash with shake + accumulating corpses/stains + banner bearers + rout with fleeing stream + victory hop. Good.

**Title text per battle:** also show army names facing: counters show names.

Let me also add subtle **battle scars pre-battle**: none (fresh field each time).

**Accessibility/meta:** title tag "Field of Crowns — Mass Battle Simulation".

Now write out the entire file, carefully. I'll aim for clean, well-commented code. Let me write final code with attention to syntax correctness.

Also: `ellipse` support assumed fine.

One more detail: counters bar fill colors set via style background at battle start; chips too. Winner name color in verdict: set style.color.

Let me handle `phase` variable name clash with DOM el phaseEl — fine.

Text for counters: cntL/cntR numbers; update when changed.

Elapsed format: m:ss.

Let me now think about `step()` ordering for intro: during intro, units shouldn't move: gate movement with phase==='intro' → spd=0 (but idle sway). Simply: in movement, if(phase==='intro') spd=0 (unless...). And hold: no separate hold needed — intro covers 1.05s.

Also during 'victory' state: fighting stops? Winner units: tgt may be despawned → advance branch moves them toward enemy centroid (which is dead army's last centroid?) — enemy centroid of empty army → guard: if enemy has no alive units, winners stop: in advance branch: if enemy count===0 → celebrate idle (spd=0). Set phase 'end' → in endBattle set all winner units celeb=true; their movement: if(phase==='end') spd=0 with slight shuffle. Let me set state flag `over=true` and in unit update: if(over && !u.flee){ spd=0; } — they stand & hop (draw). Also their tgt cleared.

Also after end, keep particles/stamps rendering; loser stragglers keep fleeing (flee branch unaffected by over) ✓ — they despawn, counts drop, tally updates — nice.

Also winner count during victory: constant (no more fighting; unless loser... none left fighting). Runner deaths still possible if chaser adjacent at end moment — fine, minor.

**Also f0/f1 counting:** compute in update loop: after processing unit: if(u.alive&&!u.flee) f[u.side]++.

**Victory condition check placement:** after loop each frame while phase!=='intro' && !over.

Wait — also possible both armies never meet? They always charge. Fine.

**Also ensure rout threshold doesn't trigger during intro** — counts equal; fine.

**Kill during fight: attacker's tgt dead → next frame retarget.** ✓

**Swing trigger on attack** ✓ (u.swing=1 set when attacking).

**Sound:** none.

Now, particles budget: deaths/sec up to ~80 × (blood 9 + dust 2 + smoke .4) ≈ 1000 particles/s spawn, lifetime ~0.4s → ~400 concurrent — cap 800 ok.

Blood particle speeds: sc-scaled: v = (rand 40..140)*sc px/s in random dir, slight downward bias? top-down: random dir fine, damp fast.

Dust: v small 10-40*sc, r grows, alpha decays.

Smoke: vy: -6 (drift "up" screen? top-down smoke just spreads) — do slow radial drift + wind: vx 8..20, vy -4..4; alpha 0.08 start decay; radius grows sc*6→sc*18. Draw with 'rgba(60,62,58,alpha)'.

Also big initial clash: spawn a dust wave along front? On first clash, spawn 60 dust puffs along the line — dramatic! Do when firstClash triggers: sample units engaged? Simple: 50 dust puffs at random positions near centroid line between armies (x midpoint, y random around centroid y ±120) — great "impact" moment + shake. ✓

Also on charge phase maybe drum? no audio.

**HUD number formatting:** plain.

Now write everything. I'll be careful with typos.

Also `pick(arr)`.

PALETTES:
```js
const PALETTES=[
 {name:'moor', h:88,s:17,l:20, dust:'122,112,86'},
 {name:'steppe',h:66,s:20,l:26, dust:'138,124,88'},
 {name:'heath',h:140,s:12,l:16, dust:'96,104,88'},
 {name:'ash', h:48,s:10,l:24, dust:'140,130,104'},
];
```
Ground texture uses h,s,l with variations ±. Field base maybe l-2..l+8 blobs.

Sky/hills fixed tones.

**groundTex generation:**
```js
texC width TW=720 height TH=405 (scale 0.45).
tx.fillStyle=hsl(h,s,l-2); fillRect;
// patches: 90: radial? Use simple circles alpha low:
for i<90: x,y,r=20+rnd*70; tx.fillStyle=`hsla(${h+(-14+rnd*28)},${s}%,${l+(-7+rnd*14)}%,0.13)`; ellipse fill.
// streaks: 40 long thin darker horizontal-ish lines alpha .06 (field plough lines!) — plough lines add realism: for i<26: y row bands? Actually plough lines run along world x: for y=... draw faint horizontal strokes every ~30px alt alpha — subtle. I'll add gentle horizontal banding: for band every 24px: fillRect(0,y,TW, 10) alpha 0.03 dark/light alternating — simulates field strips.
// speckle: 4200 dots 1px: hsl lighter/darker alpha .12-.3
// a few light dry patches etc.
```

**buildBackground details:** 

Sky: linear gradient. Also pale sun glow: radialGradient centered (VW*0.5, topY) radius VW*0.42: 'rgba(236,222,188,0.16)' → 0 — subtle warm haze. fill top area.

Hills: two silhouette layers via path: y = base + sin noise. Colors: far '#77725f' with alpha .8? Let me: far hills fill '#6f6a5e'; near treeline '#3f4438'. Both slightly transparent? Solid fine given haze overlay afterwards.

Treeline bumpy: for x step 6: y=topY-2 - (noise) small arcs? Simple: path with quadratic bumps: build via sin combos.

Order: sky → sun glow → far hills → treeline → field strips → haze band → features (rocks/trees/craters) → done. Haze band after strips: linear from (topY) rgba(160,155,135,0.28) → transparent at topY+VH*0.30 — also cover hills bottom? Hills above topY unaffected... haze should also slightly cover treeline base: start gradient at topY*0.7.

Field strips start exactly at topY (p=0 → sy=topY). Above topY: hills. There might be tiny gap due to pow curve: strip 0 covers sy0=topY ✓.

Features: 
```js
function w2s(x,y){const p=y/Hw,sc=scaleAt(p);return [VW*0.5+(x-Ww*0.5)*sc, topY+Math.pow(p,PEXP)*depth, sc];}
rocks 30: [x,y,sc]: shadow ellipse offset, stone: fill '#7d7a6d' shade vary, ellipse rotated, highlight top-left arc lighter.
craters 3: at random center field: ellipse rx=sc*55..85, ry=rx*0.55, fill darker palette alpha .35, rim highlight arc lighter alpha .12, inner darker.
tufts: 160: 2-3 strokes 2-4px length dark-light green alpha .3 — at 1px width lines.
trees 5: near top area (y<170) or sides x<120|x>1480: trunk: dark line up (screen -y) length 12*sc? Trees seen from above at slight angle: draw canopy blobs + tiny trunk base + long shadow east. blob: 3 overlapping circles '#2f3526' vary. shadow: ellipse offset +.
```
Keep muted so units pop.

Wait — features should be *under* units but they're baked into bg ✓. But trees baked could get walked over by units (they walk "through" tree canopy visually — tree at edges, minor. Place trees at |x-800|>620 edges and far top so rarely overlapped; routed flee along edges may pass under canopies — acceptable minor artifact, or just avoid x edges within flee band? Fleeing runs to x=±26 at their y (varied y). Trees at corners mostly. Fine.

**Decal blood color:** fixed dark maroon independent of palette ✓.

**Counts bar init:** width 100%.

**Verdict chip?** vName colored with winner accent.

Let me now also decide **unit speed vs world scale sanity:** spd 54-70 u/s; spacing 10.5 → units move ~6 body lengths/s — lively. Charging 1.75× ≈ 105-122. dt-based ✓.

**Attack range 12, fight hysteresis 15.** Separation radius 8.5, world sep strength 34, fighting sep 12.

Let me now think about how the melee actually spreads: front units lock; behind units advance toward tgt (front enemy) but blocked by separation of allies ahead → they pile behind → lateral spread as separation pushes sideways → line bulges, wraps. Outer units path around (their tgt is frontal; but nearest-enemy switching when closer enemy appears lateral → flank wrap). Should look organic enough.

One risk: rear units pushing forward squeeze front line into enemy → overlap through enemy lines since separation includes enemies (d2<72 pushes) → front stays coherent-ish. OK.

**Improve chaos:** per-unit aggression: some units (10%) "daring": move at 1.15 speed and target nearest regardless (they penetrate) → creates breakthrough pockets. Add u.bold=rnd<0.12 → speed×1.15 and fight enter range 13. Subtle.

**Centroid targeting when no tgt:** dest x = enemy centroid x → all units converge to centroid → they funnel toward center of enemy mass — during advance that's fine (head-on). After rout: winners with no alive enemies: enemy cx stale? If c1===0, set armies[1].cx stays last value; but over=true stops movement anyway. Before over, during mop-up, enemies alive (fleeing) → tgt set (they're enemies found in sense; fleeing units ARE sensed). Chasing: attacker targets fleeing unit ✓. If none in sense range → advance toward enemy centroid (fleeing mass centroid — moving toward their escape edge ✓ pursuit!). Since fleeing centroid moves toward edge, chasers follow — nice.

Enemy centroid compute includes fleeing units ✓.

**HUD update cadence:** every frame check count changed → update textContent; bar widths too.

**Timer:** t (battle time) displayed mm:ss.

Now, writing the final HTML. Let me carefully produce the code, keeping everything consistent. I'll write it in one go with care about every referenced variable.

Also remember: no emoji anywhere; icons not needed. Comments in English (user request in English).

Also the intro title should perhaps include subtitle with both army names — counters cover that.

Let me define global variables:

```js
let units=[], particles=[], stamps=[];
let armies=[null,null];
let state='boot', phase='intro', t=0, tG=0, vt=0, shake=0, battleN=0;
let fallen=0, routed=0, engaged=0, firstClash=false, clashT=0, lastFlavor=0;
let winner=-1, over=false, palette=PALETTES[0];
let lastCnt=[-1,-1];
```

Careful: name shadowing `state` etc fine.

DOM ids: scene, hud, armyL, armyR, nameL, nameR, chipL, chipR, cntL, cntR, barL, barR, overline, title, phase, tally, verdict, vOver, vName, vSub, fader, titleWrap.

Counters markup:

```html
<div class="army hud-shadow" id="armyL">
  <div class="aname"><span class="chip" id="chipL"></span><span id="nameL"></span></div>
  <div class="acount" id="cntL">0</div>
  <div class="abar"><i id="barL"></i></div>
  <div class="asub">on the field</div>
</div>
```
mirror for right.

**Fonts:** Georgia primary — it's a system serif, allowed (restriction was on Inter/Roboto/Arial/system-ui as primary identity; Georgia is fine and fits the chronicle style).

Now — writing out. I'll go section by section.

Also, drawUnits: iterate sorted list; but stamping dead handled in killUnit. Sorted list built each frame from alive units.

Let me make sure the unit 'a' heading initial: red faces +x (a=0), blue faces -x (a=π).

Sword rest angle a + w*1.15: for red facing right, sword held on side — fine.

Also draw subtle unit outline dark: stroke colD with lineWidth r*0.25 — since colD darker.

Helmet: color light gray-beige '#b7b3a4'? faction-neutral leather/steel: use '#a8a79b' vary. Precompute per unit: u.hc = hsl(45, 12%, L) L 55-70 — leather/steel mix.

Weapon color '#c9cbc4'.

Victory: some kneel? skip.

**Also banner flag color:** brighter faction: flagCol = hsl(hue, sat+12, 55). Precompute on unit (u.fcol).

Let me handle **celeb drawing**: sword raised: ang = -PI/2 + w*0.3 + sway. Bounce hop. Also flag wave amplitude bigger when celeb.

**Performance:** drawing flags with quadratic curves per bearer — only 6 bearers ✓.

**Write killUnit spawn positions** in world → convert inside spawn functions.

spawnBlood(wx,wy,n,pw) where pw=power scale:
```js
const p=wy/Hw, sc=scaleAt(p), sx=..., sy=...;
for(n){ const a=Math.random()*TAU, sp=(30+Math.random()*110)*sc*(pw||1);
 particles.push({ty:0,x:sx+..., y:sy+..., vx:Math.cos(a)*sp, vy:Math.sin(a)*sp*0.7, l:0.25+Math.random()*0.3, tl:same, r:(0.9+Math.random()*1.4)*sc, });
}
```
Store l and tl for alpha fade: alpha=l/tl.

dust:
```js
{ty:1, vx small, vy small, l:0.5+rnd*0.5, r0: sc*(2+rnd*3), gr: sc*(6+rnd*8)}
```
draw r = r0 + (1-l/tl)*gr, alpha = 0.16*(l/tl)? dust fade linear.

smoke:
```js
{ty:2, vx:6+rnd*14 (px/s scaled sc), vy:(-4+rnd*8)*sc, l:1.6+rnd*1.2, r0:sc*(3+rnd*3), gr:sc*(10+rnd*8)}
alpha=0.11*(l/tl)
```

spark (metal flash on hit): {ty:3, l:0.1, r:1.2*sc, vx fast} — draw pale yellow. Maybe skip sparks; sword swing already animates. Add tiny white flash dot at target on hit: 1-2 particles type3. Cheap ✓.

Particle update:
```js
for(let i=particles.length-1;i>=0;i--){const p=particles[i]; p.l-=dt; if(p.l<=0){particles[i]=particles[particles.length-1];particles.pop();continue;}
 p.x+=p.vx*dt; p.y+=p.vy*dt;
 const f=1-3*dt... use p.vx*=k where k = p.ty===2?1:(1-2.8*dt) clamp>0.
}
```

Draw:
```js
ctx.save()? no.
for p: if ty2 continue (drawn earlier);
 if ty0: ctx.fillStyle='rgba(112,16,16,'+a... string concat per particle — 400/frame ok but GC churn; precompute 3 shades with fixed alpha? Alpha varies with life... Use globalAlpha: set ctx.globalAlpha=a; fillStyle from small palette array p.c index. Do:
 ctx.globalAlpha=a; ctx.fillStyle=p.c; arc...
reset globalAlpha=1 after loop.
```
Colors arrays: BLDC=['#7d1416','#5f0f12','#8f1b1a']; dust color per palette: pal.dust string 'rgba(r,g,b,'? store pal.dustRGB='122,112,86' → fillStyle=`rgba(${pal.dustRGB},1)` with globalAlpha.

smoke fillStyle 'rgb(64,66,60)'.

**Blood stamping at kill:** sizes: stamp s.s (world radius) = 5+rnd*3.

**Corpse:** ang = u.a + (rnd-0.5)*1.2; col=u.dcol.

**dcol:** hsla(h, s*0.5, 18+rnd*5, 0.85).

Now the DOM/CSS/JS full write-up. Also make sure `phaseEl` update uses animation API with fallback if not supported.

Also handle window blur → dt clamp ✓.

Let me also give **units slight elongation** oriented to heading? Body circle + helmet already directional. Fine.

**Battle name places:** 
['Ashvale','Blackmere','Wolford','Ravenhill','Stonewatch','Coldbrook','Thornfield','Grimsmoor','Eagleford','Saltmere','Harrowgate','Duskwold','Redfern','Caelmarsh','Fennwick','Ironholt'].

Battle title variants: `The Battle of X` / `The Field of X` / `The Siege of X`? Siege doesn't fit. Use "The Battle of X" mostly, sometimes "The Field of X" or "The Raid on X"? Keep 'The Battle of' + occasionally 'The Field of'.

Overline: `BATTLE ${roman(battleN)} · ${year flavor}`? Add flavor season: 'The Dying of the Leaf'? Keep overline: `BATTLE ${roman}` simple. Maybe add "· ANNO 1147+" random? cute: year = 1090+battleN*3+rand? Eh — add: `BATTLE ${roman(battleN)} · ${['THE WET SEASON','THE HARVEST MOON','FIRST FROST','THE LONG DRY','LAMMAS TIDE']}` — flavor. Sure, small touch.

**Victory sub:** `${n} survivors · ${fallen} fallen · ${mm:ss}`.

**Draw phase:** also small helper setPhase(txt): phaseEl.textContent=txt; animate fade.

Melee flavor lines:
```js
const MELEE=[
 'No order remains — a savage melee',
 'The center buckles under the press',
 'Shields splinter, blades find gaps',
 'The ranks dissolve into a killing ground',
 'Steel flashes across the trampled grass'
];
```

Rout: `${loser.name} breaks and flees the field!`

Victory phase: `${winner.name} holds the field.`

Clash: 'The lines collide!'
Charge: 'The drums beat — the lines charge!'
Advance: 'The armies advance across the field.'
Intro: 'Two hosts draw up for battle.'

Now writing code — final. I'll be very careful with the unit loop and all closures.

About `armies[u.side].charging` when army null? fine.

Also `breakArmy` — set broken, assign fl delays, phase message, maybe drop banner? If bearer flees, banner still waves while fleeing — fine.

Kill of banner bearer → stampFlag with u.fcol.

**Draw sorting:** drawList array reused: const drawList=[]; each render: dl.length=0; push; sort.

Let me estimate render cost: per unit: 1 ellipse shadow, maybe banner (rare), sword stroke, body fill+stroke, helmet fill, visor fill, damage overlay (conditional) ≈ 6-7 ops × ~700 alive avg → 5k ops + 1000 sort. OK.

**Canvas text?** none in canvas — all HUD DOM. Good.

**Initial boot:** resize(); newBattle(); rAF. newBattle sets fader handling: initially fader.classList 'on' in HTML → after newBattle, requestAnimationFrame(()=>rAF(()=>fader.classList.remove('on'))) to ensure transition applies after paint. Use double rAF.

Actually newBattle is also called at battle end (fader already 'on'). Then we remove 'on' → fade from black. So inside newBattle: after rebuild, schedule removal:
```js
requestAnimationFrame(()=>{ requestAnimationFrame(()=>{ faderEl.classList.remove('on'); }); });
```
And titleWrap re-show: remove 'show', reflow, add — but transition delay ensures nice entrance. Do within newBattle directly:
```js
titleWrap.classList.remove('show'); void titleWrap.offsetWidth; setTimeout(()=>titleWrap.classList.add('show'), 250);
```
Verdict hide: verdict.classList.remove('show').

Hmm setTimeout fine.

**state transitions:** state used for 'victory' timing; I'll just use phase: phases: 'intro','advance','charge','clash','melee','rout','end'. In step: 
```
t+=dt;
if(phase==='end'){ vt+=dt; if(!fading && vt>5.2){fading=true; faderEl.classList.add('on');} if(fading && vt>6.4){ newBattle(); } }
```
newBattle resets vt=0, fading=false, phase='intro'.

Victory check occurs only when phase in advance..rout.

Careful: breakArmy sets phase='rout' — then clash→melee transition guard: only auto-advance melee flavor if phase==='melee' — after rout, phase stays rout; but melee flavor lines could continue? No — rout message stands. Victory overrides.

firstClash sets phase='clash' only if phase==='charge'||'advance' (safety).

Melee transition: if(phase==='clash' && t-clashT>7) → 'melee'.

**engaged counting** for rumble.

**HUD tally:** `${fallen} fallen · ${routed} routed · ${fmt(t)}` update every frame cheap if changed string. Compose only when second changes: keep lastSec.

Now let me also double check projection constant: pw=VW*0.985/Ww. At VW=1600 → pw=0.985. Unit r=3.5 world → px r=3.5*sc, sc=(0.6..1.07)*0.985 → at mid p=.5: sc≈0.835*0.985≈0.82 → r≈2.9px, diameter 5.5px. Slightly small but with 1000 units it reads as mass battle; near-field units (p=1) r≈3.7px (7.4px diameter) — visible. Could increase unit size to 4.2/5.2. Spacing 10.5 vs diameter 8.4 world → slight overlap in ranks — dense medieval press — good. Let me set r base 3.9, big 4.9. Screen diameter mid ≈ 6.4px. Fine.

Also counts 520 per side: block 26×20 grid y-span 26*11=286 (y from cy-143..+143; cy=450 → 307..593 within field ✓). Line 40×13: y-span 40*11=440: 450±220 → 230..670 ✓. Wedge ~ rows 20, width_i=5+2.2i → last ≈ 46.8*11=515 → cy=450±257 → 193..707 ✓ ok.

Wedge orientation: front row (narrow) at front. For side0: front x = cx + depth/2. Row i at x=frontX - i*11. count_i = 4+round(i*2.2). Total = Σ_{0..19} (4+2.2i) = 80+2.2*190=498 → add remainder to last rows: compute positions then while(count<N) add extra to random rows — or just accept ~498 and top up with extra row behind. Simpler: generate list of positions for desired N by iterating rows until N reached. I'll write generator producing array of {x,y} then push units until N.

Generator approach for all formations:
```js
function formation(type, N, frontX, cy, dir){ // dir: +1 facing +x (red): rows go back (decreasing x). 
 const out=[]; const sx=10.8, sy=11.2;
 if(type==='block'){ const cols=Math.ceil(N/20); wait block: ranks=20 → per row ceil(N/20)=26; iterate rows 0..19: cnt=26 (last rows fewer to total N): standard: idx=0; for r=0..19: cnt=min(26, N-idx) ... place j: y=cy+(j-(cnt-1)/2)*sy; x=frontX - dir*r*rankDepth... wait dir: red faces +x, front at max x, deeper rows smaller x: x=frontX - r*rank? For blue faces -x, front at min x: frontX_blue = cx - depth/2; deeper rows larger x: x=frontX + r*rankDepth. Use sign = side0? -1:+1 for "backwards" step: x=frontX + step*r where step=side0?-depth:depth. I'll pass dirBack = side0? -1: +1 and frontX computed by caller.
 }
 line: per row ceil(N/13)=40, rows 13.
 wedge: row r cnt = 4+Math.round(r*2.2) until N exhausted; rows until filled; frontX at row0.
}
```
Return array; jitter each ±1.6.

Rank depth sy? I used sy for y spacing 11.2 and rank depth 11 — same-ish fine.

blue cx=1200: block frontX=1200-104=1096, red frontX=400+104=504. Gap=592 ✓.

cy randomize ±40 per battle: cy=450+rand(-40,40).

**Check line formation front gap:** red line frontX=400+ (13-1)*11/2=400+66=466; blue=1200-66=1134; gap 668. Slight longer march — fine.

**Now charge latch:** gap computed from centroids: block centroids at 400/1200 → gap 800 → charge when <430: they advance closing ~2*spd*1.12: spd avg 62*1.12=69 each → 138/s: 800→430 in 2.7s + intro 1.05 + hold? (hold removed, intro covers) → charge at ~2.8s; then closing 2*108=216 → contact ~1.8s → clash ~4.6s. Good.

Also charging latch per army independently: if only red charging (gap threshold same for both since gap symmetric) → both latch same frame basically. Fine.

**Fighting detection & tgt from sense:** sense radius: 3×3 cells of 48 → max sensing ~ up to ~96 world units diagonal. Advance-to-centroid until enemies within ~96 → then tgt & chase. OK.

Also during charge, units target nearest enemy found — with gap 430→96, they beeline to centroid; per-unit lateral noise small. When gap<96, sense finds enemies → each targets nearest — collisions spread across the whole front ✓.

**One subtlety:** sense only finds enemies within 9 cells (3×3). A red unit at the far flank may have blue 200 away → no tgt → advance toward blue centroid → converges ✓.

**Spawn jitter & separation at spawn:** spacing 11 > sep radius 8.5 ✓ no initial push.

**Unit removal from units array?** Keep dead in array (alive=false) for battle duration; rebuild next battle. Grid insertion only alive ✓. Draw list only alive ✓. Loops skip dead ✓. units.length = 1040 constant per battle. Fine.

**Battle end cleanup:** newBattle: units.length=0 then push new.

**Memory:** fine.

Now let me write the actual final file text. I'll write carefully, double-checking each function.

Additional check — `scaleAt(p)` used in stamp/redraw before resize sets pw — order: resize() sets pw then newBattle. ✓

Also on resize mid-battle: rebuild bg (uses current palette ✓), redraw stamps ✓, counters persist. Units positions world-space → reprojected next frame ✓. 

Edge: topY depends on VH; projY uses pow each call ✓.

Let me write drawUnit fully:

```js
function drawUnit(u){
 const p=u.y/Hw, sc=scaleAt(p);
 const sx=VW*0.5+(u.x-Ww*0.5)*sc;
 let sy=topY+Math.pow(p,PEXP)*depth;
 const r=(u.big?4.9:3.9)*sc;
 let hop=0;
 if(u.celeb){ hop=Math.abs(Math.sin(vt*6.3+u.sw))*r*1.35; }
 // shadow
 ctx.globalAlpha=1;
 ctx.fillStyle='rgba(14,16,10,0.34)';
 ctx.beginPath();
 ctx.ellipse(sx+r*0.35, sy+r*0.5, r*1.08*(1-hop*0.06), r*0.5,0,0,TAU);
 ctx.fill();
 sy-=hop;
 const ca=Math.cos(u.a), sa=Math.sin(u.a);
 // banner
 if(u.banner){
   const wv=Math.sin(tG*(u.celeb?9:3.2)+u.sw)*0.5+0.5; // 0..1
   const tipx=sx+Math.sin(tG*1.7+u.sw)*r*0.5, tipy=sy-r*4.6;
   ctx.strokeStyle='#ded6c2'; ctx.lineWidth=Math.max(1,r*0.15);
   ctx.beginPath(); ctx.moveTo(sx, sy-r*0.3); ctx.lineTo(tipx,tipy); ctx.stroke();
   ctx.fillStyle=u.fcol;
   ctx.beginPath();
   const fl=r*2.6*(0.85+wv*0.3);
   ctx.moveTo(tipx,tipy);
   ctx.quadraticCurveTo(tipx+fl*0.5, tipy+r*0.55-wv*r*0.8, tipx+fl, tipy+r*0.15-wv*r*0.5);
   ctx.lineTo(tipx+fl, tipy+r*0.95-wv*r*0.5);
   ctx.quadraticCurveTo(tipx+fl*0.5, tipy+r*1.3-wv*r*0.6, tipx, tipy+r*1.15);
   ctx.closePath(); ctx.fill();
 }
 // sword
 let ang;
 const wside=u.w; // ±1
 if(u.swing>0){
   const pr=1-u.swing;
   ang=u.a + wside*(1.2-2.2*Math.sin(Math.min(1,pr)*Math.PI));
   wait sin(pr*π) peaks at pr=0.5: ang = a + w*(1.2 - 2.2*sin) → at pr=0: a+w*1.2; pr=0.5: a-w*1.0 (swept across front); pr=1: a+w*1.2. sweep through front ✓.
 } else if(u.celeb){
   ang=-Math.PI*0.5 + wside*0.35 + Math.sin(tG*3.4+u.sw)*0.25;
 } else {
   ang=u.a + wside*1.2 + Math.sin(tG*2.2+u.sw)*0.05;
 }
 ctx.strokeStyle='#cfd0c8';
 ctx.lineWidth=Math.max(1,r*0.26);
 ctx.beginPath();
 ctx.moveTo(sx+Math.cos(ang)*r*0.5, sy+Math.sin(ang)*r*0.5);
 ctx.lineTo(sx+Math.cos(ang)*r*2.15, sy+Math.sin(ang)*r*2.15);
 ctx.stroke();
 // body
 ctx.fillStyle=u.col;
 ctx.beginPath(); ctx.arc(sx,sy,r,0,TAU); ctx.fill();
 ctx.lineWidth=Math.max(0.7,r*0.22); ctx.strokeStyle=u.colD; ctx.stroke();
 // hurt tint
 const hr=1-u.hp/u.mhp;
 if(hr>0.12){ ctx.fillStyle='rgba(96,14,14,'+(hr*0.5).toFixed(3)+')'; ctx.beginPath(); ctx.arc(sx,sy,r,0,TAU); ctx.fill(); }
 // helmet
 const hx=sx+ca*r*0.45, hy=sy+sa*r*0.45-r*0.18;
 ctx.fillStyle=u.hc; ctx.beginPath(); ctx.arc(hx,hy,r*0.52,0,TAU); ctx.fill();
 // visor slit dot
 ctx.fillStyle='rgba(18,20,16,0.55)'; ctx.beginPath(); ctx.arc(hx+ca*r*0.34, hy+sa*r*0.34, Math.max(0.6,r*0.14),0,TAU); ctx.fill();
}
```
globalAlpha reset: I set fillStyle per draw; ensure globalAlpha stays 1 (I only set in particles pass — reset after).

vt for hop — use (vt or time since end) — declare global vt increments in end phase only; hop uses vt ✓ (0 before end).

**Sword stroke behind body:** draw sword before body ✓ (as coded: sword then body). During raised celebration sword drawn from center up — behind body partially, looks held. Fine.

Wait — sword behind body means at rest the sword sticking out on side ✓; when swinging across front, body covers center portion — still reads. OK.

**render():**

```js
function render(){
 ctx.setTransform(DPR,0,0,DPR,0,0);
 const ox=(Math.random()*2-1)*shake, oy=(Math.random()*2-1)*shake*0.6;
 ctx.translate(ox,oy);
 ctx.fillStyle='#0d0f0b'; ctx.fillRect(-24,-24,VW+48,VH+48);
 ctx.drawImage(bgC,0,0,VW,VH);
 ctx.drawImage(dcC,0,0,VW,VH);
 // smoke first
 for p ty2: draw
 // units
 dl.length=0; for u alive dl.push(u); dl.sort((a,b)=>a.y-b.y); for drawUnit
 // rest particles
 // done
}
```
Note translate before drawing all; overlay drawn after resetting translate? Vignette static while scene shakes — good:
```js
 ctx.setTransform(DPR,0,0,DPR,0,0);
 ctx.drawImage(ovC,0,0,VW,VH);
```

Particle draw:
```js
function drawParticles(smokePass){
 for(...){const p=particles[i]; const isS=p.ty===2; if(isS!==smokePass)continue;
  const a=p.l/p.tl;
  if(p.ty===2){ ctx.globalAlpha=a*0.12; ctx.fillStyle='rgb(66,68,62)'; ctx.beginPath(); ctx.arc(p.x,p.y,p.r+(p.tl-p.l)*p.gr? hmm store r0 and growth: r=p.r0+(1-a)*p.gr; arc r; fill; }
  else if(p.ty===1){ ctx.globalAlpha=a*0.20; ctx.fillStyle=pal.dustFill; r=p.r0+(1-a)*p.gr; arc fill }
  else if(p.ty===0){ ctx.globalAlpha=Math.min(1,a*1.4); ctx.fillStyle=p.c; r=p.r0*(0.4+a*0.6)? shrink: r=p.r0*a? shrink: r=p.r0*(0.35+0.65*a); arc fill }
  else { ctx.globalAlpha=a; ctx.fillStyle='#f4ead2'; fillRect(p.x-p.r/2,...,p.r,p.r) tiny spark — square? tiny 1-2px flash; use arc. }
 }
 ctx.globalAlpha=1;
}
```

**updateParticles(dt)** as described; smoke gets wobble: p.vx += Math.sin(tG*2+p.y*0.05)*dt*6? keep simple: constant drift.

Now the step() full implementation with all counters. Let me also count f0,f1 (fighting) inside main loop.

Also track army.cx even when count 0 — guard.

Let me also handle charging latch message only once (phase check ✓).

Write breakArmy:
```js
function breakArmy(a){
 if(a.broken)return; a.broken=true;
 for(const u of units) if(u.alive&&u.side===a.side&&!u.flee){ u.fl=Math.random()*1.6; }
 setPhase(a.name+' breaks and flees!');
}
```
Units convert when fl expires:
in loop: `if(u.fl>0){u.fl-=dt; if(u.fl<=0)u.flee=true;}` — but only meaningful for broken army units; harmless otherwise (fl init 0).

Note: unit mid-fight with fl>0 keeps fighting until convert — good (last stand).

Fleeing unit update: before sense? It still senses (cheap) but ignore tgt. Movement: 
```js
if(u.flee){
 if(u.fl>0){...stand jitter...} else { dirx=u.side?1:-1; diry=Math.sin(t*3+u.sw)*0.3; spd=u.spd*2.25; vx=dirx*spd... }
 if((u.side===0&&u.x<-20)||(u.side===1&&u.x>Ww+20)){despawn}
}
```

Also fleeing units still get hit (they're in grid; enemies sense them). They don't attack ✓.

hurt(): if v already dead skip. Add small hit flash? blood particles enough.

**killUnit fx:**
```js
function killUnit(v){
 if(!v.alive)return; v.alive=false;
 const a=armies[v.side]; a.count--; fallen++;
 const sd=(Math.random()*1e9)|0;
 stampBlood(v.x+(Math.random()*8-4), v.y+(Math.random()*6-3), 4.5+Math.random()*3, sd);
 stampCorpse(...);
 spawnBlood(v.x,v.y,9,1);
 spawnDust(v.x,v.y,2);
 if(Math.random()<0.45) spawnSmoke(v.x,v.y,1);
}
```

hurt():
```js
function hurt(v,d,by){
 if(!v.alive)return;
 v.hp-=d;
 spawnBlood(v.x,v.y,2,0.7);
 if(v.hp<=0) killUnit(v);
}
```

**Grid cell func:**
```js
function cellOf(x,y){
 let cx=(x/CS)|0; if(cx<0)cx=0; else if(cx>=GW)cx=GW-1;
 let cy=(y/CS)|0; if(cy<0)cy=0; else if(cy>=GH)cy=GH-1;
 return cy*GW+cx;
}
```

**Full step():**

```js
function step(dt){
 t+=dt;
 const A=armies[0],B=armies[1];
 if(phase==='intro'){ if(t>1.05){ phase='advance'; setPhase('The armies advance across the field.'); } else { updateParticles(dt); updateHud(); return; } }
 // grid rebuild
 head.fill(-1);
 for(let i=0;i<units.length;i++){const u=units[i]; if(!u.alive)continue; const c=cellOf(u.x,u.y); nxt[i]=head[c]; head[c]=i;}
 // centroids
 let s0x=0,s0y=0,n0=0,s1x=0,s1y=0,n1=0;
 for(let i=0;i<units.length;i++){const u=units[i]; if(!u.alive)continue; if(u.side){s1x+=u.x;s1y+=u.y;n1++;}else{s0x+=u.x;s0y+=u.y;n0++...}} careful names: n0.
 A.cx=n0?s0x/n0:A.cx; A.cy=n0?s0y/n0:450; B similarly.
 const gap=Math.abs(A.cx-B.cx);
 if(!A.charging&&gap<430)A.charging=true;
 if(!B.charging&&gap<430)B.charging=true;
 if(phase==='advance'&&A.charging&&B.charging){phase='charge'; setPhase('The drums beat — the lines charge!');}
 
 let f0=0,f1=0; let eng=0;
 for(let i=0;i<units.length;i++){
   const u=units[i]; if(!u.alive)continue;
   // sense
   let nd2=1e9, ne=-1, spx=0, spy=0;
   const cx0=clampCell..., do inline:
   let gx=(u.x/CS)|0; if(gx<0)gx=0; else if(gx>=GW)gx=GW-1;
   let gy=(u.y/CS)|0; if(gy<0)gy=0; else if(gy>=GH)gy=GH-1;
   const x0=gx>0?gx-1:0, x1=gx<GW-1?gx+1:GW-1;
   const y0=gy>0?gy-1:0, y1=gy<GH-1?gy+1:GH-1;
   for(let yy=y0;yy<=y1;yy++){
     const rowB=yy*GW;
     for(let xx=x0;xx<=x1;xx++){
       for(let j=head[rowB+xx]; j!==-1; j=nxt[j]){
         if(j===i)continue;
         const v=units[j]; if(!v.alive)continue;
         const dx=v.x-u.x, dy=v.y-u.y, d2=dx*dx+dy*dy;
         if(d2<SEP2){ if(d2>1e-4){ const dd=1/Math.sqrt(d2), f=1-dd*... wait f=1-d/SEP: d=1/dd... compute d=Math.sqrt(d2) once: 
            const d=Math.sqrt(d2), f=1-d/SEPR; spx-=dx/d*f; spy-=dy/d*f; }
         }
         if(v.side!==u.side&&d2<nd2){nd2=d2;ne=j;}
       }
     }
   }
   // clamp separation magnitude
   let sm=spx*spx+spy*spy; if(sm>1) {const inv=1/Math.sqrt(sm); spx*=inv; spy*=inv;}
   // targeting
   if(!u.flee){
     const cur=u.tgt, curOK=!!(cur&&cur.alive);
     if(ne>=0){
       const cand=units[ne];
       if(!curOK) u.tgt=cand;
       else{
         const cdx=cur.x-u.x, cdy=cur.y-u.y, cd2=cdx*cdx+cdy*cdy;
         if(nd2<cd2*0.6||cd2>3600) u.tgt=cand;
       }
     } else {
       if(curOK){ const cdx=cur.x-u.x, cdy=cur.y-u.y; if(cdx*cdx+cdy*cdy>3600) u.tgt=null; }
       else u.tgt=null;
     }
   }
   // move/fight
   let vx=0, vy=0, faceTo=null, moving=false;
   const tg=u.tgt;
   if(u.flee){
     if(u.fl>0){ u.fl-=dt; if(u.fl<=0)u.flee=true; }
     else{
       const sp2=u.spd*2.25;
       vx=(u.side?1:-1)*sp2 + Math.sin(t*2.6+u.sw)*10;
       vy=Math.sin(t*3.1+u.sw*1.7)*sp2*0.22;
       moving=true;
     }
     if((u.side===0&&u.x<-20)||(u.side===1&&u.x>Ww+20)){
       u.alive=false; (u.side?B:A).count--; routed++;
       continue;
     }
   } else if(phase!=='end' && tg && tg.alive){
     const dx=tg.x-u.x, dy=tg.y-u.y; const d2=dx*dx+dy*dy;
     if(!u.fig){ if(d2<FIGHT2) u.fight=true; }
     else if(d2>EXIT2||!tg.alive) u.fight=false;
     if(u.fight){
       eng++;
       faceTo=Math.atan2(dy,dx);
       u.cd-=dt;
       if(u.cd<=0){
         u.cd=u.cds*(0.7+Math.random()*0.7);
         u.swing=1;
         const rage=1+Math.max(0,t-18)*0.045;
         if(!firstClash){ firstClash=true; clashT=t; phase='clash'; setPhase('The lines collide!'); shake=Math.max(shake,7); clashBurst(); }
         hurt(tg,u.dmg*rage,u);
       }
     } else {
       const d=Math.sqrt(d2)||1;
       const ch=tg.flee?2.0:(A2=B...)? charging multiplier:
       const mult=armies[u.side].charging?1.75:1.12;
       const sp2=u.spd*(tg.flee?1.95:mult)*(u.bold?1.1:1);
       vx=dx/d*sp2; vy=dy/d*sp2; moving=true;
     }
   } else {
     if(phase!=='end'){
       const ec=armies[1-u.side];
       const dxy=ec.cy||450;
       let ax=ec.cx-u.x;
       let ay=(u.y0*0.82+dxy*0.18)-u.y;
       const dl2=ax*ax+ay*ay;
       if(dl2>4){
         const d=Math.sqrt(dl2);
         const mult=armies[u.side].charging?1.75:1.1;
         const sp2=u.spd*mult;
         let m1x=ax/d, m1y=ay/d;
         const wob=Math.sin(t*2.3+u.sw)*0.22;
         const cw=Math.cos(wob), sw=Math.sin(wob);
         vx=(m1x*cw-m1y*sw)*sp2; vy=(m1x*sw+m1y*cw)*sp2; moving=true;
       }
     }
   }
   // separation velocity
   const sf=u.fight?13:32;
   vx+=spx*sf; vy+=spy*sf;
   u.x+=vx*dt; u.y+=vy*dt;
   if(u.y<16)u.y=16; else if(u.y>Hw-16)u.y=Hw-16;
   if(!u.flee){ if(u.x<10)u.x=10; else if(u.x>Ww-10)u.x=Ww-10; }
   // heading
   let ta;
   if(faceTo!==null) ta=faceTo;
   else if(moving) ta=Math.atan2(vy,vx);
   else ta=u.a;
   let da=ta-u.a;
   while(da>Math.PI)da-=TAU; while(da<-Math.PI)da+=TAU;
   u.a+=da*(faceTo!==null?Math.min(1,dt*16):Math.min(1,dt*7));
   if(u.swing>0)u.swing=Math.max(0,u.swing-dt*5);
   if(!u.flee){ if(u.fight&&...) — count fighting: if(u.side===0)f0++; else f1++; } — wait fighting counter should be alive && !flee (fighters = not fleeing). Count regardless of engagement: yes f counts non-fleeing. Place after: if(!u.flee){ u.side? f1++ : f0++; }
 }
 engaged=eng;
 shake=Math.max(0,shake-dt*7);
 if(eng>150)shake=Math.max(shake,0.55);
 updateParticles(dt);
 // phase & morale
 if(phase==='clash'&&t-clashT>7){phase='melee';lastFlavor=t;setPhase(MELEE[(Math.random()*MELEE.length)|0]);}
 if(phase==='melee'&&t-lastFlavor>9){lastFlavor=t;setPhase(MELEE[(Math.random()*MELEE.length)|0]);}
 if(!A.broken&&!B.broken){
   if(t>42) breakArmy(A.count<=B.count?A:B);
   else if(A.count>0&&B.count>0){
     if(A.count<B.count*0.34)breakArmy(A);
     else if(B.count<A.count*0.34)breakArmy(B);
   }
 }
 if((phase==='advance'||phase==='charge'||phase==='clash'||phase==='melee'||phase==='rout')&&(f0===0||f1===0)){
   let wn;
   if(f0===0&&f1===0) wn=A.count>B.count?0:(B.count>A.count?1:-1);
   else wn=f1===0?0:1;
   endBattle(wn);
 }
 updateHud();
}
```

Wait — fighting count f0/f1: counted for all non-fleeing alive units. At battle start both >0. Victory when one side's f==0 — includes case where entire army dead or fled. But at intro→advance both counts high ✓. Edge: what if an army is entirely wiped while other also zero simultaneously — handled.

Also after endBattle, phase='end'; loop condition excludes 'end' ✓. But fleeing continue: the flee branch is inside unit loop and runs regardless of phase ✓. And phase==='end' blocks advance-branch movement (else branch checks phase!=='end') ✓ and fight branch: tg may be despawned → tg.alive false → falls to else → phase end → no move → they stand ✓. But u.fight may remain true with dead tgt: faceTo uses tg? Fight branch requires tg && tg.alive ✓ else goes to advance/end branch. But u.fight stale true — next frame with no valid tgt goes to else branch; u.fight never reset → fine since fight only consulted when tg alive... I set u.fight=false when !tg.alive? In fight branch condition: `else if(phase!=='end' && tg && tg.alive)` — if tgt dead, go to else-branch (advance) — u.fight stays true but harmless. Set u.fight=false there? Add in else-branch: u.fight=false. Cleaner. ✓

Hmm also when tgt dead but another enemy nearby — sense re-targets next frame (cur not OK → u.tgt=cand ✓).

endBattle(wn):
```js
function endBattle(wn){
 if(phase==='end')return;
 phase='end'; vt=0; winner=wn;
 for(const u of units) if(u.alive&&!u.flee){ u.celeb=true; if(u.side!==wn)u.celeb=false; }
 wait: winner side units celeb=true; if wn===-1 none.
 for u: u.celeb=(wn>=0&&u.side===wn);
 u.tgt=null; u.fight=false;
 const wA=wn>=0?armies[wn]:null;
 vOver.textContent = wn>=0?'Victory':'Annihilation';
 vName.textContent = wn>=0? wA.name : 'No banner remains';
 vName.style.color = wn>=0? (wn===0?'#e06a55':'#7fa7d6') : '#cfc9b8';
 vSub.textContent = wn>=0? wA.count+' survivors hold the field — '+fallen+' fell in '+fmt(t) : 'Both armies lie broken upon the field';
 verdict.classList.add('show');
 if(wn>=0) setPhase(wA.name+' holds the field.');
 else setPhase('The field falls silent.');
 shake=0;
}
```
Chip colors: red accent '#e0705a'? Let me define ACCENT=['#e0705a','#82a8d8']? For text on dark: red-ish #e2725b (terracotta) and #86a9d4. Units' colors deeper. OK.

vName color: winner faction accent.

Fading handled in step when phase==='end': at top:
```js
if(phase==='end'){
  vt+=dt;
  if(!fading&&vt>5.4){fading=true; faderEl.classList.add('on');}
  if(fading&&vt>6.6){ newBattle(); return; }
  updateParticles(dt); updateHud(); return; // units frozen? They should keep celebrating/fleeing!
}
```
Hmm — during 'end', units should still animate (celebration, fleeing). So don't return early — run the full unit loop but with combat disabled. The loop handles phase==='end' via branches: flee units keep moving; others: fight branch requires tg alive — tg null → advance branch gated by phase!=='end' → they stand (vx=vy=0 + separation drift) ✓. Celebrate drawn ✓. So run everything; just skip morale checks (condition includes phase list excluding 'end' ✓) and skip charge latch (harmless anyway). But careful: attack branch inside fight — tg null so no attacks ✓.

So step runs fully for all phases; the intro early-return I had — remove it, let units stand during intro via movement gating. Intro gating: in movement branches: if(phase==='intro') → treat like end (stand). Simplest: at top of behavior: `const canAct = phase!=='intro' && phase!=='end';` then in fight/move branches require canAct; flee allowed always (nobody flees during intro anyway).

And 'end' fade logic at top of step:
```js
if(phase==='end'){ vt+=dt; if(!fading&&vt>5.2){fading=true;faderEl.classList.add('on');} if(fading&&vt>6.3){ newBattle(); return; } }
```
newBattle sets phase='intro', t=0 etc.

Also updateHud each frame at end of step.

**updateHud:**
```js
function updateHud(){
 const a0=armies[0].count, a1=armies[1].count;
 if(a0!==lastCnt[0]){lastCnt[0]=a0; cntL.textContent=a0; barL.style.width=(a0/armies[0].initial*100)+'%';}
 same right.
 const s=Math.floor(t); if(s!==lastSec){lastSec=s; tally.textContent=fallen+' fallen · '+routed+' routed · '+fmt(t);}
}
```
fmt(t): m:ss.

**setPhase(txt):**
```js
function setPhase(s){ phaseEl.textContent=s; if(phaseEl.animate) phaseEl.animate([{opacity:0,transform:'translateY(5px)'},{opacity:1,transform:'translateY(0)'}],{duration:420,easing:'ease-out'}); }
```
phaseEl has css opacity .85 — animate overrides fine.

**newBattle():**
```js
function newBattle(){
 battleN++;
 const pal=PALETTES[(Math.random()*PALETTES.length)|0]; palette=pal;
 makeGroundTexture(pal); buildBackground();
 stamps.length=0; dcX.clearRect? need transform set: dcX.setTransform(DPR,0,0,DPR,0,0); dcX.clearRect(0,0,VW,VH);
 particles.length=0;
 units.length=0;
 const nmR=pick(NAMES_R), nmB=pick(NAMES_B);
 const place=pick(PLACES);
 const ttl=Math.random()<0.3?'The Field of ':'The Battle of ';
 armies=[makeArmy(0,nmR),makeArmy(1,nmB)];
 fallen=0;routed=0;firstClash=false;clashT=0;lastFlavor=0;vt=0;fading=false;winner=-1;shake=0;engaged=0;
 phase='intro'; t=0; lastCnt=[-1,-1]; lastSec=-1;
 // HUD
 nameL.textContent=nmR; nameR.textContent=nmB;
 chipL.style.background=ACCENT[0]; chipR... barL.style.width='100%'; cntL.textContent=armies[0].count; cntR...
 overline.textContent='Battle '+roman(battleN)+' · '+pick(SEASONS);
 titleEl.textContent=ttl+pick(PLACES);
 verdict.classList.remove('show');
 titleWrap.classList.remove('show'); void titleWrap.offsetWidth;
 titleTimer→ setTimeout(()=>titleWrap.classList.add('show'),300);
 setPhase('Two hosts muster for battle.'); hmm during intro display: 'Two hosts draw up for battle' — then advance msg replaces at 1.05s.
 // fade from black
 requestAnimationFrame(()=>requestAnimationFrame(()=>faderEl.classList.remove('on')));
}
```
Note: reuse of same name twice in a row possible — acceptable, or track last used indices to avoid repeats. Minor: pick avoiding immediate repeat: store last indices. I'll implement pickNo(arr, last) simple.

**makeArmy(side,name):**
```js
function makeArmy(side,name){
 const hue=side?212:8, sat=side?42:56;
 const str=0.93+Math.random()*0.14;
 const type=pick(FORMS);
 const cx=side?1200:400, cy=450+(Math.random()*80-40);
 const frontX= side? cx-105 : cx+105; // depth/2 for max ranks 19? block ranks 20→half 104.5; line 13→66; wedge varies (rows up to ~20). Let me compute frontX inside formation gen: pass cx & side; formation returns positions + we compute frontX = cx + (side?-1:1)*depth*0.5 where depth=(rows-1)*11.
```
Simplify: formation generator returns {pts, frontX}: compute rows first then positions.

Let me write generator:
```js
function genFormation(type,N,cy){
 // returns array of {x offset from front, y} plus frontX
 const sx=10.9, sy=11.3;
 let rows, per, counts=[];
 if(type==='line'){ rows=13; per=Math.ceil(N/rows); }
 else if(type==='block'){ rows=20; per=Math.ceil(N/rows); }
 else { // wedge
   rows=0; let tot=0; counts=[];
   while(tot<N){ const c=4+Math.round(rows*2.2); counts.push(c); tot+=c; rows++; }
   // counts may overshoot; trim last
 }
 const depth=(rows-1)*10.6;
 for r in 0..rows-1:
   const cnt = type==='wedge'? counts[r] : Math.min(per, N - r*per);
   wait for uniform: remaining = N - placed; cnt=Math.min(per,remaining).
   for j<cnt: y=cy+(j-(cnt-1)/2)*sy;
   x = frontX + back*r*10.6 where frontX= cx+(side?-1:1)*(depth/2)?? hmm wedge front row is narrow: frontX for wedge = cx + (side? -1:1)*(depth/2)? wedge depth=(rows-1)*10.6; front at extreme. yes same formula.
   place x = frontX + (side? 1 : -1)*r*10.6; (red: back rows go -x... wait red front at right (+x side of its block): red frontX=cx+depth/2; back rows decrease x: x=frontX - r*10.6 → sign=-1 for side0. side1: frontX=cx-depth/2; back rows +: sign=+1.
 }
```
Check y bounds: line: per=40 → y span 40*10.9=436 → cy±218: cy up to 490 → 272..708 ✓; block per=26 → 283 span ✓; wedge max cnt=4+19*2.2≈46 → span 500 → cy±250 → up to 700, down to 200 ✓ (cy 410..490).

Jitter ±1.4.

**makeArmy:**
```js
function makeArmy(side,name){
 const a={side,name,count:0,initial:0,broken:false,charging:false,cx:side?1200:400,cy:450};
 const type=pick(FORMS);
 const N=520;
 const pts=genFormation(type,N,side);
 for(const pt of pts){
   const l=40+Math.random()*14;
   const u={
     x:pt.x+(Math.random()*3-1.5), y:pt.y+(Math.random()*3-1.5), y0:pt.y,
     side, a:side?Math.PI:0,
     hp:0,mhp:88+Math.random()*30, dmg:(15+Math.random()*9)*str,
     cds:0.48+Math.random()*0.26, cd:Math.random()*0.5,
     spd:52+Math.random()*18,
     tgt:null, rt:Math.random()*0.3, fight:false, swing:0,
     sw:Math.random()*TAU, w:Math.random()<0.5?-1:1,
     big:Math.random()<0.07, bold:Math.random()<0.12, banner:false,
     flee:false, fl:0, celeb:false, alive:true,
     col:`hsl(${hue+(Math.random()*8-4)},${sat}%,${l}%)`,
     colD:`hsl(${hue},${sat}%,${l*0.5}%)`,
     dcol:`hsla(${hue},${Math.round(sat*0.5)}%,${16+Math.random()*5}%,0.9)`,
     hc:`hsl(46,${10+Math.random()*10}%,${58+Math.random()*14}%)`,
     fcol:`hsl(${hue},${sat+14}%,54%)`,
   };
   u.mhp=Math.round(u.mhp*(0.9+Math.random()*0.2)); wait keep simple: u.hp=u.mhp.
   units.push(u); a.count++;
 }
 a.initial=a.count;
 // banners
 for(let b=0;b<3;b++){ const u=units[units.length-1-((Math.random()*N)|0)]; hmm pick random from this army: index range — track start index. Pass startIdx: const sIdx=units.length-N; const u=units[sIdx+((Math.random()*N)|0)]; u.banner=true; u.mhp*=1.7; u.hp=u.mhp; }
 return a;
}
```
Careful: `l` used in col strings — define const li=40+Math.random()*14.

hsl with fractional values fine.

Blue hue 212 sat 42 light ~40-54 — steel blue, ok distinct from "default blue" tailwind? It's a faction color demanded by the sim; visually it's a muted steel blue. Fine.

**roman(n):**
```js
function roman(n){const T=[[1000,'M'],[900,'CM'],[500,'D'],[400,'CD'],[100,'C'],[90,'XC'],[50,'L'],[40,'XL'],[10,'X'],[9,'IX'],[5,'V'],[4,'IV'],[1,'I']];let s='';for(const[v,r]of T){while(n>=v){s+=r;n-=v;}}return s;}
```

**Names lists finalize:**
```js
const NAMES_R=['The Crimson Host','The Red Legion','The Scarlet Banner','The Rose Company','The Bloodaxe Warband','The Redward Men'];
const NAMES_B=['The Azure Order','The Cobalt Company','The Sapphire Guard','The Winter Host','The Riverlord Blues','The Bluebanner Ward'];
const PLACES=['Ashvale','Blackmere','Wolford Fen','Ravenhill','Stonewatch','Coldbrook','Thornfield','Grimsmoor','Eagleford','Saltmere','Harrowgate','Duskwold','Redfern Cross','Caelmarsh','Ironholt','Fennwick'];
const SEASONS=['the Wet Season','the Harvest Moon','First Frost','the Long Dry','Lammas Tide','the Sowing Wind'];
const FORMS=['block','line','wedge'];
const MELEE=[...as above];
```

**Title/overline composition done.**

**pick with no immediate repeat:** store lastPick per array? simple: function pick(a){return a[(Math.random()*a.length)|0]} — repeats possible but harmless.

Now bg features: also add **faint battlefield boundary?** no.

**buildBackground** must exist before first render: newBattle calls makeGround+buildBackground ✓.

**Overlay grain:** build in resize.

Let me also double-check **decal canvas transform on resize** — resize sets dcX transform & calls redrawStamps (which clears & redraws). redrawStamps:
```js
function redrawStamps(){
 dcX.setTransform(DPR,0,0,DPR,0,0);
 dcX.clearRect(0,0,VW,VH);
 for(const s of stamps) drawStamp(dcX,s);
}
```
drawStamp uses scaleAt → needs pw set ✓.

**stampBlood/corpse/flag push + immediate draw + trim:**
```js
function addStamp(s){ stamps.push(s); if(stamps.length>1200) stamps.shift(); drawStamp(dcX,s); }
```
Wait — shift removes oldest but dcX still has it painted; next shift would need clearing that region — impossible cheaply. Alternative: cap high enough that overflow rare: battle ~1600 deaths × 2 stamps = 3200 > 1200. Hmm. Options: (a) accept cap by skipping oldest — visually oldest fade? can't erase. (b) increase cap to 4000 and skip redraw perf concern: redrawStamps draws 4000 stamps on resize — each ~8 arcs → 32k arcs one-time ~ maybe 50-120ms — acceptable on resize (rare). (c) reduce stamps: corpse stamp includes its own blood (combine blood into corpse stamp) → 1 stamp per death ≈ 1600. Plus occasional extra blood. Cap 2600. Redraw on resize: 2600×~9 ellipses = 23k arcs — one-time ~80ms — acceptable.

Combine: stampDeath(k:0) does blood splat + corpse + weapon. And banner drop separate (rare). Blood hits (non-fatal) don't stamp. 

Also add tiny ground scuffs from movement? skip.

So stamps: per death 1 (death), plus flags. Cap 3000; when exceeding, just stop adding blood-only? Simplest: cap array; when full, overwrite via index cursor ring! Ring buffer: stamps fixed array 3000, cursor cycles; redraw draws in insertion order (oldest first → newest on top ✓). Store count. 
```js
const stamps=new Array(3000); let sN=0, sI=0;
function addStamp(s){ if(sN<3000){stamps[sN++]=s;} else {stamps[sI]=s; sI=(sI+1)%3000;} drawStamp(dcX,s); }
redraw: for(i=0;i<sN;i++) drawStamp(stamps[(sI+i)%3000]) when full — insertion order: oldest is at sI. When not full: 0..sN-1.
```
Handle both cases: order = full? (sI..) : (0..sN). ✓

**drawStamp implementation** (as sketched). Corpse includes blood beneath: draw 5-7 blood blobs then body.

Let me also give blood slight palette-independent dark maroon 'rgba(70,10,12,x)'.

**Now the intro return issue:** during phase 'intro', units stand — but separation still applies → tiny settle jitter — fine (looks like shuffling ranks). Actually give idle shuffle: spd 0 but separation on → they settle apart slightly. Nice.

**Charge behavior check:** armies charging latch gap<430. Units' advance dest = enemy centroid → they steer toward centroid, not straight line — the blocks converge slightly toward center — fine.

**What about units walking out of world y bounds — clamped ✓.**

**Performance check `head.fill(-1)`** 646 ints × trivial.

**Test victory edge:** both armies broken simultaneously impossible (breakArmy called once per frame per side; check `!A.broken&&!B.broken` gate → only one breaks ever? If A broken, later B could also break if condition B.count<A.count*0.34 — gate requires both unbroken → once one broken, other never "breaks" — but its units might all die → f1==0 → victory for A ✓. Or B could still have fighters while A all fled: f1>0, f0==0 → victory B?? Wait if A broke and fled, and B still fighting: f0→0 quickly → victory declared for B even though B was winning?! Careful: victory condition should be: loser = broken side fully gone. If A broke and its fighting count hits 0 (all fleeing), B wins — but my condition f0===0 triggers endBattle with wn = f1===0?0:1 → f0===0 → wn=1?? Wait wn logic: `wn = f1===0 ? 0 : 1` means if B has no fighters, winner is A(0); else winner is 1?? That's wrong: if f0===0 (A has no fighters) then winner should be B(1). Let me redo: 
```
if(f0===0&&f1===0) wn = A.count>B.count?0:(B.count>A.count?1:-1);
else if(f0===0) wn=1;   // A can no longer fight
else wn=0;              // B can no longer fight
```
✓. But scenario: A broken & fleeing (f0→0) while B still has fighters → wn=1 = B — but B is the winner, correct! (B never broke because gate blocked second break; B just wins as A routs.) ✓ Good — the `!A.broken&&!B.broken` gate only blocks the *second* break morale event; victory flows correctly.

But subtle: B count could be lower than A count when A routs? Rout threshold ensures A.count < 0.34*B.count at break → B stronger ✓.

**Victory when one army wiped without routing:** f=0 via annihilation ✓.

**During 'end', morale checks skip (phase gate) ✓.**

**updateParticles during intro:** main loop runs step which (intro) still runs full unit loop with canAct false → fine, drop the early-return.

During intro, sense/grid still runs — fine.

**One more mechanic** — "formations break apart into chaotic melee": emergent ✓. Also maybe increase separation noise over time? The rage + bold variance enough.

**HUD counters font tabular.**

**Now assemble CSS fully** (with responsive tweaks):

Also add slight text stroke via text-shadow done.

Media query for narrow screens: hide .asub? keep.

**Write final HTML now.** I'll be meticulous about brackets and semicolons. Also wrap all JS in IIFE to avoid globals leaking (optional).

Also `const TAU=Math.PI*2;`

**updateParticles:**
```js
function updateParticles(dt){
 for(let i=particles.length-1;i>=0;i--){
  const p=particles[i]; p.l-=dt;
  if(p.l<=0){ const l=particles.pop(); if(i<particles.length) particles[i]=l; continue; }
  p.x+=p.vx*dt; p.y+=p.vy*dt;
  if(p.ty===0){ p.vx*=Math.max(0,1-6*dt); p.vy*=Math.max(0,1-6*dt); }
  else if(p.ty===1){ p.vx*=Math.max(0,1-3*dt); p.vy*=Math.max(0,1-3*dt); }
  else if(p.ty===2){ p.x+=Math.sin(t*1.4+p.sw)*8*dt; }
 }
}
```
Give smoke a sw field (random phase). Use p.sw for all.

spawners:
```js
function spawnBlood(wx,wy,n,pw){
 const pp=wy/Hw, sc=scaleAt(pp);
 const sx=VW*0.5+(wx-Ww*0.5)*sc, sy=topY+Math.pow(pp,PEXP)*depth;
 for(let i=0;i<n;i++){
  const a=Math.random()*TAU, sp=(26+Math.random()*95)*sc*(pw||1);
  const l=0.22+Math.random()*0.3;
  particles.push({ty:0,x:sx+(Math.random()*4-2)*sc,y:sy+(Math.random()*3-1.5)*sc,
   vx:Math.cos(a)*sp, vy:Math.sin(a)*sp*0.7, l, tl:l, r0:(0.8+Math.random()*1.5)*sc, c:BLD[(Math.random()*3)|0], sw:0});
 }
}
```
dust:
```js
function spawnDust(wx,wy,n){
 ... sc...
 for: a rnd, sp=(8+rnd*30)*sc; l=0.5+rnd*0.5;
 particles.push({ty:1, vx:cos*sp, vy:sin*sp*0.6, l,tl:l, r0:(1.5+rnd*2.5)*sc, gr:(5+rnd*7)*sc, c:'', sw:0});
}
function spawnSmoke(wx,wy,n){ l=1.5+rnd*1.3; particles.push({ty:2,vx:(4+rnd*14)*sc, vy:(-3+rnd*6)*sc, l,tl:l, r0:(2.5+rnd*3)*sc, gr:(9+rnd*9)*sc, sw:Math.random()*TAU,c:'',x:sx,y:sy}); }
```
Dust color: fillStyle from palette.dust computed at draw with globalAlpha: store color string DUSTC = `rgba(${pal.dust},1)`? pal.dust as 'r,g,b' string → `rgba(122,112,86,`? I'll set fillStyle=`rgb(${palette.dust})` and use globalAlpha ✓. Global palette variable updated per battle.

Also first clash burst: in the firstClash block: spawn ring of dust: 
```js
for(let k=0;k<26;k++){ spawnDust(A.cx+(B.cx-A.cx)*Math.random(), 450+(Math.random()*2-1)*230 + (A.cy?...)...}
```
Simpler: midpoint x=(A.cx+B.cx)/2, y around B.cy/A.cy avg ± 260: spawn 30 dust + shake ✓.

**drawParticles:**
```js
function drawParticles(smoke){
 for(let i=0;i<particles.length;i++){
  const p=particles[i]; const isS=p.ty===2;
  if(isS!==smoke) continue;
  const a=p.l/p.tl;
  if(p.ty===2){
    ctx.globalAlpha=a*0.13;
    ctx.fillStyle='rgb(64,66,60)';
    ctx.beginPath(); ctx.arc(p.x,p.y,p.r0+(1-a)*p.gr,0,TAU); ctx.fill();
  } else if(p.ty===1){
    ctx.globalAlpha=a*0.22;
    ctx.fillStyle=DUSTFILL;
    ctx.beginPath(); ctx.arc(p.x,p.y,p.r0+(1-a)*p.gr,0,TAU); ctx.fill();
  } else if(p.ty===0){
    ctx.globalAlpha=Math.min(1,a*1.3);
    ctx.fillStyle=p.c;
    const r=p.r0*(0.35+0.65*a);
    ctx.beginPath(); ctx.arc(p.x,p.y,r,0,TAU); ctx.fill();
  } else {
    ctx.globalAlpha=a; ctx.fillStyle='#f2ead6';
    ctx.beginPath(); ctx.arc(p.x,p.y,p.r0,0,TAU); ctx.fill();
  }
 }
 ctx.globalAlpha=1;
}
```
DUSTFILL global updated per battle: DUSTFILL=`rgb(${palette.dust})`.

Smoke drawn before units, others after.

**Check: type 3 sparks** — used? add on attack: spawn 1 spark at target: minor; include in hurt: `if(Math.random()<0.5) spawnSpark(v.x,v.y)`. Sure, cheap. Actually blood spray is enough; sparks add melee glint — include, tiny.

Also **clash dust burst**: firstClash block.

**Spawn cap:** if particles.length>900 skip pushing non-essential. Add guard inside spawns: `if(particles.length>900)return;` for smoke/dust; blood keep but cap 1200.

**HUD numbers initial:** set in newBattle ✓.

**Roman/overline text-transform uppercase css.**

Now — verify unit y0 usage: advance dest y = u.y0*0.82 + ec.cy*0.18 + sin wobble? I wrote ay=(u.y0*0.82 + ecy*0.18) - u.y. With wobble rotation. ✓ Also clamp dest within field: y0 within spawn ✓.

**One concern: units at the back keep marching forward into the fight — good pressure.**

**Melee spread over time — charge line collision at middle; fine.**

**Also don't let red and blue spawn overlap center — gap 591 ✓.**

Now finalize the **HTML skeleton** and CSS with ids matching. Also `<meta name=viewport>`.

Let me also handle the `titleWrap` transitions with delay for phase? fine.

**Write out roman + fmt:**
```js
function fmt(s){const m=Math.floor(s/60),ss=Math.floor(s%60);return m+':'+String(ss).padStart(2,'0');}
```

**Verdict element markup:**
```html
<div id="verdict" class="hud-shadow">
 <div class="vover" id="vOver">Victory</div>
 <div id="vName"></div>
 <div id="vSub"></div>
</div>
```

**Tally:** `<div id="tally" class="hud-shadow"></div>`

Also maybe an unobtrusive hint bottom-right "simulation loops automatically"? Not needed... a tiny caption could be nice: bottom-left: 'an endless war — each battle fought anew'. Skip; tally suffices.

**Check: units visible against ground:** ground l≈20-26%, units l≈40-54% + rim dark — pops ✓. Shadows help.

**Corpses visibility:** dcol l 16-21% vs ground 20-26% — close; make corpse l 13-17% and blood darker red — visible via hue contrast (red vs olive) ✓ blood blobs alpha .45-.7 hue red reads.

Let me also brighten blood slightly: rgba(88,12,14,.5-.75).

**One more perf thought:** `Math.pow` per unit per frame ×3 (draw+proj in drawUnit only) fine.

**Sorting:** dl sort comparator — allocate none. ✓

**Now write everything as final answer.** Estimate ~600-700 lines. Let me carefully write, then re-verify key logic mentally.

Also the requirement "starts automatically, no interaction" ✓.

Let me also double check the wedge counts sum: rows until tot>=N; last row may overshoot; when placing, cap by remaining. Implementation:

```js
function genFormation(type,N,side){
 const pts=[]; const sx=10.9, sy=11.2;
 let rows, per, counts=null;
 if(type==='wedge'){
   counts=[]; let tot=0, r=0;
   while(tot<N){ const c=Math.min(4+Math.round(r*2.3), N-tot); counts.push(c); tot+=c; r++; }
   rows=counts.length;
 } else if(type==='line'){ rows=13; per=Math.ceil(N/rows); }
 else { rows=20; per=Math.ceil(N/rows); }
 const depth=(rows-1)*10.6;
 const cy=... passed in actually. Pass cy & cx & side.
 const sgn = side? 1 : -1; // back-step direction in x
 const frontX = (side? -1: 1)*... hmm: side1 front faces -x → front at cx - depth/2; back rows increase x. side0: front at cx+depth/2; back rows decrease x.
 let placed=0;
 for(let r=0;r<rows&&placed<N;r++){
   const cnt = counts? Math.min(counts[r], N-placed) : Math.min(per, N-placed);
   const bx = (side? cx-depth*0.5 : cx+depth*0.5) + sgn*10.6*r; // sgn=side?+1:-1 ✓ side1 back rows +x, side0 back rows -x
   for(let j=0;j<cnt;j++){
     pts.push({x:bx, y:cy+(j-(cnt-1)/2)*sy});
     placed++;
   }
 }
 return pts;
}
```
Pass cx, cy as args.

Wait wedge frontX: front row (r=0, 4 units) at the front extreme ✓ narrow tip toward enemy.

**Check line rows=13 per=ceil(520/13)=40 ✓ 13*10.9 y-span=141.7? no — y span depends on per (40): (40-1)*11.2=437 ✓.**

Block per=26 → span 25*11.2=280 ✓.

**Rank depth:** block depth=19*10.6=201; line 12*10.6=127; wedge ~ rows≈? Σ 4+2.2r: r=0..18 gives Σ=4*19+2.2*171=76+376=452 <520; r=19: c=4+41.8≈46 → tot 498; r=20: c=48 → 546 ≥520 → rows=21, depth=20*10.6=212. Front gap wedge: red frontX=400+106=506; blue=1200-106=1094 → gap 588 ✓.

All good.

**makeArmy assembles units & banner.** Note units push order = army0 then army1; banner pick via startIdx.

**Let me also add slight per-army "drums" visual? no.**

**HUD chip diamonds (rotate 45deg).**

Now, one more important detail: the first frame before any battle — boot: resize→newBattle→loop. Fine.

**Potential divide-by-zero: armies[1-u.side].cx when enemy count 0 → guarded (cx retains last value; initialized). ✓

**updateHud initial bars:** set width 100% at battle start (lastCnt forced -1 → update sets). ✓

**Edge: division by initial — initial stored ✓.**

**Let me also handle document hidden → dt clamp 0.05 ✓.

**Also add `image-rendering` default fine.

**Write the final code now.** During writing, keep variable names consistent:

Globals: cv, ctx, bgC,bgX, dcC,dcX, ovC,ovX, texC,texX, DPR,VW,VH, topY,depth,pw, palette, DUSTFILL, units, particles, stamps ring, armies, phase,t,vt,shake,engaged, fallen,routed, firstClash,clashT,lastFlavor, battleN, winner, fading, lastCnt,lastSec, dl, head,nxt, TAU, constants.

Also SEPR=8.5, SEP2=72.25, FIGHT2=12^2=144, EXIT2=15.5^2=240.25 — wait fight enter when d<12 (FIGHT2=144), exit d>15.5. But attack range while fighting uses fight state, no per-frame distance re-check needed beyond hysteresis ✓.

RANGE check uses tgt distance each frame ✓.

Also units retarget: I removed rt timers; sense-based switching each frame is fine (cheap since sense loop already done). But nearest switch `nd2<cd2*0.6` may cause dithering; add slight hysteresis: switch if nd2 < cd2*0.55. ok.

Additionally prevent targeting units nearly engaged by many? no.

Also "nearest enemy" claim satisfied by sense+fallback ✓.

Now let me also make sure **fleeing units ignore separation?** They should push through crowds: keep separation but reduced (sf same) — they may jam at edges with chasers — fine, dramatic crush at edge... they despawn at x bounds quickly.

Fleeing through enemy lines: they'll get attacked — good.

**Also y0 clamp: cy chosen 410-490 with spans ≤ ±260 → min y ~150 max ~750 within [16,884] ✓.**

**Draw order for banners:** pole drawn in drawUnit before sword/body ✓.

Let me also decide **ACCENT colors:** ACCENT=['#e0715a','#8fb2dc']? red accent #e0715a; blue #8fb2d9? For chips + bar fills + verdict name. Bars fill uses these.

Counter numbers color: default ink; maybe tint subtly: keep ink.

**HUD names:** nameL small caps uppercase; may overflow width 172px for 'The Bloodaxe Warband' — font 11px letterspacing .14em — ~20 chars ok maybe wraps; add white-space normal fine, line-height tight. Use width 190px.

OK writing final answer now. Also add small comment header in JS.

One more check — **bg strips drawing:** texC 720×405 mapping world 1600×900 (scale 0.45): sY=y0*0.45, sH=(y1-y0)*0.45. Ensure last strip within texture: use sH=min(TH-sY, computed). Also strips must start slightly before topY? p=0 exactly topY ✓.

Strips count: choose step so each strip ≈1.5px near bottom: near-bottom strip world height Hw/strips; screen height ≈ d(sy)/dp * step/Hw... near p=1 derivative = depth*PEXP/Hw*step... let me just use strips=220 → world step 900/220≈4.09 → bottom screen height ≈ 4.09/900*1.42*depth ≈ 4.09*1.42*0.87 ≈ 5px?? hmm: dsy = PEXP*p^0.42*(depth/Hw)*dWorld = 1.42*depth/900*4.09 ≈ 1.42*0.94*VH... let me compute: depth≈0.95VH; dsy≈1.42*0.95VH*4.09/900 ≈ 0.0058VH ≈ 4.6px at VH=800 → banding visible? drawImage strips with 1px vertical interpolation... adjacent strips sample adjacent texture rows; scale changes slightly per strip — piecewise but smooth enough (scale varies 4.6px strip by ~0.3%). Should look fine. Use strips=240 → ~2.9px each. Cost 240×3 drawImage one-time ✓.

Far strips: near p=0 derivative→0: screen height per strip → tiny (many strips compress near top) — overlapping draws fine (each drawn at its sy with height to next) — I compute sy0,sy1 per strip and draw height sy1-sy0 (could be <1px far top: dh<1 draws sub-pixel — fine, or skip if dh<0.3 → but then gaps: add epsilon). Use dh=sy1-sy0+0.75.

Also horizontal sampling: source is whole width TW — dest width dw=Ww*sc... but wait: dest must correspond to world x 0..1600 → dw = 1600*pw*sc = (VW*0.985/pw?) — pw=VW*0.985/Ww → Ww*pw=VW*0.985 ✓ dw=VW*0.985*sc? No: sc=scaleAt(p)=(SF+(SN-SF)p)*pw → dw=Ww*sc = Ww*pw*k = VW*0.985*k where k=persp factor ✓. dx=VW/2-dw/2 ✓.

**Vertical texture aliasing at far strips:** many strips sample nearly same source line → fine (magnified texture far away? Actually far = compressed: many world rows per screen px — we draw one strip per world row-band → oversampled — ok).

Hmm wait: far strips: dh small (0.5px) but we have 240 strips → the top ~30 strips occupy few px — draws overlap heavily — fine.

**Haze band after strips:** gradient rgba(168,162,142,0.30) at topY-6 → transparent at topY+0.32VH? Use two stops. Also slight cool tint top.

**Features placement uses w2s helper.**

Craters: 2-3, radius world 40-70.

Rocks: 30, sizes world 1.5-3.5 radius — tiny; draw ellipse gray w/ shadow.

Grass tufts: 150 tiny strokes — at far scale nearly invisible; ok cheap.

Trees: 6: positions: y<180 (far band) random x; plus 2 near left/right mid edges (x<130 or >1470, y 300-600). Draw: shadow ellipse (offset +x), trunk small dark rect, canopy: 3 blobs dark green-gray #2c3325 alpha .9, highlight blob. Size world radius ~10-16 → screen ~8-13px at mid — visible but subtle. Also second smaller bush type. Keep 5-7 items.

Also add **faint world-edge darkening** baked via vignette ✓.

**Now the overlay vignette:** radial: createRadialGradient(VW/2, VH*0.52, min(VW,VH)*0.36, VW/2, VH*0.52, max(VW,VH)*0.75); stops: 0 rgba(0,0,0,0), 1 rgba(5,7,5,0.5). Plus top-bottom slight: linear top rgba(8,10,10,0.25)→0 by 12%: since sky already dark, ok skip. Grain pattern alpha 0.05.

Grain gen: gcv 128; ImageData random gray.

**Check vignette drawn ABOVE units adds cohesion ✓.**

**HUD legibility on bright field:** text-shadow ok.

**Final code writing** — I'll now produce it. Also double-check no `let` redeclare bugs.

Also remember updateHud called in step end; and during 'end' phase too (counts drain from fleeing) ✓ since step runs.

**Victory hop uses vt which resets each battle ✓.**

**celeb units still in fight branch? tg cleared; advance branch gated by phase!=='end' → stationary with separation jitter ✓ (they'll slowly shove apart — fine, celebratory crowd disperses slightly). Maybe also gentle random shuffle: add tiny wander when celeb: vx=sin(t*1.3+sw)*8. Cute — add in advance-branch when phase==='end': 
```js
vx=Math.sin(t*1.1+u.sw)*9; vy=Math.cos(t*0.9+u.sw*1.3)*7;
```
✓.

**Also winner banner bearers wave — handled by u.banner & celeb wv.**

**Fading & newBattle ordering:** newBattle called while fader 'on' → rebuild + requestAnimationFrame remove class → transition 0.9s reveal. ✓

**Boot:** resize(); newBattle(); requestAnimationFrame(loop). newBattle calls buildBackground which needs texC — makeGroundTexture called inside newBattle before buildBackground ✓. resize() also calls buildBackground if palette set — guard: `if(palette) buildBackground();`.

resize() calls redrawStamps ✓ (stamps empty initially).

**Resize listener:** window.addEventListener('resize', resize).

**Potential bug:** in resize, dcC size set then redrawStamps uses stamps ✓.

**roman for battleN.**

**SEASONS pick.**

I think we're ready. Also include a brief text explanation after the code block, per my practice. Language: English (user wrote English).

Let me also double check the **fight enter/exit and separation conflict**: fighting units separated at 13 strength vs SEP radius 8.5: neighbors within 8.5 push apart; fight range enter 12 — units approaching: chase until d<12 → fight; separation pushes them apart until d≈8.5 boundary only (they're at 12 > 8.5 → no separation between the pair!) — wait SEP radius 8.5 < fight distance 12 → the fighting pair doesn't push each other at all ✓ good. Other units nearby within 8.5 push — fine.

But then units stop at d≈12 and swing — visually they stand slightly apart — with radius ~4 world each, gap 12 means ~4 world gap between edges — reads as dueling distance ✓. Add slight forward lunge on swing: offset body toward target during swing: shift draw pos by cos/sin(a)*r*0.5*swing — adds punch. Implement in drawUnit: lunge = Math.sin(u.swing*Math.PI)... u.swing goes 1→0; lunge amount = Math.sin(u.swing*Math.PI)*r*0.6 toward facing ✓ cheap and lively.

**Hit feedback direction:** blood spawns at target ✓.

**Attack sound none.**

**Check cd initial random so ranks don't sync ✓.**

**Rage ramp message? no.**

**Count check on killUnit for banner flags: stamp dropped flag: if(v.banner) addStamp({k:2,...col:v.fcol}) ✓.**

**Also fleeing banner bearer keeps flag — fine.**

Now — writing. I'll keep code tidy with sections. Let me also decide `u.y0` used only initial; after melee they wander — advance dest uses y0 (home lane) — during melee tgt exists mostly; fine.

Potential subtle issue: **advance dest x = enemy centroid x**: early on, red dest x=1200 — units march right ✓; they converge y toward blend 0.82 home — mild.

**When enemy army broken & fleeing:** winners chase (tgt fleeing) — mult 1.95 vs flee 2.25 — runners slowly pull away but despawn at edge ✓ pursuit visual ✓.

**Hmm, chasers with no tgt in range during pursuit: advance toward fleeing centroid → chase ✓.**

**After all enemies despawned:** count 0, f 0 → endBattle already triggered earlier when f hit 0 (before despawn completes) ✓ — endBattle at the moment last enemy starts fleeing (within fl delays, f counts non-flee units: they still count until converted... fl conversion makes u.flee=true after delay; f counts !flee → after all converted, f=0 → end). During fl delay they're still "fighting" count ✓.

Edge: broken army unit killed while fl pending → fine.

**endBattle during phase 'rout'** ✓ gate list includes 'rout'.

Also possible: A breaks; A units flee; but before f0 reaches 0, B count drops to 0?? B can't lose units except by kills — A is fleeing, not fighting... A units with fl>0 still fight! They can kill B units. If B somehow gets wiped while A broken: f1===0 → wn=0 (A wins)?? A broke but survives — weird but acceptable ("the day is carried"). Rare. Fine.

**One more: breakArmy threshold uses counts incl. fleeing — after break, counts drop as they despawn; second break gate blocked anyway.**

**Victory while some enemies still fighting? f loser==0 exactly means all losers fleeing/dead ✓.**

Alright — also **HUD 'fighting' vs count**: bar uses count ✓.

**Numbers format:** counts plain integers.

**Let me write the code.** (Finally.) I'll include modest comments.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Field of Crowns — a mass battle, endlessly refought</title>
<style>
 html,body{margin:0;height:100%;overflow:hidden;background:#0a0b09}
 #scene{position:fixed;inset:0;display:block}
 #hud{position:fixed;inset:0;pointer-events:none;color:#e9e4d4;font-family:Georgia,'Times New Roman','Palatino Linotype',serif}
 .sh{text-shadow:0 1px 2px rgba(0,0,0,.8),0 0 16px rgba(0,0,0,.5)}
 #titleWrap{position:absolute;top:16px;left:50%;transform:translateX(-50%);text-align:center;opacity:0;transition:opacity .9s ease .1s;max-width:70vw}
 #titleWrap.show{opacity:1}
 #overline{font-size:11px;letter-spacing:.4em;text-transform:uppercase;opacity:.7}
 #title{font-size:clamp(22px,3.6vw,40px);font-weight:700;letter-spacing:.02em;line-height:1.08;margin:4px 0 0}
 .rule{width:150px;height:1px;margin:9px auto 8px;background:linear-gradient(90deg,transparent,rgba(233,228,212,.55),transparent)}
 #phase{font-style:italic;font-size:clamp(12px,1.4vw,15px);opacity:.88;min-height:1.3em}
 .army{position:absolute;top:22px;width:180px}
 #armyL{left:24px}#armyR{right:24px;text-align:right}
 .aname{font-size:11px;letter-spacing:.13em;text-transform:uppercase;opacity:.92;display:flex;align-items:center;gap:8px}
 #armyR .aname{justify-content:flex-end}
 .chip{width:9px;height:9px;transform:rotate(45deg);flex:none;box-shadow:0 0 0 1px rgba(0,0,0,.4)}
 .acount{font-size:clamp(26px,3vw,38px);font-weight:700;line-height:1.1;margin-top:3px;font-variant-numeric:tabular-nums}
 .abar{height:3px;background:rgba(233,228,212,.16);margin-top:7px;position:relative}
 .abar i{position:absolute;left:0;top:0;bottom:0;width:100%}
 #armyR .abar i{left:auto;right:0}
 .asub{font-size:10px;letter-spacing:.22em;text-transform:uppercase;opacity:.5;margin-top:6px}
 #tally{position:absolute;bottom:16px;left:50%;transform:translateX(-50%);font-size:11px;letter-spacing:.26em;text-transform:uppercase;opacity:.6;white-space:nowrap}
 #verdict{position:absolute;left:50%;top:40%;transform:translate(-50%,-50%);text-align:center;opacity:0;transition:opacity .9s ease}
 #verdict.show{opacity:1}
 #vOver{font-size:13px;letter-spacing:.6em;text-transform:uppercase;opacity:.85;margin-bottom:10px}
 #vName{font-size:clamp(30px,4.6vw,52px);font-weight:700;line-height:1.05}
 #vSub{font-size:clamp(12px,1.4vw,15px);font-style:italic;opacity:.9;margin-top:10px}
 #fader{position:fixed;inset:0;background:#06070a;opacity:1;transition:opacity .9s ease;pointer-events:none}
 #fader.on{opacity:1}
</style>
```
Wait #fader default opacity? Start 'on' (black) then removed. Set base opacity:0 and .on{opacity:1}; markup class="on". ✓ (as written base 0 — I put opacity:1 accidentally; fix base 0.)

HUD html:

```html
<canvas id="scene"></canvas>
<div id="hud">
 <div class="army sh" id="armyL">
  <div class="aname"><span class="chip" id="chipL"></span><span id="nameL"></span></div>
  <div class="acount" id="cntL">0</div>
  <div class="abar"><i id="barL"></i></div>
  <div class="asub">on the field</div>
 </div>
 <div class="army sh" id="armyR">
  <div class="aname"><span id="nameR"></span><span class="chip" id="chipR"></span></div>
  <div class="acount" id="cntR">0</div>
  <div class="abar"><i id="barR"></i></div>
  <div class="asub">on the field</div>
 </div>
 <div id="titleWrap" class="sh">
  <div id="overline"></div>
  <h1 id="title"></h1>
  <div class="rule"></div>
  <div id="phase"></div>
 </div>
 <div id="verdict" class="sh">
  <div id="vOver"></div>
  <div id="vName"></div>
  <div id="vSub"></div>
 </div>
 <div id="tally" class="sh"></div>
</div>
<div id="fader" class="on"></div>
```

h1 margin default — set margin in css (did: margin 4px 0 0? I set `#title{...margin:4px 0 0}` — includes margin shorthand ✓; but h1 default font-weight bold anyway; ok).

barL initial width 100% via css `.abar i{width:100%}` ✓.

Now JS. Writing completely:

```js
<script>
(function(){
'use strict';
const TAU=Math.PI*2;
const Ww=1600, Hw=900;
const CS=48, GW=Math.ceil(Ww/CS), GH=Math.ceil(Hw/CS);
const SEPR=8.5, SEP2=SEPR*SEPR, FIGHT2=144, BREAK2=242;
const MAXS=3000;

const cv=document.getElementById('scene');
const ctx=cv.getContext('2d');
const $=id=>document.getElementById(id);
const nameL=$('nameL'),nameR=$('nameR'),cntL=$('cntL'),cntR=$('cntR'),
      barL=$('barL'),barR=$('barR'),chipL=$('chipL'),chipR=$('chipR'),
      overline=$('overline'),titleEl=$('title'),phaseEl=$('phase'),
      tallyEl=$('tally'),verdict=$('verdict'),vOver=$('vOver'),vName=$('vName'),vSub=$('vSub'),
      fader=$('fader'),titleWrap=$('titleWrap');

const bgC=document.createElement('canvas'),bgX=bgC.getContext('2d');
const dcC=document.createElement('canvas'),dcX=dcC.getContext('2d');
const ovC=document.createElement('canvas'),ovX=ovC.getContext('2d');
const texC=document.createElement('canvas');const texX=texC.getContext('2d');
const TW=720,TH=405;

let DPR=1,VW=960,VH=600,topY=60,depth=500,pw=0.6;
const PEXP=1.42,SF=0.60,SN=1.07;
```

... continue. I'll write helper scaleAt, projY.

Data lists, palettes.

State vars.

resize()

makeGround(pal), buildBackground(), buildOverlay()

stamp ring, drawStamp, redrawStamps

units creation, formations

grid arrays

step, updateParticles, spawns

drawUnit, drawParticles, render

HUD funcs

newBattle, endBattle, breakArmy, hurt, killUnit

boot.

Let me carefully write step's flee-despawn `continue` — inside for loop over units with index i — continue fine.

Also `u.rt` unused now (dropped) — remove from creation or keep harmless. Drop.

Let me now also verify drawUnit lunge uses u.a facing; during fight faceTo set so facing target ✓.

Now, particle caps: guard in spawn functions: `if(particles.length>900)return;` for dust/smoke; blood allow up to 1200: guard 1200.

drawParticles(DUSTFILL) uses palette var.

buildOverlay grain: 
```js
const gcv=document.createElement('canvas');gcv.width=gcv.height=128;
const gx=gcv.getContext('2d');const id=gx.createImageData(128,128);
for(i...){v=(Math.random()*255)|0; d[i*4]=d[i*4+1]=d[i*4+2]=v; d[i*4+3]=255;}
gx.putImageData(id,0,0);
pattern=ovX.createPattern(gcv,'repeat');
```
Then in buildOverlay: fill vignette; ovX.globalAlpha=0.05; fillStyle=pattern; fillRect; alpha reset. Pattern coordinates fixed — fine.

Wait grain pattern over whole screen each rebuild ✓.

**w2s helper for bg features:**
```js
function w2s(x,y){const p=y/Hw,sc=(SF+(SN-SF)*p)*pw;return [VW*0.5+(x-Ww*0.5)*sc, topY+Math.pow(p,PEXP)*depth, sc];}
```

**buildBackground details** — write with palette:
```js
function buildBackground(){
 const g=bgX; const pal=palette;
 g.setTransform(DPR,0,0,DPR,0,0);
 // sky
 const sky=g.createLinearGradient(0,0,0,topY+VH*0.03);
 sky.addColorStop(0,'#2c2f33');sky.addColorStop(0.65,'#6a655c');sky.addColorStop(1,'#93897a');
 g.fillStyle=sky;g.fillRect(0,0,VW,topY+3);
 // sun haze
 const rg=g.createRadialGradient(VW*0.5,topY*0.9,10,VW*0.5,topY*0.9,VW*0.42);
 rg.addColorStop(0,'rgba(242,226,186,0.22)');rg.addColorStop(1,'rgba(242,226,186,0)');
 g.fillStyle=rg;g.fillRect(0,0,VW,topY+6);
 // far hills
 hillLayer(g, topY*0.52, topY*0.16, '#6e695e');
 hillLayer(g, topY*0.72, topY*0.12, '#57534a');
 // treeline
 treeLine(g, topY-1);
 // field strips
 const strips=240, step=Hw/strips, kx=TH/Hw;
 for(let i=0;i<strips;i++){
   const y0=i*step, y1=y0+step;
   const p0=y0/Hw,p1=y1/Hw,p=(p0+p1)/2;
   const sy0=topY+Math.pow(p0,PEXP)*depth, sy1=topY+Math.pow(p1,PEXP)*depth;
   const sc=(SF+(SN-SF)*p)*pw;
   const dw=Ww*sc, dx=VW*0.5-dw*0.5;
   const sY=Math.min(TH-1,y0*k), sH=Math.max(0.5,(y1-y0)*k);
   g.drawImage(texC,0,sY,TW,sH, dx-dw,sy0,dw,(sy1-sy0)+1.2);
   g.drawImage(texC,0,sY,TW,sH, dx,sy0,dw,(sy1-sy0)+1.2);
   g.drawImage(texC,0,sY,TW,sH, dx+dw,sy0,dw,(sy1-sy0)+1.2);
 }
 // haze near horizon
 const hz=g.createLinearGradient(0,topY-4,0,topY+VH*0.30);
 hz.addColorStop(0,'rgba(158,152,132,0.38)');hz.addColorStop(1,'rgba(158,152,132,0)');
 g.fillStyle=hz;g.fillRect(0,topY-4,VW,VH*0.30+4);
 // features
 ...rocks, tufts, craters, trees...
}
```
hillLayer: path from (0, y+wave) across using sin combos then close to topY+? fill down to topY (meets field). Implement:
```js
function hillLayer(g,base,amp,col){
 g.fillStyle=col;g.beginPath();g.moveTo(0,topY+4);
 for(let x=0;x<=VW;x+=10){g.lineTo(x,base+Math.sin(x*0.011+seed?)*amp+Math.sin(x*0.027+1.7)*amp*0.5);}
 g.lineTo(VW,topY+4);g.closePath();g.fill();
}
```
Use deterministic pseudo (Math.random fine — built once per battle).

treeLine: bumpy dark band:
```js
g.fillStyle='#3d4237';beginPath;moveTo(0,topY+2);
for(x step 7){y=topY-3-Math.abs(Math.sin(x*0.05))*5-Math.sin(x*0.013)*3; lineTo}
lineTo(VW,topY+2);closePath;fill;
```

Features:
```js
// craters
for(let i=0;i<3;i++){const [x,y,sc]=w2s(200+Math.random()*1200, 250+Math.random()*500);
 const r=(45+Math.random()*45)*sc;
 g.fillStyle='rgba(0,0,0,0.16)';ellipse(x,y+ r*0.15,r,r*0.55) fill;
 g.strokeStyle='rgba(255,250,230,0.07)';lw=max(1,r*0.06); ellipse arc top half stroke;
 g.fillStyle='rgba(0,0,0,0.12)'; inner ellipse r*0.6;
}
// rocks
for(let i=0;i<34;i++){[x,y,sc]=w2s(rand margins); const r=(1.6+Math.random()*2.4)*sc;
 shadow: fill rgba(0,0,0,.2) ellipse(x+r*0.5,y+r*0.4,r*1.2,r*0.5)
 stone: fill hsl(40,6%,38±): ellipse(x,y-r*0.2,r,r*0.7, rot rand)
 highlight: rgba(255,250,235,.12) small ellipse offset -r*0.3
}
// grass tufts
for(let i=0;i<170;i++){[x,y,sc]; strokeStyle 'rgba(20,26,12,0.35)' or lighter; lw1; small 3 strokes upward-ish len 3*sc}
// trees at edges/far
for(let i=0;i<6;i++){ pick x: i<3 → far band y=60..170 x rand; else edges x<120 or >1480, y 250..650.
 [sx,sy,sc]; const s=12*sc;
 shadow: rgba(0,0,0,.25) ellipse(sx+s*1.4, sy+s*0.5, s*1.6, s*0.5)
 trunk: fill '#241f18' rect(sx-1, sy-s*1.2, 2.4, s*1.2)? from above-ish: draw small trunk ellipse + canopy blobs above (screen up):
 canopy blobs at (sx, sy-s*1.4) etc: 3 arcs radius s*0.7 colors '#2a3123','#31392a','#262d1f' random offsets.
}
```
Trees from above at slight angle: canopy covering trunk; place canopy slightly up-screen (north) — conveys tilt ✓.

All features use Math.random each battle — regen per battle gives variety ✓ (bg rebuilt each battle).

**makeGround(pal):**
```js
function makeGround(pal){
 texC.width=TW;texC.height=TH;
 const g=texX;
 g.fillStyle=`hsl(${pal.h},${pal.s}%,${pal.l-2}%)`;g.fillRect(0,0,TW,TH);
 // plough bands
 for(let y=0;y<TH;y+=9+((y*7)%5)){
   g.fillStyle=`hsla(${pal.h},${pal.s}%,${pal.l+(y/TH*6)-2}%,0.10)`;
   g.fillRect(0,y,TW,2);
 }
 hmm simpler: horizontal bands every ~8px alternate slight lighten:
 let b=0; for(let y=0;y<TH;y+=14+((b*7)%9)){b++; g.fillStyle=`hsla(${pal.h},${pal.s}%,${pal.l-3+(b%2)*4}%,0.12)`; g.fillRect(0,y,TW,6);}
 // patches
 for(let i=0;i<110;i++){
  const r=18+Math.random()*70;
  g.fillStyle=`hsla(${pal.h+(-16+Math.random()*32)},${pal.s}%,${pal.l+(-8+Math.random()*16)}%,0.12)`;
  g.beginPath();g.ellipse(Math.random()*TW,Math.random()*TH,r,r*(0.5+Math.random()*0.5),Math.random()*3,0,TAU);g.fill();
 }
 // speckles
 for(let i=0;i<5200;i++){
  const l2=pal.l+(Math.random()*22-11);
  g.fillStyle=`hsla(${pal.h+Math.random()*20-10},${pal.s}%,${l2}%,${0.10+Math.random()*0.2})`;
  const s2=Math.random()<0.9?1:2;
  g.fillRect(Math.random()*TW,Math.random()*TH,s2,s2);
 }
 // sparse dry blades
 g.strokeStyle=`hsla(${pal.h},${pal.s+10}%,${pal.l+14}%,0.25)`;g.lineWidth=1;
 for(let i=0;i<380;i++){const x=Math.random()*TW,y=Math.random()*TH;g.beginPath();g.moveTo(x,y);g.lineTo(x+Math.random()*3-1.5,y-2-Math.random()*3);g.stroke();}
}
```
Note texC sized each battle — width assignment clears ✓.

Palette dust string used for particles: DUSTFILL=`rgb(${pal.dust})`.

**buildOverlay:**
```js
function buildOverlay(){
 ovX.setTransform(DPR,0,0,DPR,0,0);
 ovX.clearRect(0,0,VW,VH);
 const r1=ovX.createRadialGradient(VW*0.5,VH*0.52,Math.min(VW,VH)*0.34,VW*0.5,VH*0.55,Math.max(VW,VH)*0.78);
 r1.addColorStop(0,'rgba(6,8,6,0)');r1.addColorStop(1,'rgba(6,8,6,0.52)');
 ovX.fillStyle=r1;ovX.fillRect(0,0,VW,VH);
 // grain
 if(!grainPat) makeGrain();
 ovX.globalAlpha=0.05;ovX.fillStyle=grainPat;ovX.fillRect(0,0,VW,VH);ovX.globalAlpha=1;
}
```
makeGrain builds pattern from an offscreen — pattern created by ovX context — fine once (pattern resolution independent of size). Build once at boot.

**Stamp ring:**
```js
const STMAX=2800;const stamps=new Array(STMAX);let sN=0,sI=0;
function addStamp(s){ if(sN<STMAX){stamps[sN++]=s;} else {stamps[sI]=s;sI=(sI+1)%STMAX;} drawStamp(dcX,s); }
function redrawStamps(){ dcX.setTransform(DPR,0,0,DPR,0,0);dcX.clearRect(0,0,VW,VH);
 const full=sN>=STMAX;
 for(let i=0;i<sN;i++){ drawStamp(dcX, stamps[full?((sI+i)%STMAX):i]); }
}
```
careful: when not full sN counts stored. full condition: sN===STMAX (set sN=STMAX when wrapping). Implement:
```js
function addStamp(s){ if(sN<STMAX){stamps[sN++]=s;} else {stamps[sI]=s;sI=(sI+1)%STMAX;} drawStamp(dcX,s); }
function redrawStamps(){ dcX.setTransform(DPR,0,0,DPR,0,0); dcX.clearRect(0,0,VW,VH);
 const wrapped = sN===STMAX? true: false; // track flag: use variable full
 for(let i=0;i<sN;i++){ const idx= fullFlag ? (sI+i)%STMAX : i; drawStamp(dcX,stamps[idx]); }
}
```
Add `fullFlag` boolean set when wrap begins. Simple.

newBattle: sN=0;sI=0;fullFlag=false; clear dc.

**drawStamp:**
```js
function drawStamp(g,s){
 const p=s.y/Hw, sc=(SF+(SN-SF)*p)*pw;
 const sx=VW*0.5+(s.x-Ww*0.5)*sc, sy=topY+Math.pow(p,PEXP)*depth;
 const R=s.s*sc;
 const rng=mulberry32(s.sd);
 if(s.k===0){ // fallen soldier + blood
   for(let i=0;i<7;i++){
     const a=rng()*TAU, rr=rng()*rng();
     const bx=sx+Math.cos(a)*R*1.9*rr, by=sy+Math.sin(a)*R*1.25*rr;
     const br=R*(0.3+rng()*0.62);
     g.fillStyle=`rgba(${58+(rng()*36|0)},${8+(rng()*10|0)},${11+(rng()*10|0)},${(0.4+rng()*0.32).toFixed(2)})`;
     g.beginPath();g.ellipse(bx,by,br,br*(0.55+rng()*0.45),rng()*3,0,TAU);g.fill();
   }
   // body
   g.save();g.translate(sx,sy);g.rotate(s.ang);
   g.fillStyle=s.col;
   g.beginPath();g.ellipse(0,0,R*1.28,R*0.6,0,0,TAU);g.fill();
   g.fillStyle='rgba(158,152,138,0.75)';
   g.beginPath();g.arc(R*0.98,0,R*0.4,0,TAU);g.fill();
   g.strokeStyle='rgba(30,32,28,0.65)';g.lineWidth=Math.max(1,R*0.15);
   g.beginPath();g.moveTo(-R*0.3,R*0.55);g.lineTo(R*1.55,R*0.95);g.stroke();
   g.restore();
 } else { // dropped banner
   g.save();g.translate(sx,sy);g.rotate(s.ang);
   g.strokeStyle='rgba(60,58,50,0.8)';g.lineWidth=Math.max(1,R*0.14);
   g.beginPath();g.moveTo(-R*1.6,0);g.lineTo(R*1.8,R*0.3);g.stroke();
   g.fillStyle=s.col;
   g.beginPath();g.ellipse(R*0.9,R*0.05,R*0.85,R*0.42,0.2,0,TAU);g.fill();
   g.restore();
 }
}
```

killUnit stamps: addStamp({k:0,x:vx+jit,y:vy+jit,s:4.6+rnd*2.6,ang:... ,sd:rand32, col? not needed since body uses generic gray? I wrote corpse body color = s.col but replaced with neutral? Let me use faction-tinted dead color: fill s.col (deadCol). I set fillStyle=s.col before body — I wrote neutral 'rgba(158..)' for helmet. Body uses s.col ✓ include col in stamp object.

Order: blood blobs then body ✓ (body over blood center).

**mulberry32:**
```js
function mulberry32(a){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;}}
```

**drawUnit lunge:** compute `lx=Math.cos(u.a)*r*0.55*sw, ly=Math.sin...` where sw=Math.sin(u.swing*Math.PI) if swing>0 else 0; apply to sx,sy after shadow? Shift body+sword+helmet but not shadow: compute sx2=sx+lx, sy2=sy-lungedY? lunge in facing dir (world) — screen: facing dir has world dx,dy → screen offset ≈ (cos*sc, sin*sc*0.85?) — approx use (ca*sc, sa*sc*0.8). lunge = Math.sin(min(1,u.swing)*π)? u.swing decays 1→0, sin(swing*π): at swing=1 → 0?? sin(π)=0 — wrong peak. Use lunge=Math.sin((1-u.swing)*π): rises then falls as swing 1→0? (1-swing): 0→1; sin(p*π) peaks mid ✓ same as sword sweep param pr. Use pr=1-u.swing shared.

```js
const pr=u.swing>0? 1-u.swing : 0;
const lg=Math.sin(Math.min(1,pr)*Math.PI)*r*0.6*sc;
sx2=sx+ca*lg... wait ca is cos of u.a (world angle) — screen offset: dx_screen=ca*lg? Since lg already includes sc? define lg=Math.sin(pr*π)*0.6 (world units) → screen offset=(ca*lg*sc, sa*lg*sc). ok.
```
Apply to sword base, body, helmet positions (sx2,sy2). Shadow stays.

**One more: heading for red initial a=0 ✓ blue π ✓.**

**HUD bar colors:** barL.style.background=ACCENT[0]; etc at newBattle.

ACCENT=['#d96a52','#7ea4cf'].

Chips same.

vName color set in endBattle.

**tally format:** `${fallen} fallen · ${routed} routed · ${fmt(t)}` — em space? plain '·'.

**fmt:** `${m}:${ss<10?'0':''}${ss}`.

**phase initial:** setPhase('Two hosts muster for battle.') at newBattle.

**overline text:** `Battle ${roman(battleN)} · ${pick(SEASONS)}` (css uppercase).

**title:** `${prefix}${pick(PLACES)}` prefix 'The Battle of ' / 'The Field of '.

Also avoid same place consecutively: track lastPlace index.

OK — also **pick** helper:
```js
function pick(a){return a[(Math.random()*a.length)|0];}
```

**Names avoid repeat consecutive:** track lastNameIdx per list similarly — minor; skip (random ok, duplicates unlikely noticed). Eh, quick guard for places & names: store lastIdx, reroll once if same. Implement small helper pickNE(a,mem,key). I'll keep simple: random pick; duplicates rare (6-16 options). Fine.

**Main loop:**
```js
let last=performance.now();
function frame(now){
 requestAnimationFrame(frame);
 let dt=(now-last)/1000; last=now;
 if(dt>0.06)dt=0.06; if(dt<0)dt=0;
 tG+=dt;
 step(dt);
 render();
}
requestAnimationFrame(frame);
```
tG used for wave anims; t battle time; vt victory time.

step handles phase timing.

Also during phase 'end' with fading, continue rendering & stepping (celebration) ✓.

**Intro gating within behavior:** `const active = phase!=='intro' && phase!=='end';`

Fight/move branches require active; flee works anytime (not intro anyway).

Advance branch replaced by idle shuffle when !active:
```js
} else if(!active){
  vx=Math.sin(tG*1.2+u.sw)*8; vy=Math.cos(tG*0.9+u.sw*1.7)*6;
} else { // advance toward enemy centroid
```
Also fight requires active ✓ (tgt null at end anyway).

Also charging latches only when active? They latch during advance — phase 'advance' is active ✓; gate latch with phase!=='intro' implicitly (gap large at intro anyway... at intro gap=~600-800 >430 ✓ no latch).

**Also first frame phase='intro' → units stand ✓.**

Now **killUnit while iterating**: called inside loop via hurt — modifies v.alive; grid iteration for other units unaffected this frame (v skipped later by alive check) ✓. Also nxt array intact ✓.

**One subtlety — target reference to unit that later despawns (fled): alive false → targeting invalid ✓.**

**Performance of stamps during mass deaths:** each death draws ~10 ellipses onto decal canvas — fine.

**Let me also cap corpse stamps count inherent ring 3000 ✓ (battle deaths ≤ ~1100 → fits without wrap; wrap exists for safety).**

**Ring not needed given sizes but keep.**

**Check bar update when initial differs:** bar width = count/initial.

**verdict transition** ok.

**One more visual:** during 'charge', maybe speed lines? no.

**Test mental run of numbers:** At boot: resize → topY=VH*0.082, depth=VH*1.03-topY. pw=VW*0.985/1600.

VH=800: topY=65.6; depth=760; pw for VW=1440: 0.886.

Unit at y=450: p=0.5, sy=65.6+0.5^1.42*760=65.6+760*0.372=348; sc=(0.6+0.47*0.5)*0.88=0.83*0.88? wait SF+(SN-SF)*p = 0.6+0.47*0.5=0.835 → sc=0.835*0.88=0.735. r=3.9*0.735≈2.87px → diameter 5.7px ✓ good density.

Block width screen at mid: 26*10.9=283 world → 283*0.735≈208px wide block. Two blocks + gap (591 world → 434px) fits 1440 ✓. Whole field width at mid: 1600*0.735=1176px ✓.

Field vertical: y 0→900 maps to 65.6→~890 ✓.

**Spawn y span block: 283 world → sy positions compressed at far rows — fine.**

Everything seems consistent. Now also confirm **fleeing to left edge for red:** red spawn x~260-480 center-left; flee dest x=-20 → cross behind their own start — they run off left edge ✓.

**Despawn condition red x<-20:** from x~300 at speed ~120 → 2.7s to exit ✓ good pacing.

**Counters drop as they exit ✓.**

**Victory triggers when f0==0 — i.e., once all red converted to flee (fl delays ≤1.6s) — endBattle at ~1.6s after break; runners still 1-3s from edge; celebration begins while stragglers stream — ✓ nice.

**After endBattle, fleeing continue despawning (their loop branch unconditional) ✓.**

**Also winner units chase fleeing even after 'end'? active=false → they idle-celebrate; chasers stop — acceptable (victory poses).**

Now write **step** fully with correct branch structure. Let me write it out cleanly (this is the heart — be careful):

```js
function step(dt){
 const A=armies[0],B=armies[1];
 if(phase==='end'){
   vt+=dt;
   if(!fading&&vt>5.2){fading=true;fader.classList.add('on');}
   if(fading&&vt>6.35){newBattle();return;}
 }
 if(phase==='intro'&&t>1.05){phase='advance';setPhase('The armies advance across the field.');}
 t+=dt;
 // rebuild grid
 head.fill(-1);
 for(let i=0;i<units.length;i++){const u=units[i];if(!u.alive)continue;const c=cellOf(u.x,u.y);nxt[i]=head[c];head[c]=i;}
 // centroids
 let s0x=0,s0y=0,n0=0,s1x=0,s1y=0,n1=0;
 for(let i=0;i<units.length;i++){const u=units[i];if(!u.alive)continue;if(u.side){s1x+=u.x;s1y+=u.y;n1++;}else{s0x+=u.x;s0y+=u.y;n0++;}}
 if(n0){A.cx=s0x/n0;A.cy=s0y/n0;}
 if(n1){B.cx=s1x/n1;B.cy=s1y/n1;}
 const gap=Math.abs(A.cx-B.cx);
 if(phase==='advance'){
   if(gap<430&&!A.charging)A.charging=true;
   if(gap<430&&!B.charging)B.charging=true;
   if(A.charging&&B.charging){phase='charge';setPhase('The drums beat — the lines charge!');}
 }
 const active=(phase!=='intro'&&phase!=='end');
 let f0=0,f1=0,eng=0;
 for(let i=0;i<units.length;i++){
   const u=units[i];if(!u.alive)continue;
   // --- sense ---
   let nd2=1e12,ne=-1,spx=0,spy=0;
   let gxi=(u.x/CS)|0;if(gx... (name gx)
   ...
   for(let yy=y0;yy<=y1;yy++){
     const rb=yy*GW;
     for(let xx=x0;xx<=x1;xx++){
       for(let j=head[rb+xx];j!==-1;j=nxt[j]){
         if(j===i)continue;
         const v=units[j];if(!v.alive)continue;
         const dx=v.x-u.x,dy=v.y-u.y,d2=dx*dx+dy*dy;
         if(d2<SEP2&&d2>1e-6){const d=Math.sqrt(d2),f=1-d/SEPR;spx-=dx/d*f;spy-=dy/d*f;}
         if(v.side!==u.side&&d2<nd2){nd2=d2;ne=j;}
       }
     }
   }
   let sm2=spx*spx+spy*spy;
   if(sm2>1){const iv=1/Math.sqrt(sm2);spx*=iv;spy*=iv;}
   // --- targeting ---
   let cur=u.tgt,curOK=cur!==null&&cur.alive;
   if(active&&!u.flee){
     if(ne>=0){
       const cand=units[ne];
       if(!curOK)u.tgt=cand;
       else{
         const cdx=cur.x-u.x,cdy=cur.y-u.y,cd2=cdx*cdx+cdy*cdy;
         if(nd2<cd2*0.5||cd2>2500)u.tgt=cand;
       }
     }else{
       if(curOK){const cdx=cur.x-u.x,cdy=cur.y-u.y;if(cdx*cdx+cdy*cdy>3600)u.tgt=null;}
       else u.tgt=null;
     }
   } else if(!active){u.tgt=null;}
   cur=u.tgt;curOK=cur!==null&&cur.alive;
   // --- act ---
   let vx=0,vy=0,face=-9;
   if(u.flee){
     if(u.fl>0){u.fl-=dt;if(u.fl<=0)u.flee=true;}
     else{
       const sp=u.spd*2.25;
       vx=(u.side?1:-1)*sp+Math.sin(t*2.7+u.sw)*22;
       vy=Math.sin(t*3.3+u.sw*1.7)*sp*0.22;
     }
     if((u.side===0&&u.x<-18)||(u.side===1&&u.x>Ww+18)){
       u.alive=false;if(u.side){B.count--;routed++;}else{A.count--;routed++;}
       continue;
     }
   }else if(active&&u.tgt&&u.tgt.alive){
     const tg=u.tgt;
     const dx=tg.x-u.x,dy=tg.y-u.y,d2=dx*dx+dy*dy;
     if(!u.fight){if(d2<FIGHT2)u.fight=true;}
     else if(d2>BREAK2)u.fight=false;
     if(u.fight){
       eng++;
       face=Math.atan2(dy,dx);
       u.cd-=dt;
       if(u.cd<=0){
         u.cd=u.cds*(0.7+Math.random()*0.7);
         u.swing=1;
         if(!firstClash){firstClash=true;clashT=t;phase='clash';setPhase('The lines collide!');shake=Math.max(shake,7);
           for(let k=0;k<30;k++)spawnDust((A.cx+B.cx)*0.5+(Math.random()*90-45),(A.cy+B.cy)*0.5+(Math.random()*480-240));
         }
         hurt(tg,u.dmg*(1+Math.max(0,t-18)*0.045));
       }
     }else{
       const d=Math.sqrt(d2)||0.01;
       const sp=u.spd*(tg.flee?1.95:(armies[u.side].charging?1.75:1.12))*(u.bold?1.08:1);
       vx=dx/d*sp;vy=dy/d*sp;
     }
   }else if(active){
     const ec=1-u.side?B:A; // careful: armies[1-u.side]
     const ecx=armies[1-u.side].cx, ecy=armies[1-u.side].cy;
     const ax=ecx-u.x, ay=(u.y0*0.82+ecy*0.18)-u.y;
     const d2=ax*ax+ay*ay;
     if(d2>9){
       const d=Math.sqrt(d2);
       const sp=u.spd*(armies[u.side].charging?1.75:1.1);
       const wb=Math.sin(t*2.2+u.sw)*0.22;
       const cw=Math.cos(wb),sw2=Math.sin(wb);
       const m1x=ax/d,m1y=ay/d;
       vx=(m1x*cw-m1y*sw2)*sp; vy=(m1x*sw2+m1y*cw)*sp;
     }
   }else{
     vx=Math.sin(tG*1.15+u.sw)*9;vy=Math.cos(tG*0.85+u.sw*1.6)*7;
   }
   // --- separation ---
   const sf=u.fight&&!u.flee?13:30;
   vx+=spx*sf;vy+=spy*sf;
   u.x+=vx*dt;u.y+=vy*dt;
   if(u.y<16)u.y=16;else if(u.y>Hw-16)u.y=Hw-16;
   if(!u.flee){if(u.x<10)u.x=10;else if(u.x>Ww-10)u.x=Ww-10;}
   // --- heading ---
   let ta=face!==-9?face:(Math.abs(vx)+Math.abs(vy)>1?Math.atan2(vy,vx):u.a);
   let da=ta-u.a;
   while(da>Math.PI)da-=TAU;while(da<-Math.PI)da+=TAU;
   u.a+=da*Math.min(1,dt*(face>=-8?14:6.5));
   if(u.swing>0)u.swing=u.swing-dt*5>0?u.swing-dt*5:0;
   if(!u.flee){if(u.side)f1++;else f0++;}
 }
 engaged=eng;
 shake=Math.max(0,shake-dt*7);
 if(eng>150)shake=Math.max(shake,0.5);
 updateParticles(dt);
 // morale & resolution
 if(phase==='clash'&&t-clashT>7){phase='melee';lastFlavor=t;setPhase(pick(MELEE));}
 else if(phase==='melee'&&t-lastFlavor>9){lastFlavor=t;setPhase(pick(MELEE));}
 if(phase!=='intro'&&phase!=='end'){
   if(!A.broken&&!B.broken){
     if(t>42)breakArmy(A.count<=B.count?A:B);
     else if(A.count>0&&B.count>0){
       if(A.count<B.count*0.34)breakArmy(A);
       else if(B.count<A.count*0.34)breakArmy(B);
     }
   }
   if(f0===0||f1===0){
     let wn;
     if(f0===0&&f1===0)wn=A.count>B.count?0:(B.count>A.count?1:-1);
     else if(f0===0)wn=1;else wn=0;
     endBattle(wn);
   }
 }
 updateHud();
}
```

Bug check: `face` sentinel -9 vs atan2 could return values near -9? atan2 ∈ [-π,π] ≈ [-3.14,3.14]; sentinel -9 safe. Condition `face>=-8` ok.

`const ec=1-u.side?B:A;` — messy leftover; I use armies[1-u.side] directly; remove ec line.

Also targeting switch threshold: `nd2<cd2*0.5` — switching only if candidate half distance squared... nd2 is candidate d²; switch if candidate significantly closer or current too far (>2500 = 50u). ✓

Flee check `u.fl>0` — but u.fl only set on break; init 0 ✓.

Fight branch `hurt(tg,...)` — tg may have died earlier this frame from another attacker — hurt guards ✓. Also tgt reference may be stale despawned → guarded by tg.alive in branch condition ✓ (`u.fight` computed with alive tg? branch entered only if tg.alive checked at top `active&&u.tgt&&u.tgt.alive` — wait I wrote `if(active&&u.tgt&&u.tgt.alive)`? In code above: `}else if(active&&u.tgt&&u.tgt.alive){` — hmm I wrote fight/else-if structure: outer chain: `if(u.flee){...} else if(active&&u.tgt&&u.tgt.alive){ ...fight or chase... } else if(active){advance} else {idle}`. Need u.fight reset when tgt gone: if tgt dead → advance branch; u.fight stays true → next frame tgt recomputed; if new tgt within 12 → fight immediately ✓; if new tgt far → move branch (d2>FIGHT? fight flag true but d2>BREAK2 → set false ✓ since branch re-evaluates). ✓

`u.tgt` init null.

**Counters f0/f1 for victory: counted for all alive non-flee ✓ (includes fighting & standing).**

**breakArmy:**
```js
function breakArmy(a){
 if(a.broken)return;a.broken=true;
 for(let i=0;i<units.length;i++){const u=units[i];if(u.alive&&u.side===a.side&&!u.flee)u.fl=Math.random()*1.6;}
 setPhase(a.name+' breaks and flees the field!');
}
```

**endBattle:**
```js
function endBattle(wn){
 if(phase==='end')return;
 phase='end';vt=0;winner=wn;fading=false;
 for(let i=0;i<units.length;i++){const u=units[i];
   if(u.alive){u.celeb=(wn>=0&&u.side===wn&&!u.flee);u.tgt=null;u.fight=false;}
 }
 const A=armies[0],B=armies[1];
 if(wn>=0){
   const w=armies[wn];
   vOver.textContent='Victory';
   vName.textContent=w.name;
   vName.style.color=ACCENT[wn];
   vSub.textContent=w.count+' survivors hold the field — '+fallen+' fell in '+fmt(t);
   setPhase(w.name+' holds the field.');
 }else{
   vOver.textContent='Annihilation';
   vName.textContent='No banner remains';
   vName.style.color='#cfc9b6';
   vSub.textContent='Both armies lie broken upon the field — '+fallen+' fell.';
   setPhase('The field falls silent.');
 }
 verdict.classList.add('show');
 shake=0;
}
```

**hurt/kill:**
```js
function hurt(v,d){
 if(!v.alive)return;
 v.hp-=d;
 spawnBlood(v.x,v.y,2,0.75);
 if(Math.random()<0.35)spawnSpark(v.x,v.y);
 if(v.hp<=0)killUnit(v);
}
function killUnit(v){
 if(!v.alive)return;
 v.alive=false;
 const a=armies[v.side];a.count--;fallen++;
 addStamp({k:0,x:v.x+(Math.random()*8-4),y:v.y+(Math.random()*6-3),s:4.4+Math.random()*2.8,
   ang:v.a+(Math.random()-0.5)*1.4,col:v.dcol,sd:(Math.random()*4294967295)>>>0});
 spawnBlood(v.x,v.y,9,1);
 spawnDust(v.x,v.y,2);
 if(Math.random()<0.4)spawnSmoke(v.x,v.y);
 if(v.banner)addStamp({k:1,x:v.x,y:v.y+4,s:4,ang:Math.random()*3,col:v.fcol,sd:1});
}
```

**Spawns:**
```js
function spawnBlood(wx,wy,n,pw){
 if(particles.length>1100)return;
 const p=wy/Hw,sc=(SF+(SN-SF)*p)*pw;
 const sx=VW*0.5+(wx-Ww*0.5)*sc, sy=topY+Math.pow(p,PEXP)*depth;
 for(let i=0;i<n;i++){
   const a=Math.random()*TAU,sp=(24+Math.random()*100)*sc*pw2... careful name clash pw (pixels per world). Rename global pw → PPW? I used pw globally. local param named `pow`? reserved-ish (not reserved). Rename spawn param `mag`.
```
I'll name spawn functions spawnBlood(wx,wy,n,mag).

```js
function spawnBlood(wx,wy,n,mag){
 if(particles.length>1100)return;
 const p=wy/Hw,sc=(SF+(SN-SF)*p)*PPW;
 const sx=VW*0.5+(wx-Ww*0.5)*sc, sy=topY+Math.pow(p,PEXP)*depth;
 for(let i=0;i<n;i++){
   const a=Math.random()*TAU,sp=(24+Math.random()*100)*sc*mag;
   const l=0.2+Math.random()*0.3;
   particles.push({ty:0,x:sx+(Math.random()*6-3)*sc,y:sy+(Math.random()*4-2)*sc,
     vx:Math.cos(a)*sp,vy:Math.sin(a)*sp*0.72,l:l,tl:l,r0:(0.8+Math.random()*1.6)*sc,c:BLD[(Math.random()*BLD.length)|0],sw:0,gr:0});
 }
}
```
Rename global pw→PPW everywhere (proj funcs & stamps & features). Careful consistency.

spawnDust:
```js
function spawnDust(wx,wy){
 if(particles.length>1100)return;
 const p=wy/Hw,sc=(SF+(SN-SF)*p)*PPW;
 const sx=..., sy=...;
 const a=Math.random()*TAU,sp=(6+Math.random()*26)*sc;
 const l=0.5+Math.random()*0.55;
 particles.push({ty:1,x:sx,y:sy,vx:Math.cos(a)*sp,vy:Math.sin(a)*sp*0.5,l:l,tl:l,r0:(1.6+Math.random()*2.4)*sc,gr:(6+Math.random()*8)*sc,c:'',sw:0});
}
```
spawnSmoke similar l=1.4+rnd*1.2, r0=(2.5+rnd*3)*sc, gr=(9+rnd*10)*sc, vx=(4+rnd*13)*sc, vy=(-3+rnd*6)*sc, sw rnd*TAU.

spawnSpark:
```js
{l:0.09+rnd*0.06, r0:(0.9+rnd*0.8)*sc, vx fast 160*sc rnd dir, vy*0.5}
```
ty:3.

**updateParticles:** as planned; also smoke uses sw wobble.

**render + drawUnit + drawParticles.**

drawList global `const dl=[]`.

**HUD updates:**
```js
function updateHud(){
 const a0=armies[0].count,a1=armies[1].count;
 if(a0!==lastC0){lastC0=a0;cntL.textContent=a0;barL.style.width=(a0/armies[0].initial*100).toFixed(1)+'%';}
 if(a1!==lastC1){lastC1=a1;cntR.textContent=a1;barR.style.width=(a1/armies[1].initial*100).toFixed(1)+'%';}
 const s=t|0;
 if(s!==lastSec){lastSec=s;tallyEl.textContent=fallen+' fallen · '+routed+' routed · '+fmt(s);}
}
```

**newBattle:**
```js
function newBattle(){
 battleN++;
 palette=pick(PALS);DUSTFILL='rgb('+palette.dust+')';
 makeGround(palette);buildBackground();
 sN=0;sI=0;fullS=false;
 dcX.setTransform(DPR,0,0,DPR,0,0);dcX.clearRect(0,0,VW,VH);
 particles.length=0;
 const nmR=pick(NAMES_R),nmB=pick(NAMES_B);
 armies=[makeArmy(0,nmR),makeArmy(1,nmB)];
 fallen=0;routed=0;firstClash=false;clashT=0;lastFlavor=0;vt=0;fading=false;winner=-1;
 phase='intro';t=0;lastC0=-1;lastC1=-1;lastSec=-1;engaged=0;shake=0;
 nameL.textContent=nmR;nameR.textContent=nmB;
 chipL.style.background=ACCENT[0];chipR.style.background=ACCENT[1];
 barL.style.background=ACCENT[0];barR.style.background=ACCENT[1];
 cntL.textContent=armies[0].count;cntR.textContent=armies[1].count;
 barL.style.width='100%';barR.style.width='100%';
 overline.textContent='Battle '+roman(battleN)+' · '+pick(SEASONS);
 titleEl.textContent=(Math.random()<0.3?'The Field of ':'The Battle of ')+pick(PLACES);
 verdict.classList.remove('show');
 setPhase('Two hosts muster for battle.');
 titleWrap.classList.remove('show');void titleWrap.offsetWidth;
 setTimeout(function(){titleWrap.classList.add('show');},250);
 requestAnimationFrame(function(){requestAnimationFrame(function(){fader.classList.remove('on');});});
}
```

titleWrap var needed.

**makeArmy final:**
```js
function makeArmy(side,name){
 const a={side:side,name:name,count:0,initial:0,broken:false,charging:false,cx:side?1200:400,cy:450};
 const hue=side?212:8, sat=side?40:56;
 const st=0.93+Math.random()*0.14;
 const type=pick(FORMS);
 const N=520;
 const pts=genFormation(type,N,side,side?1200:400,450+(Math.random()*80-40));
 const sIdx=units.length;
 for(let i=0;i<pts.length;i++){
   const li=40+Math.random()*14;
   const u={x:pts[i].x+(Math.random()*3-1.5),y:pts[i].y+(Math.random()*3-1.5),y0:pts[i].y,
     side:side,a:side?Math.PI:0,hp:0,mhp:0,dmg:(15+Math.random()*9)*st,
     cds:0.46+Math.random()*0.26,cd:Math.random()*0.5,
     spd:52+Math.random()*18,tgt:null,fight:false,swing:0,
     sw:Math.random()*TAU,w:Math.random()<0.5?-1:1,
     big:Math.random()<0.07,bold:Math.random()<0.12,banner:false,
     flee:false,fl:0,celeb:false,alive:true,
     col:'hsl('+Math.round(hue+Math.random()*8-4)+','+sat+'%,'+li.toFixed(1)+'%)',
     colD:'hsl('+hue+','+sat+'%,'+(li*0.48).toFixed(1)+'%)',
     dcol:'hsla('+hue+','+Math.round(sat*0.5)+'%,'+(15+Math.random()*5).toFixed(1)+'%,0.92)',
     hc:'hsl(45,'+(8+Math.random()*10|0)+'%,'+(56+Math.random()*16|0)+'%)',
     fcol:'hsl('+hue+','+(sat+16)+'%,52%)'};
   u.mhp=88+Math.random()*30; u.hp=u.mhp;
   units.push(u);a.count++;
 }
 a.initial=a.count;
 for(let b=0;b<3;b++){const u=units[sIdx+((Math.random()*a.count)|0)];u.banner=true;u.mhp*=1.7;u.hp=u.mhp;u.big=true;}
 return a;
}
```

**genFormation:**
```js
function genFormation(type,N,side,cx,cy){
 const pts=[],sy=11.2;let rows,per,counts=null;
 if(type==='wedge'){
   counts=[];let tot=0,r=0;
   while(tot<N){const c=Math.min(4+Math.round(r*2.2),N-tot);counts.push(c);tot+=c;r++;}
   rows=counts.length;
 }else if(type==='line'){rows=13;per=Math.ceil(N/rows);}
 else{rows=20;per=Math.ceil(N/rows);}
 const depth=(rows-1)*10.6;
 let placed=0;
 for(let r=0;r<rows&&placed<N;r++){
   const cnt=counts?counts[r]:Math.min(per,N-placed);
   const bx=(side?cx-depth*0.5:cx+depth*0.5)+(side?1:-1)*10.6*r;
   for(let j=0;j<cnt;j++){pts.push({x:bx,y:cy+(j-(cnt-1)/2)*sy});placed++;}
 }
 return pts;
}
```

**resize:**
```js
function resize(){
 DPR=Math.min(window.devicePixelRatio||1,2);
 VW=window.innerWidth;VH=window.innerHeight;
 cv.width=Math.round(VW*DPR);cv.height=Math.round(VH*DPR);
 bgC.width=cv.width;bgC.height=cv.height;
 dcC.width=cv.width;dcC.height=cv.height;
 ovC.width=cv.width;ovC.height=cv.height;
 topY=VH*0.082;depth=VH*1.03-topY;PPW=VW*0.985/Ww;
 if(palette){makeGround? no just: buildBackground();redrawStamps();}
}
```
ctx transform set each frame.

Boot: makeGrain(); resize(); newBattle(); frame loop. Note newBattle calls buildBackground (needs DPR set ✓).

**w2s uses PPW.**

**drawStamp uses PPW, scaleAt inline.**

Let me define helpers:
```js
function scaleAt(p){return (SF+(SN-SF)*p)*PPW;}
function projY(p){return topY+Math.pow(p,PEXP)*depth;}
```
Use in drawUnit/drawStamp/spawns.

**Check dcX transform in drawStamp:** stamps drawn to dcX which has transform DPR — using css px coords ✓.

**bgX transform:** set at buildBackground start: bgX.setTransform(DPR,0,0,DPR,0,0) ✓ then drawImage(bgC,0,0,VW,VH) in render with ctx transform DPR ✓ (bgC pixel size VW*DPR — drawImage with dest w/h VW,VH scales correctly ✓).

**Now double-check render:**
```js
function render(){
 ctx.setTransform(DPR,0,0,DPR,0,0);
 const ox=(Math.random()*2-1)*shake,oy=(Math.random()*2-1)*shake*0.6;
 if(shake>0.01)ctx.translate(ox,oy);
 ctx.fillStyle='#0c0e0a';ctx.fillRect(-30,-30,VW+60,VH+60);
 ctx.drawImage(bgC,0,0,VW,VH);
 ctx.drawImage(dcC,0,0,VW,VH);
 drawParticles(true);
 dl.length=0;
 for(let i=0;i<units.length;i++){const u=units[i];if(u.alive)dl.push(u);}
 dl.sort(cmpY);
 for(let i=0;i<dl.length;i++)drawUnit(dl[i]);
 drawParticles(false);
 ctx.setTransform(DPR,0,0,DPR,0,0);
 ctx.drawImage(ovC,0,0,VW,VH);
}
const cmpY=(a,b)=>a.y-b.y;
```

**drawUnit** — finalize with lunge:
```js
function drawUnit(u){
 const p=u.y/Hw,sc=scaleAt(p);
 const sx0=VW*0.5+(u.x-Ww*0.5)*sc;
 let sy0=topY+Math.pow(p,PEXP)*depth;
 const r=(u.big?4.9:3.9)*sc;
 const hop=u.celeb?Math.abs(Math.sin(vt*6.3+u.sw))*r*1.35:0;
 ctx.fillStyle='rgba(13,15,10,0.34)';
 ctx.beginPath();ctx.ellipse(sx0+r*0.35,sy0+r*0.5,r*1.05,r*0.48,0,0,TAU);ctx.fill();
 const pr=u.swing>0?1-u.swing:0;
 const lg=Math.sin(Math.min(1,pr)*Math.PI)*r*0.55;
 const ca=Math.cos(u.a),sa=Math.sin(u.a);
 const sx=sx0+ca*lg, sy=sy0-hop+sa*lg*0.8;
 if(u.banner){
   const wv=Math.sin(tG*(u.celeb?9:3.1)+u.sw)*0.5+0.5;
   const tx=sx+Math.sin(tG*1.6+u.sw)*r*0.5, ty=sy-r*4.4;
   ctx.strokeStyle='#d9d1bd';ctx.lineWidth=Math.max(1,r*0.16);
   ctx.beginPath();ctx.moveTo(sx,sy-r*0.3);ctx.lineTo(tx,ty);ctx.stroke();
   ctx.fillStyle=u.fcol;
   const fl=r*2.6*(0.8+wv*0.4);
   ctx.beginPath();
   ctx.moveTo(tx,ty);
   ctx.quadraticCurveTo(tx+fl*0.5,ty+r*0.5-wv*r*0.9,tx+fl,ty+r*0.1-wv*r*0.6);
   ctx.lineTo(tx+fl,ty+r*0.95-wv*r*0.6);
   ctx.quadraticCurveTo(tx+fl*0.5,ty+r*1.35-wv*r*0.7,tx,ty+r*1.1);
   ctx.closePath();ctx.fill();
 }
 let ang;
 if(u.swing>0){
   ang=u.a+u.w*(1.2-2.25*Math.sin(Math.min(1,pr)*Math.PI));
 }else if(u.celeb){
   ang=-Math.PI*0.5+u.w*0.35+Math.sin(tG*3.6+u.sw)*0.25;
 }else{
   ang=u.a+u.w*1.2+Math.sin(tG*2.1+u.sw)*0.06;
 }
 ctx.strokeStyle='#ccd0c6';
 ctx.lineWidth=Math.max(1,r*0.26);
 ctx.beginPath();
 ctx.moveTo(sx+Math.cos(ang)*r*0.4,sy+Math.sin(ang)*r*0.4);
 ctx.lineTo(sx+Math.cos(ang)*r*2.1,sy+Math.sin(ang)*r*2.1);
 ctx.stroke();
 ctx.fillStyle=u.col;
 ctx.beginPath();ctx.arc(sx,sy,r,0,TAU);ctx.fill();
 ctx.lineWidth=Math.max(0.7,r*0.24);ctx.strokeStyle=u.colD;ctx.stroke();
 const hr=1-u.hp/u.mhp;
 if(hr>0.14){ctx.fillStyle='rgba(96,14,14,'+Math.min(0.55,hr*0.55).toFixed(3)+')';ctx.beginPath();ctx.arc(sx,sy,r,0,TAU);ctx.fill();}
 const hx=sx+ca*r*0.45,hy=sy+sa*r*0.45-r*0.16;
 ctx.fillStyle=u.hc;ctx.beginPath();ctx.arc(hx,hy,r*0.52,0,TAU);ctx.fill();
 ctx.fillStyle='rgba(16,18,14,0.55)';
 ctx.beginPath();ctx.arc(hx+ca*r*0.32,hy+sa*r*0.32,Math.max(0.6,r*0.15),0,TAU);ctx.fill();
}
```
Note: u.w ±1 → sword held on left or right of facing ✓.

**drawParticles:**
```js
function drawParticles(smoke){
 const n=particles.length;
 for(let i=0;i<n;i++){
   const q=particles[i];
   const isS=q.ty===2;
   if(isS!==smoke)continue;
   const a=q.l/q.tl;
   if(q.ty===2){
     ctx.globalAlpha=a*0.13;ctx.fillStyle='rgb(63,65,58)';
     ctx.beginPath();ctx.arc(q.x,q.y,q.r0+(1-a)*q.gr,0,TAU);ctx.fill();
   }else if(q.ty===1){
     ctx.globalAlpha=a*0.2;ctx.fillStyle=DUSTFILL;
     ctx.beginPath();ctx.arc(q.x,q.y,q.r0+(1-a)*q.gr,0,TAU);ctx.fill();
   }else if(q.ty===0){
     ctx.globalAlpha=Math.min(1,a*1.4);ctx.fillStyle=q.c;
     ctx.beginPath();ctx.arc(q.x,q.y,q.r0*(0.35+0.65*a),0,TAU);ctx.fill();
   }else{
     ctx.globalAlpha=a;ctx.fillStyle='#f2ecd8';
     ctx.beginPath();ctx.arc(q.x,q.y,q.r0,0,TAU);ctx.fill();
   }
 }
 ctx.globalAlpha=1;
}
```

**updateParticles:**
```js
function updateParticles(dt){
 for(let i=particles.length-1;i>=0;i--){
   const q=particles[i];q.l-=dt;
   if(q.l<=0){const lastP=particles.pop();if(i<particles.length)particles[i]=lastP;continue;}
   q.x+=q.vx*dt;q.y+=q.vy*dt;
   if(q.ty===0){const f=Math.max(0,1-5.5*dt);q.vx*=f;q.vy*=f;}
   else if(q.ty===1){const f=Math.max(0,1-2.6*dt);q.vx*=f;q.vy*=f;}
   else if(q.ty===2){q.x+=Math.sin(tG*1.4+q.sw)*9*dt;}
 }
}
```

**Constants:** SEPR=8.6, SEP2=73.96 — define numerically.

Also, guard: **units killed inside sense loop? hurt called in act phase after sense; killUnit modifies alive — grid head arrays fine.**

**One more: stamp corpse under later live units — decals under units ✓ since dcC drawn before units.**

**Cell coords in cellOf:**
```js
function cellOf(x,y){
 let cx=(x/CS)|0;if(cx<0)cx=0;else if(cx>=GW)cx=GW-1;
 let cy=(y/CS)|0;if(cy<0)cy=0;else if(cy>=GH)cy=GH-1;
 return cy*GW+cx;
}
```
GH=Math.ceil(900/48)=19 (18.75→19); cells 34*19=646 ✓.

**Grid head/nxt sizes:** head Int32Array(GW*GH)=646; nxt Int32Array(1100) — units ≤1040 ✓.

**Numbers:** units per battle 1040 (520×2). counts fine.

Now the **roman()** and **fmt()**.

**pick** etc.

Also **SEASONS** with 'the' lowercase — overline uppercase transform handles.

**Title id `title` conflicts with document.title? getElementById fine.**

**Variable name `t` battle time vs `tG` global.** In drawUnit I used tG for waves ✓ and vt for hop ✓.

**`engaged` variable maybe unused elsewhere; keep for rumble.**

**HUD initial values set in newBattle ✓; first frame after intro begins shows counts.**

**Fader initial:** markup `<div id="fader" class="on">` with CSS `#fader{opacity:0;transition:opacity .95s ease}#fader.on{opacity:1}` — boot: newBattle schedules removal → fade in ✓. Subsequent battles: added then removed ✓.

**Potential CSS: title h1 margin default 0.67em — override margin:2px 0 0.**

**Colors final:**
ACCENT=['#d9684f','#7fa7d0'].
Unit red: hue 8 sat 56 light 40-54 → strong crimson ✓. colD dark maroon.
Unit blue: hue 212 sat 40 light 40-54 → steel ✓.

BLD=['#7a1214','#5e0d10','#93201c'].

Palettes:
```js
const PALETTES=[
 {h:88,s:16,l:19,dust:'128,118,92'},
 {h:70,s:18,l:24,dust:'142,128,92'},
 {h:145,s:11,l:15,dust:'98,106,92'},
 {h:47,s:9,l:23,dust:'146,134,104'},
];
```

Check blood vs red army confusion: blood darker/desaturated, units brighter with outlines — fine.

**Sky/hills colors** fine.

**Time to write the complete final file.** Also include brief comments. Watch out: in step, early return when newBattle called (phase changed mid-step) — after newBattle() `return` — remaining loop skipped ✓.

Also updateHud called every step ✓; during intro counts show full.

**fmt:**
```js
function fmt(s){const m=(s/60)|0;const ss=s%60;return m+':'+(ss<10?'0':'')+ss;}
```
call with integer seconds.

**roman:**
```js
function roman(n){const v=[1000,900,500,400,100,90,50,40,10,9,5,4,1],s=['M','CM','D','CD','C','XC','L','XL','X','IX','V','IV','I'];let o='';for(let i=0;i<v.length;i++){while(n>=v[i]){o+=s[i];n-=v[i];}}return o;}
```

**MELEE lines:**
```js
const MELEE=[
 'No order remains — a savage melee',
 'The center buckles under the press of bodies',
 'Shields splinter; blades find the gaps',
 'The ranks dissolve into a killing ground',
 'Steel flashes across the trampled grass'
];
```

**Charge message:** 'The horns sound — the lines charge!'

**Clash:** 'The lines collide!'

**Now assemble entire HTML.** Also `<meta name="color-scheme" content="dark">` optional.

Also ensure no `console` leftovers.

Let me also reconsider: recording window 30s — the intro fade (0.95s) + muster (1.05s) fine.

Also check that at advance start units actually move: phase 'advance' → active ✓ spd mult 1.1 (army.charging false) → u.spd≈52-70 × 1.1 ≈ 57-77 — hmm brisk march; blocks close 591 gap: relative 130/s → charge latch at gap 430 after ~1.3s (t≈2.4), then 1.75× → relative ~210/s → contact ~1.9s → clash ≈ t 4.3s ✓.

Wait latch threshold 430 vs gap: at t=1.05 gap≈591 (blocks) / 588 (wedge) / 668 (line) — closing from march; latch when gap<430 → ~1.2-2.5s later ✓.

**Charge speed 1.75× ~95-125 u/s each — dramatic ✓.**

**Melee death rates:** front fight ring; fine.

Also worried: **units stop at fight range 12 but separation sf=13 while fighting with neighbors within 8.6 — ranks compact.**

Behind-ranks push: many units targeting same front enemy → they cluster around it within BREAK radius; separation among them spreads — melee knot forms ✓.

**Potential stacking through:** enemy separation included ✓.

**Victory celebration hop for big/bold ok.**

**One more possible perf hot spot:** dl.sort with closure comparator — fine.

**Also ensure `phaseEl` update on rout during clash phase etc — setPhase overrides ✓; but the melee flavor block runs only when phase==='melee'; after rout phase='rout'? I never set a distinct phase var on break — setPhase called but phase var stays previous ('clash'/'melee') → then melee flavor timer could overwrite rout message! Fix: introduce flag `routShown` or set phase variable to 'rout'. Add in breakArmy: `phase='rout';`. Then victory gate includes 'rout' ✓, and flavor blocks gated to 'melee' only ✓. Also clash→melee transition condition phase==='clash' — after rout, stays rout ✓.

But careful: breakArmy during 'advance'/'charge'? Threshold 0.34 count ratio can't trigger before contact realistically. t>42 force — could be during any phase; fine.

**After break, charging latches irrelevant.**

**End gate list:** `phase==='advance'||'charge'||'clash'||'melee'||'rout'` — implement as `phase!=='intro'&&phase!=='end'` ✓.

**`breakArmy` may be called when a.count===0? gate count>0 ✓ (t>42 branch: pick smaller; if counts equal 0/0? then f already 0 → endBattle earlier).**

Now — **write the file**. Also last check on drawParticles smoke color visibility on dark ground: alpha 0.13 gray blobs — subtle ✓ plus many during carnage.

Also **spawnSmoke at deaths** adds haze over time ✓.

**Ambient wind dust during battle? skip.**

**Final sanity on `hurt` signature** (v,d) ✓.

**spark spawn location:** at target pos ✓.

Let me also add small **hit pause**? no.

**Write final HTML now, in full.** I'll be careful about typos, undeclared vars: declare all: 

Globals list: cv,ctx,DOM refs,bgC,bgX,dcC,dcX,ovC,ovX,texC,texX,TW,TH,grainPat,DPR,VW,VH,topY,depth,PPW,PEXP,SF,SN,palette,DUSTFILL,units,particles,dl,stamps ring (STMAX,stamps,sN,sI,fullS),head,nxt,armies,phase,t,tG,vt,shake,engaged,fallen,routed,firstClash,clashT,lastFlavor,battleN,winner,fading,lastC0,lastC1,lastSec, constants (TAU,Ww,Hw,CS,GW,GH,SEPR,SEP2,FIGHT2,BREAK2,ACCENT,BLD,lists,MELEE,FORMS,SEASONS,PLACES,NAMES_R,NAMES_B,last=performance.now()).

Note: `last` name conflicts? fine.

`titleWrap` ref.

In drawUnit I referenced `vt` global ✓.

In makeArmy: units.push — ensure units global.

OK also `head` fill each step: head.fill(-1) — Int32Array ✓.

One more: **`cellOf` unused if inline in step** — I inline; but keep function anyway? Inline in step for speed; fine to keep function and call — call overhead ok but inline better; I'll inline.

**Check `u.y0` set ✓.**

**Check blue facing π; wobble fine.**

**Bar width for right side grows from right (css right:0) ✓.**

Also **asub text**: "on the field" both.

**Verdict top 40% — may overlap phase text — visually ok (phase italic small).

I think the code is ready to write. Also double-check the **first-clash dust burst** uses spawnDust at world coords — signature spawnDust(wx,wy) single particle per call ✓ loop 30.

Let me write everything now as the final answer. Also after code block, a concise explanation.

Length: acceptable.

One more consideration — **`u.cds*(0.7+Math.random()*0.7)`** avg ≈ cds*1.05 ≈ 0.55s ✓.

**Rage factor** `1+Math.max(0,t-18)*0.045` at t=40 → 1.99 — battles definitely conclude.

**Rout check frequency:** every frame ✓.

**Edge case: both armies never charge because gap stays >430 due to clumping? Centroids approach; fine.**

**Check charge latch: I gate latch inside `if(phase==='advance')` — if one army latches and phase flips to 'charge' only when both — if a wedge vs line yields asymmetric contact distances, both latch since gap same for both... gap is centroid distance — same condition both → latch same frame ✓ (I can latch both unconditionally same frame; kept).**

**Victory celebration may also include a few leftover enemy fleeing — fine.**

Also **winner units might keep `u.fight=true` stale — at end tgt=null → idle ✓ (fight flag irrelevant as branch requires tgt).**

**t continues during 'end' — melee flavor gated ✓; rage unused.**

**particles continue updating in 'end' ✓ via step (updateParticles called in step main path — yes it's called every step after loop) ✓.**

During intro early frames: step runs fully (grid, etc.) — fine.

Also **don't spawn clash dust repeatedly** — firstClash flag ✓.

I also want **victory banner waving faster** — handled via tG*(celeb?9:3.1).

**Write it.**

Also for safety define `let grainPat=null;`.

makeGrain:
```js
function makeGrain(){
 const gc=document.createElement('canvas');gc.width=gc.height=140;
 const gx2=gc.getContext('2d');
 const im=gx2.createImageData(140,140);const d=im.data;
 for(let i=0;i<d.length;i+=4){const v=(Math.random()*255)|0;d[i]=d[i+1]=d[i+2]=v;d[i+3]=255;}
 gx2.putImageData(im,0,0);
 grainPat=ovX.createPattern(gc,'repeat');
}
```

Call after ovC exists (boot) ✓.

**buildBackground hillLayer uses closure seed — just Math.random-free sin combos deterministic.**

Everything set. Compose final answer: single ```html block + short explanation (English). Also mention performance/spatial grid briefly.

Careful writing ~700 lines without syntax slips. Let me finalize a few remaining constants: SF=0.6, SN=1.07, PEXP=1.42.

topY=VH*0.082; depth=VH*1.03-topY.

Also below-field bottom: p=1 → sy=topY+depth=VH*1.03 ✓ slightly below viewport → bottom rows overflow — fine (vignette).

**rock/tree feature placement uses w2s after strips ✓.**

**One risk: `drawImage` with sY computed from world y (0..900)*TH/Hw — TH/Hw=0.45 ✓ sY up to 405-? last strip y0=895.6*0.45=403 → sH=405-403=2? y1=900 → sH=(900-895.6)*0.45≈2 ✓ within bounds ✓ (clamped sY min TH-1... fine).

**drawImage arg order: (img, sx,sy,sw,sh, dx,dy,dw,dh) ✓.**

**In strips loop, sY=Math.min(TH-2, y0*k)** safe.

Let me now also handle **`u.fight` when tgt set but distance jumps >BREAK2** ✓ handled.

**`face` var initialized -9; ta fallback** ✓.

**Heading turn speed when moving 6/s ✓.**

**Also swing decays even when not fighting ✓ (global per unit).**

**Victory hop for banner bearer with pole — pole anchored to sy (bouncing) ✓ fun.**

Final: write answer. Also short explanation (~150 words). Go.

Wait — one more check in step: the intro early-return I removed; but during intro, charge latch gate `phase==='advance'` ✓; unit act: active=false → idle shuffle — but separation active → fine.

And counts: f0/f1 counted even during intro (all alive) — victory gate requires phase!=='intro' ✓.

Also `engaged` rumble only during melee ✓.

Edge: `updateHud` before armies exist? boot order: newBattle before first frame ✓.

resize before newBattle: palette undefined → skip bg build ✓; then newBattle builds. ✓

`redrawStamps` in resize when palette exists ✓.

Also `window.addEventListener('resize',resize)`.

DUSTFILL initial '' until newBattle — set before first render ✓.

OK writing final.

Also small thing: `#tally` bottom center may overlap on tiny screens — fine.

Also add `user-select:none` body.

Now produce the final file.

Let me write the whole thing in one pass, being extra careful with matching braces and names. I'll mentally lint as I go.

Additional careful point: in `step`, when `newBattle()` is called mid-step (fading end), after it we `return` — but `newBattle` uses `dcX.setTransform(DPR,...)` — DPR current ✓.

In `newBattle`, `makeGround` resets texC size — texX transform default identity ✓ coordinates in tex space.

In buildBackground, use bgX.setTransform(DPR,...) then all drawing in css px ✓. drawImage(texC...) source coords in tex pixels ✓ dest css px ✓.

hillLayer defined before use (function hoisting ✓ since function declarations).

Let me write out. (Also `const dl=[]`.)

Counting `eng` uses post-increment after branches — placed `if(!u.flee){if(u.side)f1++;else f0++;}` at loop end ✓; eng incremented in fight branch ✓.

`engaged` global assigned; rumble uses engaged.

Also don't forget `u.rt` removed everywhere.

In sensing, `nd2` initial 1e12 ✓.

Potential subtle bug: **candidate switch `nd2<cd2*0.5`** when cur exists but candidate much closer — good.

When curOK but nd2 large (no enemy in sense) and cd2<3600 keep chasing cur beyond sense — cur could be fleeing far — chase across field ✓ capped by 3600 (60u) drop.

Chasing fleeing: chaser speed 1.95 vs runner 2.25 — gap grows; when >60 tgt dropped → advance toward centroid (fleeing centroid) → re-approach ✓ perpetual pursuit until despawn ✓.

**During 'end' (victory) chasers stop (active false) — fleeing stragglers exit — counts finalize.** ✓

Write final HTML now. Also include `overflow:hidden` etc.

For the explanation: describe architecture: fixed timestep-ish rAF, uniform grid 48px cells, ring-buffer decals, trapezoid projection, phases, auto-restart. Keep concise.

One more decision: unit count 520/side ✓ "at least 500".

Also double-check FIGHT2=12²=144, BREAK2=15.5²≈240 ✓ constants.

SEPR: separation radius 8.6 → SEP2≈74.

Final code below.

Also careful: in act branch for flee, when u.fl>0 → they stand; separation still applies; ok.

And `u.fl` initial 0; `if(u.fl>0){u.fl-=dt; if(u.fl<=0)u.flee=true;}` — after convert, subsequent frames go to else ✓.

Also broken units that were mid-`u.fight` — fight branch requires !u.flee — flee true → flee branch ✓ disengage.

**killUnit called via hurt inside loop; despawn via flee uses `continue` — but note the f0/f1 count happens after movement; despawn path `continue` skips count — but we already decremented counts there ✓ and unit won't be counted next frame (alive false) ✓.**

**Now truly write.**

Also one more flourish for signature moment: on clash, besides shake+dust, add a quick white flash overlay? Subtle: flash=0.35 decay drawn as full-rect fill 'rgba(240,235,215,flash)'. Add flash variable; on firstClash flash=0.28; decay flash-=dt*1.4; draw after particles before overlay. Cheap & punchy. ✓

Draw: `if(flash>0){ctx.globalAlpha=Math.max(0,flash);ctx.fillStyle='#f5eeda';ctx.fillRect(...);ctx.globalAlpha=1;}` within shaken transform — fine.

Also flash on battle end? no.

Alright — final file:  — writing now, complete and careful.

Also remember comment language: English (user English) ✓.

Let me count roughly the melee region density vs grid: ok.

**After writing, quick mental smoke test of first frames:**
- boot: grain made, resize (palette undefined → only sizes; note buildBackground skipped), newBattle: palette set, ground made, bg built, armies built, HUD set, fader off next frames.
- frame: step: phase intro; t<1.05 → no advance msg yet; grid rebuild; centroids; active false → idle; render: bg, decal(empty), particles none, units drawn standing (sword idle sway, banners wave) ✓ nice muster tableau.
- t>1.05 → advance message; units march; gap closes; charge at ~2.5s; clash ~4.5s; melee; rout ~18-30s; victory; fade; new battle. ✓

Also confirm bar initial width 100% ✓ and counters set.

Potential visual check: units at intro standing in ranks — with separations they jiggle slightly — organic ✓.

Done planning; write final.

Ah wait — one bug candidate: in `step`, I latch charging only in phase 'advance'. If a unit makes first contact while phase 'charge' → sets phase 'clash' inside attack ✓.

Also make sure `setPhase` exists before first call (function decl hoisted ✓).

Another: `verdict.classList.add('show')` — CSS transition ✓.

**`fmt` input integer ✓.**

**Bar `i` elements: css `.abar i{...}` uses `<i>` ✓.**

Also `#armyR .abar i{left:auto;right:0}` ✓.

Writing final code — GO.

After code, explanation: mention grid hashing, painter's sort, trapezoid projection, persistent decal ring, morale rout, auto loop; note it starts instantly and the full arc (advance→charge→clash→melee→rout→victory) lands within ~30s, then loops.