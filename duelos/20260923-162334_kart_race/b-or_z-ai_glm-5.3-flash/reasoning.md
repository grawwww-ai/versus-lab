Let me plan this carefully. This is a big task: a self-running Mario Kart-style race in three.js, single HTML file, no external resources.

Key components:

1. **Track**: closed circuit with curves and hills. I'll define a centerline via a CatmullRomCurve3 (closed) with control points including elevation changes. Then build a ribbon mesh for the road (extruded across a width), plus kerbs (red/white striped strips along edges on curves), plus start/finish line, checkered pattern maybe via vertex colors or a canvas texture.

Since no external images, I can generate textures procedurally with canvas (that's fine — no external resources, all inline). Canvas textures for asphalt noise, kerb stripes, grass, checkered start line, billboards, etc.

2. **Scenery**: trees (cone + cylinder), grandstands near start, banners/billboards, floating hot air balloons maybe, clouds, mountains far away, item boxes? Keep it performant but lively. Decorated scenery: trees, grandstand,广告牌 with canvas text, clouds, starting gate arch.

3. **Karts**: 6 karts. Each kart: body (box + cockpit), driver (sphere head with cap, simple body), 4 wheels that rotate with speed and front wheels steer. Drifting: when turning hard, kart yaw offsets from velocity direction, tilt/roll, spawn skid particles (dust) at rear wheels. Dust particles: Points or small sprite planes. I'll implement a simple particle pool with small planes/points using canvas circle texture.

4. **AI**: karts follow the racing line (centerline with slight lateral offsets per kart), target a point ahead on the curve, steer toward it, throttle control based on upcoming curvature, drift when curvature high, collision avoidance/overtaking: simple lateral offset changes when a kart is ahead nearby — shift target offset to the side with room. Kart-to-kart soft collision (push apart).

Physics: simple arcade. Each kart has position, heading, speed. Accelerate toward max speed (varies per kart slightly), brake for corners based on angle of curve ahead. Steering: turn rate toward target heading. Drift state: when |steer| large and speed high, increase yaw rate, reduce grip slightly, spawn particles, kart visual yaw lags.

Lateral position: karts are free-moving on a plane with height sampled from track height function. To keep them on track, the racing line target keeps them on; plus if off track (distance from centerline > half width), slow down (grass) and steer back.

I need closest-point-on-curve queries. Precompute a dense polyline of the curve (e.g., 1000 samples with position, tangent, normal (lateral), curvature, elevation). Then nearest-sample lookup with local search per kart per frame (search near previous index). That's efficient.

Track progress metric for position ranking: lap * trackLength + distanceAlong. Ranking computed each frame, display 1st–6th with names and colors.

Lap counting: when progress crosses start line (sample index wraps from high to low) with forward direction, increment lap. Race lasts e.g. 4 laps? "at least two laps". I'll do 4 laps and then loop (restart) — or just continue infinitely by resetting laps. Actually "may loop or continue after that". I'll make it 5 laps then restart automatically with countdown again. Simpler: infinite race, but show lap counter up to e.g. 5 then restart. Let me do: LAPS = 4; after finish, karts keep driving (cooldown), then after all finish or a timer, restart with countdown. Simpler: after leader completes LAPS, show "FINISH", keep karts driving for a few seconds, then reset and countdown again. That gives a nice loop.

Actually simplest robust: infinite laps but lap counter shows min(lap, LAPS). Hmm, a restart with countdown is a nice touch and shows the countdown feature repeatedly for a recording loop. Let's do: total race LAPS=3 (>=2), after leader finishes, brief "FINISH" banner, 3s later reset all karts to grid, countdown 3-2-1-GO, race again. Recording window 30s: countdown ~3.5s, then ~26s of racing covering maybe 2 laps depending on track length. Let me make lap time ~10-13s so 2 laps happen within 30s. Track length maybe ~600-700 units, speed ~35-45 u/s → lap ~15s. Hmm. Let's size track ~450m, avg speed ~40 → lap ~11s. Two laps by ~26s. Good. Or 4 laps of shorter track. Let's aim lap ~9-11s: track length ~380 with speeds ~38.

Let me define control points for a fun circuit with hills:

Something like a rounded rectangle with an S-curve and elevation:

```
const pts = [
  (0, 0, 90), (60, 0, 95), (110, 2, 70), (130, 5, 20), (125, 8, -35),
  (95, 10, -70), (40, 8, -85), (-15, 5, -95), (-60, 2, -70), (-75, 0, -20),
  (-60, 0, 30), (-90, 3, 70)... 
```

Hmm, let me just design a closed loop, roughly 400-500 units perimeter. I'll use CatmullRomCurve3 closed with ~10-14 points including y variation (0 to 8). I'll verify mentally the shape stays non-self-intersecting: keep it convex-ish with one inward pinch (hairpin-ish) for interest.

Points (x, y, z), closed:
- P0 (0, 0, 100) start/finish on a straight
- P1 (80, 0, 100)
- P2 (130, 3, 60) 
- P3 (140, 6, 0)
- P4 (110, 8, -50)
- P5 (55, 9, -75)
- P6 (0, 7, -60)  (crest hill)
- P7 (-45, 5, -85)
- P8 (-95, 3, -70)
- P9 (-115, 1, -15)
- P10 (-95, 0, 45)
- P11 (-40, 0, 85)

That's a loop going clockwise? Let's check direction: from (0,100) to (80,100) → +x; then to (130,60) → turning; to (140,0); to (110,-50); (55,-75); (0,-60) — this pinches inward (z increases from -75 to -60 while x same) creating an S; then (-45,-85), (-95,-70), (-115,-15), (-95,45), (-40,85), back to (0,100). This is counterclockwise? Going right along top (z=100 is "south"? whatever), then down the right side, left along bottom with a wiggle, up the left side. It's a closed loop, no self intersection. The wiggle at P6 gives an S-curve/chicane. Good.

Perimeter estimate: roughly width ~255 (x from -115 to 140), height ~185 (z -85 to 100). Loop perimeter ~ maybe 700? Hmm that might be too long. Let's compute rough: top straight ~ (0,100)→(80,100): 80. (80,100)→(130,60): √(50²+40²)=64. →(140,0): √(10²+60²)=61. →(110,-50): √(30²+50²)=58. →(55,-75): √(55²+25²)=60. →(0,-60): √(55²+15²)=57. →(-45,-85): √(45²+25²)=51. →(-95,-70): √(50²+15²)=52. →(-115,-15): √(20²+55²)=58. →(-95,45): √(20²+60²)=63. →(-40,85): √(55²+40²)=68. →(0,100): √(40²+15²)=43. Total ≈ 715. With avg speed 40 → lap 18s. Too long for 2 laps in 26s. Options: scale down by 0.7 → ~500 length, lap ~12.5s at 40 u/s. Or increase speeds to ~55 → lap ~13s at 715. Karts at 55 u/s with track width ~14 looks fine if kart scale ~2. Let's scale coordinates by 0.72 → length ~515, speed ~45-52 → lap ~10.5s. Two laps in ~21s after countdown. 

Actually kart speeds: max ~48, corners slow to ~26. Average maybe 40 → lap 13s. Two laps by 3.5+26 = ~29.5s. Cutting close. Let me scale to 0.65 → length ~465, avg 38 → lap 12.2s. Countdown 3.2s + 2 laps = 27.6s. OK. Or LAPS such that we see at least 2 laps within 30s; also the window is "show everything important" — countdown, positions, laps, drift, overtake, camera cut. Fine. I'll make track scale ~0.68 and max speeds ~46-50.

Alternatively make the countdown faster: 3-2-1 with 0.8s each = 2.4s + GO. Then racing 27s → 2 laps at 13s each. 

Road width: 12 (half-width 6). Karts ~1.6 wide. Fine.

5. **Cameras**: chase camera on leader: position behind kart based on kart heading, smooth lerp; occasional cuts to trackside cameras: pick from a set of fixed camera positions around track (corners), lookAt leader; hold 3-4s, then back to chase. Cut logic: every 6-9s, chance to switch to trackside for 2.5-3.5s. Also ensure within first 30s at least one trackside cut happens. I'll schedule: cut at t=9s to trackside, t=12.5 back, then random every 7±2s alternate. Camera transition: hard cut (that's "cuts occasionally"), maybe brief. Hard cut is fine and stylish.

Chase camera also should look nice over hills: position = kart pos - forward*d + up*h, lookAt kart pos + forward*look. Smooth with damping.

6. **HUD**: Position list (1st-6th) with colored chips + names + gap/lap info; lap counter "LAP 2/3"; countdown overlay big numbers; speed maybe not needed; race timer. Style: I want an authored look — a bold arcade-style HUD, custom typography via CSS (no external fonts allowed! "no external resources, CDNs, fonts or images" — so only system fonts... but I prefer to avoid boring defaults; I can use a stacked font-family like "Trebuchet MS", or draw text with canvas/SVG. Since no external fonts, I'll craft HUD with heavy weights, letter-spacing, skew/italic transforms to get racing feel, using system fonts creatively (e.g., `font-family: 'Arial Black', 'Avenir Next', Futura, sans-serif` — Arial Black is a system font on most machines and has a chunky look; combined with skew and outlines it reads as arcade). I'll avoid gradients as decoration; use flat bold colors: cream/paper background chips? HUD over 3D: dark translucent panels with high-contrast text, one accent color (racing red/orange?). I'll go with a " retro racing" palette: ink navy panels? Let me choose: background sky a warm light blue, grass green, asphalt gray. HUD: dark charcoal panels (#15181d with slight alpha), text off-white, accent = tangerine (#ff5a1f) or racing yellow. Number styling with skewed italic. That's tasteful.

The three.js scene background: I'll use a sky color + fog, sun light + hemisphere. Maybe a subtle sky dome with canvas gradient... gradient in sky is natural (it's a sky, not decoration). A vertical sky gradient is legitimate for atmosphere; I'll keep it subtle (light horizon haze). That's environmental realism, fine.

7. **Countdown**: 3,2,1,GO with big overlay numbers animating (scale punch). Start lights on the start arch maybe: three lights turning red then green. Nice touch: gantry with 3 light boxes.

8. **Particles**: dust/skid. Implementation: a pool of ~300 sprite planes (or THREE.Points with per-point size/alpha). Simpler: THREE.Points with custom shader? To keep it simpler and robust, use many small meshes is expensive. Use THREE.Sprite? Sprites are individual draw calls — 300 sprites = 300 draw calls, too many. Use THREE.Points with a PointsMaterial + canvas texture, per-vertex color, and set position/alpha via attribute; fade by shrinking? PointsMaterial has global size. Better: custom ShaderMaterial for points with attributes size, alpha, and a soft circle texture generated on canvas. That's ~40 lines. Fine, I'll do a small shader.

Skid marks on road: could add — dark quads placed under rear wheels when drifting. Nice detail: pool of small dark plane meshes laid on road, fading. That adds a lot of "drift" readability. I'll add a skid mark pool (~200 quads, reused ring buffer) — as InstancedMesh? Simpler: a single BufferGeometry with dynamic quads... Simplest robust: InstancedMesh with 400 instances, each instance a small dark rounded quad; set matrix per spawn; fade via instance color? Fading per-instance requires instanceColor which multiplies material color — with a black material and white texture? Let's do: material black semi-transparent; opacity global. Instead of fading individually, just overwrite oldest. Slight z-fighting handled with polygonOffset and y = road+0.02. Each skid segment: quad oriented along wheel motion, length ~0.8. Spawn every frame while drifting at rear wheel positions. Ring buffer of 600 instances. That works and is cheap (one draw call).

Dust particles: also could be instanced or points. Points shader is easiest with per-particle alpha & size. I'll write a tiny ShaderMaterial.

Also exhaust puffs? skip. Confetti at finish? Maybe skip for scope; but signature moment: drifting karts with skid marks + dust + camera cuts + countdown lights. Maybe add "wahoo" — no audio (no external resources; WebAudio generated beeps possible! Countdown beeps via WebAudio oscillator — nice touch, no assets needed. But autoplay policies: audio context may start suspended without user gesture. Recording may not have gesture. I'll add beeps but resume on first pointer/keydown; if suspended, silent. Optional; low cost. I'll include it guarded.)

9. **Kart model**: build with primitives:
- chassis: rounded box (BoxGeometry with bevel look via multiple boxes), color per kart.
- front bumper, rear bumper.
- seat + driver: torso (box), head (sphere) with helmet color + visor (dark box/strip), hands? keep simple.
- steering wheel: torus.
- 4 wheels: cylinder rotated, dark gray with hubcap; front wheels in steering groups to yaw.
- exhaust pipes small cylinders.
- Shadow: fake blob shadow (dark circle plane under kart) — cheaper than real shadows for 6 karts; but directional light shadows for the whole scene could be nice... Shadow map over 500-unit track is expensive/blurry. I'll use blob shadows for karts and maybe no scene shadows, but light the scene well (hemisphere + directional with vertex-lit materials? Lambert/Phong fine). Trees could have blob shadows too — skip, keep clean. Actually a directional shadow with tight-follow on leader could be complex. Blob shadows only. Good.

Kart tilt: roll into corners (lean out or in? karts lean outward slightly or drift-lean inward), pitch on accel/brake, and hop on drift initiation? Mario Kart drift hop — small hop when entering drift! Fun detail: y bounce. I'll add small hop when drift starts.

Wheel steering: front wheel group yaw = steering angle; wheels spin by speed/radius.

Driver head turns toward steering slightly; driver leans in drift.

10. **AI details**:

Per kart state: `pos` (Vector3), `heading` (yaw), `speed`, `steer` (current front angle), `drift` (-1/0/1), `lap`, `progress`, `trackIdx` (nearest sample), `laneOffset` (target lateral), `laneCurrent`.

Update (fixed dt or clamped):
- Find nearest sample index near previous (search ±30 samples).
- Look ahead: sample at idx + lookahead(speed) → target point = center + lateral * laneOffset(targetIdx). Lookahead distance grows with speed (e.g., 6 + speed*0.35).
- Desired heading = atan2 of (target - pos).
- Steering: angleDiff → steer input = clamp(diff * k). Front wheel visual angle = steer * 0.5.
- Speed control: compute max cornering speed from curvature ahead: sample curvature at idx + K (a few probes ahead: curvMax over next ~35 units). vmax = sqrt(a_lat / curvature) with a_lat ~ 55 (grippy arcade). If speed > vmax → brake; else accelerate. Also grass penalty: if |lateral| > roadHalf - kartHalf → cap speed to 12 and add bumpiness.
- Apply: heading += steerInput * turnRate * dt * speedFactor; speed += accel/brake; pos += forward * speed * dt. Then set y from track height at nearest sample (blend) — better: y sampled from track surface at (projected point). Compute lateral distance from centerline; road is flat across width (no banking) so y = sample.y (use nearest sample y; smooth by lerp). Also add banking? skip.
- Drift: if |steerInput| > 0.55 && speed > 20 && onRoad → drift = sign; while drifting: extra yaw rate (drift yaw = steerInput * base + drift * extra), visual body yaw offset ~ 0.45 rad opposite/into, reduced accel, dust particles + skid marks, slight speed decay. Exit drift when steerInput small or speed < 15. Mario Kart drifts let you hold tighter line; I'll model: during drift, kart's heading changes more than velocity direction (velocity follows heading with lag) → produces slide angle. Simplify: maintain `slideAngle` that eases toward drift target; movement direction = heading rotated by -slideAngle*0.6. Visual body yaw = heading + slideAngle*0.9 (kart points into the slide). Looks like drifting.
- Overtaking/avoidance: each kart checks karts ahead within 12 units and |lateralDiff| < 2.2 → choose side: prefer inside line for overtaking; set desired laneOffset offset to pass (±2.2), and if very close, limit speed slightly to avoid ramming (unless slightly faster). Also soft collision: if dist < 1.9, push apart along diff vector, small speed penalty for rear kart.
- Also slight rubber-banding: karts behind leader get small speed boost (× up to 1.06), leader slight −2%? Keep subtle so it's fair-ish but keeps pack together for overtakes. I'll add gentle catch-up: if progressDiff to leader > 30 → boost 1.05.
- Per-kart personality: maxSpeed 44–50, cornerSkill (a_lat 45–62), lineOffsetBase random -1.8..1.8, aggression.

Starting grid: 6 karts in 2 columns × 3 rows behind start line, staggered; small random.

Race positions: sort by (lap, progress along lap, distance to next... ) use totalDist = lap*trackLen + s (s = arc length at nearest sample + lateral adjust). Ties fine.

Lap increments when crossing sample index wrap: track sPrev → sNew where s from arc-length param; if sPrev > L*0.9 && sNew < L*0.1 → lap++. Only count if moving forward. Start karts just behind line with lap = 0? Show "LAP 1/3" at start. Let lap counter display = min(lap+1, LAPS) until finished. Karts start with progress slightly negative (grid behind line): set lap = 0 and s near L - gridOffset... That complicates wrap logic. Alternative: define progress s as arc distance from start line; grid positions have s = L - smallOffset → i.e., s near end of lap 0. When crossing start, sPrev ~ L-5 → sNew ~ 2 → wrap triggers lap 0→1. Display lap = clamp(lap, 1, LAPS)? Hmm: before crossing, lap=0, display "LAP 1/3" as max(1, lap) — but they haven't crossed line... In racing, grid is before line and crossing starts lap 1 — display "LAP 1/3" from the start is standard in games. After 1st crossing lap=1 (still lap 1). After 2nd crossing lap=2 → "LAP 2/3". After lap 3 crossing (lap=3... wait crossing from lap2→3 shows LAP 3; when leader crosses with lap becoming 4 → finish). Let me define lap starts at 0; on wrap lap++; display: min(max(lap,1)... hmm before first crossing lap=0 → show LAP 1/3; after first crossing lap=1 → LAP 1? No — crossing the line the first time begins lap 1 which was already displayed. Standard arcade: lap counter = laps completed + 1. Grid is "lap 0 completed" → "LAP 1". After completing lap 1 → "LAP 2". So display = lapCompleted+1 where lapCompleted counts line crossings... but crossing at race start from grid shouldn't count as completing a lap. Ugh — grid is before the line; crossing it at start would increment. Solution: place grid just AFTER logic: initialize lapCompleted = 0, and grid s values are small negative → represent as s = L - offset with lap = -1? Then crossing start increments to lap = 0 (start of lap 1). Display = lap + 1 clamped ≥1. Let's do that: each kart lap starts at -1; s initial = L - gridOffset (i.e., behind line in arc terms). On wrap: lap++. Display lap# = min(lap+1, LAPS). Race finishes for a kart when lap reaches LAPS (i.e., crossing line after completing lap LAPS) → finished flag. Leader finishing triggers finish sequence.

totalProgress for ranking = lap * L + s. With lap=-1 initially and s near L: total = -L + (L-off) = -off. 

11. **Track mesh construction**:

Samples: N=600 points along curve (getSpacedPoints or manual). For each: pos, tangent (normalized, from neighbors), lateral = perpendicular in XZ (tangent cross up... but track has slopes; use up = (0,1,0) so lateral = (tz? ) perpendicular of tangent projected: lat = normalize(cross(up, tangent)) → gives left vector. Curvature: signed curvature via heading angle change per arc length, smoothed.

Road geometry: for each sample, left = pos + lat*halfW, right = pos - lat*halfW, y same as pos.y (flat crown) — build triangle strip with UVs (u across, v = arclength/texLen). Asphalt texture: canvas 256: dark gray with noise speckles + subtle center wear lines? Keep: noise + faint tire darkening at racing line? Simple noise. RepeatWrapping, v repeat every ~8 units.

Kerbs: strips outside road edges where |curvature| > threshold: width ~1.1, painted red/white via texture stripes along length. Build as separate ribbons following edge, slightly raised (y +0.06) with slight outward slope. To avoid complex segmenting, build kerb ribbon for the entire loop on both sides but color stripes only... simpler to build full-loop kerb strips on both sides (looks fine everywhere, Mario Kart tracks often have full kerbs). I'll add kerbs along whole track both sides — actually that's a lot of red/white; real MK does that often. OK full loop kerbs, texture repeating stripes.

Grass: big ground plane at y = -0.02 (but track has hills up to y≈6-7... ground plane can't follow). Options: make ground follow track height near track and fall off to base level far away. Build a wide ground skirt ribbon: for each sample, vertices at lateral offsets: [-80, -30, -12(halfW+kerb), ... symmetric] with y: trackY at road edge, then blend down to terrain base 0 beyond ~35 units. Also add gentle noise to far terrain. Plus a huge flat ground plane at y = -0.5 for the far background colored grass. The skirt ribbons (say offsets: 6, 9(kerb), 14, 24, 45, 80) each side with heights easing from trackY to terrainY(=0 or slight noise). That keeps track sitting on grassy berm. Grass texture: canvas green noise. This skirt approach is standard.

Track elevation: control points y up to ~6-7 after scaling (scale 0.68: y up to ~6). Hills visible via skirt following. Camera chase looks fine.

Start/finish: checkered strip across road at s=0: a quad ribbon segment with checker canvas texture, plus overhead gantry: two pillars + banner box with canvas text "LAP" ... text "START" or custom "GRAN TURBINO"? I'll write something like "PIXEL GP" — name the race "POLY PEAK GP" or "CIRCUIT ROSSO". Let me brand it "CARTA VELOCE GP"? Keep tasteful: "SUNSET CIRCUIT — GRAND PRIX". I'll pick track name "Crestline GP". HUD title small.

Billboards/scenery along track: 
- Trees: cone pines + round oaks, scattered outside track using lateral offset 10–40, avoiding road: sample random s, side, offset; y from skirt approx (use trackY at that s blended by offset). Count ~120 trees. Use InstancedMesh for trunk & foliage (two instanced meshes) for perf.
- Grandstand near start: box tiers with colored crowd dots (canvas texture) — place along main straight outside.
- Advert boards: low walls with canvas textures (fun fake sponsors: "PISTON", "TURBO", "1-UP", "SHINE SPRITES"? avoid IP... generic: "VELOCE", "NITRO COLA", "APEX", "KUMO TYRES"). Place a few along corners facing track. Use plane with canvas texture text.
- Arches/banner over track at 1-2 places? Start gantry enough, maybe one more arch mid-track. Add torii-like arch with "SECTOR 2"? Fine, one extra arch.
- Clouds: few flattened white spheres/groups drifting slowly.
- Balloon: one hot air balloon floating (nice skyline moment).
- Mountains: distant ring of large cones (low poly) at radius ~600, muted color, behind fog.
- Item boxes? Mario Kart style rotating cube with "?" — could be a nice touch but karts don't use items; skip to avoid confusion. Maybe a few spinning "?" boxes as decoration that karts pass through with a little sparkle? Scope control — skip.

Crowd sounds? no.

12. **Positions HUD**: left side vertical list: rows "1 ▸ FLAMPIO" with color chip. Update ~5 times/sec. Also top center: "LAP 2/3" + timer; right: current camera label ("CHASE CAM" / "T-CAM 3")? Nice broadcast touch. Keep minimal.

Names & colors (6): 
- ROSSO (red #e23b2e)
- AZZURRO (blue #2e7de0)? avoid default blue vibe... it's a kart livery, fine but I'll pick distinct palette: 
  1. "Pepper" red #e0402f
  2. "Minty" teal #2fa88a
  3. "Bumble" yellow #f2b705
  4. "Cobalt" ... use #3b6fd4? It's livery not UI, acceptable. Maybe "Blueberry" #3e63c4.
  5. "Grape" purple #8a4fc9? purple as kart color ok.
  6. "Snow" white #f2f3f5 with dark trim? White kart reads well.
Names: PEPPER, MINTY, BUMBLE, BERRY, GRAPE, POWDER. Cute Mario-ish. Drivers with helmet colors matching.

13. **Countdown lights** on gantry: 3 spheres, red on at 3,2,1... standard F1: lights on then all off = go. I'll do: show "3" light1 red, "2" light2, "1" light3, "GO" → green flash + karts go. Overlay number synchronized.

14. **Camera system**:
- Modes: CHASE, TRACKSIDE.
- Chase: compute desired pos = kartPos - forward*7.5 + up*3.4 (forward = kart heading dir, not velocity, but blend slide for style). Smooth position with exp damping (e.g., lerp factor 1 - exp(-dt*4)). lookAt target = kartPos + forward*4 + up*1.2, also smoothed. FOV maybe widen with speed slightly (55 → 62). Nice.
- Trackside cams: pick points: predefined list computed from track samples: choose ~8 spots at outside of corners, offset ~14 from center, y = trackY + 4. Choose ones near action. Cut selection: pick cam whose view of leader is good (distance < 120). Hold 3s. Also pan (lookAt leader continuously) — broadcast feel. Hard cut in/out.
- Cut scheduling: nextCut = now + 6 + rnd*4; on cut, if in chase and rnd < 0.55 → trackside for 2.5-3.5s then back to chase. Ensure first special cut around t≈8-10s after GO.
- During countdown: cinematic — slow orbit around grid / front of grid camera showing karts. Nice: start with a pan across the grid then settle behind leader? Simple: countdown camera = slowly moving dolly along the grid side, then cut to chase at GO. I'll do: camera orbits around the pack center (radius 14, height 4) during countdown, then at GO switch to chase. Signature moment ✓.

15. **Finish/loop**: when leader lap completes LAPS (3): banner "FINISH" + winner name, karts continue (AI keeps driving, slow to 70%?), confetti? After 4s → fade overlay? then reset: karts to grid, countdown again. I'll implement raceState: 'countdown' | 'racing' | 'finished' → after 5s reset to countdown. HUD shows final order briefly.

16. **Performance**: instanced trees, one points cloud for dust, instanced skids, merged geometry for road/skirt/kerbs. 6 karts × ~20 meshes = fine.

Renderer: antialias, setPixelRatio min(devicePixelRatio, 2), fog, ACES tone mapping? ACESFilmic gives nice color. sRGB output. r186: renderer.outputColorSpace = THREE.SRGBColorSpace default. Use MeshLambert/MeshStandard? Standard with low roughness variety; Lambert cheaper but Standard fine with few lights: DirectionalLight (sun, warm) + HemisphereLight (sky/ground). intensity tuned for r186 (useLegacyLights false default; physically based intensities: dir ~2.5, hemi ~0.9? For r155+, light intensity units changed; common values: hemi 1.0, dir 2.0-3.0 works with ACES).

Let me also handle canvas texture colorspace: tex.colorSpace = THREE.SRGBColorSpace.

17. **Curvature-based racing line**: nice racing line: offset toward outside at entry... too complex. Simpler: AI target lane = clamp(-curvatureAhead * k, -1, 1) * (halfW - 1.5) → karts hug inside of corners (apex-cutting): offset = -sign(curv) * magnitude where curv sign relates to turn direction. With lateral defined as left normal, signed curvature k>0 means turning left → apex on left → offset toward left = +? If lateral vector = left, offset positive = left. Turning left → apex left → laneOffset = +mag * smooth(curv*k). I'll compute smoothed curvature ahead and set lane = clamp(k*Kmax) * (halfW-2.0), plus personality offset and avoidance offset. This yields natural-looking lines. Lookahead distance ~ speed * 0.5 + 4 for lane target too (so they move to outside before corner... simple version just goes to apex; without outside-in it still looks decent). Maybe add small anticipation: use curvature at idx + lookDist, and blend. Good enough.

Corner speed: vmax = sqrt(aLat / |k|), clamp to maxSpeed. Look ahead minimum over window idx..idx+window for braking. Braking distance: simple: probe vmax at several ahead distances (10,20,30,45) and require speed ≤ sqrt(v² + 2*a_brake*d)? Proper: allowed = min over probes of sqrt(vmax_at_probe² + 2*brakeDecel*dist). Then throttle/brake toward allowed. brakeDecel ~ 30, accel ~ 18-22. This gives realistic braking into corners. 

Turn rate: kart heading turn rate limited: maxYawRate = grip: e.g., 2.2 rad/s at low speed, reduce with speed? Arcade: yawRate = steer * clamp( (9 / max(speed,5)) * something...). Let's do: desiredYaw = angleDiff; yawRate limit = 2.6 * clamp(1.2 - speed/120, 0.55, 1.1)? Simpler: yawLimit = 2.4 * (aLat/ (speed*speed + 60))? Physical: yawRate max = aLat / speed (can't exceed lateral accel). yawMax = min(2.8, aLat/max(speed,4)). Then steer toward desired heading with that limit. During drift add extra yaw authority (slide allows tighter rotation). Good.

Position integration: velocity direction = heading rotated by slideAngle; pos += dir * speed*dt. slideAngle eases to driftSlide (0.5 rad * driftIntensity) else 0. During drift also speed decays a bit and lateral grip reduced meaning kart travels wider — emerges from slideAngle geometry: if slide rotates velocity away from heading... In drift, real kart: velocity lags heading. Setting movement dir = heading - slide*sign? If drifting through left turn (heading turning left), kart nose points left of velocity → velocity = heading rotated right by slide. So moveDir = heading rotated by -slide (slide>0 for left drift). Visual yaw = heading + slide*0.6? Hmm: nose points INTO turn: visualYaw = heading + slide*? Let's define: during left drift, moveDirYaw = heading - slide; body yaw = heading (kart heading = nose). Actually simpler: keep `heading` as NOSE direction. movement direction = heading rotated by -slide (slide ∈ [0, 0.45]). Then AI steering controls heading; the slide makes kart run wider, which the AI compensates by pointing more into the corner — emergent drift look ✓. Skids when slide > 0.25.

Drift trigger: when |steerInput|>0.6 && speed>24 && curvatureAtKart significant → enter drift (with hop). Maintain while turning; release when steer relaxes or speed<16 → slide eases to 0.

Overtake: with laneOffsets shifting ±2.5 and soft collisions, overtakes will happen especially with rubber-band. Also stagger base lanes per personality + corner line — plenty of position swaps. I'll add explicit side-pick: if kart ahead within 10 && closing: targetLane = clamp(aheadKart.currentLane ± 2.6 chosen by side with more room (prefer inside of upcoming corner)). 

18. **Particles (dust)**: Points pool 400. Attributes: position (updated CPU), size, alpha, color (dust tan on road? On grass green-brown). Spawn while drifting at rear wheels: pos + rand, vel slight up/out, life 0.6-1s, size grows. Also grass spray when off-road. Update CPU each frame writing arrays, draw with shader: gl_PointSize = size * (300/dist) etc. Texture: radial soft circle canvas. blending normal, depthWrite false.

19. **Skid marks**: InstancedMesh plane 0.28×1.0, material black opacity 0.35, 500 instances ring buffer. Spawn while drift at each rear wheel: quaternion aligned to movement dir, y = roadY+0.02 (+ follow slope: set from sample y). Place both rear wheels every other frame. Ring buffer index.

Ensure skid quads follow hill slope: orient to track normal? Just flat horizontal at sample y is fine for gentle slopes; use track surface y at kart pos.

20. **HUD design**: 

- Top-left: leaderboard panel: rows with rank number (skewed bold), color chip, name; leader row highlighted; live updating. Panel: dark #101216cc, border-left accent? Racing style: rows as slanted parallelogram chips. 
- Top-right: LAP x/3 big + race clock.
- Bottom-right: camera tag "ONBOARD • P1 PEPPER" or "T-CAM 2" small.
- Center overlay: countdown numbers with punch animation; "GO!" ; FINISH banner with winner.
- Bottom-left maybe minimap? A small SVG/canvas minimap of track with dots for karts — great broadcast feature and shows circuit shape! Draw track outline once to a small canvas (from samples), then per frame draw dots. Cheap and impressive. I'll include minimap bottom-left (canvas 150×150), rotated? static top-down with dots colored per kart + S/F marker.

That's a strong HUD. Fonts: use stack: `Futura, "Trebuchet MS", "Segoe UI", sans-serif` with heavy weights, italic skew, letterspacing. Numbers with `font-variant-numeric: tabular-nums`.

21. **Audio**: tiny WebAudio: countdown beeps (3 low, 1 high), soft engine hum? Engine hum per kart via oscillator could be messy; skip engines, keep beeps only, resumed on user gesture if available. Actually recording without gesture → no sound anyway. Include guarded.

Let me now write the code carefully. Structure:

```html
<!DOCTYPE html>
<html><head><meta charset><meta viewport><title>...</title>
<style>...</style></head>
<body>
<div id="hud"> ... </div>
<script type="module">
import * as THREE from 'three';
// maybe no addons needed (no OrbitControls needed since auto cameras). 
...
</script>
</body></html>
```

No controls needed. Import only three.

Let me write utilities:

```js
const rand=(a,b)=>a+Math.random()*(b-a);
```

**Track definition:**

```js
const CP = [
 [0,0,100],[80,0,100],[132,3,62],[142,6,2],[112,8,-52],
 [56,9,-78],[0,7,-62],[-46,5,-88],[-98,3,-72],[-118,1,-16],
 [-96,0,46],[-42,0,86]
].map(p=>new THREE.Vector3(p[0]*S, p[1]*S, p[2]*S)); // S=0.72
```

Wait, scaling y too flattens hills: y*0.72 → max 6.5. fine. Actually keep y scale maybe 1.0 for drama: y values [0,3,6,8,9,7,5,3,1,0...] *0.9. Let me scale xz by 0.72 and y by 1.0: hills up to 9 → noticeable. Track slope over ~50 units horizontal, 9 rise — fine.

curve = new THREE.CatmullRomCurve3(CP, true, 'catmullrom', 0.5);

Samples: N=700; use curve.getSpacedPoints(N) → equally spaced by arclength approx. For each i: p = pts[i]; tangent from pts[i+1]-pts[i-1]; left = cross(up, tangent).normalize() — careful orientation: cross((0,1,0), t) gives vector perpendicular pointing... for t=(1,0,0): cross(up,t) = (0,1,0)×(1,0,0) = (1*0-0*0, 0*1-0*0... compute: up×t = (uy*tz - uz*ty, uz*tx - ux*tz, ux*ty - uy*tx) = (1*0-0*0, 0*1-0*0, 0*0-1*1) = (0,0,-1). So left = -z when heading +x. In three.js coords, if we look from +y down with +x right and +z toward viewer... heading +x, left is -z? Depends orientation; doesn't matter—call it `side` vector; consistent sign for curvature.

Curvature signed: heading angle h_i = atan2(t.x, t.z)? Use yaw = atan2(t.x, t.z). dYaw wrapped / ds → k. Then smooth k with box filter width ~15 samples, plus stronger smoothing for lane target.

Arc length per sample ds ≈ L/N.

Road half width: 7 (road 14 wide). Karts lane within ±5.

**Build road geometry:**

```js
function buildRibbon(samples, offA, offB, yA, yB, uvScale, closed=true)
```
Generic: builds strip between lateral offsets offA..offB with additional y offsets. Return BufferGeometry with positions, normals(computed), uv.

Vertices per sample i (0..N, wrap with duplicate for uv seam: use N+1 rows where row N duplicates row 0 with v = L/uvLen).

Road: offsets -7..+7, uv u 0..1, v = s/7 (texture repeats each 7 units). Asphalt canvas 128×128 noise.

Kerb left: offsets 7..8.2 with y +0.05→+0.12 slope? Kerb slightly raised outer? Real kerbs slope down outward. Inner edge at road edge y+0.06, outer y+0.02? Just add +0.05 lift both, stripes texture along v with 3.2 units period (red/white). Also to avoid z-fight with road, kerb is separate lateral band, no overlap. And skirt grass starts at 8.2.

Skirt: offsets from 8.2 outward to 90 with height easing: y(off) = trackY * falloff + terrainNoise. Let me define for offsets o in [8.2, 16, 26, 42, 70, 100]: t = smoothstep((o-8.2)/60) → y = trackY*(1-t) + baseY(o) where base = 0 + noise small. Simpler: y = trackY * (1 - smoothstep(0,55,o-8.2)) + noise*smoothstep. Also slight downslope near road (apron). Grass texture repeat. Build both sides. Also center? Road covers center.

Also to hide seam between kerb outer edge and skirt start: same offset 8.2 → continuous.

Ground far plane: big circle radius 700 at y=-0.6 grass color darker, plus mountains cones at r 550-650. Fog: color matching sky horizon, near 250 far 800? Fog to fade mountains nicely: Fog(sky, 300, 900).

Sky: scene.background = canvas gradient texture? Background as Color + large sky dome mesh (sphere with gradient canvas, BackSide) radius 850 — gradient subtle from #bfe3ff zenith? Palette: warm afternoon: zenith #6fb7e8... I said avoid default-blue vibes for UI; sky is naturally blue. Warm-time: light cyan-blue sky, warm sun. Sky dome gradient: top #4f9ad8 → horizon #dfeef5 warm haze. Fog color #dfeef5.

Sun directional from (0.5, 0.8, 0.3) warm white 2.2. Hemi: sky #bcdcff ground #9dbb7a intensity 0.9. Materials Lambert mostly.

**Start line**: at s=0, quad across road: checker texture (2 rows × 14 cols), length 3 units. Also gantry: cylinders + box banner with canvas texture text "CRESTLINE GP" + lights (3 spheres emissive toggled by countdown).

**Trees**: instanced. Trunk: cylinder(0.18,0.24,1.2). Foliage pine: cone(1.4, 3.2) two stacked? Use one cone + one smaller cone; to keep instancing simple: foliage = cone; some trees get sphere foliage instead → two instanced sets: pines (cone) and broadleaf (icosphere). Scatter: for i<140: s random, side ±1, offset rand 12..55; pos = sampleP + sideVec*o; y = surfaceY(pos) approx = trackY*(falloff) → compute same easing function given |o|. Add jitter. Scale rand 0.7-1.6. Skip if near start gantry or grandstand region. Also skip where |o|<10.

Blob shadows under trees? skip.

**Grandstand**: boxes: base box 24×2×5, tiered steps 3 boxes, crowd texture canvas (random colored dots on dark). Roof plane. Place along straight at s≈ some segment, offset side -13 (left of track). Orient along track tangent. Add fence? skip. Also place a few flags: small triangles on poles that wave (rotate slightly)? Simple: pole cylinder + flag plane with vertex animation? Keep static flag with slight rotation animation via instance? Just 6 flag groups with sin rotation — cheap, do individually (12 meshes).

**Ad boards**: plane 8×1.4 on two posts, canvas textures with sponsor names & flat two-tone design. Place ~8 around corners at offset ~10-12 facing track (rotate to face inward: yaw = tangent yaw + 90°*side... set to face the road: lookAt center point). 

**Arch**: at apex of a corner, over road: two pillars at ±9, box across at y+5.5 with texture "SECTOR 2"? Keep simple, one extra arch mid-track "KUMHO"? generic "APEX TYRES".

**Clouds**: 8 groups of 3 spheres flattened, white, at y 60-90, radius scatter 300-500, drift slowly (x += t*1).

**Balloons**: 1-2: sphere (r=6) colored two-tone (two hemispheres? use two-material? simpler: one color + basket box + ropes lines). Slow bob. 

**Kart construction** (per kart, function buildKart(color, accent)):

Group `root` (position/heading applied). Child `body` group for visual yaw offset (drift) & tilt:
- floor pan: box 1.5×0.18×2.4, color dark
- main cowl: box 1.3×0.5×1.6 at front, kart color; nose cone: box slanted? Use box scaled + a "spoiler" rear wing? Karts: seat back, engine block behind seat, exhaust pipes (2 small cylinders up).
- side pods: two boxes color.
- front bumper: thin box; rear bumper.
- driver: group at seat: torso box 0.55×0.5×0.35 (suit color = accent), head sphere r0.3 helmet color, visor: box dark front, arms? skip; shoulders. Head group can tilt/turn with steering.
- steering wheel: torus r0.16 tube0.03 tilted, on column; rotates with steer.
- wheels: FL/FR groups at (±0.78, 0.3, 0.85) containing wheel mesh: cylinder(r0.3, w0.24) rotated z 90°, dark #222 + hub: small cylinder lighter. Rear wheels slightly bigger r0.34 at (±0.82, 0.34, -0.85).
- blob shadow: circle plane r1.3 black alpha 0.35 at y0.02, separate from body tilt (attach to root).

Wheel spin: rotate wheel meshes around their local axis (cylinder rotated so spin = rotation.x? If cylinder axis along X (after rotation.z=PI/2), spinning = rotation.x += speed/r*dt... rotate the mesh around x axis. I'll wrap each wheel mesh in a steer group for front yaw; spin applied to inner mesh rotation.x (its local x = axle). Cylinder default axis Y; rotate geometry once: geo.rotateZ(PI/2) → axis along X. Then mesh.rotation.x spins around axle? rotation.x rotates around X axis — axle is X, so spinning around its axle = rotation.x ✓. Front steer group rotation.y = steerAngle ✓.

Body visual: bodyGroup.rotation.y = slide visual offset (heading is root's yaw; root.rotation.y = heading + slideVis? I'll set root yaw = heading (movement nose), and body extra yaw = slide*0.85 to show drift angle... wait: movement dir = heading - slide; nose should point INTO turn more than velocity: nose yaw = moveYaw + slide. If root.rotation.y = nose yaw = heading + slide? Let me define heading = nose yaw. moveYaw = heading - slide. Then body visual yaw offset relative to root = 0 — root already shows drift (nose vs velocity). But wheels & skids spawn at rear wheels: rear wheel world pos from body matrix fine. Simplify: root.rotation.y = heading (nose). velocity dir yaw = heading - slide. body child rotates slightly +slide*0.3 for extra drama? Not needed; keep body aligned, add roll: body.rotation.z = -steer*0.06 - slide*0.15 (lean), body.rotation.x = pitch (accel/brake + hill slope handled by root y & slope alignment? Root alignment to slope: pitch root to track slope: sample trackY ahead/behind → pitch = atan2(dy, dist). I'll tilt root.rotation.x = slopePitch + accelPitch. Need order: use root.rotation order 'YXZ' so yaw then pitch then roll ✓.

Hop: on drift start, hopT = 1 → body y = sin(pi*hopT)*0.35 decaying.

Collision radius ~1.0.

**AI code sketch:**

```js
class Kart {
 constructor(cfg){...}
}
```

Fields: pos Vector3, yaw, speed 0, steer (visual), steerInput, drift (0/±1), slide, laneCur, laneTgt, lap=-1, sPrev, idx (sample index), prog, finished, name,color,maxSpeed,accel,aLat,aggr.

update(dt):

```
// nearest sample search around this.idx
let best=idx, bd=Inf;
for(let j=-6;j<=30;j++){ const k=(idx+j+N)%N; d2 = dist2XZ(pos, P[k]); if(d2<bd){bd=d2;best=k} }
idx=best;
// forward projection: refine s: ds component
```

For progress s: use arc = idx*ds + projection of (pos - P[idx]) onto tangent.

Lookahead: la = 5 + speed*0.42 (units) → li = idx + la/ds.
Target point: T = P[li] + side[li]*laneAt(li). laneAt = clamp(kSm[li]*Kline, -1,1)*(half-1.6) + laneTgt(personality/overtake).

Hmm sign: if k>0 = turning left, apex on left side = +side? side = up×tangent = points... computed earlier side=(0,0,-1) for t=(1,0,0). If track turns left (counterclockwise when viewed from above with x right z down?)... I can't be sure of sign convention; safest: lane = -kSmoothed*mag might put karts on outside — visually still fine (they'd take wide lines = bad). I must get sign right. Let me reason: define yaw = atan2(t.x, t.z). Hmm in three.js, common heading: forward = (sin yaw, 0, cos yaw). If turning left (from +x toward -z? "left" relative to forward +x is... with forward=(sin,0,cos): at yaw=0 forward=+z; increasing yaw rotates toward +x. Cross product up×t for t=(0,0,1): (1*1-0*0, 0*0-0*1, 0*0-1*0)=(1,0,0)=+x. Is +x "left" of +z? For a viewer at +y looking down -y with... In three.js, right-hand coordinate system: if forward = +z? Actually camera looks down -z by default. For a kart facing +z (forward (0,0,1)), its right side is... using right = forward × up? right-hand: forward(0,0,1) × up(0,1,0) = (0*0-1*1, 1*0-0*0, 0*1-0*0) = (-1,0,0) = -x. So right = -x, left = +x. And side = up × forward = (0,1,0)×(0,0,1) = (1*1-0*0, 0*0-0*1, 0*0-1*0) = (1,0,0) = +x = LEFT ✓. So side vector = up×tangent = left side of travel. Good.

Signed curvature: yaw increases when turning... if forward rotates from +z toward +x (yaw=atan2(t.x,t.z): t=(0,0,1)→0; t=(1,0,0)→π/2). Turning from +z toward +x: is that left or right? Facing +z, left = +x → yes turning toward +x = turning LEFT, and yaw increased 0→π/2. So dYaw/ds > 0 = left turn = apex on LEFT = lane offset toward +side. So lane_apex = clamp(k*K)*(half-1.7) with k>0 → positive → toward left/apex ✓.

So laneTgt_base = clamp(kAhead * lineGain, -1, 1) * maxLane + personalBias + overtakeShift.

Steering: desiredYaw = atan2(T.x-pos.x, T.z-pos.z); diff = wrapAngle(desiredYaw - heading). steerInput = clamp(diff*2.2 + kFeed?, -1,1). heading += steerInput*yawMax*dt. yawMax = min(3.0, (aLat*1.35)/max(speed,6))? At speed 40, aLat 55: 74/40=1.85 rad/s ok; at speed 15: 74/15≈4.9→clamp 3. Fine.

Slide/drift: driftTarget = (|steerInput|>0.55 && speed>22 && onRoad) ? sign(steerInput) : 0. When engaged from 0: hop, drift=sign. slideTgt = drift * (0.28 + |steerInput|*0.22) maybe also scale with speed. slide ease toward slideTgt at rate 2.5/s (attack) and 4/s (release). moveYaw = heading - slide (slide sign: left drift slide>0, move dir = heading rotated right = yaw minus? yaw increases leftward (as derived: turning toward +x from +z increases yaw = left). Velocity lags nose: nose further left than velocity → moveYaw = yaw - slide*sign... if drifting left (turning left, drift=+1), nose is left of velocity → moveYaw = heading - slide (slide positive). ✓. moveDir = (sin moveYaw, 0, cos moveYaw).

Also while drifting, add slight inward yaw boost: heading += drift*0.35*dt extra so drift tightens line (and slide keeps velocity wide) — produces classic drift arc. And lane target during drift = deeper apex.

Speed: allowed = maxSpeed; probe ahead distances d in [6, 14, 24, 38, 55]: k_p = maxCurvBetween(idx, idx+d/ds) (precompute running max? compute per probe by scanning few samples — 5 probes × ~10 samples × 6 karts × 60fps = fine). vAllowed_p = sqrt(aLat_eff / k_p); allowed = min(allowed, sqrt(v_p² + 2*brake*d)). Note when drifting aLat reduced (0.75×) → slower drift corners. Grass: allowed = min(allowed, 14).

accel: if speed<allowed: speed += accel*dt*(1 - speed/maxSpeed*0.4); else speed -= brake*dt (or coast -8 if close). speed = clamp ≥ 8 min (karts never fully stop).

Overtaking: every 0.3s scan others: nearest ahead within 11 units (compare prog difference along track & lateral): if (other.prog - prog in (0,11]) && |laneDiff| < 2.4: side = pick: prefer inside of corner ahead: insideSign = sign(kAheadAhead); candidate offsets: shift = (side==+1? +2.6 : -2.6) relative to other's lane... set overtakeShift toward chosen side bounded by ±(half-1.3); also if gap <3.5: speed cap = other.speed*0.98+? Actually to overtake need to be faster or equal & go around: allow slight boost: if closing speed low, cap to avoid ram: if gap<2.5: speed = min(speed, other.speed + 1). Soft resolve: if dist2 < (1.9)²: push both apart 0.5*overlap along diff; rear one loses 4% speed. Also lateral nudge changes laneCur naturally? laneCur is target for steering; physical push changes pos directly, fine.

laneCur eases toward laneTgt (rate 2.2/s). Steering target uses laneCur.

Off-track detection: |lateralPos| > half+1 → grass. Compute lateralPos = dot(pos-P[idx], side[idx]). Grass: add bobble (body jitter), dust particles greenish, speed cap. Also stronger: if > half+6 (way off) steer back hard (target = P[idx] center) — with lane logic shouldn't happen.

Lap: s = arc; if sPrev > L*0.8 && s < L*0.2 → lap++ (finished check); if s < L*0.2 && sPrev > L*0.8 reverse? ignore. prog = lap*L + s.

Also anti-cut: if kart cuts across grass big, s jumps forward legitimately via nearest sample... e.g., cutting the S-wiggle at P6 region: nearest sample tracking might jump across the pinch — the wiggle might be tight enough that nearest-point search (limited window ±30 samples = 30*ds ≈ 30*0.9≈27 units) prevents big jumps; ds = L/N ≈ 465/600 ≈ 0.78. Window 30 ≈ 23 units per frame — at 45 u/s, per-frame move 0.75 → fine.

Wait, the wiggle at P5-P7: from (56,-78) to (0,-62) to (-46,-88) after scaling 0.72: (40,-56) → (0,-45) → (-33,-63). Distance between the two legs: the track passes (0,-45) with neighbors at ±~30. Track half width 7 → the gap between bottom-left leg and... The path goes down-right then up to (0,-45) then down-left: forms a "V" pointing up (northward). Legs separated: segment (40,-56)-(0,-45) vs (0,-45)-(-33,-63): they meet at apex. Non-adjacent parts: (40,-56) area vs (-33,-63) area distance ≈ 73 fine. Adjacent approach angle at apex ~ maybe sharp: incoming direction from (40,-56) to (0,-45): (-40,11) normalized; outgoing to (-33,-63): (-33,-18). Angle between: dot = (−40)(−33)+(11)(−18)= 1320−198=1122; |a|=41.5,|b|=37.5 → cos=1122/1556=0.72 → 44° turn. Sharp-ish chicane, good for overtakes under braking. With CatmullRom smoothing it'll be a nice S. OK.

Also check the segment (0,-45) doesn't collide with start straight at z≈72 (100*0.72): start straight z=72, wiggle z=-45, fine.

Elevation after scale: y values: 0,0,3,6,8,9,7,5,3,1,0,0 → ×1.0 → max 9. Slopes: from (112,8,-52)*0.72 to (56,9,-78): dy=1 over d≈42 fine. From y=9 down to y=0 over ((-46,-88)-... from (-46,5,-88) to (-98,3,-72): fine. Long climb from z=46 area (0) up to 8-9 around the back — a climb of 8 over ~200 units: gentle. Maybe amplify y ×1.4 for drama: max 12.6. Slope max ~ (9→5 drop between samples 40 units apart: dy 4 → 5.7° ok). Let me scale y by 1.35 → crest at ~12. Hills visible in chase cam ✓.

**Start grid**: s0 = L - (6 + row*5) for rows 0,1,2 (rows of 2, staggered lateral ±2.2). yaw = tangent yaw at their s. pos = P + side*lane ±. Set lap=-1, sPrev accordingly = s0... careful: s initial near L: lap=-1 → prog = -L + (L-6) = -6 ✓ nice.

But lap counting wrap uses sPrev>L*0.8 → s<L*0.2 → with initial s near L: first frames s stays ~L until crossing → lap becomes 0 (display LAP 1) ✓. Then LAPS=3: when lap reaches 3 (crossed line 4th time: after laps 1,2,3 completed) → finished. Display: lap# = clamp(lap+1, 1, LAPS) → shows 1,2,3 ✓. After finish, keep driving (finished karts: continue but slower? keep normal, mark finished). Leader crossing → state 'finished', show banner, schedule reset in 6s.

**Race clock**: starts at GO. mm:ss.d display.

**Positions list**: computed each frame: sort karts by prog desc (finished ones keep prog order fine). Rows: rank, color chip, name. Gap: show "+x.xs" behind leader? Compute time gap approx via prog difference / leader speed — or show lap of each? Simplest polished: leader shows "LEADER", others "+gap" where gap = (leaderProg - prog)/avgSpeed... Better: distance gap in meters? Mario Kart style shows nothing; broadcast shows intervals. I'll show interval in seconds estimated: diffProg / max(other.speed, 10). Update text 4×/s to avoid jitter. Also tiny up/down arrow when position changed? Nice: ▲▼ colored. Arrows via CSS triangles or characters — characters "▲" are unicode, not emoji, acceptable? It's a text glyph; fine, but might render as emoji on some platforms? "▲" (U+25B2) renders as text glyph typically. I'll use small CSS-drawn carets to be safe... simpler: just show rank number, no arrows. Keep clean.

**Minimap**: canvas 160×160. Precompute path in map space (fit bbox). Draw: track as thick line (stroke width 7 dark, then 5 light gray? style: dark outline + inner asphalt + start notch). Each frame clear & redraw path (store as Path2D) + dots (karts by prog→map pos: use sample at idx + lateral) with leader ring. Rotate map? static fine.

**Particles shader**:

```
uniforms: uTex
attributes: aSize, aAlpha, aColor(3)
vertex: gl_PointSize = aSize * (140.0 / -mvPosition.z); vAlpha...
fragment: tex * color, alpha *= vAlpha
transparent, depthWrite:false
```

CPU pool: arrays pos(Float32Array), vel, life, maxLife, size. On spawn find next index (ring). Update per frame: life -= dt; pos += vel*dt; vel.y -= slight? dust rises: vel *= drag; alpha = life/maxLife * 0.8; size grows. Set needsUpdate on attributes. Draw range full; dead particles alpha=0 & position y=-999.

Spawn dust: while drifting or grass: rate ~ 90/s per rear wheel combined: spawn 2-3 per frame per wheel when drift. Color: on road: tan #cbb49a; on grass: #7fae5a-ish? use mix by lateralPos.

Also small speed-line/exhaust? skip.

**Countdown flow**:

state 'intro'? At load: brief 1s "grid walk" then countdown. Timeline: t=0 page load: raceState='countdown', cdEnd = now+3.9 (beeps at 1.0,2.0,3.0, GO at 3.9? Standard: 3-2-1 each 0.9s then GO). Karts locked (speed 0) during countdown. Countdown camera: slow dolly across grid: pos = gridCenter + side*10 + forward*? animate along. At GO: green flash, raceState='racing', camera mode chase.

Camera cut scheduling starts after GO+4s: nextCut = 8s after GO. When triggered: pick trackside cam (from list of ~10), duration 3s, then chase. Next cut 6-9s later. Trackside cam choice: nearest to leader ahead region; ensure lookAt leader.

Trackside cams: precompute: for i in steps of N/16: pos = P + side*(±13) + y+2.5... choose side randomly, ensure offset from road ≥ 12. Also elevate y+3. Store with name "T-CAM n".

Also a nice extra: heli cam? Keep two modes + countdown dolly.

**Chase cam smoothing**: camPos.lerp(desired, 1-exp(-5dt)); look target smoothed similarly (1-exp(-8dt)). While kart goes over crest, keep cam y ≥ kartY? Use desired pos with up vector; fine.

During drift, chase camera could angle slightly (offset toward drift side) — add lateral offset = -slide*3. Nice.

**Numbers check for "everything in 30s"**: countdown ~4s; racing from ~4s; lap length ~ (compute later; approx 465) avg speed ~ maybe 34 (corners) → lap ~13.7s. Leader finishes lap1 ~18s, lap2 ~31.7s — lap counter shows "LAP 2" at ~18s ✓ and 2nd lap completes just after 30s. Hmm "at least two laps" race duration — race is 3 laps total ✓ (duration requirement is about the race length, not what's visible in 30s). To show lap 2 in progress & position swaps plenty. Maybe bump speeds slightly: maxSpeed 46-52, corner aLat 60-70 → avg ~38 → lap 12.2s. Leader on lap 3 by ~28.5s. Good — show "LAP 3/3" within 30s ✓.

Let me tune: ds = L/N. L: compute actual — control points after scale 0.72 perimeter ~715*0.72 ≈ 515 but CatmullRom with tension rounds corners slightly shorter... roughly 500-520. Set N=700 → ds≈0.73.

Kart params: maxSpeed = rand(45,50); accel = 20; brake = 30; aLat = rand(58, 70); drift helps corner? Real MK drift boosts. Keep aLat high → corners fast; the S apex speed sqrt(65/0.006?) curvature of 44° turn over radius: radius ≈ (arc)/angle... The S has radius maybe ~35 units → k=0.028 → v=sqrt(65/0.035?) k=1/35=0.0286 → v= sqrt(65/0.0286)= sqrt(2272)=47.7 — that's full speed; corners won't slow karts! Need tighter corners or lower aLat. Wider track corners: hairpin radius ~25 → v=sqrt(65*35)= wait v=sqrt(aLat/k)=sqrt(aLat*r). r=35 → sqrt(65*35)=47.7. Hmm so with aLat 65, karts corner at 47 — everything flat out. For visible braking/cornering need aLat ~ 25-35 or tighter radii. Mario Kart arcade feel: grip high but let's set aLat 28-36 → hairpin r30: v=sqrt(32*30)=31; long sweepers r80: v=50+ (flat out). Good mix: sweepers flat, chicane & hairpin braking to ~28-32. Lap avg ~40 → lap ~12.5s ✓. And drift when steerInput high at those corners ✓. yawMax = aLat*1.4/speed: at v=30 → 1.4*32/30 = 1.5 rad/s; needed yaw rate for r30 at v31: ω=v/r=1.03 ✓ ok. Tight hairpin r18: v=sqrt(32*18)=24, ω=1.33 ✓ within limit 1.49. OK but margin thin; set yawMax = aLat*1.6/max(speed,8) and clamp 3.2. Plus drift extra yaw helps.

Track tightest: let me make sure there's at least one hairpin: add a tighter corner: modify point P10 area: (-96,0,46)→ maybe pull in (-80,0,40)? The left-bottom sweeping region is broad. Alternatively tighten P2/P3 top-right into a 180°: P1(80,0,100), P2(132,3,62), P3(142,6,2) then P4(112,8,-52): radius ~ 50-60 — sweeper. Add hairpin by inserting a hook: after P9(-118,1,-16)*0.72... Let me just tighten the bottom-left: replace P8-P10 with (-90,3,-60), (-105,2,-20), (-70,1,10), (-95,0,42)? That creates an S on the left side. Hmm risk of self-intersection with P11(-42,0,86)→P0. Let me design final control points more deliberately (scale applied after):

Raw points (x, y, z), loop:
1. (0, 0, 100) — main straight start (finish line at s=0 here)
2. (70, 0, 102)
3. (118, 2, 78)
4. (138, 5, 30) — sweeper entry
5. (128, 8, -22)
6. (86, 10, -52) — hilltop curve
7. (36, 8, -46)  — pull inward (chicane apex)
8. (-6, 9, -70)  — back out (S)
9. (-52, 6, -88)
10. (-92, 4, -70)
11. (-104, 2, -24) — left sweeper
12. (-74, 1, 8)   — hairpin-ish inward hook
13. (-84, 0, 52)
14. (-40, 0, 86) — onto straight

Check the hook 11→12→13: from (-104,-24) to (-74,8) to (-84,52): direction changes from NE to N to NW-then... 12→13 = (-10,44) mostly +z; 11→12=(30,32) NE; 10→11=(-12,46) N. So path: going N at x≈-104, cuts right to x=-74 (turn right ~36°), then back left to x=-84 going N — that's a gentle S, not hairpin. For a hairpin need ~150° turn. Let me instead make point 12 (-64,1,0) and 13 (-80,0,46): 11→12: (40,24) NE-ish 33°; 12→13: (-16,46) NNW ~-19°... still mild.

Alternative: put hairpin at top after the sweeper: after point 4 (138,5,30) add point (150, 7, -8)? then 5 (118,9,-34): 4→5'... Let me not over-engineer; the chicane + sweepers + S already give varied corners; CatmullRom curvature will produce braking zones. But at least one genuinely tight corner makes drifting obvious. The chicane at points 7-8: 6(86,-52)→7(36,-46)→8(-6,-70): 6→7 dir (-50,6); 7→8 (-42,-24): angle between: cos=(2100 - 144)/(50.4*48.4)= 1956/2439=0.80 → 36° right turn, then 8→9(-46,-18): dir (-40, -18)... wait 8→9 = (-52-(-6), -88-(-70)) = (-46,-18): from (-42,-24) to (-46,-18): angle small. So single 36° kink — medium corner r ≈ ds/Δyaw... arc length through it ~60, Δyaw 0.63 rad → r≈95?? No: r ≈ arc/Δyaw only if constant curvature; a 36° (0.63 rad) turn spread over ~40 units → r ~ 64 → corner speed sqrt(32*64)=45 — barely slows. Hmm.

My corners are all too gentle because loop is big. To get tight corners, control points must be closer/spikier. Let me shrink track: scale 0.6 and add explicit tight corner pairs (two points close together force small radius).

Better approach: pick corner radii explicitly. Standard technique: place points so that consecutive segments meet at desired angles with the curve rounding radius ~ proportional to point spacing. CatmullRom radius ≈ spacing of neighbors. For a tight 90° corner radius ~18: put points ~25 apart around corner.

Let me redesign with a mix — layout roughly like a figure with long straight, hairpin, esses:

Points (x,z), y listed separately:
A (0, 100) y0 — straight
B (90, 100) y0
C (125, 82) y1 — 45° kink into:
D (135, 40) y4
E (112, -2) y6 — right sweeper (from heading north-ish turning west)... 

Hmm wait, direction of travel: A→B heading +x. Then turn left (up in plan = -z? Let me set plan with z downward on my mental map; whatever, loop must be consistent). Let me just carefully craft coordinates forming a nice closed loop, verifying angles between consecutive segments:

I'll design clockwise when plotted with x→right, z→up. Travel counterclockwise? Doesn't matter. Sequence:

1. (0, 100)
2. (85, 100)   — straight, heading +x
3. (128, 84)   — slight left (turn ~30°): dir1=(85,0); dir2=(43,-16)→ -20° (turning toward -z). 
4. (140, 36)   — dir3=(12,-48) steep -z; turn from -20° to ~-76° = 56° more. Sweeper.
5. (120, -12)  — dir4=(-20,-48): ~-113°... turn 37°.
6. (76, -34)   — dir5=(-44,-22): -153°, turn 40°.
7. (30, -30)   — dir6=(-46,4): +175°, turn 32° (now heading -x slightly +z) — this creates a left-right S with previous.
8. (0, -52)    — dir7=(-30,-22): -144°, turn 41° right.
9. (-40, -60)  — dir8=(-40,-8): -169°, turn 25°.
10. (-78, -44) — dir9=(-38,16): +157°→ heading up-left; turn 34°.
11. (-98, -8)  — dir10=(-20,36): +119°... 

Wait I need to be careful: angle = atan2(dz, dx)? Let me use compass-free approach: just ensure no self-intersection and enough total turning (Σ exterior angles = 360° for a simple closed loop).

Sum of turns so far: 30+56+37+40+32+41+25+34+? Let me recompute properly later — actually simpler: I trust a hand-drawn loop: points ordered around a loop with a wiggle inward will close fine as long as the final points come back. Continue:

11. (-98, -8) — heading N
12. (-96, 34)  — dir=(-2,42) N, slight right hook: after 10→11 (heading NNE ~ +119°?) I'm overcomplicating.

Honest approach: define points on a rough circle with radius varying (like a wavy circle) — guaranteed simple loop with smooth varying curvature, then perturb a couple of points to create tighter corners. Parametric: angle θ_i, radius r_i:

θ = i/12*2π. r varies 55–85. Position x = cos θ * r, z = sin θ * r (this loops counterclockwise in x-z plane... whatever). Curvature comes from radius variation + angular spacing. Tight corner = small r over few samples.

r per i (12 points): [85, 84, 80, 60, 46, 62, 80, 82, 70, 48, 52, 74]
θ_i = i * 30°.

Point i: (r_i cos θ_i, r_i sin θ_i). The radius dips at i=4 (46) and i=9 (48) create tighter local curvature. But curvature of a polar curve r(θ): k ≈ (r² + 2r'² - r r'')/(r²+r'²)^{3/2}. With r varying smoothly, curvature stays modest (circle r=50 → k=0.02 → corner speed sqrt(32/0.02)=40). Tight corners need genuinely small radius sections: e.g., a hairpin r=15 → k=0.066 → v=22.

OK let me hand-place a track with known corner radii — like drawing with straight segments and arcs:

Main straight along z=100 from x=-60 to x=90 (length 150) heading +x.
Turn 1 (T1): 90° left at (90,100)→ arc r=22 center (90,78): ends heading +? traveling +x turning left (toward -z if left is... in plan x-right/z-up, traveling +x, left turn = toward +z? Using standard math orientation (x right, z up in plan), heading +x, left = +z. But three.js z toward viewer; plan view from above (+y down at ground) flips handedness... irrelevant for construction.)

Define track path in plan (x, z):
- Straight: (-70, 96) → (80, 96). heading 0°(+x).
- T1 left 90°, r=20: arc center (80, 76), from (80,96) to (100,76). End heading 90° plan-angle = +? traveling +x turning left toward -z... let me define left turn = clockwise in plan (x right, z up): heading +x, clockwise turn heads toward -z (down). Fine: T1: center (80,76): start (80,96) heading +x, quarter arc to (100,76) heading -z(270°... i.e., downward in plan). 
- Back straight: (100,76) → (100,-30) heading -z (length 106). 
- T2: left 90° r=16: center (84,-30): from (100,-30) to (84,-46), end heading -x.
- Short chute: (84,-46)→(52,-46) heading -x (32).
- T3 hairpin right 160°? A hairpin: from heading -x turn right (toward +z then +x): 180° U-turn r=14: center (52,-60): from (52,-46) arc right 180° to (52,-74) heading +x. 
- Then straight slight: (52,-74)→(92,-80)? heading slightly down-right; then T4 left... 

This is getting complex; simpler: I'll construct the curve from a list of points placed at straight midpoints and corner apexes with roughly correct spacing — CatmullRom through well-chosen points tends to look right if spacing at corners ≈ radius. Honestly, for the deliverable, "closed circuit with curves and hills" doesn't demand specific radii — I just need visibly varied corners including at least one slow one. Easiest reliable method: take my earlier 12-point loop (which I verified as simple) and shrink it so corner radii shrink too. Earlier loop ~715 raw perimeter with radii maybe ~60-80 → scale 0.55 → perimeter ~390, radii ~33-44 — still medium. Tighter: make two corners sharp by adding near-duplicate points (CatmullRom with clustered points creates tighter bends): e.g., insert extra points around the chicane.

Alternative pragmatic approach: accept medium-speed corners with aLat tuned so karts still slow to ~60-75% on them, plus ONE tight cluster: around the P6 wiggle, add intermediate points to pinch the S:

Final control points (x, y, z) — scale factor 1.0 (already final coordinates), perimeter target ~470:

```
(  0, 0,  74)   start/finish straight
( 58, 0,  76)
( 96, 2,  58)   T1 entry
( 104, 4,  22)  T1 mid
( 88, 7, -10)   T1 exit / hill up
( 60, 9, -20)   crest
( 28, 8, -10)   dip inward (right kink)
(  8, 9, -34)   S left
(-24, 8, -52)   S exit
(-58, 6, -52)   
(-84, 4, -26)   left sweeper
(-78, 2,  8)    
(-92, 1, 40)    hook out
(-58, 0, 62)    final corner onto straight
```

Check loop simplicity: plot mentally: start (0,74) going +x to (58,76)→(96,58): heading turning left(up?)... in plan x right, z up: from +x heading curving to (-z)? (58,76)→(96,58): dir (38,-18) heading down-right (turning right if z-up? from (1,0) to (0.9,-0.43) = clockwise = right turn). Then (96,58)→(104,22): (8,-36) more downward. →(88,7): (-16,-15) down-left. →(60,-20): (-28,-27). →(28,-10): (-32,10) down-left→left-up: turned past south heading west-north. →(8,-34): (-20,-24) down-left again (S!). →(-24,-52): (-32,-18). →(-58,-52): (-34,0) west. →(-84,-26): (-26,26) up-left. →(-78,8): (6,34) up (right turn). →(-92,40): (-14,32) up-left (left turn, S). →(-58,74): (34,34) up-right. →(0,74): (58,0) right. → closes.

Does segment (28,-10)→(8,-34) come close to (-24,-52)→(-58,-52)? (8,-34) to (-24,-52) region: distance fine. Does the S at (60,-20)/(28,-10) pinch against (8,-34)/(-24,-52)? Points (28,-10) and (-24,-52) are far. The inward spike (28,-10): neighbors (60,-20) and (8,-34): this creates a left-right S with radius maybe ~15-25 → corner speed sqrt(30/0.05)≈24 ✓ drift city. Also (-78,8)&(-92,40) mini-S on left. Top-right sweeper broad. Looks good: 14 points, angles all moderate, no self-intersection (the two "spikes" go inward but stays simple). Perimeter estimate: sum segment lengths: (58,2)→... compute: 
P0(0,74)→P1(58,76): 58
→P2(96,58): √(38²+18²)=42
→P3(104,22): 36.9
→P4(88,7): 21.9
→P5(60,-20): 39
→P6(28,-10): 33.5
→P7(8,-34): 32.3
→P8(-24,-52): 37.7
→P9(-58,-52): 34
→P10(-84,-26): 36.8
→P11(-78,8): 34.7
→P12(-92,40): 34.5
→P13(-58,74): 48.1
→P0: 58
Total ≈ 539. Hmm bigger than earlier estimate due to added points. With CatmullRom smoothing ≈ 540. Lap at avg 38 → 14.2s. Two laps ~28.5s + countdown 4 = 32.5 — slightly over 30 but "at least two laps" refers to race length; still I'd like leader on lap 3 within 30. Bump speeds: maxSpeed 48-54, aLat 34-42, avg ~41 → lap 13.2 → lap2 ends ~30.4. Eh. Alternatively scale 0.9 → L≈486 → lap 11.9s: crossings at 4+11.9=15.9 (lap2 start), 27.8 (lap3 start) ✓ "LAP 3/3" visible by 28s, 2 full laps completed by ~28s ✓. Do scale 0.9 on xz, y ×1.1. Radii shrink 0.9 slightly → tighter corners, speeds still ok.

y-values: 0,0,2,4,7,9,8,9,8,6,4,2,1,0 → scaled ×1.1 → up to ~10. Slope between P5(60,9,-20) and P6(28,8,-10): fine.

Karts: 6, maxSpeed rand 48–54, accel 22, brake 34, aLat rand 36–44, drift slides. Hairpin-ish S corner v = sqrt(40*20)=28 ✓ nice speed variance.

**Kerb placement**: full loop both sides.

**Grandstand** along straight: at s near start-line minus 40 → position P at idx of s=L-40, side offset -16 (left side of straight... choose outer side away from infield? The straight is top of loop (z=74+), outside is +z. Put grandstand outside: side sign determined by which side is "outside": at start straight, travel +x, side=up×tangent: tangent (0.98,0,0.18)? side=( -t.z? ) earlier: side = up×t: t=(1,0,0)→side=(0,0,-1)?? Wait earlier computed up×t for t=(0,0,1) = (1,0,0). For t=(1,0,0): up×t = (0,1,0)×(1,0,0) = (1*0-0*0, 0*1-0*0, 0*0-1*1) = (0,0,-1). Hmm that's LEFT = -z when heading +x? In three.js (x right, z toward viewer), heading +x with up +y: left hand side is -z? Consider standing facing +x, up +y: your left is +z? Right-hand rule: forward × up = right? forward(1,0,0)×up(0,1,0) = (0*0-0*1, 0*0-1*0, 1*1-0*0) = (0,0,1)?? cross((1,0,0),(0,1,0)) = (0*0-0*1, 0*0-1*0, 1*1-0*0) = (0,0,1). Hmm forward×up = (0,0,1). Is forward×up right or left? For camera: right = forward×up? In three.js, camera looks down -z, up +y, right +x: forward(0,0,-1)×up(0,1,0) = ((0)(0)-(-1)(1), (-1)(0)-(0)(0), (0)(1)-(0)(0)) = (1,0,0) = right ✓. So right = forward×up. So heading (1,0,0): right = (1,0,0)×(0,1,0) = (0*0-0*1, 0*0-... compute: (a2b3−a3b2, a3b1−a1b3, a1b2−a2b1) with a=(1,0,0), b=(0,1,0): = (0*0−0*1, 0*0−1*0, 1*1−0*0) = (0,0,1) = +z is RIGHT. So left = -z ✓ side=up×t = -left? up×t: a=(0,1,0),b=(1,0,0): (1*0−0*0, 0*1−0*0, 0*0−1*1) = (0,0,-1) = left ✓. Good: side = left. Outside of the loop at start straight: loop interior is z<74 side (loop goes down to z=-52*0.9), so outside = +z = right = -side. Grandstand at -16*side → +z ✓.

Whatever — I'll place scenery with signed offsets and eyeball via math; risks acceptable.

**Tree/foliage placement rule**: offset magnitude between 11 and 55, both sides; avoid grandstand zone (near start straight outside) and billboards.

**Now HUD structure (DOM)**:

```html
<div id="ui">
  <div id="board"><div class="bt">RUNNING ORDER</div><div id="rows"></div></div>
  <div id="lapbox"><div id="lap">LAP 1/3</div><div id="clock">0:00.0</div></div>
  <canvas id="map" width="150" height="150"></canvas>
  <div id="camtag">GRID CAM</div>
  <div id="big"></div>  countdown / GO / FINISH
  <div id="title">CRESTLINE GP ... small caption?</div>
</div>
```

Title flourish: bottom-center small "CRESTLINE GP — AI GRAND PRIX" fading after start? Keep camtag & everything subtle. I'll add a brief intro title that fades at GO.

CSS: absolute positions, pointer-events none. Rows: parallelogram via transform: skewX(-10deg) on container, unskew content. Leader row accent border. Colors from kart colors.

Countdown numbers: #big font-size 120px, skew, text-shadow hard offset (solid offset shadow = chunky arcade, not glow — solid 4px offset shadow is fine, not a glow). Animate with CSS class re-trigger (scale from 1.6→1 + fade).

GO: green #7ade3f? accent palette: HUD base charcoal #14161a, paper text #f4f1e6, accent tangerine #ff4d1c? Racing feel ✓.

**Now write all the code.** I'll be systematic. Estimated ~900 lines. Let me draft.

```js
import * as THREE from 'three';

// ---------- helpers ----------
const rand=(a,b)=>a+Math.random()*(b-a);
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const wrapPI=a=>{while(a>Math.PI)a-=2*Math.PI;while(a<-Math.PI)a+=2*Math.PI;return a;};
const lerp=(a,b,t)=>a+(b-a)*t;
const damp=(a,b,l,dt)=>lerp(a,b,1-Math.exp(-b? no
```

damp: `const damp=(rate,dt)=>1-Math.exp(-rate*dt);`

**Canvas texture helpers:**

```js
function makeCanvas(w,h,fn){const c=document.createElement('canvas');c.width=w;c.height=h;const g=c.getContext('2d');fn(g,w,h);const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;return t;}
```

Asphalt: fill #3a3d42, speckles random darker/lighter dots, faint crack lines? Keep speckle. RepeatWrapping both, anisotropy 4.

Grass: base #6da84e? Mario-bright: #79b356 with darker blotches + tiny light dashes. Repeat.

Kerb: 64×64: half red half white vertically → repeated along v gives stripes; set repeat so stripe length ~3 units: v repeat = L/3? We'll build kerb ribbon with v = s/3.2 and texture 1 stripe pair per tile: draw top half white bottom half red? Actually stripes across: canvas 32×64: red top half, white bottom → v repeat gives alternating ✓.

Checker: 8×2 grid black/white, used on start ribbon with u repeat 7, v repeat 1? I'll draw checker directly 160×32 with 20px squares → 8 cols; geometry uv u 0..1 across width? checker across road: u across → need ~10 squares across: draw canvas 200×40 with 10×2 squares; uv u 0-1, v 0-1 over 3.5 length ✓.

Crowd: random dots on dark.

Billboard textures: function makeSign(text, bg, fg): bold italic text centered.

**Track build:**

```js
const SCALE=0.9;
const raw=[[0,0,74],[58,0,76],[96,2,58],[104,4,22],[88,7,-10],[60,9,-20],[28,8,-10],[8,9,-34],[-24,8,-52],[-58,6,-52],[-84,4,-26],[-78,2,8],[-92,1,40],[-58,0,62]];
```

wait earlier list had 14 with (-92,1,40) then (-58,0,62)? I wrote (−58,0,86) before scaling; use (-58,0,66)? The straight goes from (-58,74) to (0,74): P13 = (-58,0,70). Set final: [-58,0,70]. Also check P12 (-92,1,40) → P13 (-58,0,70): fine.

Hmm one more check: P4 (88,7,-10) and P5 (60,9,-20): the crest near (60,-20). And the S: P5(60,-20)→P6(28,-10)→P7(8,-34): up-down wiggle ✓. Also P11(-78,8)→P12(-92,40): small S with P10→P11. 

curve = CatmullRomCurve3(points.map(p=>new Vector3(p[0]*SCALE, p[1]*1.1, p[2]*SCALE)), true, 'centripetal'? Use 'catmullrom' default tension 0.5. Centripetal avoids loops with uneven spacing — safer: 'centripetal'.

N=700 samples via getSpacedPoints(N) returns N+1 points (last = first). I'll take first N as unique, wrap manually.

Arrays: P[i] (Vector3), T[i] tangent normalized (from P[i+1]-P[i-1]), Sd[i] side = up×T (normalized, y=0), yaw[i], ks[i] curvature = wrap(yaw[i+1]-yaw[i-1]) / (2*ds) with sign, smoothed ks (window 9), kMax window helper.

ds: compute cumulative? getSpacedPoints equal spacing approx: ds = totalLen/N where totalLen = curve.getLength(). Minor variance fine.

Banking: none; but road normal should follow slope for ribbon normals — compute via cross of edge vector & tangent per segment; use computeVertexNormals on geometry — fine.

**Ribbon builder:**

```js
function ribbon(offA, offB, yLiftA, yLiftB, mat, vRepeat /* units per tile */, uMode){
  const pos=[],uv=[],idx=[];
  for(let i=0;i<=N;i++){const j=i%N;const p=P[j],s=Sd[j];
    pos.push(p.x+s.x*offA, p.y+yLiftA, p.z+s.z*offA);
    pos.push(p.x+s.x*offB, p.y+yLiftB, p.z+s.z*offB);
    uv.push(0, (i*ds)/vRepeat, 1, (i*ds)/vRepeat);
  }
  for(let i=0;i<N;i++){const a=i*2;idx.push(a,a+1,a+2, a+1,a+3,a+2);}
  const g=new THREE.BufferGeometry();
  g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));
  g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));
  g.setIndex(idx);g.computeVertexNormals();
  return new THREE.Mesh(g,mat);
}
```

Winding order & normals: with side=left, offset offA left... need upward-facing normals: triangle (a, a+1, a+2): a=left_i, a+1=right_i, a+2=left_{i+1}. Orientation depends on left/right definition; if wrong, normals point down — fix by checking: computeVertexNormals gives normal per winding; I'll just set material side: DoubleSide for road/skirt to be safe, and if lighting looks off... Lambert DoubleSide with wrong normals = dark. Better ensure winding: Take i=0 near P0(0,0,74), T≈(1,0,0), Sd = left = (0,0,-1)?? earlier: heading +x → left = -z?? computed above: right=+z so left=(0,0,-1) ✓ Sd=(0,0,-1). offA = +7 → point A=(0, y, 74-7)=(0,y,67); offB=-7 → B=(0,y,81). i+1: x+=ds≈0.77: A'=(0.77,y,67), B'=(0.77,y,81). Triangle (A, B, A'): cross(B-A, A'-A) = cross((0,0,14),(0.77,0,0)) = (0*0-14*0, 14*0.77-0*0, 0) = (0, 10.8, 0) → +y ✓ up. 

But wait: with y decreasing? plus yLifts fine.

Also uv v continuous across wrap seam: row i=N uses j=0 but v = N*ds/dsLen = L/3.2 — texture repeat must divide evenly or seam mismatch: choose vRepeat such that L/vRepeat is integer-ish; L actual ~ measure at runtime: vRepeat = L/Math.round(L/3.2). ✓ Same trick for road (tile 8) and grass.

**Skirt**: multi-band ribbon with height falloff — custom:

offsets: [[8.2, 0], [15, ...], ...] with y = mix(trackY, groundY, t) where t by smoothstep on offset, groundY = -0.6 + gentle noise via pseudo-random per sample: n = sin(x*0.05)+cos(z*0.04)... small ±0.8. Also outermost offset 130 blends fully to ground; then big ground disc r=800 at y=-0.6 (slightly below skirt outer edge → but skirt outer y ≈ -0.6±noise — z-fight risk where noise<0 dips below disc. Set disc at y=-1.4, skirt ends at y≈-0.6 → gap visible from side? Distant fog hides; also skirt outer edge y should land exactly at -0.6 and noise only applies to middle offsets. Fine: offsets [8.2→trackY+? apron], define array of (offset, yExpr):

```
const skirt=[[8.2,1],[13,0.82],[20,0.55],[32,0.28],[52,0.1],[80,0],[120,0]];
y = trackY*w + ground*(1-w) where w from table (lerp between entries by offset), ground=-0.55.
```

Add per-vertex noise*(1-w)*1.5 for natural terrain. Implement: function skirtY(off, i) piecewise-lerp. Build as one ribbon strip per side covering offsets sequence → mesh with grass material (repeat ~ every 6 units in v, u repeat proportional to width... u across: 0..(offMax-offMin)/6).

Simpler: build skirt as multiple flat ribbons? One mesh with varying offsets: positions: for i rows: for k offsets: vertex. Two sides. I'll write buildSkirt(side) producing grid.

**Start line & gantry:**

Find idx0=0 (s=0 at P[0]). Ribbon segment across road: build small geometry manually using samples near 0: rows at i=0 and i=ceil(3.5/ds): quad strip with checker texture, y+0.03.

Gantry: group at P[0]: posts at ±(halfW+1.5) using Sd[0]; crossbar box (width 2*(halfW+1.5), height 1.6, depth 0.8) at y=trackY+6 with banner texture front/back. Lights: 5 circles? Use 3 spheres r0.22 under crossbar at x offsets -1,0,1 (relative center), material emissive red toggled: mat each (clone) emissiveIntensity 0/2.

Also second arch mid-track with "APEX" banner.

**Trees etc:** as planned, instanced:

```js
function scatterTrees(){
 const pineGeo trunk cyl, leaf cone; oak: trunk + icosphere.
 count 150; choose i, side, off=11..52; skip if within start straight outside zone (|s - sStart|<30 && side==outside) → keep some? Grandstand placed at specific s; avoid overlap by skipping offs<25 there.
 pos y = skirtYat(off, i) approx: compute via same function (trackY*(w)) — trees on slopes ok.
 instance matrix: position + scale + rotY random.
}
```

InstancedMesh trunk (cyl), leaves (cone) — pines; and oaks (sphere). Colors: vary leaf color via instanceColor? Use setColorAt for subtle variation ✓.

**Billboards**: 6 signs: choose sample indices spread, side outside (alternate), off = halfW+4.5, face toward track: mesh.lookAt(P[i]). Plane 7×2.2 + 2 post cylinders + texture.

**Grandstand**: at s ≈ L*0.97 (just before line? along straight after line?) Straight spans P13(-58,70)→P0(0,74)→P1(58,76): place along s from idx ~ (L-40) to (L+40)? Simply position group at P around idx for s=L*0.5*... Let me compute index: start line at s=0 (P[0]=(0,66.6? ) The straight along z≈74*0.9=66.6 spans x from -52 to 52. Put grandstand on outside (+z, right side = -Sd) centered at x≈0 offset +18: pos = P[0] + right*18 where right=-Sd. Group: base box 46×1×6 at y0, tiers: 3 steps rising, crowd texture on tier tops? Use boxes with crowd texture on the sloped front? Simple: 4 stacked boxes each set back, each front face crowd material (multi-material box: use array materials [side, side, top(crowd)...]). Simpler: one big box tilted? I'll build steps: for r in 0..3: box(width 46, h 0.9, d 2.2) at z offsets & y rising, material crowd on top face — apply crowd texture to entire box (looks like confetti crowd block) acceptable at distance. Plus roof: thin box on posts, accent color. Add flag poles.

Fence along straight: small posts + rails? skip for scope; boards enough.

**Clouds**: group of 3 spheres (scaled y 0.5), MeshLambert white flat? Lambert with fog fine. y 55-85.

**Balloons** ×2: sphere scaled, basket, animate bob + slow drift circle.

**Distant mountains**: cone geometry radius rand 60-140 height 50-120, positioned ring r=650..750, color desaturated blue-grey #8fa3b8 with fog → soft backdrop. ~14 cones. Also a sun disc? skip.

**Karts**: build function returns {root, body, wheels:{...}, steerL, steerR, driver...}. Colors: define KARTS config array with name, color, trim.

```js
const ROSTER=[
 {name:'PEPPER', c:0xe0452f, trim:0x8c2418},
 {name:'MINTY', c:0x37b37a, trim:0x1d6b48},
 {name:'BUMBLE', c:0xf0b429, c2:...},
 {name:'BERRY', c:0x3e6fd0...} hmm blue livery ok
 {name:'GRAPE', c:0x8a4fc9},
 {name:'POWDER', c:0xe8ecef, trim dark}
];
```

Maybe replace blue with orange? PEPPER red + orange too close. Keep cobalt "BERRY" — fine as livery.

Driver skin: helmet color = kart color, suit dark #22262b with accent stripes? simple.

**Kart physics constants**:

```
halfW=7 (road), lane max ±(halfW-1.9)=±5.1
```

**Main loop**: fixed timestep? Use clamped dt = min(0.033, delta). Physics fine at variable dt.

**Positions & HUD update** every frame cheap; text updates throttled (every 0.15s) to avoid layout thrash. Rows: create 6 row divs once; update textContent & chip colors static; reorder via CSS order or re-append sorted. Use rank to set row order: rows[i].style.order? Parent flex column: set style.order = rank. And class leader.

**Camera**:

- chase: behind leader.
- trackside list built from samples every ~N/14 with alternating sides, off 13-16, y+3.
- cut logic in update: if mode=='chase' && t>nextCut: switch trackside: pick the one with min distance to leader within 30..90 & facing? just nearest within 100, prefer random among 3 nearest. Hold till cutEnd → back to chase, nextCut = t + rand(6,10).
- countdown cam: dolly: center = gridMid; cam pos orbit: angle = -0.9 + t*0.15? Slow lateral slide: pos = center + fwd*18 + side*sin? I'll do gentle arc around grid front: radius 16 around center, angle sweeping 40° over countdown, lookAt center+up1. At GO → chase.

Camera FOV 58, speed-based to 66 for chase.

**Countdown numbers**: big overlay; JS sets textContent & restarts animation (el.classList.remove/void offsetWidth/add).

**Beeps**: WebAudio: function beep(f, t): osc square? use 'triangle', gain envelope. Ac enabled lazily; attempt resume on visibility/pointer. Race restarts also re-run countdown beeps.

**Race reset**: function gridKarts(): positions: row = floor(gi/2), col = gi%2: s = L - 8 - row*5.5; lateral = (col? 2.4 : -2.4) + tiny jitter; pos = P[idx(s)] + Sd*lateral; yaw = tangent yaw at s; speed 0, lap=-1, slide 0 etc. Also clear particles & skids (reset alpha attr / instance count).

idxFromS(s): s mod L / ds.

**Finish**: when leader crosses with lap→LAPS: state='finish', big "FINISH", sub "WINNER — name"; karts continue; after 5.5s: reset & countdown again. Also stop clock at leader finish time.

**HUD lap display**: leader's current lap: `LAP ${min(lap+1,LAPS)}/3`; after finish: "FINISH".

**Clock**: race time from GO until leader finish.

Edge: karts finishing continue driving (AI keeps running) — fine, they cruise.

**Overtake guarantee**: differences in maxSpeed (48-54) + aLat variance + rubberband ensure swaps. Also starting grid order ≠ speed order → early overtakes visible ✓. Place faster karts at back: sort roster so fastest starts P6 (row 2)? Set grid order manually: speeds assigned so grid ~ random.

Let me also add slight per-kart lane wander (sin(t*0.3+i)*0.8) for organic movement.

**Collision resolution detail**: for pairs: if |progDiff| < 3 && |latDiff| < 1.9 → physical push: compute actual world dist; if d < 1.8: separate along (a.pos-b.pos) normalized by (1.8-d)/2 each; and dampen relative velocity slightly. Using world positions simplest: check dist2 < 1.8² then push. But when side-by-side on different lane, distance maybe 2.4 fine. Also prevent pushing off track: after push, clamp lateral? skip.

Ram penalty: if kart behind (prog less) and closing → rear.speed = min(rear.speed, front.speed+2) when d<3. Simple.

**Drift conditions refine**: driftVal target: if onRoad && speed>26 && |steerInput|>0.5 → sign; keep while |steerInput|>0.3 && speed>18. Also require |kAhead|>0.02 (actually steering implies corner). During drift: yawExtra = drift*1.1*dt*speedFactor; slide target 0.32+0.25*|steer|; moveYaw = yaw - slide*drift? sign: drift=+1 means turning left (yaw increasing). moveYaw = yaw - slide (slide ≥0 always, times drift sign: moveYaw = yaw - slide*drift). Wait: left turn: nose left of velocity: velocityYaw = yaw - slide (slide>0) ✓. Right drift: drift=-1: velocity = yaw + slide → moveYaw = yaw - slide*drift ✓ (drift=-1 → +slide ✓).

Visual body yaw relative to root: root yaw = yaw (nose). Kart looks correct since nose points into corner beyond velocity ✓. Add body roll: body.rotation.z = clamp(steerInput*0.10 + slide*drift*0.18...) sign: rolling outward: left turn → roll right (positive z rotation? test visually can't; choose lean-in like Mario Kart: lean into corner: left turn lean left = rotation.z negative? For object facing +z... I'll use body.rotation.z = slide*drift*0.22 + steer*0.08 and flip sign if looks wrong — can't see it; keep modest values so either sign looks ok. I'll reason: root yaw: rotation.y = yaw with forward = (sin yaw, 0, cos yaw). Local z forward. Rolling around local z: positive rotation.z tilts left side up? For an object facing +z (yaw 0), rotation.z positive rotates +x axis toward +y → right side (which is... local +x: with yaw=0 forward=(0,0,1), right = forward×up = (0,0,1)×(0,1,0)=(1,0,0)... wait cross((0,0,1),(0,1,0)) = (0*0-1*1, 1*0-0*0, 0*1-0*0)=(-1,0,0). Hmm: a=(0,0,1), b=(0,1,0): cross = (a2b3−a3b2, a3b1−a1b3, a1b2−a2b1) = (0*0−1*1, 1*0−0*0, 0*1−0*0) = (−1,0,0). So right = -x?? Earlier for camera forward -z: forward×up = (0,0,-1)×(0,1,0) = ((0)(0)-(-1)(1), (-1)(0)-(0)(0), (0)(1)-(0)(0)) = (1,0,0)=+x and that was right ✓. So for forward +z, right = -x. Then left = +x. rotation.z>0 rotates +x toward +y (right-hand about z): raises LEFT side → leans right. Left turn (drift+1) should lean... karts lean INTO turn (left) → left side down → rotation.z negative for drift=+1. So body.rotation.z = -drift*slide*0.5 - steerInput*0.06. Whatever sign, magnitude ~0.15 subtle. Fine.

Steering visual on wheels: steerVis eases to steerInput*0.42 rad.

Wheel spin: rotation.x += speed/0.33*dt (r=0.33) — sign: forward motion wheels roll... rotation.x positive with forward +z? Wheel cylinder axis along x; rolling forward (+z local? kart forward local +z since yaw0 forward=(0,0,1)) rolling about x axis: point at top moves +z when rotation.x negative? ω × r: angular velocity +x̂, point at bottom (0,-r,0): v = ω×r = (1,0,0)×(0,-r,0) = (0*0-0*(-r), 0*0-1*0, 1*(-r)-0*0) = (0,0,-r) → bottom moves -z → ground contact moving backward → kart moves forward ✓ (like rolling). So rotation.x += speed/r*dt ✓.

**Dust/skid spawn positions**: rear wheels world pos: compute via localToWorld of wheel placeholders: store rear wheel Object3D refs; getWorldPosition each frame when spawning.

**Skid mark orientation**: yaw of movement: quad rotated rotation.y = moveYaw (use kart moveYaw) & positioned at wheel ground pos; also slight random. Instance matrix compose(pos, quat(yaw), scale(1, 1, len)). Base plane geometry rotated to lie flat: PlaneGeometry(0.3, 1.4).rotateX(-PI/2) → lies in XZ; then instance yaw. Slight y offset 0.03 above road: need road surface y at that point = kart's ground y (kart pos y is track surface). Kart root y = trackY at its position (sample-based + lateral flat). We store kart.groundY. Use that.

Kart root y = groundY (wheels radius baked into model: model built with wheels at y≈0.3 so root at ground). Add slope pitch: compute slope from track heights ahead/behind: pitch = atan2(P[i+2].y - P[i-2].y, 4*ds) with sign: nose up when going uphill. root.rotation.x = -pitch? For rotation order YXZ and forward +z local... when yaw=0 forward +z; going uphill means y increases along +z → nose up = rotate around x negative? Rotation.x negative tilts +z axis toward +y? Rotation about +x by -θ: z-axis moves toward +y ✓ (right-hand: +θ about x takes +y→+z... θ positive: y→z, z→-y; so to lift +z toward +y need θ negative ✓). pitch = atan2(dy, dz_path)... compute from tangent: dy/ds along tangent: pitch = -atan2(T[i].y, horizLen)? T normalized includes y. slopeUp = T.y (positive climbing). rotation.x = -asin(T.y)?? climbing → nose up → negative x-rotation ✓ rotation.x = -Math.asin(clamp(T.y,-0.5,0.5)). Combined with accel pitch small.

Body pitch from accel: body.rotation.x = clamp(accelSmoothed * 0.006...) minor; include small.

**AI steering into hills** — using XZ for yaw math ✓.

**Track surface height sampling for kart y**: y = P[idx].y + (P[idx+1].y-P[idx].y)*frac + lateral tilt none. Blend: kart y directly set (no vertical velocity) — hills handled by track. Since kart stays near centerline laterally (within ±8) flat across ok. When far off (grass skirt), y should follow skirt falloff... karts rarely exceed off=+... AI keeps them on track; collisions might push slightly off — skirtY approx: if |lat|>halfW: y = trackY*w(|lat|)+ground*(1-w) using skirt weight function ✓ implement shared function heightAt(idx, lat).

**Leader chase target selection**: leader = standings[0]; but if leader finished... fine continue. Also occasionally show battles? Requirement says chase the leader. ok.

**Position list gap column**: show "L2" for lap? Keep: right side small text: leader "—" others "+2.4s". Compute gap = (progLead - prog)/max(speed,10). Format +x.xs.

**Intro title**: overlay #big shows "CRESTLINE GP" at t<1? I'll fold into countdown: state countdown duration 4.4: first 0.8s show "CRESTLINE GP" then 3,2,1 at 1.4/2.3/3.2, GO at 4.1? Simpler timeline: cd = 4.6s: t in [0,0.9): "CRESTLINE GP" small? Might overcomplicate; do: 3 at 1.0, 2 at 1.9, 1 at 2.8, GO at 3.7 → GO ends countdown, karts launch. Beeps at each.

**Cam tag**: update text: "GRID CAM" during countdown; "CHASE • P1 PEPPER" during chase; "TRACKSIDE CAM 4" for trackside.

**Restart**: clear skid instances (set count 0 then restore 500? just reset all instance matrices scale 0 & count) — I'll set mesh.count=0 initially and grow; on reset set count=0. Particles: kill all (life=0). Reset karts. state countdown. Also reset clock.

**Also engine idle wobble**: body slight bob by speed: body.position.y = 0.02*sin(t*30+i) on grass bigger.

**Grass detection & dust color**: lateral abs > halfW-0.6 → grass: cap speed, spawn green-brown dust, body rumble (body.position.y jitter).

Right — also requirement "wheels that turn" ✓ (front steer + spin), "dust or skid particles" ✓ both.

"Karts have simple drivers" ✓ helmet+torso+arms? Add two arm boxes to wheel? Small: shoulder box + arms as thin cylinders angled to wheel — nice detail, cheap. I'll add arms: two thin boxes from torso to steering wheel. And head turns with steer.

**Signature moment**: the drift storms — dust plumes + skid marks + hop; plus cinematic grid dolly & broadcast cuts. Good enough.

Now — performance & correctness concerns:

- getSpacedPoints(700) each call computes; fine once.
- computeVertexNormals on ribbon with duplicated seam vertices: seam normals slightly off (visible lighting seam) — acceptable; or fix by averaging — skip, use DoubleSide? Lambert lighting with seam normal error minor.

Wait — normals: for road I computed winding gives +y; computeVertexNormals averages; seam row duplicates get their own normals — slight shade difference at start line, negligible.

- Kerb geometry: two ribbons per kerb (left: off 7→8.4 slight raise & tilt: yLift inner 0.07 outer 0.02; right: off -7→-8.4 with lifts swapped). Add outer edge meets skirt 8.4? skirt starts 8.4. Set kerb outer 8.4, skirt start 8.4.

- Road texture v tile 8 → road canvas noise tile must be seamless-ish: random speckles — seam subtle, fine. Make speckles dense so seams invisible.

- Fog + sky dome: sky dome material fog:false.

- ACES: renderer.toneMapping = ACESFilmicToneMapping, exposure 1.0? With Lambert & these colors, 1.05. Colors may wash; tune exposure 1.05.

Lighting: hemi (skyColor 0xbfdfff, ground 0x7f9a5e, 0.85), sun dir (0xfff2dd, 2.6) position (120, 180, 60). No shadows (blob shadows only).

Blob shadow: CircleGeometry(1.4).rotateX(-PI/2), MeshBasicMaterial black transparent opacity 0.28, depthWrite false, renderOrder to avoid z-fight: position y = groundY+0.02 relative root at ground → root at ground so child at y=0.02 ✓ but root y = track surface; wheels touch 0. shadow at 0.02 ok; skid marks at 0.03 could z-fight with shadow — both transparent, order: shadow renderOrder 1, skid 2? Skids drawn after shadows fine (both depthWrite false, drawn in order added; set renderOrder shadow 90, skid 91, particles 100).

Particles texture: radial gradient white→transparent.

**Points shader details**:

```js
const pGeo=new THREE.BufferGeometry();
pGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(MAXP*3),3));
pGeo.setAttribute('aSize', ...1);
pGeo.setAttribute('aAlpha',...1);
pGeo.setAttribute('aColor', ...3);
```

Material ShaderMaterial:

```
vertex:
attribute float aSize; attribute float aAlpha; attribute vec3 aColor;
varying float vA; varying vec3 vC;
void main(){ vA=aAlpha; vC=aColor; vec4 mv=modelViewMatrix*vec4(position,1.0);
gl_PointSize = aSize * (160.0/max(1.0,-mv.z)); gl_Position=projectionMatrix*mv; }
fragment:
uniform sampler2D uT; varying float vA; varying vec3 vC;
void main(){ vec4 t=texture2D(uT, gl_PointCoord); gl_FragColor=vec4(vC, t.a*vA); if(gl_FragColor.a<0.01) discard; }
transparent:true, depthWrite:false
```

Update: for each alive: pos += vel*dt; vel *= (1-2.2dt) horizontal drag, vel.y += (buoy 0.8dt?) dust rises slightly then fades: vel.y decays to +0.5. size = size0*(1+ (1-life)*1.8). alpha = clamp(life/maxLife)*0.55.

needsUpdate on attributes each frame (400 particles trivial).

Spawn function dust(x,y,z, base color, count, spread, vel).

While drifting: each frame spawn 2 per rear wheel: color tan (0.79,0.72,0.6)+rand; grass: (0.45,0.62,0.35). life rand 0.5-0.9, vel = kartVel*0.25 + rand sphere*1.2 + up*rand(0.5,1.5). size rand 0.6-1.3 (world units → gl_PointSize scale factor: at dist 10, size 1 → 16px... choose factor 220: at dist 10 → 22px for size1 ok).

Also exhaust idle puffs at countdown: small gray puffs behind karts — cute; spawn 3/s per kart during countdown. ✓ adds life to intro.

**Countdown kart revs**: karts bob (body pitch oscillate) & wheels don't move; light pulses.

**Timing budget**: everything computed per frame is light.

Now HUD CSS: define palette:

```
--ink:#15171b; --paper:#f5f2e8; --accent:#ff4d1c; --green:#8bd450?
```

Board rows: font bold italic, skewX(-8deg), background rgba(18,20,24,.78), border-left 3px color, backdrop-filter blur(4px) (cheap, fine). Rank number big; name; gap small right-aligned tabular.

Lap box top-right: big "LAP 1/3" + clock under.

Minimap bottom-right? Board top-left, lapbox top-right, map bottom-left, camtag bottom-right, big center. Fine.

Minimap render: precompute pts scaled to 150 canvas with 12px padding, path drawn once to offscreen? Just redraw each frame: stroke track: lineWidth 8 color #2a2e34, then lineWidth 4.5 #4a4f58? Then start line tick accent, kart dots r3 with white outline. Rotate to fit: simple scale fit bbox ✓.

Cam tag: small mono-ish uppercase letter-spaced.

Big text: 130px, italic 900, color paper, -webkit-text-stroke 3px ink? Text stroke + solid offset shadow. Countdown numbers color accent for GO green.

Also small "REC-safe" simplicity: avoid pure white flashes.

Now think about failure modes in AI driving:

1. Steering gain: steerInput = clamp(diff*2.0, -1, 1) with yawMax speed-dependent; if lookahead too short karts weave; lookahead = 5 + speed*0.45 (at 50: 27.5 units ahead ~ 55 samples) ok. Add second farther target blend? Use target = point at la; plus lane from curvature at idx+la2 (la2 = la + 8). Lane applied at target point.

Actually potential oscillation: with lane offsets changing along track and lookahead, kart cuts inside fine. Add damping: steer based on angle error + heading error vs path yaw: input = clamp(diff*1.7 + (pathYaw-yaw)*0.8?) Let me: err = wrap(targetYaw - yaw); steer = clamp(err*2.2, -1,1). yaw += steer*yawMax*dt. With lookahead ~27 units, this tracks smoothly (pursuit). ✓

2. Corner cut risk on hairpin-ish S: apex lane clamp keeps within road; drift widens (slide) — if drift carries wide onto grass, grass slowdown punishes and they recover (steer to target on road). Add safeguard: if |lat| > halfW+2 → strong steer to center: laneTgt = 0 & lookahead shortened. ✓

3. Karts stuck after collisions: soft push + speed floor 6 → recover.

4. Braking calc: probes: for d in [8,16,26,40,58]: idx_p = idx + d/ds; k = maxAbsCurv over span idx..idx_p (step 4): v_c = sqrt(aLat / max(k, 1e-4)) — use kMax over span (not abs, per sign but magnitude). allowed = min(allowed, sqrt(v_c² + 2*brakeDecel*d)). brakeDecel 26. This yields braking before corners ✓. But max over span with sampling every ~4 samples (≈3.5 units) fine.

Also lateral cut: allowed uses aLat*0.8 while drifting? Compute drift after speed decision — order: compute steer & drift state first (based on previous), then allowed with driftFactor = drift? 0.8:1.

5. Overtake side-pick: relProg = wrapProg(other.prog - prog) in (0, 12): latDiff = other.laneCur - laneCur; if |latDiff| < 2.2: choose my shift: prefer side where |laneTgtNew| < halfW-1.6 and toward inside of upcoming corner: insideSign = sign(kAheadSmoothed). shift = insideSign * 2.6 if room else -insideSign*2.6. Set overtakeShift easing in (attack 3/s) with timeout 2.5s or until passed. Also anti-bump: if gap < 3: speedCap = other.speed * 1.02.

Simplify: implement blocking/overtake as: desired = baseLane + wander; then for nearest ahead within 12 & lateral overlap: desired = clamp(otherLane ± 2.6 chosen side, limits). Eases via laneCur damp. Physical push handles contact. Good enough — visible overtakes guaranteed by speed deltas & drift lines differing.

6. prog wrap: prog = lap*L + s where s∈[0,L). lap from -1: initial s = L-6 → prog = -6 ✓ monotonic increasing through 0 ✓.

7. Nearest-sample search must handle high speed: window ±40 each frame — cost 80 dist checks × 6 = fine.

8. Start: karts accelerate at GO: stagger accel with tiny rand delays (0-0.3s) — realism.

Now the track skirt noise function: n(x,z)= sin(x*0.06)*1.2 + cos(z*0.05+2)*1.2 + sin((x+z)*0.02)*2 → ±4 hills far out; near road w≈1 so fine.

Kerb stripes geometry maybe also add on inside of tight corners only — full loop simpler & looks deliberate.

Also add a low wall/barrier? Tire barriers on outside of tight corners: rows of toruses? Instanced torus tires stacked at outer edge of corners 3&7 — cute & cheap: place N tires along s ranges where |k|>0.045 at off = ±(halfW+2.5) outer side (sign of -k? outside = opposite of apex side = -sign(k)*... apex side = +sign(k) left; outside = right when k>0 → offset = -sign(k)*(halfW+2.2)). Tires: TorusGeometry(0.55,0.28) rotateX 90, stacked 2 high, every ~2.2 units. Black with random colored (red/white?) some painted accent. ~80 instances × maybe 2 stacks. Adds "race track" authenticity. 

Item-ish decoration: skip.

Startline banner text: "CRESTLINE GP". Sponsors on boards: "NITRO COLA", "APEX TYRES", "VELOCE FUEL", "PIRANHA PAINT"? avoid Nintendo refs: "1UP" is Nintendo-ish; use generic: "TURBO+ ", "KOYO BRAKES", "SLIPSTREAM", "PIT-STOP COFFEE". Fun ✓.

Flags: along grandstand & some corners: pole + triangle flag (shape via custom geometry or plane with 2 triangles) accent/kart colors; animate rotation.z slight wave via sin.

Right, code size manageable. Let me also handle the countdown camera & transition: store camMode: 'grid'|'chase'|'side'. On GO: camMode='chase' (hard cut ok). During 'grid': cam orbit: center = average of grid front row; angle from -2.6 to -1.6 rad slow. lookAt center.

Also make sure first 30s show a trackside cut: schedule first cut at GO+5s → side cam 3s → chase. Since 30s window from load: countdown ~4.3 + 5 + 3 = 12.3s first side cam ✓ then cuts every ~7s: second cut ~19s, third ~26s ✓ multiple cuts shown.

Trackside cam position should look at kart — lookAt leader each frame, with slight FOV zoom by distance: fov = clamp(38, 60)? set fov = 45 - something. Simple: fov 50 constant, fine. Actually broadcast long-lens look: fov 30 when far. fov = clamp(2400/dist? ) compute: fov = clamp(50 - dist*0.08, 28, 50)? do simple: fov = clamp(2600/dist, 30, 55) → dist 50→52, 80→32.5. update projection each frame when side cam. ✓

Chase cam also: fov 56 + speed*0.12 (→ up to ~62).

Skid marks also on hard braking (speed drop > threshold)? minor; keep drift-only + grass? grass no skids (dust only).

Engine sound — skip (autoplay restrictions).

**Kart numbering on nose?** skip.

Let me also double check r186 API details:

- THREE.CatmullRomCurve3(points, closed, curveType, tension) ✓.
- CanvasTexture, colorSpace ✓.
- InstancedMesh(geo, mat, count); setMatrixAt; instanceMatrix.needsUpdate.
- instanceColor: setColorAt then instanceColor.needsUpdate.
- Fog, HemisphereLight args (sky, ground, intensity) ✓.
- PointsMaterial custom via ShaderMaterial ✓.
- renderer.outputColorSpace default SRGB in r152+ ✓ leave.
- MeshLambertMaterial fine. For tone mapping ACESFilmicToneMapping ✓.

Import map given: "three" → module. Only import three.

Pixel ratio clamp 2. Resize handler.

Antialias true.

Now write everything concretely. I'll carefully write the physics update function.

Constants:

```
const LAPS=3, HALF=7, N=700;
```

Track sampling code:

```js
const cps = RAW.map(p=>new THREE.Vector3(p[0]*0.9, p[1]*1.15, p[2]*0.9));
const curve = new THREE.CatmullRomCurve3(cps, true, 'centripetal');
const trackLen = curve.getLength();
const ds = trackLen/N;
const pts = curve.getSpacedPoints(N); // N+1, last ~ first
P = pts.slice(0,N)
for i: T[i] = P[(i+1)%N] - P[(i-1+N)%N], normalize; yaw[i]=atan2(T.x,T.z);
Sd[i] = new Vector3(-T.z? left = up×T = ( T.z*1? compute: up×T = (1*T.z - 0*T.y? formula a=(0,1,0), b=(Tx,Ty,Tz): cross = (1*Tz - 0*Ty, 0*Tx - 0*Tz, 0*Ty - 1*Tx) = (Tz, 0, -Tx). For T=(1,0,0): (0,0,-1) ✓ left.
So Sd = (Tz, 0, -Tx) normalized (T normalized).
curv raw: k[i] = wrap(yaw[i+1]-yaw[i-1])/(2*ds). smooth 2 passes window ±6.
```

Note yaw sign vs left: turning left = yaw increasing (derived: from +z toward +x is left and yaw increases... let me re-verify: yaw=atan2(Tx,Tz). T=(0,0,1)→0 (facing +z). Left of +z is +x (established: right=-x, left=+x). T=(1,0,0)→atan2(1,0)=+π/2 ✓ yaw increases turning left. And Sd=left. Apex side for k>0 (left turn) = left = +Sd ✓ consistent with earlier.

heightAt(i, lat): base = P[i].y; if |lat| <= 8.4 → base (+ kerb negligible); else w = falloff(|lat|): piecewise from skirt table (8.4→1, 13→0.8, 20→0.55, 32→0.3, 52→0.12, 80→0.02, 120→0): y = base*w + (GROUND + noise(i))*(1-w). Implement skirtW(off).

Actually build skirt mesh using exactly skirtW & groundNoise so karts on grass match visuals ✓.

groundNoise(x,z) = sin(x*0.045)*1.1+cos(z*0.043)*1.0+sin((x+z)*0.021)*1.6 → ±3.7, plus base -0.4. At far offsets mountains of grass — nice rolling terrain. But careful: grandstand/trees placed with this function ✓ share.

**Skirt geometry builder**:

```js
function buildSkirt(sign){ // sign +1 left, -1 right
 const offs=[8.4, 12, 18, 26, 38, 55, 80, 115];
 rows: i 0..N (wrap dup), each off: pos = P + Sd*off*sign, y = trackY*W + (GROUNDY + noise)* (1-W)
 uv: u = (off-8.4)/10 (repeat via texture repeat? set uv = off/7 for u tile, v = i*ds/7)
 indices grid.
}
```

W computed from off via same piecewise function — define skirtW(off) piecewise linear through same array with W values [1,0.9,0.72,0.5,0.28,0.12,0.03,0].

Wait must match heightAt: heightAt uses W(off) ✓ same function.

Grass material: Lambert map grassTex, color 0xffffff. Texture repeat handled by uv values (u = off/7 → tiles every 7 units across, v every 7 along): set v = i*ds/7, u = off/7 ✓.

**Road ribbon with lift**: road y lift +0.02? Keep road at trackY exactly, skirt at off 8.4 W=1 → same y → tiny gap band between kerb outer (8.4) and skirt start (8.4) continuous ✓. Kerb from 7→8.4 raised 0.06/0.02 — small step; grass W at 8.4 =1 → trackY, kerb outer 0.02 above — fine.

Start line ribbon 0→3.5 units: rows idx 0 and idx ceil(3.5/ds): lift +0.04. UV u 0..1, v 0..1 checker canvas with squares 10×2? Road width 14 → 10 squares of 1.4 ✓.

**Gantry**: at idx 2 (a bit past line? place exactly at idx0): posts: cylinders r0.25 h6 at lat ±(HALF+1.2), y from trackY; crossbar: box(len=2*(HALF+1.2)+1, 1.5, 0.6) centered y+5.4; banner texture on box front/back (materials array: [side,side,side,side,front(banner),back(banner)]) — box materials order: +x,-x,+y,-y,+z,-z. Orient group along Sd/yaw. Lights: 3 spheres at lat -1,0,1... hang below crossbar y+4.6, sphere r0.28, mat MeshBasic? emissive look: MeshBasicMaterial color dark red #3a0d08; when on: color bright #ff3b2f — toggling basic color is enough (glow-ish via bloom none; fine + scale pulse).

Orientation: group.position=P[2]; group.quaternion from yaw: rotation.y = yaw[2]. In group local: forward +z? our yaw convention forward=(sin,0,cos) meaning local +z is forward when rotation.y=yaw ✓. So crossbar along local X ✓ posts at x=±8.2 ✓ banner faces +z/-z (front/back along track) ✓.

Mid arch similar with different banner "SECTOR 2" at idx ~ N*0.55.

**Grandstand** positioning: pick idx at s = L*0.5? No — near main straight before line: straight is last segment P13→P0→P1. Put stand along idx range around s = L - 40? Center stand at idx ≈ N - 40/ds? Let me place at P[0] shifted back along track: sLine0=0; stand center s = L - 30 (30 units before line, outside = +z side at straight? At P0 heading +x, left = -z, outside = -left? loop interior: the loop extends z<74 → interior = -z side = left side. Outside = +z = -Sd. Stand center = P0 + (-Sd)*(HALF+7) i.e., lat -19 in Sd terms... use lat = -(HALF+12) = -19. Stand extends along tangent ±23. Also small chance overlapping billboards — fine.

Build stand group with local axes: rotate y = yaw so local X along track. Steps: 4 rows: row r: box(40, 1.0, 2.4) at local (0, r*0.85+0.5, -(1.4 + r*2.0))? Wait depth direction = local +z is track-forward; stand faces track: stand placed outside, its front toward track = local -z? Track center is at lat direction: with group at lat -19*... ugh signs. Let me place stand group at P0 shifted by Sd*+? Let me just set standGroup.position = P0.clone().addScaledVector(Sd0, 20).add(0,0,0); with Sd0 = left = -z at start → that puts it INSIDE (z smaller). I want outside +z: Sd0 = (Tz,0,-Tx) with T≈(1,0,0) → Sd=(0,0,-1) → Sd*20 → z-20 → inside. So use -20: position = P0 - Sd0*20 → z 74*0.9=66.6 +20 → z 86.6 outside ✓.

Stand rotation.y = yaw0 (+x heading → yaw=atan2(1,0)=π/2). Group local axes rotated: local +z maps to world (sin yaw,0,cos yaw) = (1,0,0) = +x = track direction ✓. Local +x maps to (cos yaw,0,-sin yaw) = (0,0,-1) = -z = left = toward track? Track center is at lat +19 relative... stand at world z 86.6, track at z 66.6 → track is -z direction from stand = local +x direction ✓ so stand faces -localX? I'll orient rows along local z (length along track) and stack rows increasing local +x (away from track) with height: row r at local x = r*2.0, y = 1 + r*0.85, box depth along x 2.0, width along z 40, height 1.7 (so seats above previous row). Crowd texture on top faces... simplest: each row box material crowd all over (MeshLambert with crowdTex, repeat scaled). From chase cam you see colorful steps ✓. Roof: thin box (44,0.3,7) at x=3.2, y=5.4, accent color + 4 post cylinders front edge. Plus advertising banner front: plane (40,1.1) at x=-0.9 facing track (rotation.y = -π/2? plane default faces +z; to face local -x: rotation.y=-π/2) with sign texture. Good enough.

Compute once.

**Fences/tire stacks**: at 2 tightest corner outsides — find corners: idx ranges where smoothed |k| > 0.05 contiguous; take top 2-3 segments, place tires along outer edge lat = -sign(k)*(HALF+2.6): torus r0.5 tube0.26, rotX(π/2) flat, stack 2. Instanced count = sum lengths/2.2*2. Cap 160. Color: mostly #1c1d20, every 5th red or white via instanceColor ✓ (MeshLambert supports instanceColor? InstancedMesh.setColorAt works with materials using color — yes, with Lambert it multiplies.)

Skip if too fiddly — it's straightforward loops, keep.

**Trees**: 130: idx random, side random, off = 12 + rand*45 (skip if |k|>0.05 && off < 16 near racing edge? whatever). y = heightAt. Two types. Also distance-based fog handles blend. Also cluster density: fine random.

Trees near start straight outside could block side cams — cams pick positions; visual overlap acceptable.

Billboards 8: idx = i*N/8 + offset, alternate side; plane at lat = -(HALF+5) or +(HALF+5) alternating; lookAt track point → set plane rotation.y = yaw + (side facing). Implement: group.position = P + Sd*latSign*(HALF+5); group.lookAt(P.x, group.position.y, P.z) → plane child rotated to face group -z? lookAt orients +z toward target → plane (faces +z) visible ✓ place plane at group origin, posts below.

Sign textures: bg colors flat (#f2e9d8 cream with ink text, or accent bg white text), text italic 900. Also small stripe footer.

**Now the Kart class** (write carefully):

```js
class Kart{
 constructor(cfg, gi){
   this.cfg=cfg; this.name=cfg.name;
   this.maxSpeed = cfg.speed; this.aLat=cfg.aLat; this.accel=22+rand(0,3); this.brake=30+rand(0,6);
   this.laneBias = rand(-1.4,1.4);
   build mesh... this.root, this.body, refs.
   this.reset(gi);
 }
 reset(gi){
   const row=gi>>1, col=gi&1;
   const s = trackLen - 8 - row*5.5;
   const idx = Math.floor(s/ds)%N;
   const lat = (col? 2.3 : -2.3);
   const p=P[idx], sd=Sd[idx];
   this.pos = new THREE.Vector3(p.x+sd.x*lat, 0, p.z+sd.z*lat);
   this.idx=idx; this.s = s; this.sPrev=s; this.lap=-1;
   this.yaw = yawArr[idx]; this.speed=0; this.steer=0; this.steerVis=0;
   this.drift=0; this.slide=0; this.hop=0;
   this.laneCur=lat; this.laneTgt=0; this.otTimer=0; this.otShift=0;
   this.finished=false; this.finT=0;
   this.groundY = p.y;
   this.prog = -((trackLen - s)) → compute: lap*L + s = -L + s = -(8+row*5.5) ✓
   update visuals instantly.
 }
 ...
}
```

Hmm groundY: pos y stored separately: pos.y = groundY always (root at surface). I'll keep this.pos with y included (set each frame).

update(dt, t):

```
// --- nearest sample search
let best=this.idx, bd=Infinity;
for(let o=-8;o<=40;o++){const k=(this.idx+o+N)%N; const dx=this.pos.x-P[k].x, dz=this.pos.z-P[k].z; const d=dx*dx+dz*dz; if(d<bd){bd=d;best=k;}}
this.idx=best;
const i=this.idx;
// lateral
const lat = (this.pos.x-P[i].x)*Sd[i].x + (this.pos.z-P[i].z)*Sd[i].z;
this.lat=lat;
const onRoad = Math.abs(lat) < HALF+0.4; // kerb counts
const onKerb = !onRoad && Math.abs(lat)<HALF+1.8;
```

Wait HALF=7, road edge 7, kerb to 8.4: onRoad |lat|<=7.4; kerb 7.4-8.4 (slight bump: body jitter + tiny speed keep). grass beyond 8.4.

Racing progress s: s = i*ds + forward projection: proj = (pos-P[i])·T[i]; s = (i*ds + proj + L) % L.

Lap crossing: if this.sPrev > L*0.75 && s < L*0.25 → this.lap++; if lap===LAPS → finished=true... Also handle reverse crossing (recovering) : if sPrev < L*0.25 && s > L*0.75 → lap--. ✓

prog = lap*L + s.

--- AI target:

```
const look = 6 + this.speed*0.5; // units
const li = (i + Math.round(look/ds)) % N;
const li2 = (i + Math.round((look+10)/ds)) % N;
// base racing lane: apex hugging using curvature ahead
const kA = kSmooth[li2];
let lane = clamp(kA*38, -1, 1) * (HALF-1.9) ; // hug apex
```

Hmm gain: max |k| ~ 1/18=0.055 → 0.055*38=2.09 → lane ±(HALF-1.9)=±5.1 clamp ✓; gentle k=0.01 → 0.38 small. Pre-apex? Add out-in: combine curvature now vs ahead: lane = clamp( (kNear*10 + kFar*30) ...). Keep simple: apex hug at target point gives decent lines. Add slight out-in: anticipate: lane = clamp(kA,−1,1 normalized) * (HALF-1.9) — plus bias.

lane += this.laneBias*0.5; lane += this.otShift; clamp to ±(HALF-1.5).

Lane target smoothing: this.laneCur += clamp(lane - laneCur, -dt*3.5*?, ...) use exponential: laneCur = damp toward laneTgt rate 2.2.

Then target point: tp = P[li] + Sd[li]*laneCur... using laneCur (current) at li.

desiredYaw = atan2(tp.x-pos.x, tp.z-pos.z);
err = wrap(desiredYaw - this.yaw);
steerIn = clamp(err*2.4, -1, 1);

Drift logic:

```
const cornering = Math.abs(kSmooth[(i+Math.round(18/ds))%N]);
if(this.drift===0){
  if(onRoad && this.speed>27 && Math.abs(steerIn)>0.62 && Math.abs(kA)>0.028){ this.drift=Math.sign(steerIn); this.hop=1; }
} else {
  if(Math.abs(steerIn)<0.34 || this.speed<20 || Math.abs(lat)>HALF+0.6) this.drift=0;
}
```

slideTgt = drift? (0.30 + Math.abs(steerIn)*0.22)*clamp(this.speed/40,0.5,1) : 0; slide damp toward slideTgt (rate 3.5 in, 5 out). hop decay: hop -= dt*3.2; hopY = sin(clamp(1-hop... track hopT from 1→0: bodyY = sin(hop*π)*0.3.

Yaw update:

```
const yawMax = Math.min(3.0, this.aLat*1.7/Math.max(this.speed,6));
this.yaw += steerIn*yawMax*dt + this.drift*0.9*dt*clamp(this.speed/30,0,1);
```

drift extra rotation makes drift tighter (counteracts widen). ✓

moveYaw = this.yaw - this.slide*this.drift; (slide>=0)

Wait careful: drift=+1 (left): moveYaw = yaw - slide ✓. drift=-1: moveYaw = yaw + slide ✓.

Speed control:

```
let vAllow=this.maxSpeed * (this.finished?0.85:1) * (onRoad?1:(onKerb?0.96:0.42));
// grass rough: also add noise
const probes=[6,14,24,38,56,80];
for(d of probes){ const pi=(i+Math.round(d/ds))%N; let km=0; for(let q=0;q<=Math.round(10/ds);q+=3){ km=Math.max(km, Math.abs(kSmooth[(pi+q)%N])); }
  const vc = Math.sqrt(this.aLat*(this.drift?0.8:1)/Math.max(km,0.004));
  vAllow = Math.min(vAllow, Math.sqrt(vc*vc + 2*this.brake*d));
}
// rubber band
const gapL = leaderProg - this.prog; if(gapL>0) vAllow *= 1+Math.min(gapL/900, 0.05); else vAllow *= 1 - Math.min(-gapL/900,0.02)*? keep tiny.
```

Hmm rubber band: multiply maxSpeed portion only; fine to multiply vAllow.

Also overtaking boost off drift: drift exit mini-boost: when drift ends and was >0.6s: speed += 2.5 (feels MK) ✓ small.

Throttle:

```
if(this.speed < vAllow - 0.5) this.speed = Math.min(vAllow, this.speed + this.accel*dt*(1 - 0.35*this.speed/this.maxSpeed));
else if(this.speed > vAllow+1) this.speed = Math.max(vAllow, this.speed - this.brake*dt);
else this.speed += (vAllow-this.speed)*Math.min(1,dt*3);
```

Position:

```
const my = moveYaw;
this.pos.x += Math.sin(my)*this.speed*dt;
this.pos.z += Math.cos(my)*this.speed*dt;
```

Height: groundY via sample: gy = heightAt(i', lat) where i' = nearest (use i + proj adjust: use i). Set pos.y = gy (plus smoothing to avoid steps: pos.y = lerp(prev, gy, 0.5)).

Collision (pairwise, done globally after all updates):

```
for pairs: d = dist(posA,posB) horizontal; if d<1.75: n=(A-B)/d; push=(1.8-d)*0.5; A+=n*push; B-=n*push;
 rear (smaller prog within 6): rear.speed = min(rear.speed, front.speed+1.5); tiny yaw jolt?
```

Drift/skid state: skidding = this.drift!==0 && speed>18 && onRoad. While skidding: spawn dust at rear wheels each frame (2 per wheel), spawn skid quads every 0.025s (timer). Grass: dust green + rumble.

Visuals update:

```
root.position.copy(pos); root.position.y = groundY;
root.rotation.y = this.yaw;  // nose heading
// slope pitch:
root.rotation.x = -Math.asin(clamp(T[i].y,-0.6,0.6)) ... 
```

Wait rotation order YXZ: root.rotation.order='YXZ'. pitch sign: forward local +z; climbing → nose up = rotation.x negative ✓ (checked). But yaw uses world yaw where forward=(sinYaw,0,cosYaw) matches local +z→world ✓.

body.rotation.y = extra drama 0? The nose already includes slip visually? Nose = yaw, velocity = moveYaw: root rotated to yaw; velocity direction differs — visually kart appears sliding ✓. Additional body.rotation.y = -slide*drift*0.35? that would reduce apparent angle (making body toward velocity)... Actually more Mario look: kart rotated MORE into corner: body.rotation.y = slide*drift*0.45 extra counter? Hmm: classic drift shows kart nose pointing MORE inside than motion — root yaw already does that relative to velocity. Add a bit more: body.rotation.y = drift*slide*0.5 ✓ (left drift: nose further left).

Roll: body.rotation.z = -drift*slide*0.55 (lean into? computed earlier lean into left turn = negative z for drift+1 ✓).

Hop: body.position.y = hopY; grass rumble: += rand jitter when off road.

Wheels: steerVis → front groups rotation.y = steerVis*0.5; spin all wheel meshes rotation.x += speed/0.34*dt (rear r bigger 0.36: separate).

Driver: head.rotation.y = steerVis*0.5; body lean small; steering wheel rotation.z? torus tilted; rotate around its local axis: wheel.rotation.y? Place steering wheel tilted; spin rotation.z = steerVis*1.2 — okay approximate.

Exhaust pipes: two small cylinders at rear — puffs.

Blob shadow: child of root at y 0.02 (root at ground): but when hopping body rises, shadow stays ✓ shadow on root not body ✓. Scale slightly with hop (1 - hopY*0.3), opacity fade.

Track pitch uses T at idx — plus hillcrest airtime? skip (karts glued).

**Standings**: arr = karts.slice().sort((a,b)=> (b.finished?-1e9? finished karts ranked by finT order ahead? Once finished, keep them ahead: sort key: finished? (1e9 - finT*?) : prog... finished earlier = higher. key = a.finished ? 1e7 + (1e5 - a.finT) : a.prog? Mixed units: finT small (<60): 1e7 + (1e4 - finT) vs prog max = LAPS*L + L ≈ 3*486 ≈ 1458. So finished keys 1e7+ dominate ✓.

**HUD update**: for rank r, kart k: row element: rank text, name, chip color (static), gap text: k===leader? 'LEADER' : '+'+gap.toFixed(1)+'s' — but also show lap "L{lap}"? Keep gap. Also highlight rows moving: reorder via style.order = r.

Row markup:

```
<div class="row"><span class="rk">1</span><span class="chip" style="background:#..."></span><span class="nm">PEPPER</span><span class="gp">LEADER</span></div>
```

Leader row class 'ld' → accent border.

**Clock**: from goTime: t - goTime while racing; freeze at leader finish (store raceTime). format m:ss.t.

**Lap display**: leaderLap = clamp(leader.lap+1,1,LAPS); text `LAP ${x}/${LAPS}`; during countdown "LAP –/3"? show "LAP 1/3" pre-race fine. After finish: "FINISH".

**Countdown implementation** in tick:

```
state: 'cd'|'race'|'post'
cdT counts down from 4.6: 
 thresholds: >3.7: title "CRESTLINE GP" (class small), 3.7-2.8: '3' + light1, ... GO at <=0.9? 
```

Let me define: cdT from 4.6 → 0; display mapping: cdT>3.6: intro text; (3.6,2.7]: '3'; (2.7,1.8]: '2'; (1.8,0.9]: '1'; (0.9,0]: 'GO!' — and karts released when cdT<=0.9 (GO moment) — then big shows GO until 0.4. Beep on each transition (track lastStage). Lights: stage≥1..3 red on; at GO lights off + green? swap to green emissive for 1s then off.

Karts: speed locked 0 during cd (skip physics except visuals & exhaust puffs & rev jitter). At GO: state='race', raceT starts 0.

Post: when leader.finished && raceT > leaderFinT + 5 → resetAll → state 'cd' again (cdT=4.6, keep camera mode → countdown dolly cam).

During 'post', karts keep racing (AI unaffected, finished flag slows 0.9×? keep them racing so scene stays alive; leader.finished only affects standings order & banner). Also maybe confetti at finish? Could spawn colorful particles above leader — reuse dust system with random bright colors & gravity! ✓ cheap & celebratory. Spawn burst at finish line moment.

**Cameras implement**:

```
let camMode='grid';
chaseCam(): const k=leader; fwd=(sin yaw,0,cos yaw); drift offset: sideAmt = -k.drift*k.slide*3.2;
 desired = pos - fwd*(7.2+speed*0.05) + up*(3.1) + sideVec*sideAmt
 camPos.lerp(desired, 1-exp(-dt*4.5));
 look = pos + fwd*5 + up*1.1; lookSm.lerp(... rate 9);
 cam.position.copy(camPos + small shake at speed? skip); cam.lookAt(lookSm); cam.fov=...
```

Also prevent camera below ground: camPos.y = max(camPos.y, heightAtApprox(camXZ)+1.2)? compute nearest sample to camera? Cheap: use leader ground y + 2.4 minimum and terrain func heightAt needs (i,lat) — camera anywhere: compute nearest sample to camera pos quickly (reuse coarse search every frame? full N scan 700 × once per frame is fine!). Terrain height fn from (x,z): need i — do full scan for camera (700 iters) OK. camY = max(desired, h+1.5).

Trackside: pick camIdx among TSCAMS with dist to leader in [18, 110], choose random weighted by closeness; set once per cut. During side cam: lookAt leader pos+up*0.8; fov dynamic.

Grid cam: dolly: center = avg of kart positions (or P[L-10]); angle sweep: a = -0.7 + (1-cdT/4.6)*0.9; radius 15; camPos = center + (sin,cos)*(r) at y center+4.5; look at center+1. Set each frame (smooth by construction).

At GO switch to chase: initialize camPos behind leader instantly to avoid lerp swoosh from grid cam: set camPos = desired exactly.

**Skid instancing pool**:

```
const SKN=700; skGeo=PlaneGeometry(0.34,1.5).rotateX(-Math.PI/2); skMat=MeshBasicMaterial({color:0x14? use 0x0d0d0f, transparent:true, opacity:0.42, depthWrite:false}); skMesh=InstancedMesh(skGeo,skMat,SKN); skMesh.count=SKN initially all scale 0.
let skHead=0; function addSkid(x,y,z,yaw){ const m=new THREE.Matrix4()... compose(pos(y+0.02), quatY(yaw), scale(1,1,1)); skMesh.setMatrixAt(skHead,m); skHead=(skHead+1)%SKN; skMesh.instanceMatrix.needsUpdate=true; }
```

Per-kart skid timer spawn every 0.03s per wheel while skidding → covers long marks (segment length = speed*0.03 ≈ 1.0-1.5 matches quad length 1.5 ✓).

Reset: zero all matrices (scale 0) loop.

Wait plane rotateX(-π/2): plane in XY → after rotX -90: lies in XZ, length along? PlaneGeometry(w,h): w along x, h along y; after rotateX(-90°): y→z... h becomes along z ✓ forward = +z? Rotation to align with moveYaw: mesh rotation.y=yaw aligns local +z to world forward (sin yaw,0,cos yaw) ✓ since local z after geometry rotation stays z. ✓

Also add slight opacity variance? fine constant.

**Dust color** also for exhaust: gray puffs.

Confetti: colors random from palette, gravity: in particle update, type? Add per-particle gravity flag: store in vel update: I'll include aGrav attribute? Simplify: use color/behavior same; confetti: vel up 6-9, gravity applies: I'll add global gravity constant per particle via array g[] (dust g=-0.4 buoyancy? dust: vel.y += 0.6*dt rise; confetti: vel.y -= 9*dt). Store gy per particle. ✓

Now write out everything for real. I must be careful about length — it's long but fine. Let me also make sure no external fonts: CSS uses local stack.

One more consideration: the "position list (1st to 6th)" — I'll show all six rows always. Lap counter top-right. ✓

Countdown: overlay big numbers ✓ lights ✓.

No keyboard ✓ no controls (OrbitControls not needed).

Import map provided — only `three` import needed.

Write CSS thoughtfully:

```css
*{margin:0;box-sizing:border-box}
html,body{height:100%;overflow:hidden;background:#0b0d10;font-family:'Futura','Trebuchet MS','Segoe UI',Verdana,sans-serif}
#ui{position:fixed;inset:0;pointer-events:none;z-index:5}
.panel{background:rgba(16,18,22,.82);color:#f4f1e8;backdrop-filter:blur(3px)}
#board{position:absolute;top:14px;left:14px;padding:10px 12px;border-radius:10px;...}
```

Rows skewed: `.row{display:flex;...;transform:skewX(-8deg)} .row>*{transform:skewX(8deg)}`? Unskew content might complicate; simpler: skew only background via ::before? Simplest: skew whole row slightly and don't unskew text (italic look intended). Fine: skew rows -8deg and set font italic — cohesive slanted look.

Chips: 10px squares with kart color + border.

Big overlay: #big absolutely centered, font-size clamp(90px, 18vw, 170px), italic 900, letterspacing, color #f4f1e8 with text-shadow: 6px 6px 0 #15171b (hard offset — chunky arcade, not glow ✓). Classes .pop animation keyframes scale 1.8→1 fade in, and .fade for out. GO uses color #7fd63c; FINISH uses accent; intro uses smaller.

Also add subtle vignette overlay for cinematic feel: radial-gradient? That's a gradient... decorative gradient — vignette is subtle photographic device; I'd rather skip to stay clean. Skip.

Cam tag bottom-right small panel.

Minimap: canvas with panel styling.

Title intro: incorporate into big overlay as class .small (font-size 40px letterspaced) showing "CRESTLINE GP — 3 LAPS".

Now particles MAXP=500.

Let me now also decide track texture repeat: asphalt tile 9 units: uv v = s/tile where tile = L/round(L/8).

Kerb tile 3.4.

Grass tile 7.

Write buildRibbon generic with (offInner, offOuter, liftInner, liftOuter, mat, tileV) for left side where offInner>offOuter? I'll write explicit small builders to avoid sign bugs:

road: rows i in 0..N (dup seam): vertex L = P+Sd*+7 (y+0), R = P+Sd*-7.
kerbL: A = +7 (y+0.07), B = +8.4 (y+0.02).
kerbR: A = -7 (y+0.07), B = -8.4 (y+0.02).
skirt side handled separately with its own builder.

Kerb uv: u 0..1 across, v = s/tile; texture: red/white halves along v: canvas 32w×64h: top 32 rows white, bottom red → repeats ✓. Kerb mats: left & right can share.

Road: asphalt canvas 128: base #3d4045, 1400 speckles ±, some darker patches (racing line hint: two darker vertical bands? Draw 2 darker blurred bands along v direction center-ish? optional skip).

Start line: separate small ribbon with checker.

Grandstand crowd canvas: 128×64 dark bg + 300 random dots in palette.

Billboard canvases: per sponsor: 256×96: bg color, stripe, text italic bold centered, small sub-caption.

Banner "CRESTLINE GP" 512×96: dark bg, paper text, accent slashes.

Mountains: cones with flat lambert colors (#7d90a6, #93a7ba alt), fog will haze ✓.

Cloud material MeshLambert emissive? white with fog... clouds far → fogged heavily (fog far 900; clouds at 300-500 → partially fogged nice).

Fog: new THREE.Fog(0xdfeef2, 260, 950). Sky dome radius 1000 > fog far — dome itself fogged? Set skyMat.fog=false ✓. Background color same as fog as fallback.

Sun: DirectionalLight(0xfff1dc, 2.8) pos (150,200,80). Hemi: (0xcfe8ff, 0x8fae6d, 0.9). Ambient extra 0.15? Hemi covers.

Tone mapping ACES exposure 1.1.

Materials: kart bodies MeshLambert (matte toys) + slight MeshPhong for helmets? Keep Lambert everywhere; accents via colors. Maybe MeshStandard for road? Lambert fine.

**Performance check**: draw calls: road+kerbs+skirts(2)+ground+sky+startline+gantry(3-4)+arch(3)+boards(8×2)+stand(6)+trees(3 instanced)+tires(1)+mountains(1 instanced or merged: use InstancedMesh cone 14)+clouds(~8 meshes or 1 instanced)+balloons(2×2)+karts(6×~15=90)+skid(1)+particles(1)+flags(6×2). ~120 draw calls — fine.

Kart mesh detail: merge? Each kart ~14 meshes ×6 = 84 calls. Acceptable.

Now write the code — final pass for correctness of every math sign.

Track direction & side: verified. Left offset positive.

**Grid stagger**: grid positions lat ±2.3 both within road ✓.

**Countdown camera**: center at P[N-12] area (grid): compute gridCenter = avg kart pos. camPos = center + rot(angle)*(dist 16) + y+4.2; look center+1. Angle from -2.9→-2.2? Add slow push-in radius 17→13. Look nice.

**Ensure karts visible in first 30s**: ✓.

**Post finish camera**: keep chase; maybe during 'post' switch to a slow orbit around winner? Keep chase; fine.

Now particulars for sorting stability: recompute standings each frame cheaply.

**heightAt(i,lat)**: 

```
function skirtW(off){ // 8.4→1 ... 115→0, piecewise via table
 const T=[[8.4,1],[12,0.88],[18,0.62],[28,0.4],[45,0.2],[70,0.07],[115,0]];
 ...
}
function groundN(x,z){ return Math.sin(x*0.043)*1.2+Math.cos(z*0.037+1.7)*1.1+Math.sin((x+z)*0.019)*1.8; }
function heightAt(i,lat){ const a=Math.abs(lat); const base=P[i].y;
 if(a<=8.4) return base;
 const w=skirtW(a); return base*w + (-0.5+groundN(P[i].x+Sd[i].x*lat, P[i].z+Sd[i].z*lat))*(1-w);
}
```

But skirt builder must use the same → consistent ✓. Note skirt vertex y uses lat = off*sign.

Edge case: adjacent skirt rows sample noise continuously ✓.

Kerb outer 8.4 y=+0.02 vs skirt at 8.4 y = base → tiny 0.02 lip fine (add lift 0.02 to skirt first ring? leave, invisible).

**Road seam**: rows 0..N with row N = sample 0 but v = L/tile (non-integer tiles issue solved by tile chosen to divide L exactly: tile = L/round(L/8) ✓ so v=round(L/8) at seam → texture period matches ✓.

**Curvature for lane & speed**: kS[i] smoothed; magnitudes: corner radius r → k=1/r. Chicane r~20 → 0.05. v=sqrt(aLat 40/0.05)=28 ✓.

Let me double-check the chicane geometry radius from control points: P5(60,9,-20), P6(28,8,-10), P7(8,9,-34): the direction changes: P5→P6 (-32,10), P6→P7 (-20,-24): angle of each: atan2 in plan: seg1 angle = atan2(10,-32)... net turn between seg1 and seg2: cosθ = (640-240)/(33.5*31.2)= 400/1041=0.384 → θ=67° spread over two segments ≈ radius ~ ds_seg/(θ/2)? Segment lengths 33.5 & 31; if 67° turn distributed, radius ≈ arc/θ ≈ (33.5+31)/2 / 1.17 ≈ 27.6 → k≈0.037 → v=sqrt(40/0.037)=33. Hmm moderate. The CatmullRom will round further. Plus P7→P8 (-32,-18) turns back. So chicane peak |k| maybe 0.04-0.05 → v≈29. OK drift corners ✓. The 90°-ish turn near P3(104,22)→P4(88,7): seg3 (8,-36) → seg4 (-16,-15): cosθ=(8*-16 + (-36)(-15))/(37*21.9)= (-128+540)/777=0.53→58°: radius ≈ 37/1.0 ≈ 30ish. Sweeper top-right radius bigger. Min corner speeds ~ sqrt(40/0.05)=28. Fine — braking visible from 50→28.

But will karts drift? Trigger: |steer|>0.62 && |kA|>0.028 && speed>26. At corner entry speed still high (50→ braking), steering err grows → steer>0.62 likely ✓ drift engages, slide 0.3-0.5, dust ✓. Long sweepers k≈0.015 no drift, just steering ✓ variety.

yawMax: aLat*1.7/speed: at 28: 40*1.7/28=2.43 rad/s; required ω = v/r = 28/25 = 1.12 ✓ plenty authority to hold line even with slide.

Slide affects width: velocity yaw lags by slide rad: extra outward radius ≈ ... with yaw turning at ω and slide s, the kart runs wider by roughly v*s/ω? s=0.35 → wider by 0.35*r ≈ 9 units?? Too much — would fly off. Hmm: steady-state: heading rotates with track; velocity direction = heading - slide: if heading exactly tracks tangent yaw, velocity points slide*inside→outward: lateral drift speed = v*sin(slide)≈v*slide = 28*0.35 ≈ 10 u/s outward!? That's wrong sign thinking: in a left corner, tangent yaw increases; kart's velocity should point slightly OUTSIDE (right of tangent? no—sliding outward means velocity more toward outside = velocity yaw = tangent - slide (for left turn, outside is right = decreasing yaw) ✓ that's what we have: moveYaw = yaw - slide: kart drifts outward at v*sin(slide) ≈ 10 u/s while the corner pulls... In steady cornering, yaw rate ω rotates the velocity vector too: lateral acceleration = v*ω_total. If kart travels along a circle of radius r: velocity direction rotates at ω = v/r. If heading = velocity + slide, heading rotates at same ω. The kart position moves along velocity; to stay on circle, velocity must rotate — it does via heading rotation ✓. So "runs wider" isn't from slide per se — it's from the AI target: if AI steers heading to track the racing line, velocity = heading - slide points outward from target line → kart runs wide by amount depending on how steering corrects. The pursuit controller will point nose further inside to compensate: err includes position error → nose deeper inside → bigger visual slide ✓ and net path stays near line. Net effect: looks drifty, stays on road. But steering authority must compensate: extra lateral error correction needs yaw rate ≈ ω + (v*slide)/r? With yawMax 2.4 vs needed v/r + slide compensation... compensation rate ≈ v*slide / lookahead? The pursuit handles it as long as err gain ok. Risk: oscillation. Mitigate: reduce slide magnitude 0.22-0.38, and increase steer gain 2.6, lookahead moderate. Also clamp slide effect by reducing it at high speed? Set slideTgt max 0.32. And lane target during drift = deeper apex (adds margin): if drifting, lane -= drift*1.2 (aim further inside) ✓ classic.

I think tuning: slideTgt = drift? clamp(0.16+|steer|*0.22,0,0.34):0; moveYaw offset ±0.32 → lateral slip v*0.32≈9-16?? v*sin(0.32)=v*0.31≈ 10 u/s. That's a LOT of slip velocity... but the pursuit correction redirects heading more inside so path curves back — net path deviation depends on controller. To be safe, make slide mostly VISUAL: reduce physical slip: moveYaw = yaw - slide*drift*0.5 (physical half), body visual full slide. Compromise physical 0.5× (max 0.16 → slip ~5 u/s). OK.

Also drift corner speed: during drift aLat*0.8 → corner caps lower → karts slow in drifts ✓.

Test mentally hairpin: k=0.05 (r20), approach 50: braking: allowed at d=0: sqrt(40/0.05)=28; probes ensure decel from 50→28 needs d = (2500-784)/(2*30)=28.6 → braking starts ~29+ units before ✓ AI brakes on approach ✓.

**Collision with tires/barriers**: karts never leave road normally; skip barrier collision.

**Overtake logic** concrete:

```
// in update, every frame cheap:
this.otShift approach 0 (decay rate 1.5/s) unless active target.
find ahead: for others: dp = wrapL(o.prog - this.prog) in (0.5, 13); lateral gap = o.lat - this.lat; if |gap|<2.6 && speed> o.speed-2:
  choose side: prefer inside upcoming: inSig = Math.sign(kSmooth[li2]) || 1;
  let want = o.lat + inSig*2.7; if |want| > HALF-1.7 → want = o.lat - inSig*2.7;
  if |want| <= HALF-1.4: this.otShift = want - baseLane? 
```

Simpler: set this.laneTgt directly = want (override) with timer 1.2s. Also rear-kart speed cap if dp<3.2: speed = min(speed, o.speed+1.5). Store o ref to avoid recompute — fine each frame (6 karts → 30 pairs).

Also lateral proximity in world (lat defined via own idx; both near same idx fine).

**Wrap prog diff**: dp = o.prog - this.prog; since both near (racing), no wrap issue except start (-) fine.

**Also side-by-side same speed**: both pick same side? They compute want from each other symmetric... A ahead picks nothing (only looks ahead) → B dodges ✓ no conflict.

Alright, also **HUD leader name in cam tag**.

**Countdown revs**: during cd, body.position.y = 0.03*sin(t*40+phase) jitter, exhaust puffs.

**GO burst**: spawn dust burst behind each kart at GO ✓.

Let me now also compute grid center for cd cam: karts at s≈L-8-row*5.5, lat ±2.3 → center ≈ P[N-16]. camAngle sweep.

**Trackside cams list**: build from samples every N/18: lat alternate ±(HALF+7..9), y = heightAt+2.6. Store Vector3 + name. Exclude cams too close to each other.

At cut time: candidates within dist 15..120 of leader, pick random. If none (leader far from all? impossible with 16 cams) fallback chase.

**Cut timing**: after GO: first at +5s, then each return +rand(6,9). During side: 3s (+fov set). Also cut on FINISH: one side cam of leader crossing? keep chase.

**Loop recording note**: everything important (countdown, racing, drifts, overtakes, HUD) happens continuously; first 30s covers countdown + ~2 laps + 2-3 cam cuts ✓.

Potential worry: leader lap2 completion at ~4+12.5+12.5=29s ✓ shows "LAP 3/3" before 30s. 

Lap length ~540*0.9=486 wait I scaled 0.9 → raw perimeter 539 → L≈539*0.9≈485 minus Catmull rounding ≈ maybe 470. avg speed: maxSpeed 48-54, corners drop to ~26-30 for maybe 25% of lap, sweepers 45+: avg ≈ 41 → lap ≈ 11.5s ✓.

Set maxSpeed values: [54, 52.5, 51.5, 50.5, 49.5, 48.5] assigned randomly to roster? Assign per config directly with names so personalities stable: PEPPER 54 aggressive, MINTY 52.8, BUMBLE 51.8, BERRY 50.8, GRAPE 49.8, POWDER 49. Grid order: fastest at back for overtakes: grid slot 0 (pole) = POWDER ... slot 5 = PEPPER. ✓ drama early.

aLat: 36-44 random each race? Keep fixed per kart: [42,40.5,39.5,38.5,37.5,36.5] shuffled-ish.

Rubber band mild keeps pack close → constant position swaps ✓.

**Numbers on leaderboard update frequency**: every 0.25s.

**Minimap**: transform: find bbox of P; scale to fit 150-20; map(x,z) → (mx,my): note canvas y = z? Orientation whatever: mx = (x - cx)*sc + 75; my = (z - cz)*sc + 75 ✓ (mirror irrelevant).

Draw each frame: bg transparent (panel css behind), path once cached as Path2D in map coords ✓, then dots. Start line: small perpendicular tick at P[0] using Sd[0].

Kart dot: use proj of pos (mx from x,z) ✓ color = css color; leader white ring.

Canvas 150×150 with panel bg via CSS.

**Fonts**: numbers italic bold. Use `font-style:italic; font-weight:900` with Trebuchet fallback — Trebuchet has bold italic ✓ decent. Add letter-spacing on labels.

Now, code writing time. I'll write it in one pass, carefully.

Also remember: no alert/confirm ✓; no lorem ✓; everything wired ✓.

Edge: `wrapPI` needed for err.

Let me write the JS in order:

1. Setup renderer/scene/camera/lights/sky/fog.
2. Texture helpers + textures.
3. Track sampling arrays.
4. Geometry builders (road, kerbs, skirt, start line, ground disc, sky dome).
5. Props (gantry, arch, boards, stand, trees, tires, flags, clouds, balloons, mountains).
6. Particles system.
7. Skid system.
8. Kart class + roster + spawn.
9. Cameras + trackside cams.
10. HUD refs + minimap.
11. Race state machine + loop.

Careful details:

- `curve.getSpacedPoints(N)` returns N+1 points where point[N] == point[0] (closed). Use slice(0,N).
- Tangents: central difference.
- Curvature: k[i] = wrap(yaw[i+1]-yaw[i-1])/(2*ds); smooth twice ±5.

Skirt builder both sides:

```js
const SK_OFF=[8.4,12,18,28,45,70,115];
const SK_W  =[1,0.86,0.6,0.38,0.18,0.06,0];
function skirtW(a){ for(let j=1;j<SK_OFF.length;j++){ if(a<=SK_OFF[j]){ const t=(a-SK_OFF[j-1])/(SK_OFF[j]-SK_OFF[j-1]); return SK_W[j-1]+(SK_W[j]-SK_W[j-1])*t; } } return 0; }
```

a < 8.4 handled earlier (w=1).

Skirt mesh per side: rows i 0..N (seam dup), cols 7 offsets: y = P.y*w + GROUND*(1-w) where GROUND = -0.55 + groundN(world x,z of that vertex) — note noise uses actual world pos ✓ matches heightAt? heightAt uses noise at (P + Sd*lat) ✓ same.

Wait heightAt for kart grass: y = P[i].y*w + (-0.5 + groundN(x,z))*(1-w) ✓ same formula. 

Indices: for i<N, for j<6: quad (i,j),(i,j+1),(i+1,j)... two triangles.

uv: u = off/7 (tiles), v = i*ds/7. Grass tile 7 ✓ (tile = L/round(L/7) for seam continuity — pass computed tile).

computeVertexNormals ✓.

Far ground: CircleGeometry(900, 48).rotateX(-π/2) at y=-1.5, grass darker color 0x6f9c4e with same texture repeat 80? Use plain color material with slight texture: reuse grass tex repeat 60 ✓.

Also outer skirt edge at 115 y ≈ ground(-0.5+noise up to +3.4, min -3.85) → could dip below ground plane at -1.5 → holes? Outer skirt w=0 → y = -0.55+noise ∈ [-4.3, +3.3]. Ground plane at -1.5 cuts through → visible seam where skirt dips below. Fix: clamp noise positive-ish: noise = 1.0 + (sin..)*? make GROUND y = -0.55 + (noise*0.5+0.9) → range: noise∈[-4,4]*0.5 → [-2,2]+0.9-0.55 → [-1.65, 2.35] hmm still dips below -1.5 slightly. Use ground disc at y=-2.2 and hills mostly above: range [-1.65,2.35] vs -2.2 ✓ no dip. And skirt edge at ~-1.65..2.35 vs disc -2.2: gap of up to 4.5 at high edges → visible skirt "cliff" edge from above? From chase cam mostly看不到 far edge; mountains ring at r 650 hides horizon. Also fog. Accept: set disc y=-2.3, radius 1200 (beyond fog far 950 → fully fogged horizon ✓).

Mountains at r 620-780, heights 60-150, cone radius 80-180, fog-blended ✓ positioned all around (angle random 14 of them), y = -2.3 base.

Sky dome: SphereGeometry(1500, 16, 8)?? beyond camera far — set camera far 3000 ✓. Gradient canvas 256×256 vertical: top #5aa7e0 → mid #a8cfe8 → horizon #eef3ee warmish. Map with mapping: use MeshBasicMaterial map, side BackSide, fog:false, depthWrite false? Dome at radius 1500 centered origin: fine.

Sun position also add a bright disc sprite in sky? skip.

Clouds: Lambert white, slightly emissive 0x?? Lambert color 0xffffff, fog applies — clouds at ~350 dist moderately fogged ok. flat-scaled spheres cluster.

Flag wave: store flags list, anim rotation.z = sin(t*3+i)*0.15 + tilt base.

Balloon: sphere r5 scale y1.15 color bright + basket; float y sin.

**Arch banner mid**: "SLIPSTREAM SECTOR".

**Tire stacks**: find segments: scan i: |kS[i]|>0.045; group contiguous (wrap aware). For each group longer than 12 samples: outerSign = -Math.sign(kS[mid]) (outside of turn); place tires at s step 2.4: lat = outerSign*(HALF+2.4); pos = P + Sd*lat; y = heightAt? at that lat ~ w≈1 (8.4 < HALF+2.4=9.4 → just past kerb: w(9.4)= between 8.4(1) and 12(0.86): t=(9.4-8.4)/3.6=0.28 → w=0.96 → y ≈ trackY*0.96 + ground*0.04 ✓ use heightAt(idx, lat). Stack second at y+0.55 with slight offset. Cap total 140 instances (2 instanced meshes: dark & accent colors: create two InstancedMeshes with counts; simpler: single InstancedMesh with setColorAt: color mostly #232427, some #d4452f / #e8e6df).

Torus rotated: TorusGeometry(0.5, 0.26, 8, 14) rotateX(π/2) → lies flat (donut around y). ✓

**Trees**: InstancedMesh ×3 (trunk, cone, ball). counts: pines 90, oaks 60. Trunk shared geometry both types (scale varies). Compose matrix with scale & rot. Leaf colors setColorAt: greens varied (pine 0x2f7a3d base varied ±, oak 0x4d9b4a...). Also autumn few 0xc47a2e? tasteful mix.

Tree placement avoid |lat|<10.5, avoid near track overlap: also avoid placing INSIDE loop where karts... inside is fine (infield decoration). But avoid the infield of tight corners where cutting lines... AI stays on road; trees at |lat|≥10.5 always ≥ 3.5 off kerb edge ✓ (kerb ends 8.4).

Also avoid duplicates too close to each other? random fine.

Grandstand occupies specific area: skip trees within box near start outside: if (s within [L-70, L+20] && outsideSide) skip. Compute s per tree idx.

**Billboards**: 8, idx spread i*N/8 + N/16, side alternate; lat = ±(HALF+5.5); lookAt(P[idx] at same y). Texts: ["NITRO-COLA","APEX TYRES","VELOCE FUEL","KOYO BRAKES","SLIPSTREAM","PIT STOP CAFÉ","TURBO+","GRIP-X"] with varied bg (accent red, cream, teal, charcoal...). 

**Crowd canvas**: dark #1a1d22 bg, dots random pastel colors, 2 rows blocks... fine.

**HUD building**: rows created dynamically:

```js
const rowsEl=document.getElementById('rows');
const rowEls=ROSTER.map((r,i)=>{ create div... });
```

Update: standings order → for each rowEl: set style.order=i; rank text i+1; name; gap.

Wait each row corresponds to a kart (fixed chip color/name) and moves via order ✓.

Gap: leader: '—' else '+x.xs'. Also append lap badge when finished: 'FIN'.

**Race timer format**: `m:ss.d`.

**Cam tag**: text.

Now the countdown overlay logic with lights:

```js
function setLights(n){ for j in 0..2: lights[j].material.color.set(j< n? 0xff2d1e : 0x35100c) }
```

MeshBasicMaterial per sphere.

At GO: set all to 0x2aff5a? green flash 1s then dark: schedule via raceT<1.

**State machine in tick(t)**:

```
if(state==='cd'){
  cdT -= dt; stage changes → big.textContent + pop; lights.
  karts: visual rev only.
  camMode='grid'.
  if(cdT<=0.9 && !goShown){ 'GO!' green; goTime=t; state='race'; raceT=0; lights green; }
```

Hmm release karts AT 'GO' display: when cdT<=0.9 show GO and set state 'race' (karts start accelerating) ✓ countdown numbers at cdT 3.6/2.7/1.8/0.9 boundaries as computed from 4.5 start.

Timeline: cdT init 4.5. stage = cdT>3.6?0 : >2.7?1 : >1.8?2 : >0.9?3 : 4(GO). stage transitions trigger pops & beeps (stage 1,2,3 → 660Hz short; GO → 990Hz long). Lights lit = min(stage,3) with stage≥1... light count = stage (1→1 light, 2→2, 3→3, GO→green).

Intro stage shows "CRESTLINE GP" small class.

'race': raceT += dt; physics; cams logic; laps; finish detection (leader.finished → state='post', postT=0, show FINISH + winner, confetti burst at gantry? at leader pos).
'post': karts continue physics (finished ones keep lapping), postT+=dt; if postT>5 → resetRace() → state='cd', cdT=4.5, camera grid, clear big, reset skids/particles, reset lights.

**Confetti**: spawnConfetti(pos): 80 particles colors palette, vel random up 5-9, g strong, life 1.4, size 0.35 — via particle system with gravity support ✓.

Particle update needs per-particle gravity: arrays g[].

**Exhaust puffs**: during cd & race slight: spawn gray small at rear center every 0.15s while speed<5? Just during cd.

Now — write kart visuals builder:

```js
function buildKartMesh(cfg){
 const g=new THREE.Group(); // root
 const body=new THREE.Group(); g.add(body);
 const M=(c)=>new THREE.MeshLambertMaterial({color:c});
 const c=cfg.c, trim=cfg.trim;
 // floor
 pan = box(1.55,0.16,2.5) at y0.28 color 0x24262b
 // cowl front
 nose = box(1.15,0.42,0.95) at (0,0.55,0.85) color c
 noseTip = box(0.7,0.3,0.4) at (0,0.5,1.45)? maybe wedge: use box scaled; fine
 sidepods L/R box(0.34,0.42,1.1) at (±0.72,0.5,0.15) color c
 engine box(0.7,0.5,0.6) at (0,0.62,-0.75) color 0x303338
 exhaust ×2 cylinder r0.07 len0.5 rotX 90° at (±0.2,0.95,-1.0) color 0x8b8f96
 spoiler rear: box(1.3,0.08,0.35) at (0,1.05,-1.15) color trim + 2 struts
 seatback box(0.7,0.55,0.18) at (0,0.85,-0.42) color trim
 bumper front box(1.5,0.14,0.18) at (0,0.35,1.55) color trim; rear similar at -1.35
 // driver
 torso box(0.56,0.5,0.4) at (0,1.05,-0.25) color 0x2a2d33 (suit) — add accent stripe small box on chest color c
 helmet sphere(0.30) at (0,1.52,-0.22) color c... helmet = kart color, visor: box(0.34,0.12,0.1) at (0,1.52,0.06) color 0x14161a — relative helmet center: helmet at z -0.22, visor at z +0.05 (front).
 arms: box(0.1,0.1,0.5) rot to wheel: place two from shoulders (±0.26,1.28,-0.1) angled forward-down; approximate rotation.x = -1.1... eh set rotation set from positions: keep simple: arm boxes rotated x -0.9, positioned (±0.22, 1.25, 0.02).
 hands skip.
 steering wheel: torus(0.17,0.035) at (0,1.18,0.28) rotX ~ -1.1 (facing driver) color 0x1b1d20 + column small.
 head group: put helmet+visor in headG for rotation.
 // wheels
 wheelGeo: cylinder(0.32,0.32,0.26,10).rotateZ(π/2) dark 0x17181b; hub cylinder(0.15,0.15,0.27,8).rotateZ(π/2) color 0xb9bfc6? merged: just add hub as second mesh child of wheel mesh? For spin we rotate a wheelGroup containing tire+hub → each wheel = Group with tire mesh + hub mesh; front wheels inside steerGroup.
 positions: front z 0.82 x ±0.78 y 0.32; rear r0.36 w0.3 z -0.78 y 0.36, x ±0.85.
 rear wheels also steer? no.
 shadow: circle(1.5) rotX -π/2 at y 0.02 opacity 0.3 color 0x000000, renderOrder 89.
 return {root:g, body, headG, wheels:[fl,fr,rl,rr] (spin groups), steerL, steerR, steerWheel}
}
```

Front wheels: steerL group at position, rotation.y=steer; child spin group rotation.x spins. Rear: spin only.

Scale: kart total ~1.6 wide, 2.5 long — road 14 wide fits 7 karts wide ✓.

Speed feel: 50 u/s with kart length 2.5 → 20 lengths/s — camera 7 behind: fine.

**Kart colors config**:

```js
ROSTER=[
 {name:'POWDER', c:0xe9eef2, trim:0x9aa4ad, speed:48.6, aLat:36.5},
 {name:'GRAPE',  c:0x8a4fc9, trim:0x5c2f8a, speed:49.7, aLat:37.6},
 {name:'BERRY',  c:0x3a66c9? , ...}
```

Berry cobalt 0x365ac2. BUMBLE 0xf2b32a trim 0x8a5f10. MINTY 0x2fae7e trim 0x1c6b4c. PEPPER 0xe0432c trim 0x8e2416.

Grid order = array index (0 pole ... 5 last) with PEPPER last (fastest) ✓.

**Camera up/lookAt**: use cam.lookAt(look) with cam.up default.

**Grid cam sweep**: center = P[(N-14+N)%N]... karts at rows behind line: s = L-8-row*5.5 → i ≈ N - 8/ds... ds≈0.79 (485/616? N=700, ds≈0.68). i ≈ N-12-8*row. center = avg pos of karts. cam: ang from -2.4 → -1.4 as cdT 4.5→0.9; radius 15→12; height center+4.5→3.2; look center+ (0,1.2,0). Also slight side. Fine.

**Chase initial snap at GO**: compute desired & set camPos directly.

**Trackside list**:

```
TSCAMS=[]; for(k=0;k<16;k++){ i=k*N/16; side=(k%2?1:-1); lat=side*(HALF+8); pos=P[i]+Sd[i]*lat; pos.y=heightAt(i,lat)+2.6; TSCAMS.push(pos) }
```

Cut pick: dist to leader 15..140, pick 3 nearest, random.

**Side cam hold**: store sideUntil, sidePos. fov: dist-based.

**Chase while leader finished**: keep leader = standings[0] (finished karts ordered by finish time; leader remains the winner ✓).

Hmm during 'post', winner keeps driving; camera follows ✓ nice victory lap.

**Confetti colors**: use roster colors + white.

Now write ALL the code. Also double-check the road ribbon winding for kerbs similarly (same pattern as road → +y normals ✓). Skirt: columns left-to-right? Build same pattern: for j offset increasing outward: triangle (i,j),(i+1,j),(i,j+1)? Let me just reuse ribbon-style: vertices ordered [off0, off1] pairs per row like road with two columns → but skirt has 7 columns. Write generic grid builder:

```js
function gridGeo(cols, rowFn, tileU, tileV, seam){ 
 // rowFn(i, j) -> Vector3
 positions rows 0..N (N+1 rows incl seam), cols count
 uv u = uCoords[j], v = i*ds/tileV
 indices: for i<N, j<c-1: a=i*c+j: tri a, a+c, a+1 ; a+1, a+c, a+c+1
}
```

Check winding for upward normals with left-to-right columns in +Sd order (left→right): vertex(i,j) at lat = offs[j] (offs descending from +8.4? For left side: offs = [+115 ... +8.4] or ascending? Let me define offs array ascending j: [8.4, 12, 18, ...115] (going right for the RIGHT side using negative? For left skirt: lat = +offs[j] (j→ outer). For right side: lat = -offs[j].

Winding: For left-side skirt, j increasing = further LEFT. Row i forward. Take near start: Sd=(0,0,-1) (left = -z): vertex (i, j0=off 8.4) at z = 74*0.9-8.4 → z0; (i, j1=off 12) z smaller (more left). forward row i+1: x+ds. Triangle (a=(i,j0), b=(i+1,j0), c=(i,j1)): vectors b-a=(ds,0,0)... in world: a=(0, y, Z-8.4), b=(0.68, y, Z-8.4), c=(0, y, Z-12). cross(b-a, c-a) = cross((0.68,0,0), (0,0,-3.6)) = (0*(-3.6)-0*0, 0*0-0.68*(-3.6), 0) = (0, 2.45, 0) +y ✓ good with tri (a, b, c) i.e. (i,j),(i+1,j),(i,j+1). Then second tri (b, c2=(i+1,j+1), c): (b, c, c2): cross(c-b, c2-b) = cross((-0.68,0,-3.6), (0,0,-3.6)) = (0*(-3.6) - (-3.6)*0, (-3.6)*0 - (-0.68)(-3.6), ...) = (0, -2.45, ...) DOWN ✗. Order (b, c2, c): cross(c2-b, c-b) = cross((0,0,0)?? c2-b = (0.68-0.68, 0, -3.6)= (0,0,-3.6); c-b = (-0.68,0,-3.6). cross((0,0,-3.6), (-0.68,0,-3.6)) = (0*(-3.6) - (-3.6)*0, (-3.6)*(-0.68) - 0*(-3.6), 0*0-0*(-0.68)) = (0, 2.45, 0) ✓ up. So indices per quad: (a, a+c, a+1) and (a+1, a+c, a+c+1). 

For the two-column ribbons (road/kerb) same as earlier verified: (a, a+1, a+2) with a=left_i... earlier road: vertex order per row: [offA=+7 (left), offB=-7] → cols left→right too: a=i*2+0 (left), a+1 (right): tri (a, a+1, a+2)= (L_i, R_i, L_{i+1}) verified up ✓. Match pattern (i,j),(i+1,j),(i,j+1) with j0=left(+7), j1=right(-7): tri(a=(i,L), b=(i+1,L), c=(i,R)) — earlier I verified (A, B, A') = (L_i, R_i, L_{i+1}) hmm inconsistent ordering but both windings? Earlier: triangle (A(L_i), B(R_i), A'(L_{i+1})): cross(B-A, A'-A): B-A = (0,0,-14)?? wait left=+7 → A at z = Z-7? Sd left = -z direction: A = P + Sd*7 → z smaller. B = P - Sd*7 → z = Z+7. B-A = (0,0,14). A'-A = (ds,0,0). cross((0,0,14),(0.68,0,0)) = (0*0-14*0, 14*0.68-0*0, 0-0) = (0, 9.5, 0) ✓ up. Good — road tri order (L_i, R_i, L_i+1) up; my grid pattern (i,j0=L... wait grid pattern tri (i,j0),(i+1,j0),(i,j1) = (L_i, L_{i+1}, R_i): cross(L_{i+1}-L_i, R_i-L_i) = cross((0.68,0,0), (0,0,14)) = (0*14-0*0, 0*0-0.68*14, 0) = (0,-9.5,0) DOWN. So for road use order (a, a+1, a+c) etc. To avoid sign bugs, simplest: use DoubleSide on all ground materials (road, kerb, grass) — lighting: DoubleSide with Lambert: normals still computed; backface lit incorrectly? Lambert double side flips normals for backfaces in three.js (it handles two-sided lighting). Yes MeshLambertMaterial DoubleSide lights correctly both sides. So DoubleSide everywhere ground → no winding worry. ✓ Do that. (Slight cost negligible.)

Still computeVertexNormals gives consistent normals mostly up; fine.

**Start line orientation**: rows from idx0=0 to idx1: build 2-row grid with own geometry (like ribbon between i=0 and i=ir) width across FULL road: verts L0,R0,L1,R1 with checker tex uv (0,0),(1,0),(0,1),(1,1) — orientation: u across ✓.

Checker canvas: 10 cols × 2 rows squares: canvas 200×40, sq 20.

**Banner texture**: canvas 512×96 dark #1b1e24, text "CRESTLINE GP" paper + accent diagonal stripes at ends.

**Crowd**: 256×96.

Now particle spawn while drifting: rate: spawnAcc += dt*rate; while>1 spawn. rate 70 per wheel? total 140/s per kart ×4 drifting karts = 560/s, life 0.8 → ~450 alive of 500 pool... tight. Reduce: 45/s per wheel → 90/s/kart, alive ≈ 90*0.8=72/kart, 3 drifting ≈ 270 + grass dust ✓. MAXP=600.

Skid spawn: 2 wheels × every 0.03s = 66/s per drifting kart; pool 900, life forever (until overwritten ring). Circumference coverage: total drift-time... ring overwrites oldest fine. 900 instances one draw call OK.

**Performance of nearest search & probes** trivial.

**Memory/GC**: avoid per-frame allocations: reuse temp vectors.

Now, HUD text updates: use textContent only when changed (cache strings) — minor, fine every 0.25s.

**Let me also double check lap counting edge**: karts start s≈L-8 (lap -1). Crossing line: sPrev ~ L-2 > 0.75L ✓ s ~ 1 < 0.25L ✓ lap→0 ✓ display max(lap+1,1)=1 ✓. During race lap 0→1 at next crossing etc. Finish when lap==LAPS (3): after 4 crossings total (start-cross + 3 laps)? Wait: crossing #1: -1→0 (start of lap 1). #2: 0→1 (start lap 2). #3: 1→2 (lap 3). #4: 2→3 → lap==LAPS=3 → finished. So kart crosses finish line 4 times total: once at start + 3 racing laps = 3 laps completed ✓ display: lap 0→"LAP 1", 1→"2", 2→"3", 3→FIN ✓.

prog = lap*L+s: initial: -L + (L-8) = -8 ✓ increases through 0 at start line, etc. Finished kart prog keeps growing (keeps driving) but ranking uses finished key ✓.

**Leader determination for rubber band**: leaderProg = max prog among unfinished? Use standings[0].prog (works overall).

**Wrap angle in steering when target behind**? err clamp ±1 after gain → smooth.

**Spin-out risk** none.

**What if kart slides off road during drift**: grass cap 0.42×maxSpeed → slows, dust, recovers ✓. Also lateral position beyond 12: hard steer lane 0. Add: if |lat|>HALF+3 → laneTgt=0, lookahead 4.

**Karts jumping hills**: y set directly from track → smooth since curve smooth.

Pitch: rotation.x = -asin(T.y) plus small bob. Since root.rotation.order='YXZ', setting rotation.x & y ok.

Roll on banking none.

**Check side vector with hills**: Sd computed from XZ-projected tangent? T from 3D positions includes y; Sd = (T.z, 0, -T.x) normalized (XZ) ✓ do that (ignore y).

**yawArr** from atan2(T.x, T.z) ✓.

**getWorldPosition for wheels** each frame for skid/dust: use rear wheel groups' matrixWorld: temp vec. root.updateMatrixWorld needed before? We set transforms then call scene.updateMatrixWorld once in render; but we need wheel world pos during update — compute manually: rear wheel world pos = root.position + rotate offset by yaw: offsets known constants (±0.85, -0.78) → compute via sin/cos — cheap & no matrix deps ✓.

rear wheel world offset: local (±0.85, 0, -0.78): world x = pos.x + (lx*cos(yaw) + lz*sin(yaw))? Rotation yaw about Y: world = (lx*cosY + lz*sinY, ly, -lx*sinY + lz*cosY)? For three.js rotation.y=θ: x' = lx*cosθ + lz*sinθ; z' = -lx*sinθ + lz*cosθ ✓ (right-handed Y rotation: x' = x cosθ + z sinθ, z' = −x sinθ + z cosθ). ✓

Skid y = pos.y + 0.03.

**Dust color on kerb/road**: tan; grass: green-brown mix.

**Confetti spawn**: at leader pos + up 2, 70 particles, vel random sphere*3 + up*7, g=-9, drag, life 1.6, size 0.32, colors palette.

Particle update with per-particle g: vel.y += g*dt; dust g=+0.5 (rise) then... dust rise looks odd long; use g=-0.15 slight settle for dust, drag high. Confetti g=-9. Store gArr.

Alpha fade: a = (life/maxLife); dust alpha curve a*0.5; store baseAlpha per particle.

Size grow: size = s0*(1+2*(1-a)).

gl_PointSize clamp: gl_PointSize = clamp(..., 1.0, 64.0).

Fog on particles? ShaderMaterial no fog — distant dust pops bright — acceptable (dust mostly near cam subject).

**Skid color**: 0x101114 opacity 0.4.

**Rendering order/transparency**: road opaque; kerb opaque; skid transparent renderOrder 5; shadow renderOrder 6; particles 7; depthWrite false each.

Shadow (blob) under kart might z-fight with skid marks — both transparent no depthWrite, order: skid 5, blob 6 (blob on top of skid ok) & particles 7. ✓

**Board updates**: also show tiny drift indicator? no.

**Extra polish — engine sound**: skip.

**HTML skeleton** and CSS finalize:

Panels: I want slightly angled, chunky racing telemetry look:

```css
.panel{background:rgba(15,17,21,.85); border:1px solid rgba(255,255,255,.08); box-shadow:0 2px 0 rgba(0,0,0,.35); border-radius:8px}
#board{top:16px;left:16px;padding:8px 10px;min-width:210px}
#board h4{font-size:10px;letter-spacing:.22em;color:#9aa2ad;margin:2px 2px 6px}
.row{display:flex;align-items:center;gap:7px;padding:3px 8px;border-radius:5px;transform:skewX(-8deg);margin:2px 0;font-weight:700;font-style:italic}
.row .rk{width:18px;font-size:15px;color:#8b939e}
.row .chip{width:9px;height:9px;border-radius:2px;flex:none}
.row .nm{flex:1;font-size:13px;letter-spacing:.04em}
.row .gp{font-size:11px;color:#9aa2ad;font-variant-numeric:tabular-nums}
.row.ld{background:rgba(255,77,28,.16);outline:1px solid rgba(255,77,28,.5)}
.row.ld .rk{color:#ff6a3d}
```

Skew whole row incl text — italic anyway ✓.

Lapbox:

```css
#lapbox{position:absolute;top:16px;right:16px;text-align:right;padding:8px 14px}
#lap{font-size:24px;font-weight:900;font-style:italic;letter-spacing:.03em}
#clock{font-size:13px;color:#9aa2ad;font-variant-numeric:tabular-nums;margin-top:2px}
```

Map bottom-left; camtag bottom-right small.

Big:

```css
#big{position:absolute;left:50%;top:38%;transform:translate(-50%,-50%);font-size:min(17vw,150px);font-weight:900;font-style:italic;color:#f4f1e8;text-shadow:0.06em 0.09em 0 #15171b;letter-spacing:.02em;display:none}
#big.on{display:block}
#big.go{color:#8bd450}
#big.fin{color:#ff4d1c;font-size:min(11vw,90px)}
#big.small{font-size:min(6vw,44px)}
@keyframes pop{0%{transform:translate(-50%,-50%) scale(2.1);opacity:0}18%{opacity:1}100%{transform:translate(-50%,-50%) scale(1);opacity:1}}
#big.pop{animation:pop .45s cubic-bezier(.2,.9,.3,1.2) both}
```

Retrigger: remove class, force reflow, add.

Sub caption bottom-center: "SELF-DRIVING GRAND PRIX • 3 LAPS" tiny? Add #sub under big during intro? Put a static small line bottom center: "CRESTLINE GP · AI GRAND PRIX · 3 LAPS". OK.

Wait — also need to be careful: `#big` transform conflicts (translate + scale) handled in keyframes ✓.

Now the big code write. I'll aim for clarity + compactness. Let me write final HTML now, mentally checking each subsystem as I go.

Additional check — import map only includes "three" and "three/addons/". We only import three ✓.

Potential runtime pitfalls to avoid:

- `THREE.CanvasTexture` needs `wrapS/wrapT = RepeatWrapping` where uv>1 ✓ set.
- `renderer.setAnimationFrame` loop via setAnimationLoop.
- `getSpacedPoints` returns Vector3s ✓.
- Curvature sign & smoothing arrays Float32.
- InstancedMesh needs `instanceMatrix.setUsage(THREE.DynamicDrawUsage)` for skids.
- Points frustumCulled = false (positions change) — set frustumCulled=false on points & skid mesh & karts maybe fine default (karts have bounds).
- kart root frustumCulled default per-mesh fine.

Let me now decide leaderboard gap: time gap est = (progLead - prog)/clamp(speed,8,999). Fine.

Also add speed lines? no.

Countdown lights: build into gantry: three spheres r0.26 spaced 0.75 on crossbar underside front. Materials MeshBasicMaterial (unlit reads as lit). dark: 0x2a0f0c; on: 0xff3524; go: 0x39e75a.

Let me now also decide ds: N=700; L≈? compute at runtime; ds = L/N.

Lookahead rounding uses ds.

Lane gain: kS values: typical corner k 0.03-0.06; want lane ±(HALF-1.9)=±5.1 at k≈0.04 → gain 120? 0.04*120=4.8 ✓. Use gain 110. Small k 0.01 → 1.1 subtle ✓.

Wait sign: apex side = +Sd*sign(k)? k>0 left turn → apex left = +lane ✓ lane = clamp(k*110, -1,1)*5.1 → target position P + Sd*lane ✓.

Steering err gain 2.4.

Brake probes include curvature max between idx and probe point: iterate step 3 samples.

Drift extra yaw: +drift*0.75*dt*speedFactor.

Now think about whether karts might collide at start (grid 2.3 lateral, rows 5.5 apart): rows separated along track 5.5 > kart length 2.5 ✓ no overlap. Column gap 4.6 ✓.

At GO accel differences → immediate small overtakes into T1 (braking zone) — great.

**Post state camera**: continue chase winner.

**Multiple finishes**: other karts finish too — mark finished (lap>=LAPS) but keep driving; their rows show 'FIN' gap? Row gap for finished: show 'FIN'. Sorting finished by finT then others by prog ✓.

Let me also add slight variation in racing line per lap via laneBias wander: lane += Math.sin(t*0.23+phase)*0.6 ✓ organic.

Okay — also the "title" moment: maybe add a big first-frame overlay "CRESTLINE GP" during intro stage of countdown ✓ (stage 0 shows track name). 

**Write the code.**

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Crestline GP — self-driving kart race</title>
<style> ... </style>
</head>
<body>
<div id="ui">
  <div id="board" class="panel"><h4>RUNNING ORDER</h4><div id="rows"></div></div>
  <div id="lapbox" class="panel"><div id="lap">LAP 1/3</div><div id="clock">0:00.0</div></div>
  <div id="mapbox" class="panel"><canvas id="map" width="168" height="168"></canvas></div>
  <div id="camtag" class="panel">GRID CAM</div>
  <div id="sub">CRESTLINE GP · SIX AI DRIVERS · THREE LAPS · NO DRIVERS REQUIRED</div>
  <div id="big" class="on"></div>
</div>
<script type="module">
import * as THREE from 'three';
... everything
</script>
</body>
</html>
```

Map panel with padding; canvas inside.

Now the module script. Let me write it fully and carefully. (I'll count on careful mental execution.)

```js
/* ---------- basics ---------- */
const W=()=>innerWidth,H=()=>innerHeight;
const renderer=new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.setSize(W(),H());
renderer.toneMapping=THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure=1.08;
document.body.appendChild(renderer.domElement);
const scene=new THREE.Scene();
scene.fog=new THREE.Fog(0xdfeef2,240,980);
const cam=new THREE.PerspectiveCamera(58,W()/H(),0.1,4000);
addEventListener('resize',()=>{cam.aspect=W()/H();cam.updateProjectionMatrix();renderer.setSize(W(),H())});
```

Lights:

```js
scene.add(new THREE.HemisphereLight(0xcfe6ff,0x87a560,0.95));
const sun=new THREE.DirectionalLight(0xfff0d8,2.6); sun.position.set(160,220,90); scene.add(sun);
```

Sky dome:

```js
const skyTex=makeTex(256,256,(g,w,h)=>{const gr=g.createLinearGradient(0,0,0,h);gr.addColorStop(0,'#4d9bd6');gr.addColorStop(0.55,'#a9d2ea');gr.addColorStop(0.8,'#e8f1ea');gr.addColorStop(1,'#e8f1ea');g.fillStyle=gr;g.fillRect(0,0,w,h);});
const sky=new THREE.Mesh(new THREE.SphereGeometry(1600,20,10),new THREE.MeshBasicMaterial({map:skyTex,side:THREE.BackSide,fog:false,depthWrite:false}));
scene.add(sky);
```

Sky sphere with gradient mapped: sphere UV v from top→bottom ✓.

Helpers:

```js
function makeTex(w,h,fn,repeat){const c=document.createElement('canvas');c.width=w;c.height=h;const g=c.getContext('2d');fn(g,w,h);const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;if(repeat){t.wrapS=t.wrapT=THREE.RepeatWrapping;}t.anisotropy=8;return t;}
```

Track:

```js
const RAW=[[0,0,74],[58,0,76],[96,2,58],[104,4,22],[88,7,-10],[60,9,-20],[28,8,-10],[8,9,-34],[-24,8,-52],[-58,6,-52],[-84,4,-26],[-78,2,8],[-92,1,40],[-58,0,70]];
const SC=0.9;
const cps=RAW.map(p=>new THREE.Vector3(p[0]*SC,p[1]*1.2,p[2]*SC));
const curve=new THREE.CatmullRomCurve3(cps,true,'centripetal');
const N=700, L=curve.getLength(), ds=L/N;
const pts=curve.getSpacedPoints(N);
const P=pts.slice(0,N);
const T=[],SD=[],YAW=new Float32Array(N),K=new Float32Array(N),KS=new Float32Array(N);
for(let i=0;i<N;i++){const a=P[i],b=P[(i+1)%N],c=P[(i-1+N)%N];const t=new THREE.Vector3().subVectors(b,c).normalize();T.push(t);YAW[i]=Math.atan2(t.x,t.z);SD.push(new THREE.Vector3(t.z,0,-t.x).normalize());}
for(let i=0;i<N;i++){K[i]=wrapPI(YAW[(i+1)%N]-YAW[(i-1+N)%N])/(2*ds);}
// smooth twice
smooth(K,KS,6); // write into KS
function smoothInto(src,dst,w){...}
```

Implement smoothing: 

```js
function smoothArr(src,dst,w){for(let i=0;i<N;i++){let s=0;for(let o=-w;o<=w;o++)s+=src[(i+o+N)%N];dst[i]=s/(2*w+1);}}
smoothArr(K,KSm1,6); smoothArr(KSm1,KS,6);
```

Keep both arrays.

Track surface helpers:

```js
const HALF=7;
const SK_OFF=[8.4,12,18,28,45,70,115], SK_W=[1,.85,.6,.38,.18,.06,0];
function skirtW(a){if(a<=SK_OFF[0])return 1;for(let j=1;j<SK_OFF.length;j++){if(a<=SK_OFF[j]){const t=(a-SK_OFF[j-1])/(SK_OFF[j]-SK_OFF[j-1]);return SK_W[j-1]+(SK_W[j]-SK_W[j-1])*t;}}return 0;}
function gNoise(x,z){return Math.sin(x*.043)*1.1+Math.cos(z*.037+1.7)*1.0+Math.sin((x+z)*.019)*1.6;}
function groundY(x,z){return -0.6+gNoise(x,z)*0.75;}
function heightAt(i,lat){const a=Math.abs(lat);const p=P[i],sd=SD[i];if(a<=8.4)return p.y;const w=skirtW(a);const x=p.x+sd.x*lat,z=p.z+sd.z*lat;return p.y*w+groundY(x,z)*(1-w);}
```

groundY range: gNoise∈[-3.7,3.7]*0.75 → ±2.8 → y ∈ [-3.4, 2.2] vs far disc at -2.4... dips to -3.4 below disc → holes at outer ring (r>70 from track, map interior mostly). Interior area within loop: skirt inner offsets near track both sides cover band 8.4-115 both sides — interior of loop (center region) not covered by skirts! The loop interior (big area inside circuit) has no ground except far disc at -2.4 while track at y 0-10 → visible cliff at inner skirt outer edge (offset 115 from inner side may overshoot across the middle). Hmm: inner offsets extend up to 115 units inward; loop is ~250 wide → inner skirts from both sides overlap in middle (115*2=230 < width ~230? borderline) — overlapping skirts z-fight where both cover!

Fix: make skirt asymmetric widths: extend OUTER side far (to 160) and INNER side shorter (to ~55) — but inner region center may still be uncovered: loop spans x -105..125, z -70..90 in scaled coords... interior distances from track centerline to the "middle" of the infield: e.g., point (0,10): distance to nearest track point? Track passes near (28,-9)... nearest ~ (28,-9)→(0,10) dist ≈ 33; also straight z 66: dist 56. So infield max distance to track ~35-45. Inner skirt width 55 covers ✓. Outer side: distance to map edge beyond outer: extend 160.

But overlapping: inner skirt of one segment vs outer of another across the pinch? The S pinch: two legs 40 apart → inner skirt 55 wide from each crosses the other leg → overlap & z-fight & wrong height (height uses own base P → mismatched heights cause spikes!). Danger zones: anywhere track approaches itself < 2*offset.

Pinch points: S-chicane region: P6(28,-10) to P8(-24,-52): distance between track segments: segment P6→P7 (28,-10)→(8,-34) and segment P8→P9 (-24,-52)→(-58,-52): closest ~ (8,-34) to (-24,-52): √(32²+18²)=36.7 → skirts 55 wide overlap ✗. Also P11(-78,8) to P13(-58,70) vs P10-P11 region and start straight? (-78,8)→(-58,70)? segment P12→P13 (-92,40)→(-58,70): vs straight P13→P0: meet at P13. Non-adjacent: P11(-78,8) & P12(-92,40) S: legs: P10→P11 (-84,-26)→(-78,8) vs P12→P13 (-92,40)→(-58,70): closest (-78,8) to (-92,40): 35 → overlap ✗.

Solutions: (a) clamp skirt width dynamically by local clearance: compute for each sample the max safe offset: min over other samples of distance-to-other-centerline; width = min(55, clearance-2). Precompute per-sample clearance O(N²) = 490k ops once ✓ fine. Then skirt rows vary per sample: build skirt with per-row outer offset = clamp(clearance-2, 12, 55) inner / (12, 160) outer. Rows with different col counts complicate the grid — instead use FIXED columns but cap height issue... simpler: (b) make skirts modest: inner 40, outer 90, and fix the two pinch regions by increasing their separation: adjust control points to keep min self-distance > 2*offset+kerb (≈ 100+)? Too demanding.

Alternative (c): skirt moderate width (inner 34, outer 70) + far ground disc raised to blend: gaps between skirt edge and disc? Disc at fixed -2.4; skirt edges vary. There will be visible boundary but both grass-textured; heights differ (skirt edge y ≈ base*w + ground*(1-w) with w small → ≈ groundY ≈ -0.6±2.8; disc -2.4 → up to 5 gap cliff). With fog & trees, acceptable? Might look glitchy from side cams on hills.

Better (d): proper solution: compute clearance-based skirt width per row (option a) with grid columns normalized: use columns at fractions of local max width: off_j = wmax_j * f_j where f = [8.4/wmax?]. Hmm kerb ends at 8.4 fixed; skirt from 8.4 → wmax: cols at off = 8.4 + (wmax-8.4)*frac, frac=[0,0.12,0.3,0.55,1]. Then heights: y = base*(wfunc(off)) ... wfunc from skirtW(off) still fine (independent). Since widths vary per row, the mesh is a valid grid (columns continuous, no folds as wmax varies smoothly — clearance varies smoothly along track mostly; pinch regions wmax small on both legs ✓).

Clearance computation: for each i, clearance = min over j of |P[i]-P[j]| for samples with |i-j| arc distance > 30 (exclude neighbors along track). O(N²)=490k with cheap math — fine.

Then inner skirt wmax_i = clamp(clearance_i*0.5 - 1.5, 11, 55)? clearance = distance to nearest non-neighbor centerline point; safe half-width = clearance/2 - small margin: two facing skirts each extend clearance/2 - 0.6 → gap small. But careful: clearance measured centerline-to-centerline; skirt extends laterally clearance/2 → both sides just touch ✓.

Outer side clearance typically huge → cap 150.

Also trees/tires/boards must respect clearance too: tree offset ≤ min(52, clearance*0.45) and skip if < 12. Compute using clearance array (per idx) ✓.

Boards at HALF+5.5=12.5: check clearance > 26 else flip side/shift: choose side with larger clearance. Compute per board: pick side by clearance_i(left/right) — need directional clearance... approximate: use global clearance and alternate side; if clearance<28 skip board. Given pinch regions ~35 clearance ✓ boards mostly fine; choose board indices away from pinches: manually choose idx list spread & verify by clearance>28 condition at runtime (skip if fails). ✓

Grandstand: near straight outside — clearance there large ✓.

Tire stacks at corners: placed at HALF+2.4=9.4 lateral; clearance at corners could be ~35 → fine (9.4 < 17.5).

Also start gantry fine.

OK implement clearance:

```js
const CLEAR=new Float32Array(N);
for(let i=0;i<N;i++){let m=1e9;const xi=P[i].x,zi=P[i].z;for(let j=0;j<N;j++){const d=Math.abs(i-j);const dd=Math.min(d,N-d);if(dd<40)continue;const dx=P[j].x-xi,dz=P[j].z-zi;const q=dx*dx+dz*dz;if(q<m)m=q;}CLEAR[i]=Math.sqrt(m);}
```

490k iterations fine at load.

Skirt builder per side with per-row width:

```js
function buildSkirt(sign){
 const fr=[0,0.1,0.26,0.5,1.0]; // fraction of (wmax-8.4)
 const wOfF=f=>{...}
 rows N+1, cols 5:
 for i: wmax = sign>0? Math.min(150, CLEAR[i]*0.5-0.8) : Math.min(60, CLEAR[i]*0.5-0.8);
   wait outer vs inner: which side is "inner"? depends on track turn direction per location — not global. Hmm! Inner/outer differs per segment. Ugh.
```

Right — inside vs outside of loop varies around the track. But clearance limit applies to BOTH sides (whichever faces a pinch). So per-row per-side wmax_side = clamp(CLEAR*0.5-0.8, 11, 150) — same formula both sides, cap 150 for outer areas (clearance big). Inner pinch areas get ~16. And the loop's center: is it covered? Infield point (0,10): nearest track segments distance ~33-40 → CLEAR at those samples ~33 → skirt extends 0.5*33-0.8 ≈ 15.7 from each side... two sides facing the infield region across pinch: e.g., chicane legs at distance 36.7 → each skirt ~17.5 → gap 36.7-17.5*2 ≈ 1.7 ✓ covered (edges 1.7 apart, heights both ≈ ground*(1-w) with w at edge ≈ 0 → both at groundY: continuous ✓ roughly). Infield middle (0,10): covered by skirts of nearby segments? Distance from (0,10) to segment P5-P6 (60,-20)-(28,-10): distance to segment: point-seg: nearest (28,-10): d=√(28²+20²)=34.4 → those samples' clearance ≈ min over others... could be smaller due to P7 side: (8,-34)→(0,10): 45. So CLEAR≈34 → skirt width ≈16 from that leg toward (0,10)? Wait skirt extends laterally from the leg both directions; the infield point (0,10) lies within 16 of the leg? Distance 34 — NOT covered! Gap in infield middle: hole showing far disc at -2.4 below track y~9 → visible pit!

Need infield coverage: increase skirt width on the concave side beyond clearance/2 is unsafe only where another leg faces it — but the gap between facing skirts is (clearance - 2*(clearance/2-0.8)) = 1.6: covered by both edges! Wait if each side extends clearance/2 - 0.8, combined 2*(c/2-0.8) = c - 1.6 < c → the region BETWEEN the two facing skirt edges (width 1.6) is uncovered... tiny slit; but my concern: point (0,10) distance 34 from nearest leg, but ALSO ~34 from other legs → each leg's skirt extends 16.2 toward it → still 34-16.2 = 17.8 uncovered?? No wait: clearance is distance to the NEAREST other leg; if distance from leg A to infield point is 34 and clearance at leg A is 34 (nearest neighbor leg B)... skirt from A extends 16.2 laterally; the infield point at 34 away not covered by A; is it covered by the leg on the other side? Also ~34 away, extends 16 → 18 gap remains ✗ hole.

Hmm. Infield regions far from ALL track (> half min clearance) stay uncovered. For a loop, the infield center can be ~40+ from track everywhere → hole of radius ~20 around incenter.

Fix: add interior "infield" patch mesh: a simple large disc/shape covering the loop interior at... height varies (track above at y0-10, infield ground should be groundY ~ -0.6±2). If interior ground at groundY level, the inner skirt (which falls from trackY to groundY by offset ~45) covers the slope; interior hole at ground level filled by disc at y = -1.0 (below min groundY? groundY min -3.4...). Hmm groundY noise ±2.8.

Alternative cleaner approach: DON'T vary skirt by clearance; instead fix skirt width 55 BOTH sides, and REMOVE track self-approach problems by adjusting the track design so min clearance ≥ 115?? Too big.

Cleanest: compute skirt height with heightAt formula (which uses distance-based falloff w) and just build skirts WIDE (to 160) but resolve overlaps by height function alone? Overlapping meshes with same height function: both use heightAt(own i, own lat) — at overlapping region, two vertices from different legs at same (x,z) compute heights: heightAt uses base P[i].y * w(lat) where w depends on distance from OWN leg. At an overlap point at distance d1 from leg1 (w1) and d2 from leg2: heights differ if track heights differ → z-fight/intersect artifacts. But how often do overlaps occur with heights differing? At chicane legs 36 apart, both skirts 55 → big overlap band ~74 wide! Both compute y = own base * w(d) + ground*(1-w). At midpoint d=18 from each: w(18)=0.55ish → y = base*0.55+g*0.45: leg A base 8, leg B base 8 (both similar in that region ~8-9) → heights ≈ equal! Because bases similar, overlapping surfaces nearly coincide → z-fighting flicker where exactly equal, but visually same texture — mostly fine?? Risky but the S region heights: P6 y=8*1.2=9.6? RAW y: P5 y9,P6 y8,P7 y9,P8 y8 (scaled ×1.2 → 9.6-10.8) similar ✓. The other pinch (P11-P13 region): bases y 2,1,0 ×1.2 → 2.4,1.2,0: legs P10→P11 (base 4.8) vs P12→P13 (1.2): at midpoint d≈17 from each, w≈0.38 → yA=4.8*0.38+g*0.62≈1.8+0.6g... yB=1.2*0.38+... difference ≈ 1.4 → two overlapping surfaces 1.4 apart → one pokes through the other → visible seam artifacts (a grass ledge). Hmm.

Better fix: make heights depend ONLY on absolute position, not on which leg: define terrain field: y(x,z) = blend between "near-track height" and ground based on distance to nearest centerline point! I.e., precompute for the skirt vertices (and kart grass) via nearest-sample distance: y = trackY(nearest)*w(dist) + groundY(x,z)*(1-w). If BOTH skirts use nearest-sample-based height, overlapping regions compute IDENTICAL height (same nearest sample) → perfectly continuous terrain everywhere ✓✓. 

So: heightAt(x,z): find nearest sample j (full scan for static builds; for karts use local search): d = dist(P[j], (x,z)); lat≈d (unsigned); y = P[j].y * skirtW(d) + groundY(x,z)*(1-skirtW(d)). But note for d<8.4 (on road) w=1 → track height flat across road ✓ but careful: nearest-sample distance ≠ lateral distance when far along track... for points near track it's ≈ lateral ✓. For skirt far offsets, "nearest" might be a different leg — consistent anyway ✓.

But wait: road must use exact P[i].y along its length (built from samples) ✓ separate.

And skirt mesh: build per-side rows i, cols offsets 8.4→55, vertex pos = P[i] + SD[i]*off, but height from field function heightField(x,z) (which may not equal P[i].y*w! For inner-side pinch areas, the field height at that vertex uses ITS nearest sample — maybe the other leg — giving continuous terrain, while the vertex xz sits at legA's lateral offset... the mesh still forms: rows along track A, heights from field → surfaces from both legs meet continuously in overlap (same field) ✓. Slopes could be weird where field nearest = other leg while positioned along legA — but geometry stays continuous since field is continuous ✓. 

But there's a subtlety: field function w uses distance-to-nearest-centerline; along a vertex row at offset 8.4 from leg A, nearest is A ✓ w=1 → y = A.y ✓ matches road edge ✓.

Also hill slopes: distance field includes... fine.

And kart off-road height: use same field with its nearest sample (local search ok since kart near track). ✓ Consistent.

But one more: skirtW(dist) uses dist not signed lat; for on-road karts |lat|<8.4 → track y ✓.

Skirt grid then: cols offsets FIXED [8.4, 12, 18, 28, 45, 70, 110, 160]? Overlap between opposite skirts: both compute same field → coincident surfaces → z-fight where EXACTLY coplanar overlapping triangles... Two large overlapping grass surfaces with identical height at every point: z-fighting flicker! Because both rendered with same y → depth equal → flicker.

Avoid overlaps: cap skirt width by per-row clearance as planned (option a) AND use field height: widths vary, no overlaps, heights continuous ✓✓. Combined solution: per-row wmax = clamp(CLEAR[i]*0.5-0.9, 12, 170); cols at fractions; height via heightField at vertex (x,z) (nearest-sample scan for build: O(N*cols) with full scan per vertex = 700*7*700 = 3.4M... too slow? 3.4M simple ops ≈ fine actually (~50ms). But better: for skirt vertex at P[i]+SD[i]*off, candidate nearest is near i: search j in [i-120, i+120] window (arc 80) plus... nearest could be another leg: but if another leg were nearer than ~off... that's exactly the pinch case where wmax small → off small → nearest is i itself ✓. For safety search window ±150 samples. Cost 700*7*240 ≈ 1.2M ✓ fine.

For kart height when far off road (rare), local window ±80 fine.

Field function:

```js
function fieldHeight(x,z, iGuess){ // nearest sample via window around iGuess
 search j in window: min d2 → j*, d
 w = skirtW(d); return P[j].y*w + groundY(x,z)*(1-w);
}
```

And heightAt(i,lat) for karts: compute x,z then fieldHeight(x,z,i) ✓. For on-road (d = |lat|) consistent ✓.

But subtle: kart ON road at lat 5: nearest distance 5 → w=1 → y=P[j].y where j nearest ✓ matches road ✓.

For skirt vertex at off 8.4: d should be 8.4 → w=1 → y=P[j].y ✓ matches kerb outer edge ✓.

Edge: vertex pos xz = P[i]+SD[i]*8.4; nearest sample might be i (d 8.4) ✓.

Good — terrain solved.

Skirt cols: [8.4, 12, 18, 28, 45, 70, 110, wmax]? Simplify: cols at f in [0,0.08,0.2,0.4,0.7,1] of (wmax-8.4). wmax per row = clamp(CLEAR[i]*0.5-0.9, 13, 170). Sign per side.

Far disc at y=-2.6 only visible beyond skirt edges (far outside) ✓ no overlap since skirt covers to 170 ≥ ... disc radius 1500 centered origin: region between skirt outer edge (variable ≤170) and disc — disc at fixed -2.6, skirt edge at groundY (≈-0.6±2 → min -3.35) → could dip below disc → disc pokes through? Where groundY < -2.6, disc (at -2.6) is ABOVE skirt edge → tiny overlap sliver far away — barely visible & fogged; accept. Or clamp groundY min: groundY = -0.6 + noise*0.75, clamp min -2.2 → ≥ -2.8? clamp lower bound: Math.max(y, -2.4) for field ground part... simpler: gNoise*0.6 → ±2.2 → ground y ∈ [-3.2, 2.0]... let me just set disc y = -3.6 and noise amp 0.7 (±2.6 → min -3.3 > -3.6 ✓ never below disc) ✓. But then hill dips -3.3 vs track 0: fine.

Also trees on far outer slopes: height via fieldHeight with their i ✓.

Trees INSIDE infield (between skirts?) — infield middle beyond skirt reach (uncovered by skirt) shows disc at -3.6 → hole/cliff in infield where skirt edge (groundY≈-0.6±2) meets disc -3.6: step up to 3+ visible in infield middle... but infield middle IS covered? Skirts from both sides extend toward center: width limited by CLEAR*0.5-0.9: infield center point equidistant ~c from surrounding legs; each skirt covers up to c/2 → middle band width ~1.8 uncovered — tiny ✓ actually infield IS covered (two skirts from facing legs nearly meet). The uncovered sliver ~2 wide at the pinch middle at heights ≈ groundY both sides ✓ negligible gap to disc? Gap region: skirt edge at groundY vs disc -3.6: a 2-wide crack showing depth — could look like a dark seam; mitigate: place a few bushes/trees there? Or make skirts slightly overlap: wmax = CLEAR*0.5+3 (overlap 6) → overlapping coplanar? Heights at overlap: both use fieldHeight(same nearest? not same!) → z-fight sliver. Prefer small gap hidden by terrain irregularity + decor. Honestly a 1.8-wide seam at ~35 units from track, viewed from ground-level cams: reads as a subtle gully ✓ acceptable. Even better: add SECOND inner ring: no. Ship it.

Actually simplest robust alternative: since pinch zones are the issue, I could just design track with min clearance ≥ 80 (scale up spacing) so fixed 38-wide skirts never overlap and always cover infield... min distance between non-adjacent legs in my layout: chicane legs ~36*0.9=32 scaled... clearance*0.5 ≈ 18 < 38 → overlap. To get clearance 76+ everywhere requires much bigger track. Keep dynamic approach.

OK. Decision made. Now write everything. Also trees limit |off| ≤ min(wmax_i*0.85, 60) & ≥ 10.5.

**Now actual final code.** I'll write it out fully and check as I go. (Time to just write it.)

Also remember granular details:

- kart wheels turn: front steer groups.
- dust while drifting & offroad.
- position list updates.
- countdown.
- chase cam cuts.
- ≥2 laps: LAPS=3.

Kart update ordering in frame: 1) each kart AI update (moves), 2) pairwise collisions adjust pos, 3) recompute nearest for pushed karts next frame (fine), 4) visuals sync, 5) standings, HUD, minimap, cameras, particles, skids.

Let me handle kart visual sync function updateVisual(dt):

```
root.position.set(pos.x, pos.y, pos.z) (pos.y=groundY smoothed)
root.rotation.set(pitch, yaw, 0) order YXZ
body.rotation.z = roll; body.rotation.y = drift*slide*0.55; body.rotation.x = pitchAcc;
body.position.y = hop + grass jitter
wheels spin & steer
head/steeringwheel
blob shadow scale/opacity by hop
```

Ground smoothing: targetY = fieldHeight; pos.y += (targetY-pos.y)*min(1,dt*18).

**Countdown staging** with beeps:

```js
let stage=-1;
function cdStage(){ return cdT>3.6?0: cdT>2.7?1: cdT>1.8?2: cdT>0.9?3:4; }
```

On change: pop text: stages text: 0:'CRESTLINE GP'(small),1:'3',2:'2',3:'1',4:'GO!'(go class). Lights set = stage (stage1→1... stage4→GO green).

Beep func:

```js
let AC=null; function beep(f,d=0.12,type='square',g=0.06){try{AC=AC||new (window.AudioContext||window.webkitAudioContext)();if(AC.state==='suspended')AC.resume();const o=AC.createOscillator(),v=AC.createGain();o.type=type;o.frequency.value=f;v.gain.value=g;o.connect(v);v.connect(AC.destination);const t=AC.currentTime;v.gain.setValueAtTime(g,t);v.gain.exponentialRampToValueAtTime(0.0001,t+f? t+d);o.start(t);o.stop(t+d+0.02);}catch(e){}}
```

Fine (silent until gesture; harmless).

**Camera code**:

```js
const camPos=new THREE.Vector3(0,10,120), camLook=new THREE.Vector3();
let camMode='grid', sideCam=null, sideUntil=0, nextCutT=Infinity;
```

Per frame:

```
const leader=standings[0];
if(state==='cd'){ grid dolly }
else if(sideCam && t<sideUntil){ cam.position.copy(sideCam); fov side; lookAt leader pos+ (0,1,0) }
else { sideCam=null; chase }
cam.fov lerp; updateProjectionMatrix when changed.
```

Chase desired:

```
const k=leader;
const fy=k.yaw; const fwd=new Vector3(Math.sin(fy),0,Math.cos(fy));
const drift side offset: right vector rv=(fwd.z? right = (cos? For yaw: right = (cos yaw? forward=(sin,0,cos): right = forward × up? earlier right = forward×up... compute right = (fwd.z, 0, -fwd.x)? Check: fwd=(0,0,1) → right should be (-1,0,0) (since right=-x for +z forward): (fwd.z,0,-fwd.x) = (1,0,0) ✗ that's left. right = (-fwd.z, 0, fwd.x): (−1,0,0) ✓.
sideOff = -k.drift*k.slide*4.5 → for left drift (drift+1) side negative → offset toward right? sideVec multiplied: camPos = pos - fwd*dist + right*(sideOff)? Let me define lateral = (-fwd.z,0,fwd.x) is RIGHT. camOffset lateral = -drift*slide*4 → left drift → lateral -4 → toward LEFT (outside of left turn? left turn outside is right...). Drift cam: show kart angled — put camera slightly toward OUTSIDE of drift so we see the slide angle: left turn drift → kart slides outward (right); camera toward right side sees the angle. offset right = +right*4 for left drift: lateral = +drift*slide*4.5. ok whatever — subtle.
desired = pos - fwd*(6.8 + speed*0.06) + up*(3.0 + speed*0.012) + right*lateral
camPos.lerp(desired, 1-exp(-5.5*dt));
// keep above terrain:
const h=fieldHeight(camPos.x,camPos.z, leader.idx)+1.2; if(camPos.y<h)camPos.y=h;
look = pos + fwd*5.5 + (0,1.4,0); lookSm.lerp(look, 1-exp(-9dt));
cam.lookAt(lookSm);
fov target = 55 + speed*0.16 → 55..64.
```

During big drifts camera swing via lateral ✓.

Side cam: static pos; lookAt leader (pos+up1.2); fov = clamp(2400/dist... compute dist each frame: fov = clamp(THREE.MathUtils.radToDeg(2*Math.atan(6/d))? To keep kart ~constant size: required fov so that kart width 1.6 fills ~1/5 of view: tan(hfov/2)= (1.6*5/2)/d... simpler: fov = clamp(90 - dist*0.35, 26, 55)? dist 40 → 76→55; dist 80 → 62→55; dist 120 → 48; meh. Use fov = clamp(2600/dist, 28, 55): dist 50→52, 80→32.5, 120→28 ✓ good tele feel.

nextCut scheduling after GO: nextCutT = goAbs + 5. In race/post: if !sideCam && t>nextCutT → pick side cam (dist 15..150), sideUntil = t+2.8+rand; if sideCam && t>sideUntil → sideCam=null, nextCutT = t + 6+rand(0,3).

During countdown: grid cam.

Also at state change to 'post': nextCutT small? fine.

**Grid dolly**:

```
const c=gridC; // computed avg of kart positions at reset
const u=(4.5-cdT)/3.6; // 0→1
const ang=-2.2+u*1.1; const rad=16-u*4;
cam.position.set(c.x+Math.sin(ang)*rad, c.y+4.2-u*1.2, c.z+Math.cos(ang)*rad);
cam.lookAt(c.x, c.y+1.0, c.z);
```

ang around which axis — fine.

At GO: snap chase: compute desired and set camPos & lookSm.

**Minimap**:

```js
const mapC=document.getElementById('map'), mg=mapC.getContext('2d');
// fit
let minx=..., etc from P; scale = (168-24)/max(w,h); ox=84 - (minx+maxx)/2*scale ... note also center y.
const mapPt=(x,z)=>[ (x-cx)*sc+84, (z-cz)*sc+84 ];
path = new Path2D(); P loop lineTo closePath.
each frame: clearRect; stroke path lineWidth 9 '#23262c'; lineWidth 5 '#3d4148'; start tick accent; karts dots (leader bigger + white ring).
```

Canvas CSS panel bg + padding; canvas rounded.

DPR for canvas crispness: set canvas width 336 & style 168? Keep simple: width=336 height=336, ctx.scale(2,2), css 168. ✓

**Standings recompute** each frame:

```js
standings = karts.slice().sort((a,b)=> key(b)-key(a)); key=k=> k.finished? 1e6+(1e4-k.finT*10) : k.prog;
```

finT*10 to order; ensure finished keys > max prog (max prog ≈ 3*486+... during post they keep driving: prog grows past 1e6? no: prog = lap*L+s; laps grow unbounded if they keep lapping during post (5s → +0.5 lap) → lap ≤ 4 → prog ≤ ~2400 ≪ 1e6 ✓. But long-run? Post resets after 5s ✓.

**HUD rows**: rowEl order & content update every 0.25s.

**Lap text**: leader.lap+1 clamp 1..LAPS; if state post → 'FINISH'.

**Clock**: raceT.

Now particle system code:

```js
const PN=600;
const pPos=new Float32Array(PN*3), pSize=new Float32Array(PN), pAlp=new Float32Array(PN), pCol=new Float32Array(PN*3);
const pVel=new Float32Array(PN*3), pLife=new Float32Array(PN), pMax=new Float32Array(PN), pG=new Float32Array(PN), pS0=new Float32Array(PN), pA0=new Float32Array(PN);
let pHead=0;
geometry attrs; ShaderMaterial;
function spawnP(x,y,z,vx,vy,vz,size,life,r,g,b,alpha,grav){
 const i=pHead; pHead=(pHead+1)%PN;
 ...
}
function updateP(dt){ for i: if(pLife[i]>0){ pLife-=dt; if<=0 → pAlp=0, y=-999 (set pos y -999); else integrate: vel*=drag... vel.y+=pG*dt; pos+=vel*dt; t=1-life/max; size=pS0*(1+2.2t); alpha=pA0*(life/max)... write arrays; } mark needsUpdate }
```

Drag: multiply horizontal by (1-2.5*dt).

Dust spawn per kart per frame while skidding:

```
if(k.skid){ for w of rearWheels(worldPos): n=2: spawn(w.x+rand*.3, w.y+0.1, w.z+..., vel = kartVel*0.2 + rand*1.4, up 0.5-1.5, size 0.5-1.1, life 0.5-0.9, color tan/green by surface, alpha 0.5, grav -0.4?) }
```

dust grav slight +0.35 (rise) then fade; choose g=0.4.

Grass: color 0.36,0.52,0.28; road/kerb dust: 0.78,0.72,0.6 with alpha 0.4.

Exhaust: gray (0.55) small size 0.3, life 0.5, during cd & low speed.

Confetti: colors [kart colors], grav -9, drag low, size 0.34, life 1.4, alpha 0.9, count 90 at leader front. Also small burst at GO behind karts.

Skid system:

```js
const SKN=900;
skidMesh instanced; head=0; 
function addSkid(x,y,z,yaw){ m.compose(pos, quat from yaw (reuse tmp), scale 1); setMatrixAt(head++%SKN); instanceMatrix.needsUpdate=true }
```

Per kart: skidTimer -= dt; while skidding && timer<=0: add both wheels; timer=0.028.

Quat: tmpQ.setFromAxisAngle(UP, yaw).

**Kart physical constants re-check**: yawMax = min(3.0, aLat*1.75/max(speed,6)). At v=28 a=40: 2.43 ✓. At v=48: 1.46 — sweeper r=80: ω needed = 48/80 = 0.6 ✓.

Steer gain 2.4 err: err typical when tracking: lookahead 6+0.5v: v48 → 30 units ahead: err small ~0.1 → steer 0.24 ✓ stable.

Brake probes: probes d=[7,15,25,38,55,75]; scan window for k max: from pi to pi+? just kS at probe point & a couple before: km = max(|KS[pi-2..pi+2]|)? The corner may start beyond probe... vAllowed at distance d uses curvature AT the corner located ~d ahead: probing only at exact point might miss peak. Better: scan j from i+2 to i+80 step 4: track max k & its distance dmin; then allowed for that corner: sqrt(vc² + 2*b*dcorner). Single-pass: iterate j i+2..i+85 step 3: k=|KS[j]|; if k>0.004: d=(j-i)*ds; vc=sqrt(aLat/m k)... compute allowed=min(allowed, sqrt(vc*vc + 2*brakeAcc*d)). 28 samples × 6 karts ✓ cheap & correct.

Drift trigger uses KS at i+ ~20/ds.

Lane: apexHug: lane = clamp(KS[(i+Math.round((look*0.9)/ds))%N]*110,-1,1)*(HALF-2.0). Add bias & otShift; clamp ±(HALF-1.6)=5.4.

Also when drift active: bias deeper: lane -= drift*1.2.

Steering target point: li = i + round(look/ds); tp = P[li] + SD[li]*laneCur (use laneCur — smoothed target lane). Hmm use laneCur for position, laneTgt for smoothing: laneCur damps toward laneTgt rate 2.5/s.

**Drift mini boost**: on drift exit if driftTime>0.5: speed += 1.8 (cap maxSpeed+3), tiny.

**Collision**: after updates:

```js
for(a<b): dx,dz; d2; if(d2< (1.75)^2 && d2>1e-6): d=sqrt; nx,nz; overlap=1.8-d; a.pos += n*overlap*0.5*? a moves +n*0.5*overlap? n from b→a: a.pos += n*(ov*0.55); b.pos -= n*(ov*0.55); speed adjust: rear = lower prog: rear.speed = Math.min(rear.speed, front.speed+1.2); front.speed += 0.4 (nudge)? skip.
```

Also small heading jolt? skip.

**Visual**: dust also when colliding? skip.

**Grass detection**: |lat| > HALF+0.5 → grass (beyond kerb outer 8.4? kerb 7-8.4: rumble: onKerb: tiny jitter, no slowdown (maybe 0.98). grass: |lat|>8.6.

vAllow grass factor 0.42, plus extra decel handled by allow < speed → brake toward it.

Also spawn grass dust when grass & speed>10.

Now the countdown visuals: karts static: wheels static; slight body shake: body.position.y = 0.02*Math.sin(gt*35+i*2); head look forward; exhaust puffs every ~0.12s per kart (spawnP gray at rear).

Also during 'cd', set camMode grid; big overlay stages.

**Reset function**:

```js
function resetRace(){
 karts.forEach((k,gi)=>k.reset(gi));
 skid mesh: for i<SKN set scale0 matrix; head=0;
 particles: pLife.fill(0); pAlp.fill(0); positions y -999? just alpha 0 (discard) ✓ set pAlp zero & needsUpdate.
 standings recompute; raceT=0; state='cd'; cdT=4.5; stage=-1; sideCam=null; nextCutT=Infinity;
 gridC computed.
}
```

scale0 matrix: compose with scale (0,0,0): tmpM.makeScale(0,0,0)? makeScale then set position? Just tmpM.set(... zeros with 0 scale) — compose with scale 0 ✓.

**Kart.reset** also reset visual transforms & skid timer & drift etc ✓.

Let me also add small **position change flash** on rows? skip.

**Names & chips in rows built once** ✓.

Right — also must not forget: "wheels that turn" front steering visible; "dust or skid particles" ✓; "live position list 1st to 6th" ✓; "lap counter" ✓; "chase camera on leading kart cuts occasionally to trackside" ✓; "start countdown" ✓; "race starts on its own, ≥2 laps, no keyboard" ✓ (LAPS 3).

Also think about initial camera before countdown? state starts 'cd' immediately with dolly ✓.

Time to write final file text. I'll write carefully, compact but readable, with comments. Let me draft fully now (this is the deliverable; aim correctness > brevity).

Also one more consideration — `wrapPI` for YAW diff.

Let me pre-compute some numeric checks:

- ds ≈ L/N: L ≈ ? RAW perimeter 539 × SC 0.9 = 485 + curve smoothing → ~480; ds≈0.686.
- probes: j range i+2..i+85 step 3 → up to ~58 units ahead; braking from 54 to 28 needs (2916-784)/(2*30)=35.6 units ✓ within 58 ✓.
- lookahead look = 6+0.5*speed → 27-33 ✓.

Kart corner speeds: chicane min radius ~24 → vc=sqrt(40/0.05)=28.3 ✓ drift zone.

Wait KS smoothing reduces peak k; real apex k maybe 0.05 smoothed to 0.035 → vc=31.6. Drift threshold |KS|>0.026 at +20 units ✓ will trigger.

Top straight: P13(-52.2,63)→P0(0,66.6)→P1(52.2,68.4) (scaled): gentle. Start line at P[0].

**Grid pos**: s=L-8-row*5.5 → rows at L-8, L-13.5, L-19 → along straight before line ✓ straight segment from P13(-52,63) to P1: length ~104 ✓ fits.

**Countdown lights orientation**: gantry at idx0 facing along track: lights face -z local (toward approaching karts)? Karts approach from behind gantry (they cross line traveling +local z? they travel along +z local (forward)). Karts behind line see gantry's back face (local -z side). Lights mounted on crossbar facing -z: sphere visible anyway (3D sphere) ✓ no orientation issue.

**Grandstand crowd texture repeat**: set repeat (6,1).

Let me write out tree scattering avoiding track: for attempts: i=rand idx, side=±1, off = 10+rand^2*45; also require off < CLEAR[i]*0.45 (avoid crossing other leg) → else retry. y=fieldHeight at pos ✓.

fieldHeight for arbitrary (x,z) with guess i: search window ±140 samples step 2 then refine? For static placement, full scan ok (200 trees × 700 = 140k ✓). For per-frame kart & camera: local window ±60 step1 = 120 checks ✓.

Implement fieldHeight(x,z,i): window ±60 (≈41 units each side... at 60 samples = 41 units arc; a point 30 units off track laterally: nearest sample still within window ✓ since lateral < arc window ✓).

Camera terrain check uses leader.idx guess ✓ fine.

Also global terrain height func for skirt building: use per-vertex with i known: search window ±150.

Edge: skirt vertex could be nearer to a DIFFERENT leg (pinch): window ±150 might miss it if other leg farther in index but spatially close: pinch legs are usually far apart in index too (S sections: leg separation ~30-80 samples ✓ within 150). The straight vs far side: index gap large (~300+) > 150 ✗ → window misses → but wmax there is capped by CLEAR anyway (pinch → small wmax) → far leg irrelevant ✓. For big-clearance rows (outer side), off up to 170: nearest sample spatially = own i ✓ within window ✓.

Wait: outer side at a pinch? Both sides of leg at pinch have small CLEAR → wmax small both sides ✓ cap fine.

But hmm: wmax formula uses CLEAR[i]*0.5-0.9: CLEAR is distance to nearest other-leg centerline; skirt extends CLEAR/2-0.9 → facing skirts leave 1.8 gap ✓.

For inner skirt at wide regions (e.g., infield center big area): CLEAR ~ distance to nearest leg 33-40 → wmax ≈ 15-16: infield center (radius ~15 from center) NOT covered by skirts → gap region in middle of loop showing far disc! Loop interior around (0,10)-(−20,30)? Distance from (0,10) to nearest track point: computed ~34 → skirt covers 16 from each surrounding leg → center ~ (0,10) region: distance 34 from ALL legs? Then uncovered disk of radius ~34-16=18 around (0,10) shows disc at -3.6 while skirt edges at groundY(-0.6±2): seam cliff ~3 units — in the MIDDLE of the infield, far from camera focus... visible from side cams & chase on hills! Hmm. Mitigate: add an infield pond/decor? Better: add one more ground layer: a big disc at groundY-ish level? The issue is terrain height varies ±2.

Alternative: raise far-disc to y = -1.6 and reduce noise amp to 0.5 (±1.85 → ground ∈ [-2.45, 1.25]) → skirt edge min -2.45 vs disc -2.6: ✓ no dip; gap seam ≤ ~4.5 but heights close → seam is a gentle 1-3 unit step, fog & distance hide it. And clamp: groundY = -0.6 + gN*0.5. Skirt edge height ≈ groundY. Disc at -2.7. Max step 2.5 — reads as a low bank/hollow ✓ fine. Trees planted near seam hide it partially. Good enough — moving on.

Actually wait, also simpler alternative: make the far disc NOT flat: skip. Ship it.

**Infield decoration**: add a few trees/billboard INSIDE infield: tree placement uses random side ±: inner side trees at off 10..(CLEAR*0.45) ✓ they'll populate infield edges. Add a small lake? skip.

Flags along start straight outside & gantry ✓.

Okay — also kart blob shadow on road only (karts stay near road) ✓ uses pos.y + 0.03.

**Let me now also design HUD minimap orientation**: fit track bbox; fine.

**Final code assembly** — writing now, complete file. I'll keep functions tight. Also add `overflow:hidden`, canvas block.

One more requirement re-read: "dust or skid particles" ✓ both; "wheels that turn" ✓; "simple drivers" ✓; "kerbs" ✓; "hills" ✓; "decorated scenery" ✓; "six karts" ✓; "follow racing line, take corners, drift, overtake" ✓; "position list, lap counter, chase cam + trackside cuts, countdown" ✓; "starts itself, ≥2 laps, no keyboard" ✓; "three.js r186 module" ✓.

Now writing the file. I'll number sections mentally to keep coherent. Given complexity, I'll write ~700-850 lines. Let me go.

```js
/* ============ setup ============ */
```

Kart build details (write concretely with helper `box(w,h,d,c,x,y,z,parent)`):

```js
function box(w,h,d,c,x=0,y=0,z=0,p=null){const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),new THREE.MeshLambertMaterial({color:c}));m.position.set(x,y,z);if(p)p.add(m);return m;}
```

Materials count: many small materials — fine (or cache by color: matCache). Use cache to reduce program count: `const MATS={}; const mat=c=>MATS[c]??=new THREE.MeshLambertMaterial({color:c});` ✓ shared.

Kart geometry (units): width 1.7, length 2.6, wheel r 0.33.

Details:

```
root (Group, rotation.order='YXZ')
 ├ shadow (circle 1.5, y0.03, opacity .3)
 └ body (Group at y 0)
    ├ pan box(1.5,0.14,2.4, dark 0x23262b) y0.32
    ├ nose box(1.05,0.34,0.9, c) y0.52 z0.78
    ├ noseTip box(0.6,0.22,0.4, trim) y0.5 z1.28
    ├ podL/R box(0.32,0.34,1.1, c) (±0.62,0.5,0.05)
    ├ cockpit rim? skip
    ├ engine box(0.62,0.42,0.55, 0x2c2f34) y0.66 z-0.8
    ├ exhL/R cyl(0.06,0.06,0.42) rotX(π/2) (±0.18,0.92,-1.05) 0x9aa0a8
    ├ spoiler box(1.35,0.07,0.34, trim) (0,1.02,-1.12) + struts×2 box(0.06,0.22,0.06) (±0.5,0.9,-1.1)
    ├ seat box(0.62,0.5,0.16, trim) (0,0.78,-0.38)
    ├ bumpF box(1.55,0.12,0.2, trim) (0,0.34,1.32); bumpR (0,0.34,-1.32)
    ├ driver group at (0,0,-0.15):
    │   torso box(0.55,0.48,0.38, 0x2a2d33) y1.02
    │   arms box(0.09,0.09,0.42, 0x2a2d33) (±0.24,1.22,0.18) rot.x=-1.0
    │   headG (y1.5,z0.02): helm sphere(0.3, c) ; visor box(0.34,0.14,0.1,0x101215) (0,0.02,0.22); cap? ok
    ├ steerW torus(0.16,0.035,6,12) (0,1.14,0.3) rot.x=-1.15 col 0x17191d
    ├ wheelFL etc:
    front: steer group at (±0.74,0.33,0.85) → spin group → tire cyl(0.33,0.33,0.24,12) rotZ(π/2) dark + hub cyl(0.13,0.13,0.25,8) rotZ light 0xb9bfc6
    rear: spin at (±0.78,0.37,-0.82) r0.37 w0.3
```

Front wheels z +0.85 (forward is +z local ✓ since yaw convention forward=(sin,cos) and root rotation.y=yaw maps local +z → world fwd ✓).

Body parts z positive = front ✓ consistent (nose z 0.78 front ✓).

Arm rotation: arms from shoulder to wheel (wheel at z0.3 y1.14, shoulder y1.22 z0.05?) — arm box oriented along z, rotate x -0.9 tilts... rough ok.

Head turn: headG.rotation.y = steerVis*0.5.

Steering wheel spin: sw.rotation.z? After rot.x=-1.15 the torus local z points... just rotate sw.rotation.y? Eh — set steer wheel as child of a holder with rot.x, then rotate holder.rotation.z? Torus in XY plane default (axis z). rot.x=-1.15 tilts toward driver. Spinning around its axis = rotation.z of the mesh (local z axis still torus axis before tilt? If we rotate mesh.rotation.x, its local z tilts too; spinning about torus axis = rotate about LOCAL z: mesh.rotation.z? Order XYZ: rotation applied... simplest: put tilt on parent holder, spin on child mesh.rotation.z ✓.

Fine details enough.

**Now the AI numbers final**:

```
maxSpeed per roster; accel 21; brake 30;
yawMax=min(3.0, aLat*1.7/max(v,6))
steer=clamp(err*2.5,-1,1)
drift in: |steer|>0.6 && v>26 && |KS[i+~26]|>0.024 && |lat|<8.5
drift out: |steer|<0.32 || v<20 || |lat|>9
slideTgt = drift? 0.14+0.22*min(1,|steer|) : 0 (max 0.36)
moveYaw = yaw - drift*slide*0.55
hop on entry.
miniBoost on exit +1.6 (≤maxSpeed+2)
```

Slip physical 0.55×0.36≈0.2 rad max → lateral slip v*sin≈ up to 10?? 0.36*0.55=0.198; v=30 → sin0.2≈0.2 → 6 u/s outward — still a lot; but steering pursuit compensates (nose turns more inside, path curves back). Risk of wide drift pushing off road: the lane target during drift = deeper apex (lane -= drift*1.2) counteracts ✓ plus grass penalty recovers. Actually let me reduce physical slip factor to 0.4 (max slip angle 0.26 rad → 5.5°) — visible slide without chaos; visual body yaw adds extra 0.35. OK: moveYaw = yaw - drift*slide*0.4, body.rotation.y = drift*slide*0.8.

Kart visual roll lean: body.rotation.z = -drift*slide*0.6 - steerVis*0.05.

Hmm sign for roll: earlier determined lean into left turn → rotation.z negative for drift+1 ✓ -drift*slide*0.5 ok.

**Collision radius** 1.75.

**Standings & camera leader switch smoothness**: chase follows standings[0]; when leader changes, camera snaps? Lerp handles (desired jumps → camPos lerps quickly across track — could swoop weirdly mid-race). Better: keep chaseTarget = current leader but if leader changes, briefly increase lerp rate? The swoop across the track when leader swaps is actually jarring. Options: camera cuts to side cam on leader change? Simpler: chase desired computed from NEW leader: camPos lerp rate high (fast catch) → a quick swing — acceptable-ish, often happens during side cam hold (then cut back to new leader cleanly!). Since cuts happen often, most swaps masked. Also when returning from side cam, snap directly (no lerp from old pos): on mode switch to chase → snap. ✓ Implement snapCam flag.

**Minimap colors**: use CSS hex strings per kart stored in cfg.css.

**Row building** with chip color = css.

**The finish banner**: big text 'FINISH' + sub line? Use #big with class fin showing "FINISH" then small line under? Add #sub2 element? Keep single big; after 1.2s change text to "WINNER · PEPPER"? Do: big shows "FINISH"; after 1.4s big shows winner name small? Simpler: big.textContent = 'FINISH — PEPPER'? Font large... set class fin (smaller) text `FINISH · PEPPER WINS` ✓.

Confetti spawn at that moment at leader position ✓.

**Post → reset at 5.5s** ✓.

**raceT clock** stops at winner finish: store finalTime = raceT at that moment; display continues? Show frozen finalTime ✓ standard.

Now — leaderboard gap uses leader prog; after finish, gaps vs winner frozen? compute vs standings[0].prog — winner keeps driving so prog grows; finished others show FIN ✓; unfinished show gap vs winner? During post, leader = winner (finished, key huge) → gap for unfinished = (winnerProg? key mismatch). During post, compute gap vs leader.prog still fine (winner keeps racing, gap meaningful-ish) ✓.

**Minor**: kart.finished karts keep lapping; their lap increments beyond LAPS — lap display uses leader only ✓ fine.

**Performance**: per frame: 6 karts × (nearest 49 + probes ~30 + overhead) trivial.

Now — WRITE IT.

Also don't forget `scene.fog` and background fallback color, and renderer clear color irrelevant w/ sky dome.

Also `renderer.domElement` styling default fullscreen ✓ body margin 0.

Let me also handle tab visibility dt clamp (dt=min(0.05, delta)) ✓.

Also initial camPos before first frame: set at grid dolly per state ✓ computed each frame in cd.

**Write out the track prop positions** using idx fractions:

- gantry: idx 4.
- arch2: idx Math.round(N*0.56).
- boards: 8 at idx (k+0.5)*N/8, side alternate, skip if CLEAR<30 → shift idx by +17 until ok (try few).
- tires: segments |KS|>0.042 contiguous (min length 8 samples): step 2.6 units.
- flags: along straight idx N-90..N-10 step ~14 outside; plus near gantry.
- trees 150 attempts.
- clouds 8; balloons 2; mountains 16.

**Bench**: trees instanced: trunkIM (150), pineIM (150), oakIM? Combine: leaf geometry cone for pines (count pC), icosahedron for oaks (oC). Use 3 instanced meshes with counts set. Colors per instance via setColorAt (needs material color white + vertexColors? instanceColor works with Lambert ✓).

Tree y: fieldHeight(x,z, i) minus small sink 0.15.

Scale random.

Tire stacks: as computed.

Also START banner secondary arch texture "SLIPSTREAM SECTOR".

**Crowd/stands detail**: 

```
stand group at P[idxS] where idx = N-46; outside dir = -SD? Determine outside: which side is outside? At straight (heading +x), left SD=(0,0,-1) points toward interior (interior z<66 side? interior of loop: loop extends to z≈-47 at bottom; straight at z≈66-68 top; interior = below = -z = left ✓ so outside = -SD → lat negative side. Position: pos = P + SD*(-(HALF+13)) etc. stand faces track: lookAt(track point).
Rows: 4 steps: box(44,1.6,2.4) at local offsets rising; use crowd tex on all faces (uv scale) — MeshLambert map crowdTex, repeat via geometry uv default (0-1) stretched — set tex.repeat(6,1)? Shared texture though — clone texture for stand with repeat set ✓.
Roof plane box(46,0.25,8) at y 6.5 tilted slight; posts 4.
Back wall? skip.
```

Also a few umbrella dots? skip.

**Fences**: white posts+rail along start straight outside edge: posts every 4 units idx range [N-80, N+40] at lat ±? Just outside kerb (HALF+1.2), height 0.9: instanced post cylinder(0.05,0.05,0.9) count ~30 + rail: long thin boxes per segment... skip rails; posts+ two rails as one long box per straight side? Simple: rail = box(0.06,0.06,len) positioned along tangent — do 2 rails × ~30 segments = 60 meshes... too many; use instanced posts only + skip rails. Fine, minor.

Actually skip fence entirely; boards/tires/flags enough.

**Balloon**: group: sphere(4.5) color striped? two-tone via two half? Use LatheGeometry? Just sphere + basket + 4 lines (thin cylinders). Animate pos y bob & rotate slowly. 2 balloons.

**Clouds**: 7 groups of 3 spheres scaled (2.5,0.9,1.4)*rand; Lambert white; y 40-70; drift x slowly, wrap ±600.

**Mountains**: cone(1,1,5) scaled: radius 90-160, height 70-150; color #7e93a8 & #93a7ba; positions ring radius 620-820 around center of track bbox center. With fog 950 far → nicely hazy ✓.

**Center of map**: track bbox center ≈ ((-104+104)/2? scaled coords: x from -92*0.9=-83 to 104*0.9=94 → cx≈5; z from -52*0.9=-47 to 74*0.9=67 → cz≈10. Mountains centered (5,0,10).

Sky/fog color harmony ✓.

**Let me also double check kart progress vs road direction**: our samples order: P from curve.getSpacedPoints follows control point order: P0(0,66.6)→P1(52,66.6...) wait scaled: RAW×0.9: P0=(0,0,66.6), P1=(52.2,y,68.4)? RAW[1]=[58,0,74] → (52.2, 0, 66.6)... hmm z: 74*0.9=66.6 both P0 z 66.6 & P1 z 66.6? RAW[1] z=74 → 66.6 ✓ straight along +x ✓. Then turns... direction of travel = increasing i. Karts drive in +i direction (target ahead = i+look) ✓ grid placed behind line at s=L-8 ✓ lap crossing logic ✓.

Which visual direction does the loop turn? Points go (0,66)→(52,66)→(86,52)... → z decreasing → clockwise in x-z plane (viewed from +y looking down with x right, z up? screen mapping irrelevant) — fine.

Signed curvature consistency: derived left = SD; k>0 = yaw increasing = turning left toward... yaw=atan2(Tx,Tz): T=(1,0)→yaw π/2 (facing +x). Turning from +x toward -z (as track does after P1): T=(1,0)→T=(0.7,..,-0.7): yaw atan2(0.7,-0.7)= 3π/4 — yaw INCREASED from π/2 → k>0 = left turn?? But turning from +x toward -z... facing +x, left = -z ✓ (established) → yes turning toward -z is LEFT ✓ k>0 left ✓ consistent. 

At P1→P2 the track turns LEFT (toward -z from +x)? Wait it goes (52,66)→(86,52): direction (34,-14) from (1,0)-ish → yes veering left ✓.

Loop closure total turn should be ±2π ✓ whatever.

**Check the "outside" of turn 1 for tire stacks**: apex side = +SD*sign(k); outside = opposite ✓ formula uses -sign(k).

**Billboard facing**: group.lookAt(track point) — plane child faces +z → after lookAt, +z points to track ✓ visible from track ✓.

**Board posts**: cylinders below plane.

**Trees on hills**: y from fieldHeight ✓.

**Blob shadow texture**: radial? Use plain circle geometry with basic material opacity 0.28 — crisp edge; soften with canvas radial texture: make radialTex once (black center → transparent) used for both blob & particles ✓ (blob material color black, map radial, transparent).

Particles material uses same tex ✓.

**Kart front z +0.85 wheels & rear -0.82**: length 2.6 ✓.

**Wheel radius**: front 0.33 → y 0.33; rear 0.37 → y 0.37.

**Steering angle visual**: steerVis damps to steer*0.42 (rad max ~0.42 ≈ 24° ✓).

Wheel spin: rotation.x += (speed/0.33)*dt for front (r.33), rear r0.37.

Hmm spin sign: derived rotation.x positive → forward ✓.

**Drift dust offset**: rear wheels world pos: local (±0.78, -0.82): world = pos + R(yaw)·local. R: wx = lx*cos(yaw)+lz*sin(yaw); wz = -lx*sin(yaw)+lz*cos(yaw) ✓.

**Skid quads at rear wheels** yaw = moveYaw ✓ length along movement 1.5 covers spacing speed*0.03.

Spawn interval 0.028s → at 50 u/s spacing 1.35 ✓ continuous.

**Confetti & finish**: detect leader lap crossing in kart.update → if lap===LAPS && !finished: finished=true, finT=raceT; if kart is leader (first finisher) → trigger finish state.

First finisher = standings[0] at that moment? The one whose lap hits LAPS first IS the leader effectively ✓ (they're ahead). Trigger raceEnd(kart).

**Countdown beeps**: stage changes: beep(560,0.1); GO: beep(920,0.5,'square').

**Also rev sounds none**.

**Reset timing**: postT>5 → resetRace().

**Big overlay initial**: "CRESTLINE GP" small intro (stage 0) then numbers ✓.

**Cam tag text**: grid: 'GRID CAM'; chase: `CHASE · P${rank} ${name}`; side: `TRACKSIDE ${i%4+1}`.

Compute rank of leader = 1 always ✓ show leader name.

Also maybe cam tag shows speed? skip.

**Colors CSS**: accent #ff4d1c; green go #86e04e.

Alright, also sub caption line: static bottom-center small.

**Write out everything now in final form.** During writing, keep variable names consistent: P, SD, T, YAW, KS, KS2(second smoothed?) Use KSm (smoothed once) & KS (twice) — use KS for logic.

Let me write the lap-checking constants: LAP_FORWARD thresholds: sPrev>0.72L && s<0.28L.

Kart.update signature update(dt,t,ctx) — needs leaderProg for rubber band: pass leaderProg (max prog). Compute before updates ✓ (previous frame's standings fine).

Rubber band: factor = 1 + clamp((leaderProg - prog)*0.0004, -0.02, 0.06) — trailing karts up to +6%, leader -0..-2%? if diff<0 → -0.02 max. Wait leader has gap 0 → 1.0. Others behind positive boost ✓. Apply to vAllow only ✓.

Also throttle & braking smoothing: accelSm for body pitch: pitch = clamp((v - vPrev)/dt * -0.004? use (speed change): aInst=(speed-prevSpeed)/dt; bodyPitch = clamp(aInst*0.006, -0.05, 0.06) lerped.

Slope pitch: rotation.x = -Math.asin(clamp(T[i].y,-.5,.5)) + hmm sign: climbing (T.y>0) → nose up → rotation.x negative ✓ -asin(T.y) gives negative ✓.

Wait rotation.x negative = nose up? Earlier: rotation about +x by -θ lifts +z (forward) toward +y ✓ yes nose up. ✓

But rotation.x applies BEFORE yaw? order 'YXZ' → yaw first then pitch about the yawed local x ✓ correct vehicle behavior.

Roll (body.rotation.z) local ✓.

**Grid reset yaw**: yawArr[idx] ✓.

**pos.y initial**: fieldHeight at grid = P[idx].y (on road) ✓.

**One more mechanic**: kart.root children shadow scale with hop ✓ minor skip (keep static).

**Minimap dots**: leader ring: draw white circle r5 under colored r3.5 ✓.

**Countdown overlay 'CRESTLINE GP'** uses class small → font ~44px ✓ pop.

Now, be careful with one physics detail: `steer` (input) used for yaw update; store as this.steerIn; steerVis for visuals.

Also lateral slip means kart can drift wide beyond road even with pursuit — grass slow handles ✓.

**Collision after move** before visuals: positions adjusted; groundY recompute? negligible.

**Frame budget** fine.

Also, remember requirement "The animation should show everything important within the first 30 seconds" — countdown starts immediately on load ✓; beeps maybe blocked but visual countdown ✓; overtakes: grid reversed speeds → pass at T1 within ~6s ✓; drifts at first chicane ~8-10s ✓; trackside cut at ~GO+5 ✓; lap counter to LAP 3 by ~29s ✓ (lap1 ~11.5s: crossing at ~GO+11.5=15.5 → LAP 2; +11.5 → 27 → LAP 3 ✓).

Set LAPS=3.

**Kart draw call count**: each kart meshes: pan, nose, 2 pods, engine, 2 exh, spoiler, 2 struts, seat, 2 bumpers, torso, 2 arms, helm, visor, sw holder+sw, 4×(steer? front steer group + spin + tire + hub ×2, rear spin+tire+hub ×2) ≈ 28 objects ×6 = 168 draw calls... a bit high but static geometry small — fine for modern GPUs (draw calls cheap-ish). Could merge hub into tire (two meshes each wheel: 8). OK total scene ~350 draw calls worst — still fine at 60fps generally. Reduce a bit: struts merge into spoiler? Keep, fine.

Actually let me trim: exhaust 1 pipe, struts skip (attach spoiler directly), arms 1? Keep 2 arms (driver visibility). ~26 each. OK.

**Let me now write the actual final answer code.** I'll write it in one continuous block, testing logic mentally as I write. Pay attention to:

- All referenced DOM ids exist.
- No syntax errors (careful with template literals inside module).
- Texture creation before materials.
- Order: constants → helpers → track arrays → geometry → scenery → particles → skids → karts → HUD → cameras → state machine → loop.

Writing:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Crestline GP — a self-driving kart race</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  html,body{width:100%;height:100%;overflow:hidden;background:#0c0e11}
  canvas.webgl{display:block}
  #ui{position:fixed;inset:0;pointer-events:none;z-index:10;font-family:"Trebuchet MS","Segoe UI",Verdana,sans-serif;color:#f4f1e8}
  .panel{background:rgba(14,16,20,.84);border:1px solid rgba(255,255,255,.09);border-radius:10px;box-shadow:0 3px 0 rgba(0,0,0,.35)}
  #board{position:absolute;top:16px;left:16px;padding:10px 12px 12px;min-width:216px}
  #board h4{font-size:10px;letter-spacing:.28em;color:#8f97a3;font-weight:700;margin:0 2px 8px}
  .row{display:flex;align-items:center;gap:8px;padding:3px 9px;margin:3px 0;border-radius:5px;transform:skewX(-9deg)}
  .row .rk{width:16px;font-size:15px;font-weight:900;font-style:italic;color:#79818d}
  .row .chip{width:10px;height:10px;border-radius:3px;flex:none;box-shadow:inset 0 0 0 1px rgba(0,0,0,.35)}
  .row .nm{flex:1;font-size:13.5px;font-weight:700;font-style:italic;letter-spacing:.05em}
  .row .gp{font-size:11px;color:#98a0ac;font-variant-numeric:tabular-nums;min-width:52px;text-align:right}
  .row.ld{background:rgba(255,79,32,.18);box-shadow:inset 0 0 0 1px rgba(255,79,32,.55)}
  .row.ld .rk{color:#ff6a3c}
  #lapbox{position:absolute;top:16px;right:16px;padding:9px 16px 10px;text-align:right}
  #lap{font-size:23px;font-weight:900;font-style:italic;letter-spacing:.04em}
  #clock{font-size:12.5px;color:#98a0ac;font-variant-numeric:tabular-nums;letter-spacing:.08em}
  #mapbox{position:absolute;left:16px;bottom:16px;padding:8px;border-radius:10px}
  #map{display:block;width:168px;height:168px}
  #camtag{position:absolute;right:16px;bottom:16px;padding:7px 13px;font-size:11px;font-weight:700;letter-spacing:.24em;color:#c9cfd8}
  #sub{position:absolute;left:50%;bottom:14px;transform:translateX(-50%);font-size:10.5px;letter-spacing:.34em;color:rgba(244,241,232,.5);white-space:nowrap}
  #big{position:absolute;left:50%;top:36%;transform:translate(-50%,-50%);font-size:min(17vw,150px);font-weight:900;font-style:italic;letter-spacing:.02em;color:#f4f1e8;text-shadow:.05em .08em 0 #14161a;display:none;text-align:center;line-height:1}
  #big.on{display:block}
  #big.go{color:#8be04a}
  #big.fin{color:#ff4f20;font-size:min(8.5vw,64px)}
  #big.sm{font-size:min(6.4vw,46px);letter-spacing:.12em}
  #big.pop{animation:pop .5s cubic-bezier(.2,.85,.3,1.15) both}
  @keyframes pop{0%{transform:translate(-50%,-50%) scale(2.4);opacity:0}22%{opacity:1}100%{transform:translate(-50%,-50%) scale(1)}}
</style>
</head>
<body>
<div id="ui">
  <div id="board" class="panel"><h4>RUNNING ORDER</h4><div id="rows"></div></div>
  <div id="lapbox" class="panel"><div id="lap">LAP 1/3</div><div id="clock">0:00.0</div></div>
  <div id="mapbox" class="panel"><canvas id="map" width="336" height="336"></canvas></div>
  <div id="camtag" class="panel">GRID CAM</div>
  <div id="sub">CRESTLINE GP · SIX AI DRIVERS · THREE LAPS · CHASE + TRACKSIDE CAMERAS</div>
  <div id="big" class="on sm"></div>
</div>
<script type="module">
import * as THREE from 'three';
/* ... */
</script>
</body>
</html>
```

Now the big module. Let me carefully write each part.

```js
// ---------- tiny utils ----------
const rand=(a,b)=>a+Math.random()*(b-a);
const clamp=(v,a,b)=>v<a?a:v>b?b:v;
const lerp=(a,b,t)=>a+(b-a)*t;
const wrapPI=a=>{a%=Math.PI*2;if(a>Math.PI)a-=Math.PI*2;if(a<-Math.PI)a+=Math.PI*2;return a;};
const damp=(rate,dt)=>1-Math.exp(-rate*dt);
```

matCache + geometry helpers.

Track:

```js
const RAW=[[0,0,74],[58,0,74],[96,2,58],[104,4,22],[88,7,-10],[60,9,-20],[28,8,-10],[8,9,-34],[-24,8,-52],[-58,6,-52],[-84,4,-26],[-78,2,8],[-92,1,40],[-58,0,70]];
```

Wait P13 z: to make straight with P0 z=74? P13=( -58,0,70) vs P0 (0,0,74): slight angle ok (curve). Keep (-58,0,72).

Perimeter check earlier 539 with P13 (-58,74): I changed z 70 vs 74 negligible.

Scale: SC=0.9, y×1.2.

```js
const cps=RAW.map(p=>new THREE.Vector3(p[0]*0.9,p[1]*1.2,p[2]*0.9));
const curve=new THREE.CatmullRomCurve3(cps,true,'centripetal');
const N=700,L=curve.getLength(),ds=L/N;
const P=curve.getSpacedPoints(N).slice(0,N); // hmm getSpacedPoints(N) gives N+1 pts, index N == index 0
```

Note: getSpacedPoints uses getLength internally fine.

T/SD/YAW/K/KSm/KS arrays; clearance.

Road/kerb/skirt/startline materials & textures:

asphalt:

```js
const asphaltTex=makeTex(128,128,(g)=>{g.fillStyle='#41454c';g.fillRect(0,0,128,128);for(let i=0;i<2600;i++){const v=Math.random();g.fillStyle=v<.5?'rgba(20,22,26,.5)':'rgba(255,255,255,.06)';g.fillRect(Math.random()*128,Math.random()*128,1.4,1.4);} // subtle tire wear bands
 g.fillStyle='rgba(15,16,19,.25)';g.fillRect(20,0,14,128);g.fillRect(94,0,14,128);});
asphaltTex.wrapS=asphaltTex.wrapT=THREE.RepeatWrapping;
```

Wear bands at fixed u positions — u spans across road 0..1 ✓ two darker strips ✓ nice.

grass:

```js
const grassTex=makeTex(128,128,(g)=>{g.fillStyle='#6fa551';g.fillRect(0,0,128,128);for(let i=0;i<2400;i++){g.fillStyle=Math.random()<.5?'rgba(48,84,38,.5)':'rgba(150,190,90,.35)';const s=Math.random()<.85?1:2;g.fillRect(Math.random()*128,Math.random()*128,s,1+Math.random()*2);}for(let i=0;i<26;i++){g.fillStyle='rgba(60,96,44,.30)';g.beginPath();g.arc(Math.random()*128,Math.random()*128,4+Math.random()*10,0,7);g.fill();}});
```

repeat wrap.

kerb:

```js
const kerbTex=makeTex(32,64,(g)=>{g.fillStyle='#e8e4da';g.fillRect(0,0,32,64);g.fillStyle='#d8402a';g.fillRect(0,0,32,32);});wrap repeat
```

checker:

```js
const checkTex=makeTex(200,40,(g)=>{for(let x=0;x<10;x++)for(let y=0;y<2;y++){g.fillStyle=(x+y)%2?'#17181c':'#efece2';g.fillRect(x*20,y*20,20,20);}});
```

crowd:

```js
const crowdTex=makeTex(256,64,(g)=>{g.fillStyle='#20232a';g.fillRect(0,0,256,96?)...
```

canvas 256×96: rows of dots: colors palette ['#e2d8c8','#d8402a','#f0b429','#3f7fae'?? avoid default blue... use '#4f8f6f' teal, '#c95d9f']. Random 700 dots r1-2.

banner:

```js
const bannerTex=makeTex(512,96,(g)=>{g.fillStyle='#171a20';g.fillRect(0,0,512,96);g.fillStyle='#ff4f20';g.fillRect(0,0,14,96);g.fillRect(498,0,14,96);diag stripes; g.fillStyle='#f4f1e8';g.font='900 italic 52px Trebuchet MS, sans-serif'... textAlign center baseline middle fillText('CRESTLINE GP',256,50)});
```

Fonts in canvas: generic families fine.

sign tex maker:

```js
function signTex(txt,bg,fg){return makeTex(256,96,g=>{g.fillStyle=bg;g.fillRect(0,0,256,96);g.fillStyle='rgba(255,255,255,.14)';g.fillRect(0,70,256,10);g.fillStyle=fg;g.font='900 italic 34px "Trebuchet MS",sans-serif';g.textAlign='center';g.textBaseline='middle';g.fillText(txt,128,48);});}
```

Ground materials:

```js
const roadMat=new THREE.MeshLambertMaterial({map:asphaltTex,side:THREE.DoubleSide});
kerbMat, grassMat similar.
```

Generic strip builder:

```js
function buildStrip(offL,offR,liftL,liftR,mat,tile){
 const pos=[],uv=[],idx=[];const vTile=L/Math.round(L/tile);
 for(let i=0;i<=N;i++){const j=i%N,p=P[j],sd=SD[j];
  pos.push(p.x+sd.x*offL,p.y+liftL,p.z+sd.z*offL, p.x+sd.x*offR,p.y+liftR??...
```

careful: pass liftR param.

```js
function buildStrip(offL,offR,liftL,liftR,mat,tile,uMode){
 const g=new THREE.BufferGeometry();const pos=[],uv=[],ind=[];
 const vt=L/Math.max(1,Math.round(L/tile));
 for(let i=0;i<=N;i++){const j=i%N,p=P[j],sd=SD[j],v=i*ds/vt;
  pos.push(p.x+sd.x*offL,p.y+liftL,p.z+sd.z*offL);
  pos.push(p.x+sd.x*offR,p.y+liftR,p.z+sd.z*offR);
  uv.push(0,v,1,v);
 }
 for(let i=0;i<N;i++){const a=i*2;ind.push(a,a+1,a+2,a+1,a+3,a+2);}
 g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));
 g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));
 g.setIndex(ind);g.computeVertexNormals();
 const m=new THREE.Mesh(g,mat);m.frustumCulled=false;return m;
}
```

Road: buildStrip(7,-7,0,0,roadMat,8): u across full width, v tiles 8 → asphalt repeat set (1,?) texture repeats via v ✓ u 0..1 one tile across (asphalt band stretch fine).

Kerbs: buildStrip(HALF, HALF+1.4, 0.07, 0.02, kerbMat, 3.2) and (-HALF, -(HALF+1.4)... wait mirrored: buildStrip(-HALF, -(HALF+1.4)...) orientation irrelevant ✓.

But kerb u: texture repeat across: set kerbTex.repeat? Using uv u 0..1 with texture once across ✓ (stripes along v). v tile 3.2 → red/white each 1.6 ✓.

Road uv u 0-1 (single texture across, wear bands at u .16 & .73 ✓).

Skirt builder (variable width grid):

```js
function buildSkirt(sign){
 const fr=[0,0.1,0.26,0.5,1.0];
 const g=new THREE.BufferGeometry();const pos=[],uv=[],ind=[];
 const vt=L/Math.max(1,Math.round(L/7));
 for(let i=0;i<=N;i++){const j=i%N,p=P[j],sd=SD[j];
  const wmax=clamp(CLEAR[j]*0.5-0.9,13,180);
  for(let c=0;c<fr.length;c++){const off=8.4+(wmax-8.4)*fr[c];
   const x=p.x+sd.x*off*sign, z=p.z+sd.z*off*sign;
   pos.push(x, fieldH(x,z,j), z); uv.push(off/vt, i*ds/vt);
  }
 }
 for(i<N)for(c<4): ind.push(base, base+C, base+1, base+1, base+c? grid indices:
   a=i*fr.length+c; b=(i+1)*fr.length+c; ind.push(a,b,a+1, a+1,b,b+1);
 computeVertexNormals; mesh frustumCulled=false;
}
```

fieldH(x,z,guess): nearest sample in window ±150 step 2 then refine ±2: 

```js
function fieldH(x,z,gi){let bj=gi,bd=1e9;
 for(let o=-150;o<=150;o+=2){const j=(gi+o+N*4)%N;const dx=P[j].x-x,dz=P[j].z-z;const d=dx*dx+dz*dz;if(d<bd){bd=d;bj=j}}
 refine ±2 step1; d=sqrt(bd);
 const w=skirtW(d);return P[bj].y*w+groundY(x,z)*(1-w);}
```

150 samples*2 = 150 iterations *2 (step2 → 151 iter) fine ×(701 rows ×5 cols ×2 sides)=7010 verts ×150 checks = 1M ✓.

Hmm wait skirtW(d) uses d as distance ✓ consistent for karts too (heightAt via fieldH with kart idx) ✓.

But careful: kart ground on road: d=|lat| small → nearest sample near kart ✓.

Also skid/quads & blob use kart y ✓.

Start line:

```js
const startMesh: build small strip between sample 0 and idxK=ceil(3.4/ds): custom geometry 2 rows:
rows r=0: i0=0; row1: i1=5? 3.4/ds≈5 rows ahead: use P[0..5]? Build quad strip over samples 0..5 with checker uv (u across 0..1, v 0..1 across the 5 rows) — simple: reuse buildStrip limited range: write inline small builder or just buildStrip variant with i range. I'll write buildStripRange(i0,i1,offL,offR,liftL,liftR,mat,tileU,tileV).
```

Simpler: manual 4-vert quad: corners: P[1]±SD*7 & P[6]±SD*7, y+0.06; uv (0,0),(1,0),(0,1),(1,1); two tris. Checker 10×2 squares across 14 length → square 1.4 wide, 3.4 long/2 rows=1.7 long — near square ✓ good.

Gantry & arch builder function makeGate(idx, txt, withLights):

```js
group; p=P[idx], sd, yawR=YAW[idx];
posts: cylinder(0.28,0.34,6.4) at ±(HALF+1.6)*sd, y=p.y+3.2
bar: box(width=2*(HALF+1.6),1.5,0.7) materials [side...]: front/back banner texture: BoxGeometry material array: order [+x,-x,+y,-y,+z,-z]: banner on +z & -z faces: matArr=[side,side,side,side,banner,banner].
bar position: (p.x, p.y+6.2, p.z) then rotate group.rotation.y=yawR — build group at p with rotation.y=yawR; children local: posts at local x=±(HALF+1.6), bar at y 6.2 local, lights local (±1.1/0, 4.9? under bar: y=5.2, z=-0.5 front side facing -z (approaching karts come from -z local? karts travel +i direction = local +z (since yaw maps +z to forward): karts approach the gate from behind = they arrive at gate moving +z; gate ahead of them: they see the -z face → lights on -z side: z=-0.45 ✓ visible.
lights: 3 spheres r0.24 at local (−1.2,0,−0.45),(0,..),(1.2,...) y=5.2, MeshBasicMaterial dark; store in lightsArr.
banner texture on +z/-z faces ✓ (mirrored one side, fine).
```

Second arch no lights, text 'SLIPSTREAM'.

Boards:

```js
const BOARDS=[['NITRO-COLA','#d8402a'],['APEX TYRES','#f4f1e8','#d8402a'?]...] with fg colors variants: use function signTex(txt,bg,fg).
positions k=0..7: idx=Math.floor((k+0.5)*N/8); side=k%2?1:-1; lat=side*(HALF+5.5); require CLEAR[idx]>26 else idx+=30 retry;
group at p+sd*lat, group.lookAt(p.x, group.y, p.z) — lookAt with same y: plane faces track ✓.
plane 7.2×2.3 at y+2.4; posts 2 cylinders r0.09 h2.4 at x±2.6.
```

lookAt from group position toward P (same y) ✓.

Stand:

```js
const stand=new THREE.Group(); position P[N-30] offset sd*(HALF+14)*(-1)? Which side outside at start straight: left SD=(0,0,-1) interior... wait interior z smaller: P0 z 66.6 heading +x → left = SD = (Tz,0,-Tx) with T≈(1,0,0.03)→ sd≈(0.03,0,-1) → left points -z ✓ interior. Outside = +z = -sd → offset = -sd*(HALF+14).
stand.rotation.y=YAW[idx] then local +x = ? With rotation.y=θ, local +x maps to world (cosθ,0,-sinθ); θ=YAW≈π/2 → (0,0,-1) = -z = interior side. So rows stepping toward interior = local +x direction... I want steps rising AWAY from track: away from track = +z world = local -x. So row r: local x = -r*2.2. Or just rotate π: set stand.rotation.y=YAW+π then local +x maps to +z (away) ✓ use that: children: rows at local +x*(r*2.2), facing track needs crowd on -x face... crowd boxes: box(2.2 depth? Let me define: row box: width(z-dir local? ) — I'll make rows: box(44 (along local z? no...

Ugh, simplify: build stand in world coords: stand at pos; orient with lookAt so its local -z faces the track: group.lookAt(trackPoint) → local +z toward track. Then rows: local x spans along track tangent? After lookAt, local +x = ? lookAt sets +z toward target; +x = up×+z-ish (right-handed): whatever — build rows along local z? Risky. 

Alternative dead-simple: place rows as world-space boxes oriented by yaw: row r: center = base + sdVec*(-(HALF+2 + r*2.3)) + tangent*0 ; box dims: along tangent length 44 (use BoxGeometry(2.3,1.7,44) rotated y=yaw? BoxGeometry(x,y,z): I want depth along sd and width along tangent: create geo Box(44,1.7,2.3) then mesh.rotation.y = yaw+? tangent yaw θ: box local x should align with tangent direction (sinθ,0,cosθ)... A Box's local x axis maps under rotation.y=θ to (cosθ,0,-sinθ). Tangent = (sinθ,0,cosθ). These align when? cosθ=?? For θ=π/2: box x→(0,0,-1), tangent (1,0,0) ✗ perpendicular. So use Box(44,...) with rotation.y = θ - π/2? Box local x (1,0,0) → rotated (cosφ,0,-sinφ); want = (sinθ,0,cosθ): cosφ=sinθ, -sinφ=cosθ → φ = θ - π/2? cos(θ-π/2)=sinθ ✓ sin(θ-π/2)=-cosθ → -sinφ = cosθ ✓. So mesh.rotation.y = YAW[idx]-π/2 makes box long axis along tangent ✓. Similarly depth axis along sd.

So: base point B = P[idx] + sd*(-(HALF+2)) (outside start), rows r=0..3: center = B + sd*(-r*2.3) + y=(0.85*r+0.85); geometry Box(46,1.7,2.3) rotation.y=YAW-π/2. Crowd texture on boxes: apply to all — box UV stretch: crowdTex.repeat(8,1) wrap ✓ (MeshLambert map). Different repeat per row? same fine.

Roof: Box(48,0.3,10) at B + sd*(-4.5), y=7.6, rotation.y same, color accent dark 0x23262b; posts: 6 cylinders r0.12 h7 at spread along tangent ±20, at sd*(-8.5)?? place behind top row: posts at sd*(-(HALF+2+9))... approximate ✓.

Front wall banner: Plane(46,1.6) at B + y 2.6? facing track: plane rotation.y = YAW+π? Plane default normal +z; want normal pointing toward track = +sd direction = ... plane normal +z rotated by rotation.y=φ → (sinφ,0,cosφ); want = -sd (from outside toward track) = -(Tz,0,-Tx) = (-Tz,0,Tx). With tangent (sinθ,0,cosθ): -sd = (-cosθ? sd=(Tz,0,-Tx) = (cosθ_, ...). Let me compute concretely: tangent t=(sinθ,0,cosθ); sd = left = (t.z,0,-t.x) = (cosθ,0,-sinθ). Facing direction from stand toward track = -sd = (-cosθ,0,sinθ). Need (sinφ,0,cosφ) = (-cosθ,0,sinθ) → sinφ=-cosθ, cosφ=sinθ → φ = θ+π/2? sin(θ+π/2)=cosθ ✗. φ=π/2-θ? sin=cosθ ✗ sign. φ = θ + 3π/2? sin(θ+3π/2) = -cosθ ✓ cos(θ+3π/2)=sinθ ✓. So rotation.y = YAW+3π/2 (or YAW-π/2 equivalently ✓ since 3π/2 ≡ -π/2). Interesting: same as rows rotation. And front banner plane faces -sd with rotation.y=YAW-π/2? plane's +z → (sin(YAW-π/2),0,cos(YAW-π/2)) = (-cosθ,0,sinθ) ✓ = -sd ✓. So banner plane rotation.y = YAW-π/2, positioned at B + sd*(+1.1) (toward track from B) at y 3.4? Rows rise behind; banner at front face ✓.

But wait — earlier row centers: B at sd*(-(HALF+2)) relative... I set B outside using -sd; rows extend further outside: row r center = B + sd*(-r*2.3) → more outside ✓ (since -sd is outside direction, -r*2.3*sd = +r*2.3*(-sd) ✓ away). ✓

 Crowd texture dot colors on dark — visible from behind? karts mostly see front banner ✓.

OK.

Flags: pole cylinder(0.05,0.05,3.2) + flag plane(1.4,0.9) offset; store flags for wave (rotation.y base + sin). 8 flags: idx = N-70 + k*12 (before line outside)? outside lat -(HALF+2.2)... plus a few inside. Simple loop k<10: idx=(N-80+k*7)%N, side=(k%2? 1:-1), lat=side*(HALF+2.6). Flag colors from roster. Wave: flagMesh.rotation.y = side? plus scale.x wobble. Keep small.

Trees: instanced:

```js
const trunkGeo=new THREE.CylinderGeometry(.14,.22,1.3,6);trunkGeo.translate(0,.65,0);
const coneGeo=new THREE.ConeGeometry(1.5,3.6,7);coneGeo.translate(0,2.8,0);
const ballGeo=new THREE.IcosahedronGeometry(1.5,0);ballGeo.translate(0,2.6,0);
counts: pines 90, oaks 55.
matTrunk=Lambert 0x6b4a33; leafs Lambert white with instance colors.
attempt loop max 400, placed 0..145: idx=(Math.random()*N)|0; side=±; off=10+Math.random()*Math.random()*46; if(off>CLEAR[idx]*0.5-2) continue; if near stand zone (idx>N-60 && side<0?) skip; pos, y=fieldH; s=rand(.7,1.7); pine if rnd<.6.
matrix compose; setColorAt leaf: pine colors: hsl green vary: c=new Color().setHSL(0.30+rand(-.04,.05), .45+rand(.2), .28+rand(.12)); oak: setHSL(0.26±, .4, .3).
```

InstancedMesh set count exactly placed → create arrays first (list of placements) then meshes with count.

Tires: instanced torus:

```js
segments: scan KS: |KS[i]|>0.04 runs; for each run len>10: step 2.6 units: n=runLen*ds/2.6; for k: idx=runStart+k*stepSamples... place at lat = -Math.sign(KS[mid])*(HALF+2.6): pos p+sd*lat; y=fieldH+0.32; stack second at +0.62 offset lat ±0.3 jitter.
InstancedMesh(tireGeo(0.52,0.26,8,14).rotateX(PI/2)? torus default in XY plane, rotate X 90 → lies flat XZ ✓.
colors: setColorAt: mostly 0x24262a, every 6th 0xd8402a, some 0xe8e4da.
```

Cap total 400 instances; count set.

Clouds/balloons/mountains as described.

Particles & skids as planned.

Karts & HUD & cams & loop.

Now — special care: geometry without index for skirt uses fr length fixed 5 columns; but I push per-row wmax: offsets differ per row → columns "follow" clearance ✓ no folding since clearance smooth.

The seam row i=N duplicates i=0 ✓ (j=N%N=0) ✓ continuous.

Normals via computeVertexNormals on indexed grid ✓.

For karts heightAt: use fieldH(x,z,this.idx) — window ±150 covers lateral up to? Kart at lat 12 off road: nearest sample spatially could be own idx ✓ within window ✓.

Now AI per-frame code writing... Also collect leaderProg each frame: compute standings first (from last frame prog) then updates? Order: update karts (using prev leaderProg), then collisions, then standings, HUD.

Simplify: leaderProg = max over karts of prog (prev values) — compute at frame start.

Also overtake scanning needs other karts' prog — prev-frame values fine.

Let me now also finalize Kart.reset grid slots: pole (gi=0) at front row right? lat ±2.3, rows: s=L-9-row*5.6.

Kart index mapping: ROSTER order = grid order (index 0 = pole). ROSTER sorted slowest→fastest? I said POWDER pole... define ROSTER array in grid order: [POWDER(48.6), GRAPE(49.7), BERRY(50.8), BUMBLE(51.8), MINTY(52.7), PEPPER(53.8)] ✓ fastest at back → overtaking early ✓.

Colors: POWDER white-ish 0xe8edf1 trim 0x8f979f; GRAPE 0x8a4fc9 trim 0x5a2f8f; BERRY 0x3f66c4 trim 0x24407e; BUMBLE 0xf0b429 trim 0x8a6410; MINTY 0x2fae7e trim 0x1a6b4a; PEPPER 0xe0452e trim 0x8e2416.

CSS chip colors strings stored.

Driver suit colors: dark 0x262a31, helmet = kart color, visor dark.

Names on rows ✓.

**Countdown & loop skeleton**:

```js
let state='cd', cdT=4.6, raceT=0, stage=-1, goAt=0, postT=0, finalT=null;
const karts=ROSTER.map((cfg,gi)=>new Kart(cfg,gi));
let standings=[...karts];
function bigShow(txt,cls){big.textContent=txt;big.className='on '+cls;void big.offsetWidth;big.classList.add('pop');}
```

Hmm re-trigger: set className without pop, force reflow, add pop ✓.

Tick:

```js
renderer.setAnimationLoop(()=>{ const t=performance.now()/1000; dt=clamp(t-tp,0.001,0.05); tp=t;
 if(state==='cd'){
   cdT-=dt; const st=cdT>3.7?0:cdT>2.8?1:cdT>1.9?2:cdT>0.95?3:4;
   if(st!==stage){stage=st; onStage(st);}
   karts.forEach(k=>k.idle(dt,t));
   if(cdT<=0.95){ // GO moment handled at stage 4
   }
 } else { raceT+=dt; karts.forEach(k=>k.update(dt,t)); collide(); }
 karts.forEach(k=>k.visual(dt,t));
 // standings
 standings=[...karts].sort((a,b)=>key(b)-key(a));
 // finish detect handled inside update (needs raceT & finish trigger)
 hud(t); cams(dt,t); particles.update(dt); mapDraw();
 renderer.render(scene,cam);
});
```

onStage(st): st0: big 'CRESTLINE GP' sm; beep 440. st1: '3' lights 1 beep 620. st2 '2' lights2. st3 '1' lights3. st4: 'GO!' go class, lights green flash, state='race'? At stage 4 we set state='race', goAt=t, raceT=0, nextCut=t+5, snapCam=true; beep 950 long. Lights stay green 1s then dark (check in cams/update: if state==='race' && raceT>1 && lightsGreen) reset dark.

Note: when stage 4 fires, cdT≤0.95; set state='race' immediately ✓ karts go.

Idle during cd: karts don't move; exhaust puffs; body jitter. In 'cd' don't run update.

Post: in karts update when leader finished & state==='race': set state='post', postT=0, finalT=raceT, confetti, big 'FINISH · NAME WINS' fin class. In loop: if state==='post': postT+=dt; if>5.2 → resetRace().

During 'post' karts continue update ✓ (their finished flag set individually too).

resetRace(): stage=-1, state='cd', cdT=4.6, big 'CRESTLINE GP' sm pop? show; lights dark; clear particles/skids; karts reset; finalT=null; camMode grid.

Also at very first load: big shows title ✓ via initial bigShow in init.

**Cam tag & lap clock update** in hud() every frame cheap (textContent set — throttle 0.2s for rows only).

Now Kart.update full code:

```js
update(dt,t){
 const i=this.nearest();
 const p=P[i],sd=SD[i];
 // progress
 let s=(i*ds + (this.pos.x-p.x)*T[i].x + (this.pos.z-p.z)*T[i].z)%L; if(s<0)s+=L;
 const sp=this.s; this.s=s;
 if(sp>L*0.72&&s<L*0.28){this.lap++; if(this.lap>=LAPS&&!this.finished){this.finished=true;this.finT=raceT;onFinish(this);} }
 else if(sp<L*0.28&&s>L*0.72){this.lap--;}
 this.prog=this.lap*L+s;
 const lat=(this.pos.x-p.x)*sd.x+(this.pos.z-p.z)*sd.z; this.lat=lat;
 const alat=Math.abs(lat);
 const grass=alat>8.6, kerb=!grass&&alat>HALF-0.4;
 // target lane
 const look=6+this.speed*0.5;
 const li=(i+Math.round(look/ds))%N;
 const la2=(i+Math.round((look*0.9+14)/ds))%N;
 let lane=clamp(KS[li]*110,-1,1)*(HALF-2.0);
 lane+=Math.sin(t*0.25+this.phase)*0.55+this.laneBias;
 lane-=this.drift*1.1;
 // overtake check
 this.ot= Math.max(0,this.ot-dt);
 if(this.ot<=0){
  for(const o of karts){ if(o===this)continue; let dp=o.prog-this.prog; if(dp>0.4&&dp<13){ const ld=o.lat-this.lat; if(Math.abs(ld)<2.3){ const ins=KS[la2]; const s2=(ins>=0?1:-1); let want=(o.lat+s2*2.7); if(Math.abs(want)>HALF-1.5) want=o.lat-s2*2.7; if(Math.abs(want)<HALF-1.2){this.otLane=want; this.ot=1.4;} 
   }
  }
 }
 this.ot>0 → lane= this.otLane (blend? just override while ot>0 with quick ease)
 laneTgt=clamp(lane,-(HALF-1.4),HALF-1.4);
 this.laneCur+=(laneTgt-this.laneCur)*damp(2.4,dt);
 // steering
 const tp=P[li]; const tx=tp.x+SD[li].x*this.laneCur, tz=tp.z+SD[li].z*this.laneCur;
 const err=wrapPI(Math.atan2(tx-this.pos.x,tz-this.pos.z)-this.yaw);
 let steer=clamp(err*2.5,-1,1);
 // drift state
 const kAh=KS[(i+Math.round(24/ds))%N];
 if(this.drift===0){ if(!grass&&this.speed>26&&Math.abs(steer)>0.6&&Math.abs(kAh)>0.026){this.drift=steer>0?1:-1;this.hop=1;this.driftT=0;} }
 else{ this.driftT+=dt; if(Math.abs(steer)<0.32||this.speed<20||grass){ // exit
   if(this.driftT>0.5)this.speed=Math.min(this.maxSpeed+2.5,this.speed+2.2);
   this.drift=0; }
 }
 // speed target
 let vA=this.maxSpeed*(this.finished?0.8:1);
 if(grass)vA*=0.4; else if(kerb)vA*=0.985;
 const brk=this.brake;
 for(let q=3;q<=84;q+=6){const j=(i+q)%N;const km=Math.abs(KSm[j]);if(km>0.012){const vc=Math.sqrt(this.aLat*(this.drift?0.82:1)/km);const d=q*ds;vA=Math.min(vA,Math.sqrt(vc*vc+2*this.brake*d));}}
 // rubber band
 const gap=leadProg-this.prog; vA*=1+clamp(gap*0.00045,-0.02,0.06);
 // integrate speed
 if(this.speed<vA) this.speed=Math.min(vA,this.speed+this.accel*dt*(1-0.4*this.speed/this.maxSpeed));
 else this.speed=Math.max(vA,this.speed-this.brake*dt);
 // yaw
 const ym=Math.min(3.0,this.aLat*1.7/Math.max(this.speed,6));
 this.yaw+=steer*ym*dt+this.drift*0.85*dt*clamp(this.speed/34,0,1);
 // slide
 const sT=this.drift? (0.15+0.24*Math.abs(steer)) : 0;
 this.slide+=(sT-this.slide)*damp(this.drift?3.2:5.5,dt);
 const my=this.yaw-this.drift*this.slide*0.55;
 this.pos.x+=Math.sin(my)*this.speed*dt;
 this.pos.z+=Math.cos(my)*this.speed*dt;
 // height
 const gy=fieldH(this.pos.x,this.pos.z,i);
 this.pos.y+=(gy-this.pos.y)*Math.min(1,dt*10);
 this.gy=gy;
 this.steerVis+=(steer*0.42-this.steerVis)*damp(10,dt);
 // skid & dust flags
 this.skid=this.drift!==0&&!grass;
 this.grassDust=grass&&this.speed>6;
 // skid marks
 if(this.skid){this.skT-=dt;if(this.skT<=0){this.skT=0.03;rearWheelPositions→addSkid both}}
 if(this.skid||this.grassDust){spawn dust particles}
 this.prog=this.lap*L+this.s;
}
```

Wait lap-- case: `else if` I wrote — careful with else placement ✓.

neadle leadProg global computed each frame before updates: leadProg = max prog. ✓

Note lap-- guard: only when actually reversing across line (rare) ✓.

Ah wait: there's an issue with `this.ot` overriding lane: implement: if(this.ot>0){lane = this.otLane; this.ot-=dt} — I wrote ot as timer decrement twice; clean: 

```
let laneBase = clamp(...)+wander+bias;
let lane = laneBase;
if(this.ot>0){lane=this.otLane; this.ot-=dt;}
```

✓.

Also finish slowdown: finished karts cruise 0.8×max — but they keep racing lines ✓.

`onFinish(k)`: first finisher triggers state change:

```
function onFinish(k){ if(state!=='race')return; state='post'; postT=0; finalT=raceT;
 big.className='on fin'; big.textContent=`FINISH · ${k.name} WINS`; confettiBurst(k);
 camtag etc; nextCut maybe side cam: force sideCam near? keep chase ✓ }
```

Also individual finished earlier handled (only first triggers post; others finishing during post just set flags & rows FIN ✓).

Collisions:

```js
function collide(){ for a<b: dx=b.pos.x-a.pos.x... d2; if(d2<3.06(=1.75²)... r=1.75; if(d2<r*r&&d2>1e-4){d=sqrt;nx=dx/d,nz=dz/d;ov=(r-d); a.pos.x-=nx*ov*0.5;...b.pos.x+=nx*ov*0.5; // rear speed cap
  if(a.prog>b.prog){b.speed=Math.min(b.speed,a.speed+1.0);} else {a.speed=Math.min(a.speed,b.speed+1.0);} } }
```

n direction from a to b: dx = b.x-a.x: push a back -n, b forward +n ✓.

Visual sync:

```js
visual(dt,t){
 const r=this.root;
 r.position.set(this.pos.x,this.pos.y,this.pos.z);
 r.rotation.x=-Math.asin(clamp(T[this.idx].y,-0.55,0.55));
 r.rotation.y=this.yaw;
 // body
 const hopY=Math.sin(Math.min(1,Math.max(0,this.hop))*Math.PI)*0.32; this.hop-=dt*2.6;
 let jit=this.grassDust?(Math.sin(t*47+this.phase)*0.035):0;
 if(state==='cd')jit=Math.sin(t*30+this.gi*1.7)*0.02; // revs
 this.body.position.y=hopY+jit;
 this.body.rotation.z=-this.drift*this.slide*0.5 - this.steerVis*0.12;
 this.body.rotation.y=this.drift*this.slide*0.5;
 const aI=clamp((this.speed-this.pv)/Math.max(dt,1e-3),-40,25); this.pSm+=(aI-this.pSm)*damp(4,dt);
 this.body.rotation.x=clamp(-this.pSm*0.004,-0.06,0.07);
 this.hop=Math.max(0,this.hop-dt*2.6);
 // wheels
 const w=this.speed/0.33*dt; this.wFL.rotation.x+=w;... all four
 this.steerL.rotation.y=this.steerVis; this.steerR.rotation.y=this.steerVis;
 this.headG.rotation.y=this.steerVis*0.9;
 this.sw.rotation.z=-this.steerVis*2.2;
}
```

Dust spawning done in update (per frame while flags): 

```js
if(this.skid||this.grassDust){
 for(const [lx,lz] of [[0.8,-0.85],[-0.8,-0.85]]){
  const wx=this.pos.x+lx*Math.cos(this.yaw)+lz*Math.sin(this.yaw);
  const wz=this.pos.z-lx*Math.sin(this.yaw)+lz*Math.cos(this.yaw);
  if(this.skid&&Math.random()<0.85){spawn 1-2 dust gray}
  ...
}}
```

Rate: per frame 85% per wheel ×2 wheels ≈ 1.7 particles/frame while drifting (60fps → 100/s) too many? Life 0.7 → ~70 alive per kart, 2-3 drifting → ~200 ✓ fine with PN 600. Cap spawn: use accumulator: this.dustAcc+=dt*46; while≥1 spawn.

Simplify: chance-based with accumulator ✓.

Dust colors: road drift: warm gray (0.72,0.68,0.62); grass: (0.42,0.55,0.3). kerb: mix. alpha 0.5, size rand 0.5-1.0 growing, vel: kart vel*0.3 + rand 0.8 + up 1.2.

Exhaust idle (cd): spawn gray at rear center each 0.15s.

Confetti burst: 90 particles colors random from palette, vel rand sphere 4 + up 7, grav -9, life 1.5, size 0.3, alpha 0.9. ✓

Particle update integration as planned.

Skid marks while skid: spawn at both rear wheels every 0.03: y=this.gy+0.02 (use gy stored). yaw for quad = moveYaw direction: use my (movement yaw) stored this.my ✓.

Also spawn when braking hard? skip.

**Cameras final**:

```js
let camMode='chase', sideCamPos=null, sideUntil=0, nextCut=1e9, snapNext=true;
const camPosS=new THREE.Vector3(0,30,140), lookS=new THREE.Vector3();
function cams(dt,t){
 const lead=standings[0];
 if(state==='cd'){ grid dolly; camTag 'GRID CAM'; return; }
 if(t<sideUntil&&sideCamPos){ cam.position.copy? place static; look at lead.pos+1.2y; fov=clamp(2400/dist,26,55); tag `TRACKSIDE CAM` }
 else { sideCamPos=null;
   if(t>nextCut){ pick side cam near lead (dist 16..150): sideCamPos=..., sideUntil=t+2.6+Math.random()*1.2; nextCut=t+9+Math.random()*4; }
   chase:
   const fw=...; desired...
   if(snapNext){camPosS.copy(desired);snapNext=false;}
   camPosS.lerp(desired,damp(4.5,dt));
   terrain clamp; lookS lerp to lead pos+fwd*4.5+1.2y damp(9);
   cam.position.copy(camPosS); cam.lookAt(lookS);
   fovT=55+lead.speed*0.13;
 }
 cam.fov+=(fovT-cam.fov)*damp(5,dt); cam.updateProjectionMatrix();
}
```

nextCut set at GO: nextCut=goAt+4.5. When side cam chosen: sideUntil=t+3.0; on expiry nextCut=t+6.5+rnd*3; snapNext=true (for chase re-entry snap ✓).

Pick side cam: candidates TSCAMS filtered by dist; if none → keep chase & nextCut=t+3.

Grid dolly:

```js
const c=gridC; const u=clamp((4.6-cdT)/3.6,0,1);
const ang=-2.1+u*1.2, rad=16-u*4.5;
cam.position.set(c.x+Math.sin(ang)*rad, c.y+4.6-u*1.4, c.z+Math.cos(ang)*rad);
cam.lookAt(c.x,c.y+1.1,c.z);
fovT=50;
```

gridC = average of kart positions (recomputed at reset) ✓ plus maybe center of gantry.

Also side cams list: 14 positions.

While side cam: kart still needs to be in view: lookAt leader ✓.

Also add slight camera shake on grass? skip.

**HUD update**:

```js
let hudT=0;
function hud(t,dt){ hudT-=dt; if(hudT<=0){hudT=0.24;
  // rows
  standings.forEach((k,ix)=>{const el=rowEls[k.gi];el.style.order=ix;el.classList.toggle('ld',ix===0);
    el.q('.rk').textContent=ix+1;
    el.q('.gp').textContent = k.finished? 'FIN' : (ix===0?'LEADER':'+'+((lead.prog-k.prog)/Math.max(k.speed,8)).toFixed(1)+'s');
  });
  lapEl.textContent = state==='post'?'FINISH':`LAP ${clamp(standings[0].lap+1,1,LAPS)}/${LAPS}`;
  clockEl.textContent = fmt(finalT??raceT);
 }}
```

fmt: m:ss.d.

Map draw: each frame.

Alright — also add `key(k)` for sorting:

```js
const key=k=>k.finished?1e6+(1e4-k.finT):k.prog;
```

**Kart.nearest()**:

```js
nearest(){let bi=this.idx,bd=1e9;for(let o=-10;o<=34;o++){const j=(this.idx+o+N)%N;const dx=P[j].x-this.pos.x,dz=P[j].z-this.pos.z;const d=dx*dx+dz*dz;if(d<bd){bd=d;bi=j;}}this.idx=bi;}
```

Call at start of update. Note window asymmetric forward +34 (overtake forward bias ok) & -10. ds≈0.68; window forward 34≈23u per frame ✓ (kart moves ≤0.9u/frame) plenty.

Edge at spawn: idx set from grid s ✓.

**fieldH** window ±150 step2 — 150 samples ≈ 103 units; kart lat < ~15 ✓.

Also fieldH needs brefine: fine.

**leadProg** global var updated in tick before kart updates: `let leadProg=0; karts.forEach(k=>leadProg=Math.max(leadProg,k.prog));` (prev frame) ✓ init after reset: prog ≈ -9 → leadProg=-9 ✓ rubber band ~ equal ✓.

**Kart.reset** must set prog BEFORE anything: prog=-9ish ✓.

Also spawn dust during countdown exhaust: handled in kart.idle:

```js
idle(dt,t){ this.speed=0; visuals minimal (reuse visual()); exhaust timer: this.exT-=dt; if<0 {0.16; spawn gray puff at rear center up 0.6} }
```

Just call visual with speed 0 & hop0 ✓ plus puffs.

Now write kart mesh builder concretely with coordinates (I'll finalize numbers while writing; keep proportions sane).

Also blob shadow texture: radialTex (black→transparent) reused: blob material MeshBasicMaterial({map:radialTex,transparent:true,opacity:0.55? with black texture alpha... build radial canvas: rgba(0,0,0,0.85)→0. MeshBasicMaterial({map:radialTex,transparent:true,depthWrite:false}) color default white × texture black ✓.

particle texture: white radial: rgba(255,255,255,1)→0 with soft falloff ✓.

**Points shader**:

```js
const pMat=new THREE.ShaderMaterial({transparent:true,depthWrite:false,uniforms:{uT:{value:softTex}},
vertexShader:`attribute float aSize;attribute float aAlp;attribute vec3 aCol;varying float vA;varying vec3 vC;
void main(){vA=aAlp;vC=aCol;vec4 mv=modelViewMatrix*vec4(position,1.0);gl_PointSize=clamp(aSize*(230.0/-mv.z),0.0,90.0);gl_Position=projectionMatrix*mv;}`,
fragmentShader:`uniform sampler2D uT;varying float vA;varying vec3 vC;
void main(){float a=texture2D(uT,gl_PointCoord).a*vA;if(a<0.02)discard;gl_FragColor=vec4(vC,a);}`});
```

Points frustumCulled false ✓.

Note attributes named position built-in ✓.

**Map draw**: 

```js
const mg=map.getContext('2d'); map.width=336... set once with scale(2,2)? I set canvas 336 attr & css 168: mg.setTransform(2,0,0,2,0,0) once ✓.
compute bounds from P with margin.
const mPath=new Path2D(); P.forEach... mapPt.
frame: mg.clearRect(0,0,168,168); stroke... lineJoin round.
start tick: line across at P[0] using SD[0]: from mapPt(P0+SD*7) to (P0-SD*7) stroke accent width 3.
karts: for standings reversed (draw leader last): dot fill css color, stroke #101216 width1.5? plus leader white halo.
```

css colors: precompute '#'+c.toString(16).padStart(6,'0').

**Flag wave**: flags array {mesh,base}; in tick: f.mesh.rotation.y=f.b+Math.sin(t*2.2+i)*0.28; slight rotation.z.

**Balloon bob**: y=base+sin(t*0.5+i)*1.5; rotation.y slow.

**Clouds drift**: x+=dt*1.2; wrap if >700 → -700.

Countdown lights green: store lightMats; states.

OK also **TSCAMS**:

```js
const TSCAMS=[];for(let k=0;k<14;k++){const i=Math.round(k*N/14+9)%N;const side=k%2?1:-1;const off=side*(HALF+7.5+((k*13)%5));const x=P[i].x+SD[i].x*off,z=...;TSCAMS.push(new THREE.Vector3(x,fieldH(x,z,i)+2.8,z));}
```

Pick: filter dist to leader between 14 and 130; random among up to 4 nearest-ish: sort by dist, take first 4, random pick ✓.

**Board lookAt**: bg.plane faces +z after group.lookAt(target at same height) ✓.

One concern: group.lookAt for objects at world: group.position set then lookAt(target) orients +z toward target ✓ plane child at (0, y,0) faces track ✓ posts at (±2, -1.2?) below plane: plane center y 2.6 (group at ground y: set group.position y = fieldH+0). posts children at (±2.6, 1.1, 0) height 2.4 → from ground to plane bottom ✓.

Now **writing the final file** for real, being careful about every identifier. Also remember `renderer.domElement.className='webgl'`.

Let me also predefine tmp objects: const _v1=new THREE.Vector3() etc; _m4, _q, UP.

Also kart rear wheel world calc uses yaw (nose) — but skid mark direction uses movement yaw my: store this.my=my ✓.

Also dust color on kerb: use (0.85,0.5,0.4)? fine mix.

One more: **onStage lights**: lightMats colors: dark #2a100c; stage1: mat0 red bright 0xff3520; etc; GO: all 0x2bd45a; after raceT>1.2: dark again (set flag) ✓.

**Beep impl**:

```js
function beep(f,d=0.12,g=0.05){try{AC=AC||new(window.AudioContext||window.webkitAudioContext)();if(AC.state==='suspended')AC.resume();const o=AC.createOscillator(),gn=AC.createGain();o.type='triangle';o.frequency.value=f;gn.gain.setValueAtTime(g,AC.currentTime);gn.gain.exponentialRampToValueAtTime(0.0001,AC.currentTime+d);o.connect(gn).connect(AC.destination);o.start();o.stop(AC.currentTime+d+0.05);}catch(e){}}
```

Add resume on pointerdown once.

Now — potential subtle bug: kart `prog` used for standings & rubber band & overtake dp — defined as lap*L+s ✓ set at end of update; initial from reset: prog = -1*L + s where s=L-9 → prog=-9 ✓.

**Reset grid positions**: gi → row=gi>>1, col=gi&1; s=L-9-row*5.5; idx=Math.round(s/ds)%N; lat=col?2.3:-2.3; pos=P+SD*lat; yaw=YAW[idx]; s val = L-9-row*5.5 (recompute s from idx*ds for consistency: this.s=idx*ds? minor mismatch fine — set this.s=sPrev=idx*ds ✓ and lap=-1: prog = -L + (L-9-...) = -9-... ✓ negative ✓.

Karts visual reset: call visual(0.016,0) once after setting fields (hop 0 etc) ✓.

**Check `fieldH` guess for karts near road**: fine.

**One risk**: at GO, karts at lat ±2.3 but lane target = apex lane (based on KS ahead ~ ±?) — laneCur starts at grid lat ✓ damps toward laneTgt ✓ smooth merge ✓.

**Check yaw err at start**: target far ahead on curve; yaw aligned ✓ small err ✓.

**Lap display before first crossing**: leader.lap=-1 → clamp(0,1,3)=1 ✓ 'LAP 1/3' ✓.

Now the **finish slowdown & AI after finish**: finished → maxSpeed factor 0.8 ✓ still racing line ✓.

**Standings during post**: finished sorted by finT ascending → winner first ✓.

**Confetti position**: at leader pos when finishing (near line) ✓.

**Big overlay** fin: `FINISH · PEPPER WINS`.

**resetRace** also: state='cd'; stage=-1; cdT=4.6; bigShow('CRESTLINE GP','sm'); lights dark; finalT=null; postT=0; sideUntil=0; sideCamPos=null; nextCut=1e9; snapNext=true; skid reset; particles clear; karts reset; gridC recompute; standings recompute ✓.

Also cam during 'post' continues chase/side ✓ nextCut maybe schedule: fine.

**Initial call**: resetRace() at boot + first bigShow ✓ (resetRace does it).

Let me also handle window blur/visibility dt clamp ✓ done.

**Trees near track on outside of tight corners may overlap tire walls** — visually fine.

**One risk: kerb geometry z-fight with road at inner edge (off exactly ±7, lift 0.07)** — lifted above ✓ no fight.

**Skirt row 0 at 8.4 vs kerb outer 8.4 lift 0.02** — grass y = field = track y; kerb outer at +0.02 → tiny lip ✓.

**Start line lift +0.03 over road** ✓.

**Blob shadows & skids on road**: skid y = gy+0.02, road at gy → ok; blob at gy+0.03 above skids ✓ renderOrder handles blending order (skid drawn before blob? transparent sorted by z anyway; set renderOrder: skid 4, blob 5, points 6 ✓).

Also karts on road: gy == P.y (road surface) ✓ wheels touch ✓.

**Hill crest pitch**: fine.

**Numbers for grid rows**: row separation 5.5 along s; lat stagger: poles right side? Alternate: gi0 lat -2.3 (left), gi1 +2.3, gi2 -2.3 row1... F1 staggered: offsets alternate columns ✓ fine.

**Kart count 6 ✓.**

**Potential issue: karts ram each other at start**: rows 5.5 apart & accel similar → rear karts catch slightly; collision caps ✓.

**Test collision radius vs lane width**: side-by-side lat diff 4.6 > 1.75 ✓ no false push. During racing lat diff ≥ ~2.3 for overtakes; soft push handles rest ✓.

Now — final worry: **performance of computeVertexNormals on big skirt geometry** (701×5=3505 verts ×2 sides) trivial.

**Map panel** css width 168.

**Sub caption**: fine.

Also include **OrbitControls?** Not needed; skip (allowed).

Double-check **import**: only three ✓.

Also **`big` element classes**: base '#big' with .on; cls param: bigShow(txt, cls): big.className='on '+cls; then reflow; add 'pop'.

CSS: #big variants .sm .go .fin — combined classes e.g. 'on sm pop' — but animation re-trigger: removing 'pop' then re-adding after reflow ✓ implement:

```js
function bigShow(txt,cls){big.textContent=txt;big.className='on '+cls;void big.offsetWidth;big.classList.add('pop');}
```

✓.

**Countdown stage colors**: '3','2','1' default paper; GO uses 'go' class ✓; finish 'fin' ✓.

Now write the FULL final code carefully. I'll also do a final mental pass for bugs afterwards.

Also small thing: `curve.getSpacedPoints(N)` returns N+1 points; P slice(0,N) ✓ and P[N-1]→P[0] wrap consistent (spacing equal ✓).

YAW computation: T[i] = P[(i+1)%N] − P[(i-1+N)%N] then normalize; T[i].y kept for pitch; SD uses XZ normalized.

Curvature K[i] = wrapPI(yawNext - yawPrev)/(2ds); then KSm = smooth(K, w6); KS = smooth(KSm, w6). Use KSm for braking (less lag) and KS for lane/drift ✓.

Let me also handle karts driving backwards (rare): lap-- handles ✓.

**collide()** also small separation along prog? The radial push suffices.

**Alright — writing final deliverable now.** Also add small "wind" ambient motion: banners? skip.

Estimate laps: verify L: RAW scaled perimeter ~539*0.9=485; centripetal catmull smooths corners inward slightly → maybe 470-500. speeds 48-54 max, avg ~41-43 → lap ~11-11.5s ✓.

Kart aLat variance 36-44: corner min speeds: chicane k~0.05 → v=sqrt(38/0.05)=27.6 ✓ drift there.

Drift threshold speed>26 ✓ at corner entry v~45 braking → reaches 26-30 in zone → drift triggers mid-corner ✓ visible dust ✓.

Also make sure karts don't drift on gentle sweepers: threshold |KS|>0.026 → radius <38.5 ✓ sweepers r 50-80 excluded ✓.

**Flag & board & stand positions relative to clearance** ✓ computed with CLEAR.

**Stand overlap with boards?** boards at k*index spread; one might land near stand zone idx>N-30 → skip boards idx in [N-60,N] range: adjust condition.

Alright, writing. (Also ensure no `#` heading start; begin reply with a sentence.)

Also double check points where karts could clip gantry posts: posts at ±(HALF+1.6)=±8.6 lateral — karts max lat 5.4 + drift slip ~2 → 7.5 < 8.6 ✓ ok.

Tire walls at HALF+2.6=9.6 lateral: karts on grass may hit visually — no physics; fine, rare.

**Now write the code.** I'll produce the complete file.

Additional check on `buildStrip` uv for kerb: u 0→1 across 1.4 width; kerbTex drawn vertical stripes along v ✓.

Road tile 9: `L/Math.round(L/8)`.

For startline geometry:

```js
(function(){const i0=1,i1=7;const pos=[],uv=[],ind=[0,2,1,2,3,1]; wait order: verts: A=P[i0]+sd*7 (left), B=P[i0]-sd*7, C=P[i1]+sd*7, D=P[i1]-sd*7; tris (A,B,C),(B,D,C): check up: B-A=(0,0,14)? sd≈(0,0,-1): A=P+sd*7 → z-7; B z+7; B-A=(0,0,14); C-A≈(dx,0,-7+..)... cross((0,0,14),(dx,0,0)) = (0*0-14*0, 14*dx-0, 0)=(0,14dx,0) dx>0 ✓ up.
uv: A(0,0) B(1,0) C(0,1) D(1,1).
mat basic Lambert map checkTex.
y lift +0.035.
})();
```

Also **gantry lights**: create 3 MeshBasicMaterial spheres; store refs.

Let me now also handle **cam.up**: default (0,1,0) ✓ lookAt fine.

**HUD row build**:

```js
const rowsEl=document.getElementById('rows');
const rowEls=ROSTER.map((cfg,gi)=>{const d=document.createElement('div');d.className='row';
 d.innerHTML=`<span class="rk"></span><span class="chip" style="background:${cfg.css}"></span><span class="nm">${cfg.name}</span><span class="gp"></span>`;
 rowsEl.appendChild(d);return d;});
```

order via style.order ✓ container needs display:flex column: add css `#rows{display:flex;flex-direction:column}` ✓.

**fmt time**:

```js
const fmt=t=>{const m=Math.floor(t/60),s=t-m*60;return m+':'+(s<10?'0':'')+s.toFixed(1);};
```

**Confetti colors** from roster css + white.

Now writing the complete final file. I'll be thorough and careful about matching braces. Let me also recheck the shader attribute name conflicts: 'position' built-in ✓ custom aSize etc ✓.

Also **Points geometry buffer usage**: set attributes with DynamicDrawUsage.

Final check on kart steering geometry: steerL group at front-left position with rotation.y=steerVis; child spin group rotates x. Wheel meshes: tire cylinder rotated so axis along X: CylinderGeometry(r,r,w,12) default axis Y → rotateZ(π/2) → axis X ✓ spin about X ✓ front steer rotation.y turns wheel ✓ hub: cylinder(0.13,0.13,w+0.02) same rot as tire child ✓ (visual hub spins too ✓).

Let me write kart build function:

```js
function buildKart(cfg){
 const root=new THREE.Group();root.rotation.order='YXZ';
 const body=new THREE.Group();root.add(body);
 const c=cfg.c,tr=cfg.trim;
 const add=(geo,mat,x,y,z,parent=body)=>{const m=new THREE.Mesh(geo,mat);m.position.set(x,y,z);parent.add(m);return m;};
 const B=(w,h,d,m)=>new THREE.BoxGeometry(w,h,d);
 add(B(1.5,0.15,2.4,0),mat(0x23262b),0,0.33,0,body);
 add(B(1.06,0.32,0.95,0),mat(c),0,0.53,0.8,body);
 add(B(0.62,0.2,0.5,0),mat(c),0,0.42,1.35,body); // nose tip
 add(B(0.34,0.3,1.15,0),mat(c),0.64,0.52,0.05,body);
 add(B(0.34,0.3,1.15,0),mat(c),-0.64,0.52,0.05,body);
 add(B(0.6,0.4,0.55,0),mat(0x2c3036),0,0.68,-0.82,body); // engine
 const ex=add(new THREE.CylinderGeometry(0.06,0.075,0.5,6),mat(0x9aa1a9),0.2,0.95,-1.05,body);ex.rotation.x=Math.PI/2;
 add(B(1.34,0.08,0.36,0),mat(tr),0,1.06,-1.14,body); // wing
 add(B(0.07,0.24,0.3,0),mat(tr),0.5,0.92,-1.02,body); ... struts
 add(B(0.6,0.5,0.16,0),mat(0x1c1f24),0,0.86,-0.4,body); // seat back
 add(B(1.56,0.13,0.2,0),mat(tr),0,0.36,1.32,body);
 add(B(1.56,0.13,0.2,0),mat(tr),0,0.34,-1.34,body);
 // driver
 const dr=new THREE.Group();dr.position.set(0,0,-0.12);body.add(dr);
 add(B(0.55,0.46,0.42,0),mat(0x2a2e35),0,1.0,0,dr);
 armL=add(B(0.11,0.11,0.46,0),mat(0x2a2e35),0.25,1.2,0.22,dr);armL.rotation.x=-1.05; armR mirror;
 const headG=new THREE.Group();headG.position.set(0,1.42,0.02);dr.add(headG);
 add(new THREE.SphereGeometry(0.3,12,10),mat(c),0,0,0,headG);
 add(B(0.36,0.15,0.14,0),mat(0x111418),0,0.02,0.24,headG); // visor
 // steering
 const swH=new THREE.Group();swH.position.set(0,1.12,0.34);dr.add(swH);swH.rotation.x=-1.05;
 const sw=add(new THREE.TorusGeometry(0.16,0.03,6,14),mat(0x17191d),0,0,0,swH);
 // wheels
 const tire=new THREE.CylinderGeometry(0.32,0.32,0.25,12);tire.rotateZ(Math.PI/2);
 const hub=new THREE.CylinderGeometry(0.14,0.14,0.27,8);hub.rotateZ(Math.PI/2);
 const rtire=tire.clone();? scale rear bigger: new CylinderGeometry(0.36,...,0.3).rotateZ...
 function wheel(x,y,z,r,wdt,steerParent){
  const holder=new THREE.Group();holder.position.set(x,y,z);
  const spin=new THREE.Group();holder.add(spin);
  const tg=new THREE.CylinderGeometry(r,r,r*0.8,12);tg.rotateZ(Math.PI/2);
  spin.add(new THREE.Mesh(tg,mat(0x191b1e)));
  const hg=new THREE.CylinderGeometry(r*0.45,r*0.45,r*0.85,8);hg.rotateZ(Math.PI/2);
  spin.add(new THREE.Mesh(hg,mat(0xb9bfc6)));
  (steerParent||body).add(holder);
  return {holder,spin};
 }
 const wFL=wheel(0.72,0.32,0.86,0.3), wFR=wheel(-0.72,...);
 root.add(wFL.holder)... note wheel() needs parent: pass root.
 rear: wheel(±0.78,0.36,-0.84,0.34).
 blob: const blob=new THREE.Mesh(new THREE.CircleGeometry(1.35,20).rotateX(-Math.PI/2),blobMat);blob.position.y=0.03;blob.renderOrder=5;root.add(blob);
 return {root,body,headG,steerL:wFL.holder,steerR:wFR.holder,spins:[wFL.spin,wFR.spin,wRL.spin,wRR.spin],blob};
}
```

Wheel steering: rotate holder.rotation.y ✓ (holder at position, children spin) ✓.

dr group is child of body so head lean with body ✓.

**Kart class fields**: gi, cfg refs; pos Vector3; etc.

Also collision uses pos ✓ pushed positions then visual sync uses pos ✓.

**fieldH guess for kart**: pass this.idx ✓.

Let me also handle hop: on drift entry this.hop=1 then decays; hopY sin(hop*π)? hop goes 1→0 over ~0.38s: sin(hop*π): at 1→0, sin π→0 peak at 0.5 ✓ smooth hop ✓.

**Grass bump**: also add slight speed shake via jit ✓ done.

**Confetti**: particles.spawnBurst(pos).

**Countdown lights flash green 1s**: store goT: in tick if(state==='race'&&raceT<1.1) lights green else if(stage>=4 && raceT>1.1) lights dark. Implement: track lightsState.

Simpler: in onStage(4): set lights green; schedule via setTimeout(()=>lightsDark(),1400)? setTimeout okay ✓ but on quick reset edge — fine, use raceT check in cams: if(raceT>1.2&&lightsOn){lightsDark();lightsOn=false;} ✓.

Now, the **countdown initial stage 0** shows 'CRESTLINE GP' — but first frame big shows via resetRace ✓; stage starts -1 then st computed 0 → triggers.

**onStage(0)** also beep? light. fine beep(440).

Also during cd, karts idle: they shouldn't run update; call visual only + exhaust puffs:

In tick: if state==='cd': karts.forEach(k=>{k.exT-=dt; if(k.exT<0){k.exT=0.18+Math.random()*0.1; puff}}) ✓.

**GO stage**: state changes to 'race' when st===4 && stage was 3: handle in onStage: if(st===4){state='race';goAt=t;raceT=0;nextCut=t+4.5;snapNext=true;beep(930,0.5,0.07);lights green; bigShow('GO!','go')}. Note big 'GO!' then remove after 0.9s: keep till first cut? hide via timeout: setTimeout hide 0.85s ✓ but recording restart loops: fine — but setTimeout during reset may hide new big text: guard: hide only if still showing GO: check big.textContent==='GO!' ✓.

Similarly countdown numbers remain until next stage replaces ✓ (each stage sets new text) — after GO, 'GO!' stays until hidden ✓.

Also 'CRESTLINE GP' during stage 0 stays 0.9s then '3' replaces ✓.

**Timers with setTimeout vs loop-state**: acceptable.

**Post big text**: `FINISH · ${name} WINS` cls 'fin' stays until reset (reset sets sm text) ✓.

Now finalize **numbers for cam**: chase distance 7.2, height 3.1, lookahead 4.5, height look +1.3.

Side cam pick code:

```js
function pickSide(lead){
 const c=TSCAMS.map(p=>({p,d:p.distanceTo(lead.pos)})).filter(o=>o.d>13&&o.d<140).sort((a,b)=>a.d-b.d).slice(0,4);
 if(!c.length)return null;return c[(Math.random()*c.length)|0].p;
}
```

**Trackside cam tag names**: 'TRACKSIDE CAM'.

Also **during post**: keep cutting? nextCut logic continues ✓.

**Chase cam when leader changes**: desired jumps; lerp smooths; plus snapNext only on mode transitions ✓ acceptable.

**Snap on race start**: snapNext=true at GO ✓ and after side cam ends ✓.

**HUD clock** during cd shows 0:00.0 ✓ (raceT 0).

**Minimap**: include kart dots colored; leader gets white outline.

**One more check** — buildStrip normals with DoubleSide + Lambert: fine.

**Kerb repeat count**: v tile 3.2 ✓.

**Anisotropy** 8 ✓.

**Sky texture**: gradient vertical; sphere UV: v=1 at top? SphereGeometry v: 0 at bottom? For BackSide gradient flip maybe; visually acceptable either way (top should be blue). Sphere uv v=0 at bottom (phi=π)? In three.js sphere: v goes 0 at top? THREE.SphereGeometry: v = 1 - phi/π? uv.y = 1 - (phiStart...)/... I recall v=0 at top? Actually uv (0,0) at... safer: create gradient with top color at y=0 and horizon at y=h; if inverted, sky looks wrong (dark bottom?). Mitigate: make gradient symmetric-ish? Use radial? Simplest: test can't — instead use a large sphere with vertex-colored gradient? Use ShaderMaterial simple: color mix by normalized world y:

```js
skyMat=new THREE.ShaderMaterial({side:THREE.BackSide,depthWrite:false,uniforms:{},vertexShader:`varying vec3 vW;void main(){vW=(modelMatrix*vec4(position,1.0)).xyz;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,
fragmentShader:`varying vec3 vW;void main(){float h=normalize(vW).y;vec3 top=vec3(0.29,0.58,0.82);vec3 hor=vec3(0.90,0.94,0.93);vec3 c=mix(hor,top,smoothstep(0.0,0.5,h));gl_FragColor=vec4(c,1.0);}`,fog:false? ShaderMaterial ignores fog by default ✓});
```

Clean & correct ✓. Sphere radius 1600, cam far 3000 ✓. Position sphere at scene origin; cam moves ±... radius big enough ✓.

**Fog color** 0xe6f0ea matches horizon ✓.

**Ground disc** radius 1400 y=-3.6 color slightly darker grass (use grassTex repeat 90? big circle uv 0..1 → texture stretched: set map with repeat via uv scale: CircleGeometry uv 0-1 across diameter: set texture.repeat(140,140)?? repeat applies to texture globally (shared with skirt) — conflict. Clone texture for ground with own repeat ✓ (grassTex2=grassTex.clone(); needsUpdate). Simpler: ground uses plain color 0x5d8f45 Lambert ✓ plus skirt handles texture near track ✓.

**Mountains** within fog far: at 650-800, fog far 950: partially fogged ✓ good.

**Balloons** near infield above: y 25-40.

I think we're ready to write. Also remember: NO keyboard; no controls import.

Also add a **subtle sun disc**? skip.

**Post finish slowdown visual**: fine.

**Confetti burst position**: at kart pos +2y.

**Sorting**: Array.prototype.sort stable ✓.

**One risk**: fieldH called ~ (6 karts ×2) + cams + spawn per frame with window 150 step2 = 151 iters → trivial.

**Skirt builder cost**: 701 rows ×5 cols fieldH each 151 iters ≈ 530k ✓ per side ×2 ✓ fine one-time.

**CLEAR computation** 700×700 ≈ 490k ✓.

**getSpacedPoints** fine.

**Trees 150 × fieldH(151)** 23k ✓.

Now write everything. Also final visual: add slight vignette? skip (no gradients).

Let me also make sure **the leading kart's chase camera doesn't clip hills**: camY also clamped ≥ fieldH+1.3 ✓.

Also **camera near plane 0.1** ok.

**Kart scale sanity vs road width 14**: kart 1.7 wide ✓ 6 karts racing side by side OK.

**Speed vs camera**: chase at 50 u/s: motion blur none; fine.

**Countdown duration**: cdT 4.6 → stages: >3.7 intro (0.9s), 3.7-2.8 '3', 2.8-1.9 '2', 1.9-0.95 '1', ≤0.95 GO. ✓ total ~3.7s to GO.

Write final code — carefully now, since I can't run it. Extra care on:

- All variables declared.
- No use of undefined `stage` etc.
- Order of definitions before use in module (function hoisting for function declarations OK).

Let me write the code and simultaneously review line by line.

Regarding `mat()` cache keys: numeric colors ✓.

Board group lookAt: use group.position then group.lookAt(px, group.position.y, pz) — but lookAt makes +z point AT target ✓ plane child faces +z ✓ visible from track ✓.

Trees InstancedMesh with setColorAt before first render & instanceColor.needsUpdate=true ✓.

For instanced meshes with Lambert & instanceColor: material color white base ✓ set leaf material color 0xffffff then setColorAt greens ✓.

Tire stack instanced with colors ✓.

Flags: simple.

Also **start gantry banner text both sides** — texture same both faces (one mirrored) fine.

**Grid staging** — karts visual facing forward ✓.

Let me also handle ** kart.blob scale by hop** skip.

**Now write final code.**

Draft module code fully:

```js
import * as THREE from 'three';

/* ---------- helpers ---------- */
const clamp=(v,a,b)=>v<a?a:v>b?b:v;
const rand=(a,b)=>a+Math.random()*(b-a);
const wrapPI=a=>{a%=Math.PI*2;if(a>Math.PI)a-=Math.PI*2;if(a<-Math.PI)a+=Math.PI*2;return a;};
const damp=(r,dt)=>1-Math.exp(-r*dt);
const _q=new THREE.Quaternion(),_m=new THREE.Matrix4(),_s=new THREE.Vector3(1,1,1),UP=new THREE.Vector3(0,1,0);

const MATC={};const mat=c=>MATC[c]||(MATC[c]=new THREE.MeshLambertMaterial({color:c}));
function makeTex(w,h,fn){const c=document.createElement('canvas');c.width=w;c.height=h;const g=c.getContext('2d');fn(g,w,h);const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=8;return t;}
```

radial tex:

```js
const softTex=makeTex(64,64,(g)=>{const r=g.createRadialGradient(32,32,2,32,32,30);r.addColorStop(0,'rgba(255,255,255,1)');r.addColorStop(0.55,'rgba(255,255,255,.55)');r.addColorStop(1,'rgba(255,255,255,0)');g.fillStyle=r;g.fillRect(0,0,64,64);});
const blobTex=makeTex(64,64,(g)=>{const r=g.createRadialGradient(32,32,4,32,32,30);r.addColorStop(0,'rgba(0,0,0,.8)');r.addColorStop(0.7,'rgba(0,0,0,.45)');r.addColorStop(1,'rgba(0,0,0,0)');g.fillStyle=r;g.fillRect(0,0,64,64);});
```

Track data & arrays (as planned).

Textures: asphalt, grass, kerb, checker, crowd, banner; sign generator.

Geometries: buildStrip, buildSkirt both sides, startline, ground disc, sky.

Scenery: gates, boards, stand, trees, tires, flags, clouds, balloons, mountains.

Particles class-ish object.

Skid pool.

Karts.

HUD.

Cams & state.

Loop.

Also `resize`.

Let me write with care about which variables the tick closure uses.

Also: during 'post', karts keep updating ✓ collide ✓.

Also confetti burst uses spawnP multiple.

Exhaust spawn position: rear center: local (0,0.9?,-1.1): world similar transform w/ yaw: just use rear center (0,-1.1): wx = pos.x + lz*sin(yaw)... lz=-1.1: wx=pos.x-1.1*sin(yaw); wz=pos.z-1.1*cos(yaw) ✓ y=pos.y+0.95.

Wait rotate local (0, -1.1): wx = 0*cos+(-1.1)*sin = -1.1 sinYaw ✓ wz = -0*sin + (-1.1)*cos = -1.1 cosYaw ✓.

OK writing final. For readability I'll include section comments. Final length maybe ~600 lines. Go.

Also double check KARTS grid order index: ROSTER[gi] slowest first ✓.

Wait — one more consideration about **drift visual yaw vs root**: root.rotation.y=this.yaw (nose). body.rotation.y adds drift*slide*0.5 extra → exaggerates angle ✓ total visual slip ≈ slide*(0.55+0.4)... nose relative velocity = slide*0.55 (physical) + body extra 0.35 ≈ 0.5 rad ≈ 29° nice.

Set body extra: this.drift*this.slide*0.5.

**Roll sign**: body.rotation.z = -(this.drift*this.slide*0.5) - this.steerVis*0.1 → lean into corner. For left drift (drift 1): negative z rot: leans left ✓ (checked earlier: rotation.z positive raises left side → negative lowers left = lean left ✓).

**Pitch**: body.rotation.x from accel: accelerating → nose up slightly: aInst>0 → rotation.x negative? rotation.x negative = nose up ✓ so rotation.x = -aSm*k with k>0: -aSm*0.004: a=+15 → -0.06 nose up ✓ braking a=-30 → +0.09 clamp 0.08 nose down ✓.

**Now** consider startup: karts created, resetRace called, loop starts, stage transitions... At first frames idx window: this.idx from reset = round(s/ds)%N ✓.

Also **this.prog** initial: lap=-1, s = s → prog = -L + (L-9-row*5.5) = -(9+row*5.5) ✓.

**Rubber band gap** uses prog differences ✓.

**collide uses prog** ✓ computed prev frame for others ✓ fine.

**One concern**: `this.s` initialization before first update: set in reset ✓ else lap logic spurious: sPrev=this.s ✓.

**Kart.visual when speed 0**: wheels static ✓.

**Countdown camera dolly center**: gridC avg positions computed AFTER reset in resetRace: loop karts sum pos ✓ y avg ✓.

Alright, final code write-out.

Also double-check **buildStrip frustumCulled=false** to avoid disappearing due to bad bounds (computeVertexNormals fine; bounding sphere computed from positions ✓ actually fine, keep culling default true? Large strips have big bounds ✓ ok but safe: set frustumCulled=false for all track pieces ✓ cheap).

Points & skid frustumCulled=false ✓.

**Ground circle** at y=-3.6 radius 1500 centered (5,?,10): CircleGeometry(1500,40) → uv fine no map (plain color) ✓ fog applies ✓.

Fog far 950 < mountains 650 visible hazy ✓ ground beyond fades to fog ✓.

**Camera far 4000** to include sky sphere 1600 ✓ set far 4200.

**Exposure/brightness**: Lambert + hemi 0.95 + dir 2.6 with ACES — should look decent; sky shader unaffected by tonemapping? ShaderMaterial output also tone-mapped? Tone mapping applies to all materials unless material.toneMapped=false. Set skyMat.toneMapped=false to keep exact colors ✓. Similarly blob/soft particle materials keep default (black/white fine).

Let me now also double check **checkTex uv orientation**: quad rows i0→i1 along track: v 0→1 over 2 rows ✓ squares 20px: canvas 200×40 = 10×2 ✓ across u ✓.

**crowd tex on BoxGeometry**: map applies all faces; front/back faces show dots pattern stretched — acceptable.

Time to output. I'll write the complete HTML now carefully, keeping code tight but complete. During writing, track brackets carefully.

Also—board title "RUNNING ORDER"; gap formatting: leader 'LEADER' others '+x.xs'; finished 'FIN'.

Also add rank numbers 1-6 with leader accent ✓.

Edge: gap when other finished but leader not? finished karts rank above by key ✓ gap vs leader (standings[0]) ✓ fine.

Write clock as raceT frozen after finish: finalT set → display finalT ✓.

fmt(finalT!==null?finalT:raceT).

**Lap counter during post**: 'FINISH' ✓.

Let me handle onStage details:

```js
function onStage(st,t){
 if(st===0){bigShow('CRESTLINE GP','sm');beep(420,.1,.04);}
 else if(st>=1&&st<=3){bigShow(String(4-st),'');setLights(4-st===3?1:4-st===2?2:3); hmm mapping: st1→'3'→1 light; st2→'2'→2; st3→'1'→3 ✓ setLights(st); beep(600,.14,.05);}
 else{bigShow('GO!','go');setLightsGo();beep(940,.5,.07);state='race';goAt=t;raceT=0;nextCut=t+4.5;snapNext=true;}
}
```

setLights(n): mats colors: i<n → red bright else dark. setLightsGo: all green. After 1.2s of race: lightsDark (flag check in tick).

**tick skeleton**:

```js
let tp=performance.now()/1000;
renderer.setAnimationLoop(()=>{
 const t=performance.now()/1000;const dt=clamp(t-tp,0.001,0.05);tp=t;
 if(state==='cd'){
   cdT-=dt;const st=cdT>3.7?0:cdT>2.8?1:cdT>1.9?2:cdT>0.95?3:4;
   if(st!==stage){stage=st;onStage(st,t);}
 }else if(state==='race'||state==='post'){
   raceT+=dt;
   leadProg=-1e9;karts.forEach(k=>leadProg=Math.max(leadProg,k.prog));
   karts.forEach(k=>k.update(dt,t));
   collide();
   if(state==='post'){postT+=dt;if(postT>5.4)resetRace();}
 }
 karts.forEach(k=>k.visual(dt,t));
 standings=karts.slice().sort((a,b)=>keyK(b)-keyK(a));
 // lights off after go
 if(goT!==0&&t>goT+1.25&&lightsLit){setLights(0);lightsLit=false;}
 hmm manage.
 hudT logic...
 cams(dt,t);
 dust.update(dt);
 drawMap();
 renderer.render(scene,cam);
});
```

Simplify lights: in onStage(4) set lightsLit=true, goTime=t; in tick if(lightsLit && t-goAt>1.2){setLights(0);lightsLit=false}.

postT increment: inside race/post branch I wrote raceT+=dt for both ✓ postT handled: if(state==='post')postT+=dt.

onFinish(k): if(state==='race'){state='post';postT=0;finalT=raceT;confetti(k);bigShow(`FINISH · ${k.name} WINS`,'fin');} Also k.lap may exceed LAPS later (keeps driving) — each crossing calls onFinish but guarded by state!=='race' → skip ✓ but kart.finished set in update before calling ✓.

Wait: update sets finished & finT then calls onFinish once (guard !finished before). ✓

**resetRace()**:

```js
function resetRace(){
 dust.clear();skidClear();
 karts.forEach((k,i)=>k.reset(i));
 gridC.set(0,0,0);karts.forEach(k=>gridC.add(k.pos));gridC.multiplyScalar(1/6);gridC.y+=0;
 stage=-1;cdT=4.6;state='cd';raceT=0;finalT=null;postT=0;nextCut=1e9;sideCam=null;sideUntil=0;snapNext=true;lightsLit=false;setLights(0);
 bigShow('CRESTLINE GP','sm');
 cam.fov=52;cam.updateProjectionMatrix();
}
```

gridC y: avg of pos.y ✓.

**cams(dt,t)** implement fully:

```js
function cams(dt,t){
 let fovT=55;
 if(state==='cd'){
  const u=clamp((4.6-cdT)/3.65,0,1);
  const ang=-2.2+u*1.25, rad=16.5-u*4.5;
  cam.position.set(gridC.x+Math.sin(ang)*rad,gridC.y+4.8-u*1.6,gridC.z+Math.cos(ang)*rad);
  cam.lookAt(gridC.x,gridC.y+1.0,gridC.z);
  camTag.textContent='GRID CAM';fovT=48;
 }else{
  const lead=standings[0];
  if(sideCam&&t<sideUntil){
   cam.position.copy(sideCam);
   _v1.set(lead.pos.x,lead.pos.y+1.1,lead.pos.z);
   cam.lookAt(_v1);
   const d=_v1.distanceTo(cam.position);
   fovT=clamp(2600/Math.max(d,10),26,55);
   camTag.textContent='TRACKSIDE CAM';
  }else{
   if(sideCam){sideCam=null;nextCut=t+6.5+Math.random()*3.5;snapNext=true;}
   if(t>nextCut){const c=pickCam(lead);if(c){sideCam=c;sideUntil=t+2.9;}}
   if(!sideCam){
    const fy=lead.yaw;const sx=Math.sin(fy),cz=Math.cos(fy);
    // forward and right vectors
    const fx=sx,fz=cz,rx=-cz,rz=sx;
```

Wait right vector: right = (-fwd.z,0,fwd.x)? Earlier: for fwd=(0,0,1) right=(-1,0,0): (-fz,0,fx) = (-1,0,0) ✓. So rx=-cos? fwd=(sin,0,cos): right=(-cos? -fwd.z = -cos(fy)... hold on fwd.z=cos(fy); right=(-fwd.z,0,fwd.x)=(-cos fy, 0, sin fy). Hmm but earlier I derived for heading +x (yaw π/2): fwd=(1,0,0); right=(0,0,1) ✓ formula: (-0? -fwd.z=0, fwd.x=1 → (0,0,1) ✓ +z is right for +x heading ✓ matches earlier ✓.

```
    const lat=lead.drift*lead.slide*4.2;
    _v1.set(lead.pos.x-fx*(6.9+lead.speed*0.055)+rx*lat, lead.pos.y+3.0+lead.speed*0.012, lead.pos.z-fz*...+rz*lat);
```

careful: desired = pos - fwd*dist + up*h + right*lat:

```
    _v1.set(lead.pos.x - fx*D + rx*lat, lead.pos.y + H, lead.pos.z - fz*D + rz*lat);
```

where fx=sin(fy), fz=cos(fy); rx=-fz? right=(-fwd.z,0,fwd.x) → rx=-fz, rz=fx ✓.

```
    if(snapNext){camPosS.copy(_v1);lookS.set(lead.pos.x,lead.pos.y+1.2,lead.pos.z);snapNext=false;}
    camPosS.lerp(_v1,damp(4.2,dt));
    const minY=fieldH(camPosS.x,camPosS.z,lead.idx)+1.25;
    if(camPosS.y<minY)camPosS.y=minY;
    cam.position.copy(camPosS);
    _v2.set(lead.pos.x+fx*4.5,lead.pos.y+1.35,lead.pos.z+fz*4.5);
    lookS.lerp(_v2,damp(10,dt));
    cam.lookAt(lookS);
    fovT=54+lead.speed*0.14;
    const rank=1;camTag.textContent=`CHASE · P1 ${lead.name}`;
   }
  }
 }
 cam.fov+=(fovT-cam.fov)*damp(4,dt);cam.updateProjectionMatrix();
}
```

pickCam: sorted by dist take 4, random ✓ also require dist>14.

While sideCam active, also update sideCam look each frame ✓ done above.

**hud()**:

```js
let hudAcc=0;
function hud(dt){hudAcc-=dt;if(hudAcc>0)return;hudAcc=0.24;
 const lead=standings[0];
 standings.forEach((k,ix)=>{const el=rowEls[k.gi];el.style.order=ix;el.classList.toggle('ld',ix===0);
  el.children[0].textContent=ix+1;
  el.children[3].textContent= ix===0?'—':(k.finished?'FIN':'+'+Math.max(0,(lead.prog-k.prog)/Math.max(k.speed,8)).toFixed(1));
 });
 lapEl.textContent= state==='post'?'FINISH':`LAP ${clamp(lead.lap+1,1,LAPS)}/${LAPS}`;
 clockEl.textContent=fmt(finalT!==null?finalT:raceT);
}
```

leader gap '—'.

**drawMap**:

```js
function drawMap(){mg.clearRect(0,0,168,168);
 mg.lineJoin='round';mg.lineCap='round';
 mg.strokeStyle='#262a31';mg.lineWidth=10;mg.stroke(mPath);
 mg.strokeStyle='#454b54';mg.lineWidth=5;mg.stroke(mPath);
 // start tick
 mg.strokeStyle='#ff4f20';mg.lineWidth=3;mg.beginPath();mg.moveTo(sxA,syA);mg.lineTo(sxB,syB);mg.stroke();
 for(let i=standings.length-1;i>=0;i--){const k=standings[i];const [x,y]=m2(k.pos.x,k.pos.z);
  if(i===0){mg.fillStyle='#fff';mg.beginPath();mg.arc(x,y,5.4,0,7);mg.fill();}
  mg.fillStyle=k.cfg.css;mg.beginPath();mg.arc(x,y,i===0?4:3.4,0,7);mg.fill();
  mg.strokeStyle='rgba(0,0,0,.55)';mg.lineWidth=1;mg.stroke();}
}
```

arc end angle 7 > 2π fine.

m2 mapping & bounds computed once.

**Particles**:

```js
const dust={...} implement with arrays & update.
```

Write it:

```js
const PN=560;
const pGeo=new THREE.BufferGeometry();
const pPos=new Float32Array(PN*3),pSize=new Float32Array(PN),pAlp=new Float32Array(PN),pCol=new Float32Array(PN*3);
pPos.fill(-999);? set y -50: init loop set y -999.
pGeo.setAttribute('position',new THREE.BufferAttribute(pPos,3).setUsage(THREE.DynamicDrawUsage));
... aSize aAlp aCol
const pVel=new Float32Array(PN*3),pLife=new Float32Array(PN),pMaxL=new Float32Array(PN),pGrav=new Float32Array(PN),pS0=new Float32Array(PN),pA0=new Float32Array(PN),pDr=new Float32Array(PN);
let pH=0;
const pts=new THREE.Points(pGeo,pMat);pts.frustumCulled=false;scene.add(pts);
function spawnP(x,y,z,vx,vy,vz,life,size,r,g,b,al,grav,drag){
 const i=pH;pH=(pH+1)%PN;
 pPos[i*3]=x;pPos[i*3+1]=y;pPos[i*3+2]=z;
 pVel[i*3]=vx;pVel[i*3+1]=vy;pVel[i*3+2]=vz;
 pLife[i]=pMaxL[i]=life;pSize[i]=size;pDr[i]=size;
 pCol... pAlp[i]=al? store base alpha in pA0 — need array: const pA0=...; pGrav.
}
function updateDust(dt){
 for(let i=0;i<PN;i++){
  if(pLife[i]<=0){pAlp[i]=0;continue;}
  pLife[i]-=dt;const t=1-pLife[i]/pMaxL[i];
  const dr=Math.max(0,1-2.6*dt);
  pVel[i*3]*=dr;pVel[i*3+2]*=dr;pVel[i*3+1]=pVel[i*3+1]*dr+ (pGrav[i])*dt;
  pPos[i*3]+=pVel[i*3]*dt;pPos[i*3+1]+=pVel[i*3+1]*dt;pPos[i*3+2]+=pVel[i*3+2]*dt;
  pSize[i]=pDr[i]*(1+2.4*t);
  pAlp[i]=pA0[i]*(1-t)*(t<0.15?t/0.15:1);
 }
 attrs needsUpdate=true;
}
```

pA0 array ✓ add.

Dust spawn helpers:

```js
function dustPuff(x,y,z,vx,vy,vz,scale,col){spawnP(...)}
```

I'll inline in kart.

Confetti:

```js
function confetti(k){for(let i=0;i<110;i++){const c=ROSTER[i%6];const col=new THREE.Color(c.c);... spawn at k.pos + rand, vel rand sphere*4 + up rand 5..9, grav -9, life 1.2-1.8, size 0.3-0.45, alpha .9}}
```

new THREE.Color per confetto — fine one-time.

Dust color arrays: pass r,g,b floats.

Kart dust colors: road skid: (0.74,0.70,0.63); kerb: (0.8,0.55,0.45)?; grass: (0.42,0.56,0.30). choose by |lat|.

**Skid pool**:

```js
const SKN=800;
const skGeo=new THREE.PlaneGeometry(0.32,1.6);skGeo.rotateX(-Math.PI/2);
const skMat=new THREE.MeshBasicMaterial({color:0x0c0d10,transparent:true,opacity:0.4,depthWrite:false});
const skMesh=new THREE.InstancedMesh(skGeo,skMat,SKN);skMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);skMesh.frustumCulled=false;skMesh.renderOrder=4;
let skH=0;const _zero=new THREE.Matrix4().makeScale(0,0,0);
for(let i=0;i<SKN;i++)skMesh.setMatrixAt(i,_zero);
function skidClear(){for(let i=0;i<SKN;i++)skMesh.setMatrixAt(i,_zero);skMesh.instanceMatrix.needsUpdate=true;skH=0;}
function addSkid(x,y,z,yaw){_q.setFromAxisAngle(UP,yaw);_m4.compose(_v1.set(x,y,z),_q,_s.set(1,1,1));skMesh.setMatrixAt(skH,_m4? compose into _m4 then set);skH=(skH+1)%SKN;skMesh.instanceMatrix.needsUpdate=true;}
```

Plane rotated flat: PlaneGeometry in XY; rotateX(-π/2): Y→? plane normal +z → after rotX(-90): normal +y? Rotating about X by -90°: +y→+z? R_x(-90): y→ -z? Let me: rotation about x by angle a: y' = y cos a - z sin a; z' = y sin a + z cos a. a=-90: cos0 sin=-1: y'=0*y? For point (0,1,0): y'=cos(-90)*1 - sin(-90)*0 = 0; z' = sin(-90)*1 + cos*0 = -1 → normal (0,0,-1) points down; the face normal -z; with DoubleSide fine (set side DoubleSide) ✓; geometry height along Y originally → after rotate lies along Z ✓ length axis z ✓ width x ✓.

Material side: set DoubleSide to be safe.

**Kart update dust & skid spawn** (in update end):

```js
if(this.drift!==0||this.grassDust){
 this.dustAcc+=dt*52;
 while(this.dustAcc>=1){this.dustAcc-=1;
  const side=Math.random()<0.5?0.8:-0.8;
  const lx=side,lz=-0.84;
  const wx=this.pos.x+lx*Math.cos(this.yaw)+lz*Math.sin(this.yaw);
  const wz=this.pos.z-lx*Math.sin(this.yaw)+lz*Math.cos(this.yaw);
  const gr=Math.abs(this.lat)>8.6;
  const r=gr?0.42+Math.random()*0.1:0.72+Math.random()*0.1;
  const g2=gr?0.55:0.67,b=gr?0.3:0.6;
  spawnP(wx,this.gy+0.12,wz, Math.sin(this.my)*this.speed*0.25+rand(-0.9,0.9), rand(0.8,2.0), Math.cos(this.my)*this.speed*0.25+rand(-0.9,0.9), rand(0.5,0.95), rand(0.55,1.15), r,g,b, gr?0.6:0.5, 0.6);
 }
 this.skT-=dt;
 if(this.skT<=0){this.skT=0.028;
  for(const lx of [0.8,-0.8]){const lz=-0.84;
   const wx=this.pos.x+lx*Math.cos(this.yaw)+lz*Math.sin(this.yaw);
   const wz=this.pos.z-lx*Math.sin(this.yaw)+lz*Math.cos(this.yaw);
   addSkid(wx,this.gy+0.025,wz,this.my);}
 }
}else{this.dustAcc=0;}
```

my stored ✓ (this.my=my).

**Exhaust during cd** in tick:

```js
if(state==='cd')karts.forEach(k=>{k.exT-=dt;if(k.exT<=0){k.exT=0.16+Math.random()*0.12;
 const wx=k.pos.x-1.15*Math.sin(k.yaw),wz=k.pos.z-1.15*Math.cos(k.yaw);
 spawnP(wx,k.pos.y+0.95,wz,rand(-0.3,0.3),rand(0.5,1.1),rand(-0.3,0.3)+Math.cos(k.yaw)*0.3? just up, rand(0.5,0.8),rand(0.28,0.42),0.62,0.62,0.64,0.5,0.35);}});
```

Also exhaust during race occasionally? skip.

**onFinish**:

```js
function onFinish(k){if(state!=='race')return;state='post';postT=0;finalT=raceT;
 bigShow(`FINISH · ${k.name} WINS`,'fin');
 for(let i=0;i<130;i++){const c=ROSTER[(Math.random()*6)|0];const col=new THREE.Color(c.c);
  spawnP(k.pos.x+rand(-2,2),k.pos.y+rand(1,3),k.pos.z+rand(-2,2),rand(-4,4),rand(4,9),rand(-4,4),rand(1.2,2),rand(0.28,0.5),col.r,col.g,col.b,0.95,-9);}}
```

**Standings key**: finished by finT asc: key = finished? 1e6 - finT : prog. (higher better; finished earlier → larger 1e6-finT ✓).

**reset kart**: also reset finished, finT, drift, slide, hop, skT, dustAcc, exT, ot, otLane, steerVis, laneCur=lat ✓ root rotation reset via visual ✓.

Now **collide**:

```js
function collide(){
 for(let a=0;a<6;a++)for(let b=a+1;b<6;b++){const A=karts[a],Bk=karts[b];
  const dx=Bk.pos.x-A.pos.x,dz=Bk.pos.z-A.pos.z;const d2=dx*dx+dz*dz;
  if(d2<3.24&&d2>1e-4){const d=Math.sqrt(d2),nx=dx/d,nz=dz/d,ov=(1.8-Math.sqrt(d2))*0.5;
   A.pos.x-=nx*ov;A.pos.z-=nz... careful nz: n from A→B is (nx,nz): A pushed -n, Bk +n:
   A.pos.x-=nx*ov*1.05;A.pos.z-=nz*ov*1.05;Bk.pos.x+=nx*ov*1.05;Bk.pos.z+=nz*ov*1.05;
   if(A.prog>Bk.prog){Bk.speed=Math.min(Bk.speed,A.speed+1.0);}else{A.speed=Math.min(A.speed,Bk.speed+1.0);}
  }}}
```

r=1.8 → d2<3.24 ✓.

**pickCam**:

```js
function pickCam(lead){const arr=[];for(const c of TSCAMS){const d=c.distanceTo(lead.pos);if(d>13&&d<140)arr.push({c,d});}
 if(!arr.length)return null;arr.sort((x,y)=>x.d-y.d);return arr[Math.min(arr.length-1,(Math.random()*Math.min(4,arr.length))|0)].c;}
```

**Map setup**:

```js
let minx=1e9,maxx=-1e9,minz=1e9,maxz=-1e9;
P.forEach(p=>{minx=Math.min(minx,p.x);...});
const mcx=(minx+maxx)/2,mcz=(minz+maxz)/2;
const ms=Math.min(150/(maxx-minx),150/(maxz-minz));
const m2=(x,z)=>[(x-mcx)*ms+84,(z-mcz)*ms+84];
const mPath=new Path2D();
P.forEach((p,i)=>{const[x,y]=m2(p.x,p.z);i?mPath.lineTo(x,y):mPath.moveTo(x,y);});mPath.closePath();
const st0=m2(P[0].x+SD[0].x*9,P[0].z+SD[0].z*9),st1=m2(P[0].x-SD[0].x*9,P[0].z-SD[0].z*9);
```

canvas 168 css; backing 336 with setTransform(2,2) — set once: mg.setTransform(2,0,0,2,0,0) ✓ then clearRect(0,0,168,168) each frame ✓.

**Trees build**:

```js
const treeList=[];
let guard=0;
while(treeList.length<150&&guard++<800){
 const i=(Math.random()*N)|0,side=Math.random()<0.5?1:-1;
 const off=10+Math.random()*Math.random()*44;
 if(off>CLEAR[i]*0.48-2)continue;
 if(i>N-70&&side<0)continue; // grandstand side? stand outside = -sd at start straight... side<0 means lat negative = outside there ✓ skip zone idx in [N-90,N-5] & side -1.
 const x=P[i].x+SD[i].x*off*side,z=P[i].z+SD[i].z*off*side;
 treeList.push({x,z,y:fieldH(x,z,i)-0.15,s:rand(0.75,1.7),r:Math.random()*6.28,pine:Math.random()<0.6});
}
```

Hmm outside at start straight: sd=(cosθ...) with heading +x: sd=(Tz,0,-Tx)≈(0.03,0,-1) → sd points -z = interior? interior z smaller ✓ so outside = -sd direction = lat negative ✓ side<0 is outside ✓ skip stand zone i∈[N-95, N+10] & side<0 ✓ (also gantry area fine trees ok).

Instanced:

```js
const trunkI=new THREE.InstancedMesh(trunkGeo,mat(0x6e4f36),treeList.length);
const pineI=new THREE.InstancedMesh(coneGeo,new THREE.MeshLambertMaterial({color:0xffffff}),nPine);
const oakI=... nOak;
fill matrices with compose; setColorAt: pine: Color().setHSL(0.33+rand(-0.03,0.04),0.42,0.26+rand(0.08)); oak: setHSL(0.27,0.45,0.3).
```

Trunk no per-color.

Also small bushes? skip.

**Tires**: gather runs:

```js
const tireList=[];
{let run=0;for(let i=0;i<=N;i++){const hot=i<N&&Math.abs(KSm[i])>0.042;if(hot)run++;else{if(run>12){const mid=(i-run+ (run>>1))... place along run: for(let j=i-run;j<i;j+=3){...}} run=0;}}}
```

step 3 samples ≈2 units: n up to run/3; cap total 240 (if exceed, skip extra). Place: lat=-Math.sign(KS[j])*(HALF+2.6): y=fieldH+0.3. Also second layer offset every other: y+0.62 for every 3rd.

Use one InstancedMesh count tireList.length with per-instance color.

**Flags**: 10 poles: outside & inside mix; flag mesh: PlaneGeometry(1.3,0.8) DoubleSide colored per roster; pole cylinder 0.05×2.6 gray; store flag meshes for waving (rotate around pole: geometry translate(0.7,0,0) so rotation.y swings it around pole ✓).

Flag positions idx: (N-88+k*8)%N side alternate ±(HALF+2.6).

**Clouds**: 7 groups: sphere geo shared; group of 3 meshes scaled; material Lambert white emissive? Lambert lit — clouds white-ish: use MeshLambertMaterial({color:0xffffff, emissive:0x9fb2c0? no—keep simple Lambert white with high hemi; fine. fog:true default → distant clouds hazy ✓. positions radius 250-480 angle rand, y 45-75, scale rand 4-9. Store for drift: cloud.position.x += dt*1.2 wrap.

**Balloons**: 2: sphere r4 (segments 12) color accent & teal + basket small box + ropes skip; positions over infield (mcx±30), y 26-34; bob.

**Mountains**: 15 cones radius 90-160 height 70-160 at ring 600-800 → with fog. Color 0x7d92a8 & 0x8fa3b6 alternate; Lambert.

Alright — also add slight **kerb bumps**: when |lat| in (HALF-0.6, 8.6): body jitter small: add to jit: kerb? include in visual: if(!grass && Math.abs(this.lat)>HALF-0.5) jit+=Math.sin(t*43+this.gi)*0.02 ✓ nice detail.

**Sound**: none required.

Now, finally — **verify timing** lap length: L≈? curve length: control polygon 539*0.9≈485; centripetal catmull length maybe ~470. avg speed: let's estimate segments: straights (start straight ~95 units at 50+), sweeper ~0.02 → v=sqrt(38/0.02... let me just trust ~40-44 avg → lap 10.7-11.7s ✓.

**LAPS=3** ✓.

Also **countdown karts rev wheel? static** ✓.

One more important thing: **the leader chase camera at race start**: leader initially whoever; at GO all prog ≈ equal; standings[0] arbitrary but stable-ish; fine.

**Cleanup of lookAt with order**: cam.rotation default order XYZ; lookAt handles ✓.

Potential z-fighting: road vs kerb share edge at ±7 exactly with kerb lifted ✓; skirt at 8.4 vs kerb outer 8.4 lifted 0.02 ✓ tiny gap vertical 0.02-0.07 ok.

Start line at samples 1..7 lift 0.035 above road ✓.

Skid marks at gy+0.025 — above road (road exactly gy) ✓ but on slopes the quad is horizontal while road tilts → edges may dip under on slopes: slope ~ up to 8% over 0.8-length quad → height diff 0.32*0.08=0.026 ≈ lift → borderline; increase skid y offset to gy+0.04 and it's fine (blob at 0.03? blob above skid? blob at +0.05? Let me set: skid +0.045, blob +0.07. Blob must be above skid to composite: both transparent; blob renderOrder 6 > skid 5 with depthWrite false both — draw order by renderOrder then depth test against opaque road only (skid/blob don't write depth) ✓ blob visible over skid ✓.

Particles renderOrder 7 ✓ depthTest true ✓.

**HTML ids**: big, lap, clock, map, camtag, rows, board, sub.

Also I referenced `q` helpers—just use children indexes ✓.

**Roster css**: '#'+hex.

Let me also give karts slight **scale variety**? no.

**Names on board**: yes.

Now — I also want a subtle **speed sense**: chase FOV grows w/ speed ✓.

Also **kart shadows** blob opacity constant ✓.

**Final check on the AI lane sign with actual track direction**: our loop travel direction: P0(0,66.6) → P1(52.2,66.6) → ... toward P2 (86.4,52.2): from +x heading, next segment direction (34,-14.4)*? Wait cps scaled: RAW[2]=[96,2,58]→(86.4,2.4,52.2): P1→P2 dir=(33.9, ?, -14.4): turning toward -z = LEFT (established: heading +x, left = -z ✓). So the first corner is LEFT → k>0 → apex lane positive = +SD = left ✓ karts hug left apex ✓ correct.

The S after: P5(54,10.8,-18)→P6(25.2,9.6,-9)→P7(7.2,10.8,-30.6): segment dirs: P5→P6 (-28.8,+9), P6→P7 (-18,-21.6): first left? dir1 angle: atan2(dx,dz)=atan2(-28.8,9): heading ~ -72.6°(west-north?) whatever sign flips → k<0 right turn then k>0 ✓ S ✓.

**Hill crest airtime**: karts glued to ground (pos.y set) ✓ no jump physics; pitch follows ✓ fine.

Now write everything out — FINAL. I'll produce the HTML with the complete script. Watch syntax carefully (no stray backticks; template literals used a few places ✓).

Also — `const q=(sel)=>document.querySelector(sel)` shortcuts.

Let me also pre-verify `buildStrip` usage for kerbs on right side: buildStrip(-7,-8.4,0.07,0.02,...) ✓ uv fine.

Let me also decide **standings initial** before first sort: initialize standings=karts.slice() ✓.

**goAt unused?** used for... nothing else; drop.

**One risk**: at reset, karts placed at idx round((L-9-row*5.5)/ds) — negative? L-19 >0 ✓.

**FieldH window for skirt ±150 step2**: at pinch, vertex near other leg: nearest j might be within window ✓ (pinch legs index distance: chicane legs P6-ish idx vs P8 idx: separated by ~ (RAW idx3→7) ~ 3-4 segments ≈ 4/14*700 = 200 samples > 150? Hmm pinch between segment P6-P7 and P8-P9: index gap maybe ~150-250 samples. If window misses the truly-nearest leg... fieldH used for SKIRT VERTICES with gi = own row index: vertex at off ≤ 13 in pinch (wmax small): its true nearest is own row (distance ~8-13) vs other leg (~24+) → own ✓ fine even if window clipped. For far-offset vertices (clearance large, no pinch) own row nearest ✓. So window ±150 fine for skirt verts. For karts (near road) own ✓. For trees off ≤ 52 with CLEAR check ✓ own-ish fine — worst case slight height mismatch invisible under trees.

Wait, but there's a subtle issue: skirt vertex height uses fieldH(x,z,gi) which computes nearest distance d from the vertex to centerline — for a vertex at off=13 in a pinch area where the OTHER leg is closer (d_other < 13)? Possible if legs within 26 units: min pinch distance ~36*0.9=32 → d_other ≥ 18 > own off (≤ wmax ≈ 13) ✓ own nearest ✓ consistent.

But the FLATness: w=skirtW(own off) uses own base P[gi].y ✓ matches road ✓.

And the gap between facing skirt edges (~1.8 units): both edges at w≈skirtW(≈12.9)≈0.87 → heights ≈ 0.87*base + 0.13*ground: bases of two legs differ (e.g., 9.6 vs 8.4): heights differ by ~1 → tiny cliff in the 1.8-gap seam → looks like a small trench ✓ acceptable.

Hmm wait, actually that's wrong: wmax = CLEAR*0.5-0.9 where CLEAR≈36 → wmax≈17: at off=17, d=17 → skirtW(17)≈ between 12(0.86) and 18(0.6): ≈0.88? SK_OFF table: [8.4→1,12→0.85,18→0.6,28→0.38,45→0.18,70→0.06,115→0]. At 17: ~0.63?? interp 12→18: (17-12)/6=0.83 → 0.86-0.83*0.26≈0.65. So facing edges each at w≈0.65 → heights 0.65*base+0.35*ground → diff (bases say 9.6 vs 7.2?) At chicane legs bases: P6 y=9.6, P8 area y ~ 8*1.2=9.6 similar → fine ✓.

OK good enough. These seams are far from cameras mostly.

Also the **inner skirt cap**: wmax min 13 → inner skirt at least 13 wide both sides → in pinch total 2*17+gap... fine.

**Big remaining risk**: none structural. Write it.

Also don't forget **`#rows{display:flex;flex-direction:column}`** and row children spans widths.

Also font sizes ok.

Let me also add a tiny **"position change" flash**: skip.

Alright, compose the final file. I'll also add `user-select:none`.

Also last flourish: **sub caption** & title branding consistent "CRESTLINE GP".

Also **document title** ✓.

Counting renderer clear color: sky sphere covers ✓.

**Write final code now** — being extra careful with:
- All variables declared (strict module).
- Using `_v1,_v2,_q,_m4` temps without conflicts (careful in addSkid where _v1 used by caller too — use dedicated temps in skid: `_sv`).

Let me write.

```js
/* ======================= SCENE ======================= */
const renderer=new THREE.WebGLRenderer({antialias:true});
...
```

I'll now write the entire final answer. During writing, double-check every formula sign one more time (esp. wheel world offset, rotations).

Wheel world pos formula check: rotation.y=yaw: world = R_y(yaw)·local. R_y(θ): x'=x cosθ + z sinθ; z' = −x sinθ + z cosθ. For yaw=0 (facing +z): local rear-left (−0.8, −0.84) → world (−0.84? x'=−0.8*1+(−0.84)*0=−0.8 ✓ z'=−(−0.8)*0+(−0.84)=−0.84 ✓.

For yaw=π/2 (facing +x): local front (0,+1): x'=0*0+... x'=0*0+1*1? cos(π/2)=0,sin=1: x'=x*0+z*1 = z → front z0.86→x'=0.86 ✓ z'=−x*1+z*0=−x → local left x+0.8 → world z −0.8: facing +x, left = −z ✓.

Move: pos += (sin(my), cos(my))*v ✓ matches forward=(sinYaw,0,cosYaw) ✓ consistent with yaw=atan2(Tx,Tz) ✓.

Slope pitch sign recheck: rotation.x applied after yaw (order YXZ: yaw then pitch in local frame): local forward +z; pitch about local x by θ: +z rotates toward −y for positive θ? R_x(θ): z-axis → (0, sinθ? For vector (0,0,1): y' = −sinθ? R_x(θ): y'=y cosθ − z sinθ = −sinθ; z'=y sinθ + z cosθ = cosθ. So positive θ tips forward-down (nose down). Climbing needs nose up → θ negative ✓ rotation.x = −asin(T.y) with T.y>0 climbing → negative ✓ nose up ✓.

Drift yaw boost: this.yaw += drift*0.9*dt*spd factor — drift=+1 left turn: yaw increases = turn left ✓.

moveYaw = yaw − drift*slide*0.55: left drift: velocity yaw less than heading (heading more left) ✓.

Overtake inside pick: ins = sign of KS ahead: KS>0 left turn → inside is left = +lat ✓ want = o.lat + s*2.7 with s=+1 ✓.

Kerb zone boundaries: road edge HALF=7; kerb region |lat|∈(6.6? define: road if |lat|<7.6; kerb 7.6-8.6; grass >8.6. Kerb bump jit when 7.4<|lat|<8.7 ✓ minor.

Grass slowdown 0.4× — harsh; use 0.45 & extra wobble ✓. Also add slight random yaw wiggle on grass? skip.

**vA grass** = maxSpeed*0.4 → braking from 50 to 20 quick via brake ✓ dust ✓.

**Kerb speed** 0.985 ✓.

Also ensure **drift requires onRoad**: !grass ✓.

**Steering while grass**: still steers ✓ recovery ✓.

Final: **kart headers position on minimap** ✓.

**One more**: big overlay during post shows winner; after reset shows CRESTLINE GP ✓.

**HUD initial**: rows exist; lap 'LAP 1/3'; clock 0:00.0 ✓.

Also **spawn dust on hard braking** (speed drop > 8/s & onRoad): adds life: implement: if(this.brakeVis>threshold) small gray puffs at front wheels? skip — drift dust suffices.

I think we're ready. Also **ensure no emoji** anywhere ✓; icons none needed ✓.

Also the **sub line** bottom: fine.

Let me also double check **CatmullRom centripetal closed** — curve.getSpacedPoints uses arc lengths ✓.

**One numerical check for skirt verts count**: (N+1)*5*2 = 7010 verts ✓ indices 700*4*2*3? fine.

**drawMap standings reversed draw** ✓.

**rowEls order property**: container flex column with order ✓ initial order = gi set once.

**HUD leader gap min width** ok.

**Check KS threshold for lane gain 110**: max |KS| ~0.05 → 5.5 clamp 5.4 ✓ gentle corners 0.01 → 1.1 ✓.

**Speed cap while overtaking**: implemented via rear speed cap in collide ✓ plus ot lane dodge ✓.

Now write final answer. Also mention brief explanation after the code block per instructions ("include a brief text explanation after the code").

Also careful: `standings` used before first sort in cams when state==='cd' → initialized at startup as karts.slice() ✓.

`leadProg` init -1e9 each frame before updates ✓ used in update via closure ✓.

Also within kart.update I use `raceT` (for drift timing? no) and `t` param ✓.

Also I should double check the **visual() pitch when T[i].y**: T normalized? T computed as difference then normalized? I normalize: T[i].normalize() ✓ then T.y is sin(slope) ✓ asin fine.

Let me also handle **`K` smoothing arrays** defined before scenery uses fieldH? fieldH doesn't use K ✓.

**CLEAR** used by trees & skirt ✓ compute before.

Order in file: constants → track arrays → fieldH/skirtW → textures/materials → geometry builders + add to scene → clearance → skirt (needs CLEAR) → props → particles → skids → karts → HUD → cams → state → loop.

CLEAR compute before skirt ✓.

Now writing the deliverable. (Finally!) I'll keep it tidy.

One more consideration on performance of `fieldH` inside skirt builder: 701 rows ×5 cols ×2 sides = 7010 calls × 151 iter = 1.06M — fine.

Also CLEAR O(N²/2) with wrap skip — 245k pairs ✓.

Let me also make sure I DON'T call getSpacedPoints twice etc.

Writing the code now — final.

Ah, one more: **`buildStrip`** UV v uses vt computed from tile: v=i*ds/vt where vt=L/round(L/tile) → v spans 0..round(L/tile) integer at seam ✓ repeat wraps ✓.

**roadTex repeat**: texture repeats via v coordinate ✓ wrap set ✓.

**kerb u**: across 1.4 wide: kerbTex 32×64 drawn red top half → v tiles → stripes along track ✓ u maps whole texture across 1.4 width ✓ fine.

**crowd tex repeat**: set tex.repeat.set(8,1) & wrapS repeat ✓ (crowd only on stand boxes).

Now — write!

Also: **`renderer.outputColorSpace`** default SRGB ✓ fine.

**Hemi ground color** greenish ✓.

Final code:

(Also add gentle idle engine bob for karts during countdown via jit ✓ done.)

Also add **`scene.background`** fallback = new Color(0xdfeee9) (in case sky sphere edge) ✓.

Countdown numbers also show lights ✓.

Double-check `bigShow` re-trigger:

```js
function bigShow(txt,cls){big.textContent=txt;big.className='on'+(cls?' '+cls:'');void big.offsetWidth;big.classList.add('pop');}
```

✓ css #big base display none; .on display block ✓.

GO hide: setTimeout(()=>{if(big.textContent==='GO!')big.classList.remove('on');},900).

**Karts cast blob shadow scale**: skip.

Also add slight **sun disc**: skip.

OK — compose final answer now. I'll write ~650 lines carefully.

One more subtle: **`visual()`** uses T[this.idx].y — T normalized ✓ asin fine.

And **`this.gy`** set in update before visual; during cd, kart.update not called → gy from reset ✓ (set this.gy=pos.y in reset) ✓.

**spawnP signature**: (x,y,z,vx,vy,vz,life,size,r,g,b,alpha,grav).

Also **updateDust alpha attr** & size attr arrays updated ✓.

**pSize attr** vs pDr: size updated = pDr (base) * growth: store pS0.

Write dust update:

```
for i: if(pLife[i]>0){pLife[i]-=dt;const u=1-pLife[i]/pMaxL[i];
 pSize[i]=pBase[i]*(1+2.6*u);pAlp[i]=pAlpha[i]*(1-u);
 if(pLife[i]<=0){pAlp[i]=0;continue;}
 drag; vel; pos;
} else pAlp[i]=0;
```

positions of dead stay wherever (alpha 0 → discard) ✓ init y -999 ✓.

**Points material uniforms**: none except none. ✓

Everything set. Compose now. Also double check start gantry lights reachable: lights stored global.

For the second arch: skip lights.

Let me finalize prop list quickly in code.

Also **flags wave update** loop: flags.forEach((f,i)=>f.rotation.y=f.userData.b+Math.sin(t*2.1+i*1.7)*0.3).

Balloons bob; clouds drift.

Now write the final response. Also keep in mind not starting with '#'.

Let me also decide LAPS=3 ✓ and mention "three laps" caption.

Counting total render objects OK.

Write it!

Small correction: In `update`, when computing `s` I use T[i] dot — T normalized ✓ proj can be negative near sample boundary — s=(i*ds+proj+L)%L ✓.

Lap detection uses this.s vs this.sPrev stored BEFORE overwrite: careful order: compute s, compare with this.s (prev), then assign ✓.

In reset: this.s = idx*ds (approx) ✓.

prog initial set = lap*L + s ✓.

At update end: this.prog=this.lap*L+this.s ✓.

Rubber band uses leadProg (prev frame max prog) ✓ fine.

Edge: during post, finished karts keep lapping (lap grows > LAPS): lap detection fine, finished stays true; speed factor 0.8 ✓; their prog keeps increasing — ranking key uses finished → stable order by finT ✓ winner stays P1 ✓.

OK writing the final file now — for real this time.

Also remember `<script type="module">` — no import map addition ✓.

After the code block: brief explanation. Keep concise.