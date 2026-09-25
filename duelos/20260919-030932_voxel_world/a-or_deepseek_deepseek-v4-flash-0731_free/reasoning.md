User wants a Minecraft-style voxel world with:
1. Procedurally generated terrain (128x128 columns) using layered noise
2. Grass-topped hills, snowy mountain peaks, sandy beaches, lake/sea with semi-transparent water
3. Trees made of wood and leaf blocks
4. Per-face shading for blocks
5. Procedural pixel-art textures on canvas
6. Sky with sun, soft distance fog, block clouds that drift
7. InstancedMesh or merged geometry for performance
8. Cinematic flythrough camera
9. requestAnimationFrame timestamp for animation
10. Full-window canvas with resizing
11. Auto-starts, no interaction

Let me build this step by step.

I'll use:
- Three.js r186 from import map
- SimplexNoise or implement my own noise (I'll use a simple noise implementation)
- InstancedMesh for terrain blocks
- Canvas-based textures

Let me think about the architecture:

1. **Noise generation**: I'll implement a simple value noise or Perlin noise for terrain height, and use fBm (fractal Brownian motion) for layered noise.

2. **Terrain**: 128x128 columns. Generate height map with noise. Classify blocks:
   - Under water level: sand or underwater sand
   - At terrain height: grass (if not underwater), snow (if high), sand (if near water), stone (if high altitude)
   - Below surface: dirt, then stone deeper

3. **Water**: Semi-transparent blue plane or boxes at water level.

4. **Trees**: Scattered on grass blocks, wood trunk + leaf blocks.

5. **Textures**: Create pixel-art textures on canvas for each block type:
   - Grass (top, side, bottom)
   - Dirt
   - Stone
   - Sand
   - Snow
   - Wood (log)
   - Leaves
   - Water

6. **Per-face shading**: Multiply texture colors by face-specific light intensity (top = 1.0, front/back = 0.8, left/right = 0.7, bottom = 0.5, etc.) or use different shading per face.

7. **Rendering**: Use InstancedMesh for each block type, or merge geometries. InstancedMesh is easier.

8. **Camera**: Smooth path using Catmull-Rom curve or Bezier curves. Use THREE.CatmullRomCurve3.

9. **Clouds**: Semi-transparent white cubes or planes drifting.

10. **Sky**: Gradient sky using scene.background or shader.

11. **Fog**: THREE.Fog for distance fog.

Let me think about the texture generation more carefully.

For pixel-art textures, I'll create small canvases (like 16x16) and draw pixel patterns per block type.

Block types and their textures:
- Grass top: green with random lighter green pixels
- Grass side: dirt with green grass overhang
- Dirt: brown with variation
- Stone: gray with lighter/darker patches
- Sand: tan/yellow with variation
- Snow: white with light blue tint
- Wood log: brown with vertical stripes
- Wood top: concentric rings
- Leaves: dark green with variation
- Water: blue with some transparency

Per-face shading: I'll create separate materials or use instance color to tint faces. Actually, with InstancedMesh, I can set per-instance colors. But for per-face shading, I need to either:
1. Create separate InstancedMesh for each face direction
2. Use a custom shader
3. Use different materials for each face direction

Actually, the simplest approach with merged geometry is to create geometry with per-face vertex colors for shading. But with InstancedMesh, we can use instance colors to tint the whole block, but that doesn't give per-face shading within a block.

Let me think about this differently. The standard Minecraft-style approach:
- For each block type, create a box geometry with 6 faces, each face having its own material (or UV mapping).
- Use MeshLambertMaterial or MeshPhongMaterial which gives natural directional shading.
- Apply textures via materials.

Actually, with MeshLambertMaterial or MeshPhongMaterial, lighting gives per-face shading automatically. But to get that "Minecraft look" with per-face brightness baked in, we can use MeshBasicMaterial with different colors per face, or we can use a custom material.

Let me use MeshLambertMaterial with a directional light - that will give natural face shading. But to make it more Minecraft-like, I'll bake the face shading into the textures or use vertex colors.

Actually, the cleanest approach:
- Create box geometries with 6 different materials (one per face) - this is the traditional Minecraft rendering approach.
- Each material uses the procedural texture.
- For per-face shading, multiply the texture by a brightness factor.

But creating individual boxes for every block would be too many draw calls. So I need to merge geometries or use InstancedMesh.

With InstancedMesh, I can have multiple faces with different materials using a group of meshes (one InstancedMesh per face direction), or use a single material with UVMapping and a texture atlas.

Let me go with the merge approach: Create merged geometry for each block type with per-face UVs and per-face shading colors.

Actually, let me reconsider. The most straightforward approach:

For each visible block:
- Create a BoxGeometry with 6 materials (one per face: +x, -x, +y, -y, +z, -z)
- Apply per-face material shading by setting material colors
- For InstancedMesh, we'd need 6 InstancedMeshes (one per face) or use a different approach.

Hmm, actually with InstancedMesh, I can create one InstancedMesh per block type, using a material with vertex colors baked for face shading. Let me use merged geometry instead:

Merged geometry approach:
1. For each block type, create a box geometry where each face has baked-in vertex colors
2. Update the geometry into a BufferGeometry
3. Add the geometry to a Mesh with a texture material
4. Use two sets of UVs: one for the texture, and vertex colors for face shading

Actually, let me use a simpler approach:

For each block type, create a BoxGeometry with 6 materials. Each material is a MeshLambertMaterial with a texture. For face shading, I'll bake the face brightness into the material color:

```javascript
// For each face direction:
const faceColors = {
  px: 0.8, nx: 0.8, // right/left
  py: 1.0, ny: 0.5, // top/bottom
  pz: 0.7, nz: 0.7  // front/back
};
```

But this requires 6 materials per box geometry, which complicates InstancedMesh.

Alternative: Use a single MeshLambertMaterial with vertex colors for face shading, and texture in the material. Create a box geometry, iterate its faces (or position attributes for BufferGeometry), and set vertex colors based on face direction.

In three.js r186, BoxGeometry creates a BufferGeometry with position, normal, uv attributes. I can add a color attribute:

```javascript
const geo = new THREE.BoxGeometry(1, 1, 1);
const positionAttribute = geo.getAttribute('position');
const colors = new Float32Array(positionAttribute.count * 3);
for (let i = 0; i < positionAttribute.count; i++) {
  // Determine which face based on normal
  const normal = new THREE.Vector3();
  // Get normal from position? Need accessor for normals
}
```

Actually, BoxGeometry has a normal attribute. I can iterate normals to determine face direction and assign colors.

But wait, with InstancedMesh, I can't have per-instance different geometry. I'd need to use the same geometry for all blocks of the same type. So I should create a single BoxGeometry with vertex colors for face shading for each block type.

Hmm, but if I want different block faces to use different textures (like grass block has different top/side/bottom textures), I need UV mapping to select the right texture from an atlas or use multiple materials.

Let me think of a cleaner approach:

**Approach: Texture Atlas + InstancedMesh + Face Shading via Vertex Colors**

1. Create a texture atlas containing all block textures.
2. Map UVs of the BoxGeometry to the correct region of the atlas for each face.
3. Use vertex colors for face shading (darker on sides, brighter on top).
4. Use one InstancedMesh for all blocks of each type (or for all visible blocks of same type), or even one InstancedMesh for all blocks with instance attributes for texture type.

Actually, let me simplify even more:

**Simplest approach: Merged Geometry per Block Type**

For each block type:
1. Generate a CanvasTexture for that block type (grass side, dirt, stone, etc.)
2. Create a MeshLambertMaterial with that texture
3. For each block of that type, create a BoxGeometry, set per-face vertex colors for shading, and merge into a single BufferGeometry
4. Create one Mesh for each block type with the merged geometry

This avoids the texture atlas complexity and the InstancedMesh limitation with multiple-materials-in-a-single-instance.

But for the grass block, the top and bottom faces need different textures than the sides. So I'd need either:
- A texture atlas for the grass block (top has green, side has dirt+green, bottom has dirt)
- Or separate the geometry: top faces use one geometry, side faces use another.

Let me just use the texture atlas approach. It's cleaner.

Actually, let me reconsider. Let me use a material array for each BoxMesh:

```javascript
const materials = [
  pxMaterial, // +x
  nxMaterial, // -x
  pyMaterial, // +y (top)
  nyMaterial, // -y (bottom)
  pzMaterial, // +z
  nzMaterial, // -z
];
```

For grass blocks, the top material is grass top, the bottom is dirt, and the sides are grass side.

For MergedMesh, we can merge geometries with different material groups. But this gets complicated.

Let me go back to fundamentals:

Option 1: Use a Texture Atlas with a single material for all block types.
- Create a canvas with all block textures arranged in a grid.
- For each block geometry, set UVs to point to the correct texture in the atlas.
- The grass block uses different UV regions for different faces.

This is the most Minecraft-like approach.

Option 2: Use InstancedMesh with per-block-type materials, and use groups within the InstancedMesh to handle different faces.

Actually, let me reconsider the whole approach:

Since we have many block types and need different textures per face, and we want performance:

**Use merged geometry with multi-material groups.**

1. For each block type, compute which texture to use for each face.
2. Create a merged geometry where vertices for different faces reference different material indices.
3. Use a material array with all textures.

But this is complex. Let me use a simpler approach:

**Use one InstancedMesh per block-type/face combination** - this gives maximum flexibility but too many draw calls.

Actually, 10 block types * 6 faces = 60 meshes, but we only need meshes for faces that appear:
- Grass: 3 materials (top, bottom, side)
- Water: 1 material (or 6 same)
- Wood: 3 materials (top/bottom, sides)
- Leaves: 1 material
- Stone: 1 material
- Dirt: 1 material
- Sand: 1 material
- Snow: 1 material

But InstancedMesh with a MeshLambertMaterial and one material per mesh.

OK, let me step back and go with a practical approach:

**Practical approach: Use InstancedMesh for each block type, with per-face shading via vertex colors.**

For blocks with different textures per face (like grass), I'll use a custom approach:
- For the grass block, create a geometry with per-face UV mapping to a texture atlas canvas.

Actually, you know what, let me use a texture atlas. Here's my plan:

1. Create a 16x16 pixel texture atlas with all block textures.
2. Each block face maps to a 16x16 pixel region in the atlas.
3. Use a single material with the atlas texture for all blocks.
4. Use vertex colors for per-face shading.

5. Use InstancedMesh with the single material.

This is the cleanest approach.

Atlas layout (4x4 grid of 16x16 pixel textures, 64x64 total):
- 0,0: dirt
- 1,0: grass_side
- 2,0: grass_top
- 3,0: stone
- 0,1: sand
- 1,1: wood_side
- 2,1: leaves
- 3,1: snow
- 0,2: water
- 1,2: wood_top
- 2,2: grass_bottom (same as dirt)
- ... 

Actually, let me simplify and just create separate materials. With merged geometry, we can use geometry groups to reference different materials.

OK let me try a different, simpler approach:

**Simplest working approach:**

For each block type, create a BoxGeometry. For each face of the box, set UVs to map to the appropriate texture region in a texture atlas. Add vertex colors for per-face shading. Then use InstancedMesh for all blocks of the same type.

Wait, but if I use a texture atlas, a single material can be used for all block types. The UVs on the geometry will select which texture region is used.

But with InstancedMesh, all instances use the same geometry. So if I use a BoxGeometry with UVs mapped to the atlas, and use the same geometry for all block types... the UVs need to be different per texture type.

Solution: Use a custom attribute for texture type, and a shader that samples the atlas based on the texture type.

This is getting complicated. Let me use a simpler, more pragmatic approach:

**Pragmatic approach: Merged geometry with multi-material groups.**

For each block type (dirt, grass, stone, wood, leaves, sand, snow, water), create a merged geometry. Use one InstancedMesh per block type.

For grass blocks, create a custom BoxGeometry where different faces have different UVs pointing to different atlas regions. Add vertex colors for face shading.

Actually, let me simplify even further. I'll use separate Texture objects per block face direction:

For each block type, create 6 materials (right, left, top, bottom, front, back). Create a BoxGeometry per block type. Each material is a MeshLambertMaterial with a CanvasTexture.

Then, for each block type:
- Create a BufferGeometry from the BoxGeometry
- Merge instances of this geometry at different positions using InstancedMesh

This gives us 6 materials per block type, but since it's InstancedMesh, we need only one mesh per block type.

In three.js, InstancedMesh supports multiple materials using `material` array and mesh groups. Actually, InstancedMesh supports `setMaterial` and groups. But the base geometry has groups that select which material to use. So:

```javascript
const geo = new THREE.BoxGeometry(1, 1, 1);
// By default, BoxGeometry has 6 groups (one per face).
// Each group references a material index.
```

When using InstancedMesh with geometry groups, the material index in each group selects which material from the material array to use. This is perfect.

Wait, but InstancedMesh takes one material. Actually no, InstancedMesh can take an array of materials and uses geometry groups to select which material to use. Let me check...

In three.js, `InstancedMesh` extends `Mesh`. The `Mesh`'s `material` can be an array. The geometry's groups specify which material index to use for each set of triangles.

So I can:
1. Create a BoxGeometry (which has 6 groups, one per face).
2. Create an array of 6 materials (one per face).
3. Create an InstancedMesh with the BoxGeometry and the material array.
4. For each instance, set the transformation matrix to place the block.

This handles per-face textures. For per-face shading, I can set the material colors:
```javascript
const brightness = [0.8, 0.8, 1.0, 0.5, 0.7, 0.7]; // right, left, top, bottom, front, back
```

But MeshLambertMaterial will also get lighting from the scene's lights. So if I add a directional light and ambient light, the faces will be shaded naturally. That might be enough. The per-face shading requirement says "per-face shading so the cube shapes read clearly". Directional lighting will do this.

OK, let me go with this approach:

**Final approach:**

1. Generate procedural textures on canvas for each block face:
   - grass_top, grass_side, dirt, stone, sand, snow, wood_side, wood_top, leaves, water

2. Create a BoxGeometry for each block type (or just use one BoxGeometry since all are 1x1x1).

3. For each block type, create 6 materials (right, left, top, bottom, front, back) using MeshLambertMaterial with the appropriate texture.

4. Use InstancedMesh for each block type. Set instance matrices for all blocks of that type.

5. Add lighting:
   - AmbientLight (soft fill)
   - DirectionalLight (sun)

6. Add fog: THREE.Fog

7. Camera: Create a smooth path with THREE.CatmullRomCurve3 through the landscape.

8. Water: Semi-transparent blue material with a slight animation.

9. Clouds: A few white, semi-transparent cube meshes or low-poly plane clouds that drift.

10. Sky: Set scene.background to a gradient color. Use a skybox or just a background color with fog.

Let me think about the sky. Three.js has a Sky addon, but since we're keeping it simple, I'll use:
- scene.background = new THREE.Color(0x87CEEB) // sky blue
- scene.fog = new THREE.Fog(0x87CEEB, 50, 250)

For the sun, I'll add a sprite or a mesh (a small yellow circle) positioned far away.

Now let me implement this.

**Texture Generation:**

I'll create a function that generates a 16x16 pixel canvas texture with some noise:

```javascript
function createTexture(baseColor, variation, getPixel) {
    const canvas = document.createElement('canvas');
    canvas.width = 16;
    canvas.height = 16;
    const ctx = canvas.getContext('2d');
    for (let y = 0; y < 16; y++) {
        for (let x = 0; x < 16; x++) {
            let color = getPixel(x, y);
            ctx.fillStyle = color;
            ctx.fillRect(x, y, 1, 1);
        }
    }
    const texture = new THREE.CanvasTexture(canvas);
    texture.magFilter = THREE.NearestFilter;
    texture.minFilter = THREE.NearestFilter;
    return texture;
}
```

**Block type enum:**

```javascript
const BlockType = {
    AIR: 0,
    GRASS: 1,
    DIRT: 2,
    STONE: 3,
    WOOD: 4,
    LEAVES: 5,
    SAND: 6,
    SNOW: 7,
    WATER: 8,
};
```

**Noise implementation:**

I'll implement a simple 2D value noise or use a seeded perlin noise.

```javascript
// Simple hash-based noise
function hash2D(x, y, seed) {
    let n = x * 374761393 + y * 668265263 + seed;
    n = (n ^ (n >> 13)) * 1274126177;
    return (n ^ (n >> 16)) / 2147483648;
}

function smoothNoise(x, y, seed) {
    const ix = Math.floor(x);
    const iy = Math.floor(y);
    const fx = x - ix;
    const fy = y - iy;
    // Smoothstep
    const sx = fx * fx * (3 - 2 * fx);
    const sy = fy * fy * (3 - 2 * fy);
    const v00 = hash2D(ix, iy, seed);
    const v10 = hash2D(ix+1, iy, seed);
    const v01 = hash2D(ix, iy+1, seed);
    const v11 = hash2D(ix+1, iy+1, seed);
    return lerp(lerp(v00, v10, sx), lerp(v01, v11, sx), sy);
}

function fbm(x, y, octaves, seed) {
    let value = 0;
    let amplitude = 1;
    let frequency = 1;
    let maxValue = 0;
    for (let i = 0; i < octaves; i++) {
        value += smoothNoise(x * frequency, y * frequency, seed) * amplitude;
        maxValue += amplitude;
        amplitude *= 0.5;
        frequency *= 2;
    }
    return value / maxValue;
}
```

**Terrain Generation:**

```javascript
const WORLD_SIZE = 128;
const WATER_LEVEL = 24;
const SEA_LEVEL = 20;

function generateHeight(x, z) {
    const h = fbm(x * 0.05, z * 0.05, 4, 1234);
    const hills = Math.pow(h, 1.5) * 60;
    const base = 20;
    return base + hills;
}
```

Let me refine:
- Terrain height: base 20, hills up to 80 or so.
- Water level at 24.
- Beach level: blocks near water level are sand.
- Grass on top when height > water level.
- Snow on peaks when height > 60.

Actually, let me make it more interesting:
- Continentalness: large-scale noise for continents
- Erosion: smaller-scale noise for detail

Let me use:
```javascript
function generateHeight(x, z) {
    const continentalness = fbm(x * 0.01, z * 0.01, 4, 1000);
    const hills = fbm(x * 0.05, z * 0.05, 3, 2000);
    let height = 20 + continentalness * 30 + hills * 30;
    if (height < 0) height = 0;
    return height;
}
```

Hmm, let me tune this properly:

Base terrain:
- Low areas: around y=15-25
- Plains: y=25-35
- Hills: y=35-60
- Mountains: y=60-100

Let me use:
```javascript
function generateHeight(x, z) {
    const h1 = fbm(x * 0.02, z * 0.02, 4, 1234);
    const h2 = fbm(x * 0.08, z * 0.08, 3, 5678);
    const height = 24 + h1 * 30 + h2 * 15;
    return height;
}
```

Water level at 20, so:
- Below 20: underwater, sand at bottom, water above
- 20-24: beach, sand on top
- 24-60: grass
- 60+: snow

Wait, I need to think about this more carefully.

For a 128x128 world, the height range should be reasonable.

Let me define:
```javascript
const SEA_LEVEL = 24;
const BEACH_HEIGHT = 26; // Above this, grass; below, sand
const SNOW_HEIGHT = 55; // Above this, snow

function generateHeight(x, z) {
    let h = 0;
    // Large scale features
    h += fbm(x * 0.008, z * 0.008, 4, 42) * 80;
    // Medium detail
    h += fbm(x * 0.04, z * 0.04, 3, 43) * 10;
    // High detail
    h += fbm(x * 0.12, z * 0.12, 2, 44) * 3;
    // Normalize to around 30 center
    return h;
}
```

Actually, the fbm function I wrote returns values in [0, 1] on average around 0.5. So the height would be around 0.5 * 80 = 40. But with octaves, the range is [0, 1] but mostly around 0.5.

Let me get a better range: 

```javascript
function generateHeight(x, z) {
    const large = fbm(x * 0.01, z * 0.01, 4, 42) - 0.5; // [-0.5, 0.5]
    const detail = fbm(x * 0.04, z * 0.04, 3, 43) - 0.5;
    const height = 30 + large * 40 + detail * 15;
    return Math.max(1, height);
}
```

This gives heights from ~-25 to ~85, centered at 30.

Water at 20. So:
- Height < 20: underwater terrain (sand)
- 20 <= height < 22: beach (sand just above water)
- 22 <= height < 55: grass
- Height >= 55: snow on top

Let me also consider noise for terrain features like trees:

```javascript
function shouldPlaceTree(x, z, height) {
    if (height < 25 || height > 45) return false;
    const n = hash2D(x, z, 999);
    return n > 0.98;
}
```

OK, let me now plan the block layout.

**Block Layout:**

For each column (x, z):
1. Compute height = Math.floor(generateHeight(x, z))
2. The top block at height is the surface block:
   - If height < SEA_LEVEL: sand (or underwater sand?) — Actually let me think:
     - Underwater, the top block should be sand or gravel.
     - Just above water: sand (beach)
     - Higher: grass or snow
3. Below the top block: 4 blocks of dirt, then stone.
4. If underwater, fill from height+1 to SEA_LEVEL with water blocks.

Let me define:

```javascript
for (let x = 0; x < WORLD_SIZE; x++) {
    for (let z = 0; z < WORLD_SIZE; z++) {
        const height = Math.floor(generateHeight(x, z));
        const biome = getBiome(height);
        
        for (let y = 0; y <= Math.max(height, SEA_LEVEL); y++) {
            let blockType = BlockType.AIR;
            
            if (y === 0) {
                blockType = BlockType.STONE;
            } else if (y === height) {
                if (height < SEA_LEVEL - 1) {
                    blockType = BlockType.DIRT; // underwater
                } else if (height < SEA_LEVEL + 1) {
                    blockType = BlockType.SAND;
                } else if (height < SNOW_HEIGHT) {
                    blockType = BlockType.GRASS;
                } else {
                    blockType = BlockType.SNOW;
                }
            } else if (y < height) {
                if (y < height - 4) {
                    blockType = BlockType.STONE;
                } else {
                    blockType = BlockType.DIRT;
                }
            }
            
            // Override top blocks for snow
            if (y === height && height >= SNOW_HEIGHT) {
                blockType = BlockType.SNOW;
            }
            
            blocks[x][z][y] = blockType;
        }
        
        // Water
        if (height < SEA_LEVEL) {
            for (let y = height + 1; y <= SEA_LEVEL; y++) {
                blocks[x][z][y] = BlockType.WATER;
            }
        }
    }
}
```

Wait, I need to store blocks in a 3D array. For 128x128x80, that's about 1.3 million entries. That's fine.

Actually, I should only create meshes for blocks that have at least one exposed face (i.e., a neighbor is air or water).

**Mesh Generation:**

For each block position:
1. Get the block type.
2. If AIR, skip.
3. For each of the 6 directions, check the neighbor:
   - If neighbor is AIR or WATER (and current is not water), then the face is visible.
   - For water, only create face if adjacent block is AIR or has a different water level.

Actually, for simplicity, let me just check if the neighbor is AIR or WATER for solid blocks. For water, check if neighbor is AIR.

Then add an instance to the appropriate InstancedMesh.

But with InstancedMesh, we need to update the matrix for each instance. Let me count instances first, then create the InstancedMesh.

Actually, creating InstancedMesh with an initially small size and growing isn't straightforward (the `instanceMatrix` is fixed-size). So I need to count first:

1. Count visible faces for each block type.
2. Create InstancedMesh with the right counts.
3. Fill in the instances.

But wait, for per-face UV mapping (grass block), I need to store which face is which. In the BoxGeometry, faces are in groups. Each group corresponds to a material index.

Let me use the BoxGeometry with 6 groups and a material array.

For a simple case:
- Grass block: materials = [grassSide, grassSide, grassTop, dirt, grassSide, grassSide]
  - Right (+x): grassSide
  - Left (-x): grassSide  
  - Top (+y): grassTop
  - Bottom (-y): dirt
  - Front (+z): grassSide
  - Back (-z): grassSide

- Water: all faces water, translucent
- Wood: side=woodSide, top/bottom=woodTop
- Leaves: all leaves
- Stone: all stone
- Dirt: all dirt
- Sand: all sand
- Snow: all snow

For InstancedMesh with multiple materials, I need to create separate InstancedMesh for each material slot, or use a single InstancedMesh per block type with material array (which should work).

Wait, I just checked: `InstancedMesh` uses `setMatrixAt` for each instance, and the render uses the geometry groups and the material array of the mesh. So I can create one InstancedMesh per block type, with a material array (6 materials), and it should work.

Let me verify: In three.js, a Mesh with a material array works by using geometry groups (or "faces" in older versions). BoxGeometry has 6 groups, each with a material index. The Mesh material can be an array; each group renders with the material at the group's material index.

Yes, this works.

So my plan:

```javascript
// Create BoxGeometry
const boxGeometry = new THREE.BoxGeometry(1, 1, 1);

// For each block type, create an InstancedMesh
// with the same geometry but different materials.

function createInstancedMesh(materials) {
    return new THREE.InstancedMesh(
        boxGeometry,
        materials,
        0
    );
}
```

But I need to know the count first. So let me:

1. Iterate all blocks, determine visible faces.
2. For each block type, store a list of positions and which faces are visible.
3. Create InstancedMesh for each block type with the appropriate count.
4. Set instance matrices.

For each block position, if a face is visible:
- The instance matrix is a 4x4 transform placing the block at (x, y, z).
- The face visibility is determined by which materials are needed.

Wait, for InstancedMesh, we set the matrix for the whole instance (the block). We don't set per-face visibility. If some faces of a block are hidden (e.g., neighbor block), we could:
- Use a custom shader that discards hidden faces based on instance attributes.
- Or we can still render the full block and rely on the depth buffer to hide internal faces.

The Minecraft approach is to not render hidden faces. But with InstancedMesh, we can't easily do per-face culling. However, if we use a single InstancedMesh per block type, and the geometry has all 6 faces, then hidden faces will be rendered but then occluded by the depth buffer. This is less efficient but simpler.

For better performance, we can:
1. Create a separate InstancedMesh for each face of each block type that has visible faces.
2. Or use a custom geometry that includes only the visible faces.

Actually, let me go with a hybrid:
- Create one InstancedMesh per block type, but use a geometry that has all 6 faces.
- To reduce overdraw, we could use a custom shader with an "instance face visibility" attribute. But this adds complexity.

For simplicity and acceptable performance, let me just render all faces for all instances (including hidden ones). The depth buffer will handle occlusion correctly. For 128x128 world with average 30 blocks tall, that's ~500k blocks, but only the surface blocks would be rendered... Actually if we render all blocks including internal ones, that's 128*128*30 = 491,520 blocks. Each block has 12 triangles = ~5.9M triangles. That might be heavy but doable.

But wait, I'm creating InstancedMesh for each block type. If I add an instance for every non-air block, that's ~400k instances across all types. That's way too many for InstancedMesh (they're designed for hundreds or thousands, not hundreds of thousands).

Actually, InstancedMesh can handle thousands or tens of thousands, but 400k might be too slow.

So I should only render faces that are on the surface. But with InstancedMesh we need to render whole blocks, not individual faces.

Hmm, this is the classic problem. Let me think of a better approach.

**Option 1: Cull hidden blocks, but render all 6 faces of visible blocks.**
- Count blocks that have at least one exposed face.
- Add each such block once to its block type's InstancedMesh.
- Use depth buffer to handle face-level culling (which happens for faces that are between adjacent visible blocks).

This works well. The number of visible blocks is roughly the surface area of the terrain, which for 128x128 is a few thousand to ~10k. That's manageable.

But some blocks will have hidden faces between adjacent visible blocks. Those faces will be rendered but then depth-tested away. This is what Minecraft does with chunk "interior" faces when not culled. It's acceptable.

**Option 2: Use chunk-wise mesh generation.**
- Divide the world into chunks (e.g., 16x16x16).
- For each chunk, generate a merged geometry with only the exposed faces.
- Use multiple materials per chunk.

This is more complex but much more efficient. Since we need to write a lot of code, let me go with Option 1 for simplicity, but be smart about it:

1. Only add a block to its InstancedMesh if at least one of its 6 neighbors is AIR or WATER.
2. This reduces visible blocks significantly (from ~500k to ~20-30k for a 128x128 terrain).

The block count for visible blocks in a 128x128 terrain is roughly the sum of exposed surface blocks. With height averaging ~30, and 128x128 columns, the number of surface blocks is ~16,384. Each surface block is at most 1 block, but we also need edge blocks (below overhangs, etc.). In practice, maybe 2-3x that, so ~50k. That's manageable for InstancedMesh.

Actually wait, the interior blocks below the surface (dirt/stone) are NOT visible, so we only add the top few layers of each column. So the count is:
- Top surface block (grass/sand/snow): 128*128 = 16,384
- Below surface (dirt, a few blocks): ~2*128*128 = 32,768
- Exposed stone faces (cliffs): maybe a few thousand
- Water blocks: ~128*128*(SEA_LEVEL - terrain_height) for underwater columns = a few thousand

Total visible blocks: ~50k. That's fine for InstancedMesh.

Actually, let me be more careful. The bottom of the ocean is covered with sand, and the water above is blocks too. So:
- Sand blocks at ocean bottom: for a column with water, there's 1 sand block at the bottom.
- Water blocks: (SEA_LEVEL - terrain_height) blocks of water.

In the shallow parts, that's maybe 2-4 water blocks per column. Total: 128*128*~2 = 33k water blocks. Plus 16k sand blocks. Plus 16k surface blocks. Total ~65k.

Hmm, 16k water instances + 16k sand + 16k grass = 48k. Plus other types. Still manageable.

OK, let me go with this approach. But to reduce the instance count, let me only add blocks that have at least one visible face:

For each block (x, y, z):
1. Determine block type.
2. Check all 6 neighbors:
   - If any neighbor is AIR (and block is not WATER), the block is visible (or at least should be added).
   - If block type is WATER, check if neighbors are AIR (to expose the water surface).
3. If visible, add to the appropriate InstancedMesh.

Actually, for water, we need to render the water surface (top face) even if the block below is water. So water blocks at the surface need to be rendered.

Let me refine:
- For solid blocks: add to InstancedMesh if any neighbor is AIR or WATER.
- For water blocks: add always (they're cheap, and we need the surface).

Actually, this is getting complicated with different rules per block type. Let me use a simpler heuristic:
- Add a block to InstancedMesh if any neighbor is AIR.
- For water, add the block if the block above is AIR (surface water) or if a side neighbor is AIR.

Wait, I also need to consider that water should render even if neighbors are water but on the surface.

OK, let me simplify:
- For every block position in the world:
  - If it's AIR, skip.
  - If it's WATER:
    - Add to water InstancedMesh if any of the 4 horizontal neighbors is AIR, or if the block above is AIR. (This renders water surface and edges.)
  - For other blocks:
    - Add to their type's InstancedMesh if any of the 6 neighbors is AIR or WATER.

This should give good results.

Actually, hmm, for underwater sand, it's below water. If I add sand only when neighbor is AIR or WATER, then the sand at the bottom of the ocean will be added (neighbor above is WATER). And the water above will be added (neighbor above is AIR or side neighbor is AIR). Good.

But sand that is below 2 blocks of dirt won't be added, which is correct since it's not visible.

Let me implement this properly.

**Implementation plan:**

1. Generate height map: `heightMap[x][z]` for x,z in [0, 128).

2. Build 3D block array: `blocks[x][y][z]` where x,z in [0,128), y in [0, maxHeight+SEA_LEVEL_EXTRA).

   Actually, I'll compute the max height per column and also store the block types.

3. For rendering, use InstancedMesh.

Blocks to create:
- Grass (grass block with different textures per face)
- Dirt
- Stone
- Sand
- Snow (top is white, side is snow-covered grass?)
  - Actually, let me make snow blocks have snow texture on all faces. Or, more Minecraft-like: snow layer on top. Let me just make the block have snow texture on all faces.
- Wood log
- Leaves
- Water (semi-transparent)

For the grass block:
- Top: green grass texture
- Bottom: dirt texture
- Sides: dirt with green top edge (grass side)

For snow blocks (at mountain peaks):
- Top: snow (white)
- Sides: grass side with snow at top? Or just all snow.
- Actually, let me make them just snow blocks. The block type is "snow block", not a snow layer on grass.

Wait, the requirement says "snowy mountain peaks". So the top has snow, and the sides could be grass/stone with snow. Let me create a "snow" block type that is all white. The mountain peaks will have this block type on top.

Actually, Minecraft gives mountains a snowy grass block. Let me create:
- Snowy grass block: top is snow, sides are dirt with snow at the top, bottom is dirt.

This adds a new block type. But I already have a lot of block types. Let me keep it simple:
- At high altitude, use a single block type "snow block" with snow texture on all faces. Or, use grass block but with a snow_texture on top and snow_side on the sides.

To keep the block count reasonable, let me just use "snow" as a block type that replaces grass at high altitudes. The top is white, the sides are white-ish.

OK let me implement it now.

Actually, let me reconsider the texture approach. I was going to use separate materials per face direction for each block type. But with many block types, this means creating many materials. Let me count:

- Grass: 3 unique materials (top, side, bottom/dirt)
- Dirt: 1 material (all faces)
- Stone: 1 material
- Sand: 1
- Snow: 1 (all white)
- Wood: 2 (side, top/bottom)
- Leaves: 1
- Water: 1

Total unique materials: 3 + 1 + 1 + 1 + 1 + 2 + 1 + 1 = 11 materials.

That's fine. I'll create 11 CanvasTexture objects and 11 MeshLambertMaterial objects.

For the grass block, I'll use a material array: [grassSide, grassSide, grassTop, dirt, grassSide, grassSide].

For wood: [woodSide, woodSide, woodTop, woodTop, woodSide, woodSide].

For each block type, create an InstancedMesh with the material array (or a single material if the same on all faces).

Wait, InstancedMesh with material array: I need to make sure it works. Looking at three.js docs:

```javascript
const mesh = new THREE.InstancedMesh(geometry, material, count);
```
Where material can be an array. But the geometry must have groups that reference the material indices.

BoxGeometry from three.js creates groups automatically:
- Group 0: px (+x face)
- Group 1: nx (-x face)
- Group 2: py (+y face)
- Group 3: ny (-y face)
- Group 4: pz (+z face)
- Group 5: nz (-z face)

This is the standard order for BoxGeometry in three.js.

So for a grass block, I'd set:
```javascript
const grassMaterials = [sideMat, sideMat, topMat, bottomMat, sideMat, sideMat];
```

And for a wood block:
```javascript
const woodMaterials = [woodSideMat, woodSideMat, woodTopMat, woodTopMat, woodSideMat, woodSideMat];
```

This works.

**Per-face shading:**

To make faces read clearly, I'll set material colors:
```javascript
const faceShading = [0.8, 0.8, 1.0, 0.6, 0.7, 0.7];
```

And add lighting:
```javascript
const ambientLight = new THREE.AmbientLight(0x606060, 1);
scene.add(ambientLight);
const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
dirLight.position.set(50, 100, 50);
scene.add(dirLight);
```

Actually, if I use MeshLambertMaterial with textures, the material already uses scene lights. So I can rely on lighting for per-face shading. But to make it more pronounced, I can also bake face shading into the material color.

Wait, MeshLambertMaterial with textures: the texture is multiplied by the material color. So if I set material.color to a shade value per face, the texture will be tinted. This works.

Let me create a helper:

```javascript
function createFaceMaterials(textures, faceShading) {
    return textures.map((tex, i) => {
        const mat = new THREE.MeshLambertMaterial({ map: tex });
        mat.color = new THREE.Color(faceShading[i]);
        return mat;
    });
}
```

Hmm, but MeshLambertMaterial with a map will still use the map's color multiplied by the material color. So:
- material.color = 0xffffff means texture is unchanged.
- material.color = 0xcc8080 would tint the texture red-ish.

Actually, for per-face shading, I want to multiply by a gray value:
```javascript
mat.color = new THREE.Color(faceShading[i]); // e.g., 0xCCCCCC for 0.8
```
Since faceShading is a number like 0.8, `new THREE.Color(0.8)` would create a very dark color (0.8/255). I need to use `new THREE.Color().setHSL(0, 0, 0.8)` or `new THREE.Color(faceShading, faceShading, faceShading)`.

Or simpler: `material.color.set(faceShading)` where faceShading is a number like 0.8 which is treated as a grayscale value in set.

Let me check: `new THREE.Color(0.8)` - the constructor accepts `(r, g, b)`, `(hex)`, or `(color)`. If a single number is passed, it's treated as a hex number. 0.8 as a hex number is 0x000000? No, 0.8 in JS is 0.8, which when passed to Color is treated as 0, 0, 0 (rounds to 0).

So I should use `new THREE.Color(setHue)` or just clamp: `new THREE.Color(0.8, 0.8, 0.8)`.

I'll use:
```javascript
const faceShading = [
    new THREE.Color(0.8, 0.8, 0.8),  // px
    new THREE.Color(0.8, 0.8, 0.8),  // nx
    new THREE.Color(1.0, 1.0, 1.0),  // py (top, brightest)
    new THREE.Color(0.6, 0.6, 0.6),  // ny (bottom)
    new THREE.Color(0.7, 0.7, 0.7),  // pz (front)
    new THREE.Color(0.7, 0.7, 0.7),  // nz (back)
];
```

For each material:
```javascript
const mat = new THREE.MeshLambertMaterial({ map: texture });
mat.color.copy(faceShading[i]);
```

Actually, MeshLambertMaterial's color modulates the map color. So if I set color to gray 0.8, the map is darkened by 20%. Good.

But I also want some ambient light. Also, with a directional light, the face shading will be combined. Let me just use a set of materials with baked face shading as the color, and add a directional light that's mostly white but moderate intensity.

Hmm, but using MeshLambertMaterial with a light, the face lighting is affected by the light direction, which changes per face. This might give natural shading but could vary with light direction.

To get a consistent Minecraft look, I'll:
1. Disable directional lights, use only ambient light, and bake face shading into materials.
2. Or keep directional light and accept natural face shading.

Actually, let me use a directional light. In Minecraft, the sun lights up some faces differently (like top faces are brighter, sides are medium). This gives a 3D effect.

But to ensure consistent per-face shading regardless of camera angle, I'll use MeshLambertMaterial with a directional light positioned at a fixed angle. The top face will be brightest (facing up toward the light), sides will be medium, bottoms will be dark. This is exactly what we want.

However, there's an issue: MeshLambertMaterial's lighting is computed in world space, so if the light is at (50, 100, 50), the faces pointing toward that light will be lit. For a voxel world, this gives natural sun-like lighting.

But I also explicitly set material colors for face shading, which would multiply the texture. This double-darkening might make things too dark. Let me just use the directional light and maybe an ambient light for the unlit sides. The material color for all faces will be white (1,1,1) so it doesn't alter the texture.

For per-face shading to make blocks readable, I can bake it into the texture itself (e.g., for side textures, darken the bottom portion). Or I can set vertex colors.

Actually, let me go with:
- Material color = white for all faces
- Directional light: intensity 1.0, position (0.5, 1.0, 0.3)
- Ambient light: intensity 0.5

This gives good per-face shading naturally.

Let me test my understanding: A BoxGeometry with 6 faces, each with a MeshLambertMaterial. The top face has a normal pointing up, and the light comes from above, so it's bright. The side faces have normals pointing horizontally, so they get less light. The bottom face is dark. This creates the Minecraft-like per-face shading.

Actually, let me do both: Use the directional light for natural shading AND bake a small face-shading factor into the material color for extra clarity.

OK let me just write the code and stop overthinking.

**Per-block-type materials:**

I'll create a helper:

```javascript
function createBlockMaterials(materialSpec) {
    // materialSpec: array of 6 material indices or material objects
}
```

Let me create the textures first, then the materials, then the InstancedMeshes.

**Textures:**

I'll generate 16x16 textures.

```javascript
function createCanvasTexture(render) {
    const canvas = document.createElement('canvas');
    canvas.width = 16;
    canvas.height = 16;
    const ctx = canvas.getContext('2d');
    render(ctx);
    const texture = new THREE.CanvasTexture(canvas);
    texture.magFilter = THREE.NearestFilter;
    texture.minFilter = THREE.NearestFilter;
    texture.generateMipmaps = false;
    return texture;
}
```

Grass top:
```javascript
const grassTopTexture = createCanvasTexture((ctx) => {
    for (let y = 0; y < 16; y++) {
        for (let x = 0; x < 16; x++) {
            const g = 120 + Math.random() * 40 | 0;
            ctx.fillStyle = `rgb(40, ${g}, 40)`;
            ctx.fillRect(x, y, 1, 1);
        }
    }
    // Add some individual pixel variation
    for (let i = 0; i < 10; i++) {
        ctx.fillStyle = `rgba(255,255,255,0.1)`;
        ctx.fillRect(Math.random()*16|0, Math.random()*16|0, 1, 1);
    }
});
```

Dirt:
```javascript
const dirtTexture = createCanvasTexture((ctx) => {
    for (let y = 0; y < 16; y++) {
        for (let x = 0; x < 16; x++) {
            const v = 120 + Math.random() * 40 | 0;
            ctx.fillStyle = `rgb(${v*0.8|0}, ${v*0.6|0}, ${v*0.4|0})`;
            ctx.fillRect(x, y, 1, 1);
        }
    }
});
```

Hmm, let me use a helper function to generate base colors with randomness:

```javascript
function createPixelTexture(baseColor, variation, pixelFn) {
    return createCanvasTexture((ctx) => {
        for (let y = 0; y < 16; y++) {
            for (let x = 0; x < 16; x++) {
                if (pixelFn) {
                    ctx.fillStyle = pixelFn(x, y);
                } else {
                    const v = 1 + (Math.random() * 2 - 1) * variation;
                    const r = Math.max(0, Math.min(255, baseColor[0] * v)) | 0;
                    const g = Math.max(0, Math.min(255, baseColor[1] * v)) | 0;
                    const b = Math.max(0, Math.min(255, baseColor[2] * v)) | 0;
                    ctx.fillStyle = `rgb(${r},${g},${b})`;
                }
                ctx.fillRect(x, y, 1, 1);
            }
        }
    });
}
```

OK let me just write simple texture functions:

Grass top:
```javascript
ctx.fillStyle = '#5b8c3e';
for (let x = 0; x < 16; x++) {
    for (let y = 0; y < 16; y++) {
        const shade = 0.8 + Math.random() * 0.4;
        const r = 80 * shade | 0, g = 140 * shade | 0, b = 60 * shade | 0;
        ctx.fillStyle = `rgb(${r},${g},${b})`;
        ctx.fillRect(x, y, 1, 1);
    }
}
// Add lighter patches
for (let i = 0; i < 20; i++) {
    const x = Math.random() * 16 | 0, y = Math.random() * 16 | 0;
    ctx.fillStyle = 'rgba(255,255,255,0.1)';
    ctx.fillRect(x, y, 1, 1);
}
```

Grass side:
```javascript
// Dirt bottom + green top
for (let y = 0; y < 16; y++) {
    for (let x = 0; x < 16; x++) {
        const shade = 0.8 + Math.random() * 0.4;
        if (y < 3) {
            const r = 80 * shade | 0, g = 140 * shade | 0, b = 60 * shade | 0;
            ctx.fillStyle = `rgb(${r},${g},${b})`;
        } else {
            const v = 120 * shade | 0;
            ctx.fillStyle = `rgb(${v},${v*0.7|0},${v*0.5|0})`;
        }
        ctx.fillRect(x, y, 1, 1);
    }
}
```

And so on. This is going to be a lot of texture code, but that's fine.

**Camera Flythrough:**

I'll create a path using THREE.CatmullRomCurve3 or THREE.BezierCurve3, or even a custom Catmull-Rom curve through specified points:

```javascript
const curve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(-40, 30, -40),
    new THREE.Vector3(0, 25, 20),
    new THREE.Vector3(40, 40, 60),
    new THREE.Vector3(-20, 20, 80),
    new THREE.Vector3(-60, 35, 40),
    new THREE.Vector3(-20, 15, -20),
]);

const cameraPosition = curve.getPoint(t);
const lookAt = curve.getPoint(Math.min(t + 0.05, 1));
camera.position.copy(cameraPosition);
camera.lookAt(lookAt);
```

Or use a smooth path. I'll adjust points to fly above hills and between mountains.

**Clouds:**

Create a few groups of white cubes or planes:

```javascript
function createCloud() {
    const group = new THREE.Group();
    const cloudMaterial = new THREE.MeshLambertMaterial({ color: 0xffffff, transparent: true, opacity: 0.8 });
    // Randomly add boxes to form a cloud shape
    for (let i = 0; i < 6; i++) {
        const size = 4 + Math.random() * 6;
        const mesh = new THREE.Mesh(new THREE.BoxGeometry(size, 2, size * 0.6), cloudMaterial);
        mesh.position.set((Math.random()-0.5)*10, (Math.random()-0.5)*1, (Math.random()-0.5)*10);
        group.add(mesh);
    }
    return group;
}
```

Then add 10-20 clouds at random positions, drifting slowly.

**Sky:**

```javascript
scene.background = new THREE.Color(0x87CEEB);
scene.fog = new THREE.Fog(0x87CEEB, 80, 200);
```

**Sun:**

A glowing sphere or sprite:

```javascript
const sunMesh = new THREE.Mesh(
    new THREE.CircleGeometry(20, 16),
    new THREE.MeshBasicMaterial({ color: 0xffdd44 })
);
sunMesh.position.set(200, 150, -100);
sunMesh.lookAt(0, 0, 0);
scene.add(sunMesh);
```

Or use a sprite with a radial gradient.

Actually, for a simple sun, I'll use a sprite:

```javascript
const sunTexture = createSunTexture(); // canvas with radial gradient
const sunMaterial = new THREE.SpriteMaterial({ map: sunTexture, transparent: true });
const sun = new THREE.Sprite(sunMaterial);
sun.scale.set(50, 50, 1);
sun.position.set(200, 150, -100);
scene.add(sun);
```

Or just a large circle mesh.

Let me go with a circle geometry.

OK, this is a lot. Let me start writing the code.

Actually, before I start, let me reconsider the mesh generation more carefully.

For the block types, I'll define:

```javascript
const BLOCK_TYPES = {
    AIR: 0,
    GRASS: 1,
    DIRT: 2,
    STONE: 3,
    SAND: 4,
    SNOW_BLOCK: 5,
    WOOD: 6,
    LEAVES: 7,
    WATER: 8,
};
```

For each block type, I'll define the material index array:

```javascript
const BLOCK_MATERIALS = {
    [BLOCK_TYPES.GRASS]: [SIDE, SIDE, TOP, BOTTOM, SIDE, SIDE],
    // where SIDE=grass_side, TOP=grass_top, BOTTOM=dirt
    ...
};
```

Actually, let me use material indices rather than actual material objects. I'll create a global material array and use indices.

Let me define:

```javascript
const MAT_GRASS_TOP = 0;
const MAT_GRASS_SIDE = 1;
const MAT_DIRT = 2;
const MAT_STONE = 3;
const MAT_SAND = 4;
const MAT_SNOW = 5;
const MAT_WOOD_SIDE = 6;
const MAT_WOOD_TOP = 7;
const MAT_LEAVES = 8;
const MAT_WATER = 9;

const allMaterials = [];
let materialsCreated = false;

function initMaterials() {
    if (materialsCreated) return;
    allMaterials[MAT_GRASS_TOP] = createMat(grassTopTexture);
    // ... create all materials
    materialsCreated = true;
}
```

Then for each block type, define which materials to use per face:

```javascript
const BLOCK_TYPE_MATERIALS = {
    [BLOCK_TYPES.GRASS]: [MAT_GRASS_SIDE, MAT_GRASS_SIDE, MAT_GRASS_TOP, MAT_DIRT, MAT_GRASS_SIDE, MAT_GRASS_SIDE],
    [BLOCK_TYPES.DIRT]: [MAT_DIRT, MAT_DIRT, MAT_DIRT, MAT_DIRT, MAT_DIRT, MAT_DIRT],
    // ...
};
```

When creating InstancedMesh for a block type:
```javascript
const materials = BLOCK_TYPE_MATERIALS[type].map(i => allMaterials[i]);
const mesh = new THREE.InstancedMesh(geometry, materials, instances.length);
```

But InstancedMesh's `material` property is an array. When rendering, three.js uses the geometry groups to pick which material from the array to use. The material index in the group should be the index into the material array. Since I'm passing the materials for a specific block type, the arrays are 6 elements long, and BoxGeometry groups use 0-5. So this works.

Wait, but I need to assign 6 materials per BoxGeometry. The BoxGeometry has 6 groups. If I pass an array of 6 materials, each group will use the corresponding material. This is correct.

For the `MeshLambertMaterial`, when `map` is set, the map's color is multiplied by the material's color and the lighting. If I want the texture to be visible, I need either:
- material.map = texture; material.color = white (0xffffff)
- Or material.color = faceShading[i] to multiply

I'll use material.color = white for all, and rely on scene lights for shading.

But for extra "Minecraft per-face shading" as required, I can use material.color = faceShading[i] where faceShading values are gray levels.

Let me compute a good faceShading:
```javascript
const FACE_SHADING = [
    0.8, // px
    0.8, // nx
    1.0, // py
    0.5, // ny
    0.7, // pz
    0.7, // nz
];
```

And set material.color = new THREE.Color(FACE_SHADING[i], FACE_SHADING[i], FACE_SHADING[i]).

With MeshLambertMaterial, this color multiplies the texture. So the top face is full brightness, sides are 0.7-0.8, bottom is 0.5. Combined with the ambient + directional light, the result will be a nice per-face shading.

Actually, MeshLambertMaterial with color multiplication: the final color = mappedColor * color * light. If color is gray 0.8, the mappedColor is darkened by 20%. The light (ambient + directional) then further modulates.

If the ambient light is 0.5 and the directional light is 0.8, then the total light on a face depends on the normal orientation.

Let me set:
- Ambient light: 0x606060, intensity 0.6 (or just ambientColor 0x404040, intensity 0.6)
- Directional light: 0xffffff, intensity 0.7
- Material color: faceShading.

For the top face (normal up): light amount = ambient 0.6 + directional * dot(normal, lightDir). If lightDir is (0.5, 1, 0.3), dot(up, lightDir) = 1 * 1 = 1 *... wait, normalize lightDir. If lightDir = normalize(0.5, 1, 0.3), then dot(up, lightDir) = 1 * (1/length). Length = sqrt(0.25+1+0.09) = sqrt(1.34) ≈ 1.158. So dot = 0.863. Total light = 0.6 + 0.7*0.863 = 0.6 + 0.604 = 1.204. So top faces get full brightness (saturates).

For side faces: dot = |lightDir| * horizontal component. The horizontal components relative to lightDir... This gets complicated. Let me just set a directional light and let it do its thing.

Actually, let me simplify and not use material colors for face shading. Instead, rely on:
1. A strong directional light (sun) positioned above.
2. Ambient light for fill.

This gives natural Minecraft-like lighting where the top is bright, sides are medium, and bottom is dark. The "per-face shading" requirement is satisfied because different faces receive different light amounts.

But there's a catch: if the light is directional from above, the top faces will be brightest. The side faces will have moderate brightness. This makes cubes read clearly as 3D shapes.

If I additionally set material.color to faceShading, it would darken the side faces further and make them even more distinct. This is good.

Let me go with both:
- Material color = faceShading value, so top=1.0, sides=0.8/0.7, bottom=0.5.
- Add an ambient light 0x404040 and a directional light 0xffffff with intensity 0.8.

This should give a nice Minecraft look.

**Implementation of InstancedMesh:**

After building the block array, I need to:

1. Count how many instances of each block type are visible.
2. Create InstancedMesh with appropriate counts.
3. Fill in instance matrices.

Let me do this:

```javascript
// Count visible instances
const counts = {};
for (let x = 0; x < WORLD_SIZE; x++) {
    for (let z = 0; z < WORLD_SIZE; z++) {
        for (let y = 0; y < MAX_HEIGHT; y++) {
            const type = blocks[x][y][z];
            if (type === BLOCK_TYPES.AIR) continue;
            if (isVisible(x, y, z)) {
                if (!counts[type]) counts[type] = 0;
                counts[type]++;
            }
        }
    }
}
```

Where `isVisible` checks if any neighbor is AIR or WATER (for non-water blocks) or AIR (for water blocks).

But `blocks` as a 3D array [x][y][z] is large. It's okay.

Actually, I'll use a flat Uint8Array for the block array:

```javascript
const blocks = new Uint8Array(WORLD_SIZE * MAX_HEIGHT * WORLD_SIZE);
function getBlock(x, y, z) {
    if (x < 0 || y < 0 || z < 0 || x >= WORLD_SIZE || y >= MAX_HEIGHT || z >= WORLD_SIZE) return BLOCK_TYPES.AIR;
    return blocks[(y * WORLD_SIZE + z) * WORLD_SIZE + x];
}
function setBlock(x, y, z, type) {
    blocks[(y * WORLD_SIZE + z) * WORLD_SIZE + x] = type;
}
```

Wait, indexing: if x varies fastest, then:
index = (y * WORLD_SIZE + z) * WORLD_SIZE + x.

Or (x, y, z) with x fastest.

For chunks, prefer zyyx? Actually, doesn't matter. I'll use:
index = (x * WORLD_SIZE + z) * MAX_HEIGHT + y

Hmm, this is getting confusing. Let me use a simple 3D array or a flat array with index = (x * WORLD_SIZE + z) * MAX_HEIGHT + y.

Actually, for cache efficiency, y should be the fastest. So:
index = (x * WORLD_SIZE + z) * MAX_HEIGHT + y

This is fine.

Let me also store the max height generated so I know the array size.

For the world generation:

```javascript
const WORLD_SIZE = 128;
const SEA_LEVEL = 24;
const SNOW_LEVEL = 55;

const MAX_HEIGHT = 80; // Max terrain height

// Generate height map
const heights = new Float32Array(WORLD_SIZE * WORLD_SIZE);

for (let x = 0; x < WORLD_SIZE; x++) {
    for (let z = 0; z < WORLD_SIZE; z++) {
        heights[z * WORLD_SIZE + x] = generateHeight(x, z);
    }
}

// Build block array
for (let x = 0; x < WORLD_SIZE; x++) {
    for (let z = 0; z < WORLD_SIZE; z++) {
        const h = Math.floor(heights[z * WORLD_SIZE + x]);
        for (let y = 0; y <= Math.max(h, SEA_LEVEL); y++) {
            let type;
            if (y === 0) {
                type = BLOCK_TYPES.STONE;
            } else if (y === h) {
                // Surface
                if (h < SEA_LEVEL - 1) {
                    type = BLOCK_TYPES.DIRT; // underwater
                } else if (h < SEA_LEVEL + 2) {
                    type = BLOCK_TYPES.SAND;
                } else if (h < SNOW_LEVEL) {
                    type = BLOCK_TYPES.GRASS;
                } else {
                    type = BLOCK_TYPES.SNOW_BLOCK;
                }
            } else if (y >= h - 4 && y < h) {
                type = BLOCK_TYPES.DIRT;
            } else {
                type = BLOCK_TYPES.STONE;
            }
            setBlock(x, y, z, type);
        }
        // Water
        if (h < SEA_LEVEL) {
            for (let y = h + 1; y <= SEA_LEVEL; y++) {
                setBlock(x, y, z, BLOCK_TYPES.WATER);
            }
        }
    }
}
```

Hmm, but underwater, the surface block should be sand, not dirt. Let me adjust:
- If h < SEA_LEVEL - 1: the top of the underwater column is sand (at position h). Actually, in Minecraft, underwater terrain is usually sand/gravel.
- If h < SEA_LEVEL: the surface block (at y=h) is sand.
- Below that: dirt/stone.

Let me fix:
```javascript
if (y === h) {
    if (h < SEA_LEVEL) {
        type = BLOCK_TYPES.SAND;
    } else if (h < SEA_LEVEL + 2) {
        type = BLOCK_TYPES.SAND; // beach
    } else if (h < SNOW_LEVEL) {
        type = BLOCK_TYPES.GRASS;
    } else {
        type = BLOCK_TYPES.SNOW_BLOCK;
    }
}
```

And for the block below the surface:
```javascript
if (y === h - 1 || y === h - 2) {
    type = BLOCK_TYPES.DIRT;
}
```

Wait, with beaches, sand should also be on the beach level (just above sea level). Let me do:
- h < SEA_LEVEL: underwater, top = sand
- SEA_LEVEL <= h < SEA_LEVEL + 2: beach, top = sand
- h >= SEA_LEVEL + 2: grassland, top = grass (or snow if high)

This gives sandy beaches around the water.

Now, trees:
- On grass blocks (h >= SEA_LEVEL + 2 && h < SNOW_LEVEL), with some probability.
- Tree consists of wood trunk (3-5 blocks tall) and leaves (a sphere-ish blob around the top).

I'll generate trees during block generation, after terrain generation but before mesh generation.

```javascript
function generateTree(x, y, z) {
    // Place tree
    const trunkHeight = 4 + Math.floor(Math.random() * 3); // 4-6
    // Ensure space
    for (let i = 0; i < trunkHeight; i++) {
        setBlock(x, y + i, z, BLOCK_TYPES.WOOD);
    }
    // Leaves
    const leafTop = y + trunkHeight;
    for (let dy = -2; dy <= 1; dy++) {
        const r = dy < 0 ? 2 : (dy === 1 ? 1 : 2);
        for (let dx = -r; dx <= r; dx++) {
            for (let dz = -r; dz <= r; dz++) {
                if (Math.abs(dx) === r && Math.abs(dz) === r && Math.random() < 0.3) continue;
                const lx = x + dx;
                const lz = z + dz;
                const ly = leafTop + dy;
                if (getBlock(lx, ly, lz) === BLOCK_TYPES.AIR) {
                    setBlock(lx, ly, lz, BLOCK_TYPES.LEAVES);
                }
            }
        }
    }
}
```

Now, for the mesh generation, I need to iterate all blocks and check visibility.

**isVisible function:**

```javascript
function isVisible(x, y, z, type) {
    // For water blocks, only render top face and horizontal faces
    // For solid blocks, render if any neighbor is AIR or WATER (or when on the border of the world)
    const neighbors = [
        getBlock(x-1,y,z), getBlock(x+1,y,z),
        getBlock(x,y-1,z), getBlock(x,y+1,z),
        getBlock(x,y,z-1), getBlock(x,y,z+1),
    ];
    for (const n of neighbors) {
        if (n === BLOCK_TYPES.AIR || n === BLOCK_TYPES.WATER) return true;
    }
    return false;
}
```

But for water blocks, we want to render water even if surrounded by other water (for underwater submerged faces? Actually, we only need water surface and edges). So:

```javascript
function isWaterVisible(x, y, z) {
    // Render if any neighbor is AIR
    return getBlock(x-1,y,z) === BLOCK_TYPES.AIR ||
           getBlock(x+1,y,z) === BLOCK_TYPES.AIR ||
           getBlock(x,y-1,z) === BLOCK_TYPES.AIR ||
           getBlock(x,y+1,z) === BLOCK_TYPES.AIR ||
           getBlock(x,y,z-1) === BLOCK_TYPES.AIR ||
           getBlock(x,y,z+1) === BLOCK_TYPES.AIR;
}
```

Actually, water's bottom face (y-1) is never visible since water sits on the terrain. But water's top face (y+1) is visible if the block above is AIR.

OK let me simplify: For all block types including water, render the block if any neighbor is AIR or WATER. For water specifically, also render if the block above is AIR. Wait, if any neighbor is WATER and the current block is also WATER, that means the interior of the water body. We don't need to render interior water blocks.

Actually, in Minecraft, water is semi-transparent. When you look into a lake, you see the water surface and the sides. The interior water blocks are not rendered as separate cubes; instead, the top surface is a plane, and the sides are the edges of the body of water.

So for water:
- Top face: always rendered (covers the lake surface).
- Side faces: rendered where the water body meets AIR (shoreline).
- Bottom face: not rendered (the sand below covers it).

But since we're using a box mesh for water blocks, we'd render the sides even when adjacent to other water blocks (which are also semi-transparent). This means interior faces between two water blocks would be rendered, which looks bad.

To avoid this, I should only render water blocks that are on the surface (no water above) or at the edges (neighbor is AIR or solid block).

In my visibility check:
```javascript
// For water:
if (type === BLOCK_TYPES.WATER) {
    const above = getBlock(x, y+1, z);
    const below = getBlock(x, y-1, z);
    // Visible if no water above (surface), or side neighbors are not water, or below is not water? Actually:
    // We want to render water if any adjacent block is AIR or solid (non-water).
    // Since all blocks of water are of type WATER, adjacent water blocks are NOT AIR.
    // So water is visible if any neighbor is not WATER.
    for (let dx=-1; dx<=1; dx++)
      for (let dz=-1; dz<=1; dz++)
        for (let dy=-1; dy<=1; dy++) {
          if (dx===0 && dy===0 && dz===0) continue;
          const nx = x+dx, ny = y+dy, nz = z+dz;
          if (nx<0||nz<0||nx>=WORLD_SIZE||nz>=WORLD_SIZE) continue;
          const n = getBlock(nx, ny, nz);
          if (n !== BLOCK_TYPES.WATER && n !== BLOCK_TYPES.AIR) return true;
          if (n === BLOCK_TYPES.AIR) return true;
        }
    return false;
}
```

Wait, but the water block below the surface (interior) has neighbors that are all water or the terrain at the bottom. So it's not visible. The surface water block has AIR above, so it's visible. The water block at the edges (e.g., next to a sand block) has a non-water neighbor, so it's visible.

But what about a water block right above the terrain? Its bottom neighbor is sand, so it's visible. Good.

For solid blocks:
```javascript
if (type !== BLOCK_TYPES.WATER) {
    return getBlock(x-1,y,z) === BLOCK_TYPES.AIR || 
           getBlock(x+1,y,z) === BLOCK_TYPES.AIR ||
           getBlock(x,y-1,z) === BLOCK_TYPES.AIR ||
           getBlock(x,y+1,z) === BLOCK_TYPES.AIR ||
           getBlock(x,y,z-1) === BLOCK_TYPES.AIR ||
           getBlock(x,y,z+1) === BLOCK_TYPES.AIR ||
           getBlock(x-1,y,z) === BLOCK_TYPES.WATER ||
           getBlock(x+1,y,z) === BLOCK_TYPES.WATER ||
           getBlock(x,y,z-1) === BLOCK_TYPES.WATER ||
           getBlock(x,y,z+1) === BLOCK_TYPES.WATER;
}
```

This also captures water-adjacent blocks (e.g., a sand block next to water).

But this doesn't check the block below for water, because a sand block underwater has WATER above, not beside. So:
```javascript
getBlock(x,y+1,z) === BLOCK_TYPES.WATER
```
would make a block visible if it's underwater. Actually, if a block is below water, its top face touches water, which means it should be rendered so we can see it through the water. Yes, this is correct.

But this also means every underwater block that has WATER above would be added. That's exactly what we want: underwater terrain (sand, dirt, stone) should be visible through the transparent water.

OK, but this will also make lots of blocks visible. For example, a stone block deep below the terrain that has water somewhere above it in the same column. But the stone block's top face touches either stone or dirt, not water. The water might be high above, but not directly adjacent. My visibility check only checks immediate neighbors, so a stone block at depth 10, with the surface at depth 20 and water above, would have neighbors that are stone/dirt, not water. So it wouldn't be rendered. Good.

Wait, for underwater terrain, the block at the ocean floor has WATER above it (immediate neighbor). So it will be visible. Deeper blocks have only solid neighbors, so they won't be visible.

OK, I think this approach works.

**Instance Counting and Creation:**

First pass: count visible instances per type.
Second pass: create InstancedMesh and set matrices.

Actually, for the count to work, I'll use `updateMatrix()` for each instance.

```javascript
// Initialize counts
const counts = {};
const matrices = {};
const types = Object.keys(BLOCK_TYPES).filter(k => k !== 'AIR');
for (const t of types) {
    counts[BLOCK_TYPES[t]] = 0;
}

// Count
for (let x = 0; x < WORLD_SIZE; x++) {
    for (let z = 0; z < WORLD_SIZE; z++) {
        for (let y = 0; y < MAX_HEIGHT; y++) {
            const type = getBlock(x, y, z);
            if (type === BLOCK_TYPES.AIR) continue;
            if (isVisible(x, y, z, type)) {
                counts[type]++;
            }
        }
    }
}
```

Then create meshes:

```javascript
const meshes = [];
const _matrix = new THREE.Matrix4();

for (const [typeStr, count] of Object.entries(counts)) {
    if (count === 0) continue;
    const type = Number(typeStr);
    const materials = BLOCK_TYPE_MATERIALS[type].map(i => allMaterials[i]);
    const mesh = new THREE.InstancedMesh(blockGeometry, materials, count);
    mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage); // optional
    // Will fill in second pass
    let index = 0;
    for (let x = 0; x < WORLD_SIZE; x++) {
        for (let z = 0; z < WORLD_SIZE; z++) {
            for (let y = 0; y < MAX_HEIGHT; y++) {
                const btype = getBlock(x, y, z);
                if (btype !== type) continue;
                if (isVisible(x, y, z, btype)) {
                    _matrix.makeTranslation(x + 0.5, y + 0.5, z + 0.5);
                    mesh.setMatrixAt(index++, _matrix);
                }
            }
        }
    }
    mesh.instanceMatrix.needsUpdate = true;
    meshes.push(mesh);
}
```

Hmm, this does two passes (counting and filling) and also calls `isVisible` twice. I could store the visible instances during the first pass. But storing positions for every block type could be memory-heavy. Let me just do two passes; the total number of blocks is ~500k, so `isVisible` is fast enough.

Wait, I'm iterating y in the range [0, MAX_HEIGHT) for each (x, z). MAX_HEIGHT=80, so total iterations = 128*128*80 = 1,310,720. That's fine.

Actually, I should iterate y only up to the max generated height + SEA_LEVEL + leaves + tree height. So MAX_HEIGHT=90 is good.

Let me set `MAX_HEIGHT = 100` to be safe.

**Block Geometry:**

```javascript
const blockGeometry = new THREE.BoxGeometry(1, 1, 1);
```

For water, I might want a slightly smaller box (like 0.9 scale) so the water surface has visible gaps. But for simplicity, let me use a full box.

For water transparency, set:
```javascript
const waterMaterial = new THREE.MeshLambertMaterial({...});
waterMaterial.transparent = true;
waterMaterial.opacity = 0.7;
```

But if I use a material array, each material can be transparent/opaque. Good.

**Camera Path:**

```javascript
const curve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(-40, 35, -40),
    new THREE.Vector3(10, 30, 10),
    new THREE.Vector3(60, 50, 50),
    new THREE.Vector3(20, 30, 100),
    new THREE.Vector3(-30, 25, 90),
    new THREE.Vector3(-70, 45, 50),
    new THREE.Vector3(-20, 30, 0),
], true);
```

Actually, the world is 128x128 (from 0 to 127). The center is around (64, 64). Let me position the path to fly over the interesting parts.

Let me make the camera path as:

```javascript
const curve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(10, 40, 5),
    new THREE.Vector3(20, 35, 30),
    new THREE.Vector3(50, 45, 70),
    new THREE.Vector3(80, 30, 90),
    new THREE.Vector3(100, 25, 60),
    new THREE.Vector3(90, 35, 30),
    new THREE.Vector3(60, 45, 20),
    new THREE.Vector3(30, 35, 10),
], false);
```

And animate:

```javascript
let t = 0;
const speed = 0.05; // Adjust as needed
function animate() {
    requestAnimationFrame(animate);
    t += speed * delta;
    if (t > 1) t = 0; // loop
    const p = curve.getPoint(t);
    const look = curve.getPoint(Math.min(t + 0.02, 1));
    camera.position.copy(p);
    camera.lookAt(look);
    renderer.render(scene, camera);
}
```

**Clouds:**

```javascript
function createCloud() {
    const group = new THREE.Group();
    const geo = new THREE.BoxGeometry(1, 1, 1);
    const mat = new THREE.MeshLambertMaterial({ color: 0xffffff, transparent: true, opacity: 0.7 });
    for (let i = 0; i < 8; i++) {
        const mesh = new THREE.Mesh(geo, mat);
        const w = 5 + Math.random() * 5;
        const h = 1.2 + Math.random() * 1;
        mesh.scale.set(w, h, w * 0.7);
        mesh.position.set(
            (Math.random() - 0.5) * 20,
            (Math.random() - 0.5) * 2,
            (Math.random() - 0.5) * 15
        );
        group.add(mesh);
    }
    return group;
}
```

Add 15 clouds at random positions in the sky, each at y ~ 70-90.

**Sun:**

```javascript
// Create a glowing sun sprite
const sunCanvas = document.createElement('canvas');
sunCanvas.width = 128;
sunCanvas.height = 128;
const sctx = sunCanvas.getContext('2d');
const gradient = sctx.createRadialGradient(64, 64, 0, 64, 64, 64);
gradient.addColorStop(0, 'rgba(255, 255, 180, 1)');
gradient.addColorStop(0.3, 'rgba(255, 230, 100, 0.8)');
gradient.addColorStop(1, 'rgba(255, 200, 50, 0)');
sctx.fillStyle = gradient;
sctx.fillRect(0, 0, 128, 128);
const sunTexture = new THREE.CanvasTexture(sunCanvas);
const sunMaterial = new THREE.SpriteMaterial({ map: sunTexture, transparent: true, depthWrite: false });
const sun = new THREE.Sprite(sunMaterial);
sun.position.set(80, 180, -50);
sun.scale.set(80, 80, 1);
scene.add(sun);
```

Hmm, but with sun position at (80, 180, -50), it would appear in the sky. Since our world is 128x128, the sun can be positioned far away. The sprite always faces the camera, so `lookAt` isn't needed.

Actually, the sun should be far from the scene. But with a camera that moves, a distant sprite is fine.

Let me set sun.position = (200, 150, -100).

OK now, let me also consider the directional light position to match the sun.

```javascript
const dirLight = new THREE.DirectionalLight(0xffffff, 1);
dirLight.position.set(0.5, 1, 0.3);
dirLight.target.position.set(0, 0, 0);
scene.add(dirLight.target);
scene.add(dirLight);
```

Using a unit direction for the light. The light direction is from `dirLight.position` to `dirLight.target.position`. Since target is at (0,0,0), the light direction is toward the origin.

Wait, `DirectionalLight`'s position and target define the direction. From position (0.5, 1, 0.3) toward (0,0,0), the direction is (-0.5, -1, -0.3). The light rays travel from the target toward the position? Actually, in three.js, for directional lights, the light comes from `position` to `target`. So if position is above-target, the light is coming from above.

But the position is a direction, not an absolute position. Let me use:
```javascript
dirLight.position.set(50, 100, 30);
dirLight.target.position.set(64, 0, 64);
```

This points from (50,100,30) to (64,0,64), which is generally downward and toward the world center. Good.

Now, for the sun sprite to line up with the directional light, it should be in the same direction. But with a sprite billboarded to face the camera, it doesn't have a real position. I'll just place it in the sky.

OK, I think I've planned enough. Let me write the code.

One concern: InstancedMesh with material array - does it work correctly? Let me double-check.

From the three.js docs: `Material` can be an array of materials. The `geometry.groups` (or `BufferGeometry` groups) specify which material to use for each indexed range.

For BoxGeometry, the groups are:
```
BoxGeometry creates:
- 6 groups (one for each face):
  0: +x
  1: -x
  2: +y
  3: -y
  4: +z
  5: -z
```

And each group has a material index (0 by default). When we assign `material = [mat0, mat1, mat2, ...]`, the groups use their materialIndex property to pick from the array.

But wait, the groups' materialIndex values in BoxGeometry are set to 0 by default. To use different materials for different faces, I'd need to create a BoxGeometry (or similar) that has group material indices 0 through 5.

However, in three.js, `BoxGeometry` creates groups with material index 0 for all groups. The docs say:
"BoxGeometry... This class generates geometry... The groups are set up with material index 0 for all groups except the last one, which gets the material index set..."

Hmm, actually I think BoxGeometry creates 6 groups, each with material index = group index (0-5). Let me verify.

Looking at the three.js source code for BoxGeometry:
```javascript
// build each side of the box geometry
function buildPlane( u, v, w, udir, vdir, width, height, depth, materialIndex ) {
    // ...
    buildPlane( 'z', 'y', 'x', -1, -1, depth, height, width, 0 ); // px
    buildPlane( 'z', 'y', 'x',  1, -1, depth, height, -width, 1 ); // nx
    buildPlane( 'x', 'z', 'y',  1,  1, width, depth, height, 2 ); // py
    buildPlane( 'x', 'z', 'y',  1, -1, width, depth, -height, 3 ); // ny
    buildPlane( 'x', 'y', 'z',  1, -1, width, height, depth, 4 ); // pz
    buildPlane( 'x', 'y', 'z', -1, -1, width, height, -depth, 5 ); // nz
}
```

The last parameter is `materialIndex`. So yes, BoxGeometry creates 6 groups with material indices 0-5. This means passing an array of 6 materials will work as expected.

Great.

Now let me also verify InstancedMesh usage with material array: InstancedMesh extends Mesh, which has a `material` property. The render path uses `material` (if array) with `group.materialIndex` to select the material. Since the mesh is an InstancedMesh, each instance is drawn with the same material array, but different world matrices. So yes, it works.

But there's a catch: if some materials in the array are transparent and others are opaque, the render order is sorted per-face (which can cause issues). In our case, the grass block has all opaque materials, the water block has all transparent. So the render order between blocks might be off for water (transparent) vs. opaque blocks. This is handled by three.js: transparent objects are rendered after opaque ones. But since the water mesh is a single InstancedMesh with a transparent material, all water instances render together. This is fine for water surfaces but could cause sorting issues if the camera sees two transparent water instances at different depths.

For a first implementation, this is acceptable.

Now let me write the actual code. This is going to be long.

Actually, one more consideration: the per-face material array. For water, all six materials are the same transparent material. For leaves, all six materials are the same opaque (or transparent?) material. Let me make leaves slightly transparent? No, just opaque for now.

OK, writing the code now.

Let me also create a function to generate random colors for textures.

Actually, let me simplify the texture generation and use deterministic pixels.

```javascript
function createNoiseTexture(baseRGB, variation, fn) {
    return createCanvasTexture((ctx) => {
        for (let y = 0; y < 16; y++) {
            for (let x = 0; x < 16; x++) {
                const v = (Math.random() - 0.5) * variation * 255;
                let r = baseRGB[0] + v;
                let g = baseRGB[1] + v;
                let b = baseRGB[2] + v;
                if (fn) {
                    const c = fn(x, y);
                    if (c) {
                        r = c[0]; g = c[1]; b = c[2];
                    }
                }
                ctx.fillStyle = `rgb(${r|0},${g|0},${b|0})`;
                ctx.fillRect(x, y, 1, 1);
            }
        }
    });
}
```

Hmm, this is overcomplicating. Let me just write straightforward fillRect loops for each texture.

Let me begin coding.

```html
<!DOCTYPE html>
<html>
<head>
    <title>Voxel Terrain</title>
    <style>body { margin: 0; overflow: hidden; }</style>
</head>
<body>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
// ... Code ...
</script>
</body>
</html>
```

Wait, I should use the latest three.js with ES modules, or a CDN that provides a global THREE. Let me use:

```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
```

Or use the modern import map approach. For simplicity, use r128 global.

Actually, r128 doesn't have `InstancedMesh`? It does (since r110 or so). Good.

Let me write the complete code now.

One more consideration: The block array. I'll use a flat Uint8Array called `world`.

```javascript
const WORLD_SIZE = 128;
const MAX_HEIGHT = 80;
const SEA_LEVEL = 24;
const SNOW_LEVEL = 55;

const BLOCK = {
    AIR: 0,
    GRASS: 1,
    DIRT: 2,
    STONE: 3,
    SAND: 4,
    SNOW: 5,
    WOOD: 6,
    LEAVES: 7,
    WATER: 8,
    COUNT: 9
};

// Flat world storage: index = (x * WORLD_SIZE + z) * MAX_HEIGHT + y
function worldIndex(x, y, z) {
    return (x * WORLD_SIZE + z) * MAX_HEIGHT + y;
}

const world = new Uint8Array(WORLD_SIZE * WORLD_SIZE * MAX_HEIGHT);

function getBlock(x, y, z) {
    if (x < 0 || y < 0 || z < 0 || x >= WORLD_SIZE || y >= MAX_HEIGHT || z >= WORLD_SIZE)
        return BLOCK.AIR;
    return world[worldIndex(x, y, z)];
}

function setBlock(x, y, z, type) {
    if (x < 0 || y < 0 || z < 0 || x >= WORLD_SIZE || y >= MAX_HEIGHT || z >= WORLD_SIZE)
        return;
    world[worldIndex(x, y, z)] = type;
}
```

Now the noise function:

```javascript
function mulberry32(a) {
    return function() {
        a |= 0; a = a + 0x6D2B79F5 | 0;
        let t = Math.imul(a ^ a >>> 15, 1 | a);
        t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
        return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
}

// Hash function for integer coordinates
function hash2D(x, z, seed) {
    let n = x * 374761393 + z * 668265263 + seed * 974711;
    n = Math.imul(n ^ n >>> 13, 1274126177);
    n ^= n >>> 16;
    return (n & 0xffff) / 0xffff;
}
```

Hmm, `hash2D` might return values outside [0,1]. Let me normalize:
```javascript
let n = (x * 0x1f1f1f1f) ^ (z * 0x15f1f2f3) ^ seed;
n = (n ^ (n >>> 16)) * 0x85ebca6b;
n = n ^ (n >>> 13);
return (n & 0xffffffff) / 4294967296;
```

But this is signed. Let me use:
```javascript
function hash2D(x, z, seed) {
    let n = x + z * 374761393 + seed;
    n = (n ^ (n >> 16)) * 0x7feb352d;
    n = (n ^ (n >> 15)) * 0x846ca68b;
    n = (n ^ (n >> 16));
    return (n & 0x7fffffff) / 0x7fffffff;
}
```

But JS bitwise operations work on 32-bit signed integers. `x + z * 374761393` could overflow. Let me use a simpler approach:

```javascript
function hash2D(x, z, seed = 0) {
    let h = x * 374761393 + z * 668265263 + seed;
    h = (h ^ (h >> 13)) * 1274126177;
    h = ((h ^ (h >> 16)) >>> 0) / 4294967296;
    return h;
}
```

In JS, `h` is a signed 32-bit integer after bitwise operations. `h >>> 0` converts to unsigned. Good.

For smooth noise, I'll use simple value noise with bilinear interpolation:

```javascript
function valueNoise(x, z, seed) {
    const xi = Math.floor(x), zi = Math.floor(z);
    const xf = x - xi, zf = z - zi;
    const v00 = hash2D(xi, zi, seed);
    const v10 = hash2D(xi+1, zi, seed);
    const v01 = hash2D(xi, zi+1, seed);
    const v11 = hash2D(xi+1, zi+1, seed);
    const sx = xf * xf * (3 - 2 * xf);
    const sz = zf * zf * (3 - 2 * zf);
    const a = v00 + (v10 - v00) * sx;
    const b = v01 + (v11 - v01) * sx;
    return a + (b - a) * sz;
}
function fbm(x, z, seed, octaves) {
    let value = 0, amp = 1, freq = 1;
    let max = 0;
    for (let i = 0; i < octaves; i++) {
        value += amp * valueNoise(x * freq, z * freq, seed + i * 100);
        max += amp;
        amp *= 0.5;
        freq *= 2;
    }
    return value / max;
}
```

Then generate height:
```javascript
function generateHeight(x, z) {
    const n = fbm(x / 50, z / 50, 42, 5);
    // More mountains near the center, flatter near the edges? Let's add a base + variation.
    let h = n * 40 + 25;
    h = Math.max(0, Math.min(MAX_HEIGHT - 1, h));
    return h;
}
```

But this creates rolling hills. For more interesting terrain with mountains and valleys, add some ridged noise:
```javascript
const ridged = 1 - 2 * Math.abs(0.5 - n);
h = ridged * ridged * 50 + 10;
// blend with a milder fbm
h = h * 0.7 + n * 40 * 0.3 + 15;
```

Hmm, let me just use two octaves of FBM and a height equation:

```javascript
const base = fbm(x / 100, z / 100, 50, 4); // 0..1
const detail = fbm(x / 40 + 100, z / 40 + 100, 60, 3); // 0..1
let h = base * 35 + detail * 15 + 5;
h = Math.max(2, Math.min(70, h));
```

This gives terrain ranging from ~5 to ~55. Good.

Now let me put it all together. This is going to be a big script.

For performance, I'll generate the world and build InstancedMeshes. Let me also add a simple animation loop.

One issue: The default three.js camera has a near/far clipping. For a 128x128 world, far=500 is fine.

Let me set:
```javascript
const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);
```

Add OrbitControls? No, we want a flythrough camera. But for development, OrbitControls is useful. Let me use both: OrbitControls for interaction (if user clicks/drags), and a scripted path. Actually, the requirement says "flythrough", so let me use a scripted path and no controls. But I'll still add an option to orbit.

Let me keep it simple: no controls.

Here's the full code structure:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Voxel Terrain</title>
    <style>body{margin:0;overflow:hidden;}canvas{display:block;}</style>
</head>
<body>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
// Constants
// ...
// Scene setup
// ...
// Noise functions
// ...
// World generation
// ...
// Materials
// ...
// InstancedMesh building
// ...
// Cloud, sun, environment
// ...
// Animation
</script>
</body>
</html>
```

Let me now write the full code.

Wait, before doing that, let me reconsider the `isVisible` function and the InstancedMesh building process. It might be slow to iterate over all blocks twice. But 1.3M iterations is fine for JS.

However, I need to ensure I don't double-create InstancedMeshes. Let me use a two-pass approach:

```javascript
// First pass: count visible blocks per type
const typeCounts = new Array(BLOCK.COUNT).fill(0);
for (let x = 0; x < WORLD_SIZE; x++) {
    for (let z = 0; z < WORLD_SIZE; z++) {
        for (let y = 0; y < MAX_HEIGHT; y++) {
            const type = getBlock(x, y, z);
            if (type === BLOCK.AIR) continue;
            if (isVisible(x, y, z, type)) typeCounts[type]++;
        }
    }
}

// Create meshes
const instancedMeshes = [];
const dummyMatrix = new THREE.Matrix4();
const dummyPosition = new THREE.Vector3();
const dummyQuaternion = new THREE.Quaternion();
const dummyScale = new THREE.Vector3(1, 1, 1);

for (let type = 1; type < BLOCK.COUNT; type++) {
    const count = typeCounts[type];
    if (count === 0) continue;

    const materials = getBlockMaterials(type);
    const mesh = new THREE.InstancedMesh(blockGeo, materials, count);
    let index = 0;

    for (let x = 0; x < WORLD_SIZE; x++) {
        for (let z = 0; z < WORLD_SIZE; z++) {
            for (let y = 0; y < MAX_HEIGHT; y++) {
                if (getBlock(x, y, z) !== type) continue;
                if (!isVisible(x, y, z, type)) continue;
                dummyPosition.set(x + 0.5, y + 0.5, z + 0.5);
                dummyMatrix.compose(dummyPosition, dummyQuaternion, dummyScale);
                mesh.setMatrixAt(index++, dummyMatrix);
            }
        }
    }
    mesh.instanceMatrix.needsUpdate = true;
    instancedMeshes.push(mesh);
}
```

The `isVisible` function needs to be fast. Let me define it:

```javascript
function isVisible(x, y, z, type) {
    if (type === BLOCK.WATER) {
        // Water is visible if any of the 6 neighbors is not water
        return getBlock(x-1, y, z) !== BLOCK.WATER ||
               getBlock(x+1, y, z) !== BLOCK.WATER ||
               getBlock(x, y-1, z) !== BLOCK.WATER ||
               getBlock(x, y+1, z) !== BLOCK.WATER ||
               getBlock(x, y, z-1) !== BLOCK.WATER ||
               getBlock(x, y, z+1) !== BLOCK.WATER;
    } else {
        // Solid block: visible if any neighbor is AIR or WATER, or it's at the edge of the world
        return getBlock(x-1, y, z) === BLOCK.AIR ||
               getBlock(x+1, y, z) === BLOCK.AIR ||
               getBlock(x, y-1, z) === BLOCK.AIR ||
               getBlock(x, y+1, z) === BLOCK.AIR ||
               getBlock(x, y, z-1) === BLOCK.AIR ||
               getBlock(x, y, z+1) === BLOCK.AIR ||
               getBlock(x-1, y, z) === BLOCK.WATER ||
               getBlock(x+1, y, z) === BLOCK.WATER ||
               getBlock(x, y-1, z) === BLOCK.WATER ||
               getBlock(x, y+1, z) === BLOCK.WATER ||
               getBlock(x, y, z-1) === BLOCK.WATER ||
               getBlock(x, y, z+1) === BLOCK.WATER;
    }
}
```

Wait, for water: water is visible if any neighbor is not water (including AIR, solid, or edge of world). But interior water blocks (all 6 neighbors are water) should not be rendered. My condition `!== BLOCK.WATER` for all 6 neighbors covers this: if all neighbors are water, it's not visible. If any neighbor is not water, it's visible.

But what about water block above terrain? Its bottom neighbor is sand (not water), so it's visible. Good.

What about a water surface in the middle of a lake? The top neighbor is AIR (not water), so it's visible. Good.

What about a submerged stone block? Its top neighbor is WATER, so it's visible. Good.

But this causes a problem: A stone block deep below the water but not at the surface (e.g., at the bottom of the lake, but with water above) would have `getBlock(x, y+1, z) === WATER`, making it visible. This is correct—we need this block to be visible through the water. But what about a stone block that's at the bottom, with other stone blocks above? Its top neighbor is stone, not water, so it wouldn't be visible. Correct.

However, the condition `getBlock(x, y-1, z) === WATER` would make a block visible if it's below water. Wait, that means any stone block that has water below it? No, that's not right. The block below being water means the block is floating on water (impossible). So `y-1` being water doesn't happen naturally. But `y+1` being water means the block is below water, which should be visible.

Actually, my code checks all 6 neighbors for WATER. For a stone block at the bottom of a lake (solid underwater terrain), the neighbor above (y+1) might be water, or might be another stone if there are multiple blocks. If it's directly under water's bottom surface (one stone block below the water), then `getBlock(x, y+1, z)` is WATER, so the stone is visible. Good.

But what about a stone block deeper below? Its neighbors are all stone, so it's not visible. Good.

There's a performance issue: for every block we call `isVisible`, which calls `getBlock` 12 times. This is fine for 1.3M blocks.

But there's a bug: For a solid block underwater, we want it visible if any neighbor is WATER. The condition `getBlock(x, y+1, z) === WATER` for the block at the top of the terrain under water is true. But what about a block that's below the water level but has a stone block above it? Its top neighbor is stone, not water. Its side neighbors are stone. So it's not visible. That's correct because you can't see it through the water—it's surrounded by stone.

Wait, but what about a stone block that's underwater, with stone above it (the surface is one block higher), but the surface has water on top? The block has a neighbor above that's stone, not water. But from the side, if the camera is looking at the underwater stone wall, you'd see stone faces. Let me think.

The visibility check should determine if a face of the block is exposed to air or water. If the block is surrounded by other stone blocks, no face is exposed, so it's not visible. If one neighbor is water (e.g., the block at the water's edge), then a face is exposed to water, so you'd see it. My visibility condition covers this.

But there's a subtlety: If a block's neighbor is water, and the water is transparent, you might see the face. But if the water is fully between the camera and the block, the water itself would also be visible (since water is a transparent InstancedMesh). This could cause z-fighting or sorting issues.

For now, with opaque underwater blocks and transparent water, it should be acceptable. The underwater blocks will be rendered because they're adjacent to water, and the water is transparent so they'll be visible.

One more issue: If the camera is inside a water block, the camera should see water edges. But since we always move through air (our flythrough points are above the terrain), it's not a problem.

OK, I think this is good enough. Let me write the code.

Actually, to reduce overdraw, I could skip the water visibility check and just render all surface water blocks. But I'll keep it.

Also, when creating materials, I need to set `side: THREE.DoubleSide` or `THREE.FrontSide`? For a water box, we only need the front side if the camera is outside. But if the camera is outside looking at a shoreline, the front side suffices. Setting `side: THREE.DoubleSide` can help see the water from inside, but there are no inside views for our flythrough. Let me use `THREE.FrontSide` for solid blocks and `THREE.DoubleSide` for water (to see the surface from slightly below).

Actually, if I set `side: THREE.FrontSide` for water blocks, when looking from above at the surface, you see the top face (front face, normal up). When looking from below (underwater), you wouldn't see the face. For our flythrough above the water, this is fine.

For simplicity, use `THREE.DoubleSide` for water material to see the surface from all angles.

Now, material transparency:
```javascript
const waterMaterial = new THREE.MeshLambertMaterial({
    color: 0x3377ff,
    transparent: true,
    opacity: 0.7,
    side: THREE.DoubleSide,
    depthWrite: false // To avoid sorting artifacts? Actually, should be true for water? Let me leave it true.
});
```

But since we use `map`, the color will be modulated by the texture. Do I want a texture for water? I'll create a procedural water texture:
```javascript
const waterTexture = createCanvasTexture((ctx) => {
    for (let y = 0; y < 16; y++) {
        for (let x = 0; x < 16; x++) {
            const v = 40 + Math.random() * 20;
            ctx.fillStyle = `rgb(${40+v|0}, ${80+v|0}, ${160+v|0})`;
            ctx.fillRect(x, y, 1, 1);
        }
    }
});
```

Actually, let me use a solid color material instead of a texture for water. With transparency, a solid blue color looks fine. I'll just use `new THREE.MeshLambertMaterial({ color: 0x3366cc, transparent: true, opacity: 0.6 })`.

But the requirement likely expects textures for all blocks. Let me create a simple water texture.

OK, I'm going to optimize for simplicity and just code it now. Here goes.

Let me also consider the block materials after creation: I need to set `material.color` to faceShading. But some block types (like water) share the same material for all faces, so the faceShading would be uniform. For water, this is fine.

Wait, but for InstancedMesh with material array, all instances use the same materials. So water blocks have the same faceShading on all faces (1.0). This means the sides of a water block are the same brightness as the top. To add depth per block, I could set faceShading for water too, but since water is transparent, the shading differences are less noticeable.

Hmm, this is getting complicated. Let me simplify: don't use material color for faceShading. Instead, rely on the directional light to shade faces. This gives a consistent look for all blocks. The top faces are bright, sides are medium, bottoms are dark—naturally.

So all materials have `color: 0xffffff` (white), meaning texture colors are unchanged. The directional light and ambient light do the shading.

But the requirement says "make sure each cube face is clearly distinguishable" (or similar). The lighting does this naturally.

OK, let me go with:
- ambient light: 0x606060, intensity: 0.6
- directional light: 0xffffff, intensity: 0.7
- material color: 0xffffff for all

But for some blocks, I want specific colors. Water material will have `color: 0x88ccff` (light blue) to tint the texture or just be solid.

Alright. Writing the code now. I'll try to keep it around 500 lines.

Wait, actually, for the textures to actually appear with lighting, I need the material's `map` set. If I just set `color`, the block is a solid color. Since I'm creating procedural textures, the texture is in the `map`. So:

```javascript
const material = new THREE.MeshLambertMaterial({ map: texture, color: 0xffffff });
```

The texture's pixels are the colors. Lighting multiplies by material.color (white) and the light.

OK let me write it. I'll create all the textures as 16x16 canvases.

I also realize I should update the InstancedMesh count to match the number of set matrices. If, during the fill pass, we add fewer instances than counted (shouldn't happen, but just in case), three.js might draw extra instances with identity matrices. But since we only set `count` matrices and the InstancedMesh's `count` property is the number of instances, it should be fine. Actually, when creating `new THREE.InstancedMesh(geometry, material, count)`, the instanceMatrix BufferAttribute is sized for `count`. If we don't set all matrices (e.g., the count was too high), the remaining ones are identity matrices (at origin). So we need accurate counts.

My two-pass should give accurate counts if `isVisible` always returns the same value in both passes. Yes, since `isVisible` only depends on the block world, which is not modified between passes.

One issue: `isVisible` for a block at the edge of the world treats out-of-bounds as air. So a block at x=0 (with no left neighbor) is always visible. This means the side faces of the world are always rendered. For an island-style world, this is fine.

But actually, if we have solid blocks at the edge, the side faces would be visible, which makes the world look like a floating island. Since we're not planning to have a floating island, this could look weird—the edge of our 128x128 world would show flat walls of blocks on the sides.

To avoid this, I can return false for visibility at the world borders? But that would create holes at the edge if the camera flies there. Better to generate terrain that naturally slopes down at the borders. Or just ignore edge cases and let the sides show; it's fine for a demo.

Alternatively, I can generate terrain with smooth falloff near the borders (like an island in the middle of the ocean). This way, the edges are at sea level (water), and there are no visible side faces.

Let me use a falloff:

```javascript
const falloff = (x, z, size) => {
    const dx = Math.abs(x - size / 2) / (size / 2);
    const dz = Math.abs(z - size / 2) / (size / 2);
    return Math.max(dx, dz); // 0 at center, 1 at edge
};
// In height function:
const f = falloff(x, z, WORLD_SIZE);
// Raise terrain in the middle, lower at edges:
h += (1 - f) * 20 - 10; // etc.
```

Hmm, this requires some tuning. Alternatively, I can just leave it; the world edges will show some cubes but the camera path won't go that far.

Let me set the camera path well inside the world bounds so the edges aren't visible.

Alright, I'll write the code now.

One more thing: The water should be flat at SEA_LEVEL. Currently, I set water blocks from h+1 to SEA_LEVEL. This fills the space between the terrain height and sea level, creating lakes. Good.

But for terrain height `h` above sea level, no water blocks are placed. Good.

Now, let me write the final code.

Actually, I realize that setBlock uses `MAX_HEIGHT` for y range. If the terrain height is `Math.floor(h)` and h can be up to maybe 60, trees can add up to 8 blocks above that, so max block y could be ~68. With MAX_HEIGHT=80, there's room.

Let me set MAX_HEIGHT = 60 to save memory? Or 80 to be safe. Use 80.

Also, the InstancedMesh iteration is x, z, y. For cache efficiency, I should iterate y last for each (x, z), because the 3D array index uses y fastest. My loop:
```javascript
for (let x = 0; x < WORLD_SIZE; x++)
    for (let z = 0; z < WORLD_SIZE; z++)
        for (let y = 2; y < MAX_HEIGHT; y++)
```
This means for each (x,z), we access world[index] = (x*SIZE+z)*MAX_HEIGHT + y, which increments y quickly. This is cache-friendly.

OK, here's the code.

Actually, I'm a bit worried about the total number of instances. A 128x128x80 world with 1.3M blocks, maybe ~500k visible instances if the terrain is fully solid. InstancedMesh with 500k instances is a lot and may be slow to render. But since we only render cubes, the GPU can handle it? Maybe not. Let me limit the world size to 60x60? No, I'll keep 128 but note that this is a demo.

Actually, typical voxel worlds use mesh generation with multiple cubes per chunk. Using one InstancedMesh per block type with up to 500k instances might be too much. But for this demo, let's see.

Wait, visible instances: A solid cube in the interior is not visible. For a heightmap terrain, the number of visible blocks is roughly the surface area * average vertical thickness /? Actually, the surface blocks (top layer) are visible. For a 128x128 grid, that's 16,384 surface blocks. But with overhangs and trees, it could be more. In practice, maybe 30-50k blocks are visible. That's okay.

But the `isVisible` function would count blocks adjacent to water (underwater blocks). For a lake of, say, 30x30x10 blocks, the underwater terrain layer directly beneath the water is visible. That adds more.

Total visible blocks might be around 50-100k, which is fine for InstancedMesh.

But there's a problem: InstancedMesh with multiple materials uses a single draw call per material. For an InstancedMesh with 6 materials (BoxGeometry 6 groups), each material set with its own draw call. So per InstancedMesh, there are 6 draw calls (one per face material). With ~5 block types, that's 30 draw calls. This is fine.

Actually, each group in the geometry is rendered with its corresponding material in the array. So for each type, there are 6 draw calls (unless the material array has duplicates, which three.js doesn't optimize away). For ~5 types, 30 draw calls—fine.

OK, let's write the code now.

Let me also consider that the default BoxGeometry has UV coordinates that map to the full 0-1 range for each face. The textures will repeat per face.

Now, here's the comprehensive script. I'll code the textures as a map from material index to a callback that draws on a canvas.

Given the complexity, let me organize the code:

1. Setup (renderer, scene, camera, lights)
2. Noise utilities
3. World generation (terrain + trees)
4. Materials & textures
5. Mesh generation
6. Environment (clouds, sun)
7. Animation (flythrough)

I'll put all the code in a single script tag.

Let me write this out now.

Note: I'm using three.js r128, which has `THREE.FlyControls`? No, but I can implement camera animation manually.

Here's the flythrough animation:

```javascript
const points = [
    new THREE.Vector3(10, 30, 10),
    new THREE.Vector3(30, 40, 30),
    new THREE.Vector3(60, 50, 70),
    new THREE.Vector3(80, 35, 90),
    new THREE.Vector3(90, 25, 60),
    new THREE.Vector3(70, 35, 30),
    new THREE.Vector3(40, 45, 20),
    new THREE.Vector3(10, 35, 10),
];
const curve = new THREE.CatmullRomCurve3(points, false);

const totalTime = 20; // seconds
let t = 0;
let lastTime = performance.now();

function animate(time) {
    requestAnimationFrame(animate);
    let delta = (time - lastTime) / 1000;
    lastTime = time;
    t += delta / totalTime;
    if (t > 1) t = 0;

    const pos = curve.getPoint(t);
    const look = curve.getPoint(Math.min(t + 0.05, 1));
    camera.position.copy(pos);
    camera.lookAt(look);

    // Move clouds
    cloudGroup.children.forEach(c => {
        c.position.x += 1.5 * delta;
        c.position.z += 0.8 * delta;
        if (c.position.x > 160) c.position.x = -32;
        if (c.position.z > 160) c.position.z = -32;
    });

    renderer.render(scene, camera);
}
requestAnimationFrame(animate);
```

With the animate function receiving the time.

Let me also add a resize handler.

OK, I'll write the entire thing now in the code block. This will be long.

One quick check: `THREE.InstancedMesh` was introduced in r122? Actually, it's been there a long time. In r128, it's `THREE.InstancedMesh`. The constructor is `new THREE.InstancedMesh(geometry, material, count)`.

Also, setting the matrix for each instance: `mesh.setMatrixAt(i, matrix)`. After that, `mesh.instanceMatrix.needsUpdate = true`.

Now, writing the code:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Voxel Terrain</title>
    <style>
        body { margin: 0; overflow: hidden; background: #000; }
        canvas { display: block; }
        #info {
            position: absolute; top: 10px; left: 10px; color: white;
            font-family: Arial, sans-serif; font-size: 14px;
            background: rgba(0,0,0,0.5); padding: 10px; border-radius: 4px;
            pointer-events: none;
        }
    </style>
</head>
<body>
<div id="info">Flythrough</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
// ... code
</script>
</body>
</html>
```

Let me now actually type out the implementation.

Given that this is a text-based response, I can't execute the code, but I'll provide the complete script.

Wait, I should also include the `THREE.InstancedMesh` check: In r128, InstancedMesh's `setMatrixAt` is available. Yes.

Also, for creating the canvas textures, I'll use `THREE.CanvasTexture` which takes a canvas element.

Let me write a helper:
```javascript
function createTexture(draw) {
    const canvas = document.createElement('canvas');
    canvas.width = 16;
    canvas.height = 16;
    const ctx = canvas.getContext('2d');
    draw(ctx);
    const texture = new THREE.CanvasTexture(canvas);
    texture.magFilter = THREE.NearestFilter;
    texture.minFilter = THREE.LinearMipMapLinearFilter; // maybe Nearest to keep pixelated?
    texture.wrapS = THREE.RepeatWrapping;
    texture.wrapT = THREE.RepeatWrapping;
    return texture;
}
```

For pixelated look (Minecraft-like), use NearestFilter for both min and mag. But textures are 16x16, so Nearest gives sharp pixels.

Set:
```javascript
texture.magFilter = THREE.NearestFilter;
texture.minFilter = THREE.NearestFilter;
```

Actually, to avoid mipmapping issues, set `texture.generateMipmaps = false;` and use `NearestFilter`.

OK.

Now, the actual code (abridged to fit the response length; but I'll be thorough).

Actually, I realize that using `InstancedMesh` with a material array for each block type requires that the material array has exactly the same number of elements as the geometry groups. Since we pass an array of 6 materials, it works.

But for the `blockGeo`, I need to use `new THREE.BoxGeometry(1, 1, 1)`. The BoxGeometry has 6 groups, one per face.

Wait, I need to verify: BoxGeometry has 4 vertices per face, 6 faces => 24 vertices. The groups correspond to the 6 material indices. Yes.

Now, the `getBlockMaterials(type)` function:
```javascript
function getBlockMaterials(type) {
    const tex = textures[type];
    const mats = [];
    const materialIndex = 0; // default
    for (let i = 0; i < 6; i++) {
        mats.push(tex[i]); // or a shared material
    }
    return mats;
}
```

But some blocks, like GRASS, need different top and side textures. So the material array for GRASS would be:
```
[sideTexture, sideTexture, topTexture, bottomTexture, sideTexture, sideTexture]
```

For DIRT, all same [`dirtTexture`, ...].
For WOOD, side and top/bottom different.
etc.

I'll create each material separately:
```javascript
const dirtMat = new THREE.MeshLambertMaterial({ map: dirtTexture });
const grassSideMat = new THREE.MeshLambertMaterial({ map: grassSideTexture });
const grassTopMat = new THREE.MeshLambertMaterial({ map: grassTopTexture });
const stoneMat = new THREE.MeshLambertMaterial({ map: stoneTexture });
const sandMat = new THREE.MeshLambertMaterial({ map: sandTexture });
const woodSideMat = new THREE.MeshLambertMaterial({ map: woodSideTexture });
const leavesMat = new THREE.MeshLambertMaterial({ map: leavesTexture });
const snowMat = new THREE.MeshLambertMaterial({ map: snowTexture });
const waterMat = new THREE.MeshLambertMaterial({
    color: 0x4488ff,
    transparent: true,
    opacity: 0.7,
    side: THREE.DoubleSide,
});
```

Then `getBlockMaterials` returns an array of these for each face.

But wait, for LEAVES, the material is semi-transparent? In Minecraft, leaves are opaque with transparency in the texture. For simplicity, I'll make leaves slightly transparent (alpha: 0.8) to add variation. Actually, I'll make them fully opaque.

For water, I'll use a single material without a texture. But the InstancedMesh for water needs 6 materials (one per face) even if they're all the same water material. So I can pass `[waterMat, waterMat, waterMat, waterMat, waterMat, waterMat]`.

But three.js might combine them? No, it still makes 6 draw calls. Fine.

Alright, let me write the complete code. Since this is long, I'll present it as a complete HTML file.

Wait, actually, I need to include XML escape? No, this is raw HTML/JS.

Let me also add some trees. Tree generation is:

```javascript
function generateTree(x, y, z) {
    const h = 4 + (Math.random() * 3 | 0);
    for (let i = 0; i < h; i++) {
        if (getBlock(x, y + i, z) === BLOCK.AIR) {
            setBlock(x, y + i, z, BLOCK.WOOD);
        }
    }
    const top = y + h;
    for (let dy = -2; dy <= 1; dy++) {
        const r = dy < 0 ? 2 : (dy < 1 ? 2 : 1);
        for (let dx = -r; dx <= r; dx++) {
            for (let dz = -r; dz <= r; dz++) {
                if (Math.abs(dx) === r && Math.abs(dz) === r && Math.random() < 0.3) continue;
                const lx = x + dx;
                const ly = top + dy;
                const lz = z + dz;
                if (getBlock(lx, ly, lz) === BLOCK.AIR) {
                    setBlock(lx, ly, lz, BLOCK.LEAVES);
                }
            }
        }
    }
}
```

And in world gen:
```javascript
// After terrain generation, randomly place trees:
for (let x = 2; x < WORLD_SIZE - 2; x++) {
    for (let z = 2; z < WORLD_SIZE - 2; z++) {
        if (hash2D(x, z, 12345) < 0.005) {
            const h = Math.floor(heights[z * WORLD_SIZE + x]);
            if (h >= SEA_LEVEL + 2 && h < SNOW_LEVEL - 2) {
                // Ensure the top block is grass
                if (getBlock(x, h, z) === BLOCK.GRASS) {
                    if (getBlock(x, h + 1, z) === BLOCK.AIR) {
                        generateTree(x, h + 1, z);
                    }
                }
            }
        }
    }
}
```

But iterating x,z and checking hash for every cell is O(WORLD_SIZE^2). For 128x128=16k cells, trivial. Great.

Actually, I should iterate only every few cells to avoid trees too close together. Or use a spatial hash. For simplicity, just use probability 0.005 per cell, which gives ~80 trees.

OK.

Now, the heights array needs to be stored before generating the block world? Actually, I generate heights on the fly for each column. I can compute heights first and store them, or compute twice. Let me store in a Float32Array for efficiency.

Here's the world generation sequence:

1. Generate heights using fBm noise.
2. Fill the world with terrain blocks.
3. Carve water.
4. Generate trees.
5. Build InstancedMeshes.

Let me combine 2 and 3 in one loop, and add water after.

Actually, step 2: for each column, iterate y from 0 to terrainHeight, set block type based on rules. Then add water from terrainHeight+1 to SEA_LEVEL.

Step 4: generate trees after terrain (but only on grassy areas above water).

OK, I think I have a complete plan. Let me now write the final code.

Actually, I realize that writing a fully working three.js application in this response is complex but doable. I'll provide the full code.

Since the code is long, let me focus on correctness over brevity. I'll include comments.

Let me write it.