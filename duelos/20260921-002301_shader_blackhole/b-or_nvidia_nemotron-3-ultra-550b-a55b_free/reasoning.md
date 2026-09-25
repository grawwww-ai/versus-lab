The user wants a black hole visualization with gravitational lensing, accretion disk, and starfield - all in a single HTML file with raw WebGL2. This is a complex shader project. Let me break down what's needed:

1. **Full-screen quad** with WebGL2
2. **Fragment shader** that does:
   - Ray marching through curved spacetime (Schwarzschild metric)
   - Accretion disk with temperature gradient (hot inner → cool outer)
   - Gravitational lensing (light bending around black hole)
   - Photon ring at 1.5 Schwarzschild radii
   - Event horizon at 1 Schwarzschild radius
   - Starfield background with lensing distortion
   - Camera orbiting and tilting over time
   - Disk rotation

Key physics:
- Schwarzschild metric for ray tracing in curved spacetime
- Geodesic equations for photon paths
- Accretion disk emission based on temperature (blackbody-ish)
- Doppler shift from disk rotation
- Gravitational redshift

Let me design the shader carefully. I'll use a simplified but visually accurate approach:
- Ray march from camera through curved space
- Use effective potential for photon orbits
- Analytical approximations for light bending where possible
- For the disk: use Novikov-Thorne temperature profile T ∝ r^(-3/4)
- Color mapping: inner=white/orange, outer=red
- Photon ring at r=3M (1.5 Rs)
- Event horizon at r=2M

Camera motion:
- Slow orbit around black hole
- Slow tilt oscillation
- Distance ~10-15 Rs for good view

Starfield: procedural noise-based stars, lensed by same gravity

Let me write the complete implementation.