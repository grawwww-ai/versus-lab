We need to create a single HTML file with raw WebGL2, full-screen quad, raymarching fragment shader showing stormy ocean at sunset.

Let me write the shader carefully.

Approach: raymarch a heightfield ocean surface. Camera bobbing. Sky with clouds via fbm, sun with glow. Water: intersect ray with height field using iterative raymarching steps, compute normal via gradient, fresnel reflection mixing sky color and water color, sun specular reflection, foam based on wave height/steepness.

Let me write GLSL.

Vertex shader: full screen triangle/quad, pass uv.

Fragment shader:
- precision highp float.
- uniforms: iResolution, iTime.

Noise: hash + value noise 3D, fbm.

Ocean height function:
```
float waveHeight(vec2 p, float t){
  float h = 0.0;
  float amp = 1.0;
  float freq = 0.18;
  vec2 dir = normalize(vec2(1.0,0.35));
  for(int i=0;i<5;i++){
     float n = fbm(p*freq + dir*t*1.6*freq*... )
  }
}
```
Better: sum of several noise octaves with different directions and speeds.

```
float ocean(vec2 p, float t){
  float h=0.0;
  float a=1.0;
  float s=0.0;
  vec2 q = p*0.55;
  h += fbm(q + vec2(t*0.35, t*0.12)) * 1.0;
  h += fbm(q*2.1 + vec2(-t*0.5, t*0.28)) * 0.5;
  h += fbm(q*4.3 + vec2(t*0.8, -t*0.6)) * 0.25;
  h += fbm(q*8.7 + vec2(-t*1.3, t*1.1)) * 0.125;
  return h;
}
```
Need normalization ~ sum of amps = 1.875, fbm returns ~0..1 or -1..1. Use smooth noise in [-1,1] → sum in [-1.875,1.875]. Scale by ~0.35 → amplitude ~0.65. Hmm, wave height scale in world units. Camera height ~ 2.5 units above water. Let's tune.

Let me set up coordinates: world x,z ground plane, y up. Camera at (0, camY, 0) looking at slightly below horizon or towards horizon with pitch.

Raymarch: for the ocean, do a fixed number of steps along ray, checking y < oceanHeight. Actually a robust approach: ray march with increasing step size, and when below surface, binary refine.

Standard technique:

```
float t = 0.1;
float hit = -1.0;
for(int i=0;i<90;i++){
  vec3 p = ro + rd*t;
  float h = ocean(p.xz, time);
  float d = p.y - h;
  if(d < 0.0){ hit = t; break; }
  t += max(0.05, d*0.5);
}
```
This is a sphere-trace-like approach with distance d = p.y - h, which is not a true distance but works okay-ish since gradient magnitude ~ maybe < 1. Use step = max(0.05, d*0.4).

Then refine with binary search for smoother surface.

Normal: compute analytic-ish via finite differences of height function:
```
vec3 getNormal(vec2 p, float t){
  float e = 0.02;
  float hL = ocean(p - vec2(e,0.0), t);
  float hR = ocean(p + vec2(e,0.0), t);
  float hD = ocean(p - vec2(0.0,e), t);
  float hU = ocean(p + vec2(0.0,e), t);
  return normalize(vec3(hL-hR, 2.0*e, hD-hU));
}
```

Foam: based on height above threshold and steepness. foam = smoothstep(threshold, maxH, h) combined with noise.

Sun: direction low, e.g. normalize(vec3(0.6, 0.06, -1.0)) — place sun ahead of camera.

Sky: fbm clouds in direction, dark grey-blue with orange near sun. Sun disc bright orange, glow.

Water color: dark, with fresnel mixing sky reflection and deep water color. Specular sun reflection: reflect ray, compare with sun dir, power.

Fog near horizon: mix with fog color based on distance or based on ray direction y.

Let me write the sky function:

```
vec3 sky(vec3 rd, vec3 sunDir){
  float y = max(rd.y, 0.0);
  // base gradient
  vec3 zen = vec3(0.06,0.08,0.16);
  vec3 hor = vec3(0.55,0.32,0.22);
  vec3 col = mix(hor, zen, pow(y, 0.45));
  // sun glow
  float sd = max(dot(rd, sunDir),0.0);
  col += vec3(1.0,0.45,0.15) * pow(sd, 8.0)*0.6;
  col += vec3(1.0,0.55,0.25) * pow(sd, 2.0)*0.20;
  // clouds
  ... fbm on rd.xz/rd.y projection
}
```

Clouds: use `vec2 uv = rd.xz / max(rd.y, 0.06) * 0.35` — for rd.y>0. Then fbm(uv + time*wind). Cloud density: c = fbm. darken.

Cloud color: base dark grey = mix based on lighting toward sun. Let's do:
```
float d = fbm(uv*1.0 + vec2(t*0.02, t*0.01));
d = smoothstep(0.35, 0.75, d);
vec3 cloudDark = vec3(0.10,0.11,0.15);
vec3 cloudLit = vec3(0.75,0.42,0.28);
float lit = pow(max(dot(rd,sunDir),0.0), 3.0);
vec3 cc = mix(cloudDark, cloudLit, lit*0.8 + 0.1);
col = mix(col, cc, d*0.85);
```
Careful with high rd.y: uv → 0, so clouds converge. Fine.

Since rd.y can be negative for reflected rays below horizon — but we only use sky for reflection direction which will have y>0 mostly. Clamp.

Fog: mix the surface color with fog color near horizon based on distance: fogAmt = 1 - exp(-dist * 0.02) or based on the ray direction y. Also add horizon haze.

Let me consider that the visible ocean extends to the horizon. With camera height ~2.5, horizon at distance d = sqrt(2*R*h) but for flat plane, horizon at infinity. So rays nearly parallel to the water never hit. Need max distance clamp: if t > maxDist, treat as sky. Use maxDist like 400. Rows with rd.y slightly negative will get hits far away; with fog blending it'll look like horizon haze. Good.

Actually with a flat plane, ray at rd.y = -0.001 hits at distance camY/0.001 = 2500. Cap at, say, 300 and treat as fog/sky. Fog will hide it. Set fog such that at 300 distance the surface is nearly fog color matching horizon. Good.

Camera bobbing: ro = vec3(sin(t*0.7)*0.15, 2.6 + sin(t*1.1)*0.18 + sin(t*2.3)*0.06, t*0.0)... Actually moving forward? Keep camera in place but water moves. Bobbing rotation too: small pitch/roll.

Let's set camera position fixed at origin horizontally but water noise evolves with time so waves roll by. Actually to feel like moving, the wave noise's time term makes patterns move. Good enough.

Camera direction: forward = normalize(vec3(0.0, -0.05, -1.0)) plus bob rotation. Let's define with a look-at-ish approach:

```
vec3 ro = vec3(bobx, camY, bobz);
vec3 ta = vec3(0.0, 0.9 + bobY2, 0.0) ... 
```
Hmm, simplest: compute forward direction from pitch/yaw, then build basis.

```
float pitch = -0.045 + sin(t*0.9)*0.012;
float yaw = sin(t*0.37)*0.05;
vec3 rd0 = normalize(vec3(0.0, sin(pitch), -cos(pitch)));  // roughly
```
Better to build forward = normalize(vec3(sin(yaw)*cos(pitch), sin(pitch), -cos(yaw)*cos(pitch))). Then right = normalize(cross(vec3(0,1,0), forward))... careful sign. up = cross(forward, right).

Then rd = normalize(forward * 1.0 + right*uv.x*... + up*uv.y*...). Use fov.

Sun placed at direction normalize(vec3(0.35, 0.07, -1.0)) — to the right of center, low. With camera facing -z, sun appears right of center and low. Good.

Let me now write the noise functions.

```
float hash(vec3 p){
  p = fract(p*0.3183099 + vec3(0.1,0.2,0.3));
  p *= 17.0;
  return fract(p.x*p.y*p.z*(p.x+p.y+p.z));
}
float noise(vec3 x){
  vec3 i = floor(x);
  vec3 f = fract(x);
  f = f*f*(3.0-2.0*f);
  return mix(mix(mix(hash(i+vec3(0,0,0)), hash(i+vec3(1,0,0)), f.x),
                 mix(hash(i+vec3(0,1,0)), hash(i+vec3(1,1,0)), f.x), f.y),
             mix(mix(hash(i+vec3(0,0,1)), hash(i+vec3(1,0,1)), f.x),
                 mix(hash(i+vec3(0,1,1)), hash(i+vec3(1,1,1)), f.x), f.y), f.z);
}
```
That returns 0..1. I'll convert to -1..1 where needed.

fbm3:
```
float fbm(vec3 p){
  float a=0.5, s=0.0;
  for(int i=0;i<5;i++){ s += a*noise(p); p*=2.02; a*=0.5; }
  return s; // ~0..1
}
```

For ocean, use 2D-ish by passing vec3(x, 0, z)? That's 3D noise sampled on a plane — fine but slower. Alternatively write 2D noise. Let's just write a 2D noise too, cheaper.

Actually I'll just do 2D noise for ocean and 3D for clouds... clouds can be 2D too (uv domain). Let's use 2D noise for both, with time as a third dimension for evolution? Use 2D noise + time offset in the domain. Fine.

Let's define:
```
float hash21(vec2 p){ p = fract(p*vec2(123.34,456.21)); p += dot(p,p+45.32); return fract(p.x*p.y); }
float noise2(vec2 x){ ... }
float fbm2(vec2 p){ 5 octaves }
```

Ocean height:
```
float oceanH(vec2 p, float t){
  vec2 q = p * 0.35;
  float h = 0.0;
  h += fbm2(q*1.0 + vec2(t*0.35, t*0.10)) * 1.0;
  h += fbm2(q*2.13 + vec2(-t*0.62, t*0.31)) * 0.55;
  h += fbm2(q*4.37 + vec2(t*0.9, -t*0.72)) * 0.28;
  h += fbm2(q*9.1 + vec2(-t*1.5, t*1.2)) * 0.12;
  return (h - 0.97) * 1.35;  // roughly -1..1
}
```
fbm2 with 5 octaves sums a=0.5,0.25,... = ~0.97 max, mean ~0.48. So h ranges roughly [0, 1.95]. Hmm, actually fbm sum with amplitudes 0.5..0.03125 = 0.96875. Times weights: base weight 1 → fbm2 in [0,0.97]; with weights: total max = 0.97*(1+0.55+0.28+0.12)= 0.97*1.95 = 1.89, min ~0. Mean ~0.94. So subtract 0.94 and scale. Let's just use (h - 0.95)*1.6 giving range about [-1.5, 1.5] roughly, typical ±0.5.

Hmm, terrain amplitude ~1.5 world units with camera at 2.6 — could be too much; waves up to 1.5 above mean, camera 2.6 → waves nearly reaching camera. That could be dramatic. Let's scale to (h-0.95)*1.1 → ±1.0. Camera at y=2.2. Waves ±1.0 → crests at 1.0, camera 2.2. OK.

Actually let me increase the small-octave contribution for choppiness.

Let's just tune reasonably and hope.

Now the raymarch. Number of steps: 100 with adaptive stepping. Distance along ray: t from 0.05 to 500.

```
float t = 0.2;
float tmax = 500.0;
float hitT = -1.0;
for(int i=0;i<110;i++){
  vec3 pos = ro + rd*t;
  float h = oceanH(pos.xz, time);
  float d = pos.y - h;
  if(d < 0.001){ hitT = t; break; }
  t += max(0.06, d*0.45);
  if(t > tmax){ break; }
}
```
Hmm, if the ray goes upward (rd.y > 0), d grows, t grows quickly and exceeds tmax fast. Fine.

Then binary refine:
```
if(hitT > 0.0){
  float t0 = hitT*0.85, t1 = hitT;  // careful with stepping
  for(int i=0;i<8;i++){
    float tm = 0.5*(t0+t1);
    float d = (ro+rd*tm).y - oceanH((ro+rd*tm).xz, time);
    if(d > 0.0) t0 = tm; else t1 = tm;
  }
  hitT = 0.5*(t0+t1);
}
```
Hmm, need t0 above surface. Since previous step was above surface, t0 = hitT - lastStep works better. Just use t0 = hitT*0.9 — could be below surface if step large. Use 8 iterations anyway; slight error acceptable. Actually, safer: store prevT. Let me store prev t in a variable.

Let me restructure:

```
float t = 0.2;
float prev = t;
float hitT = -1.0;
for(int i=0;i<120;i++){
  vec3 pos = ro + rd*t;
  float d = pos.y - oceanH(pos.xz, time);
  if(d < 0.0){ hitT = t; break; }
  prev = t;
  t += max(0.05, d*0.4);
  if(t > 500.0) break;
}
```
Then refine between prev and hitT. prev has d>=0, hitT has d<0. Good.

But performance: 120 iterations × oceanH which does 4 fbm2 calls × 5 octaves = 20 noise samples each with 4 hashes... that's a lot. 120 × 20 × ~4 = 9600 hash calls per pixel. Too heavy maybe. Hmm.

Let's reduce: use 3 octaves per fbm and 3 wave layers. Actually the number of raymarch steps needed: with adaptive stepping, typical is maybe 30-60. Let's cap at 80 and use a cheaper ocean function.

Alternative: reduce fbm octaves to 4 and use 3 layers: 12 noise samples per oceanH call. 80 steps × 12 = 960 noise samples. Each noise2 = 4 hashes + mix. That's ~4000 hash ops per pixel. At 1920×1080 that's 8 billion ops... too slow for 60fps but maybe OK-ish at lower res. Hmm.

We should render at reduced resolution? We could set canvas to half resolution internally but CSS full size. That's a common trick. But requirement: canvas fills window. We can have canvas with lower drawing buffer resolution and CSS scaled to fill. That's acceptable — "fill the window". I'll use devicePixelRatio capped at 1 and maybe a scale factor of 0.75 or so. Hmm, but quality. Let's do render scale that adapts: min(1, ... ) Actually simplest: use scale = 1 but with `Math.min(window.devicePixelRatio, 1)`. For a 1080p window that's 2M pixels. With the above cost, might be ~10-20 fps on integrated GPU. Risky.

Let's reduce resolution to about 1/2 linear (0.25 pixel count) — since waves are smooth, upscaling looks fine with a bit of softness. Actually raymarched ocean edges benefit. Let's use a scale factor of 0.6? Hmm.

Alternative: render to a smaller framebuffer... no, just set canvas.width = innerWidth * scale.

I'll use scale = 0.75 with dpr capped at 1... Let me use: `const scale = Math.min(1, 900 / Math.max(window.innerWidth, window.innerHeight))`? No, that doesn't scale with area properly.

Let's do: target ~ 500k-700k pixels. `let pixelScale = Math.sqrt(650000 / (w*h))` clamped to [0.4, 1]. That gives 1280×720 = 921600 → scale 0.84. Hmm.

Honestly, let's just cap total pixels at ~800k and use CSS upscaling. Fine.

Actually, let's also reduce ocean cost. Let's think about the step count more concretely. Camera at height 2.2 looking nearly horizontally. Rays going downward hit within maybe 10-50 units, with the adaptive step d*0.4 it should take maybe 20-40 steps. Rays above horizon exit immediately after a few steps. So average maybe 25 steps. With 12 noise samples each = 300 noise samples per pixel. Plus normal computation (4 oceanH calls) and foam. Reasonable.

Let's use fbm with 4 octaves and 3 wave layers → 12 noise2 calls.

Actually we can reduce normal to 3 samples (front difference): use central differential for 2 axes = 4 evaluations. Keep 4.

OK. Total ~ (steps 30 + 4 + 8 binary) × 12 ≈ 500 noise2 calls. At 800k pixels = 400M noise2 calls/frame... each noise2 = 4 hash + 3 mixes ≈ 20 flops. 8 GFLOP/frame. Too much for 60fps on most GPUs at that resolution? Modern GPUs do ~1-5 TFLOPS, so 8 GFLOP/frame → 500 fps theoretically. Actually fine. Integrated GPUs ~500 GFLOPS → 16 fps. Hmm, borderline.

Let's limit to 600k pixels and reduce steps to 90 max. Should be OK. Most recording setups are decent.

Let me now write the full shader.

```glsl
#version 300 es
precision highp float;
out vec4 fragColor;
uniform vec2 iResolution;
uniform float iTime;

#define PI 3.14159265

float hash21(vec2 p){
  p = fract(p * vec2(123.34, 456.21));
  p += dot(p, p + 45.32);
  return fract(p.x * p.y);
}

float noise2(vec2 x){
  vec2 i = floor(x);
  vec2 f = fract(x);
  vec2 u = f*f*(3.0-2.0*f);
  float a = hash21(i);
  float b = hash21(i + vec2(1.0,0.0));
  float c = hash21(i + vec2(0.0,1.0));
  float d = hash21(i + vec2(1.0,1.0));
  return mix(mix(a,b,u.x), mix(c,d,u.x), u.y);
}

float fbm(vec2 p){
  float s = 0.0, a = 0.5;
  mat2 rot = mat2(0.8,0.6,-0.6,0.8);
  for(int i=0;i<4;i++){
    s += a * noise2(p);
    p = rot * p * 2.03;
    a *= 0.5;
  }
  return s; // ~0..0.94
}
```

Rotation each octave to avoid axis alignment artifacts. Good.

Ocean height:
```
float oceanH(vec2 p, float t){
  vec2 q = p * 0.32;
  float h = 0.0;
  h += fbm(q*1.00 + vec2(t*0.30,  t*0.11)) * 1.00;
  h += fbm(q*2.17 + vec2(-t*0.55, t*0.29)) * 0.55;
  h += fbm(q*4.61 + vec2(t*0.85, -t*0.63)) * 0.27;
  h += fbm(q*9.30 + vec2(-t*1.35, t*1.05)) * 0.12;
  return (h - 0.93) * 1.15;
}
```
Sum weights = 1.94, times fbm mean 0.47 → mean 0.91. Range about [0, 1.82]. After subtracting 0.93 and ×1.15: mean ~ -0.02, range [-1.07, 1.02]. Good.

Hmm, but the realistic "rolling waves" look — with the fbm, the large-scale features are at frequency q*0.32 = p*0.32... wait q = p*0.32, then q*1.0 → p*0.32. So the base noise has feature size ~ 3 units. Camera at 2.2 height, horizon... waves of 3-6 unit wavelength. That's big-ish relative to camera height; good for "large rolling waves".

Actually to make it feel like a big ocean, we want waves of several meters and camera at 2-3 m. Yes.

Normal:
```
vec3 oceanNormal(vec2 p, float t){
  float e = 0.12;
  float hL = oceanH(p - vec2(e,0.0), t);
  float hR = oceanH(p + vec2(e,0.0), t);
  float hD = oceanH(p - vec2(0.0,e), t);
  float hU = oceanH(p + vec2(0.0,e), t);
  return normalize(vec3(hL - hR, 2.0*e, hD - hU));
}
```
Wait, this gives a normal with y-component 2e = 0.24 which after normalize... The gradient magnitude with wave amplitude ~1 and wavelength ~3 → slope ~ 1/3 per unit... hL-hR over 2e=0.24 gives roughly the slope * 0.24. Normal = normalize(vec3(hL-hR, 2e, hD-hU)) — correct form is (dh/dx * ... ). Standard: normal ∝ (-dh/dx, 1, -dh/dz) where dh/dx ≈ (hR-hL)/(2e). So normal ∝ ((hL-hR)/(2e), 1, (hD-hU)/(2e)) ∝ (hL-hR, 2e, hD-hU). Yes correct.

With e=0.12, that's fine. But high-frequency detail might alias. Use e = 0.15.

Sky:

```
vec3 skyColor(vec3 rd, vec3 sunDir, float t){
  float y = rd.y;
  float hy = max(y, 0.0);
  vec3 zenith = vec3(0.045, 0.06, 0.13);
  vec3 horizon = vec3(0.42, 0.22, 0.18);
  vec3 col = mix(horizon, zenith, pow(hy, 0.42));
  
  // sunset glow near horizon around sun azimuth
  float sunAmt = max(dot(rd, sunDir), 0.0);
  col += vec3(1.0, 0.42, 0.12) * pow(sunAmt, 6.0) * 0.55;
  col += vec3(1.0, 0.30, 0.08) * pow(sunAmt, 1.7) * 0.22 * smoothstep(-0.1, 0.35, y+0.15);
  
  // clouds
  if(y > 0.002){
    vec2 uv = rd.xz / (y + 0.12) * 0.9;
    uv += vec2(t*0.02, t*0.008);
    float c = fbm(uv*0.6);
    float c2 = fbm(uv*1.6 + 5.0);
    float dens = smoothstep(0.42, 0.72, c*0.75 + c2*0.35);
    ...
  }
}
```

Hmm careful: rd.xz/y at y→0 blows up. Use y+0.12 which caps magnitude at ~8 for rd.xz ~1. That spreads clouds. Good, that simulates a cloud plane at some height.

Cloud color: dark on the far side, lit near sun.
```
float lit = pow(max(dot(rd, sunDir),0.0), 2.0);
vec3 cbase = vec3(0.07, 0.075, 0.10);
vec3 clit = vec3(0.85, 0.42, 0.22);
vec3 ccol = mix(cbase, clit, lit * 0.9 + 0.06);
col = mix(col, ccol, dens * 0.9);
```
Also darken clouds to make them dramatic. And add a bright rim near sun.

Sun disc: add after clouds so it's in front? Physically the sun should be behind clouds, but for a dramatic look, let's draw the sun disc before clouds so clouds occlude it (more dramatic). Actually with a low sun near horizon and clouds, partial occlusion is nice. Let's draw the sun disc first, then clouds on top with density. But then the sun's bright glow would be dimmed by clouds. That's realistic. Let's do that.

Sun disc:
```
float sd = dot(rd, sunDir);
float disc = smoothstep(0.9993, 0.9997, sd);
col += vec3(1.0, 0.62, 0.28) * disc * 4.0;
```
Careful with the glow near horizon.

Then clouds on top with `col = mix(col, ccol, dens)`. But then the sun disc gets dimmed by dense clouds. Fine.

Hmm, but the sun's glow contribution `pow(sunAmt,6)*0.55` also gets dimmed. Slightly odd but acceptable. Actually better: apply clouds first then add the direct sun disc and glow on top, so the sun burns through slightly. Let's do: sky gradient + clouds, then add sun glow and disc. With disc add it'd show through clouds — that's a bit unrealistic but looks dramatic. Compromise: add glow after clouds (glow scatters), and disc before clouds... 

Simplest: compute sky+clouds, then add sun glow * (1 - cloudDensity*0.7) and disc * (1-cloudDensity). Eh, let me just add sun after clouds with full strength; a low sun burning through storm clouds looks great.

Actually let's do: add glow after clouds, disc after clouds but multiplied by (1 - dens*0.85) so it can be partially hidden. Hmm, that makes the sun look weird with holes. Just add it fully. It's an art piece.

I'll do: sun glow and disc added after clouds.

Water shading:

```
vec3 waterColor(vec3 pos, vec3 rd, vec3 n, vec3 sunDir, float t){
  vec3 refl = reflect(rd, n);
  refl.y = abs(refl.y); // ensure above horizon? Actually can be negative for grazing. Use max(refl.y, 0.008)
  vec3 skyR = skyColor(refl, sunDir, t);
  float fres = 0.02 + 0.98 * pow(1.0 - max(dot(-rd, n), 0.0), 5.0);
  
  // deep water
  vec3 deep = vec3(0.015, 0.03, 0.045);
  float h = pos.y;
  vec3 shallow = vec3(0.05, 0.09, 0.11);
  vec3 base = mix(deep, shallow, smoothstep(-0.5, 1.2, h));
  
  // sun specular
  vec3 hDir = normalize(sunDir - rd);
  float spec = pow(max(dot(n, hDir), 0.0), 220.0);
  ...
}
```

Actually with the sun low, the specular highlight would be a big glitter path. Use a broader specular plus glitter: `pow(max(dot(n,halfV),0.0), 300.0)*3.0`.

Foam:
```
float heightF = smoothstep(0.35, 0.85, pos.y);
float steep = 1.0 - n.y; // 0 flat, up to 1
float steepF = smoothstep(0.10, 0.35, steep);
float foamNoise = fbm(pos.xz*1.5 + vec2(t*0.3, -t*0.2));
float foam = clamp(heightF * (0.4 + 0.6*steepF) * (0.5 + 0.9*foamNoise), 0.0, 1.0);
foam = smoothstep(0.35, 0.9, foam);
```
Then color = mix(water, foamColor, foam) with foamColor ~ vec3(0.85,0.86,0.88) tinted by sun a bit.

Final compositing:
```
vec3 col = mix(base, skyR, fres);
col += spec * sunTint;
col = mix(col, foamCol, foam);
```
Fresnel should weight the reflection. Also add subsurface scattering glow in wave crests facing the sun (orange translucency) — nice touch:
```
float sss = pow(max(dot(n, sunDir), 0.0), 3.0) * smoothstep(0.0, 1.0, pos.y);
col += vec3(0.5, 0.18, 0.05) * sss * 0.5;
```

Fog: distance-based.
```
float dist = length(pos - ro);
float fogAmt = 1.0 - exp(-dist*0.0065);
vec3 fogCol = skyColor(normalize(vec3(rd.x, 0.02, rd.z)), sunDir, t);  // horizon-ish
col = mix(col, fogCol, fogAmt*0.9);
```
Better: sample the sky in the ray direction at the horizon: fogCol = skyColor(vec3(rd.x, 0.02, rd.z) normalized, ...). Let's just use a fixed horizon color mixed with the sun glow direction.

Let's compute fog color = mix(horizonFog, sunGlow) where horizonFog = vec3(0.28,0.20,0.20).

Ok.

Now main:

```
void main(){
  vec2 fragCoord = gl_FragCoord.xy;
  vec2 uv = (fragCoord - 0.5*iResolution) / iResolution.y;
  
  float t = iTime;
  
  // camera bobbing
  vec3 ro = vec3(sin(t*0.53)*0.25, 2.30 + sin(t*1.13)*0.13 + sin(t*2.31)*0.045, cos(t*0.41)*0.2);
  float pitch = -0.055 + sin(t*0.83)*0.018 + sin(t*1.7)*0.006;
  float yaw = sin(t*0.29)*0.06;
  
  vec3 fwd = normalize(vec3(sin(yaw)*cos(pitch), sin(pitch), -cos(yaw)*cos(pitch)));
  vec3 right = normalize(cross(vec3(0.0,1.0,0.0), fwd));
  vec3 up = cross(fwd, right);
  
  float fov = 1.4; // focal
  vec3 rd = normalize(fwd*fov + right*uv.x + up*uv.y);
  
  vec3 sunDir = normalize(vec3(0.42, 0.075, -1.0));
  
  vec3 col = skyColor(rd, sunDir, t);
  
  // ocean
  if(rd.y < 0.12){  // could hit
    ... march ...
  }
}
```

Hmm, the horizon: with camera y=2.3 and waves up to ~1, rays with rd.y slightly positive could still hit a wave crest nearby? Only if the crest is above the camera. Waves max ~1.0 < 2.3, so no. Rays with rd.y > 0 never hit. But wait — camera at 2.3 and wave crests at ~1.0, so rays must go down. Right. Set condition rd.y < 0.0.

But also there's an issue: near-horizon rays with tiny negative rd.y hit at huge distances (t = 2.3/0.005 = 460) which exceeds our 500 cap... borderline. Fog covers it.

Actually there's a subtlety: with the flat plane and camera at height h, the horizon is at infinite distance; the visible water fills everything below the horizon line. With fog fading to horizon color, the transition to sky looks natural.

But we should ensure that rays just below the horizon still find a hit before tmax=500. If rd.y = -0.005, hit at 460 < 500. ok. If rd.y = -0.001, hit at 2300 > 500 → break, treated as sky. But sky at rd.y=-0.001 gives ~horizon color anyway since we compute skyColor with max(y,0). Actually skyColor with y slightly negative: pow(hy,0.42) with hy=0 → horizon color. And clouds are only for y>0. So it blends. But the sky at negative y would be pure horizon color which might be brighter than the fog. Fine.

Hmm, one thing: the fog blend uses skyColor at the horizon. If the ocean surface fades into fog at ~400 units, and the sky just above is similar, the horizon is seamless. Good.

Let's set fog to reach ~0.9 at 400 units: exp(-400*k) = 0.1 → k = 0.00576. Use 0.0055.

Also need the fog to not apply to nearby water. At 20 units fog = 1-exp(-0.11) = 0.10. Fine.

Now let me also handle the reflection: `refl.y` might be negative near grazing; skyColor handles negative y okay-ish (returns horizon color, no clouds). Let's clamp refl.y = max(refl.y, 0.005) then normalize... Actually just use skyColor(refl, ...) — inside we use y and max(y,0) for gradient and only add clouds if y>0.002. Fine.

But for the specular reflection of the sun on the water, that comes naturally from skyColor's sun glow (pow(sunAmt, 6)*0.55) multiplied by fresnel. Hmm — the sun disc in the reflection requires refl to align with sunDir which happens on the glitter path. The disc smoothstep(0.9993,0.9997) is tiny; for a rough surface, we'd want a broader highlight. Let's add a proper specular term with the half vector.

Let's compute:
```
vec3 H = normalize(sunDir - rd);   // half vector between view dir (-rd) and light
float s = max(dot(n, H), 0.0);
float spec = pow(s, 400.0) * 4.0 + pow(s, 40.0) * 0.25;
col += vec3(1.0, 0.55, 0.25) * spec;
```

That gives a nice sharp glitter + broad sheen.

Now foam color — should be lit by the sun: `vec3 foamCol = vec3(0.75,0.72,0.70) * (0.4 + 0.6*max(dot(n,sunDir),0.0)) + sunTint*spec`.

Let's keep it simple.

Now let's think about the "large rolling waves" - the fbm approach with the layer frequencies at 1x, 2.17x, 4.61x, 9.3x of q = p*0.32. Base wavelength: noise2 features at integer grid, so wavelength ~ 1/0.32 = 3.1 units. Amplitude of the base layer ~ 1.15 * fbm range... The fbm output range is 0..0.94 with typical deviation ~0.2. So base layer contributes ±0.23. Combined with weights, total deviation maybe ±0.45 in world units. With wavelength 3 units, slope ~ 0.45/1.5 = 0.3. That's gentle rolling. To make it more dramatic, maybe increase overall amplitude to 1.6 and reduce q scale to 0.22 (longer waves).

Let's set q = p*0.22 → base wavelength ~4.5 units. Amplitude scale 1.7 → deviations ±0.65. Slopes ~0.29. Hmm, still gentle. We want steeper, choppier. Increase the higher-frequency weights a bit.

Actually let's use amplitude scale 2.0 and see. Camera at 2.4, waves ±0.8. Crests nearly at camera height. Sounds dramatic and good.

For foam, threshold on height: pos.y > 0.4 or so.

Hmm, but with the mean at 0 and standard deviation ~0.35, crests above 0.5 are rare-ish. Foam should appear on maybe 10% of the surface. Let's tune: smoothstep(0.15, 0.75, pos.y) — that gives substantial foam at 0.6+.

I'll make it adaptive-ish: foam = smoothstep(0.2, 0.7, h) * steepness factor. Plus noise modulation.

OK, let's write the final shader.

One more consideration: the number of raymarch iterations and the pixel scale. Let's set pixel scale so total pixels ≤ ~700k.

Let me write the JS:

```js
const canvas = document.getElementById('c');
const gl = canvas.getContext('webgl2', {antialias:false, alpha:false, powerPreference:'high-performance'});
if(!gl){ document.body.innerHTML = 'WebGL2 not supported'; }

const vsSource = `#version 300 es
in vec2 aPos;
void main(){ gl_Position = vec4(aPos, 0.0, 1.0); }`;

const fsSource = `...`;

function compile(type, src){...}

const prog = ...
const vao = gl.createVertexArray();
gl.bindVertexArray(vao);
const buf = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, buf);
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 3,-1, -1,3]), gl.STATIC_DRAW);
const loc = gl.getAttribLocation(prog, 'aPos');
gl.enableVertexAttribArray(loc);
gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);

const uRes = gl.getUniformLocation(prog, 'iResolution');
const uTime = gl.getUniformLocation(prog, 'iTime');
```

Resize handler sets canvas.width/height with scaling.

Render loop with requestAnimationFrame, timestamp in ms → seconds.

Note: the vertex array must be bound at draw time — with a single VAO we bind once and it stays bound (unless something unbinds). Fine.

Full-screen triangle: positions (-1,-1), (3,-1), (-1,3) covers the screen. Good.

Let's write out the fragment shader fully:

```glsl
#version 300 es
precision highp float;
out vec4 fragColor;
uniform vec2 iResolution;
uniform float iTime;

const float PI = 3.14159265359;

float hash21(vec2 p){
  p = fract(p * vec2(123.34, 456.21));
  p += dot(p, p + 45.32);
  return fract(p.x * p.y);
}

float noise2(vec2 x){
  vec2 i = floor(x);
  vec2 f = fract(x);
  vec2 u = f*f*(3.0 - 2.0*f);
  float a = hash21(i);
  float b = hash21(i + vec2(1.0, 0.0));
  float c = hash21(i + vec2(0.0, 1.0));
  float d = hash21(i + vec2(1.0, 1.0));
  return mix(mix(a,b,u.x), mix(c,d,u.x), u.y);
}

const mat2 ROT = mat2(0.80, 0.60, -0.60, 0.80);

float fbm(vec2 p){
  float s = 0.0;
  float a = 0.5;
  for(int i = 0; i < 4; i++){
    s += a * noise2(p);
    p = ROT * p * 2.03;
    a *= 0.5;
  }
  return s;
}
```

Careful: `mat2` constant at global scope in GLSL ES 3.0 — `const mat2 ROT = mat2(...)` should be fine.

Ocean height and normal as discussed.

Sky function.

Main.

Let me write skyColor carefully:

```glsl
vec3 skyColor(vec3 rd, vec3 sunDir, float t){
  float y = max(rd.y, 0.0);
  vec3 zenith = vec3(0.035, 0.055, 0.115);
  vec3 horizon = vec3(0.30, 0.17, 0.155);
  vec3 col = mix(horizon, zenith, pow(y, 0.40));

  float sd = max(dot(rd, sunDir), 0.0);
  
  // clouds
  if(rd.y > 0.001){
    vec2 uv = rd.xz / (rd.y + 0.14);
    uv = uv * 0.65 + vec2(t * 0.018, t * 0.007);
    float n1 = fbm(uv * 0.9);
    float n2 = fbm(uv * 2.3 + 11.3);
    float dens = smoothstep(0.38, 0.80, n1 * 0.85 + n2 * 0.45);
    dens *= smoothstep(0.0, 0.12, rd.y);   // fade at horizon
    float lit = pow(sd, 2.5);
    vec3 cDark = vec3(0.055, 0.060, 0.085);
    vec3 cLit  = vec3(0.75, 0.36, 0.20);
    vec3 ccol = mix(cDark, cLit, lit * 0.85 + 0.08);
    // subtle bright rim
    ccol += vec3(1.0,0.5,0.2) * pow(sd, 12.0) * 0.5;
    col = mix(col, ccol, dens * 0.92);
  }
  
  // sun glow
  col += vec3(1.0, 0.40, 0.12) * pow(sd, 8.0) * 0.7;
  col += vec3(1.0, 0.28, 0.06) * pow(sd, 2.2) * 0.22;
  
  // sun disc
  float disc = smoothstep(0.9990, 0.99965, sd);
  col += vec3(1.0, 0.66, 0.30) * disc * 6.0;
  
  return col;
}
```

Hmm, `dens *= smoothstep(0.0, 0.12, rd.y)` will fade clouds right at the horizon. That's a bit odd — clouds should be visible down to the horizon. But the uv blows up near the horizon (uv → rd.xz/0.14, magnitude up to ~7) so clouds become tiny near horizon. It's fine either way; let's use a milder fade or none. Actually the smoothstep(0.0,0.12) fade means that at the horizon the sky is clean, which gives a nice clear sunset band. I'll keep a subtle version: smoothstep(0.0, 0.06, rd.y).

Hmm, the sun disc at low altitude with clouds: sunDir.y = 0.075/|(0.42,0.075,-1)| ≈ 0.075/1.087 ≈ 0.069. So the sun is at elevation ~4°. Its elevation angle in the sky. The camera pitch is about -0.055 rad ≈ -3°, so the sun appears slightly above center. Good.

Now `pow(sd, 8.0)*0.7` — at sd=1 near the sun that's 0.7. Plus pow(sd,2.2)*0.22. So near the sun we get bright orange. Good.

Water color function. Let me write main's ocean branch:

```glsl
vec3 shadeOcean(vec3 ro, vec3 rd, vec3 sunDir, float t, float dist, vec3 pos, out float alpha)
```

Let me just inline it in main to keep it simpler, or write a function returning the color and a "hit" flag.

Actually, since I need to blend with sky, I'll write it inline.

Main:

```glsl
void main(){
  vec2 res = iResolution;
  vec2 uv = (gl_FragCoord.xy - 0.5*res) / res.y;
  float t = iTime;
  
  // --- camera ---
  float bobY = sin(t*1.13)*0.14 + sin(t*2.37)*0.05;
  float bobX = sin(t*0.53)*0.30;
  float bobZ = cos(t*0.41)*0.30;
  vec3 ro = vec3(bobX, 2.45 + bobY, bobZ);
  
  float pitch = -0.075 + sin(t*0.83)*0.022 + sin(t*1.61)*0.008;
  float roll  = sin(t*0.71)*0.030;
  float yaw   = sin(t*0.29)*0.05;
  
  vec3 fwd = normalize(vec3(sin(yaw)*cos(pitch), sin(pitch), -cos(yaw)*cos(pitch)));
  vec3 right = normalize(cross(fwd, vec3(0.0,1.0,0.0)));  // hmm sign
  vec3 up = cross(right, fwd);
```

Careful with handedness. For a right-handed system with fwd = -z, up = +y, right should be +x. cross(fwd, up) = cross((0,0,-1),(0,1,0)) = (0*0 - (-1)*1, (-1)*0 - 0*0, 0*1 - 0*0) = (1, 0, 0). Yes! So right = cross(fwd, worldUp). Good.

Then up = cross(right, fwd)? cross((1,0,0),(0,0,-1)) = (0*(-1) - 0*0, 0*0 - 1*(-1), 0) = (0, 1, 0). Good.

Then apply roll by rotating right and up around fwd:
```
  right = right*cos(roll) + up*sin(roll);
  up = cross(right, fwd);  // re-orthogonalize... 
```
Hmm, that may flip. Let's just do:
```
vec3 r2 = right*cos(roll) + up*sin(roll);
vec3 u2 = -right*sin(roll) + up*cos(roll);
right = r2; up = u2;
```
Fine.

Ray:
```
  float focal = 1.5;
  vec3 rd = normalize(fwd*focal + right*uv.x + up*uv.y);
  vec3 sunDir = normalize(vec3(0.42, 0.075, -1.0));
  
  vec3 col = skyColor(rd, sunDir, t);
  
  // --- ocean ---
  if(rd.y < 0.0){
    float tmax = 420.0;
    float tt = 0.25;
    float prevT = tt;
    float hitT = -1.0;
    for(int i = 0; i < 96; i++){
      vec3 p = ro + rd*tt;
      float h = oceanH(p.xz, t);
      float d = p.y - h;
      if(d < 0.0){ hitT = tt; break; }
      prevT = tt;
      tt += max(0.06, d * 0.45);
      if(tt > tmax) break;
    }
    if(hitT > 0.0){
      // refine
      float a = prevT, b = hitT;
      for(int i = 0; i < 6; i++){
        float m = 0.5*(a+b);
        vec3 pm = ro + rd*m;
        if(pm.y - oceanH(pm.xz, t) > 0.0) a = m; else b = m;
      }
      float td = 0.5*(a+b);
      vec3 pos = ro + rd*td;
      vec3 n = oceanNormal(pos.xz, t);
      ...
    }
  }
```

Wait: `oceanH` normal uses e=0.15 and 4 evaluations; but with the noise frequencies up to q*9.3*2.03^3 ≈ 9.3*8.4 = 78 * 0.22 = 17 cycles per unit... hmm, wait. q = p*0.22, then layer freq 9.3 → p*2.05, then fbm's internal octaves ×2.03 each up to 2.03^3 = 8.4 → frequency 17 per unit → wavelength 0.06 units. That's very fine detail. With e=0.15 that's massively undersampled → noise. Hmm.

Let me reduce: the highest layer frequency should have a wavelength of at least ~0.5 units. Layer freq of 9.3 with q=p*0.22 gives p*2.05 with base wavelength 0.5. Then the fbm's 4th octave is 8× that → wavelength 0.06. Way too fine, will alias badly.

Options: in the normal computation, use a larger epsilon (like 0.3), or reduce the max frequency. Let's use a larger epsilon for normals: e = 0.25? Then the finest detail is smoothed but still aliased.

Better: cut down the fine octaves. Let's use 3 octaves in fbm → 2.03^2 = 4× the base. Then the highest frequency layer: p*2.05*4 = 8.2 per unit → wavelength 0.12. Still small.

Alternatively reduce the layer frequencies: use 1.0, 2.0, 3.9, 7.3 with q = p*0.18. Then layer 4 base = p*1.31, ×4 (3 octaves) = 5.25 → wavelength 0.19. Hmm.

Actually, aliasing in the far field is inevitable regardless; the waves are far away but the screen-space frequency matters. At distance 400 with a wavelength of 0.5 units, that's way below a pixel. So we need either LOD or accept noise. Realistically, distant water in these shaders always has this problem. The fog helps hide it — at 400 units the fog is 90%, so noise is mostly washed out. At 50 units, a 0.12 wavelength = 8 pixels... it's OK-ish.

Hmm, actually the pixel footprint at distance d for a screen of height H pixels and vertical FOV ~ 0.63 rad is about d*0.63/H per pixel in world units. At d=50, H=800: 0.04 units/pixel. So a 0.12 wavelength is 3 pixels — borderline but acceptable. At d=100, 0.08/pixel → under-sampled. But fog at 100 = 1-exp(-0.55) = 42%, so partly hidden.

Let's keep total octaves modest: fbm with 4 octaves but highest layer amplitude 0.12 (small contribution), so aliasing is low-amplitude. Fine. And use normal epsilon 0.2 for a smoother normal.

Actually, let me just use e = 0.18 and fbm with 4 octaves. It'll be fine.

Alternatively, I could reduce the highest-frequency layer's contribution in the height (0.12 weight) — already small.

OK, moving on.

Now the shading:

```glsl
      vec3 n = oceanNormal(pos.xz, t);
      vec3 viewDir = -rd;
      
      // fresnel
      float fres = 0.02 + 0.98 * pow(1.0 - max(dot(viewDir, n), 0.0), 5.0);
      
      // reflection
      vec3 refl = reflect(rd, n);
      refl.y = max(refl.y, 0.002);
      vec3 skyRefl = skyColor(normalize(refl), sunDir, t);
      
      // deep water body colour
      float ph = pos.y;
      vec3 deepCol = vec3(0.008, 0.022, 0.035);
      vec3 crestCol = vec3(0.05, 0.10, 0.12);
      vec3 body = mix(deepCol, crestCol, smoothstep(-0.6, 1.0, ph));
      
      // subsurface glow from sun through crests
      float sss = pow(max(dot(n, sunDir), 0.0), 2.0) * smoothstep(-0.2, 0.9, ph);
      body += vec3(0.35, 0.13, 0.03) * sss;
      
      vec3 water = mix(body, skyRefl, fres);
      
      // specular sun highlight
      vec3 H = normalize(sunDir + viewDir);
      float sp = max(dot(n, H), 0.0);
      float spec = pow(sp, 600.0) * 5.0 + pow(sp, 60.0) * 0.35;
      water += vec3(1.0, 0.52, 0.22) * spec;
      
      // foam
      float steep = 1.0 - n.y;
      float fh = smoothstep(0.25, 0.95, ph);
      float fs = smoothstep(0.06, 0.30, steep);
      float fn = fbm(pos.xz * 1.6 + vec2(t*0.25, -t*0.18));
      float foam = fh * (0.35 + 0.9 * fs) * (0.45 + 1.1 * fn);
      foam = smoothstep(0.42, 0.95, foam);
      vec3 foamCol = vec3(0.80, 0.80, 0.82) * (0.15 + 0.85 * clamp(dot(n, sunDir)+0.25, 0.0, 1.0));
      foamCol += vec3(1.0, 0.45, 0.15) * spec * 0.5;
      water = mix(water, foamCol, foam);
```

Hmm, foamCol with dot(n,sunDir): the sun is near the horizon so the dot with a mostly-up normal is small (~0.07). Then foamCol = 0.8 * (0.15+0.85*0.32) = 0.8*0.42 = 0.34. Darkish foam. Let's use a different lighting: add ambient sky: foamCol = vec3(0.75) * (0.25 + 0.9*max(dot(n,sunDir),0.0)) + sky ambient. Let's just make it vec3(0.62,0.60,0.58) base and add sun tint. It's a storm — foam is greyish white.

Simplify: 
```
vec3 foamCol = vec3(0.70, 0.70, 0.72);
foamCol *= 0.45 + 0.55*clamp(dot(n, normalize(vec3(sunDir.x, 0.35, sunDir.z))), 0.0, 1.0);
```
Eh. Let's keep: `vec3 foamCol = vec3(0.62, 0.63, 0.66) + vec3(0.45,0.22,0.08)*max(dot(n,sunDir),0.0)*2.0;` Something like that. I'll go with something reasonable.

Then fog:
```
      float dist = td;
      float fogAmt = 1.0 - exp(-dist * 0.0060);
      vec3 fogCol = skyColor(normalize(vec3(rd.x, 0.03, rd.z)), sunDir, t);
      water = mix(water, fogCol, clamp(fogAmt, 0.0, 1.0) * 0.95);
      col = water;
```

Wait, skyColor with rd.y = 0.03 gives horizon color plus the sun glow if the azimuth points toward the sun. That's good for a sunset horizon glow.

Hmm, but `normalize(vec3(rd.x, 0.03, rd.z))` — rd.x, rd.z normalized in the horizontal plane. Then y=0.03/1 ≈ 0.03. OK.

Then the fog color also includes the sun's glow term `pow(sd,8)*0.7` which for a nearly-horizontal direction toward the sun gives a strong glow → the water near the horizon toward the sun gets a nice orange glow. 

One issue: the fog color at the horizon is bright orange near the sun, but the water surface right there reflects the sky too, doubling up. Acceptable.

Now, about the "storm" look: dark clouds, dark water. Good.

Let's double check the sun direction and camera. Camera faces -z with a slight yaw wobble. Sun at (0.42, 0.075, -1) normalized → azimuth to the right and forward. Good, sun visible in the right part of the frame, low.

Reflection of the sun on the water: the glitter path extends from the horizon below the sun toward the camera. Good.

Now, potential issue: the sun disc added after clouds in skyColor — in the water reflection, the reflected ray toward the sun also includes the disc, giving a bright spot. Good.

Now the horizon line: The transition where the ocean ends. Rays with rd.y >= 0 show pure sky. Rays with rd.y < 0 show ocean fading into fog. The fog at max distance (420) is 1-exp(-2.52) = 0.92, so 8% of the ocean color remains — nearly invisible. And the sky just above the horizon is the horizon gradient color (0.30, 0.17, 0.155) plus glow. The fog color at the horizon is the same, so it matches. 

One more: `skyColor` for rays with rd.y slightly negative — the `col = mix(horizon, zenith, pow(y,0.4))` with y=0 gives horizon color, and no clouds. Fine, matches the fog.

Now, the ocean raymarch for rays with rd.y < 0 but very close to 0 will not hit within 420 → then `hitT < 0` and we just keep the sky color. Good.

Performance concern: for rd.y < 0, we always do up to 96 iterations. For rays that miss (near horizon), we do all 96. That's a lot. Let's reduce: since the near-horizon rays have d = p.y - h starting at 2.45 and decreasing slowly, the step is max(0.06, d*0.45) — for the first steps d~2.4 so step ~1.1, and tt increases geometrically-ish. Actually tt increases by d*0.45 where d decreases as tt increases... For a ray with rd.y = -0.01, at tt=100, p.y = 2.45-1 = 1.45, h ~ 0, d=1.45, step 0.65. At tt=200, p.y=0.45, d~0.45, step 0.2. At tt=245 it hits. That's roughly... the step shrinks linearly, so it takes many iterations. Number of iterations ~ integral. Starting at tt=0.25 with step ~1.1, then steps shrink... Actually the step size is proportional to the remaining distance to the surface, so it's like exponential approach: tt_{n+1} = tt_n + 0.45*d where d = 2.45 + rd.y*tt ≈ 2.45 - 0.01*tt. This is a linear ODE: dtt/dn = 0.45*d, d = 2.45 - 0.01*tt. Solution... it converges slowly. Hmm.

With 96 iterations, starting at 0.25 with step ~1, the distance grows roughly like: it's like compound interest but decreasing. Let's just estimate: the step is 0.45 * d where d decreases by 0.01 per unit tt. tt goes 0.25 → 1 → 2.3 → 5 → 10.5 → 21 → 41 → 79 → 150 → 250... roughly doubling each time initially. So 96 iterations gets far beyond 420. Actually for near-horizon rays, we break at tt > 420 which happens around iteration ~20-30. So it's fine! Because the step grows when d is large.

Wait but the step is capped by d*0.45 and d starts at 2.45, so the initial steps are ~1.1. tt: 0.25, 1.35, 2.55, ... growing by ~0.45*d. Since d decreases slowly, this is roughly geometric with ratio 1.45 while d is large... Actually d = 2.45 - 0.01*tt, so tt_{n+1} = tt_n + 0.45*(2.45-0.01*tt_n) = 1.1025 + tt_n*(1 - 0.0045)... that's nearly additive, so it grows linearly at ~1.1 per step! That's bad — 420/1.1 = 380 steps.

Hmm right, because rd.y is tiny so d barely decreases. For a steep ray (rd.y = -0.5), d decreases fast and the step... p.y at tt is 2.45 - 0.5*tt, hits at tt=4.9. Steps: 0.25, 0.25+0.45*2.32=1.29, d=2.45-0.645=1.8, step 0.81 → 2.1, d=1.4, step 0.63 → 2.73, d=1.08, step 0.49 → 3.22, d=0.84, step 0.38... converges to 4.9 in ~10 steps. Good.

For grazing rays, we need a better strategy. Options: cap the max distance lower, or use a step that grows with tt even when d is nearly constant. Use `tt += max(0.06, d*0.45, tt*0.02)`? Hmm, that would make the steps grow geometrically for far distances: step_min = tt*0.05 → grows. Then for the grazing ray, tt goes 0.25 → 0.26 → ... slow initially but accelerates. Let's use `tt += max(0.06, d*0.45, tt*0.03)`. With tt*0.03, after 100 units the step is 3. That gives geometric growth. Total iterations to reach 420: from 0.25 growing at 3% per step → 0.25*1.03^n = 420 → n = ln(1680)/ln(1.03) = 7.4/0.0296 = 250 steps. Still too many. Use 8%: n = 7.4/0.077 = 96. Hmm.

Alternatively reduce tmax to 250 and increase fog so it's fully opaque at 250: k such that exp(-250k) = 0.05 → k = 0.012. But then near water (50 units) fog = 45%. That's too foggy for 50 units.

Hmm. Actually maybe it's fine — a stormy sea with heavy haze. But the waves at 50 units would be washed out.

Better approach: make the fog distance-dependent in a way that matches the horizon. Or: instead of a hard max distance, handle the "miss" case by blending to the sky horizon color.

Alternative: for rays with rd.y > -0.02 (near horizon), just skip the ocean march and use the sky/horizon. That limits the max distance to 2.45/0.02 = 122 units. With fog at 122: 1-exp(-0.012*122) = 1-exp(-1.46) = 0.77. Not quite opaque but the remaining 23% of the ocean color... hmm.

Let's combine: use gradient-adaptive stepping AND a horizon cutoff.

Actually the simplest robust fix: use the step `tt += max(0.06, d*0.45, tt*0.05)`. With 5% growth: n = ln(420/0.25)/ln(1.05) = 7.4/0.0488 = 152 steps. Too many at 96 max. With 8%: 96 steps. So exactly borderline.

Hmm, but the growth `tt*0.05` only kicks in when tt > 0.45*d/0.05... let's see: d*0.45 vs tt*0.05 → tt > 9d. For d~2.4, tt > 21.6. So the growth term dominates for tt > ~22. Then from 22 to 420 with 8% growth = ln(19)/0.077 = 38 steps. Plus the initial ~20 steps to get to 22. Total ~60 steps. That fits in 96. 

Let's use `tt += max(0.08, d*0.45, tt*0.08)`. Starting: step = max(0.08, 1.1, 0.02) = 1.1. tt: 0.25, 1.35, 2.55, ... The d*0.45 term dominates while d is large. d = 2.45 - |rd.y|*tt. With rd.y = -0.001, d ≈ 2.42, step ≈ 1.09. tt reaches 22 after ~20 steps in a roughly linear fashion (since d decreases slowly). Then the tt*0.08 term takes over: step = 1.76, 1.9, ... geometric. From 22: 22*1.08^n = 420 → n = ln(19)/0.077 = 38. Total 58 steps. Good, under 96.

But quality: the step of 1.1 at tt=0.25-22 means we skip over waves — for a grazing ray, we'd miss crests. But at those distances the waves are near the horizon, small on screen. Acceptable. Though a step of 1.1 world units at distance 10 could miss a wave crest of height 0.5... but for grazing rays, the ray is only 1.1 above the surface at 10 units... Actually d = p.y - h, and p.y decreases slowly; the wave height field varies ±0.8 with a wavelength of ~4. A step of 1.1 could miss the peak of a wave. It would still hit somewhere in the trough. The result: the ray hits the surface slightly past the crest. That's an error of ~1 unit at distance 10 — a visible artifact maybe. But it's smoothed out by the waves being similar.

Alternative: use a proper distance bound. Since the height field is bounded |h| <= Hmax, we can use the safe step: the vertical distance d = p.y - h >= p.y - Hmax. For a ray with rd.y < 0, the distance to the surface along the ray is at most... if p.y > Hmax, then no hit yet, and we can advance to where p.y = Hmax: step = (p.y - Hmax)/(-rd.y). That's the classic "cone tracing" for height fields! Since the max height is known (say Hmax = 1.3), we can safely jump.

```
float Hmax = 1.4;
if(p.y > Hmax){
  tt += (p.y - Hmax)/(-rd.y) * 0.95;  // safe
} else {
  tt += max(0.02, ...);
}
```
Hmm, that's a valid conservative bound: while p.y > Hmax, the ray cannot hit the surface. Excellent — this makes near-horizon rays reach far distances in logarithmic steps too? Let's see: p.y > Hmax means tt < (2.45-1.4)/|rd.y| = 1.05/|rd.y|. For rd.y = -0.001, that's tt < 1050 — beyond our range. And the step = (p.y - Hmax)/0.001 * 0.95 which starts at 1.0. So with rd.y = -0.001, the step per iteration ≈ (2.45 - 1.4 - 0.001*tt)/0.001 = 1050 - tt. So tt_{next} = tt + 0.95*(1050-tt) → converges to 1050 geometrically with ratio 0.05! That's fast: from 0.25 to 1050, ~4 iterations. But wait, that overshoots — the ray will never hit because the surface max is 1.4 and the ray is at 1.4 at tt=1050, and beyond that the ray is below the max height but the actual surface... The step is conservative as long as it stays above Hmax. Once below, we need fine steps. But with 0.95 factor, it will converge to where p.y ≈ Hmax, and then the fine stepping begins. That's efficient.

Actually good: use the safe cone step when p.y > Hmax, else use small steps (d*0.45 min 0.02).

But careful about the 0.95 factor — with a factor of 1.0 it converges exactly to p.y = Hmax; with 0.95 it approaches asymptotically. Let's use 0.98.

Hmm, but this makes the ray march jump right to the point where p.y = Hmax, which might be far away (tt = 1050), and if we then break at tmax=420, we never get there. Let's see: tt goes 0.25 → 0.25+0.98*(1050-0.25)= 1029 → break at tmax. Two iterations. 

For rd.y = -0.01: p.y = Hmax at tt = 105. Step 1: 0.25 + 0.98*104.75 = 102.9 → then p.y = 2.45 - 1.029 = 1.42 ≈ Hmax. Then below Hmax, we start fine stepping. Hmm, but at that point we're at tt=103 and p.y=1.42 while the actual surface at that point might be at h=0.5, so we're 0.9 above. The fine stepping then needs to find the surface: d = 0.9, step 0.4... and the ray descends at 0.01/unit, so it takes 0.4/0.01 = 40 units to descend 0.4. With step = d*0.45 = 0.4, that's 100 iterations. Bad.

Hmm, the issue is that when the ray is shallow, d decreases slowly, so d*0.45 steps are small in tt terms. We need the step in tt to be bounded below by something related to the descent rate. Actually the correct step for a heightfield ray march when heading down: the step should be limited by how much d changes, which is |rd.y| * step. So the step in tt should be ~ d/|rd.y| (that would take us to d=0). Since d can't be reduced faster than |rd.y|*tt, the optimal step is d/|rd.y| — which is huge. But the surface height varies, so d can drop faster where the terrain rises.

Combined bound: the safe step is determined by BOTH the max height AND the max slope of the terrain in the horizontal direction. If the terrain slope is bounded by S, then moving horizontally by dt*xz-amount changes h by at most S * horizontal distance. 

A common approach: d_ray = p.y - h; descend at rate |rd.y| per unit tt; terrain can rise at rate S * |rd.xz| per unit tt. So the minimum approach rate is (|rd.y| + S*|rd.xz|)... Actually the safe step is d / (|rd.y| + S*|rd.xz|) if the terrain's slope is bounded by S. But the terrain here has slopes up to maybe 1.5 (steep waves). Then the safe step is d/(0.01 + 1.5*1.0) = d/1.51. For d=0.9, that's 0.6. Still slow for the shallow ray.

Hmm, but wait: with a slope bound of S=1.5, a ray descending at 0.01/unit while the terrain rises at 1.5/unit will hit the terrain within 0.6 units — so the step of 0.6 IS correct and safe. But then d after the step would be 0.9 - 0.01*0.6 = 0.89 (if the terrain doesn't rise). So we'd need many steps to cover 400 units. That's the fundamental problem with shallow rays over a flat-ish plane: they travel a long way.

But physically, the ray at rd.y=-0.01 from height 2.45 hits the mean water level at tt=245. The terrain is ±0.8 around the mean. So it hits somewhere between tt=165 and tt=325. We can't skip that.

So realistically, we need ~100+ steps for near-horizon rays OR we accept approximations.

Pragmatic solution: limit the ocean to a max distance of ~250 and increase fog. Or use a two-phase approach: coarse steps in the far region.

Alternatively: for shallow rays, use a fixed large step (like 2-5 units) since the waves at that distance are subpixel anyway. The key insight: at tt > 60, the wave detail is smaller than a pixel, so precision doesn't matter — only the average height (~0) matters. So we can use big steps.

So: step = max(0.06, d*0.45) normally, but if tt > 60, use step = max(tt*0.04, d*0.45). At tt=60, step becomes 2.4 (growing). From 60 to 420 with 4% growth: ln(7)/0.039 = 50 steps. Plus the ~30 steps to reach 60 = 80 total. Hmm, tight but within 96.

Let's use tt*0.06 for tt>40: from 40, ln(10.5)/0.058 = 41 steps. Plus ~25 to reach 40 = 66. OK.

Actually, let's simplify: step = max(0.05, d*0.45, tt*0.045) always. For small tt, tt*0.045 is tiny so it doesn't matter. Let's compute the total iteration count for a near-horizon ray:
- tt=0.25, step = max(0.05, 1.08, 0.011) = 1.08 → tt=1.33
- ... d stays ~2.4 until tt gets large. Steps ≈ 1.08 each, so tt grows ~1.08/step. From 0.25 to 21 (where tt*0.045 = 0.95 ≈ 1.08), that's ~19 steps. 
- Then the tt term dominates: step = 0.045*tt, geometric ratio 1.045. From 21 → 420: ln(20)/0.044 = 68 steps.
Total ~87 steps. Within 96 but barely.

Use 0.06: crossover at tt*0.06 = 1.08 → tt = 18. From 18 → 420 with ratio 1.06: ln(23)/0.058 = 54 steps. Total ~19+54 = 73. Good.

But at tt=60, step = 3.6 — that's a big step. It could cause the ray to skip over the surface entirely (if d is small) or to hit far past the true hit. For rays at tt>60, hmm, the horizontal distance is ~60, and a step of 3.6 means we check every 3.6 units. Waves have a ~4-unit wavelength, so we could miss a crest entirely and hit the next trough. But we're at 60+ units distance where a wave of height 0.8 subtends a small angle... at 60 units distance and camera height 2.45, the angular size of a 0.8-unit wave is 0.013 rad, and with a vertical FOV of 0.67 rad over 800 pixels, that's 16 pixels. Hmm, that's significant! Missing a wave crest at 60 units would be visible.

Hmm. But actually the d*0.45 term would still apply if d is small. The step is the max of the three, so a big step only occurs if d is large... no wait, max means we take the LARGEST. That's wrong! The safe step should be the MINIMUM of the bounds, except for the tt-growth term which is a hack. 

The issue: with linear growth (max of d*0.45 and a tt-proportional term), we take the larger. That's unsafe near the surface. But when d is small (near the surface), d*0.45 is small, and taking the max with tt*0.06 would jump over the surface. Bad.

So: use the tt-growth term ONLY when d is large relative to the step. I.e.:
```
float step = max(0.06, d*0.45);
if(tt > 25.0) step = max(step, tt*0.05);  // hmm still unsafe
```

Better: combine as `step = max(d*0.45, min(tt*0.05, d*2.5))`. So the growth term can't exceed 2.5*d — meaning we never jump more than 2.5 times the clearance. When d is small, the step is limited to 2.5d. Hmm, but that's still 2.5x the clearance which could overshoot a crest... d*0.45 means we advance less than half the clearance, which is safe for gentle terrain. 2.5d could overshoot.

OK, alternative: make the growth factor apply to tt but cap the total step: `step = min(max(0.06, d*0.45), ...)`. Hmm.

Let me think differently. The real issue is the far region. What if I just clip the ocean at a distance where the waves are ~1 pixel, and use fog to blend? At distance D, the wave of height 0.8 subtends 0.8/D rad. For that to be under ~1.5 pixels with 800px over 0.67 rad: 0.8/D < 0.00125 → D > 640. Hmm, so far.

But honestly, at 640 units the fog is 1-exp(-0.006*640) = 98%. So the far region contributes almost nothing but costs a lot.

Compromise: tmax = 200 and fog k = 0.011 (at 200: 89% fog; at 100: 67%; at 50: 42%; at 20: 20%). That's a foggy, misty storm. Actually that could look quite atmospheric and matches the "subtle fog near the horizon" requirement... though 67% fog at 100 units is not subtle.

Hmm. Let's reconsider: maybe use a nonzero fog that's more like a haze that increases with distance, plus a horizon blend.

Actually, let's reconsider the geometry. The camera is at 2.45 units. The waves are ±0.8. So a ray going down at -0.01 hits the surface at ~245 units. At that distance the surface is at screen position... The horizon is at rd.y = 0, and the ray at -0.01 rad below. With a FOV of 0.67 rad and 800 px, 0.01 rad = 12 pixels below the horizon. So the region between the horizon and 12 pixels below is beyond 245 units. That's a thin band. Rays that hit at 100 units have rd.y ≈ -(2.45)/100 = -0.0245 → 29 pixels below the horizon. So the ocean from 29 pixels below the horizon to the horizon is the far region (100+ units).

Given the screen is ~800 px tall, that band is 29 px — small but noticeable. Using big steps there costs accuracy but the fog covers a lot.

So let's plan: tmax = 300, fog k = 0.009 (at 300 → 93%). Rays hitting between 245 and 300 are covered by fog.

For the stepping, I'll use:
```
float step = max(0.05, d*0.45);
// accelerate in the far field, but never jump more than 3x the clearance
if(tt > 30.0) step = max(step, min(tt*0.06, d*3.0));
```
Hmm, when d is 2.4 and tt=30, min(1.8, 7.2) = 1.8 vs d*0.45=1.08 → step 1.8. When d=0.5 and tt=100: min(6, 1.5) = 1.5 vs 0.225 → step 1.5. That jumps 3x the clearance — could overshoot a crest by up to 1.5 units when the clearance is 0.5. That would produce a visible artifact where the ray passes through a crest.

Hmm, but actually a "pass-through" would mean the ray goes under a wave and continues... and then it might hit the backside later or exit. Since we're marching along a ray that's descending slowly, if we jump past the crest, we'd continue and possibly never hit (d becomes negative? no, if we pass through a crest, d was positive before and after... ). Actually the issue: if the ray passes through a crest, the subsequent d could be negative (below the surface), and then we'd detect a hit at a wrong location. Since we only check d<0, if we jumped over a crest and landed where d<0, we'd report a hit there. If we land where d>0, we continue.

We'd only detect a hit if we land below the surface. If we jumped clean over the crest and back above the surface (unlikely for shallow rays), we'd miss it entirely.

I think in practice, the visual artifact is minor in the far field. Let's go with a moderate acceleration and accept it.

Actually, you know what? Let me reduce the wave amplitude in the far field... no, too complex.

Alternative much simpler approach: reduce the maximum view distance by tilting the camera down more and... no.

Let me just be pragmatic: tmax = 260, fog k = 0.011. At 260 → 94%. At 100 → 67%. Hmm, that's a lot of fog at 100 units. But the waves at 100 units are quite far — with a camera height of 2.45 and waves of ~1, waves at 100 units are pretty small on screen. Fog at 67% means they're heavily faded. It could look like a hazy stormy sunset. Honestly that might look great.

Hmm, but "subtle fog near the horizon" — the requirement. Let's use k = 0.0075: at 100 → 53%, at 200 → 78%, at 300 → 89%. And tmax = 350. Compromise. The far band would be at 350/... the horizon band.

I'll go with k ≈ 0.008 and tmax = 320.

And for stepping, use: `step = max(0.06, d*0.45)` and if tt > 40, `step = max(step, min(tt*0.05, d*2.0))`.

Hmm, d*2.0 when d is small... Let me think about the near-surface case for a steep ray. For a steep ray, d decreases fast; the tt*0.05 term only matters when tt*0.05 > d*0.45, i.e., tt > 9d. For a steep ray at tt=40, d might already be 0.2, so 9d = 1.8 < 40 → the term applies: min(2.0, 0.4) = 0.4 which is > d*0.45=0.09. So the step becomes 0.4 with d=0.2 → overshoot. Bad!

OK so the acceleration should only apply when d is large. Let's condition on d: `if(d > 0.3) step = max(step, min(tt*0.05, d*0.8));`. With d*0.8, we advance 80% of the clearance — safe-ish for gentle terrain. And with d>0.3 it only kicks in far from the surface.

Hmm, but for a shallow ray, d stays ~2.4 for a long time, so the acceleration applies. For a steep ray, d drops below 0.3 quickly and the acceleration stops. 

Let's estimate the near-horizon ray again: d ≈ 2.4 - 0.01*tt. For tt < 100, d > 1.4. Step = max(0.06, 0.45d, min(0.05tt, 0.8d)). At tt=40: min(2, 1.9) = 1.9 > 0.45*2.1=0.95 → step 1.9. tt=42 → step = min(2.1, 1.9)=1.9... it grows. Let's just say the step is ~0.8d = 1.9, growing as tt grows. tt goes 40, 42, 44... no wait, step = min(0.05*tt, 0.8*d). At tt=40, 0.05*40=2, 0.8*2.05=1.64 → step 1.64. tt=41.6 → 0.05*41.6=2.08, 0.8*2.03=1.62 → 1.62. So it's ~1.6 per step. That's linear, not geometric! Because 0.8*d stays ~1.6. Damn.

The constraint d*0.8 is what limits it. So it's still linear at ~1.6/step. From 40 to 320: 175 steps. Way too many.

OK. The fundamental tension: we can't safely advance more than ~d, and d decreases slowly for shallow rays.

Real solution: for shallow rays, the terrain height variation is small compared to d, so we can use a "heightfield cone" bound: d_safe = (p.y - Hmax) / (|rd.y| + S*L) where... no.

Hmm wait. Actually let's reconsider. For a shallow ray at tt=40 with d=2.05, the surface max height is Hmax=0.9. The clearance above Hmax is 2.45 - 0.01*40 - 0.9 = 1.15. The ray descends at 0.01/unit, so it will take 115 more units to reach Hmax. So we can safely advance 115 units! (times a safety factor).

So the correct bound: while p.y > Hmax, advance by (p.y - Hmax)/(-rd.y) * 0.95. That's the cone bound I mentioned. For a shallow ray this is a huge jump.

Let's redo: for a shallow ray with rd.y = -0.01 and p.y = 2.05 at tt=40, the jump is (2.05-0.9)/0.01*0.95 = 109 → tt = 149. Then p.y = 2.45-1.49 = 0.96 ≈ Hmax. Then jump again: (0.96-0.9)/0.01*0.95 = 5.7 → tt=155. Then p.y=0.9. Now we're at the max height level, and the actual h at that point might be 0.5, so d = 0.4. Then fine stepping with d*0.45 = 0.18 per step, and the ray descends at 0.0016 per step... it would take 250 steps to descend to the surface. Ugh again!

The problem: at the Hmax level, the ray is nearly parallel to the water and the actual surface is below. It descends very slowly.

But here's the thing: since the surface is bounded by ±Hmax and varies, and the ray is nearly horizontal, the ray WILL eventually intersect the surface where the terrain rises. But it could take hundreds of units.

Hmm, so realistically for shallow rays we should just say: this ray hits the surface at "very far" and it's essentially fog. We can cap tmax and give up.

OK, final decision: cap tmax at ~250, use the cone bound for efficiency, and use strong-ish fog. Let's do:

```
float Hmax = 1.0;
for(...){
  vec3 p = ro + rd*tt;
  float h = oceanH(p.xz, t);
  float d = p.y - h;
  if(d < 0.0){ hitT = tt; break; }
  prevT = tt;
  float step;
  if(p.y > Hmax){
    step = (p.y - Hmax) / max(-rd.y, 0.001) * 0.9;
    step = max(step, 0.05);
  } else {
    step = max(0.05, d * 0.5);
  }
  tt += step;
  if(tt > tmax) break;
}
```
But as shown, this still leaves the near-surface shallow case slow. Let's add a fallback: if tt > 60 and d < 0.6, use a step of 1.0 (accepting inaccuracy in the far field):

```
step = max(step, min(1.5, d*... ))
```
Ugh.

You know what — simpler idea: make the near-horizon rays just not hit the water at all. I.e., limit tmax to a modest value like 250 AND make the fog fully opaque by then, so the ray "misses" and shows sky (which matches the fog color). The transition is invisible if the fog color at max distance equals the sky color at the horizon.

So: fog = 1 - exp(-dist*k) and we want fog(250) ≈ 0.98 → k = 0.0156. At 50 units: 1-exp(-0.78) = 0.54. Half the water at 50 units is fog. Hmm, that's a lot but for a misty storm it might be OK.

Alternatively, don't use exponential fog; use a fog that stays low until far distances then ramps: fog = smoothstep(30, 250, dist)^1.5 or something. E.g. `fog = 1.0 - exp(-pow(dist*0.006, 2.0))` → at 50: 1-exp(-0.09) = 0.086; at 150: 1-exp(-0.81)=0.55; at 250: 1-exp(-2.25)=0.89; at 320: 1-exp(-3.7)=0.975. That's better! A quadratic falloff keeps the near field clear.

Let's use `fogAmt = 1.0 - exp(-pow(max(dist-15.0,0.0)*0.0065, 2.0))`. At dist=50: (35*0.0065)^2 = 0.0517 → 0.05. At 100: (85*0.0065)^2=0.305 → 0.26. At 200: (185*0.0065)^2=1.446 → 0.76. At 300: (285*.0065)^2=3.43 → 0.967. At 340: 4.4 → 0.988. 

So with tmax = 340, the far edge is 99% fogged. The sky at the horizon must match. 

Now, stepping: with tmax=340, near-horizon rays need to march far. But with the cone-bound stepping, they'll get there fast (jumping huge amounts), and then they either hit or reach tmax. With the cone bound, after reaching the Hmax level, the steps become small... but tmax will be reached in maybe 20 more steps of ~1 unit? No, from tt=150 to 340 with steps of ~1 = 190 steps.

Hmm.

OK, alternative for the near-surface shallow case: since the terrain is bounded by [-Hmax, Hmax] and the ray is above -Hmax... we can't bound better without knowing the slope.

Let me just use a minimum step that grows with tt in the far field, accepting inaccuracy:
```
step = max(step, min(tt * 0.06, d * 0.9));
```
At tt=150, d=0.4: min(9, 0.36) = 0.36 vs d*0.5 = 0.2 → step 0.36. Still limited by d*0.9. So linear-ish.

The d*0.9 cap is the problem. But if d is 0.4 and the terrain amplitude is 1.0, jumping 0.36 could overshoot a crest of height 0.4... but crests that high are rare. Let's allow d*f with f up to 3 in the far field: step = max(step, min(tt*0.06, d*3.0)) for tt > 40. At tt=150, d=0.4: min(9, 1.2) = 1.2. That could overshoot the surface. But at that distance, does it matter? The error would be a slightly wrong hit distance for near-horizon rays, which are heavily fogged. And these rays are within ~10 pixels of the horizon. I think it's acceptable.

Actually, hmm, wait. If the step overshoots and lands below the surface (d<0), we detect a hit at the wrong place. If it lands above, we continue. Either way the error is bounded by the step size, and the visual impact at 150+ units with 60% fog is minimal.

OK, let's go with:
```
float step = max(0.05, d * 0.5);
if(tt > 30.0) step = max(step, min(tt * 0.05, d * 3.0));
```
And rely on tmax = 340 and heavy far fog.

Let's estimate the iteration count for rd.y = -0.01:
- Steps of max(0.5*d, 0.05*tt capped by 3d).
- tt=0.25, d=2.45: step = max(1.2, min(0.0125, 7.35)=0.0125) = 1.2
- tt grows by ~1.2 each until 0.05*tt exceeds 1.2 → tt > 24. So ~20 steps to reach tt=24, d ≈ 2.2.
- Then step = max(1.1, min(0.05tt, 6.6)). At tt=24: min(1.2, 6.6)=1.2 vs 1.1 → 1.2. tt=25.2 → 0.05*25.2=1.26. So it grows slowly: 5% per step. From 24 to 340: ln(14)/0.05 = 53 steps.
Total ~73 steps. 

For a steep ray (rd.y = -0.5): hits at tt≈5. Steps: d*0.5, so ~5-8 steps. Good.

For rd.y = -0.05: hits at ~49 (mean level). d*0.5 stepping: d = 2.45-0.05tt. Steps: 1.2, then d=1.5 step 0.75, ... converges. Around 15-20 steps. Fine.

Good. Max 96 iterations, typically 20-75. Let's set the loop to 100 iterations.

Hmm, one concern: the `min(tt*0.05, d*3.0)` when tt > 30 — for a ray that's about to hit (d small), the step is 3d which overshoots. But we refine with binary search between prevT and hitT, so the hit position is refined. But if we overshoot the crest entirely (jump over it), we miss it. With 3d clearance, jumping over a crest that's 3d tall... the terrain varies by up to ~2 units over the step. Possible but rare, and it's in the far field. OK.

Actually let's make the far-field acceleration only apply when d is large-ish, say d > 0.25, else use d*0.5:
```
if(tt > 30.0 && d > 0.25) step = max(step, min(tt*0.05, d*3.0));
```
Then near the surface it stays safe. But then shallow rays that get close to the surface will slow down again... At tt=150 with d=0.4: d>0.25 so the acceleration applies. Only when d<0.25 does it stop, and then the step is 0.125, and the ray would be near the surface... Hmm, that gives ~10 extra steps. Fine, keep it simple without the d condition but with d*3.

I'll go with `if(tt > 30.0) step = max(step, min(tt*0.05, d*3.0));`.

Hmm, actually there's a risk: with d*3.0, if we're at d=2.2 and tt=25, step = min(1.25, 6.6) = 1.25 — fine. No risk there since the min with tt*0.05 caps it.

Alright.

Now let's also double check: `prevT` for the binary search — we set prevT = tt before advancing. Good.

Let me now also reconsider the oceanH cost. Each call = 4 fbm = 16 noise2. The march uses 1 per step (say 50 avg) + 4 for the normal + 6*1 for the binary search = 60 per pixel. 60*16 = 960 noise2 calls per pixel. At 700k pixels = 672M noise2/frame. Each noise2 ~ 4 hashes (each ~10 ops) + 6 mixes ≈ 50 ops → 33 GOPs/frame. Way too slow!

Hmm. That's a problem. 33 GFLOP per frame at 60fps = 2 TFLOPS. Modern GPUs can do that but it's heavy. Integrated won't.

Need to reduce. Options:
1. Reduce pixel count: 700k → 350k (0.5 scale). Halves it.
2. Reduce fbm octaves from 4 to 3 → 12 per oceanH.
3. Reduce march steps.

Let's do fbm with 3 octaves and 3 wave layers → 9 noise2 per oceanH. Hmm, we need 4 wave layers for the rolling look... 3 might be enough if the fbm has 3-4 octaves.

Let's do: fbm with 3 octaves (freqs 1, 2.03, 4.12), and 4 wave layers. Then 12 noise2 per oceanH.

Actually, let's reconsider: noise2 with 4 hash calls. Each hash21 is ~6 ops. So noise2 ≈ 4*6 + 6 = 30 ops. 12 noise2 = 360 ops per oceanH. Times 60 march steps = 21600 ops per pixel. Times 400k pixels = 8.6 GOPs/frame. At 60 fps = 520 GFLOPS. That's feasible on a mid-range GPU (which does 1-5 TFLOPS). On integrated (~500 GFLOPS), it'd be 1 fps... hmm, no, integrated GPUs like Intel Iris do ~500 GFLOPS-1 TFLOPS. So ~30-60 fps. OK-ish.

Let's target ~400k pixels: for a 1920x1080 window (2M px), scale = sqrt(400000/2073600) = 0.44. That's quite blurry. Hmm.

Let's do 700k: scale 0.58. 1400x790 internal.

Hmm, let's compromise at ~600k and optimize the noise.

Actually, I can reduce the march steps by using a lower tmax... The march cost dominates. Let's reduce tmax to 250 and increase fog slightly. Then the far region is reached in fewer steps.

With tmax = 250: near-horizon rays take ~65 steps. Fine.

Hmm, also, most pixels are in the lower half of the screen (water) and they're steep rays with few steps. The near-horizon band is thin. So the average step count is maybe 25. Let's assume 30 avg.

30 steps * 360 ops = 10800 ops/pixel for the march, plus normal 4*360 = 1440, plus sky ~2 fbm*3 octaves*30 = fine, plus foam.

Total ~15000 ops/pixel. At 600k px = 9 GOPs/frame → 540 GFLOPS at 60fps. OK.

Let's go with a pixel budget of ~600k and adaptive: if the device is slow we can't know. Just fix it.

Actually, let's simplify: use `Math.min(window.devicePixelRatio, 1)` and a render scale of 0.6 fixed? For a 1920x1080 window: 1152x648 = 746k. Acceptable.

Hmm, let's do scale based on area: `scale = Math.min(1, Math.sqrt(650000/(w*h)))`, and multiply by min(dpr,1). Then for 1920x1080 with dpr 1: sqrt(650000/2073600) = 0.56. Internal 1075x605.

Let's just do it.

Now, let me finalize the fbm with 3 octaves:

```glsl
float fbm(vec2 p){
  float s = 0.0;
  float a = 0.5;
  for(int i = 0; i < 3; i++){
    s += a * noise2(p);
    p = ROT * p * 2.07;
    a *= 0.5;
  }
  return s; // 0..0.875
}
```

Ocean:
```glsl
float oceanH(vec2 p, float t){
  vec2 q = p * 0.20;
  float h = 0.0;
  h += fbm(q * 1.00 + vec2( t * 0.32,  t * 0.12)) * 1.00;
  h += fbm(q * 2.13 + vec2(-t * 0.55,  t * 0.30)) * 0.55;
  h += fbm(q * 4.31 + vec2( t * 0.90, -t * 0.66)) * 0.28;
  h += fbm(q * 8.77 + vec2(-t * 1.45,  t * 1.10)) * 0.13;
  return (h - 0.82) * 1.9;
}
```
fbm mean ≈ 0.4375, so the weighted sum mean ≈ 0.4375*1.96 = 0.857. Range [0, 0.875*1.96=1.715]. Subtract 0.82 → mean 0.037, range [-0.82, 0.895]. Times 1.9 → mean ~0.07, range [-1.56, 1.7]. Hmm, too tall. Camera at 2.45 would sometimes be inside waves. But the extremes are rare (they require all octaves to align).

Typical deviation: the fbm's std dev... The sum of 3 octaves each uniform-ish. Let's just say the typical range is ±0.3 in the pre-scale value → ±0.57 after scaling by 1.9. That's decent waves.

Let's use scale 1.6: range ±0.48 typical, extremes ±1.3. Camera at 2.45. OK. Let's go with 1.7.

Hmm, let me set the camera height to 2.8 to be safe, and the wave scale to 1.7. Then crests at ~1.3 max, camera at 2.8. Good.

Actually for a "boat" feel, being close to the water is better. 2.8 is fine.

Let me now reconsider the base wavelength: q = p*0.20, layer freq 1.0 → p*0.20, so the noise features are ~1/0.2 = 5 units. With 3 octaves, the finest is 4.29× → features of 1.16 units. That's good for choppy detail.

The highest layer: q*8.77 → p*1.75, finest octave 4.29× → 0.117 units wavelength. Amplitude 0.13*1.7 = 0.22. Hmm, that's a 0.22-amplitude wave with a 0.12-wavelength → slope of ~3.5. Very choppy, will alias. Let's reduce the highest layer to 0.10 and lower the frequency to 6.5.

Let me set layers: 1.00, 2.11, 4.13, 7.7 with weights 1.0, 0.55, 0.28, 0.13.
Highest: p*0.2*7.7 = p*1.54, finest octave 4.29 → 0.15 wavelength, amplitude 0.13*1.7 = 0.22. Slope 0.22/0.075 — still steep. But the actual octave amplitude in the fbm is 0.125 (the third octave), so the contribution to h from that octave is 0.13*0.125 = 0.016 pre-scale, ×1.7 = 0.028 amplitude at 0.15 wavelength → slope 0.37. That's fine! I confused myself.

OK good. The total amplitude is what matters. Let's move on.

Foam threshold: the surface height (in world units) after scaling: mean ~0.06, std maybe 0.3. Foam at pos.y > 0.35 or so.

Alright, let me write the final code.

Also I should double check `oceanNormal` epsilon: with features down to 0.15 wavelength, e=0.18 is fine (larger than the finest features, so they're smoothed). Use e = 0.15.

Now let's write everything out.

```glsl
#version 300 es
precision highp float;
out vec4 fragColor;

uniform vec2  iResolution;
uniform float iTime;

const float PI = 3.141592653589793;

// ---------- noise ----------
float hash21(vec2 p){
  p = fract(p * vec2(123.34, 456.21));
  p += dot(p, p + 45.32);
  return fract(p.x * p.y);
}

float noise2(vec2 x){
  vec2 i = floor(x);
  vec2 f = fract(x);
  vec2 u = f * f * (3.0 - 2.0 * f);
  float a = hash21(i);
  float b = hash21(i + vec2(1.0, 0.0));
  float c = hash21(i + vec2(0.0, 1.0));
  float d = hash21(i + vec2(1.0, 1.0));
  return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

float fbm(vec2 p){
  float s = 0.0;
  float a = 0.5;
  for(int i = 0; i < 3; i++){
    s += a * noise2(p);
    p = mat2(0.80, 0.60, -0.60, 0.80) * p * 2.07;
    a *= 0.5;
  }
  return s;
}
```

Hmm, `mat2(...)*p*2.07` — operator precedence: mat2 * p * 2.07 is fine (left to right).

Ocean functions:

```glsl
float oceanH(vec2 p, float t){
  vec2 q = p * 0.20;
  float h = 0.0;
  h += fbm(q * 1.00 + vec2( t * 0.30,  t * 0.11)) * 1.00;
  h += fbm(q * 2.11 + vec2(-t * 0.52,  t * 0.28)) * 0.55;
  h += fbm(q * 4.13 + vec2( t * 0.86, -t * 0.61)) * 0.28;
  h += fbm(q * 7.70 + vec2(-t * 1.35,  t * 1.02)) * 0.13;
  return (h - 0.83) * 1.75;
}

vec3 oceanNormal(vec2 p, float t){
  float e = 0.16;
  float hL = oceanH(p - vec2(e, 0.0), t);
  float hR = oceanH(p + vec2(e, 0.0), t);
  float hD = oceanH(p - vec2(0.0, e), t);
  float hU = oceanH(p + vec2(0.0, e), t);
  return normalize(vec3(hL - hR, 2.0 * e, hD - hU));
}
```

Sky:

```glsl
vec3 skyColor(vec3 rd, vec3 sunDir, float t){
  float y = max(rd.y, 0.0);
  vec3 zenith  = vec3(0.030, 0.045, 0.098);
  vec3 horizon = vec3(0.235, 0.135, 0.145);
  vec3 col = mix(horizon, zenith, pow(y, 0.42));

  float sd = max(dot(rd, sunDir), 0.0);

  // clouds
  if(rd.y > 0.0015){
    vec2 uv = rd.xz / (rd.y + 0.13);
    uv = uv * 0.75 + vec2(t * 0.015, t * 0.006);
    float n1 = fbm(uv * 0.75);
    float n2 = fbm(uv * 1.95 + 17.0);
    float dens = smoothstep(0.34, 0.78, n1 * 0.95 + n2 * 0.5);
    dens *= smoothstep(0.0, 0.05, rd.y);
    float lit = pow(sd, 2.2);
    vec3 cDark = vec3(0.045, 0.052, 0.080);
    vec3 cLit  = vec3(0.72, 0.34, 0.19);
    vec3 cc = mix(cDark, cLit, lit * 0.9 + 0.05);
    cc += vec3(1.0, 0.55, 0.25) * pow(sd, 14.0) * 0.35;
    col = mix(col, cc, dens * 0.93);
  }

  // sun glow
  col += vec3(1.00, 0.42, 0.13) * pow(sd, 8.0)  * 0.75;
  col += vec3(1.00, 0.30, 0.07) * pow(sd, 2.0)  * 0.20;

  // sun disc
  float disc = smoothstep(0.99920, 0.99975, sd);
  col += vec3(1.0, 0.72, 0.38) * disc * 7.0;

  return col;
}
```

Wait: the sun disc smoothstep range - with sd = dot(rd, sunDir), the angular radius: 1-sd = 1-cos(θ) ≈ θ²/2. For a disc of radius 0.02 rad (1.1°), θ²/2 = 0.0002 → sd = 0.9998. So the disc from 0.9992 to 0.99975 corresponds to θ from 0.028 to 0.011 rad. That's a disc of radius 0.011 rad ≈ 0.63°. That's about the real sun's angular radius (0.27°)... slightly larger. Fine, gives a visible sun. With 800px over 0.67 rad, 0.011 rad = 13 pixels. Good size.

Hmm, but with hard-edged smoothstep it'll be a sharp disc with a soft edge. Fine.

One problem: `pow(sd, 8.0)*0.75` — near the sun, sd≈1, so the glow adds 0.75+0.2 = 0.95 plus the disc 7. That's very bright. Good.

Also the sky near the horizon away from the sun: horizon color (0.235, 0.135, 0.145) — a dusky purple-brown. Nice.

Now the main.

```glsl
void main(){
  vec2 uv = (gl_FragCoord.xy - 0.5 * iResolution) / iResolution.y;
  float t = iTime;

  // ---- camera on a bobbing boat ----
  vec3 ro = vec3(sin(t * 0.53) * 0.35,
                 2.80 + sin(t * 1.13) * 0.16 + sin(t * 2.37) * 0.055,
                 cos(t * 0.41) * 0.35);

  float pitch = -0.085 + sin(t * 0.83) * 0.026 + sin(t * 1.67) * 0.009;
  float roll  = sin(t * 0.71) * 0.035 + sin(t * 1.31) * 0.012;
  float yaw   = sin(t * 0.29) * 0.06;

  vec3 fwd   = normalize(vec3(sin(yaw) * cos(pitch), sin(pitch), -cos(yaw) * cos(pitch)));
  vec3 right = normalize(cross(fwd, vec3(0.0, 1.0, 0.0)));
  vec3 up    = cross(right, fwd);

  // apply roll
  vec3 r2 = right * cos(roll) + up * sin(roll);
  vec3 u2 = up * cos(roll) - right * sin(roll);

  vec3 rd = normalize(fwd * 1.55 + r2 * uv.x + u2 * uv.y);

  vec3 sunDir = normalize(vec3(0.44, 0.075, -1.0));

  vec3 col = skyColor(rd, sunDir, t);
  ...
}
```

Wait: cross(fwd, worldUp) when fwd is nearly -z gives right ≈ +x? cross((0,0,-1),(0,1,0)) = (0*0-(-1)*1, (-1)*0-0*0, 0*1-0*0) = (1, 0, 0). Yes.

Then up = cross(right, fwd) = cross((1,0,0),(0,0,-1)) = (0*(-1)-0*0, 0*0-1*(-1), 1*0-0*0) = (0,1,0). 

Now the ocean:

```glsl
  if(rd.y < 0.0){
    float tmax = 260.0;
    float tt = 0.20;
    float prevT = tt;
    float hitT = -1.0;

    for(int i = 0; i < 100; i++){
      vec3 p = ro + rd * tt;
      float h = oceanH(p.xz, t);
      float d = p.y - h;
      if(d < 0.0){ hitT = tt; break; }
      prevT = tt;
      float step = max(0.05, d * 0.5);
      if(tt > 30.0) step = max(step, min(tt * 0.05, d * 3.0));
      tt += step;
      if(tt > tmax) break;
    }
```

Hmm, careful: if the ray is going up (rd.y>0) we don't enter. If rd.y < 0 but close to 0, the loop breaks at tmax.

Then:

```glsl
    if(hitT > 0.0){
      float a = prevT, b = hitT;
      for(int i = 0; i < 6; i++){
        float m = 0.5 * (a + b);
        vec3 pm = ro + rd * m;
        if(pm.y - oceanH(pm.xz, t) > 0.0) a = m; else b = m;
      }
      float dist = 0.5 * (a + b);
      vec3 pos = ro + rd * dist;
      vec3 n = oceanNormal(pos.xz, t);
      ...
    }
```

Shading as described.

Now, `if(rd.y < 0.0)` — but the water surface can be above the camera? No, crests max ~1.3 < 2.8. OK.

But wait: what about rays with rd.y slightly positive that graze a far crest? Not possible since crests are below the camera.

Foam: let me write it.

```glsl
      vec3 viewDir = -rd;
      float fres = 0.02 + 0.98 * pow(1.0 - max(dot(viewDir, n), 0.0), 5.0);

      vec3 refl = reflect(rd, n);
      refl.y = max(refl.y, 0.001);
      vec3 skyRefl = skyColor(normalize(refl), sunDir, t);

      float ph = pos.y;
      vec3 deep  = vec3(0.006, 0.018, 0.030);
      vec3 crest = vec3(0.035, 0.075, 0.095);
      vec3 body  = mix(deep, crest, smoothstep(-0.6, 1.1, ph));

      // translucency in the wave faces
      float sss = pow(max(dot(n, sunDir), 0.0), 2.5) * smoothstep(-0.3, 0.9, ph);
      body += vec3(0.40, 0.15, 0.035) * sss * 0.8;

      vec3 water = mix(body, skyRefl, fres);

      vec3 hv = normalize(sunDir + viewDir);
      float sp = max(dot(n, hv), 0.0);
      float spec = pow(sp, 700.0) * 6.0 + pow(sp, 80.0) * 0.35;
      water += vec3(1.0, 0.55, 0.24) * spec;

      // foam
      float steep = 1.0 - n.y;
      float fh = smoothstep(0.20, 0.95, ph);
      float fs = smoothstep(0.05, 0.28, steep);
      float fn = fbm(pos.xz * 1.4 + vec2(t * 0.22, -t * 0.17));
      float foam = fh * (0.30 + 1.0 * fs) * (0.45 + 1.3 * fn);
      foam = smoothstep(0.45, 1.0, foam);
      vec3 foamCol = vec3(0.66, 0.67, 0.70) * (0.30 + 0.70 * clamp(dot(n, sunDir) * 3.0 + 0.35, 0.0, 1.0));
      foamCol += vec3(1.0, 0.5, 0.2) * spec * 0.6;
      water = mix(water, foamCol, foam);

      // fog
      float fogAmt = 1.0 - exp(-pow(max(dist - 12.0, 0.0) * 0.0075, 2.0));
      vec3 fogCol = skyColor(normalize(vec3(rd.x, 0.035, rd.z)), sunDir, t);
      water = mix(water, fogCol, clamp(fogAmt, 0.0, 1.0));
      col = water;
```

Fog check: dist=50 → (38*0.0075)^2 = 0.081 → 0.078. dist=100 → (0.66)^2=0.436 → 0.35. dist=200 → (1.41)^2=1.99 → 0.86. dist=260 → (1.86)^2=3.46 → 0.97. Good — at tmax the ocean is 97% fogged, matching the sky.

`clamp(dot(n, sunDir)*3.0 + 0.35, ...)`: dot(n,sunDir) for a mostly-up normal and a low sun ≈ 0.07 → 0.21+0.35 = 0.56. So foam brightness 0.66*(0.3+0.7*0.56) = 0.66*0.69 = 0.46. Reasonable grey foam. For faces tilted toward the sun it gets brighter.

Then outside the if: `col = ...`.

Also, one more: should I add a slight gamma / tone map? The sky glow values can exceed 1. Let's do a soft tonemap: `col = col / (1.0 + col)` would darken too much. Use `col = 1.0 - exp(-col * 1.2)` and then pow(col, 1/2.2)? Hmm, but I've been picking colors assuming linear output... Actually for a nice look, let's do:

```
col = max(col, 0.0);
col = col / (1.0 + col * 0.35);   // soft rolloff
col = pow(col, vec3(0.4545));
```
Gamma correction will brighten everything a lot. The sky horizon color 0.235 → pow(0.235,0.4545) = 0.52. That's a mid-grey. Hmm, that's fine actually.

But the water deep color 0.006 → 0.09. OK.

Let's think: with gamma, everything gets brighter. The horizon at 0.52, the zenith at pow(0.098, 0.4545) = 0.35. That's a fairly bright sky, not dramatic. Hmm. Maybe I should darken the base colors then. Since I'm designing by feel, let me just apply the tonemap + gamma and adjust the palette.

Alternatively, skip gamma and just apply a soft tonemap. Then the colors are as authored (which I've tuned to look reasonable in linear-ish terms... but I haven't actually tested).

Hmm, I need to make a judgment call. Let me include a mild tonemap and a gamma of 1/1.8 (a partial correction) — no, that's hacky.

Let me just go with: tonemap `col = col/(1+col)` won't work well.

Decision: apply `col = pow(clamp(col,0,1), vec3(0.85))` — a mild contrast lift. Hmm.

Actually you know what, let's do proper gamma 2.2 with colors designed for it. Let me re-derive:

Sky zenith in linear: I want the final displayed value ~0.10 (dark blue). pow(x, 1/2.2) = 0.10 → x = 0.1^2.2 = 0.0063. So zenith linear = (0.005, 0.007, 0.016) approximately (with a slight blue bias).

Horizon: I want displayed ~0.35 reddish-grey. x = 0.35^2.2 = 0.10. So horizon = (0.10, 0.055, 0.055)? That would display as (0.35, 0.27, 0.27) — hmm, that's a warm grey.

Hmm, this is getting complicated. Let me think about it differently: I'll write the shader without gamma correction (output directly), designing the colors as they appear. This is common in shadertoy-ish code and I can reason about the final appearance directly. Since we're not doing physical light transport, that's fine.

So: remove the gamma. Just clamp. Maybe apply a very soft tonemap to keep the sun from being a flat white blob: `col = col - 0.02*col*col`? Eh, just clamp.

Actually, the sun disc at 7.0 will clamp to white in a small area, which is fine (the sun should be blown out). But the surrounding glow at 0.75+ will also blow out to white-ish (1.0, 0.42*0.75... wait, the glow adds vec3(1,0.42,0.13)*0.75 = (0.75, 0.31, 0.098) on top of the horizon (0.235,0.135,0.145) = (0.985, 0.445, 0.24). Not clamped. Good, orange.

OK, no gamma. Simple clamp at the end. Actually, let me apply a very gentle `col = col / (1.0 + 0.15*col)` — no, skip it. Just clamp.

Hmm, but with no tonemapping, the water and sky will look flat-ish? No, it'll be fine.

Let's finalize.

One more: I should double-check the `disc` in the water reflection. The reflected ray from a wave facet could align exactly with the sun, creating a tiny bright dot. That's fine.

Let's now write the JS.

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Stormy Ocean at Sunset</title>
<style>
  html, body { margin:0; padding:0; width:100%; height:100%; overflow:hidden; background:#000; }
  #glcanvas { display:block; width:100vw; height:100vh; }
</style>
</head>
<body>
<canvas id="glcanvas"></canvas>
<script>
(function(){
  "use strict";
  const canvas = document.getElementById('glcanvas');
  const gl = canvas.getContext('webgl2', { antialias: false, alpha: false, depth: false, stencil: false, powerPreference: 'high-performance' });
  if(!gl){
    document.body.innerHTML = '<p style="color:#fff;font-family:sans-serif;padding:1em">WebGL2 is not available in this browser.</p>';
    return;
  }
  ...
})();
</script>
</body>
</html>
```

Shaders as template literals.

Compile helper:

```js
function createShader(type, src){
  const s = gl.createShader(type);
  gl.shaderSource(s, src);
  gl.compileShader(s);
  if(!gl.getShaderParameter(s, gl.COMPILE_STATUS)){
    console.error(gl.getShaderInfoLog(s), src);
    throw new Error('shader compile error');
  }
  return s;
}
```

Program linking.

Then set up the VAO.

Resize:
```js
let renderScale = 1;
function resize(){
  const dpr = Math.min(window.devicePixelRatio || 1, 1);
  const w = window.innerWidth, h = window.innerHeight;
  const budget = 620000;
  let s = Math.min(1, Math.sqrt(budget / Math.max(1, w*h*dpr*dpr)));
  s = Math.max(s, 0.35);
  canvas.width = Math.max(1, Math.round(w * dpr * s));
  canvas.height = Math.max(1, Math.round(h * dpr * s));
  canvas.style.width = w + 'px';
  canvas.style.height = h + 'px';
  gl.viewport(0, 0, canvas.width, canvas.height);
}
window.addEventListener('resize', resize);
```

Wait, `canvas.style.width = '100vw'` in CSS already, but setting explicit px is fine too. Actually let's keep the CSS 100vw/100vh and not set inline styles. But then the canvas element's CSS size is the viewport, and the drawing buffer is smaller → the browser scales it. Good. I'll leave the CSS.

Hmm, but with `width:100vw` and `height:100vh` on the canvas and `display:block`, it should fill exactly.

Render loop:
```js
let startTime = 0;
function frame(now){
  if(!startTime) startTime = now;
  const t = (now - startTime) * 0.001;
  gl.uniform2f(uResLoc, canvas.width, canvas.height);
  gl.uniform1f(uTimeLoc, t);
  gl.drawArrays(gl.TRIANGLES, 0, 3);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
```

Note: iResolution should be the drawing buffer size since gl_FragCoord uses it. Yes.

Also handle context loss? Not needed.

Now, about "starts automatically" — yes, rAF starts immediately.

Let me also add a check: if the shader fails to compile, show an error.

Let me write the full fragment shader source now, carefully.

```glsl
#version 300 es
precision highp float;

out vec4 fragColor;

uniform vec2  iResolution;
uniform float iTime;

float hash21(vec2 p){
  p = fract(p * vec2(123.34, 456.21));
  p += dot(p, p + 45.32);
  return fract(p.x * p.y);
}

float noise2(vec2 x){
  vec2 i = floor(x);
  vec2 f = fract(x);
  vec2 u = f * f * (3.0 - 2.0 * f);
  float a = hash21(i);
  float b = hash21(i + vec2(1.0, 0.0));
  float c = hash21(i + vec2(0.0, 1.0));
  float d = hash21(i + vec2(1.0, 1.0));
  return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

float fbm(vec2 p){
  float s = 0.0;
  float a = 0.5;
  for(int i = 0; i < 3; i++){
    s += a * noise2(p);
    p = mat2(0.80, 0.60, -0.60, 0.80) * p * 2.07;
    a *= 0.5;
  }
  return s;
}

float oceanH(vec2 p, float t){
  vec2 q = p * 0.20;
  float h = 0.0;
  h += fbm(q * 1.00 + vec2( t * 0.30,  t * 0.11)) * 1.00;
  h += fbm(q * 2.11 + vec2(-t * 0.52,  t * 0.28)) * 0.55;
  h += fbm(q * 4.13 + vec2( t * 0.86, -t * 0.61)) * 0.28;
  h += fbm(q * 7.70 + vec2(-t * 1.35,  t * 1.02)) * 0.13;
  return (h - 0.83) * 1.75;
}

vec3 oceanNormal(vec2 p, float t){
  float e = 0.16;
  float hL = oceanH(p - vec2(e, 0.0), t);
  float hR = oceanH(p + vec2(e, 0.0), t);
  float hD = oceanH(p - vec2(0.0, e), t);
  float hU = oceanH(p + vec2(0.0, e), t);
  return normalize(vec3(hL - hR, 2.0 * e, hD - hU));
}

vec3 skyColor(vec3 rd, vec3 sunDir, float t){
  ...
}
```

Wait — `mat2(0.80, 0.60, -0.60, 0.80)` constructed inside the loop. Should be fine (compiler hoists). Or declare a const at global scope:
```glsl
const mat2 ROT = mat2(0.80, 0.60, -0.60, 0.80);
```
GLSL ES 3.0 supports const mat2 with a constructor. Yes.

Now, potential issue: in GLSL ES 3.00, `const` global with a non-constant initializer is disallowed, but a mat2 constructor with literals is a constant expression. Fine.

Let me write out the whole thing.

One concern about `pow(sd, 8.0)` with sd possibly 0 → pow(0, 8) = 0, fine. pow of negative is undefined — sd >= 0 since it's a max with 0. Good.

In skyColor, `pow(y, 0.42)` with y = max(rd.y, 0) — fine.

Let me finalize and write out the complete file.

Also: `dens *= smoothstep(0.0, 0.05, rd.y);` — at rd.y = 0.05, full density. OK.

Let me also double check the cloud uv: `rd.xz / (rd.y + 0.13)`. At rd.y = 0.5 (high in the sky), uv = rd.xz/0.63. |rd.xz| ≤ 0.866. So uv magnitude ≤ 1.37, times 0.75 = 1.03. Then fbm(uv*0.75) → max input ~0.77. So at high elevations we sample a tiny region of noise → giant clouds. Hmm, that's the projection of a cloud plane. At rd.y = 0.05: uv = rd.xz/0.18, magnitude up to 4.8, times 0.75 = 3.6, times 0.75 (fbm arg) = 2.7. So the clouds span a range of ~3 noise units from the zenith to the horizon. That's quite few features. Might look like a big blob. Let's increase: uv * 1.6 instead of 0.75, and the fbm args 1.0 and 2.6.

Then at rd.y=0.5: uv*1.6 max = 2.2, fbm arg max 2.2 → ~2 features. At the horizon: 7.7 → ~7 features. Reasonable.

Let me use uv = rd.xz/(rd.y+0.11) * 1.5, then n1 = fbm(uv*0.9), n2 = fbm(uv*2.2+17.0).

Hmm, dpr: with (rd.y+0.11), at rd.y=0.5 → 1.64 denominator. uv max = 0.866/1.64*1.5 = 0.79. fbm arg 0.71. So less than one noise cell at the zenith → a single smooth blob overhead. Meh. That's typical for cloud-plane projections. It's fine.

Actually, let's reduce the +0.11 to +0.06 so the clouds are denser near the horizon and the projection is more compressed. At rd.y=0.5 → 0.56 denominator → uv max 2.3 → fbm arg 2.07 → 2 features. Better.

But then at rd.y=0.0 the denominator is 0.06 → uv max = 14.4 → very compressed near the horizon. Good, clouds converge at the horizon.

Use +0.08 as a compromise.

OK. Writing the final code now.

One more thought on the ocean raymarch start: `tt = 0.20`. Since the camera is at y=2.8 and the max wave height is ~1.4, the ray can't hit before tt=0.2. Fine.

Also I should ensure `prevT` is correctly the last above-surface t. Yes.

Potential issue: if hitT is found on the very first iteration (tt=0.2), prevT = 0.2 as well (initialized before the loop). Then the binary search between 0.2 and 0.2 gives 0.2. Fine.

Let me write out the final HTML.

Also for robustness, add `gl.getExtension('WEBGL_lose_context')`? No.

Final check on the shader loop: `for(int i = 0; i < 100; i++)` with a break — fine in GLSL ES 3.0.

Writing it all out now.

Actually, one more consideration on the camera: the bobbing `ro.x = sin(t*0.53)*0.35` moves the camera laterally. Since the water is a static function of world position (with time evolution), moving the camera laterally makes the waves appear to move relative to the camera. Good.

But there's a subtlety: the water surface evolves with time in a way that isn't purely advective, so it looks like moving water. Good.

Let me write it.

Also, `rd.y < 0.0` gate — but with camera roll, rd for the top of the screen is well above 0. Fine.

Let me write the final answer.

Oh wait, one issue: for pixels where rd.y >= 0 we skip the ocean entirely, so the bottom edge... no, rd.y >= 0 means sky. Correct.

But there's a discontinuity at the horizon: just below it we have the heavily fogged ocean, just above we have the sky. The fog color = skyColor(horizon-ish direction) which matches skyColor(rd) at rd.y ≈ 0.035 vs 0. Should be close. Good.

Final code writing.

Let me reconsider the foam smoothstep thresholds once more. 
- ph = pos.y ranges roughly [-0.8, 1.3] typically, mean 0.06.
- fh = smoothstep(0.20, 0.95, ph): nonzero when ph > 0.2. That's maybe 30% of the surface.
- steep = 1-n.y, ranges 0 to ~0.5. fs = smoothstep(0.05, 0.28, steep).
- fn = fbm(...) ranges 0..0.875, mean 0.44.
- foam = fh * (0.3 + fs) * (0.45 + 1.3*fn): at fh=1, fs=0.5, fn=0.44 → 1 * 0.8 * 1.02 = 0.82. smoothstep(0.45,1.0,0.82) = smoothstep → (0.82-0.45)/0.55 = 0.67 → 0.67²(3-2*0.67)= 0.45*1.66 = 0.74. So foam = 0.74 where the wave is high and steep. Reasonable. Where fn is low (0.1): 1*0.8*(0.58) = 0.46 → smoothstep → ~0.005. So the noise breaks it up well. 

Now writing.

For the specular: `pow(sp, 700.0)` — with highp this is fine. `sp` is the dot with the half vector. Sun near horizon, view near horizon → the half vector is near the horizon direction, so dot(n, hv) is small for upward normals... Let's compute: sunDir ≈ (0.4, 0.07, -0.91). viewDir ≈ (0,0,1) for a ray going into the screen (rd = (0,0,-1), viewDir = -rd = (0,0,1)). hv = normalize((0.4, 0.07, 0.09)) ≈ (0.96, 0.17, 0.22). dot with n=(0,1,0) → 0.17. pow(0.17, 700) ≈ 0. So no specular on flat water. Only on facets tilted toward the half vector. On a wave facet tilted toward the sun, n could be like (0.5, 0.85, -0.15) → dot = 0.48+0.14-0.03 = 0.59 → pow(0.59,700) = 0. Hmm, very tight. pow(0.9,700) = e^(700*ln0.9) = e^-73.7 ≈ 0. So the specular only appears when sp > 0.99. That's the glitter path — very sparse sparkles. That's actually realistic for a sun glitter path, but with our smooth normals it might be too sparse/invisible.

Let's loosen: pow(sp, 120.0)*3.0 + pow(sp, 12.0)*0.15. pow(0.9,120) = e^-12.6 = 3.4e-6. Still tiny. pow(0.95,120)= e^-6.15=0.002. So the highlight needs sp > 0.97.

Hmm, the issue is that the wave normals rarely point exactly at the half vector. With a max slope of ~0.5 (n.y ≈ 0.9), sp max ≈ 0.9*0.17 + 0.43*0.6 ≈ 0.15+0.26 = 0.41. pow(0.41, 12) = 1e-5. So basically no specular at all!

The problem: the sun is low (elevation 4°) and the view is nearly horizontal, so the half vector is nearly horizontal, and the water normal is nearly vertical. The angle between them is ~80°. Real sun glitter on water works because ripples tilt the normals by up to 30-40°.

So I need steeper normals, or a much broader specular. Options:
- Increase the wave slopes (more high-frequency amplitude).
- Use a broader specular lobe: pow(sp, 6.0) * 0.4. pow(0.41, 6) = 0.0047. Still small.

Hmm. Actually, the "sun glitter path" in reality comes from the reflection of the sun (which is at a low elevation) off wave facets tilted toward the camera. The reflection direction from a facet must point at the sun. For a low sun and a low camera, the facet normal must be nearly vertical tilted... Let's think: the ray from the camera going down to the water, reflecting up toward the sun. If the sun is at 4° elevation and the camera is at 3° above the water looking down at -1°, the reflected ray must go up at 4°. The normal bisects the incident (-1° down) and the reflected (4° up)... 

Actually the half vector between the view direction and the sun direction. The view direction to the surface point is downward at some angle. For a point at distance d on the water, the view direction is about atan(2.8/d) below horizontal. At d=30, that's 5.3° below horizontal. The sun is 4° above. The half vector is at (−5.3+4)/2 = −0.65° ≈ horizontal. And the water normal must be along the half vector... no wait.

For specular reflection: the normal must be the half vector between the light direction (to the sun) and the view direction (to the camera). Light direction = sunDir = 4° up. View direction = from surface to camera = 5.3° up. Half vector = 4.65° up, i.e., nearly horizontal. So the water normal must be nearly horizontal! That's nonsense — the water surface normal is nearly vertical.

Hmm, I have it backwards. Let me redo. 

For a flat mirror (normal = up), the incident ray from the camera going down at 5.3° reflects to go up at 5.3°. The sun is at 4° up. So the reflected ray direction (5.3° up) is close to the sun direction (4° up) — meaning yes! A flat water surface reflects the sky at 5.3° elevation, which is right where the low sun is. So the sun glitter appears.

So in terms of the half-vector: H = normalize(V + L) where V = direction from surface to camera = (0, sin5.3°, ...) ≈ 5.3° up, L = sunDir ≈ 4° up. H ≈ 4.65° up, nearly horizontal. And dot(N, H) with N = (0,1,0) → sin(4.65°) = 0.081. pow(0.081, 700) ≈ 0. 

The issue: my specular formula uses the half vector but with H being nearly horizontal, the dot with a vertical normal is tiny. That's correct physically — the specular reflection of a low sun off flat water IS dim in the "microfacet" model because the flat surface reflects the ray at the mirror angle but the specular lobe... 

Hmm no. The mirror reflection is exactly captured by H = normalize(V+L) and the normal must equal H. For a flat surface with N = up, and V at 5.3° up, L at 4° up — H should be at 4.65° up, and N=up is 90° away from H. Contradiction!

Let me recompute. V = from surface to camera. If the camera is 2.8 units above and 30 units away, V = (0, 2.8, 30)/30.13 ≈ (0, 0.093, 0.996) → 5.3° up. Good.
L = sunDir = (0, 0.07, 0.997) → 4° up. 
H = normalize(V+L) = normalize((0, 0.163, 1.993)) = (0, 0.0815, 0.9967) → 4.7° up. Correct.
N = (0,1,0) = 90° up.
dot(N,H) = 0.0815.
Angle between N and H = 85.3°.

But the mirror reflection of V about N: reflect(-V, N) where -V is the incident direction (from camera to surface) = (0, -0.093, -0.996). reflect = incident - 2*dot(incident,N)*N = (0,-0.093,-0.996) - 2*(-0.093)*(0,1,0) = (0, 0.093, -0.996). So the reflected direction goes back toward the camera... wait, that's pointing up and toward the camera (-z direction is toward the camera if the camera is at +z? Let me set up: the camera at (0, 2.8, 30), looking at the origin. The surface point at the origin. V = (camera - surface)/|..| = (0, 0.093, 0.996) (pointing up and +z toward the camera).

Incident ray from camera to surface: I = -V = (0, -0.093, -0.996). Reflect about N=(0,1,0): R = I - 2(I·N)N = (0,-0.093,-0.996) + 0.186*(0,1,0) = (0, 0.093, -0.996). So the reflected ray goes up and in the -z direction, i.e., away from the camera toward the horizon on the other side... 

Hmm, but the sun is in the -z direction from the surface point (sunDir = (0, 0.07, -0.997) means the sun is toward -z). Yes! R = (0, 0.093, -0.996) ≈ sunDir. 

So dot(N, H) = 0.0815 but the reflection is nearly perfect. That's because H is the half vector and N should equal H for a perfect mirror, but here N=(0,1,0) and H=(0,0.0815,0.9967). They're 85° apart!? But the reflection works...

Ah, I see my error. H = normalize(V + L) where V is the direction TO the viewer and L is the direction TO the light. Then for a perfect mirror, N = H. Let me check: V = (0, 0.093, 0.996), L = (0, 0.07, -0.997). I mixed up the sign of L! sunDir points from the surface toward the sun = (0, 0.07, -0.997). So L = (0, 0.07, -0.997).

H = normalize(V + L) = normalize((0, 0.163, -0.001)) = (0, 1.0, -0.006). ≈ N! 

So I need to be careful: in my shader, `viewDir = -rd` where rd is the ray direction from the camera into the scene. At the surface, rd points from the camera toward the surface, continuing away. So the direction from the surface to the camera is -rd. Yes, viewDir = -rd is correct.

And my code has `vec3 hv = normalize(sunDir + viewDir);` — that's L + V. Correct!

I made an arithmetic error above by using +z for the sun. OK good. So the specular does work with nearly-vertical normals when the geometry aligns. Let me redo the estimate: with the camera at (0,0,0)ish and the surface at distance d in the -z direction, V = -rd ≈ (0, small, +1) pointing up and back toward the camera. sunDir = (0.4, 0.07, -0.91) normalized... wait, the sun is at +x and -z, so the sun is off to the right and forward. The reflection off flat water for a ray going in the -z direction would go back to +z... 

Hold on. If the camera is at the origin looking in the -z direction, and the sun is at direction (0.4, 0.07, -0.91) — that's in the -z direction, i.e., in front of the camera. Rays from the camera going down and forward (-z) hit the water and reflect. reflect(rd, N) with rd = (0, -0.1, -0.995) and N = (0,1,0) gives (0, 0.1, -0.995). So the reflected ray goes up and forward, matching the sun direction (0.4, 0.07, -0.91) if the x-components match. But the reflected ray has x=0. So flat water reflects straight ahead, and the sun is to the right. The glitter path would be where the water tilts to the left... Actually the glitter path on the water lies along the line between the camera and the point below the sun. Rays going toward that point have x>0. rd = (0.4, -0.1, -0.91) normalized. The reflection off flat water: (0.4, 0.1, -0.91) — which is close to the sun direction (0.4, 0.07, -0.91)! Great. So flat water directly reflects the sun along the whole glitter path.

So dot(N,H) with N=(0,1,0): H = normalize(V + L) where V = -rd = (-0.4, 0.1, 0.91) and L = (0.4, 0.07, -0.91). Sum = (0, 0.17, 0) → normalize = (0,1,0). dot with N = 1! 

So the specular works. My earlier confusion was about the sign of L. Good.

So with pow(sp, 700) it'll be a very tight sun glitter, and pow(sp, 80)*0.35 gives a broader sheen. With wave slopes perturbing the normal, sp varies. Good.

Let me use pow(sp, 900.0)*8.0 + pow(sp, 60.0)*0.3. Actually, for a nice broad glitter path, a moderately tight lobe is good. Let's use pow(sp, 300.0)*4.0 + pow(sp, 30.0)*0.25.

OK, good.

Also, note the sky's sun glow reflection in the water: skyRefl includes the sun glow, which multiplied by fresnel gives a bright streak. Combined with the specular, it should look great.

Now writing the final code for real.

One last thing: the `fres` term. `dot(viewDir, n)` where viewDir = -rd. For a downward-looking ray, viewDir points up, n points up, so the dot is positive. At grazing angles (rd nearly horizontal), viewDir·n → 0 → fres → 1. Good.

Also, the deep water body color should be modulated by the fresnel... yes, `mix(body, skyRefl, fres)`. Good.

Writing now.

Actually also: I want the water to look dark and stormy with the sky reflecting. Let's add a slight color to the reflection... no, keep it.

Final code:

Also need to handle the `if(rd.y < 0.0)` block properly with the `col` variable.

Let me write it.

Note on `uniform vec2 iResolution` — I'll use it.

Let me write out the complete file now.

Also I realize I should double-check the highest-frequency terms don't cause the normal to be super noisy. oceanNormal with e=0.16 evaluates oceanH at ±0.16. The highest frequency content has a wavelength of ~0.15 units, so it's undersampled → noisy normals in the distance. But those high frequencies have low amplitude (~0.03 world units) so the normal perturbation is ~0.03/0.32 = 0.09 slope. Small. Acceptable.

Alright. Writing.

For the JS, I'll be careful with template literal escaping — no backticks inside the shader.

Let me produce the final file.