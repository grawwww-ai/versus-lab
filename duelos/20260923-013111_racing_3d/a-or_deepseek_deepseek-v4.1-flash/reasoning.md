Let me build a complete self-contained HTML file with three.js racing scene.

Key components:
1. Track: closed loop built procedurally from a Catmull-Rom curve. Generate road mesh (extruded ribbon), kerbs on both edges, start/finish line.
2. Landscape: grass ground plane, trees (cones + cylinders), maybe buildings.
3. Sky: gradient sky via large sphere with shader or just background color + fog.
4. Player car: body, wheels spinning, lights (headlights with spotlights maybe just emissive), detailed from primitives.
5. 3 rivals in different colors, AI follows racing line, overtaking (vary speed / offset from centerline).
6. Chase camera behind player.
7. HUD: speed, lap counter, position.

Let me design the track curve. Use a closed CatmullRomCurve3 with points forming an interesting closed loop.

Points (x, z) on a plane, y = 0 approximately, maybe slight elevation.

Let's use a track of ~ 100 units scale. Car ~ 4 units long.

Track points:
```
const pts = [
  [0, 0, 0],
  [60, 0, -40],
  [110, 0, -120],
  [60, 0, -200],
  [-30, 0, -220],
  [-110, 0, -160],
  [-120, 0, -60],
  [-60, 0, 20],
  [-20, 0, 60],
  ...
]
```
Hmm, need closed loop. Let me craft a nicer shape: a big oval with a chicane.

Let me define track centerline points going around:
```
[  0,   0, -150],
[ 100,  0, -180],
[ 170,  0, -110],
[ 160,  0,  -10],
[ 100,  0,   40],
[ 120,  0,  110],
[  60,  0,  160],
[ -40,  0,  150],
[ -90,  0,   90],
[-160,  0,   70],
[-190,  0,  -20],
[-140,  0,  -80],
[-120,  0, -150],
[ -60,  0, -180],
```
That's a closed loop roughly. Fine.

Track width ~ 14 units. Road mesh built by sampling curve at N points, computing tangent and normal (perpendicular in XZ plane), then creating vertices left/right.

Kerbs: thin strips on edges with alternating red/white colors. I'll build kerb as separate geometry with vertex colors alternating, or use two meshes... Simpler: build a ribbon of segments each with its own color, alternating red/white. Use a single BufferGeometry with vertex colors.

Grass: big plane with color, plus maybe some noise. Keep simple: large plane with grass green, plus a slightly raised "terrain".

Trees: cone + cylinder merged, placed randomly avoiding track. Check distance from curve samples > threshold.

Buildings: boxes with random colors, placed further out.

Sky: gradient using a large sphere with a shader material (BackSide). Plus hemisphere light + directional light.

Sun: maybe.

Car model function: createCar(colorHex) returns THREE.Group with:
- body: BoxGeometry ~ 4 x 0.7 x 1.8, rounded? use scaled boxes.
- cabin: smaller box on top.
- nose slope: maybe another box.
- wheels: CylinderGeometry rotated, radius 0.35, width 0.3, dark with a lighter hub.
- lights: front white emissive small boxes, rear red emissive.
- spoiler.

Wheels spin: rotate around local x-axis by speed.

Car AI: each car has a parameter `t` along curve (arc-length-ish). Actually easier: use curve.getPointAt(u) and offset laterally. Each car has position u in [0,1) and lateral offset. Speed determined by target speed with cornering slowdown. Overtaking: raycast-ish check ahead — simple: if a car ahead within some distance is slower and lateral offset difference small, shift lateral offset to pass.

Simplest approach that looks good: each car has an "offset" target from the centerline, and a speed. Speed depends on curvature ahead. Overtaking: compute distance to other cars; if another car is close ahead, steer offset away.

Let me implement:

```js
class Car {
  constructor(color, isPlayer, offsetBias) {...}
  update(dt) {...}
}
```

Track curve: THREE.CatmullRomCurve3, closed, curveType 'catmullrom', tension 0.5. Use `getSpacedPoints` for arc-length uniform. Actually I'll precompute an array of samples: positions, tangents, and cumulative length for uniform parametrization. `curve.getPointAt(u)` uses arc-length parametrization — good, use directly.

For AI cornering: compute curvature by sampling tangent at u and u+du. Compute angle difference, derive target speed: `targetSpeed = clamp(maxSpeed * (1 - curvature*k), minSpeed, maxSpeed)`.

Also need to know lap completion: when u wraps from ~1 to 0, increment lap.

Position calculation: total progress = lap + u, sorted descending.

Camera: chase camera behind player car, smoothed. Player car is one of the AI cars (it drives itself). So the player car also uses AI logic but with slightly higher target speed maybe, and camera follows.

Add sense of speed: camera FOV increases with speed, plus motion blur? FOV is enough. Also add a slight camera shake.

HUD: overlay divs with speed (km/h), lap counter, position.

Let me write the code.

```js
import * as THREE from 'three';
```

No addons needed really. Maybe not.

Scene setup:

```js
const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0x9fc4e8, 200, 700);
const camera = new THREE.PerspectiveCamera(70, w/h, 0.5, 2000);
const renderer = new THREE.WebGLRenderer({antialias:true});
```

Sky: large sphere with ShaderMaterial gradient.

```js
const skyGeo = new THREE.SphereGeometry(1200, 32, 16);
const skyMat = new THREE.ShaderMaterial({
  uniforms: { top: {value: new THREE.Color(0x1e5fa8)}, bottom: {value: new THREE.Color(0xbfe3ff)}, offset:{value:100}, exponent:{value:0.7} },
  vertexShader: `varying vec3 vWorldPosition; void main(){ vec4 wp = modelMatrix * vec4(position,1.0); vWorldPosition = wp.xyz; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0);}`,
  fragmentShader: `uniform vec3 top; uniform vec3 bottom; uniform float offset; uniform float exponent; varying vec3 vWorldPosition; void main(){ float h = normalize(vWorldPosition + vec3(0.0,offset,0.0)).y; gl_FragColor = vec4(mix(bottom, top, max(pow(max(h,0.0), exponent), 0.0)),1.0);}`,
  side: THREE.BackSide
});
```

Grass: PlaneGeometry 3000x3000 rotated -PI/2, color 0x4a8f3c. Maybe add a subtle noise texture via canvas... but "no external images" - canvas generated texture is fine, it's inline. I'll keep it simple with just color plus maybe some vertex color variation. Actually a simple procedural canvas texture for grass would improve looks. Let's do a small canvas noise texture repeated.

Track geometry function:

```js
function buildTrack(curve, width) {
  const N = 500;
  // positions arrays
}
```

For each i in 0..N-1, u = i/N, p = curve.getPointAt(u), tangent = curve.getTangentAt(u), normal = perpendicular: (tangent.z, 0, -tangent.x) normalized... For a left/right offset: right vector = tangent cross up? up=(0,1,0). right = tangent × up = (t.y*0 - t.z*1... let's compute: t × up where up=(0,1,0): 
t=(tx,ty,tz), up=(0,1,0).
cross = (ty*0 - tz*1, tz*0 - tx*0, tx*1 - ty*0) = (-tz, 0, tx).
So right = (-tz, 0, tx) normalized. Good.

Left edge = p - right*halfWidth, right edge = p + right*halfWidth.

Build road as triangle strip -> indexed geometry with UVs. Also lift road slightly y+0.02 to avoid z-fighting with grass; better set grass at y=-0.05.

Actually let's make the track slightly elevated: y = 0 for road, grass at y=-0.1.

Kerbs: on both sides, width 1.2, from halfWidth to halfWidth+1.2. Alternate colors per segment: use vertex colors on the kerb ribbon, red/white alternating every ~4 segments. Also kerbs slightly raised at outer? Keep flat but y+0.06.

Actually kerbs should be on the inside of corners mostly, but for arcade, both sides is fine.

Start/finish line: a plane across track at u=0, with checkered texture generated from canvas. Rectangle width = trackWidth, depth 3. Use canvas texture with checker.

Now cars.

Car geometry details:
- chassis: BoxGeometry(1.9, 0.5, 4.0) at y=0.55 — wait, orientation: car length along z? Let's define car forward along +z? In three.js, default lookAt... I'll build car with forward = +z, and use `car.lookAt(target)` which orients -z toward target... Actually Object3D.lookAt makes the object's +z? For non-camera objects, lookAt points the +z axis toward the target? Let me recall: Object3D.lookAt rotates the object so that its local +Z axis points toward the target (for cameras it's -Z). Yes, for regular objects, +Z faces the target. Wait — actually the docs say: "Rotates the object to face a point in world space." And implementation uses `m1.lookAt(eye, target, up)` where for non-camera `m1.lookAt(target, position, up)`. Hmm.

In Object3D.lookAt:
```js
if ( this.isCamera || this.isLight ) {
  _m1.lookAt( _position, _target, this.up );
} else {
  _m1.lookAt( _target, _position, this.up );
}
```
Matrix4.lookAt(eye, target, up) builds a rotation where z = normalize(eye - target). So for non-camera: eye=_target, target=_position → z = normalize(target - position) = direction to target. So +Z faces target. Good.

So build car facing +Z.

Car parts:
- Body lower: BoxGeometry(1.8, 0.5, 4.2), y=0.5, color main.
- Body upper/cabin: BoxGeometry(1.5, 0.45, 1.9), y=0.95, z=-0.2, slightly darker/glass color.
- Nose wedge: BoxGeometry(1.6,0.3,1.0) at z=1.9, y=0.42, scaled.
- Rear spoiler: BoxGeometry(1.6,0.08,0.5) at y=1.15, z=-2.0 plus supports.
- Wheels: radius 0.45, width 0.35. Positions: x=±0.95, z=±1.4, y=0.45.
- Wheel = CylinderGeometry(0.45,0.45,0.35,16) rotated z by PI/2 so axis along x. Add hub: smaller cylinder lighter color. Group each wheel so we can rotate.x for spin... wait if cylinder axis along X after rotation, spinning is rotation about X. So wheel group with rotation.x = spin. Hmm but rotate the cylinder mesh itself: create wheelGroup, add cylinder rotated PI/2 about Z (axis along X), then set wheelGroup.rotation.x = spinAngle. But rotating group about x rotates the cylinder around X axis which is its axis — correct spin.

Hmm, careful: rotating a cylinder about its own axis is invisible unless it has texture/spokes. Add a spoke box crossing the wheel so spin is visible. Yes: add two thin boxes crossing through the wheel center. Good.

- Headlights: small boxes at front with emissive white material. Plus optional SpotLight? Too expensive for 4 cars. Just emissive + maybe a small pointlight for player. Skip lights, use emissive.
- Taillights: red emissive boxes at rear.
- Also add brake light glow when slowing — nice touch, can change emissive intensity.

Under car: a dark shadow plane? Use a circular shadow with transparent material. Or just rely on lighting. I'll add a simple dark ellipse plane under each car.

Number of cars: player + 3 rivals = 4.

Colors: player red (0xd81e2c), rivals blue, yellow, green.

AI logic:

Each car:
- `u` param 0..1 along curve
- `speed` (units/sec)
- `lateral` offset (target and current)
- `lap`

Track length L = curve.getLength(). speed along the curve: du = speed * dt / L.

Corner handling: compute curvature at u.

```js
function curvatureAt(u) {
  const d = 0.01;
  const t1 = curve.getTangentAt((u - d + 1) % 1);
  const t2 = curve.getTangentAt((u + d) % 1);
  const ang = t1.angleTo(t2); // radians over 2d arc length
  return ang / (2*d*L);
}
```
Then max speed = sqrt(latAccel / curvature) roughly. Clamp.

Let's precompute an array of curvature samples for speed lookup (N=400) to avoid getTangentAt calls every frame per car. Good.

Also target speed = min(topSpeed, sqrt(maxLat/curv)). With maxLat ~ 60 units/s² and L ~ 1000.

Let me estimate: track length ~ maybe 900 units. A car at 60 units/s takes 15s per lap. 3 laps = 45s. Fine — we want to see lap counting within 30s ideally... Lap 1/3 in 30 seconds is fine, they'd see lap 1 changing to lap 2 maybe. Let's make lap ~15s. Top speed ~ 70 u/s.

Actually "the animation should show everything important within the first 30 seconds" — the HUD, cars driving, overtaking. Fine.

Let's compute curvature: for a corner of radius R, curvature = 1/R. Track corner radii ~ 40 units. maxLat = 80 → v = sqrt(80*40) = 56. Straight: v = 70. OK.

Lateral offset for overtaking: base offset per car (racing line offsets). Simpler: each car has desired offset (bias) which they change to avoid collisions.

Collision avoidance:
For each pair of cars, compute distance along track: `du = (other.u - car.u + 1) % 1` and convert to distance `du * L`. If 0 < gap < 12 and |other.lateral - car.lateral| < 2.5 → the car behind should shift lateral to overtake: target offset = other.lateral + sign * 3 (pick side with more room, clamp to ±(halfWidth-1.5)). Also if gap < 5, reduce speed to avoid ramming.

Also if the car is blocked and there's no room, slow down.

Also add slight speed difference so overtakes happen naturally: each car has a speedMultiplier between 0.97 and 1.03.

Player car: the "player" is also AI-driven but with a slightly better multiplier, and the chase camera follows it. Position display: player's position among 4.

Camera: 
```js
const camTarget = car position + offset behind based on car heading
```
Smooth using lerp with dt.

Better: compute desired camera position = car.position - forward*distance + up*height, where forward is car's world direction. Then `camera.position.lerp(desired, 1 - exp(-dt*6))`. Look at car position + forward*10.

Speed sense: FOV = 65 + speed*0.25, clamped.

Also add slight camera shake at high speed? Optional.

HUD: absolutely positioned divs, updating textContent each frame.

Let's also handle: cars should be placed at start line at staggered positions, lateral offsets, and offset u values slightly behind.

Now the trees: place around using random positions, check distance to track centerline. Precompute sample points array (from track building) and check min distance > halfWidth + 6.

Buildings: a few boxes with different heights/colors placed further out (> 40 from track).

Also add some grandstands? keep it modest.

Let's write it.

```js
// ---------- Track curve ----------
const trackPoints = [
  new THREE.Vector3(  0, 0, -170),
  new THREE.Vector3( 110, 0, -190),
  new THREE.Vector3( 185, 0, -120),
  new THREE.Vector3( 180, 0,  -20),
  new THREE.Vector3( 110, 0,   45),
  new THREE.Vector3( 130, 0,  120),
  new THREE.Vector3(  60, 0,  175),
  new THREE.Vector3( -40, 0,  165),
  new THREE.Vector3( -95, 0,  100),
  new THREE.Vector3(-170, 0,   80),
  new THREE.Vector3(-205, 0,  -10),
  new THREE.Vector3(-150, 0,  -85),
  new THREE.Vector3(-130, 0, -160),
  new THREE.Vector3( -60, 0, -195),
];
const curve = new THREE.CatmullRomCurve3(trackPoints, true, 'catmullrom', 0.5);
```

Track length maybe ~1100. Good.

Half width 9 → track 18 wide. Cars 1.8 wide... that's wide but ok for arcade overtaking. Maybe track width 16, halfWidth 8.

Let's use trackWidth = 16.

Building the road mesh:

```js
const SEG = 600;
const roadPositions = [], roadUVs = [], roadIndices = [];
const centerSamples = [];
for (let i=0;i<=SEG;i++){
  const u = i/SEG;
  const p = curve.getPointAt(u % 1);
  const t = curve.getTangentAt(u % 1);
  const right = new THREE.Vector3(-t.z, 0, t.x).normalize();
  ...
}
```
Careful with u=1 → getPointAt(1) ok.

Vertices: for each i, left = p + right*hw, right = p - right*hw... whichever, doesn't matter. Let's do v0 = p - right*hw (left in some sense), v1 = p + right*hw.

Indices: for i in 0..SEG-1: a = 2i, b=2i+1, c=2i+2, d=2i+3 → triangles (a,b,d) hmm need correct winding for upward normal. Let's just use MeshStandardMaterial with side: DoubleSide to be safe? That costs a bit but is fine. Actually let's get winding right: we want the normal to point up (+y). Vertices: index 2i = left point (p - right*hw), 2i+1 = right point (p + right*hw), progressing along tangent.

Triangle (2i, 2i+2, 2i+1): vectors: A = P(2i), B = P(2i+2) (ahead), C = P(2i+1) (right). AB ≈ tangent, AC ≈ right vector (2*hw). normal = AB × AC = tangent × right. tangent=(tx,0,tz), right=(-tz,0,tx). cross = (0*tx - tz*0, tz*(-tz) - tx*tx, tx*0 - 0*(-tz)) = (0, -(tz²+tx²), 0) = (0,-1,0). Downward. So reverse: (2i, 2i+1, 2i+2) gives normal up. Let's use triangles: (a, b, c) and (b, d, c) where a=2i (left), b=2i+1 (right), c=2i+2 (next left), d=2i+3 (next right).

Check (a,b,c): AB = right dir, AC = tangent. right × tangent = -tangent × right = (0,1,0). Up. Good.
(b,d,c): BD = tangent, BC = -right + tangent... let's trust the standard quad triangulation (a,b,c),(b,d,c) preserves winding. Yes standard.

UVs: u along length (i/SEG * repeat), v across 0..1. For road texture I'll create a simple asphalt canvas texture with noise and a dashed center line? Hmm, center line might look nice. Let's create a canvas texture: dark gray noise. And repeat along length many times.

Actually simpler and cleaner: use plain dark gray material with slight roughness, plus separate white dashed centre line strips? Skip centre line; road with kerbs looks fine. But an asphalt texture adds realism. Let me generate a canvas 128x128 noise texture, repeat (1, 100) — for the road. Since UV v goes across width... I'll set uv = (u_across, v_along) hmm. Let's set uv.x = 0 or 1 across, uv.y = i/SEG * 200 (repeat along). Then texture.repeat not needed if UVs already scaled. Just set wrapT = RepeatWrapping and uv.y scaled.

Kerb ribbon: same approach, from hw to hw+1.2, with y slightly higher and vertex colors. For alternating red/white, color per segment index i: (Math.floor(i/6) % 2 == 0) ? red : white. Set both vertices of that segment's column... but vertices are shared between segments. Since we need per-segment colors, easier to just create separate quads with duplicated vertices. Or assign vertex color per row i and accept gradient. Actually assigning per row color and having strip means smooth gradient between red and white — looks like a transition. Better to duplicate. Let's build kerb with non-indexed geometry: for each segment i, create 2 triangles with 6 vertices, all with the segment's color. That's 600 segments * 2 sides * 6 = 7200 verts. Fine.

Actually simpler: use both kerbs in one geometry, non-indexed.

Let me write a helper:

```js
function buildRibbon(curve, innerOffset, outerOffset, y, segments, colorFn) {
  const positions = [], colors = [], indices = [];
  ...
}
```

Hmm, let me just write two functions: buildRoad and buildKerbs.

For the start/finish line: create a plane at curve.getPointAt(0)+ y 0.03, oriented with the track. Use a checkerboard canvas texture on a PlaneGeometry(trackWidth, 3). Rotate to lie flat: plane default is in XY, rotate -PI/2 about X → lies in XZ. Then we need to align its "up in plane" with the tangent. Easier: create the mesh, position it, then set rotation.y = atan2(t.x, t.z) and rotation.x = -PI/2. Order matters with Euler default XYZ. Hmm, applying rotation.x=-PI/2 first then y... Euler XYZ applies... Let's instead use a container: create a group, set group.position and group.rotation.y = angle, and inside add plane rotated -PI/2 about X. That way plane local +Y (its height) maps to group -Z... whatever, it's a square-ish stripe so orientation about vertical axis matters. Set angle = atan2(t.x, t.z)? We want the plane's width (x) to be perpendicular to the tangent, i.e., along `right`. right = (-tz, 0, tx). The group's local X axis after rotation.y = θ is (cosθ, 0, -sinθ). We want that = (-tz, 0, tx) → cosθ = -tz, -sinθ = tx → sinθ = -tx. θ = atan2(-tx, -tz). OK.

Actually the plane width should span the track (perpendicular) and the depth (3 units) along the track. The plane geometry is (width=16, height=3) in local XY. After rotate -PI/2 about X: local Y → world -Z... The plane's local Y axis becomes local Z axis direction (rotate x by -90: Y→-Z? rotation about X by -90°: Y axis (0,1,0) → (0, cos(-90), sin(-90)) = (0,0,-1). So local +Y → -Z. And local Z (normal (0,0,1)) → (0, cos(-90)*0 - ... ) let's compute: rotating (0,0,1) about X by -90°: (0, 0*cos - 1*sin(-90)... formula: y' = y cosθ - z sinθ, z' = y sinθ + z cosθ. θ=-90: cos=0, sin=-1. For (0,0,1): y' = 0*0 - 1*(-1) = 1, z' = 0*(-1) + 1*0 = 0. So normal → (0,1,0) up. Good. And (0,1,0) → y' = 1*0 - 0 = 0, z' = 1*(-1) + 0 = -1 → (0,0,-1). So local +Y → -Z (group's -Z). 

So in group local space: X spans track width, -Z along... we want the 3-unit depth along the group's Z which will be aligned to track tangent. Group rotation.y = θ such that group's local Z axis maps to tangent: local Z (0,0,1) after rotation.y=θ → (sinθ, 0, cosθ). Set = tangent → sinθ = tx, cosθ = tz → θ = atan2(tx, tz). Then local X maps to (cosθ, 0, -sinθ) = (tz, 0, -tx) = -right. Fine, it's just the width direction (flipped, doesn't matter).

Good: group.rotation.y = Math.atan2(t.x, t.z).

Now trees: 
- Trunk: CylinderGeometry(0.35,0.5,3,6) brown.
- Foliage: 2-3 ConeGeometry or IcosahedronGeometry green.

Use InstancedMesh? Not needed for ~150 trees; but each tree group with 2 meshes = 300 draw calls. Hmm, that's a lot but ok at 60fps? Probably fine but let's use InstancedMesh for performance: trunkInstanced and foliageInstanced. Simpler: just create merged geometry per tree type... Let's just use InstancedMesh with random scale/rotation. Two InstancedMeshes: trunks and leaves. Leaves as a cone.

Buildings: InstancedMesh of boxes with per-instance color. Use `setColorAt`.

Okay, let's just do:
- trees: 120 instances (trunk cylinder + foliage cone), random scale.
- buildings: 25 instances boxes with random colors, placed outside track.

Grass: plane 3000x3000.

Also add a few "hills"? skip.

Let me now write the car creation.

```js
function createCar(color) {
  const g = new THREE.Group();
  const bodyMat = new THREE.MeshStandardMaterial({color, metalness:0.5, roughness:0.35});
  const darkMat = new THREE.MeshStandardMaterial({color:0x1a1a1e, metalness:0.4, roughness:0.6});
  const glassMat = new THREE.MeshStandardMaterial({color:0x88bbdd, metalness:0.9, roughness:0.1, transparent:true, opacity:0.75});
  ...
}
```

Body: 
- main box (1.8 w, 0.55 h, 4.0 l) at y=0.55
- lower skirt box (1.9, 0.25, 3.6) at y=0.3 dark
- cabin: box(1.5, 0.5, 1.7) at y=1.05, z=-0.15, glass
- roof: box(1.3,0.1,1.5) at y=1.32? Might be overkill. Use cabin glass + roof plate color.
- nose: box(1.7, 0.3, 1.2) at y=0.55, z=1.9? Actually the main box already extends to z=2. Let's make main body 3.6 long (z from -1.8 to 1.8) and nose box tapered.

Let me lay out:
- chassis: BoxGeometry(1.8, 0.6, 3.8), pos y=0.6.
- front nose: BoxGeometry(1.6, 0.35, 1.0), pos y=0.5, z=2.2 — extends forward to 2.7.
- rear deck: BoxGeometry(1.7, 0.35, 0.8), pos y=0.85, z=-2.0.
- cabin: BoxGeometry(1.45, 0.55, 1.6), pos y=1.15, z=-0.2, glass material.
- spoiler: BoxGeometry(1.7, 0.1, 0.5), y=1.35, z=-2.1, dark; supports two boxes.
- headlights: BoxGeometry(0.35,0.14,0.1) at x=±0.6, y=0.62, z=2.72 emissive white.
- taillights: BoxGeometry(0.45,0.14,0.1) at x=±0.6, y=0.75, z=-2.42 emissive red.
- wheels: at (±0.92, 0.45, ±1.35).

Wheel: cylinder radius 0.45, height 0.34, radialSegments 14, rotated PI/2 about Z so axis along X. Tire dark. Add hub disc (cylinder radius 0.22, height 0.36, lighter gray) same orientation. Plus a "spoke" box (0.05, 0.7, 0.08)? Actually to see spin, put a small box across the wheel face: BoxGeometry(0.36, 0.06, 0.8)? Hmm, the wheel's face plane is YZ (since axis along X). A spoke bar along Y: BoxGeometry(0.36, 0.9, 0.08) — wait width along X = 0.36 (wheel width), height along Y = 0.9 (diameter-ish), depth along Z = 0.08. Positioned at wheel center. That gives a bar visible from the side. Add another rotated 90° about X for a cross. Good enough.

Actually simpler: use a cylinder with fewer radial segments and a lighter material for the hub, plus a spoke box. Fine.

Wheel group at position, contains tire mesh + spoke; rotate the group about X for spin.

Hmm: the wheel axis is along X (left-right). Rotating the wheel group about X spins it. Yes.

Now car headlights emissive: use MeshStandardMaterial with emissive: 0xffffff, emissiveIntensity: 1. Taillights emissive red.

Now the car update:

```js
const cars = [];
class RaceCar {
  constructor(color, isPlayer, skill, startOffset) {
    this.mesh = createCar(color);
    scene.add(this.mesh);
    this.u = 0; // param
    this.lap = 1;
    this.speed = 0;
    this.lateral = startOffset;
    this.targetLateral = startOffset;
    this.wheels = [...];
    this.skill = skill;
    this.progress = 0;
  }
}
```

Wait, for lap counting with `u` wrapping: keep a continuous `dist` variable that increases; u = (dist / L) % 1; lap = floor(dist/L) + 1.

That's cleaner: each car has `dist` (total distance travelled along the centerline). u = (dist / L) % 1. lap = Math.floor(dist / L) + 1. Start with dist = -offsetBehind so they start behind the line... Actually to have them start AT the start line, set dist = small negative values so they cross quickly? For lap counting, they should complete 3 laps. Let's start all cars slightly behind the start line: dist = -(i * 3). Lap counter = floor(dist/L)+1 which for negative dist gives 0. Hmm. Let's just clamp lap display to max(1, ...).

Alternative: start them just after the line: dist = i*3, lap = 1. Then lap increments when floor(dist/L)+1 changes. After L distance, lap=2. Fine. Position them staggered laterally.

Let's set grid: player at dist=0 with lateral -3; rivals at dist = -5, -10, -15 hmm but negative dist gives lap 0. Use dist starting at 5,10,15,20 for the four cars in grid order and lateral offsets ±3. Then all have lap 1. But the ones with larger dist are ahead — fine, that's a grid.

Actually let's put the player at the back to make it interesting? No — put player 2nd on grid so overtaking happens.

Grid: 
- car0 (rival blue) dist=6, lateral=-3
- car1 (player red) dist=10, lateral=+3  — wait larger dist is further ahead. Let's do: player dist = 12, lateral=3; rivals at 0, 4, 8 with alternating lateral.

Hmm, "dist" increases forward. Cars with larger dist are ahead. So the one at 12 is pole. Let's make player start 3rd: player dist=6; rivals at 12, 9, 3.

Fine, details.

Speed update per frame:

```js
update(dt) {
  const u = (this.dist / L) % 1;
  // curvature ahead
  const lookAheadDist = 15 + this.speed * 0.8;
  const cu = ((u + lookAheadDist / L) % 1);
  const curv = curvatureSample(cu);
  let targetSpeed = Math.min(this.topSpeed, Math.sqrt(this.maxLat / Math.max(curv, 1e-4)));
  targetSpeed *= this.skill;
  ...
}
```

Hmm, using curvature at lookahead to determine corner speed is a decent approximation. But the car should brake before the corner. Look ahead by speed*0.8 seconds. Then target speed computed from curvature there — but that means when entering the corner the car is still going fast. Better: compute the max speed over a few lookahead points and take the minimum considering braking distance. Simplify: sample curvature at several points ahead (0..60 units) and compute allowed speed = min over samples of sqrt(maxLat/curv) adjusted by distance (can brake at rate). 

Simpler heuristic that looks fine: 
```
let vmax = topSpeed;
for (let d = 0; d < 70; d += 10) {
  const c = curvAt(u + d/L);
  const vCorner = Math.sqrt(maxLat / Math.max(c, 0.0005));
  const allowed = Math.sqrt(vCorner*vCorner + 2*brake*d);
  vmax = Math.min(vmax, allowed);
}
```
That's proper braking distance physics: to slow to vCorner over distance d with deceleration `brake`. 

Then targetSpeed = vmax * skill.

Accelerate/brake: 
```
const accel = (targetSpeed > this.speed) ? this.accelRate : -this.brakeRate;
this.speed += accel*dt... 
```
but clamp toward target smoothly. Use:
```
const diff = targetSpeed - this.speed;
this.speed += THREE.MathUtils.clamp(diff, -brake*dt, accel*dt);
```

Then this.dist += this.speed * dt.

Lateral: steer toward target lateral with a rate limit:
```
this.lateral += THREE.MathUtils.clamp(this.targetLateral - this.lateral, -latRate*dt, latRate*dt);
```

Position on track: p = curve.getPointAt(u); right = ...; pos = p + right*lateral; y = p.y (+ maybe small).

Wait my right vector: right = (-tz, 0, tx). Let's call it `side`. Then pos = p + side * lateral.

Orientation: heading tangent = curve.getTangentAt(u). But with lateral movement there should be a slight yaw. Ignore, or compute using the derivative. Just use lookAt(pos + tangent).

Actually to make it smooth, store a smoothed heading vector. Let's just compute `lookAt` each frame with the target point ahead: `car.mesh.lookAt(p_ahead + side*lateral)` where p_ahead = curve.getPointAt(u + small). This gives a natural look.

Also add body roll on corners? Nice touch: roll = -curvature * speed factor. Set mesh.rotation.z after lookAt... but lookAt sets quaternion. Could apply as child group. Let's put car visual in an inner group and apply roll to inner group's rotation.z. And pitch on accel/brake. Let's keep simple: inner group rotation.z = roll, rotation.x = pitch.

Hmm, but lookAt on outer group sets full orientation including... The outer group rotates to face along track; the inner group can rotate about local Z (roll). Good.

Wheels spin: `wheel.rotation.x += speed / wheelRadius * dt`. Since car moves forward along +Z? Wait — the car mesh faces +Z toward the lookAt target. The wheel spin about X axis: moving forward in +Z means top of wheel moves +Z → rotation about X negative? Rotating about +X by angle θ: point (0,1,0) → (0, cosθ, sinθ). For forward roll, the top of the wheel moves forward (+Z) so θ increasing gives +Z at top... wait, forward means the wheel rolls such that the top moves in the direction of travel. Travel direction is +Z (car's local). Rotating about X by +θ moves the top point (0,r,0) toward +Z. Yes, so rotation.x += speed*dt/r. 

Now AI overtaking logic.

Each frame, for each pair (a, b) with a behind b:
```
let gap = b.dist - a.dist;
if (gap > L/2) gap -= L; // wrap
if (gap < L/2 && gap > 0 && gap < 15) { ... }
```
Hmm careful with wrap. Since all cars are roughly in the same area, gap = ((b.dist - a.dist) mod L). Let's compute `gap = ((b.dist - a.dist) % L + L) % L;` then if gap < 15, b is close ahead of a.

Then:
- lateral difference: `dl = b.lateral - a.lateral`.
- If |dl| < 3.2 (they'd collide), a should steer: choose side: if a.lateral > b.lateral → pass on the... a targets b.lateral + 4 clamped to track bounds; else b.lateral - 4. But also need to consider track width and other cars. Simple approach.
- If the gap is small (< 8), reduce target speed slightly (drafting? no, just avoid ramming).

Also need to reset targetLateral back to the "racing line" when clear. Racing line offset: use a per-car preferred offset (e.g. sinusoidal based on u, cutting corners). Let's give each car a `lineOffset` = baseOffset + sin(u*2π*3)*1.5 or something. Actually a nice touch: apex cutting - offset toward inside of corners. Compute from curvature sign? Curvature sign requires cross product. Let's keep it simple: preferred offset = car.bias (constant, e.g. -1.5, 0, 1.5, 0) plus small sine wobble. Meh. Simpler: preferred = 0 for all, with slight per-car bias. Overtake target overrides.

Let me implement:

```js
const desired = this.biasOffset + Math.sin(u * Math.PI * 6) * 0.8;
let target = desired;
let speedScale = 1;
for each other car b:
   gap = ...
   if (gap < 18 && gap > -1) {
     const dl = b.lateral - this.lateral;
     if (Math.abs(dl) < 3.5) {
       // need to move aside
       const dir = dl > 0 ? -1 : 1;  // move to the opposite side of b
       target = THREE.MathUtils.clamp(this.lateral + dir * 6, -maxLat, maxLat);
       // hmm this creates a nudge
     }
     if (gap < 9) speedScale = Math.min(speedScale, 0.85 + gap/60);  // slow slightly
   }
```

Hmm, if two cars are side by side (gap ~0), the behind one should keep its lateral. Let me use: if gap between -3 and 14 and |dl| < 3.5 → steer away from b by moving target to b.lateral ± 3.6 on the side away from b... Actually moving *away* from b means if b is to my left (dl < 0 meaning b.lateral < a.lateral... careful: dl = b.lateral - a.lateral; dl<0 → b is to my left (more negative lateral)). Then I should move right: target = b.lateral + 3.6 = a.lateral + dl + 3.6. Hmm if dl is -1, target = a.lateral + 2.6. That's only slightly to the right. Better to just set target = a.lateral + sign * 4 where sign = (dl < 0) ? +1 : -1. But repeated every frame this would keep pushing. Clamp to track bounds ±(hw - 2.5) = ±5.5.

Actually simpler and effective: target = b.lateral + (dl < 0 ? 4.2 : -4.2), clamped. So the car aims to be 4.2 units to the side of the other car. That naturally handles the shift and settles.

But if b.lateral is +5 (near the edge) then target = 5 + 4.2 = 9.2, clamped to 5.5. Then if this car is already at 5.5 and dl small... it'd just sit there. Might cause a stuck pair. Add: if the car is much faster and stuck for a while... it's fine, they'll eventually pass since speeds differ. Also allow going slightly off-track edge? No.

Let me allow lateral range ±(hw - 2) = ±6 with hw=8.

Hmm, actually with a 16-wide track and cars 1.8 wide, three can be side by side. Fine.

Also collision resolution: if two cars actually overlap (gap < 4.5 and |dl| < 2.2), push them apart laterally and slow the rear one. Let's add a simple hard resolve: move the rear car's lateral away and reduce speed.

Let's write:

```js
resolveCollisions() {
  for pairs: 
    if (gap < 4.5 && gap > -4.5 && |dl| < 2.0) {
      const push = (2.0 - Math.abs(dl)) ...
    }
}
```
Might be overkill. I'll do a light version: if gap < 4.2 and |dl| < 2.2, then a.lateral -= sign(dl||1)*... and a.speed *= 0.98.

OK.

Position ranking: sort cars by dist descending → index+1. Player's rank displayed with suffix.

Now the camera.

```js
const camOffset = new THREE.Vector3();
function updateCamera(dt) {
  const car = player.mesh;
  const speed = player.speed;
  const back = 8 + speed * 0.09;
  const up = 3.2;
  const fwd = new THREE.Vector3(0,0,1).applyQuaternion(car.quaternion); // car forward
  ...
}
```
Wait car forward is +Z in local. So `fwd = new THREE.Vector3(0,0,1).applyQuaternion(car.quaternion)`.

desiredPos = car.position - fwd*back + (0, up, 0).
Then smooth: `camera.position.lerp(desiredPos, 1 - Math.exp(-8*dt))`.
LookAt: target = car.position + fwd*12 + (0,1.2,0). Smooth the look target too.

FOV: `camera.fov = 62 + speed*0.35; camera.updateProjectionMatrix();` — with speed ~70, fov = 62+24 = 86. Maybe too much. Use 60 + speed*0.25 → 77. OK.

Also add a speed-line effect? Skip.

Handle resize.

Time: use requestAnimationFrame timestamp.

```js
let last = 0;
function animate(now) {
  requestAnimationFrame(animate);
  const dt = Math.min((now - last)/1000, 0.05); last = now;
  ...
}
requestAnimationFrame(animate);
```
First frame dt = 0 (last=0 → now likely large; set last = performance.now() initially). Use `if (last === 0) last = now;`.

Now HUD elements:
```html
<div id="hud">
  <div id="speed">0<span>KM/H</span></div>
  <div id="lap">LAP 1/3</div>
  <div id="pos">1st</div>
</div>
```

Style: absolute positioned, monospace, big, with text-shadow.

Let's also add a small "mini" info at the top.

Speed in km/h: speed (units/s) * 3.6? If units are meters, 70 m/s = 252 km/h. That's fine for arcade. Multiply by 3.6 and round.

Now, let's write the curvature precompute.

```js
const CURV_N = 1000;
const curvArray = new Float32Array(CURV_N);
for (let i=0;i<CURV_N;i++){
  const u = i/CURV_N;
  const t1 = curve.getTangentAt(u);
  const t2 = curve.getTangentAt((u + 1/CURV_N) % 1);
  const ang = t1.angleTo(t2);
  const ds = L / CURV_N;
  curvArray[i] = ang / ds;
}
function curvAt(u) {
  const f = ((u % 1) + 1) % 1 * CURV_N;
  return curvArray[Math.floor(f) % CURV_N];
}
```
Note: getTangentAt uses arc-length param too. angleTo returns unsigned angle. Good.

L = curve.getLength().

Now sample the corner speed using curvature. maxLatAccel = 75 (units/s²). For curvature 0.025 (radius 40), v = sqrt(75/0.025) = sqrt(3000) = 54.8. Top speed 78 → on straights.

Lap time: track length L. Let's compute later — I'll just make sure it feels right.

Now the track curvature: with points ~100 units apart and Catmull-Rom tension 0.5, corners have radius ~50. OK.

Let's also add track elevation variation? Keeping y=0 keeps everything simpler (cars on flat plane). Maybe add slight elevation by modifying y in the curve points. Then cars follow p.y and it looks nicer. Let's add modest y values: e.g., some points y=0, some y=4. The track surface will have slope; cars will follow. Camera also. It's fine since we use the curve points for position. But the road mesh rendered from the curve will also slope — fine.

However, the car's "up" orientation via lookAt uses the world up, so on slopes it'd be slightly off but acceptable. Let's add mild elevation: ±3 units. Actually let's keep it flat to avoid issues with kerbs and start line. Hmm, slight elevation adds a lot visually. I'll add small y values (±4) and it should be fine.

Wait, but the ground plane is flat at y=-0.1, so elevated track sections would float. Need to either keep track flat or make the ground follow. Keep flat. Grass at y=-0.15, road at y=0.

Hmm, but the road is flat at y=0 and the ground at y=-0.15 — from a distance you'd see a floating ribbon. Add a slight embankment? Not necessary; -0.15 is small. Actually let's make grass at y = -0.3 and add a "verge" ribbon under the kerbs? Meh. Keep the road at y = 0.05 and grass at y=0. Fine — tiny offset avoids z-fighting.

Actually let's do road at y=0.06, kerbs top at y=0.12, grass at y=0. Cars at y from curve (0) + wheel offset. Hmm, cars are positioned at curve point y (0), and their wheels are at y=0.45 with radius 0.45, so the wheel bottom touches y=0. If the road is at y=0.06, wheels sink slightly. Just put road at y=0.02 and grass at y=-0.05. Fine.

Let's finalize: roadY = 0.02, kerbY = 0.06, grassY = -0.06, cars at curve y = 0 → wheel bottoms at 0 (0.02 above grass). Good.

Grass with a subtle canvas texture to break up flatness. Let me create a canvas 256x256 with green noise, repeat 60x60 over a 3000x3000 plane.

Now let's think about draw calls: road, kerbs x2 (or one merged), grass, sky, start line, ~4 cars × ~15 meshes = 60, trees instanced 2, buildings 1. Fine.

Let me write the code now.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Arcade Racer</title>
<style>
  html,body{margin:0;padding:0;overflow:hidden;background:#000;height:100%;}
  canvas{display:block;}
  #hud{position:fixed;inset:0;pointer-events:none;font-family:"Trebuchet MS",Arial,sans-serif;color:#fff;text-shadow:0 2px 8px rgba(0,0,0,.8);}
  ...
</style>
</head>
<body>
<div id="hud">
  <div class="panel" id="speedPanel">
    <div class="big" id="speedVal">0</div><div class="unit">KM/H</div>
  </div>
  <div class="panel" id="lapPanel">LAP <span id="lapVal">1</span>/3</div>
  <div class="panel" id="posPanel"><span id="posVal">1st</span></div>
</div>
<script type="importmap">...</script>  <!-- provided, do not add -->
```
The instructions say an import map is provided — so I should NOT add my own. Just use the import statement. OK, so no import map in my file. Right, "An import map is provided for you: do not add your own import map". So I just write `import * as THREE from 'three';`.

Now writing everything.

Let me write the JS carefully.

```js
import * as THREE from 'three';

// ---------- Renderer ----------
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0xbfd8ef, 260, 900);

const camera = new THREE.PerspectiveCamera(62, window.innerWidth/window.innerHeight, 0.5, 3000);
```

Shadows: with 4 cars and instanced trees, shadow maps could be slow but okay. Let's enable shadows only for the directional light with a tight shadow camera around the player? Since the player moves, the shadow camera needs to follow. Simple: attach the directional light to a target following the player. Might be more complex than needed. Let's disable shadows and instead use a fake shadow (dark circle under each car) and rely on ambient occlusion-ish look. Actually shadows add a lot... but a moving shadow camera is easy: set light.position = player.position + offset, light.target.position = player.position, and update matrix. Let's do that with a shadow camera of ±60.

Actually let's keep it simpler and disable shadows for reliability. Hmm. I'll enable them — it looks much better. With shadow map size 2048 and a ±80 ortho camera following the player. Cars cast shadows, trees receive... Actually trees are instanced; they can cast shadows too. Let's have grass receive shadows and cars cast.

Risk: performance. It's a small scene. Should be fine.

Let me do it.

Directional light:
```js
const sun = new THREE.DirectionalLight(0xfff3d6, 2.2);
sun.position.set(80, 140, 60);
sun.castShadow = true;
sun.shadow.mapSize.set(2048,2048);
sun.shadow.camera.left = -90; right 90; top 90; bottom -90; near 1; far 400;
scene.add(sun); scene.add(sun.target);
```
Each frame: sun.position.copy(player.position).add(offset); sun.target.position.copy(player.position); sun.target.updateMatrixWorld();

Hemisphere light: `new THREE.HemisphereLight(0x9fd2ff, 0x3d6b2c, 1.1)`.

Ambient boost.

Sky sphere and fog color should match.

OK writing now for real.

```js
// ---------- Sky ----------
const skyMat = new THREE.ShaderMaterial({
  uniforms: {
    topColor: { value: new THREE.Color(0x2b6bd6) },
    botColor: { value: new THREE.Color(0xd9ecff) },
    offset: { value: 120 },
    exponent: { value: 0.75 }
  },
  vertexShader: `
    varying vec3 vWorldPosition;
    void main(){
      vec4 wp = modelMatrix * vec4(position, 1.0);
      vWorldPosition = wp.xyz;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0);
    }`,
  fragmentShader: `
    uniform vec3 topColor; uniform vec3 botColor; uniform float offset; uniform float exponent;
    varying vec3 vWorldPosition;
    void main(){
      float h = normalize(vWorldPosition + vec3(0.0, offset, 0.0)).y;
      float f = pow(max(h, 0.0), exponent);
      gl_FragColor = vec4(mix(botColor, topColor, f), 1.0);
    }`,
  side: THREE.BackSide,
  depthWrite: false
});
const sky = new THREE.Mesh(new THREE.SphereGeometry(1500, 32, 16), skyMat);
scene.add(sky);
```
Sky follows camera? With radius 1500 and camera far 3000, and the track spanning ~400 units, the camera stays within the sphere. Good.

Fog: color 0xc8ddf0, near 300 far 1200. Hmm, with the sky sphere being affected by fog? ShaderMaterial without fog uniforms isn't affected. Good.

Now the track curve and geometry.

I'll write the whole thing and then mentally check.

Let me write out the full file.

```js
// ---------- Track ----------
const trackPoints = [
  [   0, -175], [ 110, -195], [ 190, -125], [ 185,  -25],
  [ 115,   45], [ 135,  125], [  60,  180], [ -45,  170],
  [ -95,  105], [-175,   85], [-205,  -15], [-150,  -90],
  [-125, -165], [ -60, -200]
].map(([x,z]) => new THREE.Vector3(x, 0, z));

const curve = new THREE.CatmullRomCurve3(trackPoints, true, 'catmullrom', 0.5);
curve.arcLengthDivisions = 2000;
const L = curve.getLength();
const HALF_W = 8;
```

Road mesh:

```js
const SEG = 800;
const roadGeo = new THREE.BufferGeometry();
const rPos = new Float32Array((SEG+1)*2*3);
const rUV = new Float32Array((SEG+1)*2*2);
const rIdx = [];
for (let i=0;i<=SEG;i++){
  const u = (i % SEG) / SEG;
  const p = curve.getPointAt(u);
  const t = curve.getTangentAt(u);
  const side = new THREE.Vector3(-t.z, 0, t.x).normalize();
  const a = p.clone().addScaledVector(side, -HALF_W);
  const b = p.clone().addScaledVector(side,  HALF_W);
  a.y = b.y = 0.02;
  const o = i*6;
  rPos[o] = a.x; rPos[o+1] = a.y; rPos[o+2] = a.z;
  rPos[o+3] = b.x; rPos[o+4] = b.y; rPos[o+5] = b.z;
  const uv = i*4;
  rUV[uv] = 0; rUV[uv+1] = i*0.5;
  rUV[uv+2] = 1; rUV[uv+3] = i*0.5;
  if (i < SEG) {
    const k = i*2;
    rIdx.push(k, k+1, k+2, k+1, k+3, k+2);
  }
}
```

Wait for i = SEG, u = 0 which equals the start point, so the last row duplicates the first row. Good, and we don't add indices for it.

Hmm, `(i % SEG) / SEG` for i=SEG gives 0. Good.

Note: getPointAt(0) and getPointAt(1) should be the same point for a closed curve. Yes.

Asphalt texture: canvas.

```js
function makeAsphaltTexture(){
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#3a3d42';
  ctx.fillRect(0,0,128,128);
  for (let i=0;i<4000;i++){
    const x = Math.random()*128, y = Math.random()*128;
    const g = 40 + Math.random()*50;
    ctx.fillStyle = `rgba(${g},${g},${g+3},0.5)`;
    ctx.fillRect(x,y,1.5,1.5);
  }
  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  return tex;
}
```
UV v goes i*0.5 → 800*0.5 = 400 repeats along the length. The texture will be compressed but it's noise anyway. Actually 400 repeats over ~1200 units means each tile is 3 units. That's a big noise scale — fine.

Hmm, but wrapS with uv.x from 0..1 across 16 units — the noise gets stretched. It's fine; it's random noise.

Kerbs: build a non-indexed geometry.

```js
function buildKerb(sideSign) {
  const positions = [], colors = [], uvs = [];
  const inner = HALF_W, outer = HALF_W + 1.3;
  for (let i=0;i<SEG;i++){
    const u0 = i/SEG, u1 = (i+1)/SEG;
    const p0 = curve.getPointAt(u0), p1 = curve.getPointAt(u1);
    const t0 = curve.getTangentAt(u0), t1 = curve.getTangentAt(u1);
    const s0 = new THREE.Vector3(-t0.z,0,t0.x).normalize();
    const s1 = new THREE.Vector3(-t1.z,0,t1.x).normalize();
    const A0 = p0.clone().addScaledVector(s0, sideSign*inner);
    const B0 = p0.clone().addScaledVector(s0, sideSign*outer);
    const A1 = p1.clone().addScaledVector(s1, sideSign*inner);
    const B1 = p1.clone().addScaledVector(s1, sideSign*outer);
    A0.y = B0.y = A1.y = B1.y = 0.07;
    const col = (Math.floor(i/4) % 2 === 0) ? [1,0.15,0.15] : [0.95,0.95,0.95];
    // triangles
    ...
  }
}
```
Each segment: 2 triangles = 6 vertices, all with the same color.

Order for correct winding — I'll just use DoubleSide for kerbs to be safe. Same for road actually? Road: let's keep FrontSide with correct winding as computed. I'll test mentally.

Actually, using `side: THREE.DoubleSide` on the road is safest and the perf cost is negligible. I'll do that for road and kerb. Hmm, but shadows with DoubleSide... fine, no shadows cast on the road mesh.

Let me just do DoubleSide for road and kerbs. Simplifies.

Start/finish line: use a canvas checker texture.

```js
function makeCheckerTexture(){
  const c = document.createElement('canvas');
  c.width = 64; c.height = 16;
  const ctx = c.getContext('2d');
  for (let y=0;y<2;y++) for (let x=0;x<16;x++){
    ctx.fillStyle = ((x+y)%2===0) ? '#ffffff' : '#111111';
    ctx.fillRect(x*4, y*8, 4, 8);
  }
  ...
}
```
Plane 16 wide x 3 deep with the texture. Since the plane's local Y (3 units) maps to the Z depth, and texture v goes along the height... 16 columns across the width and 2 rows deep. Fine.

Also add start gantry? Skip. Maybe a simple pair of posts + a banner at the start line. Nice touch but optional. I'll add two red posts and a banner box. Eh — keep it. Actually, it adds "arcade" feel. Let's add a simple gantry: two boxes at ±(HALF_W+1.5) and a horizontal box spanning across at height 7. Cheap. Yes.

Trees: instanced.

```js
function placeProps(){
  const treeCount = 140;
  const trunkGeo = new THREE.CylinderGeometry(0.25, 0.45, 3, 6);
  const trunkMat = new THREE.MeshStandardMaterial({color:0x6b4a2b, roughness:0.9});
  const leafGeo = new THREE.ConeGeometry(2.6, 6, 8);
  const leafMat = new THREE.MeshStandardMaterial({color:0x2f7a35, roughness:0.9, flatShading:true});
  ...
}
```
Using InstancedMesh with dummy Object3D.

Position rejection: sample random points in [-500,500]^2, check distance to nearest of `centerSamples` (I'll build an array of ~200 track sample points) must be > HALF_W + 7. Also check the point is not too far (within 500).

Also add buildings: 20 boxes, distance > 60 from track.

Let me build `trackSamples` array of Vector3 for distance checks.

Now cars.

Let me write createCar:

```js
function createCar(colorHex, isPlayer){
  const car = new THREE.Group();

  const bodyMat = new THREE.MeshStandardMaterial({ color: colorHex, metalness: 0.55, roughness: 0.3 });
  const darkMat = new THREE.MeshStandardMaterial({ color: 0x14161a, metalness: 0.5, roughness: 0.55 });
  const glassMat = new THREE.MeshStandardMaterial({ color: 0x9fd8ff, metalness: 1.0, roughness: 0.08, transparent: true, opacity: 0.6 });
  const lightMat = new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xffffcc, emissiveIntensity: 1.4, roughness:0.3 });
  const tailMat = new THREE.MeshStandardMaterial({ color: 0x330000, emissive: 0xff2200, emissiveIntensity: 1.2 });

  const visual = new THREE.Group();
  car.add(visual);

  // chassis
  const chassis = new THREE.Mesh(new THREE.BoxGeometry(1.9, 0.55, 3.9), bodyMat);
  chassis.position.y = 0.62;
  visual.add(chassis);

  // lower skirt
  const skirt = new THREE.Mesh(new THREE.BoxGeometry(1.95, 0.28, 3.6), darkMat);
  skirt.position.y = 0.33;
  visual.add(skirt);

  // nose
  const nose = new THREE.Mesh(new THREE.BoxGeometry(1.7, 0.34, 1.0), bodyMat);
  nose.position.set(0, 0.5, 2.35);
  visual.add(nose);

  // cockpit
  const cockpit = new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.55, 1.8), glassMat);
  cockpit.position.set(0, 1.12, -0.25);
  visual.add(cockpit);

  // roof
  const roof = new THREE.Mesh(new THREE.BoxGeometry(1.35, 0.12, 1.3), bodyMat);
  roof.position.set(0, 1.4, -0.35);
  visual.add(roof);

  // rear deck
  const deck = new THREE.Mesh(new THREE.BoxGeometry(1.8, 0.3, 1.0), bodyMat);
  deck.position.set(0, 0.95, -1.85);
  visual.add(deck);

  // spoiler
  const wing = new THREE.Mesh(new THREE.BoxGeometry(1.85, 0.09, 0.55), darkMat);
  wing.position.set(0, 1.35, -2.35);
  visual.add(wing);
  for (const sx of [-0.7, 0.7]) {
    const strut = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.4, 0.12), darkMat);
    strut.position.set(sx, 1.15, -2.3);
    visual.add(strut);
  }

  // headlights
  for (const sx of [-0.58, 0.58]) {
    const hl = new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.16, 0.1), lightMat);
    hl.position.set(sx, 0.6, 2.86);
    visual.add(hl);
  }
  // taillights
  for (const sx of [-0.62, 0.62]) {
    const tl = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.16, 0.1), tailMat);
    tl.position.set(sx, 0.78, -2.62);
    visual.add(tl);
  }

  // wheels
  const wheels = [];
  const tireMat = new THREE.MeshStandardMaterial({color:0x1b1b1f, roughness:0.95});
  const rimMat = new THREE.MeshStandardMaterial({color:0xc8ccd4, metalness:0.9, roughness:0.25});
  const wheelDefs = [[-0.95, 1.35],[0.95,1.35],[-0.95,-1.5],[0.95,-1.5]];
  for (const [wx, wz] of wheelDefs){
    const wg = new THREE.Group();
    wg.position.set(wx, 0.45, wz);
    const tire = new THREE.Mesh(new THREE.CylinderGeometry(0.45,0.45,0.34,16), tireMat);
    tire.rotation.z = Math.PI/2;
    wg.add(tire);
    const rim = new THREE.Mesh(new THREE.CylinderGeometry(0.24,0.24,0.36,10), rimMat);
    rim.rotation.z = Math.PI/2;
    wg.add(rim);
    const spoke = new THREE.Mesh(new THREE.BoxGeometry(0.38, 0.78, 0.09), rimMat);
    wg.add(spoke);
    const spoke2 = new THREE.Mesh(new THREE.BoxGeometry(0.38, 0.09, 0.78), rimMat);
    wg.add(spoke2);
    visual.add(wg);
    wheels.push(wg);
  }
  ...
}
```
Wait, the spoke boxes: the wheel face plane is YZ. A box of (0.38 x, 0.78 y, 0.09 z) is a vertical bar across the wheel face. Good. The second: (0.38, 0.09, 0.78) horizontal bar. Together a cross. Good.

Hmm, but front wheels should steer. Add steering by rotating wheel group about Y. But we also rotate about X for spin. If we set rotation order... Use a nested group: steerGroup (rotation.y) → spinGroup (rotation.x). Let's do that for the front wheels.

Simplify: create wheel groups as `steer` groups, and inside a `spin` group. wheels array holds spin groups; steerWheels array holds steer groups.

Also add a fake shadow: a dark plane under the car. `CircleGeometry` scaled, material transparent black, rotation.x=-PI/2, y=0.03. Actually with real shadows enabled, skip.

Since I'm enabling shadows, set castShadow on the car meshes.

Let's iterate over `visual.children`... some are groups. Use traverse.

```js
car.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = false; } });
```
That sets castShadow on ~20 meshes per car. Shadow rendering cost: 4 cars × 20 meshes × 2 (shadow + main) = fine.

OK.

Now RaceCar class.

```js
class Racer {
  constructor(opts){
    this.color = opts.color;
    this.isPlayer = !!opts.isPlayer;
    this.skill = opts.skill;      // speed multiplier
    this.bias = opts.bias;        // preferred lateral offset
    this.dist = opts.dist;
    this.lateral = opts.lateral;
    this.targetLateral = opts.lateral;
    this.speed = 20;
    this.maxSpeed = 74 * this.skill;
    this.maxLatAccel = 78;
    this.accelRate = 28;
    this.brakeRate = 55;
    this.lap = 1;
    this.roll = 0;
    this.pitch = 0;

    const built = createCar(opts.color);
    this.mesh = built.group;
    this.visual = built.visual;
    this.spinWheels = built.spinWheels;
    this.steerWheels = built.steerWheels;
    scene.add(this.mesh);
    this.place();
  }
  ...
}
```

`place()`: compute u from dist, get point/tangent, set position, lookAt ahead point.

```js
place(dt){
  const u = ((this.dist / L) % 1 + 1) % 1;
  const p = curve.getPointAt(u);
  const t = curve.getTangentAt(u);
  const side = new THREE.Vector3(-t.z, 0, t.x).normalize();
  this.mesh.position.copy(p).addScaledVector(side, this.lateral);
  this.mesh.position.y = 0;

  const uAhead = (u + 6 / L) % 1;
  const pA = curve.getPointAt(uAhead);
  const tA = curve.getTangentAt(uAhead);
  const sideA = new THREE.Vector3(-tA.z, 0, tA.x).normalize();
  const look = pA.clone().addScaledVector(sideA, this.lateral);
  look.y = 0;
  this.mesh.lookAt(look);
}
```
Careful: `lookAt` with the up vector (0,1,0) — since the car and look are both at y=0, the direction is horizontal, no gimbal issues. Good.

But there's a subtlety: if the car position and look position are identical (they won't be, 6 units apart), fine.

Roll: the visual group rotation.z. Set from curvature: `this.roll = -curv * speed * speed * 0.0008` clamp. Actually roll should be applied relative to the car's local frame. visual.rotation.z = roll. Positive roll... let's just pick something and it'll look fine either way. Let's use `roll = THREE.MathUtils.clamp(curvSigned * this.speed * 0.012, -0.18, 0.18)`. Hmm, I need signed curvature. Instead, use lateral acceleration = the change of heading. Let's just compute from the tangent change with sign using cross product:

Actually simpler: use the steering-like proxy = (targetLateral - lateral) not great. Let me compute signed curvature:

```js
const u = ...;
const t0 = curve.getTangentAt(u), t1 = curve.getTangentAt((u+0.005)%1);
const crossY = t0.x * t1.z - t0.z * t1.x;   // y component of t0 × t1
```
t0 × t1 y-component = t0.z*t1.x - t0.x*t1.z. Let me just define `const signed = t0.x*t1.z - t0.z*t1.x;` and the sign just flips the roll direction; I'll pick visually. Since I can't visually check, let me reason: if the car turns left, it should roll to the right (outward).

Hmm. Let's derive. t0 = (1,0,0) (heading +X), then turning left (toward +Z? in three.js with Y up, a left turn from +X heading is toward -Z... let's see: facing +X, up +Y, left is... right-handed: forward × up = right? forward=(1,0,0), up=(0,1,0), right = forward × up = (0*0-0*1, 0*0-1*0, 1*1-0*0) = (0,0,1). So right is +Z, left is -Z.

Car turning left: t1 = (1, 0, -ε) roughly. 
signed = t0.x*t1.z - t0.z*t1.x = 1*(-ε) - 0 = -ε. Negative for a left turn.

When turning left, the car body rolls to the right, i.e. rotation about the local Z axis... The car's local Z is forward. Rolling right means the top tilts toward the car's right, which is local +X... rotation about local Z (forward axis) by angle φ: local +Y (up) rotates toward local -X? Rotation about +Z by φ: (x,y) → (x cosφ - y sinφ, x sinφ + y cosφ). Point (0,1,0) → (-sinφ, cosφ, 0). So for φ>0, up tilts toward -X = car's left. Hmm wait, which is the car's left in local coords? Local forward is +Z, up is +Y, so right = forward × up = (0,0,1)×(0,1,0) = (0*0-1*1, 1*0-0*0, 0*1-0*0) = (-1, 0, 0). So local right is -X!

Hmm, that's because the car model faces +Z. Let me double check with the standard: in three.js the camera looks along -Z, so its right is +X, up +Y. For an object facing +Z, right = forward × up: (0,0,1) × (0,1,0) = determinant:
i (0*0 - 1*1) - j (0*0 - 1*0) + k (0*1 - 0*0) = (-1, 0, 0). Yes, right = -X.

Hmm, but that's for a left-handed... whatever, it's the math.

So rolling right = up tilts toward local -X (which is right). From the rotation formula, up (0,1,0) rotates to (-sinφ, cosφ, 0). For it to tilt toward -X we need -sinφ < 0, i.e., sinφ > 0, φ > 0.

So for a left turn (signed < 0), we want φ > 0. So φ = -signed * k. Great: `roll = -signed * speedFactor`.

Whatever, if I got the sign wrong it's a subtle visual. Let's just do it.

Actually, hmm, I realize I should double check that the car's "forward" is +Z after lookAt. Object3D.lookAt for non-camera orients +Z toward the target. Yes, verified earlier from the source. Good.

And wheels: front wheels at z = +1.35 (front). Good, consistent.

Now the update loop:

```js
update(dt, all){
  const u = ((this.dist / L) % 1 + 1) % 1;

  // --- speed target from curvature ahead ---
  let vTarget = this.maxSpeed;
  for (let d = 0; d < 90; d += 9) {
    const cu = (u + d / L) % 1;
    const c = curvAt(cu);
    const vC = Math.sqrt(this.maxLatAccel / Math.max(c, 0.0008));
    const allowed = Math.sqrt(vC*vC + 2 * this.brakeRate * d);
    if (allowed < vTarget) vTarget = allowed;
  }
  ...
}
```
Hmm, `vTarget` should also be capped by maxSpeed. Yes it starts at maxSpeed.

But this includes d=0 which gives the corner speed right now — if the car is already in a corner going too fast, the target is much lower and it brakes hard. Fine.

Then apply the overtaking modifiers.

Then:
```js
  const dv = vTarget - this.speed;
  if (dv > 0) this.speed += Math.min(dv, this.accelRate * dt);
  else this.speed += Math.max(dv, -this.brakeRate * dt);
  this.speed = Math.max(this.speed, 5);
```

Then `this.dist += this.speed * dt;`

Lap: `const newLap = Math.floor(this.dist / L) + 1;` — but dist starts positive and grows, so lap starts at 1 and becomes 2 after L. Cap at 3. When the race is done... just keep going. For the HUD, show `Math.min(lap, 3)`.

Position: rank by dist.

Overtaking logic (do it before the speed update, modifying vTarget and targetLateral):

```js
let avoid = null;
let bestGap = Infinity;
for (const other of all) {
  if (other === this) continue;
  let gap = other.dist - this.dist;
  gap = ((gap % L) + L) % L;
  if (gap < 20 && gap < bestGap) { bestGap = gap; avoid = other; }
}
if (avoid && bestGap < 20) {
  const dl = avoid.lateral - this.lateral;
  if (Math.abs(dl) < 3.6) {
    const dir = dl >= 0 ? -1 : 1;
    this.targetLateral = THREE.MathUtils.clamp(avoid.lateral + dir * 4.5, -MAXLAT, MAXLAT);
    // if the target is clamped to the same as now, try the other side
    if (Math.abs(this.targetLateral - this.lateral) < 1.0) {
      this.targetLateral = THREE.MathUtils.clamp(avoid.lateral - dir * 4.5, -MAXLAT, MAXLAT);
    }
  }
  if (bestGap < 10) vTarget = Math.min(vTarget, avoid.speed * (0.85 + bestGap*0.03));
}
```

Hmm the fallback: if the clamped target is basically where we are, try the other side. Good.

Else: `this.targetLateral = this.bias + Math.sin(u * Math.PI * 2 * 3) * 1.0;` Hmm, the racing line. Actually a sinusoid of u with 3 cycles gives a nice weaving line. But that could look like the car is drunk. Let's keep bias constant with a mild apex-hunting: `this.targetLateral = this.bias;` Simple and clean. Different cars have different biases, which leads to natural overtaking on straights.

MAXLAT = HALF_W - 2 = 6. Car half-width ~1, so at lateral 6 the car edge is at 7, and the track edge is at 8. Good.

Lateral movement rate: `this.lateral += clamp(target - lateral, -12*dt, 12*dt)` → moves 12 units/sec. Fine.

Then place the car.

Also, add a small idle "engine" wobble? No.

Now the wheel spin: `spinAngle += speed/0.45 * dt`.

Steering visual: front wheels steer based on the change in lateral target... `steerAngle = clamp((targetLateral - lateral) * 0.15, -0.5, 0.5)`. Nice.

Camera: as described.

HUD update every frame.

Race positions: sort a copy of cars by dist desc; find player index.

Position suffix: 1st, 2nd, 3rd, 4th.

Let's also add a "LAP X/3" and when the player finishes 3 laps... just keep driving, display stays at 3/3.

Let me now also think about the initial camera placement so the first frame isn't jarring. Set camera behind the player at init.

Now let's think about framing the "first 30 seconds" — everything is visible immediately: the player car, rivals ahead, HUD, track, trees. Good.

Now, the curvature array indexing: `curvAt(u)` where u ∈ [0,1). Precompute with the same rounding.

Let me write it.

One more consideration: `curve.getPointAt(u)` for a closed CatmullRomCurve3 — `getPointAt` uses `getUtoTmapping` based on arc lengths. Fine.

Performance: getPointAt/getTangentAt call getLengths which is cached after the first call. Called ~5 times per car per frame + camera. 4 cars × 4 = 16 calls/frame. Fine.

Let's write out the code.

Also, I should double-check `curve.getTangentAt(u)` for u=0 on a closed curve. Should be fine.

Let me write the final code.

```js
// ---------- init scene ----------
...
// ---------- track ----------
...
// ---------- props ----------
...
// ---------- cars ----------
...
// ---------- loop ----------
```

Detailed code:

```js
const clockStart = performance.now();
let lastTime = 0;

function animate(now) {
  requestAnimationFrame(animate);
  if (!lastTime) lastTime = now;
  let dt = (now - lastTime) / 1000;
  lastTime = now;
  dt = Math.min(dt, 1/30);

  for (const c of racers) c.update(dt, racers);
  for (const c of racers) c.place();

  updateCamera(dt);
  updateHUD();
  updateSun();

  renderer.render(scene, camera);
}
requestAnimationFrame(animate);
```

Hmm — I should separate the physics update from the place. Actually place() needs to be after the update. But update uses `other.dist` and `other.lateral` which are scalars updated in the update step. Fine. Then place all.

Order in update: I'll have `update(dt, all)` do both the physics and the positioning. But then the car that runs first sees the stale positions of the others — negligible.

Let me keep physics in update and call place separately after all updates. Cleaner.

Now the camera:

```js
const camPos = new THREE.Vector3();
const camLook = new THREE.Vector3();
let camInit = false;

function updateCamera(dt) {
  const car = player.mesh;
  const fwd = new THREE.Vector3(0,0,1).applyQuaternion(car.quaternion);
  const speed = player.speed;
  const back = 9 + speed * 0.11;
  const height = 3.6 + speed * 0.012;

  const desired = car.position.clone().addScaledVector(fwd, -back);
  desired.y = car.position.y + height;

  const lookTarget = car.position.clone().addScaledVector(fwd, 12);
  lookTarget.y = car.position.y + 1.4;

  if (!camInit) { camPos.copy(desired); camLook.copy(lookTarget); camInit = true; }

  const k = 1 - Math.exp(-7 * dt);
  camPos.lerp(desired, k);
  camLook.lerp(lookTarget, 1 - Math.exp(-10*dt));

  // small shake
  const t = performance.now() * 0.001;
  camera.position.copy(camPos);
  camera.position.y += Math.sin(t*23)*0.02*speed*0.05;
  camera.lookAt(camLook);

  const targetFov = 62 + speed * 0.28;
  camera.fov += (targetFov - camera.fov) * (1 - Math.exp(-4*dt));
  camera.updateProjectionMatrix();
}
```
Hmm, fov 62 + 74*0.28 = 82.7 at top speed. That's quite wide, gives a good speed feel.

Careful: camera should not go below the grass. y is at least 3.6-ish. Fine.

Also, if the car is on a slope — no slopes. Fine.

Let's write `updateHUD`:
```js
const speedEl = ..., lapEl, posEl;
function updateHUD(){
  speedEl.textContent = Math.round(player.speed * 3.6);
  lapEl.textContent = Math.min(player.lap, TOTAL_LAPS);
  posEl.textContent = ordinal(pos) + suffix...
}
```
HUD "LAP 1/3".

Now the ordering of positions.

```js
const order = racers.slice().sort((a,b)=> b.dist - a.dist);
const idx = order.indexOf(player);
const posStr = ['1st','2nd','3rd','4th'][idx];
```

Now let's write everything out.

One more thing: the start line gantry.

Also maybe add a few "track markers" — barrels/cones? Skip.

Let me write the final code.

Regarding the grass plane and fog: fog near 260 far 900 with a 3000x3000 plane means the ground fades into the fog color which should match the horizon sky color (0xd9ecff-ish). Set fog color to 0xcfe3f5.

Let me finalize colors:
- sky top: 0x2a6fd4, bottom: 0xcfe6ff
- fog: 0xcfe6ff

Lighting: hemisphere(0xbfe0ff, 0x4a7a35, 0.9), directional 0xfff0d0 intensity 2.0.

With THREE r186, the default color management is on (renderer.outputColorSpace = SRGB by default). Intensities: directional light 2.0 is fine with physically correct lighting? In r155+, `useLegacyLights` was removed and lights use physical units. DirectionalLight intensity 2-3 works. I'll use 2.2 for the sun and 1.2 for the hemisphere.

Renderer tone mapping: use ACESFilmic? That would darken. Let's use `THREE.NoToneMapping` default, or ACES with exposure 1.1. I'll skip tone mapping to keep colors punchy.

OK. Writing final answer now.

Actually one concern: `MeshStandardMaterial` with metalness 0.55 and roughness 0.3 without an environment map looks dark/black. Since there's no env map, metallic surfaces appear dark. Better to use low metalness (0.1-0.2) and moderate roughness, relying on diffuse. Or add a simple environment map via PMREMGenerator from the sky scene. That's extra complexity but makes cars look great.

Simple alternative: use `metalness: 0.2, roughness: 0.45` for car bodies. And glass with metalness 0.0 and a light blue color with opacity. That'll look fine.

Actually, I can cheaply generate an env map: create a scene with the sky shader and use PMREMGenerator.fromScene(). Let's do it — it's a few lines and improves everything.

```js
const pmrem = new THREE.PMREMGenerator(renderer);
const envScene = new THREE.Scene();
envScene.add(new THREE.Mesh(new THREE.SphereGeometry(100, 16, 8), skyMat.clone()));
const envRT = pmrem.fromScene(envScene, 0.04);
scene.environment = envRT.texture;
```
Hmm, `fromScene` needs the material with side BackSide. Cloning the shader material works. Then dispose.

This is nice: the cars get reflections. Let's include it. But careful about `pmrem.fromScene` requiring the camera... it handles it.

Actually, could just use `scene.environment = envRT.texture` which applies to all standard materials. Road would also get a slight reflection — with roughness 0.9 it's subtle. Fine.

Set `scene.environmentIntensity = 0.7` (r165+ supports scene.environmentIntensity). In r186 it exists. OK, I'll set it to 0.8.

Hmm, is `environmentIntensity` a Scene property? Yes, added in r163. Safe.

Let's write it.

Final concern about performance of 4 cars × 20 meshes with shadows: ~80 shadow draw calls + 80 main. Plus the road, kerbs, trees (2 instanced), buildings, grass, sky. ~180 draw calls. Fine.

Actually, let's reduce: set castShadow only on the main body meshes? Simpler to just traverse. It's fine.

Now writing.

For the trees' instanced mesh, `castShadow = true` and `receiveShadow`... trees casting shadows on the grass requires the shadow camera to cover them, but the shadow camera follows the player with ±90 extent. Trees within that range cast shadows. Good.

Hmm, but if the shadow camera follows the player, the sun position must also update. Let me set:

```js
function updateSun(){
  const p = player.mesh.position;
  sun.position.set(p.x + 80, 140, p.z + 60);
  sun.target.position.copy(p);
  sun.target.updateMatrixWorld();
  sun.shadow.camera.updateProjectionMatrix(); // not needed unless changed
}
```
Since the light is directional, its position only matters for the shadow camera. The shadow camera's ortho box is centered on the light's position looking at the target. With near=1, far=400, and the light at distance ~170 from the target, that covers it.

OK. Writing now.

One more: `sun.shadow.bias = -0.0005` to avoid acne.

Writing the final HTML.

Let me carefully write the kerb builder with DoubleSide.

```js
function buildKerb(sign){
  const positions = [];
  const colors = [];
  const inner = HALF_W;
  const outer = HALF_W + 1.4;
  const y = 0.075;
  for (let i = 0; i < SEG; i++) {
    const u0 = i / SEG, u1 = (i + 1) / SEG;
    const p0 = curve.getPointAt(u0), p1 = curve.getPointAt(u1);
    const t0 = curve.getTangentAt(u0), t1 = curve.getTangentAt(u1);
    const s0 = new THREE.Vector3(-t0.z, 0, t0.x).normalize();
    const s1 = new THREE.Vector3(-t1.z, 0, t1.x).normalize();
    const a0 = p0.clone().addScaledVector(s0, sign * inner); a0.y = y;
    const b0 = p0.clone().addScaledVector(s0, sign * outer); b0.y = y;
    const a1 = p1.clone().addScaledVector(s1, sign * inner); a1.y = y;
    const b1 = p1.clone().addScaledVector(s1, sign * outer); b1.y = y;
    const c = (Math.floor(i / 5) % 2 === 0)
      ? [0.85, 0.10, 0.10]
      : [0.95, 0.95, 0.95];
    positions.push(a0.x,a0.y,a0.z, b0.x,b0.y,b0.z, a1.x,a1.y,a1.z);
    positions.push(b0.x,b0.y,b0.z, b1.x,b1.y,b1.z, a1.x,a1.y,a1.z);
    for (let k = 0; k < 6; k++) colors.push(c[0], c[1], c[2]);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
  g.computeVertexNormals();
  return g;
}
```
800 segments × 2 kerbs × 6 verts = 9600 verts. Fine.

Material: `new THREE.MeshStandardMaterial({vertexColors: true, roughness: 0.8, side: THREE.DoubleSide})`.

Ok, writing everything now for real.

Also need to double check: `curve.getTangentAt` on a curve where u is exactly 1 → returns tangent at 1. We use u1 = (i+1)/SEG which for i = SEG-1 is 1. Fine.

Great, let's write.

For the checker start line, I need `THREE.CanvasTexture` with `colorSpace = THREE.SRGBColorSpace`.

Also for the asphalt and grass textures, set colorSpace SRGB.

Let me write it all out.

Final code:

I'll also add a subtle guard: `renderer.setAnimationLoop` vs requestAnimationFrame — the requirement says use requestAnimationFrame with timestamps. Use rAF.

Writing now.

Let me also make sure the HUD is styled nicely — a speed panel bottom-left, lap top-center, position top-right, maybe with a semi-transparent dark background and rounded corners.

Let me produce the final file.