We need to create a single self-contained HTML file with three.js from import map (provided by environment). We must not add our own import map. So we just use `import * as THREE from 'three'`.

Let me design the whole thing.

Key components:
1. City generation: grid of streets, blocks with buildings. Use instanced or merged geometry for perf. Let's do a grid of e.g. 8x8 blocks, each block ~40 units, roads ~12 units wide. Total ~ 400x400 city.
2. Roads: draw as ground plane with dark color, plus lane markings. Simpler: a big plane with dark asphalt, and block interiors as sidewalks/parks with lighter concrete. Actually easier: build road plane covering everything as asphalt, then place "block" meshes (sidewalk slabs with buildings on top).
3. Buildings: box geometry with varied heights/colors, using vertex-colored materials or per-building color. Use InstancedMesh with per-instance color for perf. Windows via emissive texture? We can procedurally generate a canvas texture for facades — but "no images" refers to external resources; canvas-generated textures are fine. Let's generate a window texture with canvas for facades. That gives nice variety.
4. Street furniture: street lights (poles with light cone), traffic lights at intersections, trees in parks, benches. Keep it moderate.
5. Traffic: cars driving along lanes, obeying traffic lights at intersections. Simple approach: each car follows a lane path (grid-based roads), moves along, stops when light is red ahead. Use a graph of road nodes: intersections on a grid; cars travel between adjacent intersections along lane offsets.
6. Pedestrians: walk along sidewalks, simple loop paths around blocks.
7. Hero car: follows a route (random waypoints at intersections), uses same lane graph, brakes for lights, overtakes (if car ahead slow, shift lane?), drifts on corners (visual: extra yaw, tire marks maybe).
8. Chase camera + cinematic angles switching occasionally.
9. Day-night cycle: sky color changes, sun directional light moves, street lights turn on at night (emissive + point lights limited).
10. Wanted level: police cars spawn and pursue hero. Increase wanted level over time / when collisions.
11. Minimap: 2D canvas overlay in corner showing streets grid and cars.
12. HUD: speed.

Performance: keep counts moderate: ~40 traffic cars, ~60 pedestrians, ~10 police, buildings ~400 instanced.

Let me think about the road graph.

Grid: N = 7 roads each direction? Let's define:
- GRID = 8 blocks across, block size B = 44, road width W = 14.
- Positions: road center lines at x = i*(B+W) for i in 0..GRID. So city spans from 0 to GRID*(B+W) = 8*58 = 464.

Let's just use coordinates centered later, or just work in world coords 0..464 and offset the whole city by -232.

Lane offsets: each road has two lanes, offset ±3.5 from center.

Traffic driving on right side (like US): driving in +x direction uses lane at +z offset? Let's define: for a car travelling in +X direction, it keeps to the right side, which is... if +X is east and +Z is south (in three.js, X right, Z toward viewer), hmm. Let's just pick: travelling +X → offset in +Z; travelling -X → offset -Z; travelling +Z → offset -X; travelling -Z → offset +X. That's consistent with right-hand traffic if Y is up and we consider... whatever, consistency is what matters: on a two-lane road, opposing traffic separated. Check consistency: For +X direction, right side of a driver facing +X: right hand points to... In three.js, X right, Y up, Z out of screen toward viewer. Facing +X, up is +Y, right = forward × up? Actually right = forward cross up? For a right-handed coordinate system, right = forward × up gives... let's compute: forward=(1,0,0), up=(0,1,0). forward × up = (1,0,0)×(0,1,0) = (0*0-0*1, 0*0-1*0, 1*1-0*0) = (0,0,1). So right = +Z. Good, so travelling +X keeps offset +Z. Travelling +Z: forward=(0,0,1), right = (0,0,1)×(0,1,0) = (0*0-1*1, 1*0-0*0, 0*1-0*0)= (-1,0,0). So offset -X. Consistent with what I said. Good.

So lane offset for direction d: offsetVec = right(d) * 3.5.

Cars travel between intersections. At each intersection node (i,j) meaning road index i in x, j in z. Node position: x = i*S, z = j*S where S = B+W.

A car's state: current node (i,j), direction dir (one of +X,-X,+Z,-Z), progress. It moves along the segment from current node to next node. At the end, it picks a new direction (not reverse, and must stay in bounds). Then it continues.

Position = lerp between nodes + lane offset perpendicular.

Traffic light: at each intersection, cycle phases. Let's give each intersection a phase offset based on (i+j)%2, with cycle 10 seconds: NS green for 5, EW green for 5. Actually simpler: greenNS = ((t*0.5 + (i+j)*0.25) % 1) < 0.5.

Car checks: distance to next intersection. If within braking distance and light for its direction is red, decelerate to stop at stop line (before intersection, e.g. 6 units before node).

Also car-to-car: check car ahead in same lane segment, slow down.

That's a decent amount of logic. Let's keep it O(n²) over ~50 cars = 2500 checks per frame — fine.

Hero car: same movement but higher speed, more aggressive, with drift on corners. Also overtaking: if blocked, temporarily offset lane (move to opposite lane) — might cause head-on but who cares; visually interesting.

Let's simplify hero: follows route through intersections randomly, but prefers to keep going straight or turn. It brakes at lights too? "braking at lights" yes. But to look exciting, maybe hero runs reds sometimes. Hmm, requirement says braking at lights. Keep braking but with a bit of aggression.

Drift: when turning, add extra yaw rotation and lateral slip.

Let me write the car as a Group with a body mesh (box), cabin, wheels (cylinders), headlights, taillights. For perf with ~60 cars, that's fine (each ~8 meshes = 480 meshes). Acceptable but maybe reduce. Use simple low-poly car: body box, roof box, 4 wheels as cylinders... Actually 4 wheels × 60 cars = 240 cylinders. Fine-ish. Let's just do body + cabin + wheels simplified (maybe 2 wheels visible per side? no, 4). It's fine on modern hardware.

Actually let's reduce: traffic cars get body + cabin + 4 wheels = 6 meshes ×40 = 240. OK.

Use shared geometries and materials where possible. Different colors → separate materials per car (40 materials, fine).

Police cars: white/black with flashing lights (two small emissive spheres alternating red/blue).

Pedestrians: simple capsule body + sphere head, simplified. Walk along the sidewalk around blocks. Let's have each pedestrian assigned to a block, walking around the block perimeter on the sidewalk, with a loop. Some walk across? Keep simple: perimeter loop with corner turning.

Actually simpler: pedestrians walk along a rectangle path around a block at sidewalk offset, moving at ~1.4 m/s, rotating to face direction. Add slight bobbing.

Building generation: for each block, subdivide into smaller building footprints. Each block is B x B = 44x44. Leave sidewalk margin 3 units, so buildable 38x38. Split into 2x2 or 3x3 sub-lots with small gaps. Some blocks become parks (grass + trees + paths).

Buildings: use InstancedMesh with box geometry, per-instance color, and scale per instance. But then window texture UVs get stretched. Alternative: use a facade texture that tiles, and since it's instanced with non-uniform scale, the texture will stretch. Hmm. Could set texture repeat per instance? Not with instancing easily.

Alternative: don't use instancing; create individual meshes but merge geometry? For ~200 buildings, individual meshes with their own material is 200 draw calls, acceptable. Actually with lights, 200 draw calls fine.

But we could reduce by using per-building material color and a shared canvas texture with the window pattern; UV stretch is fine-ish if we set the box geometry UVs scaled... Simpler approach: create a box geometry per building and scale UVs by (width, height) so window pattern repeats correctly. That means unique geometry per building — 200 geometries, fine (small vertex count).

Actually easiest: use a shader-free approach: material with map = windowTexture, and adjust geometry UV attribute per building so that map repeats ~every 4 units. Let's do that: for box geometry, uv attribute for each face. BoxGeometry UVs are per-face 0..1. We can multiply u by (faceWidth/4) and v by (faceHeight/4). Since faces differ in dimensions (side faces: width=depth, height), we need to modify per face. BoxGeometry has 6 faces of 4 vertices each, order: +X, -X, +Y, -Y, +Z, -Z. Faces +X/-X have width = depth, +Z/-Z have width = width, +Y/-Y are top/bottom (roof).

We can manually set UVs. Let me just build a custom function that, given w,h,d, creates a BoxGeometry and rewrites UVs.

BoxGeometry uv groups: each face has 4 vertices in order. For face +X: vertices with positions... uv (0,1),(1,1),(0,0),(1,0) roughly. Multiply by repeat.

Let me write:

```js
function makeBuildingGeo(w,h,d){
  const g = new THREE.BoxGeometry(w,h,d);
  const uv = g.attributes.uv;
  const ru = 1/4, rv = 1/3.5; // window cell size in world units
  // faces: 0:+X (u along -z, v along y), 1:-X, 2:+Y, 3:-Y, 4:+Z, 5:-Z
  const dims = [[d,h],[d,h],[w,d],[w,d],[w,h],[w,h]];
  for(let f=0; f<6; f++){
    const [fw, fh] = dims[f];
    const su = fw*ru, sv = fh*rv;
    for(let k=0;k<4;k++){
      const i = f*4+k;
      uv.setXY(i, uv.getX(i)*su, uv.getY(i)*sv);
    }
  }
  uv.needsUpdate = true;
  return g;
}
```
And texture wrapS/T = RepeatWrapping.

Windows texture: canvas 64x64: dark facade with lit windows grid. But for day, windows look dark; at night they emit. We can use emissiveMap = same canvas but with only windows lit... Simpler: use the window texture as map, and also as emissiveMap with emissive color changing by time of day (0 at day, warm at night). Actually emissiveMap multiplies emissive color. So set emissive = warm color * nightFactor. But the map's facade base color would then also emit. Make emissive map separate texture where facade is black and windows are white. That's easy: generate two canvases.

OK.

Building color variety: multiply map by material color. Use per-building material with color. 200 materials — fine.

Let's cut down: maybe 120 buildings total. City 8x8 blocks = 64 blocks, some are parks (say 15%), rest have 2-4 buildings each. That could be ~150 buildings. OK, acceptable.

Hmm, but performance with shadows... Let's enable a directional light with shadows over a limited area around the hero car? Shadow maps for 150 buildings re-rendered each frame — could be slow. Maybe disable shadows and fake it with a dark ground gradient. Let's skip shadows entirely for safety, or enable only for cars. Actually shadows add a lot of visual quality. Let's do: renderer.shadowMap enabled, directional light with shadow camera covering a modest area following the hero car, and only cars + ground receive/cast. Buildings castShadow true too but the shadow camera only covers ~120 units around hero. Hmm, buildings are big. Let's just skip shadows; use ambient occlusion-ish coloring (darker ground near buildings not needed). Simpler: no shadows. Keep it performant. Maybe add a simple fake shadow blob under cars (dark circle plane). That's cheap and looks good.

OK.

Sky: use a large sphere with gradient shader or just scene.background color lerped. Let's use a simple gradient sky via a big sphere with ShaderMaterial (top color/bottom color uniforms updated with time of day). Plus a sun sphere/disc. And maybe stars at night — could add a Points object with random positions on a sphere, opacity by night factor.

Fog: THREE.FogExp2 for depth.

Night: street lights on. Street lights: pole + a small emissive sphere, plus we won't add real point lights for all (too many). Add a few point lights near the hero? We can add ~6 pooled point lights that follow nearby street lamps. Might be complex. Alternative: use emissive lamp head + a "light pool" decal on ground (a circle plane with additive blending). That's cheap and looks fine. Let's do that: each street lamp gets a ground glow disc, visible at night.

Also car headlights: cone of light? Add a small spotlight for hero car only, plus emissive headlight quads for all cars at night. Hero gets 2 spotlights maybe. Keep it simple: emissive materials + fake light cone (transparent cone mesh) for hero.

Let's now plan the code structure.

```js
import * as THREE from 'three';
```

Global setup: renderer, scene, camera.

Constants:
```
const BLOCK = 44, ROAD = 14, S = BLOCK + ROAD; // 58
const GRID = 8; // number of blocks per side
const CITY = GRID * S; // 464
const HALF = CITY/2;
```
Road centerlines at x = i*S for i in 0..GRID. So x from 0 to GRID*S = 464. Block centers at x = i*S + S/2 for i in 0..GRID-1.

World position from grid coords: subtract HALF so city centered at origin.

Ground: big plane (dark asphalt) covering city + margin. Actually ground base = grass/dirt color, then roads as separate planes.

Simpler: 
- Base plane: grass color, size CITY + 200.
- Road planes: for each road line (both directions), a plane of width ROAD covering the city length; plus they overlap at intersections (fine).
- Intersections have asphalt too - covered by overlapping planes.

Road markings: dashed center line — use small white boxes? Might be many. Use a texture on road? Let's make a road texture via canvas: asphalt noise + dashed yellow center line + white edge lines. But road planes oriented in two directions; we can rotate UVs. Let's just create a canvas texture 64x256 representing a road strip: line along length. For an X-direction road, plane of size (CITY, ROAD) with texture repeat (CITY/ (something), 1). Hmm, we want dashes repeating along length: set repeat.x = CITY/8, repeat.y = 1. The texture: horizontal dashes along u. Let's define texture where u is along road length, v across width. Draw: asphalt gray, dashed line at v=0.5, solid lines near edges.

For roads in Z direction, rotate the plane by 90° about Y so u maps along z. Good.

Sidewalks: for each block, a slightly raised box (height 0.25) of size BLOCK x BLOCK, light gray, with the block content on top.

Now crossing/lane offsets: lane offset = 3.5 from center. Road half width 7. Good, so lanes centered at ±3.5 with 7 width... a bit wide but ok. Let's use 3.2.

Traffic light poles at intersection corners.

Now, let's write the traffic system.

```js
const nodes = []; // intersection positions
function nodePos(i,j){ return new THREE.Vector3(i*S - HALF, 0, j*S - HALF); }
```

Directions: 
```js
const DIRS = [
 {name:'+x', v:new THREE.Vector2(1,0), right:new THREE.Vector2(0,1)},  // right = +z
 {name:'-x', v:new THREE.Vector2(-1,0), right:new THREE.Vector2(0,-1)},
 {name:'+z', v:new THREE.Vector2(0,1), right:new THREE.Vector2(-1,0)},
 {name:'-z', v:new THREE.Vector2(0,-1), right:new THREE.Vector2(1,0)},
];
```
Wait check right vector math in 2D (x,z): forward f=(fx,fz), up=(0,1,0) in 3D. right = f × up in 3D: (fx,0,fz) × (0,1,0) = (0*0 - fz*1, fz*0 - fx*0, fx*1 - 0*0) = (-fz, 0, fx). So right = (-fz, fx) in (x,z).

Check +x: f=(1,0) → right = (0,1) = +z. ✓.
+z: f=(0,1) → right = (-1,0) = -x ✓.
-x: f=(-1,0) → right=(0,-1) ✓.
-z: f=(0,-1) → right = (1,0) ✓.

Great, right = (-fz, fx).

Lane offset vector = right * LANE (3.2).

Car state:
- i, j (current node indices)
- dir index
- t (distance travelled along the segment from node(i,j) toward next node)
- speed
- nextI, nextJ computed from dir.

Segment length = S.

Position: p = node(i,j) + dirVec * t + laneOffset(dir). Note at t=0 the car is at the intersection center offset laterally. For stop line: we want car to stop before entering intersection, i.e. t <= S - stopDist where stopDist ~ 7 (half road width + 1). So stop when t = S - 7.

Hmm but at t=S the car reaches next node. Between nodes the car is on the segment.

Car placement: the car's actual world position = nodePos(i,j) + dirVec*t + laneOffset. And heading = dirVec.

When t >= S: set i=nextI, j=nextJ, t -= S, choose new direction.

Direction validity: must stay in [0,GRID] range for node indices. If next node out of range, must turn.

Choose new direction: exclude reverse; prefer straight; pick randomly among valid.

Traffic light check: at intersection node (i,j) — actually the light controlling entry into node(i,j) from direction d. Hmm, the car is at node(i,j) travelling toward node(nextI,nextJ). It needs the light at the next intersection for its approach direction. The light at intersection (ni,nj) for direction d: green if (d is along x and EW green) etc. Let's define per intersection phase offset = ((ni+nj)*0.5) mod 1, and green-x if phase < 0.5 else green-z... Actually we want a cycle. Let:

```js
function lightPhase(ni,nj,t){
  const off = ((ni*0.37 + nj*0.61) % 1);
  return (t*0.12 + off) % 1;  // cycle ~8.3s
}
function isGreenX(ni,nj,t){ return lightPhase(ni,nj,t) < 0.45; }
```
So X-direction traffic goes on green when phase<0.45, Z-direction when 0.55<phase<1.0 (0.45-0.55 = yellow/all red).

Car stop logic: if next node in range, and distance to next node > (S - STOP) i.e. car hasn't entered intersection yet, and light for direction is red → target speed 0, decelerate. Once t > S - STOP (already in intersection), keep going.

Let's do: 
```
const distToNode = S - t;  // distance remaining to next node center
if (distToNode > STOP_DIST) { check light }
```
STOP_DIST = 8. If light is red and distToNode < 25, brake.

Simplify: desired speed = base speed; if light red for our direction at next intersection and distToNode < 30, desired = 0; but don't stop if we're already too close (distToNode < 8) — just go.

Also car-following: look for cars in same segment (same i,j,dir) with t > my t, find min gap. If gap < 12, desiredSpeed reduced.

Since we're comparing t, only cars in the same (i,j,dir) lane matter. Good, cheap.

Implement: for each car, iterate over all cars... O(n²) with n=50, 2500 per frame, fine.

Actually better: maintain lanes map. Let's just brute force, it's fine.

Collision avoidance: if gap < 6, hard brake.

Hero car: same but with a route. Let's have hero choose directions with a preference for going straight and turning randomly, and drive faster (25 m/s). Hero accelerates fast, brakes at lights (maybe reduces). Overtaking: if a car ahead within 15 units, hero shifts lateral offset from 3.2 to 0 (center of road) or into the oncoming lane (-3.2). Let's implement a `lateral` variable that lerps to target. When overtaking, target = -3.2 (opposite lane). Then back to 3.2 after passing. Good enough visually.

Drift: on turning at an intersection, add a visual yaw offset and a slide: during the turn, the car's lateral position interpolates and the yaw lags... Actually the car's position snaps when moving from one segment to another. To make corners smooth, we should interpolate the car's actual position toward the ideal position rather than snapping. Let's have each vehicle maintain an actual position and heading that smoothly follow the "ideal" logical position. That gives nice cornering arcs.

For drift on hero: compute angle difference, if turning sharply and speed high, add extra yaw (oversteer) and reduce grip so heading lags position. Let's implement:

- idealPos, idealHeading computed from logical state.
- actual heading angle lerps toward ideal heading with a rate; when the turn is sharp & speed high, lerp slower (car slides), and add a visual yaw offset proportional to drift amount.

Simpler visual: heroYaw = smoothed heading + driftAngle, where driftAngle = clamp(turnRate * speed * k, ...). And add slip: car's forward velocity direction differs from heading.

I'll do: hero has `slip` value. On sharp turn, slip grows, then decays. The mesh rotation.y = heading + slip. And position offset lateral = -slip * speed * 0.05 maybe. Eh, keep it simple: rotate the car mesh extra and add tire smoke particles maybe. Let's skip smoke for simplicity but add small skid marks? Skip.

Actually a simple and effective drift look: mesh yaw = heading + slipAngle where slipAngle is the difference between velocity direction and heading. When turning, the car's heading turns faster than velocity direction. Let's just compute: velocity direction = derivative of actual position. Simpler to fake: when |dHeading/dt| large and speed high, slip = -sign(dHeading) * min(0.5, ...). Then decay.

OK let's just fake it, it's fine.

Now the camera: chase camera behind hero, smoothed. Occasionally switch to cinematic angles (e.g., low front view, side view, top-down) for ~3 seconds, then back.

Wanted level: increases over time when... Let's just increase wanted level when hero runs a red light or hits something. Or simply: after 15 seconds, police start spawning with wanted 1, escalating. Requirement: "a wanted-level chase where police cars pursue the hero car". Let's make it simple: wanted level starts at 1 after ~10s, increases every 20s up to 5, spawning police cars nearby. Police use simple pursuit: steer toward hero position, ignoring lanes.

Police movement: free steering — position + velocity, steer toward target point slightly ahead of hero. Keep them on roads? They'd cut through buildings. To avoid ugly building clipping, let police follow the road grid too, but with a "seek" direction: they move along the road network toward the hero's nearest node. That's complex. Alternative: give police simple direct pursuit but constrain them to road corridors: since the city is a grid, we can push them back to the nearest road line. Let's do: police steer toward hero; after moving, clamp position to nearest road corridor (if |x - nearestRoadX| > ROAD/2 - 1 and |z - nearestRoadZ| > ROAD/2 -1, push toward nearest road center). Hmm, this snapping might be jittery but workable.

Actually simpler and looks good: police use the same lane-graph AI as traffic but choose directions that minimize distance to hero. That means they follow roads and turn at intersections toward the hero. They'll be a bit dumb but look plausible. And they can ignore traffic lights. Let's do that. They'll be on lanes near hero. Give them higher speed.

Yes, let's do that: police are cars with `aggressive` flag: don't stop at lights, faster, and choose direction at intersections to minimize distance to hero.

Good.

Traffic cars also should maybe flee? No, keep them.

Minimap: canvas 2D in corner, size 180x180, showing city roads as lines, hero as a dot, police as red dots, traffic as white dots. Rotate map? Keep north-up with hero-centered view. Let's do hero-centered with a scale showing ~150 world units.

HUD: speed in km/h (speed * 3.6 if units are m/s). Plus wanted level stars.

Now let's think about counts and performance:
- Buildings: ~150 meshes with unique geometry. Each BoxGeometry with 24 verts. Fine.
- Trees in parks: instanced or simple. Let's use a shared cone+cylinder merged geometry, individual meshes with instancing? Use InstancedMesh for tree trunks and foliage. Or just group. ~100 trees → 200 meshes. Hmm. Use InstancedMesh: one for trunks (cylinder), one for foliage (cone/sphere). Good.
- Street lights: pole (cylinder) + arm + lamp. Instanced for poles, instanced for lamp heads.
- Traffic lights: at each intersection, 4 poles. 9x9 = 81 intersections × 4 = 324 poles. Too many. Reduce: place traffic lights only at some intersections? Or just 2 per intersection (one per axis). Let's do 2 per intersection → 162. Still a lot of meshes. Use InstancedMesh for the poles and the light boxes. And the actual red/yellow/green emissive lamps: use a small instanced mesh with per-instance color updated each frame. Hmm, updating instance colors each frame for 162*3 lights... Actually we can just have 3 instanced meshes (red, yellow, green), each with 162 instances, and toggle visibility... but visibility per instance needs scale 0. We can set instance matrix scale to 0/1 per frame. That's 3*162 matrix updates per frame = 486, fine but let's simplify.

Alternative: place traffic lights only at intersections where GRID ordering, i.e., all of them but with a single signal head showing the state for the cross street... Honestly, for the visual, maybe place traffic light poles at intersections but render the light state via a single emissive sphere colored by state. Using InstancedMesh with instanceColor updated when states change (every frame is fine, 81 instances).

Let's do: at each intersection, place 4 traffic signal heads (one per approach) but simplify to 2 instanced meshes: pole instanced + head instanced with instanceColor. Actually the head needs to show green/red. Use InstancedMesh of a small box with `instanceColor` set to green/red/yellow, and material with vertexColors... InstancedMesh instanceColor works with standard material (it multiplies color). Use MeshBasicMaterial so it glows bright. Yes: MeshBasicMaterial with instanceColor. Set colors per frame. 81 intersections × 4 heads = 324 instances. Updating colors each frame: 324*3 floats, fine.

Hmm, but 324 poles too... Only place a pole at 2 corners per intersection with an arm extending over the road. Let's simplify further: place one signal head per approach direction, mounted on a pole at the corner. 4 poles per intersection. With instancing it's fine (instanced pole mesh with 324 instances).

Actually let's limit the number of intersections that have traffic lights: use every intersection (9x9=81). 324 poles instanced = 1 draw call. Fine.

Let's reduce complexity: traffic light pole = thin box; head = small box with a bright emissive face. Use two InstancedMeshes.

OK, let's write it.

Actually, to reduce risk, maybe only place traffic lights at intersections where (i+j) is even... no, cars stop at any intersection they encounter. If there's no light there, they'd stop at nothing. Let's keep lights at all intersections and the logic consistent.

Hmm wait, cars check the light at the NEXT node. All nodes have lights. Good.

Let's now write the code.

```js
// ---------- Setup ----------
const renderer = new THREE.WebGLRenderer({antialias:true, powerPreference:'high-performance'});
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x9fb4c7, 0.0035);

const camera = new THREE.PerspectiveCamera(60, innerWidth/innerHeight, 0.5, 1200);
```

Lights:
- Hemisphere light
- Directional sun (updated with day cycle)
- Ambient minimal

Sky: gradient shader on a big sphere (BackSide).

Let's write sky shader:

```glsl
varying vec3 vWorldPos;
void main(){ vWorldPos = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }
```
frag: mix based on normalize(vWorldPos).y between horizon color and zenith.

Uniforms: topColor, bottomColor, sunDir, sunColor.

Add sun glow: `float d = dot(normalize(vWorldPos), sunDir); col += sunColor * pow(max(d,0.0), 32.0) * 2.0;`

Stars: Points with random positions on sphere radius 600, size 1.5, opacity controlled by night factor.

Day/night cycle: `timeOfDay` in [0,1), full cycle duration ~120s. Start at ~0.28 (morning). Actually to show night within 30s, let's start at 0.35 (afternoon) and make the cycle 90 seconds so night comes around t=20s... Hmm, "should show everything important within the first 30 seconds". Day-night: let's make the cycle shortish, like 100s, starting at dusk-ish 0.55 so night falls at ~15s. Hmm, but then the first 15s is daytime which is nice.

Let's set cycle length 120s and start at 0.42 (mid-afternoon), sun sets around... Let's define sun angle = timeOfDay*2π - π/2 so that timeOfDay 0.25 = noon, 0.5 = sunset, 0.75 = midnight. Start at 0.30 → afternoon. Sunset at 0.5 → t=24s. Night from 0.5 to 1.0 → 24s to 60s, then sunrise at 1.0 = 120s. Hmm that's a long night.

Let's compress: cycle length 80s. Start 0.25 (noon). Sunset at 0.5 → t = 20s. Night at t=20-60s. Sunrise at t=60s. That shows both day and night within 30 seconds. 

Hmm, but racing at night for 40s... it's fine, street lights and headlights look cool.

Actually let's make it so that the daytime portion is longer: sun elevation = sin(2π*(t-0.25)) ... whatever. Let's use:

`dayPhase = (elapsed / 80) % 1`
`sunAngle = (dayPhase - 0.25) * Math.PI * 2` → at dayPhase 0.25, sunAngle=0 → sun at horizon? Let's define sun direction:

sunElev = sin(sunAngle), sunAz = cos(sunAngle). Sun position = (cos*..., etc).

Let's simply do: 
```
const a = (dayPhase) * Math.PI * 2 - Math.PI/2;
sunDir = new THREE.Vector3(Math.cos(a)*0.6, Math.sin(a), Math.cos(a)*0.8).normalize();
```
At dayPhase 0.25: a = 0, sunDir = (0.6, 0, 0.8) → sun at horizon. Hmm.

Let's set: `a = dayPhase*2π`; sunDir = (cos a, sin a, 0.3) normalized... At dayPhase=0.25, sin=1 → sun overhead. At 0.5, sin=0 → horizon. At 0.75, sin=-1 → below (night). At 0, sin=0 → horizon (sunrise). 

So start dayPhase at 0.15 → sun elevation sin(0.15*2π)=sin(54°)=0.81, high. Good. Then sunset at dayPhase 0.5 → t = 0.35*80 = 28s. That's right at the edge. Let's use cycle 70s → sunset at t=24.5s. Good.

Hmm, we want the daylight driving to be the main show, and night to appear within the window. 24s of day, then night. Then night until t=59.5s. OK.

Actually maybe start at dayPhase 0.10 (mid-morning) and cycle 75s → sunset at 0.4*75 = 30s. Hmm exactly 30. Let's do start 0.18, cycle 72s: sunset at (0.5-0.18)*72 = 23s. Fine.

Let's use: `dayPhase = 0.18 + elapsed/72`.

Night factor: `night = smoothstep(0.15, -0.15, sunDir.y)` i.e., 1 when sun below horizon.

Sun light intensity = clamp(sunDir.y*2, 0, 1) * 1.2 etc. Ambient/hemisphere adjusts.

Street lights on when night > 0.4.

OK.

Now, let's write the actual code. I'll be careful with structure.

```js
// ===== Constants =====
const BLOCK = 44, ROAD = 14, S = BLOCK + ROAD;
const GRID = 8;
const CITY = GRID * S;   // 464
const HALF = CITY / 2;
const LANE = 3.2;
const SIDEWALK_H = 0.3;
```

Wait — roads at i*S for i in 0..GRID gives GRID+1 = 9 lines. Blocks between them. City extent from -ROAD/2 to CITY+ROAD/2. Let's shift by HALF so it's centered: world = gridX - HALF. Grid x=0 → -232, x=CITY → 232. Block centers at i*S + S/2 - HALF.

Now generation of the world.

**Ground**: PlaneGeometry(CITY+400, CITY+400) rotated -π/2, color dark green/gray. Actually outside the city, make it darker grass. Fine.

**Roads**: For each i in 0..GRID: a plane along Z at x = i*S - HALF, size (ROAD, CITY + ROAD). And along X at z = j*S - HALF, size (CITY+ROAD, ROAD). Texture with dashes.

Let's create the road texture:
```js
function makeRoadTexture(axis){
  const c = document.createElement('canvas'); c.width=64; c.height=64;
  const ctx = c.getContext('2d');
  ctx.fillStyle='#3a3a40'; ctx.fillRect(0,0,64,64);
  // noise
  for(let i=0;i<400;i++){ ctx.fillStyle = `rgba(255,255,255,${Math.random()*0.03})`; ctx.fillRect(Math.random()*64,Math.random()*64,2,2);}
  // u is along length. dashes: draw a horizontal line at v=0.5
  ...
}
```
Hmm, mapping: For a plane of size (ROAD, CITY) lying with rotation... Let's think about PlaneGeometry(w,h) default in XY plane, UV u along x (width), v along y (height). After rotateX(-π/2), x stays x, y→-z... Actually rotateX(-π/2) maps y to -z? Let's see: rotating about X by -90°: y' = y cos(-90) - z sin(-90) = z... hmm, for a point (x,y,0): y' = y*cos(-90°) - 0 = 0, z' = y*sin(-90°) + 0 = -y. So point (x,y,0) → (x, 0, -y). So plane width along x, height along -z. So u along x, v along z (reversed).

For a road along Z: I want the dash pattern along z. So use PlaneGeometry(ROAD, CITY) and after rotation, u along x = across the road, v along z = along the road. Texture: repeat.x = 1 (across), repeat.y = CITY/8 (along). So the texture's v axis contains the dash pattern. Canvas: width=64 (across road), height=64 (along). Draw dashes vertically at x=32 (center). Good.

For a road along X: use PlaneGeometry(CITY, ROAD) → u along x (along road, repeat = CITY/8), v along z (across road, repeat 1). Draw dashes horizontally at y=32.

So one canvas function with a `flip` param. Or just make two textures. Simpler: make a single 64x64 canvas with the dash along one axis, and rotate the texture by setting texture.rotation... eh, just make two canvases.

Let me write a helper that draws a road texture given orientation.

Actually simpler: write the canvas with the road running along the vertical (v) axis, and for X-roads use `texture.rotation = Math.PI/2` with center 0.5,0.5. Rotation of texture repeat is messy. Just make two textures.

OK.

**Blocks**: For each block (i,j), center at (i*S + S/2 - HALF, j*S + S/2 - HALF). Create:
- Sidewalk slab: BoxGeometry(BLOCK, SIDEWALK_H, BLOCK), position y = SIDEWALK_H/2, material light gray. Actually let's make it a box from y=0 to 0.3.
- Then decide: park or buildings.

Park: green top surface (a plane at y=0.31 with grass color), trees, paths, maybe a pond.

Buildings: subdivide the 44x44 into a grid of lots. Let's do: choose a pattern: [2,2] or [3,2] or [2,3] with margins.

For each lot, create a building: width ~ lotSize - gap, depth similar, height random 8..40.

Then create mesh with the facade material (map = windowTex, emissiveMap = windowEmissiveTex), color random from palette.

Also add a roof detail? Skip.

Let's limit subdivisions to keep building count moderate: 64 blocks, ~25% parks → 48 building blocks × ~3 buildings = ~144 buildings. OK.

**Street lamps**: along roads at intervals, on sidewalk edges. For each road line, place lamps every ~29 units on alternating sides. Count: 9 roads × 2 directions × 16 positions = 288. Too many. Let's do every other block: place lamp at each block corner on one side. Hmm.

Let's just place lamps at positions along each road at spacing S (every 58 units), alternating sides: 9 roads × 8 positions × 2 axes = 144 lamps. With instancing, fine.

Each lamp: pole (cylinder r=0.15 h=6), arm (box), lamp head (box). Three instanced meshes with 144 instances each. Plus a glow disc on ground (instanced plane, additive). OK.

**Trees**: for parks and along sidewalks. Instanced: trunk cylinder + foliage sphere/cone. ~150 trees.

**Traffic lights**: at each intersection (9x9=81), 4 poles. Instanced pole (cylinder r=0.12 h=5) and head (box 0.5x1.2x0.5) positioned at corner, with instanceColor updated.

Hmm, the head color changes: red/green/yellow. Let's use MeshBasicMaterial for the head instanced mesh with instanceColor. The head is a box; we color the whole box. Fine, it reads as a glowing signal.

Actually nicer: make the head a small vertical box with 3 emissive dots... let's skip, just a colored box ~0.4×1.0×0.4, plus maybe a black backing box. Fine.

Let's just do colored box.

**Now vehicles**.

Car factory: creates a group.

```js
function makeCar(color, isPolice){
  const g = new THREE.Group();
  const bodyMat = new THREE.MeshLambertMaterial({color});
  ...
}
```
Wait, MeshLambertMaterial supports emissive? Yes, Lambert has emissive. Use MeshLambertMaterial for cheapness. Or MeshStandardMaterial for better look but more expensive. With ~60 cars × 6 meshes = 360 meshes, Lambert is fine and cheap.

Actually let's use MeshPhongMaterial for cars to get some shininess. Meh, Lambert is fine. Let's use StandardMaterial for hero and police, Lambert for traffic? Keep uniform: MeshLambertMaterial everywhere except special.

Car body: BoxGeometry(1.8, 0.7, 4.2) at y=0.7. Cabin: BoxGeometry(1.6, 0.55, 2.0) at y=1.25, z=-0.2. Wheels: cylinder r=0.35, h=0.25, rotated Z by π/2, at (±0.9, 0.35, ±1.3).

Headlights: small boxes at front, emissive white, at z=-2.05 (front is -z if car faces -z... let's define car forward as +z? Convention: default car forward = +z? Let's make forward = +x for simplicity? No — let's define the car model facing +Z, and set rotation.y = atan2(dir.x, dir.z).

Hmm: heading angle for direction (dx,dz): rotation.y = Math.atan2(dx, dz). With rotation.y = θ, the local +Z axis maps to world (sin θ, 0, cos θ). So yes, forward = local +Z.

So build the car with the front at +Z. Headlights at z=+2.05, taillights at z=-2.05.

OK.

Wheels: cylinder axis along X → rotateZ(π/2) since cylinder default axis is Y. After rotateZ(π/2), axis along X. Good.

Add a fake shadow: a circle plane (dark, transparent) at y=0.02 under the car, as a child, rotated -π/2. But as a child of the group, it inherits rotation. Fine since it's flat.

Hmm, but the group rotates about Y, and the shadow plane rotated -π/2 about X is horizontal. OK.

**Pedestrians**: capsule-ish: cylinder body + sphere head. Walk around block perimeters on the sidewalk.

Pedestrian path: around block (i,j), a rectangle at radius BLOCK/2 + 1.5 from the block center... wait, sidewalks are the block slabs themselves; the block slab is BLOCK wide and the buildings are inset. So pedestrians walk on the block slab near its edge. Path rectangle: half-extent = BLOCK/2 - 2.

Pedestrian state: block index, param s along the perimeter, direction (cw/ccw), speed. Position = perimeter point. Heading from perimeter tangent.

Perimeter length = 8*(BLOCK/2 - 2)... For a square path of half-extent h, perimeter = 8h. Let h = 18 → perimeter 144.

Compute position from s: 
```
const p = s % (8*h);
let x,z;
if (p < 2h) { x = -h + p; z = -h; }  // moving +x along the bottom
else if (p < 4h) { x = h; z = -h + (p-2h); }
else if (p < 6h) { x = h - (p-4h); z = h; }
else { x = -h; z = h - (p-6h); }
```
Wait 2h per side, 4 sides = 8h. Yes.

Then heading toward next direction.

Add slight bobbing: y = 0.3 + abs(sin(t*8))*0.05.

Pedestrian count: 64 blocks × 3 = 192. Too many meshes (2 each = 384). Reduce: only blocks that are not parks get pedestrians; ~48 × 3 = 144 pedestrians → 288 meshes. Hmm.

Let's reduce to 2 per block → 96 pedestrians, 192 meshes. Acceptable? Combined with cars (360 meshes) and buildings (150) and instanced stuff... total ~800 draw calls. That might be heavy but probably OK on desktop. Hmm, risky.

Let's cut: pedestrians use a merged geometry (body + head merged into one geometry) so 1 mesh each. Use BufferGeometryUtils? We'd need to import 'three/addons/utils/BufferGeometryUtils.js'. That's allowed (addons from three/addons). But we can also just merge manually: create a capsule-like geometry from a cylinder + sphere using `BufferGeometryUtils.mergeGeometries`. Let's import it. It's allowed.

Actually simpler: use THREE.CapsuleGeometry for the body (radius 0.3, length 0.9) and a SphereGeometry head as a separate mesh — 2 meshes. Or just use one capsule and color the whole thing... A capsule alone looks like a pill person. Let's do capsule body + head merged. I'll import BufferGeometryUtils.

Hmm, importing addons requires the import map to resolve 'three/addons/'. The prompt says an import map is provided. OK, so `import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';` should work. But to reduce risk, maybe just avoid it and accept 2 meshes per pedestrian. Let's limit pedestrians to ~80, so 160 meshes. That's fine.

Actually, let me reduce meshes more aggressively: for cars, I could merge body+cabin into one geometry... but colors differ per part. Body and cabin could share material. Merge body and cabin into one geometry → 1 mesh. Wheels: 4 → could be merged into 1 geometry if we build a merged wheel geometry. Then each car = body mesh + wheels mesh + lights mesh = 3 meshes. With 50 cars = 150 meshes. 

Let's do that: build car geometry parts manually by translating and merging. Without BufferGeometryUtils, I can create merged geometry by creating a BoxGeometry and applying matrix, then... no merge without utils.

OK, let me just import BufferGeometryUtils. It's a standard addon. Risk is low.

Hmm, but "do not add your own import map or any CDN URL" — the import map is provided and includes 'three/addons/'. I'll trust it.

Actually, to be safest, I'll avoid addons entirely and just accept more meshes but keep counts low. Let's estimate:

- Traffic cars: 36 → each 6 meshes = 216
- Police: 8 → 48
- Hero: 1 → 6
- Pedestrians: 72 → 144
- Buildings: 150
- Instanced: ~10 draw calls
- Roads/sidewalks: ~20
Total ≈ 600 meshes. Should run OK at 60fps on a decent machine. Modern GPUs handle 600 draw calls fine.

Hmm, but low-end... Let's aim for that. Actually let's reduce wheels to be part of a single "wheel pair" geometry? No.

Let me reduce traffic cars to 30 and pedestrians to 60. Total meshes ≈ 500. Fine.

Actually, I realize I can reduce car meshes: wheels as a single mesh? Without merge util, I can create 4 wheel meshes. Alternatively, use a simpler car: body box + cabin box + 2 wheel-pair cylinders (long cylinders spanning the width, like axles with wheels). That's 4 meshes. Meh, similar.

Let's just go with the straightforward approach.

Now let's write the code.

```js
// ---- Scene setup ----
```

I'll write it all out now.

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Autonomous City</title>
<style>
  html,body{margin:0;height:100%;overflow:hidden;background:#000;font-family:system-ui,sans-serif;}
  canvas{display:block;}
  #hud{position:fixed;left:0;top:0;width:100%;height:100%;pointer-events:none;}
  ...
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

I'll put the HUD as DOM elements: speed, wanted stars, minimap canvas.

Let me write the JS.

```js
const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x8899aa, 0.0028);

const camera = new THREE.PerspectiveCamera(62, innerWidth/innerHeight, 0.5, 2000);
```

Sky dome:

```js
const skyUniforms = {
  top: {value: new THREE.Color(0x2a6fd4)},
  bottom: {value: new THREE.Color(0xbcd6ee)},
  sunDir: {value: new THREE.Vector3(0,1,0)},
  sunColor: {value: new THREE.Color(0xffddaa)},
};
const skyGeo = new THREE.SphereGeometry(900, 32, 16);
const skyMat = new THREE.ShaderMaterial({
  uniforms: skyUniforms,
  side: THREE.BackSide,
  depthWrite: false,
  vertexShader: `varying vec3 vPos; void main(){ vPos = position; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0);} `,
  fragmentShader: `
    uniform vec3 top; uniform vec3 bottom; uniform vec3 sunDir; uniform vec3 sunColor;
    varying vec3 vPos;
    void main(){
      vec3 d = normalize(vPos);
      float h = clamp(d.y*0.5+0.5, 0.0, 1.0);
      vec3 col = mix(bottom, top, pow(h, 0.8));
      float s = max(dot(d, normalize(sunDir)), 0.0);
      col += sunColor * pow(s, 24.0) * 0.8;
      col += sunColor * pow(s, 4.0) * 0.12;
      gl_FragColor = vec4(col, 1.0);
    }`
});
const sky = new THREE.Mesh(skyGeo, skyMat);
sky.frustumCulled = false;
scene.add(sky);
```

Stars:
```js
const starGeo = new THREE.BufferGeometry();
const starPos = [];
for(let i=0;i<600;i++){
  const v = new THREE.Vector3().randomDirection().multiplyScalar(800);
  if(v.y < 0) v.y *= -1; // upper hemisphere
  starPos.push(v.x, v.y, v.z);
}
starGeo.setAttribute('position', new THREE.Float32BufferAttribute(starPos,3));
const starMat = new THREE.PointsMaterial({color:0xffffff, size:2.2, sizeAttenuation:false, transparent:true, opacity:0});
const stars = new THREE.Points(starGeo, starMat);
stars.frustumCulled = false;
scene.add(stars);
```

Hmm, PointsMaterial size with sizeAttenuation false uses pixels. Good.

Lights:
```js
const hemi = new THREE.HemisphereLight(0xaaccff, 0x444433, 1.0);
scene.add(hemi);
const sun = new THREE.DirectionalLight(0xffeedd, 1.2);
scene.add(sun);
const ambient = new THREE.AmbientLight(0x404060, 0.4);
scene.add(ambient);
```

Now the city.

```js
const GRID = 8, BLOCK = 44, ROAD = 14, S = BLOCK+ROAD;
const CITY = GRID*S, HALF = CITY/2;
```

Helper to convert grid line index to world coordinate: `gx = i*S - HALF`.

Roads: from -HALF-ROAD/2 to HALF+ROAD/2? Let's make road planes span the full city plus a bit: length CITY + ROAD*2.

Road texture:

```js
function makeRoadTexture(horizontal){
  const c = document.createElement('canvas');
  c.width = 64; c.height = 256;
  const g = c.getContext('2d');
  g.fillStyle = '#33343a'; g.fillRect(0,0,64,256);
  // noise
  for(let i=0;i<300;i++){
    g.fillStyle = 'rgba(255,255,255,'+(Math.random()*0.035)+')';
    g.fillRect(Math.random()*64, Math.random()*256, 3, 3);
  }
  // edge lines
  g.fillStyle = 'rgba(230,230,220,0.55)';
  g.fillRect(5, 0, 2, 256);
  g.fillRect(57, 0, 2, 256);
  // center dashes
  g.fillStyle = 'rgba(240,220,120,0.75)';
  for(let y=0;y<256;y+=32){ g.fillRect(31, y, 3, 16); }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  ...
}
```
Hmm the uv orientation. As discussed: for a plane rotated -π/2 about X, u is along world X, v is along world Z (with sign flip). So for a road along Z (a plane of size (ROAD, LEN)), u across = road width, v along = road length. Texture: canvas x = u = across road (0..64), canvas y = v = along road. So draw edge lines as vertical stripes at x=5 and x=57 (across), and dashes as vertical segments along y. My drawing above: `g.fillRect(5,0,2,256)` = vertical stripe at x=5 — that's across the road at position 5/64 of width. Good. Dashes at x=31, height 16 along y. Good.

Repeat: repeat.set(1, LEN/16) so dashes repeat every 16 units → dash pattern of 32px in a 256px texture = 1/8 of texture. If texture repeats every 16 world units along the road, then one dash cycle = 16/8 = 2 units. Too dense. Let's set repeat.y = LEN/64 → each texture tile = 64 world units, dash cycle = 64/8 = 8 units (dash 4, gap 4). Good.

For a road along X, we make a plane (LEN, ROAD), where u along X = length, v across. So the texture needs dashes along u and edge lines along v. So we need a second canvas where the pattern is transposed. Or we can just rotate the plane around the Z... no.

Easiest: create the texture with the pattern along canvas-x (horizontal) for X-roads, and along canvas-y for Z-roads. Two canvases.

Let me write `makeRoadTexture(axis)` where axis 'x' means the road runs along X.

```js
function makeRoadTexture(axis){
  const W=256, H=64;
  const c = document.createElement('canvas');
  c.width = W; c.height = H;
  const g = c.getContext('2d');
  g.fillStyle = '#34353b'; g.fillRect(0,0,W,H);
  for(let i=0;i<400;i++){
    g.fillStyle='rgba(255,255,255,'+(Math.random()*0.03)+')';
    g.fillRect(Math.random()*W, Math.random()*H, 3, 3);
  }
  g.fillStyle='rgba(235,235,225,0.5)';
  if(axis==='x'){ g.fillRect(0,5,W,2); g.fillRect(0,H-7,W,2); }
  else { g.fillRect(5,0,2,H); g.fillRect(W-7,0,2,H); }
  g.fillStyle='rgba(245,225,130,0.8)';
  if(axis==='x'){ for(let x=0;x<W;x+=32) g.fillRect(x, H/2-1.5, 16, 3); }
  else { for(let y=0;y<H;y+=32) g.fillRect(W/2-1.5, y, 3, 16); }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.anisotropy = 4;
  return t;
}
```

Wait — for axis 'x', the road runs along X, so u (canvas x) is along the road. The dashes should repeat along u. So repeat.x = LEN/64, repeat.y = 1. And the canvas: dashes drawn horizontally along x ✓, edge lines horizontal along x at top/bottom ✓ (these run along the road at the edges across the width). ✓

For axis 'z', road along Z, u = across (width), v = along (length). Canvas: u = canvas x = across, v = canvas y = along. Edge lines vertical at x=5, x=W-7 ✓. Dashes vertical at x=W/2 ✓. repeat.x = 1, repeat.y = LEN/64.

Good, my code above matches (with W=256 being the road-length direction for 'x'... hmm I set W=256 as canvas width for both). For axis 'x', canvas width 256 is along the road. For 'z', canvas width 256 is across the road and height 64 along. Hmm, that's inverted: for 'z' road, I want the canvas to have u (x, across-road) small and v (y, along-road) large. But I set W=256, H=64. That gives u range 256 across and v range 64 along — the repeat would be repeat.x=1, repeat.y=LEN/64 which means the texture covers 256px across the 14-unit road width and repeats every 64 units along. The dash pattern would be squished. But since we drew edge lines as vertical stripes at x=5 and x=W-7=249, those would map to across the road at 5/256 and 249/256 — fine actually. And the dashes at x=W/2=128 → center of the road ✓, repeating every 32px along v, and v repeats every 64 world units → texture height 64px covers 64 world units → dash cycle 32px = 32 world units. Too long.

Let me just simplify: use a 64×256 canvas for 'z' roads (width 64 = across, height 256 = along), and 256×64 for 'x' roads. Let me restructure:

```js
function makeRoadTexture(axis){
  const L = 256, Wd = 64;
  const c = document.createElement('canvas');
  c.width = axis==='x' ? L : Wd;
  c.height = axis==='x' ? Wd : L;
  ...
}
```
And use generic drawing based on which axis is the "length" direction. Let me write it with length along canvas x for 'x' and along canvas y for 'z'.

I'll write it clearly with two branches. Fine.

Then repeat: for 'x' road: repeat.set(LEN/64, 1). For 'z': repeat.set(1, LEN/64).

OK.

Ground plane: use a simple color, maybe with a subtle texture. Just color 0x3a4a35 (dark green-gray). Actually the area outside the city should look like grass/terrain. Use 0x2e3b2e. And add fog.

Now blocks.

```js
const blockData = []; // for minimap: parks etc.
```

Building facade textures:

```js
function makeFacadeTextures(){
  const S = 64;
  const c = document.createElement('canvas'); c.width=c.height=S;
  const g = c.getContext('2d');
  g.fillStyle='#c8c4bc'; g.fillRect(0,0,S,S);
  // subtle
  ...
  // windows
  const e = document.createElement('canvas'); e.width=e.height=S;
  const ge = e.getContext('2d');
  ge.fillStyle='#000'; ge.fillRect(0,0,S,S);
  
  // grid of windows: 2 cols x 2 rows per tile? Let's do 2x2 windows per 64px tile => window size ~20x20 with margins
  for(let i=0;i<2;i++) for(let j=0;j<2;j++){
    const x = 8 + i*28, y = 8 + j*28, w=20, h=20;
    g.fillStyle = '#4a5866'; g.fillRect(x,y,w,h);
    g.fillStyle = 'rgba(0,0,0,0.25)'; g.fillRect(x, y, w, 3);
    ge.fillStyle = Math.random()<0.6 ? '#ffd9a0' : '#88aacc';  // hmm random per window
    ge.fillRect(x,y,w,h);
  }
  ...
}
```
Actually we want a texture, and different buildings will use the same texture. That's fine — the lit windows pattern repeats. Acceptable.

Hmm, but with random lit windows the emissive map won't match the base map windows. It doesn't need to match exactly.

Let's do it slightly differently: draw windows on both canvases at the same positions; base map has dark blue-gray windows, emissive map has warm light with random on/off.

Tile size 64 px = 4 world units? Let's set the window cell size in world units: one texture tile covers 4 units horizontally and 4 vertically. So each tile has 2x2 windows → window every 2 units. That's a bit small for a building. Let's make one tile = 8 world units with 2x2 windows → windows every 4 units. Reasonable.

So in makeBuildingGeo: ru = 1/8, rv = 1/8.

Hmm, for a 20-wide building, that's 2.5 tiles → 5 windows across. Good.

OK.

Building materials: MeshLambertMaterial({map: facadeTex, emissiveMap: facadeEmissive, emissive: 0x000000, color: 0xffffff}) — and we set per-building color by making separate materials with different `color`. The emissive is updated globally at night: we'd need to update each material's emissive color. With 150 materials, updating each frame is fine but wasteful. Let's update only when the night factor changes meaningfully (every ~10 frames). Or just share a few materials (say 6 color variants) — then we update 6 materials. 

Let's use 6 shared materials with different colors. That reduces material count and makes night updates trivial.

But then all buildings with the same variant share a material — fine.

Actually with shared materials, we can't have per-building color variation beyond 6. That's fine.

Hmm, but emissive on Lambert: `material.emissive` color. Set to warm * night. Good.

Also for the roofs (top face), the map will show windows on the roof which looks odd. Let's handle: for the +Y face, set UVs to a small corner region of the texture that's plain (e.g., the base color region). Actually the whole texture has windows everywhere. Let's make the texture have a "plain" strip. Alternative: use material array — 6 materials for the box faces, with the top using a plain roof material. BoxGeometry has 6 groups. So `new THREE.Mesh(geo, [sideMat, sideMat, roofMat, roofMat, sideMat, sideMat])`. That's a material array per mesh — still fine with shared materials.

Let's do that. Roof material: dark gray Lambert shared.

OK, and the UV fix should only apply to the side faces (indices 0,1,4,5). For top/bottom, leave default.

Hmm, but the boxes have different sizes; the roof UV doesn't matter much.

Let's write makeBuildingGeo.

```js
function buildingGeometry(w,h,d){
  const geo = new THREE.BoxGeometry(w,h,d);
  const uv = geo.attributes.uv;
  const TILE = 8;
  const faces = [[d,h],[d,h],[w,d],[w,d],[w,h],[w,h]];
  for(let f=0; f<6; f++){
    const [fw,fh] = faces[f];
    const su = Math.max(1, Math.round(fw/TILE));
    const sv = Math.max(1, Math.round(fh/TILE));
    for(let k=0;k<4;k++){
      const idx = f*4+k;
      uv.setXY(idx, uv.getX(idx)*su, uv.getY(idx)*sv);
    }
  }
  uv.needsUpdate = true;
  return geo;
}
```

Using Math.round for su/sv keeps tiles mostly whole. Good.

Now, `geo.translate` — we position via mesh.position.

Buildings placed with base at y = SIDEWALK_H (0.3) and height h, so position.y = SIDEWALK_H + h/2.

Now let's build the city.

```js
const cityGroup = new THREE.Group();
scene.add(cityGroup);
```

Roads:
```js
const roadLen = CITY + ROAD*2;
const roadMatX = new THREE.MeshLambertMaterial({map: makeRoadTexture('x')});
const roadMatZ = new THREE.MeshLambertMaterial({map: makeRoadTexture('z')});
```
Wait, each road mesh needs its own texture repeat setting if lengths differ. They're all the same length, so one material each works.

texture.repeat.set(roadLen/64, 1) for X.
texture.repeat.set(1, roadLen/64) for Z.

Then create plane geometry once and instance? Just create meshes.

```js
const roadGeoX = new THREE.PlaneGeometry(roadLen, ROAD); roadGeoX.rotateX(-Math.PI/2);
const roadGeoZ = new THREE.PlaneGeometry(ROAD, roadLen); roadGeoZ.rotateX(-Math.PI/2);
```
Wait, do these rotations give correct UV mapping? PlaneGeometry(w,h) with rotateX(-π/2): as computed, x→x, y→-z. UV u along x, v along y→ -z. So for roadGeoX (w=roadLen along x, h=ROAD along z), u along the road ✓, v across ✓. For roadGeoZ (w=ROAD along x, h=roadLen along z), u across ✓, v along ✓. 

Now the mesh position: y = 0.02 to sit above the ground.

Now blocks:

```js
for(let i=0;i<GRID;i++) for(let j=0;j<GRID;j++){
  const cx = i*S + S/2 - HALF;
  const cz = j*S + S/2 - HALF;
  const isPark = Math.random() < 0.18;
  buildBlock(cx, cz, isPark, i, j);
}
```

buildBlock: creates sidewalk slab, then content.

Sidewalk slab: BoxGeometry(BLOCK, 0.3, BLOCK) at y=0.15, material gray.

Then:
- if park: grass plane on top (BLOCK-1.5 square) at y=0.31, trees, paths, maybe a small pond.
- else: buildings.

Buildings subdivision: choose nx, nz from [1,2,3] such that lot size >= 12.

```js
const nx = 2 + (Math.random()<0.35?1:0); // 2 or 3
const nz = 2 + (Math.random()<0.35?1:0);
```
lot = BLOCK/nx, minus gap 2.

For each lot: building w = lotW - rand(2..5), d = lotD - rand(2..5), h = 6 + rand*35 (with variation, some taller).

Also occasionally skip a lot for variety (small plaza).

Building position: center of lot.

Let's also add height falloff: taller buildings near the center of the city. `const distFromCenter = ...; height *= ...`. Nice touch.

OK.

Now street lamps. Place along roads.

For each grid line index k in 0..GRID:
- X-direction road (along X) at z = k*S - HALF: place lamps at x = various positions, on the sidewalk side (z offset ±(ROAD/2 + 1)).
- Z-direction road at x = k*S - HALF.

Position lamps at block centers along the road: x = i*S + S/2 - HALF for i in 0..GRID-1.

So for each k, for each i in 0..GRID-1: lamp at (i*S+S/2-HALF, k*S-HALF + side*(ROAD/2+1.2)). Alternate side by i%2.

Total: (GRID+1) * GRID * 2 (both axes) = 9*8*2 = 144. OK.

Each lamp has a pole and a head. Use InstancedMesh:
- pole: CylinderGeometry(0.12, 0.15, 7, 6) — instanced with 144.
- head: BoxGeometry(0.5,0.25,1.2) offset toward the road.
- glow: a plane on the ground, additive.

Let's compute the orientation: the lamp arm should extend over the road. For an X-road with the lamp on the +z side, the head is at z + (-1) * ... it should extend toward the road center, so toward -z if on +z side.

Simplify: just put the head directly on top of the pole slightly offset. And a glow disc on the ground below.

Let's keep the pole and a lamp head box at the top. Simple.

For instancing with a matrix: use `new THREE.Matrix4().compose(pos, quat, scale)`.

Fine.

Trees: in parks and along sidewalks. Instanced trunk (cylinder) + foliage (icosahedron/sphere scaled). Let's place trees in parks (8-15 each) and along some sidewalks.

Total trees maybe 200. Two instanced meshes.

Now traffic lights. For each intersection (i,j) with i,j in 0..GRID:
Position: (i*S - HALF, 0, j*S - HALF).
Corners: 4 corners at (±(ROAD/2+1), ±(ROAD/2+1)).

For each corner, place a pole of height 5.5 and a signal head at the top facing the road.

Head color depends on the direction it controls. A corner pole serves the traffic approaching from... Let's simplify: for each intersection, place 4 heads, one per approach direction. The head is placed across the intersection from the approach.

Hmm, let's simplify to: each intersection has 4 poles at the 4 corners; each pole gets a head colored by the phase for one axis. Corners at (+x,+z) and (-x,-z) control the X traffic; corners at (-x,+z) and (+x,-z) control the Z traffic.

So instanceColor per pole = green/red based on the axis.

I'll create the traffic light as a single instanced mesh (pole + head combined? no, different geometry). Use two instanced meshes: poles (cylinder) and heads (box). Both with 4*81 = 324 instances.

Actually, we could reduce by only having poles at 2 corners. Eh, 324 instances is one draw call each. Fine.

Head colors: for X-axis poles, color = isGreenX ? 0x00ff44 : 0xff2200, with yellow during transition. Let's compute:

```js
const p = lightPhase(ni,nj,t);
let xState; // 'g','y','r'
if(p<0.42) xState='g'; else if(p<0.48) xState='y'; else xState='r';
```
And the Z axis gets green when p is in [0.5, 0.92], yellow [0.92,0.98], red otherwise.

Good.

For isGreenX used in car logic: xState==='g'.

Now vehicles.

Let's write the Vehicle class.

```js
class Vehicle {
  constructor(opts){ ... }
}
```

Hmm, let's use plain objects with functions for speed of writing.

Car state fields:
- i, j: current node indices
- dir: 0..3
- t: distance along segment
- speed
- maxSpeed
- lateral: current lateral offset (lerped)
- pos: THREE.Vector3 (smoothed)
- heading: number (smoothed)
- mesh: THREE.Group

Update:
1. Determine target speed.
2. Accelerate/brake.
3. Move t += speed*dt.
4. If t >= S: advance to next node, choose new dir.
5. Compute ideal position & heading.
6. Smooth.

Let's write:

```js
const DIRV = [ new THREE.Vector2(1,0), new THREE.Vector2(-1,0), new THREE.Vector2(0,1), new THREE.Vector2(0,-1) ];
const RIGHTV = [ new THREE.Vector2(0,1), new THREE.Vector2(0,-1), new THREE.Vector2(-1,0), new THREE.Vector2(1,0) ];
```

Node world position: `nx = i*S - HALF`, `nz = j*S - HALF`.

Ideal position = node + dir*t + right*LANE*latScale.

Wait: for the vehicle to be at lane offset, we use RIGHTV[dir]*LANE. Plus, for the hero overtaking, lateral can be 0 or -LANE.

Let's store `laneOffset` per vehicle (default LANE) and lerp toward a target.

Position: p = (node.x + dir.x*t + right.x*off, 0, node.z + dir.z*t + right.y*off).

Heading angle: atan2(dir.x, dir.z).

When turning at a node, the position jumps instantaneously at the corner. To smooth, we lerp the visual position. But at high speed, the lerp creates a rounded corner — which is what we want.

Use `visPos.lerp(idealPos, 1 - Math.exp(-dt*8))`. And heading smoothed similarly, or better, derive heading from the velocity (change in visPos). Let's derive heading from movement:

```js
const vel = visPos.clone().sub(prevPos);
if(vel.lengthSq() > 0.0001) targetHeading = Math.atan2(vel.x, vel.z);
```
Then smooth heading toward targetHeading with angle wrapping.

Hmm, deriving from movement means at a stop, heading stays. That's fine.

Actually, computing heading from the smoothed position gives natural cornering. And drift = angle difference. Let's use that.

But careful: when reversing... not applicable.

Let's do:
- idealPos computed each frame.
- visPos lerps toward idealPos.
- velocity = (visPos - prevVisPos)/dt → direction.
- headingTarget = atan2(vel.x, vel.z) if speed > 0.5 else keep.
- heading = smooth toward headingTarget.

Then mesh.position.copy(visPos); mesh.rotation.y = heading (+ drift offset for the hero).

For the drift effect, we add `driftAngle` to the hero's mesh rotation. driftAngle accumulates based on turning rate and decays:

```js
const turnRate = angleDelta(heading, prevHeading)/dt;
driftAngle += (-turnRate * speed * 0.02 - driftAngle) * Math.min(1, dt*3);
```
Hmm. Let's do: `targetDrift = clamp(-turnRate * speed * 0.04, -0.6, 0.6)`, and driftAngle lerps toward it. That means when turning left (positive turn rate), the car yaws right (negative)... Actually for a drift, the car's nose points into the turn more than the velocity direction. When turning left, the heading is left of the velocity, so the mesh should rotate further left: driftAngle = +turnRate * something. Let's just use `targetDrift = clamp(turnRate * speed * 0.05, -0.7, 0.7)` and add to heading. Sign might be wrong but visually it's just an oversteer look. Let's think: if the car is turning left (turnRate > 0, since yaw increases counterclockwise when viewed from above... in three.js, rotation.y positive rotates from +Z toward +X, which is clockwise when viewed from above (+Y down)? Let's see: rotation.y = θ, forward = (sin θ, 0, cos θ). At θ=0, forward = +Z. At θ=π/2, forward = +X. Going from +Z to +X... viewed from above (looking down -Y), with X to the right and Z toward the viewer (down on screen)... hmm. In a standard top-down view with X right and Z down (screen), +Z→+X is going from down to right = counterclockwise on screen? Down (0,1) to right (1,0) — that's counterclockwise if we consider screen coords y-down. Ugh.

Doesn't matter much. Let's set driftAngle = -turnRate*speed*0.05 clamped, and just check visually... I can't check. Let me reason properly.

We want: when the car turns, the nose points more into the turn than the velocity direction. The velocity direction IS the heading we compute. If we add drift in the same direction as the turn, the nose points further into the turn. turnRate has the same sign as the direction of heading change. So driftAngle = k * turnRate with k>0 adds more rotation in the turning direction. So `targetDrift = clamp(turnRate * speed * 0.05, -0.6, 0.6)`.

Wait, if drifting, the car's nose points inside the turn (toward the apex), and the rear slides out. Yes, so nose points further into the turn than the velocity. So driftAngle should be in the same direction as the turn. ✓. Use k = 0.04, clamp ±0.5.

Good.

Additionally, add a slight lateral slide: not needed visually.

Now traffic AI:

```js
function updateVehicle(v, dt){
  let desired = v.maxSpeed;
  
  // Traffic light
  const ni = v.i + DIRV[v.dir].x, nj = v.j + DIRV[v.dir].y;
  const distToNode = S - v.t;
  if(ni>=0 && ni<=GRID && nj>=0 && nj<=GRID && !v.ignoreLights){
    const state = axisState(ni, nj, v.dir, time);
    if(state !== 'g' && distToNode < 30 && distToNode > 6){
      desired = Math.min(desired, ...);
    }
  }
  ...
}
```

Hmm, need a smooth deceleration. Simple approach: 

```js
if (shouldStop) {
  const d = distToNode - 6; // distance to stop line
  desired = Math.max(0, Math.min(desired, d * 0.8));  // speed proportional to distance
}
```
That gives a natural slowdown. Use a factor so the car stops smoothly. d*0.8 means at d=20, speed 16. Reasonable.

Actually a better model: desired = sqrt(2*a*d) with a=8. Let's use `desired = Math.min(desired, Math.sqrt(Math.max(0, 2*6*d)))` → at d=10 → sqrt(120)=11. OK.

And car-following: find the nearest car ahead in the same lane.

```js
let gap = Infinity;
for(const o of vehicles){
  if(o===v) continue;
  if(o.i===v.i && o.j===v.j && o.dir===v.dir && o.t > v.t){ gap = Math.min(gap, o.t - v.t); }
}
```
But cars near a node boundary: a car that just passed the node has different i,j. Slight inconsistency, but ok.

If gap < 20: desired = min(desired, sqrt(max(0, 2*8*(gap-4.5)))).

For the hero with overtaking: if gap < 18 and the hero isn't already overtaking, set laneTarget to -LANE (overtake lane) and reduce... Actually the hero should just switch lanes and keep speed.

Let's implement hero lateral:
```js
if (heroOvertake) { hero.laneTarget = -LANE*0.9 } else { hero.laneTarget = LANE*0.9 }
```
Wait, the lane offset is relative to the direction's right vector. Negative offset means the opposite lane (oncoming). Yes.

Hero overtake decision: if a traffic car is ahead within 18 units in the same lane and speed is high, start overtaking for ~2.5s or until past.

Also check oncoming traffic? Nah.

Now, the "hero route": choose directions at intersections. Prefer going straight (60%), left/right (40%). Also avoid leaving the city.

For police: choose the direction that minimizes distance to the hero. Compute for each valid direction the next node position and pick the one closest to the hero's position. Also, since police shouldn't stop at lights, set ignoreLights = true. And they should be fast.

Also, police cars should be near the hero. Spawn at a node near the hero (a few blocks away).

Wanted level: let's start at 0. After ~8 seconds, set to 1 and spawn 2 police. Then increase every ~12s by 1 up to 5, adding police.

Actually let's make it: wanted level = 1 + floor(elapsed/15) capped at 5, starting at t=6. Police count = wanted*2.

Police despawn if too far? Keep it simple: keep them.

Hmm, but police spawning right on top of the hero would look odd. Spawn at a node 2-3 blocks away, moving toward the hero.

Let's write a spawnPolice() that picks a node with distance 60-160 from the hero.

OK.

Now, collisions between the hero and traffic/police? Skip, but the hero should avoid. Keep simple.

Camera:

```js
const camMode = { type:'chase', timer: 4 };
```
Cinematic modes: 'low' (in front, low), 'side', 'top', 'chase'. Switch every ~6 seconds, with chase being the default ~60% of the time.

Chase camera: target position = hero.pos + behind * distance + up * height, where behind = -heroForward * 8 + up*4. Smooth lerp.

For cinematic: pick a position and look at the hero.

Let's implement a camera state machine:

```js
let camTimer = 0, camMode = 'chase', camDuration = 6;

function updateCamera(dt){
  camTimer += dt;
  if (camTimer > camDuration) {
    camTimer = 0;
    const modes = ['chase','chase','chase','side','front','low','top'];
    camMode = modes[Math.floor(Math.random()*modes.length)];
    camDuration = camMode==='chase' ? 6 : 3.5;
  }
  ...
}
```

For the cinematic modes, use a static position computed at mode start relative to the hero, and slightly move (e.g., dolly). Let's compute at mode switch: store `camOffset` in hero-local space.

E.g., side: offset = right*10 + up*3, look at hero.
front: offset = forward*12 + up*1.5.
low: offset = forward*6 + up*0.8.
top: offset = up*30, slightly behind.

Then camera position = hero.pos + offset (world), smoothed. For chase, the offset is behind.

Since the hero moves fast, static cinematic cameras will lose the hero quickly. Better: keep the camera attached with the offset but allow some lag. Actually, "cinematic" moments where the camera is briefly fixed in world space as the car passes is very GTA-like. But we also need to keep the action visible.

Compromise: For cinematic modes, set the camera position once (world-fixed) and look at the hero. Duration 2.5-3s. Since the hero moves at ~20 m/s, in 3s it travels 60m — it would fly past the camera. Hmm. Then the camera would look at it from behind. That's actually a nice "car passes by" shot but the car goes away.

Let's make cinematic modes track with an offset but with a different, more dynamic offset:
- 'side': the camera is at hero.pos + right*9 + up*2.5, looking at the hero. It tracks alongside. Nice.
- 'front': camera ahead of the hero, looking back at it, offset = forward*10 (computed from the hero's forward at that moment) — but if it's world-fixed, the hero drives into it. Let's make it track: camera = hero.pos + forward*9 + up*1.2 looking at hero. As the hero moves forward, the camera moves too, staying ahead. This looks like a "leading" shot. Good.
- 'low': camera = hero.pos + right*3 + up*0.7, looking at the hero but slightly ahead (look at hero.pos + forward*5).
- 'top': camera = hero.pos + up*28 - forward*5, looking down.
- 'chase': standard.

All tracking, with smoothing. That keeps the action visible and gives varied angles. Good.

For extra flavor, add a slight lag: use a smoothed camera position.

Let's implement: for each mode, compute `desiredPos` and `lookAt`. Then `camera.position.lerp(desiredPos, 1-exp(-dt*k))` with k depending on mode (higher for chase for tightness, lower for cinematic for smoothness). And the lookAt target also smoothed.

Ok.

Minimap: draw on a 2D canvas. Each frame:
- clear
- translate to center, scale
- draw roads as lines: for each grid line, a line.
- draw traffic cars as small dots (white/gray), police as red dots, hero as a green/cyan triangle.
- Actually rotating the map so the hero faces up is nicer. Let's do north-up for simplicity, hero centered, with the hero as an arrow rotated by heading.

Scale: show 200 world units across a 180px canvas → scale = 180/200 = 0.9 px per unit.

Draw: 
```js
ctx.setTransform(1,0,0,1,0,0);
ctx.clearRect(0,0,size,size);
ctx.save();
ctx.translate(size/2, size/2);
ctx.scale(sc, sc);
ctx.translate(-hero.x, -hero.z);
// roads
ctx.strokeStyle='#555'; ctx.lineWidth = ROAD;
for each grid line: moveTo(x, -HALF-...); lineTo(x, HALF+...)
...
```
Hmm, with lineWidth = ROAD in scaled units, the line width scales too. Good.

Then restore and draw dots.

Let's use a separate transform for dots so they have constant size. Actually simpler: draw everything in the scaled space, with dot radius = 2/sc.

Fine.

HUD: speed text (km/h) and wanted stars.

Let's use DOM elements for the speed and wanted level, and a canvas for the minimap.

Speed: display as `Math.round(speed*3.6*3)` to look fast? Our car speeds: hero max ~28 m/s = 100 km/h. That's realistic. But it'll look fast enough? In a 464-unit city, 28 m/s crosses the city in 16s. That's fast. Good.

Actually the scale: 1 unit = 1 meter. Buildings 44m blocks. Roads 14m wide. That's realistic. Car length 4.2m. Good.

Hero speed: 25 m/s = 90 km/h. Traffic: 9-13 m/s.

Hmm, with the camera FOV 62 and speed 25 m/s, motion should feel good.

Let's make the hero faster: 30 m/s max (108 km/h), and boost sometimes.

OK, let's write.

One more thing: the hero should brake at lights. But if it brakes at every red light, it will be stop-and-go a lot. That's fine and realistic. Add: hero runs reds occasionally (10% chance)? The requirement says "braking at lights". Let's have it brake but with a slightly higher tolerance — it brakes hard and sometimes squeaks through on yellow.

Let's implement: hero stops if the light is red/yellow and distToNode > 6 and distToNode < 30.

Let's just do it.

Now, the drift on corners: the hero takes corners fast. With lane-graph movement, speed through the intersection isn't reduced much. Let's have the hero brake slightly before turns.

Actually, the hero's turn decision is made at the node. We could look ahead: when distToNode < 20 and the chosen direction will be a turn, reduce speed. But the direction is chosen at the node. Let's pre-choose the next direction when entering the segment. Store `nextDir`. Then the hero can prepare.

Let's do that: when a vehicle advances to a new segment, it picks `pendingDir` for the next node. Then it can check if the upcoming turn is sharp and brake.

Simplify: for the hero, when distToNode < 15 and pendingDir != dir (a turn), target speed = maxSpeed * 0.55. That gives a nice corner entry, and combined with the drift it looks great.

OK.

Let me now write all the code properly.

```js
// ============ Utility ============
function rand(a,b){ return a + Math.random()*(b-a); }
function randInt(a,b){ return Math.floor(rand(a,b+1)); }
function clamp(v,a,b){ return Math.max(a, Math.min(b,v)); }
function lerp(a,b,t){ return a+(b-a)*t; }
function angleLerp(a,b,t){ let d = b-a; while(d>Math.PI) d-=2*Math.PI; while(d<-Math.PI) d+=2*Math.PI; return a+d*t; }
```

Now let's write the whole thing.

I'll write the code in order.

```js
import * as THREE from 'three';

/* ---------- basic setup ---------- */
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x8fa6c0, 0.0022);

const camera = new THREE.PerspectiveCamera(62, window.innerWidth/window.innerHeight, 0.4, 2200);

window.addEventListener('resize', ()=>{
  camera.aspect = window.innerWidth/window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});
```

Tone mapping with ACES might make things dark. Let's use NoToneMapping to keep colors predictable. Actually ACES gives nicer skies. Hmm. Let's use ACESFilmic with exposure 1.1.

Careful: With tone mapping, the emissive night stuff looks nicer. OK.

Sky shader with ACES... the sky colors will be desaturated. Fine.

Let's use `renderer.toneMapping = THREE.ACESFilmicToneMapping`.

Hmm, actually to keep control, let's skip tone mapping (NoToneMapping) and just use sRGB output. Colors will be exactly as specified. I'll go with that for predictability.

Let's continue.

Now the full code. I'll write it out.

```js
/* ---------- constants ---------- */
const GRID = 8;
const BLOCK = 44;
const ROAD = 14;
const S = BLOCK + ROAD;         // 58
const CITY = GRID * S;          // 464
const HALF = CITY / 2;
const LANE = 3.4;
const ROADH = ROAD / 2;
const SW_H = 0.35;
```

Wait: block centers at i*S + S/2 - HALF where S/2 = 29. Block half = 22. Road half = 7. So the block spans from center-22 to center+22, and the road starts at 22 from the center... Let's verify: block center at i*S + 29. Block spans [i*S+7, i*S+51]. Road center at i*S spans [i*S-7, i*S+7]. Next road at (i+1)*S spans [(i+1)*S-7, (i+1)*S+7] = [i*S+51, i*S+65]. ✓ Perfect tiling.

Good, so the world spans from -HALF-ROADH... Let's define the world coordinate as `worldX(i) = i*S - HALF`. Node (0,0) at (-232, -232). Node (GRID,GRID) at (232,232). The city extends from -239 to 239 (including road halves). Good.

Now, the ground plane should cover ±(HALF+200).

Let's write everything.

```js
/* ---------- lights ---------- */
const hemi = new THREE.HemisphereLight(0xbfd4ff, 0x3a3a30, 0.8);
scene.add(hemi);
const sunLight = new THREE.DirectionalLight(0xfff2dd, 1.5);
sunLight.position.set(100, 150, 60);
scene.add(sunLight);
const moonLight = new THREE.DirectionalLight(0x8899ff, 0.0);
scene.add(moonLight);
```

Actually, let's use one directional light and change its color/intensity with the sun elevation. And a hemisphere light as ambient.

Now, let's write the sky update:

```js
function updateSky(t){
  const dayPhase = (0.18 + t/72) % 1;
  const a = dayPhase * Math.PI * 2;
  const sunDir = new THREE.Vector3(Math.cos(a)*0.55, Math.sin(a), Math.cos(a)*0.75).normalize();
  ...
}
```
Hmm, `Math.cos(a)` appears twice; at a=π/2 (noon), cos=0 → sunDir=(0,1,0) directly overhead. At a=0 → (0.55, 0, 0.75) normalized — sun at the horizon in the +x+z direction. At a=π → (-0.55,0,-0.75) — the opposite horizon. Good, sunrise/sunset on the x-z diagonal.

Wait, but at a=0 the sun is at the horizon and at a=π it's also at the horizon. Between (a in (π, 2π)), sin(a) < 0 → the sun is below the horizon → night. Good.

Elevation = sunDir.y.

Let's compute:
- `sunUp = clamp(sunDir.y, 0, 1)`.
- `daylight = smoothstep(-0.1, 0.15, sunDir.y)`.

Colors:
- At night: sky top 0x050a1a, bottom 0x131a2e.
- At day: top 0x2b6fd6, bottom 0x9dc4e8.
- At sunrise/sunset: bottom orange.

Let's compute with a few lerps:

```js
const nightCol = new THREE.Color(0x05070f);
const duskCol = new THREE.Color(0xd2603a);
const dayCol = new THREE.Color(0x3f86e0);
const dayBot = new THREE.Color(0xa8c8e8);
const nightBot = new THREE.Color(0x101828);
```

Blend: 
```js
const horizonT = clamp(sunDir.y*3 + 0.5, 0, 1); // 
```
Eh, let's simplify:

```js
const elev = sunDir.y;
const dayF = clamp((elev+0.12)/0.35, 0, 1);       // 0 night, 1 day
const duskF = clamp(1 - Math.abs(elev)/0.25, 0, 1); // peak at horizon
```

top = mix(nightTop, dayTop, dayF) then mix with dusk orange by duskF*0.8.
bottom = mix(nightBot, dayBot, dayF) then mix with dusk orange.

Then apply to the shader uniforms.

Sun light color: mix(orange, white, clamp(elev/0.4,0,1)).
Sun light intensity: clamp(elev,0,1)*1.6 + 0.05.
Moon: intensity = clamp(-elev,0,1)*0.25.

Hemisphere: intensity = 0.15 + dayF*0.75.

Street lights on when dayF < 0.35.

That's manageable.

Let's have a function `updateEnvironment(dt, elapsed)`.

Now let me actually write everything out. It's long but let's go.

I'll write the code now in final form.

```js
/* =========================================================
   CITY GEOMETRY
   ========================================================= */
const cityGroup = new THREE.Group();
scene.add(cityGroup);

// ground
{
  const g = new THREE.PlaneGeometry(CITY + 600, CITY + 600);
  g.rotateX(-Math.PI/2);
  const m = new THREE.MeshLambertMaterial({ color: 0x2c3a2a });
  const mesh = new THREE.Mesh(g, m);
  mesh.position.y = -0.02;
  cityGroup.add(mesh);
}
```

Roads...

```js
function makeRoadTexture(alongX){
  const LEN = 256, WID = 64;
  const c = document.createElement('canvas');
  c.width = alongX ? LEN : WID;
  c.height = alongX ? WID : LEN;
  const g = c.getContext('2d');
  g.fillStyle = '#35363c';
  g.fillRect(0,0,c.width,c.height);
  for(let i=0;i<500;i++){
    g.fillStyle = 'rgba(255,255,255,'+(Math.random()*0.03).toFixed(3)+')';
    g.fillRect(Math.random()*c.width, Math.random()*c.height, 3, 3);
  }
  g.fillStyle = 'rgba(230,230,215,0.45)';
  if(alongX){ g.fillRect(0, 4, LEN, 2); g.fillRect(0, WID-6, LEN, 2); }
  else { g.fillRect(4, 0, 2, LEN); g.fillRect(WID-6, 0, 2, LEN); }
  g.fillStyle = 'rgba(245,220,110,0.8)';
  if(alongX){ for(let x=0;x<LEN;x+=32){ g.fillRect(x, WID/2-1.5, 16, 3); } }
  else { for(let y=0;y<LEN;y+=32){ g.fillRect(WID/2-1.5, y, 3, 16); } }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.anisotropy = 8;
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
```

Note: `t.colorSpace = THREE.SRGBColorSpace` for canvas textures used as color maps. In r186, texture.colorSpace is the property. Yes.

Roads:
```js
const ROAD_LEN = CITY + ROAD*2 + 40;
{
  const texX = makeRoadTexture(true);
  texX.repeat.set(ROAD_LEN/64, 1);
  const texZ = makeRoadTexture(false);
  texZ.repeat.set(1, ROAD_LEN/64);
  const matX = new THREE.MeshLambertMaterial({ map: texX });
  const matZ = new THREE.MeshLambertMaterial({ map: texZ });
  const geoX = new THREE.PlaneGeometry(ROAD_LEN, ROAD).rotateX(-Math.PI/2);
  const geoZ = new THREE.PlaneGeometry(ROAD, ROAD_LEN).rotateX(-Math.PI/2);
  for(let i=0;i<=GRID;i++){
    const p = i*S - HALF;
    const mx = new THREE.Mesh(geoX, matX);
    mx.position.set(0, 0.01, p);
    cityGroup.add(mx);
    const mz = new THREE.Mesh(geoZ, matZ);
    mz.position.set(p, 0.01, 0);
    cityGroup.add(mz);
  }
}
```
Wait, geoX is a plane of width ROAD_LEN along x and height ROAD along z. So the mesh position z = p (road along X at z=p) ✓. And geoZ is width ROAD along x, height ROAD_LEN along z; positioned at x = p ✓.

Note: `PlaneGeometry(...).rotateX()` returns the geometry (rotateX returns `this`). Yes.

Hmm — the texture repeat is set on the shared texture. texX.repeat.x = ROAD_LEN/64 ≈ 480/64 = 7.5. Each tile = 64 world units along the road. Dash cycle = 32px of 256px = 1/8 tile = 8 world units → dash 4 units, gap 4 units. Good.

But across the road: for texX, the canvas is 64 wide (the road width direction). The plane is 14 wide. So the texture is squeezed from 64 to 14 units. The edge lines at x=4 and x=58 → at 4/64*14 = 0.875 and 12.7 units from the edge. Good — about 1 unit from each edge.

Center dashes at x=32 → center of the road ✓.

For texZ, canvas 64 wide = across the road, 256 tall = along. repeat.y = 7.5. Same.

OK good.

Sidewalks and blocks.

```js
const facadeTex = makeFacade(0);  // returns {map, emissive}
```

Let me write makeFacade:

```js
function makeFacadeTexture(){
  const T = 128;
  const c = document.createElement('canvas');
  c.width = c.height = T;
  const g = c.getContext('2d');
  // base wall
  g.fillStyle = '#b9b4ab';
  g.fillRect(0,0,T,T);
  // slight noise
  for(let i=0;i<800;i++){
    g.fillStyle = 'rgba(0,0,0,'+(Math.random()*0.05).toFixed(3)+')';
    g.fillRect(Math.random()*T, Math.random()*T, 2, 2);
  }
  const e = document.createElement('canvas');
  e.width = e.height = T;
  const ge = e.getContext('2d');
  ge.fillStyle = '#000';
  ge.fillRect(0,0,T,T);

  const cols = 4, rows = 4;
  const cw = T/cols, ch = T/rows;
  for(let i=0;i<cols;i++) for(let j=0;j<rows;j++){
    const x = i*cw + cw*0.22, y = j*ch + ch*0.2;
    const w = cw*0.56, h = ch*0.5;
    g.fillStyle = '#3c4a58';
    g.fillRect(x,y,w,h);
    g.fillStyle = 'rgba(255,255,255,0.12)';
    g.fillRect(x,y,w,h*0.3);
    if(Math.random() < 0.55){
      ge.fillStyle = ['#ffcf87','#ffd9a0','#c9e2ff'][Math.floor(Math.random()*3)];
      ge.fillRect(x,y,w,h);
    }
  }
  const map = new THREE.CanvasTexture(c);
  const emi = new THREE.CanvasTexture(e);
  [map, emi].forEach(t=>{ t.wrapS=t.wrapT=THREE.RepeatWrapping; t.anisotropy=4; });
  map.colorSpace = THREE.SRGBColorSpace;
  emi.colorSpace = THREE.SRGBColorSpace;
  return { map, emi };
}
```

Tile = 8 world units with 4x4 windows = 16 windows per 8x8 units → window every 2 units. Too dense. Let's use TILE = 12 or reduce cols/rows to 2x2.

Let's use cols=2, rows=2 and tile = 7 world units. Window every 3.5 units → windows 2 units wide, 2 units tall. Reasonable for a building.

Actually windows are typically 1.5m wide with 1m spacing → 2.5m spacing. So a tile of 7 units with 2 windows → 3.5m spacing. Fine.

Let's use TILE = 7.

Hmm, but with Math.round(fw/TILE) the tiling might mismatch between the top and bottom of the building. It's fine.

Actually, using round() means the UV scale is an integer, so the pattern aligns at edges. Good.

Let's use TILE = 6.5, cols=2, rows=2.

Eh, just use TILE = 7.

OK.

Now, buildings.

```js
const buildingMats = [];
const palette = [0xdfd8cc, 0xc9c2b4, 0xb8bcc4, 0xd6c7b0, 0xa8aeb8, 0xe0d5c5];
for(const p of palette){
  const m = new THREE.MeshLambertMaterial({ map: facade.map, emissiveMap: facade.emi, emissive: 0x000000, color: p });
  buildingMats.push(m);
}
```
Hmm, `color` multiplies the map. The map base is #b9b4ab (light gray). Multiplying by 0xdfd8cc gives a slightly warm gray. Good.

Roof material: `new THREE.MeshLambertMaterial({ color: 0x6a6a68 })`.

Wait, but the roof material needs an emissive update too? No.

Side materials: buildingMats[i]. We need a material array [side, side, roof, roof, side, side].

Now, at night, we set emissive on all buildingMats. Fine.

Building geometry:

```js
function buildingGeometry(w,h,d){
  const geo = new THREE.BoxGeometry(w,h,d);
  const uv = geo.attributes.uv;
  const TILE = 7;
  const dims = [[d,h],[d,h],[w,d],[w,d],[w,h],[w,h]];
  for(let f=0;f<6;f++){
    if(f===2||f===3) continue;
    const su = Math.max(1, Math.round(dims[f][0]/TILE));
    const sv = Math.max(1, Math.round(dims[f][1]/TILE));
    for(let k=0;k<4;k++){
      const idx = f*4+k;
      uv.setXY(idx, uv.getX(idx)*su, uv.getY(idx)*sv);
    }
  }
  uv.needsUpdate = true;
  return geo;
}
```

Hmm wait: BoxGeometry might not have 4 vertices per face in the order I assume — it does: 6 faces × 4 verts = 24 verts. ✓

Now blocks:

```js
const parkSpots = [];  // for minimap maybe

for(let i=0;i<GRID;i++){
  for(let j=0;j<GRID;j++){
    const cx = i*S + S/2 - HALF;
    const cz = j*S + S/2 - HALF;
    // sidewalk slab
    const slab = new THREE.Mesh(new THREE.BoxGeometry(BLOCK, SW_H, BLOCK), sidewalkMat);
    slab.position.set(cx, SW_H/2, cz);
    cityGroup.add(slab);
    
    const isPark = Math.random() < 0.16;
    if(isPark) buildPark(cx, cz);
    else buildBuildings(cx, cz, i, j);
  }
}
```

Hmm, creating a new BoxGeometry per block is 64 geometries. Fine.

sidewalkMat = MeshLambertMaterial({color: 0x9a9a94}).

buildBuildings:

```js
function buildBuildings(cx, cz, bi, bj){
  const nx = Math.random()<0.6?2:3;
  const nz = Math.random()<0.6?2:3;
  const lotW = BLOCK/nx, lotD = BLOCK/nz;
  const cityCenterDist = Math.hypot(cx, cz) / HALF; // 0 center, 1 edge
  for(let a=0;a<nx;a++){
    for(let b=0;b<nz;b++){
      if(Math.random()<0.12) continue; // gap
      const lx = cx - BLOCK/2 + lotW*(a+0.5);
      const lz = cz - BLOCK/2 + lotD*(b+0.5);
      const w = lotW - rand(3,7);
      const d = lotD - rand(3,7);
      let h = rand(8, 22) + (1-cityCenterDist)*rand(0,20);
      if(Math.random()<0.08) h *= 1.8;
      h = Math.min(h, 60);
      const geo = buildingGeometry(w,h,d);
      const mat = buildingMats[Math.floor(Math.random()*buildingMats.length)];
      const mesh = new THREE.Mesh(geo, [mat,mat,roofMat,roofMat,mat,mat]);
      mesh.position.set(lx, SW_H + h/2, lz);
      cityGroup.add(mesh);
    }
  }
}
```

That gives up to 9 buildings per block. With 54 building blocks × avg 4 = 216 buildings. Hmm, that's a lot of draw calls. Let's reduce: nx,nz ∈ {1,2} mostly. With BLOCK=44, nx=1 → lot 44 wide, building ~38 wide. That's a big building. Fine.

Let's use nx = Math.random()<0.5?1:2. So avg 1.5 × 1.5 = 2.25 buildings per block minus gaps ≈ 2. 54 blocks × 2 = 108 buildings. Good.

Hmm, but with nx=1, lotW=44, building w=44-5=39 wide. That's a big footprint. With a height of 20, that's a wide slab building. OK, looks fine.

Let's mix: nx = randInt(1,2), nz = randInt(1,2).

OK. And if the building is huge (w>30), make it a bit taller on average.

Fine.

buildPark:

```js
function buildPark(cx, cz){
  const grass = new THREE.Mesh(new THREE.PlaneGeometry(BLOCK-2, BLOCK-2).rotateX(-Math.PI/2), grassMat);
  grass.position.set(cx, SW_H+0.01, cz);
  cityGroup.add(grass);
  // trees
  const n = randInt(5, 10);
  for(let k=0;k<n;k++){
    const tx = cx + rand(-BLOCK/2+4, BLOCK/2-4);
    const tz = cz + rand(-BLOCK/2+4, BLOCK/2-4);
    treeSpots.push([tx, tz, rand(0.8,1.5)]);
  }
  // path
  ...
}
```

Trees collected globally and built as instanced meshes at the end.

Also add street trees along sidewalks: for each block, a couple along the edges. Let's add 2-4 per block along the sidewalk edge.

Actually, let's just add trees from parks plus some along the block perimeters. Total maybe 300 trees. Instanced, so fine.

Hmm, instanced trees with per-instance scale — need to compose the matrix. Fine.

Let's do trees: trunk instanced (cylinder r=0.25, h=2.5) and foliage instanced (icosahedron r=2). Each with a per-instance position/scale.

For the foliage, we can also vary the color via instanceColor. Let's do that for variety.

OK.

Now, pedestrians. Let's define them after the blocks are built.

Now let's write the vehicle system.

```js
const VEHICLES = [];   // all cars (traffic + police + hero)
const PEDS = [];
```

Car creation:

```js
const carGeoBody = new THREE.BoxGeometry(1.9, 0.75, 4.4);
const carGeoRoof = new THREE.BoxGeometry(1.7, 0.6, 2.2);
const carGeoWheel = new THREE.CylinderGeometry(0.38, 0.38, 0.28, 10).rotateZ(Math.PI/2);
```
Careful: `CylinderGeometry(...).rotateZ()` returns the geometry. ✓

Wait, `rotateZ` on a geometry rotates the vertices. Cylinder axis is Y; rotating about Z by π/2 makes the axis along X. ✓

Car build:

```js
function makeCarMesh(color, type){
  const g = new THREE.Group();
  const bodyMat = new THREE.MeshLambertMaterial({ color });
  const body = new THREE.Mesh(carGeoBody, bodyMat);
  body.position.y = 0.72;
  g.add(body);
  const roofMat = new THREE.MeshLambertMaterial({ color: 0x22242a });
  const roof = new THREE.Mesh(carGeoRoof, roofMat);
  roof.position.set(0, 1.32, -0.15);
  g.add(roof);
  const wheelMat = new THREE.MeshLambertMaterial({ color: 0x141418 });
  for(const [x,z] of [[-0.98,1.4],[0.98,1.4],[-0.98,-1.4],[0.98,-1.4]]){
    const w = new THREE.Mesh(carGeoWheel, wheelMat);
    w.position.set(x, 0.38, z);
    g.add(w);
  }
  // headlights
  const hlMat = new THREE.MeshBasicMaterial({ color: 0xfff6cc });
  ...
}
```

Hmm, the headlights should only be visible at night. We can set their material color to black in the day. Since they're MeshBasicMaterial, we can update the color. Let's create shared materials `headMat` and `tailMat` and update them globally with the night factor.

headMat = MeshBasicMaterial({color: 0x000000}); tailMat similarly.

Front of car at +Z: headlights at z = 2.2, taillights at z = -2.2.

Add small boxes: BoxGeometry(0.45,0.18,0.1).

Let's create shared geometries for those too.

Then a fake shadow: a plane (circle) at y=0.02, size 2.4×5, dark, transparent, as a child of the group. But since the group rotates, it's fine.

Let's use a shared geometry: `new THREE.PlaneGeometry(2.4, 5).rotateX(-Math.PI/2)`.

Material: MeshBasicMaterial({color:0x000000, transparent:true, opacity:0.25, depthWrite:false}).

Hmm, this will z-fight with the road. Put it at y=0.05, and set the renderOrder... It's fine with depthWrite false and a small offset.

Actually, a transparent plane over the road: fine.

Hmm, but the road surface is at y=0.01 and the sidewalk at 0.35. The car's shadow at y=0.05 would be hidden by the sidewalk when on a sidewalk. Not an issue.

OK.

Police cars: white body with black doors? Just use white and add flashing lights (two small spheres, red and blue, on the roof). Animate the material color each frame.

Hero: a distinct color (e.g., 0xff3b30 red or a bright cyan). Let's make it a bright orange-red sports car, slightly lower and sleeker.

Let's now write the vehicle update.

```js
function createVehicle(opts){
  const v = {
    i: opts.i, j: opts.j, dir: opts.dir, t: opts.t || 0,
    speed: 0,
    maxSpeed: opts.maxSpeed,
    accel: opts.accel || 6,
    brake: opts.brake || 14,
    isHero: !!opts.isHero,
    isPolice: !!opts.isPolice,
    ignoreLights: !!opts.isPolice,
    lane: LANE,
    laneTarget: LANE,
    pos: new THREE.Vector3(),
    prevPos: new THREE.Vector3(),
    heading: 0,
    prevHeading: 0,
    drift: 0,
    pendingDir: opts.dir,
    mesh: makeCarMesh(opts.color, opts.isPolice?'police':'normal'),
  };
  ...
}
```

Set the initial position: compute from the node + dir*t + right*lane.

Let me write a helper:

```js
function lanePos(i, j, dir, t, lane){
  const d = DIRV[dir], r = RIGHTV[dir];
  return new THREE.Vector3(
    i*S - HALF + d.x*t + r.x*lane,
    0,
    j*S - HALF + d.y*t + r.y*lane
  );
}
```
Note DIRV as Vector2 with .x and .y where .y is the z component. OK.

Update:

```js
function updateVehicle(v, dt, time){
  // --- traffic light ---
  const dirv = DIRV[v.dir];
  const ni = v.i + dirv.x, nj = v.j + dirv.y;
  let desired = v.maxSpeed;
  const distToNode = S - v.t;

  const inBounds = ni>=0 && ni<=GRID && nj>=0 && nj<=GRID;

  if(inBounds && !v.ignoreLights){
    const st = getLightState(ni, nj, v.dir, time);
    if(st !== 'g' && distToNode > 7 && distToNode < 34){
      const d = distToNode - 7;
      desired = Math.min(desired, Math.sqrt(Math.max(0, 2*5*d)));
    }
  }
  
  // --- cornering speed for hero ---
  if(v.isHero && inBounds && v.pendingDir !== v.dir && distToNode < 22){
    desired = Math.min(desired, v.maxSpeed*0.5);
  }
  
  // --- car following ---
  let gap = 1e9;
  for(const o of VEHICLES){
    if(o === v || o.isPolice) continue;   // hmm, police should also be avoided
    if(o.i===v.i && o.j===v.j && o.dir===v.dir && o.t > v.t){
      gap = Math.min(gap, o.t - v.t);
    }
  }
  ...
}
```

Hmm, police cars also need to avoid each other. Let's include all vehicles in the gap check but only consider those ahead.

Actually, police should probably not be blocked. Let's include all vehicles in the gap calculation; the police will just weave... they can't weave. They'll follow. That's fine.

Let's include all vehicles (including the hero) for gap checks. Actually the hero is in the list too. So police will follow the hero at a distance. Hmm, for a chase, we want them close. It's fine — they'll be right behind.

OK, let's include everything.

```js
  if(gap < 22){
    const g = gap - 5.5;
    if(g <= 0) desired = 0;
    else desired = Math.min(desired, Math.sqrt(Math.max(0, 2*6*g)));
  }
```

Hmm, but for the hero overtaking, we want to ignore the gap constraint when in the overtake lane. Let's check: if v.laneTarget !== LANE (overtaking), skip the gap limit... but only if the gap is small and we're moving into the other lane. Let's just reduce it: if the hero is overtaking, gap threshold 12 instead of 22.

Alright, let's implement the hero overtake logic separately.

```js
  // hero overtaking
  if(v.isHero){
    if(gap < 20 && v.speed > 12 && !v.overtaking){
      v.overtaking = true; v.otTimer = 0;
    }
    if(v.overtaking){
      v.otTimer += dt;
      v.laneTarget = -LANE*0.85;
      if(v.otTimer > 2.5 || gap > 30) { v.overtaking=false; }
    } else {
      v.laneTarget = LANE;
    }
  }
```

Hmm, if overtaking, the gap check keeps it slow. Let's change: if `v.overtaking`, use a smaller safety gap.

Let me restructure: compute `gapLimit = v.overtaking ? 10 : 22`.

Hmm, when the hero overtakes, the car ahead is in the same lane logically (same i,j,dir,t) regardless of lateral position. So the gap limit applies. But in reality the hero is in the other lane now. So set gapLimit = 6 while overtaking.

OK.

Now acceleration:

```js
  if(v.speed < desired){
    v.speed = Math.min(desired, v.speed + v.accel*dt);
  } else {
    v.speed = Math.max(desired, v.speed - v.brake*dt);
  }
  v.speed = Math.max(0, v.speed);
```

Then advance:

```js
  v.t += v.speed*dt;
  while(v.t >= S){
    v.t -= S;
    v.i = v.i + DIRV[v.dir].x;
    v.j = v.j + DIRV[v.dir].y;
    v.dir = v.pendingDir;
    v.pendingDir = chooseDir(v);
  }
```

Wait, there's a bug: we advance to the node (i,j) becomes the next node, then dir becomes pendingDir which was chosen for that node. And then choose a new pendingDir for the following node.

But `chooseDir` needs to know from which direction we're arriving — that's `v.dir` before reassignment. Let's do:

```js
    const fromDir = v.dir;
    v.i += DIRV[fromDir].x;
    v.j += DIRV[fromDir].y;
    v.dir = v.pendingDir;
    v.pendingDir = chooseDir(v.i, v.j, v.dir, v);
```

And chooseDir(i, j, currentDir, v) picks a new direction that is valid from node (i,j) — i.e., the next node (i+dx, j+dz) must be within bounds, and not the reverse of currentDir unless it's the only option.

```js
function chooseDir(i, j, curDir, v){
  const opts = [];
  for(let d=0; d<4; d++){
    if(d === (curDir^1)) continue; // opposite dir; note: dir indices: 0=+x,1=-x,2=+z,3=-z, so opposite of 0 is 1, 2 is 3. XOR 1 works: 0^1=1, 1^1=0, 2^1=3, 3^1=2 ✓
    const ni = i + DIRV[d].x, nj = j + DIRV[d].y;
    if(ni<0||ni>GRID||nj<0||nj>GRID) continue;
    opts.push(d);
  }
  if(opts.length===0) return curDir^1;
  // prefer straight
  if(opts.includes(curDir) && Math.random()<0.6) return curDir;
  return opts[Math.floor(Math.random()*opts.length)];
}
```

For police, override with a pursuit choice.

OK.

Then compute the ideal position and smooth.

```js
  const ideal = lanePos(v.i, v.j, v.dir, v.t, v.lane);
  v.lane += (v.laneTarget - v.lane) * Math.min(1, dt*3);
  
  const k = 1 - Math.exp(-dt*10);
  v.prevPos.copy(v.pos);
  v.pos.lerp(ideal, k);
```

Hmm, but v.lane is used in lanePos before being updated — order matters slightly, not important.

Wait, there's an issue: lanePos uses v.lane, but we lerp v.lane after. Let's lerp first, then compute ideal.

Also, when the vehicle wraps around a node, the ideal position jumps by a corner. The lerp smooths it. Good.

Then heading:

```js
  const dx = v.pos.x - v.prevPos.x, dz = v.pos.z - v.prevPos.z;
  if(dx*dx+dz*dz > 1e-6){
    const target = Math.atan2(dx, dz);
    v.heading = angleLerp(v.heading, target, Math.min(1, dt*12));
  }
```

Hmm, but at the moment of the node transition, the position jumps smoothly so the velocity direction is smooth. Good.

Drift:
```js
  const turn = angleDiff(v.heading, v.prevHeading) / Math.max(dt, 1e-3);
  v.prevHeading = v.heading;
```

Hmm, prevHeading should be set after computing. Let's compute:

```js
  let turnRate = 0;
  if(dt > 0){
    let d = v.heading - v.prevHeading;
    while(d > Math.PI) d -= Math.PI*2;
    while(d < -Math.PI) d += Math.PI*2;
    turnRate = d/dt;
  }
  v.prevHeading = v.heading;
  
  const targetDrift = v.isHero ? clamp(turnRate * v.speed * 0.045, -0.55, 0.55) : 0;
  v.drift += (targetDrift - v.drift) * Math.min(1, dt*6);
  
  v.mesh.position.copy(v.pos);
  v.mesh.rotation.y = v.heading + v.drift;
```

Hmm, `v.heading + v.drift` — but the drift rotation makes the car not aligned with the direction of travel. Correct.

Also add suspension roll? Skip.

Now, the "t" for a vehicle that just spawned: it should be placed correctly at t.

Let me handle initial placement: create the vehicle, compute the ideal position from the initial state, and set v.pos = ideal.

Let me write the spawn function.

```js
function spawnVehicle(opts){
  const v = { ... };
  v.pos.copy(lanePos(v.i, v.j, v.dir, v.t, v.lane));
  v.prevPos.copy(v.pos);
  v.heading = Math.atan2(DIRV[v.dir].x, DIRV[v.dir].y);
  v.prevHeading = v.heading;
  v.mesh.position.copy(v.pos);
  v.mesh.rotation.y = v.heading;
  scene.add(v.mesh);
  VEHICLES.push(v);
  return v;
}
```

Hmm, `Math.atan2(dir.x, dir.z)` — DIRV[dir] is a Vector2 where .x = x and .y = z. So atan2(DIRV[dir].x, DIRV[dir].y). ✓

OK.

Now the hero. It starts somewhere in the city.

Police spawn: pick a random node far from the hero, pick a direction whose next node is valid, set t = 0.

Let's write:

```js
function spawnPolice(){
  const hero = HERO;
  let best = null, bestScore = -1;
  for(let k=0;k<20;k++){
    const i = randInt(1, GRID-1), j = randInt(1, GRID-1);
    const p = new THREE.Vector3(i*S-HALF, 0, j*S-HALF);
    const d = p.distanceTo(hero.pos);
    if(d > 60 && d < 200 && Math.random()*200 > bestScore){ ... }
  }
}
```

Simpler: pick a random node, compute distance to the hero, and accept if 80 < d < 250. Try 30 times.

OK.

Now the minimap and HUD.

Let's finalize the code. I'll write it all now carefully.

One thing: `time` used for the traffic lights — use a global `worldTime` that accumulates.

`getLightState(ni, nj, dir, time)`:
```js
function lightPhase(ni,nj,t){
  const off = (ni*0.37 + nj*0.61) % 1;
  return ((t*0.11 + off) % 1 + 1) % 1;
}
function getLightState(ni,nj,dir,t){
  const p = lightPhase(ni,nj,t);
  const isX = (dir===0||dir===1);
  const q = isX ? p : (p + 0.5) % 1;
  if(q < 0.42) return 'g';
  if(q < 0.48) return 'y';
  return 'r';
}
```
Cycle: t*0.11 → period ~9s. Full cycle in p of 1. X green for 0.42 of 9s = 3.8s. Hmm, a bit short. Use t*0.08 → 12.5s cycle → green 5.25s. Good.

Let me use `t*0.085`.

OK.

Now the traffic light visuals: for each intersection, 4 poles. Color based on getLightState for the axis.

Let's store the traffic light instances with their intersection and axis:
```js
const tlInstances = []; // {ni, nj, axis}
```
For each intersection, for each of the 4 corners, determine the axis: corners at (+x,+z) and (-x,-z) → the pole is associated with the X-axis traffic. Corners at (-x,+z) and (+x,-z) → Z-axis.

Hmm, actually the corner positions: the pole for controlling X traffic should be placed where the X traffic can see it — on the far side of the intersection. Meh, just place them.

Let me simplify: place 4 poles at the corners, and assign the axis as: corner (sx, sz) where sx,sz ∈ {-1,+1}. If sx === sz → X axis... whatever. Just do: if (sx*sz > 0) → X else Z. Consistent.

Actually let's just do 2 poles per intersection to reduce clutter... no, 4 looks better (one per corner). Fine.

Colors updated each frame.

InstancedMesh with instanceColor: need `mesh.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(count*3), 3)` or use `setColorAt`. `setColorAt` automatically creates instanceColor. Then set `instanceColor.needsUpdate = true` each frame after updates.

Material: MeshBasicMaterial({color: 0xffffff, vertexColors: false}) — instanceColor works with MeshBasicMaterial automatically in recent three versions. Yes, InstancedMesh with instanceColor works as long as the material supports color (basic does).

Hmm, one gotcha: if instanceColor exists, three multiplies `diffuse * instanceColor`. So set material.color = white.

OK.

Now, the street lamp glow at night: instanced planes with additive blending... InstancedMesh with a transparent additive material. The opacity should fade with night. Set material.opacity = night*0.5.

Hmm, the instanced mesh material's opacity is uniform, so we can update it globally. 

But additive blending on the ground with a soft circular texture: create a radial gradient canvas texture.

OK, let's do it.

Number of instances: 144 lamps.

Let's write:

```js
const lampPositions = [];  // {x, z, rot}
```

For each road line k (0..GRID) and each block index i (0..GRID-1):
- For the X-road at z = k*S-HALF: lamp at x = i*S + S/2 - HALF. Side: (i%2===0 ? 1 : -1). z offset = side*(ROADH+1.6)... wait, the lamp should be on the sidewalk, which starts at ROADH from the road center. The block edge is at 7 from the road center. So put the lamp at 7+1.5 = 8.5 from the road center. The block slab spans from 7 to 51 relative to the road center, i.e., from the block center ±22. The lamp at 8.5 from the road center is on the slab near its edge. ✓

So z = k*S - HALF + side*8.5.

Similarly for the Z-roads.

Total lamps: 9*8*2 = 144. OK.

Hmm, that's a lot of lamps (every 58 units). Fine.

Now trees along sidewalks: let's add trees in parks only, plus maybe some along block edges. Let's keep it simple: parks only, plus a few random sidewalk trees.

Number of trees: 64 blocks × 0.16 parks ≈ 10 parks × 8 trees = 80. Add 100 sidewalk trees → 180 total. Instanced: fine.

Let's add sidewalk trees at block corners-ish positions. Meh — just add 2 per block at random positions on the block slab edge.

OK.

Now pedestrians.

```js
const PEDS = [];
const pedGeoBody = new THREE.CapsuleGeometry(0.28, 0.7, 4, 8);
const pedGeoHead = new THREE.SphereGeometry(0.24, 8, 6);
```

Wait, CapsuleGeometry exists in three r140+. Yes.

Each pedestrian: a group with body + head. 2 meshes each. 60 pedestrians → 120 meshes.

Let's create a single material per pedestrian with a random color... that's 60 materials. Or use a few shared materials (6 colors). Let's use shared.

Pedestrian update: s += speed*dt; position from perimeter; heading from tangent.

Let's write:

```js
function pedPos(s, h, cx, cz){
  const P = 8*h;
  let p = ((s % P) + P) % P;
  let x, z, ang;
  if(p < 2*h){ x = -h + p; z = -h; ang = Math.PI/2; }
  else if(p < 4*h){ x = h; z = -h + (p-2*h); ang = 0; }
  else if(p < 6*h){ x = h - (p-4*h); z = h; ang = -Math.PI/2; }
  else { x = -h; z = h - (p-6*h); ang = Math.PI; }
  return {x: cx+x, z: cz+z, ang};
}
```

Wait, the heading: forward direction. For the first segment (moving +x), the heading angle = atan2(dx, dz) = atan2(1, 0) = π/2. ✓
Second (moving +z): atan2(0,1) = 0 ✓.
Third (moving -x): atan2(-1,0) = -π/2 ✓.
Fourth (moving -z): atan2(0,-1) = π ✓.

Good.

Set the mesh rotation.y = ang. Since the character model has no forward distinction, whatever.

Add a bob: y = SW_H + 0.85 + Math.sin(t*10 + phase)*0.05.

Hmm, capsule radius 0.28, length 0.7 → total height 1.26. Center at y = 0.63. Plus head at 1.26+0.15 = 1.4. Hmm, too short. Let's make the body capsule radius 0.22, length 0.9 → height 1.34. Position the body at y=0.67+... 

Let's model: legs+body as a capsule: radius 0.22, length 0.85 (cylinder part), total height 1.29. Positioned with its center at y = 1.29/2 + 0.35 (sidewalk) = ~1.0. Hmm, that makes a 1.3m tall person on a 0.35 sidewalk.

Let's use a capsule radius=0.25, length=1.0 → total height 1.5. Center at 0.75. Head sphere radius 0.22 at y=1.65.

Total height ~1.87. Good.

Group position at (x, SW_H + bob, z).

OK.

Number of pedestrians: 2 per non-park block, ~54*2 = 108. That's 216 meshes. Let's reduce to 1 per block → 54 pedestrians, 108 meshes. Hmm, sparse.

Let's do 2 per block but only for half the blocks: 54 peds. Meh.

Let's do: 90 pedestrians, 180 meshes. Combined with 40 cars × 6 = 240 meshes, buildings ~110, and instanced stuff. Total ~750 meshes.

Hmm. That's a lot but each is tiny. Modern GPUs handle 1000+ draw calls at 60fps usually. Let's go with it but be a bit conservative: 70 pedestrians, 32 traffic cars, 8 police.

32*6=192, 70*2=140, buildings 110 → ~450 + instanced + roads. ~500 draw calls. Good.

OK, let's finalize.

Actually, I realize I should double check the `CapsuleGeometry` signature: `CapsuleGeometry(radius, length, capSegments, radialSegments)`. Yes.

Now, let me write out the whole file.

Also: the hero car should have a "boost" sometimes and a target speed that varies. Let's give it a target speed of 26-32 m/s, varying.

Let me also handle the hero's traffic light braking: it stops. But then police catch up. Fine.

Let me write the final code.

One more consideration: the initial camera should be positioned right away so the first frame isn't weird.

Let's write.

```js
/* ============ MAIN LOOP ============ */
let lastTime = performance.now();
let elapsed = 0;
let worldTime = 0;

function animate(now){
  requestAnimationFrame(animate);
  const dt = Math.min(0.05, (now - lastTime)/1000);
  lastTime = now;
  elapsed += dt;
  worldTime += dt;
  
  updateEnvironment(dt, elapsed);
  updateTrafficLights(worldTime);
  updateVehicles(dt);
  updatePedestrians(dt, elapsed);
  updateWanted(dt, elapsed);
  updateCamera(dt);
  updateHUD();
  
  renderer.render(scene, camera);
}
```

Order matters: the hero should be updated before the police so the police can target the hero's new position. Let's update the hero first.

Let me restructure: `updateVehicles` loops over VEHICLES; the hero is first in the array. Since we iterate in order and the hero is index 0, it updates first. Good.

Now, let's write the minimap.

```js
const mapCanvas = document.getElementById('minimap');
const mctx = mapCanvas.getContext('2d');
const MAP_SIZE = 170;
const MAP_RANGE = 220;
```

Draw:
```js
function drawMinimap(){
  const s = MAP_SIZE / MAP_RANGE;
  mctx.clearRect(0,0,MAP_SIZE,MAP_SIZE);
  mctx.save();
  mctx.beginPath();
  mctx.rect(0,0,MAP_SIZE,MAP_SIZE);
  mctx.clip();
  mctx.fillStyle = '#0e1218';
  mctx.fillRect(0,0,MAP_SIZE,MAP_SIZE);
  mctx.translate(MAP_SIZE/2, MAP_SIZE/2);
  mctx.scale(s, s);
  mctx.translate(-HERO.pos.x, -HERO.pos.z);
  // roads
  mctx.strokeStyle = '#2f3742';
  mctx.lineWidth = ROAD;
  mctx.beginPath();
  for(let i=0;i<=GRID;i++){
    const p = i*S - HALF;
    mctx.moveTo(p, -HALF-10); mctx.lineTo(p, HALF+10);
    mctx.moveTo(-HALF-10, p); mctx.lineTo(HALF+10, p);
  }
  mctx.stroke();
  mctx.restore();
  ...
}
```

Hmm, the lineWidth in the scaled space: lineWidth = ROAD = 14 world units → 14*s px = 14*0.77 = 10.8 px. Good.

Then draw the dots in screen space after restoring:

Actually easier: keep the transform and draw dots with radius in world units. Let's restore and compute screen positions manually.

```js
  function toMap(x, z){
    return [MAP_SIZE/2 + (x - HERO.pos.x)*s, MAP_SIZE/2 + (z - HERO.pos.z)*s];
  }
```

Then draw the hero as a triangle rotated by heading, police as red dots, traffic as gray dots.

Good.

Now, the HUD elements.

```html
<div id="hud">
  <div id="speedo"><span id="spd">0</span><small>KM/H</small></div>
  <div id="wanted"></div>
</div>
<canvas id="minimap" width="170" height="170"></canvas>
```

CSS positions.

Let's write the CSS:

```css
#minimap{position:fixed;right:14px;bottom:14px;width:170px;height:170px;border-radius:10px;border:2px solid rgba(255,255,255,0.25);box-shadow:0 4px 20px rgba(0,0,0,0.5);background:#0e1218;}
#hud{position:fixed;inset:0;pointer-events:none;font-family:ui-monospace,monospace;color:#eef;}
#speedo{position:absolute;left:22px;bottom:20px;font-size:52px;font-weight:700;color:#fff;text-shadow:0 2px 12px rgba(0,0,0,0.8);letter-spacing:-2px;}
#speedo small{font-size:14px;letter-spacing:2px;opacity:0.7;margin-left:8px;}
#wanted{position:absolute;right:22px;top:20px;font-size:26px;letter-spacing:2px;color:#ffcc33;text-shadow:0 2px 10px rgba(0,0,0,0.9);}
```

The minimap is at bottom-right, so the wanted level at top-right. Speed at bottom-left.

OK.

Now writing everything. Let me be careful with the sky shader and the directional light.

Let me write updateEnvironment:

```js
const _sunDir = new THREE.Vector3();
function updateEnvironment(dt, t){
  const dayPhase = (0.17 + t/72) % 1;
  const a = dayPhase * Math.PI * 2;
  _sunDir.set(Math.cos(a)*0.55, Math.sin(a), Math.cos(a)*0.75).normalize();
  
  const elev = _sunDir.y;
  const dayF = clamp((elev + 0.15)/0.4, 0, 1);
  const duskF = clamp(1 - Math.abs(elev)/0.22, 0, 1);
  const night = 1 - dayF;
  
  // sky colors
  const topDay = new THREE.Color(0x2f6fd0), topNight = new THREE.Color(0x05070f);
  ...
}
```

Creating colors every frame is wasteful. Pre-create them outside.

```js
const C = {
  topDay: new THREE.Color(0x2f6fd0),
  topNight: new THREE.Color(0x04060e),
  botDay: new THREE.Color(0xa9c9e8),
  botNight: new THREE.Color(0x0b1220),
  dusk: new THREE.Color(0xe0763a),
  sunDay: new THREE.Color(0xfff3e0),
  sunDusk: new THREE.Color(0xff8a3c),
  moon: new THREE.Color(0x9fb4ff),
};
const tmpColor = new THREE.Color();
```

```js
  tmpColor.copy(C.topNight).lerp(C.topDay, dayF);
  tmpColor.lerp(C.dusk, duskF*0.75);
  skyUniforms.top.value.copy(tmpColor);
  
  tmpColor.copy(C.botNight).lerp(C.botDay, dayF);
  tmpColor.lerp(C.dusk, duskF*0.85);
  skyUniforms.bottom.value.copy(tmpColor);
  
  skyUniforms.sunDir.value.copy(_sunDir);
  
  tmpColor.copy(C.sunDusk).lerp(C.sunDay, clamp(elev/0.35, 0, 1));
  skyUniforms.sunColor.value.copy(tmpColor);
  
  // lights
  sunLight.position.copy(_sunDir).multiplyScalar(300);
  sunLight.color.copy(tmpColor);
  sunLight.intensity = clamp(elev*1.6, 0, 1.7);
  
  moonLight.position.copy(_sunDir).multiplyScalar(-300);
  moonLight.intensity = clamp(-elev*0.9, 0, 0.35);
  
  hemi.intensity = 0.18 + dayF*0.72;
  hemi.color.setHex(0xbfd4ff).lerp(...) // skip
  
  // fog color
  scene.fog.color.copy(skyUniforms.bottom.value);
  
  // stars
  starMat.opacity = clamp(night*1.4 - 0.35, 0, 0.9);
  
  // street lights
  const lightsOn = clamp((0.35 - dayF)/0.35, 0, 1);
  lampGlowMat.opacity = lightsOn*0.55;
  lampHeadMat.color.setRGB(lightsOn, lightsOn*0.92, lightsOn*0.7);
  buildingEmissive... 
```

For the building emissive: `buildingMats.forEach(m => m.emissive.setRGB(0.9*lightsOn, 0.75*lightsOn, 0.5*lightsOn))`. That's a bit expensive per frame for 6 materials — fine.

Hmm, but emissiveMap makes windows glow. Yes.

Headlights: headMat.color.setRGB(...) — make it bright white when lightsOn > 0.
Taillights: red.

OK.

Now let's write it. Also `renderer.setClearColor` isn't needed since we have the sky sphere. But the fog color should match the horizon.

Alright, writing the final code now.

For the sun disc, the shader adds a glow. Good.

One issue: the sky sphere radius 900 and the camera far plane 2200. Fine.

The sky sphere follows the camera? If the camera moves far, the sky sphere is centered at the origin and the camera might get close to its edge. The city is only ±240, so it's fine.

Let's write.

Also I need `sunLight` and `moonLight` as directional lights with no shadows.

Let me now write out everything.

Final code:

Also note: `THREE.CapsuleGeometry` — check it exists. Yes since r140.

Let me write the complete file.

One more: `angleLerp` with `Math.min(1, dt*12)` as t.

Let me write the code.

Also, pedestrians should be on sidewalks. The block slab is BLOCK wide, and the path half-extent h = BLOCK/2 - 2 = 20. So the path is 40x40, within the 44x44 slab ✓, and the buildings are inset by ~3-5 units from the slab edge... Hmm, buildings could be at the slab edge. Let's inset the buildings more: lot sizes are BLOCK/nx and buildings are lot - rand(3,7) wide. With nx=1, the lot is 44 and the building is 44-5=39 wide, centered → spanning from cx-19.5 to cx+19.5. The path is at ±20. So the pedestrian path would clip into the building edge. Let's set h = BLOCK/2 - 3.5 = 18.5. And ensure buildings are at most 36 wide when nx=1. Let's make the building width = lot - rand(5,9) → max 39. Hmm.

Better: limit the building extent to 2*(h-1) = 35 when nx=1. Let's just subtract more: `const w = Math.min(lotW - rand(4,8), 34)`. And for nx=2, lot=22, w = 22-5 = 17. Fine.

Actually with a max of 34 and h=18.5 (path at ±18.5), the building edge is at 17. Person at 18.5 + radius 0.25 = 18.75. Gap of 1.75. Fine.

OK.

Let's finalize.

Actually, for the ped path, I want them to also walk around and not collide with trees. Whatever.

Let's write the code!

One more: the hero should be visible from the start. Start the hero at a node near the center.

Let's write.

Also, I should make sure `VEHICLES` gap check for the hero: the hero is index 0.

Let me write the update loop:

```js
for(const v of VEHICLES) updateVehicle(v, dt);
```

And within updateVehicle, the gap scan loops over VEHICLES. O(n²) with n=42 → 1764 iterations. Fine.

Also the pedestrians update: O(n).

OK writing now.

Regarding `getLightState` being called for each car each frame: fine.

Let me write the final code.

Also for traffic lights visuals update:

```js
function updateTrafficLightVisuals(t){
  for(let k=0;k<tlData.length;k++){
    const d = tlData[k];
    const st = getLightState(d.ni, d.nj, d.dir, t);
    let col;
    if(st==='g') col = tmpColor.setHex(0x22ff66);
    else if(st==='y') col = tmpColor.setHex(0xffcc22);
    else col = tmpColor.setHex(0xff3322);
    tlHeadMesh.setColorAt(k, col);
  }
  tlHeadMesh.instanceColor.needsUpdate = true;
}
```

324 setColorAt calls per frame — fine.

Hmm, `setColorAt` requires the instanceColor attribute to exist. It creates it on first call. OK.

Let's do it.

Now writing the whole file for real.

I'll be careful about the order of declarations: functions used before definition are fine if they're function declarations (hoisted).

But `const` variables must be declared before use at runtime. So I'll structure: constants, setup, then build the city, then vehicles, then the loop.

Let me write.

Final concern: performance of `new THREE.Color()` in loops — avoid.

Writing now.

For the lamp glow, I'll use an InstancedMesh of a plane rotated flat with an additive radial texture.

```js
const glowTex = (()=>{
  const c = document.createElement('canvas'); c.width=c.height=64;
  const g = c.getContext('2d');
  const grd = g.createRadialGradient(32,32,0,32,32,32);
  grd.addColorStop(0,'rgba(255,225,160,0.9)');
  grd.addColorStop(0.5,'rgba(255,210,130,0.25)');
  grd.addColorStop(1,'rgba(255,200,120,0)');
  g.fillStyle = grd; g.fillRect(0,0,64,64);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
})();
const lampGlowMat = new THREE.MeshBasicMaterial({ map: glowTex, transparent:true, blending: THREE.AdditiveBlending, depthWrite:false, opacity:0 });
```

And a plane geometry 10x10 rotated flat.

Instanced with the lamp positions.

OK.

Now writing.

Let me carefully write the whole thing out.

Also, I want the hero car to be identifiable: make it bright red with a spoiler maybe. Just color.

Alright.

Let me also add: the hero's speed varies — occasionally it slows down. And it stops at red lights. Fine.

Now the code:

```js
// ---------- sky ----------
```

Let me write the final answer.

Regarding `scene.fog` color — update from the sky bottom color.

Also the fog density: 0.0022 means at 300 units, exp(-(0.0022*300)^2) = exp(-0.435) = 0.65. Hmm, FogExp2 factor = 1 - exp(-(d*density)^2). At d=300: (0.66)^2 = 0.435 → fog = 0.35. OK, moderate.

Let's use 0.0025.

Alright, writing.

Actually one more important thing: when the hero is moving, the buildings around should be visible. With the camera at ~7 units behind and 3 up, FOV 62, we see a good amount.

Let's write.

I also want the camera to have a slight FOV increase with speed for a sense of speed. Optional, skip.

Writing the final code now.

def makeCarMesh with police lights:

```js
if(isPolice){
  const red = new THREE.MeshBasicMaterial({color:0xff2020});
  const blue = new THREE.MeshBasicMaterial({color:0x2060ff});
  ...
}
```
Store references for flashing. Let's store `v.policeLights = [redMat, blueMat]` and flash them.

For simplicity: create two small boxes on the roof, and each police car has its own materials (8 police × 2 = 16 materials, fine).

Flash: `redMat.color.setRGB(flash?1:0.05, 0, 0)`.

OK.

Writing now for real.

Let me write out the code in one go.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Neon District — Autonomous City</title>
<style>...</style>
</head>
<body>
<div id="hud">
  <div id="speedo">0<small>KM/H</small></div>
  <div id="wanted"></div>
</div>
<canvas id="minimap" width="170" height="170"></canvas>
<script type="module">
...
</script>
</body>
</html>
```

Now the JS.

I'll write it carefully.

```js
import * as THREE from 'three';
```

Let me start.

```js
/* ---------------- utils ---------------- */
const rand = (a,b)=>a+Math.random()*(b-a);
const randInt = (a,b)=>Math.floor(rand(a,b+1));
const clamp = (v,a,b)=>v<a?a:(v>b?b:v);
const lerp = (a,b,t)=>a+(b-a)*t;
function angleLerp(a,b,t){
  let d=(b-a)%(Math.PI*2);
  if(d>Math.PI)d-=Math.PI*2; if(d<-Math.PI)d+=Math.PI*2;
  return a+d*t;
}
```

Note `%` with negative in JS gives negative results, so handle with while loops. Let me use the while version to be safe.

OK. Writing.

Let me write the full script now, mentally checking each part.

I think I'm ready. Let me produce the file.

Regarding the `HERO` variable being referenced in functions defined earlier — I'll declare `let HERO = null;` early.

Let's go.

For `updateWanted`, increase the wanted level over time:

```js
function updateWanted(dt, t){
  const target = clamp(Math.floor((t - 5)/13) + 1, 0, 5);
  if(t < 5) return; // no wanted yet
  while(WANTED < target && POLICE.length < 12){
    WANTED++;
    spawnPolice();
    spawnPolice();
  }
}
```

Hmm, at t=5 → target = 1 → spawn 2 police. At t=18 → target=2 → spawn 2 more. Etc.

Let's cap the police at 12.

Actually `Math.floor((t-5)/13)+1`: at t=5 → 1, t=18 → 2, t=31 → 3, t=44 → 4, t=57 → 5. Good — the police appear progressively. But within the first 30s we only get to wanted 2. That's fine — the first 30s shows the chase starting.

Hmm, "show everything important within the first 30 seconds". Police appear at t=5s. Good. Wanted level 2 at 18s, level 3 at 31s. Fine.

Let's make it faster: (t-4)/8 → level 1 at 4s, 2 at 12s, 3 at 20s, 4 at 28s, 5 at 36s. Better.

OK.

Now writing the final code.

Let me write it.

Regarding the initial hero position: place it at node (4,4) which is near the center: (4*58-232, 4*58-232) = (0, 0). 

Let's go.

One more detail on `lanePos`: uses `i*S - HALF`. For i=4: 4*58-232 = 0. ✓

OK.

Writing.

I also need to make sure the hero doesn't drive out of the city. `chooseDir` ensures the next node is in bounds. ✓

Alright, final code.

Also: after the hero passes t >= S and wraps, we handle the while loop. But if speed*dt > S, we'd loop multiple times. Fine.

Let me write.

For pedestrians, the block data: I need a list of block centers that are not parks. Let me collect them during generation.

```js
const pedBlocks = [];
```
In the block loop: `if(!isPark) pedBlocks.push({x:cx, z:cz, h: BLOCK/2 - 3.5});`

Then create pedestrians.

OK, writing now.

Final: let me make sure the code doesn't have syntax errors. I'll write it carefully.

Note on `THREE.PlaneGeometry(...).rotateX(-Math.PI/2)` — rotateX returns `this`, so it works.

Let me write the code.

Also, for the instanced traffic light poles, I need a matrix per instance. I'll use a dummy Object3D.

OK writing.

Let me write out the entire script now.

I'll write it in the answer.

Regarding `setColorAt` — it requires `mesh.instanceColor` to be set. `InstancedMesh.setColorAt(index, color)` creates it if null. Yes, in the three.js source:

```js
setColorAt( index, color ) {
    if ( this.instanceColor === null ) {
        this.instanceColor = new InstancedBufferAttribute( new Float32Array( this.instanceMatrix.count * 3 ).fill( 1 ), 3 );
    }
    color.toArray( this.instanceColor.array, index * 3 );
}
```
Note `.fill(1)` — so the default is white. Good.

OK.

Writing the final code now.

Let me think about the number of traffic lights: (GRID+1)^2 = 81 intersections × 4 = 324 poles. Poles are cylinders with 6 segments. Instanced, so it's 1 draw call. But 324 shadow... no shadows. Fine.

Hmm, 324 poles might visually clutter. Let's keep it.

Actually, let me reduce to 2 poles per intersection: one for the X axis and one for the Z axis, placed at opposite corners. That's 162. Cleaner. Hmm, but then some approaches have no visible light. Doesn't matter visually much.

Let's do 4 per intersection but only at intersections where (i+j) % 1 === 0 — all of them. Fine, keep 4.

Hmm, 324 instances of a 6-sided cylinder = fine.

OK, writing.

Let me now produce the final answer.

For the pole geometry: CylinderGeometry(0.1, 0.12, 5.2, 5) with the origin at the center, so position y = 2.6.

Head: BoxGeometry(0.5, 1.1, 0.5) — I'd rather have a horizontal arm. Let's just do a box on top of the pole at y=5.4, offset slightly toward the road.

Fine.

Writing.

Also, the traffic light head material: MeshBasicMaterial with instanceColor. But we also want it to look dark when off — the color we set IS the color, so at night it glows. During the day it's still colored. Fine — traffic lights are colored during the day too.

OK.

Final write.

Let me carefully produce it.

Actually, one thought on `instanceColor` + `MeshBasicMaterial`: in three r150+, InstancedMesh instanceColor is applied via `USE_INSTANCING_COLOR` when `instanceColor` is set. It works with basic material. ✓

Writing.

I'll now write the complete HTML.

Note: I should also handle the case where `document.getElementById('minimap')` exists — yes.

Alright.

Let me write out the pedestrian creation:

```js
const pedBodyMat = [];
for(let i=0;i<6;i++) pedBodyMat.push(new THREE.MeshLambertMaterial({color: new THREE.Color().setHSL(Math.random(), 0.5, 0.5)}));
```

Body geometry: capsule. Head: sphere with skin color.

Shared head material: 0xd9a882.

Let's write.

OK, final answer time. I'll write it all out.

Double-check the sky shader: `varying vec3 vPos;` and `position` attribute in the vertex shader — for a sphere, position is the local position. Since the sphere is at the origin with no rotation, that's the direction. ✓

Writing now.

Let me be careful with the `#speedo` innerHTML update: `spd.textContent = Math.round(speed*3.6)`.

Hero speed max ~30 m/s → 108 km/h. Fine.

Let's write.

Also, I should make sure the game doesn't crash if `instanceColor` is null in the first frame — we call setColorAt in the first update, which creates it. Then `tlHeadMesh.instanceColor.needsUpdate = true`. ✓ But if tlData is empty... it isn't.

OK writing.

One last thing: the `chooseDir` for police.

```js
function chooseDirFor(v, i, j, curDir){
  const opts = [];
  for(let d=0;d<4;d++){
    if(d === (curDir^1)) continue;
    const ni=i+DIRV[d].x, nj=j+DIRV[d].y;
    if(ni<0||ni>GRID||nj<0||nj>GRID) continue;
    opts.push(d);
  }
  if(opts.length===0) return curDir^1;
  if(v.isPolice && HERO){
    let best = opts[0], bd = Infinity;
    for(const d of opts){
      const nx = (i+DIRV[d].x)*S - HALF;
      const nz = (j+DIRV[d].y)*S - HALF;
      const dist = (nx-HERO.pos.x)**2 + (nz-HERO.pos.z)**2;
      if(dist < bd){ bd = dist; best = d; }
    }
    return best;
  }
  if(opts.includes(curDir) && Math.random()<0.62) return curDir;
  return opts[randInt(0,opts.length-1)];
}
```

Good.

Now writing the answer.

Hmm, `randInt(0, opts.length-1)` — my randInt(a,b) returns floor(rand(a, b+1)). So randInt(0, len-1) → floor(rand(0, len)) → 0..len-1 ✓.

OK. Writing!

Let me estimate the total code lines ~800. That's fine.

Writing now.