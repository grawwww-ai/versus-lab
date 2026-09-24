Create a single HTML file: implement value noise / simplex noise ourselves, layer multiple octaves, flow field, particles with trails (fade canvas via semi-transparent black fill or alpha compositing), additive blending via 'lighter' globalCompositeOperation, time-varying palette (hue drift), occasional "reset wave" — a radial wave that pushes particles outward and clears trails.

Use the timestamp of rAF. Resize handler.

Implementation: simple 3D or 2D value noise with smooth interpolation (fbm). Implement 3D value noise (x, y, time) with a permutation-like hash. Layer 3–4 octaves.

Particles: about 4000. Each has a position, previous position, and a color index within the palette. Draw a line from prev to pos with hsl color, composite is 'lighter'.

Trail fade: each frame, fill with rgba(dark) with low alpha, using composite 'source-over'. But since the palette is colorful, fading to black is fine.

Reset wave: every ~8–15 seconds, spawn a wave: a circle that expands from a random center; particles near the wave front get a slight push; also, temporarily increase the fade alpha to erase trails. Keep it gentle.

Palette: pick a base hue that drifts slowly with time, plus an offset; color = hsl(base + offset + noise, sat, light).

Handle DPR: just set canvas width = innerWidth etc., and reinitialize on resize.

Write the code.
