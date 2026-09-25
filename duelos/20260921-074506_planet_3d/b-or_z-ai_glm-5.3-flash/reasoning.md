The user wants a procedural alien planet rendered from orbit using three.js. Let me plan this carefully — this is a signature-piece kind of scene, and I want it to feel authored, not like a generic "sphere with noise" demo.

Key requirements checklist:
1. Planet with custom shader for terrain colors (oceans, continents, ice caps) based on 3D noise — I'll write a GLSL fragment shader with FBM (fractal Brownian motion) 3D simplex noise. Ocean level, land with elevation-based coloring, polar ice caps, specular highlights on water, subtle emissive city-lights? No — it's an alien planet, maybe bioluminescent coastlines for interest? That could be a nice touch but might look gimmicky. Let me keep it: deep ocean → shallow ocean → beach → lowlands → highlands → mountains → snow, plus ice caps near poles (blend with latitude + noise for irregular edges).
2. Slowly rotating cloud layer — separate sphere slightly larger, with its own shader using 3D noise, alpha blending, rotating at a slightly different speed than the planet.
3. Glowing atmospheric rim (fresnel) — a slightly larger sphere with BackSide material, additive blending, fresnel-based alpha. Also I can add fresnel rim on the planet surface itself.
4. Ring system with transparency — a ring geometry with custom shader: radial noise bands, shadowing from planet (planet shadow on rings!), and the ring casting... at minimum, planet shadow on rings is a big win. I'll compute the shadow in the ring shader: given sun direction and planet center/radius, compute whether the ray from ring point toward sun hits the planet sphere. That's a classic technique and looks great.
5. Small moon orbiting the planet that "casts light and shadow interest" — the moon orbits; it should be lit by the sun (Lambert shading in a shader or MeshStandardMaterial with a directional light). To make shadow interest: I could have the moon pass in front of the planet (transit) and its shadow cast onto the planet — I can compute the moon's shadow in the planet shader! Given moon position (uniform) and sun direction, project: for each fragment on planet surface, compute ray from fragment to sun, check if it intersects the moon sphere → darken. That's a beautiful touch: a moon shadow sweeping across the planet's face. Similarly, the moon can pass through the planet's shadow (eclipse) — I can compute planet shadow on the moon in the moon's shader. Both are doable with analytic sphere shadowing in GLSL. This gives real "shadow interest".
6. Distant sun with lens-flare-like glow — a sprite-like billboard with a shader glow (radial falloff, some anamorphic streak, hexagonal-ish ghost circles?). I'll make a sun billboard with a custom shader: bright core, glow, horizontal streak. Maybe a couple of faint "ghost" discs along the line from sun through screen center — that's a classic lens flare. I can do that in screen space: compute the sun's projected position, and place ghost sprites at mirrored positions. Simpler: build the flare from a few additive sprites (core + halo + streak + ghosts) positioned in NDC space each frame based on sun projection. I'll implement a small lens flare system: sun billboard in world space (scaled large, depthWrite false), plus ghost elements rendered in screen space using an orthographic overlay or just CSS? Better to keep in WebGL: use a THREE.Group with sprites whose positions I compute each frame from the sun's projected NDC position, rendered with an ortho camera in a separate scene pass, or trick: put ghosts in the main scene but compute position via unproject. Easiest robust approach: a second scene with OrthographicCamera(-1,1,1,-1) rendered after the main scene with autoClear false; ghost positions computed in JS from sun's NDC coords. Also fade flare when sun is occluded by the planet (raycast / occlusion test) — nice detail: check if sun is behind the planet from camera's view; fade the flare accordingly. I can do a simple analytic test: ray from camera to sun, distance to planet sphere; if hit before sun distance → occluded. Fade smoothly.
7. Dense starfield — Points with a shader: varying sizes, subtle color variation, twinkle. Also maybe a faint background nebula? Could add a large sphere with a very subtle noise-based nebula tint — alien sky bonus. Keep it subtle. Dense starfield: e.g. 6000 points on a large sphere radius.
8. Camera slowly drifts around the planet — I'll animate camera position on an inclined circular-ish path with slight bobbing, always lookAt planet. Maybe also slight radius breathing. Requirements say no interaction needed; I could still add OrbitControls but the camera is auto-driven, so skip controls. Actually they mention OrbitControls as an example of addons available, but not required. I'll do pure drift.
9. requestAnimationFrame timestamp for time — yes, use `performance.now()`-based timestamp from rAF callback.
10. Full-window canvas + resize handling — yes.
11. Auto-starts, everything important visible in first 30 seconds.

Orbital choreography for the first 30 seconds (I should design this deliberately):
- The moon's orbital period: make it so a transit happens early, say moon passes between sun and planet around t=8–15s, casting a shadow across the planet face. Also a ring crossing view.
- Camera path: start slightly wide, drift in and around, maybe an inclination change so we see rings edge-on-ish then tilt.

Let me design the scene:

Units: planet radius = 10. Ring inner ~14, outer ~24. Moon radius 1.6, orbit radius ~45–55, inclined orbit. Sun far away in a direction, e.g. direction (1, 0.35, 0.5) normalized, distance 400 with a big billboard scale.

Lighting: I'll do most lighting manually in shaders (sun direction uniform) rather than relying on three lights, since everything is custom shaders. That gives full control: terminator line, warm sun color, cool ambient from "space" (very subtle blue-gray fill so the night side isn't pitch black — actually for an alien planet, faint ambient plus maybe subtle night-side glow like bioluminescent plankton along coasts? Hmm, that could be the "signature moment": glowing coastlines on the night side. It's alien and memorable. Let me consider: emissive turquoise speckles along shorelines on the dark side. That's tasteful if subtle — thin glowing rims where ocean meets land, visible mainly on the night side. I'll include it with modest intensity. It sells "alien".)

Shaders needed:
A) Planet surface shader:
- Vertex: pass normal (world), position (world / object), uv not needed (use object-space position for noise so rotation rotates terrain with mesh — I'll rotate the mesh itself for planet spin, so noise in object space stays glued to surface).
- Fragment: 3D simplex noise (I'll write a compact simplex noise implementation — the classic Ashima webgl-noise snoise). FBM with 5-6 octaves. Elevation e = fbm(p * freq). Continent mask: another lower-freq fbm to define continents vs ocean basins. Combine: h = fbm1 * 0.7 + continents*... Let me do: base = fbm(p*1.2) → remap to create land/ocean threshold at seaLevel (adjustable, maybe 0.02). Add ridged noise for mountains on land.
- Colors: alien palette. I want to avoid cliché Earth-blue. Alien: teal/turquoise ocean? Or a violet-ish? Hmm. Let's design a palette: ocean deep = dark indigo-teal (#0a2a3a → maybe #06202e), shallow = bright teal (#1a7f8c), land: dark olive/rust lowlands? Alien vegetation could be deep red/rust vegetation (like Mars with oceans) or teal-green. Let me pick: land lowlands = muted sage/olive-green with rust patches, highlands = rocky tan/gray, mountains = gray-white, snow above threshold. Ice caps at |latitude| > ~0.75 with noisy edge, white-blue. Sun specular on ocean (Blinn-Phong strong specular only on water). Fresnel rim on the planet: slight atmospheric blue scattering at grazing angles on lit side.
- Moon shadow: compute analytically. Given uniform moonPos (world), moonRadius, sunDir: fragment world pos p. Vector from p to sun = sunDir (directional). Compute closest approach of ray (p + t*sunDir) to moon center: d = distance from moon center to the ray. If d < moonRadius and t>0 → in shadow. Soften: smoothstep(moonRadius, moonRadius*0.4, d) for soft umbra, plus a wider penumbra factor. Multiply diffuse light by (1 - shadow). Also add slight ambient unaffected. Since sun is directional, that's fine.
- Night lights: coastline glow — where |h - seaLevel| small AND on the night side (dot(normal, sunDir) < 0), add emissive teal. Use noise to break it into speckles/blobs. Subtle.

B) Cloud shader:
- Sphere radius planetR * 1.03. Own rotation (slower or faster). Fragment: fbm 3D noise in object space, threshold for cloud coverage, alpha = smoothstep. Color white-ish but tinted by sun: lit side white, night side very dark blue. Also add slight fresnel edge fade so clouds don't silhouette hard. Use same lighting: NdotL for shading clouds. Clouds should be lit like the planet. Transparent, depthWrite false.
- Maybe two cloud systems? Keep one, with a big swirl: distort noise by rotating domain over time slightly? Clouds rotate with mesh (mesh.rotation.y += dt * speed). Add noise domain warp for interesting shapes: p + fbm offset.

C) Atmosphere rim:
- Sphere radius planetR * 1.07, BackSide? Standard approach: material with side: BackSide, blending: Additive, fragment computes fresnel using view dir and normal: glow = pow(1 - dot(viewDir, normal)... For backside sphere, intensity peaks at rim. Also modulate by sun: atmosphere glows brighter on lit side — compute sunFactor = clamp(dot(normal, sunDir)*0.5+0.5...) and maybe a forward-scattering boost when looking toward the sun through the limb. Color: alien atmosphere — maybe a cyan/mint atmosphere to match teal ocean? Or a peach/orange atmosphere contrasting with teal? Peach-orange rim on teal ocean could be gorgeous. Let me pick atmosphere color: soft aqua-cyan with a hint of green... Actually a subtle two-tone: base cyan, with orange tint at terminator (sunset ring!) — that's a beautiful detail: near the terminator the rim shifts warm. Implement: warmth = based on dot(normal, sunDir) near zero → mix in orange. 

D) Rings:
- RingGeometry(inner, outer, segments). Need proper UVs: RingGeometry UVs are weird (they're planar). Better to compute radial coordinate in shader from world/object position: in object space, ring lies in XY plane; radius = length(position.xy). Pass position as varying. Fragment: r normalized t = (r - inner)/(outer - inner). Banding: 1D noise function of r (use fbm over r*freq via a hash-based 1D value noise, or reuse 3D noise sampled at vec3(r*40.0, 0, 0)). Alpha = band pattern * smooth edges (fade at inner and outer). Color: icy tan/gray with subtle hue variation by radius. Lighting: rings are thin particles — shade by |dot(sunDir, ringNormal)|-ish, plus back-scattering; simpler: brightness = 0.5 + 0.5*abs(dot(sunDir, planeNormal))? Actually rings brightness depends on whether sun is above/below and viewing angle; simple approach: base brightness constant, plus planet shadow computed analytically: ray from ring point toward sun; does it hit planet sphere (center at world origin, radius planetR)? Since planet center is at origin and rings centered too, compute: p world, d = sunDir; find closest approach of ray to origin: b = dot(p, d); closest = p - d*b (if b < 0, sun is "behind" in that direction... careful: we want the shadow when the planet is between the point and the sun, i.e., moving from p along +sunDir we approach the sun; shadow occurs if the segment from p toward sun passes through planet sphere: t = dot(-p, d)... let me just compute: let v = -p (vector from point to planet center). proj = dot(v, d) (distance along ray to closest approach to center). If proj > 0: closestPoint = p + d*proj; distToCenter = length(closestPoint). If distToCenter < planetR → shadow. Soft edge: smoothstep(planetR, planetR - 1.0, distToCenter)? Soften with smoothstep over ~1 unit penumbra. Also alpha of shadow multiplies light.
- Also ring shadow on the planet! The planet shader could compute ring shadow: does the ray from planet surface point toward sun cross the ring plane between inner and outer radius? That's a great detail: rings cast a banded shadow line across the planet. Compute: plane y_world = 0 (rings in XZ plane if I rotate ring geometry to lie flat). Ray from p along sunDir: t = -p.y / sunDir.y if sunDir.y != 0 and t>0; hit point q = p + sunDir*t; r = length(q.xz); if inner < r < outer → in ring shadow with the same banding alpha (sample band function at r). This needs the band function shared between shaders — duplicate GLSL code, fine. This is a gorgeous detail: thin shadow bands across the planet's clouds too? I'll add it to planet at least; clouds could have it too but let's keep clouds simpler... Actually adding to clouds is the same computation — include for consistency (rings shadow falls on clouds too). Maybe just planet to keep cloud shader lighter. Hmm, I'll add to both — it's cheap (one ray-plane intersection + noise eval). Actually cloud shader already expensive with fbm; one more 1D fbm fine.

- Ring transparency & lighting on both faces: side: DoubleSide, transparent, depthWrite false.

E) Moon:
- Moon mesh: custom shader or MeshStandardMaterial? For eclipse shadow (planet shadow on moon) I need custom logic: ray from moon surface toward sun, check intersection with planet sphere (center origin, radius R): similar analytic test. Plus Lambert + a bit of ambient. I'll write a small custom shader for the moon with 3D noise for crater-ish mottling and simple lambert, plus eclipse softening: penumbra scale relative to... simple smoothstep on distance vs planet radius with soft edge ~ planetR*0.15. The moon also should receive... does the moon's shadow hit the planet? Yes — planet shader handles it via moonPos uniform. And ring shader could receive moon shadow too — skip, minor.
- Moon orbit: inclined plane, e.g. inclination 12° from ring plane, radius ~48, period ~ let's choreograph: I want a transit in the first 30s. Moon angular speed ω = 2π / T. If T = 60s, moon does half an orbit in 30s. I can set initial phase so that at t ≈ 12s the moon crosses the sun-planet line (as seen broadly). The shadow will sweep across the planet when the moon is between sun and planet — that happens when moon position ≈ along sunDir direction from planet (moon at position ≈ sunDir * orbitR) — wait: for the moon to be between sun and planet, moon should be on the sun side: moonPos ≈ sunDir * orbitRadius. Then its shadow falls on the planet. Set phase so moonPos = sunDir * orbitR at t≈12s. But also the camera should be positioned to see the shadowed face. Camera drifts around; the shadow sweeps the hemisphere facing the sun; camera sees the lit face when camera is roughly on the sun side too. Hmm, I need to choreograph camera and moon together.

Let me set up coordinates: sunDir = normalize(vec3(1.0, 0.25, 0.6))... let me choose sun direction = normalize((1, 0.3, 0.35))? I'll place sun visual at sunDir * 700 (beyond starfield? starfield at radius ~1200; sun sprite at ~600 with scale ~90). Make starfield radius 1500, sun at 800, far plane 4000.

Camera path: radius oscillates 26 → 40, angle θ(t) = slow rotation. I want at transit time (t≈10–16s) the camera to be near the sun side, looking at the planet with the moon shadow visible, and the moon itself visible in frame near the limb. Camera angle: position = (cos θ, φ, sin θ)*radius with some inclination. If sun is along +X mostly (sunDir ≈ normalize(1, 0.28, 0.45)), then camera near θ ≈ 0 is on the sun side.

Let me define: θ(t) = θ0 + 2π * t / 90 (full orbit in 90s). θ0 = -0.5 rad, so at t=12s, θ ≈ -0.5 + 0.84 ≈ 0.34 rad — near sun side. Good. Also vertical bob: y = sin(t*0.15)*3 + base inclination. Camera lookAt slightly offset (0,0,0) with maybe slight offset toward the moon during transit? Keep lookAt at planet center with slight drift; planet occupies frame. FOV 55.

Also during first seconds, maybe start slightly further and dolly in for a reveal: radius(t) = 34 + 8*sin(t*0.1 + 1) → at t=0 radius ≈ 34+8*0.84 ≈ 40.7, at t≈? min when sin = -1 → t*0.1+1 = -π/2+... hmm sin(t*0.1+1) = -1 when t*0.1+1 = 3π/4? no, -1 at angle = -π/2 + 2πk → t*0.1 = -1 - π/2 + 2π → t = ( -2.5708 + 6.2832)/0.1 = 37.1s. Too late. Use radius = 30 + 6*sin(0.12*t - 1.2): at t=0, sin(-1.2) = -0.93 → r ≈ 24.4; rising... Let me just do: r = 32 - 7*exp(-t*0.15) + 2.5*sin(t*0.2): starts at 32-7+0 = 25, settles toward 32 ± 2.5. Nice slow drift-in reveal. Fine.

F) Sun & lens flare:
- Sun billboard: THREE.Sprite? Sprite material with custom... SpriteMaterial can't take custom shader easily. Use a plane mesh that always faces camera: use THREE.Sprite with a CanvasTexture? No external images but CanvasTexture is generated locally — allowed (no external resources). But shader approach is cleaner: create a PlaneGeometry(1,1) with ShaderMaterial (additive, depthWrite false, depthTest true? If depthTest true and planet occludes sun, the sprite gets hidden properly — good for realism; when sun is behind planet we shouldn't see it. Sun at distance 800, planet at origin radius 10 — when camera is on the opposite side, planet blocks the sun sprite. With depthTest true and the sprite at distance 800, it'd be occluded — but partially? It would be fully hidden behind planet core — but a real sun behind a planet would show atmosphere glow spill. That's handled by atmosphere rim (backside additive sphere renders over? Atmosphere at radius ~10.7 also depth tested... it's a mesh at that location, so it occludes the sun too. The atmospheric rim glow would still be visible around the planet limb — okay that reads fine.)
- Actually simpler and prettier: render the sun with depthTest true so occlusion is natural, and separately compute occlusion factor for the lens flare ghosts in JS (ray-sphere test), fading them.
- Sun shader: uv-centered radial glow: core = exp(-r*k) hot white-yellow core, halo = exp(-r*k2) tinted, plus subtle rays? Maybe a 4-point star diffraction cross: spikes = pow(abs(uv.x),...)... Let me do: intensity = core + halo + cross spikes (thin horizontal + vertical streaks) with slight warm color (slightly greenish-white or warm white). Alien sun could be a bit orange or white-blue. Let's make it warm white with peach halo to match atmosphere.
- Lens flare ghosts: in JS, compute sun position projected to NDC: sunNDC. Ghost positions: center of screen (0,0) mirrored: ghost_i position = sunNDC * (-k_i) for various k (0.3, 0.6, 1.0, 1.4...). Render ghosts as circles with ring edges, colored subtly (teal/amber), additive, in an ortho overlay scene. Also anamorphic horizontal streak centered at sun in screen space: a wide thin quad at sun NDC position — but sun NDC might be off-screen; streak visible only partially. I can render overlay elements even when sun is off-screen (ghosts along the center line are visible even when sun is off-screen — classic). But keep intensity tied to occlusion & sun visibility factor.
- Implementation: second scene `flareScene` with `OrthographicCamera(-aspect, aspect, 1, -1)`; each element is a mesh with PlaneGeometry positioned at sunNDC * aspect (x scaled by aspect) etc. Simpler: use NDC coordinates directly and set ortho camera to (-1,1,1,-1) but then x positions need aspect correction for circular ghosts: ghost circle in NDC would be elliptical. To keep circles, scale x by aspect: position x_ndc * aspect when rendering with ortho(-aspect, aspect...). I'll do: ortho camera left=-aspect, right=aspect, top=1, bottom=-1. Ghost at screen pos: (sunNDC.x * f * aspect? hmm. Let me think: screen position in "aspect-corrected NDC" space: sx = ndc.x * aspect, sy = ndc.y. Ortho camera maps x∈[-aspect, aspect]. So ghost center at (ndc.x * k * aspect, ndc.y * k) for factor k (mirrored through center). Ghost size in these units ~0.05–0.15 (height fraction). Circle geometry radius in y-units; with ortho aspect correction, a circle of radius r in this space appears as... x-units equal y-units visually only if we set ortho to (-aspect, aspect, 1, -1) with canvas aspect = W/H — then one unit in x = one unit in y on screen. Yes: because visible x-range = 2*aspect corresponds to width W, so x-unit = W/(2*aspect) = H/2 = y-unit. 
- Ghost shader: circle with soft edge and ring: intensity = smoothstep(1, 0.8, r) * (0.35 + ring at r≈0.85). Tint per ghost. Opacity multiplied by flare visibility factor (computed in JS: occlusion of sun by planet: fade, plus fade when sun NDC far off-screen: factor = smoothstep based on distance of sunNDC from view frustum, e.g. fade out beyond |x|>1.8 or so; ghosts can persist a bit off-screen).
- Also fade flare by sun's depth? Skip; analytic occlusion enough.

Occlusion test JS: camera position C, sun world position S, planet center O=(0,0,0), radius R=10 (maybe use atmosphere radius 10.9 for soft). Ray dir D = normalize(S - C). t_max = |S - C|. Closest approach of ray to O: b = dot(O - C, D) = dot(-C, D). If b > 0 and b < t_max: dist = |C + D*b - O|; occlusion = smoothstep(R_atm, R_atm*0.9?, dist) → occluded amount. visibility = 1 - occlusion (with soft edges). Also the sun billboard itself: keep depthTest true so it hides naturally; but also multiply its opacity by visibility to get soft re-emergence rather than hard pop at limb. Nice.

G) Starfield:
- BufferGeometry Points, N=6500, positions on sphere radius 1400–1800 (random), sizes attribute, color temperature variation (blue-white to warm). Shader: gl_PointSize = size * (300/ -mvPosition.z)? For distant points just fixed size scaled by DPR. Add twinkle: brightness *= 0.8 + 0.2*sin(time*speed + phase). Round point shape with soft edge in fragment. Also a few brighter "hero" stars with cross flare? Keep simple: size distribution with a few large.
- Subtle nebula: big inverted sphere (radius 2000, BackSide) with fbm-based very dim tint (deep teal + faint magenta) — additive or normal with dark colors. Keep dim (max ~0.05-0.1) so stars read. This adds "alien sky" richness. I'll include it with careful low intensity. Hmm — a large sphere with 3D fbm evaluated per fragment: fine, 4 octaves. Also render stars just outside? Stars at radius ~1500 < 2000 so they're in front of nebula sphere — with nebula sphere using normal blending and dark colors, and depthWrite... Nebula sphere is opaque (writes depth at 2000) and stars at 1500 pass depth test. Fine. But nebula must not write... it can write depth, doesn't matter. Alternatively render nebula with depthWrite false and it's fine either way. Order: nebula is farther, drawn... make nebula material depthWrite: false, side BackSide, and it renders whenever; stars additive? Stars: additive blending, depthWrite false. Nebula normal blending with colors near black slightly tinted. Ensure render order: set nebula renderOrder = -2, stars = -1.

Also make the nebula very subtle and noise-anisotropic. Fine.

H) Optional: orbit line for the moon? A faint elliptical path adds composition — a subtle line (circle geometry, line basic material, very low opacity) tilted to moon orbit plane. Nice touch, cheap. Maybe skip — could look like clutter. Actually a barely-visible orbit line adds "orbital mechanics" readability. I'll add with opacity 0.15.

Now performance: planet fragment shader with ~6 octave fbm of simplex noise + more — per-pixel cost fine on desktop GPUs; typical for such demos. Cloud shader similar. Rings cheap. Moon cheap. Starfield cheap. Total fine.

Shader code details:

Simplex noise 3D (Ashima): I'll include the standard `snoise(vec3 v)` implementation. It's well-known public-domain code (MIT). I'll write it out.

FBM:
```glsl
float fbm(vec3 p){
  float f = 0.0, a = 0.5;
  for(int i=0;i<5;i++){ f += a*snoise(p); p = p*2.02 + vec3(17.3, 9.1, 3.7); a *= 0.5; }
  return f;
}
```

Terrain generation: I want distinct continents. Approach:
```glsl
vec3 p = normalize(vObjPos); // unit sphere position
float continent = fbm(p * 1.6 + seedOffset); // low freq
float detail = fbm(p * 5.0 + off2);
float ridge = 1.0 - abs(snoise(p*3.5 + off3)); // ridged
float h = continent * 0.75 + detail * 0.25;
h += (ridge - 0.5) * 0.15 * smoothstep(0.0, 0.3, h - seaLevel); // mountains on land
```
Then land = smoothstep(seaLevel, seaLevel + 0.03, h). Ocean depth = seaLevel - h for deep color.

Latitude: lat = abs(p.y) (object space y is spin axis). Ice caps: iceMask = smoothstep(0.72, 0.85, abs(p.y) + 0.06*fbm(p*4.0)) — noisy polar edge. Ice overrides color; also snow on high mountains anywhere.

Color mapping (alien palette):
- deepOcean: #06283a-ish but more alien: deep teal-ink vec3(0.012, 0.09, 0.12)? Let me pick a rich alien ocean: deep = rgb(0.010, 0.075, 0.105) very dark teal; shallow = rgb(0.05, 0.35, 0.38) bright teal-green. Coast shelf band visible.
- Land: lowland vegetation — alien flora could be deep russet/burgundy: rgb(0.32, 0.16, 0.12)? Or mossy olive rgb(0.22, 0.26, 0.14). Mixed: use noise to blend between "vegetation" (dark olive-teal rgb(0.13, 0.24, 0.16)) and "rust desert" (rgb(0.42, 0.23, 0.13)) by region noise → continents with varied biomes. Highlands rocky: rgb(0.38, 0.33, 0.27); peaks snow: rgb(0.9).
- Beach: thin sand band rgb(0.55, 0.45, 0.30).
- Ice caps: rgb(0.85, 0.92, 0.96) with faint blue in crevasses (noise-modulated).

Specular: ocean gets specular = pow(max(dot(reflect(-sunDir, n), viewDir),0), 60) * waterMask; adds sun glint. Also broad soft sheen on water: pow(...,8)*0.15.

Fresnel rim on planet surface: rim = pow(1 - dot(n, viewDir), 3.0) * atmosphereColor * dayFactor — adds atmosphere in-scatter on the limb.

Night side: diffuse = max(dot(n, sunDir), 0.0); ambient = 0.02; nightLights: mask = coast proximity * speckle noise * (1 - dayFactor). Coast proximity = 1 - smoothstep(0.0, 0.05, abs(h - seaLevel)) restricted to land side (h slightly above sea) → glow teal rgb(0.1, 0.9, 0.7) * speckle * night. Also maybe glow only on land near coast. Speckle: snoise(p*30) thresholded → clusters. Keep intensity modest (0.0–0.6) so it's a discovery detail, not garish. It'll be visible in first 30s when the night side rotates into view — with camera near sun side we see mostly day side... The terminator will be visible on the limb regions. Hmm, choreography: maybe at start, the camera sees the planet with a nice terminator (half-lit). If camera is at θ0 = -0.5 and sun at +X-ish, the planet's day side faces the camera mostly... Let me compute: camera position angle θ means camera at (cosθ*R, y, sinθ*R). Sun at direction sunDir = normalize(1, 0.3, 0.45) ≈ azimuth atan2(0.45, 1) ≈ 0.42 rad. When camera azimuth θ ≈ 0.42 → full day side. When θ ≈ 0.42 + π → night side. At θ0 = -0.3, t=0 camera azimuth = -0.3, sun azimuth 0.42: angle between camera and sun azimuth = 0.72 rad ≈ 41° — planet appears mostly lit with terminator slightly visible on one limb (the camera sees the day side offset by 41°, so a crescent-ish... at 41° separation we still see most of the lit face plus a bit of night near the limb). Good: we'll see the terminator band, night glow strip, and as camera drifts we get changing phases. And the moon transit at t≈12s: at t=12, θ = -0.3 + 12*(2π/90) = -0.3 + 0.838 = 0.538 rad — very close to sun azimuth 0.42 → camera near sub-solar point → moon shadow on the planet face visible, moon near the sun direction in the sky (close to sun glare — dramatic!). Hmm, moon near the sun in screen space might get lost in glare. Maybe better: transit when camera is ~60° from sun azimuth so the shadow is clearly on the visible disc and the moon is off to the side. Let's tune: at t=12s I want camera azimuth ≈ sun_az + 0.9? Then the terminator crosses the disc, shadow lands near terminator — dramatic. Hmm, or simpler: camera azimuth ≈ sun_az + 0.5. θ(t) = θ0 + ωt. Choose ω = 2π/90 ≈ 0.0698 rad/s. At t=13: θ = θ0 + 0.907. Want θ ≈ 0.42 + 0.55 = 0.97 → θ0 ≈ 0.063. Then t=0: camera az 0.063 vs sun az 0.42 → separation 0.36 rad (20°): planet nearly fully lit, slightly angled — nice bright opening. Then transit at t≈13s with separation 0.55 rad (~31°): shadow well within the visible disc. Good. Also moon at transit: moonPos ≈ sunDir * orbitR... the moon will appear near the sun's screen direction from the planet — but since camera is 31° off, the moon appears at 31° from the sun in screen space. That's fine, away from glare center.

Moon phase setup: moonPos(t) = orbitR * (cos(a), 0, sin(a)) rotated by inclination matrix; a(t) = a0 + 2π t/T. For moon between sun and planet at t=13s: moon direction from planet ≈ sunDir (azimuth 0.42, elevation ~0.26 above plane? sunDir has y-component 0.28 normalized: elevation ≈ asin(0.28/|..|)... sunDir = normalize(1, 0.3, 0.45): |v| = sqrt(1+0.09+0.2025)=sqrt(1.2925)=1.1369 → y=0.264. elevation ≈ 15.3°. Moon orbit inclination 12° similar-ish. The shadow will still land on the planet even if not perfectly aligned (as long as within ~ the planet's angular size from moon distance: moon at 48, planet radius 10 → shadow cone tolerance ~ ±11.5°). With elevation mismatch ~3°, fine — shadow lands offset from center, which looks natural.

So set moon angular position so that its azimuth = sun azimuth (0.42) at t=13, with T=70s: ω_m = 2π/70 = 0.0898. a0 = 0.42 - 13*0.0898 = 0.42 - 1.167 = -0.747 rad. Moon direction in its orbital plane: (cos a, 0, sin a) then rotate about X axis (or Z) by inclination. The world position: apply small tilt: y = sin(incl)*sin(a)... Let me define orbit: first base circle in XZ: pos = (cos a, 0, sin a) * R; then tilt about the X-axis by inc: pos = (x, -z*sin? ) Let me use a quaternion or simply: y' = z*sin(inc)?? Rotating about X axis by angle inc: y' = y*cos(inc) - z*sin(inc) = -z*sin(inc); z' = y*sin(inc) + z*cos(inc) = z*cos(inc). So pos_world = (cos a * R, -sin a * R * sin(inc), sin a * R * cos(inc)). With inc = 0.2 rad.

Then moon world elevation when a=0.42: y = -sin(0.42)*R*sin(0.2) = -0.408*48*0.1987 = -3.89 → elevation angle = -4.6°. Sun elevation +15.3°. Mismatch ~20° → shadow would miss the planet? The shadow of the moon points along -sunDir from the moon; it hits the planet if the alignment angle < planet angular radius from the moon ≈ atan(10/48) ≈ 11.8°. 20° mismatch → shadow misses. Need better alignment.

Options: tilt moon orbit so elevation matches sun elevation at transit time. Rotate orbit plane about... I can tilt the orbit plane about the axis perpendicular... Let me instead tilt the orbit plane about the X-axis by angle so that at a = a_transit (0.42), the orbit point's elevation ≈ sun elevation. Orbit point elevation for point (cos a, -sin a sin inc, sin a cos inc): elevation angle φ = asin(y/r) = asin(-sin a * sin inc). At a=0.42: -sin(0.42)*sin(inc) = sin(15.3°)=0.264 → sin inc = -0.264/0.408 = -0.648 → inc = -0.7 rad. That's a big tilt (40°) but it's fine — the moon's orbit is tilted ~40°, crossing the ring plane. Actually a highly inclined moon orbit is visually interesting (moon goes above and below the rings). But at inc = -0.7 rad, the orbit's max |elevation| = 40°: the moon will swing high above the planet and low below — nice dynamism. But wait, also need moon crossing in FRONT of planet (between camera-visible side): at transit, moon is on the sun side; camera is 31° off sun azimuth, so the moon at azimuth 0.42 elevation 15° will be visible against the sky near the planet or in front of it? The moon is at distance 48 from planet center; camera at ~32 from center. Whether the moon appears in front of the planet disc depends on geometry: moon at position (0.906, 0.264, 0.333)*48 ≈ (43.5, 12.7, 16.0). Camera at azimuth ~0.97 rad (0.42+0.55), radius ~31, y ~4: camera pos ≈ (31*cos0.97, 4, 31*sin0.97) = (17.4, 4, 25.6). Moon direction from camera: (43.5-17.4, 12.7-4, 16-25.6) = (26.1, 8.7, -9.6), normalized ≈ (0.87, 0.29, -0.32)... The planet direction from camera: (-17.4, -4, -25.6) normalized ≈ (-0.55, -0.13, -0.82). Angle between moon dir and planet dir: dot = 0.87*-0.55 + 0.29*-0.13 + (-0.32)(-0.82) = -0.479 - 0.038 + 0.262 = -0.255 → angle ≈ 105°. So the moon is way off to the side, not against the planet disc — the shadow lands on the planet but the moon itself is off-frame or far to the side. Hmm. That's actually fine and realistic (eclipse shadow from a moon far from the disc). But "moon casts light and shadow interest" — the shadow sweeping across the planet IS the interest; also the moon passing near/in front of the planet would be nice to see at some point in 30s.

Alternative: make the moon orbit tighter (radius 26? but rings go to 24 — moon orbit at 30, just outside rings, period shorter). With moon at 30 and planet radius 10, angular radius from moon = atan(10/30) = 18.4° — more forgiving alignment. And the moon closer appears larger in frame. Let me set moon orbit radius 30, moon radius 1.7 (larger apparent size). Then alignment tolerance ~19°.

Let me reconsider the transit geometry: For the shadow to be visible to the viewer dramatically, ideally the moon is roughly between camera and planet? No — shadow visible when sun-moon-planet roughly aligned, regardless of camera, as long as camera sees the lit face where the shadow falls. The shadow center falls at planet point where the -sunDir ray from the moon center hits. We computed alignment via angular mismatch between (moon→planet direction... hmm actually the shadow direction is -sunDir (directional light). The shadow lands on the planet if the ray from moonPos in direction -sunDir passes within planetR of origin... i.e., the perpendicular distance from origin to the line {moonPos + t*(-sunDir)} < 10 (roughly, and t>0).

Let me parametrize and just choose numbers that work, checking at t=13:
- sunDir = normalize(1, 0.3, 0.45) → s = (0.8796, 0.2639, 0.3958).
- Moon orbit: radius Rm = 30, tilt: I'll tilt orbit about the Z axis? Let me think differently: I want, at transit time, moonPos ≈ s * 30 = (26.4, 7.9, 11.9) (approximately, so that shadow ray passes near origin — actually exact alignment: moonPos = s*30 gives perpendicular distance 0 — shadow dead center. Offset by a couple units for natural look.)
- Moon orbit as circle of radius 30 passing through that point with inclination ~25° for visual interest, and angular speed so it moves visibly (period 70s → moves 0.9 rad in 13s? that's 51°... during the 30s window it'll sweep 154° — dramatic motion, maybe too fast? "small moon orbiting" — a visible sweep is good for a 30s recording. Moon moving through the frame at noticeable speed is good for the recording.)

Define orbit param: pos(t) = Ry(inclination applied via...) — simplest: 
```
a = a0 + wm*t;
pos = vec3(cos a, 0, sin a) * Rm;      // in orbital plane
// tilt about X axis by inc:
pos.y' = -pos.z * sin(inc)? 
```
I want pos(t_transit) = (26.4, 7.9, 11.9). With tilt about X: x = cos a * Rm, y = -sin a * sin(inc) * Rm, z = sin a * cos(inc) * Rm. For y positive at transit need sin(a)*sin(inc) < 0. Let inc = -0.35 rad (tilt so that when sin a > 0, y > 0 since sin(inc)<0 → -sin a * sin(inc) > 0). Then elevation at transit = asin(7.9/30) = asin(0.263) = 15.3° = exactly matching sun elevation. Solve: -sin a * sin(-0.35) * 30 = 7.9 → sin a * 0.3429 * 30 = 7.9 → sin a = 0.768 → a = 0.694 or π - 0.694 = 2.447. Also z = sin a * cos(0.35)*30 = 0.768*0.9394*30 = 21.6 ≠ 11.9. Hmm, with fixed Rm=30, the constraint y/s = sin(elev) and z determined by a; x = cos a * 30. If a = 0.694: x = 30*0.769 = 23.1, z = 21.6 → moon azimuth = atan2(21.6, 23.1) = 0.75 rad vs sun azimuth 0.42. Perpendicular distance of origin from shadow ray: the shadow ray from moonPos P along -s: distance = |P - (P·s)s| = |P|*sqrt(1 - (P·s)²/|P|²)... P·s = (23.1*0.8796 + 7.9*0.2639 + 21.6*0.3958) = 20.32 + 2.085 + 8.55 = 30.95. |P| = sqrt(23.1² + 7.9² + 21.6²) = sqrt(533.6 + 62.4 + 466.6) = sqrt(1062.8) = 32.6. Hmm |P| should be 30... wait Rm=30 and tilt preserves length: x²+y²+z² = 30²·(cos²a + sin²a(sin²inc+cos²inc)) = 900. Let me recompute: x = cos(0.694)*30 = 0.769*30 = 23.07; y = -sin(0.694)*sin(-0.35)*30 = 0.6397*0.3429*30 = 6.58; z = sin(0.694)*cos(0.35)*30 = 0.6397*0.9394*30 = 18.03. |P| = sqrt(532+43+325) = sqrt(900) = 30. ✓. P·s = 23.07*0.8796 + 6.58*0.2639 + 18.03*0.3958 = 20.29 + 1.737 + 7.137 = 29.16. dist = sqrt(900 - 850.3) = sqrt(49.7) = 7.05 < 10 ✓. So the shadow ray passes 7 units from center — lands off-center on the planet. Good enough, and the shadow will be visible.

But honestly, rather than hand-solving exact trig, I'll implement the moon orbit in JS with the tilt and just pick constants, then mentally sanity-check. Also, exact dead-center vs off-center doesn't matter much. But there's risk the shadow never actually crosses the visible disc in the 30s window if I mess up. Let me instead design more robustly: I'll compute the moon position with parameters and ALSO, to guarantee a transit, I can just directly verify the math numerically in my head... Let me simplify by choosing the moon orbit tilted about the X axis as above and choosing a0 so transit occurs at t=12s, and check the shadow distance over the window t ∈ [8, 20].

Parameters: Rm = 30, inc = -0.32, T = 75s → wm = 0.08378 rad/s.
Transit target: shadow near center at t=12 → want P(12)·(direction) such that dist small.
P(t) = (30 cos a, -30 sin a sin inc, 30 sin a cos inc), a = a0 + wm t.
At t=12: a = a0 + 1.0053.
Shadow perpendicular distance d = |P| sin(angle between P and s) = 30 * sqrt(1 - cos²γ) where cos γ = P̂·s.
P̂·s = 0.8796 cos a + (-sin a sin inc)(0.2639) + (sin a cos inc)(0.3958)
= 0.8796 cos a + sin a (−sin(−0.32)·0.2639 + cos(0.32)·0.3958)
sin(-0.32) = -0.3146 → -(-0.3146)(0.2639) = +0.08303; cos(0.32) = 0.9492 → 0.9492*0.3958 = 0.3757. Sum = 0.4587.
So cos γ = 0.8796 cos a + 0.4587 sin a. Max when tan a = 0.4587/0.8796 → a* = 0.4811, max cosγ = sqrt(0.8796² + 0.4587²) = sqrt(0.7737 + 0.2104) = sqrt(0.9841) = 0.99202 → min dist = 30 * sqrt(1 - 0.9841) = 30 * 0.1262 = 3.79. So closest approach of shadow to planet center is 3.79 (within the 10 radius → dead-ish center hit ✓) at a = 0.481.
Set a(12) = 0.481 → a0 = 0.481 - 12*0.08378 = 0.481 - 1.0054 = -0.524.
So a(t) = -0.524 + 0.08378 t.

Check timing of shadow crossing: d(a) = 30 sqrt(1 - (0.8796 cos a + 0.4587 sin a)²). Near a=0.481, cosγ ≈ 0.992 - (dγ²/2)... γ changes at rate da/dt * dγ/da; dγ/da at optimum = |(−0.8796 sin a + 0.4587 cos a)| = sqrt(0.8796²+0.4587²) = 0.992 (derivative magnitude). So dγ/dt = 0.08378 * 0.992 ≈ 0.0831 rad/s. Shadow distance d ≈ 30·|γ| for small γ (approximately, since d = 30 sin γ ≈ 30 γ when γ small; also the shadow moves across the planet at speed ≈ 30·dγ/dt = 2.5 units/s). Planet radius 10: shadow is within the disc for |d| < 10 → γ < 0.333 → duration ≈ 2*0.333/0.0831 ≈ 8.0s. So transit spans roughly t ∈ [8, 16]s with closest approach at t=12. The shadow sweeps across the disc over ~8 seconds — perfect for the recording window. Also need the camera to be looking at the right face: shadow lands near the sub-solar... the shadow is on the planet where the sun-facing hemisphere is (shadow between moon and sun... the shadow falls on the hemisphere facing the sun, around the sub-solar point region). Camera azimuth during t∈[8,16]: θ = θ0 + ωc t. I want camera azimuth ≈ sun azimuth ± up to ~50° during that window so the shadow region is visible. Sun azimuth = atan2(0.3958, 0.8796) = 0.4222 rad.

Camera: ωc = 2π/100 ≈ 0.0628 rad/s (full orbit in 100s — slow drift). At t=12, want camera az ≈ 0.42 + 0.35 (≈20° off sub-solar, so shadow is visible well within the disc with nice terminator context). θ0 = 0.77 - 12*0.0628 = 0.77 - 0.754 = 0.016. So θ(t) = 0.016 + 0.0628 t. At t=0: az 0.016 vs sun az 0.422 → 23° separation: planet mostly lit, slightly from the left — good opening composition. At t=12: 20°. At t=30: az = 1.9 vs 0.42 → 85° off — planet half-lit, terminator center — good closing shot. 

Camera elevation: y = 3.5 + 2.5*sin(t*0.18 + 1.0)? At t=0: 3.5 + 2.5*0.84 = 5.6 (elevation ~10°) looking slightly down at rings; drifting up/down. Let's do y(t) = 4.5*sin(0.11*t + 0.6) + 2. At t=0: 4.5*0.625+2 = 4.81. Fine — gentle vertical drift.

Camera radius: r(t) = 33 - 6*exp(-0.12 t) + 2.0*sin(0.15 t). t=0: 33-6+0 = 27. t=12: 33 - 6*0.237 + 2*0.83 ≈ 33 - 1.42 + 1.66 ≈ 33.2. t=30: 33 + 2*sin(4.5)=33-1.97≈31. Hmm sin(4.5 rad) = -0.978 → 31. Fine: starts ~27, drifts to ~32-34. Planet radius 10 with FOV 50° at distance 27: planet angular size ≈ 2*atan(10/27) ≈ 40° — planet fills a good portion of the 50° FOV vertically. Maybe slightly tight; rings extend to 24 → angular 2*atan(24/27) = 83° — rings would overflow the frame. That's okay-ish (rings sweeping across the frame edges can look cinematic), but I'd rather frame the whole ring system at the start. At distance 40, rings (24) span 2*atan(24/40) = 62° — still over 50° FOV. Distance 55: 2*atan(24/55)=47.3° fits. Hmm, full rings visible requires fairly far. Compromise: radius drift 34 → 40, FOV 55: at 40, ring span = 2*atan(24/40) = 61.9° > 55° — rings slightly cropped at the edges, which honestly looks cinematic (rings sweeping out of frame). But requirement says "everything important within first 30 seconds" — rings being partially cropped is fine as long as the ring system reads clearly. I'd like a wide opening shot: r(0) = 42, settling to ~34. r(t) = 34 + 8*exp(-0.09 t) + 1.5*sin(0.13 t): t=0: 42; t=30: 34 + 8*0.027 + 1.5*sin(3.9) = 34 + 0.22 - 0.32 ≈ 33.9. Good. Planet angular size at 42: 2*atan(10/42) = 26.8° — planet with rings at 55° FOV fills much of frame. Good.

Also, since the moon orbit is tilted (inc -0.32 → moon oscillates y ∈ ±9.5) the moon will pass above/below. At t=12 (a=0.481): moon at (23.1, 6.1... recompute with inc=-0.32: y = -30 sin a sin(-0.32) = 30*0.4626*0.3146 = 4.37; z = 30 sin a cos(0.32) = 30*0.4626*0.9492 = 13.17; x = 30 cos(0.481) = 30*0.8866 = 26.6. Position (26.6, 4.4, 13.2). Camera at t=12: az 0.77, r 33.5, y ≈ 4.5*sin(0.11*12+0.6)+2 = 4.5*sin(1.92)+2 = 4.5*0.937+2 = 6.2 → cam ≈ (33.5*cos0.77, 6.2, 33.5*sin0.77) = (23.8, 6.2, 23.5). Moon direction from camera: (2.8, -1.8, -10.3) → mostly -z... Planet center direction: (-23.8, -6.2, -23.5). Angle between: normalize moon dir ≈ (0.258, -0.166, -0.951); planet dir ≈ (-0.68, -0.17, -0.71)... wait normalize: |(-23.8,-6.2,-23.5)| = sqrt(566+38+552) = sqrt(1156) = 34 → (-0.70, -0.18, -0.69). dot = 0.258*-0.70 + (-0.18)(-0.18)?? dot = (0.258)(-0.70) + (-0.166)(-0.18) + (-0.951)(-0.69) = -0.181 + 0.030 + 0.656 = 0.505 → angle ≈ 59.7°. Moon is 60° away from planet center direction — well outside the planet disc (planet angular radius ~17°), and possibly within FOV? Camera looks at planet center; FOV 55° vertical → half-angle 27.5°; moon at 60° off-axis → out of frame at that moment. The moon will be visible at other times: when is the moon within ~25° of the planet-center direction from the camera? That happens when the moon is roughly behind or in front along the camera axis. The moon at azimuth a (its orbital azimuth ≈ a since inc small-ish, azimuth = atan2(z, x) = atan2(sin a cos inc, cos a) ≈ a). Moon appears in front of the planet (between camera and planet) when moon az ≈ camera az and moon is on camera's side. Camera az goes 0.016 → 1.9 over 30s; moon az = a(t) = -0.524 + 0.0838t goes -0.524 → 1.99. Moon az ≈ camera az when -0.524 + 0.0838t = 0.016 + 0.0628t → 0.021t = 0.54 → t ≈ 25.7s. At t≈25.7s: moon az ≈ 1.63, camera az ≈ 1.63. Moon world pos: a = -0.524+0.0838*25.7 = 1.63 → pos = (30 cos1.63, 4.37-ish, 30 sin1.63 * 0.949) = (30*(-0.0595), 30*0.9982*0.3146, 30*0.9982*0.949) = (-1.79, 9.42, 28.4). Camera at t=25.7: az 1.63, r = 34 + 8*e^{-3.08} + 1.5 sin(3.34) = 34 + 0.38 + 1.5*(-0.197) = 34.08, y = 4.5 sin(0.11*25.7+0.6)+2 = 4.5 sin(3.427)+2 = 4.5*(-0.279)+2 = 0.74. Cam = (34.08 cos1.63, 0.74, 34.08 sin1.63) = (34.08*(-0.0595), 0.74, 34.08*0.9982) = (-2.03, 0.74, 34.02). Moon is at (-1.79, 9.42, 28.4) — that's between camera and planet? Distance from camera to moon ≈ sqrt(0.058 + 75.3 + 31.7) ≈ sqrt(107) ≈ 10.35. Moon direction vs planet direction: planet dir from cam ≈ (2.03, -0.74, -34.02)/34.06 ≈ (0.0596, -0.0217, -0.9987). Moon dir = (0.24, 8.68, -5.62)/10.36 ≈ (0.0232, 0.8376, -0.5425). dot = 0.0014 - 0.0182 + 0.5428 ≈ 0.526 → 58°. Hmm — the moon is above the planet (y=9.42 vs camera y=0.74) so it appears high above the planet, ~58° off-axis → likely outside FOV. Ugh.

The issue: the moon's elevation at a=1.63 is asin(9.42/30) = 18.2° above the ring plane, and camera is near the ring plane → moon appears well above. When the moon is on the camera's side at low elevation (a near π... elevation = 0 when sin a = 0, i.e., a = 0 or π). At a = π (moon opposite the transit side): moon az ≈ π. Camera az reaches π at t = (π - 0.016)/0.0628 ≈ 49.7s — outside the 30s window. At a = 0 (t = 6.25s): moon pos = (30, 0, 0), az 0. Camera az at t=6.25 = 0.41. Moon dir from camera at t=6.25: cam = (r cos 0.408, y, r sin 0.408), r = 34 + 8 e^{-0.75} + 1.5 sin(0.8125) = 34 + 3.77 + 1.09 = 38.9, y = 4.5 sin(1.2875)+2 = 4.5*0.960+2 = 6.32. cam = (35.72, 6.32, 15.42). Moon (30, 0, 0): dir = (-5.72, -6.32, -15.42), norm 17.6 → (-0.325, -0.359, -0.876). Planet dir: (-35.72, -6.32, -15.42)/39.2 = (-0.911, -0.161, -0.393). dot = 0.296 + 0.058 + 0.344 = 0.698 → 45.7° off-axis. Still outside 27.5° half-FOV. Hmm.

The problem: the moon on the camera side at radius 30 vs camera at ~35 — the moon subtends a large angle because it's close to the camera. To have the moon transit visually across the planet disc, the moon should be behind... no wait, in front (camera side) at radius 30 with camera at 38: the moon is 8 units from the camera orbit — appears at large angular offsets. 

Alternative approach for "moon casts light and shadow interest": maybe I'm overcomplicating. The requirement: "a small moon orbiting the planet that casts light and shadow interest". Interpretation: the moon adds light/shadow dynamics — its shadow on the planet (eclipse), the planet's shadow on the moon (lunar eclipse), and it being a lit body in the scene. It doesn't require the moon to visually cross the planet disc. My planned eclipse shadow sweeping the planet IS the shadow interest. Plus I'll make sure the moon is visible in frame at some point in the first 30s (e.g., when it's far to the side but within FOV when the camera is wider, or when passing behind the planet near the limb — a moon disappearing behind the planet is lovely).

Let me check when the moon passes near/behind the planet from the camera's view: moon behind planet (opposite side from camera): moon az ≈ camera az + π. Camera az(t) = 0.016 + 0.0628t; moon az(t) = -0.524 + 0.0838t. Set moon az = camera az + π: -0.524 + 0.0838t = 0.016 + 0.0628t + 3.1416 → 0.021t = 3.682 → t = 175s. Too far. Hmm because moon angular speed only slightly faster than camera. Relative angular rate = 0.021 rad/s → full relative loop = 2π/0.021 = 299s. That means in 30s the moon moves only 0.63 rad relative to the camera. Not great for showing the moon prominently.

Let me speed the moon: T = 42s → wm = 0.1496. Relative rate = 0.1496 - 0.0628 = 0.0868 rad/s → relative loop in 72s. In 30s: 2.6 rad relative swing. Better. Redo transit timing: transit (shadow near center) at a* = 0.481 (computed above, geometry unchanged except Rm — I might raise Rm to 34 to fit outside rings (outer ring 24)... moon at 30 is outside rings (24) fine. Keep Rm = 30.) Hmm wait — should the moon be bigger than... "small moon" — radius 1.7 vs planet 10: ratio 0.17, Earth-Moon is 0.27; fine, reads as small. Maybe 1.5.

Recompute with wm = 0.1496, transit at t = 11: a0 = 0.481 - 11*0.1496 = 0.481 - 1.6456 = -1.165. So a(t) = -1.165 + 0.1496 t.
Shadow crossing: shadow within disc for γ < 0.333 rad; dγ/dt = wm * 0.992 ≈ 0.1484 → duration ≈ 2*0.333/0.1484 = 4.5s. Transit spans t ≈ [8.75, 13.25]. Good — a 4.5s shadow sweep, clearly visible.

Moon visible in frame: when moon az ≈ camera az (moon between camera and planet, or to the side but within FOV): -1.165 + 0.1496t = 0.016 + 0.0628t → 0.0868t = 1.181 → t = 13.6s. At t=13.6: camera az = 0.87, moon a = 0.870. Moon elevation at a=0.87: y = 30 sin(0.87) * 0.3146 = 30*0.7643*0.3146 = 7.21 (positive, above plane); horizontal dist = sqrt(900 - 52) = 29.1; pos = (30 cos0.87, 7.21, 29.1 sin0.87... wait z = 30 sin a cos inc = 30*0.7643*0.9492 = 21.76; x = 30 cos 0.87 = 19.28. pos = (19.28, 7.21, 21.76). Camera at t=13.6: az 0.87, r = 34 + 8 e^{-1.632} + 1.5 sin(2.04) = 34 + 1.615 + 1.354 = 36.97, y = 4.5 sin(0.11*13.6 + 0.6) + 2 = 4.5 sin(2.096) + 2 = 4.5*0.864 + 2 = 5.89. cam = (36.99*... let me: r cos az = 36.99*0.6453?? cos(0.87) = 0.6453? cos(0.87 rad): 0.87 rad ≈ 49.9°, cos ≈ 0.644, sin ≈ 0.765. cam = (23.8, 5.89, 28.3). Moon dir from cam: (19.28-23.8, 7.21-5.89, 21.76-23.5) = (-4.52, 1.32, -1.74), |v| = sqrt(20.4+1.74+3.03) = sqrt(25.2) = 5.02 → dir ≈ (-0.90, 0.26, -0.35). Planet dir: (-23.8, -5.89, -23.5)/34.1 = (-0.698, -0.173, -0.689). dot = 0.628 - 0.045 + 0.241 = 0.824 → 34.5° off-axis. Vertical FOV half = 27.5°, horizontal half = 27.5*aspect (widescreen ~ 43°). Moon at 34.5° off-axis: within horizontal FOV if aspect ≥ 1.26 — on typical widescreen (16:9, aspect 1.78 → horizontal half-angle ≈ 45.5° for vertical 55°... actually hFov = 2 atan(tan(27.5°)*1.78) = 2 atan(0.5206*1.78) = 2 atan(0.9267) = 2*42.8° = 85.6°, half 42.8°). So the moon at 34.5° off-axis horizontally-ish would be visible near frame edge. But distance from camera only ~5 units — the moon (radius 1.5) would appear HUGE (angular radius atan(1.5/5) = 16.7°) — a giant moon looming in the corner of the frame. Hmm, that could actually be a cool foreground moment ("small moon" passing close to camera) but might block the view and look accidental. Risky.

Alternative: make the moon orbit radius larger (44) and slower relative motion but ensure a visible pass. Or: accept the moon being visible mid-frame when it's near conjunction with the planet center direction (in front or behind the planet). Let me compute for behind-the-planet: moon az = camera az + π → with wm=0.1496: 0.0868t = π + ... : -1.165 + 0.1496t = 0.016 + 0.0628t + 3.1416 → 0.0868t = 4.323 → t = 49.8s. Outside window. For in-front (moon between camera and planet): computed t=13.6 above (moon near camera). Hmm.

What if the camera orbits the OTHER direction (ωc negative)? Then relative rate = 0.1496 + 0.0628 = 0.2124 rad/s → relative loop in 29.6s! That means within the 30s window, the moon makes a full relative pass: it will be behind the planet once, in front (near camera) once. Camera moving opposite to the moon also adds dynamism (sun position relative to camera changes faster → terminator phase changes more visibly within 30s — good for showing day/night!).

Camera az: θ(t) = θ0 - 0.0628 t (moving clockwise when viewed from +Y). Sun az 0.422. For the transit at t=11 to be visible, camera az at t≈11 should be near sun az (within ~50°): θ(11) = θ0 - 0.69 ≈ 0.42 + 0.3 → θ0 ≈ 1.41? Let's see: we want at t≈11 the camera az somewhat on the day side, e.g. θ(11) = 0.9 (27° ahead of sun az... camera az 0.9 vs sun 0.422 → 27.5° separation — shadow visible on the lit disc). θ0 = 0.9 + 0.0628*11 = 0.9 + 0.691 = 1.591. Then θ(0) = 1.59 vs sun az 0.422 → separation 1.17 rad = 67°: opening shot shows the planet ~60% lit (nice terminator through frame, night side with glow visible on one limb). Then camera moves toward az 0.9 by t=11 (more day side), transit shadow sweeps t∈[8.75,13.25] with camera separation from sun az: at t=10, θ = 1.59-0.628 = 0.96 → 31° separation. Good. Then camera continues: at t=30, θ = 1.59 - 1.884 = -0.294 → separation from sun az = 0.716 rad = 41°: planet mostly lit with terminator at edge. Hmm, decent arc: start 67° (dramatic terminator), mid 20-30° (bright, transit visible), end 45°.

Moon relative pass: moon az a(t) = -1.165 + 0.1496t. Camera az θ(t) = 1.591 - 0.0628t. Relative angle (moon - camera) = -2.756 + 0.2124t. Moon behind planet (relative ≈ π) at t = (3.1416+2.756)/0.2124 = 27.75s. Ooh — at t ≈ 27.7s the moon passes directly behind the planet (occultation!) right near the end of the 30s window. And when is the moon in front/near camera? relative ≈ 0 at t = 13.0s — right after transit, moon swings around near the camera... At t=13, moon pos: a = 0.779; pos = (30cos0.779, y, 30 sin0.779*0.9492): cos 0.779 = 0.7116, sin = 0.7026 → (21.35, 6.63, 20.0). Camera at t=13: θ = 1.591-0.816 = 0.775, r ≈ 34 + 8 e^{-1.56} + 1.5 sin(1.95) ≈ 34+1.79+1.42 = 37.2, y = 4.5 sin(0.11*13+0.6)+2 = 4.5 sin(2.03)+2 = 4.5*0.897+2 = 6.04. cam = (37.2*0.7143, 6.04, 37.2*0.6997) = (26.57, 6.04, 26.03). Moon dist from cam: (21.35-26.57, 6.63-6.04, 20.0-26.57) = (-5.22, 0.59, -6.57) → |v| = 8.46. Moon appears at angular radius atan(1.5/8.46) = 10° — sizable but at distance 8.5 it's off to the side: direction from cam: (-0.617, 0.07, -0.78); planet dir: (-26.57, -6.04, -26.57)/38.2 = (-0.780, -0.177, -0.779). dot = 0.432 - 0.012 + 0.608 = 1.028?? That's >1 — recalc: 0.617*0.698 = 0.4307; 0.07*(-0.177) = -0.0124; 0.78*(-0.779) = -0.6076?? sign: moon dir z = -0.78, planet dir z = -0.779 → product = +0.6076. Total = 0.4307 - 0.0124 + 0.6076 = 1.026 — impossible, I made an arithmetic slip. Moon dir: (-5.22, 0.59, -6.57)/8.46: components: -0.617, 0.0697, -0.7766. Planet dir: (-26.57, -6.04, -26.57)/38.2 → (-0.698, -0.158, -0.6955). dot = (-0.617)(-0.698) + (0.0697)(-0.6955)?? no: dot = sum of products: (-0.617)(-0.698) = 0.4307; (0.0697)(-0.6955) = -0.0485; (-0.776)(-0.6955) = 0.5397. Sum = 1.029. Still > 1?! That can't be. Let me recompute moon distance: Δ = (-5.22, 0.59, -6.57): 27.2 + 0.35 + 43.2 = 70.75 → |Δ| = 8.41. OK. Hmm, dot > 1 means nearly same direction — the moon is almost exactly along the planet direction from the camera?! Moon at (21.35, 6.63, 20.0), camera at (26.57, 6.04, 26.03): moon is 8.4 away in roughly the same direction as the planet center (planet center at origin, direction (-26.57, -6.04, -26.03) — same octant as moon direction (-5.22, 0.59, -6.57)). Indeed the moon is nearly aligned: it's in FRONT of the planet (closer to camera), slightly off-axis. Angular offset: recompute properly: cos = 1.029/ (1)?? |moon dir| = 1, |planet dir| = 1. dot can't exceed 1 — my components must be slightly off but it's ≈1 → the moon is nearly dead-center in front of the planet at t=13! Interesting: right after the transit (shadow crossing ends t≈13.25), the moon itself... wait no — at transit (t=11) the moon is between sun and planet (on the sun side, az 0.49); camera az at t=11 is 0.90. Moon on the sun side at az 0.49 while camera is at az 0.90 — the moon is 25° away in azimuth from the camera's position around the planet. Is the moon between camera and planet then? Moon pos at t=11: a = -1.165+1.6456 = 0.4806 → (30*0.8868, y, 30*0.4623*0.9492) = (26.6, 4.37, 13.17). Camera at t=11: θ = 1.591-0.691 = 0.900, r = 34 + 8 e^{-1.32} + 1.5 sin(1.65) = 34 + 2.14 + 1.495 = 37.6, y = 4.5 sin(1.81) + 2 = 4.5*0.9716 + 2 = 6.29. cam = (37.6 cos0.9, 6.29, 37.6 sin0.9) = (37.6*0.6216, 6.29, 37.6*0.7833) = (23.37, 6.29, 29.45). Moon dir from cam: (3.23, -1.92, -16.28), |v| = 16.75 → (0.193, -0.115, -0.972). Planet dir: (-23.37, -6.29, -29.45)/38.2 = (-0.612, -0.165, -0.771). dot = -0.118 + 0.019 + 0.749 = 0.650 → 49.4°. So at transit the moon is 49° off the planet-center axis — near/just outside the frame edge horizontally (half-hFov ~43°). The moon might be just outside view during the shadow transit. The shadow is the star anyway. Then by t=13 the moon sweeps around to near the camera-planet axis and appears large in front of the planet. Then it recedes and at t≈27.7 goes behind the planet (occulted). Hmm wait — that trajectory doesn't make sense: the moon orbits continuously; relative angle decreases from... relative = moonAz - camAz = -2.756 + 0.2124t: at t=0: -2.756 rad (≈ -158°) → moon is nearly opposite the camera (behind planet side, but offset 22° so visible to the side, partially behind?). At t=0: cam θ=1.591, moon az = -1.165: difference = -2.756 → moon is at angle 2.756 rad behind... The moon's position relative to the camera-planet axis: moon az - cam az = -2.756 ≈ -158°, meaning the moon is nearly anti-aligned with the camera direction → the moon is behind the planet region, offset by 22°. Planet angular radius from camera at t=0 (dist ~41): atan(10/41) = 13.7°; moon at 22° azimuth offset from anti-camera direction, at distance... moon pos t=0: a=-1.165 → (30cos(-1.165), y, 30 sin(-1.165)*0.9492) = (30*0.3946, 30*(-0.9189)*0.3146, 30*(-0.9189)*0.9492) = (11.84, -8.67, -26.17). Hmm y negative — moon below the ring plane early on. Camera at t=0: θ=1.591 → cam = (r cos1.591, y, r sin1.591) ≈ (r*(-0.0197), y, r*0.9998) ≈ (−0.73, 4.93, 37.0) with r=37.3, y = 4.5 sin(0.6)+2 = 4.53. Moon at (11.84, -8.67, -26.17) — direction from cam: (12.57, -13.6, -63.2), |v| = 66.3 → (0.19, -0.205, -0.953). Planet dir: (0.0197, -0.131, -0.991). dot = 0.0037 + 0.0269 + 0.944 = 0.975 → 13°: the moon appears 13° off the planet center — right at the planet's limb (planet angular radius 13.7°)! At t=0 the moon is emerging from behind the planet's edge (or about to slip behind). Interesting opening: moon near the limb. But it's on the night side (camera at az 1.59, sun az 0.42 — camera is 67° around; the moon at az -1.165 is on the far side... its lit side faces the sun; from the camera we'd see it mostly dark (thin crescent) near the planet's dark limb. Moody opening. Hmm, could be great or could be unreadable. Also the moon is below the ring plane and behind — it may be partially occluded by the planet: distance from cam to moon 66; is the line cam→moon intersecting the planet sphere (radius 10)? Closest approach: cam C=(−0.73, 4.93, 37.0), dir to moon D = (0.19, -0.205, -0.953). b = dot(-C, D) = -(−0.73*0.19 + 4.93*(-0.205) + 37.0*(-0.953)) = -(-0.139 - 1.011 - 35.26) = 36.0. Closest point: C + 36*D = (−0.73+6.84, 4.93-7.38, 37.0-34.3) = (6.11, -1.45, 2.70). Distance from origin = sqrt(37.3 + 2.1 + 7.3) = sqrt(66.5) = 8.15 < 10 → the moon is fully behind the planet at t=0 (occluded). It emerges when closest-approach distance > 10: as relative angle changes at 0.2124 rad/s, the lateral offset grows ≈ 66*0.2124*(t) ≈ 14 t units → exceeds (10 - 8.15) ≈ 1.85 → t ≈ 0.13s?? That linearization is too crude near tangency. Roughly: the moon exits occultation within the first ~1-2 seconds. So the opening shows a moon slipping out from behind the planet — a lovely reveal if it works. But risky: it could instead drift across the planet's disc (transit silhouette) — moon at 66 away, moving laterally at 66*0.2124 ≈ 14 units/s?! That's fast screen motion. Hmm, the relative angular speed 0.2124 rad/s at distance ~60 → the moon crosses the sky quickly. Angular speed as seen from camera ≈ (relative angular rate) since camera orbits too... The moon's angular velocity relative to the camera: both orbit the origin; the moon's apparent motion across the sky = combination. Roughly the moon sweeps 2π relative in 29.6s — it will cross the planet disc quickly at some point (a silhouette transit across the planet! also dramatic) and be near the camera (huge) at t≈13.

Concern: at t≈13 the moon is very close to the camera (8.5 units) and appears large — it might dominate the frame awkwardly, and pass across the view quickly. Let me estimate its angular size over time: camera-moon distance varies a lot. t=13: 8.4 (angular radius 10°); at t=16: relative = -2.756+3.398 = 0.64 rad → moon 37° off-axis... it swings around quickly. This could be chaotic.

Honestly, maybe simpler is better: I don't need the moon to pass super close to the camera. Options: (a) tilt the moon's orbit so it stays mostly outside the camera's orbit radius — camera r ~ 34-40, moon Rm = 48 — then the moon never comes between camera and planet... it can still cross in front of the planet when it's on the camera's side only if its radius < camera radius. With Rm = 44 > camera r ≈ 34-40, the moon stays outside the camera's orbit — it never looms near the camera. It appears in front of the planet only when... no: if the moon is always farther from origin than the camera, it can still be between camera and planet only if... the line from camera to planet extends beyond the planet; the moon at radius 44 crossing that line on the far side of the planet = behind the planet region. In front of the planet disc requires the moon to be between camera and planet → moon distance from camera < camera-planet distance and roughly along that axis → moon within radius < camera radius region... Not strictly (geometry off-axis), but roughly: with Rm > camera r, the moon passes in front of the planet disc only when it's between camera and planet... impossible since the moon is farther from origin than... hmm, actually the camera-planet line: points along it have radii from camera r down to 0. Moon at 44 with camera at 36: the moon could cross that line at a point 44 from origin — which is beyond the camera (36) — i.e., behind the camera. So no in-front transits. The moon will pass behind the planet (occultation) once per relative orbit. With Rm = 44: relative angular rate with wm: choose T_m such that one relative revolution ≈ 30-40s. wm - ωc: with ωc = -0.0628 (opposite), relative rate = wm + 0.0628. For a relative period of ~35s: wm + 0.0628 = 0.1795 → wm = 0.1167 → Tm = 53.8s. In 30s the moon sweeps 0.2124*30... no: 0.1795 rad/s?? recompute: wm + 0.0628 = 0.1167 + 0.0628 = 0.1795 rad/s → in 30s: 5.39 rad relative swing — nearly a full relative loop within the window. So: moon crosses behind the planet once, swings wide to the side, comes around... And transit (eclipse shadow) timing independent-ish.

But also with Rm=44 the moon passes near the sun line for eclipse: same analysis as before with a* = 0.481 for closest shadow approach... wait that a* was computed for the geometry with the shadow-ray closest-approach minimization: cos γ = 0.8796 cos a + 0.4587 sin a (this depended on inc = -0.32 and sunDir only, not Rm). Closest approach distance = Rm * 0.1262 = 3.79 for Rm=30; for Rm=44: 5.55 — still within the planet (10) ✓. Good: shadow sweep with Rm=44: shadow speed across planet ≈ Rm * dγ/dt = 44 * 0.1795*0.992 ≈ 7.8 units/s → crosses the 20-unit disc in ~2.6s. A bit quick but visible. With wm = 0.1167 (same direction as before): relative rate = 0.1167+0.0628 = 0.1795; dγ/dt = 0.1167*0.992 = 0.1158 → shadow crossing duration ≈ 20/(44*0.115) ≈ 20/5.05 ≈ 4.0s. Good.

Let me now fix parameters:
- Camera: θ(t) = θ0 - ωc t with ωc = 0.0628 (camera clockwise). Start θ0 such that opening shows a nice 60-70% lit planet and the transit is visible around t=10-13.
- Moon: a(t) = a0 + wm t, wm = 0.1167, Rm = 44, inc = -0.32 rad tilt about X.
- Eclipse transit: shadow closest at a = 0.481. Set a(t_e) = 0.481 with t_e = 11 → a0 = 0.481 - 1.284 = -0.803.

Wait, earlier I derived a* = 0.481 for inc=-0.32. Let me recheck that derivation: cos γ = s·P̂ where P̂ = (cos a, -sin a sin inc, sin a cos inc) with inc = -0.32: -sin a sin(-0.32) = sin a * 0.3146; sin a cos(-0.32) = sin a * 0.9492. P̂ = (cos a, 0.3146 sin a, 0.9492 sin a). s = (0.8796, 0.2639, 0.3958). cos γ = 0.8796 cos a + sin a (0.3146*0.2639 + 0.9492*0.3958) = 0.8796 cos a + sin a (0.08303 + 0.3757) = 0.8796 cos a + 0.4587 sin a. ✓. Max at a* = atan(0.4587/0.8796) = atan(0.5215) = 0.4800 rad ✓. min distance = Rm sqrt(1-0.9841) = Rm*0.1261.

With Rm = 44: closest shadow distance 5.55 — the shadow center passes 5.55 units from planet center, i.e., the shadow crosses the disc off-center (planet radius 10, so it crosses the middle region). 

Camera at t=11: want camera az ≈ sun az + 0.5 (≈29°): θ(11) = 0.422 + 0.5 = 0.922 → θ0 = 0.922 + 0.0628*11 = 0.922 + 0.691 = 1.613. θ(t) = 1.591 - 0.0628t (close to before). At t=0: θ = 1.591, sun az 0.422 → separation 1.169 rad = 67°. The planet appears ~63% lit? The phase: camera-sun angle 67° → we see a bit more than half the lit hemisphere. Good.

Where does the moon appear relative to frame? Relative angle moon-cam = -2.556 + 0.2124t (recompute: a0 - θ0 = -0.80 - 1.591 = -2.391; relative = a - θ = (-0.80 + 0.1496t) - (1.591 - 0.0628t) = -2.391 + 0.2124t). At t=0: -2.391 rad = -137° → moon is behind the planet, offset 43° from dead-behind → outside the planet disc (angular radius 14°) → visible on the far side, to the left. At t=11 (transit): relative = -2.391 + 2.336 = -0.055 ≈ 0 → the moon is nearly aligned with the camera direction — i.e., the moon is between the camera and the planet?? But at transit the moon must be between the SUN and the planet. Camera az at t=11 = 0.922, sun az = 0.422: they're 29° apart. Moon at az 0.48 (= sun az region). The moon being at relative angle -3° from the camera axis means the moon appears very close to the planet center direction from the camera — the moon is in FRONT of the planet (between camera and planet? or behind?). Moon distance from origin = 44; camera-planet distance ≈ 37.6; the moon is FARTHER from origin than the camera... The camera looks at the planet (origin). The moon at radius 44 in a direction 3° off the camera's look axis: the camera is at radius ~37.6 looking inward at the origin; a point at radius 44 near the camera's azimuth is BEHIND the camera... wait no. Camera at az 0.922, radius 37.6: position ≈ (37.6 cos0.922, y, 37.6 sin0.922) = (22.77, y, 29.75). Moon at a=0.4806: (44*0.8868, 44*0.4623*0.3146*... recompute y: y = -Rm sin a sin inc = -44 * sin(0.4806) * sin(-0.32) = 44*0.4623*0.3146 = 6.40; x = 44*0.8868 = 39.02; z = 44*0.4623*0.9492 = 19.31. Moon pos (39.0, 6.4, 19.3). Camera (22.8, ~6, 29.8). Vector cam→moon = (16.2, 0.4, -10.5); vector cam→origin = (-22.8, -6, -29.75). dot: (16.2)(-22.8) + ... = -369 - 2.4 + 312 = -59 → NEGATIVE → the moon is BEHIND the camera (its direction from camera is opposite the planet direction). So at t=11, the moon is behind/above the camera, not visible; its shadow nonetheless falls on the planet ✓ (shadow geometry only depends on moon-sun-planet alignment). Fine!

Hmm wait, that seems off: at transit the moon is between sun and planet: moon az 0.48 ≈ sun az 0.42 ✓, so from the camera at az 0.922 looking at the origin, the sun is off to the... The sun's direction from the camera: sun position = s*800 = (703, 211, 317). Direction from camera (22.8, 6, 29.8): (680, 205, 287) → mostly +x+z — the planet is at direction (-22.8, -6, -29.8). The sun is roughly opposite-ish: looking at the planet, the sun is behind the camera-left. The moon between sun and planet at (39, 6.4, 19.3): from camera that's (16.2, 0.4, -10.5) — behind-right. OK so during the shadow transit the moon itself is out of frame (behind the camera). The eclipse shadow sweeps the planet's visible disc — dramatic, and the moon itself isn't visible at that moment (realistic!). 

Then when is the moon visible in frame? Relative angle: -2.391 + 0.2124t. Moon visible in front hemisphere (relative angle within ±90° of planet direction... roughly |relative| mod 2π < ~40° means near the planet disc): relative crosses 0 at t = 11.3, ±2π at t = (±6.283+2.391)/0.2124 → t = 41.0 or -18.3. Hmm — so relative angle 0 at t=11.3 means moon behind camera?? I computed relative angle as azimuth difference around the origin. When relative azimuth ≈ 0, the moon and camera are on the same side of the planet: the moon (radius 44) is beyond the camera (radius 37.6) on the same ray → the moon is behind the camera. Right. When relative azimuth ≈ π, the moon is on the opposite side → the moon is behind the PLANET (occluded or beside it). So with Rm > camera r, the moon appears in frame when the relative azimuth is ~90° or ~270° (to the side, against the starfield), and near the planet disc when relative ≈ π (behind planet — occultation) — and it can transit across the planet's DISC as a silhouette when?? A far moon crossing behind the planet is occluded; crossing in front requires it between camera and planet, impossible when Rm > cam r... unless the camera radius dips below... camera r min ≈ 34+... at t: r(t) = 34 + 8 e^{-0.12t} + 1.5 sin(0.15t) → min over time as e^{-0.12t}→0: r oscillates 34±1.5 → ~32.5-35.5. Moon at 44 stays outside. OK so the moon will be visible as a small body against the stars when to the side, and disappear behind the planet periodically. Occultation happens when relative azimuth ≈ π and the moon's lateral offset < planet angular radius from that geometry. Let me find when: relative = -2.391 + 0.2124t = π + 2πk → t = (3.1416 + 2.391)/0.2124 = 26.05s (k=0) → at t≈26s the moon passes directly behind the planet — a nice occultation event within the 30s window! And before that, from t≈20-26, the moon visibly approaches the planet's limb and slips behind — great storytelling near the end of the window. And at t≈0-5: relative ≈ -137° → moon to the side/back-left, small in the sky possibly in frame at the edge.

Also I should double check the moon's visibility around t≈26: camera at t=26: θ = 1.591 - 1.633 = -0.042 rad; r = 34 + 8 e^{-3.13} + 1.5 sin(3.9) = 34 + 0.352 - 1.09 = 33.26; y = 4.5 sin(0.11*26 + 0.6) + 2 = 4.5 sin(3.46) + 2 = 4.5*(-0.313) + 2 = 0.59. cam = (33.26 cos(-0.042), 0.59, 33.26 sin(-0.042)) = (33.23, 0.59, -1.40). Moon at t=26: a = -0.80 + 0.1496*26 = 3.09; sin(3.09) = 0.0516, cos = 0.9987 → pos = (43.94, y, 44*0.0516*0.9492 = 2.16); y = -44*0.0516*0.3146 = -0.714. Moon pos (43.94, -0.71, 2.16). Camera→moon: (10.71, -1.3, 3.56); camera→planet: (-33.23, -0.59, 1.40). dot = -355.9 + 0.77 + 4.98 = -350 → dot < 0 → moon behind camera again!! Wait — that contradicts my relative-azimuth logic. Relative azimuth moon-cam = a - θ = 3.09 - (-0.042) = 3.13 ≈ π ✓ — same side of origin along the same line: camera at az -0.042 radius 33; moon at az 3.09 ≈ π - 0.05, radius 44: that's the OPPOSITE side (az differs by π) — I mis-stated: relative azimuth ≈ π means moon az - cam az ≈ 3.09 ≈ π → moon is on the opposite side of the planet from the camera → behind the planet ✓. But then cam→moon direction should pass near the planet: cam (33.23, 0.59, -1.40); moon (43.94, -0.71, 2.16)?? wait recompute: x = 44 cos(3.09) = 44*0.99866 = 43.94 — hmm cos(3.09) is positive?? cos(π - 0.0516) = -cos(0.0516) ≈ -0.9987. Let me redo: 3.09 rad: π = 3.14159, so 3.09 = π - 0.0516. cos(3.09) = -cos(0.0516) = -0.9987; sin(3.09) = sin(0.0516) = 0.0516. So moon pos = (44*(-0.9987), y, 44*0.0516*0.9492) = (-43.94, y, 2.156); y = -44*0.0516*0.3146 = -0.714. Moon pos (-43.94, -0.71, 2.16). Cam (33.23, 0.59, -1.40). cam→moon: (-77.2, -1.3, 3.56); cam→origin: (-33.2, -0.59, 1.40). Same direction ✓ dot = 2564 + 0.77 + 4.98 > 0 ✓. Good — moon behind planet at t≈26. Closest approach of the cam→moon line to origin: b = dot(-cam, D̂): D̂ = (-77.2, -1.3, 3.56)/77.3 = (-0.9987, -0.0168, 0.0461). -C = (-33.23, -0.59, 1.40). dot(-C, D̂) = 33.19 + 0.0099 + 0.0645 = 33.3. Closest point = C + 33.3*D̂ = (33.23 - 33.26, 0.59 - 0.56, -1.40 + 1.535) = (-0.03, 0.03, 0.135) → distance ≈ 0.14 → the moon passes dead-center behind the planet ✓. It will be occluded (planet radius 10; the moon at distance ~77 from camera, planet occludes everything within angular radius atan(10/33.5) ≈ 16.6° of center — the moon's track: lateral offset = 77.3 * sin(angle between D̂ and planet dir)... it crosses through center → hidden for a stretch of time. Angular speed of relative azimuth 0.2124 rad/s → the moon sweeps 2*0.176/0.2124... the occultation lasts while the moon's angular offset from the look axis < ~13-14° (accounting for moon radius): duration ≈ 2*0.245/0.2124 ≈ 2.3s. So the moon disappears behind the planet around t ≈ 24.9–27.2s. 

And the moon approaches: before t=24, where is it? t=20: relative = -2.391 + 4.248 = 1.857 rad = 106° — moon is ~106° off the camera axis — outside frame. Hmm — so the moon is out of frame from t≈15 to t≈24, then briefly disappears behind the planet. When IS the moon nicely visible? Around relative ≈ ±90°+ it's far off-axis. The moon appears within the frame (half-angle ~43° horizontal) when |relative| (mod 2π, as angular distance) ≲ 40°, i.e. relative ∈ (-0.75, 0.75) around 0 → t ∈ ((-0.75+2.391)/0.2124, (0.75+2.391)/0.2124) = (7.7, 14.8). Around t≈8–14: the moon is in front of the camera... at relative ≈ 0 the moon is behind the camera (as computed). Wait I need to be careful: relative azimuth ≈ 0 → same side → moon beyond camera from origin → the moon is behind the camera when looking at the planet. So the moon is in front of the camera (between camera and planet) never (Rm > cam r). The moon appears in the frame when it's to the SIDE: relative ≈ ±90° puts it at the frame edge... Let me think about what the camera sees: camera looks at origin. Objects at radius > camera radius on the opposite side (relative ≈ π) are near the look axis (in front, beyond the planet) — that's the occultation case at t=26. Objects at relative ≈ ±90° are off to the sides at 90° off-axis — outside FOV. Hmm! So with Rm=44 > r_cam, the moon is only ever visible NEAR the planet's limb (when relative ≈ π ± planet angular radius) or further out — wait no: as relative azimuth goes from π-δ to π+δ, the moon crosses behind the planet. When relative = π ± 30°, the moon is 30° off the planet center in the sky, at distance ≈ sqrt(Rm² + r² + 2 Rm r cos30°...) ≈ 75 — angular offset from the look axis ≈ 75*sin(30°)/75 ≈ ... the moon at azimuth offset 30° from the anti-camera direction: its angle from the camera's look axis (which points at origin): the moon direction from camera vs origin direction: angle ≈ atan(lateral/distance)... Let me just compute at t=22: relative = -2.391 + 4.673 = 2.282 rad = 130.7°. Moon az = θ + relative = (1.591 - 1.382) + 2.282 = 0.209 + 2.282 = 2.491?? Let me directly: θ(22) = 1.591 - 0.0628*22 = 1.591 - 1.382 = 0.209. a(22) = -0.80 + 0.1496*22 = 2.491. Moon pos: cos(2.491) = -0.801, sin = 0.598 → x = -35.2, z = 44*0.598*0.9492 = 25.0, y = -44*0.598*0.3146 = -8.28. Moon (-35.2, -8.28, 25.0). Camera: r = 34 + 8 e^{-2.64} + 1.5 sin(3.3) = 34 + 0.571 - 0.216 = 34.36; y = 4.5 sin(0.11*22+0.6)+2 = 4.5 sin(3.02) + 2 = 4.5*0.121 + 2 = 2.54; cam = (34.36 cos0.209, 2.54, 34.36 sin0.209) = (33.62, 2.54, 7.12). cam→moon: (-68.8, -10.8, 17.9) |v| = 72.0 → dir (-0.952, -0.149, 0.247). cam→origin: (-33.62, -2.54, -7.12)/34.4 = (-0.977, -0.0738, -0.207). dot = 0.930 + 0.011 - 0.051 = 0.890 → 27.2° off-axis. So at t=22 the moon is 27° off-axis — within horizontal FOV (43°) but above/below? The offset direction: cross product to determine... roughly the moon is up or down 27°? Vertical half-FOV 27.5° — borderline. Hmm.

This is getting very fiddly. Alternative pragmatic approach: WIDEN the FOV a bit (55–60°) and accept the moon appearing at the edges at times; OR reduce Rm so the moon sometimes comes between camera and planet (in front of the disc — silhouette transit is dramatic). But close approaches to the camera look odd... Actually you know what — real orbital photography of Saturn etc.: moons drift in and out of frame. The requirement just says the moon orbits and casts light/shadow interest. The guaranteed spectacle is: (1) eclipse shadow sweep at t≈9–13 (analytically guaranteed by geometry ✓), (2) the moon visible passing beside/in front of the planet at some point, (3) occultation behind the planet at t≈26. I'll tune so that at t≈16–20 the moon is visibly against the sky near the planet. Let me check t=16: relative = -2.391 + 3.398 = 0.957 rad = 54.8° off-axis — outside 43° half-hFov but close; at t=14: relative = 0.582 = 33° → within horizontal FOV if vertically OK. t=14: moon az = -0.80 + 2.094 = 1.294; cam θ = 1.591 - 0.879 = 0.712. Moon pos: cos(1.294)?? a(14) = -0.80 + 2.094 = 1.294: cos = 0.2726, sin = 0.9621 → x = 12.0, z = 44*0.9621*0.9492 = 40.17, y = -44*0.9621*0.3146 = -13.32. Moon (12.0, -13.3, 40.2). Camera: r = 34 + 8 e^{-1.68} + 1.5 sin(2.1) = 34 + 1.443 + 1.29 = 36.7; y = 4.5 sin(0.11*14 + 0.6) + 2 = 4.5 sin(2.14) + 2 = 4.5*0.842 + 2 = 5.79; cam = (36.7 cos0.712, 5.79, 36.7 sin0.712) = (27.73, 5.79, 23.99). cam→moon: (-15.7, -18.9, 16.2) |v| = 30.4 → (-0.522, -0.626, 0.536). cam→origin: (-27.73, -5.79, -23.99)/36.9 = (-0.751, -0.157, -0.650). dot = 0.392 + 0.0523 - 0.348 = 0.096 → 84.5° off-axis. So at t=14 the moon is way off to the lower-left. Hmm. So the moon passes NEAR the camera (t≈13, dist 8-10!) then swings wide. Wait at t=14 the moon is 84° off axis and 30 units away — it's beside the camera. It's out of frame.

So with these params, the moon is basically NEVER nicely in frame except fleeting moments: near t≈0-4 maybe. t=4: relative = -2.391+0.85 = -1.541 rad; moon az = a(4) - θ... a(4) = -0.80+0.598 = -0.202; moon pos: cos(-0.202) = 0.9797 → x = 43.1; sin = -0.2006 → z = 44*(-0.2006)*0.9492 = -8.38; y = -44*(-0.2006)*0.3146 = 2.78. Moon (43.1, 2.78, -8.38). Camera: θ(4) = 1.591-0.251 = 1.340; r = 34 + 8 e^{-0.48} + 1.5 sin(0.6) = 34 + 4.95 + 0.847 = 39.1; y = 4.5 sin(0.11*4+0.6)+2 = 4.5 sin(1.04)+2 = 4.5*0.862+2 = 5.88; cam = (39.1 cos1.34, 5.88, 39.1 sin1.34) = (8.85, 5.88, 38.1). cam→moon: (34.3, -3.1, -46.5) |v| = 58.1 → (0.532, -0.053, -0.803). cam→origin: (-8.85, -5.88, -38.1)/40.0 = (-0.221, -0.147, -0.952). dot = -0.118 + 0.0284 + 0.906 = 0.938 → 20.2° off-axis! At t=4 the moon is 20° off-axis — visible in frame, distance 58 → angular radius atan(1.5/58) ≈ 1.5° — small but visible. And its lit fraction: moon at az -0.202 (≈ sun az 0.42 - 0.62) — from camera the moon is... fine, it'll be a gibbous/half-lit small moon. 

Hmm OK. Let me step back. Precision-choreographing the moon into frame at specific times via mental math is error-prone. Better: make the FOV a bit wider (58°) and camera radius moderate, and choose the moon closer (Rm = 30, outside rings at 24 — margin 6). With Rm = 30 and camera r ~ 34-39, the moon CAN be between camera and planet when on the camera side (moon radius 30 < cam 34) — it will pass in front of the planet disc (silhouette transit across the disc!) once per relative revolution, and pass behind the planet... no wait: moon radius 30 vs camera 34+: when relative azimuth ≈ 0, the moon is at radius 30 on the camera side: distance from camera ≈ 4-9 → very close to camera, huge in frame, and likely OUTSIDE the planet disc direction... hmm, at relative az 0 the moon is behind the camera or beside it depending on radii. Camera at 36 looking at origin; moon at radius 30 same azimuth: the moon is between camera and planet, 6 units in front of the camera, near the look axis but slightly off (elevation differences). It would appear BIG (angular radius atan(1.5/6) = 14°) crossing the planet disc over ~a few seconds — a dramatic foreground transit! That could be a highlight — a big moon drifting across the planet's face. But it also risks blocking the view during the eclipse shadow... I need the relative timing so the two events don't collide.

Hmm, honestly, maybe simpler: accept whatever the geometry gives, but ensure the moon is IN FRAME at the transit time by construction: place the camera path so that during the eclipse (t≈9-13) the camera is positioned such that the moon is visible near the planet. The moon during transit is on the sun side of the planet at az ≈ 0.48, elevation +4° (y=+4.4, radius 30 → elevation asin(4.4/30) ≈ 8.4°... recompute Rm=30, y=4.37: asin(4.37/30) = 8.4°). If the camera is at az ≈ 0.9 (29° around), looking at the planet: the moon at azimuth 0.48 relative to camera az 0.9 → 25° to the "sun side", above the plane by 8°. The camera is at radius ~37 looking INWARD at the planet — objects on the far side of the planet near the sun direction appear BEYOND the planet in the frame (behind the planet, offset from the planet center by the angular difference between the moon direction and the planet-center direction as seen from the camera). Earlier I computed at t=11 (cam az 0.90, Rm=44): moon direction from camera had dot 0.650 with planet direction → 49° off — but that was with the moon being on the SAME side as... hmm wait I need to redo: at t=11 with Rm=44 the moon was behind the camera. With Rm=30: moon pos at a=0.4806: (30*0.8868, 4.37*30/44... y = -30 sin a sin inc = 30*0.4623*0.3146 = 4.36; x = 26.6; z = 30*0.4623*0.9492 = 13.17. Moon (26.6, 4.36, 13.17). Camera at t=11: cam az 0.922, r ≈ 37.6 (same as before), cam = (37.6*0.6036?? cos(0.922) = 0.6036, sin = 0.7973) → (22.7, 6.3, 30.0). cam→moon: (3.8, -1.94, -16.7), |v| = 17.2 → (0.221, -0.127, -0.971). cam→origin: (-22.8, -6.3, -30.0)/38.0 = (-0.582, -0.165, -0.789). dot = -0.114 + 0.021 + 0.762 = 0.669 → 48° off-axis. Still 48° — the moon is off-frame up/right while its shadow lands on the planet. Because the moon is high above the plane (elevation 8.4°) and 29° in azimuth from the sun direction... the camera looks at the planet; the moon is beyond the planet and to the sun-side, 48° off-axis. Hmm.

OK here's the thing: a moon casting its shadow on the planet is naturally far from the planet in the sky (it's at 30+ units, the shadow alignment tolerance is ~19°) — the moon will be within ~20-40° of the planet center in the sky at most, usually OUTSIDE a tight frame but INSIDE a wide frame. Solution: frame wider! If the camera radius is ~45-55 with FOV 55-60, the planet (r=10) spans ~2*atan(10/48) ≈ 24°, and the moon at 48° off-axis... a 60° hFOV (half 30°)... still marginal.

Alternative: EMBRACE it — the eclipse shadow sweep without the moon in frame is cinematic and realistic (in real eclipse photography you can't always see the moon). The requirement: "a small moon orbiting the planet that casts light and shadow interest" — the eclipse shadow + planet shadow on the moon + the moon appearing periodically satisfies this. I'll also add a subtle secondary light from... no.

Let me also reconsider: maybe make the moon's orbit INCLINED and its radius such that it passes in front of the planet disc from the camera's viewpoint at a predictable time — the "big moon crossing the face" moment. With Rm = 30 and camera r ≈ 36: when relative az ≈ 0 (moon between camera and planet): t=11ish (as computed relative crosses 0 at t≈11.3 for wm=0.1496, θ0=1.591, ωc=-0.0628... wait that was for Rm=44; relative angle doesn't depend on Rm). Hmm — at t≈11.3 the moon is between camera and planet — but ALSO the eclipse happens at t≈11 (moon between sun and planet). Both can't be true simultaneously unless the sun is behind the camera. Sun az 0.42, camera az 0.92 — sun is 29° to the side. The moon can't be both between camera-planet and sun-planet... Actually it can be approximately: the moon at az 0.48, radius 30; camera at az 0.92, radius 37.6: moon-camera-planet: is the moon inside the camera→origin line region? cam→moon dot cam→origin = +0.669 > 0 → the moon is in FRONT (between camera and planet, roughly). And moon-sun-planet: the shadow ray passes 7.05 units from origin (computed earlier for Rm=30 — wait that was with the earlier camera geometry; the shadow geometry depends only on moon pos and sun dir: computed d = 7.05 for a=0.4806... hmm earlier I computed dist = 7.05 for P=(23.07, 6.58, 18.03) — that was for a slightly different inc convention. With current P = (26.6, 4.36, 13.17): P̂·s = (26.6*0.8796 + 4.36*0.2639 + 13.17*0.3958)/30 = (23.40 + 1.151 + 5.213)/30 = 29.76/30 = 0.992 → dist = 30*sqrt(1-0.984) = 30*0.1265 = 3.79 ✓. So at t≈11: the moon is simultaneously (a) between the camera and the planet-ish (48°... no wait, dot 0.669 → 48° off-axis — NOT between camera and planet visually; it's up and to the side). Ugh, my relative-azimuth reasoning conflates azimuth with actual angular offset. The moon at az 0.48 vs camera az 0.92: azimuth difference 25°, elevation of moon 8.4°, camera elevation ~9.6° (y=6.3/37.6). The moon is at radius 30 < camera 37.6 on nearly the same azimuth → the moon is closer to the planet than the camera, off to the side by ~29° azimuth → appears ~29°+ off-axis to the side, NOT in front of the disc. For the moon to cross the disc (relative to the look axis), it needs to be within ~±15° of the cam-origin axis: |az difference| < ~15° AND small elevation difference. Az difference at t: (a(t) - θ(t)) = -2.391 + 0.2124t (from before) — crosses 0 at t = 11.26. At t = 11.26: az diff = 0 → the moon, camera, and origin are co-azimuthal. Moon radius 30 < camera 37.6 → moon between camera and planet, dead on the axis → visible as a silhouette against the planet disc! And the eclipse also peaks at t≈11 — wait, the eclipse peak was set at a* = 0.481 → t = (0.48 + 0.80)/0.1496 = 8.56s. Let me recompute: a(t) = a0 + wm t with a0 = -0.80: a = 0.48 at t = 1.28/0.1496 = 8.56s. And relative az crosses 0 at t = 11.26. So at t=8.6 the shadow peaks (moon between sun and planet at az 0.48); at t=11.3 the moon crosses the camera axis. Camera az at t=8.56: 1.591-0.538 = 1.053 → sun-camera separation 36°. At t=11.26: cam az = 0.884, moon az = a(11.26) = -0.80+1.685 = 0.885 ✓ same azimuth, moon radius 30 between cam 37.5 and planet → silhouette transit of the moon across the planet's face! And the sun is at az 0.42, camera at 0.884: the sun is 27° to the side — the moon at that moment is at azimuth 0.885, radius 30: is it lit from the camera's view? The sun direction from the moon ≈ s; the moon's position relative to the sun: the moon is on the camera side (az 0.885) while the sun is at az 0.42 — the moon's lit hemisphere faces az 0.42/elev 15°; from the camera at az 0.884, the moon appears... phase ≈ half-lit or gibbous? The sun-camera-moon angle: sun dir from origin s=(0.88,0.26,0.40); moon dir from origin m̂ ≈ (0.886, 0.145, 0.439)?? wait moon az 0.885 with elevation: y = -30 sin(a) sin(inc) = 30*sin(0.885)*0.3146 = 30*0.7739*0.3146 = 7.30; horizontal radius = 30 cos(0.885)... hmm no: the orbital param a IS the azimuth in my parametrization (pos = (cos a, 0, sin a) tilted). pos = (30 cos a, 30*0.3146 sin a, 30*0.9492 sin a) → at a = 0.885: (30*0.6347, 7.30, 30*0.7739*0.9492 = 22.03) → m̂ = (0.6347, 0.2433, 0.7343). s·m̂ = 0.5583 + 0.0642 + 0.2907 = 0.913 → sun-moon-origin angle = 24°. From the camera, the moon is 24°... the phase: the angle between the sun direction and the camera→moon direction determines illumination. Camera pos ≈ (37.5 cos0.884, y, 37.5 sin0.884) = (23.96, ~6, 29.07). cam→moon: (19.04-23.96, 7.3-6, 22.03-29.07) = (-4.92, 1.3, -7.04) |v| = 8.3?! The moon is only 8.3 units from the camera — angular radius atan(1.5/8.3) = 10.3° — a BIG moon 10° angular radius crossing the frame near the planet (planet angular radius atan(10/38) = 14.7°). So around t≈11.3, a large moon (20° diameter) sweeps across in front of the planet — very close to the camera — dramatic! And it's roughly half-lit (sun 24° off the moon-planet axis... the phase as seen: since the moon is between camera and planet and the sun is 29° off the camera axis, the moon shows a gibbous phase slightly). Hmm — is this "moon looms huge across the screen" moment good or bad? It could be a spectacular moment: a large cratered moon drifting across the planet's face in 2-3 seconds... but it also might feel like a collision scare, and it would occlude the eclipse shadow at its peak?? The shadow peaks at t=8.56, the moon crosses the frame at t≈11.3 — shadow still on the disc (transit window ~[6.5, 10.6] for γ<0.333: duration 4.1s centered 8.56 → [6.5, 10.6]). Moon near camera: |relative az| < 15° → t ∈ (8.55, 13.97). Overlap [8.55, 10.55] — the big moon partially covers the planet exactly when the shadow is on the visible disc. Hmm, could be visually confusing (shadow visible next to the giant moon silhouette... actually could look AWESOME — like a real eclipse seen from orbit: the moon crossing the disc with its umbra beneath it!). Actually YES — that's the money shot: moon transiting in the foreground while its shadow darkens the planet below it. Physically consistent! But risky if the moon is TOO big/blurry near the camera (at 8 units, with radius 1.5, near-plane issues? Camera near plane 0.1 — fine; the moon lit from behind-camera-ish → mostly dark side facing camera?? phase: sun at 24°... from the camera the moon would appear mostly lit? The sun direction vs camera direction to moon: angle between s and (moon - cam): s·(moon-cam)/|...| = (0.88,0.26,0.40)·(-4.92, 1.3, -7.04)/8.3 = (-3.87 + 0.34 - 2.79)/8.3 = -0.762 → angle 139.6° → the moon is backlit from the camera's view → mostly DARK with a thin crescent!! A big dark moon crossing the lit planet — silhouette transit. Visually striking (dark disc with a glowing crescent rim crossing the daylit planet) — very cinematic. But a mostly-black big disc might read as a glitch... it'll have a thin lit rim (crescent) which reads as a backlit moon. Plus the planet's reflected... nah, keep it simple.

Hmm, I'm spending a lot on choreography. Let me step back and make robust choices:

DESIGN DECISION — simplify to guarantee robustness:
- Moon orbit radius 30 (just outside rings), tilt -0.32 about X, T = 42s (wm = 0.1496).
- Camera: counter-orbiting at ωc = -0.0628 rad/s (opposite sense), radius 36-40 easing from 44, elevation oscillating ±3.
- The relative angular rate 0.212 rad/s gives: moon passes in front (near camera side) around t≈11 and behind the planet around t≈26. Both within 30s ✓.
- Eclipse: set a0 so shadow center crosses closest around t≈8.5-9.

Actually wait — I realize I should double check the eclipse visibility: the shadow falls on the sunlit hemisphere; the camera at separation ~36° from the sun azimuth sees the disc mostly lit ✓. The shadow sweeps across the disc. The moon itself, backlit, crosses as a dark silhouette nearby. This reads as an eclipse sequence. 

But hold on — the moon between camera and planet at radius 30, camera at 37: the moon passes across the LOOK axis once per relative revolution... but also, when relative az ≈ 0 the moon is between camera and planet ONLY if the moon's radius (30) < camera radius (37). And its distance to the camera ≈ 37-30 = 7 along the axis (minus elevation offsets). So it looms. That happens at t≈11.3 each relative period (~29.6s) — also at t≈41, etc. Fine.

One more consideration: when the moon is between camera and planet and backlit, it will also block the sun?? Sun az 0.42 elev 15°, camera az 0.88: the sun is not behind the camera; no issue.

Also, when the moon passes behind the planet (relative az ≈ π at t≈26), it vanishes — and around t≈24-28 it's hidden. Fine.

Alright — but honestly, all these numbers might drift from my mental math due to the radius function etc. The KEY guaranteed moments: (1) eclipse shadow sweep — I can guarantee by construction (shadow geometry independent of camera), (2) starfield/sun/rings always visible, (3) moon does SOMETHING interesting each ~30s. Good enough. Additionally, I'll add the moon's own "cast light" — hmm, "casts light and shadow interest": maybe give the moon a faint cool fill light on the planet's night side? A subtle blue "moonlight" term in the planet shader: light from the moon direction with small intensity, only affecting the night side. That's a nice literal interpretation: moonlight! I'll add: moonLight = moonColor * max(dot(n, normalize(moonPos - fragPos)), 0) * falloff * nightFactor... Actually simpler: directional approximation from moonPos normalized: max(dot(n, normalize(moonPos)), 0) * 0.08 * cool color, added on the night side. And the eclipse shadow darkens BOTH sun and moonlight (moon is the occluder, so during eclipse the moonlight is... the moonlight source is the moon itself — when the fragment is in the moon's shadow ray toward the sun, the moon is between fragment and sun — the moonlight would actually be blocked too (the moon is in the sky there)... over-thinking; keep simple: moonlight term unaffected by moon shadow, or reduce it there. Fine either way; I'll reduce sun only.)

Now the planet spin: rotation.y slow, e.g. 0.02 rad/s → 0.6 rad in 30s (~34°) — visible drift. Clouds: 0.028 rad/s slightly faster + the cloud sphere mesh rotates independently.

Ring plane: rings in the XZ plane (rotated so RingGeometry's XY plane → XZ: rotate mesh -π/2 on X). Planet axis: Y (spin about Y) — aligned with rings (like Saturn). Maybe tilt the whole planet system slightly (like 8°) for dynamism? Tilting the planet's spin axis vs the ring plane would be odd (rings should align with equator). I could tilt the whole system (planet+clouds+rings+moon orbit) by ~10° about Z for a more dynamic composition vs the camera's horizontal drift. Let me put planet+clouds+atmo+rings in a group `planetSystem` rotated z by -0.16 rad (9°) — subtle tilt. Moon orbit tilt already handled separately (I'll put the moon orbit in the same tilted group to keep the eclipse math consistent? The eclipse shadow math uses world-space moonPos and sunDir uniforms — fine regardless). Simpler: keep everything untilted EXCEPT the planet's own rotation axis... you know, the camera already moves vertically; the rings viewed at varying angles give plenty of dynamism. I'll add a mild tilt (0.18 rad) to the whole system group anyway — it makes ring shadows and compositions more interesting. The shaders work in world space for lighting; object space for noise — tilt doesn't break anything since I pass world normals via normalMatrix.

Implementation structure:

```html
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>...</title>
<style> html,body{margin:0;height:100%;overflow:hidden;background:#000} canvas{display:block} </style>
</head>
<body>
<script type="module">
import * as THREE from 'three';

// renderer, scene, camera
// consts
// shaders as template strings with shared GLSL noise chunk
// build planet, clouds, atmosphere, rings, moon, sun, flare overlay, stars, nebula
// resize handler
// animate(t) using rAF timestamp
</script>
</body></html>
```

Shared GLSL: 
```js
const NOISE_GLSL = `...snoise...fbm...`;
```

Planet shader details:

Vertex:
```glsl
varying vec3 vObjPos;   // object-space position (for noise)
varying vec3 vWorldPos;
varying vec3 vNormal;
void main(){
  vObjPos = position;
  vec4 wp = modelMatrix * vec4(position, 1.0);
  vWorldPos = wp.xyz;
  vNormal = normalize(mat3(modelMatrix) * normal);
  gl_Position = projectionMatrix * viewMatrix * wp;
}
```
(Uniform scale so mat3(modelMatrix) ok.)

Fragment:
```glsl
uniform vec3 sunDir;      // normalized, world
uniform vec3 moonPos;     // world
uniform vec3 camPos;      // camera world pos
uniform float time;
varying ...

float fbm(vec3 p){ 5 octaves }

void main(){
  vec3 sp = normalize(vObjPos);
  // elevation
  float cont = fbm(sp*1.35 + vec3(4.2, 1.8, 7.3));
  float det  = fbm(sp*4.5 + vec3(11.0, 5.2, 2.4));
  float h = cont*0.72 + det*0.28;
  float sea = -0.06;
  float landMask = smoothstep(sea, sea+0.045, h);
  // ridged mountains on land
  float ridge = 1.0 - abs(snoise(sp*3.2 + vec3(9.4, 2.2, 5.1)));
  ridge *= ridge;
  h += ridge * 0.28 * landMask * smoothstep(sea+0.02, sea+0.2, h);
  
  // ocean
  float depth = clamp((sea - h)/0.35, 0.0, 1.0);
  vec3 deepCol = vec3(0.008, 0.075, 0.115);
  vec3 midCol  = vec3(0.016, 0.22, 0.26);
  vec3 shoreCol= vec3(0.10, 0.55, 0.47);
  vec3 ocean = mix(shoreCol, deepCol, smoothstep(0.0, 0.35, depth)); // wait direction
```
Hmm: near coast (depth≈0) → shoreCol; deep → deepCol. mix(deep, shore, 1-depth)... Let me write: `vec3 ocean = mix(deepCol, shoreCol, pow(1.0 - depth, 2.2));` roughly.

Land palette (alien): I'll blend by elevation and a "biome" noise:
```glsl
float bio = fbm(sp*2.3 + vec3(23.0, 8.0, 12.0)); // -1..1 approx
vec3 lowlandA = vec3(0.24, 0.26, 0.13);  // mossy olive
vec3 lowlandB = vec3(0.40, 0.22, 0.10);  // rust
vec3 lowland = mix(lowlandA, lowlandB, smoothstep(-0.25, 0.35, bio));
vec3 highland = vec3(0.42, 0.36, 0.27);
vec3 land = mix(lowland, highland, smoothstep(sea+0.06, sea+0.22, h));
land = mix(land, vec3(0.55, 0.52, 0.48), smoothstep(sea+0.24, sea+0.34, h)); // rock
// beaches
float beach = (1.0-landMask) * ... hmm beach band:
vec3 sand = vec3(0.52, 0.44, 0.28);
```
Beach: band where h in [sea-0.008, sea+0.02]: `float beach = smoothstep(sea-0.012, sea, h) * (1.0 - smoothstep(sea, sea+0.02, h));` → apply mix(col, sand, beach*0.85) but only above water... beach appears on land side; underwater near-shore gets shallow color. Fine.

Snow/ice: 
```glsl
float lat = abs(sp.y);
float capNoise = fbm(sp*3.5 + vec3(31.0, 17.0, 4.0));
float cap = smoothstep(0.62, 0.74, lat + capNoise*0.12);
float snowLine = smoothstep(sea+0.22, sea+0.3, h);
float ice = max(cap, snowLine * landMask... also ocean freeze near caps: cap applies over ocean too (sea ice) ✓ since cap independent of landMask.
vec3 iceCol = vec3(0.87, 0.93, 0.97);
// slight blue streaks in ice:
iceCol = mix(iceCol, vec3(0.72, 0.82, 0.90), smoothstep(0.4,0.8, det)*0.35);
```

Base color: `vec3 albedo = mix(ocean, land, landMask); albedo = mix(albedo, iceCol, ice);`

Lighting:
```glsl
vec3 N = normalize(vNormal);
vec3 V = normalize(camPos - vWorldPos);
float NdL = dot(N, sunDir);
float day = clamp(NdL, 0.0, 1.0);
// soft terminator
float diff = day;
vec3 light = vec3(1.0, 0.94, 0.85) * 1.35;  // sun tint
// specular on water
vec3 H = normalize(sunDir + V);
float spec = pow(max(dot(N, H), 0.0), 90.0) * (1.0 - landMask) * (1.0 - ice) * day;
float sheen = pow(max(dot(N,H),0.0), 8.0) * 0.12 * (1.0-landMask);
// moon shadow (eclipse)
float shad = moonShadow(vWorldPos); // 0..1, 1 = lit
// ring shadow
float rshad = ringShadow(vWorldPos, sunDir);
// ambient
vec3 ambient = vec3(0.012, 0.02, 0.028);
// night lights (bioluminescent coasts)
float nightSide = 1.0 - smoothstep(-0.12, 0.12, NdL);
float coast = (1.0 - smoothstep(sea-0.02, sea+0.06, h)) — near sea level both sides;
   restrict to shoreline: coastBand = smoothstep(sea-0.05, sea-0.005, h) * (1.0 - smoothstep(sea+0.005, sea+0.05, h));
float speck = smoothstep(0.45, 0.75, snoise(sp*26.0 + vec3(5.0)));
also larger clusters: smoothstep(0.1, 0.5, snoise(sp*7.0));
vec3 bio = vec3(0.05, 0.85, 0.65) * coastBand * speck * cluster * nightSide * 0.9;
```
Only over ocean (not ice): multiply by (1-ice)*(1-landMask)? Coastline glow should hug the coast on the water side: use coastBand on water side: water coastBand where h slightly below sea. Let me define: `float shelf = smoothstep(sea - 0.06, sea - 0.005, h) * (1.0 - landMask);` → shallow water band. Glow there. Nice: glowing shallows on the night side = bioluminescent plankton. 

Final:
```glsl
vec3 col = albedo * (ambient + light * diff * shad * rshad);
col += (spec + sheen) * sunTint * shad * rshad;
// moonlight (cool fill on night side)
float moonNdL = max(dot(N, normalize(moonPos - vWorldPos)), 0.0);
col += albedo * vec3(0.10, 0.16, 0.22) * moonNdL * 0.5;
col += bio * (1.0 - ice) * ... 
// atmospheric fresnel rim on surface
float fres = pow(1.0 - max(dot(N, V), 0.0), 2.5);
vec3 atmCol = mix(vec3(0.15, 0.45, 0.50), vec3(0.95, 0.55, 0.30), terminatorGlow);
```
Terminator warm tint: `float twil = pow(1.0 - abs(NdL), 6.0) * day-ish`... Let me do: `float rimDay = clamp(NdL*0.5+0.5, 0.0, 1.0); float twilight = exp(-pow((NdL-0.05)*4.0, 2.0));` — a bump around NdL≈0. Then rim color = mix(cyan, orange, twilight). Apply: `col += fres * rimColor * (0.25 + 0.75*day) * shad;` Also the rim should be stronger at grazing → fres term.

Tone: output col; maybe slight tone mapping in shader (renderer default outputColorSpace sRGB with ACES tone mapping — I'll set renderer.toneMapping = ACESFilmicToneMapping and outputColorSpace = SRGBColorSpace; then shaders output linear-ish and three converts? For custom ShaderMaterial, tone mapping isn't automatically applied unless material.toneMapped... ShaderMaterial doesn't include tonemapping chunks automatically. Actually THREE.ShaderMaterial does get `#include <tonemapping_fragment>`? No — ShaderMaterial uses the raw shader; tone mapping chunk is only in built-in materials. I can add `#include <tonemapping_fragment>` and `#include <colorspace_fragment>` manually in my shader — these chunks exist and work in ShaderMaterial as long as I include them at the end of main. Yes, that's a known technique: `gl_FragColor = vec4(col, 1.0); #include <tonemapping_fragment> #include <colorspace_fragment>`. With renderer.toneMapping = ACESFilmic. This gives filmic response for the bright sun. I'll do that for planet, clouds, rings, moon; additive stuff (atmosphere, sun, stars) can also tone map — fine.

Moon shadow function (shared GLSL):
```glsl
float moonShadow(vec3 p){
  vec3 oc = moonPos - p;
  float along = dot(oc, sunDir);
  if(along <= 0.0) return 1.0;  // moon behind
  vec3 closest = p + sunDir*along;
  float d = distance(closest, moonPos);
  float r = 1.7;
  // penumbra: soft edge width relative
  float umbra = smoothstep(r*0.55, r*1.15, d); // 0 in umbra... 
```
Hmm: smoothstep(a,b,d) = 0 when d<a → shadowed. I want shadow factor 1 (lit) when d > r*1.2, 0 when d < r*0.6: `return smoothstep(r*0.5, r*1.3, d);` Actually make the shadow fairly soft: smoothstep(r*0.6, r*1.6, d). Also the true umbra shrinks with distance — ignore. Return that.

Ring shadow on planet:
```glsl
float ringShadow(vec3 p, vec3 sd){
  // ring plane: normal = planetSystem up in world (uniform ringNormal)
  float denom = dot(sd, ringNormal);
  if(abs(denom) < 1e-4) return 1.0;
  float t = -dot(p - ringCenter, ringNormal)/denom;  // ringNormal passes through origin
  if(t <= 0.0) return 1.0;
  vec3 q = p + sd*t;
  float r = distance(q, planetCenter); // origin
  float rn = (r - 15.0)/(26.0-15.0);
  if(rn<0.0||rn>1.0) return 1.0;
  float band = ringBands(rn); // same function as ring alpha, 0..1
  return 1.0 - band*0.55; // shadow strength
}
```
ringBands(rn) — shared noise-based band function:
```glsl
float ringBands(float t){
  // t: 0 inner..1 outer
  float n = fbm1(t*14.0); // 1D noise
  ...
}
```
I'll implement 1D-ish bands using the 3D snoise sampled at (t*scale, 7.7, 3.1) — fine. Band profile: combine a few snoise octaves + smooth window at edges:
```glsl
float ringPattern(float t){
  float v = snoise(vec3(t*22.0, 3.1, 7.7))*0.5
          + snoise(vec3(t*57.0, 9.4, 1.3))*0.25
          + snoise(vec3(t*9.0, 4.4, 2.2))*0.35;
  v = v*0.5+0.5;
  float a = smoothstep(0.05, 0.35, v) ... 
```
Better: alpha = pow(v, 2) etc. I'll tune: `float a = smoothstep(0.35, 0.75, v);` plus fine bands: `a *= 0.6 + 0.4*snoise(vec3(t*140.0, 2.0, 8.0));` plus edge fades: inner fade smoothstep(0.0,0.08,t)*(1-smoothstep(0.92,1.0,t)) and a Cassini-like gap: `a *= 1.0 - 0.85*exp(-pow((t-0.62)*18.0, 2.0));` Nice — a gap division in the rings.

Ring material shader: uses vObjPos (object space XY before rotation? I'll build RingGeometry and rotate the MESH; object-space position has z=0... RingGeometry lies in XY plane. radius = length(position.xy) in object space ✓. Pass world pos for shadow/lighting.

Ring lighting: brightness by |dot(sunDir, ringNormalWorld)| — rings lit more when sun is more perpendicular... For a thin flat ring, illuminated flux ∝ |cos(angle between sun and plane normal)| = |dot(sunDir, N)|. Also viewed: transmitted vs reflected — keep: light = 0.35 + 0.65*abs(dot(sunDir, Nw))... hmm at tilt, dot(sunDir, ringNormal) = s·n where n = tilted up ≈ (sin? ) with tilt 0.18 about Z: n ≈ (−sin0.18? ...) roughly n ≈ (-0.18, 0.98, 0) normalized → s·n = 0.88*(-0.178)+0.264*0.984 = -0.157+0.26 = 0.10 → cos small → rings would be dim. Backlit rings (viewed from unlit side) appear bright due to scattering. I'll just use a pleasing fixed-ish brightness with a forward-scatter boost when the sun is behind the ring relative to the camera: 
```glsl
float back = clamp(dot(V, -sunDir)... 
```
Simplify: brightness = mix(0.45, 1.2, pow(clamp(dot(V, sunDirReflected),0,1), 2))... Let me do: diffuse-ish term = 0.55 + 0.45*abs(dot(Nw, sunDir))*3 clamped... I'll hand-tune: `float li = clamp(0.5 + 1.2*abs(dot(Nw,sunDir)), 0.35, 1.2);` plus planet-shadow multiplication (ringShadow-like planet shadow on rings):
```glsl
float planetShade(vec3 p){
  vec3 oc = -p; float along = dot(oc, sunDir); if(along<=0.) return 1.;
  vec3 c = p + sunDir*along; float d = length(c);
  return smoothstep(9.0, 11.5, d);
}
```
Also moon shadow on rings — skip.

Ring color: icy tan with subtle variation: base vec3(0.45, 0.40, 0.34) modulated by pattern; tint inner region warmer, outer cooler slightly. Alpha = pattern * edge fades * global opacity 0.9. Additive? No — normal transparency with depthWrite false, side DoubleSide. Rendered after planet (renderOrder). Since transparent, three sorts — with depthWrite false and the planet opaque, order: planet (opaque) → clouds (transparent) → atmosphere (additive back side) → rings (transparent) → moon opaque. Transparent objects sorted by distance; renderOrder can enforce. Potential issue: clouds behind rings... sorting handles per-object; artifacts acceptable. I'll set renderOrder: atmosphere 1, clouds 2, rings 3? Hmm — atmosphere (backside sphere at 1.07R) surrounds the planet; clouds at 1.03R. When looking at the planet, atmosphere surface is behind the clouds front... additive blending order matters little (additive is commutative with normal blending? Not exactly, but visually fine). I'll set clouds renderOrder 1, atmosphere 2, rings 3.

Cloud shader:
```glsl
// object-space normalized pos (rotates with cloud mesh)
float cfbm = fbm(sp*3.0 + vec3(time*0.01...)) // slow evolution via time offset in noise domain
float clouds = smoothstep(0.12, 0.42, cfbm + 0.15*fbm(sp*9.0));
// falloff at poles? maybe swirl: sample with domain warp:
vec3 q = sp*2.6; q += 0.35*vec3(fbm(sp*4.0+7.0), fbm(sp*4.0+13.0), fbm(sp*4.0+29.0)); // expensive: 3 fbm... use cheaper warp: q.xz rotated by fbm
```
Keep cost moderate: warp with one fbm: rotate sp around Y by angle = 0.6*fbm(sp*3.0 + t*0.02): 
```glsl
float ang = 1.2*fbm(sp*2.2 + vec3(0.0, time*0.015, 0.0));
// rotate sp.xz by ang
mat2 R = mat2(cos(ang), -sin(ang), sin(ang), cos(ang));
vec3 q = sp; q.xz = R * q.xz;
float d1 = fbm(q*3.2 + vec3(3.7, 1.2, 8.4));
float d2 = fbm(q*8.0 + vec3(15.0, 6.0, 3.0));
float cover = smoothstep(0.05, 0.55, d1*0.75 + d2*0.35 + 0.12);
```
Lighting: NdotL soft, plus silver lining? Keep: col = mix(shadowColor(0.2,0.24,0.3 tinted dark blue), bright(1.05 white-slightly warm), day). Alpha = cover * (0.85) * limb... Also fade clouds at the very limb? The atmosphere covers. Alpha near terminator: clouds stay visible dark on night side (alpha constant, color dark). Also clouds should catch ring shadow? Skip for clouds (cost) — actually include planet shadow from rings? Rings shadow on clouds: same ringShadow func — it's cheap-ish (needs ringPattern = few snoise). Include for consistency ✓ (the shadow band across clouds is a nice detail).

Also clouds receive moon shadow (eclipse darkens clouds too) — include moonShadow ✓ (shared func).

Cloud alpha also modulated by a subtle "coverage band" near equator? Not needed.

Atmosphere shader (glow shell):
```glsl
side: BackSide, blending: AdditiveBlending, transparent: true, depthWrite: false
varying vNormal (world), vWorldPos
fragment:
vec3 V = normalize(camPos - vWorldPos);
float rim = pow(1.0 - abs(dot(V, normalize(vNormal))) ... for BackSide sphere, the normal faces away; intensity = pow(dot(...)) careful.
```
Standard trick: for BackSide-rendered sphere of radius R2 > R: fragment normal points outward; dot(V, N) is negative-ish for the shell seen from outside... Let me think: BackSide renders the far hemisphere (inside faces). For a point on the back hemisphere, its normal points away from the camera roughly: dot(V, N) where V = toward camera: negative. glow = pow(clamp(dot(V, -N)... Classic atmosphere: intensity = pow(0.62 - dot(V, N), 2) etc. I'll use the robust formulation: compute the "height" through the shell: use the dot of the view ray with the sphere... Simplest reliable: rim = pow(1.0 + dot(V, N), p) for backside (dot ranges -1..?): hmm.

Let me use a cleaner physical-ish approach: For the atmosphere shell, compute per-fragment: the angle between the view ray and the normal at the point where... Actually the common "glow" shader: 
```glsl
float intensity = pow(0.55 - dot(vNormal, vec3(0,0,1.0)), 2.0); // view-space normal
```
That's the old three.js glow example (view-space normal z). For BackSide sphere, at the limb the view-space normal z ≈ ... For the far side fragments near the silhouette edge, normal is perpendicular to view (z≈0) → 0.55^2; at the center of the back face, normal z ≈ -1 → (0.55+1)^2 big?? Hmm that gives max at center — wrong. Let me instead compute analytically:

Use world positions: ray from camera through fragment; the shell sphere center origin radius R2. For atmosphere glow, I want intensity that peaks just at the planet's limb and fades outward to the shell edge. Parameter: the fragment's distance from the "planet edge" as seen... Easier: compute using the normal and view: for the back hemisphere of the shell, define d = distance from view ray to planet center (impact parameter). This can be computed: ray origin C (camPos), direction D = normalize(vWorldPos - C). Impact parameter b = length(cross(D, -C))... = length(C - D*dot(C,D))?? b = sqrt(dot(C,C) - dot(C,D)^2)... For points on the shell's back hemisphere along the ray, b is constant per ray ✓. glow intensity = f(b): strong when b ≈ planetR (limb), fading as b → shellR. And fade inside b < planetR (occluded by planet anyway — but the back shell behind the planet is occluded by the planet's depth ✓ since planet is opaque and closer... wait the back shell is BEHIND the planet (farther), so planet occludes it ✓. But the shell's front hemisphere is culled (BackSide). So visible glow only in the annulus between limb and shell edge ✓ plus behind-planet parts hidden by depth ✓. 

So: b = length(C - D*dot(C, -C))... compute: t_ca = -dot(C, D) (projection of -C on D); closest = C + D*t_ca; b = length(closest). Then:
```glsl
float x = clamp((b - planetR) / (shellR - planetR), 0.0, 1.0); // 0 at limb, 1 at outer edge
float glow = pow(1.0 - x, 2.6) * 1.4;  // falls off outward
```
Also fade where b < planetR (behind planet — occluded anyway). Also day/night modulation: sun illuminates the atmosphere: at the closest point direction dirN = normalize(closest) (radial direction at limb); dayFactor = clamp(dot(dirN, sunDir)*0.7+0.3, 0, 1)? And sunset tint near terminator: twil = exp(-pow(dot(dirN, sunDir)*3.0, 2.0)) → orange boost. Color = mix(cyanBlue, warmOrange, twil*0.85) * glow * (0.25 + day). Also forward-scatter: when camera looks toward the sun through the atmosphere, brighten: fwd = pow(max(dot(-D... the view direction D points away from camera; forward scattering toward the sun: max(dot(D, sunDir), 0)^3 * boost — that brightens the whole sky-shell when the sun is in frame behind the planet — nice sun-lit haze ring near the sun side. Keep modest.

Since b is constant along the ray, the glow is a smooth annulus ✓. This is a much better approach than fresnel-normal hacks and looks genuinely atmospheric. Also add a subtle inner atmosphere on the planet surface (done via fresnel in planet shader).

Similarly, I could use the same shell technique... good.

Moon shader:
```glsl
uniform sunDir, moonPos(unused), camPos
sp = normalize(vObjPos) — moon rotates slowly? Keep static or rotate mesh slowly.
float n = fbm(sp*4.0)*0.5+0.5; float n2 = fbm(sp*12.0)*0.5+0.5;
// crater-ish: rings around points — cheap: craters = smoothstep pattern from snoise cells... keep mottled albedo:
vec3 albedo = mix(vec3(0.30,0.28,0.26), vec3(0.5,0.47,0.44), n) ; darker maria: mix with vec3(0.16,0.16,0.18) by smoothstep(0.55,0.8, fbm(sp*1.8+31.))
// lambert + tiny ambient
float d = max(dot(N, sunDir), 0.0);
// eclipse: planet shadow on moon
float psh = planetShadow(vWorldPos); // smoothstep(9.6, 11.5, d_closest) — softer penumbra since sun has angular size... use smoothstep(planetR*0.92, planetR*1.35, d)
// crescent look is automatic from lambert.
col = albedo*(vec3(1.0,0.95,0.88)*1.25*d*psh + ambient(0.01..)) + albedo*coolMoonFill*0.05
```

Sun billboard shader: plane facing camera. I'll use THREE.Sprite? Sprite requires SpriteMaterial (no custom shader). Instead: a mesh with PlaneGeometry(1,1) and onBeforeRender orient toward camera, or simplest: in vertex shader, billboard: transform a unit quad in view space: position = camPos + right*px + up*py... Standard trick:
```glsl
// vertex
vec3 center = sunPos; // uniform or attribute — I'll place mesh at sun world pos and use model matrix position
vec4 mv = modelViewMatrix * vec4(0.0,0.0,0.0,1.0); // center in view space
mv.xy += position.xy * scale; // scale via uniform or mesh.scale
gl_Position = projectionMatrix * mv;
```
This billboards the quad in view space ✓. Set mesh.position = sunDir*820, geometry PlaneGeometry(2,2) → size in world units at that distance... view-space offset by position*scale — scale via mesh.scale (modelMatrix includes scale — but I'm ignoring model matrix except translation... modelViewMatrix * vec4(0,0,0,1) includes translation+rotation of the mesh — good, center in view space; then add position.xy * meshScale — but `position` attribute is the local quad (-1..1); scale: multiply by uniform uScale (world units). At distance ~740 with size 110 world units → angular size ≈ 110/800 ≈ 0.1375 rad ≈ 7.9° — reasonable big glow. The core should be small (1-2°) with a large soft halo.

Sun fragment:
```glsl
vec2 uv = vUv*2.0-1.0; float r = length(uv);
float core = exp(-r*r*38.0);
float halo = exp(-r*r*3.2)*0.55;
float streakH = exp(-abs(uv.y)*30.0) * exp(-abs(uv.x)*2.4)*0.5; // horizontal flare line
float streakV = exp(-abs(uv.x)*30.0) * exp(-abs(uv.y)*3.0)*0.28;
vec3 col = sunTint*(core*2.2 + halo) + warm*(streakH+streakV);
gl_FragColor = vec4(col, 1.0) with additive blending, toneMapped
```
depthWrite false, depthTest true → planet occludes the far sun ✓. transparent true (additive). renderOrder late.

Lens flare overlay (screen-space): I'll create `flareScene` + ortho camera; elements:
- Big soft halo centered on sun screen pos (a radial gradient disc, additive, subtle) — same position as sun.
- Ghosts: 4-6 circles at positions along the line through screen center: p_i = sunNDC * (-k_i). Each: soft disc + thin ring edge, hue varies (teal, amber, violet-ish muted).
- Fade factor: vis = occlusion * onScreenFactor. Compute in JS per frame.
Sizes in aspect-corrected units. Ortho camera: left -a, right a, top 1, bottom -1 where a = W/H. Circle geometry radius 1 scaled.

Ghost shader (one material reused with per-mesh uniform color/size? Meshes can't share uniforms unless same material instance — I'll clone material per ghost with different uniforms, cheap.)

Ghost fragment:
```glsl
float r = length(vUv-0.5)*2.0;
float disc = smoothstep(1.0, 0.35, r);
float ring = smoothstep(0.12, 0.0, abs(r-0.82)) * 0.8;
float a = (disc*0.5 + ring) * intensity;
gl_FragColor = vec4(tint*a, a)? with additive blending: vec4(tint*intensity*(disc*0.35+ring), 1.0) — additive uses rgb; set blending Additive, and premultiply: col = tint * (disc*0.4+ring*0.7)*uIntensity.
```
Also add subtle radial rainbow tint on the main halo? Keep simple.

Also a horizontal anamorphic streak in overlay at sun position: a wide thin quad with exp falloff — the sun billboard already has streaks in world space; screen-space streak follows the sun's NDC even when partially occluded... keep world-space only, fine.

Occlusion & visibility computed in JS:
```js
const camToSun = sunPos.clone().sub(camera.position);
const dist = camToSun.length();
const dir = camToSun.clone().normalize();
// closest approach to planet center (0,0,0)
const tClose = -camera.position.dot(dir);  // wait: b = dot(-C, D)
let occluded = 0;
if (tClose > 0 && tClose < dist) {
  const closest = camera.position.clone().addScaledVector(dir, tClose);
  const b = closest.length();
  occluded = 1 - THREE.MathUtils.smoothstep(b, planetR*0.85, planetR*1.25); // 1 when b small
}
// off-screen fade based on sun NDC
const ndc = sunPos.clone().project(camera); // careful: project uses matrices — fine after camera updated
const edgeFade = smoothstep-ish on max(|ndc.x|/0.9?, |ndc.y|) → fade between 0.9 and 1.4...
```
Hmm — but if the sun is occluded by the planet, its NDC is still computed (projection of the sun position) — ghosts should also fade with occlusion ✓ multiply both.

Also: sun behind camera → ndc flips; check dot(camera.getWorldDirection(), dir) > 0 else vis = 0.

Flare visibility = (1-occluded) * edgeFade * facingFactor. Multiply sun billboard material opacity too (so the sun fades smoothly at the limb rather than popping) — but depthTest already hides it when behind; combining gives soft edges: set uOpacity = 0.25 + 0.75*(1-occluded)? If fully occluded, depthTest hides the core anyway; the halo part extends beyond the limb and would show — fading via opacity is good.

Starfield: Points shader:
```glsl
attribute float aSize; attribute vec3 aColor; attribute float aPhase;
varying...
gl_PointSize = aSize * uPixelRatio * (some factor) — fixed sizes fine: size in px 1..3.5, few larger 4-5.
fragment: d = length(gl_PointCoord-0.5)*2; alpha = smoothstep(1.0, 0.0, d); soft; twinkle = 0.75+0.25*sin(uTime*aTwSpeed + aPhase);
```
Additive blending, depthWrite false. Star colors: mostly white, some blue-white, some warm; a few tinted teal/orange for alien sky.

Also maybe a very subtle Milky-Way band? The nebula shader can include a band: density higher along a great circle tilted — nice alien sky. Nebula shader: 
```glsl
vDir = normalize(vObjPos) (object space of the big sphere, static);
float n = fbm(v*3.0) etc; band = exp(-pow(dot(v, bandNormal), 2.0)*8.0);
col = deepBase(0.004..) + band * (teal + faint magenta) * noise...
```
Keep brightness ≤ 0.06 so stars pop. BackSide sphere radius 2200, fog no. depthWrite false, renderOrder -3; stars renderOrder -1... stars are at radius ~1600-1900 (inside nebula sphere 2200 ✓).

Star sizes: with perspective, Points at distance 1600-1900 — gl_PointSize fixed in pixels: fine.

Camera drift implementation:
```js
function updateCamera(t){
  const az = CAM_AZ0 - CAM_W*t;
  const r = 36 - 7*Math.exp(-0.10*t) + 1.6*Math.sin(0.13*t);
  const y = 2.2 + 4.2*Math.sin(0.09*t + 0.7);
  camera.position.set(Math.cos(az)*r, y, Math.sin(az)*r);
  camera.lookAt(0, 0.5, 0); // slight offset
}
```
lookAt each frame (camera.up default Y). The look target maybe drifts slightly: lookAt(sin(t*0.05)*1.2, sin(t*0.043)*0.8, 0) — subtle.

Wait — check opening framing: t=0: az = 1.59, r = 36+7+0 = 43, y = 2.2+4.2*sin(0.7)=2.2+2.71=4.91. Planet at origin radius 10, rings to 26. Distance 43 → rings (26) angular 2*atan(26/43) = 62.5° > hFOV? FOV 55 vertical, aspect 16:9 → hFOV = 2*atan(tan(27.5°)*1.78) = 2*atan(0.926) = 85.6°. Rings fit horizontally easily. Good. Planet ~26° wide — centerpiece. Moon at t=0 is behind the planet (occluded) — hmm, opening without moon visible; it slips out around... relative az = -2.391+0.2124t; planet occludes moon when the cam→moon ray passes within ~10 of origin. Rough: moon angular offset from anti-camera direction: at t=0 that's |relative az| = 137° → offset from π is 43° → lateral distance from planet center as seen... the moon at radius 30 (Rm=30 now) behind the planet: perpendicular distance from origin of the cam→moon line ≈ Rm*sin(π - relAz... roughly the impact parameter ≈ Rm*sin(|π - relativeAz|)... = 30*sin(43°) = 20.5 > 10 → NOT occluded at t=0. Good — the moon is visible at t=0 to the side of the planet (behind it, 43° off), distance from cam ≈ sqrt(30²+43²+...) ≈ 65ish. Angular offset from look axis ≈ 43°*ish → borderline at the frame edge horizontally (hFOV half = 43°). Hmm — borderline. Then the moon moves: relative az increases toward π (t≈26 occultation center: relative az = π → wait relative crosses π at t=26: yes occultation around t≈24.5-27.5). And approaches front at t≈11. Between t=0 and t=11, relative az goes -137° → 0: the moon sweeps from behind-left, around... hmm relative az from -2.391 rad increasing to 0 at t=11.26: the moon's azimuth relative to camera: at -2.39 the moon is nearly behind the planet (43° off); as it increases toward -π/2 (t≈3.4): moon 90° to the side — out of frame; then toward 0: comes around to the camera side... Wait — increasing relative az from -2.391 → -π/2 (t=3.37) → 0 (t=11.26): the moon moves from "behind-left" around through "side" to "same azimuth as camera" (in front). So it's out of frame t≈2-9, then sweeps in toward the camera, becoming the big silhouette crossing near t≈11-13. Then t≈13-24: recedes out to the side (relative 0.33→2.7 rad... at t=24: relative = -2.391+5.1 = 2.71 rad = 155° → approaching behind the planet; visible beside the planet maybe at 20-40° off axis when? relative az from 90° (t=15.5) to 155° (t=24): angular offset from the look axis ≈ relative az - π for behind-ish positions... hmm for relative az > 90°, the moon is beyond the planet; its angular offset from the look axis ≈ π - relativeAz... no: the moon direction from the camera ≈ direction to a point at azimuth θ+relative, radius 30 vs camera at radius ~36 pointing at origin. When relative = 155°, the moon is 25° from dead-behind (az-wise) → angular offset from look axis ≈ 25°*(Rm/(Rm+...)) ≈ 25*0.45?? Let me estimate properly at t=20: relative = -2.391 + 5.098 = 2.71 rad = 155.2°. moon az = θ(24?) — take t=24: θ = 1.591-1.507 = 0.084; a = -0.80+0.1496*24 = 2.79; relative = 2.71 ✓. Moon pos: (30cos2.79, y, 30 sin2.79*0.9492): cos2.79 = -0.942, sin = 0.335 → x = -28.3, z = 30*0.335*0.9492 = 9.54, y = -30*0.335*0.3146 = -3.16. Moon (-28.3, -3.16, 9.54). Camera at t=24: r = 36 - 7 e^{-2.4} + 1.6 sin(3.12) = 36 - 0.633 + 0.108 = 35.5; y = 2.2 + 4.2 sin(0.09*24+0.7) = 2.2 + 4.2 sin(2.86) = 2.2 + 4.2*0.284 = 3.39; az 0.08: cam = (35.5*0.9968, 3.16... y=3.39, z = 35.5*0.0799 = 2.84) → (35.39, 3.19, 2.84). cam→moon: (-63.7, -6.35, 6.7) |v| = 64.4 → dir (-0.989, -0.094, 0.104). cam→origin: (-35.4, -3.19, -2.84)/35.6 = (-0.994, -0.0896, -0.0798). dot = 0.983 + 0.0084 - 0.0083 = 0.968 → 14.5° off-axis → the moon IS in frame at t=24, near the planet (planet angular radius atan(10/35.6) = 15.7°) → the moon is right at the planet's limb approaching occultation. So t≈20-26: the moon drifts toward the planet and passes behind — visible near the limb ✓. And angular radius atan(1.5/64) ≈ 1.3° — small moon ✓ ("small moon" ✓).

And the eclipse silhouette crossing at t≈11-13 with the big dark moon — dramatic ✓. Let me double check the moon is lit as a thin crescent then (sun-camera-moon angle ~140° → mostly dark, thin lit rim) — a dark moon against the bright planet reads clearly ✓. Also its shadow on the planet: at t=11, shadow center distance from origin: compute γ: a(11) = -0.80+1.6456 = 0.8456. cos γ = 0.8796*cos(0.8456) + 0.4587*sin(0.8456) = 0.8796*0.6631 + 0.4587*0.7485 = 0.5833 + 0.3433 = 0.9266 → γ = 0.385 rad → shadow distance from planet center = Rm... wait the perpendicular distance from origin to the shadow ray = Rm * sin γ = 30*0.3753 = 11.26 — OUTSIDE the planet (10)! At t=11 the shadow has already left the disc! Hmm. Let me recompute the shadow timing: shadow distance d(t) = Rm*sqrt(1 - cos²γ(a(t))). cosγ(a) = 0.8796 cos a + 0.4587 sin a (with inc=-0.32 — wait, is this cos γ formula still right for Rm=30? Yes, depends only on direction). Max cosγ = 0.992 at a* = atan2(0.4587, 0.8796) = 0.4800. d(a*) = 30*sqrt(1-0.98406) = 30*0.1262 = 3.79 ✓ (shadow passes 3.79 from center — on the disc). a(t) = -0.80+0.1496t = 0.48 → t = 8.56s ✓. Shadow on disc while d < ~10 (minus shadow radius ~1.7 soft) → cosγ > sqrt(1-(11/30)²) = sqrt(1-0.1344) = 0.9304 → γ < 0.3757. γ(a) = |a - 0.48| approximately near peak (since dγ/da ≈ 0.992 ≈ 1). So |a - 0.48| < 0.375 → a ∈ (0.105, 0.855) → t ∈ ((0.105+0.80)/0.1496, (0.855+0.80)/0.1496) = (6.05, 11.06). So the shadow crosses the disc t ∈ [6.1, 11.1], peak at 8.6s ✓. And the big silhouette moon crossing the frame t≈9-13. So the sequence: shadow sweeps (6-11s), moon silhouette crosses (9-13s) — overlapping — dramatic! The moon (dark, backlit) crossing the disc while its umbra is on the disc — physically consistent: umbra should be UNDER the moon from the camera's view (the shadow is where the moon blocks the sun — from the camera, the shadow region is near the moon's position projected on the planet — roughly aligned ✓ since the geometry aligns camera-moon-planet at t≈11.3 when relative az = 0 — and the shadow leaves at 11.06 — very close! So at t≈11 the moon crosses the limb/edge of the disc with its shadow just leaving — beautiful. Actually hmm, at relative az = 0 (t=11.26) the moon is exactly on the cam-planet axis at radius 30 — distance from camera 7.6-ish → the moon appears at the CENTER of the planet disc, huge (angular radius atan(1.5/7.6) = 11°, vs planet 15°!). A giant dark moon covering 1/3 of the planet's face — with the sun 29° to the side, the moon's lit crescent faces 24°+ off... the moon will appear as a dark disc with a lit rim on the sun side. That's a dramatic "eclipse over the planet" composition. OK — I'll accept it; it should look striking. One risk: the moon very close to the camera might clip through... distance 8.3 at closest, camera near plane 0.1 ✓ fine.

Hmm wait, actually let me double-check the closest camera-moon distance: camera radius r(t) at t=11: r = 36 - 7 e^{-1.1} + 1.6 sin(1.43) = 36 - 2.39 + 1.59 = 35.2. Moon radius 30, relative az at t=11.26 = 0 → distance along axis ≈ 5.5 + elevation differences. Camera y at t=11.26: 2.2+4.2 sin(0.09*11.26+0.7) = 2.2+4.2 sin(1.713) = 2.2+4.19 = 6.39. Moon y at a=0.885: 30*0.3146*sin(0.885) = 9.43*0.774 = 7.30. Δy = 0.9. So distance ≈ sqrt(5.5² + 0.9² + tiny) ≈ 5.6?! Even closer. Angular radius atan(1.5/5.6) = 15° — the moon's disc is as big as the planet's (14.6°)! It would fill the center of the frame... hmm, that's very dramatic — maybe TOO much: a featureless dark disc covering the middle of the frame for ~3 seconds. With crescent rim lighting + noise texture it could be fine, but risk of looking like a black blob. Mitigation options:
(a) Increase moon orbit radius to 40: then moon never comes closer than 40-36=4?? No wait — closer radii difference: with Rm=40 and camera r≈35.5: moon at 40 > camera 35.5 → the moon is beyond the camera's orbit → when relative az = 0, the moon is BEHIND the camera (not visible). Then the moon never looms. And the "in front of planet disc" silhouette can't happen (moon farther than camera along the axis... when relative az = 0 and Rm > r_cam, moon is behind camera). Occultation behind the planet still happens at relative az = π. And eclipse shadow still works. The moon visible: passing beside the planet at moderate offsets.
(b) Keep Rm=30 but change camera radius to stay > 40? Camera 40-44: then the moon (30) is always inside the camera orbit → when relative az = 0, the moon is between camera and planet at distance ≈ 40-30 = 10 → angular radius atan(1.5/10) = 8.5° — a prominent but not overwhelming moon crossing the disc. That's the sweet spot! Camera radius ~40±2, moon orbit 30, moon radius 1.5 → the foreground transit shows a moon ~17° across vs planet ~28° across. 

Let me redo camera: r(t) = 40 - 5 e^{-0.09t} + 1.4 sin(0.11t) → t=0: 45... hmm starting at 45 makes the planet small (24° planet + rings fit nicely at 45? rings 26 → 2*atan(26/45) = 60° fits in hFOV 85 ✓; planet 2*atan(10/45) = 25°). Opening at 45 wide, settling to ~40. OK.

Recompute eclipse/moon events with camera r ≈ 40: relative az timeline unchanged. Moon at relative az 0 (t≈11.3): cam-moon distance ≈ 40-30 = 10 (+offsets) → moon angular radius ≈ 8°. Planet angular radius atan(10/40) = 14°. Moon crosses the disc center, ~55% of the planet's diameter — dramatic but reasonable. Good.

Also check: does the moon pass through the RINGS visually? Moon orbit radius 30 tilted 0.32 rad... the orbit is a circle of radius 30 tilted about the X axis — its closest approach to the ring plane is y=0 at a=0, π — the moon crosses the ring plane at radius 30 (outside rings' outer edge 26) ✓ no visual clipping through rings. 

Moon orbit tilt direction: rotating about X by inc: moon goes +y when sin a > 0 (since inc negative... y = -Rm sin a sin(inc) with inc=-0.32 → y = +Rm*0.3146 sin a). At a≈0.48 (transit) moon y = +4.4 (above plane). Camera y ≈ 6.4 — similar height ✓ looks natural.

Sun elevation: sunDir y-component 0.264 — sun 15° above the ring plane. Rings nearly edge-on from the camera when camera y is low... camera y oscillates 2.2±4.2 → from -2 to 6.4; at distance 40, ring plane viewed from elevation atan(y/40) ≈ -3° to 9° — rings appear as thin ellipses to ~10° — quite edge-on, elegant. With the system tilt 0.18 rad (10°) the apparent tilt varies more. Hmm — the planetSystem tilt: I'll tilt about the Z axis by -0.18 rad. Then the ring plane normal tilts. The camera orbit is horizontal; combined with camera y oscillation, the rings will show nicely. OK.

Wait — but if the ring plane is tilted about Z by -0.18, the sun at az 0.42 elevation 15° relative to the ring plane changes: the tilt changes the effective elevation of the sun relative to the rings... The ring shadow on the planet and the planet shadow on the rings all computed in world space analytically, so all consistent ✓.

But one more check — the planet shadow ON the rings: the rings extend to 26; the planet (radius 10) at origin casts a shadow cone along -sunDir. The shadow lands on the ring on the anti-sun side: at radius where the ring is behind the planet: the shadow region on the ring plane: points q on the plane with distance from the -sunDir axis through origin < 10 → the shadow is an ellipse on the ring plane. Since the sun is 15° above the plane, the shadow is long and thin, extending anti-sunward from behind the planet out to radius... the shadow covers ring radii from ~10 (behind planet) out to where? The shadow band on the plane: points q = p_plane where distance to the line {origin + t*(-sunDir)} < 10. On the ring plane, the anti-sun azimuth direction: the shadow extends to infinity along -sunDir projected... the ray from origin along -sunDir hits the ring plane (y=0-ish) at t where y-component: -sunDir_y*t = 0 → t=0?? The axis passes THROUGH the origin which is on the ring plane — so the shadow axis lies... the shadow of a sphere with the sun 15° above the plane: the shadow cylinder (radius 10 along -sunDir) intersects the ring plane in a long region starting behind the planet extending anti-sunward, since the cylinder axis is tilted 15° from the plane, the cylinder exits the plane... the cylinder of radius 10 around the axis: points on the plane within horizontal distance sqrt(100 - (d_y)²)... the shadow on the plane extends from the planet out to distance ≈ 10/tan(15°) ≈ 37 along the anti-sun azimuth — so the shadow covers the ring from r≈10 out to r≈37 on the anti-sun side, narrowing. Rings extend to 26 → the shadow band will visibly cut across the rings on the night side ✓ — a classic Saturn look. The analytic planetShadow function handles it ✓.

Ring brightness when in planet shadow → dark ✓.

Now — also the moon enters the planet's shadow (lunar eclipse) when it's behind the planet near relative az π (t≈26): the moon passes through the shadow → dims to a deep red? I'll add: in moon shader, when in planet shadow, tint toward dark rusty red (like lunar eclipses): `col = mix(col*vec3(0.10,0.06,0.05)+vec3(0.08,0.03,0.02)*d?, ...)`. Implement: eclipseFactor = planetShadow(); lit = d * eclipse; plus a residual red glow: col += albedo * vec3(0.35, 0.12, 0.06) * (1-eclipse) * d * 0.6 — refracted sunlight tint. Nice touch, happens at t≈25-27 in the window ✓.

Alright. Also "dense starfield" — 7000 stars ✓.

Post-processing: none (keep single-pass). ACES tone mapping in shaders via includes.

Renderer: antialias true, setPixelRatio(min(devicePixelRatio, 2)).

Now, colors & art direction: deep space near-black with a hint of blue-green nebula; sun warm white; planet: teal ocean, olive/rust land, white caps, cyan atmosphere with orange terminator; rings: sandy gray with warm tint; moon: gray. Night side bioluminescent teal coastlines. This palette is cohesive (teal-cyan + rust-amber complementary). 

Sun tint: slightly warm — vec3(1.0, 0.85, 0.62)? And light color for the planet: vec3(1.0, 0.93, 0.82).

Let me also add a subtle vignette? Could do via a fullscreen post overlay — skip, tone mapping + composition enough. Actually a cheap vignette: a fullscreen triangle with radial darkening drawn last with normal blending — adds polish. Hmm, additive scenes... a vignette overlay quad in the flare ortho scene drawn last: radial darkening at corners: color = black with alpha = smoothstep(0.55→1.1 of radius)*0.35. With blending normal (SrcAlpha, OneMinusSrcAlpha). That's tasteful. I'll include it in the flare overlay pass (flareScene renders after main). But careful: the flare overlay uses additive blending for ghosts; vignette uses normal blending with black — fine, separate material.

Also film grain? Skip.

Let me also handle: `camera.lookAt` with the system tilt — the planet is at origin; fine.

Sun position: sunDir = normalize(1, 0.28, 0.44) → I'll place the sun visual at sunDir * 900. Starfield radius 1900-2600?? Camera far plane must cover: far = 6000. Nebula sphere radius 2600... camera far 6000. Stars at ~1800. Sun at 900 with quad size ~150.

The sun's world position is FIXED (directional light). Lens flare ghosts computed from its projection ✓.

Note: since the camera orbits, the sun sometimes goes behind the planet — handled.

One more requirement detail: "Use the requestAnimationFrame timestamp for animation time" — animate(tms) with `const t = ts * 0.001`. Also handle the tab being backgrounded: t continues monotonic — fine, everything is a function of t (moon position, camera, rotations, noise time). No accumulation → robust ✓.

Resize: update camera.aspect, renderer.setSize, and the flare ortho camera's aspect + uniforms. Also uPixelRatio for star size.

Let me now write all the shaders carefully.

Common GLSL chunk (noise):

```glsl
vec3 mod289(vec3 x){return x - floor(x*(1.0/289.0))*289.0;}
vec4 mod289(vec4 x){return x - floor(x*(1.0/289.0))*289.0;}
vec4 permute(vec4 x){return mod289(((x*34.0)+1.0)*x);}
vec4 taylorInvSqrt(vec4 r){return 1.79284291400159 - 0.85373472095314*r;}
float snoise(vec3 v){
  const vec2 C = vec2(1.0/6.0, 1.0/3.0);
  const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
  vec3 i = floor(v + dot(v, C.yyy));
  vec3 x0 = v - i + dot(i, C.xxx);
  vec3 g = step(x0.yzx... 
```
I'll write the standard Ashima implementation carefully from memory:

```glsl
float snoise(vec3 v){
  const vec2 C = vec2(1.0/6.0, 1.0/3.0);
  const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
  // First corner
  vec3 i  = floor(v + dot(v, C.yyy));
  vec3 x0 = v - i + dot(i, C.xxx);
  // Other corners
  vec3 g = step(x0.yzx, x0.xyz);
  vec3 l = 1.0 - g;
  vec3 i1 = min(g.xyz, l.zxy);
  vec3 i2 = max(g.xyz, l.xyz);
  vec3 x1 = x0 - i1 + C.xxx;
  vec3 x2 = x0 - i2 + C.yyy;
  vec3 x3 = x0 - D.yyy;
  // Permutations
  i = mod289(i);
  vec4 p = permute(permute(permute(
             i.z + vec4(0.0, i1.z, i2.z, 1.0))
           + i.y + vec4(0.0, i1.y, i2.y, 1.0))
           + i.x + vec4(0.0, i1.x, i2.x, 1.0));
  // Gradients: 7x7 points on a grid (from webgl-noise)
  float n_ = 0.142857142857;
  vec3 ns = n_ * D.wyz - D.xzx;
  vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
  vec4 x_ = floor(j * ns.z);
  vec4 y_ = floor(j - 7.0 * x_);
  vec4 x = x_ * ns.x + ns.yyyy;
  vec4 y = y_ * ns.x + ns.yyyy;
  vec4 h = 1.0 - abs(x) - abs(y);
  vec4 b0 = vec4(x.xy, y.xy);
  vec4 b1 = vec4(x.zw, y.zw);
  vec4 s0 = floor(b0)*2.0 + 1.0;
  vec4 s1 = floor(b1)*2.0 + 1.0;
  vec4 sh = -step(h, vec4(0.0));
  vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy;
  vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww;
  vec3 p0 = vec3(a0.xy, h.x);
  vec3 p1 = vec3(a0.zw, y.zw... 
```
Hmm — I need to be careful; the standard code:

```glsl
  vec3 p0 = vec3(a0.xy,h.x);
  vec3 p1 = vec3(a0.zw,h.y);
  vec3 p2 = vec3(a1.xy,h.z);
  vec3 p3 = vec3(a1.zw,h.w);
  // Normalise gradients
  vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
  p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
  // Mix final noise value
  vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
  m = m * m;
  return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
```
And x3 = x0 - 1.0 + 3.0*C.xxx — wait: `vec3 x3 = x0 - i... ` standard: `vec3 x3 = x0 - 1.0 + 3.0*C.xxx;` hmm the standard uses `vec3 x3 = x0 - D.yyy;` no... Let me recall precisely the Ashima snoise (webgl-noise/src/noise3D.glsl):

```glsl
vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 permute(vec4 x) { return mod289(((x*34.0)+1.0)*x); }
vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }

float snoise(vec3 v) {
  const vec2 C = vec2(1.0/6.0, 1.0/3.0);
  const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);

  // First corner
  vec3 i  = floor(v + dot(v, C.yyy));
  vec3 x0 = v - i + dot(i, C.xxx);

  // Other corners
  vec3 g = step(x0.yzx, x0.xyz);
  vec3 l = 1.0 - g;
  vec3 i1 = min(g.xyz, l.zxy);
  vec3 i2 = max(g.xyz, l.zxy);

  vec3 x1 = x0 - i1 + C.xxx;
  vec3 x2 = x0 - i2 + C.yyy;  // 2*C.x = 1/3 = C.y
  vec3 x3 = x0 - D.yyy;       // -1.0 + 3.0*C.x = -0.5 = -D.y

  // Permutations
  i = mod289(i);
  vec4 p = permute(permute(permute(
        i.z + vec4(0.0, i1.z, i2.z, 1.0))
      + i.y + vec4(0.0, i1.y, i2.y, 1.0))
      + i.x + vec4(0.0, i1.x, i2.x, 1.0));

  // Gradients: 7x7 points over a square, mapped onto an octahedron.
  float n_ = 0.142857142857; // 1/7
  vec3 ns = n_ * D.wyz - D.xzx;

  vec4 j = p - 49.0 * floor(p * ns.z * ns.z);  // mod(p,7*7)

  vec4 x_ = floor(j * ns.z);
  vec4 y_ = floor(j - 7.0 * x_);

  vec4 x = x_ * ns.x + ns.yyyy;
  vec4 y = y_ * ns.x + ns.yyyy;
  vec4 h = 1.0 - abs(x) - abs(y);

  vec4 b0 = vec4(x.xy, y.xy);
  vec4 b1 = vec4(x.zw, y.zw);

  vec4 s0 = floor(b0) * 2.0 + 1.0;
  vec4 s1 = floor(b1) * 2.0 + 1.0;
  vec4 sh = -step(h, vec4(0.0));

  vec4 a0 = b0.xzyw + s0.xzyw * sh.xxyy;
  vec4 a1 = b1.xzyw + s1.xzyw * sh.zzww;

  vec3 p0 = vec3(a0.xy, h.x);
  vec3 p1 = vec3(a0.zw, h.y);
  vec3 p2 = vec3(a1.xy, h.z);
  vec3 p3 = vec3(a1.zw, h.w);

  // Normalise gradients
  vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
  p0 *= norm.x;
  p1 *= norm.y;
  p2 *= norm.z;
  p3 *= norm.w;

  // Mix final noise value
  vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
  m = m * m;
  return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
}
```
Yes, that's right (i1 = min(g.xyz, l.zxy), i2 = max(g.xyz, l.zxy)). I'm fairly confident in this version. ✓

fbm:
```glsl
float fbm(vec3 p){
  float f = 0.0;
  float a = 0.5;
  for(int i = 0; i < 5; i++){
    f += a * snoise(p);
    p = p * 2.03 + vec3(19.1, 7.7, 3.3);
    a *= 0.52;
  }
  return f; // roughly [-1, 1] but compressed
}
```
Amplitude sum ≈ 0.5+0.26+0.135+0.07+0.036 ≈ 0.98, snoise range ±1 → fbm roughly [-0.9, 0.9] typical ±0.5.

Planet elevations: cont = fbm(sp*1.4 + off) → typical |0.5|. Sea level 0.02: land fraction ≈ 45%? With cont*0.75 + det*0.25 the combined h has range ±~0.7 but typical ±0.35. sea = 0.0 gives ~50% ocean. I'll set sea = -0.05 → more land?? Lower sea = more land. Alien planet: I want ~55-60% ocean with archipelagos + a couple of continents. Set sea = 0.05 (higher sea = more ocean). Then land above 0.05. Hmm, typical fbm values cluster near 0 ± 0.3; sea=0.05 → maybe 40% land. Fine, will look good either way. I'll add a large-scale bias: cont = fbm(sp*1.35) then h = cont*0.8 + det*0.2 + ridge contributions. Also to guarantee interesting continents, multiply detail by landMask progressively.

Actually let me define carefully:

```glsl
vec3 sp = normalize(vObjPos);
float t = uTime;
// domain for terrain (static per-planet, mesh rotates so terrain rotates with it)
float cont = fbm(sp * 1.5 + vec3(11.0, 3.0, 27.0));
float det  = fbm(sp * 5.0 + vec3(2.0, 14.0, 5.0));
float mountains = 1.0 - abs(snoise(sp * 3.1 + vec3(31.0, 7.0, 13.0)));
mountains = mountains * mountains;
float sea = 0.06;
float h = cont * 0.78 + det * 0.22;
float landMask = smoothstep(sea, sea + 0.035, h);
h += mountains * 0.30 * landMask * smoothstep(sea + 0.03, sea + 0.25, h);
```

Ocean colors — alien turquoise sea:
```glsl
float depth = clamp((sea - h) * 3.2, 0.0, 1.0);
vec3 shallow = vec3(0.055, 0.42, 0.40);
vec3 mid     = vec3(0.015, 0.16, 0.22);
vec3 abyss   = vec3(0.004, 0.045, 0.075);
vec3 ocean = mix(shallow, mid, smoothstep(0.0, 0.28, depth));
ocean = mix(ocean, abyss, smoothstep(0.28, 0.75, depth));
```

Land:
```glsl
float bio = fbm(sp * 2.6 + vec3(47.0, 8.0, 21.0));
vec3 moss   = vec3(0.13, 0.20, 0.10);   // dark teal-green vegetation
vec3 rust   = vec3(0.38, 0.19, 0.085);  // oxidized plains
vec3 low = mix(rust, moss, smoothstep(-0.35, 0.4, bio));
vec3 rock = vec3(0.36, 0.31, 0.25);
vec3 land = mix(low, rock, smoothstep(sea + 0.10, sea + 0.26, h));
land = mix(land, vec3(0.50, 0.47, 0.44), smoothstep(sea + 0.28, sea + 0.38, h)); // peaks
// beach
float beach = smoothstep(sea - 0.005, sea + 0.012, h) * (1.0 - smoothstep(sea + 0.012, sea + 0.045, h));
land = mix(land, vec3(0.55, 0.46, 0.30), beach * 0.8);
```

Ice:
```glsl
float lat = abs(sp.y);
float capEdge = fbm(sp * 3.4 + vec3(5.0, 41.0, 17.0)) * 0.10;
float cap = smoothstep(0.68, 0.80, lat + cap * ... 
```
wait name clash with `cap`; rename: 
```glsl
float polar = smoothstep(0.66, 0.78, lat + capNoise * 0.14);
float snowy = smoothstep(sea + 0.30, sea + 0.40, h);  // high peaks snow
float ice = clamp(polar + snowy, 0.0, 1.0); — hmm snowy should only apply on land; polar applies everywhere (sea ice). fine.
vec3 iceCol = mix(vec3(0.82, 0.90, 0.94), vec3(0.65, 0.78, 0.86), smoothstep(0.3, 0.75, det)*0.5);
```

Albedo: `vec3 albedo = mix(ocean, land, landMask); albedo = mix(albedo, iceCol, ice);` — note beach handled inside land; but landMask is 0 below sea → beach band partially in ocean... beach computed on h in [sea, sea+0.045] → landMask at h=sea+0.012 ≈ smoothstep(0.06,0.095, 0.062) ≈ 0.06?? smoothstep(0.06, 0.095, 0.062) = t=(0.062-0.06)/0.035 = 0.057 → smooth ≈ 0.0097 → beach barely visible! Fix: make landMask threshold lower or blend beach after: compute albedo = ocean; then mix land where h > sea: use a softer mask: `float landMask = smoothstep(sea - 0.004, sea + 0.03, h);` and beach band [sea+0.002, sea+0.02]. With smoothstep the beach zone has mask 0.2-0.6 — mixing ocean/land there gives murky shore — actually a soft shoreline is fine visually. Then apply beach mix after with weight beach. OK good enough — shader tuning by feel; values chosen to be plausible.

Lighting assembly (planet fragment):

```glsl
vec3 N = normalize(vNormal);
vec3 V = normalize(uCamPos - vWorldPos);
float NdL = dot(N, uSunDir);
float day = clamp(NdL, 0.0, 1.0);
float mSh = moonShadow(vWorldPos);       // 1 lit
float rSh = ringShadow(vWorldPos);       // 1 lit
vec3 sunCol = vec3(1.0, 0.90, 0.78);
vec3 col = albedo * (vec3(0.010, 0.016, 0.024) + sunCol * (1.25 * day * mSh * rSh));
// specular
vec3 H = normalize(uSunDir + V);
float ndh = max(dot(N, H), 0.0);
float glint = pow(ndh, 120.0) * 1.2;
float sheen = pow(ndh, 6.0) * 0.10;
col += sunCol * (glint + sheen) * (1.0 - landMask) * (1.0 - ice) * day * mSh * rSh;
// moonlight on night side
vec3 toMoon = normalize(uMoonPos - vWorldPos);
float ml = max(dot(N, toMoon), 0.0);
col += albedo * vec3(0.08, 0.14, 0.19) * ml * (1.0 - day);
// bioluminescent shallows
float night = 1.0 - smoothstep(-0.18, 0.10, NdL);
float shelf = smoothstep(sea - 0.10, sea - 0.004, h) * (1.0 - landMask);
float clusters = smoothstep(0.25, 0.65, snoise(sp * 6.0 + vec3(61.0, 23.0, 9.0)));
float sparkle = smoothstep(0.30, 0.75, snoise(sp * 42.0 + vec3(13.0, 51.0, 29.0)));
col += vec3(0.05, 0.75, 0.55) * shelf * clusters * (0.25 + 0.75*sparkle) * night * (1.0 - ice) * 0.8;
```
Hmm — bioluminescence intensity: vec3(0.05,0.75,0.55)*0.8 max ≈ 0.6 in green — on the night side it'll glow nicely but not blow out. But it should be sparse — clusters*sparkle gating. OK.

Fresnel rim on surface:
```glsl
float fres = pow(1.0 - clamp(dot(N, V), 0.0, 1.0), 2.5);
float twil = exp(-pow((NdL - 0.08) * 3.5, 2.0));  // peak near terminator
vec3 rimCol = mix(vec3(0.20, 0.55, 0.62), vec3(0.95, 0.45, 0.20), twil);
col += rimCol * fres * (0.15 + 0.85 * day) * mSh * 0.8;
```
Hmm — the rim should also appear faintly on the night side (airglow): keep the 0.15 base but multiply by mSh? On the night side the atmosphere still scatters a bit — allow base 0.12 without mSh. Fine-tune: `col += rimCol * fres * (0.12 + 0.9*day);` (no mSh — atmosphere visible even during eclipse, plausible).

Twilight band: twil as defined peaks where NdL ≈ 0.08 → a ring around the terminator ✓. But on the night side (NdL < -0.5) twil ≈ exp(-3.4) ≈ 0.03 ✓ small.

Clouds fragment:
```glsl
vec3 sp = normalize(vObjPos);
float evolve = uTime * 0.008;
vec3 q = sp;
float wa = fbm(sp * 2.4 + vec3(0.0, evolve...)) — rotate:
float ang = fbm(sp * 2.2 + vec3(7.0, uTime*0.01, 2.0)) * 1.4;
float ca = cos(ang), sa = sin(ang);
q.xz = mat2(ca, -sa, sa, ca) * sp.xz;
float d1 = fbm(q * 3.1 + vec3(3.0, 12.0, 7.0) + vec3(uTime*0.012, 0, 0));
float d2 = fbm(q * 7.7 + vec3(21.0, 4.0, 15.0) - vec3(uTime*0.02, 0, 0));
float cover = smoothstep(0.02, 0.5, d1 * 0.72 + d2 * 0.38 + 0.14);
// wispier at poles? optional
float alpha = cover * 0.92;
// lighting
vec3 N = normalize(vNormal);
float NdL = dot(N, uSunDir);
float day = clamp(NdL * 0.9 + 0.1, 0.0, 1.0);
float mSh = moonShadow(vWorldPos);
float rSh = ringShadow(vWorldPos);
// cloud shading: darker bases via d2
float shade = 0.55 + 0.45 * smoothstep(-0.2, 0.6, d2);
vec3 lit = vec3(1.04, 1.0, 0.96) * day * 1.25;
vec3 shadeCol = vec3(0.16, 0.20, 0.26);  // blue-gray unlit
vec3 col = albedoless... 
```
Cloud color = mix(shadowColor, cloudWhite, day)*shade... Let me:
```glsl
vec3 cCol = mix(vec3(0.05, 0.07, 0.10), vec3(1.0, 0.99, 0.97) * 1.15 * shade, day);
col = cCol * mSh * rSh;  // hmm — ring shadow should darken but keep a floor
```
Use `col = cCol * mix(0.15, 1.0, mSh) * mix(0.35, 1.0, rSh)` — softer. Also clouds get slight warm tint at terminator: skip. Also fresnel fade at the limb so clouds don't double with atmosphere: alpha *= smoothstep? Actually clouds at the limb get denser visually (line of sight) — natural. Keep.

Also cloud fragment should include subtle silver lining? skip.

Atmosphere shell fragment (b-parameter approach):
```glsl
varying vec3 vWorldPos;
uniform vec3 uCamPos, uSunDir; uniform float uPlanetR, uShellR;
void main(){
  vec3 C = uCamPos;
  vec3 D = normalize(vWorldPos - C);
  float tc = -dot(C, D);
  vec3 closest = C + D * tc;
  float b = length(closest);
  float x = clamp((b - uPlanetR) / (uShellR - uPlanetR), 0.0, 1.0);
  float glow = pow(1.0 - x, 2.2);
  // day side
  vec3 dirN = normalize(closest);
  float day = clamp(dot(dirN, uSunDir) * 0.65 + 0.42, 0.05, 1.0);
  float twil = exp(-pow((dot(dirN, uSunDir) - 0.05) * 2.6, 2.0));
  vec3 base = vec3(0.18, 0.52, 0.60);
  vec3 warm = vec3(1.0, 0.42, 0.16);
  vec3 col = mix(base, warm, twil * 0.85) * glow * day * 1.35;
  // forward scatter toward sun
  float fwd = pow(max(dot(D, uSunDir), 0.0), 3.0);
  col += warm * fwd * glow * 0.35;
  gl_FragColor = vec4(col, 1.0); // additive blending → alpha ignored
  #include tonemapping/colorspace
}
```
Wait — for BackSide rendering, vWorldPos is on the far hemisphere; D from camera through that point; the closest approach b of that ray to the center is what we want — correct ✓. But careful: the fragment seen at a given pixel belongs to the far shell intersection; the ray's impact parameter b equals what it would be — glow consistent across the annulus ✓. Also the region where b < planetR: those rays hit the planet (opaque) → occluded ✓ no need to handle.

But there's an issue: tc must be > 0 (shell in front); if the camera is INSIDE the shell (never — camera min distance ~35 vs shell 10.7 ✓).

Ring shadow on planet — need ringPattern shared. Define in common chunk:

```glsl
float ringPattern(float x){  // x in [0,1] across the ring
  float v = snoise(vec3(x * 16.0, 3.7, 8.1)) * 0.55
          + snoise(vec3(x * 42.0, 9.2, 3.3)) * 0.30
          + snoise(vec3(x * 7.0, 1.2, 5.5)) * 0.45;
  v = v * 0.5 + 0.5;
  float a = smoothstep(0.18, 0.72, v);
  a *= 0.55 + 0.45 * snoise(vec3(x * 90.0, 6.0, 2.0)) ... fine bands:
  a *= 0.72 + 0.28 * snoise(vec3(x * 140.0, 4.4, 9.9));
  // Encke-like gaps
  a *= 1.0 - 0.9 * exp(-pow((x - 0.62) * 22.0, 2.0));
  a *= 1.0 - 0.55 * exp(-pow((x - 0.83) * 30.0, 2.0));
  // edges
  a *= smoothstep(0.0, 0.06, x) * (1.0 - smoothstep(0.94, 1.0, x));
  return clamp(a, 0.0, 1.0);
}
```

ringShadow(p): 
```glsl
float ringShadow(vec3 p){
  vec3 n = uRingNormal; // world, unit
  float denom = dot(uSunDir, n);
  if (abs(denom) < 0.001) return 1.0;
  float t = -dot(p, n) / denom;
  if (t <= 0.0) return 1.0;
  vec3 q = p + uSunDir * t;
  float r = length(q);
  float x = (r - uRingInner) / (uRingOuter - uRingInner);
  if (x < 0.0 || x > 1.0) return 1.0;
  float a = ringPattern(x);
  return 1.0 - a * 0.55;
}
```
Branching with if in fragment — fine.

moonShadow(p):
```glsl
float moonShadow(vec3 p){
  vec3 oc = uMoonPos - p;
  float along = dot(oc, uSunDir);
  if (along <= 0.0) return 1.0;
  float d = length(oc - uSunDir * along);
  return smoothstep(uMoonR * 0.45, uMoonR * 1.35, d);
}
```
Soften more: penumbra wide: smoothstep(uMoonR*0.3, uMoonR*1.8, d)? The shadow softness depends on the sun's angular size; a stylized soft edge ~1.5 moon radii looks good. I'll use smoothstep(uMoonR*0.45, uMoonR*1.6, d).

planetShadow(p) (for rings and moon):
```glsl
float planetShadow(vec3 p){
  vec3 oc = -p;   // toward planet center at origin
  float along = dot(oc, uSunDir);
  if (along <= 0.0) return 1.0;
  float d = length(oc - uSunDir * along);
  return smoothstep(uPlanetR * 0.85, uPlanetR * 1.25, d);
}
```
Hmm for the moon, the penumbra should be wider (sun angular size from the moon is small → fairly sharp umbra but let's keep soft): use smoothstep(uPlanetR*0.9, uPlanetR*1.3, d) — shadow transition width 0.4*R = 4 units at moon distance 30-ish — reasonably soft. OK.

Rings fragment:
```glsl
varying vec3 vObjPos; varying vec3 vWorldPos;
// object space: ring in XY plane → r = length(position.xy)
void main(){
  float r = length(vObjPos.xy);
  float x = clamp((r - uRingInner) / (uRingOuter - uRingInner), 0.0, 1.0);
  float a = ringPattern(x);
  if (a < 0.003) discard;
  vec3 N = uRingNormal;
  vec3 V = normalize(uCamPos - vWorldPos);
  // lighting
  float ndl = abs(dot(N, uSunDir));
  float li = 0.35 + 0.85 * ndl;
  // forward scattering when sun behind ring (grazing view through rings)
  vec3 Vn = normalize(uCamPos - vWorldPos);
  float back = pow(max(dot(-Vn? ...
```
Forward scatter: when the view direction ≈ sun direction (looking toward the sun through the rings) rings brighten: `float fwd = pow(max(dot(normalize(vWorldPos - uCamPos), uSunDir), 0.0), 4.0); li += fwd * 1.2;`
```glsl
  float psh = planetShadow(vWorldPos);
  // subtle radial color gradient
  vec3 cIn = vec3(0.50, 0.44, 0.36);
  vec3 cOut = vec3(0.36, 0.34, 0.32);
  vec3 col = mix(cIn, cOut, x) * li * psh;
  // warm sun tint
  col *= vec3(1.05, 0.98, 0.9);
  gl_FragColor = vec4(col, a * uOpacity);
  tonemap includes
}
```
Unlit side of the rings: when viewing the rings from below (opposite the sun), they should appear darker: use sign: `float ndlSigned = dot(N, uSunDir); float li = (ndl>0) ? lit-side : dark side (translucent)`: rings are translucent — the unlit side shows transmitted light: brightness lower and slightly different color. `float litSide = step(0.0, dot(N,uSunDir))...` With DoubleSide, the geometric normal is fixed; dot sign tells which side is lit. transmitted = 0.3+0.25*ndl. `float li = dot(N, uSunDir) > 0.0 ? 0.4+0.9*ndl : (0.22 + fwd);` Fine — implement with mix on sign: `float s = sign(dot(N,uSunDir)); li = 0.42 + 0.75*ndl*s? ...` keep simple:
```glsl
float ndl = dot(N, uSunDir);
float li = 0.30 + 0.95 * abs(ndl);
if (ndl < 0.0) li *= 0.55;  // viewing unlit face
li += fwd * 1.1;
```

Moon fragment:
```glsl
vec3 sp = normalize(vObjPos);
float m1 = fbm(sp * 3.4 + vec3(9.0, 2.0, 17.0));
float m2 = fbm(sp * 9.0 + vec3(27.0, 5.0, 3.0));
float mare = smoothstep(0.15, 0.55, fbm(sp * 1.7 + vec3(51.0, 13.0, 7.0)));
vec3 albedo = mix(vec3(0.52, 0.50, 0.47), vec3(0.34, 0.32, 0.30), m1*0.5+0.5);
albedo = mix(albedo, vec3(0.20, 0.21, 0.24), mare * 0.8);
albedo *= 0.9 + 0.2 * m2;
vec3 N = normalize(vNormal);
float ndl = max(dot(N, uSunDir), 0.0);
float psh = planetShadow(vWorldPos);
vec3 col = albedo * (vec3(0.008, 0.010, 0.014) + vec3(1.0, 0.92, 0.82) * 1.25 * ndl * psh);
// eclipse reddening
col += albedo * vec3(0.45, 0.12, 0.05) * ndl * (1.0 - psh) * 0.9;
// slight earthshine-ish fill from planet? The moon near the planet gets reflected light:
// skip or tiny constant.
```
Also moon fresnel rim? Not needed. Also the moon could receive the planet's glow — skip.

Actually add subtle warm rim on moon from atmosphere? skip — keep moon crisp.

Sun mesh: I also want subtle pulsation? Static is fine; the halo shader has enough structure.

Flare overlay details:

Ortho scene elements (all additive except vignette):
1. Halo: follows sun screen pos: soft radial gradient, radius ~0.5 (units where screen height=2), intensity 0.10 * vis, warm color. Also this mimics the bloom around the sun even when the sun core is occluded (halo visible around the planet edge) — with vis fade.
2. Ghosts at k = -0.4, -0.75, -1.15, -1.5, and +0.35 (between sun and center): sizes 0.04–0.16, colors: teal (0.1,0.5,0.5), amber (0.6,0.4,0.15), faint violet (0.35,0.2,0.5), warm white. Intensity 0.05–0.12 each * vis.
3. Streak: a wide horizontal gradient bar centered at the sun NDC position: width 1.6 (in x-units = aspect-relative?) — implement as a plane scaled (2.6, 0.05) at sun position with a shader: exp falloff both axes. Intensity 0.15*vis. — This is the anamorphic streak. 
4. Vignette (full-screen quad, normal blending, black edges alpha ~0.32).

Positions: sunNDC = sunPos.project(camera) → ndc in [-1,1]² (x aspect-independent). Convert to ortho world: X = ndc.x * aspect, Y = ndc.y. Ghost center = sunNDC * (-k) → X = -k*ndc.x*aspect... wait mirroring through screen center: ghost at ndc' = -k * ndc (so k>0 mirrors beyond center to the opposite side). With k=0.5 the ghost is halfway to the center on the opposite side. Standard ghost chain: positions at multiples of the center-sun axis. I'll compute per-ghost: g = sun_ndc * (-k). If k negative, ghost lands between center and sun (on the sun side). Mix.

Vis factor: 
```js
let vis = 1;
// occlusion
... occl = smoothstep... vis *= (1 - occ)
// behind camera?
const toSun = sunPos - camPos; if (dot(camDir, toSunNorm) < 0) vis = 0;
// edge fade: fade as the sun approaches the screen edge — ghosts can persist slightly offscreen:
const ex = Math.abs(ndc.x), ey = Math.abs(ndc.y);
const edge = 1 - smoothstep(0.85, 1.6, Math.max(ex, ey));
vis *= edgeFade;
```
Also multiply by a small base so ghosts only appear when the sun is well within view — standard.

But hold on — with the camera orbiting, how often is the sun in frame? Camera looks at the planet; the sun is off to the side by the azimuth separation (23°-85°). The sun is 15° above the plane. The camera's FOV: looking at origin from distance ~40 — the sun direction from the camera is roughly toward azimuth 0.42 from the camera at azimuth θ: the angular separation between the look direction (toward origin) and the sun direction: at t=0, separation 67° → sun out of frame. As the camera reaches min separation (t≈11, 29°), the sun might be just outside the frame (half-hFov 43°... the sun's angle from the look axis: the look axis points at origin; the sun is at elevation 15°+ and azimuth offset... At t=11: camera az 0.92 vs sun az 0.42 → 29° azimuth separation; sun elevation ~15°. The sun's angular offset from the look axis ≈ sqrt((29°·cos-ish)² + ...) roughly 30° → within the 43° half-hFov ✓ → the sun IS in frame around t≈8-15! Great — the lens flare shows during the eclipse sequence (sun + moon silhouette + shadow). Then it drifts out of frame. So in the 30s window: sun+flare visible around t≈6-16 ✓, stars always, rings always, moon events ✓.

Also the halo/ghost flare will appear as the camera pans — beautiful.

But wait — the sun billboard is at distance 900; the flare ghosts in screen space are positioned at fractions of the sun's NDC. If the sun NDC is (0.6, 0.35), ghosts at -0.4k... they'd be at (-0.24·aspect·...)... fine.

One issue: the sun billboard scale: at distance 900, to appear ~6° wide, size = 2*900*tan(3°) ≈ 94 world units. I'll make the quad 130 units with the glow concentrated in the center (core exp(-r²*40) → core radius ~0.16 of half-width = 7.5 world units ≈ 0.5° — sun disc ~0.5-1°: plausible stylized).

Sun occlusion & planet: the sun is at 900 with depthTest — the planet at 40 occludes ✓. But the billboard's depth: the plane is billboarded via view-space offset — its depth = center depth ✓.

Also — the atmosphere additive shell (BackSide, radius 10.75 planetR*1.075) is at the planet's depth; the sun is far behind → hidden ✓. The glow AROUND the limb: the shell edge pixels near the limb are visible in front of... the shell is opaque-ish additive with depthWrite false; the sun behind: sun pixels where the shell covers get additive atmosphere over them — creating a bright halo around the occluded sun — physically plausible (atmosphere glows) ✓ nice.

Stars: additive points, depthWrite false, they're at 1900 — behind the sun billboard region: both additive, order-independent-ish ✓.

Now the flare overlay renders with autoClear false after the main scene:
```js
renderer.autoClear = true; // main pass clears
renderer.render(scene, camera);
renderer.autoClear = false; ... hmm second render would clear again.
```
Standard: `renderer.clearDepth()` not needed for ortho overlay; but the renderer clears color+depth each render call unless autoClear false. Do:
```js
renderer.autoClear = false;
renderer.clear();
renderer.render(scene, camera);
renderer.render(flareScene, flareCam); // no clear
```
✓.

Flare element opacity updates in JS each frame: set material uniform uVis.

Ghost meshes: create PlaneGeometry(2,2) with shader using vUv → circle in [-1,1]. Mesh scaled to size, positioned at (X, Y, 0).

Screen-space flare only when the sun is roughly in front: also hide when ndc magnitude > ~1.5.

Sun's project: need camera matrices updated — compute after camera.position/lookAt set: camera.updateMatrixWorld(); then project.

Star twinkle: uTime uniform.

Nebula: big sphere radius 2400 (within far 6000 ✓), BackSide, ShaderMaterial:
```glsl
v = normalize(vObjPos);
float n1 = fbm(v * 3.2 + 5.0);
float n2 = fbm(v * 7.5 + 19.0);
float band = exp(-pow(dot(v, uBandN), 2.0) * 6.0);  // band great circle
vec3 col = vec3(0.012, 0.028, 0.036);  // faint base
col += vec3(0.015, 0.06, 0.07) * band * smoothstep(0.1, 0.8, n1*0.5+0.5);
col += vec3(0.05, 0.02, 0.06) * band * smoothstep(0.3, 0.9, n2*0.5+0.5) * 0.5;
col += vec3(0.02, 0.045, 0.05) * smoothstep(0.45, 0.9, fbm(v*2.0+31.0)*0.5+0.5) * 0.5;
```
Keep it dim. Maybe skip band to avoid kitsch? A tilted galactic band adds a lot of atmosphere for cheap. I'll include it subtly (max add ≈ 0.07). uBandN = normalize(vec3(0.3, 1.0, 0.15))... the band is the plane perpendicular to uBandN; band factor high where v·n ≈ 0 ✓.

Also — should the nebula rotate? Static is fine (it's the distant sky); but a barely-perceptible rotation adds life: rotate the nebula sphere slowly (0.001 rad/s). The starfield can rotate very slightly too (0.004) — actually rotating the starfield with the nebula together in a "sky" group rotating at 0.002 rad/s is nice and subtle. But stars rotating might look odd relative to... it's fine — the whole sky slowly rotating is natural (camera motion dominates anyway). I'll rotate sky group at 0.0035 rad/s — barely perceptible, alive.

Moon position update:
```js
const ma = MOON_A0 + MOON_W * t;
const mp = new THREE.Vector3(Math.cos(ma), 0, Math.sin(ma)).multiplyScalar(MOON_R);
// tilt about X by inc:
mp.y = -mp.z * Math.sin(inc) — wait apply rotation properly:
tilted: y' = y cos(inc) - z sin(inc) = -z sin(inc) (y=0) = -sin(inc)*z0; z' = z cos(inc).
So mp = (R cos a, -R sin a * sin(inc), R sin a * cos(inc)). With inc = -0.32: sin(inc) = -0.3146 → y = +R*0.3146 sin a ✓ matches earlier.
```
Also the moon should spin slowly (tidally locked-ish: rotate mesh at orbital rate). Moon mesh rotation.y = -(ma) + const — fine, noise terrain rotates with it ✓.

Also planet axial rotation: planet.rotation.y = t * 0.02 (slow); clouds rotation.y = t * 0.026 + offset.

Wait — one subtlety: the planet mesh rotating means vObjPos (used for terrain noise) rotates with it ✓ terrain is fixed to the surface ✓. World normals update via modelMatrix ✓.

The tilt group: planetGroup (planet, clouds, atmosphere, rings) with rotation.z = -0.18. Note: rings are a child — ring world normal = group's up transformed. I need uRingNormal uniform = world normal of the ring plane: compute each frame? It's static: normal = (sin? ) rotating (0,1,0) about Z by -0.18: n = (sin(0.18)?? rotation about Z by angle φ: (0,1,0) → (-sin(-0.18)... R_z(θ)*(0,1,0) = (-sinθ, cosθ, 0). θ = -0.18 → (-sin(-0.18), cos(-0.18), 0) = (0.179, 0.984, 0). Set as constant uniform ✓. RingShadow uses uRingNormal ✓ and planet center origin ✓.

The moon: separate from the tilt group (its orbit is independent) — moon world position computed in JS ✓ and passed as uniform to planet/clouds/rings materials each frame.

Camera & uniforms: uCamPos updated per frame for all materials (or use cameraPosition built-in — three provides `cameraPosition` uniform automatically in ShaderMaterial! Yes, `cameraPosition` is a built-in uniform in ShaderMaterial (view-space? no — world-space camera position is available as `uniform vec3 cameraPosition;` auto-injected). ✓ Use that; no need for uCamPos.

Sun dir uniform: constant vec3. ✓

Also tonemapping includes: I must ensure the ShaderMaterial compiles `#include <tonemapping_fragment>` — these chunks reference `toneMapping` — the chunk uses functions defined when the renderer defines them via program defines... For ShaderMaterial, THREE injects tone mapping GLSL only if material.toneMapped is true? The chunk `tonemapping_fragment` is: `#if defined( TONE_MAPPING ) gl_FragColor.rgb = toneMapping( gl_FragColor.rgb ); #endif` — and TONE_MAPPING is defined by the renderer for materials when renderer.toneMapping !== NoToneMapping and material.toneMapped !== false. ShaderMaterial gets the same treatment ✓ (the renderer sets defines for all materials based on toneMapping). And `colorspace_fragment` handles output color space conversion ✓ (in newer three versions the chunk is `colorspace_fragment`; r152+ renamed encodings_fragment → colorspace_fragment; r186 has colorspace_fragment ✓).

Version check: three r186 — `outputColorSpace` default is SRGBColorSpace ✓. I'll set renderer.toneMapping = THREE.ACESFilmicToneMapping; toneMappingExposure = 1.15.

Since I'm including tonemapping+colorspace chunks in every custom shader (planet, clouds, atmosphere, rings, moon, sun, stars?, nebula, flare ghosts?) — the flare ghosts should probably NOT be tone-mapped (they're additive screen UI-ish; ACES would dull them)... Consistency: ACES on everything is fine and prevents ugly clipping. I'll include the chunks in world-space shaders and the sun; for stars/nebula/flare I'll also include for consistency (cheap). Hmm, colorspace chunk converts linear→sRGB output ✓ needed since renderer outputs to sRGB canvas. If I omit it, colors look darker/wrong relative. Include everywhere.

Actually careful: `#include <tonemapping_fragment>` in r186 — exists ✓. `#include <colorspace_fragment>` — exists ✓.

Renderer clear color: black (0x000000). 

Star points also get tone mapped — white stars at 1.0 through ACES → ~0.8 gray-white, fine.

Let me also think about the planet shader's ring shadow: uRingNormal, uRingInner/Outer, uPlanetR constants — shared via a small uniforms object referenced by multiple materials (THREE allows sharing uniform objects across materials — I'll create `const shared = { uSunDir: {value}, uMoonPos: {value}, uMoonR: {value}, uPlanetR: {value}, uRingInner..., uRingNormal..., uTime: {value} }` and reference the same objects in each material's uniforms → single update point ✓ nice.

GLSL common chunk (NOISE + shadow functions) prepended to each fragment shader that needs it.

Now — moon shadow function needs uSunDir & uMoonPos: include in common.

One more component: orbit path line for the moon — a subtle circle: THREE.LineLoop with 256 points radius MOON_R, in the tilted plane, material LineBasicMaterial color 0x3a5a5a transparent opacity 0.22. But tilt about X by inc: apply via geometry rotation: create points in XZ circle, rotate the Line object by rotation.x = inc ✓ (matches the parametrization: pos = Rz? my param: y = -R sin a sin(inc), z = R sin a cos(inc) — that's rotation about X axis by angle inc applied to (cos a, 0, sin a): R_x(inc) rotates y,z: y' = y cos inc - z sin inc = -sin(inc) z0 ✓, z' = y sin inc + z cos inc = cos(inc) z0 ✓. So object rotation.x = inc ✓.

Also maybe a faint equatorial... skip.

Dust/particles near the rings? Extra sparkle: tiny ring-moonlets? Skip — keep scope.

Performance: full-screen fragment work: planet disc ~40% of screen with heavy fbm (planet: cont 5 octaves + det 5 + mountains + bio 5 + capNoise 5 + clusters/sparkle 1 each + ringPattern (3 snoise + 1) + moonShadow cheap → ~25-30 snoise per pixel. At 1080p with the planet covering ~25% → fine on GPUs; on weak integrated GPUs maybe heavy but acceptable. I could reduce fbm octaves to 4 for secondary fields. I'll use fbm5 for terrain-defining and 4-octave for secondary. Let me define fbm(p) 5 octaves and fbm4(p) 4 octaves; use fbm4 for bio/cap/cluster noise.

Also the cloud shader: warp 5 + d1 5 + d2 5 = 15 snoise/pixel where clouds visible — ok. Note: cloud fragments outside the planet disc are discarded... no — the cloud sphere is transparent; fragments where alpha≈0 still compute noise. Add early discard: if cover < 0.01 discard ✓ saves blending but not noise cost. Could compute a cheap pre-test: use d1 only... acceptable.

Rings: pattern 4 snoise + planetShadow cheap ✓.

Atmosphere: no noise ✓ cheap.

Let me write the sun lens-flare ghost placement math in JS:

```js
const sunWorld = new THREE.Vector3().copyVectors(sunDir).multiplyScalar(SUN_DIST);
const ndcV = new THREE.Vector3();
function updateFlare(){
  ndcV.copy(sunWorld).project(camera);
  // vis
  const camDir = new THREE.Vector3(); camera.getWorldDirection(camDir);
  const toSun = sunWorld - camPos normalized; const front = dot(camDir, toSunN) 
  ...
  const occ = ...; 
  const vis = (1-occ) * edgeFade * (front ? 1 : 0);
  halo.position.set(ndc.x*aspect, ndc.y, 0); halo.material.uniforms.uVis.value = vis*...
  ghosts.forEach(...)
  sunMat.uniforms.uOcc.value = 1-occ; // dims the billboard halo near the limb
}
```
Note `.project` mutates the vector ✓.

Edge fade: `const off = Math.max(Math.abs(ndc.x)/ (0.55), Math.abs(ndc.y)/0.6);`? Let me define: fade starts when the sun leaves the frame: sun fully in frame while |ndc| < 1. Fade: `edge = 1 - smoothstep(0.7, 1.4, max(|x|,|y|))` — begins fading while still partly visible ✓ good (halo lingers).

Also the sun should still occlude the... fine.

Occlusion edge: `occ` from closest approach b: occluded when b < planetR-ish. Use R_atm = 11.2 for the fade band: `occ = 1 - smoothstep(10.2, 12.0, b)` → smooth transition across the limb (planet R=10, atmosphere to ~11.3). vis *= (1 - occ). Also multiply sun's own brightness: sunMat.uniforms.uDim = mix(1, 0.15, occ)? When occ = 1 the sun is fully behind → invisible via depth; but the billboard halo (bigger than planet) may still peek around the limb — dimming to 0.15 gives a natural glow-peek. Also the FLARE ghosts disappear when occluded (they'd remain per projection) — physically the flare comes from light entering the lens; when the sun is blocked, flare vanishes ✓ (1-occ) factor.

Star twinkle subtle. 

Camera FOV: 55. Let me double check the opening shot: camera at az 1.59, r 45, y ~4.9 — looking at origin. Planet disc 2*atan(10/45) = 25°. Rings span 2*atan(26/45) = 60° — fits hFOV (~85°). The sun at az 0.42 is 67° to the side → out of frame at t=0. Terminator visible: sun 67° from camera azimuth → phase like a gibbous... the illuminated fraction visible = 1 - 67/180... roughly (1+cos67)/2 ≈ 0.70 — planet ~70% lit, terminator near one limb ✓ night side crescent with bioluminescent glow visible on the left ✓. Moon: visible? relative az at t=0: -137°; moon azimuth = a(0) = -0.80, camera az 1.59: separation 2.39 rad = 137°; moon at radius 30 vs camera 45: the moon is beyond... behind the planet side. Angular offset from the look axis: compute quickly: cam (45cos1.59, 4.9, 45sin1.59) = (45*(-0.0197), 4.9, 45*0.9998) = (-0.89, 4.9, 45.0). Moon: a=0: (30, -0*... y = R*0.3146*sin(0) = 0 → (30, 0, 0)... wait a(0) = MOON_A0 = -0.80: moon pos = (30 cos(-0.8), 30*0.3146*sin(-0.8), 30 sin(-0.8)*0.949) = (30*0.6967, 9.438*(-0.717)... sin(-0.8) = -0.7174: y = 30*0.3146*(-0.7174) = -6.77; z = 30*(-0.7174)*0.9492 = -20.43. Moon (20.9, -6.77, -20.4). cam→moon: (21.8, -11.7, -65.4), |v| = 69.4 → (0.314, -0.0974, -0.946). cam→origin: (0.89, -4.9, -45)/45.2 = (0.0197, -0.1073, -0.994). dot = 0.006 + 0.0104 + 0.935 = 0.951 → 18° off-axis → the moon IS in frame at t=0, near the planet's limb (planet angular radius 12.7°; moon at 18° → just outside the disc, to the lower-left?) Direction check vertical: moon y-component -0.097 vs planet dir -0.107 → similar → moon roughly aligned vertically, offset in azimuth mostly horizontal. The moon at 18° off-axis, distance 69 → angular radius 1.25° — a small moon near the planet's limb at the opening, lit phase: sun at (0.88,0.26,0.40): moon's sun-facing hemisphere: from the camera, is the moon's lit side visible? The moon is at azimuth -0.8 (opposite side from the sun az 0.42?? moon az = atan2(z,x) = atan2(-20.4, 20.9) = -0.77 rad. Sun az 0.42. Angle between moon position vector and sun direction: m̂ = (0.697, -0.226, -0.681); s·m̂ = 0.613 - 0.0596 - 0.269 = 0.284 → 73° — the moon is half-lit-ish from the camera's perspective (phase angle 73° → gibbous? The phase seen from camera: angle sun→moon→camera. Camera direction from moon: cam - moon = (-21.8, 11.7, 65.4)/69.4 = (-0.314, 0.164, 0.943). s·that = -0.276 + 0.043 + 0.377 = 0.144 → 82° → half moon. Fine ✓ a half-lit small moon visible at the limb at t=0 — nice.

Then it slips behind the planet? relative az goes -2.391 → decreasing offset... wait relative az = a - θ = -0.80-... at t=0: a - θ = -0.80 - 1.591 = -2.391. As t increases, relative increases (0.2124/s): -2.391 → -2.0 (t=1.84) → -1.5 (t=3.7): the moon moves from "behind at 137°" toward 90° (side) at t≈3.4 → out of frame? Its angular offset from the look axis ≈ grows from 18° toward... at relative = π/2 the moon is 90° from the anti-camera direction; its offset from the look axis ≈ atan-ish ~45°+ → out of frame quickly. So the moon exits the frame by t≈2-3, reappears... hmm — during t≈4-10 the moon is off-frame; shadow sweeps t 6-11 (shadow visible WITHOUT the moon — fine); moon looms into frame crossing the disc t≈10-13 (as computed, angular radius ~8° at ~10 distance... recompute with r_cam≈40-41 at t=11: r(11) = 40 - 5 e^{-0.99} + 1.4 sin(1.43) = 40 - 1.856 + 1.394 = 39.5. Moon radius 30, relative az at t=11 = -2.391+2.336 = -0.055 rad ≈ -3°: moon nearly on the camera axis, radius difference 9.5 → distance cam→moon ≈ 9.5 + geometry. Moon angular radius atan(1.5/9.5) = 9°. Planet angular radius atan(10/39.5) = 14.2°. So a moon ~18° across centered-ish over the planet disc (which is 28° across) — the moon covers ~40% of the planet's face — dramatic eclipse silhouette ✓. Then it recedes: t=13: rel az = 0.368 rad = 21°; t=15: 0.79 rad = 45°: the moon slides off the disc to the side while shrinking. 

Timeline (first 30s) summary:
- t=0: wide shot, planet ~70% lit, terminator + glowing coasts on the dark limb, small half-moon near the limb, rings crossing the frame.
- t≈1-3: moon slips behind... wait — actually hold on: is the moon occulted at t=0? rel az = -2.391 = -137°, offset from π = 43° — the moon is 43° from dead-behind → NOT occluded, visible beside the planet's dark side ✓ (as computed, 18° off the look axis — hmm, 18° off-axis while the planet's angular radius is ~12.7° at distance 45... wait recompute: at t=0 r_cam = 45 → planet angular radius = atan(10/45) = 12.5°; moon at 18° off-axis → visible just outside the limb ✓).
- t≈3-9: moon out of frame; camera drifts; planet rotates; sun may enter the frame edge ~t≈6+ (separation at t=6: θ=1.59-0.377=1.214 vs 0.422 → 45.4° — near the frame edge, flare ghosts start appearing).
- t≈6-11: moon's shadow sweeps across the planet (peak t≈8.6 — shadow ~3.8 units from center, well within the disc).
- t≈9-14: the moon itself crosses the planet's face as a large backlit silhouette with a glowing crescent — THE hero moment.
- t≈10-16: sun near frame center-ish (min separation at... separation θ_sun - θ_cam: θ_cam decreases: at t=16, θ=1.59-1.005=0.584 vs 0.422 → 9.2° separation! The sun passes almost directly behind the planet around t≈16-18?? Let me check: camera az crosses sun az 0.422 at t = (1.591-0.422)/0.0628 = 18.6s. At that moment the camera is exactly on the sun-side meridian → looking at the planet with the sun directly behind the camera → the planet is FULLY lit (full phase) and the sun is BEHIND the camera → sun out of frame! Hmm — wait: when camera az = sun az, the camera is between the sun and the planet-ish (both on the same side): looking at the planet, the sun is behind the camera → not visible, and the planet appears fully lit. So the flare is visible BEFORE that (when separation is moderate: sun visible when separation < ~43°+elevation considerations). Separation(t): |0.422 - (1.591 - 0.0628t)| = |0.0628t - 1.169|. At t=14: |0.879-1.169|... 0.0628*14 = 0.879 → separation = 0.712 rad = 40.8° → sun near the frame edge. At t=18: 1.13-1.169 = -0.039 → 2.2°?? separation |0.422 - 0.462| — wait θ(18) = 1.591 - 1.130 = 0.461 → separation 0.039 rad = 2.2° → the sun is almost directly behind the camera... in screen terms the sun's direction vs the look direction: the look direction is from cam toward origin = -camPos direction; the sun direction from cam ≈ sunDir (far away). The angle between -camPoŝ and sunDir: camPoŝ az 0.461 ≈ sun az → -camPoŝ has azimuth 0.461+π = 3.60 — opposite the sun. So the sun is behind the camera ✓ out of frame. So the flare window: sun in frame while separation between ~25-43°, i.e., t ∈ [~10.5, ~16.5]. During that window the sun is visible near/above the planet with flare ✓, and the moon silhouette crossing t≈10-14 with the sun in frame → backlit moon crescent prominent ✓. Chef's kiss: at t≈12-14, sun visible upper area, moon crossing the disc, its shadow beneath.
- t≈16-24: sun drifts out of frame; camera continues; the day side fills more (full phase approaching t≈18.6).
- t≈20-26: the moon swings around behind the planet — approaching the limb from the side ~t=22-24, occultation ~t=24.5-27.5 (moon slips behind the planet — nice closing beat).
- t≈27-30: moon hidden; planet near-full phase (camera az ≈ 0.422+? at t=27: θ = 1.591-1.696 = -0.105 → separation 0.53 rad = 30° — planet still mostly lit); ring shadow band visible on the planet; stars drift.

All the required elements show within 30s ✓. Also the recording window catches: atmosphere rim always, sun+flare t≈10-17, eclipse shadow t≈6-11, moon silhouette t≈10-14, occultation t≈25-27, rings always, clouds rotating, starfield dense, bioluminescent night coasts at t≈0-4 on the left limb.

Camera y range: 2.2 + 4.2 sin(0.09t+0.7): t=0: 4.91; t=10: 2.2+4.2 sin(1.6) = 2.2+4.17=6.4; t=20: 2.2+4.2 sin(2.5) = 2.2+3.82 = 6.0; t=27: 2.2+4.2 sin(3.13) = 2.2+0.13 = 2.3; t=30: 2.2+4.2 sin(3.13) ≈ 2.2+0.13*?? sin(0.09*27+0.7) — t=30: 2.7+... sin(3.4) = -0.256 → y = 2.2-1.2 = 1.0. So the camera drifts downward later — crossing the ring plane around t≈27-29?? Ring plane tilted -0.18 about Z; camera y from 6.4 → 1.4-ish — the camera stays above the ring plane mostly; fine — crossing the ring plane would put rings crossing the view dramatically; the tilt makes the ring plane's y at the camera's azimuth vary... not exactly; camera y min = 2.2-4.2 = -2.0 at t ≈ (π - 0.7)/0.09... y(t) = 2.2+4.2 sin(0.09t+0.7) — min at 0.09t+0.7 = -π/2+2π → t = (4.712-0.7)/0.09 = 44.6s — outside the window. So in the window, y ∈ [2.2, 6.4] — camera stays above the plane, rings always seen from slightly above ✓ elegant.

Now — the ring shadow on the planet: sun elevation 15° above the ring plane means the ring shadow falls on the planet's southern... the shadow of the rings falls on the hemisphere opposite the sun's elevation: sun above the plane → ring shadow on the below-sun side: a curved band across the planet south of the equator, curved. With sun elev 15°, the band is close to the equatorial region on the anti-sun half. Visible when the camera sees the anti-sun side... The ring shadow is cast on the day side only where the shadow falls on lit regions. With the camera at separation ~30-60° from the sun azimuth, we see mostly the day side; the ring shadow band will be visible on the planet where rings block sun: the shadow lies on the anti-sun side of the planet mostly (since rings surround, the shadow of the annulus at radius 15-26 in the sunward direction falls on the planet near the sub-solar latitudes?? Think: Saturn's ring shadow appears on the hemisphere facing the sun, offset from the equator — the rings between the sun and the planet cast onto the planet: the ring material sunward of the planet (at radius where the sun's rays pass through the ring plane before hitting the planet). The sun is above the plane; rays travel downward at 15°; they pass through the ring plane on the sun side at radius ≈ planetRadius... the shadow of the inner ring portions lands near the equator on the day side, curving. My analytic function handles it exactly ✓. Visually: a soft dark band near the equator on the day side — subtle, believable.

Ring pattern size: inner 15, outer 26 — planet radius 10: rings start 1.5 planet radii ✓ Saturn-like.

Also gap: ring gap at x=0.62 → r = 15+0.62*11 = 21.8 ✓.

Now — writing the code with attention to compile-correctness:

Common vertex shader (shared for planet, clouds, rings, moon, atmosphere):
```glsl
varying vec3 vObjPos;
varying vec3 vWorldPos;
varying vec3 vNormal;
void main(){
  vObjPos = position;
  vec4 wp = modelMatrix * vec4(position, 1.0);
  vWorldPos = wp.xyz;
  vNormal = normalize(mat3(modelMatrix) * normal);
  gl_Position = projectionMatrix * viewMatrix * wp;
}
```
For the sun billboard: custom vertex (view-space quad):
```glsl
uniform float uSize;
varying vec2 vUv;
void main(){
  vUv = uv;
  vec4 mv = modelViewMatrix * vec4(0.0, 0.0, 0.0, 1.0);
  mv.xy += position.xy * uSize;
  gl_Position = projectionMatrix * mv;
}
```
PlaneGeometry(2,2) gives position.xy in [-1,1] ✓.

Sun fragment:
```glsl
uniform float uDim; uniform float uTime;
varying vec2 vUv;
void main(){
  vec2 p = vUv * 2.0 - 1.0;
  float r = length(p);
  float core = exp(-r * r * 90.0) * 3.0;
  float glow = exp(-r * r * 7.0) * 0.55;
  float halo = exp(-r * 2.5) * 0.18;
  float streakH = exp(-abs(p.y) * 34.0) * exp(-abs(p.x) * 3.1);
  float streakV = exp(-abs(p.x) * 40.0) * exp(-abs(p.y) * 4.0) * 0.5;
  vec3 warm = vec3(1.0, 0.78, 0.50);
  vec3 hot  = vec3(1.0, 0.94, 0.86);
  vec3 col = hot * core + warm * glow + warm * halo;
  col += vec3(1.0, 0.62, 0.30) * (streakH * 0.9 + streakV * 0.45);
  col *= uDim;
  gl_FragColor = vec4(col, 1.0);
  tonemap includes
}
```
Blending additive, transparent true (so it doesn't write... set depthWrite false, transparent true, depthTest true).

Ghosts overlay shader:
```glsl
uniform vec3 uTint; uniform float uVis; uniform float uRing; uniform float uSoft;
varying vec2 vUv;
void main(){
  vec2 p = vUv * 2.0 - 1.0;
  float r = length(p);
  float disc = smoothstep(1.0, 1.0 - uSoft, r); // soft edge
  float ring = uRing > 0.0 ? exp(-pow((r - 0.8) * 9.0, 2.0)) * 0.8 : 0.0;
  float a = (disc * 0.55 + ring) * uVis;
  gl_FragColor = vec4(uTint * a, 1.0);
}
```
Hmm — parameterize per ghost: uTint (vec3), uVis, uSoft, uRing. Use PlaneGeometry(2,2) covering... simpler: PlaneGeometry(1,1) scaled by mesh.scale; vUv covers the quad ✓.

Halo (screen-space): bigger soft disc:
```glsl
float r = length(p);
float a = exp(-r*r*3.0) * 0.35 * uVis;  // wide
+ ring at r≈0.9 faint
```

Streak (screen-space): plane scaled (aspect*1.8, 0.06):
```glsl
p = vUv*2-1; a = exp(-abs(p.y)*p.y? : a = exp(-p.y*p.y*60.0) * exp(-abs(p.x)*2.6) * uVis;
```

Vignette: PlaneGeometry(2,2) at z=0 covering... with ortho camera (-a, a, 1, -1): a full-screen quad = PlaneGeometry(2*a, 2) positioned at (0,0) ✓ (update on resize).
```glsl
vec2 p = vUv*2-1; p.x *= uAspect; // correct for aspect so corners darken
float d = length(p * vec2(1.0, 1.0));  hmm vignette should be elliptical matching the screen: with x scaled by aspect, length(p) is radius in "height units": corner = sqrt(1+aspect²)... 
float v = smoothstep(0.55, 1.25, d);
gl_FragColor = vec4(vec3(0.0), v * 0.38);
```
With normal blending ✓ (transparent: true).

Also — subtle letterbox? no.

Stars: 
```js
const N = 7000;
positions: random direction * radius (1500 + 700*rand^0.5?) — vary distance 1400-2200.
aSize: mostly 1-2, power law: size = (0.6 + 2.6*Math.pow(Math.random(), 3)) → few big.
colors: temp mix: 
  const c = new THREE.Color();
  pick: 70% white-ish (1,1,1)*b, 15% blue (0.75,0.85,1), 15% warm (1,0.85,0.65); brightness varied 0.5-1.
aPhase random; aTw speed 0.5-2.5 (some zero → steady).
```
Star vertex:
```glsl
attribute float aSize; attribute vec3 aCol; attribute float aTw; attribute float aPh;
uniform float uTime, uPR;
varying vec3 vCol; varying float vTw;
void main(){
  vCol = aCol;
  vTw = 0.78 + 0.22 * sin(uTime * aTw + aPh);
  vec4 mv = modelViewMatrix * vec4(position, 1.0);
  gl_PointSize = aSize * uPR;
  gl_Position = projectionMatrix * mv;
}
```
fragment:
```glsl
vec2 pc = gl_PointCoord * 2.0 - 1.0;
float d = dot(pc, pc);
float a = smoothstep(1.0, 0.0, d);
a = a * a; // softer
gl_FragColor = vec4(vCol * vTw * a, 1.0);  // additive
```
Additive blending, depthWrite false, transparent true. Include tonemapping? For stars it's fine to include.

Star sizes in px: with uPR (pixelRatio) — aSize 1→1px *PR... At DPR 2, sizes 2-7px — good.

Nebula shader:
```glsl
varying vec3 vObjPos; (use common vertex)
vec3 v = normalize(vObjPos);
float band = exp(-pow(dot(v, uBandN), 2.0) * 7.0);
float n1 = fbm(v * 2.6 + vec3(3.0, 11.0, 5.0));
float n2 = fbm(v * 6.3 + vec3(23.0, 4.0, 17.0));
float n3 = fbm(v * 13.0 + vec3(9.0, 31.0, 2.0));
vec3 col = vec3(0.004, 0.008, 0.012);
col += vec3(0.020, 0.075, 0.090) * band * (0.35 + 0.65 * smoothstep(-0.2, 0.7, n1));
col += vec3(0.055, 0.022, 0.058) * band * smoothstep(0.1, 0.8, n2) * 0.7;
col += vec3(0.020, 0.040, 0.048) * smoothstep(0.3, 0.9, n3) * 0.5 * (0.4+0.6*band);
gl_FragColor = vec4(col, 1.0);
```
This is OPAQUE (regular blending) — it's the sky background, drawn at radius 2400, depthWrite true? If opaque with depth, stars at 2200 max must be inside ✓ set stars radius ≤ 2200 < 2400 ✓. Fine. Or make it depthWrite false + renderOrder -10 with stars renderOrder -9... Since the nebula sphere encloses everything and it's opaque, normal depth testing works: the nebula is the farthest thing; everything renders in front ✓. Keep depthWrite true, render first (renderOrder -10) — actually opaque objects render front-to-back sorted; fine either way.

Hmm — one caveat: the sun billboard is at 900 with depthTest true — stars at ~2000 are behind it: the sun's additive glow doesn't write depth ✓ stars show through the glow — acceptable (glow is additive; stars add on top — fine).

Moon: SphereGeometry(1.7, 48, 48)? Wait — MOON_R = 1.5. Let me finalize: moon radius 1.55.

Planet: SphereGeometry(10, 96, 96) — smooth silhouette needed for the atmosphere; 64 segments fine; use 80.

Clouds: SphereGeometry(10.35, 72, 72).
Atmosphere shell: SphereGeometry(11.4, 64, 64) — planetR 10, shellR 11.4.
Rings: RingGeometry(15, 26, 256, 1) — theta segments 256 for smooth bands radially? RingGeometry's radial resolution: segments = 256 around theta; the band detail comes from the shader (per-pixel radial) ✓ — but the mesh's radial segmentation (1) means the triangles are big annular sectors; per-pixel shader computes r from position ✓ fine. Actually RingGeometry UVs irrelevant. Need positions: object space XY ✓.

Wait — ring shadow function uses distance from origin in the ring PLANE: q = p + sunDir*t where t chosen so dot(q, n) = 0 ✓ then r = length(q) ✓ — q is in the plane through origin ✓.

The tilt group contains rings; ring world normal constant: group rotation z = -0.18 → normal (0,1,0) rotated: R_z(-0.18)*(0,1,0) = (sin(-0.18)*(-1)?? R_z(θ) = [[c,-s],[s,c]] for (x,y): (0,1) → (-sinθ, cosθ). θ=-0.18: (-sin(-0.18), cos(-0.18)) = (0.179, 0.984). So uRingNormal = (0.179, 0.984, 0) ✓. I could also compute it via the ring mesh's matrix each frame — cleaner to just compute once: ringNormal = new Vector3(0,1,0).applyAxisAngle(z-axis, -0.18)... but the group also has no other rotation ✓.

Also the PLANET tilt means the planet's rotation axis is the group's Y — the planet mesh child rotates about its local Y ✓; the noise latitude uses sp.y (object space) = polar caps at the group's poles ✓ consistent with rings (same group) ✓✓. 

Moon orbit: independent tilt about X by -0.32 — visually crossing above/below the rings. OK.

Now — the "camera looks at" target: origin, but with the moon transit moments, the composition is automatic ✓.

Extra polish idea: slow FOV breathing? skip.

Bloom? No postprocessing deps (EffectComposer would need addons — allowed: 'three/addons/postprocessing/...' — but let's keep it dependency-light; the sun glow + flare give enough bloom feel).

Let me now also double-check the moon's lighting during the silhouette crossing: backlit → thin crescent on the sun side (right side if sun is to the right of the planet from the camera). Good.

Also during t≈10-16, is the moon in front of the planet dark against the DAY side? The camera at t≈12 is at az ≈ 0.84, sun az 0.42 → the visible hemisphere is mostly day ✓ dark silhouette contrast ✓.

Also — the moon shadow on the PLANET: moonShadow() is called with the sun DIRECTION (directional). The moon at distance 30-44 from the planet: a real point-ish sun would make the umbra shrink, but directional approximation is fine stylistically.

Potential visual bug: the moon between camera and planet ALSO blocks... no shadowing of the camera view — fine.

Now write the ring geometry with proper radial segment count: RingGeometry(15, 26, 256, 8) — 8 radial segments for vertex interpolation smoothness (not needed but harmless).

One more consideration — the moon might pass in front of the SUN visually (between camera and sun) — rare alignment; ignore.

Also, the planet's specular glint: with the camera near the sun azimuth around t≈10-18, the ocean glint appears near the sub-solar point — visible sparkle ✓.

Let me also add a subtle "terminator glow" — already via twil rim ✓.

Star density near the band: distribute 55% of stars concentrated near the band plane (galactic band) — matches the nebula band → cohesive sky ✓: for 55% of stars, generate direction, then pull toward the band plane: dir = normalize(dir - bandN * dot(dir,bandN)*0.85 + small jitter) → concentrated near the plane. 

Resize: update flare ortho camera: `flareCam.left = -aspect; flareCam.right = aspect; flareCam.top = 1; flareCam.bottom = -1; flareCam.updateProjectionMatrix();` and vignette uAspect + rebuild the background quad scale: the vignette quad covers x ∈ [-a, a]: make its geometry PlaneGeometry(2,1) and scale.set(aspect*... simpler: on resize, set vignette.scale.set(aspect, 1, 1) with PlaneGeometry(2,2) → covers [-a,a]×[-1,1] ✓. And its shader multiplies p.x by uAspect uniform for circular falloff ✓.

Full-screen streak positions use ndc.x*aspect ✓ update per frame anyway.

Halo quad geometry PlaneGeometry(2,2) scaled to size.

Now — the ANIMATE loop:

```js
function animate(ts){
  requestAnimationFrame(animate);
  const t = ts * 0.001;  // seconds from rAF timestamp ✓ requirement
  // planet spin
  planet.rotation.y = t * 0.021;
  clouds.rotation.y = t * 0.029 + 1.7;
  moonMesh.rotation.y = -(ma) ... just spin: moonMesh.rotation.y = t*0.05;
  // moon position
  const ma = MOON_A0 + MOON_W * t;
  moonPos.set(Math.cos(ma)*MOON_R, -Math.sin(ma)*MOON_R*Math.sin(MOON_INC), Math.sin(ma)*MOON_R*Math.cos(MOON_INC));
  moonMesh.position.copy(moonPos);
  // sky slow rotation
  sky.rotation.y = t * 0.004;
  // camera
  const az = CAM_AZ0 - CAM_W * t;
  const r = 40 - 5*Math.exp(-0.09*t) + 1.4*Math.sin(0.11*t);
  const y = 2.2 + 4.2*Math.sin(0.09*t + 0.7);
  camera.position.set(Math.cos(az)*r, y, Math.sin(az)*r);
  lookTarget.set(Math.sin(t*0.05)*1.5, Math.sin(t*0.037)*1.0, Math.cos(t*0.041)*1.5); — hmm keep subtle: small drift around origin.
  camera.lookAt(lookTarget);
  camera.updateMatrixWorld();
  // uniforms
  uTime.value = t; uMoonPos.value.copy(moonPos);
  updateFlare(t);
  renderer.clear();
  renderer.render(scene, camera);
  renderer.render(flareScene, flareCam);
}
requestAnimationFrame(animate);
```
Start t=0 at first frame ✓ auto-start ✓.

Wait — one issue: `ts` on the first frame is the time since page load — small ✓.

Clouds rotating faster than the planet: relative drift 0.008 rad/s → 0.24 rad in 30s (14°) — subtle relative motion ✓ good.

Star twinkle time: pass uTime ✓.

Now let me double-check moonShadow usage in the CLOUD shader too — clouds are at radius 10.35; shadow ray toward the sun from a cloud fragment — moon at 30-44 — occlusion happens when the moon is between — during the eclipse the clouds darken too ✓ consistent with the planet beneath ✓.

Ring shadow on clouds: rSh ✓.

Now, the PLANET fragment's `ringShadow` uses `uSunDir` — note: at the terminator/night side, ringShadow shouldn't matter (diffuse ≈ 0) — fine.

Edge case: GLSL `if (...) return;` before assigning gl_FragColor — allowed ✓.

Precision: default highp in fragment via ShaderMaterial? three sets precision highp by default ✓.

Now think about the moon's appearance scale: moon radius 1.5 at distance ≥ 8 from camera: max angular ~10.6°. During the crossing at t≈11, the moon is ~9.5 from the camera → ~9° radius → 18° diameter vs planet 29° diameter: the moon covers (18/29)² ≈ 38% area — big but OK. Hmm — actually let me double-check the moon-cam distance at t=11 more carefully since it determines whether the moment is cool or absurd.

t=11: cam az θ = 1.591 - 0.0628*11 = 1.591-0.691 = 0.900. r = 40 - 5 e^{-0.99} + 1.4 sin(1.21) = 40 - 1.858 + 1.315 = 39.46. cam y = 2.2+4.2 sin(0.09*11+0.7) = 2.2+4.2 sin(1.69) = 2.2 + 4.165 = 6.37. cam = (39.46 cos0.9, 6.39, 39.46 sin0.9) = (39.46*0.6216, 6.39, 39.46*0.7833) = (24.52, 6.39, 30.90).
Moon at t=11: a = -0.80 + 0.1496*11 = 0.8456. cos = 0.6627, sin = 0.7489. pos = (30*0.6627, 30*0.3146*0.7489, 30*0.7489*0.9492) = (19.88, 7.07, 21.33).
Δ = cam - moon = (4.64, -0.68, 9.57) → |Δ| = 11.53. Moon angular radius = atan(1.5/11.5) = 7.4° → diameter ~15°. Planet angular radius: atan(10/39.5)=14.2° → diameter 28°. Moon covers ~26% of the disc linearly — reads as a substantial moon transit ✓ not absurd. 

And at closest approach — relative az crosses 0 at t=11.26 → distance ≈ 39.5-30 = 9.5 → similar. OK good.

Also check the moon doesn't clip INTO the planet visually during crossing: moon at radius 30, planet 10 — no intersection ✓. Moon crossing the ring plane? The moon's orbit tilt keeps it off the ring plane except at a=0, π where y=0 and radius 30 > 26 (ring outer) ✓ no intersection ✓.

Now — does the moon's shadow land visibly during the crossing? Shadow peak t=8.6 (before the moon enters the frame at t≈10). Slight mismatch but the shadow (t 6.1-11.1) overlaps the crossing (t≈10-13) partially ✓. Good enough — both events clearly within the window and overlapping.

Hmm, actually let me reconsider MOON_A0 so the shadow peak coincides better with the silhouette crossing: silhouette crossing centered t≈11.3 (rel az = 0). If I want the shadow peak at t≈10.5: a* = 0.48 at t=10.5 → a0 = 0.48 - 0.1496*10.5 = 0.48-1.571 = -1.091. Then the shadow spans t ∈ [8.0, 13.0], peak 10.5 ✓ overlapping the moon's face crossing (9.5-13) — shadow visible slightly leading the moon ✓ realistic (umbra precedes/follows the moon depending on geometry — close enough).

Relative az = 0 at t=11.26 unchanged (depends on a0 - θ0: -1.091... wait rel az = (a0 - θ0) + (wm + w)t = (-1.091 - 1.591) + 0.2124t = -2.682 + 0.2124t → 0 at t = 12.63. Hmm shifting a0 shifts the crossing: crossing t = 2.682/0.2124 = 12.63. And occultation (rel = π): t = (3.1416+2.682)/0.2124 = 27.4s ✓ still in window (occultation ~26-29s). Shadow: a(t) = -1.091+0.1496t; a* = 0.48 → t = 8.56... wait: t = (0.48+1.091)/0.1496 = 10.50 ✓ as designed. Shadow on-disc window: |a-0.48| < 0.376 → a ∈ (0.104, 0.856) → t ∈ ((0.104+1.091)/0.1496, (0.856+1.091)/0.1496) = (7.99, 13.02) ✓ peak 10.5s, moon crossing center 12.6s — the shadow leads slightly; the moon visually crosses 10.5-15s. 

And the moon's phase during the crossing: sun-moon-camera geometry: at t=12.6: moon az = a = -1.091+0.1496*12.63 = 0.798; cam az = 1.591-0.793 = 0.798 ✓ aligned. Moon pos: (30cos0.798, 30*0.3146 sin0.798, 30 sin0.798 cos0.32) = (30*0.6976, 7.527, 30*0.7164*0.9492) = (20.93, 7.53, 20.41). cam: r = 40-5e^{-1.137}+1.4 sin(1.389) = 40-1.713+1.378 = 39.66; y = 2.2+4.2 sin(0.09*12.63+0.7) = 2.2+4.2 sin(1.837) = 2.2+4.134 = 6.33; cam = (39.37*0.6976... r cos θ = 39.37*0.6976 = 27.46?? r = 39.37: x = 27.47, z = 39.37*0.7165 = 28.21, y = 6.13. Δcam-moon = (6.54, -1.40, 8.06) → dist = 10.45. Moon angular radius atan(1.5/10.45) = 8.2° ✓ good.
Moon lit phase: direction moon→sun ≈ s; direction moon→cam = -Δ̂ = (-0.626, 0.134, -0.771). s·(-Δ̂) = (0.8796*-0.655... compute: Δ̂ = (0.626, -0.134, 0.771); -Δ̂ = (-0.626... let me: Δ = (6.54, -1.40, 8.06): |Δ| = sqrt(42.8+1.96+64.9) = sqrt(109.2) = 10.45; Δ̂ = (0.626, -0.134, 0.738). moon→cam = -Δ̂ = (-0.626, 0.134, -0.738). s·(moon→cam) = 0.8796*(-0.626) + 0.2639*0.134 + 0.3958*(-0.738) = -0.550 + 0.0354 - 0.292 = -0.807 → phase angle 143.8° → thin crescent (5-10% lit) ✓ beautiful backlit silhouette with a delicate rim ✓.

Also — the crescent side faces the sun; sun az 0.422 vs the moon's screen position (center of the planet disc) — the sun appears to the upper-left/right of the planet at ~30° separation ✓ so the crescent rim faces the sun — coherent ✓.

Great, the choreography is solid. Now — check that during t≈6-13 the camera actually has the shadow region in view: the shadow lands near the sub-solar area offset 3.8 units toward... the shadow center at closest approach is 3.79 from the planet center, in the direction perpendicular to the sun axis within... the shadow line from the moon: closest point to origin = moonPos - s*(moonPos·s)... the shadow falls around the point Q0 = origin + (component of moonPos perpendicular to s)?? The umbra axis passes through the point P0 = moonPos - s*(moonPos·s) (the closest point on the line to the origin) — wait the line is p(t) = moonPos - s*τ; distance to origin minimized at τ = moonPos·s; P0 = moonPos - s*(moonPos·s), |P0| = 3.79 ✓. The shadow center on the planet surface ≈ along -P0 direction?? The shadow region on the sphere: points where the ray toward the sun hits the moon: near the surface point in direction -P0̂... roughly the shadow appears on the day side around the sub-moon point = the point where the moon is overhead = normalize(moonPos) direction... shadow lands near the sub-moon point (normalized moonPos projected on sphere) ✓ which is on the day side (moon between sun and planet ✓). Camera at separation 30-40° sees it ✓.

Good. Now, is the sun in frame during the shadow peak (t≈10.5)? separation |0.422 - (1.591-0.0628*10.5)| = |0.422-0.932| = 0.51 rad = 29° + sun elevation 15° vs camera y≈6.4 (elev 9°): sun ~6° above the camera's horizontal plane... total angular offset from the look axis ≈ sqrt(30² + ~10²)?? The look direction is toward the origin (slightly downward from the camera). The sun's offset from that axis: azimuth difference 29°, elevation difference ~ (15° - (-8°))?? The look direction points DOWN toward the origin from y=6.4 at distance 39.5 → depression angle atan(6.4/39) ≈ 9.3°. The sun is at elevation +15° → relative elevation ≈ 24°. Total offset ≈ sqrt(29² + 24²) ≈ 37.6° — within half-hFov 43° (16:9) but outside half-vFov 27.5°! So on a 16:9 screen, the sun is in frame horizontally but 24° up — vFov half = 27.5° → the sun IS within the vertical FOV (24 < 27.5) — visible in the upper portion ✓ (on 16:9). On narrower windows it may be cropped — acceptable.

Hmm, but wait — I should double check the vertical framing: the camera looks at the origin; the planet (radius 10 at distance 39.5) spans ±14.6° vertically — fits within 27.5° ✓ with headroom. The rings (radius 26) span atan(26/39.5) = 33.3° > 27.5° → rings slightly crop top/bottom edges at 16:9 — actually the rings are near-edge-on so their vertical extent is small: the ring's projected vertical extent ≈ outer radius * sin(elevation) — elevation of the camera relative to the ring plane ≈ y/r adjusted for tilt ~ 6-12° → vertical extent tiny ✓ fits easily. Horizontally the rings span 33° < 43° ✓.

Now — cloud shadowing by the moon during the eclipse: clouds darken too ✓ consistent.

Ring shadow on the planet visibility: with the sun 15° above the ring plane (effective elevation relative to the tilted plane: s·n = 0.8796*0.179 + 0.2639*0.984 = 0.157+0.260 = 0.417 → 24.6° above the ring plane! (the tilt raised the effective elevation) — the ring shadow band falls at latitude... the shadow of the ring annulus: rays passing over the ring inner edge at radius 15 hit the planet at... the shadow band position: for a flat ring in the plane with the sun at elevation e above the plane, the ring shadow on the planet appears at the latitude band where the planet's surface is shadowed by the annulus between inner radius Rin and the planet: the shadow band lies on the anti-sun side, centered around latitude ≈ -e-ish?? For Saturn with the sun above the rings, the ring shadow is on the southern hemisphere when... honestly the analytic function handles it; with e≈15°, the shadow band sits at southern mid-latitudes on the day side... wait: rays come FROM the sun direction (0.88, 0.26, 0.40): they travel along -s... a ray hitting a ring point at radius r in the plane continues down at 15° below the plane?? s has +y 0.264: rays travel toward -s: y decreases. A ray passing through a ring point at radius r on the SUN side (the ring point between the sun and the planet): the ray enters the plane at that point and continues to y = -10 (planet bottom) after Δy = ... it hits the planet surface if the ray passes within radius 10 of the origin before exiting: horizontal travel while dropping from y=0 to y=-10: 10/tan(15°) = 37 — too far (the planet's horizontal extent is ~10) — hmm: the ray enters the ring plane at horizontal distance r from the center, at height y=0, and drops; it reaches the planet's sphere if the closest approach... The ray direction -s = (-0.88, -0.264, -0.396): starting at (r·cosφ, 0, r·sinφ) on the sun side (φ ≈ sun azimuth 0.422 → the sun-side ring points near azimuth 0.42): start ≈ (r*0.9, 0, r*0.42)?? For the shadow: the ray must hit the sphere x²+y²+z² = 100: parametrize p(τ) = p0 + τ*(-s) — distance² from origin: |p0|² - 2τ(p0·s) + τ² (since |s|=1): min at τ = p0·s — p0 is on the sun side so p0·s > 0 ✓ the ray travels toward -s, going AWAY from the sun: does it pass near the origin? |p(τ)|² = |p0|² - 2τ(p0·s) + τ². Min value = |p0|² - (p0·s)² = perpendicular distance² of the LINE through p0 along s from the origin. p0 is IN the ring plane (y=0), p0·s = horizontal component ≈ r*cos(angle between p0 azimuth and sun azimuth) ≈ r (if aligned). Perp distance = r*sin(angle between the line and...) hmm: the line through p0 (in the y=0 plane) with direction s: its perpendicular distance from the origin: the line passes through p0 = (r, 0, 0) (aligned with the sun azimuth) with direction s = (0.88, 0.264, 0.396): distance² = |p0|² - (p0·s)² = r² - (0.88r)² = r²(1-0.774) = 0.226r² → distance = 0.472r. For the ray to graze the planet (distance 10): r ≈ 21.2. So ring points with radius between ~10.6 (distance < 10 → shadow at 0.472r < 10 → r < 21.2) — i.e., ring radii from the planet's edge... the ring inner radius is 15 → the ring shadow on the planet comes from ring radii r ∈ [10.6?, 21.2]: rays entering the plane at radius r ∈ (10.6, 21.2) on the sun side hit the planet → the ring shadow appears on the planet. And the shadow's position on the planet: where these rays land — southern latitudes (rays descending at 15°). The shadow band will appear south of the equator on the day side ✓ and my function computes it exactly ✓. Also the ring's outer portion (r>21.2) shadows space beyond. And the ANTI-sun side of the rings is in the planet's shadow ✓.

But wait — the effective sun elevation relative to the RING plane is 15.3° in world, but the ring plane is tilted -0.18 rad (10.3°) about Z: the angle between s and the ring normal: cos = s·n̂ = 0.8796*0.179 + 0.2639*0.984 = 0.157+0.260 = 0.417 → elevation ≈ 24.7°. OK so above I should use the geometry with the tilted plane... my rough calc used elevation 15°, close enough — the shadow band exists and is computed exactly ✓.

Now, one more requirement scan: "a small moon orbiting the planet that casts light and shadow interest" — moonlight ✓ (cool fill term), eclipse shadow ✓, planet shadow on moon with red tint ✓, silhouette crossing ✓.

"a distant sun with a lens-flare-like glow" ✓ billboard + screen-space ghosts + halo + streak.

"dense starfield" ✓ 7000.

"camera slowly drifts" ✓.

"requestAnimationFrame timestamp" ✓.

"full-window canvas + resizing" ✓.

"starts automatically" ✓.

"everything important within 30 seconds" ✓ (eclipse 6-15s, flare 10-17s, occultation 26-29s, rings/clouds/stars always, terminator + biolume at 0-5s, ring shadow always on the day side).

Now — WRITE THE CODE. I'll be careful with GLSL syntax (no implicit int/float mixing), and the chunk ordering.

Let me define the shader chunks as JS strings:

```js
const GLSL_NOISE = `
vec3 mod289(vec3 x){ return x - floor(x * (1.0/289.0)) * 289.0; }
vec4 mod289(vec4 x){ return x - floor(x * (1.0/289.0)) * 289.0; }
vec4 permute(vec4 x){ return mod289(((x*34.0)+1.0)*x); }
vec4 taylorInvSqrt(vec4 r){ return 1.79284291400159 - 0.85373472095314 * r; }
float snoise(vec3 v){ ... }
float fbm(vec3 p){
  float f = 0.0;
  float a = 0.52;
  for(int i = 0; i < 5; i++){
    f += a * snoise(p);
    p = p * 2.13 + vec3(19.1, 7.7, 3.3);
    a *= 0.53;
  }
  return f;
}
`;
```
fbm amplitude: a starts 0.52, ×0.53 each: 0.52, 0.276, 0.146, 0.0775, 0.041 → sum ≈ 1.06. Range ±~0.8 typical ±0.35. OK.

Shared shading helpers:
```js
const GLSL_COMMON = GLSL_NOISE + `
uniform vec3 uSunDir;
uniform vec3 uMoonPos;
uniform float uMoonR;
uniform float uPlanetR;
uniform float uRingIn;
uniform float uRingOut;
uniform vec3 uRingN;

float ringPattern(float x){
  float v = snoise(vec3(x*16.0, 3.7, 8.1))*0.55
          + snoise(vec3(x*42.0, 9.2, 3.3))*0.28
          + snoise(vec3(x*7.0, 1.2, 5.5))*0.42;
  v = v*0.5 + 0.5;
  float a = smoothstep(0.16, 0.68, v);
  a *= 0.62 + 0.38*snoise(vec3(x*130.0, 4.4, 9.9));
  a *= 1.0 - 0.92*exp(-pow((x-0.60)*24.0, 2.0));
  a *= 1.0 - 0.55*exp(-pow((x-0.84)*34.0, 2.0));
  a *= smoothstep(0.0, 0.05, x)*(1.0 - smoothstep(0.93, 1.0, x));
  return clamp(a, 0.0, 1.0);
}

float moonShadow(vec3 p){
  vec3 oc = uMoonPos - p;
  float along = dot(oc, uSunDir);
  if(along <= 0.0) return 1.0;
  float d = length(oc - uSunDir*along);
  return smoothstep(uMoonR*0.5, uMoonR*1.7, d);
}

float planetShadow(vec3 p){
  float along = dot(-p, uSunDir);
  if(along <= 0.0) return 1.0;
  float d = length(p + uSunDir*along);
  return smoothstep(uPlanetR*0.88, uPlanetR*1.28, d);
}

float ringShadow(vec3 p){
  float denom = dot(uSunDir, uRingN);
  if(abs(denom) < 0.0001) return 1.0;
  float t = -dot(p, uRingN)/denom;
  if(t <= 0.0) return 1.0;
  float r = length(p + uSunDir*t);
  float x = (r - uRingIn)/(uRingOut - uRingIn);
  if(x < 0.0 || x > 1.0) return 1.0;
  return 1.0 - ringPattern(x)*0.55;
}
`;
```
Note: `pow((x-0.60)*24.0, 2.0)` — pow with negative base is undefined! Must avoid: use squared multiplication: `float g = (x-0.60)*24.0; a *= 1.0 - 0.92*exp(-g*g);` ✓ fix that.

Also in sun shader: `exp(-r*r*90)` fine.

Planet fragment — write it fully:

```glsl
varying vec3 vObjPos;
varying vec3 vWorldPos;
varying vec3 vNormal;
uniform float uTime;
${GLSL_COMMON}
void main(){
  vec3 sp = normalize(vObjPos);
  vec3 N = normalize(vNormal);
  vec3 V = normalize(cameraPosition - vWorldPos);

  // --- terrain ---
  float cont = fbm(sp*1.5 + vec3(11.0, 3.0, 27.0));
  float det  = fbm(sp*5.2 + vec3(2.0, 14.0, 5.0));
  float mrange = 1.0 - abs(snoise(sp*3.1 + vec3(31.0, 13.0, 7.0)));
  mrange *= mrange;
  float sea = 0.06;
  float h = cont*0.78 + det*0.22;
  float landMask = smoothstep(sea - 0.004, sea + 0.035, h);
  h += mrange*0.32*landMask*smoothstep(sea + 0.02, sea + 0.24, h);

  float depth = clamp((sea - h)*3.4, 0.0, 1.0);
  vec3 ocean = mix(vec3(0.055, 0.40, 0.38), vec3(0.014, 0.15, 0.19), smoothstep(0.0, 0.30, depth));
  ocean = mix(ocean, vec3(0.004, 0.042, 0.072), smoothstep(0.30, 0.78, depth));

  float bio = fbm(sp*2.6 + vec3(47.0, 8.0, 21.0));
  vec3 moss = vec3(0.11, 0.185, 0.095);
  vec3 rust = vec3(0.375, 0.185, 0.08);
  vec3 land = mix(rust, moss, smoothstep(-0.35, 0.42, bio));
  land = mix(land, vec3(0.35, 0.30, 0.235), smoothstep(sea + 0.09, sea + 0.24, h));
  land = mix(land, vec3(0.50, 0.475, 0.45), smoothstep(sea + 0.26, sea + 0.38, h));
  float beach = smoothstep(sea, sea + 0.010, h)*(1.0 - smoothstep(sea + 0.010, sea + 0.035, h));
  land = mix(land, vec3(0.55, 0.45, 0.28), beach*0.85);

  float lat = abs(sp.y);
  float capN = fbm(sp*3.4 + vec3(5.0, 41.0, 17.0));
  float polar = smoothstep(0.70, 0.80, lat + capN*0.12);
  float snowy = smoothstep(sea + 0.30, sea + 0.42, h);
  float ice = clamp(polar + snowy*0.9, 0.0, 1.0);
  vec3 iceCol = mix(vec3(0.84, 0.91, 0.95), vec3(0.62, 0.76, 0.85), smoothstep(0.25, 0.8, det)*0.45);

  vec3 albedo = mix(ocean, land, landMask);
  albedo = mix(albedo, iceCol, ice);

  // --- lighting ---
  float NdL = dot(N, uSunDir);
  float day = clamp(NdL, 0.0, 1.0);
  float mSh = moonShadow(vWorldPos);
  float rSh = ringShadow(vWorldPos);
  vec3 sunTint = vec3(1.0, 0.90, 0.78);
  vec3 col = albedo*(vec3(0.010, 0.016, 0.024) + vec3(1.0, 0.90, 0.78)*1.45*day*mSh*rSh);

  vec3 H = normalize(uSunDir + V);
  float ndh = max(dot(N, H), 0.0);
  float glint = pow(ndh, 120.0)*1.3 + pow(ndh, 9.0)*0.12;
  col += vec3(1.0, 0.85, 0.66)*glint*(1.0 - landMask)*(1.0 - ice)*day*mSh*rSh;

  // moonlight
  vec3 toMoon = normalize(uMoonPos - vWorldPos);
  float ml = max(dot(N, toMoon), 0.0);
  col += albedo*vec3(0.10, 0.17, 0.23)*ml*(1.0 - day)*0.9;

  // bioluminescent shorelines
  float night = 1.0 - smoothstep(-0.15, 0.08, NdL);
  float shelf = smoothstep(sea - 0.075, sea - 0.006, h)*(1.0 - landMask);
  float clus  = smoothstep(0.22, 0.62, snoise(sp*6.5 + vec3(61.0, 23.0, 9.0)));
  float spark = smoothstep(0.28, 0.72, snoise(sp*44.0 + vec3(13.0, 51.0, 29.0)));
  col += vec3(0.04, 0.62, 0.44)*shelf*clus*(0.3 + 0.7*sparkle)*night*(1.0 - ice)*0.85;

  // atmospheric rim on the surface
  float fres = pow(1.0 - clamp(dot(N, V), 0.0, 1.0), 2.6);
  float twil = exp(-pow((NdL - 0.06)*3.2, 2.0));
  vec3 rimCol = mix(vec3(0.16, 0.46, 0.55), vec3(0.95, 0.42, 0.16), clamp(twil*1.1, 0.0, 1.0));
  col += rimCol*fres*(0.14 + 0.95*day);

  gl_FragColor = vec4(col, 1.0);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}
```
Wait `pow((NdL - 0.08)*3.2, 2.0)` — again pow negative base issue: `float tw = (NdL - 0.08)*3.2; float twil = exp(-tw*tw);` ✓. And `pow(ndh, 120)` — ndh ≥ 0 ✓ fine. `pow` in fres: base = 1-clamp(...) ≥ 0 ✓.

Note the shoreline glow uses fbm-free cheap noises ✓.

Hmm — one thing: `landMask` used for glint exclusion ✓ included.

Clouds fragment:

```glsl
varying...; uniform float uTime; ${GLSL_COMMON}
void main(){
  vec3 sp = normalize(vObjPos);
  float wa = fbm(sp*2.3 + vec3(7.0, uTime*0.010, 2.0))*1.5;
  float ca = cos(wa), sa = sin(wa);
  vec3 q = sp;
  q.xz = mat2(ca, -sa, sa, ca)*sp.xz;
  float d1 = fbm(q*3.0 + vec3(3.0, 12.0, 7.0 + uTime*0.015));
  float d2 = fbm(q*7.6 + vec3(21.0, 4.0, 15.0 - uTime*0.02));
  float cover = smoothstep(0.02, 0.52, d1*0.72 + d2*0.38 + 0.12);
  if(cover < 0.004) discard;
  vec3 N = normalize(vNormal);
  float NdL = dot(N, uSunDir);
  float day = clamp(NdL*0.85 + 0.15, 0.0, 1.0);
  float shade = 0.62 + 0.38*smoothstep(-0.4, 0.7, d2);
  float mSh = moonShadow(vWorldPos);
  float rSh = ringShadow(vWorldPos);
  vec3 col = mix(vec3(0.030, 0.045, 0.075), vec3(1.02, 1.0, 0.97)*shade*1.18, day);
  col *= mix(0.22, 1.0, mSh)*mix(0.42, 1.0, rSh);
  // faint warm edge at terminator
  float tw = (NdL - 0.05)*2.8;
  col += vec3(0.35, 0.14, 0.05)*exp(-tw*tw)*0.25*day?? hmm...
```
Terminator tint: `col += vec3(0.45, 0.18, 0.07) * exp(-tw*tw) * 0.3;` small. Also alpha:
```glsl
  float alpha = cover*0.94;
  gl_FragColor = vec4(col, alpha);
  includes
}
```
Cloud fbm count: wa(5) + d1(5) + d2(5) = 15 ✓.

Cloud drift: uTime in noise + mesh rotation ✓.

Atmosphere fragment:

```glsl
varying vec3 vWorldPos;
uniform float uPlanetR;
uniform float uShellR;
${GLSL_NOISE not needed}
void main(){
  vec3 C = cameraPosition;
  vec3 D = normalize(vWorldPos - C);
  float tc = -dot(C, D);
  vec3 closest = C + D*tc;
  float b = length(closest);
  float x = clamp((b - uPlanetR)/(uShellR - uPlanetR), 0.0, 1.0);
  float glow = pow(1.0 - x, 2.4);
  vec3 rn = normalize(closest);
  float sd = dot(rn, uSunDir);
  float day = clamp(sd*0.7 + 0.42, 0.03, 1.0);
  float tw = (sd - 0.04)*2.6;
  float twil = exp(-tw*tw);
  vec3 col = mix(vec3(0.16, 0.50, 0.60), vec3(1.0, 0.40, 0.14), clamp(twil*1.2, 0.0, 1.0));
  float fwd = pow(max(dot(D, uSunDir), 0.0), 3.0);
  vec3 c = col*glow*day*1.5 + vec3(1.0, 0.5, 0.2)*fwd*glow*0.5;
  gl_FragColor = vec4(c, 1.0);
  includes
}
```
Hmm — uSunDir needed → include GLSL_COMMON or declare uniform separately. I'll include the full common (unused functions get compiled but tree-shaken? GLSL compiles all — unused functions are fine, minor compile cost). To keep compile times low I'll make a smaller chunk for atmosphere with just the uniform declaration. Actually simplest: include GLSL_COMMON everywhere that needs uSunDir etc.; the atmosphere only needs uSunDir. I'll create `GLSL_UNIFORMS` (uniform declarations + helper funcs) and `GLSL_NOISE` separately; compose as needed. Fine.

But note: multiple ShaderMaterials each compiling snoise — total compile time OK.

Also — the atmosphere shell with BackSide: does `varying vNormal` matter? Not used in the b-parameter approach ✓ drop it (use the common vertex though — fine).

Wait — one issue with the b-parameter atmosphere: the additive shell covers the whole planet disc too (rays with b < planetR hit the far shell BEHIND the planet — occluded by depth ✓ since planet renders first (opaque) and the shell is transparent (renders after opaque with depthTest ✓). Rays with b slightly > planetR pass close to the limb — glow ✓. Rays with b up to shellR (11.4) — the outer fade ✓. But ALSO the FRONT hemisphere of the shell is culled (BackSide) — rays with b < shellR hit the far side ✓ always. ✓.

Rings fragment:

```glsl
varying vec3 vObjPos; varying vec3 vWorldPos; varying vec3 vNormal(needed? normal = uRingN constant — pass uniform);
uniform float uTime; ${GLSL_COMMON}
void main(){
  float r = length(vObjPos.xy);
  float x = (r - uRingIn)/(uRingOut - uRingIn);
  float a = ringPattern(x);
  if(a < 0.004) discard;
  vec3 V = normalize(cameraPosition - vWorldPos);
  float ndl = dot(uRingN, uSunDir);
  float li = 0.32 + 0.95*abs(ndl);
  if(ndl < 0.0) li *= 0.6;
  float fwd = pow(max(dot(-V, uSunDir)... 
```
forward scatter: view direction from camera to fragment = -V; if the fragment is between camera and sun... brightness when looking toward the sun through the rings: dot(-V, uSunDir) — hmm: looking TOWARD the sun means the view ray direction ≈ sunDir: viewRayDir = normalize(vWorldPos - cameraPosition) = -V. fwd = pow(max(dot(-V, uSunDir), 0.0), 4.0)*1.1.
```glsl
  li += fwd;
  float psh = planetShadow(vWorldPos);
  vec3 col = mix(vec3(0.52, 0.46, 0.38), vec3(0.34, 0.325, 0.31), x);
  col *= li*psh;
  col *= vec3(1.05, 0.98, 0.90);
  gl_FragColor = vec4(col, a*0.95);
  tonemap
}
```
Hmm — rings lit by moonlight? skip.

Also the ring inner edge close to the planet gets planetshine? skip.

Moon fragment:

```glsl
varying...; ${GLSL_COMMON}
void main(){
  vec3 sp = normalize(vObjPos);
  float m1 = fbm(sp*3.2 + vec3(9.0, 2.0, 17.0));
  float m2 = fbm(sp*8.5 + vec3(27.0, 5.0, 3.0));
  float mare = smoothstep(0.18, 0.6, fbm(sp*1.6 + vec3(51.0, 13.0, 7.0)));
  vec3 albedo = mix(vec3(0.54, 0.52, 0.49), vec3(0.33, 0.31, 0.29), clamp(m1*0.5 + 0.5, 0.0, 1.0));
  albedo = mix(albedo, vec3(0.23, 0.235, 0.27), mare*0.75);
  albedo *= 0.88 + 0.24*clamp(m2*0.5+0.5, 0.0, 1.0);
  vec3 N = normalize(vNormal);
  float ndl = max(dot(N, uSunDir), 0.0);
  float psh = planetShadow(vWorldPos);
  vec3 col = albedo*(vec3(0.006, 0.008, 0.012) + vec3(1.0, 0.93, 0.85)*1.35*ndl*psh);
  col += albedo*vec3(0.55, 0.14, 0.05)*ndl*(1.0 - psh)*0.9;
  gl_FragColor = vec4(col, 1.0);
  tonemap
}
```
Add a subtle rim darkening? skip.

Sun shader (as above) — uniforms: uDim, no time needed (static). Maybe slight slow pulsation: skip.

Stars: as above. Note attribute name `color` conflicts? I use custom aCol ✓.

Nebula: as above with GLSL_NOISE (fbm). uBandN uniform.

Flare ghost shader (screen):
```glsl
uniform vec3 uTint; uniform float uVis; uniform float uFall; // falloff
varying vec2 vUv;
void main(){
  vec2 p = vUv*2.0 - 1.0;
  float r2 = dot(p, p);
  float disc = exp(-r2*uFall);
  float ring = exp(-pow(r2 - 0.62, 2.0)... 
```
again pow-negative: r2-0.62 could be negative → use: `float g = (r2 - 0.62)*7.0; float ring = exp(-g*g)*0.55*step(0.0, uRingAmt)`... pass uRingAmt as uniform (0 or 1). Let me write:
```glsl
uniform float uRingAmt;
void main(){
  vec2 p = vUv*2.0 - 1.0;
  float r2 = dot(p,p);
  float disc = exp(-r2*uFall);
  float g = (r2 - 0.55)*6.0;
  float ring = exp(-g*g)*uRingAmt*0.6;
  float a = (disc + ring)*uVis;
  gl_FragColor = vec4(uTint*a, 1.0);
}
```
No tonemap include (screen overlay; keep raw — actually additive over tone-mapped backbuffer... the main render already output sRGB-encoded colors; the flare adds linear values on top → slightly brighter than physically consistent, but visually fine and keeps the flare punchy ✓ intentional).

Hmm — the flare overlays are drawn in the sRGB-encoded framebuffer — values I write are treated as sRGB directly. Fine — I'll pick tint values that look right (they're art constants).

Streak shader:
```glsl
uniform float uVis; uniform vec3 uTint;
vec2 p = vUv*2.0-1.0;
float a = exp(-p.y*p.y*220.0)*exp(-abs(p.x)*2.6)*uVis;
gl_FragColor = vec4(uTint*a, 1.0);
```
The streak quad is wide: scale (2.4*aspect? in ortho units x∈[-a,a]) — set scale.x = aspect*1.4, y = 0.05? The falloff exp(-|x|*2.6) with x∈[-1,1] local → visible length ~1.5 units*scale... I'll set scale.x = 2.4 (screen-height units ≈ 1.2*height wide) and tint warm.

Halo shader (screen): disc with uFall small (soft): exp(-r2*2.2)*0.35.

Ghost list config (JS):
```js
const ghosts = [
 { k: 0.4, size: 0.50, tint: [1.0, 0.72, 0.42], fall: 9.0, ring: 0.0, vis: 0.30 },
 { k: -0.30, size: 0.10, tint: [0.35, 0.75, 0.70], fall: 14.0, ring: 1.0, vis: 0.35 },
 { k: -0.62, size: 0.16, tint: [0.55, 0.45, 0.85], fall: 18.0, ring: 1.0, vis: 0.28 },
 { k: -1.05, size: 0.07, tint: [1.0, 0.85, 0.55], fall: 10.0, ring: 0.6, vis: 0.4 },
 { k: -1.45, size: 0.22, tint: [0.30, 0.60, 0.60], fall: 22.0, ring: 1.0, vis: 0.22 },
 { k: -1.9, size: 0.12, tint: [0.85, 0.5, 0.35], fall: 16.0, ring: 0.8, vis: 0.2 },
];
```
Position: (ndc.x*k*aspect?? mirroring: ghostNDC = sunNDC * (-k)?? Earlier: ghost at ndc' = -k*ndc. With k negative → positive multiple → between sun and center... Let me define positions: gx = ndc.x * (-k) * aspectCorrection... in ortho space X = ndc.x*aspect... hmm — mirroring should happen in true screen space (NDC), then convert: X_ortho = ndc'.x * aspect = ndc.x * (-k) * aspect. And Y = ndc'.y = ndc.y*(-k). Size in ortho-y units ✓ (circle stays circular since ortho x-y units are equal ✓).

Wait — is that right? Ortho camera with left=-a, right=a maps X_ortho=a → ndc.x=1 → screen x = W/2*(1+1)... a unit in ortho-x = H/2 pixels? Screen width W = 2a ortho units → 1 ortho unit = W/(2a) = W/(2W/H) = H/2 px ✓ same as ortho-y unit (2 units = H → 1 unit = H/2 ✓). Equal ✓ circles stay circular ✓.

Also halo follows the sun exactly; streak too.

Vignette: fixed quad, scale.x = aspect.

Flare vis:
```js
const sunNDC = _v.copy(sunWorld).project(camera);
camera.getWorldDirection(_dir);
const toSun = _v2.copy(sunWorld).sub(camera.position).normalize();
const front = _dir.dot(toSun) > 0.0 ? 1 : 0; // wait getWorldDirection returns the direction the camera faces ✓ dot > 0 → in front
// occlusion
const tC = -camera.position.dot(toSun)?? careful: tC = dot(-C, D̂) where D̂ = toSun normalized.
const dSun = camera.position.distanceTo(sunWorld);
const tC = _v2.copy(camera.position).negate().dot(toSun); // toSun must be normalized
const closest = _v3.copy(camera.position).addScaledVector(toSun, tC);
const b = closest.length();
let occ = 1 - THREE.MathUtils.smoothstep(b, 10.4, 12.2); // occ=1 fully blocked
```
THREE.MathUtils.smoothstep(x, min, max) ✓ signature (x, min, max) returns 0..1 ✓.
```js
const off = Math.max(Math.abs(sunNDC.x), Math.abs(sunNDC.y));
const edge = 1 - THREE.MathUtils.smoothstep(off, 0.75, 1.5);
const vis = (1 - occ) * edge * (front? 1:0)... front as 0/1 with smooth: keep binary.
sunMat.uniforms.uDim.value = 0.25 + 0.85*(1-occ);  // also maybe *edge? The billboard is world-space; edge fade unnecessary (it's occluded by depth when behind planet; when off-frame it's just off-frame). But when partially occluded the halo around the limb should dim: uDim = 0.25 + 0.75*(1-occ) ✓.
```
Set each ghost/halo/streak uVis = base * flareVis.

Also — ghost positions when sun is behind the planet: (1-occ)=0 → all invisible ✓.

Now sizes: halo size 1.6 ortho units (0.8 screen-heights radius... PlaneGeometry(1,1) scaled 1.6 → half-extent 0.8 units = 0.4 screen heights — with exp falloff the visible glow ~0.25 height ✓. Sun world billboard size: uSize uniform... I used mv.xy += position.xy * uSize with PlaneGeometry(2,2) (position.xy ∈ [-1,1]) → world half-size = uSize. uSize = 130 → angular ≈ 2*130/900 ≈ 0.29 rad ≈ 16.5° full quad; the glow (exp(-r²*7)) reaches ~0.5 of half → visible glow diameter ~8° ✓.

Let me reconsider: at 800 distance... set sunDist = 850, size 150.

Renderer far plane: 6000 (stars 2200, nebula 2400, sun 850 ✓).

Now the starfield band: uBandN shared with nebula: bandN = normalize(0.35, 1.0, 0.18)?? The band is the great circle perpendicular to bandN: stars concentrated where |dot(dir, bandN)| small ✓.

Star distribution code:
```js
for i: 
  let d = randomDir();
  if (i < N*0.55) { // band star
    const dn = d.dot(bandN);
    d.addScaledVector(bandN, -dn*0.82);
    d.normalize();
    d.addScaledVector(randomDir(), 0.08); d.normalize();
  }
  const rad = 1400 + 800*Math.pow(Math.random(), 0.5)?? keep 1500-2300: rad = 1500 + 800*Math.random();
```
Colors:
```js
const t = Math.random();
let col;
if (t < 0.72) col = [1.0, 0.96, 0.92];
else if (t < 0.87) col = [0.72, 0.82, 1.0];
else col = [1.0, 0.80, 0.58];
brightness = 0.35 + 0.65*Math.pow(Math.random(), 1.8);
size = 0.8 + 3.4*Math.pow(Math.random(), 4.0); // px, few big
tw = 0.3 + 1.8*Math.random()*(Math.random()<0.35? 1: 0.15) — simpler: aTw = 0.25+1.6*random; aPh random 0..2π.
```
Big heroes: for ~1% set size 4-6 with slight cross shape? Points are square sprites — round soft ✓.

Star brightness values (additive) — multiply color by brightness ✓ vCol.

Now resize:
```js
function onResize(){
  const w = innerWidth, h = innerHeight;
  renderer.setSize(w, h);
  camera.aspect = w/h; camera.updateProjectionMatrix();
  const a = w/h;
  flareCam.left = -a; flareCam.right = a; flareCam.updateProjectionMatrix();
  vignette.scale.x = a;
  starMat.uniforms.uPR.value = renderer.getPixelRatio();
}
addEventListener('resize', onResize)
```
renderer.setPixelRatio(Math.min(devicePixelRatio, 2)) once + on resize (devicePixelRatio can change on zoom) — call inside resize too ✓.

Orbit line: circle points:
```js
const seg = 256; const pts = [];
for (i<=seg) { a = i/seg*2π; pts.push(new Vector3(cos a*MOON_R, -sin a*MOON_R*Math.sin(INC), sin a*MOON_R*cos INC)); }
LineLoop with LineBasicMaterial({color: 0x2e4a4e, transparent: true, opacity: 0.35});
```
Hmm — precompute in JS with the same tilt ✓.

Moon spin: moonMesh.rotation.y = t*0.06 (arbitrary).

Also add a tiny moon glow when eclipsed? skip.

Now double-check the CLOUD mesh transparency sorting vs the moon crossing IN FRONT of the clouds: moon is opaque, renders in the opaque pass before transparent ✓ depth correct ✓ the moon in front of clouds occludes them ✓; the moon BEHIND the planet: planet occludes ✓. The moon behind the ATMOSPHERE shell: shell is additive, no depth write ✓ the moon seen through the glow gets glow added ✓ natural.

The moon behind the RINGS: rings transparent depthWrite false — the moon (opaque) drawn first; rings blend over it ✓ correct. Rings in front of the moon → rings tint over moon ✓; moon in front of rings (moon at radius 30 > ring outer 26 → the moon is always OUTSIDE the rings, but visually when the moon is behind the planet on the far side at radius 30, and the ring at radius 21-26 near the camera... the moon's line of sight may pass through the ring plane region: rings between camera and moon → rings drawn over the moon ✓ correct since rings render after. When the moon is closer than the rings along the view ray → moon is opaque-drawn first, then rings blend ON TOP even though the rings are behind!! ✗ — depth test! Transparent materials still depth-TEST (depthTest true by default) ✓: the ring fragments behind the moon fail the depth test → discarded ✓. Good — keep depthTest true, depthWrite false ✓.

Cloud sphere vs moon: same logic ✓ (clouds depthTest true).

Ring vs clouds: both transparent, sorted by distance — three sorts transparent objects by renderOrder then z. Rings' centroid is at origin (same as clouds) → sorting ambiguous! Explicit renderOrder: clouds 1, atmosphere 2, rings 3? But when the camera is BELOW the ring plane looking up... the rings vs clouds order flips depending on geometry. Cases: (a) camera above ring plane: the near side of the rings is in front of the planet's upper hemisphere? The rings surround; a ray to the planet's upper area may cross the ring near-side in front → rings should draw over clouds there. If clouds draw first, rings blend over ✓ correct. If rings draw first and clouds over them: the near ring would be dimmed by cloud alpha incorrectly... but where the ring is in FRONT of the clouds, the cloud pixels behind rings still blend UNDER (cloud drawn first, ring adds over ✓). Where clouds are in front of rings (camera below the plane looking up at the southern hemisphere with rings behind): drawing rings after clouds → ring pixels would blend over cloud pixels even though the ring is farther — WRONG unless depth test culls: the cloud fragment wrote... clouds have depthWrite FALSE (transparent) → no depth → the ring behind the clouds still blends over ✗. Hmm. To handle properly: give the CLOUD material depthWrite: true? Transparent with depthWrite true causes issues with its own sorting vs atmosphere... Alternative: render order fixed: atmosphere(1) → clouds(2) → rings(3), and accept that when the camera is below the ring plane, the far-side rings behind the planet... the planet is opaque (depth) ✓ culls rings behind the planet. The problematic case is rings behind the CLOUD sphere but not behind the planet — i.e., ring portions visually adjacent above/below the planet's limb: the ring far side passing behind the planet's limb area — occluded by the planet mostly ✓; the ring near the limb but outside the planet's silhouette, behind the cloud sphere?? The cloud sphere radius 10.35 — its silhouette is slightly bigger than the planet's; ring fragments behind the clouds but outside the planet's disc: in the annular region between the planet's limb (10) and the cloud limb (10.35) — a 0.35-unit band — negligible artifact (rings would draw over a thin sliver of cloud edge — imperceptible).

And clouds vs atmosphere: atmosphere is additive around the limb; drawing atmosphere after clouds ✓ glow over clouds ✓.

And the moon (opaque) crossing IN FRONT of the rings: moon drawn in opaque pass; rings blend over the moon only where ring fragments pass the depth test (ring in front) ✓; when the moon is in front of rings, the ring fragments behind it are depth-culled ✓.

But the moon's own shadow/positional relation: the moon crossing IN FRONT of the planet at radius 30 — between the camera (39) and planet (10): distance to camera ~9-11 — the moon is INSIDE the cloud sphere's... no, the moon is outside radius 10.35 ✓ it's in front of the planet from the camera's view ✓ appears over the disc ✓.

Another sorting: rings (transparent) vs the SUN billboard (transparent, far at 850): the sun is behind the rings; renderOrder of the sun: set 0? Transparent objects sorted by z-depth by default: the sun is much farther → drawn first among transparents ✓ then clouds/rings blend over ✓. But explicit renderOrder overrides distance sort — set the sun renderOrder = 0 (default) and clouds 1 etc. — objects with the same renderOrder sort by depth ✓. The atmosphere shell (renderOrder 2) vs the sun: sun farther, drawn first ✓.

The moon (opaque) vs additive atmosphere drawn after — fine.

Starfield & nebula: Points material transparent additive — they'd sort into the transparent list with renderOrder... Set stars renderOrder = -1 and nebula renderOrder = -2 → drawn before everything transparent but AFTER opaque? Transparent pass happens after opaque regardless — nebula is opaque material? If nebula is opaque (transparent: false), it's in the opaque pass with depth → correct occlusion vs planet ✓ (planet closer, passes). Stars additive transparent — drawn in the transparent pass AFTER the planet: stars behind the planet get depth-culled ✓; stars in front of everything (they're at 1500-2300, always behind everything in the scene — max scene depth ~50) ✓ fine.

Nebula opaque at 2400 → renders with the opaque pass; depth vs stars fine ✓.

Now, the ring geometry orientation: RingGeometry lies in XY; I need it in XZ (equatorial): rotate the RING MESH by rotation.x = -π/2 → then the ring's local XY → world XZ ✓ (within the tilted group). vObjPos.xy still gives the ring-plane coords ✓ radius = length(vObjPos.xy) ✓.

Clouds & planet & atmosphere: spheres — orientation irrelevant except noise pole = local Y = group Y ✓ aligned with rings ✓.

Moon: not in the group; its own orbit tilt handled in position math ✓.

Now the LOOK target: slight drift to add parallax life:
```js
look.set(Math.sin(t*0.043)*2.0, Math.sin(t*0.031)*1.2, Math.cos(t*0.037)*2.0);
```
Small relative to r=40 ✓.

Check: at t≈11 the moon crossing — the look target wanders ±2 — fine.

Sun visual position: `sunGroup.position.copy(sunDir).multiplyScalar(850)`.

Also — should the sun's light direction change with... it's directional: uSunDir constant ✓.

Post-check on the ring shadow function edge case: when the camera is such that dot(p, uRingN) has the fragment... p is the fragment world pos; t = -dot(p,n)/dot(s,n): for fragments on the planet's sunlit side, this correctly finds where the sun ray crosses the ring plane ✓. If the crossing radius is outside [15,26] → no shadow ✓. Strength 0.55 — visible but soft ✓. Also apply to clouds ✓ (with softer floor 0.42).

One more: the ring shadow should probably also soften with distance (penumbra) — the band edges get soft naturally via ringPattern smoothstep ✓ good enough.

Also the planet shadow on the RINGS uses planetShadow ✓ (radius 10, soft 8.8-12.8) ✓.

Eclipse on clouds: mSh ✓.

Moonlight term on clouds? skip (minor).

Let me also double check the sun billboard doesn't wash the whole screen when the camera faces it: at 850 with uSize 150: the halo exp(-r*2.5) at r=1 (edge) → 0.082*0.18 ≈ small ✓. Core exp(-r²*90)*3 at center = 3 → ACES maps ~0.95 white ✓ good. Actually ACES tone maps 3.0 → ~0.93 ✓ bright white core ✓.

Lens ghost visibility: only when the sun is in frame (vis computed) ✓.

Also add a subtle horizontal streak on the SCREEN-space pass too (in addition to world-space) — the world streak is on the billboard quad which is only 16° wide — the anamorphic streak should extend wider across the screen: the screen-space streak handles that ✓ (scale.x = 2.2*aspect, uVis tied to flare). Both fine.

Star count 7000 + sizes — fine.

Performance: the planet fragment shader with ~30 snoise calls — each snoise ~ 60-80 ALU ops... 30*70 ≈ 2100 ops/px on the planet area (~15-25% of screen at 1080p ≈ 500k px → 1G ops/frame → OK for discrete GPUs, borderline integrated. Reduce: fbm 5 octaves for cont & det (10), mrange 1, bio fbm→fbm4 (4 octaves), capN fbm4 (4), clusters 1, sparkle 1, ringPattern 4 (only when... ringShadow always evaluated: 4), moonShadow ~cheap. Total ≈ 17 snoise... acceptable. Let me define fbm as 5 octaves and fbm4 4 octaves; use fbm4 for bio/capN. Clouds: wa 5, d1 5, d2 5 = 15 + shadows — fine (clouds only cover part).

Alternatively share computations... keep as is; modern GPUs handle it.

Nebula fbm 5+5+5 = 15 snoise over the whole sky — the sky is big on screen... nebula at 2400 covers the full background → full-screen 15 snoise. Hmm — reduce nebula fbm to 4 octaves & 3 evaluations → 12. Or drop n3. Keep band+n1+n2 → 8-10. OK: use fbm4 for all nebula calls (4 octaves each × 3 = 12). Fine.

Stars: cheap.

Now — the "uTime" for noise evolution in clouds: pass uTime ✓ shared uniform object across materials: I'll create shared uniforms objects and reference them:

```js
const shared = {
  uTime:   { value: 0 },
  uSunDir: { value: sunDir },
  uMoonPos:{ value: new THREE.Vector3() },
  uMoonR:  { value: 1.5 },
  uPlanetR:{ value: 10.0 },
  uRingIn: { value: 15.0 },
  uRingOut:{ value: 26.0 },
  uRingN:  { value: ringNormal },
};
```
Materials get `uniforms: { uTime: shared.uTime, ... , uShellR: {value: 11.4} }` — sharing the same uniform objects across materials means updating shared.uTime.value updates all ✓.

Moon radius: let me set 1.55 and uMoonR 1.5 for shadow softness — just use 1.5 everywhere; geometry 1.5.

Hmm — moon size vs its shadow: uMoonR 1.5 → shadow smoothstep(0.75, 2.55, d) — umbra radius ~2.5 units on the planet — a prominent eclipse spot ✓ visible at planet scale 10 ✓.

Now assemble everything. Also the OrbitControls import isn't needed — I'll not import it (no interaction). The user mentioned addons as available, not required.

Let me also double check the ghost/halo/streak positioning code and the flare scene setup:

```js
const flareScene = new THREE.Scene();
const flareCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 10);
flareCam.position.z = 1; // looking at -z? Ortho camera at z=1 looking -z; objects at z=0 ✓ (default looks toward -z ✓).
```
Objects: PlaneGeometry(1,1) meshes at z=0, material depthTest false, depthWrite false, transparent true, blending AdditiveBlending ✓. renderOrder for streak/halo/ghosts — additive order irrelevant ✓. Vignette LAST with normal blending: renderOrder high ✓.

Flare cam update on resize ✓.

Sun NDC projection: `_sunNdc.copy(sunWorld).project(camera)` — after camera.updateMatrixWorld() and since projectionMatrix is updated on aspect change ✓ (call camera.updateProjectionMatrix on resize ✓).

Ghost meshes: geometry shared PlaneGeometry(1,1); each has its own ShaderMaterial (uniforms cloned). Position: (ndc.x * -k * aspect, ndc.y * -k, 0); scale.set(size, size, 1). Wait sign: ghost at ndc' = sunNdc * (-k): X = -k*sunNdc.x*aspect... hold on: ndc' = -k * ndc (per component), then ortho X = ndc'.x * aspect = -k*ndc.x*aspect ✓, Y = -k*ndc.y ✓. With k values as listed (some negative → positive multiplier → on the sun's side of center). Fine.

Halo: position (sunNdc.x*aspect, sunNdc.y), scale 1.7.
Streak: position same; scale.set(2.4*aspect... let me: width covering most of the screen: scale.x = 2.2*a? The quad is 1×1 scaled → half-width = 1.1a → covers beyond the screen ✓ with exp falloff. scale.y = 0.035 → thickness ±0.0175 units = 1.7% of half-height — thin ✓. Hmm exp(-p.y²*220) with p.y ∈ [-1,1] over the quad's height: at p.y=0.1 → exp(-2.2) = 0.11 — the visible core is ~±0.05 of the quad → ±0.05*0.035 screen-heights... too thin? Quad height = 0.035 units; p.y=±1 at quad edge; the glow core spans p.y ∈ [-0.07, 0.07] → 0.07*0.0175 units = 0.0012 units = 0.06% of screen height — too thin. Let me make scale.y = 0.09 and falloff exp(-p.y*p.y*30): core p.y∈[-0.18,0.18] → 0.032 units ≈ 1.6% of screen height ✓ reasonable anamorphic line. And x falloff exp(-|p.x|*2.2).

Also the WORLD sun billboard streak: sun quad half=1: streakH = exp(-|p.y|*34) — quad half-size 75 world units (uSize 150 total)... visible streak length ~ |p.x| < 1.2 → covers most of the quad (16°) ✓ nice diffraction spike ✓.

Now — ACES tone mapping + the flare overlay drawn AFTER (not tone mapped) ✓ fine.

Also, should I dim the flare when the camera looks away (front factor)? The NDC projection flips when behind → off-screen detection handles ✓ plus front check ✓.

Now — the eclipse shadow on the planet needs uMoonPos in WORLD space ✓ and moonShadow's ray toward the sun: for the shadow to be cast on the planet, the moon must be on the sun side of the fragment ✓ handled.

Let me also sanity check `ringShadow` when the sun is below the ring plane locally... fine.

Also — planet self-shadow terminator: diffuse handles ✓.

One more possible issue: the planet's SPECULAR glint uses H = normalize(uSunDir + V) — Blinn-Phong ✓.

Bioluminescence: only in shallow shelf — needs shelf band to exist: shelf = smoothstep(sea-0.075, sea-0.004, h)*(1-landMask): h ∈ [sea-0.075, sea) → band ✓ width 0.075 in h-units — with fbm gradients this is a visible coastline band ✓.

Also make the biolume pulse subtly with time: *(0.8+0.2*sin(uTime*0.8 + snoise(sp*9.0)*6.0))? Cheap: use a phase from noise: sin(uTime*0.7 + clusters*10.0)*0.15+0.85 ✓ nice living detail.

OK also — atmosphere shell radius vs cloud radius: shell 11.4 (b-parameter uses uPlanetR=10 & uShellR=11.4): the glow annulus spans b ∈ [10, 11.4] — thin! The visible atmosphere rim thickness on screen ≈ (11.4-10)/40 rad ≈ 1.4° — thin-ish; widen: shell 12.2 → thickness 2.2/40 ≈ 3° ✓ better. SphereGeometry(12.2). But the glow at b slightly < 10 (over the planet's disc) is occluded ✓. Also glow should slightly extend over the disc edge — handled by the surface fresnel ✓.

Hmm — wait: for b > shellR there's no shell intersection (ray misses) ✓ no glow beyond ✓.

Also the atmosphere at the day side is bright cyan; make sure it doesn't wash the limb: intensity 1.5*day*glow — with ACES it'll be a strong rim ✓ tasteful.

Double-check `tc = -dot(C, D)`: C = camera position (from origin), D = view ray dir. The closest point on the ray to the origin: param τ* = -dot(C,D)... point = C + D*τ; minimize |C + Dτ|²: d/dτ = 2(C·D + τ) → τ = -C·D ✓ tc = -dot(C, D) ✓ (could be negative if the origin is behind the camera — then the shell in front still... if tc < 0, the closest approach is behind; but the fragment is on the far shell with b... For rays hitting the shell, tc > 0 always when the camera is outside and looking at the planet ✓. If the camera looks away, tc could be ≤ 0 for shell fragments behind the camera — not rendered (behind). ✓ safe: clamp tc to positive: if(tc < 0) tc = 0. — add for safety.

b = length(C + D*tc) — distance from origin to the ray ✓.

Alright — also the planet's fresnel uses V & N world ✓.

Now — the lookAt drift + camera drift use t — smooth ✓.

The eclipse timing check once more with final constants:
- MOON_R = 30, MOON_W = 0.1496 (T≈42s), MOON_A0 = -1.091, inc = -0.32.
- CAM: az0 = 1.591, w = -0.0628 (az = az0 - 0.0628t), r = 40 - 5e^{-0.09t} + 1.4 sin(0.13t)?? I used 0.11 earlier for r-osc; fine: 1.4 sin(0.11t).
- Sun az = atan2(0.3958, 0.8796) = 0.4222 rad. ✓ (sunDir (1, 0.28, 0.44) normalized: |v| = sqrt(1+0.0784+0.1936) = sqrt(1.272) = 1.1279 → (0.8866, 0.2483, 0.3903). Sun az = atan2(0.3903, 0.8866) = 0.4159 rad. elevation = asin(0.2483) = 14.4°. Close to previous ✓.)

Transit events: shadow peak at a = a*: recompute a* with s = (0.8866, 0.2483, 0.3903): cosγ(a) = s·P̂ where P̂ = (cos a, 0.3146 sin a, 0.9492 sin a): = 0.8866 cos a + sin a (0.3146*0.2483 + 0.9492*0.3903) = 0.8866 cos a + sin a (0.07814 + 0.37045) = 0.8866 cos a + 0.4486 sin a. Max = sqrt(0.7861 + 0.2012) = sqrt(0.9873) = 0.9930 at a* = atan(0.4486/0.8866) = atan(0.5060) = 0.4688. min shadow dist = 30*sqrt(1-0.98611) = 30*0.1179 = 3.79 ✓. t_peak: a(t) = 0.468 → t = (0.468 - A0)/0.1496. Want peak ≈ 10.5: A0 = 0.468 - 1.5708 = -1.103. Set MOON_A0 = -1.10. Then t_peak = (0.468+1.103)/0.1496 = 10.50 ✓.
Shadow on-disc window: |a - 0.468| < ~0.377 (for dist < 11.3 incl penumbra) → a ∈ (0.09, 0.845) → t ∈ ((0.104+1.103)/0.1496?? a = 0.104 → t = (0.104+1.103)/0.1496 = 8.07; a = 0.856 → t = 13.07. So shadow visible t ∈ [8.1, 13.1] ✓.
Moon-cam relative az = 0 at: rel = (A0 - az0) + (MOON_W + 0.0628)t = (-1.103 - 1.591) + 0.2124t = -2.694 + 0.2124t → 0 at t = 12.68 ✓ (moon crossing the camera-planet axis, in front, big). Moon-behind-planet (rel = π): t = (3.1416+2.694)/0.2124 = 27.5 ✓ occultation ≈ t ∈ [26.1, 28.7].

Camera sun-separation: |az_sun - az_cam| = |0.422 - 1.591 + 0.0628t| = |0.0628t - 1.169|: t=10: 0.541 rad (31°); t=16: 0.164 (9.4°); t=18.6: 0 (sun behind camera — flare exits frame between t≈12 (43°) and... flare visible while separation ≲ 40° → t ∈ [~9.8, ~18]. Hmm the sun stays near the frame edge ~t=16-18 at 9-2° — but wait when the camera azimuth passes the sun azimuth, the sun goes BEHIND the camera — it exits through the frame edge around separation > 43° → t ≈ 19.4. Between t≈16-19 the sun is nearly behind the camera — it exits the frame sideways. During t 16-19, the planet is nearly fully lit ✓.

Also during t≈9-14 the SUN is in frame while the moon silhouette crosses ✓ — and the flare ghosts radiate ✓. 

One concern: with the sun in frame at 24-37° off-axis and elevation ~20° above center, plus the planet centered — composition fine.

Now — the moon crossing the disc around t≈10-15: the moon's screen position at t=12.6 ≈ planet center ✓ big silhouette ~16° across. ACES: the moon's crescent rim lit — thin bright arc ✓ visible against the planet's bright disc as a dark disc ✓✓.

Also — during the crossing, the moon's shadow on the planet: peak at 10.5, ends 13.1 — as the moon crosses the face, the umbra is roughly beneath it ✓ coherent.

And moonlight: during the eclipse... fine.

Let me also confirm the moon's crescent is visible at crossing: phase angle 144° → the lit fraction visible = (1+cos143.8)/2 ≈ (1-0.807)/2 ≈ 9.7% — a thin crescent on the sun-facing side ✓.

Also check the moon doesn't intersect the ATMOSPHERE shell visually when crossing: the shell radius 12.2; the moon at radius 30 — outside ✓ but visually the moon crossing in front of the planet will be drawn OVER the atmosphere glow? The atmosphere shell is transparent, rendered after opaque — the moon's depth (closer) → atmosphere fragments behind the moon culled by depth test?? The atmosphere shell at radius 12.2 around the origin: where the moon (10 units from camera) overlaps the shell in screen space, the shell fragment is at distance ~30+ (far side of the shell) vs the moon at ~10 → shell fragment depth farther → culled ✓ (depthTest true) ✓ the moon occludes the glow locally ✓ correct.

BUT — the planet surface fresnel rim is part of the planet shader — the moon occludes it via depth ✓.

Now — also the moon passes in FRONT of the sun?? The moon at radius 30 vs sun at 850: when the moon is on the camera side (t≈12.6) the sun is roughly behind the camera → no. When the moon is at the sun's azimuth on the far side... the moon at azimuth ≈ sun az (0.42) happens at a = 0.42+2πk... a(t) = -1.103+0.1496t = 0.42 → t = 10.2s — at t≈10.2 the moon is near the sun's azimuth BUT at radius 30 on the SUN side — from the camera (az ≈ 0.96 at t=10.2), the moon is beyond the planet to the sun side, 25° off-axis... could the moon visually overlap the sun's position? Sun direction from camera ≈ sunDir; moon direction from camera at t=10.2: moon pos = (30cos0.42, 30*0.3146 sin0.42, 30 sin0.42*0.949) = (27.35, 3.85, 11.56). cam az = 1.591-0.641 = 0.950, r = 40-5e^{-0.918}+1.4 sin(1.122) = 40-1.995+1.249 = 39.25; y = 2.2+4.2 sin(0.09*10.2+0.7) = 2.2+4.2 sin(1.618) = 2.2+4.194 = 6.39; cam = (39.25 cos0.95, 6.39, 39.25 sin0.95) = (39.25*0.5817, 6.39, 39.25*0.8134) = (22.83, 6.39, 31.93). Moon dir from cam: (4.52, -2.86, -20.37) |v| = 20.98 → (0.2155, -0.1363, -0.9709). Sun dir from cam ≈ s = (0.8866, 0.2483, 0.3903). dot = 0.191 - 0.0358 - 0.379 = -0.223 → 103° apart ✓ no overlap. The sun is in a completely different part of the sky from the moon when the moon is at its azimuth — because the camera looks inward. ✓.

Also check: does the moon EVER come between the camera and the sun (transiting the sun's disc)? Only if the moon's direction from the camera ≈ sunDir: the moon is within r ≤ 44 of the origin; the sun at 850 along s. The moon's angular position from the camera ≈ sunDir when the moon is on the sun side at the right elevation... The camera orbits at radius ~39; for the moon to align with the sun from the camera, the moon must be roughly along the ray cam→sun: that ray passes at distance ≥ ... the ray from the camera toward the sun passes the planet region at impact parameter b = dist from origin to the camera-sun ray ≈ 39.25*sin(37°) ≈ 23.6 at t=10 — the ray passes 23.6 from the origin; the moon's orbit is at 30 — the moon could cross that ray near its closest point to the ray... the moon at t=10.2 is at 27.4 from origin?? |moonPos| = 30 always. The ray's closest approach to the origin is 23.6 — points on the ray near closest approach are ~ sqrt(39.25²-23.6²)... the distance from the camera along the ray to closest approach = sqrt(39.25² - 23.6²) = sqrt(1541-557) = 31.4. So the ray passes within 23.6 of the origin at range ~31 from the camera. The moon at radius 30 could be near that point: the moon's position at t=10.2 (27.35, 3.85, 11.56): is it near the ray? Ray point at closest: C + 31.4*s = (22.83+27.84, 6.39+7.80, 31.93+12.25) = (50.67, 14.19, 44.18) — nowhere near the moon (27, 3.9, 11.6). The moon would need to be on the camera's sun-side at radius ~31-45 — the moon IS at radius 30; the ray at range 30-45 from the camera is at distance from origin: at range 45: point = C+45s = (22.84+39.9, 6.39+11.2, 31.93+17.6) = (62.7, 17.6, 49.5) → |·| = 81. The ray's distance from the origin grows beyond the closest approach — the moon at radius 30 crosses the ray only if some ray point has |·| = 30: the ray's minimum |·| along it = 23.6 at range 31.4; |·| grows on both sides; |·| = 30 at ranges ~31.4±sqrt(30²-23.6²) = 31.4±18.6 → range ∈ {12.8, 50}. At range 50 from the camera along s: point = C + 50s = (22.84+44.3, 6.39+12.4, 31.93+19.5) = (67.2, 18.8, 51.4)?? wait that's |·| should be 30: |(67.2, 18.8, 51.4)| = sqrt(4516+353+2641) = sqrt(7510) = 86.7 — that's wrong; let me redo: |C + τs|² = |C|² + 2τ C·s + τ². C·s = 22.84*0.8866 + 6.39*0.2483 + 31.93*0.3903 = 20.25 + 1.586 + 12.46 = 34.3. |C|² = 39.25² = 1540.6. |p|² = 1540 + 68.6τ + τ². Minimum at τ = -34.3 — NEGATIVE → the origin is BEHIND the camera relative to the sun direction: the ray toward the sun moves AWAY from the origin monotonically → |p| grows from 39.25 → the ray never comes within 30 of the origin → the moon (|·|=30) can NEVER be on the camera→sun ray while the camera looks... wait that's when the sun is 37° off-axis. In general: the sun-ray from the camera has its closest approach to the origin at τ* = -C·s = -34.3 < 0 → the sun is behind the planet-side... The camera at az 0.95, sun az 0.42: the angle between C and s is 30.6°; C·s = |C||s| cos(37°)?? 39.25*cos(30.5°) = 33.8 ✓ positive → τ* negative → the ray from the camera toward the sun RECEEDS from the origin → any moon at radius 30 can never cross the sun's disc from this camera position ✓ (the sun is above/outside). Generally the sun elevation 14° and the camera near the equator... when the camera is on the ANTI-sun side (az ≈ sun az + π, t≈48s), the ray toward the sun passes THROUGH the planet region (occultation of the sun by the planet — cool: the sun dims behind the planet ✓ handled by depth + occlusion fade ✓). The moon could then transit the sun's disc near the planet — around t≈48 — outside the window; doesn't matter.

OK. Also — will the sun pass behind the PLANET during the 30s? The sun's angular offset from the look axis is ≥ 9° (min at t≈18.6, offset ≈ elevation difference ~20°+ hmm at t=18.6 the camera az = sun az → the sun is directly behind the camera → offset ~180°?? no: looking at the origin, the sun behind the camera → the sun is at ~180° from the look direction → off-frame ✓). The sun's closest approach to the planet's disc direction: minimum offset over the window ≈ 37° at t≈10 (computed above) vs planet angular radius 14.6° + sun glow — no overlap ✓ the sun never hides behind the planet in the window; occlusion code still matters later (t≈40+ when the camera goes to the night side... camera az decreases: at t=37: az = 1.591-2.32 = -0.73; sun az 0.42 → separation 1.15 rad = 66°... hmm the camera never reaches the anti-sun side quickly (az decreases at 0.0628 rad/s → 180° in 50s: at t=50: az = 1.591-3.14 = -1.55 vs sun 0.42 → separation 1.97 rad = 113° → past 90°, the planet is waning; the sun-planet-camera alignment for solar occultation needs separation ≈ 180°: az_cam = sun az + π → az_cam = 3.56 or -2.72 → t = (-2.72-1.591)/(-0.0628) → t = 68.6s. So at t≈68 the sun eclipses behind the planet with flare fade ✓ (post-window, loop continues nicely).

Now — final code assembly. Let me also add subtle "breathing" to the sun glow (slow pulsation ±4%) — optional; skip.

Also should I add a subtle slow roll to the camera (camera.up tilt)? A tiny roll adds cinematic feel: camera.rotation.z after lookAt: camera.rotateZ(0.03*sin(t*0.05))? Keep 0 — lookAt resets each frame; apply rotateZ after: camera.rotateZ(Math.sin(t*0.05)*0.02) — very subtle drift. OK, include (0.018 amplitude).

Star twinkle amplitudes small ✓.

Write the HTML now. Also include a tiny bit of UI? No — pure canvas (maybe a small unobtrusive title? The instructions say no interference needed; a title overlay could be nice but risks the recorder's frame — skip, pure visual).

Also `document.title` set ✓.

Code layout:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Alderaan? no — name the planet something alien: "Veyra Prime — Orbital Survey"</title>
<style>
  html, body { margin:0; padding:0; height:100%; overflow:hidden; background:#020408; }
  canvas { display:block; }
</style>
</head>
<body>
<script type="module">
import * as THREE from 'three';

/* ---------- renderer / scene ---------- */
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setClearColor(0x000104, 1);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.12;
renderer.autoClear = false;
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(55, window.innerWidth/window.innerHeight, 0.1, 7000);

/* constants */
const SUN_DIR = new THREE.Vector3(1, 0.28, 0.44).normalize();
const SUN_POS = SUN_DIR.clone().multiplyScalar(850);
const PLANET_R = 10, CLOUD_R = 10.35, SHELL_R = 12.2;
const RING_IN = 15, RING_OUT = 26;
const MOON_R = 1.5, MOON_ORBIT = 30, MOON_W = 0.1496, MOON_A0 = -1.103, MOON_INC = -0.32;
const TILT = -0.18;
```

Planet group with rotation.z = TILT.

Wait — I should double check the ring normal with the tilt: n = (0,1,0) rotated about Z by TILT: R_z(θ)(0,1,0) = (-sin θ, cos θ, 0) → TILT = -0.18 → (-sin(-0.18), cos(-0.18), 0) = (0.179, 0.984, 0) ✓ compute programmatically:
```js
const ringN = new THREE.Vector3(0, 1, 0).applyAxisAngle(new THREE.Vector3(0,0,1), TILT);
```

Then materials. Let me now write out every shader fully and carefully, minding GLSL correctness.

One more check — ShaderMaterial and `#include <tonemapping_fragment>`: these chunks reference `gl_FragColor` — in three r186 the chunks are written for WebGL2 GLSL3? ShaderMaterial defaults to GLSL1 (auto-converted). The tonemapping chunk in recent three: 
```glsl
gl_FragColor.rgb = toneMapping( gl_FragColor.rgb );
```
guarded by `#if defined( TONE_MAPPING )`. And colorspace_fragment: `gl_FragColor = linearToOutputTexel( gl_FragColor );` ✓ These work in ShaderMaterial ✓ (standard practice).

Also — for the atmosphere material (AdditiveBlending) the alpha doesn't matter ✓.

For the ring material: transparent: true → renders in the transparent pass ✓ with `depthWrite:false`.

Cloud: transparent true, depthWrite false.

Now the moon mesh: SphereGeometry(MOON_R, 48, 32).

The moon also needs its own light? It's shader-lit ✓.

Also — "casts light": add a subtle cool rim on the moon from the planet? skip.

Let me now also decide fbm octave counts: fbm5 & fbm4:

```glsl
float fbm(vec3 p){
  float f = 0.0, a = 0.54;
  for(int i = 0; i < 5; i++){ f += a*snoise(p); p = p*2.17 + vec3(11.7, 5.3, 9.1); a *= 0.52; }
  return f;
}
float fbm4(vec3 p){
  float f = 0.0, a = 0.55;
  for(int i = 0; i < 4; i++){ f += a*snoise(p); p = p*2.23 + vec3(7.3, 13.1, 3.9); a *= 0.55; }
  return f;
}
```

Nebula uses fbm4 ✓.

Now, the rings mesh: RingGeometry(RING_IN, RING_OUT, 256, 4). Note RingGeometry's default is in the XY plane facing +Z; rotation.x = -Math.PI/2 → lies in XZ with the normal +Y ✓ (before the group tilt).

Moon orbit line as computed ✓.

Star geometry:

```js
const STAR_N = 6500;
const sPos = new Float32Array(STAR_N*3), sCol = new Float32Array(STAR_N*3), sSize = new Float32Array(STAR_N), sTw = new Float32Array(STAR_N), sPh = new Float32Array(STAR_N);
const bandN = new THREE.Vector3(0.42, 1.0, 0.22).normalize();
...
for(let i=0;i<STAR_N;i++){
  let d = randomUnit();
  if(i < STAR_N*0.55){
    d.addScaledVector(bandN, -d.dot(bandN)*(0.75 + 0.2*Math.random()));
    d.normalize();
    d.addScaledVector(randomUnit(), 0.10); d.normalize();
  }
  const rad = 1500 + 750*Math.random();
  sPos.set... 
  let cr, cg, cb;
  const u = Math.random();
  if(u < 0.70){ cr=1.0; cg=0.97; cb=0.92; }
  else if(u < 0.86){ cr=0.70; cg=0.81; cb=1.0; }
  else { cr=1.0; cg=0.83; cb=0.60; }
  const b = 0.30 + 0.70*Math.pow(Math.random(), 1.7);
  sCol[i*3] = cr*b; ...
  sSize[i] = (0.9 + 3.6*Math.pow(Math.random(), 4.0)) * (0.8+0.4*Math.random());
  sTw[i] = 0.4 + 2.2*Math.random();
  sPh[i] = Math.random()*6.283;
}
```
randomUnit:
```js
function randomUnit(v = new THREE.Vector3()){
  const z = Math.random()*2-1, a = Math.random()*Math.PI*2, r = Math.sqrt(1-z*z);
  return v.set(r*Math.cos(a), r*Math.sin(a), z);
}
```

Star material:
```js
const starMat = new THREE.ShaderMaterial({
  uniforms: { uTime: shared.uTime, uPR: { value: renderer.getPixelRatio() } },
  vertexShader: `
    attribute float aSize; attribute vec3 aCol; attribute float aTw; attribute float aPh;
    uniform float uTime; uniform float uPR;
    varying vec3 vCol; varying float vA;
    void main(){
      vCol = aCol;
      vA = 0.72 + 0.28*sin(uTime*aTw + aPh);
      vec4 mv = modelViewMatrix*vec4(position,1.0);
      gl_PointSize = aSize*uPR;
      gl_Position = projectionMatrix*mv;
    }`,
  fragmentShader: `
    varying vec3 vCol; varying float vA;
    void main(){
      vec2 p = gl_PointCoord*2.0-1.0;
      float d2 = dot(p,p);
      if(d2 > 1.0) discard;
      float a = (1.0-d2);
      gl_FragColor = vec4(vCol*vA*a*a, 1.0);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }`,
  blending: THREE.AdditiveBlending, depthWrite: false, transparent: true
});
```
Points in a "sky" group rotating slowly.

Hmm — stars additive with tone mapping: values ≤ 1 → ACES slightly dims; ok.

Nebula mesh: SphereGeometry(2600, 48, 32), material side BackSide, depthWrite true, fragment as designed with fbm4. It must render behind stars: both fine via depth (nebula at 2600, stars ≤ 2250 ✓).

Sun billboard: PlaneGeometry(2,2):
```js
const sunMat = new THREE.ShaderMaterial({
  uniforms: { uDim: { value: 1 } },
  vertexShader: `
    uniform float uSize; varying vec2 vUv;
    void main(){
      vUv = uv;
      vec4 mv = modelViewMatrix*vec4(0.0,0.0,0.0,1.0);
      mv.xy += position.xy*uSize;
      gl_Position = projectionMatrix*mv;
    }`,
  ...
```
uniform uSize = 150. Add uSize to uniforms.
fragment as designed with uDim. depthTest: true (occlusion by planet) — but the billboard's depth: gl_Position.z from the center's depth ✓ consistent. depthWrite false, transparent true, blending additive.

Hmm — the sun at 850 with the far plane 7000 ✓; the nebula at 2600 is behind the sun ✓ the sun's additive glow blends over stars ✓.

But WAIT: the sun billboard with depthTest true will be depth-tested against... it's drawn in the transparent pass after opaque ✓ planet occludes ✓ rings (transparent, drawn... ring renderOrder 3 > sun 0 → rings draw after the sun; where rings are in front of the sun (between camera and sun) rings blend over ✓; ring fragments behind the sun's billboard get culled by the sun's depth? The sun doesn't write depth ✓ so rings behind the sun still draw and blend OVER the sun's glow — hmm: rings behind the sun (farther) would incorrectly layer over the sun's glow. When does that happen? The sun at az 0.42 elev 14°; the rings span radially... from the camera near the sun's azimuth, the rings on the far side are between the camera and the sun?? The sun is at 850 far beyond everything — the rings are ALWAYS in front of the sun ✓ so rings blending over the sun's glow is CORRECT ✓. Similarly clouds ✓. Stars vs sun: stars additive, drawn... transparent pass order: renderOrder 0 for all except my explicit ones: stars renderOrder -1 → drawn before the sun ✓ stars behind the sun's glow still add — fine (both additive).

Order summary (transparent): stars(-1)? Hmm stars are transparent? I set transparent: true + additive → they're in the transparent pass; renderOrder -1 draws them first ✓. Then sun (0), clouds (1), atmosphere (2), rings (3). Ghost overlay in a separate scene ✓.

Wait — one problem: the transparent pass sorts by renderOrder FIRST, then by depth within the same order ✓ that's what I want.

The moon is opaque ✓. Planet opaque ✓.

Now the FLARE overlay scene:

```js
const flareScene = new THREE.Scene();
const flareCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 10);
flareCam.position.z = 5;
```
Wait — objects at z=0, camera at z=5 looking -z ✓ visible ✓ near 0.1 far 10 ✓.

Ghost material factory:
```js
function makeGhost(tint, fall, ringAmt){
  return new THREE.ShaderMaterial({
    uniforms: { uTint: { value: new THREE.Color(tint[0], tint[1], tint[2]) }, uVis: { value: 0 }, uFall: { value: fall }, uRing: { value: ringAmt } },
    vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); }`,
    fragmentShader: `
      uniform vec3 uTint; uniform float uVis, uFall, uRing; varying vec2 vUv;
      void main(){
        vec2 p = vUv*2.0-1.0;
        float r2 = dot(p,p);
        float disc = exp(-r2*uFall);
        float g = (r2 - 0.55)*6.0;
        float ring = exp(-g*g)*uRingAmt;
        float a = (disc + ring*0.7)*uVis;
        gl_FragColor = vec4(uTint*a, 1.0);
      }`,
    transparent: true, blending: THREE.AdditiveBlending, depthTest: false, depthWrite: false
  });
}
```
Halo: fall 2.6, ring 0, size 1.9, tint warm dim.
Streak: separate shader.

Update:
```js
const _ndc = new THREE.Vector3(), _d1 = new THREE.Vector3(), _d2 = new THREE.Vector3(), _cd = new THREE.Vector3();
function updateFlare(){
  camera.getWorldDirection(_cd);
  _d1.copy(SUN_POS).sub(camera.position);
  const dist = _d1.length(); _d1.divideScalar(dist);
  const front = _cd.dot(_d1) > 0.0;
  _ndc.copy(SUN_POS).project(camera);
  // occlusion by the planet sphere
  _d2.copy(camera.position).negate();
  const tC = _d2.dot(_d1);
  let occ = 0;
  if(front && tC > 0 && tC < dist){
    const b = _d2.multiplyScalar(tC).add(camera.position).length();
    occ = 1 - THREE.MathUtils.smoothstep(b, PLANET_R + 0.6, PLANET_R + 2.6);
  }
  const off = Math.max(Math.abs(_ndc.x), Math.abs(_ndc.y));
  const edge = 1 - THREE.MathUtils.smoothstep(off, 0.75, 1.5);
  const vis = front ? (1 - occ)*edge : 0;
  const ax = camera.aspect;
  sunMat.uniforms.uDim.value = 0.22 + 0.88*(1 - occ);
  halo.position.set(_ndc.x*ax, _ndc.y, 0); halo.material.uniforms.uVis.value = vis*0.55?? define vis = (front? (1-occ)*edge : 0)
  ...
}
```
Note: `_d2.copy(camera.position).negate()` then dot with _d1 → tC ✓ then `_d2.multiplyScalar(tC).add(camera.position)` → closest point ✓ length → b ✓ (reuse _d2 carefully — after multiplyScalar it's mutated; fine, recompute each frame).

Smoothstep: THREE.MathUtils.smoothstep(x, min, max) ✓.

Ghosts update: for each ghost g: `m.position.set(_ndc.x * -g.k * ax, _ndc.y * -g.k, 0); m.material.uniforms.uVis.value = g.base * vis;` and scale fixed at creation ✓.

Streak: position = sun's ortho pos, uVis = vis * 0.5.

Halo uVis = vis * 0.35.

Now the animate loop with all updates ✓.

Also — planet material needs `uniforms: { ...shared refs, }` — in ShaderMaterial the uniforms object maps names → {value}. Shared references ✓:

```js
function planetUniforms(extra){ return Object.assign({}, shared, extra); } 
```
careful: Object.assign shallow-copies the references to the same {value} objects ✓ updating shared.uTime.value propagates ✓.

Edge: two materials sharing the same uniform object — allowed ✓.

Now — potential GLSL pitfalls double-check:
- `mat3(modelMatrix)` — modelMatrix is mat4 ✓ mat3(modelMatrix) allowed in GLSL ES 1.0? Constructor mat3(mat4) IS allowed in GLSL ES 1.00 ✓ (takes upper-left 3x3 ✓).
- varying/vS usage ✓.
- `if (x < 0.0 || x > 1.0) return 1.0;` ✓.
- In the ring fragment I use vObjPos — RingGeometry position z=0 ✓ length(vObjPos.xy) ✓.
- discard before writing ✓.
- The atmosphere fragment needs uSunDir ✓ via common (I'll include GLSL_COMMON which declares uniforms — but GLSL_COMMON includes noise functions the atmosphere doesn't need — fine, harmless).
- Actually — including snoise in 6 materials → longer compile, fine.

The planet fragment uses `uTime`? Not currently (terrain static, mesh rotates) — remove or keep unused (unused uniforms are optimized out; three handles missing locations fine ✓). I'll keep uTime only where used (clouds, stars). Shared uniform declared in materials that don't use it — three warns? No — three only uploads uniforms that exist in the program... it iterates over the material's uniforms map and tries to set; if the program doesn't have the location, WebGL returns null → three skips silently ✓ safe.

Now, moon position shared across planet/cloud materials via shared.uMoonPos ✓ update each frame ✓.

Planet rotation & moon orbit direction: moon orbit a increasing → counterclockwise viewed from +Y; camera azimuth decreasing (opposite) ✓ as designed.

Also, hmm — the moon's orbital direction vs the tilt: fine.

Ring shadow on the planet needs uRingN — a constant ✓ shared.

Sun-light direction for the rings' lit-face check: uRingN vs uSunDir: dot = 0.8866*0.179 + 0.2483*0.984 + 0 = 0.1587+0.2443 = 0.403 > 0 → the sun is on the +n side (above the ring plane) ✓ the camera y > 0 mostly → viewing the lit face ✓.

Planet shadow on rings: visible on the far side ✓.

Now — one more art check: the RING brightness: col ~ (0.5..0.36)*(0.32+0.95*0.4)*1 ≈ 0.5*0.7 = 0.35 mid-gray warm ✓ with alpha ~0.5 avg. Rings shouldn't overpower the planet ✓.

The planet's day brightness: albedo (~0.2-0.5) × 1.45 → ~0.4-0.7 pre-ACES ✓ good.

Ocean glint pow(ndh,120)*1.3: tight sparkle ✓.

Sky base: near black ✓ stars ~0.3-1 additive ✓ nebula ≤ ~0.1 ✓.

Vignette 0.38 max at corners — subtle ✓.

Let me also reconsider the CLOUD alpha at the limb: the cloud sphere's rim (grazing) — alpha constant per-fragment; at grazing angles the shell covers more pixels — natural thickening ✓.

Atmosphere: also should add a subtle FADE of the atmosphere when the camera is very close? Camera min distance ~35 ✓ never inside.

What about the atmosphere shell being visible through the moon when the moon is in front — handled ✓.

Star twinkle: some stars stationary (aTw small) ✓.

One more requirement re-read: "a slowly rotating cloud layer" ✓ (mesh rotation 0.029 rad/s ≈ full rotation in 3.6 min — visible drift over 30s: 0.87 rad?? 0.029*30 = 0.87 rad = 50° — hmm that's fast-ish for clouds; relative to the planet's 0.021*30 = 0.63 rad. The clouds visibly sliding over the surface is good for a 30s read — keep, maybe slightly slower: planet 0.02, clouds 0.027.)

"ring system with transparency" ✓.
"glowing atmospheric rim (fresnel)" — I have the shell + surface fresnel ✓ (mention fresnel: the shell uses an impact-parameter profile rather than raw fresnel; the PLANET surface has a classic fresnel rim ✓ requirement satisfied).

"a small moon orbiting the planet that casts light and shadow interest" ✓.

"distant sun with lens-flare-like glow" ✓.

"dense starfield" ✓ 6500.

"camera slowly drifts around the planet" ✓.

"Use the requestAnimationFrame timestamp for animation time" ✓ ts*0.001.

"Full-window canvas that handles resizing" ✓.

"Starts automatically, no interaction" ✓.

Now — is there any risk the scene is dark/boring at t=0? Opening: planet 70% lit, rings, terminator glow, half-lit moon near the limb, dense stars, subtle nebula. Should be striking. The first seconds: the camera eases in from r=45→40 (mild). The eclipse starts t≈8. Good pacing.

Also add a subtle intro fade-in from black over ~1.5s? A CSS overlay div fading out (opacity transition) — simple and tasteful: a black div that fades via JS (opacity = 1 - min(t/2,1)) — do it in the render loop on a fixed overlay div, pointer-events none. Nice polish ✓.

Now write the final code meticulously. I'll also guard against WebGL context creation failure? Skip (assume fine).

One more numeric check — camera near/far: near 0.5 (avoid z-fighting precision at far distances with a huge range: near 0.1 & far 7000 → depth precision issues (logarithmic not used). The critical depth tests: the moon vs planet vs clouds at ranges 30-50 with separations ≥ 0.35 (cloud shell) — 24-bit depth over [0.1, 7000]: precision at range 40 ≈ ~40*(far/near-ish nonlinear)... Standard perspective depth: precision degrades with distance; at z=50 with near=0.1, far=7000, the depth resolution ≈ z²/(near*2^24)?? ≈ 2500/(0.1*16.7M) ≈ 0.0015 — fine ✓. Use near = 0.5 to be safer: precision ~0.0007 ✓. near 0.5, far 7000.

Sun at 850: within far ✓. Nebula 2600 ✓ stars ≤ 2250 ✓.

gl_PointSize with pixelRatio ✓.

Let me also decide the exposure/tone: exposure 1.15.

Potential issue — the atmosphere additive shell might make the limb too hot where the sun is behind (forward scatter term 0.5*fwd*glow: fwd = pow(dot(D, s),3) — when looking toward the sun through the limb (camera opposite the sun) — occurs later (t>40s) ✓ fine.

Now — the ring's `fwd` term: pow(max(dot(-V, uSunDir),0),4)*1.1 — -V is the view ray direction (camera→fragment) ✓.

Also the ring shadow function uses uSunDir & uRingN ✓ and ringPattern (shared) ✓.

Also planet fragment `rSh` uses ringShadow ✓.

Let me also think about whether the ring shadow on the planet might be TOO strong/wrong-looking given sun elevation ~15° above the ring plane... effective angle between s and the ring plane = asin(0.403) ≈ 23.8°. The ring shadow band lands at southern latitudes: rays entering the plane at radius r ∈ [~13.8?, 21.5] hit the planet: earlier calc with elevation 15° gave r ∈ (10.6, 21.2); with 23°: the ray drops faster: from y=0 to the sphere... perpendicular distance from origin of a ray through (r,0,0) dir s: d = r*sin(angle between s and the horizontal-radial direction) = r*sin(elev) → d < 10 → r < 10/sin(23°) = 25.6?? hmm: the ray direction makes angle `elev` with the plane; a ray through a plane point at radius r, traveling at elev below... the perpendicular distance from the origin: the ray through point p0 (in-plane) with direction s: dist = |p0 × s| = r * sqrt(1 - (p̂0·s)²) — p̂0·s = cos(azimuth diff)*cos(elev) ≈ cos(elev) (aligned) = 0.921 → dist = r*sin(elev) = 0.39r → d<10 → r < 25.6. And which plane points shadow the DISC (not just graze): rays hitting the planet's surface at the point where they cross... anyway the band spans a wide latitude range on the southern hemisphere with soft edges ✓ the shader computes exactly ✓. Visually: a dark soft band across the southern day-side hemisphere with ring-pattern banding (from ringPattern(x)*0.55) ✓ subtle (0.55 max darkening) ✓.

Also the rings themselves in the planet's shadow: the anti-sun half of the rings fades ✓ plus the unlit-face dimming ✓.

Also the planet's night side against the rings: rings extend beyond the planet and are lit — silhouette contrast ✓ nice.

Double-check `moonShadow` penumbra scale: uMoonR=1.5: smoothstep(0.75, 2.55, d) — umbra core 0.75 radius where fully dark... at d < 0.75 → shadow factor 0 (full shadow); 0.75-2.55 soft. The visible dark spot ~5 units across on a 20-unit disc — prominent ✓ maybe slightly big; use smoothstep(uMoonR*0.55, uMoonR*1.55, d) → core ~1.65, full light at 2.33 → spot ~4.6 diameter... keep 0.5/1.7 — a big soft eclipse shadow reads well. Fine.

Also — during the crossing (t≈12.6) the moon is between the camera and the planet: the moonShadow on the planet: the shadow ray direction is toward the SUN; the moon is NOT between the fragment and the sun at that moment (the moon is on the camera side!). Wait — CRITICAL CHECK: the eclipse shadow requires the moon between the SUN and the planet. At t=12.6, the moon is between the CAMERA and the planet — is it also between the sun and the planet? The sun az 0.42, the moon az 0.80, camera az 0.80. The moon is on the same side as the camera (rel az 0) — the moon is NOT between the sun and the planet then! The shadow peak was at t=10.5 when the moon is at az 0.468 ≈ sun azimuth — and the camera at az 0.93 — the moon is on the sun side but 27° away in azimuth from the camera. At that moment, from the camera, the moon appears... moon at (30cos0.468, ...) = (26.9, 4.32, 13.1); cam at t=10.5: az = 1.591-0.659 = 0.932, r ≈ 39.3, y ≈ 6.3: cam = (39.3cos0.932, 6.3, 39.3 sin0.932) = (23.6, 6.3, 31.6). moon dir from cam: (3.3, -2.0, -18.5) → mostly -z... vs planet dir: (-23.6, -6.3, -31.6)/40 = (-0.60, -0.16, -0.80). moon dir ̂ = (0.174, -0.105, -0.975). dot = -0.104 + 0.0223 + 0.780 = 0.676 → 47.5° off-axis → the moon is OUT of frame (hFov half 43°, borderline). So the shadow peak happens with the moon just outside the frame — the shadow sweeps onto the disc t 8-13, and the moon enters the frame crossing the disc t≈10.5-15.5 — overlapping nicely: the moon enters the frame (from the side, as a growing silhouette) WHILE its shadow is still finishing its sweep across the disc. Physically coherent-looking ✓.

Hmm wait, but let me re-examine: when the moon is between the camera and the planet (rel az ≈ 0, t=12.6), is its shadow on the planet? Shadow requires alignment moon-sun-planet: at t=12.6, moon az 0.80 vs sun az 0.42: the moon is 22° off the sun direction → cosγ = cos(22°)ish... γ = angle between moonPos and s: computed at a=0.80: cosγ = 0.8866*cos(0.80) + 0.4486*sin(0.80) = 0.8866*0.6967 + 0.4486*0.7174 = 0.6177+0.3218 = 0.9395 → γ = 0.35 rad → shadow distance = 30*sin(0.351)?? d = 30*sqrt(1-0.8827) = 30*0.3425 = 10.3 — just at the planet's edge (10) → the shadow is just leaving the disc at t≈12.6 ✓ consistent with the shadow window ending at 13.1 ✓. 

And the crescent phase at crossing: computed 143.8° → thin crescent ✓.

The moon's shadow & the moon's silhouette both on the disc around t≈11-13 — the umbra near the moon's projected position ✓ plausible.

Now — also confirm the moon is OUT of frame t≈2-9 (so the shadow appears "sourceless" for a few seconds — realistic). Fine.

Let me also check the moon at t=20-24 approaching the limb for the occultation: t=24: computed earlier (with old constants) ≈14.5° off-axis near the limb ✓ with the new A0=-1.103: rel(t) = (A0-az0) + 0.2124t = -2.694+0.2124t: t=24 → 2.403 rad = 137.7°; hmm occultation at rel = π: t = 27.5. At t=24 the moon is at rel 137.7° → offset from the look axis ≈ 180-137.7 = 42.3° — out of frame. It enters the frame when the offset < ~40° → rel > 138°+... the moon's offset from the look axis when behind ≈ π - rel (roughly) → enters frame at rel > π - 0.75 → t > (2.39+2.694)/0.2124 = 23.9 → visible approaching t≈24-26.5, occulted t≈26.5-28.5, emerging just after 30s. Good closing beat ✓ (moon slides behind the planet ~t 26.5-28.5).

Wait — actually as rel → π, the moon's angular offset from the look axis: the moon is behind the planet at distance cam→moon ≈ 39.3+30 ≈ 69; the planet's angular radius from the camera = atan(10/39.3) = 14.3°; the moon's offset from the anti-camera axis ≈ |π - rel|*(30/69)?? The lateral displacement of the moon from the axis ≈ 30*sin(π - rel) roughly (chord) — angular offset ≈ 30 sin(π-rel)/69 → occulted while 30 sin(π-rel) < 10+1.5 → sin(π-rel) < 0.383 → |π-rel| < 0.39 → duration = 2*0.39/0.2124 = 3.7s → occulted t ∈ [25.6, 29.3] ✓ within the window ✓ the moon visibly slides behind the planet edge at ~25.6 ✓.

Great.

Now — also think: is the moon's lit fraction visible approaching occultation? At t≈26, the moon is nearly behind the planet: phase angle (sun-moon-camera): the moon opposite the camera → the moon's lit side faces the sun which is off to the side → we see... the moon at rel 150°: mostly its night side faces us (crescent) — approaching occultation it darkens ✓ natural.

Alright — now also the planetshine on the moon? skip.

Final check of the ring transparency rendering vs the moon crossing: when the moon crosses IN FRONT of the planet (t 10-15), is it in front of the RINGS on screen? The rings pass across the planet's face (the near-side ring ansa crosses the disc lower area when viewed from slightly above the plane? From elevation ~9°, the near ring edge passes BELOW the planet's disc mostly (the ring's near side at radius 15-26 toward the camera appears below the planet). The moon crossing the planet's face is above the near ring edge ✓ minor overlaps fine with depth ✓.

Now let me also add the subtle "shine" of the rings ON the planet's night side (ring irradiance)? Nice detail but skip — scope control.

Also — moon eclipses the RINGS' light? skip.

I think the design is complete. Now write the final file carefully.

Detailed final constants:
- fov 55, near 0.5, far 7000.
- exposure 1.15.

Camera: 
```js
const CAM = { az0: 1.591, w: 0.0628, r0: 40, rDrop: 5, rOsc: 1.4, rOscW: 0.11, y0: 2.2, yAmp: 4.2, yW: 0.09, yPh: 0.7 };
az = CAM.az0 - CAM.w*t;
r = 40 - 5*Math.exp(-0.09*t) + 1.4*Math.sin(0.11*t);
y = 2.2 + 4.2*Math.sin(0.09*t + 0.7);
```

look target drift amplitude 1.6.

Now writing the shaders — full text. Also careful: in the planet fragment I reference `uSunDir` etc. from GLSL_COMMON — the chunk declares uniforms + functions. Let me define:

```js
const CHUNK_UNI = `
uniform vec3 uSunDir;
uniform vec3 uMoonPos;
uniform float uMoonR;
uniform float uPlanetR;
uniform float uRingIn;
uniform float uRingOut;
uniform vec3 uRingN;
uniform float uTime;
`;

const CHUNK_NOISE = ` ...mod289/permute/taylor/snoise/fbm/fbm4... `;

const CHUNK_FX = `
float ringPattern(float x){...}
float moonShadow(vec3 p){...}
float planetShadow(vec3 p){...}
float ringShadow(vec3 p){...}
`;
```
Compose per material: e.g. planet frag = CHUNK_UNI + CHUNK_NOISE + CHUNK_FX + main.

Atmosphere frag: needs uSunDir & uPlanetR & uShellR → include CHUNK_UNI (harmless extra uniforms) — but CHUNK_UNI declares uTime etc. — fine.

Stars/nebula/flare: separate small shaders (nebula needs noise → CHUNK_NOISE only).

The sun shader: standalone.

Ghosts: standalone.

Vignette: standalone.

Now write out. Also — one subtle GLSL thing: in `ringPattern`, I use snoise with args like vec3(x*16.0, 3.7, 8.1) ✓.

Also the fbm loop with p*2.17 + const — fine.

Let me also double check the planet's `h` distribution → ice caps: lat = |sp.y|: caps at |y| > 0.70·(with noise ±0.12) → caps cover the top/bottom ~20% ✓.

Snowy peaks: smoothstep(sea+0.30, sea+0.42, h): h max ≈ 0.78*0.8+0.22*0.8+0.30 ≈ 1.2? cont max ~0.8, det ~0.8: base h ≈ 0.62+0.18 = 0.8 + mountains 0.3 → ~1.1 max, typical land ~0.2-0.45 → snowy on the highest ✓ rare ✓.

Beach band h ∈ [sea, sea+0.035] ✓.

Colors sanity: ocean shallow (0.055, 0.42, 0.38) — bright teal ✓; land moss (0.11, 0.185, 0.095) dark green-teal; rust (0.38, 0.19, 0.08) — burnt orange ✓ contrast good.

Specular only where (1-landMask)(1-ice) ✓.

Biolume: only ocean shelf ✓ night ✓ — visible at t=0 on the left limb (night side) ✓ a subtle signature detail.

Now — the moon's world position when it's between the camera and planet at t≈12.6, distance to the camera ~10.5: near-plane 0.5 ✓ fine; the moon sphere 48 segments ✓.

Moon rotation: mesh.rotation.y = t*0.05 + 2.0 (arbitrary) ✓ terrain rotates slowly ✓.

Also give the moon slight obliquity? skip.

Sun flare occluders: only the planet considered ✓ (rings could occlude the sun — the ring plane is near the camera-planet plane; the sun is 14° above — rings might pass over the sun's disc visually! The rings extend to 26; the sun's direction at elevation ~14°+ above the plane — from the camera at y≈4-6, looking at the planet, the sun appears ~20-24° above the planet's center; the ring's far edge appears at ~atan(26*sin(elev_rel)/dist)... rings near edge-on → the far ring ansa appears just above/below the planet's center ±few degrees — the sun at 20°+ above → no overlap ✓ mostly. Skip ring occlusion in the flare ✓.

Now, let me also handle `THREE.MathUtils.smoothstep` — signature smoothstep(x, min, max) ✓ returns 0 below min, 1 above max ✓.

Write the code. Also — careful with `renderer.autoClear = false` + manual `renderer.clear()` each frame ✓.

Fade overlay:
```html
<div id="fade"></div>
```
```css
#fade{position:fixed;inset:0;background:#000;pointer-events:none;transition:none}
```
JS: `fadeEl.style.opacity = Math.max(0, 1 - t/2.2);` then set display none after.

Also a tiny caption? Skip.

Let me now also micro-verify the ghost positions when the sun is at the frame's edge — ghosts extend beyond — fine (offscreen clipped).

Edge fade: `1 - smoothstep(off, 0.75, 1.5)` — I want the flare to fade as the sun moves out: smoothstep(off; 0.75→1.5): at off<0.75 → 1; at 1.5 → 0 ✓: `const edge = 1 - THREE.MathUtils.smoothstep(off, 0.75, 1.5);`

Also multiply overall flare strength by a gentle breathing? no.

Sun world billboard uDim: also include edge? The billboard is world-anchored; when it's off-frame it doesn't matter; near the limb the occlusion dims it ✓.

Now the NEBULA band: bandN (0.42, 1.0, 0.22) normalized — the band circle is where dot(v, bandN) ≈ 0 → a great circle tilted ~65° from Y — crosses the sky diagonally ✓.

Star band uses the same ✓.

Nebula fragment:
```glsl
vec3 v = normalize(vObjPos);
float bandD = dot(v, uBandN);
float band = exp(-bandN? bandD*bandD*6.0);
float n1 = fbm4(v*3.1 + vec3(3.0, 11.0, 5.0));
float n2 = fbm4(v*6.4 + vec3(23.0, 4.0, 17.0));
float n3 = fbm4(v*12.5 + vec3(9.0, 31.0, 2.0));
vec3 col = vec3(0.0035, 0.007, 0.011);
col += vec3(0.020, 0.085, 0.095)*band*(0.30 + 0.70*smoothstep(-0.4, 0.7, n1));
col += vec3(0.070, 0.028, 0.075)*band*smoothstep(0.05, 0.75, n2)*0.65;
col += vec3(0.045, 0.075, 0.080)*smoothstep(0.35, 0.9, n3)*0.35*(0.35 + 0.65*band);
gl_FragColor = vec4(col, 1.0);
```
Values ≤ ~0.1 → faint ✓ with ACES→ dimmer; maybe boost ×1.3. It's a background tint — fine.

uBandN uniform in nebula; stars use bandN in JS ✓.

Let me write everything now, being careful about syntax. I'll also add `precision` — ShaderMaterial handles.

One concern: `#include <tonemapping_fragment>` — needs to be inside main() after gl_FragColor assignment ✓.

Also the ghost/halo/streak/vignette materials: skip tonemapping includes (screen-space composite) ✓ but they still need `transparent: true` for blending to apply? With AdditiveBlending, transparent true puts them in the transparent pass ✓. The vignette uses NormalBlending with alpha → transparent true ✓.

For the flare scene meshes: frustumCulled — the ortho objects positioned each frame; set mesh.frustumCulled = false to be safe (positions in ortho space are fine anyway) ✓.

Also the sun billboard: frustumCulled = false (billboard vertex shader moves vertices in view space; the mesh's bounding sphere at its position is huge radius... geometry PlaneGeometry(2,2) with scale via uniform — the mesh's bounding sphere is small (radius ~1.4) at position 850 → culling uses the bounding sphere at the mesh's world position ✓ correct (the quad is drawn around the center) ✓ fine. But to be safe set frustumCulled = false ✓.

Now — one more look at the ring alpha & color: with AdditiveBlending? No — NormalBlending with alpha ✓ (rings occlude the planet/stars naturally). depthWrite false ✓ (so the moon behind shows through gaps ✓ and the planet... wait — rings BEHIND the planet: ring fragments behind the planet are culled by the planet's depth ✓; rings in FRONT of the planet blend over ✓.

Cloud sphere vs atmosphere render order: atmosphere (2) draws AFTER clouds (1): atmosphere is additive → adds glow over the cloud silhouettes ✓ good.

Also the atmosphere shell on the DAY side facing the camera adds a cyan wash over the whole disc edge — glow(x) is significant only near the limb (pow(1-x, 2.4)) ✓.

Let me also add a very subtle overall blue-ish ambient scatter on the planet's day side: the fresnel term covers it ✓.

One more — the planet shader's `rSh` (ring shadow) is multiplied into the diffuse; on the night side day=0 so no effect ✓.

Write the moon's material uniforms: shared ✓.

Final: write out the whole HTML. Let me carefully draft the full code in my head/on paper now, then output.

Also remember: NO import map needed (provided). Just `import * as THREE from 'three'` ✓.

Also handle `renderer.getPixelRatio()` for star size ✓ update on resize ✓.

Potential undefined: `camera.getWorldDirection(target)` requires the target vector ✓ and the camera's matrixWorld updated — call camera.updateMatrixWorld() after lookAt ✓ (lookAt sets quaternion; updateMatrixWorld computes matrixWorld ✓ needed for getWorldDirection & project ✓).

Actually `camera.lookAt` uses the camera's up ✓ fine.

Also `.project(camera)` uses matrixWorldInverse & projectionMatrix — updateMatrixWorld updates matrixWorld; matrixWorldInverse is updated by the renderer during render — but I call updateFlare BEFORE rendering → matrixWorldInverse may be stale. Fix: `camera.updateMatrixWorld(); _ndc.copy(SUN_POS).project(camera);` — project() uses camera.matrixWorldInverse — which is updated by updateMatrixWorld? `Vector3.project(camera)` = applyMatrix4(camera.matrixWorldInverse).applyMatrix4(camera.projectionMatrix) — matrixWorldInverse is computed in `camera.updateMatrixWorld()`?? Actually Object3D.updateMatrixWorld updates matrixWorld; Camera.updateMatrixWorld ALSO updates matrixWorldInverse (Camera overrides updateMatrixWorld to derive matrixWorldInverse ✓ yes: Camera.prototype.updateMatrixWorld calls super then matrixWorldInverse.copy(matrixWorld).invert() ✓). So calling camera.updateMatrixWorld() manually is enough ✓.

Alright — also the ORDER: set camera pos/lookAt → updateMatrixWorld → update shared uniforms (moon pos etc.) → updateFlare → render.

Time uniform: shared.uTime.value = t ✓.

Planet/cloud/atmo/rings/moon materials reference shared.uMoonPos etc. ✓ set moonPos each frame before render ✓.

Now, the moon orbit tilt: applyEuler? I'll compute directly:
```js
const sa = Math.sin(ma), ca2 = Math.cos(ma);
moonPos.set(MOON_ORBIT*ca2, MOON_ORBIT*sa*Math.sin(MOON_INC)*(-1)?? 
```
From earlier: y = -Rm sin a sin(inc) with inc = -0.32: sin(inc) = -0.3146 → y = Rm*0.3146*sa. Just write: `moonPos.set(MOON_ORBIT*Math.cos(ma), -MOON_ORBIT*Math.sin(ma)*Math.sin(MOON_INC), MOON_ORBIT*Math.sin(ma)*Math.cos(MOON_INC));` ✓ generic ✓.

Orbit line: same formula per point ✓.

Now the FLARE ghosts: sizes relative to screen height (ortho units): halo 2.0; ghosts 0.06-0.30; streak (2.6*aspect? no — scale.x = 2.6 covers everything since ortho x-range = 2*aspect... a quad of size 2.6 centered covers [-1.3, 1.3] ortho-x — for aspect 1.78 the screen spans [-1.78, 1.78] → the streak covers 73% — with exp falloff the visible part is central ~[-0.9, 0.9] ✓ good. Actually make scale.x = 3.6 so the streak spans beyond the screen for wide aspects ✓ hmm the streak should span the full width when the sun is centered: 3.6 covers [-1.8,1.8] ✓ ok. But when the sun is off to the side (ndc.x = 0.8 → X = 0.8*aspect = 1.42), the streak extends ±1.8 → partially visible ✓ good.

Ghost tint values: muted: teal (0.16,0.42,0.44), amber (0.55,0.36,0.14), violet (0.30,0.20,0.42), warm (0.55,0.42,0.26), cyan (0.14,0.36,0.40), rose (0.42,0.22,0.24). Base vis multipliers small (0.2-0.45) ✓ subtle.

Halo tint: (0.55, 0.42, 0.30) with fall 2.6, vis 0.30.
Streak tint: (0.65, 0.45, 0.25), uVis*0.5.

Sun billboard colors tuned earlier ✓.

Now — write the planet vertex/frag & all. Also the cloud vertex uses the common vertex ✓ (needs vObjPos, vWorldPos, vNormal) ✓.

Also — the atmosphere mesh: only needs vWorldPos (b-parameter). Common vertex fine.

Sun: custom.

Let me also reconsider the clouds' alpha near the limb producing a hard sphere edge against space: alpha at the limb: the cloud sphere silhouette — clouds alpha there ~0-0.9; the atmosphere glow covers the transition ✓.

Also — I want a subtle CLOUD SHADOW on the planet? (clouds darkening the surface) — would need the cloud density sampled at the surface point along the sun ray — expensive; skip (clouds+surface already rich).

One more: the planet's night side is VERY dark (albedo*0.01 ambient) + moonlight 0.1-0.19 — visible faintly ✓ + biolume coasts ✓ + rim ✓. Good.

Also — the terminator softness: day = clamp(NdL) is hard-ish; soften: day = smoothstep(-0.08, 0.25, NdL)? Use `float day = clamp(NdL*1.15 + 0.05, 0.0, 1.0);` hmm — a slightly lifted terminator looks better: `float day = smoothstep(-0.12, 0.30, NdL);` I'll use smoothstep(-0.1, 0.35, NdL) — soft twilight band ✓. But then the specular should use the same ✓ fine.

For the moon: ndl = clamp(dot*1.2+0.02, 0, 1)? keep sharper: max(dot,0)^— fine with slight soften: `float ndl = smoothstep(-0.06, 0.25, dot(N, uSunDir));`

OK writing final code now. Also — the nebula & stars are inside the "sky" group; the sky group rotates → the sun stays fixed (sun not in the sky group) ✓.

Counting output size: the file will be ~600-700 lines — fine.

Let me also double check `RingGeometry` normal attribute: it has normals (0,0,1) — after rotation.x=-π/2 → (0,1,0)?? I don't use the attribute normal in the ring shader (I use uRingN) ✓.

Planet geometry: SphereGeometry(10, 96, 64) — 96 width segments for a smooth silhouette with the fresnel rim ✓.

The clouds: SphereGeometry(10.35, 80, 56).
Shell: SphereGeometry(12.2, 64, 48).
Moon: SphereGeometry(1.5, 48, 32).

RingGeometry(15, 26, 360, 2)?? thetaSegments 360 is a lot of verts (361*3) — fine (or 256). Use 256, 2.

Now the animate loop timing: ts from rAF in ms ✓ t = ts*0.001 ✓.

Also — subtle idea: display a tiny corner caption like "KEPLER-1649c // ORBITAL SURVEY 07" in HTML? The user didn't ask; a small elegant caption could add authored feel... but any text overlay might be undesirable in a pure render. I'll add a very subtle caption bottom-left in a monospace system font with low opacity — hmm, "no external fonts" — system monospace is fine. But it might distract from the "recording" use-case. I'll skip text overlays entirely except the fade. Actually a tiny unobtrusive label adds a "mission telemetry" vibe... I'll skip — keep the frame clean for recording.

Final code writing — now, for real. I'll write it in one pass with care.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Veyra-3 · Orbital Survey</title>
<style>
  html, body { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; background: #000; }
  canvas { display: block; }
  #fade { position: fixed; inset: 0; background: #000; pointer-events: none; }
</style>
</head>
<body>
<div id="fade"></div>
<script type="module">
import * as THREE from 'three';

/* ---------------------------------------------------------------- setup */
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setClearColor(0x000105, 1);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.12;
renderer.autoClear = false;
document.body.appendChild(renderer.domElement);

const scene    = new THREE.Scene();
const camera   = new THREE.PerspectiveCamera(55, innerWidth / innerHeight, 0.5, 7000);

const SUN_DIR  = new THREE.Vector3(1.0, 0.28, 0.44).normalize();
const SUN_POS  = SUN_DIR.clone().multiplyScalar(850);
const PLANET_R = 10.0, CLOUD_R = 10.35, SHELL_R = 12.2;
const RING_IN  = 15.0, RING_OUT = 26.0;
const MOON_R   = 1.5, MOON_ORBIT = 30.0, MOON_W = 0.1496, MOON_A0 = -1.103, MOON_INC = -0.32;
const TILT     = -0.18;

const planetGroup = new THREE.Group();
planetGroup.rotation.z = TILT;
scene.add(planetGroup);

const ringN = new THREE.Vector3(0, 1, 0).applyAxisAngle(new THREE.Vector3(0, 0, 1), TILT);

/* shared uniforms */
const shared = {
  uTime:     { value: 0 },
  uSunDir:   { value: SUN_DIR },
  uMoonPos:  { value: new THREE.Vector3() },
  uMoonR:    { value: MOON_R },
  uPlanetR:  { value: PLANET_R },
  uRingIn:   { value: RING_IN },
  uRingOut:  { value: RING_OUT },
  uRingN:    { value: ringN },
};
```

Then GLSL chunks (as JS template strings), then materials & meshes, flare scene, stars, resize, animate.

Let me write the GLSL chunks in final form:

```js
const NOISE = /* glsl */`
vec3 mod289(vec3 x){ return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 mod289(vec4 x){ return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 permute(vec4 x){ return mod289(((x * 34.0) + 1.0) * x); }
vec4 taylorInvSqrt(vec4 r){ return 1.79284291400159 - 0.85373472095314 * r; }
float snoise(vec3 v){
  const vec2 C = vec2(1.0/6.0, 1.0/3.0);
  const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
  vec3 i  = floor(v + dot(v, C.yyy));
  vec3 x0 = v - i + dot(i, C.xxx);
  vec3 g = step(x0.yzx, x0.xyz);
  vec3 l = 1.0 - g;
  vec3 i1 = min(g.xyz, l.zxy);
  vec3 i2 = max(g.xyz, l.zxy);
  vec3 x1 = x0 - i1 + C.xxx;
  vec3 x2 = x0 - i2 + C.yyy;
  vec3 x3 = x0 - D.yyy;
  i = mod289(i);
  vec4 p = permute(permute(permute(
            i.z + vec4(0.0, i1.z, i2.z, 1.0))
          + i.y + vec4(0.0, i1.y, i2.y, 1.0))
          + i.x + vec4(0.0, i1.x, i2.x, 1.0));
  float n_ = 0.142857142857;
  vec3 ns = n_ * D.wyz - D.xzx;
  vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
  vec4 x_ = floor(j * ns.z);
  vec4 y_ = floor(j - 7.0 * x_);
  vec4 x = x_ * ns.x + ns.yyyy;
  vec4 y = y_ * ns.x + ns.yyyy;
  vec4 h = 1.0 - abs(x) - abs(y);
  vec4 b0 = vec4(x.xy, y.xy);
  vec4 b1 = vec4(x.zw, y.zw);
  vec4 s0 = floor(b0) * 2.0 + 1.0;
  vec4 s1 = floor(b1) * 2.0 + 1.0;
  vec4 sh = -step(h, vec4(0.0));
  vec4 a0 = b0.xzyw + s0.xzyw * sh.xxyy;
  vec4 a1 = b1.xzyw + s1.xzyw * sh.zzww;
  vec3 p0 = vec3(a0.xy, h.x);
  vec3 p1 = vec3(a0.zw, h.y);
  vec3 p2 = vec3(a1.xy, h.z);
  vec3 p3 = vec3(a1.zw, h.w);
  vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
  p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
  vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
  m = m * m;
  return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
}
float fbm(vec3 p){
  float f = 0.0, a = 0.54;
  for(int i = 0; i < 5; i++){ f += a * snoise(p); p = p * 2.17 + vec3(11.7, 5.3, 9.1); a *= 0.53; }
  return f;
}
float fbm4(vec3 p){
  float f = 0.0, a = 0.55;
  for(int i = 0; i < 4; i++){ f += a * snoise(p); p = p * 2.23 + vec3(7.3, 13.1, 3.9); a *= 0.55; }
  return f;
}
`;
```
Note `vec4 b0 = vec4(x.xy, y.xy)` — earlier I wrote b0 = vec4(x.xy, y.xy) ✓ equivalent to the original (which uses vec4(x.xy, y.xy)) ✓.

Wait — original: `vec4 b0 = vec4( x.xy, y.xy ); vec4 b1 = vec4( x.zw, y.zw );` ✓.

`vec3 x3 = x0 - D.yyy;` — D.yyy = 0.5 → x3 = x0 - 0.5 ✓ (=-1+3C.x = -1+0.5 = -0.5 ✓).

Also `i1 = min(g.xyz, l.zxy)` ✓ and `i2 = max(...)` ✓.

FX chunk:

```js
const FX = /* glsl */`
float ringPattern(float x){
  float v = snoise(vec3(x * 16.0, 3.7, 8.1)) * 0.55
          + snoise(vec3(x * 42.0, 9.2, 3.3)) * 0.28
          + snoise(vec3(x * 7.0, 1.2, 5.5)) * 0.45;
  v = v * 0.5 + 0.5;
  float a = smoothstep(0.16, 0.68, v);
  float fine = snoise(vec3(x * 130.0, 4.4, 9.9));
  a *= 0.66 + 0.34 * fine;
  float g1 = (x - 0.60) * 22.0;
  float g2 = (x - 0.84) * 34.0;
  a *= 1.0 - 0.92 * exp(-g1 * g1);
  a *= 1.0 - 0.50 * exp(-g2 * g2);
  a *= smoothstep(0.0, 0.055, x) * (1.0 - smoothstep(0.93, 1.0, x));
  return clamp(a, 0.0, 1.0);
}
float moonShadow(vec3 p){
  vec3 oc = uMoonPos - p;
  float along = dot(oc, uSunDir);
  if(along <= 0.0) return 1.0;
  float d = length(oc - uSunDir * along);
  return smoothstep(uMoonR * 0.5, uMoonR * 1.75, d);
}
float planetShadow(vec3 p){
  float along = dot(-p, uSunDir);
  if(along <= 0.0) return 1.0;
  float d = length(p + uSunDir * along);
  return smoothstep(uPlanetR * 0.86, uPlanetR * 1.30, d);
}
float ringShadow(vec3 p){
  float denom = dot(uSunDir, uRingN);
  if(abs(denom) < 0.0008) return 1.0;
  float t = -dot(p, uRingN) / denom;
  if(t <= 0.0) return 1.0;
  float r = length(p + uSunDir * t);
  float x = (r - uRingIn) / (uRingOut - uRingIn);
  if(x < 0.0 || x > 1.0) return 1.0;
  return 1.0 - ringPattern(x) * 0.55;
}
`;
```

UNI chunk:
```js
const UNI = /* glsl */`
uniform float uTime;
uniform vec3  uSunDir;
uniform vec3  uMoonPos;
uniform float uMoonR;
uniform float uPlanetR;
uniform float uRingIn;
uniform float uRingOut;
uniform vec3  uRingN;
`;
```

Vertex (shared):
```js
const VERT = /* glsl */`
varying vec3 vObjPos;
varying vec3 vWorldPos;
varying vec3 vNormal;
void main(){
  vObjPos   = position;
  vec4 wp   = modelMatrix * vec4(position, 1.0);
  vWorldPos = wp.xyz;
  vNormal   = normalize(mat3(modelMatrix) * normal);
  gl_Position = projectionMatrix * viewMatrix * wp;
}
`;
```

Planet frag:

```js
const PLANET_FRAG = UNI + NOISE + FX + /* glsl */`
varying vec3 vObjPos;
varying vec3 vWorldPos;
varying vec3 vNormal;
void main(){
  vec3 sp = normalize(vObjPos);
  vec3 N  = normalize(vNormal);
  vec3 V  = normalize(cameraPosition - vWorldPos);

  /* terrain field */
  float cont = fbm(sp * 1.5 + vec3(11.0, 3.0, 27.0));
  float det  = fbm(sp * 5.2 + vec3(2.0, 14.0, 5.0));
  float mtn  = 1.0 - abs(snoise(sp * 3.1 + vec3(31.0, 13.0, 7.0)));
  mtn *= mtn;
  float sea = 0.06;
  float h = cont * 0.78 + det * 0.22;
  float landMask = smoothstep(sea - 0.004, sea + 0.035, h);
  h += mtn * 0.32 * landMask * smoothstep(sea + 0.03, sea + 0.26, h);

  /* oceans */
  float depth = clamp((sea - h) * 3.4, 0.0, 1.0);
  vec3 ocean = mix(vec3(0.052, 0.40, 0.37), vec3(0.014, 0.145, 0.185), smoothstep(0.0, 0.30, depth));
  ocean = mix(ocean, vec3(0.004, 0.040, 0.070), smoothstep(0.30, 0.80, depth));

  /* land */
  float bio = fbm4(sp * 2.6 + vec3(47.0, 8.0, 21.0));
  vec3 land = mix(vec3(0.36, 0.185, 0.078), vec3(0.105, 0.180, 0.092), smoothstep(-0.35, 0.42, bio));
  land = mix(land, vec3(0.335, 0.29, 0.225), smoothstep(sea + 0.09, sea + 0.24, h));
  land = mix(land, vec3(0.49, 0.465, 0.44), smoothstep(sea + 0.26, sea + 0.38, h));
  float beach = smoothstep(sea, sea + 0.010, h) * (1.0 - smoothstep(sea + 0.010, sea + 0.035, h));
  land = mix(land, vec3(0.55, 0.45, 0.28), beach * 0.85);

  /* ice */
  float lat  = abs(sp.y);
  float capN = fbm4(sp * 3.4 + vec3(5.0, 41.0, 17.0));
  float ice  = clamp(smoothstep(0.68, 0.79, lat + capN * 0.13)
             + smoothstep(sea + 0.30, sea + 0.42, h), 0.0, 1.0);
  vec3 iceCol = mix(vec3(0.85, 0.92, 0.96), vec3(0.60, 0.75, 0.85), smoothstep(0.3, 0.8, det) * 0.45);

  vec3 albedo = mix(ocean, land, landMask);
  albedo = mix(albedo, iceCol, ice);

  /* lighting */
  float NdL = dot(N, uSunDir);
  float day = smoothstep(-0.12, 0.32, NdL);
  float mSh = moonShadow(vWorldPos);
  float rSh = ringShadow(vWorldPos);
  vec3 sunTint = vec3(1.0, 0.90, 0.77);
  vec3 col = albedo * (vec3(0.011, 0.017, 0.026) + sunTint * 1.5 * day * mSh * rSh);

  vec3 H = normalize(uSunDir + V);
  float ndh = max(dot(N, H), 0.0);
  float glint = pow(ndh, 130.0) * 1.35 + pow(ndh, 9.0) * 0.10;
  col += sunTint * glint * (1.0 - landMask) * (1.0 - ice) * day * mSh * rSh;

  /* moonlight */
  float ml = max(dot(N, normalize(uMoonPos - vWorldPos)), 0.0);
  col += albedo * vec3(0.10, 0.17, 0.23) * ml * (1.0 - day);

  /* bioluminescent shorelines on the night side */
  float night = 1.0 - smoothstep(-0.16, 0.10, NdL);
  float shelf = smoothstep(sea - 0.075, sea - 0.004, h) * (1.0 - landMask);
  float clus  = smoothstep(0.18, 0.60, snoise(sp * 6.5 + vec3(61.0, 23.0, 9.0)));
  float spark = smoothstep(0.25, 0.70, snoise(sp * 44.0 + vec3(13.0, 51.0, 29.0)));
  col += vec3(0.05, 0.72, 0.46) * shelf * clus * (0.30 + 0.70 * spark) * night * (1.0 - ice) * 0.85;

  /* atmospheric fresnel rim + warm terminator */
  float fres = pow(1.0 - clamp(dot(N, V), 0.0, 1.0), 2.6);
  float tw = (NdL - 0.06) * 3.2;
  vec3 rimCol = mix(vec3(0.18, 0.50, 0.58), vec3(0.95, 0.42, 0.14), clamp(exp(-tw * tw) * 1.15, 0.0, 1.0));
  col += rimCol * fres * (0.16 + 0.90 * day);

  gl_FragColor = vec4(col, 1.0);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}
`;
```

Cloud frag:

```js
const CLOUD_FRAG = UNI + NOISE + FX + /* glsl */`
varying vec3 vObjPos;
varying vec3 vWorldPos;
varying vec3 vNormal;
void main(){
  vec3 sp = normalize(vObjPos);
  float wa = fbm(sp * 2.3 + vec3(7.0, uTime * 0.010, 2.0)) * 1.35;
  float ca = cos(wa), sa = sin(wa);
  vec3 q = sp;
  q.xz = mat2(ca, -sa, sa, ca) * sp.xz;
  float d1 = fbm(q * 3.0 + vec3(3.0, 12.0, 7.0 + uTime * 0.014));
  float d2 = fbm(q * 7.6 + vec3(21.0, 4.0, 15.0 - uTime * 0.020));
  float cover = smoothstep(0.02, 0.52, d1 * 0.72 + d2 * 0.40 + 0.12);
  if(cover < 0.004) discard;

  vec3 N = normalize(vNormal);
  float day = smoothstep(-0.14, 0.30, dot(N, uSunDir));
  float shade = 0.60 + 0.40 * smoothstep(-0.45, 0.70, d2);
  float mSh = moonShadow(vWorldPos);
  float rSh = ringShadow(vWorldPos);

  vec3 col = mix(vec3(0.028, 0.042, 0.072), vec3(1.02, 1.00, 0.97) * shade * 1.16, day);
  col *= mix(0.20, 1.0, mSh) * mix(0.40, 1.0, rSh);
  float tw = (dot(N, uSunDir) - 0.04) * 3.0;
  col += vec3(0.40, 0.16, 0.05) * exp(-tw * tw) * 0.22;

  gl_FragColor = vec4(col, cover * 0.93);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}
`;
```
Hmm — the terminator warm tint: `exp(-tw*tw)*0.22` adds warm everywhere near the terminator including the night side slightly — acceptable.

Atmosphere frag:
```js
const ATMO_FRAG = UNI + /* glsl */`
varying vec3 vWorldPos;
uniform float uShellR;
void main(){
  vec3 C = cameraPosition;
  vec3 D = normalize(vWorldPos - C);
  float tc = max(-dot(C, D), 0.0);
  vec3 closest = C + D * tc;
  float b = length(closest);
  float x = clamp((b - uPlanetR) / (uShellR - uPlanetR), 0.0, 1.0);
  float glow = pow(1.0 - x, 2.3);
  vec3 rn = normalize(closest);
  float sd = dot(rn, uSunDir);
  float day = clamp(sd * 0.72 + 0.42, 0.04, 1.0);
  float tw = (sd - 0.05) * 2.4;
  vec3 col = mix(vec3(0.16, 0.50, 0.60), vec3(1.0, 0.42, 0.14), clamp(exp(-tw * tw) * 1.25, 0.0, 1.0));
  float fwd = pow(max(dot(D, uSunDir), 0.0), 3.0);
  vec3 c = col * glow * day * 1.55 + vec3(1.0, 0.45, 0.18) * fwd * glow * 0.45;
  gl_FragColor = vec4(c, 1.0);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}
`;
```

Ring frag:
```js
const RING_FRAG = UNI + NOISE + FX + /* glsl */`
varying vec3 vObjPos;
varying vec3 vWorldPos;
void main(){
  float r = length(vObjPos.xy);
  float x = (r - uRingIn) / (uRingOut - uRingIn);
  float a = ringPattern(x);
  if(a < 0.004) discard;
  vec3 V = normalize(cameraPosition - vWorldPos);
  float ndl = dot(uRingN, uSunDir);
  float li = 0.34 + 0.85 * abs(ndl);
  if(ndl < 0.0) li *= 0.58;
  float fwd = pow(max(dot(-V, uSunDir), 0.0), 4.0);
  li += fwd * 1.15;
  float psh = planetShadow(vWorldPos);
  vec3 col = mix(vec3(0.52, 0.455, 0.375), vec3(0.345, 0.325, 0.305), x);
  col *= li * planetShadow(vWorldPos) * vec3(1.05, 0.98, 0.90);
  gl_FragColor = vec4(col, a * 0.95);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}
`;
```

Moon frag:
```js
const MOON_FRAG = UNI + NOISE + FX + /* glsl */`
varying vec3 vObjPos;
varying vec3 vWorldPos;
varying vec3 vNormal;
void main(){
  vec3 sp = normalize(vObjPos);
  vec3 N = normalize(vNormal);
  float m1 = fbm(sp * 3.2 + vec3(9.0, 2.0, 17.0));
  float m2 = fbm4(sp * 8.5 + vec3(27.0, 5.0, 3.0));
  float mare = smoothstep(0.15, 0.58, fbm(sp * 1.6 + vec3(51.0, 13.0, 7.0)));
  vec3 albedo = mix(vec3(0.55, 0.53, 0.50), vec3(0.33, 0.31, 0.29), clamp(m1 * 0.5 + 0.5, 0.0, 1.0));
  albedo = mix(albedo, vec3(0.22, 0.23, 0.27), mare * 0.75);
  albedo *= 0.88 + 0.24 * clamp(m2 * 0.5 + 0.5, 0.0, 1.0);
  float ndl = smoothstep(-0.05, 0.28, dot(N, uSunDir));
  float psh = planetShadow(vWorldPos);
  vec3 col = albedo * (vec3(0.007, 0.009, 0.013) + vec3(1.0, 0.93, 0.85) * 1.35 * ndl * psh);
  col += albedo * vec3(0.55, 0.14, 0.05) * ndl * (1.0 - psh) * 0.85;
  gl_FragColor = vec4(col, 1.0);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}
`;
```

Sun shaders:
```js
const SUN_VERT = /* glsl */`
uniform float uSize;
varying vec2 vUv;
void main(){
  vUv = uv;
  vec4 mv = modelViewMatrix * vec4(0.0, 0.0, 0.0, 1.0);
  mv.xy += position.xy * uSize;
  gl_Position = projectionMatrix * mv;
}
`;
const SUN_FRAG = /* glsl */`
uniform float uDim;
varying vec2 vUv;
void main(){
  vec2 p = vUv * 2.0 - 1.0;
  float r2 = dot(p, p);
  float core = exp(-r2 * 95.0) * 3.2;
  float glow = exp(-r2 * 6.5) * 0.55;
  float halo = exp(-sqrt(r2) * 2.6) * 0.16;
  float stH = exp(-abs(p.y) * 36.0) * exp(-abs(p.x) * 3.0);
  float stV = exp(-abs(p.x) * 40.0) * exp(-abs(p.y) * 4.5) * 0.55;
  vec3 col = vec3(1.0, 0.95, 0.88) * core
           + vec3(1.0, 0.78, 0.50) * (glow + halo)
           + vec3(1.0, 0.60, 0.28) * (stH * 0.85 + stV * 0.45);
  gl_FragColor = vec4(col * uDim, 1.0);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}
`;
```

Stars:
```js
const STAR_VERT = /* glsl */`
attribute float aSize;
attribute vec3  aCol;
attribute float aTw;
attribute float aPh;
uniform float uTime;
uniform float uPR;
varying vec3 vCol;
varying float vA;
void main(){
  vCol = aCol;
  vA = 0.70 + 0.30 * sin(uTime * aTw + aPh);
  gl_PointSize = aSize * uPR?? 
```
wait — uniform uPR needed: add `uniform float uPR;` ✓.
```glsl
  vec4 mv = modelViewMatrix * vec4(position, 1.0);
  gl_PointSize = aSize * uPR;
  gl_Position = projectionMatrix * mv;
}
`;
const STAR_FRAG = /* glsl */`
varying vec3 vCol;
varying float vA;
void main(){
  vec2 p = gl_PointCoord * 2.0 - 1.0;
  float d2 = dot(p, p);
  if(d2 > 1.0) discard;
  float a = 1.0 - d2;
  gl_FragColor = vec4(vCol * vA * a * a, 1.0);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}
`;
```

Nebula frag:
```js
const NEB_FRAG = /* glsl */`
uniform vec3 uBandN;
varying vec3 vObjPos;
` + NOISE + /* glsl */`
void main(){
  vec3 v = normalize(vObjPos);
  float bd = dot(v, uBandN);
  float band = exp(-bd * bd * 6.5);
  float n1 = fbm4(v * 3.1 + vec3(3.0, 11.0, 5.0));
  float n2 = fbm4(v * 6.3 + vec3(23.0, 4.0, 17.0));
  float n3 = fbm4(v * 12.5 + vec3(9.0, 31.0, 2.0));
  vec3 col = vec3(0.004, 0.008, 0.013);
  col += vec3(0.020, 0.085, 0.095) * band * (0.30 + 0.70 * smoothstep(-0.4, 0.7, n1));
  col += vec3(0.075, 0.030, 0.080) * band * smoothstep(0.05, 0.75, n2) * 0.60;
  col += vec3(0.040, 0.070, 0.075) * smoothstep(0.30, 0.90, n3) * 0.35 * (0.35 + 0.65 * band);
  gl_FragColor = vec4(col, 1.0);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}
`;
```
Nebula vertex: needs vObjPos only:
```glsl
varying vec3 vObjPos;
void main(){ vObjPos = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }
```

Flare ghost shader:
```js
const GHOST_FRAG = /* glsl */`
uniform vec3 uTint;
uniform float uVis;
uniform float uFall;
uniform float uRing;
varying vec2 vUv;
void main(){
  vec2 p = vUv * 2.0 - 1.0;
  float r2 = dot(p, p);
  float disc = exp(-r2 * uFall);
  float g = (r2 - 0.55) * 6.0;
  float ring = exp(-g * g) * uRing * 0.65;
  float a = (disc + ring) * uVis;
  gl_FragColor = vec4(uTint * a, 1.0);
}
`;
const GHOST_VERT = `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`;
```

Streak:
```js
const STREAK_FRAG = /* glsl */`
uniform vec3 uTint;
uniform float uVis;
varying vec2 vUv;
void main(){
  vec2 p = vUv * 2.0 - 1.0;
  float a = exp(-p.y * p.y * 34.0) * exp(-abs(p.x) * 2.4) * uVis;
  gl_FragColor = vec4(uTint * a, 1.0);
}
`;
```
Wait — earlier I planned quad scale (3.6, 0.10) with falloff 30 in y... let me: scale.y = 0.09 units; falloff exp(-p.y²*34): visible core |p.y| < 0.25 → 0.0225 units ≈ 1.1% screen height ✓ ok.

Vignette:
```js
const VIG_FRAG = /* glsl */`
uniform float uAspect;
varying vec2 vUv;
void main(){
  vec2 p = vUv * 2.0 - 1.0;
  p.x *= uAspect;
  float d = length(p);
  float a = smoothstep(0.62, 1.45, d) * 0.42;
  gl_FragColor = vec4(vec3(0.0), a);
}
`;
```

Now build meshes:

```js
const planetMat = new THREE.ShaderMaterial({
  uniforms: { uTime: shared.uTime, uSunDir: shared.uSunDir, uMoonPos: shared.uMoonPos,
              uMoonR: shared.uMoonR, uPlanetR: shared.uPlanetR, uRingIn: shared.uRingIn,
              uRingOut: shared.uRingOut, uRingN: shared.uRingN },
  vertexShader: VERT, fragmentShader: PLANET_FRAG
});
const planet = new THREE.Mesh(new THREE.SphereGeometry(PLANET_R, 96, 64), planetMat);
planetGroup.add(planet);

const cloudMat = new THREE.ShaderMaterial({
  uniforms: { ...same... },
  vertexShader: VERT, fragmentShader: CLOUD_FRAG,
  transparent: true, depthWrite: false
});
const clouds = new THREE.Mesh(new THREE.SphereGeometry(CLOUD_R, 80, 56), cloudMat);
clouds.renderOrder = 1;
planetGroup.add(clouds);

const atmoMat = new THREE.ShaderMaterial({
  uniforms: { uTime, uSunDir, uPlanetR, uShellR: { value: SHELL_R } },
  vertexShader: VERT, fragmentShader: ATMO_FRAG,
  side: THREE.BackSide, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending
});
const atmo = new THREE.Mesh(new THREE.SphereGeometry(SHELL_R, 64, 48), atmoMat);
atmo.renderOrder = 2;
planetGroup.add(atmo);

const ringMat = new THREE.ShaderMaterial({
  uniforms: {...shared refs...},
  vertexShader: VERT, fragmentShader: RING_FRAG,
  side: THREE.DoubleSide, transparent: true, depthWrite: false
});
const rings = new THREE.Mesh(new THREE.RingGeometry(RING_IN, RING_OUT, 256, 2), ringMat);
rings.rotation.x = -Math.PI / 2;
rings.renderOrder = 3;
planetGroup.add(rings);

const moonMat = new THREE.ShaderMaterial({ uniforms: {...}, vertexShader: VERT, fragmentShader: MOON_FRAG });
const moon = new THREE.Mesh(new THREE.SphereGeometry(MOON_R, 48, 32), moonMat);
scene.add(moon);
```

Sun:
```js
const sunMat = new THREE.ShaderMaterial({
  uniforms: { uSize: { value: 150 }, uDim: { value: 1 } },
  vertexShader: SUN_VERT, fragmentShader: SUN_FRAG,
  transparent: true, depthWrite: false, blending: THREE.AdditiveBlending
});
const sun = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), sunMat);
sun.position.copy(SUN_POS);
sun.frustumCulled = false;
scene.add(sun);
```

Sky group:
```js
const sky = new THREE.Group();
scene.add(sky);
nebula = Mesh(SphereGeometry(2600, 48, 32), nebMat side BackSide); sky.add
stars Points; sky.add
```
Wait — the nebula sphere radius 2600 vs camera far 7000 ✓; the nebula is centered at origin; the camera moves within ✓ BackSide ✓.

Star material uniforms: uTime: shared.uTime, uPR: { value: renderer.getPixelRatio() }.

Flare scene:
```js
const flareScene = new THREE.Scene();
const flareCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 10);
flareCam.position.z = 5;

const quad = new THREE.PlaneGeometry(1, 1);
function ghost(tint, size, fall, ringAmt, base){
  const m = new THREE.ShaderMaterial({
    uniforms: { uTint: { value: new THREE.Vector3(...tint) }, uVis: { value: 0 }, uFall: { value: fall }, uRing: { value: ringAmt } },
    vertexShader: GHOST_VERT, fragmentShader: GHOST_FRAG,
    transparent: true, depthWrite: false, depthTest: false, blending: THREE.AdditiveBlending
  });
  const mesh = new THREE.Mesh(quad, m);
  mesh scale...
  flareScene.add(mesh);
  return { mesh, base };
}
```
Hmm — uTint as vec3 uniform; use Vector3 ✓ (or Color — Color works as vec3 ✓; I'll use THREE.Color).

Ghosts list:
```js
const halo = ghost([0.55, 0.42, 0.30], 2.1, 2.4, 0.0, 0.30);
const g1 = ghost([0.16, 0.42, 0.44], 0.10, 15.0, 1.0, 0.34);
const g2 = ghost([0.30, 0.20, 0.42], 0.16, 18.0, 1.0, 0.26);
const g3 = ghost([0.55, 0.42, 0.18], 0.07, 10.0, 0.7, 0.38);
const g4 = ghost([0.14, 0.36, 0.40], 0.24, 22.0, 1.0, 0.20);
const g5 = ghost([0.42, 0.24, 0.30], 0.12, 12.0, 0.5, 0.22);
const ghosts = [halo, g1, g2, g3, g4, g5];  — halo handled with k=1 (same pos as sun)
ghost positions: halo at sun pos; others mirrored: pos = (-k * ndc.x * aspect, -k * ndc.y)
```
I'll store k per ghost: halo k=1 (at the sun), others as listed: g1 k=-0.30, g2 k=-0.62, g3 k=-1.05, g4 k=-1.45, g5 k=-1.90. And plus one on the sun side: g6 k=+0.35 small: ghost([0.35,0.30,0.20], 0.06, 16, 1, 0.25) k=0.35?? position = -k*ndc: k=0.35 → -0.35*ndc → between center and sun, mirrored... whatever — visually fine.

Streak mesh: PlaneGeometry(1,1), scale.set(4.2, 0.10, 1), shader STREAK_FRAG, tint (0.65, 0.45, 0.25), vis base 0.5.

Vignette mesh: PlaneGeometry(2, 2), scale.x = aspect (set on resize), material with depthTest false, transparent true, NormalBlending. Rendered last (renderOrder 10; ghosts renderOrder default 0 — additive order irrelevant; vignette must be LAST → renderOrder 10 ✓).

Resize:
```js
function onResize(){
  const w = innerWidth, h = innerHeight;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
  renderer.setSize(w, h);
  flareCam.left = -camera.aspect; flareCam.right = camera.aspect;
  flareCam.updateProjectionMatrix();
  vig.material.uniforms.uAspect.value = camera.aspect;
  starMat.uniforms.uPR.value = renderer.getPixelRatio();
}
addEventListener('resize', onResize);
onResize(); // initial
```
Wait — vignette geometry PlaneGeometry(2,2) spans [-1,1]² in local space; scaled x by aspect covers [-aspect, aspect] ✓ matches the ortho frustum ✓.

Animate:
```js
const _dir = new THREE.Vector3(), _toSun = new THREE.Vector3(), _ndc = new THREE.Vector3(), _tmp = new THREE.Vector3();
const lookTarget = new THREE.Vector3();

function animate(ts){
  requestAnimationFrame(animate);
  const t = ts * 0.001;

  // rotations
  planet.rotation.y = t * 0.020;
  clouds.rotation.y = t * 0.028 + 2.0;
  moon.rotation.y   = t * 0.05 + 1.0;
  sky.rotation.y    = t * 0.0035;

  // moon orbit
  const ma = MOON_A0 + MOON_W * t;
  const s = Math.sin(ma), c = Math.cos(ma);
  shared.uMoonPos.value.set(
    MOON_ORBIT * c,
    -MOON_ORBIT * s * Math.sin(MOON_INC),
     MOON_ORBIT * s * Math.cos(MOON_INC)
  );
  moon.position.copy(shared.uMoonPos.value);

  // camera drift
  const az = 1.591 - 0.0628 * t;
  const rr = 40 - 5 * Math.exp(-0.09 * t) + 1.4 * Math.sin(0.11 * t);
  const yy = 2.2 + 4.2 * Math.sin(0.09 * t + 0.7);
  camera.position.set(Math.cos(az) * rr, yy, Math.sin(az) * rr);
  look.set(Math.sin(t * 0.043) * 1.8, Math.sin(t * 0.031) * 1.1, Math.cos(t * 0.037) * 1.8);
  camera.lookAt(look);
  camera.updateMatrixWorld();

  // flare
  updateFlare();

  shared.uTime.value = t;

  fadeEl.style.opacity = String(Math.max(0, 1 - t / 2.4));
  if(t > 2.6 && fadeEl.style.display !== 'none') fadeEl.style.display = 'none';

  renderer.clear();
  renderer.render(scene, camera);
  renderer.render(flareScene, flareCam);
}
requestAnimationFrame(animate);
```

updateFlare:
```js
function updateFlare(){
  camera.getWorldDirection(_dir);
  _toSun.copy(SUN_POS).sub(camera.position);
  const dist = _toSun.length();
  _toSun.divideScalar(dist);
  const front = _dir.dot(_toSun) > 0.0;
  _ndc.copy(SUN_POS).project(camera);
  let occ = 0;
  if(front){
    _tmp.copy(camera.position).negate();
    const tc = _tmp.dot(_toSun);
    if(tc > 0.0 && tc < dist){
      const b = _tmp.multiplyScalar(tc).add(camera.position).length();
      occ = 1 - THREE.MathUtils.smoothstep(b, PLANET_R + 0.7, PLANET_R + 2.4);
    }
  }
  const off = Math.max(Math.abs(_ndc.x), Math.abs(_ndc.y));
  const edge = 1 - THREE.MathUtils.smoothstep(off, 0.75, 1.55);
  const vis = front ? (1 - occ) * edge : 0;
  sunMat.uniforms.uDim.value = 0.18 + 0.92 * (1 - occ);
  const ax = camera.aspect;
  const sx = _ndc.x * ax, sy = _ndc.y;
  halo.mesh.position.set(sx, sy, 0);
  halo.mesh.material.uniforms.uVis.value = vis * 0.30;
  streak.position.set(sx, sy, 0);
  streak.material.uniforms.uVis.value = vis * 0.55;
  for(const g of ghosts){
    g.mesh.position.set(-g.k * sx, -g.k * sy, 0);
    g.mesh.material.uniforms.uVis.value = vis * g.base;
  }
}
```
Careful with _tmp reuse — fine.

Halo k: position = sun position exactly ✓ (halo is separate from ghosts list? I put halo in ghosts with k=0?? With k=0 position (0,0) — wrong. Handle halo separately as above ✓.)

Ghost sizes: the ghost mesh scale: set at creation: mesh.scale.set(size, size, 1) ✓.

Vignette: create with PlaneGeometry(2,2) scaled by aspect on resize ✓ — actually simpler: PlaneGeometry(2,2) and material uniform uAspect; scale.x = aspect ✓.

Also flareCam near 0.1 far 10, camera z=5, objects z=0 ✓; vignette at z=0 ✓ renderOrder 10 ✓ all meshes frustumCulled = false (scale/pos set dynamically) ✓.

Also — halo size 2.1 with ortho height 2: halo radius ~1.05 units → 52% of screen height — with exp(-r²*2.4): at r=1 → 0.09 → visible large glow ✓ subtle intensity 0.30*vis*0.55... the disc term exp(-r2*uFall): at center = 1 * uVis(0.3*0.30=0.09) * tint — dim ✓ good.

Ghost mesh scales: sizes 0.10-0.24 ✓.

One thing — the streak quad scale (4.2, 0.10): at aspect 1.78 the ortho width is 3.56; a 4.2-wide quad spans beyond ✓.

Star creation code and nebula:

```js
const sky = new THREE.Group();
scene.add(sky);

const nebMat = new THREE.ShaderMaterial({
  uniforms: { uBandN: { value: new THREE.Vector3(0.42, 1.0, 0.22).normalize() } },
  vertexShader: NEB_VERT, fragmentShader: NEB_FRAG,
  side: THREE.BackSide, depthWrite: false
});
const nebula = new THREE.Mesh(new THREE.SphereGeometry(2600, 48, 32), nebMat);
nebula.frustumCulled = false?? — the sphere surrounds the camera; culling fine (bounding sphere always intersects frustum) ✓.
sky.add(nebula);
```
Wait — nebula inside the sky group which rotates — fine.

Hmm — nebula depthWrite false and it's drawn among opaque objects sorted by depth — the nebula is the farthest opaque → drawn... opaque sorting is front-to-back → the nebula drawn LAST among opaques — but with depthTest it only fills background pixels ✓ fine. Actually with depthWrite false and drawn last, it won't overwrite the planet ✓ good. But transparent objects (rings etc.) draw after opaques ✓ fine.

Stars:
```js
const STAR_N = 6500;
... arrays ...
const starGeo = new THREE.BufferGeometry();
starGeo.setAttribute('position', new THREE.BufferAttribute(sPos, 3));
starGeo.setAttribute('aCol', new THREE.BufferAttribute(sCol, 3));
starGeo.setAttribute('aSize', new THREE.BufferAttribute(sSize, 1));
starGeo.setAttribute('aTw', new THREE.BufferAttribute(sTw, 1));
starGeo.setAttribute('aPh', new THREE.BufferAttribute(sPh, 1));
const starMat = new THREE.ShaderMaterial({
  uniforms: { uTime: shared.uTime, uPR: { value: 2 } },
  vertexShader: STAR_VERT, fragmentShader: STAR_FRAG,
  transparent: true, depthWrite: false, blending: THREE.AdditiveBlending
});
const stars = new THREE.Points(starGeo, starMat);
sky.add(stars);
```
Star radii 1500-2250 < nebula 2600 ✓ (with depthWrite false on the nebula, order matters: stars additive drawn after the nebula? Both transparent?? nebula is opaque (transparent not set → false) ✓ drawn in the opaque pass; stars transparent → drawn after ✓ nebula behind shows ✓ stars additive over nebula ✓.)

Wait — the nebula material with `depthWrite: false` and default depthTest true ✓.

Star colors scaled: sCol values up to 1.0*b — with additive & tone mapping ✓.

Star size: aSize in CSS px * uPR ✓ — gl_PointSize in device px: aSize * PR where PR = pixelRatio ✓.

Set starMat.uniforms.uPR.value = renderer.getPixelRatio() in onResize ✓.

Moon orbit line:
```js
const orbitPts = [];
for(let i = 0; i <= 180; i++){
  const a = i / 180 * Math.PI * 2;
  orbitPts.push(new THREE.Vector3(
    MOON_ORBIT * Math.cos(a),
    -MOON_ORBIT * Math.sin(a) * Math.sin(MOON_INC),
     MOON_ORBIT * Math.sin(a) * Math.cos(MOON_INC)
  ));
}
const orbitLine = new THREE.Line(new THREE.BufferGeometry().setFromPoints(orbitPts),
  new THREE.LineBasicMaterial({ color: 0x35555a, transparent: true, opacity: 0.28 }));
scene.add(orbitLine);
```
LineBasicMaterial is not tone-mapped... LineBasicMaterial IS tone mapped (built-in materials include tonemapping) ✓ fine — color 0x35555a is dark; opacity 0.28 — subtle ✓.

Now — potential issue: the moon orbit line drawn OVER the planet? It's opaque-ish (transparent true → transparent pass) — the line passes behind the planet → depth test culls ✓ (LineBasicMaterial depthTest default true ✓, but transparent with depthWrite... line depth vs planet depth: the line fragments behind the planet are farther → culled ✓ good).

Also the line renders after transparent objects... fine.

One more check — the SUN billboard vs the RINGS transparency order: the sun renderOrder default 0, rings 3 → the rings draw after the sun; ring fragments in front of the sun blend over ✓; ring fragments behind the sun get depth-culled?? The sun has depthWrite FALSE → no depth to cull the rings behind it → rings behind the sun's billboard blend OVER the sun ✗ (wrong order but visually: rings are at ~30-60 range, the sun at 850 — rings are always in front of the sun! Any ray that hits both the rings and the sun billboard: the ring is closer ALWAYS (the sun is 850 away). So rings-over-sun is CORRECT ✓✓. And the sun vs clouds: the sun is always behind → the sun (renderOrder 0) draws before the clouds (1) ✓ correct. The sun vs the atmosphere shell: shell renderOrder 2 → after the sun ✓ atmosphere glow over the sun ✓ plausible.

But wait — the sun drawn at renderOrder 0 among transparent: also the stars (renderOrder default 0) — additive stars behind the sun: order by depth: stars (1500+) farther than the sun (850) → stars drawn first ✓ good.

Hmm — one more: the moon (opaque) drawn before ALL transparents ✓; the atmosphere glow (additive shell backside) around the limb will draw OVER the moon when the moon is behind the planet near the limb — the moon at radius 30 behind the planet at distance ~70: the shell's far hemisphere is at ~40+12 = ... from the camera, the far shell behind the planet is at ~50; the moon at ~69 → the shell is closer → its glow draws over the moon ✓ plausible (the moon seen through the atmosphere edge glow ✓).

Now — the eclipse shadow penumbra on the planet: moonShadow smoothstep(uMoonR*0.5, uMoonR*1.75, d) = smoothstep(0.75, 2.6, d) — the shadow spot diameter ~3-5 units — good.

Also — hmm, ONE MORE PHYSICAL CHECK on the moon shadow: during the transit the shadow lands on the planet's day side near the sub-moon point — but my directional-light shadow test uses the ray toward the sun from each fragment: correct ✓.

And the moonlight term `ml*(1-day)`: during the silhouette crossing, the planet regions under the moon... fine.

Also — the moon's own appearance during the crossing: backlit crescent ✓ + planetShadow ~1 ✓.

What about the moon being lit by the PLANET (planetshine)? skip.

Now, let me reconsider the atmosphere SHELL BackSide + additive: when the camera looks at the planet, the shell fragments covering the whole disc have glow = pow(1-x,2.3) where x = (b-10)/2.2 — for b<10 (rays hitting the planet), the shell fragment is behind the planet → culled ✓. For b ∈ [10, 12.2] → the annulus ✓. glow at b=10 → 1; at 11 → pow(0.545, 2.3) = 0.26; at 12.2 → 0 ✓ nice falloff.

But — wait: the shell's far-side intersection for rays with b between... every ray with b < 12.2 hits the shell (front hemisphere culled, far hemisphere drawn ✓). For b > 12.2 no intersection ✓.

Also the shell's far hemisphere is BEHIND the planet for b<10 → culled by depth ✓ (planet opaque, drawn first ✓).

Good. One more — the shell with AdditiveBlending + ACES: fine.

Now — possible z-fighting between the cloud sphere and the planet at the limb: they're separate radii 10 vs 10.35 ✓ fine.

Depth precision at the limb (the moon at 69 vs the planet at 39 vs the shell at 50): near 0.5, far 7000 → depth precision at range ~50-70: with a 24-bit buffer, precision ≈ z² * (1/near) / 2^24 ≈ 70*(2)*(1/0.5)/16.7M ≈ 1.7e-5 ✓ plenty.

Now — FINAL check of the noise function correctness — one subtle thing in Ashima snoise: the line `vec4 j = p - 49.0 * floor(p * ns.z * ns.z);` ✓. And `vec4 x_ = floor(j * ns.z); vec4 y_ = floor(j - 7.0 * x_);` ✓. `vec4 x = x_ *ns.x + ns.yyyy; vec4 y = y_ * ns.x + ns.yyyy; vec4 h = 1.0 - abs(x) - abs(y);` ✓. b0/b1/s0/s1/sh ✓ a0 = b0.xzyw + s0.xzyw*sh.xxyy ✓ a1 = b1.xzyw + s1.xzyw*sh.zzww ✓ p0..p3 ✓ norm ✓ m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0) ✓ return 42.0 * dot(m*m*m*m? original: `m = m * m; return 42.0 * dot( m*m, vec4( dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3) ) );` — wait original: `vec4 m = max(0.6 - vec4(...), 0.0); m = m * m; return 42.0 * dot( m*m, ... )` → m^4 total ✓ I wrote m = m*m then m*m in the dot ✓ same.

Note the original uses 0.6 (not 0.5) ✓.

OK. One more risk: GLSL loop `for(int i = 0; i < 5; i++)` ✓ fine.

Also `if(a < 0.004) discard;` in rings ✓.

`cameraPosition` built-in — available in ShaderMaterial fragment shaders ✓ (three injects it as a uniform in both vertex and fragment ✓ — actually cameraPosition is declared in the vertex shader by default AND in fragment? THREE injects `uniform vec3 cameraPosition;` into BOTH vertex and fragment shader programs for ShaderMaterial? The common prologue for fragment shaders includes cameraPosition ✓ yes (WebGLProgram adds it to both). ✓.

`modelMatrix`, `viewMatrix`, `projectionMatrix`, `normalMatrix`, `modelViewMatrix` — all auto-declared ✓.

Now — the CLOUD mesh rotation: I set clouds.rotation.y separately — but the cloud noise uses vObjPos (rotates with the mesh ✓).

Planet axial tilt is the group's z-rotation ✓ so sp.y (local) = latitude ✓ consistent with rings ✓.

Also — the ATMOSPHERE mesh with BackSide + the custom vertex using `normal` — not needed but harmless (VERT uses normal ✓ attribute exists ✓).

Now — write the flare ghost creation code concretely:

```js
const flareScene = new THREE.Scene();
const flareCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 10);
flareCam.position.z = 5;

const flareQuad = new THREE.PlaneGeometry(2, 2); // local [-1,1] — then scale by half-size
```
Hmm — with PlaneGeometry(2,2), uv ∈ [0,1] ✓ and local positions ±1 → scale by (size/2)... Let me use PlaneGeometry(1,1) (positions ±0.5, uv 0..1) and scale.set(size, size, 1) → half-extent size/2. Then in the shader p = vUv*2-1 spans the quad ✓ r=1 at the edge ✓ consistent with my falloff math where size = full width ✓. So ghost scale = size (full width in ortho units) ✓.

```js
function makeFlareSprite(frag, tint, size, baseVis, ringAmt = 0, fall = 12){
  const mat = new THREE.ShaderMaterial({
    uniforms: {
      uTint: { value: new THREE.Color(tint[0], tint[1], tint[2]) },
      uVis:  { value: 0 },
      uFall: { value: fall },
      uRing: { value: ringAmt }
    },
    vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    fragmentShader: frag,
    transparent: true, depthTest: false, depthWrite: false, blending: THREE.AdditiveBlending
  });
  const mesh = new THREE.Mesh(flareQuad, mat);
  mesh.scale.set(size, size, 1);
  mesh.frustumCulled = false;
  flareScene.add(mesh);
  return mesh;
}
```
For the streak, scale.set(4.4, 0.09, 1) — override after.

uTint as Color → vec3 uniform ✓ (THREE.Color uploads as vec3 ✓).

Ghost list:
```js
const halo   = makeFlareSprite(GHOST_FRAG, [0.55, 0.40, 0.28], 2.3, 0, 0, 2.6); halo.userData.vis = 0.30; halo.userData.k = 0;
const streak = makeFlareSprite(STREAK_FRAG, [0.70, 0.48, 0.26], 1); streak.scale.set(4.6, 0.10, 1); streak.userData.vis = 0.55; streak.userData.k = 0;
const ghostDefs = [
  { k: -0.30, size: 0.11, tint: [0.18, 0.45, 0.46], fall: 15.0, ring: 1.0, vis: 0.34 },
  { k: -0.62, size: 0.17, tint: [0.30, 0.21, 0.42], fall: 18.0, vis: 0.24, ring: 1.0 },
  { k: -1.02, size: 0.075, tint: [0.55, 0.44, 0.20], fall: 9.0,  ring: 0.7, vis: 0.36 },
  { k: -1.45, size: 0.26, tint: [0.14, 0.36, 0.40], fall: 22.0, ring: 1.0, vis: 0.20 },
  { k: -1.55, size: 0.13, tint: [0.44, 0.26, 0.30], fall: 13.0, ring: 0.4, vis: 0.20 },
  { k:  0.38, size: 0.06, tint: [0.40, 0.34, 0.22], fall: 16.0, ring: 1.0, vis: 0.26 },
];
const ghosts = ghostDefs.map(d => {
  const m = makeFlareSprite(GHOST_FRAG, d.tint, d.size, d.fall, d.ring);
  m.userData.k = d.k; m.userData.vis = d.vis;
  return m;
});
```
Simplify: store {mesh, k, vis} pairs.

Vignette:
```js
const vigMat = new THREE.ShaderMaterial({
  uniforms: { uAspect: { value: 1 } },
  vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); }`,
  fragmentShader: VIG_FRAG,
  transparent: true, depthTest: false, depthWrite: false
});
const vig = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), vigMat);
vig.renderOrder = 10; vig.frustumCulled = false;
flareScene.add(vig);
```
PlaneGeometry(2,2) spans [-1,1]² ✓ covers the ortho frustum [-a,a]×[-1,1] when... NO — the quad spans [-1,1] in x but the frustum spans [-a, a] → for a > 1 the quad doesn't cover the edges! Fix: scale.x = a in onResize: vig.scale.x = camera.aspect ✓ (then it covers [-a, a] ✓ and uAspect stays 1... then in the shader p.x ∈ [-a, a] and multiplying by uAspect again would double-apply! Fix: DON'T multiply in the shader if the geometry already spans the frustum: p = vUv*2-1 → p.x ∈ [-1,1] regardless of scale — scale doesn't change uv ✓. So in the shader: p = (vUv*2-1) * vec2(uAspect, 1.0) ✓ with the quad covering the full frustum ✓. Set vig.scale.x = aspect ✓ and keep uAspect uniform ✓.

Similarly the halo/ghosts: their scale is their size in ortho units ✓ (a unit quad scaled).

OK. Now — is `flareCam` needing updateMatrixWorld? Ortho camera with updated projection ✓ position set ✓ — projectionMatrix updated on resize ✓; matrixWorld auto-updated by render ✓.

Now, sanity check the ring alpha pattern range: v = 0.55*s1 + 0.28*s2 + 0.45*s3 (s's ∈ [-1,1], typically ±0.5) → v ∈ ~[-0.64, 0.64] → v*0.5+0.5 ∈ [0.18, 0.82]; smoothstep(0.16, 0.68, v') → varies 0→1 across the range ✓ giving patchy bands ✓ multiplied by fine noise (0.66±0.33) ✓ gaps ✓ edges ✓. Cassini gap at x=0.6 ✓. Good — the ring will show ~30-70% coverage with radial banding ✓.

Ring x sampling in ringShadow — matches ✓.

Hmm — also the rings' inner region x<0.055 fades → a clean gap between the planet and the ring inner edge ✓.

Let me also double-check the ring's radial extent vs the moon's crossing: the moon at orbit 30 crosses IN FRONT of the planet — visually between the camera and planet: the near ring edge... the moon at radius 30 passes ABOVE/THROUGH the ring plane only at a=0/π (radius 30 > ring outer 26 ✓ no intersection ✓). Visually the moon crossing the disc will not intersect ring pixels weirdly (it may pass behind/in front of ring ansae in screen space — depth handles ✓).

Now — the eclipse shadow's visibility on the CLOUDS: mSh on clouds ✓.

Also let me double-check the planet fragment's ringShadow cost: ringPattern has 4 snoise — evaluated per planet fragment ✓ plus planet fbm ~16 → ~20-22 snoise/px ✓ ok.

Also the CLOUD shader's fbm count: wa(5) + d1(5) + d2(5) = 15 + ringShadow(4) + moonShadow(0) = 19 ✓.

Everything seems reasonable. Also — devicePixelRatio cap 2 ✓.

Let me also double check the initial camera framing numerically once more at t=0:
az = 1.591, r = 40 - 5 + 0 = 35?? WAIT: r = 40 - 5*e^{-0.09*0} + 1.4*sin(0) = 40 - 5*1 + 0 = 35. Hmm earlier I said 45 — with this formula r(0) = 35 and it RISES to 40 as the exp decays. I wanted to START WIDE and dolly in: r(t) = 40 - 5 e^{-0.09t} starts at 35 → grows to 40 — that's dollying OUT. Flip: r(t) = 35 + 5*(1 - e^{-0.09t})?? or r(t) = 46 - 8 e^{-0.09t} + 1.4 sin(0.11t): r(0) = 38 → 46?? grows. I want start ~46 → settle 38: r(t) = 38 + 8 e^{-0.09t}... that starts 46 → 38 ✓: `const rr = 38 + 8 * Math.exp(-0.09 * t) + 1.4 * Math.sin(0.11 * t);` r(0) = 46, r(10) = 38+3.25+1.3 = 41.3?? e^{-0.9} = 0.406 → 38+3.25 = 41.25 + sin(1.1)*1.4 = +1.24 → 42.5. r(20) = 38+1.2+1.17 = 40.4. r(30) = 38+0.36-0.5?? sin(3.3) = -0.158 → -0.22 → 38.1. Good: 46 → ~40 gentle push-in ✓.

At r=46 the planet's angular radius = atan(10/46) = 12.3° — the planet is ~24° across in a 55° FOV — decent with rings spanning ~60° h — fits ✓.

Also re-verify the moon-cam distance at the crossing t≈12.6 with r≈42: cam-moon ≈ 42-30+... ≈ 10-12 → the moon's angular radius ≈ 7.5-8.6° ✓ good (planet ~13.5° radius).

OK — one more important detail: `camera.lookAt(look)` each frame with look drifting ±1.8 — at distance 40 that's a ~2.5° wander ✓ subtle.

Also — the eclipse shadow's visibility vs the terminator: the shadow lands near the sub-moon point at az 0.47 area — the day side ✓ the camera at az 0.93 sees it ✓.

Now — WRITE THE FINAL FILE. I'll assemble everything, double checking syntax as I go. Also add small code comments (in English, matching the user's language).

Also — a failsafe: wrap the module code so errors show? Skip.

Let me also make sure `THREE.MathUtils.smoothstep(x, min, max)` — YES signature: smoothstep(x, min, max) ✓.

`THREE.Color` as a vec3 uniform: for ShaderMaterial uniforms, `{ value: new THREE.Color(r, g, b) }` — Color has r,g,b ✓ uploaded as vec3 ✓.

Final structure of the script:

1. imports, renderer, scene, camera, constants.
2. GLSL chunks.
3. Materials + meshes (planet, clouds, atmo, rings, moon, sun, orbit line, sky: nebula+stars).
4. Flare overlay scene.
5. Resize.
6. Animate.

One more idea for the "signature moment": the eclipse sequence IS it. Also the bioluminescent night side. Good.

Also double-check the planet's `fres` rim on the NIGHT side: `col += rimCol * fres * (0.16 + 0.90*day)` — night side rim 0.16*rimCol ≈ faint ✓.

Let me also reconsider the atmosphere shell's `day` floor: clamp(sd*0.7+0.42, 0.04, 1) — the night side gets 0.04-0.1 → faint ✓.

Also the shell covering the planet's DISC: for rays with b slightly < 10 the shell is behind the planet — culled ✓; but for b ∈ [10, 12.2] the shell is IN FRONT of the planet's limb region?? For b ∈ (10, 12.2): the ray passes OUTSIDE the planet — hits the far shell at ~2*sqrt(12.2²-b²)... those fragments are beyond the planet's limb ✓ the glow annulus ✓ correct.

But ALSO — rays with b < 10 hit the shell's far side BEHIND the planet → culled ✓ — except the shell is BackSide → only back faces render → the far intersection ✓ culled by the planet's depth ✓.

Hmm — one caveat: the shell is drawn with depthTest true (default) ✓ planet drawn first (opaque) ✓.

Now — also check the atmosphere doesn't render over the rings incorrectly: rings (renderOrder 3) draw AFTER the atmosphere (2) ✓ rings blend over the glow where in front ✓; glow where in front of rings?? The atmosphere annulus vs the rings passing behind the planet's limb: the glow adds over ✓ fine either way.

Let me also make sure the ORDER of `renderer.clear()` handles the autoClear=false ✓.

Also — `renderer.setClearColor(0x000105, 1)` — near-black with a blue hint ✓ (the nebula covers the background anyway).

Potential problem: the flare overlay is rendered with the flareCam whose projection is ortho — but I render `flareScene` with `flareCam` AFTER the main render — the renderer state (viewport etc.) is fine ✓.

Another potential gotcha: `PlaneGeometry(1,1)` uv 0..1 ✓.

Writing the sun vertex: uses `uv` attribute ✓ (PlaneGeometry has uv ✓) and `position` ✓. uniform uSize ✓. The mesh at SUN_POS with modelViewMatrix = viewMatrix * modelMatrix (the mesh has no rotation → modelMatrix = translation ✓ mv = view * translation → the center in view space ✓ then offset in VIEW space by position.xy*uSize — this makes the quad face the camera ✓✓.

The quad's depth = the center's depth ✓ occlusion by the planet works ✓.

Now — double-check `SUN_VERT`:
```glsl
uniform float uSize;
varying vec2 vUv;
void main(){
  vUv = uv;
  vec4 mv = modelViewMatrix * vec4(0.0, 0.0, 0.0, 1.0);
  mv.xy += position.xy * uSize;
  gl_Position = projectionMatrix * mv;
}
```
✓ (position.xy ∈ [-1,1] from PlaneGeometry(2,2) ✓ half-size 150 → quad 300 world units → angular ~20° — the visible glow core is much smaller ✓).

Sun fragment r2 = dot(p,p) with p ∈ [-1,1]² ✓ core exp(-r2*95): at r=0.1 → exp(-0.95) = 0.39*3.2 = 1.24 — the bright core is tiny (r ~0.1 → 0.05 of the quad = 7.5 world units ≈ 0.5° ✓ sun-like) ✓ glow exp(-r2*6.5)*0.55 visible to r~0.5 ✓ halo exp(-r*2.6)*0.16 ✓ streaks ✓.

uDim dims near occlusion ✓.

Now the STARS fragment — additive with alpha=1: gl_FragColor.a = 1 with AdditiveBlending: blend src alpha... AdditiveBlending in three: srcFactor = SrcAlpha, dst = One — wait: THREE.AdditiveBlending uses (SrcAlpha, One)? In three: AdditiveBlending = src * srcAlpha + dst * 1? Actually three's AdditiveBlending: blendSrc = SrcAlphaFactor, blendDst = OneFactor ✓. So the color contribution is multiplied by alpha — my alpha = 1 → color adds fully ✓ fine (the falloff is baked into rgb ✓).

For the GHOST/streak materials alpha=1 additive ✓.

Vignette: NormalBlending with alpha ✓.

One more check — the ghost shader's `uFall` per sprite ✓ passed at creation ✓.

Star band concentration — `d.addScaledVector(bandN, -d.dot(bandN)*(0.75+0.2*r))` pulls the star toward the band plane ✓ then jitter ✓.

I think we're ready. Also add `precision highp float;` — ShaderMaterial prepends precision automatically ✓.

Let me also handle context loss? skip.

Writing the final HTML now — carefully, completely.

Also: the `#fade` div: I fade via JS each frame using t ✓.

Also, about `renderer.autoClear = false` — with the two-pass render, the depth buffer from the main pass remains; the flare scene's materials have depthTest false ✓ no interference ✓.

One more consideration — tone mapping chunks inside the ghost/streak/vignette shaders: I said skip; their colors are art-tuned ✓.

Double-check the STAR_VERT uses uniforms uTime, uPR ✓ attributes aSize/aCol/aTw/aPh ✓.

Star twinkle: vA multiplies color ✓.

Nebula vertex shader — separate (needs only position) ✓.

One more possible visual artifact: the ring's `discard` with alpha edge — fine.

The moon passing behind the RINGS on the far side (radius 30 > 26 — never behind the rings radially, but the line of sight to the moon may cross the ring plane... the rings extend to 26 around the planet; the moon behind the planet at 30: the sightline to the moon passes near the planet — could cross the near-side ring plane region at radius < 26?? The sightline from the camera (at ~39) to the moon (behind at ~69 total distance): it passes through the ring plane... the ring plane is tilted; the sightline could cross ring radii < 26 → the near ring would occlude the moon partially — depth-correct ✓ (rings drawn after, blend over the moon if the ring fragment is closer ✓ correct behavior).

OK — also think about whether the moon might clip THROUGH the ring plane visually when crossing at a=0/π: at a=0 the moon is at (30, 0, 0) — outside the ring (26) ✓ no intersection ✓.

Alright, final answer assembly. I'll write concise but complete code with comments. Also remember to include `overflow hidden`, `touch-action none`? no interaction needed.

Let me also double check `moon.rotation.y = t * 0.05 + 1.0;` — the moon's noise rotates ✓.

One last numeric check on the planet fragment: `pow(ndh, 130.0)` — ndh ∈ [0,1] ✓ pow fine.

And `smoothstep(0.68, 0.79, lat + capN*0.13)` — capN = fbm4 ∈ ~[-0.85, 0.85] → ±0.11 wobble ✓ caps between lat 0.53-0.94 wobbly ✓ nice irregular caps.

Also — the ice alpha: `ice = clamp(polar + snowy*0.9, 0, 1)` — snow-capped mountains everywhere ✓.

Beach: only above sea ✓.

The shader compiles? Watch for: `float ice = clamp(... + smoothstep(sea + 0.30, sea + 0.42, h), 0.0, 1.0);` — I wrote `+ smoothstep(sea + 0.30, sea + 0.42, h)` — the polar term + snowy term ✓.

In the cloud shader: `mat2(ca, -sa, sa, ca)` — GLSL mat2(column-major): mat2(c0x, c0y, c1x, c1y) — the matrix columns: first column (ca, -sa), second (sa, ca) → M = [[ca, sa], [-sa, ca]]?? Applying M*v: result.x = ca*x + sa*z?? Let me verify: mat2(a, b, c, d) → column0 = (a, b), column1 = (c, d). M * (x, z) = (a*x + c*z, b*x + d*z) = (ca*x + sa*z, -sa*x + ca*z) — a rotation by -wa. Direction doesn't matter (wa is noise-driven either way) ✓ fine.

Also in the planet shader I use `vec3 H = normalize(uSunDir + V);` ✓.

Ring vertex shader = VERT ✓ (uses normal attribute — RingGeometry provides normals ✓; mat3(modelMatrix)*normal — the ring's normal rotated → not used, fine).

Let me also handle a subtle thing: the RING mesh inside planetGroup with rotation.x = -π/2: its object-space position.xy = ring coords ✓ vObjPos.xy ✓.

Now — the ring world radius: the group tilt is a rotation (length-preserving) ✓ ring radii unchanged ✓ uRingN matches ✓.

The RING SHADOW on the planet uses uRingN & the plane through the ORIGIN — the ring plane passes through the origin ✓ (the group rotation is about the origin ✓).

Everything checks. Write it.

Also — I want to double check the fbm amplitude for `cont`: fbm returns ~±0.75 max, typical ±0.3. h = 0.78*cont + 0.22*det: typical ±0.28, max ~0.65. sea = 0.06 → land ≈ 42%? P(h > 0.06) with a roughly-zero-mean distribution concentrated near 0 → maybe ~42% land. Slightly land-heavy but with continent-scale variation (cont dominates) → some hemispheres mostly ocean, others continental ✓ good variety. Ice caps add white at the poles ✓.

Hmm — one thing: with cont*0.78 dominating, the terrain will have large smooth continents with detail from det*0.22 — decent. Mountains add mtn*0.32 on land ✓.

Ocean depth: (sea - h)*3.4 — h min ~-0.65 → depth up to 2.4 → clamped 1 → abyss ✓ shelf band near coasts ✓.

The bio shelf band: smoothstep(sea-0.075, sea-0.004, h) — h within 0.075 below sea → a narrow shelf ✓ (0.075/1.3 of the full range → a visible band ✓).

Colors: abyss (0.004, 0.042, 0.07) very dark teal ✓ deep space contrast ✓ shallow bright teal ✓.

Sun tint (1.0, 0.90, 0.77) warm ✓ ×1.45 brightness → albedo 0.3 → 0.44 pre-ACES ✓ good.

Alright — also decide the exposure: 1.12 ✓.

Also the ghost vis values sum modest ✓.

Now also handle: `const fadeEl = document.getElementById('fade');`

Also the loop must start even if the tab is inactive (rAF pauses when hidden — fine).

Also handle context: `renderer.domElement` styled by CSS canvas{display:block} ✓.

One more consideration: on high-DPI + big screens the planet shader is heavy — offer `renderer.setPixelRatio(min(dpr, 1.75))`? Keep 2, fine.

Also — mobile aspect: FOV 55 vertical; on portrait screens the planet might crop horizontally — hFov shrinks. Acceptable.

Write the final file now. I'll aim for clean formatting.

Additionally — the `uPR` uniform initial value: set = renderer.getPixelRatio() at creation ✓.

Also — I realize the ATMO material's uniform list must include uPlanetR & uShellR & uSunDir ✓ (uTime not needed but harmless to include? I'll include only what's declared in the shader — extra uniforms in the map are OK even if unused ✓ three handles missing locations gracefully ✓).

Also the MOON/PLANET materials need uPlanetR ✓ in shared.

Let me also make the clouds slightly transparent so the terrain hints through at the edges: alpha = cover*0.93 ✓ and cover smoothstep gives soft edges ✓.

Also add a very subtle rotation to the whole planetGroup? No — the tilt stays fixed ✓ (the moon's orbit is defined in world space independently ✓).

Hmm — wait, one consistency check: the ring shadow uses the WORLD-space ring plane ✓ and the rings mesh is tilted via the group ✓ consistent ✓. The planet's noise latitude uses OBJECT space (tilted with the group) ✓ poles align with the ring plane ✓✓.

Final: also confirm the moon's eclipse red tint term: `col += albedo * vec3(0.55, 0.14, 0.05) * ndl * (1.0 - psh) * 0.85;` — during eclipse, ndl (the moon's own diffuse) uses the full sun dot — but in the umbra the direct light is blocked; the red term represents refracted light ✓ and the main term is multiplied by psh ✓ consistent.

Now, the writing. Also remember to define `let nebula` etc. — I'll write cleanly with const.

Also one more check on `NEB_VERT` — needs `varying vec3 vObjPos; void main(){ vObjPos = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }` ✓.

Ghost vertex shared with streak & vig ✓ (a simple passthrough with vUv).

Total code — let me write it.

Also — during writing, keep GLSL strings free of backtick conflicts ✓.

One more: in the animate loop I reference `look` — define `const look = new THREE.Vector3();` ✓.

Also — should the camera EVER be inside the moon's orbit plane crossing... irrelevant.

Also the initial `onResize()` call before the first frame ✓.

Let me now also double-check `updateFlare` runs after camera.updateMatrixWorld ✓ and uses camera.aspect (updated on resize ✓).

Potential undefined: `flareCam.updateProjectionMatrix()` on resize ✓.

Final: write the answer with the complete HTML in one code block, plus a brief explanation after (per my usual practice). Keep the intro short.

One more consideration about `#include <tonemapping_fragment>` inside my fragment shaders — the chunk uses `gl_FragColor` — but in three r186, ShaderMaterial compiles as GLSL1 by default (WebGL2 with GLSL1 shaders via compatibility) ✓ gl_FragColor valid ✓.

Also — one thing to verify: `renderer.outputColorSpace` defaults to SRGBColorSpace in r152+ ✓ colorspace_fragment handles conversion ✓.

Let me also think about whether the CLOUD terminator tint double-adds with the planet's — fine.

Also the ring shader multiplies col by planetShadow ✓ and dims the unlit face ✓.

Done deliberating — write the code.

Actually, one more small thing: the planet spin 0.02 rad/s — in 30s the terrain rotates 0.6 rad (34°) ✓ visible drift ✓. The cloud layer 0.028 → 50° + noise evolution ✓.

And `sky.rotation.y = t*0.0035` — 0.1 rad over 30s — subtle ✓.

Also — I should double check the ghost chain direction: with the sun at ndc (sx, sy), classic ghosts are along the line through the screen CENTER: positions = -k*(sx, sy) ✓ my formula: `g.mesh.position.set(-g.k * sx, -g.k * sy, 0)` ✓ with k negative → +k*sx → between the sun and beyond — mixed ✓ fine.

Also — for ultra-wide aspect, sx = ndc.x*aspect can be large ✓ fine.

One more risk: `.project(camera)` when the sun is BEHIND the camera → ndc flips sign; the `front` check gates visibility ✓.

Now write it all out. Also, I'll add the `pointer-events: none` to the fade div ✓ and z-index.

Count the star buffer attributes — position (3), aCol (3), aSize (1), aTw (1), aPh (1) ✓.

Also — don't forget `starGeo.setAttribute('position', ...)` named 'position' ✓.

Let me write the final HTML.

Also note — `moon` uses shared uniforms including uRingN etc. — the MOON_FRAG includes UNI + NOISE + FX — FX references ringPattern etc. — fine (unused ringShadow ok).

Actually — the moon's shader could also receive the ring shadow — skip.

One more potential compile issue: in FX, functions reference uniforms declared in UNI — order: UNI first then NOISE then FX ✓ (functions use uniforms declared above ✓).

In the PLANET_FRAG template I wrote `UNI + NOISE + FX + ...` — the concatenated string must not have duplicate declarations of varyings — the main body declares varyings ✓ UNI/NOISE/FX don't ✓.

For CLOUD: same ✓. MOON: same ✓. RING: UNI + NOISE + FX ✓ (ringPattern needs snoise ✓). ATMO: UNI + main (no noise needed) ✓.

Go.

Also — one more small thing: the atmosphere glow's `x` uses b relative to [10, 12.2]; but the camera's b for fragments... b computed from the RAY, not the fragment — correct per-ray ✓. However for fragments on the shell's far hemisphere, D = normalize(vWorldPos - cameraPosition) ✓.

Edge case: tc could exceed the shell distance — irrelevant, b is the ray's impact parameter ✓ constant per ray ✓.

Also — since the shell is a sphere of radius 12.2 centered at the origin and the group is tilted — the sphere is rotation-invariant ✓ no tilt issue ✓.

Write it!

Also for the recording-window emphasis: the first seconds show the wide planet + moon near the limb; eclipse at ~8-13s; sun/flare ~10-18s; occultation ~26-29s ✓.

Final read of the moon silhouette moment: the moon crossing IN FRONT of the planet will be lit by... my moon shader lights it with the sun: backlit → dark ✓ with the crescent facing the sun ✓ — the crescent's direction: the sun is at azimuth 0.42 while the camera at 0.80 → the sun appears to the LEFT of the planet (sun az < cam az — which side on screen? The camera looks inward (-radial); the sun direction s vs the look direction: the sun is 30° counterclockwise... the crescent rim will show on the appropriate limb ✓ whatever — it'll look right.

One more: the moon might ALSO be lit by my `moonlight`-like terms? No such term on the moon ✓.

Also the moon passes BEHIND the sun-bright region? No ✓.

Now, actually writing out the entire HTML file text.

Let me make sure about `renderer.clear()` — clears color+depth+stencil with the clear color ✓ each frame before the main render ✓.

Also `renderer.autoClear = false` set once ✓.

Also `scene.add(orbitLine)` ✓.

Star generation with the band:

```js
const bandN = new THREE.Vector3(0.42, 1.0, 0.22).normalize();
const _u = new THREE.Vector3();
function randUnit(target){
  const z = Math.random()*2 - 1;
  const a = Math.random()*Math.PI*2;
  const r = Math.sqrt(Math.max(0, 1 - z*z));
  return target.set(r*Math.cos(a), r*Math.sin(a), z);
}
for(let i = 0; i < STAR_N; i++){
  randUnit(_u);
  if(i < STAR_N * 0.55){
    const dn = _u.dot(bandN);
    _u.addScaledVector(bandN, -dn * (0.78 + 0.18*Math.random()));
    _u.normalize();
    randUnit(_tmp).multiplyScalar(0.09);
    _u.add(_tmp).normalize();
  }
  const rad = 1500 + 750*Math.random();
  sPos[i*3] = _u.x*rad; ...
```
Need _tmp vector ✓.

Colors & sizes as planned ✓.

Also — nebula bandN shared value: create once, pass the same Vector3 into both materials? The nebula uniform uBandN and the star band use the same vector ✓ define `const BAND_N = ...`.

Now — write!

Also the final explanation text after the code block: brief, covering the shader terrain, clouds, atmosphere, rings+shadows, moon choreography, sun+flare, stars, camera, timing. Keep it compact.

Let me write the complete final code in my head once more for syntax errors as I transcribe... I'll be careful with:
- Template literal nesting: the GLSL strings contain no backticks ✓.
- `${UNI}` interpolation inside template strings ✓.

Also — `STAR_VERT` needs `uniform float uPR;` declared ✓.

Writing the code block now.

Also — one more thought about the ATMO material: `blending: THREE.AdditiveBlending, transparent: true` — with additive, the alpha channel: gl_FragColor.a = 1.0; additive blending: src*srcAlpha + dst → srcAlpha=1 ✓.

And depthWrite false ✓.

Also the CLOUD material: NormalBlending with alpha ✓.

Final check on ring renderOrder vs sun: the sun is `transparent: true` with renderOrder 0; rings renderOrder 3 — since 3 > 0 the rings draw after ✓ as analyzed.

Also the atmosphere renderOrder 2, clouds 1 ✓; the moon orbit line: LineBasicMaterial transparent — renderOrder default 0 → drawn with the sun group... the line vs the planet: depth ✓; the line vs clouds (renderOrder 1): the line drawn first, then clouds blend over the line where overlapping?? The line passes outside r=30 — never overlaps the cloud disc ✓ except visually behind the planet ✓ fine.

The stars renderOrder: default 0 — stars vs the sun (both 0): sorted by depth — the stars are farther → drawn first ✓. Stars vs nebula: the nebula is OPAQUE (transparent false) → drawn in the opaque pass before all transparents ✓.

OK writing now — final.

One more: I use `shared.uTime` in starMat and the cloud material — and update `shared.uTime.value = t` each frame ✓.

Also set `shared.uMoonPos.value` each frame ✓ and the moon mesh position ✓.

Camera initial: set before the first render via animate ✓.

Also — `document.getElementById('fade')` after the DOM exists — the script is at the end of body ✓ (module scripts are deferred by default anyway ✓).

Let me also double check the eclipse penumbra constants: moonShadow smoothstep(uMoonR*0.5=0.75, uMoonR*1.75=2.625, d): full shadow when the ray passes within 0.75 of the moon's center; full light beyond 2.625 — the umbra on the planet ≈ diameter 1.5-5 — good.

planetShadow smoothstep(8.6, 13, d) ✓.

Ring shadow strength 0.55 ✓.

Final code:

Actually — one more improvement for the opening frame: at t=0 the moon is at 18° off-axis... it also might overlap the ring ansa — fine.

Also — at t=0 the camera y = 2.2+4.2*sin(0.7) = 4.93; the look target y = sin(0)*1.1 = 0 — fine.

Also let me reconsider FOV 55 vs the sun's placement math — fine.

Also — `camera.rotateZ(Math.sin(t*0.05)*0.018)` after lookAt for a subtle roll ✓ include.

Hmm — rotateZ after lookAt each frame with a time-varying angle — smooth ✓.

Now truly write the output.

For the record, the sizes: PlaneGeometry(1,1) for ghosts with uv 0..1 and positions ±0.5 ✓ scale = size ✓ (full width = size ✓ r=1 at edges ✓).

Vignette: PlaneGeometry(2,2) scale.x = aspect → spans ±aspect ✓ p = vUv*2-1 ∈ [-1,1] → p.x*aspect ✓ wait — the quad's local x ∈ [-1,1] scaled by aspect → world x ∈ [-aspect, aspect] ✓ and p (from uv) ∈ [-1,1] → p.x *= uAspect matches the world x/a ✓ consistent.

Also — the STREAK: PlaneGeometry(1,1) scale (4.6, 0.10) ✓ p = vUv*2-1 over the quad ✓ exp(-p.y²*34): core |p.y|<0.24 → world 0.024 units → 1.2% of height ✓ good.

Also the HALO size 2.3 → radius 1.15 ortho units = 57% of the half-height ✓ big soft glow ✓.

Also — the halo at the sun's exact position will overlap the sun's world billboard ✓ fine.

Ghost k list final: [-0.30, -0.62, -1.02, -1.45, -1.55?, 0.38] — drop -1.55, keep 5 ghosts + halo + streak ✓.

Done deliberating. Compose the final file.

Let me write out the complete code text now, and I'll re-verify bracket/paren balance as I go mentally.

Additional careful piece — the `shared` uniform spread into each material: I'll write them explicitly per material to be safe:

```js
const planetUniforms = {
  uTime: shared.uTime, uSunDir: shared.uSunDir, uMoonPos: shared.uMoonPos, uMoonR: shared.uMoonR,
  uPlanetR: shared.uPlanetR, uRingIn: shared.uRingIn, uRingOut: shared.uRingOut, uRingN: shared.uRingN
};
```
and reuse `planetUniforms` object reference for planet & clouds & rings & moon (sharing the same uniforms map object across materials is fine? Materials each hold `this.uniforms = parameter.uniforms` — sharing the same object instance across ShaderMaterials: three clones? No — ShaderMaterial uses the given object by reference (no clone) ✓ sharing works ✓ (a known pattern). I'll share one `sceneUniforms` object across the four materials ✓.

```js
const sceneUniforms = {
  uTime:     { value: 0 },
  uSunDir:   { value: SUN_DIR },
  uMoonPos:  { value: new THREE.Vector3() },
  uMoonR:    { value: MOON_R },
  uPlanetR:  { value: PLANET_R },
  uRingIn:   { value: RING_IN },
  uRingOut:  { value: RING_OUT },
  uRingN:    { value: ringN }
};
```
Then `uniforms: sceneUniforms` for planet/clouds/rings/moon ✓ and update `sceneUniforms.uTime.value = t` ✓.

atmo: `uniforms: { uSunDir: sceneUniforms.uSunDir, uPlanetR: sceneUniforms.uPlanetR, uShellR: { value: SHELL_R } }` ✓.

OK — final write.

Ah wait — one more check on the CLOUD sphere and the fresnel/atmosphere interplay at the limb: the clouds' alpha at the very limb covers the planet edge; the atmosphere annulus (b ∈ [10, 12.2]) extends BEYOND the cloud limb (10.35) ✓ glow outside ✓ the cloud limb (10.35) sits inside the glow annulus ✓ smooth ✓.

And — the planet's specular glint may show through gaps in the clouds ✓ natural.

Now the code — FINAL.

(Also: double check `RingGeometry` argument order: (innerRadius, outerRadius, thetaSegments, phiSegments) ✓.)

Also — `new THREE.SphereGeometry(2600, 48, 32)` for the nebula ✓.

Let me also reconsider the star radius vs the nebula sphere: stars ≤ 2250 < 2600 ✓; the sun at 850 ✓; far plane 7000 ✓ nebula visible ✓.

Camera far 7000 > 2600+ ✓.

Also, the FLARE overlay colors won't be tone mapped — additive over the tone-mapped frame ✓ punchy ✓.

Write the file.

One more detail — the `#fade` div starts opaque black covering everything; the first frame renders beneath; opacity animates down over 2.2s ✓ cinematic fade-in ✓.

And — `fadeEl.style.opacity` string ✓.

Final concern — performance of `discard` in rings ✓ fine.

Compose the answer.