Create a single HTML file containing an import map (provided? "import map is provided" — but do we need to include it in the file? It says "don't add your own import map or CDN URLs". So the environment provides the import map, and all we need to use is `import * as THREE from 'three'`). OK.

Build the scene: dark background, fog (THREE.FogExp2), a group of buildings with window textures generated via canvas, neon signs (emissive planes/boxes), a wet reflective street — use a simple MeshStandardMaterial with high metalness and low roughness, or a Reflector? Simpler: a dark street with high metalness and some fake "reflection" — we could also use the Reflector addon, but that doubles rendering cost. Simpler: a dark glossy street, and maybe add a few emissive "wet streak" planes. That's good enough.

Flying cars: small emissive box geometries moving along a CatmullRomCurve3 path.

Bloom: EffectComposer, RenderPass, UnrealBloomPass.

Camera path: a CatmullRomCurve3 that goes through the city, position = curve.getPoint(t), lookAt is a point slightly ahead.

Window texture: create a canvas texture with a grid of lit/unlit windows, emissiveMap.

Let's write the code.

Details:
- scene.fog = new THREE.FogExp2(0x0a0a18, 0.008);
- Buildings: about 300, random heights, placed in a grid with jitter, avoiding the central street path? Keep a corridor near the x-axis clear for the camera path. Camera path: a curve meandering through the city.

Place buildings on a grid: positions x,z from -400 to 400, spacing ~40, skip if close to a path line. Simpler: skip buildings where |x| < 25 (main street) or |z|<25? The camera path meanders; define the curve and keep buildings away from it? Even simpler: clear a ring near the camera path by checking the minimum distance to the curve points — costly but one-shot is OK: sample the curve at 200 points, and skip building positions within 30 units.

Windows: generate a few canvas textures (4 variants), use as emissiveMap and map with the same canvas. Material: MeshLambertMaterial? Use MeshStandardMaterial with emissive white, emissiveMap is the texture, color is dark.

Neon signs: thin BoxGeometry or PlaneGeometry with an emissive color, randomly pink (0xff2d95), cyan (0x00e5ff), purple (0x9d4edd). Some are vertical strips on building sides, some are "billboards" at random heights.

Cars: about 12, each with its own curve (CatmullRomCurve3, closed, at a random altitude), moving at a random speed. Cars are small box + emissive light trails (thin plane or a second box). Use a bright emissive color.

Street: a large plane with color 0x05050a, metalness 0.9, roughness 0.15, but the environment is needed to make the reflection look nice. With bloom and a dark environment, a metal plane might just go black. Add a big dark hemisphere environment? Or MeshPhongMaterial with envMap? Simplest: the street is a dark material with some opacity, and we rely on the building emissives + fog. To fake wet reflections, we can add a second "mirror" plane: duplicate the buildings and flip them with low opacity? That's a decent trick: a reflection group = buildings.clone, y scale -1, opacity 0.25, transparent, render order, depthWrite false. But the windows are emissive — a clone of the same material will also be emissive. Might look good. But memory/geometry cost: 300 buildings is fine.

Alternative: use the Reflector addon: 'three/addons/objects/Reflector.js'. That gives true reflection, at the cost of a scene re-render. For a few hundred meshes, no problem. But the Reflector's texture is also affected by fog — no problem. Let's use a Reflector with color 0x050508 and a dark overlay? The Reflector is a mirror plane; to make it "wet", set textureMatrix, and color multiplies. Reflector's color darkens the reflection. It might look too mirror-like. Add a roughness trick? The Reflector is a perfect mirror. Acceptable as "wet and reflective." But when combined with bloom, the reflections will bloom too — good, like neon on a wet street.

But Reflector renders the scene from a mirrored camera — including the fog, no problem. Performance: an extra scene render; a few hundred boxes should be fine.

But the Reflector reflects the skybox/background too — the background is a dark color, so no problem.

Let's use the Reflector: `new Reflector(new THREE.PlaneGeometry(...), {clipBias: 0.003, textureWidth: 1024, textureHeight: 1024, color: 0x101018})`. To dim the reflection, set the Reflector material's color.

Hmm, a full-mirror street might look weird. A slightly rough look: we can overlay a dark semi-transparent plane on top of the Reflector to mute it, and add faint streaks. Let's put a slightly larger, 0x06060c, opacity 0.35, transparent dark plane 0.01 above the Reflector.

Cars should also be excluded from the Reflector? They will be reflected — no problem, actually good.

Camera path: define the curve points, e.g.:
```
const camPts = [
 new THREE.Vector3(-380, 60, 0),
 new THREE.Vector3(-200, 35, 40),
 new THREE.Vector3(-80, 90, -30),
 new THREE.Vector3(60, 40, 30),
 new THREE.Vector3(180, 110, -20),
 new THREE.Vector3(320, 50, 40),
 new THREE.Vector3(420, 80, 0),
];
```
A closed loop? A looping path (closed true) for continuous gliding. Then the camera position = curve.getPointAt(frac), and lookAt is a point slightly ahead (frac+0.02). Add a slight up/down bob using sin(time).

Buildings: for a grid, x from -420 to 420, step ~44, z similarly; random jitter; skip if near a curve point (distance < 34) — precompute 400 curve samples, and for each building candidate, quickly check all samples (400*~900 candidates = 360k distance checks, fine at startup).

Also skip the central crossroads: if |x|<18 || |z|<18, skip — keep the street wide.

Building: BoxGeometry(w, h, w), h 30 to 160, w/z 12-26.

Texture: function makeWindowTexture: 128x256 canvas, 8x32 window grid, each lit at random probability, color random from a dim set (white, warm, cyan tinge). Use as map and emissiveMap, emissiveIntensity ~1.2, color 0x0a0a12, emissive 0xffffff.

UV: box UVs map the texture per face; top face shows the texture weirdly — no problem.

Neon: for each building, with some probability, add a thin box: e.g., a vertical strip 1x h x 1 on a corner, or a horizontal sign. Emissive material with color, emissiveIntensity 2, plus a pointLight? Too many point lights would kill performance. Only a few point lights (8 or so) near the path for a local glow, plus a dim ambient, maybe also a directional.

Lights: ambient 0x111122 low, maybe a bluish moonlight directional.

Cars: each has its own closed CatmullRomCurve3 at altitude 15-120, 5-8 random points. Car group: body box (dark, small), light bar (thin emissive box, white or red), tail light. Orient along the tangent: car.lookAt(tangent) or use a matrix.

Speed: t += dt * speed; frac = (t)%1.

Cars should also avoid buildings? The curves are random — the cars might pass through buildings. Mitigation: keep car altitudes in a range and accept some clipping, or make the curves at a high altitude (60-160) with large radius — many buildings are shorter than 160, hmm. Alternative: constrain car curve points to be far from buildings? Simpler: cars are "few", e.g., 6, altitudes 40-140, wide loops; occasional intersection is acceptable for this demo, but might look bad. Can we quickly check each car curve sample point against building boxes? 6 cars × 100 samples × 900 buildings = 540k AABB checks, fine at startup. If a car intersects, we can nudge the altitude up. Simpler: sample each car curve at 100 points; for each sample, check each building's AABB (expanded by 3); if it hits, raise the car altitude by 10 and rebuild the curve, up to a max of a few attempts, with a cap. Actually simplest: after a collision, shift all points up by (hit building height + 8). Let's do this: build the curve, and for each car, test samples; if a collision, move all y up by 15 and rebuild, up to 10 times, with a cap. Good.

Fog: FogExp2 color 0x070714 density 0.006.

Renderer: setPixelRatio min(devicePixelRatio,2), outputColorSpace default.

Composer: RenderPass + UnrealBloomPass(strength 1.2, radius 0.6, threshold 0.15) + OutputPass (r186 includes OutputPass; needed for correct color). import { OutputPass } from 'three/addons/postprocessing/OutputPass.js'.

Animation: clock time from the rAF timestamp: use `function animate(time)` with time in ms; t = time*0.001.

Camera lookAt: to avoid jitter, use a smoothed look target: lerp the look target.

Resize: update camera aspect, renderer, composer, bloom resolution.

Sky: scene.background = a dark color with a slight gradient — a big sphere? Just a color 0x050510. Maybe also add a faint "moon" glow: an emissive sphere far away — skip or add a small one.

Add distant haze: fog handles it.

Road markings: add faint emissive lines along the main street (thin cyan boxes, low intensity).

Let's write the file.

Number of buildings: grid -440..440 step 44 → 21x21 ≈ 441 minus skips → about 300. "Hundreds" ✓.

Let's write the code carefully.

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Neon City Flythrough</title>
<style>
  html,body{margin:0;padding:0;height:100%;overflow:hidden;background:#000;}
  canvas{display:block;}
</style>
</head>
<body>
<script type="module">
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { Reflector } from 'three/addons/objects/Reflector.js';
```

Then the main code.

makeWindowCanvas: canvas 64x128? window columns 6, rows 24. Lit probability 0.35, color: pick from ['#ffd9a0','#cfe8ff','#ffffff','#9fd8ff'] etc., with random alpha/brightness. Dark base #05060a.

Create 4 textures, each a THREE.CanvasTexture, colorSpace = SRGBColorSpace, anisotropy.

Building material per texture: 4 materials, MeshStandardMaterial({color:0x0b0c14, roughness:0.85, metalness:0.1, emissive:0xffffff, emissiveMap:tex, emissiveIntensity:1.1, map:tex}).

Wait, the map is also dark, no problem.

Neon colors: 0xff2f9e pink, 0x00e5ff cyan, 0xa14dff purple.

Neon sign types:
1) Vertical strip: BoxGeometry(0.8, h*0.6, 0.8), placed at a random corner, y = h*0.2..
2) Billboard: a thin box 8-14 x 3-6, at some height on one side, random rotation? Keep axis-aligned, on a random side.

Material: MeshBasicMaterial({color: neon, }) — basic isn't affected by lights; bloom threshold 0.15 will make bright colors bloom. To bloom strongly, we need color values > 1: MeshBasicMaterial's color can exceed 1 with c.setRGB(r*2,...). Simpler: new THREE.Color(hex).multiplyScalar(3). Good.

Point lights: about 10, at random building sign positions near the path, color neon, intensity 60, distance 120, decay 2. r186's light units are physically-based (useLegacyLights false is the default), intensity in candela units — 60 might be reasonable for a point light. Let's set intensity to around 200, distance 150.

Street: Reflector plane 1000x1000, y=-0.2? Building bottom at y=0. Reflector at y=0. Over a dark overlay plane at y=0.02, material MeshBasicMaterial({color:0x03040a, transparent:true, opacity:0.45, depthWrite:false}) — this darkens the reflections.

Also the street glow lines: thin boxes along x and z, 0.05 above, basic material cyan, scale 1.5.

Cars: 8 of them. Each: altitude a random 30..130, random center near origin, radius 150-300, 6 points on a circle with jitter, closed CatmullRomCurve3.

Collision fix: a buildings array with {min:Vector3, max:Vector3, pad}. function collides(curve): sample 120 points; if any point is inside any box, return the max y of the colliding boxes + 6, else null. Loop up to 12 times: newY = baseY + offset; rebuild the curve with all points' y = alt + offset; if no collision, break.

Car mesh:
```
const car = new THREE.Group();
body: BoxGeometry(3.2, 0.7, 1.4), MeshStandardMaterial color 0x11131c metalness .9 roughness .35
glow: BoxGeometry(3.4,0.15,0.5) basic color white*4, at y 0.35, z? plus two tail lights at the rear, red*4.
```
Orientation: pos = curve.getPointAt(u); ahead = curve.getPointAt(u+0.005); car.position.copy(pos); car.lookAt(ahead).

Update u: u = (u + dt*speed) % 1.

Camera curve: a closed CatmullRomCurve3 (centripetal) with the points above, but the points need to not intersect any buildings — we already skip buildings near the curve. But the curve passes between them: we precompute 600 samples of the camera curve, and skip buildings within 26 of a sample.

Also, the curve must be away from the street edge — no problem.

Camera: fov 60, near 0.1 far 1200.

Animation:

```
let last = 0;
function animate(time){
  requestAnimationFrame(animate);
  const t = time*0.001;
  const dt = Math.min((time - last)*0.001 || 0.016, 0.1); last = time;
  const u = (t * 0.012) % 1; // path period ~83 seconds
  const pos = camCurve.getPointAt(u);
  pos.y += Math.sin(t*0.5)*2;
  camera.position.copy(pos);
  const look = camCurve.getPointAt((u+0.02)%1);
  // smoothing
  lookTarget.lerp(look, 1 - Math.pow(0.001, dt)); // frame-rate independent smoothing
  camera.lookAt(lookTarget);
  // subtle roll
  camera.rotation.z += Math.sin(t*0.23)*0.01; // add after lookAt
  update cars...
  composer.render();
}
requestAnimationFrame(animate);
```

Hmm, getPointAt requires arc-length parameterization — no problem.

Initialize lookTarget to the curve point at the u of the first frame: at t=0, u=0. Set lookTarget to camCurve.getPointAt(0.02).

Roll: after lookAt, camera.rotation.z += ... OK.

Resize handler:

```
addEventListener('resize', ()=>{
  const w = innerWidth, h = innerHeight;
  camera.aspect = w/h; camera.updateProjectionMatrix();
  renderer.setSize(w,h);
  composer.setSize(w,h);
});
```

renderer.setPixelRatio(Math.min(devicePixelRatio,2)); composer.setPixelRatio? EffectComposer uses the renderer size; to match, do composer.setPixelRatio(pr) too.

Building material with a map: also set emissiveIntensity ~1.0.

Let's also add a subtle large "skyline haze": a huge sphere, basic material, side BackSide, dark blue, fog false — optional; a background color 0x06070f is enough, plus fog.

Renderer: `renderer = new THREE.WebGLRenderer({antialias:true})`.

Add stars? Skip.

Add a distant fog color-matched background plane, no problem.

Another requirement: "hundreds of skyscrapers with lit window lights and neon signs" ✓.

Point lights: to limit, 12.

Also add a dim hemisphere light: HemisphereLight(0x1a1e3a, 0x05060c, 0.6).

Let's write it all.

Car collision data: a list of boxes from the buildings array, each {x1,x2,y1,y2,z1,z2} with pad 3.

Also check car curves near the main path? Not necessary.

Also check that buildings are above 0.

Grid: `for gx=-440; gx<=440; gx+=44` with jitter ±12, skip if Math.abs(x)<20||Math.abs(z)<20 (keep a crossroads street) — but the camera path meanders with |z| up to ~40, and the 20 corridor is fine, since buildings near the curve are excluded.

Actually, the curve x goes from -380 to 420, z up to ±40. Camera corridor: buildings within 26 of the curve samples are excluded, good.

Height: random with a bias: h = 25 + Math.pow(Math.random(),1.6)*150 → mostly low, some tall.

Now, Reflector and fog: the Reflector renders the scene into its texture with its own camera — the fog is applied, OK.

Bloom threshold 0.15, strength 1.15, radius 0.7.

Let's also consider performance: 300 building meshes each with a unique box geometry (different sizes) → 300 draw calls + 300 in Reflector = 600 + others. OK.

Let's write the final HTML.

Edge: `time` parameter of rAF is a DOMHighResTimeStamp; fine.

Neon sign generation: for each building, with probability 0.45: pick a random side and a neon color.

Vertical strip: height hs = 8 + rnd*40, width 0.7, position at the building's edge: x = ±(w/2 + 0.1), z = ±(d/2 + 0.1).
Billboard: size (4+rnd*8, 1.5+rnd*3), offset by half the size on one face.

Material: basic, color = new THREE.Color(hex).multiplyScalar(2.5).

Also small "hologram rings"? Skip.

Street lines: along the z=0 and x=0 lines: thin boxes (length 900, width 0.4, height 0.02) at y 0.03, basic material cyan, 0.8 scale — subtle.

Also add dashes along the center line of the road? Skip.

OK, let's write the code fully and carefully.

One more thing: OutputPass is in 'three/addons/postprocessing/OutputPass.js' — yes, since r152.

Let's make sure we don't reference `renderer.outputColorSpace` etc.

Final answer: a single html block.
