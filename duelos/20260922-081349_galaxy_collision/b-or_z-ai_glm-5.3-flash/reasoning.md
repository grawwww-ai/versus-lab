Let me design this carefully. This is a big task: two spiral galaxies colliding with ~40,000+ stars, GPU physics or cheap approximation, tidal tails and bridges, orbiting camera, starfield background, time label in Myr, all in one HTML file with three.js r186 as ES module.

Key design decisions:

**Physics approach**: The classic cheap way to get beautiful tidal tails is a restricted N-body approach: the two galactic cores are the only massive bodies (2-body problem integrated with real gravity), and each star is a massless test particle attracted to both cores. This is actually how the famous Toomre & Toomre (1972) simulations were done, and it produces gorgeous tidal tails and bridges. I could compute this on CPU each frame — 40,000 stars × 2 cores = 80,000 force evaluations, trivial in JS. But the requirement says "run the physics on the GPU or with a cheap approximation so it stays smooth". A restricted 3-body test-particle model is exactly that cheap approximation. But GPU physics would be even better and more impressive. Options:

1. **CPU simulation** with typed arrays, updating a BufferAttribute each frame. 40k particles × simple 2-body attraction is ~fine at 60fps in JS. Simple and reliable.

2. **GPU simulation** via FBO ping-pong: store positions and velocities in float textures, run a fragment shader with gravity toward two point masses. This is elegant and stays smooth even with 100k+ particles. In three.js, I'd need to render to render targets, using full-screen quads and shader materials. This is doable without addons — I'll write my own minimal ping-pong simulation: two RTs for position, two for velocity, an UpdateMaterial. Points rendered from the position texture by computing UV from gl_VertexID... Actually in WebGL2 with GLSL ES 3.0 I can use gl_VertexID to do texture-free geometry: place points directly by indexing the position texture in the vertex shader, with a BufferGeometry carrying only a per-vertex reference (or even zero-attribute draw). Three.js r186 supports WebGL2 by default. Using gl_VertexID requires an attribute-less draw which three.js can struggle with — three.js typically requires at least one attribute to compute draw count. The standard trick: create a dummy attribute with reference UVs per particle (2 floats), then vertex shader does `texture(posTex, uv)`. That's clean and well-supported.

GPU FBO physics plan:
- N particles per galaxy (e.g., 2 × 24,000 = 48,000; texture sizes: use W×H grids like 256×96 per... better: one texture for all particles, say 512×128 = 65,536 slots, use 2×24k = 48k). Let me pick texture 512 × 128 = 65536. Actually simpler: width 512, height 128.
- DataTextures: RGBA float. Position texture: xyz + w = particle "core index" or seed/flag. Velocity texture: xyz + w unused.
- Simulation step (fragment shader, per full-screen quad over the sim texture):
  - read pos, vel
  - gravity from core A and core B (positions passed as uniforms, integrated on CPU — the two cores form a 2-body problem which I integrate in JS with high accuracy; cheap)
  - softening epsilon
  - leapfrog/Euler integration with dt uniform.
  - Optionally a bit of initial in-plane rotation maintained? No external forces needed; test particles in an initially circular orbit around a point mass will keep orbiting (Kepler), giving spiral-ish motion; real galaxies need a flatter rotation curve to hold spiral arms. With point-mass gravity, inner particles orbit faster (ω ∝ r^-3/2) which causes strong differential rotation — the arms will wind up a lot. Since the galaxy is built as a spiral pattern at t=0, differential winding under point-mass potential will tighten the arms over time. Over the 30s window this might make the arms blur into rings. To keep arms visible, I could give the rotation curve a flat-ish profile: v = v0 * (r / (r + rc))^0.5-ish... Let me think.

  For a test particle to remain on a nice spiral over tens of seconds of sim time, the angular speed should depend mildly on radius. A flat rotation curve (v const) gives Ω ∝ 1/r, still differential but much less winding than Kepler. Actually a log potential gives flat v. I don't need self-consistency: I just directly prescribe initial velocities from a chosen rotation curve v_c(r) = Vflat * r / sqrt(r² + rc²) blend... Simplest: v = Vflat * (r/(r+rc))^? Hmm. Let me use v_c(r) = Vflat * r / (r + a)^{?}... 

  Common trick: v_c(r) = Vmax * r / sqrt(r² + rc²)? That's nearly flat beyond rc, rising inside. Then Ω = v/r decreases with r → differential rotation, arms wind but slowly. Since the encounter happens fast (cores merge/pass within a few seconds), initial spiral arms get tidally distorted anyway — which is what we want. The winding mainly matters in the first seconds before the galaxies interact strongly. I'll start the galaxies well separated with an approach that takes ~4–6 seconds before first strong interaction, so some winding will occur. With a mildly falling rotation curve the winding is graceful (like real galaxies' spiral winding). I'll also spawn the stars directly ON the spiral arms (logarithmic spirals with scatter), so at t=0 they look like clean spiral galaxies; slight winding just looks natural.

  Alternative to keep arms crisp longer: give each star its own angular speed consistent with the potential I actually use in the sim. If sim gravity is a point mass (Kepler), then to be self-consistent, circular velocity is Keplerian and arms wind fast. To avoid fast winding I can use a softened point potential in the sim (like Plummer): φ = -GM/√(r²+ε²). Circular velocity v² = GM r² / (r²+ε²)^{3/2}. For r >> ε, Keplerian. Hmm.

  Actually the arms winding under Kepler is quite fast: Ω ∝ r^{-1.5}; ratio inner/outer over factor 4 radius is 8×. Over 6 seconds that's a lot of wrap. But you know, in these collision visualizations, the initial disk quickly gets disturbed anyway. Also I can reduce pre-interaction time: start galaxies at moderate distance with inbound velocity so first pericenter within ~3–4 seconds, then tails develop through the rest.

  Better idea: use two mass components per galaxy in the shader — a compact bulge mass plus an extended halo mass (two Plummer spheres per galaxy, different softening). That gives a rising-then-flat rotation curve, less inner differential winding, and keeps stars more coherent. Each star feels: bulgeA, haloA, bulgeB, haloB → 4 gravity terms. Cheap in shader. Cores themselves integrated on CPU with just the combined potential of the other galaxy treated as point mass (2-body). During merger the cores pass close and can merge (damped) — I'll add a dynamical-friction-ish drag when cores are close so they eventually coalesce, which reads nicely as a merger remnant.

  Actually, to make the final merger look good: after pericenter passages, apply drag force on relative velocity ∝ exp(-d/d0). Then cores sink and orbit tightly, forming a bright combined core. That's cinematic.

- Tidal features: purely emergent from restricted 3-body — tails and bridges appear naturally. 

**Rendering**:
- THREE.Points with additive blending, custom ShaderMaterial. Size attenuation, per-star size and color. Color: warm yellow at core → blue-white in arms. I'll compute color from initial radius: inner = warm (1.0, 0.85, 0.6), outer = blue-white (0.7, 0.8, 1.0), plus some randomness and a few bright "O-stars" sprinkled in arms (slightly larger, bluer). Per-particle size attribute.
- Also render the two cores as bright glowing sprites (larger additive points or textured sprites made procedurally — a canvas-generated radial gradient texture... wait, no images allowed? "no external resources... or images" — external images; a runtime-generated canvas texture is fine, it's not external. But actually I can also just use a shader-based soft point sprite: in fragment shader, dist from gl_PointCoord center, gaussian falloff. No texture needed. Good.)
- Starfield background: a separate far-away static Points sphere (~2000 stars), subtle, maybe slight twinkle not needed. Dark background (black / very dark blue). Use fog? no.
- Camera: slow orbit — I'll move camera on an inclined circular orbit around the system barycenter, with slight drift in radius; lookAt center (barycenter or midpoint drifting toward merged core). Requirement says "slowly orbiting camera that frames the whole event" and also "Starts automatically, no interaction needed". I can still add OrbitControls but auto-rotating; but "no interaction needed" just means it starts by itself. To be safe and cinematic, I'll do a scripted camera: slowly orbiting with changing angle/radius over time, maybe easing closer during merger. I could also allow OrbitControls? If I use OrbitControls with autoRotate, user can drag too. But scripted camera radius changes conflict with controls. Simplest robust: custom scripted orbit (no controls). The requirement mentions OrbitControls as an example only. I'll do scripted camera — guaranteed good framing for recording.

Hmm, but interactive? "no interaction needed" — scripted is fine.

**Time label**: simulated time in Myr. I'll define a mapping: sim seconds → Myr. Choose scale so encounter spans e.g. 0–600 Myr over the first ~30s real time (20 Myr per real second is plausible for galaxy interactions). Label top-left small, monospace-ish scientific look: "T + 213 Myr". Also maybe pericenter indicator? Keep it simple: time + maybe "PHASE: FIRST PASSAGE / TIDAL BRIDGES / COALESCENCE". A small phase label adds cinematic science flavor. Nice touch but keep minimal.

**Timeline design** (real seconds, at ~60fps):
- dt sim per frame: I'll run fixed physics dt with substeps for stability. Let sim speed be constant in real time: simTime += speed * realDt.
- Initial separation: let's set units. Use arbitrary units: galaxy disk radius ~ 10 units. Core mass chosen so orbital speeds look nice. I'll tune numerically: choose G*M_bulge such that circular speed at r=5 is v=? For visual pacing: distance between galaxies ~ 90 units initially, approach speed such that first pericenter at t≈5s real. If sim speed S (sim units per real second) — easier: work directly in sim units and pick dt per frame = realDt * TIME_SCALE. Let TIME_SCALE = 12 sim-units per real second... Let me define numbers concretely.

Let disk radius R=10 (stars out to ~10–12, tails extend further). Bulge mass parameter: GM_b = 60 (so v_circ at r=3: sqrt(60*9/(9+ε²)^{...}) with Plummer ε=1.2: v² = GM r²/(r²+ε²)^{3/2} = 60*9/(9+2.07)^{1.5}=540/(11.07^1.5=36.8)=14.7 → v≈3.83. Orbital period at r=3: 2π*3/3.83 ≈ 4.9 time units. Hmm I want the disk rotation to be visibly moving — period of outer stars (r=10): v² = 60*100/(101)^{1.5}=6000/1015=5.9→v=2.43; period=2π*10/2.43≈25.9 time units. With halo added, outer v higher.

Time mapping: if 1 real second = 3 time units, outer disk does a revolution in ~8.6 real seconds — nice visible rotation. Then 30 real seconds = 90 time units. Galaxy encounter: separation 90 → with relative speed ~9/time unit... first passage after ~8 time units ≈ 2.7 s real. Maybe a bit fast; I'd like ~4–5 s of approach. Set initial separation 110 and approach radial speed 8 → 12 time units to close to ~25 (accounting acceleration). Hmm gravity accelerates. Let me just integrate cores on CPU at runtime with chosen initial conditions and tune constants mentally; but I can't test... I need robust behavior. Let me carefully pick a proven-like configuration.

Actually, let me think in terms of a two-body hyperbolic/parabolic encounter. Masses M1 = M2 (equal galaxies). Each galaxy's "active mass" for the other core's motion: use total GM_gal = GM_bulge + GM_halo. Let GM_gal = 400 (bulge 120, halo 280?). Hmm let me choose scale-free numbers and compute.

Let me define:
- Bulge: GM=90, softening εb=1.6
- Halo: GM=310, softening εh=9.0 (extended)
- Total per galaxy GM=400.

Disk stars: radius 2 → 12. Circular speed with combined bulge+halo Plummer potentials: v² = Σ GM_i r² / (r²+ε_i²)^{3/2}.
At r=2: bulge: 90*4/(4+2.56)^{1.5}=360/(6.56^1.5=16.8)=21.4; halo: 310*4/(4+81)^{1.5}=1240/785=1.58; total v²≈23 → v≈4.8.
At r=6: bulge: 90*36/(36+2.56)^1.5 = 3240/(38.56^1.5=239)=13.6; halo: 310*36/(36+81)^1.5=11160/(117^1.5=1265)=8.82; total 22.4 → v≈4.73.
At r=10: bulge: 90*100/(100+2.56)^1.5=9000/(102.56^1.5=1039)=8.66; halo: 310*100/(100+81)^1.5=31000/(181^1.5=2437)=12.7; total 21.4→v≈4.62.
At r=12: bulge 90*144/(146.6)^1.5=12960/(1774)=7.3; halo 310*144/(225)^1.5=44640/(3375)=13.2; total 20.5 → v=4.53.

Beautiful — nearly flat rotation curve v≈4.6–4.8 across the disk. That's a proper flat curve, so spiral arms will wind slowly and coherently. 

Orbital periods: r=3: compute v at 3: bulge 90*9/(9+2.56)^1.5=810/(11.56^1.5=39.3)=20.6; halo 310*9/(90)^1.5=2790/854=3.27; v²=23.9→v=4.89; period=2π*3/4.89=3.85.
r=10: period=2π*10/4.62=13.6.
r=12: period=2π*12/4.53=16.6.

Differential ratio inner/outer Ω: (4.89/3)/(4.53/12)=1.63/0.377=4.3. Over 10 time units, inner stars sweep ~2.5 revolutions, outer ~0.6 — arms wind substantially in 10 time units but that's fine since interaction begins then.

Core-core orbit: relative motion of two point masses GM_total_attracting = 800 (each feels other's full 400; relative acceleration = -G(M1+M2) r̂/r² = -800/r², but softened when close? For core-core integration I'll use the softened mutual potential with combined softening (ε ≈ 3) so close passes don't blow up, plus drag for merger.

Initial: separation D0 = 120, approaching nearly parabolically. Parabolic relative speed at separation r: v_par = sqrt(2*800/r). At r=120: sqrt(1600/120)=3.65. If I start with speed slightly less than parabolic (bound orbit, e=high eccentricity), the cores will fall in, whip around, and come back — multiple passages leading to merger with drag. That's the classic merger dance. Let me set initial relative speed ~0.8 * v_par = 2.9, mostly radial with small tangential component to get angular momentum → pericenter maybe 8–12 (close pass through disks → dramatic tails).

Estimate first pericenter time: falling from 120 with average speed ~4–5 (accelerating from 2.9 to pericenter speed ~ sqrt(2*800/10)≈12.6): rough average 4.5 → time ≈ (120−10)/4.5 ≈ 24 time units?? That's too long. Hmm wait — acceleration grows: a=800/r². At r=120: 0.055. At r=60: 0.22. At r=30: 0.9. Average accel ~0.3 → Δv over 100 distance... v² increases by 2∫a dr = 2*800*(1/10 − 1/120) ≈ 1600*0.075=120 → wait v² = v0² + 2∫800 dr/r² = v0² + 1600(1/r_p − 1/r0)... let me redo: energy: v²/2 − 800/r = const. v0²=2.9²=8.4 at r=120 → E = 4.2 − 6.67 = −2.47. At r=10: v²/2 = E + 80 = 77.5 → v=12.45. OK.

Time to fall: use approximated two-body formula. For radial-ish fall... time from r0=120 to r_p=10 with E=−2.47, L small. Hmm, radial infall time from rest at r_max where E=−800/r_max → r_max = 800/2.47=324. Radial fall time from 324 to 10 ≈ (π/2)*(r_max^{3/2})/sqrt(2*800) * (something)... Free-fall time to center from r_max: t = (π/2) * r_max^{3/2} / sqrt(2 GM) = 1.5708 * 324^1.5 / 40 = 1.5708*5832/40 = 229. Time from 324 to 120: fraction... using t(r) = sqrt(r_max³/2GM) * (acos(sqrt(r/r_max)) + sqrt((r/r_max)(1−r/r_max))). Let x=r/r_max. At r=120: x=0.37: acos(0.608)=0.916; sqrt(0.37*0.63)=0.483; sum=1.399. At r=10: x=0.0309: acos(0.1757)=1.394; sqrt(0.0309*0.969)=0.173; sum=1.567. Δt = sqrt(324³/1600)*(1.567−1.399) = sqrt(34,012,224/1600=21258)=145.8*0.168=24.5. Yeah ~24 time units for first pericenter. Too slow if 3 time units/sec → 8 real seconds of approach. Actually... hmm, is 8 s of approach bad? The requirement: "everything important within the first 30 seconds". Approach (8s) + first passage + tails (10s) + merger (12s) = 30s. That could work but the approach should already show galaxies growing, rotating. Actually a bit slow-burn is cinematic, but risky — I want first passage by ~6–7s. Options: increase sim time scale to 4/s → 6s approach. Outer disk period 13.6–16.6 time units → at 4/s that's 3.4–4.1 s per disk revolution — nice and visible. 30 s = 120 time units. Merger timescale with drag: after first passage, cores on eccentric orbit with apocenter maybe ~60–80; period ~ 2π sqrt(a³/800): a=40 → 2π*sqrt(64000/800=80)=2π*8.94=56 time units — too long! With drag applied strongly, they'll decay in 1–2 orbits. I need drag tuned so second passage happens ~15–20 time units after first, and coalescence by ~60–80 time units total (≈15–20 real seconds at 4/s). Hmm, real mergers take a few passages; for cinema I'll compress with strong drag near close approach. It's an approximation, fine.

Alternative: make initial orbit more bound (v0 = 0.7*v_par) → r_max = 800/(E) with E = v0²/2 − 800/120: v0=2.56, v0²=6.55, E=3.27−6.67=−3.39 → r_max=236. Fall time from 236: sqrt(236³/1600)=sqrt(13.1e6/1600=8190)=90.5; t(120): x=0.508: acos(0.713)=0.777; sqrt(0.508*0.492)=0.5; sum 1.277; t(10): 1.567. Δ=90.5*0.29=26.2. Not much better (fall time weakly depends). The big lever is r_max (i.e., total energy). To fall faster, start closer OR give more speed... no—more speed → larger r_max→longer? If unbound (positive E), the galaxies pass once and escape — unless drag captures them. Parabolic-ish with slight positive energy + drag capture on first passage is actually the standard fast-merger cinematic setup: first passage happens when they've closed from 120, and drag at pericenter removes enough energy to bind them. But if E>0 and drag only at pericenter, apocenter after capture is determined; can still be long.

Better: reduce initial separation to ~70–80 and set disks radius 10 — galaxies start partially framed, approach visible, first pericenter ~15 time units ≈ 4 s at 4/s. With D0=80: E = v0²/2 − 800/80 = v0²/2 − 10. Choose v0 = 3.2 (parabolic at 80 = sqrt(20)=4.47; ratio 0.72) → E = 5.12 − 10 = −4.88 → r_max = 164. Fall time sqrt(164³/1600) = sqrt(4.41e6/1600=2756)=52.5; t(80): x=0.488: acos(0.698)=0.795; sqrt(.488*.512)=0.5; sum=1.295; t(pericenter 10): 1.567 → Δ=52.5*0.272=14.3 time units ≈ 3.6 s real. 

But wait — tangential momentum: with pericenter ~10 and L: v_t0 at r=80 → L = 80*v_t0. At pericenter: v_p = sqrt(2*(E + 800/10)) = sqrt(2*(−4.88+80))=sqrt(150.2)=12.26. L = r_p * v_p → r_p = 80*v_t0/12.26. For r_p=10: v_t0 = 1.53. Then radial v0 = sqrt(3.2² − 1.53²) = sqrt(10.24−2.34)=2.81. Good: mostly infalling with a bit of swirl → prograde encounter gives classic tails.

Second passage: after first passage, apocenter: at apocenter v is small; E=−4.88 (energy conserved between passages) → r_a = 800/4.88 ≈ 164 (if v_a≈0; with some v_a, a bit less). Orbit period a=(r_a+r_p)/2=(164+10)/2=87 → P=2π*sqrt(87³/800)=2π*sqrt(824,000/800=1030)=2π*32.1=201. Way too long — must rely on drag to shrink quickly. Drag: F_drag = −k * v_rel * exp(−r/λ) applied to relative motion, with λ ~ 8, k chosen so each pericenter passage removes large fraction of orbital energy. During passage, v_rel ~ 12 near r=10; time near pericenter ~ few units; Δv_drag ≈ k*12*exp(−10/8)*Δt ≈ k*12*0.29*2 ≈ 7k per passage. To remove ~60% of energy per passage... E = −4.88 initially; after passage 1, want apocenter ~40: E_a = −800/40 = −20 (with small v at apo). Energy removal ΔE ≈ 15 per unit reduced mass → equivalent Δv: ΔE = v·Δv (per unit mass) with v~12 → Δv ≈ 15/12 ≈ 1.25... that seems small; but energy is quadratic in v: better think: at pericenter v=12.3, orbital energy per mass at pericenter: v²/2 − 800/10 = 75.6−80 = −4.4 (conserved). Removing Δv=1.25 radially-ish changes KE by v·Δv ≈ 15. So Δv ~1.3–2 per passage suffices to bring apocenter from 164 to ~50: E=−20 → need ΔE≈15 → Δv≈1.2. So drag coefficient modest: k such that k*12*0.29*T_eff ≈ 1.5, T_eff≈1.5 → k ≈ 0.3. Hmm but drag also acts at 2nd, 3rd passages with shrinking periods → coalescence in ~3 passages ≈ first passage at t=14, apoc 164... wait after passage 1 apocenter ~? Δv=1.5 at v=12.3 → new E = v'²/2 − 80 with v'² = 12.3² − 2*12.3*1.5 + 1.5²≈151−37+2=116 → E=116/2−80=−22 → r_a≈36. Period a=(36+10)/2=23 → P=2π*sqrt(23³/800)=2π*sqrt(12167/800=15.2)=2π*3.9=24.5 time units. So second passage at t≈14+12=26 (half period from pericenter to apocenter to pericenter... from pericenter, time to next pericenter = full period 24.5). Second passage t≈38, third ≈ t≈55 with shrinking, coalesced by ~60–70. At 4 t.u./s: passages at 3.5s, 9.5s, 14s; merged core by ~16s; remaining 14s shows remnant with relaxed tails + long-lived shells. 

These estimates are rough (drag reduces apocenter each pass, so passages come faster and faster). Good enough; I'll implement drag with k≈0.35, λ=7, and cap: when separation < 2, additionally strong damping to glue cores. Also to avoid un-physical immediate slingshot weirdness, core-core softened with ε_cc=2.5.

Also important: as cores move, disk stars feel both cores' bulge+halo potentials. But after merger, two overlapping halos — fine.

One more physics nicety: the halos following the cores is what makes tails extend: test particles respond to moving potentials — fine, standard restricted simulation.

Now, star initial distribution per galaxy:
- N1 = e.g. 26,000, N2 = 22,000 (or equal 24k each; requirement ≥20k per galaxy). Texture: I'll use one simulation texture sized W×H = 512×128 = 65,536 particles total; use N1+N2 = 52,000, rest unused (or make N exactly 65,536? that's 32k per galaxy — GPU can handle easily; but more is not needed; keep ~52k for smoothness on modest GPUs — FBO sim of 65k is trivial anyway. Let me use N1=N2=24,000 → 48,000, texture 512×128 with 17,536 unused rows... unused particles: I'll park them far away (or just simulate them harmlessly far). Simpler: make the texture exactly fit: 48000 = 512 × 93.75 — not integer. Options: W=384, H=125 = 48,000. Or just use 65536 with all active: N1=32768, N2=32768 → 65,536 total, 32k per galaxy ≥20k. Texture 256×256. Clean! Physics cost identical (full-screen pass). Points: 65,536 points is fine for rendering with a single draw call. Let me do that: texSize 256, N=65536, first half galaxy A, second half galaxy B.

Wait — memory & fill: 256×256 RGBA32F ×2 (pos+vel) ×2 (ping-pong) = tiny. Sim shader trivial. 

Galaxy construction (per galaxy, at its initial position, oriented with some inclination):
- Position A: (−40, 0, −? ) hmm initial separation 80 along some axis in the orbital plane; I'll put the orbital plane tilted for cinematic view. Let me define orbital plane as X-Z plane (y up), galaxies A at (−40,0,0) and B at (+40,0,0)?? separation 80 → half-distance 40 each. Velocities: relative velocity v_rel = (radial 2.81, tangential 1.53). Each core moves at half relative velocity around barycenter: A velocity = +v_rel/2 direction... define relative vector r = r_B − r_A = (80,0,0). Relative velocity v_rel pointing: A moves toward B and sideways. Let me set: v_rel = (−2.81, 0, +1.53)?? Hmm sign: r from A to B is +x; infall means d|r|/dt < 0 → v_rel·r̂ < 0 → v_rel,x < 0. Tangential along −z or +z — choose so the encounter angular momentum makes galaxies rotate "prograde-ish" for the majority of stars; but each galaxy's spin orientation I control separately. Classic tails are strongest when disk spin is prograde with orbital angular momentum. I'll tilt both galaxies to be roughly prograde with the orbit, with different inclinations (A ~ 20°, B ~ −35° plus some yaw) for visual variety.

Set: orbital angular momentum L = r × v_rel. r=(80,0,0), v_rel=(−2.81, 0, 1.53) → L = (80,0,0)×(−2.81,0,1.53) = (0*1.53−0*0, 0*(−2.81)−80*1.53, 80*0−0) = (0, −122.4, 0). So orbital L is along −y. For prograde disk spin, disk angular momentum should be along −y-ish. So disks should spin clockwise viewed from +y. I'll set galaxy disk plane roughly X-Z with spin −y, then tilt.

Each core's individual velocity: v_A = −v_rel/2 * (m_B/(M))... equal masses: v_A = −v_rel/2, v_B = +v_rel/2 relative to barycenter at origin. With v_rel=(−2.81,0,1.53): v_A = (1.405, 0, −0.765), v_B = (−1.405, 0, 0.765). Check: relative velocity v_B − v_A = (−2.81, 0, 1.53). ✓.

Per-galaxy construction:
- bulge/core stars: ~25% of stars, spherical-ish Plummer distribution with radius ~1.5–2.5, warm colors, small random velocities (pressure support-ish; just give them small isotropic velocities ~0.5*v_circ or slight rotation; they'll sink into the core potential — since they're test particles in Plummer potential, an isotropic Plummer distribution needs specific velocity structure to stay equilibrium; otherwise it will collapse/pulse. Hmm. Simplest robust approach for bulge: give bulge stars circular orbits in random planes? That makes a puffy rotating spheroid that stays roughly stable (each star on its own Kepler-ish orbit in the Plummer potential — actually individual orbits in a spherical potential are stable regardless of velocity direction as long as speed < escape). Right! In a FIXED potential, any star with bound Keplerian-ish orbit just orbits forever. The "collapse" concern only applies if stars were forming a self-gravitating system. Here the potential is fixed (bulge+halo moving with core), so ANY distribution of velocities below escape velocity gives a stable-ish cloud, just evolving shape (virialization not needed). So: bulge stars: positions from Plummer sphere radius scale 1.5, velocities: isotropic with magnitude ~ 0.6 * local circular speed + slight net rotation. They'll form a glowing ellipsoid, mildly pulsing — fine visually.

  Actually even better for the "bright core" look: many bulge stars concentrated → additive blending naturally makes a bright core. Plus I'll add 2–3 large soft glow sprites at core positions that follow the cores (rendered as points with huge size and soft gaussian falloff, colored warm). These give the cinematic bloom-ish core without postprocessing bloom.

  Should I add UnrealBloomPass? It requires EffectComposer addons (importable from three/addons). It would elevate the cinematic quality massively. But bloom over 65k additive points might be heavy on some GPUs at full res; UnrealBloom is okay usually. Risk: composer + resize handling more code, but I've done it many times. Additive points already glow via accumulation; a mild bloom adds halo feel. Hmm, decide: I'll skip postprocessing bloom and instead bake glow into point sprites (gaussian falloff with extended halo per point: intensity = core gaussian + wider faint gaussian). With additive blending and thousands of overlapping points, cores will saturate to white nicely and arms get a hazy glow. This is robust and fast. I might add ONE extra "haze" points layer per galaxy: a few hundred large, very faint sprites tracing the disk to give diffuse galaxy glow (like unresolved starlight). That reads beautifully. These haze particles can also be simulated with the same GPU sim (they're just more particles with big size and low alpha!). Elegant: include them in the 65,536 budget? Then star counts... requirement "at least 20,000 stars rendered as glowing points" per galaxy — I'll have 32,000 true stars per galaxy plus ~800 haze particles per galaxy as a separate small CPU-simulated? No — just make them simulated too: total texture 256×256 = 65536: 31,000 stars A + 31,000 stars B + 1,768 haze (888+888)? Let me restructure: starsA = 30,000, starsB = 30,000, hazeA=2,000, hazeB=2,000, plus 1,536 spare parked at infinity (invisible: set w=0 → alpha 0 / size 0). Total 65,536. Wait, spare ones still get simulated — park them at r=10^6 with zero velocity; gravity from cores at distance 1e6 is negligible (~800/1e12). Fine. Or simpler: make haze 3,768? Let me just do: A stars 31,232? Ugh, keep clean numbers:

  - texSize = 256 → N = 65,536.
  - stars per galaxy: 30,000 each (60,000) → index 0..59,999.
  - haze per galaxy: 2,500 each (5,000) → 60,000..64,999.
  - spare: 536 → parked far, alpha 0.

  Requirement satisfied: 30,000 ≥ 20,000 per galaxy. 

  Hmm wait, but haze particles being simulated with the same gravity: they represent "unresolved light" — fine, they'll form tails too, glowing haze in tails — actually gorgeous (tidal tail gas/stars glow). Keep.

- Disk stars: 75% of stars. Position: radius r sampled ~ r = R_max * sqrt(u)-ish but I want denser center: use r = −ln(1−u)*scale? Exponential disk: p(r) ∝ r exp(−r/h). Sample via: r = h * (− W(…)) — no closed form simple; use rejection or mix: r = Rmax * pow(random, 0.65) gives concentration inward. Let me use r = r_in + (Rmax−r_in) * u^1.8 with r_in=1.2, Rmax=12? That's density increasing... u^1.8 biases toward small r. Density ∝ dr/du / surface... For visuals, what matters: star density per area decreasing outward, arms contrasting. I'll sample r with distribution biased inward: r = Rmax * (u^{0.7})? Let me not overthink: r = Rmax * sqrt(u) gives uniform surface density (more stars at large r in ring counts but uniform per area — looks flat). To get inward-bright disk: r = Rmax * pow(u, 0.75)?? For u uniform in [0,1], CDF r ∝ r^{1/0.75}=r^{1.33}: number of stars with radius < r ∝ r^{1.33}, surface density ∝ (1/2πr) dN/dr ∝ r^{0.33} — slightly increasing outward?? No: dN/dr ∝ r^{0.33}, σ ∝ r^{0.33}/r = r^{−0.67}. OK so pow(u,0.75) gives σ ∝ r^{−2/3}. I want steeper: pow(u, 1.0): dN/dr ∝ r, σ ∝ const. Hmm I mixed up. Let N(r) ∝ r^k → σ = N'(r)/(2πr) ∝ r^{k−2}. For exponential-like σ ∝ e^{−r/h} ~ steep, use k≈1 → σ ∝ 1/r (Malmquist) — reasonable. pow(u, 1/k): with k=1, r = Rmax*u gives N∝r, σ∝1/r. Hmm σ∝1/r isn't very centrally concentrated. k=0.6 → r = Rmax * u^{1/0.6}=Rmax*u^{1.67}, σ ∝ r^{−1.4}. Good: use r = Rmax * pow(u, 1.7), Rmax=12. Plus inner hole avoided since bulge dominates r<2 (blend fine).

- Spiral arms: logarithmic spirals. For a 2-armed galaxy: θ_arm(r) = θ0 + ln(r/r0)/tan(pitch). Pitch angle p ~ 15–20° (tan p ≈ 0.27–0.36). Stars: 70% assigned to arms: pick arm m ∈ {0,1} (or 2 arms for A, maybe 3 arms? give galaxy A 2 arms, galaxy B 2 arms too; or B gets 3 for variety — sure, B: 3 arms, slightly different pitch), scatter around arm center with gaussian spread growing with r (σθ ≈ 0.18 + r*0.01? and radial jitter σr ≈ 0.8). Remaining 30%: smooth disk background (uniform θ) with lower weight — gives inter-arm haze so arms stand out but disk looks continuous.

  IMPORTANT: arms defined as loci of star birth; in a live simulation the stars will rotate at Ω(r) and wind. Initial pattern winds trailing. Fine.

  Disk thickness: z offset gaussian σ ~ 0.25 + r*0.02 (flaring), times galaxy scale (disk radius 12 → thickness ~0.4 near center, 0.7 edge). Thin disks read as "disk galaxies" from inclination.

  Vertical velocities: tiny random ~0.05.

- Velocities for disk stars: circular v_c(r) computed from the SAME potential the shader uses (bulge+halo Plummer of their host) so orbits are consistent. v vector = tangential direction (spin direction) * v_c * (1 + small scatter 2–4%) + small radial scatter (±2%) + vertical. This keeps the disk coherent for seconds before interaction. Compute v_c in JS with same formula as shader (GM_b, ε_b, GM_h, ε_h).

- Spin direction & inclination: build local disk coordinates (u,v,w) basis; spin sign s = ±1 for prograde vs orbital L. Galaxy A: mostly prograde (s such that L_disk ≈ aligned with orbital L(−y)): tilt ~25°; galaxy B: tilt ~45° other direction and flipped-ish (retrograde component) — actually a mix gives richer morphology: one prograde → long tails; one mildly inclined → slightly different tail. I'll do A: L_disk aligned with −y tilted 22° about x; B: aligned −y tilted −38° about z, plus rotate some yaw. Just apply Euler rotations to positions & velocities per galaxy.

- Colors: color determined at spawn from final radius & arm membership & random: inner (r<2.5): warm (1.0, 0.82, 0.55)→(1.0,0.9,0.7); mid: (0.95, 0.92, 0.9) whiteish; outer/arms: blue-white (0.62, 0.74, 1.0) with some pure blue accents (0.45,0.6,1.0). Add per-star brightness variance. Haze: color = galaxy tint (A slightly warm ivory, B slightly cooler) very low alpha, big size.

Store per-particle static attributes in a separate texture or vertex attributes? Points draw: I'll create BufferGeometry with per-vertex attribute `aRef` (vec2 uv into sim texture) — 65,536 × 2 floats = fine. Additional static attributes (size, color) could be a third float4 packed... I can pack static data into ANOTHER DataTexture (color+size: RGBA: r,g,b,size) sampled with same uv. Or simpler: attributes in geometry: aColor (3), aSize (1). 65k vertices × 4 floats — trivial for a static buffer. Attributes are simpler (no extra texture fetch). But note: when using attributes + drawing points via THREE.Points with custom shader, all good.

But wait: with aRef as the only "position-ish" data, three.js needs `position` attribute to compute bounding sphere / draw range. I'll provide a dummy position attribute? Points requires 'position' for count. I can set position = the aRef uv values (and use `position.xy` as uv) — i.e., name the attribute 'position' (vec2 in a vec3 slot; set z=0). Then vertex shader: `vUv = position.xy;` then fetch sim texture. Need geometry.boundingSphere set manually (frustum culling off: `points.frustumCulled = false`). drawRange = full. 

Vertex shader:
```
uniform sampler2D uPos; // xyz = position, w = alpha/mode flag? 
attribute ... actually position attribute holds uv.
varying vColor, vAlpha...
vec4 p = texture2D(uPos, position.xy); // WebGL2 GLSL3? three ShaderMaterial default GLSL1 with texture2D works (three compiles to GLSL3? No—three uses GLSL1-style with #define texture2D texture when WebGL2... three automatically converts texture2D in ShaderMaterial? For raw ShaderMaterial three does NOT rewrite GLSL, but with WebGL2 it prepends "#version 300 es" only if material.glslVersion set. Default ShaderMaterial in WebGL2: three prepends 300 es? Let me recall: In WebGLRenderer, isWebGL2 true; for built-in materials three uses GLSL3 conversions internally via #include? Hmm. Actually three.js ShaderMaterial defaults: glslVersion = null → shaders compiled as GLSL ES 1.00 even on WebGL2 (WebGL2 accepts ES 1.00 shaders). Yes! WebGL2 contexts accept #version 100 shaders (ES 1.00) — WebGL2 supports both GLSL ES 1.00 and 3.00. So texture2D works fine. Good — keep GLSL1 syntax everywhere.
```

FBO ping-pong sim in three.js without addons: I'll create:
- `rtPos[2]`, `rtVel[2]`: WebGLRenderTargets with type FloatType (or HalfFloat — positions up to ±200 with fine detail: half float has 10-bit mantissa → at value 100, precision ~0.0625 — too coarse for smooth inner orbits? At r=1 near core, position quantization 0.03–0.06 would jitter stars. Use FloatType — widely supported (WebGL2 with EXT_color_buffer_float — available essentially everywhere WebGL2 is; three r186 requires WebGL2). I'll request FloatType; fallback HalfFloat if float rendering unsupported (check `renderer.capabilities`/extension; if not, HalfFloat with scaled-down units... I'll just try float, and if `renderer.extensions.get('EXT_color_buffer_float')` is null, fall back to HalfFloatType and hope; also LinearFilter needs OES_texture_float_linear — I'll use NearestFilter (exact texel fetch, no interpolation needed since uv = exact texel centers).

Sim step per frame: fixed number of substeps (e.g., 2–3 substeps × dt). Each substep:
1. render fullscreen quad into rtVel[dst] with velocity-update shader (reads pos[src], vel[src]; applies gravity & drag-of-stars? no drag on stars; integrates velocity: semi-implicit Euler: v += a*dt; maybe slight velocity clamp).
2. render into rtPos[dst]: pos += v_dst * dt. (Read the just-written vel[dst] — sequential passes fine.)
Swap src/dst.

Cores integrated in JS with same substeps (semi-implicit, softened mutual gravity + drag). Uniforms: coreA pos & GM params (vec4: x,y,z, GMbulgeA; second vec4 for halo? pack: uCoreA1 = (pos.xyz, GM_bulge), uCoreA2 = (halo ε? I need per core: pos (3), GMb, εb, GMh, εh → 2 vec4s per core where w slots carry GM and ε... 4 vec4 uniforms: uCoreAb=(posA,GMbA), uCoreAh=(εbA,GMhA,εhA, unused)... clunky. Just use: uCorePosA (vec3), uCorePosB (vec3), uCorePar (vec4) = (GMb, εb, GMh, εh) shared by both galaxies (equal masses — I'll make both galaxies identical masses; different visual spin/tilt only. Simpler and symmetric.) 

Hmm — equal masses is fine.

Acceleration in shader for star at position p:
a = −Σ_c GMb * (p−c)/( |p−c|² + εb² )^{3/2} + GMh * (p−c)/( |p−c|² + εh² )^{3/2}

dt stability: near core center, a ~ GMb/εb² * r... max accel at Plummer ~ GMb/(εb²) * something: max of r/(r²+ε²)^{3/2} at r=ε/√2? derivative: max at r = ε/√2·... value = (ε/√2)/ (ε²·(1.5)^{1.5})... anyway |a|max ≈ GMb * 0.385/εb² = 90*0.385/2.56 ≈ 13.5 for bulge; halo: 310*0.385/81 = 1.47. Total ~15. Velocity near core ~5. dt=0.02 → Δv=0.3 per step vs v=5 — 6% per step, semi-implicit Euler okay-ish; but orbital period at r=1.2: v_c(1.2): bulge 90*1.44/(1.44+2.56)^1.5=129.6/8=16.2; halo 310*1.44/(82.4)^1.5=446/747=0.6 → v²≈16.8→v=4.1; period=2π*1.2/4.1=1.84 → dt=0.02 → 92 steps/orbit — fine. Inner bulge stars r~0.5: v: bulge 90*0.25/(0.25+2.56)^1.5=22.5/4.71=4.78→v=2.19; period 2π*.5/2.19=1.43→ 71 steps/orbit. Fine. Use dt = 0.02 with 2 substeps per frame at 60fps → sim speed = 2.4 t.u./s. Hmm I wanted ~4 t.u./s. dt=0.03, 2 substeps → 3.6/s; dt=0.025, 3 substeps → 4.5/s (3 sim passes/frame — still trivial GPU cost: 3 passes × 2 textures × 256² — nothing). GPU-wise even 10 substeps would be fine, but let's be mindful of 120Hz displays: substeps tied to fixed dt accumulation vs frame time? Use real elapsed time: simTimeTarget += realDt * SPEED; steps = clamp(round((target−done)/dt))... Simplest robust: accumulate real dt (clamped to 0.05 max), nSub = ceil(acc/dt) capped at 6, dt_eff = acc/nSub (variable dt slightly — variable dt with semi-implicit Euler fine given margins). Hmm variable dt changes physics slightly; acceptable. Or fixed-step accumulator: while(acc>=dt && steps<6){step; acc-=dt;} — leftover acc causes micro-stutter in sim progression but visual smoothness dominated by rendering... stars' motion would jump by 1 step occasionally — imperceptible. I'll use accumulator with max 5 steps, dt=0.024 → SPEED = 60*0.024 = 1.44 t.u./s?? Wait: steps per real second = 60 (if acc grows 1/60 each frame and dt=0.024 consumes it each frame) → sim rate = 60 * 0.024 = 1.44 t.u./s. For 4 t.u./s need dt=0.0667 per frame — too big a step for stability (at r=1.2, 28 steps/orbit → mushy). Alternatively 2 fixed steps of dt=0.033 per frame → 4 t.u./s: 55 steps/orbit at r=1.2, still OK-ish; inner bulge stars r=0.5: 43 steps/orbit — marginal but bulge is a fuzzy glow; slight numerical heating invisible. Hmm, accuracy at pericenter passages: stars passing near the COMPANION core at v~12: during close encounter dt=0.033*12=0.4 per step — with softening εb=1.6 it won't explode (softened force bounded: max a=13.5+..., Δv ≤ 0.5/step). OK.

Actually let me reconsider SPEED: is 4 t.u./s right? Encounter timeline: first pericenter ~14 t.u. → 3.5s. Total 30s = 120 t.u. Post-merger relaxation continues. Outer tail material at r=30: v~2–3 → period ~70 t.u. — tails visibly evolve. Good. And Myr mapping: 120 t.u. ≡ say 550 Myr → 1 t.u. = 4.6 Myr → label "T = 213 Myr" climbing ~18 Myr/s. Hmm, real mergers take ~1–2 Gyr; but first-passage-to-coalescence in ~600 Myr is plausible for direct encounter. I'll map 1 t.u. = 5 Myr → 30s ≈ 600 Myr. Label: "t =  473 Myr". 

But hmm, first passage at 3.5s might feel abrupt? The requirement says show everything important in first 30s — earlier action is safer for recording. But also nice to have a moment to appreciate two intact spirals. First pericenter at ~4.5–5s real is a good compromise: D0=90, v0 slightly lower. Let me recompute with D0=90, v0_total=3.4 (v_t=1.45, v_r=3.08): E = 5.78 − 800/90=5.78−8.89=−3.11 → r_max = 257. Fall time: sqrt(257³/1600)=sqrt(1.7e7/1600=10625)=103; t(90): x=0.35: acos(sqrt... let me: acos(0.592)=0.937; sqrt(0.35*0.65)=0.477; sum=1.414; t(10)=1.567 → Δ=103*0.153=15.8 t.u. → at 4 t.u./s = 3.9s. Hmm similar. To push to ~5s: D0=105, v_r=2.9, v_t=1.4 (v0=3.22): E=5.18−7.62=−2.44→r_max=328. fall: sqrt(328³/1600)=sqrt(3.53e7/1600=22050)=148.5; t(105): x=0.32: acos(0.566)=0.9705; sqrt(0.32*0.68)=0.466; sum 1.4365; Δ=148.5*0.13=19.3 t.u. → 4.8s. And with v_t=1.4 at r=105: r_p = 105*1.4/12.3... pericenter v_p: v_p²=2(E+800/10)=2(−2.44+80)=155→v_p=12.45; r_p=147/12.45=11.8. Slightly wide pericenter; want ~8–10 for dramatic tails: v_t=1.15 → L=120.75 → r_p=9.7. v_r = sqrt(3.22²−1.15²)=sqrt(10.37−1.32)=3.01.

So initial conditions: r_A=(−52.5,0,0), r_B=(+52.5,0,0), v_rel=(−3.01, 0, 1.15)*? wait sign convention: v_rel = v_B − v_A. Infall: r_AB = r_B − r_A = (105,0,0); need v_rel·x̂ < 0: v_rel = (−3.01, 0, 1.15). Then v_A = −v_rel/2 = (1.505, 0, −0.575); v_B = (−1.505, 0, 0.575). Orbital L = r_AB × v_rel = (105,0,0)×(−3.01,0,1.15) = (0, 105*1.15−0, 0) = (0, +120.75, 0)?? compute cross: (r_y v_z − r_z v_y, r_z v_x − r_x v_z, r_x v_y − r_y v_x) = (0*1.15−0*0, 0*(−3.01) − 105*1.15, 105*0−0) = (0, −120.75, 0). Hmm: r_z v_x − r_x v_z = 0 − 105*1.15 = −120.75. So L_orb = (0, −120.75, 0) → −y. Prograde disks: disk angular momentum ~ −y.

Then pericenter ~9.7 with disks radius 12 → deep pass through disk → strong tails. 

Now, drag & eventual merger: drag on relative velocity: a_drag = −k_d * v_rel * exp(−r/7)?? At pericenter r=9.7: exp(−9.7/7)=0.25. a_drag = k_d*12.45*0.25 = 3.1*k_d. Duration near pericenter (r<15): time ≈ 2*15/12.45·(arc factor ~1.5) ≈ 3.6 → Δv ≈ 11 k_d·? Let me just set k_d = 0.35 → Δv ≈ 1.1/pass at first. Then subsequent passages closer (r_p shrinks due to drag? drag is velocity-proportional; it removes energy and angular momentum; pericenter shrinks too). Later passages r_p ~ 4–6: exp(−5/7)=0.49, stronger. Probably coalescence by t≈60–75 t.u. (15–19 s). Add extra "core stickiness": when r < 3, apply strong drag k2=1.2*exp(−r/1.5) → they quickly spiral into common center. Also I should stop displaying two cores separately after merge — cores overlap → single bright core automatically. To avoid residual tight binary jitter (which could look odd/breathing), the strong near-drag will damp it within a few t.u.

Alternative simpler: cap — when r < 2.0 and |v_rel| small, blend cores together (lerp positions). I'll implement the strong drag; check stability: with k2 large, v_rel damps exponentially; drag force ~ k2*v*exp(...): at r=1: a_drag = 1.2*v*0.51=0.61v per t.u. → damping timescale 1.6 t.u. → fine, they'll merge smoothly. Mutual softened gravity ε_cc = 2.2 → they don't singularize.

Edge case: numerical drift of barycenter — cores integrate symmetric, barycenter stays ~fixed at origin. Stars' potential is centered on cores → whole system stays centered near origin. Camera orbits origin. During encounter barycenter exactly at origin (equal masses, symmetric integration) — nice for framing.

Now the cores' own motion uses full mutual gravity softened: a = −G M_other * (r_i − r_j)/(d² + ε_cc²)^{3/2} with G M_total per galaxy = 400 (GMb+GMh). Slight inconsistency with test-particle forces (which see bulge+halo separately) — irrelevant.

Also: since the galaxies' halos overlap post-merger, stars in tails feel double halos — fine.

**Now think about what it looks like:**
- t=0–4s: two grand spirals, rotating (inner region visibly spinning: inner period ~1.8 t.u. → 0.45s per revolution at 4 t.u./s — whoa, inner stars whip around every half second. Visually that's a swirling core — could look frantic. Hmm. Inner disk r=2: period 2π*2/4.8=2.6 t.u. = 0.65s. That's fast but that's real differential rotation; cinematically it gives "alive" feel. Maybe slightly reduce SPEED to 3 t.u./s → inner rev 0.87s, first passage 6.4s. Hmm, the "everything in 30s" — fine. Actually the swirl speed sells the simulation as alive. Keep ~3.4 t.u./s: dt=0.028×2 substeps×60 = 3.36 t.u./s. First pericenter ≈ 19.3/3.36 = 5.7s. 30s → 101 t.u. ≈ 505 Myr at 5 Myr/t.u. Fine. Let me set dt=0.028, substeps=2, plus accumulator handles 120Hz (at 120fps, acc per frame 1/120; fixed steps of 0.028 would run at 60 steps/s only if accumulator... with fixed-step accumulator: at 120fps, acc=1/120 each frame → step every other frame → stars update at 60Hz — fine visually? Points move smoothly since steps are small; but a star moving 0.15 units per 8ms... at 60Hz updates with 16.7ms spacing — motion still smooth (60 updates/sec is smooth). But rendering interpolates? No — positions static between updates → effectively 60Hz motion at 120Hz display: perfectly fine (film is 24Hz).

  Alternatively variable substeps: nSub = ceil(acc/dt_fixed) with dt_sub = acc/nSub. At 120fps: nSub=1, dt_sub=0.014 — smoother! At 60fps: nSub=2, dt=0.028. This adapts beautifully. Cap nSub≤4 (if tab lag). Use this. Sim rate: SPEED = 3.4 t.u. per real second: each frame advance acc = realDt*3.4, subdivide. Variable dt semi-implicit Euler: stable given max |a| ~ 15 and v~12: dt≤0.033*12=0.44 movement vs softening 1.6 — fine. At 120Hz dt=0.014 even better.

- t≈5.7s: first pericenter — galaxies whip past each other, bridges form between them, tails fling outward. This happens fast (pericenter passage ~2–3 t.u. ≈ 1s real) — dramatic slingshot.
- t≈8–12s: tails develop; apocenter ~exp(−)... with drag Δv~1.1 at first pass: recompute apocenter: v_p reduces from 12.45 by ~1.1 → 11.35: E = 64.4−80 = −15.6 → r_a = 51. a=(51+9)/2=30 → P=2π√(27000/800)=2π*5.8=36.5 t.u. → next pericenter at ~5.7s + 36.5/3.4 ≈ 16.4s. Hmm that's a long gap with galaxies apart at 51 units — tails expand during this. Fine cinematically (second passage at ~16s, third ~22s after stronger drag shrinks period, merged by ~24–26s). Let me strengthen drag: k_d=0.5, λ=8 → Δv1 ≈ 0.5*12.45*exp(−9.7/8=0.297→0.54 wait exp(−1.21)=0.298)*duration(~3.6*0.8 weighted) ≈ 0.5*12.45*0.298*3 = 5.6?? That's huge — too much (would kill the orbit instantly, maybe good? Δv 5.6 vs v 12.4 → E after: v'=7 → E'=24.5−80=−55 → r_a=14.5 → immediate rapid inspiral, merger at ~12s. Hmm. Middle ground: k_d=0.35, λ=6: exp(−9.7/6)=0.199; Δv≈0.35*12.45*0.199*3≈2.6 → v'=10 → E'=50−80=−30 → r_a≈26.7 → a=18 → P=2π√(5832/800=7.29)=2π*2.7=17 t.u.=5s real. Second passage at ~10.7s, with more drag at closer passage... third by ~14s, merged ~16–18s. Then 12+s of remnant with magnificent double tails. I like this pacing better. But careful: drag applied CONTINUOUSLY (also during approach at r=100: exp(−100/6)≈0 → no effect. Good.) Also drag only on core-core relative motion — stars unaffected (they get their dynamics from potentials).

  Also should drag apply only when moving? a_drag = −k*v_rel*exp(−r/λ)*falloff also maybe scale by 1/(1+(r/λ)^2)... fine as is.

  Danger: over-damping makes cores fall straight in and merge like drops — actually that's cinematically fine (galaxies do coalesce). With v_t=1.15 initial and drag removing angular momentum at each passage, remnant spin comes from stars, not cores. OK.

  Let me finalize: k_d = 0.32, λ = 6.0; extra near drag: k2 = 1.5 * exp(−r/1.4) when r<4? Just add: a_drag += −1.6 * v_rel * exp(−(r/2.0)²)?? At r=2: exp(−1)=0.37 → 0.59*v per t.u.; at r=0.5: exp(−0.06)=0.94 → 1.5*v. Damping time ~0.7 t.u. → cores glue within ~2 t.u. of final contact. Good.

- Camera: start framing both galaxies: they're at ±52.5 → camera radius ~150 looking at origin. As they close, camera radius slowly eases to ~95–110, with slow orbit ω ≈ 0.05 rad/s?? Over 30s → 1.5 rad total — nice. Camera height varies: y = R*sin(inclination), inclination drifting from 18° to 38° (slow craning). Also slight lateral drift. LookAt target: origin, but during late merger maybe drift toward merged core (=origin anyway). Keep target at origin with tiny offset drift for parallax. Also FOV 55–60.

  Actually one more cinematic touch: camera radius should follow the action: tails extend to r~50–70 → camera at ~140–160 to frame; early approach galaxies span ±52.5+12 → need ~150 too. So: R(t) = 165 → 135 over 30s with gentle sine breathing ±8. Also I want a subtle "push-in" during first pericenter? Keep simple monotonic drift + breathing; scripted = reliable.

  Star size attenuation: size in world units → gl_PointSize = size * (H/2) / dist * proj... standard: gl_PointSize = uSize * uPixelRatio * (300 / -mvPosition.z). I'll compute: pointSize = aSize * uScale / dist, uScale = drawingBufferHeight * 0.5 / tan(fov/2)?? For perspective: pointSize_px = worldSize * (height_px / (2*tan(fov/2))) / depth. I'll set uPerspective = height_px / (2*tan(fov*0.5)) updated on resize. Star world sizes ~0.35–1.1 → at dist 140: px = 0.5* (900/(2*tan(27.5°)=1.041)) /140 = 0.5*864/140 ≈ 3.1 px. Reasonable. Bright core stars smaller but many → additive saturation. Haze: world size 18–30, alpha ~0.02–0.04 → giant soft glow.

  gl_PointSize max: implementations cap (often 1024 or 8192; WebGL guarantees ALIASED_POINT_SIZE_RANGE at least [1,1]?? Actually WebGL2 guarantees only 1..1?? No — OpenGL ES 3.0 spec minimum max point size is 1.0?! In practice desktop GPUs allow large points (≥1024); some mobile limit to 64 or 256. Hmm, risk: haze points of size 20–30 world → at dist 50: px = 25*864/50 = 432 px — might exceed mobile caps → haze pops/clips. Desktop typical cap 1024–2048 (fine). Given target is likely desktop recording, acceptable. I'll keep haze sizes moderate (≤ ~400px typical) and mention nothing. Alternatively use quads via instancing — overkill. Points it is.

- Twinkle: subtle per-star phase → alpha flicker in shader (sin(uTime*f + phase)*small). Adds life cheaply. Keep very subtle.

- Background starfield: 2,200 points on sphere r≈1200–1800, sizes 1–2.4 px, faint white/blue/warm mix, additive, NO size attenuation (or attenuation with huge sizes at huge distance... simpler: fixed pixel sizes via shader branch — separate material with gl_PointSize = aSize (no attenuation), depthWrite false. Slight opacity variance. Also ~30 brighter stars. And a very faint large-scale nebulosity? Could add a handful of ultra-faint big sprites for depth — maybe skip, keep background pure dark with stars. Dark starfield required. ✓.

- The time label: DOM element, top-left, styled: thin border? Scientific HUD: monospace-ish font stack ("SF Mono", "Cascadia Code", Consolas, monospace — no external fonts, use system monospace which is fine and not an "overused primary font" since it's a HUD readout, not identity typography... The label is UI microcopy; monospace HUD is appropriate & tasteful). Content: "T + 047.2 Myr" plus a second line with phase: "APPROACH → FIRST PASSAGE → TIDAL BRIDGES → TAIL EXPANSION → COALESCENCE → RELAXATION". Phase derived from sim state: separation & time. Also maybe separation readout "Δ 84.3 kpc" — maps 1 t.u. length unit: disk radius 12 ≡ 15 kpc → 1 unit = 1.25 kpc. Show separation in kpc. Nice scientific flavor. Keep the HUD small, unobtrusive, corner.

  Cinematic extra: a subtle title bottom-left? "GALACTIC COLLISION — restricted three-body simulation" small caption. Adds authored feel. Maybe bottom-right tiny caption "N = 60,000 test stars · softened gravity". Tasteful, tiny, low-opacity.

- Vignette: CSS radial gradient overlay? That's a gradient — but as a photographic vignette (transparent → dark edges) it's not a "decorative gradient banner" — it's cinematic grading. I'll use a subtle CSS vignette (radial-gradient transparent 55% → rgba(0,0,0,0.5) 100%). I think that's legitimate cinematography, not cheap decoration. Keep it subtle. Hmm — I said I avoid decorative gradients; a vignette is a filmic device and I judge it earns its place. Keep at low strength. Alternatively do it in-shader... CSS overlay div with pointer-events none is easiest.

**Rendering details / quality:**
- renderer: antialias false (points don't need MSAA; edges are soft sprites). Actually background stars as points — aliasing irrelevant. antialias:false saves perf. Set clearColor #000208 (near-black with hint of blue). 
- devicePixelRatio: cap at 2 (and maybe 1.75) for perf.
- Additive blending: THREE.AdditiveBlending, depthWrite:false, depthTest:false? For points within galaxies, depth test off with additive is standard (order independent). Background stars also depthTest false, drawn first (renderOrder). Set scene renderOrder: bg 0, haze/stars 1. Transparent: true.
- Tone: colors can exceed 1 in accumulation — with default tone mapping? renderer.toneMapping = ACESFilmic? For additive HDR-ish accumulation, ACES gives lovely highlight rolloff (cores go white-gold instead of clipping). OutputColorSpace SRGB. Points material custom shader: include tonemapping? Custom ShaderMaterial fragments don't automatically get tone mapping unless I include `#include <tonemapping_fragment>` and `#include <colorspace_fragment>`. I can add those chunks — they work in ShaderMaterial if the renderer defines the uniforms... tone mapping chunk uses toneMapping function compiled per renderer settings (three injects defines for built-in materials; for ShaderMaterial, `#include <tonemapping_fragment>` works since three parses includes, and the tonemapping GLSL functions come from `tonemapping_pars_fragment` which I must also include. And `toneMappingExposure` uniform is added automatically? For ShaderMaterial, renderer sets toneMappingExposure only for materials with toneMapped=true? Hmm — the uniform is part of the program's uniforms from UniformsLib? Safer: do my own filmic-ish curve manually in the shader: c = c/(1+c) or a mild ACES approx:
  ```
  vec3 tone(vec3 x){ return clamp((x*(2.51*x+0.03))/(x*(2.43*x+0.59)+0.14),0.,1.); }
  ```
  Wait that's the ACES fitted curve (Narkowicz) — apply to accumulated color per-point? NO — tone mapping per-point breaks additive accumulation (blending happens after fragment). Additive blending is linear accumulation; applying ACES per fragment then adding ≠ ACES of sum. Proper way: render HDR then post tonemap — needs composer. Without post: design point brightness so sums land in [0,~1.5] and rely on additive glow; final look: bright cores clip to white — that's fine/expected (white saturated core with colored fringe is actually how astrophotos look). Alternatively use blending that lets me do more: use CustomBlending with SRC_ALPHA? Additive with color*alpha premultiplied... Standard: gl_FragColor = vec4(color * intensity * alpha, 1) with AdditiveBlending (src=ONE dst=ONE? THREE.AdditiveBlending uses src=SRC_ALPHA? — THREE.AdditiveBlending: blendSrc = SrcAlphaFactor, blendDst = OneFactor. So output alpha scales contribution. I'll set gl_FragColor = vec4(col, alpha) where col can exceed 1... fine.
  
  Per-fragment I'll compute intensity profile: 
  ```
  float d = length(gl_PointCoord - 0.5)*2.0; // 0..1
  float glow = exp(-d*d*4.5);          // core
  glow += 0.28*exp(-d*d*1.4);          // soft halo? hmm wider gaussian: exp(-d*d*1.2)*0.15
  alpha = glow; color = vColor * (core brightness)
  ```
  Multiply by vAlpha and twinkle. Frag: `gl_FragColor = vec4(vColor * glow * vBright, glow*vAlpha)`? With AdditiveBlending (SrcAlpha, One): contribution = col*alpha... wait blendSrc SrcAlpha multiplies BOTH rgb by alpha? SrcAlpha factor applies to source RGB; source alpha channel multiplied by dst factor One... contribution rgb = srcRGB * srcA. If I output rgb=vColor*glow and a=glow*vAlpha → contribution = vColor*glow²*vAlpha — squaring the profile (sharper core, dimmer halo). Simpler: premultiply myself and use CustomBlending ONE,ONE: gl_FragColor = vec4(vColor*profile*vAlpha*brightness, 1). I'll use THREE.CustomBlending with blendEquation Add, src ONE, dst ONE — explicit and clean.

- Saturate handling: cores will sum >1 → clip to white naturally. 

- To give stars a hint of diffraction sparkle? Skip; keep gaussian.

**Now the GPU sim details:**

Textures: 
- posTex: RGBA32F, xyz=position, w=flag (1 = active/star, 0.5 = haze, 0 = spare/hidden). Alpha channel used for... actually alpha/visibility can be derived from index in render shader via a static attribute — I'll put per-particle static (color, size, alpha) in geometry attributes anyway, so w can carry e.g. "generation heat" unused. Keep w unused (store 0).
- velTex: RGBA32F xyz + w unused.

Initialization: generate data in JS typed arrays → THREE.DataTexture → upload → also copy into RTs. To seed the ping-pong RTs, render a fullscreen "copy" pass from the DataTexture into each rtPos[0], rtVel[0] (a trivial copy shader), OR simpler: since WebGL2 supports color buffer upload... easiest robust: render copy pass. I'll write a tiny CopyMaterial (fullscreen triangle). Also need rtPos[1], rtVel[1] initialized (they'll be written first frame anyway before read? order: step writes vel[dst] reading vel[src]; then pos[dst] reading pos[src] & vel[dst]. So dst targets are written before read — no init needed beyond allocation (allocate with null content — must ensure not read-before-write: fine by construction). 

Fullscreen quad: use THREE.OrthographicCamera(-1,1,1,-1,0,1) + PlaneGeometry(2,2) + ShaderMaterial, own scene: simScene, simCam. Render: renderer.setRenderTarget(rt); render(simScene, simCam). Careful: state leaks (viewport auto-handled by three). Also disable renderer.setRenderTarget(null) after.

Sim fragment shader (velocity update):
```
uniform sampler2D tPos, tVel;
uniform vec3 uCoreA, uCoreB;
uniform vec4 uPot; // GMb, epsb2(=eps^2), GMh, epsh2
uniform float dt;
varying vec2 vUv; (from vertex pass-through of uv)
void main(){
  vec4 P = texture2D(tPos, vUv);
  vec4 V = texture2D(tVel, vUv);
  vec3 p = P.xyz; vec3 v = V.xyz;
  vec3 a = vec3(0);
  // two cores
  vec3 dA = uCoreA - p; float rA2 = dot(dA,dA);
  vec3 dB = uCoreB - p; float rB2 = dot(dB,dB);
  a += dA * (uPot.x * inversesqrt(pow(rA2+uPot.y, 3.0))) ... 
```
compute: a += dA * GMb / pow(rA2+eb2, 1.5) + dA * GMh / pow(rA2+eh2, 1.5); same for B. Use inversesqrt: f = GMb * inversesqrt(rA2+eb2) / (rA2+eb2) → = GMb/(r+e)^{1.5} ✓ cheaper.

Then v += a*dt. Optionally mild global damping? No.

Also add tiny "softening vs escape": clamp speed to < 40 to avoid freak ejections dominating view? Tidal ejection is desired; cap at 60.

Position update shader:
```
vec4 P = texture2D(tPos, vUv); vec4 V = texture2D(tVel, vUv);
gl_FragColor = vec4(P.xyz + V.xyz*dt, P.w);
```

Cores updated in JS with same dt per substep (semi-implicit). Also compute drag.

Note: shader potentials use GMb=90,eb=1.6 / GMh=310,eh=9 — hmm reconsider halo size: halo ε=9 means halo potential is broad; stars at r=12 (disk edge) feel halo strongly — rotation curve flat ✓. Tails: when a star is tidally pulled, halo keeps it bound longer → longer-lived tails. Good.

Escape check: disk stars at r=12 need v_esc from potential: v_esc² = 2Σ GM/√(r²+ε²) = 2*(90/√(144+2.56) + 310/√(144+81)) = 2*(90/12.1 + 310/15) = 2*(7.44+20.67)=56.2 → v_esc=7.5; v_circ=4.5. Tidal stripping during pericenter at relative speeds ~12 — plenty of energy → tails fly out to 30–60. Some stars escape entirely → they'll drift away; that's physical and looks fine (faint diffuse spray). With cap 60 they won't teleport.

**Spiral arm math:**
For galaxy with 2 arms: for arm star: choose arm index m∈{0,1}: θ = θ_m + ln(max(r,0.8)/r0)/tan(p) + scatter. r0=1.0? Use θ(r) = k*ln(r) with k = 1/tan(pitch): pitch 18° → tan=0.325 → k≈3.08. Over r from 1.5→12: Δθ = 3.08*ln(8)=6.4 rad ≈ 1 full wrap — nice grand design. Scatter: σθ = 0.22 rad + jitter grows outward slightly; also radial gaussian jitter σr=0.9. Plus 30% smooth component with σθ uniform.

Direction: trailing vs leading relative to spin: spin Ω along L_disk; arms should trail: θ decreases as r increases if spin positive... honestly visually either works; I'll make them trail: with spin direction s (angular velocity sign about local w axis), trailing arms wind opposite to rotation. Since rotation will naturally wind the pattern further, initial trailing arms will become tighter over time — over ~19 t.u. pre-encounter the winding adds k*Δ... stars at different r shear by Δθ = (Ω(1.5)−Ω(12))*t = (3.26−0.28)*? Ω(1.5)=v/r=4.85/1.5=3.23; Ω(12)=4.5/12=0.375; ΔΩ≈2.86 rad/t.u.; over 5 t.u. → 14 rad shear!! That's 2+ wraps — arms would wind up into tight rings before first passage (5.7s real = 19 t.u.?? wait 5.7s real * 3.4 t.u./s = 19.4 t.u. → shear 55 rad ≈ 9 wraps — the spiral would be wound into an multi-ring blur before the collision! BAD.

Hmm. This is the classic winding problem. Solutions:
1. Start the encounter sooner (shorter approach): first pericenter at ~3–4 t.u.?? Then shear ~8–11 rad — still 1.5+ wraps. 
2. Use a rotation curve with LESS shear (more rigid rotation): Ω closer to constant → pattern persists. Rigid rotation = harmonic potential (solid body) — but then no flat curve... Compromise potential: strong extended halo + weak bulge → Ω(r) varies less. With pure halo Plummer (ε=9, GM=400): v² = 400 r²/(r²+81)^{1.5}: at r=2: 400*4/85^{1.5}=1600/785=2.04→v=1.43?? Ω=0.71. r=6: 400*36/(117)^{1.5}=14400/1265=11.4→v=3.37 Ω=0.56. r=12: 400*144/(225)^1.5=57600/3375=17.1→v=4.13 Ω=0.34. Shear over disk: 0.71−0.34=0.37 rad/t.u. → over 19 t.u.: 7 rad ≈ 1.1 wraps. Still winds but gracefully (initial arms become tighter spiral — actually looks like natural evolution). Hmm but inner rotation would look slow (period 2π/0.71=8.8 t.u.=2.6s) — the alive swirl is gone; disks look static-ish.

3. Pattern trick: DON'T let stars define arms initially via birth positions that shear apart; instead accept winding — actually in real grand-design images arms are density waves... too deep.

4. Reduce pre-encounter time by starting CLOSER: D0=64 → E = v0²/2 − 12.5. v0=2.6 (parabolic at 64 = sqrt(25)=5 → ratio .52): E=3.38−12.5=−9.1→r_max=88; fall time sqrt(88³/1600)=sqrt(681472/1600=426)=20.6*?? wait formula: t = sqrt(r_max³/2GM)*(acos...): sqrt(88³/1600)=20.6; t(64): x=0.727: acos(0.853)=0.548; sqrt(0.727*0.273)=0.445; sum=0.993; t(pericenter ~9): 1.567 → Δt=20.6*0.574=11.8 t.u. Hmm still ~12 t.u. because fall time scales sqrt(r³). To get 5 t.u. fall, need r_max ~ 40?? sqrt(40³/1600)=6.32; times Δfactor(~0.57)=3.6 t.u. → D0 such that 800/E… r_max=40 → E=−20 → v0²/2 = −20+800/D0. D0=45: E=−20+17.8 → v0² negative — impossible: E min at v0=0: E=−800/D0=−17.8 → r_max=45 → fall from rest at 45: sqrt(45³/1600)=7.55*0.57≈4.3 t.u. So starting essentially at rest at D0=45 gives 4.3 t.u. fall — but starting at rest looks odd (galaxies hanging then falling — actually fine? "deep-space encounter" — with slight inward drift it's fine). But D0=45 with disk radius 12 means disks are already close (gap 21) — visually "about to collide" from t=0. The approach phase would be short (~1.3s). I lose the majestic approach.

Rethink: maybe moderate: accept ~1.5–2 wraps of winding pre-encounter but START the arms wound such that... no wait, actually winding makes arms TIGHTER — after 1–2 wraps the two-arm pattern becomes a multi-turn logarithmic spiral — actually a tightly wound spiral still LOOKS like a spiral galaxy (like NGC whorl galaxies!). The visual problem is when differential shear blurs arms into uniformity — but pure shear of a 2-arm pattern never blurs it into uniformity, it wraps it into a fine multi-armed whorl; with additive rendering of 60k points, a highly-wound spiral becomes fine concentric-ish rings — looks like a "pinwheel". Slightly odd but actually still galaxy-like. Hmm.

BUT combined with per-star epicyclic motion? Stars on circular orbits maintain exact radius; the pattern shears but each ring stays crisp. The initial random scatter in r (σr=0.9) means each arm strand has radial thickness that persists; azimuthal shear stretches arm scatter along arc — arms become thin arcs → the disk turns into fine concentric ringlets ("wrapped rosette"). Over 19 t.u. with scatter σθ=0.22 → arc spread 0.22*2.86*19?? no: azimuthal spreading of a strand = ΔΩ_t * t? Two stars at same θ0, r differing by δr: after time t, angular separation = |dΩ/dr| δr t. dΩ/dr ≈ −2.86/10.5 ≈ −0.27 rad per unit r per t.u.; δr~0.5 → after 10 t.u.: 1.35 rad separation → arm strand spreads over 1.35 rad — arm contrast reduced a lot. Combined with wrap → by t=19 t.u. disks look like smooth annular haze with slight ringlets. Then the collision onsets with disks that have lost spiral structure — the "spiral galaxies" requirement visually mostly holds only early (~first 2–3 s real). Not great.

Better solution: **reduce shear by construction — make the potential more harmonic in the disk region**, i.e., increase halo ε & GM so that v ∝ r (solid body) inside r<6, flat outside. Solid body inner → arms co-rotate inner region... Mixed: bulge small GM=40, ε=1.2; halo GM=360, ε=16?: v² = 40 r²/(r²+1.44)^1.5 + 360 r²/(r²+256)^1.5. r=2: 40*4/10.07=15.9; 360*4/(260)^1.5=1440/4192=0.34 → v²≈16.2→v=4.03, Ω=2.01. r=4: 40*16/(17.44)^1.5=640/72.9=8.78; 360*16/(272)^1.5=5760/4487=1.28; v²=10.06→v=3.17?? wait that's lower than at r=2 — rising curve then: Ω(4)=0.79. r=2 Ω=2.01 vs r=4 Ω=0.79 — still big shear inside 4. The bulge always causes central shear. Reduce bulge mass, keep core bright via dense star concentration instead of deep potential. Bulge GM=25, ε=1.0; halo GM=375, ε=14: r=2: 25*4/(5)^1.5=100/11.18=8.94; 375*4/(200)^1.5=1500/2828=0.53 → v²=9.47→v=3.08 Ω=1.54. r=1: 25/(2)^1.5=8.84; halo 375/(197)^1.5=375/2765=0.136 → v²=8.97→v=3.0 Ω=3.0. r=6: bulge 25*36/(37)^1.5=900/225=4.0; halo 375*36/(232)^1.5=13500/3534=3.82 → v²=7.82→v=2.8?? v decreasing?? Ω=0.47. r=12: bulge 25*144/(145)^1.5=3600/1746=2.06; halo 375*144/(340)^1.5=54000/6274=8.61 → v²=10.67 → v=3.27 Ω=0.27. Hmm curve: v rises 3.0→2.8→3.27 — nearly flat ~3 with dip — fine-ish. Shear Ω 1→12: 3.0→0.27: still 2.7 rad/t.u. The inner Ω=3 is the killer (bulge). 

**Different approach — decouple pattern persistence from shear: make stars' angular speeds EQUAL within each galaxy? I.e., cheat the initial velocities: give every disk star the same angular velocity Ω0 (rigid rotation) even though potential is Keplerian-ish.** Then initially the disk rotates rigidly — the spiral pattern persists PERFECTLY (rigid rotation preserves any pattern). But the velocity field is inconsistent with the potential → stars begin to epicycle: those moving slower than local circular speed fall inward, faster move out — the disk heats/rings, arms blur via radial mixing after a few epicycle periods (epicycle period ~ 2π/κ ~ similar to orbital period at that radius ~ few t.u.). Within ~5 t.u. disk puffs. Hmm.

**Alternative: accept physics but reduce pre-encounter window by starting galaxies already close AND moving fast: D0=70, v0 = 4.6 (≈ parabolic at 70: sqrt(2*800/70)=4.78 — nearly parabolic, slight bound):** E=10.6−11.43=−0.84 → r_max=950?? With v mostly radial: fall time from... parabolic-ish infall from 70: time ≈ (2/3)*(70^{1.5})/sqrt(2*800)*?? For parabolic radial fall from r0 to rp: t = (2/3) r0^{3/2}/sqrt(2GM) * [(rp/r0)^{3/2}...] formula: t = sqrt(2) * r0^{1.5}/(3*sqrt(GM)) *... let me just: parabolic fall time from r0 to ~0: (2/3)*sqrt(r0³/(2GM)) = (2/3)*sqrt(343000/1600)= (2/3)*14.64=9.76?? Hmm that doesn't match earlier. Check earlier: from rest at r_max (bound, E=−GM/r_max): fall time = (π/2)*sqrt(r_max³/(2GM)). For parabolic (E=0, "from infinity") falling to r: t = (2/3) r^{3/2}/sqrt(2GM) measured from... the formula t(r) = sqrt(2/ (GM)) * (2/3) r^{3/2} — total time to fall from r0 to 0 = (2/3)*sqrt(r0³/(2GM))? units: sqrt(r0³/GM) has time units ✓. From r0=70: (2/3)*sqrt(343000/1600)= (2/3)*sqrt(214)= (2/3)*14.6=9.76 t.u. to reach center — to reach r=10 slightly less: ~9.3 t.u. Still 9+ t.u. (√r scaling is brutal).

OK so physics of gravity says: to have first passage within ~5 t.u., initial separation must be ≲45–55 OR initial speeds must be high (fast hyperbolic approach — visually fine! Galaxies zooming toward each other). High-speed approach: v0 = 9 t.u. at D0=75, mostly radial, slightly bound or parabolic: v_par(75)=sqrt(2*800/75)=4.62 → v0=9 is hyperbolic (E=40.5−10.67=+29.8) — they'd fly past and escape unless drag captures. First pericenter time: with high approach speed, time to close 75−10 = 65 at avg speed ~9→12: ≈ 6 t.u. ✓. Pericenter speed: v_p = sqrt(2(E+800/rp)) = sqrt(2(29.8+80))=14.8. r_p = L/v_p: choose v_t=2.2 → L=165 → r_p=11.1. Hmm fast encounter: pericenter passage duration even shorter — tails get flung MORE dramatically (higher relative energy → longer, hotter tails). Capture via drag: need to remove E=+29.8 → ΔE = v·Δv: at v=14.8: Δv needed ~ 29.8/14.8 ≈ 2 per pass (if all removed at passage). Drag k_d: Δv ≈ k*14.8*exp(−11/6)*3 ≈ k*14.8*0.16*3=7.1k → k=0.3 → Δv=2.1 ✓ then E≈0−ish... after pass 1: v'=12.7 → E' = 80.6−80=0.6?? still unbound marginally; second pass removes more (closer, slower? hmm E barely bound → apocenter huge → 2nd passage delayed ~long. Ugh.

Honestly, tuning blind is risky. Let me step back and pick robustness: **the two-core orbit is integrated numerically in JS in real time — I can shape it arbitrarily with a scripted drag profile and even scripted pericenter targets.** I control pericenter timing precisely by construction: I can even prescribe core motion kinematically? No — cores must respond to gravity for believability, but drag knobs let me shape it. Alternatively **prescribe the core relative orbit analytically** (a designed trajectory: inspiraling decaying ellipse), i.e., cores follow a choreographed path, stars feel choreographed cores. Fully deterministic, exact timing control, still physically plausible-looking. The "physics" then is: stars = test particles in time-varying two-center potential (this is literally the restricted 3-body setup, just with the binary's orbit prescribed rather than integrated). Since binary orbit evolution in real mergers is driven by dynamical friction with dark halo — prescribing it with a decay law is defensible as "cheap approximation". And I keep FULL control of pacing: first pericenter exactly at t=6s, second at 12s, merger at 20s. 

I like this a lot. Implementation: cores' relative separation vector follows a decaying spiral: 
r_rel(t) = A(t) * [cos φ(t), sin φ(t)] in orbital plane, with A(t) decaying smoothly from D0 to ~0.5, φ(t) = ∫ ω dt with ω from angular momentum conservation-ish: ω(t) = L0 / A(t)² (Kepler-ish for near-parabolic? For decaying orbit, use ω = C/A² with C chosen so pericenter speeds look right). Design: A(t) = piecewise/smooth function: A0=105 → 10 by t_p1=19 t.u.? Wait with prescribed motion I can even have the FIRST approach slow then... Let me design the relative orbit as a function of accumulated "phase":

Simplest choreography — a inspiraling pseudo-ellipse: use eccentric-anomaly-like parameter E(t) increasing with time (faster near pericenter for Kepler look), radius:
r(E) = a(1 − e·cos E), with a(t), e(t) decaying over time (a: 60→4, e: 0.88→0.2). φ = true anomaly from E: tan(ν/2)=sqrt((1+e)/(1−e)) tan(E/2). Position angle rotates by ν each orbit + periapsis precession? This gives a proper rosette inspiral — physically evocative (decaying eccentric orbit due to friction). Timing: E(t) = E0 + ω_E * t with ω_E increasing as a shrinks (Kepler: period ∝ a^{1.5}) → ω_E(t) = ω0 * (a0/a(t))^{1.5}.

Let me define: a(t) = a0 * exp(−t/τ_a) clipped, e(t) = e0 * exp(−t/τ_e). a0=48, so apocenter initial = a(1+e)=90 (D0 ✓ matches ±52.5... earlier core positions ±52.5 = D0/2 ✓ with a0(1+e0)=90, pericenter1 = a0(1−e0): choose e0=0.82 → r_p=8.6 ✓). Choose timing: first pericenter at t≈6s real = 20 t.u. (at 3.4 t.u./s). With Kepler-ish phase rate: ∫ω dt from 0..20 should equal ~π (starting at apocenter E=π? Start at apocenter: E=π; first pericenter at E=2π). So mean motion over first 20 t.u. ≈ π rad → ω̄ ≈ 0.157 rad/t.u. Kepler: ω ∝ a^{−3/2}: ω(t) = ω_ap0 * (a0/a(t))^{1.5}. With a decaying exp(−t/τ): a(t)/a0 = e^{−t/τ} → ω = ω0 e^{1.5t/τ}. ∫0..20 ω0 e^{1.5t/τ} dt = ω0 (τ/1.5)(e^{30/τ}−1) = π. If τ=16: e^{1.875}=6.52 → ω0*16/1.5*5.52 = ω0*58.9 = π → ω0=0.0533. Then pericenter speed consistency: v at pericenter ~ ω(t_p)*r?? Not exactly (radial velocity matters). Hmm — actually for prescribed circular-ish parametrization, velocity = d/dt[A(t)(cosφ, sinφ)] — I compute it analytically/numerically in JS by finite difference? I can compute position r1(t), r2(t) directly from relative vector history and get velocities by analytic derivative: v_rel = dA/dt * r̂ + A * dφ/dt * φ̂. All computable in closed form since a(t), φ(t) analytic (φ via integral — compute numerically each frame by integrating ω with fine dt alongside substeps: φ += ω*dt each substep ✓ and A, dA/dt analytic).

Then core positions: barycenter fixed at origin: coreA = −(mB/M) r_rel = −0.5 r_rel, coreB = +0.5 r_rel (equal masses). Core velocities = ±0.5 v_rel. All analytic. Cores never "merge" numerically — a(t)→ small: clamp a_min=1.2, e_min=0.15 → they orbit tightly at r~1–1.4 forever → looks like single merged core with tiny jitter (1 unit at distance 150 = sub-pixel; plus a tiny residual orbital wobble actually looks alive). Also add slight final eccentricity damping so they settle: e→0.05.

But wait: prescribed trajectory must LOOK like gravity: the stars feel the cores' potential; cores' motion needs to be consistent-ish with mutual gravity else subtle giveaways (e.g., cores slingshotting unrealistically). With decaying Keplerian rosette, motion near pericenter is fast and swing-by curved — looks right. dA/dt negative always (inspiral) — fine.

Actually — simpler alternative that's still prescribed but smoother: define relative orbit via pericenter passages: hmm, the a(t), e(t), E(t) parametrization above is good. Let me refine parameters for the desired timeline (sim units, SPEED=3.4 t.u./s → 30s ≈ 102 t.u.):

- t=0: apocenter, A=90 (a0=49.5?? a(1+e)=90 with e0=0.82, a0=49.45, r_p0=8.9).
- First pericenter at t≈20 t.u. (5.9s).
- Second pericenter ≈ t=20+P1; P1 = 2π sqrt(a1³/800)?? With a1 after decay: at t=20: a=49.45 e^{−20/16}=49.45*0.286=14.2?? τ_a=16 too fast. Let me instead directly choose phase evolution and radius evolution to hit milestones, rather than physical τ:

Design targets (t in t.u.):
- t=0: A=90, at apocenter, radial infall begins.
- t=20: pericenter 1, A=9.
- t=20→45: back out to A≈34 (apocenter 2), then in.
- t=45: pericenter 2, A=6.5.
- t=45→62: out to A≈16, back.
- t=62: pericenter 3, A=4.5.
- t=62→75: out to 9, back.
- t=75: A=3.2.
- t=75+: decaying to A≈1.6, circularizing, ω ~ continuous.
- After ~85: essentially merged, tiny circular orbit r=1.5.

Implementing via a(t) & e(t) smooth functions + phase integral: rather than hand-piecewise, use: a(t) = a_fin + (a0−a_fin) * exp(−(t/τ)^β)? With β>1 gives slow start... Let me use a decreasing function passing near targets: honestly simpler: define A(t) directly via a smooth monotone curve through control points with monotone interpolation? But A(t) must OSCILLATE (in and out) between pericenters. The a-e parametrization handles oscillation naturally.

Try: a(t) = 49.45 * exp(−(t/τa)^1.0)?? At t=20: want instantaneous a such that pericenter r_p = a(1−e)=9: if e(t)=0.82*e^{−t/30}: e(20)=0.42 → a(1−0.42)=9 → a=15.5 → decay from 49.45: τa: 49.45 e^{−20/τa}=15.5 → τa=20.3. Check apocenter2 at t≈45: a(45)=49.45*e^{−2.217}=5.4; e(45)=0.82*e^{−1.5}=0.184 → r_a = a(1+e)=6.4?? But I wanted apocenter2 ≈34 — contradiction: with τa=20.3 the orbit shrinks way too fast (apocenter2 only 6.4 → effectively merged by t=45 with pericenters at t=20,~33,~42...). Hmm, that gives: pass1 t=20, then quick decay: passes at ~t=29, 36, 41, 45, 48... merger complete ~t=45 (13s real). Then 17s of remnant evolution — too much remnant, too little dance? Actually maybe fine? Real merger videos show: pass, tails swing around, second pass, merge. Passes at 5.9s, 8.5s, 10.6s... cores merge by ~13s. Tails continue evolving beautifully through 30s. Hmm, the double-tail remnant phase is honestly the prettiest part. But the SECOND passage is where the biggest tails erupt in real simulations...

Let me reconsider pacing: maybe better: slower SPEED for same real-time pacing? All scaling is relative. What matters: (a) disk inner swirl period ~0.6–0.9s real for aliveness; (b) first pericenter ~5–6s; (c) second ~11–13s; (d) merged ~18–20s; (e) remnant tail evolution 20–30s.

Inner swirl: Ω_inner=3.23 rad/t.u. (with my bulge GM 90 ε 1.6 at r=1.5) → period 1.94 t.u. For 0.7s real → SPEED = 2.77 t.u./s. Then 30s = 83 t.u. Timeline in t.u.: pericenters at 19, 40, 55; merged ~65; remnant 65–83 (6.5s). OK!

So SPEED ≈ 2.75 t.u./s. Hmm but then the whole disk rotation (outer period 13.6 t.u. = 4.9s real) — visible ✓.

Now choreograph core relative orbit (t.u.):
- Start apocenter A=90 at t=0.
- Pericenter 1 at t≈19, r_p=9.
- Apocenter 2 at t≈31, A≈30.
- Pericenter 2 at t≈40, r_p=6.
- Apocenter 3 at t≈47.5, A≈13.
- Pericenter 3 at t≈53, r_p=4.
- Apocenter 4: t≈57.5, A≈7.5.
- Pericenter 4: t≈61, r_p≈3.
- Then rapid circular decay: A→1.8 by t≈68; after that A ≈ 1.8 constant, ω → settle to ~2.2 rad/t.u. (period 2.9 t.u. ≈ 1s real — tiny wobble, imperceptible at distance, or set ω final 1.2). Also e(t): 0.82 → 0.5 → 0.35 → 0.25 → 0.12 → 0.05.

Rather than a(t),e(t) exponentials (hard to hit milestones), I'll define these via smooth interpolation over CONTROL POINTS using monotone cubic (or Catmull-Rom with manual clamping) in t. a(t) control points: (0,49.45) (19, ~? a at pericenter time: a is semi-major — during the orbit a is "constant" per orbit but our a(t) varies continuously; pericenter radius = a(1−e) evaluated at that t). Let me define r_p(t) = a(t)(1−e(t)) and r_a(t) = a(t)(1+e(t)).

Control points:
r_a: (0,90) (31,30) (47.5,13) (57.5,7.5) (68,2.2) (75,1.9) (∞→1.8)
r_p: (19,9) (40,6) (53,4) (61,3) (68,1.7) → (75+,1.7)

From these: a(t)=(r_a+r_p)/2, e=(r_a−r_p)/(r_a+r_p). I'll define r_a(t) and r_p(t) via piecewise smoothstep-ish interpolation between keypoints:
- r_a keypoints: [0,90],[19, ~38?]... hmm r_a at t=19 is mid-orbit value ~ average-ish. This is getting fiddly. Cleaner: parametrize by ANGLE: the relative orbit is (in polar) r(φ) with rosette precession... 

Alternative much simpler choreography that looks great: **multi-lobe decaying epicycle**: r(φ) = r_apo_decay... You know what, let me use a different formulation: prescribe the relative position as a damped Kepler orbit via "universal variable"?? Overkill.

Cleanest practical: define a(t) and e(t) with exponential decays TUNED to hit my targets approximately, accepting approximate milestone times:
- a(t) = 3 + 46.5*exp(−t/22) → a(0)=49.5, a(19)=3+46.5*0.42=22.5, a(40)=3+46.5*0.162=10.5, a(60)=3+46.5*0.0656=6.05, a(80)=3+3.66=6.7?? e^{−80/22}=0.0264*46.5=1.23 → a=4.23. 
- e(t) = 0.05 + 0.77*exp(−t/26): e(0)=0.82, e(19)=0.05+0.77*0.48=0.42, e(40)=0.05+0.77*0.216=0.216, e(60)=0.098, e(80)=0.059.
- r_p(t)=a(1−e): t=0: 49.5*0.18=8.9?? Wait r_p at t=0 should be ~8.9 for pass1 at t≈19 — but r_p(t) is the pericenter of the CURRENT osculating orbit; the first actual pericenter passage happens at t≈19 with the orbit's parameters AT THAT TIME: a(19)=22.5, e(19)=0.42 → r_p=13.1, r_a=31.9. Hmm — so first pass at r≈13 not 9 — fine-ish (13 with disk radius 12 = grazing through outer disk → still strong response but maybe weaker bridges... r_p=13 vs disk 12: just outside disk — decent tails but the dramatic deep cut comes from r_p < 10.

The issue: exponential a(t) decays too fast early. Use power-law-ish slower decay with a floor and faster late decay: a(t) = a_fin + (a0−a_fin)/(1+(t/T)^s) — heavy-tail: at t=19 stays high. Want a(19)≈? For pass1: r_p1 = a(19)(1−e(19)) ≈ 9 & r_a2 (apocenter after pass 1, at t≈31) = a(31)(1+e(31)) ≈ 30.

Take a(t) = 3 + 46.5/(1+(t/24)^1.6): t=19: (0.792)^1.6=0.684 → a=3+27.6=30.6; t=31: (1.29)^1.6=1.506 → a=3+30.9=33.9?? That INCREASED relative to... no: a(31) = 3+46.5/2.506=21.6. t=40: (1.667)^1.6=2.32→a=3+20=23?? 46.5/2.32=20 → a=23. Hmm at t=40, want pericenter2 r_p=6 with a=23 → e=(1−6/23)=0.74?? But e should have decayed... contradiction: if a is still 23 at second pericenter but r_p=6, then apocenter after would be a(1+e)=40 — no good; I want r_a≈13 by then.

The tension: Kepler's a can't drop from 30 to 8 in 10 t.u. without the orbit passing through... actually it CAN with drag (drag removes energy AT pericenter: a drops abruptly at each passage — a(t) is piecewise constant between passes, dropping at passages!). So model a(t) as STAIRCASE with rapid smooth drops at passage times. Similarly e. So: piecewise per orbit:
- Orbit 1 (t∈[0,19]): a1=49.5?? wait if a=49.5, e=0.82 for orbit 1, period P=2π√(a³/800)=2π√(121287/800=151.6)=2π*12.31=77 t.u. — half period (apo→peri) = 38.6 t.u. — but I want first pericenter at t=19! Contradiction with Kepler timing: falling from apocenter 90 to pericenter 9 with a=49.5 takes 38.6 t.u. — too slow (11+ s real). To fall in 19 t.u., need either smaller a (but a is set by apocenter 90 → a≥45) — OR the initial infall is FASTER than Kepler (extra drag during approach? physically dynamical friction with halos does accelerate mergers... but halos only overlap late). OR just accept longer fall: first pericenter at t≈38 t.u. = 14 s real?? TOO LATE.

Hmm wait — check my earlier free-fall estimate: from rest at r=90 (E=−8.89, r_max=90): t_fall = (π/2)*sqrt(90³/1600) = 1.5708*sqrt(729000/1600=455.6)=1.5708*21.3=33.5 t.u. to CENTER; to r=9: t(r) = sqrt(r_max³/2GM)*(acos√x + √(x(1−x))), x=r/r_max: x=0.1: acos(0.316)=1.247; √(0.09)=0.3 → 1.547; t = 21.3*1.547=33. From r=90: x=1: acos(0)=π/2=1.5708 + 0 = 1.5708 → 33.5. So fall 90→9 ≈ 0.6 t.u.?? No wait: t decreases toward... at x=1 sum=1.5708 (t=33.5), at x=0.1 sum=1.547 (t=33.0) — the fall from 90 to 9 takes only 0.5 t.u.?! That can't be right... OH I see — free fall from REST at r_max: the object accelerates massively; most time is spent near apocenter where speeds are tiny. From 90 to 9 in 0.5 t.u.?? At r=90, a=800/8100=0.099 — after 0.5 t.u. v≈0.05?? Contradiction. Let me recompute: hmm the radial fall parametrization: for E=−GM/r_max, r(η)... let me just sanity check with numbers: falling from rest at 90: after t, v² = 1600(1/r − 1/90). After t=5: distance fallen ≈ ∫v dt; v grows: at r=80: v=sqrt(1600*(0.0125−0.0111))=sqrt(2.22)=1.49; r=60: sqrt(1600*(0.01667−0.01111))=sqrt(8.9)=2.98; r=40: sqrt(1600*(0.025−0.0111))=4.72; r=20: sqrt(1600*0.0389)=7.89; r=9: sqrt(1600*(0.111−0.0111))=12.65. Time ≈ ∫dr/v from 9..90: rough segments: 90→60 avg v≈2 → 15; 60→40 avg v≈3.7 → 5.4; 40→20 avg v≈6 → 3.3; 20→9 avg v≈10 → 1.1; total ≈ 24.8 t.u. OK so ~25 t.u. (my formula misuse above was wrong — correct Kepler free-fall from apocenter with a=45, e=1: time apo→peri = half period of e=1 degenerate... whatever, ~25 t.u.). So natural free-fall from 90 = 25 t.u. = 9s real. Hmm. And with some initial inward velocity (v_r0=3): time shortens to ~17–19 t.u. ✓ (matches my earlier estimate of ~19 t.u. for D0=105, v0=3.2).

So Kepler-consistent choreography: start at t=0 NOT at apocenter but already mid-fall with inward velocity — i.e., start on an eccentric orbit at true anomaly ν0 with r0=90 heading inward, pericenter reached 19 t.u. later. Let me construct: orbit with a=45, e≈?; r(ν)=a(1−e²)/(1+e cosν). At r=90: 90 = 45(1−e²)/(1+e cosν0) → 2(1+e cosν0) = 1−e² → e cosν0 = (1−e²−2)/2 = −(1+e²)/2. Need |e cosν0| ≤ e → (1+e²)/2 ≤ e → (e−1)² ≤ 0 → only e=1. So r=90 = apocenter for any bound orbit with a=45! Right: r_a = a(1+e) ≤ 2a = 90. So starting AT r=90 means starting at apocenter → slow start (v≈0 at apo — galaxies momentarily hanging, then falling — 25 t.u. fall). To have meaningful inward speed at r=90 need a > 45 (e.g., a=60: r=90 with e cos ν0 = (a(1−e²)/r − 1)/e = (60(1−e²)/90 −1)/e = (2(1−e²)/3 −1)/e = ((2−2e²−3)/3)/e = −(1+2e²)/(3e). For e=0.5: −(1+0.5)/1.5=−1 → ν0=π?? e=0.5: (1+2*0.25)/(1.5)=1.5/1.5=1 → again apocenter (r_a=60*1.5=90). Hmm: any (a,e) with r_a=90 has v=0 at r=90. To start at r=90 with inward velocity, need r_a > 90: a=55, e=0.75 → r_a=96.25, r_p=13.75. At r=90: cosν0 = (a(1−e²)/r − 1)/e = (55*0.4375/90 −1)/0.75 = (0.2674−1)/0.75 = −0.977 → ν0 ≈ 167.6°. Time from ν0 to pericenter: eccentric anomaly: cos E = (cosν + e)/(1+ e cosν): cosν=−0.977: (−0.977+0.75)/(1−0.733)= −0.227/0.267=−0.851 → E0 = 2.586 rad (≈148°); pericenter E=0... time from E0 to 2π: (E0→π→2π): M = E − e sinE: M0 = 2.586 − 0.75*sin(2.586)= 2.586−0.75*0.526=2.192; M(2π)=2π → ΔM = 2π−2.192 = 4.091; Δt = ΔM * sqrt(a³/800) = 4.091*sqrt(166375/800=208)=4.091*14.42=59 t.u.!!! Way too slow — because apocenter 96 with a=55 → period 2π*14.42=90.6, and we're near apocenter crawling.

I keep fighting Kepler timing. Conclusion: to get a swift cinematic approach (≤6s real ≈ 17–20 t.u. from r=90 to pericenter ~9), physics needs either initial v_r ≈ 3 (bound, moderately eccentric — computed earlier: works, ~17 t.u.) — that's FINE. Let me redo cleanly: choose orbit a=45 (so apocenter ≤90), start at r=90 = apocenter exactly with... v=0 there — no. Use a=50, e=0.85: r_a=92.5, r_p=7.5. Start at r=90: cosν0=(50(1−0.7225)/90 −1)/0.85 = (0.1542−1)/0.85=−0.995 → ν0=174.3°, E0: cosE=(−0.995+0.85)/(1+0.85*(−0.995))= −0.145/0.1542=−0.940 → E0=2.80 rad; M0=2.80−0.85*sin(2.80)=2.80−0.85*0.335=2.516; ΔM=2π−2.516=3.767; t=3.767*sqrt(125000/800=156.25)=3.767*12.5=47?? STILL huge. Hmm why? sqrt(a³/GM_total) with a=50: 12.5 t.u. is the "time unit scale"; near-apocenter crawl consumes most of the period. M0 near 2π−1.27 → the remaining phase 3.77 rad of MEAN anomaly but true motion near pericenter... wait ΔM=3.77 means the orbit is 60% of period remaining → 47 t.u. But actual fall from r=90 (near apo 92.5) to peri 7.5 should take ~half period + bit = 39 t.u. Yeah ~40+ t.u. So ANY bound orbit starting at r≈90 takes ~25–40 t.u. to pericenter?? But earlier I computed D0=105, v_r=3.01, v_t=1.15 → E=−2.44 → r_max=328, fall 19 t.u. That's a MORE energetic orbit (a=(r_p+r_a)/2=(9.7+328)/2=169!) yet falls faster?? Because it starts at r=105 << r_a=328 with substantial radial velocity 3.01 — it's mid-dive, not loitering at apocenter. Yes! The trick: give substantial INITIAL RADIAL VELOCITY at t=0 — start already diving. r_a=328 is just where it WOULD go if not for drag; drag isn't acting far out (exp(−r/λ)≈0) — but wait, prescribed-vs-integrated: if I PRESCRIBE the core motion, I don't need Kepler consistency at all! I can start at r=90 with v_r=−3 and let the prescribed trajectory be whatever I design. The earlier INTEGRATED plan gave pericenter at ~19 t.u. naturally. And the prescriptive plan needs choreography matching roughly that.

OK final decision — HYBRID: integrate the two cores numerically (2-body softened + drag), with initial conditions chosen for good timing (D0=105?? hmm wait now: with v_r=3.01, v_t=1.15 at D0=105 → pericenter ~9.7 at t≈19 t.u.). Then drag shapes the subsequent decay. The earlier staircase concern (P1=36 t.u. gap) is handled by drag tuning — and drag is a FREE parameter I can make strong since I have a fallback: additional gentle "always-on" tidal drag ∝ 1/(1+(r/25)²)? Hmm.

Let me now be careful and design the core orbit with drag analytically-ish, passage by passage, to ensure good pacing. Setup: μ = G(M1+M2) = 800. ε_cc softening for mutual force: I'll integrate with softened force −μ (r_vec)/(r²+ε²)^{3/2}, ε_cc=2 → near pericenter force capped ≈ μ*r/(r²+4)^{1.5}: at r=2: 1600/(8)^1.5=1600/22.6=70.7?? wait μ=800: a = 800*r/(r²+4)^{1.5}: r=2 → 1600/22.63=70.7; r=4: 3200/(20)^1.5=3200/89.4=35.8; r=9.7: 7760/(98.1)^1.5=7760/971=8.0 (vs unsoftened 8.5 — softening negligible there ✓).

Drag: a_d = −c_d * v_rel * exp(−r/λ_d). Passages:

Passage 1 (t≈19, r_p=9.7, v_p≈12.4): drag active r<~15: exp(−9.7/6)=0.198; effective duration ~ 3 t.u. (weighted) → Δv ≈ c_d*12.4*0.198*3 ≈ 7.4 c_d. Want post-pass1 apocenter ~35: E_after = v'²/2 − μ/r_p(at v' evaluated at pericenter; r_p≈9.7 unchanged during brief pass): E = v'²/2 − 82.5. Want r_a=35 → E = −μ/(r_a+r_p... for softened not exact; approx E = −μ/(2a), a=(35+9.7)/2=22.4 → E=−17.9 → v'² = 2(82.5−17.9)=129 → v'=11.4 → Δv=1.0 → c_d = 1.0/7.4 = 0.135. Hmm that's small; also drag at r 10–15 region during approach (incoming v high ~12): approaching from 30→10 takes Δv_drag ≈ c_d*∫v exp dt: ∫ over path: roughly path length 25 at v~9 avg with exp(−r/6) averaging ~0.08 → ≈ c_d*25*0.08?? ∫v exp(−r/6) dt = ∫ exp(−r/6) dr ≈ [−6 exp(−r/6)] from 30→10 = 6(0.0066−...)=6*(e^{−1.67}−e^{−5})=6*(0.189−0.0067)=1.09 → Δv ≈ c_d*v̄*1.09 ≈ c_d*10 → inbound Δv ≈ 10 c_d ~ 1.35 for c_d=0.135 — slows approach slightly (fine, adds ~10% to fall time).

Orbit 2: a=22.4, e: r_p 9.7, r_a 35 → e=(35−9.7)/44.7=0.566; P=2π√(22.4³/800)=2π√(11239/800=14.05)=2π*3.75=23.6 t.u. Pericenter1 at t=19 → pericenter2 at t≈19+23.6=42.6. Hmm 42.6 t.u. = 15.5s real. Gap 9.6s between passes — long stretch with tails swinging (that's OK cinematically — the tails from pass 1 are the highlight; galaxies separate to 35 units with long tails — gorgeous "Antennae" phase). Antennae at apocenter = iconic. ✓

Passage 2 (t≈42.6, r_p≈9.7, v_p: E=−17.9 → v_p=sqrt(2(82.5−17.9))=11.4): drag Δv ≈ c_d*11.4*0.198*3=6.8c_d → want r_a3 ≈ 14: a3=(14+9.7)/2=11.85 → E=−33.8 → v'²=2(82.5−33.8)=97.4→v'=9.87 → Δv=1.53 → need c_d≈0.225. Conflict: same c_d must give Δv 1.0 at pass1 and 1.53 at pass2 — pass2 naturally gives 6.8*c_d = 0.92 for c_d=0.135 → v'=10.5 → E=−26.9 → a=17.2 → r_a=24.7?? Then pass3 at P=2π√(17.2³/800)=2π√(5090/800=6.36)=2π*2.52=15.8 → t≈58.4; pass3 Δv≈0.9*... each pass Δv~1 → apocenters: 35→24.7→? pass3: v_p: E=−26.9: v_p=sqrt(2(82.5−26.9))=10.5; Δv=0.92→v'=9.6→E'=46−82.5=−36.5→a=13.4→r_a=17.2, P=2π√(2406/800=3.0)=10.9→pass4 t≈69.3, r_p shrinks? drag also removes L: L after passes shrinks → r_p decreases: L1 initial 120; ΔL ≈ c_d*exp*r*... L loss per pass ~ Δv_tangential*r ~ 1*10=10 → r_p = L/v_p: after 3 passes L≈90, v_p≈9.6 → r_p≈9.4?? hmm softened... r_p stays ~8–9. Fine — passes keep r_p ~8, apocenters: 35, 25, 17, 12 (t≈78), then P≈8 → passes at 86, 92, ... merger (r_a<4) by t≈100 (29s real). Cutting close to the 30s window — merged core right at the end. Risky. Increase c_d to 0.2: pass1 Δv=1.48→v'=10.9→E=−23→a=20.5→r_a=31, P=21.4→pass2 t=40.4: Δv=1.35→v'=10.1→E=−30.8→a=16.5→r_a=23.4,P=16.4→pass3 t=56.8: Δv≈1.2→a≈13→r_a≈17?? let me: v_p at pass3: E=−30.8: v_p=sqrt(2(82.5−30.8))=10.17; Δv≈0.2*10.17*0.198*3=1.21→v'=8.96→E'=40.1−82.5=−42.4→a=12.25→r_a=14.8; P=2π√(1838/800=2.30)=9.53→pass4 t≈66.3: v_p=sqrt(2(82.5−42.4))=8.95;Δv=1.06→v'=7.9→E'=31.2−82.5=−51.3→a=9.75→r_a=11.5; P=2π√(927/800=1.16)=6.77→pass5 t≈73: Δv≈0.95→v'=6.95→E'=24.2−82.5=−58.3→a=7.75→r_a=8.5?? hmm wait r_p also shrinking... P=2π√(465/800=0.58)=4.8→pass6 t≈77.9... by pass 7–8 (t≈82–86) a≈4 → r_a≈6, passes every 3.3 t.u., then rapid: merged (r_a~2.5) by t≈90–92 (26.5s). Tight but OK. Also near-drag (r<4: k2) accelerates final coalescence once r_p drops below ~4 — L shrinks each pass so r_p: starts 9.7, after ~5 passes L≈120−5*8=80, v_p≈7 → r_p≈11?? hmm L/v_p: 80/7=11.4?? That says r_p GROWS — no: L loss per pass: ΔL = r_p * Δv_t ≈ 9.7*1.0=9.7 per pass → L: 120→110→100→91→82→73; v_p: 12.4→10.9→10.1→8.96→7.9→6.95 → r_p = L/v_p: 9.7, 10.1, 9.9, 10.2, 10.4, 10.5 — r_p ~ constant ~10! The drag as modeled (∝v) barely changes r_p — orbits shrink in apocenter only, r_p stuck at ~10, and merger stalls: a→(10+r_a)/2 with r_a→10 → circular orbit r=10 with slow decay via continuous drag: at circular r=10, drag Δv/t.u. = 0.2*v_c(10)*0.189 = 0.2*4.62*0.19=0.175/t.u. → v decays, r decays at rate: dr/dt ≈ 2 r Δv/v = 2*10*0.175/4.6 = 0.76/t.u. → from 10 to 2: ~11 t.u. → total merged ~ t=92+ hmm plus near-drag kicks in below r=4. Roughly merged by t≈95 (28s). Too late. Fix: make λ_d bigger (drag reaches farther, λ=10) and c_d 0.25: continuous decay stronger: at r=10: exp(−1)=0.368: rate=0.25*4.62*0.368=0.425/t.u. → dr/dt=2*10*0.425/4.6=1.85/t.u. → 10→2 in ~5 t.u. after circularization ~t≈80 → merged ~t=85 (25s) ✓. And passages shrink faster too. Also add the near-drag r<4 term to finish.

But bigger λ_d also drags during approach: inbound Δv = c_d*v̄*∫exp(−r/10)dr from 105→10 = 0.25*~6*(10*(e^{−1}−e^{−10.5}))=0.25*6*10*0.367=5.5!! That kills the inbound speed (slows approach, delays pass1 to ~24 t.u. — acceptable? changes v_p... ugh. Hmm. The exp(−r/λ) integral over a long approach is substantial when λ=10.

Fix: make drag depend on relative SPEED too? Dynamical friction ∝ ρ(v) ~ stronger at low speed? Real Chandrasekhar drag ∝ 1/v²-ish at high v... Make drag ∝ exp(−r/λ) * v/(v²+s²)^{?}... complicated. Simpler: gate drag by proximity more sharply: exp(−(r/λ)²) with λ=9: at r=105: e^{−136}≈0 ✓; at r=30: e^{−11}=1.7e−5; at r=10: e^{−1.23}=0.29; r=5: e^{−0.31}=0.73; r=2: 0.95. Inbound integral ∫exp(−(r/9)²) dr from 10→105 ≈ ∫10..∞ ≈ 9*√π/2*(erfc stuff) ≈ 9*0.886*(erfc(1.11)≈0.116)?? ∫_10^∞ e^{−(r/9)²}dr = 9∫_{1.11}^∞ e^{−u²}du = 9*0.886*erfc(1.11)=9*0.886*0.117=0.93 → inbound Δv = 0.25*10*0.93 = 2.3 — still notable (v_r 3→~2.4 early?? it's applied gradually; the deceleration mostly matters far out where v small... Δv 2.3 on v0 3.2 would stall the infall!! Because far away speed is only 3. Losing 2.3 → approach nearly stalls → falls from rest → slow. BAD.

Rethink: gate drag ALSO by time? No... Gate by speed direction? Real fix: dynamical friction acts on the CORES due to halo stars; in restricted sim, friction magnitude ∝ 1/v_rel² for high v... At v=12 near pericenter vs v=3 inbound: F∝1/v² gives 16× stronger when slow — opposite of what I want. Hmm, but honestly the physical accuracy here is a joke anyway; what I need is a control system: I want: minimal drag during t<pericenter1, strong energy removal at each pericenter, continuous mild decay later. I can simply TIME-GATE the drag: drag ramp: c_d(t) = c_max * smoothstep(16, 20, t)?? Drag turns on near first pericenter. But that's blatantly scripted — however it's invisible: drag only affects the two core points, and its effect (orbit decay) is exactly what real dynamical friction produces. Nobody can tell drag was time-gated. But robustness: if pericenter time shifts (numerics), the gate might mistime. Pericenter1 timing is quite deterministic given fixed ICs and dt≤0.033 (small integration error). Use gate: c_d(t) = 0.28 * s(t) where s(t) = clamp((t−14)/6, 0, 1) — reaches full at t=20 ≈ pass1. Inbound (t<14): zero drag ✓. Then continuous thereafter. Also pericenter-triggered extra: none needed.

Also I realize the approach: v0=(3.01 radial, 1.15 tangential) at r=105 → but with gate-on at 14, inbound unaffected ✓. Pass1 timing ~19–20 t.u. (5.6–5.9s real at 3.4?? SPEED: let me now fix SPEED=3.4?? earlier I derived 2.75 from inner swirl period. Hmm conflict: timeline targets assumed ~3.4. Let me re-derive: I want first pass at ~5.5–6s real. If SPEED=2.8: pass1 at 19 t.u. → 6.8s. If SPEED=3.4: 5.6s. Inner swirl at SPEED=3.4: inner Ω(1.5)=3.23 rad/t.u. → rev per 1.94 t.u. = 0.57s real — very fast swirl; but only the INNERMOST stars (r<2); at r=3: Ω=1.63 → period 1.05s. Looks like a lively swirling core — I think it's fine and lively. Mid-disk r=6: Ω=0.79 → period 7.9 t.u. = 2.3s. Fine. I'll go SPEED = 3.3 t.u./s: pass1 ≈ 5.8s. Total 30s ≈ 99 t.u.: merged by ~85–90 ✓, then ~4s of remnant + continuing.

Hmm wait, but with drag gate at t=14–20 and pass1 at ~19: drag starts acting slightly BEFORE pericenter (t=17–19 exp... at t=17 gate=0.5, r≈~20?? inbound r at t=17: roughly 90→... near r~20–25: drag Δv there ~0.28*0.5*11*exp(−22/9)²... ≈0 — negligible ✓. Good: gate mostly matters near r<15 anyway. Actually simpler: keep gate but also the r² gaussian; combined they're safe.

Let me also double check pass1 Δv with c_d=0.28, λ=9 (gaussian exp(−(r/9)²)): near pericenter r 9.7: exp(−1.16)=0.313; duration weighted ~3 → Δv ≈ 0.28*12.4*0.313*3 = 3.26?! Too strong (v'=9.2 → E'=42.3−82.5=−40 → a=13.1, r_a=16.5): pass2 at P=2π√(2241/800=2.8)=2π*1.673=10.5 → t≈30 (8.8s): Δv≈0.28*10.1*0.31*3=2.6→v'=7.5→E'=28−82.5=−54→a=7.75→r_a=5.9?? with r_p~? L shrinks fast → pass3 quickly t≈37, then near-drag, merged by ~42–46 t.u. (13s). TOO FAST merger. Reduce: c_d=0.16: pass1 Δv=1.86→v'=10.5→E'=55−82.5=−27.5→a=16.7→r_a=23.8, P=15.9→pass2 t≈35.6: Δv=0.16*10.4*0.31*3=1.55→v'=8.9→E'=39.6−82.5=−42.9→a=11.2→r_a=12.7,P=2π√(1405/800=1.756)=8.33→pass3 t≈44: Δv≈1.3→v'=7.6→E'=28.9−82.5=−53.6→a=7.2→r_a≈4.7?? (r_p also shrinking now: L: 120−Σ(r_p*Δv_t): after 3 passes L≈120−9.7*4.7=74.5?? v_p 7.6 → r_p=9.8 — r_p stays ~10 again! a=7.2 with r_p=9.8?? IMPOSSIBLE (r_p ≤ a). My arithmetic is inconsistent because energy and L must both be tracked. Honestly, hand-computing coupled (E,L) drag evolution is error-prone. The near-drag (r<4) never engages since r_p stays ~10 → merger stalls at r~10 circular orbit decaying via continuous drag: at r=10, gaussian exp(−1.23)=0.29: rate = 0.16*4.62*0.29 = 0.214/t.u. → dr/dt = 2*10*0.214/4.62 = 0.93/t.u. → r 10→3: ~9 t.u. → merged ~t=53 (15.6s) ✓ acceptable! Then remnant phase 15.6→30s = long tail evolution. Hmm maybe slightly long in remnant, but tails keep evolving and camera keeps moving; plus I can extend second-galaxy effects... Acceptable. Actually you know, let me add a mild long-range drag component with different shape: a_d = −v * [c1*exp(−(r/9)²) + c2*exp(−(r/28)²)] with c2=0.012: at r=30: 0.012*e^{−1.15}=0.0038 → during tail-swinging phase (v~4–6) Δv/t.u. ~0.02 — negligible; at r=105 inbound: 0.012*e^{−14}≈0 ✓. The c2 term barely matters; skip it. Keep single gaussian + near-term.

Merger final look: cores orbit at r~2–3, decaying to ~1.5, tightly circling each other every ~2π√(1.5³·?)... ω = sqrt(800/r³) unsoftened = sqrt(800/3.4)=15.3 rad/t.u. — at r=1.5 softened a lot: with ε=2, inner motion is harmonic-ish: ω ≈ sqrt(800/( (r²+4)^{1.5}/r ))... at r=1: a=800/(5)^{1.5}=71.6 → ω=sqrt(a/r)=8.5 rad/t.u. → period 0.74 t.u. = 0.22s real — cores whirl rapidly around each other at close range — visually a single jittering blob — fine (sub-pixel-ish at 150 distance: 1.5 units/150 rad ≈ 0.01 rad ≈ 6 px apart max — a slight binary shimmer, actually adds life; or damp to near-zero separation: increase near-drag: k2=2.5*exp(−(r/2.2)²)?? at r=2: 2.5*0.59=1.48*v per t.u. — damping time 0.7 t.u.; at r=1: 2.5*0.81=2.0 → strong. They'll spiral to ~0.5–1 separation and keep tiny fast circle. OK, plus their GLOW overlap makes single core. Good.

One more consideration: when cores overlap (post-merger), the combined potential = sum of two bulge+halo at nearly same point → central potential doubles: stars near center orbit faster — fine. Central brightness doubles (additive) — the remnant core looks brighter — natural.

**Now, GPU sim vs CPU sim — sanity check on the GPU approach complexity.** I'll do GPU FBO. Components:
1. DataTexture init (pos, vel) — generated in JS with the galaxy builder. 256×256 RGBA float arrays: 65536*4 floats*4B = 1MB each — trivial.
2. Copy-to-RT initial pass (two small passes) OR use renderTarget from texture... simplest: `copyShader` pass rendering the DataTexture into rtPos[src] and rtVel[src]. Fine.
3. Sim passes per substep: vel update, pos update.
4. Render points sampling rtPos[src].

Number of programs: copy, velStep, posStep, pointsMat, bgPointsMat — 5 small shaders. OK.

Potential pitfall: reading and writing same texture — avoided via ping-pong ✓. Float RT filtering: NearestFilter ✓. Need `renderer.getContext().getExtension('EXT_color_buffer_float')` — three enables automatically? THREE WebGLRenderer checks for EXT_color_buffer_float when FloatType targets used; in r186 WebGL2, float render targets need that extension; typically available. I'll guard: if missing, fallback to HalfFloatType (positions up to ~300 with half-float mantissa 10 bits → at 200, ulp=0.125 — inner-disk stars at r~1.5 have ulp 0.001 ✓ fine actually! Half float precision at small values is good; problem only at large coordinates: tail stars at r=100: ulp=0.0625 — jitter of 0.06 at 100 distance invisible. Velocity values ~10: ulp at 10 = 0.00625 — Δv per step 0.3 fine; accumulate over steps? velocities get overwritten each step from pos/gravity — error doesn't accumulate in v (v computed fresh?? no, v integrated: v += a*dt — v accumulates; error per step ~ulp(v)=0.006 vs typical a*dt≈0.2 — 3% noise per step — acceptable jitter? Hmm, could cause slight diffusion in streaming tails. Float32 preferred; HalfFloat fallback acceptable. Fine.)

Also DataTexture with FloatType: needs `texture.internalFormat`? three handles RGBA32F upload from FloatType DataTexture in WebGL2 ✓ (uses internalformat RGBA32F automatically when type FloatType and format RGBAFormat — yes r186 handles).

Points geometry: I need per-vertex UV into the 256×256 texture. Build Float32Array position attribute (3 comps: u, v, 0) for 65536 vertices — index i → u=(i%256+0.5)/256, v=(floor(i/256)+0.5)/256. Plus aColor (3), aSize (1), aAlpha? pack alpha into aSize as vec2 attribute (size, alpha) — or aData vec4 (size, alpha, twinklePhase, twinkleAmp). Let me use two attributes: aColor (vec3), aProp (vec4: size, alpha, phase, twk). Vertex count 65536 × (3+3+4) floats = 650k floats = 2.6MB ✓.

Also cores' glow: separate Points with 2 vertices, updated each frame from CPU core positions (BufferAttribute update), big soft sprites with warm color + slight difference per galaxy. Size ~ world 26 & 20. Plus maybe an inner intense small one. Additive. These give the "bright core" bloom feel. Also render a tiny super-bright center: the star density already does it. Cores' glow sprites: make them subtle (the star bulge is the real core); glow sprite alpha low (0.10–0.18) with wide gaussian → soft halo around core. During merger they overlap → brighter single halo ✓. Also fade core glow slightly as separation shrinks?? They overlap additively → fine.

Hmm — one issue: core glow sprite size huge (26 world units) → point size px at dist 140: 26*864/140 = 160 px ✓ under caps typically. OK.

Also DISK HAZE particles (2,500 per galaxy, sizes 10–22, alpha 0.02): they'll show the disk plane as luminous fog, and get tidally drawn into tails — beautiful. And central haze concentration: bias haze r distribution inward (r = 13*pow(u,2.2)?? σ heavier center) with a few at r<2 for core glow support. Colors: A: warm ivory (1.0,0.88,0.72), B: cool ivory (0.85,0.9,1.05→clamp) subtle difference.

**Spiral arms visual strength:** additive blending of 30k stars: arms need contrast: arm stars 65%, inter-arm 35% with dimmer brightness (multiply brightness 0.55) → arms pop. Also arm stars slightly bigger & bluer (young stars): size 1.15×, color bluer; inter-arm: smaller, warmer (old disk population) — astronomically evocative ✓. Bulge: warm/bright. This gives real "population gradient" — warm yellow core → blue-white arms ✓ requirement.

**Camera path:** parametric over T=real time:
- angle θ_c(t) = θ0 + 0.055*t (rad/s → 30s: +1.65 rad ≈ 94°) — slow orbit ✓.
- elevation φ_c(t) = 0.32 + 0.10*sin(t*0.045+1)?? Let me: elevation drifts 0.30 → 0.52 rad (17°→30°) via smooth: φ = 0.30 + 0.22*smoothstep(0,30,t) + tiny breathing.
- radius R(t) = 168 − 34*smoothstep(0,26,t) + 10*sin(t*0.21+2)?? breathing ±10 might feel wobbly; make it gentle ±6. Also during late phase (t>22) very slowly pull out to show remnant + tails: R = 134 + 0.8*(t−26) for t>26.
- Target: origin; maybe slight offset toward the action midpoint: mid = (coreA+coreB)/2 = barycenter ≈ origin exactly. So origin ✓. Slight target bob: none.
- FOV 50. Near 0.1 far 4000 (background stars at 1500–2600 ✓ inside far).

Camera roll? A tiny roll adds cinema but complicates framing; skip (up = Y).

Also camera should avoid being edge-on early (tails best at intermediate inclination) ✓ 17°→30°.

**HUD:** top-left:
```
T +047.3 Myr
ΔCORE 38.2 kpc · SEP VELOCITY 212 km/s
PHASE — FIRST APPROACH
```
Map: 1 length unit = 1.25 kpc (disk 12 → 15 kpc ✓). Velocity: v units → km/s: v_circ ≈ 4.6 ≈ 220 km/s → 1 v-unit ≈ 48 km/s. Show "V_REL 287 km/s". Phase logic:
- t < pass1−2: "FIRST APPROACH"
- until cores separating & sep>15 after pass1: "TIDAL BRIDGES · TAIL EJECTION" — detect via time & separation: phase by sim time thresholds known-ish? Since physics emergent-ish, use thresholds on sim time (t<18: approach; 18–30: first passage; 30–42: tails; 42–55: second passage...; >68: coalescence; >78: remnant). But pass times depend on drag... deterministic enough (fixed ICs). I'll gate on core separation S(t) and t: 
  - phase = APPROACH if t < t_p1_guess−3 && S decreasing?? simpler: use S: S>55 & t small → APPROACH; S<18 first time → FIRST PASSAGE (flag); after pass1 flag & S rising >20 → TIDAL TAILS; second dip S<10 → SECOND PASSAGE; S<5 sustained → COALESCENCE; t>85 → MERGER REMNANT. I'll implement small state machine with flags — robust to timing shifts.

Actually simpler robust: track pericenter events: count minima of S. state: pre (before 1st min), then after each minimum increment. Labels: ["FIRST APPROACH","FIRST PASSAGE — TIDAL BRIDGES","TAIL EXPANSION","SECOND PASSAGE","RAPID DECAY","COALESCENCE","MERGER REMNANT"] — choose by pass count + S magnitude. Fine.

Keep HUD minimal: line1: time Myr big-ish; line2: sep + rel velocity; line3: phase. Small caps, letterspaced, 10–11px, opacity 0.8, thin left border accent? I'll style: no border, just text with a small tick mark. Color: pale cyan-white on black, monospace.

Bottom-right caption: "RESTRICTED N-BODY · 65,536 PARTICLES · SOFTENED GRAVITY" tiny, 35% opacity. Bottom-left: title "COLLIDING SPIRAL GALAXIES" + sub "restricted three-body simulation" — gives cinematic title card. Maybe fade the title out after 8s (CSS animation) so it doesn't distract — nice touch: title fades to 0.25 opacity? Or fades out entirely at 10s. I'll fade out to 0 over 2s at t=9s.

**Now write the galaxy builder.**

```
function buildGalaxy(target, offset, params):
  params: center (vec3), spinBasis (three Euler applied), nStars, nHaze, arms (2 or 3), pitch, armColorShift, phase0, dir(spin sign)
```
Local frame: start with disk in XY plane?? I'll build in local coords: disk plane = local XZ? Let me build disk in local X–Y plane with z as vertical (easier mentally: arms in XY, thickness z), then apply rotation matrix R_galaxy to orient, then translate.

Star generation (i in [0,nStars)):
- u = random(); r = R_MAX * pow(u, 1.7)?? Let me reconsider: r = 12 * pow(u, 1.7) gives median r = 12*0.5^{1.7}=12*0.307=3.7 — half the stars within 3.7 — good central concentration.
  Hmm but I also want plenty of outer-disk stars for tails (tidal tails pull from outer disk — outer stars are easiest to strip). With r^{−1.4} surface profile, outer disk (8–12) has ~? N(r>R)= (1−(r/12)^{...}) CDF: P(r<x) = x^{1.7}/12^{1.7}... P(r>8)=1−(8/12)^{1.7}=1−0.53=0.47?? (8/12)^{1.7} = (0.667)^{1.7}=e^{1.7*ln0.667}=e^{−0.689}=0.502 → 49.8% beyond r=8 — plenty ✓. Hmm wait that means density isn't that centrally concentrated; but with bulge stars added separately, fine. Actually reconsider: pow(u,1.7) with u uniform: CDF(r) = P = (r/12)^{1/1.7}?? NO: if r = 12 u^{1.7}, then u = (r/12)^{1/1.7} → CDF P(r<r*) = (r*/12)^{0.588}. P(r>8) = 1−(0.667)^{0.588}=1−0.779=0.22. dN/dr ∝ r^{0.588−1}=r^{−0.41}, σ∝r^{−1.41} ✓ (matches earlier). OK P(r>8)=22%, P(r>10)=1−(0.833)^{0.588}=1−0.896=10.4%. Good.
- Bulge vs disk: first nBulge = 22% of stars: Plummer sphere: sample: radius: Plummer CDF: q = m: r = a_b / sqrt( (1−q²)^{... } Plummer: p(r) ∝ r²/(r²+a)³... sample via: r = a_b * (q²)^{... Standard: r = a_b / sqrt(X^{-2/3} − 1) where X uniform (0,1]. With a_b=1.6, cap r at 6 (tail of distribution). Velocity: for visual stability give circular speed in RANDOM orientation (each bulge star orbits in its own random plane) → spheroid with mild random streaming; plus slight net rotation 20%: v = v_c(r_local... but potential includes halo — for bulge stars at r<2: v_c ≈ sqrt(GMb r²/(r²+εb²)^{1.5} + GMh r²/(r²+εh²)^{1.5}) ≈ using GMb=90: at r=1: 90/(2.56+1)^{1.5}=90/6.74=13.4+halo 310/(82)^1.5=310/742=0.42 → v=3.69. Escape at r=1: 2*(90/√3.56 + 310/√82) = 2*(47.7+34.2)=164 → v_esc=12.8 — v=3.7 well bound ✓. Random-plane circular orbits stay at ~constant r ✓ (Kepler-ish in softened potential — closed-ish orbits precess slightly, fine). This yields a stable glowing spheroid. To avoid bulge stars drifting into a flat disk over time (precession randomizes) — fine either way.
  Actually better look: 60% bulge stars: near-isotropic velocities with magnitude ~0.55*v_c(r) in random directions (pressure-supported puff — each star on a bounded orbit within potential; the cloud will slowly mix but stay ~spheroidal since orbits are rosettes in spherical potential ✓). And 40%: rotating strongly. Either way stable-ish. I'll do: velocity = tangential-ish: random unit vector × (0.4–0.8 v_c) + net spin component. Simplest: v = (random unit vec)*vc*rand(0.35,0.75) + spinDir*vc*0.35. OK.
- Disk stars: 78%.
  - arm assignment: with prob 0.62: arm star: choose arm m: θ = φ_m + pitchLog(r) + gauss()*σθ(r) where σθ = 0.16 + 0.012*r?? At r=10: 0.28 — arms ~±0.3 rad wide at edge — reasonable. Also occasionally (10% of arm stars) big scatter (σθ*2.5) for feathery spurs.
  - else: field star: θ uniform, brightness lower.
  - r jitter: r *= (1 + gauss()*0.06); min r 0.9.
  - z: gauss()* (0.16 + 0.028*r) → at r=10: σz=0.44; plus arms slightly thinner (multiply 0.8).
  - velocity: v_c(r) from combined potential (JS mirror of shader): 
    vc(r) = sqrt( GMb*r²/(r²+εb²)^1.5 + GMh*r²/(r²+εh²)^1.5 )... careful: v_c² = r * |a| = r*Σ GM r/(r²+ε²)^{1.5} = Σ GM r²/(r²+ε²)^{1.5} ✓.
    tangential dir: spin sign × (−sinθ, cosθ, 0) in local frame. Magnitude vc*(1+gauss*0.03) + radial component gauss*0.05*vc?? small: vr = gauss()*0.04*vc; vertical vz = gauss()*0.05*vc*(z thin).
    Hmm also add slight arm-related velocity perturbation? skip.
- Colors:
  - bulge: warm: base (1.0, 0.78, 0.48) ± jitter → some (1.0,0.85,0.6); brightness 0.9–1.3 (many stars → additive saturation).
  - disk arm stars: color lerp by radius: inner (r<3): (1.0,0.88,0.62); mid (5): (0.92,0.93,0.98); outer (10+): (0.62,0.76,1.0); plus 8% of arm stars: hot blue (0.5,0.65,1.2 clamped) brightness 1.4, size 1.3 (O/B stars in arms ✓).
  - field/inter-arm: warmer: lerp similar but shifted warm: (0.98,0.86,0.6)→(0.8,0.85,1.0) with radius; brightness 0.6–0.8.
  - size: base 0.55–0.95 random, arm stars ×1.1, hot ones ×1.4, bulge 0.5–0.8 (small & numerous).
  Also a tiny fraction (1.5%) "giants": size 1.6–2.2, brightness 1.6 — sparkly foreground feel.

- Haze particles: nHaze per galaxy: r distribution: r = 13.5*pow(u, 2.4)?? median: 13.5*0.5^{2.4}=13.5*0.19=2.56 — concentrated ✓; some large r: P(r>10)=1−(0.74)^{0.417}?? u=(r/13.5)^{1/2.4}: P(r<10)=(0.74)^{0.417}=0.881 → 12% beyond 10 ✓. z σ ~ (0.5+0.05r) slightly thicker. size: 9 + 16*u2² (few huge); alpha 0.018–0.05 (inner ones slightly higher). Color per galaxy tint. Velocity: vc like disk stars (they co-rotate ✓ keeps haze disk-like, then tails sweep haze too ✓). Arms influence? haze follows smooth disk (θ uniform) — but to give the arms a glow-lit feel, add 40% of haze biased to arms too — nice: arms get soft glow beneath crisp stars → grand-design luminous arms ✓. Yes do that.

Galaxy orientation: A: build local, then rotate: I want disk angular momentum ≈ orbital L (−y) with tilt. Local disk L = +z (if spin counterclockwise in XY when viewed from +z... choose spin s=+1 → L_local=+z; then rotate local +z → target direction. Galaxy A: target L dir: normalize(−y tilted): rotate by Euler: rx = +0.42 rad about X: +z → (0, sin0.42?, ...) Let me not overthink: I'll define per galaxy a quaternion from two rotations: qA = Euler(0.45, 0.0, 0.35) applied to identity — disk normal becomes R*(0,0,1). As long as resulting L·(−y) > 0.5 → mostly prograde. Let me compute: Euler order XYZ: R = Rx(0.45)Ry(0)Rz(0.35)?? three Euler default 'XYZ' applies as R = Rz then... three's Euler XYZ: rotation matrix = Rx*Ry*Rz? In three.js, Euler order 'XYZ' means R = Rx(x) * Ry(y) * Rz(z)?? Actually three composes as R = Rz? Let me avoid confusion: I'll construct basis vectors manually: for each galaxy define normal vector n (unit) and a reference in-plane axis, compute orthonormal basis (e1, e2, n) via cross products. Spin direction s: velocity tangential = s * vc * normalize(cross(n, pos_local)) — for spin with L = s*n. Set:
- A: n_A = normalize(vec3(0.25, −0.92, −0.30))?? want n·(0,−1,0)≈0.92 ✓ prograde (L≈−y). 
- B: n_B = normalize(vec3(−0.55, −0.62, 0.56)): n·(−y)=0.62 → inclined 52° from orbital plane — moderately inclined prograde — different look ✓. Hmm or make B partially RETROGRADE for contrast (retrograde galaxies develop weaker tails but a nice bridge)... The classic Antennae: both prograde-ish. Variety: A strongly prograde (long tails), B inclined prograde (broader fan). Keep both prograde.
- e1: pick arbitrary vector not parallel to n: e1 = normalize(cross(n, arbitrary)), e2 = cross(n, e1).

Positions of local coords: p_world = C_g + e1*x + e2*y + n*z. Velocity: v_world = v_x*e1 + v_y*e2 + v_z*n where local tangential for spin s: for star at local (x,y): r̂=(cosθ, sinθ); tangential (counterclockwise looking down +z... velocity dir for spin s: t̂ = s*(−sinθ, cosθ, 0) → angular momentum along +z*s → L_world = s * n ✓.

Galaxy initial centers: A at (−52.5, 0, 0), B at (52.5, 0, 0). Core velocities v_A = (1.505, 0, −0.575)*?? wait v_A = −v_rel/2 where v_rel = (−3.01, 0, 1.15): v_A = (1.505, 0, −0.575), v_B = (−1.505, 0, 0.575) ✓ (in JS: compute from constants).

Check orbital plane is X-Z (y=0) ✓; camera orbits with elevation about origin in this plane-ish region ✓.

Wait — v_t tangential direction: v_rel=(−3.01, 0, 1.15): L = r×v = (105,0,0)×(−3.01,0,1.15): L_y = r_z*v_x − r_x*v_z = 0 − 105*1.15 = −120.75 → L = (0,−120.75,0) ✓ as computed. Both galaxy spins n ≈ −y ⇒ prograde ✓.

**Pericenter & disk overlap:** pass1 r_p≈9.7: disks radius 12, centers 9.7 apart → heavy overlap of outer disks → strong bridge+tails ✓. Inclinations mean actual star-core distances vary ✓.

**Numbers final:**
- GMb=90, εb=1.6 → εb²=2.56
- GMh=310, εh=9 → εh²=81
- Per galaxy total 400; μ_pair=800.
- Disk Rmax=12, bulge a=1.6 capped 5.
- vc(3)≈? computed 4.89 earlier?? recompute: bulge: 90*9/(9+2.56)^{1.5}: (11.56)^{1.5}=39.3 → 20.6; halo: 310*9/(90)^{1.5}=2790/854=3.27 → v²=23.9, v=4.89 ✓.
- dt: adaptive substeps: acc = min(realDt,0.05)*SPEED; nSub = clamp(ceil(acc/0.03), 1, 4); h = acc/nSub. GPU: nSub passes. At 60fps: acc=3.3/60=0.055 → nSub=2, h=0.0275 ✓. At 120fps: acc=0.0275 → nSub=1, h=0.0275 ✓ consistent. At 30fps: acc=0.11 → nSub=4, h=0.0275 ✓. 

- Max speed clamp in shader: v = v * (1/(1+|v|*dt/60))?? simpler: if (speed2 > 3600) v *= 60/speed... use soft clamp: sp = length(v); f = 1.0/max(1.0, sp/55.0)?? v *= min(1, 55/sp). eh fine.

**Star brightness & additive saturation estimate:** 30k stars/galaxy; near core, hundreds of stars within a few px → saturation to white ✓. Arms: maybe 3–8 stars per px overlapping with brightness ~0.3 each → 1–2.5 → bright ✓ with gaussian falloff giving glow. Should look lush. Global exposure multiplier uniform uExposure ≈ 1.0–1.3; I'll tune ~1.15.

**Background stars:** 2400 pts, positions on sphere shell radius 1400–2400 (uniform on sphere: normalize gaussian vec). Sizes: attribute 0.8–2.2 px (no attenuation: gl_PointSize = size * pixelRatio? size in px scaled by pixelRatio uniform... renderer handles buffer scaling? gl_PointSize in device px; multiply by uPixelRatio ✓). Colors: mostly white (0.75–1.0), 20% warm, 20% blue-ish, brightness 0.25–0.9, few (2%) bright 1.3 with size 2.6. Alpha gaussian profile same shader-ish; separate simple material with own vertex/frag (no texture sampling — static positions attribute!). bg points: static BufferGeometry with real positions ✓. slight parallax as camera orbits (they're at finite radius 1400+ → mild parallax, nice depth) ✓. Maybe slow rotation of bg sphere for subtle life: rotate bg points object at 0.002 rad/s — imperceptible drift, adds polish. Also subtle twinkle for bg: skip or very subtle sin — keep, cheap.

**Extra "cinematic" polish candidates:**
- Lens-flare-ish anamorphic streak on cores? Could add horizontal streak sprite on cores (thin wide gaussian): a second core sprite scaled x×?? Points can't be anisotropic easily (gl_PointCoord square). Could use a second Points layer with a fragment that multiplies profile by exp(−pc.y²*40) → horizontal streak! gl_PointCoord gives y → anisotropic gaussian = streak ✓. Nice cinematic touch: faint warm streak across each core, alpha 0.05. Hmm — tasteful? Small, subtle: yes, adds "cinematic scientific viz" feel. I'll add streak layer for cores only (2 points, size ~34, alpha low, bluish-white). Keep VERY subtle.
- Vignette + film grain? Grain via CSS? skip grain (can cheapen). Vignette subtle ✓.
- Slow-motion at first pericenter?? Time dilation: SPEED *= (0.55 + 0.45*smoothstep(...)) around pass1 — cinematic ramp! Risky for physics pacing but purely time-mapping (no physics change) — the passage slows to savor the slingshot, then speeds up. Nice: implement uSpeed(t_real): base 3.3; near pass1 real-time window (4.5–7.5s): dip to 2.0; near pass2 (~10.5–13s): dip 2.3; hmm but pass2 timing in real time depends on integrated physics... I can detect proximity via core separation rate: slowmo factor = 1/(1+2.2*exp(−((S−9)/4)²))?? Slow when cores near close approach: factor = 1 − 0.62*exp(−((S−9.5)/3.5)²) → at S=9.5: factor 0.38 → dramatic slowdown at EACH passage (self-triggering!) — but post-merger S~1.5 → factor ~0.38 forever → sim crawls after merger — bad. Gate by t: slowmo = 1 − 0.6*exp(−((S−9.5)/3.5)²) * fadeout(t>70)?? After merger S≈1.5, exp(−((1.5−9.5)/3.5)²)=exp(−5.2)=0.0055 → factor 0.997 ✓ NO problem! exp kills it. At S=6: exp(−0.367)=0.69→factor 0.585; S=9.5: 0.4; S=13: exp(−0.37)=0.69?? (13−9.5=3.5 → exp(−1)=0.368) → 0.78; S=20: exp(−3.06)=0.047→0.97. So slowdown only during close passages ✓✓. Also final coalescence S<4: exp(−(5/3.5)²)... S=2: exp(−4.16)=0.0156 → 0.99 ✓. So each passage gets a cinematic ~0.4× ramp. But: passage duration in sim ~3 t.u.; at factor 0.4 that's 3/0.4... real duration = ∫dt_sim/factor — the ramp doubles-triples the screen time of the sling — good drama. Also maps Myr label consistently (label counts sim time — slowdown just shows slower Myr progression — correct!). ✓ Implement: effSpeed = SPEED * (1 − 0.62*exp(−((S−9.5)/3.5)²)). Also make sure it can't stall physics: min factor 0.38 ✓ fine.

  Hmm, but there's subtlety: the slowmo triggers when S crosses ~9.5 — including during final circular decay at S≈2 (no, exp handles) and during the CIRCADPOST merger S~2 fine. During second pass S dips to ~9.7 again → slowmo again ✓ desired. Third+ passes S~9.8 too → every passage gets savored. OK but maybe reduce depth after first: depth = 0.62 * clamp(1.6 − passCount*0.25,...)? Eh — keep uniform 0.55; simpler, consistent.

- Also: make camera radius react slightly to tails extent? Skip — scripted R is fine (tails reach ~50–70 < R 134 ✓ framed).

**Physics correctness for stars — the initial velocities use host potential; during encounter, companion potential perturbs ✓. After merger, stars orbit combined double potential ✓.**

**Potential mismatch check:** shader uses cores' CURRENT positions each substep (uniforms updated per substep? — I update uniforms before EACH substep pass: core positions integrated in JS at substep granularity: for each substep: first update core pos/vel by h (semi-implicit + drag), set uniforms, then run vel pass & pos pass with that h. Slight ordering asymmetry — fine.)

Hmm wait, actually: star update uses core position at midpoint ideally; per-substep sync is plenty.

**Core integration (JS):**
```
// relative vector d = coreB - coreA
acc on relative: a_rel = -mu * d/( (|d|²+ecc²)^1.5 )  [motion of B relative to A]
+ drag: a_rel -= dragC(t,S) * v_rel * exp(-(S/9)^2) + near: -2.2*v_rel*exp(-(S/2.2)^2)
v_rel += a_rel*h; d += v_rel*h;
coreA = -d/2; coreB = +d/2; vA = -v_rel/2; vB = +v_rel/2.
```
Note: with equal masses and barycenter at origin ✓ (initial d=(105,0,0), v_rel=(−3.01,0,1.15) → barycenter static at origin exactly ✓ (COM momentum zero)).

Drag gate: dragGate = smoothstep(13, 19, simT) — implemented in JS.

c_d final: let me settle c_d = 0.17, λ_gauss = 9 (i.e., exp(−(S/9)²)), near drag k2 = 2.4*exp(−(S/2.3)²). Expected: pass1 Δv ≈ 0.17*12.4*0.31*3 ≈ 1.97 → v'≈10.5 → r_a ≈ 24 (as computed) → pass2 at t≈19+16=35 (10.3s) → Δv≈0.17*10.4*0.31*3=1.64 → v'≈8.7 → E'=37.8−82.5=−44.7 → a≈11.1 → r_a≈12.5, P≈8.3 → pass3 t≈43.5: Δv≈0.17*9.2*0.31*3≈1.46→v'≈7.7?? v_p3: E=−44.7: v_p=sqrt(2(82.5−44.7))=8.7 — consistent; Δv 1.46 → v'=7.2 → E'=25.9−82.5=−56.6 → a=6.6 → r_a≈3.4?? if r_p stays ~9.8 impossible (r_p<a) → my r_p bookkeeping is off because L shrinks: ΔL per pass = r_p×Δv_t ≈ 9.7*1.4 = 13.6: L: 120→106 (pass1: Δv mostly along v (perpendicular-ish? drag opposes velocity → removes both radial? at pericenter v mostly tangential → ΔL≈r_p*Δv ✓) → L: 120→106→92→79 → r_p = L/v_p: pass2: 106/10.4=10.2; pass3: 92/8.7=10.6; pass4: 79/7.2=11.0?! r_p GROWS?? That can't be — drag reduces L but also E... circularization: yes! Drag circularizes: r_p rises toward r_a falling; they meet at circular orbit radius ~ r_p≈r_a≈?? energy: E=−44.7 → circular r = 800/2|E|... for circular orbit at r: E=−μ/(2r) → r = μ/(2|E|) = 800/89.4=8.9. L_circ = sqrt(μ r)= sqrt(800*8.9)=84.4 ✓ ≈ 79 close. So after pass3, orbit ≈ circular r≈9, decaying via continuous drag: rate: dr/dt = −2 r c_d v_c exp(−(r/9)²)/?? dv/dr relation: for near-circular: v²=μ/r → dE/dr = μ/(2r²); dE/dt = v·a_d = −c_d v² exp(−(r/9)²)·v?? a_d = −c_d v exp(...)*v → dE/dt = −c_d v² exp = −c_d (μ/r) exp. dr/dt = dE/dt / (dE/dr) = [−c_d μ/r * exp] * [2r²/μ] = −2 c_d r exp(−(r/9)²). At r=9: −2*0.17*9*0.368=−1.13/t.u. → r: 9→3 in ~7 t.u. (with exp growing as r shrinks: faster; roughly 5–6 t.u.) → circularized ~t=44+... wait pass3 at 43.5 → circular r≈9 by then; decay to near-drag zone (r<4, near-drag exp(−(4/2.3)²)=0.25*2.4=0.6 strong) by t≈50 → coalescence ~t≈52–55 (16s real) ✓. Then remnant evolution 16→30s ✓. 

But hmm — wait, pass1 r_a≈24: between t=19 and 35 the cores swing out to 24 — tails from pass1 have 16 t.u. (4.7s) to develop before pass2 — good pacing. ✓ 

BUT all this depends on my Δv estimates which are crude (weighted duration 3 t.u. guess). If actual Δv is 2× my estimate, merger happens by t≈35 (10s) — still acceptable pacing-wise (a bit quick but fine). If Δv is 0.5×, merger at t≈70 (20.6s) — also fine. Either way, we get: approach → pass → tails → (passes) → merger within window, robust to factor-2 errors in my drag estimate. This robustness matters more than exact timing. Also the slowmo near passages adds savoring regardless. 

One risk: if drag over-strong at pass1, cores barely swing out (r_a~10) → second pass immediate → rapid merge by t≈30: still shows everything, just compressed. Mitigate: pick c_d = 0.15 conservative and gate drag to start slightly AFTER... no — gate 13→19. Also add floor: after pass1, ensure r_a ≥ ~18?? Can't easily. Accept.

Also: guard against stars falling INTO ε too deep: softened ✓ max a bounded ✓.

**Tails forming check:** outer disk stars (r 8–12) at pass1: companion core passes at distance ~ (9.7 − their projected...) → they get yanked toward/behind companion; prograde outer stars get boosted → tail; inner form bridge. With v_p=12.4 vs local vc 4.6 — strong impulse ✓ tails to r~30–60 over following 10–20 t.u. ✓ classic Antennae look. 

**Rendering order & materials:**
- scene.background = new THREE.Color(0x02030a)?? very dark blue-black. Actually pure near-black: #04060c. Hmm "dark starfield background" — near-black ✓.
- bgStars: renderOrder 0, additive, depthWrite false, depthTest false.
- galaxy points: renderOrder 2.
- core glows: renderOrder 3.
- All additive → order irrelevant visually (additive commutes) except vs background (bg adds too) — all commute ✓. Just disable depth entirely.

**Resolution scaling:** renderer.setPixelRatio(min(devicePixelRatio, 2)); on resize update camera aspect, uPerspectiveScale uniform (used for point sizing), renderer size. Points size uniform: uProjScale = (renderer height in device px) * 0.5 / tan(fov/2 rad)?? gl_PointSize = aSize * uProjScale / (-mvPosition.z). With height in device pixels (drawingBufferHeight) — use renderer.getSize → CSS px * pixelRatio. I'll compute: const hPx = size.y * pixelRatio; uProjScale = hPx / (2*tan(fov/2)). At h=1080, fov 50: tan25°=0.466 → 1080/0.932=1159. Star size 0.7 at dist 140: 0.7*1159/140 = 5.8 px. Hmm slightly big; sizes 0.35–0.9 typical → 2.9–7.4 px. Bulge small stars 0.4 → 3.3px ✓. Fine — I'll tune base sizes: stars 0.32–0.85, giants to 1.5, haze 9–24, core glow 22–30. At closest camera approach R≈134–150. Tail stars at r=60: dist from cam ~90–180: px = 0.6*1159/120≈5.8 ✓.

Point size floor: gl_PointSize < 1 → flicker/aliasing: clamp max(size, 1.0)?? For tiny far stars clamp to ≥1.1 px and scale alpha by (size_px/1.1)² to conserve flux?? Simple: px = max(px, 1.05); slight brightness boost when clamped not needed. Fine.

**Alpha/twinkle:** twinkle: b *= 0.82 + 0.18*sin(uTime*(1.5+2.5*fract(phase*7)) + phase*40)?? keep subtle: amplitude 0.15, freq per-star 0.5–2 Hz. Only apply to stars not haze (twk=0 for haze).

**Sim shader — velocities for SPARE particles:** parked at p=(3e4,0,0)? a≈0 ✓ v=0 ✓. They render with alpha 0 (their aProp alpha=0) → invisible ✓ but still processed — negligible.

**gl_VertexID approach vs attribute:** using `position` attribute storing uv — three.js Points needs position; set frustumCulled=false. In vertex shader: `vec2 uv = position.xy;` — but three also computes... fine. BUT: three.js WebGLProgram will define attribute vec3 position automatically ✓ (built-in). I'll name extra attrs aColor, aProp.

**Ping-pong in code:**

```
const TEX = 256, N = TEX*TEX;
let rtP = [], rtV = [], idx = 0;
createRT(): new THREE.WebGLRenderTarget(TEX, TEX, { type: FloatType, format: RGBAFormat, minFilter: NearestFilter, magFilter: NearestFilter, depthBuffer: false, stencilBuffer: false, wrapS/T: Clamp });
```
Init: fill posData/velData Float32Array; make DataTextures (posInitTex, velInitTex); render copy pass into rtP[0], rtV[0]. rtP[1], rtV[1] allocated empty.

Sim step function step(h):
```
// cores already advanced by caller per substep with h; uniforms set:
velMat.uniforms.tPos.value = rtP[idx].texture; tVel = rtV[idx].texture; dt = h; cores uniforms set;
renderer.setRenderTarget(rtV[1-idx]); renderer.render(simScene, simCam); // simScene holds quad with velMat
posMat.uniforms: tPos=rtP[idx], tVel=rtV[1-idx](new), dt=h;
render into rtP[1-idx];
idx = 1-idx;
```
Two materials on same quad: swap mesh.material before each render ✓.

**Points material vertex shader:**
```
uniform sampler2D uPosTex; uniform float uProjScale; uniform float uTime;
attribute vec3 aColor; attribute vec4 aProp; // size, alpha, phase, twk
varying vec3 vColor; varying float vAlpha;
void main(){
  vec4 P = texture2D(uPosTex, position.xy);
  vec4 mv = modelViewMatrix * vec4(P.xyz, 1.0);
  float size = aProp.x; float alpha = aProp.y;
  float tw = 1.0 - aProp.w * (0.5 + 0.5*sin(uTime*(0.6+aProp.z*1.7)+aProp.z*37.0));
  // gl_PointSize
  float ps = size * uProjScale / max(1.0, -mv.z);
  gl_PointSize = max(ps, 1.1);
  float dim = ps < 1.1 ? (ps/1.1)*(ps/1.1) : 1.0; // conserve brightness for clamped tiny points? 
  gl_Position = projectionMatrix * mv;
  vColor = aColor * tw * dim;
  vAlpha = alpha;
}
```
Hmm dim factor: when clamping size up, brightness should NOT increase — multiply color by min(1, (ps/1.1)^2) ✓ included.

Fragment:
```
varying...
void main(){
  vec2 q = gl_PointCoord*2.0 - 1.0;
  float d2 = dot(q,q);
  if (d2 > 1.0) discard;
  float g = exp(-d2*3.0);       // main gaussian: at edge d2=1 → e^-3=0.05
  g += 0.16*exp(-d2*1.1);       // soft halo
  gl_FragColor = vec4(vColor * g * vAlpha, 1.0);
}
```
CustomBlending ONE ONE. Brightness tuned via aColor magnitude (I'll fold brightness into aColor at build: aColor = color * brightness * globalExposure).

Wait — additive with alpha ignored: gl_FragColor.a=1 with ONE/ONE adds rgb only ✓.

Haze particles same shader (big size, low alpha ✓ via aProp.y).

Core glow: separate Points (2 verts) with its own material: uniforms uPos (vec3 array?) — simpler: update position attribute each frame (2 vertices). Same profile shader but bigger halo: g = exp(-d2*2.2)*0.5 + 0.35*exp(-d2*0.7); color warm; alpha uniform per core? encode per-vertex color+alpha attribute. Streak layer: third Points with fragment: g = exp(-q.x*q.x*2.0) * exp(-q.y*q.y*28.0)?? horizontal streak: narrow in y, wide in x ✓ alpha low (0.05), size ~30. Blends additive. Subtle.

Core glow update: positions attribute .needsUpdate. Colors: A warm (1.0,0.82,0.6), B slightly cooler (0.85,0.85,1.0)?? B galaxy color scheme slightly bluer overall. Alpha ~0.35 each with profile peak ~0.5 → adds gentle halo.

Hmm — also during approach, cores are INSIDE their star swarms (bulge) — glow adds soft bloom around each bulge ✓.

**Camera implementation:**
```
camAngle += ... computed from t: ang = 0.62 + 0.052*t;  (start angle chosen so galaxies' separation axis (x) is viewed at pleasing oblique: camera at angle 0.62 rad from x-axis in XZ?? position: x=R cosφ_elev cos(ang), z=R cosφ sin(ang), y=R sinφ_elev. 
elev = 0.34 + 0.16*smoothstep(6,26,t) → 0.34→0.50 rad (19.5°→28.6°).
R = 172 − 30*smoothstep(4,24,t) + 7*sin(t*0.19+1.7) → ~172→142±7.
```
Then camera.position.set(...); camera.lookAt(0, 1.5, 0)?? slight y offset target? lookAt(origin) fine.

Also slight lateral drift of target toward the "action": during tails phase tails asymmetric — target origin fine.

Let me double check framing early: galaxies at ±52.5 with disk 12 → extent ±64.5; camera R=172, elev 0.34 → distance to each galaxy ~172±: angular size: galaxy disk radius 12 at distance ~165 → radius ~12*1159/165?? on-screen: half-height of view at dist 165: 165*tan(25°)=77 → disk 12/77 ≈ 15% of half-height — two galaxies nicely framed with space between ✓ tails will grow into frame ✓. At pass1 tails extend ±40 → within 77 ✓. Later R=142, tails 60 → 60/(142*0.466=66) = 0.9 half-height — nearly fills frame vertically ✓ dramatic but framed; horizontal half-FOV larger with wide aspect ✓. Good.

fov 50 might crop long tails at the end; tails elongated along original orbital directions... acceptable; R end 142 + breathing. Maybe end R 150: R = 172 − 24*smoothstep(4,26,t) = 148 end ±7. OK: R(t) = 172 − 26*smoothstep(4,26,t) + 6.5*sin(t*0.16+1.7). 

**Time label mapping:** MyrPerTU = 5.0 → at 3.3 t.u./s → 16.5 Myr per real second → 30s = 495 Myr ✓ nice (label shows e.g. "T + 348 Myr"). Show one decimal? "T + 0347 MYR" — I'll show integer with pad: `t = 347 Myr`. Plus "Δ 41.3 kpc" and "v_r 213 km/s" maybe combined line. Format: 
```
04:23.7  ← no, not needed
T  = 347 MYR
Δ  = 41.3 KPC   ·  V = 187 KM/S
PHASE · TIDAL TAILS
```
Units lowercase/uppercase mix: use uppercase small labels with letterspacing, values in brighter color. 

Phase names:
1. "QUIESCENT APPROACH" (t < 15 t.u.)
2. "FIRST PASSAGE" (around pass1: S<14 first descent, until S>18 rising... implement: state machine on S minima)
3. "TAIL EJECTION / BRIDGES" 
4. "SECOND PASSAGE"
5. "RAPID INSPIRAL"
6. "COALESCENCE"
7. "MERGER REMNANT"

State machine:
```
minimaCount=0; prevS; lastMinS; descending flag
each frame: if S < prevS-ε... track: if descending && S > prevS → minimum at prevS (count++). 
labels: count 0: if t<8 "FIRST APPROACH" else "FINAL APPROACH"; count1: S<12? "FIRST PASSAGE"→ after minimum, S>20: "TIDAL TAILS EXPANDING"; count2 minima: during S<12 "SECOND PASSAGE" else "SECOND ENCOUNTER — SHELLS FORMING"; count≥3: S>4? "RAPID INSPIRAL" : "COALESCENCE"; if S<3 && t>50: "COALESCENCE"; t>62: "MERGER REMNANT".
```
I'll write a compact heuristic: use passage count n and current S:
- n==0: "FIRST APPROACH"
- n>=1: if S < 12: passage labels by n: 1→"FIRST PASSAGE · BRIDGE FORMING", 2→"SECOND PASSAGE", ≥3→"FINAL PASSAGES"
  else: n==1: (t < 30?) "TIDAL TAILS · BRIDGE" ; n==2: "TAILS SWEEP OUT"; n>=3: S>5? "RAPID INSPIRAL" : ... 
- S < 3.5 && n>=3: "COALESCENCE"
- t > 64: "MERGER REMNANT"
Fine.

**Startup:** everything synchronous: build arrays (65k particles: generation loop with gaussian — fast, <100ms), init textures, first render. Title fade-in CSS animation. 

**Now — write the code.** Structure inside one HTML:

```html
<!DOCTYPE html><html><head><meta charset><meta viewport><title>...
<style> body{margin:0;overflow:hidden;background:#020409;color:#cfe2ff} canvas{display:block}
#hud{position:fixed;top:22px;left:24px;font:11px/1.7 ui-monospace,'SF Mono','Cascadia Code',Menlo,Consolas,monospace; letter-spacing:.08em; ...}
#title bottom-left, fades
#credit bottom-right
#vignette overlay
</style></head><body>
<div id="vignette"></div>
<div id="hud">...</div>
<div id="title">...</div>
<div id="caption">...</div>
<script type="module"> import * as THREE from 'three'; ... </script>
```

HUD design details: 
- #hud: pointer-events none; color #9fb8d8; text-transform uppercase; small. Value spans brighter #e8f1ff.
- Title: bottom-left: "SPIRAL GALAXY COLLISION" — styled with letterspaced thin; sub: "restricted three-body simulation · 65,536 test particles". Fade out via JS at t>9s (add class).
- Bottom-right caption: " softened gravity · N=65536 " small dim.

Actually keep bottom-right minimal: "TIDAL TAILS EMERGE FROM RESTRICTED THREE-BODY DYNAMICS"? Too chatty. Just: "N-BODY · SOFTENED GRAVITY". Hmm the title already says restricted three-body. Bottom-right: I'll put live readout of camera?? Unnecessary. Maybe a small "record-friendly" note? No. Put phase there? Keep phase in HUD top-left. Bottom-right: tiny "36,000+ STARS · 60 FPS TARGET"? I'll put "65536 PARTICLES · GPU INTEGRATION". OK.

Now the module code:

```js
import * as THREE from 'three';

// ---------- constants ----------
const TEX = 256, NP = TEX*TEX; // 65536
const N_STARS = 30000, N_HAZE = 2500; // per galaxy; 2*(30000+2500)=65000; spare 536
const GM_B = 90, EPS_B2 = 1.6*1.6, GM_H = 310, EPS_H2 = 9*9;
const MU = 800, EPS_CC2 = 2.0*2.0;
const SPEED = 3.3;         // sim units per real second
const MYR_PER_TU = 5.0;
const KPC_PER_UNIT = 1.25, KMS_PER_V = 48;
const R_DISK = 12;
```

Wait N check: 2*32500 = 65000, spare 536 ✓.

Random helpers: mulberry32 seeded (deterministic visuals ✓ nice for consistency) — I'll use a seeded PRNG so the piece always looks the same (authored). gauss via Box-Muller with cached spare.

Galaxy builder returns arrays appended into big Float32Arrays:
- pos0 (NP*4), vel0 (NP*4), col (NP*3), prop (NP*4).

```js
function makeBasis(n){ // n unit
  const a = Math.abs(n.y) < 0.9 ? new THREE.Vector3(0,1,0) : new THREE.Vector3(1,0,0);
  const e1 = new THREE.Vector3().crossVectors(a, n).normalize();
  const e2 = new THREE.Vector3().crossVectors(n, e1).normalize();
  return [e1,e2,n];
}
```

Per galaxy config:
```js
const galaxies = [
 { center: new THREE.Vector3(-52.5,0,0), vel: new THREE.Vector3(1.505,0,-0.575),
   normal: normalize(0.18,-0.93,-0.32), arms: 2, pitch: 0.30 (rad→ tan≈0.31→k=3.2), armPhase: 0.3, tint warm, hazeTint (1.0,0.86,0.66) },
 { center: (52.5,0,0), vel: (-1.505,0,0.575),
   normal: normalize(-0.52,-0.60,0.61), arms: 2?? give B 2 arms too but different pitch 0.36 and phase 1.1, tint cooler (0.82,0.88,1.0) }
];
```
Hmm wait — check normal A: (0.18,−0.93,−0.32): |v|=sqrt(0.0324+0.8649+0.1024)=sqrt(0.9997)=1.0 ✓ nice. B: (−0.52,−0.60,0.61): norm = sqrt(0.2704+0.36+0.3721)=sqrt(1.0025)≈1 ✓.

Spin s: A: +1 (L = n_A ≈ −y ✓ prograde). B: +1 with n_B having −y component 0.60 ✓ prograde but inclined 53° — okay variety.

Arm winding direction must TRAIL the spin: spin angular velocity about n with sign s: stars move with tangential t̂ = s*(−sinθ, cosθ,0) in local frame (e1,e2,n basis): local pos = (r cosθ, r sinθ, z); velocity direction (−sinθ, cosθ)*s. Angular velocity vector = s*ω*n. Arms: trailing means arm curls opposite to rotation direction: as radius increases, θ_arm decreases (for s=+1): θ(r) = θ_m − k*ln(r/r0) with k=1/tan(pitch) > 0. Fine — define θ = armPhase + m*π − k*ln(max(r,r0)) with k≈3.2 (pitch 17°). For B k≈2.8 (pitch 19.6°), 2 arms phase offset π.

Also note which visual handedness results — either way looks like a spiral ✓.

Star loop per galaxy g (index base = g*(N_STARS+N_HAZE)):

```js
for (let i=0;i<N_STARS;i++){
  const isBulge = i < N_STARS*0.24;
  let x,y,z, vx,vy,vz, r;
  if (isBulge) { Plummer sample a=1.6, rmax 5.2; random direction position: 
     // sample Plummer radius: X=rand; r = a/sqrt(pow(X,-2/3)-1); clamp
     dir: random unit sphere;
     pos = dir*r (z compressed *0.85 slight oblate? keep spherical);
     speed: vc(r)* (0.35+0.45*rand) direction random unit ⊥?? simply random unit vector*speed + net spin: tangential component around n: 
     vel = randUnit*speed*0.75 + tangentialDir(pos)*vc*0.45?? Let me: v = spinCirc(pos, 0.5) + randUnit()*vc(r)*0.42; where spinCirc gives s*ω... simpler: vt = cross(nAxis, p).normalize()*vc*0.5 (rotational streaming) + randUnit*vc*0.4.
     color warm; size 0.34+0.4*rand²; alpha 1; brightness 0.75+0.5rand.
  } else { disk star:
     u=rand(); r = R_DISK * Math.pow(u,1.7); if(r<0.7) r=0.7+rand*0.4;
     armStar = rand()<0.62;
     let th;
     if (armStar){ m = floor(rand()*arms); sig = 0.14+0.013*r; if(rand()<0.10) sig*=2.6; th = armPhase + m*(2π/arms) - k*ln(max(r,1.2)) + gauss()*sig; }
     else th = rand()*2π;
     r *= 1+gauss()*0.05;
     z = gauss()*(0.15+0.03*r)*(armStar?0.85:1);
     local pos (r cos th, r sin th, z);
     vc = vCirc(r); 
     tangential dir: s*(-sin th, cos th, 0);
     v = tang*vc*(1+gauss()*0.035) + radialDir*gauss()*0.045*vc + zhat*n?? vertical: n̂*gauss()*0.05*vc*0.5;
     color: radius-based ramp + arm boost;
  }
  transform: world = center + e1*x + e2*y + n*z; vel world = e1*vx + e2*vy + n*vz.
  write arrays.
}
```

vCirc(r): `Math.sqrt(GM_B*r*r/Math.pow(r*r+EPS_B2,1.5) + GM_H*r*r/Math.pow(r*r+EPS_H2,1.5))`.

Color ramp function:
```js
function diskColor(r, arm, rnd){
  // t = clamp(r/11,0,1)
  // inner warm → outer blue-white
  const t = Math.min(1, r/10.5);
  let c = lerp3([1.0,0.87,0.62], [0.58,0.72,1.0], smoothstep-ish t);
  if (arm){ c = lerp(c, [0.62,0.78,1.05 clamp 1], 0.35) } // arms bluer
  else { c = lerp(c, [1.0,0.9,0.7], 0.2) } // inter-arm warmer/redder
  hot: if (arm && rnd<0.09): c = [0.55,0.68,1.15→clamp1.15 ok], brightness 1.5, size 1.25
  jitter each channel ±0.05
}
```
Brightness folded into color*scale where scale = (0.55+0.75*rand)*exposure... careful additive saturation: typical star contributes color*g*alpha with g peak 1 → each star ~0.6–1.3 × color. Overlaps of 2–6 stars → 2–5 → clipped white-ish in dense spots — good (sparkling). Exposure uniform folded at build (constant 1.0; tune overall via global multiplier constant EXPOSURE=1.0 baked... I'll keep a uniform uExposure in shader instead — easier to tweak: multiply vColor in vertex shader. Set 1.0 default, maybe 1.1.)

Haze:
```js
for i<N_HAZE:
 u=rand(); r = 13.5*Math.pow(u,2.3); if r<0.6 r=0.6..; 
 th: 45% arm-biased (same arm formula, bigger scatter), else uniform.
 z = gauss()*(0.5+0.06*r);
 vc same; tangential velocity ×1.0 (+small scatter).
 size = 8 + 20*rand*rand; alpha = 0.028/(1+size*0.04)?? bigger → lower alpha: alpha = 0.02+0.03*rand*(1 - size/30)?; simple: alpha = 0.045*Math.pow(rand(),1.5)+0.015.
 color: galaxy tint * (0.8+0.4rand): A: (1.0,0.85,0.62); B: (0.72,0.80,1.0)?? B tint slightly blue-violet? avoid violet... (0.70,0.82,1.0) is blue-white ✓.
```

Spare 536: pos (5e4 + i, 0, 0)?? put all at same far point (5e4,0,0), v=0, prop alpha 0, size 0 → vertex shader: gl_PointSize set but alpha 0 → discarded after frag (alpha 0 → contribution 0 even without discard — fine; still costs fill for 536 pts of size... size 0 → max(ps,1.1)=1.1px — negligible ✓). Actually set aProp.x=0 → size*proj/dist → 0 → clamped 1.1px, alpha 0 → no output ✓.

**Init textures:** posInit DataTexture: Float32Array NP*4; needs .neutral: set w=0. velInit similarly. DataTexture(data, TEX, TEX, RGBAFormat, FloatType); minFilter=magFilter=Nearest; needsUpdate=true.

**Copy pass:** copyMat with map uniform; render into rtP[idx=0] & rtV[0]. Then dispose init textures (or keep, tiny). Dispose to be clean.

**Sim shaders:**

velFrag:
```glsl
uniform sampler2D tPos, tVel;
uniform vec3 uCoreA, uCoreB;
uniform vec4 uGrav; // GMb, epsb2, GMh, epsh2
uniform float dt;
varying vec2 vUv;
void main(){
  vec3 p = texture2D(tPos, vUv).xyz;
  vec3 v = texture2D(tVel, vUv).xyz;
  vec3 a = vec3(0.0);
  vec3 dA = uCoreA - p; float rA2 = dot(dA,dA);
  vec3 dB = uCoreB - p; float rB2 = dot(dB,dB);
  float fa = GM_B * inversesqrt(rA2+EPS_B2); fa /= (rA2+EPS_B2);
  ... 
```
Wait write clean:
```
  float wA = uGrav.x / pow(rA2 + uGrav.y, 1.5) + uGrav.z / pow(rA2 + uGrav.w, 1.5);
  float wB = uGrav.x / pow(rB2 + uGrav.y, 1.5) + uGrav.z / pow(rB2 + uGrav.w, 1.5);
  vec3 a = dA*wA + dB*wB;
  v += a*dt;
  float sp2 = dot(v,v);
  if (sp2 > 3600.0) v *= 60.0/sqrt(sp2);
  gl_FragColor = vec4(v, 0.0);
```
pow(x,1.5) fine. Could use inversesqrt for speed: w = g*inversesqrt(q)/q — same. Use inversesqrt (cheaper):
`float ia = inversesqrt(rA2+uGrav.y); float wA = uGrav.x*ia*ia*ia + uGrav.z*ih*ih*ih;` — i³ = (r²+ε²)^{-1.5} ✓. Do that.

posFrag:
```
vec4 P = texture2D(tPos, vUv); vec4 V = texture2D(tVel, vUv);
gl_FragColor = vec4(P.xyz + V.xyz*dt, P.w);
```

vert (sim quad):
```
varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }
```
PlaneGeometry(2,2) provides position ±1 and uv ✓.

copyFrag: `gl_FragColor = texture2D(tSrc, vUv);`

**Points shaders:** as above. One material handles stars + haze + spares via attributes ✓.

Vertex:
```glsl
uniform sampler2D uPosTex;
uniform float uProj;     // heightPx / (2 tan(fov/2))
uniform float uTime;
uniform float uExposure;
attribute vec3 aColor;
attribute vec4 aProp;    // size, alpha, phase, twinkleAmt
varying vec3 vColor;
varying float vSoft;     // maybe unused
void main(){
  vec4 P = texture2D(uPosTex, position.xy);
  vec4 mv = modelViewMatrix * vec4(P.xyz, 1.0);
  float ps = aProp.x * uProj / max(0.1, -mv.z);
  float clamped = max(ps, 1.2);
  float dim = min(1.0, (ps/1.2)*(ps/1.2));
  float tw = 1.0 - aProp.w * (0.5 + 0.5 * sin(uTime * (0.5 + fract(aProp.z)*1.6) + aProp.z*61.0));
  gl_PointSize = clamped;
  gl_Position = projectionMatrix * mv;
  vColor = aColor * (uExposure * dim * tw);
  vAlpha = aProp.y;
}
```
position.xy is the uv (values 0..1) ✓ attribute named 'position' auto-declared by three; I fill Float32Array with (u, v, 0).

Fragment:
```glsl
varying vec3 vColor; varying float vAlpha;
void main(){
  vec2 q = gl_PointCoord*2.0 - 1.0;
  float d2 = dot(q,q);
  if (d2 > 1.0) discard;
  float g = exp(-d2*3.2) + 0.18*exp(-d2*1.15);
  gl_FragColor = vec4(vColor * (g * vAlpha), 1.0);
}
```
Wait brightness: peak g=1.18; alpha folded ✓.

Material: `blending: THREE.CustomBlending, blendEquation: AddEquation, blendSrc: OneFactor, blendDst: OneFactor, depthTest:false, depthWrite:false, transparent:true`.

Core glow material: vertex: plain attribute positions (3 verts? A glow, B glow, and maybe 2 extra small bright nuclei): I'll do 2 vertices with per-vertex color+size+alpha attributes; fragment with wider profile:
```
float g = exp(-d2*2.4)*0.55 + 0.30*exp(-d2*0.55);
```
Size world ~26 (halo). Also small intense nucleus sprite: could be same vertex with different size... The bulge stars already saturate; glow adds halo. Vertex colors: A: (1.0,0.80,0.55)*0.5, alpha handled: I'll fold: aGlow = vec4(color, alpha); final: vec4(col*alpha*g...). Add streak: second Points with 2 verts, size ~34, fragment: `float g = exp(-q.x*q.x*1.6) * exp(-q.y*q.y*30.0);` color slightly blue-white (0.8,0.88,1.0)*0.35, alpha 0.5?? Keep VERY subtle: alpha 0.28. Hmm anamorphic streak horizontal in SCREEN space (gl_PointCoord is screen-aligned ✓ since point sprites are screen-facing quads ✓). 

Update per frame: positions from coreA/coreB. needsUpdate ✓.

But careful: core glow Points also need frustumCulled=false and updated boundingSphere? frustumCulled false ✓.

**Background stars:** geometry positions shell; attributes color & size & phase; material with no texture:
```
vertex: gl_PointSize = aSize * uPixelRatio; standard projection; twinkle subtle.
frag: gaussian: g = exp(-d2*3.0); alpha from aAlpha attribute? fold into color magnitude ✓ additive.
```
Also they should not be tone... additive fine. 2400 stars, radius 1300–2400. Sizes in px: 0.7–2.0 (×pixelRatio). brightness 0.2–1.0. Some blue/warm tint. Plus faint band? A subtle "distant galaxy haze" — skip.

Hmm — dark starfield: with additive bg stars total ambient glow tiny ✓.

**Camera + loop:**

```js
const clock = ... use rAF timestamp (required: "Use the requestAnimationFrame timestamp for animation time"): 
function frame(tms){ requestAnimationFrame(frame); const t = tms*0.001; realDt = min(t - last, 0.05); last = t; ... }
```
First frame: last initialized on first call (if last<0 → last=t, dt=0).

Physics advance:
```js
let simT = 0, acc = 0;
const slowFactor = () => { const S = sepLen; return 1 - 0.62*Math.exp(-((S-9.5)/3.5)**2) };  // wait exp(-(S-9.5)²/12.25)
acc += realDt * SPEED * slowFactor();
let nSub = Math.min(4, Math.max(1, Math.ceil(acc/0.03)));
const h = acc/nSub; acc = 0; // consume all
for (k<nSub){ stepCores(h); setCoreUniforms(); simStep(h); simT += h; }
```
Hmm acc=0 after consuming — with nSub capped 4, if realDt big (tab switch), leftover dropped (acc=0) ✓ fine.

stepCores(h): integrate relative vector with semi-implicit:
```
S2 = d·d + EPS_CC2?? a_rel = −MU * d / pow(d·d + EPS_CC2, 1.5)
drag: gate = smoothstep(13,19,simT) (use simT before step); 
S = |d|
ad = −(0.17*gate)* v_rel * exp(−(S/9)²) − 2.4 * v_rel * exp(−(S/2.3)²)
a_rel += ad
v_rel += a_rel*h; d += v_rel*h
```
Note drag applied to relative coordinate ✓ (forces equal-opposite on cores conserve barycenter ✓).

Uniforms: uCoreA = d*-0.5, uCoreB = d*0.5 (vec3). Update glow point positions = cores.

Wait — also cores' velocities needed for HUD v_rel ✓ keep.

**Passage counting for phase + slowmo:** compute S each frame; track prevS; descending detection:
```
if (S < prevS) descending=true, minTrack=min...
else if (descending && S > prevS + 1e-6){ if (prevS < 16) passages++; descending=false; }
```
Also require prevS < 16 to count as passage (avoid counting noise at start: at t=0 S=105 decreasing ✓ descending=true immediately; minimum at pericenter ~9.7 ✓ counts passage 1 ✓).

**HUD update (every ~6 frames or each frame cheap):**
```
myr = simT * 5
sep kpc = S * 1.25
vrel km/s = |v_rel| * 48
phase text per logic.
```
DOM text updates each frame OK (cheap), maybe every other frame.

**Resize:**
```
function resize(){ w=innerWidth,h=innerHeight; renderer.setSize(w,h); camera.aspect=w/h; updateProjectionMatrix; uProj = (h*pixelRatio)/(2*tan(fov/2 rad)); pointsMat.uniforms.uProj.value = ...; bgMat.uniforms.uPixelRatio = pixelRatio }
window.addEventListener('resize', resize)
```
Also handle pixelRatio change (zoom) — recompute in resize ✓.

**Title fade:** after t>9: title.classList.add('fade') → CSS opacity 0 transition 1.5s.

**Perf estimate:** sim: 2 passes × 65k fragments × (few ALU) — trivial. Points: 65.5k vertices + overdraw: haze big points cause fill: 5000 haze × avg (size ~15 world → ~120px → 14k px) = 70M px?? WAIT that's a lot: 5000 haze sprites × π*(60px)² ≈ 5000×11310 = 56.5M fragments/frame — too much for weak GPUs! Hmm. Reduce: haze sizes 8+16*r² avg ~13.5 world → px at 140 dist: 13.5*1159/140 = 112 px diameter → area ~9800 px × 5000 = 49M. Yes heavy. Mitigations: (a) reduce haze count to 1400/galaxy (2800): 27M — still heavy; (b) smaller haze: size 5–12 world (~40–100px): avg 75px → area 4400 × 3000 = 13M ✓ okay; (c) rely on the 60k stars for glow and use fewer, smaller haze: 2200 per galaxy, size 4+9*r² (avg ~7 → 58px dia → 2600px²) → 4400×2600 = 11.5M px ✓ acceptable (mobile-ish GPUs handle ~1–2 Gpx/s → 11.5M×60 = 0.7Gpx/s — hmm borderline but these are ALU-light fragments (discard early for d2>1 kills 21% of quad area; gaussian cheap). Also big core glows: 4 sprites × ~(180px)² ×π/4 ≈ 4×25k = 100k px — negligible.

Hmm also star fill: 60k stars × avg (3.5px)² ×0.785 ≈ 60k×9.6 = 0.6M ✓ negligible. Twinkle etc fine.

Actually also consider: on very high-DPI (pixelRatio 2 → uProj doubles → px sizes double → fill ×4). Cap pixelRatio at 1.75? Cap 2 standard; fill from haze at 4K-equivalent... Let me scale haze alpha down but keep. I'll cap DPR at 2 and reduce haze a bit: 2000 per galaxy, sizes 4–13. Also the exponential falloff means outer half of each sprite is dim — fine.

Also we could halve haze fill by rendering haze only... no, keep simple with modest numbers.

Sim GPU: also each sim pass renders 65k fragments (fullscreen 256×256 RT) — trivial ✓.

**JS per-frame cost:** negligible (cores + HUD).

**Memory:** arrays ~ (4+4+3+4)*65536 floats ≈ 1MB ✓.

**Determinism / seeding:** seed PRNG 1234; gauss with spare.

Now — double-check three.js r186 API specifics:
- `new THREE.WebGLRenderTarget(w, h, {type: THREE.FloatType, format: THREE.RGBAFormat, minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter, depthBuffer: false})` ✓. In recent versions samples:0 default ✓. Also `colorSpace`: render targets default linear (NoColorSpace) ✓ good — sim data must stay raw.
- DataTexture: `new THREE.DataTexture(data, w, h, THREE.RGBAFormat, THREE.FloatType)`; set .magFilter/.minFilter = Nearest; .needsUpdate = true; .generateMipmaps=false? default false for DataTexture? DataTexture default minFilter Nearest ✓ generateMipmaps false ✓. Set explicitly anyway.
- ShaderMaterial with custom attributes ✓ (WebGL2 → GLSL100 shaders still fine; attributes work).
- Points frustumCulled = false ✓.
- renderer.setRenderTarget(rt); renderer.render(scene,cam); then setRenderTarget(null) ✓.
- CustomBlending constants ✓.
- OutputColorSpace default SRGB in r152+ ✓ — with additive shader colors, the renderer converts final output? When rendering to canvas with outputColorSpace SRGB, three appends colorspace conversion ONLY for built-in materials via fragment includes; ShaderMaterial custom WITHOUT `#include <colorspace_fragment>` will NOT convert → my colors output linear values into an sRGB-displayed canvas → appear darker than authored... Actually the canvas is sRGB; my shader writes raw values → interpreted as sRGB directly → effectively my values ARE the sRGB values. Since I hand-tune constants anyway, fine — I'll author constants to look right with raw output (this is what most ShaderMaterial examples do). Keep consistent: no tonemap includes, direct output.
- Import map provided (three + addons) ✓ I only need 'three'.

Also note: `texture2D` in GLSL100 ✓. `inversesqrt` ✓.

One more check — **points with position attribute = uv values:** three.js computes `geometry.computeBoundingSphere` for raycast etc. — Points constructor doesn't auto-compute; renderer might call... WebGLRenderer doesn't need bounds if frustumCulled=false ✓. Also object.renderOrder fine.

**gl_PointSize when size huge (haze near camera):** camera stays ≥ ~120 from content — haze at r 60 toward camera: dist ~70: px = 12*1159/70 = 200px ok.

**Star size vs distance clamping** ✓.

**Initial camera before first frame:** set via same function t=0 ✓.

**Antialias:** false; but background star points look fine. Canvas default alpha: renderer with alpha false, clearColor #01030a-ish. Slight blue-black: (0.008, 0.012, 0.03)? Use new THREE.Color(0x020409).

**Let me also reconsider whether arms will look good at t=0 given rotational shear over the first ~5s:** shear dΩ: from v_c nearly flat (4.6–4.9 for r 3–12) → Ω = 4.7/r: dθ/dt between r=3 and r=12: 1.57−0.39=1.18 rad/t.u.?? Ω(3)=4.89/3=1.63; Ω(12)=4.53/12=0.377 → ΔΩ=1.25 rad/t.u. Over first passage at ~19 t.u.: relative twist 24 rad = 3.8 revolutions between inner and outer edge — the initial 2-arm spiral (wound k·ln over ~1 wrap) will add ~2–3 wraps in the inner-mid region... Arms become tightly wound pinwheel by ~t=8–10 t.u.?? Let me estimate arm contrast lifetime: two stars at r=3 and r=4: Ω diff = 1.63−1.31=0.32 rad/t.u. → after 10 t.u.: 3.2 rad — arm strand at inner disk spreads over ~3 rad — arm definition in inner region blurs within ~6–8 t.u. (2–2.5s real) — BUT by t=19 the encounter starts and re-scrambles everything into tails anyway. Hmm — so for the first ~2–3 seconds the spiral is crisp, then inner arms smear toward rings, outer arms persist longer (outer ΔΩ small: r=8 vs 12: 0.575−0.377=0.2 → 10 t.u. → 2 rad spread — outer arms stay recognizable ~8+s ✓). Given the camera is far and galaxies small on screen early, the visible impression remains "two spiral galaxies" through approach, with graceful winding — physically honest (real galaxies wind too, just slower). 

Could reduce winding by flattening rotation curve MORE (raise halo GM, lower bulge): try GM_B=60, GM_H=340, εh=10: vc(3)= 60*9/(11.56^1.5=39.3)=13.7 + 340*9/(109)^1.5=3060/1138=2.69 → v²=16.4 v=4.05 Ω=1.35; vc(12): 60*144/(147.6^1.5=1793)=4.8 + 340*144/(244)^1.5=48960/3812=12.8 → v²=17.6 v=4.2 Ω=0.35; ΔΩ(3→12)=1.0 (vs 1.25) — 20% better; inner vc lower → slower inner swirl (period at r=3: 4.66 t.u. = 1.4s real — still lively). Also vc(1.5): 60*2.25/(2.25+2.56=4.81^1.5=10.55)=12.8 + 340*2.25/(4.81+100=104.8^1.5=1072)=0.71 → v²=13.5 v=3.68 Ω=2.45 → period 2.6 t.u.=0.78s ✓ lively.

Also lower vc means slower tails ejection? Encounter strength relative to binding: v_p 12.4 vs v_esc at r=10: 2*(60/√102.6 + 340/√(100+100)) = 2*(5.92+24.04)=59.9 → v_esc=7.74; vc=4.35 — comparable ratio to before ✓ tails still eject plenty.

Let me adopt: GM_B=60, εb=1.5 (εb²=2.25), GM_H=340, εh=10 (εh²=100), MU=800, εcc=2. 

Recheck vc table: r=2: 60*4/(6.25^1.5=15.6)=15.4 + 340*4/(104^1.5=1061)=1.28 → v²=16.7→4.08; r=6: 60*36/(38.25^1.5=236.6)=9.13 + 340*36/(136^1.5=1586)=7.72 → v²=16.85→4.1; r=9: 60*81/(83.25^1.5=759)=6.4+340*81/(181^1.5=2436)=11.3→v²=17.7→4.2; r=12: 4.2 ✓ FLAT ~4.1 across 2–12 ✓✓ nice solid disk. Ω: r=2: 2.04; r=6: 0.68; r=12: 0.35. ΔΩ(2→12)=1.69?? worse inner... inner r=2: Ω=2.04 vs before (bulge90: Ω(2)=4.8/2=2.4) — better ✓. Overall shear between adjacent radii lower ✓.

Orbital dynamics of cores: unchanged (MU=800 total? cores attract with full galaxy mass 400 each → MU=800 ✓ regardless of bulge/halo split ✓).

Bulge star speeds: at r=1: 60/(3.25^1.5=5.86)=10.2+340/(101^1.5=1015)=0.335 → v²=10.6 v=3.25 ✓.

Escape speeds: at r=3: 2*(60/√11.25 + 340/√109)=2*(17.9+32.6)=101 → 10.05; v_c 4.05 → bound ✓. Pass1 impulse: companion core bulge 60+halo 340 with approach speed 12.4: outer stars can get Δv up to ~2*GM_p/(b*v) (gravitational focusing impulse): for b~5, GM_p=400: Δv ≈ 2*400*2/(b*v)?? formula Δv ≈ 2GM/(b v∞): 2*400/(5*12.4)=12.9 — comparable to v_c ✓ strong stripping ✓ tails guaranteed.

**Star density at center vs bulge:** bulge 24% of 30k = 7200 stars within r~2–3 → super bright core ✓. 

**Colors of bulge vs disk transitions:** smooth ✓.

Now, let me also make sure the **first frame isn't before textures copied** — do init before starting rAF ✓ synchronous.

**Fallback if FloatType RT unsupported:** check `renderer.extensions.has('EXT_color_buffer_float')`?? three r186: WebGLRenderer.capabilities... I'll do:
```
const floatOK = renderer.extensions.get('EXT_color_buffer_float') || renderer.extensions.get('EXT_color_buffer_half_float');
```
Hmm extensions.get returns ext or null. If neither → fallback HalfFloatType (WebGL2 always supports half float rendering? EXT_color_buffer_half_float needed too in WebGL2 for EXT... actually WebGL2 supports RGBA16F rendering with EXT_color_buffer_float OR EXT_color_buffer_half_float; mostly available). Simplest: try FloatType; if extension missing, use HalfFloatType. DataTexture for init must match? Init textures are sampled, not rendered-to — FloatType sampling requires OES_texture_float in WebGL1 but WebGL2 supports 32F texture sampling natively ✓ (filtering needs extension but we use Nearest ✓). So init DataTextures can stay Float32 regardless; only RT type falls back. Positions in half RT: fine.

Edge: if BOTH missing (ancient ANGLE) — extremely unlikely; ignore (could fallback CPU sim… no, keep scope).

**Now writing out all numbers & constants concretely:**

```
TEX=256; NP=65536
N_STARS=30000/galaxy; N_HAZE=2000/galaxy → used 64000; spare 1536?? 65536−64000=1536. OK spares 1536.
Actually let me do N_HAZE=2200 → used 64400, spare 1136. eh fine — round: haze 2200.

Wait: fill rate concern: 4400 haze — okay as computed.
```

Galaxy A config:
```
center (-52.5, 0, 0); vel (1.505, 0, -0.575)
normal: n = normalize(0.16, -0.94, -0.30)
arms: 2; k=3.4 (pitch ~16.4°); armPhase 0.4
tint haze: (1.00, 0.84, 0.60)
coreGlow color: (1.0, 0.78, 0.50)
```
Galaxy B:
```
center (52.5, 0, 0); vel (-1.505, 0, 0.575)
normal: normalize(-0.50, -0.58, 0.64)
arms: 2; k=2.9; armPhase 1.35
haze tint: (0.66, 0.78, 1.00)
coreGlow: (0.92, 0.80, 1.0)?? avoid violet → (0.85, 0.82, 1.0) pale blue-white.
```
Hmm B normal: check |(−0.50,−0.58,0.64)| = sqrt(0.25+0.3364+0.4096)=sqrt(0.996)=0.998 → normalize ✓. n_B·(0,−1,0)=0.58 → inclination ~55° from orbital L — prograde tilted ✓. Also n_B·x negative → disk tilted toward viewer differently ✓.

But WAIT: spin handedness: I set velocity tangential = s*(-sinθ, cosθ, 0)*vc in LOCAL frame → angular momentum along local +z*s → world: s*n. For prograde want L_disk·L_orb > 0, L_orb = −y. A: s*0.94·(−1)→ need s=+1 → L_A ≈ −0.94y ✓. B: s=+1 → L_B·(−y)=0.58 ✓. Both s=+1 ✓.

Arm winding: θ(r) = phase + m*π − k*ln(r)?? Trailing check: stars rotate with dθ/dt = Ω*s... in local frame rotation direction: velocity (−sinθ, cosθ) → dθ/dt = +vc/r > 0 (counterclockwise in local xy-plane viewed from +z i.e. from n side). Arms trailing: arm tangent opposes rotation at larger radius... a trailing spiral: θ decreases as r increases (for CCW rotation): θ = θ0 − k ln r ✓ (as r↑, θ↓ → arm sweeps backward relative to CCW rotation ✓). k=1/tan(pitch): pitch 16° → tan=0.287 → k=3.5. OK A k=3.5, B k=2.95.

Arm span sanity: r from 1.2→12: ln ratio ln(10)=2.3 × k=3.5 → Δθ=8 rad per arm — arm wraps ~1.3 turns ✓ grand design.

**Disk vertical:** z gaussian σ = 0.14+0.028r: at r=3: 0.22; r=10: 0.42 ✓ thin.

**Now core glow sprites:** sizes: A 26, B 24; but early approach the cores sit inside bright bulges; glow halo radius ~26 world ≈ bulge×?? fine soft ambient. alpha: fold: color*(0.5), profile peak 0.85 → contribution peak ~0.42·warm — visible soft halo ✓. During merger: two glows within ~1.5 units → single brighter halo ✓.

Also nucleus hotspots: add 2 extra tiny bright sprites size 3.5, color (1.0,0.9,0.75), alpha high 1.2 → compact brilliant center. Actually bulge stars already blow out; skip extra nucleus — simpler. Hmm, one small addition for cinematic: I'll include per-core a "nucleus" vertex in the same glow geometry: 4 vertices total: [A-halo, B-halo, A-nucleus, B-nucleus]. Nucleus size 4.2, alpha 0.9, profile sharper (exp(-d2*5)). Per-vertex need profile type → add attribute aKind (0 halo, 1 nucleus, 2 streak): fragment branches by varying. Let me combine halo+nucleus+streak into ONE Points (4 verts) with aKind varying:
```
if k==0: g = exp(-d2*2.6)*0.6 + 0.32*exp(-d2*0.6)
if k==1: g = exp(-d2*4.5)*1.2
if k==2: g = exp(-q.x*q.x*2.0)*exp(-q.y*q.y*26.0)*0.9
```
sizes: halo 26, nucleus 4.5, streak 30 (wide flat). colors per galaxy. Streak alpha low: color*0.30.

I need gl_PointCoord y-direction — symmetric gaussian, no issue ✓.

Streak subtle: contribution peak 0.9*0.3=0.27 blue-white — hmm might look like an artifact line; make 0.18. Actually at size 30 world = 250px wide streak across core — cinematic anamorphic ✓ keep 0.2 intensity, very soft x-falloff (exp(-qx²*2.0) → at qx=0.7: 0.37... too wide? width ~±0.7 of sprite → 175px — long elegant streak; y sigma: exp(-y²*26): half-width ~0.14 → 35px tall — thin ✓.)

Hmm — risk: streaks could read as "cheap lens flare". Keep intensity 0.15 and size 24. Tasteful.

**HUD phase & numbers formatting:** use padStart. Time: `String(Math.floor(myr)).padStart(3,'0')`. Show as `T + 347 MYR`. Also small progress hint? no.

**Caption bottom-right:** `RESTRICTED THREE-BODY · 65,536 PARTICLES · GPU-INTEGRATED` — dim.

**Title bottom-left:** 
```
GALACTIC COLLISION
two spiral galaxies · tidal disruption simulation
```
Fade in 1s, fade out at 9–11s. Big-ish thin letterspaced (16px, spacing 0.35em). Second line 10px dim.

Let me also consider adding a **pericenter flash cue**: when passage happens, HUD phase changes — enough.

**Testing-by-inspection of subtle three.js gotchas:**

1. ShaderMaterial + Points + CustomBlending: need `transparent: true` so it renders in transparent pass with blending ✓ (blending applies regardless if material.blending set and transparent... For opaque objects blending is skipped? three sets blending state from material.blending always; but objects with transparent=false render in opaque pass sorted front-to-back — blending still applied? WebGLState sets blending per material — I believe material.blending is honored even for opaque, but to be safe set transparent:true → proper transparent pass (sorted back-to-front — irrelevant for additive) ✓.

2. `depthTest:false, depthWrite:false` for all transparent ✓ (they'd otherwise fight; scene has no depth writes at all — bg, stars, glow all no-depth ✓ order-independent additive ✓).

3. Sim scene: separate Scene with quad; material depthTest false; renderer autoClear default true — rendering into RT clears with renderer clear color — irrelevant since quad covers screen ✓. But careful: renderer clears to its clearColor each setRenderTarget render — fine.

Also disable `renderer.autoClear`? keep default (true) fine.

4. DataTexture upload of Float32: type FloatType + RGBAFormat → internalFormat RGBA32F ✓ r186 handles. (`texture.internalFormat` null → three computes from type/format ✓.)

5. Reading rtP[idx].texture in Points material uniform each frame ✓.

6. NearestFilter on RT textures: set in RT options ✓; also `texture.generateMipmaps=false` default for RTT ✓.

7. Uniform update of core positions per substep: velMat.uniforms.uCoreA.value.set(...) — using Vector3s ✓.

8. Camera near/far: near 0.5, far 6000; bg at ≤2600 ✓; logarithmicDepthBuffer no.

9. iOS: FloatType blending... additive blending to canvas fine; sim RT blending off ✓.

10. HalfFloat fallback: velocities magnitude ~12 with half precision ulp 0.0098 near 12 — integration noise ~0.1% — ok.

11. `renderer.setPixelRatio` before setSize ✓; and uProj uses drawingBufferHeight = h*pixelRatio — use renderer.getDrawingBufferSize(target) ✓ robust.

12. When tab hidden long → realDt clamped 0.05 ✓ physics continues normally.

13. IMPORTANT — three.js module import: importmap provided by host environment ("An import map is provided for you") — I must NOT add my own importmap; just `import * as THREE from 'three'` ✓. Don't import addons (not needed).

14. `type="module"` script ✓. No CDN ✓ no external anything ✓ fonts system ✓.

**Let me now also double-check the initial-condition velocities give the intended pericenter ~9.7 with the SOFTENED (εcc=2) mutual force:** softening barely matters at r>4 ✓. Earlier estimate: E=−2.44 per reduced mass... wait with μ=800 I derived using 800 ✓. L0 = 105*1.15 = 120.75 ✓. Pericenter of softened orbit ≈ 9.5–10 ✓. Pericenter TIME ~19 t.u. (est) ✓. Good.

But note: I should double check v_rel vector components: v_r = 3.01, v_t = 1.15 → v0² = 9.06+1.32=10.38 → v0=3.22 ✓ E = 5.19 − 800/105 = 5.19−7.619 = −2.43 ✓. r_max = 800/2.43 = 329. First passage time estimate ~19 t.u. ✓ (computed earlier via integral for D0=105: 19.3).

Hmm one more: with drag gate starting t=13–19 — during 13–19 the cores are at r≈?? falling: r(13)? Rough: r(t) from energy... r drops 105→~35 by t≈13?? Fall pace: r(t): v grows; rough table: t=0:105; v_r0=3.0; a(105)=800/11025=0.0726; t=5: v≈3.4, r≈90; t=10: v≈4.3, r≈70; t=13: v≈5.2, r≈57; t=16: v≈6.8, r≈40; t=18: v≈9, r≈22; t=19: v≈12, r≈10 ✓. Gate at 13–19: drag active from r~57 in — inbound extra Δv small (exp(−(57/9)²)=e^{−40}=0 ✓ zero until r<25: t≈17.5+: Δv_inbound ≈ 0.17*∫v exp(−(r/9)²) dt from r=25→10 ≈ 0.17*∫exp dr ≈ 0.17*(∫_{10}^{25} e^{−(r/9)²}dr ≈ 9*0.886*(erf(25/9=2.78)−erf(1.11)) = 7.97*(0.9987−0.8848)?? erf(1.11)≈0.886? hmm: erf(1.11)=0.886? erf(1.1)≈0.880, so ≈ 7.97*0.115=0.92) → Δv≈0.16 — negligible ✓. Pass1 timing ~19–19.5 t.u. → 5.8s real ✓. 

**One concern — will the BRIDGE be visible?** Bridge = stars pulled between the two galaxies during/after pass. With r_p≈9.7 and disks 12 — outer stars inter-penetrate — yes bridge forms ✓ plus haze particles make it luminous ✓.

**Camera slowmo interplay:** slowFactor uses S — during approach S from 105 → passes 9.5 region only at passage ✓; also during tail phase S goes 24 → dips each passage ✓; each dip slows time briefly ✓ cinematic.

Let me now also reconsider SPEED: 3.3 t.u./s. First pass 5.8s. Second pass ~t=35 t.u. = 10.6s. Coalescence ~t≈52–58 = 16–17.5s. Remnant till 30s. Myr label at 5 Myr/t.u.: pass1 at ~97 Myr, merge at ~270 Myr, end ~500 Myr ✓ plausible numbers ✓.

**Write phase logic concretely:**
```js
let passages = 0, prevS = 1e9, inPass = false;
function updatePhase(S, t){
  if (S < prevS - 1e-4) { inPass = true; minS = Math.min(minS ?? S, S); }
  else if (inPass && S > prevS) { if (prevS < 16 && passages===0 || prevS < 14) { passages++; } inPass=false; minS=1e9; }
  prevS = S;
  ...
}
```
Hmm careful: S<prevS each frame while descending; when S starts increasing, the minimum was prevS (last descending frame). Condition to count: minS < 16. Implement:
```js
if (S < prevS){ descending = true; }
else if (descending){ if (prevS < 17) passages++; descending = false; }
prevS = S;
```
At frame 1: S=105, prevS=1e9: S<prevS → descending=true; prevS=105. Works ✓.

Labels:
```js
function phaseName(){
  if (t > 62 && S < 4) return 'MERGER REMNANT';
  if (passages === 0) return S < 30 ? 'FINAL APPROACH' : 'FIRST APPROACH';
  if (S < 4.5) return passages>=3 ? 'COALESCENCE' : 'CORE OVERLAP';
  if (S < 13) return passages===1 ? 'FIRST PASSAGE · BRIDGE' : passages===2 ? 'SECOND PASSAGE' : 'FINAL PASSAGE';
  if (passages === 1) return 'TIDAL TAILS EJECTING';
  if (passages === 2) return 'TAILS EXPANDING';
  return 'RAPID INSPIRAL';
}
```
t>62 gate: use simT ✓.

**Numbers double-check for vc used at build time must MATCH shader potential** ✓ both use GM_B/εb/GM_H/εh constants ✓ (JS: Math.pow, GLSL pow — same).

**One more physics nuance:** disk star velocities computed for circular orbits in HOST potential only; but at t=0 companion is 105 away — perturbation negligible ✓.

**Bulge initial velocities:** mix: v = tangential_stream + random: 
```
tangential dir: cross(n, p̂) * s → normalize → * vc(r)*0.55
random: randUnit() * vc(r)*0.45
```
at small r this gives |v| ~ 0.7 vc → bound ✓ spheroid with net spin ✓.

**Now think about the ARM star velocity perturbation for realism — epicyclic:** small radial ±0.04 vc ✓ included. This causes arms to shear/wind — accepted.

**Sanity: initial view angle** — galaxies at ±52.5 on x-axis; camera angle start: pick ang0 = 2.35 rad?? camera pos angle measured from +x in XZ-plane: pos = (R cosE cosA, R sinE, R cosE sinA). At A=0 camera on +x axis → looking down the separation axis (galaxies one behind another) — bad. Want separation axis roughly perpendicular-ish to view but slightly oblique: A0 = 1.15 rad (~66°) → camera direction (cos66°=0.41, sin66°=0.91) → separation axis x projects at cos(angle between x-axis and camera dir)... The apparent separation on screen ∝ sin(angle between view dir and x-axis) = sin(66°)=0.91?? view direction from camera to origin = −(cam dir): angle between x-axis and view dir: 180−66 → sin = 0.91 ✓ good: galaxies appear separated ~0.91×actual horizontally-ish. Over 30s A increases 0.052*30=1.56 rad → ends at 2.71 rad (155°) — separation axis becomes nearly anti-parallel to view (sin155°=0.42) — galaxies foreshortened at end — hmm, but by then it's a merged remnant with tails; tails oriented ~ along orbital plane various directions — fine. Also elevation changes composition ✓. Alternatively drift ang slower and reverse? Monotonic 0.045 rad/s → 1.35 rad total: end 2.5 rad (143°, sin=0.6). OK use 0.045.

Wait — also consider that camera at elevation 0.34: the orbital plane (XZ) seen from 19.5° above — tails in-plane ✓ visible foreshortened but with elevation growing to ~29° they open up ✓ good storytelling: tails flat early → open up later ✓.

**Breathing radius:** +6.5 sin — okay.

**Also initial dolly-in:** R from 172→146 via smoothstep(4,26): starts wide (both galaxies full in frame at ±52.5 + growth room ✓).

**Potential problem — camera sees core glow sprites as huge squares?** No — gaussian falloff to ~0 at edge (exp(-d2*2.6): at d2=1 → 0.074 — hmm edge cutoff visible? 0.074*alpha0.5*color... at sprite edge there's a faint step. Increase falloff: exp(-d2*3.5): edge 0.03 — plus halo term 0.32*exp(-0.6)=0.176?! The wide-halo term is LARGE at edge (0.176) → visible circular edge! Fix: multiply whole profile by edge fade: `g *= smoothstep(1.0, 0.85, d2)`?? i.e., fade to 0 at rim: g *= (1 - smoothstep(0.8,1.0,d2)). Apply to all point profiles (stars too — star edge: main exp(-d2*3.2)=0.04 + halo 0.18*exp(-1.15)=0.057 → edge 0.097 — noticeable on big sprites, invisible on 4px stars, but haze 60px: 10% step → faint ring — apply edge fade universally ✓):
```
float rim = 1.0 - smoothstep(0.72, 1.0, d2);
g *= rim;
```
Slightly darkens overall — fine, tune alphas up a touch.

Also gl_PointCoord y flip: symmetric ✓.

**Sub-step uniform hazard:** when nSub>1, vel pass uses tVel=rtV[idx] etc. — ensure indices consistent: I'll write function simSubstep(h) that does both passes and flips idx ✓.

**Let me also add subtle rotation to whole galaxy-field?** No — physics moves everything.

**Write out vel shader's core uniforms per substep:** cores advanced with SAME h before star pass ✓ order: stepCores(h) → set uniforms → velPass → posPass.

**HUD DOM:**
```html
<div id="hud">
  <div class="row"><span class="lab">T</span><span id="tval">+000 MYR</span></div>
  <div class="row"><span class="lab">SEP</span><span id="sval">105.0 KPC</span></div>
  <div class="row"><span class="lab">VEL</span><span id="vval">— KM/S</span></div>
  <div class="row phase"><span id="phase">FIRST APPROACH</span></div>
</div>
```
Hmm SEP in kpc: initial 105 units × 1.25 = 131 kpc — realistic pair separation ✓ nice. v_rel 3.22×48 = 155 km/s ✓ plausible.

Style: top-left, 10px font, letter-spacing .14em, color rgba(170,195,225,.75); values color #eaf3ff; phase in dim cyan #7fd4ff?? avoid neon glow — plain #9fd8ef no text-shadow. A thin 1px left rule? Use small tick: `border-left:1px solid rgba(140,170,210,.25); padding-left:10px`. Tasteful.

Title: bottom-left 26px from edge:
```
GALACTIC COLLISION   (13px, ls .42em, #dfe9f5)
Two spiral galaxies — restricted three-body tidal simulation (10px, dim)
```
CSS animation fadeout at 10s: I'll trigger via JS adding class after t>10 (transition 2.5s → opacity 0, translateY slight). 

Caption bottom-right: `N = 65,536 TEST PARTICLES · SOFTENED GRAVITY · Δt GPU-INTEGRATED` 9px dim. Hmm simplify: "65,536 PARTICLES · SOFTENED GRAVITY · RESTRICTED N-BODY".

**Vignette:** div overlay: `background: radial-gradient(ellipse at center, transparent 58%, rgba(2,4,10,.55) 100%)` — filmic edge darkening ✓ subtle. Plus maybe top gradient for HUD legibility: tiny linear gradient top 80px rgba(0,0,10,.35)→0 — acceptable functional. I'll include only vignette; HUD text fine on black.

**Now write final code carefully.** Let me draft the full JS mentally with attention to correctness.

```js
import * as THREE from 'three';

/* ---------- deterministic RNG ---------- */
let seed = 88172645;
function rnd(){ seed ^= seed<<13; seed^=seed>>>17; seed^=seed<<5; return ((seed>>>0)/4294967296); }
```
xorshift32 ✓ deterministic. gauss:
```js
let gSpare=null;
function gauss(){ if(gSpare!==null){const v=gSpare;gSpare=null;return v;} let u=0,v=0; u=rnd()||1e-9; v=rnd(); const m=Math.sqrt(-2*Math.log(u)); gSpare=m*Math.sin(6.2831853*v); return m*Math.cos(6.2831853*v); }
```

/* constants */
```js
const TEXS=256, NP=TEXS*TEXS;
const NSTARS=30000, NHAZE=2200;   // per galaxy → used 64400
const GM_B=60, EB2=1.5*1.5, GM_H=340, EH2=10*10;
const MU=800, CC2=2.0*2.0;
const SPEED=3.3, MYR=5.0, KPC=1.25, KMS=48;
const RDISK=12;
```

vCirc:
```js
function vCirc(r){ const r2=r*r; return Math.sqrt(GM_B*r2/Math.pow(r2+EB2,1.5) + GM_H*r2/Math.pow(r2+EH2,1.5)); }
```

Galaxy generation into arrays:
```js
const posArr=new Float32Array(NP*4), velArr=new Float32Array(NP*4),
      colArr=new Float32Array(NP*3), propArr=new Float32Array(NP*4);

function addGalaxy(gi, cx,cy,cz, vx,vy,vz, nx,ny,nz, k, phase0, hazeTint){
  // basis
  let n=new THREE.Vector3(nx,ny,nz).normalize();
  const helper = Math.abs(n.y)<0.92 ? new THREE.Vector3(0,1,0) : new THREE.Vector3(1,0,0);
  const e1=new THREE.Vector3().crossVectors(helper,n).normalize();
  const e2=new THREE.Vector3().crossVectors(n,e1).normalize();
  const C=new THREE.Vector3(cx,cy,cz), CV=new THREE.Vector3(vx,vy,vz);
  const base=gi*(NSTARS+NHAZE);
  let idx=base;
  const put=(px,py,pz, v0,v1,v2, r,g,b, size,alpha,ph,twk)=>{
    const wpos=new THREE.Vector3(px,py,pz);  // local→world via basis… 
```
Hmm — doing Vector3 ops per particle = slow-ish for 65k but fine (~ms). But cleaner: inline math with precomputed basis components:
world.x = cx + e1x*lx + e2x*ly + nx*lz etc. I'll do scalar math (fast, no allocs):

```js
  const e1x=e1.x,e1y=e1.y,e1z=e1.z, e2x=e2.x,..., nx=n.x...
  function emit(lx,ly,lz, lvx,lvy,lvz, r,g,b, size,alpha, ph,twk){
    const wx=cx+e1x*lx+e2x*ly+nx*lz, wy=cy+e1y*lx+e2y*ly+ny*lz, wz=cz+e1z*lx+e2z*ly+nz*lz;
    const wvx=vx+e1x*lvx+e2x*lvy+nx*lvz, ...
    const i4=idx*4, i3=idx*3;
    posArr[i4]=wx; posArr[i4+1]=wy; posArr[i4+2]=wz; posArr[i4+3]=0;
    velArr[i4]=wvx; ...
    colArr[i3]=r; ...
    propArr[i4]=size; propArr[i4+1]=alpha; propArr[i4+2]=ph; propArr[i4+3]=twk;
    idx++;
  }
```

Bulge stars (i<NSTARS*0.24):
```js
for(let i=0;i<NSTARS;i++){
  const bulge = i < NSTARS*0.24;
  if(bulge){
    // Plummer radius
    const X=Math.max(rnd(),1e-6);
    let r=1.5/Math.sqrt(Math.pow(X,-2/3)-1);
    if(r>5.0) r=5.0*Math.pow(rnd(),0.5)?? // clamp: r=1.5+3.5*rnd();
```
Plummer a_b: with GM_B=60, choose a_b=1.5 ✓ (softening εb=1.5 matches scale). Clamp r>4.5 → resample-ish: if r>4.5: r=0.6+3.9*rnd() — fine (tail trimming).
```js
    // random direction
    const u2=rnd()*2-1, phi=rnd()*6.2832, s1=Math.sqrt(1-u2*u2);
    const dx=Math.cos(phi)*s1, dy=Math.sin(phi)*s1, dz=u2;
    const vc=vCirc(r);
    const spd=vc*(0.30+0.55*rnd());
    // streaming around n: t = normalize(cross(n, pos)) * vc*0.5
    // tangential: cross(n, d) (not normalized: |d|=1 so |cross|=sin angle) → normalize
    let tx=ny*dz-nz*dy, ty=nz*dx-nx*dz, tz=nx*dy-ny*dx;
    const tl=Math.hypot(tx,ty,tz)||1; 
    const cf=vc*0.55/tl;
    const v0=(dx*spd*0.9)?? 
```
Hmm combine: velocity = randomDir*spd + tangential*vc*0.5?? total |v| could exceed... v_esc(r=1)=2*(60/√(1+2.25)+340/√(1+100))=2*(33.3+33.8)=134→11.6; v typical: spd≈vc(1)*0.55avg≈(vc(1)=sqrt(60/5.86+340*1/1015... compute: 60*1/6.475?? wait vc(1): GM_B*1/( (1+2.25)^1.5=5.86 )=10.24; halo: 340*1/(101)^1.5=340*1/1015=0.335 → v²=10.6 → vc=3.25. spd~3.25*(0.3..0.85)=1–2.8 + 0.5*3.25=1.6 → |v| up to ~4.4 « 11.6 ✓ bound.

color: warm: base b0 = 0.85+0.35*rnd(): 
```js
    const cr=1.0, cg=0.72+0.16*rnd(), cb=0.42+0.20*rnd();
    const br=(0.55+0.75*rnd());
    emit(r*dx, r*dy, r*dz, dx*spd+tx*cf, dy*spd+ty*cf, dz*spd+tz*cf, cr*br, cg*br, cb*br, 0.30+0.34*rnd()*rnd(), 1.0, rnd(), 0.35);
```
size ~0.30–0.64 small ✓ twk 0.35 subtle.

Disk stars:
```js
  else {
    let r=RDISK*Math.pow(rnd(),1.7);
    if(r<0.8) r=0.8+rnd()*0.5;
    r*=1+gauss()*0.05;
    const arm = rnd()<0.60;
    let th;
    if(arm){
      const m=(rnd()<0.5?0:1);
      let sig=0.13+0.012*r; if(rnd()<0.10) sig*=2.4;
      th=phase0 + m*Math.PI - k*Math.log(Math.max(r,1.1)) + gauss()*sig;
    } else th=rnd()*6.2832;
    const z=gauss()*(0.13+0.030*r)*(arm?0.8:1.0);
    const ct=Math.cos(th), st=Math.sin(th);
    const vc=vCirc(r)*(1+gauss()*0.03);
    const vr=gauss()*0.05*vc, vzv=gauss()*0.04*vc;
    // tangential (s=+1): (-st, ct, 0); radial: (ct, st, 0)
    const lvx=-st*vc+ct*vr, lvy=ct*vc+st*vr, lvz=vzv;
    // color
    const t=Math.min(1, r/10.5);
    let cr,cg,cb, br, size;
    // warm→blue ramp
    const w=[1.0,0.86,0.60], bb=[0.60,0.74,1.05];
    let mr=w[0]+(bb[0]-w[0])*t, mg=..., mb=...;
    if(arm){ mr=mr*0.92+0.06; mg=mg*0.94+0.06; mb=Math.min(1.15, mb+0.08); }
    else { mr=Math.min(1.05, mr+0.05); mg*=0.97; mb*=0.9; }
    // hot blue giants in arms
    if(arm && rnd()<0.085){ mr=0.62; mg=0.74; mb=1.15; br=1.35+0.5*rnd(); size=0.85+0.5*rnd(); }
    else { br=(0.40+0.65*rnd())*(arm?1.0:0.72); size=0.34+0.40*Math.pow(rnd(),1.6); }
    // slight per-star jitter
    const j=(rnd()-0.5)*0.08; 
    emit(r*ct, r*st, z, lvx, lvy, lvz, Math.min(1.2,(mr+j))*br, (mg+j*0.6)*br, Math.min(1.25,(mb+j*0.4))*br, size, 1.0, rnd(), 0.3+0.5*rnd());
  }
```
Hmm careful brightness folding: color*br where br up to ~1.9 for giants — additive sum per star peak ~1.9 ✓.

Wait — the ramp at t=1: (0.60,0.74,1.05): blue-white ✓; at t=0: warm ✓. Arm boost pushes bluer ✓; requirement "warm yellow cores to blue-white arms" ✓ (also radial ramp does this since arms stronger outer).

Haze:
```js
for(let i=0;i<NHAZE;i++){
  let r=13.5*Math.pow(rnd(),2.3); if(r<0.7) r=0.7+rnd()*0.5;
  let th;
  if(rnd()<0.45){ const m=rnd()<0.5?0:1; th=phase0+m*Math.PI-k*Math.log(Math.max(r,1.1))+gauss()*(0.25+0.02*r); }
  else th=rnd()*6.2832;
  const z=gauss()*(0.45+0.05*r);
  const ct=Math.cos(th), st=Math.sin(th);
  const vc=vCirc(r)*(1+gauss()*0.04);
  emit(r*ct, r*st, z, -st*vc, ct*vc, gauss()*0.03, hazeTint[0]*(0.75+0.5*rnd()), hazeTint[1]*(...), hazeTint[2]*(...), 3.5+9.0*rnd()*rnd(), 0.05+0.05*rnd()*rnd()?? , rnd(), 0.0);
}
```
Haze size: world 3.5–12.5 → px at 140: 3.5*1159/140=29px to 12.5→103px ✓ moderate. alpha 0.02–0.09?? With additive, 2200 haze × alpha ~0.04 × color ~0.8 → per-area accumulation where overlapping ~5 haze → 0.16 luminosity — soft glow ✓. Inner haze concentration adds core glow ✓.

Hmm wait haze twk 0 ✓ (no twinkle).

Spare particles (idx from 64400 to 65535):
```js
for(;idx<NP;idx++){ const i4=idx*4; posArr[i4]=5e4; velArr same 0; propArr[i4]=0; propArr[i4+1]=0; ... }
```
Set pos y,z 0 ✓ v 0 ✓ alpha 0 ✓.

Wait — posArr w component: unused, set 0 ✓ (all inits default 0 for untouched ✓ Float32Array auto-zero ✓ so only set xyz & alpha/size.)

**Core glow geometry:**
```js
const glowGeo=new THREE.BufferGeometry();
positions Float32Array(4*3); colors(4*3); props: size+alpha packed → attributes aGlowSize? Use custom attributes: position (3), aColor(3), aSize(1), aAlpha(1), aKind(1).
verts: 0: A halo (size 26, alpha 0.5, kind 0, color warm A)
       1: B halo (24, 0.5, 0, cool B)
       2: A nucleus (4.5, 1.0, 1, warm bright)
       3: B nucleus (4.2, 1.0, 1, cool bright)
streak: separate? kind 2 with anisotropic profile needs gl_PointCoord — fine same material: verts 4: A streak (size 24, alpha 0.35, kind2, color (0.75,0.85,1.0)), 5: B streak same-ish.
```
glow vertex shader: standard transform, gl_PointSize = aSize*uProj/max(0.1,-mv.z); varyings vColor (color*alpha), vKind.
frag:
```
vec2 q=gl_PointCoord*2.-1.; float d2=dot(q,q);
float g;
if(vKind<0.5) g = exp(-d2*3.0)*0.55 + 0.4*exp(-d2*0.9);
else if(vKind<1.5) g = exp(-d2*4.0);
else g = exp(-q.x*q.x*2.2)*exp(-q.y*q.y*30.0);
g *= 1.0-smoothstep(0.75,1.0,d2);
gl_FragColor=vec4(vColor*g,1.0);
```
halo peak: 0.55+0.4=0.95×alpha0.5=0.47 ✓; nucleus peak 1.0×alpha1 × color(1,0.9,0.7)*?? nucleus color *1.4 brightness → saturated white-gold center ✓. streak peak: alpha 0.35×0.9?? g peak = 1×0.9=0.9?? set streak alpha 0.22, color (0.7,0.82,1.0) → peak 0.15 — subtle ✓.

Positions updated each frame:
```js
gp[i3]=coreA.x ... needsUpdate=true
```

**Background stars:**
```js
const NBG=2600; geometry positions on shell r=1400+rnd()*1000; random colors: base white (0.75..1) with temp variation: mix white with warm (1,0.85,0.7) or cool (0.75,0.85,1); brightness 0.12+0.6*rnd()^2; few bright: 3% br 1.2 size 2.4.
size px: 0.8+1.3*rnd()^2 (× pixelRatio in shader).
material: additive, no depth; vertex: gl_PointSize=aSize*uPR; twinkle: subtle 0.15.
```
Also make bg stars NOT twinkle much (0.2 amt for 30% only). fine.

**Materials/uniforms shared:** uTime used by stars & bg ✓ update per frame.

**Now the render loop:**

```js
let lastT=-1, simT=0, idx=0;
const core = { d:new THREE.Vector3(105,0,0), v:new THREE.Vector3(-3.01,0,1.15) };
```
Wait: d = rB − r_A = (105,0,0) ✓; v_rel = vB−vA = (−3.01, 0, 1.15) ✓.

stepCores(h):
```js
const S2=d.lengthSq(), S=Math.sqrt(S2);
// relative acceleration on B due to A: a = -MU * d̂ / (S2+CC2)^1.5 * ... 
const inv=1/Math.pow(S2+CC2,1.5);
ax=-MU*d.x*inv ...
// drag
const gate=smoothstep(13,19,simT);
const dg=Math.exp(-(S/9)*(S/9))*0.17*gate + Math.exp(-(S/2.3)*(S/2.3))*2.4;
ax-=dg*v.x; ...
v.addScaledVector(a,h); d.addScaledVector(v,h);
```
smoothstep helper JS:
```js
const sstep=(a,b,x)=>{x=Math.min(1,Math.max(0,(x-a)/(b-a)));return x*x*(3-2*x);}
```

Core positions: A=−d/2, B=+d/2 → set uniform vec3s: uCoreA.value.set(-d.x*0.5,...) ✓; store for glow & HUD.

Frame:
```js
function loop(tms){
  requestAnimationFrame(loop);
  const t=tms*0.001;
  if(lastT<0) lastT=t;
  let dt=Math.min(0.05, Math.max(0, t-lastT)); lastT=t;
  elapsed=t;
  // slow-mo factor
  const S0=core.d.length();
  const slow=1-0.62*Math.exp(-Math.pow((S0-9.5)/3.5,2));
  acc+=dt*SPEED*slow;
  const n=Math.max(1,Math.min(4,Math.ceil(acc/0.03)));
  const h=acc/n; acc=0;
  for(let k=0;k<n;k++){ stepCores(h); setCoreUniforms(); simStep(h); simT+=h; }
  updateCamera(t);
  updateGlows();
  updateHUD();
  starsMat.uniforms.uTime.value=t; bgMat.uniforms.uTime.value=t;
  renderer.render(scene,camera);
}
requestAnimationFrame(loop);
```

simStep(h):
```js
velMat.uniforms.tPos.value=rtP[idx].texture;
velMat.uniforms.tVel.value=rtV[idx].texture;
velMat.uniforms.dt.value=h;
quad.material=velMat;
renderer.setRenderTarget(rtV[1-idx]); renderer.render(simScene,simCam);
posMat.uniforms.tPos.value=rtP[idx].texture;
posMat.uniforms.tVel.value=rtV[1-idx].texture;
posMat.uniforms.dt.value=h;
quad.material=posMat;
renderer.setRenderTarget(rtP[1-idx]); renderer.render(simScene,simCam);
renderer.setRenderTarget(null);
idx=1-idx;
starsMat.uniforms.uPosTex.value=rtP[idx].texture;
```

setCoreUniforms: velMat.uniforms.uCoreA.value.set(-d.x*.5,-d.y*.5,-d.z*.5); uCoreB = +; ALSO update glow positions here or per frame ✓ per frame fine (substeps within a frame — glow drawn once per frame at final positions ✓).

Init sequence:
```js
renderer setup → build data → create RTs → copy init textures into rtP[0], rtV[0] via copyMat → dispose DataTextures → build scene → resize handler → start loop.
```
Copy pass: quad.material=copyMat; copyMat.uniforms.tSrc.value=posInitTex; setRenderTarget(rtP[0]); render; same vel → rtV[0]; setRenderTarget(null).

**Init RT allocation:** rtP[1], rtV[1] created empty — but posStep READS rtP[idx] (initialized) ✓ writes dst ✓. First substep: vel reads rtV[0] ✓.

**Uniform uProj:** compute on resize:
```js
function computeProj(){ const v=new THREE.Vector2(); renderer.getDrawingBufferSize(v); const fovR=camera.fov*Math.PI/180; return v.y/(2*Math.tan(fovR/2)); }
```
Set starsMat & glowMat & (bg uses uPR only).

**Camera update:**
```js
function updateCamera(t){
  const ang=1.12+0.045*t;
  const el=0.34+0.17*sstep(4,26,t)+0.02*Math.sin(t*0.23);
  const R=172-27*sstep(4,26,t)+6.5*Math.sin(t*0.16+1.7);
  camera.position.set(R*Math.cos(el)*Math.cos(ang), R*Math.sin(el), R*Math.cos(el)*Math.sin(ang));
  camera.lookAt(0,0,0);
}
```
Check el range: 0.34→0.51+0.02 → 19.5°→30° ✓.

**HUD update:**
```js
const elT=..., elS=..., elV=..., elP=...
every frame:
myr=simT*MYR → text `+${String(Math.floor(myr)).padStart(3,'0')} MYR`
sepKpc=S*KPC → `${sepKpc.toFixed(1)} KPC`
vKms=v.length()*KMS → `${Math.round(vKms)} KM/S`
phase.textContent=phaseName();
```

**Title fade:** if(elapsed>10) title.classList.add('gone') — CSS: #title{transition:opacity 2.2s ease, transform 2.2s ease} .gone{opacity:0; transform:translateY(6px)}.

**Assemble HTML/CSS:**

```css
html,body{height:100%}
body{margin:0;background:#02030a;overflow:hidden}
canvas{position:fixed;inset:0;display:block}
#vig{position:fixed;inset:0;pointer-events:none;background:radial-gradient(120% 90% at 50% 46%, rgba(0,0,0,0) 55%, rgba(1,2,8,.62) 100%)}
#hud{position:fixed;top:20px;left:22px;...}
```
Wait: vignette uses radial-gradient — as discussed, filmic, keep subtle (0.62 might be strong; use .5).

Font stack: `ui-monospace, 'SF Mono', 'Cascadia Code', Menlo, Consolas, monospace`.

Colors: labels rgba(150,175,205,.55); values #dfe9f5; phase #8fc8e8.

Also letter-spacing generous; line-height 1.75; font-size 10px; uppercase.

Add small top-left tick before T? A 1px vertical rule with padding-left 12px ✓.

Title styles:
```css
#title{position:fixed;left:24px;bottom:26px;...}
#title h1{font-size:13px;letter-spacing:.46em;font-weight:500;color:#e6eef8;margin:0 0 6px}
#title p{font-size:10px;letter-spacing:.18em;color:rgba(150,178,208,.55);margin:0}
```
No glow/text-shadow ✓.

caption bottom-right:
```css
#cap{position:fixed;right:24px;bottom:28px;font-size:9px;letter-spacing:.22em;color:rgba(140,165,195,.4);text-align:right}
```
Content: "RESTRICTED THREE-BODY · 65,536 PARTICLES · ADDITIVE RENDER".

Hmm the whole thing must start automatically ✓ rAF starts on load ✓.

**Edge case: WebGL context creation failure** — add try/catch → message div. Minor; include graceful message.

**Also verify: `position` attribute for stars uses values in [0,1] — three.js may warn about NaN bounding? We set frustumCulled=false; three still computes boundingSphere on first render for... only if needed (raycast/frustum). With frustumCulled false, skip ✓. Actually WebGLRenderer checks object.geometry.boundingSphere only when frustum culling enabled ✓.

**gl_PointSize cap:** some drivers clamp silently — fine.

**Verify star vertex shader `position` semantic:** three declares `attribute vec3 position;` in vertex prelude for ShaderMaterial ✓ (built-in attributes included). ✓ uv/normal also declared but unused (PlaneGeometry only for sim).

For Points geometry: I must set geometry.setAttribute('position', BufferAttribute(uvArray, 3)) ✓.

**Check np vertex count:** drawRange defaults to Infinity → uses index count/position count = 65536 ✓.

**Sim shader precision:** default highp in fragment for ShaderMaterial? three sets precision highp by default ✓ positions up to 5e4 for spares — highp float (fp32) ✓ fine.

**Gravity magnitudes check in shader:** GM_B=60: at r=1.5 near bulge: a=60*1.5/(2.25+2.25)^1.5=90/9.54=9.4 ✓ bounded.

**Velocity cap 60:** tails eject at ~Δv 8–12 over vc 4 → up to ~15 — cap rarely hit ✓.

**Now — estimate whether tails will actually look dramatic with these params.** Impulse at pericenter for outer disk star: companion (total GM 400, but star feels bulge60+halo340 with εh=10) passing at min distance ~ b: star at disk edge r=10–12 near passage line: companion core passes within ~ (9.7 ± geometry) — star-companion distance could be ~2–8 → force: at dist 5: a = 400*5/(25+100)^1.5 = 2000/1397=1.43 per unit... duration ~ (encounter timescale ~ 2b/v ~ 2*5/12=0.83 t.u.) → Δv ≈ 1.4*0.8 ≈ 1.1?? Hmm that seems modest vs vc=4.3. Let me compute more carefully: gravitational impulse from a Plummer-softened point passing at impact parameter b with speed v∞: Δv ≈ 2GM/(v) * b/(b²+ε²)^{...}... For ε=10 (halo!) the impulse is REDUCED a lot: effective 2GM b/(b²+ε²): at b=5, ε=10: 2*400*5/(125)=32/... wait formula for soft impulse ≈ 2GM/(v∞) * b/(b²+ε²)?? = 2*400*5/(25+100)/12.4 = 4000/125/12.4=2.58. Plus bulge component (ε=1.5): 2*60*5/(25+2.25)/12.4=600/27.25/12.4=1.77. Total Δv ~4.3?? (rough) — comparable to vc — significant ✓ tails will be strong. Stars closer (b=2): halo: 2*400*2/(4+100)/12.4=1600/104/12.4=1.24; bulge: 240/(4+2.25)/12.4=3.12 → Δv~4.4 ✓. OK stripping Δv ~3–5 vs binding v_esc~7.7 — substantial tail ejection without total vaporization ✓ good balance. Tails extend tens of units over subsequent 20–40 t.u. ✓.

**The bridge:** stars between cores get pulled both ways → bridge ✓ emergent.

**Check pass2 timing again with GM split irrelevant (MU=800 same)** ✓ as before.

**What about stars gaining energy from the TIME-VARYING potential?** Test particles in moving potential — energy not conserved → some heating — fine/expected.

**Numerical: substep h~0.0275; pericenter v=12.4 → step move 0.34 units vs εcc=2, εb=1.5, εh=10 → fine.**

**Now HUD phase — also add "SEP" decreasing arrow?** skip.

**One more polish: slight color grading — bg very dark blue; galaxies warm/blue — good contrast. Camera lookAt origin ✓.**

**Potential issue: additive accumulation over black with sRGB output — colors authored in 0..1.2 range; fine.**

**Core glow size 26 world → at end R~146, dist ~146: px = 26*1159/146 = 206px — halo ✓ under typical point cap (usually ≥ 1024 desktop; some Macs 511?? Apple M-series: 511?? Actually Apple GPUs ALIASED_POINT_SIZE_RANGE max = 511! Hmm — M1/M2 Macs: point size max 511 — 206 < 511 ✓ fine. Haze max 12.5 world → ~100px ✓. Even if a driver clamps to 64, haze shrinks — degraded but not broken. OK.**

Wait, iOS Safari: point size max 511 too ✓; Android Adreno: 1024 ✓. OK.

**Now think again about the requirement "at least 20,000 stars rendered as glowing points (additive blending)"** — 30k/galaxy ✓ + haze extra ✓. "colours going from warm yellow cores to blue-white arms" ✓. "tidal tails and bridges" ✓ emergent. "slowly orbiting camera" ✓. "dark starfield background" ✓. "small on-screen label with simulated time in Myr" ✓. "rAF timestamp" ✓ using tms. "GPU or cheap approximation" ✓ GPU FBO integration (restricted three-body). "full-window canvas + resize" ✓. "starts automatically" ✓. "everything important in first 30s" ✓ choreographed.

Let me also double check **the sim runs on the GPU but core pair integrated on CPU** — that's fine ("GPU or cheap approximation" — both!).

**Time label**: they said "small on-screen label with the simulated time in millions of years" ✓ top-left.

Now — **careful writing of the shaders with exact GLSL** (GLSL1):

simVert:
```glsl
varying vec2 vUv;
void main(){ vUv=uv; gl_Position=vec4(position.xy,0.,1.); }
```

copyFrag:
```glsl
uniform sampler2D tSrc; varying vec2 vUv;
void main(){ gl_FragColor=texture2D(tSrc,vUv); }
```

velFrag:
```glsl
precision highp float;
uniform sampler2D tPos; uniform sampler2D tVel;
uniform vec3 uCoreA; uniform vec3 uCoreB;
uniform vec4 uGrav; // GM_B, EB2, GM_H, EH2
uniform float dt;
varying vec2 vUv;
void main(){
  vec3 p=texture2D(tPos,vUv).xyz;
  vec3 v=texture2D(tVel,vUv).xyz;
  vec3 dA=uCoreA-p; float qA=dot(dA,dA);
  vec3 dB=uCoreB-p; float qB=dot(dB,dB);
  float iAb=inversesqrt(qA+uGrav.y); float iAh=inversesqrt(qA+uGrav.w);
  float iBb=inversesqrt(qB+uGrav.y); float iBh=inversesqrt(qB+uGrav.w);
  vec3 a=dA*(uGrav.x*iAb*iAb*iAb+uGrav.z*iAh*iAh*iAh)
        +dB*(uGrav.x*iBb*iBb*iBb+uGrav.z*iBh*iBh*iBh);
  v+=a*dt;
  float s2=dot(v,v);
  if(s2>4900.0) v*=70.0/sqrt(s2);
  gl_FragColor=vec4(v,0.0);
}
```
(ShaderMaterial adds precision automatically; including again is harmless? Redeclaring precision may conflict — three prepends `precision highp float;` already; do NOT redeclare. Omit.)

posFrag:
```glsl
uniform sampler2D tPos; uniform sampler2D tVel; uniform float dt;
varying vec2 vUv;
void main(){
  vec4 P=texture2D(tPos,vUv);
  vec3 V=texture2D(tVel,vUv).xyz;
  gl_FragColor=vec4(P.xyz+V*dt*dt?? 
```
careful: P.xyz + V.xyz*dt ✓.

starsVert:
```glsl
uniform sampler2D uPosTex;
uniform float uProj;
uniform float uTime;
uniform float uExposure;
attribute vec3 aColor;
attribute vec4 aProp;
varying vec3 vColor;
varying float vAlpha;
void main(){
  vec4 P=texture2D(uPosTex,position.xy);
  vec4 mv=modelViewMatrix*vec4(P.xyz,1.0);
  float dist=max(0.1,-mv.z);
  float ps=aProp.x*uProj/dist;
  float cl=max(ps,1.25);
  float dim=ps<1.25?(ps*ps)/(1.25*1.25):1.0;
  float tw=1.0-aProp.w*(0.5+0.5*sin(uTime*(0.55+fract(aProp.z)*1.7)+aProp.z*63.0));
  gl_PointSize=cl;
  gl_Position=projectionMatrix*mv;
  vColor=aColor*(uExposure*dim*tw);
  vAlpha=aProp.y;
}
```
Hmm `position` is attribute vec3 — position.xy in [0,1] ✓.

starsFrag:
```glsl
varying vec3 vColor; varying float vAlpha;
void main(){
  vec2 q=gl_PointCoord*2.0-1.0;
  float d2=dot(q,q);
  if(d2>1.0) discard;
  float g=(exp(-d2*3.4)+0.16*exp(-d2*1.2))*(1.0-smoothstep(0.72,1.0,d2));
  gl_FragColor=vec4(vColor*(g*vAlpha),1.0);
}
```

glowVert:
```glsl
attribute float aSize; attribute float aAlpha; attribute float aKind; attribute vec3 aColor;
uniform float uProj;
varying vec3 vColor; varying float vKind;
void main(){
  vec4 mv=modelViewMatrix*vec4(position,1.0);
  gl_PointSize=aSize*uProj/max(0.1,-mv.z);
  gl_Position=projectionMatrix*mv;
  vColor=aColor*aAlpha; vKind=aKind;
}
```
glowFrag as sketched.

bgVert:
```glsl
attribute float aSize; attribute vec3 aColor; attribute float aTw;
uniform float uPR; uniform float uTime;
varying vec3 vColor;
void main(){
  vec4 mv=modelViewMatrix*vec4(position,1.0);
  gl_Position=projectionMatrix*mv;
  float tw=1.0-aTw*0.5*(0.5+0.5*sin(uTime*(0.4+fract(aTw*13.7)*1.3)+aTw*97.0));
  gl_PointSize=aSize*uPR;
  vColor=aColor*tw;
}
```
bgFrag: gaussian disc:
```
vec2 q=gl_PointCoord*2.-1.; float d2=dot(q,q); if(d2>1.) discard;
float g=exp(-d2*3.5)*(1.0-smoothstep(0.7,1.,d2));
gl_FragColor=vec4(vColor*g,1.0);
```

All additive ONE/ONE, no depth.

**Points objects:** stars Points (starsMat), bg Points (bgMat), glow Points (glowMat). scene.add each; frustumCulled=false all.

**Now camera near plane 0.5, far 8000** (bg at 2400 max ✓).

**Renderer:** `new THREE.WebGLRenderer({antialias:false, powerPreference:'high-performance'})`; setClearColor(0x02030a, 1).

Wait — clear color with additive content: background near-black ✓. scene.background = null; use setClearColor.

**Let me reconsider `uExposure`:** 1.0; I'll set 1.15 — mild.

Also fold a global STAR brightness into color already ✓.

**Potential visual issue — inner disk oversaturation hiding spiral structure near center:** bulge warm saturated core with disk arms starting r>2 — classic ✓.

**Check arm contrast:** arm stars 60% with brightness ×1.0 vs field 40% ×0.72 → contrast ~2:1 per unit area?? Arm surface density enhancement: stars concentrated σθ~0.2 rad: arm peak density ~ armFrac/(σθ√(2π) * 2 arms) vs field uniform: at r=6: arms: 0.6/(2*0.2*2.5)=0.6/1.0=0.6 per rad?? peak linear density vs field 0.4/(2π)=0.064 per rad → peak/field ≈ 9× ✓ strong grand-design arms with brightness weighting → visible ✓ plus haze arms glow ✓.

**Now — sanity on total star velocity scatter vs disk stability:** vr 0.05vc, vz 0.04vc — cold disk ✓ arms stay thin.

**Bulge pulsation:** isotropic velocities ~0.3–0.85 vc + streaming 0.55vc: total ~0.9vc → these stars orbit at r±~30% — gentle breathing of bulge — invisible in glow ✓.

**Write phase/label code robustly** ✓ as sketched.

**One more idea — "collapse" of the HUD during first seconds:** static ✓ fine.

**Auto-quality:** if fps low, reduce pixelRatio? Implement light adaptive: track avg frame time over 60 frames; if >26ms and pixelRatio>1 → setPixelRatio(max(1, pr-0.25)) + resize. Cheap insurance ✓ include (simple, ~10 lines).

**Double-check the initial DataTexture w channel:** posInit w = 0 ✓ irrelevant.

**Dispose:** init textures disposed after copy ✓.

**Sim camera:** `new THREE.OrthographicCamera(-1,1,1,-1,0,1)`; quad at z=0 ✓. Sim materials: `depthTest:false, depthWrite:false`.

**Check: renderer.render(simScene, simCam) — simScene contains quad mesh; must not have scene fog/background — default null ✓. autoClear clears RT to clear color then quad covers all ✓.**

**Verify swap correctness for first frame:** idx starts 0; vel pass reads rtV[0] (init) writes rtV[1]; pos reads rtP[0], rtV[1] writes rtP[1]; idx→1. Points read rtP[1] ✓.

**Uniform vector reuse:** allocate once.

**Now write phase logic + slow-mo + counters cleanly:**

```js
let passages=0, prevS=1e9, descending=false;
function trackPassages(S){ if(S<prevS){descending=true;} else if(descending){ if(prevS<17.5) passages++; descending=false; } prevS=S; }
```

phaseName():
```js
function phaseName(S){
  if(simT>64 && S<4) return 'MERGER REMNANT';
  if(passages===0) return S<34?'FINAL APPROACH':'FIRST APPROACH';
  if(S<4.2) return 'COALESCENCE';
  if(S<13){
    if(passages===1) return 'FIRST PASSAGE · BRIDGE';
    if(passages===2) return 'SECOND PASSAGE';
    return 'FINAL PASSAGES';
  }
  if(passages===1) return 'TIDAL TAILS EJECTING';
  if(passages===2) return 'TAILS EXPANDING';
  return 'RAPID INSPIRAL';
}
```

**HUD value updates:** cache DOM refs; update strings each frame (fine).

Number formatting: time `+ ${String(Math.min(999,Math.floor(myr))).padStart(3,'0')} MYR`; after 999 keep counting (padStart handles) ✓.

**One more thing: importmap** — provided by environment; do NOT include. ✓

**Also they said addons available but not required.** I use none ✓.

**Let me write the CSS fully & HTML skeleton:**

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Galactic Collision — Tidal Disruption</title>
<style>
  :root{ --ink:#dfe9f5; --dim:rgba(148,175,205,.55); }
  html,body{height:100%}
  body{margin:0;background:#020409;overflow:hidden;font-family:ui-monospace,'SF Mono','Cascadia Code',Menlo,Consolas,'Liberation Mono',monospace;}
  canvas{position:fixed;inset:0;display:block}
  #vig{position:fixed;inset:0;pointer-events:none;background:radial-gradient(125% 95% at 50% 45%,rgba(0,0,0,0) 55%,rgba(1,2,7,.55) 100%)}
  #hud{position:fixed;top:22px;left:24px;pointer-events:none;border-left:1px solid rgba(150,180,215,.28);padding-left:12px;color:var(--ink);font-size:10px;letter-spacing:.16em;line-height:1.9;user-select:none}
  #hud .lab{display:inline-block;width:3.2em;color:var(--dim)}
  #hud .ph{margin-top:6px;color:#8fc6e4;letter-spacing:.22em}
  #title{position:fixed;left:24px;bottom:26px;pointer-events:none;transition:opacity 2.4s ease,transform 2.4s ease}
  #title h1{margin:0 0 7px;font-size:13px;font-weight:500;letter-spacing:.5em;color:#e8eff8}
  #title p{margin:0;font-size:10px;letter-spacing:.18em;color:var(--dim)}
  #title.gone{opacity:0;transform:translateY(8px)}
  #cap{position:fixed;right:24px;bottom:28px;pointer-events:none;text-align:right;font-size:9px;letter-spacing:.24em;color:rgba(140,168,198,.38)}
  @media (max-width:640px){ #cap{display:none} }
</style>
</head>
<body>
<div id="vig"></div>
<div id="hud">
  <div><span class="lab">T</span><span id="hT">+000 MYR</span></div>
  <div><span class="lab">SEP</span><span id="hS">131.3 KPC</span></div>
  <div><span class="lab">VEL</span><span id="hV">155 KM/S</span></div>
  <div class="ph" id="hP">FIRST APPROACH</div>
</div>
<div id="title"><h1>GALACTIC COLLISION</h1><p>TWO SPIRAL GALAXIES · TIDAL DISRUPTION SIMULATION</p></div>
<div id="cap">RESTRICTED THREE-BODY · 65 536 PARTICLES · GPU-INTEGRATED GRAVITY</div>
<script type="module"> ... </script>
</body></html>
```

**Now — one open question: does the encounter axis orientation relative to camera start look good?** Camera ang0=1.12 rad: camera at (cos1.12=0.436, sin=0.900)*R cos el → mostly +z side. Galaxies along x-axis → projected separation ≈ |sin(angle between x and view)|... view dir from cam to origin ≈ −(0.436,·,0.900): separation along x appears with horizontal screen component: screen-right vector = normalize(cross(up, viewDir))... whatever — the pair will be seen obliquely (good, ~64° between view dir and x-axis → separation largely across screen ✓). Rotation of camera over time changes this ✓.

Also galaxy disks: A normal (0.16,−0.94,−0.30) — disk plane contains... seen from cam elevation ~0.34 — disks appear as ellipses ✓.

**Vertical velocities of disk stars in world frame via basis ✓ handled by emit transform.**

**Now, carefully re-examine the emit() world-transform math:** local (lx,ly,lz) with basis e1,e2,n: world = C + e1*lx + e2*ly + n*lz ✓ and velocity similarly ✓.

**Star positions for spare slots must not disturb sim:** at (5e4,0,0): gravity from cores: a = 800*5e4/(2.5e9)^1.5 = 4e7/1.25e14 = 3.2e-7 ✓ negligible; stays ✓.

**dt accumulation with slow-mo:** acc integrates scaled time ✓ sim label consistent ✓.

**Check stepCores initial drag gate uses simT (module-level) ✓.**

**One risk: with the SLOWMO factor dipping when S≈9.5, at the very start S=105 → factor 1 ✓; S decreases monotonically to pericenter → slowmo engages smoothly ✓ (as S→9.5, factor→0.38; the passage takes ~2.5 t.u. → real duration ~2.5/0.45avg ≈ 5.5s?? hmm — passage "near S=9.5±3.5" lasts maybe 1.5 t.u. at avg factor ~0.55 → ~2.7s real of slo-mo — good drama; overall pass window (S<20) ~3 t.u. → ~6s real?! Hmm that might make first passage drag: total real time for S from 25→9.5→25: sim Δt ≈ 2.8 t.u.; factors: at S=25: 1−0.62*exp(−(15.5/3.5)²)=1−0.62*exp(−19.6)≈1; S=15: 1−0.62*exp(−1.84)=0.896; S=12: 1−0.62*0.687=0.574; S=9.5: 0.38; so effective sim rate ~0.6 avg over the window → real ≈ 2.8/0.6/3.3?? wait: real dt = simDt/(SPEED*factor): total real = ∫dtsim/(3.3*f(S)): ≈ (1/3.3)*∫dtsim/f: ∫dtsim/f ≈ let's approx sim time spent: S 25→13: 1.1 t.u. (fast, f~0.95) → 1.16; S 13→9.5: 0.5 t.u. f~0.5 → 1.0; S 9.5→13: 0.5 f 0.5 → 1.0; 13→25: 1.1 f 0.95 → 1.16; total ≈ 4.3s real. OK ~4.3s for the pericenter swing — dramatic but not stuck ✓. And total timeline shifts: effective SPEED reduced only near passages; overall milestones in real time roughly: pass1 ~6–8s, pass2 ~12–15s, merge ~18–21s ✓ within window ✓.

Hmm — one subtlety: slowmo reduces time-average SPEED → milestones later than earlier estimates by ~15%. Merge ~t=52–58 sim → real ≈ 17–19s + slowmo extra ~2s → ~19–21s ✓ still fine; remnant 21–30s ✓.

**Also double check drag won't merge cores before pass2 (i.e., pass1 must remain a flyby with r_a≈24):** drag Δv at pass1 estimated 1.7–2.0 → r_a 22–26 ✓.

But wait — drag ALSO acts during the outbound leg (t 20–30, r 10→24: exp(−(r/9)²): at r=15: 0.06; contributes Δv ~0.17*v(≈7)*∫... small ✓ apocenter slightly less — fine.

**And continuous decay between pass2 and coalescence: circularized r≈9 → near-drag kicks at r<4 after decay ~7–9 t.u. → coalescence ~16–19s real ✓.**

Post-merge: cores at r~1.5 orbiting fast (period ~0.2s real) with slowmo≈1 ✓; combined glow steady ✓.

**Now consider: is there any chance the cores get EJECTED (slingshot) due to softened potential quirk?** No — drag only removes energy ✓.

**Numerical drift of barycenter from drag:** drag applies equal-opposite on the pair in relative coords → barycenter EXACT ✓. Star forces use core positions from d ✓ consistent.

**Now the code for adaptive DPR:**
```js
let ftAvg=16.7, ftCount=0;
in loop: ftAvg+=(dtmsReal-ftAvg)*0.05; every 120 frames: if(ftAvg>30 && pr>1){ pr=Math.max(1,pr-0.25); renderer.setPixelRatio(pr); onResize(); }
```
dtmsReal from t-lastRaw before clamp. Simple ✓.

**Ensure uTime for stars — sim time or real?** twinkle in real seconds ✓ t.

**What if user's device is 30fps?** nSub adapts ✓ h stays ~0.033–0.05: at 30fps: acc=0.05*3.3=0.165 → nSub=4 (cap) → h=0.041 — slightly coarse but ok (ceil(0.165/0.03)=6 → capped 4 → h=0.041) — stability fine (h 0.041 at v 12: step 0.5 — ok with softening).

**Also — initial camera before first frame:** loop sets it ✓.

**Everything considered — now also double check `renderer.getDrawingBufferSize`** exists (r186: `renderer.getDrawingBufferSize(target: Vector2)`) ✓.

**Also THREE.Points with ShaderMaterial and attribute named `position` holding uv — vertex shader uses `position` ✓ provided.**

Hmm — one thing: for Points, three.js material program includes `#ifdef USE_SIZEATTENUATION`? Only for built-in; ShaderMaterial raw ✓.

**Attribute setup code:**
```js
const starGeo=new THREE.BufferGeometry();
starGeo.setAttribute('position', new THREE.BufferAttribute(uvArr,3));
starGeo.setAttribute('aColor', new THREE.BufferAttribute(colArr,3));
starGeo.setAttribute('aProp', new THREE.BufferAttribute(propArr,4));
```
uvArr Float32Array(NP*3): for i: u=((i%TEXS)+0.5)/TEXS; v=((i/TEXS|0)+0.5)/TEXS; z=0 ✓.

**One more consideration — texture coordinate v orientation:** DataTexture row 0 = v=0 → maps to texel row 0 ✓ particle index i at uv computed exactly matches DataTexture layout (row-major) ✓ since both use same convention (three DataTexture: data[0] is (0,0) texel, uv (0.5/TEXS,...) ✓ and RT rendering: the quad's uv → framebuffer: rendering into RT with vUv, then sampling RT with same uv — need consistent orientation between RT write and RT read: writing at vUv writes to texel at (vUv*res) with y... In WebGL, framebuffer y is UP in NDC; texture v=0 = bottom row. Quad uv v=0 at bottom (PlaneGeometry uv 0 at bottom) → writes texel row bottom ✓; sampling with v=0 reads bottom ✓ consistent ✓. And DataTexture init: copied via the copy shader (sample init texture with vUv, write to RT at vUv) → orientation consistent regardless of DataTexture row order ✓✓ — that's why the copy pass approach is robust. Particle i lives at texel (i%256, i/256) in BOTH init texture and RT (since copy preserves uv↔texel mapping: init texture texel (u,v) read → written to RT texel (u,v) ✓). ✓

**Glow points & bg: frustumCulled false ✓.**

**Order of scene children & renderOrder:** all additive commutative ✓; still set renderOrder: bg 0, stars 1, glow 2 (any).

**Also — starsMat needs `uniforms: { uPosTex, uProj, uTime, uExposure }` ✓; update uPosTex each frame after sim ✓ (done in simStep).**

**Wait — potential double-render of simScene needing `quad.frustumCulled=false`** (orthographic, at origin, frustum [-1,1] — plane exactly fills; culling fine; set false anyway ✓).

**Check glow positions attribute update:** glowGeo positions dynamic (setUsage DynamicDrawUsage) ✓.

**HUD numbers: initial values** — set at build (SEP 131.3 KPC? initial S=105 units → 105*1.25=131.3 ✓; V=|v_rel|=3.22*48=154.5 ✓). 

**Now assemble the phase→HUD and check "MYR" formatting: start "T +000 MYR".** Fine.

**Final check of galaxy B tilt & tails:** B inclined 55° → its tails fan out of plane — 3D richness ✓.

**Also I want the two galaxies slightly different sizes?** Equal masses chosen for symmetric dynamics (barycenter centered → camera framing trivial ✓). Keep equal; visual variety via tilt/arm pitch/color ✓.

**Double-check `sstep` smoothstep JS helper** ✓.

**Potential problem: `pow(rnd(),1.7)` etc. fine.**

**gauss() at startup** uses rnd ✓ deterministic seed 88172645 (nonzero ✓ xorshift requires nonzero ✓).

**Write `emit` closure carefully** — define inside addGalaxy with captured arrays & idx local variable; return final idx for chaining (second galaxy starts at base offset anyway ✓ pass gi: base=gi*(NSTARS+NHAZE) with idx starting there ✓; spares filled after both).

Galaxy B tint arrays: [0.62,0.76,1.05] haze; A: [1.0,0.84,0.58].

**Also add per-galaxy slight brightness difference?** A slightly brighter warm; B cooler — subtle ✓ via tints & core glow colors ✓.

**Star color ramp function inline in loop** ✓ as sketched. Let me finalize the ramp math:
```js
const t=Math.min(1,Math.max(0,(r-1.2)/10.0)); // 0 at r=1.2 → 1 at 11.2
let mr=1.0-0.42*t, mg=0.86-0.14*t, mb=0.58+0.47*t;
```
→ at t=0: (1.0,0.86,0.58) warm; t=1: (0.58,0.72,1.05) blue-white ✓.
arm: mr+=0.03; mg+=0.05; mb+=0.10 (clamped ≤1.15)
field: mr+=0.06; mg+=0.02; mb-=0.06 (warmer, ≥0.3)
hot giants override ✓.

Brightness: arm: br=0.5+0.7*rnd(); field: br=0.34+0.5*rnd(); giants 1.5+0.5rnd.
Sizes: normal 0.34+0.42*rnd()^1.5; giants 0.9+0.55*rnd(); bulge 0.28+0.32*rnd()^2.

Bulge color: (1.0, 0.70+0.18rnd, 0.40+0.22rnd) × br (0.5+0.8rnd).

Hmm bulge brightness: 7200 stars dense → very bright — keep br 0.5–1.1 ✓ saturation desired.

**Haze alpha:** 0.028+0.05*rnd()^2 (mostly ~0.03, few 0.08) ✓ size 3.5+9*rnd()^2 → 3.5–12.5 ✓.

Also haze color scaled by (0.7+0.5*rnd()).

**Check overall luminous balance:** I'll set uExposure 1.1 and trust additive buildup; individual star contributions ~0.4–1.5; disk regions overlap 2–5 stars → 1.5–4 clipped → white-hot specks with colored fringes ✓ cinematic.

**Potential moiré/flicker of sub-pixel stars:** dim factor (ps/1.25)² conserves flux ✓ reduces shimmer ✓.

**Now — write JS for bg stars:**
```js
const NBG=2600;
bgPos=new Float32Array(NBG*3); bgCol=new Float32Array(NBG*3); bgProp=new Float32Array(NBG*2)?? attributes: aSize float, aTw float → two attrs or pack: use aProp vec2? simpler two Float32 attrs.
for i: dir random on sphere: z=2u-1, phi; r=1400+1100*rnd();
col: base=0.5+0.5*rnd(); temp=rnd(); 
 if temp<0.18: warm (1,0.82,0.66) else if temp>0.80: cool (0.72,0.83,1.0) else white (0.92,0.95,1.0);
 brightness=0.10+0.55*rnd()*rnd(); if(rnd()<0.03) brightness=1.0, size bigger.
 size=0.7+1.5*rnd()*rnd(); bright ones 2.6.
 tw= rnd()<0.35? 0.5+0.5rnd() : 0.0;
```
multiply color×brightness ✓.

**Now — check bg visible but subtle:** 2600 stars brightness ~0.3 → visible on black ✓.

**One more feature — requirement says "may loop or continue after 30s"** — continue ✓ (physics keeps evolving; camera keeps orbiting; after merger it's remnant evolution; fine. Maybe at t>75s, nothing new — acceptable. Could add slow fade-restart? No — continue is explicitly allowed.)

Hmm — after coalescence, drag near-field keeps cores at r~0.8–1.5 orbiting; the double bulge potential → stars swirl; tails keep expanding/shearing → still alive ✓.

**Let me also reconsider NHAZE=2200 vs fill:** 4400 haze sprites avg ~ (size 3.5–12.5 avg ~7.6 world → px ~63 dia → area 3100) × 4400 = 13.6M px/frame + edge-fade discard (~21% early-out via discard d2>1 only 21.5%... discard happens for corners; gaussian computed for remaining. Fine ~11M effective. At 60fps = 0.66 Gfrag/s with cheap shader — OK for discrete GPUs & Apple silicon; integrated Intel might chug → adaptive DPR reduces 4× at pr 1 ✓ (fill scales with DPR²) ✓ good insurance.

Also stars: 64k × ~(2.5px dia → 5px²) = 0.3M ✓ negligible.

**Also: additive blending without depth — glow nuclei visible THROUGH disk — correct aesthetic ✓.**

**Sanity: initial camera at R=172 — galaxies at ±52.5 + disks → angular half-extent ~ atan(64/172)=20.4° vs half-FOV vertical 25° — fits vertically even when separation axis vertical-ish ✓; horizontal typically wider ✓.**

**Now, code the init copy pass BEFORE first sim step and BEFORE first render** ✓ order in main():

```js
1. renderer, scene, camera
2. build arrays (galaxies + spares)
3. DataTextures posInit/velInit
4. RTs ×4
5. simScene quad + materials (copy/vel/pos)
6. copy pos & vel into slot 0
7. dispose init textures
8. star geometry/material/points; bg; glow
9. resize(); listeners
10. requestAnimationFrame(loop)
```

**Also — set `starsMat.uniforms.uPosTex.value = rtP[idx].texture` initially (idx=0 → rtP[0] which now holds init) — but first simStep already sets it ✓ set anyway.**

**Check: THREE.DataTexture needs .needsUpdate=true ✓ and `flipY=false` default for DataTexture ✓ (irrelevant via copy).**

**Edge: FloatType DataTexture + NearestFilter sampling in WebGL2 ✓ (no OES needed for nearest in WebGL2? WebGL2 samples RGBA32F with nearest natively ✓).**

**RT texture params:** RT default min/mag Linear — for float linear needs OES_texture_float_linear — I set Nearest explicitly in options ✓.

**gl_FragColor w=1, blending ONE,ONE adds alpha too → dst alpha accumulates >1 — canvas alpha:false → fine ✓ (renderer alpha default false ✓).**

**Now, write everything out — also double check the vertex shader for glow uses `position` attribute (vec3 world coords updated per frame) ✓ and per-vertex attributes aColor,aSize,aAlpha,aKind ✓.**

**Cap: `gl_PointSize` needs no +0.5 alignment... fine.**

Let me also double check the **vel shader's softening values as uniforms vec4 uGrav = (60, 2.25, 340, 100)** ✓ set once.

**HUD: also show sim rate? no.**

**One more idea for extra polish within budget: the "SLOW-MO" could also slightly ease camera FOV?** skip — camera choreography is enough.

Alright — also **check that at t=0 the galaxies look like proper spirals from camera:** arms trailing, 2 arms each, plus haze — ✓.

**Potential concern: disk stars' initial circular orbits in the PRESENCE of the companion's static potential?** Companion at 105 away: tidal influence negligible ✓.

**Write the phase of arms relative to companion? irrelevant.**

**One more subtlety — the CORES' glow: during approach the cores are at bulge centers; glow halo alpha 0.5 peak 0.47 → adds ~0.2–0.4 luminance over bulge — nice.**

**Let me also make sure the two nuclei vertices' positions track cores — yes same buffer.**

**Battery: requestAnimationFrame timestamps — first callback tms may be large (page load time) — fine since I diff.**

**Also handle context loss? skip (out of scope).**

**Write the final `phaseName` thresholds tuned to sim times: simT>64 → remnant.** With slowmo delays, coalescence real ~19s = sim ~55–60 hmm: real 19s × avg effective ~2.9 t.u./s ≈ 55 t.u. → 'MERGER REMNANT' at simT>64 → ~22s real ✓ ok.

Also 'COALESCENCE' when S<4.2 ✓ (during final inspiral dips).

**Check trackPassages threshold 17.5:** pericenters ~9.7, then later ~10 — count ✓. Apocenter swings up to 24–26 — S increases past 17.5 → descending flag resets ✓ no false counts.

Hmm — but wait: between pass1 (S min 9.7) and apocenter 24: S rises through 17.5 ✓ fine. BUT what if drag makes pass1 apocenter < 17.5? Then S never exceeds 17.5 after pass1... then next minimum (pass2 at S~9) — the rising-falling cycle still detected: descending set when S decreasing from 9.7's rise... let me trace: S falls 105→9.7 (descending=true); rises 9.7→15 (S>prevS & descending → count passage1 IF prevS<17.5 ✓ (prevS is the minimum 9.7) ✓ passage counted at the FIRST rising frame ✓ good — count happens on rise-start using the minimum value ✓. Then S rises to apo 15, falls again → descending, min ~9 → rises → count passage2 (prevS=9 <17.5 ✓). So even with small orbits, passages count ✓. And 'passages≥3' labels kick in ✓.

**Now assemble EVERYTHING into final code. Also add small try/catch with fallback message.**

Also — I realize I should double check the **`uv` attribute existence for sim quad**: PlaneGeometry has uv ✓.

**Sim quad size:** PlaneGeometry(2,2) → positions ±1 ✓ vertex shader passes through ✓.

**Check `renderer.setRenderTarget(rtV[1-idx])` then `render` — viewport set to RT size automatically ✓.**

**After sim steps: `renderer.setRenderTarget(null)` before scene render ✓ (done at end of simStep; loop renders scene after ✓ but if nSub loop, each simStep ends with setRenderTarget(null) — then next substep sets again — harmless ✓.**

**One more possible pitfall: `material.uniforms` shared references — velMat & posMat separate ✓.**

**Also for copy pass, need `quad.material=copyMat` then restore — handled by assignment each time ✓.**

**DPI change on zoom → resize listener catches via window resize? zoom triggers resize ✓.**

Let me now also verify **glow nuclei won't be occluded weirdly** — no depth ✓.

**Check the streak orientation:** gl_PointCoord x along screen x ✓ horizontal streak ✓.

**Time to also reconsider the arm pitch constants:** k=1/tan(pitch): pitch 16° → tan 0.2867 → k=3.49 → A k=3.5 ✓; B pitch 19°: tan 0.344 → k=2.9 ✓.

**Also — both galaxies' arm count 2.** Maybe B gets 3 arms for distinction? 3-arm at pitch 21° (k=2.6), phase offsets 2π/3. Hmm — 3-armed spiral is a nice distinguishing touch: B arms=3. But tail morphology from B still fine. Let me give B 3 arms (m*2π/3) with slightly looser scatter. Wait — B's role: second passage wrecks it; 3 arms look distinct ✓ do it. In code: armIndex m = floor(rnd()*arms); offset = m*2π/arms.

For A: arms=2, offset=m*π.

**Also disk size: B slightly smaller? RDISK same 12; fine.**

**Final param table:**
```
A: center(-52.5,0,0) vel(1.505,0,-0.575) n=norm(0.16,-0.94,-0.30) k=3.5 phase0=0.35 arms=2
B: center( 52.5,0,0) vel(-1.505,0,0.575) n=norm(-0.50,-0.58,0.64)?? 
```
Hmm wait: B normal −0.50 x-component: the B disk tilts toward −x (toward companion) — fine.

Actually let me double-check B normal y: −0.58 → prograde ✓; z 0.64: B disk plane contains strong z-tilt → viewed from camera elevation +0.34 (above plane), B's disk tilts... n_z=0.64 means B's north pole leans +z (camera side) → we see B's disk more face-on ✓ nice variety (A more edge-on-ish: n_A=(0.16,−0.94,−0.30): n·viewdir? cam dir ~ (0.44, 0.33, 0.90)-ish: n_A·(0.44,0.33,0.90) = 0.07−0.31−0.27=−0.51 → A seen at 59° inclination (fairly edge-on, dramatic) ✓ B: n_B·dir = −0.22−0.19+0.58=0.17 → B nearly face-on early ✓ GREAT composition: one edge-on-ish, one face-on-ish, both evolving as camera orbits.

Wait — is A too edge-on to show spiral arms early? Inclination 59° — arms visible as ellipses ✓ fine (59° shows arms well).

**v_rel tangential sign & prograde disks — verify tails develop prograde (the classic long tails need prograde): disk L ≈ −y, orbital L=−y ✓ prograde ✓.**

**Let me finalize drift: ang=1.12+0.045t.**

At t=0: cam at angle 1.12 in XZ: pos=(R cos el cos 1.12, R sin el, R cos el sin 1.12) = (0.435R', 0.333R, 0.90R') with R'=R cos0.34=0.943R → (0.41,0.333,0.849)R. View of x-axis galaxies: separation direction (1,0,0) vs camera→origin dir (−0.41,−0.33,−0.85): the x-axis appears mostly horizontal-right?? screen-right = normalize(cross(up,(0,0,0)−pos))... cross((0,1,0), (−0.41,−0.33,−0.85)) = (1*(−0.85)−0*(−0.33), 0*(−0.41)−0*(−0.85), 0*(−0.33)−1*(−0.41)) = (−0.85, 0, 0.41)/|..| → screen right ≈ (−0.85,0,0.41). Galaxy A at (−52.5,0,0) relative to center: screen-x = dot((−52.5,0,0), right) = −52.5*(−0.85)=+44.6 → A appears RIGHT, B LEFT — fine either way ✓ separation mostly horizontal (44.6 of 52.5) ✓ with depth offset ✓ good.

**Alright — also final check of "brightness of arms vs core" in HUD-free visual: ok.**

Now, let me carefully write the whole file. I'll be methodical. Also add comments (in English — user's language is English ✓).

Additional micro-decisions while writing:

- `const TAU=Math.PI*2`.
- Avoid allocations in loop: reuse temp Vector3s.
- `starsMat.uniforms.uPosTex.value` — assign `.texture` each frame ✓.
- Make sure `uProj` set AFTER renderer sized ✓ call onResize() once before loop.

- **Nucleus glow might look like a weird dot if cores separate from bulge centers?** Cores ARE bulge centers ✓ (stars initialized around initial core positions; cores move with galaxy... wait — do the BULGE STARS follow the cores? The stars are test particles; the galaxy's stars move under the cores' gravity — the core drags its bound stars along ✓ standard restricted approach; bulge stars bound to their core (deep potential) ✓ they follow ✓.

- **Halo particles following**: halo is potential-only (massive, follows core by construction) ✓.

**Also: think about whether bulge stars remain bound during pericenter pass:** bulge stars v_esc ~11 vs impulse ~4 → mostly bound ✓ core stays bright ✓ (some swap → fine).

**Write the JS in a clean order with section comments.** Estimated ~450 lines total. Let me write it.

Also one more consideration on the **slowmo formula**: exp(−((S−9.5)/3.5)²) — at S=105: exp(−(95.5/3.5)²)=exp(−745)=0 ✓.

And **make sure slowmo doesn't stall at S≈9.5 for a long time during circular decay phase (r≈9 circle!)**: after circularization r≈9-10 — S stays ~9–10 → slowmo factor ~0.4 PERSISTENT during inspiral phase!! BAD: the final inspiral would crawl at 0.4× for ~7 t.u. → +5s real. Hmm. Fix: gate slow-mo by RADIAL VELOCITY (passages have high |v_rel| ~10–12; circular decay v~4.3): slow factor *= clamp((|v|−5.5)/4, 0, 1)?? At pass: v=12 → gate 1 ✓; circular r=9: v=4.6 → gate 0 ✓; during elliptical outbound/inbound v varies 5–12 — near apocenter v~2 → gate 0 ✓ fine (slowmo only near fast pericenter swings ✓ exactly desired). Implement: 
```js
const vv=core.v.length();
const gate=Math.min(1,Math.max(0,(vv-5.0)/3.5));
slow=1-0.62*Math.exp(-Math.pow((S-9.5)/3.5,2))*gate;
```
At circular v=4.6: gate=0 ✓. During pass1 inbound at S=13, v≈10 → gate 1 ✓.

**Also — check v_rel at apocenter2 ~ v_t=... E=−18ish, a=22: v_apo = sqrt(2(E+μ/r))=sqrt(2(−18+800/24))=sqrt(2*15.3)=5.5?? gate=(5.5−5)/3.5=0.14 — slight slowmo near apocenter×exp(−((24−9.5)/3.5)²)=e^{−17}≈0 → product 0 ✓ fine.**

Good.

**Now also think: do I want the slowmo at pass2 & 3 equally strong? depth 0.62 each time — pass3&4 are quick; fine.**

**One more numerical check — first pericenter REAL time with slowmo:** earlier ≈5.8s + slowmo extra ~1.5s ≈ 6.5–7s — hmm pushing late. Reduce approach: bump v_r slightly: v_r=3.2, v_t=1.12: v0²=10.24+1.25=11.5 → E=5.75−7.62=−1.87 → fall faster ~17 t.u.?? and pericenter: L=117.6; v_p=sqrt(2(80−1.87))=12.5 → r_p=117.6/12.5=9.4 ✓. Fall time ~17.5 t.u. → 5.3s + slowmo ~1.5 → pass at ~6.5s?? The slowmo mostly engages DURING passage (S<13 at t≈18.3) — the pre-passage approach at S 25→13 is quick (f≈0.9). Pass peak at ~5.5–6s ✓ good. Set v_rel=(−3.2, 0, 1.12). Recheck drag pass1: v_p=12.5 similar ✓ r_p=9.4 ✓.

Then r_max=428 (irrelevant), fine.

v_A=(1.6,0,−0.56), v_B=(−1.6,0,0.56). ✓

**And initial HUD VEL: |v_rel|=sqrt(10.24+1.2544)=3.391 → ×48=163 km/s ✓.**

**SEP initial: 105×1.25=131.3 ✓.**

Double-check **fall-time estimate with v_r=3.2:** E=−1.87, r_max=428; t from 105 to 9.4: using earlier integral approach with v0: v²(x) = v0²+2μ(1/r−1/r0): mean speed ~ sqrt at mid r~40: v²=11.5+1600(0.025−0.00952)=11.5+24.8=36.3→6.0; segments: 105→60: avg v≈ sqrt(11.5+1600(1/80−1/105))≈sqrt(11.5+4.57)=4.0 → 11.2 t.u.; 60→30: v at 45: sqrt(11.5+1600(0.0222−0.00952))=sqrt(31.8)=5.6; at 30: sqrt(11.5+1600*(0.0333−0.00952))=sqrt(49.5)=7.0 → avg 6.3 → 4.8; 30→15: at 22: sqrt(11.5+1600(0.0455−0.00952)=69)=8.3; at 15: sqrt(11.5+1600(0.0667−0.0095)=103)=10.1 → avg 9.2 → 1.63; 15→9.4: avg ~11.5 → 0.49; total ≈ 18.1 t.u. → 5.5s real ✓ pass1 at ~5.5–6s incl slight slowmo start ✓.

**Timeline recheck (real seconds):** pass1 ≈ 5.8; apo2 ≈ 5.8+ (half period 16/2*... orbit2 a≈21 P≈21.6: apo at +10.8 sim ≈ +3.3s?? hmm with slowmo added during pass (~+1.5s): apo2 ≈ 10.5s; pass2 ≈ 5.8+1.5+21.6/3.3=5.8+1.5+6.5≈13.8s; pass3 ≈ +8.3/3.3+slowmo≈+3.2 → 17s; circular ~r9 by simT≈47 (≈15.5s real); decay to r<4: ~+7 t.u. ≈ +2.4s → coalescence ≈ 18–19s real; remnant 19–30s ✓✓ good.

I might nudge SPEED to 3.45 to tighten slightly. Eh — keep 3.3, fine within window.

**Also — check pass2 Δv & subsequent with c_d=0.17:** pass2: v_p: E after pass1: v'≈12.5−(0.17*12.5*0.31*3≈1.97)=10.5 → E=55.1−80.4 (μ/rp: rp 9.4: 800/9.4=85.1) → E'=55.1−85.1=−30 → a=(rp+ra)/2 with ra: E=−μ/2a → a=800/60=13.3; rp: L2 = L1−rp*Δv_t≈117.6−9.4*1.97≈99 → rp=L/v_p... v_p2=sqrt(2(E'+85.1))=10.5 → rp=99/10.5=9.4 (circularization keeps rp~9.4); ra=2*13.3−9.4=17.2?? Hmm apocenter2 ≈17 (not 24) — period P=2π√(13.3³/800)=2π√(2352/800=2.94)=2π*1.715=10.8 t.u. → pass2 at simT≈19+10.8=29.8 (9.5s real incl slowmo ~10.5s) — EARLIER than my previous estimate. Then pass3 at ~+8: simT≈38 (12.5s); pass4 ~46 (15s); circularized ~r9 simT≈50; decay → merge simT≈57–60 (18.5s real). Tails have less time at wide separation (apo 17) — hmm — the "Antennae swing-out" is compressed: tails reach ~30–40 while cores at apo 17 — still fine visually (tails extend beyond core separation). But I'd like a bit more breathing: reduce c_d to 0.13: pass1 Δv≈1.5 → v'=11 → E'=60.5−85.1=−24.6 → a=16.2 → ra=23; P=2π√(4250/800=5.31)=14.5 → pass2 at 19+14.5=33.5 (11s real); pass2 Δv≈0.13*11*0.31*3=1.33 → v'=9.7?? v_p2=sqrt(2(24.6+85.1))?? wait E'=−24.6: v_p=sqrt(2(E'+85.1))=sqrt(120.9)=11.0 ✓; Δv=1.33 → v'=9.67 → E''=46.8−85.1=−38.3 → a=10.6 → ra≈11.8, P=2π√(1191/800=1.49)=7.67 → pass3 ≈41.2 (13.5s); pass3 Δv≈1.2 → v'=8.5 → E'''=36.1−85.1=−49 → a=8.15 → ra≈6.9?? rp: L: 117.6−9.4*(1.5+1.33+1.2)=76.5 → rp=76.5/8.5=9.0; a=8.15 < rp?! inconsistent again — the bookkeeping breaks because drag removes L faster than my crude ΔL. Reality: the orbit circularizes around r ≈ L²/μ/(1+e)… with L=76.5: r_circ=L²/μ=5852/800=7.3. So post-pass3 orbit ≈ circular r~7–8, P≈2π√(7.65³/800)?? softened... ≈2π*0.75=4.7?? sqrt(448/800=0.56)=0.75 → P≈4.7 t.u. Then continuous drag: dr/dt=−2 c_d r exp(−(r/9)²)≈−2*0.13*7.3*0.53=−1.0/t.u. → r 7.3→4 in ~4 t.u. → near-drag takes over → coalescence ≈ simT 41+4+2 ≈ 47–50 → ~15s real ✓; remnant 15–30s — hmm 15s of remnant. That's a long tail phase — but honestly the expanding tails + swirl ARE the show; plus slow camera drift keeps it alive. Alternatively bump c_d=0.15 middle. I'll set c_d=0.14. Expect coalescence ~15–18s real. Accept variance; emergent anyway.

Hmm — actually wait. I want to double-check the DRAG's effect on rp once more: drag ∝ −v removes angular momentum proportionally: rp stays ~constant while ra drops (circularization) — then once circular, r decays. So sequence of passages at rp≈9.4 with shrinking periods ✓ merged core at r~1.5 eventually via near-drag ✓.

**But hold on — rp≈9.4 while disks have radius 12:** repeated passages each shred outer disks more ✓ tails regenerate each pass ✓ good.

**Also consider: is pass1 possibly TOO close (stars plunging through companion core region)?** Stars passing within ε~1.5 of companion core get strong kick but softened ✓ max Δv bounded ✓ some scatter — fine (bulge exchange).

**OK — now let me also think about HUD "SEP" during post-merge: shows ~1.9 KPC — fine (binary core).**

**Also, "VEL" shows relative speed ~ small post-merge ✓.**

Now write the code FOR REAL. I'll be careful with GLSL string template literals and attribute setups.

One more detail — **three.js r186 ShaderMaterial vertex shader prelude includes `attribute vec3 position; attribute vec2 uv;` etc. — using `uv` in simVert ✓.**

Also **`modelViewMatrix`, `projectionMatrix` auto uniforms ✓.**

**For the sim materials, no matrices needed.**

**Write JS:**

```js
import * as THREE from 'three';

// ===== deterministic RNG =====
let _s = 0x9e3779b9 ^ 1234567;
function rnd(){ _s^=_s<<13; _s^=_s>>>17; _s^=_s<<5; return (_s>>>0)/4294967296; }
```
Careful: _s<<13 in JS on 32-bit via bitwise → yes bitwise ops coerce to int32 ✓; after xorshift keep >>>0 for output; state stays int32 ✓ nonzero forever (xorshift period 2^32−1) ✓.

```js
let _sp=null;
function gauss(){ if(_sp!==null){const v=_sp;_sp=null;return v;}
  const u=Math.max(rnd(),1e-12), v=rnd(), m=Math.sqrt(-2*Math.log(u));
  _sp=m*Math.sin(6.28318530718*v); return m*Math.cos(6.28318530718*v); }
```

Constants... then arrays, then addGalaxy.

Then a helper clamp, lerp.

Colors — define function ramp(r, arm).

**Emit function:** closes over e1,e2,n,C,CV components.

I'll write addGalaxy(gi, cfg) where cfg holds everything.

**Star loop body — final:**

```js
function addGalaxy(gi, cf){
  const n = new THREE.Vector3(...cf.n).normalize();
  const h = Math.abs(n.y)<0.92 ? new THREE.Vector3(0,1,0) : new THREE.Vector3(1,0,0);
  const e1 = new THREE.Vector3().crossVectors(h,n).normalize();
  const e2 = new THREE.Vector3().crossVectors(n,e1).normalize();
  const [cx,cy,cz]=cf.c, [vx,vy,vz]=cf.v;
  const a1x=e1.x,a1y=e1.y,a1z=e1.z, a2x=e2.x,a2y=e2.y,a2z=e2.z, an=n.x,nyv=n.y,nz=n.z;
  let idx = gi*(NSTARS+NHAZE);
  const emit=(lx,ly,lz,ux,uy,uz, r,g,b, size,al,ph,tw)=>{
    const i4=idx*4, i3=idx*3;
    posArr[i4]   = cx + a1x*lx + a2x*ly + an*lz;
    posArr[i4+1] = cy + a1y*lx + a2y*ly + nyv*lz;
    posArr[i4+2] = cz + a1z*lx + a2z*ly + nz*lz;
    posArr[i4+3] = 0;
    velArr[i4]   = vx + a1x*ux + a2x*uy + an*uz;
    velArr[i4+1] = vy + a1y*ux + a2y*uy + nyv*uz;
    velArr[i4+2] = vz + a1z*ux + a2z*uy + nz*uz;
    velArr[i4+3] = 0;
    colArr[i3]=r; colArr[i3+1]=g; colArr[i3+2]=b;
    propArr[i4]=size; propArr[i4+1]=al; propArr[i4+2]=ph; propArr[i4+3]=tw;
    idx++;
  };
  const NB=Math.floor(NSTARS*0.24);
  for(let i=0;i<NB;i++){
    const X=Math.max(rnd(),1e-6);
    let r=1.5/Math.sqrt(Math.pow(X,-2/3)-1);
    if(r>4.6) r=0.5+4.1*rnd();
    const u2=rnd()*2-1, ph=rnd()*TAU, s1=Math.sqrt(Math.max(0,1-u2*u2));
    const dx=Math.cos(ph)*s1, dy=Math.sin(ph)*s1, dz=u2;
    const vc=vCirc(r);
    const sp=vc*(0.28+0.55*rnd());
    let tx=nyv*dz-nz*dy, ty=nz*dx-an*dz, tz=an*dy-nyv*dx;
    const tl=Math.hypot(tx,ty,tz)||1, cf2=vc*0.55/tl;
    const br=0.5+0.75*rnd();
    emit(r*dx,r*dy,r*dz, dx*sp+tx*cf2, dy*sp+ty*cf2, dz*sp+tz*cf2,
         1.0*br, (0.70+0.18*rnd())*br, (0.40+0.22*rnd())*br,
         0.28+0.34*rnd()*rnd(), 1, rnd(), 0.3+0.3*rnd());
  }
  for(let i=NB;i<NSTARS;i++){
    let r=RDISK*Math.pow(rnd(),1.7);
    if(r<0.8) r=0.8+0.5*rnd();
    r*=1+0.05*gauss();
    const arm=rnd()<0.60;
    let th;
    if(arm){
      const m=Math.floor(rnd()*cf.arms);
      let sig=0.13+0.012*r; if(rnd()<0.10) sig*=2.4;
      th=cf.ph0 + m*TAU/cf.arms - cf.k*Math.log(Math.max(r,1.1)) + gauss()*sig;
    } else th=rnd()*TAU;
    const z=gauss()*(0.13+0.030*r)*(arm?0.8:1);
    const ct=Math.cos(th), st=Math.sin(th);
    const vc=vCirc(r)*(1+0.03*gauss());
    const vr=0.05*vc*gauss(), vzz=0.04*vc*gauss();
    const t=Math.min(1,Math.max(0,(r-1.2)/10));
    let cr=1.0-0.42*t, cg=0.86-0.14*t, cb=0.58+0.47*t;
    let br, size;
    if(arm && rnd()<0.085){ cr=0.60; cg=0.72; cb=1.12; br=1.35+0.5*rnd(); size=0.85+0.55*rnd(); }
    else if(arm){ cr+=0.04; cg+=0.05; cb=Math.min(1.15,cb+0.10); br=0.50+0.70*rnd(); size=0.34+0.42*Math.pow(rnd(),1.5); }
    else { cr=Math.min(1.05,cr+0.07); cg+=0.02; cb=Math.max(0.34,cb-0.08); br=0.34+0.50*rnd(); size=0.32+0.38*Math.pow(rnd(),1.5); }
    emit(r*ct, r*st, z, -st*vc+ct*vr, ct*vc+st*vr, vzz,
         Math.min(1.2,cr)*br, Math.min(1.2,cg)*br, Math.min(1.25,cb)*br,
         size, 1, rnd(), 0.25+0.55*rnd());
  }
  for(let i=0;i<NHAZE;i++){
    let r=13.5*Math.pow(rnd(),2.3); if(r<0.7) r=0.7+0.5*rnd();
    let th;
    if(rnd()<0.45){ const m=Math.floor(rnd()*cf.arms);
      th=cf.ph0+m*TAU/cf.arms - cf.k*Math.log(Math.max(r,1.1)) + gauss()*(0.25+0.02*r); }
    else th=rnd()*TAU;
    const z=gauss()*(0.45+0.05*r);
    const ct=Math.cos(th), st=Math.sin(th);
    const vc=vCirc(r)*(1+0.04*gauss());
    const br=0.7+0.5*rnd();
    emit(r*ct, r*st, z, -st*vc, ct*vc, 0.03*gauss(),
         cf.tint[0]*br, cf.tint[1]*br, cf.tint[2]*br,
         3.5+9.0*rnd()*rnd(), 0.028+0.05*rnd()*rnd(), rnd(), 0);
  }
}
```

Wait — disk-star arm membership vs color: `arm` chosen BEFORE th; hot giants only among arm ✓.

Check `emit` alpha param: stars al=1, haze al small ✓.

**Spare fill:**
```js
for(let i=(NSTARS+NHAZE)*2; i<NP; i++){
  const i4=i*4; posArr[i4]=5e4; propArr[i4]=0; propArr[i4+1]=0; propArr[i4+3]=0;
}
```
(defaults zero anyway except pos x; set y,z 0 default ✓ alpha 0 ✓.)

**Galaxy configs:**
```js
const GAL=[
 { c:[-52.5,0,0], v:[1.6,0,-0.56], n:[0.16,-0.94,-0.30], arms:2, k:3.5, ph0:0.35, tint:[1.0,0.84,0.58] },
 { c:[ 52.5,0,0], v:[-1.6,0,0.56], n:[-0.50,-0.58,0.64], arms:3, k:2.9, ph0:1.15, tint:[0.62,0.76,1.05] }
];
```

**Core init:**
```js
const relP=new THREE.Vector3(105,0,0), relV=new THREE.Vector3(-3.2,0,1.12);
```

**stepCores(h):**
```js
function stepCores(h){
  const S2=relP.lengthSq(), S=Math.sqrt(S2);
  const inv=1/Math.pow(S2+CC2,1.5);
  let ax=-MU*relP.x*inv, ay=-MU*relP.y*inv, az=-MU*relP.z*inv;
  const gate=sstep(13,19,simT);
  const dg=0.14*gate*Math.exp(-(S*S)/81) + 2.4*Math.exp(-(S*S)/(2.3*2.3));
  ax-=dg*relV.x; ay-=dg*relV.y; az-=dg*relV.z;
  relV.x+=ax*h; relV.y+=ay*h; relV.z+=az*h;
  relP.x+=relV.x*h; relP.y+=relV.y*h; relP.z+=relV.z*h;
}
```
Note exp(−(S/9)²) = exp(−S²/81) ✓.

**Uniform core update:**
```js
coreA.set(-0.5*relP.x, ...); coreB.set(+0.5*...);
velMat.uniforms.uCoreA.value.copy(coreA) — or direct set on the uniform's vector.
```
I'll store uniform value vectors and set directly:
```js
velMat.uniforms.uCoreA.value.set(-relP.x*0.5,-relP.y*0.5,-relP.z*0.5);
velMat.uniforms.uCoreB.value.set( relP.x*0.5, relP.y*0.5, relP.z*0.5);
```

**Glow update:** glowPos array: [A.xyz]*3 verts? vertices: 0 A-halo,1 B-halo,2 A-nuc,3 B-nuc,4 A-streak,5 B-streak:
```js
const gp=glowGeo.attributes.position.array;
gp[0..2]=coreA; gp[3..5]=coreB; gp[6..8]=coreA; gp[9..11]=coreB; gp[12..14]=coreA; gp[15..17]=coreB;
needsUpdate ✓
```

Glow attributes:
```js
colors: 0: (1.0,0.78,0.52) 1: (0.86,0.84,1.0) 2: (1.0,0.88,0.66) 3: (0.92,0.90,1.0) 4: (0.72,0.82,1.0) 5: (0.78,0.86,1.0)
sizes:  26, 24, 4.6, 4.2, 24, 22
alphas: 0.42, 0.42, 0.9, 0.9, 0.16, 0.16
kinds:  0,0,1,1,2,2
```

**bg build** as sketched.

**Sim RT creation:**
```js
function makeRT(){ return new THREE.WebGLRenderTarget(TEXS,TEXS,{ type: rtType, format:THREE.RGBAFormat, minFilter:THREE.NearestFilter, magFilter:THREE.NearestFilter, wrapS:THREE.ClampToEdgeWrapping, wrapT:THREE.ClampToEdgeWrapping, depthBuffer:false, stencilBuffer:false }); }
const rtType = (renderer.extensions.get('EXT_color_buffer_float')||renderer.capabilities.isWebGL2 && renderer.extensions.get('EXT_color_buffer_half_float')) ? THREE.FloatType : THREE.HalfFloatType;
```
Hmm — logic: prefer Float; if EXT_color_buffer_float missing try Half (needs EXT_color_buffer_half_float; if that's missing too we're doomed but proceed). Simplify:
```js
const hasF = !!renderer.extensions.get('EXT_color_buffer_float');
const rtType = hasF ? THREE.FloatType : THREE.HalfFloatType;
```

**Init DataTextures:**
```js
const posInit=new THREE.DataTexture(posArr,TEXS,TEXS,THREE.RGBAFormat,THREE.FloatType);
posInit.minFilter=posInit.magFilter=THREE.NearestFilter; posInit.needsUpdate=true;
```
Note: DataTexture with FloatType — upload works in WebGL2 ✓ (if not, half? arrays are Float32; HalfFloat DataTexture needs Uint16 — skip, WebGL2 fine).

**Copy pass:** copyMat uniforms {tSrc}; run for pos & vel.

Then dispose posInit/velInit.

**Points star material creation** with uniforms {uPosTex:{value:null}, uProj:{value:1000}, uTime:{value:0}, uExposure:{value:1.12}}.

**bg material** uniforms {uPR, uTime}.

**glow material** uniforms {uProj}.

**Loop with HUD & passage tracking & DPR adapt.**

**onResize:**
```js
function onResize(){
  const w=innerWidth,h=innerHeight;
  renderer.setPixelRatio(PR);
  renderer.setSize(w,h);
  camera.aspect=w/h; camera.updateProjectionMatrix();
  const db=new THREE.Vector2(); renderer.getDrawingBufferSize(db);
  const proj=db.y/(2*Math.tan(camera.fov*Math.PI/360));
  starsMat.uniforms.uProj.value=proj;
  glowMat.uniforms.uProj.value=proj;
  bgMat.uniforms.uPR.value=PR;
}
```
fov/2 in rad: camera.fov deg → tan(rad/2): Math.tan(fov*π/360) ✓.

**Adaptive quality:**
```js
let ft=16.7, frames=0;
in loop: const raw=(t-lastRaw)*1000?? I track dt real (clamped) — better measure raw: keep rawDt variable.
ft+= (rawDt*1000-ft)*0.04; frames++;
if(frames===240){ ft=16.7 reset? } 
Simpler: every frame if (ft>34 && PR>1.01): PR=Math.max(1,PR-0.25); onResize(); ft=16.7;
```
Check with 34ms threshold (below 30fps) ✓.

**Everything seems planned. Let me now also double check star vertex shader clamp threshold 1.25 vs twinkle: fine.**

**gl_FragColor for stars: vColor*(g*vAlpha) — vColor already includes exposure & dim & tw ✓.**

**One more check — the star vertex shader clamps ps with max BEFORE dim calc: dim=(ps/1.25)² uses unclamped ps ✓ (I compute dim from ps then cl=max(ps,1.25)) ✓ code accordingly.**

**Check: `if(d2>1.0) discard;` — points square edges removed ✓.**

**Now think about whether the FIRST rendered frame might show garbage RT (uninitialized rtP[1] read?)** — first frame: sim substeps run BEFORE first scene render ✓ so points read rtP[1] after write ✓.

But careful: my loop order: compute acc (dt=0 first frame → nSub=max(1, ceil(0/0.03)=1?? ceil(0)=0 → max(1,0)=1 → h=0) → simStep(0) — h=0 writes zeros+0 → pos stays (copy already done into slot0; slot1 gets pos+0*... reads rtP[0] writes rtP[1] with v*0 → same ✓ fine.

Actually nSub=max(1,...) with h=0 → harmless ✓.

**Also: at first frame, set starsMat uPosTex BEFORE render — after substeps it points to rtP[1] ✓.**

**Check uniform sampler assignment each substep — fine.**

**One more: `renderer.autoClear=true` — when rendering simScene into RT: clears RT with clearColor (0x02030a) then quad overwrites everything ✓.**

Hmm — clear ALPHA: clearColor alpha 1 → dst alpha 1; quad writes alpha... sim shaders write w=0/pos w... posFrag writes P.w? I wrote gl_FragColor=vec4(P.xyz+V*dt, P.w)?? Let me write vec4(nx,ny,nz,P.w) with P.w preserved (0) ✓ irrelevant.

**vel shader writes vec4(v,0)** ✓.

**copy shader writes texture as-is ✓.**

Now — **HTML title/meta & lang ✓.**

**Also think about whether I should include OrbitControls for optional interaction:** "Starts automatically, no interaction needed" — scripted camera; adding OrbitControls would FIGHT the scripted motion. Skip controls entirely ✓.

**Potential minor issue: additive blending of 64k points with `transparent:true` → sorted per-object not per-vertex; irrelevant ✓.**

**Check three.js r186 still supports `THREE.CustomBlending` etc. ✓.**

**Also `THREE.AdditiveBlending` alternative — I'll use CustomBlending with explicit factors ✓.**

**Let me also double-check DataTexture constructor signature r186: `new THREE.DataTexture(data, width, height, format, type)` ✓ then `.needsUpdate=true` ✓.**

**RT options key names r186: {minFilter, magFilter, wrapS, wrapT, format, type, depthBuffer, stencilBuffer, generateMipmaps?} — generateMipmaps default false for RT ✓.**

**Check `renderer.extensions.get` returns extension object or null ✓.**

**Also — WebGL2 feature `gl_VertexID` not needed ✓.**

**Write the vertex count: starGeo.setDrawRange? default fine.**

**Potential issue — `position` attribute for Points must be vec3; uvArr length NP*3 ✓.**

**One more consideration on sim texture NP=65536 & the star shader reading `position.xy` — uv values exactly at texel centers ((i+0.5)/256) ✓ Nearest sampling exact ✓ no bleeding.**

**Alright — also the requirement mentions "cinematic scientific visualization" — the HUD + title + vignette + slow-mo deliver that.**

**Let me also handle the edge case where `acc` after cap leaves remainder — I set acc=0 (drop) — could cause slight time dilation under heavy lag — acceptable.**

Actually improve: cap nSub at 6 and h up to 0.05: acc up to 6*0.05=0.3 → at SPEED 3.3 covers 0.09s real... whatever, keep cap 4 & drop.

**Final code writing — also include small comments. Let me now write the entire file end-to-end and review it once more for syntax errors.**

Also — HUD `SEP` label: "SEP" separation; maybe "Δ" symbol? Use "SEP". VEL label "VEL". T label "T".

One more time about Myr: "simulated time in millions of years" — label "+348 MYR" ✓ (MYR = millions of years ✓). I'll write "T +348 MYR". Hmm clearer: "T = 348 MYR"? Use "T + 348 MYR" (elapsed since start).

**Phase text width jitter** — fixed-width font ✓.

**Also consider prefers-reduced-motion?** skip (it's a visualization page).

Let me also make sure **no console errors**: e.g., `THREE.Vector2()` for getDrawingBufferSize requires arg in r186? `getDrawingBufferSize(target)` — target required ✓ provide.

`camera.lookAt(0,0,0)` after position set each frame ✓.

**Check star material blending props:**
```js
transparent:true, depthTest:false, depthWrite:false,
blending:THREE.CustomBlending, blendEquation:THREE.AddEquation, blendSrc:THREE.OneFactor, blendDst:THREE.OneFactor,
```
✓ (blendSrcAlpha default null → uses blendSrc ✓.)

**Now — one deeper look at the ARM appearance at t=0 from the camera: A galaxy inclination ~59°, k=3.5, 2 arms — should read clearly. The disk spans 12 units at distance ~170 → on-screen radius ~12*1159/170 ≈ 82px — the spiral pattern visible ✓ (82px disk with 30k stars → dense).**

Hmm — 82px radius disk is smallish. Camera R=172 initial maybe too far? Half-FOV 25° covers 80 units at 172 → disk 12 = 15% of half-height. Two galaxies + margins — could tighten to R0=150: extent needed ±64 → tan: 64/150=0.43 > tan25=0.466 ok fits (0.43<0.466) vertically when separation vertical-ish... borderline when separation axis aligns vertically at some camera angle: apparent vertical extent = 64*|sin(elev-ish components)|... the separation is in XZ plane; camera elevation 19° → vertical screen extent of x-axis separation ≈ 64*sin(19°)≈21 ✓ small; horizontal extent 64*cos component ≤64 → horizontal half-FOV = tan(25°*aspect... aspect 16:9: horizontal half-angle = atan(tan25°*1.78)=39° → covers 150*0.81=122 ✓ plenty. So R=150 works even worst-case; tails later need ~±60 vertical-ish: elevation grows → in-plane tails project mostly horizontally too ✓. Set R0=158, Rmin=132: R=158−26*sstep(4,26)+6.5 sin. At end 132±6.5 ✓. Disk on-screen radius at 158: 12*1159/158=88px ✓.

Hmm, also small screens (mobile portrait): aspect<1 → horizontal FOV shrinks: half-horizontal = atan(tan25°*aspect): aspect 0.5: 13.2° → covers 158*0.235=37 < 64!! Galaxies cropped horizontally on portrait! Mitigate: scale R by aspect: R_eff = R * clamp(1.6/aspect?? For aspect<1.1: multiply R by (1.25/aspect)^0.8?? Simple: fitR = R * Math.max(1, 1.35/Math.max(0.5,aspect))? At aspect 0.5: ×2.7 → 426 — too far; better: multiply by max(1, 1.15/aspect): aspect .5 → ×2.3 → 363 — galaxies small but visible ✓ acceptable; desktop aspect 1.78 → ×1 ✓ unaffected. Use factor = Math.max(1, 1.15/aspect). Slight compromise, fine.

Also FOV: maybe fov 55 for a bit wider (half 27.5°): tan=0.52 → covers more; keeps sizes similar-ish. I'll set fov 55 and uProj consistent (auto from camera.fov ✓). Then R can be ~150: half-height cover at 150: 78 ✓. Let me finalize fov=55, R(t)=152−24*sstep(4,26,t)+6*sin(0.16t+1.7), aspect fit factor as above.

Recompute px sizes with fov55: uProj=h/(2 tan27.5°)=h/1.041 ≈ 1037 (at 1080). star size 0.5 → at 150: 3.5px ✓ similar.

**Vignette strength 0.5 ✓.**

**Now REALLY write it.**

Actually — one more thing to verify: **the vel shader's `uGrav` is vec4 uniform**: uniforms: uGrav:{value:new THREE.Vector4(GM_B,EB2,GM_H,EH2)} ✓.

**And potential double-check of sstep use in drag gate:** sstep(13,19,simT) ✓.

**Passage tracking must run with the S value AFTER steps (per frame) ✓.**

**HUD update per frame ✓.**

**Let me also double check the twinkle doesn't affect haze (tw=0 ✓) and bulge slight ✓.**

**Write the final answer file.** Structure:

1. `<!DOCTYPE html>` head + CSS.
2. body divs.
3. module script.

Let me write out the module script fully, mentally compiling:

```js
import * as THREE from 'three';

const TAU = Math.PI*2;

/* ---------- deterministic RNG ---------- */
let _s = (0x9e3779b9 ^ 0x85245d1) >>> 0;   // hmm ensure nonzero int32
```
careful: 0x9e3779b9 ^ 0x85245d1 = fine nonzero. xorshift on int32 state: use `let _s = 123456789;` simple. `_s^=_s<<13; _s^=_s>>>17; _s^=_s<<5;` — with JS these produce signed ints but consistent; output `(_s>>>0)/4294967296` ✓.

I'll write:
```js
let _s = 987654321;
const rnd = () => { _s ^= _s<<13; _s ^= _s>>>17; _s ^= _s<<5; return ((_s>>>0)%1000000000)/1000000000; };
```
Hmm (_s>>>0)/4294967296 direct is fine.

gauss as above.

```js
const clamp=(x,a,b)=>x<a?a:(x>b?b:x);
const sstep=(a,b,x)=>{const t=clamp((x-a)/(b-a),0,1);return t*t*(3-2*t);};
```

```js
// ===== simulation constants =====
const TEXS=256, NP=TEXS*TEXS;
const NSTARS=30000, NHAZE=2200;
const GM_B=60, EB2=1.5*1.5, GM_H=340, EH2=10.0*10.0;
const MU=800, CC2=4.0;
const RDISK=12;
const SPEED=3.3, MYR_PER_TU=5, KPC_PER_U=1.25, KMS_PER_V=48;
const CD=0.14, LAM2=81, NEAR_K=2.4, NEAR2=2.3*2.3;
```

vCirc ✓.

Arrays & addGalaxy ✓ as drafted.

```js
// ===== renderer / scene =====
const renderer=new THREE.WebGLRenderer({antialias:false,powerPreference:'high-performance'});
renderer.setClearColor(new THREE.Color(0x02030a),1);
renderer.autoClear=true;
document.body.appendChild(renderer.domElement);
const scene=new THREE.Scene();
const camera=new THREE.PerspectiveCamera(55,1,0.5,9000);
```

RTs, sim scene, materials, copy init ✓.

Star points, bg, glow ✓.

Loop ✓.

Resize ✓.

Adaptive PR ✓.

Title fade ✓.

Let me also compute the initial HUD values string placeholders — will be overwritten first frame ✓.

Now, writing the **star vertex shader** — one more consideration: `attribute vec4 aProp` etc. — three auto-prepends attribute declarations ONLY for built-ins (position, normal, uv, color if defined)... For custom attributes I must declare them in the shader: `attribute vec3 aColor; attribute vec4 aProp;` ✓ (allowed in GLSL1 ShaderMaterial). Yes — custom attributes must be declared manually ✓ I do.

Glow shader declares aColor,aSize,aAlpha,aKind ✓.

bg shader declares aSize,aColor,aTw ✓.

**Also for the glow/bg materials: same blending config ✓; bg renderOrder -1? Set bg.renderOrder=0, stars 1, glow 2 ✓.**

**glow geometry: BufferGeometry with 'position' (dynamic), 'aColor','aSize','aAlpha','aKind' ✓ frustumCulled=false ✓.**

**bg geometry: position static + attrs ✓ frustumCulled=false (positions far — would pass anyway).**

Now the **loop** — also update `simClock`... variables:

```js
let lastT=-1, simT=0, acc=0, idx=0, PR=Math.min(window.devicePixelRatio||1,2);
let passages=0, prevS=1e9, descending=false;
let ftAvg=16.7, ftN=0;
```

loop(tms):
```js
const loop=(tms)=>{
  requestAnimationFrame(loop);
  const t=tms*0.001;
  if(lastT<0){ lastT=t; }
  const rawDt=Math.max(0,t-lastT); lastT=t;
  const dt=Math.min(rawDt,0.05);

  // adaptive resolution
  ftAvg+=(rawDt*1000-ftAvg)*0.05;
  if(++ftN>=90){ ftN=0; if(ftAvg>34 && PR>1.01){ PR=Math.max(1,PR-0.25); onResize(); } ftAvg=16.7; }

  // physics substeps
  const S0=relP.length(), V0=relV.length();
  const gate=Math.min(1,Math.max(0,(V0-5)/3.5));
  const slow=1-0.62*Math.exp(-((S0-9.5)*(S0-9.5))/12.25)*gate;
  acc+=dt*SPEED*slow;
  const n=Math.max(1,Math.min(4,Math.ceil(acc/0.03)));
  const h=acc/n; acc=0;
  for(let k=0;k<n;k++){
    stepCores(h);
    velMat.uniforms.uCoreA.value.set(-relP.x*0.5,-relP.y*0.5,-relP.z*0.5);
    velMat.uniforms.uCoreB.value.set( relP.x*0.5, relP.y*0.5, relP.z*0.5);
    simStep(h);
    simT+=h;
  }
```
Hmm — velMat uniforms should be set INSIDE simStep? simStep sets samplers & dt; core uniforms set once per frame before substeps BUT they change per substep... set per substep as above ✓ (before each simStep) ✓ order fine.

```js
  // passages
  const S=relP.length();
  if(S<prevS) descending=true;
  else if(descending){ if(prevS<17.5) passages++; descending=false; }
  prevS=S;

  // camera
  const aspect=camera.aspect;
  const fit=Math.max(1,1.15/aspect);
  const ang=1.12+0.045*t;
  const el=0.34+0.17*sstep(4,26,t)+0.02*Math.sin(t*0.23);
  const R=(152-24*sstep(4,26,t)+6*Math.sin(t*0.16+1.7))*fit;
  camera.position.set(R*Math.cos(el)*Math.cos(ang), R*Math.sin(el), R*Math.cos(el)*Math.sin(ang));
  camera.lookAt(0,0,0);

  // glow follow
  const gp=glowGeo.attributes.position.array;
  const Ax=-relP.x*0.5, Ay=-relP.y*0.5, Az=-relP.z*0.5, Bx=-Ax, By=-Ay, Bz=-Az;
  gp.set([Ax,Ay,Az, Bx,By,Bz, Ax,Ay,Az, Bx,By,Bz, Ax,Ay,Az, Bx,By,Bz],0);
  glowGeo.attributes.position.needsUpdate=true;

  // uniforms time
  starsMat.uniforms.uTime.value=t;
  bgMat.uniforms.uTime.value=t;

  // HUD
  const myr=simT*MYR_PER_TU;
  hT.textContent='+'+String(Math.floor(myr)).padStart(3,'0')+' MYR';
  hS.textContent=(S*KPC_PER_U).toFixed(1)+' KPC';
  hV.textContent=Math.round(relV.length()*KMS_PER_V)+' KM/S';
  hP.textContent=phaseName(S);

  if(t>10) titleEl.classList.add('gone');

  renderer.render(scene,camera);
};
requestAnimationFrame(loop);
```

Wait — `gp.set([...],0)` allocates array per frame — fine (tiny) or write manually. Fine.

**phaseName:**
```js
function phaseName(S){
  if(simT>64 && S<4) return 'MERGER REMNANT';
  if(passages===0) return S<34?'FINAL APPROACH':'FIRST APPROACH';
  if(S<4.2) return 'COALESCENCE';
  if(S<13){
    if(passages===1) return 'FIRST PASSAGE · BRIDGE';
    if(passages===2) return 'SECOND PASSAGE';
    return 'FINAL PASSAGES';
  }
  if(passages===1) return 'TIDAL TAILS EJECTING';
  if(passages===2) return 'TAILS EXPANDING';
  return 'RAPID INSPIRAL';
}
```

**simStep:**
```js
function simStep(h){
  velMat.uniforms.tPos.value=rtP[idx].texture;
  velMat.uniforms.tVel.value=rtV[idx].texture;
  velMat.uniforms.dt.value=h;
  quad.material=velMat;
  renderer.setRenderTarget(rtV[1-idx]);
  renderer.render(simScene,simCam);

  posMat.uniforms.tPos.value=rtP[idx].texture;
  posMat.uniforms.tVel.value=rtV[1-idx].texture;
  posMat.uniforms.dt.value=h;
  quad.material=posMat;
  renderer.setRenderTarget(rtP[1-idx]);
  renderer.render(simScene,simCam);
  renderer.setRenderTarget(null);
  idx=1-idx;
  starsMat.uniforms.uPosTex.value=rtP[idx].texture;
}
```

**Init copy:**
```js
quad.material=copyMat;
copyMat.uniforms.tSrc.value=posInit;
renderer.setRenderTarget(rtP[0]); renderer.render(simScene,simCam);
copyMat.uniforms.tSrc.value=velInit;
renderer.setRenderTarget(rtV[0]); renderer.render(simScene,simCam);
renderer.setRenderTarget(null);
posInit.dispose(); velInit.dispose();
```

Hmm — DataTexture variable names posInitTex — fine.

**Now — one more subtle three.js thing: reusing the same `quad.material` across materials — assignment ok ✓.**

**Check simScene creation:**
```js
const simScene=new THREE.Scene();
const simCam=new THREE.OrthographicCamera(-1,1,1,-1,0,1);
const quad=new THREE.Mesh(new THREE.PlaneGeometry(2,2), null);
quad.frustumCulled=false;
simScene.add(quad);
```
Mesh with material null initially — render only after set ✓ (copy pass sets before first render ✓).

**Now the shaders as template strings.** Also — star vertex: uses `uv`? no. OK.

Double check **`texture2D(uPosTex, position.xy)`** — position.xy in [0,1] ✓.

**Check glow fragment kind branching with varying float — use if chain ✓.**

**bg vertex: `gl_PointSize=aSize*uPR;` ✓.**

**One risk: three.js may complain `gl_PointSize` set but material not Points — they are Points ✓.**

**Also `sizeAttenuation` irrelevant for ShaderMaterial ✓.**

**Final check — CSS ids referenced: hT,hS,hV,hP,title(el id 'title'), cap. Get refs after DOM (script at end ✓).**

**Also `#title.gone` class add ✓.**

**Prevent context menu / selection? fine.**

**Check: `renderer.domElement` inserted before overlays? Overlays are position:fixed divs already in DOM before canvas append → canvas appended AFTER them in DOM order but positioned fixed → stacking: later DOM = on top. Canvas would cover HUD! Fix: canvas z-index: use CSS `canvas{z-index:0}` and overlays z-index 2? Set explicit: canvas{position:fixed;inset:0;z-index:0} #vig{z-index:1} #hud,#title,#cap{z-index:2}. ✓**

**Now, double check star geometry attribute names don't collide with built-ins (aColor, aProp ok).**

**One more potential correctness trap — `renderer.extensions.get('EXT_color_buffer_float')` may return null but also log warning — fine.**

**HalfFloat fallback with Float32Array DataTexture init: copy shader reads Float texture (fine) writes to half RT (values within half range ✓ positions ≤ 5e4 — half max 65504 ✓ spare at 5e4 ok! velocities small ✓. But half precision for spares irrelevant.)**

Edge: 5e4 < 65504 ✓ lucky. If positions ever exceeded 65504 → inf — spares capped ✓ real stars stay < few hundred ✓.

**Also — `renderer.setClearColor` with color + alpha 1 ✓.**

**Camera far 9000 > bg 2500 ✓.**

**Check camera near 0.5 — glow sprites near camera? never closer than ~100 ✓.**

I think the design is complete. Now — also let me reconsider **N_HAZE=2200 per galaxy → total particles used = 2*(30000+2200)=64400; spares=1136 ✓.**

**One more improvement — "at least 20,000 stars per galaxy rendered as glowing points" — 30k ✓ plus haze 2200 also glowing points ✓.**

**Requirement "colours going from warm yellow cores to blue-white arms" — ✓ implemented (radial ramp + population split).**

Let me also double-check the **arm theta formula sign vs spin** once more, because if arms LEAD, it looks subtly off to experts but fine to everyone; trailing chosen: θ = ph0 + m*π − k*ln r; rotation CCW (dθ/dt>0) in local frame. Arm tangent direction: dθ/dr = −k/r < 0. Rotation sweeps material CCW; a trailing arm has its outer end rotated BACK (clockwise) relative to inner end ✓ that's what −k ln r gives ✓.

**Also verify spin sign in world for A: local tangential (−st, ct, 0) with s=+1 → L_local=+z → world L=+n_A = (0.16,−0.94,−0.30) → dominant −y ✓ prograde with orbital L=(0,−...,0) ✓.**

**Now, one more think about bulge streaming direction: tx=ny*dz−nz*dy etc = cross(n, d)?? cross(n,d) = (n_y d_z − n_z d_y, n_z d_x − n_x d_z, n_x d_y − n_y d_x) ✓ matches — direction of rotation consistent with +n ✓ same handedness as disk ✓ good (bulge co-rotates).**

**Velocity magnitudes for bulge: sp=vc*(0.28+0.55) + tangential 0.55vc — total up to ~1.4vc ≈ 4.6 at r=1 — escape at r=1: 2*(60/√3.25 + 340/√101)=2*(33.3+33.8)=134 → 11.6 ✓ bound.**

**Also — check that disk stars' vc uses r possibly up to 13.5 (haze) ✓ vCirc handles.**

**Potential issue: stars at r<0.8 forced 0.8+ — inner disk blends with bulge ✓.**

Alright — also **let me pre-verify the initial relative orbit numerically one more time for sanity with a quick mental Euler integration?** Trust analytic estimates ✓ (pericenter ~9.4 at ~18 t.u.).

Hmm, actually one worry: the SOFTENED mutual force with εcc=2 reduces the effective attraction at r<~4, which slightly raises rp over sequential passes?? No — softening only matters when rp<~4; rp stays ~9.4 until circular decay — decay to r~4 then near-drag & softening make final plunge gentle ✓.

**Also — the stars feel bulge+halo of BOTH cores; at merger the combined center-of-mass potential is fine ✓.**

**Let me also confirm the tail stars don't get lost to infinity en masse (visual):** ejecta Δv ~4–6 vs v_esc(10)≈7.7 → marginal → many remain bound on elongated orbits → tails arc back ✓ some escape ✓ realistic Antennae look.

**Check per-frame JS allocations:** small ✓.

**Now — the final HTML. Also add `<noscript>`? skip.**

Let me write the complete file now, carefully, keeping GLSL strings clean.

Additional check on the star vertex shader: I reference `fract(aProp.z)` where aProp.z=ph random 0..1 — freq 0.55+0..1.7 ✓.

Also — `uExposure` multiply: vColor=aColor*(uExposure*dim*tw) ✓.

And in fragment: `vec4(vColor*(g*vAlpha),1.0)` ✓.

Wait — for the stars I folded brightness into aColor at build (col*br) — those values can reach ~2.4 for giants ✓ fine.

**Glow nucleus alpha 0.9 & profile peak exp(0)=1 → contribution ~0.9*color(≈1,0.88,0.66) ≈ 0.9 — plus halo — core region total (with thousands of bulge stars) saturates ✓.**

**Let me reconsider halo size 26 world: halo profile exp(-d2*3)*0.55+0.4*exp(-d2*0.9): at d2=0.5 (r=0.707 of radius=13 world): 0.55*e^-1.5=0.123+0.4*e^-0.45=0.256 → 0.38×0.42=0.16 — broad soft halo ✓ nice.**

**Streak: size 24 → 24 world ≈ 250px?? px=24*1037/150=166 → streak length ~±0.75*166=125px each side ✓ subtle at alpha 0.16.**

Hmm — streak might intersect HUD? It's in-scene — fine.

**Now — write bg star colors with slight blue/warm ✓; also add ~40 "distant galaxies" tiny elongated?? skip.**

**Final sanity on drag gate start 13→19:** if pass1 actually occurs ~18, gate reaches 1.0 at 19 — drag slightly ramps during final approach ✓ intended.

**One more potential failure mode: what if my timing estimates are off and pass1 happens at simT=25 (7.6s)?** Fine. If at 14 (4.2s)? Fine too. Robust ✓.

**What if drag over-deliberates and cores merge during pass1 (r_a<4)?** c_d=0.14 Δv~1.6 max — no ✓.

**What if drag UNDER-delivers and merger happens at simT>75 (~24s+)?** Still within window; phase labels handle ✓. To hedge, add a slow baseline drag beyond gate: + 0.02*exp(−(S/40)²)*?? adds continuous decay always (after gate): 0.02 at r<20 → dr/dt=−2*0.02*9*0.36≈0.13 — negligible. Skip.

Also hedge the opposite: after simT>55, if S still >12, increase near-drag? Add late-phase extra drag: dg += 0.5*exp(−(S/9)²)*sstep(45,60,simT) — accelerates late merger deterministically ✓ cheap insurance for pacing. Include: after simT 45→60 drag triples gradually → merger guaranteed by ~20s. ✓ Implement:
```js
const late=sstep(45,60,simT)*0.45;
dg=CD*gate*exp(-S2/LAM2) + NEAR_K*exp(-S2/NEAR2) + late*exp(-S2/LAM2);
```
At S=9: late adds 0.45*0.37=0.17 → modest ✓ good.

**OK, write it all.** Also remember: NO importmap in my file (provided externally) — just the module script. The instructions: "An import map is provided for you: do not add your own import map or any CDN URL." ✓.

Let me also compute `uProj` correctly: db.y is drawing-buffer height in pixels ✓ gl_PointSize expects device px ✓.

**Writing the final code now — with attention to every bracket.** I'll compose it fully then re-scan for syntax.

Also: define DOM refs:
```js
const hT=document.getElementById('hT'), ... const titleEl=document.getElementById('title');
```

Also the initial onResize() call before loop ✓ and after renderer creation.

Potential ordering bug: onResize references starsMat etc — define after materials ✓.

**Also — `powerPreference` fine.**

**Also for robustness wrap main in try/catch and show error overlay:**
```js
try{ main(); }catch(e){ const d=document.createElement('div'); d.style.cssText='position:fixed;inset:0;display:flex;align-items:center;justify-content:center;color:#9fb4d0;font:12px monospace'; d.textContent='WebGL initialization failed: '+e.message; document.body.appendChild(d); }
```
Wrap everything in main() ✓.

Hmm — but `requestAnimationFrame(loop)` inside main ✓.

Now — **count lines & write**. Also, per instructions, after the code block, include a brief explanation of the implementation.

One more mini-check of the vertex shader for stars: `float dim=ps<1.25?(ps*ps)/1.5625:1.0;` (1.25²=1.5625) ✓.

And gl_PointSize=cl where cl=max(ps,1.25) ✓.

Also should star sizes be multiplied by... haze sizes 3.5–12.5 with alpha 0.028–0.078 — wait: bigger sprites → same alpha spreads over more px → dimmer per px ✓ natural.

**Double-check the disk radial CDF gives enough stars at 8–12 for tails: P(r>8)=1−(8/12)^{1/1.7}: (0.667)^{0.588}=e^{0.588*ln0.667}=e^{−0.2386}=0.788 → 21% ✓; plus haze 13.5*... P(r>8): (8/13.5)^{1/2.3}=(0.593)^{0.435}=e^{−0.227}=0.797 → 20% ✓.**

**Also — I should double check the vc flatness once more with final constants (GM_B=60, εb=1.5; GM_H=340, εh=10):**
r=1: 60/(3.25^1.5=5.86)=10.24; 340*1/(101^1.5=1015)=0.335 → v²=10.57?? wait v²=ΣGM r²/(r²+ε²)^1.5: r=1: bulge 60*1/5.86=10.24; halo 340*1/1015=0.335; v=√10.58=3.25 ✓
r=2: 60*4/(6.25^1.5=15.6)=15.4; 340*4/(104^1.5=1061)=1.28 → v²=16.7 v=4.08 ✓
r=4: 60*16/(18.25^1.5=77.9)=12.3; 340*16/(116^1.5=1249)=4.36 → v²=16.7 v=4.08 ✓✓
r=6: 9.13+340*36/(136^1.5=1586)=7.72 → 16.85 → 4.10 ✓
r=8: 60*64/(66.25^1.5=539)=7.12; 340*64/(164^1.5=2100)=10.36 → 17.5 → 4.18 ✓
r=10: 60*100/(102.25^1.5=1034)=5.80; 340*100/(200^1.5=2828)=12.0 → 17.8 → 4.22 ✓
r=12: 5.08?? 60*144/(145.25^1.5=1750)=4.93; 340*144/(244^1.5=3812)=12.85 → 17.8 → 4.22 ✓
Superb — flat 4.1±0.15 across the whole disk ✓. Ω: r=2:2.04, r=12:0.35.

**Disk period at r=6: 2π*6/4.1=9.2 t.u.=2.8s ✓ visible rotation.**

**Escape speeds:** r=6: 2*(60/√38.25+340/√136)=2*(9.70+29.2)=77.8→8.8; r=10: 2*(5.92+24.0)=59.9→7.7; ✓.

Impulse Δv~4 vs v_esc 8 → outer half unbound-ish → tails; inner bound → disk survives ✓ balance good.

Now finalize **glow colors** — A core (1.0,0.80,0.55), B (0.88,0.85,1.0); nuclei brighter white-ish: A (1.0,0.92,0.75), B (0.95,0.95,1.0).

**Write bg: NBG=2600.**

Let me also add **a very faint blue ambient fog?** no.

Also **the caption** bottom-right: "RESTRICTED THREE-BODY GRAVITY · 65 536 PARTICLES · GPU-INTEGRATED". ✓

**Title**: h1 "GALACTIC COLLISION", p "TWO SPIRAL GALAXIES · TIDAL DISRUPTION SIMULATION". ✓

Now — one FINAL think about a subtle rendering artifact: additive points + `transparent:true` + no depth — big haze sprites rendered after stars could... additive is order-independent ✓ no artifact.

**Also — stars behind the core glow: all additive ✓.**

**Performance of fragment `discard` on big sprites: fine.**

**Now write everything. During writing, maintain variable name consistency:**

- posArr, velArr, colArr, propArr
- uvArr
- rtP=[rt0,rt1], rtV=[...]
- velMat, posMat, copyMat
- simScene, simCam, quad
- starsGeo, starsMat, starsPts
- bgGeo, bgMat, bgPts
- glowGeo, glowMat, glowPts
- relP, relV
- coreApos? not needed; compute inline.

Also — **star shader uniform `uProj` shared with glowMat's own uProj ✓ separate materials, separate uniforms ✓.**

Let me also double check **`renderer.getDrawingBufferSize(vec2)`** name — yes `getDrawingBufferSize( target )` ✓.

**Also — after `renderer.setPixelRatio(PR)` in adaptive step, must call onResize to update uProj ✓ (onResize does both) ✓.**

Write the file.

Actually, one more improvement for the **"cinematic"** feel: **letterbox bars?** Two thin black bars top/bottom (like 2.39:1)? On a full-window canvas, subtle 24px gradient bars could cheapen; skip — vignette suffices.

Also **maybe a soft "scanline" grain?** skip.

FINAL check on requirement "Use the requestAnimationFrame timestamp for animation time" — I use `tms` for camera, twinkle, dt ✓ (clock unused) ✓.

"Full-window canvas that handles resizing" ✓.

Now writing out. I'll also add concise comments. Watch template literal escaping — no backticks inside GLSL.

Also — units label check: SEP initial 131.3 KPC — hmm realistic galaxy pair separations before encounter ~50–150 kpc ✓ nice.

VEL initial: |v_rel|=sqrt(3.2²+1.12²)=sqrt(10.24+1.2544)=3.3918 → ×48=163 ✓.

Let me now also decide **`MYR_PER_TU=5`**: 30s→~99 t.u.→~495 Myr ✓; final label ~500+ ✓.

Writing the code:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Galactic Collision — Tidal Disruption</title>
<style>
  html,body{height:100%}
  body{margin:0;background:#020409;overflow:hidden;
       font-family:ui-monospace,"SF Mono","Cascadia Code",Menlo,Consolas,"Liberation Mono",monospace;
       -webkit-font-smoothing:antialiased}
  canvas{position:fixed;inset:0;display:block;z-index:0}
  #vig{position:fixed;inset:0;z-index:1;pointer-events:none;
       background:radial-gradient(130% 100% at 50% 45%, rgba(0,0,0,0) 55%, rgba(1,2,7,.55) 100%)}
  #hud{position:fixed;top:22px;left:24px;z-index:2;pointer-events:none;user-select:none;
       border-left:1px solid rgba(150,180,215,.28);padding-left:12px;
       color:#dfe9f5;font-size:10px;letter-spacing:.16em;line-height:1.95}
  #hud .lab{display:inline-block;min-width:3.4em;color:rgba(148,175,205,.55)}
  #hud .ph{margin-top:7px;color:#8fc6e4;letter-spacing:.24em}
  #title{position:fixed;left:24px;bottom:26px;z-index:2;pointer-events:none;user-select:none;
         transition:opacity 2.4s ease,transform 2.4s ease}
  #title h1{margin:0 0 7px;font-size:13px;font-weight:500;letter-spacing:.5em;color:#e8eff8}
  #title p{margin:0;font-size:10px;letter-spacing:.2em;color:rgba(148,175,205,.55)}
  #title.gone{opacity:0;transform:translateY(8px)}
  #cap{position:fixed;right:24px;bottom:28px;z-index:2;pointer-events:none;user-select:none;
       text-align:right;font-size:9px;letter-spacing:.24em;color:rgba(140,168,198,.38)}
  @media(max-width:640px){#cap{display:none}}
</style>
</head>
<body>
<div id="vig"></div>
<div id="hud">
  <div><span class="lab">T</span><span id="hT">+000 MYR</span></div>
  <div><span class="lab">SEP</span><span id="hS">131.3 KPC</span></div>
  <div><span class="lab">VEL</span><span id="hV">163 KM/S</span></div>
  <div class="ph" id="hP">FIRST APPROACH</div>
</div>
<div id="title"><h1>GALACTIC COLLISION</h1><p>TWO SPIRAL GALAXIES · TIDAL DISRUPTION SIMULATION</p></div>
<div id="cap">RESTRICTED THREE-BODY · 65 536 PARTICLES · GPU-INTEGRATED GRAVITY</div>
<script type="module">
import * as THREE from 'three';
... (all code)
</script>
</body>
</html>
```

Module code (full):

```js
const TAU=Math.PI*2;
const clamp=(x,a,b)=>x<a?a:(x>b?b:x);
const sstep=(a,b,x)=>{const t=clamp((x-a)/(b-a),0,1);return t*t*(3-2*t);};

/* deterministic RNG so the piece always renders the same way */
let _s=987654321;
const rnd=()=>{ _s^=_s<<13; _s^=_s>>>17; _s^=_s<<5; return (_s>>>0)/4294967296; };
let _g=null;
const gauss=()=>{ if(_g!==null){const v=_g;_g=null;return v;}
  const u=Math.max(rnd(),1e-12), v=rnd(), m=Math.sqrt(-2*Math.log(u));
  _g=m*Math.sin(TAU*v); return m*Math.cos(TAU*v); };

/* ===== physics constants (sim units; 1 u ≈ 1.25 kpc, 1 v ≈ 48 km/s, 1 t ≈ 5 Myr) ===== */
const TEXS=256, NP=TEXS*TEXS;
const NSTARS=30000, NHAZE=2200;
const GM_B=60,  EB2=1.5*1.5;
const GM_H=340, EH2=10.0*10.0;
const MU=800, CC2=4.0;
const RDISK=12;
const SPEED=3.3, MYR_PER_TU=5, KPC_PER_U=1.25, KMS_PER_V=48;
const CD=0.14, LAM2=81, NEAR_K=2.4, NEAR2=2.3*2.3;

const vCirc=r=>{ const r2=r*r;
  return Math.sqrt(GM_B*r2/Math.pow(r2+EB2,1.5)+GM_H*r2/Math.pow(r2+EH2,1.5)); };

/* ===== particle buffers ===== */
const posArr=new Float32Array(NP*4), velArr=new Float32Array(NP*4),
      colArr=new Float32Array(NP*3), propArr=new Float32Array(NP*4);

function addGalaxy(gi,cf){
  const n=new THREE.Vector3(cf.n[0],cf.n[1],cf.n[2]).normalize();
  const h=Math.abs(n.y)<0.92?new THREE.Vector3(0,1,0):new THREE.Vector3(1,0,0);
  const e1=new THREE.Vector3().crossVectors(h,n).normalize();
  const e2=new THREE.Vector3().crossVectors(n,e1).normalize();
  const [cx,cy,cz]=cf.c,[vx,vy,vz]=cf.v;
  const A1x=e1.x,A1y=e1.y,A1z=e1.z,A2x=e2.x,A2y=e2.y,A2z=e2.z,Nx=n.x,Ny=n.y,Nz=n.z;
  let idx=gi*(NSTARS+NHAZE);
  const emit=(lx,ly,lz,ux,uy,uz,r,g,b,size,al,ph,tw)=>{
    const i4=idx*4,i3=idx*3;
    posArr[i4]=cx+A1x*lx+A2x*ly+Nx*lz; posArr[i4+1]=cy+A1y*lx+A2y*ly+Ny*lz;
    posArr[i4+2]=cz+A1z*lx+A2z*ly+Nz*lz; posArr[i4+3]=0;
    velArr[i4]=vx+A1x*ux+A2x*uy+Nx*uz; velArr[i4+1]=vy+A1y*ux+A2y*uy+Ny*uz;
    velArr[i4+2]=vz+A1z*ux+A2z*uy+Nz*uz; velArr[i4+3]=0;
    colArr[i3]=r; colArr[i3+1]=g; colArr[i3+2]=b;
    propArr[i4]=size; propArr[i4+1]=al; propArr[i4+2]=ph; propArr[i4+3]=tw;
    idx++;
  };
  /* bulge: Plummer sphere, warm, isotropic + net spin */
  const NB=Math.floor(NSTARS*0.24);
  for(let i=0;i<NB;i++){
    const X=Math.max(rnd(),1e-6);
    let r=1.5/Math.sqrt(Math.pow(X,-2/3)-1); if(r>4.6)r=0.5+4.1*rnd();
    const u2=rnd()*2-1, ph=rnd()*TAU, s1=Math.sqrt(Math.max(0,1-u2*u2));
    const dx=Math.cos(ph)*s1, dy=Math.sin(ph)*s1, dz=u2;
    const vc=vCirc(r), sp=vc*(0.28+0.55*rnd());
    let tx=Ny*dz-Nz*dy, ty=Nz*dx-Nx*dz, tz=Nx*dy-Ny*dx;
    const tl=Math.hypot(tx,ty,tz)||1, f=vc*0.55/tl, br=0.5+0.75*rnd();
    emit(r*dx,r*dy,r*dz, dx*sp+tx*f, dy*sp+ty*f, dz*sp+tz*f,
         br,(0.70+0.18*rnd())*br,(0.40+0.22*rnd())*br,
         0.28+0.34*rnd()*rnd(), 1, rnd(), 0.3+0.3*rnd());
  }
  /* disk: exponential-ish, logarithmic spiral arms, warm centre → blue-white rim */
  for(let i=NB;i<NSTARS;i++){
    let r=RDISK*Math.pow(rnd(),1.7); if(r<0.8)r=0.8+0.5*rnd();
    r*=1+0.05*gauss();
    const arm=rnd()<0.60; let th;
    if(arm){ const m=Math.floor(rnd()*cf.arms);
      let sig=0.13+0.012*r; if(rnd()<0.10)sig*=2.4;
      th=cf.ph0+m*TAU/cf.arms-cf.k*Math.log(Math.max(r,1.1))+gauss()*sig;
    } else th=rnd()*TAU;
    const z=gauss()*(0.13+0.030*r)*(arm?0.8:1);
    const ct=Math.cos(th), st=Math.sin(th);
    const vc=vCirc(r)*(1+0.03*gauss());
    const vr=0.05*vc*gauss(), vv=0.04*vc*gauss();
    const t=clamp((r-1.2)/10,0,1);
    let cr=1.0-0.42*t, cg=0.86-0.14*t, cb=0.58+0.47*t, br, size;
    if(arm&&rnd()<0.085){ cr=0.60;cg=0.72;cb=1.12; br=1.35+0.5*rnd(); size=0.85+0.55*rnd(); }
    else if(arm){ cr+=0.04;cg+=0.05;cb=Math.min(1.15,cb+0.10); br=0.50+0.70*rnd(); size=0.34+0.42*Math.pow(rnd(),1.5); }
    else { cr=Math.min(1.05,cr+0.07);cg+=0.02;cb=Math.max(0.34,cb-0.08); br=0.34+0.50*rnd(); size=0.32+0.38*Math.pow(rnd(),1.5); }
    emit(r*ct,r*st,z, -st*vc+ct*vr, ct*vc+st*vr, vv,
         Math.min(1.2,cr)*br, Math.min(1.2,cg)*br, Math.min(1.25,cb)*br,
         size, 1, rnd(), 0.25+0.55*rnd());
  }
  /* diffuse starlight haze (co-rotating, arms included → luminous arms & bridges) */
  for(let i=0;i<NHAZE;i++){
    let r=13.5*Math.pow(rnd(),2.3); if(r<0.7)r=0.7+0.5*rnd();
    let th;
    if(rnd()<0.45){ const m=Math.floor(rnd()*cf.arms);
      th=cf.ph0+m*TAU/cf.arms-cf.k*Math.log(Math.max(r,1.1))+gauss()*(0.25+0.02*r);
    } else th=rnd()*TAU;
    const z=gauss()*(0.45+0.05*r), ct=Math.cos(th), st=Math.sin(th);
    const vc=vCirc(r)*(1+0.04*gauss()), br=0.7+0.5*rnd();
    emit(r*ct,r*st,z, -st*vc, ct*vc, 0.03*gauss(),
         cf.tint[0]*br, cf.tint[1]*br, cf.tint[2]*br,
         3.5+9.0*rnd()*rnd(), 0.028+0.05*rnd()*rnd(), rnd(), 0);
  }
}

const GAL=[
 {c:[-52.5,0,0], v:[ 1.6,0,-0.56], n:[ 0.16,-0.94,-0.30], arms:2, k:3.5, ph0:0.35, tint:[1.00,0.84,0.58]},
 {c:[ 52.5,0,0], v:[-1.6,0, 0.56], n:[-0.50,-0.58, 0.64], arms:3, k:2.9, ph0:1.15, tint:[0.62,0.76,1.05]}
];
addGalaxy(0,GAL[0]); addGalaxy(1,GAL[1]);
for(let i=2*(NSTARS+NHAZE);i<NP;i++){ posArr[i*4]=5e4; } /* spare slots stay invisible */
```

Then renderer & rest.

**Wait — `addGalaxy` references THREE before renderer creation — fine (imported).**

Renderer & scenes:

```js
const renderer=new THREE.WebGLRenderer({antialias:false,powerPreference:'high-performance'});
renderer.setClearColor(new THREE.Color(0x02030a),1);
document.body.appendChild(renderer.domElement);
const scene=new THREE.Scene();
const camera=new THREE.PerspectiveCamera(55,1,0.5,9000);

/* ===== GPU state (ping-pong float buffers) ===== */
const hasFloat=!!renderer.extensions.get('EXT_color_buffer_float');
const RTT=hasFloat?THREE.FloatType:THREE.HalfFloatType;
const mkRT=()=>new THREE.WebGLRenderTarget(TEXS,TEXS,{type:RTT,format:THREE.RGBAFormat,
  minFilter:THREE.NearestFilter,magFilter:THREE.NearestFilter,
  wrapS:THREE.ClampToEdgeWrapping,wrapT:THREE.ClampToEdgeWrapping,
  depthBuffer:false,stencilBuffer:false});
const rtP=[mkRT(),mkRT()], rtV=[mkRT(),mkRT()];

const simScene=new THREE.Scene();
const simCam=new THREE.OrthographicCamera(-1,1,1,-1,0,1);
const quad=new THREE.Mesh(new THREE.PlaneGeometry(2,2));
quad.frustumCulled=false; simScene.add(quad);

const SIM_VERT=`
varying vec2 vUv;
void main(){ vUv=uv; gl_Position=vec4(position.xy,0.0,1.0); }`;

const copyMat=new THREE.ShaderMaterial({
  uniforms:{tSrc:{value:null}},
  vertexShader:SIM_VERT,
  fragmentShader:`uniform sampler2D tSrc; varying vec2 vUv;
    void main(){ gl_FragColor=texture2D(tSrc,vUv); }`,
  depthTest:false, depthWrite:false });

const velMat=new THREE.ShaderMaterial({
  uniforms:{ tPos:{value:null}, tVel:{value:null},
    uCoreA:{value:new THREE.Vector3()}, uCoreB:{value:new THREE.Vector3()},
    uGrav:{value:new THREE.Vector4(GM_B,EB2,GM_H,EH2)}, dt:{value:0} },
  vertexShader:SIM_VERT,
  fragmentShader:`
    uniform sampler2D tPos,tVel;
    uniform vec3 uCoreA,uCoreB;
    uniform vec4 uGrav;
    uniform float dt;
    varying vec2 vUv;
    void main(){
      vec3 p=texture2D(tPos,vUv).xyz;
      vec3 v=texture2D(tVel,vUv).xyz;
      vec3 dA=uCoreA-p; float qA=dot(dA,dA);
      vec3 dB=uCoreB-p; float qB=dot(dB,dB);
      float ab=inversesqrt(qA+uGrav.y), ah=inversesqrt(qA+uGrav.w);
      float bb=inversesqrt(qB+uGrav.y), bh=inversesqrt(qB+uGrav.w);
      vec3 a=dA*(uGrav.x*ab*ab*ab+uGrav.z*ah*ah*ah)
            +dB*(uGrav.x*bb*bb*bb+uGrav.z*bh*bh*bh);
      v+=a*dt;
      float s2=dot(v,v);
      if(s2>4900.0) v*=70.0/sqrt(s2);
      gl_FragColor=vec4(v,0.0);
    }`,
  depthTest:false, depthWrite:false });

const posMat=new THREE.ShaderMaterial({
  uniforms:{tPos:{value:null},tVel:{value:null},dt:{value:0}},
  vertexShader:SIM_VERT,
  fragmentShader:`
    uniform sampler2D tPos,tVel;
    uniform float dt;
    varying vec2 vUv;
    void main(){
      vec4 P=texture2D(tPos,vUv);
      vec3 V=texture2D(tVel,vUv).xyz;
      gl_FragColor=vec4(P.xyz+V*dt,P.w);
    }`,
  depthTest:false, depthWrite:false });
```

Init textures & copy:

```js
const posInit=new THREE.DataTexture(posArr,TEXS,TEXS,THREE.RGBAFormat,THREE.FloatType);
const velInit=new THREE.DataTexture(velArr,TEXS,TEXS,THREE.RGBAFormat,THREE.FloatType);
for(const t of [posInit,velInit]){ t.minFilter=t.magFilter=THREE.NearestFilter; t.needsUpdate=true; }
quad.material=copyMat;
copyMat.uniforms.tSrc.value=posInit;
renderer.setRenderTarget(rtP[0]); renderer.render(simScene,simCam);
copyMat.uniforms.tSrc.value=velInit;
renderer.setRenderTarget(rtV[0]); renderer.render(simScene,simCam);
renderer.setRenderTarget(null);
posInit.dispose(); velInit.dispose();
```

Star points:

```js
const uvArr=new Float32Array(NP*3);
for(let i=0;i<NP;i++){
  uvArr[i*3]=((i%TEXS)+0.5)/TEXS;
  uvArr[i*3+1]=(Math.floor(i/TEXS)+0.5)/TEXS;
  uvArr[i*3+2]=0;
}
const starsGeo=new THREE.BufferGeometry();
starsGeo.setAttribute('position',new THREE.BufferAttribute(uvArr,3));
starsGeo.setAttribute('aColor',new THREE.BufferAttribute(colArr,3));
starsGeo.setAttribute('aProp',new THREE.BufferAttribute(propArr,4));

const starsMat=new THREE.ShaderMaterial({
  uniforms:{ uPosTex:{value:rtP[0].texture}, uProj:{value:1000},
             uTime:{value:0}, uExposure:{value:1.12} },
  vertexShader:`
    uniform sampler2D uPosTex;
    uniform float uProj,uTime,uExposure;
    attribute vec3 aColor;
    attribute vec4 aProp;
    varying vec3 vColor;
    varying float vAlpha;
    void main(){
      vec4 P=texture2D(uPosTex,position.xy);
      vec4 mv=modelViewMatrix*vec4(P.xyz,1.0);
      float ps=aProp.x*uProj/max(0.1,-mv.z);
      float dim=ps<1.25?(ps*ps)/1.5625:1.0;
      float tw=1.0-aProp.w*(0.5+0.5*sin(uTime*(0.55+fract(aProp.z)*1.7)+aProp.z*63.0));
      gl_PointSize=max(ps,1.25);
      gl_Position=projectionMatrix*mv;
      vColor=aColor*(uExposure*dim*tw);
      vAlpha=aProp.y;
    }`,
  fragmentShader:`
    varying vec3 vColor;
    varying float vAlpha;
    void main(){
      vec2 q=gl_PointCoord*2.0-1.0;
      float d2=dot(q,q);
      if(d2>1.0) discard;
      float g=(exp(-d2*3.4)+0.16*exp(-d2*1.2))*(1.0-smoothstep(0.72,1.0,d2));
      gl_FragColor=vec4(vColor*(g*vAlpha),1.0);
    }`,
  transparent:true, depthTest:false, depthWrite:false,
  blending:THREE.CustomBlending, blendEquation:THREE.AddEquation,
  blendSrc:THREE.OneFactor, blendDst:THREE.OneFactor });

const starsPts=new THREE.Points(starsGeo,starsMat);
starsPts.frustumCulled=false; starsPts.renderOrder=1;
scene.add(starsPts);
```

Hmm — one thing: posArr's w=0 — gl_FragColor alpha... fine.

Core glow:

```js
const glowGeo=new THREE.BufferGeometry();
glowGeo.setAttribute('position',new THREE.BufferAttribute(new Float32Array(18),3));
glowGeo.setAttribute('aColor',new THREE.BufferAttribute(new Float32Array([
  1.00,0.78,0.52,  0.88,0.85,1.00,  1.00,0.92,0.75,  0.95,0.95,1.00,  0.72,0.82,1.00,  0.78,0.86,1.00]),3));
glowGeo.setAttribute('aSize',new THREE.BufferAttribute(new Float32Array([26,24,4.6,4.2,24,22]),1));
glowGeo.setAttribute('aAlpha',new THREE.BufferAttribute(new Float32Array([0.42,0.42,0.9,0.9,0.16,0.16]),1));
glowGeo.setAttribute('aKind',new THREE.BufferAttribute(new Float32Array([0,0,1,1,2,2]),1));
const glowMat=new THREE.ShaderMaterial({
  uniforms:{uProj:{value:1000}},
  vertexShader:`
    uniform float uProj;
    attribute vec3 aColor;
    attribute float aSize,aAlpha,aKind;
    varying vec3 vColor;
    varying float vKind;
    void main(){
      vec4 mv=modelViewMatrix*vec4(position,1.0);
      gl_PointSize=aSize*uProj/max(0.1,-mv.z);
      gl_Position=projectionMatrix*mv;
      vColor=aColor*aAlpha; vKind=aKind;
    }`,
  fragmentShader:`
    varying vec3 vColor;
    varying float vKind;
    void main(){
      vec2 q=gl_PointCoord*2.0-1.0;
      float d2=dot(q,q);
      if(d2>1.0) discard;
      float g;
      if(vKind<0.5)      g=0.55*exp(-d2*3.0)+0.40*exp(-d2*0.9);
      else if(vKind<1.5) g=exp(-d2*4.0);
      else               g=exp(-q.x*q.x*2.2)*exp(-q.y*q.y*30.0);
      g*=1.0-smoothstep(0.75,1.0,d2);
      gl_FragColor=vec4(vColor*g,1.0);
    }`,
  transparent:true, depthTest:false, depthWrite:false,
  blending:THREE.CustomBlending, blendEquation:THREE.AddEquation,
  blendSrc:THREE.OneFactor, blendDst:THREE.OneFactor });
const glowPts=new THREE.Points(glowGeo,glowMat);
glowPts.frustumCulled=false; glowPts.renderOrder=2;
scene.add(glowPts);
```

Hmm — glow streak for kind 2: exp(-q.y²*30) at q.y=0.2 → 0.30 — thin ✓; rim fade kills at d2>0.75... rim fade multiplies streak ends too ✓ fine.

Background:

```js
const NBG=2600;
const bgPos=new Float32Array(NBG*3), bgCol=new Float32Array(NBG*3),
      bgSize=new Float32Array(NBG), bgTw=new Float32Array(NBG);
for(let i=0;i<NBG;i++){
  const u=rnd()*2-1, ph=rnd()*TAU, s1=Math.sqrt(Math.max(0,1-u*u));
  const R=1400+1100*rnd();
  bgPos[i*3]=R*s1*Math.cos(ph); bgPos[i*3+1]=R*u; bgPos[i*3+2]=R*s1*Math.sin(ph);
  const t=rnd(); let r,g,b;
  if(t<0.18){ r=1.0;g=0.82;b=0.66; } else if(t>0.82){ r=0.72;g=0.83;b=1.0; } else { r=0.92;g=0.95;b=1.0; }
  let br=0.10+0.55*rnd()*rnd(), size=0.7+1.5*rnd()*rnd();
  if(rnd()<0.03){ br=1.1; size=2.6; }
  bgCol[i*3]=r*br; bgCol[i*3+1]=g*br; bgCol[i*3+2]=b*br;
  bgSize[i]=size; bgTw[i]=rnd()<0.35?0.5+0.5*rnd():0.0;
}
const bgGeo=new THREE.BufferGeometry();
bgGeo.setAttribute('position',new THREE.BufferAttribute(bgPos,3));
bgGeo.setAttribute('aColor',new THREE.BufferAttribute(bgCol,3));
bgGeo.setAttribute('aSize',new THREE.BufferAttribute(bgSize,1));
bgGeo.setAttribute('aTw',new THREE.BufferAttribute(bgTw,1));
const bgMat=new THREE.ShaderMaterial({
  uniforms:{uPR:{value:1},uTime:{value:0}},
  vertexShader:`
    uniform float uPR,uTime;
    attribute vec3 aColor;
    attribute float aSize,aTw;
    varying vec3 vColor;
    void main(){
      vec4 mv=modelViewMatrix*vec4(position,1.0);
      gl_Position=projectionMatrix*mv;
      float tw=1.0-aTw*0.45*(0.5+0.5*sin(uTime*(0.4+fract(aTw*13.7)*1.3)+aTw*97.0));
      gl_PointSize=aSize*uPR;
      vColor=aColor*tw;
    }`,
  fragmentShader:`
    varying vec3 vColor;
    void main(){
      vec2 q=gl_PointCoord*2.0-1.0;
      float d2=dot(q,q);
      if(d2>1.0) discard;
      float g=exp(-d2*3.5)*(1.0-smoothstep(0.7,1.0,d2));
      gl_FragColor=vec4(vColor*g,1.0);
    }`,
  transparent:true, depthTest:false, depthWrite:false,
  blending:THREE.CustomBlending, blendEquation:THREE.AddEquation,
  blendSrc:THREE.OneFactor, blendDst:THREE.OneFactor });
const bgPts=new THREE.Points(bgGeo,bgMat);
bgPts.frustumCulled=false; bgPts.renderOrder=0;
scene.add(bgPts);
```

Resize:

```js
let PR=Math.min(window.devicePixelRatio||1,2);
const dbSize=new THREE.Vector2();
function onResize(){
  renderer.setPixelRatio(PR);
  renderer.setSize(window.innerWidth,window.innerHeight);
  camera.aspect=window.innerWidth/window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.getDrawingBufferSize(dbSize);
  const proj=dbSize.y/(2*Math.tan(camera.fov*Math.PI/360));
  starsMat.uniforms.uProj.value=proj;
  glowMat.uniforms.uProj.value=proj;
  bgMat.uniforms.uPR.value=PR;
}
window.addEventListener('resize',onResize);
onResize();
```

Cores:

```js
const relP=new THREE.Vector3(105,0,0), relV=new THREE.Vector3(-3.2,0,1.12);
let simT=0;
function stepCores(h){
  const S2=relP.lengthSq(), S=Math.sqrt(S2);
  const inv=1/Math.pow(S2+CC2,1.5);
  let ax=-MU*relP.x*inv, ay=-MU*relP.y*inv, az=-MU*relP.z*inv;
  const late=0.45*sstep(45,60,simT);
  const dg=CD*sstep(13,19,simT)*Math.exp(-S2/LAM2)
          +NEAR_K*Math.exp(-S2/NEAR2)
          +late*Math.exp(-S2/LAM2);
  ax-=dg*relV.x; ay-=dg*relV.y; az-=dg*relV.z;
  relV.x+=ax*h; relV.y+=ay*h; relV.z+=az*h;
  relP.x+=relV.x*h; relP.y+=relV.y*h; relP.z+=relV.z*h;
}
```

Sim step fn + loop + HUD + phase as planned.

Wait — order in file: simStep function references rtP etc ✓ defined above ✓.

**Loop:**

```js
const hT=document.getElementById('hT'), hS=document.getElementById('hS'),
      hV=document.getElementById('hV'), hP=document.getElementById('hP'),
      titleEl=document.getElementById('title');
let lastT=-1, acc=0, idx=0, passages=0, prevS=1e9, descending=false, ftAvg=16.7, ftN=0;

function phaseName(S){
  if(simT>64&&S<4) return 'MERGER REMNANT';
  if(passages===0) return S<34?'FINAL APPROACH':'FIRST APPROACH';
  if(S<4.2) return 'COALESCENCE';
  if(S<13){
    if(passages===1) return 'FIRST PASSAGE \u00B7 BRIDGE';
    if(passages===2) return 'SECOND PASSAGE';
    return 'FINAL PASSAGES';
  }
  if(passages===1) return 'TIDAL TAILS EJECTING';
  if(passages===2) return 'TAILS EXPANDING';
  return 'RAPID INSPIRAL';
}

function loop(tms){
  requestAnimationFrame(loop);
  const t=tms*0.001;
  if(lastT<0) lastT=t;
  const rawDt=Math.max(0,t-lastT); lastT=t;
  const dt=Math.min(rawDt,0.05);

  ftAvg+=(rawDt*1000-ftAvg)*0.05;
  if(++ftN>=90){ ftN=0; if(ftAvg>34&&PR>1.01){ PR=Math.max(1,PR-0.25); onResize(); } ftAvg=16.7; }

  const S0=relP.length(), V0=relV.length();
  const gate=clamp((V0-5)/3.5,0,1);
  const slow=1-0.62*Math.exp(-((S0-9.5)*(S0-9.5))/12.25)*gate;
  acc+=dt*SPEED*slow;
  const n=Math.max(1,Math.min(4,Math.ceil(acc/0.03)));
  const h=acc/n; acc=0;
  for(let k=0;k<n;k++){
    stepCores(h);
    velMat.uniforms.uCoreA.value.set(-relP.x*0.5,-relP.y*0.5,-relP.z*0.5);
    velMat.uniforms.uCoreB.value.set( relP.x*0.5, relP.y*0.5, relP.z*0.5);
    simStep(h);
    simT+=h;
  }

  const S=relP.length();
  if(S<prevS) descending=true;
  else if(descending){ if(prevS<17.5) passages++; descending=false; }
  prevS=S;

  const fit=Math.max(1,1.15/camera.aspect);
  const ang=1.12+0.045*t;
  const el=0.34+0.17*sstep(4,26,t)+0.02*Math.sin(t*0.23);
  const R=(152-24*sstep(4,26,t)+6*Math.sin(t*0.16+1.7))*fit;
  camera.position.set(R*Math.cos(el)*Math.cos(ang),R*Math.sin(el),R*Math.cos(el)*Math.sin(ang));
  camera.lookAt(0,0,0);

  const gp=glowGeo.attributes.position.array;
  const Ax=-relP.x*0.5,Ay=-relP.y*0.5,Az=-relP.z*0.5;
  gp[0]=Ax;gp[1]=Ay;gp[2]=Az;  gp[3]=-Ax;gp[4]=-Ay;gp[5]=-Az;
  gp[6]=Ax;gp[7]=Ay;gp[8]=Az;  gp[9]=-Ax;gp[10]=-Ay;gp[11]=-Az;
  gp[12]=Ax;gp[13]=Ay;gp[14]=Az; gp[15]=-Ax;gp[16]=-Ay;gp[17]=-Az;
  glowGeo.attributes.position.needsUpdate=true;

  starsMat.uniforms.uTime.value=t;
  bgMat.uniforms.uTime.value=t;

  hT.textContent='+'+String(Math.floor(simT*MYR_PER_TU)).padStart(3,'0')+' MYR';
  hS.textContent=(S*KPC_PER_U).toFixed(1)+' KPC';
  hV.textContent=Math.round(relV.length()*KMS_PER_V)+' KM/S';
  hP.textContent=phaseName(S);
  if(t>10) titleEl.classList.add('gone');

  renderer.render(scene,camera);
}
requestAnimationFrame(loop);
```

And wrap in try/catch:

Actually structure: put everything inside an IIFE with try/catch, or top-level with window error handler... I'll wrap the whole module body in try/catch:

```js
try {
  ... everything ...
} catch(err){
  const d=document.createElement('div');
  d.style.cssText='position:fixed;inset:0;z-index:9;display:flex;align-items:center;justify-content:center;color:#9fb4d0;font:12px/1.6 ui-monospace,monospace;text-align:center;padding:0 24px';
  d.textContent='Could not start WebGL: '+(err&&err.message?err.message:err);
  document.body.appendChild(d);
}
```
Note: function declarations inside try block are fine (block-scoped in strict? module code is strict; function declarations in blocks are block-scoped but all within same block ✓ fine).

Hmm — `requestAnimationFrame(loop)` inside try ✓; errors thrown inside loop's rAF callback occur outside try — acceptable (after setup succeeds, runtime errors unlikely).

Now — **simStep defined before loop; verify it references `idx` (let in outer scope) ✓.**

```js
function simStep(h){
  velMat.uniforms.tPos.value=rtP[idx].texture;
  velMat.uniforms.tVel.value=rtV[idx].texture;
  velMat.uniforms.dt.value=h;
  quad.material=velMat;
  renderer.setRenderTarget(rtV[1-idx]);
  renderer.render(simScene,simCam);
  posMat.uniforms.tPos.value=rtP[idx].texture;
  posMat.uniforms.tVel.value=rtV[1-idx].texture;
  posMat.uniforms.dt.value=h;
  quad.material=posMat;
  renderer.setRenderTarget(rtP[1-idx]);
  renderer.render(simScene,simCam);
  renderer.setRenderTarget(null);
  idx=1-idx;
  starsMat.uniforms.uPosTex.value=rtP[idx].texture;
}
```

**Check: starsMat.uniforms.uPosTex initial value rtP[0].texture — before first simStep, but first loop runs substeps before render ✓.**

Now — a couple of remaining verification passes on **GLSL numeric literal styles** (floats need decimals: `0.5` etc — check `v*=70.0/sqrt(s2)` ✓; `uGrav.x*ab*ab*ab` ✓).

**In starsVert: `float ps=aProp.x*uProj/max(0.1,-mv.z);` ✓.**

**Glow vertex: `attribute float aSize,aAlpha,aKind;` — GLSL allows comma-separated declarations? `attribute float aSize, aAlpha, aKind;` — yes valid GLSL. I'll write them separated for clarity: three lines.**

**three.js prelude also declares `attribute vec3 position;` etc — my extra attribute declarations coexist ✓.**

**Check bgVert `fract(aTw*13.7)` with aTw up to 1.0 ✓.**

**Stars: aProp.z=ph random 0..1; `fract(aProp.z)*1.7` → 0..1.7 + 0.55 → freq 0.55–2.25 rad/s?? that's sin(uTime*freq) — period 2π/2.25 ≈ 2.8s ✓ gentle.**

**One more — the `dim` when ps<1.25: uses ps²/1.5625 — at ps→0 (size 0 spares): dim→0 ✓ and alpha 0 ✓ double-invisible ✓.**

**Check spare particles: propArr all zeros → size 0, alpha 0, tw 0 ✓; pos (5e4,0,0) ✓ vel 0 ✓.**

Wait — actually default Float32Array zeros ✓ but posArr[i*4]=5e4 set; y,z remain 0 ✓.

**Now check the initial relative orbit once more against the drag gate timing:** gate sstep(13,19,simT) — pass1 at ~18: gate≈0.83 at 18 — drag during final approach r~12-15: exp(−(13²)/81)=exp(−2.09)=0.124 ×0.14×0.83=0.0144×v — tiny ✓.

**Check the slow-mo gate: (V0−5)/3.5 — during approach V0 grows 3.4→12.5; at V0=8 (t≈16): gate=0.86, S≈20: exp(−(10.5²)/12.25)=exp(−9)=1.2e−4 ✓ negligible ✓.**

**One thing I want to double check: `acc/0.03` ceil → at 60fps acc=0.055 → n=2, h=0.0275 ✓; at 144fps: acc=0.0229 → n=1 h=0.0229 ✓; at 24fps (slow): acc=0.1375 → n=5→4 cap, h=0.0344 ✓ good.**

**Also — the drag `late` uses simT which changes per substep ✓ fine.**

**Verify the HUD `SEP` at merger: S~1.5–3 → 1.9–3.8 KPC ✓.**

**Phase 'MERGER REMNANT' requires simT>64 && S<4 ✓ (S will be <4 ✓).**

Now — **potential problem: `prevS` initialization 1e9 with first frame S=105 → S<prevS → descending=true ✓.**

**Also — `passages` could over-count if S oscillates due to binary wobble post-merger (S<17.5 always ✓ counts increments each wobble cycle!). Post-merger S~1.5±: wobbling around → S rises/falls slightly each frame?? The tight binary: S oscillates between ~1 and ~2 each orbit (0.2s) → passages++ rapidly → phaseName with passages≥3 → S<13 branch → 'FINAL PASSAGES' until S<4.2 → 'COALESCENCE' — passages counting irrelevant there ✓. And simT>64 → 'MERGER REMNANT' ✓. So over-counting harmless ✓. But ALSO the slow-mo: gate=(V0−5)/3.5: tight binary V0 = |v_rel| could be ~2–4 (circular at r1.5: v=sqrt(μ r/(r²+4)^1.5)·?? relative orbital speed at r=1.5 softened: a=800*1.5/(2.25+4)^1.5=1200/15.6=76.9 → v=sqrt(a*r)=sqrt(115)=10.7!! v_rel ~10.7 at tight binary → gate=1; slow=1−0.62*exp(−((1.5−9.5)²)/12.25)=1−0.62*exp(−5.22)=0.996 ✓ fine.**

**But wait — v_rel=10.7 at r=1.5 — the HUD VEL shows 10.7*48=515 km/s during final binary — hmm plausible-ish for merging nuclei (500 km/s relative is high but it's a display detail; decays as they sink further (v ~ sqrt(a r): r 0.8: a=800*0.8/(0.64+4)^1.5=640/10=64 → v=sqrt(51)=7.2 → 345 km/s). It'll read as violent final coalescence — acceptable & actually dramatic. OK.**

Hmm — although: near-drag NEAR_K=2.4 with damping time 1/2.4≈0.4 t.u. at r<1 — the binary will sink to r~0.5–0.8 and v_rel ~6–7 → 300 km/s — fine.

**One more scenario check — could the near-drag cause CORES to cross through each other and oscillate wildly (spring)?** Softened harmonic + strong damping → overdamped ✓ no.

**And could drag make relV overshoot to negative radial causing S to grow again post-merge?** Damped ✓.

**Also — after full merge, halo potentials centered at same point: total central attraction doubles → disk stars orbit faster — remnant looks dynamic ✓.**

I'm fairly confident in the plan now. Let me also decide **whether to reduce NSTARS to 26k for weaker GPUs?** Requirement ≥20k. 30k fine — GPU sim is resolution-independent, rendering 64k points trivial. Keep.

**Let me reconsider the star size baseline once more:** stars size 0.32–0.76 typical, giants 0.85–1.4, at uProj≈1037, dist 150: px = size*1037/150 = size*6.9: typical 2.2–5.2px ✓ giants 6–9.7px ✓ nice.

At closest approach camera R≈128–135, dist to near galaxy ~85: px scale ×1.76 → cores sparkle ✓.

**Haze: 3.5–12.5 → 24–86px ✓.**

**glow halo 26 → 180px ✓ nucleus 4.6 → 32px ✓ streak 24 → 166px ✓.**

**bg: size px 0.7–2.6 ×PR ✓.**

Now — final re-read of requirements... "two disk galaxies with visible spiral arms and a bright core" ✓; "each with at least 20,000 stars rendered as glowing points (additive blending)" ✓ 30k+2.2k; "colours going from warm yellow cores to blue-white arms" ✓; "galaxies approach and interact through gravity... tidal tails and bridges pulled out" ✓ emergent restricted 3-body on GPU; "slowly orbiting camera that frames the whole event" ✓; "dark starfield background" ✓; "small on-screen label with simulated time in Myr" ✓; "rAF timestamp" ✓; "GPU or cheap approximation physics" ✓ GPU FBO integration; "full-window canvas + resize" ✓; "starts automatically" ✓; "single html block" ✓; "three r186 ES module import" ✓; "no import map added" ✓.

One more consideration — **`renderer.extensions.get` call BEFORE any RT creation but after renderer creation ✓.**

Also — should I set `renderer.outputColorSpace`? default SRGB ✓ leave.

**Also `THREE.ColorManagement` default enabled — my raw shader colors unaffected ✓ (ShaderMaterial bypasses).**

Alright — also **double-check PlaneGeometry uv attribute exists for `uv` in SIM_VERT ✓ (PlaneGeometry generates uv).**

**Check: `quad=new THREE.Mesh(new THREE.PlaneGeometry(2,2))` — material undefined → default MeshBasicMaterial? Passing undefined material → THREE.Mesh(geometry) uses default `new MeshBasicMaterial()` — fine, replaced before render ✓. Actually I create with only geometry — Mesh constructor signature (geometry, material) — material undefined → defaults ✓.**

Now, one more scan for a subtle bug: in `addGalaxy`, `emit` uses `idx` from closure with `idx++` — fine.

`for(let i=2*(NSTARS+NHAZE); i<NP; i++){ posArr[i*4]=5e4; }` ✓.

**Check the halo streaming cross product for bulge: uses components Nx,Ny,Nz — I wrote tx=Ny*dz−Nz*dy etc ✓ matches cross(n,d).**

**One more check — `Math.hypot` ✓.**

**Potential NaN: vCirc(r) with r>0 ✓; gauss fine; pow(X,-2/3) with X≥1e-6 → max ~1e4 → r=1.5/sqrt(1e4−1)≈0.015 — tiny r bulge stars — fine (deep core; softened potential keeps them sane; vc(0.015)≈sqrt(60*2.25e-4/(2.25)^1.5=0.0135/3.375=0.004)=0.063 — nearly static deep-core stars — they linger at center ✓ fine (they add to the bright core).**

Hmm wait — that formula: v²=GM r²/(r²+ε²)^{1.5}: r=0.015: 60*2.25e-4/(2.2523)^{1.5}=0.0135/3.38=0.004 → v=0.063 ✓ tiny — these stars barely move — good (central density cusp).

**One more possible visual issue: bulge stars with tiny r (~0.015–0.3) all pile at exact center → super bright pinpoint — good (nucleus).**

**Now think about the very center brightness accumulation: ~2000 stars within r<0.5 → each 2–4px → total additive → giant white blob radius few px + glow sprites → brilliant core ✓ "bright core" ✓.**

Also — during the final merger, two such cores coincide → 2× brightness ✓.

**Edge — the spare particles at (5e4,0,0) are INSIDE camera far (9000)? They'd be culled by frustum? frustumCulled=false → they're transformed: position 5e4 → projected... behind/away — they render as 1.25px dots with alpha 0 → fragment writes vColor*g*0 = 0 → invisible ✓ but they still cost a vertex × 1136 — nothing.**

Wait — dim = (ps/1.25)² with ps = 0 → 0; vColor=0; g*0 → black additive → no-op ✓.

**Now — camera `fit` factor also applied to el? no ✓.**

**Also — HUD initial content matches first frame ✓ approx.**

**What about `document.title` ✓.**

**Let me also double check the dt clamp: rawDt can be 0 on double-rAF same timestamp → dt=0 → n=1,h=0 ✓ harmless.**

**`Math.ceil(0/0.03)=0` → n=max(1,0)=1 ✓.**

Now — an important REVIEW of the vel shader's reading of `tPos` w: posFrag writes P.w preserved ✓ (init 0) ✓ irrelevant.

**Also — check that the sim renders don't accidentally use `scene`'s fog/background — simScene separate ✓.**

**Check RT texture .texture reference after swap ✓.**

**Potential state leak: rendering simScene with materials that have `transparent` undefined (default false) — fine.**

**Blending state for sim materials: default NormalBlending; dst alpha... irrelevant, full overwrite ✓.**

I think the code is solid. Let me also add **`renderer.domElement.style` via CSS (canvas selector)** ✓ done.

**Also ensure body has canvas before overlays? z-index handles ✓.**

One more aesthetic double-check — **clear color 0x02030a** = rgb(2,3,10) very dark blue ✓ "dark starfield background" ✓.

**Vignette overlay uses radial-gradient — I'm comfortable: it's a photographic vignette.**

Also **`.ph` letter-spacing .24em with '·' separators ✓.**

Now — **write the final explanation (brief) after the code block** per my practice: describe approach: restricted three-body (two live cores + 65k test particles on GPU ping-pong float buffers), choreographed drag/dynamical friction, spin-up flat rotation curve for stable arms, population-based coloring, camera choreography, slow-mo at passages, HUD mapping.

Also mention the fallback (half-float) & adaptive resolution.

Let me do one more end-to-end mental compile of the script for syntax slips as I write it out — particularly template literals, and that I define `simStep` BEFORE `loop` uses it (function hoisting handles ✓ function declarations hoisted ✓).

Variables used across: `simT` declared once ✓ (don't redeclare). `idx` declared once ✓. `PR` declared before onResize ✓ (onResize called after declaration ✓).

Order plan in script:
1. helpers/RNG
2. constants + vCirc
3. buffers + addGalaxy + GAL + calls + spares
4. renderer/scene/camera
5. RTs + sim materials + init copy
6. star points + glow + bg
7. onResize + listener + call
8. cores + stepCores + simStep
9. HUD refs + loop + phaseName
10. rAF start

All inside try{...}catch{...}.

One catch — `let` declarations inside try block: loop function references them via closure ✓ same block scope ✓.

Also careful: I use `for(const t of [posInit,velInit])` — `t` shadows nothing ✓.

In bg loop I use variable `t` for temperature — inside main try block, later loop uses `t` — different scopes (for-let) ✓.

Let me also double check `starsMat` uniform `uPosTex:{value:rtP[0].texture}` — rtP defined ✓ before starsMat ✓ order ok (RTs created step 5, stars step 6 ✓).

**Also — `glowGeo.attributes.position.array` — BufferAttribute array ✓.**

**Potential problem: glow Points uses default `Points.material` — our ShaderMaterial; three needs `uniform uProj` — provided ✓.**

**One more — `bgMat.uniforms.uPR` updated in onResize ✓.**

**HUD numbers width: '131.3 KPC' — fits ✓.**

Okay — also one last thought about **whether first pericenter could be missed due to too-large h near pericenter**: h≈0.0275; near rp the relative orbit curves sharply: ω = v/r ≈ 12.5/9.4 = 1.33 rad/t.u. → per step 0.037 rad ✓ fine.

And the stars' innermost orbits: ω(1)=3.25 rad/t.u. → 0.09 rad/step ✓.

**Also — the disc inner stars vs BULGE potential ε=1.5: stars at r<1.5 feel near-harmonic ✓ stable ✓.**

Also let me reconsider **whether pass1 at rp 9.4 with disks radius 12 gives tails growing mainly from the NEAR sides** — yes classic bridge (near sides) + tails (far sides) ✓.

**Final: also make sure the two galaxy normals aren't accidentally causing e1/e2 degenerate: n_A≈(0.16,−0.94,−0.30): helper (0,1,0): cross((0,1,0),n) = (1*(−0.30)−0*(−0.94), 0*0.16−0*(−0.30), 0*(−0.94)−1*0.16) = (−0.30, 0, −0.16) ✓ non-zero ✓. n_B=(−0.50,−0.58,0.64): |n.y|=0.58<0.92 → helper (0,1,0): cross = (1*0.64−0, 0−0*(−0.50)?? cross(h,n) = h×n = (h_y n_z − h_z n_y, h_z n_x − h_x n_z, h_x n_y − h_y n_x) = (1*0.64−0, 0−0, 0−1*(−0.50)) = (0.64, 0, 0.50) ✓ fine.**

**Also check n_B normalized: len sqrt(0.25+0.3364+0.4096)=sqrt(0.996)=0.998 → normalize ✓.**

Alright — also I realize I should double check the **`uGrav` vec4 vs GLSL uniform vec4 ✓.**

**And `inversesqrt` availability ✓ GLSL ES 1.0 ✓.**

Let me now also quickly reconsider the **exposure/saturation of the arms against the vignette** — fine.

**Post-30s behavior:** camera keeps orbiting; sim continues (merger remnant, tails shearing). It continues indefinitely ✓.

Also — **a tiny last flourish**: page background CSS matches clear color ✓.

Writing final answer now. Also double check that I DON'T include an importmap (forbidden) ✓ and no addons ✓.

One more potential runtime nit — **`renderer.extensions.get('EXT_color_buffer_float')` on WebGL1 fallback?** r186 requires WebGL2 (WebGL1 removed in r163+) — if WebGL2 unavailable, WebGLRenderer throws → caught → error message ✓.

Also — **`new THREE.WebGLRenderTarget` with `type:THREE.HalfFloatType` fallback ✓.**

Also — in the copy pass, if the RT is HalfFloat but source DataTexture Float32 — fine ✓.

Let me also think — **should the sim include a tiny bit of numerical velocity diffusion guard? no.**

**Final potential pitfall — three.js `Points` + ShaderMaterial + `gl_PointSize` must be set in ALL paths of vertex shader ✓ (single path) ✓.**

**And gl_Position ✓.**

Now also double check the star fragment rim fade: `(1.0-smoothstep(0.72,1.0,d2))` at center 1 ✓ edge 0 ✓.

**One more time about the `slow` formula sign: `1-0.62*exp(...)*gate` max reduction 0.62 → min factor 0.38 ✓ never stalls ✓.**

Also gate uses V0 — during pass1 V0≈12.5 ✓.

**And — `acc` integration: with slow factor applied per frame before subdivision ✓ fine.**

Let me also confirm **`sstep(45,60,simT)` late-drag — simT at that point ~mid-game; harmless if merger already done (S<2: exp(−S²/81)≈1 → adds 0.45 drag on the tight binary → dampens to r~0.6 — hmm makes final binary VERY tight (v_rel ~5 → 240 km/s) fine ✓.**

OK — final worry about **arms winding before pass1 making galaxies look "ring-like" at ~5s:** earlier analysis: inner strands spread Δθ~3 rad by t≈10 — the inner disk (r<4) becomes a bright swirl; outer arms (r 6–12) keep contrast (ΔΩ 0.2 → 2 rad over 10 t.u. — moderate). With 2 log arms initially wound ~1.3 turns, after adding shear the pattern becomes a tighter multi-flop spiral — from the camera distance with additive glow this reads as an elegant pinwheel — acceptable and physically motivated. Plus the encounter re-stirs everything by t≈18. Also the HAZE arms (biased 45%) shear too — same.

Could I reduce early winding a bit more by lowering inner Ω? GM_B=60 gives vc(1)=3.25, Ω(2)=2.04. Alternative: εb=1.9 (softer bulge): vc(2): 60*4/(4+3.61=7.61^1.5=21)=11.4; halo 1.28 → v²=12.7→3.57, Ω(2)=1.78; vc(1): 60/(4.61^1.5=9.9)=6.06+0.34→v²=6.4→2.53, Ω=2.53. Bulge star speeds drop a bit; inner swirl slightly slower; shear (2→12): 1.78−0.35=1.43 vs 1.69 — 15% better. Also softer bulge = cores interact slightly less sharply... MU unchanged ✓; εb=1.9 with bulge Plummer a=1.5? bulge scale 1.5 vs potential ε 1.9 fine.

Hmm, but vc flatness: r=4: 60*16/(19.61^1.5=86.8)=11.06+4.36=15.4→3.93; r=6: 60*36/(39.61^1.5=249)=8.67+7.72=16.4→4.05; r=10: 60*100/(103.61^1.5=1054)=5.69+12.0=17.7→4.21; r=12: 60*144/(147.61^1.5=1792)=4.83+12.85=17.7→4.21 ✓ still flat ✓. Use EB2=1.9²=3.61. Bulge a=1.5 stays.

And bulge vCirc for star speeds: vc(1)=sqrt(6.06+0.335)=2.55 ✓.

Update: EB2=3.61. Also glow nucleus etc unaffected ✓. vCirc in shader uses uGrav=(60,3.61,340,100) ✓ set from constants ✓ consistent.

Escape speeds slightly lower: r=10: 2*(60/√103.61+340/√200)=2*(5.9+24.04)=59.9 same-ish ✓.

OK. Also update drag-free disk stability ✓.

Also **check vc(0.5): 60*0.25/(0.25+3.61=3.86^1.5=7.58)=1.98+340*0.25/(100.25^1.5=1003)=0.085 → v²=2.06 v=1.44, Ω=2.87 — innermost disk stars swirl period 2.2 t.u.=0.66s ✓ lively but not frantic.**

Good — final constants: GM_B=60, EB2=3.61, GM_H=340, EH2=100, bulge Plummer a=1.5.

Hmm — one more: bulge potential εb=1.9 vs bulge star distribution a=1.5 — stars within ~1.5 ✓ consistent-ish ✓.

Also recompute **passage rp vs bulge softening of COMPANION on stars: εb=1.9 fine.**

Now truly write it out.

Wait — one more thing: **the `emit` for bulge uses `vCirc(r)` where r can be 0.015 → vc tiny ✓; and Plummer sample uses a=1.5 ✓.**

Also — **`propArr` twinkle for bulge 0.3–0.6 ✓.**

Also HUD: initial values I hardcode in HTML will be replaced in first frame ✓.

Double-check **`String(Math.floor(...)).padStart(3,'0')`** for e.g. 1042 → '1042' (4 digits, padStart no-op) ✓.

**Also — cap displayed Myr at 9999 ✓ naturally.**

Let me also add the phase line prefixed with a label? `PHASE` small: I set `#hud .ph` as its own line — maybe prefix "▸"? no symbols; keep plain text.

Also — **check `hP` initial 'FIRST APPROACH' ✓ consistent with phaseName at S=105 ✓.**

Now write the FINAL file.

Actually — one more thing to double-check: **`renderer.setRenderTarget(rtV[1-idx])` FIRST FRAME with idx=0 → writes rtV[1] ✓ which was allocated but never initialized — WebGLRenderTarget initializes texture lazily; writing before reading ✓ posStep then reads rtV[1] AFTER writing ✓ same frame ordering inside simStep ✓.**

Also — **`quad.material` swap: rendering simScene twice per substep with different materials ✓.**

Also — after the copy passes, `quad.material` remains copyMat; first substep sets velMat ✓.

Also — the very first `renderer.render(scene,camera)` happens after substeps ✓.

Alright, compose the final answer. I'll keep comments concise. Also final choice: title text, caption text as planned.

Also — one FINAL check of the **star vertex shader `position` attribute semantics**: I named the geometry attribute 'position' with item size 3 where x=u,y=v,z=0 ✓ shader uses position.xy ✓ and three's prelude declares `attribute vec3 position;` ✓ no conflict.

And — `modelViewMatrix` for points object at identity ✓.

Also — **objects at world coords up to 5e4 in vertex shader: mv.z=-5e4 → ps=0*proj/5e4=0 ✓ no INF issues ✓.**

One more consideration — **precision: `highp` default in vertex; fragment default highp too (three sets `precision highp float;`) ✓.**

Writing now.

Also — will the **HUD overlap the canvas top-left galaxies?** Galaxies centered; HUD small corner ✓ fine.

Let me also double check `#hud` line format: labels "T","SEP","VEL" with min-width 3.4em — T row: lab 'T' + value; alignment consistent ✓.

Final: the explanation paragraph after the code (concise, first person, covering: GPU ping-pong restricted three-body, choreographed friction, flat rotation curve & populations, camera+slow-mo, HUD mapping, perf fallbacks).

Also — count: NSTARS*2 = 60,000 stars + 4,400 haze = 64,400 active; caption says "65 536 PARTICLES" ✓ accurate (texture slots).

One more trivial thing: caption "GPU-INTEGRATED GRAVITY" fine.

Also — in `phaseName`, the '·' char — I'll write it directly as '·' (UTF-8 ✓).

Let me write everything now, carefully and completely.

Also — hmm, `const NB=Math.floor(NSTARS*0.24)` = 7200 ✓.

While writing `addGalaxy`, note `cf.tint` used only for haze ✓.

Double-check galaxy B arms=3 → `m*TAU/cf.arms` = m*2π/3 ✓.

Final structural check of loop's nSub cap: at very first frames with lastT init: rawDt≈0 → fine.

Also — safety: if `document.hidden` for a while, rawDt up to big → clamped 0.05 ✓ sim pauses effectively (drops time) ✓ good (no spiral of death).

Done planning. Write the answer.

Let me make sure the GLSL strings don't contain backticks and JS template literal `${}` sequences — none.

Also `u00B7` for '·' — I'll just type '·'.

One more review of value `1.5625` = 1.25² ✓.

Also in stars fragment: `vColor*(g*vAlpha)` — vAlpha is varying float ✓ declared ✓.

In stars vertex: declared `varying float vAlpha;` set ✓.

bg fragment: uses vColor ✓ declared in both ✓.

glow: vKind varying float ✓.

All good. Write final.

Also — hmm, do I want `starsPts.renderOrder=1` etc — with transparent objects three sorts by z anyway; renderOrder overrides ✓ set explicitly.

Also set `bgPts.renderOrder=0; starsPts.renderOrder=1; glowPts.renderOrder=2;` ✓.

Final answer time. I'll write the complete HTML.

Let me also do a final sanity pass on ONE subtle physics-visual coupling: the disk stars orbit their core which MOVES along the prescribed relative orbit — at t=0 cores have velocity (±1.6,0,∓0.56) — the whole galaxy translates — stars' world velocities include the translation via emit ✓ (velArr includes CV) ✓ consistent — galaxies move as coherent bodies initially ✓.

And the STARS feel only the cores (not each other) ✓ restricted ✓.

Also — barycenter: star distribution symmetric-ish; barycenter of STARS drifts slightly (mass not exactly centered on cores due to random sampling — tiny, invisible; camera targets origin (cores' barycenter exactly) ✓ fine.

Also — one more check of v_A: v_rel/2 = (−1.6, 0, 0.56); v_A = −v_rel/2 = (1.6,0,−0.56) ✓ matches GAL[0].v ✓; v_B = (−1.6,0,0.56) ✓.

And initial core positions: A=(−52.5,0,0) = −d/2 with d=(105,0,0) ✓; B=+52.5 ✓.

Write it.

Actually — also worth double-checking `velArr` w default 0 ✓ untouched ✓.

And in posInit DataTexture I pass posArr directly (with w=0) ✓.

NOW writing the deliverable.

Post-code explanation: keep ~10-15 lines, first person, no headings per se... a few short bullets are fine. Also mention tuning constants mapping (1 unit=1.25 kpc, 5 Myr per time-unit).

Also — record window 30s: mention first passage ≈6s, tails by ~10s, coalescence ≈16–20s, remnant after.

Alright.