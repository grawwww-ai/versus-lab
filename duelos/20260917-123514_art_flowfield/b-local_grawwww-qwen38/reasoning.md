Create a single HTML file: flow field using a self-made value noise (e.g., 3D value noise, or a simple fBm), thousands of particles, trails via a semi-transparent black overlay, additive compositing (globalCompositeOperation 'lighter'), a palette that shifts over time, and a periodic "reset wave" that fades the canvas / resets particles. Resize handling.

Let's write clean code:

- Canvas is full-screen, with DPR handling (possibly clamped at 1 for performance; using dpr might be better, but with thousands of particles + trails, 1 is sufficient).
- Noise: 3D value noise using a hash + smoothstep, 3–4 octave fBm, time as the third dimension.
- Particles: around 6000–9000 depending on the area. Each has pos, prev, life, hue index, speed.
- Drawing: fade the canvas with a dark rectangle using 'source-over' (e.g., rgba(bg, 0.045)), then set 'lighter' and draw line segments with strokeStyle color from the palette, alpha ~0.35, lineWidth ~1.
- Palette: an array of base hues; slowly rotate with an offset over time; color = hsl.
- Reset wave: every ~12–20 seconds, a radial wave from a random center: particles inside the wave radius get respawned with a small chance, and a slight additional fade is applied; more simply: draw a soft ring? "A gentle reset wave so the image continues to evolve": periodically pick a center, animate an expanding radius over ~3 seconds, and particles inside the wave band are probabilistically reset, plus a light global fade.

Implementation: wave = {x, y, r, active}. r grows; the band is r..r+width; if a particle is inside the band, 4% chance of respawn. When r > max, the wave is inactive; the next one is scheduled.

Resize: set canvas size, and to avoid a hard clear, copy the old content? On resize, just clear and let it re-render; or use an offscreen to preserve? More simply: drawImage the old canvas onto the new one.

Performance: use ctx.beginPath per particle — 8k strokes per frame might be heavy but generally fine. Batch by color? Since the palette has gradients, per-particle color is fine; 6–7k lines per frame at lineWidth 1, no problem.

Trail fade: fillRect with rgba(5,8,16,0.05).

Palette: define a set of hues, e.g., [200, 320, 45, 260, 170] — shift over time: hue = base + time*small value + noise. Color from a small fixed set with slight variation; use hsla.

Time: t = timestamp * 0.001.

Noise implementation: hash function for integer lattice, 3D value noise, quintic smoothstep interpolation. fBm with 3 octaves.

Particle update: angle = noise(x*sc, y*sc, t*ts) * PI * something (e.g., *2.2); vx=cos, vy=sin; speed varies slightly. Life countdown; respawn at random position on life<0 or off-screen.

Also, draw a faint dot at the starting position? Not needed.

Add a slight per-particle speed variance.

Let's write the file.
