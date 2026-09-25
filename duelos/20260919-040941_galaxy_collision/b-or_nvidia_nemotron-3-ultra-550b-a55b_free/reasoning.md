The user wants a cinematic scientific visualization of two spiral galaxies colliding using three.js. This is a complex simulation that needs to run smoothly with 40,000+ particles. Let me break down the requirements:

1. Two disk galaxies with visible spiral arms and bright cores
2. At least 20,000 stars each (40,000+ total) as glowing points with additive blending
3. Colors: warm yellow cores to blue-white arms
4. Galaxies approach and interact through gravity - tidal tails and bridges
5. Slowly orbiting camera
6. Dark starfield background
7. On-screen label with simulated time in millions of years
8. Use requestAnimationFrame timestamp for animation time
9. Physics on GPU or cheap approximation for smooth performance
10. Full-window canvas with resize handling
11. Starts automatically, no interaction needed
12. Single self-contained HTML file with inline CSS/JS

Key challenges:
- 40,000+ particles with gravity simulation needs to be fast
- GPU simulation via compute shaders would be ideal but complex in three.js
- Cheap approximation: use analytical orbital mechanics + tidal forces
- Additive blending for glowing stars
- Spiral arm structure generation
- Tidal tail formation during encounter

Approach:
1. Generate two galaxies with spiral structure using parametric equations
2. Use a simplified N-body approximation: each star orbits its galaxy center with perturbations from the other galaxy
3. For performance, compute forces on CPU but in a simplified way, or use GPU via transform feedback / compute shader
4. Actually, for 40k particles at 60fps, CPU can work if optimized (40k * 2 force calculations = 80k ops/frame, very doable)
5. Use BufferGeometry with Points and custom shader for additive blending glow
6. Background starfield as static points
7. Camera orbits slowly around the center of mass

Let me design the physics:
- Each galaxy has a center position, velocity, mass
- Stars have position relative to galaxy center, orbital parameters
- Simplified: stars are test particles in combined potential of two Plummer spheres or Miyamoto-Nagai disks
- Even simpler: each star has a base orbital radius and angle, orbits galaxy center, plus tidal acceleration from other galaxy

Actually, for a "cinematic scientific visualization" that looks convincing but runs fast:
- Pre-compute initial spiral positions
- Each frame: update galaxy centers (two-body problem)
- For each star: compute position = galaxy_center + rotated(initial_offset) + tidal_displacement
- Tidal displacement approximated by integrating tidal acceleration

Better approach: Restricted N-body where galaxy centers move analytically (two-body Kepler), and stars are test particles feeling both galaxy potentials. But 40k particles * 2 potentials = 80k force evals/frame, trivial for JS.

Let me use a simplified potential: Plummer sphere for each galaxy (softened point mass)
Potential: Φ = -GM / sqrt(r² + ε²)
Acceleration: a = -GM * r / (r² + ε²)^(3/2)

Galaxy centers: integrate their mutual orbit with leapfrog
Stars: integrate in the frame of their host galaxy? No, better in inertial frame.

Actually, for tidal tails to form naturally, we need stars to respond to the time-varying potential. Simplest: leapfrog integrate all 40k particles in the combined potential of two moving Plummer spheres. 40k * 2 = 80k force calculations per frame. At 60fps, that's 4.8M ops/sec - very fast in JS if typed arrays used.

Let's do it properly:
- 20,000 particles per galaxy
- Each particle has position, velocity (Float32Array)
- Two galaxy centers have position, velocity, mass
- Softening length ε
- Time step dt scaled for visual effect (not real physics time)
- Leapfrog integration (kick-drift-kick)

Initial conditions:
- Galaxy 1 at (-d/2, 0, 0), Galaxy 2 at (d/2, 0, 0)
- Initial velocities for parabolic or elliptical encounter
- Stars distributed in exponential disk with spiral perturbation

Spiral arms: Use logarithmic spiral: r = r0 * exp(b*θ)
Add multiple arms with phase offsets

Colors: Core (r < r_core) = warm yellow (1, 0.9, 0.6)
Arm: blue-white (0.7, 0.8, 1.0)
Transition based on radius and arm phase

Additive blending: Points material with blending: THREE.AdditiveBlending, transparent: true, depthWrite: false
Custom shader for glow effect: size attenuation, color based on attribute

Background starfield: 5000 distant points, static

Camera: orbits around center of mass at distance, slowly rotating

Time label: overlay div, updates with simulation time in Myr

Let me code this efficiently.

Performance considerations:
- Use Float32Array for all particle data
- Single BufferGeometry for each galaxy's stars (or combined)
- Update positions in vertex shader? No, CPU update is fine for 40k
- Actually, GPU compute would be better but three.js compute shader support is limited. CPU with typed arrays is fast enough.

Wait, 40k particles * 3 components * 2 (pos+vel) = 240k floats. Updating each frame:
for i in 0..N-1:
  compute accel from galaxy1 and galaxy2
  vel += accel * dt
  pos += vel * dt

That's ~40k * 20 ops = 800k ops/frame. At 60fps = 48M ops/sec. JS can do ~100M-1B ops/sec. Should be fine.

But we need TWO galaxies' stars. So 40k total particles. Each feels force from two galaxy centers (not from each other - that's the approximation). So 40k * 2 force calcs.

Let me structure:
- Galaxy class: mass, pos, vel, stars (arrays)
- Stars: local to galaxy? No, global coordinates easier for rendering.

Actually, render all stars in one Points object for efficiency? But different colors per galaxy. Can use color attribute.

One Points object with 40k points, each has position, color, size.

Background stars: separate Points, static.

Shaders:
- Vertex: compute size based on distance, pass color
- Fragment: radial gradient for glow, additive blending

Let's write the code.

Spiral generation:
For each galaxy, generate 20k stars:
- Sample radius from exponential distribution: r = -h * ln(1 - u) where h = scale length
- Sample angle θ uniform
- Add spiral perturbation: θ += A * sin(m * θ + φ(r)) for m arms
- Height z from sech² or Gaussian
- Velocity: circular orbit v_circ = sqrt(GM/r) * (1 - softening correction) + random dispersion
- Velocity vector: tangential + small radial + vertical

Galaxy centers initial orbit:
- Separation d = 100 kpc (visual units)
- Mass M = 1e11 solar masses each (in code units)
- G = 1 (code units)
- Relative velocity for parabolic encounter: v = sqrt(2GM/d) at pericenter? Let's set initial conditions for a close pass.

Better: place galaxies at apocenter of elliptical orbit, or start far apart and fall together.

Cinematic: start separated, approach, interact, separate.

Set initial positions: (-200, 0, 0) and (200, 0, 0)
Initial velocities: (0, 0.3, 0.1) and (0, -0.3, -0.1) - giving angular momentum

Time scaling: 1 code time unit = 10 Myr? Display time in Myr.

dt = 0.1 code units per frame? Need to tune for visual speed.

Softening ε = 2 kpc (visual units)

Let's define code units:
- Length: 1 kpc
- Mass: 1e10 solar masses
- G = 4.3009e-6 kpc (km/s)² / M_sun ... better use dimensionless.

Use N-body units: G=1, M=1, R=1 (virial radius). But for visualization, just pick numbers that look good.

Set:
- Galaxy mass = 1000
- G = 1
- Initial separation = 50
- Softening = 2
- dt = 0.05

Stars: 20k each, disk scale radius = 5, scale height = 0.5

Circular velocity at r: v_c = sqrt(GM * r² / (r² + ε²)^(3/2)) for Plummer? Actually for Plummer sphere, mass enclosed M(r) = M * r³ / (r² + ε²)^(3/2)
So v_circ = sqrt(G * M(r) / r) = sqrt(G * M * r² / (r² + ε²)^(3/2))

Add velocity dispersion: 0.1 * v_circ random.

Spiral arms: m=2 arms, pattern speed? For simplicity, static spiral in initial conditions, then let it wind up? Or live spiral? Too complex. Just initial spiral pattern, then stars orbit and shear naturally.

Spiral: θ = θ0 + A * exp(-r/r_sp) * sin(m * θ0 + φ)
Actually, logarithmic spiral: r = r0 * exp(k * θ) => θ = (1/k) * ln(r/r0)
Perturbation: Δθ = A * sin(m * θ + φ)

Let's implement.

Rendering:
- Vertex shader: point size = baseSize * (1.0 / -mvPosition.z) * pixelRatio
- Color from attribute
- Fragment: radial gradient: float d = length(gl_PointCoord - 0.5); alpha = smoothstep(0.5, 0.0, d) * color.a

Background: simple points, smaller, dimmer.

Camera: orbit around (0,0,0) at radius 150, height 50, slow rotation.

Time label: DOM element, fixed position.

Resize: update renderer size, camera aspect.

Now, let's write the complete HTML.

I'll use a single script module, import three and OrbitControls (though we don't need controls, camera is auto). But user mentioned OrbitControls in addons example. We'll just implement custom camera animation.

No external resources. All inline.

Let's code.