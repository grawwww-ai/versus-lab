User wants a complete self-contained HTML file with a Three.js 3D racing game. Let me break down the requirements:

1. **Track**: Closed race track with curves, kerbs, start/finish line, procedurally built
2. **Landscape**: Grass, trees/buildings, sky
3. **Player car**: Detailed from primitives (body, wheels, lights)
4. **Rival cars**: At least 3, different colors
5. **AI**: All cars follow racing line, overtaking
6. **Camera**: Chase camera behind player, sense of speed
7. **HUD**: Speed, lap counter (Lap 1/3), race position (e.g., 2nd)
8. **Animation**: requestAnimationFrame timestamp
9. **Full-window canvas**, resizing, starts automatically

Let me plan this out:

### Track
- Use a closed curve (CatmullRomCurve3 or custom) for the track center
- Create track geometry from the curve with width
- Add kerbs (red/white curbs) on curves
- Start/finish line

### Landscape
- Large plane with grass color
- Trees (cone + cylinder)
- Maybe simple buildings

### Player Car
- Box for body
- Cylinder for wheels (rotating)
- Small boxes for headlights

### Rival Cars
- 3 cars with different colors

### AI
- Follow points along the racing line
- Overtaking logic (slowing down or changing lanes)

### Camera
- Chase camera behind player car

### HUD
- HTML overlay with speed, lap, position

Let me think about the track design. I'll use a closed curve. Let me create a nice racing track curve.

For the track:
- Define a curve using CatmullRomCurve3 in the XZ plane
- Create track geometry by extruding or creating a ribbon
- Place kerbs on curves

Actually, let me create the track as a flat ribbon mesh. I'll generate vertices along the curve.

For the racing line, I'll precompute points along the curve and have AI cars follow them.

Let me design a track:

```javascript
const trackPoints = [
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(20, 0, -20),
    new THREE.Vector3(40, 0, -40),
    new THREE.Vector3(60, 0, -20),
    new THREE.Vector3(70, 0, 20),
    new THREE.Vector3(50, 0, 50),
    new THREE.Vector3(20, 0, 60),
    new THREE.Vector3(-20, 0, 50),
    new THREE.Vector3(-40, 0, 30),
    new THREE.Vector3(-30, 0, 0),
    new THREE.Vector3(-10, 0, -10),
];
```

Hmm, let me make a more interesting track. Let me use a custom closed curve.

Actually, let me use CatmullRomCurve3 and create a closed loop.

```javascript
const trackPoints = [
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(30, 0, -30),
    new THREE.Vector3(60, 0, 0),
    new THREE.Vector3(60, 0, 40),
    new THREE.Vector3(30, 0, 70),
    new THREE.Vector3(-10, 0, 60),
    new THREE.Vector3(-40, 0, 40),
    new THREE.Vector3(-40, 0, 10),
    new THREE.Vector3(-20, 0, -10),
];
const trackCurve = new THREE.CatmullRomCurve3(trackPoints, true, 'catmullrom', 0.5);
```

This gives a closed track. I'll get points along it.

For the track geometry:
- Get points along the curve
- For each point, compute perpendicular direction (right vector)
- Create vertices for left and right edges
- Create faces

Let me write a function to generate track geometry.

```javascript
function createTrackGeometry(curve, width, segments) {
    const positions = [];
    const uvs = [];
    const indices = [];
    
    for (let i = 0; i <= segments; i++) {
        const t = i / segments;
        const point = curve.getPointAt(t);
        const tangent = curve.getTangentAt(t);
        const normal = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();
        
        const left = point.clone().add(normal.clone().multiplyScalar(width / 2));
        const right = point.clone().add(normal.clone().multiplyScalar(-width / 2));
        
        positions.push(left.x, 0.05, left.z);
        positions.push(right.x, 0.05, right.z);
        
        uvs.push(t, 0);
        uvs.push(t, 1);
        
        if (i < segments) {
            const base = i * 2;
            indices.push(base, base + 1, base + 2);
            indices.push(base + 1, base + 3, base + 2);
        }
    }
    
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geometry.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
    geometry.setIndex(indices);
    geometry.computeVertexNormals();
    
    return geometry;
}
```

For the racing line, I'll precompute points and tangents.

### Cars

Player car:
```javascript
function createPlayerCar() {
    const car = new THREE.Group();
    
    // Body
    const bodyGeom = new THREE.BoxGeometry(2, 0.8, 4);
    const bodyMat = new THREE.MeshPhongMaterial({ color: 0xff0000 });
    const body = new THREE.Mesh(bodyGeom, bodyMat);
    body.position.y = 0.6;
    car.add(body);
    
    // Cabin
    const cabinGeom = new THREE.BoxGeometry(1.6, 0.6, 2);
    const cabinMat = new THREE.MeshPhongMaterial({ color: 0x333366 });
    const cabin = new THREE.Mesh(cabinGeom, cabinMat);
    cabin.position.set(0, 1.2, -0.3);
    car.add(cabin);
    
    // Wheels
    const wheelGeom = new THREE.CylinderGeometry(0.4, 0.4, 0.3, 16);
    wheelGeom.rotateZ(Math.PI / 2);
    const wheelMat = new THREE.MeshPhongMaterial({ color: 0x111111 });
    
    const wheelPositions = [
        [-0.9, 0.4, 1.2],
        [0.9, 0.4, 1.2],
        [-0.9, 0.4, -1.2],
        [0.9, 0.4, -1.2]
    ];
    
    const wheels = [];
    wheelPositions.forEach(pos => {
        const wheel = new THREE.Mesh(wheelGeom, wheelMat);
        wheel.position.set(...pos);
        car.add(wheel);
        wheels.push(wheel);
    });
    
    // Headlights
    const headlightGeom = new THREE.BoxGeometry(0.3, 0.3, 0.1);
    const headlightMat = new THREE.MeshPhongMaterial({ color: 0xffffaa, emissive: 0xffffaa, emissiveIntensity: 0.5 });
    
    const headlightPositions = [
        [-0.5, 0.7, 2],
        [0.5, 0.7, 2]
    ];
    
    headlightPositions.forEach(pos => {
        const headlight = new THREE.Mesh(headlightGeom, headlightMat);
        headlight.position.set(...pos);
        car.add(headlight);
    });
    
    // Tail lights
    const taillightMat = new THREE.MeshPhongMaterial({ color: 0xff0000, emissive: 0xff0000, emissiveIntensity: 0.3 });
    
    const taillightPositions = [
        [-0.6, 0.7, -2],
        [0.6, 0.7, -2]
    ];
    
    taillightPositions.forEach(pos => {
        const taillight = new THREE.Mesh(headlightGeom, taillightMat);
        taillight.position.set(...pos);
        car.add(taillight);
    });
    
    // Store wheels for animation
    car.userData.wheels = wheels;
    
    return car;
}
```

For AI cars, similar but different colors.

### AI System

All cars (including player) follow the racing line. But they need to overtake. I'll implement a basic overtaking system:

- Each car has a "track position" (distance along the track)
- Cars follow the racing line with a certain offset
- When a car is faster and catches up, it can change lanes (offset) to overtake

Actually, for simplicity, let me have all cars follow the racing line, and when a car is faster and approaching another car, it will steer around.

Let me think about a simpler approach:
- Each car has a `trackOffset` (how far along the track)
- Cars move along the track by increasing trackOffset
- The position on track is determined by `curve.getPointAt(t)` where t = trackOffset / totalLength
- Cars have different speeds, and when they are close to a car in front, they slow down
- For overtaking, a car can move to the side (offset perpendicular to the track direction)

Actually, let me think about this more carefully.

For a racing game, I need cars to:
1. Follow the racing line around the track
2. Have different speeds (some faster, some slower)
3. Overtake each other

I'll implement it like this:
- Precompute the racing line as a series of points
- Each car has a `progress` value (0 to 1) indicating how far along the track
- Cars move at a speed that depends on their engine power
- When approaching a car ahead, they slow down or change offset to overtake

Let me simplify: cars follow the track center line with a lane offset. Overtaking happens by changing lanes.

Here's my plan:
- The track has a center curve
- Each car has a `laneOffset` value (-1, 0, 1) for left, center, right
- When a car wants to overtake, it changes lane offset
- The actual position is: center + normal * laneOffset * laneWidth

Actually, for a more realistic racing feel, let me have the AI cars follow the curve at different speeds, and use simple collision avoidance.

Let me redesign:

**AI System Architecture:**

Each car has:
- `progress`: float (0-1) along track
- `speed`: current speed
- `targetSpeed`: desired speed
- `laneOffset`: -1 to 1 for side offset

Each frame:
1. Update progress: `progress += speed * dt / trackLength`
2. Get position from curve at progress
3. Get tangent from curve at progress
4. Compute perpendicular direction
5. Apply lateral offset (for racing line or overtaking)
6. For overtaking: check for cars ahead, if too close, change lane offset or slow down

This is getting complex. Let me simplify further.

**Simplified Approach:**

All cars move along the track using a progress variable. The position is computed from a curve. Cars have different target speeds, and I'll implement simple overtaking:

- Each car has a `speed` that varies
- When a car is behind another car (progress is close), it slows down
- To overtake, a car uses a lane offset to go around

Actually, let me take a simpler approach that still looks good:

- All cars follow the same racing line (the curve)
- They simply go around at different constant speeds
- When a faster car catches up to a slower car, it slows down to match speed
- For overtaking, the faster car occasionally moves to the side

You know what, let me do something even simpler but effective:

Each car follows a slightly different racing line (different lateral offsets). When a car is faster and catches up, it can use a more favorable line (different offset) to overtake.

Actually, let me just make all cars follow the racing line but with:
1. Different speeds
2. Simple collision avoidance (slow down if too close to car ahead)
3. Overtaking by changing lateral offset when close

Let me implement this step by step.

### Car Following the Racing Line

```javascript
// Each frame, for each car:
function updateCar(car, dt) {
    // Update progress
    car.progress += car.speed * dt / trackLength;
    if (car.progress >= 1) car.progress -= 1;
    
    // Get position on curve
    const pos = curve.getPointAt(car.progress);
    const tangent = curve.getTangentAt(car.progress);
    const normal = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();
    
    // Apply lateral offset
    const position = pos.clone().add(normal.clone().multiplyScalar(car.laneOffset));
    
    // Update car position and rotation
    car.mesh.position.copy(position);
    car.mesh.position.y = 0.4;
    
    const angle = Math.atan2(tangent.x, tangent.z);
    car.mesh.rotation.y = angle;
    
    // Update wheel rotation
    car.wheels.forEach(wheel => {
        wheel.rotation.x += car.speed * dt;
    });
}
```

For overtaking, I'll have cars change their laneOffset over time.

### Better Overtaking

Let me have each car maintain a `laneOffset` that changes when overtaking:

```javascript
// In the update loop for each car:
// Check for cars ahead
const aheadCars = allCars.filter(other => 
    other !== car && 
    (other.progress - car.progress + 1) % 1 < 0.1 && // roughly 10% ahead
    (other.progress - car.progress + 1) % 1 > 0
);

if (aheadCars.length > 0 && car.speed > aheadCars[0].speed) {
    // Need to overtake - change lane
    car.targetLaneOffset = -Sign(car.laneOffset) || 1;
}
```

This is getting complicated. Let me use a cleaner approach.

**Approach: Waypoint Following with Overtaking**

Actually, let me simplify to make it work:

1. Precompute a list of points along the track (racing line)
2. Each car follows these points
3. Cars have different target speeds
4. For overtaking, when a car is behind another and going faster, it moves to the side (lateral offset) while passing

Let me implement this with a more straightforward approach.

### Track and Racing Line

First, let me define the track as a CatmullRomCurve3, and get a series of points:

```javascript
const trackPoints = [];
const numPoints = 500;
for (let i = 0; i < numPoints; i++) {
    trackPoints.push(trackCurve.getPointAt(i / numPoints));
}
```

Then each car has a `currentTarget` index (which point on the track it's headed toward).

### Car Movement

```javascript
function updateCar(car, dt) {
    // Move toward current target
    const target = trackPoints[car.targetIndex];
    const pos = car.mesh.position;
    
    const dx = target.x - pos.x;
    const dz = target.z - pos.z;
    const dist = Math.sqrt(dx*dx + dz*dz);
    
    if (dist < 0.5) {
        car.targetIndex = (car.targetIndex + 1) % numPoints;
    }
    
    // Move forward
    const angle = Math.atan2(target.x - pos.x, target.z - pos.z);
    // ... but this doesn't give a sense of speed along the track
}
```

This approach doesn't give a nice speed metric. Let me instead use the progress-based approach.

### Progress-based with lateral offset

Let me use the progress approach with lane changing for overtaking. Here's my final plan:

**Track:**
- CatmullRomCurve3 closed curve
- Track width: 8 units
- Racing line follows the center of the track

**Car properties:**
- `progress`: 0 to 1
- `speed`: current speed
- `baseSpeed`: desired speed (AI)
- `laneOffset`: -1 to 1, -0.5 to 0.5 for racing line, larger for overtaking

**Update logic:**

```javascript
function updateCar(car, dt) {
    const trackLength = trackCurve.getLength();
    const speed = car.speed;
    
    // Update progress
    car.progress = (car.progress + speed * dt / trackLength) % 1;
    
    // Get position
    const pos = trackCurve.getPointAt(car.progress);
    const tangent = trackCurve.getTangentAt(car.progress);
    const normal = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();
    
    // Target position with lane offset
    const laneOffset = car.laneOffset * 2.5; // lateral shift in world units
    const targetPos = pos.clone().add(normal.clone().multiplyScalar(laneOffset));
    
    // Smooth movement
    car.mesh.position.lerp(targetPos, 0.1);
    
    // Rotation
    const angle = Math.atan2(tangent.x, tangent.z);
    car.mesh.rotation.y = angle;
    
    // Wheel spin
    car.wheels.forEach(w => {
        w.rotation.x += speed * dt;
    });
}
```

**Overtaking:**
- Periodically, a car may decide to change lane offset
- When a car is close to the car ahead (distance along track < threshold), it tries to overtake

Let me define a simpler overtaking algorithm:

```javascript
function checkCollisionAndOvertake(car, allCars, dt) {
    // Find the car directly ahead
    let closestAhead = null;
    let minDist = Infinity;
    
    for (const other of allCars) {
        if (other === car) continue;
        
        let dist = other.progress - car.progress;
        if (dist < 0) dist += 1;
        
        if (dist > 0 && dist < 0.1 && dist < minDist) {
            minDist = dist;
            closestAhead = other;
        }
    }
    
    if (closestAhead) {
        const relativeSpeed = car.speed - closestAhead.speed;
        if (relativeSpeed > 0) {
            // We're faster - need to overtake or slow down
            if (car.overtakeCooldown <= 0) {
                // Change lane to overtake
                car.targetLaneOffset = car.laneOffset > 0 ? -0.8 : 0.8;
                car.isOvertaking = true;
                
                // After some time, return to racing line
                car.overtakeCooldown = 2;
            }
            
            // Slow down if blocked
            if (car.isOvertaking && Math.abs(car.laneOffset - car.targetLaneOffset) < 0.1) {
                car.speed = closestAhead.speed * 0.9;
            }
        }
    }
    
    // Move lane offset toward target
    car.laneOffset += (car.targetLaneOffset - car.laneOffset) * dt * 2;
    
    // Update cooldown
    if (car.overtakeCooldown > 0) {
        car.overtakeCooldown -= dt;
        if (car.overtakeCooldown <= 0) {
            car.targetLaneOffset = 0;
            car.isOvertaking = false;
        }
    }
}
```

This is still getting complex. Let me simplify even more for the demo.

**Simplified Overtaking:**

I'll have each AI car maintain its own progress around the track. They all have slightly different base speeds. When a faster car catches up to a slower one (close progress), the faster car will:
1. Steer to the side (change lane offset to positive or negative)
2. Speed up slightly to pass
3. After passing, return to the racing line

For the player, similar logic applies but the player's speed is controllable.

Actually, since the requirement says "all cars are driven by an AI", the player car is also AI-driven. So the whole thing is a simulation.

Let me make all 4 cars AI-driven, and the chase camera follows one of them.

### Simpler Approach for AI

Let me do the following:

1. All cars follow the track using progress-based movement
2. Each car has a `baseSpeed` (slightly different for each)
3. They adjust speed based on curvature (slow down on curves)
4. For overtaking, when a car is within a certain distance of the car ahead:
   - Change lane offset to the side
   - Maintain speed
   - Once past, return to center

Here's a cleaner implementation:

```javascript
function updateCar(car, dt) {
    // Get the current track position
    const trackLength = trackCurve.getLength();
    
    // Slow down on curves
    const tangent = trackCurve.getTangentAt(car.progress);
    const nextTangent = trackCurve.getTangentAt(Math.min(car.progress + 0.01, 1));
    const curvature = tangent.angleTo(nextTangent) / 0.01;
    
    // Target speed based on curvature
    let targetSpeed = car.baseSpeed / (1 + curvature * 5);
    targetSpeed = Math.max(5, Math.min(car.baseSpeed, targetSpeed));
    
    // Check for cars ahead
    let carAhead = null;
    let minDist = Infinity;
    for (const other of cars) {
        if (other === car) continue;
        let dist = other.progress - car.progress;
        if (dist < 0) dist += 1;
        if (dist < minDist) {
            minDist = dist;
            carAhead = other;
        }
    }
    
    // Avoid collision
    let speed = targetSpeed;
    if (carAhead && minDist < 0.02) {
        const timeToCollision = minDist * trackLength / Math.max(speed - carAhead.speed, 0.1);
        if (timeToCollision < 2) {
            speed = Math.min(speed, carAhead.speed);
        }
        
        // Overtake
        if (timeToCollision < 3 && minDist < 0.015) {
            // Change lane
            const side = car.laneOffset >= 0 ? -1 : 1;
            car.targetLaneOffset = side * 0.8;
            car.overtaking = true;
        }
    }
    
    // Return to center after overtaking
    if (car.overtaking) {
        car.overtakeTimer += dt;
        if (car.overtakeTimer > 1.5) {
            car.targetLaneOffset = 0;
            if (Math.abs(car.laneOffset - car.targetLaneOffset) < 0.05) {
                car.overtaking = false;
                car.overtakeTimer = 0;
            }
        }
    }
    
    car.speed = speed;
    
    // Update progress
    car.progress = (car.progress + car.speed * dt / trackLength) % 1;
    
    // Get position
    const pos = trackCurve.getPointAt(car.progress);
    const tangentAtPos = trackCurve.getTangentAt(car.progress);
    const normal = new THREE.Vector3(-tangentAtPos.z, 0, tangentAtPos.x).normalize();
    
    // Update lane offset
    car.laneOffset = THREE.MathUtils.lerp(car.laneOffset, car.targetLaneOffset, dt * 3);
    
    // Apply position
    const targetPos = pos.clone().add(normal.clone().multiplyScalar(car.laneOffset * 2.5));
    car.mesh.position.set(targetPos.x, 0.4, targetPos.z);
    
    // Face direction
    const angle = Math.atan2(tangentAtPos.x, tangentAtPos.z);
    car.mesh.rotation.y = angle;
    
    // Wheel spin
    const wheelSpeed = car.speed * 2;
    car.wheels.forEach(w => {
        w.rotation.x += wheelSpeed * dt;
    });
}
```

This should work reasonably well.

### Start/Finish Line

The start/finish line is on the track at progress 0. I'll create a plane with a checkerboard pattern or colored stripes.

```javascript
function createStartFinishLine() {
    const pos = trackCurve.getPointAt(0);
    const tangent = trackCurve.getTangentAt(0);
    const normal = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();
    
    const group = new THREE.Group();
    
    // Checkerboard pattern
    const lineMaterial = new THREE.MeshPhongMaterial({ color: 0xffffff });
    const lineGeometry = new THREE.PlaneGeometry(8, 1);
    
    for (let i = -4; i < 4; i++) {
        const mesh = new THREE.Mesh(lineGeometry, lineMaterial);
        mesh.position.copy(pos);
        mesh.position.y = 0.05;
        mesh.lookAt(pos.clone().add(tangent));
        
        // Alternate colors
        if (Math.floor((i + 4) / 0.5) % 2 === 0) {
            mesh.material = new THREE.MeshPhongMaterial({ color: 0xffffff });
        } else {
            mesh.material = new THREE.MeshPhongMaterial({ color: 0x000000 });
        }
        
        mesh.position.copy(pos);
        mesh.position.add(normal.clone().multiplyScalar(i * 0.5));
        
        group.add(mesh);
    }
    
    return group;
}
```

Actually, let me use a simpler approach for the start line: just a plane with a texture generated using a canvas.

```javascript
function createStartLine() {
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 32;
    const ctx = canvas.getContext('2d');
    
    // Checkerboard
    const cellSize = 16;
    for (let y = 0; y < 2; y++) {
        for (let x = 0; x < 16; x++) {
            ctx.fillStyle = (x + y) % 2 === 0 ? '#ffffff' : '#000000';
            ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
        }
    }
    
    const texture = new THREE.CanvasTexture(canvas);
    
    const pos = trackCurve.getPointAt(0);
    const tangent = trackCurve.getTangentAt(0);
    const normal = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();
    
    const planeGeom = new THREE.PlaneGeometry(8, 1);
    const planeMat = new THREE.MeshPhongMaterial({ map: texture });
    const plane = new THREE.Mesh(planeGeom, planeMat);
    
    plane.position.copy(pos);
    plane.position.add(normal.clone().multiplyScalar(0)); // center
    plane.position.y = 0.1;
    
    // Rotate to align with track
    plane.rotation.y = Math.atan2(tangent.x, tangent.z);
    
    return plane;
}
```

### Kerbs

Kerbs are at the edges of the track, especially on curves. They're red and white stripes.

```javascript
function createKerbs() {
    // Place kerbs at intervals along the track
    const kerbs = new THREE.Group();
    
    const numKerbs = 50;
    for (let i = 0; i < numKerbs; i++) {
        const t = i / numKerbs;
        const pos = trackCurve.getPointAt(t);
        const tangent = trackCurve.getTangentAt(t);
        const normal = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();
        
        // Left kerb
        const leftPos = pos.clone().add(normal.clone().multiplyScalar(4));
        const kerbGeom = new THREE.BoxGeometry(2, 0.1, 1);
        const kerbMat = new THREE.MeshPhongMaterial({ 
            color: i % 2 === 0 ? 0xff0000 : 0xffffff 
        });
        const kerb = new THREE.Mesh(kerbGeom, kerbMat);
        kerb.position.copy(leftPos);
        kerb.position.y = 0.1;
        // Rotate to follow track
        kerb.rotation.y = Math.atan2(tangent.x, tangent.z);
        kerbs.add(kerb);
    }
    
    return kerbs;
}
```

### Landscape

For the landscape, I need:
- A large ground plane (grass green)
- Trees (cone + cylinder)
- Maybe some simple buildings

```javascript
function createLandscape() {
    // Ground
    const groundGeom = new THREE.PlaneGeometry(500, 500);
    const groundMat = new THREE.MeshPhongMaterial({ color: 0x4a7c3f });
    const ground = new THREE.Mesh(groundGeom, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.05;
    scene.add(ground);
    
    // Trees
    for (let i = 0; i < 50; i++) {
        const tree = createTree();
        // Place randomly but not on the track
        const angle = Math.random() * Math.PI * 2;
        const radius = 20 + Math.random() * 100;
        const x = Math.cos(angle) * radius;
        const z = Math.sin(angle) * radius;
        
        // Check if not on track
        const trackPos = trackCurve.getPointAt(0);
        const distToTrack = trackCurve.getPointAt(0).distanceTo(new THREE.Vector3(x, 0, z));
        
        // Simple check: if far from track center, place it
        tree.position.set(x, 0, z);
        scene.add(tree);
    }
}

function createTree() {
    const tree = new THREE.Group();
    
    const trunkGeom = new THREE.CylinderGeometry(0.5, 0.7, 2);
    const trunkMat = new THREE.MeshPhongMaterial({ color: 0x8B4513 });
    const trunk = new THREE.Mesh(trunkGeom, trunkMat);
    trunk.position.y = 1;
    tree.add(trunk);
    
    const foliageGeom = new THREE.ConeGeometry(1.5, 3, 8);
    const foliageMat = new THREE.MeshPhongMaterial({ color: 0x228B22 });
    const foliage = new THREE.Mesh(foliageGeom, foliageMat);
    foliage.position.y = 3;
    tree.add(foliage);
    
    return tree;
}
```

Wait, I need to make sure trees don't spawn on the track. Let me check distance to the track curve:

```javascript
function isOnTrack(x, z) {
    for (let t = 0; t <= 1; t += 0.01) {
        const point = trackCurve.getPointAt(t);
        const dist = Math.sqrt((point.x - x)**2 + (point.z - z)**2);
        if (dist < 6) return true;
    }
    return false;
}
```

Actually, for simplicity, I'll just place trees far from the track or use a distance check.

### Sky

Three.js has a sky implementation. I can use `THREE.CubeTextureLoader` but since we can't use external resources, I'll create a simple sky with a gradient shader or just use a color.

Actually, since no external resources, let me use a simple approach:
- `scene.background = new THREE.Color(0x87CEEB)` for sky blue
- Or use a gradient with `THREE.CanvasTexture`

Actually, let me create a gradient sky using a canvas texture:

```javascript
const canvas = document.createElement('canvas');
canvas.width = 2;
canvas.height = 512;
const ctx = canvas.getContext('2d');
const gradient = ctx.createLinearGradient(0, 0, 0, 512);
gradient.addColorStop(0, '#1a6dd4');
gradient.addColorStop(0.7, '#87CEEB');
gradient.addColorStop(1, '#b0d4f1');
ctx.fillStyle = gradient;
ctx.fillRect(0, 0, 2, 512);

const skyTexture = new THREE.CanvasTexture(canvas);
scene.background = skyTexture;
```

Hmm, but for a cube sky, maybe I should just set a color and add fog.

Actually, for the sky, let me use a large sphere with a gradient material or just scene.background. Let me use scene.background = new THREE.Color(0x87CEEB) along with fog for depth.

Or, better yet, create a simple sky dome:

```javascript
const skyGeom = new THREE.SphereGeometry(200, 32, 15);
const skyMat = new THREE.ShaderMaterial({
    side: THREE.BackSide,
    uniforms: {
        topColor: { value: new THREE.Color(0x0077ff) },
        bottomColor: { value: new THREE.Color(0x87CEEB) }
    },
    vertexShader: `
        varying vec3 vWorldPosition;
        void main() {
            vec4 worldPosition = modelMatrix * vec4(position, 1.0);
            vWorldPosition = worldPosition.xyz;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
    `,
    fragmentShader: `
        uniform vec3 topColor;
        uniform vec3 bottomColor;
        varying vec3 vWorldPosition;
        void main() {
            float h = normalize(vWorldPosition).y;
            gl_FragColor = vec4(mix(bottomColor, topColor, max(h, 0.0)), 1.0);
        }
    `
});
const sky = new THREE.Mesh(skyGeom, skyMat);
scene.add(sky);
```

This is nice and doesn't need external resources.

### HUD

I'll use HTML/CSS for the HUD:

```html
<div id="hud">
    <div id="speed">120 km/h</div>
    <div id="lap">Lap 1/3</div>
    <div id="position">2nd</div>
</div>
```

```css
#hud {
    position: absolute;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    color: white;
    font-family: Arial, sans-serif;
    font-size: 24px;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
    display: flex;
    gap: 40px;
    background: rgba(0,0,0,0.4);
    padding: 10px 20px;
    border-radius: 10px;
}
```

### Camera

Chase camera behind the player car:

```javascript
function updateCamera() {
    const car = playerCar;
    const carPos = car.position;
    const carQuat = car.quaternion;
    
    // Camera behind car
    const cameraOffset = new THREE.Vector3(0, 4, -8);
    cameraOffset.applyQuaternion(carQuat);
    
    const desiredPos = carPos.clone().add(cameraOffset);
    
    // Smooth follow
    camera.position.lerp(desiredPos, 0.1);
    camera.lookAt(carPos);
}
```

Actually, I should use a more responsive chase camera:

```javascript
function updateCamera() {
    const car = cars[playerIndex];
    const carPos = new THREE.Vector3();
    car.getWorldPosition(carPos);
    
    // Camera position behind and above
    const cameraOffset = new THREE.Vector3(0, 5, -10);
    cameraOffset.applyAxisAngle(new THREE.Vector3(0, 1, 0), car.rotation.y);
    
    const desiredPos = carPos.clone().add(cameraOffset);
    
    // Smooth follow
    camera.position.lerp(desiredPos, 0.05);
    
    // Look at car
    const lookTarget = carPos.clone().add(new THREE.Vector3(0, 1, 0));
    camera.lookAt(lookTarget);
    
    // FOV for speed effect
    const speed = car.userData.speed || 0;
    camera.fov = 60 + speed * 0.2;
    camera.updateProjectionMatrix();
}
```

### Building

For buildings, I'll create simple box structures:

```javascript
function createBuilding(x, z) {
    const building = new THREE.Group();
    
    const height = 5 + Math.random() * 15;
    
    const bodyGeom = new THREE.BoxGeometry(5, height, 5);
    const bodyMat = new THREE.MeshPhongMaterial({ 
        color: new THREE.Color().setHSL(0.1 + Math.random() * 0.8, 0.3, 0.5) 
    });
    const body = new THREE.Mesh(bodyGeom, bodyMat);
    body.position.y = height / 2;
    building.add(body);
    
    // Windows
    for (let i = 0; i < 4; i++) {
        const windowGeom = new THREE.BoxGeometry(0.8, 0.8, 0.1);
        const windowMat = new THREE.MeshPhongMaterial({ color: 0xffffcc, emissive: 0xffffcc, emissiveIntensity: 0.3 });
        const window = new THREE.Mesh(windowGeom, windowMat);
        window.position.y = 2 + i * 2;
        window.position.z = 2.51;
        building.add(window);
    }
    
    building.position.set(x, 0, z);
    return building;
}
```

### Putting it all together

Let me now write the complete code. Let me be careful about:

1. Track generation with proper UVs
2. Car physics (simplified)
3. AI following and overtaking
4. Camera
5. HUD
6. Lap counting

### Lap Counting

To count laps, I need to detect when a car crosses the start/finish line.

```javascript
// Track crossings of the start line
// Each car has a lastProgress value
// When a car's progress goes from near-1 to near-0 (or wraps), it crosses the line

function updateLapCount(car, dt) {
    if (car.progress < car.lastProgress - 0.5) {
        // Crossed the line
        if (car === playerCar) {
            lapCount++;
            if (lapCount > 3) {
                // Race finished
            }
        }
        car.lap++;
    }
    car.lastProgress = car.progress;
}
```

Hmm, but I need to track lap for each car.

Actually, for the HUD, I need the player's lap (1-3) and position.

### Race Position

Position is determined by lap count + progress. Cars with more laps are ahead. If same lap, higher progress is ahead.

```javascript
function updateRacePosition() {
    const standings = cars.map((car, index) => ({
        index,
        totalProgress: car.lap + car.progress
    }));
    standings.sort((a, b) => b.totalProgress - a.totalProgress);
    
    // Player position
    for (let i = 0; i < standings.length; i++) {
        if (standings[i].index === playerIndex) {
            playerPosition = i + 1;
            break;
        }
    }
}
```

### Speed

Speed is the current speed of the player's car, displayed in km/h.

```javascript
const speedKmh = Math.round(car.speed * 3.6);
// Assuming car.speed is in m/s
```

Wait, my car.speed is in units per second. Let me calibrate. If the track is ~200 units long and cars go at ~20 units/sec, that's about 0.1 laps/sec, so a lap takes 10 seconds. That seems reasonable for an arcade game.

Let me set car speeds in the range 20-30 units/sec, which would show as about 72-108 km/h in the HUD (multiply by 3.6). That seems fine.

Actually, let me just set the HUD speed to be proportional to the car's speed.

### Let me now write the full code

I need to be careful about several things:

1. The track curve needs to be closed (loop)
2. All meshes need proper materials
3. Lighting needs to be set up
4. The camera needs to properly follow

Let me define the track curve:

```javascript
const trackPoints = [
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(30, 0, -30),
    new THREE.Vector3(60, 0, 0),
    new THREE.Vector3(60, 0, 40),
    new THREE.Vector3(30, 0, 70),
    new THREE.Vector3(-10, 0, 60),
    new THREE.Vector3(-40, 0, 40),
    new THREE.Vector3(-40, 0, 10),
    new THREE.Vector3(-20, 0, -10),
];
const trackCurve = new THREE.CatmullRomCurve3(trackPoints, true, 'catmullrom', 0.5);
```

Wait, but the track needs to be wider and more interesting. Let me adjust.

Let me go with a more interesting shape:

```javascript
const trackPoints = [
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(40, 0, -20),
    new THREE.Vector3(80, 0, 10),
    new THREE.Vector3(70, 0, 60),
    new THREE.Vector3(30, 0, 80),
    new THREE.Vector3(-20, 0, 70),
    new THREE.Vector3(-50, 0, 40),
    new THREE.Vector3(-40, 0, 0),
    new THREE.Vector3(-10, 0, -20),
];
```

Hmm actually the CatmullRomCurve3 with closed=true might make the loop very smooth. Let me check if the points are far enough apart for a nice track.

Let me also think about the track width. I'll use 8 units wide track.

For the kerbs, I'll place them at curve edges. I can create kerbs as elongated boxes placed along the track edge.

Let me consider using THREE.CurvePath or just CatmullRomCurve3.

Actually, let me just code it up and see.

For the start/finish line, I'll create a plane with a checkerboard texture generated via canvas, placed at progress 0 on the track.

Let me now write the complete file. This will be a large file, so let me structure it well.

Actually, let me reconsider the track. Using CatmullRomCurve3 with closed=true, the track will be a smooth loop. I'll generate geometry by creating a ribbon mesh.

Let me code this step by step:

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Racing Game</title>
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { overflow: hidden; font-family: Arial, sans-serif; }
    canvas { display: block; }
    
    #hud {
        position: absolute;
        bottom: 30px;
        left: 50%;
        transform: translateX(-50%);
        display: flex;
        gap: 30px;
        align-items: center;
        background: rgba(0,0,0,0.6);
        padding: 15px 30px;
        border-radius: 12px;
        color: white;
        font-size: 20px;
        font-weight: bold;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.8);
        pointer-events: none;
    }
    
    .hud-item {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .hud-label {
        font-size: 14px;
        color: rgba(255,255,255,0.7);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .hud-value {
        font-size: 28px;
        color: #ffcc00;
    }
    
    #position-value {
        color: #00ff88;
    }
    
    #lap-value {
        color: #66bbff;
    }
</style>
</head>
<body>
<div id="hud">
    <div class="hud-item">
        <span class="hud-label">Speed</span>
        <span class="hud-value" id="speed-value">0</span>
        <span class="hud-label">km/h</span>
    </div>
    <div class="hud-item">
        <span class="hud-label">Lap</span>
        <span class="hud-value" id="lap-value">1/3</span>
    </div>
    <div class="hud-item">
        <span class="hud-label">Pos</span>
        <span class="hud-value" id="position-value">1st</span>
    </div>
</div>

<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// ... game code
</script>
</body>
</html>
```

Now the game code:

```javascript
// Scene setup
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x87CEEB);
scene.fog = new THREE.Fog(0x87CEEB, 200, 400);

const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);

// Lighting
const ambientLight = new THREE.AmbientLight(0x404040, 0.8);
scene.add(ambientLight);

const directionalLight = new THREE.DirectionalLight(0xffffff, 1.0);
directionalLight.position.set(50, 100, 50);
directionalLight.castShadow = true;
directionalLight.shadow.mapSize.width = 2048;
directionalLight.shadow.mapSize.height = 2048;
directionalLight.shadow.camera.near = 0.5;
directionalLight.shadow.camera.far = 500;
directionalLight.shadow.camera.left = -100;
directionalLight.shadow.camera.right = 100;
directionalLight.shadow.camera.top = 100;
directionalLight.shadow.camera.bottom = -100;
scene.add(directionalLight);

// =========== TRACK ===========

// ... track code

// =========== CARS ===========

// ... car code

// =========== ANIMATION ===========

// ...
```

Let me write the complete code now. This is going to be long.

Actually, let me think about the track geometry more carefully.

**Track Geometry:**

I'll generate the track as a flat mesh using vertices along the curve. The track surface should be at y=0.05 (slightly above ground).

```javascript
function createTrackGeometry() {
    const segments = 300;
    const width = 8;
    
    const vertices = [];
    const uvs = [];
    const indices = [];
    
    for (let i = 0; i <= segments; i++) {
        const t = i / segments;
        const point = trackCurve.getPointAt(t);
        const tangent = trackCurve.getTangentAt(t);
        // Perpendicular vector in XZ plane
        const normal = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();
        
        const left = point.clone().add(normal.clone().multiplyScalar(width / 2));
        const right = point.clone().add(normal.clone().multiplyScalar(-width / 2));
        
        vertices.push(left.x, 0.05, left.z);
        vertices.push(right.x, 0.05, right.z);
        
        uvs.push(t * 10, 0);
        uvs.push(t * 10, 1);
        
        if (i < segments) {
            const a = i * 2;
            const b = i * 2 + 1;
            const c = (i + 1) * 2;
            const d = (i + 1) * 2 + 1;
            
            indices.push(a, b, c);
            indices.push(b, d, c);
        }
    }
    
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    geometry.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
    geometry.setIndex(indices);
    geometry.computeVertexNormals();
    
    return geometry;
}
```

For the track texture, I'll create a canvas with a racing surface pattern:

```javascript
function createTrackTexture() {
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 64;
    const ctx = canvas.getContext('2d');
    
    // Asphalt
    ctx.fillStyle = '#333333';
    ctx.fillRect(0, 0, 256, 64);
    
    // Lighter grey for some texture
    for (let i = 0; i < 500; i++) {
        ctx.fillStyle = `rgba(${80 + Math.random() * 40}, ${80 + Math.random() * 40}, ${80 + Math.random() * 40}, 0.3)`;
        ctx.fillRect(Math.random() * 256, Math.random() * 64, 2, 2);
    }
    
    // Edge lines
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, 256, 2);
    ctx.fillRect(0, 62, 256, 2);
    
    const texture = new THREE.CanvasTexture(canvas);
    texture.wrapS = THREE.RepeatWrapping;
    texture.repeat.set(20, 1);
    
    return texture;
}
```

For the start/finish line:

```javascript
function createStartFinishLine() {
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 64;
    const ctx = canvas.getContext('2d');
    
    // Checkerboard pattern
    const cellSize = 16;
    for (let y = 0; y < 4; y++) {
        for (let x = 0; x < 16; x++) {
            ctx.fillStyle = (x + y) % 2 === 0 ? '#fff' : '#000';
            ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
        }
    }
    
    const texture = new THREE.CanvasTexture(canvas);
    
    // Position at start of track
    const pos = trackCurve.getPointAt(0);
    const tangent = trackCurve.getTangentAt(0);
    const normal = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();
    
    const startGeom = new THREE.PlaneGeometry(8, 1);
    const startMat = new THREE.MeshPhongMaterial({ map: texture });
    const start = new THREE.Mesh(startGeom, startMat);
    
    start.position.copy(pos);
    start.position.y = 0.06;
    
    // Rotate to face along the track
    const angle = Math.atan2(tangent.x, tangent.z);
    start.rotation.y = angle;
    
    return start;
}
```

Wait, the plane needs to be oriented so the checkerboard is visible. Since the track is in XZ plane and the plane is in XY by default, I need to rotate it to be horizontal.

Actually, THREE.PlaneGeometry in three.js is in XY plane. To make it lie flat (XZ plane), rotate -90 degrees around X.

But I also need it oriented along the track. Let me use lookAt or the rotation approach.

Better approach:
```javascript
start.rotation.x = -Math.PI / 2;  // Lay flat
start.rotation.y = angle;  // Rotate to match track direction
```

Hmm, rotations are tricky. Let me use `lookAt`:

```javascript
start.lookAt(pos.clone().add(tangent));
start.rotateX(-Math.PI / 2);  // Lay flat
```

Actually, let me use a simple approach with explicit rotations:

```javascript
// Create plane in XZ plane
start.rotation.x = -Math.PI / 2;
// Now rotate around Y to align with tangent
// The plane's local X axis should align with the track normal
// and local Y should align with tangent

// Better: use quaternion
const quaternion = new THREE.Quaternion();
const up = new THREE.Vector3(0, 1, 0);
const mat4 = new THREE.Matrix4();
mat4.lookAt(new THREE.Vector3(), tangent, up);
// mat4.lookAt gives -Z pointing to target, but we want the plane
// to be perpendicular to the track surface... 

// Actually, let me just compute it differently.
// The plane should be a horizontal strip crossing the track.
// Its long dimension (width) should be perpendicular to the track.
// Its short dimension (height in plane coords) should be along the track.

// Create the plane geometry manually - a simple quad
const w = 8; // width of track
const h = 1; // width of the line
const geo = new THREE.PlaneGeometry(w, h);
const mat = new THREE.MeshBasicMaterial({ color: 0xffffff });

// The default plane is xy. We need to rotate to xz, then align with track.
// PlaneGeometry default is in XY plane. To make it in XZ plane (facing up), rotate -90° around X.
// Then to align with the track, rotate around Y.

const mesh = new THREE.Mesh(geo, mat);
mesh.rotation.x = -Math.PI / 2;
mesh.rotation.y = angle;
mesh.position.set(pos.x, 0.1, pos.z);
```

This should work for placing the start line.

OK, let me just plug in the values and handle it.

Actually, let me simplify by using a small plane for the start line with a BoxGeometry or simple MeshBasicMaterial.

Let me use a different approach: create a checkerboard texture on a box that is slightly elevated.

You know what, let me just create something that works. I'll create the start line as a strip of small boxes:

```javascript
function createStartFinishLine() {
    const group = new THREE.Group();
    const pos = trackCurve.getPointAt(0);
    const tangent = trackCurve.getTangentAt(0);
    const normal = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();
    const angle = Math.atan2(tangent.x, tangent.z);
    
    // Create a canvas with checkerboard
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 32;
    const ctx = canvas.getContext('2d');
    const cellSize = 16;
    for (let y = 0; y < 2; y++) {
        for (let x = 0; x < 16; x++) {
            ctx.fillStyle = (x + y) % 2 === 0 ? '#ffffff' : '#000000';
            ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
        }
    }
    
    const texture = new THREE.CanvasTexture(canvas);
    const geom = new THREE.PlaneGeometry(8, 1);
    const mat = new THREE.MeshPhongMaterial({ map: texture });
    const plane = new THREE.Mesh(geom, mat);
    
    plane.position.copy(pos);
    plane.position.y = 0.08;
    
    // Rotate to lie flat and align with track
    plane.rotation.x = -Math.PI / 2;
    plane.rotation.y = angle;
    
    return plane;
}
```

Actually, when a plane is rotated -90° around X, its local X becomes world X, and local Y becomes world -Z. So the texture would be in the XZ plane with the checkerboard facing up.

After that, rotating around Y aligns it with the track.

Actually, the UV mapping will be correct because the texture is in the plane's local coordinates. After rotation to XZ plane, the UV stays with the geometry. So the checkerboard will lie flat on the track.

But I want the checkerboard to be perpendicular to the track direction. Since the plane's local width is 8 (track width) and the texture's width is 8 units, the pattern will span across the track. The height of the plane (1 unit) goes along the track direction.

The texture is 256x32, so the checkerboard cells are 16x16 pixels, meaning there are 16 cells across the 8-unit width. That's 0.5 unit per cell. And 2 cells along the track direction.

That looks good.

OK, let me just code the whole thing now. I'll be concise but thorough.

Here's my plan for the code structure:

```
1. Import three.js
2. Scene, camera, renderer setup
3. Lighting
4. Track creation
   - Define curve
   - Create track geometry
   - Add texture
   - Add kerbs
   - Add start/finish line
5. Landscape
   - Ground
   - Trees
   - Buildings
   - Sky
6. Cars (4 cars: 1 player + 3 rivals)
   - Create car meshes
   - Store with AI data
7. AI system
   - Initialize car AI data
   - Update function for each car
   - Overtaking
8. Game state
   - Lap tracking
   - Race position
9. Camera
   - Chase camera
10. HUD
11. Animation loop
```

Let me code each part.

Actually, for the sky, I'll use a simple gradient shader. Let me use `scene.background` with a canvas texture instead, which is simpler.

```javascript
// Sky
const skyCanvas = document.createElement('canvas');
skyCanvas.width = 2;
skyCanvas.height = 512;
const skyCtx = skyCanvas.getContext('2d');
const gradient = skyCtx.createLinearGradient(0, 0, 0, 512);
gradient.addColorStop(0, '#1a6dd4');
gradient.addColorStop(0.6, '#87CEEB');
gradient.addColorStop(1, '#c8e8f8');
skyCtx.fillStyle = gradient;
skyCtx.fillRect(0, 0, 2, 512);
scene.background = new THREE.CanvasTexture(skyCanvas);
```

But this will only have the texture as background, not a skybox. Actually, `scene.background` with a texture will stretch it, which won't look great for a sky.

Let me use `scene.background = new THREE.Color(0x87CEEB)` and add some clouds.

Or use a hemisphere light and a sky color:
```javascript
scene.background = new THREE.Color(0x87CEEB);
scene.fog = new THREE.Fog(0x87CEEB, 200, 400);
```

Now for the fog and background, cars far away will fade to sky color. That's fine.

Let me also add some simple clouds using sprites or planes.

Actually, let me keep it simple and just use a nice sky color and add some clouds as flat 3D shapes.

OK, let me just code it. I'll make a clean, well-structured implementation.

Let me define the complete car creation function:

```javascript
function createCar(color) {
    const car = new THREE.Group();
    
    // Body
    const bodyGeom = new THREE.BoxGeometry(2, 0.6, 4);
    const bodyMat = new THREE.MeshPhongMaterial({ 
        color: color, 
        specular: 0x444444, 
        shininess: 30 
    });
    const body = new THREE.Mesh(bodyGeom, bodyMat);
    body.position.y = 0.5;
    body.castShadow = true;
    car.add(body);
    
    // Cabin
    const cabinGeom = new THREE.BoxGeometry(1.6, 0.5, 2);
    const cabinMat = new THREE.MeshPhongMaterial({ 
        color: 0x1e3a5f, 
        specular: 0x222222, 
        shininess: 20 
    });
    const cabin = new THREE.Mesh(cabinGeom, cabinMat);
    cabin.position.set(0, 0.9, -0.3);
    cabin.castShadow = true;
    car.add(cabin);
    
    // Wheels
    const wheelGeom = new THREE.CylinderGeometry(0.35, 0.35, 0.25, 16);
    wheelGeom.rotateZ(Math.PI / 2);
    const wheelMat = new THREE.MeshPhongMaterial({ color: 0x222222, specular: 0x111111 });
    
    const wheelPositions = [
        [-0.85, 0.35, 1.1],  // front-left
        [0.85, 0.35, 1.1],   // front-right
        [-0.85, 0.35, -1.1], // rear-left
        [0.85, 0.35, -1.1]   // rear-right
    ];
    
    const wheels = [];
    wheelPositions.forEach(pos => {
        const wheel = new THREE.Mesh(wheelGeom, wheelMat);
        wheel.position.set(...pos);
        wheel.rotation.y = 0; // Cylinder already rotated
        wheel.castShadow = true;
        car.add(wheel);
        wheels.push(wheel);
    });
    
    // Headlights
    const headlightGeom = new THREE.BoxGeometry(0.3, 0.25, 0.1);
    const headlightMat = new THREE.MeshPhongMaterial({ 
        color: 0xffffcc, 
        emissive: 0xffffcc, 
        emissiveIntensity: 0.3 
    });
    
    [[-0.55, 0.6, 2], [0.55, 0.6, 2]].forEach(pos => {
        const headlight = new THREE.Mesh(headlightGeom, headlightMat);
        headlight.position.set(...pos);
        car.add(headlight);
    });
    
    // Rear lights
    const taillightMat = new THREE.MeshPhongMaterial({ 
        color: 0xff0000, 
        emissive: 0xff0000, 
        emissiveIntensity: 0.2 
    });
    
    [[-0.55, 0.6, -2], [0.55, 0.6, -2]].forEach(pos => {
        const taillight = new THREE.Mesh(headlightGeom, taillightMat);
        taillight.position.set(...pos);
        car.add(taillight);
    });
    
    // Store wheels for animation
    car.userData.wheels = wheels;
    car.userData.speed = 0;
    car.userData.progress = 0;
    car.userData.laneOffset = 0;
    car.userData.targetLaneOffset = 0;
    car.userData.baseSpeed = 25; // units per second
    car.userData.lap = 0;
    car.userData.overtakeCooldown = 0;
    car.userData.isOvertaking = false;
    
    return car;
}
```

Alright, let me write the complete code now. I need to be thorough and cover all the requirements.

For the AI, let me define a simple but effective approach:

Each car has:
- `progress`: float 0-1 around the track
- `baseSpeed`: desired speed
- `currentSpeed`: actual speed
- `laneOffset`: lateral offset from center
- `targetLaneOffset`: for lane changes

The update function:
1. Adjust speed based on curvature ahead
2. Check for cars ahead and react
3. Move along the track
4. Update position and rotation
5. Update wheel spin

Let me implement this.

For racing line, I want the cars to follow the natural racing line on curves. I can approximate this by using a lateral offset in curves.

Actually, for simplicity, I'll have cars follow the center line + small offset.

Let me finalize the AI:

```javascript
function updateCarAI(car, dt) {
    const trackLen = trackCurve.getLength();
    
    // Check for cars ahead
    let carAhead = null;
    let minDist = Infinity;
    
    for (const other of cars) {
        if (other === car) continue;
        
        let dist = other.userData.progress - car.userData.progress;
        if (dist < 0) dist += 1;
        
        if (dist > 0 && dist < minDist) {
            minDist = dist;
            carAhead = other;
        }
    }
    
    // Curvature-based speed adjustment
    const t = car.userData.progress;
    const tangent = trackCurve.getTangentAt(t);
    const nextT = Math.min(t + 0.01, 1);
    const nextTangent = trackCurve.getTangentAt(nextT);
    const curvature = tangent.angleTo(nextTangent) / 0.01;
    
    let targetSpeed = car.userData.baseSpeed / (1 + curvature * 2);
    targetSpeed = Math.max(10, Math.min(car.userData.baseSpeed, targetSpeed));
    
    // Overtaking logic
    if (carAhead && minDist < 0.08) {
        const distToCar = minDist * trackLen;
        
        // If too close, slow down
        if (distToCar < 3) {
            targetSpeed = Math.min(targetSpeed, carAhead.userData.currentSpeed * 0.8);
        }
        
        // If faster and we want to overtake
        if (car.userData.currentSpeed > carAhead.userData.currentSpeed && 
            minDist < 0.05 && 
            car.userData.overtakeCooldown <= 0) {
            
            // Change lane
            const side = Math.random() > 0.5 ? 1 : -1;
            car.userData.targetLaneOffset = side * 0.7;
            car.userData.isOvertaking = true;
            car.userData.overtakeCooldown = 3;
        }
    }
    
    // Return to center after overtaking
    if (car.userData.isOvertaking) {
        car.userData.overtakeCooldown -= dt;
        if (car.userData.overtakeCooldown <= 0) {
            car.userData.targetLaneOffset = 0;
            if (Math.abs(car.userData.laneOffset) < 0.05) {
                car.userData.isOvertaking = false;
            }
        }
    }
    
    // Update speed
    car.userData.currentSpeed = THREE.MathUtils.lerp(
        car.userData.currentSpeed || targetSpeed,
        targetSpeed,
        dt * 3
    );
    
    // Update progress
    car.userData.progress = (car.userData.progress + car.userData.currentSpeed * dt / trackLen) % 1;
    
    // Update lane offset
    car.userData.laneOffset = THREE.MathUtils.lerp(
        car.userData.laneOffset,
        car.userData.targetLaneOffset,
        dt * 2
    );
    
    // Get position on track
    const pos = trackCurve.getPointAt(car.userData.progress);
    const tangentAt = trackCurve.getTangentAt(car.userData.progress);
    const normal = new THREE.Vector3(-tangentAt.z, 0, tangentAt.x).normalize();
    
    // Set car position
    const targetPos = pos.clone().add(normal.clone().multiplyScalar(car.userData.laneOffset * 2.5));
    targetPos.y = car.userData.progress < 0.5 ? 0.4 : 0.4;
    car.position.set(targetPos.x, targetPos.y, targetPos.z);
    
    // Face direction of travel
    const angle = Math.atan2(tangentAt.x, tangentAt.z);
    car.rotation.y = angle;
    
    // Wheel spin
    car.userData.wheels.forEach(w => {
        w.rotation.x += car.userData.currentSpeed * dt * 0.5;
    });
}
```

Wait, there's a problem with laneOffset. When the car is on a curve, having a lateral offset perpendicular to the tangent may cause the car to drift off the track. This is fine as long as the offset is small.

The track width is 8, so offset of 0.7 * 2.5 = 1.75 units from center. That's within the track.

Now, for the player car, I'll use the same AI but track its lap and position.

Actually, the player car should also drive itself... Let me re-read the requirements.

"all cars are driven by an AI that follows the racing line around the track"

So yes, all cars are AI-driven. The player camera follows one specific car.

Let me make the first car the "player" car (red, in the center of the starting grid).

Starting positions:
- Player car: progress 0, laneOffset 0
- Rival 1: progress 0.02, laneOffset -1
- Rival 2: progress 0.02, laneOffset 1
- Rival 3: progress 0.04, laneOffset 0

Actually, let me place them staggered:
- Player: progress 0, laneOffset 0
- Rival 1: progress 0.015, laneOffset 0.6
- Rival 2: progress 0.03, laneOffset -0.6
- Rival 3: progress 0.045, laneOffset 0

This way they start close together and immediately begin racing.

For lap counting, I'll check when the progress wraps from >0.9 to <0.1.

Let me now put this all together. I need to be careful with the track generation and make sure everything works.

Actually, let me reconsider the track. With CatmullRomCurve3 and closed=true, the track will be smooth. But points that are too close together will make a very tight track. Let me test with some points.

Given the track dimensions, let me define track points that create a nice racing circuit.

```javascript
const trackPoints = [
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(30, 0, -25),
    new THREE.Vector3(60, 0, 0),
    new THREE.Vector3(70, 0, 30),
    new THREE.Vector3(55, 0, 60),
    new THREE.Vector3(25, 0, 70),
    new THREE.Vector3(-10, 0, 60),
    new THREE.Vector3(-35, 0, 40),
    new THREE.Vector3(-40, 0, 10),
    new THREE.Vector3(-25, 0, -10),
];
```

This creates a nice circuit with some curves.

Wait, let me make sure the track is closed. With `new THREE.CatmullRomCurve3(trackPoints, true)`, it's closed.

Now the track length will be computed by three.js internally.

For the racing cars, I need to initialize their speeds to reasonable values.

Let me also handle the `car.userData.currentSpeed` initialization properly.

Here's a more refined approach for initialization:

```javascript
function initCar(car, progress, laneOffset, speed) {
    car.userData.progress = progress;
    car.userData.laneOffset = laneOffset;
    car.userData.targetLaneOffset = laneOffset;
    car.userData.baseSpeed = speed;
    car.userData.currentSpeed = speed;
    car.userData.overtakeCooldown = 0;
    car.userData.isOvertaking = false;
    car.userData.lap = 0;
    car.userData.lastProgress = progress;
    
    // Set initial position
    const pos = getTrackPosition(progress, laneOffset);
    car.position.set(pos.x, pos.y, pos.z);
    const tangent = trackCurve.getTangentAt(progress);
    car.rotation.y = Math.atan2(tangent.x, tangent.z);
}

function getTrackPosition(progress, laneOffset) {
    const pos = trackCurve.getPointAt(progress);
    const tangent = trackCurve.getTangentAt(progress);
    const normal = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();
    
    return pos.clone().add(normal.multiplyScalar(laneOffset * 2.5));
}
```

OK, I think I have enough design. Let me write the complete file now.

One more thing: the HUD needs to update. I'll use `document.getElementById` to update the values.

For the speed in the HUD, I'll use `Math.round(car.userData.currentSpeed * 3.6)` to get km/h. With baseSpeed around 25-35, that gives 90-126 km/h, which is reasonable.

Actually, let me scale it a bit. `currentSpeed * 3.6` is in "units per hour" if currentSpeed is in units per second. But units aren't kilometers, they're just game units. So let me use `Math.round(car.userData.currentSpeed * 4)` for display, or just display `Math.round(car.userData.currentSpeed * 3.6)` and accept it's a game number.

Let me use `Math.round(car.userData.currentSpeed * 3.6)` and display as km/h.

For lap counting:
```javascript
// In car update
if (car.userData.progress < car.userData.lastProgress - 0.5) {
    // Crossed start/finish line
    car.userData.lap++;
    car.userData.lapText = car.userData.lap;
}
car.userData.lastProgress = car.userData.progress;
```

Hmm, this detects when progress wraps from near 1 to near 0. Since progress goes from 0 to 1, wrapping means we crossed the start line.

Actually, `car.userData.lastProgress` should store the previous frame's progress. If the car crosses from 0.9 to 0.1, the wrap detection `0.1 < 0.9 - 0.5` is true, so we count a lap.

But what if progress goes from 0.95 to 0.9 normally (slowing down)? We don't want to count that as a lap. The wrap detection `0.9 < 0.95 - 0.5 = 0.45` would be false. Good.

What if car is at 0.02 and goes to 0.98 (driving backward)? Not possible since cars move forward.

OK, this works.

For race position:
```javascript
function updateRacePosition() {
    // Sort cars by (lap, progress)
    const standings = carList.map((car, index) => ({
        index,
        totalProgress: car.userData.lap + car.userData.progress
    }));
    standings.sort((a, b) => b.totalProgress - a.totalProgress);
    
    for (let i = 0; i < standings.length; i++) {
        if (standings[i].index === 0) {
            position = i + 1;
            break;
        }
    }
}
```

Wait, the total progress for lap 0 goes from 0 to 1, lap 1 from 1 to 2, etc. So a car on lap 0 with progress 0.9 has total progress 0.9. A car on lap 1 with progress 0.1 has total progress 1.1. So it works correctly.

But what if some cars are on lap 2 and others on lap 0? The total progress approach handles this well:
- Car on lap 0, progress 0.9 → 0.9
- Car on lap 1, progress 0.1 → 1.1
- Car on lap 1, progress 0.0 → 1.0

So the car on lap 1 with progress 0.1 is ahead. Good.

For the first lap, I'll use progress directly since all cars start at progress around 0.

Actually, I need to initialize the cars' progress before the race starts. Let me place them at the starting position.

The starting position is at progress 0. For a grid start:
- Player: progress 0, laneOffset 0
- Rival 1: progress -0.01 (i.e., 0.99), laneOffset 0.8
- ...

Actually, negative progress wraps to 0.99. Let me use:
- Player: progress 0, laneOffset 0
- Rival 1: progress 0.01, laneOffset 0.8
- Rival 2: progress 0.01, laneOffset -0.8
- Rival 3: progress 0.02, laneOffset 0

Hmm, but then they're already slightly ahead of the player. Let me offset the starting progress:
- Player: progress 0, laneOffset 0
- Rival 1: progress 0.005, laneOffset 0.8
- Rival 2: progress 0.005, laneOffset -0.8
- Rival 3: progress 0.01, laneOffset 0

This places them slightly ahead on the grid, which simulates a grid start.

OK, I think I've designed enough. Let me write the actual code.

One issue: the `progress` property starts at some value and the AI updates it. But if the car starts at progress 0 with a lane offset, the initial position should be computed correctly.

Also, for the player car, I want to track which car is the "player". Let me just set `playerCar = cars[0]`.

Let me code it now. I'll try to be clean but the code will be long.

Actually, one more optimization: for the AI following and overtaking, I should compute things simply.

Let me define the cars array with userData properly.

Here's my complete implementation. Let me write it:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>AI Racing</title>
    <style>
        * { margin: 0; padding: 0; }
        body { overflow: hidden; background: #000; font-family: 'Segoe UI', Arial, sans-serif; }
        canvas { display: block; }
        
        #hud {
            position: absolute;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 30px;
            align-items: center;
            background: rgba(0,0,0,0.7);
            padding: 12px 30px;
            border-radius: 15px;
            color: white;
            pointer-events: none;
            border: 1px solid rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            font-size: 18px;
        }
        
        .hud-item {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .hud-label {
            font-size: 13px;
            color: rgba(255,255,255,0.6);
            text-transform: uppercase;
            letter-spacing: 2px;
        }
        
        .hud-value {
            font-size: 32px;
            font-weight: bold;
            color: #fff;
            text-shadow: 0 0 10px rgba(255,255,255,0.3);
        }
        
        #speed-value { color: #00ff88; }
        #lap-value { color: #66bbff; }
        #position-value { color: #ffcc00; }
        
        .separator {
            width: 1px;
            height: 40px;
            background: rgba(255,255,255,0.2);
        }
    </style>
</head>
<body>
    <div id="hud">
        <div class="hud-item">
            <span class="hud-label">Speed</span>
            <span class="hud-value" id="speed-value">0</span>
            <span style="font-size:14px;color:rgba(255,255,255,0.6)">km/h</span>
        </div>
        <div class="separator"></div>
        <div class="hud-item">
            <span class="hud-label">Lap</span>
            <span class="hud-value" id="lap-value">1/3</span>
        </div>
        <div class="separator"></div>
        <div class="hud-item">
            <span class="hud-label">Pos</span>
            <span class="hud-value" id="position-value">1st</span>
        </div>
    </div>
    
    <script type="module">
    import * as THREE from 'three';
    
    // ... all the game code here
    </script>
</body>
</html>
```

Now let me write the complete game code. This is going to be a large file.

Actually, let me first check: does the requirement say "player car is also AI-driven"? Let me re-read:

"all cars are driven by an AI that follows the racing line around the track"

Yes. So all cars are AI-driven. The camera follows one car (let's call it the "player" car), and the HUD shows that car's status.

This simplifies things - I don't need user input at all.

Let me now write the full implementation.

One more consideration: the track texture. Since I can't use external images, I'll generate all textures with canvas.

For the track, I'll create an asphalt texture with canvas.

For the start line, a checkerboard pattern.

For the environment (trees, buildings), simple colored materials.

Let me write it all.

Actually, one issue I realize: with `trackCurve.getPointAt(t)`, t is in the range [0, 1]. But `getPointAt` expects a parameter where 0 <= t <= 1, and it returns a point on the curve. For a closed curve, `getPointAt(0)` = `getPointAt(1)` = the starting point.

So when a car's progress is 0.999 and we add `dt * speed / trackLength` to make it cross 1.0, it wraps to 0.0. Good.

But there's a performance concern: `trackCurve.getPointAt(t)` uses arc-length params, so it should be O(1) or similar. Actually, three.js's Curve.getPointAt uses arc length param computed with `getUtoTmapping` which internally calls `getLengths()` which is O(n). This could be expensive if called very frame for every car.

To avoid this, I can precompute the curve points and their corresponding parameters. Or use `getPoint` instead, which is O(1) but doesn't account for arc length.

Actually, three.js caches the arc length on first call. From the docs:
"getPointAt( u ) for a distance u (0 ... 1)."
Internally, it uses `getUtoTmapping(u)` to convert u (0-1) to t (0-1), then calls `getPoint(t)`.

The `getUtoTmapping` uses the curve's length and precomputed lookup table. This is efficient enough.

OK, let me just use it.

Actually, there's one more issue. `trackCurve.getTangentAt(t)` also uses `getUtoTmapping`.

Fine, this should work efficiently.

Let me now write the actual code. I'll aim for a complete, working implementation.

Let me write the full code:

```javascript
import * as THREE from 'three';

// ===== SCENE SETUP =====
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x87CEEB);
scene.fog = new THREE.Fog(0x87CEEB, 200, 500);

const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(0, 30, -40);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);

// ===== LIGHTING =====
const ambientLight = new THREE.AmbientLight(0x87CEEB, 0.6);
scene.add(ambientLight);

const hemisphereLight = new THREE.HemisphereLight(0x87CEEB, 0x4a7c3f, 0.8);
scene.add(hemisphereLight);

const sunLight = new THREE.DirectionalLight(0xffffee, 1.2);
sunLight.position.set(100, 80, 50);
sunLight.castShadow = true;
sunLight.shadow.mapSize.width = 2048;
sunLight.shadow.mapSize.height = 2048;
sunLight.shadow.camera.left = -80;
sunLight.shadow.camera.right = 80;
sunLight.shadow.camera.top = 80;
sunLight.shadow.camera.bottom = -80;
sunLight.shadow.camera.near = 1;
sunLight.shadow.camera.far = 300;
scene.add(sunLight);

// ===== TRACK =====
const trackPoints = [
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(30, 0, -25),
    new THREE.Vector3(60, 0, 0),
    new THREE.Vector3(70, 0, 30),
    new THREE.Vector3(55, 0, 60),
    new THREE.Vector3(25, 0, 70),
    new THREE.Vector3(-10, 0, 60),
    new THREE.Vector3(-35, 0, 40),
    new THREE.Vector3(-40, 0, 10),
    new THREE.Vector3(-25, 0, -10),
];
const trackCurve = new THREE.CatmullRomCurve3(trackPoints, true, 'catmullrom', 0.5);
const trackLength = trackCurve.getLength();

// ===== GROUND =====
const groundGeom = new THREE.PlaneGeometry(600, 600);
const groundMat = new THREE.MeshPhongMaterial({ color: 0x4a7c3f, side: THREE.DoubleSide });
const ground = new THREE.Mesh(groundGeom, groundMat);
ground.rotation.x = -Math.PI / 2;
ground.position.y = -0.1;
ground.receiveShadow = true;
scene.add(ground);

// ===== TRACK MESH =====
// Create track geometry
function createTrackMesh() {
    const segments = 400;
    const trackWidth = 8;
    
    const positions = [];
    const uvs = [];
    const indices = [];
    
    for (let i = 0; i <= segments; i++) {
        const t = i / segments;
        const point = trackCurve.getPointAt(t);
        const tangent = trackCurve.getTangentAt(t);
        const normal = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();
        
        const left = new THREE.Vector3(
            point.x + normal.x * trackWidth / 2,
            0.05,
            point.z + normal.z * trackWidth / 2
        );
        const right = new THREE.Vector3(
            point.x - normal.x * trackWidth / 2,
            0.05,
            point.z - normal.z * trackWidth / 2
        );
        
        positions.push(left.x, left.y, left.z);
        positions.push(right.x, right.y, right.z);
        
        uvs.push(i / segments * 20, 0);
        uvs.push(i / segments * 20, 1);
        
        if (i < segments) {
            const a = i * 2;
            const b = i * 2 + 1;
            const c = (i + 1) * 2;
            const d = (i + 1) * 2 + 1;
            
            indices.push(a, b, c);
            indices.push(b, d, c);
        }
    }
    
    const geom = new THREE.BufferGeometry();
    geom.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geom.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
    geom.setIndex(indices);
    geom.computeVertexNormals();
    
    // Create texture
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 64;
    const ctx = canvas.getContext('2d');
    
    // Asphalt
    ctx.fillStyle = '#333';
    ctx.fillRect(0, 0, 256, 64);
    
    // Noise
    for (let i = 0; i < 1000; i++) {
        const x = Math.random() * 256;
        const y = Math.random() * 64;
        const shade = 50 + Math.random() * 20;
        ctx.fillStyle = `rgba(${shade}, ${shade}, ${shade}, 0.3)`;
        ctx.fillRect(x, y, 1, 1);
    }
    
    // Edge lines
    ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
    ctx.fillRect(0, 0, 256, 2);
    ctx.fillRect(0, 62, 256, 2);
    
    // Center dashed line
    ctx.setLineDash([10, 10]);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, 32);
    ctx.lineTo(256, 32);
    ctx.stroke();
    
    const texture = new THREE.CanvasTexture(canvas);
    texture.wrapS = THREE.RepeatWrapping;
    texture.repeat.set(30, 1);
    
    const mat = new THREE.MeshPhongMaterial({ 
        map: texture, 
        side: THREE.DoubleSide,
        shininess: 5 
    });
    
    const mesh = new THREE.Mesh(geom, mat);
    mesh.receiveShadow = true;
    return mesh;
}

const trackMesh = createTrackMesh();
scene.add(trackMesh);

// ===== START/FINISH LINE =====
function createStartFinishLine() {
    // Create canvas with checkerboard
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 32;
    const ctx = canvas.getContext('2d');
    
    const cellSize = 16;
    for (let y = 0; y < 2; y++) {
        for (let x = 0; x < 16; x++) {
            ctx.fillStyle = (x + y) % 2 === 0 ? '#fff' : '#000';
            ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
        }
    }
    
    const texture = new THREE.CanvasTexture(canvas);
    
    const pos = trackCurve.getPointAt(0);
    const tangent = trackCurve.getTangentAt(0);
    const norm = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();
    
    // Create plane geometry
    const geom = new THREE.PlaneGeometry(8, 1);
    const mat = new THREE.MeshPhongMaterial({ map: texture, side: THREE.DoubleSide });
    const plane = new THREE.Mesh(geom, mat);
    
    plane.position.copy(pos);
    plane.position.add(norm.clone().multiplyScalar(0));
    plane.position.y = 0.08;
    
    // Rotate: default plane is XY, we want XZ (facing up), then align with track
    plane.quaternion.setFromEuler(new THREE.Euler(-Math.PI / 2, 0, 0));
    // Now position is XZ facing up, rotate around Y to align
    const angle = Math.atan2(tangent.x, tangent.z);
    plane.rotateY(angle);
    
    return plane;
}

scene.add(createStartFinishLine());

// ===== KERBS =====
function createKerbs() {
    const kerbGroup = new THREE.Group();
    const numKerbs = 60;
    
    for (let i = 0; i < numKerbs; i++) {
        const t = i / numKerbs;
        const pos = trackCurve.getPointAt(t);
        const tangent = trackCurve.getTangentAt(t);
        const normal = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();
        
        const color = i % 2 === 0 ? 0xff0000 : 0xffffff;
        const geom = new THREE.BoxGeometry(1.5, 0.08, 0.5);
        const mat = new THREE.MeshPhongMaterial({ color });
        
        // Left kerb
        const leftPos = pos.clone().add(normal.clone().multiplyScalar(4));
        const leftKerb = new THREE.Mesh(geom, mat);
        leftKerb.position.copy(leftPos);
        leftKerb.position.y = 0.06;
        leftKerb.rotation.y = Math.atan2(tangent.x, tangent.z);
        kerbGroup.add(leftKerb);
    }
    
    return kerbGroup;
}

// Add kerbs
const kerbs = createKerbs();
scene.add(kerbs);

// ===== LANDSCAPE =====
function createTree(x, z) {
    const tree = new THREE.Group();
    
    // Trunk
    const trunkGeom = new THREE.CylinderGeometry(0.4, 0.6, 2);
    const trunkMat = new THREE.MeshPhongMaterial({ color: 0x8B4513 });
    const trunk = new THREE.Mesh(trunkGeom, trunkMat);
    trunk.position.y = 1;
    trunk.castShadow = true;
    tree.add(trunk);
    
    // Foliage
    const foliage1 = new THREE.ConeGeometry(1.5, 2.5, 8);
    const foliageMat = new THREE.MeshPhongMaterial({ color: 0x228B22 });
    const foliage = new THREE.Mesh(foliage1, foliageMat);
    foliage.position.y = 3;
    foliage.castShadow = true;
    tree.add(foliage);
    
    const foliage2 = new THREE.ConeGeometry(1.2, 2, 8);
    const foliage2Mesh = new THREE.Mesh(foliage2, foliageMat);
    foliage2Mesh.position.y = 4.2;
    tree.add(foliage2Mesh);
    
    tree.position.set(x, 0, z);
    return tree;
}

// Place trees
function isOnTrack(x, z) {
    // Check distance to track at various parameters
    for (let t = 0; t <= 1; t += 0.02) {
        const point = trackCurve.getPointAt(t);
        const dist = Math.sqrt((point.x - x) ** 2 + (point.z - z) ** 2);
        if (dist < 12) return true;
    }
    return false;
}

// ... (place trees)

// ===== CARS =====
function createCar(color) {
    const car = new THREE.Group();
    
    // Body
    const bodyGeom = new THREE.BoxGeometry(2, 0.6, 4);
    const bodyMat = new THREE.MeshPhongMaterial({ 
        color: color, 
        specular: 0x444444, 
        shininess: 30 
    });
    const body = new THREE.Mesh(bodyGeom, bodyMat);
    body.position.y = 0.5;
    body.castShadow = true;
    car.add(body);
    
    // Cabin
    const cabinGeom = new THREE.BoxGeometry(1.5, 0.5, 2);
    const cabinMat = new THREE.MeshPhongMaterial({ 
        color: 0x1e3a5f, 
        specular: 0x222222, 
        shininess: 20 
    });
    const cabin = new THREE.Mesh(cabinGeom, cabinMat);
    cabin.position.set(0, 0.85, -0.3);
    cabin.castShadow = true;
    car.add(cabin);
    
    // Wheels
    const wheelGeom = new THREE.CylinderGeometry(0.35, 0.35, 0.25, 16);
    wheelGeom.rotateZ(Math.PI / 2);
    const wheelMat = new THREE.MeshPhongMaterial({ 
        color: 0x222222, 
        specular: 0x111111,
        shininess: 10
    });
    
    const wheelPositions = [
        [-0.85, 0.35, 1.15],
        [0.85, 0.35, 1.15],
        [-0.85, 0.35, -1.15],
        [0.85, 0.35, -1.15]
    ];
    
    const wheels = [];
    wheelPositions.forEach(pos => {
        const wheel = new THREE.Mesh(wheelGeom, wheelMat);
        wheel.position.set(...pos);
        wheel.castShadow = true;
        car.add(wheel);
        wheels.push(wheel);
    });
    
    // Headlights
    const headlightGeom = new THREE.BoxGeometry(0.4, 0.25, 0.1);
    const headlightMat = new THREE.MeshPhongMaterial({ 
        color: 0xffffcc, 
        emissive: 0xffffcc, 
        emissiveIntensity: 0.3 
    });
    
    [[-0.55, 0.6, 2], [0.55, 0.6, 2]].forEach(pos => {
        const light = new THREE.Mesh(headlightGeom, headlightMat);
        light.position.set(...pos);
        car.add(light);
    });
    
    // Tail lights
    const taillightMat = new THREE.MeshPhongMaterial({ 
        color: 0xff0000, 
        emissive: 0xff0000, 
        emissiveIntensity: 0.3 
    });
    
    [[-0.55, 0.6, -2], [0.55, 0.6, -2]].forEach(pos => {
        const light = new THREE.Mesh(headlightGeom, taillightMat);
        light.position.set(...pos);
        car.add(light);
    });
    
    // Store wheels
    car.userData.wheels = wheels;
    car.userData.currentSpeed = 0;
    car.userData.progress = 0;
    car.userData.laneOffset = 0;
    car.userData.targetLaneOffset = 0;
    car.userData.baseSpeed = 25 + Math.random() * 10;
    car.userData.overtakeCooldown = 0;
    car.userData.isOvertaking = false;
    car.userData.lap = 0;
    car.userData.lastProgress = 0;
    car.userData.currentSpeed = car.userData.baseSpeed;
    
    scene.add(car);
    return car;
}
```

OK, I realize this is getting very long. Let me just write it all out in one cohesive file. Let me complete the implementation.

I need to carefully handle:
1. Car initialization and starting position
2. AI update functions
3. Camera following
4. HUD updates

Let me be efficient and write a complete working implementation.

One more concern: the starting position for the cars. The start line is at progress 0. For a grid start, the cars should be positioned before the finish line. In motor racing, the grid starts behind the start line.

But since the start line IS at progress 0, and the cars are placed at progress ~0, they won't need to "enter" the track - they start there. This is fine for simplicity.

For the race, since all cars start at progress around 0, they'll complete one lap when they cross progress 1.0 back to 0.0. With a lap count of 3, the game will end when all cars reach lap 3.

Actually, I'll make the player car start at progress 0, with rivals slightly ahead. This way the player is at the back of the grid.

Let me now finalize the code...

Actually, I realize I should also add trees and buildings around the track for visual variety. Let me place them with some randomness but avoid the track.

For efficiency, I'll place 30 trees and 10 buildings.

The sky is blue, fog makes distant objects fade.

Let me write the complete code now. Given the complexity, I'll create a clean, well-commented file.

I'll also add some clouds using simple white shapes.

Actually, let me not add clouds to keep the code shorter. The sky color is enough.

Let me finalize. Here's my complete implementation:

Wait, I realize there might be an issue with the trackCurve.getPointAt and getTangentAt using different t values. getPointAt uses arc-length parameterization, while getTangentAt also does. So for a given t (0-1), both give consistent results. Good.

Also, I need to make sure the cars' positions are in the track plane (y ≈ 0.05 + car height offset). The car's y position should be at track level (0.05) plus the car's body height.

Actually, the car mesh is built with body at y=0.5 (center), wheels at y=0.35. So the car's origin is at the track level. When I set the car's y position to 0.05 (track surface), the car will be sitting on the track.

Let me make sure the car's position y is 0.05.

OK, let me write the final code now.

One more thing: I'll need to handle window resize:

```javascript
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});
```

And here's a reusable function to get the track position for a given progress and lane offset:

```javascript
function getTrackPosition(progress, laneOffset) {
    const pos = trackCurve.getPointAt(progress);
    const tangent = trackCurve.getTangentAt(progress);
    // Perpendicular to tangent in XZ plane
    const normal = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();
    
    return new THREE.Vector3(
        pos.x + normal.x * laneOffset * 3,
        0.05,
        pos.z + normal.z * laneOffset * 3
    );
}
```

With laneOffset in the range [-1, 1], the car stays within the 8-unit-wide track (offset up to 3 units from center).

OK, I'm going to write the complete code. Let me do this now. It's going to be a large file but everything will be included.

Actually, to keep it manageable, let me write the code in sections, being careful about the details. I'll definitely include:

1. Renderer, scene, camera setup
2. Lights
3. Track generation
4. Start line
5. Kerbs
6. Environment (ground, trees, buildings)
7. Car model
8. Car AI
9. Game state and HUD
10. Animation loop

Here's the complete code:

Let me write it out. I'll skip creating skyboxes and clouds for simplicity but add everything else.

Actually, for the environment, I need to be careful about the isOnTrack function. Checking all values of t (from 0 to 1 in steps of 0.02) is 51 checks per tree. With 30 trees, that's 1530 checks. At startup, this is fine.

But actually, I can just place trees far from the track using a simpler distance check. Let me use a fixed seed or just place them randomly and check if they're too close to the track.

The simplest approach: try random positions and keep only those that are at least 15 units from the track center.

Let me implement this.

Actually, instead of checking all t values, I can use a simpler constraint: just check a few points along the track and see if the position is far enough.

For a random position (x, z), I check if the distance to any point on the track (sampled at intervals) is less than some threshold. If so, try again.

Let me use:
```javascript
function isFarFromTrack(x, z, minDist) {
    const numSamples = 100;
    for (let i = 0; i < numSamples; i++) {
        const t = i / numSamples;
        const point = trackCurve.getPointAt(t);
        const dist = Math.sqrt((point.x - x) ** 2 + (point.z - z) ** 2);
        if (dist < minDist) return false;
    }
    return true;
}
```

Then place trees only at positions where `isFarFromTrack(x, z, 10)` returns true.

OK let me write the complete code. I'll handle all of this.

One more thing: the car AI needs to work correctly when cars cross the start line. When a car's progress wraps from >0.5 to <0.5, that means it crossed the start line (position 0). I need to check for this in each frame.

Wait, no. The progress wraps from 1.0 to 0.0. If the progress was 0.9 and the next frame it's 0.1, that means it wrapped. But it could also mean it went backward, which can't happen because the update always increases progress.

So: if `car.userData.progress < car.userData.lastProgress - 0.5`, then the car crossed the start line.

But what if the car is at 0.95 and moves to 0.05 (wrapping)? `0.05 < 0.95 - 0.5 = 0.45` is true. So this works.

What if the car is at 0.3 and moves to 0.5? `0.5 < 0.3 - 0.5 = -0.2` is false. Good.

Alright, that's the correct check.

Let me also think about initial positions. For the grid:
- Car 0 (player): progress 0.0, laneOffset 0
- Car 1: progress -0.01 (same as 0.99), laneOffset 0.8
- Car 2: progress -0.01, laneOffset -0.8
- Car 3: progress -0.02, laneOffset 0

Wait, negative progress wraps to near 1.0, which would place the car at the start/finish line. But I want the grid to be slightly BEHIND the start line.

Actually, for simplicity, let me just place all cars at progress 0 with different laneOffsets. The race starts immediately.

Hmm, but if they all start at progress 0, they're all exactly at the start line. That's fine - the AI will naturally separate them.

Actually, the progress values:
- Car 0: 0.000
- Car 1: 0.005
- Car 2: 0.010
- Car 3: 0.015

This means car 0 starts at the front, car 3 at the back. This is a standard grid.

Hmm, but for the "player" car, I want it to be in the back to make it exciting, or in the front to make it special. Since all cars are AI-driven, let me make the player car start at the back of the grid.

Player: progress 0.015, laneOffset 0
Rival 1: progress 0.000, laneOffset 0.6
Rival 2: progress 0.000, laneOffset -0.6
Rival 3: progress 0.000, laneOffset 0

Hmm, but that would mean the rivals start at the front. Let me make:
Player: progress 0.010, laneOffset 0
Rival 1: progress 0.000, laneOffset 0.6
Rival 2: progress 0.000, laneOffset -0.6
Rival 3: progress 0.005, laneOffset 0

This puts the player at the back. But actually, the AI will handle overtaking and position changes throughout the race, so starting positions don't matter too much.

OK, let me just set them up and move on.

Actually wait, car positions on the track: the progress values determine their position. Car 0 at progress 0, Car 1 at progress 0.005, etc. The lane offsets determine their lateral position.

At progress 0.005, the cars are at the start line, just after it.

OK, I'll just place them:
```javascript
const carSpecs = [
    { progress: 0.00, lane: 0,   color: 0xff0000 }, // Player car (red)
    { progress: 0.01, lane: 0.8, color: 0x0066ff }, // Blue car
    { progress: 0.01, lane: -0.8,color: 0x00cc00 }, // Green car
    { progress: 0.02, lane: 0,   color: 0xffcc00 }, // Yellow car
];
```

Wait, with the player at progress 0, and others at 0.01 and 0.02, the others are ahead. That's bad for the player.

Let me make the player start behind:
```javascript
const carSpecs = [
    { progress: 0.02, lane: 0,   color: 0xff0000 }, // Player car (red) - at back
    { progress: 0.00, lane: 0,   color: 0x0066ff }, // Blue car - front
    { progress: 0.005, lane: 0.6, color: 0x00cc00 }, // Green car
    { progress: 0.005, lane: -0.6,color: 0xffcc00 }, // Yellow car
];
```

Actually, I'll just make the player car the first one and place it at the back of the grid.

Let me simplify: I'll just give them these initial values:
```javascript
const colors = [0xff0000, 0x0066ff, 0x00cc00, 0xffcc00];
const carData = [
    { progress: 0.02, lane: 0,    baseSpeed: 30 }, // Player (red)
    { progress: 0.00, lane: 0.6,  baseSpeed: 28 }, // Blue
    { progress: 0.00, lane: -0.6, baseSpeed: 29 }, // Green
    { progress: 0.01, lane: 0,    baseSpeed: 27 }, // Yellow
];
```

This gives the player car the highest base speed (30) but starts from the back.

Alright, let me code this up.

One more thing: I should use all cars in the `cars` array and mark `cars[0]` as the player car.

OK, I'm ready to write the complete code. Let me be thorough and careful.

Actually, let me reconsider the track points. The CatmullRomCurve creates a smooth curve through the points. With closed=true, it creates a loop. But the points I defined might create a track where cars are angled oddly at certain points.

Let me test mentally:
- (0,0,0) → (30,0,-25): goes left and forward in -Z direction
- (30,0,-25) → (60,0,0): goes right and forward
- (60,0,0) → (70,0,30): continues right
- (70,0,30) → (55,0,60): curves left
- (55,0,60) → (25,0,70): continues left
- (25,0,70) → (-10,0,60): curves left
- (-10,0,60) → (-35,0,40): continues left
- (-35,0,40) → (-40,0,10): curves left
- (-40,0,10) → (-25,0,-10): curves right
- (-25,0,-10) → (0,0,0): curves right

This forms a nice loop with gentle curves. The tangent somewhere at (70,0,30) might be pointing roughly along +Z.

I think this creates a nice track. Let me go with it.

Now, let me also decide on scale. The track is about 100 units across at its widest. This is a good size for the game.

The car width is 2 units, and the track is 8 units wide. So the track is about 4 cars wide. Perfect for racing.

The car length is 4 units. At a base speed of 30 units/sec, that's 7.5 car lengths per second. The track is about 60 units long per lap (rough guess)... wait, let me compute.

The track has points spanning about 70 units in X and 80 units in Z. The perimeter is roughly 2*(70+80) = 300 units. At 30 units/sec, that's about 10 seconds per lap. That's a bit short.

Let me increase the track size or increase the speeds. Actually, let me reduce the scale of the cars or increase the track size.

Actually, looking at the dimensions: posis (0,0,0) to (60,0,0) is 60 units. The track is large enough.

At 30 units/sec, a lap of ~300 units takes 10 seconds. For 3 laps, that's 30 seconds. That's pretty short.

Let me either:
1. Make the track bigger
2. Slow down the cars
3. Accept it and have lots of laps

Option 1: Make the track bigger by scaling the points. Let me use:
```javascript
const trackPoints = [
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(60, 0, -50),
    new THREE.Vector3(120, 0, 0),
    new THREE.Vector3(140, 0, 60),
    new THREE.Vector3(110, 0, 120),
    new THREE.Vector3(50, 0, 140),
    new THREE.Vector3(-20, 0, 120),
    new THREE.Vector3(-70, 0, 80),
    new THREE.Vector3(-80, 0, 20),
    new THREE.Vector3(-50, 0, -20),
];
```

This makes the track about 280 units wide by 240 units tall. The perimeter is much larger. At 30 units/sec, a lap would take maybe 60-80 seconds. That's good for a race.

Actually, let me check: the points span from -80 to +140 in X (220 units) and -50 to +140 in Z (190 units). The perimeter would be roughly 2*(220+190) = 820 units. At 30 units/sec, that's about 27 seconds per lap. For 3 laps, that's about 80 seconds. Good.

But actually, the natural track width is 8 units with this scale. Let me scale the track width to 10 units to give more room for overtaking.

OK, let me adjust the track width to 10.

Also, I realize the track might be too wide for the car size. Let me keep it at 8 and accept that it's a bit tight for overtaking.

Alright, let me use these track points and move on.

Actually, let me simplify. The track points I originally defined (30, -25, 60, etc.) create a track that's about 70x80 units. The scale is a bit small. The cars are 4 units long, so about 2 cars per 8 units. The track fits about 2 cars side by side in the curves.

Let me scale everything up by 2 for the track points:
```javascript
const trackPoints = [
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(60, 0, -50),
    new THREE.Vector3(120, 0, 0),
    new THREE.Vector3(140, 0, 60),
    new THREE.Vector3(110, 0, 120),
    new THREE.Vector3(50, 0, 140),
    new THREE.Vector3(-20, 0, 120),
    new THREE.Vector3(-70, 0, 80),
    new THREE.Vector3(-80, 0, 20),
    new THREE.Vector3(-50, 0, -20),
];
```

Hmm, this makes the track 280 units wide and 240 units tall. That's quite big.

Let me use a middle ground:
```javascript
const trackPoints = [
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(40, 0, -35),
    new THREE.Vector3(80, 0, 0),
    new THREE.Vector3(95, 0, 40),
    new THREE.Vector3(70, 0, 80),
    new THREE.Vector3(30, 0, 90),
    new THREE.Vector3(-15, 0, 75),
    new THREE.Vector3(-45, 0, 50),
    new THREE.Vector3(-50, 0, 15),
    new THREE.Vector3(-30, 0, -10),
];
```

This spans about 145 units in X and 125 units in Z. Perimeter maybe 400 units. At 30 units/sec, that's ~13 sec/lap. Still short but acceptable.

Let me use even bigger points:
```javascript
const trackPoints = [
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(50, 0, -40),
    new THREE.Vector3(100, 0, 0),
    new THREE.Vector3(120, 0, 50),
    new THREE.Vector3(90, 0, 100),
    new THREE.Vector3(40, 0, 115),
    new THREE.Vector3(-15, 0, 90),
    new THREE.Vector3(-55, 0, 60),
    new THREE.Vector3(-65, 0, 15),
    new THREE.Vector3(-40, 0, -15),
];
```

This spans about 185 units in X and 155 units in Z. Perimeter maybe 600 units. At 30-40 units/sec, that's 15-20 seconds per lap. 3 laps = 45-60 seconds. That's reasonable.

Actually, I think I'm overthinking this. Let me just use these track points and adjust the car speeds to make it fun. If the track is too big, I can increase car speeds. If too small, decrease.

Let me use base speeds of 50-60 units/sec for the cars, giving roughly 10-15 seconds per lap.

OK, I'll set the track points as:
```javascript
const trackPoints = [
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(50, 0, -40),
    new THREE.Vector3(100, 0, 0),
    new THREE.Vector3(120, 0, 50),
    new THREE.Vector3(90, 0, 100),
    new THREE.Vector3(40, 0, 115),
    new THREE.Vector3(-15, 0, 90),
    new THREE.Vector3(-55, 0, 60),
    new THREE.Vector3(-65, 0, 15),
    new THREE.Vector3(-40, 0, -15),
];
```

And set car speeds to:
- Player: 60
- Rival 1: 58
- Rival 2: 56
- Rival 3: 55

The AI will handle the racing. The cars will take racing lines based on curvature.

Wait, I need to make the speeds relative to the scale. With a track of ~600 units perimeter and speeds of 60 units/sec, a lap takes 10 seconds. 3 laps = 30 seconds. That's still short but acceptable.

Actually, I want the race to be more like 1-2 minutes. Let me increase the speeds or make them race for 5 laps.

Let me set the lap count to 5 and speeds at 50-60. That gives:
- 600 units (perimeter) / 55 units/sec (avg) ≈ 11 sec per lap
- 5 laps = 55 seconds

That's fine. But I could also make the track bigger. Let's go with 5 laps.

Actually, you know what, I'll adjust the lap count in the code.

OK, let me write the code now. I'm going to aim for correctness and completeness. Here goes!

One last concern: the car's lane offset. If the track curves, having a lane offset means the car is always perpendicular to the tangent at its progress coordinate. This means the car follows the racing line correctly.

But if the car's laneOffset changes while on a curve, it might cut across lanes, which is actually what overtaking is. Good.

Let me set the lane offset range to [-1, 1], which corresponds to ±3 units from the track center.

OK, writing the complete code now. I'll split it into logical sections.

Wait, actually, one issue with the `getTrackPosition` function: I use a multiplier of 3 for the lane offset. But the track is 8 units wide, so the car center should be at most ±3.5 units from the center (track edges are at ±4). So laneOffset * 3 gives a max of ±3 units. That's good - the car stays within the track with a small margin.

Hmm, but the initial lane offsets are 0.6 and -0.6, giving ±1.8 units from center. That's inside the track.

Alright. Let me write it.

One more consideration: for the car rotation, I need to make sure the car faces the direction of travel. The track tangent gives the direction of travel (forward). So I set the car's Y rotation to `Math.atan2(tangent.x, tangent.z)`.

Since the car mesh is built with the front facing +Z, this should work.

Actually, wait. The car mesh has the engine (front) at +Z. If the tangent points in the direction of travel, then the car's front should be in the tangent direction. So:

`car.rotation.y = Math.atan2(tangent.x, tangent.z)`

This makes the car's local +Z axis point in the tangent direction.

But `Math.atan2(x, z)` gives the angle from +Z. If tangent is (1, 0, 0), the angle would be atan2(1, 0) = π/2, which rotates the car 90° around Y. The local +Z would then point in the +X direction, which is correct.

If tangent is (0, 0, 1) (pointing in +Z), the angle is atan2(0, 1) = 0, so no rotation. The car's +Z is the global +Z, which matches the tangent. Good.

If tangent is (0, 0, -1) (pointing in -Z), the angle is atan2(0, -1) = π. The car's +Z would point in -Z. Correct.

OK, this should work.

Alright, I'm done thinking. Let me code.

Actually, one final concern: I should also update the car's position every frame, not just the AI state. The AI sets the userData, and then I update the mesh position from the AI data.

Let me design the update loop:
1. Compute the target speed based on curvature and cars ahead
2. Update currentSpeed
3. Update progress
4. Check for wrap (crossing start line)
5. Update lane offset
6. Update mesh position and rotation
7. Update wheel rotation
8. Update camera position

This is all in one function.

Now let me write the complete file.

Actually, I realize I should also make sure that the start line is at the same position for all cars. Since the track is a loop, progress 0 is the start line. When a car crosses from progress ~0.9 to ~0.1, it's crossing the start line.

In the code, I check for: `if (newProgress < oldProgress - 0.5)` to detect crossing.

OK, let me write it! Here goes the complete implementation.

Also, I realized that for the camera, I should have it look at the player car from behind. I'll set the camera to follow the car, positioned slightly behind and above.

Given the car's rotation, I can offset the camera in the car's local coordinates:
- Camera position = car position + local offset (0, 12, -16) converted to world
- Camera look at car position + local offset (0, 1, 0) maybe

But actually, it's easier to:
1. Get the car's world position
2. Get the car's forward direction (tangent)
3. Set camera position = car position - tangent * 16 + up * 10
4. Look at car position + tangent * 3

Let me use a smooth camera that follows the car.

Actually, since all cars move fast, a simple camera that follows the player car is best.

I'll use:
```javascript
// Camera follows player car
const playerCar = cars[0];
const playerPos = playerCar.position.clone();
const tangent = trackCurve.getTangentAt(playerCar.userData.progress);
const cameraTarget = playerCar.position.clone().add(new THREE.Vector3(tangent.x, 0, tangent.z).multiplyScalar(5)).add(new THREE.Vector3(0, 2, 0));

camera.position.lerp(cameraPos, 0.1); // smooth
camera.lookAt(cameraTarget);
```

Actually, let me just set the camera hard each frame:
```javascript
const playerPos = playerCar.position;
const tangent = trackCurve.getTangentAt(playerCar.userData.progress);
const camDist = 12;
const camHeight = 8;
const cameraPos = new THREE.Vector3(
    playerPos.x - tangent.x * camDist,
    playerPos.y + camHeight,
    playerPos.z - tangent.z * camDist
);
camera.position.copy(cameraPos);
const target = new THREE.Vector3(
    playerPos.x + tangent.x * 5,
    playerPos.y + 1,
    playerPos.z + tangent.z * 5
);
camera.lookAt(target);
```

This places the camera behind and to the side of the car, looking in the direction of travel.

OK, let me finalize the code. I'm going to write the complete implementation now. Here it is: