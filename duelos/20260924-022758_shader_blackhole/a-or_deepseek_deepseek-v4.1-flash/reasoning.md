Let me write a WebGL2 black hole shader.

Approach: full-screen quad, fragment shader does ray marching / analytic geodesic bending in Schwarzschild-like metric.

A common approach: for each pixel, compute ray direction from camera, then integrate the photon path in the black hole gravitational field using a simple ODE: d²x/dλ² = -1.5 * h² * x / |x|^5 (the standard "Schwarzschild null geodesic" approximation in units where rs = 1... actually the standard equation for photon in Schwarzschild: d²u/dφ² + u = 3/2 * rs * u², where u = 1/r. In Cartesian, the acceleration form: d²x/dλ² = -1.5 * h² * x_hat / r^4... let me recall.

Known formulation used in many shadertoy black holes: 
```
vec3 pos = camPos;
vec3 dir = rayDir;
float h2 = length(cross(pos, dir))^2;  // conserved angular momentum squared
for steps:
    float r = length(pos);
    vec3 accel = -1.5 * h2 * pos / pow(r, 5.0);
    // integrate
    dir += accel * dt;
    pos += dir * dt;
```
This is with rs = 1 (units where Schwarzschild radius = 1)? Let's check: the equation for null geodesic in Schwarzschild with M, using affine parameter: d²x/dλ² = -3/2 * rs * h² * x / r^5 where h = |x × dx/dλ|. Actually the standard: for the orbit equation u'' + u = 3M u², with rs = 2M, gives u'' + u = (3/2) rs u². In Cartesian, d²x/dλ² = -(3/2) rs h² x / r^5. Yes, that's the known formula. Many implementations use `-1.5 * h2 * pos / pow(r,5)` with rs = 1... Let me just use that with a scale factor for tuning. I'll set units where rs = 1 and use accel = -1.5 * h2 * pos / r^5. Then event horizon at r = 1, photon sphere at 1.5, ISCO at 3.

Rendering: ray march from camera position outward. Camera at distance ~ 12-15 rs. Integrate until r < 1 (captured → black) or r > far (escaped → sample sky with final direction) or step limit.

Accretion disk: in the plane y = 0 (equatorial plane), from r_inner ≈ 2.6 (or 3) to r_outer ≈ 12. When the ray crosses the plane (sign change of y), interpolate the crossing point, check if within disk radii, sample disk color with noise turbulence, accumulate emission with alpha. Allow multiple crossings (front and back of disk), giving the Interstellar look: the far side appears above and below the hole.

Starfield: procedural hash-based stars from the escaped direction.

Photon ring: naturally arises from the lensing; but add a thin bright ring by boosting emission for rays that pass near the photon sphere. Actually the photon ring appears naturally as the lensed image of the disk edge. But we can add subtle glow near r ~ 1.5.

Let's write the shader.

Details:

Camera: orbiting around, at radius R = 14, inclination tilts between say 8° and 20° over time. Actually "slowly orbits and tilts". Use time-based: angle = t*0.08, tilt = 0.15 + 0.12*sin(t*0.05) radians? Let's give tilt ~ 10-20 degrees so we see the disk nearly edge-on-ish, giving the Interstellar look. Interstellar's Gargantua was nearly edge-on. Let's use inclination around 5-15 degrees above the plane.

Camera position: 
```
float camDist = 14.0;
float az = t * 0.1;
float el = 0.18 + 0.10 * sin(t * 0.07); // radians above plane
vec3 camPos = camDist * vec3(cos(el)*cos(az), sin(el), cos(el)*sin(az));
```
Target: origin. Up: vec3(0,1,0).

Build camera basis.

Ray direction: normalize(uv.x * right + uv.y * up + focal * forward).

Marching: adaptive step: dt proportional to r maybe. Use fixed small steps but with step size scaled: dt = clamp(r*0.15, 0.05, ...) Hmm, better: use RK-ish or simple leapfrog with step scaled by r.

A common robust approach: step size = 0.15 * r? Near the hole we need small steps. Let's use dt = 0.08 * r maybe with max steps 300-500. Since it's a fragment shader at full window resolution, 400 steps might be heavy on big screens. Let's cap: use adaptive steps and limit to ~250. Could also render at reduced resolution (e.g., devicePixelRatio capped at 1, or even 0.75 scale) for performance. Let's cap pixel ratio to 1 and maybe render at a slightly lower internal resolution and scale with CSS... but full-window crispness matters for stars. I'll cap DPR at 1.25 or so and use max 300 steps with early exit.

Actually, to be safe on performance, I'll add an internal render scale: canvas width = floor(clientWidth * scale) with scale = min(devicePixelRatio, 1.5). Hmm, most screens are 1-2 DPR. Let's use min(dpr, 1.5) but also cap total pixels ~ 2.2M maybe. Simpler: scale = Math.min(window.devicePixelRatio || 1, 1.5). Fine.

Integration scheme: use velocity Verlet-ish:

```
for (int i = 0; i < MAXSTEPS; i++) {
   float r = length(pos);
   if (r < 1.0) { captured; break; }
   if (r > 60.0) break;  // escaped
   // check disk crossing before stepping
   ...
   float dt = ...;
   vec3 acc = -1.5 * h2 * pos / (r*r*r*r*r);
   dir += acc * dt;
   vec3 newPos = pos + dir * dt;
   ...
}
```

Careful: h2 must be computed from initial pos and dir (conserved). h = length(cross(pos, dir)); but dir isn't unit-speed if we use non-affine steps... With the acceleration formula, |dir| is conserved only if... hmm. Actually in this formulation, dir is dx/dλ and the magnitude |dx/dλ| isn't necessarily 1 for null geodesics in this Cartesian approximation? Let's check: the equation d²x/dλ² = -(3/2) rs h² x/r^5 with h = |x × dx/dλ| conserved. For a null geodesic in Schwarzschild, with the standard Cartesian-ish trick, the speed |dx/dλ| is not conserved in general. But the approximation used in shadertoy (e.g., "Black hole with accretion disk" by... ) keeps |dir| approximately constant when far away. Actually a known result: for this ODE, |dx/dλ|² is conserved? Let's check: d/dλ (|v|²/2) = v·a = -(3/2)h² (v·x)/r^5 = -(3/2)h² (1/2) d(r²)/dλ / r^5. Hmm, not zero in general. So speed changes. That's fine; it's still the correct geodesic shape (up to reparametrization? no — it is the correct orbit equation, since the orbit shape u(φ) matches). Indeed the orbit equation derived: for the ODE a = -1.5 h² x/r^5, one can show that the trajectory shape matches the null geodesic in Schwarzschild with rs = 1 (in the sense that r(φ) satisfies u'' + u = 1.5 u²... let's verify).

Let r = 1/u, and h = r² dφ/dλ = const (angular momentum per unit... yes since acceleration is radial, angular momentum is conserved exactly). Then standard: d²u/dφ² + u = -a_r/(h² u²)... Let's derive: radial acceleration a_r = -1.5 h² / r^4 = -1.5 h² u^4. Then the Binet equation: d²u/dφ² + u = -a_r/(h² u²) = 1.5 h² u^4/(h² u²) = 1.5 u². Yes! Exactly the null geodesic equation with rs=1. 

So the shape is right; the parameterization speed changes but that just affects step sizes. Since h is computed as |x × v| with v = normalized ray direction (|v|=1 initially), h is conserved regardless of speed changes since a is radial. Good.

But careful: h2 = |x×v|² where v = dir. Since dir's magnitude changes, but h stays conserved (angular momentum), fine.

Step size: use dt scaled by r to keep near-hole accuracy. Actually since speed changes, let's just use dt = clamp(0.12 * r, 0.02, 0.6) hmm. Near r=1, dt = 0.12 — might be too big? Photon sphere at 1.5 with r changing fast. Let's use dt = 0.05 + 0.1*(r-1) clamped... Let me use dt = max(0.035, 0.09*r) capped at 0.5. With r=1: dt = 0.09. Hmm.

Better: I recall good implementations use `float dt = 0.15 * r / (1.0 + ...)`. Let's just test mentally: total path length ~ from camera 14 to near hole ~ 14 units of length; with dt ~ 0.1-0.5, we need maybe 60-150 steps for typical rays. For rays that loop around the photon sphere, more steps. Cap at 300.

Actually to be safe about quality, use 350 max steps with early termination. At 2M pixels * 350 steps that's too much for GPU? Modern GPUs handle it, maybe 30-60 fps at 1080p. Hmm, 1920*1080 = 2M pixels, each doing ~150 steps of ~20 flops = 6 GFLOP per frame. At 60fps that's 360 GFLOPS — feasible for a decent GPU but rough on integrated. I'll use render scale ~ min(dpr,1) and maybe additionally cap at 1600x900-ish? Let's do: scale = min(dpr, 1.5); and if width*height > 2.4M, scale down. Let's keep it simple with a target max pixel count.

Alternative optimization: reduce steps and use bigger steps far away. Use dt = 0.1 * r with min 0.05, max 0.9, and MAXSTEPS = 256. Far from hole with r=14, dt=0.9... wait 0.1*14 = 1.4 capped at 0.9. Rays going outward escape quickly. Fine.

Hmm but accuracy: with dt proportional to r, the angular error... For a straight ray, integrating with dt = 0.1*r gives ~10 steps per e-fold; fine.

Let me now design the disk sampling.

Disk: plane y=0 (equatorial). Between crossings, we detect sign change of pos.y. Let prevPos, pos. If prevPos.y * pos.y < 0 (crossing) and not first step, compute t = prevPos.y / (prevPos.y - pos.y), hit = mix(prevPos, pos, t). r_hit = length(hit.xz). If r_hit between inner and outer: sample.

Disk emission: temperature-based color: inner hot white-orange, outer cooler red. Use radial falloff.

Turbulence: use noise in polar coordinates with rotation: the disk rotates differentially (Keplerian: ω ∝ r^{-1.5}). So sample noise at angle φ - t*ω(r)... but that would make the noise rotate; instead, we can rotate the noise pattern. Use value noise fbm on coordinates (log r, φ + t*ω(r))? Hmm. Simpler: compute a rotating coordinate: angle offset = t * 0.6 / pow(r,1.5) ... For the visual, we want streaks. Use noise sampled at vec2(cos/sin rotated...). Let's do:

```
float ang = atan(p.z, p.x);
float omega = 1.2 / pow(r, 1.5); // Keplerian-ish
float a = ang + omega * time;
vec2 q = vec2(a * r * 0.5, r); // hmm
```

Better: use 3D noise in a rotating frame. Let's just do: sample fbm at position rotated by -omega*time about y axis, using the hit point's xz and scaled. Rotating the point about Y by angle omega(r)*t gives shearing which is exactly differential rotation. 

```
float rot = time * 1.0 / pow(r, 1.5) * 2.0;
float c = cos(rot), s = sin(rot);
vec3 pr = vec3(c*hit.x - s*hit.z, 0.0, s*hit.x + c*hit.z);
float n = fbm(vec3(pr.xz * 0.8, r*0.5)); // hmm
```

Actually for a disk we want the noise to be a function of (r, φ) with streaks. Using 3D value noise with vec3(x, 0, z)*freq works but rotation makes the pattern spin with radius-dependent rate → nice shear.

But wait: for the far side of the disk (behind the hole), its light is bent; the same sampling applies since we sample at the actual crossing point in space. Good.

Multiple crossings: accumulate color with alpha blending: 
```
color += transmittance * diskColor * density;
transmittance *= (1 - density*opacity);
```
with front-to-back ordering automatically because we march from camera. Good.

Also add a "glow"/halo around the black hole (the hot inner region), plus photon ring.

Photon ring: rays that wind near r=1.5. Natural disk lensing gives the ring, but for the classic look we can add an extra glow based on minimum r reached by the ray, weighted by disk brightness. Actually simplest: track the minimum radius rMin along the ray. Then add ring glow: intensity = exp(-((rMin - 1.5)^2)/something) * small. Hmm, the photon ring in reality is the lensed image of the disk — brightest. Let's just make sure the disk sampling near the inner edge (r ~ 2.5-3) is bright and the lensing naturally creates the ring. Plus add a subtle extra glow for rays with rMin close to 1.5 to make a crisp thin photon ring.

Actually, a nice trick: the photon ring appears at impact parameter b ≈ 2.598 rs (3√3/2). Add glow based on rMin: rays that graze rMin in [1.5, 1.7] get a thin bright ring. Let's do: `ring = exp(-pow((rMin - 1.55)/0.06, 2.0))` times a color like pale orange-white, and add. But careful: this could look artificial. It's fine — thin photon ring is requested.

Let's compute rMin during the march (min of length(pos)).

Starfield: procedural. Use direction after escape (normalized dir), hash to grid on a sphere. Standard approach: 
```
vec3 d = normalize(dir);
// map to cube faces or use spherical coords
```
Simplest: use a 3D hash grid: cell = floor(d * N) — but directions near the sphere surface... Use the classic: 
```
float stars(vec3 dir) {
  vec3 p = dir * 200.0;
  vec3 id = floor(p);
  vec3 f = fract(p) - 0.5;
  float h = hash13(id);
  ...
}
```
That creates stars at cell centers with random offsets. Need to check neighbors for star placement... Simpler approach: use the "star field" from hash of a direction quantized via spherical coords:

```
vec2 sph = vec2(atan(d.z,d.x), asin(d.y));
vec2 uv = sph * vec2(30.0, 15.0); // scale
```
but spherical mapping distorts near poles and has seams. It's acceptable-ish but the seam at φ=±π could show a line. Since we're looking around, a visible seam might appear. Use cube map approach: pick dominant axis, compute face uv, scale. That's cleaner.

Let's do:
```
vec3 ad = abs(d);
float m = max(ad.x, max(ad.y, ad.z));
vec2 uv;
if (ad.x == m) uv = vec2(d.z, d.y)/ad.x * vec2(sign(d.x),1.0);
else if (ad.y == m) uv = vec2(d.x, d.z)/ad.y * vec2(1.0, sign(d.y));
else uv = vec2(d.x, d.y)/ad.z * vec2(sign(d.z),1.0);
```
Then stars from hash grid on uv*scale. Use 2x2 neighbor check for a decent star distribution. Or simpler: use a "star layer" with hash per cell giving brightness and position within cell, then compute distance from cell-local random point to fragment → star. That's the standard approach with jittered points. Let's implement:

```
float starLayer(vec2 uv, float density, float scale, float size) {
  vec2 p = uv * scale;
  vec2 id = floor(p);
  vec2 gv = fract(p) - 0.5;
  float acc = 0.0;
  for (int y=-1;y<=1;y++) for (int x=-1;x<=1;x++) {
     vec2 o = vec2(float(x), float(y));
     vec2 cid = id + o;
     vec2 rnd = hash22(cid);
     if (rnd.x > density) continue;  // hmm need actual star presence
     vec2 sp = o + (rnd*0.8 + 0.1) - 0.5;  // star pos within neighbor cell relative to center
     float d = length(gv - sp);
     float b = smoothstep(size, 0.0, d);
     acc += b * (0.5 + 0.5*hash(cid.y*13.1+cid.x));
  }
  return acc;
}
```
9 iterations * 2 layers = fine.

Star colors: slightly varying (blue-white-yellow). Multiply by tint based on hash.

Also add a faint nebula? Not required. Maybe a subtle Milky Way band for depth. Optional — keep simple, maybe a very faint noise-based haze to avoid pure black background. I'll add a subtle background gradient/noise.

Now the starfield must be lensed — yes, we sample stars with the final escaped direction, which is bent. 

But note: the escape direction needs normalization, and the starfield should use the direction, not position. Since stars are at infinity, use normalize(dir) at escape. Good.

Now, the disk color function:

```
vec3 diskColor(float r, float phi, float t, out float density)
```
Temperature: T ∝ r^{-3/4} roughly for thin disk. Color ramp: inner (r ~ 2.5) white-hot with orange; mid: orange; outer: deep red.

Let's define:
```
float inner = 2.2, outer = 13.0;
float x = clamp((r - inner)/(outer - inner), 0.0, 1.0);
```
Brightness: falloff ~ 1/r^2 or so, but with inner edge brighter. Let's do `float radial = pow(inner/r, 2.0)` clipped... hmm that makes outer very dim. Use mix.

Color ramp:
```
vec3 hot = vec3(1.0, 0.95, 0.85);   // white hot
vec3 mid = vec3(1.0, 0.5, 0.12);    // orange
vec3 cool = vec3(0.7, 0.12, 0.03);  // deep red
```
Interpolate: for x in [0,0.35] mix hot→mid, [0.35,1] mix mid→cool.

Brightness: `float bright = mix(3.0, 0.6, smoothstep(0.0,1.0,x))` roughly, times something.

Turbulence: fbm noise with shear gives density variation. Use `float n = fbm(...)` in [0,1]; density = pow(n, 2.0) * profile.

Also apply a smooth fade at inner and outer edges: 
```
float edge = smoothstep(inner, inner+0.5, r) * (1.0 - smoothstep(outer-3.0, outer, r));
```
Hmm, inner edge should be sharp-ish and bright.

Also add a vertical thickness: the disk is thin (y=0 plane), so crossing detection gives a natural thin plane. But to avoid aliasing (thin plane → single sample), we could accumulate multiple samples near the plane. Standard approach: when the ray is within the disk thickness region (|y| < thickness), accumulate emission. That gives a volumetric look. Let's do that: during marching, if |pos.y| < diskThickness (which scales with r maybe) and r within disk radii, accumulate emission with step-based density. That gives smoother, softer disk. But then the "crossing" resolution is handled by step size which near the disk could be large... Hmm.

Alternative hybrid: use crossing detection with interpolation, and blend the emission with a soft alpha based on the ray's angle to the plane. The thin-plane approach gives crisp results and is common. Let's use the crossing approach, and multiply density by a factor depending on 1/|dot(dir, normal)| maybe (longer path through a slab). Actually: optical depth through a slab of thickness H at grazing angle: path = H / |dir.y|, capped. So density ∝ min(H/|dir.y|, cap). This naturally makes the disk brighter when viewed edge-on (grazing) — which is physically reasonable and gives that nice bright edge-on look. But it can blow up. Cap it.

I'll do: `float pathFactor = clamp(0.15/ max(abs(dirY), 0.02), 0.0, 6.0)`. Hmm, need dirY at crossing: use mix of prevDir and dir, or just dir.

Let's do: at crossing, `float dY = mix(prevDir.y, dir.y, tt)`. Use that.

Then density = baseDensity * profile * noise * pathFactor, then alpha = 1 - exp(-density * ...). Accumulate with transmittance.

Also, the "inner edge hot orange-white": near inner radius add extra glow.

Additionally, the disk's inner region should be lensed to form the ring over/under the hole. That's automatic.

Now the sky background sampling: if ray escapes (r > escapeR), color = starfield(normalize(dir)). If captured (r < 1), color = black (with maybe a tiny bit of the photon ring added).

Also need: the ray may neither escape nor be captured within max steps → treat as captured-ish (black) or escaped with last direction? Better: if steps exhausted, use black if r < some threshold else starfield. Typically rays near the photon sphere. Let's just treat as captured (black) to avoid artifacts... Actually if the ray is still far away after max steps (unlikely), black would be wrong. Let's decide by r: if r > 5 use starfield, else black. Fine.

Now, tone mapping: colors can get bright; use ACES-ish or simple: color = 1 - exp(-color * exposure) then gamma. Use `pow(color, vec3(1/2.2))` after.

Also add a subtle bloom-ish glow: hard without post-processing. Instead, add a glow term near the black hole: e.g., add a halo proportional to exp(-r/…) computed from... hmm, we can add glow based on the ray's minimum distance: `glow = exp(-(rMin-1.0)*1.5)` giving a soft halo around the hole. That's cheap and looks decent. But careful not to fill the whole screen. Let's add small amount.

Let's now write the noise functions.

```glsl
float hash11(float p){ p = fract(p*0.1031); p *= p+33.33; p *= p+p; return fract(p); }
vec2 hash22(vec2 p){
  vec3 p3 = fract(vec3(p.xyx)*vec3(0.1031,0.1030,0.0973));
  p3 += dot(p3, p3.yzx+33.33);
  return fract((p3.xx+p3.yz)*p3.zy);
}
float hash13(vec3 p3){
  p3 = fract(p3 * 0.1031);
  p3 += dot(p3, p3.zyx + 31.32);
  return fract((p3.x + p3.y) * p3.z);
}
float vnoise(vec3 x){
  vec3 i = floor(x); vec3 f = fract(x);
  f = f*f*(3.0-2.0*f);
  float n000 = hash13(i+vec3(0,0,0));
  ...
  return mix(mix(mix(n000,n100,f.x), mix(n010,n110,f.x), f.y), mix(mix(n001,n101,f.x), mix(n011,n111,f.x), f.y), f.z);
}
```

8 hash calls per noise, fbm 4 octaves = 32 hashes per sample — with maybe 2-3 disk crossings per ray that's fine.

Now the fragment shader main:

```glsl
#version 300 es
precision highp float;
uniform vec2 uRes;
uniform float uTime;
out vec4 outColor;
```

Camera setup:
```
float t = uTime;
float camDist = 16.0;
float az = t*0.06;
float el = 0.14 + 0.10*sin(t*0.045);  // radians above disk plane
vec3 camPos = vec3(cos(el)*cos(az), sin(el), cos(el)*sin(az)) * camDist;
vec3 target = vec3(0.0);
vec3 fwd = normalize(target - camPos);
vec3 right = normalize(cross(fwd, vec3(0,1,0)));
vec3 up = cross(right, fwd);
vec2 p = (gl_FragCoord.xy - 0.5*uRes)/uRes.y;
float fov = 1.6; // focal
vec3 rd = normalize(p.x*right + p.y*up + fov*fwd);
```
Hmm, note: `up = cross(right, fwd)` — check handedness: right = normalize(cross(fwd, worldUp)); up = cross(right, fwd). Let's verify with fwd=(0,0,-1), worldUp=(0,1,0): cross(fwd, up) = (0,0,-1)x(0,1,0) = (0*0-(-1)*1, (-1)*0-0*0, 0*1-0*0) = (1, 0, 0). right = (1,0,0). up = cross(right,fwd) = (1,0,0)x(0,0,-1) = (0*(-1)-0*0, 0*0-1*(-1), 0) = (0,1,0). Good.

Camera elevation ~0.14-0.24 rad ≈ 8-14°. That's near edge-on, good for Interstellar look.

Disk inner radius: with rs=1, ISCO = 3. But Interstellar-like images show the disk extending to ~inner. Let's set inner = 2.6, outer = 14. Camera at 16 with fov giving the disk nicely framed.

Hmm, actually with camera distance 16 and outer disk radius 14, the disk nearly fills the view. Let's set outer = 11, camera distance 15.

Let's think about the visual scale: The black hole shadow has apparent radius b = 2.6 rs for a distant observer. So with rs = 1, shadow radius ~2.6 units at distance 15 → angular radius ~ 2.6/15 = 0.173 rad ≈ 10°. With vertical FOV = 2*atan(0.5/fov)... if fov = 1.6 (in units where p.y ranges ±0.5), the half-angle = atan(0.5/1.6) = 0.303 rad ≈ 17°. So the shadow (10°) occupies 10/17 ≈ 60% of half-height → diameter 120% of half height = 60% of screen height. That's quite big. Maybe reduce: camera dist 20, or increase fov. Let's aim for the shadow ~ 35% of screen height. Half-angle for shadow with dist 18: atan(2.6/18) = 0.1437 rad. Want that to be ~0.17 of half-height... screen half height = 0.5 in p units → we want the shadow radius in p units ≈ 0.17. p.y = tan(angle) * fov... roughly p.y = fov * tan(θ) = 1.6*0.1437*... hmm wait p.y = tan(θ)*focal? Let's redo: rd = normalize(p.x*right + p.y*up + fov*fwd). For small angles, tan θ ≈ p.y/fov. So shadow radius in p.y: p.y = fov * tanθ = 1.6 * 0.1437 = 0.23. Screen half-height is 0.5. So shadow radius = 46% of half-height = 23% of screen height. Shadow diameter ~46% of screen height. Reasonable for a dramatic look. Maybe a bit big but fine. Actually with lensing the apparent shadow radius is b = 3√3/2 rs ≈ 2.598 rs. At distance 18 that's θ = 0.144 rad. OK.

Hmm, but also the disk outer radius 11 at distance 18 → angular 0.55 rad → tan = 0.61 → p.y = 0.98, off screen. That's fine (disk extends beyond view), but we might want the whole disk visible. In Interstellar, the disk fills the frame. Let's keep outer = 12 and camera dist 20 to have a good composition: shadow radius p.y = 1.6*2.598/20 = 0.208 (42% of half height). Disk outer edge at r=12, seen edge-on extends horizontally: p.x = 1.6 * (12/20) ≈ 0.96 — wider than the half-width? p.x range depends on aspect. For 16:9, p.x ranges ±0.89. So the disk edge is just at/beyond the frame horizontally. Good, that's cinematic.

Actually, let's reduce camera distance to 16 and outer radius to 12: shadow p.y = 1.6*2.598/16 = 0.26 → 52% of half-height. Disk outer at 12/16*1.6 = 1.2 → off-screen horizontally. Fine, it fills the frame.

I'll go with camDist = 16, outer = 12, inner = 2.6.

Hmm, one consideration: with camera at 16 and near-edge-on view, the disk's near side passes in front of the hole and the far side lensed above/below. 

Now, the disk should be "turbulent" — with fbm noise and shearing.

Let me write the disk sample:

```glsl
vec3 diskSample(vec3 p, float r, float tt, out float alpha)
```
Where p is the 3D hit point, r its radius.

```glsl
float phi = atan(p.z, p.x);
// Keplerian shear
float omega = 1.6 / pow(r, 1.5);
float a = phi + omega * tt;   // rotating angle
// noise in (a, r) space: use 3D noise with wrapping? Use:
vec3 q = vec3(cos(a), sin(a), 0.0) * r * 0.9;  // hmm this makes noise repeat
```
Actually using (cos a, sin a)*r reconstructs the rotated point. So: rotated point = rotY(-omega*t) applied to p. Let's just compute:
```
float c = cos(omega*tt), s = sin(omega*tt);
vec3 pr = vec3(c*p.x - s*p.z, p.y, s*p.x + c*p.z);
```
Then noise = fbm(pr * 0.55 + vec3(0, 0, 0)) — but the disk is in the y=0 plane, so pr.y = 0, and 3D noise sampled in a plane is fine.

To get streaks (filaments), stretch the noise azimuthally? With differential rotation the shear naturally creates spirals over time. Since noise is sampled at fixed positions in the rotating frame, at t=0 the pattern is random; the rotation shears it into spirals. Good.

Use fbm with 4 octaves and maybe anisotropy: sample at (pr.xz * freq) where freq differs for radial vs azimuthal to make streaks. Let's do `vec3 sp = vec3(pr.x, 0.0, pr.z) * 0.5;` and add `sp.y = r*0.3` for variation? Hmm.

Let's write: 
```
float n = 0.0;
vec3 sp = pr * 0.6;
float amp = 0.5;
for (int i=0;i<4;i++){
   n += amp * vnoise(sp);
   sp *= 2.03; amp *= 0.5;
}
```
The 3D noise with y=0 always: vnoise(sp) where sp.y = 0 — the interpolation in y is fine.

Better idea for filaments: use `sp = vec3(pr.x*0.5, r*0.35, pr.z*0.5)` — no wait pr.x, pr.z already encode position; multiplying x,z by 0.5 and adding r as y creates a pattern that varies with radius independently — that could look odd. Keep it simple: noise(pr * 0.6).

Then density = pow(n, 1.8) roughly.

Radial profile:
```
float x = clamp((r - INNER) / (OUTER - INNER), 0.0, 1.0);
float radialFalloff = pow(1.0 - x, 2.0) * ... 
```
Hmm, we want brightness peaking near inner edge. Let's do:
```
float bright = mix(1.0, 0.08, smoothstep(0.0, 1.0, x)) ... 
```
Actually the physical thin-disk emission ∝ r^-3 roughly (T^4 with T∝r^-3/4). So brightness ∝ (INNER/r)^3. At r=12, (2.6/12)^3 = 0.01 — very dim. Too dim for our purposes. Use a gentler power: (INNER/r)^1.8, gives 0.06. Still dim. For visual appeal, let's use a softer falloff with a floor:

`float bri = pow(INNER/r, 1.6);` → at r=12: (0.2167)^1.6 = e^{1.6*ln0.2167} = e^{1.6*(-1.529)} = e^{-2.446}=0.0866. Hmm.

We'll boost the overall with exposure and make the outer regions visible with a "cool red" color that's still visible. Since we tone map, an HDR range is fine: inner brightness ~ 1.0, outer ~ 0.05, then exposure ~2 and ACES-ish. The outer disk will look dark red. Good — that matches "cooler red outer regions".

Let's use: `float bri = 2.5 * pow(INNER/r, 1.5);` plus a boost near the inner edge:
```
float innerGlow = exp(-(r - INNER) * 1.2); // extra hot glow at inner edge
```

Color:
```
float t01 = clamp((r - INNER) / 8.0, 0.0, 1.0);
vec3 col = mix(vec3(1.0, 0.93, 0.82), vec3(1.0, 0.45, 0.10), smoothstep(0.0,0.45,t01));
col = mix(col, vec3(0.55, 0.08, 0.02), smoothstep(0.45,1.0,t01));
```
Hmm, the innermost should be white-hot: mix with white near r=INNER.

Let's define temperature-ish parameter `tt01 = clamp((r-INNER)/ (OUTER-INNER), 0,1)` and then:
```
vec3 col = mix(vec3(1.0,0.98,0.92), vec3(1.0,0.55,0.15), smoothstep(0.0,0.25,tt01));
col = mix(col, vec3(0.85,0.20,0.05), smoothstep(0.25,0.7,tt01));
col = mix(col, vec3(0.45,0.06,0.02), smoothstep(0.7,1.0,tt01));
```

Density/alpha:
```
float dens = bri * (0.35 + 0.9*n) ;
float pathF = clamp(0.5/ max(abs(dY), 0.05), 0.6, 5.0);
float a = 1.0 - exp(-dens * pathF * 0.6);
vec3 emit = col * (bri * (0.5 + 1.2*n) + innerGlow);
```

Hmm, careful: brightness in the color and alpha separately. Let's keep it simpler: emission = col * bright * noiseModulated, alpha from density.

Then accumulation:
```
color += trans * emit * pathF;   // no, let's fold pathF into alpha and emission consistently
```
Simplify: treat as emissive-absorptive medium: 
```
float sigma = dens * pathF;  // optical depth per crossing
float alpha = 1.0 - exp(-sigma);
color += trans * emit;   // emit already scaled
trans *= (1.0 - alpha);
```
where emit = col * bright * (0.6+0.8*n) * clamp(sigma*2, 0, 2)? Getting complicated. Let's just do:

```
float n = fbm(...);          // 0..1
float density = profile(r) * (0.25 + 1.5*n) * pathF;
float alpha = 1.0 - exp(-density * 1.2);
vec3 emit = col * (bri * (0.4 + 1.6*n)) * 1.5;
color += trans * emit;
trans *= (1.0 - alpha);
```
Where bri includes innerGlow. This is fine and tunable by eye... but I can't see the result. So I need to be conservative and reasonable.

Let me think about typical values. At r = 3 (inner), bri = 2.5*(2.6/3)^1.5 = 2.5*0.807 = 2.0. innerGlow = exp(-(3-2.6)*1.2)= exp(-0.48)=0.62. Total bri ~ 2.6. n ~ 0.5. emit = col * 2.6*1.2*1.5 = col*4.7. With col ~ (1,0.6,0.2), emit ~ (4.7, 2.8, 0.9). Tone mapped with exposure ~1 and ACES → near white with orange. Good.

At r=10: bri = 2.5*(2.6/10)^1.5 = 2.5*0.1326 = 0.33. emit = col*(0.33*1.2)*1.5 = col*0.6. col at t01=(10-2.6)/9.4=0.79 → mix toward (0.45,0.06,0.02) → ~ (0.5,0.1,0.03). emit ~ (0.3,0.06,0.02). Dim red. Tone-mapped that's a dark red — visible. Good.

Alpha: density at r=3: profile ~1, n=0.5 → (0.25+0.75)=1.0, pathF maybe 2 → density 2 → alpha = 1-exp(-2.4)=0.91. Quite opaque. At r=10: profile ~ (1-x)=0.2 → density 0.2*1.0*2 = 0.4 → alpha = 1-exp(-0.48)=0.38. OK.

Hmm, pathF: when viewed near edge-on, |dY| is small (ray nearly parallel to disk plane) → pathF large. Cap at ~4. Since our camera is at ~10° elevation, rays toward the disk have |dir.y| around sin(10°)=0.17 → pathF = 0.5/0.17 = 2.9. Fine.

Now about the ray marching and crossing detection with large steps: near the disk, step sizes could be ~0.5-1.0, so the crossing interpolation is essential. With interpolation, we get the exact crossing point. Good.

But there's a subtlety: for rays that graze the disk plane at a shallow angle (nearly tangent), there may be no sign change but the ray passes through the disk region. With a thin disk this is a measure-zero case. Fine.

Let's now also handle the case where the camera is above the disk plane and looking down at a shallow angle: rays hit the disk once (front, on the near side) — well, actually the ray hits the disk plane once going down; the far side of the disk is behind the hole, so rays that pass near the hole bend and hit the disk plane multiple times (top image and bottom image). Those crossings give the classic look. 

Also rays that start above the plane and go up escape without crossing.

Great.

Now the photon ring: we track rMin. Then:
```
float ringGlow = exp(-pow((rMin - 1.52)/0.09, 2.0));
```
Hmm, but that's a ring around the shadow edge; the actual photon ring radius depends on the impact parameter. rMin for a ray with impact parameter b is the closest approach. The photon sphere is at r=1.5. Rays with b slightly above 2.598 wind around and escape; those have rMin ≈ 1.5. So the ring appears at the shadow edge. Good.

The ring should be thin and bright. Add: `col += vec3(1.0,0.75,0.45) * ringGlow * 0.6 * trans;` — but trans at that point... The ring is outside the shadow, so it's accumulated after the disk? No, rMin is computed along the whole ray, so we should add it at the end (multiplied by trans at the end). Actually, adding at the end with the final transmittance is right.

Hmm, but adding a ring glow unconditionally would make a ring around the black hole even where the disk is in front. That's fine visually (the ring is at the shadow edge, mostly not covered by the disk since the disk's front part crosses in front... at edge-on view the disk does cross in front of the shadow). Actually in Interstellar, the front part of the disk passes in front of the black hole. Hmm, but the photon ring is the bright thin ring at the shadow edge. It's fine to add it with transmittance attenuation.

Let me also add a general "glow" around the black hole from the disk light: `glow = 0.06 * exp(-(rMin-1.0)*0.8)` colored orange. This creates a soft halo. Let's include modestly.

Also the "thin photon ring" — we could also make it based on final escape direction distance from the shadow center, but rMin approach is better.

Now: stars.

```glsl
vec3 starField(vec3 d) {
  // cube map uv
  vec3 ad = abs(d);
  vec2 uv; float face;
  if (ad.x >= ad.y && ad.x >= ad.z) { uv = vec2(d.z, d.y)/ad.x; face = d.x>0.0?0.0:1.0; }
  else if (ad.y >= ad.z) { uv = vec2(d.x, d.z)/ad.y; face = d.y>0.0?2.0:3.0; }
  else { uv = vec2(d.x, d.y)/ad.z; face = d.z>0.0?4.0:5.0; }
  ...
}
```
Then for stars: 3 layers with different scales.

```
float stars(vec2 uv, float scale, float density, float size, float seed) {
  vec2 p = uv * scale + seed;
  vec2 id = floor(p);
  vec2 gv = fract(p) - 0.5;
  float acc = 0.0;
  for (int j = -1; j <= 1; j++) {
    for (int i = -1; i <= 1; i++) {
      vec2 o = vec2(float(i), float(j));
      vec2 cid = id + o;
      vec2 h = hash22(cid + seed);
      if (h.x > density) continue;
      vec2 sp = o + (h - 0.5)*0.85;
      float dd = length(gv - sp);
      float b = smoothstep(size, 0.0, dd);
      b *= b;
      acc += b;
    }
  }
  return acc;
}
```
Hmm, `if (h.x > density) continue;` — in GLSL ES 3.00, `continue` inside loops is fine.

Star brightness variation: multiply by (0.3 + 0.7*h.y). Let's fold it in.

Star color: tint by temperature: mix between bluish white and warm white based on a hash.

Then final sky = stars * brightness + faint nebula.

Also, the lensing near the hole magnifies the starfield creating an Einstein ring effect — automatic.

One more: the "photon ring" also makes the starfield distort. Fine.

Now performance: 9 iterations per star layer * 3 layers = 27 hash22 calls + ... that's fine.

Actually we should only compute the starfield once per ray (at escape). Good.

Let me also handle the disk's own "glow" affecting the sky? No.

Now the tone mapping. Let's use:

```
vec3 aces(vec3 x){
  const float a=2.51,b=0.03,c=2.43,d=0.59,e=0.14;
  return clamp((x*(a*x+b))/(x*(c*x+d)+e),0.0,1.0);
}
```
Apply exposure before: `color *= 1.0;` then aces, then gamma? ACES already includes a sort of gamma-ish. Many shaders do `pow(aces(color), vec3(1/2.2))`. Let's do: color = aces(color * exposure); color = pow(color, vec3(0.4545)); Hmm, ACES output is already display-referred-ish (it's meant to be applied to linear then converted with sRGB OETF). Standard practice: linear → ACES tonemap → sRGB encode. So do pow(color, 1/2.2) after. OK.

Let me set exposure ~1.2.

Now let's write the full code.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Black Hole</title>
<style>
  html,body{margin:0;padding:0;height:100%;background:#000;overflow:hidden;}
  canvas{display:block;width:100vw;height:100vh;}
</style>
</head>
<body>
<canvas id="c"></canvas>
<script>
const canvas = document.getElementById('c');
const gl = canvas.getContext('webgl2', {antialias:false, powerPreference:'high-performance'});
if(!gl){ document.body.innerHTML = '<p style="color:#fff;font-family:sans-serif">WebGL2 not supported.</p>'; }

const vertSrc = `#version 300 es
in vec2 aPos;
void main(){ gl_Position = vec4(aPos, 0.0, 1.0); }
`;

const fragSrc = `#version 300 es
precision highp float;
...
`;

function createShader(type, src){...}
...
</script>
</body>
</html>
```

Full-screen quad: two triangles via a VBO with 6 vertices, or use gl_VertexID with no buffers (WebGL2 supports gl_VertexID). Simpler: create a buffer with 6 vec2.

Now, writing the fragment shader carefully.

```glsl
#version 300 es
precision highp float;
out vec4 fragColor;

uniform vec2  uRes;
uniform float uTime;

#define PI 3.141592653589793

// ---------- hash / noise ----------
float hash13(vec3 p3){
  p3 = fract(p3 * 0.1031);
  p3 += dot(p3, p3.zyx + 31.32);
  return fract((p3.x + p3.y) * p3.z);
}
vec2 hash22(vec2 p){
  vec3 p3 = fract(vec3(p.xyx) * vec3(0.1031, 0.1030, 0.0973));
  p3 += dot(p3, p3.yzx + 33.33);
  return fract((p3.xx + p3.yz) * p3.zy);
}
float vnoise(vec3 x){
  vec3 i = floor(x), f = fract(x);
  f = f*f*(3.0 - 2.0*f);
  float n000 = hash13(i + vec3(0.0,0.0,0.0));
  float n100 = hash13(i + vec3(1.0,0.0,0.0));
  float n010 = hash13(i + vec3(0.0,1.0,0.0));
  float n110 = hash13(i + vec3(1.0,1.0,0.0));
  float n001 = hash13(i + vec3(0.0,0.0,1.0));
  float n101 = hash13(i + vec3(1.0,0.0,1.0));
  float n011 = hash13(i + vec3(0.0,1.0,1.0));
  float n111 = hash13(i + vec3(1.0,1.0,1.0));
  return mix(mix(mix(n000,n100,f.x), mix(n010,n110,f.x), f.y),
             mix(mix(n001,n101,f.x), mix(n011,n111,f.x), f.y), f.z);
}
float fbm(vec3 p){
  float s = 0.0, a = 0.5;
  for(int i = 0; i < 4; i++){
    s += a * vnoise(p);
    p = p * 2.02 + vec3(17.3, 9.1, 5.7);
    a *= 0.5;
  }
  return s / 0.9375;  // normalize (0.5+0.25+0.125+0.0625)
}
```

Note: p = p*2.02 + offset — the offset helps decorrelate.

Wait, fbm normalization: sum of amplitudes 0.9375, so dividing gives 0..1. Good.

Star field:

```glsl
vec2 dirToFaceUV(vec3 d){
  vec3 a = abs(d);
  if (a.x >= a.y && a.x >= a.z) return vec2(d.z, d.y) / a.x * (d.x > 0.0 ? 1.0 : -1.0);
  if (a.y >= a.z) return vec2(d.x, d.z) / a.y * (d.y > 0.0 ? 1.0 : -1.0);
  return vec2(d.x, d.y) / a.z * (d.z > 0.0 ? 1.0 : -1.0);
}
```
Hmm, the mirroring sign doesn't matter much for stars. Actually, for continuity it does matter at face edges, but since stars are random points, discontinuities are invisible. Just use the standard cube map UV without sign correction. Actually without sign correction, the mapping is discontinuous across face boundaries but that just means a star's neighborhood is remapped — invisible. Fine, keep simple: `return vec2(d.z, d.y)/a.x;` etc.

But wait: using the face UV means the same star pattern is repeated... no, each face has a different UV range, and we use the same hash grid, so patterns will be continuous-ish across the cube faces? Different faces map to the same UV region? For face +x, uv = (d.z, d.y)/|d.x| ∈ [-1,1]². For face +z, uv = (d.x,d.y)/|d.z| ∈ [-1,1]². So all faces map to [-1,1]² — the same region! So the star pattern from face +x and face +z would be identical, creating a repeating pattern. Bad. Add a per-face offset: pass a seed based on the face index.

Let's return a vec3 (uv, faceIndex) and use faceIndex*17.0 as seed offset.

```glsl
vec3 dirToFace(vec3 d){
  vec3 a = abs(d);
  if (a.x >= a.y && a.x >= a.z) return vec3(d.z, d.y)/a.x, d.x > 0.0 ? 0.0 : 1.0);
  ...
}
```
GLSL doesn't have that syntax; return a vec3 where z = face id.

OK.

```glsl
float starLayer(vec2 uv, float scale, float density, float size, float seed){
  vec2 p = uv * scale;
  vec2 id = floor(p);
  vec2 gv = fract(p) - 0.5;
  float acc = 0.0;
  for(int j = -1; j <= 1; j++){
    for(int i = -1; i <= 1; i++){
      vec2 o = vec2(float(i), float(j));
      vec2 h = hash22(id + o + seed * 13.7);
      if(h.x > density) continue;
      vec2 sp = o + (h - 0.5) * 0.9;
      float dd = length(gv - sp);
      float b = smoothstep(size, 0.0, dd);
      acc += b * b * (0.25 + 0.75 * h.y);
    }
  }
  return acc;
}
```

Then:
```glsl
vec3 skyColor(vec3 d){
  vec3 f = dirToFace(d);
  vec2 uv = f.xy;
  float seed = f.z;
  float s = 0.0;
  s += starLayer(uv, 8.0, 0.22, 0.09, seed + 0.0) * 1.0;
  s += starLayer(uv, 18.0, 0.18, 0.055, seed + 5.0) * 0.7;
  s += starLayer(uv, 40.0, 0.14, 0.035, seed + 11.0) * 0.45;
  ...
}
```
Hmm — scale 40 with uv in [-1,1] → grid of 80x80 cells per face. With density 0.14, that's ~900 stars per face * 6 faces = 5400 stars. Reasonable. But the `size` parameter is in cell units; at scale 40, size 0.035 cell units — the star radius in uv terms is 0.035/40 = tiny. Actually the star size should be in screen space, not cell space, otherwise higher scales give smaller stars. That's fine — different layers have different star sizes.

But there's an issue: at high scale (40), the cells are small, and the pixel footprint may be larger than the cell → aliasing/flickering. Since we can't easily do AA, use a moderate max scale. Let's use scales 6, 14, 30. Also, the star size relative to the cell: with size 0.04 in cell units and cell = 1/30 of a face... a face covers a large angle. It'll be sub-pixel at high resolution. Stars will flicker. To mitigate, we can make the star brightness scale with the size — or accept it.

Alternative: compute star field in screen space after lensing? No.

Hmm, a common trick: make stars "soft" with a smoothstep over a fixed screen-space-ish size. But screen-space size varies. Let's just keep the layers coarse enough: scales 5, 11, 22 with sizes 0.12, 0.08, 0.05. At scale 22, cell size in uv = 1/22 = 0.045; the star radius = 0.05 cell units = 0.0023 uv. The screen: uv spans about... The FOV is about 2*atan(0.5/1.6) ≈ 35° vertically = 0.6 rad. Screen height ~ 900 px. So 1 rad ≈ 1500 px. 0.0023 uv ≈ 0.0023 * 0.6 rad? Roughly uv range of the face: a face covers up to 90°, and uv ∈ [-1,1] covers that. So uv 0.0023 ≈ 0.0023/2*90° = 0.1° = 0.0018 rad ≈ 2.7 px. That's a decent star size (a few pixels). Good.

Actually wait, the relationship: for a face, uv = tan-ish mapping. Near the face center, uv ≈ angle in radians (for small angles). So uv 0.0023 → 0.0023 rad → ~3.5 px. Good.

Stars will be a few pixels — fine.

Let's also add a subtle galactic haze using fbm on the direction to avoid a totally black background:
```
float haze = fbm(d * 3.0);
col += vec3(0.05,0.06,0.10) * pow(haze, 3.0) * 0.6;
```
Hmm, that adds a dim blue-ish glow. Might look nice. Keep it very subtle.

Star colors: mix between (0.7,0.8,1.0) bluish and (1.0,0.9,0.75) warm using a hash. Let's use per-layer tint via hash of the cell? We'd need to accumulate color per star. Simplify: compute the star intensity in two "channels" — actually, let's just tint the whole starfield slightly and add a bit of variation via the layer: layer1 warm, layer2 blue, layer3 white. Good enough.

Actually, better: make starLayer return a vec2 (intensity, warmness)? Let's keep it simple: return intensity and apply fixed tints per layer.

Now the main ray march.

```glsl
void main(){
  vec2 res = uRes;
  vec2 uv = (gl_FragCoord.xy - 0.5*res) / res.y;

  float t = uTime;

  // camera
  float camDist = 16.0;
  float az = t * 0.07;
  float el = 0.17 + 0.09 * sin(t * 0.041);
  vec3 camPos = vec3(cos(el)*cos(az), sin(el), cos(el)*sin(az)) * camDist;
  vec3 fwd = normalize(-camPos);
  vec3 right = normalize(cross(fwd, vec3(0.0,1.0,0.0)));
  vec3 up = cross(right, fwd);
  float focal = 1.55;
  vec3 rd = normalize(uv.x*right + uv.y*up + focal*fwd);

  vec3 pos = camPos;
  vec3 dir = rd;
  float h2 = dot(cross(pos, dir), cross(pos, dir)); // conserved

  vec3 color = vec3(0.0);
  float trans = 1.0;
  float rMin = 1e9;

  const int MAX_STEPS = 300;
  bool captured = false;
  bool escaped = false;

  vec3 prevPos = pos;
  vec3 prevDir = dir;

  for(int i = 0; i < MAX_STEPS; i++){
    float r = length(pos);
    rMin = min(rMin, r);
    if(r < 1.0){ captured = true; break; }
    if(r > 40.0){ escaped = true; break; }

    float dt = clamp(0.08 * r, 0.03, 1.2);   // hmm
    ...
  }
}
```

Wait, we need to check disk crossing between prevPos and the new pos. Let's structure:

```
prevPos = pos;
prevDir = dir;
float r = length(pos);
float dt = clamp(0.055 * r, 0.035, 1.0);
// integrate
vec3 acc = -1.5 * h2 * pos / pow(r, 5.0);
dir += acc * dt;
pos += dir * dt;

// check plane crossing
if(prevPos.y * pos.y < 0.0) {
   float k = prevPos.y / (prevPos.y - pos.y);
   vec3 hit = mix(prevPos, pos, k);
   float rr = length(hit.xz);
   if(rr > INNER && rr < OUTER) {
      float dY = mix(prevDir.y, dir.y, k);
      ... accumulate
   }
}
```

Hmm, but the acceleration applied to dir before the position update — using the accel at the old position. Semi-implicit Euler with variable steps is okay.

Wait, there's an issue: computing acc with pos before updating, then dir += acc*dt, then pos += dir*dt. That's semi-implicit Euler (symplectic-ish). Fine.

Now, the step size: near r=1, dt = 0.055 — that's small, but the region r<1 is the black hole, and we stop there. Near r=1.5, dt=0.08. With 300 steps, we can traverse... If a ray takes a winding path near the photon sphere, each orbit is ~2π*1.5 = 9.4 units, at dt ~0.1 → 94 steps per orbit. 300 steps allows ~3 orbits. OK.

But the total budget: from r=16 to r=1, the path length is ~15; with dt up to 1.0 at large r, that's maybe 30 steps. Good.

Actually dt = clamp(0.055*r, 0.035, 1.0): at r=16 → 0.88. The straight-line distance from 16 to 1 is 15 units, ~25 steps. Fine.

Hmm, but accuracy for the deflection far away: at r=16 with dt=0.88, the deflection is small there anyway. Fine.

Let me reconsider the accuracy near the photon sphere. dt = 0.055*1.5 = 0.0825. Angular step = 0.0825/1.5 = 0.055 rad ≈ 3°. With ~64 steps per orbit, that's decent accuracy for the ring structure. Might cause slight banding in the photon ring, but okay. Let's use a smaller coefficient: 0.045*r → at r=1.5: 0.0675 (2.6°/step). And max dt 0.9.

Number of steps: let's set MAX_STEPS = 320.

Also for performance, we could break early when the ray is far away and moving away: if r > 40, break. Also if dot(pos, dir) > 0 and r > 25 → escape. Let's keep r > 40.

Now the disk accumulation code:

```glsl
if(prevPos.y * pos.y < 0.0){
  float k = prevPos.y / (prevPos.y - pos.y);
  vec3 hit = mix(prevPos, pos, k);
  float rr = length(hit.xz);
  if(rr > DISK_IN && rr < DISK_OUT){
     float dY = abs(mix(prevDir.y, dir.y, k));
     // rotation for shear
     float omega = 1.7 / pow(rr, 1.5);
     float ang = omega * t;
     float ca = cos(ang), sa = sin(ang);
     vec3 pr = vec3(ca*hit.x - sa*hit.z, 0.0, sa*hit.x + ca*hit.z);
     float n = fbm(pr * 0.55 + vec3(0.0, rr*0.25, 0.0));
     ...
  }
}
```
Hmm, `pr*0.55` where pr.y = 0 → the noise is a 2D slice of 3D noise at y=0. Adding rr*0.25 as the y coordinate makes the noise vary with radius in a way that could break the shear pattern. Let's not; instead use `fbm(vec3(pr.x, 0.0, pr.z) * 0.5)`.

Hmm, but with a pure 2D slice, the noise pattern is a 2D field that rotates. Since the rotation angle depends on r, we get shear. Good.

But note: rotating the sample point by +ang means the pattern rotates by -ang... whatever, the direction of rotation just needs to match the orbital direction for a natural look. Keplerian orbits go counterclockwise (viewed from +y) if ω > 0 in the standard sense. Doesn't matter visually.

Wait, actually there's a subtlety: the disk should appear to rotate. With the sample point rotated by ang = ω(r)*t, the pattern at radius r appears to rotate by -ang. Since ω decreases with r, the inner rotates faster → correct differential rotation. Good.

Now the density:

```glsl
float x = clamp((rr - DISK_IN) / (DISK_OUT - DISK_IN), 0.0, 1.0);
float radial = mix(1.0, 0.12, smoothstep(0.0, 1.0, x)); // hmm
```
Let's use a power law: `float radial = pow(DISK_IN / rr, 1.7);` → at rr=DISK_IN: 1. At rr=12 with DISK_IN=2.6: (0.2167)^1.7 = e^{-2.60} = 0.074.

And an inner boost: `radial *= 1.0 + 1.5*exp(-(rr-DISK_IN)*1.5);` at rr=2.6 → *2.5.

Edge fades:
```
float edgeIn = smoothstep(DISK_IN, DISK_IN + 0.35, rr);
float edgeOut = 1.0 - smoothstep(DISK_OUT - 3.0, DISK_OUT, rr);
```
Hmm, DISK_OUT = 12, so the fade starts at 9. That might be too gradual. Use `1.0 - smoothstep(DISK_OUT*0.65, DISK_OUT, rr)`.

Density noise: `float dens = radial * edgeIn * edgeOut * (0.15 + 1.35*n);`

Path factor: `float pf = clamp(0.35 / max(dY, 0.03), 0.5, 5.0);`

Then:
```
float sigma = dens * pf * 3.0;
float alpha = 1.0 - exp(-sigma);
```

Emission color:
```
float tt01 = clamp((rr - DISK_IN) / (DISK_OUT - DISK_IN), 0.0, 1.0);
vec3 col = mix(vec3(1.0,0.97,0.90), vec3(1.0,0.52,0.14), smoothstep(0.0,0.30,tt01));
col = mix(col, vec3(0.80,0.18,0.05), smoothstep(0.30,0.75,tt01));
col = mix(col, vec3(0.40,0.05,0.02), smoothstep(0.75,1.0,tt01));
```
Hmm, at tt01 = 0 the color is (1,0.97,0.9) — white hot. Good.

Emission magnitude: `float em = radial * (0.35 + 1.5*n) * 2.0 * edgeIn * edgeOut;` Hmm, and then color * em.

Wait, radial already includes the inner boost. Let's compute `float bright = radial * edgeIn * edgeOut * (0.4 + 1.6*n);`

Then `vec3 emit = col * bright * 3.0;`

Then `color += trans * emit; trans *= (1.0 - alpha);`

Hmm, the emission and alpha both scale with density, which is physically consistent for an emissive medium: emission ∝ density, absorption ∝ density. So emit = col * dens * someScale, and alpha from dens*pf. Actually with a slab, the total emission ∝ density * pathLength, same as alpha. So let's do:

```
float dens = radial * edgeIn * edgeOut * (0.2 + 1.3*n) * pf;  // includes path factor
float alpha = 1.0 - exp(-dens * 1.8);
vec3 emit = col * dens * 2.2;
color += trans * emit;
trans *= (1.0 - alpha);
```
Then emit and alpha are consistent. With dens up to... at rr=3, radial = pow(2.6/3,1.7)=0.79, inner boost *1+1.5*exp(-0.6)=1.82 → 1.44. edgeIn=1, edgeOut=1, n=0.5 → (0.2+0.65)=0.85 → dens = 1.44*0.85*pf. pf at 10° elevation: dY ≈ 0.17 → pf = 0.35/0.17 = 2.06 (capped 5). dens = 2.5. alpha = 1-exp(-4.5) = 0.989. emit = col*2.5*2.2 = col*5.5. col ~ (1,0.9,0.8) → (5.5, 4.9, 4.4). After tone mapping with exposure 1.0: ACES(5.5) ≈ 1.0 → white. Hmm, the inner disk will be blown out white. That might be okay for the inner edge (hot white) but we want orange too. Let's reduce: emit = col * dens * 1.2 → col*3 → ACES(3.0) ≈ 0.93 for the red channel... ACES(3) = (3*(2.51*3+0.03))/(3*(2.43*3+0.59)+0.14) = (3*7.56)/(3*7.88+0.14) = 22.68/23.78 = 0.954. So the red channel is 0.95, green (col.g=0.9 → 2.7) → (2.7*(2.51*2.7+0.03))/(2.7*(2.43*2.7+0.59)+0.14) = (2.7*6.807)/(2.7*7.151+0.14)= 18.38/19.45 = 0.945. So it's nearly white. Slightly orange-white. That's actually what we want for the inner edge.

For the mid disk at rr=6: radial = pow(2.6/6,1.7) = (0.4333)^1.7 = e^{1.7*(-0.836)} = e^{-1.42}=0.24. inner boost: 1+1.5*exp(-5.1)=1.006. → 0.24. edgeIn=1, edgeOut=1. n=0.5 → 0.85. dens = 0.24*0.85*2 = 0.41. alpha = 1-exp(-0.74) = 0.52. emit = col*0.41*1.2 = col*0.49. col at tt01=(6-2.6)/9.4=0.36 → mix between (1,0.52,0.14) at 0.3 and (0.8,0.18,0.05) at 0.75: smoothstep(0.3,0.75,0.36)= smoothstep gives (0.06/0.45)=0.133 → smoothstep = 0.133²*(3-2*0.133)=0.0177*2.73=0.048. So col ≈ (0.99, 0.50, 0.135). emit ≈ (0.48, 0.245, 0.066). After ACES + gamma: ACES(0.48)= (0.48*(2.51*0.48+0.03))/(0.48*(2.43*0.48+0.59)+0.14) = (0.48*1.235)/(0.48*1.756+0.14)= 0.593/0.983 = 0.603. gamma → 0.603^0.4545 = 0.795. Green: 0.245 → ACES = (0.245*(0.615+0.03))/(0.245*(0.595+0.59)+0.14) = (0.245*0.645)/(0.245*1.185+0.14) = 0.158/(0.290+0.14)=0.158/0.430=0.367 → gamma 0.633. Blue: 0.066 → ACES ≈ (0.066*(0.166+0.03))/(0.066*(0.160+0.59)+0.14) = (0.066*0.196)/(0.0495+0.14)=0.0129/0.1895=0.068 → gamma 0.29. So the mid disk is (0.80, 0.63, 0.29) → orange-tan. Good.

At rr=11: radial = pow(0.236,1.7)= e^{1.7*(-1.444)} = e^{-2.45}=0.086. dens = 0.086*0.85*2 = 0.146. alpha = 0.23. emit = col*0.146*1.2 = col*0.175. col at tt01=0.89 → mix toward (0.4,0.05,0.02): smoothstep(0.75,1.0,0.89) = (0.14/0.25)=0.56 → ss=0.56²*(3-1.12)=0.3136*1.88=0.59. col ≈ mix((0.8,0.18,0.05),(0.4,0.05,0.02),0.59) = (0.564, 0.103, 0.032). emit = (0.099, 0.018, 0.0056). ACES(0.099)= (0.099*(0.248+0.03))/(0.099*(0.240+0.59)+0.14)= (0.099*0.278)/(0.0822+0.14)=0.0275/0.222=0.124 → gamma = 0.124^0.4545 = 0.386. Green: 0.018 → ≈ 0.018*... small, ACES(0.018)= (0.018*(0.045+0.03))/(0.018*(0.044+0.59)+0.14)= (0.018*0.075)/(0.0114+0.14)=0.00135/0.1514=0.0089 → gamma = 0.0089^0.4545 = e^{0.4545*ln0.0089} = e^{0.4545*(-4.72)} = e^{-2.146}=0.117. Blue ~0.06. So the outer disk is (0.39, 0.12, 0.06) → dark red. 

Now, the tone-mapped result seems reasonable. Exposure 1.0. Maybe 1.2 to brighten. Let's use 1.15.

Now, the photon ring and glow:

```
// after the loop
float ring = exp(-pow((rMin - 1.52)/0.10, 2.0));
color += trans * vec3(1.0, 0.82, 0.55) * ring * 0.55;
```
Hmm, the ring should be thin: sigma 0.10 in rMin units. rMin varies quickly with impact parameter near the critical value, so this gives a thin ring. But is 0.10 too thick? The relationship between rMin and b near b_c: rMin ≈ 1.5 + something. For b just above b_c = 2.598, the ray winds around and rMin ≈ 1.5. For b = 3.0, rMin ≈ ? Let's approximate: rMin is roughly where the radial motion turns around. For a rough estimate, rMin ~ b for large b. Near b_c, rMin → 1.5. The derivative drMin/db is large near b_c? Actually near b_c, rMin approaches 1.5 asymptotically as the number of windings increases. So a range of rMin from 1.5 to 1.6 corresponds to a range of b from b_c to b_c+ε, with ε small. So the ring in the image is thin. Good. Let's use sigma = 0.06.

But careful: rays that fall in (captured) have rMin → 1.0. Rays that escape with b slightly > b_c have rMin ≈ 1.5. So the ring glow appears right at the shadow edge. 

Also, the disk's lensed image also forms a ring at the shadow edge naturally.

Additional glow around the hole:
```
float glow = exp(-(rMin - 1.0) * 0.9) * 0.10;
color += trans * vec3(1.0, 0.55, 0.25) * glow;
```
Hmm, this adds an orange halo everywhere within a few rs. Might wash things out. Let's make it small: 0.06.

Hmm, also should the glow be added even where trans is low? Multiplying by trans is fine.

Now the background:
```
if (escaped) {
   vec3 d = normalize(dir);
   color += trans * skyColor(d);
}
```
If captured, nothing (black).

If neither (max steps reached): decide by r. Let's add:
```
if (!captured && !escaped) {
   // likely still winding; treat as captured unless far
   float r = length(pos);
   if (r > 6.0) color += trans * skyColor(normalize(dir));
}
```

Hmm, actually if the loop ends due to MAX_STEPS without breaking, we handle it. Let's structure with flags.

Let me restructure the loop to use a `for` with breaks and then handle the background after.

Also note: for captured rays we still might want to add the ring glow... no, the ring is for escaping rays.

Actually, careful: rMin for captured rays goes down to <1, so exp(-((rMin-1.52)/0.06)^2) with rMin=0.5 gives exp(-(17)^2) ≈ 0. Fine.

Now, one more consideration: the disk's inner region should be visible in front of the black hole (the near side crossing in front of the shadow). At our elevation of ~10°, yes.

Let's also double check the "far side bends over and under" effect. With the camera above the plane at 10°, the far side of the disk appears as an arc above the black hole, and due to lensing the underside image appears below. Yes, this is what the geodesic integration produces.

Now let's also double-check the direction of the disk rotation vs the camera orbit — doesn't matter.

Now let's write the star function fully.

```glsl
vec3 dirToFace(vec3 d){
  vec3 a = abs(d);
  if(a.x >= a.y && a.x >= a.z) return vec3(d.z, d.y)/a.x, 0.0);
  ...
}
```
Can't return two things easily. Return a vec3 with the face index in z:

```glsl
vec3 dirToFace(vec3 d){
  vec3 a = abs(d);
  if(a.x >= a.y && a.x >= a.z) return vec3(d.z/a.x, d.y/a.x, d.x > 0.0 ? 0.0 : 1.0);
  if(a.y >= a.z)               return vec3(d.x/a.y, d.z/a.y, d.y > 0.0 ? 2.0 : 3.0);
  return vec3(d.x/a.z, d.y/a.z, d.z > 0.0 ? 4.0 : 5.0);
}
```

Then:
```glsl
vec3 skyColor(vec3 d){
  vec3 f = dirToFace(d);
  vec2 uv = f.xy;
  float seed = f.z * 19.13;

  float s1 = starLayer(uv, 5.0, 0.30, 0.16, seed + 1.0);
  float s2 = starLayer(uv, 12.0, 0.22, 0.10, seed + 7.0);
  float s3 = starLayer(uv, 26.0, 0.16, 0.07, seed + 13.0);

  vec3 col = vec3(0.0);
  col += vec3(1.0, 0.94, 0.85) * s1 * 1.0;
  col += vec3(0.80, 0.88, 1.0) * s2 * 0.75;
  col += vec3(1.0, 1.0, 1.0) * s3 * 0.5;

  // faint galactic haze
  float h = fbm(d * 2.5 + 3.7);
  col += vec3(0.035, 0.045, 0.075) * pow(h, 3.0) * 2.0;

  return col;
}
```
Hmm, the haze uses fbm(d*2.5) which is 4 octaves * 8 hashes = 32 hashes. Fine, done once per escaped ray.

Actually wait — for the haze, I want a subtle Milky Way-like band. Using fbm(d*2.5) gives a blobby pattern. Fine.

Star brightness: a star with b² accumulation. Let's check: for a star at the center of a pixel, dd=0 → b=1 → contributes 1.0. With size 0.16 cell units at scale 5: the cell is 1/5 = 0.2 uv. The star radius is 0.16 cell = 0.032 uv ≈ 0.032 rad ≈ 48 px. That's huge! Too big.

Let's reconsider. size is in cell units (since gv is in [-0.5,0.5] cell units). At scale 5, a cell is 0.2 in uv, so size 0.16 cells = 0.032 uv. As computed, uv ≈ radians near the face center, so 0.032 rad ≈ 0.032 * (screen_height/0.6 rad) ≈ 0.032*1500 = 48 px. Way too big.

I need much smaller sizes. Let's target star radii of ~1-3 px. With ~1500 px/rad, 1 px ≈ 0.00067 rad ≈ 0.00067 uv. At scale 5, cell = 0.2 uv → size in cell units = 0.00067/0.2 = 0.0033. Hmm, that's tiny, and the smoothstep will alias.

Alternative: make the star size in uv space constant, not cell space. I.e., compute the distance in uv space: `dd = length((gv - sp) * cellSizeInUV)`. But the star density per cell would then be high.

Honestly, the simplest approach: use larger scales so cells are small, and use star size as a fraction of the cell. At scale 26, cell = 0.038 uv → star size 0.07 cells = 0.0027 uv ≈ 4 px. That's fine. At scale 12: cell = 0.083, size 0.10 → 0.0083 uv ≈ 12 px. Too big.

So: sizes should be ~0.02-0.06 cells for the coarser layers. Let's set:
- layer 1: scale 6, size 0.02 → 0.0033 uv ≈ 5 px
- layer 2: scale 14, size 0.03 → 0.0021 uv ≈ 3 px
- layer 3: scale 30, size 0.05 → 0.0017 uv ≈ 2.5 px

Hmm, these are all similar sizes. That's fine — stars of 2-5 px. But note the lensing will magnify/demagnify them.

Actually there's another subtlety: the "uv ≈ radians" approximation only holds near the face center. Near the face edges, uv → ∞ (since |d.z|/|d.x| can be large... no wait, for face +x, uv = (d.z/|d.x|, d.y/|d.x|) and both components are ≤ 1 in magnitude since |d.x| is the largest component. So uv ∈ [-1,1]². At the face center, uv=(0,0) and the angle from the face normal is 0. At the face corner, |d.z| = |d.x| = |d.y|, uv = (1,1), the angle from the normal is 54.7°. So the mapping compresses: uv=1 corresponds to 54.7° = 0.955 rad. So near the corners the scale factor is ~0.95 rad per uv unit... Actually, it's tan(θ) = |uv| roughly, so θ = atan(|uv|). At |uv|=1, θ=0.785 rad (45°). Hmm, right: uv = tan(θ) for the radial direction. So dθ/duv = 1/(1+u²), which at u=1 is 0.5. So near the corners, 1 uv unit ≈ 0.5 rad. Fine, within a factor of 2.

So a star size of 0.002 uv ≈ 0.002 rad ≈ 3 px. Good.

Let's also ensure the star layers don't have visible grid artifacts. With smoothstep(size, 0, dd) and b², it's a soft blob. Fine.

Star density: with `if(h.x > density) continue;` and density 0.3, about 30% of cells have a star. At scale 6, the face has 12x12 = 144 cells * 0.3 = 43 stars per face. Across 6 faces = 260 stars. Visible as sparse bright stars. At scale 30, 60x60=3600 cells * 0.16 = 576 per face * 6 = 3456 faint stars. Good.

Total sky: about 3700 stars. The visible FOV covers ~1/20 of the sky, so ~185 stars visible. Good.

Now, the fbm for the haze: `fbm(d*2.5)`. d is a unit vector, so d*2.5 spans a sphere of radius 2.5 — that's only ~5 noise cells across, so the haze is very low frequency. Use d*6.0 for more detail. And pow(h,3)*2 → subtle.

OK. Now let's think about performance again. Per pixel: up to 320 marching steps, each with a length() and a division (pow(r,5)). That's the bulk. Plus disk sampling at crossings (maybe 1-3 per ray) with 4-octave fbm (32 hash13 calls each). Plus star sampling once for escaped rays.

The main cost is the march. Let's reduce MAX_STEPS to 280 and use an adaptive step. Should be OK on a modern GPU at ~1-2 MP.

I'll set the render scale to min(devicePixelRatio, 1.5) but also cap the total pixels at ~2.3M.

Let me write the resize handler:

```js
function resize(){
  const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
  let w = Math.floor(innerWidth * dpr);
  let h = Math.floor(innerHeight * dpr);
  const maxPix = 2400000;
  const pix = w*h;
  if(pix > maxPix){
    const s = Math.sqrt(maxPix/pix);
    w = Math.floor(w*s); h = Math.floor(h*s);
  }
  if(canvas.width !== w || canvas.height !== h){
    canvas.width = w; canvas.height = h;
    gl.viewport(0,0,w,h);
  }
}
```
Call on resize and each frame (cheap check).

Canvas CSS: width 100vw, height 100vh — the canvas is stretched to fill. Since we keep the aspect ratio the same (both scaled), no distortion.

Now the render loop with requestAnimationFrame(timestamp).

Let me write the JS:

```js
const gl = canvas.getContext('webgl2', {antialias:false, alpha:false, depth:false, powerPreference:'high-performance'});
```

Compile the program, set up the VAO/VBO with 6 vertices forming 2 triangles covering [-1,1]².

```js
const quad = new Float32Array([-1,-1, 1,-1, -1,1, -1,1, 1,-1, 1,1]);
const vao = gl.createVertexArray();
gl.bindVertexArray(vao);
const vbo = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
gl.bufferData(gl.ARRAY_BUFFER, quad, gl.STATIC_DRAW);
const loc = gl.getAttribLocation(prog, 'aPos');
gl.enableVertexAttribArray(loc);
gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
```

Then in the loop: `gl.uniform1f(uTimeLoc, t)` where t = timestamp/1000 (maybe modulo something to avoid precision issues after a long time; fract isn't needed but large floats lose precision. Let's use `t = (timestamp - startTime)/1000` and maybe wrap at some large value like 1e5. Fine.)

Hmm, one thing: since the noise is sampled at rotated positions with `omega*t`, and t grows, cos/sin of large arguments lose precision. With t up to 1e5 and omega up to ~0.7, the argument is ~7e4 — cos/sin in highp float should still be OK-ish (highp float has ~7 digits, so 7e4 with 7 digits gives precision ~0.007 rad). Fine for a 30s recording anyway. But let's wrap time: use `float tt = mod(uTime, 1000.0);` — but then the camera orbit also jumps. Hmm, mod 1000 with an orbit period of 2π/0.07 ≈ 90s — the jump would be visible. Just don't wrap; the recording is 30s.

Actually, to be safe for long runs, I'll compute the camera angle and rotation angles in JS with double precision and pass them as uniforms? That's over-engineering. Let's just wrap the time in JS: `t = (timestamp/1000) % 3600` — no visible seam issue for a while. Actually mod 3600 with period... the camera azimuth az = t*0.07, period = 89.8s. A jump at 3600s would be visible but who cares. Fine, use modulo 3600.

Hmm, but the disk noise rotation would also jump. Not a concern for a 30s recording.

Actually, simplest: don't wrap. The floats will be fine for the duration of a recording.

Now let me write the final shader code carefully.

One more detail: `h2 = dot(cross(pos,dir), cross(pos,dir))` — compute once at the start. Since the acceleration is radial, the angular momentum is conserved exactly by the ODE, but numerically with Euler steps it might drift slightly. Recomputing h2 each step would be more stable? Actually the ODE requires h2 to be the conserved quantity; recomputing each step from the current state gives a value that should be nearly constant anyway. Let's just compute it once — standard practice.

Now let's write it.

```glsl
#version 300 es
precision highp float;
precision highp int;

out vec4 fragColor;

uniform vec2  uRes;
uniform float uTime;

const float PI = 3.14159265359;
const float DISK_IN  = 2.55;
const float DISK_OUT = 12.0;

// ============ hashing / noise ============
float hash13(vec3 p3){
  p3 = fract(p3 * 0.1031);
  p3 += dot(p3, p3.zyx + 31.32);
  return fract((p3.x + p3.y) * p3.z);
}
vec2 hash22(vec2 p){
  vec3 p3 = fract(vec3(p.xyx) * vec3(0.1031, 0.1030, 0.0973));
  p3 += dot(p3, p3.yzx + 33.33);
  return fract((p3.xx + p3.yz) * p3.zy);
}
float vnoise(vec3 x){ ... }
float fbm(vec3 p){ ... }
```

I'll write the full thing now.

For the disk crossing, I also want to handle the case where the ray passes very close to the plane without crossing (grazing) — ignore.

Another consideration: the disk should also be "seen" by rays that are inside the disk plane region but never cross y=0 because the camera is exactly in the plane — not our case.

Let me now write out the entire fragment shader main:

```glsl
void main(){
  vec2 uv = (gl_FragCoord.xy - 0.5*uRes) / uRes.y;
  float t = uTime;

  // ---- camera ----
  float camDist = 16.0;
  float az = t * 0.065;
  float el = 0.16 + 0.085 * sin(t * 0.037);
  vec3 camPos = vec3(cos(el)*cos(az), sin(el), cos(el)*sin(az)) * camDist;
  vec3 fwd = -normalize(camPos);
  vec3 right = normalize(cross(fwd, vec3(0.0, 1.0, 0.0)));
  vec3 up = cross(right, fwd);
  vec3 rd = normalize(uv.x * right + uv.y * up + 1.55 * fwd);

  vec3 pos = camPos;
  vec3 dir = rd;
  vec3 L = cross(pos, dir);
  float h2 = dot(L, L);

  vec3 col = vec3(0.0);
  float trans = 1.0;
  float rMin = 1e5;
  bool captured = false;
  bool escaped  = false;

  for(int i = 0; i < 300; i++){
    float r = length(pos);
    rMin = min(rMin, r);
    if(r < 1.0){ captured = true; break; }
    if(r > 45.0){ escaped = true; break; }

    vec3 prevPos = pos;
    vec3 prevDir = dir;

    float dt = clamp(0.05 * r, 0.035, 0.9);
    vec3 acc = -1.5 * h2 * pos / (r*r*r*r*r);
    dir += acc * dt;
    pos += dir * dt;

    if(prevPos.y * pos.y < 0.0){
      float k = prevPos.y / (prevPos.y - pos.y);
      vec3 hit = mix(prevPos, pos, k);
      float rr = length(hit.xz);
      if(rr > DISK_IN && rr < DISK_OUT){
        float dY = abs(mix(prevDir.y, dir.y, k));
        float pf = clamp(0.30 / max(dY, 0.02), 0.4, 4.5);

        float om = 1.9 / pow(rr, 1.5);
        float a  = om * t;
        float ca = cos(a), sa = sin(a);
        vec3 pr = vec3(ca*hit.x - sa*hit.z, 0.0, sa*hit.x + ca*hit.z);
        float n = fbm(pr * 0.5);
        n = pow(n, 1.6);   // hmm, careful: fbm returns ~0..1 with mean 0.5

        float x = (rr - DISK_IN) / (DISK_OUT - DISK_IN);
        float radial = pow(DISK_IN / rr, 1.7);
        radial *= 1.0 + 1.6 * exp(-(rr - DISK_IN) * 1.6);
        float edgeIn  = smoothstep(DISK_IN, DISK_IN + 0.30, rr);
        float edgeOut = 1.0 - smoothstep(DISK_OUT * 0.62, DISK_OUT, rr);
        float shape = radial * edgeIn * edgeOut;

        float dens = shape * (0.18 + 1.5 * n) * pf;
        float alpha = 1.0 - exp(-dens * 1.6);
        vec3 col_disk = diskColor(x);
        vec3 emit = col_disk * dens * 1.3;
        col += trans * emit;
        trans *= (1.0 - alpha);
        if(trans < 0.004) break;
      }
    }
  }

  // photon ring / glow
  float ring = exp(-pow((rMin - 1.53) / 0.075, 2.0));
  col += trans * vec3(1.0, 0.85, 0.60) * ring * 0.9;
  col += trans * vec3(1.0, 0.5, 0.22) * exp(-max(rMin - 1.0, 0.0) * 1.2) * 0.045;

  if(!captured){
    if(escaped || length(pos) > 5.0){
      col += trans * skyColor(normalize(dir));
    }
  }

  col *= 1.15;
  col = aces(col);
  col = pow(col, vec3(1.0/2.2));
  fragColor = vec4(col, 1.0);
}
```

Wait, there's a bug: `if(trans < 0.004) break;` inside the disk-crossing block — that breaks the marching loop, leaving `captured`/`escaped` both false. Then the background check: `if(!captured && (escaped || length(pos) > 5.0))` — if we broke early, pos is near the disk, length(pos) > 5 possibly. But trans is ~0, so it doesn't matter. Fine.

Also, the `escaped` flag: `if(r > 45.0)`. But we start at r=16, so the escape radius of 45 requires traveling 29 units outward. With dt capped at 0.9, that's ~32 steps after leaving the disk region. Acceptable. Actually, we could reduce it to r > 25 to save steps. But rays that are bent might still be near the hole... if r > 25 and moving outward, it's fine. But if the ray is moving inward from 25, it's not escaping. Hmm, at r > 25 the deflection is tiny; the ray is essentially straight. So we could check `if(r > 22.0 && dot(pos, dir) > 0.0) escaped = true;`. That saves a lot of steps. Let's do that.

Actually careful: `dot(pos,dir) > 0` means moving outward. At r>22, the ray is essentially free. Good.

Let's use: `if(r > 24.0 && dot(pos,dir) > 0.0){ escaped = true; break; }`.

Hmm, but there's a subtlety: what if the ray is at r=24 moving outward but the deflection would have curved it back? At r=24, the deflection is negligible (the total deflection for b=3 is ~ a few radians, but the deflection accumulates mostly near the hole; at r=24 the remaining deflection is tiny). Fine.

Also the initial camera distance is 16, so the ray starts inside the 24 radius. It'll take ~10 steps to get to 24. Fine.

Hmm, but with the camera at 16 and the disk outer radius at 12, rays going toward the disk take a while. Fine.

Let's now double check the step size near the camera: dt = 0.05*16 = 0.8, capped at 0.9. So 0.8. Distance from 16 to ~3 is 13 → ~17 steps. OK.

Accuracy concern: with dt=0.8 at r=16, the ray direction changes by |acc|*dt = 1.5*h2/r^4 * dt. With h2 ~ (16*sinθ)² where θ is the angle between pos and dir... For a ray heading toward the hole, h ≈ b ≈ 3, so h2 = 9. acc = 1.5*9/16^4 = 13.5/65536 = 2e-4. Times dt=0.8 → 1.7e-4 change in direction per step. Negligible. Good.

Now, an important detail: the camera's "up" vector when the camera is near the disk plane. Since el > 0 always (0.16 - 0.085 = 0.075 rad min), we never have a degenerate case. Good.

Now `diskColor(x)`:

```glsl
vec3 diskColor(float x){
  vec3 c = mix(vec3(1.0, 0.98, 0.92), vec3(1.0, 0.55, 0.15), smoothstep(0.0, 0.28, x));
  c = mix(c, vec3(0.85, 0.20, 0.05), smoothstep(0.28, 0.72, x));
  c = mix(c, vec3(0.42, 0.06, 0.02), smoothstep(0.72, 1.0, x));
  return c;
}
```

Now, `n = pow(fbm(...), 1.6)` — fbm returns values roughly in 0..1 with a mean of ~0.5. pow(0.5, 1.6) = 0.33. Then dens = shape*(0.18+1.5*0.33)*pf = shape*0.675*pf. Hmm, that reduces the brightness compared to my earlier estimate. Let's not apply pow; just use n directly. Then the density modulation is (0.18 + 1.5n) which ranges 0.18..1.68 with a mean of ~0.93.

But we want contrast (turbulence). Let's use `n = smoothstep(0.25, 0.85, fbm(...))` to increase contrast. Then n ∈ 0..1 with more extremes. Then dens = shape * (0.12 + 1.5*n) * pf.

Hmm, actually maybe better: use two noise scales — a large-scale one for the overall brightness and a fine one for filaments. Let's do:

```
float n1 = fbm(pr * 0.35);          // large scale
float n2 = fbm(pr * 1.3 + 11.0);    // fine scale
float n = mix(n1, n2, 0.35);
n = smoothstep(0.22, 0.85, n);
```
That's 8 octaves total = 64 hash calls per crossing. Times up to 3 crossings = 192. Plus the march. Hmm, it's heavy but probably OK. Let's use 3 octaves for fbm instead of 4 to save some. Actually, let me use a single fbm with 4 octaves and a contrast curve — cheaper and looks fine.

`float n = fbm(pr * 0.55); n = smoothstep(0.25, 0.9, n);`

Hmm, the smoothstep edges depend on the fbm distribution. Value noise fbm typically has values concentrated around 0.5 with a range of maybe 0.15-0.85. So smoothstep(0.25,0.9) maps that to ~0..0.9. Reasonable contrast.

Let's go with that.

Also, I want the inner disk to look "hot" with more contrast — the inner region is hotter and more turbulent. Fine as is.

Now, there's another visual element: the disk should have a bright inner edge ring visible. Handled by the radial boost.

Let me reconsider `pf` (path factor). When the camera is at 10° elevation and looking at the disk, dY ≈ 0.17 → pf = 0.3/0.17 = 1.76. For rays that graze the disk plane (the lensed far side), dY could be very small → pf up to 4.5. That creates bright arcs where the disk is seen edge-on. Good.

But careful: for the direct view of the disk's near side (front), the ray hits the plane at a steep-ish angle... no, at 10° elevation, all rays hit the plane at ~10° except those that are bent. So the whole disk has a similar pf. Fine.

Now, the alpha accumulation with a single crossing gives a max alpha of 1-exp(-dens*1.6). For the outer disk (dens ~0.15), alpha ~0.21. With 2-3 crossings, the accumulated opacity is higher. Fine.

Now let's also double-check the case where the ray crosses the disk plane outside DISK_OUT (rr > 12): we skip, no accumulation. Good. And rr < DISK_IN: skip (the hole region). Good.

Now the sky. Let's write it.

Also, I should double check the `dirToFace` function for the case a.x >= a.y && a.x >= a.z — the first branch. Fine.

Let me finalize the star layer sizes: since I estimated uv ≈ radians near the face center, and the screen is ~0.6 rad tall for ~900 px, then 1 uv ≈ 1 rad ≈ 1500 px near the center. Star radius target ~2-3 px → 0.0015-0.002 uv.

- Layer A: scale 6 → cell 0.1667 uv; size 0.012 cells → 0.002 uv ≈ 3 px. Density 0.25.
- Layer B: scale 14 → cell 0.0714; size 0.028 → 0.002 uv ≈ 3 px. Density 0.2.
- Layer C: scale 30 → cell 0.0333; size 0.06 → 0.002 uv ≈ 3 px. Density 0.15.

Hmm, all the same apparent size. That's fine, but the smoothstep with a very small size relative to the cell means the star is a tiny dot — at high resolution this could alias. Let's make them slightly bigger: 0.004 uv ≈ 6 px for the brightest layer, 0.0025 for the faint ones.

Actually, for a nicer look, bright stars slightly larger, faint ones smaller:
- Layer A: scale 5, size 0.025 (→ 0.005 uv ≈ 7px), density 0.3, brightness 1.0
- Layer B: scale 11, size 0.035 (→ 0.0032 uv ≈ 5px), density 0.22, brightness 0.6
- Layer C: scale 24, size 0.05 (→ 0.002 uv ≈ 3px), density 0.18, brightness 0.35

The star "radius" here is where the smoothstep reaches 0; with b², the visible core is smaller. OK.

Hmm, the 7px stars might look like blobs. Let's reduce layer A to size 0.02 → 0.004 uv ≈ 6 px. With b² the visible core is ~2-3 px. Good.

Alright. Let's also make the star intensity vary more: `acc += b*b*(0.15 + 0.85*h.y)`.

Now writing everything out.

One more thing: the "thin photon ring". Let me also add a subtle secondary consideration — the photon ring should be visible even when the disk is not behind. It's fine.

Let me also consider: should the disk occlude the stars behind it? Yes, via `trans`.

Let me also make sure the shadow is truly pitch black: captured rays get col = 0 + ring contributions (which are ~0 for rMin < 1.4). Actually for captured rays, rMin → 1.0, so exp(-((1.0-1.53)/0.075)^2) = exp(-50) ≈ 0. Good. And the glow term exp(-(rMin-1.0)*1.2) at rMin=1.0 is exp(0)=1 → 0.045 * orange. That would make the shadow not black! Hmm. For captured rays, rMin can be 0.9 (we break at r<1). exp(-(0.9-1)*1.2)= exp(0.12)=1.13 → glow 0.05. That's a dim orange glow inside the shadow. Not good.

Let me change the glow to depend on rMin being > 1.5-ish: `float glow = exp(-max(rMin - 1.4, 0.0) * 1.2) * 0.05;` — for rMin=0.9, max(...,0)=0 → glow=0.05. Still 0.05. Hmm.

Better: make the glow ∝ smoothstep to kill it for captured rays. Or just drop the extra glow entirely and rely on the ring. Actually, a soft halo around the hole is nice, but it should come from the ring itself. Let's use:

```
float ring = exp(-pow((rMin - 1.53)/0.09, 2.0));
col += trans * vec3(1.0, 0.85, 0.62) * ring * 0.8;
```
and a wider halo:
```
float halo = exp(-pow((rMin - 1.53)/0.45, 2.0));
col += trans * vec3(1.0, 0.55, 0.25) * halo * 0.05;
```
For rMin = 0.9: ((0.9-1.53)/0.45)² = (−1.4)² = 1.96 → exp(-1.96)=0.14 → 0.007. Small enough. But hmm, for captured rays rMin can be anywhere from 0 to 1. At rMin = 1.0: ((1-1.53)/0.45)² = 1.39 → exp = 0.25 → 0.0125. Slight glow inside the shadow edge. That's actually physically plausible (the shadow edge isn't perfectly sharp in a real render). But it should be very subtle. 0.0125 in linear → after ACES+gamma ≈ 0.15 gray-orange. Hmm, that's visible. Let's reduce to 0.03 → 0.0075 → gamma ~0.11. Hmm, still visible but that's at the very edge of the shadow, which is fine and even desirable (the photon ring is bright there anyway).

Actually, wait. The halo term should really only apply to rays that escape or pass near. Let's multiply the halo by a factor that goes to zero for captured rays: since the ring is at rMin ≈ 1.5, and captured rays have rMin < 1.0, the Gaussian with sigma 0.45 gives a value of 0.14 at rMin=0.9, which is 14% of the max. It's a smooth falloff. It's fine. I'll use 0.04 amplitude.

Hmm, but actually there's a subtlety: rays that are captured have rMin approaching 0 (they fall in), but we break at r < 1.0, so rMin ∈ [0.9-ish, 1.0]. Actually, rMin is the min over the sampled positions, and we break when r < 1.0, so rMin is somewhere just below 1.0, like 0.95. So all captured rays have rMin ≈ 0.95. Then the halo value is constant across the shadow → a uniform glow across the whole shadow, not a falloff! That's bad — it would make the shadow uniformly dark-orange instead of pitch black.

Right! Because rMin for captured rays is always ~0.95 (the last step before breaking). So the halo term would be a constant 0.14*0.04 = 0.0056 across the entire shadow. That's a uniform dim glow over the shadow. After tone mapping: 0.0056 → ACES ≈ 0.0056*... roughly linear at small values: ACES(0.0056) ≈ (0.0056*(0.014+0.03))/(0.0056*(0.0136+0.59)+0.14) = (0.0056*0.044)/(0.1434) = 0.000246/0.1434 = 0.0017 → gamma: 0.0017^0.4545 = e^{0.4545*(-6.38)} = e^{-2.9} = 0.055. So a dark gray of 0.055 — noticeable but subtle. Still, "pitch-black event horizon" is required.

Better: only apply the ring/halo when the ray escapes (or at least when rMin > 1.2). Let's gate it: multiply by `step(1.15, rMin)`. Or simply compute the ring only if !captured. Since captured rays are exactly those with rMin < 1.0, and rays near the critical impact parameter have rMin ≈ 1.5. Rays that escape with small b (like b = 2.7) have rMin ~1.5. Rays that escape with large b have larger rMin. So gating on !captured is fine — but then the ring's inner edge is exactly the shadow boundary. 

Let's do:
```
float ringMask = captured ? 0.0 : 1.0;
```
and apply. Hmm, but rays that hit MAX_STEPS... they're near the photon sphere, rMin ~1.5, so the ring would appear. Those are fine (they're effectively captured, so their color is black except the ring). Hmm, rays that exhaust steps are those that wind a lot — they'd be black. Adding a ring there is consistent with the ring being at the shadow edge.

OK: apply the ring/halo only when !captured. And multiply the halo by a mask.

Actually, simpler: since captured rays have rMin ∈ [0.9,1.0] and escaping rays near the photon sphere have rMin ≈ 1.5+, using a narrow Gaussian for the ring (sigma 0.075) centered at 1.53 means captured rays get exp(-((0.95-1.53)/0.075)²) = exp(-59.8) ≈ 0. So the ring is fine without gating. Only the wide halo is problematic. Let's just make the halo narrower or gate it.

I'll gate both with `captured ? 0.0 : 1.0` for safety, and use a narrow halo (sigma 0.3, amplitude 0.05).

Hmm, but for rays that reach MAX_STEPS and are effectively captured, we'd add the ring. Those rays have rMin ~1.5, so they're at the ring — fine.

Alright, but hold on: is the region just inside the shadow edge (rays captured with b slightly less than b_c) going to be black? Yes. Good — pitch black.

Now, let me reconsider whether the photon ring should be a hard thin ring. In real renders, the photon ring is a thin bright ring formed by the disk's light. Our added ring is a synthetic glow. Adding it with amplitude 0.8 gives a bright thin ring. Good.

Let me now also think about the starfield distortion near the ring: automatic.

Let's write the final code.

Also, one more thought on `escaped`: for rays that escape, we use `normalize(dir)`. But dir's magnitude changes during the march (it's not unit). normalize handles it.

Let me now write out the whole file.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Black Hole — WebGL2</title>
<style>
  html,body{margin:0;padding:0;width:100%;height:100%;background:#000;overflow:hidden}
  canvas{display:block;width:100vw;height:100vh;background:#000}
</style>
</head>
<body>
<canvas id="glcanvas"></canvas>
<script>
(function(){
  "use strict";
  const canvas = document.getElementById('glcanvas');
  const gl = canvas.getContext('webgl2', {antialias:false, alpha:false, depth:false, stencil:false, powerPreference:'high-performance'});
  if(!gl){ document.body.innerHTML = '<div style="color:#888;font:14px sans-serif;padding:20px">WebGL2 is not available in this browser.</div>'; return; }

  const vsSrc = `#version 300 es
  in vec2 aPos;
  void main(){ gl_Position = vec4(aPos, 0.0, 1.0); }
  `;

  const fsSrc = `#version 300 es
  precision highp float;
  ...
  `;
  ...
})();
</script>
</body>
</html>
```

Let me write the full fragment shader text now, carefully.

```glsl
#version 300 es
precision highp float;

out vec4 fragColor;

uniform vec2  uRes;
uniform float uTime;

const float DISK_IN  = 2.55;
const float DISK_OUT = 12.0;

/* ---------- hash ---------- */
float hash13(vec3 p3){
  p3 = fract(p3 * 0.1031);
  p3 += dot(p3, p3.zyx + 31.32);
  return fract((p3.x + p3.y) * p3.z);
}
vec2 hash22(vec2 p){
  vec3 p3 = fract(vec3(p.xyx) * vec3(0.1031, 0.1030, 0.0973));
  p3 += dot(p3, p3.yzx + 33.33);
  return fract((p3.xx + p3.yz) * p3.zy);
}

/* ---------- value noise ---------- */
float vnoise(vec3 x){
  vec3 i = floor(x);
  vec3 f = fract(x);
  f = f * f * (3.0 - 2.0 * f);
  float n000 = hash13(i + vec3(0.0, 0.0, 0.0));
  float n100 = hash13(i + vec3(1.0, 0.0, 0.0));
  float n010 = hash13(i + vec3(0.0, 1.0, 0.0));
  float n110 = hash13(i + vec3(1.0, 1.0, 0.0));
  float n001 = hash13(i + vec3(0.0, 0.0, 1.0));
  float n101 = hash13(i + vec3(1.0, 0.0, 1.0));
  float n011 = hash13(i + vec3(0.0, 1.0, 1.0));
  float n111 = hash13(i + vec3(1.0, 1.0, 1.0));
  return mix(mix(mix(n000, n100, f.x), mix(n010, n110, f.x), f.y),
             mix(mix(n001, n101, f.x), mix(n011, n111, f.x), f.y), f.z);
}

float fbm(vec3 p){
  float s = 0.0;
  float a = 0.5;
  for(int i = 0; i < 4; i++){
    s += a * vnoise(p);
    p = p * 2.03 + vec3(13.7, 7.3, 5.1);
    a *= 0.5;
  }
  return s * 1.0667; // /0.9375
}
```

1/0.9375 = 1.0667. OK.

```glsl
/* ---------- starfield ---------- */
vec3 dirToFace(vec3 d){
  vec3 a = abs(d);
  if(a.x >= a.y && a.x >= a.z) return vec3(d.z / a.x, d.y / a.x, d.x > 0.0 ? 0.0 : 1.0);
  if(a.y >= a.z)               return vec3(d.x / a.y, d.z / a.y, d.y > 0.0 ? 2.0 : 3.0);
  return vec3(d.x / a.z, d.y / a.z, d.z > 0.0 ? 4.0 : 5.0);
}

float starLayer(vec2 uv, float scale, float density, float size, float seed){
  vec2 p  = uv * scale;
  vec2 id = floor(p);
  vec2 gv = fract(p) - 0.5;
  float acc = 0.0;
  for(int j = -1; j <= 1; j++){
    for(int i = -1; i <= 1; i++){
      vec2 o  = vec2(float(i), float(j));
      vec2 h  = hash22(id + o + seed);
      if(h.x > density) continue;
      vec2 sp = o + (h - 0.5) * 0.85;
      float dd = length(gv - sp);
      float b  = smoothstep(size, 0.0, dd);
      acc += b * b * (0.15 + 0.85 * h.y);
    }
  }
  return acc;
}

vec3 skyColor(vec3 d){
  vec3 f = dirToFace(d);
  vec2 uv = f.xy;
  float seed = f.z * 37.0;

  float s1 = starLayer(uv,  5.0, 0.30, 0.020, seed + 1.7);
  float s2 = starLayer(uv, 11.0, 0.22, 0.035, seed + 9.3);
  float s3 = starLayer(uv, 24.0, 0.18, 0.055, seed + 21.1);

  vec3 col = vec3(0.0);
  col += vec3(1.00, 0.93, 0.82) * s1 * 1.10;
  col += vec3(0.82, 0.89, 1.00) * s2 * 0.65;
  col += vec3(1.00, 1.00, 1.00) * s3 * 0.35;

  float h = fbm(d * 6.0 + 4.3);
  col += vec3(0.030, 0.040, 0.070) * pow(h, 3.0) * 2.2;

  return col;
}
```

Wait: hash22(id + o + seed) — seed is a float, and id+o is a vec2, so `id + o + seed` broadcasts seed to both components. That's fine but it means the same seed offset for both x and y — fine.

Hmm, one issue: `if(h.x > density) continue;` — the loop variable is used in a conditional continue; GLSL ES 3.0 allows continue. Fine.

Now the disk color function and main.

Let me write main:

```glsl
vec3 diskColor(float x){
  vec3 c = mix(vec3(1.00, 0.97, 0.90), vec3(1.00, 0.55, 0.15), smoothstep(0.00, 0.28, x));
  c = mix(c, vec3(0.88, 0.21, 0.05), smoothstep(0.28, 0.72, x));
  c = mix(c, vec3(0.42, 0.06, 0.02), smoothstep(0.72, 1.00, x));
  return c;
}

vec3 aces(vec3 x){
  return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0);
}

void main(){
  vec2 uv = (gl_FragCoord.xy - 0.5 * uRes) / uRes.y;
  float t = uTime;

  /* --- camera --- */
  float camDist = 16.0;
  float az = t * 0.065;
  float el = 0.16 + 0.085 * sin(t * 0.037);
  vec3 camPos = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az)) * camDist;
  vec3 fwd    = -normalize(camPos);
  vec3 right  = normalize(cross(fwd, vec3(0.0, 1.0, 0.0)));
  vec3 up     = cross(right, fwd);
  vec3 rayDir = normalize(uv.x * right + uv.y * up + 1.55 * fwd);

  vec3 pos = camPos;
  vec3 dir = rayDir;
  vec3 Lv  = cross(pos, dir);
  float h2 = dot(Lv, Lv);

  vec3  col   = vec3(0.0);
  float trans = 1.0;
  float rMin  = 1e5;
  bool  captured = false;
  bool  escaped  = false;

  for(int i = 0; i < 300; i++){
    float r = length(pos);
    rMin = min(rMin, r);

    if(r < 1.0){ captured = true; break; }
    if(r > 24.0 && dot(pos, dir) > 0.0){ escaped = true; break; }

    vec3 prevPos = pos;
    vec3 prevDir = dir;

    float dt = clamp(0.05 * r, 0.03, 0.85);
    vec3 acc = -1.5 * h2 * pos / (r * r * r * r * r);
    dir += acc * dt;
    pos += dir * dt;

    if(prevPos.y * pos.y < 0.0){
      float k = prevPos.y / (prevPos.y - pos.y);
      vec3 hit = mix(prevPos, pos, k);
      float rr = length(hit.xz);
      if(rr > DISK_IN && rr < DISK_OUT){
        float dY = abs(mix(prevDir.y, dir.y, k));
        float pf = clamp(0.30 / max(dY, 0.02), 0.4, 4.5);

        float om = 1.9 / pow(rr, 1.5);
        float a  = om * t;
        float ca = cos(a), sa = sin(a);
        vec3  pr = vec3(ca * hit.x - sa * hit.z, 0.0, sa * hit.x + ca * hit.z);

        float n = fbm(pr * 0.55);
        n = smoothstep(0.22, 0.88, n);

        float x = (rr - DISK_IN) / (DISK_OUT - DISK_IN);
        float radial = pow(DISK_IN / rr, 1.7) * (1.0 + 1.7 * exp(-(rr - DISK_IN) * 1.6));
        float edgeIn  = smoothstep(DISK_IN, DISK_IN + 0.30, rr);
        float edgeOut = 1.0 - smoothstep(DISK_OUT * 0.62, DISK_OUT, rr);
        float shape = radial * edgeIn * edgeOut;

        float dens  = shape * (0.15 + 1.55 * n) * pf;
        float alpha = 1.0 - exp(-dens * 1.6);

        col   += trans * diskColor(x) * dens * 1.35;
        trans *= (1.0 - alpha);

        if(trans < 0.003) break;
      }
    }
  }

  if(!captured){
    float ring = exp(-pow((rMin - 1.53) / 0.075, 2.0));
    float halo = exp(-pow((rMin - 1.53) / 0.32, 2.0));
    col += trans * vec3(1.0, 0.86, 0.62) * ring * 0.85;
    col += trans * vec3(1.0, 0.55, 0.26) * halo * 0.06;
  }

  if(!captured && (escaped || length(pos) > 6.0)){
    col += trans * skyColor(normalize(dir));
  }

  col *= 1.15;
  col = aces(col);
  col = pow(col, vec3(1.0 / 2.2));
  fragColor = vec4(col, 1.0);
}
```

Hmm, one issue: if the loop exits because of `trans < 0.003`, then `captured` and `escaped` are false, and `length(pos) > 6.0` might be true, so we'd add the sky... but trans ≈ 0, so no effect. Good.

Another issue: if the loop exits normally (i reaches 300) with r between 1 and 24 and moving inward, then captured=false, escaped=false, and length(pos) could be > 6 → we'd add the sky with the current trans. If trans is high (ray didn't hit the disk), we'd show stars where there should be black. This happens for rays that wind many times — those have rMin ~1.5, so pos could be anywhere with r ~ 1.5-3, meaning length(pos) < 6 → no sky → black. Good, that's the desired behavior (they're effectively captured).

Hmm, but wait: those rays have rMin ~1.5 and we add the ring glow. That's the photon ring region. Good.

Another consideration: the check `r > 24.0 && dot(pos,dir) > 0.0`. At the start, the camera is at r=16, so the first steps have r < 24. But some rays (pointing away from the hole) immediately go outward and reach r=24 after ~10 steps. Fine.

Hmm, wait: there's an important detail. The initial ray direction is normalized, so |dir| = 1 initially. After the acceleration, |dir| changes. For rays that go outward, the acceleration is tiny. Fine.

Now, another important check: `h2` — at the camera position r=16, with the ray pointing at the hole, h = |pos × dir| ≈ 16 * sin(angle between). For a ray pointing directly at the center, h=0 → no deflection → straight into the hole. Correct.

Now let me double check the accretion disk's inner radius vs. the shadow. DISK_IN = 2.55, and the shadow's apparent radius is 2.6 rs. So the disk's inner edge is just inside the apparent shadow radius... The disk's inner edge at r=2.55 will be partially hidden behind the shadow for the near side? No — the near side of the disk at r=2.55 is in front of the hole, closer to the camera. It will appear in front of the shadow. The far side at r=2.55 is behind, and its lensed image appears near the ring.

Hmm, in the Interstellar image, the inner edge of the disk is at the ISCO = 6M = 3 rs for a non-spinning BH. Using 2.55 is slightly inside the ISCO, but visually fine. Let's use 2.7 for a bit more clearance from the photon ring. Actually, having the disk's inner edge close to the photon sphere makes for a more dramatic, brighter ring. Let's keep 2.6.

Hmm, one thing to consider: with DISK_IN = 2.6 and the shadow's apparent radius 2.598, the near-side inner edge of the disk (which is at the closest point to the camera, r=2.6 from the center, at distance ~16-2.6 = 13.4 from the camera, projected onto the screen) appears at an angular offset of ~2.6/13.4 = 0.194 rad, vs the shadow radius of 0.162 rad. So the near inner edge is just outside the shadow. Good, and the far inner edge gets lensed into the ring region.

OK.

Now let's double check `smoothstep(DISK_OUT * 0.62, DISK_OUT, rr)` = smoothstep(7.44, 12, rr). So the disk fades from r=7.4 to 12. Combined with radial = (2.6/r)^1.7, which at 12 is 0.074, the outer part is dim. The fade might make it too dim. Let's use smoothstep(DISK_OUT*0.7, DISK_OUT, rr) = (8.4, 12). Meh, either is fine. I'll use 0.65.

Now, about "cooler red outer regions": with the color ramp going to (0.42,0.06,0.02) at the outer edge, yes.

Now let's think about whether the disk will be visible at all given the camera elevation of ~9-14°. The disk is a thin plane; at 10° elevation we see it as a thin ellipse — good, that's the Interstellar look.

One more consideration: the disk's emission should also illuminate... no, keep it simple.

Let's now think about the starfield brightness. Stars: s1 accumulates b*b*(0.15+0.85*h.y) over 9 neighbors, but only one star is typically near. Max ~1.0*1.0 = 1.0. Then col += (1,0.93,0.82)*1.0*1.1 = ~1.1. After exposure 1.15 and ACES: ACES(1.26) = (1.26*(3.16+0.03))/(1.26*(3.06+0.59)+0.14) = (1.26*3.19)/(1.26*3.65+0.14)=4.02/4.74=0.848 → gamma → 0.928. Bright white star. Good.

The faint layer s3: 0.35 max → after ACES ~0.35*... ACES(0.35) ≈ (0.35*(0.878+0.03))/(0.35*(0.85+0.59)+0.14) = (0.35*0.908)/(0.504+0.14) = 0.318/0.644 = 0.494 → gamma 0.72. Hmm, that's bright for a "faint" star. The issue is that b*b reaches 1.0 at the star center. Most pixels won't be at the center though. But it means faint stars are still quite visible at their cores. That's fine, actually — stars should be visible.

But maybe I should reduce the amplitudes: s1*1.0, s2*0.5, s3*0.25. Let's keep as is-ish.

Now, the haze: vec3(0.03,0.04,0.07)*pow(h,3)*2.2. pow(h,3) with h~0.5 → 0.125. So ~0.03*0.125*2.2 = 0.008 in linear → after ACES ~0.008 → gamma 0.008^0.4545 = e^{0.4545*(-4.83)} = e^{-2.2} = 0.11. Hmm, that's a visible gray-blue haze of 11% brightness. That might be too much — it would lift the blacks. Let's reduce the amplitude: 0.5 instead of 2.2 → 0.002 linear → gamma ≈ 0.06. Still visible. Let's use 0.8. Hmm.

Actually, the background sky shouldn't be pitch black — a faint haze is nice. But the requirement says the event horizon is pitch black, not the sky. A faint star haze in the background is fine. Let's use amplitude 1.0 with the color (0.03,0.04,0.07): at h=0.5, we get 0.03*0.125*1.0 = 0.00375 → gamma ≈ 0.08. Subtle. Good.

Hmm, but wait: the haze is added to the sky, and the sky is only visible where the ray escapes. Good.

Let me also reconsider: pow(h,3) where h can be up to ~0.85 → 0.61. So the brightest haze patches are 0.03*0.61 = 0.018 → gamma 0.16. That's a visible nebula patch. Fine.

Now, let's finalize the JS.

```js
function compile(type, src){
  const s = gl.createShader(type);
  gl.shaderSource(s, src);
  gl.compileShader(s);
  if(!gl.getShaderParameter(s, gl.COMPILE_STATUS)){
    console.error(gl.getShaderInfoLog(s));
    throw new Error('shader compile error');
  }
  return s;
}
```

Program linking, uniform locations.

Then:

```js
const prog = ...;
gl.useProgram(prog);
const uRes = gl.getUniformLocation(prog, 'uRes');
const uTime = gl.getUniformLocation(prog, 'uTime');

const vao = gl.createVertexArray();
gl.bindVertexArray(vao);
const vbo = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 3,-1, -1,3]), gl.STATIC_DRAW);
```
A single big triangle covering the screen: vertices (-1,-1), (3,-1), (-1,3). That covers the whole [-1,1]² quad. Nice and simple.

```js
const aPos = gl.getAttribLocation(prog, 'aPos');
gl.enableVertexAttribArray(aPos);
gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);
```

Resize:

```js
let W = 0, H = 0;
function resize(){
  const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
  let w = Math.max(1, Math.floor(window.innerWidth * dpr));
  let h = Math.max(1, Math.floor(window.innerHeight * dpr));
  const maxPix = 2300000;
  if(w * h > maxPix){
    const s = Math.sqrt(maxPix / (w * h));
    w = Math.max(1, Math.floor(w * s));
    h = Math.max(1, Math.floor(h * s));
  }
  if(w !== W || h !== H){
    W = w; H = h;
    canvas.width = w; canvas.height = h;
    gl.viewport(0, 0, w, h);
  }
}
window.addEventListener('resize', resize);
resize();
```

Render loop:

```js
let start = null;
function frame(ts){
  if(start === null) start = ts;
  const t = (ts - start) * 0.001;
  resize();
  gl.uniform2f(uRes, W, H);
  gl.uniform1f(uTime, t);
  gl.drawArrays(gl.TRIANGLES, 0, 3);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
```

Note: gl.drawArrays needs the VAO bound and the program in use — set once outside the loop. But resize() doesn't change those. Fine.

Hmm: `gl.uniform2f(uRes, W, H)` — but the canvas may have been resized to a different W,H in resize() (if the window changed). We call resize() before setting the uniform, and resize updates W,H. Good.

Now, let's double check the disk turbulence rotation direction and the "disk rotates" requirement. The noise pattern rotates about the y-axis with angular speed ω = 1.9/r^1.5. At r=3, ω = 0.366 rad/s → a full rotation in 17s. At r=10, ω = 0.06 rad/s → 105s. Over 30s, the inner disk rotates ~1.7 times, the outer ~0.3 times. Good, visible motion.

Hmm, is that too fast? The inner disk spinning at 1.7 revolutions in 30s is quite visible. Good for a recording.

Now the camera orbit: az = 0.065 rad/s → 1.86°/s → 56° over 30s. Visible. Good.

Tilt: el = 0.16 + 0.085*sin(t*0.037) → period 170s, amplitude ±0.085 rad = ±4.9°. Slow tilt. Good.

Now let me double check the direction of `right` and the handedness, so the image isn't mirrored. Not critical.

One more: since the camera orbits, the disk's rotation direction relative to the camera changes... fine.

Let me reconsider the step count. 300 iterations with early breaks. Worst case, rays that wind near the photon sphere use all 300. Typical rays use ~40-80. OK.

Potential issue: the `for` loop with a `break` and the `if(trans < 0.003) break;` — in GLSL ES 3.0, break inside a nested if inside a loop is fine.

Now let me reconsider the disk accumulation with multiple crossings and the `trans` factor. When the ray passes through the disk's front side, trans drops. Then the far side's lensed image is dimmed. That's physically correct.

Hmm, but there's an issue: the disk's front side (near the camera) is at r ~ 3-12, and the far side is behind the hole. The ray hits the front side first (large alpha), then continues, gets lensed, and hits the far side. So the far side's lensed image is dimmed by the front disk's opacity. In reality, the far side's image appears above/below the hole, where the front disk is not in the way — those are different pixels! For a pixel looking above the hole, the ray doesn't pass through the front disk (it goes above it). So the lensed far-side image above the hole is not attenuated. Good.

For pixels looking directly at the hole's center (which is black), the ray passes through the front disk region... no, at the center of the shadow, the ray goes toward the hole and is captured; it might cross the disk plane near r~2.6 (inside DISK_IN=2.6) — just outside the inner edge. So it'd be slightly attenuated. Fine.

OK, now let me also think about whether the near side of the disk should occlude the shadow. Yes, at 10° elevation, the near side of the disk (r from 2.6 to 12) projects onto the screen below the shadow center mostly, crossing in front of the lower part of the shadow. Actually at a shallow elevation angle, the disk's near side appears as a thin band across the lower part of the hole... Hmm, with the elevation at 10°, the disk's near edge (r=12, nearest point) is at distance ~16-12 = 4 from the camera... wait, the camera is at 16 from the center, and the disk's outer radius is 12. The nearest point of the disk to the camera is at r=12 in the direction of the camera: distance = 16 - 12 = 4. That point projects to an angle... hmm, the disk's near edge is at distance 4 from the camera, and it's 12*sin(10°) = 2.08 units below the camera's plane... Let's think in terms of the screen: the camera is at (16cos(el), 16 sin(el), 0) roughly, with el = 0.16. The disk's near point is at (12, 0, 0). The vector from the camera to that point: (12-16cos(0.16), -16 sin(0.16), 0) = (12-15.795, -2.55, 0) = (-3.795, -2.55, 0). So it's behind the camera! Wait, no: the camera is at distance 16 from the origin along the direction (cos el, sin el, 0). The point (12,0,0) is closer to the origin. The camera looks toward the origin, i.e., in the direction -(cos el, sin el, 0). The point (12,0,0) relative to the camera is (12 - 16cos el, -16 sin el, 0) = (-3.79, -2.55, 0). The view direction is (-cos el, -sin el, 0) = (-0.987, -0.159, 0). The dot product with the relative vector: (-3.79)(-0.987) + (-2.55)(-0.159) = 3.74 + 0.405 = 4.15 > 0. So it's in front of the camera, at distance ~4.5. Its angular offset from the view axis: the perpendicular component... The relative vector has magnitude sqrt(3.79²+2.55²) = 4.57. The parallel component is 4.15. The perpendicular component is sqrt(4.57²-4.15²)= sqrt(20.9-17.2)=1.92. So the angle = atan(1.92/4.15) = 0.433 rad = 24.8°. That's a big angle — near the edge of the frame (the half-FOV is ~17°). So the disk's near edge is off-screen (or at the very corner). 

Hmm! That means the disk's outer parts are outside the frame, and we mostly see the inner region. The half-height FOV: focal 1.55 → half-angle = atan(0.5/1.55) = 0.312 rad = 17.9°. So a point at 24.8° off-axis is outside the vertical FOV but the horizontal FOV is larger (for a 16:9 aspect, the horizontal half-angle = atan(0.89/1.55) = 29.9°). So the disk's near edge is at the corners of the frame, roughly.

Hmm, this means the disk fills a lot of the frame, going off the bottom/sides. That could look good (immersive) but might cut off the "cooler red outer regions". Let's reduce the outer radius to 9 and/or increase the camera distance to 20.

Let's reconsider. With camDist = 20, el = 0.16:
- Shadow radius: 2.598/20 = 0.13 rad → in p.y units: 1.55*tan(0.13) = 0.202 → 40% of the half-height. Shadow diameter = 40% of the screen height. Good.
- Disk outer edge at r=10: the near point (10,0,0) relative to the camera at (19.74, 3.19, 0): (-9.74, -3.19, 0), magnitude 10.25, view dir (-0.987,-0.159,0), dot = 9.61+0.507 = 10.12, perp = sqrt(105-102.4) = 1.6, angle = atan(1.6/10.12) = 0.157 rad = 9°. So it's within the frame (half-FOV 17.9°). 

So with camDist=20 and DISK_OUT=10, the entire disk is visible. Let's check the disk's far edge: point (-10, 0, 0) relative to the camera: (-29.74, -3.19, 0), magnitude 29.9, dot with view dir = 29.35+0.507 = 29.86, perp = sqrt(894-891.6)=1.55, angle = 0.052 rad = 3°. So the far edge is at 3° above... below? It's at 3° from the axis, on the opposite side of the near edge. So the disk spans about 12° vertically on the screen — that's a thin band. And horizontally it spans ±(some angle). The disk's edge-on ellipse: the semi-major axis is 10 units at a distance of ~20 → the angular half-width = atan(10/20) = 0.46 rad = 26.5° — near the horizontal edge of the frame (29.9° for 16:9). Good.

So the composition: a thin bright band across the middle, the black hole in the center with the shadow, and the lensed far side arcing above and below. 

Hmm, with el = 0.16 (9°), the disk band is quite thin. The Interstellar look has a fairly thin disk too. But maybe a slightly higher elevation shows the disk's top surface better. Let's use el between 0.14 and 0.30 (8° to 17°), i.e., el = 0.22 + 0.08*sin(...). Average ~12.6°.

Hmm, but at higher elevation, the "bends over the top" effect is less dramatic. The classic Interstellar image is nearly edge-on (~1-5°). But then the disk is very thin. Let's compromise at ~10-15°.

Let's use el = 0.20 + 0.07*sin(t*0.037) → range 0.13 to 0.27 (7.4° to 15.5°).

And camDist = 20, DISK_OUT = 10.5, DISK_IN = 2.6.

Let's re-check the disk brightness scaling with these numbers: radial = (2.6/r)^1.7 at r=10.5 → (0.2476)^1.7 = e^{1.7*(-1.396)} = e^{-2.37} = 0.093. Fine.

Actually, let me reconsider the vertical extent of the disk band. At 10° elevation, the disk's near edge at r=10.5 is at a vertical angle of... The near edge point (10.5, 0, 0), the camera at 20*(cos0.2, sin0.2, 0) = (19.6, 3.97, 0). Relative: (-9.1, -3.97, 0). The view dir: (-0.980, -0.199, 0). Dot = 8.92 + 0.79 = 9.71. Perp = sqrt(9.1²+3.97² - 9.71²) = sqrt(82.8+15.8-94.3) = sqrt(4.3) = 2.07. Angle = atan(2.07/9.71) = 0.21 rad = 12°. And the far edge is at ~2-3° on the other side. So the disk spans from about -12° (below) to +3° (above) — a 15° vertical band, versus the 35.8° full vertical FOV. So the disk band occupies ~42% of the screen height. That's substantial and looks good.

Hmm wait, I need to double check the sign. The near edge appears below the center (since the camera is above the plane looking down at the near edge). The far edge appears above the center. So the band goes from -12° to +3°: mostly below the center. The black hole shadow is centered at 0° with a radius of 7.4°. So the shadow overlaps the upper part of the disk band. The lensed far-side image arcs above the shadow. Good, that's the classic look.

Alright, let's finalize with camDist = 20, DISK_OUT = 10.5.

Hmm, but with the camera at 20, the initial ray marching distance to the hole is longer, so more steps are consumed before reaching the interesting region. With dt = 0.05*r capped at 0.85, going from r=20 to r=3 takes about... at r=20, dt=0.85 (capped at 0.85 since 0.05*20 = 1.0 > 0.85). Each step covers ~0.85 units, so ~20 steps to cover 17 units. Fine.

But the escape radius of 24 is now barely beyond the camera distance of 20, which is fine since we check `r > 24 && dot(pos,dir) > 0`.

Hmm, actually, for rays pointing away from the hole, they start at r=20 and go outward; they reach 24 in ~5 steps. Good.

Let me now also double-check the accuracy of the march with dt = 0.85 at r=20 for a ray heading toward the hole: the direction change per step is |acc|*dt = 1.5*h2/r^4*dt. With h2 ≈ (20*sin(θ))² and θ small... For a ray with impact parameter b=3 at r=20: h = 3 (approximately, h = |r × v| = b for a straight ray... actually h = b*v where v is the speed, and v=1 initially, so h ≈ 3). acc = 1.5*9/160000 = 8.4e-5. Times dt=0.85 → 7e-5 rad. Negligible. Fine.

Now, one concern: the total deflection for a ray with b=3 should be significant. The formula handles it as r decreases.

OK. Now, let's also handle the disk's inner edge relative to the shadow for the near side. DISK_IN = 2.6, and the shadow's apparent radius at distance 20 is 2.598/20 = 0.13 rad. The near inner edge at (2.6, 0, 0) — relative to the camera at (19.6, 3.97, 0): (-17.0, -3.97, 0), dot with view dir = 16.66+0.79 = 17.45, |rel| = 17.46, perp = sqrt(304.6-304.5)= 0.3... let me compute properly: |rel|² = 289 + 15.76 = 304.76. dot² = 304.5. perp² = 0.26, perp = 0.51. angle = atan(0.51/17.45) = 0.029 rad. So the near inner edge appears at 0.029 rad below the axis, while the shadow radius is 0.13 rad. So the near inner edge of the disk is *inside* the shadow's apparent radius — it appears in front of the black hole, in the lower part. That's correct and looks right (the disk passes in front of the hole's lower portion).

Great.

Now, one more thing to verify: `uv.y` positive is up. gl_FragCoord.y increases upward in WebGL. Yes.

Now let's write out the final code. I'll be careful with GLSL syntax.

A few more considerations for robustness:
- Use `const int MAX_STEPS = 300;` — actually, in the loop I'll use a literal.
- Loops with a constant bound are fine in GLSL ES 3.0.

Let me also double check the `pow(rr, 1.5)` — pow with a positive base is fine.

`pow(DISK_IN / rr, 1.7)` — fine.

`exp(-dens * 1.6)` — fine.

One thing: `vec3 acc = -1.5 * h2 * pos / (r*r*r*r*r);` — h2 is a float, pos is a vec3 → float*vec3 is fine. `-1.5 * h2` is a float, times pos → vec3. Divided by a float → vec3. Good.

Let me write the final code.

Also, I want to double check the `dirToFace` return with the ternary inside a vec3 constructor: `vec3(d.z/a.x, d.y/a.x, d.x > 0.0 ? 0.0 : 1.0)` — valid GLSL.

Let me now also think about whether the star field will look static or rotate with the camera. Since it's sampled from the ray direction, it will be fixed in world space and the camera orbit will pan across it. Good.

One last concern: performance. The fbm inside the disk loop is called per crossing. With 4 octaves × 8 hashes = 32 hash13 calls per fbm. If a ray has 3 crossings, that's ~96 hash calls. Plus the star field: 3 layers × 9 cells = 27 hash22 calls + the haze fbm (32 hashes). So ~60 for escaped rays. Total maybe 150-200 hash calls per pixel worst case, plus 300 march steps. Should be OK at ~2M pixels on a decent GPU (maybe 30-60 fps). On weaker GPUs, the pixel cap will help.

Let me reduce MAX_STEPS to 260 to be safer. Hmm, but that could cause artifacts for winding rays. 260 is fine.

Actually, let me reconsider: the step size near the photon sphere is dt = 0.05*1.5 = 0.075. An orbit at r=1.5 is 9.42 units → 125 steps per orbit. So 260 steps allows ~2 orbits. Rays that wind more than that will be terminated (and treated as black + ring). That's acceptable — the higher-order images are extremely faint anyway.

Hmm, but actually those rays produce the fine structure of the photon ring. With 2 orbits, we get the first-order image plus some. Fine.

Let me use 300 to be safe, and rely on the pixel cap for performance.

Let me write it now.

Actually, one more improvement: adaptive step size based on the local curvature. Standard trick: `dt = clamp(0.05*r, 0.03, 0.85)`. Near r=1.5, dt=0.075; that's 5% of r per step, which is fine.

Alright, writing the final answer.

Wait — one more check on `smoothstep(0.22, 0.88, n)` where n = fbm(...). fbm returns s*1.0667 where s = sum of a*vnoise, a = 0.5, 0.25, 0.125, 0.0625 → sum = 0.9375. So fbm ∈ [0, 1]. The distribution is concentrated around 0.5. smoothstep(0.22, 0.88) maps 0.5 → 0.5. Good contrast.

Now, `dens = shape * (0.15 + 1.55*n) * pf`. With n ∈ [0,1], the modulation is 0.15 to 1.7. Good.

Let me write the final code.

Also I should double-check: `col += trans * diskColor(x) * dens * 1.35;` — the emission is proportional to dens, which includes pf (path factor). And alpha = 1-exp(-dens*1.6). So emission/alpha ratio ~ constant. Good.

Final check on the disk emission magnitude with the new numbers at the inner region (r=3, pf~1.8):
shape = radial*edgeIn*edgeOut. radial = (2.6/3)^1.7 * (1+1.7*exp(-0.4*1.6)) = 0.79 * (1+1.7*0.527) = 0.79*1.896 = 1.50. edgeIn = smoothstep(2.6, 2.9, 3) = 1. edgeOut = 1. shape = 1.50.
n ~ 0.5 → dens = 1.50*(0.15+0.775)*1.8 = 1.50*0.925*1.8 = 2.5. alpha = 1-exp(-4) = 0.982.
emit = diskColor(x)*2.5*1.35 = col*3.37. col at x=(3-2.6)/7.9 = 0.05 → mix white→orange at smoothstep(0,0.28,0.05)= smoothstep = (0.05/0.28)=0.1786 → 0.1786²*(3-0.357)=0.0319*2.643=0.0843. col = mix((1,0.97,0.9),(1,0.55,0.15),0.084) = (1, 0.935, 0.837). emit = (3.37, 3.15, 2.82). After exposure 1.15: (3.88, 3.62, 3.24) → ACES → (0.96, 0.95, 0.94) → gamma → (0.98, 0.977, 0.97). Nearly white. Good for the hot inner edge, though it loses the orange. Hmm. The inner edge should be "hot orange-white". A pure white is a bit much. Let's reduce the emission scale to 1.0 and make the innermost color less white: (1.0, 0.93, 0.80). Then emit = col*2.5*1.0 = (2.5, 2.32, 2.0) → ×1.15 = (2.87,2.67,2.3) → ACES: for 2.87: (2.87*(7.20+0.03))/(2.87*(6.97+0.59)+0.14) = (2.87*7.23)/(21.7+0.14)= 20.75/21.84 = 0.95. For 2.3: (2.3*(5.77+0.03))/(2.3*(5.59+0.59)+0.14) = (2.3*5.80)/(14.2+0.14) = 13.34/14.34 = 0.93. So (0.95, 0.945, 0.93) → still nearly white. 

The problem is that ACES saturates. To keep the orange hue in the bright inner region, I need the emission to be lower, around 1.0-1.5 total. Let's use an emission scale of 0.6: emit = col*2.5*0.6 = (1.5, 1.4, 1.26) → ×1.15 = (1.72, 1.61, 1.45) → ACES: 1.72 → (1.72*(4.32+0.03))/(1.72*(4.18+0.59)+0.14) = (1.72*4.35)/(8.2+0.14)=7.48/8.34=0.897. 1.45 → (1.45*(3.64+0.03))/(1.45*(3.52+0.59)+0.14) = (1.45*3.67)/(5.96+0.14)=5.32/6.10=0.872. So (0.897, 0.888, 0.872) — still washed out. The issue is that ACES compresses and desaturates at high values.

To get a nice orange-white, the ratio between the channels needs to be larger. Let's make the inner color more orange: (1.0, 0.75, 0.45) for the hottest part? But "hot orange-white inner edge" — the innermost should be white-ish with orange around it. 

The real fix: the brightest part (white) should be at the very inner edge, and the orange should dominate slightly outward. Since the radial falloff is steep, the white will be a thin band. That's fine.

Let's set the emission scale to 1.0 and keep the color ramp. The inner edge will be white-hot (thin), and at x=0.15 (r≈3.8) the color is more orange: smoothstep(0,0.28,0.15) = (0.536)²*(3-1.07) = 0.287*1.93 = 0.554 → col = mix(white, (1,0.55,0.15), 0.554) = (1, 0.762, 0.485). radial at 3.8 = (2.6/3.8)^1.7 * (1+1.7*exp(-1.92)) = (0.684)^1.7 = e^{1.7*(-0.38)} = e^{-0.646}=0.524; ×(1+1.7*0.146)=×1.248 → 0.654. dens = 0.654*0.925*1.8 = 1.09. emit = (1,0.762,0.485)*1.09*1.0 = (1.09, 0.83, 0.53) → ×1.15 = (1.25,0.955,0.61) → ACES: 1.25 → (1.25*(3.17+0.03))/(1.25*(3.04+0.59)+0.14) = (1.25*3.2)/(4.54+0.14)=4.0/4.68=0.855. 0.955 → (0.955*(2.43+0.03))/(0.955*(2.32+0.59)+0.14)= (0.955*2.46)/(2.78+0.14)=2.35/2.92=0.805. 0.61 → (0.61*(1.56+0.03))/(0.61*(1.48+0.59)+0.14)=(0.61*1.59)/(1.26+0.14)=0.97/1.40=0.693. So (0.855, 0.805, 0.693) → gamma → (0.93, 0.90, 0.845). Hmm, still washed out (nearly white with a slight warm tint).

The problem: ACES at ~0.85 output is desaturated. The gamma then lifts everything. Hmm, the output (0.93, 0.90, 0.845) is a pale warm white. That's actually fine for a "hot" region. And further out it gets more orange/red.

Let's check r=6: x = (6-2.6)/7.9 = 0.43. smoothstep(0.28,0.72,0.43) = (0.15/0.44)=0.341 → 0.341²*(3-0.682)=0.116*2.318=0.269. col = mix((1,0.55,0.15),(0.88,0.21,0.05),0.269) = (0.968, 0.459, 0.123). radial = (2.6/6)^1.7 = (0.4333)^1.7 = e^{-1.42} = 0.241; ×(1+1.7*exp(-5.44)) = ×1.0073 → 0.243. dens = 0.243*0.925*1.8 = 0.405. emit = col*0.405 = (0.392, 0.186, 0.050) → ×1.15 = (0.451, 0.214, 0.057) → ACES: 0.451 → (0.451*(1.132+0.03))/(0.451*(1.096+0.59)+0.14) = (0.451*1.162)/(0.760+0.14) = 0.524/0.900 = 0.582. 0.214 → (0.214*(0.537+0.03))/(0.214*(0.520+0.59)+0.14) = (0.214*0.567)/(0.2376+0.14)=0.1213/0.3776=0.321. 0.057 → (0.057*(0.143+0.03))/(0.057*(0.1385+0.59)+0.14)= (0.057*0.173)/(0.0415+0.14)=0.00986/0.1815=0.0543. → gamma: 0.582^0.4545 = e^{0.4545*(-0.541)} = e^{-0.246}=0.782. 0.321^0.4545 = e^{0.4545*(-1.136)} = e^{-0.516}=0.597. 0.0543^0.4545 = e^{0.4545*(-2.913)} = e^{-1.324}=0.266. So (0.78, 0.60, 0.27) → orange-tan. Good.

At r=10: x = 0.937 → smoothstep(0.72,1.0,0.937) = (0.217/0.28)=0.775 → 0.775²*(3-1.55)=0.6*1.45=0.87. col = mix((0.88,0.21,0.05),(0.42,0.06,0.02),0.87) = (0.48, 0.0795, 0.024). radial = (0.26)^1.7 = e^{-2.29} = 0.101; ×1 = 0.101. edgeOut = 1 - smoothstep(6.825, 10.5, 10) = 1 - smoothstep → (10-6.825)/3.675 = 0.864 → 0.864²*(3-1.728)=0.746*1.272=0.949 → edgeOut = 0.051. Hmm! That kills the outer disk. shape = 0.101*0.051 = 0.0052. dens = 0.0052*0.925*1.8 = 0.0087. Way too dim.

The edgeOut fade is too aggressive. Let's use smoothstep(DISK_OUT*0.8, DISK_OUT, rr) = smoothstep(8.4, 10.5, rr). At rr=10: (1.6/2.1)=0.762 → 0.762²*(3-1.524)=0.58*1.476=0.857 → edgeOut = 0.143. shape = 0.101*0.143 = 0.0145. Still dim, but the radial falloff is the main culprit (0.101 at r=10 vs 1.5 at r=3).

Hmm. So the outer disk at r=10 is ~100x dimmer than the inner. That's physically reasonable but visually the outer region will be nearly invisible. Let's soften the radial falloff: use pow(DISK_IN/rr, 1.2) → at r=10: (0.26)^1.2 = e^{1.2*(-1.347)} = e^{-1.616}=0.199. Better. And at r=6: (0.4333)^1.2 = e^{-1.004} = 0.366.

Then at r=10: shape = 0.199*0.143 = 0.0285, dens = 0.0285*0.925*1.8 = 0.047, alpha = 0.073. emit = col*0.047 = (0.48,0.08,0.024)*0.047 = (0.0226, 0.0037, 0.0011) → ×1.15 = (0.026, 0.0043, 0.0013) → ACES ≈ roughly linear here: ACES(0.026) = (0.026*(0.0653+0.03))/(0.026*(0.0632+0.59)+0.14) = (0.026*0.0953)/(0.0170+0.14) = 0.00248/0.157 = 0.0158 → gamma = 0.0158^0.4545 = e^{0.4545*(-4.147)} = e^{-1.885} = 0.152. Green: 0.0043 → ≈ 0.0043*... ACES(0.0043) ≈ (0.0043*0.0408)/(0.1434) = 0.000175/0.1434=0.00122 → gamma = 0.00122^0.4545 = e^{0.4545*(-6.71)} = e^{-3.05}=0.047. Blue: ~0.03. So the outer disk is (0.15, 0.05, 0.03) → dark red-brown. Visible against black. OK, that works. It's a "cool red outer region". 

Hmm, but the contrast between the inner (white) and outer (dark red) is huge. That's realistic. Fine.

But I worry the outer disk will be too dim overall. Let's boost the outer disk with a flatter profile: add a floor to the radial profile. E.g. `float radial = pow(DISK_IN/rr, 1.2) + 0.06;` — that adds a constant. At r=10: 0.199+0.06 = 0.259, dens = 0.259*0.143*0.925*1.8 = 0.062, emit = col*0.062 → (0.0298,0.005,0.0015) → gamma ≈ 0.17. Slightly brighter. Meh.

Alternatively, use a "temperature" that stays visible: it's fine. Let's keep pow(DISK_IN/rr, 1.25) and no floor, plus the smooth outer fade from 0.75*DISK_OUT.

Actually, let me reconsider the overall exposure. The outer disk being dark red at ~0.15 brightness is fine — it reads as "cooler red outer regions". Good.

Let me settle: 
- radial = pow(DISK_IN/rr, 1.3) * (1.0 + 1.8*exp(-(rr-DISK_IN)*1.6))
- edgeOut = 1 - smoothstep(DISK_OUT*0.72, DISK_OUT, rr)

At r=10.5 (the very edge) it's 0 anyway.

OK, good enough. Let me also double check the inner: at r=2.6, radial = 1 * (1+1.8) = 2.8. dens = 2.8*0.925*1.8 = 4.66. emit = col*4.66*1.0. col at x=0 is (1,0.93,0.80) → emit = (4.66, 4.33, 3.73) → ×1.15 → ACES → (0.97,0.965,0.96) → white. Fine, the very inner edge is white-hot.

Now let me reduce the emission multiplier a bit so that only the very inner edge is white: use emit scale 0.85. Then at r=3: emit = (1,0.935,0.837)*2.5*0.85 = (2.13,1.99,1.78) → ×1.15 = (2.45,2.29,2.05) → ACES: 2.45 → (2.45*(6.15+0.03))/(2.45*(5.95+0.59)+0.14) = (2.45*6.18)/(16.0+0.14) = 15.14/16.14 = 0.938. 2.05 → (2.05*(5.15+0.03))/(2.05*(4.98+0.59)+0.14) = (2.05*5.18)/(11.42+0.14)=10.62/11.56=0.919. → (0.938, 0.928, 0.919) → nearly white. OK.

Fine. The disk's inner region will be bright white-orange with the outer parts orange to red. Good.

Let me finalize and write the code.

Actually, let me reconsider the exposure: maybe use 1.0 and let the ACES do its thing. I'll set exposure 1.1.

Now writing the final file.

One more: I should ensure the photon ring isn't too bright compared to the disk. ring amplitude 0.85 → after ACES+gamma ≈ 0.9 white-orange. That's a bright thin ring. Good.

Let me write it all out now.

Also, note: `if(h.x > density) continue;` inside a double loop — I should double check that `continue` skips to the next inner-loop iteration. Yes.

Final code:

I'll write the HTML now.

One last thought about the canvas fill: `canvas{width:100vw;height:100vh}` and the internal buffer is scaled by dpr. The aspect ratio is preserved since both dimensions use the same scale. Good.

Let me write it.

Actually, I realize I should double check one thing: `vec3 pr = vec3(ca*hit.x - sa*hit.z, 0.0, sa*hit.x + ca*hit.z);` then `fbm(pr * 0.55)`. The noise frequency: pr is in units of rs, ranging up to ~12. Times 0.55 → up to 6.6. So about 6 noise cells across the disk's radius. That's a low-frequency pattern. With 4 octaves, the finest is at 6.6*8 = 53 cells. Hmm, that gives features of size ~0.15 rs at the finest. Reasonable for turbulence.

But at the inner region (r ~ 3), pr*0.55 ~ 1.65, so the finest octave is at 13 → features of size 0.23 rs. The disk's inner region is ~2.6-5, so a few features. Good.

The shear from differential rotation will stretch these into spirals over time. Good.

Alright. Writing now.

Wait, one more important check on the rotation: `float a = om * t;` with om = 1.9/pow(rr,1.5). At rr=2.6, om = 1.9/4.19 = 0.453 rad/s. Over 30 s, a = 13.6 rad = 2.2 revolutions. Good.

And the rotation of the sample point means the pattern rotates by -a. Fine.

Let me write the final file.

I'll also add a `#define` for MAX_STEPS.

Final concern: the shader's compile time and the loop unrolling. A 300-iteration loop with complex body might be slow to compile on some drivers. It's usually fine. ANGLE handles this. Let's keep 300 but maybe reduce to 256 (a power of two, sometimes better). I'll use 280. Eh, 300 is fine.

Write it.