Let me plan this carefully. I need to build a single self-contained HTML file with:

1. A voxel Minecraft-style world, at least 128×128 columns, procedurally generated with layered noise
2. Terrain types: grass-topped hills, snowy peaks, sandy beaches, water (semi-transparent), trees (wood + leaves)
3. Per-face shading so cubes read clearly
4. Procedural pixel-art textures drawn on canvas
5. Sky with sun, distance fog, drifting block clouds
6. InstancedMesh or merged geometry for performance
7. Cinematic camera flythrough on a smooth path, looking around
8. requestAnimationFrame timestamp for time
9. Full-window canvas with resize handling
10. Auto-starts, no interaction needed
11. Everything important shown in first 30 seconds

Let me design the architecture:

**Terrain generation:**
- 128×128 grid (or maybe 144×144 for a bit more). Let's do 128×128 as required.
- Layered noise: I'll implement value noise with fBm (multiple octaves) — layered noise means combining multiple noise layers at different frequencies. I'll write a seeded PRNG-based value noise with smooth interpolation, then fBm.
- Height function: base fBm for hills, plus a second lower-frequency "continental" layer to create a sea area and mountain region. Layered noise could be: continentalness (low freq) + erosion + hills + detail. Let's do:
  - `continent = fbm(x*0.006, z*0.006)` large scale — determines sea vs land vs mountains
  - `hills = fbm(x*0.02, z*0.02)` medium
  - `detail = fbm(x*0.08, z*0.08)` small
  - Combine with weights.
- Water level, e.g., y=8. Beach = height within 1 block above water → sand. Snow above certain height (e.g., y > 26 or based on slope/height). Grass otherwise.
- Trees: scattered on grass blocks with some probability, avoiding edges, using deterministic hash so reproducible. Tree: 4-6 tall trunk of wood, leaf blob (sphere-ish or Minecraft style canopy).

**Rendering:**
- Use merged geometry (BufferGeometry) with only visible faces (face culling against neighbors). This is the classic approach — build one geometry for opaque blocks (grass, dirt, stone, sand, snow, wood, leaves), one for water (semi-transparent). Actually leaves could be in opaque too since I'll draw them opaque textures (Minecraft "fast" leaves). That's fine.
- Per-face shading: I bake shading into vertex colors — top faces brightest (1.0), north/south (z faces) e.g. 0.8, east/west (x faces) 0.6 or so, bottom darkest (0.5). Plus simple ambient occlusion at vertices would be great for the voxel look — vertex AO based on neighboring blocks (the classic Minecraft AO trick). That significantly improves readability. I'll implement per-vertex AO: for each face vertex, check the two side neighbors and corner neighbor in the face's plane. AO values: 3-side (3 - occlusion count) → brightness multipliers [0.5, 0.7, 0.85, 1.0] etc.
- Textures: procedural canvas, pixel-art style. I'll create a texture atlas: a single canvas with tiles of 16×16 pixels each, arranged in a grid. Tiles needed:
  - grass top (green with noise)
  - grass side (dirt with green strip on top)
  - dirt
  - stone
  - sand
  - snow
  - snow side (dirt/stone with snow strip)? For snowy tops, blocks under snow cap... Actually in Minecraft snow blocks are full white. I'll make snowy peaks have snow block on top, stone/dirt beneath. Snow side could be dirt with white top strip — nice detail.
  - wood bark side, wood top (rings)
  - leaves
  - water (semi-transparent handled by material opacity; texture can be blue with lighter ripples)
- UVs: each block face maps to its tile in the atlas. To avoid bleeding, I'll use NearestFilter and inset UVs slightly (half-texel padding) or add padding. With NearestFilter and no mipmaps, bleeding is minimal; I can inset by a tiny epsilon. Actually to be safe: generate atlas with tile size 16, and set texture.magFilter = NearestFilter, minFilter = NearestFilter (no mipmap → no distant shimmering issues... well there will be aliasing at distance but acceptable; or use NearestMipmapLinear with generated mipmaps but mip blending across tiles causes bleeding). I'll use NearestFilter min/mag and generateMipmaps=false. To reduce distant moiré, could render at decent resolution. Fine.

Actually, better: pad each tile by duplicating edge pixels? Simpler: keep Nearest without mipmaps. Distant terrain may shimmer slightly during flythrough but acceptable. Hmm, shimmering during a cinematic flythrough could look bad. Alternative: use a mipmap-friendly atlas where each 16px tile is surrounded... With mipmaps, level 1 averages 2×2 blocks which stays within tile only if tile size divisible; bleeding occurs at tile boundaries at higher mip levels. A common trick: make each tile 16×16 but draw it into a 32×32 cell with 8px edge-extension padding, and UV map only the central 16×16. Mip levels up to ~3 are then safe. That adds complexity; maybe simpler: limit mip levels via `texture.minFilter = THREE.NearestMipMapNearestFilter`? Bleeding still happens.

Let me think about how important mipmaps are. Fog will hide far distance. The camera flies fairly low over terrain; nearest blocks are close, far blocks are fogged. Some shimmer is actually stylistically pixel-y. I'll go with magFilter Nearest, minFilter Linear... no — minFilter Linear with a non-mipmapped texture does bilinear sampling; across-tile bleeding only at exact tile borders within the atlas because linear filtering samples neighbors — at tile edges, sampling can reach adjacent tile pixels. With UV insets of half a texel, we avoid that. I'll inset UVs by 0.5 texel on each side. With minFilter = LinearFilter (no mips), distant shimmer reduced vs Nearest? Linear reduces aliasing somewhat. Hmm, but linear filtering on pixel art at close range blurs it. magFilter Nearest keeps close-range crispness; minFilter affects when texture is minified (far away). Actually THREE treats min vs mag by derivative; using minFilter=LinearFilter and magFilter=NearestFilter gives crisp near, slightly smoothed far. That's a good combo. And with half-texel UV inset, no cross-tile bleed. 

Wait — half texel inset with linear filter means at tile edges we sample the edge pixel duplicated — effectively clamped edge, good. But the inset also slightly crops the texture visually — negligible.

Hmm, but with minification without mipmaps you still get aliasing/shimmer. Fog helps. Let me also consider: scene fog from ~60 to ~140 units; world 128 wide. Camera flies at moderate altitude. Distant terrain is heavily fogged → shimmer hidden. Good.

**Chunking:** For 128×128 with height up to ~40, block count could be large but merged geometry handles it. I should generate geometry in chunks (e.g., 32×32 chunk regions) so each chunk is one merged mesh — helps frustum culling and keeps single draw call count low (16 chunks). Water as separate merged mesh per chunk or one global merged water mesh — water surface is mostly flat at sea level; but lakes above? I'll only have water fill up to sea level where terrain is below. Water geometry: top faces at sea level (y = seaLevel) where terrain height < seaLevel, plus side faces where needed at the boundary... Since water is inside terrain basins, the visible faces are the top surface and possibly side faces at map edges. To keep simple: build water top faces for all columns where height < seaLevel, at y = seaLevel (top of block seaLevel-? Let's define: column height h = number of solid blocks, top solid block at y = h-1. If h <= seaLevel... let me define seaLevel as the y coordinate of the water surface. If terrain height (top solid block index) < seaLevel, then water fills from height..seaLevel-1, with top water face at y = seaLevel - 0.1 (slightly below top to avoid z-fighting with nothing... actually water top face at y = seaLevel, i.e., the top plane of the block at y=seaLevel-1). Water blocks occupy y from h to seaLevel-1. Top face at y=seaLevel (top of the highest water block). Side faces: where water meets air horizontally — at the map boundary or where adjacent column terrain is lower? If adjacent column has terrain height >= seaLevel, water side is hidden against... no wait — if adjacent column's terrain height < seaLevel too, both have water, no face needed. If adjacent column height >= seaLevel... then adjacent solid block occupies that y, so water side is hidden. So water side faces only visible at the map boundary. Also underside not needed. And where the terrain slopes below water level at the shore, we see water top surface meeting sand — fine, no side faces needed except map edges. I'll just also render water side faces at map edge columns for a clean edge, or simply lower camera paths so map edges are less visible + fog. I'll include edge side faces for completeness — actually simpler: render water sides wherever neighbor column (in-map) has no water at that y and no solid block at that y (i.e., neighbor terrain height <= y < seaLevel)... that can happen if neighbor column is lower terrain — but then neighbor also has water there (since neighbor height < seaLevel). Hmm: neighbor has water if neighborH < seaLevel... if neighborH = 3 and seaLevel = 8, neighbor column has water at y=3..7. Our water at y=3..7 too. So sides coincide, no face. If neighborH >= seaLevel, solid blocks there. So indeed within the map, water side faces are never exposed. Only at map borders. I'll add border sides to make the world look like an island slab? Minecraft-style floating slab edge could be charming — classic "superflat world edge". I'll render water border sides. And opaque terrain border sides too — the terrain mesher naturally handles it if out-of-map counts as air. That makes the world a floating island slab — looks good with fog around.

Actually out-of-map = air means we render all side faces at borders — 4 sides × 128 columns × height ~ up to 40 blocks... that's 128×4×~15 avg = ~7700 faces extra. Fine, and it looks nice (visible cliffs at edge). But with fog and the camera staying inside-ish, edges barely visible. OK.

**Face culling:** standard: for each solid block, for each of 6 directions, if neighbor is air (or transparent-water for opaque blocks — water blocks should be treated as transparent so terrain under water renders sand visible through water; and water next to opaque doesn't render its own faces), add face. Water faces: water next to air (above) → top face; water next to opaque? no face; water-water → no face.

Leaves: treat as opaque (fast graphics). Blocks adjacent to leaves culled — fine.

**AO:** classic algorithm per vertex:
```
ao(side1, side2, corner) = side1 && side2 ? 0 : 3 - (side1+side2+corner)
```
brightness factor = 0.4 + ao*0.2 → [0.4, 0.6, 0.8, 1.0]? That's quite strong; commonly [0.55, 0.75, 0.9, 1.0] or similar. I'll use table [0.45, 0.65, 0.82, 1.0] maybe. Combined with face directional shade (top 1.0, sides 0.75/0.62, bottom 0.5). Multiply into vertex color.

Also need to handle the quad flip for AO (anisotropy): if a00+a11 > a01+a10 flip triangulation. I'll implement that for quality.

**Meshing data structures:** I'll build a heightmap-based world: since terrain is heightmap-based (no caves/overhangs except trees), I can store columns: for each (x,z): height h, and block type per y is derived: top block type (grass/sand/snow), under-top (dirt/sand/stone), deep stone. Trees add wood/leaf blocks — these need a full 3D structure or a separate map. Let me use a flat Uint8Array world of size X*Y*Z with Y = 64 (max height 64). 128*128*64 = 1,048,576 bytes = 1MB. Fine. Fill terrain, then place trees writing into array. Then mesh the whole array with neighbor checks. Simple and robust. Trees near map edges: keep trees ≥ 3 blocks from edges so canopies fit (canopy radius 2).

Memory/time: meshing 1M voxels — fine in JS, done once at startup. Should take maybe 100–300ms. OK.

Actually to reduce face count: interior blocks all culled; only surface faces generated: roughly surface area ~ 128*128 top faces + hills sides + trees ≈ maybe 60–120k faces? Let's estimate: 16,384 top faces, plus side faces from height differences: average |Δh| between neighbors maybe 1.5 → 2 per edge × ~32k edges ≈ 60k? Hmm could be ~40k side faces. Plus border faces ~8k. Plus trees ~ let's see 150 trees × (trunk 5×4 side faces=20 + canopy leaves exposed ~ 60) ≈ 12k. Total maybe ~80–120k faces = 160–240k triangles. Very manageable for merged BufferGeometry on any GPU.

Vertex count: 4 verts/face × ~110k faces = 440k verts, each with position (3f), normal (3f, or drop normals since we use vertex colors and MeshBasicMaterial — no lights needed!), uv (2f), color (3f). Using MeshBasicMaterial with vertexColors: true and map: atlas — lighting fully baked in vertex colors. That's the cheapest and looks exactly like classic Minecraft. 

Hmm — should I use MeshLambert + directional light for sun? Baked per-face shading already gives the Minecraft look; adding a real directional light with Lambert could double-shade. I'll go with MeshBasicMaterial + baked shading (Minecraft-authentic). Vertex colors multiply the texture. 

Also water: MeshBasicMaterial with transparency, opacity ~0.75, slight animation? I can animate water texture offset or vertex... keep simple: opacity 0.8, color tint. Maybe animate texture offset for gentle flow — the atlas is shared; I'd need a separate water material with its own texture. I'll make water a separate material with its own small canvas texture (32×32 ripples, repeat) — simpler than atlas, and animate `map.offset` slowly for movement. Nice touch: `waterMat.map.offset.y = t*0.02`. With RepeatWrapping. UVs for water top faces: world coords scaled so texture repeats every few blocks.

**Sky:** 
- Gradient sky via a big sphere/dome with custom shader or `scene.background` color + fog. I want a nice gradient: use a large sphere with ShaderMaterial (BackSide) with vertical gradient (horizon warm/whitish, zenith blue). Plus fog color matching horizon. Sun: a sprite/plane with radial gradient canvas texture, positioned in sky, always distant (attach to camera? or just far away at fixed direction; since camera moves within 128 world, a sun at distance 400 in fixed direction works with fog? Fog would fog the sun if it's a mesh with fog:true — set material fog:false. Sun as a plane with additive blending, or just a bright circle texture. Add subtle glow via larger soft radial texture. I should be careful with "no glow ornaments" taste — but a sun with a soft halo is natural, not a glowing title. Keep it tasteful: crisp disc + very subtle halo.
- Clouds: blocky Minecraft clouds — flat white translucent quads (Minecraft clouds are flat planes at fixed altitude, cellular shapes). Generate a cloud pattern from noise on a grid (e.g., 12×12-block cells), create merged geometry of flat boxes (thin boxes, e.g., 12 wide × 4 deep × 4? Minecraft clouds are 12×4×4? Actually Minecraft cloud texture cells are 12×12 px... The classic look: flat white slabs). I'll generate cloud cells: for each cell in a large grid (like 40×40 cells of size 8 units), if noise > threshold, add a flat box 8×1×8 (maybe 1 unit thick... Minecraft clouds are 4 thick? visually thin). Slight extra: give clouds a bottom face slightly shaded. Clouds drift slowly along +x, wrapping around. Material: MeshBasicMaterial white, transparent opacity 0.55, fog: false? With fog they'd fade at distance — actually fog on clouds looks nice; but fog is calculated from camera distance — clouds at y=60+ far away get fogged nicely. Keep fog true but fog range might not reach clouds near camera... fine either way. I'll use fog: true so distant clouds blend into sky. Hmm, fog color is horizon-ish; clouds against blue sky getting fogged to whitish — fine.

Cloud drift: move the cloud group x += speed*dt; wrap using modulo of pattern width — regenerate positions via two cloud meshes leapfrogging, or simpler: make the cloud field larger than world (e.g., 400 wide) and translate x from -200..+200 then wrap (offset resets — visible pop). Better: wrap individual cells: put cloud mesh group; each frame group.position.x = (t*speed) % cellSize... if pattern is periodic with period P in cells, moving group by P*cellSize returns identical appearance. If noise-based pattern isn't periodic, wrap will pop. Solution: make cloud pattern from a periodic hash: cell occupied if hash(cellIndexX mod N, cellIndexZ) < threshold — then pattern is periodic in x with period N cells → moving by N*cellSize is seamless. I'll do that: hash(i mod 40, j) based occupancy, plus smoothing? Blocky is the point. Maybe make blobs: occupancy = fbm-ish but periodic: use hash of ((i%N)+N)%N — that's periodic. To make clusters rather than salt-and-pepper, I can combine neighbor cells... Simplest: threshold on value noise sampled at cell centers with period N. I can implement value noise with period: lattice hash of (i mod N, j) — the noise itself is periodic if I wrap lattice coords. My value noise uses integer lattice hashed; if I hash (i mod N), the noise is N-periodic in that axis when the frequency is 1/cell. So: noise at frequency base, sample at (x*scale) with lattice wrap mod N. I'll just write a small dedicated periodic cloud noise: `cloudNoise(i,j)` = average of hash at (i,j), (i+1,j), (i,j+1), (i+1,j+1) smoothed — meh. Alternatively simpler and fine: occupancy = h(i,j) where h = hash2(i mod 32, j mod 32), then apply a smoothing pass: cell occupied if sum of 3×3 neighborhood ≥ k → produces blobby clusters. All periodic. 

I'll build cloud geometry once as merged boxes in a group of width N*cell, and set group.position.x = -(t*speed mod (N*cell)). Seamless loop. 

**Fog:** THREE.Fog(color, near, far). Fog color should match horizon color for seamless blend. Sky dome unaffected by fog (fog:false in its material / ShaderMaterial ignores fog by default).

**Camera path:** Smooth cinematic flythrough. Design a path using CatmullRomCurve3 through waypoints that:
- Start low over the sea/beach looking at the island
- Sweep over water toward shore, rise over hills, weave between hills (path over valleys), climb to reveal snowy peaks, pass near trees, descend along lake, end wide shot.
- Duration: loop maybe 60–75s, but key moments in first 30s. Loop with curve closed? A closed loop makes seamless looping. I'll make a closed CatmullRom curve around/over the island.
- Look direction: lookAt a target point that moves along a second curve (offset ahead), or lookAt targets that vary: use a separate CatmullRom for the look target with more variation — looking at mountains, down at water, etc. Add gentle banking/roll? Roll could complicate; skip roll, but add smooth look-ahead with slight lateral offset oscillation for "looking around". Also add subtle sinusoidal bob.

Camera height must clear terrain: I'll design waypoints manually after seeing typical heights... Since terrain is procedural with a fixed seed I control, I can tune the seed offline? I can't run it here, so I must make it robust: compute terrain heights at generation time, then build the camera path relative to actual heights: choose waypoints in (x,z), set y = terrainHeight(x,z) + clearance, and smooth. Even better: sample the curve, and clamp camera y above terrain: after computing pos along curve, do y = max(y, groundHeight+minClear) with smoothing... Simpler robust approach: define control points; for each control point, set y = max(groundHeight(x,z), seaLevel) + clearance_i where clearance varies (low over water: +3, over hills: +6, mountain reveal: +20 high). Then CatmullRom smooths. But between control points, a hill could poke through. To guarantee no clipping: after sampling the curve densely at build time, raise samples: compute for each sample the required minimum y = ground+clear, then enforce monotone-ish smoothing: iterate y_i = max(y_i, ground_i + clearance), then smooth y again a couple passes (or use a moving-max filter). A practical approach: 
1. Sample curve at N points, get base y from curve.
2. minY_i = groundHeight at (x,z) + clearance (clearance ~4–6, lower over water: ground includes water? ground for water areas = seaLevel; we want to fly low over water: clearance above water surface ~3).
3. y_i = max(base_i, minY_i).
4. Apply several smoothing iterations (moving average) on y, then re-raise where violated, small blend... Could oscillate. Alternative simpler: since I control seed and can compute ground anywhere cheaply via the height function (pure function of x,z!), I can just build the path as: pos(x,z along curve) with y = terrainClearanceFunction sampled along the way, smoothed by sampling the clearance with wide gaussian. Because height function is analytic (noise), I can query max clearance along future segment.

Simplest robust: build path points; for each path point p(t), y = f(t) where f built from: sample the analytic max ground height in a neighborhood? Let me do: y_needed(s) = maxGroundAlong(s-Δ..s+Δ) + clearance(s). Then apply exponential smoothing over s. Then camera follows exactly this. Since it's precomputed at startup into an array of e.g. 600 samples (loop), cost trivial. Also do the same for the look-target path? Look target can be terrain points (look at mountains etc.) — I'll define look targets as specific interesting points: pick from generated world: e.g., the highest peak position, the lake center, a dense tree area, beach point... I can find these programmatically after generation: highest peak (max h), a big water region center, etc. Then look-target curve: CatmullRom through those points (with y adjusted), looping. Camera looks at target — but instantaneous lookAt each frame with moving target can be jittery if target moves across; using a smooth CatmullRom for targets with arc-length parametrization is smooth enough.

Actually a cleaner cinematic approach: camera position on closed curve; lookAt target = position on a second closed curve that leads the camera (points ahead along the terrain at interesting spots). And to "look around", add slight offset: target += lateral*sin(...) small. Also add gentle FOV? Keep constant.

Timing: closed loop duration ~72s; key beats in first 30s. Let me script beats:
- t=0–8s: low over the sea, water to the sides, island & beach ahead, sun visible.
- t=8–15s: cross the beach, skim over sand and grass, trees passing.
- t=15–24s: climb alongside hills, valley weave, reveal snowy peak (camera looks at peak).
- t=24–32s: crest high point, wide vista over the whole island + lake, then descend toward lake shore.

I'll orient the world so the sea is at one side and mountains at the other, by biasing the noise: continent layer: add a gradient/directional bias: e.g., continent value increases toward -z (mountains at north), sea toward +z. I can craft height function: 
```
c = fbm2(x*0.0045+13.7, z*0.0045)  // 0..1
bias = (z/size) // 0 at -z edge... 
```
Let me define: sea occupy roughly the +z third, mountains the -z third. Use coordinate u = (z/SZ + 0.5) in [0,1] (0 at z=-64, 1 at +64). continent = fbm*0.5 + (1-u)*0.45 → higher toward -z. Then height mapping:
```
h = seaFloor + (continent-based)
```
Let me design height function concretely:

World: SX=SZ=128, SY=48? Max height: sea level at y=12? Let me set: waterLevel = 13 (water surface at y=13, water blocks at y ≤ 12 occupying up to 12... let me define surfaceY = 13 meaning water top face at y=13.0).

Height computation:
```
// continental: 0..1, controls sea vs mountains
const cont = fbm(x*0.006, z*0.006, 4) // ~[-1,1]
// directional: +1 at mountains (-z), -1 at sea (+z)
const dir = ( -z ) / 64  → in [-1,1]; actually dir = (64 - z)/128*2-1? Let me: t = (z + 64)/128 → 0 at z=-64 (mountain side), 1 at z=+64 (sea side). dir = 1 - 2t → 1 at mountains.
let e = cont*0.55 + dir*0.45  // ∈ ~[-1,1]
// hills
const hill = fbm(x*0.02, z*0.02, 4)
// detail
const det = fbm(x*0.07, z*0.07, 2)
```
Then map e to base elevation:
```
base = lerp: 
if e < -0.1 → sea floor: depth = map e from [-1,-0.1] to [-10, 0] below water
else land: height = lerp from waterLevel to peak by e^power
```
I'll write something like:
```
let h;
const t = smoothstep(-0.15, 0.35, e); // land factor 0..1
const land = waterLevel + t*t*30 * (0.75 + 0.35*hill) ... 
```
Hmm, let me be more careful and produce good-looking results. I'll define:

```
waterLevel = 12 (surface at y=12, water fills y in [.., 11]? 
```
Let me define ground height H(x,z) = integer top solid y. Water surface W = 13 (top water face at y = 13.0 → water blocks occupy up to y=12, i.e., columns with H < 13 have water from H+1..12... wait if H is top solid block index, blocks occupy y=0..H. Water occupies y=H+1 .. 12, top face at y=13. So beach condition: H == 12 or 13 → sand; H in [13..] grass; snow if H > 30 maybe with dithered line; stone if H > 26 transition.

Hmm let me choose numbers:
- SY (world height) = 56.
- Water level W (surface y) = 12 → water top at y=12.0, water blocks y=H+1..11 (since block at y occupies [y, y+1]). Let me define block y occupies vertical span [y, y+1]. Solid blocks: y=0..H. If H ≤ 11: water fills y=H+1..11, top water face at y=12.0. Beach: H == 12..13 → sand top. Underwater floor: sand near shore, dirt/stone deeper? Minecraft: sand under shallow water, gravel/dirt deeper. I'll do sand if H ≥ W-4 (i.e., H in [8..12] underwater near shore → sand), else stone/dirt below.

Height mapping (continuous elev before quantize):
```
const m = fbm(x*0.0055, z*0.0055, 4, seedA);        // continent, ~[-1,1]
const dirBias = 1 - 2*(z+64)/128;                    // +1 at z=-64 (mountains), -1 at z=+64
let e = m*0.6 + dirBias*0.4;
```
Wait dirBias +1 at mountains: at z=-64, t=0, dirBias=1. Good.

Then:
```
const hills = fbm(x*0.018, z*0.018, 4, seedB);      // ~[-1,1]
const detail = fbm(x*0.06, z*0.06, 3, seedC);
let hgt;
if (e < -0.05) {
   // sea: depth increases with -e
   const d = (-e - 0.05)/0.95; // 0..1
   hgt = W - 2 - d*11 + hills*1.5 + detail;  // down to ~W-13
} else {
   const t = smoothstep? land elevation: 
   const land01 = e; // 0.05..1
   const mountainous = smoothstep(0.25, 0.9, e);
   hgt = W + 1.5 + land01*14*(0.6+0.5*hills) + mountainous*mountainous*22*(0.8+0.35*hills) + detail*1.5;
}
```
Let me estimate max: e up to ~1 (m*0.6 up to .6 + dir .4 = 1.0), land01=1, mountainous=1: hgt = 12+1.5+14*1.1 + 22*1.15 + 1.5 ≈ 12+1.5+15.4+25.3+1.5 ≈ 55.7 — too high vs SY=56 (need ≤ 54 with trees on top? trees only on grass, not snow peaks — okay but canopy up to +7). Let me cap: worldHeight array SY=64, terrain up to ~50, trees up to ~44+7=51 < 64. Fine — set SY=64, clamp hgt to ≤ 50. Memory 128*128*64=1MB fine.

Min: hgt ≈ 12-2-11-1.5-1 = -3.5 → clamp ≥ 3 (keep bedrock-ish floor at y≥2, stone below). Underwater floor min y ~ 3. Depth up to ~9 below surface. Good — visible through semi-transparent water.

Snow: H ≥ 32 + dither (dither via hash: snow if H ≥ 32 + (hash*4 - 2)? I'll do: snowLine = 30 + hash(x,z)*6 → snow top if H > snowLine; stone top if H > snowLine-4 (rocky band below snow); grass otherwise. Also expose stone on steep slopes? Skip slope detection — height bands fine, maybe add: if hill slope steep → stone. Slope from neighbor heights in the mesher? Simpler: compute local gradient from height function finite differences: if |∇H| large → stone even below snowline. Nice touch but optional; I'll add cheap version: steep = (|dHdx|+|dHdz| > 2.2) → stone/dirt top on grass areas. Hmm, since column tops only, side exposure shows dirt under grass top; that's classic Minecraft anyway. I'll skip slope-based to keep code lean but maybe include simple version. Let me include it — it's ~5 lines using height function gradient. Actually the block type assignment happens per column using H; gradient computable from the continuous height function. I'll include: steep slopes → stone surface. It adds realism to mountains. OK.

Beach: sand if H ≤ W+1 (H in [W-3..W+1] sand; below that underwater: sand if H ≥ W-4 else stone with dirt patches? Under deep water use stone/dirt? Minecraft deep ocean is gravel; I'll use stone for deep, sand shallow.

Trees: on grass columns (H > W+1, not snow, not steep), hash(x,z) < 0.012 and local max-ish (avoid adjacent trees: require hash of (x,z) to be the minimum among 3×3 neighborhood hashes? That's a neat trick: place tree if h(x,z) is strict minimum in 5×5 → guarantees spacing). Also avoid map edge (≥3 from edge... canopy radius 2 → margin 2, plus trunk 1; margin 3 safe). Also maybe density modulated by forest noise (fbm at low freq > 0.1) → clustering into groves. Nice: forest = fbm(x*0.01+..., ...) > 0.15 → density 0.05 else 0.004. I'll implement spacing via "is local min of hash in 5×5 radius" — that's 25 hash evals per candidate; only for cells passing the cheap hash test first. Fine.

Tree structure (per tree at (tx, H, tz)): trunk height th = 4 + hash*3 (4–6). Leaves: canopy: for dy in [th-3 .. th+1]... classic oak: leaves in a 5×5 at two layers below top, 3×3 above, plus top cross. Let me do:
- layers: y = base+th-3, base+th-2: radius 2 (5×5) minus corners randomly (hash-based corner skip)
- y = base+th-1: radius 1 (3×3) minus corners sometimes
- y = base+th: radius 1 cross (skip corners)
- y = base+th+1: plus shape (center + 4)
Trunk from base..base+th-1 (leaves don't replace trunk). All written into voxel array with type LEAF/WOOD if currently air. Base ground = H (trunk starts at H+1). Ensure base+th+1 < SY.

Block types enum:
0 air, 1 grass, 2 dirt, 3 stone, 4 sand, 5 snow(block: snow-capped? I'll do full snow block texture white), 6 wood, 7 leaves, 8 water(special-cased in mesher, not in opaque array — actually store water in array as type 8 but mesh separately).

For grass block: top = grassTop tile, sides = grassSide, bottom = dirt. Snow block: top snow, side snowSide (dirt w/ white cap)? For mountain snow I'd rather have full snow blocks on top, and beneath them stone. Side texture of snow block = snow side (white with dirt bottom? In Minecraft "snowy grass" side is dirt with snow rim). I'll draw snowSide: mostly white top half? Let me: snow block sides = snowy dirt side (top 4px snow, rest dirt)? If snow is 1-2 blocks thick on peaks, sides visible at cliff edges. I'll make snow blocks fully white (snow top + snow side full white slightly shaded) — cleaner for peaks. And stone beneath. OK: SNOW = full white tile all faces.

**Tiles (16×16 each) in atlas 4×4 (256×64? 4 cols × 4 rows = 16 tiles at 64×64 px):** tiles needed: grassTop, grassSide, dirt, stone, sand, snow, woodSide, woodTop, leaves, and maybe gravel — 9 tiles → atlas 4×4 grid = 64×64 px canvas. Fine. Actually padding: with half-texel UV inset, ok.

Pixel-art drawing: for each tile, per-pixel fill with base color + random darker/lighter variants (seeded). E.g.:
- grassTop: base #6fbf44-ish... Minecraft grass ~ (124,189,66)? I'll pick pleasing palette: grass top base rgb(106,170,64) with per-pixel variation ±10%.
- dirt: rgb(134,96,67) variation, with occasional darker speckles.
- grassSide: dirt base + top 3-4 px grass with jagged boundary (random dip 0-2px).
- stone: rgb(125,125,125) variation, some cracks? Keep speckle.
- sand: rgb(219,207,163) variation.
- snow: rgb(240,246,250) variation.
- woodSide: vertical stripes alternating rgb(104,78,47)/(87,64,38) with variation; bark look: columns of 1px with occasional lighter.
- woodTop: rings — concentric squares light/dark.
- leaves: rgb(58,122,40)? Leaves in Minecraft are semi-dappled: mix of leaf green with darker holes (draw some pixels much darker to fake depth). Since opaque, use varied greens with dark speckles.
- (optional) water tile separate texture: 32×32 blue rgb(50,110,190) with lighter wave streaks; opacity 0.72.

For deterministic randomness in textures use a seeded PRNG (mulberry32).

**Atlas UV mapping:** tile index → (col,row). Face UVs: map the 4 corners to tile rect inset by 0.5/64 (half texel of 64px atlas? half texel = 0.5/atlasPixelSize). Atlas 64×64 with 16×16 tiles → tile UV size 0.25. inset e = 0.5/64 = 0.0078125.

**Mesher details:**

For each solid voxel and each of 6 faces: neighbor lookup; if neighbor is air or water (for solid blocks: face visible if neighbor is air or water or leaves? leaves opaque → hidden; treat leaves opaque) — visible if neighborType == AIR || neighborType == WATER. For water blocks: face visible if neighbor == AIR (top mostly). Underwater: solid faces adjacent to water should be rendered (visible through water) — handled since neighbor==WATER → render.

Face vertex data: I'll define for each of 6 dirs the 4 corner offsets, normal, and the AO neighbor offsets. Standard tables. Let me define faces as:

For dir +X (normal (1,0,0)): quad at x+1 plane, corners (1,0,0),(1,1,0),(1,1,1),(1,0,1) with correct winding (CCW viewed from +x): looking from +x toward -x, CCW: (1,0,1),(1,0,0),(1,1,0),(1,1,1)? Let me carefully define using a generic method: I'll write faces with explicit arrays and verify winding mentally. Alternatively build quads and set two triangles with indices (0,1,2, 0,2,3) — need CCW when viewed from outside for front face (THREE default frontface CCW). I'll define each face's corners in CCW order as seen from outside:

+Y (top), viewed from above (+y looking down -y): CCW in the x-z plane as seen from above means... When looking down the -y axis (from above), we see x right, z toward viewer? Coordinate: right-handed, +y up, +x right, +z toward viewer (out of screen). Looking from above (down -y): x to the right, z downward on screen... hmm let me just carefully compute one and trust symmetrical definitions.

Standard approach — define for each face 4 vertices; normal via cross product check. Let me define:

Top (+y): v0=(0,1,0), v1=(0,1,1), v2=(1,1,1), v3=(1,1,0). Triangles (v0,v1,v2),(v0,v2,v3). Normal = (v1-v0)×(v2-v0) = (0,0,1)×(1,0,1)... (v1-v0)=(0,0,1), (v2-v0)=(1,0,1). cross = (0*1-1*0, 1*1-0*1, 0*0-0*1) = (0,1,0)? cross((0,0,1),(1,0,1)) = (0*1 - 1*0, 1*1 - 0*1, 0*0 - 0*1) = (0, 1, 0). Yes +y. 

Bottom (-y): v0=(0,0,0), v1=(1,0,0), v2=(1,0,1), v3=(0,0,1). (v1-v0)=(1,0,0),(v2-v0)=(1,0,1) cross = (0*1-0*0, 0*1-1*1, 1*0-0*1) = (0,-1,0). Good.

+X: plane x=1. v0=(1,0,0), v1=(1,1,0), v2=(1,1,1), v3=(1,0,1). (v1-v0)=(0,1,0), (v2-v0)=(0,1,1). cross = (1*1-0*1, 0*0-0*1, 0*1-1*0) = (1,0,0). Good.

-X: plane x=0. v0=(0,0,1), v1=(0,1,1), v2=(0,1,0), v3=(0,0,0). (v1-v0)=(0,1,0),(v2-v0)=(0,1,-1). cross=(1*(-1)-0*1, 0*0-0*(-1), 0*1-1*0) = (-1,0,0). Good.

+Z: plane z=1. v0=(1,0,1)? Let me: v0=(0,0,1), v1=(1,0,1), v2=(1,1,1), v3=(0,1,1). (v1-v0)=(1,0,0),(v2-v0)=(1,1,0). cross=(0*0-0*1, 0*1-1*0, 1*1-0*1)=(0,0,1). Good.

-Z: plane z=0. v0=(1,0,0), v1=(0,0,0), v2=(0,1,0), v3=(1,1,0). (v1-v0)=(-1,0,0),(v2-v0)=(-1,1,0). cross=(0*0-0*1, 0*(-1)-(-1)*0, (-1)*1-0*(-1)) = (0,0,-1). Good.

UVs per face: map so textures aren't rotated weirdly. For top/bottom: (x,z) → (u,v). For sides: horizontal along the face, v along y (v increases upward; in three.js UV v=0 bottom of texture by default with flipY=true for canvas textures). I'll assign: for +X face vertices v0(y=0),v1(y=1),v2(y=1),v3(y=0): u from z? For +X face, horizontal axis is z (from z=0 at v0 to z=1 at v3? v0=(1,0,0) z=0, v3=(1,0,1) z=1). Assign uv: v0=(u0,0), v1=(u0,1)... v1 is at y=1 → v=1. So uv per vertex: v0:(a,0), v1:(a,1), v2:(b,1), v3:(b,0) where a,b = tile u edges (order maybe mirrored but pixel-art noise textures don't care about mirroring; grass side must be upright — v up correct). For -X: v0=(0,0,1)→(a,0), v1=(0,1,1)→(a,1), v2=(0,1,0)→(b,1), v3=(0,0,0)→(b,0). +Z: v0=(0,0,1)→(a,0), v1=(1,0,1)→(b,0), v2=(1,1,1)→(b,1), v3=(0,1,1)→(a,1). -Z: v0=(1,0,0)→(a,0), v1=(0,0,0)→(b,0), v2=(0,1,0)→(b,1), v3=(1,1,0)→(a,1). Good — v aligned with y everywhere on sides. Top: v0=(0,1,0)→(a,c), v1=(0,1,1)→(a,d), v2=(1,1,1)→(b,d), v3=(1,1,0)→(b,c). Bottom: similar map (x,z).

AO per vertex: for a face with normal n, vertex at corner c: the three neighbors to test are the blocks adjacent to the face plane: side1 = neighbor offset along tangent1 direction (±), side2 along tangent2 (±), corner = both. For each face I need per-vertex the two tangent directions signs. Generic method: for vertex corner coordinates (cx,cy,cz) each 0/1 relative to block, and face normal axis: the two tangent axes t1,t2 (the axes ≠ normal axis). Sign for tangent axis a: s = (c[a]==1 ? +1 : -1)... but careful: neighbor offsets are from the block position: neighbor in direction of tangent axis a with sign s where s = c[a]*2-1. Then:
- side1 = block + n + t1*s1 (only the normal-offset cell plus one tangent offset)
- side2 = block + n + t2*s2
- corner = block + n + t1*s1 + t2*s2
where n is the face normal offset (e.g., for top face: block + (0,1,0) is the air cell above). occl(x) = solid&&opaque (count water as non-occluding, leaves occluding? leaves occlude → yes count leaves as occluders for AO; looks fine).

ao level = side1&&side2 ? 0 : 3-(side1+side2+corner). brightness = aoCurve[level] = [0.45, 0.62, 0.8, 1.0] maybe. Combined color = faceShade[dir] * ao * blockTint? blockTint unused (textures carry color). Vertex color = shade value (grayscale) → color attribute (r=g=b=shade). MeshBasicMaterial vertexColors multiplies texture. 

Quad flip based on AO: if a0+a2 > a1+a3 use triangles (0,1,2)(0,2,3) else (1,2,3)(1,3,0) — standard: choose the diagonal connecting the two vertices with higher combined AO to avoid dark diagonal artifacts. Standard rule: if a00 + a11 > a01 + a10 flip. With my vertex ordering (v0..v3 around quad), diagonal options: (v0,v2) or (v1,v3). Default triangulation (0,1,2)(0,2,3) uses diagonal v0-v2. If a0+a2 < a1+a3 → flip to diagonal v1-v3: triangles (1,2,3)(1,3,0). I'll implement that.

Geometry building: arrays positions (Float32), colors, uvs, indices (Uint32). Build per chunk (16×16 columns? or 32×32) → chunks of 32×32 → 4×4=16 opaque meshes + 16 water meshes? Water is few — one global water mesh fine (its faces are top planes only, plus border sides). But frustum culling benefit from chunks; water few faces anyway. I'll do opaque in 32×32 chunks (16 meshes), water as single merged mesh (maybe 2k faces). Also clouds one mesh, sky dome, sun.

Bounding: set positions in world coordinates directly (no per-chunk offset needed); geometry.computeBoundingSphere for frustum culling. Or set positions local to chunk origin and mesh.position — better precision not needed. World coords fine.

Estimated indices > 65535 per chunk? Per 32×32 chunk faces maybe ~8–15k → verts ~60k > 65535 possible; use Uint32 indices to be safe.

**Camera path construction:**

After world gen, I have height function H(x,z) (analytic) and water level. Define path control points (in world coords, world spans x,z ∈ [0,128] — I'll center world at origin: blocks placed x-64.. x+64? Simpler: keep voxel coords 0..127 and set world group position -64 to center; camera path in centered coords. Or compute everything in voxel coords and just place camera path there; centering only matters for sun/sky positions. I'll build meshes in voxel coords but subtract 64 in the mesher (i.e., emit positions as (x-64+..., y, z-64...))? That complicates neighbor lookups none — just offset when writing positions. I'll generate voxels in [0,SX) and write vertex positions with offset -SX/2 → centered at origin. Sun direction fixed e.g. (−0.4, 0.5, −0.6) normalized... mountains at -z, sun placed toward mountains-ish so peaks are lit? With baked shading, sun position only matters for the visible sun disc and cloud brightness. I'll put sun low-ish in the sky toward the sea (+z? ) Hmm: cinematic: sun visible in frame during sea approach → camera starts over sea looking toward island (mountains beyond). If sun is behind mountains at start, it's hidden. Place sun to the east (+x) moderately high, so during circling it appears sometimes. Let me define sun direction from center: (0.45, 0.55, 0.35)? normalized → position = dir * 380. During path around the island the sun will enter view occasionally. Good enough; also make the sky shader brighten around sun azimuth? Could add subtle sun glow in sky shader — nice: sky gradient + additive halo around sun direction. Tasteful.

Path control points: I'll compute after generation using actual terrain: choose a sequence of (x,z, clearance) and build points:
```
const pts = [
 {x: -10, z:  95, cl: 2.5, look:...},   // over sea, low
 ...
]
```
But better to design relative to terrain features found at runtime: find peak (max H) location, find deep water center, beach between. Since noise + directional bias guarantees: sea near +z edge, mountains near -z. I can hardcode approximate (x,z) route since terrain layout is forced by the bias, with runtime y from height function. Route (centered coords, world edge at ±64):

1. (-20, 88) over deep sea, low (cl above water 3)
2. ( 25, 70) approaching beach
3. ( 45, 45) over beach/bay low
4. ( 52, 18) rising over grass hills
5. ( 30, -5) between hills (valley) — need clearance from terrain
6. ( 0, -25) near peak flank, higher
7. (-30, -35) high, reveal peak (camera at cl 26 → ~45 altitude)
8. (-55, -10) curving around west side, descending
9. (-58, 25) along west shore/sea
10. (-40, 60) over water toward start
Closed loop through these with CatmullRom (closed). Y per point = max(ground+clearance) computed then smoothed along samples.

Look target path: separate closed curve through interesting points:
- (10, 60) shoreline
- peak location (found at runtime, y = peak top +2)
- lake? my terrain has sea at +z; also maybe an inland lake — with continent noise there may be pockets below water level inland → lakes exist naturally. Find largest inland water region? Simple: scan columns with water and H < W-3 that are >20 blocks from +z edge... simpler: pick the water column farthest from sea edge (max distance from z=128 side) → "lake". Eh, might overcomplicate. Alternative look targets: peak, beach point, forest area (tree with most neighbors), valley. I'll gather: peak point, a mid mountain flank, forest center (average position of trees cluster: pick tree with max tree-count in 16-radius), bay point (water at mid x). Then look curve CatmullRom closed through ~6 points with y = target ground + 4..8.

Then per frame: t param → camera pos curve.getPointAt(u) (use arc-length param via getPointAt for constant speed — CatmullRomCurve3 supports getPointAt with arc length; precompute .getLength etc. — fine, three does this automatically with updateArcLengths; getPointAt uses cached lengths). Loop duration D=72s → u = (t/D) % 1.

Look target: u2 = (t/D + lead) % 1, with lead ~0.03 → target slightly ahead; plus lateral sway: target += right*sin(t*0.3)*4? The target curve already weaves. Also vertical bob on camera: +sin(t*0.5)*0.4 subtle.

Smoothing the look: camera.lookAt each frame is fine as target moves smoothly. To avoid roll issues — lookAt uses up (0,1,0), fine.

Clearance guarantee: build camera y via sampled loop:
```
const N=720; for i in 0..N-1: p = baseCurve.getPointAt(i/N); g = groundHeightAt(p.x,p.z) (from analytic height fn; if underwater ground = terrainH but we want clearance above water surface: base = max(H+1, W) ... define groundRef = max(H(x,z)+1, Wsurface) then minY = groundRef + clearanceProfile(i)
```
clearance per control point given; interpolate clearance along samples too (catmull on clearance or just lerp between control samples). Then y_i = max(baseCurveY_i, minY_i); then smooth: 3 passes of y_i = (y_{i-1}+2y_i+y_{i+1})/4 then clamp again to minY (max keeps safety) — final pass order: smooth then max then smooth-light. I'll do: repeat { smooth; enforce max; } 3 times → converges with smooth ramps. Enforce after each smoothing so final respects minima. Ramps: when terrain rises 10 blocks between samples (adjacent samples 1/720 of ~450-unit loop ≈ 0.6 units apart... loop length maybe ~500 units; N=720 → ~0.7 unit per sample; terrain slope up to ~1 → y rises ~0.7/sample; smoothing keeps within a couple samples. Fine.

Then final camera samples array: positions[i] and I'll create a new CatmullRomCurve3(closed) from these smoothed points and use getPointAt for constant speed... Creating a curve from 720 points with closed=true: getPointAt heavy? It's fine — arc length computed once. But Catmull through 720 dense points is fine and effectively equals samples. Alternatively interpolate samples directly with linear + the y already smooth — could show slight polyline kinks in direction; Catmull from dense samples is smooth. I'll build final CatmullRomCurve3 from every 4th sample (180 points) closed, tension default 0.5 → smooth.

Actually simpler: skip baseCurve: build control points list with y=0 placeholder, sample, adjust y, smooth, build final curve. Yes as above.

Also the "look" curve: targets at fixed world points, closed CatmullRom, y set per point. Ensure look target doesn't go under terrain: y = max(groundRef(x,z)+2, y). Also since camera may be far from target (e.g., 80 units), fog on target area fine.

Timing check — first 30s must show: sea+beach (start), hills+trees, snowy peak, wide vista, clouds+sun. With loop u=(t/72): 
- u 0→0.11 (0–8s): segment 1–2 sea → beach.
- 0.11–0.21 (8–15s): beach→hills.
- 0.21–0.33 (15–24s): hills→valley→peak flank.
- 0.33–0.44 (24–32s): peak→high vista→descend west.
Good coverage.

I should double-check the control points map to terrain that exists: mountains at -z (north), sea at +z (south). Points with z negative are inland/north. Peak found at runtime — I could snap control point 7 to be near the peak: e.g., replace (-30,-35) with (peak.x+8, peak.z+10) so camera passes right by the peak. And look-target at exact peak. Also valley point: choose (0,-5) may be on a hill — clearance handles it (camera rises over terrain). Weave between hills would be nicer but risky without inspecting terrain; clearance logic keeps it safe and still dynamic since camera hugs terrain. To enhance "between hills" feel, I can route through a low pass: find the lowest-terrain crossing along some line? E.g., find min height along the x=0 column between z=-30..0 → set valley point there. Cheap and effective. Similarly find the beach crossing: along the start→land route, find where H crosses W near path. Eh — keep a couple of runtime snaps: peak flank snap + valley snap. Good.

**Sun:** Directional look: a THREE.Mesh plane (or Sprite) with canvas radial texture: bright core disc + soft falloff; additive blending; depthWrite false; positioned at sunDir*400 (inside sky dome radius 800? dome radius ~ 900, camera far 2000). Render order: sky dome (BackSide) first, then sun. Fog must not affect: material.fog=false.

Sky dome: ShaderMaterial with uniforms topColor, horizonColor, plus sun glow: color = mix(horizon, top, pow(max(h,0),0.6)) + sunGlow where sunGlow = pow(max(dot(dir, sunDir),0), 40)*haloColor*0.6 + wider*0.15. Dome follows camera position (dome.position.copy(camera.position)) so it never gets exited — with radius 900 and far plane 1200 fine. Since camera moves ±70, fixed dome at origin radius 1000 also fine, but following camera is safer. I'll follow camera (only x/z? follow fully; y as well but horizon gradient is view-direction based so fine).

Fog: THREE.Fog(horizonFogColor, 90, 260)? World diag ~180; camera far 1200 (to include dome at 900 — dome material fog:false anyway, so far can be 600 with dome radius 500? If fog far 260, distant dome areas fully fogged?? Fog applies to materials with fog:true; dome ShaderMaterial without fog chunk → unaffected. Terrain fogged to fogColor; horizon color should equal fog color → seamless. Sky dome near horizon should be fogColor-ish then blend up to zenith blue. Good: horizonColor == fogColor.

Water also fogged (fog:true default) — good.

Clouds: fog true — at distance ~150+ they fade into sky. Cloud altitude y=78 (above peaks ~50). Clouds within fog range near camera → visible clearly overhead.

**Performance:** draw calls: 16 chunk meshes + 1 water + clouds + dome + sun ≈ 20. 

**Resize:** renderer.setSize(window.innerWidth, innerHeight), camera.aspect update. devicePixelRatio clamp min(dpr,2).

**Clock:** use performance-timestamp from rAF: `function loop(ts){ ... t = ts*0.001 ... }` — first frame ts may be large? It's time since page origin — fine as absolute. Use `const t = ts / 1000`. Also guard first-frame delta spikes: dt = clamp(t - last, 0, 0.1) for cloud drift and water offset (though both are functions of absolute t anyway → use absolute t, no dt needed. Camera u absolute too. So dt unused — good, immune to tab switching.)

Cloud drift: group.position.x = -((t*speed) % period). Speed ~1.5 units/s. Period = cloudPatternWidth (e.g., 48 cells × 10 = 480). Negative modulo: ((t*s) % P + P) % P → x = -that. Movement direction -x or +x, whatever.

Water texture offset: waterTexture.offset.set((t*0.008)%1, (t*0.013)%1) — with RepeatWrapping.

Also gentle water opacity pulsing? no. Maybe vertex-level water bob? skip.

**Now, code structure:**

```html
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>...</title>
<style> html,body{margin:0;height:100%;overflow:hidden;background:#0b0e14} canvas{display:block} </style>
</head>
<body>
<script type="module">
import * as THREE from 'three';

// --- PRNG & noise ---
function mulberry32(seed){...}
function hash2(x,y,seed) // integer hash → [0,1)
value noise: lattice smooth interp (quintic), fbm with octaves.

// --- constants ---
SX=SZ=128, SY=64, WATER_Y=12 (surface), ...

// height function (analytic, floats) hCont(x,z) returns float elevation
// worldgen: fill Uint8Array vox
// block ids, tree placement

// --- textures: atlas canvas 64x64 (4x4 tiles of 16), water canvas
// tile drawing functions

// --- mesher: build chunk geometries with AO, per-face shade, atlas UVs
// water geometry builder

// --- scene setup: renderer, camera, fog, sky dome shader, sun, clouds

// --- camera path build (using height function)

// --- animate(ts)
</script>
</body></html>
```

Let me now write all the pieces carefully.

**Noise implementation:**

```js
function hash2i(x, y, seed){
  let h = (x*374761393 + y*668265263 + seed*1442695041) | 0;  // need Math.imul for safety
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  h ^= h >>> 16;
  return (h >>> 0) / 4294967296;
}
```
Use Math.imul for the multiply steps:
```js
function hash2(x, y, seed){
  let h = Math.imul(x, 374761393) + Math.imul(y, 668265263) + Math.imul(seed|0, 1442695041) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  h ^= h >>> 16;
  return (h >>> 0) / 4294967296;
}
```

Value noise:
```js
function vnoise(x, y, seed){
  const xi = Math.floor(x), yi = Math.floor(y);
  const xf = x - xi, yf = y - yi;
  const u = xf*xf*xf*(xf*(xf*6-15)+10);
  const v = yf*yf*yf*(yf*(yf*6-15)+10);
  const a = hash2(xi, yi, seed), b = hash2(xi+1, yi, seed);
  const c = hash2(xi, yi+1, seed), d = hash2(xi+1, yi+1, seed);
  return (a + (b-a)*u) + ((c + (d-c)*u) - (a + (b-a)*u))*v; // 0..1
}
```
Return centered: (vnoise*2-1).

fbm:
```js
function fbm(x, y, seed, oct=4, lac=2, gain=0.5){
  let a=1, f=1, s=0, norm=0;
  for(let i=0;i<oct;i++){ s += a*vnoiseC(x*f, y*f, seed+i*101); norm+=a; a*=gain; f*=lac; }
  return s/norm; // ~[-1,1]
}
```

**Height function:**

```js
const SX=128, SZ=128, SY=64;
const WATER = 12; // water surface at y=WATER (top face). Water blocks occupy up to WATER-1.
const worldOff = SX/2; // centered coords shift

function elevation(x, z){ // x,z in centered coords; returns continuous elevation (float, block-top height)
  const wx = x + worldOff, wz = z + worldOff; // 0..128
  const cont = fbm(wx*0.0065, wz*0.0065, 11, 4);
  const t = wz / SZ;                 // 0 north(-z? wait
```
Hmm careful: centered coords: z_center ∈ [-64,64]; z_c=-64 ↔ wz=0. Mountains at low wz (north, -z). t = wz/SZ ∈ [0,1], 0 at north. dirBias = 1 - 2t? At wz=0 → +1 (mountains), wz=128 → -1 (sea). But a pure linear ramp plus noise: e = cont*0.6 + (1-2t)*0.5. At north edge: e ≈ 0.6c + 0.5 ∈ [−0.1, 1.1]; mostly high. At south: e ≈ 0.6c − 0.5 ∈ [−1.1, 0.1] mostly sea. Middle: transition zone with beaches around e≈0. Should give sea in southern ~35%, mountains northern ~30%, hills between. Also want a bay indenting the coast for a nicer beach shot — the cont noise handles coastline variation (cont large positive at mid-south could create land; large negative at mid-north could create a northern bay/lake — nice: an inland lake or fjord).

Elevation mapping:
```js
const hills = fbm(wx*0.02, wz*0.02, 47, 4);
const det = fbm(wx*0.065, wz*0.065, 83, 3);
let e = cont*0.62 + (1-2*t)*0.5;
let h;
if(e < 0){
  const d = Math.min(1, -e/0.9);
  h = WATER - 1.5 - d*d*12 + hills*1.6 + det*1.2;
} else {
  const m = smoothstep(0.18, 0.85, e);
  h = WATER + 1.2 + e*13*(0.7+0.45*hills) + m*m*20*(0.85+0.4*hills) + det*1.6;
}
return h;
```
Estimates: sea: h ∈ [12-1.5-12-2.8, 12-1.5+2.8] = [-4.3, 13.3] → shallow near coast (e slightly<0 → d small → h≈10.5±) — wait at e→0⁻, h ≈ 10.5 ± 2.8 → could be above WATER=12? 13.3 > 12 → creates land; that's okay — coastline where e crosses 0 gets h crossing ~12 — beach forms near e≈0. Actually land side e>0: h = 12+1.2 + small → ≥ ~12.2+... at e=0.05: 13.2 + e*13*(...)≈ +0.65 → ~13.9±hills... hmm at e=0.05, e*13*(0.7+0.45*hills) with hills∈[-1,1]: 0.65*(0.25..1.15)=0.16..0.75; det ±1.6 → h ∈ [12+1.2+0.16-1.6, ...+0.75+1.6] = [11.76, 15.5]. So shoreline straddles water level 12 — beaches and tiny islets. Good.

Mountains: e up to 1.11: m=1, h = 12+1.2 + 14.4*(0.7+0.45h) + 20*(0.85+0.4h) + ±1.6 ≈ 13.2 + [10..15] + [17..25] + ±1.6 → up to ~54.8, min ~ 39. So deep-north always high mountains ~40–55 — maybe too uniformly high? cont*0.62 with cont as fbm ~[-0.8,0.8] typical → e at north = 0.5 + [-0.5,0.5] → [0,1] — varies; m = smoothstep(0.18,0.85,e) varies → mountains range ~25–50. Fine. Clamp h to [3, 52].

smoothstep helper needed.

Block typing per column (integer H = clamp(round? floor)):
```js
H = Math.max(3, Math.min(52, Math.floor(h)));  // top solid block y = H? 
```
Define solid blocks y=0..H-1? or 0..H? Let me define H = number of solid blocks → top block at y=H-1. Then water fills y=H..WATER-1 when H < WATER; top water face at y=WATER. Beach if H-1 == WATER → top block at y=12? hmm let me recompute: if top solid at y=H-1 and water surface at y=WATER: land at/below water when H-1 <= WATER-1 i.e. H <= WATER. Dry land: H ≥ WATER+1 (top block y ≥ WATER). Beach: top block y in {WATER, WATER+1} → H in {13, 14} → sand. Wait if H = WATER+1 → top block y=12 = WATER → that block's top face at y=13 = water level +1? Water surface at y=WATER=12 means top water face at y=12.0 and water blocks occupy y=11 (when H=12: blocks 0..11, water at y=11? no: water fills y=H..WATER-1 = 12..11 = empty → H=12 means top solid at 11, top solid face at 12.0 == water surface exactly → shoreline exactly at water level. H=13 → top solid y=12, face at 13 — one above water. Let me simplify: water surface y_s = WATER (12.0). Column dry if H ≥ 13. Beach when H ∈ {13, 14} (top y 12 or 13, i.e., 0–1 above water) → sand. Underwater: sand if H ≥ 9 (shallow), else stone floor? deep floor mix dirt/stone. Grass if H ≥ 15. Snow if H ≥ 34 + dither*4 (dither hash ±2 → 32..38). Stone band if H ≥ 28 + dither*4 (rocky below snow). Steep slope → stone: compute gradient of elevation function: |elev(x+1)-elev(x-1)| + |elev(z+1)-elev(z-1)| — expensive (4 extra fbm evals per column × 16k columns = fine, 64k evals ~ ok. fbm 4 oct = 16 lattice hashes → ~1M hash calls, trivial).

Actually the elevation function evaluated per column already; gradient doubles-ish cost — fine (startup < 200ms).

Under-column composition: y=0..2 stone (bedrockish), then stone up to H-4, dirt for H-3..H-2, top block per biome. For sand columns: sand top 3 deep then stone. Snow columns: snow top, stone below (or dirt then stone). Simple rules:

```
type(H, y):
 if y > H-1: (air or water)
 top block t0:
   if H >= snowLine(x,z): SNOW
   elif H >= rockLine(x,z) or steep: STONE
   elif H >= 15: GRASS
   elif H >= 13: SAND
   elif H >= 9: SAND (underwater shallow)
   else: DIRT? or STONE — deep sea floor: DIRT with stone patches → use STONE? Minecraft deep = gravel; DIRT looks fine underwater. Use DIRT for H in [6..9), STONE below 6? simple: else DIRT.
 sub-blocks:
   if top SAND → sand for y ≥ H-3, stone below
   elif top GRASS → dirt for y ≥ H-3 (H-3..H-2), stone below
   elif SNOW → stone below (with dirt band H-3..H-2? stone fine)
   else stone/dirt mix: use stone
```

Trees on GRASS tops with H ≥ 16 (above beach), not steep, forest noise gating, spacing via local-min hash. Tree placement writes WOOD at y=H..H+th-1 (wait top solid at H-1, so trunk starts at y=H). Leaves as described.

Also I need the voxel getter/setter: idx = (y*SZ + z)*SX + x.

**Mesher:**

For chunked meshing: chunks of 32×32 columns → 4×4 = 16 chunks. Each chunk mesh includes all blocks whose (x,z) in chunk — including full column height. Neighbor lookups cross chunk borders via global array — fine.

Face tables — I'll write a compact face descriptor:

```js
// For each face: normal, 4 corner offsets (CCW from outside), uv per corner
const FACES = [
 { // +x
   dir:[1,0,0],
   corners:[[1,0,0],[1,1,0],[1,1,1],[1,0,1]],
   uvs:[[0,0],[0,1],[1,1],[1,0]], // u along z
   shade:0.80
 },
 { // -x
   dir:[-1,0,0],
   corners:[[0,0,1],[0,1,1],[0,1,0],[0,0,0]],
   uvs:[[0,0],[0,1],[1,1],[1,0]],
   shade:0.80
 },
 { // +y
   dir:[0,1,0],
   corners:[[0,1,0],[0,1,1],[1,1,1],[1,1,0]],
   uvs:[[0,0],[0,1],[1,1],[1,0]],
   shade:1.0
 },
 { // -y
   dir:[0,-1,0],
   corners:[[0,0,0],[1,0,0],[1,0,1],[0,0,1]],
   uvs:[[0,0],[1,0],[1,1],[0,1]],
   shade:0.5
 },
 { // +z
   dir:[0,0,1],
   corners:[[0,0,1],[1,0,1],[1,1,1],[0,1,1]],
   uvs:[[0,0],[1,0],[1,1],[0,1]],
   shade:0.66
 },
 { // -z
   dir:[0,0,-1],
   corners:[[1,0,0],[0,0,0],[0,1,0],[1,1,0]],
   uvs:[[0,0],[1,0],[1,1],[0,1]],
   shade:0.66
 }
];
```
Hmm — differentiate x-faces vs z-faces shades for more depth: +x/-x 0.78, +z/-z 0.62? Minecraft uses: top 1.0, bottom 0.5, x-sides 0.6, z-sides 0.8 (N/S vs E/W differ). I'll do x:0.62, z:0.8? Wait — but then which is which relative to sun? Doesn't matter (baked). Use +x/-x: 0.72, +z/-z: 0.82? Minecraft: E/W faces 0.6, N/S 0.8. I'll pick x:0.65, z:0.82 for clear cube reading. Hmm, per-face distinct also helps chunk readability. Final: top 1.0, bottom 0.55, ±x 0.68, ±z 0.84.

Wait — shading note: with MeshBasicMaterial and vertexColors, texture * color. Texture tiles drawn at full brightness; shade multiplies. Good.

AO occluder check: opaque = type not in {AIR, WATER}. (Leaves occlude — acceptable, gives trees depth.)

UV atlas mapping: tile index per (blockType, face): 
```
const TILE = {
 1: {top:0, side:1, bottom:2},   // grass: 0 grassTop, 1 grassSide, 2 dirt
 2: {all:2},  // dirt
 3: {all:3},  // stone
 4: {all:4},  // sand
 5: {all:5},  // snow
 6: {top:7,bottom:7,side:6}, // wood: 6 bark, 7 rings
 7: {all:8},  // leaves
};
```
Atlas layout: indices 0..8 → col=i%4, row=floor(i/4). Atlas canvas 4 tiles × 16px = 64px wide, 2 rows needed → 64×32? Make 64×64 (4 rows) for headroom. uv: tileUV(idx, corner u,v): 
```
const tu = (idx % 4) / 4, tv = 1 - (Math.floor(idx/4)+1)/4; // row from top: canvas row 0 at top of image; texture v=1 at top (flipY true default for CanvasTexture? THREE.CanvasTexture flipY default true). With flipY=true, v=1 corresponds to canvas y=0 (top). So tile row 0 (top of canvas) → v range [0.75, 1]. tv_top = 1 - row/4? Let me: row r occupies canvas y ∈ [r*16, (r+1)*16) → in texture v (flipY): v = 1 - y/64 → v ∈ [1-(r+1)*0.25, 1-r*0.25]. So vMin = 1-(r+1)*0.25 = 0.75 - r*0.25... for r=0: [0.75,1]. u = col*0.25 + u*0.25.
```
With half-texel inset: u ∈ [col*0.25 + eps, (col+1)*0.25 - eps], eps = 0.5/64 = 0.0078125.

Compute per face corner: `u = uMin + cu*(uMax-uMin)`, similarly v. 

**Water meshing:** iterate columns; if H < WATER (water exists: blocks y=H..WATER-1): add top face at y=WATER (corners at (x..x+1, WATER, z..z+1)) — with normal +y, shade 1.0 (or 0.95). Also check: if column is water, neighbor columns at map edge → side faces from y=H..WATER-1 on border; and interior neighbors always water-or-solid as analyzed. Border side faces: for x=0: face -x at plane x=0 for y in [H..WATER-1]... visible from outside only. Include for slab look. Also underside of water at map border? Not visible from outside bottom (camera stays above y≈3? Camera min y = groundRef+2.5 ≥ 5+... sea floor min 3 → camera over deep sea at y≈ WATER+3=15 — never below. Skip undersides.

Wait, also water top face where adjacent column has H ≥ WATER (solid shore) — water top at y=12 abuts solid block at y=12.. — the sand block side is rendered (since neighbor of sand is water → face rendered). Good, no gap: water top plane at y=12, sand block occupies y=12..13 with side face rendered down to y=12. Good.

Water UVs: world-based: u = (x+corner)/4 etc. with texture repeat. Water texture separate 32×32 canvas, RepeatWrapping. Set water geometry UV = worldpos*0.25. Both top and side faces need reasonable UVs — sides: u along horizontal, v along y (0..1 scaled). Fine.

Water material: MeshBasicMaterial({map: waterTex, transparent:true, opacity:0.72, vertexColors:true, depthWrite:false? }) — depthWrite false avoids sorting issues with itself; but then terrain behind water renders fine since opaque drawn first (three sorts transparent last). Multiple water top faces coplanar — overlapping not an issue with same material. But depthWrite:false lets far water show through near water — they're coplanar, no overlap. Keep depthWrite:false to be safe with clouds/sun? Clouds are above. OK.

Vertex colors for water: slight depth-based darkening? Could color water top faces by depth (deep = darker blue via vertex color 0.75, shallow 1.0) — nice touch: depth = WATER - H → shade = clamp(1 - depth*0.03, 0.7, 1). I'll include.

**Clouds:**

```
cell = 8 (world units), grid N=44 × M=44 cells covering 352×352 (world 128 + margin), centered at origin. Occupancy periodic in x with period 44 cells → wrap seamless. To be safe on z too (no drift in z, but coverage beyond fog needed): z range just needs to cover fog radius ~260 → 352 wide enough centered.
occupancy: n = smoothedHash: base = hash2(i mod 44, j, 999); use value-noise-like: v = (h(i,j)+h(i+1,j)+h(i,j+1)+h(i+1,j+1))/4 at coarser? I'll do: occ if fbm-like periodic noise > 0.55: sample pnoise = vnoise(i*0.35, j*0.35, seed) with lattice wrapped mod? My vnoise isn't periodic. Simplest periodic blobby: occ(i,j) = blockno where block = (h(i,j) > 0.6) then apply morphological: occ if count of "on" in 3×3 ≥ 5? Since I generate once, I can do two passes over the grid. That yields clumps. Also then delete isolated? The ≥5 rule handles it.
Each occupied cell → box geometry (cell*0.98 wide, 1.6? thick... Minecraft clouds ~4 thick relative to 12 block cells; cell=8 → thickness 1.6? Let me: thickness 1.2, y=78. Actually give slight thickness 1.5 and also a second sparse layer at y=86 for depth? Keep one layer, maybe double-thickness if neighbor below/above... keep simple single layer.
Merged: build BufferGeometry manually or use THREE.BoxGeometry merged via arrays. I'll construct positions directly: for each cell, push a cuboid (only faces? all 6 faces of thin box — cheap, few hundred boxes × 6 faces × 2 tri = fine). Actually only need top, bottom, and 4 sides when neighbor cell empty — cull like voxels for nicer look: bottom face shade 0.85, top 1.0, sides 0.92. Vertex colors → white cloud with subtle shading. Material MeshBasicMaterial({vertexColors:true, transparent:true, opacity:0.55, depthWrite:false, fog:true}).
Cloud drift: group.position.x = -mod(t*1.4, 44*8=352). Pattern periodic → seamless.
```

Clouds at y=78 with opacity 0.55 white against blue — good. depthWrite false + transparent → renders after opaque; against sky dome (renderOrder?). Sky dome: renderOrder -1? Dome is opaque-ish (ShaderMaterial, BackSide) drawn among opaque; depthWrite? Dome at radius 800 following camera; terrain closer writes depth; dome drawn with depthWrite true? If dome drawn first with depthWrite false and renderOrder very early, then terrain overwrites. Set dome.material.depthWrite=false, dome.renderOrder=-2, clouds renderOrder 1 (after water?) Transparent objects sorted by distance; water & clouds both transparent — three sorts back-to-front by distance; dome is not transparent (opaque list) — fine.

Sun: additive plane, renderOrder 2? Sun must draw after dome; it's transparent (additive) → drawn in transparent pass sorted with clouds/water. Sun at distance 700 → drawn first among transparents (farthest) — good, then clouds over it, water nearest. But water is at distance < sun always → drawn after sun → water over sun when looking through water toward sun — correct occlusion? Sun is behind everything (sky), so yes.

Sun should render behind clouds even when clouds nearer — sorted by depth → sun (700) first. 

Also: sun square plane must face camera → use THREE.Sprite? Sprite with additive material — sprites always face camera, easy. SpriteMaterial({map: sunTex, fog:false... SpriteMaterial has fog option? It has fog property — set fog:false? SpriteMaterial doesn't inherit scene fog? It does support fog:false. Set transparent, depthWrite false, depthTest true? If depthTest true and dome wrote no depth, sun passes depth vs terrain (mountains occlude sun → good: sun should set behind mountains? Sun drawn in transparent pass after opaque with depthTest → occluded by mountains correctly. But sprite at distance 700 with far plane 1200 ok.

Alternatively make the sun a square (Minecraft sun is square!). A square sun is a charming Minecraft-authentic touch. Sprite with square texture (crisp white square with slight warm edge glow). I'll draw 64×64: centered square 26×26 pure white slightly warm (#fff7d0), plus soft radial falloff behind. Sprite scale ~ 90.

**Sky dome shader:**

```glsl
varying vec3 vDir; // world direction (position - cameraPos) — since dome centered on camera, use normalized local position
vertex: vDir = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0);
fragment:
 float h = normalize(vDir).y;
 vec3 sky = mix(horizonColor, zenithColor, pow(clamp(h, 0.0, 1.0), 0.55));
 below horizon: mix(horizonColor, horizonColor*0.9?, ...) — below horizon (h<0) use horizon color slightly darkened toward fog color: keep horizonColor for h<0 (fog covers terrain anyway).
 float sunAmt = pow(clamp(dot(normalize(vDir), sunDir),0.,1.), 30.0);? 
 sun glow subtle: sky += sunColor * (0.35*pow(sdot,8) + 0.5*pow(sdot,90)); — gives halo.
```
Colors: zenith #2f6ecc? Let me pick a pleasing daytime palette: zenith rgb(0.30,0.56,0.92)? and horizon rgb(0.78,0.88,0.96) near white-blue. Fog color: rgb(0.80,0.88,0.95) matching horizon slightly. Actually fog color should equal the sky color near horizon in typical view directions — horizon color ~ (0.79,0.87,0.94). Use fog #c6dff0 ≈ (0.776,0.874,0.941). zenith #3d7dd6? Let me set zenith (0.23,0.46,0.82) → #3b75d1. Hmm keep it vibrant but not purple. Fine.

The sun glow in shader plus sprite sun disc — combined looks natural.

**Camera path details:**

groundRef(x,z): 
```js
function groundRef(x,z){
  const h = elevation(x,z); // continuous
  const H = Math.max(3, Math.min(52, Math.floor(h)));
  return Math.max(H, WATER); // water surface counts as ground for flying (fly above water surface)
}
```
For sea area, groundRef = WATER=12 → clearance 2.5 → camera y≈14.5, skimming water. 

Control points (centered coords). World extents ±64. Sea south (z>~30 typically? e<0 south half; shoreline meanders around z ~ 10..40 given noise). Mountains north.

Let me define route (I'll snap some at runtime):

```js
const CP = [
 [-30,  92, 3.2],   // deep-ish sea SW, low
 [ 18,  80, 3.0],   // sea, approaching coast
 [ 46,  56, 3.0],   // bay/beach skim
 [ 56,  28, 6.5],   // grass hills east
 [ 44,   2, 5.0],   // descend into valley (snapped to pass)
 [ 18, -18, 5.5],   // valley weave
 [ -8, -30, 16.0],  // climb toward peak flank (snapped near peak)
 [ -34, -40, 26.0], // high beside summit — vista
 [ -56, -16, 14.0], // curving down west ridge
 [ -58,  18, 6.0],  // west shore
 [ -50,  52, 4.0],  // along coast/sea
 [ -18,  84, 3.4],  // out to sea heading back east — wait first point [-30,92] close; fine (closed loop)
];
```
That's 12 points, closed. Runtime snapping: 
- valley pass: along the segment x from 56→18 crossing z around 2..-18: find minimal ground along the straight line between CP[3] and CP[5] sampled, set CP[4] to that min point, clearance 4.5. Implementation: sample s∈[0,1] along line p3→p5 (50 steps), pick s minimizing groundRef, set CP[4] = lerp(p3,p5,s), cl=5.0.
- peak flank: find peak (max elevation over grid, smoothed 3×3? just max of H). CP[6] = point at distance ~14 from peak on the south-east side: peak + normalized(peak→center? ) hmm: approach from east: CP[6] = peak + (dirToPeakFrom CP[5] reversed...). Simple: CP[6] = peakPos + (10, 12) offset toward camera side: offset direction from peak toward CP[5] normalized × 16 → keeps continuity of approach. cl=15.
- CP[7]: high vista: offset from peak opposite side × 30, cl = 28 (well above peak? peak H ~ up to 52; cl 28 above groundRef at that xz (which is lower than peak) → camera y = ground+28 could still be below peak top → looking across at summit — good "beside the summit". Ensure camera y > peak H - 5? Not necessary; being beside a 50-high summit at y=ground(~40)+28=68? ground at CP[7] maybe 35 → 63 — above peak. Hmm "beside summit" nicer slightly below top: I'd rather CP[7] cl=20 → y≈55 near summit height. Let me set cl 20 and rely on look target = peak top. Then CP[8] descend cl 13.

Then build samples:
```js
const baseCurve = new THREE.CatmullRomCurve3(cps.map(p=>new THREE.Vector3(p[0],0,p[1])), true, 'centripetal', 0.5);
const N=1024;
for i: pos=baseCurve.getPointAt(i/N); g=groundRef(pos.x,pos.z); baseY[i]=g + clearance[i] where clearance interpolated from control points — how to interpolate clearance along samples? Each sample's nearest control point? Better: compute clearance array along samples by mapping: for each control point, its parameter u_i on curve (getUtoTmapping? complicated). Alternative: clearance function = smooth function of position: cl(x,z) = max over control points of cl_j * weight(dist)? Simplest: clearance constant 4.0 for all, EXCEPT specified high points... 

Alternative simpler approach: skip separate clearance interpolation: compute y_i = max over j of (g_j + cl_j) * falloff(dist_i, cp_j)? Messy.

Cleaner: build "route clearance" via: cl_i = lerp based on distance to nearest control points: For sample i, find its two bracketing control points by projection... Overkill.

Pragmatic: define clearance per control point; compute per-sample clearance by Catmull-interpolating a 1D function over the same parameterization: create THREE.CatmullRomCurve3 with points (cp.x, cp.cl, cp.z)?? Trick: make a second curve with Y=clearance and sample it with same u → clearance_i = clCurve.getPointAt(i/N).y. Clever and simple! baseCurve from (x, 0, z); clCurve from (x, cl, z) same points → getPointAt(i/N).y gives interpolated clearance. 

Then y_i = max(groundRef(x_i,z_i) + cl_i, yRaw?) — there's no other y source; y = g+cl directly, then smoothing pass to round steps:
```
for iter in 0..2: for i: y[i] = (y[i-1]+2y[i]+y[i+1])/4 (circular)
then re-enforce y[i] = max(y[i], g_i + cl_i)  (re-raise)
```
After re-enforce, small kinks possible; acceptable. Actually smooth-then-enforce-then-smooth-once? Enforce last = guarantees clearance. Kinks minor since g varies smoothly except block quantization (floor) → steps of 1 unit; cl smooth; y=g+cl has 1-unit steps — smoothing pass reduces to gentle slopes; enforcing max reintroduces ≤1-unit step only where smoothing lowered below minimum — then final small smoothing without re-enforce? A final half-pass then enforce... The 1-unit terracing in camera height is probably imperceptible (camera also moves in x,z continuously, and look direction dominates). I'll do: y = max(g+cl); smooth 2 passes; enforce; smooth 1 pass with weight 0.5 (y = (y_prev+y_next)/2*0.35 + y*0.65...). Then tiny violations ≤ ~0.5 unit — acceptable (clearance had margin? cl values ~3 over water — cutting 0.5 into a 3-unit clearance over flat water fine since water is flat: g constant → smoothing exact, no violation. On hills, cl ≥ 4.5 gives margin.) Good: over water cl 3, terrain flat → fine; hills cl ≥ 4.5 > violation ~0.5. Safe.

Final curve: CatmullRomCurve3(points every 3rd sample? Use all 1024? getPointAt on 1024-point closed curve: arc-length precompute does 200 divisions default... For a curve with 1024 segments, arcLengthDivisions default 200 → inaccurate param mapping? CatmullRomCurve3 arc length computed via getLengths(divisions) — I can set curve.arcLengthDivisions = 2000 before use. Fine. Or simply skip getPointAt and use getPoint(t) (uniform in segment parameter) — speed varies slightly with segment lengths; segments from dense uniform-arc samples → nearly uniform already! Since samples are equally spaced by arc length (from baseCurve.getPointAt), building a curve through them and using getPoint(t) gives near-constant speed. I'll use getPoint (no arc-length recompute) on a curve built from every 4th sample (256 pts, closed). Or even simpler: interpolate the sample array directly: u∈[0,1) → f = u*N, i0=floor, frac, lerp positions — linear interp of dense samples is smooth enough (0.6-unit spacing) — direction changes tiny per step; look target provides most of motion feel. I'll do direct lerp — cheap & robust. Positions array of Vector3, function samplePath(u) → lerped pos. Plus add bob: pos.y += sin(t*0.6)*0.35.

Look targets: gather POIs at runtime:
- peak top: (px, Hpeak+3, pz)
- beach: find along southern coast: scan z from south edge upward at x≈20: first column with H ≥ 13 → point (x, H+2, z-6)? Simpler: coastline point nearest to (30, ?, 40): scan columns where H==13... I'll find any beach: iterate grid, find cell with H==WATER+1 (=13) closest to (30,45)? Store.
- forest: tree with most trees within radius 12 → its position, y=H+8.
- lake/inland water: column with H ≤ WATER-6 farthest from south edge → deep water POI (northern bay if exists) — y = WATER+2. If none (all water in south), pick deep sea point: the water column with min H (deepest) → y=WATER+2.
- west ridge point: (-45, g+10, -5)?
- bay/sea open: (0, WATER+2, 70)?

Look curve control points (closed): sequence roughly matching camera route order so target stays generally ahead:
1. (25, ?, 62) coast approach — y = groundRef+3
2. beach POI +y2
3. (40, ?, 5) inland hills y=g+4
4. valley pass point y=g+3
5. peak top (px, py+2, pz)
6. peak again?? — looking at peak while passing: target 5 = summit; as camera goes CP[6]→CP[7]→CP[8], target stays summit then moves to west ridge:
7. (-55, g+8, -10) west ridge
8. deep water / open sea (−10, WATER+2, 75)?
Then closes back to 1. Order roughly follows camera's route (which goes CCW? route: start south-west sea (−30,92) → east (18,80) → (46,56) coast → north through hills → peak NW → west ridge → south along west coast → back. Target curve order should also go east-coast → hills → peak → west → sea. Matches list above. Good.

Look sampling: same technique — dense samples via getPointAt on its own closed curve, then direct lerp; add slight sway: target += perpendicular offset sin? I'll add: offset target by sin(t*0.23)*5 along the camera-right direction — creates gentle "looking around". Hmm — could cause target drift into terrain; amplitude 5 fine.

Actually simpler sway: look target y += sin(t*0.5)*1.5, x/z sway via rotating target around camera by small angle: angle = sin(t*0.21)*0.12 rad — rotate (target-camera) around Y by that angle. Elegant "glance" effect. I'll implement rotation of the look vector.

FOV: 60. Maybe slight dynamic FOV for speed feel? Keep 62 constant... A subtle FOV breathing (60→66 at fast low segments) — skip, keep simple.

**Camera up / roll:** none.

**Water animation:** map offset drift; also could scale UV. fine.

**Leaves sway?** Static (baked) — fine.

**Startup flow:** everything synchronous; ~1M voxel fill + meshing ~ maybe 150–400ms — acceptable before first frame. Could show nothing (black) briefly — fine, or set clear color early. OK.

**Now — texture atlas drawing:**

```js
function makeAtlas(){
 const c = document.createElement('canvas'); c.width=64; c.height=64; // 4x4 tiles
 const g = c.getContext('2d');
 const rng = mulberry32(1337);
 function px(tx,ty,x,y,r,gg,b){ g.fillStyle=`rgb(${r},${gg},${b})`; g.fillRect(tx*16+x, ty*16+y,1,1); }
 // helpers: drawTile(i, fn) where fn(x,y) returns [r,g,b]
}
```
Tile painters:

```js
function speck(base, amt){ // vary
  const v = (rng()*2-1)*amt;
  return [clamp base.r+v, ...]
}
```
- grassTop (tile 0): base (104,168,70), variation ±14, occasionally darker blade pixels (10% chance multiply 0.85).
- grassSide (1): dirt base (138,98,63)±12; top rows: grass overhang: for x: depth = 2 + (hash based 0..2): if y < depth → grass color (use same grass palette darker slightly (94,150,62)); plus a 1px darker green at boundary occasionally.
- dirt (2): (138,98,63)±14 with 8% dark spots (100,70,45).
- stone (3): (128,128,128)±10, 10% darker (100), 5% lighter (150).
- sand (4): (218,205,158)±10 with 6% darker grains.
- snow (5): (238,244,248)±6, some (222,232,240) patches.
- wood bark (6): vertical striping: base per column x: colBase = (98,74,46) shifted by column hash ±10; per pixel ±6; occasional dark knot? plus horizontal breaks 5%.
- wood rings (7): center 16×16: dist = max(|x-7.5|,|y-7.5|) (square rings): ring color alternating light (176,142,94)/(128,100,64) by ring index parity, plus noise.
- leaves (8): base (64,124,48)? plus variation ±16; 15% much darker (36,80,30) faking depth; 8% lighter highlight (88,150,66).

Water texture (separate 32×32): base (54,118,198)? Minecraft water more like (47,93,190). Per-pixel ±8; add horizontal streak lighter rows: for a few random rows y: 30% chance row has lighter pixels (70,140,220) for random runs. Simple noise-based. NearestFilter, RepeatWrapping.

Sun texture 64×64: radial: core square? Let me do: soft radial glow (rgba warm white) drawn with radial gradient from center: stops: 0 → rgba(255,244,214,1) small, then falloff; plus crisp square: fillRect centered 22×22 pure #fff. Since additive, colors add over sky. Might look great: square sun (Minecraft) + subtle halo.

Now check canvas → THREE.CanvasTexture with magFilter Nearest, minFilter Linear? Hmm — for the atlas I said minFilter Linear + no mipmaps: set `tex.generateMipmaps=false; tex.minFilter=THREE.LinearFilter; tex.magFilter=THREE.NearestFilter;` colorSpace: THREE.SRGBColorSpace (r186 default renderer outputColorSpace srgb; textures need colorSpace set for correct color). Set atlas.colorSpace = THREE.SRGBColorSpace, water too, sun too (sun additive fine either).

Renderer: `new THREE.WebGLRenderer({antialias:true})`, outputColorSpace default SRGB. Vertex colors treated linear; my shade values linear — multiplying texture (srgb→linear) by color — fine.

**Geometry building code:**

```js
function buildWorld(){
 const vox = new Uint8Array(SX*SY*SZ);
 // fill columns
 for x,z: compute elev etc, fill types
 // trees
 // meshing
}
```
Index: `(y*SZ + z)*SX + x` → idx(x,y,z)= x + SX*(z + SZ*y). get(x,y,z): bounds check → 0 (air) outside (borders exposed) except y<0 treat solid (never rendered bottom at y=0? bottom face at y=0: neighbor y=-1 → treat as air → renders bottom face of the world slab. From below it's visible; camera never below. Could treat y<0 as solid to cull bottom faces — do that (saves 16k faces).

Mesher loop per chunk:
```js
for cx in 0..3, cz in 0..3:
 arrays pos[], col[], uv[], idx[]
 for x in cx*32.. : for z...: for y in 0..SY-1:
   t = get(x,y,z); if !t || t==WATER_TYPE skip (water handled separately)
   for f in 6 faces:
     n = get(x+dx, y+dy, z+dz)
     if n==0 || n==WATER: emit face
```
Emit: compute AO per corner (need neighbor sampling: for corner c (0/1 per axis), tangent axes = the two non-normal axes; s_a = c[a]?1:-1; side1 = get(x+dir + t1vec*s1 ...) — careful: base cell for AO sampling = (x,y,z)+dir (the air block in front of the face). Then offsets from that cell along tangent axes with signs. occl if opaque solid (not air/water).

Vertex position = (x-64 + corner[0], y + corner[1], z-64 + corner[2]) — center offset −64 for x,z. (worldOff=64.)

Color = shade*aoCurve[ao]; but also slight variation per block type? Grass top slightly varied via texture already. Add subtle per-block color jitter? Textures have variation; skip.

UV per corner from face table + tile.

Indices with flip rule.

Per-chunk BufferGeometry:
```js
geo.setAttribute('position', new THREE.Float32BufferAttribute(pos,3));
geo.setAttribute('color', ...,3); geo.setAttribute('uv',...,2); geo.setIndex(idx);
geo.computeBoundingSphere(); // or set manually: bounding box known
```
Mesh with atlasMat = new THREE.MeshBasicMaterial({map:atlasTex, vertexColors:true}); mesh.frustumCulled default true w/ bounding sphere — good.

Water builder similar (single pass over columns, top faces + border sides), one geometry.

Count check: fine.

**Clouds builder:**

```js
const CELL=8, CN=48; // covers 384
grid occ via hash + 3x3 smoothing as described.
geometry: for each occ cell (i,j) → world x0 = (i-CN/2)*CELL, z0=(j-CN/2)*CELL (+ offset so world centered), y base 76.
push faces with culling vs neighbors (top always, bottom always, sides if neighbor empty).
thickness T=1.6.
colors: top 1.0, bottom 0.82, sides 0.9.
```
Material: MeshBasicMaterial({vertexColors:true, transparent:true, opacity:0.5, depthWrite:false}). Drift group.

One nuance: transparent cloud over water: both transparent; sorting by distance — cloud far above; three sorts by distance to camera; water below clouds nearer? If camera looks up through cloud at sky fine; looking down at water through cloud? Cloud at y=76+, camera below → cloud drawn after water if farther — distance from camera to cloud mesh center vs water center — sorting is per-object; cloud merged mesh center could be nearer than water center... water mesh bounding sphere center is world center (0, ~12, 0); cloud center (0,77,0). If camera at (0,20,40): distance to water center ~ sqrt(64+400+1600)?? whatever — mis-sorting between two transparents shows only where they overlap on screen: looking down through a cloud to water — cloud drawn first if sorted farther; then water over it → water would hide cloud?? Water is semi-transparent so cloud would still show through, slightly — artifacts minor. To reduce: cloud opacity low anyway. Alternatively render clouds with renderOrder=10 (always last) → clouds drawn over water — when looking down through cloud: cloud over water = correct-ish (cloud is above water from any camera below it? If camera above cloud looking down at water: correct order would be water then cloud? From above, cloud is nearer → should draw last → renderOrder 10 correct. From below, cloud farther → should draw first (before water) but renderOrder forces last → cloud drawn over water — since both semi-transparent, blending order swapped: result = water*(1-a_c)... slight brightness difference where overlapping; acceptable. I'll set clouds renderOrder 5, water renderOrder 1... wait renderOrder overrides sorting within transparent list (sorted by renderOrder groups then distance). Sun sprite renderOrder? Sun far, should be drawn before water/clouds: set sun.renderOrder = 0 (first among transparents) — but transparent list sorted: renderOrder ascending then back-to-front. Sun renderOrder 0 → drawn before water(1)/clouds(5). Good.

**Animation loop:**

```js
function animate(ts){
 requestAnimationFrame(animate);
 const t = ts*0.001;
 // camera
 const u = ((t/LOOP) % 1 + 1) % 1;
 camPos = samplePath(u); camPos.y += Math.sin(t*0.55)*0.35;
 target = sampleLook((u+0.045)%1);
 // sway: rotate look vector
 const v = target.sub(camPos); const ang = Math.sin(t*0.19)*0.14; rotate around Y: 
 v.applyAxisAngle(up, ang); camera.position.copy(camPos); camera.lookAt(camPos + v) — or camera.lookAt(tmp.copy(camPos).add(v)).
 // sky dome follows
 dome.position.copy(camera.position);
 // clouds
 cloudGroup.position.x = -(((t*1.5) % CLOUDSPAN)+CLOUDSPAN)%CLOUDSPAN;
 // water
 waterTex.offset.set(Math.sin(t*0.02)?, ...) — simple linear drift: offset.x = (t*0.01)%1, offset.y=(t*0.006)%1.
 renderer.render(scene,camera);
}
```
t starts at first rAF timestamp (could be ~0.5s after load) — path starts at u≈0 — beginning of sea shot. Good.

Look-ahead 0.045 of loop (~3.2s ahead ≈ 22 units along path) — target near path ahead. But my look curve is separate POI-based, not the path — param lead on POI curve is fine: it moves target through POIs at its own schedule.

Hmm, one concern: the look curve parametrization vs camera route timing mismatch — e.g., camera passes peak at u≈0.30 (t≈21.6s) but look curve reaches peak POI at its own u fraction depending on POI spacing (arc-length). Arc-length parametrization of look curve distributes by distance between POIs — POIs are spread around the island similar to route → roughly aligned. I'll nudge lead per segment? Simplify: since target curve is closed and roughly parallels the camera route, lead 0.06 gives target ≈ ahead-right of camera most of the time. During the peak segment, I want camera looking AT the summit for a while — with a smooth target curve passing through summit point, target lingers near summit only briefly (arc-length through). To linger: duplicate the summit POI? CatmullRom through [.., peak, peak, ..] creates zero-length segments (arc-length param gets weird with duplicate points — getPointAt handles zero-length segments poorly but doesn't crash; tangents fine-ish). Alternative: insert two points near summit offset slightly (peak+(-4,0,2), peak+(-8,0,-2)?) so the target slows near the summit... Actually with arc-length parametrization, spacing controls dwell: two close points around summit = target dwells near summit region while camera approaches. I'll add summit-adjacent points: p_peak1 = peak+(3,2,4), p_peak2 = peak+(-3,2,2)? Hmm — risk overengineering without visual test.

Alternative robust approach for look: target = sampleLook with its own u lead; PLUS when camera is within range of the peak segment (u∈[0.26,0.40]), blend target toward summit by factor w = smoothstep — a "lock-on" blend. That guarantees the money shot: as camera climbs past the flank, view locks to summit, then releases. Blend: target' = lerp(targetCurvePoint, summitPoint, w(u)). Compute w from u window with smooth in/out. Similarly early: during u∈[0.0,0.14] lock toward the coast/beach point (w up to 0.5) so opening frame shows shoreline. I'll implement generic "focus moments": list of {u0,u1,point,strength} with smoothstep ramps; final target = lerp(baseTarget, focus.point, focusWeight). This is clean and controllable. Focus list:
- {0.00–0.10, coast point (beach POI), s=0.7}: opening over sea → gaze at shore/island.
- {0.13–0.22, forest POI, 0.65}: passing over hills → glance at grove.
- {0.24–0.36, summit, 0.95}: peak reveal.
- {0.40–0.50, west ridge valley/sea? maybe deep-water POI 0.6}: after vista, look down the west shore.
- {0.55–0.68, deep sea/lake 0.6}? 
- maybe {0.7–0.8, coast 0.5}, {0.85–0.97, sea horizon? use water POI south 0.5}.

With loop 72s: u*72: 0–7.2 coast; 9.4–15.8 forest; 17.3–25.9 summit; 28.8–36 ridge; ... Good — summit reveal lands ~18–26s, vista after. First 30s covered: sea, beach, hills, forest, summit, wide vista (from high CP at u~0.33–0.42 = 24–30s looking around west ridge/sea). 

The base look curve still adds motion between focuses.

Sway: apply small rotation after focus blending — amplitude 0.10 rad, freq 0.13 Hz? sin(t*0.8)*0.06 plus slower sin(t*0.29)*0.08 — combined organic. Fine.

**Fog & distances:** camera near 0.1, far 1500. Fog: new THREE.Fog(0xc8ddf0, 60, 240). Hmm — at wide vista (high camera y≈60, looking across 180 units of island): far edge heavily fogged — atmospheric, good. Water surface extends to edges — fog covers. Sun sprite at 700 → fully fogged if fog applied — SpriteMaterial fog:false? SpriteMaterial supports fog property (default true) — set fog:false.

Sky dome radius 900, camera far must exceed 900+70 → far=1400. Dome ShaderMaterial fog:false (no fog code anyway).

**Water at horizon vs fog:** water transparent material fog:true default → far water fades to fog color — but transparency + fog works (fog mixes toward fog color) — good.

**Clouds fog:** cloud material fog default true → distant clouds fade to fog color — but clouds high in sky against blue — fog color pale blue — acceptable.

**Vertex color space:** colors I set (shade) interpreted linear; final = sRGBTexture(linearized) * shade → output converted back to sRGB. Perceptually, shade 0.68 in linear ≈ 0.84 sRGB — fine, I'll tune values as sRGB-ish anyway: I'll just tune until looks right; choose top 1.0, z-sides 0.80, x-sides 0.66, bottom 0.5; aoCurve [0.42, 0.62, 0.8, 1.0] — these act in linear space; converted appears softer. Let me slightly strengthen: x-sides 0.60, ao [0.38,0.60,0.78,1.0]. Hmm hard to predict; go with: top 1.0, ±z 0.82, ±x 0.64, bottom 0.50; AO curve [0.42, 0.61, 0.80, 1.0]. Reasonable.

**Tree canopy leaves near chunk borders:** tree placement done globally before meshing; vox array holds leaves; mesher handles. Trees near chunk boundary: fine (global neighbor lookups).

**Determinism:** all noise seeded with constants → same world every load. Good for a "recordable" 30s window (consistent).

Let me also double check tree spacing rule: candidate if hash2(x,z,S=7)<density && forestNoise ok; then verify strict local min of hash2(x,z,S=8) over 5×5 neighborhood → spacing ≥2 apart? Local min over 5×5 ensures no other tree candidate within Chebyshev 2 (their hashes would need to be larger; if two adjacent both candidates, the smaller wins and the other is suppressed since it isn't a strict min... two cells: a < b: a is min (b in neighborhood, b>a → a strict min ok); b has a<b in neighborhood → not min → suppressed. Both equal? hash equal measure-zero. So min spacing 2 blocks between trunks. Canopies radius 2 will overlap → merged forests, fine (Minecraft-like). Density: candidates p≈0.05 in forest zones, suppressed to ~1/26 of 5×5 cells ≈ p_effective ~ 0.05/26?? No: local-min over 5×5 among random hashes: each cell independently candidate w.p. q; a candidate cell is kept if its hash is min over its 25-cell neighborhood — probability 1/25 (hash independent) → effective density q/25 per column?? That's wrong: kept density = P(cell is candidate AND min in 5×5) = q * (1/25) ≈ 0.05/25 = 0.002 → 128²*0.002 ≈ 33 trees in forest zones. Hmm a bit sparse; forest zones maybe 40% of land (~4000 columns) → 8 trees. Too few! Fix: don't gate on candidate-hash for all cells; instead: tree at (x,z) if h=hash2(x,z,7) < density AND h is local min over 5×5 of hash2(·,·,7). Then kept density = density/25... same math: candidates are cells with h<0.05; kept if min over neighborhood — but neighbors mostly aren't candidates; the min among *candidates* matters! Correction: b suppresses a only if b is also a candidate (hash<0.05) and b<a?? No — the rule "kept if h(x,z) < h(n) for all candidate neighbors n" — non-candidate neighbors can't host trees so they don't suppress. Correct rule: cell kept iff (h < density) and for all cells n in 5×5 (n≠cell) with h(n) < density: h(n) > h(cell). Probability: cell is candidate (q=0.05); among the other 24 cells, expected candidates = 24q = 1.2; P(all candidates in neighborhood have larger hash) = E[(1-q)^{k}]... roughly P(no candidate with smaller hash) = sum over k candidates: P(k candidates) * (1/(k+1)) = Σ C(24,k) q^k (1-q)^{24-k} /(k+1). Approx with q=0.05: mean 1.2 → ≈ Σ Poisson-ish/(k+1) ≈ (1-e^{-1.2})/1.2 ≈ 0.55. So kept ≈ q*0.55 ≈ 0.0275 per column in forest zones → forest zone 5000 columns → ~140 trees. 

Let me now also double check trunk/leaf geometry fits: trunk top y = H + th (th 4-6) ≤ 46+6=52 < SY=64 ✓. Canopy top +1 → 53 ✓.

**Check water side faces at borders:** border columns with H < WATER: side faces y=H..WATER-1 at the four map-edge planes, visible from outside — the camera path stays within ±64? CP x max 58, min -58; camera y above water; edges at ±64 with fog — edges visible when looking outward: shows terrain cross-section cliff — nice "diorama" look. Also bottom faces of water at border? Water bottom sits on solid (H floor) — no. And terrain bottom face y=0 — culled via treating y<0 as solid. ✓.

Also need water top face ONLY where water exists: H < WATER. Note H counts solid count; blocks y=0..H-1 solid; water blocks y=H..WATER-1 when H<WATER... wait WATER=12: water blocks y from H to 11 inclusive → count = 12-H. Top face at y=WATER=12.0 ✓. Dry land: H ≥ 13 → top solid at y=12 (face at 13.0 > water 12 ✓ shoreline above water). H=12: top solid y=11, face at 12.0 == water level: exactly at waterline — I classify H≤12 as underwater (H<13) → gets water above? H=12 → water blocks y=12..11 → none; top face? H<WATER (12<12 false) → no water. So H=12 = exactly-at-waterline land, gets SAND (beach) ✓ no water top face ✓. H=11: water at y=11 only, top face at 12 ✓ sand floor (H≥9 → sand) ✓.

Beach rule: H in {12,13,14} → sand top. Underwater H in [9..11] sand; H<9 → dirt floor? make dirt for H in [5..8], stone H<5. Fine.

Grass: H ≥ 15. What about H=14 vs 15 gap? H=14 sand (beach), H=15 grass ✓.

Snow: H ≥ 30 + dither where dither = hash2(x,z,seed)*5 → threshold 30..35; rock band: H ≥ 25 + dither*5 → stone. Hmm also make some grass peek: fine.

Steepness: gradient g = max abs diff of elevation between 4-neighbors... compute via elevation() calls: e1=elevation(x+1,z)-elevation(x-1,z) etc. steep if |e1|+|e2| > 3.4 → stone top (below snow threshold). Note elevation() for neighbor columns — but the top-type decision uses H (quantized) — ok.

But wait: elevation(x,z) uses centered coords x∈[-64,64); at x=63.5? Columns x=0..127 centered at x-64+0.5? Hmm — voxel (x) spans [x-64, x-63]. For height sampling I use elevation at block center? I'll just call elevation(x-64, z-64) treating voxel coords directly; half-block offset irrelevant.

Column type assignment code:

```js
for(let z=0; z<SZ; z++) for(let x=0; x<SX; x++){
  const e = elevAt(x,z) (continuous);
  let H = Math.floor(e); H = clamp(H, 3, 52);
  const dx = elevAt(x+1,z)-elevAt(x-1,z), dz = elevAt(x,z+1)-elevAt(x,z-1);
  const steep = Math.abs(dx)+Math.abs(dz) > 3.2;
  const dith = hash2(x,z,5)*6-3;
  let top;
  if(H >= 30+dith) top=SNOW;
  else if(H >= 25+dith || steep) top=STONE;
  else if(H >= 15) top=GRASS;
  else if(H >= 12) top=SAND;      // includes 12..14
  else if(H >= 9) top=SAND;       // shallow underwater
  else if(H >= 5) top=DIRT;
  else top=STONE;
  ...
}
```
Wait H≥15 grass but H in 12..14 sand — but I want beaches only near water; H=14 could occur on inland hills base — sand there looks odd-ish but reads as shoreline of seasonal... acceptable; alternatively sand only if H ≤ 14 AND within 3 of water level AND near a water column... keep simple: sand if H ≤ 14 (it'll appear at low ground — reads as sandy flats near coast — fine, coasts are where low ground is due to bias).

Hmm wait: H≥9 → sand for underwater too — merge: H≤14 → sand except H<9: dirt/stone. Let me finalize:

```
if H >= snowLine → SNOW
elif H >= rockLine || steep → STONE
elif H >= 15 → GRASS
elif H >= 9 → SAND        // beach + shallow bed (H 9..14)
elif H >= 5 → DIRT
else STONE
```
Under-column fill:
```
for y in 0..H-1:
  if y >= H-1 → top
  elif y >= H-4 → (top==SAND? SAND : top==GRASS? DIRT : top==SNOW? STONE : top==STONE? STONE : DIRT)
  else STONE
```
Actually for GRASS top: dirt band H-4..H-2 then stone below ✓. For SAND: sand band ✓. SNOW: stone band. STONE: stone. DIRT: dirt band then stone.

Snow line dither: snowLine = 30 + hash2(x,z,91)*5 (30..35); rockLine = snowLine - 4 → 26..31. OK.

Trees: condition top==GRASS && H>=16 && !steep && forest fbm(wx*0.012, wz*0.012, seed 71) > 0.0? Let me: f = fbm(...); density = f > 0.12 ? 0.045 : (f > -0.1 ? 0.006 : 0.0); then hash gate + local-min gate; margin from map edge ≥ 3 (x,z in [3,124]).

**Meshing water top shade:** vertex color per corner: depthShade = 1 - min(1,(WATER-H))*0.028 → deeper darker (down to ~0.72 at depth 10). Multiply also by 0.98? fine.

Also — should water top faces get slight inset or be flush? Flush at y=12; adjacent sand top at y=12? No — sand top face at y=13 for H=13. For H=12 (at waterline) sand top at y=12 == water top plane of neighbors → coplanar z-fighting between water top (neighbor column) and sand top?? They're in different cells: water top at cell (x,z) spans that cell; sand top at adjacent cell spans adjacent — no overlap ✓.

**Water sides at border:** color = depthShade, shade 0.75.

**Numbers for camera clearances:** over water cl 3.0 → y≈15. Water surface 12 — camera 3 above ✓. Beach skim cl 4. Hills 5–7. Peak flank 15, vista 20.

Wait CP[7] cl 20 → y = ground(≈? at (-34,-40) e high → maybe H≈40) + 20 = 60 — above summit (≤52)? Summit at peak location; CP[7] ground maybe 38 → y 58 → above everything → god-tier vista. Hmm I wanted "beside summit": make cl 14 → y≈52 ≈ summit height, looking at peak (focus 0.95). Then CP[8] cl 12 descending west. Vista wide happens on CP[8]→CP[9] while descending — looking down west shore + sea with focus {0.40–0.5} on a valley/sea POI. OK adjust: CP[6] cl 12 (climb), CP[7] cl 15, CP[8] cl 12, CP[9] cl 6, CP[10] cl 4, CP[11] cl 3.

Let me recheck each CP ground estimate (e = cont*0.62 + (1-2t)*0.5, t=(z+64)/128):

- CP0 (−30,92): wz=156?? wait wz = z+64 → z=92 → wz=156 > 128! Out of bounds — centered coords: z ∈ [−64,64]. My CPs must be within ±64! CP0 (−30, 92) invalid. Fix: world z from −64..64; sea at z ≥ +30ish. Redo CPs (x,z within ±60):

```
CP = [
 [-26,  52, 3.2],  // sea SW
 [ 14,  56, 3.0],  // sea S, coast ahead (shore ~ z 20..45?)
 [ 42,  40, 3.4],  // SE coast skim
 [ 54,  16, 6.0],  // E hills
 [ 40,  -6, 5.0],  // valley pass (snap)
 [ 14, -20, 5.5],  // hills weave
 [ -6, -34, 12.0], // climb (snap near peak)
 [ -28, -44, 15.0],// beside summit
 [ -50, -26, 12.0],// west ridge descend
 [ -56,   2, 6.0], // west slope
 [ -48,  30, 4.0], // SW coast
 [ -26,  54, 3.2], // out to sea — near CP0; make [-20,58,3.0]? closed loop back to CP0 (-26,52) — too close? CP11 (-26,54) vs CP0 (-26,52) nearly duplicate → remove one; keep 11 points ending [-16, 58, 3.0].
]
```
11 points closed. Check z=56 → wz=120 → t=0.9375 → dirBias=1-1.875=-0.875 → e = cont*0.62 −0.875 ≈ [−1.37,−0.19] mostly deep sea ✓ camera cl 3 above water ✓ groundRef=WATER → y=15.

CP1 (14,56): same sea ✓. CP2 (42,40): wz=104, t=0.8125, bias=−0.625, e = 0.62c−0.625 ∈ [−1.1,−0.06] → sea; coast slightly north. Camera at cl 3.4 → maybe still over water; beach nearby ahead ✓. Hmm I want the beach skim clearly over sand: CP3 (54,16): wz=80, t=0.625, bias=−0.25, e=0.62c−0.25 ∈ [−0.74,0.25] — coast zone: H ~ waterline ± → groundRef = max(H,12) ≈ 12–16 → cl 6 → y≈18–22 skimming beach/hills ✓.

CP4 (40,−6): wz=58, t=0.453, bias=0.094, e=0.62c+0.094 ∈ [−0.4,0.59] → low-to-mid land; snapped to lowest pass along CP3→CP5 line ✓ cl 5.
CP5 (14,−20): wz=44, t=0.344, bias=0.3125, e∈[0.06,0.8] → land/hills ✓ cl 5.5 (terrain-hugging).
CP6 (−6,−34): wz=30, t=0.234, bias=0.53, e∈[0.2,1.02] → mountains ✓ cl 12, snapped toward peak flank.
CP7 (−28,−44): wz=20, bias=0.6875, e∈[0.3,1.18] → high mountains, ground ~30–50, cl 15 → y up to 60s — hmm groundRef here could be ~45 → y=60. Beside summit ✓.
CP8 (−50,−26): wz=38, t=0.297, bias=0.406, e∈[0.15,0.95] → mountains west edge; cl 12.
CP9 (−56,2): wz=66, bias=−0.031, e∈[−0.35,0.46] → coast/hills west ✓ cl 6.
CP10 (−48,30): wz=94, bias=−0.469, e∈[−0.78,0.03] → mostly sea/coast cl 4 → groundRef 12–16, y≈16–20 ✓.
CP11 (−16,58): deep-ish sea ✓ cl 3.

Route: starts SW sea heading east along south coast, turns north up east side, weaves through center, peak NW, down west side, along SW coast, back to start. Nice circuit. Duration 72s.

But wait — camera near x=±54–56 with fog far 240: edges of world visible — fine.

Peak snapping: peak = argmax H over grid (interior). CP6 ← peak + normalize(CP6−peak)*14 → keeps CP6 roughly 14 from summit on the approach side. If original CP6 already close, fine. Also CP7 ← peak + normalize(CP7−peak)*22, cl 15.

Also guard: if peak ground at CP7 + 15 < summit − ? irrelevant.

Look POIs:
- coastPOI: beach point near (30, 30)? search: scan all columns, H==13 or 14, pick the one closest to (36, 34)?? Coast zone z ~ 25–45 east side. Point y = 14.
- forestPOI: tree cluster centroid.
- summitPOI: (px, Hmax+2, pz).
- westSeaPOI: deep water west? deep sea south: (−20, 13, 48)? pick water column closest to (−24, 44).
- valleyPOI: the snapped pass point ground+2.
- eastHillsPOI: (46, g+4, 12)?

Look curve points (closed, ordered along route): coastSE (near CP2/3 area) → eastHills → valleyPOI → summitPOI → westRidge (−52, g+8, −18) → westSea (−24, 14, 44) → back. That's 6.

Focus windows (u in loop): map route: total loop param — control point u_i ≈ i/11 (roughly, arc-length adjusts). CP2 coast ~ u 0.18; hmm opening at u=0 (CP0 sea SW) focus coast 0–0.10 (t 0–7.2) target coastPOI (east along coast) ✓ nice opening: over water, island ahead.
- forest focus: camera CP4–CP5 (u ~0.36–0.45 = 26–32s)?? Hmm wait recompute: u_i ≈ i/11: CP3 u≈0.27 (19.5s), CP4 0.36 (26s), CP5 0.45 (32s), CP6 0.55 (39s), CP7 0.64 (46s)... That pushes summit reveal to ~40–50s — beyond 30s window! Requirement: everything important in first 30s. Need to compress: either shorter loop (LOOP=55s) or reorder route so summit comes earlier. Let me set LOOP=56s and/or re-plan: make summit around u 0.30–0.42 → t 17–24s at LOOP 56. Reorder route: start sea SW → coast skim → turn north EARLIER through hills center → peak by u≈0.35 → then descend west → wide sea vista → along south coast back. My CP order already does this; issue is 11 points spread. With LOOP=56: CP3 coast t=0.27*56≈15s, CP5 hills 25s, CP6/7 peak 31–36s — still late. Compress first half: reduce points before peak: 

Revised CP list (8 points before peak region → indices 0..7, peak at CP5/CP6):

```
CP = [
 [-26,  50, 3.2],  // 0 sea SW (u=0)
 [ 20,  54, 3.0],  // 1 sea S
 [ 46,  36, 3.6],  // 2 SE coast/beach skim
 [ 52,  10, 6.0],  // 3 E hills
 [ 30, -14, 5.0],  // 4 valley pass (snap)
 [  2, -32, 12.0], // 5 climb toward peak (snap flank)
 [ -26, -44, 15.0],// 6 beside summit (snap)
 [ -48, -28, 12.0],// 7 west ridge
 [ -56,   4, 6.0], // 8 west slope/coast
 [ -44,  32, 4.0], // 9 SW coast
 [ -20,  54, 3.0], // 10 sea heading east
]
```
11 points, closed. u_i ≈ i/11 roughly but arc-length weighting: distances vary — sea segments long (CP0→CP1 46 units), etc. Total length rough sum: CP0→1: √(46²+4²)≈46; 1→2: √(26²+18²)≈32; 2→3: √(6²+26²)≈27; 3→4: √(22²+24²)≈33; 4→5: √(28²+18²)≈33; 5→6: √(28²+12²)≈30; 6→7: √(22²+16²)≈27; 7→8: √(8²+32²)≈33; 8→9: √(12²+28²)≈30; 9→10: √(24²+22²)≈33; 10→0: √(6²+4²)≈7?? CP10 (−20,54) → CP0 (−26,50): 7 units — too short, causes tight curve. Make CP10 (−8, 58) → dist to CP0 ≈ √(18²+8²)=20. OK.

Total ≈ 355 units. Arc u for CP5 (cumulative: 46+32+27+33=138 → u=138/355=0.39), CP6 (168 → 0.47), CP7 (0.55). At LOOP 56s: coast CP2 ~ u=0.22 → 12s; valley CP4 u≈0.31 → 17s; climb CP5 22s; summit CP6 u 0.47 → 26s; west ridge CP7 u 0.55 → 31s. Summit reveal 22–30s ✓ vista into 30–36s. Beach 10–14s. Hills/valley 14–22s. Sea opening 0–10s. 

Focus windows (with LOOP=56):
- coast: u 0.02–0.14 (t 1–8): target beach/coastPOI strength 0.75.
- hills/forest: u 0.20–0.30 (11–17s): forestPOI 0.6.
- summit: u 0.36–0.50 (20–28s): summitPOI 0.95.
- west vista: u 0.55–0.66 (31–37s): westSeaPOI 0.6.
- south sea: u 0.78–0.92 (44–51s): coastPOI or deep sea 0.5 → loops back to opening.

Fine. And "look curve" base provides motion between.

Loop duration: 56s — beyond 30s requirement satisfied by 30s coverage. Good. Actually also nice: everything in first 30.

**Look lead:** u_look = (u + 0.06) % 1 with the look curve sampled at its own arc-length — plus focus blending overrides near POIs.

Hmm — one more consideration: focus strength at summit 0.95 nearly locks target to summit while camera moves CP5→CP7 — as camera passes beside/below summit and continues, holding lookAt on summit then releasing at u=0.50 — release ramp smoothstep over 0.03 (~1.7s) — smooth.

**Check camera-terrain collisions along segments between CPs:** the dense-sample + max-clearance enforcement handles it (samples along full curve). ✓. Also look-target could be inside a hill (forest POI y=g+2 fine; valleyPOI y=g+2). Focus targets have their own y set. Sway rotation small. OK.

**Now sun position:** sunDir = normalize(0.35, 0.62, 0.25)? East-southeast, elevation ~55°. Opening shot: camera at (−26,15,50) looking east toward coast (focus coast) → sun at east-south-up — likely in upper frame — sun visible in opening ✓ lovely.

Sun sprite position = camera.position + sunDir*750 each frame (so it never parallaxes weirdly / stays beyond fog w/ fog disabled). Since dome follows camera, sun follows too. Scale ~120.

**Sky shader sun halo** uses sunDir uniform ✓.

**Cloud shadowing?** none. fine.

**Verify three r186 API details:**
- `new THREE.WebGLRenderer({antialias:true})`; `renderer.setPixelRatio(Math.min(devicePixelRatio,2))`; `renderer.setSize(w,h)`; `renderer.outputColorSpace` default SRGBColorSpace ✓.
- `THREE.CanvasTexture(canvas)`; `texture.colorSpace = THREE.SRGBColorSpace`; `magFilter=THREE.NearestFilter`; `minFilter=THREE.LinearFilter`?? Hmm minFilter LinearFilter valid (no mips) ✓ but note: when generateMipmaps=false and minFilter=LinearFilter → fine. For water RepeatWrapping both axes ✓.
- `THREE.Fog(color, near, far)` ✓ scene.fog.
- `CatmullRomCurve3(points, closed=true, 'catmullrom', tension)` — types: 'centripetal' default? Default 'centripetal'. I'll use 'centripetal' (avoids overshoot) — actually for camera path smoothness 'catmullrom' with tension 0.5 gives nicer arcs; centripetal avoids loops. I'll use centripetal for safety. For dense-sample final path I use manual lerp anyway. Look curve also manual dense samples. So CatmullRomCurve3(points, true, 'centripetal', 0.5).
- getPointAt requires updateArcLengths — getPointAt calls getUtoTmapping which uses getLengths cached (divisions default = arcLengthDivisions = 200). For base curves with 11 points, 200 divisions plenty ✓.
- Sprite: `new THREE.Sprite(new THREE.SpriteMaterial({map, transparent:true, blending:THREE.AdditiveBlending, depthWrite:false, fog:false? }))` — SpriteMaterial has `fog` param? SpriteMaterial extends Material — fog property exists on SpriteMaterial? Checking memory: SpriteMaterial supports fog (yes, it has .fog since it's part of material params; sprite shader includes fog chunks). Setting fog:false in constructor — supported? Material params include fog for materials that support it; SpriteMaterial does support fog (sprite.glsl has fog). I'll set it; if unsupported it's ignored harmlessly.
- ShaderMaterial for dome: uniforms {topColor, horizonColor, sunDir, sunColor}; side: THREE.BackSide; depthWrite:false; fog: false (ShaderMaterial ignores fog unless fog:true + shader chunks — fine).
- applyAxisAngle exists on Vector3 ✓.
- BufferGeometry setIndex with array (Uint32Array via new THREE.Uint32BufferAttribute(idx,1)) ✓.

**Chunk mesh count & materials:** one material shared. 

**Edge case: chunk boundary AO/AO across chunk borders** — uses global vox ✓.

**Water geometry normals:** MeshBasicMaterial ignores normals ✓ skip normal attribute entirely (also skip for terrain — Basic doesn't need normals). Saves memory. ✓

**Check winding + flip:** flip rule: quad verts v0..v3 (CCW). Default tris (0,1,2),(0,2,3) with diagonal 0-2. If a0+a2 > a1+a3 keep, else flip to (1,2,3),(1,3,0) diagonal 1-3? The common rule: if a00 + a11 > a01 + a10 → flipped quad. With ordering, choose diagonal between the pair with the *smaller* sum? The goal: the crease should follow the diagonal whose endpoints have lower AO combined... Honestly the standard from 0fps article: `if a00 + a11 > a01 + a10 generate flipped quad`. Mapping: vertices in order (00,01,11,10) around. Diagonal default connects v0(00)-v2(11); flipped connects v1(01)-v3(10). Rule: if a(v0)+a(v2) > a(v1)+a(v3) → use flipped (diagonal v1-v3)? In the article, flipped means diagonal through 01-10... The purpose: put the diagonal across the corners with *more similar/higher* AO to avoid the darkened corner spreading across the quad. Concretely the artifact: when one corner is much darker (ao 0-1), using the diagonal through it darkens the whole triangle band. Preferred: diagonal should connect the two darkest? Hmm: With diagonal through dark corner, dark corner influences only its triangle... Let me think: interpolation across quad: triangles share the diagonal edge; vertices' colors interpolate within each triangle. If corner A is dark (ao low) and others bright: if diagonal passes through A, both triangles touch A → dark spreads along diagonal; if diagonal avoids A (opposite pair), dark confined to one triangle → sharper, correct-looking. So diagonal should AVOID the dark corner → diagonal through the brighter pair. Rule: connect pair with higher sum: if a0+a2 ≥ a1+a3 → diagonal 0-2 (default); else diagonal 1-3. Yes — keep if a0+a2 ≥ a1+a3 else flip. (My earlier statement matches.)

**AO neighbor sampling direction sign detail:** For face with dir d (unit axis), base cell b = voxel + d. For corner with tangent coords (s1 along t1, s2 along t2) where s=+1 if corner coord on that axis is 1 else −1: 
side1 = b + t1*s1; side2 = b + t2*s2; corner = b + t1*s1 + t2*s2. ✓ classic.

Wait — is that right for corners where the face-plane coordinate equals the corner? E.g., top face (+y), corner (0,1,0): tangents x,z: s_x = −1 (x=0), s_z = −1 (z=0). base b=(x,y+1,z). side1=(x−1,y+1,z), side2=(x,y+1,z−1), corner=(x−1,y+1,z−1) ✓ correct.

**Face shade table:** index by face: [+x:0.64, −x:0.64, +y:1.0, −y:0.5, +z:0.82, −z:0.82]? Directional variety: make +x 0.66, −x 0.60? Slight asymmetry adds depth (fake sun from +x/sun dir east). Sun at +x east → make +x faces brightest side: +x 0.76, −x 0.58, +z 0.82, −z 0.70? Hmm careful: too many levels gets noisy. I'll go: +y 1.0, −y 0.5, +x 0.75, −x 0.58, +z 0.84, −z 0.66. Sun in +x+z quadrant → +x and +z brighter ✓ coherent.

**UV mapping for grass side v:** v=0 at bottom of face → texture bottom. Canvas tile drawn with grass strip at top of tile (canvas y small) → with flipY, canvas top = v=1 → v=1 at face top ✓ grass strip appears at top ✓.

**Atlas rows:** tiles 0..8: row0: 0 grassTop,1 grassSide,2 dirt,3 stone; row1: 4 sand,5 snow,6 woodSide,7 woodTop; row2: 8 leaves. ✓

Tile idx → uv rect: col=i&3, row=i>>2. uMin=(col+eps')*0.25... eps in tile units: half texel = 0.5/16 of tile = 0.03125 tile → uMin = col*0.25 + 0.03125*0.25?? Careful: half-texel in UV = 0.5px / 64px = 1/128 = 0.0078125. uMin = col*0.25 + 1/128; uMax = (col+1)*0.25 − 1/128. v: row r: vMax = 1 − r*0.25 − 1/128? Canvas row r occupies y ∈ [16r,16r+16]; flipY: v = 1 − y/64 → y=16r → v = 1 − 0.25r (top edge); y=16r+16 → v = 1−0.25(r+1) (bottom edge). So vTop = 1−0.25r − 1/128, vBottom = 1−0.25(r+1) + 1/128. Face uv v (0 bottom..1 top of face) maps: vUV = vBottom + v*(vTop−vBottom). ✓

**Water UV:** top face: u=(x+cx)*0.25, v=(z+cz)*0.25 (repeat every 4 blocks). Sides: u = horizontal*0.25, v = y*0.25... texture vertical repeat — ok.

**Let me also add subtle underwater tint?** no.

**Blocks visible through water:** opaque faces adjacent to water are rendered ✓ (condition n==AIR || n==WATER). Also terrain sides at border adjacent to air ✓. Leaves adjacent to water? trunk in water? trees only on land ✓.

**Snow on trees?** trees below snowline only (grass tops) ✓.

**Counts recheck:** world 128×128 columns. fbm calls per column: elevation called 5× per column (center + 4 for gradient) each = 3 fbm (cont 4 oct + hills 4 + det 3 = 11 vnoise = 44 hashes) → 220 hashes/column → 3.6M hash calls — hmm ~ maybe 30–60ms. Fine. Could cache but fine. Actually trees forest noise extra per candidate cell — only where hash gate passes (rare) ✓. Meshing: 1M voxel iterations × 6 neighbor checks — ~6M array reads + face emits — maybe 100–200ms. Total startup < 0.5s ✓.

**Memory for geometry:** ~ (faces) top 16k + sides ~45k + border ~8k + trees ~15k ≈ 84k faces → 336k verts × (3+3+2)=8 floats ×4B = 10.7MB + indices 84k×6×4B=2MB ✓ fine.

**Now writing the sky shader:**

```js
const skyMat = new THREE.ShaderMaterial({
 side: THREE.BackSide, depthWrite:false,
 uniforms:{ topC:{value:new THREE.Color(0x3a76d2)}, horC:{value:new THREE.Color(0xcaddf0)}, sunD:{value:sunDir}, sunC:{value:new THREE.Color(0xfff2c8)} },
 vertexShader:`varying vec3 vP; void main(){ vP = position; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); }`,
 fragmentShader:`
  uniform vec3 topC, horC, sunD, sunC; varying vec3 vP;
  void main(){
   vec3 d = normalize(vP);
   float h = clamp(d.y, -1.0, 1.0);
   vec3 sky = mix(horC, topC, pow(max(h,0.0), 0.58));
   if(h<0.0) sky = horC * (1.0 + h*0.35);  // slightly darker below horizon
   float s = clamp(dot(d, normalize(sunD)), 0.0, 1.0);
   sky += sunC * (0.28*pow(s,6.0) + 0.45*pow(s,80.0));
   gl_FragColor = vec4(sky, 1.0);
  }`
});
```
Below-horizon: `horC*(1+h*0.35)` darkens toward nadir ✓. Output colorspace: ShaderMaterial writes gl_FragColor raw — renderer outputColorSpace conversion applies only to built-in materials? For ShaderMaterial, tone mapping/color space fragments NOT auto-included; output goes directly — colors set as sRGB values will render as-is (treated as final). Meanwhile MeshBasicMaterial textures get sRGB decode + linear→sRGB encode. Mixed pipeline: sky colors authored in sRGB appear correct (since no conversion). Fog color: built-in materials fog in linear?? Fog color specified as THREE.Color 0xcaddf0 — Color from hex is sRGB → stored as-is? In r186, `new THREE.Color(0xcaddf0)` stores components converted to linear-srgb working space (Color management enabled by default: THREE.ColorManagement.enabled = true default; hex assumed sRGB → converted to linear). Fog computed in linear then output encoded ✓ consistent with horizon: sky shader outputs horC raw sRGB = 0xcaddf0 → screen shows 0xcaddf0; terrain at far fog: fogColor linear(0xcaddf0) rendered → encoded back to 0xcaddf0 ✓ match! Similarly sky uniform colors: I pass new THREE.Color(hex) — under color management, `new THREE.Color(0x3a76d2)` converts to linear internally?? Then my shader outputs linear values as raw → appears washed?? Careful: ShaderMaterial uniform Color: value converted when set? THREE.Color(hex) with ColorManagement: hex converted sRGB→linear on assignment (via .setHex with SRGBColorSpace? Default: Color.setHex assumes srgb and converts to working linear? In r152+ with color management on, `new Color(0x...)` converts to linear working space? Actually: Color stores components; setHex applies conversion only if ColorManagement.enabled — yes, setHex(hex, colorSpace=SRGBColorSpace) converts to working (linear). So uniform value = linear components. My shader then outputs them raw → screen (no encode) → appears darker (linear values displayed as sRGB). To handle: either set colors via `new THREE.Color().setHex(0x..., THREE.LinearSRGBColorSpace)`?? Hmm simpler: in shader, convert: `gl_FragColor = vec4(pow(sky, vec3(1.0/2.2)), 1.0)`? Not exact sRGB. Or pass uniforms as raw sRGB: use `new THREE.Color(r,g,b)` with components 0..1 — Color(r,g,b) numeric constructor does NOT convert (setRGB with default colorSpace... in recent three, setRGB default colorSpace = LinearSRGB? Hmm: Color.setRGB(r,g,b, colorSpace = ColorManagement.workingColorSpace)? I recall numeric setRGB treats values as working-space (linear) by default. And setHex treats as sRGB converting to linear. So to get raw sRGB values through: construct via setHex with... I want shader input = the sRGB numbers. Options: pass uniform as Vector3 with raw values — clean: `sunD` vector; colors as `new THREE.Vector3(0.79,0.87,0.94)`. Shader outputs raw → displayed as-is = authored sRGB ✓. Do that. 

And fog color consistency: fog hex 0xc6dbef → sRGB (0.776,0.859,0.937)... let me choose fog = 0xc8def2: components (0.784,0.871,0.949). Sky horizon vec3 same numbers ✓. They'll match visually as reasoned (built-in pipeline: linear fog → encode back to same sRGB). One nuance: tonemapping — renderer.toneMapping default NoToneMapping ✓ no shift. 

Vertex colors on MeshBasic: my shade multipliers set as vertex color attribute — Color attribute values are used raw in shader (vertexColors multiply in linear space) ✓ fine.

**Cloud color:** white × shade. opacity 0.5.

**Water color tint:** texture blue × white-ish vertex shade; opacity 0.72.

**Sun sprite texture:** radial gradient: createRadialGradient center: stops (0, 'rgba(255,250,230,1)'), (0.25,'rgba(255,244,200,0.9)'), (0.5,'rgba(255,236,180,0.25)'), (1,'rgba(255,236,180,0)'). Plus crisp square drawn over center: fillStyle '#fffef2', fillRect(24,24,16,16)? At 64px canvas, square 18px centered. Additive blending → square core + halo. Scale sprite 140 world units at distance 750 → angular ~ 10.7° — sun real ~0.5° but stylized big-ish; Minecraft sun is ~ big. Maybe scale 90 → 6.9°. ok.

**Order of code:** all synchronous in module; then `requestAnimationFrame(animate)`.

**Resize handler:**
```js
addEventListener('resize', ()=>{ camera.aspect=innerWidth/innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth,innerHeight); });
```

**One more requirement check:** "per-face shading so cube shapes read clearly" ✓ baked. "procedural textures canvas pixel-art" ✓. "sun, soft distance fog, fluffy block clouds drift slowly" ✓ (block clouds: rectangular slabs — "fluffy" via clustered blobs). "InstancedMesh or merged geometry" ✓ merged. "camera flies automatically over and between hills on smooth path, looking around" ✓. "rAF timestamp" ✓. "full-window canvas resize" ✓. "starts automatically" ✓. "show everything in first 30s" ✓. "may loop" ✓ 56s loop.

Also — module import from 'three' with provided importmap ✓ no CDN added.

**Detailed mesher code sketch:**

```js
const AIR=0,GRASS=1,DIRT=2,STONE=3,SAND=4,SNOW=5,WOOD=6,LEAF=7,WATERB=8;
const OPAQ = t => t!==AIR && t!==WATERB;
```
Neighbor visibility for solid face: `nb===AIR || nb===WATERB`.

Build function:

```js
function buildChunkGeometry(cx0, cz0){
 const pos=[], col=[], uv=[], ind=[];
 let v=0;
 for(let x=cx0; x<cx0+CH; x++) for(let z=cz0; z<cz0+CH; z++){
  for(let y=0; y<SY; y++){
   const t = V(x,y,z); if(t===AIR||t===WATERB) continue;
   for(let f=0; f<6; f++){
    const F=FACES[f];
    const nb = V(x+F.d[0], y+F.d[1], z+F.d[2]);
    if(!(nb===AIR||nb===WATERB)) continue;
    // tile
    const ti = tileFor(t, f);
    const r = rect(ti);
    // shade & AO
    const shade = Fshades[f];
    const ao = [];
    for(let ci=0; ci<4; ci++){
      const c = F.c[ci];
      // corner pos
      pos.push(x-64+c[0], y+c[1], z-64+c[2]);
      // uv
      uv.push(r.u0 + F.uv[ci][0]*(r.u1-r.u0), r.v0 + F.uv[ci][1]*(r.v1-r.v0));
      // ao
      const a = vertAO(x,y,z,F,c);
      ao.push(a);
      const b = shade*AOL[a];
      col.push(b,b,b);
    }
    if(ao[0]+ao[2] >= ao[1]+ao[3]) ind.push(v,v+1,v+2, v,v+2,v+3);
    else ind.push(v+1,v+2,v+3, v+1,v+3,v);
    v+=4;
   }
  }
 }
 ...build geometry if v>0
}
```
vertAO:
```js
function vertAO(x,y,z,F,c){
 const d=F.d;
 // tangent axes: the two axes where d==0
 let t1, t2; // axis indices
 if(d[0]!==0){ t1=1; t2=2; } else if(d[1]!==0){ t1=0; t2=2; } else { t1=0; t2=1; }
 const s1 = c[t1]===1?1:-1, s2 = c[t2]===1?1:-1;
 const b=[x+d[0], y+d[1], z+d[2]];
 const p1=[...b]; p1[t1]+=s1;
 const p2=[...b]; p2[t2]+=s2;
 const p3=[...b]; p3[t1]+=s1; p3[t2]+=s2;
 const o1=OPAQ(V(p1[0],p1[1],p1[2]))?1:0, o2=..., o3=...;
 const lvl = (o1&&o2)?0 : 3-(o1+o2+o3);
 return lvl;
}
```
V(x,y,z) with bounds: outside horizontally → AIR (0); y<0 → STONE (occlude); y≥SY → AIR.

Perf: vertAO allocates arrays per vertex — 4 per face × 84k faces = 336k small arrays — GC churn at startup, acceptable but let me write it without allocations using scalar math:

```js
function vertAO(x,y,z,d, t1,t2, s1,s2){ ... compute coords via axis indexing with switch? }
```
I can precompute per-face per-corner the three offset vectors at startup (each face: 4 corners × 3 offsets = 12 offset triples) → store in FACES[f].ao[ci] = [[o1],[o2],[o3]] as flat int arrays. Then vertAO just reads. Precompute once — clean & fast. 

FACES structure final:
```js
{ d:[..], c:[[..]x4], uv:[[..]x4], shade, aoOffsets:[[o1x,o1y,o1z, o2x.., o3x..] x4] }
```
Build aoOffsets programmatically from d and c as described.

Also face winding — verified above.

**Tile lookup:**
```js
function tileFor(t, f){ // f: 0..5 (+x,-x,+y,-y,+z,-z)
 switch(t){
  case GRASS: return f===2?0 : f===3?2 : 1;
  case DIRT: return 2;
  case STONE: return 3;
  case SAND: return 4;
  case SNOW: return 5;
  case WOOD: return (f===2||f===3)?7:6;
  case LEAF: return 8;
 }
}
```

**Water mesher:**
```js
const wpos=[], wcol=[], wuv=[], wind=[];
top faces: for x,z: H stored? I need per-column H — store heightMap Int16 during gen. if H<WATER: quad at y=WATER: corners (x,y,z),(x,y,z+1),(x+1,y,z+1),(x+1,y,z) — same winding as +y face. shade: ds = depthShade. uv world-based. flip not needed (no AO) — use default diag.
border sides: for each border column with H<WATER: for x==0: face at plane x=0 facing −x: corners like −x face at each y in H..WATER-1: emit quads. Similarly x==SX-1 (+x plane x=SX → world x = SX-64=64), z borders.
Actually simpler: loop y from H to WATER-1: emit side quad. Only if column water. ✓
```
Water top winding same as top face: v0=(0, y,0) etc with corners [[0,0,0],[0,0,1],[1,0,1],[1,1,0]]→ for water at y=W: [[0,W,0],[0,W,1],[1,W,1],[1,W,0]]? My +y face corners were [[0,1,0],[0,1,1],[1,1,1],[1,1,0]] ✓ (x,z pattern 00,01,11,10) CCW from above ✓.

Border side faces winding: for −x face at x=0: corners [[0,y,1],[0,y+1,1],[0,y+1,0],[0,y,0]]? From −x face table: [[0,0,1],[0,1,1],[0,1,0],[0,0,0]] ✓ replace y-offsets. For +x at x=SX: plane world x = SX → local corner x=1 → position x+1... face +x corners [[1,0,0],[1,1,0],[1,1,1],[1,0,1]] at x=SX−1 block: position = (SX-1)+1 = SX → world SX-64 ✓. For z borders analogous.

Water shade for sides: 0.8, top: depthShade.

Hmm also: water top faces adjacent to border where neighbor outside is AIR — my rule for water: only top faces (nb above is AIR always for top). Top face rendered even under... fine. Also water under leaves? no.

Also should I render water top faces also where H<WATER but block above water is... always air ✓.

**Cloud builder:**

```js
const CN=48, CS=8, T=1.5, CY=74;
occ = Uint8Array(CN*CN);
for i,j: h1 = hash2(((i%CN)+CN)%CN, j, 909) — wait periodicity needed only in x (drift axis). Use i wrap: hi = i (0..CN-1) already; hash2(i, j, 909) — drift wrap by CN cells seamless ✓ (no need mod since I only use i in [0,CN)).
raw[i][j] = hash2(i,j,909) < 0.42 ? 1:0
smoothing: occ = neighbors3x3 count ≥ 5 → 1 (with raw).
also j range full (no wrap needed in z).
Then faces: for occ cells: 
 top quad y=CY+T (shade 1.0), bottom y=CY (0.78), sides where neighbor empty: shade 0.9, plus... to fake volume maybe make thickness vary? keep uniform.
world x0 = (i - CN/2)*CS + driftOrigin... group at origin; geometry local; group.position.x animated.
z0 = (j - CN/2)*CS.
```
Only sides where neighbor cell empty (within grid; outside grid treat empty). Top/bottom always (thin slab, cheap: 2 quads × ~600 cells + sides ~ 600 → ~2.4k faces fine).

Cells count: 48×48=2304 cells, occ p≈0.3 → ~700 cells → faces ~700×2 + perimeter sides ~ maybe 800 → 2200 faces ✓.

Material transparent — will be one draw call.

Also — clouds should be "fluffy": clusters from smoothing ✓ blocky slabs like Minecraft ✓.

**Camera path sampling code:**

```js
const LOOP = 56;
const basePts = CP.map(p=>new THREE.Vector3(p[0],0,p[1]));
const clPts = CP.map(p=>new THREE.Vector3(p[0],p[2],p[1]));
const baseCurve = new THREE.CatmullRomCurve3(basePts, true, 'centripetal');
const clCurve = new THREE.CatmullRomCurve3(clPts, true, 'centripetal');
const NS=1024; camY = new Float32Array(NS); camP=[]; 
for(i<NS){ u=i/NS; p=baseCurve.getPointAt(u); const g=groundRef(p.x,p.z); const cl=clCurve.getPointAt(u).y; camY[i]=g+cl; camP.push(p); }
// snapping of CPs happens BEFORE curve creation: 
```
Snapping before curves:
```js
// peak find: scan grid step 2 for max H.
// CP5 snap: CP[5] = peak + normalize(CP[5]-peak)*16 → but keep cl.
// CP6 snap: CP[6] = peak + normalize(CP[6]-peak)*24, cl 15.
// valley snap: along line CP[3]→CP[5]: sample 40 points, pick min groundRef → CP[4]=that point (cl 5).
```
Hmm — snapping CP[5] toward peak changes the valley line — snap valley AFTER peak snaps. Order: find peak → snap CP5, CP6 → snap CP4 (valley along CP3–CP5).

peak location: mountains north — peak likely near north edge; CP5/CP6 approach from south-east ✓.

If peak H is like 52 and CP6 = peak + 24 units away toward SE: groundRef there maybe ~30 → y=45 vs summit 52 — camera slightly below summit, looking up at peak — dramatic ✓.

Then smooth camY: 
```js
for(iter=0; iter<3; iter++){
  const y2 = camY.slice();
  for i: camY[i] = (y2[(i-1+NS)%NS] + 2*y2[i] + y2[(i+1)%NS])/4;
  for i: camY[i] = Math.max(camY[i], minBase[i]); // minBase = g+cl cached
}
// final tiny smoothing without enforcement? skip — steps ≤ ~1 fine. Actually enforce-then-nothing leaves steps where smoothing dipped below min: those points jump back up → possible 1-unit steps — negligible.
```
Store final camSamples: Vector3(p.x, camY[i], p.z) every sample; sampling function lerps between i and i+1.

Look samples similarly: lookCurve closed through POI points (after POI determination), NS2=512, but y also from curve directly (POI y values) with mild smoothing? POI y's fine; curve smooths. Also raise look targets above ground: at build, enforce per sample: ly[i] = max(ly[i], groundRef+1.5)? For sample points x,z — look target under a hill would look into hill — enforce max(ground+1.5). Then small smoothing. OK.

samplePath(u): 
```js
function samplePath(arr, u){ const f=((u%1)+1)%1*arr.length... careful: samples uniform: i=floor(f), a=arr[i], b=arr[(i+1)%N], lerp.
```

**Focus blending:**
```js
const FOCUS=[
 {a:0.015,b:0.13,p:coastPOI,s:0.75},
 {a:0.20,b:0.30,p:forestPOI,s:0.6},
 {a:0.36,b:0.50,p:summitPOI,s:0.95},
 {a:0.56,b:0.68,p:westPOI,s:0.6},
 {a:0.80,b:0.93,p:seaPOI,s:0.55},
];
weight(u,f): ramp = smoothstep((u-a)/0.025) * smoothstep... w = s * smoothstep(a, a+0.03, u) * (1 - smoothstep(b-0.03, b, u));
final target: base look point; apply strongest focus (or accumulate: start target=look; for each f: target.lerp(f.p, w)) — sequential lerp fine (windows overlap unlikely).
```
Opening at u=0: focus a=0.015 — at u=0 weight 0 → looks along base curve — base curve near POIs anyway. Fine, ramp quickly.

Note focus p stored as Vector3; target lerped copy — use temp vectors, no allocation per frame ideally: preallocate temps.

Sway:
```js
const look = target - camPos; 
ang = Math.sin(t*0.5)*0.05 + Math.sin(t*0.23+1.7)*0.09;
look.applyAxisAngle(UP, ang);
camera.lookAt(tmp.copy(camPos).add(look));
```
Also small y bob added to camPos.

Hmm: applyAxisAngle around Y only — fine (no roll).

**Also initial camera orientation**: set from t=0 evaluation before first frame? First frame sets it ✓.

**groundRef uses elevation()** (analytic) — consistent with generated world (H from same function) ✓ but trees add height not in elevation — camera path might pass through tree canopies where cl ~5 over forest! Tree tops at H+7; camera at H+5 → clips through canopy possibly. Mitigate: groundRef adds tree-aware? Cheap: in groundRef, use heightMap (actual top solid incl. nothing—heightMap is terrain only)... simplest: increase clearance in forest? Or compute path clearance using a canopy-aware height grid: canopyGrid = heightMap + 8 where tree present. I have tree positions list — build Float32Array groundMax = heightMap; for each tree: for cells in radius 2 around trunk: groundMax = max(groundMax, H+th+2)? Then groundRef(x,z) reads this grid (bilinear? nearest fine) instead of elevation → includes canopy. But smoothing of camera path handles transitions. Use grid lookup with clamp; outside grid → use elevation fallback. Since path stays within ±64 (world bounds), grid covers all ✓ (grid index from centered coords: gx = round(x+64) clamp 0..127).

So groundRef = grid-based:
```js
const flyH = new Float32Array(128*128); // during worldgen fill with H; trees update with trunk top+2 over trunk cell + canopy radius... simply: for tree at (x,z,H,th): for dx -2..2, dz -2..2 (canopy): flyH = max(flyH, H+th+2)? canopy top = H+th+1; +1 margin → H+th+2. For trunk cell just H+th+2 also ✓.
```
And water: flyH = max(flyH, WATER) for water columns → since flyH stores H (≤12 in water) → max with 12 ✓ do at end: flyH[i]=Math.max(flyH[i], WATER).

groundRefC(x,z): gx=clamp(round(x+64),0,127), gz=... return flyH[gx+128*gz]. Plus clearance. The camera path between grid samples uses nearest — 1-unit steps smoothed by the y-smoothing passes ✓.

**Water POI (deep sea south) & west POI:**
- seaPOI: water column (H≤8) nearest to (−10, 45)?? Opening look: camera CP0 (−26,50) → focus coast at (beach east ~(40,30)?) — hmm coastPOI should be visible ahead: camera heading east (CP0→CP1 direction +x). coastPOI near (34, 34)?? Actually camera at z~50, looking east-southeast — beach POI at (36,36) — direction from camera (−26,15,50) to (36,14,36): mostly +x, slight −z, downward — good with sun beyond? sun at +x+z... fine.
- coastPOI found: nearest beach column to (36, 36). y = 15.
- forestPOI: cluster centroid + y at its ground +6.
- summitPOI: peak + y H+3.
- westPOI: point on west coast: nearest beach/water column to (−52, 12)? Let me: water column nearest (−54, 20), y=WATER+2 → looking down at west shore sea.
- seaPOI (south deep): water column nearest (−6, 56), y=WATER+2.

Look curve points order (closed): coastPOI → eastHills(46, g+5, 8) → valleyPOI(snapped CP4, y g+3) → summitPOI → westRidge(−46, g+6, −20) → westPOI → seaPOI?? hmm keep 6: [coastPOI, eastHills, valleyPOI, summitPOI, westRidge, westPOI] closed — from westPOI back to coastPOI spans the south sea ✓ nice: during final segment camera over south sea looking at coast ✓.

**East hills POI ground**: g from flyH ✓.

**Check focus on summit while camera between CP5..CP7 (u .36–.50):** base look curve at that u — look curve param differs from camera param; blending 0.95 to summit dominates ✓.

**Vista after summit:** camera CP7 (−28,−44 cl15) → CP8 (−48,−26) descending — looking at westRidge/westPOI — fine.

**Numbers: fov 62; near .1; far 1500.**

**Let me now also handle devicePixelRatio and antialias with performance:** ~250k tris + fill — fine.

**Potential pitfall: THREE.ColorManagement + vertexColors on MeshBasicMaterial with map — colors multiply in linear — textures sRGB→linear decode then multiply then encode — standard ✓.

**Write the water texture:**
```js
32×32: base: for each pixel: n = vnoise(x*0.3, y*0.3, seed)…simple: base (52,110,190) ± hash*14; streaks: if (y*32+x) hash < 0.08 → lighter (86,152,224); a few dark (36,80,150).
```
Actually nicer: horizontal-ish wave bands: v = vnoise(x*0.25, y*0.55, 5) → threshold bands → pixel light/dark. I'll do simple: n=vnoise(x*0.35,y*0.6,seed 31); shade = n>0.6? light : n<0.35? dark : base ± small. Since repeat wrapping causes seam at edges (noise not periodic) — barely noticeable on water; mitigate: mirror wrapping (THREE.MirroredRepeatWrapping) → seamless ✓ use mirrored for water.

**Atlas texture:** wrap default clamp ✓.

**Cloud texture:** none (plain color + vertex shade) ✓.

**Snow tile:** pure-ish white — with per-face shading shows relief ✓.

Now, sun glare through terrain: sun sprite depthTest true → occluded by mountains ✓ (transparent pass after opaque).

**Dome geometry:** SphereGeometry(900, 32, 15). follow camera each frame.

**Fog near/far:** Fog(0xc8def2, 70, 230). World 128 wide — from high vista (y 55) looking across, far corner ~ 200 → heavily fogged ✓ soft. Near 70 keeps mid-ground crisp.

Cloud fog: clouds within ~100 mostly unfogged ✓.

**Cloud altitude 74 vs camera max ~60 — camera never above clouds — fine, clouds always overhead ✓. Peak 52 + margin. CP7 y up to maybe 62? ground 40 + 15 = 55; ok below 74 ✓.

**Trees list also used for forestPOI:** compute cluster: for each tree, count trees within 14 → pick max → centroid of those.

**Bedrock:** y=0 always stone ✓ (fill from y=0).

Let me also double-check the fill loop for underwater columns: H=6 (deep): top=DIRT? rule: H≥9 sand, H≥5 dirt, else stone → H=6 → dirt top; band y≥H-4=2..4 dirt? top at y=5; y in [2..4] band dirt, y 0..1 stone. OK.

**Now assemble the entire code.** I'll write it carefully, aiming for clean organized sections with brief comments (in English — user request is English). Also a tiny start overlay? No — starts automatically, no interaction. Maybe a subtle title overlay that fades? Tasteful cinematic letterbox bars! Cinematic flythrough — letterbox black bars top/bottom (CSS) would sell "cinematic". Add thin bars (6vh) with CSS transition, fade in after load. Hmm — could be considered ornament? It serves the cinematic framing ask; I'll add subtle bars (~7% height, pure black) — classic. I'll keep them; they also hide any edge artifacts. Actually — recording window is 30s; bars reduce visible area slightly... keep them slim (5vh). I'll include; tasteful.

Also small caption text ("procedural voxel world") fading out after few seconds? Might be nice for cinema feel; minimal: a tiny label bottom-left with monospace? I'd rather keep it clean — just letterbox. Hmm, a quiet title card for the first seconds ("VOXEL DRIFT — a procedural world") then fades — cinematic. But font constraints: no external fonts; system monospace... Using generic fonts is allowed (no external resources). I'll use a simple uppercase letter-spaced sans (system-ui) small caption bottom, fading out at 6s. Keep it subtle. Fine.

Wait — should double-check: "no interaction needed" — no controls; OrbitControls not needed.

**Also — the recording window:** everything important within 30s: sea+beach ✓ (0–14s), hills/forest ✓ (11–17s), valley ✓, summit reveal ✓ (20–28s), wide vista starts ~28s (CP7 at u≈.55*56≈31s — hmm vista slightly after 30). Let me tighten: summit focus window 0.36–0.50 → t 20–28s ✓; camera high point CP6→CP7 around u .47–.55 → 26–31s — the vista (looking down from high) begins ~27s with focus releasing toward westPOI at 0.56 (31s). The high wide view itself occurs as camera crests ~26–31s while still looking at summit + release → by 29–30s target swings to west/sea vista. Acceptable: "everything important" — sea, beach, hills, trees, peak, clouds, sun all clearly within 30s ✓.

Could compress more: LOOP 52 → summit at 0.47*52≈24.4s, vista ~28.5s. Let me set LOOP=52. Then focus windows in u same; t = u*52: coast 1–7s, forest 10.5–15.5, summit 18.7–26, west vista 29–35. Good. LOOP=52.

Speed along path: length ~355 + terrain climbing extra ~ 380 → 380/52 ≈ 7.3 units/s — brisk but cinematic-ish (Minecraft blocks 1m — 7 m/s ~ flying). Fine.

**One more check — getPointAt on CatmullRomCurve3 closed:** supported ✓ (closed curves param 0 at first point).

**Hmm — clCurve uses y=cl — but CatmullRom interpolates y through points including possibly negative? cl all positive ✓.

**Valley snap:** CP[4] = argmin over line CP3→CP5 — but snapped CP5 changes line — order: peak snap first, then valley ✓.

**Peak find:**
```js
let pk={x:64,z:64,h:0};
for x step 2, z step 2 (interior 4..123): if Hmap> pk.h → update. Then refine ±2 full res? fine coarse.
```
Hmap stored during gen (Int16Array 128×128) — I'll store hm[] as I fill columns.

Also guard: if peak.h < 30 (no real mountain — shouldn't happen with bias) skip summit focus? Just proceed; terrain bias guarantees.

**Trees into flyH:** canopy radius 2 → cells within ±2 of trunk get max(flyH, ground+th+2). But wait, th varies per tree: th = 4 + floor(hash*3) (4–6); top of canopy = H + th + 1 (layer at base+th+1? my canopy layers: y = base+th-3.. base+th+1 → top = H+th+1? base = H (first trunk block at y=H since top solid at H-1). Trunk y from H to H+th-1. Canopy layers at y = H+th-3 .. H+th+1 → top leaf at H+th+1. flyH = H+th+2 ✓.

Tree gen detail:
```js
function placeTree(x,z,H,th){
 const topY = H+th-1; // top trunk block
 for(y=H; y<=topY; y++) set(x,y,z,WOOD);
 // canopy layers
 for(dy=-2; dy<=1; dy++){ // y = topY+dy+? Let me define layers relative to topY:
   const y = topY + dy + 1; // layers at topY-1, topY, topY+1, topY+2
   hmm simpler explicit:
 }
}
```
Explicit canopy:
- Layer A (y = H+th-3 and H+th-2): radius 2, skip corners if hash>0.4 (per corner).
- Layer B (y = H+th-1): radius 1 full 3×3? plus corners maybe skip randomly.
- Layer C (y = H+th): radius 1 cross (no corners).
- Layer D (y = H+th+1): cross radius 1 (center+4)? Minecraft has small plus on top. I'll do layer C = 3×3 minus corners, layer D = plus shape.

Trunk th ≥ 4 → canopy bottom at H+1 (H+th-3 = H+1 for th=4) ✓ leaves above ground.

Set leaves only into AIR cells.

Wait — canopy must not extend past map borders: trees restricted x,z ∈ [3,124] ✓ radius 2 fits.

**Leaf corner skip determinism:** hash2(x*3+dx, z*3+dz, seed 4242) etc.

**Now — write everything. Also double-check water border sides use flyH-independent stuff ✓.**

Let me write the final code now, being careful with details.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Voxel Isles — Cinematic Flythrough</title>
<style>
  html,body{margin:0;padding:0;width:100%;height:100%;overflow:hidden;background:#0a0d12}
  canvas{display:block}
  #cine{position:fixed;left:0;right:0;height:5.5vh;background:#000;z-index:5;pointer-events:none;transition:opacity 1.2s ease}
  #cine.top{top:0}#cine.bot{bottom:0}
  #cap{position:fixed;left:24px;bottom:calc(5.5vh + 14px);z-index:6;color:#fff;opacity:.85;
       font:500 11px/1.4 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
       letter-spacing:.22em;text-transform:uppercase;text-shadow:0 1px 2px rgba(0,0,0,.5);
       transition:opacity 1.6s ease;pointer-events:none}
</style>
</head>
<body>
<div id="cine" class="top"></div><div id="cine" class="bot"></div>
<div id="cap">procedural voxel isles — autonomous flight</div>
<script type="module">
import * as THREE from 'three';
...
</script>
</body>
</html>
```
Duplicate id "cine" — use classes instead. Fine: `<div class="cine top">`.

Caption fade: setTimeout 6500 → opacity 0. Letterbox: keep permanently (or fade after 40s? keep — cinematic identity).

Hmm — letterbox + caption: caption inside bottom bar area? Put caption just above bottom bar ✓ as styled.

Now the JS. Let me write it fully and carefully.

```js
import * as THREE from 'three';

/* ---------- deterministic noise ---------- */
function hash2(x, y, s){
  let h = (Math.imul(x|0, 374761393) + Math.imul(y|0, 668265263) + Math.imul(s|0, 1442695041))|0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  h ^= h >>> 16;
  return (h >>> 0) / 4294967296;
}
function vnoise(x, y, s){
  const xi = Math.floor(x), yi = Math.floor(y);
  let xf = x-xi, yf = y-yi;
  xf = xf*xf*xf*(xf*(xf*6-15)+10);
  yf = yf*yf*yf*(yf*(yf*6-15)+10);
  const a = hash2(xi,yi,s), b = hash2(xi+1,yi,s), c = hash2(xi,yi+1,s), d = hash2(xi+1,yi+1,s);
  return a + (b-a)*xf + (c-a)*yf + (a-b-c+d)*xf*yf;
}
function fbm(x, y, s, oct){
  let a=1, f=1, sum=0, norm=0;
  for(let i=0;i<oct;i++){ sum += a*(vnoise(x*f, y*f, s+i*97)*2-1); norm+=a; a*=0.5; f*=2.03; }
  return sum/norm;
}
const smoothstep=(a,b,x)=>{ x=Math.min(1,Math.max(0,(x-a)/(b-a))); return x*x*(3-2*x); };
const clamp=(v,a,b)=>v<a?a:v>b?b:v;
```

World constants:
```js
const SX=128, SZ=128, SY=64, HALF=64;
const WATER=12;       // water surface plane (top face y)
const CH=32;          // chunk size
const AIR=0,GRASS=1,DIRT=2,STONE=3,SAND=4,SNOW=5,WOOD=6,LEAF=7,WATERB=8;
```

Elevation:
```js
function elevation(x, z){ // centered coords
  const wx = x+HALF, wz = z+HALF;
  const cont = fbm(wx*0.0062, wz*0.0062, 1013, 4);
  const bias = 1 - 2*wz/SZ;          // +1 north (mountains), -1 south (sea)
  const e = cont*0.62 + bias*0.5;
  const hills = fbm(wx*0.021, wz*0.021, 777, 4);
  const det   = fbm(wx*0.062, wz*0.062, 555, 3);
  let h;
  if(e < 0){
    const d = Math.min(1, -e/0.85);
    h = WATER - 1.6 - d*d*11 + hills*1.5 + det*1.1;
  } else {
    const m = smoothstep(0.16, 0.85, e);
    h = WATER + 1.3 + e*12*(0.7+0.45*hills) + m*m*21*(0.85+0.4*hills) + det*1.5;
  }
  return h;
}
```
Check ranges: sea e=-0.85..: h = 10.4 - 11 ±2.6 → ~-3.2..2.4?? 10.4−11 = −0.6 ±2.6 → clamp to ≥3 → flat deep floor at 3. Slightly shallow-clamped; make deeper: d*d*11 → floor -3.2 clamps 3; depth from surface 12 → 9 deep. OK fine (SY floor). Also e min ~ -1.12: d=1 → same clamp. Sea depth 9 ✓.

Land mid e=0.3: m=smoothstep(0.16,0.85,0.3)=~0.06?? (0.3-0.16)/0.69=0.203 → ss=0.107 → m²=0.0115: h=13.3+3.6*(0.7+0.45h)+0.24+... ≈ 13.3+[1.1..5.0] ≈ 14.4–18.5 rolling hills ✓.

e=0.6: m=ss(0.636)=0.717?? (0.6-0.16)/0.69=0.638→ss=0.638²(3-2*0.638)=0.407*1.724=0.702→m²=0.49: h=13.3+7.2*(0.25..1.15)+10.3*(0.45..1.25) = 13.3+[1.8..8.3]+[4.6..12.9] ≈ 19.7–34.5 → mountains foothills ✓.

e=1.0: m=1: 13.3+12*(0.25..1.15)+21*(0.45..1.25) = 13.3+[3..13.8]+[9.5..26.3] → 25.8–53.4 clamp 52 ✓ peaks.

Shoreline e≈0: land side h≈13.3±det... h=13.3+0+det*1.5+e*12*(...)≈ 11.8–14.8 → beaches around 12–14 ✓ water at 12: H=13,14 sand beaches ✓. Sea side near e→0⁻: h = 10.4 ± ~2.6 → 8–13: hmm 13 > water → tiny islets/bars ✓ fine, natural.

Column gen:
```js
const vox = new Uint8Array(SX*SY*SZ);
const hm = new Int16Array(SX*SZ);
const flyH = new Float32Array(SX*SZ);
const idx=(x,y,z)=> x + SX*(z + SZ*y);
const V=(x,y,z)=> (x<0||x>=SX||z<0||z>=SZ||y>=SY) ? AIR : (y<0 ? STONE : vox[idx(x,y,z)]);
```
fill:
```js
const trees=[];
for(let z=0;z<SZ;z++)for(let x=0;x<SX;x++){
  const eC = elevation(x-HALF, z-HALF);
  const gx = elevation(x+1-HALF,z-HALF)-elevation(x-1-HALF,z-HALF);
  const gz = elevation(x-HALF,z+1-HALF)-elevation(x-HALF,z-1-HALF);
  const steep = Math.abs(gx)+Math.abs(gz) > 3.4;
  let H = clamp(Math.floor(eC), 3, 52);
  hm[...] = H;
  const dith = hash2(x,z,61)*6;
  let top;
  if(H >= 30+dith) top=SNOW;
  else if(H >= 26+dith || steep) top=STONE;
  else if(H >= 15) top=GRASS;
  else if(H >= 9) top=SAND;
  else if(H >= 5) top=DIRT;
  else top=STONE;
  for(let y=0;y<H;y++){
    let t;
    if(y===H-1) t=top;
    else if(y>=H-4) t = top===SAND?SAND : top===GRASS?DIRT : top===DIRT?DIRT : STONE;
    else t=STONE;
    vox[idx(x,y,z)]=t;
  }
  flyH[...]=H;
}
```
dith 0..6 → snowLine 30–36, rock 26–32. Peak 52 > 36 ✓ snow caps.

Trees:
```js
for(let z=3;z<SZ-3;z++)for(let x=3;x<SX-3;x++){
  const h0 = hm[x+SZ*z]... wait hm index: x + SX*z.
  if(hm[i] < 16) continue; // grass check separately: need top==GRASS: recompute? store topType array? Simpler: check H: grass iff 15 <= H < snowline/rockline... I didn't store top. Store topType in a Uint8Array topT. Let me store topT per column.
```
I'll store `topT` Uint8Array. Tree conditions: topT===GRASS && !steep — store steep? recompute steep cheap? I'll store `isSteep` bit in topT? Use separate Uint8Array flags or encode: I'll just also store steepFlag array. Eh — simpler: store `colInfo` Uint8: bits. Meh — just two arrays: topT and steepA (Uint8). fine.

Tree placement:
```js
const forest = fbm((x-HALF)*0.013, (z-HALF)*0.013, 424, 3);
const dens = forest > 0.18 ? 0.05 : (forest > -0.05 ? 0.007 : 0);
if(dens>0){
  const h0 = hash2(x,z,8804);
  if(h0 < dens){
    // local-min among candidate neighbors in 5x5
    let ok=true;
    for(let dz=-2;dz<=2 && ok;dz++)for(let dx=-2;dx<=2;dx++){
      if(dx===0&&dz===0) continue;
      const nx=x+dx, nz=z+dz;
      if(nx<3||nx>=SX-3||nz<3||nz>=SZ-3) continue;
      if(hash2(nx,nz,8804) < dens && hash2(nx,nz,8804) < h0){ ok=false; break; }
    }
```
Hmm comparing candidates: neighbor candidate with smaller hash suppresses. If neighbor hash < dens && < h0 → suppress. Ties negligible ✓.
```js
    if(ok && !steepA && H≥16){
      const th = 4 + Math.floor(hash2(x,z,8805)*3); // 4..6
      trees.push({x,z,h:H,th});
      // write trunk & canopy into vox
      ...
      // flyH raise
      for(dz=-2..2)for(dx=-2..2){ flyH[cell] = max(flyH, H+th+2); } // only within canopy radius? fine all 25
    }
  }
}
```
Canopy write:
```js
const ty = H+th-1; // top trunk y
for(let y=H;y<H+th;y++) if(vox[idx(x,y,z)]===AIR) vox[idx(x,y,z)]=WOOD;
const put=(X,Y,Z)=>{ if(Y<SY && vox[idx(X,Y,Z)]===AIR) vox[idx(X,Y,Z)]=LEAF; };
for(const dy of [-3,-2]){ // layers radius 2 at y=H+th-3, H+th-2
  const Y=H+th+dy;
  for(let dz=-2;dz<=2;dz++)for(let dx=-2;dx<=2;dx++){
    if(dx===0&&dz===0&&dy>=-1) continue?? trunk there for dy -3,-2 → trunk occupies (0,0) — put() only writes AIR so trunk safe ✓ just call put for all; skip corners randomly:
    if(Math.abs(dx)===2&&Math.abs(dz)===2 && hash2(x*7+dx, z*7+dz*3+dy, 8811)<0.6) continue;
    put(x+dx,Y,z+dz);
  }
}
// layer radius1 at H+th-1: full 3x3
const Y1=H+th-1;
for(dz -1..1, dx -1..1) put(x+dx,Y1,z+dz);
// layer cross at H+th: 3x3 minus corners
const Y2=H+th;
for... if(Math.abs(dx)+Math.abs(dz)<=1) put; — plus maybe corners? Minecraft top layer: plus shape. ok plus.
// top plus at H+th+1: center + 4
```
Hmm total tree height: H+th+1 top leaf. Let me recheck layering: trunk top at H+th-1. Layers: (a) H+th-3 & H+th-2 → radius 2 (big skirt), (b) H+th-1 → radius 1 full, (c) H+th → plus, (d) H+th+1 → plus(center+4)? Two plus layers adjacent looks thin-topped; make (c) full 3×3 minus random corners, (d) plus. OK:

- a: dy ∈ {−3,−2} (y=H+th−3, H+th−2): r=2, corners maybe skipped
- b: y=H+th−1: r=1 full
- c: y=H+th: r=1, skip corners
- d: y=H+th+1: plus (center+orth)

For th=4: skirt at H+1,H+2 — low skirt ✓ classic oak.

flyH raise: radius 2 → matches skirt; plus center column higher but +2 margin covers (H+th+2 ≥ all leaf tops +1 ✓).

**Store per-column arrays:** topT, steepA — declare before fill loop.

**Meshing.** FACES table with precomputed AO offsets:

```js
const FACES=[
 {d:[ 1,0,0], c:[[1,0,0],[1,1,0],[1,1,1],[1,0,1]], u:[[0,0],[0,1],[1,1],[1,0]], sh:0.75},
 {d:[-1,0,0], c:[[0,0,1],[0,1,1],[0,1,0],[0,0,0]], u:[[0,0],[0,1],[1,1],[1,0]], sh:0.58},
 {d:[0, 1,0], c:[[0,1,0],[0,1,1],[1,1,1],[1,1,0]], u:[[0,0],[0,1],[1,1],[1,0]], sh:1.0},
 {d:[0,-1,0], c:[[0,0,0],[1,0,0],[1,0,1],[0,0,1]], u:[[0,0],[1,0],[1,1],[0,1]], sh:0.5},
 {d:[0,0, 1], c:[[0,0,1],[1,0,1],[1,1,1],[0,1,1]], u:[[0,0],[1,0],[1,1],[0,1]], sh:0.84},
 {d:[0,0,-1], c:[[1,0,0],[0,0,0],[0,1,0],[1,1,0]], u:[[0,0],[1,0],[1,1],[0,1]], sh:0.66},
];
// precompute AO offsets
for(const F of FACES){
  const d=F.d;
  const ax = d[0]!==0?0 : d[1]!==0?1:2;
  const t1 = ax===0?1:0, t2 = ax===2?1:2;
```
Wait choose tangents: axes ≠ ax: if ax=0 → t1=1,t2=2; ax=1 → t1=0,t2=2; ax=2 → t1=0,t2=1.
```js
  F.ao = F.c.map(c=>{
    const s1 = c[t1]? 1:-1, s2 = c[t2]? 1:-1;
    const o1=[d[0],d[1],d[2]]; o1[t1]+=s1;
    const o2=[d[0],d[1],d[2]]; o2[t2]+=s2;
    const o3=[d[0],d[1],d[2]]; o3[t1]+=s1; o3[t2]+=s2;
    return [o1,o2,o3];
  });
}
```
Careful: `c[t1]?1:-1` — c values 0/1 ✓.

AOL = [0.42, 0.62, 0.8, 1.0].

Chunk build:
```js
function buildChunk(cx, cz){
  const pos=[], col=[], uvs=[], ind=[]; let n=0;
  const x0=cx*CH, z0=cz*CH;
  for(let x=x0;x<x0+CH;x++)for(let z=z0;z<z0+CH;z++)for(let y=0;y<SY;y++){
    const t=vox[idx(x,y,z)];
    if(t===AIR||t===WATERB) continue;
    for(let f=0;f<6;f++){
      const F=FACES[f], d=F.d;
      const nb=V(x+d[0],y+d[1],z+d[2]);
      if(nb!==AIR && nb!==WATERB) continue;
      const ti=tileFor(t,f);
      const u0=(ti&3)*0.25+EPS, u1=(ti&3)*0.25+0.25-EPS;
      const row=ti>>2, v1=1-row*0.25-EPS, v0=1-(row+1)*0.25+EPS;
      const ao=[0,0,0,0];
      for(let ci=0;ci<4;ci++){
        const c=F.c[ci];
        pos.push(x-HALF+c[0], y+c[1], z-HALF+c[2]);
        uvs.push(u0+F.u[ci][0]*(u1-u0), v0+F.u[ci][1]*(v1-v0));
        const O=F.ao[ci];
        const a1=OPAQ(V(x+O[0][0],y+O[0][1],z+O[0][2]))?1:0;
        const a2=OPAQ(V(x+O[1][0],y+O[1][1],z+O[1][2]))?1:0;
        const a3=OPAQ(V(x+O[2][0],y+O[2][1],z+O[2][2]))?1:0;
        const l=(a1&&a2)?0:3-(a1+a2+a3);
        ao[ci]=l;
        const b=F.sh*AOL[l];
        col.push(b,b,b);
      }
      if(ao[0]+ao[2] >= ao[1]+ao[3]) ind.push(n,n+1,n+2,n,n+2,n+3);
      else ind.push(n+1,n+2,n+3,n+1,n+3,n);
      n+=4;
    }
  }
  if(!n) return null;
  const g=new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos,3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(col,3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uvs,2));
  g.setIndex(ind);
  g.computeBoundingSphere();
  return g;
}
```
ind as regular array → setIndex(array) auto chooses Uint16/32 based on max ✓ (three checks max index > 65535 → Uint32) ✓.

EPS = 1/128 (half texel of 64px atlas). Wait atlas 64×64 → texel = 1/64 UV per pixel; half = 1/128 ✓.

Water build:
```js
function buildWater(){
  const pos=[],col=[],uvs=[],ind=[]; let n=0;
  const quad=(p, c, u)=>{ pos.push(...p); col.push(...c); uvs.push(...u); };
  for(let z=0;z<SZ;z++)for(let x=0;x<SX;x++){
    const H=hm[x+SX*z];
    if(H>=WATER) continue;
    const depth=WATER-H;
    const s=clamp(1-depth*0.03, 0.66, 1)*0.96;
    // top quad
    const X=x-HALF, Z=z-HALF, Y=WATER;
    pos.push(X,Y,Z, X,Y,Z+1, X+1,Y,Z+1, X+1,Y,Z);
    for(let k=0;k<4;k++) col.push(s,s,s);
    uvs.push(X*0.25,Z*0.25, X*0.25,(Z+1)*0.25, (X+1)*0.25,(Z+1)*0.25, (X+1)*0.25,Z*0.25);
    ind.push(n,n+1,n+2,n,n+2,n+3); n+=4;
    // border sides
    if(x===0) side(-1); if(x===SX-1) side(1); if(z===0) side(-3)... 
  }
}
```
Write side helper inline: for face dir:
- x=0 (−x face): for y=H..WATER-1: quad corners (plane x=0): (0,y,1),(0,y+1,1),(0,y+1,0),(0,y,0) local + offsets: X=−64: corners: (X, y, Z+1),(X,y+1,Z+1),(X,y+1,Z),(X,y,Z) matching −x face pattern [[0,0,1],[0,1,1],[0,1,0],[0,0,0]] ✓ color 0.8*s? shade 0.75*s. uv: u along z: (Z+1..Z)*0.25; v along y*0.25.
Simplify: uv approximate: push (0,0),(0,1),(1,1),(1,0) scaled — water tex mirrored repeat; uv values beyond 1 fine (repeat). For sides: u=(z or x)*0.25, v=y*0.25.

I'll write a compact emit for each border:
```js
function sideQ(a,b,c,dv, s){ // 4 corner positions, uv 4 pairs
```
Eh, I'll write straightforward code with a small helper `pushQuad(vs, uvsArr, s)`.

Border condition — only if that border column has water (H<WATER) ✓; and neighbor outside is AIR ✓ always.

Also — water side visible from inside map? Never (shown earlier) ✓.

**Scene setup:**
```js
const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio||1, 2));
renderer.setSize(innerWidth, innerHeight);
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
const FOGC = 0xc9def2;
scene.fog = new THREE.Fog(FOGC, 70, 235);
const camera = new THREE.PerspectiveCamera(62, innerWidth/innerHeight, 0.1, 1600);
```
Sky dome:
```js
const SUNDIR = new THREE.Vector3(0.42, 0.58, 0.28).normalize();
const skyGeo = new THREE.SphereGeometry(950, 32, 16);
const skyMat = new THREE.ShaderMaterial({side:THREE.BackSide, depthWrite:false, uniforms:{
  hor:{value:new THREE.Vector3(0.788,0.871,0.949)},
  zen:{value:new THREE.Vector3(0.216,0.441,0.784)},
  sunD:{value:SUNDIR},
  sunC:{value:new THREE.Vector3(1.0,0.93,0.75)}
}, vertexShader:..., fragmentShader:...});
const sky = new THREE.Mesh(skyGeo, skyMat); sky.frustumCulled=false; scene.add(sky);
```
zen (0.216,0.441,0.784) = #3B70C8-ish; hor = #C9DEF2 matches fog ✓.

fragment:
```glsl
uniform vec3 hor, zen, sunD, sunC; varying vec3 vP;
void main(){
  vec3 d = normalize(vP);
  float h = d.y;
  vec3 col = mix(hor, zen, pow(clamp(h,0.0,1.0), 0.55));
  col = mix(col, hor*vec3(0.94,0.95,0.98), clamp(-h*2.2,0.0,1.0));
  float s = clamp(dot(d, sunD), 0.0, 1.0);
  col += sunC * (0.30*pow(s,5.0) + 0.5*pow(s,60.0));
  gl_FragColor = vec4(col, 1.0);
}
```
vertex: `varying vec3 vP; void main(){ vP=position; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }`

Sun sprite:
```js
function sunTexture(){
  const c=document.createElement('canvas'); c.width=c.height=64;
  const g=c.getContext('2d');
  const rg=g.createRadialGradient(32,32,2,32,32,32);
  rg.addColorStop(0,'rgba(255,246,214,0.9)');
  rg.addColorStop(0.3,'rgba(255,238,190,0.35)');
  rg.addColorStop(1,'rgba(255,238,190,0)');
  g.fillStyle=rg; g.fillRect(0,0,64,64);
  g.fillStyle='#fff8dc'; g.fillRect(24,24,16,16);  // crisp Minecraft-y square sun
  const t=new THREE.CanvasTexture(c); t.colorSpace=THREE.SRGBColorSpace; return t;
}
const sun = new THREE.Sprite(new THREE.SpriteMaterial({map:sunTexture(), transparent:true, blending:THREE.AdditiveBlending, depthWrite:false, fog:false}));
sun.scale.setScalar(120);
scene.add(sun);
```
Hmm sun square 16/64 of 120 = 30 units at 750 dist ≈ 2.3° ✓ nice.

Sun position each frame: `sun.position.copy(camera.position).addScaledVector(SUNDIR, 800);` — 800 < dome 950 ✓ inside dome, beyond fog far (fog off on sprite ✓). depthTest: sprite default depthTest true; terrain occludes ✓; dome depthWrite false → doesn't occlude ✓.

Atlas:
```js
function makeAtlas(){
  const TS=16, COLS=4, c=document.createElement('canvas');
  c.width=c.height=TS*COLS;
  const g=c.getContext('2d');
  let seed=7; const rnd=()=>{ seed=(seed*1103515245+12345)&0x7fffffff; return seed/0x7fffffff; };
  const P=(tx,ty,x,y,r,gg,b)=>{ g.fillStyle=`rgb(${r|0},${gg|0},${b|0})`; g.fillRect(tx*TS+x, ty*TS+y, 1,1); };
  const each=(ti,fn)=>{ const tx=ti&3, ty=ti>>2; for(let y=0;y<TS;y++)for(let x=0;x<TS;x++){ const col=fn(x,y); P(tx,ty,x,y,col[0],col[1],col[2]); } };
  const vary=(c,a)=>{ const v=(rnd()*2-1)*a; return [clamp(c[0]+v,0,255), clamp(c[1]+v,0,255), clamp(c[2]+v,0,255)]; };

  // 0 grass top
  each(0,(x,y)=>{ let c=vary([104,168,74],13); if(rnd()<0.10) c=[c[0]*0.82,c[1]*0.82,c[2]*0.82]; return c; });
  // 2 dirt (draw before 1 needs it? each independent)
  each(2,(x,y)=>{ let c=vary([136,97,63],13); if(rnd()<0.09) c=vary([104,72,46],8); return c; });
  // 1 grass side
  each(1,(x,y)=>{
    const edge = 3 + Math.floor(hash2(x,0,91)*3); // grass depth per column 3..5
    if(y<edge-? hmm
```
Let me: per column x, grassDepth = 3 + (hash>0.5?1:0) + (hash>0.8?1:0) → 3..5. If y < grassDepth-? For pixel (x,y): if y < gTop[x] → grass color; y == gTop → darker green edge; else dirt. Wait top of tile is y=0 ✓ grass strip at top:
```js
  const gd=[]; for(let x=0;x<TS;x++) gd.push(2+Math.floor(hash2(x,1,92)*3)); // 2..4
  each(1,(x,y)=>{
    if(y<gd[x]) { const c=vary([97,158,66],11); return c; }
    if(y===gd[x]) return vary([78,130,52],8);
    let c=vary([136,97,63],13); if(rnd()<0.08) c=vary([106,74,48],8); return c;
  });
```
  // 3 stone
```js
  each(3,(x,y)=>{ let c=vary([127,127,129],9); if(rnd()<0.08) c=vary([100,100,104],6); if(rnd()<0.05) c=vary([148,148,152],6); return c; });
```
  // 4 sand
```js
  each(4,(x,y)=>{ let c=vary([219,205,158],9); if(rnd()<0.07) c=vary([194,178,130],7); return c; });
```
  // 5 snow
```js
  each(5,(x,y)=>{ let c=vary([240,245,250],5); if(rnd()<0.07) c=vary([222,231,242],5); return c; });
```
  // 6 wood side
```js
  each(6,(x,y)=>{
    const stripe = hash2(x,3,93); // per-column tone
    let base = stripe<0.33? [96,72,45] : stripe<0.66? [108,82,52] : [88,66,40];
    let c=vary(base,7);
    if(rnd()<0.06) c=vary([70,52,32],6);
    return c;
  });
```
  // 7 wood top rings
```js
  each(7,(x,y)=>{
    const d=Math.max(Math.abs(x-7.5), Math.abs(y-7.5)); // 0.5..7.5
    const ring=Math.floor(d)%2;
    let c = ring? [122,95,60] : [156,124,80];
    if(d>6.5) c=[96,72,46]; // bark rim
    return vary(c,7);
  });
```
  // 8 leaves
```js
  each(8,(x,y)=>{ const r=rnd(); if(r<0.16) return vary([34,74,28],7); if(r<0.30) return vary([88,148,64],9); return vary([58,112,44],11); });
```
Texture:
```js
const atlas = new THREE.CanvasTexture(c);
atlas.magFilter=THREE.NearestFilter; atlas.minFilter=THREE.LinearFilter; atlas.generateMipmaps=false;
atlas.colorSpace=THREE.SRGBColorSpace;
```
Hmm — LinearFilter min without mipmaps: on minification WebGL uses bilinear — okay.

Wait: `rnd()` used inside `each` callbacks — order of evaluation per pixel deterministic ✓.

Materials:
```js
const terrainMat = new THREE.MeshBasicMaterial({map:atlas, vertexColors:true});
const waterTex = makeWaterTex(); (RepeatWrapping mirrored both axes, Nearest/Linear similar)
const waterMat = new THREE.MeshBasicMaterial({map:waterTex, transparent:true, opacity:0.74, vertexColors:true, depthWrite:false});
```
Add chunks:
```js
const worldGroup = new THREE.Group(); scene.add(worldGroup);
for cx 0..3, cz 0..3: geo=buildChunk; mesh=new THREE.Mesh(geo, terrainMat); worldGroup.add(mesh);
const waterMesh = new THREE.Mesh(buildWater(), waterMat); waterMesh.renderOrder=1; scene.add(waterMesh);
```
Clouds:
```js
function buildClouds(){
 const CN=48, CS=8, TH=1.6, CY=76;
 const raw=new Uint8Array(CN*CN), occ=new Uint8Array(CN*CN);
 for(let j=0;j<CN;j++)for(let i=0;i<CN;i++) raw[i+j*CN] = hash2(i,j,3131)<0.40?1:0;
 for(let j=0;j<CN;j++)for(let i=0;i<CN;i++){
   let cnt=0; for(let dj=-1;dj<=1;dj++)for(let di=-1;di<=1;di++){
     const ii=(i+di+CN)%CN, jj=j+dj; if(jj<0||jj>=CN) continue; cnt+=raw[ii+jj*CN];
   }
   occ[i+j*CN]= cnt>=5?1:0;
 }
 const at=(i,j)=> (i<0||i>=CN||j<0||j>=CN)?0:occ[i+j*CN];
 const pos=[],col=[],ind=[]; let n=0;
 const quad=(v,s,uvs)=>{ pos.push(...v); for(let k=0;k<4;k++)col.push(s,s,s); uvs&&0; ind.push(n,n+1,n+2,n,n+2,n+3); n+=4; };
```
UVs not needed (plain color material) → geometry without uv attribute; MeshBasicMaterial without map doesn't need uv ✓.
```js
 for(let j=0;j<CN;j++)for(let i=0;i<CN;i++){
   if(!occ[i+j*CN]) continue;
   const x0=(i-CN/2)*CS, z0=(j-CN/2)*CS, y0=CY, y1=CY+TH;
   // top
   quad([x0,y1,z0, x0,y1,z0+CS, x0+CS,y1,z0+CS, x0+CS,y1,z0], 1.0);
   // bottom
   quad([x0,y0,z0, x0+CS,y0,z0, x0+CS,y0,z0+CS, x0,y0,z0+CS], 0.78);
   // sides (only when neighbor empty)
   if(!at(i+1,j)) quad([x0+CS,y0,z0, x0+CS,y0,z0+CS, x0+CS,y1,z0+CS, x0+CS,y1,z0], 0.9);
   if(!at(i-1,j)) quad([x0,y0,z0+CS, x0,y0,z0, x0,y1,z0, x0,y1,z0+CS], 0.9);
   if(!at(i,j+1)) quad([x0+CS,y0,z0+CS, x0,y0,z0+CS, x0,y1,z0+CS, x0+CS,y1,z0+CS], 0.92);
   if(!at(i,j-1)) quad([x0,y0,z0, x0+CS,y0,z0, x0+CS,y1,z0, x0,y1,z0], 0.92);
 }
 geometry...
}
```
Check windings: top face corners (x0,z0),(x0,z0+CS),(x0+CS,z0+CS),(x0+CS,z0) = pattern (00,01,11,10) viewed from +y — matches my top face ✓ CCW from above ✓. Bottom: (00,10,11,01) matches bottom face ✓. +x side at x0+CS: corners (y0,z0),(y0,z0+CS),(y1,z0+CS),(y1,z0): compare +x face pattern [[1,0,0],[1,1,0],[1,1,1],[1,0,1]] = (z0,y0),(z0,y1),(z1,y1),(z1,y0) — mine is (y0,z0),(y0,z1),(y1,z1),(y1,z0) — ordering differs but is it CCW from +x? Vertices: A=(y0,z0),B=(y0,z1),C=(y1,z1),D=(y1,z0). Cross (B−A)×(C−A): B−A=(0,0,CS), C−A=(CS,0,CS)?? wait A=(x, y0, z0): B−A = (0,0,CS); C−A = (0,TH,CS). cross = (0,0,CS)×(0,TH,CS) = (0*CS−CS*TH, CS*0−0*CS, 0*TH−0*0) = (−CS·TH, 0, 0) → −x direction ✗ wrong winding! Let me recompute: cross((0,0,c),(0,t,c)) = (0·c − c·t, c·0 − 0·c, 0·t − 0·0) = (−ct, 0, 0). Yes −x. So flip: use corners (x0+CS,y0,z0+CS),(x0+CS,y0,z0),(x0+CS,y1,z0),(x0+CS,y1,z0+CS)?? Let me just take the standard +x face pattern with axes mapping: corners [[1,0,0],[1,1,0],[1,1,1],[1,0,1]] = (x1,y0,z0),(x1,y1,z0),(x1,y1,z1),(x1,y0,z1). So quad args: [x1,y0,z0, x1,y1,z0, x1,y1,z1, x1,y0,z1] ✓ use that. Similarly derive others from FACES patterns:

+x: [x1,y0,z0, x1,y1,z0, x1,y1,z1, x1,y0,z1]
−x: [[0,0,1],[0,1,1],[0,1,0],[0,0,0]] → [x0,y0,z1, x0,y1,z1, x0,y1,z0, x0,y0,z0]
+z: [[0,0,1],[1,0,1],[1,1,1],[0,1,1]] → [x0,y0,z1, x1,y0,z1, x1,y1,z1, x0,y1,z1]
−z: [[1,0,0],[0,0,0],[0,1,0],[1,1,0]] → [x1,y0,z0, x0,y0,z0, x0,y1,z0, x1,y1,z0]
top: [[0,1,0],[0,1,1],[1,1,1],[1,1,0]] → [x0,y1,z0, x0,y1,z1, x1,y1,z1, x1,y1,z0] ✓ matches
bottom: [[0,0,0],[1,0,0],[1,0,1],[0,0,1]] → [x0,y0,z0, x1,y0,z0, x1,y0,z1, x0,y0,z1] ✓ matches mine ✓

I'll use these exact patterns for cloud sides. Same patterns needed for water border sides — reuse constants: SIDE_QUADS keyed by dir sign. Let me define helper:

```js
const SIDE={ '+x':[[1,0,0],[1,1,0],[1,1,1],[1,0,1]], '-x':[[0,0,1],[0,1,1],[0,1,0],[0,0,0]], '+z':[[0,0,1],[1,0,1],[1,1,1],[0,1,1]], '-z':[[1,0,0],[0,0,0],[0,1,0],[1,1,0]] };
```
For water sides: for each corner [cx,cy,cz] → position (x + cx (adjusted for border plane), y+cy, z+cz) where for +x face at block x=SX−1: cx=1 → x+1 = SX ✓ same formula as terrain (corner offsets relative to block). So water sides can be emitted exactly like terrain faces using FACES entries 0,1,4,5 with block coords (0,y,z) etc. Nice: I'll reuse FACES with a generic emitQuad(F, blockX,blockY,blockZ, colorScale, uvMode...). Simplify: write water sides with FACES:

```js
const borders=[[0,0,1],[SX-1,0,1],[0,0,2]... ] meh.
```
I'll code water sides explicitly:
```js
function waterSide(f, x, z, H, s){
  const F=FACES[f]; // f in {0,1,4,5}
  for(let y=H;y<WATER;y++){
    ... push 4 corners with uv (worldu*0.25 etc), color s
  }
}
```
uv for sides: use F.u patterns: u = (horizontal coord)*0.25, v = y*0.25: For +x face: F.u = [[0,0],[0,1],[1,1],[1,0]]: u corresponds to z: corner0 z=z → u=z*0.25? I'd like world-continuous: u=(z+cz)*0.25, v=(y+cy)*0.25. For ±z faces: u=(x+cx)*0.25, v=(y+cy)*0.25. For x-faces: u=(z+cz)*0.25, v=(y+cy)*0.25. Write accordingly.

OK.

**Cloud material:** `new THREE.MeshBasicMaterial({vertexColors:true, transparent:true, opacity:0.5, depthWrite:false})`. Add fog default true ✓.

Hmm one issue: cloud opacity 0.5 white over bright sky → visible ✓; over sun additive — fine.

**Letterbox + caption + fade logic.**

**Camera path build code:**

```js
// --- points of interest ---
let peak={x:64,z:64,h:0};
for(let z=2;z<SZ-2;z++)for(let x=2;x<SX-2;x++){ const h=hm[x+SX*z]; if(h>peak.h) peak={x,z,h}; }
const peakP = new THREE.Vector3(peak.x-HALF, peak.h+2.5, peak.z-HALF);

// beach POI: nearest column with topT===SAND && hm===13or14 to (36,36)?? search:
function nearestCol(tx,tz,pred){ let best=null,bd=1e9; for(z..)for(x..){ if(pred(x,z)){ const d=(x-tx)^2+(z-tz)^2; if(d<bd){bd=d;best={x,z};} } } return best; }
const beach = nearestCol(36+HALF, 40+HALF, (x,z)=> hm[x+SX*z]>=13 && hm[x+SX*z]<=14 && x>HALF); // prefer east half? hmm pred with x> HALF restricts east — could fail if no beach east... coast exists all around south; east coast at x near 64? East edge x=127 is boundary — coast bends. Use x >= 40 (east-ish). If null → relax: any sand. I'll implement with fallback.
const coastPOI = new THREE.Vector3(beach.x-HALF, 14.5, beach.z-HALF);
```
Hmm y for beach POI: 14.5 fixed near water level ✓.

```js
// forest POI
let fbest={n:0,c:null};
for(const t of trees){ let n=0,sx=0,sz=0; for(const u of trees){ const d=Math.max(Math.abs(u.x-t.x),Math.abs(u.z-t.z)); if(d<12){n++;sx+=u.x;sz+=u.z;} } if(n>fbest.n) fbest={n,c:{x:sx/n,z:sz/n,h:t.h}}; }
const forestPOI = fbest.c? new THREE.Vector3(fbest.c.x-HALF, fbest.c.h+7, fbest.c.z-HALF) : new THREE.Vector3(10, 20, -10);
```
O(trees²) — trees ~150 → 22k ops fine.

```js
// west sea POI: water column nearest (-54+HALF=10?? centered -54 → x=10) hmm nearest to centered (−50, 16) → grid (14, 80): pred hm< WATER-1.
const westSea = nearestCol(14, 80, (x,z)=> hm[x+SX*z] <= WATER-3);
const westPOI = new THREE.Vector3(westSea.x-HALF, WATER+2, westSea.z-HALF);
// south deep POI nearest centered (−6,54) → grid (58, 118)
const deep = nearestCol(58, 118, (x,z)=> hm[x+SX*z] <= WATER-5);
const seaPOI = new THREE.Vector3(deep.x-HALF, WATER+2, deep.x?? z-HALF);
```
Fallbacks if null: use fixed positions (e.g., westPOI = (−52, 14, 10); seaPOI = (−6, 14, 52)). I'll make nearestCol return null and handle.

Actually guaranteed: sea in south half — hm ≤ 7 exists surely (deep areas). West: bias at z centered ~16 → wz=80 → bias −0.25 → some water on west too but not guaranteed near west edge... fallback fine.

**CP snapping:**
```js
const CP=[
 [-26, 50, 3.2],[ 20, 54, 3.0],[ 46, 36, 3.6],[ 52, 10, 6.0],[ 30,-14, 5.0],[ 2,-32,12.0],[-26,-44,15.0],[-48,-28,12.0],[-56, 4, 6.0],[-44, 32, 4.0],[-8, 58, 3.0]
];
// snap peak flank points
let v5=new THREE.Vector3(CP[5][0],0,CP[5][1]).sub(new THREE.Vector3(peakP.x,0,peakP.z)); 
```
Wait: CP5 = peak + dir(CP5_orig − peak)*16:
```js
const pk2=new THREE.Vector3(peakP.x,0,peakP.z);
let d5=new THREE.Vector3(CP[5][0]-pk2.x,0,CP[5][1]-pk2.z); if(d5.length()<1) d5.set(1,0,1); d5.normalize();
CP[5][0]=pk2.x+d5.x*16; CP[5][1]=pk2.z+d5.z*16; CP[5][2]=11.5;
let d6=new THREE.Vector3(CP[6][0]-pk2.x,0,CP[6][1]-pk2.z); d6.normalize();
CP[6][0]=pk2.x+d6.x*24; CP[6][1]=pk2.z+d6.z*24; CP[6][2]=15.5;
```
Peak at north (z≈−45?) — CP5 (2,−32) is south-east of peak → dir points SE ✓ CP6 (−26,−44): near peak west → dir W-ish ✓ gives pass-by west side. Good.

```js
// valley snap along CP3→CP5
let bv=1e9, bp=null;
for(let s=0.15;s<=0.85;s+=0.05){
  const x=CP[3][0]+(CP[5][0]-CP[3][0])*s, z=CP[3][1]+(CP[5][1]-CP[3][1])*s;
  const g=flyGround(x,z); if(g<bv){bv=g;bp=[x,z];}
}
CP[4][0]=bp[0]; CP[4][1]=bp[1]; CP[4][2]=5.0;
```
flyGround(x,z): grid lookup: 
```js
function flyGround(x,z){ const gx=clamp(Math.round(x+HALF),0,SX-1), gz=clamp(Math.round(z+HALF),0,SZ-1); return flyH[gx+SX*gz]; }
```
Note flyH filled AFTER trees (raised) — order: fill columns → trees (raise flyH, cap at WATER) → then path. ✓ flyH water: after trees: `flyH[i]=Math.max(flyH[i], WATER)`.

Hmm wait — flyH for water should be WATER (fly above surface) ✓; for land H (top block y = H−1; standing surface at y=H) — clearance measured from y=H ✓ camera at H+cl: cl 3 → 3 above ground surface ✓.

**Curves & sampling:**

```js
const cCurve=new THREE.CatmullRomCurve3(CP.map(p=>new THREE.Vector3(p[0],0,p[1])), true, 'centripetal', 0.5);
const kCurve=new THREE.CatmullRomCurve3(CP.map(p=>new THREE.Vector3(p[0],p[2],p[1])), true, 'centripetal', 0.5);
const NS=1024, camPts=[], minY=new Float32Array(NS);
for(let i=0;i<NS;i++){
  const u=i/NS, p=cCurve.getPointAt(u), k=kCurve.getPointAt(u).y;
  const g=flyGround(p.x,p.z);
  minY[i]=g+k; camPts.push(new THREE.Vector3(p.x,0,p.z));
}
let ys=Float32Array.from(minY);
for(let it=0; it<3; it++){
  const t2=Float32Array.from(ys);
  for(let i=0;i<NS;i++) ys[i]=Math.max((t2[(i+NS-1)%NS]+2*t2[i]+t2[(i+1)%NS])/4, minY[i]);
}
for(let i=0;i<NS;i++) camPts[i].y=ys[i];
function sampleArr(arr,u,out){ const f=(((u%1)+1)%1)*arr.length?? 
```
careful: samples i correspond u_i=i/NS; sample at u → f = u*NS; i0=floor(f)%NS; i1=(i0+1)%NS; a=frac; out.lerpVectors(arr[i0],arr[i1],a) ✓.

Look curve:
```js
const gHill = flyGround(46,8);
const LOOKPTS=[
 coastPOI,
 new THREE.Vector3(46-HALF, gHill+5, 8-HALF),       // east hills
 new THREE.Vector3(CP[4][0], flyGround(CP[4][0],CP[4][1])+3, CP[4][1]), // pass
 peakP.clone(),
 new THREE.Vector3(-46, flyGround(-46,-20)+7, -20), // west ridge
 westPOI
];
const lCurve=new THREE.CatmullRomCurve3(LOOKPTS, true, 'centripetal', 0.5);
const NL=512, lookPts=[], lookMin=new Float32Array(NL);
for(i){ u=i/NL; p=lCurve.getPointAt(u); lookPts.push(p); lookMin[i]=flyGround(p.x,p.z)+1.6; }
smooth look y similarly 2 passes with max.
```
Wait valley POI y uses flyGround+3 ✓. east hills POI ground via flyGround at (46,8) ✓.

**Focus:**
```js
const FOCUS=[
 {a:0.02,b:0.135,p:coastPOI,s:0.75},
 {a:0.205,b:0.305,p:forestPOI,s:0.6},
 {a:0.365,b:0.505,p:peakP,s:0.95},
 {a:0.565,b:0.69,p:westPOI,s:0.6},
 {a:0.80,b:0.93,p:seaPOI,s:0.55},
];
```
Check camera CP indices ↔ u: cumulative distances (with snaps, approx): earlier total ~360. CP4 u≈ (46+32+27+33)/360=0.38?? hmm earlier I estimated CP4 at u 0.31 with slightly different points. Let me recompute cumulative with current CP (post-snap approx):
CP0(−26,50)→CP1(20,54): 46.2
→CP2(46,36): √(26²+18²)=31.6 (cum 77.8)
→CP3(52,10): √(36+676)=26.8 (104.6)
→CP4(30,−14): √(484+576)=32.6 (137.2)
→CP5(snap ~ peak+16 SE): peak≈? unknown exactly; assume CP5≈(6,−38)? dist CP4→CP5 ≈ √(576+576)=33.9 (171.1)
→CP6 (peak+24 W?)≈(−20,−47): ≈27.9 (199)
→CP7(−48,−28): √(784+361)=33.8 (232.8)
→CP8(−56,4): √(64+1024)=33 (265.8)
→CP9(−44,32): √(144+784)=30.5 (296.3)
→CP10(−8,58): √(1296+676)=44.4 (340.7)
→CP0: √(324+64)=19.7 (360.4)
Total 360. u_i: CP2=0.216, CP3=0.29, CP4=0.381, CP5=0.475, CP6=0.552, CP7=0.646, CP8=0.738, CP9=0.822, CP10=0.946.

Hmm! That shifts my schedule: coast CP2 at u 0.216 → t=11.2s (LOOP 52). Forest CP4 u .381 → 19.8s. Summit CP6 u 0.552 → 28.7s — too late for the 30s window! And CP10→CP0 gap small (19.7) makes Catmull arc density uneven — fine but schedule late.

Fix options: increase LOOP? No — need summit ≤ ~27s. Reorder route: visit peak earlier — make the route go: sea → coast → up the EAST side quickly to peak (u~0.35) → west ridge → descend → long sea stretch home. Reduce pre-peak points: 

New CP plan:
```
CP0 (−26, 50, 3.2)   sea SW — start
CP1 ( 26, 52, 3.0)   sea S (long glide, coast ahead)
CP2 ( 48, 30, 4.0)   round SE corner over beach
CP3 ( 50,  2, 6.0)   east hills climb
CP4 ( 30,-16, 5.0)   valley pass (snap)
CP5 (  4,-34,11.5)   peak flank approach (snap)
CP6 (-24,-46,15.5)   beside summit (snap)
CP7 (-48,-30,12.0)   west ridge descend
CP8 (-56,  6, 6.0)   west slope
CP9 (-42, 34, 4.0)   SW coast
CP10 ( 2, 58, 3.0)   south sea, heading back east
```
Same 11 but shifted north earlier: CP2 (48,30) closer to corner. Distances: CP0→1: 52.1; 1→2: √(484+484)=22.1?? (26→48 dx22, 52→30 dz−22) = 31.1; 2→3: √(4+784)=28.1; 3→4: √(400+196)=24.4; 4→5: ~30; 5→6: ~28; 6→7: ~33; 7→8: √(64+1296)=36.9; 8→9: √(196+784)=31.3; 9→10: √(2500+576)=55.4; 10→0: √(784+64)=29.1. Total ≈ 52+31+28+24+30+28+33+37+31+55+29 = 379. Cum: CP2 0.219, CP3 0.293, CP4 0.357, CP5 0.436, CP6 0.510, CP7 0.597...

Still summit (CP6) at u .51 → 26.5s; focus window 0.40–0.52 → t 21–27 ✓ camera beside summit ~24–29s. Vista descent 29–35s. Hmm the "everything by 30s": summit reveal by 27 ✓; wide vista partially by 30 ✓. Sea/beach: CP1–CP3 0.14–0.29 → 7–15s ✓. Forest: between CP3–CP5 (0.29–0.44 → 15–23s) focus forest 0.27–0.38 (14–20s) ✓. 

Alternatively shorten pre-peak by removing CP1? Route density fine. Let me finalize focus windows:
```
{a:0.03,b:0.15,p:coastPOI,s:0.7},    // t 1.6–7.8 coast gaze from sea
{a:0.27,b:0.385,p:forestPOI,s:0.6},  // t 14–20
{a:0.40,b:0.525,p:peakP,s:0.95},     // t 20.8–27.3
{a:0.56,b:0.68,p:westPOI,s:0.6},     // t 29–35
{a:0.80,b:0.92,p:seaPOI,s:0.55},     // t 41.6–48
```
Also opening u∈[0,0.03): base look curve starts at coastPOI (first LOOKPTS point) — CatmullRom closed with getPointAt(0) = first point = coastPOI — camera at CP0 sea looks at coast immediately ✓.

But wait — look curve param vs camera: lead u+0.06: at camera u=0, look u=0.06 → look curve slightly ahead (toward east hills) — hmm opening focus (coast) overrides with w ramping from a=0.03... at u=0 w=0 → target = look(0.06) ≈ between coastPOI and eastHills — fine (island ahead).

**Recheck focus vs camera positions:**
- coast focus 0.03–0.15: camera u 0.03–0.15 → between CP0–CP1 sea glide looking at beach east ✓ sun beyond? sun at (+x,+y,+z) east-south — camera looking +x-ish → sun in frame upper area ✓.
- forest 0.27–0.385: camera CP2–CP3–CP4 over beach/hills looking at forest (which is where? forestPOI anywhere with dense trees — could be anywhere grass; unknown position relative to route... risk: forestPOI behind camera → focus yanks view backwards. Mitigate: choose forestPOI near route: pick tree cluster nearest to the route path (route known after CPs? circular dependency mild: compute route samples first, then find forest cluster minimizing distance to route with count weight). Let me: after building camPts, iterate trees clusters: score = count within 12 − distToRoute*0.15; pick best; forestPOI = centroid with y. distToRoute = min over sampled camPts (step 8) horizontal distance. ✓ robust.
- summit 0.40–0.525 ✓ peak near route ✓.
- west 0.56–0.68: camera CP6–CP7–CP8 descending west; westPOI west sea near (−50,16)? camera around x −24..−56 z −46..6 — looking WSW at sea ✓.
- south sea 0.80–0.92: camera CP9–CP10 over SW coast/sea looking at deep sea POI south ✓ loops to opening.

**Peak approach direction check:** CP5 = peak + 16 toward old CP5 (4,−34) − peak. If peak at (60?, z −50?) hmm peak likely near north-center: e.g., peak grid (70, 18) → centered (6, −46). CP5 old (4,−34): dir = (−2, +12) → normalized ≈ (−0.16, 0.99) → CP5 = (6−2.6, −46+15.8) = (3.4, −30.2) ✓ south of peak, camera climbs facing peak ✓. CP6 old (−24,−46): dir = (−30, 0) → CP6 = (−18, −46) ✓ west of peak at 24 → camera looks east at summit with focus ✓ then CP7 (−48,−30) continues west ✓ smooth.

**Clearance over canopy near peak: flyGround includes trees ✓ cl 11.5/15.5 clears canopies (canopy top ~ H+8; flyH = H+th+2 ≤ H+8; cl 11.5 > 8 ✓).

**Check CP1→CP2 over beach: CP2 (48,30): ground? wz=94 → bias −0.469, e=0.62c−0.469 — coast zone; ground maybe 10–16; cl 4 → y 14–20 ✓ skimming.

**Speed & motion smoothness:** getPointAt uniform ✓.

**Camera bob:** ±0.35 y — fine over water (cl 3 → 2.65 min) ✓ above water always.

**Look sway:** ±~0.13 rad ≈ 7.5° ✓ subtle.

**Now — performance of per-frame work:** trivial.

**Fog + dome harmony:** dome radius 950 > fog far 235: dome visible beyond fog (no fog on shader) ✓ horizon of dome shows hor color == fog color ✓ terrain fades into it ✓. Below-horizon dome slightly darker (0.94 factor) — but terrain (water) extends to edges ±64 only; beyond world edge, below-horizon dome visible → looks like sea haze? The world edge at ±64 from center; camera at ±56; looking outward at edge: terrain ends ~8–70 units away then dome below horizon — fogged terrain near edge? At distance 70–235 fog ramps; edge terrain at ~70+ partially fogged; beyond it dome under-horizon ≈ hor*0.94 ≈ fog*0.94 — slight seam possible. Mitigate: make below-horizon factor 1.0 (same as hor) → seamless. But then below-horizon dome = hor exactly = fog color → terrain fades into it perfectly ✓. Drop the darkening (or keep tiny 0.98). I'll use `mix(col, hor, clamp(-h*3.0,0,1))` → below horizon exactly hor ✓.

**Water border sides** — visible at world edge below horizon: water slab side at y 0..12 colored — with fog fading ✓ diorama look ✓.

**Also terrain border sides** — V() outside → AIR → faces emitted ✓ (bottom culled via y<0→STONE ✓... wait V returns STONE for y<0 — bottom face at y=0 has nb=STONE → culled ✓).

**OPAQ:** `(t!==AIR && t!==WATERB)` → STONE etc true; for AO occluders leaves count ✓.

**Check tileFor for SNOW sides:** all 5 ✓. WOOD top/bottom tile 7 ✓.

**Grass under trees:** trunk base at y=H replaces? topT grass at H−1 stays grass under trunk ✓ fine (Minecraft has dirt under tree — minor).

**Now the animation function:**

```js
const UP=new THREE.Vector3(0,1,0);
const camTmp=new THREE.Vector3(), lookTmp=new THREE.Vector3(), tgtTmp=new THREE.Vector3(), vecTmp=new THREE.Vector3();
let lastCapTime=...
function animate(ts){
  requestAnimationFrame(animate);
  const t=ts*0.001;
  const u=((t/LOOP)%1+1)%1;
  sampleArr(camPts,u,camTmp);
  camTmp.y += Math.sin(t*0.55)*0.3 + Math.sin(t*0.23+2.0)*0.2;
  camera.position.copy(camTmp);
  sampleArr(lookPts,(u+0.055)%1,lookTmp);
  // focus
  let tgt=vecTmp.copy(lookTmp);
  for(const f of FOCUS){
    const w=f.s*smoothstep(f.a,f.a+0.035,u)*(1-smoothstep(f.b-0.035,f.b,u));
    if(w>0) tgt.lerp(f.p,w);
  }
```
Wait smoothstep(a,b,x) with my signature smoothstep(a,b,x) ✓. Sequential lerp ok.
```js
  // sway: rotate (tgt-cam) around Y
  tgt.sub(camTmp);
  const ang=Math.sin(t*0.5)*0.05+Math.sin(t*0.21+1.3)*0.085;
  tgt.applyAxisAngle(UP,ang);
  camera.lookAt(camTmp.x+tgt.x, camTmp.y+tgt.y, camTmp.z+tgt.z);
```
careful: camTmp was used for position ✓ still holds camera pos ✓ but I mutated camTmp? I did `camTmp.y += bob` before copying to camera.position — camTmp holds final pos ✓. tgt.sub(camTmp) — vecTmp was tgt... let me rename: tgt = look vector temp. After sub & rotate, lookAt(camPos+tgt) ✓.
```js
  sky.position.copy(camera.position);
  sun.position.copy(camera.position).addScaledVector(SUNDIR,800);
  clouds.position.x = -((((t*1.6)%CLOUDSPAN)+CLOUDSPAN)%CLOUDSPAN);
  waterTex.offset.set((t*0.012)%1, (t*0.007)%1);
  renderer.render(scene,camera);
}
requestAnimationFrame(animate);
```
MirroredRepeat wrapping with offset — fine (offset works with mirrored repeat ✓).

CLOUDSPAN = CN*CS = 384.

Hmm — clouds drifting −x with wrap 384 ✓ pattern period 384 in x ✓ seamless.

Wait — cloud group spans x ∈ [−192,192] centered; when group shifts by −s (s∈[0,384)), coverage x ∈ [−192−s, 192−s] — at s=0 coverage [−192,192] — camera at x −56..56 + view distance 235 → need clouds up to x ~ 56+235=291 > 192! Not covered at s=0 east side; at s=380: coverage [−572,−188] — nothing near camera! Broken. Fix: duplicate: add second cloud mesh at +CLOUDSPAN offset (child at x=+384): combined coverage [−192+s'...]. With group shift s and child2 at x+384: coverage [−192−s, 192−s] ∪ [192−s, 576−s] = [−192−s, 576−s] — always covers [−192, 192+?]... at s=0: [−192,576] ✓; s=384: [−576,192] ✓. Camera needs [camx−235, camx+235] ⊂ [−291, 291] ⊂ [−192−s,576−s] for all s? At s=0: [−192,576] covers [−291?NO: −291 < −192 ✗ west gap at s≈0. Add child3 at −384: coverage [−576−s, 576−s] ✓ always covers ±291 ✓. So 3 copies (original + x+384 + x−384). Or reduce needed: fog far 235 → clouds visible to ~235; camx range +56 (CP3 x 50, east) → need up to 291; west camx −56 → −291. With 2 copies (0, +384): coverage [−192−s, 576−s]: at s=0 → [−192,576]: west needs −291 ✗. So 3 copies. Cheap (geometry shared? each mesh own geometry — build one geometry, three meshes sharing it ✓).

Wait actually simpler: make cloud field wider: CN=96 cells? 96×8=768 span, cells 96²=9216, occupancy ~0.3 → 2700 cells → faces ~ 2700*2+perim ~ 7000 — fine too. But pattern period must equal full span for seamless wrap → CN=96 span 768: coverage needed 582 < 768 ✓ single mesh covers [−384−s, 384−s] ⊇ [−291,291] for s ∈ [0,768)? At s=0: [−384,384] ✓; s=768 wraps to 0 ✓; s=100: [−484,284] — need up to +291 ✗ marginal! camx max 50+? CP3 x=50, fog 235 → 285 > 284 ✗ borderline. Use CN=104 (span 832): [−416−s, 416−s] worst s→0: +416 ✓ −416 ✓ covers ±291 ✓ for all s? coverage always width 832 centered −s: worst case s=416: [−832, 0]?? no: coverage [−416−s, +416−s]; at s=416: [−832, 0] — east side needs +291 ✗!! Because wrap shifts pattern; near s=416 the whole field shifted west by 416 → east sky empty until wrap. So single field insufficient regardless of width unless width ≥ span+needed... The 3-copy approach with period 384: three copies at offsets {0,+384,−384} inside group; group shift s∈[0,384): union coverage [−192−s−384, 192−s+384] = [−576−s, 576−s] — always contains [−291,291]? At s=0: [−576,576] ✓; s=383: [−959,193]?? 576−383=193 < 291 ✗!! Hmm wait recompute: copies at c ∈ {−384,0,384} each covering [c−192−s, c+192−s]. Union: [−384−192−s, 384+192−s] = [−576−s, 576−s]. At s=380: [−956, 196] — east limit 196 < 291 ✗. Grr — because the union is contiguous only spanning copies' outer edges: union is [min c −192 −s, max c +192 −s] = [−576−s, 576−s] — contiguous ✓ but shifts with s. To guarantee fixed coverage [−291,291] for all s∈[0,384): need max c +192 − 384 ≥ 291 → max c ≥ 483 → c max = 768? With copies at {−384,0,384} the top cover at s=384⁻: 384+192−384=192. Need copies spaced ≤ 2*192=384 apart AND extend beyond: add copies at ±768: union [−960−s, 960−s]: at s=384: [−1344, 576]?? wait s∈[0,384): min coverage east = 960−384=576?? no: east edge = 960−s ≥ 960−384=576 ✓ ≥291 ✓; west edge = −960−s ≤ −960 ✓. So copies at {−768,−384,0,384,768} (5 copies) guarantee coverage. That's because wrap s resets at 384 — at s→384⁻, pattern has moved almost a full period west, needing copy at +768 to fill east. 5 copies × ~700-cell geometry sharing one geometry — 5 draw calls, fine. Alternatively animate by repositioning: keep ONE mesh and wrap its x with modulo such that coverage maintained — impossible with single fixed-coverage... Standard solution: 5 copies sharing geometry — fine and simple. Actually reduce copies by making cell grid wider than period? Period must equal pattern width for seamless wrap — pattern width = CN*CS fixed. Copies needed = ceil((2*(fogfar+camrange) + width)/width)?? = ceil((582+?)/384)... coverage needed width 582; with copies spaced 384 covering contiguous 384*ncopies −? Each copy width 384 spaced 384 → contiguous band of width 384*n centered? Not centered — anchored: union width 384n; need union ⊇ [−291,291] for all s ∈ [0,384): union [−(192+384k)−s, ...] as computed → need k=2 each side (5 copies). Alternatively make span bigger: CN=72 (span 576): copies at {−576,0,576} → union [−864−s, 864−s], s∈[0,576): east edge ≥ 864−576=288 < 291 marginal ✗. CN=80 (640): copies {−640,0,640}: east ≥ 960−640=320 ✓ west ≤ −320−? west edge −960−s ✓. So CN=80 cells (span 640, 3 copies). Cells 80²=6400 → occ ~1900 → faces ~5k ✓ 3 draw calls ✓. 

Hmm wait CN=80: coverage per copy [c−320, c+320]; copies at −640,0,640; union [−960,960] shifted by −s: [−960−s, 960−s]; s∈[0,640): east edge min = 960−640=320 ✓ ≥291 ✓; west edge max = −960−0=−960 ≤ −291 ✓. ✓ 3 copies.

CN must relate to hash periodicity: pattern periodic with period CN in i — wrap shift by CN*CS=640 seamless ✓ (drift modulo 640).

Set CN=80, CS=8, occupancy threshold tune: raw p=0.38, cluster ≥5 → final density? rough — fine.

Also clouds should not intersect mountains: CY=76 > 52+? peaks ≤52 ✓ (leaves none up there) ✓.

**Cloud drift speed:** 1.6 u/s slow ✓.

**Water offset speeds** small ✓.

**Check getPointAt cost per frame:** look curve getPointAt: uses cached arc lengths ✓ O(1) after init.

**Init order:** 
1. constants & noise
2. world gen (vox, hm, topT, steepA, trees, flyH)
3. atlas & textures & materials
4. mesher → meshes
5. clouds
6. sky, sun, fog, renderer
7. POIs, CP snap, curves, samples, focus
8. events, animate.

**topT & steepA storage:** 
```js
const topT=new Uint8Array(SX*SZ), steepA=new Uint8Array(SX*SZ);
```
Fill in column loop.

Tree condition uses topT===GRASS && !steepA && H≥16 (hm).

Hmm wait: steep computation: gradient from elevation — 4 extra elevation() calls per column — elevation cost: 3 fbm (4+4+3=11 vnoise, each 4 hashes + math) ≈ 44 hashes → 5 calls = 220 hashes/column ×16384 = 3.6M — ok (~50ms). Could reduce by computing gradient from hm after (integer heights): steep via neighbor hm? But hm computed in same loop — compute steepness in second pass using hm (cheap!). Do: first pass fill columns w/o steep; second pass compute steep from hm neighbors: |hm[x+1]−hm[x−1]| + |hm[z+1]−hm[z−1]| > 3 → steep. But top assignment already done without steep... Reorder: pass1 compute H & topT (without steep), pass2 apply steep override: if steep && top is GRASS → change top block to STONE and also the dirt band? Changing top after fill: re-voxel top cells: set vox top to STONE. Since top block at y=H−1: `if(steep && topT===GRASS){ vox[idx(x,H-1,z)]=STONE; topT=STONE; }` — also band below remains dirt — visible? side faces show dirt under stone cap — meh acceptable... Or set band too: for y in H−4..H−1 if vox is GRASS/DIRT → STONE? That makes steep hills rocky — nice. Do: `for(let y=Math.max(0,H-4); y<H; y++) if(vox===GRASS||vox===DIRT) vox=STONE; topT=STONE;` ✓ cheap.

Also trees check topT after steep pass ✓ order: pass1 fill → pass2 steep → trees → flyH water-cap → POIs/path.

**Water cap:** after trees (flyH raised for trees) → cap `Math.max(flyH[i], WATER)` ✓.

**Now — the terrain material side: DoubleSide?** Faces emitted only where visible from outside; winding correct → FrontSide ✓ default.

**Water material side:** FrontSide ✓ (top visible from above; sides from outside). Underwater looking up? Camera never underwater ✓.

**Leaves both sides?** culled as opaque ✓.

**Check chunk mesh count:** 16 chunks; empty chunks (all air? never — terrain everywhere ≥3) ✓.

**Also — "grass-topped hills" with sand at H≤14: interior low areas (valleys at H 13–14) become sand flats — reads as dry lakebeds/meadows — acceptable, but maybe restrict sand to near-water: sand if H≤14 AND (H≤14 && anyNeighborColumn H≤12 within distance 6?) — expensive-ish. Alternative: sand if H ≤ 13 (tight beach: H 12–13? hmm at waterline H=12 exactly at water surface; beach 13–14 gives 1–2 above water. Inland valleys with H 13–14 are rare (transition zone near coasts only, since e≈0 band is coastal). Actually e∈[0,0.1] inland? e = cont*0.62+bias — inland bias ~0 → e=cont could be near 0 in mid-island → low flats mid-island possible → sand flats there. That's fine visually (sandy clearings). Keep simple.

**Numbers audit for water depth shade:** depth up to 9 → s = 1−0.27=0.73 ✓.

**Renderer clear color:** dome covers everything ✓ but set clear color to fog color anyway.

**Camera far 1600 > dome 950+offset ✓.**

**Potential z-fighting: none coplanar except water top vs sand top? Different cells ✓.

**Check focus POI y for coastPOI: 14.5 — camera high later? fine.

**lookPts smoothing: lookMin enforce: some look samples might dip under terrain when curve crosses a hill between POIs — enforce max(ground+1.6) ✓ then light smoothing... but enforcing after smoothing creates steps; look target height steps cause slight view jitter — 1-unit steps at distance — imperceptible. Do: y=max(y, min) then one gentle smooth WITHOUT re-enforce (violations ≤ ~0.5 → target may clip hill crests by 0.5 occasionally — viewing from afar, a target slightly inside a hillside means camera looks "at" the hill — visually fine (it's looking at terrain anyway). OK: smooth 2 passes → enforce → done.

Also look target when camera near it (passing over valley POI): target ~3 above ground, camera 5 above → looking down slightly ✓.

**Sway + focus double-move** ✓ subtle.

**Fog on terrain material:** MeshBasicMaterial fog:true default ✓.

**Test mental image of opening frame:** t=0: camera at CP0 (−26, ~15.2, 50), y≈15 (3.2 above water). Look: lookPts at u=0.055 → between coastPOI and eastHills... coastPOI ≈ (beach near east (36,34)?) → direction from camera: Δ=(~62, 0, −16) → looking east-north-east across sea toward coast ✓ island fills frame ✓ sun ENE-ish high (SUNDIR (0.42,0.58,0.28): east, 54° elev, slightly +z) — looking +x: sun ahead-up ✓ beautiful backlit-ish.

Wait coastPOI x: beach nearest to (36+? I said nearestCol(36+HALF?? centered (36, 34) → grid (100, 98)). Beach near there: coast zone z≈28–45 at east ✓ plausible; if noise puts water there, fallback finds nearest sand to that point ✓.

**Caption fade & letterbox**: implement with small script at end:
```js
setTimeout(()=>{ document.getElementById('cap').style.opacity='0'; }, 6500);
```
Letterbox stays. (Use class not duplicate id.)

**One more detail — `renderer.setAnimationLoop` vs rAF: requirement says use requestAnimationFrame timestamp → use rAF explicitly ✓.

**Import map provided externally — I must NOT add my own. Just import 'three'.** ✓

**Check: no OrbitControls needed; no addons.**

**Edge case: WebGPU? no.**

**Write out water side quads with FACES reuse:** I'll write dedicated code:

```js
function pushWaterSide(f, x, z, H, s){
  const F=FACES[f], d=F.d;
  for(let y=H;y<WATER;y++){
    const base=wn; // current vertex count
    for(let ci=0;ci<4;ci++){
      const c=F.c[ci];
      wpos.push(x-HALF+c[0], y+c[1], z-HALF+c[2]);
      const uu = (d[0]!==0) ? (z+c[2])*0.25 : (x+c[0])*0.25;
      wuv.push(uu, (y+c[1])*0.25);
      wcol.push(s,s,s);
    }
    wind.push(base,base+1,base+2,base,base+2,base+3); wn+=4;
  }
}
```
called for border columns:
```js
if(x===0) pushWaterSide(1, x, z, H, 0.75);   // -x face index1
if(x===SX-1) pushWaterSide(0, x, z, H, 0.75);
if(z===0) pushWaterSide(5, x, z, H, 0.72);
if(z===SZ-1) pushWaterSide(4, x, z, H, 0.72);
```
face indices: 0:+x,1:−x,4:+z,5:−z ✓.

**Water top quad ordering** matches +y face pattern ✓ indices default (no AO flip needed).

**Cloud geometry build — define with plain arrays; no uv.**

**Sun glow subtle check** — additive sprite over sky → mild. ✓

**Also add a very subtle horizon haze band in sky shader?** Already horizon-colored ✓.

**Test winding for −x water side** pattern [[0,0,1],[0,1,1],[0,1,0],[0,0,0]] → at block x=0: corners (0,y,1)... position x+0=0 → world −64 ✓ outward normal −x ✓ visible from west outside ✓.

**Water top face color s applies per vertex ✓.**

**hm vs topT index consistency: i=x+SX*z ✓.**

**fbm lacunarity 2.03 offset — vnoise grid alignment fine.**

**Check elevation continuity at world border for gradient: elevation(x±1) outside centered range: elevation handles any coords (wx = x+64 could be −1..129 — noise defined everywhere ✓).

**hm floor: clamp(3..52): sea floor min 3 ✓ (e −1.1 → h = 10.4−11−... ≈ −2.8 → 3 ✓ flat deep bottom ✓ ok).

Wait sea formula: h = WATER−1.6 − d²·11 + hills*1.5 + det*1.1: at e=−0.2: d=0.235 → h=10.4−0.61±2.6 ≈ 7.2–13.6 → hmm 13.6 above WATER → islet ✓ shoreline-ish ✓. At e=−0.5: d=0.588→ d²=0.346→ h=10.4−3.8±2.6 = 4–9.2 ✓ shallow sea. Good gradual coast ✓ beaches where h∈[12,14] ✓.

**Trees density check:** forest = fbm(...)>0.18 → 0.05 — forest zones maybe 25% of grass; kept ≈ 0.05*0.55 ≈ 0.0275/col → grass cols ~7000 → ~190*0.25?? Let me: forest-zone grass columns ~2500 → ~68 trees; sparse-zone 0.007*0.55=0.0038 → ~4500 cols → 17 → total ~85 trees. Hmm a bit sparse for "forests". Raise: forest>0.15 → 0.09; mid 0.012. → ~120 + 30 = 150 trees ✓ good. Also require H≥16 && H<26 (no trees on high mountains)? grass only exists < rockLine 26 ✓ inherent.

**Also — trees not on steep ✓.**

**Check flyH for tree cells also under canopy overhang beyond trunk ±2 ✓ radius 2 ✓.

**Camera path vs tall peak: CP6 cl 15.5 from ground e.g. 30 → 45.5; summit 52 nearby at distance 24 — camera below summit looking up ✓ no collision (24 away horizontally, summit top 52 — ray from camera to peakPOI (52+2.5) passes over intermediate terrain? terrain between camera & peak along the line — peak is the max ✓ fine).

**Check CP7 (−48,−30): ground? wz=34: bias=1−2*34/128=0.469; e=0.62c+0.469 ∈ [0.03,0.86] — mountains west: ground maybe 20–40; cl 12 → y 32–52 ✓ descending from CP6 45.5 ok.

**Fine. Now — also handle context loss? skip.

**Double-check three r186 module URL:** provided importmap — just `import * as THREE from 'three'` ✓.

**Check CanvasTexture needs `texture.needsUpdate` — CanvasTexture sets needsUpdate=true automatically ✓.

**Water texture creation:**
```js
function makeWaterTex(){
  const s=32, c=document.createElement('canvas'); c.width=c.height=s;
  const g=c.getContext('2d'); const img=g.createImageData(s,s);
  for(let y=0;y<s;y++)for(let x=0;x<s;x++){
    const n=vnoise(x*0.35, y*0.7, 314);
    let r,gg,b;
    if(n>0.62){ r=88;gg=152;b=222; }
    else if(n<0.38){ r=38;gg=84;b=156; }
    else { r=54;gg=112;b=192; }
    const v=(hash2(x,y,77)*2-1)*7;
    const k=(y*s+x)*4;
    img.data[k]=r+v; img.data[k+1]=gg+v; img.data[k+2]=b+v; img.data[k+3]=255;
  }
  g.putImageData(img,0,0);
  const t=new THREE.CanvasTexture(c);
  t.wrapS=t.wrapT=THREE.MirroredRepeatWrapping;
  t.magFilter=THREE.NearestFilter; t.minFilter=THREE.LinearFilter; t.generateMipmaps=false;
  t.colorSpace=THREE.SRGBColorSpace;
  return t;
}
```
✓.

**Tile for sand under water same atlas ✓.

**Let me reconsider atlas min filter & shimmer:** distant terrain minified — LinearFilter reduces but aliasing persists; fog hides most. Accept.

**devicePixelRatio clamp 2 ✓.**

**Also — antialias with pixelated textures: MSAA affects geometry edges ✓ good.

**Check that MeshBasicMaterial vertexColors with sRGB texture multiplication appears correctly shaded (linear multiply) ✓ intended.

**Check possible issue: chunks at world border use V() out-of-bounds → AIR ✓ sides drawn ✓.

**Check indices type:** three setIndex(array) → chooses Uint32BufferAttribute if any value > 65535 (via arrayNeedsUint32) ✓.

**Chunk geometry position count:** could exceed 65535 verts — indices handle ✓ (positions fine as Float32).

**GC:** building arrays via push — hundreds of thousands of pushes — fine (~100ms).

**Now — write the final HTML. Also include graceful WebGL check? minimal try/catch — skip, keep lean but robust.

**Caption element with class; letterbox divs.**

Let me also double check `sampleArr`:
```js
function sampleArr(arr,u,out){
  const f=(((u%1)+1)%1)*arr.length; // arr.length = NS
  const i0=Math.floor(f)%arr.length, i1=(i0+1)%arr.length, a=f-Math.floor(f);
  out.lerpVectors(arr[i0], arr[i1], a);
  return out;
}
```
Note: sample u corresponds to position between i0 and i1 — points spaced 1/NS of loop ✓ consistent for cam & look (different NS each — use arr.length generic ✓).

**Focus lerp target heights:** focus p fixed ✓.

**One risk — lookPts base curve might make camera look through a mountain ridge between POIs (target behind ridge) — view shows ridge instead of POI: acceptable cinematic (looking at terrain). The focus windows pin the important views ✓.

**Also — initial frames before textures loaded:** CanvasTexture immediate ✓ no async.

**Total draw calls:** 16 terrain + 1 water + 3 clouds + dome + sprite ≈ 22 ✓.

**Let me also confirm the AO darkening doesn't over-darken grass tops at tree bases (leaves occlude) — tree shadows on ground: side1/side2/corner around trunk → dark patch under canopy — actually nice (fake shadow).

**Water top AO? none (no AO for water) ✓.

**Now write everything out.** I'll be meticulous about syntax. Let me also predefine `AOL`, `EPS`.

One more think about `kCurve` clearance interpolation — CP cl values: [3.2,3.0,4.0,6.0,5.0,11.5,15.5,12.0,6.0,4.0,3.0] — CatmullRom through (x, cl, z) points: y interpolates smoothly ✓ but centripetal parameterization may overshoot cl slightly between points (e.g., 3.2→3.0 fine; 4→6→5 mild) — overshoot harmless.

Also clearance CP2 4.0 over beach skim — ground at beach ~12–16 (above water): camera 16–20 ✓.

Wait CP2 (48,30) ground could be water (12) → y 16 ✓.

**Check flyGround at CP positions uses grid — includes water cap ✓.

**Potential problem: camera path near world edge CP8 x=−56 (grid x=8): border at −64 — 8 units from edge, fine.

**Also — make sure `hm` fill uses Math.floor of eC but eC computed with x−HALF (integers) — consistent with elevation used in gradient? gradient uses elevation(x±1−HALF) ✓.

**Steep pass:**
```js
for(let z=0;z<SZ;z++)for(let x=0;x<SX;x++){
  const hx1=hm[Math.min(SX-1,x+1)+SX*z], hx0=hm[Math.max(0,x-1)+SX*z];
  const hz1=hm[x+SX*Math.min(SZ-1,z+1)], hz0=hm[x+SX*Math.max(0,z-1)];
  if(Math.abs(hx1-hx0)+Math.abs(hz1-hz0) > 3){
    const i=x+SX*z;
    if(topT[i]===GRASS){
      topT[i]=STONE;
      const H=hm[i];
      for(let y=Math.max(0,H-4);y<H;y++){ const v=vox[idx(x,y,z)]; if(v===GRASS||v===DIRT) vox[idx(x,y,z)]=STONE; }
    }
  }
}
```
Hmm — also make SNOW stay on steep (snow caps steep ✓ fine).

Wait — this changes grass→stone tops on steep slopes: threshold 3 (sum of two axis diffs over 2-block span) — moderate slopes stay grass ✓.

**Bedrock nuance: none needed.**

**Sanity: SY=64 but tree max y = H+th+1 ≤ 52+6+1=59 <64 ✓.**

**Cloud geometry BufferGeometry:**
```js
const cg=new THREE.BufferGeometry();
cg.setAttribute('position', new THREE.Float32BufferAttribute(cpos,3));
cg.setAttribute('color', new THREE.Float32BufferAttribute(ccol,3));
cg.setIndex(cind); cg.computeBoundingSphere();
```
3 meshes share cg; frustumCulled: bounding sphere huge — set frustumCulled=false for clouds (always visible) ✓ simpler.

**Terrain meshes frustumCulled true with bounding spheres ✓.**

**Water mesh frustumCulled: bounding sphere covers world ✓ fine.

**Sky frustumCulled=false ✓.

Now — full code assembly. Also verify no leftover pseudo-code. Let me write it in final form, mentally compiling.

Also — `const OPAQ=t=>t!==AIR&&t!==WATERB;` used in mesher ✓.

Potential subtlety: `F.ao` built with FACES defined via object literals — I'll build after array creation.

UV EPS on v: v1 = 1−row*0.25−EPS; v0 = 1−(row+1)*0.25+EPS ✓ (v1 > v0 ✓).

Grass side v orientation: F.u v components: for side faces I set uv v = F.u[ci][1] where pattern has 0 at bottom corners (y=0) ✓ e.g. +x face u=[[0,0],[0,1],[1,1],[1,0]] corners y:0,1,1,0 ✓ v matches y ✓.

For ±z faces pattern [[0,0],[1,0],[1,1],[0,1]] corners y:0,0,1,1 ✓ ✓.

Top face: any orientation fine.

Bottom face [[0,0],[1,0],[1,1],[0,1]] — fine.

**tileFor:**
```js
function tileFor(t,f){
  switch(t){
    case GRASS: return f===2?0:(f===3?2:1);
    case WOOD:  return (f===2||f===3)?7:6;
    case DIRT: return 2; case STONE: return 3; case SAND: return 4;
    case SNOW: return 5; case LEAF: return 8;
  }
  return 3;
}
```
✓ (face 2=+y top, 3=−y bottom).

**Focus `p` are Vector3 references ✓ (peakP etc). tgt.lerp(f.p, w) — tgt is a temp copy ✓.

**camPts y smoothing uses minY — need both arrays; ok.

**Look y smoothing:**
```js
const lmin=new Float32Array(NL), lys=new Float32Array(NL);
for i: p=lCurve.getPointAt(i/NL); lookPts.push(p.clone()); lmin[i]=flyGround(p.x,p.z)+1.6; lys[i]=p.y;
smooth lys 2 passes; enforce max(lmin); assign lookPts[i].y=lys[i].
```

**Also — CP cl for CP0/CP10 etc fine.

**Hmm — one thing: `lookTmp` initial: sampleArr(lookPts, ...) ✓.

**Check letterbox CSS uses class .cine with top/bottom modifiers ✓.

**Title: "Voxel Isles".**

**Also handle `visibilitychange`? not needed (absolute-time anims).

Let me also reconsider LOOP: 52s; requirement "first 30 seconds" ✓ summit by ~27s ✓.

Also double-check first visible frame: t≈0 → u=0 → camera CP0 area ✓.

**One more possible glitch: `u+0.055` for look lead — look curve NS=512; fine.

**Sway rotation axis: UP ✓.

**Water render order vs clouds:** water renderOrder 1, clouds 2, sun default 0 → order: sun, water, clouds ✓ (transparent sorted by renderOrder first). Sun before water: sun drawn first then water blends over ✓ correct (sun behind water surface when looking at water toward sun? Sun is sky background — water in front — correct ✓).

Wait — sprites: sun.renderOrder default 0 — transparent list sorted by renderOrder then depth ✓.

**Cloud depthWrite false ✓ water depthWrite false ✓ — terrain occludes both via depth test ✓ (they test against terrain depth ✓).

**Now write final code.** I'll also add small helper `nearestCol` with fallback null.

Let me write `nearestCol`:
```js
function nearestCol(tx,tz,pred){
  let best=null, bd=1e9;
  for(let z=2;z<SZ-2;z++)for(let x=2;x<SX-2;x++){
    if(!pred(x,z)) continue;
    const d=(x-tx)*(x-tx)+(z-tz)*(z-tz);
    if(d<bd){bd=d;best=[x,z];}
  }
  return best;
}
```
Full scans ×3 — 48k iterations each ✓.

coastPOI:
```js
let b=nearestCol(100,98,(x,z)=>{const h=hm[x+SX*z]; return h>=13&&h<=14;});
if(!b) b=nearestCol(64,110,(x,z)=>{const h=hm[x+SX*z]; return h>=13&&h<=14;});
const coastPOI = b? new THREE.Vector3(b[0]-HALF, 14.5, b[1]-HALF) : new THREE.Vector3(30,14,36);
```
grid tx for centered (36,34): 100, 98 ✓.

westPOI:
```js
let w=nearestCol(12,78,(x,z)=>hm[x+SX*z]<=WATER-3);
const westPOI = w? new THREE.Vector3(w[0]-HALF, WATER+2, w[1]-HALF) : new THREE.Vector3(-50, WATER+2, 8);
```
grid (12,78) ↔ centered (−52,14) ✓.

seaPOI:
```js
let dp=nearestCol(58,116,(x,z)=>hm[x+SX*z]<=WATER-5);
const seaPOI = dp? new THREE.Vector3(dp[0]-HALF, WATER+2, dp[1]-HALF) : new THREE.Vector3(-4, WATER+2, 50);
```

forestPOI (after camPts built):
```js
let fbest=null, fbs=-1;
for(let i=0;i<trees.length;i++){
  const t=trees[i]; let cnt=0,sx=0,sz=0;
  for(let j=0;j<trees.length;j++){
    const o=trees[j];
    if(Math.abs(o.x-t.x)<=12 && Math.abs(o.z-t.z)<=12){ cnt++; sx+=o.x; sz+=o.z; }
  }
  // distance to route
  let rd=1e9;
  for(let k=0;k<NS;k+=16){ const p=camPts[k]; const dd=(p.x-(t.x-HALF))**2+(p.z-(t.z-HALF))**2; if(dd<rd)rd=dd; }
  const score=cnt-Math.sqrt(rd)*0.25;
  if(score>fbs){ fbs=score; fbest={x:sx/cnt, z:sz/cnt, h:t.h}; }
}
const forestPOI=new THREE.Vector3(fbest.x-HALF, fbest.h+7.5, fbest.z-HALF);
```
✓ (trees.length ≥1? if zero trees (unlikely) guard: if(!trees.length) forestPOI=fallback.)

**Order: camPts built → forestPOI → LOOKPTS → look samples.**

Now — final code writing. Also compute `CLOUDSPAN=640`.

Cloud occupancy threshold: raw hash<0.38 → ~0.38; cluster count≥5 of 9 → smooths to blobs; final density maybe ~0.35. 6400 cells → ~2200 cells → faces = top+bottom 4400 + sides ~ maybe 1500 → 6k faces ×3 copies ok.

Hmm CN=80 but pattern periodic period 80 in i ✓ (hash2(i,j) used directly with i∈[0,80)).

Cloud drift: `cloudsGroup.position.x = -(((t*1.6)%640+640)%640);`

**Also — clouds y 76.**

Let me also double check camera CP max y: CP6 cl 15.5 + ground(~35–45) → 50–60; clouds at 76 ✓ camera below clouds ✓.

**Sun angle: SUNDIR (0.42,0.58,0.28) normalized → (0.55,0.76,0.37)? compute: len=√(0.1764+0.3364+0.0784)=√0.5912=0.769 → (0.546,0.754,0.364). Elevation ~49°. ok.

**Dome follows camera fully (x,y,z) ✓.

**Also — camera roll: none ✓.

**Final check of the "signature" quality:** opening low sea glide with square sun + island reveal, beach skim, forest weave, summit lock-on with orbit, western sea vista, drifting block clouds, AO-shaded voxels, letterbox. Good — feels authored.

Potential visual risk: fog far 235 with world only 180 diag — from summit vista nearly everything mid-fogged; soft ✓ "soft distance fog" required ✓.

Alright — also the requirement "at least 128x128 columns" ✓ exactly 128×128.

"layered noise" ✓ continent + hills + detail fbm layers.

Let me now write the file completely.

Additional micro-details while writing:

- `elevation` name conflict none.
- Precompute per-column loop uses `const i=x+SX*z`.
- In tree placement loop I need hm & topT & steep — after passes ✓.
- trees stored as {x,z,h,th}.
- Canopy `put` guard bounds x±2 within [1,126] given trunk ∈[3,124] ✓.

Tree canopy code:
```js
function plantTree(x,z,H,th){
  const top=H+th-1;
  for(let y=H;y<=top;y++) if(vox[idx(x,y,z)]===AIR) vox[idx(x,y,z)]=WOOD;
  const put=(X,Y,Z)=>{ if(Y>0&&Y<SY&&vox[idx(X,Y,Z)]===AIR) vox[idx(X,Y,Z)]=LEAF; };
  for(const dy of [-3,-2]){
    const Y=top+dy+1; // = H+th-3, H+th-2 ✓
    for(let dz=-2;dz<=2;dz++)for(let dx=-2;dx<=2;dx++){
      if(Math.abs(dx)===2&&Math.abs(dz)===2&&hash2(x+dx*3, z*5+dz*7+dy, 8811)<0.55) continue;
      put(x+dx,Y,z+dz);
    }
  }
  for(let dz=-1;dz<=1;dz++)for(let dx=-1;dx<=1;dx++) put(x+dx,top+1,z+dz);
  for(let dz=-1;dz<=1;dz++)for(let dx=-1;dx<=1;dx++){
    if(Math.abs(dx)+Math.abs(dz)<=1) put(x+dx,top+2,z+dz);
  }
  put? top+2 = H+th+1 ✓ plus shape ✓
}
```
Wait layer b at top+1 = H+th ✓ full 3×3; layer c at top+2 = H+th+1 plus ✓. And skirt layers at top−1?? I set dy −3→Y=top−2=H+th−2 and dy −2→Y=top−1=H+th−1. Hmm I intended skirt at H+th−3 and H+th−2. Let me redefine clean:
- skirt1 y = H+th−3, skirt2 y = H+th−2 (radius 2)
- mid y = H+th−1 (radius1 full) — note trunk top at H+th−1 — trunk occupies center ✓ put only into AIR ✓
- upper y = H+th (plus)
- tip y = H+th+1 (single + orth?) — earlier plan had plus at H+th+1 and nothing higher; plus at H+th AND plus at H+th+1? I'll do: y=H+th: 3×3 minus corners; y=H+th+1: plus (center+4). Total top H+th+1 ✓.

Rewrite:
```js
for(let dy of [H+th-3, H+th-2]) { radius2 with corner skip }
for 3x3 full at H+th-1
for 3x3 minus corners at H+th
for plus at H+th+1
```
For th=4: H+th−3 = H+1 ✓ skirt low ✓.

Also trunk 1×1 at center from H..H+th−1 ✓.

Tree spacing allowed adjacent canopies merge ✓.

**flyH raise:**
```js
for(let dz=-2;dz<=2;dz++)for(let dx=-2;dx<=2;dx++){
  const fi=(x+dx)+SX*(z+dz);
  if(flyH[fi]<H+th+2) flyH[fi]=H+th+2;
}
```
✓.

**Water cap after trees:**
```js
for(let i=0;i<SX*SZ;i++) if(flyH[i]<WATER) flyH[i]=WATER;
```

**Camera path: also ensure camera stays inside bounds: CP within ±56 ✓ curve overshoot? centripetal Catmull may overshoot slightly beyond control points (a few units) — clearance sampling follows actual curve ✓ may exceed 64 edge slightly → flyGround clamps → fine; camera at x=±66 briefly over edge void — ground clamped to edge column heights — visually flying just outside the slab edge — acceptable; CP9/CP8 x −56 with overshoot maybe −60 ok. Set fog & edges fine.

Hmm — CatmullRom 'centripetal' overshoot is minimal ✓.

**Check focus windows vs camera timing again with final CPs (distances recomputed):
CP0(−26,50) CP1(26,52) CP2(48,30) CP3(50,2) CP4 snap? CP5/6 snapped near peak. Let me finalize CP array literals:
```js
const CP=[
 [-26, 50, 3.2],
 [ 26, 52, 3.0],
 [ 48, 30, 4.0],
 [ 50,  2, 6.0],
 [ 30,-16, 5.0],   // replaced by valley snap
 [  4,-34,11.5],   // snapped to peak flank
 [-24,-46,15.5],   // snapped beside summit
 [-48,-30,12.0],
 [-56,  6, 6.0],
 [-42, 34, 4.0],
 [  2, 58, 3.0],
];
```
peak unknown position; assume around (5..15, −40..−50) centered. Snap CP5 to 16 from peak toward old CP5 dir ✓ CP6 24 toward old CP6 dir ✓.

Cumulative distances (approx, using snapped guesses pk=(8,−45)): CP5→(5.6,−29.6)? dir old CP5 (4,−34)−pk = (−4,11) len 11.7 → norm(−0.34,0.94) → CP5 = pk + (−5.5,15) = (2.5,−30) ✓. CP6: (−24,−46)−pk=(−32,−1) → CP6 = pk+(−31.7,−1) = (−23.7,−46) ✓ ~24.

Route lengths:
0→1: 52.2
1→2: √(484+484)=31.1 (83.3)
2→3: √(4+784)=28.1 (111.4)
3→4: √(400+196)=24.4 (135.8)
4→5: (30,−16)→(2.5,−30): √(756+196)=30.9 (166.7)
5→6: (2.5,−30)→(−23.7,−46): √(686+256)=30.7 (197.4)
6→7: (−23.7,−46)→(−48,−30): √(590+256)=29.1 (226.5)
7→8: √(64+1296)=36.9 (263.4)
8→9: √(196+784)=31.3 (294.7)
9→10: √(1936+576)=50.1 (344.8)
10→0: √(784+64)=29.1 (373.9)
u: CP2=0.223, CP3=0.298, CP4=0.363, CP5=0.446, CP6=0.528, CP7=0.606, CP8=0.704, CP9=0.788, CP10=0.922.

t = u*52: CP2 11.6s, CP3 15.5, CP4 18.9, CP5 23.2, CP6 27.5, CP7 31.5, CP8 36.6, CP9 41, CP10 47.9.

Focus windows update:
- coast: camera CP1–CP3 (t 8–16): window u 0.10–0.26 (5.2–13.5s) targeting beach — camera still on sea CP1–CP2 ✓ set {a:0.10,b:0.26,s:0.7}.
- forest: camera CP3–CP5 (15.5–23): window u 0.30–0.42 (15.6–21.8) s 0.6.
- summit: camera CP5–CP7 (23–31.5): window u 0.44–0.56 (22.9–29.1) s 0.95 ✓ summit reveal 23–29s ✓ within 30 ✓.
- west: camera CP7–CP9 (31.5–41): window u 0.62–0.74 (32–38.5) s 0.6.
- south sea: camera CP9–CP11 (41–52): window u 0.82–0.94 (42.6–48.9) s 0.55.

Opening (0–5.2s): base look curve → starts coastPOI drifting — good.

Alright — also LOOKPTS with updated route:
```js
const LOOKPTS=[
 coastPOI,
 new THREE.Vector3(46, gHill+5, 6),      // east hills (centered)
 valleyPOI,  // = (CP[4][0], flyGround+3, CP[4][1])
 peakP.clone(),
 new THREE.Vector3(-44, flyGround(-44,-24)+7, -24), // west ridge
 westPOI
];
```
✓.

Hmm `flyGround` expects centered coords ✓ (rounds +64).

**Also — make sure focus.w ramps: smoothstep(f.a, f.a+0.035, u)*(1−smoothstep(f.b−0.035,f.b,u)) ✓ windows ≥0.09 wide ✓.

**Alright, writing the final file now.** I'll write clean sectioned code with concise comments. Length ~600 lines. Let me carefully produce valid JS (no TS).

Also — I should double check `THREE.Float32BufferAttribute(posArray, 3)` accepts plain array ✓.

Water geometry: `wn` counter etc.

Let me define mesher constants EPS=1/128.

One more consideration — `renderer.setClearColor(FOGC)` not needed but harmless; skip (dome covers).

Also `scene.background` unnecessary.

Write `onResize`.

Caption: also hide if reduced motion? skip.

**Possible perf hiccup: `computeBoundingSphere` per chunk on big arrays — fine.

**Now writing. During writing, double check every referenced variable exists.**

Also for safety: wrap main in try/catch and show error text? Skip — keep clean.

Also — one subtle bug risk: in `sampleArr`, `arr.length` for camPts = NS (1024) ✓ lookPts NL=512 ✓.

`focus` uses `f.p` Vector3 ✓.

`camera.lookAt(x,y,z)` accepts numbers ✓.

Water `renderOrder=1`; clouds meshes renderOrder=2.

Cloud material opacity 0.5; also make clouds slightly warm-white 0xffffff base color? vertexColors already 1.0 — material color default white ✓.

**Terrain material:** also set `material.fog=true` default ✓.

Also to enrich: subtle color tint variation per block type? Grass top texture handles ✓.

Edge case: what if `peak.h < 28` (weak mountains)? bias ensures mountains — skip guard.

Also `hm` values used for beach pred — hm≥13&&≤14 ✓.

Also caption/letterbox markup.

**Let me also reconsider cl values for terrain-hugging segments: valley cl 5.0 — hills rise abruptly; enforcement via minY per sample ✓ smoothing may cut into cl slightly (≤ ~0.6) → min effective ~4.4 above ground — canopy clearance uses flyH incl trees ✓ ok.

**Camera near plane 0.1, blocks close when skimming — fine.

**FOV 62.

Final code — writing now, carefully.

```js
/* ============ setup ============ */
const renderer=new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
renderer.setSize(window.innerWidth,window.innerHeight);
document.body.appendChild(renderer.domElement);

const scene=new THREE.Scene();
scene.fog=new THREE.Fog(0xc9def2,70,235);
const camera=new THREE.PerspectiveCamera(62,window.innerWidth/window.innerHeight,0.1,1600);
```

Then world gen... (as planned)

Then atlas/materials, meshing, water, clouds, sky/sun, path, animate, resize.

Also — hmm, `const FOGC=0xc9def2` used in fog & dome hor vec (0.788,0.871,0.949): c9=201/255=0.788, de=222/255=0.871, f2=242/255=0.949 ✓ consistent.

Zen color: pick (0.20,0.42,0.76) #33 6B C2-ish — nice deep-ish blue without purple.

Sun tint (1.0,0.94,0.78).

Alright, also let me pre-verify the fragment shader compiles: uses varying vP; uniforms declared; ok.

Sprite `fog:false` — SpriteMaterial constructor accepts fog param ✓ (Material.fog exists; sprite shader supports fog — with fog:false uniform skip ✓).

One more: sprite in front of dome: dome radius 950 BackSide depthWrite false — depth buffer empty there → sprite at 800 passes ✓.

Terrain depth vs water: water transparent drawn after opaque ✓ tests depth ✓.

**Underwater terrain visibility:** opaque sand faces under water rendered ✓ (nb WATER → face emitted) ✓ seen through translucent water ✓.

Let me also double-check topT for underwater sand: H in [9..12] → SAND top ✓ (rule H>=9 SAND for H≤14) ✓ deep floor H≤8: H>=5 DIRT else STONE ✓.

Also possible: H≥15 grass but underwater?? H≥15 → top y=14 > WATER=12 → dry ✓ consistent.

Wait — H ≥ 15 grass; H = 13,14 sand (beach, above water 1–2) ✓; H=12 sand at waterline ✓; 9–11 underwater sand ✓; ✓.

Hmm wait rule above: `else if(H>=15) GRASS; else if(H>=9) SAND;` — H=13,14 → SAND ✓ (not grass) ✓ good; but snow/rock lines override for high H ✓.

But note: sand also for H 9–14 regardless of water adjacency ✓ accepted.

**steep threshold 3 with hm diffs over 2 columns: e.g., terrace 2 each side → 4 → steep ✓ gentle 1 → 2 no ✓.

**Final trace of animate locals** — ensure `sampleArr` writes into provided out ✓.

Also — `tgtTmp` reuse: 
```js
const lookDir=new THREE.Vector3();
...
sampleArr(lookPts,lu,lookTmp);
lookDir.copy(lookTmp);
for(focus...) lookDir.lerp(f.p,w);
lookDir.sub(camTmp).applyAxisAngle(UP,ang);
camera.lookAt(camTmp.x+lookDir.x, camTmp.y+lookDir.y, camTmp.z+lookDir.z);
```
✓ clean.

Bob applied to camTmp before copying to camera.position ✓ (camTmp holds pos+? I add bob to camTmp.y then camera.position.copy(camTmp) ✓; lookDir uses camTmp ✓ consistent).

Alright — also store LOOP=52, and focus list uses u windows as decided.

Also — one more possible issue: at u exactly 0 (first frame), lookPts sample at 0.055 ✓ fine.

**Write out cloud builder with SIDE patterns** (using explicit corner lists per side as derived):

```js
function addQuad(v, s, pos, col, ind, nObj){ pos.push(...v); for(let k=0;k<4;k++)col.push(s,s,s); ind.push(nObj.n,nObj.n+1,nObj.n+2,nObj.n,nObj.n+2,nObj.n+3); nObj.n+=4; }
```
Use closure counters instead — write inline in buildClouds with local n.

Sides for cloud cell (x0,z0,x1=x0+CS,z1=z0+CS,y0=CY,y1=CY+TH):
+x (at x1): [x1,y0,z0, x1,y1,z0, x1,y1,z1, x1,y0,z1] ✓ (from pattern [[1,0,0],[1,1,0],[1,1,1],[1,0,1]])
−x (at x0): [x0,y0,z1, x0,y1,z1, x0,y1,z0, x0,y0,z0] ✓
+z (at z1): [x0,y0,z1, x1,y0,z1, x1,y1,z1, x0,y1,z1] ✓
−z (at z0): [x1,y0,z0, x0,y0,z0, x0,y1,z0, x1,y1,z0] ✓
top: [x0,y1,z0, x0,y1,z1, x1,y1,z1, x1,y1,z0] ✓
bottom: [x0,y0,z0, x1,y0,z0, x1,y0,z1, x0,y0,z1] ✓

✓.

Water sides reuse FACES table (already correct).

Also — cloud side shading 0.9; also darken slightly bottom 0.78 ✓.

**Now, finally, potential issue — CatmullRomCurve3 with 3-component points where y=0 for all: curve in plane ✓ fine. kCurve uses (x, cl, z) ✓.

`getPointAt` on closed centripetal curve ✓.

I think the design is solid. Write the file.

One more requirement re-read: "blocks must have per-face shading so the cube shapes read clearly (draw the block textures procedurally on a canvas, pixel-art style)" ✓ both done. "a sky with a sun, soft distance fog and fluffy block clouds that drift slowly" ✓. "Use InstancedMesh or merged geometry" ✓ merged. "camera flies automatically over and between the hills on a smooth path, looking around the landscape" ✓. "Use the requestAnimationFrame timestamp for animation time" ✓. "Full-window canvas that handles resizing" ✓. "Starts automatically, no interaction needed" ✓.

Also everything within first 30s: sea ✓ beach ✓ hills ✓ trees ✓ snowy peaks ✓ (visible from CP3–CP5 approach & summit focus) ✓ water transparency ✓ clouds ✓ sun ✓.

Now write it. I'll keep comments concise. Estimated ~550 lines.

Also: careful that `hash2` with negative coords (centered) works: Math.imul handles negatives ✓ floor for vnoise negative ✓.

vnoise with negative x: Math.floor ✓.

In `elevation`, wx = x+HALF where x centered float (e.g., 63−64=−1) → wx=63 ✓ positive ✓ mostly.

gradient calls: elevation(x+1−HALF...) → wx up to 128+? x=127 → wx=128 → fine (hash domain unbounded).

Also note `flyGround` returns flyH which is ≥ WATER ✓.

Writing HTML skeleton with letterbox & caption.

Let me also double check the tree local-min suppress loop indexes bounds: nx,nz within [3,SX-3) — skip out-of-range neighbors (they can't host trees anyway... trees allowed x∈[3,SX-3)? my tree loop bounds `z=3; z<SZ-3` → x∈[3,124] ✓ neighbor check bounds same ✓).

Also the candidate hash < dens check inside suppress loop: `hash2(nx,nz,8804)<dens && hash2(nx,nz,8804)<h0` — two calls; fine.

Wait subtle: neighbor with hash < dens but > h0 doesn't suppress ✓; neighbor ≥ dens can't suppress ✓ matches "kept iff min among candidates" ✓.

dens varies with forest noise per column — candidates defined per-column dens — neighbor may have different dens — fine approximation ✓.

Tree H: `const H=hm[i]` require ≥16 ✓ and topT GRASS ✓ !steepA[i] ✓.

Tree loop also should skip if column has water above (H≥16 dry ✓).

Also — hmm, `forest` fbm at (x−HALF)*0.013: forest zones blobs ~77 units scale — nice groves ✓.

**One more possible visual improvement — snow blocks: make snow side slightly different from top? Keep all-snow tile ✓.

Also grass side tile drawn with grass depth 2–4: for side faces of grass blocks sitting on lower grass — the dirt part shows — classic ✓.

Also — block under grass top at cliff shows dirt side ✓ (since column fill: y=H−1 grass, H−5..H−2 dirt band? my band: y≥H−4 → dirt for grass columns: y=H−4..H−2 dirt, below stone ✓ so side exposure below grass top shows 3 dirt then stone ✓ nice.

Sand columns: sand band H−4..H−1 (4 sand) then stone ✓ beaches show sand cliffs ✓.

**Write final answer now.** Also brief explanation after the code block, per my usual practice.

Let me make sure about `new THREE.CatmullRomCurve3(points, true, 'centripetal', 0.5)` — signature (points, closed, curveType, tension) ✓ tension used only for 'catmullrom' type; harmless.

Also — `getPointAt(u, target)` optional target — pass temps to avoid allocs at init only (init loop fine with allocs).

Animate allocations: sampleArr writes into preallocated ✓; lookDir reused ✓; no per-frame allocs except maybe none ✓.

**Resize:** update renderer + camera ✓.

**Also — `document.hidden` big dt:** absolute-time based → no jumps ✓ (u jumps forward — camera teleports ahead after tab switch — acceptable; could clamp — skip).

Hmm — actually a nice touch: keep u continuous (absolute) ✓ fine.

Now — writing the code text. I'll be extra careful with commas/brackets. Also avoid `**` exponent? fine in modern browsers.

Counting potential mistakes in FACES uv for ±z: pattern [[0,0],[1,0],[1,1],[0,1]] with corners [[0,0,1],[1,0,1],[1,1,1],[0,1,1]] → u=x ✓ v=y ✓.

For −z: corners [[1,0,0],[0,0,0],[0,1,0],[1,1,0]], uv [[0,0],[1,0],[1,1],[0,1]]: corner0 x=1→u=0, corner1 x=0→u=1 — mirrored horizontally (texture flips) — fine for noise textures.

+x: corners [[1,0,0],[1,1,0],[1,1,1],[1,0,1]], uv [[0,0],[0,1],[1,1],[1,0]]: corner0 (y0,z0)→(0,0); corner1 (y1,z0)→(0,1) v=y ✓; corner2 (y1,z1)→(1,1) ✓; corner3 (y0,z1)→(1,0) ✓.

−x: corners [[0,0,1],[0,1,1],[0,1,0],[0,0,0]] uv [[0,0],[0,1],[1,1],[1,0]]: v=y ✓.

Top: corners [[0,1,0],[0,1,1],[1,1,1],[1,1,0]] uv [[0,0],[0,1],[1,1],[1,0]]: maps (x,z)→(u,v) with v=z ✓ fine.

Bottom: corners [[0,0,0],[1,0,0],[1,0,1],[0,0,1]] uv [[0,0],[1,0],[1,1],[0,1]]: u=x, v=z ✓.

Good.

`FACES` shades: indices 0..5 = +x,−x,+y,−y,+z,−z with sh [0.74, 0.58, 1.0, 0.5, 0.84, 0.66].

Now the full listing.

Also — remember: single html code block, then a brief explanation. Let me draft the code.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Voxel Isles — Cinematic Flythrough</title>
<style>
  html,body{margin:0;height:100%;overflow:hidden;background:#0a0d12}
  canvas{display:block}
  .bar{position:fixed;left:0;right:0;height:5.5vh;background:#000;z-index:5;pointer-events:none}
  .bar.top{top:0}.bar.bot{bottom:0}
  #cap{position:fixed;left:26px;bottom:calc(5.5vh + 16px);z-index:6;color:#fff;opacity:.8;
    font:500 11px/1.4 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
    letter-spacing:.24em;text-transform:uppercase;text-shadow:0 1px 3px rgba(0,0,0,.55);
    transition:opacity 1.8s ease;pointer-events:none}
</style>
</head>
<body>
<div class="bar top"></div><div class="bar bot"></div>
<div id="cap">voxel isles · autonomous cinematic flight</div>
<script type="module">
import * as THREE from 'three';

/* ---------------- deterministic hash / value noise ---------------- */
function hash2(x,y,s){...}
...
</script>
</body>
</html>
```

Now full JS. Writing carefully:

```js
function hash2(x, y, s){
  let h = (Math.imul(x|0, 374761393) ^ Math.imul(y|0, 668265263) ^ Math.imul(s|0, 1442695041)) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  h ^= h >>> 16;
  return (h >>> 0) / 4294967296;
}
```
(xor combine fine).

vnoise & fbm as planned.

World gen constants & arrays.

Column pass:
```js
const vox=new Uint8Array(SX*SY*SZ);
const hm=new Int16Array(SX*SZ);
const topT=new Uint8Array(SX*SZ);
const flyH=new Float32Array(SX*SZ);
for(let z=0;z<SZ;z++)for(let x=0;x<SX;x++){
  const e=elevation(x-HALF,z-HALF);
  const H=clamp(Math.floor(e),3,52);
  const i=x+SX*z;
  hm[i]=H;
  const dith=hash2(x,z,61)*6;
  let top;
  if(H>=30+dith) top=SNOW;
  else if(H>=26+dith) top=STONE;
  else if(H>=15) top=GRASS;
  else if(H>=9) top=SAND;
  else if(H>=5) top=DIRT;
  else top=STONE;
  topT[i]=top;
  for(let y=0;y<H;y++){
    let t;
    if(y===H-1) t=top;
    else if(y>=H-4) t=(top===SAND)?SAND:(top===GRASS||top===DIRT)?DIRT:STONE;
    else t=STONE;
    vox[idx(x,y,z)]=t;
  }
}
```
steep pass; trees pass; water cap pass.

Mesher as planned.

OK let me also decide: should terrain material be `side: FrontSide` default ✓.

Also `waterMat = new THREE.MeshBasicMaterial({map:waterTex,transparent:true,opacity:0.74,vertexColors:true,depthWrite:false})`.

Compose scene.

Path & focus & animate as planned.

Resize handler.

Caption fade timeout.

Let me now also double check `elevation` biased ocean: at CP10 (2,58): wz=122 → bias=1−1.906=−0.906 → e=0.62c−0.906 ≤ −0.3 always → water ✓ deep-ish. ✓

CP9 (−42,34): wz=96 → bias −0.5 → e ∈ [−0.99, −0.0]?? 0.62c ∈ [−0.5,0.5] → e ∈ [−1.0, 0.0] → mostly water/coast — camera cl 4 → over water y≈16 ✓ coast SW ✓ hmm CP9 intended SW coast; might be water — fine ("along the coast").

CP8 (−56,6): wz=62 → bias −0.031 → e ∈ [−0.35,0.47] → coast/hills mix ✓.

Alright. One more: opening CP0 (−26,50): wz=114, bias −0.78 → e∈[−1.09,−0.17] water ✓ y≈15 ✓.

Also verify summit focus reachable: peakP from actual gen — camera CP6 24 away ✓.

Also — lookPts NL=512 with smoothing; lookMin enforce ✓.

Now — actually writing out the entire final file text. I'll aim for clarity + correctness. Let me mentally "run" tricky parts once more:

buildChunk loops x0=cx*CH... CH=32, cx∈0..3 ✓ covers 0..127 ✓.

Water builder separate ✓.

trees array & plantTree ✓.

POI code after path samples (needs camPts) ✓ order: snap CPs → curves → camPts → POIs (forest) → LOOKPTS → lookPts → FOCUS → animate.

coastPOI & westPOI & seaPOI & peakP can be before curves ✓.

FOCUS references POIs ✓.

Also LOOKPTS valley POI: `new THREE.Vector3(CP[4][0], flyGround(CP[4][0],CP[4][1])+3, CP[4][1])` ✓ after valley snap ✓.

Also east hills POI ground: `flyGround(46,6)`.

Check `flyGround` signature (x,z) centered ✓.

animate: 

```js
const UP=new THREE.Vector3(0,1,0);
const camPos=new THREE.Vector3(), lookP=new THREE.Vector3(), lookDir=new THREE.Vector3();
function animate(ts){
  requestAnimationFrame(animate);
  const t=ts*0.001;
  const u=((t/LOOP)%1+1)%1;
  sampleArr(camPts,u,camPos);
  camPos.y+=Math.sin(t*0.55)*0.3+Math.sin(t*0.23+2.0)*0.2;
  camera.position.copy(camPos);
  sampleArr(lookPts,u+0.055,lookP);
  lookDir.copy(lookP);
  for(const f of FOCUS){
    const w=f.s*smoothstep(f.a,f.a+0.035,u)*(1-smoothstep(f.b-0.035,f.b,u));
    if(w>0)lookDir.lerp(f.p,w);
  }
  lookDir.sub(camPos);
  const ang=Math.sin(t*0.5)*0.05+Math.sin(t*0.21+1.3)*0.085;
  lookDir.applyAxisAngle(UP,ang);
  camera.lookAt(camPos.x+lookDir.x,camPos.y+lookDir.y,camPos.z+lookDir.z);
  sky.position.copy(camera.position);
  sun.position.copy(camera.position).addScaledVector(SUNDIR,800);
  clouds.position.x=-(((t*1.6)%CLOUDSPAN)+CLOUDSPAN)%CLOUDSPAN;
  waterTex.offset.set((t*0.012)%1,(t*0.007)%1);
  renderer.render(scene,camera);
}
requestAnimationFrame(animate);
```
sampleArr handles u>1 via mod ✓.

**Also**: `camera.lookAt` with default up ✓.

Alright — also we need `const CLOUDSPAN=CN*CS` exported from buildClouds — define CN=80, CS=8 globally.

Cloud meshes: 
```js
const clouds=new THREE.Group();
const cgeo=buildCloudGeometry();
for(const off of [-CLOUDSPAN,0,CLOUDSPAN]){
  const m=new THREE.Mesh(cgeo,cloudMat);
  m.position.x=off; m.renderOrder=2; m.frustumCulled=false;
  clouds.add(m);
}
scene.add(clouds);
```
✓ coverage proven.

buildCloudGeometry returns BufferGeometry with cells centered at origin ✓.

Also cloud Y at 76 (within geometry) ✓.

Wait — 3 copies each width 640 spanning union [−960,960] before shift ✓ as analyzed.

**Check cloud pattern wrap: drift modulo 640 ✓ group children offsets fixed ✓ seamless because pattern periodic 640 in x ✓.**

Double-check pattern periodicity: occ depends on hash2(i,j) with i∈[0,80) — the x-extent maps i→x0=(i−40)*8 → pattern over x∈[−320,320) periodic in x with period 640 ✓.

**Also water sides at borders: my pushWaterSide loops y from H to WATER−1 → for H≥WATER skip (no water) ✓ called only when H<WATER ✓.

Also border columns where terrain H≥WATER (dry) — no water sides ✓; terrain sides drawn by chunk mesher (nb out-of-bounds AIR) ✓.

Now writing final. Also include a guard: if `trees.length===0` fallback forestPOI.

Also caption timeout.

Also — the topT for underwater H 9..12 is SAND — beach pred uses hm 13..14 — but shore visually sand also underwater ✓ fine.

Let me also double check snow dithering line: `H>=30+dith` dith∈[0,6) → snow from 30–36 with dithered border ✓; rock `H>=26+dith` ✓.

Peaks ~45–52 → snow ✓; mid mountains 26–32 mixed rock/snow dithered ✓ nice transition.

Also grass H≥15 < rock 26 → grass up to ~26 ✓ hills grass-topped ✓.

**One risk: `elevation` produces sea only south — but focus westPOI nearest water to grid (12,78) → centered (−52,14): e at wz=78: bias −0.219: e ∈ [−0.53,0.09] → water likely west ✓ ok fallback anyway.

**Also verify camera doesn't pass through clouds (y 76) — max cam y ~ 60 ✓.

**Also double check terrain mat renders leaves & wood ✓ same atlas ✓.

Now, writing the complete file — final pass for syntax as I go.

Additionally — I realize I should double check `smoothstep(f.b-0.035, f.b, u)` — for u beyond b → 1 → weight 0 ✓.

Also focus overlapping windows: none overlap given gaps ✓.

Let me also think again about look lead 0.055 → 2.9s ahead along look curve — look curve length? POIs around island ~ 300 → 2.9s*?? look curve parametrized by its own length (≈340?) → 0.055*340≈19 units ahead — target ahead of its "synced" position. Since look & cam curves aren't synced anyway, lead just shifts phases; fine.

Also — possible weirdness: look target sometimes behind camera (curve phase mismatch) — e.g., camera at CP2 heading north while look curve point somewhere south — with focus windows pinning key views and base curve roughly paralleling route, mostly ahead-ish. Risk accepted; sway + focus keep it cinematic. To reduce phase mismatch, I could parametrize look by camera-u with per-POI mapping... overkill. The look POI sequence order matches route order; both closed with similar circumference; phases roughly aligned (coastPOI first, camera starts near coast segment). Camera starts at sea SW (CP0) at u=0; look curve starts at coastPOI (u=0 = coast). Camera reaches coast ~u=0.15; look reaches coast at 0 — target reaches coast *before* camera → target is ahead ✓ generally target leads. With lead +0.055 → leads more ✓. Then look continues to east hills while camera still at sea — target far ahead (east hills visible from sea ✓ fine). Sum: look target leads camera by ~1 POI — actually pleasant (looking toward where we're going). By summit: look hits summit at u≈0.42*? — look curve cumulative: coastPOI(0) → eastHills (~60 units?) → valley (~60) → summit (~70) → westRidge (~60) → westPOI (~70) → coast (~120) total ~440; summit at cum ~190 → u=0.43; camera summit window 0.44–0.56 — aligned ✓ nice.

westPOI at cum ~320/440=0.73; camera west window 0.62–0.74 ✓ close ✓.
seaPOI... wait seaPOI not in LOOKPTS (only focus) ✓ fine.

coast focus window 0.10–0.26: look base near eastHills/valley then; focus pulls to coast ✓.

OK good. Also forestPOI position in look curve? Not included — forest only via focus ✓ (base look may point elsewhere during forest window; focus 0.6 blend partial ✓).

Now — finalize LOOP=52.

Also double check `sampleArr(lookPts, u+0.055, lookP)` — u+0.055 may exceed 1 → mod inside ✓.

Everything seems coherent. Write it.

Actually, one more consideration on the water texture UV scale: top faces uv = world*0.25 → tile 4 units; texture 32px → 8px per block ✓ chunky ✓.

Water top face color s also multiplied by texture — deep dark ✓.

And — since waterMat depthWrite false, terrain under water renders (drawn earlier opaque) ✓ blending over ✓.

Also should water opacity vary with view angle? no.

FINAL: write the answer. Brief explanation after code: mention generation layers, AO, merged chunks, path system, etc. Keep explanation concise (~10 lines).

Also note: renderer.outputColorSpace default sRGB ✓ nothing to set.

Also `THREE.SRGBColorSpace` on atlas/water/sun ✓.

One more syntax check for template literal inside P(): `rgb(${r|0},${g|0},${b|0})` — careful variable name g conflicts with canvas ctx `g`! In makeAtlas I use `g` for context and also `g` param names in vary... rename ctx to `q` or use different: `const ctx=c.getContext('2d')`. Use ctx. In vary, params (c,a) with c array — fine. In each callbacks I use variable names r/g/b — avoid conflict with outer ctx (named ctx) ✓. Inside callbacks `let c=vary(...)` shadows... `each(ti,fn)` signature uses (x,y) => returns array; internally uses tx,ty — ok. In callback `c` local ✓. P uses (tx,ty,x,y,r,gg,b) ✓.

In makeWaterTex I named img data — fine.

Also `makeSunTex` uses ctx.

Watch out: in buildChunk I named variable `uvs` and also F.u — fine.

`ind.push(n,...)` where n vertex counter ✓.

Also careful: `const F=FACES[f]` and `F.u[ci]` etc ✓; `F.ao[ci]` array of 3 offsets ✓.

Also in AO: `OPAQ(V(...))` — V returns numbers; OPAQ boolean → `?1:0` ✓.

Alright — also for chunk geometry, if `n===0` skip creating mesh (won't happen) ✓.

Also world meshes: name collisions none.

Writing now — FINAL.

Also let me pre-decide numbers:
- AOL=[0.42,0.62,0.80,1.0]
- EPS=1/128

double-check tile rect v for row 0 (tiles 0..3): v1=1−EPS≈0.992, v0=0.75+EPS ✓.

Also — atlas drawn rows: tile idx → tx=idx&3, ty=idx>>2 with idx up to 8 → ty=2 ✓ canvas 64×64 holds rows 0..3 ✓.

Sun texture colorSpace SRGB ✓ additive.

Now — count of SY loop for mesher: y<SY ✓ (64).

vox idx helper defined before use ✓.

Let me write `idx` as arrow: `const idx=(x,y,z)=>x+SX*(z+SZ*y);` ✓ (y-major; fine).

V:
```js
const V=(x,y,z)=>{
  if(y<0) return STONE;
  if(x<0||x>=SX||z<0||z>=SZ||y>=SY) return AIR;
  return vox[x+SX*(z+SZ*y)];
};
```
✓.

Everything set. Compose final answer. Watch total length — big but fine.

Also — final "fluffy" clouds: maybe two stacked layers? Single slab layer fine.

One more idea for polish within budget: subtle vignette? CSS radial-gradient overlay — ornament? Skip — letterbox enough.

Write final HTML.

While writing the atlas `each` helper: 
```js
const each=(ti,fn)=>{const tx=ti&3,ty=ti>>2;for(let y=0;y<16;y++)for(let x=0;x<16;x++){const c=fn(x,y);ctx.fillStyle='rgb('+(c[0]|0)+','+(c[1]|0)+','+(c[2]|0)+')';ctx.fillRect(tx*16+x,ty*16+y,1,1);}};
```
✓.

Grass side gd array computed before ✓.

Note in tile 1 callback uses gd[x] and rnd and hash2 ✓ deterministic ✓.

Water: as planned.

Cloud builder: as planned with arrays cpos,ccol,cind and counter.

Let me also make sure `buildCloudGeometry` includes all cells incl. j edges: at(i,j) out-of-range → 0 → side faces at field border always drawn ✓ fine (they're far/fogged).

Path building code — write carefully:

```js
/* camera route (centered coords): x, z, clearance */
const CP=[...];
/* find highest summit */
let pkx=HALF,pkz=HALF,pkh=0;
for(let z=2;z<SZ-2;z+=1)for(let x=2;x<SX-2;x+=1){const h=hm[x+SX*z];if(h>pkh){pkh=h;pkx=x;pkz=z;}}
const peakP=new THREE.Vector3(pkx-HALF,pkh+2.5,pkz-HALF);
/* snap flank + overlook points to the summit */
{
  const d5=new THREE.Vector3(CP[5][0]-peakP.x,0,CP[5][1]-peakP.z);
  if(d5.lengthSq()<1)d5.set(0.7,0,0.7); d5.normalize();
  CP[5][0]=peakP.x+d5.x*16; CP[5][1]=peakP.z+d5.z*16;
  const d6=new THREE.Vector3(CP[6][0]-peakP.x,0,CP[6][1]-peakP.z);
  if(d6.lengthSq()<1)d6.set(-0.7,0,0.7); d6.normalize();
  CP[6][0]=peakP.x+d6.x*24; CP[6][1]=peakP.z+d6.z*24;
}
/* snap the pass to the lowest saddle on the approach */
{
  let bg=1e9,bx=CP[4][0],bz=CP[4][1];
  for(let s=0.15;s<=0.86;s+=0.05){
    const x=CP[3][0]+(CP[5][0]-CP[3][0])*s, z=CP[3][1]+(CP[5][1]-CP[3][1])*s;
    const g=flyGround(x,z);
    if(g<bg){bg=g;bx=x;bz=z;}
  }
  CP[4][0]=bx; CP[4][1]=bz;
}
```
✓ (flyGround defined before).

```js
const routeCurve=new THREE.CatmullRomCurve3(CP.map(p=>new THREE.Vector3(p[0],0,p[1])),true,'centripetal',0.5);
const clearCurve=new THREE.CatmullRomCurve3(CP.map(p=>new THREE.Vector3(p[0],p[2],p[1])),true,'centripetal',0.5);
const NS=1024, camPts=[], minY=new Float32Array(NS);
for(let i=0;i<NS;i++){
  const p=routeCurve.getPointAt(i/NS);
  minY[i]=flyGround(p.x,p.z)+clearCurve.getPointAt(i/NS).y;
  camPts.push(p);
}
const ys=Float32Array.from(minY);
for(let it=0;it<3;it++){
  const t2=Float32Array.from(ys);
  for(let i=0;i<NS;i++){
    const s=(t2[(i+NS-1)%NS]+2*t2[i]+t2[(i+1)%NS])*0.25;
    ys[i]=Math.max(s,minY[i]);
  }
}
for(let i=0;i<NS;i++)camPts[i].y=ys[i];
```
✓.

POIs, look curve, samples, FOCUS ✓.

Finally animate + resize + caption fade.

Also — `sampleArr` defined before animate ✓.

Let me also handle `lookPts` smoothing:
```js
const NL=512, lookPts=[], lmin=new Float32Array(NL), ly=new Float32Array(NL);
for(let i=0;i<NL;i++){
  const p=lCurve.getPointAt(i/NL);
  lookPts.push(p);
  ly[i]=p.y;
  lmin[i]=flyGround(p.x,p.z)+1.6;
}
for(let it=0;it<2;it++){
  const t2=Float32Array.from(ly);
  for(let i=0;i<NL;i++)ly[i]=(t2[(i+NL-1)%NL]+2*t2[i]+t2[(i+1)%NL])*0.25;
}
for(let i=0;i<NL;i++)lookPts[i].y=Math.max(ly[i],lmin[i]);
```
✓.

FOCUS windows final:
```js
const FOCUS=[
  {a:0.10, b:0.26, p:coastPOI,  s:0.70},
  {a:0.30, b:0.42, p:forestPOI, s:0.60},
  {a:0.44, b:0.56, p:peakP,     s:0.95},
  {a:0.62, b:0.74, p:westPOI,   s:0.60},
  {a:0.82, b:0.94, p:seaPOI,    s:0.55},
];
```
Hmm — summit focus {0.44–0.56}: camera at CP5 (u .446, t 23.2) through CP6 (0.528, 27.5) → release 0.56 (29.1s) ✓.

But wait: at u<0.10 opening (0–5.2s) no focus — base look at coastPOI then drifting east — good.

Double-check forest focus window (0.30–0.42 → 15.6–21.8s): camera CP3 (0.298, 15.5) → CP4 (0.363) → CP5 (0.446): over hills/pass ✓ forestPOI near route ✓.

Also — during coast focus (0.10–0.26), camera CP1 (0.139)→CP2 (0.223)→CP3 (0.298): sea→beach→east hills. Focus releases 0.26 as camera leaves beach ✓.

west focus (0.62–0.74): camera CP7 (0.606)→CP8 (0.704): descending west ridge → looking WSW sea ✓.

sea focus (0.82–0.94): camera CP9 (0.788)→CP10 (0.922): SW coast→south sea looking at deep water ✓ then release → base look → loops toward coastPOI (u 0.0 of look ≈ coast) — camera near CP10/CP0 sea — coast ahead ✓ seamless-ish loop ✓.

At loop wrap u→0: camera jumps from u=1 back to CP0 — closed curve so continuous ✓ focus coast ramps in at 0.10 — during 0–0.10 base look = lookPts near coastPOI→eastHills — continuous with pre-wrap (u .94–1: base look near westPOI→coastPOI wrap; lookPts closed so continuous ✓; focus sea released by 0.94+0.035 → continuous ✓). 

Everything checks. Write it out.

Wait — one more: focus `s` multiplies ramp — max weight s ✓.

Also — the peakP y = pkh+2.5 — target slightly above summit ✓.

Also — the camera at CP6 y = ground(CP6)+15.5: ground at 24 west of peak maybe ~40 → 55.5 — near summit 52+ ✓ slightly above — orbit-ish reveal ✓.

Alright — also worth double-checking camera y at CP5: ground flank ~ (peak−?) maybe 30 + 11.5 = 41.5 climbing to 55.5 — nice ascent.

Also CP4 valley ground maybe ~14–18 → y 19–23 ✓ weave.

Done — write final.

Also caption id 'cap' ✓ timeout fade.

Let me write the code in full now, mentally linting as I go. I'll number-check braces at the end.

Additionally — `makeAtlas` must run before materials; `waterTex` before waterMat ✓.

Order in script:
1. imports
2. helpers (hash/noise/clamp/smoothstep)
3. constants
4. elevation, flyGround (flyGround needs flyH — define function after arrays; hoisting: function declarations hoist ✓ if I use `function flyGround` it hoists; arrays defined before call time ✓)
5. gen passes
6. textures & materials
7. mesher + build meshes
8. clouds
9. sky/sun
10. route/POIs/samples/focus
11. animate/resize/caption

One more check on `elevation` — I use `WATER` constant inside ✓ defined above.

Also inside `plantTree` uses idx & vox ✓ defined.

Also — make sure `steepA` defined & filled in steep pass, then trees uses `steepA[i]` ✓.

Tree pass:
```js
const trees=[];
for(let z=3;z<SZ-3;z++)for(let x=3;x<SX-3;x++){
  const i=x+SX*z;
  if(topT[i]!==GRASS||steepA[i])continue;
  const H=hm[i];
  if(H<16)continue;
  const f=fbm((x-HALF)*0.013,(z-HALF)*0.013,424,3);
  const dens=f>0.15?0.09:(f>-0.05?0.012:0);
  if(!dens)continue;
  const h0=hash2(x,z,8804);
  if(h0>=dens)continue;
  let ok=true;
  for(let dz=-2;dz<=2&&ok;dz++)for(let dx=-2;dx<=2;dx++){
    if(!dx&&!dz)continue;
    const nx=x+dx,nz=z+dz;
    const hn=hash2(nx,nz,8804);
    if(hn<dens&&hn<h0){ok=false;break;}
  }
  if(!ok)continue;
  const th=4+Math.floor(hash2(x,z,8805)*3);
  trees.push({x,z,h:H,th});
  plantTree(x,z,H,th);
  for(let dz=-2;dz<=2;dz++)for(let dx=-2;dx<=2;dx++){
    const fi=(x+dx)+SX*(z+dz);
    if(flyH[fi]<H+th+2)flyH[fi]=H+th+2;
  }
}
```
inner loop break only inner — outer condition `ok` checked ✓.

steep pass:
```js
const steepA=new Uint8Array(SX*SZ);
for(let z=0;z<SZ;z++)for(let x=0;x<SX;x++){
  const i=x+SX*z;
  const gx=Math.abs(hm[Math.min(SX-1,x+1)+SX*z]-hm[Math.max(0,x-1)+SX*z]);
  const gz=Math.abs(hm[x+SX*Math.min(SZ-1,z+1)]-hm[x+SX*Math.max(0,z-1)]);
  if(gx+gz>3&&topT[i]===GRASS){
    steepA[i]=1;topT[i]=STONE;
    const H=hm[i];
    for(let y=Math.max(0,H-4);y<H;y++){
      const v=vox[idx(x,y,z)];
      if(v===GRASS||v===DIRT)vox[idx(x,y,z)]=STONE;
    }
  }
}
```
✓.

Water cap:
```js
for(let i=0;i<SX*SZ;i++)if(flyH[i]<WATER)flyH[i]=WATER;
```
✓.

Mesher — final. Then:

```js
const terrainMat=new THREE.MeshBasicMaterial({map:atlasTex,vertexColors:true});
const worldGroup=new THREE.Group();scene.add(worldGroup);
for(let cz=0;cz<4;cz++)for(let cx=0;cx<4;cx++){
  const g=buildChunk(cx*CH,cz*CH);
  if(g)worldGroup.add(new THREE.Mesh(g,terrainMat));
}
```
buildChunk takes x0,z0 ✓.

Water:
```js
const wgeo=buildWaterGeometry();
const waterMesh=new THREE.Mesh(wgeo,waterMat);waterMesh.renderOrder=1;scene.add(waterMesh);
```
buildWaterGeometry as planned with wn counter & helpers.

Write buildWaterGeometry concretely:
```js
function buildWaterGeometry(){
  const pos=[],col=[],uv=[],ind=[];let n=0;
  for(let z=0;z<SZ;z++)for(let x=0;x<SX;x++){
    const H=hm[x+SX*z];
    if(H>=WATER)continue;
    const s=clamp(1-(WATER-H)*0.03,0.66,1)*0.96;
    const X=x-HALF,Z=z-HALF,Y=WATER;
    pos.push(X,Y,Z, X,Y,Z+1, X+1,Y,Z+1, X+1,Y,Z);
    for(let k=0;k<4;k++)col.push(s,s,s);
    uv.push(X*0.25,Z*0.25, X*0.25,(Z+1)*0.25, (X+1)*0.25,(Z+1)*0.25, (X+1)*0.25,Z*0.25);
    ind.push(n,n+1,n+2,n,n+2,n+3);n+=4;
    const side=(f)=>{
      const F=FACES[f],d=F.d;
      for(let y=H;y<WATER;y++){
        for(let ci=0;ci<4;ci++){
          const c=F.c[ci];
          pos.push(x-HALF+c[0],y+c[1],z-HALF+c[2]);
          const uu=(d[0]!==0)?(z+c[2])*0.25:(x+c[0])*0.25;
          uv.push(uu,(y+c[1])*0.25);
          col.push(s,s,s);
        }
        ind.push(n,n+1,n+2,n,n+2,n+3);n+=4;
      }
    };
    if(x===0)side(1);
    if(x===SX-1)side(0);
    if(z===0)side(5);
    if(z===SZ-1)side(4);
  }
  const g=new THREE.BufferGeometry();
  g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));
  g.setAttribute('color',new THREE.Float32BufferAttribute(col,3));
  g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));
  g.setIndex(ind);g.computeBoundingSphere();
  return g;
}
```
✓.

Cloud geometry:
```js
function buildCloudGeometry(){
  const CNn=80,CSl=8,TH=1.6,CY=76;
  const raw=new Uint8Array(CNn*CNn),occ=new Uint8Array(CNn*CNn);
  for(let j=0;j<CNn;j++)for(let i=0;i<CNn;i++)raw[i+j*CNn]=hash2(i,j,3131)<0.38?1:0;
  for(let j=0;j<CNn;j++)for(let i=0;i<CNn;i++){
    let cnt=0;
    for(let dj=-1;dj<=1;dj++)for(let di=-1;di<=1;di++){
      const jj=j+dj;if(jj<0||jj>=CNn)continue;
      cnt+=raw[((i+di+CNn)%CNn)+jj*CNn];
    }
    occ[i+j*CNn]=cnt>=5?1:0;
  }
  const at=(i,j)=>(i<0||i>=CNn||j<0||j>=CNn)?0:occ[i+j*CNn];
  const pos=[],col=[],ind=[];let n=0;
  const quad=(v,s)=>{pos.push(...v);for(let k=0;k<4;k++)col.push(s,s,s);ind.push(n,n+1,n+2,n,n+2,n+3);n+=4;};
  for(let j=0;j<CNn;j++)for(let i=0;i<CNn;i++){
    if(!occ[i+j*CNn])continue;
    const x0=(i-40)*CSl,z0=(j-40)*CSl,x1=x0+CSl,z1=z0+CSl,y0=CY,y1=CY+TH;
    quad([x0,y1,z0,x0,y1,z1,x1,y1,z1,x1,y1,z0],1.0);
    quad([x0,y0,z0,x1,y0,z0,x1,y0,z1,x0,y0,z1],0.78);
    if(!at(i+1,j))quad([x1,y0,z0,x1,y1,z0,x1,y1,z1,x1,y0,z1],0.9);
    if(!at(i-1,j))quad([x0,y0,z1,x0,y1,z1,x0,y1,z0,x0,y0,z0],0.9);
    if(!at(i,j+1))quad([x0,y0,z1,x1,y0,z1,x1,y1,z1,x0,y1,z1],0.92);
    if(!at(i,j-1))quad([x1,y0,z0,x0,y0,z0,x0,y1,z0,x1,y1,z0],0.92);
  }
  const g=new THREE.BufferGeometry();
  g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));
  g.setAttribute('color',new THREE.Float32BufferAttribute(ccol,3));  // careful: col
  g.setIndex(ind);return g;
}
```
(fix name col.)

CLOUDSPAN = 80*8 = 640 — define const CLOUDSPAN=640.

Note the cloud mesh copy offsets ±640 and group shift — verified coverage.

Sky & sun as planned.

I also want `renderer.info`-independent ✓.

Let me also confirm smoothstep signature usage in shader-free JS contexts ✓.

Edge: `fbm` returns approx [-1,1] but can exceed slightly; fine.

Now — think about whether terrain might have H computed such that water exists at H=12 columns?? H=12 → no water (H<WATER false: 12<12 false) ✓ waterline ✓.

Also beach detection pred hm 13..14 → those exist along coasts ✓ (fallback ensures non-null mostly).

**Also caption text:** "voxel isles · autonomous cinematic flight" ✓.

Time to write the final deliverable. I'll write the explanation after in a few sentences.

Also double check: `camera.lookAt(x,y,z)` — Vector3 overload also fine.

For the sun texture: crisp square should have slight alpha edge? additive anyway.

Potential issue: SpriteMaterial `sizeAttenuation` default true ✓ scale in world units ✓ at distance 800 scale 120 → reasonable.

Also `sun.material.depthTest` default true ✓ occlusion by mountains ✓.

Final consideration — WebGL1 vs 2: r186 uses WebGL2 by default ✓ Uint32 indices fine.

Also verify `THREE.Fog` color hex vs dome hor — dome hor vec (0.788,0.871,0.949) — c9def2 = (201,222,242)/255 = (0.788,0.871,0.949) ✓.

Zenith (0.20,0.42,0.76).

Sun tint (1.0,0.94,0.78) ✓.

Also — one thing about the shader: `pow(clamp(h,0.0,1.0),0.55)` at h=0 → 0 → col=hor ✓ horizon match ✓.

Write it all.

Let me also do a final mental pass on buildChunk AO correctness for side faces: e.g., +x face, corner (1,0,0): tangents for ax=0: t1=1(y),t2=2(z); c[t1]=0→s1=−1; c[t2]=0→s2=−1. base b=(x+1,y,z). side1=(x+1,y−1,z), side2=(x+1,y,z−1), corner=(x+1,y−1,z−1) ✓ correct (blocks adjacent to the bottom-south edge of the exposed face) ✓.

Top face corner (0,1,0): ax=1, t1=0,t2=2: s1=−1,s2=−1: base (x,y+1,z): side1 (x−1,y+1,z), side2 (x,y+1,z−1), corner (x−1,y+1,z−1) ✓.

Great.

Also `F.ao` construction code:
```js
for(const F of FACES){
  const ax=F.d[0]!==0?0:(F.d[1]!==0?1:2);
  const t1=ax===0?1:0;
  const t2=ax===2?1:2;
  F.ao=F.c.map(c=>{
    const s1=c[t1]?1:-1,s2=c[t2]?1:-1;
    const o1=[...F.d];o1[t1]+=s1;
    const o2=[...F.d];o2[t2]+=s2;
    const o3=[...F.d];o3[t1]+=s1;o3[t2]+=s2;
    return [o1,o2,o3];
  });
}
```
Check t2 for ax=0: t2 = (ax===2)?1:2 → 2 ✓; ax=1 → t1=0, t2: (1===2)?1:2 → 2 ✓; ax=2 → t1=0, t2=(2===2)?1:2 → 1 ✓. 

In buildChunk AO read: `const O=F.ao[ci]; a1=OPAQ(V(x+O[0][0],y+O[0][1],z+O[0][2]))...` ✓.

All good. Compose the final response.

One more time re: importmap — "An import map is provided for you: do not add your own import map or any CDN URL." → I simply import from 'three' ✓ no script tag for importmap ✓.

Also ensure I don't use `three/addons` at all ✓.

Final: write out, then explanation.

Let me also quickly reconsider atlas min filter — LinearFilter on minification without mips: for strongly minified terrain, WebGL requires... using LinearFilter without mipmaps is legal (texture complete) ✓.

And NearestFilter mag ✓.

Also atlas.wrapS/T default ClampToEdge ✓.

Writing final code text now — attention to detail.

Also — one last detail: `sampleArr` uses arr.length — camPts length 1024 & lookPts 512 ✓.

And define `const LOOP=52;`.

Post-code explanation: concise bullet-ish paragraphs (no `#` heading start; begin with a sentence). The response must start with text, and the code block inside. Actually format: I'll give brief intro sentence, then the code block, then explanation. 

Also — caption: `setTimeout(()=>{const el=document.getElementById('cap');if(el)el.style.opacity='0';},7000);`

Done planning. Write answer.