Let me build a single HTML file that includes a Three.js r186 module, an import map (already provided — but wait, it says "an import map has been provided for you: do not add your own"). So I should just use bare imports with `import * as THREE from 'three'` and `three/addons/...`.

What to build:

- Scene, fog (FogExp2, dark purple)
- Ground plane with high metalness, low roughness, environment-like reflections — simple approach: MeshStandardMaterial with a dark color, roughness 0.15, metalness 0.9, plus maybe a fake reflection via a large dark plane. To get "wet" reflections without a real environment map, I could add a cubemap via PMREM, or just use a RoomEnvironment-like approach. More simply: create a simple gradient environment with a small procedural cube texture, or just use scene.environment from a small generated equirect texture. I can generate a tiny canvas texture (a gradient of neon colors) and set it as the scene environment. This will give the wet street some reflections.

- Buildings: InstancedMesh? Easier: generate buildings as boxes with a custom shader for emissive windows? Requirement: "hundreds of skyscrapers with emissive window lights." Best approach: use an InstancedMesh of a box geometry with a custom ShaderMaterial that draws a window grid with random lit windows and neon colors (pink, cyan, purple). This is efficient and looks nice. Use instance attributes: seed, height, etc.

Building shader: fragment computes a window pattern from local UV, hashes per instance seed, emits neon color for some windows, plus a dark body. Top edge also glows slightly.

- Neon signs: a few planes with emissive material, billboard-ish, plus "sign" text via canvas texture? "Neon signs" — I can make small glowing planes/boxes (billboards) in pink/cyan/purple with a glowing material (MeshBasicMaterial color) placed on building sides, and bloom will pick them up. Also add thin glowing lines. Keep it simple: ~60 small glowing quads and strips.

- Flying cars: small elongated boxes with glowing material, moving along a CatmullRomCurve3 path, with a few of them. Add a light trail? Keep to glowing boxes + small point lights maybe (too many point lights is bad). Just a glowing mesh, maybe two: a body + a rear light trail (thin elongated glowing box).

- Bloom: EffectComposer, RenderPass, UnrealBloomPass, OutputPass.

- Camera path: a CatmullRomCurve3 loop weaving through the city, camera.position = curve.getPointAt(t), lookAt a point slightly ahead + a slight vertical bob. Use the clock's timestamp (performance timestamp from the rAF parameter).

- Fog: FogExp2 with density ~0.015, color a dark purple #0a0616. "Volumetric-looking" — add a few large additive-blended soft fog planes? I could also add a few large transparent gradient planes drifting to fake god-rays/haze. Keep simple: fog + a few big soft sprites (canvas radial gradient texture) drifting at low opacity, additive blending, to fake volumetric haze.

- Resize handler.

City grid: place buildings on a grid with random jitter, leaving gaps for roads (streets). E.g., a 20x20 grid with spacing 30, skip some cells, random building heights 20–160. About 300 buildings.

Ground: a large 2000x2000 plane, MeshStandardMaterial, color #050510, metalness 0.95, roughness 0.12, envMapIntensity 1.2.

Environment texture: create a 64x32 canvas, dark with a pink/cyan/purple gradient, set texture.mapping = EquirectangularReflectionMapping, scene.environment = that. Maybe use PMREM; in r186, just setting an equirect env on scene.environment should work (Three handles the PMREM? actually you need to set .colorSpace; WebGLRenderer converts equirect env automatically — yes, modern three handles equirect env automatically).

Building shader material:

vertex: pass uv, world position, instanceMatrix; add an aSeed attribute (float per instance), maybe aHeight too.

fragment:
```
float hash(vec2 p){...}
// window grid
vec2 grid = vec2(12.0, 28.0);
vec2 f = fract(vUv * grid);
float w = step(0.3,f.x)*step(0.3,f.y) ... 
```
Use the box geometry's uv: box UV per face is 0..1; a window pattern per face is fine.

window id = floor(uv*grid), hash with seed -> if hash < density then lit. Color chosen from palette: hash picks pink (1.0,0.1,0.7), cyan (0.1,0.9,1), purple (0.6,0.2,1), or dim white-blue.

Body: dark base color, slight vertical gradient, plus fog.

Include fog in shader: either include fog chunks with #include <fog...>, or manually: mix with fog color by exp(-d*density^2). Easier: write manual fog in the shader (FogExp2 formula: 1-exp(-density^2 * d^2)? THREE FogExp2 factor = 1-exp(-density^2 * depth^2)... actual three: exp2: 1 - exp(-density*density*depth*depth)? THREE's FogExp2Shader: fogFactor = 1 - exp( - fogDensity * fogDensity * vFogDepth * vFogDepth ). Yes, squared.

Write custom shader with a fogDensity uniform, compute fogDepth = -mvPosition.z.

Neon signs: a set of planes with MeshBasicMaterial (toneMapped true) with high-intensity color, plus maybe a canvas texture with a simple glyph (vertical bars). Easiest: create a canvas texture with a random "kanji-like" glyph: draw a few strokes/rectangles in the color, glow via bloom. Make a small 64x64 canvas with strokes, use as an emissive-like basic material with additive blending? MeshBasicMaterial with the map, toneMapped false might blow out; OK.

Make a function to make a sign texture: dark background, random colored strokes (vertical bars, horizontal bars, circles). ~50 signs placed on random building faces near tops, random orientation.

Also add neon edge lines at some building tops: a thin box (LineSegments?) — add a glowing box frame at the top of some buildings (thin box, glowing basic material).

Cars: 8 cars, each a path: a random horizontal ring / random CatmullRom loop at a random height (40–140), random offset, speed. Car mesh: a small box body (dark), plus 2 glowing small boxes (headlights) — or one glowing box as a trail: thin elongated box with gradient? Keep to: an emissive cyan/pink box (trail) of length 4, plus a white small box for the body.

Update: t = (time*speed + offset) mod 1; pos = curve.getPointAt(t); tangent → lookAt pos+tangent.

Camera: closed CatmullRom curve with random-ish but fixed points, at heights ~30–80, weaving between buildings. t = time*0.005 mod 1 (period ~200 s). lookAt = curve.getPointAt((t+0.03)%1), plus a slight sin bob.

Use rAF timestamp: animate(timestamp), time = timestamp * 0.001.

Renderer: setPixelRatio, toneMapping ACESFilmic, exposure ~1.1, outputColorSpace default.

Composer: RenderPass, UnrealBloomPass(resolution, strength 1.2, radius 0.6, threshold 0.55), OutputPass.

Resize: camera aspect, renderer.setSize, composer.setSize, bloom resolution.

Building shader details:

```
uniform float uTime;
attribute float aSeed;
varying vec2 vUv; varying vec3 vWorldPos; varying float vSeed;
```
Wait, in a ShaderMaterial with an InstancedMesh, the instanceMatrix is available with `#ifdef USE_INSTANCING`? In a ShaderMaterial, you need to declare and multiply manually: `#include <common>` and then in the vertex: `vec4 wp = modelMatrix * instanceMatrix * vec4(position,1.0);` — the instanceMatrix attribute is auto-declared in WebGLProgram for a ShaderMaterial? Actually Three.js injects the `attribute mat4 instanceMatrix;` declaration only in built-in shaders via the instancing chunk. In a ShaderMaterial, you have to declare it yourself: `#ifdef USE_INSTANCING attribute mat4 instanceMatrix; #endif` — the USE_INSTANCING define is automatically set by the renderer for an InstancedMesh with a ShaderMaterial. Yes, the renderer sets the USE_INSTANCING program define. So declare in the shader code:

```
#ifdef USE_INSTANCING
attribute mat4 instanceMatrix;
#endif
```
Then use the guarded instMat.

Windows: use uv. Box UVs: each face 0..1. grid = vec2(8.0, 24.0)? Buildings are thin so uv x maps to width. window aspect: use a vec2(10., 30.) grid.

```
vec2 id = floor(vUv * grid);
float h = hash(id + vSeed*137.0);
float lit = step(0.55, h); // 45% lit
vec3 wc = palette(h2);
// slight flicker
float fl = 0.85 + 0.15*sin(uTime*3.0 + h*100.0);
vec3 col = body + lit * wc * fl;
```

Also darken the top/bottom edges: multiply window intensity by a smoothstep on uv.y near edges.

Maybe add a vertical neon strip to some buildings: if fract(vSeed) < 0.25, an edge line at a random x position, color from palette, intensity — good neon accents.

hash function:

```
float hash(vec2 p){ p = fract(p*vec2(123.34,456.21)); p += dot(p,p+45.32); return fract(p.x*p.y); }
```

Palette:
pink = vec3(1.0,0.15,0.75)
cyan = vec3(0.1,0.85,1.0)
purple = vec3(0.65,0.25,1.0)
warm = vec3(1.0,0.6,0.25)? Keep the spec: pink/cyan/purple only + a dim bluish white.

Manual fog in shader:
uniform vec3 uFogColor; uniform float uFogDensity;
float fdepth = length(vWorldPos - cameraPosition); (cameraPosition is built-in in ShaderMaterial, yes, it's a standard uniform)
float fogF = 1.0 - exp(-uFogDensity*uFogDensity*fdepth*fdepth);
col = mix(col, uFogColor, fogF);

Fog color: 0x0b0716, density 0.0075.

Also add a big soft haze sprite: a canvas radial gradient (white → transparent), SpriteMaterial, additive, opacity 0.06, scale ~400, place 8 sprites at random positions, drift slowly with time.

Ground reflection: with the env map, the street will reflect the env gradient — acceptable as "wet reflective." Also add a subtle grid of glowing road lines? Maybe a glowing road line texture via a canvas texture on the ground? I could add a second plane with a grid line texture (canvas) at a slightly higher position, with a faint additive basic material — neon road markings. Optional; maybe skip to keep the size down. Let me add a simple canvas grid texture on the ground with a dark base + faint cyan lane lines, used as the map on the standard material — this also gets reflected. Good: 256px canvas, dark base, faint lines, repeated 40x40.

Car paths: for each car, a random closed CatmullRom with ~8 random points inside the city area (radius ~500), height fixed with small variation per point.

Camera path: points around the ring at radius 150–450, y 25–90, closed.

Renderer background: scene.background = fog color.

Now let me write the file.

Canvas textures:

makeEnvTexture(): 256x128 canvas, gradient: bottom dark, near horizon a purple/pink band, top very dark; also a few bright small rectangles (city glow).

signTexture(): 96x128: black, pick a color, draw 3–6 random strokes: vertical bars, horizontal, circles, arcs → neon.

make ground texture: 256 canvas #05060c, cyan lines (strokeStyle rgba(0,180,255,0.35)) horizontal and vertical, plus a few pink lines.

Count: buildings on a 16x16 grid, spacing 46, skip ~18% and central road? The camera path radius is within 500, city is ~16*46=736 wide, half ~368. OK.

Building geometry: unit box (1,1,1) translated so the base is at 0: new THREE.BoxGeometry(1,1,1).translate(0,0.5,0). Per-instance scale: sx, sz 8–22, sy height 20–170. instanceMatrix scale.

Positions: gx, gz in -8..8, pos = (gx+0.5 jitter)*spacing, skip if |gx|<1 or |gz|<1? Roads: to make roads, skip cells where gx mod 4==0 or gz mod 4==0? Actually spacing 46, buildings ~20 wide, gap already ~26 — streets exist everywhere. OK.

Set aSeed = random*100.

Height: taller near center: h = base * (1 + 0.8*exp(-r2)).

Signs: for 40 random buildings, place a plane at a random face, y at 60–90% of the height, offset just above the building surface, random rotation (aligned to the face).

Add a top glow ring to ~30 buildings: a thin box at the top (sx+0.5, 0.8, sz+0.5)? Or a glowing edge: a 0.6-thick box at the top, color from palette, basic material.

Cars: 10.

Total meshes fine.

Bloom threshold 0.4, strength 1.4, radius 0.7.

Renderer: antialias true.

Now, write the code carefully.

Camera: fov 60, near 0.1, far 2000.

animate(ts):
```
function animate(time){
  requestAnimationFrame(animate);
  const t = time * 0.001;
  // camera
  const ct = (time * 0.00002) % 1;  // period 50s
  camPos = camCurve.getPointAt(ct, _v1);
  look = camCurve.getPointAt((ct+0.035)%1, _v2);
  look.y += Math.sin(t*0.5)*2.0;
  _v1.y += Math.sin(t*0.37)*1.5;
  camera.position.copy(_v1);
  camera.lookAt(_v2);
  // cars
  for each car: u=(t*speed+off)%1; car.group.position = path.getPointAt(u); tangent=path.getTangentAt(u); group.lookAt(pos+tangent)
  // haze sprites drift
  ...
  composer.render();
}
```
getPointAt with a target parameter is supported.

Cars: group with body (box 2.4,0.5,0.9, dark basic) and a light box at the rear: box(3.0,0.25,0.4) glowing color, offset z=-2, plus a front white point. Car faces the +Z direction? lookAt orients -Z toward the target by default (camera convention: object's +Z points toward the target? THREE lookAt points the object's +Z axis at the target? Object3D.lookAt: rotates so its positive Z axis points toward the target, but the camera uses -Z. Actually THREE's Object3D.lookAt makes the object's +Z point at the target (except for cameras which use -Z). So a trail at -Z is behind. Good: trail is a box centered at z=-2.5, length 4 → occupies -4.5..-0.5, behind the body.

Also a small point light per car? 10 point lights is heavy, but OK? A standard material for the ground; 10 dynamic lights is somewhat heavy but fine on a desktop. Skip the lights for performance — the glowing box + bloom is enough.

Write a hash inside the shader; no need for a seed in the fragment.

Building fragment:

```
varying vec2 vUv; varying vec3 vWorldPos; varying float vSeed;
uniform float uTime; uniform vec3 uFogColor; uniform float uFogDensity;

float hash(vec2 p){ p=fract(p*vec2(123.34,345.45)); p+=dot(p,p+3.5); return fract(p.x*p.y); }
vec3 palette(float h){
  if(h<0.34) return vec3(1.0,0.12,0.72);
  if(h<0.67) return vec3(0.12,0.85,1.0);
  return vec3(0.62,0.22,1.0);
}
void main(){
  float r = vSeed - floor(vSeed);
  vec3 body = vec3(0.012,0.014,0.03) + 0.015*r;
  vec2 grid = vec2(9.0, 26.0);
  vec2 f = vUv*grid;
  vec2 cell = floor(f);
  vec2 fr = fract(f);
  float h = hash(cell + vSeed);
  float win = step(0.45,h) * step(0.25,fr.x)*step(0.75,fr.x)? 
```
Window shape: lit if fr.x is between 0.2..0.8 and fr.y is between 0.2..0.8:
```
float inW = step(0.2,fr.x)*step(fr.x,0.8)*step(0.18,fr.y)*step(fr.y,0.82);
float lit = step(0.5,h)*inW;
```
Edge fade: fade = smoothstep(0.0,0.06,vUv.y)*smoothstep(1.0,0.94,vUv.y);
Color selection: hc = hash(cell*1.7+vSeed); c = palette(hc); occasional dim window: mix c with a dim bluish color.

Vertical accent strip:
```
if(r<0.3){ float sx = fract(vSeed*7.13); float line = smoothstep(0.985,0.995,abs(fract(vUv.x*3.0)-sx)); ... }
```
Hmm, simpler: stripX = 0.2+0.6*fract(vSeed*3.7); d = abs(vUv.x - stripX); strip = (1.0-smoothstep(0.0,0.01,d)) * step(r,0.3); color palette(r) * strip * 1.5. But on the box, uvs differ per face; OK — will show on some faces, OK.

flicker: fl = 0.8+0.2*sin(uTime*2.0+vSeed*40.0+h*30.);

col = body + lit*c*fl*1.6 + strip*sc*1.8;

fog: depth = length(vWorldPos - cameraPosition); ff = 1.0-exp(-uFogDensity*uFogDensity*depth*depth); gl_FragColor = vec4(mix(col,uFogColor,ff),1.0);

Also tone mapping: ShaderMaterial has no tone mapping applied (unless toneMapped and the shader includes it). The material's color will be output raw; the composer's output pass applies tone mapping? In the post pipeline, is the renderer's tone mapping applied at the material shader level? In r155+, is tone mapping done in the OutputPass? Actually: the renderer has a tone mapping setting; when using EffectComposer, the RenderPass renders to a linear buffer; tone mapping is... in recent three, tone mapping is applied by the OutputPass (which has the toneMapping uniform). Yes, r152+: the OutputPass performs tone mapping and color space conversion using the renderer.toneMapping setting, and intermediate passes are linear. Custom ShaderMaterial output is linear, so the OutputPass will tone map. Good — glow colors >1 will be HDR-ish.

Values: lit window ~1.6, above threshold 0.4 → bloom. OK.

Haze sprites: texture from a radial gradient canvas 256, white. SpriteMaterial({map, color:0x6a3fd0, transparent, opacity:0.05, blending:THREE.AdditiveBlending, depthWrite:false, fog:false? Does the sprite material have fog? SpriteMaterial has a fog boolean, default true; set fog:false to avoid double fog, or leave it.) Set fog:false.

Sprite scale (500, 200,1), ~10 sprites, at y 40–120, random positions, slow drift: pos.x = base + sin(t*0.02+i)*30.

Sign material: MeshBasicMaterial({map:tex, transparent:true, side:DoubleSide, toneMapped:false}) — with toneMapped false, the color may be too strong but bloom will handle it; canvas has a black background, so it's fine, additive blending? Use transparent + normal blending, black background will darken behind? With a normal transparent, the black background will occlude the building behind → a dark quad on top of the building. Better to make the background transparent: draw on a transparent canvas (clearRect) → OK with normal blending. Yes, a transparent canvas background.

Add a small "pole" too? Skip.

Env texture for the ground: equirect canvas.

renderer.toneMapping = THREE.ACESFilmicToneMapping; toneMappingExposure=1.15.

Composer:
```
composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene,camera));
bloom = new UnrealBloomPass(new THREE.Vector2(w,h), 1.3, 0.7, 0.35);
composer.addPass(bloom);
composer.addPass(new OutputPass());
```

Imports:
```
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
```

Canvas texture color space: set tex.colorSpace = THREE.SRGBColorSpace for color maps.

Now the camera curve: points:
```
const cp=[]; for(let i=0;i<10;i++){ const a=i/10*Math.PI*2; const rad=180+Math.sin(i*2.7)*120; cp.push(new THREE.Vector3(Math.cos(a)*rad, 30+((i*53)%40), Math.sin(a)*rad)); }
camCurve = new THREE.CatmullRomCurve3(cp,true);
```
City half-width ~370, so rad 60–300 to weave.

Make sure the camera doesn't clip into buildings — with fog and density, clipping is not too noticeable; keep rad ≥ 80 and heights 25–90; some clipping is acceptable but should be minimized.

Ground: 3000 size, y=0.

Also add distant skyline: big dark boxes at radius 600–900? Maybe skip.

Car count 10, path: each i, base h = 40+ i*9 %..., points 8 around center with random offset: a + random, rad random 100–420, h + jitter.

Let me now write the final HTML.

One concern: `cameraPosition` uniform is available in ShaderMaterial — yes, three provides standard uniforms (cameraPosition, projectionMatrix, etc.) to ShaderMaterial.

InstanceMatrix: in a RawShaderMaterial you declare; in a ShaderMaterial, are common attributes declared? A ShaderMaterial prepends a standard prologue that includes attribute position, normal, uv and a define for instancing? The built-in shader uses `#include <begin_vertex>` etc. For a ShaderMaterial, three prepends declarations: `attribute vec3 position; attribute vec3 normal; attribute vec2 uv;` and the defines. I recall the instanceMatrix attribute is not declared in the ShaderMaterial prologue; the safe thing is to add:

```
#ifdef USE_INSTANCING
  attribute mat4 instanceMatrix;
#endif
```
But if three also declares it, redeclaration would be a syntax error? The ShaderMaterial vertex prefix (from WebGLProgram's prefixVertex): contains `#ifdef USE_INSTANCING attribute mat4 instanceMatrix; #endif` — actually in modern three, does the prefix for non-raw materials include the instancing attribute? Let me recall: the prefixVertex string has:

```
#ifdef USE_INSTANCING
	attribute mat4 instanceMatrix;
#endif
#ifdef USE_INSTANCING_COLOR
	attribute vec3 instanceColor;
#endif
```
Yes, this is part of the standard prefix for non-raw materials (added around r118). So don't redeclare. So in the shader, just:

```
vec4 wp = vec4(position,1.0);
#ifdef USE_INSTANCING
wp = instanceMatrix * wp;
#endif
gl_Position = projectionMatrix * modelViewMatrix * wp;
```
Hmm, modelViewMatrix already includes the model matrix, but for an InstancedMesh, instanceMatrix is separate; so world = modelMatrix * instanceMatrix * position. Use:
```
vec4 wp;
#ifdef USE_INSTANCING
wp = modelMatrix * instanceMatrix * vec4(position,1.0);
#else
wp = modelMatrix * vec4(position,1.0);
#endif
gl_Position = projectionMatrix * viewMatrix * wp;
vWorldPos = wp.xyz;
```
Good.

Resize: also composer.setPixelRatio? EffectComposer has setPixelRatio; set composer.setPixelRatio(renderer.getPixelRatio()) once and setSize on resize.

Let me write the code.
