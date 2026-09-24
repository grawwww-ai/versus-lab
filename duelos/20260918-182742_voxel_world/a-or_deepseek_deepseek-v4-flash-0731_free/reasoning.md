This is a complex Three.js project. Let me break down the requirements:

1. **Minecraft-style voxel world** with:
   - Procedurally generated terrain (at least 128x128 columns)
   - Layered noise for terrain generation
   - Grass-topped hills, snowy mountain peaks, sandy beaches, lake/sea with semi-transparent water
   - Trees (wood + leaf blocks)

2. **Visual requirements**:
   - Per-face shading (different brightness per face so cubes read clearly)
   - Procedurally drawn pixel-art textures on canvas
   - Sky with sun, soft distance fog, fluffy block clouds that drift
   - Use InstancedMesh or merged geometry for performance

3. **Camera**:
   - Flies automatically on a smooth path looking around
   - Uses requestAnimationFrame timestamp
   - Full-window canvas with resize handling
   - No interaction needed

Let me plan this out:

**Terrain Generation:**
- Use a heightmap from layered noise (simplex or perlin noise)
- 128x128+ columns, maybe 256x256 for better visuals
- Height ranges: determine biome by height
  - Deep water: sand bottom
  - Beach: sand blocks
  - Grass: grass blocks
  - Hills: grass with stone, then snow at high altitude

Actually, let me simplify: Use noise for height, then based on height:
- Below sea level - 1: sand (underwater)
- Sea level: sand/beach
- Above: grass
- High altitude: stone with snow on top

**Textures:**
- Create canvas textures for: grass block (different top/side/bottom), dirt, stone, sand, snow, wood side/top, leaves, water
- Per-face shading: darker on sides, brightest on top, etc.

**Clouds:**
- Simple white cubes at high altitude, maybe using instanced mesh

**Trees:**
- Wood trunk + leaf blocks (like Minecraft oak trees)

**Performance:**
- Use InstancedMesh for blocks
- Only render visible faces (don't render interior faces)
- Actually, with InstancedMesh, we'd need to create one mesh for each block type, but that's tricky with per-face textures.

Wait, in Minecraft, each block face has different textures. For a custom voxel engine with Three.js, a common approach is:

**Option A**: Use a single geometry per chunk, with per-face vertex colors for shading, and a texture atlas. But for InstancedMesh, each instance has a single matrix, and we can't easily have different face textures.

**Option B**: For each block type, create an InstancedMesh with a BoxGeometry that has the appropriate textures per face. But then we'd need multiple meshes (one per block type) - that's fine. Use a texture atlas with different materials per block face, but InstancedMesh only supports one material per mesh.

Actually, the cleanest approach: Use a custom shader or a BoxGeometry with vertex colors for per-face shading, and a texture atlas. For InstancedMesh, we can pass per-instance data like which block type and use a shader to sample the correct atlas region.

But that's complex. Let me think of a simpler approach.

**Simpler approach**: Since we want a flythrough, not necessarily voxel editing, we can afford to create a scene graph of chunk meshes, each chunk being a merged BufferGeometry. We can generate a texture atlas containing all block textures, and build a geometry with UV coordinates pointing to the correct atlas regions for each face of each block. Use per-face shading via vertex colors or geometry normal-based coloring.

Actually, the simplest with Three.js r186:

- Create a texture atlas (canvas) with all block textures.
- For each block type, define which face uses which part of the atlas.
- For each chunk (e.g., 16x16 columns, world height ~64), create a BufferGeometry.
- For each visible block position, add 4 vertices per face (or triangles) with the correct UVs from the atlas and face shading baked into vertex colors.
- Merge all into a single BufferGeometry per chunk, then use one material (MeshLambertMaterial with map and vertexColors) to render.

This is efficient and handles per-face shading.

But given complexity in generating this code from scratch, maybe we can use InstancedMesh with multiple materials. Let me reconsider.

With InstancedMesh, we can create separate meshes for each block type. That means each cube is a BoxGeometry with 6 materials (or a material array for the 6 faces). For a given block type, all blocks look the same (same texture on each face). We can predefine the 6 material array per block type. For each block type, create one InstancedMesh.

This is simpler but less optimized: we're rendering 6 faces even for interior faces, and each block is a full cube. However, the requirement says "InstancedMesh or merged geometry" - InstancedMesh is acceptable. We'll hide interior faces? Actually, with InstancedMesh we can't easily per-instance disable faces, but we can still render all cubes. For a 128x128 world with height ~10-20, that's ~1 million blocks. InstancedMesh with 1M instances might be heavy but doable if we cull chunks? Actually, rendering 1M cubes at once even with instancing is a lot.

Let me think: if we create a world of 128x128 columns with average height 10, that's ~160k blocks. With InstancedMesh per block type, we'd render up to 160k instances. That's actually fine for WebGL. But wait, each block has 6 faces = 12 triangles per cube = ~2M triangles. InstancedMesh draws each instance as a full cube (12 triangles). 160k instances * 12 triangles = 1.9M triangles. That's okay for a modern GPU.

However, we'd need separate InstancedMesh per block type (grass, dirt, stone, sand, wood, leaves, water, snow, etc.). For each block type we'd set an instance matrix for each block of that type. That's manageable.

But there's a subtlety: when rendering a full cube with InstancedMesh, you can't hide internal faces. For the surface, only the top faces of blocks beneath are visible. If we render all blocks including interior ones, we'd be drawing hidden geometry, causing the "swimming in blocks" issue but performance-wise still okay for moderate worlds. But to avoid z-fighting or seeing through blocks, we need to have depth writing. It'll work but may be inefficient.

Actually, a common technique is to only place blocks at the surface (i.e., only blocks that have a non-air neighbor? No, that's for face culling). If we only place surface blocks (not interior), the world would look hollow. But we need solid ground. So we need to render interior blocks unless we implement face culling.

I think using merged geometry with per-face culling is the right approach. But that's more complex to code. However, the requirement says "Use InstancedMesh or merged geometry so it runs smoothly." It doesn't say we must hide interior faces. We can use InstancedMesh and render only the topmost blocks? Wait, if you fly through the landscape you'd see grass on top, and if you dip down you'd see through the ground. But the camera flies above ground mostly.

Actually, to "run smoothly", we should not render hidden faces. Let me implement a chunk-based approach with mesh merging and face culling. That's the proper way but takes more code.

Given the time to write this from scratch, maybe I can do a middle ground: use merged geometry but only generate visible faces (the 3 exposed faces of a cube if we only top surface, but for hills we need sides). Actually, a typical voxel engine only generates the faces that border air. For terrain, that's just the surface. Surface of a heightmap is O(n^2) not O(n^3). So for each column, we only create blocks and faces along the surface. That's much better. Let me do that: for each x,z column, compute the terrain height from noise. Only the top block in each column is visible (and side blocks up to the top). Under the surface, there's dirt/stone but they're hidden; we don't need to render them because they're not visible. When you look at a mountain, you see the sides, so we need blocks at the surface. The sides of a hill are partially exposed. So we need to render blocks that have at least one face exposed to air. A block is exposed if any of its 4 horizontal neighbors' terrain height is lower than this block's height, or if the sky direction neighbor is empty. Since we only have one block per column, we can compute visibility based on the heightmap.

Let me refine: For each column (x,z), terrain height h. If h > 0, then a block of some material exists at y=h. Also, might we need blocks below y=h? If the terrain is a solid mass, then the sides of hills expose cross-sections. For example, if a column is high (mountain) and its neighbor is low, the side of the mountain has a vertical face from y=low to y=high. So we need blocks at each level up to h for exposed faces. Thus the number of blocks can be more than 1 per column; it's up to the max height difference.

Simpler: For each column, the surface is defined by the heightmap. We can iterate over all blocks in the vertical range and create only those blocks whose 6 neighbors are not all present. But since terrain is a heightmap (single height per column), the only blocks we need are those that form the surface envelope. All blocks below the local height but above the neighbor's height are exposed on the side.

Let me implement a simple culling: For each column, for y from 1 to h[x][z], we add a cube at (x,y,z) if any of the 6 neighbors at height y is empty (i.e., y > neighbor_height). But that's O(height) per column. For 128x128 columns with average height 15, that's 245k blocks. That's fine.

Actually, for a heightmap, the visible blocks are exactly the ones where the 4-neighbor height is < current y. So we can just iterate y from 0 to h and if for any of the four horizontal directions neighbor_h < y, then the block at (x,y,z) is visible on that side. For the top, the top face is visible if y == h, obviously. The bottom face is never visible (since terrain is solid down to 0). So we add cubes for all y from 1 to h that are on the surface envelope. But this duplicates blocks: if a column is at height 10 and all neighbors are at height 10, then only y=10 is visible (top). But if a neighbor is 8, then y=9 and y=10 are exposed at the side. So we need y=9 and y=10.

So total block count is roughly surface area * (1 + sidelength/2)? Actually, worst-case with cliffs it could be O(h*area). For 128x128 with max height 30, that's 500k blocks. Fine.

Now, for materials: The material at a column depends on height and biome:
- If height < sea_level - 1: sand (underwater)
- If height == sea_level - 1 or sand
- If height > snow_level: stone with snow on top
- Else grass (top, dirt below) ... but wait, if we have a heightmap, the material for a column is constant along y. But grass top should only be at the very top; sides should be dirt if exposed. Since we only render surface blocks, a block at y=h is the top, and blocks y< h on exposed sides are the interior of the column (dirt/stone). So the material for each block is determined by its depth from the surface, not global y.

Actually, if we generate the world as a 3D array, then we can determine materials properly. Let's do a simple generation: We'll have noise for height. Then for each column, fill down from height to 1:
- Top block (y==h): if h < sand_level: sand else if h > snow_level: grass_block (or podzol?) else grass_block
- Below top 3 layers: dirt
- Below that: stone
But for surface rendering, we only display a fraction of those blocks. However, when a side is exposed, the visible face is a cross-section of the column, so the material should show dirt/stone layers. Thus when building visible blocks, we need to know the material at that y depth.

So let's generate a 3D array or compute on the fly:
- h[x][z] = terrain height
- material at (x,y,z) for y <= h[x][z]:
   if y == h: surface material (depends on h)
   else if y > h - 4: dirt
   else: stone
   and if h < sea_level: sand (or gravel) fill? Actually, under water bottom should be sand.
   if h > snow_level: top is snow, and sub-top is stone? Typically snowy mountain: near top, surface is stone with snow cover; below a few blocks is stone.

Let me define:
- sea_level = 12 (say)
- sand_level = sea_level + 1? Actually beach at sea level.
- snow_level = 30
- If h < sea_level - 1: material sand (underwater sand)
- If h == sea_level - 1: sand (beach)
- If h >= snow_level: stone (rock) with snow on top if y == h else stone
- Else: grass (top) / dirt (subsurface) / stone (deep)

For above sea level:
- If y == h: grass (or snow/stone) top
- else if h - y < 4: dirt
- else: stone

For below sea level, the top might be sand, and under it sand/dirt/stone.

This becomes complex. Let's simplify by using specified biomes:
- Lowlands: sand near sea, grass on top
- Mid: grass/dirt
- High: stone/snow

Let me define:
- sea_level = 15
- function getMaterial(x,y,z,h)
- if y <= 0 or y > h: air
- if h < sea_level - 1: sand (all underwater)
- if h < sea_level + 1: sand (beach) when y == h? Actually sand for beach and under water.
- if h > snow_level (say 40): 
   if y == h: snow block (or snow layer)
   else: stone
- else:
   if y == h: grass block
   else if h - y <= 3: dirt
   else: stone

This gives variety.

Now for textures:
We need to draw pixel-art style textures on a canvas. We'll create a texture atlas or separate materials.

Since I'm going to use per-face shading, I can assign vertex colors based on face normal (top brighter, sides darker). That gives 3D readability.

For the textures, I'll create a canvas per texture (grass_top, grass_side, dirt, stone, sand, snow, wood_side, leaves, water). They can be 16x16 pixels, upscaled. Pixel-art style.

Actually, to avoid texture atlas complexity, I can use a single canvas for all textures in a grid, then UV coordinates map to atlas regions. But with Three.js, if I use one material per block type, I could use a single texture atlas and multiple materials (same image, different UV offset per material). Hmm, UVs are typically set on the geometry. With BoxGeometry, the UVs are 0..1 per face. I could create different geometries per block type with UVs offset to the atlas, but then they'd use the same material. That works: define each block type as a modified BoxGeometry or a custom geometry with UVs adjusted to atlas positions. Then one mesh per type + InstancedMesh.

Actually, the easiest: create a texture atlas canvas, and for each block type create a BufferGeometry that is a BoxGeometry with UVs transformed to the atlas. But creating 6 materials per block type (one per face) is also possible: each material has a texture that is a portion of the atlas? No, textures need to be separate images or we use a single canvas per material.

Simplest for correctness: create a separate CanvasTexture for each block face type. But that's a lot of small textures. Actually, we can create one canvas per block type? For grass block, top has grass, sides has grass_side, bottom dirt. So each block type has up to 6 face textures. For sand, all faces same. For wood, top/bottom different from sides.

Let me define a material per block face type. Each material uses a CanvasTexture. The number of unique face types:
- grass_top
- grass_side
- dirt
- stone
- sand
- snow (or grass? no, snow block top)
- snow_side? Actually snowy mountain uses stone with snow top, but if top block is a snow block, all its faces snow.
- log_side
- log_top
- leaves
- water

That's ~10 textures. Manageable.

Then for each block type, define an array of 6 materials in order: [+x, -x, +y, -y, +z, -z] (right, left, top, bottom, front, back). For BoxGeometry in three.js, the material groups are in order: px, nx, py, ny, pz, nz (I need to check: yes, BoxGeometry has groups in that order).

Then for each block type, create a material array. Then for each block type, create an InstancedMesh with BoxGeometry and the material array.

But InstancedMesh with multiple materials works? Yes, InstancedMesh inherits from Mesh and uses groups. It should support groups with material array.

But there's a catch: InstancedMesh supports a single geometry and a single material or material array. The material array is passed to the mesh. The renderer draws each group. For each instance it draws the whole geometry? Actually, InstancedMesh renders all instances for a geometry as a whole, but with groups, it will render each group for all instances. That means for each block type, we'd have an InstancedMesh with a BoxGeometry that has 6 groups, and each cube draws 6 faces. Each instance counts as one cube. That is correct.

Performance: Each block type has one InstancedMesh. The number of instances is the number of blocks of that type. When rendering, for each material change, the renderer draws all instances for that group. For 6 materials, that's 6 draw calls per block type. With ~10 block types, 60 draw calls + water + clouds, that's fine.

But wait: with InstancedMesh, we cannot cull per-face (hide faces based on neighboring blocks) because InstancedMesh draws all 6 faces per cube, and there's no per-instance face visibility. So interior faces between adjacent solid blocks are rendered. That's a lot of overdraw. However, if the world is mostly solid, rendering inner faces could be very wasteful.

Let me estimate: For a hill, the number of exposed surface blocks is O(surface area + side area). The number of interior blocks is large. If we render every block as a solid cube, we'd render all 6 faces even those hidden by neighboring blocks. The total block count would be volume of terrain, which is 128*128*avg_height ~ 250k blocks, each with 6 faces = 1.5M faces. Actually the visible surface faces are maybe 5x fewer? It's not terrible. But when you fly over, the GPU must process hidden faces and perform depth testing. 1.5M triangles is nothing for a GPU. The real cost is draw calls, but InstancedMesh keeps that low. So maybe it's okay.

But the problem: z-fighting between coplanar faces of adjacent cubes. If two solid cubes are right next to each other, the shared face will be drawn twice. They're coplanar, so z-fighting may occur. To avoid, we need to only render exposed faces. So we need face culling.

Therefore, InstancedMesh with full cubes is problematic due to z-fighting on hidden faces. Even if we set depthWrite and depthTest, the face between two cubes at the same plane will z-fight because the second renders on top of the first, but due to floating point, it flickers.

So, we must avoid rendering hidden faces. This means we need to generate geometry per chunk, adding only exposed faces. That's the right approach.

Alright, let's implement a chunk-based voxel engine with face culling.

**Architecture:**

- World size: 128x128 columns (XZ). Height: up to 64.
- Divide into chunks, say 16x16 columns, so 8x8 = 64 chunks.
- For each chunk, generate a BufferGeometry containing vertices for exposed faces of all blocks in that chunk.
- Each vertex has position, normal, uv, and color (for per-face shading).
- The UVs point into a texture atlas (one canvas with all block textures arranged in a grid). We'll store all face textures in a 4x4 atlas? Or since we have ~10 unique textures, 4x4 works (16 cells).
- For each block in the chunk, check its 6 neighbors (including across chunk boundaries). If a neighbor is air (or water? water is transparent, so still render faces between water and air; and between water and solid, render water surface), then add the corresponding face.

**Texture Atlas:**
We'll draw each texture at 16x16 pixels, then create a canvas large enough. For simplicity, use a 4x4 grid = 16 cells. Place textures in the grid. In three.js, we use NearestFilter to keep pixel art crisp.

We need to define UV coordinates for each face. I'll create a function that given a block type and face index, returns the UV coordinates for the 4 corners mapping to the cell in the atlas.

Actually, we can compute the UVs in code when building geometry. For each face of a cube (BoxGeometry vertices), the UVs for that face are (0,0) to (1,1). We need to transform them to <u, v> coordinates within the atlas cell. Instead of using texture matrix, we can compute the UVs directly: uv_atlas = (uv * cellSize + cellOrigin) and maybe flip Y.

Since all textures in the atlas are the same size (16x16), we just need the cell origin.

**Faces and normals:**
For a cube, we can define the 6 faces. With per-face shading, we want to darken the sides (normals not pointing up). We'll use MeshLambertMaterial with vertexColors and a map. Actually, if we use a custom shader or just vertex colors, we can multiply the texture color by the face brightness. Three's MeshLambertMaterial takes into account directional lights, but we can also manually set vertex colors to a shade: top (1.0), bottom (0.6), sides front/back (0.8), left/right (0.7). Since we also want a sun, we can use a directional light as well. But per-face shading can be achieved by setting the vertex colors. I'll set vertex colors based on face normal.

**Clouds:**
Use simple white cubes at a high Y (e.g., 40). Drift slowly across the world. Could use InstancedMesh for cloud blocks, with a few clusters. I'll generate a few cloud "puffs" and update their positions.

**Sky:**
Set scene.background to a gradient? Actually, a sky color can be set, and fog color matching. For a sun, use a sprite or mesh. Since no external resources, create a canvas for the sun (a yellow circle) or a three.js sprite with a generated texture. Or just add a PointLight and a circle mesh.

Simplify: Set scene.fog = new THREE.Fog(skyColor, near, far). Background = skyColor. Add a sun as a Mesh with a plane geometry and a canvas texture with a glowing circle.

**Camera path:**
Use a CatmullRomCurve3 or a series of points along the terrain. The camera should smoothly fly through the landscape. We can compute a path that goes over hills and valleys. Since terrain is procedural, we can sample the height at points and create a curve. For simplicity, define a few waypoints and create a CatmullRomCurve3. The camera looks at a target also on the path, slightly ahead.

Use `requestAnimationFrame` and `clock` or the timestamp to get time. Move along the curve, set camera position and target. Use `lookAt`.

**Water:**
Water blocks below sea level. Water should be semi-transparent. For water, we still need to render the surface. In a voxel world, water occupies the space from sea_level down to the terrain floor. But rendering water as solid cubes is fine. Use transparent material.

Since we cull faces between solid blocks, water blocks need to have faces only where they meet air (or solid). Also, the top face of water at sea level should render. Underwater, the bottom faces? We'll treat water as a special block type. In face generation, a solid block face is rendered if neighbor is air. A water block is semi-transparent, so we should not render faces between two solid blocks, but we need to render faces between water and air, and between water and solid (from the water side). Actually, if water is transparent, we still need faces where water meets air to see the surface. But we don't want to see faces between water and the bottom sand? Actually, under the water, the sand/terrain blocks have faces in the water. Since water is transparent, you should see the terrain under it. So we should render the terrain faces, and water blocks on top. But if water is a solid cube, then the water cube at (x, sea_level, z) has its bottom face adjacent to the sand block below. If we hide that face (both are solid), the sand below is exposed. But the water cube's side faces are visible at the shore. So for water, we probably should still generate its top face as a flat surface, and side faces around the perimeter of the lake. The bottom face at the water-terrain boundary can be hidden to avoid the sand being covered? Actually, the sand's top face is covered by water, so we don't need to render the sand top. The water top face is what you see from above.

This gets complex. Let me simplify: I'll generate water as a separate mesh: a plane of semi-transparent blue at sea level across the whole world, with vertex animation? No, "Minecraft-style" water can be a flat translucent plane. But the requirement says "lake or sea with semi-transparent water" and blocks. Water as blocks is more Minecraft-y. Let's do a 3D water grid but only render the top surface and the side faces that border air. Actually, we can treat water as a block type. In face culling, we consider water as opaque for the purpose of hiding faces of terrain, but water itself is transparent to look at.

Simpler approach: When generating geometry:
- Iterate over all blocks in a chunk.
- A block is one of: air, solid (grass/dirt/stone/sand/snow/wood/leaves), water.
- For each block, for each of 6 directions, if the neighbor is outside the world (air), or is air, or (if current block is water and neighbor is air) then add the face.
- Actually, for water and adjacent air: add water face.
- For solid adjacent to air: add solid face.
- For solid adjacent to water: We don't want to render the solid face if it's underwater when seen from outside (since water is transparent, you'd see the solid sides from underwater; but you'd also see the solid sides from above through the water). If we don't render the solid face, the underwater terrain will be invisible from above the water (you'd see into the water column as if the sides are open, but the top of the underwater terrain is at a lower level, so you'd see through the side of the mountain underwater). Wait, imagine a hill dipping into water. The side of the hill under the water should be visible from under the water surface. If we hide all solid faces adjacent to water, then when you're underwater, you'd see through the terrain. So we need to render solid faces even if adjacent to water, because water is transparent. But we also need to render the water surface. So:
  - Render solid faces adjacent to air or water (so terrain is visible through water).
  - Render water faces adjacent to air or solid? Actually, water surface (top) adjacent to air must be rendered. Water side faces at the shore (adjacent to air) must be rendered. Water faces adjacent to solid should be hidden to avoid seeing the transparent water's inner faces? But since water is transparent, we want to see through it, so we don't want to render the far side of the water volume. So water faces between water and solid should be culled (they're interior). So water faces only where neighbor is air.

So rules:
- For each block B of type T:
   - If T is solid:
      - For each neighbor type N:
         - If N is air or (N is water and T is not water): add the solid face. (So solid faces adjacent to water are shown.)
   - If T is water:
      - For each neighbor N:
         - If N is air: add the water face. (Only the surface and shore boundaries.)
         - If N is solid: don't add (hide the face between water and solid). Because you see the solid through the water.
   - If T is air: skip.

Also, for solid B and neighbor N solid: don't add face (culled).

But wait: What about a solid block below water but with water above? The solid's top face is adjacent to water (N=water), so we add the solid face. That's the sand bottom visible through water. Good.

What about a water block below sea level and beside solid: no face. Good.

What about the bottom face of a water block? It's adjacent to solid (sand below), so no face. Good.

This should produce correct visuals.

**World generation with layered noise:**

Implement simplex or Perlin noise. Three.js doesn't include noise. I'll write a simple Perlin noise implementation or use a seeded random + smooth interpolation. To keep code compact, I'll implement a basic 2D Perlin noise or use value noise with multiple octaves.

Let me implement a small noise library (2D) with:
- hash function
- fade
- gradient

Then layer 2-3 octaves for height.

Height range: e.g., base 10 + noise * 30, so min 0, max 40. Sea level at 12.

For each (x,z):
- n = noise(x*freq1 + seed, z*freq1) * amplitude1 + noise(x*freq2+offset, z*freq2) * amplitude2 + ...
- h = Math.floor(n)
- Clamp h between 1 and 60.

But I need a seed for reproducibility. I'll use a simple seeded PRNG.

**Trees:**
Trees should be placed on grass blocks (soil) above sea level, with some probability. A tree is:
- Trunk: 4-5 logs (wood) at column (x, z), from y+1 to y+4/5.
- Leaves: a few leaves around the top: a 3x3x4 block arrangement.

When generating chunks, we need to add trees. Since tree structures span multiple columns, we should generate them in a separate pass after terrain, but before geometry.

I'll generate a tree map per column in the whole world beforehand, storing (tree type, height). Then during geometry generation, add the tree blocks.

**Clouds:**
Use a few InstancedMesh (or merged geometry) of white cubes floating at y=40. Move them along X direction over time. Since the world is 128x128, clouds could be placed above. We'll animate their positions by modifying the model matrix of the cloud group.

**Per-face shading:**
We'll fill vertex colors with brightness values per face. This also gives a nice look.

**Face generation algorithm:**

Define the 6 faces with vertices and normals. For a unit cube centered at (0,0,0), the 6 faces have 4 vertices each. Rather than hardcoding, use a standard cube and for each exposed face, copy the 4 vertices and translate to block position.

But to merge into a chunk geometry, we need to append vertices for all faces. For each face, we push 4 vertices (2 triangles, 6 indices) or 6 vertices. We'll use non-indexed geometry for simplicity. Actually, we need to add normals, uv, color. We can use a BufferGeometry with position, normal, uv, color attributes.

For each face, the vertex positions are:
- +X: (0.5,0,1), (0.5,1,1), (0.5,1,0), (0.5,0,0) ... need to get consistent winding for outward normals.
- -X: (-0.5,0,0), (-0.5,1,0), (-0.5,1,1), (-0.5,0,1)
- +Y: (0,1,0), (1,1,0), (1,1,1), (0,1,1) but careful.
Actually, let's define each face with 4 corners in CCW order from the outside. For a unit cube centered at origin, each face is at ±0.5. The normal is the outward normal. I'll generate the four corners by combinations.

For example, top face (y=+0.5): corners (-0.5,0.5,-0.5), (0.5,0.5,-0.5), (0.5,0.5,0.5), (-0.5,0.5,0.5) but with winding CCW when viewed from top (looking down -Y). Actually, three.js uses a right-hand coordinate system, and BoxGeometry faces are defined so the normal points outward if the vertices are in CCW order when viewed from outside. Let's use the standard BoxGeometry vertices and UVs and simply take the 4 vertices per face.

Alternatively, I can rely on three.js's BoxGeometry by creating a BoxGeometry and then for each face, reading the geometry attributes. But that's at runtime. Simpler: I'll create a function `addFace(positions, normals, uvs, colors, blockPos, blockType, faceDir, brightness)`. Then inside, generate the 4 corner positions for the face using constant coordinate (e.g., for +Y, y=1) and corners. Use `boxMins` and `boxMaxs` where box is unit cube [0,1] for a block at (0,0,0) translated by blockPos. Actually let's define block coordinates in voxel space: block at (x,y,z), its cube corners are (x,y,z) to (x+1,y+1,z+1). A face is one side.

I can define for each of the 6 directions:
- right (+X): faces at x = x+1. The normal (1,0,0). Corners (in CCW order from outside, looking along -X direction): (1,0,1), (1,0,0), (1,1,0), (1,1,1) -- wait, need to get CCW. Let me derive from box geometry: For the +X face of a unit box centered at origin, the vertices are (0.5, 0.5, 0.5), (0.5, 0.5, -0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5) (winding CCW when viewed from +X). Actually three.js BoxGeometry defines:
  - px: (0.5, 0.5, 0.5), (0.5, -0.5, 0.5), (0.5, -0.5, -0.5), (0.5, 0.5, -0.5) ... not sure.

I'll use a known table. For a unit cube from (0,0,0) to (1,1,1), the face corners are:
  - +X: (1,1,1), (1,0,1), (1,0,0), (1,1,0) -> normal +X. Winding? From outside looking +X, we see yz; CCW order means (1,1,1) -> (1,1,0) -> (1,0,0) -> (1,0,1)? Let's use a known set.

This is error-prone. Let me instead build a BoxGeometry and then use its attributes to generate face data. Since I need block type-specific UVs and colors (per-face shading), I can precompute the vertex and index data of a unit cube once. Then for each exposed face of a block, I copy the corresponding 6 indices (2 triangles) or the 4 vertices of that face, transform the positions by adding block offset, set UVs (depending on face/texture) and color (depending on normal). This is much less error-prone.

I'll create a unit cube BufferGeometry with:
- position for all 24 vertices? Actually BoxGeometry uses 24 vertices (4 per face) and 36 indices, with separate groups per face. Normals are per-vertex 3. UVs per vertex. We can access `geometry.attributes.position` and `geometry.index`. For each face, we know its 4 vertex indices and the 6 triangle indices (or construct from the 4). We can iterate through the face groups to know which faces correspond to which direction. Or just hardcode mapping.

Better: I'll create a simple data array of vertices for the 6 faces. Since it's a unit cube, each face has 4 vertices. I'll list them manually, but carefully ensure the winding and normals.

Let's define a block with coordinates x from 0 to 1, y up, z from 0 to 1.

The 6 faces and their corner points (CCW when viewed from outside, standard):
- Top (+Y): corners in order: (0,1,1), (1,1,1), (1,1,0), (0,1,0). Winding CCW from above (looking down -Y). Actually if you look from above, x is right, z is down in screen? It's easier to rely on three.js's coordinate system: +Y up, +X right, +Z toward camera. For top face, normal +Y. Vertices in CCW when viewed from above (looking down): (0,1,0) -> (1,1,0) -> (1,1,1) -> (0,1,1). This gives normal +Y by right-hand rule (cross product).
- Bottom (-Y): normal -Y. Viewed from below (looking up), CCW: (0,0,0) -> (0,0,1) -> (1,0,1) -> (1,0,0).
- +X (right): normal +X. Viewed from +X side (looking toward -X), CCW: (1,0,0) -> (1,1,0) -> (1,1,1) -> (1,0,1).
- -X (left): normal -X. Viewed from -X side, CCW: (0,0,1) -> (0,1,1) -> (0,1,0) -> (0,0,0).
- +Z (front): normal +Z. Viewed from +Z (looking toward -Z), CCW: (0,0,1) -> (0,1,1) -> (1,1,1) -> (1,0,1)? Wait, if normal is +Z, then CCW from outside (looking along -Z): (0,0,1) -> (1,0,1) -> (1,1,1) -> (0,1,1). Let me verify cross: (1,0,1) - (0,0,1) = (1,0,0); (1,1,1) - (0,0,1) = (1,1,0); cross = (0,0,1) which is +Z. Yes.
- -Z (back): normal -Z. Viewed from -Z (looking along +Z), CCW: (0,0,0) -> (0,1,0) -> (1,1,0) -> (1,0,0). Cross: (0,1,0)-(0,0,0)=(0,1,0); (1,1,0)-(0,0,0)=(1,1,0); cross = (0,0,-1) which is -Z. Good.

I'll store these as arrays of vertex positions for each face, with y as texture v? We'll assign UVs separately per face.

**UV mapping:**
The texture atlas will be a 4x4 grid. For a given face, we need to know which cell of the atlas to use. This depends on the block type and face direction. For simplicity, let's assign each block texture a cell index:
0: grass_top
1: grass_side
2: dirt
3: stone
4: sand
5: snow
6: wood_side
7: wood_top
8: leaves
9: water
10: (empty)
...

Actually, for grass block: top -> grass_top, sides -> grass_side, bottom -> dirt. So it's not just a single cell.

Instead of an atlas, maybe use separate textures per face. But then we'd need to either use material arrays (per face) and merge into one geometry with a single material - no, material arrays don't allow per-vertex texture selection. We could use a custom shader with a texture array. Shader complexity increases.

Alternative: Use a texture atlas. We'll map the UVs for each face based on block type and face direction. When building the geometry, for each face we compute the UV coordinates to the appropriate atlas cell.

Let's precompute a mapping `blockFaceUV[blockType][faceDirection] = {u, v}` where u,v are the top-left of the cell in the atlas grid.

For the atlas, assume 4 columns x 4 rows. Cell size 1/4.

I'll list textures:
0: grass_top
1: grass_side
2: dirt
3: stone
4: sand
5: snow
6: log_side
7: log_top
8: leaves
9: water
10: (could be rock or snow side)

For grass block:
- top: grass_top (cell 0)
- bottom: dirt (cell 2)
- sides: grass_side (cell 1)

For dirt block: all faces dirt (2)
Stone: all faces stone (3)
Sand: all sand (4)
Snow block (for snowy peaks): all faces snow (5)
Wood block:
- top/bottom: log_top (7)
- sides: log_side (6)
Leaves: all faces leaves (8)
Water: all faces water (9)

For a block that is stone with snow on top (when a block is at the surface of a snowy mountain, I'll make it a snow block; below it is stone). So no need for snowy dirt.

OK.

**Atlas texture generation:**

We'll draw each texture on a canvas at e.g., 16x16 pixel art. Then place them in the atlas canvas (64x64? Actually 4x4 cells of 16x16 = 64x64). Use nearest filtering for crisp pixels.

Let me define a function `createTexture` that takes a palette array (2D matrix) and returns a canvas. For each texture, define a 16x16 array of color indices or use a compact string.

To keep code manageable but still look good, I'll programmatically set each pixel by code for each type. For example:

Grass top: alternating light/dark green with some noise.
Grass side: dirt with a grass strip at the top.
Dirt: brown noise.
Stone: gray noise.
Sand: tan noise.
Snow: white with light blue noise.
Log side: brown vertical stripes.
Log top: rings.
Leaves: green noise with darker/lighter patches.
Water: translucent blue with noise.

Let me write a general noise texture generator: given colors [base, dark, light], fill with random pixels using seeded value. For grass side, draw top 3 pixels green.

I'll use a seeded PRNG for consistency.

**Implementing in HTML:**

Structure:
```html
<!DOCTYPE html>
<html>
<head>
<style>body{margin:0;overflow:hidden;}</style>
</head>
<body>
<script type="module">
import * as THREE from 'three';
...
</script>
</body>
</html>
```

Now let's code step by step.

### 1. Noise functions

Implement a 2D simplex or Perlin. I'll use a compact Perlin noise:

```js
function hash(x,z){ return ( (x*374761393 + z*668265263) ^ ((x+z)>>12) ) * 1274126177; } // not great
```

Better: use a gradient noise:

```js
// permutation table
const perm = new Uint8Array(512);
// seed 0..1
Math.seededRandom = ...
```

Simpler: Use classic Perlin with pixel lattice. I can use a deterministic PRNG to make random gradients.

But to save space, I'll implement value noise: random values at integer lattice points, then bilinear interpolation with smoothing (i.e., terrain smooth).

```js
function makeNoise(seed) {
  const rand = mulberry32(seed);
  const lattice = new Map();
  function randFor(x,z) {
    key = x + ',' + z;
    if not in map, set rand();
    return ...
  }
  function smoothNoise(x,z) {
    const x0 = Math.floor(x), z0 = Math.floor(z);
    const x1 = x0+1, z1 = z0+1;
    const fx = x-x0, fz = z-z0;
    const sx = fx*fx*(3-2*fx);
    const sz = fz*fz*(3-2*fz);
    const v00 = randFor(x0,z0), v01=randFor(x0,z1), v10=randFor(x1,z0), v11=randFor(x1,z1);
    return lerp(lerp(v00,v10,sx), lerp(v01,v11,sx), sz);
  }
  return smoothNoise;
}
```

Then layered:
```js
function heightAt(x,z,seed) {
  const n1 = fbm(x*0.03, z*0.03);
  ...
}
```

For fbm: 3 octaves, frequencies 0.03, 0.06, 0.12 with amplitude 16,8,4.

I'll implement mulberry32.

### 2. World generation

```js
const WORLD_SIZE=128; // columns along x and z
const SEA_LEVEL=12;
const SNOW_LEVEL=30;
const MAX_HEIGHT=40;
const chunkSize=16;
const worldChunks = [];
// height map
const heights = new Float32Array(WORLD_SIZE*WORLD_SIZE);
for (let x=0; x<WORLD_SIZE; x++) {
  for (let z=0; z<WORLD_SIZE; z++) {
    let h = Math.floor( fbm(x,z) * scale + base );
    heights[x+z*WORLD_SIZE] = Math.max(1, Math.min(MAX_HEIGHT, h));
  }
}
```

But we also need a `blockTypeAt(x,y,z)` for geometry generation. We'll wrap it.

For neighbor access across chunks, we can query `getBlock(x,y,z)` global function that reads height and materials.

Define materials as ints:
```
AIR=0, GRASS=1, DIRT=2, STONE=3, SAND=4, SNOW=5, WOOD=6, LEAVES=7, WATER=8, SAND_UNDER=...
```

Actually, in the heightmap model, there is only one block per column for the surface; below that it's solid but we only place blocks when adding exposed faces. So `blockTypeAt(x,y,z)` returns the type of the block at that position if the column's height is >= y, else AIR. The type depends on depth as discussed.

I'll write a function that returns the "material" for any block in the world, accounting for terrain + trees. But trees are special: they sit on top of columns and have blocks above the terrain height. We'll store trees in a separate data structure and `blockTypeAt` checks tree blocks first.

Simpler: generate a 3D array? That could be WORLDSIZE*MAX_HEIGHT*WORLDSIZE = 128*40*128 = 655k entries, which is fine. A Uint8Array of that size is 0.6 MB. That's trivial! Let's do full 3D array. Fill with air. Then set terrain columns. Then set tree blocks. Then query blockTypeAt directly.

This is simpler and avoids checking tree maps separately.

Let's do that.

```js
const CHUNK_SIZE=16;
const chunks = {}; // key "cx,cz" -> BufferGeometry

const worldData = new Uint8Array(WORLD_SIZE * MAX_HEIGHT * WORLD_SIZE); // fills 0 = air
function getBlock(x,y,z) {
  if (x<0||x>=WORLD_SIZE||z<0||z>=WORLD_SIZE) return AIR; // treat out of bounds as air (or solid? walls?)
  if (y<0) return STONE;
  if (y>=MAX_HEIGHT) return AIR;
  return worldData[(y*WORLD_SIZE + z)*WORLD_SIZE + x];
}
function setBlock(x,y,z,v) {
  if (x<0||x>=WORLD_SIZE||z<0||z>=WORLD_SIZE) return;
  if (y<=0 || y>=MAX_HEIGHT) return;
  worldData[(y*WORLD_SIZE+z)*WORLD_SIZE+x] = v;
}
```

Terrain:
```js
for (let x=0; x<WORLD_SIZE; x++) {
  for (let z=0; z<WORLD_SIZE; z++) {
    h = heights[z][x] // or array
    for (let y=1; y<=h; y++) {
      let type;
      if (h < SEA_LEVEL-1) {
        type = SAND;
      } else if (h < SEA_LEVEL+1) {
        // beach
        type = (y===h) ? SAND : (h-y < 4 ? SAND : SAND); // just sand
      } else if (h > SNOW_LEVEL) {
        type = (y===h) ? SNOW : STONE;
      } else {
        if (y===h) type = GRASS;
        else if (h-y <= 3) type = DIRT;
        else type = STONE;
      }
      setBlock(x,y,z,type);
    }
    // fill water
    if (h < SEA_LEVEL) {
      for (let y=h+1; y<=SEA_LEVEL; y++) {
        setBlock(x,y,z,WATER);
      }
    }
  }
}
```

Need to handle trees: on grass blocks, place a tree with some probability. Use a PRNG seeded by column or global seed. To allow trees to be placed before geometry, just run after terrain.

Trees: For each column where type is GRASS, if rand < 0.03, place a tree: trunk height 4-5, then leaves. The tree might overlap terrain; if so, skip? We'll just place, potentially growing from low valleys. But to avoid trees on water or high mountains, only on grass and y< SNOW_LEVEL - 5.

```js
function placeTree(x,z) {
  const h = height at that column
  const trunkH = 4 + Math.floor(rand()*3);
  for (let y=h+1; y<=h+trunkH; y++) setBlock(x,y,z,WOOD);
  for (let dy=-2; dy<=2; dy++) {
    for (let dx=-2; dx<=2; dx++) {
      for (let dz=-2; dz<=2; dz++) {
        if (Math.abs(dx)===2 && Math.abs(dz)===2 && Math.abs(dy)===2) continue; // square corners
        const lx=x+dx, ly=h+trunkH+dy, lz=z+dz;
        if (getBlock(lx,ly,lz)===AIR && ly<=h+trunkH+2 && ly<=MAX_HEIGHT-1) {
          setBlock(lx,ly,lz,LEAVES);
        }
      }
    }
  }
}
```

This is a bit rough, but okay.

### 3. Geometry generation

Now the core. We'll build a merged BufferGeometry per chunk.

For each chunk (cx, cz) in world:
- For each block (x,y,z) in the chunk's 16x16xMAX_HEIGHT range:
   - blockType = getBlock(x,y,z)
   - if AIR, skip
   - For each of 6 faces:
      - if shouldRenderFace(x,y,z,blockType, direction) then add face.

`shouldRenderFace`:
```
n = getBlock(x+dx, y+dy, z+dz)
if (blockType === WATER) {
  return n === AIR; // only water surfaces exposed to air
}
// solid
if (n === AIR || (n === WATER && blockType !== WATER)) return true; // faces to air and water
return false;
```

For faces at world border, we treat out-of-bounds as AIR? That would cause the sides of the world to show faces. We want the world to be an island maybe, but since it's a 128x128 grid, we can set out-of-bounds to AIR to reveal the sides. But that may show the interior of terrain from outside. Since the camera stays within, it's fine. Or set to STONE to hide sides? Actually if out of bounds is STONE, then the side faces at the border are hidden, but the world would look solid from the sides; the camera won't go out. If OOB is AIR, the edge columns have exposed sides, which looks neat. We'll treat OOB as AIR.

Now, for each face, we need to compute:
- positions: the 4 vertices, translated by block position.
- normals: the face normal.
- colors: per-face brightness.
- uvs: based on block type and face direction.

To generate the face, we'll use the `addFace` function:

```js
function addFace(geoData, x,y,z, face, brightness, uvCell) {
  const faceVerts = FACE_VERTS[face]; // array of 4 corner vectors
  const faceUvs = FACE_UVS[face]; // 0..1 UVs
  const positions = geoData.positions;
  const uvsAttr = geoData.uvs;
  const normalsAttr = geoData.normals;
  const colors = geoData.colors;
  for (let i=0; i<4; i++) {
    positions.push(x+faceVerts[i][0], y+faceVerts[i][1], z+faceVerts[i][2]);
    uvsAttr.push(
      (uvCell.u + faceUvs[i][0] * cellUV) ) // careful: cell origin in 0..1
    normalsAttr.push(FACE_NORMALS[face][0], ...);
    colors.push(brightness, brightness, brightness);
  }
  // indices: two triangles, but we'll push the 4 corners as 6 indices (if non-indexed, just push vertices and let order)
}
```

Actually, we can push 6 vertices (2 triangles) directly without indices, or use indices. Pushing 6 vertices per face is simpler for merging. Use 4 vertices and indices? We can push 4 vertices and add 4 indices (two triangles). But the renderer requires indexed geometry or non-indexed. For indexed, we need an index array. Let's use indexed: push 4 vertices, then push indices [start, start+1, start+2, start, start+2, start+3] depending on winding. But since we don't know face diagonal, we need the vertex order to be correct.

Alternatively, push 4 vertices and use `setIndex` per geometry? We need to know how many vertices before the face. Let's use non-indexed to avoid complexity: each face = 6 vertices (two triangles). We'll push 6 vertices per face. That increases vertex count but fine.

For each face, the 6 vertices are just the 4 corners, duplicated. We'll push them in order: [v0,v1,v2, v0,v2,v3].

Now the faceUVs: For a unit cube face, the UVs for the 4 corners are standard:
- +X face (right): UVs: (0,0), (0,1), (1,1), (1,0) or similar. Need to map so texture appears upright.

I'll use the standard BoxGeometry UVs. For each face, the 4 UVs are one of the four corners. To keep it simple, I'll define for each face the 4 UV corners as constant.

Actually, the exact orientation doesn't matter much for noise textures, except for grass side which would need to be upright. We'll assign accordingly.

Let me define FACE_VERTS, FACE_UVS, FACE_NORMALS for 6 directions.

I'll use the standard cube corner table from three.js. Let's derive:

For a cube with vertices as previously listed:

Top (+Y):
verts: (0,1,1), (1,1,1), (1,1,0), (0,1,0)
UVs maybe: (0,1), (1,1), (1,0), (0,0) where v is up? In three.js, UV (0,0) is bottom-left of texture. For top face, we want the texture upright when viewed from above. Since no orientation matters for global, let's use these.

But we need to be careful with three.js's texture Y direction. By default, texture.flipY is true. So v=0 is bottom of image. I'll not worry too much; as long as the texture appears roughly okay.

Actually, I'll set UVs such that the grass side top is the top of the texture. For side faces, the up direction on the face should map to +Y direction. Let me define:
- For any face, the UV coordinate (u,v) where v increases upward (i.e., from bottom to top of the texture), and u increases along the face. For side faces, the top of the texture is the top of the block.

I'll construct each face's UVs from two orthogonal vectors. But hardcoding is easier.

Given time, let's just use fixed UVs from a typical cube:

Three.js BoxGeometry UVs (from source):
- px (right) +X: UVs: (0,0), (1,0), (1,1), (0,1)? Actually, I'll not spend too long; the textures are noisy, so orientation is forgiving. Grass side has grass strip on top; if it's rotated it might look odd. Let's ensure the grass strip is at the top.

I'll define for each face the 4 vertices and corresponding UV pairs manually, testing mentally.

Let's define a face by its normal; the texture on that face should have v=1 at the top of the face (y+). For any face, the UV of a corner with y coordinate higher should have higher v. Similarly, u should span along the horizontal axis.

Therefore, write a function that, for a given face, the UVs depend on the actual x,y,z of the corner. But since we can't vary per face easily, I'll precompute.

For each face, I'll list the 4 corners in CCW order and the corresponding UVs (0,0), (1,0), (1,1), (0,1) but which corner gets what? To ensure consistent orientation:
- The corner with minY gets v=0, maxY gets v=1.
- The corner with min horizontal (relative to face) gets u=0, max gets u=1.

Let's define UV for each of the 4 corners accordingly.

For a side face (e.g., +Z): The face is at z=1. As x goes from 0 to 1, u goes from 0 to 1. As y goes from 0 to 1, v goes from 0 to 1. So corners:
(0,0,1) -> uv(0,0)
(0,1,1) -> uv(0,1)
(1,1,1) -> uv(1,1)
(1,0,1) -> uv(1,0)

-Direction: The face at z=0. To have u go left-to-right (as x increases), from the outside looking at -Z, the face appears mirrored? Actually, from the outside (looking in -Z direction), x increases to the right. So same as above: (0,0,0) -> (0,0), (0,1,0) -> (0,1), (1,1,0) -> (1,1), (1,0,0) -> (1,0).

+X face: at x=1. Across the face, as z increases, u goes from 0 to 1? From outside looking at +X, the horizontal axis is z. If we want world consistency, maybe use z as u. Let's simply set:
- +X: corners (1,0,0) -> (0,0), (1,1,0) -> (0,1), (1,1,1) -> (1,1), (1,0,1) -> (1,0)
- -X: corners (0,0,1) -> (0,0), (0,1,1) -> (0,1), (0,1,0) -> (1,1), (0,0,0) -> (1,0) maybe.

OK, to save time, I'll take a known cube. Let me use the vertex data from three.js's BoxGeometry by creating an object in JS:

Actually, a more efficient approach: use the `BoxGeometry` from Three.js and extract the position and uv attributes in a loop for building face data? Wait, we can create a `BoxGeometry(1,1,1)` and then for each face, read `geometry.attributes.position`, `geometry.attributes.normal`, `geometry.attributes.uv`. But then we'd need to map the triangles to faces and choose which triangles to include (face culling). That's unnecessary.

Let me use a manual table. I'll be careful enough.

Actually, the simplest for correctness is to use a `BoxGeometry` and in a loop over its triangles, draw all? No, we need to only draw some faces.

Given time constraints, I'll use a custom cube table from three.js source. Let me recall BoxGeometry `buildPlane` function. It takes `u`, `v`, `w` axes, `udir`, `vdir`, `width`, `height`, `depth`, `gridX`, `gridY`. For a unit cube, it creates 6 planes:
- px: buildPlane('z','y','x', -1, -1, depth, height, width) etc.

This is getting too deep.

Let me define the face vertices and UVs manually with a concrete list. I don't mind minor orientation errors as long as the textures show correctly for the most important (grass top/side).

I'll use the convention that for all faces, the UV v spans from y=0 to y=1, except for top/bottom where v spans along z.

Here's a table I can use:

```
const faces = [
  { // +X
    normal: [1,0,0],
    corners: [
      {pos:[1,0,1], uv:[1,0]},
      {pos:[1,1,1], uv:[1,1]},
      {pos:[1,1,0], uv:[0,1]},
      {pos:[1,0,0], uv:[0,0]},
    ]
  },
  { // -X
    normal:[-1,0,0],
    corners: [
      {pos:[0,0,0], uv:[0,0]},
      {pos:[0,1,0], uv:[0,1]},
      {pos:[0,1,1], uv:[1,1]},
      {pos:[0,0,1], uv:[1,0]},
    ]
  },
  { // +Y
    normal:[0,1,0],
    corners: [
      {pos:[0,1,1], uv:[0,1]},
      {pos:[0,1,0], uv:[0,0]},
      {pos:[1,1,0], uv:[1,0]},
      {pos:[1,1,1], uv:[1,1]},
    ]
  },
  { // -Y
    normal:[0,-1,0],
    corners: [
      {pos:[0,0,0], uv:[1,1]},
      {pos:[1,0,0], uv:[0,1]},
      {pos:[1,0,1], uv:[0,0]},
      {pos:[0,0,1], uv:[1,0]}, // wait, need to ensure outward normal
    ]
  },
  { // +Z
    normal:[0,0,1],
    corners: [
      {pos:[0,0,1], uv:[0,0]},
      {pos:[1,0,1], uv:[1,0]},
      {pos:[1,1,1], uv:[1,1]},
      {pos:[0,1,1], uv:[0,1]},
    ]
  },
  { // -Z
    normal:[0,0,-1],
    corners: [
      {pos:[1,0,0], uv:[1,0]},
      {pos:[0,0,0], uv:[0,0]},
      {pos:[0,1,0], uv:[0,1]},
      {pos:[1,1,0], uv:[1,1]},
    ]
  }
];
```

I need to check winding: for each face, the cross product of (c1-c0) and (c2-c0) should point outward (same as normal). If not, I should reverse the order. Let's verify the -Y face above:

Corners in order:
0: (0,0,0)
1: (1,0,0)
2: (1,0,1)
3: (0,0,1)
Vectors from 0 to 1 = (1,0,0), from 0 to 2 = (1,0,1). Cross (1,0,0) x (1,0,1) = (0*1 - 0*0, 0*1 - 1*1, 1*0 - 0*1) = (0,-1,0) which is -Y, outward. Good. So order is CCW when viewed from below.

For +Y, order:
0:(0,1,1), 1:(0,1,0), 2:(1,1,0), 3:(1,1,1)
Vectors: (0,1,1)-(0,1,1)?? Let's calculate: 0->1 = (0,0,-1), 0->2=(1,0,-1). Cross (0,0,-1)x(1,0,-1) = (0*(-1)-(-1)*0, (-1)*1-0*(-1), 0*0-0*1) = (0,-1,0) which is -Y. That's inward! So order is wrong. Let me swap.

For +Y, we want normal +Y. Use corners in CCW from above. From above, the face goes around counterclockwise. Given the cube, from above, the four corners are:
(0,1,0) -> (1,1,0) -> (1,1,1) -> (0,1,1)
Let's test: 0:(0,1,0), 1:(1,1,0), 2:(1,1,1), 3:(0,1,1). 0->1 = (1,0,0), 0->2 = (1,0,1). Cross = (0*1-0*0, 0*1-1*1,1*0-0*1) = (0,-1,0) -> still -Y? Wait, cross product (1,0,0) x (1,0,1) = (0*1 - 0*0, 0*1 - 1*1, 1*0 - 0*1) = (0,-1,0). That's -Y. I used the same as before because 0->1 and 0->2 are in the same direction? Let's try a different order:
0:(1,1,0), 1:(1,1,1), 2:(0,1,1), 3:(0,1,0)
0->1=(0,0,1), 0->2=(-1,0,1), cross = (0*1-1*1, 1*(-1)-0*1, 0-0) = (-1,-1,0) not +Y.
Let me just compute the correct order: For a plane with normal +Y, if we list vertices counterclockwise when viewed from +Y (i.e., looking down -Y), then the X-axis goes to the right, Z-axis goes downwards? Actually, in three.js, camera looks toward -Z, so when looking from above (down -Y), X is right, Z is pointing down/screen. CCW from that view is a right-handed coordinate system? Let's just use the known three.js BoxGeometry data: The top face (py) has vertices (0=-0.5,0.5,0.5), (1=0.5,0.5,0.5), (2=0.5,0.5,-0.5), (3=-0.5,0.5,-0.5) in UV order (0,1), (1,1), (1,0), (0,0)? I'm going around.

Actually, let's not manually verify. I can write the face corners as per standard box, and if the face has wrong winding, the material's side can be set to `THREE.DoubleSide` or we can fix winding with `material.side = THREE.FrontSide` and we see the outside. If we get the winding wrong, faces become invisible (since FrontSide backface culling). To avoid, we can set `material.side = THREE.DoubleSide` for all materials. Then the face is visible from either side, but we still need correct normals for lighting? Actually, if we set vertex normals manually to the outward direction, the lighting will be correct even if the triangle winding is wrong? For Lambert, the normal is from the shading normal, not the winding. But the face culling determines whether a triangle is drawn based on winding. With DoubleSide, culling disabled so it's fine. So even if my winding is accidentally inverted, with DoubleSide material it will still be visible. The only downside is potential lighting issues on wrong-wound faces? Since I'm setting normals per vertex, the normals drive lighting, not winding. So I can safely set material.side = THREE.DoubleSide and not worry about winding. But transparency sorting could be affected.

Great, that simplifies. I'll just set each face UVs and positions in any order, add normals as the face normal, and for vertex colors the brightness. Use `side: THREE.DoubleSide` in materials. The backfaces of exterior blocks won't be visible because adjacent blocks cull faces, but if there are holes, you might see inside; acceptable.

Now, for UVs, as long as I map the texture correctly, fine.

### 4. Brightness per face

Set:
- +Y: 1.0
- -Y: 0.5
- +X/-X: 0.6
- +Z/-Z: 0.8

This gives the cuboid look.

### 5. Texture Atlas

I need to create a canvas for the atlas. Let's do a 4x4 grid of textures, each 16x16. Atlas size 64x64.

Create a CanvasTexture with `magFilter = THREE.NearestFilter`, `minFilter = THREE.NearestFilter` for pixel art. Also `colorSpace = THREE.SRGBColorSpace` maybe.

I'll define textures via functions like `createGrassTop`, `createDirt`, etc.

Since writing per-pixel noise for each texture in code is lengthy, I'll make a generic noise texture generator.

```js
function createTex(palette, rng) {
  // palette: {base, dark, light} as [r,g,b]
  // create 16x16 canvas, for each pixel pick one of base/dark/light with random
}
```

For grass side, we need a dirt base and a strip of grass at the top. We can do:
```js
function createGrassSide() {
  const tex = createTex({base: DARKBROWN, dark: BROWN, light: LIGHTBROWN}, rng);
  // then overwrite top 3 rows with green noise
}
```

Since we have limited time, I'll write utility functions. But the HTML file will be large. Let me make it as concise as possible.

Actually, we can use the noise function to fill the textures. Use the same noise generator as terrain, but seeded separately.

I'll write a single function `makeTexture(seed, fn)` that takes a function `fn(x,y)` returning a color string. But that might be slow for 16x16.

Simpler: draw each cell with random blocks:

```js
function initTextureCanvas() {
  const canvas = document.createElement('canvas');
  canvas.width = 64; canvas.height = 64;
  const ctx = canvas.getContext('2d');
  // draw all textures individually into a temp canvas then drawImage to atlas.

  // We'll have an array `textures` of canvases 16x16.
}
```

Let me go through the required textures:

1. **grass_top**: 16x16 green noise. Use two green tones.
2. **grass_side**: dirt texture with top 3 rows green.
3. **dirt**: brown mottled.
4. **stone**: gray mottled.
5. **sand**: tan mottled.
6. **snow**: white with light gray/blue shading.
7. **log_side**: brown vertical brown stripes.
8. **log_top**: brown rings.
9. **leaves**: green noise with dark green.
10. **water**: blue noise with alpha (maybe we'll handle transparency via material).

For the atlas: place them at specific grid positions.

I can create a function `createPixelTexture(palette, noiseFactor, seed)`:
```js
const rng = mulberry32(seed);
const img = document.createElement('canvas'); img.width=16; img.height=16;
const ctx = img.getContext('2d');
for (let x=0;x<16;x++) {
  for (let y=0;y<16;y++) {
    let val = rng();
    let color = palette.base;
    if (val < 0.3) color = palette.dark;
    else if (val > 0.7) color = palette.light;
    ctx.fillStyle = `rgb(${color.join(',')})`;
    ctx.fillRect(x,y,1,1);
  }
}
return img;
```

But I need materials like wood_side with vertical stripes. I can draw base, then vertical lines.

I'll code each texture individually but in a compact way. For example:

```js
function texGrassTop(seed) {
  const c=tex(seed, {base:[96,160,64], dark:[64,128,32], light:[128,192,96]});
  return c;
}
function texGrassSide(seed) {
  const c=tex(seed, {base:[100,75,50], dark:[80,60,40], light:[120,90,60]});
  // draw top 3 rows green
}
```

This is going to be long but manageable. I'll store all textures in an array and then draw into atlas canvas using `drawImage`.

Let me define a helper to draw a texture into a cell:

```js
function placeInAtlas(cellIndex, img) {
  const gx = cellIndex % 4;
  const gy = Math.floor(cellIndex / 4);
  ctx.drawImage(img, gx*16, gy*16);
}
```

U vs V: The atlas is in pixel space, with (0,0) at top-left. In texture coordinates, V increases up in WebGL by default (if flipY true?). Canvas textures in three.js are flipY true by default, so the bottom of the canvas is V=0. In the atlas, cell (0,0) is top-left. When doing UV mapping, we need V to correspond correctly. If we set the UVs as (u, v) where v=1 at the top of texture, then the cell might be flipped. To avoid confusion, I'll test visually? Can't test during gen.

A safer approach: generate the atlas canvas, and then set `texture.flipY = true` (default). When we map UV (u,v) to the atlas, v=0 corresponds to the bottom of the canvas image. In our atlas, we place textures in row 0 at top. So to make the texture appear upright (grass top at top of the cube), we need to account. This is a common headache. Since the textures are noise, orientation mostly matters for grass_side's strip.

To avoid winding errors, we could set `texture.flipY = false` and draw the atlas with row 0 at the bottom? Actually, if flipY=true, image row 0 (top) becomes V=1? Let me recall: Three.js CanvasTexture loads the image, and because of flipY=true, the texture looks like the image (not flipped) because UVs are flipped. Hmm.

Maybe the simplest: Create the atlas canvas, and then, when mapping UVs, use v from the top of the cell, ignoring flip. We'll just choose UVs so that v increases upward in world (for grass side). But the atlas row 0 is the top of the canvas. In UV space with flipY=true, canvas row 0 maps to V=1. So the cell's top-left corner in image space maps to V high. Therefore, if we set the UV v such that the top of the texture maps to V high, it's correct. This is automatic if we just compute cell origin in UV from the texture coordinate system: for a cell at grid (col, row) where row is 0 at top of canvas, the UV origin (u0, v1) is:
u0 = col / 4;
v1 = 1 - row/4; // because V=1 at top? Actually, with flipY=true, V=0 is bottom. So the top-left of cell in image space maps to (u0, v1) where v1 = (gridRows - row)/4? Let's not overthink: We can set `texture.flipY = false`, so the rendering doesn't flip the image. Then the atlas canvas is used as-is; UV (0,0) is top-left of the canvas. Then a texture cell's top-left in UV is (col/4, row/4). This way, when we map a face's UVs (0 at bottom to 1 at top of face) to the cell, the cell's top (row 0 = top of image) is at V=0?? No, if flipY=false, V=0 is the top row of the image, and V increases downward. That would flip the texture when applied to geometry unless we invert V when mapping.

Three.js by default expects V to increase upward (0 at bottom). With flipY=false, UV (0,0) is top-left. So to use a texture normally, you'd set V=0 at the top, which is upside-down.

Given this confusion, I'll leave `texture.flipY = true` (default) and compute UVs with V=0 at the bottom. So for a cell, the UV coordinate for the top-left corner of the cell is:
u0 = col / columns;
v1 = 1 - row / rows; // because V=1 at top
Bottom-left corner: (u0, v0) where v0 = 1 - (row+1)/rows.

Then when building face UVs, for the top side of a cube, the texture's "up" (grass top orientation) doesn't matter. For grass_side, the top of the cell is row 0 of the image (grass strip). We want that to map to +Y direction on the face. So we set the UVs so that the top of the texture (V higher) corresponds to y=1.

We'll assign for a face: for each corner, uv = cellOrigin (u0,v0) + (u * cellWidth, v * cellHeight) where the corner's (u,v) from 0..1 is chosen so that v increases with world y. I already plan to do that.

Let me predefine face UVs where v=0 at y=0, v=1 at y=1 for sides. For top/bottom, u/v can be along x/z.

So with cell mappers, I just need the cell origin (u0,v0) where v0 is the bottom of the cell (i.e., lower V coordinate, closer to 0). Since V increases upward, the bottom of the cell is row+1? Actually, if row is 0 at bottom, then the cell's bottom-left in UV is (col/4, row/4) with V increases upward. Wait, row = 0 at bottom would be ideal. But in the atlas canvas, row 0 is at top. So row index 0 at top, 3 at bottom. In UV, the bottom-left of the atlas is (0,0), which corresponds to the bottom edge of the canvas (pixel row 63). Therefore, a cell at image row `r` (0..3, counting from top of canvas) has its V ranges from `1 - (r+1)/rows` (bottom of cell) to `1 - r/rows` (top of cell).

Thus the cell origin for a cell in column c, row r is:
u0 = c / cols;
v0 = 1 - (r+1)/rows; // bottom
v1 = 1 - r/rows; // top

We'll store cell info as (u0, v0, u1, v1).

Given this, I'll define `getCellUV(cellIndex)` returning [u0,v0,u1,v1] where u0,v0 bottom-left and u1,v1 top-right.

Then for a face corner with uv (u,v) from 0..1 (v=0 bottom of block), map:
u_map = u0 + u * (u1-u0) = u0 + u * cellW
v_map = v0 + v * (v1-v0) = v0 + v * cellH

This should work.

### 6. Materials and rendering

For the chunk geometry, we'll use a Mesh with `MeshLambertMaterial` or `MeshBasicMaterial`? If we want lighting from the sun, use Lambert and add a directional light. But with vertex colors (brightness), Lambert would multiply brightness by light color, potentially making it darker. We can actually rely on vertex colors and use `MeshBasicMaterial` ignoring lights, which is fine. Or use Lambert with ambient light.

Set `material = new THREE.MeshLambertMaterial({ map: atlasTexture, vertexColors: true, side: THREE.FrontSide? but we use DoubleSide to fix winding, side: THREE.DoubleSide, transparent? For water, we may need separate geometry with transparent material.` Because the water faces are intermingled with opaque faces. Using a transparent material for all geometry would cause sorting issues. Better: generate two geometries per chunk: one opaque, one transparent (water). The transparent geometry uses a material with `transparent: true, opacity: 0.7`. The opaque geometry uses opaque material.

So for each block, if blockType is WATER, add faces to transparent geometry; else to opaque geometry.

Both can share the same atlas texture (water cell is blue). But transparent water needs alpha. We can use `material.alphaTest`? Instead, water material has `transparent: true, opacity: 0.7`.

To make sure you see the water surface but not the underwater terrain through it too easily, we may need `depthWrite: false`? With transparent, set `depthWrite: false` to avoid sorting issues. But then the water surface may not render correctly behind other transparent surfaces. Since we only have one transparent layer, it's fine.

For the water color, the texture can have blue tones.

Now, we also need to set `vertexColors` for both. The mesh per chunk:

```js
const opaqueGeom = buildChunk(cx,cz,false);
const transparentGeom = buildChunk(cx,cz,true);
const opaqueMat = new THREE.MeshBasicMaterial({map: atlasTex, vertexColors:true, side: THREE.DoubleSide});
const waterMat = new THREE.MeshBasicMaterial({map: atlasTex, vertexColors:true, side: THREE.DoubleSide, transparent:true, opacity:0.7, depthWrite:false});
const mesh = new THREE.Mesh(opaqueGeom, opaqueMat);
const waterMesh = new THREE.Mesh(transparentGeom, waterMat);
```

But this doubles geometry? No, each chunk builds opaque and transparent vertices separately; that's fine.

However, `buildChunk` would need to generate two geometries or one geometry with groups. Easier: generate two BufferGeometries from the building function.

### 7. Camera animation

Create a curve:

```js
const points = [];
const w = WORLD_SIZE;
for (let i=0; i<10; i++) {
  const t = i/9;
  const x = 20 + Math.sin(t*Math.PI*2) * 30;
  const z = 20 + Math.cos(t*Math.PI*2) * 30;
  const y = heights[z][x] + 5; // because z and x
  points.push(new THREE.Vector3(x, y, z));
}
const curve = new THREE.CatmullRomCurve3(points, true);
```

Then in render loop, get `curve.getPoint((time % 1), cameraPos)` and `curve.getPointAt((time % 1)+0.02, target)`, with `camera.lookAt(target)`.

But `getPointAt` requires arc length calculation and may be slower; use `getPoint` and advance slightly.

### 8. Sun

Create a sprite or mesh. Use a canvas with a radial gradient.

```js
const sun = new THREE.Mesh(new THREE.PlaneGeometry(10,10), new THREE.MeshBasicMaterial({map: new THREE.CanvasTexture(sunCanvas), transparent:true, depthTest:false}));
sun.position.set(40,50,0);
sun.lookAt(camera.position);
```

But since the camera moves, the sun should stay at a fixed direction. Actually a simple directional light and a sun mesh that always faces camera would work.

I'll add a DirectionalLight from the sun's position.

### 9. Clouds

Use InstancedMesh with a few cloud meshes. Simplest: create a group of meshes using BoxGeometry(1,1,1) merged? Use InstancedMesh: generate cloud blocks in a pattern (e.g., a 3x1x2 box). Place ~5 clouds at random positions, animate by adding `time * speed` to x.

We can create a single cloud of a few blocks as a group and duplicate. But to use instancing, we can create an InstancedMesh of a single box, count = 5*numBlocks. E.g., for each cloud, add 3 boxes at offsets.

Simpler: create a `Mesh` per cloud? That would be a few draw calls, fine. We'll create 6 clouds, each a Group of a few cubes. Animate by moving the group.

### 10. Fog

Set `scene.background = new THREE.Color(0x87CEEB);` and `scene.fog = new THREE.Fog(0x87CEEB, 60, 120);` to fade the horizon.

Now let's write the code. It's going to be long, but I'll keep it compact by using loops and utility functions.

Due to the complexity, I'll try to fit it all into one script.

Before writing the full code, let's estimate the memory and performance: 8x8 chunks, each with up to 16x16x40 blocks; building geometry for each chunk might be a bit heavy at startup, but fine for 64 chunks. We generate all chunks synchronously; the page may freeze for a second. Acceptable.

Let's code.

I'll start with the HTML, include the style, and the script. In the script, I need to implement:

- mulberry32
- noise generation
- height map
- worldData setup
- trees
- atlas creation
- geometry building
- scene setup
- camera loop

Let's write the code, commenting each part.

I need to ensure the code is syntactically correct. Let's start constructing it.

Note: In the heightmap, I store `heights[x][z]` maybe as `heights[x*WORLD_SIZE + z]`.

Let's write `noise2D`:

```js
function makeNoise2D(seed) {
  const rng = mulberry32(seed);
  const perm = new Uint8Array(512);
  for (let i=0;i<256;i++) perm[i]=i;
  for (let i=255;i>0;i--) {
    const j=Math.floor(rng()*(i+1));
    [perm[i],perm[j]]=[perm[j],perm[i]];
  }
  for (let i=0;i<512;i++) perm[i+256]=perm[i];
  function fade(t){return t*t*(3-2*t);}
  function gradient(h, x, y) {
    const gradients=[[1,1],[-1,1],[1,-1],[-1,-1]];
    const g=gradients[h&3];
    return x*g[0]+y*g[1];
  }
  function noise(x,y) {
    const X=Math.floor(x)&255, Y=Math.floor(y)&255;
    x-=Math.floor(x); y-=Math.floor(y);
    const u=fade(x), v=fade(y);
    const a=perm[X]+Y, b=perm[X+1]+Y;
    const g1=perm[a&255], g2=perm[b&255], g3=perm[( (a&255)+1 )&255], g4=perm[((b&255)+1)&255];
    // no, need to use gradient at perm positions
    const gradA = gradients[g1&3]; ...
  }
}
```

This is getting complex. For simplicity, use value noise with hashed values.

I'll implement simpler value noise:

```js
function valueNoise(x,z,seed) {
  const X = Math.floor(x), Z = Math.floor(z);
  const fx = x-X, fz = z-Z;
  const sx = fx*fx*(3-2*fx);
  const sz = fz*fz*(3-2*fz);
  function hash(x,z) {
    let h = x*374761 + z*668265263 + seed*1274126177;
    h = (h ^ (h>>13)) * 1274126177;
    return ((h ^ (h>>16)) >>> 0) / 4294967295;
  }
  const v00=hash(X,Z), v10=hash(X+1,Z), v01=hash(X,Z+1), v11=hash(X+1,Z+1);
  return lerp(lerp(v00,v10,sx), lerp(v01,v11,sx), sz);
}
```

This works well and compact. The seed makes it unique.

For layered noise:

```js
function fbm(x,z,seed) {
  const octaves=4;
  let value=0, freq=1, amp=1, maxVal=0;
  for (let i=0;i<octaves;i++) {
    value += amp * valueNoise(x*freq, z*freq, seed+i*1000);
    freq *= 2.1;
    amp *= 0.55;
    maxVal += amp;
  }
  return value/maxVal; // 0..1 approximately
}
```

Good.

Now the code for `heightAt`:

```js
function heightAt(x,z) {
  let n = fbm(x*0.05, z*0.05, seed);
  n = n*n*1.5; // bias to lowlands
  let h = Math.floor( n * 30 + 5 );
  return Math.max(1, Math.min(MAX_HEIGHT-1, h));
}
```

Keep within 1..39.

Now, building worldData and filling terrain.

### Chunk geometry building

Let's define the face data arrays as objects with positions, normals, uvs, colors.

In `buildChunk(cx,cz,transparent)`:

```js
const positions=[], normals=[], uvs=[], colors=[];
for (let x=0; x<16; x++) {
  for (let z=0; z<16; z++) {
    for (let y=0; y<MAX_HEIGHT; y++) {
      const wx = cx*16+x, wz=cz*16+z;
      const type = getBlock(wx,y,wz);
      if ((type===AIR) || (type===WATER)!==transparentWater) continue;
      // For opaque geometry, skip WATER; for transparent, only WATER.
      // Actually, if transparent flag true, only add water; if false, add non-water.
      // But if type is WATER and transparent true, add.
      // if (transparent) { if (type !== WATER) continue; } else { if (type === WATER) continue; }
      for (let face=0; face<6; face++) {
        const dx=FACES[face][0], dy=FACES[face][1], dz=FACES[face][2];
        const neighbor = getBlock(wx+dx, y+dy, wz+dz);
        let drawFace;
        if (type === WATER) {
          drawFace = neighbor === AIR;
        } else {
          drawFace = neighbor === AIR || (neighbor === WATER && type !== WATER); // solid faces next to water are drawn
        }
        if (drawFace) {
          addFace(...);
        }
      }
    }
  }
}
```

But the solid faces adjacent to water: If the neighbor is water, from the solid block's side, we draw the solid face. But in the transparent pass, the water block also has faces. The solid geometry and water geometry are in separate meshes. We need to decide which one goes into which geometry regardless of neighbor. In our loop, for a solid block, if neighbor is water, we generate the solid face, which goes into the opaque mesh. For a water block, if neighbor is air, we generate a water face, which goes into the transparent mesh. Good.

But for a solid block adjacent to water, the solid face is on the boundary between solid and water. When seen from outside (air), the solid face may be hidden behind the transparent water? Actually, since the water is transparent, you'd see the solid face from outside only if the water is between the camera and the solid. But if the solid face is adjacent to water, then from above the water, the solid face is below the water surface and visible through the water. So generating it is correct.

Now, what if neighbor is AIR and type is solid: draw face. That's the surface.

The `getBlock` function for neighbors outside the world: return AIR. This means the sides of the world will have faces generated (edges), which is fine.

Now, `addFace` to push the face vertices.

I'll define `FACE_DIRS` and the corner tables.

```js
const FACE_DIRS = [
  {dir:[1,0,0], normal:[1,0,0]}, // px
  {dir:[-1,0,0], normal:[-1,0,0]},
  {dir:[0,1,0], normal:[0,1,0]},
  {dir:[0,-1,0], normal:[0,-1,0]},
  {dir:[0,0,1], normal:[0,0,1]},
  {dir:[0,0,-1], normal:[0,0,-1]},
];
```

For each face, the four corners. I'll manually define the corners as above.

Let's define the `FACE_CORNERS` array matching the faces list (0 px, 1 nx, 2 py, 3 ny, 4 pz, 5 nz). I previously listed them.

Now brightness array: [+X]=0.6, [-X]=0.6, [+Y]=1.0, [-Y]=0.5, [+Z]=0.8, [-Z]=0.8.

Face UVs: I need four UV corners per face such that v goes upward. I'll define a table `FACE_VERTEX_UVS` containing for each of the 4 corners the (u,v).

Since I already defined corners with uv in the face table, I can just use those.

Let's construct a `FACES` array (similar to above) where each entry has `normal`, `corners: [{pos:[dx,dy,dz], uv:[u,v]}, ...]`. Note that the uv values are in 0..1. These are relative to the block face, where (0,0) is bottom-left of the face (when viewed from outside) and (1,1) is top-right. Then for a given block type and cell, we add the cell offset to uv.

Now `addFace`:

```js
function addFace(chunk, x,y,z, face, type) {
  const f = FACES[face];
  const brightness = FACE_BRIGHTNESS[face];
  const cell = getCellForFace(type, face); // {u0,v0,u1,v1}
  const start = positions.length/3;
  for (let i=0; i<4; i++) {
    const p = f.corners[i].pos;
    positions.push(x+p[0], y+p[1], z+p[2]);
    normals.push(...f.normal);
    // color
    colors.push(brightness,brightness,brightness);
    // uv
    const u = cell.u0 + f.corners[i].uv[0] * cell.w;
    const v = cell.v0 + f.corners[i].uv[1] * cell.h;
    uvs.push(u,v);
  }
  // push indices for two triangles (but with duplicated verts, we need to create vertices as 6 instead of 4, or use index).
}
```

Since we're using non-indexed BufferGeometry (no index), we need exactly 3 vertices per triangle. We can push the 4 vertices and duplicate them into 6. Let's do that:

```js
const idx = f.corners;
// triangle 1: idx0, idx1, idx2
// triangle 2: idx0, idx2, idx3
for (const [i0,i1,i2] of [[0,1,2],[0,2,3]]) {
   pushVertex(idx[i0]); // the vertex data from above
   pushVertex(idx[i1]);
   pushVertex(idx[i2]);
}
```

So we'll push the 4 vertices in order, but only after we've pushed all positions? No, we need to duplicate. Alternatively, we can build arrays and then for each triangle, push the 3 vertices from the already-added 4. Let me first push 4 vertices into the chunk arrays, then immediately read them back? Too messy.

Better: use indexed geometry: push 4 vertices, and add indices `[start,start+1,start+2, start,start+2,start+3]` to a central index array. The final BufferGeometry can be indexed. This is memory efficient and avoids duplication. Let's do that.

So chunk has `positions`, `normals`, `uvs`, `colors`, and `indices`.

When adding a face, record `start = positions.length/3`, push 4 vertices, then push indices.

This results in indexed geometry, good.

`addFace`:
```js
function addFace(geo, x,y,z, face, type) {
  const f = FACES[face];
  const brightness = FACE_BRIGHTNESS[face];
  const cell = getCellForFace(type, face);
  const start = geo.positions.length/3;
  for (let i=0; i<4; i++) {
    const p = f.corners[i].pos;
    geo.positions.push(x+p[0], y+p[1], z+p[2]);
    geo.normals.push(...f.normal);
    geo.colors.push(brightness,brightness,brightness);
    const u = cell.u0 + f.corners[i].uv[0] * cell.w;
    const v = cell.v0 + f.corners[i].uv[1] * cell.h;
    geo.uvs.push(u,v);
  }
  geo.indices.push(start, start+1, start+2, start, start+2, start+3);
}
```

Now `getCellForFace(type, face)`:
- type GRASS, face top -> cell for grass_top (0)
- type GRASS, face bottom? Probably not visible if not exposed, but may happen. We can still use dirt for bottom. In our world, grass block is only at the surface, bottom may be adjacent to dirt or stone; since face culling removes faces between solids, bottom face often not drawn. But if drawn against air (e.g., on a floating island), bottom = grass_top would look odd; use dirt.
- type SAND, STONE, DIRT, SNOW -> same cell for all faces.
- type WOOD: top/bottom -> log_top; sides -> log_side.
- type LEAVES -> leaves cell.
- type WATER -> water cell.

We'll define a function using a switch.

Now the atlas cells:
Let's assign cell indices:
0: grass_top
1: grass_side
2: dirt
3: stone
4: sand
5: snow
6: log_side
7: log_top
8: leaves
9: water

Atlas grid 4x4, so cells arr in row-major from top-left. I'll fill them in order above in the array and draw them by index.

Now our `getCellForFace` returns a block's cell for a given face. But both opaque and transparent use same water cell.

Now `buildChunkGeometry(cx,cz,transparent)`:
- Create `geo = {positions:[], normals:[], uvs:[], colors:[], indices:[]}`
- Loop over blocks in chunk (x,z,y).
- `type = getBlock(wx,y,wz)`
- If type === AIR, continue.
- If transparent is true and type !== WATER or if transparent false and type === WATER, continue.
- For each face, check neighbor with `getBlock` and draw as described.
- If any face drawn, addFace...

After loops, set positions to Float32Array, etc. Create a BufferGeometry:
```js
const geometry = new THREE.BufferGeometry();
geometry.setAttribute('position', new THREE.Float32BufferAttribute(geo.positions,3));
...
geometry.setIndex(geo.indices);
return geometry;
```

If no vertices, return new THREE.BufferGeometry().

### Important: getBlock out of bounds

For `getBlock(x,y,z)`, treat x,z outside as AIR. This means the edges of the world will have side faces. But also for tree leaves that extend beyond the world, they'd be clipped? Since block placement in setBlock ignores out-of-bounds, leaves may be missing at edges. Fine.

### Water rendering

The water geometry uses the same atlas, but the blue cell. Water block geometry needs faces against air only. But water also has faces against other water blocks (internal faces) which we skip. For a single block of water on top of a tall cliff, faces on top/sides and bottom? It will look like a transparent cube. The `depthWrite:false` will make the water surface semi-transparent.

### There may be a problem: transparent water faces in chunks next to solid chunks; if camera sees through water, the solid geometry is behind, fine. But if the water is at the surface of a lake, its top face is drawn. The faces below water against solid (stone) are not drawn because neighbor != AIR, so you only see the water surface from above. From below, you'd see the bottom face of water if there's air below. Water bottom face should be drawn when facing air below (e.g., a floating water block). That's okay.

### 11. Animation loop

```js
const clock = new THREE.Clock();
function animate() {
  requestAnimationFrame(animate);
  const t = clock.getElapsedTime();
  if (cameraCurve) {
    const pos = cameraCurve.getPoint(t*0.05); // etc
    camera.position.copy(pos);
    const target = cameraCurve.getPoint(t*0.05 + 0.01);
    camera.lookAt(target);
  }
  // animate clouds
  clouds.forEach...;
  renderer.render(scene,camera);
}
```

Since building the world synchronously may take a moment, and the render loop starts after, that's fine.

### 12. Final code

The complete script is long. I'll write it carefully.

Because generating the world in a single script on load will block the page for a second; acceptable.

One issue: we're using both opaque and transparent geometries for each chunk. We can create a `Chunk` object with two meshes. Add them all to scene.

Chunk key: `cx_${cx}_cz_${cz}`.

Now, for performance, we might want to cull chunks outside camera view, but with 64 chunks it's fine.

Now let's write the actual code in the answer.

Note: I won't include the full 3D noise implementation details for each texture due to length, but I'll include enough to create the atlas.

Let's start writing the final answer.