The user wants a three.js simulation of two spiral galaxies colliding. Let me break down the requirements:

1. Two disk galaxies with visible spiral arms and a bright core
2. At least 20,000 stars rendered as glowing points (additive blending) per galaxy (so 40,000+ total)
3. Colors: warm yellow cores to blue-white arms
4. Galaxies approach and interact through gravity, showing tidal tails and bridges
5. Slowly orbiting camera framing the whole event
6. Dark starfield background
7. On-screen label with simulated time in millions of years
8. Use requestAnimationFrame timestamp
9. Physics on GPU or cheap approximation for smoothness
10. Full-window canvas with resize handling
11. Auto-start, no interaction

Since we need at least 20,000 stars per galaxy, and we want smooth performance, using a GPU-based particle system with a custom shader is best. But gravity simulation for 40,000 particles on CPU per frame would be too slow.

Let me think about the approach:

**Star Generation:**
- Each galaxy needs a disk with spiral arms. We can generate positions using density wave theory or a simpler approach: generate particles along spiral arms with some scatter.
- Use a logarithmic spiral: r = a * e^(b*theta), or simpler: theta = theta0 + log(r) * some_factor
- Actually, for a typical spiral galaxy, we can use: arms start at some radius and wind out. We can use multiple arms (e.g., 2 main arms).

**Physics Simulation:**
- Since we have 40,000+ particles, running full N-body gravity on CPU is too slow.
- Options:
  a) Use a simplified gravity model: treat each galaxy as a point mass (or Plummer sphere) and integrate particle positions in the combined potential using a "tidal" approximation.
  b) Actually, a really common trick is to have the galactic potential move (the disk particles rotate around the galactic center, and the two galaxies orbit each other). Tidal effects can be simulated by applying a differential acceleration across each galaxy.
  c) Use a GPU fragment shader to do the physics (Ping-pong FBOs in Three.js). But this is complex and heavy.

Let me think more carefully. The requirement says "run the physics on the GPU or with a cheap approximation so it stays smooth."

Cheap approximation approach:
- Each galaxy is a rigid (or semi-rigid) disk of particles that rotates around its center (differential rotation). The galaxy centers follow a Keplerian orbit (or a softening Plummer potential) around each other.
- When the galaxies get close, we want tidal tails and bridges. We can achieve this by applying tidal forces to each particle based on its position relative to the galaxy center. For a particle in a galaxy, the tidal acceleration from the other galaxy is approximately:
  a_tidal ≈ -G * M_other * (r_particle_cm / |r_galaxy_cm|^3) ... something like that. Actually, tidal field from a point mass at distance D: the differential acceleration across the galaxy is roughly a_tidal ≈ (G * M_other / D^3) * r_particle (where r_particle is the distance from the galaxy center, for particles aligned with the direction to the other galaxy). This stretches the galaxy along the line connecting the two centers (tidal tail and bridge).

Actually, a more accurate but still cheap approximation: use a "galactic tide" model. For each particle, compute the gravitational acceleration from its own galaxy (using a spherically symmetric potential or just circular velocity) and from the other galaxy (as a point mass). This requires computing the distance from each particle to each galaxy center, which is 2 * N operations, very cheap.

But wait, if we just use point mass for the other galaxy, the force on a particle from the other galaxy is:
a_1 = G * M_other * (r_other - r_particle) / |r_other - r_particle|^3

And the own galaxy's potential can be approximated as a central force that gives circular rotation: a_own = v_c^2 / r * r_hat. But to get spiral structure, particles should be on nearly circular orbits with some velocity dispersion.

Actually a common approach for collision simulations in real-time:
- Model each galaxy as a set of particles on circular orbits around the galaxy center (with some velocity dispersion).
- The galaxy centers move under each other's gravity (they are point masses).
- Each particle feels gravity from both galaxy centers (as if all mass is at the centers).
- This is the "restricted N-body" approach. It gives tidal tails, bridges, and distortion.

But there's a problem: when using a point-mass for the own galaxy, the core is very dense and particles would go elliptical. Instead, we can use a Plummer sphere potential for each galaxy. The Plummer potential has the nice property that it's analytic and gives a flat rotation curve.
Phi(r) = -G*M / sqrt(r^2 + a^2)
The corresponding circular velocity: v_c(r) = G*M * r / (r^2 + a^2)^(3/2) ... actually v_c^2 = r * dPhi/dr = G*M * r^2 / (r^2 + a^2)^(3/2).

So the force per unit mass from own galaxy on a particle at position r (relative to galaxy center) is:
a_own = -G*M * (r) / (|r|^2 + a^2)^(3/2)

And the force from the other galaxy's center:
a_other = -G*M_other * (r - D) / (|r - D|^2 + epsilon^2)^(3/2)
where D is the position vector of the other galaxy center relative to this galaxy's center.

Actually, if we do it per-particle, and the particle positions are stored in world coordinates, we need to compute for each particle:
r_i = particle.pos
R1 = r_i - center1
R2 = r_i - center2
accel = -G*M1 * R1 / (|R1|^2 + a1^2)^(3/2) - G*M2 * R2 / (|R2|^2 + a2^2)^(3/2)

This is very cheap: 2 forces per particle. For 40,000 particles, 80,000 force evaluations per frame. This is trivial for a modern CPU in JS. We can do this with a simple JS loop updating positions and velocities. But we need to also update per-frame.

Wait, but the particles in a real disk galaxy are on orbits within the disk. If we just use the Plummer potential, the orbits will be 3D and the disk will thicken. To keep the disk thin, we can add a flat disk potential or just constrain particles to have small vertical oscillations. Alternatively, we can compute the rotation curve and set particles on circular orbits in the disk plane, and to keep it thin, handle the vertical force with a spring-like restoring force.

Actually, for a visual simulation, we can:
- Generate particles in a thin disk.
- Give them circular orbits based on the rotation curve v_c(r).
- Add some random velocity dispersion.
- When computing the force, use a flattened potential (like Miyamoto-Nagai) or simply apply a vertical restoring force to keep them near the plane.

But the simplest to implement and still look great:
- Use a Plummer potential for the spherical halo (the main gravitational potential).
- The disk particles are on circular orbits in the plane (z=0) with some small random z and z-velocity.
- The vertical force from the disk is approximated by a harmonic oscillator (spring back to the plane).
- When galaxies interact, the z-component gets some excitation, causing the thin disk to warp.

Hmm, this is getting complicated. Let me step back.

Alternative approach: Compute the physics on the GPU. But that requires a render target with particle positions, read/write in the same material, Ping-pong. Three.js has some support for transform feedback (GPUParticles) but it's custom.

Actually, let's think about using the cheap approximation but making the integration stable enough.

Let me design the simulation:

1. **Galaxy centers**: Two point masses (or Plummer spheres) that orbit each other. They approach on an eccentric orbit (elliptical, maybe almost parabolic). We can integrate their positions using Newton's laws: each center feels the gravity of the other. Since they have equal mass, we can compute:
   a_center1 = -G*M*(center1 - center2) / (|center1 - center2|^2 + a^2)^(3/2)
   ... and similarly for center2.

2. **Particles**: Each particle is bound to one of the two galaxies initially. We store its position relative to the galaxy center, velocity relative to the galaxy center. We then integraterelative positions? Actually, we can store the particle's absolute position and velocity, and compute the acceleration from both galaxy centers. This gives tidal forces automatically.

For 40,000 particles, doing the following per frame:
```
for each particle:
   R1 = p.pos - c1.pos
   R2 = p.pos - c2.pos
   invR1 = 1 / (R1.lengthSq() + softening^2 + a_disk^2)
   invR2 = 1 / (R2.lengthSq() + softening^2 + a_disk^2)
   acc = -G*M1 * R1 * sqrt(invR1) * invR1? Wait, the Plummer force is G*M / (|R|^2 + a^2)^(3/2) * R. So:
   acc = -G*M1 * R1 / (|R1|^2 + a^2)^(3/2) - G*M2 * R2 / (|R2|^2 + a^2)^(3/2)
```
To compute |R1|^2, we compute dot product. Then (r2 + softening)^(3/2). A few Math.sqrt per particle. 40k * 2 = 80k force evaluations. Each evaluation: 3 sub, 3 dot, 1 sqrt, 3 mul. ~80k * 10 = 800k ops. That's nothing, will run at 60fps easily.

But we also need to update the acceleration. We can do it with a simple leapfrog or velocity Verlet.

To make it a "cheap approximation" and keep it smooth, we can use a substep of say 2-4 substeps per frame, but maybe 1 is enough if dt is small. Since this is cinematic, we can use a time scale.

**Generating Spiral Galaxies:**

To create a realistic spiral galaxy with a bright core and spiral arms, we need to generate 20,000 particles per galaxy.

Particle distribution:
- Density profile: exponential disk: rho(r) = rho0 * exp(-r / h) * sech(z / z0)^2. We can sample.
- Spiral arms: pattern associated with density waves. We can use the approach:
  - Choose a number of particles that are "arm" particles (e.g., 50%) and the rest are "disk" particles.
  - For arm particles, sample a radius from the exponential distribution, then compute theta at that radius: theta = theta_0 + m * log(r / r_inner) / tan(phi), where m is number of arms, phi is pitch angle.
  - Then set position: x = r * cos(theta), y = r * sin(theta), z from a Gaussian with small sigma.
  - Add some scatter in r and theta.

Actually, a simpler method:
```
for each particle:
   r = -h * Math.log(1 - random())   // exponential
   theta = random() * 2 * PI
   // add spiral arms
   arm_strength = 0.5
   arm_offset = 0.3 * Math.sin(2 * theta + 3 * Math.log(r))  // perturbation
   theta += arm_offset * arm_strength
   x = r * Math.cos(theta)
   y = r * Math.sin(theta)
```
But this gives two arms if we use sin(2*...).

Better: generate a density wave:
- Choose whether the particle is in arm or interarm based on probability: P_arm = p0 / cosh((r - r_peak)/r_width) ??? 

Actually, a common method for generating spiral galaxies:
1. Generate disk particles with exponential profile.
2. Assign each particle a spiral phase perturbation in tangential direction:
   d_theta = A * cos(2*(theta - theta_0) - m * log(r)) ... something.

Hmm, let's look at the classic "spiral galaxy generator" used in many demos:

```
// Galaxy parameters
const arms = 2;
const radius = 100;
const armSpread = 0.6; // how tightly wound

for (i = 0; i < count; i++) {
    // Random radius (power law to get dense center)
    let r = Math.pow(Math.random(), 2) * radius;
    // The spiral arm
    let rotation = Math.log(r) * armSpread;
    let theta = Math.random() * Math.PI * 2;
    // Offset from arm
    let armOffset = 1.0 - 0.7 * Math.pow(Math.random(), 2); // more particles near arms
    r += armOffset * 10; // spread in radius
    theta += armOffset * 0.5;
    // Convert to cartesian
    let x = Math.cos(theta + rotation) * r;
    let z = Math.sin(theta + rotation) * r;
    // ...
}
```

This is a bit hacky but can look acceptable.

Another approach: use a particle system with position in cylindrical coordinates. We can set the spiral arm density using a "spiral potential" or just random sampling from a distribution that has spiral arm structure.

I think a more reliable method to get nice spiral structure:

1. Generate a random radius from an exponential distribution.
2. Generate a random angle theta.
3. Compute the density at (r, theta) due to spiral arms: for 2 arms, the density enhancement is proportional to `1 + A * cos(2 * (theta - phi(r)))`, where phi(r) = log(r) / tan(pitch) is the winding angle, pitch maybe 0.3.
4. Use rejection sampling: if random < density(r, theta) / rho_max, accept particle.

This gives clear spiral arms with controllable strength.

Let's define:
- h_r = 30 units (disk scale length)
- r_max = 120 units
- pitch angle p = 25 degrees (so tan(p) = 0.466)
- number of arms m = 2
- arm strength A = 0.8

Density: rho(r, theta) = rho_exp(r) * (1 + A * cos(m * (theta + phi(r))))  (depending on convention, arms trailing so theta - phi(r) or theta + phi(r); need to set sign so that arms wind in the direction of rotation. Actually for trailing spirals (as seen in most galaxies), the arm curves from the center outward in the direction of rotation. In cylindrical coordinates if the rotation is counterclockwise (positive theta), the pitch angle positive means the spiral winds outward counterclockwise. We'll use phi(r) = -log(r) / tan(pitch). Actually, logarithmic spiral: r = r0 * exp(b * theta), or theta = (1/b) * ln(r / r0). For trailing arms, b = -tan(pitch)? Let's not overcomplicate. We'll set phi(r) = log(r) * something and tune.)

Actually, let's just define spiral arms in a simple way:
For each particle, compute a random radius r (exponential). Then the "unwound" angle at that radius for arm i is:
theta_arm(r) = (log(r / r_min) / tan(pitch)) + i * (2*PI / m)

Then choose a random offset from the arm: the particle's theta = theta_arm + delta_theta, where delta_theta has a Gaussian distribution with sigma = 0.2 (in radians) or something.

The easiest is to generate particles *on* the arms, then add scatter. But if all particles are on the arms, the interarm region is empty. A real galaxy has both an exponential disk (smooth) and arms. We can make some fraction of particles on the spiral arms and the rest in the smooth disk.

Let me use this:

- Total particles per galaxy: 20000.
- Fraction on arms: 0.7 (14000)
- Fraction smooth disk: 0.3 (6000)
- For arm particles:
   - Pick a radius from exponential distribution.
   - Compute the central angle at that radius: theta_arm = (log(r / r_min) / tan(pitch)) * sign + arm offset. Actually, let's define the spiral as: r = r_min * exp(theta * tan(pitch))? Wait, in a logarithmic spiral, theta = (1/tan(pitch)) * log(r / r_min). That's standard: the pitch angle p is the angle between the tangent and the circle, so tan(p) = (1/r) (dr/dtheta). Solving gives r = const * exp(theta * tan(p)), or theta = (1/tan(p)) * log(r / const).
   - We'll set const = 1, r_min = 1? Let's use code: `theta_arm = (Math.log(r / r_inner) / Math.tan(pitch)) + armOffset`. Since r > r_inner, theta increases as r increases (if pitch positive). This makes a trailing spiral for counterclockwise rotation (which is positive theta). Actually, if theta increases with r, then as you go out, the arm increases theta, meaning it winds counterclockwise (from center outward). This is what we want.
   - Then add a random offset perpendicular to the arm (in the theta direction) with some dispersion.
- For smooth disk particles:
   - r = exponential, theta = uniform.
- All particles get a z coordinate with gaussian spread, e.g., sigma = 5 units (thin disk) or maybe scale height 1/10 of scale length.

Let me set the galaxy radius to be around 100 units, scale length h=25. Then the galaxy has a visible disk out to ~100.

**Colors:**
- Need warm yellow core to blue-white arms.
- We'll assign each particle a color based on its radius relative to the galaxy size. Inner particles are yellow/orange, outer are blue/white.
- But actually, a real galaxy has a central bulge that is yellow, and the arms are blue (star-forming). So we can use a color gradient:
   - At r < some core radius: #FDB813 (warm yellow) to #FFDAB0
   - At larger r: blue-white #A0C4FF or #B0E0FF
- We can create a THREE.Color and use lerpColors.

For the additive blending, using a custom shader is best. But three.js's PointsMaterial with vertexColors and additive blending works too, but for 20k points, we want a custom shader to have glowing points. Actually, THREE.PointsMaterial has `blending: THREE.AdditiveBlending`, `transparent: true`, `vertexColors: true`, and `sizeAttenuation: true`. That's fine. But to make them glow, we can use a custom shader with a circular falloff, or use a texture. We can't use an external texture, but we can generate a CanvasTexture of a radial gradient (white center to transparent edge) for the point sprite. That's allowed because we create it in code.

Alternatively, use a ShaderMaterial to have point sprites with soft edges. But using PointsMaterial with a generated texture is simpler. Let's generate a sprite texture with a canvas.

But the requirement says "rendered as glowing points (additive blending)". So a soft point sprite is good.

To do custom per-particle size or color, we'd need ShaderMaterial. With PointsMaterial, we have `vertexColors: true`, `size`, `map`, `alphaTest`, `depthWrite: false`, etc. But we can also use `THREE.ShaderMaterial` for more control. However, ShaderMaterial with 40k points is fine.

Actually, for performance, a custom ShaderMaterial that uses gl_PointSize can handle size attenuation. Let's consider:

- Attributes: position, color.
- Uniforms: uTime? Not needed for rendering.
- Vertex shader: `gl_PointSize = uSize * uScale / -mvPosition.z;`
- Fragment shader: circular sprite with additive blending.

This gives good control. We'll use a custom ShaderMaterial.

But we also need to update positions each frame from the physics. If we use a BufferGeometry with `position` attribute, we can update the array in JS each frame.

Actually, to update 40k positions per frame, we can use `geometry.setAttribute('position', new THREE.BufferAttribute(...))` after updating the array. That's fine. Or use a `Uint8Array`? No, positions are floats.

**Timeline:**
- Simulate time in Myr (millions of years).
- The scene has a scale: 1 unit = 1 kpc? Or maybe 1 unit = 1000 light-years? Let's set realistic scales but not too crucial.
- We'll use a time scale factor in the simulation so that the collision happens over a reasonable duration (e.g., 30 seconds = 500 million years). So time factor = (500 Myr) / (30 seconds) = 16.67 Myr/second. Or maybe slower: 1 second = 5 Myr, so 30s = 150 Myr. Let's tune to look good.

We can define `simTime += deltaTime * timeScale`, where `deltaTime` is from the frame (seconds), and `timeScale` in Myr per second.

**Orbital mechanics:**
- The two galaxies have equal mass M. They approach each other from rest at some distance? Or they have an initial relative velocity.
- If we set them on a parabolic orbit, they start far apart with negligible velocity, fall in, pass through, and then go back out (or merge).
- To make it cinematic, we can start them at distance R_max = 400 units apart, zero relative velocity initially (falling in). They collide, form tails, and then go back/merge into one.
- Actually, if they are on a zero-energy orbit (parabolic), they would slow down, reversal, and go back out. But to have a merger, we need to dissipate orbital energy. Real galactic collisions merge due to dynamical friction and merging. Since we only have two centers and feel their gravity, without momentum loss, they will just pass through and oscillate. But it can still look like a collision with bridges and tails. For a more eventual merger and to keep the visual interesting, we can add a simple dynamical friction such that the galaxy centers lose orbital energy gradually, causing them to spiral in and merge. This is a "cheap approximation" for the effects of dynamical friction.

Dynamical friction formula (Chandrasekhar) is complex. A simple trick: add a damping force to the galaxy centers only: a_center = -k_friction * v_center (relative to the center of mass). This slowly circularizes and shrinks the orbit, leading to a final merger.

We can also set the initial orbit to be slightly eccentric with a large apocenter, and let dynamical friction bring them together.

Let me set:
- Galaxy masses: M1 = M2 = 1 in code units.
- Gravitational constant G = 100 (in units of distance^3 / (M * time^2)).
- Need to pick G so that the orbital time is reasonable. For a galaxy with mass M and scale radius a=10 (Plummer scale), the circular velocity at r=10 is ~ sqrt(G*M / sqrt(r^2 + a^2)? actually for Plummer: v_c(r) = sqrt(G*M * r^2 / (r^2+a^2)^(3/2)). At r=10, v = sqrt(100 * 1 * 100 / (2000)) = sqrt(5) ≈ 2.2 units/time. The orbital period at r=100: T = 2π*100/2.2 = 285 time units. If 1 time unit = 1 Myr, that's 285 Myr. That's a bit slow. We can tune.

Actually, let's do a dimension analysis:
We want a galaxy with a disk scale length h = 25 units, and the crossing time over the disk (100 units) should be maybe 1-2 seconds in real time. We'll set time units.

Let's define:
- Distance unit: 1 kpc (could be arbitrary).
- Mass unit: 10^10 solar masses? 
- G in real units is 4.3e-6 kpc (km/s)^2 / (Msun) ? This gets messy.

Let's just use arbitrary units and tune the simulation manually. We'll set:
- Simulation time in "code units" where 1 time unit = 1 Myr. But G and masses arbitrary.
- We'll adjust G so that the encounter looks good in a few seconds.

Let's derive G from the desired orbital velocity.
At a distance of 100 units from a galaxy of mass M, the circular velocity is v = sqrt(G*M/100) (roughly). If we want the orbital period around the galaxy at 100 units to be about 10 seconds (for the collision animation), then:
T = 2π*100/v = 10s → v = 62.8 units/s.
So G = v^2 * r / M = (62.8^2 * 100) / 1 = 394,000 (in units^3 / (mass * s^2)).
But then for the two galaxies orbiting each other at a separation of 300 units, with total mass 2, the relative velocity would be roughly sqrt(G*2 / 300) = sqrt(394k*2/300)= sqrt(2626)=51 units/s. That means an orbit will take T=2π*300/51=37s. That's okay.

But we also need the internal rotation of the disk to be similar. If the internal rotation speed at 25 units is ~60 units/s, the disk will rotate visibly.

So let's set G = 400,000, total mass 2, scale length 25, galaxy radius 100.

But then the scenter physical speeds are high in terms of frame rate: at 60fps, a speed of 60 units/s means 1 unit per frame. Good.

Let's refine:
- Galaxy positions are integrated with a simple leapfrog.
- Particles are integrated with the combined potential from two centers.

**Particle count and update:**
We'll have 2 galaxies * 20,000 = 40,000 particles. Each is a Point. Actually, 20k per galaxy, total 40k. That's fine.

**Initial conditions:**

1. Generate two galaxies.
2. Position them at rest? Or with initial relative velocity. Let's set initial separation of 300 units, galaxies at ±150 units on the x-axis. Zero initial relative velocity (they start from rest and fall in). But if they start at rest, they will take time to reach each other. However, if they are at rest and fall in, they will approach along a radial path, not have tangential motion. A radial collision is less interesting (no rotation of the encounters). We want a parabolic or hyperbolic orbit with some impact parameter. Let's set:
   - Galaxy 1 at (100, 0, -50) and Galaxy 2 at (-100, 0, 50)? Hmm, maybe put them at a separation of 250, with an initial velocity offset in the y-direction to give some angular momentum.
   - For example, positions: c1 = (125, 0, 0), c2 = (-125, 0, 0).
   - Velocities: v1 = (0, 0, -20), v2 = (0, 0, 20). This gives a rotating collision (they miss initially and swing around).
   - The gravitational acceleration will cause them to curve and collide.

Actually, for a nice tidal deformation, the galaxies should be on a prograde orbit (disk spins aligned with the orbital angular momentum). If the disks are in the XZ plane (rotating around Y), and the orbit is in the XY plane (rotating around Z), then the disk's rotation vector is perpendicular to the orbital plane. This is like a perpendicular passage? Let's decide.

Let's make the galaxy disks in the XZ plane (plane of the disk: x-z, with normal along Y). Each galaxy has its own rotation around the Y axis. The orbital plane is X-Y (so the two galaxies orbit in the X-Y plane). This means the disks are perpendicular to the orbital plane, which gives a nice "side-on" view at some times and "face-on" at others? Actually, if the disk is in XZ and the orbit is in XY, the galaxies will slide past each other edge-on... Hmm.

Better to have both galaxies' disks lie in the X-Y plane (so rotation around Z), and the orbital plane is also X-Y. This is the classic "disk-on-disk" collision, with the disks coplanar or inclined.

Let's set the galaxy disk normal to Y, so the disk is in the XZ plane. Real spiral galaxies are thin disks, and in a typical collision (like Milky Way and Andromeda), the disks are inclined relative to the orbital plane. But for cinematic purposes, having them all in the same plane (with some tilt) looks great.

Let me set:
- Galaxy 1 disk normal initially along Y. It rotates around Y.
- Galaxy 2 disk normal also along Y. They are coplanar. This is a "coplanar collision" and produces beautiful tidal tails.
- The orbit is in the X-Y plane, so the two galaxies approach from the side. They will collide and interpenetrate, producing tails.

But if the disks are coplanar, when they collide, the particles from both galaxies overlap, and you get a lot of direct collision. That's fine.

Actually, for a more realistic oblique collision, we can tilt one galaxy relative to the other. But that increases complexity.

Let's keep it simple: both galaxies initially in the same plane (XZ), with points rotating around Y. The two galaxy centers move in the X-Y plane. So one is above the other (in y) as they orbit. The disks are perpendicular to the orbital plane, so the galaxies are edge-on at the start, face-on later? Hmm.

Let me think of a better setup:
- Disk plane: X-Z (normal = Y).
- Galaxy 1 center at (120, 0, 0), velocity (0, 0, -30).
- Galaxy 2 center at (-120, 0, 0), velocity (0, 0, 30).
So they orbit in the X-Z plane (same as the disk plane). Their disks are coplanar. This is perfect for generating tidal tails in the disk plane.

So the orbital plane is the same as the disks. Yes, this is the classic "in-plane collision". The galaxies approach each other on a nearly parabolic path, and since they are coplanar, the tidal tails spread out in the same plane. This is visually stunning.

Thus:
- Disk particles are generated in the XZ plane with y=0 (plus small z spread in y).
- Rotation: the y component of position is zero (or small). Velocity due to rotation is in the XZ plane, perpendicular to the radius vector: for a particle at angle theta in the XZ plane, the circular velocity is v_rot * ( -sin(theta), 0, cos(theta) ) (for counterclockwise rotation when viewed from +Y).
- The galaxy centers move in the XZ plane (the plane of the disk). They will have positions with y≈0 and velocities in the XZ plane.

This way, everything is in a 2D plane (or thin slab), and the collision is fully in-plane. That gives the most dramatic tidal arms.

**Tidal tails:**
When two equal masses pass close to each other, they eject long tidal tails. To get these, the orbit must be prograde (disks rotate in the same direction as the orbital motion). We'll generate the stars with a rotation direction that matches the orbital angular momentum. If the galaxy centers pass from left to right, etc.

**Implementation strategy:**

Because we need to store and update 40k particles with velocities and integrate, we can use plain Float32Arrays.

For each galaxy's particles, we'll store:
- position (x, y, z) - world coordinates, or relative? Let's store world positions for rendering. But for the physics, we compute forces based on world positions and center positions.
- velocity (vx, vy, vz) - world coordinates.
- color (r, g, b) - constant per particle.

We also need center positions and velocities for the two galaxies.

**Integration steps per frame:**
1. Compute deltaTime from requestAnimationFrame timestamp (clamp to e.g., 0.05s).
2. Multiply by simulation speed (e.g., 1000 units? no, just a time scale).
3. Update galaxy centers using Newton's law and integrate.
4. For each particle, compute acceleration from both centers using Plummer potential (with softening to prevent crazy accelerations).
5. Update particle velocity with a time step (maybe multiple substeps for accuracy). Use velocity Verlet or leapfrog.

Wait, if we do 1 substep per frame, with dt = 1/60s and velocities ~50 units/s, the displacement per step is ~0.8 units. That's acceptable for the scale of 100 units. But we need to be careful with the force resolution in close encounters. Use a softening length (e.g., 3 units) to avoid large accelerations.

For accuracy, we can do 2 substeps per frame, or use a smaller dt. Since it's only 40k particles, 2 substeps = 80k force calculations, still fine.

Actually, per substep:
For each particle:
```
R1x = px - c1x; R1y = py - c1y; R1z = pz - c1z;
R2x = px - c2x; ...
r1sq = R1x*R1x + R1y*R1y + R1z*R1z + eps^2;
r2sq = ...
r1 = sqrt(r1sq); r1inv = 1/r1; r1inv = r1inv / r1sq? Let's compute:
r1_inv_3 = r1 / (r1sq * r1sq) ? actually (r^2)^(3/2) = r^3. So 1/r^3 = 1 / (r^2 * r). 
inv1 = 1 / (r1sq * Math.sqrt(r1sq));
```
Accel: `ax += -G*M1 * R1x * inv1`.

Where eps is the Plummer softening (e.g., 5 units).

For the gravitational constant, we'll use G = 1000? We'll calibrate.

Let's do a quick calibration:
We want the orbital speed of a galaxy at separation d to be reasonable.
In a two-body system with equal masses M and separation d, the relative orbital speed for a circular orbit is v_circ = sqrt(G*M_tot / d) ? Actually for two point masses, the relative speed on a circular orbit: sqrt(G*(M1+M2)/d). If M1=M2=M, d=200, v_circ = sqrt(G*2M/200) = sqrt(G*M/100).
For a galaxy, we also have internal rotation v_rot = sqrt(G*M / r) (roughly). So if G*M = v_rot^2 * r, we can set things.

Let's set:
- Galaxy disk scale length h = 25, maximum radius R_gal = 100.
- Desired circular speed at r = 10 from center: v = 10 units/s? Let's choose v_rot = 8 units/s. Then G*M = v^2 * r = 64 * 10 = 640. So G = 640 / M. If M = 1, G=640.
- At a separation d = 200, relative orbital speed v_circ = sqrt(G*M_tot/d) = sqrt(640*2/200) = sqrt(6.4) = 2.5 units/s. That's slow. The collision would take long. Maybe we want v_rot = 20 units/s, so G*M = 400*10=4000, G=4000. At d=200, v_circ = sqrt(8000/200)=6.3 units/s. Hmm.

The galaxies start at rest from d=300, they fall in. The infall speed at separation d will be v_infall = sqrt(2*G*M_tot * (1/d_initial - 1/d))? Actually from rest at infinity, speed at d is sqrt(2*G*M_tot / d). For d=100, v = sqrt(2*G*M_tot/100). With M_tot=2, G=4000, v= sqrt(16000/100)=12.6 units/s. That's a reasonable speed.

During the collision at d~20, the speed will be ~25 units/s. The internal rotation speed at r=10 is 20 units/s. So the collision is "fast" relative to the internal motion? Actually the requirement for tidal tails is that the encounter is "fast" (impulsive) compared to the orbital time of stars in the outer parts. The internal orbital time at r=30 is T=2π*30/20≈9.4s. The encounter duration at speed 20 units/s over distance 50 is 2.5s. So it's impulsive enough to create tails.

Let's set G=4000, M=1 for each galaxy.

But then for the particles, the force from the own galaxy should use the same G*M. The particles are test particles in the combined field of both point masses. Since we set the galaxy centers as point masses, the particles will orbit them. However, the disk particles have a spread in mass distribution, but we approximate the own galaxy as a point mass. This means the central force is 1/r^2, so the rotation curve uses v ∝ r^{-1/2} instead of flat. To make the disk more extended and support the spiral arms, we'd want a flat rotation curve, which comes from an extended halo. We can use a Plummer potential for each galaxy, which gives a core radius a. At r >> a, the force is 1/r^2; at r << a, it's linear (harmonic). The rotation curve for Plummer is:
v_c(r) = sqrt(G*M * r^2 / (r^2+a^2)^(3/2))
This rises, peaks around r≈a/√2, and then falls as r^{-1/2}. It's not flat. To get a flat rotation curve, we'd need an isothermal halo.

For simplicity, let's not worry about flat rotation. The visual structure will still show some circular motion. The disk will undergo differential rotation (inner parts rotate faster - actually for Plummer, inner parts have v∝r, so solid body; outer parts v∝1/√r). This differential rotation will wind up any spiral pattern.

Alternatively, we can use a logarithmic potential for each galaxy: Phi(r) = v0^2 * ln(sqrt(r^2+a^2))? Gives flat rotation curve. The force is: F = -v0^2 * r / (r^2+a^2). This is nice. Let's do that. It's a common model: `Phi = 0.5 * v0^2 * log(r^2 + a^2)`, force per unit mass = -v0^2 * r / (r^2+a^2). The circular speed at r >> a is v0, and at r << a it's v0 * r / a (solid body). That gives a quite flat rotation curve with a smooth core.

Let's set v0 = 25 (units/s). Then the force from own center:
`ax = -v0^2 * R.x / (R.x^2 + R.y^2 + R.z^2 + a^2)`

Where R is the vector from the other center to the particle. For the other galaxy's gravity, we also use the same form, with the other center.

So the acceleration due to each center: `a = -v0^2 * (r_rel) / (|r_rel|^2 + a^2)` where a is the Plummer scale (softening) ~= 5.

This is a bit different from a point mass; it reproduces a flattened/constant-rotation galaxy. Great.

Now the galaxy centers interact with each other. Since the centers are point masses, their mutual acceleration should be the same force: `a_center1 = -v0^2 * (center1 - center2) / (|center1 - center2|^2 + a^2)`. But wait, v0^2 here is per galaxy mass; for the interaction between two centers of mass M, we'd want G*M. However, we can set the same v0 for both, as if their halos are extended. The interaction will thus be softened. This is fine.

But if both centers have mass M and the force is `v0^2 * r / (r^2+a^2)`, this is not symmetric when one is much more massive than the other if they were different; but since equal, it's symmetric.

Actually, if we use the same softened force for particles and centers, the total potential is a pair of logarithmic potentials. This is a well-defined N-body system that is stable and gives smooth dynamics. In the limit where the two galaxies overlap, their potentials add, and the centers feel each other's force.

So I'll use:
- `v0 = 25`
- `softening = 8` (scaled by the galaxy's core radius)
- Force from a center at C on a particle at P:
```
dx = P.x - C.x
dy = P.y - C.y
dz = P.z - C.z
r2 = dx*dx + dy*dy + dz*dz + softening*softening
inv_r2 = 1 / r2
ax += -v0^2 * dx * inv_r2
...
```
Yes, because F = -v0^2 * r / r^2 = -v0^2 * r / (r^2+a^2). So `ax = -v0^2 * dx / (r2)` where r2 already includes softening^2. Good.

This means the acceleration has units of (distance/time^2). With v0 = 25 units/s, and softening=8 units, at r=8 the acceleration is v0^2 * 8 / (64+64) = 625*8/128 = 39 units/s^2. At r=100, acc = 625*100/(10000+64)=6.2 units/s^2. Circular speed at r=100: v_c^2 = v0^2 * r^2 / (r^2+a^2) = 625 * 10000 / 10064 ≈ 621, v≈24.9. So v≈v0 for large r. Nice.

This gives a flat rotation curve. Stars in the outer disk move at ~25 units/s. The disk has radius 100, so orbital period at R=100 is T=2π*100/25=25s. That's a bit fast for the animation; over 30s, the galaxy will rotate once. That's okay, maybe a bit fast. We can slow it down to make it look more majestic. Set v0=15? Then T=2π*100/15≈42s. That's nice. The collision will also happen over a similar timescale.

Let's set v0 = 18, softening = 6. Then T(100)=2π*100/18=35s. Good.

Now the galaxy centers: If they interact with the same softened force, their relative acceleration is:
`a_rel = -2 * v0^2 * (c1 - c2) / (|c1-c2|^2 + a^2)`? Actually, the force on c1 due to c2's potential is `-v0^2 * (c1-c2) / (|c1-c2|^2 + a^2)`. The same for c2 with opposite sign. So relative acceleration = `-2*v0^2 * d / (|d|^2+a^2)`. This is a valid two-body interaction. At large separation, this is like gravity with G*M_eff = 2*v0^2. So the infall speed from rest at distance R to a small separation is v_infall ≈ sqrt(2 * 2 * v0^2 * (1/R_min - 1/R_max)) ~ sqrt(4*v0^2 / R_min) = 2*v0 / sqrt(R_min). With v0=18, R_min~30, v≈12.6 units/s. At R=100, v≈ 2*18/sqrt(100)=3.6? Wait, potential difference: ΔPhi = -2*v0^2 * ln((r2+a^2)/(r1+a^2)). Actually the integral of force is logarithmic, not 1/r. So the speed is not from simple formula.

Let's not over-calc; we'll just tune visually.

**Particle dynamics in the disk:**
We want particles to be on roughly circular orbits. In the logarithmic potential, the circular velocity at radius r is:
`v_c(r) = v0 * r / sqrt(r^2 + a^2)`
and the corresponding velocity vector in the disk plane (XZ) for a particle at angle theta is:
vx = -v_c(r) * sin(theta)
vz = v_c(r) * cos(theta)
Rotation direction: counterclockwise when viewed from +Y. Since the disk is in the XZ plane, we can define positions as:
x = r * cos(theta)
z = r * r?? Actually, in three.js, y is up. The disk plane will be X-Z, so position = (r * cos(theta), 0, r * sin(theta)). Velocity = (-v_c * sin(theta), 0, v_c * cos(theta)).

But to extend the particles in 3D with a thin disk, we add a small y velocity (vertical component) and a small y position, with a restoring force to keep them near the plane. Otherwise, particles will drift vertically due to gravity of the two centers. Actually, the logarithmic force from the centers is 3D and will pull particles back toward the plane if they have a y offset, since the potential is spherically symmetric (if we use the same softening for y). The force is `-v0^2 * y / (r^2 + a^2)`. This provides a restoring force to the plane. So if we give them some initial vertical dispersion, they'll oscillate. But to keep the disk thin, we can set the initial y positions and velocities to zero. In the collision, the vertical component gets excited, producing NGC-like shells, but the disk will remain relatively thin. Good.

So for each particle:
```
r = draw from distribution
theta = ...
x = r * cos(theta)
z = r * sin(theta)
y = 0
vx = -v_c(r) * sin(theta)
vz = v_c(r) * cos(theta)
vy = 0
```
But the positions are relative to the galaxy center. The galaxy center itself is moving. So we add the center's position and velocity to the particle's initial state.

**Generating the disk with spiral arms:**

Let's implement a function to generate particle data (position, velocity, color) for one galaxy.

Parameters:
- count = 20000
- v0 = 18 (rotation speed)
- scale = 25 (disk scale length)
- radius = 100 (max radius)
- thickness = 1 (scale height) Actually, lower thickness looks better for a disk.
- softening = 6 (for force, not generation)

Spiral arm parameters:
- arms = 2
- pitch = 15 degrees = 0.26 rad
- arm_fraction = 0.7
- arm_scatter = 0.4 (in radians)

Generation algorithm:

```
function generateGalaxy(count, colorInner, colorOuter) {
    const pos = new Float32Array(count * 3);
    const vel = new Float32Array(count * 3);
    const color = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
        let r, theta;
        const r_exp = -scale * Math.log(1 - Math.random()); // exponential
        // ensure within [0.5, radius]
        r = Math.min(r_exp, radius);
        // choose whether this particle belongs to an arm or the smooth disk
        if (Math.random() < 0.7) {
            // arm particle
            // spiral arm central angle at this radius
            const theta_arm = (Math.log(r / 10) / Math.tan(pitch)) + (i % arms) * (Math.PI * 2 / arms);
            theta = theta_arm + gaussianRandom() * 0.3;
        } else {
            theta = Math.random() * Math.PI * 2;
        }
        // Maybe re-generate radius for spiral arms? Since we selected r first, the distribution along the arm is exponential.
        // Add some spread in radius around the arm? 
        if (Math.random() < 0.3) r += (Math.random() - 0.5) * 10;
        
        const x = r * Math.cos(theta);
        const z = r * Math.sin(theta);
        const y = (Math.random() - 0.5) * 0.5; // very thin
        
        // circular velocity at this radius
        const v = v0 * r / Math.sqrt(r*r + softening*softening);
        const vx = -v * Math.sin(theta);
        const vz = v * Math.cos(theta);
        const vy = (Math.random() - 0.5) * 0.2;
        
        pos[...] = ...
    }
    return ...
}
```

But this doesn't create visible distinct arms if the scatter is large. We can make the arms more prominent by increasing the fraction of arm particles and reducing scatter.

Actually, there's a neat method using a "spiral pattern" density:
Generate a random (r, theta) from exponential distribution, then compute:
```
theta_arm = Math.log(r / r_inner) / Math.tan(pitch)
arm_value = Math.cos(2 * (theta - theta_arm))
if (arm_value < -0.6) { // this is between the arms? Actually the spiral potential minimum is at cos = 1
```
We need to bias theta towards the arms. Setting `delta = theta - theta_arm` and accepting if `abs(delta) < deltaMax` works but doesn't give a smooth density.

Let's use rejection sampling:
1. Propose r from exponential distribution, theta uniform.
2. Compute winding angle `phasor = Math.cos(arms * (theta - theta_arm(r)))`.
3. Compute probability of accepting in the arm/interarm: `p_arm = 0.8 + 0.7 * phasor` (so between 0.1 and 1.5). If `random() < p_arm / 1.5`, accept.
This will create spiral arms where the density is enhanced.

Actually, for a clear visual, a simpler approach that works surprisingly well:
- For each particle, pick a random value `t` in [0,1].
- If `t < 0.8`, place the particle on an arm (i.e., generate `r` and then set theta from the arm equation). Add Gaussian scatter in r and theta.
- Else, place it in the smooth disk.

Let's implement that.

```
function gaussian() {
    return (Math.random()+Math.random()+Math.random())-1.5; // approximate normal, mean 0, variance 0.25
}
```

But for 20k particles, we can use Box-Muller for simplicity.

Let me write a helper:
```
function randn() {
    let u = 0, v = 0;
    while (u === 0) u = Math.random();
    while (v === 0) v = Math.random();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}
```

Arm generation:
```
const armPitch = 0.35; // lower = tighter? Actually theta = log(r)/tan(pitch). pitch = arctan(0.35) ≈ 19.3 degrees.

for i in count:
  let r, theta;
  if (random() < 0.75) {
      // arm particle
      r = sampleExponential(scale);
      // require r > r_inner
      r = Math.max(r, 3);
      // central arm angle
      const theta_arm = Math.log(r / 3) / Math.tan(armPitch);
      // pick a random arm
      const armIndex = Math.floor(Math.random() * arms);
      const armPhase = (armIndex / arms) * 2 * Math.PI;
      theta = theta_arm + armPhase + randn() * 0.25;
      // Add radial scatter
      r *= Math.max(0.5, 1 + randn() * 0.1);
      // exponentially smooth? maybe
  } else {
      r = sampleExponential(scale);
      theta = Math.random() * 2 * Math.PI;
  }
  // impose max radius
  r = Math.min(r, radius);
```

For the exponential distribution, `r = -scale * Math.log(1 - Math.random())`. This gives a scale length of `scale`. With scale=25, most particles within 100.

But we want the arms to start at a radius, not in the center. The nucleus should be spherical/ellipsoidal smooth. The arms primarily in the disk. We can set the inner radius for arms to 10.

Let's define:
- `r_inner_arm = 10`
- For arm particles, sample r from a distribution that peaks at maybe 30 and extends to 100. But if we use exponential, a lot of particles are in the center. We can use `r = (r_inner + (radius-r_inner)*Math.pow(Math.random(), 0.7))` to get a density that decreases outward but not as strongly. Actually the stellar disk is exponential, so inner regions have more stars. We can keep that.

For the central bulge (warm yellow core), we can generate a third population of particles that are spherically distributed with a small radius. The requirement says "bright core"; we can render a bright point at the center, or give the core a higher density of warm-colored particles. Since we use additive blending, a dense cluster of yellow particles at the center will naturally look like a bright core. So in our galaxy generator, we can make the central 10 units populated with a spherically symmetric bulge (density ∝ exp(-r^3/a^3) maybe). But we have only 20k particles; if many are in the core, fewer go in arms. But a bright core needs many particles. Perhaps 80% of the 20k are in the disk and 20% in the bulge. The bulge particles are concentrated in the central 15 units, yellow/orange.

Let's set:
- 80% disk particles (some in arms).
- 20% bulge particles (spherical, smaller radius, warmer colors).

Actually, to make a visible thin disk with arms, the bulge should be small and compact. Let's try:
- 70% disk
- 15% bulge
- 15% halo? Halo not needed.

But the request specifically: "two disk galaxies with visible spiral arms and a bright core" - so we need a bright core. We can simply place a small number of particles at the center with a bright yellow color, and also add a PointLight? No, the additive blending on a dense cluster will glow.

Maybe create a couple of THREE.Points with different sizes? No, use the same point cloud. We can add a `sprite` at the center for each galaxy to make the core bright, but that's extra.

Let's just make the central region have a higher density of particles (bulge), and the color gradient is yellow in the center, blue/white in the arms. The additive blending of many yellow particles in the center will create a bright core.

**Physics integration:**

Let's design the integration loop with substeps.

We'll store:
```
const numParticles = count1 + count2;
const positions = new Float32Array(numParticles * 3);
const velocities = new Float32Array(numParticles * 3);
const colors = new Float32Array(numParticles * 3);
```

Similarly, we have `centerPos` (array of 2 Vector3), `centerVel` (2 Vector3). Or just separate variables.

But to generate each galaxy separately, we can generate with a center position/velocity offset.

Let's use an object:
```
const galaxies = [
    { pos: new THREE.Vector3(120, 0, 0), vel: new THREE.Vector3(0, 0, -20), ... },
    { pos: new THREE.Vector3(-120, 0, 0), vel: new THREE.Vector3(0, 0, 20), ... }
];
```

Each has `particleCount`, `posOffset`, `velOffset`.

Actually, when generating, we create particles relative to the center at rest, then add the center's initial velocity to the particle velocities.

**Update loop (pseudo):**

```
function update(dt) {
    // substeps
    const steps = 2;
    const h = dt * simSpeed / steps;
    for (let s=0; s<steps; s++) {
        // integrate centers
        // compute force between centers
        // update center velocities, positions
        // integrate particles
        // compute accelerations for each particle from both centers
        // update particle velocities, positions
    }
    // update geometry attributes
}
```

We'll use symplectic Euler (semi-implicit Euler) or leapfrog. Symplectic Euler: update velocity first, then position using new velocity. For the centers:
```
let d = c2.pos - c1.pos;
let r2 = d.lengthSq() + soft2;
let inv = -v0drive / r2;  // actually a_center = -v0^2 * d / r2
let a1 = d * inv;
c1.vel += a1 * h;
c2.vel -= a1 * h;
c1.pos += c1.vel * h;
c2.pos += c2.vel * h;
```
But note: c1.vel is velocity of center1. Since c2 has the opposite acceleration, we can update both.

For particles, the acceleration from both centers:
```
let dx1 = p.pos.x - c1.pos.x; // or p.x - c1.x
...
let r1sq = dx1*dx1 + dy1*dy1 + dz1*dz1 + soft2;
let inv1 = v0sq / r1sq; // since F = -v0^2 * dx / r2
ax += -inv1 * dx1;
...
```
Wait, if r2 already includes softening, then accel = -v0^2 * dx / r2. So `inv = v0sq / r2`, `ax += -inv * dx`.

Then:
```
vx += ax * h;
px += vx * h;
```
This is the velocity Verlet-like.

For stability, we can use leapfrog where we compute acceleration from current positions, update velocities half a step, update positions, recompute, update velocities another half step. But symplectic Euler is simpler and good enough.

Given 2 substeps per frame, we want `h = dt * timeScale / 2`.

**Time scale and simulation speed:**
We'll use a global `simTime` in Myr? Actually it's a simulation time label. We need to display time in millions of years. Let's define `simRate` = (code units per second) convert to Myr: if we assume 1 code unit = 1 kpc and 1 second sim = 1 Myr? Then the animation would be slow. We can set the displayed time = elapsedSimTime in some units.

Let's decouple: the simulation is running at some speed relative to real-time. We can define `timePerSecond` = e.g., 5 Myr per real second. Then after t real seconds, `simTime = t * timePerSecond` million years. We also need the physical time step for integration. The integration time step is not directly the Myr; it's in code units.

So what is the conversion between the code time unit and Myr? It's determined by the chosen v0 and distances. If v0 = 18 code units/s, and we say 1 code unit = 1 kpc = 3.09e16 km, v0 = 18 units/s = 18 kpc / s. That's obviously not physical. But we can ignore units and just say the label shows e.g. `t = ${simTime} Myr`, where `simTime` is integrated using a factor: `simTime += dt * 50` (Myr). We can tune to match the simulation visual.

Alternatively, we can set the initial velocity/positions such that one complete orbit takes, say, 1e8 years. But then the physics time step in seconds would need to be very small.

Since it's a scientific visualization, the label can be illustrative. We'll just use a time factor that makes the collision last ~30 seconds. In 30 sec of animation, the galaxies start at 300 units apart, fall together, collide at ~5-10 sec, and interact until 30 sec. We can set `simSpeed` factor such that `dt_physics = dt_real * simSpeed`. The displayed time = dt_physics * MyrPerCodeUnit.

Let's choose: 1 code unit = 1 kpc, 1 second (real) = 1 Myr? Then the simulation runs at 1 Myr/sec. Over 30 seconds, 30 Myr. Is a collision of two galaxies inside 30 Myr realistic? No, a collision takes ~1 billion years. But it's a cinematic visualization, time compressed. We can display `simTime = accumulatedDt * (100 Myr / 30 sec)` maybe. Actually, we want to show time in Myr; if the encounter lasts 30 seconds, maybe we want it to represent hundreds of Myr. So set displayed time `T_Myr = elapsedRealSec * (300 Myr / 30 sec) = 10 Myr/sec`. That means the label will go from 0 to 300 Myr.

And the code time step `h` is in seconds (real) times a time scale to get the desired orbital dynamics. The orbital velocities we set (v0=18 units/s) are in code units per (real second). This means 1 real second corresponds to the time it takes for stars to move 18 units. If we want the physical time to compress by a factor, we can just say that the simulation runs at real-time speed, and assign the Myr label by mapping. The important thing is that the motion looks right.

Let's not overcomplicate. We'll:
- Use `dt = clock.getDelta()` from the rAF timestamp? Actually, `requestAnimationFrame` passes a timestamp to the callback. We can use that to compute deltaTime in seconds.
- Simulation physics uses `h = Math.min(dt, 0.05) * simSpeed`, where `simSpeed` is a multiplier to make the collision happen in a pleasing time. Default `simSpeed = 1`, meaning the code units are in seconds. With v0=18 units/s, a galaxy outer star at r=100 takes T=2π*100/18=35s to orbit. That's a bit slow. We can increase `simSpeed` to 2 or 3 to make it more dynamic. Let's set `simSpeed = 4` so that the outer rotation is ~4*? wait, if we increase simSpeed, then for a given h, the accelerations are multiplied by simSpeed? Actually, if we use the equations with v0 in code units, and then run substeps with `h = dt * simSpeed`, then the effective velocity over the simulation is multiplied by simSpeed. So the outer orbit period becomes 35s / 4 ≈ 8.75s. That's good.

But there's a subtlety: the acceleration is `-v0^2 * r / r2`. If we integrate with a time step `h`, the position update is `p += v*h`. If h is larger, the particle moves faster. So `simSpeed` just multiplies the time step. That's equivalent to speeding up the simulation.

So set `simSpeed = 5`. Then the collision time scale is ~10 seconds for the infall, and total animation ~40 seconds. Good.

We can also set the displayed Myr: `displayTime += dt * (250 Myr / 60 sec) * (simSpeed / 5)` etc. We'll just define:

```
const simTimeScale = 5; // code seconds per real second? Actually simSpeed.
```

Let's define a global `timeScale = 5.0` and `h = dt * timeScale`.

For the label, we'll accumulate `simTimeMyr += dt * 10 * (timeScale / 5);` so that the label goes to ~300 Myr over 30 sec at timeScale=5.

Actually, to avoid hardcoding, we can set `MyrPerCodeSec = 2` and `displayTime += dt * timeScale * MyrPerCodeSec`. With timeScale=5, that gives displayTime += dt*10. Over 30s, 300 Myr. Good.

**Rendering:**

We'll create a `THREE.Points` with a `BufferGeometry` containing `position` and `color`. We'll use a `ShaderMaterial` for additive blending and soft points.

The vertex shader:
```
attribute float size;
varying vec3 vColor;
void main() {
    vColor = color;
    vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
    gl_PointSize = size * (300.0 / -mvPosition.z);
    gl_Position = projectionMatrix * mvPosition;
}
```
But we need a `size` attribute. We can compute `size` based on the particle's radius (larger for core?) or just use a uniform size. Actually, for a bright core, we can make core particles bigger. Let's add a `size` attribute. But to keep memory low, we can compute in the shader from color? Eh, just add a `size` attribute.

Alternatively, use a fixed size for all, and rely on density for brightness. With additive blending, if 20k particles overlap in the center, it'll be bright. But point size should be around 2-4 pixels.

Let's use a uniform `uPointSize` and maybe a `size` attribute if needed.

Fragment shader:
```
varying vec3 vColor;
void main() {
    vec2 c = gl_PointCoord - vec2(0.5);
    float dist2 = dot(c,c);
    if (dist2 > 0.25) discard;
    float alpha = 1.0 - smoothstep(0.0, 0.25, dist2);
    gl_FragColor = vec4(vColor * alpha, 1.0);
    // with additive blending: blending: THREE.AdditiveBlending, transparent: true
}
```

For additive blending with ShaderMaterial, we need:
```
blending: THREE.AdditiveBlending,
depthWrite: false,
transparent: true
```

We should also set `gl_PointSize` based on `viewZ`. Use `uSize` uniform:

```
uniform float uSize;
...
gl_PointSize = uSize * (scale / -mvPosition.z);
```
where scale is the canvas height in pixels? Actually, for perspective, we want `gl_PointSize = uSize * uPixelRatio * (height / 2) / -mvPosition.z`. Let's use:
```
gl_PointSize = uSize * (300.0 / -mvPosition.z);
```
where 300 is the focal length in pixels (approx). We can multiply by renderer.getPixelRatio().

Maybe:
```
uniform float uPointScale;
...
gl_PointSize = uPointScale / -mvPosition.z;
```
Then set `uPointScale = renderer.getHeight() * 0.5 * pixelRatio * pointSizeFactor`.

Let's simplify: use `THREE.PointsMaterial` with `map` and `sizeAttenuation: true`. This handles point size automatically. But to have additive blending and a glowing sprite, we need `map`. Using a canvas texture is okay. That might be simpler than a ShaderMaterial. Let's compare.

With PointsMaterial:
- `size` is in world units? Actually in three.js, `size` is in pixels (unless sizeAttenuation true). We can set `size: 2` (pixels?), `sizeAttenuation: true`.
- `vertexColors: true` uses per-vertex color.
- `map` can be a CanvasTexture.
- `blending: THREE.AdditiveBlending`, `transparent: true`, `depthWrite: false`.

This is very simple and enough. But the point size will be uniform for all vertices. Is that okay? Yes, we can have a uniform size. The core will be naturally bright from overlapping points.

Let's use that first. If performance is an issue, we can optimize later.

But wait, with 40k points, the overhead of PointsMaterial is fine. Let's go with PointsMaterial.

**Creating the sprite texture:**

A radial gradient in a canvas:
```
function createSprite() {
    const size = 64;
    const canvas = document.createElement('canvas');
    canvas.width = size; canvas.height = size;
    const ctx = canvas.getContext('2d');
    const gradient = ctx.createRadialGradient(size/2, size/2, 0, size/2, size/2, size/2);
    gradient.addColorStop(0, 'rgba(255,255,255,1)');
    gradient.addColorStop(0.5, 'rgba(255,255,255,0.5)');
    gradient.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = gradient;
    ctx.fillRect(0,0,size,size);
    return new THREE.CanvasTexture(canvas);
}
```
With additive blending, the sprite's color is multiplied by the vertex color, so the white texture becomes the particle color.

**Background stars:**

We need a dark starfield background. We can create a second Points object with maybe 3000 stars distributed on a large sphere or cube. Each star white, additive blending also? Or just a Points with basic material. Since we're using a camera moving slowly, parallax will show if the background is at infinity. We'll make the starfield at a distance of 2000.

Create:
```
const starsGeometry = new THREE.BufferGeometry();
const starsPos = new Float32Array(3000*3);
for (...) {
    // random on a sphere of radius 1000-3000
}
const starsMaterial = new THREE.PointsMaterial({
    color: 0xffffff,
    size: 1,
    sizeAttenuation: false,
    map: createSprite(),
    blending: THREE.AdditiveBlending,
    transparent: true,
    depthWrite: false
});
```

Or just set points far away. Make sure `sizeAttenuation: false` so they are constant size.

**Camera control:**

"Slowly orbiting camera that frames the whole event." We'll create a perspective camera and update its position in the animation loop. We can use a simple orbit around the center of mass (origin), with radius maybe 350 units, height 150 units, and angle slowly increasing.

```
camera.position.x = 250 * Math.cos(t * 0.05);
camera.position.z = 250 * Math.sin(t * 0.05);
camera.position.y = 120 + 20 * Math.sin(t * 0.1);
camera.lookAt(0,0,0);
```

But the galaxies start at ±120, so a radius of 250 is good to fit them. When they merge, the system stays near the origin. Use a fixed orbit radius 300, height 150.

Also add a `THREE.OrbitControls`? The request says "no interaction needed", but it might be okay to add controls. However, it says "no interaction needed" - so auto-orbit is enough.

**Resizing:**

Add window resize listener:
```
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});
```

**Time label:**

Create a div or use HTML text overlay. Show `Time: ${simTimeMyr.toFixed(1)} Myr`. Use a small font, top-left corner.

**Putting it all together:**

Let me code this carefully.

First, setup the scene:
```
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(60, window.innerWidth/window.innerHeight, 0.1, 5000);
const renderer = new THREE.WebGLRenderer({antialias: true});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
document.body.appendChild(renderer.domElement);
```

Now the physics.

We'll have two galaxies, each with:
- `centerPos` Vector3
- `centerVel` Vector3
- `particleCount`
- ranges in the global arrays.

Let's define global arrays:
```
const MAX_PARTICLES = 50000;
const positionAttr = new THREE.BufferAttribute(new Float32Array(MAX_PARTICLES*3), 3);
const colorAttr = new THREE.BufferAttribute(new Float32Array(MAX_PARTICLES*3), 3);
```
But we don't know the total count until we generate. We can use dynamic arrays.

Let's set N1 = N2 = 20000. Total = 40000.

Create Float32Array:
```
const positions = new Float32Array(total * 3);
const velocities = new Float32Array(total * 3);
const colors = new Float32Array(total * 3);
```

But we also need per-particle size? No, not with PointsMaterial.

We'll generate galaxy 1 starting at index 0, galaxy 2 at index N1.

Let me define a function:
```
function generateGalaxy(count, centerPos, centerVel, colorInner, colorOuter, rotDir) // rotDir is +-1
```
Actually, we use `rotDir = 1` for both if we want both to rotate the same way. For the collision to be prograde, both disks should rotate in the same direction relative to the orbit. If the centers orbit counterclockwise, we want the stars to also rotate counterclockwise? For an encounter, prograde means the disk's rotation is in the same sense as the orbital motion. If both disks are co-rotating (same rotation axis and direction) and the orbit is prograde, that gives strong tidal features. We'll just set both to counterclockwise (v = v_c * (-sin, 0, cos)). We'll also choose the orbital motion to be counterclockwise in the XZ plane: for c1 at (120,0,0) and c2 at (-120,0,0), if c1 has velocity (0,0,-20) and c2 (0,0,20), the orbital angular momentum is along +Y (using right-hand rule: r1 = (120,0,0), v1 = (0,0,-20), r×v = (0,0, -20)? Wait, r cross v in 3D: (x,y,z) cross (vx,vy,vz) = (y*vz - z*vy, z*vx - x*vz, x*vy - y*vx) = (0, -z*? Actually z=0, vy=0, x=120, vz=-20, so = (0, 120*20? 120*-20? Let's compute: component y = z*vx - x*vz = 0 - 120*(-20)= 2400, so +Y). Good. So orbit angular momentum is +Y. The internal rotation is counterclockwise when viewed from +Y, so also +Y. That's co-rotating/prograde.

Alright.

**Color assignment:**

Color gradient:
- Inner 0-10 units: yellow (1.0, 0.8, 0.3)
- Mid 10-50: white (0.9, 0.9, 1.0)
- Outer 50-100: blue-white (0.7, 0.8, 1.0)

Let's write a `getColor(r, size)`:
```
const t = Math.pow(r / size, 0.6);
const c = new THREE.Color();
if (t < 0.5) {
    c.lerpColors(new THREE.Color(1.0, 0.75, 0.4), new THREE.Color(0.9, 0.9, 1.0), t*2);
} else {
    c.lerpColors(new THREE.Color(0.9, 0.9, 1.0), new THREE.Color(0.6, 0.7, 1.0), (t-0.5)*2);
}
```
But for the bright core, maybe we want more yellow. We'll use a simpler function: `color = new THREE.Color().setHSL(0.12 - 0.4 * t, 0.8, 0.4 + 0.6*t)`? Actually, yellowish core and blue arms. Hue of yellow ~0.12, blue ~0.6. So hue = 0.6 - (0.6-0.12)*t? Not all the way because the outer is blue-white, not pure blue. Let's just use an array of colors.

Maybe:
```
const inner = new THREE.Color(1.0, 0.7, 0.3);
const mid = new THREE.Color(1.0, 0.9, 0.9);
const outer = new THREE.Color(0.3, 0.5, 1.0);
```
For a particle at radius r, if r< r_in, color=inner, else lerp.

Let's define `r_norm = Math.min(1, r / maxRadius)` and:
- hue = 0.15 - 0.3 * r_norm? Hmm.

Simpler: use a linear ramp:
```
color = new THREE.Color();
color.lerpColors(inner, mid, Math.min(1, r / 20));
if (r > 20) color.lerpColors(mid, outer, Math.min(1, (r-20)/80));
```

We'll compute color at generation.

**Implementing the generator:**

Let me write `addGalaxy(count, centerPos, centerVel)` but I need to handle arrays. I'll create a standalone function that fills arrays given the galaxy parameters.

I'll use the actual THREE.js Vector3 for centers but arrays for particles.

Let's define:
```
const gal1 = { pos: new THREE.Vector3(120, 0, 0), vel: new THREE.Vector3(0, 0, -20), start: 0, count: N1 };
const gal2 = { pos: new THREE.Vector3(-120, 0, 0), vel: new THREE.Vector3(0, 0, 20), start: N1, count: N2 };
```
Then for each galaxy, generate particle states relative to the center, add center pos/vel.

But our `generateGalaxy` will just fill positions, velocities, colors for that galaxy. The centers are integrated separately.

Parameters:
```
const V0 = 18;        // rotation curve amplitude
const SOFT = 6;       // softening length (also used in generation)
const SCALE = 25;
const RADIUS = 100;
const THICK = 0.5;    // 1-sigma thickness
const ARMS_FRACTION = 0.75;
const PITCH = 0.35;   // tan(pitch)
const INNER_R = 3;
```

Function `gaussian()`:
```
function gaussian() {
    let s = 0;
    for (let i=0; i<6; i++) s += Math.random();
    return (s - 3) / 2; // approx standard normal
}
```
But Box-Muller is cleaner.

In `generateGalaxy(count, posAttr, velAttr, colorAttr, offset, colorInner, colorOuter)`:
```
for (let i=0; i<count; i++) {
    // determine if arm or smooth
    const isArm = Math.random() < ARMS_FRACTION;
    let r, theta;
    if (isArm) {
        // sample r from exponential or power
        r = -SCALE * Math.log(1 - Math.random());
        r = Math.max(r, INNER_R);
        const thetaArm = Math.log(r / INNER_R) / PITCH;
        const armIdx = Math.floor(Math.random() * 2);
        theta = thetaArm + armIdx * Math.PI + gaussian() * 0.3;
        // add radial scatter
        r *= Math.max(0.3, 1 + gaussian() * 0.15);
    } else {
        r = -SCALE * Math.log(1 - Math.random());
        theta = Math.random() * Math.PI * 2;
    }
    r = Math.min(r, RADIUS);
    
    const x = r * Math.cos(theta);
    const z = r * Math.sin(theta);
    const y = gaussian() * THICK * (1 + 0.1 * r / RADIUS); // slightly flared? or constant thickness
    
    const vCirc = V0 * r / Math.sqrt(r*r + SOFT*SOFT);
    const vx = -vCirc * Math.sin(theta);
    const vz = vCirc * Math.cos(theta);
    const vy = 0; // maybe gaussian() * 1.0
    
    // write to arrays at (offset + i)*3
    // ...
}
```

This will create a disk. But note that if we sample r from exponential, the arms will have exponential profile, so the inner parts have more particles. Because of the arm scatter in theta, the arms might be smeared. Let's test mentally: at r=10, thetaArm = log(10/3)/0.35 ≈ 3.43 rad. At r=50, thetaArm = log(50/3)/0.35 = 7.6 rad. The arms are tightly wound (pitch 0.35), so they wind around. The random Gaussian scatter of 0.3 rad in theta is relatively small. This should produce a two-armed spiral.

However, the exponential sampling puts most particles in the inner region, so the arms may be densely populated only in the inner few tens of units. To have beautiful arms, we might want to sample r from a disk with a peak around some radius, e.g., using a distribution `r * exp(-r/SCALE)` which peaks at r=SCALE. Actually, an exponential disk in surface density: Σ(r) = exp(-r/h), and sampling uniformly in r with 2πr gives `r * exp(-r/h)` distribution. In the code above, `r = -h * ln(1-u)` samples according to Σ(r) * 2πr? No, sampling r from p(r) ∝ exp(-r/h) * r? Actually, if you want surface density exponential, you sample r from p(r) ∝ r * exp(-r/h)? Wait, the number of particles per unit radius is 2πr Σ(r). If Σ(r) = exp(-r/h), then p(r) ∝ r exp(-r/h). To sample r: first sample uniform u, solve cumulative. The CDF is 1 - (1 + r/h) exp(-r/h). There's a simple inverse: `r = -h * (ln(1 - u) + something)`. Actually, if you use `r = -h * ln(1 - u)`, the distribution is p(r) = (1/h) exp(-r/h), which corresponds to surface density Σ ∝ exp(-r/h)/r, i.e., a central cusp. But it still gives particles in the center. We can use this; the visual effect may be a bright center, which is okay.

For a more realistic disk, we can use:
```
r = -SCALE * Math.log(1 - Math.random()); // this gives p(r) ~ exp(-r/SCALE)
```
This is the surface density integrated? Not exactly. It's fine.

But for the arms to be visible at larger radii, we need enough particles there. With exponential sampling, ~39% of particles have r>SCALE=25 (at 25), ~14% have r>50. So there are plenty of outer particles. Good.

The pitch angle of 0.35 is about 19 degrees. That's a bit high but okay. Tidal tails in real galaxies are very thin; we'll see.

**Velocity dispersion:**
To support the disk, we need some velocity dispersion to match the thickness. But giving exact dispersion requires solving the Jeans equations. We can approximate by adding a dispersion of `sigma = 0.2 * v_circ` in the theta direction (epicyclic approximation). Or simply add 5% noise. However, if the disk is too cold, it might form rings; too hot and it's messy. We'll add a small random to `vx`, `vz` (2% of v_circ) and maybe no vertical dispersion. This keeps the disk thin.

Actually, for the disk to be stable and not rapidly collapse, we should set the particles in near-circular orbits. The radial scatter in positions already gives some spread. Add:
```
vx += gaussian() * vCirc * 0.05;
vz += gaussian() * vCirc * 0.05;
vy += gaussian() * vCirc * 0.02;
```
This is fine.

**Center initialization:**
After generating positions/velocities relative to center, we need to add the center's initial position and velocity to the segments.

For a particle at index i:
```
const idx = (offset + i)*3;
positions[idx] = x + centerPos.x;
positions[idx+1] = y + centerPos.y;
positions[idx+2] = z + centerPos.z;
velocities[idx] = vx + centerVel.x;
velocities[idx+1] = vy + centerVel.y;
velocities[idx+2] = vz + centerVel.z;
```

The colors are same for both galaxies.

**Bulge generation:**

To make a bright core, we can add a spherical bulge. Let's incorporate into the generator:
- With probability `BULGE_FRACTION = 0.2`, generate a bulge particle:
  ```
  r = Math.pow(Math.random(), 2) * 15;
  // random sphere
  x = r * randn(); y = r * randn(); z = r * randn(); // or spherical coords
  ```
  and give a velocity that is just from the bulge's potential? We can set it on a circular orbit in the disk plane? For a spherical bulge, velocity is random. To avoid particles flying off, we need to support them against the gravitational potential. But if we set their positions in a small sphere and zero net velocity besides what? Actually, the galaxy's potential is from both centers (initialized as point masses). Bulge particles on random orbits with the same circular velocity at that radius will approximate a pressure-supported spheroid if we give them isotropic velocity dispersion. We can set:
  ```
  v_circ = V0 * r / sqrt(r^2 + SOFT^2);
  // dispersion
  sigma = v_circ / Math.sqrt(2); // for isothermal
  vx = gaussian() * sigma;
  vy = gaussian() * sigma;
  vz = gaussian() * sigma;
  ```
  This gives a nice spheroid.

But this complicates. Since the center has many particles from the exponential disk, the core will be bright anyway. The requirement "bright core" can be satisfied by the high density of disk particles with warm colors. I'll skip a separate bulge to keep the spiral arms prominent.

Actually, the exponential disk surface density diverges at center (due to the p(r) ∝ exp(-r)/r) which creates a central concentration. That might serve as the bulge.

**Integrating the physics:**

Now for the main loop. We'll use the arrays we generated.

```
const dt = Math.min(deltaTime, 0.1);
const simDt = dt * simSpeed; // use simSpeed as multiplier

for (let step=0; step<numSubsteps; step++) {
  const h = simDt / numSubsteps;
  
  // update centers
  const dx0 = gal2.pos.x - gal1.pos.x;
  const dy0 = gal2.pos.y - gal1.pos.y;
  const dz0 = gal2.pos.z - gal1.pos.z;
  const d2 = dx0*dx0 + dy0*dy0 + dz0*dz0 + SOFT*SOFT;
  const inv = V0*V0 / d2;
  const ax = inv * dx0;
  ...
  gal1.vel.x += ax * h; // wait, we want acceleration = -V0^2 * dx / d2
```
Let's derive: acceleration on gal1 due to gal2 = -V0^2 * (r1 - r2) / (|r1-r2|^2 + SOFT^2). So if `dx = gal1.x - gal2.x`, then a1 = -V0^2 * dx / d2. Similarly a2 = -V0^2 * (gal2.x - gal1.x)/d2 = +V0^2 * dx / d2.

So:
```
const dx = gal1.pos.x - gal2.pos.x;
...
const accelScale = -V0*V0 / (dx*dx + dy*dy + dz*dz + SOFT*SOFT);
gal1.vel.x += dx * accelScale * h;
...
gal2.vel.x -= dx * accelScale * h; // since gal2 - gal1 = -dx
```
Yes.

Then position:
```
gal1.pos.x += gal1.vel.x * h;
...
```

Wait, if we update velocities first (symplectic Euler), the positions should be updated with new velocities. That gives energy conservation approximately. Good.

For particles, we loop over all particles. To compute forces, we need both centers.

```
for (let i=0; i<totalParticles; i++) {
    const idx = i*3;
    let px = positions[idx];
    let py = positions[idx+1];
    let pz = positions[idx+2];
    let vx = velocities[idx];
    ...
    // forces
    let axn = 0;
    let ayn = 0;
    let azn = 0;
    for (let g=0; g<2; g++) {
        const gx = galaxies[g].pos.x;
        ...
        const dxn = px - gx;
        const dyn = py - gy;
        const dzn = pz - gz;
        const d2n = dxn*dxn + dyn*dyn + dzn*dzn + SOFT*SOFT;
        const invn = V0*V0 / d2n;
        axn -= invn * dxn;
        ayn -= invn * dyn;
        azn -= invn * dzn;
    }
    vx += axn * h;
    vy += ayn * h;
    vz += azn * h;
    px += vx * h;
    ...
    // write back
}
```

This is O(N) per substep, with 40k particles, 2 substeps = 80k, fine.

But we also need to update the BufferGeometry after the integration. We can use `geometry.attributes.position.array = positions`? Actually, if we reuse the arrays directly, we can create the geometry with those arrays, and update the `needsUpdate` flag every frame. That's the fastest way: create a `THREE.BufferAttribute` that wraps the Float32Array, and after updating the array in place, set `geometry.attributes.position.needsUpdate = true;`.

We'll create:
```
const geometry = new THREE.BufferGeometry();
geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
```
Then in the animation loop, after modifying `positions`, do:
```
geometry.attributes.position.needsUpdate = true;
```

**Performance considerations:**

40k particles is fine for CPU update. But doing 80k force calculations per substep and 2 substeps = 160k operations, trivial.

**Camera path:**

We'll orbit the origin:
```
const t = clock.getElapsedTime();
camera.position.x = 280 * Math.cos(t * 0.08);
camera.position.z = 280 * Math.sin(t * 0.08);
camera.position.y = 120 * Math.sin(t * 0.05) + 120;
camera.lookAt(0, 0, 0);
```
This gives a slow orbit around the scene.

But if the galaxies are coplanar in XZ, viewing from above (high y) shows the disk face-on; viewing from y=0 shows edge-on. The orbit will go through various angles, nice.

**The label:**
HTML:
```
<div id="time">Time: 0 Myr</div>
```
CSS:
```
position: absolute; top: 10px; left: 10px; color: white; font-family: sans-serif; z-index: 100;
```

**Uniform handling with PointsMaterial:**

For PointMaterial, we set `size`. To make the points look like stars, set `size: 2.5`, `sizeAttenuation: true`. But size attenuation uses distance to camera, so points farther away appear smaller. That's fine. The canvas texture gives a soft falloff.

We also need `vertexColors: true` so that `color` attribute is used.

```
const material = new THREE.PointsMaterial({
    color: 0xffffff,
    size: 3,
    map: createSprite(),
    vertexColors: true,
    blending: THREE.AdditiveBlending,
    transparent: true,
    depthWrite: false,
    sizeAttenuation: true
});
```

However, additive blending with a sprite that has alpha will cause the center of the sprite to be bright. Good.

One issue: by default, `Points` render as squares with gl_PointCoord. The canvas texture will be used as alpha. Good.

**Starfield background:**

Create another Points object with `size` in pixels (sizeAttenuation false). Far away, e.g., 1500. Use white points.

```
const bg = new THREE.Points(
  new THREE.BufferGeometry(),
  new THREE.PointsMaterial({
    color: 0xffffff,
    size: 1.5,
    sizeAttenuation: false,
    map: createSprite(),
    blending: THREE.AdditiveBlending,
    transparent: true,
    depthWrite: false
  })
);
const bgPos = new Float32Array(5000*3);
for (let i=0; i<5000; i++) {
    const theta = Math.random()*Math.PI*2;
    const phi = Math.acos(2*Math.random()-1);
    const r = 1500 + Math.random()*500;
    bgPos[i*3] = r*Math.sin(phi)*Math.cos(theta);
    bgPos[i*3+1] = r*Math.sin(phi)*Math.sin(theta);
    bgPos[i*3+2] = r*Math.cos(phi);
}
bg.geometry.setAttribute('position', new THREE.BufferAttribute(bgPos, 3));
scene.add(bg);
```

**Fixing the color attribute:**

In `PointsMaterial`, setting `vertexColors: true` uses the `color` attribute. We must normalize colors to 0..1. Our `colors` array holds 0..1 values.

**Potential issues:**

1. The galaxies might drift out of the camera's view as they interact. With the mutual interaction, the center of mass is conserved; since initial momenta sum to zero (c1 has vel -20z, c2 +20z, equal masses, so net momentum 0), the center of mass will stay at origin. The system stays near origin, so camera framing will work.

2. Particle velocities: We set initial velocities with `centerVel` added. The centers are at rest in the simulation's COM frame? Yes because c1.vel = (0,0,-20), c2.vel=(0,0,20), so total momentum 0.

3. Tidal field: The two galaxy potentials are superposed. If particles from the outskirts are bound to their galaxy initially, the additional gravity from the other galaxy will perturb them. That's fine.

4. Softening and time step: The maximum speed near the center of a galaxy with V0=18 and SOFT=6: at r<<SOFT, acceleration ≈ -V0^2 * r / SOFT^2 = -(324/36)*r = -9*r, so it's a harmonic oscillator with frequency ω=3 rad/s. The orbital period near the center is T≈2π/ω≈2s. Our substeps need to resolve this: h should be << 0.5s. With substeps=2 per frame at 60fps, h≈0.5/2=0.25s (with simSpeed=5), which is too large. Wait, h = dt * simSpeed * (1/numSubsteps). At 60fps, dt=1/60≈0.0167s. simSpeed=5, h=0.083s. numSubsteps=2 → h=0.0417s. That's okay for an oscillator period of 2s? 2s period, h=0.04, 50 steps per period, fine.

But wait, the equation I derived for r<<SOFT had frequency sqrt(V0^2/SOFT^2) = V0/SOFT = 18/6 = 3 rad/s → period 2.1s. So h=0.08s is 26 steps per period, fine.

5. The collision will be messy because the galaxies are described by point mass potentials, not extended disks. When two point-mass galaxies merge, their stars will be flung around. That's fine for visualization.

**Adding collision detection?**

When the centers get very close (r < 10), the force can become strong if not softened; but it is softened.

**Label update:**

We accumulate `timeMyr += dt * simSpeed * MyrPerSec`. We'll set `MyrPerSec = 2`. With simSpeed=5, that's 10 Myr per real second. Over 30s → 300 Myr. Good.

**Adding the time label:**

```
const timeLabel = document.getElementById('time');
function animate() {
    requestAnimationFrame(animate);
    const dt = Math.min(clock.getDelta(), 0.1);
    timeMyr += dt * simSpeed * 2;
    timeLabel.textContent = `Time: ${timeMyr.toFixed(0)} Myr`;
    ...
}
```

**Full code tuning:**

Let's tweak the generator to make spiral arms more apparent. The `isArm` fraction 0.75 might result in a smooth disk. The Gaussian scatter in theta (0.3 rad) might be okay. But the arm pitch 0.35 means the arms wind rather tightly; with exponential sampling, most particles are in the inner 25 units, so the arms will be visible there. Good.

We can also add a "background disk" particles (the 25%) to fill the gaps. This should give nice structure.

Let's set `ARMS_FRACTION = 0.85` to make arms more dominant. And `PITCH = 0.45` (i.e., theta = ln(r/rin)/0.45, lower pitch = tighter). Actually `PITCH` here is `tan(pitch)`. A value of 0.35 corresponds to ~19 degrees. A value of 0.2 corresponds to 11 degrees, which is more realistic (grand design spirals have pitch ~10-20). Let's set `PITCH = 0.25`, `SCATTER = 0.4` rad. The arms will be distinguishable.

But if the pitch is small, the arms wind quickly? The equation `theta = ln(r/r_inner) / tan(pitch)`. For `r_inner=5`, `r=100`, `tan(pitch)=0.25`, theta = ln(20)/0.25 = 12 rad, so about 2 full turns. That's good.

Let me set:
- `PITCH_TAN = 0.3`
- `theta_arm = Math.log(r / 5) / PITCH_TAN`

With `r_inner = 5`.

But note: I used `Math.log(r / INNER_R)`. If `r < INNER_R`, the log is negative, which would put the particle on a trailing arm backwards. So we set `Math.max(r, INNER_R)`.

**Disk thickness:**

We set `THICK = 0.3` meaning 1-sigma of 0.3 units? That's extremely thin. At a scale of 100 units, 0.3 is very thin. That's good for a disk. But the vertical gravity from the logarithmic potential will cause the disk to oscillate; since we have no vertical velocity, it's a cold disk. It will remain thin.

However, there's a risk that the disk particles at large radius have a vertical restoring force that causes them to settle? Actually, if they are in the plane with no vertical velocity, it's a perfectly flat disk. The collision will add vertical velocities and warp the disk, which is beautiful.

**Potential issue with the galaxy centers being point masses:**

The disk particles are test particles (they don't attract each other). This means the disk has no self-gravity. The arms we generate are real material, but they will wind up due to differential rotation. That's fine; the animation will show the arms winding and potentially dissolving, which is realistic.

**Adding a dark matter halo?**

The logarithmic potential essentially represents a dark matter halo. The disk particles move in this potential, which is stable.

**Testing the generator:**

Let's simulate the generation in my head:
- For a particle at r=50, thetaArm = Math.log(10)/0.3 ≈ 7.67 rad. That's in radians. Two arms: arm phases at 0 and π. So the particle has theta = 7.67 + armIdx*π + noise. Both arms are continuous logarithmic spirals.
- Because the exponential distribution has many particles at small r, the inner arms will be bright. The outer colors will be blue.

**Potential improvement: Reassign particles to each galaxy's random velocity formula**

The rotation curve uses `V0*r/sqrt(r^2+SOFT^2)`. So for r=100, v=18*100/sqrt(10000+36) ≈ 17.97. So the outer disk rotates at ~18 units/s. The orbital period at r=100 is 2π*100/18≈35s. With simSpeed=5, the orbit in animation is 7s. Good.

**Center trajectory:**

Initial centers at ±120 with velocities ∓20 z. They are bound? At r=240, the acceleration is `-2*V0^2 * d / (d^2+SOFT^2)`. For d=240, acceleration ≈ -2*324*240/(57600+36) = -155520/57636 ≈ -2.7 units/s^2. The center of mass is at 0. The relative motion under the softened force has a effective potential. The initial kinetic energy (reduced mass * v_rel^2/2) = (0.5*m * (40)^2)/? Actually, relative velocity is 40 units/s. The potential at d=240: `V0^2 * ln(d^2+SOFT^2)` times -1? The total energy for the relative motion: E = 0.5 * (v_rel)^2 + potential. The potential for this force is `Phi(d) = 2*V0^2 * 0.5 * ln(d^2+SOFT^2)`? Let's derive: acceleration = -2*V0^2 * d/(d^2+a^2) (relative). This is the gradient of `Phi = V0^2 * ln(d^2+a^2)`. Since `F = -dPhi/dd = -2*V0^2 * d/(d^2+a^2)`. Yes. At d=240, Phi ≈ V0^2 * ln(57636) ≈ 324 * 10.96 = 3551. At d=20, Phi ≈ 324 * ln(436) ≈ 324*6.08=1970. Since E = 0.5 * v_rel^2 + Phi must be conserved. Initially, v_rel=40, so E=800+3551=4351. At d=20, if all the energy is in potential, v_rel=0? But 4351 > 1970, so at d=20 the speed is sqrt(2*(4351-1970)) = sqrt(4762)=69 units/s. So the centers will approach each other at ~69 units/s at close approach. That's fast, but they'll pass through each other (since softened) and swing around. It may be a slingshot. Actually, the total energy E>0? 4351>0 means the relative motion is unbound! Indeed, because the potential is logarithmic, it rises slowly, and the initial kinetic energy is large. The two galaxies will fly past each other and eventually separate (since E>0). Over the animation, they'll have one close passage.

Wait, with `v0^2 * ln(d^2)`, the potential is unbounded above, so if E>0, the system is unbound. That means the collision is a flyby, not a merger. That's okay for the visualization; the tidal tails will be created. But after the flyby, they separate again, which might look like a "collision". The request didn't specify a merger; just "collision" perhaps. Actually, in real galaxy clusters, flybys occur. It might be more dramatic if they merge, but for a flyby, the disk structures will be disturbed and then recede, which can look awesome.

If we want a bound collision (merger), we need the relative kinetic energy to be negative enough. With `v_rel` of 40 at d=240, and the potential is positive (since `ln` large), so yes E>0. To make it bound, we'd need `v_rel` slower. For a bound orbit, E<0. Since potential is always positive (for d>1), E = T + Phi must be < Phi_max. At large d, Phi → ∞, so any finite can be bound if T is small. Actually, wait, `ln(d^2)` goes to infinity as d→∞, so for a given E, the system is bound because T>=0, but at some large d, Phi > E, so the turning point is at a finite d. So E can be positive but still bound if the potential well deepens? In a logarithmic potential, the potential goes to infinity, so all orbits are bound as long as E is finite, because as d increases, Phi → ∞, so eventually T = E - Phi becomes negative, which is impossible; the particle turns around. So any finite energy is bound in this potential! Interesting. Because the force falls as 1/d, the potential rises logarithmically, so a particle with sufficiently large energy will go out to large distance, but will come back because the potential grows without bound. So the two galaxies are gravitationally bound regardless of speed (as long as E < ∞). They may go out to large separation, but they will come back. In our simulation, we can let them recede.

Actually, because the sum of two such potentials grows like `2*v0^2 * ln(R)` at large R, indeed any test particle is bound. But the finite simulation time means they will separate and maybe not visibly return. To create a nice visualization, we can give them less initial velocity, so they come close and swing around, maybe again. That's okay.

Let's set initial velocity magnitude lower: e.g., ±10 instead of ±20. Then they'll come in more gently, possibly merging or repeatedly interacting.

We can tune by setting `centerVel = (0, 0, -15)` for gal1. This is the tangential velocity (relative to the line of centers? Actually, the centers are separated along x, velocities along z are perpendicular). So it's a tangential orbit (like a galaxy encounter). That gives an eccentric orbit. v=15 at d=240. The relative velocity is 30. The escape speed from the potential well at d=240? The potential at d=240 relative to d→∞ is infinite, so no escape. But the speed required for a particular separation? Let's not over-decide; we'll set their initial speeds to about 1/3 of the observed relative speeds at that separation? We can just use v=12; at d=240, the acceleration is about 2.7, so the time to fall a distance of 120 is sqrt(2*120/2.7) ≈ 9.4s. They will swing by in about 10s. That seems good.

Let's set gal1.vel = (0,0,-12), gal2.vel = (0,0,12). This gives a relative speed of 24, which at d=240 is significant. The closest approach will be determined by the angular momentum. They might pass by and create tidal tails from the gravitational impulse.

I think this will work.

**Brightness/point size:**

For 20k points per galaxy, the core will be dense. Point size 2.5 pixels is fine. If the label should be readable, etc.

**Potential z-fighting with additive blending:**

Additive blending with `depthWrite: false` means sorting is not critical, but you can sometimes see pixels in the background. We should render stars first? Actually, additive blending works in any order if the background is black. The color buffer accumulates.

**Three.js PointsMaterial + vertex colors:**

If we set `vertexColors: true`, in Three.js you use `color` attribute. So we need:
```
geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
```
The material will multiply the `map` texture by the vertex color.

**The `simSpeed` and substeps:**

We want the animation to be fast enough. Let's set `simSpeed = 5`. Substeps = 3 for accuracy. At 60fps, that's 180 integrations per second, times 80k force? Actually substeps=3, each substep does 1 center update + 40k particle updates. 40k*3=120k per frame, fine.

But with `simSpeed = 5`, the simulation runs 5x faster than real-time? Actually, the time step for physics is `h = dt * simSpeed / substeps = dt`. Wait, yes because dt * simSpeed / substeps = dt * 5 / 3. At 60fps, dt=1/60, h=0.0167*5/3=0.0278s. That's the physics time step. The simulation speed is 5x, meaning one real second represents 5 seconds of simulation time. But since our velocities are in code units per real (simulation) second, multiplying the time step by 5 effectively makes objects move 5x faster. Good.

We need to ensure the animation looks stable. h=0.028s is fine.

**Particle forces:**

In the integration loop, we'll have nested loops. To optimize, we can avoid doing `new THREE.Vector3` in the loop. Use raw numbers.

**Potential issue with using SHARED center positions during integration:**

For particles, we compute forces from the current centers. That's fine. We update centers and particles in the same step.

**Order of updates:**

We'll do:
1. Integrate centers (update velocities, then positions).
2. Integrate particles (update velocities, then positions).

This is symplectic for the whole system? Since centers and particles are coupled (the centers feel no force from particles), the particle integration sees the updated center positions, which is okay.

But if we update centers first, the particles see the new center positions, which might introduce a tiny error vs. updating centers after. Not important.

**Rendering the background:**

The background stars should not be affected by the camera near clipping. Our camera near 0.1, far 5000, good.

**Creating the Points object:**

```
const points = new THREE.Points(geometry, material);
scene.add(points);
```

**Three.js coordinate system:**

Y is up. The disk is in the XZ plane, so the galaxy is horizontal. The camera starts at angle 0 (x=280) and orbits; we'll see the disk edge-on at t=0? Actually, if the camera is at (280,120,0) looking at origin, the XZ plane is the galaxy plane. The camera is at height 120, radius 280, so the disk appears inclined. As the angle changes, we'll get face-on and edge-on views. Good.

**Background star positions:**

We want them to not look like a flat cube. Use spherical distribution.

**Performance improvements:**

The `createSprite` function creates a new canvas for the star and for map. We can reuse the same texture for both points and background. The texture can be shared.

**Adding a subtle bloom?**

Not necessary. Additive blending gives a glow.

**Testing the force calculation:**

Let's double-check the acceleration formula. For a single galaxy potential `Phi = 0.5 * V0^2 * ln(r^2 + a^2)`? Actually, if `F = -V0^2 * r / (r^2 + a^2)`, then `Phi = 0.5 * V0^2 * ln(r^2 + a^2)`. The acceleration is `-dVPhi/dr = -V0^2 * r / (r^2 + a^2)`. Yes, so for the relative motion of two centers, the potential energy between them is `2 * Phi`? Actually, the center of mass feels no force in a two-body interaction; the equation of relative motion uses acceleration = `-2*V0^2 * r_rel / (r_rel^2 + a^2)`. That's what we used.

For particles in the combined field of both galaxies, we simply sum the two accelerations `-V0^2 * r / (r^2+a^2)` from each galaxy. That's what the code does.

**Potential subtlety:**

When the two galaxies are separated, a particle near galaxy 1 also feels the pull from galaxy 2, which will distort the disk. That's the tidal force we want.

**Limiting the time step:**

We should cap `dt` to prevent large leaps if the tab is in background.

**Debugging the colors:**

We need to set `colors` array before creating geometry. Let's assign colors in the generation function after we get radius.

**Will the disk be stable?**

Since the disk particles are collisionless (no self-gravity) and move in the smooth potential, they will shear and form structures. The initial spiral pattern will wind up. We might not see the spiral arms after a while because differential rotation will wind them up. But over the few revolutions of the animation, they'll shear. This is okay.

**Code structure:**

I'll write the complete code in the response.

One more thing: the background stars should be fairly small, maybe size 1.5, no attenuation. But `sizeAttenuation: false` means they are in pixel units. That might look like bright dots. Good.

**Handling the TIME label:**

We need to create the label element in HTML. I'll include it in the HTML.

**Resizable renderer:**

Add the event listener.

**Putting it together:**

Here's the plan:

1. HTML/CSS for the label.
2. JS code:
   - import * as THREE from 'three';
   - init scene, camera, renderer.
   - create textures.
   - generate two galaxies' particles into arrays.
   - create background stars.
   - set up physics state (gal1, gal2, positions, velocities, colors arrays).
   - animation loop:
     - compute dt, clamp.
     - update simulation time for label.
     - perform substeps.
     - write positions back to geometry.
     - update camera orbit.
     - renderer.render.

I'll make sure to use `let` and `const` appropriately.

Let's write the code carefully.