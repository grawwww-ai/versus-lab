Let me think carefully about what makes a truly mesmerizing generative flow-field piece, because this is a genre where mediocrity is common and excellence is rare.

**Core mechanics:**
1. **Value noise implemented from scratch.** I'll build a proper gradient/value noise: a hash-based permutation table, 2D value noise with smoothstep interpolation, then **fBm (fractional Brownian motion)** layering several octaves. To make the field *evolve*, I'll use 3D noise — noise(x, y, t) — by extending the value noise with a third dimension (trilinear interpolation over hashed lattice). That gives a coherent, time-morphing flow field. Alternatively, I could domain-warp: sample noise, offset coordinates by another noise sample — domain warping produces dramatically more intricate, organic curling structures than plain fBm. I'll do fBm + one level of domain warping. That's the difference between "blobby smoke" and "intricate calligraphy".

2. **Angle field:** angle = fBm-warped noise * some multiple of 2π (e.g., 2π * 2.5 or with a twist term). Using angle = noise * π * 4 gives curling vortices. Even better: compute the field from a **curl** of a scalar potential — curl noise gives divergence-free flow so particles stream along contours beautifully and don't pile up. Curl of a scalar field ψ: vx = ∂ψ/∂y, vy = -∂ψ/∂x. I can approximate derivatives with finite differences of the warped fBm. Curl noise is more expensive (4 noise evals per particle per frame vs 1) but with a few thousand particles at reduced precision it's fine. Actually, let me think about performance.

**Performance budget:** thousands of particles (say 3000–6000 depending on device), each needing 1–4 noise evaluations per frame with ~4–5 octaves each. A 5-octave 3D value noise call is maybe 8 hash lookups × 5 octaves = 40 hash+lerp ops. ×4 for curl finite differences = 160. ×4000 particles = 640k noise units per frame. In JS that might be ~10–20ms. Risky. Options:

- Precompute the flow field into a coarse grid (e.g., cell size 8–12 px) each frame or every few frames, then particles just bilinearly sample the grid. That's the classic approach and it's fast: grid of, say, 240×135 cells ≈ 32k cells; computing curl there (4 fbm evals each = 128k fbm evals... too much every frame).

Hmm. Let me reconsider. Grid approach with direct angle (not curl): compute angle per cell via 1 warped fbm eval per cell. Grid 200×120 = 24k cells × fbm(4 octaves, 3D) — each octave needs trilinear interp of 8 hashed corners. That's 24k × 4 octaves ≈ 100k noise corner-hashes per recompute. If I recompute every 2–3 frames or interpolate between two grids, it's cheap. Actually even every frame it's probably fine (~2–4ms). But recomputing every frame at 60fps × 24k cells... let me estimate: a trilinear value-noise octave = 8 hash calls + 7 lerps. Hash = bit-mixing, cheap. Say 50ns per octave in optimized JS. 24k × 4 = 96k octaves ≈ 5ms. Hmm, borderline.

Better: **use 2D noise with time as animated offsets** — i.e., noise2(x*scale + t*driftX, y*scale + t*driftY)? That loses the "evolving in place" quality; the field would translate rather than morph. A compromise: 3D noise but recompute the grid at a lower cadence (every 3rd frame) and lerp between previous and current grid for smoothness. Or just recompute every frame with fewer octaves (3 octaves) and moderate grid resolution. Honestly, 3 octaves with time-morphing is plenty after domain warp.

Actually, let me simplify smartly: **curl from a precomputed potential grid.** Compute scalar ψ on a grid that is *one cell larger* than the angle grid (or compute ψ with wrap), then take finite differences — that's essentially free once ψ is computed. So per frame: compute ψ grid (W+1)×(H+1) of warped-fBm values, then derive vx, vy by central differences. Grid 192×112 ≈ 21.5k ψ evals, each = domain warp (2 fbm evals at 2 octaves? or cheaper warp) + 3-octave fbm. Hmm, warp itself costs.

Let me tune: warp with a *single-octave* noise per axis sampled at a coarser frequency — 2 evals × 1 octave. Main ψ = 3 octaves. Total per cell ≈ 5 octaves ≈ 40 corner hashes. ×21.5k cells ≈ 860k hash+lerp ops per frame. At ~5ns each in JIT-friendly code... maybe 4–8ms. Still risky on slow machines.

Alternative cadence: recompute field every 2 frames (field evolves slowly anyway — time-based noise changes slowly). Particles move sub-pixel per frame mostly. Recomputing every 2–3 frames is visually indistinguishable. I'll recompute the field grid every 3rd frame, and additionally nudge particle angles by time-varying rotation? No — just keep it simple: recompute every 2 frames. With 60fps that's field at 30Hz, perfectly smooth for slow drift.

Actually — even better idea for smoothness and speed: recompute half the grid rows each frame (interleaved)? Overcomplicated. Every-2-frames is fine, or I can scale particle count/grid to device. Let me also adapt: on small/slow devices, fewer particles.

Actually, let me reconsider direct per-particle noise eval, skipping the grid. 3500 particles × 4 evals (curl finite diff needs ψ at (x±e, y) and (x, y±e) — 4 evals) = 14k evals × 5 octaves = 70k octave-evals... wait that's way *less* than the grid approach? No wait: 3500 particles vs 21.5k grid cells — the grid is denser than the particle set if particles number only 3500. Hmm, but grid gives uniform coverage; per-particle adapts to particle count. Per-particle: 3500 × 4 ψ evals × ~40 hash ops = 560k ops/frame ≈ 3–6ms. Comparable. But the grid lets me do neat extras (spawn hints, background painting by field magnitude) and avoids recomputing duplicate samples when particles cluster. Also bilinear sampling of a grid is very cache-friendly.

Decision: **precompute a vector grid every N frames (N=2), bilinear-sample per particle.** Grid cell ~ 10px. Cap grid dims for huge screens (e.g., max 260×160) by increasing cell size.

Wait, actually there's an even cheaper curl trick: compute ψ grid once per refresh, vx = (ψ[y][x+1]-ψ[y][x-1]), etc. — needs ψ at ±1 cell around the sampled region, so compute ψ on grid+2 margin. Fine.

Should I use curl (divergence-free) or direct angle? Curl noise gives that gorgeous laminar flow where particles trace along level sets, creating topographic-map intricacy. Direct angle fields create streaming currents with convergence lines (particles bunch up along certain curves — can be nice too but causes clumping and saturation spots). I'll go with **curl of a domain-warped fBm potential**. That's the signature quality move. Plus I'll add a slow global swirl/rotation term that varies over time to keep motion from looking static, and a slight bias drift.

Hmm wait — pure curl flow means particles wander forever without sinks; trails will etch along equipotential-ish contours, and as the field morphs, new contours get drawn over old. That's exactly the "intricate layered etching" look I want (like Angie Ferrero / "flow fields" fine art plots). 

**Trails / rendering:**
- Canvas 2D with `globalCompositeOperation = 'lighter'` (additive) for particle dots → glow build-up.
- Fade layer: each frame draw a translucent dark rect over everything (`source-over`, fillStyle rgba(bg, alpha≈0.02–0.04)) so trails persist but decay. For richer color trails that don't just gray out, I could use `destination-out` fade (alpha fade keeping hue) — actually `destination-out` with low alpha subtracts alpha, letting the page background (black) show through; it preserves saturation better than painting semi-opaque black (which desaturates toward the bg color). Painting translucent black desaturates toward black which is fine on black bg, but the classic trick for vivid long-exposure trails: fade with `globalCompositeOperation='destination-out'` fillStyle 'rgba(0,0,0,0.03)' — this reduces alpha, and since canvas composite onto page... if the canvas itself is the bottom layer over body bg = black, reducing alpha shows black through — equivalent visually but mathematically keeps hue/chroma of remaining pixels. I'll use destination-out fade. But note: destination-out on a canvas that accumulates 'lighter' additive colors — additive can push channels above 255? No, canvas clamps at 255 per channel. Additive 'lighter' adds and clamps; fine.

One caveat with destination-out: low alpha values can leave permanent ghost residue because alpha decrement of 1–3/255 rounds to zero for some values (the infamous "trail ghosting" due to 8-bit quantization). At alpha 0.03 → 7.65/255, quantization still decrements, mostly OK; but values that land such that alpha*(remaining) rounds down to same value cause stuck pixels leaving faint etches. Mitigation: every few seconds do a slightly stronger fade, or use fade alpha with slight dithering, or periodically (the "reset waves"!) wipe more decisively. The **reset waves** actually solve this elegantly: periodically a radial wave sweeps outward from a random point; behind the wavefront, the canvas is wiped (or heavily faded) and particles get respawned/re-energized. So saturation is bounded and ghost residue gets cleaned. 

**Reset wave design:** a circular front expanding from a random (or center-biased) origin at speed v px/s. As the front passes a pixel region... easy implementation for particles: when a particle's distance from wave origin crosses inside the front radius (dist < radius and previously ≥, or simply dist < radius + smallband and not yet reset for this wave), respawn it at a fresh random position (maybe biased to near the front, like just behind it — "reborn in the wake") and give it a bright flash. For the canvas: when the wavefront passes over a region, we can't easily erase an annulus on canvas cheaply... actually we can: draw with `destination-out` a ring stroke (arc with big lineWidth = band) with soft alpha, or draw a filled circle with very low alpha repeatedly... Simpler: as the wave radius grows, each frame draw an arc ring (stroke with lineWidth ~ 40–90, soft color? no—) using destination-out with alpha ~0.25 so it carves a fading band, plus optionally a *visible* subtle luminous ring drawn with 'lighter' at very low alpha so the wave is faintly perceptible as an event. Hmm, a visible ring might read as cheap ornament. Better: make the wave legible through its *effect*: behind the front, colors reset to the new palette phase, so you see a traveling boundary where old composition dissolves and fresh filaments start drawing. That's genuinely mesmerizing. I'll add a *very* faint brighter shimmer band of particles being reborn — the reborn particles get a brief brightness boost, so the wake visibly sparkles alive. That's the perceptible signature moment without decorative gimmicks.

Also to prevent long-run saturation between waves: continuous gentle fade handles it. And palette shifting means post-wave regions draw in new hues → visible color evolution front. 

Wave timing: every ~9–14 seconds, occasionally maybe double-wave. Within the first 30 seconds (the recording window) I want at least one wave so the recorded clip shows the full cycle: start fresh at t=0 (canvas black), build up beautifully by ~8–12s, first reset wave ~13–16s, rebuild with shifted palette through 30s. Also palette should visibly shift within 30s — make the hue drift noticeable: full palette rotation period ~ 60–90s so in 30s hues shift by ~120–180°... maybe gentler: base hue drifts ~90–120° over 30s. Also give particles a *slow* lifetime (or not — curl flow keeps them wandering; I'll add soft speed variation and occasional respawn to keep distribution uniform).

**Palette:** curated, not rainbow HSL. I'll define 4–5 anchor palettes (e.g., deep teal→gold→coral; magenta→amber→cream "ember"; cyan→violet? careful with blue/purple cliché...). The instruction says palette slowly shifts over time. Curated approach: define palettes as arrays of hand-picked colors, and interpolate the *active palette* between two curated sets over time (crossfade weights), plus slow hue rotation on top? Crossfading between curated palettes gives evolving but always-tasteful color. Particle color = sample along palette gradient by (a) particle's personal parameter + (b) noise(field potential at position) so color maps to structure — that ties color to flow, making coherent colored filaments instead of confetti. Yes: color index = ψ (the potential) normalized → position along palette ramp. Since ψ is coherent spatially, whole contour bands share hue → gorgeous layered color topology that morphs. Plus per-particle jitter.

Curated palettes (hand-picked hex, avoiding default blue/purple genericism; going for rich, gallery-grade combos):
1. **"Ember"**: #ff3d00 → #ff9e00 → #ffd449 → #fff3d6 (deep orange to warm cream) with a touch of crimson #d00000.
2. **"Verdigris/Teal-gold"**: #004d40-ish deep teal #01579b? that's blue... Let me pick: #00695c, #26a69a? hmm those are material-ish. Let me hand pick: deep pine #0b3d2e, jade #1f8a70, mint-celadon #9ee7c9, gold #f4c95d, cream #fdf0d5. 
3. **"Magenta-ember"**: #2b0a3d? purple-ish — avoid leaning purple. Maybe **"Coral/ink"**: #1a1423 ink, #e63946 coral red, #ff758f rose, #ffcdb2 peach.
4. **"Aurora"**: deep green #013220, spring #38b000, lime-yellow #c5f9b5? plus cyan #7fd8d8.

Crossfade pairs cycle: ember → verdigris → coral → aurora → ember... Each phase lasts ~20–25s with smooth blending. Additive blending on black will make overlaps go white-ish where dense — need to keep per-stroke alpha low (like 0.05–0.15) so buildup is gradual.

Background: not pure black — very deep warm-black #060608 or #050507, maybe extremely subtle vignette? A radial vignette would require redrawing... skip; the fade naturally keeps edges whatever. Actually I can make the initial fill and fade color a hair off-black; fine.

**Particle rendering:** short line segments from previous position to current (gives streaks, more calligraphic than dots) with lineWidth ~1 (maybe 0.6–1.4 varied), strokeStyle from palette with low alpha. Drawing thousands of individual strokes per frame with per-stroke color changes is expensive (state changes). Optimization: batch by color bucket — quantize palette to, say, 24 color buckets; per frame, group segment indices by bucket, set strokeStyle once per bucket, draw all segments in one path (moveTo/lineTo pairs) then one stroke() call. That's a huge perf win. With `lighter` composite and alpha in the strokeStyle. Path batching with hundreds of subpaths per stroke call is fine.

Alternatively draw dots via fillRect 1×1 or 2×2 batched — lines look better. I'll do bucketed line segments. Buckets: compute color = paletteRamp(t) → precompute per-frame an array of bucket colors as rgba strings (alpha varies with particle "energy"? keep alpha per bucket constant, encode energy into bucket choice or skip). Simpler: alpha fixed ~0.14 (tuned), width fixed 1. Add subtle per-particle brightness variation by assigning particles to sub-buckets... keep simple: bucket by color only, alpha constant. Reborn "flash" particles: draw their segment bigger/brighter — separate small bucket pass with alpha 0.5 and lineWidth 1.8 for the first ~0.6s of life. That gives the wake sparkle.

**Motion model:**
- pos += vel * dt where vel = field(p) * speed + slight curl-noise jitter? Field already smooth. Add per-particle speed multiplier (0.5–1.5) and tiny random walk for texture.
- dt from rAF timestamp, clamped (max 33ms) to avoid jumps after tab switches.
- Respawn if out of bounds (wrap? wrap creates seam lines — actually wrap is fine and keeps density; but wrapped segment would draw across screen — handle by drawing only if not wrapping, i.e., if jump > threshold, skip drawing that segment). I'll wrap with seam detection.
- Max lifetime randomized (e.g., 6–20s) then respawn — keeps things fresh.
- Speed scale so that typical velocity ~ 20–60 px/s — slow enough for fine etching, fast enough to feel alive. Let me target ~30–70 px/s. Actually for mesmerizing slow build, ~25–60 px/s with variance; some "fast lane" particles (10%) at 2–3× for energy streaks.

**Noise implementation details:**
```js
// integer hash → [0,1)
function hash(ix, iy, iz) { ... }
```
I'll implement a solid 3D value noise:
```js
const P = new Uint8Array(512); // permutation
// fill with seeded shuffle
function n3(x, y, z) {
  // lattice
  const X = Math.floor(x), Y = Math.floor(y), Z = Math.floor(z);
  const fx = x - X, fy = y - Y, fz = z - Z;
  // smoothstep fade
  const u = fade(fx), v = fade(fy), w = fade(fz);
  // hash 8 corners via permutation table: h(P[P[P[Xi]+Yi]+Zi]) / 255
  ...
  // trilinear interp
}
```
Permutation-table value noise is fast. fade = quintic or cubic (cubic is fine for visuals; quintic smoother — use quintic u*u*u*(u*(u*6-15)+10), slightly costlier but better; cubic ok honestly, but quintic avoids grid artifacts at this scale... at cell ~10px octaves, cubic artifacts could show as slight diamond patterns. I'll use quintic).

fbm(x,y,z, octaves): sum amp * n3(x*freq, y*freq, z*freq+seedOffset), lacunarity 2, gain 0.5, normalize by amp sum → [-1,1] range roughly (value noise returns [0,1]; remap to [-1,1] per octave).

Domain warp: 
```
q = vec2(fbm(x+off1, y+off1, t1), fbm(x+off2, y+off2, t2))  // 1 octave each? or 2
psi = fbm3(x + warpAmp*q.x, y + warpAmp*q.y, t*speedZ)
```
Inigo Quilez style with 2–3 warp iterations produces insane intricacy but costs more. One warp iteration with 2-octave warp fields is a good middle. Warp amplitude in noise-space units ~1.0–2.0.

Time evolution: z = t * 0.06 (noise units/sec) for the potential; warp fields evolve at slightly different rates. Also slowly rotate the sampling frame? A slow rotation of sample coordinates adds a swirl. Optional.

Field refresh: every 2 frames compute ψ grid: dims GW×GH where cell = max(9, ceil(min(w,h)/... )) — simpler: cellSize chosen so GW = ceil(w/cell) ≤ 200 and GH ≤ 130; cell = max(8, w/200, h/130)? Let's just: cell = Math.max(8, Math.ceil(Math.max(w/220, h/140)))? For 1920×1080: w/220=8.7→9; h/140=7.7; cell=9 → GW=214, GH=121 ≈ 25.9k cells. Each ψ eval: 2 warp fbm (2 oct) + ψ fbm (3 oct) = 7 octaves × 8 corners = 56 corner hashes → 1.45M ops per refresh / 2 frames = 725k/frame equivalent. Should be OK in modern JS (~3–5ms every other frame). If worried, refresh every 3 frames. I'll make refresh interval adaptive: measure compute time and adjust? Over-engineering; fixed every 2 frames is fine, and I'll cap GW×GH ≤ ~26k.

Hmm, actually one more consideration: noise scale relative to screen. Base frequency: I want features ~ 150–400 px. ψ sampled at freq such that 1 noise unit ≈ 260px → k = 1/260. Octave 0 at k, octaves at 2k, 4k... 3 octaves → finest feature ~65px. Good. Warp fields at slightly lower freq (1/380) with amp ~1.3 units ≈ 340px displacement. Nice big swirls.

Then curl: vx = dψ/dy, vy = -dψ/dx (per pixel). ψ range roughly [-1,1] over features of ~260px → derivative magnitude ~ (2/260) ≈ 0.0077/px... times scale factor S chosen for target speed. I'll normalize: after computing grid, find typical |∇ψ| via RMS and set speedScale so that median speed ≈ targetSpeed (like 40 px/s). Simpler: precompute gradient from grid differences (per cell, so gradient in cell units then convert), multiply by constant tuned at authoring time. But feature scale varies with window size if k fixed in px — I'll fix noise wavelength in px (relative to min(w,h) maybe, so composition adapts). Let me define scale = min(w,h)/900 roughly; noise coords = px / (260 * scaleFactor)? To keep the *character* consistent, base wavelength ~ 0.3 × min(w,h). Then gradient per px ~ 2/(0.3·minwh). Speed in px/s = |∇ψ|px · G · pxPerNoiseUnit... let me just do: velocities computed on grid as (ψ[y+1]-ψ[y-1]) etc. (cell units per 2 cells), then particle vel = (dvx, dvy) normalized-ish... 

Cleaner approach: compute gradient grid g = ∇ψ (per noise-unit: divide pixel-derivative by pxPerUnit). Then speed = |g| · G where G tuned. To be robust, I'll normalize gradients by their RMS computed during grid build (cheap accumulate) so mean |g| ≈ 1, then vel = g * targetSpeed * (something). RMS normalization guarantees consistent liveliness across devices/sizes. 

Also add slow global rotation swirl? Curl flow already has vortices; skip extra swirl, but add a very slow uniform drift that changes direction over minutes (tiny, like 2 px/s) to prevent fully closed orbits. Actually closed orbits in curl fields are rare since field morphs over time. Skip drift; keep pure.

**Structure of code:**
- CSS: body black, canvas block full, `overflow hidden`, `cursor: none`? No interaction needed but hiding cursor is rude if user moves mouse; keep default... actually a moving cursor over art is distracting, but hiding cursor is worse UX. Leave normal.
- JS modules (all inline):
  1. RNG (mulberry32 seeded) + permutation build.
  2. ValueNoise3 with perm table.
  3. fbm, warp.
  4. Field grid class: recompute(t) → stores ψ in Float32Array((GW+2)*(GH+2)) and derived vx, vy Float32Arrays.
  5. Palette system: array of palette definitions; paletteAt(time) returns function mapping u∈[0,1] → [r,g,b] (lerp between stops; crossfade between current/next palette). Precompute 32/64 bucket colors each frame (cheap) as `[r,g,b]`, plus rgba strings with the draw alpha.
  6. Wave system: schedule next wave time; state {origin, start, speed}; each frame update radius; particles check crossing; canvas gets a destination-out ring carve (annulus via two arcs? Simplest: ctx.globalCompositeOperation='destination-out'; ctx.beginPath(); ctx.arc(origin, r + bandHalf, 0, 2π); ctx.arc(origin, max(r - bandHalf, 0), 0, 2π, true); ctx.fill() with 'evenodd'? Using two arcs with opposite winding and fill with nonzero creates annulus. Yes: outer clockwise + inner counterclockwise → annulus with nonzero rule. alpha ~ 0.5 across a band ~ tens of px — but I want soft edges; a hard annulus edge might show a visible circle seam. Alternative: multiple concentric annuli with falloff alphas (3–4 rings, widths ~ band/3, alphas descending) → soft-ish. At 30–60px band with 4 sub-rings it'll look smooth enough given low alphas. Also note carving with destination-out reduces alpha; since we draw additive over black page, reducing alpha = darkening. Good.
  
  Wait — but there's subtlety: canvas is transparent after destination-out (composited over body bg). I'll set body background to the deep color and keep canvas transparent-black-accumulating. All painting additive on transparent canvas: 'lighter' on transparent pixels works (adds onto 0). Fade via destination-out works. Initial canvas cleared. Good — this architecture is clean: page bg provides base color.
  
  Edge case: 'lighter' with alpha — drawing rgba(r,g,b,0.12) with lighter adds r*0.12 to channels and 0.12*0.12? Actually compositing: source-over alpha accumulation... with 'lighter', result alpha = min(1, αs + αd), color adds premultiplied. On transparent dest, result color = source premultiplied color, alpha = 0.12. Subsequent strokes add. Channel values accumulate toward clamp. Displayed over body bg: canvas pixel premultiplied... display = src + (1-α)·bg → for α=0.5, shows color plus 50% of bg (near-black). Fine — standard glow accumulation.destination-out subtracts α uniformly across channels (premultiplied), so hue preserved. 

  7. Particles: typed arrays for x, y, px, py (prev), life, maxLife, speedMul, hueJitter/bucketOffset, energy(flash timer).
  8. Render loop: dt from timestamp (seconds), update timeBase; every other frame → field.recompute(t); compute bucket colors; per particle: sample field bilinear → (vx, vy); step; write segment into bucket lists (preallocated Int32Array of particle indices per bucket + counts); fade canvas (destination-out alpha ~ 0.045·(dt·60)); draw wave carve; then for each bucket: beginPath, all segments, stroke.
  9. Resize handler: debounce-ish immediate resize; rebuild grid dims; rescale particle positions proportionally (or just respawn randomly); recreate canvas size (this clears content — acceptable on resize; maybe re-fill bg). Use devicePixelRatio capped at 1.5–2 for perf. Trails: DPR 1 might look slightly soft but faster; I'll use min(devicePixelRatio, 1.75) and scale ctx. Hmm, line width 1 at DPR 2 = 0.5 css px — very fine, elegant. Keep lineWidth in device px constant-ish: set ctx transform to DPR and use lineWidth ~0.8.

  On resize: recompute field grid (dims depend on w,h), reposition particles: scale positions by ratio, reset prev. Fine.

**Bucketing details:** NB = 28 buckets. Per frame: counts = new Uint16Array? Reuse arrays: bucketCount Int32Array(NB), bucketItems Int32Array(NB * maxPerBucket)? Worst case all particles one bucket → NB × N memory = 28×5000×4B = 560KB, fine. Or simpler: counting sort with prefix sums into one Int32Array(N). Per particle compute color u → bucket index b; store idx in sorted order: standard two-pass counting sort. Then per bucket: ctx.strokeStyle = colorString[b] (precomputed per frame, NB strings — building 28 strings/frame is fine), beginPath, for items: moveTo(px,py) lineTo(x,y), stroke. Reborn-flash particles excluded from normal pass? They can be in both or drawn in a special pass with brighter alpha — simpler: include normally, and additionally a second stroke of just flash particles with white-ish tint alpha 0.3, lineWidth 1.6. Flash list small.

Hmm, even simpler alternative avoiding counting sort: since NB small, do NB passes over all particles? NB×N = 140k iterations/frame of cheap checks — actually fine too, but counting sort is one pass; do counting sort, it's clean.

Actually simplest robust: per frame build array of Float32 coords grouped... Let me just implement counting sort with prefix offsets into an Int32Array of size N, plus per-particle bucket array Uint8Array. Standard.

**Color mapping detail:** u = 0.5 + 0.5·ψnorm (ψ at particle, bilinear) plus per-particle jitter ±0.06, plus slow global bias drift sin(t·small)·0.1 → subtle breathing of distribution along the ramp. Clamp [0,1]. Map through ramp: palette stops (5–6 colors each with positions). Ramp function via precomputed LUT per frame? Palette changes continuously (crossfade + hue drift). Per frame, build LUT of 64 [r,g,b] from active blended palette — cost trivial. Then bucket color = LUT[bucketU]. Bucketing: bucket = floor(u·(NB-1)+0.5)? u→NB uniform; but LUT resolution 64 vs NB 28 — just compute bucket color directly from ramp function per bucket per frame (28 ramp evals/frame — trivial), skip LUT. Ramp eval = find stops, lerp. Fine.

Palette drift within palette: also slowly rotate stops' hue? I'll implement palette as stops in HSL-ish? Curated palettes defined as RGB stops; crossfade between consecutive palettes over blend windows; PLUS a gentle hue rotation applied via converting? RGB hue rotation is messy. Alternative: crossfade between palettes is already the "slow shift" — period ~ each palette holds 16s then 8s blend? In 30s you'd see ember → (blend) → verdigris partially: clear evolution. Additionally animate a slow position offset along ramp (uBias drift) so the *emphasis* colors change continuously. That plus crossfade = satisfying evolution without hue-rotation mess. And wave resets can also advance the palette phase slightly (palette phase tied to t anyway; waves make the change visible).

Hmm — maybe also drive uBias partly by wave events: after each wave, jump uBias to a new value → post-wave region clearly different coloring. Nice touch: each wave "re-ink" starts a new color emphasis. So palette state = f(t) smooth + per-wave offset. I'll do: uBias = 0.5 + 0.35·sin(t·0.05) + wavePhase (accumulates +0.37 per wave, wraps). Combined color richness.

**Alpha/glow tuning:** stroke alpha ~0.12; with 4000 particles at 60fps, overlapping strokes saturate fast in high-|∇ψ| lanes. Fade alpha per frame ~0.05 → steady-state luminance ≈ input rate / fade rate. Tune: fade 0.035–0.06. I'll pick fade base 0.045·(dt·60 normalized), clamp per-frame fade alpha min 0.02 max 0.12.

Note the 8-bit stuck-residue issue: destination-out alpha 0.045 → 11.5/255 decrements — no quantization stuck (needs > 1/255... it multiplies existing alpha by (1-a); stuck happens when round(α(1-a)) == α; with a=0.045, α up to 255: α·0.955; e.g. α=5→4.775→5 rounds to 5! Stuck for low alphas ≤ ~11. Residue ghost trails of low alpha ~ up to 11/255 ≈ 4% brightness. Slightly visible on OLED blacks. Mitigation: periodic "deep clean" — every wave also does full-canvas destination-out alpha 0.06 fill? That darkens everything once — visible as a soft step but during wave chaos it's imperceptible. Or: alternate fade between destination-out (alpha 0.05) and source-over bg-fill (alpha 0.02) — bg fill adds color floor... body bg near black; painting rgba(6,6,8,0.02) doesn't reduce alpha below its asymptote α_bg → actually painting over transparent canvas with source-over gives alpha ≥ ... asymptote α = a/(a + ... ) hmm asymptote of repeated paint a: α∞ = a (in limit), so it drives alpha → a·255 ≈ 5/255 residue instead — also residue but different. Simplest robust: after every destination-out fade, ALSO every frame subtract a tiny constant via 'destination-out' with alpha exactly 1/255 every 3rd frame? Constant decrement removes floor: α·0.955 floor issue fixed by guaranteed −1/255 every 3 frames for nonzero pixels. Hmm, does canvas guarantee α−1/255 when α≥1/255? destination-out: αd' = αd·(1−αs); with αs = 1/255, αd=255/255 → 254/255 exact. With αd = 4/255 → 3.984 → rounds to 4 (round-half?) → stuck but next pure decrement... it never decrements if multiplication rounds back. Ugh, browsers vary.

Pragmatic approach used widely: make fade alpha moderately large (≥0.05) AND every ~2.5s do a "sink" frame with destination-out alpha ~0.2 during... visible pop. Alternatively: accept faint residue — honestly with waves carving annuli periodically and complexity of composition, low-alpha residue (≤4% over near-black bg) is practically invisible, plus each wave passes an erasing ring across the whole canvas over time covering everything eventually (wave from random origin covers all points as radius grows unbounded → yes! a full expanding circle to cover screen wipes everything along its path... the ring band only wipes the band, not interior). Hmm interior was already passed — the band is where erasure happens; interior behind front keeps the earlier carve. Since band sweeps across all points once per wave, every pixel gets carved every wave. Residue then only accumulates between waves (~10s at 4/255 floor). Invisible. Fine — also add slight per-frame fade jitter (alpha random 0.03–0.07) which breaks rounding locks statistically since different multipliers per frame: stuck requires round(α(1−a_i))==α for all i; varying a breaks it. Add tiny jitter → solved mostly. 

**Numbers:**
- Particle count: base = clamp(round(area/380), 2500, 6000). For 1920×1080 → 5.5k. That's "thousands" ✓. Maybe area/450 cap 5500. Perf: 5.5k particles × cheap ops + ~5.5k segments batched into 28 strokes — canvas path stroke of 5.5k segments might be ~2–4ms; ok. Total frame budget ~8–12ms worst case. Acceptable; also I'll auto-degrade: measure average frame time over first seconds; if > 24ms, reduce particle count by 30% once or twice. Simple adaptive guard.

- Speed: base 34 px/s (scaled by min(w,h)/1000+ factor? On a 4K screen same px/s looks slower; scale speed by sqrt(area/(1920·1080)) clamped 0.7–1.6). Per-particle speedMul 0.5–1.6, plus 8% "streak" particles ×2.6.

- dt clamp: min(0.05, dt).

- Wave: first at t≈13s, then interval 10–16s random. Speed: covers min(w,h)·1.1 in ~4.5s → v = min(w,h)/4.5... to sweep full screen maybe radius to cover diagonal: keep wave alive until radius > diag + band; v ≈ max(w,h)/5.5? For 1920 wide → 350px/s, whole sweep ~ 6s. Two waves may overlap? Prevent scheduling while active. Fine: schedule next only after current finishes.

- Particle–wave interaction: track per particle `lastWave` id (Int32 or Uint16 wave index reset). Each frame if wave active: r = wave radius; for each particle dist² to origin; if dist < r and lastWave != waveId → respawn: lastWave = waveId; position = random point in annulus just behind front? "Reborn in the wake": spawn at distance r−(random·40px) from origin along a random angle? That clusters new life along the visible front — creating a traveling luminous frontier. I love that: the wave becomes a visible ring of fresh bright filaments sweeping the canvas, behind it old ink gone. Signature moment ✓. But careful: uniform density afterwards — particles spawned along ring then diffuse via flow; over seconds they redistribute; also non-waved region keeps its particles until front arrives. Since every particle eventually gets crossed, all respawn once per wave → uniform. 

  Also respawned particles get flash energy 1 decaying over ~0.9s → brighter/wider stroke.

- Also the canvas carve: per frame while wave active, carve annulus [r−w1, r+w2] with destination-out soft rings. Band ~ 70px: sub-rings at offsets with alphas like [0.05,0.12,0.18,0.12,0.05]. Per frame the band moves v·dt ≈ 6px/frame, overlapping rings each frame compound → effective erase very strong near front — that's fine (we want behind-front clean). Actually to keep "behind front is clean" I should carve a wider trailing region with lower alpha repeatedly — since band moves slowly relative to frame, region behind front receives carve for (band/v·60) frames ≈ 70/6 ≈ 12 frames × alphas → cumulative erase ≈ 1−∏(1−a) plenty. And ahead-of-front gets slight pre-erase from leading soft edge — acceptable (slight anticipation dimming). Good enough. Alternatively carve only [r−band, r+small] asymmetric so front edge is sharp: alphas weighted behind. I'll make leading edge narrow (8px soft) and trailing 90px.

- Flash drawing: for particles with energy>0: after main bucket pass, ctx.strokeStyle = brighter (mix color w/ white 40%? per-particle color unknown in batch — use single warm-white rgba(255,240,220,0.35·e)? per-particle alpha would need grouping; use fixed alpha 0.28, lineWidth 1.7, and include only flash particles in one path. Their brightness decays by not being included once energy < threshold. Slight pop but subtle.)

**Spawn distribution:** uniform random over screen. Initial particle prev = pos (no segment first frame).

**Bilinear sampling of field:** grid coords gx = x/cell, gy = y/cell; i0=floor, frac; clamp indices; vx = lerp of vx grid. Store vx,vy Float32Array size GW×GH (interior), ψ padded for derivative. Compute ψ on (GW+2)×(GH+2) padded, gradient central diff → vx,vy at interior cells... but then bilinear at edges needs clamping — fine with clamp.

RMS normalize: after computing all vx,vy: acc += vx²+vy² → rms = sqrt(acc/(2n)); if rms > 1e-6, scale = 1/rms; multiply arrays in place. Then also soften dead zones: some regions have near-zero gradient (flat potential) → particles crawl; that's okay, adds variety; but maybe map magnitude with slight power curve: v *= (0.35 + 0.65·min(1, mag)) after normalization? Hmm — normalization changes mag distribution; skip extra shaping, curl fields are fine. Actually a small detail: to avoid all particles moving at similar speeds (RMS norm ⇒ mean |v|≈1 in grid units), multiply vel by (0.4+0.6·u_noise)? Skip — per-particle speedMul gives variety.

Grid units: vx,vy stored in "grid-normalized" units where typical magnitude 1 → particle vel = v·targetSpeed·speedMul·dt px. targetSpeed base 36 px/s. Also directional component only? |∇ψ| varies; normalized grid makes fast lanes disappear... Wait: after RMS normalization the *whole field* scaled; local variation remains (some regions 3× rms, some 0.1×). Good — lanes preserved.

One more artistic touch — **line width variation by speed?** In bucket-batched path, single lineWidth per bucket... could set per-bucket width by bucket index — nah, width by bucket looks arbitrary. Keep uniform 0.9 + flash pass. Maybe two width classes: 15% "thick ink" particles drawn in separate pass lineWidth 2.2 alpha 0.08? That adds calligraphic depth. Implement via bucket trick: reserve bucket NB (index NB) = thick pass? Simpler: per-particle class stored; counting-sort buckets = colorBucket + (isThick ? NB : 0) → NB×2 groups; groups NB..2NB-1 drawn with wider line, alpha lower. Manageable: colorStrings arrays per pass with different alpha. I'll include it — richness worth it. Total passes ≤ 56 + flash. Each pass has beginPath/stroke overhead only when count>0.

**Palette definitions** (curated hex stops, u from 0→1). Design each ramp dark→bright so additive layering escalates naturally: low-u deep/dim, high-u luminous. But since u maps to structure (potential), not density, brightness variation adds depth either way. I'll design ramps with a dark anchor at start (background-ish tones barely visible) through saturated mids to pale bright ends:

1. **Ember**: ["#1a0b08", "#7a1e0c"? ...] Let me write ramps as [stop,hex] with positions:
   - Ember/Niagara-fire: 0.0 #26120e? Hmm, near-invisible darks waste ramp range... keep darkest at 0.03 luminance-ish. Let me craft:
     P1 "Kiln": [#38100a? ...]. Concretely:
     0.00 #2a0f0b, 0.22 #8c2b10, 0.45 #d95d1e, 0.68 #f2a541, 0.86 #ffd98a, 1.00 #fff3d1
   - P2 "Verdigris": 0.00 #04211c, 0.22 #0d5c4a, 0.45 #1f9e7e, 0.66 #56c9a2, 0.84 #b7e8c8, 1.00 #f2fbe9 — plus a gold accent? Insert 0.9 gold: restructure: 0.00 #031f19, 0.25 #0b5847, 0.5 #189a76, 0.7 #7fd0a0, 0.85 #d9e8a0? hmm #d9e8a0 chartreuse, 1.00 #fdf3c0 gold-cream. Nice green→gold.
   - P3 "Coral ink": 0.00 #23060e? deep wine #2b0714, 0.22 #7a1130, 0.45 #cf2f4e? → #d64550, 0.68 #f2788f? salmon #f2889b, 0.86 #ffb9a3, 1.00 #ffe9d6.
   - P4 "Glacier/aurora": avoid default-blue vibe; teal-cyan-green with ice: 0.00 #061a1e, 0.22 #0b4652, 0.45 #12798a? teal, 0.65 #2fb8a6, 0.84 #8fe6cf? , 1.00 #eafff2. This flirts with cyan-teal, fine (not the banned default blue/purple).
   Sequence: Kiln → Verdigris → Coral → Glacier → Kiln... Crossfade 9s between holds of ~13s? Full cycle 4×22 = 88s; in 30s you see Kiln→Verdigris mostly + start of Coral. Good.

Crossfade: given phase time p = (t + waveShift?) — should wave shift palettes too? I earlier had wavePhase affecting uBias. Keep palette timeline purely time-based (t·speed + initial offset), and uBias per-wave. Fine.

Blend: idx = floor(p) mod 4, frac = p - floor; ease blend near boundaries: use smoothstep on frac over last 40%? Simpler: continuous blend weight w = smoothstep between palettes: treat p continuous, i = floor(p), f = p − i, blend = smoothstep(f... if f < 0.55 hold pure palette i; else blend (f−0.55)/0.45 → palette i+1. Ramp at u: color = mix(ramp_i(u), ramp_{i+1}(u), blend). Ramp eval per bucket: stops arrays.

Colors as [r,g,b] parsed once at init.

**"Everything important in first 30s":** timeline: t=0 black; 0–3s field+trails emerge; palette Kiln visible immediately (choose initial palette phase to start mid-Kiln bright); uBias starts 0.5; by 8–10s intricate buildup; first wave at ~12–13s sweeps by ~18s revealing Verdigris-blend era + wake sparkle; second wave maybe ~26–29s? interval 10–16 → second at ~24–28 ✓ within window. Palette blend to Coral begins ~35s (outside) — hmm, to show a *palette shift* within 30s: make first palette hold shorter (10s) then blend 6s: Kiln 0–10s, blend 10–16 (visible shift!), Verdigris hold... So schedule: hold 11s, blend 7s. Within 30s: full Kiln→Verdigris shift + waves ✓. Also initial uBias drift gives continuous hue emphasis change anyway.

I'll also add a subtle overall slow zoom/breathing of the noise time and an extremely subtle scale evolution — the noise z-time handles evolution; skip extra.

**Auto quality guard:** keep simple — measure rolling avg dt after 3s warmup; if avg > 26ms and particles > 2200 → reduce count 25% (rebuild particle arrays or just mark unused tail... easier: keep arrays, use `activeCount` variable reduced). Also cap DPR at 1.6.

**Resize:** on resize → set canvas w/h = clientW·DPR, ctx.setTransform(DPR,0,0,DPR,0,0) — wait, I plan to draw in device pixels or css px? Use css-pixel coordinate system with transform scale(DPR): all math in css px. lineWidth 0.9 css px → 1.4 device at DPR1.6, good. On resize: rebuild grid sizes, rescale particle coords by (newW/oldW etc.), keep waves? cancel active wave (restart scheduling). Clear canvas happens automatically (resizing clears). Acceptable.

Also `visibilitychange`: when hidden, rAF pauses; on resume, dt clamp handles it.

**Noise quality check:** value noise with quintic fade, 3–4 octaves, warped — will produce slightly "boxy" lows compared to Perlin gradient noise, but with warping + curl derivative, artifacts vanish. Could implement gradient noise (better anisotropy)... gradient noise 3D needs gradients per corner — costlier hash → derived gradient via sin? Use value noise; fine at this abstraction.

Actually, let me upgrade to **Perlin-style gradient noise** but cheap: gradient from hash → precomputed 16 gradient dirs table lookup: g = GRAD[h & 15] → dot with offset. Cost similar to value (hash gives index, then dot product). Quality notably better (less axis-aligned blobbiness). I'll implement 3D Perlin-ish: for 8 corners: h = P[(P[(P[X]+Y)&255]+Z)&255] & 15; grad dot (fx,fy,fz) with fade quintic trilinear. Classic Ken Perlin improved noise — I know it by heart. Range [-1,1]·~0.7. Implementation with permutation table of 256 shuffled by seeded RNG, duplicated to 512.

Improved noise fade quintic. grad function standard:
```
function grad(h, x, y, z) {
  h &= 15;
  const u = h < 8 ? x : y;
  const v = h < 4 ? y : (h === 12 || h === 14 ? x : z);
  return ((h & 1) === 0 ? u : -u) + ((h & 2) === 0 ? v : -v);
}
```
Yes.

fbm(x,y,z,oct): amp sum normalization; per octave freq×2, offset + shift to decorrelate (add 19.19 per octave? Standard: use different lattice naturally since freq doubles — but low freq doubling in 3D with same perm is fine, though first two octaves correlate when... it's standard practice, fine; add small offsets to be safe).

Warped potential:
```
function psi(x, y, t) {
  const wx = fbm(x*kw + 31.4, y*kw - 17.2, t*tw1, 2);
  const wy = fbm(x*kw - 11.9, y*kw + 47.7, t*tw2 + 5.3, 2);
  return fbm(x*k + A*wx, y*k + A*wy, t*tz, 3);
}
```
k = 1/(0.33·minDim)?? If minDim small (phone 375) wavelength 124px fine. Use baseWavelength = clamp(min(w,h)·0.36, 130, 420). k = 2π/wavelength? Perlin feature size ~ 1 unit; so k = 1/wavelength·(1/1.2)... whatever, k = 1/(wavelength). Actually Perlin "feature size" ≈ 1 lattice cell = 1/k px. Set cell = wavelength → k = 1/wavelength. Warp kw = k·0.6 (bigger warp structures), A = 1.8.

Time rates: tz = 0.10? ψ changes noticeably in a few seconds — want slow morph: features should hold ~5–10s → rate ~0.08–0.15 units/s gives lattice drift of one cell in ~8s. tw1 = 0.05, tw2 = 0.07 (warp evolves slower/differently). Also maybe modulate: t used = t + wave-triggered small jump? Waves already visually reset; keep smooth.

Per refresh compute cost: (GW+2)(GH+2) psi evals. GW~214,GH~121 → 218×125=27.2k evals × (2+2+3... warp fbm 2 oct ×2 =4, main 3 oct → 7 octaves ×8 corners = 56 grad-noise corners) ≈ 1.52M corner ops every 2 frames. Perlin corner op ~ maybe 15–25ns JS → 25–35ms?! That's too slow!! Hmm. Let me recount: corner op = perm lookups (3) + grad dot (~6 flops) + later trilinear (7 lerps shared per 8 corners). Realistically improved-noise n3 call ≈ 100–200ns in JS. 7 octaves ≈ ~1µs per psi eval. 27.2k evals ≈ 27ms. Way too slow every 2 frames!

Need to cut ~10×. Options:
(a) Coarser grid: cell 16px → GW 120, GH 68 = 8.2k cells → ~8ms per refresh. Every 3 frames → ~2.7ms/frame amortized. Feasible but 16px cells + bilinear on smooth field — fine actually! The field is smooth at wavelength 300px; 16px sampling more than adequate. Bilinear interpolation reconstructs well. Particles moving 0.5–1px/frame across a 16px grid — interpolation smooth. ✓
(b) Fewer octaves: warp 1 oct each, main 2 oct → 4 octaves = 32 corners → halves cost. Quality still good with warp.
(c) Refresh every 3–4 frames with temporal blend between old/new grids to avoid 30Hz→20Hz stepping: field change per refresh is small anyway; stepping invisible. Or lerp grids: keep two buffers, on refresh compute into B then blend? Extra cost; simpler: refresh every 3rd frame, accept 20Hz field update — motion is 0.5–1px/frame; a 3-frame step = ~2px positional quantization... visible as slight micro-jitter? With bilinear field and speed 40px/s: per refresh 2px displacement; error from stale field ~ rotation of vector over 50ms — small direction change; imperceptible in trails. OK: every 3rd frame, cell 15px.

Recount (c)+(b): padded grid (120+2)×(70+2) = 8.8k evals × 4 octaves(1+1+2? main 2 octaves might be too smooth for intricacy... main 3) → warp 1+1, main 3 = 5 oct ≈ 0.7µs → 6.2ms per refresh, /3 frames = 2ms amortized ✓. On a big 4K window, cap grid dims: GW,GH ≤ 150×90 via cell = max(15, w/150, h/90). ✓

Also I can skip warp on margins cheaply? No, keep uniform.

Let me finalize octaves: warp: 1 octave each (large-scale swirl displacement — warping with 1 octave still breaks geometry nicely; with A=1.8 displacement ~ ±1.3 lattice cells). main: 3 octaves. Total 5. Also could precompute warp fields on an even coarser grid (half-res) and bilinear them during main pass — micro-opt, skip.

Additionally: RMS normalize per refresh (cheap loop).

**Max-speed clamp:** after normalization clamp particle step length to ~ cell (15px)·0.9 per frame to avoid grid-aliasing artifacts (rare spikes).

**Frame loop order:**
1. t = ts/1000; dt = clamp(t - lastT, 0, 0.05).
2. if (frame % 3 === 0) field.update(t).
3. Update wave radius; if active: carve annulus on ctx (destination-out).
4. Fade: destination-out fillRect alpha = fadeBase·(dt·60) with jitter.
5. Compute palette bucket colors (NB=26 colors as strings) — precompute per frame.
6. Counting-sort pass assignment: for each particle i: update physics (sample field bilinear, integrate, bounds wrap, life, wave check/respawn, flash decay), determine colorU → bucket b; store segments into per-bucket arrays (counting sort: first count pass? Need bucket per particle first — do physics pass storing bucket in Uint8 array and px,py→x,y in Float32 arrays; then counting sort indices; then draw pass reads arrays. Two loops over N with simple ops — fine).
7. Draw: for b in 0..NB-1: if count: style color[b] alphaA; path from sorted idx. For thick class similar with alphaB, lineWidth 2.4. Flash pass.
8. rAF.

Physics details:
- gx = x·(1/cell), clamp to [0.5? ...] Bilinear with clamp at edges; if particle outside (shouldn't due wrap), clamp.
- vel from grid × targetSpeed × speedMul; x += vx·dt·speed... plus tiny jitter: x += (rand-0.5)·0.15.
- Wrap with margin 2: if x<−2 → x+=W+4 etc.; skip segment (set drawFlag 0 / or set px=x after wrap → zero-length segment naturally invisible: set px=x, py=y (new) so segment length 0. ✓ elegantly handled).
- life: life −= dt; if life<0 → respawn random pos, new maxLife 7–22s, speedMul resample, reset flash? small flash at every respawn? Only wave-respawn flashes; natural respawn quiet (alpha ramp-in? without ramp, new particle appears mid-screen — with low alpha stroke it's unnoticeable). Also to avoid long-term clumping: natural respawn uniform random keeps ergodicity ✓.
- Wave check as described; on wave-reset: pos = origin + dir·(r − rand·50) clamped in bounds... if annulus point outside canvas, clamp into canvas (or reflect). Simple: compute point, clamp to [4, W−4]; multiple may stack at edges — acceptable, or re-roll up to 3 tries for in-bounds point. Fine, re-roll 3×.
- flash: e = 1; e −= dt·1.4; include in flash pass while e>0.15.

Segment arrays: sx0,sy0,sx1,sy1 Float32Array(N) — actually I already store px,py,x,y arrays; counting sort stores particle index; draw pass reads pos arrays via index. Need prev pos stored per particle (px,py updated to current after step). ✓

Bucket mapping: colorU = clamp(0.5 + 0.5·psiN + jitter_i + uBiasWave + slowSin, 0, 1)·(NB-1) rounded → Uint8. Need ψ value per particle: during bilinear sampling, also interpolate ψ grid (have it) — one extra lerp set, cheap. psiN from grid normalized? ψ roughly [-1,1] but warped fbm distribution concentrated; apply slight contrast: psiN = clamp(psi·0.85+0.5). Plus temporal uBias = 0.13·sin(t·0.11+2) + waveHueOffset (each wave adds 0.41 mod 1). This shifts which ramp slice maps to typical ψ ✓.

**Thick particles:** class stored Uint8 (0 thin,1 thick, plus speedMul high for some). countThick ≈ 12%.

**Fade & glow balance:** stroke alpha thin: 0.10; thick: 0.05; flash: 0.30 white-warm. fade alpha base 0.05 ± jitter 0.015. I'll expose tunables at top. Additive 'lighter' for strokes; carve & fade 'destination-out'; make sure to reset composite per step (set once per phase).

**Also subtle background texture?** No — keep black canvas purity.

**Vignette via particle density?** no.

**Initial moments:** to avoid flat start, prefill: run ~90 warmup steps of field updates across pre-time (t from −6 to 0)? Field history irrelevant — particles start drawing immediately; buildup over 0–10s is part of the show (recording captures emergence ✓). Give initial particles staggered lives. Maybe start with slight burst: all particles flash=0.6 at t=0 → luminous birth sweep, then settles. Subtle nicety; or skip (could read as odd). I'll give initial gentle flash 0.4 — a soft luminous fade-in. Nice.

**Title/description UI?** Pure art piece — no UI. Maybe nothing at all. Keep body just canvas.

**Code size:** ~450–550 lines. Let's write it carefully.

Let me now write the noise precisely.

```js
const PERM = new Uint8Array(512);
(function seedPerm(seed){
  const rand = mulberry32(seed);
  const p = new Uint8Array(256);
  for (let i=0;i<256;i++) p[i]=i;
  for (let i=255;i>0;i--){ const j=(rand()* (i+1))|0; const t=p[i]; p[i]=p[j]; p[j]=t; }
  for (let i=0;i<512;i++) PERM[i]=p[i&255];
})(1337);

function fade(t){ return t*t*t*(t*(t*6-15)+10); }

function grad(h, x, y, z){
  h &= 15;
  const u = h < 8 ? x : y;
  const v = h < 4 ? y : (h === 12 || h === 14 ? x : z);
  return ((h & 1) ? -u : u) + ((h & 2) ? -v : v);
}

function noise3(x, y, z){
  let X = Math.floor(x), Y = Math.floor(y), Z = Math.floor(z);
  x -= X; y -= Y; z -= Z;
  X &= 255; Y &= 255; Z &= 255;
  const u = fade(x), v = fade(y), w = fade(z);
  const A = PERM[X]+Y, AA = PERM[A]+Z, AB = PERM[A+1]+Z;
  const B = PERM[X+1]+Y, BA = PERM[B]+Z, BB = PERM[B+1]+Z;
  const n000 = grad(PERM[AA], x, y, z);
  const n100 = grad(PERM[BA], x-1, y, z);
  const n010 = grad(PERM[AB], x, y-1, z);
  const n110 = grad(PERM[BB], x-1, y-1, z);
  const n001 = grad(PERM[AA+1], x, y, z-1);
  const n101 = grad(PERM[BA+1], x-1, y, z-1);
  const n011 = grad(PERM[AB+1], x, y-1, z-1);
  const n111 = grad(PERM[BB+1], x-1, y-1, z-1);
  const x00 = n000 + u*(n100-n000);
  const x10 = n010 + u*(n110-n010);
  const x01 = n001 + u*(n101-n001);
  const x11 = n011 + u*(n111-n011);
  const y0 = x00 + v*(x10-x00);
  const y1 = x01 + v*(x11-x01);
  return y0 + w*(y1-y0); // ~[-1,1]
}
```
Note PERM needs length 512 with values ≤255 and indexing PERM[A+1] where A = PERM[X]+Y ≤ 255+255=510, +1 = 511 ✓.

fbm:
```js
function fbm(x, y, z, oct){
  let a = 0.5, f = 1, s = 0, norm = 0;
  for (let o=0;o<oct;o++){
    s += a * noise3(x*f + o*17.31, y*f + o*9.7, z*f + o*31.7);
    norm += a; a *= 0.5; f *= 2.03;
  }
  return s / norm;
}
```

Potential:
```js
function potential(px, py, t){ // px,py in pixels
  const nx = px * kInv, ny = py * kInv;
  const wx = noise3(nx*0.55 + 13.7, ny*0.55 - 71.3, t*0.045 + 3.1);
  const wy = noise3(nx*0.55 - 47.9, ny*0.55 + 28.4, t*0.06 + 11.7);
  return fbm(nx + 1.9*wx + 5.2, ny + 1.9*wy - 8.4, t*0.09, 3);
}
```
Hmm — main time rate 0.09: per refresh (3 frames = 50ms) Δz = 0.0045 lattice — tiny drift ✓. Warp time rates slower.

Wait, warp coordinates: nx·0.55 → warp feature ~ 1/0.55 ≈ 1.8× base wavelength — good (big slow sways).

**Grid update:**
```js
class Field {
  constructor(){ this.psi=null; this.vx=null; this.vy=null; this.gw=0; this.gh=0; this.cell=16; }
  resize(w,h){
    this.cell = Math.max(14, Math.ceil(Math.max(w/150, h/95)));
    this.gw = Math.ceil(w/this.cell)+1;
    this.gh = Math.ceil(h/this.cell)+1;
    this.pw = this.gw+2; this.ph = this.gh+2; // padded
    this.psi = new Float32Array(this.pw*this.ph);
    this.vx = new Float32Array(this.gw*this.gh);
    this.vy = new Float32Array(this.gw*this.gh);
  }
  update(t, w, h){
    const {pw,ph,psi,cell} = this;
    const k = 1/this.waveLen; ...
```
I need wavelength — pass in or compute from w,h in resize: this.waveLen = clamp(Math.min(w,h)*0.36, 130, 430); kInv = 1/waveLen.

Fill padded psi: for j in 0..ph-1: py_px = (j-1)*cell (can be negative — fine, noise domain infinite), for i: psi[idx] = potential(px,py,t).

Gradients: for gj in 0..gh-1, gi in 0..gw-1: using padded indices i=gi+1, j=gj+1:
dψ/dpx = (psi[i+1,j] − psi[i−1,j]) / (2·cell) per px → in noise units per px. Convert to noise-units-per... I want velocity direction & relative magnitude; direction: vx ∝ ∂ψ/∂y, vy ∝ −∂ψ/∂x. Magnitude in "noise units per px" ~ 2·(1/waveLen)... whatever — normalize RMS anyway, so just set vx = psi[right]−psi[left], vy = psi[down]−psi[up] (cell-unit differences; same direction as derivatives, uniform factor 2cell irrelevant). ✓ Then RMS-normalize to mean magnitude ~1:
acc += vx²+vy²; rms = sqrt(acc/(gw*gh*2)); s = 1/max(rms, 1e-5); multiply through. Cap? Some cells near contours have |v| big; cap max mag at 3.5 after normalize (loop) — or clamp per particle step. I'll clamp in particle step.

ψ for coloring: particle bilinear over psi interior using same gi mapping.

Bilinear sample:
```js
sample(x, y, out){ // out.vox,voy,psi
  const gx = clamp(x/cell, 0, gw-1.001), gy = ...
  i=floor... 
}
```
Inline in particle loop for speed — fine, write as Field method returning via shared temp object or module-level vars. Use closure vars (module scope `let sVX, sVY, sPSI`) — method writes them.

**Wave carve geometry:** band: front at r. Erase region: [r−trailW, r+leadW], trailW=90, leadW=10, soft via 5 sub-annuli:
offsets/alpha: {−80,0.05},{−50,0.10},{−25,0.16},{−5,0.22},{+3,0.10}? Let me define sub rings centers at r−75,r−48,r−24,r−6,r+2 with half-widths ~14–22 and alphas .06,.11,.16,.20,.10. Drawing 5 annuli per frame during wave (~6s ≈ 360 frames × 5 fills) — trivial. Annulus fill:
```js
ctx.beginPath();
ctx.arc(ox, oy, rOut, 0, TAU);
ctx.arc(ox, oy, rIn, 0, TAU, true);
ctx.fill();
```
nonzero winding: outer CW (default), inner CCW (anticlockwise=true) → annulus ✓ (assuming rIn≥0; clamp rIn≥0; if rIn===0 inner circle adds nothing problematic — a zero-radius CCW arc contributes nothing ✓).
Front "leading" carve means area just ahead slightly dimmed — front visibility: since ahead is old bright image and behind is clean, the transition is crisp enough.

Additionally, should the wave front have a faint visible luminous edge? The reborn flashing particles along the wake ARE the visible edge. 

Wave completion: when r > maxR = sqrt(w²+h²) + trail + ... i.e., r − trailW > diag → deactivate, schedule next: nextWaveT = t + 9 + rand·6.

Also during wave, boost fade slightly? No need.

First wave at t0 = 12.5. waveHueOffset starts 0; each wave += 0.43.

**Spawn from wave:** ppos angle random, dist = r − 6 − rand·55; x = ox + cos·dist etc.; retry 4× if outside [6, W−6]×... else clamp. Set flash=1, life reset random, px=py=new pos.

Note: wave passes over ALL particles including just-spawned ones near front from previous frames — since check is `dist < r && lastWave !== id`, newly spawned behind front have lastWave=id → skipped ✓.

**Adaptive quality:** 
```js
let acc=0, n=0;
each frame after warmup (t>2): acc+=dt; n++;
if (n===240){ avg=acc/n; if (avg>0.028 && active>Nmin) active=floor(active*0.72), reset counters to re-check after another 240; }
```
Simplify: check every 4s window; allow max 3 reductions. Also reduce DPR? Keep DPR fixed 1.5 for predictability. Hmm — high-DPI phones (DPR 3) with css 390×844 → 585×1266 device px fine.

Let me set DPR = min(devicePixelRatio||1, 1.75).

**Segment drawing perf:** 26 buckets ×2 classes: worst 52 stroke calls each with up to N subsegments — the stroke() on huge paths is the cost; total segments = active(~5000) split across buckets → total path complexity constant regardless of bucketing ✓.

lineWidth: thin 1.0, thick 2.6; lineCap 'round'? round caps on 5000 segments cost more; 'butt' fine; maybe 'round' adds softness... perf risk; use 'butt' (default). Alpha low, seams invisible.

Colors per bucket per frame: build array of 26 strings `rgba(r,g,b,a)`. Ramp eval: palettes pre-parsed to stops {p:[positions], c:[[r,g,b]...]}. rampEval(pal, u) → find segment (stops sorted, ≤6 → linear scan fine ×26×2 palettes ×60fps trivial).

Blend palettes: current i and next (i+1)%4 with blend weight b: color = mix per channel. Implement getBucketColors(t): compute palette pair + weight once, then per bucket eval both ramps and mix.

Palette timeline: PH = 11s hold, BL = 7s blend → period 18s per palette, cycle 72s. p = t/18 → continuous; within cycle: f = p mod 1; if f < holdFrac(=11/18) → pure i; else blend smoothstep((f−holdFrac)/(blendFrac)). i = floor(p) mod 4. ✓ In first 30s: f goes 0→(30/18=1.667): shows Kiln (0–11s), blend (11–18s), Verdigris (18–29s), start blend #2 at 29s ✓ lovely.

Wait — with floor(p) cycling i, at p=1.0 (t=18) i jumps 0→1 exactly when blend finished ✓ continuous.

**uBias slow motion:** uBias = 0.10·sin(t·0.10+1.7) + waveHue. Combined with psiN·... colorU = frac? clamp(psiN·0.9 + 0.05 + uBias + jitter, 0, 1) where psiN∈[0,1]. If uBias pushes out of [0,1], clamp → colors pile at ends — clamp is fine (ends are darkest/brightest anchors; piling at bright end could bloom). Use softer waveHue ±: waveHue accumulates mod 1 but then clamp squashes... Better: make colorU = wrap? Wrapping ramp discontinuity for colorU only — ramp evaluated at wrapped u: u = (raw mod 1) — discontinuity at wrap in space would show as color seam along a contour... but ramps start & end dark-ish? Kiln ends bright cream — seam visible as a line where ψ crosses threshold — actually could look intentional (contour line)! Risky; keep clamp but limit uBias amplitude: slowSin 0.10, waveHue adds ±0.35 alternating direction? Let me do waveHue = 0.30·sin(waveIndex·2.1) — bounded ±0.3, total bias ∈ [−0.4, 0.4]; psiN·0.85+0.075 keeps base ∈[0.075,0.925]; sum can hit clamps sometimes — acceptable and simple.

**jitter per particle:** fixed random ±0.05 (stored) — static per particle... particles respawn reuse jitter (fine).

**Now — sizes/alloc:**

```js
const MAXP = 7000;
x,y,px,py: Float32Array(MAXP)
spd, jit, flash, life: Float32Array(MAXP)
cls (0/1), lastWave: Uint8/Int16Array(MAXP) — lastWave up to ~255 waves wraps: use Uint16 & waveId % 65536... simpler Uint8 with waveId&255 and initial lastWave=255(=none? collision when waveId&255===255...). Use Int32Array — memory trivial (28KB). Fine: Int32Array filled −1.
bucket: Uint8Array(MAXP)
order: Int32Array(MAXP)
counts: Int32Array(NB*2)
```

**Draw loop:**
```js
// physics+bucket pass
for i<active:
  sample field...
  integrate, wrap, life, wave...
  compute colorU → bucket[i] = b + cls[i]*NB
  counts++
// prefix sums → starts
// scatter order[starts[b]+k]... standard counting sort with running offset array (use starts copy)
// draw
```

Counting sort impl:
```js
counts.fill(0);
pass1: counts[bucket[i]]++
let sum=0; for b: starts[b]=sum; sum+=counts[b]; (starts = Int32Array(NB*2+1))
cursor.set(starts.subarray?) — use separate Int32Array cursor; for i: order[cursor[bucket[i]]++]=i.
```
✓.

**Flash pass:** collect flashIdx count while physics loop (order independent — draw after buckets): ctx.strokeStyle = 'rgba(255,244,224,0.5)' fixed; globalAlpha? encode e into... fixed alpha 0.35, lineWidth 1.6; path of segments where flash>0.12. Their bucket pass also drew them — fine (double bright core).

Hmm — flash alpha fixed 0.5 might strobe hard since many particles share front → a bright ring line — actually THAT is gorgeous: the wave visibly draws a luminous ring of fresh strokes that decays over ~0.7s. Keep 0.4.

**Order of canvas ops per frame:**
1. gco='destination-out': wave carve (if active) — carve BEFORE fade or after? Order irrelevant-ish (both multiplicative-ish alpha reduction). 
2. fade fillRect.
3. gco='lighter': draw all passes.
4. reset gco='source-over'? Not needed if always set before each phase (set explicitly each frame).

Alpha of fade fill: fillStyle 'rgba(0,0,0,alpha)' with destination-out — only alpha matters.

fade alpha per frame: base 0.045 + jitter(±0.02) scaled by dt·60 → a = (0.045 + 0.02·(rand−0.5))·(dt·60) — wait dt·60 ~1; clamp a to [0.01, 0.2]. During wave maybe slightly higher a×1.3 — helps crisp reset. ok: if wave active a *= 1.5.

Hmm — with stroke alpha 0.10 and fade 0.045: steady state ≈ each pixel receives strokes at rate proportional to local particle flux; filaments where flow concentrates will glow strongly, background regions dim — good contrast. Should be tunable; I'll pick values from experience: thin alpha 0.12, thick 0.055.

**targetSpeed:** 42 px/s base × sizeScale = clamp(Math.sqrt((w*h)/(1920*1080)), 0.65, 1.7). Per-particle spd = sizeScale·(0.55+rand^1.5·1.5) → range ~0.55–2.05·... plus cls thick? thick slower ×0.8 (broader strokes look heavy when fast). Streak class: 6% particles spd ×2.8 (merge into thin class, just big spd).

Also particle motion adds slight perpendicular oscillation? no — keep pure.

Step clamp: maxStep = cell·0.75 per frame... compute len = hypot(vx,vy)·spd·dt·targetBase... let me define vel = fieldV (normalized, typ |v|≈1) → dx = vx·SPD·spd·dt where SPD = 46·sizeScale? Let me just: speedPx = 44·sizeScale·spd; dx = vx·speedPx·dt. Clamp |dx,dy| to cell·0.8: compute d2; if > max2 scale. Rare; fine.

**Field sampling function inline:**
```js
function sampleField(f, x, y){
  let gx = x * f.invCell, gy = y * f.invCell;
  if (gx<0) gx=0; else if (gx>f.gw-1) gx=f.gw-1;
  ...
  const i = gx|0, j = gy|0;
  const fx = gx-i, fy = gy-j;
  const i0 = i, i1 = i+1<gw? i+1 : i... (since gx clamped ≤ gw−1, i ≤ gw−1, i+1 could be gw → clamp index)
  base = j*gw+i;
  const w00 = (1-fx)*(1-fy) ... standard.
  sVX = vx[base]*w00 + vx[base+1]*w10 + vx[base+gw]*w01 + vx[base+gw+1]*w11; // careful naming
  same vy, psi (psi padded — use separate mapping; simpler: store psiColor = separate gw×gh array copied from padded interior during update? Extra copy 10k floats per refresh — trivial. Do that: this.psiS (smooth interior). Actually just bilinear directly on padded with offset −1: gp index (j+1)*pw+(i+1). Same cost; do that, no extra array.)
}
```
✓ use padded psi directly.

**Wrap:** if (x < -m) x += w+2m... with m=2. After wrap, px=x etc. (draw skip). Also particle exactly at clamp edges of grid — handled.

**Life respawn:** maxLife = 8+rand·16; life initialized random·maxLife so lifetimes desync ✓.

**Let me also double-check the "reset wave" covers requirement** "occasional gentle reset waves so the image keeps evolving instead of saturating" ✓ — erases annulus, respawns particles with flash, shifts hue emphasis, waves every ~10–16s.

**Loop/continue after 30s:** continues indefinitely with palette cycle 72s and waves forever ✓.

**One more art-direction check:** the piece = black field, luminous etched filaments in curated ramps, curl-noise topology, traveling reset front with sparkling wake, palette crossfades. Signature moment = reset wave ✓. No gradient-ornament UI, no text, no interaction. Good taste: restrained, one idea carried through.

Edge: `preserveDrawingBuffer` n/a (2d). Canvas context creation `{ alpha: true }` default true fine. Also `ctx.globalCompositeOperation='lighter'` with transparent canvas — check: 'lighter' adds src & dst premultiplied ✓.

Also `desynchronized: true` hint could help perf; harmless. Add `{ alpha: true, desynchronized: true }`.

**Resize:** window resize event + also handle DPR change? Keep simple: on resize, re-init sizes, transform, field.resize, particle rescale (old→new ratio), waves canceled (waveActive=false; nextWaveT = t+6). Note: resize clears canvas — but actually changing canvas.width clears even if same? Only when value changes. Guard: if same dims, skip. On resize also do a soft re-fill? Cleared = black start; trails rebuild in seconds — acceptable (and I'll respawn all particles fresh + flash 0.5 for a graceful rebirth).

Also orientation change on mobile covered by resize.

**Visibility:** rAF stops automatically; dt clamp 50ms prevents jumps ✓. Accumulated palette time uses rAF timestamps so no drift.

**Write the code now.** Structure:

```html
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" ...><title>...</title>
<style>
  html,body{margin:0;height:100%;background:#07070a;overflow:hidden}
  canvas{display:block;width:100vw;height:100vh}
</style>
</head>
<body>
<canvas id="c"></canvas>
<script>
'use strict';
/* ---------- utils ---------- */
mulberry32, TAU, clamp, lerp
/* ---------- Perlin noise ---------- */
perm table, fade, grad3, noise3, fbm
/* ---------- palette ---------- */
PALS = [...]; parse hex
rampColor(pal, u, out3)
palettePhase(t) → i, blend
/* ---------- state ---------- */
canvas, ctx, W,H,DPR
particles arrays
field object
wave state
/* ---------- init/resize ---------- */
/* ---------- field update ---------- */
/* ---------- frame ---------- */
</script>
</body>
</html>
```

Let me carefully write each part with tuned constants.

Palettes (final picks — checking each for taste, avoiding Tailwind-blue/purple):
```js
const PALETTES = [
  // Kiln — ember & gold
  ["#200b08","#6d1f0d","#c14a17","#e88a2e","#f7c46a","#ffedc4"],
  // Verdigris — jade to gold cream
  ["#04231c","#0b5a45","#17936f","#4cc59a","#a5e3b6","#f4ecc0"],
  // Coral ink — wine to peach
  ["#26060f","#6e1030","#b52645","#e35b6e","#f79d8e","#ffe4c9"],
  // Glacier — deep teal to pale mint
  ["#041a20","#0a4152","#106e7d","#22a3a0","#7edcc3","#e9fff0"],
];
```
Positions: evenly spaced stops (i/(n−1)). Even spacing fine for these ramps.

Parse once → {p:[...], c:[...] flat arrays? store as arrays of [r,g,b]].

ramp(palA, palB, mix, u, out): locate segment in A (positions equal across palettes since same count & even spacing → reuse index) — both have 6 stops evenly at 0,0.2,...,1.0 → seg = min(4, floor(u*5)); f = u*5−seg; cA lerp stops, cB lerp stops, mix. Write [r,g,b] to shared temp; bucket strings built per frame.

Bucket colors: NB=26; per frame:
```js
for b: u=(b+0.5)/NB; rampColor(...); colStr1[b]=`rgba(r,g,b,0.12)`; colStr2[b]=`rgba(r,g,b,0.055)`;
```
String building 52/frame — fine. Actually store the rgb triplet per bucket in a Int array and build strings — yes.

Hmm, alpha as fixed strings: thin A=0.12, thick A=0.06.

**Flash stroke style:** 'rgba(255,243,220,0.38)'.

Now write the Field update with potential() closed over current params (wavelength etc. stored on field; potential uses field props or module vars kw etc.). I'll make potential a standalone function taking (x,y,t,invLen).

Let me now also double check noise3 correctness (Improved Perlin):
- X &=255 after floor; negative coords: Math.floor handles; & 255 on negative int in JS: (-1 & 255) = 255 ✓ (two's complement) — works.
- grad via PERM[AA]... standard.
- output range roughly [−1,1] (actually ±~0.87 max). fbm normalized sum ok.

**Potential & field update code:**

```js
const field = {
  cell:16, invCell:1/16, gw:0, gh:0, pw:0, ph:0,
  psi:null, vx:null, vy:null, invLen:1/300,
  resize(w,h){
    this.cell = Math.max(14, Math.ceil(Math.max(w/150, h/95)));
    this.invCell = 1/this.cell;
    this.gw = Math.floor(w/this.cell)+1;
    this.gh = Math.floor(h/this.cell)+1;
    this.pw = this.gw+2; this.ph = this.gh+2;
    this.psi = new Float32Array(this.pw*this.ph);
    this.vx = new Float32Array(this.gw*this.gh);
    this.vy = new Float32Array(this.gw*this.gh);
    const L = clamp(Math.min(w,h)*0.36, 130, 430);
    this.invLen = 1/L;
  },
  update(t){
    const {pw,ph,psi,invLen} = this;
    const k = invLen;
    let idx=0;
    for (let j=0;j<ph;j++){
      const ny = (j-1)*this.cell*k;
      for (let i=0;i<pw;i++){
        const nx = (i-1)*this.cell*k;
        const wx = noise3(nx*0.52+13.7, ny*0.52-71.3, t*0.043+3.1);
        const wy = noise3(nx*0.52-47.9, ny*0.52+28.4, t*0.057+11.7);
        psi[idx++] = fbm(nx + 1.85*wx + 5.2, ny + 1.85*wy - 8.4, t*0.085, 3);
      }
    }
    // gradients + rms
    const {gw,gh,vx,vy} = this;
    let acc=0, o=0;
    for (let j=0;j<gh;j++){
      const row=(j+1)*pw+1;
      for (let i=0;i<gw;i++){
        const p=row+i;
        const gxv = psi[p-1]-psi[p+1];   // = -2cell·dψ/dx → vy ∝ −dψ/dx ∝ +gxv
        const gyv = psi[p+pw]-psi[p-pw]; // = 2cell·dψ/dy → vx ∝ dψ/dy ∝ gyv
        vx[o]=gyv; vy[o]=gxv;
        acc += gyv*gyv+gxv*gxv;
        o++;
      }
    }
    const rms = Math.sqrt(acc/(gw*gh*2)) || 1e-6;
    const s = 1/rms;
    for (let n=0;n<gw*gh;n++){ vx[n]*=s; vy[n]*=s; }
  },
  ...
}
```
Check curl sign: velocity = (∂ψ/∂y, −∂ψ/∂x). vx = gyv = psi[j+1]−psi[j−1] = 2cell·∂ψ/∂y ✓ (y increases downward on screen — orientation just mirrors, irrelevant). vy = gxv = psi[i−1]−psi[i+1] = −2cell·∂ψ/∂x ✓.

**Sampling (module func):**
```js
let sVX=0,sVY=0,sPSI=0;
function sample(x,y){
  let gx = x*field.invCell, gy = y*field.invCell;
  const gw=field.gw, gh=field.gh;
  if(gx<0)gx=0; else if(gx>gw-1) gx=gw-1;
  if(gy<0)gy=0; else if(gy>gh-1) gy=gh-1;
  const i=gx|0, j=gy|0, fx=gx-i, fy=gy-j;
  const b=j*gw+i;
  const vx=field.vx, vy=field.vy, psi=field.psi, pw=field.pw;
  const w00=(1-fx)*(1-fy), w10=fx*(1-fy), w01=(1-fx)*fy, w11=fx*fy;
  const b1=b+1, bg=b+gw;
  sVX = vx[b]*w00+vx[b1]*w10+vx[bg]*w01+vx[bg+1]*w11;
  sVY = vy[b]*w00+vy[b1]*w10+vy[bg]*w01+vy[bg+1]*w11;
  const pb=(j+1)*pw+i+1;
  sPSI = psi[pb]*w00+psi[pb+1]*w10+psi[pb+pw]*w01+psi[pb+pw+1]*w11;
}
```
✓ (gx ≤ gw−1 → i ≤ gw−2? if gx exactly gw−1, i=gw−1, b+1 = gw → out of vx row! guard: i1 = min(i+1, gw−1). Since fx would be 0 there, w10=w11=0 — but index still read (NaN risk? reading vx[gw·(j)+gw] = next row first element — not out of array bounds (except last row last col: b+1 ≤ gw·gh−1? last j=gh−1,i=gw−1: bg+1 = (gh)·gw + gw−1+1? bg = (gh−1+1)·gw + gw−1 = gh·gw + gw−1 > len−1!! Out of bounds read → undefined → NaN). Add clamps: i1 = i<gw-1?i+1:i; j1 similarly. Cheap ✓.

**Particle init:**
```js
function spawn(i, flashV){
  X[i]=Math.random()*W; Y[i]=Math.random()*H;
  PX[i]=X[i]; PY[i]=Y[i];
  const r=Math.random();
  SPD[i]=Math.pow(r,1.4)*1.6+0.55;
  if (Math.random()<0.06) SPD[i]*=2.7;
  if (Math.random()<0.12) CLS[i]=1; else CLS[i]=0;
  JIT[i]=(Math.random()-0.5)*0.11;
  LIFE[i]=Math.random()*20;
  MAXL[i]=8+Math.random()*16;
  FLASH[i]=flashV;
}
```
Wait CLS (thick) chance: 12% thick. Fine.

MAXL stored or fold into LIFE reset... need MAXL per particle; use Float32Array MAXL. Or simpler: LIFE[i] = MAXL[i] − ... on respawn set MAXL then LIFE=MAXL·(0.5+0.5rand). Keep both arrays.

**Physics frame:**
```js
const SPD_base = 44*sizeScale;
for (let i=0;i<active;i++){
  sample(X[i],Y[i]);
  let dx = sVX*SPD_base*SPD[i]*dt;
  let dy = sVY*SPD_base*SPD[i]*dt;
  const d2=dx*dx+dy*dy, mx=field.cell*0.8;
  if (d2>mx*mx){ const s=mx/Math.sqrt(d2); dx*=s; dy*=s; }
  PX[i]=X[i]; PY[i]=Y[i];
  let nx=X[i]+dx, ny=Y[i]+dy;
  let wrapped=false;
  if (nx<-2){nx+=W+4;wrapped=true;} else if (nx>W+2){nx-=W+4;wrapped=true;}
  if (ny<-2){ny+=H+4;wrapped=true;} else if (ny>H+2){ny-=H+4;wrapped=true;}
  X[i]=nx; Y[i]=ny;
  if (wrapped){ PX[i]=nx; PY[i]=ny; }
  LIFE[i]-=dt;
  if (LIFE[i]<=0){ spawn(i,0); }
  // wave
  if (waveOn){
    const ddx=nx-waveX, ddy=ny-waveY;
    if (ddx*ddx+ddy*ddy < waveR*waveR && LASTW[i]!==waveId){
      LASTW[i]=waveId;
      // reborn in wake
      let sx=0, sy=0, ok=false;
      for (let tr=0;tr<4;tr++){
        const a=Math.random()*TAU, dd=waveR - 4 - Math.random()*55;
        sx=waveX+Math.cos(a)*dd; sy=waveY+Math.sin(a)*dd;
        if (sx>4&&sx<W-4&&sy>4&&sy<H-4){ok=true;break;}
      }
      if(!ok){sx=clamp(sx,4,W-4);sy=clamp(sy,4,H-4);}
      X[i]=sx;Y[i]=sy;PX[i]=sx;PY[i]=sy;
      LIFE[i]=MAXL[i]; FLASH[i]=1;
    }
  }
  FLASH[i]-=dt*1.5; if (FLASH[i]<0)FLASH[i]=0;
  // bucket
  let u = sPSI*0.85+0.5 + JIT[i] + uBias;
  u = u<0?0:(u>1?1:u);
  BUCKET[i] = (u*(NB-1)+0.5)|0 + CLS[i]*NB;   // careful precedence — wrap parens
}
```
Wait psiN: sPSI∈[−1,1] → u base = sPSI·0.425+0.5 ∈ [0.075,0.925]. Fix: u = sPSI*0.425+0.5 + ...

Note spawn() uses Math.random — fine.

Wave check when particle exactly spawned naturally in front region — it'll get wave-reset same frame → flash; fine.

**Draw:**
```js
// counting sort
counts.fill(0);
for i: counts[BUCKET[i]]++
starts: prefix
cursor copy
for i: order[cursor[BUCKET[i]]++]=i

ctx.globalCompositeOperation='lighter';
ctx.lineWidth=1.0;
for (let b=0;b<NB;b++){
  const s=starts[b], e=s+counts[b];
  if(e===s)continue;
  ctx.strokeStyle=thinColors[b];
  ctx.beginPath();
  for(k=s;k<e;k++){const i=order[k]; ctx.moveTo(PX[i],PY[i]); ctx.lineTo(X[i],Y[i]);}
  ctx.stroke();
}
ctx.lineWidth=2.6;
for (let b=NB;b<NB*2;b++){ ... thickColors[b-NB] ... }
// flash
ctx.lineWidth=1.7; ctx.strokeStyle=flashColor;
ctx.beginPath();
for (i<active) if (FLASH[i]>0.15){ moveTo(PX[i],PY[i]); lineTo(X[i],Y[i]); }
ctx.stroke();
```

**uBias:**
```js
uBias = 0.1*Math.sin(t*0.1+1.7) + waveHue;
```
waveHue = 0.3*Math.sin(waveCount*2.399+0.7) — golden-angle-ish variety. Plus palette independent. Hmm — I said palette shift partly conveys evolution; uBias shifts color-structure mapping. Good.

**Wave update:**
```js
if (!waveOn && t>=nextWaveT && t>4) startWave(t);
if (waveOn){
  waveR += waveSpeed*dt;
  carve();
  if (waveR - waveTrail > waveMaxR){ waveOn=false; nextWaveT = t + 9 + Math.random()*7; waveCount++; waveHue=0.3*Math.sin(waveCount*2.4+0.7); }
}
startWave: origin random with margin? random anywhere: ox = W*(0.15+0.7rand), oy = H*(0.15+0.7rand); waveSpeed = Math.max(W,H)/5.2; waveId++; waveOn=true; waveR=0; waveTrail=95; waveMaxR = Math.hypot(W,H)+waveTrail+20; nextWaveT=Infinity;
```
Also waveHue update should happen at wave START (so during wave new colors draw) — set waveHue in startWave. ✓

**carve():**
```js
ctx.globalCompositeOperation='destination-out';
const rings=[[-78,26,0.05],[-50,24,0.10],[-26,22,0.16],[-8,18,0.22],[+4,10,0.10]];
for each [off, half, a]: rIn = max(0, waveR+off-half), rOut = waveR+off+half; if rOut<=0 continue; annulus fill with globalAlpha=a? use fillStyle rgba(0,0,0,a) — with destination-out only alpha counts. Use globalAlpha to vary.
```
Set ctx.globalAlpha per ring, fillStyle '#000', then restore globalAlpha=1.

Frame order: carve first, then fade fillRect (also destination-out), then lighter drawing.

Fade:
```js
ctx.globalCompositeOperation='destination-out';
let a=(0.045+(Math.random()-0.5)*0.02)*Math.min(3,dt*60);
if (waveOn) a*=1.35;
a=clamp(a,0.012,0.25);
ctx.globalAlpha=1; ctx.fillStyle='#000';
ctx.fillRect(0,0,W,H);
```

**Palette per frame:**
```js
function updateColors(t){
  const period=18, p=t/period;
  const fi=Math.floor(p), f=p-fi;
  const i=fi%4, i2=(i+1)%4;
  const HOLD=11/18, mix = f<=HOLD?0:smoothstep((f-HOLD)/(1-HOLD));
  for (b...){ u=(b+0.5)/NB; rampMix(PALS[i],PALS[i2],mix,u,tmpRGB); thin[b]='rgba(...,0.12)'; thick[b]='rgba(...,0.055)'; }
}
```
smoothstep(x)=x*x*(3-2x).

At t=0: pure Kiln ✓.

rampMix: stops even, N=6: seg = min(4, u*5|0), f2 = u*5−seg; c = lerp(A[seg],A[seg+1],f2) then lerp with B similarly by mix. Precompute PALS parsed to arrays [r,g,b] per stop.

**Frame skeleton:**
```js
let lastTs=0, frame=0;
function frameLoop(ts){
  requestAnimationFrame(frameLoop);
  if (!lastTs) lastTs=ts;
  let dt=(ts-lastTs)/1000; lastTs=ts;
  if (dt>0.05) dt=0.05; if (dt<=0) dt=0.001;
  tNow=ts/1000;
  // warmup field: on first frame, run update(tNow) immediately
  if (frame % 3 === 0) field.update(tNow*1 + 40); 
```
Hmm offset noise time so initial field isn't the "t=0" of noise — noise at t·0.085 small → fine either way; add +50 constant so lattice position arbitrary. Eh, coordinates already offset by constants. Skip.

uBias computed with tNow.

Adaptive perf:
```js
perfAcc+=dt (after tNow>3); perfN++;
if (perfN>=240){ const avg=perfAcc/perfN; if (avg>0.030 && active>2200){ active=(active*0.72)|0; } perfAcc=0;perfN=0; }
```
Cap reductions: allow it to keep rechecking; floor 2200 guard ✓.

**Init sequence:** resize(true /*first*/) → set canvas, ctx transform, field.resize, active = clamp(area/430, 2200, 6000) (compute for all MAXP arrays but active var), spawn all with flash 0.45, field.update(0), nextWaveT=12.5, waveCount=0.

Also updateColors needs W? no.

On resize (non-first): rescale particle positions: X[i]*=W/oldW etc. (also PX/PY), clamp, field.resize, active recalc? If window grew, active up? keep same active (perf measured); recompute target SPD_base with new sizeScale ✓. Clear happens; respawn flashes 0.5? Set all FLASH=0.6 for gentle rebirth. Cancel wave.

**Prevent zero-division / degenerate** small windows: min size clamp in resize (W=max(W,50)).

**Title:** `<title>Flowfield Nocturne</title>` or similar.

**Meta viewport** for mobile.

Double-check NB memory: nothing crazy.

One subtle thing: `ctx.moveTo`/`lineTo` with DPR transform — coordinates css px ✓.

Also `ctx.lineCap='butt'` default ✓.

Let me also double check the destination-out carve with globalAlpha: fillStyle '#000' alpha channel 1 × globalAlpha → src alpha = a; dst α' = α(1−a) ✓.

And 'lighter' ignores globalAlpha? No — globalAlpha multiplies src in all modes ✓ (we keep 1 during strokes since alpha is in strokeStyle).

Also initial canvas: fully transparent → body bg #07070a shows. Fade destination-out reduces α toward 0 ✓.

**Rechecking the "thousands of particles" & first-frame cost:** active = min(6000, max(2200, area/430)). 1920×1080 → 2,073,600/430 ≈ 4822 ✓. 4K (3840×2160): 19.3M/430 = 44,900 → cap 6000. Should the cap scale with area? Density on 4K would be sparse-ish but trails accumulate; bump cap to 7000 and MAXP=7000. With adaptive reduction in place, set cap 7000. Also maybe cap by area/380 with max 7000: 1920×1080→5456. ok: active = clamp(round(area/400), 2000, 7000).

Frame cost estimate at 5400 particles: physics loop with sample() ~ maybe 1.5ms; counting sort ~0.3ms; stroke ~2–4ms; field update 6ms/3frames=2ms amortized; fade 0.3ms. Total ~6–8ms ✓.

**Noise time offsets per octave inside fbm** add cost of additions only ✓.

One thing: fbm's noise3 calls with freq f=2.03^o and offsets o*17.31 — offsets applied pre-frequency; fine decorrelation.

Potential warp magnitudes: wx,wy ∈ ~[−0.9,0.9]; ×1.85 → displacement ±1.7 lattice units ✓ dramatic warping.

**Check psi→color distribution:** fbm 3-octave range roughly [−0.8,0.8] with concentration near 0 → u concentrated mid-ramp → mostly mid colors, extremes rare — actually good (bright/dark anchors rare → precious). u = psi*0.425+0.5 maps ±0.8 → [0.16,0.84] ✓.

**Flash stroke color**: 'rgba(255,242,214,0.42)'.

Now, DPR & lineWidth: lineWidth 1.0 css at DPR 1.75 → 1.75 device px. Thin alpha 0.12 each frame per particle — buildup speed: each pixel crossed by a particle gets ~ +0.12·color per crossing... trails accumulate over many crossings → after seconds, filaments reach saturation then fade equilibrium 0.045/frame ≈ equilibrium when add rate = fade rate. Should look right; these constants are in the right ballpark from experience with such pieces.

Also add `ctx.globalCompositeOperation` reset at loop start each phase explicitly — done.

**Resize listener** with small debounce (e.g., 150ms) to avoid thrash during drag-resize? Dragging resize continuously clearing canvas is OK actually; but field realloc each event is heavy → debounce 120ms. Also handle initial `load` — script at end of body, run immediately.

Also listen to `document.visibilitychange`? not needed.

Let me also add a tiny "grain"? No — purity.

Edge: iOS Safari canvas max area — 585×1266×... at DPR capped 1.75: 390·1.75=682×1477 fine.

Now let me also handle `active` reduction allocating `order` etc. at MAXP ✓ (fixed arrays at MAXP).

Also: don't forget `ctx.setTransform(DPR,0,0,DPR,0,0)` after each canvas.width set (state resets on resize ✓ set it there).

Potential improvement — **lineJoin?** n/a separate segments.

**Also**: the very first field.update before first frame so particles don't sample zeros: call field.update(0) in init ✓. And colors update once.

Alright — also think about whether wave carving + continuous fade interacts with `lighter` stroke alpha: after carve region α≈0 → strokes immediately add on black ✓ crisp new filaments in wake ✓.

What about particles **inside** wave circle at wave birth (r=0 → origin point)? At start waveR=0; first frames carve tiny circle; particles near origin reset when dist<r — starts from origin outward ✓.

Let me also give the wave a **second harmonic**: occasionally two origins? Keep one — restraint.

Now, is there any chance the composition reads as "one big saturated blob"? Curl flow + fade equilibrium → filament etching, generally self-regulating (concentration follows |∇ψ| ridges which move as field morphs). Fine.

Also I want the **first 30s** to definitely include a wave → nextWaveT init 12.5, duration ~ (diag+trail)/speed: speed = max(W,H)/5.2 → for 1920: 369 px/s; diag 2203+115 = 2318/369 ≈ 6.3s → ends ~18.8s. Second wave at nextWaveT = 18.8+9..16 → 28–35s — might miss 30s. Tighten interval: 8 + rand·5 → second at ~27–30s ✓ borderline; make first wave 11.5s, interval 7.5+rand·4.5 → second ≈ 26.5–31.5. Hmm. Alternatively speed up waves: speed = max(W,H)/4.5 → first ends 17.6; interval 7–12 → second 24.6–29.6 ✓ within window mostly. Use interval = 7.5+rand·4 (7.5–11.5) → second 25–29 ✓. Long-term cadence every ~8–14s fine ("occasional"). Good: WAVE0=11.5, interval 7.5+4rand, speed max(W,H)/4.6.

Wait — also think: is a full-screen sweep every ~10s too erasive? The band only erases its ~100px annulus per pass; rest persists. Between waves the piece accumulates ~10s of new etching in new palette. Feels right.

Also during a wave, spawned-in-wake particles at flash → wake ring ~ thousands along ring width 60px — ring perimeter ~ up to 6000px, particles within 60px band ≈ 5400·(bandArea/screenArea) — screen 2M px, band ~ 6000·55=330k → ~800 particles flashing along ring → visible shimmering frontier ✓ lovely.

**Writing style of explanation after code:** brief, first person, cover noise impl, curl field, palette, waves, perf. Keep concise.

Let me now also decide the initial flash: spawn with FLASH 0.5 — entire canvas shimmering softly at t=0 then settling — nice "ignition".

One more check — `sample()` clamping i1/j1:
```js
const i1 = i<gw1? i+1 : i; // gw1=gw-1
const j1 = j<gh1? j+1 : j;
const b=j*gw+i, b1=j*gw+i1, bg=j1*gw+i, bg1=j1*gw+i1;
```
✓ rewrite accordingly.

`psi` sample: padded p indices: pi=i+1, pj=j+1, using i1/j1 similarly: p00=(pj)*pw+pi etc. ✓

Physics loop temp globals: sVX etc. module-level `let` ✓ (JIT will handle fine).

**Bucket precedence fix:** BUCKET[i] = ((u*(NB-1)+0.5)|0) + CLS[i]*NB;

**Colors arrays:** thinCol=new Array(NB), thickCol — fill each frame.

Also — rescale on resize: ratioX = W/oldW etc.; for i<active: X*=rx; Y*=ry; PX=X;PY=Y; (drop prev) — also flash small.

I think there's one more aesthetic consideration: pure lineWidth 1.0 might be too hairline on a 4K; scale lineWidth slightly with sizeScale: lw = 1.0·clamp(sizeScale,0.85,1.5). Sure: set each frame before passes: thin lw = LWB, thick = LWB·2.6, flash = LWB·1.7.

sizeScale = clamp(Math.sqrt(W*H/(1920*1080)), 0.62, 1.8); SPD_base = 44·sizeScale... wait speed scaling: on huge screens you want faster px/s proportional-ish; sqrt scaling ok.

Also field wavelength uses min(w,h)·0.36 — on ultrawide, min dimension governs ✓.

I believe the design is complete. Let me write the final file carefully, watching for typos, since it must run first try.

Also remember: no external anything ✓; single file ✓; starts automatically ✓.

Draft the full code mentally once more for bugs:

- `mulberry32(seed)` standard.
- Perlin `noise3` — check PERM length 512 and index math: A=PERM[X]+Y (X,Y ≤255) → ≤510; PERM[A] valid (≤511 since A ≤ 510) ✓; AA=PERM[A]+Z ≤ 255+255=510; PERM[AA+1] ≤ PERM[511] ✓ good.
- grad() returns up to |x|+|y| ~ ≤ ~1.4? values fine; noise3 output ∈ ~[−1,1]·(1/√2?) whatever — fbm normalized anyway.

Also careful: in `noise3`, after `X &= 255`, PERM[X+1] with X=255 → PERM[256] valid (dup table) ✓; B=PERM[X+1]+Y ≤ 255+255 ✓.

- Wave carve arcs: need rOut>rIn≥0; if rIn===rOut skip.

- Order of operations in loop when wave just completed: waveOn false → nextWaveT set ✓.

- `active` used in loops; MAXP arrays sized 7000.

Let me also make sure I don't allocate per frame except the ~52 color strings — fine.

Counting sort arrays: counts=Int32Array(NB*2), starts=Int32Array(NB*2), cursor=Int32Array(NB*2) — fill each frame.

Also draw only buckets with counts — using starts/counts ✓.

Final check on **`u` bias waveHue at t=0**: waveCount=0 → waveHue=0.3·sin(0.7)≈0.19 — slight initial offset fine.

Explanation text after the block: concise (~10 lines). Also code comments in English (user language English ✓).

Let me write it all out now.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Drift — a generative flow-field nocturne</title>
<style>
  html, body { margin:0; padding:0; width:100%; height:100%; overflow:hidden; background:#07070a; }
  canvas { display:block; width:100vw; height:100vh; }
</style>
</head>
<body>
<canvas id="view"></canvas>
<script>
'use strict';

/* ============================== utilities ============================== */
const TAU = Math.PI * 2;
const clamp = (v, a, b) => v < a ? a : (v > b ? b : v);
const smooth = x => x * x * (3 - 2 * x);

function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
```

then noise, palettes, etc. Let me assemble everything and double check as I go. I'll write the final answer now with the complete file, then a short explanation.

One more consideration on fade alpha values: 0.045/frame → trail half-life ≈ ln2/0.045 ≈ 15 frames ≈ 0.26s?? That's way too short — trails would vanish immediately! Wait: destination-out multiplies alpha by (1−0.045) per frame → after 1s (60 frames) α×0.955^60 ≈ 0.063 — trail visible ~2–3s. Half-life ~0.26s means a stroke loses half brightness in a quarter second — but particles continuously re-trace similar paths, so the *image* is a time-exposure with ~1–2s memory... For "long-exposure buildup into intricate composition", I want longer memory: fade 0.02/frame → half-life 0.57s, 1s → 0.30 remaining; visible ~4–6s. Hmm, but stroke alpha 0.12 with passes every frame along same filament: buildup to equilibrium: per-frame gain where N strokes overlap pixel ≈ N·0.12·local; equilibrium at 0.02 fade needs local gain 0.02 → N ≈ 0.17 strokes/frame on that pixel — i.e., a filament traced by one particle every 6 frames maintains moderate brightness. With 5400 particles on 2M pixels, each pixel crossed rarely... density: each particle draws ~1px² × length ~0.8px per frame → total painted ≈ 4300 px²/frame over 2M px² → 0.2% coverage/frame. A given filament pixel retraced every ~... particles follow coherent paths so their segments overlap path pixels repeatedly — along a filament of, say, 300 px length traced by ~10 nearby particles → each path pixel gets ~10 hits/0.8px... ~12 hits/frame? No: 10 particles each contributing 0.8px per frame along the same path → a path pixel receives ~10·(0.8/300)... eh. Realistically flow-field art uses fade 0.01–0.03 and alpha 0.05–0.3 and looks great with buildup over seconds. I'll set fade base 0.030 (jitter ±0.012), stroke thin alpha 0.10, thick 0.05. Equilibrium brightness = gain/0.03. During recording, image rich by ~8s ✓, waves prevent saturation ✓. Also stuck-pixel threshold: α·(1−0.03)=α·0.97: stuck when round(α·0.97)==α → α·0.03<0.5 → α<16.7 → residue up to 16/255 ≈ 6% — jitter ±0.012 (0.018–0.042 range) breaks locks (different multipliers each frame) mostly. Waves sweep everything anyway. OK.

Flash fade dt·1.5 → ~0.67s ✓.

Also maybe increase alpha during first seconds (dry-brush reveal)? Skip — buildup is the show.

Let me also reconsider particle step speed 44·sizeScale: with dt 1/60 → 0.73px/frame typical — segments sub-pixel; drawing sub-pixel segments with additive alpha gives soft etching — good. Fast particles (×2.7 spd ×~1.2 mul) ≈ 2.4px/frame visible streaks ✓.

I'm fairly confident in the overall tuning; these pieces are robust to ±50% in constants.

Potential worry: **field refresh every 3rd frame causes direction pop** when grid updates (bilinear between frames of different lattice). The field changes slowly (Δz per refresh ≈ 0.085·0.05 ≈ 0.004 lattice ≪1) → direction delta tiny ✓ smooth.

Also **the initial frame before first field.update**: call field.update(0) during init ✓.

Final assembly — write code cleanly with section comments. Also add a `resize` debounce:

```js
let resizeTimer=0;
window.addEventListener('resize', () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(doResize, 120);
});
```

doResize reads innerWidth/innerHeight.

Also make canvas CSS-driven and read clientWidth? Use window.innerWidth/Height directly — canvas is 100vw/100vh; equivalent minus scrollbar (none). ✓

Also `image-rendering` default ✓.

Alright, also small detail: at init `lastTs=0` then first ts maybe large (rAF timestamp epoch) — handled by `if(!lastTs) lastTs=ts`.

tNow = ts/1000 absolute — palettes/noise use absolute time fine.

Write final HTML now. I'll keep code ~330 lines with comments.

Also double check ramp even spacing: stops count 6, u*5 → seg 0..4 (seg=(u*5)|0 could hit 5 at u=1 → clamp: if(seg>4){seg=4;f=1}).

Colors to string: `rgba(${r|0},${g|0},${b|0},0.10)`.

Draw thick color alpha 0.05, thin 0.10.

Flash color warm white.

Also let me include a subtle touch: **global alpha pulsation?** no. Restraint.

Also — set `ctx.lineCap='round'`? For sub-pixel segments, round caps make dots slightly rounder/softer; cost: path with many subpaths — round caps add geometry. With ~5k segments might be OK but butt is safer. Butt.

Explanation after code: mention hand-built improved-Perlin 3D noise + fBm + domain warping, curl of potential → divergence-free flow, precomputed field grid, additive batched strokes, destination-out fading for hue-preserving decay, curated crossfading palettes tied to the potential for structural color, reset waves carving annuli + particle rebirth wake, adaptive quality, resize handling. Concise.

Let me write out everything, carefully proofreading variable names.

Extra proof for counting sort draw: after physics loop computed BUCKET for all i (0..active). counts fill 0 sized NB*2 ✓.

Code for starts:
```js
let sum=0;
for (let b=0;b<NB2;b++){ starts[b]=sum; sum+=counts[b]; }
cursor.set(starts);
for (let i=0;i<active;i++){ order[cursor[BUCKET[i]]++]=i; }
```

Draw thin: b in [0,NB), color thinCol[b]; thick: b in [NB,NB2), color thickCol[b-NB].

flash pass loop i<active check FLASH[i]>0.12.

Good. Also clamp u before bucket: u computed then clamped [0,1].

waveTrail=95; ring offsets relative front r: [−80,±26,0.05],[−52,±24,0.10],[−27,±22,0.17],[−8,±16,0.24],[+4,±9,0.10]. rIn = r+off−half; rOut = r+off+half. Skip if rOut<=0.

Also for very fast waves the per-frame band movement ~ speed/60 = max(W,H)/4.6/60 ≈ 7px @1920 → overlap great.

waveSpeed recompute on resize? wave canceled on resize — fine.

nextWaveT init = 11.5.

Also guard: start wave only if W,H > 0.

sizeScale & SPD_base recomputed in doResize; SPD_base module var used in physics.

DPR: min(devicePixelRatio||1, 1.75). On doResize recompute (covers monitor moves).

I also want `active` init: `active = Math.round(clamp(W*H/400, 2000, 7000));` MAXP=7000 ✓.

For the initial ignition: in initSpawn set FLASH=0.5.

Everything set. Also wrap entire script in IIFE? Top-level fine.

Also — colorU uses sPSI from last sample; after respawn (wave or life) within same iteration, sPSI corresponds to old position — negligible.

Now also confirm: `sample()` called before respawn uses old X,Y — fine.

Also potential NaN: field arrays initialized zero before first update? update called in init ✓.

Write final answer. Also double-check I never use emoji, no alert, etc. ✓ No external fonts ✓.

Let me write the complete code text now, mentally compiling:

Also `noise3` heavy usage inside field.update — ensure local aliasing for speed: `const P=PERM;` inside noise3 — module var lookups fine with JIT.

Potential improvement for warp noise time params — as set.

Edge: fbm offsets — add different constant offsets per octave: `(o*37.7)` etc. ✓

Final structural pass of the script:

1. utils (TAU, clamp, smooth, mulberry32)
2. noise (PERM, fade, grad, noise3, fbm)
3. palettes (hex → parsed, NB, rampMix, color state arrays)
4. canvas & state (ctx, W,H,DPR, sizeScale, SPD_base, active)
5. particle arrays
6. field object
7. wave state + functions
8. spawn/init/resize
9. frame loop
10. listeners + boot

Counting NB2 = NB*2.

Also make sure thick bucket assignment: CLS[i]*NB.

I'm also going to double check one perf hazard: `ctx.stroke()` with 28–56 separate paths — each beginPath accumulates; number of moveTo ~ up to active split. OK.

And GC pressure: color strings per frame (~52) — trivial.

Now write it.

Also — do I want a slight extra: slow ambient rotation of entire velocity field? Skip.

One last review of visual hierarchy: dominant impression = fine luminous filaments etching evolving topographic swirls on black; accent = periodic erasing front with sparkling wake; color story = curated ramps crossfading. That's a coherent single idea. Ship it.

For the explanation: first person, brief sections. Done — write final.