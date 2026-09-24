The user wants a Minecraft-style voxel world with a cinematic flythrough using three.js. Let me break down the requirements:

1. Procedurally generated terrain (128x128 columns) using layered noise
2. Grass-topped hills, snowy peaks, sandy beaches, water with transparency
3. Trees made of wood and leaf blocks
4. Per-face shading for clear cube shapes
5. Procedural pixel-art textures on canvas
6. Sky with sun, fog, drifting block clouds
7. InstancedMesh or merged geometry for performance
8. Automatic cinematic camera flythrough
9. Full-window canvas with resize handling
10. Starts automatically, no interaction needed

I'll need to:
- Create a noise function (simplex or perlin)
- Generate terrain heightmap with multiple octaves
- Determine biomes based on height and moisture
- Create block textures procedurally (grass, dirt, stone, sand, snow, water, wood, leaves)
- Use InstancedMesh for each block type
- Build a camera path using splines
- Add sky, sun, fog, clouds
- Handle animation loop with requestAnimationFrame

Let me write this as a single HTML file.