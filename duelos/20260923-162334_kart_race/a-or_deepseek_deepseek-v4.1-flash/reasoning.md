Let me build a self-contained HTML file with three.js from the import map (assumed provided). I need to create a closed circuit, karts with AI, particles, HUD, cameras, countdown.

Let me design carefully.

Track: closed loop defined by a Catmull-Rom curve (closed) with elevation. I'll generate a set of control points forming a circuit. Then build road mesh by sampling the curve, computing tangent and normal (up = Y), creating a ribbon with width. Add kerbs (red/white stripes) at edges, and maybe a center line. Hills: vary y of control points.

Karts: 6 karts, each with position along a spline parameter, lateral offset, speed. AI: follow racing line with lateral offset for overtaking, slow down in corners, drift when turning hard (visual yaw offset), particle dust when drifting.

Simplify: rather than full physics, karts move along the track curve with parametric s (distance along track) and lateral offset. Their speed depends on curvature ahead. Overtaking: steering lateral offset toward a target that avoids karts ahead. Visual: yaw from tangent plus drift angle proportional to lateral velocity/curvature.

This is a good approach — robust and gives a nice race.

Track curve: build points in XZ with y for hills, closed CatmullRomCurve3. Compute curvature by sampling.

Let me define control points for a circuit roughly in a 400-unit space.

Points (x, y, z):
Let me make an interesting shape:
(0,0,-160), (90,4,-150), (150,8,-90), (140,10,-20), (170,6,40), (140,2,100), (70,0,140), (0,3,120), (-70,8,150), (-150,10,110), (-170,4,40), (-140,0,-20), (-160,6,-80), (-100,10,-150), (-40,5,-170)

That's 15 points, closed. Good.

Racing line: offset slightly inward. Karts use the centerline with lateral offsets.

Road mesh: sample N=600 points along the curve. For each, compute position and tangent, compute right vector = tangent × up normalized (up = (0,1,0)), then left/right edges at ±halfWidth. Build BufferGeometry with vertex positions, normals (approx up), uvs. Use a canvas texture for road? No external images but we can generate canvas textures procedurally — that's allowed (no external resources). Let's create a procedural asphalt texture with a canvas: noise + center dashed line? Actually easier: build the road mesh with vertex colors or just dark material, then add white edge lines as separate thin ribbons slightly above.

Kerbs: strips at edges, alternating red/white — do it with vertex colors based on segment index (alternate every few samples).

Grass: a big plane? The track has hills so a flat plane would intersect. Instead, build a wider ribbon "grass" under the road extending outward, plus a large ground plane below at y=-? Hmm. Simpler: terrain as a large plane at y = -2 with green color, and hills are mild (max 10 units). Road at y up to 10, so the plane at y=-2 might poke through where road y is low... road at y=0 min. Grass ribbon of width 60 on each side following the track at slightly lower y than the road handles the surroundings; outer plane at y=-3 for distant ground. That works reasonably.

Actually make the road ribbon: road width 14, then shoulder/grass ribbon from 7 to 40 each side following the road with a slight drop. Then a huge circle plane far below. Let's just do the ribbon approach with a big ground disc at y=-2 for fill. Given camera angles mostly chase-view near road, it'll be fine.

Scenery: trees (cone + cylinder), rocks, grandstands (boxes), tyre stacks, billboards. Place them by sampling the curve at random t, offsetting laterally by road half width + margin, on the ground height at that point. Use InstancedMesh or just Meshes — 6 karts, ~150 scenery objects is fine.

Also: start/finish line gantry with checkered pattern (use canvas texture or alternating boxes).

Karts:
- chassis: box, slightly rounded; nose cone; driver: sphere head + body; helmet color per kart; wheels: 4 cylinders that rotate based on speed and steer front wheels.
- Group per kart; wheels as separate meshes for rotation.

Dust/skid particles: use THREE.Points with a pool of particles per kart or a global pool. Simpler: a global particle system with a pool of e.g. 400 particles, each with position, velocity, life. Use Points with a canvas-generated circular sprite texture. Update each frame: spawn from drifting karts' rear wheels.

HUD: DOM overlay with lap counter, position list with kart colors + names, countdown big text, speed maybe.

Cameras: chase camera on leader (or on a specific kart), cuts to trackside camera occasionally. Trackside cameras: pick random points on curve, camera looks at nearest kart... Let's implement: camera modes: 'chase' (follow leader with smooth lag) and 'trackside' (static position at a track point, look at leader or a random kart passing). Cut every ~6-8 seconds.

Actually "chase camera on the leading kart that cuts occasionally to a trackside camera" — so main is chase on leader, occasionally cut to trackside. Do that.

Race logic:
- Countdown 3-2-1-GO (maybe 4 seconds total including lights). During countdown karts are at grid positions, engines idle. Then race.
- Laps: 2 laps minimum. Track length: let's compute. The circuit roughly 1000+ units in circumference. Kart speed ~ 40-60 units/s. So lap ~ 20 s. 2 laps = 40s. Recording window 30s — they want everything important within first 30 seconds, "it may continue after that". Hmm, they say the animation should show everything important within first 30s. Two laps might take ~40-50s. Maybe make 3 laps but shorten the track? Or make karts faster so 2 laps completes within ~30s? Let's aim lap time ~13s: track length ~1100, speed ~85 u/s. That's fast but with 6 karts, looks fine. Actually drifting/curve handling looks better if not too fast. Let's compromise: lap ~15s, race = 3 laps = 45s+. Hmm.

Requirement: "lasts at least two laps". So make it 3 laps and each lap ~12-14s. Total ~40s. Fine — we show the important stuff in the first 30s: countdown, racing, overtakes, camera cuts, positions changing. The race ending isn't crucial in the first 30s but it's fine.

Alternatively make it loop: after the race finishes, restart. Good idea — endless loop so recording gets everything. Let's do: after finish, show results for a few seconds, then reset and countdown again. That satisfies both.

Let me compute the track length in code and set kart speeds accordingly: base speed = trackLength / 14 (roughly 14s per lap, though corners slow them).

Sizing: let's scale the circuit to about 1100 units circumference.

AI speed control: for each kart, look ahead at curvature; target speed = maxSpeed * clamp(1 - curvature*k). Compute curvature per sample along the curve (array over N samples). Precompute sample data: positions, tangents, rights, curvature, cumulative distance.

Kart update:
- s += speed * dt (s in distance units; index = s / totalLength * N, wrap)
- lateral offset x (relative, in [-maxOff, maxOff])
- overtaking: each kart looks at karts within ±15 units of s ahead and slightly overlapping laterally: steer target lateral to avoid. Simple approach: compute desired lateral offset from a "racing line" curve (a sinusoidal-ish offset toward inside of corners) plus avoidance.

Let's define racing line offset per sample: offsetRacing[i] = -curvature-based inward offset. Actually inside of corner: the curvature sign determines left/right. Define signed curvature computed via cross product of tangent changes. offsetRacing = clamp(-k * C, -4, 4)... Let me just compute: for each sample, the "lateral" signed curvature kappa. Racing line = apex: offset toward inside = -sign(kappa)*something limited. Let's do offsetRacing = clamp(-kappa * 60, -5, 5) where kappa in 1/units.

Hmm, careful with sign convention. Let me define at sample i: tangent T, right R = normalize(cross(T, up))? Let's define right = normalize(cross(up, T))? Depends. Let's just compute: given position p_i and p_{i+1}, T = normalize(p_{i+1}-p_i). right = normalize(cross(T, (0,1,0))) — this gives a vector. For a curve turning left, the center of curvature is to the left; the vector cross(T, up) — let's check with T=(0,0,-1) (moving -z), up=(0,1,0). cross(T,up) = T×up = (0*0 - (-1)*1, (-1)*0 - 0*0, 0*1 - 0*0) = (1, 0, 0). So right = +x when moving -z. Yes, in three.js, moving -z, +x is to the right. Good, right = cross(T, up).

Curvature: kappa = (T_{i+1} - T_i) dot right / ds, positive if turning right (center to the right). Then apex is at inner side: offset = sign of kappa... if turning right (kappa>0), the inside is to the right, so offset should be positive (toward right). So offsetRacing = clamp(kappa * C, -max, max). Wait inner side = right when turning right, so offset positive → toward right. Yes offsetRacing = clamp(kappa*C, -5, 5). Hmm but that gives sharp correction. Let's smooth it.

Actually a real racing line: enters wide, apexes inside, exits wide. Simple approximation: offset = clamp(kappa * C, -maxOff, maxOff) smoothed. That's fine.

Kart lateral: x_target = racingOffset[i] + avoidance + driftOut. Move x toward x_target with rate limit.

Speed: targetSpeed = baseSpeed * clamp(1 - |kappa_lookahead| * K, 0.45, 1.0). Use max |kappa| over next ~30 units.

Overtaking: For each kart, find karts ahead within gap < 12 units and lateral difference < 4. Then set avoidance offset to move to the side with more space. Also, if a kart is much faster and next to another, they just pass.

Also add slight rubber-banding to keep the pack together: karts behind get small speed boost based on distance to leader. And random variation per kart (skill).

Collision: if two karts overlap in s and lateral, push them apart laterally softly.

Positions: rank by (lap * totalLength + s) descending. Compute each frame.

Lap counting: when s wraps from >totalLength to <totalLength, lap++.

Grid start: karts start at s = totalLength - offsets (behind the start line), staggered lateral. Actually simpler: start positions ahead of the finish line? Let's define s0 = -i*8 (behind start line at s=0) but negative → wrap. Let's just set kart.s = totalLength - (i+1)*9 for grid and lap = -1? Hmm, then laps should count from crossing s=0. Alternative: give each kart startS and count laps when passing startS + lap*length. Let's simplify: start karts at s near 0 but counting laps only after they first cross the line: use a flag.

Simplest: karts start at s = -(i+1)*9 + totalLength (mod), i.e., slightly before the line. Set lap = 0, and lastS = s. When s wraps (s < lastS), lap++. Since they start before the line, they cross it immediately at the start... that'd give lap 1 at t=0 which is fine if we display lap = lap+1 (starting lap 1). So: display lap = min(lap+1, totalLaps). They cross the line at start → lap becomes 1 → still lap 1. Then after a full lap, lap 2. Finish when lap > totalLaps. Hmm, they'd finish after crossing the line 3 times for a 2-lap race.

Let's define: lapsDone starts 0 at t=0 (they're on their first lap). Crossing line increments lapsDone. Race is done when lapsDone == totalLaps (for each kart, finish order recorded). Display: "LAP " + min(lapsDone+1, totalLaps) + "/" + totalLaps.

Grid: place karts before the line, s_k = totalLength - (gridRow)*... With lateral alternating offsets ±3.5.

Camera: chase camera on leader: position = leaderPos - forward*12 + up*5, lookAt leaderPos + forward*8 + up*1.5. Smooth with lerp. Add slight speed shake.

Trackside cuts: pick a point along the track ahead of the leader, place camera at lateral offset ~18, height 6, look at leader. Cut for ~3s, then back to chase for ~7s. Use a random track sample index ahead of leader by 60-140 units.

Let's implement camera as: mode, timer, on switch compute trackside position/lookAt.

Particles: global Points with BufferGeometry, positions array, size attenuation, vertex colors? Use a smoke texture (canvas radial gradient) and PointsMaterial with map, transparent, depthWrite false, size 3, vertexColors true for dust color. Pool of 500. Each particle: pos, vel, life, maxLife. Dead particles moved to y=-1000. Actually with Points, we can set alpha via color? PointsMaterial doesn't support per-particle alpha. Use vertexColors and fade the color toward... it's additive? Use normal blending with a soft texture; fading color to transparent-ish works if we use additive blending then fading to black = invisible. Dust is light brown; additive on dark background... Let's use AdditiveBlending and fade color from warm gray to black. On grass, additive dust looks like light puffs — acceptable.

Or use custom ShaderMaterial for particles with alpha. That's cleaner. Let's do a simple ShaderMaterial:

vertex: attribute float size; attribute float alpha; varying float vAlpha; ... gl_PointSize = size * (300.0 / -mvPosition.z);
fragment: gl_FragColor = vec4(color, alpha * texture). Use a circular falloff computed procedurally: float d = length(gl_PointCoord - 0.5); alpha *= smoothstep(0.5, 0.1, d).

Simple and no texture needed. Color uniform per material — but different kart dust colors? Just use one dust color (tan/white). Skid marks: dark particles; but the same shader can't do two colors unless we use vertex colors. Let's add per-particle color attribute. Fine.

Let's implement particle system with attributes: position (vec3), size (float), alpha (float), color (vec3). Update alpha each frame in the buffer and set needsUpdate.

Number: 800 particles. Each frame update CPU: fine.

Spawn: for each kart, if drifting intensity > threshold and on ground, spawn 1-3 particles at rear wheel positions with velocity backward+random up. Also spawn dust when on grass? Karts stay on road mostly.

Also skid marks on the ground: could add dark quads. Optional; particles are enough. Maybe add skid marks as simple dark planes? Skip for simplicity, but "dust or skid particles" is required — dust particles satisfy.

Now scenery. Let's create:
- Trees: InstancedMesh? Simpler: create tree group geometry merged? Let's use InstancedMesh with cone (foliage) and cylinder (trunk) — two InstancedMeshes. ~120 trees.
- Kerbs: alternating red/white. Use vertex colors on a kerb ribbon geometry.
- Grandstands: a few boxes with striped color near start line.
- Billboards/banners over track? Maybe an arch at start/finish.
- Rocks: instanced icosahedrons.
- Start/finish gantry: two posts + top bar + checkered banner (procedural canvas texture).

Also the road markings: white edge lines on both sides of the road (thin ribbons), and a dashed center line? Kart tracks don't have center lines usually. Skip; maybe add kerbs only.

Let's write the code.

```js
import * as THREE from 'three';
```
No addons needed (no OrbitControls since camera is auto).

Track building:

```js
const ctrl = [ ... ].map(p => new THREE.Vector3(...));
const curve = new THREE.CatmullRomCurve3(ctrl, true, 'catmullrom', 0.5);
const N = 800;
const samples = [];
const totalLen = curve.getLength();
for i in 0..N: t = i/N; p = curve.getPointAt(t) — getPointAt requires arc-length param, curve.getSpacedPoints? Use curve.getPointAt(t) which uses arc length lookup. Good for uniform spacing.
```
Use curve.getPointAt(u) for uniform spacing, and getTangentAt(u).

Then compute right vectors and curvature.

```js
for (let i=0;i<N;i++){
  const u = i/N;
  const p = curve.getPointAt(u);
  const t = curve.getTangentAt(u).normalize();
  const right = new THREE.Vector3().crossVectors(t, up).normalize();
  ...
}
```
Then curvature: use difference of tangents between i and i+1, dot with right, divided by ds.

ds = totalLen/N.

kappa[i] = (T[i+1] - T[i])·right[i] / ds. Positive if turning right.

Smooth kappa with a small blur.

Road geometry: for each i (and wrap), vertices at p ± right*halfWidth, with y slightly raised? The curve y gives elevation. Road surface: build quads between consecutive samples. Add UVs: u across width, v = i/N * (totalLen/8) for texture repeat.

Create a canvas asphalt texture: 128x128 with noise, repeat wrapping. Fine.

Also grass ribbon: from halfWidth to halfWidth+40 both sides plus the outer. And shoulders. Let's do:
- road: width 2*7 = 14
- kerb: from 7 to 8.2 on each side (when in corners, always is fine)
- grass: from 8.2 to 45 on each side, dropping y by a bit (e.g., -0.5 at the outer edge).

For terrain beyond, a big ground plane at y = min terrain? Since hills up to 10, a flat plane at y=-1 will show gaps under the grass ribbon edges... Actually the grass ribbon extends 45 units from the track centerline in both directions; the track's loop spans roughly 340x340 with the interior maybe covered. Distant terrain hidden by fog. Let's set fog and a large ground disc at y = -1 colored dark green. Where the road is elevated at y=10, the grass drops from y=10 to y=3 at 45 units out, still above the plane... gaps visible from camera? The chase camera is near the ground so it mostly looks along the track; fine. Let's add fog to hide.

Actually, an easy fix: make the ground plane at y = -2 and set the grass ribbon to slope down to y=-2 at its outer edge (45 units out). But where the road is at y=0 (low sections), the grass would slope down to -2, leaving a visible dip but still connected. OK — slope from road edge y-0.2 down to -2 at 45 out. Hmm, for elevated road at y=10, slope down to -2 over 45 units is a 0.27 gradient — fine, looks like an embankment.

Let's do that: grass i, side ±: inner at hw+0.9 (after kerb) at y_road - 0.1, outer at 45 at y = -2. Actually to keep it simple: grass ribbon vertices at offsets 7.0 (kerb outer) and 45, with y offset -0.05 and -2 respectively relative to road y. Wait if the road y is 10, the outer is 8. Should the outer y be relative or absolute? Absolute -2 creates a slope down. Let's use absolute y = -2 for the outer edge, but if the road y < 0... not the case (min 0). Fine. But near the low sections the outer edge equals road level -2, a gentle slope. OK.

Ground plane: a big disc/plane at y=-2.1, color matching grass. Fine.

Trees placement: sample u random, side random, offset from 20 to 60. Ground y there: estimate as lerp between road y and -2 based on offset: since grass slopes from road edge (7) to 45, at offset d: y = roadY + (-2 - roadY) * (d-7)/(45-7)... clamp. Just place trees at the computed y.

Also place trees inside the loop — the interior of the track curve; the grass ribbon on the inner side covers 45 units. The track's inner region might be larger, showing the ground plane. Add extra trees scattered in a big area with y=-2 and skip if too close to the track. That requires distance-to-track computation. Simpler: keep the ribbon and place trees only along it (both sides), scattered 25-55 out. Also add some in the far distance with the ground plane.

Hmm, actually for the inner region: our circuit is a rough oval ~340x300. The inner side grass ribbon extends 45 units inward, leaving a large interior hole showing the flat plane at -2. Trees placed along the inner edge up to 55 units help. And the fog. And the camera is low. It's fine.

Actually, let's make the grass ribbon wider, 80 units out, so it covers most of the interior. Outer edge at 80 with y = -2. Then the remaining hole is small. Let's do inner 80 and outer 80.

Hmm but with a slope down to -2 in 80 units, if the road is at y=0 the grass is basically flat at -2 — fine.

Scenery objects:
- Trees: 140. Each: trunk cylinder (0.6 radius, 3 h), foliage cone (3 radius, 7 h) dark green, maybe 2 cones.
- Rocks: 60 small gray icosahedrons near the track edges.
- Grandstand: near the start line, a long box with stripes.
- Tyre stacks: cylinders at the corners.

Use InstancedMesh for trees (trunk + foliage) and rocks for performance.

Let me now write the kart class.

Kart:
```js
class Kart {
  constructor(index, color) {
    this.group = new THREE.Group();
    // body
    ...
  }
}
```
Body: use a box (2.2 wide, 0.7 tall, 3.6 long) color-coded, with a nose cone (cone rotated), a spoiler, driver: capsule body + sphere head with helmet color, wheels: 4 cylinders radius 0.5, width 0.4, rotated so the axis is along X.

Wheels: create as a group per wheel so the front wheels can steer (rotate around Y) and the wheel mesh rotates around X for rolling.

Positioning: chassis group's +Z forward? Let's set forward = +Z... Hmm, in the track, tangent direction. Let's orient the kart with lookAt: place group at position, then set rotation via quaternion from a matrix looking along tangent. Use a dummy Object3D: obj.position.copy(p); obj.lookAt(p + tangent). Then the object's -Z faces the tangent... Actually lookAt makes -Z point toward the target? Object3D.lookAt rotates so that the object's +Z axis... For a camera, lookAt points -Z at the target. For a regular Object3D, lookAt makes +Z point toward the target? Let me recall: Object3D.lookAt uses Matrix4.lookAt(eye, target, up) which builds a rotation where the object's -Z... Hmm. In three.js, `Object3D.lookAt` — for non-camera objects, the +Z axis points toward the target. Actually the code: 

```js
lookAt(x,y,z) {
  ...
  if (this.isCamera || this.isLight) {
    _m1.lookAt(_position, _target, this.up);
  } else {
    _m1.lookAt(_target, _position, this.up);
  }
```
Matrix4.lookAt(eye, target, up) produces a rotation where the z-axis = normalize(eye - target). For non-camera, eye=_target, target=_position → z = normalize(target - position) = direction toward the target. So +Z points toward the target. Good: build the kart model with +Z forward.

So the kart model: nose at +Z. Wheels at z = ±1.2, x = ±1.05.

Now the kart's world transform: position = track point + right * lateral + up * rideHeight. Quaternion: yaw from tangent, plus drift/slip angle, plus banking roll from curvature.

Build the orientation: yaw = atan2(T.x, T.z) (since forward is +Z, yaw around Y such that forward = (sin(yaw), 0, cos(yaw))). Then add slip angle: extra yaw proportional to drift. Then pitch from tangent's y (hill). Then roll from curvature/banking.

Simplest: construct a quaternion from a rotation matrix using the basis vectors: forward (local +Z), up (local +Y), right (local +X = ... careful: local X = up × forward? For a right-handed system with forward = +Z, up = +Y, then X = Y × Z = up × forward. Let's check: Y×Z = X. Yes, so right = up × forward. Hmm, but in vehicle terms: if forward is +Z and up is +Y, then +X = up×forward... Let's verify: (0,1,0)×(0,0,1) = (1*1-0*0, 0*0-0*1, 0-0) = (1,0,0). Yes, X = (1,0,0). So local X = up × forward. And with forward = (0,0,1), local X = (1,0,0), which in world is... moving +Z, the right side is -X? Hmm. For a person facing +Z with up +Y, their right hand points to... In a right-handed coord system, facing +Z, up +Y, right = forward × up = (0,0,1)×(0,1,0) = (0*0-1*1, 1*0-0*0, 0*1-0*0) = (-1, 0, 0). So right is -X. OK, whatever, the model is symmetric so it doesn't matter, as long as wheels are mirrored correctly. Let me just use matrix basis: xAxis = up × forward, and set the matrix. Consistent.

Track right vector at sample: R = cross(T, up). For T=(0,0,1): R = (0,0,1)×(0,1,0) = (0*0-1*1, 1*0-0*0, 0-0) = (-1,0,0). Same as the model's local X. Great — so the model's local +X aligns with the track's right vector when yaw is from tangent. 

So build the matrix with makeBasis(xAxis=right(banked), yAxis=up, zAxis=forward).

For banking, tilt the up vector along the roll axis. Let's do: quaternion = yaw quaternion around Y, then apply a roll rotation around local Z (forward) axis by bank angle. Apply as: q = qYaw * qRoll. And also a pitch for hills: qPitch around local X. Combine: q = qYaw * qPitch * qRoll. That's easy.

Drift: the kart's visual yaw offset relative to the tangent, so add a yaw offset: qYaw = rotation Y by (trackYaw + slipYaw).

Slip yaw: when drifting (hard cornering at speed), slip = -sign(kappa) * driftAmount, so the kart points outward. Since drifting means the rear slides out, the kart points more toward the inside... Actually in a drift, the car's nose points toward the inside of the corner while it slides. Hmm, for a rear-drive drift, the car rotates so the nose points inward relative to the velocity direction. Velocity is along the track; the car's heading is rotated toward the inside of the corner. Inside of a right turn is +R. So heading yaw offset = +some for right turn. Let's do slipYaw = clamp(kappa*someSpeed, -0.5, 0.5) * intensity. Right turn kappa>0 → positive yaw offset. Yaw is measured... with forward=(sin y,0,cos y) I'd need to check the sign. Let's just compute directly: forward vector = trackTangent rotated by angle a around Y: f = T*cos(a) + R'*sin(a)? Where R' = ... The rotation around Y by angle a: f = (T.x*cos a + T.z*sin a, 0, -T.x*sin a + T.z*cos a). The direction of positive yaw. Hmm, easier: build forward = T.clone().applyAxisAngle(up, a), and check that positive a rotates from T toward... For T = (0,0,1), rotating around Y by a: applyAxisAngle gives (sin a, 0, cos a). Track R for T=(0,0,1) is (-1,0,0). So positive a moves the forward direction toward +X = -R = left. So positive yaw = turn left. For a right turn (kappa > 0, since kappa = turning right... wait we defined kappa = (T_next - T_i)·R / ds. If the track turns right, the tangent rotates toward R, so (T_next - T_i)·R > 0 → kappa>0. Yes.)

So turning right → we want the kart's yaw to point toward the right (inside), meaning negative yaw a. So a = -kappa * K * intensity. Good.

Where intensity = drift factor (0..1) based on speed and curvature. Also add lateral velocity slip.

OK.

Now, the actual lateral position: kart.x (lateral offset). Its rate of change dx/dt is the lateral velocity used for drift visualization.

Let's now write update logic per kart:

```js
update(dt, karts) {
  const i = Math.floor((this.s / totalLen) * N) % N  (with wrap)
  // lookahead curvature
  let maxK = 0;
  for (let j=0;j<25;j++){ const idx=(i+j*3)%N; maxK = Math.max(maxK, Math.abs(curv[idx])); }
  ...
}
```

Wait, samples are uniform in arc length, ds = totalLen/N ≈ 1.4 units for N=800 and len=1100. So looking ahead 25*3 = 75 samples ≈ 105 units. That's plenty. Maybe look ahead 60 units = 43 samples.

targetSpeed = maxSpeed * clamp(1 - maxK*steerBrake, minFactor, 1).

Curvature magnitude: for a corner of radius 40, kappa = 0.025. For straight, ~0. So scale: 1 - kappa*  ... we want at kappa=0.025 → reduce to ~0.6. So factor = 1 - kappa/kappaMax*0.5 where kappaMax ≈ 0.05. Let's do: targetSpeed = maxSpeed * clamp(1 - |k|*12, 0.5, 1). At k=0.025 → 1-0.3=0.7. Reasonable.

But we also need to look far enough ahead so they brake before the corner. Let's blend: use a weighted max over the lookahead window with a distance falloff. Simple: for each of the next 60 units, compute the needed speed there, and take the min of (neededSpeed + distanceDecay). Eh. Simpler approach: maxK over the next 70 units — pretty good, plus acceleration limits.

Speed dynamics: this.speed += clamp(targetSpeed - speed, -brake*dt, accel*dt).

Lateral: xTarget = racingOffset[i] + avoidance. x += clamp(xTarget - x, -rate*dt, rate*dt) where rate ~ 8 units/s. Actually make lateral movement proportional to speed.

Racing offset: offsetRacing[i] precomputed = clamp(kappa_smoothed[i] * 180, -maxOff, maxOff)? With kappa = 0.025, that's 4.5. Let's use 200 and clamp to ±5.5, and halfWidth 7, so the kart stays on the road. Good. Also smooth over neighbors.

Actually a racing line offset proportional to curvature means in a corner all karts go to the inside — fine.

Avoidance: for each other kart k with 0 < (k.s - this.s) mod L < 14 and |k.x - this.x| < 3.2: steer away. Choose direction with more room: if this.x > 0 → go left (negative), else go right. Add avoidance += ±4. Also brake slightly if very close (< 6).

Collision separation: if two karts have |Δs| < 4.5 and |Δx| < 3.0, push apart laterally.

To keep the pack close, add a catch-up: speedMultiplier for karts behind based on their position in the race.

Now let's write it.

Also, the s modifier: karts with s ahead by (k.s - this.s) mod L. Implement helper.

Track position ranking: progress = lap * L + s (with lapsDone). Rank.

Names and colors:
1. Kart 1 red (#e63946), 2 blue (#2a9df4), 3 yellow (#ffd166), 4 green (#2ecc71), 5 purple (#9b5de5), 6 orange (#ff8c42).

Driver helmet colors distinct.

HUD: top-left lap + position list; center countdown; bottom-right speed? Let's do:
- Top-left: LAP 1/3
- Top-right: timer
- Left list: positions 1-6 with color chips and names, updating order.
- Center: countdown "3","2","1","GO!" then fade.

Implement with DOM and CSS.

Race state machine:
- 'countdown': t from 0 to 3.5s. Karts are on the grid, engines revving (small shake). Lights displayed.
- 'racing'
- 'finished': show "FINISH" and results, then after 6s restart.

Camera logic:
```js
let camMode = 'chase'; let camTimer = 0;
```
Every frame: camTimer -= dt; if <=0 switch: chase for ~7s, trackside for ~3.5s alternating with randomness.

Chase: target = leader (or if race finished, keep leader). Smooth follow: 
desired = leaderPos + (-forward*13) + up*5.5 (+ right* small). camera.position.lerp(desired, 1-exp(-dt*6)). lookAt point = leaderPos + forward*10 + up*1.2, also smoothed.

Trackside: choose a sample ahead of the leader (i + 40..120 samples) with lateral offset ± (12-22) and height 4-9. Camera position fixed (set once). LookAt the leader each frame. Also add slight pan.

Both modes should look good.

Also add subtle camera shake at speed in chase mode.

Let me also add a "sky": scene.background = gradient via CanvasTexture on a sphere? Simplest: scene.background = new THREE.Color(0x87ceeb) with fog. Better: a large sphere with a vertical gradient shader material. Let's do a simple gradient shader on a BackSide sphere. Or a canvas texture used as an equirect background. I'll do the shader sphere — easy.

Add some clouds? Skip. Maybe a few flattened spheres as clouds. Cheap and pretty. Let's add ~20 cloud puffs (spheres with MeshBasicMaterial white, scaled flat, high up). Fine.

Lighting: hemisphere light + directional light with shadows? Shadows cost performance but look good. With 6 karts and instanced trees, shadow map 2048 should be OK. Let's enable shadows for karts and trees (castShadow) onto the ground/road (receiveShadow). Might be heavy for 800-sample road geometry receiving shadows... It's fine.

Hmm, shadow camera needs to cover the whole track (340x340) which makes shadows low-res. Maybe set the shadow camera to follow the leader, covering ~120x120 units. Do that: each frame, set dirLight.position = leaderPos + offset, dirLight.target = leaderPos. That's a common technique. Let's do it.

Actually simpler: skip shadows, use fake shadow blobs under karts (a dark circle plane). That's cheaper and always looks OK. Hmm, real shadows look much better. Let's do real shadows with the follow technique, and also keep the blob? Just real shadows.

Let me set up: renderer.shadowMap.enabled = true, type PCFSoftShadowMap. dirLight.castShadow, mapSize 2048, camera ortho [-80,80,-80,80], near 1, far 400. Light position = target + (60, 100, 40)... normalized * 150. Update per frame with the leader's position (rounded to avoid shimmer). Good.

Trees casting shadows with instanced meshes: InstancedMesh supports castShadow. OK.

Now, particle system details.

```js
const MAXP = 900;
positions = new Float32Array(MAXP*3) init to 0 with y=-1000
alphas = new Float32Array(MAXP)
sizes = new Float32Array(MAXP)
colors = new Float32Array(MAXP*3)
```
Shader material:
```glsl
attribute float size; attribute float alpha; attribute vec3 color;
varying float vAlpha; varying vec3 vColor;
void main(){
  vAlpha = alpha; vColor = color;
  vec4 mv = modelViewMatrix * vec4(position,1.0);
  gl_PointSize = size * (300.0 / -mv.z);
  gl_Position = projectionMatrix * mv;
}
```
fragment:
```glsl
varying float vAlpha; varying vec3 vColor;
void main(){
  vec2 c = gl_PointCoord - 0.5;
  float d = length(c);
  float a = smoothstep(0.5, 0.05, d) * vAlpha;
  if (a < 0.01) discard;
  gl_FragColor = vec4(vColor, a);
}
```
transparent: true, depthWrite: false.

Note: with ShaderMaterial and Points, `gl_PointSize` scaling: `size * (300/-mv.z)` where size is world-ish. If size = 0.6, at 20 units away → 9 px. OK.

Spawning: maintain a cursor index, overwrite the oldest.

Particle update: pos += vel*dt; vel.y -= 2*dt; life -= dt; alpha = life/maxLife * base; size grows slightly.

Each particle needs a life stored in a JS array; store vel in Float32Array too.

Let's write it.

Now scenery generation code.

I need to sample the curve with the precomputed samples for placement (get position at index, plus right vector).

Helper: `function trackPoint(u)` → interpolate sample index.

Let me code the placement using the samples array:
```js
function placeAt(idx, lateral, yOff) {
  const s = samples[idx];
  return s.p.clone().add(s.right.clone().multiplyScalar(lateral)).add(new THREE.Vector3(0, yOff, 0));
}
```
Ground height for scenery: given roadY and lateral distance d: if |d| <= 8.2, y = roadY. Else t = (|d|-8.2)/(80-8.2); y = lerp(roadY-0.2, -2, t).

Trees: place at |d| in [14, 75]. And y = groundY.

But trees inside the loop might be on top of another part of the track! Because the track loops around; a point 70 units inward from one section might be near another section. Since our track is a big loop, the interior is mostly empty, but the inward direction from one part could hit another part if the loop is tight. With the offset limited to ~70 and the track being ~300 across, there's some risk in tight sections. To be safe, do a check: for each candidate, compute the distance to the nearest track sample (brute force over 800 samples × 200 candidates = 160k ops, fine) and if < 12, skip.

That's robust. Let's do that for trees and rocks. Then I can also scatter trees anywhere in a bounding box with that check.

For y placement of a tree at an arbitrary (x,z), I need the terrain height. Terrain = flat at -2 except near the track where the grass ribbon slopes. Computing exact height is complex. Approach: find the nearest track sample, get distance d and roadY, then use the same interpolation formula. Good — reuse nearestSample function.

Let's implement:
```js
function terrainHeight(x, z){
  // find nearest sample
  let best=0, bd=1e9;
  for (let i=0;i<N;i+=4){ const dx=samples[i].p.x-x, dz=samples[i].p.z-z; const d=dx*dx+dz*dz; if(d<bd){bd=d;best=i;} }
  // refine around best
  const d = Math.sqrt(bd);
  const roadY = samples[best].p.y;
  if (d <= 8.2) return roadY;
  const t = Math.min(1,(d-8.2)/71.8);
  return roadY + (-2 - roadY)*t;
}
```
Hmm, but the road y should be at the nearest point. Also for the outer side, the grass ribbon edge y = -2 at 80 out. Yes consistent.

But wait: the grass ribbon mesh I build uses the road's own frame per sample; near-tangential regions could conflict, but whatever, it's approximate. Since we skip objects within 12 units of track, the ribbon will look consistent enough.

Hmm, actually the grass ribbon from one part of the track could overlap the road of another part if the loop is tight. Let's check the control points: the min gap between different parts... e.g., (0,0,-160) and (-40,5,-170) — these are adjacent on the loop, fine. The inner hole is large. The inner grass extends 80 units inward, which for a track ~340 wide means the interior is fully covered by grass ribbons converging near the center. That could create weird overlaps/z-fighting in the middle. Since the camera is low, we won't see it much. Alternatively, use 45 units for the grass ribbon and rely on the flat plane at -2 for the rest. Overlaps are less likely then. But then the slope from roadY to -2 over 45 units... fine.

Let's do grass ribbon width 50 (from 8.2 to 50), sloping to y = -2 (absolute, but clamp so it doesn't go above the road: if roadY < -2, no; min roadY is 0 so fine). Hmm, at road y=0 the grass slopes from -0.2 down to -2, a gentle dip. Fine.

And the big ground plane at y=-2.02 with a green color, 2000x2000.

Now let's write the road geometry.

```js
function buildRibbon(offsets, yOffsets, colorFn) 
```
Let me just write specialized loops.

Road: for i in 0..N (inclusive, wrapping i%N), vertices: L = p + right*(-hw) + (0, yOff,0), R = p + right*(hw). Two triangles per segment. UVs: u = 0/1, v = i * (totalLen/N) / 8.

Kerb: on each side, from hw to hw+1.2, with alternating colors per segment (every 4 samples change? No — alternating per segment gives very fine stripes ~1.4 units — good, that's like a real kerb). Actually real kerbs are red/white alternating over ~1m. Since each segment is 1.4 units, alternate every segment. But with 800 segments it creates a lot of geometry; it's fine (1600 quads per side). Actually let's build the kerb with 4 bands: use vertex colors alternating per sample.

Kerbs should only be in corners, but let's put them all around for simplicity. Actually a kerb around the whole track is fine and looks nice.

Kerb geometry: quads from offset hw to hw+1.2 with vertices colored red/white per segment. Build as non-indexed triangles with vertex colors, using a MeshLambertMaterial with vertexColors: true.

Also lift the kerb y slightly: +0.06 at the inner edge, +0.1 at the outer? Real kerbs are raised. Let's make the outer edge slightly higher: y + 0.12. And the road edge at 0.

Edge lines: white line at hw-0.1..hw+0.1? Optional. Let's put the kerb directly adjacent and add a white line just inside the kerb (from hw-0.5 to hw-0.1) — hmm, might be too much. Keep it simple: road with kerbs, plus a start/finish line (checkered strip across the road at u=0).

Start/finish line: a plane 14 wide, 2 long, at sample 0, rotated to align with tangent, with a canvas checkered texture. Place slightly above the road (+0.02).

Also a gantry over the start line: two posts and a beam.

Road texture: procedural canvas asphalt — small noise. Let's make a 256x256 canvas: base #3a3a3d, add random gray speckles, repeat 4 x (many). Set wraps.

Actually, applying a texture with a UV v that goes 0..(length/8) means the texture repeats every 8 units along the track and once across the width. Fine.

Let me write the canvas texture functions.

```js
function makeAsphaltTexture(){
  const c = document.createElement('canvas'); c.width = c.height = 256;
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#3b3b40'; ctx.fillRect(0,0,256,256);
  for (let i=0;i<20000;i++){
    const x=Math.random()*256, y=Math.random()*256;
    const g = 40 + Math.random()*50;
    ctx.fillStyle = `rgba(${g},${g},${g+4},${0.5})`;
    ctx.fillRect(x,y,1.6,1.6);
  }
  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  return tex;
}
```

Grass texture similar with green noise.

Checkered texture for start line and gantry banner.

OK let's write everything now.

Order of code:
1. Imports, renderer, scene, camera, lights.
2. Textures.
3. Track curve + samples.
4. Road, kerb, grass, ground, start line, gantry.
5. Scenery (trees, rocks, stands, clouds).
6. Particle system.
7. Kart class + 6 karts.
8. Race state machine + HUD.
9. Camera controller.
10. Animate loop.

Let me write code.

```js
import * as THREE from 'three';

const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0x9fc6e8, 220, 620);
const camera = new THREE.PerspectiveCamera(65, innerWidth/innerHeight, 0.5, 2000);
const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);
```

Sky gradient: use a large sphere with ShaderMaterial (BackSide).

```js
const skyGeo = new THREE.SphereGeometry(900, 32, 16);
const skyMat = new THREE.ShaderMaterial({
  side: THREE.BackSide, depthWrite: false,
  uniforms: { top: {value: new THREE.Color(0x2b6fb5)}, bot: {value: new THREE.Color(0xcfe8ff)} },
  vertexShader: `varying vec3 vP; void main(){ vP = position; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0);} `,
  fragmentShader: `uniform vec3 top; uniform vec3 bot; varying vec3 vP; void main(){ float h = clamp(vP.y/500.0*0.5+0.5, 0.0, 1.0); gl_FragColor = vec4(mix(bot, top, h), 1.0);} `
});
```
Wait, but with fog, the sky sphere is at 900 and fog far 620... the sky material doesn't have fog (ShaderMaterial default fog: false). Good.

Also, the fog color should match the horizon: 0xa8c8e8.

Lights:
```js
const hemi = new THREE.HemisphereLight(0xbfe3ff, 0x4a6b3a, 0.85);
scene.add(hemi);
const sun = new THREE.DirectionalLight(0xfff2d0, 1.6);
sun.castShadow = true;
sun.shadow.mapSize.set(2048,2048);
const sc = sun.shadow.camera; sc.left=-70; sc.right=70; sc.top=70; sc.bottom=-70; sc.near=1; sc.far=400;
scene.add(sun); scene.add(sun.target);
```

Track control points — let me design a nicer circuit with hills, scale ~ ±200.

```js
const CTRL = [
  [0, 2, -200],
  [110, 8, -190],
  [190, 12, -110],
  [175, 10, -20],
  [210, 6, 60],
  [170, 2, 130],
  [90, 1, 175],
  [0, 4, 150],
  [-80, 9, 185],
  [-165, 12, 140],
  [-205, 8, 60],
  [-175, 4, -20],
  [-200, 6, -110],
  [-120, 10, -180],
  [-50, 6, -205],
];
```
This makes a big loop ~420x400. Circuit length roughly 1300. With lap time ~14s → speed ~93 u/s. That's fast, but the world is big (karts 3.6 long). Hmm, 93 u/s with karts ~4 units long = 23 karts per second. Looks like F-Zero speeds. Might be too fast for the camera to follow nicely. Let's instead make the track smaller: scale by 0.65, giving a loop ~280x260 and length ~850. Then speed ~60 u/s for a 14s lap. Still fast-ish, comparable to Mario Kart, that's fine.

Actually, let's keep the coordinates but set lap time ~16s → speed ~80. Hmm.

Let's compromise: scale control points by 0.7 → max radius ~145, length ~900. Speed for a 15s lap = 60 u/s. Kart length 3.6. That's like 17 kart lengths per second — fast but arcade-y. Mario Kart does about that. OK.

Actually, let's think about the camera: at 60 u/s, a chase camera 13 units behind will see the world rushing by; that's fine and exciting.

I'll scale the control points by 0.7 in code.

Half width 7 → road 14 wide, karts ~2.2 wide, 6 karts side by side would be 13 — good, allows overtaking.

Let me finalize the numbers:
- scale 0.7 → coordinates up to 147, elevations up to 8.4.
- N = 900 samples.
- totalLen ≈ let's estimate: the loop through those points... perimeter of the polygon roughly: points are roughly on an ellipse of 350x400 → perimeter ~1180. After ×0.7 → ~830. Plus curve smoothing. So ~850.

Lap time target ~13-15s → speed ~60. Kart max speed = 68, corner speeds down to 38.

Fine.

Now let's write sample computation:

```js
const curve = new THREE.CatmullRomCurve3(CTRL.map(p=>new THREE.Vector3(p[0]*S, p[1]*S, p[2]*S)), true, 'catmullrom', 0.5);
const N = 900;
const pts = [];
for (let i=0;i<N;i++) pts.push(curve.getPointAt(i/N));
// tangents
const tans = [];
for (let i=0;i<N;i++){
  const a = pts[(i-1+N)%N], b = pts[(i+1)%N];
  tans.push(b.clone().sub(a).normalize());
}
const rights = tans.map(t => new THREE.Vector3().crossVectors(t, UP).normalize());
```
Wait: right = cross(T, up). Earlier I computed cross(T,up) with T=(0,0,1) gives (-1,0,0) and I said that's the track right vector and it matches the model's local X. Hmm, let me double check what "right" means physically. Moving along +Z, up +Y: your right hand points to -X? Let's see: standard right-handed, X right, Y up, Z toward viewer. If I'm facing +Z (toward the viewer/out of the screen), then my right is -X (screen left). Yes. So cross(T,up) = (-1,0,0) is indeed the right side. Consistent.

Curvature:
```js
const ds = curve.getLength()/N;  // actually use totalLen/N
const curv = new Float32Array(N);
for (let i=0;i<N;i++){
  const dT = tans[(i+1)%N].clone().sub(tans[i]);
  curv[i] = dT.dot(rights[i]) / ds;
}
```
Smooth curv with a 5-tap box blur, a few passes.

Racing line offset:
```js
const raceOff = new Float32Array(N);
for (let i=0;i<N;i++){
  raceOff[i] = THREE.MathUtils.clamp(curv[i]*160, -5, 5);
}
// smooth
```
Hmm, kappa max: for a corner radius of 25 → 0.04 → ×160 = 6.4 → clamped to 5. Good.

But the racing line offset should also lead into the corner earlier and exit later. Smoothing it over ±20 samples (~20 units) handles that roughly. Let's do a couple of blur passes with a radius of 15.

Also should the racing line be offset toward the inside of the corner: inside = the direction the track turns = sign(kappa) * right. Yes, offset = +k*C along right. Good.

Now speed target per sample:
```js
const cornerSpeed = new Float32Array(N);
for (let i=0;i<N;i++){
  // max curvature over next 60 units
  let mk=0;
  for (let j=0;j<45;j++){ mk = Math.max(mk, Math.abs(curv[(i+j)%N])); }
  cornerSpeed[i] = MAXSPEED * clamp(1 - mk*14, 0.45, 1);
}
```
Precompute this once and use it (cheap, and avoids per-kart computation).

Actually use a smoothed max over the lookahead. Just take the max.

MAXSPEED = 62. Corner speed at mk=0.04 → 1-0.56 = 0.44 → clamped 0.45 → 28. Hmm, that's a big slowdown. The corners here have radius maybe 40-80 given the smooth Catmull-Rom, so mk ~ 0.012-0.025 → factor 0.83-0.65 → speed 40-52. Fine.

Now kart AI:
```js
class KartAI {
  constructor(index){
    this.index = index;
    this.s = 0; this.x = 0; this.speed = 0;
    this.laps = 0;
    this.targetX = 0;
    this.slip = 0;
    this.wheelSpin = 0;
    ...
  }
}
```

Start grid: place karts at s = -(3 + row*8) relative to totalLen, i.e. this.s = (totalLen - 3 - row*8) % totalLen. With two per row: rows 0,1,2 with lateral -3.5 and +3.5.

Actually the start line is at u=0. Grid rows behind it. Kart i (0..5): row = floor(i/2), col = i%2 → lateral = (col===0? -3.2 : 3.2). s = totalLen - 6 - row*9.

Hmm, but "laps" counting: when they cross s=0, laps++. At the start they're behind the line, so the first crossing increments laps to 1 immediately. So display lap = min(laps+1, total) would show 2 at the start... Bad.

Fix: initialize laps = -1 conceptually? Let's set `this.laps = 0` and treat the first line crossing as the start of lap 1. So: if crossing the line and laps === 0 → this is the race start (already done), so we set laps = 1. Then on the second crossing laps = 2... Finish when laps > totalLaps? Let's define: laps completed = laps. Kart crosses the start line for the first time shortly after the start → laps becomes 1 → that means "on lap 2" for display? No...

Let's simplify: give each kart a start position behind the line, and increment `lap` on each crossing including the first. Display lap = max(1, lap). So right after the start, lap = 1 → "LAP 1/3". After a full lap, lap = 2 → "LAP 2/3". After three full laps, lap = 4 → finished. So finish when lap > totalLaps, i.e. lap === totalLaps+1 = 4. And progress = (lap-1)*L + s. Good, that's consistent.

Wait but the first crossing happens ~0.1s after the start; between t=0 and then, lap=0 → display max(1,0)=1. Fine.

Grid spacing: karts at s = totalLen - 6 - row*9, so the last row is at -24 from the line. They all cross the line within ~0.5s of the start. Fine.

Race finish: when a kart's lap > totalLaps, mark finishTime and position. Race ends when all finish or when the leader finishes + 5s.

Then show results, wait 5s, reset.

Countdown: 4.5s: "3", "2", "1", "GO!" — use 1s each, with a 0.5s pre-delay. Karts don't move (speed forced 0) until GO.

Now the particle spawn: only when racing.

Let's write the kart visuals.

```js
function makeKart(color, helmetColor){
  const g = new THREE.Group();
  const bodyMat = new THREE.MeshStandardMaterial({color, metalness:0.3, roughness:0.5});
  const darkMat = new THREE.MeshStandardMaterial({color:0x222228, roughness:0.7});
  // chassis
  const chassis = new THREE.Mesh(new THREE.BoxGeometry(2.0, 0.55, 3.4), bodyMat);
  chassis.position.y = 0.62; chassis.castShadow = true; g.add(chassis);
  // nose
  const nose = new THREE.Mesh(new THREE.BoxGeometry(1.3,0.4,1.2), bodyMat);
  nose.position.set(0,0.5,1.9); nose.castShadow=true; g.add(nose);
  // side pods
  ...
  // seat
  // driver torso
  const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.35,0.42,0.7,10), suitMat);
  torso.position.set(0,1.15,-0.35);
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.34,14,10), helmetMat);
  head.position.set(0,1.62,-0.3);
  // visor
  // wheels
}
```

Wheels: front two at z=+1.15, rear at z=-1.15, x=±1.05.
Wheel mesh: CylinderGeometry(0.45,0.45,0.35,16) rotated so the axis is along X: rotation.z = Math.PI/2.

Wheel group for steering: create wheelPivot at position, add the wheel mesh to it. Steering rotates the pivot around Y.

For rolling: the wheel mesh rotates. If the wheel cylinder's axis is along X (after rotation.z = π/2), then rolling is around the X axis → rotate the mesh around... The mesh already has rotation.z = π/2 applied; adding rotation.x would compose weirdly. Better: create a parent "spin" group holding the wheel mesh with the z-rotation, and spin the group around X. Actually if the cylinder's axis is along X, then spinning it around the X axis rotates it correctly. Put the cylinder in a group with the cylinder's rotation.z=π/2, then rotate the group's rotation.x. Wait, rotating the group around X: the cylinder's axis is along the group's X axis, so the group rotation around X spins the cylinder around its own axis. Yes. Correct.

So: wheelGroup (position, steer via rotation.y for front) → spinGroup (rotation.x = spin) → cylinder mesh (rotation.z = π/2).

Good.

Also front wheels should show some steering angle from the AI. steerAngle = based on lateral velocity and curvature.

Now the kart's world transform update:

```js
const idx = this.si (float sample index) 
const p = sample position interpolated + right*x
```
Let's interpolate between samples for smoothness:
```js
const fi = (this.s / totalLen) * N;
const i0 = Math.floor(fi) % N, i1 = (i0+1)%N, f = fi - Math.floor(fi);
pos = lerp(pts[i0], pts[i1], f) + lerp(rights[i0], rights[i1], f) * this.x
tan = lerp(tans[i0], tans[i1], f).normalize()
curvHere = curv[i0]
```

Then yaw = atan2(tan.x, tan.z) + slip.
Pitch: from the tangent's y component and the track slope: pitch = -asin(tan.y)? With forward = +Z, pitching up means rotating around X by -angle... Let's just compute the basis directly to avoid sign errors:

forward = tan (normalized, includes y).
worldUp = (0,1,0).
right = cross(forward, worldUp).normalize()  → this is the track's right vector.
up = cross(right, forward).normalize()  → gives the local up perpendicular to forward.

Then apply slip by rotating forward and right around `up`:
```js
const q = new THREE.Quaternion().setFromAxisAngle(up, slipAngle);
forward.applyQuaternion(q); right.applyQuaternion(q);
```
Hmm, but rotating "right" around "up" by slipAngle: if slipAngle is positive, the forward rotates toward ... let's just accept the sign and tune. Actually let's think: we want for a right turn (curv > 0) the nose to point to the right (toward +trackRight). Rotating forward around up by angle θ: by the right-hand rule around up=(0,1,0), positive θ rotates from +Z toward +X? Rotation around Y by +θ: (x,z) → (x cosθ + z sinθ, -x sinθ + z cosθ). For forward=(0,0,1): → (sinθ, 0, cosθ)... wait using the standard three.js matrix for rotation around Y: 
[cosθ, 0, sinθ; 0,1,0; -sinθ, 0, cosθ] applied to (0,0,1) gives (sinθ, 0, cosθ). So +θ moves toward +X. And the track right for forward=+Z is (-1,0,0) = -X. So +θ moves toward left. So for a right turn we want θ negative. slip = -curv*K.

OK.

Then bank roll: rotate right and up around forward by rollAngle. Banking into the corner: for a right turn, the kart leans left? Actually karts bank toward the inside in a turn... Let's just add a small roll: roll = clamp(curv*200, -0.12, 0.12) and apply it around the forward axis so it looks dynamic. Sign doesn't matter much visually.

Then build the matrix:
```js
const m = new THREE.Matrix4().makeBasis(right, up, forward);
this.group.quaternion.setFromRotationMatrix(m);
this.group.position.copy(pos);
```
Note: makeBasis(xAxis, yAxis, zAxis) requires an orthonormal right-handed basis. right = cross(forward, up_world) and up = cross(right, forward) gives: is (right, up, forward) right-handed? Check with forward=+Z, up=+Y: right = cross(Z,Y) = (0,0,1)×(0,1,0) = (0*0-1*1, 1*0-0*0, 0*1-0*0) = (-1,0,0). up = cross(right, forward) = (-1,0,0)×(0,0,1) = (0*1-0*0, 0*0-(-1)*1, 0) = (0,1,0). Good. So basis = ((-1,0,0),(0,1,0),(0,0,1)). Determinant: x×y should equal z: (-1,0,0)×(0,1,0) = (0*0-0*1, 0*0-(-1)*0, -1*1-0*0) = (0,0,-1) ≠ z. So it's left-handed! Bad.

So I need right = cross(up, forward)? cross(Y,Z) = X = (1,0,0) for forward=+Z. Then det: x×y = (1,0,0)×(0,1,0) = (0,0,1) = z. Right-handed. 

But then the local +X = (1,0,0) which is the "left" side physically. That doesn't matter for a symmetric kart, as long as the wheels are mirrored symmetrically. Fine. So use xAxis = cross(up_world, forward).

Hmm, but then when I apply a lateral offset via the track's "right" vector (cross(T, up)), the sign relative to the kart's local X flips, but that's fine because the offset is just a lateral position; the steering visuals (front wheel yaw) might be mirrored. I'll handle that by using the same convention consistently: define the "lateral axis" L = cross(up, forward) (the kart's local +X), and everything (racing line offset, avoidance) uses L. Since cross(up,T) = -cross(T,up), the racing offset changes sign, but that's handled automatically as long as I use kappa consistent with L.

Let's redefine: renaming to avoid confusion.

Let R_track = cross(T, up) (the physical right).
Let Xkart = cross(up, T) = -R_track.

For curvature: kappa = dT·R_track/ds (positive = turning right).
Racing offset (physical right positive) = clamp(kappa*C).

When converting offset to a position: pos = p + R_track * x.

For the kart's orientation: X-axis = cross(up, T) = -R_track. With basis (Xkart, up, T) it's right-handed. Good.

And the slip rotation: rotating forward around up by θ moves +Z toward +X in world (as computed). Since the kart's local +X = cross(up,T), which for T=+Z is +X world... and rotating +Z by +θ gives (sinθ,0,cosθ) which is toward +X world = the kart's local +X. So a positive slip rotates the nose toward the kart's local +X. The kart's local +X corresponds to the physical left (since the physical right is -X). So a positive slip points the nose left.

For a right turn (kappa>0), we want the nose to point right (physically) = toward -X = negative θ. So θ = -kappa*K. Same as before. OK good.

Banking/roll around the forward axis: with the basis (X, up, T) right-handed, rolling around +T by angle φ rotates X toward up. Let's just apply a small roll for style; sign doesn't matter much.

Implementation:

```js
const fwd = tan.clone();
const upw = new THREE.Vector3(0,1,0);
const xk = new THREE.Vector3().crossVectors(upw, fwd).normalize();
const upk = new THREE.Vector3().crossVectors(fwd, xk).normalize(); // fwd × xk = z × x = y ✓
```
Check: xk × upk should = fwd. xk=+X, upk=+Y → X×Y=Z=fwd ✓.

Then apply slip: rotate xk and fwd around upk by θ.

Then apply roll: rotate xk and upk around fwd by φ.

Then makeBasis(xk, upk, fwd).

Good.

Now let me write the AI update.

```js
update(dt, all, raceState){
  if (raceState !== 'racing') { this.speed *= 0.9; ... }
  const i = this.sampleIndex();
  // target speed
  let wantSpeed = cornerSpeed[i] * this.skill * (this.catchup);
  ...
}
```

Actually, cornerSpeed is precomputed per sample with MAXSPEED. Multiply by skill (0.95..1.05).

Catch-up (rubber banding): based on the gap to the leader in progress. If behind by more than 30 units, add up to +12%; if ahead, reduce slightly. Keeps the pack together → more overtaking.

Lateral control:
```js
let xWant = raceOff[i];
// avoidance
for (const o of all) if (o !== this) {
  const gap = mod(o.s - this.s, L);
  if (gap > 0 && gap < 16) {
    const dx = o.x - this.x;
    if (Math.abs(dx) < 3.4) {
      // need to go around
      const dir = (this.x > o.x) ? 1 : -1;  // move further to our side
      ...
    }
  }
}
```
Hmm. Let's do: if a kart is ahead within 16 units and laterally close (< 3.2), then pick a passing side: prefer the side where there's more room considering the road width and the other karts. Simple: choose the side (left/right) with larger |roadHalf - 1.6| availability... Let's compute: desiredPass = (o.x > 0) ? -3.5 : 3.5 — go to the opposite side of the opponent. But if the opponent is at 0, pick based on this kart's current x sign or index parity. Then xWant = clamp(desiredPass, -5.5, 5.5). And add a bit of extra braking if gap < 6 and we can't pass.

Also, we want them to not all converge to the same line. Fine.

Let's add per-kart preferred line offset: lineBias in [-1,1] scaled by 1.5, added to raceOff.

Overtake also: if a kart is slower and blocked, the one behind will slow down too. Add: if gap < 5 and |dx| < 2.5 → reduce target speed by 15%.

Collision resolution: after updating all, for each pair with wrapped gap < 4 and |dx| < 2.6 → push apart laterally (each moves 0.5 of the overlap) and equalize speed slightly.

Let's implement a simple version: push apart laterally proportional to the overlap.

Speed update:
```js
const accel = 40, brake = 70;
if (this.speed < wantSpeed) this.speed = Math.min(wantSpeed, this.speed + accel*dt);
else this.speed = Math.max(wantSpeed, this.speed - brake*dt);
this.s = (this.s + this.speed*dt) % L;
```

Lap detection: keep prevS; if s < prevS - L/2 → crossed line → lap++.

Lateral movement:
```js
const xRate = 9;
this.x += clamp(xWant - this.x, -xRate*dt, xRate*dt);
this.x = clamp(this.x, -6, 6);
```
Also store dxLateral = (this.x - prevX)/dt for the drift visual.

Drift intensity: 
```js
const lateralSpeed = Math.abs(dxLateral);
const cornering = Math.min(1, Math.abs(curv[i]) * 45 * (this.speed/MAXSPEED));
const drift = Math.max(cornering*0.7, lateralSpeed*0.08) → clamp 0..1
```
Something like that. Then slip = -sign(curv[i]) * drift * 0.35 rad.

Hmm, actually the slip should look like oversteer: nose pointing into the corner while sliding outward. Let's do slip = -Math.sign(curv[i]) * drift * 0.3. Wait we determined θ negative for a right turn (curv>0). So slip = -curv_sign * drift * 0.35 → for curv>0, slip negative ✓.

Also spawn dust when drift > 0.25.

Wheel spin: spin += speed/0.45 * dt (radius 0.45) → the wheel's rotation.x. But which direction? The wheel rotates forward; with the kart moving +Z local, the wheel rotates... rotation.x positive rotates +Z toward +Y? Rotation around X by +θ: y→z mapping. For rolling forward (moving +Z), the top of the wheel moves +Z, so the wheel rotates around the -X axis... Let's just use `-speed*dt/0.45` and not worry; a spinning wheel's direction is barely visible. Actually it might be visible since the wheels are cylinders without spokes — no visual difference. Fine, either way.

Steering visual: front wheel rotation.y = clamp(lateral velocity * something + curv-based). Let's do steerAngle = clamp(-(xWant - x)*0.15 - curv[i]*15, -0.5, 0.5) roughly. Hmm, sign: for a right turn (curv>0), the front wheels should point right. The kart's local +X is the physical left. Rotating the wheel pivot around Y by +θ rotates the wheel's forward (+Z) toward +X (local) = left. So for a right turn we want negative θ. Curv>0 → θ = -curv*K. OK consistent with the slip sign.

Let's set steerAngle = clamp(-curv[i]*12 - (xWant-this.x)*0.08, -0.45, 0.45). Then also smooth it.

Now the position/ranking:

```js
function progressOf(k){ return (k.lap-1)*L + k.s; }
```
Hmm, at the start lap=0 → progress = -L + s, where s is near L → progress ≈ -small. That's consistent (all slightly negative). Good, monotonic. Actually with lap=0 and s ≈ L-6, progress = -L + L-6 = -6. And after crossing the line lap=1, s≈0 → progress = 0 + 0 = 0. Monotonic ✓.

Sort descending.

Display: name, color, lap.

Now the camera.

```js
const camState = { mode:'chase', timer: 6 };
function updateCamera(dt){
  const leader = karts[order[0]];
  camState.timer -= dt;
  if (camState.timer <= 0) {
    if (camState.mode === 'chase') { camState.mode='trackside'; camState.timer = 3.2; setupTrackside(leader); }
    else { camState.mode='chase'; camState.timer = 6 + Math.random()*3; }
  }
  if (camState.mode === 'chase') { ... } else { camera.position.copy(tsPos); camera.lookAt(leaderPos + up*1); }
}
```

Chase: 
```js
const fwd = leader.forwardVec; // world
const desired = leaderPos.clone().addScaledVector(fwd, -11).add(new THREE.Vector3(0,5.0,0));
camera.position.lerp(desired, 1 - Math.exp(-7*dt));
const lookTarget = leaderPos.clone().addScaledVector(fwd, 9).add(0,1.6,0);
camLook.lerp(lookTarget, 1-Math.exp(-9*dt));
camera.lookAt(camLook);
```
Also add FOV increase with speed: camera.fov = 62 + speed*0.15; updateProjectionMatrix.

Trackside: pick a sample index ahead: idx = (leaderIdx + 60 + rand*120) % N, lateral = ±(14 + rand*10), y = roadY + 4 + rand*4. Camera looks at the leader. Also could look at the nearest kart, but leader is fine.

Actually, when cutting to trackside, the camera should already be positioned before the cut. It works since we set the position instantly.

OK. Also at the race start, before the countdown ends, use a slow orbit around the grid or a long shot. Let's have the countdown camera be a static wide shot of the grid, then cut to chase on GO. Nice.

Let's implement: mode 'grid' during countdown — camera positioned at the side of the grid looking at the pack. On GO, switch to chase.

HUD update: rebuild the position list every ~0.2s.

Let me now write the final code.

One more thing: the "position list 1st-6th" needs to show colors. Use a div per kart with a color chip.

Let's write the HTML/CSS.

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Kart GP</title>
<style>
  html,body{margin:0;height:100%;overflow:hidden;background:#87b8e0;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;}
  canvas{display:block}
  #ui{position:fixed;inset:0;pointer-events:none;color:#fff;}
  .panel{position:absolute;background:rgba(10,15,25,.55);backdrop-filter:blur(4px);border-radius:12px;padding:10px 14px;}
  #standings{top:16px;left:16px;min-width:190px}
  #standings h3{...}
  .row{display:flex;align-items:center;gap:8px;font-size:14px;padding:2px 0}
  .chip{width:12px;height:12px;border-radius:3px}
  #lapBox{top:16px;right:16px;text-align:right}
  #countdown{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:120px;font-weight:900;text-shadow:...}
  ...
</style>
```

Let me write it out fully now.

Some care with the particle buffer setup and shader.

Also performance: 900 road samples × 2 tris, kerb 2 sides × 900 × 2 tris, grass 2 × 900 × 2. Total ~10k triangles. Fine.

Shadows: the road receives shadows; that requires the road mesh to have receiveShadow=true.

Let's write the code.

```js
// ---------- Utility
const UP = new THREE.Vector3(0,1,0);
const clamp = (v,a,b)=>Math.max(a,Math.min(b,v));
const lerp = (a,b,t)=>a+(b-a)*t;
const mod = (a,n)=>((a%n)+n)%n;
```

Textures:

```js
function noiseTexture(base, variance, size=256, repeat=1){
  const c = document.createElement('canvas'); c.width=c.height=size;
  const ctx = c.getContext('2d');
  ctx.fillStyle = base; ctx.fillRect(0,0,size,size);
  const img = ctx.getImageData(0,0,size,size);
  const d = img.data;
  for (let i=0;i<d.length;i+=4){
    const n = (Math.random()-0.5)*variance;
    d[i] = clamp(d[i]+n,0,255); d[i+1]=clamp(d[i+1]+n,0,255); d[i+2]=clamp(d[i+2]+n,0,255);
  }
  ctx.putImageData(img,0,0);
  const t = new THREE.CanvasTexture(c);
  t.wrapS=t.wrapT=THREE.RepeatWrapping;
  t.repeat.set(repeat,repeat);
  return t;
}
```

Road texture: noiseTexture('#3c3c42','60', 256). Repeat set later on UVs. Since I set UV v to repeat along the track, I need wrapT repeat and repeat.y = 1. Let me set the UVs directly with the desired repeat count. So the texture repeat should be (1,1) and the UVs handle it.

Grass: noiseTexture('#4f8b3b','50',256).

Checkered: for the start line.

Now, the road mesh geometry construction:

```js
const roadPositions = [], roadUvs = [], roadIndices = [];
const HW = 7;
for (let i=0;i<=N;i++){
  const k = i%N;
  const p = pts[k], r = rights[k];
  const l = p.clone().addScaledVector(r,-HW);
  const rr = p.clone().addScaledVector(r, HW);
  roadPositions.push(l.x, l.y+0.0, l.z, rr.x, rr.y, rr.z);
  const v = (i/N) * (L/8);
  roadUvs.push(0, v, 1, v);
}
for (let i=0;i<N;i++){
  const a = i*2, b = i*2+1, c = i*2+2, d = i*2+3;
  roadIndices.push(a,c,b, b,c,d);
}
```
Winding: need the normals to face up. Let's just compute normals with computeVertexNormals and check... Instead of guessing, I'll set the material to DoubleSide? That's cheaper to reason about. But shadows and lighting work better with correct normals. Let's use FrontSide and get the winding right, or just use DoubleSide for the road — it's a flat ribbon, fine. Actually with lighting, a back-facing normal would make the road black. computeVertexNormals uses the winding. Let's reason:

Vertices: a = left(i), b = right(i), c = left(i+1), d = right(i+1). Triangle (a,c,b): edge1 = c-a = forward, edge2 = b-a = right(2*HW). Normal = edge1 × edge2 = T × R_track. For T=+Z, R = -X: (0,0,1)×(-1,0,0) = (0*0-1*0, 1*(-1)-0*0, 0) = (0,-1,0). Downward. Bad.

So use (a,b,c) and (b,d,c): normal = (b-a)×(c-a) = R×T = (-1,0,0)×(0,0,1) = (0*1-0*0, 0*0-(-1)*1, 0) = (0,1,0). Up ✓.

So indices: a,b,c and b,d,c.

Wait, check the second: (b,d,c): edge1 = d-b = T, edge2 = c-b = -R + T... let's just compute: b=right(i), d=right(i+1), c=left(i+1). (d-b) = T*ds. (c-b) = -R*2HW + T*ds. Normal = (d-b)×(c-b) = (T*ds)×(-R*2HW + T*ds) = ds*(-2HW)(T×R) = -2HW*ds*(T×R) = -2HW*ds*(-up) = up*2HW*ds ✓. Good.

So for each i: push (a,b,c) and (b,d,c).

Now kerbs. For the right side: from offset HW to HW+1.3, with the outer edge lifted by 0.14. Alternate the colors per segment i%2.

I'll build a non-indexed geometry with vertex colors:
```js
for (let i=0;i<N;i++){
  const k0=i, k1=(i+1)%N;
  const col = (i%2===0) ? 0xd83a3a : 0xf2f2f2;
  // inner edge points at HW, outer at HW+1.3, lifted
  const a = pts[k0] + rights[k0]*HW ; y+0.02
  const b = pts[k0] + rights[k0]*(HW+1.3); y+0.16
  const c = pts[k1] + rights[k1]*HW; y+0.02
  const d = pts[k1] + rights[k1]*(HW+1.3); y+0.16
  push triangles (a,b,c) and (b,d,c) with the color
}
```
Wait, winding for the right side: (a,b,c) where a=inner(k0), b=outer(k0), c=inner(k1). (b-a)=R*1.3, (c-a)=T*ds. Normal = R×T = -up. Downward. Bad. Swap: (a,c,b) → normal = T×R = up ✓. And (b,c,d)? Let's be consistent: use (a,c,b) and (b,c,d). Check (b,c,d): edge1 = c-b = -R*1.3 + T*ds, edge2 = d-b = T*ds. Normal = edge1×edge2 = (-R*1.3 + T*ds)×(T*ds) = -1.3*ds*(R×T) = -1.3*ds*(-up) = up ✓.

For the left side, negative offsets: a = inner (-HW) at k0, b = outer (-HW-1.3). (b-a) = -R*1.3. Normal for (a,b,c) = (-R*1.3)×(T*ds) = -1.3ds*(R×T) = +up ✓. So the left side uses (a,b,c) and (b,d,c).

I'll write a helper `addQuadGeo(arr, a,b,c,d, flip)` that pushes two triangles with the given winding.

Simpler: write a function that builds a strip given a side sign.

```js
function buildStrip(offInner, offOuter, yInner, yOuter, colorFn){
  const pos=[], col=[], idx=[];
  for (let i=0;i<=N;i++){
    const k=i%N;
    const p=pts[k], r=rights[k];
    const si = sign;
    ...
  }
}
```
Let me just write it inline for both sides with the sign handled by reversing the vertex order when side<0. Actually easier: build the strip with offsets multiplied by `side`, and if side<0, reverse the triangle winding.

OK let's write:

```js
function makeStrip(side, o0, o1, dy0, dy1, colorFn){
  const positions=[], colors=[], indices=[];
  for (let i=0;i<=N;i++){
    const k=i%N, p=pts[k], r=rights[k];
    const A = p.clone().addScaledVector(r, side*o0); A.y += dy0;
    const B = p.clone().addScaledVector(r, side*o1); B.y += dy1;
    positions.push(A.x,A.y,A.z, B.x,B.y,B.z);
    const c = colorFn(i);
    colors.push(c.r,c.g,c.b, c.r,c.g,c.b);
  }
  for (let i=0;i<N;i++){
    const a=i*2, b=i*2+1, c=i*2+2, d=i*2+3;
    if (side>0) indices.push(a,c,b, b,c,d);
    else indices.push(a,b,c, b,d,c);
  }
  ...
}
```
Check for side>0 (right side, o0=HW inner, o1=outer): A=inner, B=outer. Same as before ✓.
For side<0 (left): A = -HW*... i.e. inner at -HW, B = outer at -(HW+1.3). Earlier I determined (a,b,c) is correct for the left side ✓. So `indices.push(a,b,c, b,d,c)` where a=A_i, b=B_i, c=A_{i+1}, d=B_{i+1}. Yes that matches.

Hmm wait, for the left side I defined a=inner(k0), b=outer(k0), c=inner(k1) — in the strip loop, a = i*2 = A_i = inner ✓, b = i*2+1 = B_i = outer ✓, c = A_{i+1} ✓, d = B_{i+1} ✓. Good.

Grass: same helper with o0 = HW+1.3, o1 = HW+50, dy0 = -0.15, dy1 = -2 (absolute? no, dy is relative to the road y). Hmm, I wanted the outer edge at absolute y=-2. Let's make dy1 computed per point: y = -2 - p.y. That's a per-vertex computation. Let me generalize the helper to accept functions for the y offsets. Or just special-case the grass with its own loop.

I'll write a more general helper that takes a function (k, p, r, out) for each edge. Simpler: write two separate loops. Let me just write a function:

```js
function buildTerrainStrip(side, offset0, offset1, yFn0, yFn1, colorFn){
  // yFn(k, p) returns world y
}
```
OK.

Actually let me simplify: just write the grass strip inline.

Let me now write everything concretely. I'll be careful.

For the ground plane: a plane 1600x1600 at y=-2, rotated -π/2, green. Use a MeshLambertMaterial with the grass texture with a large repeat.

Now, scenery placement helpers:

```js
function nearestTrack(x,z){
  let best=0, bd=1e9;
  for (let i=0;i<N;i+=3){
    const dx=pts[i].x-x, dz=pts[i].z-z; const d=dx*dx+dz*dz;
    if (d<bd){bd=d;best=i;}
  }
  return {i:best, dist:Math.sqrt(bd)};
}
```
N=900, step 3 → 300 iterations. For ~400 objects → 120k iterations. Fine.

Terrain height:
```js
function terrainY(x,z){
  const {i,dist} = nearestTrack(x,z);
  const py = pts[i].y;
  if (dist <= HW+1.3) return py;
  const t = Math.min(1,(dist-(HW+1.3))/50);
  return py + (-2 - py)*t;
}
```

Trees: generate candidates in a box of ±320 around origin, skip if dist < 13 from the track. Place ~200.

Hmm, but the interior of the track will get lots of trees which might block the camera view of other karts. That's fine and looks nice.

Also trees shouldn't be placed where the road is (handled by dist check) or off the terrain plane. Fine.

Tree: trunk CylinderGeometry(0.35,0.45,3,6) brown; foliage: two cones. For instancing, I need separate InstancedMesh per geometry part, each with its own matrices. Fine — three instanced meshes with the same per-tree transform (with the foliage offset baked into the geometry? No — the instance matrix applies to all). Use different geometries with pre-translated vertices: foliage geometry translated up by 4, etc. Yes: `geo.translate(0,4,0)`.

Let me create:
- trunkGeo = CylinderGeometry(0.35,0.5,3.5,6); translate(0,1.75,0)
- foliageGeo1 = ConeGeometry(2.4, 4.5, 7); translate(0, 4.6, 0)
- foliageGeo2 = ConeGeometry(1.8, 3.5, 7); translate(0, 6.8, 0)

All three instanced meshes share the same matrices (position, rotation around Y, scale).

Rocks: InstancedMesh of IcosahedronGeometry(1,0) with random scale/rotation, gray.

Grandstand near the start line: a box + a sloped top? Just a box with a striped material and small "crowd" boxes maybe. Keep it simple: 3 grandstands placed along the outside of the start straight, each a box 30 wide, 6 tall, 12 deep, with a striped red/white material via vertex colors? Just use two materials: a gray base and a colored top. Let's do a Group: a base box (30,4,12) gray, plus 3 rows of "seats" boxes in different colors. Simple but effective. Or use a canvas texture with dots for a crowd. Let's do a canvas crowd texture: random colored dots on a dark background. That's cheap and reads as a crowd. Apply to the front face of the stand. Good idea.

Actually simpler: the grandstand box with a crowd texture on all sides. Fine.

Also add a few "advert" boards along the track (thin boxes with bright colors) — the scenery decoration.

Let's do: 20 advertising panels at lateral ±(HW+3) around the track, random colors, 6 wide, 1.8 tall.

Maybe skip to keep the code manageable. I'll add a few simple ones.

Now, start/finish gantry: two posts at ±(HW+1.5), 7 tall, plus a box beam across the top with a checkered texture.

Where to place: at sample index 0, oriented by the tangent.

Now, the checkered start line on the road: a plane at sample 0, 14 x 2.5, rotated to lie flat, with a checker texture.

Rotation: use a mesh with rotation.x = -π/2 (lying flat), and rotation.z? To orient it, set the mesh's quaternion using the basis: I can use a Group with the same basis approach, or simply set rotation.y = yaw where yaw = atan2(T.x, T.z). Then a plane rotated -π/2 around X lies in the XZ plane with its local +Y (up in texture space) mapping to -Z? Let's not overthink: create the plane geometry in the XZ plane directly: PlaneGeometry is in XY. Rotate -π/2 about X → it lies in XZ with the plane's local +Y → world -Z... Actually rotating -π/2 around X: Y→ -Z? Let's compute: rotation around X by -π/2: (x,y,z) → (x, y cos(-90) - z sin(-90), y sin(-90) + z cos(-90)) = (x, z, -y). So a point (0,1,0) → (0,0,-1). So the plane's +Y goes to world -Z. Fine, it's a texture; orientation barely matters.

Then I set the mesh's rotation.y = yaw, and rotation order matters. Use a parent group with rotation.y = yaw, and the child plane with rotation.x = -π/2. Clean.

yaw = Math.atan2(T.x, T.z). For the group's +Z to align with T: rotating around Y by yaw takes +Z to (sin yaw, 0, cos yaw) = T ✓.

OK.

Now let's write the kart creation and the race.

I also want the karts to look decent. Let me define makeKart(index, color, helmetColor) returning {group, wheels:[{pivot, spin}], ...}.

Karts scale: length 3.6, width 2.0. Road width 14. Good.

Now, the code. Let me write it out.

```js
// ---------- Karts
const KART_COLORS = [0xe63946, 0x2f7ef2, 0xffcf33, 0x35c46a, 0xa855f7, 0xff8b3d];
const KART_NAMES = ['Rex','Blaze','Kiwi','Nitro','Volt','Dash'];
```

makeKart:
```js
function makeKart(color, helmet){
  const g = new THREE.Group();
  const bodyMat = new THREE.MeshStandardMaterial({color, roughness:0.45, metalness:0.25});
  const darkMat = new THREE.MeshStandardMaterial({color:0x23242b, roughness:0.8});
  const suitMat = new THREE.MeshStandardMaterial({color, roughness:0.8});
  const helmMat = new THREE.MeshStandardMaterial({color:helmet, roughness:0.35, metalness:0.2});
  const skinMat = new THREE.MeshStandardMaterial({color:0xf1c39a, roughness:0.9});
  const glassMat = new THREE.MeshStandardMaterial({color:0x223344, roughness:0.2, metalness:0.6});

  // main chassis
  const ch = new THREE.Mesh(new THREE.BoxGeometry(1.9, 0.5, 3.2), bodyMat);
  ch.position.y = 0.62; g.add(ch);
  // nose cone
  const nose = new THREE.Mesh(new THREE.BoxGeometry(1.2,0.34,1.1), bodyMat);
  nose.position.set(0,0.55,1.95); g.add(nose);
  // front wing
  const wing = new THREE.Mesh(new THREE.BoxGeometry(2.2,0.12,0.6), darkMat);
  wing.position.set(0,0.42,2.5); g.add(wing);
  // side pods
  for (const s of [-1,1]) {
    const pod = new THREE.Mesh(new THREE.BoxGeometry(0.55,0.42,1.7), bodyMat);
    pod.position.set(s*1.05, 0.62, -0.15); g.add(pod);
  }
  // seat
  const seat = new THREE.Mesh(new THREE.BoxGeometry(0.9,0.7,0.35), darkMat);
  seat.position.set(0,1.0,-0.5); g.add(seat);
  // engine block
  const eng = new THREE.Mesh(new THREE.BoxGeometry(1.1,0.5,0.6), darkMat);
  eng.position.set(0,0.85,-1.5); g.add(eng);
  // driver
  const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.32,0.4,0.75,10), suitMat);
  torso.position.set(0,1.25,-0.35); g.add(torso);
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.33,14,12), helmMat);
  head.position.set(0,1.78,-0.3); g.add(head);
  const visor = new THREE.Mesh(new THREE.SphereGeometry(0.34,14,12, Math.PI*0.15, Math.PI*0.7, Math.PI*0.35, Math.PI*0.3), glassMat);
  ...
```
The visor with partial sphere args is fiddly. Simpler: a small box in front of the head. Let's do a slightly flattened sphere segment... I'll just put a dark box at the front of the head: `new THREE.BoxGeometry(0.42,0.16,0.1)` positioned at (0,1.82,0.02). Good enough.

Arms: two small cylinders angled toward the wheel. Optional, add small boxes.

Wheels: radius 0.46, width 0.36, black with a light gray rim (a cylinder inside slightly smaller? skip).

```js
const wheels = [];
for (const [sx, sz] of [[-1,1],[1,1],[-1,-1],[1,-1]]) {
  const pivot = new THREE.Group();
  pivot.position.set(sx*1.0, 0.46, sz*1.15);
  const spin = new THREE.Group();
  const wm = new THREE.Mesh(new THREE.CylinderGeometry(0.46,0.46,0.36,16), darkMat);
  wm.rotation.z = Math.PI/2;
  spin.add(wm);
  // hub
  const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.22,0.22,0.38,10), new THREE.MeshStandardMaterial({color:0xdddddd, metalness:0.7, roughness:0.3}));
  hub.rotation.z = Math.PI/2; spin.add(hub);
  pivot.add(spin);
  g.add(pivot);
  wheels.push({pivot, spin, front: sz>0});
}
```
Set castShadow on the meshes.

Now the kart object:

```js
class Kart {
  constructor(i){
    this.i = i;
    this.mesh = makeKart(KART_COLORS[i], KART_HELMETS[i]);
    scene.add(this.mesh.group);
    ...
  }
}
```
I'll just make it a plain object with functions, or a class. Class is fine.

Let me write the full class:

```js
class Kart {
  constructor(i){
    this.i = i;
    const m = makeKart(KART_COLORS[i], KART_COLORS[(i+3)%6]);
    this.group = m.group; this.wheels = m.wheels;
    scene.add(this.group);
    const row = Math.floor(i/2), col = i%2;
    this.s = (L - 8 - row*9) % L;
    this.x = col===0 ? -3.2 : 3.2;
    this.speed = 0;
    this.lap = 0;
    this.prevS = this.s;
    this.skill = 0.96 + Math.random()*0.08;
    this.lineBias = (i%2===0? 1 : -1) * (0.5 + Math.random()*1.2);
    this.steer = 0;
    this.spin = 0;
    this.slip = 0;
    this.roll = 0;
    this.drift = 0;
    this.finished = false;
    this.finishTime = 0;
    this.place = i+1;
    this.forward = new THREE.Vector3(0,0,1);
    this.pos = new THREE.Vector3();
    this.dustTimer = 0;
  }
  ...
}
```

Wait: grid positions must be behind the start line, so s = L - 8 - row*9. With row 0 (i=0,1) at L-8, row 1 at L-17, row 2 at L-26. Good.

Progress = (this.lap - 1)*L + this.s. At the start, lap=0 → progress = -L + (L-8) = -8. Good.

Now the update method.

```js
update(dt, karts, state){
  const L = TRACK_LEN;
  const idxF = (this.s / L) * N;
  const i0 = Math.floor(idxF) % N;
  const i1 = (i0+1)%N;
  const f = idxF - Math.floor(idxF);
  ...
}
```

For target speed: use a lookahead over samples:
```js
let want = MAXSPEED;
for (let j = 0; j < 60; j += 4) {
  const k = (i0 + j) % N;
  want = Math.min(want, SPEED_AT[k]);
}
```
Hmm, SPEED_AT is precomputed per sample as MAXSPEED*factor. Taking min over the lookahead gives braking distance awareness: but the kart starts braking only when the corner is within the window (~60 samples ≈ 60*1 = 60 units at ds≈1). With braking from 62 to 30 at brake=70/s, that takes 0.45s, covering ~20 units. So a 60-unit lookahead is plenty.

Let me make the lookahead distance-adaptive: look ahead `speed * 1.2` units. Convert to samples: jmax = speed*1.2/ds.

Let me do:
```js
const lookSamples = Math.floor((this.speed * 1.3) / ds);
let want = MAXSPEED * this.skill;
for (let j=0;j<=lookSamples;j+=3){
  const k=(i0+j)%N;
  const need = SPEED_AT[k];
  // allow more speed if the corner is far
  want = Math.min(want, need + j*0.05);  // hmm
}
```
Simpler: want = min over the window of SPEED_AT, then multiply by skill. Fine.

Then apply the rubber band.

Then lateral:

```js
const kk = curv[i0];
let xWant = raceOff[i0] + this.lineBias;
// avoidance
for (const o of karts){
  if (o===this) continue;
  const gap = mod(o.s - this.s, L);
  if (gap > 0 && gap < 18){
    const dx = this.x - o.x;
    if (Math.abs(dx) < 3.6){
      const side = (o.x > 0.5) ? -1 : (o.x < -0.5 ? 1 : (this.lineBias>0?1:-1));
      xWant = o.x + side * 4.2;
      if (gap < 7) want *= 0.9;
    }
  }
}
xWant = clamp(xWant, -5.6, 5.6);
```

Hmm, `side` computation: if the opponent is at x=3 (right side), we want to pass on the left → our x should be less than theirs → xWant = o.x - 4.2 → side = -1. Yes matches.

Then:
```js
const dxWant = xWant - this.x;
const maxRate = 10;
const step = clamp(dxWant, -maxRate*dt, maxRate*dt);
this.x += step;
const latVel = step/dt;
```
Hmm, using step/dt is noisy. Let's store this.latVel = smoothed.

Drift: 
```js
const cornerForce = Math.abs(kk) * this.speed;
this.drift = clamp(cornerForce*0.4 + Math.abs(latVel)*0.05, 0, 1);
```
Let's tune later; roughly |kk|~0.02, speed ~50 → 1.0*0.4 = 0.4. Plus lateral velocity up to 10 → 0.5. So drift ~0.6 in corners. Good.

slip = -Math.sign(kk) * this.drift * 0.3 (only when |kk| is significant).

Actually the sign should be based on kk for cornering, but also on the lateral movement direction. Keep it simple: slip = -sign(kk)*drift*0.28.

Wheel spin: this.spin -= this.speed*dt/0.46.

Steer: this.steerTarget = clamp(-kk*14 - latVel*0.03, -0.45, 0.45)? Hmm sign: latVel positive means moving toward +x (physical right). The kart should steer toward the right → negative rotation (as established, +Y rotation moves the wheel's forward toward the kart's local +X which is the physical left). So steer = -kk*14 - latVel*0.05. Hmm, latVel is in physical right units per second, up to 10, ×0.05 = 0.5 — too much. Use 0.03.

Let's just do steer = clamp(-kk*18 - latVel*0.03, -0.5, 0.5), smoothed.

Now s update and lap detection:
```js
this.prevS = this.s;
this.s += this.speed*dt;
if (this.s >= L){ this.s -= L; this.lap++; ... }
```
Also handle the s wrap when computing gaps using mod().

Wait — but the karts start at s≈L-8 and the update this.s += speed*dt will exceed L quickly → lap becomes 1. Good.

Now, engine/regen. Fine.

Now the visual update:

```js
updateMesh(dt){
  const L = TRACK_LEN;
  const idxF = mod(this.s,L)/L*N;
  ...
  const p = new THREE.Vector3().lerpVectors(pts[i0], pts[i1], f);
  const r = new THREE.Vector3().lerpVectors(rights[i0], rights[i1], f).normalize();
  const t = new THREE.Vector3().lerpVectors(tans[i0], tans[i1], f).normalize();
  p.addScaledVector(r, this.x);
  this.pos.copy(p); this.forward.copy(t);
  // basis
  const xk = new THREE.Vector3().crossVectors(UP, t).normalize();
  const upk = new THREE.Vector3().crossVectors(t, xk).normalize();
  const fwd = t.clone();
  // slip rotation about upk
  const q = new THREE.Quaternion().setFromAxisAngle(upk, this.slip);
  xk.applyQuaternion(q); fwd.applyQuaternion(q);
  // roll about fwd
  const q2 = new THREE.Quaternion().setFromAxisAngle(fwd, this.roll);
  xk.applyQuaternion(q2); upk.applyQuaternion(q2);
  const m = new THREE.Matrix4().makeBasis(xk, upk, fwd);
  this.group.quaternion.setFromRotationMatrix(m);
  this.group.position.copy(p);
  ...
}
```
Note: fwd after slip is used for lookAt etc. But `this.forward` should probably be the velocity direction (t) for the camera. Use t for the camera. Fine.

Wheels:
```js
for (const w of this.wheels){
  w.spin.rotation.x = this.spin;
  if (w.front) w.pivot.rotation.y = this.steer;
}
```

Now dust particles: spawn from the rear wheels when drift > 0.3.

```js
if (this.drift > 0.25 && this.speed > 20){
  this.dustTimer -= dt;
  if (this.dustTimer <= 0){
    this.dustTimer = 0.02;
    // spawn 2 particles at rear wheels
    const back = this.pos.clone().addScaledVector(this.forward, -1.2);
    const side = new THREE.Vector3().crossVectors(UP, this.forward).normalize();
    for (const s of [-1,1]){
      const p = back.clone().addScaledVector(side, s*0.95);
      p.y += 0.25;
      spawnParticle(p, vel, size, life, color);
    }
  }
}
```
Velocity: backward relative to the kart + up + random, magnitude ~ speed*0.3.

Particle color: tan/gray (0.75,0.72,0.65) for dust.

OK.

Now, the global particle system:

```js
const MAXP = 1200;
const pPos = new Float32Array(MAXP*3);
const pVel = new Float32Array(MAXP*3);
const pCol = new Float32Array(MAXP*3);
const pSize = new Float32Array(MAXP);
const pAlpha = new Float32Array(MAXP);
const pLife = new Float32Array(MAXP);
const pMaxLife = new Float32Array(MAXP);
let pCursor = 0;
// init all to dead
for (let i=0;i<MAXP;i++){ pPos[i*3+1] = -1000; pAlpha[i]=0; }
```
Geometry with attributes position, color, size, alpha. Update needsUpdate on the position, alpha, and size attributes each frame.

The shader uses `size` and `alpha` attributes.

Update:
```js
for (let i=0;i<MAXP;i++){
  if (pLife[i] <= 0) continue;
  pLife[i] -= dt;
  const i3 = i*3;
  pPos[i3] += pVel[i3]*dt;
  pPos[i3+1] += pVel[i3+1]*dt;
  pPos[i3+2] += pVel[i3+2]*dt;
  pVel[i3+1] -= 3*dt;
  pVel[i3] *= (1-1.5*dt); ...
  const lt = Math.max(0, pLife[i]/pMaxLife[i]);
  pAlpha[i] = lt*0.5;
  pSize[i] += dt*2;
  if (pLife[i] <= 0) { pAlpha[i]=0; pPos[i3+1]=-1000; }
}
```
Fine.

Now, HUD.

```html
<div id="ui">
  <div class="panel" id="standings">
    <div class="title">POSITIONS</div>
    <div id="list"></div>
  </div>
  <div class="panel" id="lapBox">
    <div class="lap">LAP <span id="lapNum">1</span>/<span id="lapTot">3</span></div>
    <div class="sub" id="raceTime">0:00</div>
  </div>
  <div id="countdown"></div>
  <div id="banner"></div>
</div>
```

Update the list every frame? Rebuilding DOM every frame with 6 rows is OK but let's do every 0.15s.

I'll create the rows once and reorder them via CSS order or by re-appending. Simplest: keep an array of row elements and set `list.appendChild(row)` in the sorted order each update. That's cheap enough at 6 rows, but doing it every frame causes layout thrash. Do it every 0.2s.

Actually, set `style.order` — but flex ordering with `display:flex; flex-direction:column` supports order. Let's use order. Even simpler: keep the array sorted and set row.style.order = rank. Good.

Row content: `<span class="pos">1</span><span class="chip" style="background:#..."></span><span class="name">Rex</span>` plus a lap indicator maybe.

Now, the countdown: show "3","2","1","GO!" with CSS animations (scale + fade). I'll set the text and restart a CSS animation by toggling a class.

Let's write:
```js
function showCountdown(txt, cls){
  const el = document.getElementById('countdown');
  el.textContent = txt;
  el.className = '';
  void el.offsetWidth;
  el.className = cls; // triggers animation
}
```
With CSS keyframes for scale-in and fade-out.

Race state machine:

```js
let state = 'countdown'; // 'racing','finished'
let stateTimer = 0;
const TOTAL_LAPS = 3;
let raceTime = 0;
let countdownStep = -1;
```

Countdown: durations: 0.8s of "3" prep... Let's do:
- t in [0, 1.0): show "3"
- [1.0, 2.0): "2"
- [2.0, 3.0): "1"
- [3.0, 4.2): "GO!" then start racing at t=3.0.

So stateTimer counts up; when stateTimer crosses 3.0 → state = 'racing'.

During the countdown, the karts sit on the grid with speed 0 but with a revving shake.

On 'racing', raceTime += dt.

Finish: when kart.lap > TOTAL_LAPS → finished. Record finish order.

When all karts have finished (or after the leader finishes + 6s), state = 'finished', show the results, and after 6s reset everything.

Reset: re-init kart positions, laps, standings, camera mode, state = 'countdown'.

Let's now consider: the requirement says the race lasts at least two laps. With 3 laps it's fine.

Lap time estimate: L ≈ 850, average speed ~45 → 19s per lap. 3 laps = 57s. Too long for the 30s window? The key elements (countdown, racing, overtakes, camera cuts, HUD updates) all appear in the first 30s. The finish is not essential within the window, but a race that's still going at 30s is fine — "lasts at least two laps" is satisfied trivially.

Hmm, but I'd like the whole arc visible. Let's speed it up: MAXSPEED = 75, lap ~14-16s, 2 laps in ~30s. Let's set TOTAL_LAPS = 2 and MAXSPEED = 78 with corner speeds. Average maybe 55 → lap ~15s. Race = ~30s. Then the loop restarts. That fits the 30s window nicely: countdown (3s) + 2 laps (~30s) — a bit over, but the loop restarts.

Let's go with TOTAL_LAPS = 3 but faster karts... no. Let's do 2 laps. "lasts at least two laps" — exactly 2 laps is fine. But then the race ends right around 30s. Good, and then it loops.

Hmm, but with 2 laps, the "lap counter" shows 1/2 and 2/2. Fine.

Let's make MAXSPEED = 80, and corner speed factors 0.5-1.0. Average maybe 60. Lap = 850/60 = 14s. 2 laps = 28s + 3s countdown + restart = ~31s. 

Actually let me reconsider the scale: with MAXSPEED 80 and corners, karts move fast. Camera FOV 65. It'll look exciting. OK.

Let's set ds: N=900, L≈850 → ds≈0.94.

Now let's write the final code carefully.

One concern: `curve.getPointAt(u)` for a closed CatmullRomCurve3 — is that supported? getPointAt calls getUtoTmapping → getLengths, which works for closed curves. Yes.

Let me now write everything.

Also need `renderer.setAnimationLoop` or requestAnimationFrame with a clock.

Delta time clamped to 0.05.

Let me write the code.

```js
import * as THREE from 'three';

// ---------------------------------------------------------------- setup
const W = () => innerWidth, H = () => innerHeight;
const renderer = new THREE.WebGLRenderer({antialias:true, powerPreference:'high-performance'});
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0xa9c9e8, 260, 780);
```
Hmm, ACES tone mapping with a bright sky might wash out. Let's use it but keep the exposure at 1.0. Or skip tone mapping. I'll skip it for predictable colors. Actually ACES makes things look nicer. Let's use `THREE.ACESFilmicToneMapping` with exposure 1.1 and slightly boost light intensities. Hmm, color management in r186: `THREE.ColorManagement.enabled` is true by default and outputColorSpace is sRGB. Colors set via hex are converted to linear. Fine.

I'll keep it simple without tone mapping.

Let me write the full file now. I'll be thorough.

Camera near plane 0.5, far 2000.

Sky sphere radius 1200, fog far 780 → far objects fade to fog color. The ground plane extends 1600 → edges will fog out. Good.

Let me be careful with the `pts` and `rights` arrays being Vector3 objects.

Writing now.

```js
const SCALE = 0.7;
const CTRL = [
 [0,2,-200],[110,8,-190],[190,12,-110],[175,10,-20],[210,6,60],[170,2,130],
 [90,1,175],[0,4,150],[-80,9,185],[-165,12,140],[-205,8,60],[-175,4,-20],
 [-200,6,-110],[-120,10,-180],[-50,6,-205]
].map(a=>new THREE.Vector3(a[0]*SCALE, a[1]*SCALE, a[2]*SCALE));
```
Hmm, if I scale y by 0.7 too, the hills are up to 8.4. Good.

Curve:
```js
const CURVE = new THREE.CatmullRomCurve3(CTRL, true, 'catmullrom', 0.5);
const N = 900;
const TOTAL = CURVE.getLength();
const DS = TOTAL / N;
const pts = [], tans = [], rights = [];
for (let i=0;i<N;i++){
  const u = i/N;
  const p = CURVE.getPointAt(u);
  const t = CURVE.getTangentAt(u).normalize();
  pts.push(p); tans.push(t);
  rights.push(new THREE.Vector3().crossVectors(t, UP).normalize());
}
```
Note: getTangentAt returns a normalized tangent.

Curvature:
```js
const curv = new Float32Array(N);
for (let i=0;i<N;i++){
  const a = tans[i], b = tans[(i+1)%N];
  const dT = new THREE.Vector3().subVectors(b,a);
  curv[i] = dT.dot(rights[i]) / DS;
}
```
Smooth 3 times with a [1,2,3,2,1] kernel.

```js
function smoothArr(arr, passes){
  const n = arr.length;
  for (let p=0;p<passes;p++){
    const out = new Float32Array(n);
    for (let i=0;i<n;i++){
      out[i] = (arr[(i-2+n)%n] + 2*arr[(i-1+n)%n] + 3*arr[i] + 2*arr[(i+1)%n] + arr[(i+2)%n]) / 9;
    }
    arr.set(out);
  }
}
```

Race line:
```js
const raceOff = new Float32Array(N);
for (let i=0;i<N;i++) raceOff[i] = clamp(curv[i]*170, -5, 5);
smoothArr(raceOff, 8);
```
Hmm, smoothing with the 1-2-3-2-1 kernel over 8 passes gives a spread of ~8 units. Should be OK for a racing line.

Wait, but smoothing the racing offset over corners will reduce its amplitude a bit. Fine.

Speed map:
```js
const MAXSPEED = 80;
const speedAt = new Float32Array(N);
for (let i=0;i<N;i++){
  let mk = 0;
  for (let j=0;j<50;j++) mk = Math.max(mk, Math.abs(curv[(i+j)%N]));
  speedAt[i] = MAXSPEED * clamp(1 - mk*13, 0.42, 1.0);
}
```
At mk = 0.02 → 1-0.26 = 0.74 → 59. Good.

Now, the kart lookahead uses speedAt over the window.

Let's write the meshes.

I'll write the road/kerb/grass with the helper.

Actually, one issue: the kerb raises the outer edge by 0.16, but the karts drive at road level, so their wheels would appear to sink into the kerb when at |x| near 7. We clamp x to ±5.6, so they never reach the kerb. Good.

The grass strip starts at HW+1.3 (i.e., 8.3) and slopes down. Between the road edge (7) and 8.3 is the kerb. OK.

Now writing the actual full code. Let me be systematic.

I'll write it in one go, then review.

```js
// ---- Road
const roadGeo = new THREE.BufferGeometry();
{
  const pos = [], uv = [], idx = [];
  const HW = 7;
  for (let i=0;i<=N;i++){
    const k = i%N;
    const p = pts[k], r = rights[k];
    pos.push(p.x - r.x*HW, p.y + 0.0, p.z - r.z*HW);
    pos.push(p.x + r.x*HW, p.y + 0.0, p.z + r.z*HW);
    const v = (i/N) * (TOTAL/10);
    uv.push(0, v, 1, v);
  }
  for (let i=0;i<N;i++){
    const a=i*2, b=i*2+1, c=i*2+2, d=i*2+3;
    idx.push(a,b,c, b,d,c);
  }
  roadGeo.setAttribute('position', new THREE.Float32BufferAttribute(pos,3));
  roadGeo.setAttribute('uv', new THREE.Float32BufferAttribute(uv,2));
  roadGeo.setIndex(idx);
  roadGeo.computeVertexNormals();
}
```
Check the winding: a = left(i) = p - r*HW. Wait, I wrote `p.x - r.x*HW` first, so the first vertex is at -HW along r = the physical left. And b = +HW = the physical right. Earlier I determined the correct winding is (a,b,c) with a=left, b=right, c=left(i+1) → normal up. ✓ And (b,d,c) ✓.

UV v: TOTAL/10 ≈ 85 repeats. With a 256px texture repeating 85 times over the track... each repeat covers 10 units. Fine.

Material: MeshStandardMaterial with map, roughness 0.95.

Now the kerbs. For side ±1.

```js
function buildKerb(side){
  const pos=[], col=[], idx=[];
  const o0 = 7.0, o1 = 8.3;
  for (let i=0;i<=N;i++){
    const k=i%N, p=pts[k], r=rights[k];
    const y0 = side>0 ? 0.02 : 0.02;
    pos.push(p.x + r.x*side*o0, p.y+0.02, p.z + r.z*side*o0);
    pos.push(p.x + r.x*side*o1, p.y+0.16, p.z + r.z*side*o1);
    const c = (i%2===0) ? RED : WHITE;
    col.push(c.r,c.g,c.b, c.r,c.g,c.b);
  }
  for (let i=0;i<N;i++){
    const a=i*2,b=i*2+1,c=i*2+2,d=i*2+3;
    if (side>0) idx.push(a,c,b, b,c,d);
    else idx.push(a,b,c, b,d,c);
  }
  ...
}
```
Hmm wait, for side>0, o0=7 is the inner edge, o1=8.3 is the outer edge. And for side<0, the offsets are -7 and -8.3 → inner is -7, outer is -8.3. In the loop, vertex 0 uses o0*side = -7 = inner ✓, vertex 1 uses o1*side = -8.3 = outer ✓. Good.

But hold on: for the right side, the winding (a,c,b) where a=A_i (inner), c=A_{i+1} (inner next), b=B_i (outer). Earlier I verified (a,c,b) gives up for the right side ✓. And (b,c,d) ✓.

Wait, earlier I wrote for "side>0: indices.push(a,c,b, b,c,d)" — yes matches.

And for the left: (a,b,c, b,d,c) ✓.

Grass: for each side, from o0=8.3 to o1=60, with y from p.y-0.1 to a blended absolute -2.

Actually let's compute y1 = lerp(p.y-0.1, -2, 1) = -2 for the outer, but for high sections that's a big drop over 52 units — fine.

But there's an issue: if p.y is high (8), the outer edge at -2 gives a steep slope of 10/52 = 0.19 — fine.

For the low sections p.y=0 → the outer is -2, slope 2/52 — fine.

Grass color: use a texture with UVs. Let's give UVs u = 0/1 and v = i/N * 40.

Material: MeshLambertMaterial with map. Or Standard. Use MeshLambertMaterial for cheapness. Actually shadows: Lambert supports receiveShadow. OK.

Now the ground plane: PlaneGeometry(2400,2400), rotateX(-π/2), y=-2.05, grass material with a big repeat.

Now scenery.

```js
function nearestIdx(x,z){
  let best=0, bd=1e18;
  for (let i=0;i<N;i+=3){
    const dx=pts[i].x-x, dz=pts[i].z-z;
    const d=dx*dx+dz*dz;
    if (d<bd){bd=d;best=i;}
  }
  return {i:best, d:Math.sqrt(bd)};
}
function terrainY(x,z){
  const {i,d} = nearestIdx(x,z);
  const py = pts[i].y;
  if (d <= 8.3) return py;
  const t = Math.min(1,(d-8.3)/52);
  return py + (-2 - py)*t;
}
```

Trees: 
```js
const treeMats = [];
for (let n=0;n<260;n++){
  const x = (Math.random()-0.5)*640;
  const z = (Math.random()-0.5)*640;
  const {d} = nearestIdx(x,z);
  if (d < 14) continue;
  const y = terrainY(x,z);
  ...
}
```
Note: terrainY calls nearestIdx again — a bit wasteful but fine at load time.

Collect matrices, then create InstancedMesh with count = number of trees.

I'll gather into an array and then build.

Rocks similar.

Grandstands: place at track indices near the start (index ~0 and ~40) on the outer side.

Advertising boards: place at intervals along the track, e.g. every 90 samples, alternating sides, at offset ±(HW+3.5), a box 8 x 1.6 x 0.4, with a bright color. Rotate to align with the tangent. That adds nice trackside detail.

Let's do ~16 boards.

Building each as a separate mesh is fine (16 meshes).

Use a group with rotation.y = yaw.

OK.

Now the start gantry: at index 0.

Post geometry: BoxGeometry(0.6, 8, 0.6) at (±(HW+1.2), 4, 0) relative to the track point, rotated by yaw. Beam: BoxGeometry(2*(HW+1.2), 1.2, 0.8) at y=8.

Add a checkered banner texture on the beam.

Let's write:
```js
{
  const k = 0;
  const p = pts[k], t = tans[k];
  const yaw = Math.atan2(t.x, t.z);
  const g = new THREE.Group();
  g.position.copy(p);
  g.rotation.y = yaw;
  // posts at local x = ±(HW+1.2), z=0
  ...
}
```
Since the group's local +Z = the tangent, the local X = ... For yaw rotation, the local X maps to (cos yaw, 0, -sin yaw). And the track's right vector = cross(t, up) = (t.z, 0, -t.x)... let's check: t = (sin y, 0, cos y). cross(t, up) = t × (0,1,0) = (t.y*0 - t.z*1, t.z*0 - t.x*0, t.x*1 - t.y*0) = (-t.z, 0, t.x) = (-cos y, 0, sin y). And the local X after rotating by yaw is (cos y, 0, -sin y) = -that. So the local X = -track right = the track's left. Consistent with what I found earlier. So placing a post at local x = +8 puts it 8 units to the track's left. Doesn't matter, symmetric.

OK.

Now writing the Kart class.

Then the race controller.

Let me now also handle the finish: record the finish order in an array.

```js
let finishOrder = [];
function onKartFinish(kart){
  kart.finished = true;
  kart.finishTime = raceTime;
  finishOrder.push(kart);
}
```
When kart.lap > TOTAL_LAPS and !finished → finish.

Race ends when finishOrder.length === 6 or (finishOrder.length>0 && raceTime - finishOrder[0].finishTime > 8).

Then show "FINISH" banner and after 5s restart.

Now camera modes. Let me define:

```js
const cam = { mode:'grid', timer:0, look:new THREE.Vector3(), pos:new THREE.Vector3() };
```

At race start (state='countdown'), camera mode = 'grid': position at a nice spot near the grid looking at the karts. Compute from the start line: position = startPos + right*22 + up*8, look at the average kart position.

On GO, switch to 'chase'.

In 'chase' mode: follow the leader.

Every so often, cut to 'trackside'.

Let's write updateCamera(dt):

```js
function updateCamera(dt){
  const leader = karts[raceOrder[0]] || karts[0];
  cam.timer -= dt;
  if (state === 'countdown'){
    // grid shot
    const p = pts[0], t = tans[0], r = rights[0];
    const camPos = p.clone().addScaledVector(r, 26).addScaledVector(t, -14);
    camPos.y += 10;
    camera.position.lerp(camPos, 1-Math.exp(-3*dt));
    const look = karts[2].pos.clone().lerp(karts[5].pos, 0.4);
    look.y += 1;
    cam.look.lerp(look, 1-Math.exp(-5*dt));
    camera.lookAt(cam.look);
    return;
  }
  if (cam.timer <= 0){
    if (cam.mode === 'chase'){ cam.mode='side'; cam.timer = 3.0 + Math.random()*1.5; pickSideCam(leader); }
    else { cam.mode='chase'; cam.timer = 5.5 + Math.random()*3.5; }
  }
  if (cam.mode === 'chase'){ ... } else { ... }
}
```
Careful: cam.timer starts at 6 and mode='chase'.

Wait, on the transition to racing, we need cam.mode='chase' and cam.timer set.

pickSideCam: choose a sample index ahead of the leader: idx = (leaderSample + 50 + rnd*130) % N. Position = pts[idx] + rights[idx]*(±(13+rnd*10)) + y + (3+rnd*5). Store in cam.sidePos.

Look at the leader's position each frame (with some damping for smoothness).

Also, the side camera should look at the leader but slightly ahead — fine.

Add a "cut" feel: when switching, just snap the camera position. With lookAt smoothing it'll be a hard cut but that's what we want.

Now, FOV: in chase mode, fov = 62 + speed*0.12 → at speed 80, 71.6. Update projection matrix when it changes.

OK, writing the final code.

One more consideration: the karts' `pos` must be initialized before the first camera update. The constructor sets pos via updateMesh(0). Let's call kart.updateVisual(0) after construction... but the constructor needs pts etc., which are defined before. The Kart class is defined after the track. Fine.

Let me write the final code now, and double-check the details.

Also I should handle window resize.

Let me write out the whole thing.

For the standings list, I need kart names. Let's use: 'REX','BLAZE','KIWI','NITRO','VOLT','DASH'.

Also add a lap indicator per kart in the list? Just position.

Write the code:

```js
const KARTS = [];
for (let i=0;i<6;i++) KARTS.push(new Kart(i));
```

Race order computation:
```js
function computeOrder(){
  const arr = KARTS.slice().sort((a,b)=> progress(b) - progress(a));
  return arr;
}
```
progress(k) = k.finished ? (1e6 - k.finishTime) : ((k.lap-1)*TOTAL + k.s);
Hmm, finished karts should stay ahead. Using 1e6 - finishTime makes earlier finishers larger. But an unfinished kart's progress is at most (2)*TOTAL + TOTAL ≈ 2500. So 1e6 dominates ✓. But among finished karts, smaller finishTime → larger score ✓.

Careful: k.lap can be up to TOTAL_LAPS+1 = 3, so progress up to 3*850 = 2550. OK.

Hmm, when k.lap = 3 (finished at 2 laps... wait). Let's recompute: TOTAL_LAPS=2. Kart crosses the line at the start → lap=1. Crosses again after 1 lap → lap=2 (on lap 2). Crosses again at the end of lap 2 → lap=3 > 2 → finished. Progress just before finishing = (2-1)*850 + 849 = 1699. After finishing, since we use 1e6 - time, fine.

So the display lap = min(lap, TOTAL_LAPS) but if not crossed yet, lap=0 → show 1. Let's set displayLap = clamp(kart.lap, 1, TOTAL_LAPS).

Hmm, at the start, lap=0 → display 1 ✓. After the first crossing, lap=1 → display 1 ✓. During lap 2, lap=2 → display 2 ✓. 

Wait, that's wrong: after crossing the line the first time (at race start), lap=1, and they're on lap 1 ✓. After completing lap 1, lap=2, and they're on lap 2 ✓. Good.

And the race leader's lap display for the HUD: use the leader's lap.

OK good.

Now writing everything for real.

For the DOM updates, cache elements.

Let me write the code in full:

Also: during the countdown, karts should be stationary but revving. In the update, if state==='countdown', set speed=0 and skip movement, but still update the visual (with a small shake).

I'll add a `revving` shake to the kart group's position y.

Now writing.

```js
class Kart {
  constructor(i){...}
  update(dt){...}
  updateVisual(dt){...}
}
```

Order per frame:
1. dt
2. if state==='racing' → for each kart: kart.update(dt) (AI + movement)
   else if countdown → hold.
3. collisions
4. for each kart: kart.updateVisual(dt)
5. particles update
6. order + HUD
7. camera
8. render

For collisions I need the s and x of each kart, and to apply positional corrections before updateVisual.

Let me write the collision pass:
```js
for (let a=0;a<6;a++) for (let b=a+1;b<6;b++){
  const A=KARTS[a], B=KARTS[b];
  const gap = mod(B.s - A.s, TOTAL);
  const gap2 = mod(A.s - B.s, TOTAL);
  const ds = Math.min(gap, gap2);
  if (ds > 4) continue;
  const dx = B.x - A.x;
  if (Math.abs(dx) > 2.6) continue;
  const push = (2.6 - Math.abs(dx)) * 0.5 * Math.sign(dx || 1);
  A.x -= push*0.5; B.x += push*0.5;
  // also slow the trailing one slightly
  ...
}
```
Careful: if dx is 0, sign gives 0 → use `Math.sign(dx)||1`. And use a small push. Fine.

Also clamp x to ±5.8.

Alright, let me write the final code. I'll write it out completely now.

Additional detail: the kart's `pos` and `forward` are used by the camera before the first updateVisual. In the constructor, I'll call `this.updateVisual(0)`.

Also note: in `updateVisual`, dividing by dt when dt=0 → NaN for latVel. Handle: if dt>0.

Let me store latVel in update(dt) instead.

Final code:

I'll write `updateVisual(dt)` to only set transforms.

Let me write.

```js
updateVisual(dt){
  const fi = mod(this.s, TOTAL)/TOTAL*N;
  const i0 = Math.floor(fi)%N, i1=(i0+1)%N, f = fi - Math.floor(fi);
  const p = _v1.lerpVectors(pts[i0], pts[i1], f);
  const r = _v2.lerpVectors(rights[i0], rights[i1], f).normalize();
  const t = _v3.lerpVectors(tans[i0], tans[i1], f).normalize();
  p.addScaledVector(r, this.x);
  this.pos.copy(p);
  this.forward.copy(t);
  ...
}
```
Using shared temp vectors is fine since we copy.

But careful: `_v1.lerpVectors(...)` returns _v1, then p.addScaledVector modifies it. Fine.

Then the basis:
```js
const xk = _v4.crossVectors(UP, t).normalize();
const upk = _v5.crossVectors(t, xk).normalize();
const fwd = _v6.copy(t);
const q1 = _q1.setFromAxisAngle(upk, this.slip);
xk.applyQuaternion(q1); fwd.applyQuaternion(q1);
const q2 = _q2.setFromAxisAngle(fwd, this.roll);
xk.applyQuaternion(q2); upk.applyQuaternion(q2);
_m1.makeBasis(xk, upk, fwd);
this.group.quaternion.setFromRotationMatrix(_m1);
```
Hmm: rotating upk around fwd after already rotating xk — apply q2 to xk and upk. Since q2's axis is fwd (unchanged by q2), it's consistent. ✓

Roll sign: let's set roll = clamp(curv*100 * (speed/MAXSPEED), -0.18, 0.18) — leaning into the corner. Doesn't matter much.

Wait, we should also smooth slip and roll.

Position: this.group.position.copy(p) plus a small bounce: y += 0.02*Math.sin(t*30) at speed. Optional.

OK, writing the final now. Let me produce the file.

Also for the wheels' spin, the sign: spin += speed/0.46*dt, set w.spin.rotation.x = -this.spin (or +). Whatever.

Let me write out all the code now in final form.

One more: `renderer.setAnimationLoop(animate)`.

Also the dust particle spawn should also happen when off-track (not applicable) — fine.

For "skid particles", I'll also add a dark smoke color for hard drifts... just one color is fine, maybe darker when drift is high. Let's vary the color slightly.

Writing the particle spawn function:

```js
function spawnParticle(px,py,pz, vx,vy,vz, size, life, r,g,b){
  const i = pCursor; pCursor = (pCursor+1)%MAXP;
  const i3 = i*3;
  pPos[i3]=px; pPos[i3+1]=py; pPos[i3+2]=pz;
  pVel[i3]=vx; pVel[i3+1]=vy; pVel[i3+2]=vz;
  pCol[i3]=r; pCol[i3+1]=g; pCol[i3+2]=b;
  pSize[i]=size; pAlpha[i]=0.55; pLife[i]=life; pMaxLife[i]=life;
}
```
Wait: pAlpha gets overwritten in the update loop by lt*0.55. Actually I set pAlpha each frame from life. Let me just set pAlpha in the update: alpha = (life/maxLife)*0.6.

But new particles need an initial alpha — set in the update before rendering. Since the update runs after the spawn, it's fine. Just ensure pAlpha is set in the update for all alive particles.

OK.

Now write it all.

Let me also make sure the attributes' `needsUpdate` is set for position, alpha, size, color each frame. Color only changes when spawning, but setting it every frame is fine (it's a small buffer). Actually for 1200 particles, setting needsUpdate on 4 attributes each frame uploads 1200*3*4*4 bytes ≈ 57KB/frame. Fine.

Now, writing!

Also, `pSize` should be in world units for the shader formula. Let's use size ~0.8 → at 15 units away: 0.8 * 300/15 = 16px. Good.

Final answer time. Let me write the complete HTML.

I need to double check the `makeBasis` handedness for the kart once more with actual numbers. t = (0,0,1) (heading +Z). 
xk = cross(UP, t) = (0,1,0)×(0,0,1) = (1*1-0*0, 0*0-0*1, 0*0-1*0) = (1,0,0).
upk = cross(t, xk) = (0,0,1)×(1,0,0) = (0*0-1*0, 1*1-0*0, 0-0) = (0,1,0). ✓
Basis (X=(1,0,0), Y=(0,1,0), Z=(0,0,1)) — identity, right-handed ✓.

Great.

Now the wheels: the model has wheels at local x=±1, z=+1.15 (front). Since local X = world X here and the track's "right" is -X, the front wheels are at +Z ✓ (forward).

Everything checks.

Let me write the driver steering wheel? Skip.

Writing the final code.

For the HUD standings rows, I'll build them once:

```js
const listEl = document.getElementById('list');
const rows = KARTS.map((k,i)=>{
  const d = document.createElement('div');
  d.className='row';
  d.innerHTML = `<span class="pos"></span><span class="chip" style="background:#${KART_COLORS[i].toString(16).padStart(6,'0')}"></span><span class="name">${KART_NAMES[i]}</span>`;
  listEl.appendChild(d);
  return d;
});
```
Careful: KARTS is populated after the Kart class is defined; the DOM rows must be created after KARTS exists. Fine.

Update:
```js
function updateHUD(){
  const order = raceOrder;
  for (let i=0;i<order.length;i++){
    const k = order[i];
    const row = rows[k.i];
    row.style.order = i;
    row.querySelector('.pos').textContent = (i+1);
    row.classList.toggle('lead', i===0);
  }
  lapNumEl.textContent = clamp(order[0].lap,1,TOTAL_LAPS);
  ...
}
```
With `#list{display:flex;flex-direction:column}` the order property works.

OK writing now. Also the finish banner text.

Time formatting: mm:ss.

Let me write it.

Also I should ensure that during the countdown the HUD shows the grid order. raceOrder computed from progress — works.

Let me finalize.

One more risk: `curve.getPointAt` for u=0..1 with 900 samples; the closed curve. Should be fine.

Potential issue: CatmullRomCurve3 `getLength()` and `getPointAt` require the arc-length LUT; fine.

Writing the final answer now.

For scenery, I'll also add clouds: a few flattened spheres high up with MeshBasicMaterial white, fog:false? They're inside the fog range if at y=120 and distance 400 → fogged. Fine, that's OK, they'll blend. Let's set fog false on the cloud material and use a slightly transparent white. Actually clouds at distance >780 would fully fog out. Let's place them at y=150 with a radius of 30, and set material.fog = false so they stay visible. Fine.

Let me write.

Also, I want to double check `SPEED_AT` lookahead with `this.speed`: `const look = Math.floor(this.speed * 1.1 / DS);` At speed 80, DS≈0.94 → look ≈ 93 samples ≈ 88 units. That's a long lookahead causing early braking; that's fine and safe.

Actually it might be too conservative: they'd brake for corners 88 units ahead. The min over that window means they slow down way before the corner. Let's use a distance-based weighting instead: for each lookahead sample j (distance d = j*DS), the allowed speed there is speedAt[k] and we require v² <= v_corner² + 2*a*d (braking distance). So the current allowed speed = sqrt(speedAt[k]² + 2*brakeDecel*d). With brakeDecel = 35: at d=50, adding sqrt(900+3500)=66 vs speedAt=30 → 66. So the constraint only binds when close. 

So: want = min over j of sqrt(speedAt[k]² + 2*35*j*DS). Nice and physical.

So:
```js
let want = MAXSPEED * this.skill;
const step = 4;
for (let j=0;j<120;j+=step){
  const k = (i0+j)%N;
  const d = j*DS;
  const v = Math.sqrt(speedAt[k]*speedAt[k] + 70*d);  // 2*35
  if (v < want) want = v;
}
```
With speedAt around 30-80 and d up to 113, at d=0 v=speedAt. So effectively want ≈ min over the next ~110 units of the braking-limited speed. Good.

But careful: if the kart is slow (speed 30) and there's a fast section ahead, `want` would be high and it accelerates — good.

The kart's actual speed approaches `want` with accel/brake limits. Since want is computed from the ideal path, this works.

Now, the corner speed itself should also account for the kart's skill. Multiply at the end.

OK, writing.

Also the rubber banding: 
```js
const leaderProg = progress(raceOrder[0]);
const myProg = progress(this);
const gap = leaderProg - myProg;
let boost = 1;
if (gap > 40) boost = 1 + Math.min(0.18, gap/2000);
this.want *= boost;
```
Hmm, progress of the leader at the start... at the start, all karts are within 30 units. Fine.

Let's use `gap` measured in track units. gap/2000 with a cap of 0.15.

Good.

Let's write the final code!

Also, I should not let the karts exceed MAXSPEED. Clamp want to MAXSPEED*1.15.

Final code writing now. I'll be careful with syntax.

Let me write the whole HTML.

For the standings row height, use fixed sizes.

I'll now produce the final answer.

One last thing — the countdown display. I'll use a div with a CSS animation triggered by changing the text and restarting the animation via a class toggle.

```css
#countdown{position:absolute;left:50%;top:42%;transform:translate(-50%,-50%);font-size:150px;font-weight:900;color:#fff;text-shadow:0 6px 30px rgba(0,0,0,.6), 0 0 60px rgba(255,220,100,.5);opacity:0;}
#countdown.show{animation:pop .95s ease-out forwards;}
@keyframes pop{0%{opacity:0;transform:translate(-50%,-50%) scale(2.2);}20%{opacity:1;transform:translate(-50%,-50%) scale(1);}75%{opacity:1;}100%{opacity:0;transform:translate(-50%,-50%) scale(.85);}}
```
And restart the animation by removing/re-adding the class with a reflow.

GO! in a different color (green).

OK. Writing!

For the results banner: `#banner` centered, showing "RACE FINISHED" and the top 3. Simple.

Final code:

I also need to reset everything properly on restart: reset kart s, x, lap, speed, finished; finishOrder = []; state='countdown'; stateTimer=0; raceTime=0; camera mode='grid'; countdown index reset.

Let me write a `resetRace()`.

Writing now for real.

Also: the kart's `prevS` isn't really needed since I use `s += ...; if (s>=TOTAL) { s-=TOTAL; lap++ }`. That's the only wrap. Since speed*dt is small (< 4 units), it can't skip. Good.

But s could exceed TOTAL by more than once? No.

Also, the starting s values are near TOTAL, and the first update will push them over TOTAL → lap becomes 1 → they've "crossed" the line. Correct.

Now writing.

Wait: at the start, the karts are at s = TOTAL-8 etc. On the first update (racing), s += speed*dt. But during the countdown, speed=0, so s stays. Good.

Let me write it.

Also `mod` for gap calculations.

OK writing the final.

I'll include a small speed readout? Not required. Skip.

Let me produce the file.