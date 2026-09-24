```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Voxel World Flythrough</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { overflow: hidden; background: #000; }
canvas { display: block; }
</style>
</head>
<body>
<script type="importmap">
{
  "imports": {
    "three": "https://unpkg.com/three@0.186.0/build/three.module.js",
    "three/addons/": "https://unpkg.com/three@0.186.0/examples/jsm/"
  }
}
</script>
<script type="module">
import * as THREE from 'three';
import { CatmullRomCurve3 } from 'three';

// ============================================
// NOISE GENERATION (Simple Perlin-like noise)
// ============================================
class Noise {
  constructor(seed = 12345) {
    this.p = new Array(512);
    this.perm = new Array(256);
    let s = seed;
    for (let i = 0; i < 256; i++) {
      s = (s * 16807) % 2147483647;
      this.perm[i] = s & 255;
    }
    for (let i = 0; i < 512; i++) this.p[i] = this.perm[i & 255];
  }
  fade(t) { return t * t * t * (t * (t * 6 - 15) + 10); }
  lerp(a, b, t) { return a + t * (b - a); }
  grad(hash, x, y) {
    const h = hash & 7;
    const u = h < 4 ? x : y;
    const v = h < 4 ? y : x;
    return ((h & 1) ? -u : u) + ((h & 2) ? -2 * v : 2 * v);
  }
  noise2d(x, y) {
    const X = Math.floor(x) & 255, Y = Math.floor(y) & 255;
    x -= Math.floor(x); y -= Math.floor(y);
    const u = this.fade(x), v = this.fade(y);
    const A = this.p[X] + Y, B = this.p[X + 1] + Y;
    return this.lerp(
      this.lerp(this.grad(this.p[A], x, y), this.grad(this.p[B], x - 1, y), u),
      this.lerp(this.grad(this.p[A + 1], x, y - 1), this.grad(this.p[B + 1], x - 1, y - 1), u), v
    );
  }
  fbm(x, y, octaves = 6, lacunarity = 2.0, gain = 0.5) {
    let amp = 1, freq = 1, sum = 0, max = 0;
    for (let i = 0; i < octaves; i++) {
      sum += this.noise2d(x * freq, y * freq) * amp;
      max += amp;
      amp *= gain; freq *= lacunarity;
    }
    return sum / max;
  }
  ridged(x, y, octaves = 6) {
    let amp = 1, freq = 1, sum = 0, max = 0;
    for (let i = 0; i < octaves; i++) {
      const n = Math.abs(this.noise2d(x * freq, y * freq));
      sum += (1 - n) * amp;
      max += amp;
      amp *= 0.5; freq *= 2;
    }
    return sum / max;
  }
}

// ============================================
// PROCEDURAL TEXTURES (Pixel-art on Canvas)
// ============================================
function createBlockTextures() {
  const atlasSize = 256;
  const tileSize = 16;
  const canvas = document.createElement('canvas');
  canvas.width = atlasSize;
  canvas.height = atlasSize;
  const ctx = canvas.getContext('2d');
  ctx.imageSmoothingEnabled = false;

  const textures = {
    grass_top: 0, grass_side: 1, dirt: 2, stone: 3,
    sand: 4, snow: 5, water: 6, wood: 7, leaves: 8,
    grass_side_snow: 9
  };
  let tileIndex = 0;

  function drawTile(fn) {
    const x = (tileIndex % 16) * tileSize;
    const y = Math.floor(tileIndex / 16) * tileSize;
    ctx.save();
    ctx.translate(x, y);
    fn(ctx, tileSize);
    ctx.restore();
    tileIndex++;
  }

  // Grass top
  drawTile((ctx, s) => {
    for (let y = 0; y < s; y++) for (let x = 0; x < s; x++) {
      const v = 0.85 + Math.random() * 0.2;
      ctx.fillStyle = `rgb(${Math.floor(60*v)},${Math.floor(160*v)},${Math.floor(40*v)})`;
      ctx.fillRect(x, y, 1, 1);
    }
  });
  // Grass side
  drawTile((ctx, s) => {
    for (let y = 0; y < s; y++) for (let x = 0; x < s; x++) {
      const isGrass = y < 3;
      const v = 0.8 + Math.random() * 0.2;
      if (isGrass) {
        ctx.fillStyle = `rgb(${Math.floor(60*v)},${Math.floor(150*v)},${Math.floor(30*v)})`;
      } else {
        ctx.fillStyle = `rgb(${Math.floor(100*v)},${Math.floor(70*v)},${Math.floor(40*v)})`;
      }
      ctx.fillRect(x, y, 1, 1);
    }
  });
  // Dirt
  drawTile((ctx, s) => {
    for (let y = 0; y < s; y++) for (let x = 0; x < s; x++) {
      const v = 0.7 + Math.random() * 0.25;
      ctx.fillStyle = `rgb(${Math.floor(100*v)},${Math.floor(70*v)},${Math.floor(40*v)})`;
      ctx.fillRect(x, y, 1, 1);
    }
  });
  // Stone
  drawTile((ctx, s) => {
    for (let y = 0; y < s; y++) for (let x = 0; x < s; x++) {
      const v = 0.5 + Math.random() * 0.3;
      const c = Math.floor(120 * v);
      ctx.fillStyle = `rgb(${c},${c},${c})`;
      ctx.fillRect(x, y, 1, 1);
    }
    // cracks
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(2, 2); ctx.lineTo(14, 12);
    ctx.moveTo(14, 2); ctx.lineTo(4, 14);
    ctx.stroke();
  });
  // Sand
  drawTile((ctx, s) => {
    for (let y = 0; y < s; y++) for (let x = 0; x < s; x++) {
      const v = 0.9 + Math.random() * 0.15;
      ctx.fillStyle = `rgb(${Math.floor(230*v)},${Math.floor(210*v)},${Math.floor(160*v)})`;
      ctx.fillRect(x, y, 1, 1);
    }
  });
  // Snow
  drawTile((ctx, s) => {
    for (let y = 0; y < s; y++) for (let x = 0; x < s; x++) {
      const v = 0.95 + Math.random() * 0.05;
      ctx.fillStyle = `rgb(${Math.floor(255*v)},${Math.floor(255*v)},${Math.floor(255*v)})`;
      ctx.fillRect(x, y, 1, 1);
    }
  });
  // Water (animated later via shader)
  drawTile((ctx, s) => {
    for (let y = 0; y < s; y++) for (let x = 0; x < s; x++) {
      const v = 0.4 + Math.random() * 0.2;
      ctx.fillStyle = `rgb(${Math.floor(30*v)},${Math.floor(80*v)},${Math.floor(180*v)})`;
      ctx.fillRect(x, y, 1, 1);
    }
  });
  // Wood
  drawTile((ctx, s) => {
    for (let y = 0; y < s; y++) for (let x = 0; x < s; x++) {
      const ring = Math.sin(x * 0.8) * 2 + y * 0.1;
      const v = 0.5 + Math.sin(ring) * 0.15 + Math.random() * 0.1;
      ctx.fillStyle = `rgb(${Math.floor(120*v)},${Math.floor(70*v)},${Math.floor(30*v)})`;
      ctx.fillRect(x, y, 1, 1);
    }
    // ends
    ctx.fillStyle = '#5a3818';
    ctx.fillRect(0, 0, s, 2);
    ctx.fillRect(0, s-2, s, 2);
  });
  // Leaves
  drawTile((ctx, s) => {
    for (let y = 0; y < s; y++) for (let x = 0; x < s; x++) {
      const v = 0.6 + Math.random() * 0.3;
      const g = Math.floor(100 + 80 * v);
      ctx.fillStyle = `rgb(${Math.floor(20*v)},${g},${Math.floor(20*v)})`;
      ctx.fillRect(x, y, 1, 1);
    }
  });
  // Grass side snowy
  drawTile((ctx, s) => {
    for (let y = 0; y < s; y++) for (let x = 0; x < s; x++) {
      const isSnow = y < 3;
      const v = 0.8 + Math.random() * 0.2;
      if (isSnow) {
        ctx.fillStyle = `rgb(${Math.floor(255*v)},${Math.floor(255*v)},${Math.floor(255*v)})`;
      } else {
        ctx.fillStyle = `rgb(${Math.floor(100*v)},${Math.floor(70*v)},${Math.floor(40*v)})`;
      }
      ctx.fillRect(x, y, 1, 1);
    }
  });

  const texture = new THREE.CanvasTexture(canvas);
  texture.magFilter = THREE.NearestFilter;
  texture.minFilter = THREE.NearestFilter;
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;

  return { texture, textures, tileSize, atlasSize };
}

// ============================================
// BLOCK GEOMETRY WITH PER-FACE UVS
// ============================================
function createBlockGeometry() {
  const geom = new THREE.BoxGeometry(1, 1, 1);
  // UV layout: each face gets a 16x16 region in 256x256 atlas
  const uvs = geom.attributes.uv.array;
  const tileU = 16 / 256;
  const tileV = 16 / 256;

  function setFaceUV(faceIndex, tileX, tileY) {
    const u0 = tileX * tileU;
    const v0 = 1 - (tileY + 1) * tileV;
    const u1 = (tileX + 1) * tileU;
    const v1 = 1 - tileY * tileV;
    const base = faceIndex * 4 * 2;
    // three.js box geometry face order: +x, -x, +y, -y, +z, -z
    uvs[base + 0] = u1; uvs[base + 1] = v0;
    uvs[base + 2] = u0; uvs[base + 3] = v0;
    uvs[base + 4] = u1; uvs[base + 5] = v1;
    uvs[base + 6] = u0; uvs[base + 7] = v1;
  }

  // We'll set UVs per instance via custom attribute, but base geometry needs valid UVs
  // Default to grass top
  for (let f = 0; f < 6; f++) setFaceUV(f, 0, 0);
  geom.attributes.uv.needsUpdate = true;
  return geom;
}

// ============================================
// WORLD GENERATION
// ============================================
const WORLD_W = 128;
const WORLD_D = 128;
const MAX_HEIGHT = 48;
const WATER_LEVEL = 12;

const noise = new Noise(42);
const noise2 = new Noise(123);
const noise3 = new Noise(456);

function getHeight(x, z) {
  const nx = x / WORLD_W, nz = z / WORLD_D;
  // Continental noise
  const continental = noise.fbm(nx * 2, nz * 2, 4, 2, 0.5);
  // Mountain noise
  const mountain = Math.pow(noise2.fbm(nx * 4, nz * 4, 6, 2.2, 0.45), 1.5);
  // Ridge noise for ridges
  const ridge = noise3.ridged(nx * 8, nz * 8, 4);

  let h = continental * 0.5 + mountain * 0.4 + ridge * 0.1;
  h = Math.pow(h, 1.2);
  return Math.floor(h * MAX_HEIGHT);
}

function getMoisture(x, z) {
  return noise2.fbm(x * 0.01, z * 0.01, 4, 2, 0.5);
}

function getBiome(height, moisture, x, z) {
  if (height <= WATER_LEVEL) return 'water';
  if (height <= WATER_LEVEL + 2) return 'sand';
  if (height > MAX_HEIGHT * 0.75) return 'snow';
  if (height > MAX_HEIGHT * 0.55) return 'stone';
  return 'grass';
}

// Generate column data
const columns = new Array(WORLD_W * WORLD_D);
for (let z = 0; z < WORLD_D; z++) {
  for (let x = 0; x < WORLD_W; x++) {
    const h = getHeight(x, z);
    const m = getMoisture(x, z);
    const biome = getBiome(h, m, x, z);
    columns[z * WORLD_W + x] = { x, z, height: h, biome, moisture: m };
  }
}

// Place trees
const trees = [];
for (let z = 3; z < WORLD_D - 3; z++) {
  for (let x = 3; x < WORLD_W - 3; x++) {
    const col = columns[z * WORLD_W + x];
    if (col.biome === 'grass' && col.height > WATER_LEVEL + 2 && noise.noise2d(x * 0.1, z * 0.1) > 0.6) {
      if (Math.random() < 0.015) {
        trees.push({ x, z, height: col.height, trunkH: 4 + Math.floor(Math.random() * 3) });
      }
    }
  }
}

// ============================================
// INSTANCED MESHES
// ============================================
const { texture, textures, tileSize, atlasSize } = createBlockTextures();
const geom = createBlockGeometry();

// Block types and their face texture indices [top, bottom, +x, -x, +y, -y] -> actually three.js order: +x, -x, +y, -y, +z, -z
// We'll use a custom attribute for texture index per face per instance? Too heavy.
// Instead: separate InstancedMesh per block type, each with its own material (texture offset via material).
// But we need per-face shading (different textures per face). Solution: Use a single material with atlas, and encode face texture IDs in vertex attributes.
// Simpler: Create multiple geometries with baked UVs per block type, use InstancedMesh per type.

function makeBlockMaterial() {
  return new THREE.MeshLambertMaterial({
    map: texture,
    transparent: false,
    alphaTest: 0.1,
    vertexColors: false
  });
}

// We'll create a custom geometry per block type with correct UVs baked in.
function createTypedGeometry(type) {
  const g = new THREE.BoxGeometry(1, 1, 1);
  const uvs = g.attributes.uv.array;
  const tileU = 16 / 256;
  const tileV = 16 / 256;

  function setFace(face, tx, ty) {
    const u0 = tx * tileU, v0 = 1 - (ty + 1) * tileV;
    const u1 = (tx + 1) * tileU, v1 = 1 - ty * tileV;
    const b = face * 8;
    uvs[b+0]=u1; uvs[b+1]=v0;
    uvs[b+2]=u0; uvs[b+3]=v0;
    uvs[b+4]=u1; uvs[b+5]=v1;
    uvs[b+6]=u0; uvs[b+7]=v1;
  }

  // Face indices: 0=+x, 1=-x, 2=+y(top), 3=-y(bottom), 4=+z, 5=-z
  switch (type) {
    case 'grass':
      setFace(0, textures.grass_side, 0); // +x
      setFace(1, textures.grass_side, 0); // -x
      setFace(2, textures.grass_top, 0);  // top
      setFace(3, textures.dirt, 0);       // bottom
      setFace(4, textures.grass_side, 0); // +z
      setFace(5, textures.grass_side, 0); // -z
      break;
    case 'grass_snow':
      setFace(0, textures.grass_side_snow, 0);
      setFace(1, textures.grass_side_snow, 0);
      setFace(2, textures.snow, 0);
      setFace(3, textures.dirt, 0);
      setFace(4, textures.grass_side_snow, 0);
      setFace(5, textures.grass_side_snow, 0);
      break;
    case 'dirt':
      setFace(0, textures.dirt, 0); setFace(1, textures.dirt, 0);
      setFace(2, textures.dirt, 0); setFace(3, textures.dirt, 0);
      setFace(4, textures.dirt, 0); setFace(5, textures.dirt, 0);
      break;
    case 'stone':
      setFace(0, textures.stone, 0); setFace(1, textures.stone, 0);
      setFace(2, textures.stone, 0); setFace(3, textures.stone, 0);
      setFace(4, textures.stone, 0); setFace(5, textures.stone, 0);
      break;
    case 'sand':
      setFace(0, textures.sand, 0); setFace(1, textures.sand, 0);
      setFace(2, textures.sand, 0); setFace(3, textures.sand, 0);
      setFace(4, textures.sand, 0); setFace(5, textures.sand, 0);
      break;
    case 'snow':
      setFace(0, textures.snow, 0); setFace(1, textures.snow, 0);
      setFace(2, textures.snow, 0); setFace(3, textures.snow, 0);
      setFace(4, textures.snow, 0); setFace(5, textures.snow, 0);
      break;
    case 'wood':
      setFace(0, textures.wood, 0); setFace(1, textures.wood, 0);
      setFace(2, textures.wood, 0); setFace(3, textures.wood, 0); // top/bottom same
      setFace(4, textures.wood, 0); setFace(5, textures.wood, 0);
      break;
    case 'leaves':
      setFace(0, textures.leaves, 0); setFace(1, textures.leaves, 0);
      setFace(2, textures.leaves, 0); setFace(3, textures.leaves, 0);
      setFace(4, textures.leaves, 0); setFace(5, textures.leaves, 0);
      break;
  }
  g.attributes.uv.needsUpdate = true;
  return g;
}

// Count blocks per type
const counts = { grass:0, grass_snow:0, dirt:0, stone:0, sand:0, snow:0, water:0, wood:0, leaves:0 };

// Terrain blocks
for (const col of columns) {
  const { x, z, height, biome } = col;
  for (let y = 0; y <= height; y++) {
    let type;
    if (y === height) {
      if (biome === 'grass') type = (height > MAX_HEIGHT * 0.7) ? 'grass_snow' : 'grass';
      else if (biome === 'snow') type = 'snow';
      else if (biome === 'sand') type = 'sand';
      else if (biome === 'stone') type = 'stone';
      else type = 'grass';
    } else if (y === height - 1) {
      type = (biome === 'grass' || biome === 'grass_snow') ? 'dirt' : (biome === 'snow' ? 'snow' : biome);
    } else if (y > height - 4) {
      type = (biome === 'sand') ? 'sand' : 'dirt';
    } else {
      type = 'stone';
    }
    counts[type]++;
  }
  // Water column
  if (height < WATER_LEVEL) {
    for (let y = height + 1; y <= WATER_LEVEL; y++) counts.water++;
  }
}

// Trees
for (const t of trees) {
  for (let y = 0; y < t.trunkH; y++) counts.wood++;
  // Leaves: 3x3x3 blob at top
  const lh = t.height + t.trunkH;
  for (let dy = 0; dy < 3; dy++) {
    for (let dx = -1; dx <= 1; dx++) {
      for (let dz = -1; dz <= 1; dz++) {
        if (dx===0 && dz===0 && dy===0) continue; // trunk center
        if (Math.abs(dx)===1 && Math.abs(dz)===1 && dy===2) continue; // corners top
        counts.leaves++;
      }
    }
  }
}

// Create InstancedMeshes
const meshes = {};
const materials = {};
for (const type of Object.keys(counts)) {
  if (counts[type] === 0) continue;
  const mat = makeBlockMaterial();
  if (type === 'water') {
    mat.transparent = true;
    mat.opacity = 0.65;
    mat.depthWrite = false;
  }
  if (type === 'leaves') {
    mat.alphaTest = 0.5;
    mat.transparent = true;
  }
  materials[type] = mat;
  meshes[type] = new THREE.InstancedMesh(createTypedGeometry(type), mat, counts[type]);
  meshes[type].instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  meshes[type].count = 0;
}

// Fill instances
const dummy = new THREE.Object3D();
let indices = { grass:0, grass_snow:0, dirt:0, stone:0, sand:0, snow:0, water:0, wood:0, leaves:0 };

for (const col of columns) {
  const { x, z, height, biome } = col;
  for (let y = 0; y <= height; y++) {
    let type;
    if (y === height) {
      if (biome === 'grass') type = (height > MAX_HEIGHT * 0.7) ? 'grass_snow' : 'grass';
      else if (biome === 'snow') type = 'snow';
      else if (biome === 'sand') type = 'sand';
      else if (biome === 'stone') type = 'stone';
      else type = 'grass';
    } else if (y === height - 1) {
      type = (biome === 'grass' || biome === 'grass_snow') ? 'dirt' : (biome === 'snow' ? 'snow' : biome);
    } else if (y > height - 4) {
      type = (biome === 'sand') ? 'sand' : 'dirt';
    } else {
      type = 'stone';
    }
    dummy.position.set(x - WORLD_W/2, y, z - WORLD_D/2);
    dummy.updateMatrix();
    meshes[type].setMatrixAt(indices[type]++, dummy.matrix);
  }
  if (height < WATER_LEVEL) {
    for (let y = height + 1; y <= WATER_LEVEL; y++) {
      dummy.position.set(x - WORLD_W/2, y, z - WORLD_D/2);
      dummy.updateMatrix();
      meshes.water.setMatrixAt(indices.water++, dummy.matrix);
    }
  }
}

for (const t of trees) {
  const baseY = t.height;
  for (let y = 0; y < t.trunkH; y++) {
    dummy.position.set(t.x - WORLD_W/2, baseY + 1 + y, t.z - WORLD_D/2);
    dummy.updateMatrix();
    meshes.wood.setMatrixAt(indices.wood++, dummy.matrix);
  }
  const lh = baseY + t.trunkH;
  for (let dy = 0; dy < 3; dy++) {
    for (let dx = -1; dx <= 1; dx++) {
      for (let dz = -1; dz <= 1; dz++) {
        if (dx===0 && dz===0 && dy===0) continue;
        if (Math.abs(dx)===1 && Math.abs(dz)===1 && dy===2) continue;
        dummy.position.set(t.x + dx - WORLD_W/2, lh + dy, t.z + dz - WORLD_D/2);
        dummy.updateMatrix();
        meshes.leaves.setMatrixAt(indices.leaves++, dummy.matrix);
      }
    }
  }
}

for (const m of Object.values(meshes)) {
  m.instanceMatrix.needsUpdate = true;
  m.computeBoundingSphere();
}

// ============================================
// SCENE SETUP
// ============================================
const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x87ceeb, 0.0045);

for (const m of Object.values(meshes)) scene.add(m);

// Sky dome
const skyGeo = new THREE.SphereGeometry(500, 32, 16);
const skyMat = new THREE.MeshBasicMaterial({
  side: THREE.BackSide,
  color: 0x87ceeb,
  fog: false
});
const sky = new THREE.Mesh(skyGeo, skyMat);
scene.add(sky);

// Sun
const sunGeo = new THREE.SphereGeometry(15, 16, 16);
const sunMat = new THREE.MeshBasicMaterial({ color: 0xffee88, fog: false });
const sun = new THREE.Mesh(sunGeo, sunMat);
scene.add(sun);

// Clouds (instanced boxes)
const cloudGeo = new THREE.BoxGeometry(1, 1, 1);
const cloudMat = new THREE.MeshBasicMaterial({ color: 0xffffff, fog: true, transparent: true, opacity: 0.9 });
const cloudCount = 120;
const clouds = new THREE.InstancedMesh(cloudGeo, cloudMat, cloudCount);
const cloudData = [];
for (let i = 0; i < cloudCount; i++) {
  const x = (Math.random() - 0.5) * WORLD_W * 2;
  const z = (Math.random() - 0.5) * WORLD_D * 2;
  const y = 40 + Math.random() * 30;
  const scale = 3 + Math.random() * 5;
  const parts = 3 + Math.floor(Math.random() * 4);
  cloudData.push({ x, z, y, scale, parts, speed: 0.5 + Math.random() * 0.5, offset: Math.random() * Math.PI * 2 });
}
for (let i = 0; i < cloudCount; i++) {
  const d = cloudData[i];
  for (let p = 0; p < d.parts; p++) {
    dummy.position.set(d.x + (Math.random()-0.5)*d.scale, d.y + (Math.random()-0.5)*2, d.z + (Math.random()-0.5)*d.scale);
    dummy.scale.setScalar(0.8 + Math.random() * 0.6);
    dummy.updateMatrix();
    clouds.setMatrixAt(clouds.count++, dummy.matrix);
  }
}
clouds.instanceMatrix.needsUpdate = true;
scene.add(clouds);

// Lighting
const hemi = new THREE.HemisphereLight(0xffffee, 0x444466, 1.2);
scene.add(hemi);
const dir = new THREE.DirectionalLight(0xffffee, 1.5);
dir.position.set(100, 200, 50);
dir.castShadow = false;
scene.add(dir);

// Camera
const camera = new THREE.PerspectiveCamera(70, innerWidth / innerHeight, 0.1, 1000);
camera.position.set(-WORLD_W/2, 60, -WORLD_D/2);

// Renderer
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.shadowMap.enabled = false;
document.body.appendChild(renderer.domElement);

// Resize
window.addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});

// ============================================
// CAMERA FLYTHROUGH PATH
// ============================================
const pathPoints = [];
const numPoints = 16;
for (let i = 0; i < numPoints; i++) {
  const t = i / (numPoints - 1);
  const angle = t * Math.PI * 1.5 - Math.PI * 0.25;
  const radius = (WORLD_W * 0.45) * (0.7 + 0.3 * Math.sin(t * Math.PI * 2));
  const x = Math.cos(angle) * radius;
  const z = Math.sin(angle) * radius;
  // Sample height
  const wx = Math.floor(x + WORLD_W/2);
  const wz = Math.floor(z + WORLD_D/2);
  let hy = 40;
  if (wx >= 0 && wx < WORLD_W && wz >= 0 && wz < WORLD_D) {
    hy = columns[wz * WORLD_W + wx].height + 25;
  }
  hy = Math.max(hy, 30);
  pathPoints.push(new THREE.Vector3(x, hy, z));
}
// Close the loop
pathPoints.push(pathPoints[0].clone());

const curve = new CatmullRomCurve3(pathPoints, true, 'centripetal', 0.15);

// Look-at target path (slightly ahead)
const targetCurve = new CatmullRomCurve3(
  pathPoints.map((p, i) => {
    const next = pathPoints[(i + 1) % pathPoints.length];
    return new THREE.Vector3().lerpVectors(p, next, 0.3);
  }), true
);

// ============================================
// ANIMATION LOOP
// ============================================
let startTime = performance.now();
const loopDuration = 180000; // 3 minutes

function animate(time) {
  requestAnimationFrame(animate);
  const t = (time - startTime) / loopDuration;
  const cycle = t % 1;

  // Camera position
  const pos = curve.getPointAt(cycle);
  camera.position.copy(pos);

  // Look target
  const target = targetCurve.getPointAt((cycle + 0.02) % 1);
  camera.lookAt(target);

  // Smooth roll
  camera.rotation.z = Math.sin(cycle * Math.PI * 4) * 0.03;

  // Sun position
  const sunAngle = cycle * Math.PI * 2;
  sun.position.set(
    Math.cos(sunAngle) * 300,
    Math.sin(sunAngle) * 300,
    Math.sin(sunAngle * 0.5) * 100
  );
  // Sky color shift
  const sunHeight = Math.sin(sunAngle);
  const dawn = Math.max(0, 1 - sunHeight * 2);
  skyMat.color.setHSL(0.55, 0.6, 0.55 + dawn * 0.25);
  scene.fog.color.setHSL(0.55, 0.5, 0.55 + dawn * 0.2);
  dir.position.copy(sun.position).multiplyScalar(1.2);
  dir.intensity = 0.8 + Math.max(0, sunHeight) * 1.2;
  hemi.intensity = 0.8 + Math.max(0, sunHeight) * 0.4;
  hemi.groundColor.setHSL(0.1, 0.3, 0.2 + dawn * 0.15);

  // Animate clouds
  for (let i = 0; i < cloudCount; i++) {
    const d = cloudData[i];
    d.x += d.speed * 0.01;
    if (d.x > WORLD_W) d.x = -WORLD_W;
    // Rebuild cloud matrices? Too expensive. Just translate whole mesh.
    // Instead, we'll animate via shader? Simpler: update positions every few frames.
  }
  // Simple cloud drift: translate the whole cloud mesh group
  clouds.position.x = (time * 0.001) % (WORLD_W * 2) - WORLD_W;
  clouds.position.z = Math.sin(time * 0.0003) * 20;

  // Water animation via material opacity pulse
  if (materials.water) {
    materials.water.opacity = 0.55 + Math.sin(time * 0.002) * 0.1;
  }

  renderer.render(scene, camera);
}

requestAnimationFrame(animate);
</script>
</body>
</html>
```