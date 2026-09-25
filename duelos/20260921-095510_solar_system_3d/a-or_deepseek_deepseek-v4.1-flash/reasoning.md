Let me design a self-contained HTML file using three.js r186 with import map (provided by the environment, I just use bare imports).

Key features:
- Full window canvas, resize handling.
- Sun: emissive sphere with halo (sprite with canvas-generated radial gradient texture, additive blending). PointLight at center.
- 8 planets with procedural canvas textures.
- Saturn rings (RingGeometry with canvas texture, transparent).
- Moon orbiting Earth.
- Faint orbit lines (line loops with low opacity).
- Different orbital speeds.
- Starfield background (Points with random positions).
- Cinematic camera tour: keyframes for each planet, smooth interpolation between them, name on screen (HTML overlay with fade).
- Uses requestAnimationFrame timestamp for time.
- Everything important within first 30 seconds: 8 planets + sun... that's 9 targets in 30s → ~3.3s each. Let's include Sun at start (~2.5s) then 8 planets. Let's plan: total tour ~28s: Sun 3s, Mercury 2.8, Venus 2.8, Earth 3.2, Mars 2.8, Jupiter 3, Saturn 3.2, Uranus 2.8, Neptune 3 → sums to 26.6s. Good.

Camera approach: for each target, define a camera position relative to planet (offset), and the camera looks at planet. To make it cinematic, use damped/lerped camera movement. Simplest robust: compute desired camera position for current segment and lerp with smoothstep easing over transition, then hold. Actually a cleaner approach: define tour keyframes with time stamps; for time t, find segment between keys i and i+1, smoothstep interpolate camera position and lookAt target position. But planets move, so camera target should follow planet position. Let's do: each keyframe has a "follow" object (planet mesh) and offset vector (in world space, but maybe rotating). Camera position = planet.worldPosition + offset (offset maybe slowly rotating for cinematic feel). During transition from key A to key B, lerp between (A.planet.pos + A.offset) and (B.planet.pos + B.offset) with easing; lookAt target = lerp(A.planet.pos, B.planet.pos). That is smooth.

But scale: planets need to be visible. Real relative sizes would make Mercury tiny and Jupiter huge. "Relative sizes that make sense" — use a compressed scale: radius = k * (realRadius)^0.5 or use log. Let's do: size = Math.pow(realRadiusKm/6371, 0.5) * someBase. Earth = 1 → Mercury sqrt(0.383)=0.62, Jupiter sqrt(11.2)=3.35, Saturn sqrt(9.45)=3.07, Uranus sqrt(4.0)=2.0, Neptune sqrt(3.88)=1.97, Venus sqrt(0.949)=0.97, Mars sqrt(0.532)=0.73. That's decent: Jupiter largest, Mercury smallest. Good.

Then multiply by 1.0 and distances also compressed. Let's set Earth radius = 1.2 units maybe. Distances: use something like base spacing with sqrt of AU too. AU distances: 0.39, 0.72, 1, 1.52, 5.2, 9.54, 19.2, 30.1. Compress with pow(AU, 0.6)*? Let's just handcraft: Mercury 12, Venus 17, Earth 23, Mars 30, Jupiter 46, Saturn 62, Uranus 78, Neptune 92. Camera offsets scaled accordingly.

Sun radius maybe 4 (largest but not to scale — fine; sun should be big). Planets orbit around it.

Camera tour offsets: each planet needs an offset magnitude ~ planetRadius*4 plus something. For small planets like Mercury (radius 0.62*1.2=0.74), offset ~3.5 might be too close? Fine—cinematic close-up. But also the planet needs to be visible against the sun's glare. Let's use offset = max(3, radius*5).

Actually careful: If camera is too close to a small planet, planet fills small fraction but the background is fine. Let's set offset distances between 4 and 9 units.

Hmm, given planet distances up to 92 units and starfield, camera near/far: near 0.1, far 5000. Starfield sphere radius ~1500.

Textures: procedural canvas textures for each planet. Let's write functions:

- makeSunTexture: radial gradient with noise? Sun is emissive with halo sprite; texture can be noisy orange.
- Earth: canvas 1024x512: blue ocean base with gradient, draw continents as random blobs (green/brown), polar ice caps white, plus clouds maybe separate? Keep simple: continents via noise blobs.
- Jupiter: horizontal bands with varying colors + a great red spot ellipse + turbulence.
- Saturn: pale bands tan.
- Mars: red with darker patches and polar caps.
- Mercury: gray with craters (circles).
- Venus: yellowish swirls.
- Uranus: cyan with faint bands.
- Neptune: deep blue with bands and a dark spot.
- Moon: gray with craters.

Use a seeded random for determinism? Not required but nice. I'll use a simple mulberry32.

Texture creation: create canvas, get context, draw, then new THREE.CanvasTexture(canvas). Set colorSpace = THREE.SRGBColorSpace.

Note: for r186, THREE.SRGBColorSpace exists. Renderer outputColorSpace default is SRGB in recent versions. Fine.

Lighting: PointLight at sun with high intensity and decay 0 (or use decay 2 with huge intensity). With physically correct lights default in newer three (useLegacyLights removed in r165+?). In r186, lights use physical units: PointLight intensity in candela, with decay 2 default. For a point light at distance ~20-90 units, intensity needs to be large. Let's set decay = 0 to avoid falloff issues? Actually decay=0 gives constant intensity — simplest: light = new THREE.PointLight(0xffffff, 3, 0, 0) → intensity 3, distance 0 (infinite), decay 0. Hmm with decay 0 the intensity is as given. Let's test mentally: MeshStandardMaterial lit by point light intensity 3 with decay 0 at distance... The irradiance = intensity * ... For decay=0, intensity/distance^2 * distance^2? Actually three's point light: getDistanceAttenuation with decay=0 → 1.0. So irradiance = color*intensity → basically like a directional light of intensity 3? That would be bright. Let's use intensity ~2.5.

Also add a small ambient light (0x202040, 0.15) so the dark sides aren't pitch black. And maybe a hemisphere light.

Sun mesh: MeshBasicMaterial with emissive-like color (MeshBasicMaterial is unlit, appears self-lit). Use the sun texture with basic material and color white. Plus a sprite halo with additive blending, and maybe a couple of glow sprites of different sizes.

Halo: create canvas radial gradient: white/yellow center fading to transparent. Sprite scale ~ sun radius * 6.

Saturn rings: RingGeometry(inner, outer, 128) rotated -PI/2 on X. Need UV mapping for the ring texture: by default RingGeometry UVs map to a square-ish [0,1] space which makes radial texture look odd. Common fix: recompute UVs so that u = radial distance. Let's write custom: for each vertex, compute distance from center, set uv.x = (d - inner)/(outer-inner), uv.y = 0.5? Actually to sample a 1D-ish texture, set u = normalized radius, v = 0.5. Then create a canvas texture of width 512 (radial profile) and height 1 (or a few px). Better: use texture with bands drawn vertically? Let's create canvas 512x64 with vertical bands (x = radius). Then uv.x sample radius. Fine.

Set ring material: MeshBasicMaterial? Better MeshStandardMaterial with side: DoubleSide, transparent, alphaMap-ish. Use map with transparency via alpha channel: create canvas with gradients/bands and some transparent gaps. Set material.map = tex, transparent = true, side = DoubleSide, depthWrite false. Lighting: MeshStandardMaterial rings would be lit—but with only point light at center, ring normals point up, so the light from the center hits... point light at center, ring plane contains the light, so lighting would be nearly zero (light direction parallel to ring plane → N·L ≈ 0). Bad. Use MeshBasicMaterial for rings instead with slight tint. That's acceptable and looks fine.

Orbit lines: THREE.BufferGeometry circle points, LineBasicMaterial with opacity 0.15, transparent.

Orbit motion: use elapsed time from timestamp. angle = t * speed + phase. Planets orbit in the same plane with slight inclination maybe. Keep them near the ecliptic with tiny inclination for visual interest. Keep camera positioned slightly above the plane so orbits read as ellipses.

Planet self-rotation: rotate mesh on Y each frame (use delta or absolute: mesh.rotation.y = t * rotSpeed).

Moon: pivot object around Earth. Earth needs a group: earthGroup holds earth mesh and moonPivot. Actually to keep it simple: earthOrbit object positioned at Earth's orbital position each frame; the earth mesh inside rotates. Moon orbits earthOrbit? Moon should orbit Earth but not rotate with Earth's spin. So: earthGroup (position set from orbit) contains earthMesh (spins) and moonPivot (rotates) containing moonMesh at distance.

Label overlay: HTML div with planet name, big, fading in/out. Use font-family sans-serif, letterspacing, text-shadow. Use CSS transitions or set opacity in JS.

Tour timing: Let's define segments. Each keyframe: {name, target (function returning object3D position), offset (Vector3), duration}.

Plan:
- t 0.0–2.3: Sun (wide view). offset (0, 18, 52) looking at sun.
- Mercury 2.3–5.3
- Venus 5.3–8.3
- Earth 8.3–12.0 (includes Moon mention)
- Mars 12.0–15.0
- Jupiter 15.0–18.5
- Saturn 18.5–22.5
- Uranus 22.5–25.5
- Neptune 25.5–29.0
Then loop with a slow wide orbit? After 29s, do a final "tour complete" wide shot of the whole system, then loop back. Let's make the tour loop: after the last keyframe, transition back to Sun's wide shot over ~3s, then repeat. Total loop ~32s.

Implementation of camera: 

```
const tour = [
  {name:'The Sun', key:'sun', offset:new THREE.Vector3(0,22,58), dur:2.5},
  ...
];
```

Compute total time. Then given localTime = t % totalLoop. Find segment index and progress. Camera target position = lerp between segment i's desired camera position (target_i.position + offset_i) and segment i+1's desired camera position (target_{i+1}.position + offset_{i+1}), with smoothstep. Wait — careful: within a segment, we want the camera to hold on the planet for its whole duration, then quickly transition to the next in the beginning of the next segment? Simplest: each segment i has duration dur_i; during segment, camera = lerp(prevPos, curPos, ease(progress)) where the first part is a transition and then holds. E.g., ease over first 30% of the segment then hold. Let's do:

For segment i with target T_i and camera offset O_i:
- desiredPos_i = T_i.worldPos + O_i (offset rotates slowly around Y for cinematic drift: rotate offset by t*0.15 rad? That would make camera move while holding—nice.)
- During segment i, at progress p in [0,1]:
  - blend = smoothstep(0, 0.35, p) → transitions from previous key's desired pos to current.
  - camPos = lerp(desiredPos_{i-1}, desiredPos_i, blend)
  - lookAt target = lerp(T_{i-1}.worldPos, T_i.worldPos, blend)

Where desiredPos_{i-1} is computed with current time too (so planets' motion is accounted). This works well and gives smooth motion. Offsets rotate with time for drift.

Name label: show name of segment i, fading in during blend and fade out near the end? Simpler: opacity = 1 for most of segment, fading in during first 0.35 and out during last 0.15... but for the last frame it would fade and the next name fades in. Let's compute label opacity: fadeIn = smoothstep(0,0.2,p), fadeOut = 1 - smoothstep(0.85,1.0,p), opacity = min of them, times something. Actually for the Sun segment at start of loop, label may pop. Fine.

Alternatively keep label opacity based on camera distance blend. Keep simple with the fade scheme.

Camera offsets: For each planet, choose offset so the planet is nicely visible. Planet radius r; offset magnitude ~ max(3.2, r*4.5). Let's compute actual radius scale.

Let radiusScale: Earth base radius 1.3 units.
- Mercury: 0.62*1.3 = 0.81
- Venus: 0.97*1.3=1.26
- Earth: 1.3
- Mars: 0.73*1.3=0.95
- Jupiter: 3.35*1.3=4.35
- Saturn: 3.07*1.3=4.0 (rings to ~2.3x radius → 9.2)
- Uranus: 2.0*1.3=2.6
- Neptune: 1.97*1.3=2.56

Camera offsets:
- Sun: (0, 25, 62) — sun radius 5 → looks like a big glowing ball. Actually sun radius let's use 6 with halo. Then camera at distance ~66, sun angular size ok.
- Mercury: offset len ~ 3.0 → (2.5, 1.6, 2.5) ~ 3.9. Hmm, with a FOV of 45 and distance 3.9 for planet radius 0.81 → angular radius = atan(0.81/3.9)=11.7°, half of FOV=22.5 → planet occupies ~52% of half-height. Good.
- Jupiter r=4.35, offset ~4.35*4.5=19.6 → angular radius atan(4.35/19.6)=12.5°. Good.
- Saturn r=4.0 with rings 9.2: offset ~ 28? angular: ring 9.2/28 = 18° — slightly big but rings tilted so fine. Use offset magnitude 26.
- Uranus r=2.6: offset 12.
- Neptune r=2.56: offset 11.5.

Distances between orbits: Mercury at 12 with camera near it — the sun at 12 units away with radius 6 would be huge in the background! That's a problem: sun radius 6 with Mercury orbit radius 12 means Mercury is basically inside the sun's soup. Let's reduce sun radius to 4.5 and push orbits out: Mercury 16, Venus 22, Earth 29, Mars 37, Jupiter 58, Saturn 78, Uranus 96, Neptune 112.

Hmm, camera near Mercury at ~4 units with the sun 16 away, radius 4.5 → angular size ~15.7°, fine.

Sun radius 4.5, halo sprite scale 4.5*7 = 31. OK.

Camera far plane 4000, starfield radius 1200 (inside far).

Let's check visibility: with camera at Neptune (112 units out) the Sun is a small dot. Fine.

Now the Sun's light: PointLight intensity with decay 0. Let's set intensity 2.2 and see. Planets use MeshStandardMaterial with roughness 0.9. Plus ambient 0.12.

Let me now think about texture generation functions carefully.

Seeded RNG:
```
function mulberry32(a){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;}}
```

Write a helper to create canvas:
```
function makeCanvas(w,h){const c=document.createElement('canvas');c.width=w;c.height=h;return {c,ctx:c.getContext('2d')};}
```

Value noise function for smooth blobs: I'll do simple approach — draw many random radial-gradient blobs. That gives decent procedural look.

Earth texture (1024x512):
- Fill ocean: vertical gradient from #0a2a6b (poles) to #1565c0 (equator)? Actually ocean deep blue: '#0b3d91' base, with lighter equatorial.
- Continents: use several "landmass seeds" and draw overlapping blobs with fbm noise? Simpler: draw ~40 random ellipses of varying size in green/brown, then add lighter green highlights. To avoid uniform, use clusters: pick 8 cluster centers, each with 10-20 blobs around it.
- Ice caps: white gradient rectangles at top and bottom (with blurred edges).
- Add slight noise speckle for texture.

Jupiter (1024x512):
- Bands: loop y from 0..512, color varies via sine/noise of y: mix between tan (#d8c39a), brown (#b07b4a), cream (#f0e2c8), with turbulence: for each y, color; draw horizontal line with slight wobble: use per-x noise offset. Simpler: fill horizontal stripes with linear gradients between band colors, then overlay wavy ellipses to break up, then draw Great Red Spot.
- Use small vertical variation: for each pixel row, compute color; but also add sine wiggle by drawing sine-wave paths.

I'll do: for each y, compute t=y/512 and use a sum of sines to pick band color index from a palette; draw rect of height 1 with color. Then draw wavy horizontal strokes with alpha to simulate turbulence. Then the red spot: radial gradient ellipse '#c0392b'.

Saturn: similar bands but pale gold/tan with lower contrast.

Uranus: pale cyan with subtle bands.
Neptune: deep blue with bands and a dark storm spot and white streaks.

Mars: rust base '#c1440e', darker patches, polar caps white, craters.

Mercury: gray base '#8a8a8a' with craters: circles with darker fill and light rim.

Venus: '#e8cda2' base with swirls (bezier curves) in lighter/darker cream.

Moon: gray with craters dark maria patches.

Sun texture: radial-ish noise orange/yellow — used on the sun mesh (basic material) plus we add glow sprites. For sun surface, draw noise of granules: base '#ffb400', blobs '#fff3b0' and '#ff6a00'.

Halo texture: radial gradient white→transparent. Used with two sprites at different scales for a nice bloom-ish effect.

Starfield: 3000 points in a sphere shell radius 800-1400, small size, colors slightly varied, PointsMaterial with sizeAttenuation false? Use sizeAttenuation true with size 2 and a circular sprite texture... simplest: PointsMaterial with size 1.5, sizeAttenuation: false → all stars same pixel size, looks clean. Add a few brighter ones. Use vertexColors for variety.

Actually with sizeAttenuation false, size is in pixels — good. Set size 1.6, color white, and add some variation via vertexColors. transparent with alphaMap? Not necessary. Let's use a circular point texture with alphaTest to avoid square stars? At 1.6 px it doesn't matter much. I'll create a small radial gradient texture and use map + transparent + depthWrite false for round stars. Slight perf cost fine.

Overlay HTML: 
- Title name div centered-bottom-ish, large letters with letter-spacing, and a subtitle showing index? Let's show name and a small caption (e.g., "Mercury — 0.39 AU"). Nice touch.
- Maybe a top-left title "THE SOLAR SYSTEM" persistent small.
- Fade with CSS opacity transition driven by JS each frame.

Also add vignette overlay via CSS radial-gradient for cinematic feel.

Now, timing must ensure "everything important within the first 30 seconds". Loop total ~30s. Let's plan the timeline carefully with label names.

Timeline (seconds):
0.0 – 2.4: Sun (wide establishing)
2.4 – 5.2: Mercury
5.2 – 8.0: Venus
8.0 – 11.4: Earth (+ Moon)
11.4 – 14.2: Mars
14.2 – 17.6: Jupiter
17.6 – 21.4: Saturn (rings)
21.4 – 24.2: Uranus
24.2 – 27.3: Neptune
27.3 – 30.0: Solar system wide (overview showing all orbits)
Then loop back to Sun at 30.0 (32.4?). Hmm, make total exactly 30.0 for cleanliness: Overview 27.3–30.0 with transition to Sun wide at the start of the next loop. Actually the segment structure: each segment has target and offset; the overview segment targets the sun with a wide offset (0, 90, 190)? Then Sun's own segment offset (0,25,62) — those are two different sun segments. Let's make segment 0 = "The Solar System" overview wide and segment 9 = also overview? Hmm.

Better structure: keys array:
0: overview (target sun, offset (0,120,240) looking at origin) — but wait, with planets up to 112 units radius, a wide view needs distance ~300 to see Neptune's orbit. Camera at (0,150,300): fine with far=4000.

Actually the requirement: "camera that travels from planet to planet showing each one close up with its name on screen" and everything important in first 30s. A wide overview shot at the end is nice.

Let's do:
idx 0: "The Solar System" — sun target, offset (0, 150, 320), dur 2.6
idx 1: "Mercury" dur 2.8
idx 2: "Venus" dur 2.8
idx 3: "Earth" dur 3.6 (and label "Earth & Moon")
idx 4: "Mars" dur 2.8
idx 5: "Jupiter" dur 3.4
idx 6: "Saturn" dur 3.6
idx 7: "Uranus" dur 2.8
idx 8: "Neptune" dur 3.0
Total = 27.4. Then loop back to idx 0 with its transition happening during the first 35% of segment 0 (i.e., ~0.9s transition) — that's a fast jump from Neptune to a wide view. Hmm, that's a big jump; but the transition blend length can be proportional. Let's give a bit more: make the blend duration proportional to segment duration but at least allow longer for big jumps. Simpler: transition fraction 0.4 of the segment, so transitions take 0.4*dur. From Neptune to overview: 0.4*2.6 = 1.0s. That's a fast pan across the solar system. It's fine, cinematic even (a quick zoom out). Maybe use fraction 0.45.

Alternatively order the loop so it ends with Neptune then jumps back to wide overview. Acceptable.

Hmm but note the label fade: during the transition the previous label fades out and new one fades in. Good.

One more consideration: the camera's lookAt target during transition lerps between planet positions, so it sweeps. Fine.

Also the "name on screen" needs to be visible. I'll display name + a descriptive caption.

Now the offsets also should account for the planet's own size: I'll define offsets per planet, normalized then scaled.

Let me define for each planet in the data array:
```
{name:'Mercury', radius, orbitRadius, orbitSpeed, spinSpeed, color, tex: makeMercuryTexture, camDist: 4.0, camHeight: 1.5}
```
Then offset vector = new THREE.Vector3(camDist*0.8, camHeight, camDist*0.75).normalize() ... hmm. Just define offset as a Vector3 built from a distance and direction, then rotate around Y with time for drift.

Compute camPos = planetPos + offsetRotated where offsetRotated = offset.clone().applyAxisAngle(Y, t*0.06 + phase). That gives slow orbit drift around the planet. Nice cinematic. But careful: if the planet is near the Sun, the drift may bring the sun into view. For Mercury, the sun is behind at distance 16; camera drifts around Mercury at radius ~4, so the sun might pass through the frame. That's actually beautiful (sunlit Mercury with the sun behind). Keep it but maybe reduce drift speed.

Actually wait: with the sun that close, Mercury will be lit only on one side and the sun glare may wash out. Let's set Mercury's orbit radius a bit larger: 18. And sun radius 4.5. Fine.

Also for the sun's own segment, we use the same formula: target = sun mesh position (origin). offset (0,150,320) rotating around Y slowly? That'd swing the camera wildly. For the sun segments, use a fixed offset without rotation. I'll add a flag: rotate offset: true/false, or just set rotationRate 0 for the sun.

Simplify: each key has `spin` value for how fast to rotate the offset around Y.

Let me now write the code.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Solar System — Cinematic Tour</title>
<style>
  html,body{margin:0;height:100%;background:#000;overflow:hidden;font-family:...}
  #app{position:fixed;inset:0}
  canvas{display:block}
  #labels{position:fixed;inset:0;pointer-events:none}
  #name{position:absolute;left:0;right:0;bottom:12%;text-align:center;...}
  ...
</style>
```

Font: use system sans-serif stack, no external fonts.

Name styling: font-size clamp(28px, 6vw, 72px), letter-spacing .35em, text-transform uppercase, color #fff, text-shadow glow.

Caption: smaller, letter-spacing .25em, color rgba(255,255,255,.65).

Also a persistent top-center small title "THE SOLAR SYSTEM" with low opacity? Might conflict. Add top-left "THE SOLAR SYSTEM · A CINEMATIC TOUR" small, opacity .35, fades away? Keep it always, small.

Vignette: fixed div with radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,.75) 100%), pointer-events none. Nice cinematic.

Also add a subtle film-grain? Not necessary.

Now the JS.

```js
import * as THREE from 'three';
```
No OrbitControls needed since automatic. Fine (addons not required).

Setup:
```js
const renderer = new THREE.WebGLRenderer({antialias:true, powerPreference:'high-performance'});
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.15;
document.getElementById('app').appendChild(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(50, innerWidth/innerHeight, 0.1, 6000);
```

Careful with ACES tone mapping: it will desaturate the bright sun and dim things. It gives a filmic look. With emissive sun (basic material) at color values up to 1, ACES will map white to ~0.8 gray-ish. Sun might look dull. Let's set sun material color to values >1? MeshBasicMaterial color can't exceed 1 per channel but we can set color and use toneMapped = false for the sun and halo so they stay bright. Yes: set material.toneMapped = false for the sun and glow sprites so they render at full brightness and pop. Good trick.

For planets, ACES tone mapping with exposure ~1.2 is fine.

Lights:
```js
const sunLight = new THREE.PointLight(0xfff2d0, 3.2, 0, 0); // decay 0
sunLight.position.set(0,0,0);
scene.add(sunLight);
const ambient = new THREE.AmbientLight(0x334466, 0.35);
scene.add(ambient);
```
Hmm with decay 0 and intensity 3.2, a Lambert surface facing the light gets color * intensity * NdotL... In three, PointLight irradiance = color * intensity * attenuation; for MeshStandardMaterial, diffuse = albedo/π * irradiance * NdotL? Physically, the outgoing radiance = albedo/π * E where E = intensity * NdotL (for a point light I = intensity in candela, E = I/d²). Hmm, three implementation: getPointLightInfo: light.color = pointLight.color * pointLight.intensity * attenuation? Let's recall: in WebGLRenderer, `pointLight.color.multiplyScalar(pointLight.intensity)` hmm. Actually:

```js
// lights_pars_begin / WebGLLights
pointLight.color.copy(light.color).multiplyScalar(light.intensity * scaleFactor)
```
where scaleFactor = 1 for physical? In recent three: `const scaleFactor = ( ! physicallyCorrectLights ) ? Math.PI : 1;` — that was removed. In r155+, `useLegacyLights` default false → physically correct. When useLegacyLights is true, point light intensity multiplied by... Let me just recall that in r155+, `WebGLLights` does:

```js
} else if ( light.isPointLight ) {
  const uniforms = cache.get( light );
  uniforms.color.copy( light.color ).multiplyScalar( light.intensity * scaleFactor );
```
Hmm I think scaleFactor was removed in r165. There's `getLightState`... I'm not 100% sure but roughly intensity is in candela and irradiance = intensity/d². With decay 0, the distance attenuation is 1 (since decay=0 means no falloff). Then diffuse irradiance = intensity * NdotL. And BRDF divides by π: outgoing = albedo * E / π ≈ albedo * intensity * NdotL / π. So with intensity 3.2, albedo 1 → 3.2/π ≈ 1.0 → full white. That's about right for a "lit" look. Hmm, but with ACES tone mapping, 1.0 maps to ~0.8. Fine. Let's use intensity ~3.5 and ambient 0.25.

Actually there's a subtlety: with tone mapping and exposure, planets should look reasonably bright. I'll go with pointLight intensity 4 and ambient 0.6 with color 0x223355? Ambient light adds irradiance directly (albedo * ambientColor * intensity) → with intensity 0.3 and dark blue color, the dark side gets a faint blue tint. Good.

Let me use:
- pointLight intensity 4.0, decay 0, distance 0, color 0xfff4e0.
- ambient: new THREE.AmbientLight(0x4466aa, 0.35).

Sun mesh radius 4.5, but its light source at center — inner planets lit from distance ~18-30.

Now build textures.

Let me write the texture functions.

```js
function rand(seed){ let a = seed >>> 0; return function(){ a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
```

Common helper: noise blobs.

```js
function blob(ctx, x, y, r, color, rnd, alpha=1){
  const g = ctx.createRadialGradient(x,y,0,x,y,r);
  g.addColorStop(0, color); g.addColorStop(1, 'rgba(0,0,0,0)');
  ...
}
```
Hmm, using transparent gradient with a color string requires rgba parsing. Instead use globalAlpha.

I'll write helper:
```js
function softBlob(ctx,x,y,r,color,alpha){
  const g=ctx.createRadialGradient(x,y,0,x,y,r);
  g.addColorStop(0,color);
  g.addColorStop(1,'transparent');  // 'transparent' works in canvas as rgba(0,0,0,0)
  ctx.globalAlpha=alpha;
  ctx.fillStyle=g;
  ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fill();
  ctx.globalAlpha=1;
}
```
Note: gradient from a solid color to 'transparent' — canvas interpolates in premultiplied space? Browsers interpolate gradient color stops in unpremultiplied RGBA, so from (r,g,b,1) to (0,0,0,0) causes darkening toward the edge (since RGB goes to black). That's a known issue. To avoid, use a transparent version of the same color: e.g., use color with alpha 0. I'll pass color as an array [r,g,b].

Simplify: write a helper that takes rgb array:
```js
function blob(ctx,x,y,r,[r,g,b],a){
  const grd=ctx.createRadialGradient(x,y,0,x,y,r);
  grd.addColorStop(0,`rgba(${r},${g},${b},${a})`);
  grd.addColorStop(1,`rgba(${r},${g},${b},0)`);
  ...
}
```
Good.

Also seamless wrapping: for textures mapped on spheres, the left and right edges must match. Blobs near x=0 or x=W should wrap. I'll draw each blob up to 3 times (x-W, x, x+W) to handle wrapping. Since blobs use radial gradients and appear near edges, drawing wrapped copies at x±W handles the seam. Also we can clamp: only draw copies if within some range. Simpler to always draw 3 copies (cost is fine).

Also horizontal bands textures don't have seams issues.

Let me now write each texture.

**Sun texture** (512x256): base fill '#ff9a1f'. Draw many small blobs of '#fff0a0' and '#ff5b00' with soft edges. Then a bit of granular noise.

**Mercury** (1024x512): base '#8c8c8c'; add large darker patches via blobs of [120,120,120] and lighter [190,190,190]; then craters: for i<220: random x,y,r(2..16): draw circle with slightly darker fill, then an arc highlight. Use ctx.arc with fill rgba dark, then a light crescent: draw arc offset. Simple crater: 
```
ctx.beginPath(); ctx.arc(x,y,r,0,TAU); ctx.fillStyle='rgba(60,60,60,.35)'; ctx.fill();
ctx.beginPath(); ctx.arc(x-r*0.2,y-r*0.2,r*0.85,0,TAU); ctx.strokeStyle='rgba(230,230,230,.25)'; ctx.lineWidth=r*0.18; ctx.stroke();
```
Good enough.

**Venus** (1024x512): base '#e6cf9b'; draw wavy horizontal swirls: many semi-transparent strokes with sine paths in '#f7e7bd' and '#c9a86a'. Plus soft blobs.

**Earth** (1024x512): 
- Ocean: linear gradient vertical? Let's base '#0b2e6b' to '#1565c0' mid to '#0b2e6b'. Actually a vertical gradient from darker at poles to slightly lighter at equator.
- Continents: use clusters of blobs with greens [50,110,60], [90,140,70], and desert [180,160,90], and add darker edges.
- Ice caps: white blobs at the top and bottom rows with gradient.
- Cloud swirls: white with low alpha (0.15) blobs.

**Mars** (1024x512): base '#c1502e' -> actually '#b5461f'. Dark patches '[110,50,30]' and lighter '[220,140,90]'. Polar caps: white at both poles (north smaller). Craters few.

**Jupiter** (1024x512): bands. Palette:
```
const bands=[[214,190,150],[186,150,110],[232,214,180],[160,120,90],[210,190,160],[150,110,80]];
```
Loop y: choose color by a smooth noise function of y. Let's do: for each y, compute v = sum of sines: f = 0.5+0.5*Math.sin(y*0.09)+... Better approach: build the texture by drawing horizontal stripes of height 2 with a color computed from a pseudo-noise of y:

```js
let seedY = 0;
for(let y=0;y<H;y+=2){
  const t = y/H;
  const n = Math.sin(t*Math.PI*14)*0.5 + Math.sin(t*Math.PI*33+1.3)*0.3 + Math.sin(t*Math.PI*7.1+0.7)*0.4;
  // pick color interpolating palette
  const idx = (n+1.2)/2.4 * (palette.length-1);
  ...
}
```
Then draw the stripe. Then add turbulence: overlay many elongated soft blobs with alpha 0.15 in light/dark colors, and wavy streaks using ctx.ellipse with rotation 0, width 60-160, height 6-14.

Great Red Spot: at (x=0.65W, y=0.62H), an ellipse radial gradient in '#b5432e' with a lighter rim.

Also Jupiter's poles darker.

**Saturn** (1024x512): similar but palette paler: [226,206,160],[200,178,130],[240,226,190],[190,165,120]. Lower contrast.

**Uranus** (1024x512): base '#9fe3e8'; very subtle bands in lighter/darker cyan; slight vertical gradient.

**Neptune** (1024x512): base '#2b4bd6' → '#1b2f8f'; bands in lighter blue; dark spot ellipse; white streaks (thin elongated blobs).

**Moon** (512x256): gray base '#9a9a9a', maria dark patches [90,90,95], craters.

**Ring texture** (512x8 or 512x64): radial bands. Draw with x = radius fraction:
- Fill with gradient, then draw many vertical bands with varying alpha of tan/white/brown; a couple of dark gaps (e.g., Cassini division around x=0.62 with low alpha).
Actually with alpha, we need the canvas to support transparency: use ctx.clearRect then draw with alpha values, so the texture has alpha. Use material transparent:true.

Let's implement: for x from 0..512: n = smooth noise → alpha = 0.15 + 0.85*noise, color varying between (230,215,180) and (150,125,95). Draw 1px column. Then add gaps: multiply alpha near certain ranges.

To make it look nice, I'll compute for each column with a function that has multiple octaves. Also, since the ring is quite thin, we can just use a 1D-ish gradient.

Ring UV: I'll rewrite UVs for the RingGeometry.

RingGeometry(inner, outer, thetaSegments, phiSegments) — vertices ordered by radius rings then theta. UVs default map to a square. I'll recompute after creation:
```js
const pos = geo.attributes.position;
const uv = geo.attributes.uv;
const v3 = new THREE.Vector3();
for(let i=0;i<pos.count;i++){
  v3.fromBufferAttribute(pos,i);
  const d = v3.length();
  uv.setXY(i, (d-inner)/(outer-inner), 0.5);
}
```
Wait, RingGeometry vertices are in the XY plane by default (then we rotate the mesh -PI/2 about X to lay flat). The position attribute distance from origin in XY = radius. Yes, v3.length() works since z=0.

Good.

Now planets data and construction.

```js
const PLANETS = [
 {name:'Mercury', size:0.62, dist:18, speed:0.55, spin:0.10, incl:0.12, tex: mercuryTexture, camDist:3.4, camH:1.1, phase:0.4},
 ...
];
```
Wait, transition blend: for planets, the camera position offset should be relative and drift.

Camera distance per planet: I'll define camDist as a multiple of planet radius, e.g., 4.2 * radius, with a minimum of 3.
- Mercury r=0.81 → 3.4
- Venus r=1.26 → 5.3
- Earth r=1.3 → 5.5 (offset maybe 5.2)
- Mars r=0.95 → 4.0
- Jupiter r=4.35 → 18
- Saturn r=4.0 → 17 (need rings visible: rings extend 2.3*4 = 9.2, so distance 17 gives ring angular radius atan(9.2/17)=28° > half FOV 25. Too big. Use 26.)
- Uranus r=2.6 → 11
- Neptune r=2.56 → 11

Half-vertical FOV with fov=50 and aspect 16:9 → vertical half = 25°, horizontal half = atan(tan(25°)*1.78)=39.7°. Ring radius 9.2 at distance 26 → 19.5° angular radius. Fits vertically within 25°. Good.

For Saturn's offset, add tilt so the rings are seen at an angle: offset (0, 6, 26) etc. And note that Saturn's rings are tilted relative to the ecliptic — I'll tilt Saturn's ring mesh by ~26° relative to the planet's equator and rotate the planet's axis. Let's just tilt the whole saturn group by 26.7° on Z. Then the rings look tilted. And the camera offset has some Y so we see them.

Actually if the planet group is tilted around Z by 26.7°, the rings (rotated to lie in the group's equatorial plane) will be tilted in world space. And the camera looking from slightly above the ecliptic will see them nicely. Good.

Rotation of the planet group around Y for spin: I'll have a group per planet holding tilt; inside, the mesh spins on Y.

Structure:
```
planetGroup (position updated per frame from orbit)
  tiltGroup (rotation.set(0,0,tiltZ) for Saturn/Uranus/Neptune optional)
    mesh (rotation.y spins)
  moonPivot (for Earth)
    moonMesh
```
Hmm, careful: tiltGroup rotation will also affect... only mesh children. Fine.

Also add axis tilt for Earth (23.4°) for realism — sure, subtle.

Orbit lines: circle with radius = dist, in XZ plane, rotated... Build with points:
```js
const pts=[]; for(let i=0;i<=256;i++){const a=i/256*TAU; pts.push(new THREE.Vector3(Math.cos(a)*dist,0,Math.sin(a)*dist));}
const g = new THREE.BufferGeometry().setFromPoints(pts);
const line = new THREE.Line(g, new THREE.LineBasicMaterial({color:0x335577, transparent:true, opacity:0.22}));
```
Maybe use LineLoop. Use Line with closed points. Also, since planets have inclination, maybe skip inclination entirely and keep orbits coplanar (simpler and cleaner). I'll add a very small inclination for visual depth: each planet's orbital plane is rotated slightly? That complicates the position math. Instead: compute position with a small inclination:
```
x = cos(a)*d; z = sin(a)*d; y = sin(a)*d*sin(incl)  → hmm that's an inclined circular orbit.
```
Actually an inclined circular orbit: position = R_z? Simpler: p = (d*cos(a), d*sin(a)*sin(i), d*sin(a)*cos(i)). That's a rotation about the X axis. That's fine and cheap. Orbits lines should match. I'll keep inclinations tiny (0 to 0.05 rad) — visually almost flat. Actually for the "sun close-up" and general look, keeping everything coplanar is cleanest. I'll add tiny inclinations (±0.02 rad) for subtle depth. Fine, and generate orbit line points with the same formula.

Hmm, keep it simple: all coplanar (y=0). The camera will be tilted, giving the 3D feel. Yes, coplanar. Simpler and no mismatch.

Orbital speeds: real periods: Mercury 88d, Venus 225, Earth 365, Mars 687, Jupiter 4333, Saturn 10759, Uranus 30687, Neptune 60190. If we use real relative speeds, Neptune barely moves. Use compressed: speed = 1/sqrt(period in years) ... Let's use speed = k * period_days^(-0.5): Mercury 1/9.4=0.107, Venus 0.067, Earth 0.052, Mars 0.038, Jupiter 0.015, Saturn 0.0096, Uranus 0.0057, Neptune 0.0041. Scale by k=6 → Mercury 0.64 rad/s (too fast? period 10s). During the ~3s Mercury close-up, it will move ~2 rad — that's a lot of motion, visible and fine (planets orbiting at different speeds is a requirement). Maybe k=4: Mercury 0.43 rad/s → period 14.7s. Neptune 0.016 rad/s → period 380s. Hmm Neptune hardly moves but that's ok.

Actually during the close-up, having the planet drift noticeably relative to the background is nice. Let's use k=4.

Also add initial phases so planets aren't aligned in a line.

Sizes: radius = pow(sizeEarthRatio, 0.5)... wait I need to keep "relative sizes that make sense". Using sqrt compression preserves ordering: Mercury smallest, Jupiter largest. Let me define `size` as the sqrt-compressed value directly times base:

Mercury: sqrt(0.383)=0.619
Venus: sqrt(0.949)=0.974
Earth: 1.0
Mars: sqrt(0.532)=0.729
Jupiter: sqrt(11.21)=3.348
Saturn: sqrt(9.45)=3.074
Uranus: sqrt(4.01)=2.003
Neptune: sqrt(3.88)=1.970

Multiply by base 1.35:
Mercury 0.836, Venus 1.315, Earth 1.35, Mars 0.984, Jupiter 4.52, Saturn 4.15, Uranus 2.70, Neptune 2.66.

Good.

Distances: Mercury 18, Venus 24, Earth 31, Mars 39, Jupiter 60, Saturn 80, Uranus 100, Neptune 118.

Camera at Neptune's close-up (distance 11) — the sun is 118 away, tiny. Fine. But the sun's light reaches Neptune with decay 0 → same brightness as Mercury. Good for visibility.

Now, the tour key list with target object references. I'll build after creating the scene:

```js
const sunObj = {obj: sunGroup, name:'The Sun'...};
```
Actually the first key targets the sun with a wide offset — name "The Solar System".

Keys:
```js
const keys = [
 {label:'The Solar System', sub:'Eight planets · one star', target: sunPivot, offset: new THREE.Vector3(0, 170, 330), drift: 0.0, dur: 3.0},
 {label:'Mercury', ...},
 ...
];
```
Where the target is an Object3D whose position is updated (planet groups; the sun group stays at origin).

Camera computation each frame:
```js
let t = tourTime; // loop time
// find segment
let acc=0, i=0;
for(; i<keys.length; i++){ if(t < acc + keys[i].dur) break; acc += keys[i].dur; }
```
Careful when i reaches keys.length (t exactly at end). Handle t = t % total (< total) so ok.

Actually I want the loop to restart at t=0 with the transition from the last key (Neptune) to key 0 happening during key 0's first 40%. So for segment index 0, prev = keys[last]. Good.

```js
const k = keys[i], prev = keys[(i-1+keys.length)%keys.length];
const p = (t - acc) / k.dur;
const blend = smoothstep(clamp(p/0.42,0,1)); // transition over first 42%
const camA = camPosFor(prev, time);  // current frame world pos + offset
const camB = camPosFor(k, time);
camera.position.lerpVectors(camA, camB, blend);
lookTarget.lerpVectors(prev.target.position, k.target.position, blend);
camera.lookAt(lookTarget);
```
where camPosFor(key, time) = key.target.position + offset rotated around Y by time*drift + key.spinPhase.

Wait: rotating the offset around Y by time*drift means during the hold the camera circles the planet. But the "blend" between camA and camB also uses these drifting positions, which is fine.

But there's a subtlety: for the wide "Solar System" shot, the target is the sun at origin, and its offset rotates around Y with drift=0.03 → the camera slowly circles. That's fine and nice.

Also: for key 0 at the loop restart, during the transition from Neptune (camA = neptune pos + small offset) to key 0 (camB = wide), the interpolation is in world space, so the camera flies from Neptune outward. Nice.

However, note the blend from key i-1 to key i uses camA computed at the *current* time with key i-1's target position. Since planets move, camA moves. OK.

One problem: for i=0 (first key), prev = last key. During the first 42% of key 0's duration the camera travels from Neptune to the wide shot. At t=0 the camera is at Neptune, which might look odd at the very start. Since the loop starts at t=0, the first thing the viewer sees is the camera pulling out from Neptune... and the "everything important within 30 seconds" wouldn't hold because each planet is visited at the right times but at t=0 you're at Neptune.

Hmm. That's a problem for the recording window. The requirement says the animation shows everything important within the first 30 seconds. If at t=0 we're near Neptune and then swing wide and then Mercury etc., all 8 planets are still shown within the first 27.4 seconds. So it's fine. But the opening shot (camera at Neptune pulling back) isn't ideal.

Better: make the loop start with a clean wide shot. Option: define the timeline such that key 0 (wide shot) has no transition at its start... i.e., treat the first iteration specially? Or restructure: put the overview at the end of the list and give the "transition" to the first key as happening during the *previous* key's end? 

Alternative approach: the transition blend happens at the END of each segment instead of the beginning. I.e., during segment i, camera holds on target i for the first 60% and then transitions to key i+1 over the last 40%. Then at t=0 the camera is exactly at key 0's position (wide shot, no motion except drift), and everything proceeds. The last key (Neptune) transitions back to key 0 which is the wide shot, and at loop restart t=0 the camera is at key 0 = matches the end state. Continuous.

But careful: at t=0 the camera = key0 position exactly, and at the end of the last segment it approaches key0's position closely. Since the drift rotation depends on absolute loop time (t), key0's offset at t=0 vs at t=total differ slightly. With drift small, it's fine. Actually for continuity, use the loop time t for the drift so that at t=0 the rotation angle = 0 and at t=total the angle = total*drift (a bit different), causing a small jump when looping. To fix: make the drift for key 0 zero (fixed wide shot). Or make the drift angle depend on loop time with periods dividing the loop... Simplest: set key 0's drift = 0 (static wide shot). Then at t=0 and t=total, the camera position for key 0 is identical. 

For the other keys, the drift at the moment of transition: at the end of segment i, camA (key i) with drift, camB (key i+1) with drift — no continuity issue at loop boundary as long as key0 is static. At the loop wrap: end of the last segment gives blend=1 → camera at key0's static position. At t=0, segment 0, blend=0 (start of hold) → camera at key0's position. Continuous. 

So implement the transition at the end of the segment:
```js
const p = (t-acc)/k.dur;
const next = keys[(i+1)%keys.length];
const blend = smoothstep(clamp((p - 0.58)/0.42, 0, 1));
camPos = lerp(camForKey(k), camForKey(next), blend)
lookTarget = lerp(k.target.position, next.target.position, blend)
```
And the label: show k.label with opacity fading in quickly at the start and fading out during the transition. Label opacity = smoothstep(0,0.18,p) * (1 - smoothstep(0.55,0.9,p)). Then during the transition, the next label fades in as p goes 0.58→1? Hmm, the label would show next.label with opacity rising. Let's compute: if blend > 0.5, show next's label with opacity = (blend-0.5)*2 * something. Simpler: label opacity = f(p) for current; and when blend > 0.55, switch to the next label with opacity = smoothstep(0.55,0.95, p). Hmm, that means during transition the current label fades out and the next fades in quickly. It might look abrupt but ok.

Let me just do:
```js
let labelOpacity, labelName, labelSub;
const fadeIn = smoothstep(0, 0.14, p);
const fadeOut = 1 - smoothstep(0.52, 0.78, p);
let op = Math.min(fadeIn, fadeOut);
if (blend > 0.5) { // switching to next
  const q = (blend - 0.5) / 0.5;   // 0..1
  labelName = next.label; labelSub = next.sub;
  op = q * q;   // new one fades in
}
```
Hmm, but then at the very end of the segment the next label is at opacity 1, and at p=0 of the next segment fadeIn = 0 → it drops to 0 then rises. That causes a flicker. Better: don't fade in the next label during the transition; just fade the current out at the transition start and fade the next in at the start of its segment. So:

op = smoothstep(0,0.12,p) * (1 - smoothstep(0.6,0.85,p));

and the name shown during the segment is the current key's name. During the transition (p from 0.6 to 1), the label fades out and the camera moves; then the next segment's label fades in over 0.12*3s = 0.36s. Good, clean.

But note at t=0, key0's label fades in over 0.36s. Fine.

Timing check with transitions at the end: each segment's hold is 58% of dur, then a transition of 42%. So for a 2.8s segment, the hold is 1.6s and the transition 1.2s. The camera is only "showing each one close up" for 1.6s + the drift. Hmm, that's a short look. Maybe extend segment durations a bit and reduce the transition fraction. Let's use transition fraction 0.35 and holds of ~65%.

Recompute durations to fit within 30s:
0 Sun/overview: 3.2
1 Mercury: 2.9
2 Venus: 2.9
3 Earth: 3.7
4 Mars: 2.9
5 Jupiter: 3.5
6 Saturn: 3.7
7 Uranus: 2.9
8 Neptune: 3.1
Sum = 28.8. Transition from Neptune back to overview happens during the last 35% of Neptune = 1.09s, ending at t=28.8 with the camera at the overview. Then loop restarts. 

Hmm, but the last transition begins at 28.8-1.09 = 27.7s, so from 27.7s onward the camera is flying from Neptune to the wide view, arriving at ~28.8s. Then the loop restarts and we see the wide view for the first 65% of 3.2 = 2.08s. So the whole tour is within 28.8s. 

Everything important (all 8 planets + sun + moon + rings) seen within ~28s. Good.

Now, with transition fraction 0.35, the hold for Mercury is 1.88s of close-up. Acceptable.

Let me now double check the moon visibility during the Earth segment. Earth's camDist ~5.5 * ... let's set Earth's camDist to 7 so the moon (orbit radius ~3.2, moon radius 0.35) is visible in frame. Earth radius 1.35 at distance 7 → angular radius 11°, half FOV 25°. Moon at 3.2 from Earth → within the frame when positioned to the side. Good. Moon orbit radius 3.4, moon radius 0.37. Moon orbit speed: 0.8 rad/s? Real moon period 27.3 days vs Earth's year... compressed anyway. Let's use 0.55 rad/s so during the 3.7s Earth segment the moon moves ~2 rad — visible motion. 

Now the starfield. 4000 stars on a sphere shell radius between 900 and 1800 — but far plane is 6000, ok. Camera far must cover it: camera.far = 8000 with near 0.1 → depth precision issues? Use near 0.5, far 8000 → ratio 16000, ok with logarithmic? Not needed; use near 0.3.

Actually the camera can be at distance ~330 from origin in the wide shot; starfield at 1200-2500 radius is fine.

Let me set star sphere radius min 1200, max 2600. And camera.far = 8000.

Star colors: mostly white/blue-white with a few warm. Use vertexColors with PointsMaterial.

Points size: with sizeAttenuation false, size in pixels → 1.5–2.5. But different sizes per star require different PointsMaterial... With vertexColors we can vary brightness but not size. Use two Points objects: one with size 2.2 (fewer, brighter) and one with 1.3 (many faint). Good.

Also add a faint nebula? Skip, or add a large sprite with a soft blue-purple radial gradient at a distant point. Could be a nice touch but might look odd. Skip; instead add a subtle background gradient color: scene.background = a dark color, e.g. new THREE.Color(0x02030a). Plus fog? No fog (would dim planets weirdly with decay 0 light... actually fog would be ok but skip).

Now let's write the code carefully.

```js
import * as THREE from 'three';

const TAU = Math.PI*2;
const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));
const smoothstep=(a,b,x)=>{const t=clamp((x-a)/(b-a),0,1);return t*t*(3-2*t);};
```

Textures:

```js
function makeTexture(w,h,draw){
  const canvas=document.createElement('canvas');
  canvas.width=w; canvas.height=h;
  const ctx=canvas.getContext('2d');
  draw(ctx,w,h);
  const tex=new THREE.CanvasTexture(canvas);
  tex.colorSpace=THREE.SRGBColorSpace;
  tex.anisotropy=8;  // might need renderer capabilities; setting 8 blindly is fine (clamped by driver? Actually three uses it as-is; if max is lower it may warn). Use 4.
  tex.wrapS=THREE.RepeatWrapping;
  return tex;
}
```
Anisotropy: set maxAnisotropy from renderer after creation. I'll create the renderer first, then compute `const MAXA = renderer.capabilities.getMaxAnisotropy();`.

Order: create renderer, then textures.

Helper for sphere-wrapped blobs:

```js
function blob(ctx,w,h,x,y,r,rgb,a){
  for(const dx of [-w,0,w]){
    const g=ctx.createRadialGradient(x+dx,y,0,x+dx,y,r);
    g.addColorStop(0,`rgba(${rgb[0]},${rgb[1]},${rgb[2]},${a})`);
    g.addColorStop(1,`rgba(${rgb[0]},${rgb[1]},${rgb[2]},0)`);
    ctx.fillStyle=g;
    ctx.beginPath();ctx.arc(x+dx,y,r,0,TAU);ctx.fill();
  }
}
```
This will be a bit slow if called thousands of times with gradient creation, but we're only doing it at load. For Jupiter there might be ~300 calls * 3 = 900 gradients. Fine.

Textures at 1024x512 with heavy per-pixel work — keep the loops reasonable.

Let me write each texture function now.

```js
function texSun(){
  return makeTexture(1024,512,(ctx,w,h)=>{
    ctx.fillStyle='#ff9d1a'; ctx.fillRect(0,0,w,h);
    const rnd=rand(7);
    // large-scale mottling
    for(let i=0;i<160;i++){
      const x=rnd()*w, y=rnd()*h, r=20+rnd()*90;
      const warm=rnd()>0.5;
      blob(ctx,w,h,x,y,r,warm?[255,236,150]:[255,90,10],0.35);
    }
    // granules
    for(let i=0;i<3000;i++){
      const x=rnd()*w,y=rnd()*h,r=2+rnd()*7;
      blob(ctx,w,h,x,y,r,rnd()>0.5?[255,250,200]:[255,120,20],0.18);
    }
  });
}
```
3000 blobs * 3 gradients = 9000 gradient creations — that's maybe slow (each gradient creation is cheap-ish, but 9000 objects... probably ~50-100ms). Acceptable. But rendering 9000 arcs on a 1024x512 canvas... fine.

Hmm, the sun's texture is mostly covered by the glow sprite anyway. Simplify: 1200 granules.

Mercury:
```js
function texMercury(){
  return makeTexture(1024,512,(ctx,w,h)=>{
    ctx.fillStyle='#8b8b8b'; ctx.fillRect(0,0,w,h);
    const rnd=rand(11);
    for(let i=0;i<70;i++) blob(ctx,w,h,rnd()*w,rnd()*h,40+rnd()*110, rnd()>0.5?[120,120,122]:[170,170,168],0.35);
    craters(ctx,w,h,rnd,180,1);
  });
}
function craters(ctx,w,h,rnd,count,scale){
  for(let i=0;i<count;i++){
    const x=rnd()*w, y=rnd()*h, r=(3+rnd()*14)*scale;
    ctx.globalAlpha=0.30+rnd()*0.25;
    ctx.fillStyle='#4a4a4a';
    ctx.beginPath();ctx.arc(x,y,r,0,TAU);ctx.fill();
    ctx.globalAlpha=0.35;
    ctx.strokeStyle='#e0e0e0';
    ctx.lineWidth=Math.max(1,r*0.18);
    ctx.beginPath();ctx.arc(x-r*0.12,y-r*0.12,r*0.9,0,TAU);ctx.stroke();
    ctx.globalAlpha=1;
  }
}
```
Note craters near the seam: circles at x near 0 or w get clipped and won't wrap → visible seam with a half-crater. Acceptable/minor. I could wrap them too: draw the arc three times like blobs. Let's make the crater helper wrap as well (draw at dx -w, 0, w) when near the edge. Simpler: choose x = 30 + rnd()*(w-60) to keep away from the edges — but then there's a vertical band free of craters, which is worse. Let's wrap: draw the crater body at each of the 3 offsets using ctx.save/restore... just loop over dx like blobs. It's cheap.

Venus:
```js
function texVenus(){
  return makeTexture(1024,512,(ctx,w,h)=>{
    const g=ctx.createLinearGradient(0,0,0,h);
    g.addColorStop(0,'#d9b877'); g.addColorStop(0.5,'#f0d9a4'); g.addColorStop(1,'#d9b877');
    ctx.fillStyle=g; ctx.fillRect(0,0,w,h);
    const rnd=rand(23);
    for(let i=0;i<120;i++){
      const y=rnd()*h;
      // wavy streak
      ctx.beginPath();
      const x0=rnd()*w, len=120+rnd()*400, amp=6+rnd()*20;
      for(let x=0;x<=len;x+=8){
        const xx=x0+x, yy=y+Math.sin(x*0.02+i)*amp;
        x?ctx.lineTo(xx,yy):ctx.moveTo(xx,yy);
      }
      ctx.strokeStyle=rnd()>0.5?'rgba(255,244,205,0.35)':'rgba(180,140,80,0.28)';
      ctx.lineWidth=4+rnd()*14; ctx.stroke();
    }
    for(let i=0;i<80;i++) blob(ctx,w,h,rnd()*w,rnd()*h,40+rnd()*90,[255,240,200],0.18);
  });
}
```
Note: streaks starting at x0 near the right edge will be clipped — minor, fine.

Earth:
```js
function texEarth(){
  return makeTexture(1024,512,(ctx,w,h)=>{
    // ocean
    const og=ctx.createLinearGradient(0,0,0,h);
    og.addColorStop(0,'#0a2a55'); og.addColorStop(0.35,'#0e4a8f'); og.addColorStop(0.5,'#1567b8'); og.addColorStop(0.65,'#0e4a8f'); og.addColorStop(1,'#0a2a55');
    ctx.fillStyle=og; ctx.fillRect(0,0,w,h);
    const rnd=rand(101);
    // continents: cluster centers
    const clusters=[[0.16,0.30],[0.22,0.62],[0.30,0.45],[0.45,0.32],[0.52,0.62],[0.62,0.40],[0.72,0.30],[0.78,0.68],[0.88,0.45],[0.06,0.5]];
    for(const [cx,cy] of clusters){
      const n=6+Math.floor(rnd()*8);
      for(let i=0;i<n;i++){
        const x=(cx+(rnd()-0.5)*0.13)*w, y=(cy+(rnd()-0.5)*0.16)*h;
        const r=15+rnd()*70;
        const green = rnd()>0.35;
        blob(ctx,w,h,x,y,r, green?[60,120,60]:[150,140,80], 0.85);
        blob(ctx,w,h,x,y,r*0.6, green?[110,160,80]:[180,165,105], 0.5);
      }
    }
    // ice caps
    for(let i=0;i<140;i++){
      const x=rnd()*w;
      const top = rnd()<0.5;
      const y = top ? rnd()*h*0.09 : h - rnd()*h*0.09;
      blob(ctx,w,h,x,y,30+rnd()*60,[255,255,255],0.5);
    }
    ctx.fillStyle='rgba(255,255,255,0.9)'; ctx.fillRect(0,0,w,h*0.035); ctx.fillRect(0,h*0.965,w,h*0.035);
    // clouds
    for(let i=0;i<160;i++){
      const x=rnd()*w, y=rnd()*h;
      blob(ctx,w,h,x,y,20+rnd()*70,[255,255,255],0.13);
    }
  });
}
```
Wait, the ice caps rects at the top/bottom edges — since the sphere's poles map to v=0 and v=1, the top/bottom of the texture are the poles, so a full white band is fine (converges at the pole). But careful: at the poles, the texture wraps around → the white band is a proper cap. Good.

Note: the sphere UV mapping has v=0 at the bottom (three's SphereGeometry: v=0 at the south pole? It maps v from 0 at phiStart... For SphereGeometry, uv.y = 1 - v where the top is 1. Let me recall: in three's SphereGeometry, `uv.y = 1 - v` with v = iy/heightSegments, and iy=0 is at the top (theta = thetaStart = 0 → north pole, y = +radius). So at the top (north pole) uv.y = 1. And texture v=1 corresponds to the top of the canvas? In WebGL, texture coordinate v=0 is the bottom of the image by default (three flips textures with flipY=true default, so v=0 = bottom row of canvas... hmm). With flipY=true (default for CanvasTexture), the image is flipped so that uv (0,0) corresponds to the bottom-left of the canvas as displayed. So uv.y=1 → the top row of the canvas. North pole = uv.y = 1 = top row of canvas. Good — so the top of my canvas is the north pole. My ice caps at the top and bottom both work.

Mars:
```js
function texMars(){
  return makeTexture(1024,512,(ctx,w,h)=>{
    ctx.fillStyle='#b4461f'; ctx.fillRect(0,0,w,h);
    const rnd=rand(55);
    for(let i=0;i<90;i++) blob(ctx,w,h,rnd()*w,rnd()*h,40+rnd()*130,rnd()>0.5?[120,50,28]:[214,120,70],0.45);
    for(let i=0;i<40;i++) blob(ctx,w,h,rnd()*w,rnd()*h,20+rnd()*60,[90,40,25],0.30);
    craters(ctx,w,h,rnd,90,0.8);
    // polar caps
    for(let i=0;i<70;i++) blob(ctx,w,h,rnd()*w,rnd()*h*0.07,20+rnd()*45,[255,250,245],0.7);
    for(let i=0;i<40;i++) blob(ctx,w,h,rnd()*w,h-rnd()*h*0.06,15+rnd()*35,[255,250,245],0.6);
  });
}
```

Jupiter:
```js
function texJupiter(){
  return makeTexture(1024,512,(ctx,w,h)=>{
    const palette=[[196,166,124],[228,206,170],[168,128,92],[240,224,196],[186,146,106],[210,184,146]];
    const rnd=rand(777);
    for(let y=0;y<h;y+=2){
      const t=y/h;
      const n = Math.sin(t*Math.PI*11.0)*0.5 + Math.sin(t*Math.PI*23.0+1.7)*0.28 + Math.sin(t*Math.PI*5.0+0.4)*0.35 + Math.sin(t*Math.PI*41+2.1)*0.12;
      const idx=clamp((n+1.25)/2.5,0,0.999)*(palette.length-1);
      const i0=Math.floor(idx), i1=Math.min(palette.length-1,i0+1), f=idx-i0;
      const c=[0,1,2].map(k=>palette[i0][k]*(1-f)+palette[i1][k]*f);
      // polar darkening
      const pole = 1 - Math.pow(Math.abs(t-0.5)*2, 3)*0.35;
      ctx.fillStyle=`rgb(${Math.round(c[0]*pole)},${Math.round(c[1]*pole)},${Math.round(c[2]*pole)})`;
      ctx.fillRect(0,y,w,2);
    }
    // turbulence
    for(let i=0;i<260;i++){
      const x=rnd()*w, y=rnd()*h, ww=40+rnd()*200, hh=3+rnd()*10;
      ctx.globalAlpha=0.10+rnd()*0.18;
      ctx.fillStyle=rnd()>0.5?'#fff3d8':'#8a5a34';
      ctx.beginPath(); ctx.ellipse(x,y,ww,hh,0,0,TAU); ctx.fill();
    }
    ctx.globalAlpha=1;
    // great red spot
    const sx=w*0.62, sy=h*0.63, rx=80, ry=34;
    const g=ctx.createRadialGradient(sx,sy,0,sx,sy,rx);
    g.addColorStop(0,'rgba(190,70,45,0.95)');
    g.addColorStop(0.55,'rgba(200,100,70,0.75)');
    g.addColorStop(1,'rgba(210,150,110,0)');
    ctx.save(); ctx.translate(sx,sy); ctx.scale(1,ry/rx); ctx.translate(-sx,-sy);
    ctx.fillStyle=g; ctx.beginPath(); ctx.arc(sx,sy,rx,0,TAU); ctx.fill(); ctx.restore();
  });
}
```
Careful with the scale trick and the radial gradient—the gradient is defined in the untransformed space, but the transform applies when filling. It'll look like an ellipse. OK.

The turbulence ellipses near x=0/w will be clipped. Since they're subtle, fine.

Saturn: similar to Jupiter but paler, and no red spot.
```js
function texSaturn(){
  palette=[[222,202,158],[238,224,188],[198,172,126],[230,214,176],[206,182,138],[244,234,206]]
  ...
}
```
Add subtle streaks.

Uranus:
```js
base gradient '#a8e6e8' to '#79c9d6' plus faint bands
```
Draw horizontal bands with alpha using a sine-based noise, low contrast, then a few soft blobs.

Neptune:
```js
base '#2242c4' with gradient to '#152a80'; bands lighter '#3a5fe0'; dark spot at (0.35w,0.62h) ellipse '#101c5c'; white streaks.
```

Moon: gray with maria and craters.

Ring texture:
```js
function texRing(){
  return makeTexture(512,16,(ctx,w,h)=>{
    ctx.clearRect(0,0,w,h);
    const rnd=rand(99);
    for(let x=0;x<w;x++){
      const u=x/w;
      let n = Math.sin(u*90)*0.5 + Math.sin(u*31+1.2)*0.35 + Math.sin(u*173+0.6)*0.18 + Math.sin(u*7.3)*0.4;
      n = n*0.5+0.5; // 0..1
      let a = 0.10 + 0.85*Math.pow(n,1.3);
      // Cassini division and outer fade
      if(u>0.60&&u<0.66) a*=0.15;
      if(u>0.90) a*=Math.max(0,(1-(u-0.90)/0.10));  // hmm, ring outer edge fade
      if(u<0.06) a*=u/0.06;
      const bright=0.75+0.35*n;
      const c=[Math.round(232*bright),Math.round(214*bright),Math.round(180*bright)];
      ctx.fillStyle=`rgba(${c[0]},${c[1]},${c[2]},${a})`;
      ctx.fillRect(x,0,1,h);
    }
  });
}
```
Also maybe add fine random grain.

Now the geometry construction.

```js
const sunGroup = new THREE.Group(); scene.add(sunGroup);
const sunRadius = 4.6;
const sunTex = texSun();
const sunMat = new THREE.MeshBasicMaterial({map:sunTex, color:0xffffff, toneMapped:false});
const sunMesh = new THREE.Mesh(new THREE.SphereGeometry(sunRadius, 64, 48), sunMat);
sunGroup.add(sunMesh);
```
Hmm, toneMapped:false with a texture means the raw sRGB texture is output directly; the texture is a bright orange, so the sun will look orange. Good. Maybe boost color to a bright yellow-white: color 0xfff2cc.

Glow sprites:
```js
const glowTex = makeGlowTexture();
const glow1 = new THREE.Sprite(new THREE.SpriteMaterial({map:glowTex, color:0xffcc55, transparent:true, blending:THREE.AdditiveBlending, depthWrite:false, toneMapped:false}));
glow1.scale.setScalar(sunRadius*7);
sunGroup.add(glow1);
const glow2 = ... color 0xff9933, scale sunRadius*14, opacity 0.5
```
The glow texture: radial gradient from rgba(255,255,255,1) at center to transparent, with a strong falloff: stops at 0→1, 0.15→0.75, 0.35→0.25, 0.6→0.06, 1→0.

But a sprite always faces the camera — good.

Also, the sun mesh itself should be bright. With ACES tone mapping disabled for it (toneMapped false), the orange texture is displayed as-is. Maybe overlay a second slightly larger sphere with additive blending? The sprite handles the halo. Good enough.

Now planets:

```js
const PLANET_DATA = [
  {name:'Mercury', r:0.836, dist:18, speed:0.43, spin:0.25, tex:texMercury(), cam:3.6, camY:1.0, phase:1.7, tilt:0.03, cap:'The Swiftest Planet', sub:'0.39 AU from the Sun'},
  ...
];
```
Hmm, `sub` captions: nice. Let's include a short descriptor.

Data:
- Mercury: dist 18, speed 0.43, spin 0.20, cam 3.4
- Venus: dist 24, speed 0.30, spin 0.12, cam 5.2
- Earth: dist 31, speed 0.24, spin 0.55, cam 7.0 (with moon), tilt 0.41
- Mars: dist 39, speed 0.19, spin 0.5, cam 4.2
- Jupiter: dist 60, speed 0.09, spin 0.9, cam 18
- Saturn: dist 80, speed 0.065, spin 0.8, cam 26, rings
- Uranus: dist 100, speed 0.045, spin 0.5, cam 12
- Neptune: dist 118, speed 0.035, spin 0.5, cam 11.5

Check speeds: k=4 with period^-0.5 gave Mercury 0.43, Venus 0.27, Earth 0.21, Mars 0.15, Jupiter 0.061, Saturn 0.039, Uranus 0.023, Neptune 0.016. Let me use these values (scaled a bit). Actually with Mercury at 0.43 rad/s, during its 2.9s segment it moves 1.25 rad = 71°, and it needs to travel 360/0.43 = 14.6s per orbit. Fine, visible motion vs the starfield. Good.

But wait — for the camera to hold on Mercury closely, and Mercury moves 71° during the segment, the camera follows it (position = target + offset). Since the whole scene moves, the background stars drift — nice parallax effect.

Set speeds:
Mercury 0.44, Venus 0.28, Earth 0.21, Mars 0.15, Jupiter 0.062, Saturn 0.040, Uranus 0.024, Neptune 0.017.

Hmm, but Jupiter/Saturn/Uranus/Neptune will barely move during their ~3s segments (0.19 rad = 11° for Jupiter, 0.07 rad for Neptune = 4°). That's fine — they're still "orbiting at different speeds".

Phases: random-ish starting angles to spread them out: Mercury 0.3, Venus 2.1, Earth 4.0, Mars 5.3, Jupiter 1.1, Saturn 3.2, Uranus 5.6, Neptune 2.6. Hmm, for the wide establishing shot at the start, we'd like the planets spread around the sun nicely — they are.

But also the camera "flies from planet to planet" — long trips are fine.

Actually, one consideration: when transitioning from Mercury (dist 18) to Venus (dist 24), if they're on opposite sides of the sun, the camera flies across the sun — which is nice visually (passing the sun). OK.

Now build:

```js
const planets=[];
for(const d of PLANET_DATA){
  const group=new THREE.Group();
  group.userData = d;
  scene.add(group);
  const tiltGroup=new THREE.Group();
  tiltGroup.rotation.z = d.tilt||0;
  group.add(tiltGroup);
  const mesh=new THREE.Mesh(new THREE.SphereGeometry(d.r,48,32), new THREE.MeshStandardMaterial({map:d.tex, roughness:0.85, metalness:0.0}));
  tiltGroup.add(mesh);
  ...
  planets.push({data:d, group, mesh, ...});
}
```

For rings (Saturn), add the ring mesh to tiltGroup.

For Earth's moon: add moonPivot to the group (not tiltGroup, so it isn't affected by Earth's axial tilt):
```js
const moonPivot=new THREE.Group(); group.add(moonPivot);
const moonMesh=new THREE.Mesh(new THREE.SphereGeometry(0.37,32,24), moonMat);
moonMesh.position.set(3.6,0,0);
moonPivot.add(moonMesh);
```
And rotate moonPivot.rotation.y = t*0.55. Also tilt the moon's orbit slightly: moonPivot.rotation.z = 0.09? That would tilt the orbit plane; setting rotation.z first then rotation.y? Order matters (default XYZ). rotation.set(0, angle, 0.09) → applies X then Y then Z... Euler XYZ order applies as R = Rz*Ry*Rx? In three, Euler 'XYZ' means the rotation matrix = Rx*Ry*Rz? Actually THREE.Euler order 'XYZ' produces R = Rx * Ry * Rz applied to vectors... hmm, I recall three's makeRotationFromEuler for 'XYZ' computes R = Rx*Ry*Rz. Whatever — a slight tilt is cosmetic. I'll set moonPivot.rotation.x = 0.09 and rotate the pivot's child? Simplest: put the moon at (3.6,0,0) inside moonPivot, set moonPivot.rotation.z=0.09 (constant tilt) and animate rotation.y. With order 'XYZ'... the tilt may end up being around the world axis or not. To be safe, wrap: outerTiltGroup (rotation.z=0.12) containing moonPivot (rotation.y animated) containing moonMesh. Clean.

Also the moon should be lit by the sun — yes, standard material.

Orbit lines: for each planet, a Line with the circle at radius=dist.

Also maybe add a ring for the Earth? No.

Starfield: as described.

Now the label overlay:

```html
<div id="labels">
  <div id="nameBox">
    <div id="pname">The Solar System</div>
    <div id="psub"></div>
  </div>
</div>
```
Style with transitions? I'll set opacity directly per frame (no CSS transition) to keep sync.

Also maybe a progress bar at the bottom? Nice cinematic touch but could be distracting. Skip.

Add a small persistent top-left label: "SOLAR SYSTEM TOUR" small caps, opacity .4.

Now the animation loop:

```js
let startTime = null;
let loopTime = 0;
function animate(ts){
  requestAnimationFrame(animate);
  if(startTime===null) startTime = ts;
  const t = (ts - startTime)/1000;
  ...
}
```
The requirement: "Use the requestAnimationFrame timestamp for animation time." So use ts. Good. Use t for orbital positions and the tour clock (t % TOTAL).

For planet orbit angle: angle = phase + t * speed (absolute time, not looped — otherwise planets would jump at loop restart). Using absolute time means the positions advance continuously. But then the tour's segment target positions are continuous. The only discontinuity is the camera reset at the loop boundary for the static key 0 — which we handled by making key 0 static.

Wait, but there's another issue: key 0's target is the sun (at origin, static), so its camera position is fixed. Good.

Also, the moon angle uses absolute t.

Now let's also make the sun mesh rotate slowly: sunMesh.rotation.y = t*0.03.

Let me write the tour keys after planets are created. I need references to the target Object3D (the group) and offsets.

```js
const tourKeys = [
  {label:'The Solar System', sub:'A tour of eight worlds', target: sunGroup, off:new THREE.Vector3(0,190,340), drift:0.0, dur:3.2},
  ...for each planet: {label, sub, target: planet.group, off: vec, drift:0.05, dur}
];
```
Where the offset for a planet: direction (0.62, 0.28, 0.73) normalized * camDist, but for Saturn maybe more Y.

Let me define per planet in the data: cam (distance) and camY (height factor). offset = new Vector3(cam*0.72, cam*camY, cam*0.62)? That gives |offset| = cam*sqrt(0.72²+camY²+0.62²) roughly = cam*0.95 for camY=0.1. Fine — I'll just use a direction and normalize to cam:

```js
const dir = new THREE.Vector3(0.75, camY, 0.66).normalize();
off = dir.multiplyScalar(cam);
```
With camY = 0.22 for most, 0.35 for Saturn (to see the rings from above), 0.3 for the wide sun shot.

Drift: rotate the offset around Y by (t * drift). drift=0.05 rad/s → during a 3s hold, 0.15 rad = 8.6°, subtle. Let's use 0.08 for a nicer drift. But rotating the offset also moves the camera relative to the sun-lit side, changing the phase — nice.

Actually careful: the drift rotation makes the camera orbit the planet, but the planet's own orbital motion is fast for Mercury (0.44 rad/s) — the combined relative motion is fine.

Now, the camera lookAt target: lerp between prev.target.position and next.target.position. But the planet's position is its center. Looking at the center is fine. However, for a nicer composition, look slightly at the planet's center; the label is at the bottom of the screen. OK.

Hmm, one issue: for the wide shot of the sun, the "target" is the sun at (0,0,0) and the offset (0,190,340) → distance ~390. The whole system (Neptune at 118) would appear... the sun's orbit plane is seen from 190 above and 340 away → viewing angle ~29° above the ecliptic. The whole system spans 236 units, at distance 390 with fov 50 → vertical extent 2*390*tan(25)=364 units. So the system (236 across) fits in view. Good. The camera at y=190 looking at the origin sees the orbits as ellipses; Neptune's orbit radius 118 → the near edge at z=118 would be at distance ~sqrt(340-118)²+190²)... fine, all in view.

Let me reconsider the wide shot: the orbit lines will be visible as concentric ellipses — a classic beautiful solar system image. 

Now, the camera transition to the wide shot at the end will be a big pull-back. Good.

Let me set the wide shot to (0, 175, 330), drift 0, and maybe rotate extremely slowly? Since key0 must be static for loop continuity, use drift 0.

Now — important: at the loop restart, we're at t=0 = key0 which is the static wide shot, and the tour proceeds. Continuity: at the end of key8 (Neptune) we blended to key0's position, arriving at blend=1 → exactly key0's camera pos with static offset. At t=0 the camera = key0's pos. Match. 

Also lookAt continuity: at the end of the last segment, lookTarget = key0.target.position = (0,0,0). At t=0 the lookTarget = (0,0,0). Match. 

Now the label logic. Since the label changes at segment boundaries, and at t=0 it's key0's label fading in. Fine.

Let me write the render loop:

```js
function animate(ts){
  requestAnimationFrame(animate);
  if(t0===null) t0 = ts;
  const time = (ts - t0)/1000;

  // update planets
  for(const p of planets){
    const a = p.data.phase + time * p.data.speed;
    p.group.position.set(Math.cos(a)*p.data.dist, 0, Math.sin(a)*p.data.dist);
    p.mesh.rotation.y = time * p.data.spin + p.data.phase;
    if(p.moonPivot) p.moonPivot.rotation.y = time*0.55;
    if(p.rings) p.rings.rotation.z = ... // rings don't need spin, but slow rotation is nice: inside tiltGroup, rotating the ring mesh about its own axis (y after rotation) — skip.
  }
  sunMesh.rotation.y = time*0.02;

  // tour
  const loopT = time % TOUR_TOTAL;
  ...
  renderer.render(scene, camera);
}
```

Note: for the planets' group position, `Math.sin(a)` for z and cos for x — consistent for the orbit lines too (which are circles anyway).

Camera computation:

```js
let acc=0, ki=0;
for(ki=0;ki<tourKeys.length;ki++){
  if(loopT < acc + tourKeys[ki].dur) break;
  acc += tourKeys[ki].dur;
}
if(ki>=tourKeys.length) ki = tourKeys.length-1;   // safety
```
Hmm, when loopT < acc+dur breaks, we know loopT >= acc. p = (loopT-acc)/dur.

Then:
```js
const key = tourKeys[ki], nxt = tourKeys[(ki+1)%tourKeys.length];
const p = (loopT-acc)/key.dur;
const blend = smoothstep(0.62, 1.0, p);
const camCur = camPos(key, time), camNext = camPos(nxt, time);
camera.position.lerpVectors(camCur, camNext, blend);
tmpTarget.lerpVectors(key.target.position, nxt.target.position, blend);
camera.lookAt(tmpTarget);
```
Wait, `key.target.position` — the group positions are in world space (they're direct children of the scene), so fine.

camPos(key, time):
```js
const off = key.off.clone().applyAxisAngle(UP, time*key.drift);
return off.add(key.target.position);
```
Cloning per frame is fine (a few allocations per frame; acceptable). Or use a scratch vector.

Label opacity: 
```js
const op = smoothstep(0,0.10,p) * (1 - smoothstep(0.66,0.95,p));
nameEl.style.opacity = op;
```
And when the key changes, update the text. Track lastKeyIndex; when it changes, set the text content. But during the fade-out at the end of a segment, the text switches only at the boundary — at which point the opacity is ~0 (since fade-out reaches 0 at p=0.95 and the boundary is p=1). Good, so the switch is invisible.

Hmm, one detail: at p slightly less than 0.95, opacity ~0. Fine.

Also, I want the label to move slightly (subtle upward drift) — CSS transform based on opacity? Skip.

Now, resizing:
```js
addEventListener('resize', ()=>{
  camera.aspect = innerWidth/innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});
```

Also handle devicePixelRatio changes? Not needed.

Let's also add a subtle "sun flare" or lens flare? Skip.

One more thing: the halo sprite might be occluded by planets passing in front — with depthWrite false and additive blending, the sprite renders after opaque objects if transparent. Sprites are in the transparent queue; depth test is on by default, so if a planet is in front of the sprite... The sprite is at the sun's center and the planets are far from it, so no issue.

For the sun's glow sprite when the camera is close to the sun (wide shot at distance 390): the sprite scale is sunRadius*7 = 32 units — at 390 distance that's small. Hmm, we want a nice halo at any distance. Maybe scale the sprite bigger: sunRadius*9 for the inner glow, *20 for the outer. At distance 390, a 90-unit sprite → angular size ~13°, visible. Good.

Actually let's add three glow layers: 5.5x (bright core), 12x (medium), 26x (faint outer). Colors 0xfff0c0, 0xffb347, 0xff7b1a, opacities 0.9, 0.45, 0.22. Since additive, they build up.

Now, about tone mapping and the halo: with toneMapped=false, the sprite colors are output directly. Additive blending sums up, and values >1 get clamped to 1. Fine, gives a white-hot core.

Now let me also consider: with ACES tone mapping applied to the planets, plus a pointLight of intensity 4 and decay 0... Let me double check three r186's point light behavior with decay=0. In three's `getDistanceAttenuation(lightDistance, cutoffDistance, decayExponent)`: if decayExponent > 0 → pow(...); else return 1.0 (when cutoffDistance is 0 → `if (cutoffDistance > 0 && ...) return 0; return 1` — hmm, let me recall the actual shader code:

```glsl
float getDistanceAttenuation( const in float lightDistance, const in float cutoffDistance, const in float decayExponent ) {
  float distanceFalloff = 1.0 / max( pow( lightDistance, decayExponent ), 0.01 );
  if ( cutoffDistance > 0.0 ) {
    distanceFalloff *= pow2( saturate( 1.0 - pow4( lightDistance / cutoffDistance ) ) );
  }
  return distanceFalloff;
}
```
With decayExponent = 0: pow(d, 0) = 1 → distanceFalloff = 1/1 = 1 (since max(1, 0.01) = 1). Good, constant attenuation.

And the point light irradiance: `getPointLightInfo` → `light.color = pointLight.color * pointLight.intensity * attenuation`? Actually in the WebGLRenderer's light setup (WebGLLights), for point lights:
```js
uniforms.color.copy( light.color ).multiplyScalar( light.intensity );
```
Then in the shader: `irradiance = pointLight.color * getDistanceAttenuation(...) * dotNL`. And for physical correctness, three multiplies by PI somewhere? In the older version there was `scaleFactor = Math.PI` when useLegacyLights was false... Let me recall r155 changelog: "useLegacyLights now defaults to false" and lights are physically correct; PointLight intensity in candela; for legacy behavior, intensity was multiplied by PI. In `WebGLLights.setup`, I believe there's:

```js
} else if ( light.isPointLight ) {
  const uniforms = cache.get( light );
  uniforms.color.copy( light.color ).multiplyScalar( light.intensity * scaleFactor );
```
where `scaleFactor = ( useLegacyLights === true ) ? Math.PI : 1;`. And in r165, useLegacyLights was removed, leaving scaleFactor = 1.

So irradiance = intensity * color * attenuation = 4 for decay 0. Then the diffuse BRDF divides by π: outgoing radiance = albedo * irradiance * dotNL / π ≈ 4/3.14 ≈ 1.27 * albedo at dotNL=1. With ACES tone mapping and exposure 1.1, 1.27*1.1 = 1.4 → tone mapped to a bright but not blown value. That's reasonable. Maybe intensity 3.5 is better. I'll use 3.6 and exposure 1.1.

Also for the ambient light: AmbientLight contributes irradiance = color*intensity directly; outgoing = albedo * color * intensity / π? Ambient: `irradiance = ambientLightColor` and then diffuse = albedo * irradiance / π? Actually three's ambient: `vec3 irradiance = getAmbientLightIrradiance( ambientLightColor );` which returns ambientLightColor (already multiplied by intensity). Then `RE_IndirectDiffuse( irradiance, ... )` → `reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor )` where BRDF_Lambert = diffuseColor * RECIPROCAL_PI. So ambient also divides by π. So ambient intensity 0.6 with color blue → 0.6*0.3 = 0.18 irradiance → 0.06 outgoing. Pretty dim. Use intensity 1.2 for a visible dark-side fill: 1.2*0.25/π ≈ 0.095. Still dim but visible. Let's use ambient color 0x5577bb intensity 1.5 → ~0.15 on the dark side (with ACES + sRGB, that's a visible dark blue-gray). Hmm, that might wash out the dark sides too much. Let's use 0.9.

Fine — I'll go with ambient(0x3a5a9c, 1.0). Values are tunable but I can't test; I'll pick reasonable ones.

Since I can't visually verify, I should be conservative: the planets should clearly be lit. Sun light intensity 3.6 with decay 0 guarantees that.

Now, one risk: `toneMapped=false` on MeshBasicMaterial — supported (Material.toneMapped). Yes.

Another risk: `THREE.SRGBColorSpace` exists in r186. Yes.

CanvasTexture with `colorSpace = THREE.SRGBColorSpace` — correct for color maps.

Let's write the star field:

```js
function makeStars(){
  const geo=new THREE.BufferGeometry();
  const N=4000;
  const pos=new Float32Array(N*3), col=new Float32Array(N*3), siz=[];
  ...
}
```
Two point clouds for size variety: I'll build one geometry with 3500 faint stars (size 1.2) and another with 400 brighter (size 2.4). Colors: white, blue-white, warm.

Point material: `new THREE.PointsMaterial({size:1.4, sizeAttenuation:false, vertexColors:true, transparent:true, opacity:0.9, depthWrite:false, map:starSprite, alphaTest:0.01, blending:NormalBlending})`. With sizeAttenuation false and map with alpha, the sprite is drawn in screen space with the size in pixels. Round star texture: 32x32 radial gradient. Using blending additive would make overlapping stars brighter — nice for a "glow" look. Let's use AdditiveBlending with a soft round sprite, opacity 0.9. Hmm, additive on a dark background is fine.

Actually with additive blending and vertexColors, dim stars just add little. Good.

Let's do it.

Now write the HTML/CSS.

```css
*{box-sizing:border-box}
html,body{margin:0;padding:0;height:100%;overflow:hidden;background:#000;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
#c{position:fixed;inset:0;display:block}
#ui{position:fixed;inset:0;pointer-events:none;overflow:hidden}
#vignette{position:fixed;inset:0;pointer-events:none;
  background:radial-gradient(ellipse at 50% 50%, rgba(0,0,0,0) 35%, rgba(0,0,0,0.55) 78%, rgba(0,0,0,0.9) 100%);}
#brand{position:absolute;top:26px;left:32px;font-size:11px;letter-spacing:.42em;color:rgba(180,205,255,.55);text-transform:uppercase}
#nameWrap{position:absolute;left:0;right:0;bottom:11%;text-align:center;opacity:0;will-change:opacity}
#pname{font-size:clamp(26px,5.4vw,64px);letter-spacing:.30em;text-transform:uppercase;color:#fff;
  text-shadow:0 0 18px rgba(140,190,255,.7), 0 0 60px rgba(80,140,255,.45);font-weight:300;padding-left:.30em}
#psub{margin-top:14px;font-size:clamp(10px,1.35vw,14px);letter-spacing:.34em;text-transform:uppercase;color:rgba(190,215,255,.75);padding-left:.34em}
```
Note: letter-spacing adds trailing space; padding-left compensates for centering. Fine.

Set the wrap's opacity from JS.

Now, the code order matters: I'll write a single module script.

Let me write the whole thing now, carefully.

```js
import * as THREE from 'three';

/* ---------- helpers ---------- */
const TAU = Math.PI * 2;
const clamp = (v,a,b)=>Math.min(b,Math.max(a,v));
const smoothstep = (a,b,x)=>{ const t=clamp((x-a)/(b-a),0,1); return t*t*(3-2*t); };
function rand(seed){ let a=seed>>>0; return function(){ a=(a+0x6D2B79F5)|0; let t=Math.imul(a^(a>>>15),1|a); t=(t+Math.imul(t^(t>>>7),61|t))^t; return ((t^(t>>>14))>>>0)/4294967296; }; }

/* ---------- renderer ---------- */
const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(window.devicePixelRatio||1, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.15;
document.getElementById('c').appendChild(renderer.domElement);
```
Wait, if #c is a div with position fixed inset 0, appending the canvas there works. Or append to body. Let's use `document.body.appendChild(renderer.domElement)` and style the canvas via CSS (`canvas{display:block;position:fixed;inset:0}`). Simple.

Let me finalize the structure of the file.

Regarding the max anisotropy: 
```js
const MAXA = renderer.capabilities.getMaxAnisotropy();
```
and pass it into makeTexture via a closure variable.

Let me write out all the texture functions.

I'll write `makeTexture(w, h, drawFn)` which returns a CanvasTexture with aniso.

Now writing the final code. Let me be careful with syntax.

Additional detail — the ring geometry orientation. RingGeometry is in the XY plane. To lay it in the XZ plane (horizontal), rotate the mesh by -PI/2 about X: `ringMesh.rotation.x = -Math.PI/2`. Then the ring's "u" (radial) direction maps correctly. And it's inside tiltGroup which has rotation.z = tilt, so the ring plane gets tilted. Good.

Saturn's tilt: 26.7° = 0.466 rad on Z. Earth's 23.4° = 0.409 rad. Uranus 97.8° = 1.707 rad (extreme, will show the rings... Uranus has faint rings, we can skip them; the tilt is a nice detail — with tilt 1.7 rad the rotation axis is nearly in the orbital plane, which looks odd but is correct). Maybe use a milder 0.9 rad for visual appeal? Let's use the real 1.707 — actually it might look broken (the sphere's poles are sideways, which is correct for Uranus). Fine, keep it. Hmm, but then its bands appear as vertical stripes rather than horizontal — which is actually correct for Uranus! Nice.

Now writing the planet data with textures created eagerly.

```js
const planetDefs = [
  { name:'Mercury', r:0.84, dist:18, speed:0.440, spin:0.20, tilt:0.001, phase:0.6, cam:3.6, camY:0.18,
    sub:'Closest to the Sun · 88-day year', tex: texMercury() },
  { name:'Venus',   r:1.32, dist:24, speed:0.280, spin:0.08, tilt:0.05, phase:2.2, cam:5.4, camY:0.16,
    sub:'Thick clouds of sulphuric acid', tex: texVenus() },
  { name:'Earth',   r:1.35, dist:31, speed:0.210, spin:0.60, tilt:0.409, phase:4.1, cam:7.2, camY:0.20,
    sub:'The blue marble · one moon', tex: texEarth() },
  { name:'Mars',    r:0.98, dist:39, speed:0.150, spin:0.55, tilt:0.44, phase:5.4, cam:4.4, camY:0.18,
    sub:'The red planet · polar ice caps', tex: texMars() },
  { name:'Jupiter', r:4.52, dist:60, speed:0.062, spin:1.0, tilt:0.05, phase:1.2, cam:18.5, camY:0.16,
    sub:'Largest planet · the Great Red Spot', tex: texJupiter() },
  { name:'Saturn',  r:4.15, dist:80, speed:0.040, spin:0.9, tilt:0.466, phase:3.3, cam:26.5, camY:0.30, rings:true,
    sub:'Jewel of the Solar System · its rings', tex: texSaturn() },
  { name:'Uranus',  r:2.70, dist:100, speed:0.024, spin:0.6, tilt:1.70, phase:5.7, cam:12.0, camY:0.18,
    sub:'Tilted ice giant · 84-year orbit', tex: texUranus() },
  { name:'Neptune', r:2.66, dist:118, speed:0.017, spin:0.6, tilt:0.49, phase:2.7, cam:11.5, camY:0.18,
    sub:'Farthest planet · supersonic winds', tex: texNeptune() },
];
```

Camera offsets: `cam` is the distance. Direction: normalize(0.78, camY, 0.62) * cam... wait, if I normalize then multiply by cam, the y component becomes cam*0.18/|v| which is small. Let me just do: dir = new Vector3(0.72, camY, 0.58).normalize? Hmm, simpler: off = new Vector3(cam*0.62, cam*camY, cam*0.50). Then |off| = cam*sqrt(0.3844+0.0324+0.25) ≈ cam*0.817. So the actual distance is 0.82*cam. For Saturn with cam 26.5 → 21.7. Ring radius 4.15*2.3 = 9.5 → angular radius atan(9.5/21.7)=23.6° vs half-FOV 25°. Tight. Let's make Saturn's cam 32 to be safe.

Actually let me reconsider: with the offset direction having a Y component, the distance is 0.817*cam. For Jupiter: 0.817*18.5 = 15.1; angular radius atan(4.52/15.1) = 16.6°. Half-FOV (vertical) = 25° → Jupiter fills 66% of the half-height. Good.

Mercury: 0.817*3.6 = 2.94; radius 0.84 → atan(0.84/2.94)=16°. Good, similar size on screen for all planets. Slightly bigger than Jupiter's. Fine.

Saturn cam 32 → distance 26.1; ring 9.5 → atan(9.5/26.1) = 20°. Fits within 25°. Good. Planet radius 4.15 → 9°.

Uranus cam 12 → 9.8 distance; r 2.7 → 15.4°. Good.
Neptune cam 11.5 → 9.4; r 2.66 → 15.8°. Good.
Earth cam 7.2 → 5.9; r 1.35 → 12.9°. Moon at radius 3.7 (orbit) → the moon is at 3.7 from Earth, camera distance 5.9 → the moon can be up to 22° off-axis... plus the moon's own size. It might sometimes be outside the frame. When the moon is behind the Earth or to the side, we see it. Let's reduce the moon's orbit radius to 3.0 and increase Earth's cam to 8.5 → distance 6.9. Moon at 3.0 → max angular offset from Earth = atan(3/6.9) = 23.5°, within the vertical half-FOV of 25° but near the edge; horizontally it's fine (aspect > 1). Acceptable. Actually with the camera looking at the Earth's center, the moon at 23° off-axis is near the frame edge but visible. Let's use moon orbit radius 2.8 and Earth cam 8.5.

Hmm, but the moon's size: 0.37 radius at 6.9 distance = 3°. Small but visible as a dot. Good.

The Sun's wide shot: off = (0, 190, 340). I'll define it separately.

Now the code for building planets:

```js
const planetObjects = [];
const orbitGroup = new THREE.Group(); // not needed
for(const def of planetDefs){
  const group = new THREE.Group();
  scene.add(group);
  const tiltGroup = new THREE.Group();
  tiltGroup.rotation.z = def.tilt;
  group.add(tiltGroup);
  const mesh = new THREE.Mesh(new THREE.SphereGeometry(def.r, 48, 32), new THREE.MeshStandardMaterial({map:def.tex, roughness:0.88, metalness:0.02}));
  tiltGroup.add(mesh);
  const obj = {def, group, mesh};
  if(def.rings){ ... }
  if(def.name==='Earth'){ ... }
  planetObjects.push(obj);
  // orbit line
  ...
}
```

For Saturn's rings:
```js
const inner = def.r*1.28, outer = def.r*2.32;
const rg = new THREE.RingGeometry(inner, outer, 160, 1);
const pos = rg.attributes.position, uv = rg.attributes.uv;
const v = new THREE.Vector3();
for(let i=0;i<pos.count;i++){ v.fromBufferAttribute(pos,i); const d=v.length(); uv.setXY(i, (d-inner)/(outer-inner), 0.5); }
uv.needsUpdate = true;
const rings = new THREE.Mesh(rg, new THREE.MeshBasicMaterial({map:ringTex, transparent:true, side:THREE.DoubleSide, depthWrite:false, opacity:0.95, toneMapped:false? }));
```
Hmm, toneMapped: for MeshBasicMaterial with a texture, tone mapping is applied by default. With ACES, the rings will look slightly desaturated/dimmed. Let's keep toneMapped true for consistency with the planet's lighting? The rings are unlit basic material; with ACES the tan color becomes slightly grayer. It's fine either way. I'll leave tone mapping on (default true) for a slightly filmic look... Actually the rings would look brighter than the lit planet if toneMapped=false. Keep default.

rings.rotation.x = -Math.PI/2; tiltGroup.add(rings);

Note: RingGeometry's default UV mapping is replaced, so the texture's alpha varies radially. 

Also note: `side: THREE.DoubleSide` + `transparent: true` + `depthWrite: false`. Since the rings are a flat plane, sorting issues are minimal.

Now the Earth's moon:
```js
if(def.name==='Earth'){
  const mTilt = new THREE.Group(); mTilt.rotation.z = 0.09; group.add(mTilt);
  const pivot = new THREE.Group(); mTilt.add(pivot);
  const moon = new THREE.Mesh(new THREE.SphereGeometry(0.37, 32, 24), new THREE.MeshStandardMaterial({map: moonTex, roughness:0.95}));
  moon.position.set(2.9, 0, 0);
  pivot.add(moon);
  obj.moonPivot = pivot;
}
```
Wait, but `group` also holds tiltGroup with the Earth. The moon pivot is a sibling of tiltGroup inside the group, so the moon isn't affected by Earth's axial tilt. Correct.

Orbit lines:
```js
const pts=[];
for(let i=0;i<=180;i++){const a=i/180*TAU; pts.push(new THREE.Vector3(Math.cos(a)*def.dist, 0, Math.sin(a)*def.dist));}
const lineGeo = new THREE.BufferGeometry().setFromPoints(pts);
const line = new THREE.Line(lineGeo, new THREE.LineBasicMaterial({color:0x4a6fa5, transparent:true, opacity:0.18, depthWrite:false}));
scene.add(line);
```
Hmm, orbit lines with depthWrite false will be drawn over/under things inconsistently, but they're faint. Keep depthWrite true actually so they're properly occluded. With transparent:true, they're in the transparent pass and don't write depth by default? Material.depthWrite defaults to true, and transparent materials still write depth unless set otherwise. Fine, leave the default.

Now, the sun group: it's the target for key 0, at the origin. I'll use `sunGroup` directly and its position stays (0,0,0).

Let me write the tour keys:

```js
const SUN_WIDE = new THREE.Vector3(0, 200, 350);
const tourKeys = [
  {label:'The Solar System', sub:'Eight planets, one star', target: sunGroup, off: SUN_WIDE, drift:0, dur:3.2},
];
for(const obj of planetObjects){
  const d = obj.def;
  const off = new THREE.Vector3(d.cam*0.62, d.cam*d.camY, d.cam*0.50);
  tourKeys.push({label:d.name, sub:d.sub, target:obj.group, off, drift:0.07, dur: DURATIONS[d.name]});
}
```
Durations per name — let me store dur in the def instead.

Mercury 2.9, Venus 2.9, Earth 3.8, Mars 2.9, Jupiter 3.5, Saturn 3.8, Uranus 2.9, Neptune 3.2.
Sum: 3.2+2.9+2.9+3.8+2.9+3.5+3.8+2.9+3.2 = 29.1. 

Hmm, Neptune's transition back to the overview takes 35% of 3.2 = 1.12s, starting at 27.98s. So the whole tour completes at 29.1s. Within 30s. 

Let's double-check the label timings: the label fades in over 10% of the segment duration. For Mercury (2.9s), 0.29s. Good.

Now the loop: TOUR_TOTAL = 29.1.

Now the camera offset rotation drift: `off.clone().applyAxisAngle(new THREE.Vector3(0,1,0), time*key.drift)`.

For the wide shot, drift 0.

Let me now also double check the "blend window": smoothstep(0.62, 1.0, p). So the transition takes 38% of the segment. For Neptune: 1.2s. For the 3.8s segments: 1.44s. Good.

The hold time on each planet: 62% of the segment. Mercury: 1.8s. Earth: 2.36s. Good.

Another thought: during the transition, the camera flies in a straight line (lerp) between two positions. Fine.

Now let's write the render loop:

```js
const clockStart = performance.now(); // fallback
let t0 = null;
let lastKey = -1;
const tmpVecA = new THREE.Vector3(), tmpVecB = new THREE.Vector3(), tmpLook = new THREE.Vector3();
const YAXIS = new THREE.Vector3(0,1,0);

function frame(ts){
  requestAnimationFrame(frame);
  if(t0===null) t0 = ts;
  const time = (ts - t0) * 0.001;

  // planets
  for(const o of planetObjects){
    const d=o.def;
    const a = d.phase + time*d.speed;
    o.group.position.set(Math.cos(a)*d.dist, 0, Math.sin(a)*d.dist);
    o.mesh.rotation.y = d.phase*3 + time*d.spin;
    if(o.moonPivot) o.moonPivot.rotation.y = time*0.6;
  }
  sunMesh.rotation.y = time*0.02;

  // tour
  const lt = time % TOUR_TOTAL;
  let acc=0, ki=0;
  while(ki < tourKeys.length-1 && lt >= acc + tourKeys[ki].dur){ acc += tourKeys[ki].dur; ki++; }
  const key = tourKeys[ki];
  const nxt = tourKeys[(ki+1)%tourKeys.length];
  const p = clamp((lt-acc)/key.dur, 0, 1);
  const blend = smoothstep(0.62, 1.0, p);

  tmpVecA.copy(key.off).applyAxisAngle(YAXIS, time*key.drift).add(key.target.position);
  tmpVecB.copy(nxt.off).applyAxisAngle(YAXIS, time*nxt.drift).add(nxt.target.position);
  camera.position.lerpVectors(tmpVecA, tmpVecB, blend);
  tmpLook.lerpVectors(key.target.position, nxt.target.position, blend);
  camera.lookAt(tmpLook);
  ...
}
```

Hmm wait — `tmpLook.lerpVectors(key.target.position, nxt.target.position, blend)` — this sets tmpLook each frame (lerpVectors sets it fully). Good, no stale state.

Careful with the while loop: if lt >= acc+dur for the last key, ki stays at length-1. Since lt < TOUR_TOTAL always, the last key's range is covered. But the while condition `ki < length-1` prevents overflow. Good.

Label:
```js
  if(ki !== lastKey){
    lastKey = ki;
    nameEl.textContent = key.label;
    subEl.textContent = key.sub;
  }
  const op = smoothstep(0.0, 0.10, p) * (1 - smoothstep(0.60, 0.92, p));
  nameWrap.style.opacity = op.toFixed(3);
```
Hmm, at p between 0.62 and 1.0 the camera is transitioning, and the label fades out from 0.60 to 0.92. Good.

But careful: when ki changes at the loop boundary (ki=0), the label updates to "The Solar System". Good.

Also, the initial frame: at ts of the first frame, time=0, lt=0, p=0, opacity 0 → the label fades in. Good.

Now the sun's glow sprite scale in world units: set as constant. Good.

One more consideration: with the camera close to Mercury at ~2.9 units from its center, and the sun 18 units away, the camera's near plane 0.3 is fine. But could the camera clip into the planet? The camera distance from the planet surface is 2.9-0.84 = 2.06. Fine.

Another: during the transition from Jupiter to Saturn (18.5→32 cam), the camera passes through the region between them — no collisions since the planets are far apart.

But the transition from Mars (39) to Jupiter (60) — the camera flies from Mars's vicinity to Jupiter's, crossing the asteroid belt region (nothing there). Fine.

Potential issue: the camera might pass through the Sun during a long transition (e.g., from Venus to Earth if they're on opposite sides). The straight-line path from one planet to the next could pass close to the sun (if the sun is between them). The camera might fly into the sun (radius 4.6). That would look like a white flash. Possible but it's a cinematic "sun transit" — could be cool or ugly. To mitigate, I could add a mid-transition arc: use a quadratic path that bulges outward from the sun. Let's do a simple mitigation: interpolate the camera position in "orbital-polar" terms? Simpler: after lerping, add an upward bulge: camPos.y += sin(blend*PI) * bulgeAmount where bulgeAmount is proportional to the distance between the two camera positions (e.g., 0.12 * distance). This also makes transitions feel more like a graceful arc rather than a straight line. Let's do that: 

```js
const arc = Math.sin(Math.PI*blend) * tmpVecA.distanceTo(tmpVecB) * 0.10;
camera.position.y += arc;
```
Since blend goes 0→1 monotonically during the transition (and is 0 during the hold, and 1 at the end... wait, at the end of the segment blend=1, sin(PI)=0. Good.)

That adds a nice arc and helps avoid the sun (going up). Also the path from Neptune to the wide shot gets an arc — fine.

But careful: the arc could push the camera through the planet... no, it goes up.

Also, an arc when the two camera positions are already far apart gives a large y offset (e.g., 200 units apart → 20 units up). Fine.

Let's keep it.

Now the star sprite texture and point clouds.

```js
function texStar(){
  const c=document.createElement('canvas'); c.width=c.height=64;
  const x=c.getContext('2d');
  const g=x.createRadialGradient(32,32,0,32,32,32);
  g.addColorStop(0,'rgba(255,255,255,1)');
  g.addColorStop(0.25,'rgba(255,255,255,0.85)');
  g.addColorStop(0.55,'rgba(180,210,255,0.25)');
  g.addColorStop(1,'rgba(120,170,255,0)');
  x.fillStyle=g; x.fillRect(0,0,64,64);
  const t=new THREE.CanvasTexture(c); t.colorSpace=THREE.SRGBColorSpace; return t;
}
```

Stars:
```js
function makeStarLayer(count, size, rMin, rMax, opacity){
  const positions=new Float32Array(count*3);
  const colors=new Float32Array(count*3);
  const rnd=rand(count*7+1);
  const col=new THREE.Color();
  for(let i=0;i<count;i++){
    // random point on sphere shell
    const u=rnd()*2-1, th=rnd()*TAU, s=Math.sqrt(1-u*u);
    const r=rMin + rnd()*(rMax-rMin);
    positions[i*3]=Math.cos(th)*s*r;
    positions[i*3+1]=u*r;
    positions[i*3+2]=Math.sin(th)*s*r;
    const t=rnd();
    if(t<0.6) col.setHSL(0.58, 0.15+rnd()*0.3, 0.75+rnd()*0.25);      // blue-white
    else if(t<0.85) col.setHSL(0.10, 0.25+rnd()*0.3, 0.72+rnd()*0.25); // warm
    else col.setHSL(0.0, 0.0, 0.85+rnd()*0.15);
    colors[i*3]=col.r; colors[i*3+1]=col.g; colors[i*3+2]=col.b;
  }
  ...
}
```
Careful: `col.setHSL` with colorSpace... In r152+, setHSL takes an optional colorSpace argument defaulting to SRGB? Actually `setHSL(h,s,l, colorSpace = SRGBColorSpace)` — hmm, in recent versions, Color.setHSL signature is (h, s, l, colorSpace = ColorManagement.workingColorSpace). Since three r152, the default is working color space (linear). Whatever — it's fine for stars.

Then geometry with attributes, and PointsMaterial.

Star sizes: layer1: 3000 stars, size 1.6, shell 1400-2800, opacity 0.75. layer2: 500 stars, size 3.0, shell 1200-2600, opacity 1.

Hmm, with sizeAttenuation false, the size is in pixels regardless of distance. Good.

Note: with `map` + additive blending + alphaTest... For PointsMaterial, the map is applied with the point's UV (the point sprite covers the full quad). Fine.

Now, does the far plane matter? Camera far 8000 > 2800. OK.

Let me write the final render/loop and initialization.

One more: the "cinematic" feel could use a slight camera FOV shake or handheld noise — skip; keep it clean.

Let's also ensure the planets are all "important within 30s" — yes.

Writing the final code now.

Also, add `<div id="loading">`? Not needed since everything is procedural and immediate.

Let me write out the entire file.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Solar System — Cinematic Tour</title>
<style>
  html,body{margin:0;height:100%;overflow:hidden;background:#000;
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
  canvas{display:block;position:fixed;inset:0;}
  #ui{position:fixed;inset:0;pointer-events:none;}
  #vignette{position:absolute;inset:0;
    background:radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 30%, rgba(0,0,0,.45) 72%, rgba(0,0,0,.92) 100%);}
  #brand{position:absolute;top:24px;left:30px;font-size:11px;letter-spacing:.42em;
    text-transform:uppercase;color:rgba(170,200,255,.5);}
  #nameWrap{position:absolute;left:0;right:0;bottom:11%;text-align:center;opacity:0;}
  #pname{font-size:clamp(26px,5.2vw,62px);font-weight:300;letter-spacing:.3em;padding-left:.3em;
    text-transform:uppercase;color:#fff;text-shadow:0 0 22px rgba(140,190,255,.75),0 0 70px rgba(70,130,255,.5);}
  #psub{margin-top:14px;font-size:clamp(10px,1.3vw,13px);letter-spacing:.34em;padding-left:.34em;
    text-transform:uppercase;color:rgba(185,210,255,.7);}
</style>
</head>
<body>
<div id="ui">
  <div id="vignette"></div>
  <div id="brand">The Solar System · A Cinematic Tour</div>
  <div id="nameWrap"><div id="pname"></div><div id="psub"></div></div>
</div>
<script type="importmap">
...
```
Wait — the prompt says an import map is provided; do not add my own. So I must NOT include an importmap in my file. Just use `import * as THREE from 'three'`. OK, no import map.

Hmm, but then would the bare specifier 'three' resolve? The environment provides the import map. Yes, trust it.

Now let me write the script.

I need to double check `renderer.outputColorSpace` — default is SRGB in r186. Good.

Let me write it all out now, and be careful about the order of definitions (functions hoisted, but `const` textures are not). I'll define all the texture functions first (function declarations are hoisted), then the renderer, then create textures, then meshes, then the tour, then the loop.

Note: `texMercury()` etc. use `makeTexture` which uses `MAXA` — I need MAXA defined before calling them. I'll declare `let MAXA = 4;` at the top and set it after creating the renderer.

Let me write the code:

```js
import * as THREE from 'three';

const TAU = Math.PI * 2;
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const smoothstep = (a, b, x) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
function rand(seed) { let a = seed >>> 0; return function () { a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

/* ---------- renderer / scene / camera ---------- */
const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.15;
document.body.appendChild(renderer.domElement);
const MAXA = renderer.capabilities.getMaxAnisotropy();

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.3, 9000);
camera.position.set(0, 200, 350);

/* ---------- procedural textures ---------- */
function makeTexture(w, h, draw) { ... }
function blob(...) {...}
...
```

Then lights, sun, planets, stars, tour, loop.

Let me write all the texture code carefully.

I'll write `blob` to accept (ctx, w, h, x, y, r, rgb, a).

For the crater helper, also wrap.

```js
function craterPatch(ctx, w, h, x, y, r, rnd) {
  for (const dx of [-w, 0, w]) {
    const cx = x + dx;
    if (cx < -r || cx > w + r) continue;
    ctx.globalAlpha = 0.25 + rnd() * 0.3;
    ctx.fillStyle = '#3d3d40';
    ctx.beginPath(); ctx.arc(cx, y, r, 0, TAU); ctx.fill();
    ctx.globalAlpha = 0.30;
    ctx.strokeStyle = '#e8e8e8';
    ctx.lineWidth = Math.max(1, r * 0.16);
    ctx.beginPath(); ctx.arc(cx - r * 0.1, y - r * 0.1, r * 0.88, 0, TAU); ctx.stroke();
    if (r > 5) {
      ctx.globalAlpha = 0.18;
      ctx.fillStyle = '#ffffff';
      ctx.beginPath(); ctx.arc(cx - r * 0.25, y - r * 0.25, r * 0.35, 0, TAU); ctx.fill();
    }
  }
  ctx.globalAlpha = 1;
}
```

OK. Now let me write everything in final form. I'll be thorough.

Also, I should double check `THREE.RingGeometry(inner, outer, thetaSegments, phiSegments)` – parameters: (innerRadius, outerRadius, thetaSegments, phiSegments, thetaStart, thetaLength). The vertex layout: for iy in 0..phiSegments, for ix in 0..thetaSegments → positions. UV computed as (ix/thetaSegments, iy/phiSegments) roughly. My custom UV assignment overrides that. Good.

One concern: with phiSegments=1, there are only 2 radial rings, so the geometry is a single quad strip radially — the texture radius mapping is linear per vertex, which is fine since the interpolation is linear in radius. Good.

Now regarding the ring's appearance in the distance: fine.

Let me also add a subtle "atmosphere" glow for Earth? A slightly larger transparent sphere with a backside additive material. Nice touch but adds complexity. Maybe a simple one for Earth: a sphere of radius r*1.03 with MeshBasicMaterial color 0x4488ff, transparent, opacity 0.12, side: BackSide? Hmm, that could look muddy. Skip. Actually a "rim glow" via a sprite behind the planet is a classic cheap trick: skip. Keep it clean.

Now let me write the final file.

For the sun, also add `sunMesh.material.color` — the texture is already orange. Fine.

Let me now consider the sun's glow sprite: `new THREE.Sprite(new THREE.SpriteMaterial({map: glowTex, color: 0xffddaa, blending: THREE.AdditiveBlending, transparent:true, depthWrite:false, depthTest:true, toneMapped:false}))`. Note SpriteMaterial supports toneMapped? Material has toneMapped, so yes.

Wait, one thing: sprites in three render with `fog` etc. Fine.

Also, the glow sprites scale: `sprite.scale.set(s, s, 1)`.

Now, the sun's size relative to the camera: in the wide shot at distance ~400, the sun (radius 4.6) has an angular radius of 0.66° — a small but bright dot with a nice halo (the outer glow at 26x = 120 units → 17° angular diameter... that's a big glow ~ 8.6° radius). Hmm, that might be too much. Let's use scales: core 6x = 27.6 units (4° diameter at 400 → visible), mid 14x, outer 30x with low opacity (0.12). The outermost would be 138 units → 20° diameter. With opacity 0.12 and additive, it's a faint haze. Acceptable and cinematic. But at close range (Mercury's camera at ~2.9 from Mercury, sun 18 away), the glow with 30x = 138 units would engulf the entire view in haze! That's bad.

Solution: make the glow scale constant in world units but not too large, or use distance-based scaling. Let's use core 6x=27.6, mid 11x=50, and skip the huge one. At Mercury's close-up (18 units from the sun), a 50-unit sprite fills the view... Additive with opacity 0.4 at the center → the center of the sprite is bright. Since the sun is 18 units away and the sprite is 50 units across, the sprite would cover a huge part of the screen. Hmm, that's a problem for inner planets.

Mitigation: reduce the glow sizes: core 5x = 23 units, mid 8x = 37 units. At 18 units distance, a 37-unit sprite spans atan(18.5/18)=45° → fills most of the frame vertically. Ugh.

Alternative: the glow's brightness falls off sharply (the gradient is mostly transparent beyond 0.3 of the radius), so the visible glow is about 0.35 of the sprite's radius. With the gradient stops: 0→1, 0.2→0.55, 0.4→0.18, 0.7→0.04, 1→0. So the visible portion is roughly the inner 40%. So a 37-unit sprite shows a ~15-unit glow. That's more reasonable.

Let's define the glow texture with a fast falloff and use scales: core = sunRadius*4.5 (20.7), mid = sunRadius*9 (41.4) with color 0xffaa33 and opacity 1 (additive, but the gradient is faint at the edges).

I think that's fine. The inner planets' shots will have a bright sun backdrop — dramatic and pretty.

Actually wait, there's another consideration: for the Mercury close-up, the camera is at 2.9 units from Mercury's center and the sun is 18 units away in some direction. If Mercury is between the camera and the sun, we get a partially lit Mercury with the sun behind — beautiful. If the sun is behind the camera, we see a fully lit Mercury. Both fine.

OK, let's go.

One more: should the sun light cast shadows? No.

Finally, let me think about whether `camera.lookAt` with a moving target and lerped positions produces smooth motion. Yes.

Potential jitter: the drift rotation `time*key.drift` uses absolute time — smooth.

Let me also double check the transition blend for key i when p is in [0.62, 1]: blend goes 0→1 smoothly (smoothstep has zero derivative at both ends). Good.

Now write the final code.

Final detail: the initial camera before the first frame — set to the wide shot at (0,200,350). Fine.

Also, should I use `renderer.setAnimationLoop`? The requirement says use requestAnimationFrame with the timestamp. I'll use requestAnimationFrame directly.

Writing the code now in full.

```js
/* ---- textures ---- */
function makeTexture(w, h, draw) {
  const cv = document.createElement('canvas');
  cv.width = w; cv.height = h;
  const ctx = cv.getContext('2d');
  draw(ctx, w, h);
  const t = new THREE.CanvasTexture(cv);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = MAXA;
  t.wrapS = THREE.RepeatWrapping;
  t.needsUpdate = true;
  return t;
}
```

Careful: `t.anisotropy = MAXA` — MAXA could be 16. Fine.

blob:
```js
function blob(ctx, w, h, x, y, r, rgb, a) {
  for (let k = -1; k <= 1; k++) {
    const cx = x + k * w;
    if (cx < -r || cx > w + r) continue;
    const g = ctx.createRadialGradient(cx, y, 0, cx, y, r);
    g.addColorStop(0, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${a})`);
    g.addColorStop(1, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},0)`);
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.arc(cx, y, r, 0, TAU); ctx.fill();
  }
}
```

Now the texture functions. I'll write them all.

For Jupiter's band loop with y+=2, note that h=512 so 256 stripes. Fine.

Also for the turbulence ellipses in Jupiter, I need to guard against throwing when ww is large — fine.

Let me write out the code for real now. I'll produce the final answer.

Regarding performance: 1024x512 canvas textures × 9 (8 planets + sun) + moon + ring = fine.

One more consideration on the Earth texture: `blob(ctx,w,h,x,y,r,[60,120,60],0.85)` — with r up to 85 and the radial gradient soft edge, continents will look like soft blobs. Adding a second smaller blob with a lighter green gives some structure. It'll look like an abstract Earth. Acceptable.

To make the continents look more like landmasses, I could draw the blobs with a harder edge (alpha 0.95 at center, falling off only in the last 30%). Let me modify: add a color stop at 0.65 with the full alpha, then fade to 0 at 1. I'll add a parameter `hard` to blob? Let me create a second helper `landBlob` with stops (0, a), (0.7, a*0.9), (1, 0). That gives more defined edges. I'll just make `blob` use stops (0,a),(0.6,a*0.85),(1,0) — that changes all blobs to be more defined. Hmm, for the sun's granules a soft falloff is better. Let me add an optional parameter `sharp` defaulting to 0.55:

```js
function blob(ctx,w,h,x,y,r,rgb,a,sharp=0.55){
  ...
  g.addColorStop(0, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${a})`);
  g.addColorStop(sharp, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${a*0.75})`);
  g.addColorStop(1, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},0)`);
}
```
With sharp=0.55, the blob is fairly soft. For continents I'll pass sharp=0.75 and alpha 0.9.

OK. Writing now. I'll aim for clean, working code.

Let me write the whole script section.

```js
/* ============ SUN ============ */
const sunRadius = 4.6;
const sunGroup = new THREE.Group();
scene.add(sunGroup);
const sunMesh = new THREE.Mesh(
  new THREE.SphereGeometry(sunRadius, 64, 48),
  new THREE.MeshBasicMaterial({ map: texSun(), toneMapped: false })
);
sunGroup.add(sunMesh);

const glowTex = texGlow();
const glowSpecs = [
  { s: 4.2, c: 0xfff0c0, o: 0.95 },
  { s: 8.5, c: 0xffae4d, o: 0.55 },
  { s: 16.0, c: 0xff7b1a, o: 0.22 }
];
for (const gs of glowSpecs) {
  const m = new THREE.SpriteMaterial({ map: glowTex, color: gs.c, transparent: true, opacity: gs.o, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false });
  const sp = new THREE.Sprite(m);
  sp.scale.set(sunRadius * gs.s, sunRadius * gs.s, 1);
  sunGroup.add(sp);
}
```
Hmm, the outermost is 16*4.6 = 73.6 units across (radius 36.8). With the falloff, the visible haze is ~15 units at 0.2 opacity. Fine.

Lights:
```js
const sunLight = new THREE.PointLight(0xfff2d8, 3.6, 0, 0);
sunGroup.add(sunLight);
scene.add(new THREE.AmbientLight(0x2b3f6e, 1.1));
```
Hmm, AmbientLight intensity in the new system: `irradiance = ambientColor * intensity`? Actually, WebGLLights: `state.ambient[0] += color.r * intensity` — hmm, for ambient: `const r = color.r * intensity;` yes. Then diffuse = irradiance * albedo/π. So with intensity 1.1 and color (0.17,0.25,0.43) → irradiance ~0.2-0.47 → albedo/π * that ≈ 0.06-0.15 on the dark side. Reasonable — a faint blue fill.

OK.

Now the planets loop, orbit lines, moon, rings.

Then stars.

Then tour.

Then animate.

I think I'm ready to write it out. Let me produce the final file.

One last check on the label element opacity: I set `nameWrap.style.opacity = op`. The div has `opacity:0` initially in CSS. Good.

Also add a slight vertical parallax? No.

Writing the answer now.

Wait, one more thought on the tour: `time % TOUR_TOTAL` — using absolute `time` also drives the planet positions, which is correct.

And for the camera drift, using absolute `time` in the rotation angle means the drift angle grows unbounded; over minutes it's fine (float precision ok).

Final: writing.

Also I should double-check that `key.target.position` for the sun group is (0,0,0) — yes.

Let me also make sure that `tourKeys` includes the sun group as target with the off vector, and that `tmpVecA` for the sun uses `key.off` = SUN_WIDE. Good.

Let me write out the file.