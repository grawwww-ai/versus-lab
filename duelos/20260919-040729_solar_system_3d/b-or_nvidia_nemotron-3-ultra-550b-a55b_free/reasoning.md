We are building a self-contained HTML file with Three.js (r186) as ES module.
 Requirements:
 - Solar System with Sun (glowing, emissive, halo), 8 planets in correct order with relative sizes.
 - Procedural textures on canvas for planets (Jupiter bands, Earth oceans/continents, Mars red, etc.)
 - Saturn with rings.
 - Moon orbiting Earth.
 - Faint orbit lines.
 - Planets orbiting at different speeds.
 - Starfield background.
 - Camera travels from planet to planet, showing each close up with name on screen.
 - Use requestAnimationFrame timestamp for animation time.
 - Full-window canvas, handle resizing.
 - Starts automatically, no interaction needed.

 We'll use three.js and maybe OrbitControls for the tour? But the camera is scripted, so we might not need OrbitControls.
 However, we can use it for initial setup but then disable it during the tour.

 Steps:
 1. Set up scene, camera, renderer.
 2. Create starfield (points or a large sphere with stars texture). We'll create a starfield using points for performance.
 3. Create Sun: sphere with emissive material, and a halo (maybe a sprite or a larger transparent sphere with additive blending).
 4. Create planets: array of planet data (name, distance from sun, size, orbital period, rotation period, texture generator function).
 5. For each planet, create a mesh with procedural texture (using canvas). Also create orbit line (a ring geometry).
 6. For Earth, add Moon.
 7. For Saturn, add rings.
 8. Animation loop: update planet positions based on time, rotate planets, move camera along a predefined tour path.
 9. Camera tour: define a sequence of camera positions and targets for each planet, with duration. Use interpolation.
 10. Display planet name on screen during close-up.
 11. Handle window resize.

 Let's design the tour:
 - Start at Sun, then go to Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, Neptune, then back to Sun or overview.
 - For each planet, camera moves to a position near the planet, looks at it, stays for a few seconds, then moves to next.

 We'll use a timeline approach: each tour step has a start time and end time. We'll use the global time (from requestAnimationFrame) to determine where we are.

 However, the requirement says "camera that travels from planet to planet showing each one close up with its name on screen". So we need a cinematic camera path.

 We can create a spline path for the camera to follow, but simpler: define keyframes (position, target, time) and interpolate between them.

 Let's define keyframes for each planet:
 - Start at a global view (maybe above the solar system).
 - Then for each planet: move to a position offset from the planet (e.g., 2-3 planet radii away), look at planet, hold for 3 seconds.
 - Transition to next planet: move camera over a few seconds.

 We'll use a global clock (time in seconds) and a tour schedule.

 Implementation details:
 - Planet data: we'll use relative sizes and distances (not to scale, but visually pleasing).
 - Orbital periods: we'll use relative speeds (e.g., Mercury orbits faster than Neptune). We can use real ratios but scaled so that the tour doesn't take too long.

 Since the tour is scripted, the planet positions will be updated in real-time, but the camera moves independently.

 We'll create a function to generate procedural textures for each planet.

 Let's code step by step.

 Note: We must use import map provided? The problem says "An import map is provided for you: do not add your own import map or any CDN URL." But we are writing a single HTML file. We'll assume we can use the standard import from 'three' and addons because the environment has an import map. We'll just write the imports as usual.

 Let's write the HTML structure.

 We'll put CSS inline, JS inline in a module script.

 We'll use three.js r186.

 Let's start.