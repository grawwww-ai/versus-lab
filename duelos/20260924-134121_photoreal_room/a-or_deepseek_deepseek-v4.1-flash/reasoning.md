The user wants a single HTML file with a WebGL2 path tracer. This is a big ask. Let me write a compact but functional GPU path tracer with progressive accumulation that never stops (temporal accumulation with reset on camera/sun move... but requirement says "the view must never freeze into a still image while it cleans up"). Hmm — progressive accumulation with a moving camera means we need to reset accumulation each frame, which means each frame is a fresh 1-sample-per-pixel render — noisy but moving. That's fine: "progressive accumulation is welcome, but the view must never freeze into a still image while it cleans up."

A good compromise: do a small number of samples per frame (e.g., 2-4 bounces samples per pixel per frame), moving camera, so it's noisy but real-time and moving. Show "samples accumulated" as accumulating counter that grows forever (total samples). Actually with a moving camera, we can't accumulate across frames... unless we do temporal accumulation with reprojection, which is complex.

Alternative: accumulate while camera moves? Not possible without reprojection. Let's just render 1-2 spp per frame with the camera always moving, and display total frame count / samples per pixel this frame. Actually we could do a hybrid: render at low resolution and upscale, with several samples per frame.

Let's think about performance: full path tracing with spheres/planes, glass, metal, mirror, area light (window). At 1280x720 with 1 spp, a GPU can do maybe... a simple path tracer with 4 bounces at 720p 1spp is feasible on decent GPU (~ 1M pixels * 4 bounces * maybe 20 ops). Should be OK at maybe 20-60fps on good hardware. But we should keep resolution modest and use devicePixelRatio = 1, maybe render at 0.6 scale and upscale with CSS.

Let me design the scene analytically with ray marching? Actually easier: analytic ray tracing of spheres + boxes (slabs) + planes. That's exact and fast.

Let me define scene:
- Room: box interior, axis-aligned. Room from (-4,0,-4) to (4,3,4) maybe. Walls with different colors: back wall, side walls, ceiling, floor (wood color).
- Actually easier: represent room as an inverted box: ray from inside hits the box's inner faces. Use standard box intersection with normals pointing inward.
- Window: a hole in one wall. Need to handle the opening — that requires CSG. Alternative approach: the light comes from a "window" area light on a wall — a rectangular area light source emitting sunlight color. Combined with a directional-ish light going through the window... For realistic look, simplest: place a rectangular emissive plane at the window position (on the wall), oriented inward, with strong emission. That gives soft shadows, color bleeding, and light pool on the floor that moves as the sun moves (rotate the emissive plane or just move it?). Hmm, but a window in a wall is a hole to the sky — light direction should come from outside.

Better: model the window as a hole by making the wall with the window out of 4 boxes (frame pieces) — i.e., build the wall as slabs around the window opening. Then place an emissive quad slightly outside the window plane, oriented facing into the room (double-sided emission toward the room). Then rays from the room that hit the opening can see the emissive quad outside → sunlight direction. And we can move the sun by rotating the emissive quad's position/tilt? Physically the sun moving means the light direction changes. With an emissive quad outside the window, the direction of light entering is roughly from the quad to the room, which changes with the quad's position. If we move the emissive quad along an arc outside the window, the incoming direction changes → light pool on floor moves. That works!

Also sky background: rays escaping through the window hit the emissive quad or sky. Let's make the exterior a sky (gradient) too, but the emissive quad gives the strong directional light. Actually if rays escape into open sky, we'd get a bright environment. Let's keep the sun quad as the main light and sky as dim blue.

Hmm, but a hole in the wall via separate slabs: I'll build the wall-with-window as a set of boxes. Box intersection with a list of boxes is fine.

Let me simplify: walls as thin boxes (slabs) forming the room shell, with the window made by splitting the +Z wall into 4 pieces (below, above, left, right of window). Then outside is "sky" — infinite environment. But then we need to prevent light leaking? It's realistic — light comes through the window.

Sky: gradient function based on ray direction. Sun: an emissive disk/sphere far away in the sky direction. That's more physical: rays that escape through the window hit the sky/sun. But the sun disk is small and hard to hit via random sampling from the room → very noisy. Better: explicit light sampling of the window + sun.

Design: Use "next event estimation" toward a rectangular sun quad placed just outside the window. Actually simplest with good results: treat the window opening as an area light. Sample a point on the window rectangle (which is in the wall plane, facing inward), with cosine-weighted... no, uniform area sampling with solid angle conversion. That gives soft shadows, and the light direction follows the sun position if we... hmm, the light pool on the floor depends on the direction of incoming light, and if we sample points on the window plane with the light being the window itself (a diffuse emitter), the light pool would be fixed under the window. To get a moving sun pool, the emitter should be directional.

Alternative: make the emitter the sun quad placed outside, tilted/moved along an arc. Rays: from shading point, sample a point on the sun quad, check visibility (shadow ray must pass through the window opening — handled by hitting the wall boxes → occluded). That naturally gives the light pool shape (a projection of the window opening along sun direction) and its movement as the sun quad moves. 

So: sun quad: a rectangle of size ~4x4 placed at distance ~6 outside the window, positioned on a hemisphere arc, facing the window (normal pointing toward the room center). Emission: bright warm color, e.g., (8,7,6)*intensity. Rays that miss the sun quad hit sky (dim blue). Need the exterior to be sky-colored; rays escaping the room through the window hit sky or sun.

But wait: if the sun quad is a diffuse emitter facing the window, then visible through the window it looks like a bright rectangle — fine, it's the sun/sky.

For NEE: sample the sun quad uniformly (area sampling) → directions vary over the quad's solid angle → the light entering is somewhat soft. Making the quad far away (distance 8, size 3) gives a small angular size → fairly sharp shadows with soft edges. Good.

But the "window opening" restriction: shadow ray from floor point to sun point must not be blocked by wall boxes. Correct.

Also, the corridor of light: when a camera ray goes through the window and hits the sun quad, it will be very bright — fine.

Now, we also need to handle rays that go through the glass (refraction), mirror, etc.

Let me define the scene in code with a list of primitives:
- Spheres: glass (r=0.09 at table top), lamp (metal? a metal lamp with a shade — maybe a metal sphere + a cylinder? cylinders are more code. Let's use spheres/capsules and boxes).
- Boxes: floor(room), walls, table (top box + 4 legs or just a top box), sofa (a few boxes: base, back, 2 arms), window wall pieces.
- Mirror: a flat quad on the wall = a plane with reflectivity ~0.95. Represent as a thin box with a special material.

Since boxes are axis-aligned, I can write a slab-box intersection function.

Materials: id-based, with albedo, roughness (for glossy), metallic, transmission (glass), emission.

Simplify: material struct in GLSL as a function returning: albedo, specular/roughness, metallic, emission, transmission. Use a simple structure.

Let me write the shader.

Scene setup (right-handed, y up):
Room: x ∈ [-4, 4], y ∈ [0, 3], z ∈ [-4, 4]. Window in the +x wall? Let's put the window in the wall at x = +4 (right wall), spanning z ∈ [-1.2, 1.2], y ∈ [0.9, 2.4].

Hmm, sun moves across the sky → light pool moves across floor. Let's put the window in the wall at x=+4 wall and sun outside at positive x.

Camera path: walks through the room, orbiting/dollying. Camera stays inside the room, moving slowly. Must keep camera inside room bounds to avoid going through walls. Keep camera in region x ∈ [-2.5, 2.5] etc.

Actually with a mirror on the wall, and the camera moving around, we want to see the mirror at some point. Mirror on the -x wall or -z wall. The camera's orbit should reveal it.

Let me plan geometry concretely:

Room interior: x ∈ [-4,4], y ∈ [0,3], z ∈ [-4,4].
Walls as boxes (thickness 0.1) placed outside the interior:
- floor: y ∈ [-0.1, 0], x ∈ [-4.1,4.1], z ∈ [-4.1,4.1] → wood material.
- ceiling: y ∈ [3, 3.1] → white.
- wall at x = -4: box x ∈ [-4.1,-4] → mirror wall (or with mirror panel).
- wall at x = +4: window wall, split into 4 pieces around window opening z∈[-1.2,1.2], y∈[0.9,2.4].
- wall at z = -4: back wall, color e.g. warm beige/terracotta for nice color bleeding.
- wall at z = +4: wall behind camera, greenish? Let's make walls: left(-x) light gray, right(+x) white with window, back(-z) warm orange-ish, front(+z) light blue-ish. Color bleeding from the orange wall onto the floor/sofa.

Wait, the box slab from -4.1 to -4: the interior faces are at x=-4 exactly. Fine.

Furniture:
- Sofa: near the -z wall, facing +z. Base box: x ∈ [-1.6, 0.2], y ∈ [0,0.4], z ∈ [-3.6,-2.6]. Back: x ∈ [-1.6,0.2], y ∈ [0.4,0.9], z ∈ [-3.6,-3.4]. Arms: x ∈ [-1.7,-1.5] and [0.1,0.3], y ∈ [0,0.65], z ∈ [-3.6,-2.6]. Color: deep red/maroon fabric with some roughness. Actually let's make the sofa facing +z i.e. seat toward +z.
- Table: near center-right: top box x ∈ [1.0, 2.2], y ∈ [0.75, 0.85], z ∈ [-0.6, 0.6]. Legs: 4 thin boxes. Wood material.
- Glass on table: sphere at (1.6, 0.93, 0.0) radius 0.08, glass material (transmission 0.95, IOR 1.5). But a sphere glass is a lens — a "glass" cup. Fine, refraction through the glass is demonstrated. Maybe make it a sphere sitting on the table.
- Metal lamp: a metal object on the table — sphere at (1.3, 0.95, 0.4) r=0.1, metallic. Or a lamp on the floor: cylinder-ish. Let's do a lamp: metal stand (thin box) + metal sphere shade. Simpler: a metallic sphere + small emissive sphere? The prompt says "metal lamp". I'll do a metallic reflective sphere-ish lamp on the table: metal sphere r 0.12 at (1.2, 0.97, 0.35). And maybe an emissive small sphere inside? Not needed; sunlight is the light source. Keep the lamp as metal.

Hmm, but it'd be nice if the lamp gave light. No — keep sun as the only light.

- Mirror on the -x wall: thin box x ∈ [-4.02, -3.98], y ∈ [0.8, 2.2], z ∈ [-1.0, 1.0], material mirror (roughness 0.0, metallic 1.0 with albedo near white) or specular 1.0. Use metallic with roughness 0.02.

- Rug? Not needed.

Main light source: sun quad outside the window at x > 4.
Window opening center: (4, 1.65, 0). The sun quad placed at distance d along a direction. Sun direction varies: sun angle θ(t) changing slowly, sun moves in an arc: position = (4 + 8*cos(φ)*cos(a), 1.65 + 8*sin(a)... let's parametrize: the sun sits outside the window, direction from room center outward +x, tilted up by elevation and sideways by azimuth.

Sun position: P = (4, 1.65, 0) + R * dir, where dir = normalize(vec3(cos(el)*cos(az), sin(el), cos(el)*sin(az))) with el ∈ [20°,55°], az ∈ [-50°, 50°], R = 9. The quad is centered at P, facing -dir (toward the window), size 5x5 (big enough to cover).

Wait — the sun should be far enough that its angular size is small. Quad half-size s=2 at distance 9 → angular radius ~12.5°. That's like a big soft area light. Shadows will be quite soft. Maybe use distance 14 and size 4 → half-size 2, angular ~8°. Let's use R=12, half=2.2.

Since the sun is the only contributor besides the sky, and the window is small, let's make emission strength high, like 15.

Sky: when a ray escapes the room (misses all geometry), sample sky color based on direction: gradient blue + sun glow near sun direction. Since the room is enclosed except the window, sky rays only come through the window. Blue sky through the window adds nice ambient. But it's an infinite bright environment; if too bright, it washes out. Keep sky ~ (0.3,0.5,0.9)*0.4.

Hmm, careful: with NEE sampling the sun, and BSDF sampling possibly hitting the sky, we should weight properly. Standard: at each hit, do NEE (sample sun quad, if visible add contribution with MIS or just add directly and set the BSDF-sampled ray to skip... ). To keep it simple and correct-ish: use MIS with power heuristic for sun sampling vs. BSDF sampling hitting the sun. That's the standard approach and avoids double counting / fireflies.

But MIS adds complexity. Alternative: only NEE for the sun quad (never add emission when hitting the sun via BSDF ray — but then, specular reflections of the sun in mirrors/glass would be lost). Hmm, the mirror reflecting the window is a key visual. With only NEE, when a camera ray hits the mirror, we do NEE from the mirror point to the sun and it works (mirror is a specular-ish surface; NEE on a specular BRDF is invalid though — delta functions). Ugh.

Approach: Use MIS everywhere with a simple BSDF. Let me use:
- Diffuse: Lambert with cosine sampling.
- Specular (mirror, glass): delta — NEE is skipped for delta lobes (weight 0), and BSDF path continues; emission hit is added fully.
- Glossy metal: use GGX-ish? Simpler: use a "rough specular" via mixing diffuse and a Phong-like lobe. To keep it simple I'll use: material has `spec` (0..1), `rough`, `metal`. Sampling: with probability spec, sample a reflection direction perturbed by roughness (Phong-ish cosine power), else cosine diffuse. For NEE, treat roughness < 0.05 as delta and skip NEE.

Simplify further: avoid MIS complexity by doing this:
- NEE: sample sun quad only for non-delta surfaces. Multiply by a "light sampling" estimate.
- BSDF ray: for all surfaces, if it hits the sun quad emission directly, skip adding (to avoid double counting) — except if the previous bounce was delta (specular), in which case add it.

That's a common simplification and works well. But MIS is not that hard. Let me just do the "skip if last bounce wasn't specular" approach... Actually the standard simpler approach: MIS with balance heuristic weight for BSDF sampling = 1 (just add full emission on BSDF hit) and for light sampling weight by the pdf ratio. Hmm, that requires knowing the light pdf.

Let me just implement proper MIS with two strategies. It's ~20 lines.

Actually, let me reduce scope: I'll implement:

```
// At each bounce with shading point p, normal n, wo, material m:
// if material is diffuse-ish (not delta):
//    sample light -> direct lighting contribution
// bsdf sample -> new direction, weight *= brdf*cos/pdf
// if the new ray hits the light (sun quad) and the previous material was delta -> add emission*weight
// if the new ray hits the light and the material was not delta -> add emission*weight*misWeight where misWeight = pdf_light(wi) / (pdf_light + pdf_bsdf)
```

For that I need pdf of light sampling in the direction wi (solid angle) and pdf of BSDF sampling in that direction.

Light: uniform area sampling of the quad: pdf_area = 1/A. Convert to solid angle: pdf_light_dir = dist²/(A*|cosθ_light|). Equivalent: when sampling, contribution = brdf*cosθ_surface*Le*A/dist². So pdf_solid = dist²/(A*cosθ_light).

For BSDF-sampled direction, if it hits the light, pdf_bsdf = the pdf of the BSDF sample (Lambert: cosθ/π; specular lobe: something).

I'll implement a simplified mixture: at each non-delta surface, with prob 0.5 sample diffuse, else sample specular-glossy. The pdf must be the mixture pdf. This is getting complex but let's keep it manageable: I'll use a single-sampling approach with explicit pdf tracking.

Alternatively, simpler and physically plausible: Make all materials either:
(a) Lambertian (diffuse) with optional specular reflection handled by "reflect with probability spec" — treat as a mixture BSDF.
(b) Delta: mirror, glass.

And use MIS for the diffuse component only, ignoring the specular lobe for MIS on NEE (i.e., NEE uses only the diffuse BRDF, and the specular lobe sampled by BSDF gets full emission weight with MIS weight computed against the diffuse-aware light pdf... this is approximate).

Honestly, for visual quality, an approximate but stable approach is fine. Let's do:

- For non-delta materials: NEE samples the light using the diffuse BRDF only, weight = albedo/π * cos * Le * A / dist² * visibility. And BSDF sample: when hitting the light, add emission * weight * misWeight where misWeight = pdf_light_dir / (pdf_light_dir + pdf_bsdf_dir) — hmm, but NEE only used diffuse part while BSDF sampling might have picked the spec lobe... 

You know what, let's simplify the material model drastically to avoid MIS entirely:

Every non-delta surface uses: NEE with the full BRDF (diffuse + glossy specular approximated as diffuse-like for light sampling? no...).

Alternative simpler: Skip NEE entirely, rely on BSDF sampling + a "light sampling" only when the BSDF ray misses... no, that's too noisy.

OK here's a cleaner classic approach used in many small path tracers: **NEE for the light on all non-delta surfaces using the surface's BSDF evaluated at the light direction** (that's fine for any BRDF, you just evaluate BRDF(wo, wi) * cos * Le * G). The only requirement is that we don't double count. To avoid double counting, we do MIS: when a BSDF-sampled ray hits the light, multiply emission by weight_bsdf = pdf_light/(pdf_light+pdf_bsdf) — but this requires that NEE's pdf is exactly pdf_light and that the BSDF sampling covers the same event. Since NEE with the full BRDF evaluation gives estimate = brdf*cos*Le/pdf_light, and the BSDF strategy gives brdf*cos*Le/pdf_bsdf, combining with the balance heuristic: weight_light = pdf_light/(pdf_light+pdf_bsdf), weight_bsdf = pdf_bsdf/(pdf_light+pdf_bsdf). Both use the same brdf*cos*Le. So it works with any BRDF as long as we can compute pdf_bsdf of the direction that hits the light.

So I need pdf_bsdf for a given direction. With the mixture sampling I described: pdf = 0.5 * pdf_diffuse + 0.5 * pdf_spec, where pdf_diffuse = cos/π and pdf_spec = some lobe pdf. That's computable.

Fine, let's do it. It's not that bad.

Let me now design the BSDF:

Material:
```
struct Mat { vec3 albedo; float rough; float metal; float spec; float trans; vec3 emis; }
```
- diffuse: albedo
- specular weight `spec` (0..1), roughness `rough`, metallic tint.
- transmission `trans` for glass (delta, IOR 1.5).

Sampling:
- if trans > 0.5 → delta glass: refract/reflect by Fresnel. weight = ... and continue. Mark delta=true so NEE is skipped and the hit emission is added fully (weight 1 MIS).
- else if rough < 0.03 and spec > 0.5 → delta mirror.
- else → mixture diffuse/glossy.

To reduce complexity, maybe: treat mirror as `spec=1, rough=0.0` → delta reflection. Metal lamp: `spec=1, rough=0.15, metal=1` → glossy metal (non-delta, rough sampling). Glass: transmission.

For glossy sampling, use a simple Phong-like lobe around the reflection direction: cosine-power with exponent n = 2/(rough²) - 2 ... Let's use GGX-ish or just cosine-power. Cosine power lobe: pdf = (n+1)/(2π) * cos^n(θ), sampling: cosθ = pow(u, 1/(n+1)). Simple. Specular BRDF = spec_tint * (n+2)/(2π) * cos^n(θ) (normalized Phong). Then brdf*cos/pdf = spec_tint * cos^n... it works out.

Hmm, but the Phong lobe isn't energy conserving with the diffuse. Whatever, it's approximate and looks fine. Scale spec by fresnel maybe.

Let's write:

```glsl
vec3 bsdfEval(vec3 wo, vec3 wi, vec3 n, Mat m, out float pdf)
```
Hmm, let me just do the sampling inline.

Plan for the path loop, per pixel:

```
vec3 radiance = 0; vec3 throughput = 1;
float lastPdf = 1; bool prevDelta = true; // so first hit adds emission normally
for (int bounce=0; bounce<MAXB; bounce++){
   hit = intersect(ro, rd);
   if (!hit) { // sky
      if (prevDelta) radiance += throughput * skyColor(rd);
      else radiance += throughput * skyColor(rd) * misSky; // sky is only sampled by BSDF; NEE doesn't sample sky → no MIS needed → just add
      break;
   }
   // emission
   if (hit.emission > 0) { add with MIS weight unless prevDelta }
   ...
}
```

Simplify: sky is never NEE-sampled, so BSDF hits on sky always get full weight (no double counting). Only the sun quad needs MIS. But the sun quad is a geometric object, so rays hitting it go through the emission branch. And sky is the "no hit" branch which only the BSDF can produce → full weight. Good. But careful: the sun quad occludes sky, so the BSDF pdf for hitting the light is well-defined. OK.

So:
```
if (hit is emissive) {
   radiance += throughput * emis * (prevDelta ? 1.0 : misWeightBsdf);
   break;
}
```
where misWeightBsdf = pdf_light / (pdf_light + pdf_bsdf) · ... wait, need care with the balance heuristic. With two strategies L (light) and B (bsdf), both producing the same path, the estimator is:
- L: f/pdf_L * w_L, w_L = pdf_L/(pdf_L+pdf_B)
- B: f/pdf_B * w_B, w_B = pdf_B/(pdf_L+pdf_B)

Running both and summing gives f/(pdf_L+pdf_B) * 2? No: f*w_L/pdf_L + f*w_B/pdf_B = f/(pdf_L+pdf_B) + f/(pdf_L+pdf_B) = 2f/(pdf_L+pdf_B). Hmm, that's the correct MIS with both strategies counted. Yes, that's right — with the balance heuristic, the combined estimator is sum over strategies of w_i * f/pdf_i where w_i = pdf_i/sum. Each strategy's estimate has expectation f (since E[f/pdf_i] = f), and the MIS weights sum to 1, so the total has expectation f. Yes: adding both gives expected value f. Correct.

So on the BSDF path hitting the light, we add throughput * emis * w_B where w_B = pdf_B/(pdf_L+pdf_B). And on NEE, we add throughput * brdf*cos*Le/pdf_L * w_L.

Wait but the MIS weight applies to the "light sampling pdf" pdf_L which includes the geometry term. Let me define in the direction from the shading point toward the light sample: pdf_L_solid = dist²/(A * |cosθ_L|) where θ_L is the angle at the light between the light normal and the direction to the shading point. Then w_L = pdf_L/(pdf_L + pdf_B) where pdf_B is the BSDF pdf of that same direction. Good.

And for BSDF path: after sampling direction wi from the surface, check if it hits the light. If it hits the light with normal... we need pdf_L for that direction = dist²/(A*|cosθ_L|). And then w_B = pdf_B/(pdf_L+pdf_B).

Implementation: In the intersection function, the sun quad is a box (thin) with an emissive material. When a ray hits an emissive primitive, we compute the light pdf for that direction from the previous shading point (using the hit point). Actually simpler: check "is the hit primitive the sun quad". Then compute the pdf against it.

Let me structure: intersect returns the primitive index and the hit point. If mat.emis is nonzero:
  pdf_L = lightPdf(prevPoint, prevNormal, hitPoint, lightIndex) — computed as (dist²)/(A * cosAtLight).

Actually just define a function `sunPdf(p, d)` where d is the unit direction: it needs the distance to the quad along d, and the cosine at the quad. Since the quad is a rectangle with known center, normal, half-extents, I can intersect the plane: t = dot(center-p, n)/dot(d,n); the hit is inside if the projected coords are within extents. Then pdf = t²/(A*|dot(d,n)|).

Good, that works for a rectangle in general orientation. Let's make the sun quad a general axis-aligned rectangle (I can keep it axis-aligned to simplify? No — it must tilt as the sun moves). Let me define the sun rectangle with a center, a normal n, and two tangent vectors u,v with half-lengths. Then intersection is standard.

Actually, do I even need the sun to be a geometric quad? Alternative: treat the sun as an "infinite directional-ish" light: a disk at a far distance. Geometrically, the light pool on the floor is determined by the window opening and the incoming direction; the sun's angular size only affects shadow softness (penumbra). A far-away small disk gives sharp shadows. So: sample the sun by sampling a small disk perpendicular to the sun direction at a large distance... Equivalent to a rectangle. Just make the quad and its intersection general (oriented rectangle).

Let me make a helper for oriented-rectangle intersection. That's easy:
```
bool rectHit(vec3 ro, vec3 rd, vec3 c, vec3 n, vec3 u, vec3 v, vec2 he, out float t) {
  float dn = dot(rd, n);
  if (abs(dn) < 1e-6) return false;
  t = dot(c - ro, n)/dn;
  if (t < 1e-4) return false;
  vec3 p = ro + rd*t - c;
  float a = dot(p,u), b = dot(p,v);
  if (abs(a) > he.x || abs(b) > he.y) return false;
  return true;
}
```

The sky: if the ray misses everything, return skyColor(rd) = mix of horizon and zenith + a glow around the sun direction. And when we look at the window from inside, we see the sky.

Wait — but the sun quad is a big bright rectangle floating outside; through the window we'd see it as a big bright flat panel. That might look odd. Make it far enough and large: distance 30, half-size 6 → angular half ~11°. Hmm, that gives a huge bright rectangle covering most of the window. Alternatively, use distance 60, half-size 8 → angular ~7.6°. The penumbra: window size ~2.4m, at distance 60 the sun's angular diameter ~15° still big. Hmm, real sun is 0.5°.

To get sharper shadows, make the sun quad small and far: distance 100, half-size 1.5 → angular radius 0.86°. Then the solid angle is tiny → NEE with uniform area sampling would be extremely noisy? No — NEE with uniform area sampling gives a proper estimate: contribution = brdf*cos*Le*A/d². The A/d² is tiny, so Le must be enormous to compensate. That's fine numerically (float handles it, but noise? The variance is zero for uniform area sampling of a constant emitter — for directly visible lights it's exact.) The issue: for rough/glossy surfaces, the BRDF varies over the solid angle, but the sun is tiny so it's effectively a directional light — that's fine and low-variance.

But wait: with a small distant sun, the shadow from the window is very sharp, and soft shadows come only from... nothing. The prompt asks for soft shadows. Soft shadows arise from the area light. So we want a moderately sized sun. Let's compromise: distance 25, half-size 3 → angular radius ~6.8°. That gives pleasant soft shadows and a visible bright panel through the window (never visible really, since through the window the sun's position is at elevation 30-50° so looking out the window horizontally you'd see the sky, not the sun). The sun is up high; the window looks out horizontally at the sky. So we'd see the sky (blue gradient) through the window — nice. And the sun panel is up high, out of view.

That's realistic. The light pool on the floor would be from the sun direction. Let's set the sun elevation between 25° and 55°, azimuth varies from -60° to 60° over time → the light pool moves across the floor.

But if the sun is at elevation 50° outside the +x window, light entering through the window (y from 0.9 to 2.4) hits the floor at x from 4 - 2.4/tan(50°)... The floor patch: for the window top at y=2.4 and elevation 50°, the ray travels down at slope tan(50°)=1.19, so from y=2.4 down to 0 takes horizontal distance 2.4/1.19 = 2.0 → x from 4 to 2.0. For y=0.9: 0.9/1.19 = 0.76 → x from 4 to 3.24. So the light pool is on the floor between x=2.0 and x=4. Good—visible near the window. With azimuth, it shifts in z. Nice.

Check that the table (x ∈ [1,2.2]) gets sun on it sometimes — a nice highlight. And the sofa at x ∈ [-1.6, 0.2] is far from the window, would be in shadow — good, shows soft shadow/penumbra and color bleeding.

Now, is the room too dark? Sun intensity high, walls bounce. Might work out.

Also I should add a bit of ambient/sky light through the window: the sky is a big bright environment seen through the window, contributing ambient. Set the sky to a moderate blue-bright so it lights the room indirectly. Note sky is sampled only by BSDF rays → noise. Since the window is small, the sky contribution is small and diffuse — it'll be a bit noisy but fine at low sample counts. Alternatively, add the sky as a NEE strategy too... no, keep it simple.

Hmm, actually since it's noisy, maybe keep the sky dim and rely on the sun. Yes, keep sky moderate.

Now the "never freezes" requirement: with a moving camera, we can't accumulate. But we can render multiple samples per frame (e.g., 4 spp) at a lower internal resolution and upscale. Let's do: internal resolution = canvas size * scale (scale ~0.5-0.75), spp = 2-4 per frame. Temporal accumulation: we could accumulate frames while the camera moves if we reproject—too complex. Just do fresh accumulation each frame with N samples per pixel. If the camera moved only slightly, we could blend with the previous frame, but that creates ghosting. The requirement says the view must never freeze; fresh samples each frame satisfy it.

But "Include a small label with the number of accumulated samples." — I'll display the samples-per-pixel accumulated in the current frame, plus the frame counter. Maybe: "spp: 2 (frame 1234)". Or better: do temporal accumulation with a "reset when the camera moves" ... which is always. Hmm.

Alternative interpretation: we can accumulate over frames if we keep the camera still, but the camera is always moving. So accumulation resets constantly. Just show "spp/frame" and total frames.

Better idea: I could do a hybrid — do a small number of samples per frame with slight temporal blending (exponential moving average) to reduce noise, weighted so motion doesn't cause too much ghosting. EMA with alpha ~0.3 reduces noise by ~2x. Risky for ghosting but at slow camera motion it's fine and looks nice (like TAA). Let's do: accumulate buffer A (previous blended) and blend new render with weight 0.25. Hmm, this creates trailing. I'll skip it or use a mild blend. Actually a light temporal blend makes it look much better. Let's do a modest blend with alpha 0.35 for the new frame... Actually with 4 spp + EMA(0.3) it's like ~13 spp effective. Good.

Hmm, but at camera motion it causes smearing. The camera moves slowly. I'll include it with a fairly low blend weight (0.35 new). Let's try. Risk: implementing ping-pong FBOs. That's more code but fine.

Actually, let me simplify: no temporal blending, just render N spp per frame directly to the default framebuffer, with N as high as performance allows (e.g., 2-4). Keep it simple and robust. Noise is acceptable — it's a path tracer.

Hmm, but "photorealistic" — noise detracts. Let's do a small temporal accumulation: it's like 30 extra lines. Let me consider: an accumulation buffer (float RGBA texture), a copy/blend shader. Actually I can do the blend in the same shader: render into a texture, then a second pass that blends with the history and outputs to the screen. Or use a single pass writing to the accumulation texture with blending enabled (gl.BLEND with constant alpha) — that's easy! Use framebuffer with a RGBA16F texture, enable blending with constant alpha 0.25: dst = 0.25*src + 0.75*dst. Then draw the accumulation texture to the screen with a tonemap shader.

But with blending, reading the previous frame requires the attachment... With blending, we don't read, we just draw into it and the GPU blends with the existing content. When the view changes drastically (camera moves), the old content is stale → ghosting. With alpha 0.25 the ghost fades in ~10 frames. At 60fps that's 0.16s of ghosting — acceptable? The camera moves slowly, so it's like motion blur. I think it looks good.

But there's a subtlety: the accumulator holds the average of previous frames which were rendered from different camera positions → looks like a smear. With slow motion, this is basically temporal AA/motion blur. It's fine, even attractive.

Hmm, but the requirement "the view must never freeze into a still image while it cleans up" — with EMA it never freezes. Good.

Let me decide: use EMA with alpha depending on... let's use a fixed 0.3. Hmm, actually a danger: bright fireflies accumulate and persist. Let's clamp fireflies: clamp the sample value to something like 20. Fine.

Let me reduce risk: skip temporal accumulation. Simpler, and correctness is more important. Actually... let me do it, it makes the image much better. I'll write a small code for ping-pong accumulation.

Hmm. Let me think about the overall structure and then decide. I'll go with the accumulate-and-blend-in-shader approach:

Pass 1: render path trace to `accumTex` (RGBA16F) via a framebuffer, writing `newColor`. In the shader, output the blend: `outColor = mix(texelFetch(accumTex, ...), newColor, alpha)` — but you can't read and write the same texture in one pass. So use two textures and ping-pong, or use blending. Blending is easiest: `gl.enable(gl.BLEND); gl.blendFunc(gl.CONSTANT_ALPHA, gl.ONE_MINUS_CONSTANT_ALPHA); gl.blendColor(0,0,0,alpha);` and the shader outputs the raw new color. The framebuffer attachment is RGBA16F, and blending works with float attachments (needs EXT_float_blend for 32F, but 16F is fine).

Then pass 2: draw a fullscreen quad sampling accumTex, tonemap + gamma, to the screen.

Alpha constant per frame: use a low alpha (like 0.25) when the scene is static-ish, or 1.0 when the camera jumps. Since the camera moves continuously, use 0.25 always. Hmm, but the sun also moves → the light pool moves → ghosting of the light pool. With alpha 0.25 and slow sun motion, it's fine.

Actually, let's make it adaptive: alpha = 0.35 constant. Good enough.

Now, resolution and performance. Let's render at `min(devicePixelRatio,1) * canvasSize * 0.75`? Let's just use the canvas at CSS size with a scale factor. I'll set the render size to something like 900x560 internally and upscale to the window. Actually let's make the render target = the window size * 0.7, clamped.

Let's write the code.

Javascript structure:
- Get WebGL2 context (with `antialias:false, preserveDrawingBuffer:false`).
- Create shaders, program for pathtrace and for blit.
- Fullscreen triangle/quad.
- Uniforms: uResolution, uTime, uCamPos, uCamMat (or compute the camera in JS and pass origin + 3 basis vectors), uSunCenter, uSunRight, uSunUp, uFrame, uSeed.
- Animation loop with requestAnimationFrame.

Camera path: The camera moves through the room. Let's define a path:
```
t = time (seconds)
angle = t * 0.12  (rad/s) → full orbit in ~52s
radius = 2.6 + 0.5*sin(t*0.09)
camPos = center + (cos(angle)*radius, 0, sin(angle)*radius), y = 1.5 + 0.15*sin(t*0.15)
lookAt = varying target: a point that moves, e.g., (cos(t*0.07)*0.8, 1.0 + 0.2*sin(t*0.11), sin(t*0.07)*0.8)
```
The camera must stay inside the room: |x| < 3.6, |z| < 3.6, y ∈ [0.4, 2.6]. With center at (0,0,~0.5) and radius 2.6 → x ∈ [-2.6,2.6], z ∈ [-2.1,3.1]. OK.

But we want to see: the window (+x wall), the sofa (-z), the mirror (-x wall), the table (center-right). An orbit reveals all walls over time. With a period of ~50s, within 30s we see about 60% of the room — enough if we start at a good angle. Let's make the orbit period ~24s so it does a full loop within 30s. angle = t*0.26 rad/s → 24s per revolution. That might be too fast ("slow, smooth"). Let's do angle = t*0.22 → 28.5s per rev. Plus vertical bobbing. And the look-at target orbits too, offset, so we see different things.

Actually, a nicer approach: combine a slow orbit with a slight dolly. Let's define:
```
float a = t * 0.22;
float r = 2.3 + 0.6 * sin(t * 0.13);
camPos = vec3(cos(a)*r, 1.45 + 0.28*sin(t*0.17), sin(a)*r);
vec3 target = vec3(cos(a + 0.9)*1.2, 0.95 + 0.35*sin(t*0.11), sin(a + 0.9)*1.2);
```
Hmm, the target orbits too — the camera looks tangentially, sweeping across the room. That's a nice "reveal" motion. But if the target is close to the camera, it may look weird. Let's use a target that orbits at a different rate.

Let me think about what looks good: the camera orbits around the room center; the look direction points toward the room center but slightly off (leading the orbit) plus vertical variation. Classic. And to see the mirror and window, having the target near the center is fine — the mirror is on the -x wall, the window on the +x wall. As the camera orbits, it faces inward and the walls pass by behind. Hmm, if the camera looks at the center, the walls are behind it. We want to see the walls, so the camera should look more outward/tangentially.

Better: the camera orbits at a small radius (near center, r=1.8) and looks outward in a direction that rotates. Then as it rotates, it looks at different walls. Yes! Camera near the center, looking outward at whatever wall it's facing, with a slight orbit motion (dolly). Let's do:

```
a = t*0.2;                       // 31s per rev
camPos = (cos(a)*1.5, 1.5+0.15*sin(t*0.23), sin(a)*1.5);
lookDir = (cos(a+0.35), -0.15+0.1*sin(t*0.17) , sin(a+0.35)); // look outward, leading
```
Hmm, looking outward from the center means we see one wall at a time, and the window, mirror, sofa pass by. Over 30s the camera would look at the walls in sequence: if it starts facing the window (+x)... 

Let's tune: at t=0, a=0 → camPos=(1.5,1.5,0) — that's inside the table (table x∈[1,2.2])! Move the table or the camera. Let's set the camera orbit radius to 1.5 with center at (0, ., 0.3) and adjust.

Wait — the table at x∈[1.0,2.2], z∈[-0.6,0.6], y∈[0,0.85]. The camera at y=1.5 is above the table, so it's fine (no collision). Actually the camera is above the table at height 1.5, so it's fine. But it may clip the lamp/glass. Those are at y≈0.93, camera at 1.5 — fine.

But wait, the camera near the center at radius 1.5 in a room of half-size 4, looking outward — the walls are ~2.5-5.5m away. FOV 60° — we'd see the wall plus furniture. Good.

Hmm, but at t=0 the camera at (1.5,1.5,0) looking in direction (cos0.35, -0.15, sin0.35) ≈ (0.94, -0.15, 0.34) → looking toward the +x wall (the window wall). Good, we see the window with light streaming in. 

Then at t≈8s (a=1.6), camPos ≈ (1.5cos1.6, 1.5, 1.5sin1.6) = (-0.04, 1.5, 1.5), looking at direction (cos1.95, -0.15, sin1.95) = (-0.37,-0.15,0.93) → toward the +z wall (the front wall, behind). Hmm, that's the blank wall. Not great.

Let's have the camera look toward the center-ish but offset. Let's use lookDir = direction to a target point:
```
target = vec3(-cos(a)*1.2, 1.2 + 0.3*sin(t*0.13), -sin(a)*1.2)
```
Then the camera at radius 1.5 looking at a point at radius 1.2 on the opposite side → looking across the room, seeing the far wall behind the target. Hmm, that's always seeing the opposite wall — with the same problem but shifted.

Actually, seeing the opposite wall is what we want: from (1.5,0) looking toward (-1.2,0), we see the -x wall (mirror). 

So the camera is on one side looking across the room at the opposite wall. As `a` increases, we look at: +x wall (window) → ... let's see, camera at angle a, target at angle a+π. So the camera is always looking at the point diametrically opposite, meaning we always see the wall directly opposite the camera. As a goes 0→2π, we see all 4 walls in sequence. 

At a=0: camera at (1.5,·,0), looking toward (-1.2,·,0) → sees the -x wall (mirror). And the window is behind. Hmm.

Start at a = -π/2: camera at (0,·,-1.5) looking toward (0,·,+1.2) → sees the +z wall. Not interesting.

Let's think: we want to see the window wall and the sun streaming in at the start. Window is the +x wall. To see the +x wall, the camera must look in the +x direction, i.e., the camera is on the -x side: a = π. So start a = π at t=0: camera at (-1.5, 1.5, 0), looking toward (1.2, 1.2, 0) → the window wall in front, the table and glass and lamp are in the view (table at x 1..2.2, z -0.6..0.6) — great composition! Sofa on the left/behind... The sofa is at z ∈ [-3.6,-2.6], x ∈ [-1.6,0.2] — from the camera at (-1.5,1.5,0) looking toward +x, the sofa is to the right? The sofa is in the -z direction from the camera. Looking along +x with y up, the -z direction is to the... With a right-handed system, if forward=+x and up=+y, then right = forward × up? Let's not worry. Fine.

So: a = π + t*0.2.

Then over 30s, a goes from π to π+6 rad = ~0.28 rad short of 2π. So nearly a full revolution. We'd see: window wall → sofa wall (-z) → mirror wall (-x) → front wall (+z) → back to the window. Within 30 seconds we see everything. 

Now the sun: it should sweep so that the light pool moves across the floor. Sun azimuth from -60° to +60° over ~40s, elevation 30° to 45°. Let's make it continuous and non-jarring.

Sun position: 
```
float sa = sin(t*0.09), ... 
az = 0.9*sin(t*0.07);   // radians, ±51°
el = 0.62 + 0.18*sin(t*0.05); // 35°±10°
dir = (cos(el)*cos(az), sin(el), cos(el)*sin(az))  // pointing from the window outward (+x)
sunCenter = vec3(4.0, 1.65, 0.0) + dir * 25.0
```
Wait, the sun center should be positioned so that the light comes through the window at an angle. If the sun is at distance 25 in the direction dir, and the quad faces the room (normal = -dir).

But hold on — the window is in the +x wall at x=4, and the sun is at x = 4 + 25*cos(el)*cos(az) > 4. Good.

The light entering the room: from a floor point p, the direction to the sun center is roughly dir reversed... the shadow ray from p toward the sun region must pass through the window opening. Since the sun is far (25) and the window is 2.4 wide, the light cone from a floor point through the window is narrow. Good — sharp-ish shadows with soft edges. Sun angular radius: half-size 3.5 at distance 25 → 8°. That gives fairly soft penumbra. OK.

Hmm, but careful: since the sun quad is at distance 25 and half-size 3.5, the sun quad spans a lot. Would rays from the floor through the window hit the quad? The window from a floor point at x=2.5 subtends maybe ±25°. The sun quad subtends ±8°. So NEE samples on the quad that are occluded by the wall are wasted (about 10% hit rate?) — no, NEE doesn't require visibility to the whole quad; we sample a point on the quad, then check the shadow ray. Most samples will be blocked by the wall (since the window is small). This is wasteful (high variance): the probability that a random point on the sun quad is visible through the window from a given floor point is small (window solid angle / sun solid angle ≈ (25° / 8°)² ≈ 10). So 90% of light samples are wasted → 10x variance. Hmm.

Better: make the sun quad smaller (matching the visible cone) and place it near/at the window. Actually, the physically meaningful thing: what matters is the light entering through the window. Instead of a distant sun quad, place an emissive quad just outside the window (say 0.5m out), sized to cover the window opening, with emission such that it looks like the sun. Then the light direction is determined by the quad's orientation and position relative to the window.

Hmm, but a diffuse emitter just outside the window emits into the hemisphere facing the window; light enters the room from many directions, and the light pool would be broad/soft. To get a directional light pool that moves, the emitter should be far away (angularly small).

Compromise: put the sun quad at a moderate distance (say 8) with a modest size (half-size 1.8 → angular radius 12.7°)... still wasteful.

Alternative approach: sample the sun quad but only the portion visible through the window? Complex.

Alternative: importance-sample directions toward the window opening (as an area light) and treat the incoming light as "sunlight" modulated by the sun's visibility: i.e., NEE samples a point on the *window rectangle* (the opening), computes the direction, then evaluates whether the sun is visible in that direction (test if the direction from the window sample toward... no).

Hmm. Think differently: The physical setup is: the room has a window; outside is the sky and the sun. Light entering = sky light + sun. The sun is a distant directional light with a small angular size and it produces a light pool shaped like the window projected onto the floor.

An efficient and simple scheme: **Treat the sun as a directional light with a small angular size represented by a disk/quad placed right at the window's outer plane?** No.

Simplest efficient scheme: sample the light *through the window opening*. I.e., the light sampling strategy: sample a point q uniformly on the window opening rectangle (in the wall plane). Then the direction from p to q. Then, consider that light travels from the sun to q and needs to reach p. If we model the sun as a distant area light with angular radius θ_s, then... the radiance arriving at q from the sun direction is L_sun, but only if the sun is in that direction. Since the sun is far away, all points on the window essentially see the sun in the same direction — the sun subtends a small solid angle; a point q on the window receives sunlight if the direction from q to the sun isn't blocked (nothing blocks it outside). So essentially every point on the window is lit by the sun.

So the whole window acts as an aperture emitting a collimated beam into the room in direction -sunDir. So: the light entering the room is like a collimated beam. So the effective area light for the room is the window rectangle, emitting with a directional (delta) distribution in the sun direction, with radiance L_sun * (solid angle of the sun). Hmm, that's basically: the window emits a collimated beam.

This gives a clean NEE scheme: sample a point q on the window rectangle (uniform), direction d = normalize(q - p), then the "light" is a collimated beam arriving at q from direction -sunDir. For the beam to actually pass through q and reach p, the direction from q to p must be aligned... no wait. This is wrong. If the light is collimated (all photons travel in direction -sunDir), then the photons passing through the window plane illuminate the room. A point p is lit if the ray from p in direction +sunDir hits the window opening. That's it — a directional light with a shadow test against the window opening.

So: for NEE, we can just do the standard "sample a point on the window rectangle" — that gives the correct directions. For each sampled point q on the window, the incoming radiance at p from the direction d = (q-p)/|q-p| is: L_sun * Ω_sun * ... hmm. Let's think about the transport equation.

The irradiance at p from the sun through the window:
E(p) = ∫_Ω L_in(p, ω) cosθ dω.
The window aperture: a photon from the sun direction ω_s passes through the window and hits p if the ray from p in direction ω_s passes through the opening. So actually the incoming radiance at p is nonzero only in the solid angle subtended by the sun (as seen through the window). Since the sun's angular radius θ_s is small, L_in(p,ω) ≈ L_sun for ω within the sun's disk if the ray p+ωt passes through the window opening.

We can compute this deterministically: E(p) = L_sun * Ω_sun * cosθ_s if the ray from p in direction ω_s passes through the window opening, times a soft edge factor for the penumbra (the sun's finite size blurs the window edge, i.e., partial coverage).

That's an elegant approach! Compute the "coverage" of the sun disk as seen from p through the window. Approximate: the fraction of the sun's disk visible from p through the aperture. We can approximate this by sampling a few points on the sun disk (say, using the aperture sampling): sample a point q on the window, sample a point s on the sun disk (a small disk perpendicular to ω_s centered at distance D in direction ω_s from q or from p)... then check visibility.

Honestly, the simplest approach that's both efficient and correct: **sample a point on the sun quad** but make the sun quad's solid angle not much bigger than the window's solid angle from typical points. Or: sample the sun disk directly and check visibility with the shadow ray (which gets blocked by the wall if the ray doesn't pass through the window). The efficiency issue: the fraction of directions that pass through the window from a floor point vs. the sun's solid angle. If the sun's solid angle is larger, we waste samples; if smaller, we're efficient but shadows are sharp.

Given that the light pool should move visibly, and soft shadows are wanted, an 8° sun is nice. The waste factor is (window solid angle)/(sun solid angle). From a floor point at 2m from the window, the window (2.4 x 1.5) subtends roughly... at distance ~2m, the window is ~30° wide... Solid angle of window from p: roughly A*cos/d² = 3.6*0.5/4 = 0.45 sr?? That's huge. Hmm, from p=(2.5,0,0) to the window at x=4: d ≈ 1.5 to 3.5 (slanted). Solid angle ~ 3.6 * cos / d² ≈ 1.8/4 = 0.45 sr. The sun disk at 8° radius: solid angle = π*θ² = π*0.14² = 0.06 sr. So the window is actually bigger than the sun's solid angle for nearby points! Great — so sampling the sun quad is efficient for nearby points (the light pool region). For points far away (deep in the room, e.g., the sofa at x=-1), the window subtends A cos/d² = 3.6*0.2/25 = 0.03 sr, smaller than the sun's 0.06. But those points are in shadow anyway.

Hmm, wait. But there's another subtlety: the sun quad at distance 25 with half-size 3.5 subtends 8°. But the sun quad must be hit by the ray through the window... fine.

OK, so sampling the sun quad uniformly may waste up to ~50% at the far end and be efficient near the window. That's acceptable. Actually, we can also do a smarter thing: sample the sun quad and, to reduce waste, use a smaller quad: half-size 2 at distance 25 = 4.6° radius, solid angle 0.02 sr. That gives a slightly sharper shadow but is efficient.

Hmm, but for points in the middle of the room, the window subtends ~0.1 sr, and the sun 0.02 — fine, efficient.

Let's go with the sun quad at distance ~25, half-size 2.5, and emission tuned so the illuminance is right. Also, an issue: since the sun is far, the light pool shape = the window projected along the sun direction, which is exactly what we want.

But: the "window opening" — I need the wall geometry to occlude properly, and the wall pieces around the window are boxes. Good.

Also, should I worry that the sun quad is visible through the window and looks like a huge bright panel? At 4.6° angular radius and elevation 35-55°, if the camera looks up through the window, it would see a very bright disk 9° across. That's like looking at the sun — acceptable and even nice (bloom would be nice but no).

Also the sky: when a ray escapes through the window, the sky color. The sky's brightness should be much less than the sun. Sky ~ (0.2, 0.35, 0.7) * 1.0 maybe. That gives a blue tint through the window and lights the room softly.

Now, one thing to be careful about: the interior walls block the sky except through the window. The exterior of the wall boxes: rays that escape the room... wait, the room is enclosed by boxes that are solid; a ray from inside hits the inner face of the wall box. But if a ray hits the wall box from inside, it just stops (the box is opaque). So the "outside" is only reachable through the window opening. Good. But rays that exit through the window and then travel — they'd see the sky or the sun quad. And the exterior of the wall boxes from outside — a ray exiting through the window going backward can't hit the wall boxes' exteriors (the wall is between... well, the window opening is a hole in the wall, so rays exiting through it can hit exterior faces of other wall boxes if they go sideways — those are outside the room, painted... whatever, we can treat them as the sky or as the wall material. Not important; they're barely visible. Actually they'd be visible through the window at grazing angles. Whatever.

Hmm, but there's a subtlety: the exterior of the wall box — with slab-box intersection, if the ray is inside the box we return no hit (or we return the far face?). Standard slab intersection returns the nearest positive t. If a ray exits through the window and travels toward the -z direction, it might hit the exterior of the front wall (z=+4.1 wall box) etc. Since we return the first positive t intersection regardless, it will hit the box exterior. That's fine visually.

Wait, but there's an issue for rays that start inside the room: the room walls are boxes whose inner face is at the interior boundary. E.g., the floor box spans y∈[-0.1,0] — a ray from inside hits y=0 (top face). Fine. The ceiling box y∈[3,3.1] — a ray hits y=3 (bottom face). Fine. The wall box at x∈[-4.1,-4] spans all z,y within the room? Let's define the wall boxes so they overlap at corners to avoid gaps. If the wall boxes extend beyond the room bounds (e.g., x from -4.1 to -4, y from -0.1 to 3.1, z from -4.1 to 4.1), then the interior faces form a clean box. Good.

Now the geometry list. Let's use a uniform array of "objects" with a type flag: 0 = box (with center, half-extents), 1 = sphere (center, radius), 2 = quad (mirror), 3 = sun quad. Actually, I'll define:

```glsl
struct Obj { int type; vec3 p; vec3 a; vec3 b; vec3 c; int mat; };
```
Hmm, three vectors for a box (center, half) and a quad (center, normal, u, v, halfext). Let me use:
- Box: p=center, a=halfExtents, b,c unused.
- Sphere: p=center, a.x=radius.
- Quad: p=center, a=normal, b=u*bh, c=v*bw... 

Actually for the mirror, since it's on the wall, I could just use a thin box with a mirror material — simpler! The mirror is a flat box (thin) with a reflective material. Then I only need boxes and spheres. 

But then the "sun quad" is also a box (thin) with emissive material, rotated — an axis-aligned box can't be rotated. Hmm. The sun needs to be oriented arbitrarily.

Options: make the sun an emissive sphere at a distance (easy!). A sphere at distance 25 with radius 2.2 → angular radius 5°, and it's a proper sphere. Sphere intersection is easy. And for the light PDF, sampling a sphere uniformly by area: pdf_solid = dist²/(A*|cosθ|) where cosθ = the cosine at the sphere surface... for a sphere, the area-to-solid-angle conversion has the cos at the sphere point; we can approximate using the direction to the center: pdf ≈ dist²/(A*cosθ_center) — that's not exactly uniform-area sampling... Actually with uniform area sampling on a sphere, the pdf in solid angle is dist²/(A * |cosθ_L|) where θ_L is the angle between the light normal at the sample point and the direction to the shading point. Since the sphere is small (5°), this is essentially constant. Fine, use the exact formula with the sample point's normal.

Simpler: use uniform *solid angle* sampling of the sphere (sample a direction within the cone, or just sample the visible disk uniformly). Then pdf_solid = 1/Ω where Ω = the solid angle of the sphere ≈ π r²/d². Even easier! Sample a point on the disk of the sphere facing p: build a frame around the direction to the sun center, sample a point in a disk of radius r' ≈ r * sqrt(1 - r²/d²)... For simplicity, sample a point uniformly in a disk of radius r (the sphere's radius) perpendicular to the direction, at distance d, i.e., a "billboard" disk. Then the sampled point is on the plane through the center perpendicular to the view direction; the actual sphere point would be slightly different but for small angular size it doesn't matter. Actually, just treat the sun as a disk light: the geometry is a disk of radius R at distance d perpendicular to the direction. Then pdf_solid = 1/(π R²/d²)·(1/|cosθ|)... ugh, disk vs sphere.

Cleanest: model the sun as an actual sphere with radius R centered at C. NEE: sample uniformly in solid angle within the cone subtended by the sphere from p: pdf = 1/Ω, where Ω = 2π(1 - cos α) with sin α = R/|C-p|. Then the sampled direction may or may not hit the sphere depending on the exact geometry—if we sample within the cone, the direction hits the sphere (since the sphere subtends exactly that cone, tangentially). Yes! A direction within the cone always hits the sphere (for a sphere, the cone of directions that intersect it is exactly the cone of half-angle α). So it's clean: sample a direction in the cone, pdf = 1/Ω, and the contribution = brdf * cos * Le. And the visibility test is a shadow ray in that direction.

And the MIS pdf for a BSDF ray that hits the sun sphere: pdf_L = 1/Ω (constant over the cone). 

This is nice and clean. But the shadow ray must be traced to the sphere: I can just do a regular intersection test with all geometry, but for efficiency... it's fine.

But hold on: for the shadow ray, we need the actual distance. We can just trace the ray against all objects and check whether the nearest hit is the sun sphere. Simple.

Let's do that. The sun sphere: center = windowCenter + dir*25, radius 2.2. Angular radius from a floor point at distance ~27: 4.7°.

Hmm, wait. There's a subtlety: light emitted by the sphere is only visible inside the room through the window. The emission Le should be high enough. The illuminance from a sphere of angular radius α with radiance L: E = L * Ω * cosθ = L * 2π(1-cos α). With α=4.7°, Ω = 2π(1-0.99663) = 0.0212 sr. For E ≈ 15 (bright sunlight-ish, in arbitrary units), L ≈ 700. OK, so emission ~ 700. Values that high are fine in HDR.

Hmm, but also NEE from a point in the room: contribution = brdf*cos*Le*Ω_visible... but the visibility is boolean (the sphere either is or isn't visible through the window). Wait, no! From point p, the sun sphere is visible only through the window aperture. Since the sphere is small, the whole sphere is either visible or not (roughly), giving hard shadows! The softness comes from partial occlusion at the window edge: if part of the cone is blocked by the wall, we get partial. Since the cone is 4.7° and the wall edge is a hard occluder, the penumbra region on the floor is where the sun's disk is partially occluded by the window edge. That gives real soft shadows (penumbra width ~ the sun's angular size projected). Great, that's physically correct soft shadowing.

So the soft shadow arises naturally. And the sample-based estimate is boolean per sample, giving noise in the penumbra. That's acceptable (a few samples + temporal blend).

Now: the sky. When a BSDF ray escapes through the window and hits nothing, we return sky. Also, when the camera looks through the window, it sees the sky through the window — need to make sure the sky is visible and pretty.

But note: the sun sphere is huge and near the window; we might see it if we look up through the window. Fine.

Now the "moving sunlight" — the sun sphere moves along an arc, so the light pool moves. 

Let's now also ensure the room isn't too dark. The window is 2.4 x 1.5 = 3.6 m². With E ≈ 10 in the light pool... Let's just tune constants by feel; I can't test. I'll use reasonable values: sun radiance such that the direct illuminance on the floor is ~8-12 (bright white-ish). Then the albedo ~0.5 → radiance ~ 5 → after tonemapping with exposure ~1, it's blown out. Let's set the tonemap exposure so the sunlit floor is near white. I'll use a filmic/ACES tonemap with exposure 1.0.

Indirect: walls bounce ~0.5 → the room gets 1-3 range values. Good.

Sky: for the window view, sky radiance ~ 1.0-3.0 is good. Let's make the sky gradient from a horizon color (0.6,0.8,1.0)*1.5 to zenith (0.2,0.4,0.9)*2.0. That gives a nice bright window view.

Alright. Now let's write the shader.

```glsl
#version 300 es
precision highp float;
out vec4 outColor;
uniform vec2 uRes;
uniform float uTime;
uniform vec3 uCamPos;
uniform vec3 uCamDir; // forward
uniform vec3 uCamRight;
uniform vec3 uCamUp;
uniform vec2 uJitter;
uniform int uFrame;
uniform vec3 uSunC;
uniform float uSunR;
```

Objects: I'll hardcode them in GLSL as an array with a const count. That's simpler than uploading uniforms. Let's define:

```glsl
#define NBOX 20
struct Box { vec3 c; vec3 h; vec3 alb; float rough; float metal; float spec; float trans; vec3 emis; };
```
Hmm, that's a lot of fields. Let's use a material index lookup:

```glsl
struct Mat { vec3 albedo; float rough; float metal; float spec; float trans; vec3 emis; };
Mat getMat(int id) { ... }  // chain of ifs
```

Materials:
0: wood floor: albedo (0.45,0.26,0.13), rough 0.35, spec 0.25 (glossy varnish), metal 0
1: wall warm (back, -z): albedo (0.75,0.45,0.3), rough 0.9, spec 0.03
2: wall white (window wall + front): albedo (0.85,0.85,0.85), rough 0.9, spec 0.03
3: ceiling: albedo (0.9,0.9,0.9)
4: sofa fabric: albedo (0.35,0.06,0.07), rough 0.9
5: table wood: albedo (0.35,0.2,0.1), rough 0.25, spec 0.4
6: metal: albedo (0.95,0.85,0.6) or silver (0.95,0.95,0.95), metal 1, rough 0.12
7: mirror: metal 1, rough 0.01 → delta. albedo 0.98
8: glass: trans 0.9
9: sun: emissive
10: mirror frame? skip.

Reduce: let's have ~8 materials.

Now the object list. Let's write it as arrays in GLSL using const arrays (GLSL ES 3.0 supports const arrays with initializers? Yes, `const vec3 a[3] = vec3[3](...)`. Actually in GLSL ES 3.00, array constructors are supported. But const array initializers with a struct type... Let me just build the scene in an array of structs at the top of main... hmm, or define a function returning the object by index with a big if-chain. Let's use a compact approach:

```glsl
// objects: type 0 = box, 1 = sphere
// arrays as uniforms? 
```

I'll hardcode an array in a function:

```glsl
const int NOBJ = 22;
// store: type, data..., matid
```
GLSL ES 3.0: `const` arrays of structs with initializers — I believe you can do:
```glsl
struct Obj { int type; vec3 a; vec3 b; int mat; };
const Obj objs[3] = Obj[3](Obj(0, vec3(0), vec3(1), 0), ...);
```
This should work in GLSL ES 3.00? Const struct arrays with constructor initialization... I think it's allowed. Hmm, risky in some drivers. Alternative: use plain arrays of vec4s for each field:

```glsl
const vec4 boxC[12] = vec4[12](vec4(...), ...);
```
That's safe. Or just use if-chains in an intersection function. Honestly, a plain if-chain might be simplest and most compatible:

```glsl
bool boxHit(vec3 ro, vec3 rd, vec3 c, vec3 h, out float t) { ... }

// in intersect:
float best = 1e9; int id = -1; 
hitBox(vec3(-4.1,..), ...) 
```
That's verbose but explicit and safe. With ~22 objects, that's 22 lines per test type. Fine — it's readable.

Actually, let me use arrays of uniforms-free constants via `const vec4` arrays. It's compact:

```glsl
const vec4 BC[16] = vec4[16](vec4(cx,cy,cz, matid), ...);
const vec4 BH[16] = vec4(hx,hy,hz, 0), ...);
```
Hmm, but I also need the material id. I'll put the matid in the .w of the half-extent vector... but half-extents could be non-uniform. It's fine: BH[i].w = material id.

Let's do that. Similarly for spheres: `const vec4 SP[4] = ...` with (center.xyz, radius) and `const vec4 SPM[4] = vec4(matid)`. Or combine: sphere center.xyz, radius in w, and the material id... Let me just use two arrays and a loop with a compile-time constant count.

Hmm, actually GLSL ES 3.00 does support const array constructors:
```glsl
const vec4 arr[3] = vec4[3](vec4(1.0), vec4(2.0), vec4(3.0));
```
Yes, that's standard. Good.

So:

```glsl
const vec4 BOXES[26] = vec4[26]( ... ); // (center.xyz, mat)
const vec4 BOXH[26]  = vec4[26]( ... ); // (halfext.xyz, 0)
const vec4 SPHERES[4] = vec4[4]( ... ); // (center.xyz, r)
```
Hmm, for spheres I need the mat too: `const vec4 SPMAT[4] = vec4[4](vec4(6.0),...)` — fine.

Actually, let me simplify by treating the sun as a sphere with material id 9 (emissive). Then NEE handles it specially.

Let me now list the scene:

Room interior: x∈[-4,4], y∈[0,3], z∈[-4,4].

Boxes (center, half-extents, mat):
1. Floor: c=(0,-0.05,0), h=(4.2,0.05,4.2), mat=0 (wood)
2. Ceiling: c=(0,3.05,0), h=(4.2,0.05,4.2), mat=3
3. Wall -x: c=(-4.05,1.5,0), h=(0.05,1.6,4.2), mat=1 (warm) — hmm, let me make it the mirror wall: light gray/white so the mirror stands out. mat=2 (white)
4. Wall -z (back, behind sofa): c=(0,1.5,-4.05), h=(4.2,1.6,0.05), mat=1 (warm terracotta) → color bleeding onto the sofa and floor.
5. Wall +z (front, behind camera): c=(0,1.5,4.05), h=(4.2,1.6,0.05), mat=2 (white)
6. Window wall +x, 4 pieces around the opening (opening: y∈[0.9,2.4], z∈[-1.2,1.2]):
   a) below: c=(4.05, 0.45, 0), h=(0.05, 0.45, 4.2) → y from 0 to 0.9. But wait, the floor is at y=0 and the wall box goes from y=0 to 0.9 → center y=0.45, half 0.45. ✓
   b) above: y from 2.4 to 3.0 → c=(4.05, 2.7, 0), h=(0.05, 0.3, 4.2)
   c) left (z<-1.2): z from -4.2 to -1.2 → center z = -2.7, half = 1.5 → c=(4.05,1.65,-2.7), h=(0.05,1.65,1.5) → y from 0 to 3.3? That overlaps the floor and ceiling; fine. Let's use y center 1.5, half 1.6 → y ∈ [-0.1, 3.1]. Good.
   d) right (z>1.2): c=(4.05,1.5,2.7), h=(0.05,1.6,1.5)
   So the opening is y∈[0.9,2.4], z∈[-1.2,1.2]. ✓

Furniture:
7. Sofa seat: c=(-0.9,0.3,-3.0), h=(0.85,0.25,0.5), mat=4 (red fabric). So x∈[-1.75,-0.05], y∈[0.05,0.55], z∈[-3.5,-2.5].
   Hmm, the seat should be at y from 0.2 to 0.45 (a base + cushion). Let's do: sofa base c=(-0.9,0.15,-3.0), h=(0.85,0.15,0.5) → y∈[0,0.3]. Cushions: c=(-0.9,0.42,-3.0), h=(0.8,0.12,0.48) → y∈[0.3,0.54].
8. Sofa back: c=(-0.9,0.75,-3.4), h=(0.85,0.45,0.12) → y∈[0.3,1.2], z∈[-3.52,-3.28].
9. Sofa arm L: c=(-1.85,0.45,-3.0), h=(0.12,0.45,0.55) → x∈[-1.97,-1.73]
10. Sofa arm R: c=(0.05,0.45,-3.0), h=(0.12,0.45,0.55)

Table (coffee table): 
11. top: c=(1.6,0.72,0.0), h=(0.55,0.04,0.4) → x∈[1.05,2.15], y∈[0.68,0.76], z∈[-0.4,0.4]
12-15. legs: at (±0.45,±0.3) from the center: c=(1.15,0.34,-0.3), h=(0.03,0.34,0.03) etc. 4 legs.

Glass: sphere at (1.45,0.86,0.05), r=0.09 → sits on the table (table top at y=0.76, so center y=0.85 for r=0.09). mat=8 (glass).
Metal lamp: sphere at (1.95,0.9,-0.15), r=0.13, mat=6 (metal). Hmm, "a metal lamp" — a sphere isn't a lamp. Let's make a lamp: a metal cylinder-ish shape → I can approximate with a metal sphere for the shade plus a thin box for the stand. Or a metal sphere + a small emissive... Let's do a metal sphere shade (r=0.16) at (1.95,1.0,-0.1) and a thin stand box from the table to the shade: c=(1.95,0.88,-0.1), h=(0.02,0.12,0.02).

Hmm, that's a "lamp" — a metal shade on a stand. Good enough. Maybe make the shade a bit flattened: use an ellipsoid? Not with sphere intersection. It's fine.

Mirror on the -x wall: a thin box at x∈[-3.98,-3.94], y∈[0.9,2.3], z∈[-1.0,1.0]: c=(-3.96,1.6,0), h=(0.02,0.7,1.0), mat=7.
Add a frame? skip.

Also maybe a plant or picture — skip.

Sun sphere: center = (4,1.65,0) + dir*25, radius 2.2, mat=9 (emissive).

Total boxes: 4 (room shell: floor, ceiling, -x wall, -z wall, +z wall = 5) + 4 window wall pieces = 9, sofa 6, table 5, mirror 1 = 21. Spheres: 2 (glass, lamp) + 1 sun = 3.

Let me count the boxes carefully:
0 floor
1 ceiling
2 wall -x
3 wall -z
4 wall +z
5 win below
6 win above
7 win left
8 win right
9 sofa base
10 sofa cushion
11 sofa back
12 sofa arm L
13 sofa arm R
14 table top
15 leg1
16 leg2
17 leg3
18 leg4
19 mirror
= 20 boxes. Good.

Spheres: 0 glass, 1 lamp, 2 sun. 3 spheres.

Materials:
0 wood floor
1 warm wall
2 white wall
3 ceiling
4 sofa fabric
5 table wood
6 metal
7 mirror
8 glass
9 sun emissive

Now the intersection function:

```glsl
bool hitBox(vec3 ro, vec3 rd, vec3 c, vec3 h, out float t) {
  vec3 oc = ro - c;
  vec3 inv = 1.0/rd;              // careful with rd components == 0 → inf, which is ok-ish with the min/max
  vec3 t0 = (-h - oc)*inv;   // hmm sign
  ...
}
```
Standard: t1 = (c - h - ro)/rd, t2 = (c + h - ro)/rd, tmin = max(min(t1,t2)), tmax = min(max(t1,t2)); if tmax > max(tmin,0) → hit with t = tmin>0 ? tmin : tmax.

If the ray origin is inside the box (e.g., the camera inside... no, the camera is never inside a box). Actually the camera could be inside the "room shell" boxes? No, the camera is inside the room's interior, which is outside all the wall boxes. Fine. But I should handle it generally. If inside, t = tmax (exit) — but we'd want to report the exit... For opaque objects it doesn't matter. Let's compute: if tmin > 0 use tmin else if tmax > 0 use tmax (which happens when inside). Fine.

For the normal: use the face that was hit — determine by comparing the hit point to the box faces. Easier: compute the normal from the largest component of (p - c)/h. 

```glsl
vec3 boxNormal(vec3 p, vec3 c, vec3 h) {
  vec3 d = (p - c)/h;
  vec3 a = abs(d);
  if (a.x > a.y && a.x > a.z) return vec3(sign(d.x),0,0);
  if (a.y > a.z) return vec3(0,sign(d.y),0);
  return vec3(0,0,sign(d.z));
}
```
Good (works for axis-aligned boxes).

Sphere normal: normalize(p - c).

Now the intersection routine loops over all objects and finds the nearest. 20 boxes + 3 spheres per ray, with up to 5 bounces + shadow rays → 20*6 = 120 box tests per ray... times ~1M pixels * 2 spp = 240M box tests. Hmm, that's heavy but each box test is cheap (~10 flops). 2.4 GFlops per frame... at 60fps that's 144 GFlops/s. Too much for a typical GPU? A modern GPU does several TFLOPS, so it's OK-ish, but let's be careful. Add a simple bounding-sphere early-out? Or reduce the resolution.

Let's do: internal resolution = the canvas size clamped, with a scale of 0.6-0.75. E.g., at 1280x720 * 0.7 = 896x504 = 450k pixels. With 2 spp and 4 bounces: 450k*2*5 = 4.5M ray-scene tests * 23 objects = 100M intersection tests per frame. At 60fps = 6 G tests/s. Each test is maybe 15 ops → 90 GFLOPs. Modern GPUs (even integrated ones?) — a discrete GPU handles it. Integrated might struggle. Let's use 2 spp and MAX_BOUNCES=4, and a resolution scale around 0.65. And make the sun a "sphere" that we test last with an early exit.

I could also use a bounding box test for the whole scene... not worth it. Let's just be reasonable: internal resolution scale ~0.6, spp 2, bounces 4. And I'll add a simple ray-box rejection using the slab method quickly.

Actually a big optimization: for shadow rays, only test the boxes (20) and check if the sun sphere is hit — but actually we just need occlusion: if any object blocks, it's occluded. We can short-circuit.

OK. Let's also handle the case where the path escapes: return the sky.

Now let's write the path tracing loop.

```glsl
vec3 render(vec3 ro, vec3 rd, inout uint seed) {
  vec3 col = vec3(0.0);
  vec3 thr = vec3(1.0);
  float prevPdf = 1.0;
  bool prevDelta = true;   // treat as "came from camera" — MIS weight 1 for the first hit's emission? 
  ...
}
```
Hmm, for the camera ray, if it directly hits the sun sphere (through the window), we add the emission fully (weight 1). Set prevDelta = true at the start (meaning "no previous BSDF, so no MIS").

Hmm wait, MIS weight: when the BSDF ray hits the light, the weight is pdf_B/(pdf_L+pdf_B) computed from the *previous* shading point's sampling. For the camera ray, there's no sampling pdf, so the weight should be 1. So flag it: at the start, prevDelta = true → use weight 1.

Then in the loop:
```
for (int i=0;i<MAXB;i++) {
  Hit h = trace(ro, rd);
  if (!h.hit) { col += thr * sky(rd); break; }
  Mat m = getMat(h.mat);
  
  if (m.emissive) {
     float w = prevDelta ? 1.0 : misW;  // misW computed
     col += thr * m.emis * w;
     break;
  }
  ...
}
```
For the light hit MIS weight, I need pdf_B (the BSDF pdf of the direction that hit the light) and pdf_L (the light pdf for that direction from the previous point). I'll carry `prevPdfB` (the pdf of the direction sampled from the previous point) and compute pdf_L from the previous shading point toward the light hit point.

Simplify: compute pdf_L using the function `lightPdf(prevP, hitPoint)` where the direction is toward the hit point. Since pdf_L = 1/Ω (cone sampling), and Ω depends on the distance from prevP to the sun center. So pdf_L = 1/Ω(prevP). Constant over the small cone. Easy!

And pdf_B = the pdf from the previous BSDF sampling.

misW = pdf_B/(pdf_B + pdf_L).

Then the direct lighting at each non-delta surface:
```
if (!m.isDelta) {
   // sample the sun
   vec3 wi; float pdfL; vec3 L = sampleSun(p, wi, pdfL);
   if (L != 0) {
      // shadow ray
      if (!occluded(p+n*eps, wi)) {
         vec3 f = evalBrdf(wo, wi, n, m);
         float cosT = dot(wi, n);
         // MIS weight for light strategy
         float pdfB = brdfPdf(wo, wi, n, m);
         float wL = pdfL/(pdfL+pdfB);
         col += thr * f * cosT * L * wL / pdfL;
      }
   }
}
```
Wait, `L` is the light's radiance, and the contribution is f*cos*L/pdfL. So `sampleSun` returns the radiance and the pdf. Since the sun's radiance is uniform over the cone, L = Le. So the contribution = f*cos*Le*Ω*wL. 

Hmm, note that pdfL = 1/Ω, so dividing by pdfL multiplies by Ω. Fine.

Then the BSDF sampling:
```
vec3 wi; float pdfB; vec3 f = sampleBrdf(wo, n, m, seed, wi, pdfB);
if (pdfB <= 0) break;
thr *= f * dot(wi,n) / pdfB;
prevPdfB = pdfB;
prevDelta = m.isDelta;
prevP = p; prevN = n;
ro = p + n*eps; rd = wi;
```
And for the emissive-hit MIS weight, we need prevPdfB and the pdf_L from the previous point: pdf_L = 1/Ω(prevP_to_sun_center_distance). We compute the distance from prevP to the sun center.

But careful: the cone sampling pdf is only valid if the hit is actually the sun sphere. If the BSDF ray hits the sun sphere, then pdf_L = 1/Ω. ✓.

Note the case where prevDelta is true (mirror or glass) → the MIS weight is 1 for the emission.

Also, need `prevP` to compute the light's Ω. Actually, Ω depends on the distance, which I can compute from the hit point and the sun center — but the origin matters slightly. Just use the distance from the previous shading point. I'll store prevOrigin.

Now the BRDF.

```glsl
struct Mat { vec3 alb; float rough; float metal; float spec; float trans; vec3 emis; };
```
Let me define the material function with an if-chain returning a Mat.

```glsl
Mat getMat(int id) {
  Mat m;
  m.alb = vec3(0.5); m.rough=0.8; m.metal=0.0; m.spec=0.0; m.trans=0.0; m.emis=vec3(0.0);
  if (id==0) { m.alb=vec3(0.42,0.24,0.11); m.rough=0.3; m.spec=0.35; }
  else if (id==1) { m.alb=vec3(0.72,0.38,0.24); m.rough=0.95; }
  else if (id==2) { m.alb=vec3(0.82,0.82,0.80); m.rough=0.9; }
  else if (id==3) { m.alb=vec3(0.9,0.9,0.88); m.rough=0.95; }
  else if (id==4) { m.alb=vec3(0.38,0.07,0.08); m.rough=0.85; }
  else if (id==5) { m.alb=vec3(0.32,0.17,0.08); m.rough=0.35; m.spec=0.4; }
  else if (id==6) { m.alb=vec3(0.95,0.85,0.55); m.rough=0.15; m.metal=1.0; m.spec=1.0; }
  else if (id==7) { m.alb=vec3(0.98,0.98,0.98); m.rough=0.0; m.metal=1.0; m.spec=1.0; }
  else if (id==8) { m.alb=vec3(1.0); m.trans=1.0; m.rough=0.0; }
  else if (id==9) { m.emis=vec3(1.0,0.95,0.85)*SUN_LE; }
  return m;
}
```

For delta detection: `bool isDelta = (m.trans > 0.5) || (m.spec > 0.9 && m.rough < 0.05);`

Simplify: add a `delta` float to the material struct? I'll compute `m.rough < 0.02` → delta for specular.

Let me define isSpec = m.metal > 0.5 || m.spec > 0.5 ... Let's just write:

```glsl
bool deltaSpec = (m.rough < 0.05 && m.spec >= 0.9);
bool isGlass = m.trans > 0.5;
bool isDelta = deltaSpec || isGlass;
```

For the mirror (id 7): spec=1, rough=0, metal=1 → delta reflection with a tint = alb (0.98).
For the metal lamp (id 6): spec=1, rough=0.15, metal=1 → glossy, non-delta.

BSDF model:

Diffuse part: albedo * (1 - specWeight) / π, where specWeight = m.spec (a scalar). Actually for the metal, spec=1 so the diffuse = 0.

Glossy specular part: a Phong lobe with exponent n, tinted: for the metal, use alb; for the non-metal, use vec3(1) * spec.

Let's define:
- kd = alb * (1 - spec)
- ks = (metal>0.5 ? alb : vec3(1.0)) * spec
- n_exp = 2/(rough^2) - 2, clamp to [1, 5000]. For rough=0.15: n = 2/0.0225 - 2 = 86. For rough=0.3: 2/0.09-2 = 20. For rough 0.35: 14.

Phong BRDF: f_s = ks * (n+2)/(2π) * cos^n(α) where α is the angle from the reflection direction.

Sampling: choose diffuse with prob p_d = kd_lum/(kd_lum + ks_lum), else specular. pdf = p_d * cosθ/π + (1-p_d) * (n+1)/(2π) * cos^n α. 
Sampled value f*cos/pdf must be evaluated properly. It's easier to compute the pdf and the brdf value separately and use f*cos/pdf.

For a cosine-power lobe with exponent n, the pdf = (n+1)/(2π) cos^n α, and the value = ks*(n+2)/(2π)*cos^n α. So f/pdf = ks*(n+2)/(n+1). Nice.

So the mixture: pdf_total = pd*pdfD + (1-pd)*pdfS, and f_total = kd/π + ks*(n+2)/(2π)*cos^n α. Then the throughput factor = f_total * cosθ / pdf_total. That works and is well-defined.

OK let's write:
```glsl
float phongPdf(float cosA, float n) { return (n+1.0)*0.5*INV_PI*pow(max(cosA,0.0), n); }
```

Now, glass: delta refraction. With Fresnel (Schlick). 
```
float eta = 1.0/1.5; if (entering) eta = 1/1.5 else 1.5
```
Determining "entering": if dot(wo, n) < 0 ... let's define n as the outward normal (from the geometry). For a sphere, the normal points outward. For a glass sphere, a ray hitting it is entering; when inside, dot(rd, n) > 0.

Standard approach:
```
vec3 nl = n;
float cosi = -dot(wo, n... 
```
Let me write it carefully. Let wo = -rd (direction toward the viewer/previous point). 

```
vec3 nl = dot(wo, n) > 0 ? n : -n;   // normal facing the viewer
float eta = dot(wo, n) > 0 ? (1.0/ior) : ior;   // hmm
```
Actually: if dot(wo, n) > 0 → the viewer is outside, so we're entering → eta = 1/ior. If the ray goes inside, we're exiting → eta = ior.

Wait, wo = -rd points from the surface back to the previous point. If dot(wo,n) > 0, the previous point is on the outside → the ray is entering the glass. Then eta = 1.0/ior = 1/1.5.

Then:
```
float cosi = dot(wo, nl);
float sin2t = eta*eta*(1.0 - cosi*cosi);
if (sin2t > 1.0) → total internal reflection (reflect only)
else refract
```
Fresnel Schlick: R0 = ((1-ior)/(1+ior))^2 = 0.04. R = R0 + (1-R0)*(1-cos)^5 — using the appropriate cos (cosi if entering, cost if exiting). Use the standard.

Then with probability R reflect, else refract. Weight = 1 (since we divide by the probability... the standard trick: choose one, weight 1).

Tint: multiply by the glass albedo (1.0) or a slight green tint (0.95, 0.98, 0.95).

Now let's define the trace function.

```glsl
struct Hit { float t; vec3 p; vec3 n; int mat; bool hit; };
```

I'll implement `Hit trace(vec3 ro, vec3 rd)`.

And `bool occluded(vec3 ro, vec3 rd, float maxT)` — loops over all objects, returns true if any hit with t < maxT.

For the shadow ray to the sun: maxT = the distance to the sun sample point. Also skip... the sun sphere itself: if the shadow ray hits the sun sphere, that's the light, not an occluder. So in occluded(), skip the sun sphere (index 2 of spheres). Since the shadow ray goes toward a point inside the sun's disk, we should exclude the sun. Just check only the boxes + the non-sun spheres, with t < maxT.

Actually simpler: the shadow ray tests all objects except the sun; if any is hit closer than the light distance → occluded.

Let's now handle the NEE sampling of the sun:

```glsl
// returns radiance, sets wi, pdf (solid angle)
vec3 sampleSun(vec3 p, out vec3 wi, out float pdf) {
  vec3 d = uSunC - p;
  float dist = length(d);
  float sinA = uSunR/dist;
  if (sinA > 0.999) { pdf=1.0; wi=normalize(d); return sunLe; }
  float cosA = sqrt(1.0 - sinA*sinA);
  float omega = 2.0*PI*(1.0 - cosA);
  pdf = 1.0/omega;
  // sample direction in the cone around normalize(d)
  vec3 w = normalize(d);
  vec3 u = normalize(cross(abs(w.y)<0.9?vec3(0,1,0):vec3(1,0,0), w));
  vec3 v = cross(w,u);
  float u1 = rnd(), u2 = rnd();
  float ct = 1.0 - u1*(1.0-cosA);
  float st = sqrt(max(0.0,1.0-ct*ct));
  float phi = 2.0*PI*u2;
  wi = normalize(u*st*cos(phi) + v*st*sin(phi) + w*ct);
  return sunLe;
}
```
And the pdf for a given direction (for MIS) is pdf = 1/omega computed from the previous point's distance to the sun center.

`lightPdf(vec3 p)` = 1/omega.

Now `sunLe`: the emission. But wait — the sun sphere's material is emissive, and when a ray hits it via BSDF sampling, we get m.emis. So sunLe = the material's emission. Let's set SUN_LE = 800 or so and tune.

Let's compute the expected brightness. The floor in the light pool: irradiance E = Le * Ω * cosθ_incident... plus the window occlusion. Ω = 2π(1-cosA). With R=2.2, dist=25 → sinA = 0.088, cosA = 0.9961 → Ω = 0.0245 sr. E = 800*0.0245*0.7 = 13.7. Then the floor's radiance = E * albedo/π = 13.7*0.42/3.14 = 1.8. Hmm, that's a nice bright value. Plus the sky contribution.

For the tonemap, exposure 1.0 with ACES: 1.8 → ACES(1.8*exposure) ≈ ~0.85. Good.

Let's set SUN_LE = 700.

Sky radiance: let's use ~1.5 at the horizon, 3.0 at the zenith — this adds a blue window view and some ambient. The window's solid angle from the room is small so it adds a bit of light. Fine.

Wait, but the sky will be sampled by BSDF rays only, so it's noisy. With a small window, the sky-lit area is dimmer than the sun; it should be fine.

Hmm — but there's a subtle problem: the sky is not NEE-sampled but it IS a source of MIS inconsistency? No — MIS is only needed when two strategies sample the same light. The sky is only reachable by BSDF rays, so no double counting. Fine.

Now, the sun sphere is also visible directly when looking through the window (it's an object). If a BSDF ray from a wall hits the sun sphere, we add emission * MIS weight. Fine.

Careful: the MIS weight for a BSDF ray hitting the sun uses pdf_L computed at the previous vertex; if the previous vertex is far from where the light cone is (e.g., a mirror bounce), the cone's Ω is computed from the distance to the sun center. Fine.

But careful: if a BSDF ray hits the sun sphere from a point where the sun is not "visible" (e.g., behind the wall, the ray would have hit the wall first). Right, the sun sphere is only hit if the ray actually reached it (through the window). OK.

Now, one more thing: the sun sphere is within the scene bounds; the shadow-ray test excludes it. But the BSDF trace includes it. Good.

Let me now think about the "sky" function:
```glsl
vec3 sky(vec3 rd) {
  float t = clamp(rd.y*0.5+0.5, 0.0, 1.0);
  vec3 c = mix(vec3(0.9,0.85,0.75)*1.2, vec3(0.35,0.55,1.0)*2.2, smoothstep(0.0,0.7,rd.y));
  // sun glow
  float g = max(0.0, dot(rd, normalize(uSunC - vec3(4.0,1.65,0.0))));
  c += vec3(1.0,0.85,0.6) * pow(g, 300.0) * 5.0;
  return c;
}
```
Something like that. Also, for rays going below the horizon (rd.y<0 outside), return a ground color (dim). Not important.

Hmm, but note: the sky is only seen through the window from inside, so rd.y is rarely negative... it can be if looking downward out the window. Let's add a ground term.

Now, camera ray generation:
```
vec2 uv = (gl_FragCoord.xy + jitter - 0.5*uRes)/uRes.y;  // y-normalized
vec3 rd = normalize(uCamDir + uCamRight*uv.x*tanHalfFovX... 
```
Standard: 
```
float fov = 55 degrees;
vec3 rd = normalize(uCamF + uCamR*uv.x + uCamU*uv.y);
```
where uCamF = forward, and uCamR, uCamU are scaled by tan(fov/2) and the aspect.

Let me compute in JS: 
```
const fwd = normalize(target - pos);
const right = normalize(cross(fwd, up));
const upv = cross(right, fwd);
const tanHalf = tan(fov/2);
camR = right * tanHalf * aspect;
camU = upv * tanHalf;
camF = fwd;
```
And the shader: `rd = normalize(uCamF + uCamR*uv.x + uCamU*uv.y)` with uv in [-1,1] scaled by aspect on x.

I'll pass uv as `vec2 uv = (fragCoord - 0.5*res)/ (0.5*res.y)` → x in [-aspect, aspect], y in [-1,1]. Then rd = normalize(F + R*uv.x + U*uv.y).

Depth of field: a slight DoF. Need aperture sampling: 
```
vec2 ap = apertureDisk(rnd, rnd) * apertureRadius;
vec3 ro = camPos + camR_norm*ap.x + camU_norm*ap.y;   // using the *unnormalized* basis? 
```
We need the world-space right/up unit vectors, not scaled by tanHalf. Let me pass separate uniforms: uCamRightVec, uCamUpVec (unit), and uCamR/uCamU (scaled). Or just pass the unit right/up and the tanHalf separately. Simpler: pass uCamF, uCamR (scaled), uCamU (scaled) and additionally uCamRX, uCamUX (unit)? That's more uniforms. Alternatively, derive the unit vectors: right_unit = normalize(uCamR), up_unit = normalize(uCamU). Since uCamR = right*tanHalf*aspect, normalizing gives the unit right. 

But the focus: we want to focus on a distance `focusDist`. The ray direction from ro toward the point (camPos + rd*focusDist) — standard thin lens:
```
vec3 p = camPos + rd * focusDist;
ro = camPos + right*aperture.x + up*aperture.y;
rd = normalize(p - ro);
```
Good. Set the aperture radius ~0.02-0.04 (a slight DoF). With a focus distance of ~3.5m and an aperture of 0.03, the CoC is small — a "slight depth of field". Let's use 0.035.

Careful: with a small aperture and a near focus, distant objects blur a lot? CoC ≈ aperture * |1 - f/d|... The blur angle = apertureRadius * |1/focus - 1/d|... For aperture 0.035 and focus 3.5: at d=8 → 0.035*(1/3.5-1/8)=0.035*0.16=0.0056 rad ≈ 0.3°. With a 55° FOV over 720px, that's ~0.3/55*720 = 4 px. Reasonable slight blur.

Focus distance: set it varying to look nice, e.g., 3.5 + sin(t)*1.5? Or just fixed on the room center. Let's focus at the distance to the look-at target ≈ |target - camPos|. That keeps the subject sharp.

Now: the temporal accumulation. I'll do the blend with a constant alpha. On resize, reset (clear the accumulation buffer). Actually with EMA, on resize the content is stale — just clear it.

Hmm, one concern: with EMA blending and a moving camera, bright edges leave trails. Let's set alpha = 0.5 (a 2-frame half-life) → mild. Or 0.4. I'll use 0.4.

Hmm, is the EMA going to look bad? Let's think: the camera orbits at 0.2 rad/s → at radius 1.5, that's 0.3 m/s. The walls are ~4m away. Over 0.1s (6 frames), the camera moves 3cm → at 4m, that's ~0.4° → ~5 px of motion. With alpha 0.4, the effective ghost length is ~2.5 frames → 12 px of smearing. Hmm, that's noticeable on sharp edges. Maybe too much.

Alternative: use alpha = 0.6 (a shorter tail). The noise reduction is then ~1.6x. Meh.

Alternative: no temporal accumulation, but more spp per frame. With 4 spp at 0.6 resolution... performance?

Hmm. Let me reconsider: I'll do a compromise: alpha = 0.5 and a lower spp (2). Actually, let's think about what looks best. A path-traced image at 2 spp is quite noisy. With EMA 0.5, the effective spp ≈ 4 (variance halves). Actually, an EMA with α has an effective averaging window of 2/α - 1 samples: for α=0.5, that's 3 samples → a 1.5x noise reduction (sqrt(3/2)). Not huge.

Honestly, ghosting at α=0.5 with a slow camera is fine and looks like motion blur. Let's do α=0.5, 2 spp/frame.

Hmm, but the light pool moving also causes ghosting of the light patch. The sun moves at 0.07 rad/s; over ~0.1s it moves 0.007 rad; the light pool would shift by ~25*0.007 = 0.17m at the distance... no, on the floor the shift is ~ 0.17m ≈ significant vs. the pool size of ~2m. Over 3 frames, that's a small fraction. Fine.

OK, let me go with the EMA. Actually, you know what — let me make it simpler and more robust: no temporal accumulation. Instead, render at 2 spp and use a spatial denoise? No, too complex.

Decision: use EMA with alpha 0.45. It's 15 lines. On resize, clear the buffer.

Hmm, wait. There's one more concern with blend-based accumulation: `gl.blendFunc(gl.CONSTANT_ALPHA, gl.ONE_MINUS_CONSTANT_ALPHA)` with a float16 target requires EXT_float_blend? No — EXT_float_blend is only needed for 32F. 16F blending is core. RGBA16F is color-renderable in WebGL2 (yes, it's required to be renderable? In WebGL2, RGBA16F is color-renderable... Actually in WebGL2, RGBA16F is texture-filterable and color-renderable only with EXT_color_buffer_float. Hmm! In WebGL2, EXT_color_buffer_float enables rendering to RGBA16F/RGBA32F. Without it, RGBA16F is not color-renderable (though half-float textures exist).

To be safe, I'll request EXT_color_buffer_float and fall back to RGBA8 if unavailable. RGBA8 accumulation would clamp [0,1] — with EMA it's OK-ish but highlights clip. Let's just require the extension; most platforms have it. I'll add a fallback to RGBA8 with a note.

Alternatively, avoid the accumulation texture entirely: render directly to the canvas with the tonemapping in the shader, and do the EMA in a separate buffer... no.

Actually simplest fallback: if the float extension is missing, render direct to the screen (no EMA). I'll code both paths.

Hmm, this is getting long. Let me simplify: always render to an RGBA16F texture with EXT_color_buffer_float (requested; if missing, use RGBA8 and accept clipping). Then the second pass tonemaps to the screen. I'll write it so the internal format is chosen at init.

Let me now write the code.

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>WebGL2 Path Tracer — Interior</title>
<style>
  html,body{margin:0;height:100%;background:#000;overflow:hidden;font-family:ui-monospace,monospace}
  canvas{display:block;width:100vw;height:100vh}
  #label{position:fixed;left:10px;bottom:10px;color:#cfe;background:rgba(0,0,0,.45);padding:4px 8px;border-radius:6px;font-size:12px;letter-spacing:.4px;pointer-events:none}
</style>
</head>
<body>
<canvas id="c"></canvas>
<div id="label">…</div>
<script> ... </script>
</body>
</html>
```

Now the JS.

```js
const canvas = document.getElementById('c');
const gl = canvas.getContext('webgl2', {antialias:false, alpha:false, depth:false, stencil:false, preserveDrawingBuffer:false});
if (!gl) { document.body.innerHTML = '<p style="color:#fff">WebGL2 not supported</p>'; }
const extCBF = gl.getExtension('EXT_color_buffer_float');
```

Shaders.

Vertex shader (shared):
```glsl
#version 300 es
void main(){
  vec2 p = vec2((gl_VertexID<<1)&2, gl_VertexID&2);  // gives (0,0),(2,0),(0,2)
  gl_Position = vec4(p*2.0-1.0, 0.0, 1.0);
}
```
Wait: gl_VertexID 0 → (0,0); 1 → (2,0); 2 → (0,2). p*2-1 → (-1,-1), (3,-1), (-1,3). Full-screen triangle. And gl_FragCoord covers the whole screen. 

But I need the same vertex shader for the blit pass; that works for both.

Path tracer fragment shader:

```glsl
#version 300 es
precision highp float;
precision highp int;
out vec4 fragColor;

uniform vec2  uRes;
uniform vec3  uCamPos;
uniform vec3  uCamF;
uniform vec3  uCamR;
uniform vec3  uCamU;
uniform vec2  uJitter;
uniform float uAperture;
uniform float uFocus;
uniform vec3  uSunC;
uniform float uSunR;
uniform float uSeed;
uniform int   uSpp;
#define PI 3.14159265359
#define INV_PI 0.31830988618
```

RNG: PCG hash.

```glsl
uint hash(uint x){ x ^= x>>17; x *= 0xed5af49bu; x ^= x>>11; return x; }
uint rngState;
uint rng(){ rngState = rngState*747796405u + 2891336453u; uint w = ((rngState>>((rngState>>28u)+4u))^rngState)*277803737u; return (w>>22u)^w; }
float rnd(){ return float(rng())*(1.0/4294967296.0); }
```
That's the PCG-ish hash. Standard.

Now the scene.

```glsl
const int NBOX = 20;
const vec4 BOX[20] = vec4[20]( ... );  // xyz = center, w = mat
const vec4 BOXH[20] = vec4[20]( ... ); // xyz = half
```
Hmm, mat in the .w of the half-extent vec4 would save an array. Let's keep the separate arrays but put mat in BOX[i].w... but the center needs to be full. Use BOX[i].xyz = center, BOX[i].w unused, and BOXH[i].w = mat. That saves an array. But the material id as a float then cast to int. Fine.

Let me just write two arrays:
BOX: vec4(center.xyz, halfExtent.x)... no, half has 3 components. 

Use:
```glsl
const vec4 BC[20];  // center.xyz, 0
const vec4 BH[20];  // half.xyz, matid
```
Two arrays. And spheres:
```glsl
const vec4 SP[3];  // center.xyz, radius
```
with mats known by index: 0=glass, 1=metal, 2=sun.

Let me now hardcode. Room: x∈[-4,4], y∈[0,3], z∈[-4,4].

BC/BH list:

0 Floor: c(0,-0.05,0) h(4.2,0.05,4.2) m0
1 Ceiling: c(0,3.05,0) h(4.2,0.05,4.2) m3
2 Wall -x: c(-4.05,1.5,0) h(0.05,1.6,4.2) m2
3 Wall -z: c(0,1.5,-4.05) h(4.2,1.6,0.05) m1
4 Wall +z: c(0,1.5,4.05) h(4.2,1.6,0.05) m2
5 Win below: c(4.05,0.45,0) h(0.05,0.45,4.2) m2
6 Win above: c(4.05,2.7,0) h(0.05,0.3,4.2) m2
7 Win left: c(4.05,1.5,-2.7) h(0.05,1.6,1.5) m2
8 Win right: c(4.05,1.5,2.7) h(0.05,1.6,1.5) m2
9 Sofa base: c(-0.9,0.15,-3.0) h(0.85,0.15,0.5) m4
10 Sofa cushion: c(-0.9,0.42,-3.0) h(0.80,0.12,0.48) m4
11 Sofa back: c(-0.9,0.75,-3.4) h(0.85,0.45,0.12) m4
12 Arm L: c(-1.85,0.45,-3.0) h(0.12,0.45,0.55) m4
13 Arm R: c(0.05,0.45,-3.0) h(0.12,0.45,0.55) m4
14 Table top: c(1.6,0.72,0) h(0.55,0.04,0.42) m5
15 Leg: c(1.15,0.34,-0.32) h(0.03,0.34,0.03) m5
16 Leg: c(2.05,0.34,-0.32) h(0.03,0.34,0.03) m5
17 Leg: c(1.15,0.34,0.32) h(0.03,0.34,0.03) m5
18 Leg: c(2.05,0.34,0.32) h(0.03,0.34,0.03) m5
19 Mirror: c(-3.96,1.6,0) h(0.02,0.7,1.0) m7

Wait, the mirror at x=-3.96 with hx=0.02 → x from -3.98 to -3.94. But the wall's inner face is at x=-4. So the mirror is 0.02 in front of the wall. Good.

Hmm, the -x wall box: c(-4.05,1.5,0) h(0.05,...) → x from -4.1 to -4.0. ✓.

Spheres:
0: glass: c(1.45,0.85,0.05) r 0.09 → sits on the table top (y=0.76). 0.76+0.09 = 0.85 ✓.
1: lamp: the shade c(1.95,1.02,-0.10) r 0.16, and a stand box.
   Hmm, I need a stand: add box 20. Let me add it: c(1.95,0.88,-0.10) h(0.02,0.12,0.02) m6. That adds a 21st box. Let me include it and set NBOX=21.
2: sun.

Actually, the lamp shade as a sphere sitting on a stand looks like a lollipop. Fine, it's a "metal lamp".

Let me reconsider the lamp: put it on the floor next to the sofa? "a table with a glass and a metal lamp" — the lamp is on the table. OK, on the table. Fine.

Careful: the lamp sphere at (1.95, 1.02) r 0.16 → x from 1.79 to 2.11, z from -0.26 to 0.06, y from 0.86 to 1.18. The table top is at y up to 0.76, so the shade floats above the table with the stand connecting. Good.

Glass sphere at (1.45,0.85,0.05) r=0.09: x 1.36-1.54, z -0.04 to 0.14, y 0.76-0.94. On the table. ✓

Now the sun path. Window center at (4, 1.65, 0).

```
float t = uTime;
float az = 0.85*sin(t*0.075);        // ±48.7°
float el = 0.72 + 0.16*sin(t*0.053); // 41° ± 9°  → 32° to 50°
vec3 dir = vec3(cos(el)*cos(az), sin(el), cos(el)*sin(az));
uSunC = vec3(4.0,1.65,0.0) + dir*25.0;
```
Wait, I want the sun to be positioned so light comes through the window. The direction from the window to the sun is `dir` which has +x, +y, ±z. The light travels in the -dir direction into the room. The light pool on the floor is offset in -x from the window and offset in ∓z. Good.

The sun sphere radius 2.2 → angular radius from a point at distance ~28: 4.5°.

Hmm: I should double check the sun disk isn't so big that the light pool's soft edge is huge. The penumbra width = the window's distance from the floor along the light direction * the sun's angular size. For the window at y≈2.4 (top), the light travels to the floor ~2.4/sin(41°)... the distance along the light ray from the window to the floor is ~2.4/0.66 = 3.6m. The penumbra width ≈ 3.6 * 0.078 rad (4.5°) = 0.28m. The light pool is ~2m. So a 0.28m penumbra — nice soft shadows. 

Now, the light pool position: for a floor point, the shadow ray toward the sun must pass through the window (y from 0.9 to 2.4, z from -1.2 to 1.2). With the sun at elevation el and azimuth az, the direction from a floor point p to the sun ≈ -dir (pointing up and away). The ray from p going in direction (approximately) -(cos el cos az, sin el, cos el sin az)... wait no. The direction from the floor point to the sun center is roughly normalize(uSunC - p) ≈ (cos el cos az, sin el, cos el sin az) (since the sun is far in +x). Hmm, so the direction is +x, +y. Yes: the light comes from +x and above, so the shadows extend in -x. ✓.

A floor point p=(x,0,z): the ray to the window plane x=4 takes Δx = 4-x, so the height at the window is y = (4-x)*tan(el)*... well: y = (4-x)*(sin el)/(cos el cos az) and the z offset = (4-x)*(cos el sin az)/(cos el cos az) = (4-x)*tan(az).

For the light to pass through the window: y ∈ [0.9, 2.4] and z + (4-x)*tan(az) ∈ [-1.2,1.2].

With el=41°: tan(el)=0.87. For x=3: Δx=1 → y=0.87 <0.9 (just blocked by the sill). For x=2.5: Δx=1.5 → y=1.30 ✓. For x=2: Δx=2 → y=1.74 ✓. For x=1.4: Δx=2.6 → y=2.26 ✓. For x=1.2: Δx=2.8 → y=2.44 >2.4 ✗ (blocked by the lintel).

So the light pool spans x from ~1.3 to ~2.9 → a 1.6m wide pool on the floor. Nice, and it will sweep in z as az changes. Also, as el increases, the pool moves toward +x. 

The table (x 1.05-2.15) is inside the pool region — the sun will hit the table top and the glass/lamp → nice highlights. And it casts a shadow on the floor. 

Now, the sun sphere at distance 25 in the direction dir — is it in front of the window (outside)? uSunC = (4 + 25 cos el cos az, 1.65 + 25 sin el, 25 cos el sin az). With el=41°, cos el=0.755, az=0: x = 4+18.9 = 22.9, y = 1.65+16.4 = 18.05, z=0. Fine, high in the sky to the +x side.

Now the walls block it, so it's only visible through the window. ✓

Also: the sun sphere at radius 2.2 at 25m — is it outside the room? Yes.

One more: the wall boxes have finite extent (4.2 half). A ray from inside the room going out through the window will hit nothing (sky) — good.

Now, is there light leakage? The room is fully enclosed except the window. Rays through the window escape to the sky/sun. ✓

Alright, and the sun moving means its light pool sweeps. Also el changes slightly.

Let me now think about the sun's azimuth range: az ±48.7°. The z offset at the floor = (4-x)*tan(az) → at x=2, Δx=2, tan(48.7)=1.14 → 2.28m of z shift. The pool would move off... the window is 2.4 wide in z (±1.2), so the pool would shift out of the window's projection and disappear. Hmm, that means at max azimuth the light pool is blocked (the window's z extent limits it). At az=48.7°, for a floor point to receive light: z + (4-x)*1.14 ∈ [-1.2,1.2]. For x=2: z ∈ [-3.48, -1.08]. So the pool would be at z ≈ -2.3, which is in front of the sofa. Hmm, that's fine — the light pool moves to the sofa area. But it might partially be blocked by the sofa. That's fine, dramatic lighting.

Actually, that's nice: the sun patch sweeping across the floor and onto the sofa. But we should ensure the pool doesn't disappear entirely. With az range ±0.85 rad (±48.7°), the pool at extreme azimuth lands on z ∈ [-3.5,-1] for x=2. That's visible on the floor between the sofa and the table. OK.

Hmm, but the pool is only 1.6m wide in x and the shape gets skewed. Fine. Let's reduce the azimuth range a bit to ±0.7 rad (±40°) so the pool stays more centered: tan(40)=0.84 → z offset 1.68 at x=2 → z ∈ [-2.88,-0.48]. Ok.

Actually, we want it to move a lot to be visible as "the sun moves across the floor". Let's keep ±0.75.

Also, we could slowly vary the elevation too.

Now the camera. Let's compute the camera in JS (based on time) and pass to the shader. 

```js
const t = time;
const a = Math.PI + t*0.21;          // start looking at the window wall
const r = 1.45 + 0.25*Math.sin(t*0.13);
const camPos = [Math.cos(a)*r, 1.45 + 0.22*Math.sin(t*0.17), Math.sin(a)*r];
// target: opposite side, with vertical variation
const b = a + Math.PI;
const tr = 1.1 + 0.6*Math.sin(t*0.09);
const target = [Math.cos(b)*tr, 1.05 + 0.35*Math.sin(t*0.11), Math.sin(b)*tr];
```
Hmm, with the camera at angle a and looking at angle a+π, the camera looks across the room at the opposite wall. At t=0, a=π: camPos = (-1.45, 1.45, 0), target = (1.1*cos(2π)=1.1, 1.05, 0). So looking in the +x direction at the window wall. ✓ Great.

Then as t increases, a increases: the camera moves to a=3π/2: camPos=(0,·,-1.45), target=(0,·,+1.1) → looking toward +z (the front wall, which is blank white). Hmm, that's a boring view for a while. The walls are: +x = window, -z = sofa/warm wall, -x = mirror, +z = blank front wall. So a quarter of the orbit looks at the blank +z wall. Meh, but it's only ~7 seconds and the room's furniture is visible at the edges. Let's add something on the +z wall — a picture frame? Or move the sofa? Let's just add a couple of picture-frame boxes on the +z wall to give it interest. Or a bookshelf. Let's add a simple picture frame: a dark box with a colored canvas. Two boxes: frame and canvas. Cheap.

Actually, let's keep the object count low. Add one picture: box c(0,1.8,3.98) h(0.5,0.35,0.02) mat=5 (wood frame) and a canvas box c(0,1.8,3.95) h(0.42,0.27,0.01) mat=? Let's make a new material (emissive? no, just a colored one). I'll reuse mat 1 (warm) — a terracotta picture. Meh. Let's add mat 10: picture (deep blue/teal). Actually, an important use: a colored surface for color bleeding. Let's just do the frame + a canvas using mat 1.

Hmm, I'm adding complexity. Alternatively, accept the blank wall — the camera pans past it in ~7s and the room's other elements are visible at the edges. Since the camera looks across the room at the opposite wall, from the center we see a decent chunk of the room. It's fine. But let's add a simple picture for visual interest — 2 boxes. I'll do it.

Wait, I realize the mirror is on the -x wall, and when the camera looks at the -x wall (a = π/2 + ... ), it will see the mirror reflecting the room, including possibly the camera and the window. That's a great moment. It happens at a = 3π/2 (camera at +x side looking -x) → t = (3π/2 - π)/0.21 = 7.5s. So at ~7.5s we see the mirror. Good, within 30s.

At t=0 we see the window. At ~7.5s the mirror. At ~15s the camera looks at the -z wall (sofa) — wait let me redo. The camera looks at the wall opposite to its position. Camera at angle a (position), looking toward a+π. So it sees the wall at angle a+π. 
- a=π → sees the +x wall (window). t=0.
- a=3π/2 (t=7.5) → sees the +z wall? Wait: a=3π/2 → the camera is at (cos(3π/2), sin(3π/2)) = (0,-1) → the camera is on the -z side, looking toward a+π = 5π/2 ≡ π/2 → direction (0,+1) → the +z wall. Hmm, so the camera at the -z side (near the sofa) looking at the +z wall.

Let me recompute: at a=π, the camera is at (-1,0) [the -x side], looking toward a+π=2π ≡ 0 → direction (+1,0) → the +x wall (window). ✓ (camera on the -x side, looking at the window on the +x wall ✓).

The camera position angle a, looking toward the opposite side. So it sees the wall on the opposite side. 
- a=π → sees the +x wall (window) ✓ t=0
- a=π+π/2=3π/2 (t=7.5) → the camera at (0,-1) [the -z side], sees the +z wall.
- a=2π (t=15) → the camera at (1,0) [+x side], sees the -x wall (mirror). ✓
- a=5π/2 (t=22.4) → the camera at (0,1) [+z side], sees the -z wall (sofa).
- a=3π (t=30) → back to the window.

So within 30s we see: window (0s), +z wall (7.5s), mirror (15s), sofa (22.4s). The blank +z wall occupies 7.5s. Adding a picture helps.

Hmm, also the camera at the -z side is at (0,-1.45) which is close to the sofa (z from -3.5 to -2.5) — no, the camera is at z=-1.45, well clear. ✓.

And at the +x side, the camera is at (1.45, 1.45, 0) — above the table (x 1.05-2.15, z ±0.42), y=1.45 > table height 0.76. Fine, but the lamp top is at y=1.18 — the camera passes 0.27m above it. It might clip the lamp shade in the near plane! The camera at (1.45,1.45,0) and the lamp at (1.95,1.02,-0.10) with r=0.16 → the distance from the camera to the lamp top is sqrt(0.5²+0.43²+0.1²)=0.67. Not too close. OK.

But the glass sphere at (1.45,0.85,0.05): the camera at (1.45,1.45,0) is 0.6m above it. Fine.

Let's also add a slight forward/back dolly: r oscillates. And the target oscillates. OK.

Let me double check the camera never goes through a wall: max |camPos| = sqrt(1.7² ) with r up to 1.7 → within ±1.7. Room is ±4. ✓ y from 1.23 to 1.67 ✓.

Also, the camera should look at the target which is at radius up to 1.7 in the opposite direction. The camera is looking across, so the room's far wall is ~5.7m away. Good.

Now, is the composition good? The camera at (-1.45,1.45,0) looking at (1.1,1.05,0) — a horizontal view across the room, with the window at x=4 in the center of the view. The table at x 1.05-2.15 is right in the middle foreground. 

FOV: 55° vertical? Let's use fov=50° vertical... Actually, let's think in terms of horizontal: with aspect 16/9 and vfov 55, hfov = 2*atan(tan(27.5°)*1.78) = 2*atan(0.925) = 85°. That's wide. Let's use vfov 45° → hfov 2*atan(0.414*1.78)=2*36.4=73°. Reasonable for an interior. I'll use 48°.

Now let me write the path tracer main.

```glsl
void main(){
  vec2 uv = (gl_FragCoord.xy + uJitter - 0.5*uRes) / (0.5*uRes.y);
  ...
  vec3 acc = vec3(0.0);
  for (int s=0;s<uSpp;s++){
     // jitter per sample
     vec2 j = vec2(rnd(), rnd());  // hmm, we already jittered uv outside
  }
}
```
Better: do the jitter inside the sample loop. So:
```
for (int s=0;s<SPP;s++){
   vec2 off = vec2(rnd(), rnd()) - 0.5;
   vec2 uv = (gl_FragCoord.xy + off - 0.5*uRes)/(0.5*uRes.y);
   vec3 dir = normalize(uCamF + uCamR*uv.x + uCamU*uv.y);
   // DoF
   vec2 ap = sampleDisk()*uAperture;
   vec3 ro = uCamPos + normalize(uCamR)*ap.x + normalize(uCamU)*ap.y;
   ... hmm, careful: the aperture offset should be in the camera plane using unit vectors.
   vec3 target = ro + dir*uFocus;   // careful, use camPos + dir*focus
   vec3 ro2 = uCamPos + rightU*ap.x + upU*ap.y;
   vec3 rd = normalize(uCamPos + dir*uFocus - ro2);
   acc += trace(ro2, rd);
}
acc /= float(SPP);
fragColor = vec4(acc, 1.0);
```
Wait, `normalize(uCamR)` gives the unit right vector only if uCamR = right*tanHalf*aspect (a positive scale). Yes. Same for uCamU. Good.

Let me define the RNG seed per pixel: `rngState = hash(uint(gl_FragCoord.x) + uint(gl_FragCoord.y)*1973u + uFrame*9277u)`.

Now the trace function:

```glsl
vec3 trace(vec3 ro, vec3 rd) {
  vec3 col = vec3(0.0);
  vec3 thr = vec3(1.0);
  bool prevDelta = true;
  float prevPdf = 1.0;
  vec3 prevPos = ro;
  for (int i=0;i<MAXB;i++){
    Hit h = traceScene(ro, rd);
    if (!h.hit){ col += thr*skyColor(rd); break; }
    Mat m = getMat(h.mat);
    if (m.emis != vec3(0.0)) {   // emissive
       float w = 1.0;
       if (!prevDelta) {
          float pdfL = lightPdf(prevPos);
          w = prevPdf/(prevPdf+pdfL);
       }
       col += thr*m.emis*w;
       break;
    }
    ...
  }
}
```

Hmm, careful: for the glass, the ray continues inside and could hit the sun? No.

Also, for the glass, we need to handle the ray origin offset properly (using the normal in the direction of travel).

Let me write the shading part:

```glsl
    vec3 n = h.n;
    vec3 wo = -rd;
    if (dot(wo,n) < 0.0) n = -n;   // face the normal toward the viewer
```
Careful for the glass: we need the original outward normal to determine entering/exiting. Let me keep `vec3 gn = h.n` (geometric outward) and use `dot(rd, gn) < 0` → entering.

For non-glass surfaces, flipping n to face the viewer is fine (for thin boxes it matters little).

Let me write:

```glsl
    vec3 nl = dot(n, wo) > 0.0 ? n : -n;
```
where wo = -rd.

Then:

```glsl
    // Glass
    if (m.trans > 0.5) {
      bool entering = dot(rd, n) < 0.0;   // n is the outward geometric normal
      float eta = entering ? 1.0/IOR : IOR;
      vec3 nf = entering ? n : -n;
      float cosi = clamp(dot(wo, nf), 0.0, 1.0);
      float sin2t = eta*eta*(1.0-cosi*cosi);
      float F;
      vec3 newDir;
      if (sin2t >= 1.0) { F = 1.0; newDir = reflect(-wo, nf); }
      else {
        float cost = sqrt(1.0-sin2t);
        float r0 = (1.0-IOR)/(1.0+IOR); r0*=r0;
        float Fr = r0 + (1.0-r0)*pow(1.0-cosi,5.0);
        // use cost-based fresnel for exit? keep simple
        if (rnd() < Fr) { F = 1.0; newDir = reflect(-wo, nf); }
        else { F = 0.0; newDir = normalize(eta*(-wo) ... ); }
      }
```
Refraction: `vec3 refr = refract(-wo, nf, eta)` — GLSL's refract(I, N, eta) with I incident (pointing toward the surface), N the normal facing the incident side, eta = eta_i/eta_t. So: `refract(-wo, nf, eta)` where eta = 1/1.5 entering. Note -wo = rd. So `refract(rd, nf, eta)`. And nf is the normal facing against rd. Hmm, GLSL refract expects N to be the normal pointing toward the incident side (i.e., dot(I,N) < 0). Since nf is flipped so that dot(wo, nf) > 0, i.e., dot(-rd, nf) > 0 → dot(rd, nf) < 0 ✓. Good.

So `vec3 rdir = refract(rd, nf, eta);` if it returns 0 (TIR), reflect.

thr *= tint (a slight absorption). Then ro = h.p + rdir*eps... need to offset against the surface: ro = h.p + nf*1e-4 (offset outside the surface in the direction the ray is going). Actually, offset along the ray direction: `ro = h.p + rdir*1e-4` might not be enough for a sphere's curvature; but with the ray direction offset it's fine (moving the origin slightly along the ray keeps the same ray, avoiding self-intersection at t≈0). Actually, for a sphere, moving along the ray direction by eps keeps the origin on the same ray — the sphere is convex, so from inside the sphere, the ray will exit and then... For a glass sphere, the ray inside goes to the other side. If I offset the origin by 1e-4 along the ray, then when I trace, the self-intersection at t≈0 is avoided if eps > numerical error. Good. Use eps=1e-3 maybe. But then a thin object (like the mirror box 0.04 thick) could be skipped. For the glass sphere, 1e-3 is fine.

Actually, better: offset the origin by the normal: `ro = h.p + nf*sign*1e-3`. Hmm. Let's use the ray-direction offset with eps = 2e-4 relative... Honestly for a sphere of radius 0.09, an offset of 1e-4 along the ray avoids re-hitting the same point. Let's use `ro = h.p + rdir*1e-4;` and increase tMin in the intersection to 1e-5. Should be OK with float32 at these scales (coordinates ~1-4, so the float precision at 4 is ~5e-7). An offset of 1e-4 is 200x the ULP. Fine.

Actually, wait: after refracting into the sphere, I trace from a point just inside the sphere. The sphere's far intersection is at t up to 0.18. Fine.

Standard: for any surface, offset along the direction. Let's use 1e-4.

Now, the diffuse/glossy:

```glsl
    // compute kd, ks, exponent
    ...
```

Let me write the BRDF helpers:

```glsl
float powSpec(vec3 w, vec3 n, vec3 r, float ex) { return pow(max(dot(w,r),0.0), ex); }
```
where r = reflect(-wo, n) is the mirror direction.

```glsl
vec3 specDir(vec3 wo, vec3 n, float ex) {
  // sample around the reflection direction with cosine-power
  vec3 r = reflect(-wo, n);
  float u1 = rnd(), u2 = rnd();
  float ct = pow(u1, 1.0/(ex+1.0));
  float st = sqrt(max(0.0,1.0-ct*ct));
  float phi = 2.0*PI*u2;
  vec3 t = normalize(cross(abs(r.y)<0.9?vec3(0,1,0):vec3(1,0,0), r));
  vec3 b = cross(r,t);
  return normalize(t*st*cos(phi)+b*st*sin(phi)+r*ct);
}
```
And the probability of choosing the specular lobe: ps = luminance(ks)/(luminance(ks)+luminance(kd)). 

For metal (kd=0), ps=1. For the floor (spec 0.35, alb 0.42): ks = 1.0*0.35 = 0.35 (white tint), kd = 0.42*0.65 = 0.27 → lum(ks)=0.35, lum(kd)=0.27 → ps=0.56. So it's quite reflective. Hmm, for a varnished floor, that's a strong specular. Let's reduce the floor spec to 0.15.

Actually the "spec" parameter as a Phong amplitude with (n+2)/(2π) normalization: the peak value = ks*(n+2)/(2π); for n=20, that's ks*3.5. And the integral over the hemisphere = ks. So the spec component has an energy of ks. With ks=0.35 that's a lot of energy in the specular. For a varnished floor, maybe 0.1 is reasonable. But then the reflection would be subtle. Let's keep the floor spec at 0.25 for a nice glossy sheen, and it will show reflections of the window. Fine, artistic license.

Hmm, but there's an issue: with a Phong exponent n and the (n+2)/(2π) normalization, the lobe peak intensity grows with n. This can cause fireflies when the sun (a tiny bright light) is reflected. With rough=0.3, n=20, the peak = ks*3.5*... And the sun's radiance is 700. A glossy highlight could reach 700*0.25*3.5/... The throughput would spike: f*cos/pdf where pdf = (n+1)/(2π)cos^n. At the peak cos=1: f = ks*(n+2)/(2π) = 0.25*3.5 = 0.875, pdf = (n+1)/(2π) = 3.34, cos=1 → factor = 0.875/3.34 = 0.26. That's fine — the throughput factor is bounded by ks*(n+2)/(n+1) ≈ ks. Good, no firefly explosion.

But the MIS weight for the light: the light sample at the exact specular direction gives f*cos*Le*Ω*wL. With f up to 0.875 and Le*Ω = the irradiance ~13, that gives ~11 * wL. Fine.

OK.

Now, the diffuse sample: cosine-weighted hemisphere around nl.

The combined PDF: for the sampled direction wi, pdf = pd*pdfD + ps*pdfS, where pdfD = cos/π and pdfS = (n+1)/(2π)*cos^n(angle from r).

I choose the lobe with probability pd, then sample within that lobe. And then compute the total pdf for the direction and use f_total*cos/pdf_total. The f_total = kd/π + ks*(n+2)/(2π)*cos^n.

Good, this is a valid mixture BRDF.

Now, the color: albedo/π for diffuse. Multiply by (1-spec).

Let me write:

```glsl
vec3 kd = m.alb*(1.0-m.spec);
vec3 ks = mix(vec3(1.0), m.alb, m.metal)*m.spec;
float ex = 2.0/(m.rough*m.rough) - 2.0; clamp(1.0, 2000.0);
```
For the mirror with rough=0, this blows up. Handle the delta case separately first.

Delta specular handling:
```glsl
if (m.rough < 0.045 && m.spec > 0.5) {
   vec3 r = reflect(rd, nl);  // careful: reflect(rd, n) where n faces the viewer
   ...
}
```
Wait: `reflect(I,N)` returns I - 2*dot(N,I)*N. With I=rd and N=nl (facing the viewer, dot(rd,nl)<0) → correct reflection. ✓

thr *= ks (the tint). Then continue with ro = h.p + r*eps.

Since prevDelta=true, the next hit's emission gets weight 1 ✓, and NEE is skipped for this vertex ✓.

Alright.

Now the sky function needs the sun glow — I'll pass the sun direction.

Let's also add a slight "sun glow" around the sun in the sky. Fine.

Now the tonemap pass:

```glsl
#version 300 es
precision highp float;
in ... no, we use gl_FragCoord and a full-screen triangle.
uniform sampler2D uTex;
uniform float uExposure;
out vec4 o;
void main(){
  vec3 c = texelFetch(uTex, ivec2(gl_FragCoord.xy), 0).rgb;
  c *= uExposure;
  // ACES approx
  c = (c*(2.51*c+0.03))/(c*(2.43*c+0.59)+0.14);
  c = pow(clamp(c,0.0,1.0), vec3(1.0/2.2));
  o = vec4(c,1.0);
}
```
Note: the accumulation texture is at a lower resolution than the screen; use `texture(uTex, uv)` with linear filtering instead of texelFetch. Since the canvas is fullscreen, gl_FragCoord.xy / uScreenSize gives the uv. Use texture() with LINEAR filtering. Good.

Now, the accumulation texture needs LINEAR filtering — RGBA16F is filterable in WebGL2 (yes, half-float textures are filterable by default). RGBA32F requires OES_texture_float_linear. So use RGBA16F.

Set up:
```js
function makeTarget(w,h){
  const tex = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.texImage2D(gl.TEXTURE_2D,0, internalFormat, w,h,0, gl.RGBA, gl.HALF_FLOAT, null);
  gl.texParameteri(... MIN_FILTER, LINEAR); MAG LINEAR; WRAP CLAMP;
  const fbo = gl.createFramebuffer();
  gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
  gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
  ...
}
```

Render loop:
```js
function frame(now){
  ...
  // pass 1
  gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
  gl.viewport(0,0,RW,RH);
  gl.enable(gl.BLEND);
  gl.blendFunc(gl.CONSTANT_ALPHA, gl.ONE_MINUS_CONSTANT_ALPHA);
  gl.blendColor(0,0,0,alpha);
  gl.useProgram(ptProgram);
  set uniforms...
  gl.drawArrays(gl.TRIANGLES,0,3);
  gl.disable(gl.BLEND);
  // pass 2
  gl.bindFramebuffer(gl.FRAMEBUFFER, null);
  gl.viewport(0,0,canvas.width, canvas.height);
  gl.useProgram(blitProgram);
  bind tex 0; uniform...
  gl.drawArrays(gl.TRIANGLES,0,3);
  requestAnimationFrame(frame);
}
```
Alpha: if the size changed or it's the first frame, clear the target first and use alpha=1.

Hmm — with blending enabled and the framebuffer not cleared, the first frame blends with garbage. So on the first frame (or resize), clear the FBO and set alpha=1.0.

Now let me also handle the resolution: 
```js
const scale = 0.62;
RW = Math.max(160, Math.floor(canvas.width * scale));
```
Canvas size = window inner size * devicePixelRatio? Using devicePixelRatio > 1 costs a lot. Let's use dpr = 1 for the internal render and let CSS scale the canvas: set canvas.width = innerWidth (CSS px) and use CSS to stretch. Actually, to keep it aspect-correct, set canvas.width = innerWidth, canvas.height = innerHeight (CSS pixels), and the render target at 0.62 of that.

Actually, let's cap the internal resolution: RW = min(960, w*0.62). Hmm, for a big monitor, 0.62*1920 = 1190. That's a lot of pixels. Let's cap the total: maxPixels = 480000 (e.g., 900x533). Compute the scale so that RW*RH <= maxPixels.

Let me do:
```js
let W = innerWidth, H = innerHeight;
canvas.width = W; canvas.height = H;
let scale = Math.min(0.75, Math.sqrt(460000/(W*H)));
RW = Math.max(200, Math.round(W*scale)); RH = ...
```
Hmm, for a 1920x1080 screen: W*H = 2M, sqrt(460000/2M)=0.48 → RW=920, RH=518. OK.
For a 1200x800 screen: sqrt(460000/960000)=0.69 → capped at 0.75 → 0.69 → RW=828, RH=552.

Fine.

SPP per frame: 2. Max bounces: 4 (maybe 5). Let's use 4 for the diffuse and allow more for specular... keep it simple: 4.

Actually, for a good look with glass and mirrors, more bounces help. Let's use MAXB=5 but with Russian roulette after 2 bounces? RR adds noise. Let's use 4 fixed bounces.

Hmm, the glass sphere with 4 bounces: camera → glass (enter) → glass (exit) → floor → sky/sun. That's exactly 4. OK, workable. Let's use 5 to be safe.

Performance: 5 bounces * 2 spp * 24 objects... Let's reduce: MAXB=4, spp=2. Or make the spp adaptive based on the frame time. Let's keep it simple: spp=2, MAXB=4.

Hmm, I worry about performance on a weak GPU. I could add adaptive resolution... no, keep it simple.

Let me finalize the object list and write the code.

One more consideration: the mirror should reflect the room. It's a delta mirror (rough=0.02?). With rough < 0.045 → delta. Set the mirror's rough to 0.0 and spec=1, metal=1. Then `isDelta`. The reflection tint = ks = alb = 0.98. Good.

For the metal lamp, rough=0.12 → non-delta, spec=1, metal=1, ks=alb. ex = 2/0.0144 - 2 = 137. Nice glossy metal.

Now, let me write the whole thing.

Also, the label: "samples: X" where X = the accumulated sample count. Since we don't accumulate across frames in a strict sense, I'll display the per-frame spp and the frame counter, e.g., "2 spp/frame · frame 1234 · 4 bounces". Hmm, the requirement: "Include a small label with the number of accumulated samples." I'll show "samples: N" where N = the number of samples accumulated in the current image (i.e., spp per frame * the temporal blend's effective window). Hmm.

Alternative: I can actually implement real progressive accumulation that doesn't freeze: when the camera moves, we reset. But the camera always moves. So "accumulated samples" would always be 2-3.

Hmm, what if I make the camera move in a way... no, it must move the whole time.

I'll display: "samples/pixel: 2 · accumulated: <totalSamples>" where totalSamples = spp * frameCount (the total number of samples traced). That satisfies "the number of accumulated samples" loosely. Let me display: `spp 2 · frame 1234 · total samples 2468`. Or simply "samples: 2468 (2/frame)". I'll show a compact label.

Actually, let me reconsider: maybe a better interpretation is fine — show the samples accumulated in the current frame's image, i.e., 2. That looks weak. Let's show both: "frame 1234 · 2 spp × EMA · 2468 samples total". Hmm, keep it short:

`samples: 2468  ·  2 spp/frame  ·  4 bounces`

Good.

Now let's write the GLSL carefully.

```glsl
#version 300 es
precision highp float;
out vec4 fragColor;

uniform vec2  uRes;
uniform vec3  uCamPos;
uniform vec3  uCamF;
uniform vec3  uCamR;
uniform vec3  uCamU;
uniform float uAperture;
uniform float uFocus;
uniform vec3  uSunC;
uniform float uSunR;
uniform float uSunLe;
uniform uint  uFrame;
uniform int   uSpp;

#define PI 3.14159265359
#define INV_PI 0.3183098861837907
#define IOR 1.5
#define MAXB 5
#define NBOX 21
```

Wait, GLSL ES 3.00 supports uint uniforms. Fine.

RNG:
```glsl
uint rngState;
uint pcg(){
  rngState = rngState * 747796405u + 2891336453u;
  uint w = ((rngState >> ((rngState >> 28u) + 4u)) ^ rngState) * 277803737u;
  return (w >> 22u) ^ w;
}
float rnd(){ return float(pcg()) * 2.3283064365386963e-10; }
```

Scene data as const arrays.

```glsl
const vec4 BC[NBOX] = vec4[NBOX](
  vec4(0.0,-0.05,0.0,0.0),   // 0 floor
  ...
);
const vec4 BH[NBOX] = vec4[NBOX](
  vec4(4.2,0.05,4.2, 0.0),
  ...
);
```
where BH.w = mat id.

Hmm, GLSL will complain if I write `vec4[NBOX](...)` — array size from a const int is fine in GLSL ES 3.0.

Let me write out all the entries.

BC:
0  floor      (0, -0.05, 0)
1  ceiling    (0, 3.05, 0)
2  wall -x    (-4.05, 1.5, 0)
3  wall -z    (0, 1.5, -4.05)
4  wall +z    (0, 1.5, 4.05)
5  win below  (4.05, 0.45, 0)
6  win above  (4.05, 2.7, 0)
7  win left   (4.05, 1.5, -2.7)
8  win right  (4.05, 1.5, 2.7)
9  sofa base  (-0.9, 0.15, -3.0)
10 cushion    (-0.9, 0.42, -3.0)
11 back       (-0.9, 0.75, -3.4)
12 arm L      (-1.85, 0.45, -3.0)
13 arm R      (0.05, 0.45, -3.0)
14 table top  (1.6, 0.72, 0.0)
15 leg        (1.15, 0.34, -0.32)
16 leg        (2.05, 0.34, -0.32)
17 leg        (1.15, 0.34, 0.32)
18 leg        (2.05, 0.34, 0.32)
19 mirror     (-3.96, 1.6, 0.0)
20 lamp stand (1.95, 0.88, -0.10)

BH (half-extents, mat):
0  (4.2, 0.05, 4.2, 0)   floor mat0
1  (4.2, 0.05, 4.2, 3)   ceiling mat3
2  (0.05, 1.6, 4.2, 2)
3  (4.2, 1.6, 0.05, 1)
4  (4.2, 1.6, 0.05, 2)
5  (0.05, 0.45, 4.2, 2)
6  (0.05, 0.30, 4.2, 2)
7  (0.05, 1.6, 1.5, 2)
8  (0.05, 1.6, 1.5, 2)
9  (0.85, 0.15, 0.5, 4)
10 (0.80, 0.12, 0.48, 4)
11 (0.85, 0.45, 0.12, 4)
12 (0.12, 0.45, 0.55, 4)
13 (0.12, 0.45, 0.55, 4)
14 (0.55, 0.04, 0.42, 5)
15 (0.03, 0.34, 0.03, 5)
16 (0.03, 0.34, 0.03, 5)
17 (0.03, 0.34, 0.03, 5)
18 (0.03, 0.34, 0.03, 5)
19 (0.02, 0.70, 1.0, 7)   mirror
20 (0.02, 0.12, 0.02, 6)  lamp stand

Wait, box 11 (sofa back): c=(-0.9,0.75,-3.4), h=(0.85,0.45,0.12) → y from 0.3 to 1.2, z from -3.52 to -3.28. And the seat cushion is at z -3.48..-2.52. OK, the back overlaps the cushion. Fine (they're all opaque).

Hmm, the sofa back is at z -3.52..-3.28 which is inside the room (wall at z=-4). ✓

Also, the seat base y from 0 to 0.3, the cushion y 0.3-0.54. ✓

Spheres:
```glsl
const vec4 SP[3] = vec4[3](
  vec4(1.45, 0.85, 0.05, 0.09),   // glass
  vec4(1.95, 1.02, -0.10, 0.16),  // lamp
  vec4(0,0,0,0)                   // sun (dynamic)
);
```
The sun sphere is dynamic — I'll handle it separately in the trace (not in the const array), or pass its center/radius as uniforms to the intersection function. Let me handle the sun specially:

```glsl
bool hitSun(vec3 ro, vec3 rd, out float t){
  vec3 oc = ro - uSunC;
  float b = dot(oc, rd);
  float c = dot(oc,oc) - uSunR*uSunR;
  float h = b*b - c;
  if (h < 0.0) return false;
  h = sqrt(h);
  t = -b - h;
  if (t < 1e-4) { t = -b + h; if (t < 1e-4) return false; }
  return true;
}
```

And in traceScene, include it with mat 9.

Ok. Let me write the trace:

```glsl
struct Hit { bool hit; float t; vec3 p; vec3 n; int mat; };

Hit traceScene(vec3 ro, vec3 rd){
  Hit h; h.hit=false; h.t=1e30; h.mat=-1;
  for (int i=0;i<NBOX;i++){
    float t;
    if (boxHit(ro,rd,BC[i].xyz,BH[i].xyz,t)) {
      if (t < h.t) { h.t=t; h.hit=true; h.mat=int(BH[i].w); h.n = boxN(ro+rd*t, BC[i].xyz, BH[i].xyz); h.p = ro+rd*t; }
    }
  }
  for (int i=0;i<2;i++){
    float t; 
    if (sphHit(ro,rd,SP[i].xyz,SP[i].w,t)) { ... mat = (i==0)?8:6; }
  }
  // sun
  float t; if (hitSun(ro,rd,t)) { if (t<h.t){h.t=t;h.hit=true;h.mat=9; h.p=ro+rd*t; h.n=normalize(h.p-uSunC);} }
  return h;
}
```

Wait, h.p should be computed after. Let me restructure to compute h.p at the end.

Actually since I compute h.p inside the loop after the t update, that's wasteful but fine. Let me instead track the best t and mat and normal, then compute p at the end... but the normal needs p. OK, just compute it in the branch.

For the shadow ray:

```glsl
bool occluded(vec3 ro, vec3 rd, float maxT){
  for (int i=0;i<NBOX;i++){ float t; if (boxHit(ro,rd,BC[i].xyz,BH[i].xyz,t) && t < maxT) return true; }
  for (int i=0;i<2;i++){ float t; if (sphHit(ro,rd,SP[i].xyz,SP[i].w,t) && t < maxT) return true; }
  return false;
}
```
Note: skip the sun. ✓ And the shadow ray origin should be offset from the surface.

boxHit:
```glsl
bool boxHit(vec3 ro, vec3 rd, vec3 c, vec3 h, out float t){
  vec3 o = ro - c;
  vec3 inv = 1.0/rd;
  vec3 t1 = (-h - o)*inv;
  vec3 t2 = ( h - o)*inv;
  vec3 tmin = min(t1,t2);
  vec3 tmax = max(t1,t2);
  float tn = max(max(tmin.x,tmin.y),tmin.z);
  float tf = min(min(tmax.x,tmax.y),tmax.z);
  if (tf < max(tn, 1e-4)) return false;
  t = tn > 1e-4 ? tn : tf;
  return true;
}
```
Careful with rd components equal to 0 → inv = inf, and (-h-o)*inf = ±inf; min/max handles it: if rd.x=0 and o.x is within [-h,h], then t1.x=-inf, t2.x=+inf; if outside, both are +inf or both -inf. Hmm, if o.x > h.x then (-h-o) < 0 and (h-o) < 0, so t1 = -inf... wait (-h-o)*inf where (-h-o) is negative and inf is positive → -inf. And (h-o)*inf → -inf too. So tmin.x = tmax.x = -inf → tn = max(...,-inf) → could still be governed by other axes, and tf = min(-inf,...) = -inf → tf < tn → no hit. ✓ Correct.
If o.x < -h.x: (-h-o) > 0 → +inf; (h-o) > 0 → +inf. tmin=tmax=+inf → tn=+inf... max(tmin.x, tmin.y, tmin.z) = +inf → tf (min of the tmax) at most +inf → tf < tn is false if tf is +inf... Hmm, if all axes are +inf, tn=+inf and tf=+inf → tf < max(tn,eps) → +inf < +inf false → continues → t = tn > eps ? tn : tf → t = +inf. Then a "hit" at t=infinity. That would be a problem if it's the nearest hit (t=1e30 initial → inf > 1e30, so it wouldn't be selected). Hmm, inf > 1e30 → true, so it's not selected. Actually `t < h.t` → inf < 1e30 is false. So it won't be chosen. OK, but to be safe, let's add `if (t > 1e29) return false;`. Or check `tn < tf` properly with a bound. Let me add a max distance check: if (tn > 1e6) return false. Fine.

NaN issues: inf - inf = NaN. Where could that happen? max(min(...)) with infs — no subtraction of infs here. `(-h-o)*inv` — no. OK.

Hmm, but `t = tn > 1e-4 ? tn : tf;` if tn = -inf and tf = 5 → t=5 ✓ (the origin is inside the box and it exits at 5). Good.

sphHit: standard.

boxN:
```glsl
vec3 boxN(vec3 p, vec3 c, vec3 h){
  vec3 d = (p-c)/h;
  vec3 a = abs(d);
  if (a.x>=a.y && a.x>=a.z) return vec3(d.x>0.0?1.0:-1.0,0,0);
  if (a.y>=a.z) return vec3(0,d.y>0.0?1.0:-1.0,0);
  return vec3(0,0,d.z>0.0?1.0:-1.0);
}
```

Now the material function.

```glsl
struct Mat { vec3 alb; float rough; float spec; float metal; float trans; vec3 emis; };
Mat getMat(int id){
  Mat m;
  m.alb=vec3(0.7); m.rough=0.9; m.spec=0.0; m.metal=0.0; m.trans=0.0; m.emis=vec3(0.0);
  if (id==0){ m.alb=vec3(0.40,0.22,0.10); m.rough=0.35; m.spec=0.22; }
  else if (id==1){ m.alb=vec3(0.70,0.34,0.20); }
  else if (id==2){ m.alb=vec3(0.80,0.80,0.78); }
  else if (id==3){ m.alb=vec3(0.86,0.86,0.84); }
  else if (id==4){ m.alb=vec3(0.34,0.06,0.07); m.rough=0.85; }
  else if (id==5){ m.alb=vec3(0.30,0.15,0.07); m.rough=0.4; m.spec=0.25; }
  else if (id==6){ m.alb=vec3(0.95,0.83,0.55); m.rough=0.13; m.spec=1.0; m.metal=1.0; }
  else if (id==7){ m.alb=vec3(0.97,0.97,0.97); m.rough=0.0; m.spec=1.0; m.metal=1.0; }
  else if (id==8){ m.alb=vec3(0.95,0.98,0.95); m.trans=1.0; }
  else if (id==9){ m.emis=vec3(1.0,0.93,0.80)*uSunLe; }
  return m;
}
```

Emissive check: `if (m.emis.r+m.emis.g+m.emis.b > 0.0)`.

Now the trace:

```glsl
vec3 tracePath(vec3 ro, vec3 rd){
  vec3 col = vec3(0.0);
  vec3 thr = vec3(1.0);
  bool prevDelta = true;
  float prevPdf = 1.0;
  vec3 prevPos = ro;
  for (int bounce=0; bounce<MAXB; bounce++){
    Hit h = traceScene(ro,rd);
    if (!h.hit){ col += thr*skyColor(rd); break; }
    Mat m = getMat(h.mat);
    if (m.emis.r>0.0){
      float w = 1.0;
      if (!prevDelta){
        float pdfL = lightPdf(prevPos);
        w = prevPdf/(prevPdf+pdfL);
      }
      col += thr*m.emis*w;
      break;
    }
    vec3 n = h.n;
    vec3 wo = -rd;
    vec3 nf = dot(wo,n)>0.0 ? n : -n;

    // ---- glass
    if (m.trans > 0.5){
      bool entering = dot(rd,n) < 0.0;
      float eta = entering ? (1.0/IOR) : IOR;
      vec3 nn = entering ? n : -n;
      float cosi = clamp(dot(wo,nn),0.0,1.0);
      float sin2t = eta*eta*max(0.0,1.0-cosi*cosi);
      vec3 nd;
      if (sin2t > 1.0){ nd = reflect(rd,nn); }
      else {
        float r0 = (1.0-IOR)/(1.0+IOR); r0*=r0;
        float F = r0 + (1.0-r0)*pow(1.0-cosi,5.0);
        nd = (rnd()<F) ? reflect(rd,nn) : refract(rd,nn,eta);
        if (dot(nd,nd) < 1e-6) nd = reflect(rd,nn);
      }
      thr *= m.alb;
      prevDelta = true;
      ro = h.p + nd*1e-4;
      rd = normalize(nd);
      continue;
    }
    // ---- delta mirror
    if (m.rough < 0.05 && m.spec > 0.5){
      vec3 nd = reflect(rd, nf);
      thr *= m.alb;   // (metal tint)
      prevDelta = true;
      ro = h.p + nd*1e-4; rd = nd; continue;
    }
    // ---- glossy/diffuse
    vec3 kd = m.alb*(1.0-m.spec);
    vec3 ks = mix(vec3(1.0), m.alb, m.metal)*m.spec;
    float ex = max(1.0, 2.0/(m.rough*m.rough) - 2.0);
    float pS = lum(ks) / max(1e-4, lum(ks)+lum(kd));
    vec3 refl = reflect(-wo... 
```
Hmm careful: `reflect(rd, nf)` where nf faces the viewer. GLSL reflect(I,N) = I - 2*dot(N,I)*N. With I=rd, N=nf, dot(rd,nf)<0 → rd - 2*(neg)*nf = rd + positive*nf → points away from the surface ✓. Good.

The specular reflection direction r = reflect(rd, nf).

NEE:
```glsl
    // Next event estimation
    if (!prevDelta){ ... } // no, NEE is done at every non-delta vertex
    vec3 wi; float pdfL;
    vec3 Lr = sampleSun(h.p, wi, pdfL);
    if (Lr.r>0.0){
      float cosT = dot(wi, nf);
      if (cosT > 0.0 && !occluded(h.p+nf*1e-4, wi, 1e30)){
        // evaluate brdf
        float cA = max(dot(wi, refl), 0.0);
        vec3 f = kd*INV_PI + ks*((ex+2.0)/(2.0*PI))*pow(cA, ex);
        float pdfB = pS*((ex+1.0)/(2.0*PI))*pow(cA,ex) + (1.0-pS)*cosT*INV_PI;
        float w = pdfL/(pdfL+pdfB);
        col += thr * f * cosT * Lr * w / pdfL;
      }
    }
```
Wait, `Lr` is the radiance; the contribution is f*cos*Lr/pdfL*w. ✓

Then the BSDF sample:
```glsl
    vec3 wi; float pdfB;
    if (rnd() < pS){
      // specular lobe
      wi = specDir(refl, ex);
      float cA = max(dot(wi,refl),0.0);
      pdfB = (ex+1.0)/(2.0*PI)*pow(cA,ex);
    } else {
      wi = cosineDir(nf);
      pdfB = 0.0; // computed below
    }
```
Hmm, the pdf must be the total mixture pdf, not the individual. So:
```glsl
    float cA = max(dot(wi,refl),0.0);
    float pdfS = (ex+1.0)/(2.0*PI)*pow(cA,ex);
    float pdfD = max(dot(wi,nf),0.0)*INV_PI;
    pdfB = pS*pdfS + (1.0-pS)*pdfD;
```
And with the mixture sampling (choose the lobe with prob pS), the sampling pdf is the same mixture. ✓

Then:
```glsl
    float cosT = dot(wi,nf);
    if (cosT <= 0.0 || pdfB < 1e-7) break;
    vec3 f = kd*INV_PI + ks*((ex+2.0)/(2.0*PI))*pow(cA,ex);
    thr *= f*cosT/pdfB;
    prevDelta = false;
    prevPdf = pdfB;
    prevPos = h.p;
    ro = h.p + nf*1e-4;
    rd = wi;
```
Hmm, but I need to handle the case where the mixture sampling picks the diffuse lobe but the specular lobe's pdf matters... it's all in pdfB. ✓

Also, the specular sample could go below the surface (if the lobe is wide and near grazing). Check cosT > 0 and reject/break. Fine (a small energy loss).

For `specDir`, I need the reflection direction and a frame.

Also I should clamp the exponent: ex = min(ex, 5000).

The mix for ks: for dielectric specular, ks = vec3(1.0)*spec; for metal, ks = alb*spec. Using `mix(vec3(1.0), m.alb, m.metal)` — for the metal 1.0 → alb ✓, for dielectrics metal=0 → vec3(1.0) ✓.

Now `lum()` = dot(c, vec3(0.2126,0.7152,0.0722)).

sampleSun and lightPdf:

```glsl
float lightOmega(vec3 p){
  float d = length(uSunC - p);
  float s = clamp(uSunR/d, 0.0, 0.999);
  return 2.0*PI*(1.0-sqrt(1.0-s*s));
}
float lightPdf(vec3 p){ return 1.0/lightOmega(p); }
vec3 sampleSun(vec3 p, out vec3 wi, out float pdf){
  vec3 d = uSunC - p;
  float dist = length(d);
  float s = clamp(uSunR/dist,0.0,0.9999);
  float cosA = sqrt(1.0-s*s);
  float omega = 2.0*PI*(1.0-cosA);
  pdf = 1.0/omega;
  vec3 w = d/dist;
  vec3 t = normalize(cross(abs(w.y)<0.9?vec3(0,1,0):vec3(1,0,0), w));
  vec3 b = cross(w,t);
  float u1=rnd(), u2=rnd();
  float ct = 1.0 - u1*(1.0-cosA);
  float st = sqrt(max(0.0,1.0-ct*ct));
  float ph = 2.0*PI*u2;
  wi = normalize(t*(st*cos(ph)) + b*(st*sin(ph)) + w*ct);
  return vec3(1.0,0.93,0.80)*uSunLe;
}
```
Note: `uSunLe` is the emission, and the material emis uses the same. ✓

Then the shadow ray: `occluded(h.p + nf*1e-4, wi, 1e30)`. Actually we should limit the distance to the sun's near distance, but 1e30 works.

Hmm, one issue: the shadow ray will hit the sun sphere? No — occluded() doesn't test the sun. ✓

Now the sky:
```glsl
vec3 skyColor(vec3 rd){
  float y = rd.y;
  vec3 horizon = vec3(0.85,0.80,0.72)*1.1;
  vec3 zenith = vec3(0.30,0.48,0.95)*1.9;
  vec3 c = mix(horizon, zenith, smoothstep(0.0,0.6,y));
  c = mix(vec3(0.28,0.25,0.22)*0.6, c, smoothstep(-0.15,0.02,y)); // ground
  vec3 sd = normalize(uSunC - vec3(4.0,1.65,0.0));
  float g = max(dot(rd,sd),0.0);
  c += vec3(1.0,0.85,0.65)*pow(g,220.0)*8.0;
  return c;
}
```
Hmm, the sun glow should be much larger/brighter to mimic the sun. But the sun sphere itself is a huge emitter and appears in the sky, so the glow is minor.

Now let's ensure the sky isn't too bright when viewed through the window: peak ~2.0 radiance with the exposure... The window view will be near white with a blue tint. Fine — realistic for a window.

Hmm, but there's a subtlety: the sky contributes to the room's illumination by BSDF rays. With the sky at ~2.0 and the window's solid angle from the room center ~0.1 sr, the irradiance ~2*0.1 = 0.2. Small compared to the sun's 8. But since the sun only enters at certain angles, the sky adds a nice ambient blue. Good.

Now the camera and animation in JS.

Let's also verify that the sun sphere is never inside the room: uSunC = (4,1.65,0) + dir*25, and dir.x = cos(el)cos(az) > 0, so uSunC.x >= 4 + 25*cos(el)*cos(az) with cos(el)>=0.75*... at el=50°, cos=0.64; at az=0.75, cos(az)=0.73 → dir.x = 0.47 → x = 4+11.75 = 15.75. Fine, far away.

Also, is the sun sphere occluded by the wall for rays from deep inside the room? Yes, only the window lets light through. That's the point.

Now, one thing I should double check: the window's outer side. The sun sphere is at 25m; rays through the window hit it. The rays that hit the sun from the room must pass through the window opening. ✓

Now, potential problem: the sun is so far that the "light pool" is a projection of the window. But when the sun is at a high elevation (50°), the light pool on the floor: for the window at y 0.9-2.4, x=4, Δx = y/tan(el). At el=50°: tan=1.19 → for y=0.9, Δx=0.76 (x=3.24); for y=2.4, Δx=2.02 (x=1.98). So the pool spans x∈[1.98,3.24]. ✓

At el=32°: tan=0.62 → y=0.9 → Δx=1.44 (x=2.56); y=2.4 → Δx=3.85 (x=0.15). So the pool spans x∈[0.15, 2.56]. Bigger and further into the room, hitting the sofa? The sofa is at x∈[-1.75,-0.05] — close. Nice.

The z extent: with az, the pool shifts and skews.

Good, this creates a nice moving light pool.

Now, the initial view at t=0: the camera at (-1.45,1.45,0) looking toward +x. The light pool at t=0: az = 0, el = 0.72+0.16*sin(0) = 0.72 rad = 41.2°. The pool is at x∈[1.4,2.9] roughly, z∈[-1.2,1.2] (the window's z extent, since az=0 → the pool is directly in front of the window). The table is at x∈[1.05,2.15], z∈[-0.42,0.42] — right in the pool! So the table and the glass get sunlit at t=0, casting shadows on the floor. 

The camera at (-1.45,1.45,0) looking at (1.1,1.05,0): the table is at 2.5-3.6m away in the center of the view, the window behind it at 5.4m. Good composition. The floor pool in front.

Now let's think about the exposure: the sunlit floor at ~1.8 radiance → ACES ~0.85 → gamma → 0.93 → bright. The shadowed floor at maybe 0.15 → 0.4. Good contrast.

Let me set uExposure = 1.0.

Alright, one more consideration: the mirror at x=-3.96 is quite far from the action. When the camera is at (1.45,1.45,0) looking toward -x at t=15s, the mirror is ~5.4m away and the window is behind the camera → the mirror reflects the room including the window and the light pool. Nice.

Let's write the final code now.

One more thought on the EMA blend: I need to make sure the alpha is applied. gl.blendColor(0,0,0,alpha) and blendFunc(CONSTANT_ALPHA, ONE_MINUS_CONSTANT_ALPHA). ✓

And the FBO must be cleared/reset when the camera resets (never) or on resize. On resize, I'll recreate the FBO and set the "reset" flag for one frame.

I'll set alpha = 0.5 normally, and 1.0 when resetting.

Hmm, actually, thinking about it more: the ghosting might be objectionable when the camera moves. Let me use alpha = 0.6 (a shorter tail, ~2.5 frames effective). The noise reduction is modest. Or... let's use alpha = 0.5.

Hmm, let me think about whether the ghosting is really visible. Actually, with a moving camera, the EMA of consecutive frames creates a smeared image, which reads as motion blur. At 60fps and slow motion, the smear is ~5-15px. It looks like a slightly soft/motion-blurred image. Acceptable, even "cinematic".

I'll go with 0.5.

Actually — hmm, one risk: the accumulated image never fully refreshes, so a bright flash (e.g., the sun sweeping over a surface) would linger. It fades exponentially with a half-life of 1 frame. Fine.

Now, the frame counter and the sample counter: I'll accumulate `totalSamples += spp` and display.

Let's also cap dt for the time to avoid jumps on tab switch. Use performance.now-based time but... if the tab is inactive, rAF stops; on resume, the time jumps. That's fine (the camera jumps). Acceptable. Or I could accumulate my own time with a clamp. Let's use `t += Math.min(dt, 0.05)`.

Now let me write everything out.

Actually one more thing about the light: the sun sphere is emissive and it's a big sphere in the scene. When the camera looks through the window at the sky, we might see it, and it'll be blown out white. Good.

But there's a subtle issue: BSDF rays that hit the sun sphere add `m.emis * MIS weight`. For a diffuse surface, the MIS weight w = prevPdf/(prevPdf+pdfL). Since pdfL is tiny (1/0.0245 = 41) and prevPdf for a cosine sample ~ 1/π = 0.3, w = 0.3/(0.3+41) = 0.007. So the BSDF contribution to the sun is negligible — correct, because NEE handles it. ✓

And NEE gets w = pdfL/(pdfL+pdfB) = 41/(41+0.3) = 0.993, so it's nearly the full contribution. ✓ Good.

Now the light's contribution: f*cos*Le/pdfL*w = f*cos*Le*Ω*w. With Le=700, Ω = 0.0245 → Le*Ω = 17.2 (the "irradiance-like" term), times f*cos (~0.1 for a diffuse floor with albedo 0.4: f*cos = 0.4/π*0.7 = 0.089) → 1.53. Times w ~1 → 1.5. ✓ As computed before.

Good, so uSunLe = 700.

Hmm, but this is the light at the sun's surface radiance. Fine, it's just a number.

Now what's the total light hitting the room? The sun illuminates the window aperture; the light entering is the collimated beam through the aperture. The irradiance on a floor patch in the pool ≈ 700*0.0245*cos(50°)... ≈ 11. Then the reflected radiance ~ 11*0.4/π = 1.4.

Fine.

Let's write the code.

Also, I need to double check `lightPdf(prevPos)` — prevPos is the previous shading point. But when the BSDF ray hits the sun, the "previous point" is the last shading point. ✓ But if the ray came from the camera directly (prevDelta = true), we skip the pdf. ✓

Edge case: after a delta bounce (mirror/glass), prevDelta = true so the MIS weight is 1. ✓

Now, the code for the camera in JS:

```js
const t = time;
const a = Math.PI + t*0.21;
const r = 1.45 + 0.28*Math.sin(t*0.13);
const camPos = [Math.cos(a)*r, 1.45 + 0.22*Math.sin(t*0.17), Math.sin(a)*r];
const b = a + Math.PI;
const tr = 1.0 + 0.55*Math.sin(t*0.09);
const target = [Math.cos(b)*tr, 1.0 + 0.35*Math.sin(t*0.11), Math.sin(b)*tr];
```

Hmm, at t=0: a=π, camPos=(-1.45, 1.45, 0). Target: b=2π, tr=1.0 → (1.0, 1.0, 0). Direction = (2.45, -0.45, 0) normalized. Looking slightly downward. FOV 48°, so the window (at x=4, y 0.9-2.4) is at 5.45m — spans 1.5/5.45 = 15° vertically, within the 48° FOV. ✓

Now let's also make sure the camera doesn't yaw too wildly. The rate: d(angle)/dt = 0.21 rad/s = 12°/s. That's a slow pan. ✓ And the camera's position moves at r*0.21 = 0.3 m/s. Slow. ✓

Total per frame at 60fps: 0.2° of rotation → at 4m, that's 1.4cm — about 2-3 px. Good, the EMA smear is small. 

Now let's write the HTML.

For the uniform locations, I'll fetch them all.

Let me write the JS:

```js
const canvas = document.getElementById('c');
const gl = canvas.getContext('webgl2', {antialias:false, alpha:false, depth:false, stencil:false});
if (!gl) { document.body.innerHTML = '<h2 style="color:#fff;font-family:sans-serif">WebGL2 required</h2>'; throw 0; }
const extCBF = gl.getExtension('EXT_color_buffer_float');
const hasFloat = !!extCBF;

const vsSrc = `#version 300 es
void main(){
  vec2 p = vec2(float((gl_VertexID<<1)&2), float(gl_VertexID&2));
  gl_Position = vec4(p*2.0-1.0, 0.0, 1.0);
}`;
```
Hmm, gl_VertexID is an int; `(gl_VertexID<<1)&2` → for 0:0, 1:2&2=2, 2:4&2=0. And `gl_VertexID&2` → 0,0,2. So p = (0,0),(2,0),(0,2). Then p*2-1 = (-1,-1),(3,-1),(-1,3). ✓

Compile shaders with error checking (console).

Programs: ptProgram (vs + fs), blitProgram (vs + blit fs).

Full-screen triangle: 3 vertices, no VAO needed? In WebGL2, a VAO is required? Actually WebGL2 has a default VAO (null), and drawing with no attributes enabled is fine as long as the program doesn't use attributes. gl.drawArrays(gl.TRIANGLES, 0, 3) with no enabled attribute arrays — should work in WebGL2 (the default VAO exists). Yes, WebGL2 allows drawing without any attributes enabled. Hmm, some implementations may complain if no VAO is bound... The default VAO is bound at init. It should work.

Let me create and bind a VAO anyway for safety.

Now the render target:

```js
let rtW=0, rtH=0, rtTex=null, rtFbo=null;
function makeRT(w,h){
  if (rtTex) { gl.deleteTexture(rtTex); gl.deleteFramebuffer(rtFbo); }
  rtW=w; rtH=h;
  rtTex = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, rtTex);
  const internal = hasFloat ? gl.RGBA16F : gl.RGBA8;
  const type = hasFloat ? gl.HALF_FLOAT : gl.UNSIGNED_BYTE;
  gl.texImage2D(gl.TEXTURE_2D, 0, internal, w, h, 0, gl.RGBA, type, null);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  rtFbo = gl.createFramebuffer();
  gl.bindFramebuffer(gl.FRAMEBUFFER, rtFbo);
  gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, rtTex, 0);
  if (gl.checkFramebufferStatus(gl.FRAMEBUFFER) !== gl.FRAMEBUFFER_COMPLETE) { console.warn('FBO incomplete'); }
  gl.bindFramebuffer(gl.FRAMEBUFFER, null);
}
```

Note: for RGBA8 the accumulation would clamp; with EMA it's not terrible but let's prefer float.

Main loop with timing.

Alright, writing the full shader now. Let me be careful with GLSL syntax.

One concern: `const vec4 BC[21] = vec4[21](...)` — the array size must be a constant expression. Using the literal 21 is fine.

Let me write these out.

```glsl
const vec4 BC[21] = vec4[21](
  vec4( 0.00,-0.05, 0.00, 0.0),  // 0 floor
  vec4( 0.00, 3.05, 0.00, 0.0),  // 1 ceiling
  vec4(-4.05, 1.50, 0.00, 0.0),  // 2 wall -x
  vec4( 0.00, 1.50,-4.05, 0.0),  // 3 wall -z
  vec4( 0.00, 1.50, 4.05, 0.0),  // 4 wall +z
  vec4( 4.05, 0.45, 0.00, 0.0),  // 5 win below
  vec4( 4.05, 2.70, 0.00, 0.0),  // 6 win above
  vec4( 4.05, 1.50,-2.70, 0.0),  // 7 win left
  vec4( 4.05, 1.50, 2.70, 0.0),  // 8 win right
  vec4(-0.90, 0.15,-3.00, 0.0),  // 9 sofa base
  vec4(-0.90, 0.42,-3.00, 0.0),  // 10 cushion
  vec4(-0.90, 0.75,-3.40, 0.0),  // 11 back
  vec4(-1.85, 0.45,-3.00, 0.0),  // 12 arm L
  vec4( 0.05, 0.45,-3.00, 0.0),  // 13 arm R
  vec4( 1.60, 0.72, 0.00, 0.0),  // 14 table
  vec4( 1.15, 0.34,-0.32, 0.0),  // 15
  vec4( 2.05, 0.34,-0.32, 0.0),  // 16
  vec4( 1.15, 0.34, 0.32, 0.0),  // 17
  vec4( 2.05, 0.34, 0.32, 0.0),  // 18
  vec4(-3.96, 1.60, 0.00, 0.0),  // 19 mirror
  vec4( 1.95, 0.88,-0.10, 0.0)   // 20 lamp stand
);
```

BH with the mat in .w:

```glsl
const vec4 BH[21] = vec4[21](
  vec4(4.20,0.05,4.20, 0.0),
  vec4(4.20,0.05,4.20, 3.0),
  vec4(0.05,1.60,4.20, 2.0),
  vec4(4.20,1.60,0.05, 1.0),
  vec4(4.20,1.60,0.05, 2.0),
  vec4(0.05,0.45,4.20, 2.0),
  vec4(0.05,0.30,4.20, 2.0),
  vec4(0.05,1.60,1.50, 2.0),
  vec4(0.05,1.60,1.50, 2.0),
  vec4(0.85,0.15,0.50, 4.0),
  vec4(0.80,0.12,0.48, 4.0),
  vec4(0.85,0.45,0.12, 4.0),
  vec4(0.12,0.45,0.55, 4.0),
  vec4(0.12,0.45,0.55, 4.0),
  vec4(0.55,0.04,0.42, 5.0),
  vec4(0.03,0.34,0.03, 5.0),
  vec4(0.03,0.34,0.03, 5.0),
  vec4(0.03,0.34,0.03, 5.0),
  vec4(0.03,0.34,0.03, 5.0),
  vec4(0.02,0.70,1.00, 7.0),
  vec4(0.02,0.12,0.02, 6.0)
);
```

Wait, the picture on the +z wall — I decided to skip it. Let me reconsider... I'll add it for visual interest. That would make NBOX=23. Hmm, two more boxes: the frame and the canvas. Let me just add one box: a "picture" = a box with a wood frame material, 0.6x0.5x0.03 at (0,1.75,3.96). And the canvas... just make it a single box with the material of the warm wall (mat 1)? That looks like a painting. Meh.

Alternatively, put a tall bookshelf on the +z wall. One box: (0, 0.9, 3.8), half (0.8, 0.9, 0.25) with mat 5 (wood). That's a sideboard/cabinet. It'd break up the blank wall. Let's do that: box 21 = cabinet, mat 5. And add a small vase? No.

Hmm, but then the camera at the +z side (t=22.4s) is at (0,·,1.45) and the cabinet is at z 3.55-4.05 — fine.

Let's add one box: cabinet at (0.0, 0.45, 3.85) half (0.9, 0.45, 0.2) mat 5. → x∈[-0.9,0.9], y∈[0,1.8]... no: half y 0.45 → y∈[0,0.9]. Good, a low sideboard.

NBOX = 22.

Wait, but that could block the camera's view of the +z wall — that's fine, it adds interest.

Also maybe add a mirror-like picture frame... no, enough.

Let me finalize NBOX=22 with the cabinet as index 21.

Also, is the cabinet within the room? z from 3.65 to 4.05 — hmm, the wall's inner face is at z=4.0, so the cabinet would poke into the wall by 0.05. Let's set c z=3.78, half 0.2 → z∈[3.58,3.98]. ✓

OK.

Now let me write out the final shader code.

Also, I want to double check `refract` in GLSL ES 3.00 — yes, `genType refract(genType I, genType N, float eta)` is available.

Let me write the trace function carefully.

```glsl
vec3 tracePath(vec3 ro, vec3 rd){
  vec3 col = vec3(0.0);
  vec3 thr = vec3(1.0);
  bool  prevDelta = true;
  float prevPdf = 1.0;
  vec3  prevPos = ro;

  for (int i=0;i<MAXB;i++){
    Hit h = traceScene(ro, rd);
    if (!h.hit){ col += thr * skyColor(rd); break; }
    Mat m = getMat(h.mat);
    if (m.emis.r > 0.0){
      float w = 1.0;
      if (!prevDelta){
        float pl = lightPdf(prevPos);
        w = prevPdf / (prevPdf + pl);
      }
      col += thr * m.emis * w;
      break;
    }
    vec3 n  = h.n;
    vec3 wo = -rd;
    vec3 nf = (dot(wo,n) > 0.0) ? n : -n;

    if (m.trans > 0.5){ ... continue; }
    if (m.rough < 0.05 && m.spec > 0.5){ ... continue; }

    // ... NEE + BSDF
  }
  return col;
}
```

Careful with `continue` inside a for loop in GLSL — allowed. ✓

Now, MAXB=5 and the glass needs 2 bounces to exit. OK.

Let's write the glass block:

```glsl
    if (m.trans > 0.5){
      vec3 gn = h.n;
      bool entering = dot(rd, gn) < 0.0;
      float eta = entering ? (1.0/IOR) : IOR;
      vec3 nn = entering ? gn : -gn;
      float cosi = clamp(dot(wo, nn), 0.0, 1.0);
      float sin2t = eta*eta*(1.0 - cosi*cosi);
      vec3 nd;
      if (sin2t >= 1.0){
        nd = reflect(rd, nn);
      } else {
        float r0 = (1.0-IOR)/(1.0+IOR); r0 *= r0;
        float F = r0 + (1.0-r0)*pow(1.0-cosi, 5.0);
        nd = (rnd() < F) ? reflect(rd, nn) : refract(rd, nn, eta);
        if (dot(nd,nd) < 1e-8) nd = reflect(rd, nn);
      }
      thr *= m.alb;
      prevDelta = true;
      ro = h.p + nd * 1e-4;
      rd = normalize(nd);
      continue;
    }
```

Hmm, `refract(rd, nn, eta)` where eta = 1/1.5 for entering. GLSL: eta is the ratio of indices of refraction (i.e., eta = n_incident/n_transmitted). For entering glass from air: 1.0/1.5 ✓. For exiting: 1.5/1.0 = 1.5 ✓.

The refract result: `k = 1 - eta²(1 - dot(N,I)²)`; if k < 0 → returns 0. Since we checked sin2t < 1, k > 0. ✓

Now the mirror block:
```glsl
    if (m.rough < 0.05 && m.spec > 0.5){
      vec3 nd = reflect(rd, nf);
      thr *= m.alb * m.spec;  // hmm
      ...
    }
```
For the mirror: alb=0.97, spec=1, metal=1 → tint = alb. For a dielectric delta specular with spec=1... not used. Let's just use `thr *= mix(vec3(1.0), m.alb, m.metal) * m.spec`.

For the mirror: mix(1, 0.97, 1) = 0.97, *1 = 0.97 ✓.

Now the glossy/diffuse block:

```glsl
    vec3 kd = m.alb * (1.0 - m.spec);
    vec3 ks = mix(vec3(1.0), m.alb, m.metal) * m.spec;
    float ex = clamp(2.0/(m.rough*m.rough) - 2.0, 1.0, 4000.0);
    float pS = lum(ks) / max(1e-3, lum(ks) + lum(kd));
    vec3 rdir = reflect(rd, nf);

    // NEE
    {
      vec3 wi; float pdfL;
      vec3 Le = sampleSun(h.p, wi, pdfL);
      float cosT = dot(wi, nf);
      if (cosT > 0.0){
        if (!occluded(h.p + nf*1e-3, wi, 1e9)){
          float cA = max(dot(wi, rdir), 0.0);
          vec3 f = kd*INV_PI + ks*((ex+2.0)/(2.0*PI))*pow(cA, ex);
          float pdfS = ((ex+1.0)/(2.0*PI))*pow(cA, ex);
          float pdfD = cosT*INV_PI;
          float pdfB = pS*pdfS + (1.0-pS)*pdfD;
          float w = pdfL/(pdfL + pdfB);
          col += thr * f * cosT * Le * (w / pdfL);
        }
      }
    }
```
Note: `Le` includes uSunLe. And pdfL = 1/Ω.

Then:
```glsl
    vec3 wi; float pdfB;
    float u = rnd();
    if (u < pS){ wi = sampleSpec(rdir, ex); }
    else { wi = sampleCos(nf); }
    float cosT = dot(wi, nf);
    if (cosT <= 0.0) break;
    float cA = max(dot(wi, rdir), 0.0);
    float pdfS = ((ex+1.0)/(2.0*PI))*pow(cA, ex);
    float pdfD = cosT*INV_PI;
    pdfB = pS*pdfS + (1.0-pS)*pdfD;
    if (pdfB < 1e-6) break;
    vec3 f = kd*INV_PI + ks*((ex+2.0)/(2.0*PI))*pow(cA, ex);
    thr *= f*cosT/pdfB;
    prevDelta = false;
    prevPdf = pdfB;
    prevPos = h.p;
    ro = h.p + nf*1e-3;
    rd = wi;
```

Hmm, `nf*1e-3` for the offset — for the floor, a 1mm offset is fine. But for a thin box like the mirror (0.04 thick), a 1mm offset is fine. OK, but what about the light leaking through thin geometry? The mirror is 4cm thick, the offset is 1mm — fine.

Hmm, but for the emissive surface (the sun sphere), no offset issues since we terminate.

Let's use 5e-4 offsets.

Alright, and the russian roulette: without it, at 5 bounces the path just ends. Dark corners may be slightly darker. Let's not worry.

Now, `sampleCos(n)`:
```glsl
vec3 sampleCos(vec3 n){
  vec3 t = normalize(cross(abs(n.y)<0.9?vec3(0,1,0):vec3(1,0,0), n));
  vec3 b = cross(n, t);
  float u1=rnd(), u2=rnd();
  float r = sqrt(u1);
  float ph = 2.0*PI*u2;
  return normalize(t*(r*cos(ph)) + b*(r*sin(ph)) + n*sqrt(max(0.0,1.0-u1)));
}
```

`sampleSpec(refdir, ex)`:
```glsl
vec3 sampleSpec(vec3 r, float ex){
  vec3 t = normalize(cross(abs(r.y)<0.9?vec3(0,1,0):vec3(1,0,0), r));
  vec3 b = cross(r, t);
  float u1=rnd(), u2=rnd();
  float ct = pow(u1, 1.0/(ex+1.0));
  float st = sqrt(max(0.0,1.0-ct*ct));
  float ph = 2.0*PI*u2;
  return normalize(t*(st*cos(ph)) + b*(st*sin(ph)) + r*ct);
}
```

Good.

Now the main:

```glsl
void main(){
  rngState = uint(gl_FragCoord.x) * 1973u + uint(gl_FragCoord.y) * 9277u + uFrame * 26699u;
  rngState = pcg(); // warm up? no
  ...
  vec2 res = uRes;
  vec3 acc = vec3(0.0);
  vec3 rightU = normalize(uCamR);
  vec3 upU = normalize(uCamU);
  for (int s=0;s<8;s++){
    if (s >= uSpp) break;
    vec2 jit = vec2(rnd(), rnd());
    vec2 uv = (gl_FragCoord.xy + jit - 0.5*res) / (0.5*res.y);
    vec3 dir = normalize(uCamF + uCamR*uv.x + uCamU*uv.y);
    vec2 ap = apertureSample();   // disk of radius 1
    ap *= uAperture;
    vec3 ro = uCamPos + rightU*ap.x + upU*ap.y;
    vec3 focusP = uCamPos + dir*uFocus;
    vec3 rd = normalize(focusP - ro);
    acc += tracePath(ro, rd);
  }
  acc /= float(uSpp);
  fragColor = vec4(acc, 1.0);
}
```
The loop with a dynamic bound: `for (int s=0;s<uSpp;s++)` — GLSL ES 3.0 allows non-constant loop bounds? In GLSL ES 3.00, loops with non-constant bounds are allowed (unlike ES 1.00). Yes, ES 3.00 allows dynamic loops. But to be safe with drivers, I'll use a constant bound with a break.

Aperture sampling: a disk of radius 1: 
```glsl
vec2 apertureSample(){
  float r = sqrt(rnd());
  float a = 2.0*PI*rnd();
  return vec2(r*cos(a), r*sin(a));
}
```

Now, the uFocus: set it to the distance from the camera to the target.

Let me now write the JS animation.

```js
function updateCamera(t){
  const a = Math.PI + t*0.21;
  const r = 1.45 + 0.28*Math.sin(t*0.13);
  const px = Math.cos(a)*r, pz = Math.sin(a)*r;
  const py = 1.45 + 0.22*Math.sin(t*0.17);
  const b = a + Math.PI;
  const tr = 1.0 + 0.55*Math.sin(t*0.09);
  const tx = Math.cos(b)*tr, tz = Math.sin(b)*tr;
  const ty = 1.0 + 0.35*Math.sin(t*0.11);
  ...
}
```
Compute fwd = normalize(target-pos); right = normalize(cross(fwd, worldUp)); up = cross(right, fwd);
Then camR = right * tanHalf * aspect, camU = up * tanHalf, camF = fwd. And focus = |target - pos|.

Wait, `uCamR` should be `right * tan(fov/2) * aspect`, and uv.x ranges over [-aspect, aspect]... Let me redo: uv = (frag - 0.5*res)/(0.5*res.y). So uv.x ∈ [-aspect, aspect] where aspect = W/H, and uv.y ∈ [-1,1]. Then rd = normalize(F + R*uv.x + U*uv.y) with R = right*tanHalf and U = up*tanHalf. Then at uv=(aspect,0), the half-angle = atan(tanHalf*aspect) horizontally ✓.

Good.

Sun: 
```js
const az = 0.75*Math.sin(t*0.075);
const el = 0.72 + 0.16*Math.sin(t*0.053);
const dirx = Math.cos(el)*Math.cos(az), diry = Math.sin(el), dirz = Math.cos(el)*Math.sin(az);
sunC = [4 + dirx*25, 1.65 + diry*25, 0 + dirz*25];
```

Hmm wait, the window center is (4, 1.65, 0) and the wall is at x=4. The sun's direction from the window: should it be based at the window center? The vector from the window center to the sun = dir*25. So sunC = (4,1.65,0) + dir*25. ✓

At el=0.72, cos=0.752, sin=0.659: dir = (0.752*cos(az), 0.659, 0.752*sin(az)). At az=0: (0.752,0.659,0). sunC = (4+18.8, 1.65+16.5, 0) = (22.8, 18.15, 0). ✓

The sun's angular radius from a floor point at ~(2,0,0): distance = sqrt(20.8² + 18.15²) = 27.6 → 2.2/27.6 = 0.08 rad = 4.6°. ✓

Now the label. Update every ~10 frames.

Let's write the final code. I'll be careful with the shader string escaping (use backticks; there are no `${}` in the GLSL — careful, GLSL doesn't have `${`, so it's fine).

Actually, hmm: template literals with `${` — I must avoid `$` followed by `{` in the shader. No such thing in GLSL. ✓

Let me write everything now.

One last check on the shadow ray max distance in `occluded`: I pass 1e9, and the sun sphere isn't tested, so any hit means occlusion. ✓

And in `traceScene`, the sun sphere test uses `hitSun`.

Also, the epsilon for the shadow ray origin: `h.p + nf*1e-3` — wait, for the floor the normal is (0,1,0) and the point is at y=0, so the offset origin is at y=0.001. The floor box top is at y=0. ✓ Fine.

But careful with the wall boxes' interior faces: e.g., the -x wall's inner face is at x=-4.0, and the normal points +x. The offset origin is at x=-3.999. ✓

Now, a potential issue: the shadow ray from the floor offset by 1e-3 upward — the shadow ray goes up toward the sun. It won't hit the floor again. ✓

And for a shadow ray from a wall going up, could it hit the wall's own box? The origin is offset along the normal by 1e-3, so it's outside the box. ✓

Now writing the final code.

Also: after the loop, if the path didn't terminate (bounces exhausted), we just return the accumulated color. Fine.

Also, I should add a small firefly clamp: `col = min(col, vec3(50.0))`? With the EMA, a firefly persists. Let's clamp per-pixel per-frame: `acc = min(acc, vec3(30.0))` before output. Hmm, since the sun is bright (Le=700) and a specular reflection of the sun through the glass could produce a huge value... Let's clamp the sample to 20 and 100. I'll clamp the final acc to ~25. Actually, clamping the radiance at 25 with a tone mapper that saturates at ~4 is fine (25 → white). Let's clamp at 40.

Let me write it.

Also, for the RGBA8 fallback, values > 1 clip. With exposure 1.0, the linear values before tonemapping are ~0-4 typically, so clipping at 1 would wash out... Actually, we store the *linear HDR* value in the accumulation texture; with RGBA8 it clips to 1.0, losing the highlight range. To mitigate, I'd apply the tonemap before storing if using RGBA8. Let's just handle it: if !hasFloat, apply the tonemap in the PT shader and use a passthrough blit. Too complex. Most WebGL2 devices support EXT_color_buffer_float (it's widely supported). I'll just use RGBA16F and hope. If the extension is missing, I'll fall back to RGBA8 and accept the clipped look (still works).

Actually, to make the fallback less bad, when using RGBA8 I can store the tonemapped color... but then the EMA blending in display space. It's fine, we accept it. Actually, let me just do the simplest: use RGBA8 and apply the tonemap in the PT shader when there's no float support, and make the blit pass a passthrough (the blit shader can check a uniform `uTonemap`). Let me add a uniform `uLinear` to the blit shader: if 0, skip the tonemap. Easy enough.

Hmm, that's extra complexity for an edge case. Let me just do it — a few lines.

Actually, simpler: in the blit shader, `c = texel; if (uTone > 0.5) { tonemap }`. And the PT shader: `if (!float) acc = tonemap(acc)`. I'd need the tonemap in both shaders. Meh.

Let me just skip the fallback and assume EXT_color_buffer_float. If it's missing, I'll use RGBA8 anyway and the image will just be clipped/lower quality. No extra code.

OK writing now.

Actually hold on, I realize there might be an issue with blending to an RGBA16F target without EXT_color_buffer_float — the FBO would be incomplete and nothing renders. Let me at least test the FBO completeness and fall back to rendering directly to the screen without accumulation if it fails. Hmm. Let me just check `gl.checkFramebufferStatus` and if it's not complete, recreate with RGBA8/UNSIGNED_BYTE. That's a small amount of code in makeRT. The clipped-HDR issue remains but at least it works.

OK. Writing.

Let me write the whole file.

```js
const renderScale = 0.62;
function resize(){
  const w = Math.max(320, window.innerWidth|0);
  const h = Math.max(240, window.innerHeight|0);
  canvas.width = w; canvas.height = h;
  const maxPix = 520000;
  let s = Math.min(0.7, Math.sqrt(maxPix/(w*h)));
  const rw = Math.max(200, Math.round(w*s)), rh = Math.max(150, Math.round(h*s));
  makeRT(rw, rh);
  resetAccum = true;
}
```
Hmm, canvas.width = w means the canvas is at CSS pixel resolution. With dpr=2 the image would be slightly soft on retina. That's fine (and faster).

Actually, using the full CSS resolution for the canvas (the blit pass) is cheap. ✓

The aspect ratio used in the shader should be rtW/rtH, which equals w/h approximately (rounding aside). ✓

Let me write.

Final detail: the `uRes` uniform = (rtW, rtH).

And the blit: texture(uTex, gl_FragCoord.xy/uScreenRes).

Let's write it all out now.

Let me write the blit fragment shader:

```glsl
#version 300 es
precision highp float;
uniform sampler2D uTex;
uniform vec2 uScreen;
uniform float uExposure;
out vec4 o;
void main(){
  vec2 uv = gl_FragCoord.xy / uScreen;
  vec3 c = texture(uTex, uv).rgb;
  c *= uExposure;
  c = (c*(2.51*c+0.03))/(c*(2.43*c+0.59)+0.14);
  c = pow(clamp(c,0.0,1.0), vec3(0.4545));
  o = vec4(c,1.0);
}
```

ACES filmic approximation (Narkowicz). For c=1: (1*2.54)/(1*3.02+0.14) = 2.54/3.16 = 0.80. Slightly dark, fine.

Now, writing the final answer. Let me assemble.

One more consideration on performance: the `for` loop over NBOX with function calls — the compiler should handle it. 22 boxes + 2 spheres + 1 sun per traceScene, 5 bounces + 1 NEE shadow ray per bounce → ~6 scene traces per path × 2 spp = 12 scene traces per pixel. 12 × 25 objects = 300 intersections per pixel. At 900×500 = 450k pixels → 135M intersection tests per frame. That's a lot for 60fps but GPUs are fast. Might be ~30fps on mid hardware. Acceptable.

Let's reduce MAXB to 4 to be safer. Hmm, with 4 bounces: camera → floor(diffuse) → wall(diffuse) → floor → terminates. The color bleeding needs 2-3 bounces. OK, 4 is enough. Let's use 5 for slightly better GI but... I'll use 4.

Actually with glass we need extra bounces. The glass at 2 bounces + 2 more = 4. OK, MAXB=5, let's just do 5. Fine.

Hmm, let me compromise: MAXB=4, and rely on the fact that most paths terminate early anyway (they hit the emissive sun or escape). Actually no, paths in a closed room rarely terminate early...

Let's do MAXB=4.

Hmm, but then: camera ray hits the mirror (1 delta bounce), then hits the floor (2), then a wall (3), then the sun via NEE at bounce 4. Fine.

OK, MAXB=4. Let me count: the loop runs 4 times, each doing NEE + a BSDF bounce. So 4 diffuse bounces max. Good enough.

Writing now for real.

Let me handle `uSpp`: I'll set it to 2.

Hmm, one concern: with SPP=2 and a dynamic loop, the noise per frame is high. With the EMA at 0.5, effective ~3-4 samples. It'll be noticeably noisy but "real-time path traced" noisy, which is expected and looks good in motion.

Let me use SPP=3 if the resolution is low... just fixed at 2. Hmm. Let me make it 2 and the EMA 0.5.

OK. Writing.

Also note: `uFrame` as a uint uniform — I'll use `gl.uniform1ui`. WebGL2 supports it. Or just use a float uniform and cast. Let me use `uniform uint uFrame;` and `gl.uniform1ui(loc, frame & 0xffffffff)`. Fine.

Let me write out the final file.

Actually, for the RNG seeding: `rngState = uint(gl_FragCoord.x)*1973u + uint(gl_FragCoord.y)*9277u + uFrame*26699u;` then call pcg() a couple times to decorrelate. Fine.

Let me write everything.

Final check on the label text: I'll show `samples: N · 2 spp/frame · frame K`.

Writing the code now. I'll be meticulous.

One more thing: since the sun sphere is very bright and huge, and it's rendered as an object, when the camera looks out the window and the sun is in view, it'd be a giant white blob. At the elevation ~41°, the window's top is at y=2.4 and the camera at y≈1.5 looking horizontally — the sun at 41° elevation wouldn't be visible unless looking up. The camera's pitch varies: the target y goes from 0.65 to 1.35 while the camera is at 1.23-1.67 → a downward pitch. So we never look up. Good, the sun sphere is never directly visible (only the sky). 

Now writing.

def skyColor: I use uSunC for the glow direction; the glow is centered on the sun. Since we don't look up, it doesn't matter much.

Let me finalize.

Also, I want to double-check `lightPdf(prevPos)` uses the distance from prevPos to the sun center. ✓

Writing the code:

I'll write the whole thing now in one go.

For the label update, I'll use textContent and only update when the value changes (every 15 frames).

Also, add a `#label` styling.

Let me write out the file.