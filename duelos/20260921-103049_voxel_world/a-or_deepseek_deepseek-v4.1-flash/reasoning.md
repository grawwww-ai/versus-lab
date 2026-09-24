Let me plan this out.

We need a single HTML file with three.js r186 via import map (already provided). We need to build a voxel world:

- Procedural terrain 128x128 columns (or more). Use layered noise (implement value noise / simplex-ish myself).
- Biomes: grass hills, snowy peaks, sandy beaches, lake/sea with semi-transparent water, trees.
- Per-face shading: use vertex colors or a custom shader. Since we use InstancedMesh, we can use per-instance color? That's uniform per instance. Better: build merged geometry with per-face vertex colors baked, using a texture atlas of block textures drawn procedurally on canvas.

Approach: Create a texture atlas canvas (e.g., 16x16 tiles arranged in a grid). Draw pixel-art textures: grass top, grass side, dirt, stone, snow top, snow side, sand, wood side, wood top, leaves, water.

Then generate terrain into a merged BufferGeometry: for each visible block face, add quad with UVs into atlas tile, plus per-face shading via vertex colors (top brightest, sides medium, bottom darkest) — actually also directional shading: +X face, -X face, +Z, -Z different brightness.

Use THREE.MeshLambertMaterial with vertexColors and map = atlas texture, NearestFilter. That gives per-face shading baked in. Could also add fog.

For water: separate mesh, transparent material, animate? Keep simple: separate geometry for water surface, semi-transparent, with slight vertical bob maybe via shader. Simpler: just a transparent material with opacity 0.75, depthWrite false.

Performance: 128x128 columns with height up to ~40 → many blocks. We only emit visible faces (faces adjacent to air). Number of faces: surface area. For 128x128 = 16384 columns, each with maybe top face + a few side faces. Should be maybe 60k-150k faces → 240k-600k vertices. That's fine as one merged geometry but memory heavy-ish. Let's keep world 128x128 with heightmap from layered noise, and only generate surface-ish blocks: For each column, we fill from y=0 to height with blocks but we only emit faces that are exposed. Interior faces culled. But we still need to know which blocks exist — store a Uint8Array of size 128*128*maxHeight? That's 16384*64 = 1M bytes, fine.

Actually let's do a chunked approach for performance? Merged geometry is fine. Let's just do a single merged geometry with a BufferGeometry built from arrays.

Let's estimate faces: for each column top face = 1 (if above water or whatever). Sides: differences in height between neighbors → average maybe 1-2 side faces per column per direction... Actually side faces are only emitted where neighbor column height < current height, so total side faces ≈ sum over columns of exposed vertical faces. With smooth terrain, the average is maybe 2-3 per column. Plus trees. So maybe 16384 * (1 + 3) ≈ 65k faces → 260k verts, each vertex: position (3 floats), normal? (can use flat shading via computed normals or skip normals and use vertex color shading + material that doesn't need normals — MeshBasicMaterial with vertex colors! That would bake lighting entirely. But then fog still works with MeshBasicMaterial? Yes, fog works with basic material.

Hmm but with baked vertex color shading, we get a nice flat cartoon look. But requirement "per-face shading so the cube shapes read clearly" — baked vertex colors on faces works well. Use MeshBasicMaterial? That would look flat-ish but with baked shading it's fine and fast. However, we might want some directional light variation. Baking handles it.

Actually let's use MeshLambertMaterial with vertexColors plus a hemisphere + directional light? That gives double shading. Simpler: MeshBasicMaterial with vertex colors baked (top=1.0, sides=0.78/0.62, bottom=0.45) and fog. Add slight per-face color variation? Good.

Hmm, but leaves with transparency? Let's make leaves opaque pixel-art (Minecraft "fast" graphics). Fine.

Atlas: 4x4 tiles of 16x16 px each = 64x64 texture. Tiles needed:
0: grass_top (green with noise)
1: grass_side (dirt with green top strip)
2: dirt
3: stone
4: snow_top
5: snow_side (snow over stone/dirt)
6: sand
7: wood_side
8: wood_top
9: leaves
10: water
11: gravel/rock? maybe for mountain
12: dark grass? 
Let's do 4x4 = 16 slots, plenty.

UV padding: with NearestFilter and no mipmaps... use minFilter = NearestFilter, magFilter = NearestFilter, generateMipmaps = false. Then no bleeding issues mostly, but at distance with no mipmaps you get aliasing/shimmer. Better to use LinearMipmapLinearFilter with padding. Hmm. Let's use NearestFilter for both and generateMipmaps=false, and to avoid shimmer, we can... it's fine, actually voxel worlds often look ok. Alternatively add a small inset to UVs (e.g., 0.5/atlasSize inset). I'll inset UVs by 0.5 pixel to avoid bleeding and use NearestFilter with mipmaps disabled. Shimmering at distance may occur but with fog it's fine.

Actually let's enable mipmaps with NearestMipmapLinearFilter? With padding issues... I'll just do NearestFilter, no mipmaps. Add fog to hide distant shimmer.

Terrain generation: layered value noise with smooth interpolation, multiple octaves. Plus a "continent" mask for a lake/sea.

Plan:
- Use seeded PRNG (mulberry32) and a value-noise function with hashed gradient... Let's implement 2D value noise with smoothstep interpolation over integer lattice using a hash function.

```js
function hash2(x, y) {
  let h = x * 374761393 + y * 668265263;
  h = (h ^ (h >> 13)) * 1274126177;
  return ((h ^ (h >> 16)) >>> 0) / 4294967295;
}
```
Careful with JS number overflow — use Math.imul.

```js
function hash2(x,y){
  let h = Math.imul(x, 374761393) + Math.imul(y, 668265263);
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  h ^= h >>> 16;
  return (h >>> 0) / 4294967296;
}
```

Value noise with fade:
```js
function noise2(x, y) {
  const xi = Math.floor(x), yi = Math.floor(y);
  const xf = x - xi, yf = y - yi;
  const u = xf*xf*(3-2*xf), v = yf*yf*(3-2*yf);
  const a = hash2(xi, yi), b = hash2(xi+1, yi), c = hash2(xi, yi+1), d = hash2(xi+1, yi+1);
  return (a*(1-u)+b*u)*(1-v) + (c*(1-u)+d*u)*v;
}
```

FBM: sum octaves.

Terrain height function:
```
function terrainHeight(x, z) {
  const base = fbm(x*0.012, z*0.012, 4); // 0..1
  const mountains = fbm(x*0.006 + 100, z*0.006 + 100, 3);
  ...
}
```

Design a landscape that has: sea level ~ 12; beaches around sea level; grass hills up to ~30; snowy peaks above ~38.

Let me define:
- continent = fbm(x*0.008, z*0.008, 4) → 0..1
- ridge = ridged noise for mountains: 1 - |2*n-1|, powered.

Height = 6 + continent*18 + mountainMask * ridge * 30.

Hmm. Let's craft:

```
const nx = x / 128, nz = z / 128;
let e = fbm(x*0.013, z*0.013, 5);           // rolling hills 0..1
let m = fbm(x*0.0045 + 37.3, z*0.0045 - 12.7, 3); // large scale for mountain regions
let mountainMask = smoothstep(0.55, 0.85, m);
let ridge = 1 - Math.abs(2*fbm(x*0.02+5, z*0.02+9, 3) - 1);
let h = 8 + e*14 + mountainMask * ridge * 34;
```
Then sea level = 12. So areas where h < 12 become water. Beaches: h between 12 and 14 → sand. Grass 14-32, snow above 32 with rock/stone in between? Actually snowy peaks: above 30 use snow top, and if very steep use stone.

Also need to make sure there's a lake/sea somewhere visible. With fbm, low areas exist. Let's ensure some water by lowering the base: make `h = 6 + e*14 + ...`, sea level 12 → about half the map might be underwater. Hmm, we want mostly land with a lake/sea. Let's tune: e in [0,1] mostly around 0.5 → h ≈ 6+7 = 13 just above sea level. Good, with dips below.

Actually fbm of value noise tends to concentrate around 0.5 (sum of uniform). With 5 octaves amplitude normalized, range roughly 0.25-0.75. So h ≈ 6 + (0.25..0.75)*14 = 9.5..16.5. That's too narrow. Let's stretch: use (e-0.5)*2 clamped-ish, or use more amplitude.

Let me instead compute normalized fbm with range expansion: `e = fbm(...)` then `e = clamp((e-0.5)*2.2+0.5, 0, 1)`.

Let's simplify and just tune numbers by reasoning, then hope it looks fine.

Alternative approach that's more controllable: 
```
let h = SEA + (fbm1 - 0.5) * 30;   // rolling
h += mountainMask * ridge * 26;
```
where fbm1 has range ~0.3..0.7 → (fbm1-0.5)*30 → -6..+6. So h ranges 6..18 around sea level 12. Good.

Mountain mask from low-freq noise: mm = smoothstep(0.52, 0.72, fbm2). fbm2 range 0.3-0.7 so about 20% of map gets mountains. Then add ridge*30 * mm → peaks up to ~48. Snow above ~34.

OK. Also carve a lake: subtract a gaussian blob somewhere to guarantee water. Let's add: 
```
const lakeX = 40, lakeZ = 88, lakeR = 34;
const d = Math.hypot(x-lakeX, z-lakeZ);
h -= 14 * Math.exp(-(d*d)/(2*lakeR*lakeR)) ... 
```
Hmm, but that might conflict. Actually the noise already gives water in low areas. But guaranteed water is nice for the "lake or sea" requirement. Let's add a smooth basin subtraction.

Let's just do: h = base; then h -= 16 * exp(-(d/38)^2) for a lake centered at some point. With base h ~12, the lake bottom goes to -4. Then water fills to y=12. Fine — water surface at y=12, blocks below that are sand/dirt underwater.

Actually simpler: water plane at y = SEA_LEVEL (say 12), and we render water as a flat quad grid at y=12.001 covering all columns where terrain height < 12. That's easy: emit a water quad for every column where h < SEA. But that's 16384 quads at most for underwater columns; typically fewer. Actually we only need water quads at the top surface — emit one quad per column where h < SEA. That's fine (each underwater column gets one top water face). Merge into water geometry with slight transparency.

Better: also emit water only if the column is underwater. Good.

Now, rendering blocks:

Store blocks in a Map or typed array? Let's use a 3D array Uint8Array of size W*W*H where H = 64. Index = (y*W + z)*W + x. 128*128*64 = 1,048,576 bytes = 1MB. Fine.

Fill: for each column, for y from 0 to h-1: block type based on depth and biome.
- y == h-1 (top): 
  - if h <= SEA+1 → sand
  - else if h > SNOW_LINE → snow
  - else if h > STONE_LINE → stone
  - else grass
- below top: 
  - if within 3 of top and top is grass → dirt
  - else stone
- Underwater columns: top few layers sand.

Then trees: place on grass columns above sea level, with spacing via noise/random. Tree = trunk 4-6 wood blocks + leaves blob.

Now face culling: for each solid block, check 6 neighbors; if neighbor is air (or water for solid blocks? water should hide the faces of solid blocks under water? For transparency, faces under water are visible through water. Better: treat water as transparent, so solid blocks adjacent to water still emit faces. That's fine, and looks nice through water. But it adds faces. Fine.

Water blocks: emit faces only for water blocks adjacent to air (above) — actually just emit top face per water column plus side faces at the shoreline where adjacent column has no water. Simplest: emit top face for each water column, and side faces where neighbor column is not water (i.e., terrain height >= SEA at neighbor). Since water is a flat plane, side faces only at the boundary between water and land... but land is above water level there, so the water side face is hidden by land. Actually at shoreline, neighbor column height >= SEA means there's solid blocks at y=SEA-1.. up. So the water side face at y=SEA would be adjacent to a solid block → culled. Good. So effectively only the top faces matter. So: just emit top water quads.

Hmm but if a neighbor column has height exactly SEA-1 (top block at y=SEA-1, which is below water level), then water at that column is present too. Right, water exists for columns with h < SEA. So water column exists wherever terrain top < SEA. So water quads only at the top. And where a water column is adjacent to a land column (h >= SEA), the water's side face is against solid → hidden. Good, only top faces needed. 

But also we want to see the water surface undulating? Keep flat but with slight transparency and maybe a subtle animated UV offset... Let's just use a semi-transparent material with the water texture, plus maybe vertex colors slightly varying. Keep it simple: transparent, opacity 0.72, depthWrite false, and a slight color. And render order after opaque.

Wait, depthWrite false with a big flat plane — fine.

Now, generating geometry with vertex colors:

For each face, 4 vertices, 6 indices. Push positions, uvs, colors.

Face definitions:
- +X (right): normal (1,0,0), brightness 0.80
- -X: 0.68
- +Y (top): 1.0
- -Y (bottom): 0.5
- +Z: 0.88
- -Z: 0.74

Also add ambient occlusion? Nice-to-have; skip for perf/complexity. Actually simple AO would improve looks a lot but adds complexity. Let's add a simple per-vertex AO computed from neighboring blocks — it's a known algorithm. Hmm, might be worth it for "cinematic" quality. But risk of bugs. Let's skip AO, but add slight per-block color variation (hash-based) to break up flatness. That's cheap and looks good.

Let's include per-face brightness * per-block tint (0.92..1.08).

Textures: draw 16x16 pixel art per tile on canvas.

Tile definitions (index: name):
0: grass_top — base #6aa84f with noise dots of lighter/darker green
1: grass_side — dirt #8b5a2b with top 4 rows green
2: dirt — #8b5a2b with noise
3: stone — #8c8c8c with noise
4: snow — #f2f7ff with light speckles
5: snow_side — stone/dirt with top rows white
6: sand — #e6d9a2 with speckles
7: wood_side — #6b4a2b with vertical bark lines
8: wood_top — #a9824f with rings
9: leaves — #3f7a2e with dark/light speckles
10: water — #2f6fb5 with wave lines
11: gravel/rock? Let's use "dark stone" for cliffs — reuse stone.
Let's define 12 tiles in a 4x4 atlas (16 slots).

Atlas layout: 4 columns x 4 rows, tile size 16 → 64x64 canvas.

UV mapping: for tile index t: col = t % 4, row = floor(t/4). u0 = col/4, v0 = 1 - (row+1)/4 ... Careful with texture flip. In three.js, texture UV origin is bottom-left by default with flipY = true for canvas textures (default flipY=true means the image is flipped so that UV (0,0) is bottom-left of the image as displayed). Ugh, let's just set texture.flipY = false and compute v as row/4 from top. Actually simpler: keep flipY default true, and treat the canvas as an image where row 0 is at the top. With flipY=true, UV (0,0) maps to bottom-left of the image (i.e., canvas y = height). So for tile at canvas row r (from top), the tile spans canvas y from r*16 to (r+1)*16. In UV space with flipY, v = 1 - canvasY/64. So v_top_of_tile = 1 - r*16/64 = 1 - r/4, v_bottom = 1 - (r+1)/4.

For a quad, I'll assign UVs so the texture appears upright. Let's define per-face vertex UV assignment carefully. Since our textures are mostly noise, orientation only matters for grass_side (green strip on top) and wood_side. Let's handle it.

Simplify: for each face, define 4 corners in order (v0,v1,v2,v3) going around the face, and assign uv = (u0,v1)... Let's just be explicit per face type.

Let me define a helper: addFace(px, py, pz, faceIndex, tileIndex, tint).

For a cube at (x,y,z) with size 1, corners:
- Top face (+Y): vertices at y+1, order: (x,y+1,z), (x,y+1,z+1), (x+1,y+1,z+1), (x+1,y+1,z) — CCW when viewed from above? Let's check: viewed from +Y looking down (-Y direction), we see the XZ plane. For front-facing (CCW in screen space when viewed from outside), with right-handed coords, normal +Y. Points: A(x,1,z), B(x,1,z+1), C(x+1,1,z+1), D(x+1,1,z). Cross product of (B-A)=(0,0,1) and (C-B)=(1,0,0) → (0,0,1)×(1,0,0) = (0*0-1*0, 1*1-0*0, 0*0-0*1) = (0,1,0). Yes normal +Y. Good. Triangles: A,B,C and A,C,D.

UV for top: u from x, v from z. Let's say A=(u0,v1), B=(u0,v0)... Let's map so that the texture isn't mirrored; for top faces it doesn't matter much. Use A=(u0,v0'), B=(u0,v1'), C=(u1,v1'), D=(u1,v0') where u0=col/4, u1=(col+1)/4, and v0'=1-(row+1)/4 (bottom), v1'=1-row/4 (top). Hmm, let me define:
- U0 = col/4, U1 = (col+1)/4
- V1 = 1 - row/4 (top edge in UV, higher v)
- V0 = 1 - (row+1)/4 (bottom edge in UV, lower v)

For top face: A=(x,1,z)→(U0,V1), B=(x,1,z+1)→(U0,V0), C=(x+1,1,z+1)→(U1,V0), D=(x+1,1,z)→(U1,V1). This maps the texture's "up" (V1) toward -Z. Fine.

For side faces, we need V1 (texture top) at the top of the face (higher y).

+X face (normal +X), at x+1 plane. Viewed from +X. Corners CCW: A(x+1,y,z+1), B(x+1,y,z), C(x+1,y+1,z), D(x+1,y+1,z+1)? Let's verify normal: (B-A)=(0,0,-1), (C-B)=(0,1,0). Cross (0,0,-1)×(0,1,0) = (0*0 - (-1)*1, (-1)*0 - 0*0, 0*1 - 0*0) = (1, 0, 0). Yes +X. 

Hmm, let me use standard: for +X, vertices in order (y from bottom to top, z from ...):
Let's define with u along -z or +z. For +X face viewed from outside (from +X looking in -X direction), the local right direction is -Z... let's just do:
A = (x+1, y,   z+1)  → uv (U0, V0)
B = (x+1, y,   z  )  → uv (U1, V0)
C = (x+1, y+1, z  )  → uv (U1, V1)
D = (x+1, y+1, z+1)  → uv (U0, V1)
Triangles A,B,C and A,C,D. Normal check above gives +X. Good.

-X face (normal -X): 
A = (x, y, z) → (U0,V0)
B = (x, y, z+1) → (U1,V0)
C = (x, y+1, z+1) → (U1,V1)
D = (x, y+1, z) → (U0,V1)
Check: (B-A)=(0,0,1), (C-B)=(0,1,0). Cross = (0,0,1)×(0,1,0) = (0*0-1*1, 1*0-0*0, 0*1-0*0) = (-1,0,0). Good, -X.

+Z face (normal +Z):
A = (x, y, z+1) → (U0,V0)
B = (x+1, y, z+1) → (U1,V0)
C = (x+1, y+1, z+1) → (U1,V1)
D = (x, y+1, z+1) → (U0,V1)
Check: (B-A)=(1,0,0), (C-B)=(0,1,0). Cross = (0*0-0*1, 0*0-1*0, 1*1-0*0) = (0,0,1). Good.

-Z face (normal -Z):
A = (x+1, y, z) → (U0,V0)
B = (x, y, z) → (U1,V0)
C = (x, y+1, z) → (U1,V1)
D = (x+1, y+1, z) → (U0,V1)
Check: (B-A)=(-1,0,0), (C-B)=(0,1,0). Cross = (-1,0,0)×(0,1,0) = (0*0-0*1, 0*0-(-1)*0, -1*1-0*0) = (0,0,-1). Good.

Top face (+Y):
A = (x, y+1, z) → (U0,V1)
B = (x, y+1, z+1) → (U0,V0)
C = (x+1, y+1, z+1) → (U1,V0)
D = (x+1, y+1, z) → (U1,V1)
Wait I need to double check winding gives +Y normal. Earlier I computed with A(x,1,z), B(x,1,z+1), C(x+1,1,z+1), D(x+1,1,z) → normal +Y. Yes matches. Good.

Bottom face (-Y):
A = (x, y, z+1) → (U0,V0)
B = (x, y, z) → (U1,V0)
C = (x+1, y, z) → (U1,V1)
D = (x+1, y, z+1) → (U0,V1)
Check: (B-A) = (0,0,-1), (C-B) = (1,0,0). Cross = (0,0,-1)×(1,0,0) = (0*0-(-1)*0, (-1)*1-0*0, 0*0-0*1) = (0,-1,0). Good.

Now, since we bake shading in vertex colors and use MeshBasicMaterial (or MeshLambert with lights?). Let's use MeshBasicMaterial with vertexColors: true and map. Fog works. Actually wait — does MeshBasicMaterial support fog? Yes, `fog: true` is default for basic material.

Hmm, but no lighting means the "sun" is purely decorative. That's fine — the shading is baked. But we also want the sun in the sky (a bright disc/sprite). We can add a sun with a sprite or a mesh with basic material. And clouds made of white boxes.

Let's also consider adding a slight directional light... no, skip lights entirely. Baked shading is deterministic and fast. Actually, let me reconsider: MeshLambertMaterial with vertexColors multiplies vertex color by lighting; if I add a hemisphere light + directional light, the result is a mix. It could look nicer with the sun direction matching. But baked is safer. Go with baked + basic material.

Hmm, one issue: MeshBasicMaterial doesn't respond to lights, so the scene might look flat, but with the per-face brightness baked it should read as 3D. Good.

Sky: use a large sphere with a gradient shader material (BackSide), or set scene.background to a gradient texture. Simplest: create a canvas gradient texture and use scene.background = texture? That maps as an equirect? No — scene.background with a Texture is treated as... In newer three.js, setting scene.background to a regular Texture renders it as a full-screen background (mapping = UVMapping → it's drawn as a background image stretched). Actually three.js supports `scene.background = texture` for a 2D background (it renders as a fullscreen quad) since r118ish? Let me recall: `scene.background` can be a Color, Texture (equirect or cube), or... For a plain Texture with mapping UVMapping, three.js renders it as a full-screen background quad (it uses the background box shader with `backgroundBlurriness`... hmm). Actually I recall three.js supports "scene.background = texture" for equirectangular and cube textures; for a plain texture it... Let me check: In WebGLBackground, if background is a Texture and `background.isCubeTexture || background.mapping === CubeUVReflectionMapping` → box mesh. Else if `background.isTexture` → plane mesh (fullscreen quad) with `backgroundMaterial`. Yes! There's a planeMesh path for regular textures. It works.

But safer: create a big sky dome mesh with ShaderMaterial (BackSide) with a vertical gradient. That's fully controlled and looks nice. Let's do that: a sphere of radius 900 with a custom gradient shader, depthWrite false, fog false.

Then add the sun: a sphere/disc mesh placed far away in the sky direction, with a basic material (bright yellow-white) + maybe a glow sprite. Or bake the sun into the sky shader (a radial gradient). Let's do it in the sky shader: compute sun disc via dot product with sun direction, add a glow. That's elegant and cheap.

Sky shader:
```glsl
varying vec3 vWorldPos;
uniform vec3 uSunDir;
uniform vec3 uTopColor, uHorizonColor, uBottomColor;
void main(){
  vec3 dir = normalize(vWorldPos);
  float h = dir.y;
  vec3 col = mix(uHorizonColor, uTopColor, clamp(pow(max(h,0.0), 0.6), 0.0, 1.0));
  col = mix(col, uBottomColor, clamp(-h*2.0, 0.0, 1.0));
  float sd = max(dot(dir, uSunDir), 0.0);
  col += vec3(1.0, 0.95, 0.8) * pow(sd, 800.0) * 1.5;   // disc
  col += vec3(1.0, 0.85, 0.6) * pow(sd, 12.0) * 0.25;   // glow
  gl_FragColor = vec4(col, 1.0);
}
```
And make sure the sky mesh doesn't get fogged: `fog: false` in ShaderMaterial... ShaderMaterial doesn't apply fog unless you add it. Good.

Need to set `depthWrite: false`, `side: THREE.BackSide`, and put it in the scene with `renderOrder = -1` maybe. Or use `scene.background`. Actually a big sphere works fine if we keep it inside the camera far plane (far = 2000, radius 900). But the camera moves; if the sky sphere is centered at origin and the camera moves ~100 units, the sky shifts. Better: attach sky sphere to the camera, or just make it huge (radius 5000, far = 10000). Let's do radius 4000 and far 9000, and update sky position to follow camera each frame. Simple: `sky.position.copy(camera.position)`.

Fog: THREE.Fog(color, near, far) — with sky visible above fog... Fog affects the terrain. Use FogExp2 maybe with density 0.0025? For a world 128 wide, and the camera flying at height ~25-45, we want distant terrain to fade. Let's use Fog with near 40, far 260, color matching horizon (light blue). Hmm, with fog far 260 the whole 128 world is mostly visible. Let's use near 30 far 220 for a soft haze.

Actually with fog, the sky dome is not fogged (ShaderMaterial without fog), so the horizon color should match the fog color for a seamless look. Set fog color = horizon color.

Clouds: "fluffy block clouds that drift slowly". Create a set of clouds, each made of merged boxes (a cluster of boxes). Use InstancedMesh of a unit box with per-instance matrices and a white material with slight vertex-color shading? For block clouds, per-face shading matters less; but let's give them a MeshBasicMaterial with a color like 0xffffff and use a slight per-instance color? InstancedMesh supports instanceColor. Or just build a merged geometry of white boxes with baked face shading.

Simpler: build cloud clusters as merged BoxGeometry with vertex colors baked per face (top white, sides slightly gray, bottom grayer), all merged into one geometry, then place several copies via InstancedMesh? Or just one merged geometry for all clouds, and animate by translating the whole thing? Clouds drift at different speeds... We can just move the whole cloud group slowly in +X and wrap around. That's simplest: one merged cloud geometry, group.position.x += speed*dt, wrap at some boundary. But then all clouds move together which looks fine for drifting.

Actually to make it look better, create 3 layers of cloud groups moving at different speeds. Or just use InstancedMesh with per-instance matrices updated per frame — that's 30-60 instances, cheap. Let's do: cloud clusters as InstancedMesh of a "cloud block" (a box with baked face shading via vertex colors). Each instance is a box of random size. Hmm, individual boxes as instances is easiest: generate ~600 boxes forming ~60 cloud clusters. Update instance matrices each frame with drifting offset. 600 matrix updates per frame is fine.

Actually simplest and most performant: build merged geometry per cloud cluster... nah. Let's do InstancedMesh with 800 boxes. Per frame, update the instanceMatrix with translation drift. But we'd need to recompute matrices each frame — 800 compose operations, negligible.

Hmm, but if we just drift the whole group, we don't need per-frame matrix updates at all. Let's do: cloudGroup with merged geometry (all cloud boxes), drift x. When x > 200, wrap to -200. Since the geometry spans the whole world width, wrapping is seamless if clouds are distributed periodically... Not exactly, but with the fog and distance, a sudden jump is visible. Alternative: make the cloud group's geometry cover x from -300 to 300 and wrap at 300 → jump of 600 units, which happens off-screen? The camera looks around; hmm.

Let's just do the InstancedMesh approach with per-frame matrix updates, wrapping each cloud individually when it goes past a boundary. That's clean and each cloud wraps far away. 60 clouds * (say 20 boxes each) = 1200 instances. Updating 1200 matrices per frame: each is a Matrix4.compose or just set position via makeTranslation... Actually we can just use `dummy.position.set(...)` and `dummy.updateMatrix()` then `setMatrixAt`. 1200 * that per frame ≈ fine (maybe 0.3ms).

Hmm, actually simpler: I'll create each cloud as a Group of merged boxes? No, too many draw calls.

Let's do: InstancedMesh(cloudBoxGeo, cloudMat, count) where each instance is a single box. Cloud clusters generated by picking a center and adding 4-9 boxes around it. Store for each instance: base position offset relative to cloud center, cloud center, and drift speed. Per frame: cloudCenter.x += speed*dt; if > limit, wrap. Then instance matrix = translate(cloudCenter + offset) * scale(boxSize).

To avoid recomputing scale each time, I can precompute the full local matrix (scale + offset translation) per instance and then multiply by the cloud translation matrix. But simpler to just build the matrix each frame from scratch: dummy.position.set(...), dummy.scale.set(...), dummy.updateMatrix(). Fine.

Let's just store per instance: {cloudIndex, ox, oy, oz, sx, sy, sz}. And clouds: {x, y, z, speed}.

Actually even simpler: skip the per-instance scale by baking sizes into a few box geometries... nah, scale is fine.

Cloud material: white-ish with slight per-face shading baked into the box geometry vertex colors. Since InstancedMesh supports vertexColors from geometry, that works. Use MeshBasicMaterial({color: 0xffffff, vertexColors: true, fog: true, transparent: true, opacity: 0.9}).

Hmm, transparency for clouds: they should be fluffy/soft. Let's use opacity ~0.85 and depthWrite false? With depthWrite false, overlapping cloud boxes blend weirdly (you see through them). Let's use depthWrite true, transparent false — solid white blocks look like Minecraft clouds. Minecraft clouds are solid-ish. But "fluffy" suggests soft. Let's do transparent: true, opacity: 0.88, depthWrite: false — could cause artifacts with sorting but for clouds it usually looks okay-ish (all in one InstancedMesh, no sorting within). Hmm, with depthWrite false, the boxes' own faces won't occlude each other properly, creating a jumbled look. 

Let's go with opaque white clouds with slight blue-gray shading. That reads as Minecraft clouds. Fine. Maybe slightly transparent at 0.95? Just make them opaque.

Actually, let's make clouds with a texture? Not needed.

Camera flythrough: a smooth path over and between hills, looking around.

Use a CatmullRomCurve3 for the camera position, and another for the look-at target. Both with a `getPointAt(t)` using arc-length parameterization. Then loop over ~40 seconds. Actually we need everything important shown within the first 30 seconds. So the path should be ≤ 30s or the first 30s should cover the good stuff. Let's make a 30-second loop.

Design the path: it should fly over the landscape, dip between hills, pass over the lake, near trees, up toward mountains, and then loop. Since the world is 128x128 centered at origin (coordinates 0..128 → let's center at -64..64), and heights vary.

Let's define control points at various (x,z) with y = terrainHeight + offset. I'll sample terrain height along the path and set y = max(terrainHeight, seaLevel) + altitude. Compute at build time after terrain is generated.

Path points (in world coords, world spans -64..64):
Let's do a big loop:
- P0: (-70, ?, -70) start outside
- P1: (-40, ?, -50)
- P2: (-10, ?, -60)
- P3: (20, ?, -40)
- P4: (50, ?, -10)
- P5: (40, ?, 30)
- P6: (10, ?, 50)
- P7: (-30, ?, 40)
- P8: (-60, ?, 10)
- P9: (-70, ?, -70) close loop? CatmullRom closed curve.

Altitudes: sample terrain height h(x,z) and set y = max(h, seaLevel) + 8..18 varying to create swoops.

Look-at target: a point ahead on the path plus an offset, or a separate curve that weaves to look at interesting features. Let's create a second curve for the look target: points offset from the camera path in various directions (e.g., toward the lake, toward mountains, down at the ground, up at the sky). Actually simpler: look at a point on the camera path ahead by ~0.05 in t, plus a slow sinusoidal offset. That gives a natural "looking where you're going" feel. Then add a bit of banking/looking around with a slow sine.

Hmm, "looking around the landscape" — a slight independent drift is nice. Let's do: target = curve.getPointAt((t + 0.04) % 1) then add a per-frame offset from sin/cos to make it look around.

Actually let's define a separate lookAt curve with its own control points that point at interesting things. I'll do: lookCurve = CatmullRomCurve3 of points that are near the terrain, at a lower altitude, offset laterally. Let's just compute the look target as: a point ahead on the camera curve, with y lowered toward the terrain, and a lateral offset oscillating.

I'll do this:
```js
const t = (elapsed / DURATION) % 1;
const pos = camCurve.getPointAt(t);
const ahead = camCurve.getPointAt((t + 0.06) % 1);
const look = ahead.clone();
look.y = Math.max(terrainAt(look.x, look.z), SEA) + 2 + Math.sin(t*Math.PI*4)*4;
// add lateral drift
```
Hmm, `ahead` is already 6% ahead which at ~600 units path length is 36 units ahead. Good.

Add a slow roll/looking-around: offset look.x and look.z by sin(t*2π*1.5)*8.

Camera up: keep (0,1,0). Maybe add slight roll for cinematic feel: camera.rotation.z after lookAt. Let's add a subtle roll: `camera.rotateZ(Math.sin(t*Math.PI*2*2)*0.04)`.

Also, camera FOV maybe 60-70.

Timing: DURATION = 32 seconds. Within first 30 seconds we see most of the loop.

Now let's write the terrain generation code.

```js
const W = 128, H = 64;
const SEA = 14;
```

Height function:

```js
function fbm(x, y, oct, lac=2, gain=0.5) {
  let amp = 1, freq = 1, sum = 0, norm = 0;
  for (let i=0;i<oct;i++){
    sum += amp * noise2(x*freq, y*freq);
    norm += amp;
    amp *= gain; freq *= lac;
  }
  return sum / norm;
}
```

Wait, noise2 with different frequencies — I'm passing already-scaled coords. Let's define fbm(x, y, oct) where x,y are the base coordinates and internally multiply by frequency.

```js
function fbm(x, y, oct) {
  let amp = 1, freq = 1, sum = 0, norm = 0;
  for (let i = 0; i < oct; i++) {
    sum += amp * noise2(x * freq, y * freq);
    norm += amp;
    amp *= 0.5; freq *= 2;
  }
  return sum / norm;
}
```

Then:
```js
function heightAt(x, z) {
  // rolling hills
  let e = fbm(x*0.014, z*0.014, 4);            // 0..1
  let h = SEA + (e - 0.5) * 26;                 // -13..+13 around sea

  // mountain mask (large scale)
  let m = fbm(x*0.0055 + 100, z*0.0055 - 40, 3);
  let mm = smoothstep(0.48, 0.68, m);
  let ridge = 1 - Math.abs(2*fbm(x*0.022 + 13, z*0.022 + 7, 3) - 1);
  h += mm * ridge * 40;

  // lake basin
  const dx = x - (-30), dz = z - (28);
  const d2 = (dx*dx + dz*dz) / (46*46);
  h -= 26 * Math.exp(-d2 * 1.2);
  
  return h;
}
```

Hmm, I need to be careful the lake doesn't destroy mountains. Let's place the lake in a region where mountains are unlikely. Hard to guarantee. Just accept.

Actually, let me reconsider: rather than a gaussian subtraction which could create weird shapes, let me just rely on the natural terrain and lower the base a bit so there's a sea in the low areas. Then add a "lake" by ensuring the low-frequency noise creates one.

I'll do both: lower base so e<0.5 gives underwater, plus a mild basin.

Let me think about the ranges more concretely. Value noise with 4 octaves: mean 0.5, std maybe 0.12. So e ranges ~0.25..0.75 mostly. h = SEA + (e-0.5)*26 → SEA ± 6.5. So most terrain is within 6.5 of sea level. With SEA=14: 7.5..20.5. Underwater where e<0.5 → about half the map. Hmm, that's a lot of water. Let's use (e-0.5)*20 → ±5 → 9..19, still half underwater.

To have more land, bias: h = SEA + (e-0.45)*24 → e=0.45 → h=SEA. e ranges 0.25..0.75 → h from 14-4.8=9.2 to 14+7.2=21.2. Underwater portion: e<0.45, which is ~35%. That's reasonable for a "lake/sea".

Hmm, but with fbm the distribution is concentrated; a threshold at 0.45 gives maybe 30-40%. Fine.

Mountains: mm = smoothstep(0.5, 0.7, m) where m is 3-octave fbm with std ~0.14 → about 15% of the map has mm>0. Then h += mm*ridge*40 → up to +40. Peaks at ~60. Snow line at 34.

Hmm, H=64 max. Let's set max height ~56 to be safe. Clamp h to [1, 58].

Snow line: h > 36 → snow. Stone: 30-36. Grass below.

Actually, let's simplify biome:
- if h <= SEA+1 → sand (beach / underwater floor)
- else if h <= SEA+2.5 → sand beach
- else if h >= 38 → snow
- else if h >= 32 → stone (rocky)
- else grass

Hmm, the transition from grass to stone to snow should be based on height. With mountains up to 54, that gives a nice gradient. But the mountain mask creates slopes; steep slopes could show stone. Let's also use slope: if the local slope is steep, use stone. Compute slope from height differences. That's nice: cliffs look rocky.

Let me compute h at (x,z), and h at (x+1,z), (x,z+1) to get slope. If |dh| > 2 → stone.

OK.

Now block filling. Let's store a Uint8Array `blocks` of size W*W*H, index (y*W + z)*W + x. 0 = air.

Block types:
1 = grass, 2 = dirt, 3 = stone, 4 = sand, 5 = snow, 6 = wood, 7 = leaves, 8 = water.

For each column:
```
const hf = heightAt(x,z);
let h = Math.floor(hf);
h = clamp(h, 1, H-4);
for (let y=0; y<=h; y++) {
  let t;
  if (y === h) {
    // top block
    if (h <= SEA+1) t = SAND;
    else if (h >= SNOW) t = SNOW;
    else if (h >= ROCK) t = STONE;
    else t = GRASS;
  } else if (y > h-4) {
    t = (h <= SEA+1) ? SAND : (h >= SNOW ? STONE : DIRT);
  } else {
    t = STONE;
  }
  blocks[idx] = t;
}
```
Hmm, for snowy peaks the subsurface should be stone, and for the snow top layer, maybe 1 snow block over stone. Fine.

Water: for columns with h < SEA, fill blocks[y] = WATER for y from h+1 to SEA.

Wait, but if the top solid block is at y=h and h < SEA, then water fills h+1..SEA. Good.

Trees: after terrain, iterate over columns where top block is GRASS and h > SEA+1, with probability based on a forest noise. Place trees with min distance. Let's just use a simple approach: for each (x,z) with grass top and h between SEA+2 and 34, if hash(x,z) < 0.02 and a "forest density" noise > 0.45, and x,z within margin, plant a tree. Also enforce spacing by checking a grid or just accept overlaps (they look fine mostly). Let's enforce: keep a list and check distance > 4 from the previous tree? That's O(n²). With few hundred trees, fine.

Tree: trunk height 4-6, leaves: a 5x5x2 blob at the top + a 3x3x1 cap. Let's do a simple Minecraft-ish oak.

```js
function plantTree(x, y, z, rng) {
  const th = 4 + Math.floor(rng()*3);
  for (let i=0;i<th;i++) setBlock(x, y+1+i, z, WOOD);
  const top = y + th;
  for (let dx=-2; dx<=2; dx++) for (let dz=-2; dz<=2; dz++) {
    const r = Math.abs(dx)+Math.abs(dz);
    if (r <= 2 && !(r===2 && rng()<0.5)) {  // hmm
    }
  }
}
```
Let me do leaves as:
- layer at top-1 and top: radius 2 (5x5) minus corners
- layer at top+1: radius 1 (3x3)
- plus a single leaf at top+2 sometimes.

Standard Minecraft oak:
```
for y in [top-2, top-1]: 5x5 with corners removed
for y in [top, top+1]: 3x3
```
where top = y + th. Let's do:
- leaves at y = top-2, top-1: dx,dz in [-2,2], skip if |dx|==2 && |dz|==2 (corners), and randomly skip some edge ones.
- leaves at y = top, top+1: dx,dz in [-1,1].
Only set if the block is air.

Also make sure trees don't spawn over water or outside the map.

Now geometry building.

Iterate all blocks; for each non-air block, for each of 6 faces, check the neighbor. If the neighbor is air (0) or (for solid blocks) water — treat water as transparent → emit the face. For water blocks, only emit the top face if the block above is air.

Let me define:
```js
function isOpaque(t) { return t !== 0 && t !== WATER; }
```
For a solid block at (x,y,z) with face direction d: neighbor type nt. Emit face if !isOpaque(nt). So if the neighbor is water or air, emit. Good.

For water blocks: emit face only if the neighbor is air (0). Actually a water block's side face adjacent to air... water only exists below SEA and above terrain. Its sides: at the shoreline, the neighbor column has terrain top >= SEA so blocks[SEA] is solid → skip. Above? Water's top neighbor is air → emit top face. So water top faces emitted. But wait, we want only ONE water top face per column, which naturally happens since water fills from h+1 to SEA, and only the block at y=SEA has air above.

Hmm, but there's a subtlety: if a neighboring column has a lower terrain and water... all water columns are filled up to SEA, so all water top faces are at y=SEA. They form a flat plane. 

But we also need to handle: water at the edge of the map. Fine.

Now for the water geometry, use a separate material (transparent, blue) and separate merged geometry. Water faces get UV from the water tile, and vertex colors with brightness ~1.0 for top.

Water animation: to make it look alive, we could animate the water material's opacity or use a slight UV scroll. Since water is one merged geometry with a texture, we can offset texture.offset.y slowly. But the water texture is a tile in an atlas, so offsetting would break the atlas. Let's instead give water its own separate texture (a full 16x16 water tile as its own texture) — then we can scroll it. But the UVs for water would then be in 0..1 per block... Actually if water has its own texture, we can set UV per block face to (0..1) repeated? No, each face is a separate quad with UV 0..1 covering the whole texture. If we scroll the texture offset, each face would show a shifted version — since the texture is tileable-ish, we'd get a subtle shimmer. Hmm, but scrolling the whole texture offset moves all faces identically, which looks like the water pattern sliding. With wrapS/T = RepeatWrapping and offset animation, and UVs per face going 0..1, the offset shifts each face's sample window. That works and looks like flowing water. 

But faces are adjacent so the pattern wouldn't be continuous across faces. With a mostly-uniform water texture, it's fine.

Simplest: water material with color 0x2a6fb0, transparent, opacity 0.72, and no texture (or a subtle one). Add a slight animated distortion by... nah. Let's just use a texture with a slow offset. Good enough.

Actually, let's make the water use a slightly animated vertex displacement? No, keep it simple.

Hmm — actually, one more idea for water: give it vertex colors varying slightly by position to create subtle wave bands. Skip.

OK, decision: water = separate mesh, MeshBasicMaterial({ map: waterTex, transparent: true, opacity: 0.78, depthWrite: false, side: THREE.DoubleSide, fog: true }). Animate waterTex.offset.x/y slowly. Use a dedicated 32x32 water texture with wave patterns, RepeatWrapping.

Hmm, DoubleSide for water so we can see it from below — but we're always above. Use FrontSide for perf. Actually if the camera dips below sea level... it shouldn't. Use DoubleSide to be safe? It's only ~a few thousand quads. Fine, use FrontSide.

Now let's think about the number of faces and performance.

Let me just build it and hope. 128x128 = 16384 columns. For each column, ~1 top face + side faces. Side faces total = sum over columns of |h(x,z) - h(x+1,z)| + |h(x,z) - h(x,z+1)| (clamped at 0). With smooth terrain, average |dh| maybe 1.5 → 3 side faces per column. So ~4 faces/column → 65k faces → 65k*4 = 260k vertices, 390k triangles. That's OK for a modern GPU but the CPU-side generation takes a moment. Should be fine (< 1 second).

Memory: positions 260k*3 floats = 3.1MB, uvs 2MB, colors 3MB, indices 390k*3*4bytes... use Uint32 = 4.7MB. Total ~13MB. Fine.

Actually, we can use a Uint16 index if vertices < 65536, but we'll have more. Use Uint32Array indices (three.js handles this via setIndex with a Uint32BufferAttribute). Fine.

Alternatively use non-indexed geometry with 6 vertices per face (no index buffer) — simpler and avoids the index array. 390k vertices * (3+2+3) floats = 390k*8*4 = 12.5MB. Hmm, indexed is better. Let's use indexed.

Let me write the builder with pre-allocated arrays. Actually, let's use plain JS arrays and then convert — could be slow for 260k vertices but probably OK (~1M pushes). Let's preallocate typed arrays with an estimated size and grow if needed. Simpler: use regular arrays and `new Float32Array(arr)`. Pushing 260k*3 numbers into a JS array is fine (a few hundred ms maybe). Let's estimate the face count first, then allocate exactly.

Two-pass: first count faces, then fill. That requires iterating blocks twice — cheap. Let's do that. Or just use dynamic arrays and accept it. Let's do the two-pass count for cleanliness. Actually the neighbor check is the expensive part. Let's do it in one pass with dynamic arrays — it's simpler and the JIT handles array push reasonably. Hmm, 65k faces * 4 verts = 260k pushes per attribute array. That's fine, maybe 100ms total.

Let's do one pass with regular arrays.

Now, per-block tint: use hash of (x,y,z) to get a value in [0.93, 1.07], multiplied by face brightness. Store in color attribute.

Let's now write the code.

```js
import * as THREE from 'three';
```

No OrbitControls needed.

Structure:
1. Setup renderer, scene, camera.
2. Create texture atlas.
3. Generate terrain data.
4. Build geometry.
5. Build water mesh.
6. Build sky.
7. Build clouds.
8. Camera path.
9. Animation loop.

Let me write the atlas generation.

```js
const TILE = 16;
const ATLAS_COLS = 4;
const atlasCanvas = document.createElement('canvas');
atlasCanvas.width = atlasCanvas.height = TILE * ATLAS_COLS; // 64
const actx = atlasCanvas.getContext('2d');
```

For pixel art, use fillRect with 1x1 pixels.

Helper:
```js
function tileRect(i) {
  const col = i % ATLAS_COLS, row = Math.floor(i / ATLAS_COLS);
  return { x: col*TILE, y: row*TILE };
}
```

Now draw each tile with a small helper:
```js
function px(t, x, y, color) { ... }
```
Actually let's write a function that draws a tile given a base color and a noise function.

```js
function rnd(seed) { // deterministic
  let s = seed;
  return function() {
    s = (s * 1664525 + 1013904223) % 4294967296;
    return s / 4294967296;
  };
}
```

Draw functions:

```js
function drawTile(index, painter) {
  const {x: ox, y: oy} = tileRect(index);
  painter(ox, oy, (x, y, c) => { actx.fillStyle = c; actx.fillRect(ox+x, oy+y, 1, 1); });
}
```

grass_top (0): base #5b9c3a; add speckles with lighter #6fb84a and darker #4a8230.
grass_side (1): dirt base #7a5230 with speckles; top 3 rows green.
dirt (2): #7a5230 speckles.
stone (3): #8a8a8a with darker/lighter speckles.
snow_top (4): #f4f8ff with slight blue speckles.
snow_side (5): dirt/stone base with top 4 rows white.
sand (6): #e0d29a with speckles.
wood_side (7): #6b4b2a base with vertical darker lines.
wood_top (8): #b08a55 base with concentric rings.
leaves (9): #3f7f30 base with darker/lighter speckles and some transparent-ish holes (just darker).
water (10): #3a7fc4 base with wave lines.
gravel/other (11): #7f7f7f darker (for cliffs). Actually reuse stone.

Let's implement.

Now for the material: `new THREE.MeshBasicMaterial({ map: atlasTex, vertexColors: true, fog: true })`. Note: vertexColors multiplies with the map color.

Wait, MeshBasicMaterial's color is multiplied too; default white. Good.

Texture setup:
```js
const atlasTex = new THREE.CanvasTexture(atlasCanvas);
atlasTex.magFilter = THREE.NearestFilter;
atlasTex.minFilter = THREE.NearestFilter;
atlasTex.generateMipmaps = false;
atlasTex.colorSpace = THREE.SRGBColorSpace;
```
Hmm, in r186, `THREE.SRGBColorSpace` and renderer.outputColorSpace default is SRGB. Setting the texture colorSpace to SRGB is correct.

Also set `atlasTex.wrapS = atlasTex.wrapT = THREE.ClampToEdgeWrapping` to avoid bleeding at edges.

UV inset: use a small epsilon inset of 0.25/64 to avoid bleeding. Actually with NearestFilter and no mipmaps, bleeding only happens at exact edges due to floating point. Let's inset by 0.5 texel: uv = (px + 0.5)/64 for the outer edges? That would compress the texture. Better: inset by 0.05 texels. Let's just inset by 0.1/64.

Hmm, actually with nearest filtering, if UV lands exactly on a boundary it might sample the neighbor tile. A tiny inset fixes it. Let's use `const EPS = 0.02 / 64;` hmm that's tiny. Let's use 0.5/64 = 0.0078 inset on each side — that compresses the tile by 1 texel total which for a 16px tile means we lose a tiny bit at edges. Fine, actually it's safer. Let's use 0.25/64 inset.

Hmm, actually if I inset, the UV range per tile is [u0+eps, u1-eps], and with nearest filtering, sampling at u0+eps gives texel col*16, and at u1-eps gives texel col*16+15. Good.

OK.

Now, sun direction: let's put the sun at a nice angle, e.g., direction (0.4, 0.55, -0.7) normalized... Let's make it visible in the flythrough. Sun direction from origin: let's say the sun is at azimuth such that it's in the -Z +X direction, elevation ~35°. sunDir = normalize(0.55, 0.6, -0.58).

Hmm, the camera path moves around, so the sun will be visible at times. Good.

Sky colors: top #3a78c8 (deeper blue), horizon #bcd8f0 (pale), bottom #6b8fb5. Fog color = horizon-ish, e.g., #b8d4ee.

Actually let's make it a bit warmer: horizon #cfe3f5.

Now clouds: white boxes at y ≈ 70-95, sizes 8-24 wide, 3-5 tall. Drift along +X at 1.5-3 units/sec.

Since the world is 128 wide, clouds should span -200..200 so they're visible from anywhere. Let's spread them over a 500x500 area.

Cloud material with baked face shading: top 1.0, sides 0.92/0.86, bottom 0.75. Use a BoxGeometry(1,1,1) with vertex colors set per face. Actually BoxGeometry has 6 groups of 4 vertices each, in order: +X, -X, +Y, -Y, +Z, -Z. Each group has 4 vertices. So I can set the color attribute per group.

Let's do:
```js
const cloudGeo = new THREE.BoxGeometry(1,1,1);
const shades = [0.88, 0.82, 1.0, 0.72, 0.92, 0.86]; // +X,-X,+Y,-Y,+Z,-Z
const colors = new Float32Array(24*3);
for (let f=0; f<6; f++) for (let v=0; v<4; v++) {
  const i = (f*4+v)*3;
  colors[i] = colors[i+1] = colors[i+2] = shades[f];
}
cloudGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
```
Then InstancedMesh with MeshBasicMaterial({vertexColors: true, color: 0xffffff, fog: true}).

Wait, does InstancedMesh + vertexColors work? Yes.

Hmm, but the cloud color should be slightly blue-tinted white. Set material color to 0xf2f7ff.

Also should clouds be affected by fog? Yes, so distant clouds blend. Good.

Number of cloud instances: let's do 40 clouds * ~8 boxes = 320 boxes. Fine.

Actually, to make them "fluffy", let's generate each cloud as a cluster: a base rectangle of boxes with random sizes, plus a second layer on top with smaller boxes.

Let me write:
```js
const cloudBoxes = []; // {cx, cy, cz, ox, oy, oz, sx, sy, sz}
const cloudData = []; // {x, y, z, speed}
for (let i=0;i<44;i++){
  const cx = (rand()-0.5)*440;
  const cz = (rand()-0.5)*440;
  const cy = 78 + rand()*22;
  const w = 10 + rand()*22;
  const d = 8 + rand()*18;
  const speed = 1.0 + rand()*1.6;
  const ci = cloudData.push({x:cx, y:cy, z:cz, speed}) - 1;
  const n = 5 + Math.floor(rand()*5);
  for (let b=0;b<n;b++){
    const sx = 4 + rand()*10;
    const sy = 2.5 + rand()*2.5;
    const sz = 4 + rand()*10;
    const ox = (rand()-0.5)*w;
    const oz = (rand()-0.5)*d;
    const oy = (rand()-0.5)*2.5;
    cloudBoxes.push({ci, ox, oy, oz, sx, sy, sz});
  }
}
```
And a second smaller layer. Eh, one layer of 5-10 boxes each is enough for fluffy.

Per frame:
```js
for (let i=0;i<cloudData.length;i++){
  const c = cloudData[i];
  c.x += c.speed * dt;
  if (c.x > 260) c.x -= 520;
}
```
Then for each box, set the instance matrix. 350 boxes * compose per frame. Fine.

Actually, we can avoid updating every frame by only updating when needed... no, just update. It's fine.

Hmm, but updating instanceMatrix requires setting `instanceMatrix.needsUpdate = true` each frame, which re-uploads the buffer (350*16 floats = 22KB). Negligible.

Now, the camera path.

After terrain generation, define control points. I'll sample the terrain height along the path.

```js
const pathPts2D = [
  [-72, -72], [-40, -58], [-5, -62], [30, -48], [58, -22],
  [62, 14], [40, 44], [8, 60], [-28, 52], [-56, 24], [-68, -20]
];
```
Closed loop. For each, compute y = max(heightAt(x,z), SEA) + altitude where altitude varies: e.g., [14, 10, 16, 12, 18, 14, 10, 16, 12, 18, 14]. Let's make it vary smoothly to create swoops.

Actually, the camera should "fly over and between the hills". So altitudes between 8 and 22 above terrain. Let's compute:
```js
const pts = pathPts2D.map(([x,z], i) => {
  const h = Math.max(heightAt(x,z), SEA);
  const alt = 9 + 7 * Math.sin(i * 1.7) + 4*Math.cos(i*0.9);
  return new THREE.Vector3(x, h + alt, z);
});
const curve = new THREE.CatmullRomCurve3(pts, true, 'catmullrom', 0.5);
```
Hmm, with a closed curve and control points 60-80 units apart, CatmullRom will interpolate smoothly. But between control points, the curve might dip into terrain. To be safe, after building the curve, sample it and raise any point that's below terrain+minClearance. Let's do a post-process: sample 400 points along the curve, compute the required y, and if the curve's y is too low, adjust... but modifying curve points requires rebuilding. 

Alternative: build a custom path by sampling the curve, then correcting y, and then creating a new curve from the corrected points (400 points). That's a heavy curve but fine.

Actually, simpler: build the path from many points directly. Let's generate a smooth path parametrically and then set y from terrain:

```js
const N = 200;
const raw = [];
for (let i=0;i<N;i++){
  const t = i/N;
  const ang = t * Math.PI * 2;
  const r = 52 + 16*Math.sin(ang*2) + 8*Math.cos(ang*3);
  const x = Math.cos(ang) * r;
  const z = Math.sin(ang) * r * 0.95;
  raw.push(new THREE.Vector3(x, 0, z));
}
```
Then set y: y = max(terrainHeightAt(x,z), SEA) + clearance, where clearance = 8 + 6*sin(ang*3) etc. Then smooth the y values with a moving average to avoid jerkiness. Then create a closed CatmullRomCurve3 from these points.

This gives a nice orbit around the world center, weaving in and out. But we want to fly "between the hills" — the radius modulation does that.

Hmm, but the world is 128x128 = -64..64. A radius of 52-76 would go outside the map a lot. Let's keep the radius between 20 and 58 so we stay over the terrain. But then the camera flies in a circle over the middle, which might be too tight.

Let's do: r = 34 + 18*sin(ang*2 + 0.5). Range 16..52. Good. And add some z scaling.

Actually a loop that stays inside the map means we see the landscape from the inside — good for a flythrough. And the fog hides the map edges. Also, we should make sure the map edges aren't visible — with fog far ~200 and the world 128 wide, the edges might be visible from the air. Let's use a stronger fog (far ~150) so edges fade. Hmm, but then we can't see the mountains.

Alternative: make the world bigger, like 160x160. The requirement says at least 128x128. Let's do 160x160 = 25600 columns. Face count scales ~1.5x → ~100k faces. Should still be OK.

Hmm, let's stick with 128x128 but add fog with far ~180 and keep the camera lowish. Actually, an alternative: make the terrain extend visually by having the fog color match the sky, so the map edge blends. From an altitude of 30 looking at a map 128 wide, the far edge is ~100 units away → fog at 180 means the edge is only partially faded. Hmm.

Let's use W=160. 160*160*64 = 1.6M blocks array. Fine. Face count maybe 1.5x → 100k faces → 400k verts. Build time maybe 1-2 seconds. Acceptable.

Hmm, let's think about the build time more carefully. For each of 25600 columns, we fill ~20 blocks → 512k block writes. Then for each block we check 6 neighbors — that's 512k*6 = 3M checks. That's fine in JS, maybe 100-300ms.

But actually, most blocks are underground and fully enclosed; we still check them. We can optimize by only iterating over blocks from y = h-4 to h (the exposed surface region). But caves... no caves. Actually we only need to emit faces for blocks that have an air/water neighbor, which only happens near the surface. So we can skip interior blocks: only iterate y from max(0, h-6) to h. But side faces: a block at y could be exposed if a neighbor column has a lower height. The maximum height difference between neighbors is bounded by the terrain steepness (usually < 10). To be safe, iterate y from h-12 to h. Or just iterate all — 512k*6 checks is fine.

Let's just iterate all blocks but skip y where the block is deep (y < h - 16). Hmm, mountains with cliffs could have differences up to 10-15. Let's use y from max(0, h-20). Actually just do all y from 0 to h — simpler and safe. 512k blocks * 6 = 3M neighbor lookups. Each lookup is an array index + comparison. Should run in ~50-150ms. Fine.

Hmm, but the block array index computation with multiply... fine.

Actually, wait. There's a subtlety: for the face check, I need to look up the neighbor block. For y+1 and y-1 it's ±W*W offset. For x±1 it's ±1 (with boundary check). For z±1 it's ±W. Let me handle boundaries: if x==0 and dx==-1, the neighbor is outside → treat as air (emit face). Actually, for the map edges, emitting faces creates visible walls at the edges. Better to treat out-of-bounds as solid (don't emit) for x/z boundaries to avoid a wall of faces. Hmm, but then you'd see through. With fog, it doesn't matter much. Let's treat out-of-bounds as opaque (skip face) — saves faces.

Actually no: at the map edge, the side of the world would be open, and you'd see through the terrain into the void. But since we're flying inside the map and the fog is dense, we won't see it. Let's treat OOB as opaque (no face emitted).

Hmm, but for the bottom (y=0), if we don't emit bottom faces it's fine.

OK.

Now, the water mesh: for each column where h < SEA, add a top quad at y = SEA+1 (the top of the water block at y=SEA). Wait, blocks occupy [y, y+1]. Water fills y = h+1 .. SEA. So the top water block is at y=SEA, and its top face is at y = SEA+1. Let's use SEA = 14, so water surface at y=15.

Hmm, let me reconsider the coordinate convention: block at (x,y,z) occupies the cube from (x,y,z) to (x+1,y+1,z+1). The terrain height h means the topmost solid block is at y=h, so the ground surface is at y=h+1.

Let me redefine: `heightAt` returns the surface height in world units. The topmost solid block index = floor(h). Ground top surface = floor(h)+1.

Let's simplify: h = floor(heightAt(x,z)) → topmost block index. Ground surface y = h+1.

Sea level: water surface at y = SEA_Y. Water blocks fill from h+1 to SEA_Y-1. So water block indices y in [h+1, SEA_Y-1].

Let's set SEA_Y = 15. So water surface is at world y=15. Terrain top block index h; if h+1 < 15, then it's underwater.

Beach: if h+1 <= SEA_Y → underwater or at water level. Sand when h+1 <= SEA_Y + 2.

OK let's just define with block indices and be careful.

Let me define:
- `SEA = 15` — the y coordinate of the water surface (top of the water block at y=14).
- Water blocks are at y in [h+1, SEA-1] = [h+1, 14].
- If h >= 14, no water.

Let me now write heightAt returning a float, then h = clamp(floor(h), 1, H-2).

Now let's write everything.

One more consideration: the camera path's y should be above the terrain. I'll sample the terrain height function directly.

Let me now write the code in full.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Voxel World Flythrough</title>
<style>
  html, body { margin:0; padding:0; height:100%; overflow:hidden; background:#8fb8dc; }
  canvas { display:block; }
  #info { position:fixed; left:14px; bottom:12px; color:rgba(255,255,255,0.85); font:12px/1.4 system-ui, sans-serif; text-shadow:0 1px 3px rgba(0,0,0,.5); pointer-events:none; letter-spacing:.04em; }
</style>
</head>
<body>
<script type="importmap">
{ "imports": { "three": "...", "three/addons/": "..." } }
</script>
```
Wait — the prompt says "An import map is provided for you: do not add your own import map". So the environment already has an import map. I should NOT include one. Just use `import * as THREE from 'three'`.

OK, so no import map in my file.

Let me write the JS.

```js
import * as THREE from 'three';
```

Full code:

```js
// ---------- Renderer / Scene ----------
const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const FOG_COLOR = new THREE.Color(0xbcd6ee);
scene.fog = new THREE.Fog(FOG_COLOR, 55, 240);

const camera = new THREE.PerspectiveCamera(62, innerWidth/innerHeight, 0.1, 6000);
```

Fog near 55 far 240. The world is 160 wide → diagonal 226. From the center, the far edge is ~113. Hmm, so with fog far 240, the far edge is only at 47% fog. Let's use far 190 and near 40. Then at 113 the fog factor is (113-40)/150 = 0.49. Hmm, still visible.

Let's think about it differently: the camera flies at radius 20-55 from the center, at altitude 20-45. Looking toward the horizon, the map edge is 60-140 units away. With fog far ~160, the edge at 140 is 85% fogged. Good enough. Let's use near 30, far 175.

Hmm, but then nearby terrain (within 30 units) is unfogged and the mid-distance gets hazy. That's the desired "soft distance fog". OK.

Actually, let's use FogExp2 with density 0.0075 — gives a nice exponential falloff. At 100 units: 1-exp(-(0.0075*100)^2) = 1-exp(-0.5625) = 0.43. At 150: 1-exp(-1.265) = 0.72. At 200: 1-exp(-2.25)=0.89. That's a nice soft falloff. Let's use FogExp2 with density 0.0072.

Hmm, but with linear fog it's easier to control. Let's go with FogExp2(0xbcd6ee, 0.0068).

OK.

Now the sky dome. Let me write the shader.

```js
const skyGeo = new THREE.SphereGeometry(3000, 32, 20);
const skyMat = new THREE.ShaderMaterial({
  side: THREE.BackSide,
  depthWrite: false,
  fog: false,
  uniforms: {
    uSunDir: { value: sunDir },
    uTop: { value: new THREE.Color(0x2f6fc4) },
    uHorizon: { value: new THREE.Color(0xbcd6ee) },
    uBottom: { value: new THREE.Color(0x5c7ea3) },
  },
  vertexShader: `
    varying vec3 vDir;
    void main() {
      vDir = position;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,
  fragmentShader: `
    varying vec3 vDir;
    uniform vec3 uSunDir, uTop, uHorizon, uBottom;
    void main() {
      vec3 d = normalize(vDir);
      float h = d.y;
      vec3 col = mix(uHorizon, uTop, pow(clamp(h, 0.0, 1.0), 0.55));
      col = mix(col, uBottom, clamp(-h * 2.5, 0.0, 1.0));
      float sd = max(dot(d, uSunDir), 0.0);
      col += vec3(1.0, 0.94, 0.78) * pow(sd, 900.0) * 2.0;
      col += vec3(1.0, 0.88, 0.66) * pow(sd, 20.0) * 0.18;
      col += vec3(1.0, 0.9, 0.7) * pow(sd, 4.0) * 0.05;
      gl_FragColor = vec4(col, 1.0);
    }
  `
});
```

Note: with `outputColorSpace = SRGBColorSpace` and no tone mapping, the shader outputs linear values that get converted... Actually, ShaderMaterial output goes through the output color space conversion in the fragment shader only if the material is compiled with the color space defines. In three.js, for ShaderMaterial the user is responsible. Hmm — actually three.js appends `colorspace_fragment` chunk only if the shader includes `#include <colorspace_fragment>`. For a raw ShaderMaterial, no conversion is applied, so the values are written directly to the framebuffer (which is sRGB-encoded output... no, the framebuffer is just RGBA8, and three.js does the linear→sRGB conversion in the shader for built-in materials).

So if I write raw color values in my sky shader, they'll appear as-is in the framebuffer. Since I'm picking colors that look good in sRGB space, that's actually what I want. But then the terrain (MeshBasicMaterial with sRGB texture) gets converted from linear to sRGB on output. Hmm, so there might be a mismatch: the fog color I set is converted... 

Let me think. `scene.fog.color` is set from a hex which, in three.js r152+, is converted to linear-sRGB working space (via `Color.setHex(hex, SRGBColorSpace)` default). Then in the shader, the fog color is used in linear space and then converted to sRGB on output. So the final on-screen fog color matches the hex I specified. Good.

For my sky shader, if I set `uHorizon` from `new THREE.Color(0xbcd6ee)`, that Color is in linear working space (since setHex converts to working color space by default). If I output it directly without the linear→sRGB conversion, it'll look darker/more saturated than intended.

Solution: include the colorspace conversion in my sky shader. Add `#include <colorspace_fragment>` at the end? That chunk operates on `gl_FragColor`. Let me just do it manually:

```glsl
gl_FragColor = vec4(col, 1.0);
#include <colorspace_fragment>
```
This requires `gl_FragColor` to be defined and the chunk does `gl_FragColor = linearToOutputTexel(gl_FragColor);`. In r186, ShaderMaterial shaders get the standard prefix... Actually the `colorspace_fragment` chunk is:
```glsl
gl_FragColor = linearToOutputTexel( gl_FragColor );
```
And `linearToOutputTexel` is defined in the `colorspace_pars_fragment` chunk which is included in the material's fragment shader prefix... Hmm, for ShaderMaterial, three.js adds a prefix with common defines and includes. Let me check: in WebGLProgram, for non-raw ShaderMaterial, the fragment shader prefix includes things like `#include <colorspace_pars_fragment>`? 

Looking at three.js's WebGLProgram.js, the `prefixFragment` for regular (non-raw) shaders includes:
```
getTexelEncodingFunction / ShaderChunk['colorspace_pars_fragment'],
```
Actually in recent versions the prefix contains:
```js
prefixFragment = [
  ...
  ShaderChunk['colorspace_pars_fragment'],
  ...
]
```
Hmm, I'm not 100% sure. In r152+, `prefixFragment` includes:
```
'#include <colorspace_pars_fragment>',
```
Hmm. Let me avoid the risk.

Simpler approach: set the uniform colors using `new THREE.Color().setHex(0xbcd6ee, THREE.SRGBColorSpace)` — no wait, that's the same thing.

Alternative: use `THREE.Color` with `setRGB(r, g, b, THREE.LinearSRGBColorSpace)` to define the color directly in linear space. So I convert my desired sRGB hex to linear manually.

Even simpler: define the sky colors as raw sRGB values and output them directly, and set the fog color to match by using a color that, when converted, matches. Ugh.

Cleanest approach: Use `THREE.Color` in linear space and add the conversion in the shader. To get `linearToOutputTexel`, I can just implement it myself:

```glsl
vec3 lin2srgb(vec3 c) {
  return mix(c * 12.92, 1.055 * pow(c, vec3(1.0/2.4)) - 0.055, step(0.0031308, c));
}
```
Hmm, `step` with vec3... Let me write:
```glsl
vec3 lin2srgb(vec3 c){
  vec3 lo = c * 12.92;
  vec3 hi = 1.055 * pow(max(c, vec3(0.0)), vec3(0.4166667)) - 0.055;
  return mix(lo, hi, step(vec3(0.0031308), c));
}
```
Then `gl_FragColor = vec4(lin2srgb(col), 1.0);`

And set the uniform colors via `new THREE.Color(0x2f6fc4)` which gives linear values (since setHex converts from sRGB to linear by default in r152+). Then the shader math works in linear and converts to sRGB at the end. 

Actually wait — is the default for `new THREE.Color(hex)` to convert to working color space? In r152+, `Color.setHex(hex, colorSpace = SRGBColorSpace)` converts to the working color space (linear-sRGB). Yes, `THREE.ColorManagement.enabled` is true by default. So `new THREE.Color(0x2f6fc4)` gives linear-space RGB values. Good.

So: sky shader computes in linear, then converts to sRGB at the end. Fog color also linear. Everything consistent. 

Hmm, but there's a subtlety: does three.js apply tone mapping? Only if `renderer.toneMapping !== NoToneMapping`. Default is NoToneMapping. Good.

OK. Also, `renderer.outputColorSpace = THREE.SRGBColorSpace` is the default.

Let me double-check the MeshBasicMaterial + map + vertexColors path: the texture is sRGB (colorSpace set), so it's decoded to linear, multiplied by vertex color (which I set as raw floats — hmm, vertex colors are assumed to be in linear working space). So my brightness multipliers like 0.8 are applied in linear space, which is correct for shading.

But careful: a brightness of 0.8 in linear space looks like a bigger difference than 0.8 in sRGB. Actually, applying a linear multiplier makes the face noticeably darker. That's what we want for shading. Maybe use slightly higher values: top 1.0, sides 0.82/0.70, bottom 0.5.

Hmm, let's think: linear 0.7 → sRGB ≈ 0.87. So a side face at 0.7 linear looks like 87% brightness on screen. That's subtle. For strong cube definition, we want more contrast. Let's use: top 1.0, +Z 0.80, -Z 0.68, +X 0.72, -X 0.60, bottom 0.42.

In sRGB terms: 0.80 → 0.91, 0.68 → 0.85, 0.72→0.87, 0.60→0.81, 0.42→0.69. Hmm, those are still fairly subtle in sRGB.

Hmm. Since the texture already has color, and I multiply in linear... Let's just be more aggressive: top 1.0, +Z 0.72, -Z 0.55, +X 0.62, -X 0.46, bottom 0.30.

In sRGB: 0.72→0.87, 0.55→0.77, 0.62→0.82, 0.46→0.72, 0.30→0.58. That gives a nice range from 100% to 58%. Good contrast.

Hmm, but the texture colors also get multiplied. A green grass top at sRGB (0.35, 0.62, 0.23) → linear (0.10, 0.34, 0.04). Multiplied by 0.46 → (0.046, 0.157, 0.018) → sRGB (0.23, 0.42, 0.15). That's a dark green. Reasonable for a shadowed side.

OK, let's go with those values.

Now let me also think: should I add a slight ambient occlusion? Let's skip.

Now, writing the terrain code.

```js
const W = 160, H = 64;
const SEA = 15;  // water surface y
```

Wait, with H=64 and terrain up to ~55, that's fine.

Let me now write heightAt:

```js
function hash2(x, y) {
  let h = Math.imul(x | 0, 374761393) + Math.imul(y | 0, 668265263);
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  h ^= h >>> 16;
  return (h >>> 0) / 4294967296;
}

function vnoise(x, y) {
  const xi = Math.floor(x), yi = Math.floor(y);
  const xf = x - xi, yf = y - yi;
  const u = xf * xf * (3 - 2 * xf);
  const v = yf * yf * (3 - 2 * yf);
  const a = hash2(xi, yi), b = hash2(xi + 1, yi);
  const c = hash2(xi, yi + 1), d = hash2(xi + 1, yi + 1);
  return (a + (b - a) * u) * (1 - v) + (c + (d - c) * u) * v;
}

function fbm(x, y, oct) {
  let amp = 1, freq = 1, sum = 0, norm = 0;
  for (let i = 0; i < oct; i++) {
    sum += amp * vnoise(x * freq, y * freq);
    norm += amp;
    amp *= 0.5; freq *= 2;
  }
  return sum / norm;
}
```

Note: hash2 with negative coordinates — Math.imul handles negatives fine, and the result is a 32-bit int. `(h>>>0)/2^32` gives [0,1). Good. But `Math.floor(x)` for x=-0.5 gives -1, and hash2(-1, ...) works. OK.

smoothstep:
```js
function smoothstep(a, b, x) {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
}
```

heightAt:
```js
function heightAt(x, z) {
  // base rolling terrain
  const e = fbm(x * 0.013 + 40, z * 0.013 - 17, 4);
  let h = SEA + (e - 0.44) * 30;

  // mountains
  const m = fbm(x * 0.0065 - 90, z * 0.0065 + 55, 3);
  const mm = smoothstep(0.47, 0.66, m);
  const rn = fbm(x * 0.026 + 7, z * 0.026 + 3, 3);
  const ridge = 1 - Math.abs(2 * rn - 1);
  h += mm * ridge * 46;

  // lake basin
  const lx = x + 34, lz = z - 26;
  const ld = (lx*lx + lz*lz) / (44*44);
  h -= 30 * Math.exp(-ld * 1.6);

  return h;
}
```

Hmm, e ranges 0.25..0.75 with 4 octaves (std ~0.11). (e-0.44)*30 → -5.7..+9.3. So h ranges 9.3..24.3 around SEA=15. Water where h < 15 → e < 0.44 → about 35-40% of the map. Hmm, that's a lot of water. But with the lake basin subtracting up to 30 in the lake region, more water there.

Let's shift: (e - 0.40) * 30 → h from 10.5 to 25.5. Underwater where e<0.40 → ~30%. Plus the lake. Hmm.

Actually, let's think about it as: we want maybe 20% water. e < 0.36 → about 20%. So use (e-0.36)*30 → h from 11.7 to 26.7. Hmm, that's a lot of land at high elevation, leaving little beach.

Let's simplify: base h = SEA + (e - 0.40) * 26. e in [0.25, 0.75] → h in [11.1, 24.1]. Water where e < 0.40.

Plus mountains add up to 46. So peaks at ~70. That's over H=64. Let's cap the mountain addition: mm*ridge*40, and clamp h to [2, 58].

Hmm, peaks at 24 + 40 = 64. Clamp to 58. Let's reduce: mm*ridge*38 → max 62. Clamp at 56.

Let me reduce the base range so there's more room: base h = SEA + (e-0.40)*22 → 12.3..25.3. Then + 38 → 63. Still high. 

OK, let's set H = 72 and clamp heights to 62. Actually H=72 means 160*160*72 = 1.84M bytes. Fine.

Hmm, but really high peaks might look weird. Let's target max height ~50.

base: SEA + (e-0.40)*22 → 12.3 to 25.3, mean ~17.
mountains: mm*ridge*34 → up to 34. Peaks at 25+34 = 59. Hmm.

The issue is that the max of both is rare. Realistically mm is ~0.8 max and ridge ~0.9 → 0.72*34 = 24.5. So peaks ~ 22+24 = 46. OK that's fine.

Let's set H = 64 and clamp to 60. Snow line at 38.

Actually, let's define snow line relative to the max: SNOW_LINE = 36, ROCK_LINE = 29.

Hmm, with peaks at ~46 and typical land at ~17-25, the snow region would be small. Let's lower: SNOW_LINE = 34, ROCK_LINE = 27.

Fine, I'll tune with these numbers.

Let me reconsider the mountain mask threshold. m = fbm(...,3) has std ~0.13, mean 0.5. smoothstep(0.47, 0.66, m): m=0.47 → 0, m=0.66 → 1. Since m>0.66 is ~11% of the map and m>0.47 is ~60%, we get a broad gradient of mountain influence. That's fine — mountains rise gradually over much of the map.

Hmm, but then the "hills" would be quite tall everywhere. Let's use smoothstep(0.52, 0.70, m): m>0.70 is ~6%, m>0.52 is ~44%.

I'll go with smoothstep(0.50, 0.68, m).

OK, whatever. Let's just write it and trust it produces a varied landscape. The exact aesthetic is hard to predict; I'll aim for reasonable parameters.

Let me now write the block generation.

```js
const blocks = new Uint8Array(W * H * W);
const AIR = 0, GRASS = 1, DIRT = 2, STONE = 3, SAND = 4, SNOW = 5, WOOD = 6, LEAF = 7, WATER = 8;

function idx(x, y, z) { return (y * W + z) * W + x; }
```

Generate:
```js
const heights = new Int16Array(W * W);
for (let z = 0; z < W; z++) {
  for (let x = 0; x < W; x++) {
    let hf = heightAt(x, z);
    let h = Math.floor(hf);
    h = Math.max(1, Math.min(H - 3, h));
    heights[z*W + x] = h;

    for (let y = 0; y <= h; y++) {
      let t;
      if (y === h) {
        if (h + 1 <= SEA + 1) t = SAND;
        else if (h >= SNOW_LINE) t = SNOW;
        else if (h >= ROCK_LINE) t = STONE;
        else t = GRASS;
      } else if (y > h - 4) {
        if (h + 1 <= SEA + 1) t = SAND;
        else if (h >= ROCK_LINE) t = STONE;
        else t = DIRT;
      } else {
        t = STONE;
      }
      blocks[idx(x,y,z)] = t;
    }
    // water
    for (let y = h + 1; y < SEA; y++) {
      blocks[idx(x,y,z)] = WATER;
    }
  }
}
```

Wait — `h+1 <= SEA+1` means h <= SEA. So the sand condition is h <= SEA = 15, i.e., terrain surface at y <= 16, and water surface at 15. So columns with h <= 15 are underwater or at water level → sand. Good. And beach: h == 16, 17 → hmm, the condition only catches h <= 15.

Let's use: `h <= SEA + 2` → h <= 17 → sand (including underwater). That gives a 2-block beach above water. Good.

Then grass for h >= 18.

Snow: h >= 36. Rock: h >= 29.

Hmm, and for the "underwater floor" we want sand too. h <= 17 covers underwater (h <= 15) and the beach. Good.

But wait, for deep underwater, h might be 5, and the surface should still be sand. Yes.

Now trees. Let's place them after.

```js
const treeSpots = [];
const margin = 3;
let rngState = 12345;
function rng() {
  rngState = (Math.imul(rngState, 1664525) + 1013904223) >>> 0;
  return rngState / 4294967296;
}
```
Hmm, using a global rng with a deterministic sequence is fine but the order of calls matters. It's deterministic per run, so fine.

Actually for tree placement I want a hash-based approach so it's spatially consistent. Let's just use the rng.

```js
for (let z = margin; z < W - margin; z++) {
  for (let x = margin; x < W - margin; x++) {
    const h = heights[z*W + x];
    if (h <= SEA + 2 || h >= ROCK_LINE) continue;   // no trees on beach/rock
    const dens = fbm(x * 0.03 + 200, z * 0.03 - 120, 2);
    if (dens < 0.52) continue;
    if (rng() > 0.06) continue;
    // spacing check
    let ok = true;
    for (const t of treeSpots) {
      const dx = t[0]-x, dz = t[1]-z;
      if (dx*dx + dz*dz < 25) { ok = false; break; }
    }
    if (!ok) continue;
    treeSpots.push([x, h, z]);
  }
}
```

The spacing check is O(n²) but n is maybe 300 → 90k checks. Fine. Actually the rng() > 0.06 check comes before the spacing check, so we only do the spacing check for 6% of columns → 0.06 * 25600 = 1536 candidates, each checking against up to ~300 spots = 460k checks. Fine.

Hmm, but trees would be planted at 6% of forest columns... Let's see: forest density > 0.52 covers ~40% of columns, and 6% of those → 2.4% of the map ≈ 600 trees before spacing. With spacing 5, we'd get fewer. Let's use a spacing of 4 (dx²+dz² < 16). Maybe ~400 trees. Each tree is ~30 blocks (trunk 5 + leaves 25) → 12000 blocks. Fine.

Then plant:

```js
function setBlock(x, y, z, t, overwrite) {
  if (x < 0 || x >= W || y < 0 || y >= H || z < 0 || z >= W) return;
  const i = idx(x,y,z);
  if (!overwrite && blocks[i] !== AIR) return;
  blocks[i] = t;
}

for (const [x, h, z] of treeSpots) {
  const th = 4 + Math.floor(rng() * 3);
  for (let i = 1; i <= th; i++) setBlock(x, h + i, z, WOOD, false);
  const top = h + th;
  for (let dy = -2; dy <= 1; dy++) {
    const r = (dy <= -1) ? 2 : 1;
    for (let dx = -r; dx <= r; dx++) {
      for (let dz = -r; dz <= r; dz++) {
        if (r === 2 && Math.abs(dx) === 2 && Math.abs(dz) === 2) continue;
        if (r === 2 && (Math.abs(dx) === 2 || Math.abs(dz) === 2) && rng() < 0.35) continue;
        setBlock(x + dx, top + dy, z + dz, LEAF, false);
      }
    }
  }
  setBlock(x, top + 2, z, LEAF, false);
}
```

Hmm, `top + dy` for dy in [-2, 1] → layers at top-2, top-1, top, top+1. The trunk goes from h+1 to h+th = top. So the leaves at top-2..top+1 cover the trunk top. Good. And a single leaf at top+2.

Wait, `setBlock(..., false)` means don't overwrite — so leaves won't replace the trunk. Good. But the trunk placement with overwrite=false means if there's already a block (e.g., terrain) it won't be replaced. Since we start at h+1, which is air, that's fine.

Hmm, but trees on a slope: the trunk base is at h+1 where h is the column's top block. Fine.

Now geometry building.

```js
const positions = [], uvs = [], colors = [], indices = [];
let vcount = 0;
```

Face definitions as functions. Let me write a helper:

```js
const FACES = [
  { // +X
    dir: [1, 0, 0], shade: 0.62,
    corners: [[1,0,1],[1,0,0],[1,1,0],[1,1,1]],
    uvs: [[0,0],[1,0],[1,1],[0,1]]
  },
  ...
];
```
Where corner [cx,cy,cz] is added to the block position, and uv [u,v] is in 0..1 within the tile (u right, v up).

Then for a face, uv coords are computed as:
u = u0 + cu * (u1-u0), v = v0 + cv * (v1-v0).

Where u0 = (col + inset)/4, u1 = (col+1-inset)/4, v0 = 1 - (row+1-inset)/4, v1 = 1 - (row - ... hmm.

Let me define with the atlas 4x4:
- col = tile % 4, row = floor(tile/4)
- u0 = (col + INSET) / 4
- u1 = (col + 1 - INSET) / 4
- v1 = 1 - (row + INSET) / 4      // top of the tile in UV
- v0 = 1 - (row + 1 - INSET) / 4  // bottom of the tile in UV

With INSET = 0.25/16 = 0.015625 in tile units... wait. Let me define inset in texels: 0.5 texel out of 16 → in tile fraction that's 0.5/16 = 0.03125. Then in atlas UV units, u0 = (col + 0.03125)/4.

Hmm, let's simplify: INSET_TEXELS = 0.25. In tile units: 0.25/16 = 0.015625. So:
u0 = (col + 0.015625) / 4
u1 = (col + 0.984375) / 4
v1 = 1 - (row + 0.015625) / 4
v0 = 1 - (row + 0.984375) / 4

Good.

Now, corners and uvs per face. Let me define them as flat arrays.

Face +X: corners in order A,B,C,D where A=(1,0,1), B=(1,0,0), C=(1,1,0), D=(1,1,1); uvs: A=(0,0), B=(1,0), C=(1,1), D=(0,1).
Face -X: A=(0,0,0), B=(0,0,1), C=(0,1,1), D=(0,1,0); uvs A=(0,0),B=(1,0),C=(1,1),D=(0,1).
Face +Y: A=(0,1,0), B=(0,1,1), C=(1,1,1), D=(1,1,0); uvs A=(0,1),B=(0,0),C=(1,0),D=(1,1).
Face -Y: A=(0,0,1), B=(0,0,0), C=(1,0,0), D=(1,0,1); uvs A=(0,0),B=(1,0),C=(1,1),D=(0,1).
Face +Z: A=(0,0,1), B=(1,0,1), C=(1,1,1), D=(0,1,1); uvs A=(0,0),B=(1,0),C=(1,1),D=(0,1).
Face -Z: A=(1,0,0), B=(0,0,0), C=(0,1,0), D=(1,1,0); uvs A=(0,0),B=(1,0),C=(1,1),D=(0,1).

Wait, for -X I need to double check the winding I derived earlier:
-X: A=(x,y,z), B=(x,y,z+1), C=(x,y+1,z+1), D=(x,y+1,z). So relative: A=(0,0,0), B=(0,0,1), C=(0,1,1), D=(0,1,0). ✓.

+X: A=(x+1,y,z+1), B=(x+1,y,z), C=(x+1,y+1,z), D=(x+1,y+1,z+1) → relative A=(1,0,1), B=(1,0,0), C=(1,1,0), D=(1,1,1). ✓

+Y: A=(x,y+1,z), B=(x,y+1,z+1), C=(x+1,y+1,z+1), D=(x+1,y+1,z) → A=(0,1,0), B=(0,1,1), C=(1,1,1), D=(1,1,0). ✓

-Y: A=(x,y,z+1), B=(x,y,z), C=(x+1,y,z), D=(x+1,y,z+1) → A=(0,0,1), B=(0,0,0), C=(1,0,0), D=(1,0,1). ✓

+Z: A=(x,y,z+1), B=(x+1,y,z+1), C=(x+1,y+1,z+1), D=(x,y+1,z+1) → A=(0,0,1), B=(1,0,1), C=(1,1,1), D=(0,1,1). ✓

-Z: A=(x+1,y,z), B=(x,y,z), C=(x,y+1,z), D=(x+1,y+1,z) → A=(1,0,0), B=(0,0,0), C=(0,1,0), D=(1,1,0). ✓

Triangles: (0,1,2) and (0,2,3).

Now the UV orientation for side faces: v=0 at the bottom, v=1 at the top. With our UV mapping, v0 is the bottom of the tile and v1 the top. So uv v-coordinate = v0 + cv*(v1-v0). For A with cv=0 → v0 (bottom of tile) at the bottom of the face. ✓ So grass_side's green strip (drawn at the top of the tile, rows 0-3 in canvas coordinates) will appear at the top of the face. ✓

For the top face, uvs A=(0,1), B=(0,0), C=(1,0), D=(1,1): A is at (x, z) with v=1 (tile top), B at (x, z+1) with v=0. So the tile's top row maps to z, and the bottom row to z+1. Fine for noise textures.

Now the shading multiplier per face:
+X: 0.62
-X: 0.46
+Y: 1.0
-Y: 0.30
+Z: 0.72
-Z: 0.55

Hmm, let's reorder to match: [+X, -X, +Y, -Y, +Z, -Z] = [0.62, 0.46, 1.0, 0.30, 0.72, 0.55].

Hmm, +X vs -X differ a lot (0.62 vs 0.46). That's because the sun is at +X. Actually let me make the shading consistent with the sun direction. Sun dir = normalize(0.55, 0.6, -0.58). So the sun is toward +X, +Y, -Z.

Faces facing the sun should be brighter: +X (dot with sun.x=0.55) and -Z (dot with -sun.z=0.58). Hmm, -Z face normal is (0,0,-1), dot with sunDir = 0.58. +Z face normal (0,0,1), dot = -0.58.

So: +X bright, -Z bright, +Y brightest, -X dark, +Z dark.

Let's set: +Y 1.0, +X 0.78, -Z 0.72, -X 0.52, +Z 0.48, -Y 0.32.

Hmm, that's a nice range. Let's go with:
+X: 0.78, -X: 0.50, +Y: 1.0, -Y: 0.33, +Z: 0.47, -Z: 0.72.

Hmm, but this makes the +Z faces quite dark. In a typical scene you'd see both +X and +Z faces. The contrast is good for definition.

Let me soften a bit: +X: 0.80, -X: 0.55, +Y: 1.0, -Y: 0.35, +Z: 0.52, -Z: 0.75.

OK.

Per-block tint: hash-based, range [0.94, 1.06]. Applied multiplicatively.

Now the water: separate arrays.

Water face: only the top face of each water block at y = SEA-1 (the topmost water block). Actually, let's emit the top face for each column where h < SEA-1... hmm.

Let me reconsider. Water blocks are placed at y from h+1 to SEA-1. The topmost water block is at y = SEA-1, and its top face is at y = SEA. So the water surface is at world y = SEA = 15.

For columns where h+1 > SEA-1, i.e., h >= SEA-1, there's no water. Right.

So: for each column with h < SEA-1, emit a top face at y = SEA for the block (x, SEA-1, z).

Hmm, but the top face of a water block that's adjacent to air — yes, always air above.

OK. And water UV: use the water tile UVs (full tile 0..1 per face), with the water texture as a separate repeating texture. Let me use a separate water texture (32x32) with RepeatWrapping, and set the UV per face to (0,0),(0,1),(1,1),(1,0) — well, in the correct winding order.

Actually, if the water texture has RepeatWrapping and I animate offset, per-face UV 0..1 works.

Hmm, but I want the water UVs to be scaled so the texture repeats more across a block? 1 repeat per block is fine.

Let me just use the atlas for water too, and animate a slight opacity or use a second overlapping plane... Nah.

Decision: separate water texture (32x32 canvas with wave patterns), RepeatWrapping, offset animated.

Water face winding for the top face:
A=(x, y, z) → uv(0,1)
B=(x, y, z+1) → uv(0,0)
C=(x+1, y, z+1) → uv(1,0)
D=(x+1, y, z) → uv(1,1)
where y = SEA.

Wait, that's the +Y face with uv A=(0,1),B=(0,0),C=(1,0),D=(1,1). Yes.

Water color: vertex color 1.0 (or slight variation).

Water material: MeshBasicMaterial({ map: waterTex, transparent: true, opacity: 0.75, depthWrite: false, side: THREE.DoubleSide, fog: true, color: 0x9fd4ff }). Hmm, the color multiplies the texture. Let's set color 0xffffff and make the texture blue.

Actually with transparency, the water will show the sand/terrain below. 

Since depthWrite is false and it's a single mesh, the draw order within the mesh is by index order, which could cause artifacts where two water quads overlap... they don't overlap (they're coplanar and non-overlapping). Fine.

Now, one issue: with depthWrite false, the water won't occlude anything, but it's the topmost layer anyway.

Also, the water plane at y=15 while the terrain around it is higher — the water will be drawn over the terrain? No, depth testing still happens (depthTest is on by default), so terrain in front occludes water. Good.

But: the terrain below the water is drawn first (opaque), then the water blends over it. ✓

Also, blocks under the water surface — their top faces are at y = h+1 < 15, so they're below the water. We render them and then the water on top. 

Now, renderOrder: set water.renderOrder = 1 to ensure it draws after opaque. Three.js already sorts transparent objects after opaque. Good.

Now, the geometry creation code:

```js
const posArr = [], uvArr = [], colArr = [], idxArr = [];
let vc = 0;

function pushFace(px, py, pz, f, tile, tint, out) { ... }
```

Let me write it inline for the solid mesh and the water mesh separately.

For solid:
```js
const NEIGH = [[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]];
```

Loop:
```js
for (let y = 0; y < H; y++) {
  for (let z = 0; z < W; z++) {
    for (let x = 0; x < W; x++) {
      const t = blocks[idx(x,y,z)];
      if (t === AIR || t === WATER) continue;
      const tileSet = TILE_FOR[t]; // {top, side, bottom}
      for (let f = 0; f < 6; f++) {
        const nx = x + NEIGH[f][0], ny = y + NEIGH[f][1], nz = z + NEIGH[f][2];
        if (nx < 0 || nx >= W || nz < 0 || nz >= W || ny < 0 || ny >= H) continue;  // skip OOB
        const nt = blocks[idx(nx,ny,nz)];
        if (nt !== AIR && nt !== WATER) continue;
        ...
      }
    }
  }
}
```

Hmm, if ny >= H, skip. But the top of the world is always air since h <= H-3. OK.

Tile selection:
- top face (f===2): TILE_FOR[t].top
- bottom face (f===3): TILE_FOR[t].bottom (usually same as side, or dirt)
- else: TILE_FOR[t].side

For grass: top = grass_top (0), side = grass_side (1), bottom = dirt (2).
For dirt: all dirt (2).
For stone: all stone (3).
For sand: all sand (6).
For snow: top = snow_top (4), side = snow_side (5), bottom = dirt(2)? Let's use stone for bottom. Eh, use snow_side for the bottom too. Actually, the bottom is rarely seen. Use stone.
For wood: top/bottom = wood_top (8), side = wood_side (7).
For leaves: all leaves (9).

Let's define:
```js
const TILE_FOR = {
  [GRASS]: { top: 0, side: 1, bottom: 2 },
  [DIRT]:  { top: 2, side: 2, bottom: 2 },
  [STONE]: { top: 3, side: 3, bottom: 3 },
  [SAND]:  { top: 6, side: 6, bottom: 6 },
  [SNOW]:  { top: 4, side: 5, bottom: 3 },
  [WOOD]:  { top: 8, side: 7, bottom: 8 },
  [LEAF]:  { top: 9, side: 9, bottom: 9 },
};
```

Now the tint: 
```js
function tintAt(x,y,z) {
  let h = Math.imul(x*73856093 ^ y*19349663 ^ z*83492791, 2654435761);
  ...
}
```
Simpler: 
```js
const tv = hash2(x*31 + y*17, z*57 + y*13);  // reuse hash2
const tint = 0.94 + tv * 0.12;
```
Using hash2(x*3+y, z*5+y) — might produce patterns. Let's do `hash2(x + y * 71, z + y * 37)`. Good enough.

Actually, for the tint to look like natural variation, apply it per-block (same for all faces of a block). Yes.

Now, the vertex color = shade[f] * tint.

OK, let's write it.

After building, create the BufferGeometry:
```js
const geo = new THREE.BufferGeometry();
geo.setAttribute('position', new THREE.Float32BufferAttribute(posArr, 3));
geo.setAttribute('uv', new THREE.Float32BufferAttribute(uvArr, 2));
geo.setAttribute('color', new THREE.Float32BufferAttribute(colArr, 3));
geo.setIndex(idxArr);
geo.computeBoundingSphere();
```

Since we use MeshBasicMaterial, no normals needed. 

Now, `idxArr` could exceed 65535, so use `new THREE.Uint32BufferAttribute(idxArr, 1)` or just `geo.setIndex(idxArr)` which auto-detects. Three.js's `setIndex` with a plain array creates a Uint16 or Uint32 attribute based on the max value. Good.

Now the mesh:
```js
const terrainMat = new THREE.MeshBasicMaterial({ map: atlasTex, vertexColors: true, fog: true });
const terrain = new THREE.Mesh(geo, terrainMat);
scene.add(terrain);
```

Hmm — with MeshBasicMaterial and no lighting, is there any issue? No.

Now, let's also double check the color space of vertex colors. Vertex colors are used directly as linear values in the shader. My shade values are linear multipliers. Good.

Now let's write the sky, clouds, and animation.

Camera path:

```js
const camPts = [];
const N = 220;
for (let i = 0; i < N; i++) {
  const a = (i / N) * Math.PI * 2;
  const r = 36 + 17 * Math.sin(a * 2 + 0.7) + 7 * Math.cos(a * 3 - 0.4);
  const x = Math.cos(a) * r;
  const z = Math.sin(a) * r * 1.02;
  camPts.push(new THREE.Vector3(x, 0, z));
}
```
Range of r: 36 ± 24 → 12 to 60. Good, stays inside the 160-wide map (which spans -80..80 in world coords if centered).

Wait — I need to decide the world-to-scene coordinate mapping. The blocks are indexed 0..W-1 in x and z. Let's offset the mesh so the world center is at the origin: translate the geometry by (-W/2, 0, -W/2). Then x ranges -80..80.

So `heightAt(x, z)` should take world coordinates. Let me define heightAt in terms of world coordinates directly, and when generating blocks, call heightAt(x - W/2, z - W/2).

Let's do that. And the camera path uses world coordinates.

So `heightAt(wx, wz)` where wx, wz ∈ [-80, 80].

And the terrain geometry is translated by -W/2 in x and z. I'll just add the offset when building positions: `px = x - W/2`. Simpler: build positions with the offset directly.

OK.

Now the camera y: sample the terrain height at the camera's (x,z) and add clearance.

```js
function groundY(wx, wz) {
  const h = Math.floor(heightAt(wx, wz));
  return Math.max(h + 1, SEA);
}
```
Then y = groundY + clearance where clearance = 7 + 6*sin(a*3) etc.

But the terrain is voxelized so the actual surface is at floor(h)+1. Using the continuous heightAt is smoother. Let's use the continuous value for the camera path and add clearance, then smooth.

```js
const camY = [];
for (let i = 0; i < N; i++) {
  const p = camPts[i];
  const a = (i/N)*Math.PI*2;
  const g = Math.max(heightAt(p.x, p.z), SEA);
  const clear = 9 + 5.5 * Math.sin(a*3 + 1.1) + 3.5 * Math.cos(a*5 - 0.6);
  camY.push(g + clear);
}
```
Then smooth camY with a few passes of a moving average (circular).

Then set p.y = camY[i].

Then `const camCurve = new THREE.CatmullRomCurve3(camPts, true, 'catmullrom', 0.5);`

With 220 points, the curve is smooth. getPointAt(t) with arc-length parameterization (uses getUtoTmapping which builds a 200-length arc length table by default... actually `curve.getPointAt(u)` uses `getUtoTmapping` with `arcLengthDivisions` = 200 by default). Since we have 220 points, 200 divisions is a bit coarse but OK. Let's set `camCurve.arcLengthDivisions = 800;` for accuracy.

Hmm, actually with a closed curve and 220 control points, getPointAt should be fine.

Actually, `getPointAt` calls `getUtoTmapping(u)` which needs the arc lengths. Setting arcLengthDivisions higher improves accuracy. Let's set 1000.

Then:
```js
const pos = camCurve.getPointAt(t);
camera.position.copy(pos);
```

Look target:
```js
const ahead = camCurve.getPointAt((t + 0.055) % 1);
```
Hmm, 5.5% of the path ahead. The path length is roughly 2πr ≈ 2π*40 = 250 units. 5.5% = 14 units. That's a reasonable look-ahead.

But for a cinematic feel, I want the camera to look around more. Let's add an offset that varies:
```js
const lookTarget = ahead.clone();
lookTarget.x += Math.sin(t * Math.PI * 2 * 3) * 10;
lookTarget.z += Math.cos(t * Math.PI * 2 * 2.3) * 10;
lookTarget.y += Math.sin(t * Math.PI * 2 * 1.7) * 5;
```

Hmm, this could make it look at the sky or ground randomly. Let's keep the offsets modest and clamp the target's y to be above the terrain.

Actually, a nicer approach: make the look target a point that's ahead on the path but at a lower altitude, so we look slightly down at the landscape. Then add slow lateral drift.

```js
const ahead = camCurve.getPointAt((t + 0.05) % 1);
const target = new THREE.Vector3(
  ahead.x + Math.sin(t * Math.PI * 2 * 2.0) * 14,
  Math.max(ahead.y - 6, SEA + 2) + Math.sin(t * Math.PI * 2 * 1.3) * 8,
  ahead.z + Math.cos(t * Math.PI * 2 * 1.6) * 14
);
```

Then `camera.lookAt(target)` and add a slight roll.

Hmm, the roll needs to be applied after lookAt: `camera.rotateZ(roll)`.

OK.

Also, to make the motion feel smooth, use a slight easing on t? No, constant speed is fine. Actually, let's use a smoothstep-ish time warp so it speeds up and slows down. Let's keep constant for reliability.

Duration: 32 seconds per loop.

Actually, let's think about "show everything important within the first 30 seconds". The path loops around the whole world in 32s, so at 30s we're at 94% of the loop. Everything is shown. 

Hmm, but the path is a closed loop starting at a specific point. Let's make sure the start is a good vantage. The start at a=0: x = 36 + 17*sin(0.7) + 7*cos(-0.4) = 36 + 17*0.644 + 7*0.921 = 36 + 10.9 + 6.4 = 53.3, z = 0. So the camera starts at (53, y, 0) looking ahead. Fine.

Let's also make sure the lake is visible. The lake is centered at world (-34, 26) with a radius of ~44. Hmm, the lake center in world coords: I defined `const lx = x + 34, lz = z - 26;` so the basin center is at world x = -34, z = 26. Radius ~44 (in the exp, `ld = (lx²+lz²)/(44²)`, and `h -= 30*exp(-ld*1.6)`. At ld=1 (44 units), exp(-1.6) = 0.2 → -6. So the basin extends quite far.

Hmm, a 44-unit-radius lake in an 80-unit half-width world is big. Let's use 34.

Let's set: `const lx = x + 30, lz = z - 24; const ld = (lx*lx + lz*lz) / (36*36); h -= 26 * Math.exp(-ld * 1.5);`

That gives a lake centered at (-30, 24) with a radius of ~36 and a depth of up to 26. Combined with the base height (~17), the lake bottom would be at -9, clamped to 1. OK.

Hmm, actually, let's not make it too deep. Let's use a max subtraction of 20.

Alright, I'll tune it roughly and hope for the best.

Actually, I realize I should double-check the water rendering: the water surface is a single flat plane at y=15 spanning all underwater columns. If the terrain around it is at y=20, we see the lake as a flat blue surface. Good.

Let me also add a subtle "shore" — the sand blocks under/around the water. Already handled by the sand condition.

Let's now write the final code.

One more thing: performance of the block loop. W=160, H=64 → 1.6M iterations in the geometry loop. That's fine.

Actually, we can skip y values where the block is definitely not exposed. Let's just do all — 1.6M iterations with a few array lookups each. In JS that's maybe 50-200ms. Fine.

Hmm, actually the inner loop does `blocks[idx(x,y,z)]` which is a multiply and add. Then for non-air, 6 neighbor lookups. Most blocks are stone (deep), so they're non-air and get 6 lookups each. So ~1.6M * 6 = 10M lookups. That's maybe 200-500ms. Acceptable but let's optimize: skip y < h-10 for each column since faces below that depth are never exposed (neighbor height differences are at most ~10 for cliffs... could be more on steep mountains).

Safer optimization: for each column, we know the height. A block at (x,y,z) can only be exposed if some neighbor column has height < y or > y. Let's precompute min/max neighbor heights per column. Then iterate y from minNeighborH+1 to h. Actually:

Block at (x,y,z) with y <= h. It's exposed if:
- y == h (top exposed, if air/water above) 
- or any neighbor column has height < y (so the side is exposed)

Let `hmin = min(h of 4 neighbors)`. Then for y > hmin, there's at least one exposed side. So iterate y from hmin+1 to h. That covers everything. If hmin >= h, then iterate only y = h.

Great, this is a big optimization. Let me implement it.

```js
for (let z = 0; z < W; z++) {
  for (let x = 0; x < W; x++) {
    const h = heights[z*W+x];
    let hmin = h;
    if (x > 0) hmin = Math.min(hmin, heights[z*W + x-1]);
    if (x < W-1) hmin = Math.min(hmin, heights[z*W + x+1]);
    if (z > 0) hmin = Math.min(hmin, heights[(z-1)*W + x]);
    if (z < W-1) hmin = Math.min(hmin, heights[(z+1)*W + x]);
    const yStart = Math.max(0, hmin + 1);
    for (let y = yStart; y <= h; y++) { ... }
  }
}
```
Wait, but if hmin+1 > h (i.e., hmin >= h, meaning the column is a local minimum), then the loop doesn't run at all, and we'd miss the top face. Let's use `yStart = Math.max(0, Math.min(hmin + 1, h))`. Then the loop runs at least for y = h. 

Hmm, but actually if hmin = h (all neighbors equal or higher), then the top face at y=h is exposed (air above). Yes. So yStart = h works.

If hmin = h - 3, then yStart = h-2, and blocks at y = h-2, h-1, h are checked. Correct.

Good. This reduces the loop to ~2-4 iterations per column instead of ~20. 

But careful: trees add blocks above h. Those are handled in a separate pass. Let me handle trees in the same loop by using a per-column "max y" that includes tree blocks. Hmm, complicated.

Alternative: handle tree blocks in a separate pass over the list of tree blocks. Let me collect all tree blocks in a list during planting, then process them separately.

Actually, simplest: after the terrain pass, do a second pass over the tree block list, checking all 6 faces for each tree block. Tree blocks are only ~12000, so 6 lookups each = 72k. Fine.

But tree blocks adjacent to terrain: e.g., leaves next to a hill. The terrain pass wouldn't know about the leaf block (it treats it as air → emits the face). Then the leaf block pass emits its own faces toward air. The result: a face between a terrain block and a leaf block gets emitted twice? No — the terrain block emits a face if the neighbor is air or water. If the neighbor is a leaf block, it's not air/water, so no face. Good. And the leaf block emits a face if its neighbor is air/water. If the neighbor is terrain, no face. Correct.

But wait: the terrain pass runs BEFORE the trees are planted? No — I plant the trees first (modifying the blocks array), then build the geometry. So during the terrain pass, the leaf blocks are already in the array. Good. So I just need to make sure the terrain pass's y-range covers the tree blocks too.

Hmm. The tree blocks are above the terrain height h. So for a column with a tree, the block at y = h+5 (trunk) is above yStart..h. The terrain pass wouldn't process it.

Solution: maintain a per-column `topY` array = max(h, highest tree block in that column). Then iterate y from yStart to topY. But then for columns with tall trees, we'd iterate more y values (but only ~6 extra).

Let's do that: `const topY = new Int16Array(W*W)` initialized to h, and updated during tree planting: `topY[z*W+x] = Math.max(topY[z*W+x], y)`.

Hmm, but the leaves extend to x±2, z±2, so we need to update topY for those columns too. Just update topY in `setBlock`.

But `setBlock` is called during tree planting, which happens before the geometry pass. So I can update topY there.

Also, the yStart computation should use hmin from the terrain, which is fine since tree blocks are above.

Hmm, but a tree block at (x, y, z) where y > h: the face check needs neighbors. Those are handled by the generic loop. Fine.

Let me just make the loop: `for (let y = yStart; y <= topY[z*W+x]; y++)`.

Edge case: a tree on a column where the neighbor column is much taller — then the tree's side faces are against the hill and get culled. Correct.

OK.

Now let's also handle the "water" pass: for each column, if h < SEA-1, add a water top face. Actually the water blocks are at y from h+1 to SEA-1. The top face is at y=SEA. Wait, I said the water surface is at y = SEA = 15, and the topmost water block is at index SEA-1 = 14. So the top face is at y = 15.

Condition: water exists if h+1 <= SEA-1, i.e., h <= SEA-2 = 13.

So: `if (h <= SEA - 2) { addWaterTopFace(x, SEA, z) }`.

Hmm, careful: if h = 14, then the terrain top block is at y=14, its top face at y=15, which is exactly at the water level. So no water. Good.

Now let's write everything out.

Also, I should double check: `blocks` for water is set at y from h+1 to SEA-1. If h+1 > SEA-1, no water. Right.

Let me now also handle the underwater terrain color: sand. Already handled by `h <= SEA+2`.

Hmm, for h=13 (just under water), the top block is sand. Good.

Now let's write the final code.

Let me write the whole thing carefully.

```js
// ============ Noise ============
function hash2(x, y) {
  let h = Math.imul(x | 0, 374761393) + Math.imul(y | 0, 668265263);
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  h ^= h >>> 16;
  return (h >>> 0) / 4294967296;
}
```

Note: `x|0` truncates to int32. For x = 12345.67, `|0` gives 12345. But I'm calling hash2 with integer lattice coords already (Math.floor). Fine.

```js
function vnoise(x, y) {
  const xi = Math.floor(x), yi = Math.floor(y);
  const xf = x - xi, yf = y - yi;
  const u = xf * xf * (3 - 2 * xf);
  const v = yf * yf * (3 - 2 * yf);
  const a = hash2(xi, yi), b = hash2(xi + 1, yi);
  const c = hash2(xi, yi + 1), d = hash2(xi + 1, yi + 1);
  const top = a + (b - a) * u;
  const bot = c + (d - c) * u;
  return top + (bot - top) * v;
}
```

Good.

Now, the atlas drawing. Let me write it.

```js
const TILE = 16, ACOLS = 4, ASIZE = TILE * ACOLS; // 64
const acan = document.createElement('canvas');
acan.width = acan.height = ASIZE;
const actx = acan.getContext('2d');
actx.imageSmoothingEnabled = false;

function T(i) {
  const col = i % ACOLS, row = (i / ACOLS) | 0;
  return { ox: col * TILE, oy: row * TILE };
}

function px(i, x, y, c) {
  const { ox, oy } = T(i);
  actx.fillStyle = c;
  actx.fillRect(ox + x, oy + y, 1, 1);
}

function fillTile(i, c) {
  const { ox, oy } = T(i);
  actx.fillStyle = c;
  actx.fillRect(ox, oy, TILE, TILE);
}
```

Then a deterministic per-pixel random:
```js
function prand(x, y, seed) {
  let h = Math.imul(x + seed * 131, 374761393) ^ Math.imul(y + seed * 977, 668265263);
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  h ^= h >>> 16;
  return (h >>> 0) / 4294967296;
}
```

Now draw tiles:

```js
// 0 grass top
fillTile(0, '#5d9c3c');
for (let y=0;y<TILE;y++) for (let x=0;x<TILE;x++) {
  const r = prand(x,y,1);
  if (r < 0.22) px(0,x,y,'#4d8a30');
  else if (r > 0.80) px(0,x,y,'#71b84a');
  else if (r > 0.72) px(0,x,y,'#66a842');
}
```
Hmm, that's a lot of fillRect calls: 16*16 = 256 per tile * 12 tiles = 3072 fillRects. That's fine, but let me use a single ImageData approach for speed... nah, 3072 fillRects is instant.

Actually, let me reduce by only drawing ~40% of pixels. Fine.

```js
// 1 grass side
fillTile(1, '#7a5230');  // dirt base
for (...) dirt speckles
for (let y=0;y<4;y++) for (let x=0;x<TILE;x++) { px(1,x,y, green with variation) }
```
Let's make the grass strip on the top 4 rows with a jagged bottom edge.

```js
for (let x=0;x<TILE;x++){
  const depth = 3 + Math.floor(prand(x,0,7)*3); // 3..5
  for (let y=0;y<depth;y++){
    const r = prand(x,y,9);
    px(1, x, y, r<0.3 ? '#4d8a30' : (r>0.75 ? '#71b84a' : '#5d9c3c'));
  }
}
```

// 2 dirt
fillTile(2, '#7a5230'); speckles '#8b5f38' and '#684527'.

// 3 stone
fillTile(3, '#8f8f8f'); speckles '#7d7d7d', '#a0a0a0', and a few '#6f6f6f'.

// 4 snow top
fillTile(4, '#f2f7ff'); speckles '#dfe9f7', '#ffffff'.

// 5 snow side
fillTile(5, '#8f8f8f'); // stone base
then top 5 rows white-ish.

// 6 sand
fillTile(6, '#e2d5a0'); speckles '#d3c48c', '#efe3b4'.

// 7 wood side
fillTile(7, '#6b4a2b'); vertical lines darker '#54381f' at x=0,4,8,12 maybe; plus '#7d5a36' highlights.

// 8 wood top
fillTile(8, '#a8804d'); rings: draw a few concentric squares darker.

// 9 leaves
fillTile(9, '#3d7a2c'); speckles '#2f6122', '#4f9339', '#6aa84f'.

// 10 water (unused in atlas, but let's keep the layout) — actually let's use the atlas for water after all? No, separate.
Let's use tile 10 for a "gravel/rock" and 11 for "dark stone". Eh, keep it simple, only use 0-9.

Now the water texture (separate 32x32):
```js
const wcan = document.createElement('canvas');
wcan.width = wcan.height = 32;
const wctx = wcan.getContext('2d');
wctx.fillStyle = '#2f6fb8'; wctx.fillRect(0,0,32,32);
// wave lines
for (let y=0;y<32;y++) for (let x=0;x<32;x++){
  const r = prand(x,y,42);
  if (r < 0.10) wctx.fillStyle='#3d82cc', fillRect...
}
```
Plus some horizontal wave streaks.

Since we animate the offset, the texture should tile seamlessly. With random pixels it won't tile, but the seams will be subtle. Let's make it tile by using a periodic function. Actually, with random pixels it's fine — the seam is just one row/column.

Hmm, actually if the texture doesn't tile, we'll see a visible seam line moving across. Let's make it tile by using a hash that wraps: use `prand(x % 32, y % 32, ...)` — that's what it is. The seam issue is that pixel (31,y) and (0,y) are unrelated, creating a visible discontinuity. With a mostly uniform blue texture, it's not noticeable. But the "wave lines" would be cut.

Let's use a sinusoidal wave pattern which naturally tiles:
```js
for (let y=0;y<32;y++) for (let x=0;x<32;x++){
  const v = Math.sin((x/32)*Math.PI*2*2 + (y/32)*Math.PI*2) * 0.5 + 0.5;
  ...
}
```
Hmm, that's more of a gradient than pixel art.

Let's do: base blue, plus horizontal lighter streaks at y = 0, 8, 16, 24 with a sine-based x offset. Since it's 32 px and the pattern repeats every 8 rows, it tiles vertically. Horizontally, if the streak is uniform along x, it tiles.

```js
wctx.fillStyle = '#2a6cb4'; wctx.fillRect(0,0,32,32);
for (let y=0;y<32;y++){
  for (let x=0;x<32;x++){
    const w = Math.sin((x*0.5 + y*1.7)) ;  // hmm, doesn't tile
  }
}
```

Simplest tileable approach: use a sum of sines with integer frequencies:
```js
const val = Math.sin(x/32*Math.PI*4) * Math.cos(y/32*Math.PI*4);
```
This tiles with period 32. 

```js
for (let y=0;y<32;y++) for (let x=0;x<32;x++){
  const s = Math.sin(x*Math.PI*4/32) * Math.cos(y*Math.PI*4/32)
          + Math.sin((x+y)*Math.PI*2/32) * 0.6;
  const t = Math.max(0, Math.min(1, s*0.5 + 0.5));
  // blend between two blues
}
```
Then quantize to a few levels for a pixel-art look. And draw with fillRect per pixel. 1024 fillRects — fine.

Colors: dark #2a6cb4 → light #4a94d8.

OK, that's decent.

Actually, since the water is semi-transparent over the terrain, the texture detail matters less. Fine.

Now, let me write the whole file.

One more consideration: the `renderer.setSize` and resize handler.

```js
addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});
```

Animation loop with the timestamp:
```js
let startTime = -1;
function animate(now) {
  requestAnimationFrame(animate);
  if (startTime < 0) startTime = now;
  const t = (now - startTime) / 1000;
  ...
}
requestAnimationFrame(animate);
```

Use `now` from requestAnimationFrame for all animation (requirement: "Use the requestAnimationFrame timestamp for animation time").

For the clouds, I need dt. I'll compute dt from the timestamp difference.

OK, writing it all now.

Let me also double-check the sky sphere following the camera: `sky.position.copy(camera.position)` each frame. Since the sky sphere has radius 3000 and the camera far is 6000, it's fine.

Hmm, but the sphere is centered on the camera, so the gradient direction (vDir = position, i.e., local position) works correctly — the local position direction is the view direction. Good.

Also, `depthWrite: false` and the sphere is rendered... it should render first. Set `sky.renderOrder = -1` and `material.depthTest = false`? If depthTest is false and it renders first, everything draws over it. Let's set depthWrite: false, depthTest: false, renderOrder: -1. Hmm, but with depthTest false and renderOrder -1, it draws first and everything else covers it. That works.

Actually, with a radius of 3000 and camera far 6000, depth testing would work fine anyway. Let's keep depthTest true and depthWrite false, renderOrder -1. Hmm, if depthTest is true and the sphere is at distance 3000, and terrain is at distance < 300, the terrain passes the depth test. Fine.

But the sky sphere is rendered first (renderOrder -1), writes color but not depth. Then the terrain renders over it. Good.

Hmm, one problem: with depthWrite false and renderOrder -1, the sky is drawn, then the terrain. But the terrain has transparent objects too (water). Order: opaque objects (sorted by renderOrder then material), then transparent. The sky is opaque-ish (transparent: false), so it's in the opaque list with renderOrder -1 → drawn first. Good.

OK.

Let's also add a subtle sun glow sprite? The shader handles it.

Let me write out the code now.

Actually one more thought on the fog and the sky: the fog color should match the sky's horizon color for a seamless horizon. FogExp2 color 0xbcd6ee and the sky horizon 0xbcd6ee. Good.

Let me write.

```js
import * as THREE from 'three';

// ---------------------------------------------------------------- renderer
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const FOG_COLOR = new THREE.Color(0xbcd6ee);
scene.fog = new THREE.FogExp2(FOG_COLOR, 0.0062);

const camera = new THREE.PerspectiveCamera(62, window.innerWidth / window.innerHeight, 0.1, 8000);
```

Now, let's write the terrain constants and functions.

I'll write it all out now in the final answer. Let me be careful with the details.

For the tree planting, I need `topY` and `setBlock`.

Let me write the terrain generation function:

```js
const W = 160, H = 64;
const SEA = 15;
const SNOW_LINE = 36;
const ROCK_LINE = 29;

const AIR=0, GRASS=1, DIRT=2, STONE=3, SAND=4, SNOW=5, WOOD=6, LEAF=7, WATER=8;

const blocks = new Uint8Array(W*H*W);
const heights = new Int16Array(W*W);
const topY = new Int16Array(W*W);
const idx = (x,y,z) => (y*W + z)*W + x;
```

Wait, `idx` as an arrow function called millions of times — fine, V8 inlines it. But let's use a regular function declaration for clarity.

Generation:

```js
function generateWorld() {
  for (let z = 0; z < W; z++) {
    for (let x = 0; x < W; x++) {
      const wx = x - W/2, wz = z - W/2;
      let hf = heightAt(wx, wz);
      let h = Math.floor(hf);
      if (h < 1) h = 1;
      if (h > H - 4) h = H - 4;
      heights[z*W+x] = h;
      topY[z*W+x] = h;

      for (let y = 0; y <= h; y++) {
        let t;
        if (y === h) {
          if (h <= SEA + 2) t = SAND;
          else if (h >= SNOW_LINE) t = SNOW;
          else if (h >= ROCK_LINE) t = STONE;
          else t = GRASS;
        } else if (y > h - 4) {
          if (h <= SEA + 2) t = SAND;
          else if (h >= ROCK_LINE) t = STONE;
          else t = DIRT;
        } else {
          t = STONE;
        }
        blocks[idx(x,y,z)] = t;
      }
      for (let y = h+1; y < SEA; y++) blocks[idx(x,y,z)] = WATER;
    }
  }
  // ... trees
}
```

Hmm wait, `h <= SEA+2` = h <= 17. So for a beach column with h=17, the top block is sand at y=17, and the surface is at y=18. Water at 15. So there's a 3-block sand cliff from the water. Hmm, that's fine for a beach.

Actually let me reconsider: the beach should slope gently. With the noise, the terrain near the water will have h around 14-18, so a gentle slope. Good.

Now the trees. Also need to avoid trees on sand.

```js
  const treeList = [];
  for (let z = 4; z < W-4; z++) {
    for (let x = 4; x < W-4; x++) {
      const h = heights[z*W+x];
      if (h <= SEA + 3) continue;
      if (h >= ROCK_LINE) continue;
      const dens = fbm((x-W/2)*0.035 + 300, (z-W/2)*0.035 - 200, 2);
      if (dens < 0.52) continue;
      if (rand() > 0.05) continue;
      let ok = true;
      for (let i = 0; i < treeList.length; i++) {
        const t = treeList[i];
        const dx = t.x - x, dz = t.z - z;
        if (dx*dx + dz*dz < 30) { ok = false; break; }
      }
      if (!ok) continue;
      treeList.push({x, z, h});
    }
  }
```

Hmm, the fbm with 2 octaves at frequency 0.035 gives a patchy forest distribution. dens < 0.52 → about 55% is forest. And rand() > 0.05 → 5% of those. So 2.75% of eligible columns. That's a LOT of trees (25600 * 0.5 * 0.0275 ≈ 350 before spacing). With spacing (dx²+dz² < 30 → distance < 5.5), we'd get maybe 250 trees. OK.

Each tree: trunk 5 + leaves ~30 = 35 blocks. 250 * 35 = 8750 blocks. Fine.

Let's write the tree planting:

```js
  for (const t of treeList) {
    const { x, z, h } = t;
    const th = 4 + Math.floor(rand() * 3);
    const top = h + th;
    for (let i = 1; i <= th; i++) setBlock(x, h + i, z, WOOD);
    for (let dy = -2; dy <= 1; dy++) {
      const r = dy <= -1 ? 2 : 1;
      for (let dx = -r; dx <= r; dx++) {
        for (let dz = -r; dz <= r; dz++) {
          if (r === 2 && Math.abs(dx) === 2 && Math.abs(dz) === 2) continue;
          if (r === 2 && (Math.abs(dx) === 2 || Math.abs(dz) === 2) && rand() < 0.4) continue;
          setBlock(x+dx, top+dy, z+dz, LEAF);
        }
      }
    }
    setBlock(x, top+2, z, LEAF);
  }
```

where setBlock only writes if the target is AIR:
```js
function setBlock(x, y, z, t) {
  if (x < 0 || x >= W || y < 0 || y >= H || z < 0 || z >= W) return;
  const i = idx(x,y,z);
  if (blocks[i] !== AIR) return;
  blocks[i] = t;
  if (y > topY[z*W+x]) topY[z*W+x] = y;
}
```

Good.

Now the geometry pass. Let me write it.

```js
const FACE_DEF = [
  { n: [1,0,0],  sh: 0.80, c: [[1,0,1],[1,0,0],[1,1,0],[1,1,1]], uv: [[0,0],[1,0],[1,1],[0,1]] },
  { n: [-1,0,0], sh: 0.55, c: [[0,0,0],[0,0,1],[0,1,1],[0,1,0]], uv: [[0,0],[1,0],[1,1],[0,1]] },
  { n: [0,1,0],  sh: 1.00, c: [[0,1,0],[0,1,1],[1,1,1],[1,1,0]], uv: [[0,1],[0,0],[1,0],[1,1]] },
  { n: [0,-1,0], sh: 0.35, c: [[0,0,1],[0,0,0],[1,0,0],[1,0,1]], uv: [[0,0],[1,0],[1,1],[0,1]] },
  { n: [0,0,1],  sh: 0.52, c: [[0,0,1],[1,0,1],[1,1,1],[0,1,1]], uv: [[0,0],[1,0],[1,1],[0,1]] },
  { n: [0,0,-1], sh: 0.75, c: [[1,0,0],[0,0,0],[0,1,0],[1,1,0]], uv: [[0,0],[1,0],[1,1],[0,1]] },
];
```

UV computation:
```js
const INSET = 0.25 / TILE; // in tile units -> 0.015625
function tileUV(tile) {
  const col = tile % ACOLS, row = (tile / ACOLS) | 0;
  const u0 = (col + INSET) / ACOLS;
  const u1 = (col + 1 - INSET) / ACOLS;
  const v1 = 1 - (row + INSET) / ACOLS;
  const v0 = 1 - (row + 1 - INSET) / ACOLS;
  return { u0, u1, v0, v1 };
}
```

Then for a face, the uv for corner k with (cu, cv):
u = u0 + cu*(u1-u0)
v = v0 + cv*(v1-v0)

Now, the main loop:

```js
const pos = [], uvs = [], cols = [], inds = [];
let vcount = 0;

function emitFace(x, y, z, f, tile, tint) {
  const def = FACE_DEF[f];
  const { u0, u1, v0, v1 } = tileUV(tile);
  const base = vcount;
  for (let k = 0; k < 4; k++) {
    const c = def.c[k];
    pos.push(x + c[0], y + c[1], z + c[2]);
    const cu = def.uv[k][0], cv = def.uv[k][1];
    uvs.push(u0 + cu*(u1-u0), v0 + cv*(v1-v0));
    const s = def.sh * tint;
    cols.push(s, s, s);
  }
  inds.push(base, base+1, base+2, base, base+2, base+3);
  vcount += 4;
}
```

Note: the positions need the world offset (-W/2). I'll apply the offset by translating the geometry after building: `geo.translate(-W/2, 0, -W/2)`. 

Now the main loop:

```js
for (let z = 0; z < W; z++) {
  for (let x = 0; x < W; x++) {
    const ci = z*W + x;
    const h = heights[ci];
    const ty = topY[ci];
    let hmin = h;
    if (x > 0) hmin = Math.min(hmin, heights[ci-1]);
    if (x < W-1) hmin = Math.min(hmin, heights[ci+1]);
    if (z > 0) hmin = Math.min(hmin, heights[ci-W]);
    if (z < W-1) hmin = Math.min(hmin, heights[ci+W]);
    let yStart = hmin + 1;
    if (yStart > h) yStart = h;
    if (yStart < 0) yStart = 0;

    for (let y = yStart; y <= ty; y++) {
      const t = blocks[idx(x,y,z)];
      if (t === AIR || t === WATER) continue;
      const tiles = TILE_FOR[t];
      const tint = 0.93 + hash2(x*7 + y*13, z*11 + y*3) * 0.14;
      for (let f = 0; f < 6; f++) {
        const nx = x + FACE_DEF[f].n[0];
        const ny = y + FACE_DEF[f].n[1];
        const nz = z + FACE_DEF[f].n[2];
        if (nx < 0 || nx >= W || nz < 0 || nz >= W || ny < 0 || ny >= H) continue;
        const nt = blocks[idx(nx,ny,nz)];
        if (nt !== AIR && nt !== WATER) continue;
        const tile = f === 2 ? tiles.top : (f === 3 ? tiles.bottom : tiles.side);
        emitFace(x, y, z, f, tile, tint);
      }
    }
  }
}
```

Hmm, `hash2(x*7 + y*13, z*11 + y*3)` — for the tint. This gives a per-block value. Fine.

Wait, there's a bug: for tree blocks above the terrain, `yStart` is based on terrain but the loop goes to `ty` which includes tree blocks. So tree blocks below yStart won't be processed... but tree blocks are always above h, and yStart <= h. So tree blocks are always >= h+1 > yStart. Fine.

Hmm, unless hmin+1 > h... no, we clamp yStart to <= h. And tree blocks are at y > h. So all good.

Now the water pass:

```js
const wpos = [], wuv = [], wcol = [], wind = [];
let wvc = 0;
for (let z = 0; z < W; z++) {
  for (let x = 0; x < W; x++) {
    const h = heights[z*W+x];
    if (h > SEA - 2) continue;
    // top face at y = SEA
    const y = SEA;
    const base = wvc;
    const corners = [[0,y,0],[0,y,1],[1,y,1],[1,y,0]];
    const uvco = [[0,1],[0,0],[1,0],[1,1]];
    for (let k=0;k<4;k++){
      wpos.push(x+corners[k][0], corners[k][1], z+corners[k][2]);
      wuv.push(uvco[k][0], uvco[k][1]);
      wcol.push(1,1,1);
    }
    wind.push(base,base+1,base+2, base,base+2,base+3);
    wvc += 4;
  }
}
```

Hmm, I want the water UVs to repeat a few times per block for a finer look. Let's use uv scaled by 0.5 (half a texture per block) or 1. Since we animate the offset, using 0..1 per block with an offset animation means each block shows a shifted window. Let's use uv * 0.5 so the texture appears at 2x scale... Actually, let's just use 0..1 and a texture that's 32x32 → 32 texels per block. That's quite fine. Let's use uv range 0..0.5 so the texture appears at 2 blocks per tile... hmm, with RepeatWrapping, uv 0..0.5 samples half the texture per block. That makes it look larger. Let's use uv 0..1 → 1 texture tile per block. That's a 32px texture over a 1-unit block. Fine.

OK.

Also, the water vertex colors: 1.0. Maybe vary slightly.

Now let's assemble.

Actually, hold on. I should double check the water top face winding gives an upward normal. From the +Y face def: c = [[0,1,0],[0,1,1],[1,1,1],[1,1,0]] with y=SEA. Yes, that's what I have. Good.

Now let's put the geometry together and create meshes.

Now the clouds. Let me write:

```js
const cloudGroup = new THREE.Group();
scene.add(cloudGroup);

const cloudBoxes = [];   // {cx,cy,cz, ox,oy,oz, sx,sy,sz}
const clouds = [];       // {x,y,z,speed}
```

I'll use an InstancedMesh with count = cloudBoxes.length.

Per frame:
```js
for (const c of clouds) {
  c.x += c.speed * dt;
  if (c.x > 300) c.x -= 600;
}
for (let i = 0; i < cloudBoxes.length; i++) {
  const b = cloudBoxes[i];
  const c = clouds[b.ci];
  dummy.position.set(c.x + b.ox, c.y + b.oy, c.z + b.oz);
  dummy.scale.set(b.sx, b.sy, b.sz);
  dummy.updateMatrix();
  cloudMesh.setMatrixAt(i, dummy.matrix);
}
cloudMesh.instanceMatrix.needsUpdate = true;
```

Hmm, the clouds don't rotate, so I could precompute the local matrix (scale+offset) and then just multiply by a translation. But `dummy.position.set` + `updateMatrix` is fine.

Actually, `dummy.scale.set` + `dummy.position.set` + `updateMatrix()` composes the matrix. Fine.

Note: 350 instances * (matrix compose + setMatrixAt) per frame. setMatrixAt copies 16 floats. ~5600 float copies. Negligible.

Hmm, one issue: the clouds are spread over ±300 in x and z, but the fog will hide distant ones. With fog density 0.0062, at 300 units: 1-exp(-(0.0062*300)²) = 1-exp(-3.46) = 0.97. So they're nearly invisible. Let's spread them over ±220 instead. Or reduce the fog for clouds... The fog applies to clouds too (fog: true). Let's keep the spread at ±250 and the clouds at y=75-95.

Hmm, at ±250 with fog 0.97, they'd be invisible. Let's spread over ±180 and put more of them.

Actually, let's think: the camera is at the world center, radius ~40. Clouds at ±180 in x/z, at y~85. The distance from the camera is sqrt(180² + 60²) ≈ 190. Fog at 190: 1-exp(-(0.0062*190)²) = 1-exp(-1.39) = 0.75. So they're 75% faded. Hmm.

Let's reduce the fog density to 0.0045. At 190: 1-exp(-0.73) = 0.52. Better. At 100: 1-exp(-0.2) = 0.18. Good.

Hmm, but then distant terrain (100-150 units) is only 30-50% fogged, and the map edge at ~110 from the center would be visible. 

Trade-off. Let's use 0.0055 and spread the clouds over ±160.

Actually, since the clouds are big and fluffy, having them fade in the distance is fine and natural.

Let's use fog density 0.0055 and clouds over ±170.

Alright, let's also handle: the cloud group should probably be positioned so that the drift wraps seamlessly. If clouds are spread over x ∈ [-170, 170] and I wrap at x > 170 → x -= 340, then a cloud jumps from +170 to -170, which is far away and heavily fogged. Fine.

OK.

Now the camera path and animation.

Let me write the full path code.

```js
const camPts = [];
const NPT = 240;
for (let i = 0; i < NPT; i++) {
  const a = (i / NPT) * Math.PI * 2;
  const r = 34 + 16 * Math.sin(a * 2 + 0.7) + 6 * Math.cos(a * 3 - 0.4);
  camPts.push(new THREE.Vector3(Math.cos(a) * r, 0, Math.sin(a) * r));
}
```

Wait, `r` could go as low as 34-22 = 12 and as high as 56. The world spans -80..80. So r=56 keeps us inside. Good.

Then compute y:
```js
const ys = [];
for (let i = 0; i < NPT; i++) {
  const p = camPts[i];
  const a = (i / NPT) * Math.PI * 2;
  const g = Math.max(heightAt(p.x, p.z), SEA);
  ys.push(g + 10 + 6 * Math.sin(a * 3 + 1.2) + 4 * Math.cos(a * 5 - 0.7));
}
// smooth
for (let pass = 0; pass < 6; pass++) {
  const out = ys.slice();
  for (let i = 0; i < NPT; i++) {
    const p = (i - 1 + NPT) % NPT, n = (i + 1) % NPT;
    out[i] = (ys[p] + ys[i] * 2 + ys[n]) / 4;
  }
  for (let i = 0; i < NPT; i++) ys[i] = out[i];
}
for (let i = 0; i < NPT; i++) camPts[i].y = ys[i];
```

Hmm, smoothing 6 passes with a 3-tap filter. The circular smoothing will reduce the amplitude. It should be fine.

But there's a problem: smoothing might lower the y below the terrain in places. Let's after smoothing, clamp: `ys[i] = Math.max(ys[i], maxTerrainY + 4)`. Hmm, that reintroduces sharp changes.

Alternative: compute the required clearance profile and smooth that, then add to the terrain height. But the terrain height itself is bumpy.

Let's do this: 
```js
const clear = [];
for (i) clear[i] = 10 + 6*sin(a*3+1.2) + 4*cos(a*5-0.7);
// smooth clear
for (i) ys[i] = Math.max(heightAt(p.x,p.z), SEA) + clear[i];
```
The terrain height is continuous, so the path is continuous. The smoothing of `clear` makes it gentle. The terrain height variations along the path could be large (up to 20 units over a short distance), causing jerky camera motion. Hmm.

Better: smooth the final `ys` but then add a safety clamp:
```js
for (let pass = 0; pass < 8; pass++) { ...smooth... }
for (let i = 0; i < NPT; i++) {
  const p = camPts[i];
  const minY = Math.max(heightAt(p.x, p.z), SEA) + 5;
  ys[i] = Math.max(ys[i], minY);
}
// smooth again lightly
```

Actually, since the path radius r varies and the terrain varies, let's just use a generous clearance (10-18) so we rarely hit terrain. With a max terrain height of ~46 (mountains) and the camera path at r=12-56... the path might go right over a mountain.

Hmm. Let's compute the terrain height along the path and add a clearance of 12-20. Then the camera flies 12-20 units above the terrain, which for a voxel world at scale 1 is quite high (12 blocks). That's fine — it gives a good overview.

Actually, "flies over and between the hills" suggests lower altitudes. Let's use a clearance of 6-14 and do the smoothing + clamp.

Let me do:
1. Compute `base[i] = max(heightAt, SEA)`.
2. Smooth base heavily (many passes) → `smoothBase`. This gives a smooth "valley floor" following the terrain.
3. `ys[i] = smoothBase[i] + clearance[i]` where clearance[i] = 8 + 5*sin(...) smoothed a bit.

But smoothing the base could make it lower than the actual terrain at peaks → the camera would clip into a hill. Then clamp: `ys[i] = max(ys[i], base[i] + 5)`.

Hmm, the clamp reintroduces bumpiness at the peaks but only where needed.

Alternatively, use a max-filter instead of an average: `smoothBase[i] = max over a window`. That guarantees ys >= actual terrain. Let's do a max filter with a window of ±8 samples (out of 240 → about ±12% of the path... hmm, that's a big window, 30 units of path length).

Let's do a window of ±6 samples. The path length is ~2π*40 ≈ 250, so each sample is ~1 unit. A ±6 window = ±6 units of path. Then a max filter, then a light smoothing.

Actually, let's simplify: 
```js
ys[i] = base[i] + clearance[i]
```
then apply a few passes of a "max-preserving" smoothing: `ys[i] = max(smoothed, base[i] + 5)`. 

Let's do: smooth 5 passes, then clamp to `base[i] + 6`, then smooth 2 more passes but only in the downward direction... ugh.

Simplest reliable approach: use a large clearance so clipping never happens.

```js
ys[i] = base[i] + 9 + 6*sin(a*3+1.2) + 4*cos(a*5-0.7);
```
Range: 9 ± 10 → -1 to 19. Hmm, negative clearance.

Let's use `ys[i] = base[i] + 11 + 5*sin(a*3+1.2) + 3*cos(a*5-0.7)` → clearance 3..19.

Then smooth the whole ys with 4 passes and clamp: `ys[i] = max(ys[i], base[i] + 3.5)`.

With 4 passes of the 3-tap filter, the high-frequency terrain variations get smoothed out, and the clamp handles the rest. The result should be reasonably smooth.

Hmm, but the smoothing with a 3-tap filter over 4 passes only spreads over ±4 samples. The terrain along the path varies at the scale of the terrain features (10-20 units), so 4 samples isn't much smoothing.

Let's use more passes, like 20, which spreads over ±20 samples = ±20 units. That's a good amount of smoothing. But then the amplitude of the terrain-following is reduced (it becomes more like an average), and the clamp kicks in more often.

I think a combination works: 20 passes of smoothing + clamp. Let's try.

Actually, you know what — the visual result matters more than perfect smoothness. Even if the camera has some vertical variation, that's fine for a flythrough over hills. Let's use 8 passes + clamp.

Let me just do:
```js
// ys computed
for (let pass = 0; pass < 10; pass++) {
  const o = ys.slice();
  for (let i = 0; i < NPT; i++) {
    const p = (i - 1 + NPT) % NPT, n = (i + 1) % NPT;
    o[i] = (ys[p] + 2*ys[i] + ys[n]) * 0.25;
  }
  for (let i = 0; i < NPT; i++) ys[i] = o[i];
}
for (let i = 0; i < NPT; i++) {
  const p = camPts[i];
  const need = Math.max(heightAt(p.x, p.z), SEA) + 6;
  if (ys[i] < need) ys[i] = need;
}
```

OK, good enough.

Then create the curve:
```js
const camCurve = new THREE.CatmullRomCurve3(camPts, true, 'catmullrom', 0.5);
camCurve.arcLengthDivisions = 1200;
```

Now, one more concern: `getPointAt` on a closed CatmullRomCurve3 with 240 points — the `getUtoTmapping` builds the arc-length table lazily on first call. Fine.

Now, the animation:

```js
const DURATION = 34;
let prevTime = 0;
let elapsed = 0;

function animate(now) {
  requestAnimationFrame(animate);
  const tSec = now * 0.001;
  const dt = Math.min(0.05, prevTime ? tSec - prevTime : 0.016);
  prevTime = tSec;
  elapsed += dt;

  const u = (elapsed / DURATION) % 1;

  // camera
  const p = camCurve.getPointAt(u);
  camera.position.copy(p);
  const ahead = camCurve.getPointAt((u + 0.045) % 1);
  const look = ahead.clone();
  look.x += Math.sin(u * Math.PI * 2 * 2.0) * 12;
  look.z += Math.cos(u * Math.PI * 2 * 1.5) * 12;
  look.y = Math.max(look.y - 5, SEA + 3) + Math.sin(u * Math.PI * 2 * 1.2) * 6;
  camera.lookAt(look);
  camera.rotateZ(Math.sin(u * Math.PI * 2 * 1.5) * 0.05);

  // clouds
  ...
  
  // water texture scroll
  waterTex.offset.x = elapsed * 0.02;
  waterTex.offset.y = elapsed * 0.008;

  // sky follows
  sky.position.copy(camera.position);

  renderer.render(scene, camera);
}
```

Hmm, `camera.lookAt(look)` then `camera.rotateZ(...)` — rotateZ rotates in local space, which applies a roll. Good.

Wait, there's an issue: `look.y` — I set it based on `ahead.y` which is the curve's y. Let me just do:

```js
const look = new THREE.Vector3(
  ahead.x + Math.sin(u * 6.28 * 2) * 14,
  ahead.y - 4 + Math.sin(u * 6.28 * 1.3) * 7,
  ahead.z + Math.cos(u * 6.28 * 1.6) * 14
);
```
And ensure `look.y` is at least SEA+3 so we don't look at the ground too much. Eh, looking down at the ground is fine and cinematic.

Hmm, but if the camera looks down too much, we lose the sky/sun. Let's keep it moderate.

Let's use:
```js
look.y = ahead.y - 3 + Math.sin(u*6.28*1.3)*5;
```

And the lateral offsets of ±14 give a nice "looking around" feel.

Hmm, but if the look target is offset by 14 laterally while the ahead point is only ~11 units away (0.045 * 250), then the camera could look sideways/backwards. Let's reduce the lateral offsets to ±8 and increase the look-ahead to 0.07 (17 units).

Actually, "looking around the landscape" — some sideways looking is good. Let's use a look-ahead of 0.06 and lateral offsets of ±10.

OK.

Now, one more thing: the initial frame. `elapsed` starts at 0 and u=0. Good.

Also, I should make sure the first 30 seconds show the landscape well. The path is a full loop in 34s, so at 30s we've seen 88% of it. 

Let's set DURATION = 30 so the full loop completes within the recording window. Hmm, but then it loops at 30s. That's fine — "it may loop or continue after that".

Let's use DURATION = 32.

Alright. Let me also add a subtle vignette or color grade? No, keep it simple.

Let me finalize and write the code.

One last check on the atlas: ACOLS = 4, TILE = 16, ASIZE = 64.

Tiles used: 0 (grass top), 1 (grass side), 2 (dirt), 3 (stone), 4 (snow top), 5 (snow side), 6 (sand), 7 (wood side), 8 (wood top), 9 (leaves). All within 0-15. Good.

Let me write the drawing code for each tile now.

```js
function prand(x, y, s) {
  let h = Math.imul(x + s * 131, 374761393) ^ Math.imul(y + s * 977, 668265263);
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  h ^= h >>> 16;
  return (h >>> 0) / 4294967296;
}
```

Tile 0 — grass top:
```js
fillTile(0, '#5d9c3c');
for (let y = 0; y < 16; y++) for (let x = 0; x < 16; x++) {
  const r = prand(x, y, 1);
  if (r < 0.18) px(0, x, y, '#4a8530');
  else if (r > 0.86) px(0, x, y, '#77c04e');
  else if (r > 0.70) px(0, x, y, '#68ad44');
}
```

Tile 1 — grass side:
```js
fillTile(1, '#7d5636');
for (let y = 0; y < 16; y++) for (let x = 0; x < 16; x++) {
  const r = prand(x, y, 2);
  if (r < 0.2) px(1, x, y, '#6a4629');
  else if (r > 0.85) px(1, x, y, '#8d6440');
}
for (let x = 0; x < 16; x++) {
  const d = 3 + Math.floor(prand(x, 0, 3) * 3);
  for (let y = 0; y < d; y++) {
    const r = prand(x, y, 4);
    px(1, x, y, r < 0.25 ? '#4a8530' : (r > 0.8 ? '#77c04e' : '#5d9c3c'));
  }
}
```

Tile 2 — dirt:
```js
fillTile(2, '#7d5636');
for (...) speckles
```

Tile 3 — stone:
```js
fillTile(3, '#909090');
speckles: '#7c7c7c' (r<0.25), '#a4a4a4' (r>0.82), '#6e6e6e' (r>0.94)
```

Tile 4 — snow top:
```js
fillTile(4, '#f4f8ff');
speckles: '#e2ecf9' (r<0.3), '#ffffff' (r>0.7)
```

Tile 5 — snow side:
```js
fillTile(5, '#909090');  // stone
stone speckles
top 5 rows: snow with a jagged bottom
for (let x=0;x<16;x++){
  const d = 4 + Math.floor(prand(x,1,6)*3);
  for (let y=0;y<d;y++) px(5,x,y, prand(x,y,7)<0.3 ? '#e2ecf9' : '#f4f8ff');
}
```

Tile 6 — sand:
```js
fillTile(6, '#e3d6a2');
speckles '#d2c48b' (r<0.28), '#f0e5bb' (r>0.8)
```

Tile 7 — wood side:
```js
fillTile(7, '#6d4c2b');
for (let y=0;y<16;y++) for (let x=0;x<16;x++){
  const r = prand(x,y,8);
  if (r < 0.12) px(7,x,y,'#5a3d21');
  else if (r > 0.88) px(7,x,y,'#7d5a36');
}
// vertical grain
for (let x = 0; x < 16; x += 5) {
  for (let y = 0; y < 16; y++) px(7, x, y, '#563a1f');
}
```
Hmm, x=0,5,10,15. OK.

Tile 8 — wood top:
```js
fillTile(8, '#b08a55');
// rings
for (let y=0;y<16;y++) for (let x=0;x<16;x++){
  const dx = x - 7.5, dy = y - 7.5;
  const d = Math.sqrt(dx*dx+dy*dy);
  const ring = Math.sin(d * 1.9) ;
  if (ring > 0.4) px(8,x,y,'#9a7645');
  else if (ring < -0.5) px(8,x,y,'#c39a62');
}
```
Something like that.

Tile 9 — leaves:
```js
fillTile(9, '#3d7a2c');
for (...) {
  const r = prand(x,y,10);
  if (r < 0.22) px(9,x,y,'#2e5f21');
  else if (r > 0.84) px(9,x,y,'#4f9339');
  else if (r > 0.65) px(9,x,y,'#356e26');
}
```

OK.

Now let's write the water texture.

```js
const wcan = document.createElement('canvas');
wcan.width = wcan.height = 32;
const wctx = wcan.getContext('2d');
for (let y = 0; y < 32; y++) {
  for (let x = 0; x < 32; x++) {
    const s = Math.sin(x * Math.PI * 2 / 16) * 0.5 + Math.cos(y * Math.PI * 2 / 16) * 0.5
            + Math.sin((x + y) * Math.PI * 2 / 32) * 0.4;
    const v = Math.max(0, Math.min(1, s * 0.4 + 0.5));
    const r = Math.round(40 + v * 40);
    const g = Math.round(105 + v * 60);
    const b = Math.round(180 + v * 50);
    wctx.fillStyle = `rgb(${r},${g},${b})`;
    wctx.fillRect(x, y, 1, 1);
  }
}
```
That's 1024 fillRects — fine.

Hmm, `x * Math.PI * 2 / 16` has period 16 in x, and the texture is 32 wide, so it repeats twice. Good, it tiles.

Now, the water material:
```js
const waterTex = new THREE.CanvasTexture(wcan);
waterTex.wrapS = waterTex.wrapT = THREE.RepeatWrapping;
waterTex.magFilter = THREE.NearestFilter;
waterTex.minFilter = THREE.LinearMipmapLinearFilter;
waterTex.colorSpace = THREE.SRGBColorSpace;
```
Hmm, mixing nearest mag with linear mip is fine.

Actually with `generateMipmaps` default true and a power-of-two texture (32x32), mipmaps work. Good.

Water material:
```js
new THREE.MeshBasicMaterial({
  map: waterTex, transparent: true, opacity: 0.72,
  depthWrite: false, fog: true, color: 0xa8d8ff
})
```

Hmm, the color multiplies. Let's use 0xffffff so the texture color shows.

Actually, to make the water read better, let's use color 0x8fc4f0 and opacity 0.75.

OK.

Let's now write everything out.

One thing I should double check — `renderer.setSize` and the canvas. Also, `document.body` styling.

Let me write the final HTML.

Also: should I add a loading indicator? The generation takes maybe 1-2 seconds. The page would be blank/white during that. Let's add a simple loading overlay that's removed after generation. Actually, the generation happens synchronously on load, so the browser would show a white page. Let's add an overlay div that we remove after the first frame. But since the generation is synchronous before the first render, the overlay wouldn't even paint. Hmm.

To make it paint, I'd need to defer the generation with a setTimeout. Let's do:
```js
requestAnimationFrame(() => {
  setTimeout(init, 0);
});
```
Meh. Let's just do it synchronously; the white flash is acceptable. Actually, let me add the overlay and use a `setTimeout(init, 50)` so the overlay paints first. That's a nice touch.

Hmm, but then the animation starts after. Fine.

Actually, let's keep it simple and synchronous. The build is probably < 1s.

Hmm, 160x160x64 = 1.6M block writes plus the geometry pass. Let's estimate: the block fill loop is 160*160*20 ≈ 512k writes. The geometry pass is 25600 columns * ~4 y-values * 6 faces = 614k face checks. Plus the water pass. Total maybe 2-3M operations. Should be ~100-300ms. Fine.

Let's go with synchronous.

Actually, I realize I should double check one thing: `new THREE.Float32BufferAttribute(pos, 3)` where pos is a regular JS array with ~1M elements. That's fine.

Let me write the final code.

Let me reconsider the number of faces. 25600 columns. With the optimized loop, we process y from yStart to topY. For flat terrain, that's ~1-2 y values per column. For each, 6 face checks. So ~25600*2*6 = 307k checks. Plus the emit. Reasonable.

But actually, wait: for each column we check 6 faces for each y in the range. For a column with yStart = h (flat), we check 6 faces for 1 block. The top face is emitted (if air above). The 4 side faces: neighbors have the same height h, so the neighbor block at the same y exists → not air → no face. Bottom face: the block below exists → no face. So 1 face per column → 25600 top faces. Plus sides where heights differ.

Total faces: maybe 25600 + 25600*2 = 77k. Vertices: 308k. That's fine.

Let me now write out the complete file.

Actually, hold on. I want to double check the `yStart` optimization doesn't miss faces. Consider a column with h=10 and a neighbor with h=20 (a tall wall). hmin for this column = min over neighbors. If another neighbor has h=5, then hmin=5, yStart=6. So we process y=6..10. The block at y=10 has a side face toward the h=5 neighbor? No — the neighbor with h=5 has its top block at y=5, so at y=6..10 the neighbor is air. So yes, the block at (x, 10, z) has a side face toward that neighbor. ✓. And the block at y=6 also has a side face. ✓.

And for the neighbor with h=20: the block at (x,10,z) is against a solid block at y=10 → no face. ✓.

Good.

What about the bottom face of a block at y = hmin+1? Below it at y=hmin, the block exists (since the column is solid from 0 to h). So no face. ✓

What if hmin = 0 (a very low neighbor)? Then yStart = 1, and the block at y=1's bottom face at y=0... the neighbor column at y=0 has a block (all columns have at least y=0 filled since h>=1). So no face. ✓

Edge case: what if a column has h < hmin? Then yStart = h, and we only process y=h. Correct, since the sides are all buried.

Great.

Now let me write it all out.

Let me also handle: `if (y > h)` for tree blocks — those are above the terrain, so their neighbors below are the trunk/terrain. Fine.

Final code writing time.

Actually, one thing about the tint hash: `hash2(x*7 + y*13, z*11 + y*3)`. For large x,y,z this could produce collisions but that's fine. Actually, let me use a better hash:
```js
const tv = prand(x, z, y) // hmm
```
Let's just use `hash2(x * 3 + y * 91, z * 7 + y * 53)`. Fine.

Hmm, hash2 takes ints. `x*3 + y*91` is an int. Good.

Let me write.

Also, I should ensure `Math.imul` receives integers — `x|0` handles that.

Alright, writing the final answer now.

For the sky colors, let me pick:
- Top: 0x2a6bc9 (deeper blue)
- Horizon: 0xc3dcf2 (pale)
- Bottom: 0x7d9cc0

Sun direction: normalize(0.45, 0.62, -0.65).

Fog color: 0xc3dcf2 (match the horizon).

Hmm, the fog color should be a bit lighter/whiter near the horizon. 0xc3dcf2 is good.

Let's write.

Oh wait, one thing: `scene.fog = new THREE.FogExp2(color, density)` — the color is stored as a THREE.Color in linear working space. And the sky shader's uHorizon is also a linear color. So they match. ✓

Let me write the final file.

Actually, let me reconsider the fog density once more. With FogExp2 density d, the fog factor is 1 - exp(-(d*dist)^2).

d = 0.0055:
- 50 units: 1-exp(-0.0756) = 0.073
- 100: 1-exp(-0.3025) = 0.26
- 150: 1-exp(-0.68) = 0.49
- 200: 1-exp(-1.21) = 0.70

That's a nice soft fog. At 150 units things are half-faded. Good.

The world spans -80..80, so from the center the edge is 80-113 units. With fog at 0.26-0.49 at that distance, the edge is visible but hazy. Combined with the camera being off-center and looking across, the far edge might be at 150+ units → 50% fog. Hmm, the edge of the world would be somewhat visible.

To hide it, I could extend the terrain beyond 160... or increase the fog. Let's use d = 0.0075:
- 50: 0.13
- 100: 0.43
- 150: 0.72
- 200: 0.90

Hmm, that's pretty hazy. But it hides the world edge well. Let's compromise: d = 0.0065.
- 50: 0.10
- 100: 0.34
- 150: 0.62
- 200: 0.84

OK, let's use 0.0065. And clouds within ±150.

Actually, since the camera flies at r = 12-56 from the center, when it's at r=12 looking outward, the far edge is at 92-130 units. With fog 0.30-0.52 there, the edge is somewhat visible but hazy. Acceptable — it reads as "distance haze".

Also, at the world edge, the terrain just ends with a vertical cliff face (no faces emitted since OOB is treated as opaque... wait, no: for OOB I `continue`, meaning no face is emitted, so you'd see through the terrain into... nothing (the sky). Hmm. That's bad — you'd see a hole.

Let me instead treat OOB as AIR (emit the face), creating a wall of faces at the edges. That's better than a hole. Actually, emitting faces means you see the terrain's side wall from outside. From inside the map, you'd see the wall's back faces which are culled (backface culling) → you'd see through!

Hmm. So from inside the map looking at the edge, you'd see through the terrain (backface culled) into the sky/void. That's a hole.

Hmm, but the terrain at the edge is only ~20 blocks tall, and the camera is inside. Looking toward the edge, you see the terrain surface receding to the edge, and then... the far side of the edge wall is facing away, so it's culled. But you'd be looking at the top surface of the terrain, which continues to the edge and then stops. Beyond it, you'd see the sky/fog. Since the terrain is at y~20 and the camera is at y~35, looking down at the edge, you'd see the last row of terrain and then... the void below.

Actually no — from above, looking down at the edge, you see the top faces of the terrain up to the boundary, and beyond the boundary you'd see the sky (or whatever is behind). Since the terrain slopes down at the edges (usually), and there's fog, it should be OK-ish.

Hmm, but if the terrain is high at the edge, you'd see a sharp cut.

Better solution: make the terrain height fall off toward the edges so the map boundary is underwater or low. I.e., add an edge falloff: as you approach the map boundary, lower the terrain toward the sea level or below.

```js
// edge falloff
const ex = Math.abs(wx) / (W/2), ez = Math.abs(wz) / (W/2);
const e = Math.max(ex, ez);
if (e > 0.72) {
  const k = smoothstep(0.72, 1.0, e);
  h = h * (1-k) + (SEA - 6) * k;
}
```

This makes the terrain sink below sea level near the edges, so the world is surrounded by water. Then the water surface extends to the edge, and beyond it is fog. That's much nicer — an island!

But wait, the water plane is only emitted for columns with h < SEA-1. At the edges, h would be ~SEA-6 = 9, so water is emitted there. And the water extends to the map edge. Beyond the map edge, you'd see... the water plane ends. But the water is at y=15 and the camera is above, so you'd see the water surface ending and then the void/sky beyond.

Hmm, still a cut, but the water plane is flat and the fog will hide the far edge. With the fog at 0.5+ at 100+ units, and the water extending to 80 units from the center... 

Actually, the camera is at r=12-56. The nearest map edge could be as close as 24 units if the camera is at r=56. Then the edge would be very visible.

Hmm. Let me reduce the camera's radius range: r = 30 + 12*sin(...) + 5*cos(...) → 13 to 47. Then the nearest edge is 33 units away. Still visible.

Alternative: make the world bigger. W = 192? That's 192*192*64 = 2.36M blocks. The face count would be ~1.4x of 160. Build time ~1.5x. Probably still fine.

Hmm, but 192 wide with a camera at r=13-47 means the edges are 49-83 units away. With fog at 0.25-0.55 there. Better.

Actually, let's think about it differently: the "sea" at the edges plus fog is a natural-looking horizon. A flat water plane extending to the horizon looks like an ocean. The only issue is the hard cut at the map edge where the water stops.

Solution: extend the water plane beyond the map edges! Just emit water quads for a larger area (e.g., 40 units beyond the map on each side). Then the water extends to a distance where the fog fully hides it.

Yes! Let's do that. In the water pass, iterate over a range from -MARGIN to W+MARGIN, and for columns outside the map, treat the height as -100 (so water is always emitted). Then the water extends MARGIN units beyond the map in all directions.

With MARGIN = 60, the water extends from -60 to W+60. From the camera, the far edge of the water is at least 60 units away in the worst case, and typically much more. With fog at 0.10 at 50 units... hmm, 60 units gives fog 0.14. Not enough.

Let's use MARGIN = 120. Then the water extends 120 units beyond the map, and the fog at 120 units is 0.52, at 180 is 0.79. Hmm, still visible.

The water plane at y=15, viewed from the camera at y=30-45, at a horizontal distance of 150, the angle below horizontal is small (atan(20/150) = 7.6°). So the water would appear near the horizon, where the fog is densest in terms of screen space... no, the fog depends on distance, not screen position.

Hmm, the issue is the water plane's far edge at 150 units would be at fog 0.79 — 79% blended with the fog color. The fog color is a pale blue, and the water is blue. So the edge would be barely visible. 

And beyond the water edge, we'd see the sky, which near the horizon is the same pale blue. So the transition would be nearly invisible!

So: MARGIN = 120, and the water fades into the fog/sky. 

But that's a lot of extra water quads. The map is 160x160 = 25600 columns; adding 120 margin on each side → 400x400 = 160000 columns. That's 6x more water quads. 160k quads = 640k vertices. Hmm, that's a lot but manageable.

Optimization: only emit water for columns outside the map where the distance from the center is less than some radius, or just accept it. Actually, we could use larger quads for the outer water. Let's build the outer water as a few large quads instead of per-column quads.

Simplest: add 4 large quads (or one big ring) at y=15.001 covering the area from the map edge out to ±300. Since the water is flat and the texture repeats, a few big quads work fine.

Let's do: 
- The map water (per-column) covers the map area.
- Outer water: 4 big quads forming a frame from -M to W+M, excluding the inner W x W region.

Actually, just make one huge quad from -300 to W+300 in x and z, at y = SEA - 0.001 (slightly below the map water to avoid z-fighting). Wait, but then it would render over the terrain where the terrain is above sea level. Hmm, no — the terrain above sea level is at y > 15, so a water quad at y=15 would be below the terrain surface. Depth testing would handle it: the terrain occludes the water. But the water is transparent with depthWrite false, and it's drawn after the opaque terrain. So the water would be drawn on top of the terrain pixels where it passes the depth test.

Since the water is at y=15 and the terrain is at y>15, the terrain is closer to the camera (if the camera is above)... no, not necessarily. Depth is measured along the view ray. A terrain surface at y=20 and a water plane at y=15 — the water plane is behind (farther) than the terrain surface along the view ray if looking down at the terrain. So the depth test would reject the water. ✓

But there's a catch: the water is transparent and drawn after the opaque pass, so the depth buffer already contains the terrain depth. The water at y=15 would fail the depth test where the terrain is in front. ✓

So a single huge quad at y=15 works, as long as the terrain is above it. Where the terrain is below y=15 (underwater), the water quad is in front, and it renders. ✓

So: just one big quad! From -400 to W+400 in both x and z, at y = SEA. But then it overlaps the per-column water quads. Let's just use the big quad for everything and skip the per-column water.

Wait, but the per-column water quads are at exactly y=15 too. Z-fighting. So let's just use ONE big quad for all the water. 

But: with one big quad, the UV mapping would need to repeat a lot. With a 32x32 texture and RepeatWrapping, uv from 0 to 800 would repeat 800 times. That's fine (with mipmapping, it'll be a blur at distance). Let's set the UV to cover the whole quad with a reasonable repeat: uv = (x/4, z/4) so the texture repeats every 4 units. Over 800 units, that's 200 repeats. With mipmaps, the distant water becomes a uniform blue. Good.

Hmm, but a single quad of 800x800 units with a repeating texture at a grazing angle → heavy aliasing. Mipmaps help. And the fog helps.

Actually, let's use a grid of, say, 32x32 quads over the 800x800 area to get better vertex-level... no, the texture is the same. Mipmapping handles it.

Hmm, but with a single quad, the interpolation of UV across a huge quad is linear, which is fine for a planar surface. Anisotropic filtering would help. Let's set `waterTex.anisotropy = renderer.capabilities.getMaxAnisotropy()`.

OK, decision: ONE big water quad.

Wait, but there's an issue: the water quad at y=15 covers the entire world, including areas where the terrain is above sea level. Those areas are hidden by the terrain (depth test). ✓. But what about the areas where the terrain is between... no, it's fine.

Hmm, but there's another issue: transparency sorting. The water quad is a single transparent object. It renders after opaque. Where the terrain is above y=15, the terrain writes depth, and the water fails the depth test. ✓

And where the terrain is below y=15, the water is drawn over it with blending. ✓

Great, one quad it is.

But hold on — the water quad at y=15 will also be drawn over the beach at exactly y=15? The sand surface at h=14 is at y=15. Z-fighting! Let's offset the water to y=15.02 to avoid z-fighting. Or set the sand to h<=13 for underwater... Let's just put the water at y = 15.05. Hmm, that would create a small gap at the shoreline. Negligible visually.

Actually, the water plane at y=15 and the terrain top surface at y=15 (for h=14): coplanar → z-fighting. Let's put the water at y=15.5? That's a visible offset. Let's use y=15.08.

Hmm, actually the "sand" condition is h <= SEA+2 = 17, so h=14 gives sand, and the surface is at y=15. Water at y=15.05 would be 0.05 above. That's fine and avoids z-fighting.

Hmm, but a 0.05 gap at the shoreline — the water edge would be visible as a thin sliver. Actually no, the water covers the whole area, so at the shoreline where the terrain rises above y=15.05, the water is hidden. At h=14 (surface y=15), the water at 15.05 covers it. So the water surface is 0.05 above the sand. Visually invisible.

OK, use y = SEA + 0.06 = 15.06.

Hmm, wait. Actually let's reconsider: the water block tops are at y=SEA=15 in my terrain model, and the water plane is at 15.06. It's consistent.

Let's just use a big quad at y = SEA + 0.05, spanning -400 to W+400.

Actually, one problem: the water quad is huge (800x800), and the fog is applied per-fragment based on distance. That's fine.

Another problem: the water quad's UV. Let me set uv = (worldX / 3, worldZ / 3) so the texture repeats every 3 units. Over 800 units, that's 267 repeats. Fine.

Hmm, but with `NearestFilter` on magnification, near the camera the water looks pixelated (good), and far away it's mipmapped.

OK, let's do it.

Also, the water color should be a bit darker in deep areas... not easily done with a flat quad. Skip.

Now, one more consideration: with the water covering the whole world, the areas where the terrain is above sea level are unaffected. ✓

Alright, let's write it.

Also, since we no longer need per-column water quads, we skip that pass entirely. 

And the water blocks in the `blocks` array are still needed for the face-culling logic (so the terrain under water emits its faces). Actually, we want the terrain under the water to emit faces (so you can see the lake bottom). With water as a neighbor, we emit the face. ✓

Hmm, but do we want the underwater terrain faces emitted? Yes, so you can see the sand under the water through the transparency. ✓

OK, writing now.

Let me write the complete file.

One more: the `MARGIN` for water — let's use 300 so the water spans -300..460. Actually the world is 0..160 in block coords, centered at -80..80. Let me just make the water quad centered at the origin with a size of 1200x1200. That's plenty.

uv = (worldX/3, worldZ/3) with the quad's vertices at ±600.

OK.

Final code:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Voxel World — Cinematic Flythrough</title>
<style>
  html, body { margin: 0; height: 100%; overflow: hidden; background: #bcd6ee; }
  canvas { display: block; }
</style>
</head>
<body>
<script type="module">
import * as THREE from 'three';
... 
</script>
</body>
</html>
```

Let me write the whole thing.

I'll be careful about the order of declarations (functions hoisted, const not).

Let me draft the full script:

```js
import * as THREE from 'three';

/* ---------------- Renderer / scene ---------------- */
const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const FOG_COLOR = new THREE.Color(0xc3dcf2);
scene.fog = new THREE.FogExp2(FOG_COLOR, 0.0065);

const camera = new THREE.PerspectiveCamera(62, window.innerWidth / window.innerHeight, 0.1, 8000);

/* ---------------- Noise ---------------- */
function hash2(x, y) { ... }
function vnoise(x, y) { ... }
function fbm(x, y, oct) { ... }
function smoothstep(a, b, x) { ... }

/* ---------------- Atlas ---------------- */
...

/* ---------------- World ---------------- */
const W = 160, H = 64;
const SEA = 15;
...

/* ---------------- Build ---------------- */
...

/* ---------------- Animation ---------------- */
...
</script>
```

Alright, let me write it all out properly now.

For the sky sphere I need the sun direction:
```js
const sunDir = new THREE.Vector3(0.42, 0.58, -0.70).normalize();
```

Now writing the final answer.

Wait, one detail on `hash2`: I use `Math.imul(x|0, ...)`. If x is large (like x*3+y*91 for x,y up to 160), that's up to ~15000, fine.

Also `prand` for the atlas uses small values.

OK, writing.

Actually, I realize the `TILE_FOR` lookup with an object and computed keys — let me just use a plain array indexed by block type.

```js
const TILE_TOP = [0, 0, 2, 3, 6, 4, 8, 9, 0];  // index by block type
const TILE_SIDE = [0, 1, 2, 3, 6, 5, 7, 9, 0];
const TILE_BOT = [0, 2, 2, 3, 6, 3, 8, 9, 0];
```
Index 0 = AIR (unused), 1 = GRASS, 2 = DIRT, 3 = STONE, 4 = SAND, 5 = SNOW, 6 = WOOD, 7 = LEAF, 8 = WATER.

Good.

Now writing the final file for real.

Let me carefully write the animate function and make sure everything is defined before use.

I'll structure it as:
1. Constants and helpers
2. Atlas creation
3. World generation
4. Geometry building
5. Scene objects (terrain, water, sky, clouds)
6. Camera path
7. Animation

Let me write it.

For the clouds, I need a `dummy` Object3D.

```js
const dummy = new THREE.Object3D();
```

And the cloud InstancedMesh:
```js
const cloudGeo = new THREE.BoxGeometry(1, 1, 1);
const cshade = [0.86, 0.80, 1.0, 0.68, 0.92, 0.84];
const carr = new Float32Array(24 * 3);
for (let f = 0; f < 6; f++) {
  for (let v = 0; v < 4; v++) {
    const i = (f * 4 + v) * 3;
    carr[i] = carr[i + 1] = carr[i + 2] = cshade[f];
  }
}
cloudGeo.setAttribute('color', new THREE.BufferAttribute(carr, 3));
```

Then:
```js
const cloudMat = new THREE.MeshBasicMaterial({ color: 0xffffff, vertexColors: true, fog: true });
const cloudMesh = new THREE.InstancedMesh(cloudGeo, cloudMat, cloudBoxes.length);
cloudMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
cloudMesh.frustumCulled = false;
scene.add(cloudMesh);
```

Setting frustumCulled = false avoids bounding-sphere issues with dynamic instances.

OK.

Now, the final animation loop.

Let me write everything.

One more consideration on the sky: since it's a sphere of radius 3000 centered on the camera, and the camera far is 8000, it's fine.

Writing now.

Let me also double check: `THREE.FogExp2(color, density)` — yes.

Let me write out the final code.

Actually, one more: for the terrain material, should I use `side: THREE.FrontSide`? Yes, default. Our winding is correct.

Let me now write.

I'll also add `geo.computeBoundingSphere()`.

Final code:

(Note: I need to make sure `heightAt` is defined before it's used in world generation and the camera path.)

Let me write it.

For the edge falloff, let me add it to heightAt:

```js
function heightAt(wx, wz) {
  const e = fbm(wx * 0.013 + 40, wz * 0.013 - 17, 4);
  let h = SEA + (e - 0.40) * 26;

  const m = fbm(wx * 0.0065 - 90, wz * 0.0065 + 55, 3);
  const mm = smoothstep(0.50, 0.68, m);
  const rn = fbm(wx * 0.026 + 7, wz * 0.026 + 3, 3);
  const ridge = 1 - Math.abs(2 * rn - 1);
  h += mm * ridge * 40;

  // lake
  const lx = wx + 30, lz = wz - 24;
  const ld = (lx * lx + lz * lz) / (36 * 36);
  h -= 22 * Math.exp(-ld * 1.5);

  // edge falloff toward the map borders
  const ex = Math.abs(wx) / (W / 2);
  const ez = Math.abs(wz) / (W / 2);
  const edge = Math.max(ex, ez);
  const k = smoothstep(0.62, 1.0, edge);
  h = h * (1 - k) + (SEA - 8) * k;

  return h;
}
```

Hmm, `W` is defined after `heightAt` in my code layout? I need to make sure `W` is a const declared before `heightAt` is called (not before it's defined, since function declarations are hoisted but the const is in TDZ). Since `heightAt` is only called during world generation (after all consts are defined), it's fine.

Edge falloff: at edge=0.62 (i.e., |wx| = 49.6), the falloff starts; at edge=1.0 (|wx| = 80), h = SEA-8 = 7. So the terrain drops to below sea level near the borders. Good — the world becomes an island surrounded by ocean.

But the lake at (-30, 24) and the edge falloff might interact. It's fine.

Now, the max height: base up to SEA + 0.35*26 = 24, plus mountains up to 40 → 64. That exceeds H-4 = 60. The clamp handles it (h = min(h, 60)).

Hmm, 60 is quite tall. The camera path at r=13-47 might fly near a mountain. The path's y = max(heightAt, SEA) + clearance. Since it follows the terrain, it'll fly over the mountains. Fine.

But if the camera flies at y = 46+11 = 57, that's near the world top. Fine.

OK. Let's write it.

Actually, let me reduce the mountain height a bit: `h += mm * ridge * 34;` → max 24+34 = 58. Still high. Let's keep 34 and clamp at 58.

Snow line at 36, rock line at 29.

Alright, writing the final answer now.

One more: the `heights` array is used for the water/beach conditions. Since heightAt now includes the edge falloff, the borders will be underwater. Good.

Let me write it all out.

Actually, regarding tree placement: with the edge falloff, the borders are underwater, so trees won't spawn there (h <= SEA+3 check). Good.

Writing the final file.

Let me write the complete code now, carefully.

```js
// ============================================================
//  Voxel World — cinematic flythrough
// ============================================================
import * as THREE from 'three';

// ---------- renderer ----------
const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const FOG_COLOR = new THREE.Color(0xc3dcf2);
scene.fog = new THREE.FogExp2(FOG_COLOR, 0.0065);

const camera = new THREE.PerspectiveCamera(62, window.innerWidth / window.innerHeight, 0.1, 8000);

// ---------- math helpers ----------
function hash2(x, y) {
  let h = Math.imul(x | 0, 374761393) + Math.imul(y | 0, 668265263);
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  h ^= h >>> 16;
  return (h >>> 0) / 4294967296;
}
function vnoise(x, y) {
  const xi = Math.floor(x), yi = Math.floor(y);
  const xf = x - xi, yf = y - yi;
  const u = xf * xf * (3 - 2 * xf);
  const v = yf * yf * (3 - 2 * yf);
  const a = hash2(xi, yi), b = hash2(xi + 1, yi);
  const c = hash2(xi, yi + 1), d = hash2(xi + 1, yi + 1);
  const t0 = a + (b - a) * u;
  const t1 = c + (d - c) * u;
  return t0 + (t1 - t0) * v;
}
function fbm(x, y, oct) {
  let amp = 1, f = 1, sum = 0, norm = 0;
  for (let i = 0; i < oct; i++) {
    sum += amp * vnoise(x * f, y * f);
    norm += amp;
    amp *= 0.5; f *= 2;
  }
  return sum / norm;
}
function smoothstep(a, b, x) {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
}
```

Wait, there's a bug: `hash2(xi, yi)` where xi could be a huge number if x is large. In fbm, x = wx * 0.013 * f where wx ∈ [-80, 80] and f up to 8 → x ∈ [-8.3, 8.3]. Fine.

For the mountain mask: wx * 0.0065 * 4 (oct 3 → f up to 4) → ±2. Fine.

OK.

Now the atlas.

I'll write it all out in the final answer. Let me be thorough.

Let me now actually produce the final file.

Also I should double check `prand` usage in the atlas — I'll define a local helper.

Let me write.

Final check on the water quad: 
```js
const waterGeo = new THREE.PlaneGeometry(1400, 1400, 1, 1);
waterGeo.rotateX(-Math.PI / 2);
waterGeo.translate(0, SEA + 0.05, 0);
```
But the UVs from PlaneGeometry are 0..1. I need to scale them so the texture repeats. Let me modify the uv attribute:

```js
const uvAttr = waterGeo.attributes.uv;
for (let i = 0; i < uvAttr.count; i++) {
  uvAttr.setXY(i, uvAttr.getX(i) * 350, uvAttr.getY(i) * 350);
}
```
With a 1400x1400 plane and uv 0..350, the texture repeats every 4 units. Good.

Wait, PlaneGeometry rotated -90° about X: the plane's local +Y becomes -Z (or +Z). The UVs map to the plane's local coordinates. Fine.

Also, the water plane's normal after rotation is +Y. With MeshBasicMaterial, the normal doesn't matter, but the winding does for backface culling. After `rotateX(-PI/2)`, the plane faces +Y. ✓

OK.

Also, `waterGeo.translate(0, SEA+0.05, 0)` — but the plane is centered at the origin, and the world is centered at the origin too (after the -W/2 offset). ✓

Alright. Writing the final answer.

Oh, one more thing: with a 1400x1400 water plane and a 32x32 texture repeated 350 times, at the far distance the texture will be a blur. With mipmaps and anisotropy it should look like a soft blue. Good.

Actually, let me reconsider the repeat: 350 repeats over 1400 units = 4 units per repeat. With a 32px texture over 4 units, that's 8 texels per unit. That's quite dense. Near the camera, the water would look like fine noise. Let's use 2 units per repeat → 700 repeats. Hmm, even denser.

Let's use 8 units per repeat → 175 repeats. That gives 4 texels per unit. Reasonable.

I'll set uv scale = 1400/8 = 175.

OK, writing.

Let me finally write the whole thing.

Actually, let me reconsider the number of blocks for performance once more. W=160, H=64. The blocks array is 160*64*160 = 1,638,400 bytes = 1.6MB. Fine.

Let's go.

One last thing: I should verify the terrain generation loop bounds. `for (let y = 0; y <= h; y++)` where h can be up to 58. And H=64, so idx(x, 58, z) is valid. ✓

And the water fill: `for (let y = h+1; y < SEA; y++)` → up to y=14. ✓

OK, writing the final answer now.

Let me write out the complete HTML.

I'll also add a small "loading" fade-in? No, keep it simple.

Writing.