The user wants a complete, self-contained HTML file with a 3D Solar System using Three.js. Let me plan this carefully.

Requirements:
1. Sun glowing at center, emissive, with halo, lighting planets
2. 8 planets in correct order (Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, Neptune)
3. Relative sizes making sense (Jupiter largest, Mercury smallest)
4. Procedural textures on canvas:
   - Jupiter's bands
   - Earth's oceans and continents
   - Mars red
   - Others can be simpler
5. Saturn with rings
6. Moon orbiting Earth
7. Faint orbit lines
8. Planets orbiting at different speeds
9. Starfield background
10. Camera travels from planet to planet showing each close up with name on screen
11. Use requestAnimationFrame timestamp for animation time
12. Full-window canvas handling resize
13. Starts automatically, no interaction

Let me structure this:

- Use Three.js from import map (r186)
- Use an orthogonal or perspective camera
- Create scene, camera, renderer
- Create procedural textures using canvas
- Create sun with emissive material and glow (sprite or shader for halo)
- Create planets with orbit groups
- Add orbit lines
- Add starfield (Points or sprite)
- Animation loop with camera moving between planets
- UI overlay for planet names

Let me think about the camera tour:
- Define a sequence of camera targets (planets) and durations
- Use the total animation time to determine which segment we're in
- Smooth interpolation between targets (maybe using cubic bezier or ease in-out)

Planet data:
- Mercury: size 0.4 (relative to Earth = 1), distance ~10
- Venus: size 0.9, distance ~16
- Earth: size 1.0, distance ~22
- Mars: size 0.6, distance ~28
- Jupiter: size 3.0, distance ~40
- Saturn: size 2.5, distance ~52
- Uranus: size 1.5, distance ~64
- Neptune: size 1.4, distance ~76

Orbit speeds inversely proportional to distance (Kepler's law, simplified).

For textures, I'll create canvas-based textures:

1. **Jupiter bands**: horizontal stripes with slightly varying colors
2. **Earth**: blue oceans with green/brown continent shapes (drawn with random paths/blobs)
3. **Mars**: red/orange with darker regions
4. Others: simple gradients or noise

For the Sun:
- Mesh with basic/standard material emitting light
- Add point light at center
- Halo via sprite with radial gradient texture (canvas-generated)

Saturn's rings:
- RingGeometry with a canvas texture (radial gradient with transparency)

Orbit lines:
- LineLoop or LineSegments with circle geometry

Moon:
- Small sphere orbiting Earth

Starfield:
- Points with random positions on a large sphere

Camera tour logic:
- Wait for a short intro (maybe 3s on sun)
- Then cycle through planets: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, Neptune
- For each planet: zoom in, hold, then move to next
- Show planet name overlay during close-up

Let me code this properly. I need to be careful with:
- Canvas texture generation for each planet
- The glow/halo effect for the sun
- The camera interpolation

Let me think about the canvas textures:

For Jupiter bands:
```javascript
function createJupiterTexture() {
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 128;
    const ctx = canvas.getContext('2d');
    // Draw bands
    const colors = ['#c8a87c', '#a67c52', '#d4b896', '#8b5e3c', '#e0c9a6', '#9e7c5e'];
    // horizontal stripes
    for (let y = 0; y < 128; y++) {
        const bandH = 128 / 12;
        const band = Math.floor(y / bandH);
        ctx.fillStyle = colors[band % colors.length];
        ctx.fillRect(0, y, 256, 1);
    }
    // Add some noise/swirls
    const imgData = ctx.getImageData(0,0,256,128);
    for (let i=0; i<imgData.data.length; i+=4) {
        // add subtle noise
        const noise = (Math.random()-0.5)*20;
        imgData.data[i] += noise;
        imgData.data[i+1] += noise;
        imgData.data[i+2] += noise;
    }
    ctx.putImageData(imgData,0,0);
    return new THREE.CanvasTexture(canvas);
}
```

Actually, for smooth bands, I should draw gradient bands. Let me refine.

For Earth continents:
```javascript
function createEarthTexture() {
    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 256;
    const ctx = canvas.getContext('2d');
    // ocean
    ctx.fillStyle = '#1a66cc';
    ctx.fillRect(0,0,512,256);
    
    // draw continents as irregular shapes
    ctx.fillStyle = '#2d8a3e';
    // generate random landmasses
    for (let i=0; i<20; i++) {
        // draw random polygons
        const x = Math.random()*512;
        const y = Math.random()*256;
        const r = 20 + Math.random()*40;
        ctx.beginPath();
        ctx.ellipse(x, y, r, r*0.7, Math.random()*Math.PI, 0, 2*Math.PI);
        ctx.fill();
    }
    // add some ice caps
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, 512, 12);
    ctx.fillRect(0, 244, 512, 12);
    
    return new THREE.CanvasTexture(canvas);
}
```

Actually, the continents look too blobby. Let me use a more sophisticated algorithm: draw multiple small circles in clusters, or use a noise function. But to keep it self-contained and simple, I'll use a few random blobs with some distortion. It'll be recognizable enough on a small sphere.

For Mars:
```javascript
function createMarsTexture() {
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 128;
    const ctx = canvas.getContext('2d');
    // Base red
    ctx.fillStyle = '#c1440e';
    ctx.fillRect(0,0,256,128);
    // darker regions
    ctx.fillStyle = '#8a2f08';
    for (let i=0; i<10; i++) {
        const x = Math.random()*256;
        const y = Math.random()*128;
        const r = 10+Math.random()*30;
        ctx.beginPath();
        ctx.ellipse(x, y, r, r*0.6, Math.random()*Math.PI, 0, 2*Math.PI);
        ctx.fill();
    }
    // polar caps
    ctx.fillStyle = '#f0f0f0';
    ctx.fillRect(0, 0, 256, 8);
    ctx.fillRect(0, 120, 256, 8);
    
    return new THREE.CanvasTexture(canvas);
}
```

Sun glow:
```javascript
function createGlowSprite() {
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 256;
    const ctx = canvas.getContext('2d');
    const gradient = ctx.createRadialGradient(128,128,0,128,128,128);
    gradient.addColorStop(0, 'rgba(255,200,50,1)');
    gradient.addColorStop(0.5, 'rgba(255,150,0,0.5)');
    gradient.addColorStop(1, 'rgba(255,100,0,0)');
    ctx.fillStyle = gradient;
    ctx.fillRect(0,0,256,256);
    return new THREE.CanvasTexture(canvas);
}
```

Saturn's rings:
```javascript
function createRingTexture() {
    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 64;
    const ctx = canvas.getContext('2d');
    const gradient = ctx.createLinearGradient(0,0,512,0);
    const stops = [0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1];
    const colors = ['rgba(0,0,0,0)','rgba(180,160,140,0.2)','rgba(200,180,160,0.5)','rgba(160,140,120,0.3)','rgba(220,200,180,0.7)','rgba(150,130,110,0.4)','rgba(200,180,160,0.6)','rgba(170,150,130,0.3)','rgba(210,190,170,0.5)','rgba(180,160,140,0.2)','rgba(0,0,0,0)'];
    for (let i=0; i<stops.length; i++) {
        gradient.addColorStop(stops[i], colors[i]);
    }
    ctx.fillStyle = gradient;
    ctx.fillRect(0,0,512,64);
    return new THREE.CanvasTexture(canvas);
}
```

Actually, Rings are better done with RingGeometry and a canvas texture. Let me use the RingGeometry with a material that has transparent map.

For the starfield:
```javascript
function createStars() {
    const geometry = new THREE.BufferGeometry();
    const vertices = [];
    for (let i=0; i<5000; i++) {
        const r = 500 + Math.random()*500;
        const theta = Math.random()*Math.PI*2;
        const phi = Math.acos(2*Math.random()-1);
        vertices.push(r*Math.sin(phi)*Math.cos(theta));
        vertices.push(r*Math.sin(phi)*Math.sin(theta));
        vertices.push(r*Math.cos(phi));
    }
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    const material = new THREE.PointsMaterial({ color: 0xffffff, size: 0.5, sizeAttenuation: true });
    return new THREE.Points(geometry, material);
}
```

Camera tour logic:

I need to define a timeline. The user says "a camera that travels from planet to planet showing each one close up with its name on screen."

Sequence:
- Start at Sun for ~2s
- For each planet (Mercury through Neptune):
  - Travel to planet (2s)
  - Close-up view (2s)
  - Move to next

Total: 2 + 8*(2+2) = 34s, then maybe loop or hold.

Actually, a better approach: define camera positions as keyframes with times. Use a function to interpolate.

Let me define keyframes:
- At time 0: camera at (0, 60, 120) looking at origin (sun)
- At t=3: begin travelling to Mercury
- At t=5: arrive at Mercury, show name
- At t=8: begin travelling to Venus
- etc.

I'll use an array of objects:
```javascript
const timeline = [
    { planet: 'Sun', duration: 3 },
    { planet: 'Mercury', duration: 4 },
    { planet: 'Venus', duration: 4 },
    { planet: 'Earth', duration: 4 },
    { planet: 'Mars', duration: 4 },
    { planet: 'Jupiter', duration: 4 },
    { planet: 'Saturn', duration: 4 },
    { planet: 'Uranus', duration: 4 },
    { planet: 'Neptune', duration: 4 },
];
```

For each planet, get its world position. The camera should:
1. Move from current position to a point near the planet (offset by some distance)
2. While looking at the planet

The interpolation can be smooth using a cubic bezier or ease function.

Let me implement this with a timeline in seconds:

```javascript
function getCameraPosition(time) {
    // total timeline duration
    const durations = [3, 4, 4, 4, 4, 4, 4, 4, 4]; // 8 planets + sun
    const totalDuration = durations.reduce((a,b)=>a+b,0);
    const t = time % totalDuration;
    
    let accum = 0;
    let index = 0;
    for (let i=0; i<durations.length; i++) {
        if (t < accum + durations[i]) {
            index = i;
            break;
        }
        accum += durations[i];
    }
    
    const localT = (t - accum) / durations[index];
    // smoothstep
    const smoothT = smoothstep(localT);
    
    // Determine previous and next target
    // ...
}
```

This is getting complex. Let me simplify: Use a continuous time-based approach where each planet gets a segment, and the camera eases between the previous position and the next.

Actually, let me think of it differently. I'll define waypoints and interpolate.

I'll maintain a global clock. For each segment:
- Segment 0 (i=0): Sun, 3s
- Segment i (i=1..8): Planet i-1, 4s each

Within each segment:
- If i==0: camera positioned initially, just look at sun
- For i>=1: 
  - The first 40% of the segment: camera moves from previous planet to current planet
  - The last 60%: camera holds and orbits slightly

Wait, that doesn't work either because at the end of a segment we need to be ready to move to the next.

Let me use overlapping segments approach:
- Define a set of camera targets with times
- Each "target" is { position: Vector3, lookAt: Vector3, time: float }
- Use cubic bezier interpolation between waypoints

Let me define waypoints:
```javascript
const waypoints = [
    { pos: new THREE.Vector3(80, 30, 120), lookAt: new THREE.Vector3(0,0,0), time: 0 }, // intro
    { pos: new THREE.Vector3(10, 3, 12), lookAt: mercuryPos, time: 5 }, // mercury
    { pos: new THREE.Vector3(15, 5, 18), lookAt: venusPos, time: 9 },
    // etc.
];
```

But planet positions change over time since they orbit. So I need to compute their positions at the moment the camera arrives.

Hmm, this is getting complicated. Let me simplify:

**Simplified approach**: 
- Each planet has an angle: `angle = time * speed + offset`
- Position can be computed: `pos = (cos(angle)*radius, 0, sin(angle)*radius)`
- For the camera: I'll compute each planet's position at the **current global time**, and use that for both the planet mesh and the camera target.

Actually, since the animation is procedural and planets always move, I can compute a "nominal" position for each planet based on the global time. The camera will target the planet's current position.

For the camera path, I'll define keyframe times and interpolate between the positions of the planets at those times. But since planets are moving, I need to compute their positions at each frame for the camera target.

Let me do this:
- Planets orbit with angle = time * angularSpeed
- For camera: at any time t, determine which segment we're in
- Segment i is associated with planet i (with segment 0 being the Sun)
- Camera position: interpolation of a path that goes from planet's current position + offset

Actually, for a smooth cinematic tour, I'll do this:

```javascript
let currentPlanetIndex = 0;
let cameraTarget = new THREE.Vector3();
let cameraPos = new THREE.Vector3();
```

In the animation loop:
1. Compute current time in seconds
2. Determine segment based on time:
   - Segment 0 (0-2s): Sun, camera at (0, 50, 100) looking at (0,0,0)
   - Segment i (i=1..8): Planet i-1
3. For each segment, interpolate camera:

For the transition between planets:
- During the first 40% of a segment: ease from previous planet to current planet
- During the last 60%: stay near the planet (slight orbit)

But at segment boundaries, the camera needs to be at a nice position.

Let me use a different approach: define a continuous timeline array:

```javascript
const T = [];
// Each entry: { t, pos, lookAt, targetName }
// t = time in seconds when this waypoint is reached
// pos = camera position at that time
// lookAt = position camera looks at
```

For each planet excursion:
- Arrive time, depart time
- Position: some offset from planet

I'll compute the waypoints at startup (or dynamically as planet positions change).

Actually, let's just make it simple and robust:

**Original idea**: Use a slow continuous fly-through where the camera smoothly moves from planet to planet using sinusoidal position offsets.

Let me construct a "path" for the camera. For each planet, I'll compute a nice camera position near it: 
`cameraPos = planetPos + cameraOffset(angle)` where cameraOffset is approximately perpendicular to the radial direction.

Then I'll blend between these positions using smoothstep.

Let me actually implement a function:

```javascript
function computeCameraTargets(time) {
    // For each planet, compute its position at current time
    // Then return an array of { pos, lookAt, name }
}
```

And then the camera interpolates between these targets based on time.

OK let me just write the code. I'll define:
- 9 "stops" (Sun + 8 planets)
- Each stop has a duration (2s for sun, 3s for each planet)
- Camera moves from stop i to stop i+1 over the duration of stop i+1

The camera position for stop i is:
- Sun: (80, 30, 120)
- Planet i: planet.position + perpendicular offset * distanceFactor

Actually, let me use a proper global animation keyframe system:

```javascript
const keyframes = [];
// initialize keyframes with planet indices and durations
// each frame, compute the current keyframe segment
```

Let me just write something that works. I'll compute camera positions dynamically.

Simplest approach that is cinematic:

Each planet gets a specified time window:
- Sun: t=0 to 3
- Mercury: t=3 to 7
- Venus: t=7 to 11
- Earth: t=11 to 15
- Mars: t=15 to 19
- Jupiter: t=19 to 23
- Saturn: t=23 to 27
- Uranus: t=27 to 31
- Neptune: t=31 to 35

Then loop after 35s.

At each segment (e.g., Mercury segment 3-7):
- t=3: camera is positioned near the Sun (start point)
- t=3→5: camera travels to Mercury
- t=5→7: camera orbits/holds near Mercury

For the transition, I can use interpolated positions. Let me define it with a helper:

```javascript
function getPlanetPosition(planet, time) {
    const angle = time * planet.speed + planet.offset;
    return new THREE.Vector3(
        Math.cos(angle) * planet.distance,
        0,
        Math.sin(angle) * planet.distance
    );
}
```

For each segment:
- Compute the starting position (previous planet's position at segment start + offset)
- Compute the ending position (current planet's position + offset)
- Interpolate

OK let me think about this more carefully for the actual code.

I'll maintain a `clock` (or use the raf timestamp directly). Then in the animation loop:

```javascript
const elapsed = time * 0.001; // seconds
// determine segment
const segmentDuration = 5; // seconds per planet
const totalSegments = 9; // sun + 8 planets
const loopTime = totalSegments * segmentDuration;
const t = elapsed % loopTime;
const segment = Math.floor(t / segmentDuration);
const localT = (t % segmentDuration) / segmentDuration;
```

Now, for camera:
- `segment 0` = Sun visit
- `segment i` = planet i-1 visit

For the transition within a segment:
- 0→0.4: Travel from previous stop's camera position to current planet
- 0.4→1: Orbit/slight approach while looking at planet

But we need position of previous planet at the time we departed... this is getting complicated.

**Better approach**: Use a fixed camera path in polar coordinates. The camera will always look at a moving point (the target planet). As the target planet moves, the camera follows.

For each segment, I'll create a Hermite curve (using THREE.CubicBezierCurve3 or THREE.CatmullRomCurve3) that connects the previous camera position to the next camera position. The lookAt target will be the current planet's position.

Since planets move, I'll compute the start and end camera positions at the segment boundaries using the positions of the respective planets at those times.

Actually, let's simplify even further. Instead of worrying about the exact positions at exact times, I'll use the following:

For each segment `i` (0-indexed):
- Start time: `startTime[i]`
- End time: `startTime[i] + segmentDuration`
- Camera start position: `SEGMENT_START_POSITIONS[i]` (relative to planet i)
- Camera end position: `SEGMENT_END_POSITIONS[i]`

But because planets move, I'll define camera positions relative to the target planet's position. So at any time, camera position = targetPlanet.position + localOffset, where localOffset transitions from one value to another.

So for segment i:
- We're visiting planet i (with index 0 = Sun)
- The previous segment visited planet i-1
- At the start of segment i, localOffset = some value near planet i-1
- At the end of segment i, localOffset = some value near planet i
- The lookAt target is always planet i's current position

This way, the camera flies from a position near planet i-1 to a position near planet i.

The "localOffset" for each stop is a constant offset that gives a nice view. For example:
- Sun: (0, 30, 60)
- Mercury: (4, 2, 4)
- etc.

But these offsets are in world space and should rotate with the planet? No, just as fixed offsets in world coordinates relative to the planet's position.

Actually, here's a clean implementation:

```javascript
const segmentDuration = 4;
const numSegments = 9;
const totalTime = segmentDuration * numSegments;

function animate(time) {
    const t = time * 0.001;
    const loopT = t % totalTime;
    const seg = Math.floor(loopT / segmentDuration);
    const localT = (loopT % segmentDuration) / segmentDuration;
    
    // Ease in-out
    const smoothT = smoothstep(localT);
    
    // Current planet index (0=Sun, 1=Mercury...8=Neptune)
    const currentIndex = seg;
    const prevIndex = (seg - 1 + numSegments) % numSegments;
    
    // Get target planet positions
    const currentTarget = getTargetPosition(currentIndex, t);
    const prevTarget = getTargetPosition(prevIndex, t);
    
    // Camera offsets
    const currentOffset = getCameraOffset(currentIndex);
    const prevOffset = getCameraOffset(prevIndex);
    
    // Interpolate offsets
    const offset = new THREE.Vector3().lerpVectors(prevOffset, currentOffset, smoothT);
    const targetPos = new THREE.Vector3().lerpVectors(prevTarget, currentTarget, smoothT);
    
    // But wait, targetPos should be the current planet's position, not interpolated.
    // Hmm.
}
```

This is getting too complicated. Let me step back and use a simpler, battle-tested technique:

**Technique: Manual camera waypoints with an array.**

I'll precompute the "key" camera positions and lookAt positions for each phase, and then do a smooth interpolation between consecutive keyframes.

Since the planets move, I'll compute their positions at the moment each keyframe is active. I'll use the raf timestamp to calculate the planet positions. The keyframes are just stored in a way that references planet indices. Each keyframe has:
- `targetIndex`: which planet the camera looks at (0 = Sun, 1-8 = planets)
- `duration`: how long to take to get there (transition time)
- `hold`: how long to stay there
- `distance`: how far from the planet the camera should be
- `height`: the camera height relative to the planet

Let me define keyframes explicitly:

```javascript
const cameraPath = [
    { target: 0, distance: 60, height: 20, duration: 2, hold: 2 }, // Sun
    { target: 1, distance: 8, height: 3, duration: 3, hold: 2 }, // Mercury
    { target: 2, distance: 12, height: 4, duration: 3, hold: 2 }, // Venus
    { target: 3, distance: 14, height: 5, duration: 3, hold: 2 }, // Earth
    { target: 4, distance: 18, height: 6, duration: 3, hold: 2 }, // Mars
    { target: 5, distance: 40, height: 12, duration: 3, hold: 2 }, // Jupiter
    { target: 6, distance: 35, height: 10, duration: 3, hold: 2 }, // Saturn
    { target: 7, distance: 22, height: 7, duration: 3, hold: 2 }, // Uranus
    { target: 8, distance: 22, height: 7, duration: 3, hold: 2 }, // Neptune
    // loop
];
```

But I need to know how long each phase takes. Total duration = sum(duration + hold) = 2+2 + (3+2)*8 = 4 + 40 = 44s.

During a "duration" phase, the camera moves from the previous position to the new position. During "hold", it stays there.

But there's a problem: the planet is moving during both the transition and the hold. So if the camera looks at the planet's current position, the lookAt target moves smoothly. That's fine.

For the camera position during transition:
- Start position: current camera position
- End position: computed from target planet's position + offset
Actually, I'll define camera position relative to target: `camPos = targetPos + offset(direction)`. But during transition, target is changing.

OK, let me simplify radically:

**Final simple approach**:

For each segment `i`, during the "approach" phase (first part of segment), the camera starts at the position it ended the previous segment (which is near the previous planet) and moves to the current planet. During the "hold" phase, it stays at the same relative offset.

But rather than using actual previous camera position, I can use the previous planet's "camera offset" as a waypoint.

Actually, you know what? Let's just use a list of [time, camera position, lookAt target] keyframes. At each time, we find the surrounding keyframes and interpolate. I'll generate these keyframes dynamically based on the planet positions at any given time.

Since the planets orbit, their positions change. But if I record the time of each keyframe, I can compute the planet positions at that time. Then during playback, the keyframe positions are fixed. This means the camera path is fixed relative to the planets' positions at keyframe times.

For a smooth result, I want the camera to smoothly track the moving planet during the hold. So during the hold phase, I should compute the lookAt target as the current position of the planet, not the fixed keyframe position.

OK here's my final plan:

I'll implement a camera controller with this logic:

```javascript
let animTime = 0;

// Timeline segments
const segments = [
    { index: 0, name: 'Sun', duration: 5 }, // 2s approach + 3s hold
    { index: 1, name: 'Mercury', duration: 5 },
    { index: 2, name: 'Venus', duration: 5 },
    { index: 3, name: 'Earth', duration: 5 },
    { index: 4, name: 'Mars', duration: 5 },
    { index: 5, name: 'Jupiter', duration: 5 },
    { index: 6, name: 'Saturn', duration: 5 },
    { index: 7, name: 'Uranus', duration: 5 },
    { index: 8, name: 'Neptune', duration: 5 },
];
```

For each segment, `duration = approachTime + holdTime`. Let's say approach=2.0s, hold=3.0s.

At any time `t`:
1. Find which segment we're in (cycling)
2. localT = t - segmentStart
3. If localT < approachTime: we're in approach. Find the previous segment's planet target for the "from" position. But we don't have the previous camera position stored... 

OK you know what, let me use a simpler approach: just define camera positions explicitly as an array of keyframes, and use the actual time to interpolate between them.

I'll define 9 keyframes (one for each visit):

```javascript
const keyframes = [
    { target: 0, offset: new THREE.Vector3(60, 20, 60), name: 'THE SUN', time: 0 },
    { target: 1, offset: new THREE.Vector3(6, 2, 6), name: 'MERCURY', time: 6 },
    { target: 2, offset: new THREE.Vector3(10, 3, 10), name: 'VENUS', time: 12 },
    { target: 3, offset: new THREE.Vector3(12, 4, 12), name: 'EARTH', time: 18 },
    { target: 4, offset: new THREE.Vector3(16, 5, 16), name: 'MARS', time: 24 },
    { target: 5, offset: new THREE.Vector3(35, 10, 35), name: 'JUPITER', time: 30 },
    { target: 6, offset: new THREE.Vector3(30, 8, 30), name: 'SATURN', time: 36 },
    { target: 7, offset: new THREE.Vector3(18, 5, 18), name: 'URANUS', time: 42 },
    { target: 8, offset: new THREE.Vector3(18, 5, 18), name: 'NEPTUNE', time: 48 },
];
```

Here `target` is the index into the planets array (0=Sun, 1=Mercury...). `offset` is `cameraPos = planetPos + offset`, where planetPos is computed at the current time. Actually, to avoid the camera lagging, I should make the offset such that the camera looks at the planet.

But `offset` alone doesn't determine the lookAt - the camera should look at the planet.

For each keyframe at time `T`, I'll compute the planet's position at time `T` (the global time when the keyframe is "reached"). Then `cameraPos = planetPosAtKeyframeTime + offset`. The lookAt target is `planetPosAtKeyframeTime`.

During rendering at time `t`, I find the two surrounding keyframes and interpolate:
- position: lerp(cameraPos[prev], cameraPos[next], smoothstep)
- lookAt: lerp(planetPosAtKeyframeTime[prev], planetPosAtKeyframeTime[next], smoothstep)

But this means the camera won't exactly track the moving planet during the hold - it will lag. To fix, during the hold we can set the lookAt to the current position of the target planet.

This is getting too detailed. Let me simplify to one of these options:

**Option A**: Make the camera target directly the planet's current position. For the camera position, use a simple smoothly varying offset that is a function of time and the target planet's current position.

**Option B**: Use a fixed global path with keyframes at computed world positions (not tied to planets). This looks less dynamic but is simpler.

I'll go with a hybrid: 
- At any time t, determine the current segment (which planet to visit)
- Compute a blend parameter `u` between 0 and 1 for that segment
- Camera position = smoothly interpolate between the current planet's position + offset_in and the current planet's position + offset_out
- Camera looks at the current planet's position

So the camera always looks at the current planet. Its position is offset from the planet. As the segment progresses, the offset smoothly changes from an "arrival" offset to a "hold" offset.

Specifically, for segment `i`:
- It starts when a blend parameter goes from 0 to 1
- At segment start (u=0), offset = `prevOffset` (arriving from far away)
- At u=0.4, offset = `viewOffset[i]` (nice close-up)
- At u=0.5 to 0.8, offset holds at `viewOffset[i]`
- At u=0.8 to 1.0, offset shifts slightly to `orbitOffset[i]` for a dynamic feel

Actually, this adds complexity. Let's keep it simpler:

For each planet, define a single `viewOffset`. This is the position of the camera relative to the planet. We want the camera to always be at `planetPos + viewOffset` but with a smooth transition between offsets when switching planets.

We can achieve this by defining a time-based "offset interpolator" that uses smoothstep. But the offset is relative to a planet, and the planet is moving. So during transition from planet A to planet B, we interpolate both the offset and the planet:

```
cameraPos = lerp(planetA.pos + offsetA, planetB.pos + offsetB, smoothT)
```

And lookAt:
```
lookAt = lerp(planetA.pos, planetB.pos, smoothT)  // or just planetB.pos
```

Actually, lerping between two vectors where the endpoints are changing is fine - it creates a smooth curve.

Let me define a state machine:

```javascript
// At any given time, we have:
// - "from" planet index and "from" offset
// - "to" planet index and "to" offset
// - blend factor t (0-1)
```

When a segment starts, we know:
- fromIndex = previous planet
- toIndex = current planet
- t goes from 0 to 1 over the approach duration

Then:
```
cameraPos = lerp(planet[fromIndex].getPosition() + offsets[fromIndex],
                 planet[toIndex].getPosition() + offsets[toIndex],
                 ease(t))
lookAt = planet[toIndex].getPosition()
```

But at the end of the approach, we want to be exactly at the current planet's offset. Then during hold, the camera should track the current planet.

Actually, let's make it even simpler. During the entire segment, we set:
```
cameraPos = planet[currentIndex].getPosition() + currentOffset
```
where `currentOffset` is interpolated from `arrivalOffset` to `viewOffset` based on local time. So the camera approaches the planet along a path from a far offset to a close offset.

For the approach, the "arrivalOffset" could be the viewOffset of the previous planet, or simply a far-away distance. For example:
- At localT=0: offset = prevPlanet.viewOffset * 3 (or some large distance)
- At localT=1: offset = currentPlanet.viewOffset

This way, the camera flies from a point far away (linearly extrapolated from the previous planet's position) to the current planet. The path is smooth.

Hmm, but multiplying prevPlanet.viewOffset by 3 in world space may not make sense if prevPlanet is far away.

OK, I think the best approach is the very common one: **use a sequence of camera waypoints defined in terms of target positions (the planets).**

Let me just implement it with a simple interpolation and it'll look good enough.

Here's my final implementation plan:

1. Define 8 planets + Sun in an array, with orbital parameters.
2. Each planet has `getPosition(time)` method.
3. Define a timeline: each planet gets a time slot of 5s. Total 45s, then loop.
4. For each time:
   - Determine current segment (which planet is being visited)
   - localT = (t - segmentStart) / segmentDuration
   - The target planet is the current one.
   - Camera position: use the following formula:
     ```
     camPos = targetPlanetPos + offset
     ```
     where offset is a time-dependent smooth offset:
     - At localT=0: offset = fromOffset (a bit behind and far)
     - At localT=1: offset = viewOffset (a good close-up)
   - Use `smoothstep` to interpolate offset.
5. Camera looks at the target planet's current position.

The "fromOffset" at segment start can be:
- For the first segment (Sun): fromOffset = (40, 20, 40)
- For subsequent segments: fromOffset = previous planet's offset in world space? No, that's complex.
  Instead, just set fromOffset = (distance * 2, distance * 0.5, distance * 2) i.e., a far-away position relative to the target planet.

Actually, a nicer effect: the camera travels along a straight line from the previous planet's position to the current planet's position, staying far out. This gives a nice fly-through.

So:
```javascript
const startPos = planet[prevIndex].getPosition() + offsets[prevIndex];
const endPos = planet[currentIndex].getPosition() + offsets[currentIndex];
camPos = lerp(startPos, endPos, smoothT);
lookAt = lerp(planet[prevIndex].getPosition(), planet[currentIndex].getPosition(), smoothT);
```

But `smoothT` goes from 0 to 1 as the approach happens. During the hold:
```javascript
camPos = planet[currentIndex].getPosition() + offsets[currentIndex];
lookAt = planet[currentIndex].getPosition();
```

This way the camera always starts from the previous planet and flies to the current one.

Let me implement this properly.

Planet indices:
0: Sun
1: Mercury
2: Venus
3: Earth
4: Mars
5: Jupiter
6: Saturn
7: Uranus
8: Neptune

Offsets (per unit of planet size... actually just absolute offsets relative to planet position):
- Sun: (0, 50, 80) -- far away to fit the sun
- Mercury: (0, 3, 8)
- Venus: (0, 4, 10)
- Earth: (0, 5, 12)
- Mars: (0, 4, 12)
- Jupiter: (0, 25, 45)
- Saturn: (0, 20, 40)
- Uranus: (0, 12, 25)
- Neptune: (0, 12, 25)

But these offsets are in world coordinates. If the planet is far away, the camera will be at `planetPos + offset`. That's fine.

Actually, wait. If I compute `startPos` from the previous planet's offset but at the *current* time, the previous planet has moved. That's fine - it gives a nice match if the previous planet is still being rendered.

Let me define:
- `getPlanetPos(index, time)`: returns the position of planet at the given time.

```javascript
function getPlanetPos(index, time) {
    if (index === 0) return new THREE.Vector3(0,0,0);
    const p = planetData[index-1];
    const angle = time * p.speed + p.offset;
    return new THREE.Vector3(
        Math.cos(angle) * p.distance,
        0,
        Math.sin(angle) * p.distance
    );
}
```

For the Sun target, index=0, position is (0,0,0). For the Sun's "offset", we use a far offset so the camera is far away.

The timeline:
- Each segment has `duration = 6` seconds? Let me use 5.
- Segment 0 (Sun): 5s
- Segment 1 (Mercury): 5s
- ...
- Segment 8 (Neptune): 5s
- Total: 45s, loops.

Within a segment:
- `localT = (t - segmentStart) / duration`
- `smoothT = smoothstep(0, 1, min(localT/0.5, 1))` --- transition occurs during the first 50%? 
  
Actually, let me split the segment into two phases:
  - Phase 1 (approach): localT from 0 to 0.4 (2s) -- camera travels from prev planet to current planet
  - Phase 2 (hold): localT from 0.4 to 1.0 (3s) -- camera stays near current planet

For the approach phase, I need:
- `startT = segmentStart`
- `endT = segmentStart + 0.4 * duration`
- Interpolate camera position from `startPos` to `endPos`.
- `startPos = getPlanetPos(prevIndex, startT) + offset[prevIndex]`
- `endPos = getPlanetPos(currentIndex, endT) + offset[currentIndex]`
- Interpolation factor `u = (t - startT) / (endT - startT)`, smooth

For the hold phase:
- `cameraPos = getPlanetPos(currentIndex, t) + offset[currentIndex]`
- `lookAt = getPlanetPos(currentIndex, t)`

This is clean and should work.

But wait, for the Sun (segment 0), there's no previous planet. We start with the camera already at the Sun. So we can set the initial camera position to `getPlanetPos(0, 0) + offset[0]`.

The offset for the Sun should be large enough to see the sun entirely, e.g., (0, 30, 80).

Now let me define the offsets more carefully. The planets have the following orbital distances (I'll call them `radius` in the data):

```javascript
const planetData = [
    { name: 'Mercury', radius: 1.2, distance: 10, speed: 0.8, color: 0x8c7e6d, ... },
    { name: 'Venus', radius: 1.5, distance: 15, speed: 0.6, color: 0xe3c88e, ... },
    { name: 'Earth', radius: 1.6, distance: 20, speed: 0.5, color: 0x4a90d9, ... },
    { name: 'Mars', radius: 1.2, distance: 25, speed: 0.4, color: 0xc1440e, ... },
    { name: 'Jupiter', radius: 4.0, distance: 40, speed: 0.25, color: 0xd4a76a, ... },
    { name: 'Saturn', radius: 3.5, distance: 55, speed: 0.2, color: 0xe0b589, ... },
    { name: 'Uranus', radius: 2.0, distance: 70, speed: 0.15, color: 0x9be3e0, ... },
    { name: 'Neptune', radius: 2.0, distance: 85, speed: 0.1, color: 0x4a6de0, ... },
];
```

Wait, these distances are too small compared to real scale but good for visual. The order is correct.

The camera offsets should be relative to the planet's size:
- Sun: (0, 20, 50) - since sun has radius ~5
- Mercury: (0, 2, 5) - radius 1.2
- Venus: (0, 2.5, 6) - radius 1.5
- Earth: (0, 2.5, 6) - radius 1.6
- Mars: (0, 2, 5) - radius 1.2
- Jupiter: (0, 8, 18) - radius 4.0
- Saturn: (0, 7, 16) - radius 3.5
- Uranus: (0, 4, 9) - radius 2.0
- Neptune: (0, 4, 9) - radius 2.0

Actually, these should be adjusted so the planet fits in the frame. For a FOV of 60 degrees, the visible height at distance d is `2 * tan(30°) * d ≈ 1.1547 * d`. To see an object of radius r (diameter 2r), we need `d > 2r / 1.1547 ≈ 1.732 * r`. So `d` should be about `2.5 * r` to have some margin. So:
- Sun (r=5): d = 12.5, so (0, 5, 12) would work. Let me use (0, 5, 12).
- Mercury (r=1.2): d = 3, so (0, 1, 3)
- Venus (r=1.5): d = 3.75, so (0, 1.5, 4)
- Earth (r=1.6): d = 4, so (0, 1.5, 4)
- Mars (r=1.2): d = 3, so (0, 1, 3)
- Jupiter (r=4.0): d = 10, so (0, 4, 10)
- Saturn (r=3.5): d = 8.75, but rings extend further, so (0, 4, 12)
- Uranus (r=2.0): d = 5, so (0, 2, 5)
- Neptune (r=2.0): d = 5, so (0, 2, 5)

But the camera should also be elevated. The offset (0, 3, 6) would give distance sqrt(3^2+6^2)=6.7 from the planet, which is close to d. Good.

Actually, for a more cinematic view, I want the camera slightly above and at an angle.

Let me define the offsets as `(3, 2, 3)` relative to the planet:
- Sun: (10, 8, 20) // distance ~21, fov covers r=5 nicely
- Mercury: (1.5, 1, 3) // distance ~3.5
- Venus: (2, 1.5, 4) // distance ~4.7
- Earth: (2, 1.5, 4) // distance ~4.7
- Mars: (1.5, 1, 3) // distance ~3.5
- Jupiter: (5, 3, 10) // distance ~11.5
- Saturn: (4, 3, 10) // distance ~11.2
- Uranus: (2, 1.5, 5) // distance ~5.6
- Neptune: (2, 1.5, 5) // distance ~5.6

These will work.

Now, the camera should look at the target planet. So:
```javascript
camera.lookAt(planetPos)
```

During the approach phase, the lookAt should smoothly transition from the previous planet's position to the current planet's position. Actually, we can set lookAt to the current planet's position for the whole segment. It might look like a quick pan, which is fine.

Wait, during the approach, if we're flying from Mercury to Venus, the lookAt is suddenly at Venus... it might look odd because camera is near Mercury looking at Venus. Actually, that's OK - it's a common cinematic effect: "from Mercury, looking at Venus" then flying toward Venus turns the camera. As we approach, the planet gets bigger. This could look really cool.

But during the approach, the camera position is interpolated from `MercuryPos + offset[1]` to `VenusPos + offset[2]`. The lookAt is `VenusPos`. So at the start, the camera is near Mercury, looking at Venus. As it flies, it turns towards Venus. That's a nice effect.

Actually, let's keep it simple: lookAt = current planet's position (the one we're visiting). The transition will naturally look like a fly-by.

Let me code the segment logic now.

But wait, there's a problem: during approach, the camera position is a lerp between two world-space points that are far apart. The path crosses through the sun perhaps. That might be cool (flying past the sun). It should be fine.

Let me code this now.

Here's the actual code structure:

```javascript
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(60, window.innerWidth/window.innerHeight, 0.1, 2000);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);
```

Scene setup:
- Add stars, sun, planets, orbit lines.
- Add a light at sun position (pointLight)
- Add ambient light

Planet creation:
- Each planet is a mesh with a sphere geometry and a canvas texture.

Let me write a function to create textures.

For the Sun:
- Use MeshBasicMaterial (so it's self-lit) with emissive-like color? Actually, for glow, I'll add a Sprite with a radial gradient.

But the requirement says "emissive, with a halo". So either use:
1. `MeshBasicMaterial` (color = sun color) which is unlit and looks emissive, plus a sprite halo.
2. `MeshStandardMaterial` with `emissive` set and `emissiveMap`.

I'll go with MeshBasicMaterial for the Sun and add a point light at the center to light other planets.

Also add a glow sprite that always faces the camera.

Let me refine the texture functions:

**Create Sun texture:**
```javascript
function createSunTexture() {
    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 256;
    const ctx = canvas.getContext('2d');
    // orange-yellow gradient with noise
    const grad = ctx.createLinearGradient(0,0,0,256);
    grad.addColorStop(0, '#ffcc33');
    grad.addColorStop(0.5, '#ff9900');
    grad.addColorStop(1, '#ff6600');
    ctx.fillStyle = grad;
    ctx.fillRect(0,0,512,256);
    // Add some spots/granulation
    const img = ctx.getImageData(0,0,512,256);
    for (let i=0; i<img.data.length; i+=4) {
        const bright = (Math.random()-0.5)*40;
        img.data[i] += bright;
        img.data[i+1] += bright;
        img.data[i+2] += bright;
    }
    ctx.putImageData(img,0,0);
    return new THREE.CanvasTexture(canvas);
}
```

**Create Mercury texture:**
Greyish, cratered.

**Create Venus texture:**
Yellowish cloud layers.

**Create Earth texture:**
Blue + green continents.

**Create Mars texture:**
Red + dark patches.

**Create Jupiter texture:**
Bands.

**Create Saturn texture:**
Bands, similar to Jupiter but paler.

**Create Uranus texture:**
Smooth cyan.

**Create Neptune texture:**
Smooth blue.

Let me write a generic noise/detail generator.

Now, for the planet geometries: I'll use `SphereGeometry(radius, 32, 32)` for the sun and planets. For Saturn, add ring.

For orbit lines: `LineLoop` with 128 points in a circle.

For the Moon: small sphere (radius=0.3) orbiting Earth.

Let me write the full code now.

Actually, before that, let me think about the camera animation implementation one more time.

I'll define an array of "visits" with local time info:

```javascript
const visits = [
    { targetIndex: 0, startTime: 0, duration: 5 },
    { targetIndex: 1, startTime: 5, duration: 5 },
    ...
];
```

For each visit:
- `prevIndex`: the targetIndex of the previous visit (for the approach start)
- At the approach end (e.g., at startTime + 0.4*duration), camera should be at:
  `getPlanetPos(targetIndex, approachEndTime) + offset[targetIndex]`
- At the approach start, camera should be at:
  `getPlanetPos(prevIndex, approachStartTime) + offset[prevIndex]`

So during the approach:
```javascript
const approachDuration = 0.4 * duration;
const approachStart = startTime;
const approachEnd = startTime + approachDuration;
const u = (time - approachStart) / approachDuration;
const su = smoothstep(u);
const startPos = getPlanetPos(prevIndex, approachStart) + offset[prevIndex];
const endPos = getPlanetPos(targetIndex, approachEnd) + offset[targetIndex];
cameraPos = startPos.lerp(endPos, su);
cameraLookAt = getPlanetPos(targetIndex, time); // look toward target
```

During hold:
```javascript
cameraPos = getPlanetPos(targetIndex, time) + offset[targetIndex];
cameraLookAt = getPlanetPos(targetIndex, time);
```

Now, the issue with this is that `startPos` is computed at the *beginning* of the approach, and `endPos` is computed at the *end*. But if the previous planet is moving, then at the start of the approach, the camera is exactly at `getPlanetPos(prevIndex, approachStart) + offset[prevIndex]`. But at the end, it's at `getPlanetPos(targetIndex, approachEnd) + offset[targetIndex]`. This is fine.

But when we reach the hold phase, the camera position is `getPlanetPos(targetIndex, time) + offset[targetIndex]`, which at `time = approachEnd` is exactly `endPos`. So there's C0 continuity. Good.

During the approach, the camera lookAt is `getPlanetPos(targetIndex, time)` - so it smoothly moves with the target planet.

What about the lookAt during the approach? At the start, it's pointing to the target planet. But the camera is near the previous planet. So it might sweep. That's fine - it creates a nice pan.

Actually, I want to make sure the camera transition looks good. Let me set the lookAt to the current target planet's position at all times. This means the camera is always looking at the target planet, which is what we want.

OK, let me code it.

But wait, I also want a name display. I'll create an overlay div and update it based on the current segment.

Now, for the text display: show the planet name during its segment. I can have a div that fades in/out. I'll simply set `innerText` and toggle opacity.

Let me write the complete code now.

One thing to note: `THREE.Sprite` for the sun halo. The sprite material needs a texture with a radial gradient. I'll create a canvas texture for that.

Also, for the Sun's glow lighting effect: I'll add a `PointLight` at the sun's position. The intensity will be high. But to avoid the planets being too dark, I'll also add ambient light.

Since the sun is at the center and planets are close (distance 10-85), a point light with `decay` (in three.js r186, `decay` default is 2) might cause issues. I'll set `decay: 0` for the light and adjust intensity.

Actually, in three.js r155+, the lighting units changed. For a point light, intensity is in candela. I'll set `decay = 0` and `intensity = 3` or something. Let me test with a high value.

Alternatively, use `DirectionalLight` from the sun's position for each planet, but that's more complex. PointLight at sun with large intensity should work.

Let me set `pointLight.intensity = 2000` (because decay=2 and planets are at distance 10-85, light intensity received = 2000 / d^2. At d=20, it's 5, which is OK). Hmm, but with `decay: 0`, the intensity stays constant. Let me just set `decay: 0` and `intensity: 2` for simpler lighting.

Actually, let me use `MeshBasicMaterial` for planets? No, the requirement says "lighting the planets". So they should be lit by the sun. Use `MeshStandardMaterial` or `MeshPhongMaterial`.

I'll use `MeshStandardMaterial` with `roughness: 0.8` and the canvas texture as `map`. Add a `PointLight` at the sun with `decay: 0`, `intensity: 2.5`. Also add `AmbientLight(0x333333)` so the dark sides aren't fully black.

Wait, but if the sun is a MeshBasicMaterial, it won't cast light on itself, but it will be the light source. That's fine.

Let me now think about the camera offset for the sun. The sun's radius will be, say, 5. The offset should be about (10, 8, 25). That gives a distance of ~28, which shows the sun with some context.

OK, let me write the full code now. I'll be careful with the segment logic.

Here's the pseudo-code for the animation loop:

```javascript
const totalDuration = 5 * 9; // 45 seconds
let currentName = '';

function animate(timestamp) {
    requestAnimationFrame(animate);
    const time = timestamp * 0.001; // seconds

    // Update planet orbits
    updatePlanets(time);

    // Update moon orbit
    updateMoon(time);

    // Update camera
    updateCamera(time);

    // Update name overlay
    // ...

    renderer.render(scene, camera);
}

function updatePlanets(time) {
    planetData.forEach((data, i) => {
        const angle = time * data.speed + data.offset;
        data.mesh.position.set(
            Math.cos(angle) * data.distance,
            0,
            Math.sin(angle) * data.distance
        );
        data.mesh.rotation.y = time * data.spinSpeed;
    });
}
```

Let me define the orbit data with mesh etc.

For the camera:

```javascript
function updateCamera(time) {
    const loopTime = 9 * 5;
    const segDuration = 5;
    let t = time % loopTime;
    const segIndex = Math.floor(t / segDuration);
    const localT = (t % segDuration) / segDuration;
    
    const prevIndex = (segIndex - 1 + 9) % 9;
    const currIndex = segIndex;
    
    const approachDuration = 0.35; // fraction of segment
    const u = Math.min(localT / approachDuration, 1);
    const su = smoothstep(u);
    
    let camPos, camLookAt;
    
    if (u < 1) {
        // Approach - interpolate from prev planet position to current planet position
        const startTime = t*0 + Math.floor(time / loopTime) * loopTime + segIndex * segDuration; // hmm
```

I'm overcomplicating this. Since `time` can be arbitrarily large, I need to handle the loop carefully. For computing the approach start position, I need to know the *actual* world time at the start of the segment, not the looped time. Let me use the approach:

```javascript
const loopTime = 45;
let time = timestamp * 0.001;
let t = time % loopTime;
const segIndex = Math.floor(t / segDuration);
const localT = (t - segIndex * segDuration) / segDuration;
const segStartTime = time - (t - segIndex * segDuration);
```

Actually, `t` is already the looped time. Let me compute:
```javascript
let looped = time % loopTime;
const segIndex = Math.floor(looped / segDuration);
const localT = (looped - segIndex * segDuration) / segDuration;
const segStartTime = time - (looped - segIndex * segDuration);
```

Then:
```javascript
const approachDuration = Math.min(2.0, segDuration * 0.4); // seconds
const approachStartTime = segStartTime;
const approachEndTime = segStartTime + approachDuration;
const u = (time - approachStartTime) / approachDuration;
if (u < 1) {
    const prevSegIndex = (segIndex - 1 + 9) % 9;
    const startPos = getPlanetPos(prevSegIndex, approachStartTime).add(offsets[prevSegIndex]);
    const endPos = getPlanetPos(segIndex, approachEndTime).add(offsets[segIndex]);
    camPos = startPos.lerpVectors(startPos, endPos, smoothstep(u));
    camLookAt = getPlanetPos(segIndex, time);
} else {
    camPos = getPlanetPos(segIndex, time).add(offsets[segIndex]);
    camLookAt = getPlanetPos(segIndex, time);
}
```

But there's an issue: at segment boundaries, the camera must align with where the previous segment ended. The previous segment's hold position is computed at the *actual* time of the segment end. And the new segment's approach start position is computed at `approachStartTime` which is the *actual* time of the segment start. These are different because the previous planet has moved. So there will be a jump.

To avoid a jump, I can compute the startPos at the approachStartTime as the position where the previous camera actually would be at that moment: `getPlanetPos(prevSegIndex, approachStartTime) + offsets[prevSegIndex]` BUT the previous segment's hold kept the camera at `getPlanetPos(prevSegIndex, time) + offsets[prevSegIndex]` where `time` is the current time. So actually, if I set `startPos = getPlanetPos(prevSegIndex, approachStartTime) + offsets[prevSegIndex]`, and the previous frame's camera was at `getPlanetPos(prevSegIndex, time_prev) + offsets[prevSegIndex]`, as `time_prev -> approachStartTime`, they match. So there's no jump *if* at the moment of the segment transition, the camera is at `getPlanetPos(prevSegIndex, transitionTime) + offsets[prevSegIndex]`.

The problem is that the transition happens exactly at the segment boundary. At that moment, the previous segment was in hold status, setting `camPos = getPlanetPos(prevSegIndex, time) + offsets[prevSegIndex]`. The new segment's approach at u=0 sets `camPos = getPlanetPos(prevSegIndex, approachStartTime) + offsets[prevSegIndex]`. Since `time = approachStartTime` at the transition, these are equal. Good.

At the end of the approach, `camPos = getPlanetPos(currIndex, approachEndTime) + offsets[currIndex]`. Then the hold takes over, and at `time = approachEndTime`, they're equal. Good.

So the camera will be C0 continuous. There may be a velocity discontinuity (C1) if the two points are moving differently, but that's acceptable.

Actually, to make it even smoother, I can use a Catmull-Rom curve through the keyframe camera positions. But let's keep it simple.

However, there's a subtle bug: `getPlanetPos` for the previous segment during approach should use the previous planet's *current* position? Wait, no. The start position is fixed at the approachStartTime. But the camera position during the approach is `lerp(startPos, endPos, smoothstep(u))`. Since `endPos` is also fixed, the camera moves in a straight line from startPos to endPos. But the actual target planet is moving, so `camLookAt = getPlanetPos(currIndex, time)` will be a moving target. This is fine.

But during the approach, if the current planet moves, `endPos` was computed at `approachEndTime`. At the end of the approach, the camera is at a fixed point. But the current planet may have moved past that point. Then the hold phase sets `camPos = getPlanetPos(currIndex, time) + offsets[currIndex]`, which at `time = approachEndTime` is `endPos` by definition. So no jump.

OK, this should work.

Let me also consider: for segment 0 (Sun), the previous index is 8 (Neptune). That means during Sun's approach, the camera flies from Neptune to the Sun. That's a long flight but looks cool! At t=0, the camera is near Neptune, and over 2 seconds it flies to the Sun, then holds for 3 seconds. After 5 seconds, it starts flying to Mercury. This gives a good intro too.

Wait, but at the very beginning, at time=0, the camera will be at Neptune's position. That's fine; it's a nice opening.

Actually, for the first segment (Sun), I might want to start near the Sun rather than Neptune. Let me handle the first cycle specially: if `time < 0.01` AND we're at the very start, maybe the camera should already be at the Sun offset. But for simplicity, starting at Neptune and flying to the Sun is a cool intro. Actually, at time=0, the camera will be at `getPlanetPos(Neptune, 0) + offset[Neptune]`, which is far away including Neptune. Then over 2s, it flies to the Sun. That means the first view is Neptune? But the camera looks at the Sun, so from Neptune it looks at the Sun (a tiny dot). Then flies toward the Sun. That's actually a neat opening.

Let me set the Sun's offset to (0, 10, 30) so the Sun appears large when the camera arrives. Actually, for the Sun (radius=5), an offset of (0, 10, 30) gives distance ~31.6, which shows the sun at ~1/10 of screen height. For FOV 60, the sun would appear small. Let me use (0, 8, 20) giving distance ~21.5, sun diameter ~10, so it takes about half the screen height. Good.

Now for the name overlay: I'll update it based on `segIndex`. During the approach (u<1), should we show the target name immediately? Yes, it makes sense to show the name we're flying to.

Let me now write the code.

I'll also need to update the moon around Earth. The moon's position can be computed as Earth position + a small offset:
```javascript
const moonAngle = time * 5; // faster
moon.position.set(
    earthMesh.position.x + Math.cos(moonAngle) * 2.5,
    0,
    earthMesh.position.z + Math.sin(moonAngle) * 2.5
);
```

Now, for orbit lines, I'll create circle geometries:

```javascript
function createOrbitLine(radius) {
    const points = [];
    for (let i=0; i<=128; i++) {
        const angle = (i/128) * Math.PI * 2;
        points.push(new THREE.Vector3(Math.cos(angle)*radius, 0, Math.sin(angle)*radius));
    }
    const geo = new THREE.BufferGeometry().setFromPoints(points);
    const mat = new THREE.LineBasicMaterial({ color: 0xffffff, opacity: 0.15, transparent: true });
    return new THREE.Line(geo, mat);
}
```

Stars:
```javascript
function createStars() {
    const geometry = new THREE.BufferGeometry();
    const vertices = [];
    const colors = [];
    for (let i=0; i<8000; i++) {
        const r = 800 + Math.random()*200;
        const theta = Math.random()*Math.PI*2;
        const phi = Math.acos(2*Math.random()-1);
        vertices.push(r*Math.sin(phi)*Math.cos(theta));
        vertices.push(r*Math.sin(phi)*Math.sin(theta));
        vertices.push(r*Math.cos(phi));
        const shade = 0.5+Math.random()*0.5;
        colors.push(shade, shade, shade);
    }
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    const mat = new THREE.PointsMaterial({ size: 0.8, vertexColors: true, sizeAttenuation: true });
    return new THREE.Points(geometry, mat);
}
```

Now let me implement the procedural textures. I need to be careful with the canvas code.

For Jupiter's bands:
```javascript
function createJupiterTexture() {
    const width = 512, height = 256;
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');
    // base gradient
    const colors = ['#c8a87c', '#e0c9a6', '#9e7c5e', '#d4b896', '#b8906e', '#f0dcc0', '#a67c52'];
    const bandCount = 14;
    const bandH = height / bandCount;
    for (let i=0; i<bandCount; i++) {
        const c = colors[i % colors.length];
        ctx.fillStyle = c;
        ctx.fillRect(0, i*bandH, width, Math.ceil(bandH)+1);
    }
    // add turbulence: random horizontal streaks
    ctx.globalAlpha = 0.3;
    for (let i=0; i<300; i++) {
        const y = Math.random()*height;
        const x = Math.random()*width;
        const w = 20+Math.random()*40;
        ctx.fillStyle = `rgba(255,255,255,${Math.random()*0.3})`;
        ctx.fillRect(x, y, w, 1);
        ctx.fillStyle = `rgba(100,50,0,${Math.random()*0.2})`;
        ctx.fillRect(x, y, w, 2);
    }
    ctx.globalAlpha = 1;
    return new THREE.CanvasTexture(canvas);
}
```

For Earth:
```javascript
function createEarthTexture() {
    const width = 512, height = 256;
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');
    // ocean
    ctx.fillStyle = '#1a66cc';
    ctx.fillRect(0,0,width,height);
    
    // Draw continents using random walk blobs
    ctx.fillStyle = '#2d8a3e';
    const continents = [
        { x: width*0.2, y: height*0.4, r: 40 },
        { x: width*0.5, y: height*0.5, r: 50 },
        { x: width*0.8, y: height*0.3, r: 35 },
        { x: width*0.6, y: height*0.7, r: 45 },
    ];
    for (const c of continents) {
        ctx.beginPath();
        ctx.ellipse(c.x, c.y, c.r, c.r*0.7, 0, 0, Math.PI*2);
        ctx.fill();
    }
    // Add some islands
    for (let i=0; i<20; i++) {
        ctx.beginPath();
        ctx.ellipse(Math.random()*width, Math.random()*height, 3+Math.random()*8, 2+Math.random()*5, Math.random()*Math.PI, 0, Math.PI*2);
        ctx.fillStyle = `rgba(40,120,60,${0.5+Math.random()*0.5})`;
        ctx.fill();
    }
    // Polar caps
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, width, 15);
    ctx.fillRect(0, height-15, width, 15);
    
    return new THREE.CanvasTexture(canvas);
}
```

OK, I'll keep the textures fairly simple. The key is to get a complete working file.

Let me now assemble the entire code. I need to be mindful of the code structure.

Here's the complete file plan:

```html
<!DOCTYPE html>
<html>
<head>
<style>
    body { margin: 0; overflow: hidden; background: black; font-family: Arial, sans-serif; }
    #name { position: fixed; bottom: 10%; left: 50%; transform: translateX(-50%); color: white; font-size: 2em; text-shadow: 0 0 20px rgba(0,0,0,0.8); opacity: 0; transition: opacity 0.5s; letter-spacing: 0.2em; }
</style>
</head>
<body>
<div id="name">THE SUN</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r.../three.min.js"></script>
<script>
// ... code
</script>
</body>
</html>
```

Wait, for import maps with r186, I should use ES modules. But script tags with type="module" are fine. Actually, using the cdnjs CDN with three.module.js and import map:

```html
<script type="importmap">
{
    "imports": {
        "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js"
    }
}
</script>
```

For r160+, you need an import map. Or just use CDN with script tag:

```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
```

Using the UMD build with a global THREE is simpler for a single file. But newer versions don't have UMD builds. Let me use a known version like r128 which has UMD. But r128 lacks some features? It has everything I need: CanvasTexture, Sprite, etc. Yes, r128 is good.

Actually, let me use the module approach with CDN and an import map. Here's the cleanest way:

```html
<script type="importmap">
{
  "imports": {
    "three": "https://unpkg.com/three@0.160.0/build/three.module.js",
    "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/"
  }
}
</script>
<script type="module">
import * as THREE from 'three';
// ... code
</script>
```

But to avoid CDN issues, I can use:
```html
<script src="https://unpkg.com/three@0.160.0/build/three.min.js"></script>
```
No, that's not available as a global in new versions.

Let me use the CDN with global: `https://cdnjs.cloudflare.com/ajax/libs/three.js/r134/three.min.js` works. Actually, r134 includes a global THREE. Let me use r128 or r134.

I'll use:
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
```

This should work fine for all the features I need (Scene, PerspectiveCamera, WebGLRenderer, CanvasTexture, Sprite, PointLight, etc.). It has BufferGeometry, setFromPoints, Line, Points, etc. Good.

Let me write the code now.

Actually, for r128, `THREE.` has everything. Let me proceed.

One more thing: The renderer needs to handle the sun's point light. In r128, PointLight has `distance` and `decay`. The default `decay` in r128 is 1, not 2. I'll set `decay: 0` for no falloff. Or set `intensity: 1.5`.

OK, let me write the final code.

I realize I should also handle the window resize.

Let me write the complete implementation:

```javascript
// Scene setup
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 2000);
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
document.body.appendChild(renderer.domElement);

// Lights
const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
scene.add(ambientLight);

const sunLight = new THREE.PointLight(0xffffff, 1.5, 0, 0);
sunLight.position.set(0, 0, 0);
scene.add(sunLight);
```

Note: `PointLight(color, intensity, distance, decay)` - r128 signature is (color, intensity, distance, decay). distance=0 means infinite. decay=0 means no falloff. Set intensity maybe 1.5.

Now the planet data:

```javascript
const planetData = [
    { name: 'Mercury', radius: 1.2, distance: 10, speed: 0.8, offset: Math.random()*Math.PI*2, color: 0x8c7e6d, texture: createMercuryTexture, spin: 0.1 },
    { name: 'Venus', radius: 1.5, distance: 15, speed: 0.6, offset: Math.random()*Math.PI*2, color: 0xe3c88e, texture: createVenusTexture, spin: 0.05 },
    { name: 'Earth', radius: 1.6, distance: 20, speed: 0.5, offset: Math.random()*Math.PI*2, color: 0x4a90d9, texture: createEarthTexture, spin: 0.3 },
    { name: 'Mars', radius: 1.2, distance: 25, speed: 0.4, offset: Math.random()*Math.PI*2, color: 0xc1440e, texture: createMarsTexture, spin: 0.2 },
    { name: 'Jupiter', radius: 4.0, distance: 40, speed: 0.25, offset: Math.random()*Math.PI*2, color: 0xd4a76a, texture: createJupiterTexture, spin: 0.5 },
    { name: 'Saturn', radius: 3.5, distance: 55, speed: 0.2, offset: Math.random()*Math.PI*2, color: 0xe0b589, texture: createSaturnTexture, spin: 0.4 },
    { name: 'Uranus', radius: 2.0, distance: 70, speed: 0.15, offset: Math.random()*Math.PI*2, color: 0x9be3e0, texture: createUranusTexture, spin: 0.1 },
    { name: 'Neptune', radius: 2.0, distance: 85, speed: 0.1, offset: Math.random()*Math.PI*2, color: 0x4a6de0, texture: createNeptuneTexture, spin: 0.1 },
];
```

I'll use a larger sun:

```javascript
const sunMesh = new THREE.Mesh(
    new THREE.SphereGeometry(5, 32, 32),
    new THREE.MeshBasicMaterial({ map: createSunTexture() })
);
scene.add(sunMesh);
```

Planets:

```javascript
const planets = [];
for (let i=0; i<planetData.length; i++) {
    const data = planetData[i];
    const geo = new THREE.SphereGeometry(data.radius, 32, 32);
    const mat = new THREE.MeshStandardMaterial({ map: data.texture(), roughness: 0.8, metalness: 0.1 });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.set(data.distance, 0, 0);
    scene.add(mesh);
    data.mesh = mesh;
    planets.push(mesh);
    
    // Orbit line
    const orbit = createOrbitLine(data.distance);
    scene.add(orbit);
}
```

For Saturn's rings:
```javascript
if (data.name === 'Saturn') {
    const ringGeo = new THREE.RingGeometry(data.radius * 1.4, data.radius * 2.2, 64);
    const ringMat = new THREE.MeshBasicMaterial({
        map: createRingTexture(),
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.8
    });
    const ring = new THREE.Mesh(ringGeo, ringMat);
    ring.rotation.x = Math.PI / 2.5;
    mesh.add(ring);
}
```

Hmm, but the ring geometry's default position is in the XY plane. I need to rotate it so it's in the XZ plane: `ring.rotation.x = Math.PI / 2;`.

Actually, RingGeometry lies in the XY plane by default. To make it equatorial (XZ plane), rotate by -90 degrees around X. Let me do `ring.rotation.x = Math.PI / 2;`.

OK, let me now write the camera offsets:

```javascript
const cameraOffsets = [
    new THREE.Vector3(8, 6, 15),   // Sun (index 0)
    new THREE.Vector3(1.5, 1, 3),  // Mercury
    new THREE.Vector3(2, 1.5, 4),  // Venus
    new THREE.Vector3(2, 1.5, 4),  // Earth
    new THREE.Vector3(1.5, 1, 3),  // Mars
    new THREE.Vector3(5, 3, 10),   // Jupiter
    new THREE.Vector3(4, 3, 10),   // Saturn
    new THREE.Vector3(2, 1.5, 5),  // Uranus
    new THREE.Vector3(2, 1.5, 5),  // Neptune
];
```

Let me adjust these. For the Sun with radius 5, an offset of (8,6,15) gives distance ~17.5. That's close enough to see the sun prominently.

For Jupiter radius 4, (5,3,10) gives distance ~10.9. That should fit.

Now the camera update:

```javascript
function getPlanetPos(index, time) {
    if (index === 0) {
        return new THREE.Vector3(0, 0, 0);
    }
    const p = planetData[index - 1];
    const angle = time * p.speed + p.offset;
    return new THREE.Vector3(
        Math.cos(angle) * p.distance,
        0,
        Math.sin(angle) * p.distance
    );
}
```

Note: This uses the *original* orbit angle, independent of the mesh position. The mesh position is updated each frame using the same formula, so they'll match. Good.

Wait, in `updatePlanets`, I'm setting the position based on `time * p.speed + p.offset`. In `getPlanetPos`, I'm using the same `time * p.speed + p.offset`. So they match.

Now the camera:

```javascript
const segmentDuration = 5;
const totalSegments = 9;
const totalDuration = segmentDuration * totalSegments;

function updateCamera(time) {
    const looped = time % totalDuration;
    const segIndex = Math.floor(looped / segmentDuration);
    const localT = (looped - segIndex * segmentDuration) / segmentDuration;
    
    const segStartTime = time - (looped - segIndex * segmentDuration);
    
    const approachDuration = Math.min(2.0, segmentDuration * 0.4);
    const uRaw = localT * segmentDuration / approachDuration; // 0 to (segmentDuration/approachDuration)
    const u = Math.min(uRaw, 1);
    const su = smoothstep(u);
    
    let camPos, camLookAt;
    if (u < 1) {
        // Approach
        const prevIndex = (segIndex - 1 + totalSegments) % totalSegments;
        const startPos = getPlanetPos(prevIndex, segStartTime).add(cameraOffsets[prevIndex]);
        const endTime = segStartTime + approachDuration;
        const endPos = getPlanetPos(segIndex, endTime).add(cameraOffsets[segIndex]);
        camPos = new THREE.Vector3().lerpVectors(startPos, endPos, su);
        camLookAt = getPlanetPos(segIndex, time);
    } else {
        // Hold
        const targetPos = getPlanetPos(segIndex, time);
        camPos = targetPos.clone().add(cameraOffsets[segIndex]);
        camLookAt = targetPos;
    }
    
    camera.position.copy(camPos);
    camera.lookAt(camLookAt);
    
    // Update name
    const nameEl = document.getElementById('name');
    const names = ['THE SUN', ...planetData.map(p => p.name.toUpperCase())];
    nameEl.textContent = names[segIndex];
}
```

Wait, there's a problem: During the approach, `startPos` is computed at `segStartTime`. But `segStartTime` is in the past (by `localT * segmentDuration` seconds). At the very beginning of the segment (localT=0), `segStartTime = time`, so startPos = Neptune + offset at current time. That's correct. As time progresses, `startPos` stays constant because `segStartTime` is fixed for this segment. Good.

But wait, if `time` is beyond the approach end, `u=1` and we use the hold. The transition from approach to hold at `u=1` gives `camPos = endPos`. Then the hold sets `camPos = currentTargetPos + offset`. But `endPos` was computed as `getPlanetPos(segIndex, endTime).add(offset)`. At exactly `time = endTime`, these are equal. For `time > endTime`, the hold position tracks the moving planet, so the camera smoothly follows.

However, there's a subtle issue: At the segment boundary, the camera's position for the *next* segment's approach is computed as `getPlanetPos(prevIndex, nextSegStartTime).add(offset[prevIndex])`. But the *current* segment's hold has been setting `camPos = getPlanetPos(currIndex, time).add(offset[currIndex])`. At the boundary, `time = nextSegStartTime`, so the new approach computes `startPos = getPlanetPos(currIndex, nextSegStartTime).add(offset[currIndex])`, which is exactly the current hold position (because the hold at the boundary would be at that same expression). Wait no, the current segment's hold at time `boundaryTime` has `segIndex = currIndex`. So `camPos = getPlanetPos(currIndex, boundaryTime) + offset[currIndex]`. The next segment's approach has `prevIndex = currIndex` and `segStartTime = boundaryTime`, so `startPos = getPlanetPos(currIndex, boundaryTime) + offset[currIndex]`. They match. Continuity is preserved. 

Now, there's one issue: `smoothstep(u)` where `u` is the raw ratio `localT * segmentDuration / approachDuration`. When `localT = 0`, `u=0`, `su=0`. When `localT = approachDuration / segmentDuration` (i.e., localT=0.4 if approachDuration=2), `u=1`, `su=1`. Good.

But `smoothstep(u)` typically maps 0→0, 0.5→0.5, 1→1 with the formula `x*x*(3-2*x)`. That works.

Actually, for the approach, I should use `smoothstep(0, 1, uRaw)`? Since u is already clamped to [0,1], I can use `smoothstep(0,1,Math.min(uRaw,1))`. That's the same as `smoothstep(u)` if u is in [0,1]. So `su = smoothstep(u)` works.

Let me define:
```javascript
function smoothstep(x) {
    return x * x * (3 - 2 * x);
}
```

Now, the Sun's position is (0,0,0). The camera offset for the Sun is (8,6,15). If `segIndex=0`, the approach starts at `getPlanetPos(prevIndex=8, segStartTime) + offset[8]`, which is Neptune's position + Neptune offset. So the camera flies from Neptune to the Sun. Nice.

But there's an issue with the name display: during the approach to the Sun (first segment of each cycle), the name should show "THE SUN". That's correct with my code (`names[segIndex]`).

Now, the planet meshes need to be positioned according to the same formula. In `updatePlanets`, I'll set:
```javascript
function updatePlanets(time) {
    for (const data of planetData) {
        const angle = time * data.speed + data.offset;
        data.mesh.position.set(
            Math.cos(angle) * data.distance,
            0,
            Math.sin(angle) * data.distance
        );
        data.mesh.rotation.y = time * data.spin;
    }
}
```

Note: I removed the `offset` (the initial orbit offset). Let me set `offset` to a random value in the data to avoid all planets starting at the same angle. That's fine.

Now, the Moon:

```javascript
// Add Moon
const moonMesh = new THREE.Mesh(
    new THREE.SphereGeometry(0.3, 16, 16),
    new THREE.MeshStandardMaterial({ color: 0xcccccc })
);
scene.add(moonMesh);
```

In the update function:
```javascript
const earthData = planetData[2]; // Earth is at index 2
const earthAngle = time * earthData.speed + earthData.offset;
const earthX = Math.cos(earthAngle) * earthData.distance;
const earthZ = Math.sin(earthAngle) * earthData.distance;
const moonAngle = time * 5;
moonMesh.position.set(
    earthX + Math.cos(moonAngle) * 2.5,
    0,
    earthZ + Math.sin(moonAngle) * 2.5
);
```

But wait, `earthData.mesh.position` is set in `updatePlanets`, so I can just use that:
```javascript
const earthPos = planetData[2].mesh.position;
const moonAngle = time * 5;
moonMesh.position.set(
    earthPos.x + Math.cos(moonAngle) * 2.5,
    0,
    earthPos.z + Math.sin(moonAngle) * 2.5
);
```

Good.

Now, for the sun's halo sprite:

```javascript
const sunGlowTexture = createGlowTexture(); // radial gradient canvas texture
const sunGlowMat = new THREE.SpriteMaterial({
    map: sunGlowTexture,
    blending: THREE.AdditiveBlending,
    transparent: true,
    opacity: 0.6,
    depthWrite: false
});
const sunGlow = new THREE.Sprite(sunGlowMat);
sunGlow.scale.set(30, 30, 1);
sunGlow.position.set(0, 0, 0);
scene.add(sunGlow);
```

`createGlowTexture` creates a canvas with a radial gradient from white/yellow to transparent.

Now, let's write all the texture functions. Since I'm using `THREE.CanvasTexture`, I need to create canvases.

Let me implement each texture function as a standalone function.

OK, I think I have enough to write the full code. Let me do it now.

One more thing: the orbit lines. I'll create them after the planets so they're in the background. They use `LineBasicMaterial` with opacity.

Also, to make the planets look lit, I'll make sure the point light has enough intensity. In r128, `PointLight` with `decay=0` means no falloff. The intensity should be fine.

Let me now write the complete HTML file.

Wait, I want to double-check the sun's point light behavior. In three.js r128, `new THREE.PointLight(color, intensity, distance, decay)`. With `decay=0`, the light does not fall off. So all planets will be equally lit. The sun is at the center, so all planets face the sun (assuming the light is at the origin). Since the planets are positioned at various distances, if decay=0, they all receive the same intensity. Good.

However, with `decay=0`, the PointLight intensity in three.js r128 is used directly without physical falloff. So `intensity: 1` should be fine. But the `MeshStandardMaterial` might be too dark with just one light. I'll set `intensity: 1.5` and add ambient.

Actually, in three.js r128, `MeshStandardMaterial` uses a simple lighting model. `intensity: 1` should be fine. But I should also set `renderer.toneMapping = false` (not needed) or leave default.

OK, let's code.

Actually, for the glow texture:

```javascript
function createGlowTexture() {
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 256;
    const ctx = canvas.getContext('2d');
    const gradient = ctx.createRadialGradient(128, 128, 0, 128, 128, 128);
    gradient.addColorStop(0, 'rgba(255, 200, 50, 1)');
    gradient.addColorStop(0.3, 'rgba(255, 150, 0, 0.6)');
    gradient.addColorStop(1, 'rgba(255, 100, 0, 0)');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 256, 256);
    return new THREE.CanvasTexture(canvas);
}
```

This gives a nice glow.

Let me now think about the name overlay styling. I'll make it white with a slight shadow, and maybe add a subtitle. The name will change with the segment.

I'll also add a progress bar or something? No, keep it simple.

Now, let me write the complete code. I'll be thorough.

Actually, there's one more issue: in `updateCamera`, for the approach, I compute `startPos` using `getPlanetPos(prevIndex, segStartTime)`. But `segStartTime` is computed for *this* segment. The previous segment's hold ended at exactly `segStartTime` (because the previous segment's hold used `getPlanetPos(prevSeg, time)` for `time` up to `segStartTime`). So the continuity holds.

But what about the first frame at time=0? The camera initially has a default position (0,0,0). At time=0, we're in segment 0, localT=0, u=0. The camera should be at `getPlanetPos(prevIndex, 0) + offset[prevIndex]` where prevIndex=8 (Neptune). So the camera will snap to Neptune at the start. That's fine.

Let me also initialize the camera position at time=0 before the loop. Actually, the first `animate` call will set it.

One more thing: the orbit line for each planet should be positioned at the appropriate distance. Since the planets are at fixed distances, the orbit lines are circles in the XZ plane.

Alright, let me write the complete code now. I'll include the full file.

Actually, I realize there's another issue: `getPlanetPos` uses `data.offset` (the initial orbit angle), which is a random value. The mesh position uses the same `data.offset`. So `getPlanetPos` needs to know the exact data of the planet. Since `planetData` is accessible, it's fine.

Let me set the `offset` values to nice constants rather than random, so the solar system looks good. Like:
```javascript
offset: 0,
```
Or give them specific angles.

Actually, for the default, they can all be 0, which aligns all planets at angle 0 at time 0. That's fine.

But with `time * speed`, the planets move at different speeds, so they'll spread out naturally.

Let me set `offset: 0` for all.

Now, let me write the whole file:

```html
<!DOCTYPE html>
<html>
<head>
<style>
    body { margin: 0; overflow: hidden; background: #000; font-family: Arial, sans-serif; }
    #name { position: fixed; bottom: 50px; left: 50%; transform: translateX(-50%); color: #fff; font-size: 24px; letter-spacing: 3px; text-shadow: 0 0 20px rgba(0,0,0,0.8); opacity: 0.9; z-index: 10; }
    #info { position: fixed; top: 10px; right: 10px; color: rgba(255,255,255,0.5); font-size: 12px; z-index: 10; }
</style>
</head>
<body>
<div id="name">THE SUN</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
// ... all code
</script>
</body>
</html>
```

Let me now write the JavaScript.

Actually, one concern: `canvas.getContext('2d')` etc. All good.

Another concern: In r128, `THREE.CanvasTexture` works. `THREE.Sprite`, `THREE.SpriteMaterial`, `THREE.AdditiveBlending` all work.

Let me write the full JS now. It's going to be long but complete.

Here's my final plan for the code structure:

1. Scene, camera, renderer setup
2. Create stars
3. Create sun (mesh + glow)
4. Create planets (with textures)
5. Create orbit lines
6. Create moon
7. Define utility functions (getPlanetPos, smoothstep)
8. Define texture creation functions
9. Animation loop: update moons, planets, camera, renderer
10. Name display update
11. Window resize handler

Let me write it out fully now.

I'll keep the texture functions quite detailed to make them look decent.

For simplicity, I'll define one generic noise/detail generator that can be reused.

Let me go.

Actually, let me also set the initial camera position to something reasonable for the very first frame before the animation starts, to avoid a flash. But it's fine.

Now, writing the code...

I'll need to be careful about variable scope. All functions and variables should be within the same script scope.

Also note: I'm using `THREE.CanvasTexture` where the map is set. For `MeshStandardMaterial`, the map is the color texture. All good.

Let me start writing.

For the camera FOV: 60. The near/far: 0.1 to 2000.

Now, the orbit line for the Sun? There isn't one since the sun is at the center.

The name overlay: I want it to fade in/out. I'll simply update the text and use CSS transition on opacity. But for simplicity, I'll just set the text.

OK let me code it all in the script.

One more thing: for the update loop, I'll use `requestAnimationFrame(animate)`.

Let me write the code now.

(Note: I need to be careful with the texture creation for planets to avoid undefined errors.)

Here's a simplified version of the texture functions:

```javascript
function createSunTexture() {
    const c = document.createElement('canvas'); c.width=512; c.height=256;
    const x = c.getContext('2d');
    const g = x.createLinearGradient(0,0,0,256);
    g.addColorStop(0,'#ffcc33'); g.addColorStop(0.5,'#ff9900'); g.addColorStop(1,'#ff6600');
    x.fillStyle=g; x.fillRect(0,0,512,256);
    // noise
    const img=x.getImageData(0,0,512,256);
    for(let i=0;i<img.data.length;i+=4){
        img.data[i]+=(Math.random()-0.5)*30;
        img.data[i+1]+=(Math.random()-0.5)*30;
        img.data[i+2]+=(Math.random()-0.5)*30;
    }
    x.putImageData(img,0,0);
    return new THREE.CanvasTexture(c);
}
```

For Mercury:
```javascript
function createMercuryTexture() {
    const c = document.createElement('canvas'); c.width=256; c.height=128;
    const x = c.getContext('2d');
    x.fillStyle='#8a817b'; x.fillRect(0,0,256,128);
    // craters
    for(let i=0;i<40;i++){
        x.fillStyle=`rgba(60,60,60,${0.2+Math.random()*0.4})`;
        x.beginPath();
        x.ellipse(Math.random()*256, Math.random()*128, 2+Math.random()*6, 2+Math.random()*6, 0, 0, Math.PI*2);
        x.fill();
    }
    return new THREE.CanvasTexture(c);
}
```

And so on for other planets.

For the ring texture:
```javascript
function createRingTexture() {
    const c = document.createElement('canvas'); c.width=512; c.height=64;
    const x = c.getContext('2d');
    // horizontal gradient with alternating bands
    for(let i=0;i<512;i++){
        const shade = 150 + Math.sin(i*0.1)*30 + Math.random()*20;
        const gradient = x.createLinearGradient(i,0,i,64);
        gradient.addColorStop(0,'rgba(200,180,150,'+ (0.2+0.8*Math.abs(Math.sin(i*0.05))) +')');
        // Actually let me just fill a few bands
    }
    // Simpler: draw horizontal bands
    for(let y=0; y<64; y++){
        const v = 120 + 80*Math.sin(y*0.5);
        x.fillStyle = `rgba(${v}, ${v*0.8}, ${v*0.6}, 0.8)`;
        x.fillRect(0, y, 512, 1);
    }
    return new THREE.CanvasTexture(c);
}
```

Hmm, for the ring, a radial gradient might work better. But since the ring geometry is mapped with the texture in a cylindrical way... Actually, the RingGeometry UV mapping may not be ideal. In three.js r128, `RingGeometry` has UVs, but I'm not sure how they look. Using a texture on the ring might be distorted. For simplicity, I can just use a color with `side: DoubleSide` and `transparent: true` and `opacity: 0.6`. No texture needed.

Let me do that instead:
```javascript
const ringMat = new THREE.MeshStandardMaterial({
    color: 0xc0a070,
    side: THREE.DoubleSide,
    transparent: true,
    opacity: 0.7,
    roughness: 0.8
});
```

OK.

Let me finalize the code and write it all now. This will be a long but complete file.

Actually, there's a subtle problem: `THREE.PointLight` with `distance=0` and `decay=0` in r128? The default distance is 0 (infinite). The default decay is 1 in r128. So I should set `decay: 0` explicitly:
```javascript
const sunLight = new THREE.PointLight(0xffffff, 2, 0, 0);
```
In this constructor, the 3rd arg is `distance`, 4th is `decay`. distance=0 means infinite, decay=0 means no falloff. Good.

Alternatively, use `new THREE.AmbientLight(0x404040, 0.5)` for general fill.

Now, for `MeshStandardMaterial`, the specular response might be too strong with default settings. I'll set `metalness: 0.1, roughness: 0.9`.

OK, writing the code now. I'll be concise but complete.

One more thing: I need a `getPlanetPos` function that matches the orbit animation. The orbit animation uses `time * speed + offset`. So:

```javascript
function getPlanetPos(index, time) {
    if (index === 0) return new THREE.Vector3(0,0,0);
    const p = planetData[index-1];
    const ang = time * p.speed + p.offset;
    return new THREE.Vector3(Math.cos(ang) * p.distance, 0, Math.sin(ang) * p.distance);
}
```

Then `updatePlanets` can use this:
```javascript
function updatePlanets(time) {
    for (let i=0; i<planetData.length; i++) {
        const p = planetData[i];
        const pos = getPlanetPos(i+1, time);
        p.mesh.position.copy(pos);
        p.mesh.rotation.y += p.spin * 0.016; // approx per frame? Actually, use time * p.spin
    }
}
```

I'll use `p.mesh.rotation.y = time * p.spin;` for deterministic rotation.

Great, let me write the final code.

Actually, `p.offset` is used as an initial angle. The ray from planet to sun is at angle. For the getPlanetPos and the orbit, both use the same. Good.

Let me also set the planets to have a small axial tilt. Not necessary.

Now, I want the sun to rotate slowly: `sunMesh.rotation.y = time * 0.1;`.

Alright, writing the final code now. I'll try to keep it clean and well-commented. Since this is a single file, it'll be around 400-500 lines.

Let me code it up in my head before writing:

- `createStars()`: Add stars.
- `createGlowTexture()`: Radial gradient.
- `createSun()`, `createPlanets()`, `createMoon()`, `createOrbitLines()`, `createRings(Saturn)`.
- `animate(timestamp)`:
  - `const time = timestamp * 0.001;`
  - `updatePlanets(time);`
  - `updateMoon(time);`
  - `updateCamera(time);`
  - `updateGlow(time);` (maybe not needed)
  - `renderer.render(scene, camera);`
- `updateCamera(time)`: as discussed.

Let me also update the name element's text content with the current planet's name.

I'll use `requestAnimationFrame(animate)` at the top of `animate` so it loops.

OK, writing the code now.

One more consideration: For the `smoothstep` function in the camera update, I used the raw u value. But `smoothstep` as defined `x*x*(3-2*x)` is actually `clamp01(x)^2 * (3 - 2*clamp01(x))`. Since I already clamp `u` to [0,1], it's fine.

Alright, let me write it.

Actually, I'll also add some ambient star glows... no, keep it simple.

Let me write the complete implementation now. I'll output it as a single block of code.