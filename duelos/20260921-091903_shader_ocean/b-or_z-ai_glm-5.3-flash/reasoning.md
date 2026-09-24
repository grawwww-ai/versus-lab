The user wants a full-window WebGL2 raymarched ocean-at-sunset animation in a single self-contained HTML file. Let me plan this carefully — this is a technical piece where quality lives in the shader itself.

**Core architecture:**
- Raw WebGL2, full-screen triangle (better than quad — one triangle covering the viewport), single fragment shader doing all raymarching.
- Canvas fills window, resize handler updates canvas size + gl.viewport.
- `requestAnimationFrame` timestamp drives a `uTime` uniform.
- Everything inline: CSS, JS, GLSL.

**Scene plan (what appears in the first 30s):**
1. Large rolling waves — layered FBM noise (value noise with rotation matrix between octaves), domain-warped a bit. Gerstner-ish displacement combined with noise octaves for the big rollers.
2. Foam on crests — derived from wave height / steepness (e.g., height above threshold + noise breakup, plus a transient whitecap pattern based on the Jacobian-like measure or simply `smoothstep` on crest height modulated by noise).
3. Sky — gradient from deep orange near the sun to dark blue-grey/charcoal at zenith, with 2D FBM clouds (dark, dramatic, lit from below near sun with orange rim). Sun disc with glow.
4. Water shading — normal from central differences of the heightfield at the ray hit; fresnel (`pow(1 - dot(n, -rd), 5)` Schlick); sun reflection — perturbed reflection ray dot sun direction, raised to a power, plus a broad glitter path; sky reflection (cheap: sample the same sky function along reflected ray).
5. Fog near horizon — exponential distance fog blending water into horizon color, plus aerial perspective on sky.
6. Camera bob — position and slight roll/pitch from sum of slow sines (boat feel), a few cm-scale bob + gentle sway. Make the bobbing readable in the first seconds.

**Raymarching approach for ocean:**
Classic technique: heightmap function `map(p)` returning water height. Raymarch with a distance-ish stepping: since water is a heightfield, use the ray-height intersection trick: step along ray until `p.y < height(p.xz)`, with adaptive step sizes (bisection refine at the end for precision). Keep max distance ~ horizon (e.g., 400–800 units) with LOD: reduce octave count with distance for both speed and visual smoothing.

Height function:
```
float waveHeight(vec2 p, float t, int octaves) {
  // large rolling swell: a few big directional sine-ish/noise waves
  // + FBM detail
}
```
Better: FBM with a rotation matrix, plus a big "swell" component: e.g. `1.2*sin(dot(p, dir1)*0.06 + t*0.5)` etc. Actually noise-based rollers look better. I'll do:

```
float h = 0.0;
vec2 q = p;
// large swell: 2 octaves of very low frequency noise, moving
h += fbm stuff
```

A well-known nice ocean heightfield (from "Seascape" style but I'll write my own):

```
float seaOctave(vec2 uv, float choppy) {
  uv += noise(uv);
  vec2 wv = 1.0 - abs(sin(uv));
  vec2 swv = abs(cos(uv));
  wv = mix(wv, swv, wv);
  return pow(1.0 - pow(wv.x * wv.y, 0.65), choppy);
}
```
That's the Seascape approach — but I should write my own variant to avoid copying verbatim. I'll build a heightfield from value-noise-based ridged waves:

My plan:
- `hash(vec2)` → float.
- `noise(vec2)` → smooth interpolated value noise.
- `fbm(p)` with rotation per octave.

Height:
```
float oceanHeight(vec2 p, float t) {
  float t2 = t*...;
  // domain warp
  vec2 w = vec2(noise(p*0.05 + t*0.1), noise(p*0.05 - t*0.08));
  p += (w-0.5)*ampl;
  float h = 0.0, a = 1.0, f = 1.0;
  vec2 dir = normalize(vec2(1.0, 0.3));
  for octaves:
     float n = noise(p*f*0.? + dir*t*speed ...)
     ridged: 1-abs(2n-1)
     h += ...
}
```

Simpler and reliable: a sum of directional " Gerstner-like" waves via noise:

```
float wave(vec2 p, vec2 d, float freq, float speed, float t) {
  float x = dot(p, d)*freq + t*speed;
  float n = noise(vec2(x, ...))  // 1D-ish
}
```

I'll go with a layered approach that's known to look like rolling ocean:

```
float oceanHeight(vec2 p, float t, int detail) {
    float h = 0.0;
    // big swell (rolls): three directional components
    float amp = 3.2; float freq = 0.055; float sp = 1.0;
    vec2 d = normalize(vec2(0.8, 0.35));
    float phase = dot(p, d)*freq;
    h += (noise(vec2(phase + t*0.6, phase*0.5 - t*0.2)) - 0.5) * amp;  // hmm
```

Hmm, let me think about what actually looks good. Value-noise FBM over xz with time offset in the noise coordinates produces organic rolling waves. The key is:
- First octave: very low frequency (wavelength ~60–100 units), amplitude ~3–4 → big rollers.
- A couple of mid octaves with rotation.
- Sharp chop: use ridged/billow transform `abs` on higher octaves to get sharp crests.

And "choppiness": sharpen the sum with `h = h - pow(abs(h), something)`? Or apply `h += pow(1.0 - n, k)`... Let me use this design:

```
float noised(vec2 p) -> value noise with analytic derivatives? 
```
Analytic derivatives would give free normals — nice but adds complexity. I'll instead compute normals by finite differences of the height function with a few extra evaluations; standard and fine.

Let me write the height function:

```glsl
float hash12(vec2 p){
    vec3 p3 = fract(vec3(p.xyx) * 0.13);
    p3 += dot(p3, p3.yzx + 3.333);
    return fract((p3.x + p3.y) * p3.z);
}

float noise(vec2 p){
    vec2 i = floor(p), f = fract(p);
    vec2 u = f*f*(3.0-2.0*f);
    float a = hash12(i);
    float b = hash12(i+vec2(1,0));
    float c = hash12(i+vec2(0,1));
    float d = hash12(i+vec2(1,1));
    return mix(mix(a,b,u.x), mix(c,d,u.x), u.y);
}

const mat2 ROT = mat2(1.6, 1.2, -1.2, 1.6); // scale+rotate

float waveField(vec2 p, float t, int oct){
    float h = 0.0;
    float a = 1.0;
    float f = 0.16;         // base frequency -> wavelength ~ 6 units? 
```

Hmm, wavelength: noise cell = 1/f units. f=0.16 → cell of ~6 units. For big rolling waves I want the first octave wavelength ~ 25–40 units with amplitude ~2.5. Camera at y≈3.5, waves amplitude ~3 gives dramatic swell near camera.

Design:

```
float oceanHeight(vec2 p, float t, int oct) {
    p *= 0.06; // scale so base wavelength ~ 16 units
    float mov = t * 0.7;
    vec2 drift = vec2(1.0, 0.3) * mov; // waves travel
    float h = 0.0;
    float amp = 1.0;
    vec2 q = p + 0.35*vec2(noise(p + drift*0.3), noise(p.yx - drift*0.2)); // warp
    float f = 1.0;
    float a = 1.0;
    for (int i = 0; i < 5; i++) {
        if (i >= oct) break;
        float n = noise(q*f + drift*(f*0.4));
        // billow/ridge shape for crests
        n = 1.0 - abs(n*2.0 - 1.0);      // ridge: sharp crests
        h += n * a;
        q = ROT * q;
        f *= 2.0; a *= 0.5;
    }
    return h * ...;
}
```

Ridged noise sum with gain 0.5 gives h in [0, ~2]. Scale to get amplitude. But pure ridged noise looks like mountain ridges, not ocean. Real ocean: rounded valleys, sharper crests. Invert: `n = abs(n*2-1)` gives valleys sharp; smooth-then-sharp... The Seascape trick uses `1 - abs(sin)` combos. 

Let me shape: for each octave, take noise n∈[0,1], map to a wave profile: `w = 1.0 - abs(sin(...))`? That needs phase-coherent sin. Alternative shaping that works well: 

```
float ph = noise(q*f + ...);        // 0..1
float w = ph*2.0 - 1.0;             // -1..1
w = 1.0 - abs(w);                   // 0..1, peaked at ph=0.5 -> sharp crest where noise ~0.5
w = w*w;                            // sharpen
h += w * a;
```
Actually `1-abs(2n-1)` is triangular-peaked; squaring sharpens. This creates crests where noise crosses 0.5 — organic. Sum over octaves with rotation gives rolling choppy field. Good.

Then add a very large swell: low-frequency term:
```
float swell = noise(p*0.02 + vec2(t*0.15, t*0.07)) * 2.0? 
```
Hmm, but the base octave can BE the swell if frequency is low. Let me structure:

- Octave scale: start with `p*0.05` base (wavelength 20 units), amplitude 1.6 for first octave.
- 5–6 octaves total, gain 0.55, lacunarity ~2.05 with rotation.
- Total amplitude roughly 1.6*(1+0.55+0.3+...)≈ 3.7. Camera height ~ 4.5. Good dramatic swell.

To make it "roll", advect: each octave sampled at `q*f + dir*t*speed_f` where dir rotates slightly per octave. I'll keep a global drift direction per octave via the rotation matrix applied to a time vector.

Detail LOD: number of octaves based on distance: `oct = clamp(int(6.0 - dist*0.02), 3, 6)` — hmm, smooth LOD causes popping; using fractional blend is complex. Simpler: use fixed octave count in the height function but fade higher-octave amplitude by distance factor passed in: `a *= smoothstep(...)`? A common trick: pass `lod` float; multiply octave i amplitude by `clamp(lod - float(i), 0, 1)`. Continuous, no popping. 

Actually for performance I can do: marching uses fewer octaves; final shading normal uses more. And scale amplitude attenuation per octave by distance continuously:

```
float oceanHeight(vec2 p, float t, float lod) {
    ...
    float fade = clamp(lod - float(i), 0.0, 1.0);
    h += w * a * fade;
}
```

**Raymarching:**
Standard heightfield march:

```
float raymarchWater(vec3 ro, vec3 rd, float tmax) {
    // rd.y < 0 guaranteed when looking down toward water (or we clamp)
    float t = 0.0;
    float hPrev = ro.y - oceanHeight(ro.xz, ...); // signed distance above surface
    ...
}
```

Simple approach: linear steps with adaptive size + bisection:

```
float t = 0.0;
for (i < 100) {
    vec3 p = ro + rd*t;
    float h = p.y - oceanHeight(p.xz, t, lod);
    if (h < 0.0) { // hit -> bisect between t and tPrev
        ... bisect a few iterations
        return t;
    }
    t += max(0.15, h * 0.6);  // step proportional to height above
    if (t > tmax) break;
}
return tmax (miss -> horizon)
```

This "step proportional to clearance" works decently for heightfields but can overstep crests. Safer variant used widely: step `t += h*0.5 + 0.1` with clamp, plus if h decreasing... I'll use: step = `max(0.02, (ro.y+rd.y*t ... ))`. Let me just use the clearance-proportional stepping with a conservative factor (0.4–0.5) and bisection refine (4–6 iterations). With far plane ~ 500–900 and lod fading detail at distance, should be OK perf-wise on a decent GPU. Also limit ray count: only primary ray (no reflections raymarched — reflection uses sky color only + specular). That keeps cost manageable.

Horizon: if ray doesn't hit water (goes above horizon line), render sky. Since water is bounded amplitude ~±4, rays with `rd.y > ~ (4 - ro.y)/tmax` miss. March handles it: as t→tmax clearance stays positive; break and return -1 → sky.

Fog: blend water color to horizon sky color with `1 - exp(-dist * k)`; also make k larger near grazing. Since I return miss at tmax, rays that miss but pass just over crests near horizon should also be fogged — the sky function itself near horizon can incorporate haze. I'll add horizon fog in sky too (lighten toward sun horizon color).

**Sky function:**
```
vec3 skyColor(vec3 rd, vec3 sunDir) {
    float sunAmount = max(dot(rd, sunDir), 0.0);
    // base gradient: deep blue-slate zenith -> warm near horizon
    float y = max(rd.y, 0.0);
    vec3 zenith = vec3(0.10, 0.13, 0.20);  // dark slate blue
    vec3 horizon = vec3(0.55, 0.33, 0.20); // warm dusk
    vec3 col = mix(horizon, zenith, pow(y, 0.5));
    // sun glow
    col += sunTint * pow(sunAmount, 8.0) * 0.5;   // broad glow
    col += sunTint * pow(sunAmount, 64.0) * 0.8;  // inner glow
    col += vec3(3.0, 2.0, 1.2) * smoothstep(0.9997, 0.99985, sunAmount) * ...; // disc
```
Sun low: elevation ~ 0.05–0.1. Direction e.g. `normalize(vec3(0.0, 0.09, -1.0))` — camera looks toward -z? I'll set camera looking toward -z (forward = -z) with sun ahead slightly off-center: sunDir = normalize(vec3(0.25, 0.08, -1.0)). Slight offset is more cinematic than dead-center; but for the "sun reflection path" leading to camera, having the sun mostly ahead is good. Let me put sun at azimuth slightly right: (0.3, 0.07, -1).

**Clouds:** 2D fbm on the direction projected onto a plane (rd.xz / rd.y style for a sky dome):
```
vec2 cuv = rd.xz / (rd.y + 0.15) * scale + wind*t;
float cl = fbm(cuv);
```
Dark dramatic clouds: base clouds darker than sky, with warm underside lighting near sun: 
```
float cov = smoothstep(0.35, 0.75, cl);
vec3 cloudCol = mix(vec3(0.08,0.08,0.11) /*dark*/, sunlitCol /*orange*/, ...);
```
Lighting from below/sun side: `sunlit = pow(sunAmount, 2) * something` plus cloud-edge detail. Keep it cheap: 4–5 octave fbm. Also two layers (high + low) for depth, parallaxed by different scale factors, moving at different wind speeds.

To keep clouds from covering the sun completely — dramatic but with breaks: coverage threshold so sun area partially visible; plus sun glow bleeds through (multiply glow by (1 - cov*0.7) and add strong glow regardless — glow behind clouds looks fine).

Also darken sky overall near top — stormy. Maybe slight green-grey in clouds.

Cloud function detail:
```
float fbm4(vec2 p) { 4 octaves noise }
vec3 sky(vec3 rd) {
  float sunD = clamp(dot(rd, sunDir), 0., 1.);
  float horizonGlow...
  // clouds
  if (rd.y > 0.01) {
     vec2 uv = rd.xz / (rd.y + 0.12);
     float t1 = t*0.02;
     float c1 = fbm(uv*0.7 + vec2(t*0.03, t*0.011));
     float c2 = fbm(uv*1.7 + vec2(-t*0.05, t*0.02) + 3.7);
     float cl = c1*0.65 + c2*0.35;
     ...
  }
}
```
Careful: `rd.xz / rd.y` blows up near horizon → noise stretches (fine, looks like flat cloud deck) but can alias. Clamp division with `rd.y + 0.15` and fade clouds in near horizon via smoothstep on rd.y. Also fade cloud detail with distance from zenith to reduce aliasing... simple approach ok.

Also reflection of sky on water calls sky() — that doubles cloud cost per pixel. Could make a cheaper sky for reflections (skip fine cloud octaves). I'll write `sky(rd, bool cheap)` or pass an int quality. GLSL ES 3.0 supports function overloading / default? No default params; I'll pass a float `detail` that reduces octaves. Actually simpler: reflections use a simplified sky: gradient + sun glow + broad cloud tint, no detailed fbm. I'll implement `vec3 skySimple(vec3 rd)`.

**Water shading:**
At hit point p, t:
- Normal: finite differences with eps scaled by distance (to reduce aliasing far away): eps = 0.05 + t*0.005 or so. Compute height at (x±e, z), (x, z±e).
- Actually cheaper: 3 extra height evals: hx = H(p.xz+vec2(e,0)) - H(p.xz-vec2(e,0)) → 4 evals total for central differences; or 3 evals with forward differences. Central is better quality; height function with 5 octaves × 4 evals × per pixel is fine.
- Choppy small detail: add a high-frequency noise-based normal perturbation for sparkle (procedural "micro waves"): `n.xz += (noise grad)` — I can add a small extra bump via 2 noise evals.
- fresnel = 0.02 + 0.98*pow(1 - max(dot(n, -rd),0), 5)
- refl = skySimple(reflect(rd, n)) — reflected ray with n flattened a bit? Use full n.
- Water body color: deep teal-green dark: base = mix(deepColor, shallowColor, ...) based on wave height (crests slightly lighter/greener). Subsurface scatter trick: brighter where wave is high and viewed toward sun: `sss = pow(max(dot(sunDir, -rd)... )`. Common trick from Seascape: 
```
vec3 base = vec3(0.02, 0.09, 0.10); // deep
vec3 wcol = vec3(0.05, 0.28, 0.26);
base += wcol * height-based;
```
For sunset, water base should be dark teal with warm reflections dominating. I'll do:
```
vec3 deep = vec3(0.015, 0.045, 0.055);
vec3 shallow = vec3(0.05, 0.16, 0.15);
float hNorm = clamp((p.y - minH)/maxH ...)
vec3 water = mix(deep, shallow, ...);
// subsurface glow toward sun through crest
float sss = pow(clamp(dot(normalize(sunDir + vec3(0,0,-1))? ...
```
Simpler sss: `max(0, p.y - waveMean) * pow(max(dot(rd, sunDir)...)`. Let me do: `float sss = clamp(crestHeight,0,1) * pow(max(dot(rd, -sunDir)??`. Hmm — light passing through a crest toward viewer: viewer looks toward sun through wave → dot(rd, sunDir) negative? rd points from camera into scene; sun in front means dot(rd,sunDir) > 0. Light through crest: strong when looking toward the sun: so factor = pow(max(dot(rd, sunDir),0), 3). Combined with crest height and (1 - fresnel-ish). Multiply by warm-green color: vec3(0.1,0.5,0.4)*0.3. Good.

- Specular sun reflection: 
```
float spec = pow(max(dot(reflect(rd, n), sunDir), 0.0), 300.0) * bigIntensity;
// plus broader glitter:
float glitter = pow(max(dot(reflect(rd, n), sunDir), 0.0), 16.0) * something warm;
```
The long sun path on water comes naturally from perturbed normals at grazing angles. Add sparkle via high-frequency normal jitter. Tone down far away to avoid fireflies; clamp spec.

- Foam: compute from crest measure. I'll compute a "foam factor" during shading: based on the height relative to a threshold (e.g., p.y > 2.2) combined with fbm noise pattern that's advected, plus steepness (1 - n.y). Foam color white-ish with warm sun tint. Implementation:
```
float crest = smoothstep(1.6, 3.2, p.y + 1.2*noise(p.xz*0.5 + t*0.4));  // hmm
float foam = crest * (0.6 + 0.4*noise(p.xz*3.0 + t*vec2(1.0,-1.3)));
foam *= smoothstep(0.6, 0.95, 1.0 - n.y ...)? 
```
Also foam trailing in troughs after crests — too complex; crest foam + slope-based streaks is enough. Use foam pattern from noise octaves at different scales; multiply pattern by crest mask so foam appears as broken whitecaps. Also add foam brightening spec.

Additionally, trailing foam that fades: sample height minus smoothed... skip.

Foam also should appear slightly on the reflection? No.

- Distance fade: apply fog: `col = mix(horizonFogColor, col, exp(-t*0.008))` etc. fog color should match sky near horizon: use `skySimple(normalize(vec3(rd.x, 0.01, rd.z)))`-ish or a fixed warm-grey. I'll compute fog color from sky function at grazing direction toward the ray's azimuth: `fogCol = skySimple(normalize(vec3(rd.x, 0.015, rd.z)))` — gives azimuth-dependent (sun-side warmer) fog. 

**Camera:** positioned at y ~ 4.2, looking toward sun (target at ro + forward). Bob:
```
float bobT = t*0.8;
ro.y += sin(t*1.1)*0.35 + sin(t*0.53+1.0)*0.25;   // heave
// sway
ro.x += sin(t*0.4)*1.5; // slow drift? maybe keep position fixed but rotate
pitch += sin(t*0.9+0.5)*0.02; roll += sin(t*0.7)*0.03; yaw += sin(t*0.23)*0.05;
```
Also camera should ride roughly with the waves — sample water height at camera xz and offset? That could cause the camera to be inside a wave. Better: gentle heave that's roughly synced with a slow swell passing: `ro.y += swellHeight*0.6` where swellHeight computed at camera pos with low octaves. That gives authentic boat feel. I'll compute `float camWave = oceanHeight(ro.xz, t, 2.0);` with only big octaves and blend: `ro.y = baseY + camWave*0.55 + smallBob`. Careful: at t=0 the first frame — fine.

Camera roll/pitch: build rotation from yaw/pitch/roll → forward/right/up vectors.

**First 30 seconds:** everything (waves, foam, sun, clouds, fog, bobbing) is continuous from frame 0; sun could very slowly descend/set slightly over ~60s for drama? If it sets below horizon within 30s that changes the scene; requirement says show everything within first 30s — it already does. I might add a very slow sun elevation oscillation (period ~90s) so within 30s the sun visibly shifts a little — adds life. Keep subtle: elevation from 0.05 to 0.12 sinusoidal. Also clouds drift. Good.

**Performance considerations:**
- Resolution: full window at devicePixelRatio, maybe clamp DPR to 1.5 for perf. I'll render at `min(devicePixelRatio, 2)` and if canvas is huge, could scale down. Let me add adaptive: render scale = min(dpr, 1.75). Simple static choice; also could add dynamic resolution but keep it simple — maybe a mild dynamic resolution: monitor frame time and adjust scale between 0.6 and 1.0 of chosen base? That adds robustness. I'll implement a light adaptive resolution: every ~40 frames, if avg frame time > 22ms reduce scale (min 0.5), if < 12ms increase (max 1). Base = min(dpr, 2). This is good engineering for a heavy raymarcher. Keep it simple and safe.

- Reduce octave counts in march vs shading. March height: 5 octaves with LOD fade; normal eval: 6.

Loop unrolling: GLSL loops with dynamic break are fine in WebGL2 (ES 3.0). Use `for (int i=0;i<6;i++){ if (float(i)>=lod) break; ...}`.

**Precision:** `precision highp float;` in fragment shader. 

**JS structure:**
```js
const canvas = document.getElementById('c');
const gl = canvas.getContext('webgl2', {antialias:false, ...});
if (!gl) show fallback message.
compile program, fullscreen triangle via gl_VertexID trick (no buffer needed!):
  vertex shader: 
    const vec2 verts[3] = vec2[3](vec2(-1,-1), vec2(3,-1), vec2(-1,3));
    gl_Position = vec4(verts[gl_VertexID], 0, 1);
Need a VAO? WebGL2 requires... drawing without any attributes: need a bound VAO? In WebGL2, you can draw with no attributes using gl_VertexID; the default VAO exists (unlike core GL). WebGL2 has a default VAO bound initially, so gl.drawArrays(gl.TRIANGLES, 0, 3) works with no buffers. Yes, that's a known technique in WebGL2.

Uniforms: uTime (float seconds), uRes (vec2).
Resize: set canvas.width/height = clientWidth*dpr*scale, CSS size 100vw/100vh. Handle via ResizeObserver or window resize event; call on load. Also handle devicePixelRatio changes (matchMedia) — resize listener covers most; recompute dpr each resize.
Render loop: requestAnimationFrame(ts) → t = (ts - start)/1000. But careful: first timestamp. Use `const t = (ts - t0)*0.001` with t0 set on first frame.
```

Also handle context loss politely? Optional — add event listener to prevent default and try restore. Keep it brief; maybe skip for simplicity, but a small `webglcontextlost` handler with `event.preventDefault()` and restore-on-restored re-init is nice craft. I'll include minimal handling.

**Shader writing — let me now write it fully and carefully.**

```glsl
#version 300 es
precision highp float;

uniform float uTime;
uniform vec2  uRes;
out vec4 fragColor;

#define SUN_DIR normalize(vec3(0.28, 0.10, -1.0))  // will make it a uniform-ish const computed in main? Keep const via function.
```

Actually make sun elevation slowly vary: compute sunDir in main from uTime: 
```
float sunEl = 0.075 + 0.045*sin(uTime*0.05); // period ~125s; within 30s elevation changes by ~0.045*sin(1.5)≈0.045*0.997 full swing? sin(0.05*30)=sin(1.5)=0.997 — that's the full swing within 30s! Period = 2π/0.05 ≈ 125.7s; at t=30, phase=1.5 rad ≈ 86°, so most of the swing happens in first ~31s (peak at phase π/2 → t≈31.4s). Nice: sun visibly rises slightly toward t=31 then descends. Good — within 30s the sun moves noticeably. Maybe amplitude 0.04, base 0.08.
vec3 sunDir = normalize(vec3(0.26, sunEl, -1.0));
```

Constants:
```
const int   MARCH_STEPS = 96? 
```
Cost: 96 steps × height(5 octaves ≈ 5 noise = each 4 hashes) ≈ 96×5×4 = ~2000 hash calls per pixel worst case... heavy but heightfield marching usually terminates early. With clearance-based stepping near camera, average steps maybe 40–60. Adaptive resolution helps. I could reduce: far 600, step factor 0.55 with a safety that reduces step when clearance was decreasing? Let me implement a robust marcher:

```
float traceWater(vec3 ro, vec3 rd, out vec3 pos) {
    float tm = 0.0;      // time where above
    float tM = TMAX;     
    // if ray can never hit within tmax: ro.y + rd.y*tM > maxWave → early out
    float maxH = 4.0;
    if (ro.y > maxH && rd.y > 0.0) return -1.0;  // looking up entirely → sky (but water reflections? primary only)
    // actually also if ro.y > maxH: t_hit_max = (maxH - ro.y)/rd.y for rd.y<0... general: if ray never descends below maxH within tmax → sky
    float yAtMax = ro.y + rd.y*TMAX;
    if (yAtMax > maxH && ro.y > maxH) return -1.0;
```
Hmm — with camera bobbing, ro.y stays ~3–5 which is within wave range, so rays pointing up will still be marched... but they'd march up and away and never hit. Early-out: if rd.y > 0.02 and ro.y > waveMax → sky. If rd.y <= 0 it will eventually cross. If ro.y < waveMin? camera won't go below. Also for near-horizon rays (rd.y slightly >0 but small), ro.y ~4, maxH ~4: yAtMax = 4 + 0.005*600 = 7 > 4 → early out → sky. Good, cheap horizon rays.

March body (secant-like):
```
float t = 0.1;
float dt;
for (int i = 0; i < 100; i++) {
    vec3 p = ro + rd*t;
    float h = p.y - waveH(p.xz, t);
    if (h < 0.002*t ... ) hit
```
Standard:
```
    if (h < 0.0) {
        // bisect between tPrev and t
        float a = tPrev, b = t;
        for (int j = 0; j < 5; j++) {
            float m = 0.5*(a+b);
            vec3 pm = ro + rd*m;
            if (pm.y - waveH(pm.xz, m) < 0.0) b = m; else a = m;
        }
        t = 0.5*(a+b)... return
    }
    tPrev = t;
    t += clamp(h*0.5, minStep, maxStep) — min step grows with t: minStep = 0.02 + t*0.01? 
```
Hmm, waveH evaluated with LOD based on t so distant cheap. Step size: `t += h*0.45 + 0.02 + t*0.004;` — the additive term ensures progress at grazing angles where h can be small; proportional term adapts. But risk: stepping over a crest when h is large but crest is close — the proportional term mitigates (h small near surface). Overstepping happens when ray is high above water and steps big, then lands past a crest into a trough — bisection then finds the crossing but possibly missed an intermediate crest (crossed twice between samples → bisection finds one of them; visually acceptable, minor artifacts on crest silhouettes at horizon; with fog + distance it's fine).

Bisection each hit: 5 extra height evals. OK.

Also to help crest aliasing at horizon, LOD fade of high octaves with t.

TMAX = 900? With fog kicking in by ~0.006*900... let me set fog so that around t=500–700 water fully fades into horizon haze. TMAX=800.

Wait — horizon: with camera at y≈4 and waves up to ~4, geometric horizon is far; the water plane visually converges. Rays slightly downward but not hitting within TMAX → treat as sky/fog. To avoid a visible seam between "fogged water at TMAX" and "sky", set fog so that at TMAX fog≈1: fogAmount = 1 - exp(-t*density) with density chosen so at 800 it's ~0.98; and for sky rays near horizon, skySimple includes horizon haze blending toward same fog color. I'll make sky near rd.y≈0 blend toward the same haze color computed per azimuth. Let me define hazeColor(azimuth-ish) = skySimple at grazing; then in sky(), for rd.y < ~0.1, blend toward haze. Since skySimple itself is the function, in the sky path I can just apply: `col = mix(col, hazeCol, 1-exp(-max(0.0,(0.06-rd.y))*40))`? Simpler: fogColor = skySimple(vec3(rd.x,0.0,rd.z)) normalized horizontal dir; water fog uses same. In sky, blend clouds/base toward fogColor as rd.y→0. That guarantees seamless horizon.

Let me structure sky as:
```
vec3 skyBase(vec3 rd, float detail) {
    float sunDot = clamp(dot(rd, sunDir), 0.0, 1.0);
    float horizon = pow(1.0 - clamp(rd.y,0.0,1.0), ...);
```

I'll write concrete code below. Let me now carefully draft the whole fragment shader.

```
// ---------- constants ----------
const float PI = 3.14159265;

// ---------- hashes & noise ----------
float hash12(vec2 p){
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}
float vnoise(vec2 p){
    vec2 i = floor(p), f = fract(p);
    vec2 u = f*f*(3.0-2.0*f);
    return mix(mix(hash12(i),             hash12(i+vec2(1,0)), u.x),
               mix(hash12(i+vec2(0,1)),   hash12(i+vec2(1,1)), u.x), u.y);
}
```

Better smooth: quintic u = f*f*f*(f*(f*6-15)+10) — smoother normals. Use quintic.

FBM for clouds:
```
float fbm(vec2 p){
    float v = 0.0, a = 0.5;
    mat2 m = mat2(1.6,1.2,-1.2,1.6);
    for(int i=0;i<5;i++){ v += a*vnoise(p); p = m*p; a *= 0.5; }
    return v;  // in ~[0, ~0.97]
}
```
Cloud fbm should be able to get near 1 with 5 octaves a=0.5 sum=0.968 max... typical max lower (~0.75). Adjust coverage thresholds accordingly; or normalize. Use coverage = smoothstep(0.42, 0.78, fbm).

Ocean height:
```
// ridged multioctave, advected
float waveH(vec2 p, float t, float lod){
    p *= 0.045;                       // base wavelength ~22 world units
    vec2 drift = vec2(0.9, 0.36)*t*0.55;   // primary travel dir & speed
    // domain warp for organic motion
    vec2 w = vec2(vnoise(p*0.9 + drift*0.35),
                  vnoise(p*0.9 - drift*0.28 + 7.3));
    p += 0.30*(w - 0.5)*2.0;   // warp strength

    float h = 0.0;
    float a = 1.0;
    float f = 1.0;
    mat2 m = mat2(1.72, 1.15, -1.15, 1.72);  // rotate & scale ~2.05
    for (int i = 0; i < 6; i++){
        float fade = clamp(lod - float(i), 0.0, 1.0);
        if (fade <= 0.001) break;
        float n = vnoise(p*f + drift*(f*0.35) + float(i)*13.7);
        float ridge = 1.0 - abs(n*2.0 - 1.0);   // 0..1 peaked where n≈0.5
        ridge *= ridge;                          // sharpen crests
        h += ridge * a * fade;
        p = m*p; f = 1.0; // wait — after rotating p, f should stay 1? 
```
Hmm: standard FBM rotates the domain and multiplies frequency by lacunarity. If I rotate p each octave and keep multiplying f, that's fine too: `p = m*p` where m scales by ~2.05 and rotates; then f stays 1. Or keep p and use f. Let me do the classic iq fbm: `p = m*p; a *= 0.5;` with m containing scale. Then time advection: the drift term must scale with frequency too — if p is scaled by m each octave, adding `drift*f_i`... easier to track: after scaling p by m (which includes ×2.05 scale), the drift in that octave's domain should also scale. If I add drift before scaling: n = vnoise(p + drift) where drift per octave = drift0 * (lacunarity^i) — track drift separately:

```
    vec2 d = vec2(0.9, 0.36) * t * 0.55;   // in base domain
    ...
    for i:
        float n = vnoise(p + d);
        ...shape...
        p = m*p;
        d = (m_rot only)*d * 1.0? 
```
If p is multiplied by m (scale+rot), then to keep the pattern advecting consistently, d should be multiplied by the same matrix (so translation commutes with scaling): if octave i+1 samples vnoise(m*p_prev + D), and we want it equivalent to m*(p_prev + d) = m*p_prev + m*d, then D = m*d. So: `d = m*d;` each iteration. That works — advection scales with octave frequency. 

So:
```
float waveH(vec2 pos, float t, float lod){
    vec2 p = pos * 0.045;
    // gentle domain warp
    vec2 wp = vec2(vnoise(p*0.8 + vec2(t*0.11, -t*0.07)),
                   vnoise(p*0.8 + vec2(-t*0.09, t*0.13) + 5.2));
    p += (wp - 0.5) * 0.9;

    vec2 d = vec2(0.95, 0.38) * (t * 0.45);
    float h = 0.0;
    float a = 1.0;
    const mat2 m = mat2(1.68, 1.18, -1.18, 1.68);  // det scale? |m| = 1.68²+1.18² = 2.82+1.39=4.21, sqrt(4.21)=2.05 lacunarity. 

    for (int i = 0; i < 6; i++){
        float fade = clamp(lod - float(i), 0.0, 1.0);
        if (fade < 0.003) break;
        float n = vnoise(p + d);
        float ridge = 1.0 - abs(n*2.0 - 1.0);
        ridge *= ridge;
        h += ridge * a * fade;
        p = m * p;
        d = m * d;
        a *= 0.52;
    }
    return h;
}
```
Max h ≈ 1+0.52+0.27+0.14+0.07+0.037 ≈ 2.04, typical mean ~0.9. World amplitude: multiply outside: `h*waveAmp` with waveAmp ≈ 1.9 → peaks ~3.9, mean ~1.7. Camera base y ~ 4.6, heave ±0.6 → stays above? Mean water 1.7, crest 3.9 + camera at 4.6−0.6 = 4.0... camera could dip below a crest occasionally — actually that's a problem: if camera inside wave, everything breaks. Options: raise camera to 5.2, reduce amp to 1.7 (peaks 3.5), heave ±0.5 with correlation to wave height under camera (ride the swell: camY = base + waveAtCam*0.6 — when wave is high under camera, camera rises too). With riding: camY = 2.6 + 0.75*waveAtCam + smallBob. Wave at cam ranges 0..3.5 → camY ranges 2.6..5.2+. Hmm min 2.6 while local water is 0 at that point but nearby crests could be ~3.9 — camera at 2.6 could be below distant crest → ray hits water above camera → hits with negative clearance... The marcher handles p.y - h: if ray starts below a crest it'll immediately register h<0 at t=0.1 → weird artifact (a wall of water in face). To be safe: camY = 1.8 + waveAtCam*0.9 + bob(±0.15)? Then when local wave is 0 (trough), camera at 1.8+0.15 = 1.95; nearby crests up to... crest heights are spatially correlated; the max over the visible nearfield could still exceed 1.95. In deep swell oceans, a boat in a trough does see walls of water — that's actually realistic and dramatic! But rendering-wise, camera inside/behind a crest that occludes everything looks broken unless handled. The marcher with h<0 at start: first sample t=0.05: p.y - h... if p is inside a wave, h<0 → bisection from tPrev=0? Could return t≈0 → whole screen water. Ugly but arguably "wave crashes over you" — in a loop, it could look glitchy.

Safer: guarantee camera well above max wave: base camY = 5.0, waves peak ~3.6, heave ±0.4 → min camY 4.6 > 3.6. Waves with amplitude 1.9×2.04 = 3.88 max theoretical (rare). Set amp 1.75 → max 3.57. camY = 5.0 + sin bob ±0.45 → min 4.55 > 3.57. Safe. And the boat feel comes from bobbing + roll + the visual of big waves. Also I can add partial swell-riding: sample wave with lod=2 at camera pos, add *0.35: max extra 0.7 → camY range 5.0±0.7+small → min 4.3 > 3.57 ✓. Let me do: `float camRide = waveH(ro.xz, t, 2.0);` careful — waveH returns unscaled h (0..2.04); amp multiply 1.75 → up to 3.57; ride factor 0.28 → up to 1.0 added when at crest. Define camY = 4.7 + camRide*1.75*0.28 + heaveBob where heaveBob = 0.18*sin(t*1.3)+0.12*sin(t*2.1+1.7) (±0.3). Range: 4.7 + 0..1.0 − 0.3 .. = 4.4..6.0. Max wave 3.57 < 4.4 ✓.

Wait, but the riding term with factor 0.28 of local height — if local water is at crest 3.5, cam at 4.7+1.0 = 5.7, clearance 2.2 above local surface. In trough: local 0, cam 4.7±0.3 → clearance ≥ 4.4 above local but nearby crests 3.57 → clearance ≥0.85. Always above. 

Camera orientation: look toward sun azimuth with slight yaw sway; pitch slightly downward (~ -0.12 rad) so water occupies lower 60% and horizon upper; pitch sway ±0.02; roll sway ±0.02.

Forward: from yaw/pitch: 
```
float yaw = 0.06*sin(t*0.21) ; // sun at azimuth atan2(0.26,-1)=~0.253 rad — align forward with sun azimuth: base yaw = atan2(0.26?..). Simpler: forward = normalize(vec3(sin(yaw), pitch, -cos(yaw))) with yaw base 0.25 matching sun azimuth 0.253. Let me set sun azimuth AZ = 0.25; sunDir = normalize(vec3(sin(AZ)*cosEl, sinEl, -cos(AZ)*cosEl)) ≈ vec3(0.25, el, -0.97). And camera yaw = AZ + 0.05*sin(t*0.19).
```
Build basis:
```
vec3 fw = vec3(sin(yaw)*cos(pitch), sin(pitch), -cos(yaw)*cos(pitch));
vec3 rt = normalize(cross(fw, vec3(0,1,0)));  // careful sign: right = normalize(cross(fw, up))→ points... for fw=(0,0,-1): cross(fw,up)= (0,0,-1)×(0,1,0) = (0*0−(−1)*1, (−1)*0−0*0, 0*1−0*0) = (1,0,0). ✓ right = +x.
vec3 up = cross(rt, fw);  // (1,0,0)×(0,0,-1) = (0*(-1)−0*0, 0*0−1*(−1), 0) = (0,1,0) ✓
// apply roll: rotate rt,up around fw:
rt = cos(roll)*rt + sin(roll)*up; up = -sin(roll)*rt0 + cos(roll)*up0 — do properly.
rd = normalize(fw + uv.x*rt*aspectScale + uv.y*up) with fov: uv in [-1,1], scale tan(fov/2): fov ~ 60° vertical? For cinematic: focal = 1.3 → half-fov ≈ atan(1/1.3) ≈ 37.6° vertical — a bit tight for ocean; use focal 1.15 (~41°). Also handle aspect: uv.x *= uRes.x/uRes.y.
```
Standard: `vec2 uv = (2.0*fragCoord - uRes)/uRes.y;` then rd = normalize(uv.x*rt + uv.y*up + focal*fw).

**Normals:**
```
vec3 waveNormal(vec2 p, float t, float lod, float eps){
    float hC = waveH(p, t, lod);       // already known? pass in
    float hX = waveH(p + vec2(eps,0), t, lod);
    float hZ = waveH(p + vec2(0,eps), t, lod);
    // world amp scaling
    vec3 n = normalize(vec3(-(hX-hC)*amp/eps... 
```
Careful: height = waveH(...)*AMP. Normal of heightfield H(x,z): N = normalize(vec3(-dHdx, 1, -dHdz)). dHdx ≈ (H(x+e)−H(x−e))/(2e) for central. I'll do central differences with 4 evals for symmetry:
Actually 3 evals forward difference is cheaper and fine with small eps; but forward differences bias normals slightly. With eps small relative to feature size, negligible. Use forward: hx = H(p+ex)−H(p); hz = H(p+ez)−H(p); n = normalize(vec3(−hx*amp/eps? wait units: H world = amp*ridge. dHdx = amp*(hX−hC)/eps.

eps: scale with distance to reduce aliasing: eps = max(0.03, t*0.01)? At t=600, eps=6 — that's huge smoothing (good for horizon shimmer). Also reduce octave detail at distance via lod passed = detail level. Two LOD controls: normal eps growth handles geometric aliasing.

Micro-detail normal: add high-frequency sparkle perturbation:
```
float micro(vec2 p, float t) — 2 octaves of vnoise-based derivative fake:
n.xz += (vec2(vnoise(p*6.0+t*...), vnoise(p*6.0+17.0+...)) - 0.5) * 0.06;
```
Cheap and effective for glitter. Modulate by distance fade (fade out far) to avoid noise aliasing at horizon: `sparkle *= exp(-t*0.01)` or smoothstep(600,100,t).

**Foam:**
Compute at shading:
```
float crest = clamp((hw - 1.55) / 1.0, 0.0, 1.0); // hw in world units
```
Hmm threshold: mean height amp*0.9 ≈ 1.6; crests > ~2.6. foamBase = smoothstep(2.3, 3.3, worldH). Plus slope: steep = 1 − n.y (0 flat). foam = foamBase * pattern. pattern = fbm-ish 2–3 octaves at world scale 0.6–2 advected with the drift so foam moves with waves? Advecting foam with same drift as waves: pattern = vnoise(p*0.55 + driftWorld). Also secondary fine foam: vnoise(p*2.6+...). Compose:

```
float foamPattern = fbm(p*0.5 + wind*t*0.1 ...)  // 3 octaves
float foam = smoothstep(2.2, 3.2, H) * smoothstep(0.35, 0.75, foamPattern);
foam += smoothstep(0.35, 0.75, steepness) * small streaks?
```
Hmm wait, H world = amp*h. Let me define `float hw = p.y` at hit (that IS the world height). Crest foam: smoothstep(2.35, 3.15, p.y). Plus whitecaps also from deceleration/Jacobian — skip, keep crest+noise.

Also foam on wave fronts (where slope faces camera...) keep simple.

Foam shading: `col = mix(col, foamColor * (sun warm light), foam)` where foamColor base vec3(0.9) tinted by light: foamLit = foamCol * (ambient + sunColor*max(dot(n,sunDir),0)*...). Foam slightly warm from sunset: multiply by mix(vec3(1.0,0.85,0.7)...). Also give foam a bit of the sun glitter.

Edge/antialias foam with smoothsteps.

**Sun reflection & sky reflection:**
```
vec3 r = reflect(rd, n);
r.y = abs(r.y)*? // ensure reflects upward-ish; if r.y < 0.02 clamp to avoid reflecting below horizon: r.y = max(r.y, 0.02); renormalize? Just clamp y then normalize.
vec3 refl = skySimple(r);
float fres = 0.02 + 0.98*pow(1.0 - clamp(dot(n, -rd), 0.0, 1.0), 5.0);
// specular
float specPow = ...
float sunSpec = pow(clamp(dot(r, sunDir),0.,1.), 220.0) * 60.0;  // hot spot — clamp
sunSpec += pow(..., 24.0)*1.2;  // glitter path
```
Since normals are noisy, dot(r,sunDir) spreads → glitter path appears. Multiply by fres? Specular typically multiplied by fresnel-ish; at grazing fres→1, sun path strong. `spec = sunSpec * fres`? The glitter path at grazing already strong; multiplying by fres makes near-camera specular dim — actually fine and physical. Add also `spec *= smoothstep(0.0, 200.0, t)`? No — near sun path should extend to horizon. Clamp total to avoid fireflies: `min(spec, 8.0)`? With pow 220 and noisy normals values can spike; clamp r·sd before pow: use `float sd = clamp(dot(r,sunDir),0.,1.);` pow fine. Intensity: sun disc luminance ~ maybe 50 for HDR then tonemap. I'll tonemap with ACES-ish or `col = col/(1+col)`? Better: use a filmic curve: `col = 1.0 - exp(-col*exposure)` then gamma. Or ACES approx:
```
vec3 aces(vec3 x){ return clamp((x*(2.51*x+0.03))/(x*(2.43*x+0.59)+0.14),0.,1.); }
```
Then gamma 1/2.2 or rely on canvas sRGB — canvas expects sRGB-encoded output; apply pow(col, 1/2.2) after tonemap. ACES output is roughly display-referred already; commonly people apply gamma after. I'll do: col = aces(col*exposure); col = pow(col, vec3(0.4545)).

Hmm, ACES fit already includes some... the common Narkowicz fit maps linear→display-ish but expects gamma applied after. Yes apply gamma after.

**skySimple (for reflections & fog):**
```
vec3 skySimple(vec3 rd){
    float sd = clamp(dot(rd, sunDir), 0.0, 1.0);
    float y = max(rd.y, 0.0);
    vec3 col = mix(vec3(0.34,0.22,0.16), vec3(0.06,0.09,0.14), pow(y? ...));
```
Design colors (linear, pre-tonemap; sunset):
- Zenith: deep desaturated blue-grey: (0.05, 0.08, 0.14)
- Horizon away from sun: warm grey-mauve: (0.38, 0.26, 0.22)
- Horizon near sun: strong orange: (1.3, 0.45, 0.12)
- Sun tint: (1.0, 0.42, 0.12) glow; disc (4.0, 1.6, 0.6)×k.

skySimple:
```
float horizonFade = pow(1.0 - y, 3.0);
vec3 grad = mix(zenith, horizonWarm, horizonFade);
float az = dot(normalize(vec3(rd.x, 0.0, rd.z)), sunAzDir); // azimuthal warmth
```
Simpler: warmth via pow(sd, small):
```
vec3 col = mix(vec3(0.055,0.085,0.15), vec3(0.30,0.22,0.20), pow(1.0-y, 2.0));
col += vec3(1.15,0.42,0.10) * pow(sd, 5.0) * 0.55;         // broad warm wash toward sun
col += vec3(1.20,0.50,0.15) * pow(sd, 32.0) * 0.9;         // glow
col += vec3(2.2,1.1,0.45)  * pow(sd, 180.0)*2.0;           // inner
col += vec3(6.0,2.6,0.9)   * smoothstep(0.99955, 0.99985, sd) * 3.0;  // disc (angular radius ~1°)
```
Sun angular size: cos ~ 0.99985 ≈ 1°. smoothstep range gives soft edge. Since sunDir elevation ~0.1, the disc near horizon — good.

Horizon haze in skySimple: blend toward haze color as y→0:
```
vec3 haze = mix(vec3(0.30,0.20,0.16), vec3(0.9,0.42,0.18), pow(sdHoriz,3.0));
col = mix(col, haze, smoothstep(0.16, 0.0, y));   // only lower sky
```
where sdHoriz = dot(normalize(horizontal rd), horizontal sun) clamped. This makes skySimple self-consistent as fog color when evaluated at y=0: fogColor(rdHoriz) = skySimple(horizontal) — matches the water fog! Good: define `vec3 fogColor(vec3 rd) { return skySimple(normalize(vec3(rd.x, 0.0, rd.z))); }` but skySimple at y=0 already returns mostly haze — fine.

Careful: skySimple is used for reflections of sky in water — reflections near horizon = haze color, correct.

Clouds in main sky (not in reflections... but reflections should show clouds too, roughly). Compromise: include clouds in skySimple but with fewer octaves via a `detail` parameter. Cloud cost: fbm 4 octaves ≈ 16 hashes; called once per water pixel for reflection + once for sky pixels. Acceptable.

Let me define:
```
vec3 skyColor(vec3 rd, float detail){
    ... base gradient + sun glow ...
    // clouds
    float cl = 0.0;
    float cov = 0.0;
    if (rd.y > 0.0) {
        vec2 cuv = rd.xz / (rd.y + 0.18) * 1.35;
        // two layers
        float t = uTime;
        float c1 = fbmN(cuv*0.45 + vec2(t*0.021, t*0.008), oct1);
        float c2 = fbmN(cuv*1.15 + vec2(-t*0.033, t*0.012) + 19.7, oct2);
        float density = c1*0.72 + c2*0.42;   // ~0..1.1
        // coverage shaping
        cov = smoothstep(0.34, 0.72, density);
        // cloud shading
        float edge = smoothstep(0.30, 0.55, density) - cov; // rim?
```
Cloud lighting: dark slate bodies, warm rim toward sun:
```
vec3 cloudDark = vec3(0.055, 0.06, 0.075);
vec3 cloudLit  = vec3(0.55, 0.28, 0.14);  // sunlit undersides
float lit = pow(sd, 2.0) * (1.0 - cov*0.5) ... 
vec3 cloudCol = mix(cloudDark, cloudLit, litAmount);
```
litAmount should also depend on cloud "height" in the fbm (denser = darker): use density: thicker parts darker: lit *= (1-density). Also gaps near sun show glow.

Blend: `col = mix(col, cloudCol, cov * cloudFade)` where cloudFade = smoothstep(0.02, 0.12, rd.y) — fade clouds at horizon into haze (perspective). Also clouds shouldn't appear below horizon (rd.y<0 water covers anyway).

Sun through clouds: attenuate disc by cov partially: discGlow terms computed before cloud mix? If we mix cloud over sun disc, disc gets covered. Add bleed: after mixing, add `pow(sd,32)*0.35*(1.0-cov)` etc. Or attenuate disc by (1 - cov*0.85) so sun partially punches through thin cloud. Do: compute disc term, multiply by (1 - cov*0.8), add after cloud mix. Also broad glow unaffected (atmospheric).

Silver lining: `cov` edge near sun gets bright rim: rim = pow(sd,3)*smoothstep(0.25,0.6,density)*(1-cov)... keep something simple: cloudCol += sunTint * pow(sd, 4.0) * 0.25 * (1.0 - cov) — edges near sun glow. 

fbmN with param octaves: implement two functions fbm3/fbm4 or loop with detail-based break like waves. I'll write one fbm with max 5 and a float `oct` fade like waves.

Actually to keep compile simple, write:
```
float fbm(vec2 p, float oct){
    float v=0., a=0.5;
    for(int i=0;i<5;i++){
        float fade = clamp(oct-float(i),0.,1.);
        if (fade<0.003) break;
        v += a*vnoise(p)*fade;
        p = m*p; a*=0.55;
    }
    return v;
}
```

**Main:**
```
void main(){
    vec3 sunDir = ... from time
    vec2 uv = (2.0*gl_FragCoord.xy - uRes) / uRes.y;
    // camera
    float t = uTime;
    vec3 ro;
    float ride = waveH(ro0.xz...) — need ro.xz first; camera drifts? Keep camera xz fixed at (0,0)? A boat drifts: slow forward motion adds life: ro.xz = vec2(t*2.2, 0)? Moving through wave field at 2.2 u/s with waves drifting — creates passing swells. But waveH advection already moves waves toward camera; camera motion adds parallax. Add slow drift: pos = vec2(sin(t*0.05)*3.0, t*1.2)? Simple constant forward drift along -z? Waves drift direction (0.95,0.38): they travel roughly +x+z... hmm drift vector d = vec2(0.95,0.38)*t*0.45 added to domain p → pattern moves in -d direction? Sampling vnoise(p + d): as t increases, feature at p0+d corresponds to base point p0 → feature moves from p0+d to p0 as t↑ → moves along −d. So waves travel toward −(0.95,0.38) direction i.e. toward −x,−z. Camera looking toward −z (sun at −z). Waves moving toward −z → toward camera. 

If camera also drifts forward (−z) at some speed, it moves with waves (following) — reduce relative motion. Let camera stay near origin with gentle circular sway: ro.xz = vec2(2.0*sin(t*0.07), 1.5*sin(t*0.05+2.0)). Slow, keeps things stable.
    
    float tRide = waveH(ro.xz, t, 2.0) * 1.75;   // world height at cam (amp 1.75)
    float heave = 0.16*sin(t*1.4) + 0.11*sin(t*2.3+1.3);
    ro.y = 4.75 + tRide*0.30 + heave;
```
Check min: tRide min ~0 (mean ~0.85*1.75≈1.5) — tRide*0.3 ∈ [0,1.06]; cam y ∈ [4.45, 6.1]; max wave 3.6. clearance ≥ 0.85 at worst combined? Worst: cam at trough riding value 0 → y=4.45; nearby crest 3.6 → clearance 0.85. OK. But typical clearance above local water: cam 4.75+ride*0.3 vs water ride*1.75 → diff = 4.75 − 1.75*0.7*ride ≈ 4.75−1.2*ride ∈ [2.8, 4.75]. Fine, boat-like (a couple meters above waterline).

Pitch: base −0.10 (looking slightly down), sway: +0.025*sin(t*0.9)+0.015*sin(t*1.7+2.0). Yaw = AZ + 0.04*sin(t*0.23)+0.02*sin(t*0.41). Roll = 0.05*sin(t*0.63+0.7)+0.02*sin(t*1.1).

Heave frequencies: real boat heave ~0.1–0.5 Hz. t*1.4 → 0.22Hz ✓.

March:

```
    vec3 rd = normalize(uv.x*rt + uv.y*up + 1.35*fw);
    vec3 col;
    float tHit = trace(ro, rd);
    if (tHit > 0.0) { shade water } else { col = skyColor(rd, full) }
```
trace returns t or −1. Also cap: if rd.y >= small and ro.y > maxWave → skip.

Also note: rays pointing up but ro.y < maxWave? cam min 4.45 > 3.6 → any rd.y>0... p.y at t: ro.y + rd.y*t ≥ ro.y > 3.6 ≥ h always → never hits. Early-out: `if (rd.y > 0.0) return -1.0;` plus ro.y > maxH check unnecessary given cam always above. But safety: keep condition `if (rd.y > 0.0 && ro.y > 4.2) return -1.0;` safe.

Wait — with pitch sway the entire screen could be sky sometimes? base pitch −0.10 with focal 1.35, half-fov vertical ≈ atan(1/1.35) ≈ 36.5° → top of screen at pitch −0.10 + 0.64 rad ≈ +0.54 rad up. Plenty of sky. Water occupies from bottom to horizon. Horizon line (rd.y where ray grazes at large t): since water exists everywhere, horizon at rd.y ≈ 0⁻ plus distant wave tops → some rays with rd.y slightly >0 hit distant crests? They'd need crest > ro.y at large t: crest max 3.6 < ro.y 4.45 → never. So horizon = rays with rd.y < 0 eventually hit. Rays with rd.y ≥ 0 → sky. The visual horizon then sits where wave silhouette ends: distant waves fade via LOD + fog. Good.

But horizon will be a hard line at rd.y=0 between "never hits" (sky) and "hits eventually" — with LOD flattening distant waves and fog, the water at t≈800 is fully fog color ≈ haze = sky at y≈0 → seamless. Need fog density so exp(-t*k) ≈ 0 at 800: k=0.006 → exp(-4.8)=0.008 ✓. Also LOD: at t=800 lod → octaves fade: lod(t) = max(2.0, 7.0 − t*0.012)? At t=0: 7 (all 6 octaves... clamp), t=100: 5.8, t=400: 2.2, ≥420: 2. Hmm lod 2 → only 2 octaves = smooth big swell; normal eps also grows. Water at distance becomes smooth plane fading into fog — good.

Also march step near grazing: clearance h can be large relative to horizontal progress... steps proportional to vertical clearance works OK; but at grazing angles, steps of h*0.5 in 3D distance move mostly horizontally if rd mostly horizontal — vertical clearance changes slowly (rd.y small) → many steps. Cap iterations 100–128, cap TMAX 800. Add step floor that grows with t: `t += max(h*0.42, 0.05 + t*0.012)`? At t=400, floor ≈ 4.85 → ~ tens of steps to cross 400–800. Rough step count: near field t<100 with clearance ~2: step ~0.9 → 100 steps to cover 100... hmm too many. Let me estimate: camera clearance ~3, rd.y for mid-screen ≈ −0.3. Height above water decreases: clearance c(t) ≈ ro.y − h(x(t)) with horizontal speed |rd.xz|≈0.95 per unit t. Step = max(0.42c, floor). c ~ 3 initially → step 1.26; as it descends c shrinks... to reach water takes Δy=3 → t ≈ 10 → ~8 steps. For grazing rd.y=−0.02: Δy=3 needs t=150, steps: c stays ~2–3, step ~1 → ~100+ steps. Cap 110 iterations and floor 0.05+t*0.01: at t=100 floor 1.05, t=300 → 3.05 → progress accelerates; from t=100 to 800 needs 700/avg3 ≈ 230 steps — exceeds cap. So grazing rays end at t≈300–500 without hitting → treated as miss? If loop exhausts without h<0, return −1 → sky, but at t=500 fog ≈ 1−exp(−3)=0.95 — water nearly fog color; treating as sky at that distance = haze — nearly identical → invisible seam. But the water shading at those pixels is sky color instead of fogged water — since fog≈95%+ and haze==skySimple(y≈0) which equals what fogged water converges to, difference tiny. Acceptable. Alternatively on loop exhaustion, return t and shade water (fully fogged → same result). I'll return −1 on exhaustion but also apply fog in sky near horizon consistently (already designed haze). Fine.

Set: MAXSTEPS 110, TMAX 800, k fog 0.0055 → at 300: 1−exp(−1.65)=0.81; hmm water at t=300 only 80% fogged — grazing rays ending at 300 rendered as sky (haze) vs fogged water (80% water color) → possible seam band at horizon where step budget exhausts. The exhaust boundary is noisy per-pixel → could look like shimmering band. Mitigation: make floor grow faster: floor = 0.05 + t*0.02 → at 300: 6.05; from 100→800 avg floor ~9 → ~78 steps ✓. And steps proportional term dominates near field. Rays typically terminate by hitting water before t=400 anyway for rd.y<−0.01 (Δy≈3 → t≈150 at grazing with |rd.xz|≈1: hits when cumulative descent 3 → t≈150·(3/…) whatever — for rd.y=−0.005 nearly horizontal, t≈600 if ever; but LOD flattening means h(x) at distance is the 2-octave field max 3.6*fade... lod at 400 = 2.2 → higher octaves faded, still peaks ~2.5? lod=2 means first two octaves full, third faded 0.2 → max ≈ 1+0.52+0.27*0.2 ≈ 1.57 → world 2.75 < ro.y → still no hit for grazing rays! So visually horizon = plane where even the flattened swell isn't reached within TMAX; rays slightly below horizontal hit the flattened swell at some t. For rd.y = −0.004: descent to 2.75−4.45 = −1.7 needs t = 425 < 800 ✓ hits. rd.y = −0.001 → needs 1700 > TMAX → miss → sky. So horizon line sits at rd.y ≈ −0.004 region — a razor-thin band; the transition is softened by fog (t≈425 → fog 1−exp(−2.3)=0.9 → 90% haze; remaining 10% water tint vs sky at that grazing angle...). The sky just above horizon (y→0+) is haze color, water just below is 90% haze + 10% dark water + reflection ≈ haze too. Should blend OK. I'll also add slight extra fog boost near horizon for water: `fog = 1-exp(-t*k)` plus `+ smoothstep(500,800,t)*?` Actually just increase k to 0.0065 and also add horizon haze mix by hit distance. Let me set k=0.006: t=425 → 92%. Good enough; plus specular/fog interplay minor there.

One more consideration: the step "t += max(h*0.42, floor)" — h is clearance (p.y − waveH*amp). Use h*0.5 for speed with overshoot risk moderate; bisection fixes crossing. Overshoot beyond a crest into next trough gives wrong intersection (skips crest edge) — visible as crest silhouette flicker. Use factor 0.4 and floor growth moderate: floor = 0.06 + t*0.016 (t=300→4.9; steps from 100→800: sum ≈ 700/avg 9 ≈ 78). Total worst ~ 110 steps fine.

**Bisection:** on h<0 at t with previous tPrev having hPrev>0: 5 iterations halving. That's 5 extra height evals. Cheap enough.

Precision: also check h < eps hit threshold to avoid infinite hugging: treat h<0 as hit (bisect) — fine.

**Water color & lighting details:**

```
// shading at p, t:
float lod = max(2.0, 7.0 - tHit*0.012) + 1.0? normals need more octaves than distance geometry: use lodN = lod + 1.5 for normals.
float eps = max(0.035, tHit*0.008);
vec3 n = waveNormal(p.xz, t, lodN, eps);
// sparkle
float sp = smoothstep(420.0, 60.0, tHit);   // 1 near, 0 far
n.xz += (vec2(vnoise(p.xz*5.0 + t*0.9), vnoise(p.xz*5.0 + 11.7 - t*0.8)) - 0.5) * 0.12 * sp;
n = normalize(n);
```
Hmm t*0.9 on a 5.0-frequency field: advection speed 0.9/5 ≈ fine.

Fresnel:
```
float fres = 0.025 + 0.975*pow(1.0 - clamp(dot(n, -rd), 0.0, 1.0), 5.0);
```
Reflection:
```
vec3 r = reflect(rd, n);
r.y = abs(r.y) + 0.02;? If n tilts a lot at grazing, r.y could go negative → reflecting into water → clamp: r.y = max(r.y, 0.015); r = normalize(r);
vec3 refl = skyColor(r, 3.0);   // cheaper clouds for reflection
```
Base water:
```
float depthMix = clamp(p.y*0.28, 0.0, 1.0);  // crest lighter
vec3 deep = vec3(0.012, 0.05, 0.06);
vec3 sub  = vec3(0.06, 0.28, 0.25);
vec3 waterBase = mix(deep, sub, depthMix*0.6);
// subsurface toward sun through crests
float towardSun = pow(clamp(dot(rd, sunDir), 0.0, 1.0), 3.0);
waterBase += vec3(0.05,0.23,0.18) * towardSun * depthMix * (1.0-fres)*0.8;
```
Ambient/sky irradiance on water: multiply base by sky ambient approx vec3(0.30,0.28,0.30)? Keep simple: waterBase already dark.

Combine:
```
vec3 col = mix(waterBase, refl, fres);
// sun specular
float sd = clamp(dot(r, sunDir), 0.0, 1.0);
float spec = pow(sd, 380.0)*3.0 + pow(sd, 48.0)*0.35;
col += sunTint * spec * (fres*2.0+0.15)? 
```
Hmm — physical-ish: spec already roughly fresnel-shaped due to grazing; scale by 1: col += sunColor * spec. Sun tint (1.0,0.55,0.25)*intensity. To get the classic glitter path, the pow(48) term with noisy normals creates streak. Also add micro-sparkle: use the high-freq jitter in n (already added) so pow(380) gives sparkling dots near path. Clamp col before tonemap? ACES handles HDR.

Sun intensity: disc in sky smoothstep(...)*3*vec3(6,2.6,0.9) → up to (18,7.8,2.7) HDR → ACES tonemaps to near white core with orange rim. 

Foam:
```
float crest = smoothstep(2.35, 3.35, p.y);
float foamNoise = fbm(p.xz*0.6 + windAdv, 3.0);  // advect with waves drift to ride crests? foam should sit on crests which move; crest mask from p.y already moves with waves. Pattern static-ish ok but advect slightly for life.
float foam = crest * smoothstep(0.45, 0.75, foamNoise);
// slope-based streaks
float steep = clamp((1.0 - n.y)*4.0, 0.0, 1.0);
foam += crest*steep*0.5*smoothstep(0.35,0.7, foamNoise2?)...
```
Keep one noise, reuse: foam = crest * (0.55+0.45*foamNoise2) with foamNoise2 = fbm(...*2.0). Also trailing foam streaks in the wash behind crests: approximate with a second mask: smoothstep on p.y lower band (1.4–2.4) * stretched noise (anisotropic: scale p.xz*vec2(0.12, 0.5) rotated along wave dir) — nice touch: `float trail = smoothstep(1.5,2.6,p.y)*smoothstep(0.42,0.8, fbm(rot(p.xz)*vec2(0.08,0.35)...))`. Since waves travel along −d direction, stretch along that dir. Let me implement: 
```
vec2 fd = normalize(vec2(0.95,0.38));  // wave travel dir (features move along -fd)
vec2 st = vec2(dot(p.xz, fd), dot(p.xz, vec2(-fd.y, fd.x)));
float trailN = fbm(vec2(st.x*0.06 - t*0.5?, st.y*0.45), 3.0);
```
Foam trails elongated along travel direction: low frequency along travel axis (st.x), higher across (st.y). Advect: subtract speed along travel: st.x + t*speed... The waves move along −fd at speed |d|*baseFreq? The base domain speed: d = vec2(0.95,0.38)*t*0.45 in units of scaled domain (p*0.045). Feature velocity world = 0.45/0.045 = 10 units/s along −normalize(0.95,0.38). So trail advection: sample at st.x + 10*t? But crest mask p.y already tracks crests, so pattern just needs slow independent drift. I'll not overengineer: foamPattern = fbm(p.xz*0.7 − driftWorld*0.3, 3.0) with driftWorld = −normalize(d)*t*3.0 (slower than waves, foam lags — looks like trailing wash). 

Foam color & light:
```
vec3 foamCol = vec3(0.85, 0.82, 0.78);
float foamLight = clamp(dot(n, sunDir)*0.5+0.5, 0.0, 1.0);
vec3 foamLit = foamCol * (vec3(0.25,0.22,0.20) /*sky ambient*/ + sunTint*foamLight*1.1);
col = mix(col, foamLit, clamp(foam, 0.0, 1.0)*0.9);
// foam kills fresnel reflection partially — mixing after reflection is fine.
```
Also add foam into fog properly: foam computed before fog mix. ✓.

Distance fade of foam: foam pattern noise at t=600 aliases; multiply foam by smoothstep(650, 250, tHit)? Some foam visible at distance adds realism but aliasing... keep fade: foam *= exp(-tHit*0.004) → at 300: 0.30. Hmm that removes most distant foam. Use smoothstep(700,150,t)*0.85+0.15.

Fog:
```
vec3 haze = skyColor(normalize(vec3(rd.x, 0.0, rd.z)), 2.0); // matches sky near horizon
float fog = 1.0 - exp(-tHit*0.0065);
col = mix(col, haze, fog);
```
Note skyColor at exactly y=0 returns gradient+haze mix(...)=haze at y=0 — consistent. But it also includes sun glow terms pow(sd,...) — sun-side horizon glows → fog warmer near sun. 

**Sky detail clouds octaves:** detail=5 near, reflection detail=3, haze detail=2.

Now the sky function with clouds:

```
vec3 skyColor(vec3 rd, float detail){
    float sd = clamp(dot(rd, sunDir), 0.0, 1.0);
    float y = clamp(rd.y, 0.0, 1.0);
    // gradient
    vec3 col = mix(vec3(0.28,0.19,0.16), vec3(0.045,0.07,0.12), pow(y, 0.65));
```
Hmm: at y=0 → warm grey (0.28,0.19,0.16); zenith dark blue. pow(y,0.65) makes warm extend higher. Then azimuthal warmth toward sun: 
```
    col = mix(col, vec3(0.75,0.32,0.12), pow(sd, 3.0)*(1.0-y)*0.8);
```
Glows:
```
    col += vec3(1.0,0.40,0.10)*pow(sd,7.0)*0.6;
    col += vec3(1.2,0.55,0.18)*pow(sd,42.0)*0.9;
```
Sun disc:
```
    float disc = smoothstep(0.9993, 0.99988, sd);
    col += vec3(6.0,2.7,1.0)*disc*2.4;
```
Hmm angular size: cos threshold 0.9993 → 2.1°, 0.99988 → 0.89°. Soft-edged disc radius ~1.5°, low sun → big-looking. Fine.

Clouds (only if rd.y>0.02):
```
    if (rd.y > 0.015) {
        vec2 cuv = rd.xz/(rd.y + 0.14);
        cuv *= 0.35;                       // cloud scale
        float w1 = uTime*0.02; 
        float n1 = fbm(cuv*0.55 + vec2(w1*2.0, w1*0.7) + 3.1, detail);
        float n2 = fbm(cuv*1.5 + vec2(-w1*3.2, w1*1.3) + 11.7, detail*0.7);
        float dens = n1*0.72 + n2*0.45;    // ~0..1.05
        float cov = smoothstep(0.36, 0.74, dens);
        float hi = smoothstep(0.02, 0.14, rd.y);   // horizon fade
        cov *= hi;
        // cloud lighting
        float lit = pow(sd, 3.0)*1.2 + 0.08;
        vec3 cDark = vec3(0.045, 0.05, 0.065);
        vec3 cLit  = vec3(0.85, 0.38, 0.15);
        vec3 cCol = mix(cDark, cLit, clamp(lit,0.0,1.0) * (1.1 - dens*0.85));
        // silver lining: bright rim where dens near threshold toward sun
        cCol += vec3(1.0,0.5,0.2) * pow(sd, 6.0) * smoothstep(0.30,0.55,dens) * (1.0-smoothstep(0.55,0.8,dens)) * 0.8;
        col = mix(col, cCol, cov);
        // sun punch-through: attenuate disc by clouds
        col += vec3(6.0,2.7,1.0)*disc*2.4 * (-cov*0.75);  // re-add subtracted? 
```
Simpler: compute disc add AFTER cloud mix, scaled by (1 − cov*0.8):
Restructure: compute base gradient + glows; compute clouds into cCol/cov; mix gradient with clouds; then add disc*(1−cov*0.85) and partial glow*(1−cov*0.5). Let me finalize:

```
vec3 skyColor(vec3 rd, float detail){
    float sd = clamp(dot(rd, sunDir), 0.0, 1.0);
    float y = clamp(rd.y, 0.0, 1.0);
    vec3 col = mix(vec3(0.30,0.20,0.16), vec3(0.043,0.068,0.115), pow(y,0.6));
    col += vec3(0.95,0.36,0.10)*pow(sd,4.0)*(1.0 - y*0.5)*0.55;
    col += vec3(1.15,0.50,0.16)*pow(sd,30.0)*0.85;
    float disc = smoothstep(0.99935, 0.99990, sd);
    float cov = 0.0;
    float dens = 0.0;
    if (rd.y > 0.012) {
        vec2 cuv = rd.xz/(rd.y+0.14)*0.5;
        float tm = uTime;
        float n1 = fbm(cuv + vec2(tm*0.030, tm*0.011) + 3.1, detail);
        float n2 = fbm(cuv*2.3 + vec2(-tm*0.047, tm*0.019) + 17.7, detail*0.75);
        dens = n1*0.70 + n2*0.45;
        cov = smoothstep(0.35, 0.72, dens) * smoothstep(0.012, 0.10, rd.y);
        float lit = clamp(0.10 + pow(sd,3.0)*1.3, 0.0, 1.0);
        vec3 cCol = mix(vec3(0.040,0.047,0.062), vec3(0.90,0.38,0.15), lit*(1.15-dens));
        cCol += vec3(1.0,0.48,0.18) * pow(sd,5.0) * smoothstep(0.28,0.52,dens)*(1.0-smoothstep(0.52,0.78,dens)) * 0.9;
        col = mix(col, cCol, clamp(cov,0.0,1.0));
    }
    col += vec3(6.5,2.8,1.05) * disc * (1.0 - cov*0.85) * 2.6;
    col += vec3(1.2,0.5,0.18) * pow(sd,60.0) * (1.0 - cov*0.6) * 1.2;
    // haze near horizon (storm atmosphere)
    vec3 hdir = normalize(vec3(rd.x, 0.0, rd.z));
    float hd = clamp(dot(hdir, sunAz), 0.0, 1.0);
    vec3 haze = mix(vec3(0.30,0.21,0.17), vec3(1.05,0.48,0.20), pow(hd,3.0)*0.85);
    col = mix(col, haze, smoothstep(0.16, 0.0, y)*0.85);
    return col;
}
```
Wait — when y=0 the function returns ≈haze — used as fog color; consistent. But note `mix(col, haze, smoothstep(0.16,0,y)*0.85)`: at y=0, col→85% haze + 15% gradient(0.30,...)... slight mismatch with fog color (haze exactly). Minor: fogged water mixes toward `haze` while sky at y=0+ is 0.85haze+0.15grad → nearly same since gradient horizon ≈ haze base color (0.30,0.20,0.16 vs haze away (0.30,0.21,0.17) — basically equal!). And sun-side: gradient+glow vs haze(1.05,0.48,0.2): glow pow(sd,4)*(1−y)*0.55 at y=0 gives warm boost too. Close enough; seams will be invisible under motion. Good.

sunAz = normalize(vec3(sunDir.x, 0.0, sunDir.z)).

Reflection calls skyColor(r, 2.5) — includes clouds at reduced detail ✓.

**Wave amplitude & world scale:** waveH returns 0..~2.0 in "heightfield units"; world H = waveH*AMP with AMP=1.8. So normal calc: dH/dx = AMP * dRidge/dx.

Hold on — inside waveH I do `p = pos*0.045` etc.; return ridge sum (0..2.04). World: H(p) = AMP * waveH(p, t, lod). Fine.

Camera ride uses H at cam: waveH(...)*AMP.

Crest threshold for foam: H > ~2.3 world → waveH > 1.28. smoothstep(2.35, 3.30, pH.y).

**Let me also double check the ridged shape:** n∈[0,1] mean 0.5; ridge = 1−|2n−1| → mean 0.5, peaks 1 where n=0.5 crossing — crests are contour lines of noise → wavy banded crests. Squared: sharper. Sum over rotated octaves → organic. The field's crests will look like connected banded ridges — with rotation between octaves and domain warp, looks like ocean swell. I think with the warp it'll read as ocean. Also adding slight bias: h += ridge − 0.45 to center? For shading, absolute height matters (foam thresholds) — keep as is and tune thresholds.

Actually, one more consideration: pure `1−|2n−1|` squared ridged fbm tends to make round-blob crests; classic ocean look benefits from a steeper "choppy" profile. Alternative shaping used in many demos: 
```
float n = vnoise(p+d);
float w = 1.0 - abs(2.0*n - 1.0);   // triangle
w = smoothstep(0.0, 1.0, w);? 
h += (w*w*w) * a;
```
Cubic sharpens more. I'll use w = 1−abs(2n−1); w = w*w*(3−2w)? That smooths the peak (opposite). Let me use pow: ridge^2.2? GLSL pow fine: w*w (square) — I'll use square plus slight overall sharpening of the sum via `h = h*AMP` and foam thresholds. Also add a small negative bias per octave to make valleys broader: h += (ridge − 0.35)*a*fade with clamped a normalization — this creates flatter troughs, pointier crests. Sum mean shifts down; amplitude similar. Let me define:

```
float c = 1.0 - abs(n*2.0 - 1.0);   // 0..1
c = c*c;                             // sharpen
h += (c - 0.30) * a;                 // bias down: broader troughs
```
Max sum ≈ (1−0.30)*(1+0.52+0.27+0.14+0.073+0.038)= 0.70*2.04 ≈ 1.43; min ≈ −0.30*2.04 = −0.61. World (AMP 2.1): max 3.0, min −1.28, mean ~0.1? mean of c ~ (mean of 1−|2n−1| with n~uniform-ish 0.5) = 0.5 → 0.2*2.04*2.1 ≈ 0.86 mean world height. Hmm fine — camera at 4.7±, clearance ~3.5 typical. Foam threshold: crests > 2.2 world. Let me set AMP=2.2, foam smoothstep(2.15, 3.0, p.y)? Max 3.0 — foam only at very peaks. Let me compute worst-case sum more carefully: octaves a: 1, .52, .27, .14, .073, .038 (gain .52). Sum=2.04. Max h = .70*2.04 = 1.43 → world 3.15 (AMP 2.2). Peaks realistically ~2.6–3.0 world. Foam threshold smoothstep(2.0, 2.9, y) → foam appears on top ~30% of crests, broken by pattern noise. Good.

Camera: ro.y = 4.6 + ride*0.25 + heave(±0.28). ride = H_cam = waveH*AMP ∈ [−1.3, 3.15]. ride*0.25 ∈ [−0.33, 0.79]. camY ∈ [4.04, 5.67]. Max wave 3.15 → min clearance 0.89 when camera in trough while max crest nearby. OK.

Wait, heave ±0.28: heave = 0.16*sin(t*1.35) + 0.12*sin(t*2.17+1.4). Fine.

**Trace function:**

```
float traceWater(vec3 ro, vec3 rd, float tmax){
    if (rd.y > -0.001) return -1.0;   // camera always above max wave
    float t = 0.0;
    float tPrev = 0.0;
    float hPrev = ro.y - Hcam? 
```
Simple loop:

```
    float floor_ = 0.0;
    for (int i = 0; i < 110; i++){
        float t = ...
```
Implement:

```
float traceWater(vec3 ro, vec3 rd){
    const float TMAX = 800.0;
    if (rd.y > -0.0015) return -1.0;
    float t = 0.02;
    float lod0 = max(2.0, 7.0 - t*0.012); // evaluated per step
    for (int i = 0; i < 120; i++){
        vec3 p = ro + rd*t;
        float lod = max(2.0, 6.5 - t*0.011);
        float h = p.y - waveH(p.xz, uTime, lod)*AMP;
        if (h < 0.0){
            // bisect between tPrev and t
            float a = tPrev, b = t;
            for (int j = 0; j < 5; j++){
                float m = 0.5*(a+b);
                vec3 pm = ro + rd*m;
                float hm = pm.y - waveH(pm.xz, uTime, max(2.0,6.5-m*0.011))*AMP;
                if (hm < 0.0) b = m; else a = m;
            }
            return 0.5*(a+b);
        }
        tPrev = t;
        float step_ = max(h*0.42, 0.05 + t*0.012);
        t += step_;
        if (t > TMAX) return -1.0;
    }
    return -1.0;
}
```
Note at i=0, tPrev=0, t=0.02: p≈ro, h≈ro.y−H(cam) >0 typically (clearance). Fine.

Edge: if initial h<0 (camera below surface — shouldn't happen), bisection with a=0 gives t≈0.01 → screen = water at infinitesimal distance — glitch but bounded. Skip worry.

Cost: 120 iterations max with 6-octave (early break at lod 2 → 2-3 octaves at distance) — distance steps cheap. Near steps: lod 6 → 6 vnoise = 24 hashes per eval; ~20–40 evals near field → ~1000 hash ops/pixel worst. At 1080p×~1.5 dpr... could be heavy on weak GPUs but adaptive res helps. Also I can lower MARCH lod cap: lod = max(2.0, 5.5 − t*0.012) → full 5 octaves only within t<50. Let me use 6 octaves defined in loop but cap lod so octaves 4-5 only near: lod max 5.5. Actually my waveH loop is `i<6`; pass lod ≤ 5.5 → effectively 5 octaves + partial 6th? fade for i=5: lod−5 ∈ [0,0.5]. OK: lod = clamp(6.0 − t*0.012, 2.0, 6.0)? At t=0 → 6 (all). t=100 → 4.8, t=200 → 3.6, t=333 → 2. Fine — geometry detail fades smoothly; normals use lod+1.0 capped 6.

Hmm, one subtlety: LOD varying per sample along the ray + bisection mixing lods — fine, continuous function of t.

But LOD varying with t creates surfaces whose height changes with distance → the raymarch sees slightly different field at different t — can cause minor stepping artifacts but universally used; ok.

**Vertex shader:**

```
#version 300 es
void main(){
    vec2 v = vec2[3](vec2(-1.0,-1.0), vec2(3.0,-1.0), vec2(-1.0,3.0))[gl_VertexID];
    gl_Position = vec4(v, 0.0, 1.0);
}
```
Hmm — indexing a const array constructor by gl_VertexID: allowed in GLSL ES 3.0? Dynamic indexing of an array constructor... safer:
```
const vec2 verts[3] = vec2[3](...);
...
vec2 v = verts[gl_VertexID];
```
Dynamic index on local const array is fine in ES 3.0 (dynamic indexing supported for arrays in ES3, except samplers). OK.

**JS details:**

```js
(async? no) 
const canvas = ...; 
const gl = canvas.getContext('webgl2', {antialias:false, alpha:false, depth:false, stencil:false, powerPreference:'high-performance'});
if (!gl) { fallback message div; }
compile shaders, program, check compile/link logs → console.error + on-page message.
uniform locations.
resize():
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const scale = dpr * resScale;  // resScale adaptive
  const w = Math.max(1, Math.round(innerWidth * scale));
  const h = ...
  if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; gl.viewport(0,0,w,h); }
canvas CSS: width:100vw;height:100vh (also 100dvh for mobile? use height:100% with html,body{height:100%}). Set style via CSS.
addEventListener('resize', resize);
frame(ts):
  if (t0 < 0) t0 = ts;
  const time = (ts - t0)/1000;
  adapt: accumulate dt via ts diff; every 45 frames evaluate avg; adjust resScale between 0.5 and 1.0 (steps of 0.1).
  resize() each frame? Cheaper: call resize on 'resize' event only, but resScale changes need re-resize → call resize() when resScale changes. Also devicePixelRatio changes on zoom → 'resize' fires on zoom typically. Also check each frame cheaply: compare canvas.clientWidth... I'll call resize() every frame but early-out unless dims changed — trivial cost.
  gl.uniform1f(uTime, time); gl.uniform2f(uRes, canvas.width, canvas.height);
  drawArrays(TRIANGLES,0,3);
  rAF.
```

Adaptive resolution: base dpr clamp 2. resScale start 1.0. Frame time smoothing: ema = ema*0.9 + dt*0.1 (dt from rAF ts). Every 50 frames: if ema > 24ms and resScale > 0.55 → resScale −= 0.15; if ema < 13ms and resScale < 1.0 → resScale += 0.1 (careful oscillation: increase less aggressively, add hysteresis via cooldown 120 frames after change). Simple enough.

Also pause when tab hidden: rAF auto-pauses. Fine.

Context loss:
```
canvas.addEventListener('webglcontextlost', e => { e.preventDefault(); });
canvas.addEventListener('webglcontextrestored', () => initGL()); 
```
Requires factoring init. I'll structure init() function that compiles and sets up; on restore call init again. Keep modest.

**Loading/failure UI:** minimal centered message if WebGL2 unavailable; styled dark. Also the page needs no chrome: body margin 0, overflow hidden, canvas display:block.

Title: "Stormwater — Sunset Ocean" or similar.

**Let me now also double-check the water shading math for the sun glitter path direction.** Sun azimuth AZ: sunDir = normalize(vec3(sin(AZ), tan? Let me define el variable: 
```
float el = 0.075 + 0.05*sin(uTime*0.05 + 0.6);   // period 125.7s; at t=0: 0.075+0.05*sin(0.6)=0.075+0.0282=0.103; at t=31: 0.075+0.05*sin(1.55+0.6)=0.075+0.05*sin(2.15)=0.075+0.0415=0.1165... hmm not a big swing. Let me use phase so that min at t≈0 and max at t≈31: sin from −π/2 to +π/2 over 31s → phase = t*(π/31) − π/2 → at t=0: −1 → el = base + amp*(−1); t=31.4: +1. So el = 0.09 + 0.045*sin(t*0.1 − 1.57). At t=0: 0.045; t=31: 0.135. Sun visibly climbs from near-touching horizon to a low sun — dramatic within 30s ✓. Then continues to descend after (period 62.8s). 
vec3 sunDir = normalize(vec3(0.26, el, -1.0));
```
With el 0.045→0.135 (≈2.6°→7.7°) — nice range. At el=0.045 sun disc center slightly above horizon; disc radius ~1° → bottom edge may dip below horizon line → looks like sun sitting on water. 

Camera forward yaw should aim at sun azimuth: AZ = atan2(0.26, 1.0)? sunDir xz = (0.26, −1)/len. yaw = atan(0.26/1) ≈ 0.255. forward = vec3(sin(yaw), 0, −cos(yaw)) matches direction (0.253, 0, −0.967) ✓.

**Normal detail & spec aliasing:** at far distances, high-freq normal jitter fades (sp factor). Specular pow(380) with far normals → horizon glitter band: sun path should extend to horizon — glitter comes from geometry normals (lod-faded) — the low-freq distant water still has normals from 2 octaves → gentle broad path + near sparkles. Also add mild distance-independent fine bump via a small noise-based perturbation that fades slower (exp(-t*0.004)). Tune: sparkle amplitude 0.10 * smoothstep(500,80,t)? Let me do `float nearFade = smoothstep(600.0, 120.0, tHit);` amplitude 0.12*nearFade + 0.02.

**Tonemapping & exposure:** exposure ~1.0; ACES fit.

Also vignette subtle: `col *= 1.0 - 0.25*pow(length(uvNorm),2.5)`? uv normalized by uRes.y: length(uv) at corners ~ (aspect/1, 1)... vignette = smooth. Add mild: `col *= 1.0 - 0.18*dot(uv*0.55, uv*0.55);` cheap and tasteful. Hmm keep subtle 0.15.

Water at bottom of frame: t small (~1–3) → eps small → high detail ✓.

**One more check — sky for rd.y<0 (below horizon):** rays that miss water with rd.y<0 exist (grazing) → skyColor with y clamped 0 → haze; sun glow pow(sd,…) at grazing below horizon: sun disc visible slightly below horizon line?? Rays with rd.y<0 that miss water render sky including disc → sun reflecting below horizon — but sun is at el 0.045 with disc ±~0.9°... rays below horizon pointing at disc region: dot(rd,sunDir)≥0.99935 requires rd.y ≥ el − ~0.017 → with el=0.045, rd.y ≥ 0.028 > 0 → such rays go UP → they hit sky anyway (rd.y>0 → no water). Wait but rd.y > −0.0015 → trace returns −1 → sky. Rays with rd.y∈(−0.0015, 0) → sky path → glow terms tiny there. So no artifact: the disc only appears for rd.y>0.028. But hold on — trace early-out is `rd.y > -0.0015 return -1` — rays with rd.y = −0.001 march to TMAX=800 without hitting (descent 0.8 < min cam−maxwave 0.9)... They exhaust 120 steps? floor at t=800: 0.05+9.6=9.65/step; from 0→800 with growing floor: rough integral ~ (800)/avg(4) ≈ 200 steps > 120 → returns −1 without hitting → sky. OK consistent — such rays are within a hair of horizon; haze covers.

Actually let me reconsider TMAX and fog: rays with rd.y=−0.01: descent by t=800: 8 → hits around t≈450 (descent 4.5 ≥ cam−wave ~3.4). Fog at 450: 1−exp(−0.0065*450)=0.946. Distant water = 95% haze. Slight water tone remains — good, gives depth gradient. Rays rd.y=−0.03: hit t≈150 → fog 0.62. Nice gradient to horizon ✓.

The visible horizon line will be where water silhouette (lod-flattened waves at t 300–500, mostly fogged) meets sky haze. Because fog color == haze == skyColor(horizontal), the seam should be soft. There may be a subtle darkening band right at horizon from water base color residual — acceptable, looks like distant storm squall. Could even enhance: add horizon darkening band in sky: mix haze with slightly darker grey-blue in a band y∈[0,0.05]? The ocean distance haze typically lighter. Skip.

**Foam in reflections?** No — reflection is sky only. Fine.

**Sun glitter on water toward camera:** with sun ahead (azimuth ≈ camera forward), the specular path runs from horizon toward camera — classic. ✓

**Now write the final code.** I'll be careful with GLSL ES 3.00 syntax: `#version 300 es` must be first line — in JS template literal, ensure no leading newline. Use `out vec4 fragColor;` and `gl_FragCoord`. Loops with const bounds; dynamic `break` allowed.

Let me also add `uSun` as computed in shader from uTime — fine.

Also worth adding slight camera height-based near-clip: start t at 0.05 to avoid immediate self-hit.

Water shading function inline in main for clarity.

Let me write out everything and sanity check syntax mentally.

Fragment shader draft (final):

```glsl
#version 300 es
precision highp float;

uniform float uTime;
uniform vec2  uRes;
out vec4 fragColor;

const float PI = 3.141592653589793;
const float AMP = 2.2;          // wave amplitude (world units)
const float TMAX = 800.0;

float hash12(vec2 p){
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

float vnoise(vec2 p){
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f*f*f*(f*(f*6.0-15.0)+10.0);
    float a = hash12(i);
    float b = hash12(i + vec2(1.0, 0.0));
    float c = hash12(i + vec2(0.0, 1.0));
    float d = hash12(i + vec2(1.0, 1.0));
    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

const mat2 M2 = mat2(1.68, 1.18, -1.18, 1.68); // rotate + lacunarity ~2.05

float fbm(vec2 p, float detail){
    float v = 0.0;
    float a = 0.5;
    for (int i = 0; i < 5; i++){
        float fade = clamp(detail - float(i), 0.0, 1.0);
        if (fade < 0.003) break;
        v += a * vnoise(p) * fade;
        p = M2 * p;
        a *= 0.55;
    }
    return v;
}

// ridged, advected ocean heightfield (world height = AMP * result)
float waveField(vec2 pos, float t, float lod){
    vec2 p = pos * 0.045;
    vec2 warp = vec2(
        vnoise(p * 0.8 + vec2( t*0.110, -t*0.073)),
        vnoise(p * 0.8 + vec2(-t*0.092,  t*0.131) + 5.2)
    );
    p += (warp - 0.5) * 0.9;
    vec2 d = vec2(0.95, 0.38) * (t * 0.45);
    float h = 0.0;
    float a = 1.0;
    for (int i = 0; i < 6; i++){
        float fade = clamp(lod - float(i), 0.0, 1.0);
        if (fade < 0.003) break;
        float n = vnoise(p + d);
        float c = 1.0 - abs(n * 2.0 - 1.0);
        c *= c;
        h += (c - 0.30) * a * fade;
        p = M2 * p;
        d = M2 * d;
        a *= 0.52;
    }
    return h;
}
```

Wait — warp time frequencies: t*0.11 in domain p (already scaled ×0.045): warp noise coordinates ~p*0.8 where p∈world*0.045 → warp field wavelength ≈ 1/(0.8*0.045) ≈ 28 world units; time drift 0.11/s → slow morphing ✓.

d = baseDrift * t where baseDrift=(0.95,0.38)*0.45? I wrote d = vec2(0.95,0.38)*(t*0.45) → per octave multiplied by M2 each iteration: consistent advection. Feature speed in world: derivative of pattern position: sampling vnoise(p0 + d(t)) → features move at −dd/dt in scaled domain = −(0.95,0.38)*0.45 per second in scaled units → world speed = 0.45*|(.95,.38)|/0.045 = 0.45*1.023/0.045 ≈ 10.2 units/s. Wavelength ~22 units → period ~2.2s per wave passing. Reasonable rolling.

Hmm 10 units/s might feel fast-ish but with 22-unit swell that's stately. OK.

Normal:

```
vec3 waveNormal(vec2 p, float t, float lod, float eps){
    float h = waveField(p, t, lod);
    float hx = waveField(p + vec2(eps, 0.0), t, lod);
    float hz = waveField(p + vec2(0.0, eps), t, lod);
    return normalize(vec3(-(hx - h), 1.0, -(hz - h)) * (AMP / eps) ... 
```
careful: normal = normalize(vec3(-AMP*(hx-h)/eps, 1.0, -AMP*(hz-h)/eps)). But magnitude: (hx−h) over eps could be ~0.3/0.05=6 × AMP 2.2 = 13 → steep normals fine.

Actually wait: waveField is smooth (quintic interp), slopes moderate. Fine.

Trace:

```
float traceWater(vec3 ro, vec3 rd){
    if (rd.y > -0.0015) return -1.0;
    float t = 0.05;
    float tp = 0.0;
    for (int i = 0; i < 120; i++){
        vec3 p = ro + rd * t;
        float lod = clamp(6.0 - t * 0.012, 2.0, 6.0);
        float h = p.y - waveField(p.xz, uTime, lod) * AMP;
        if (h < 0.0){
            float a = tp;
            float b = t;
            for (int j = 0; j < 5; j++){
                float m = 0.5 * (a + b);
                vec3 q = ro + rd * m;
                float hm = q.y - waveField(q.xz, uTime, clamp(6.0 - m*0.012, 2.0, 6.0)) * AMP;
                if (hm < 0.0) b = m; else a = m;
            }
            return 0.5*(a + b);
        }
        tp = t;
        t += max(h * 0.42, 0.05 + t * 0.012);
        if (t > TMAX) return -1.0;
    }
    return -1.0;
}
```

Sky: as drafted. Need sunDir computed once per frame in main and... functions can't access uTime? They can — uniforms are global. But sunDir varies; compute inside functions? I'll compute sunDir in main and pass to functions, or recompute in each (cheap normalize). To keep signatures light, compute globally: GLSL allows global non-const initialized with uniforms? Global variables must be initialized with constant expressions in ES. So define function:

```
vec3 sunDirection(){
    float el = 0.09 + 0.045 * sin(uTime * 0.10 - 1.57);
```
Wait earlier: phase = t*0.10 − 1.57 → at t=31.4: 1.57 ✓ peak. Period 62.8s. el = 0.09 + 0.045*sin(...) → t=0: 0.045, t=31.4: 0.135. ✓
```
    return normalize(vec3(0.26, el, -1.0));
}
```
And `vec3 sunAz = normalize(vec3(sunDirection().x, 0.0, sunDirection().z))` — compute per use.

Cloud/sky:

```
vec3 skyColor(vec3 rd, float detail){
    vec3 sun = sunDirection();
    float sd = clamp(dot(rd, sun), 0.0, 1.0);
    float y = clamp(rd.y, 0.0, 1.0);

    vec3 col = mix(vec3(0.30, 0.205, 0.165), vec3(0.040, 0.066, 0.112), pow(y, 0.62));
    col += vec3(0.95, 0.34, 0.09) * pow(sd, 4.0)  * (1.0 - y * 0.55) * 0.55;
    col += vec3(1.15, 0.50, 0.16) * pow(sd, 28.0) * 0.85;

    float disc = smoothstep(0.99930, 0.99990, sd);
    float cov = 0.0;
    if (rd.y > 0.012){
        vec2 cuv = rd.xz / (rd.y + 0.14) * 0.5;
        float tm = uTime;
        float n1 = fbm(cuv * 0.85 + vec2( tm*0.028,  tm*0.010) + 3.1, detail);
        float n2 = fbm(cuv * 2.1 + vec2(-tm*0.043,  tm*0.017) + 17.7, detail * 0.75);
        float dens = n1 * 0.72 + n2 * 0.45;
        cov = smoothstep(0.36, 0.74, dens) * smoothstep(0.012, 0.16, y);
        float lit = clamp(0.10 + pow(sd, 3.0) * 1.4, 0.0, 1.0);
        vec3 cCol = mix(vec3(0.043, 0.050, 0.066), vec3(0.90, 0.36, 0.13), lit * clamp(1.15 - dens, 0.0, 1.0));
        cCol += vec3(1.0, 0.46, 0.16) * pow(sd, 5.0) * smoothstep(0.30, 0.52, dens) * (1.0 - smoothstep(0.52, 0.78, dens)) * 0.9;
        col = mix(col, cCol, cov);
    }
    col += vec3(6.5, 2.7, 0.95) * disc * (1.0 - cov * 0.85) * 2.6;
    col += vec3(1.1, 0.48, 0.16) * pow(sd, 60.0) * (1.0 - cov * 0.6);

    // horizon haze
    vec2 hxz = rd.xz; float hl = length(hxz)...
    vec3 hdir = vec3(rd.x, 0.0, rd.z) / max(length(rd.xz), 1e-4);
    float hd = clamp(dot(hdir, normalize(vec3(sun.x, 0.0, sun.z))), 0.0, 1.0);
    vec3 haze = mix(vec3(0.30, 0.21, 0.17), vec3(1.05, 0.46, 0.18), pow(hd, 3.0) * 0.9);
    col = mix(col, haze, smoothstep(0.18, 0.0, y) * 0.9);
    return col;
}
```
Note: the haze mix at y=0 gives col ≈ 0.9*haze + 0.1*(gradient+glow). Water fog uses `haze` directly computed the same way — I'll make a helper `horizonHaze(vec3 rd)` returning the haze vec3, used both in skyColor and water fog, ensuring exact match at y→0... but skyColor at y=0 returns mix 90% haze + 10% rest where rest at y=0: gradient = (0.30,0.205,0.165)+glow terms. Haze away-from-sun = (0.30,0.21,0.17). 10% difference of nearly identical colors → invisible. Good.

For water fog I'll call `skyColor(vec3(hdir…,0.018), 1.5)`? That evaluates glow at grazing including pow(sd,60) etc. — gives sun-direction warm fog ✓ and matches the y→0 sky above. Cost fine. Actually simpler and exactly consistent: fogColor = skyColor(normalize(vec3(rd.x, 0.02, rd.z)), 1.0). At y=0.02 the haze mix factor = smoothstep(0.18,0,0.02)= (0.18−0.02)/0.18=0.888 → ~0.89. And sky just above horizon at y=0.02 renders identically → water fogged to exactly the sky color at the same altitude → seamless horizon. Use detail 1.0 for cheap (clouds still computed? rd.y>0.012 → yes cloud branch runs with detail 1 → 1 octave fbm ×2 ≈ cheap). Good — reflection also uses skyColor with rd.y possibly small → fine.

But careful: reflection ray with r.y up to 1.0 → clouds at high detail... pass detail 2.5 for reflections.

Water shading in main:

```
float tHit = traceWater(ro, rd);
vec3 col;
if (tHit < 0.0){
    col = skyColor(rd, 5.0);
} else {
    vec3 p = ro + rd * tHit;
    float lodN = clamp(7.0 - tHit * 0.010, 3.0, 7.0);
    float eps = max(0.04, tHit * 0.008);
    vec3 n = waveNormal(p.xz, uTime, lodN, eps);
    float sparkle = smoothstep(500.0, 60.0, tHit);
    n.xz += (vec2(vnoise(p.xz * 5.0 + uTime * 0.9),
                  vnoise(p.xz * 5.0 + 13.7 - uTime * 0.8)) - 0.5) * (0.10 + 0.06 * sparkle);
```
Hmm — base jitter 0.10 everywhere even far → aliasing at horizon. Make amplitude = 0.12*sparkle + 0.02. Let me: amp = 0.02 + 0.10*sparkle.

Wait also the high-freq jitter vnoise(p*5) at t=400: p.xz spans large; frequency 5 in world → per-pixel footprint at 400 units is huge (pixel covers ~0.5+ units at 400 with fov) → sampling noise at freq 5/0.5 = 10× per pixel → aliasing sparkle shimmer. Fade by distance handles it (sparkle→0 at 500). At t=100: footprint ~0.15 → freq 5 → 0.75 cell/pixel — borderline ok.

Continue:

```
    n = normalize(n);
    float cosT = clamp(dot(n, -rd), 0.0, 1.0);
    float fres = 0.022 + 0.978 * pow(1.0 - cosT, 5.0);

    vec3 r = reflect(rd, n);
    r.y = abs(r.y) * 0.98 + 0.02;   // keep above surface
    r = normalize(r);
    vec3 refl = skyColor(r, 2.5);

    // water body
    float crest01 = clamp(p.y / 3.0, 0.0, 1.0);
    vec3 deep = vec3(0.012, 0.055, 0.062);
    vec3 shal = vec3(0.045, 0.21, 0.20);
    vec3 body = mix(deep, shal, crest01 * 0.55);
    float towardSun = pow(clamp(dot(rd, sunDirection()), 0.0, 1.0), 3.0);
    body += vec3(0.03, 0.16, 0.13) * towardSun * crest01 * (1.0 - fres);

    col = mix(body, refl, fres);

    // sun specular
    vec3 sun = sunDirection();
    float rs = clamp(dot(r, sun), 0.0, 1.0);
    float spec = pow(rs, 340.0) * 2.6 + pow(rs, 36.0) * 0.30;
    col += vec3(1.25, 0.55, 0.22) * spec * (0.35 + 0.65 * fres);
```
Hmm the (0.35+0.65fres) scaling — at near water looking down, fres small → spec dim ✓; grazing → strong ✓.

```
    // foam
    float fpat = fbm(p.xz * 0.55 + driftOffset, 3.0);
```
driftOffset: foam slowly advected opposite-ish: `vec2 foamAdv = vec2(-0.95, -0.38) * (uTime * 0.35);` (slow drift).

```
    float crest = smoothstep(2.05, 2.95, p.y);
    float foam = crest * smoothstep(0.42, 0.78, fpat * 0.85 + 0.25 * crest);
```
Hmm simpler: foam = crest * smoothstep(0.40, 0.75, fpat). Since fpat∈~[0.1,0.9]: foam covers ~40% of crest area in patches ✓.

Add streaky trail foam:
```
    vec2 fd = normalize(vec2(0.95, 0.38));       // wave travel axis
    vec2 st = vec2(dot(p.xz, fd), dot(p.xz, vec2(-fd.y, fd.x)));
    float trailN = fbm(vec2(st.x * 0.055 + uTime * 0.35, st.y * 0.42) + 4.7, 3.0);
```
Wait: features move along −fd; foam trail behind crest also moves along −fd → advect st.x by +uTime*speed? Sampling fbm(vec2(st.x + uTime*0.5, …)): pattern moves −x direction along fd... waves move along −(0.95,0.38)... st.x is coordinate along fd; pattern should translate along −fd → sample coordinate st.x − velocity? vnoise(p + d) moves features −d. To move trail along −fd (same as waves): add +d in sample: st.x*scale + t*speed. d positive → features move −fd ✓. Speed: trail slower than waves (10 u/s): 3.5 u/s → st.x*0.055 + t*0.19? In fbm domain: velocity in domain = speed*0.055 = 0.19/s → sample offset t*0.19. Let me write `st.x * 0.055 + uTime * 0.19`.

Trail mask: just behind crests: heights slightly below crest: smoothstep(1.2, 2.2, p.y) * (1−crest)? Foam trail exists on the back slope which is lower than crest: mask = smoothstep(1.1, 2.1, p.y) — includes crest region too, fine, multiply streaky noise:

```
    float trail = smoothstep(1.15, 2.15, p.y) * smoothstep(0.48, 0.80, trailN) * 0.7;
    foam = clamp(foam + trail, 0.0, 1.0);
    foam *= smoothstep(700.0, 150.0, tHit) * 0.85 + 0.15;   // fade distant foam
```
Hmm — distant foam fade: keep some: `* (0.2 + 0.8*smoothstep(650.0, 120.0, tHit))`.

Foam lighting:
```
    vec3 foamCol = vec3(0.92, 0.87, 0.80);
    float nl = clamp(dot(n, sun) * 0.6 + 0.4, 0.0, 1.0);
    vec3 foamLit = foamCol * (vec3(0.22, 0.20, 0.19) + vec3(1.15, 0.62, 0.30) * nl * 1.1);
    col = mix(col, foamLit, foam * 0.85);
```

Fog:
```
    vec3 fdir = normalize(vec3(rd.x, 0.02, rd.z));
    vec3 hazeC = skyColor(fdir, 1.0);
    float fog = 1.0 - exp(-tHit * 0.0062);
    col = mix(col, hazeC, fog);
```
Wait — spec added before fog gets fogged too ✓ correct physically.

Also darken deep shadow side slightly for drama — skip.

Sky pixels: also add subtle stars? No — sunset.

Tonemap:
```
    col *= 1.05;   // exposure
    // subtle vignette
    vec2 vuv = (gl_FragCoord.xy / uRes - 0.5);
    col *= 1.0 - 0.22 * dot(vuv, vuv) * 1.6;
```
Hmm vignette 0.22*1.6*0.5(max dot at corner: vuv=(±0.5·aspect?...) vuv normalized by uRes so corners (0.5, 0.5) → dot=0.5 → 1−0.176. fine.

ACES:
```
    col = aces(col);
    col = pow(col, vec3(1.0/2.2));
    fragColor = vec4(col, 1.0);
```
Wait ACES fit (Narkowitz) output is linear-ish [0,1] designed to then be gamma'd. Yes apply gamma after. Common usage applies it directly as final color without gamma too... Narkowitz ACES maps linear → display by including the RRT+ODT tone curve which outputs display-referred linear; conventionally you still apply sRGB gamma. Most shadertoy usages do `pow(aces(col), vec3(1/2.2))`? Actually Narkowitz's post says "tonemapping transform... output needs gamma"? The fit approximates the RRT+ODT which in ACES pipeline outputs linear then RRT... ugh. Practically: col=aces(col*exposure); col=pow(col,1/2.2) looks good with properly-scaled inputs. Many use without gamma and it looks washed... I'll go with gamma after ACES; tune exposure ~1.0–1.3. Given HDR sun values ~15 → aces → ~0.95; whites fine. Mid-tones: sky horizon 0.3 → aces(0.3)= (0.3*(2.51*0.3+0.03))/(0.3*(2.43*0.3+0.59)+0.14) = (0.3*0.783)/(0.3*1.319+0.14)=0.2349/0.5357=0.438 → gamma → 0.68. Reasonable brightness. Deep water 0.02→ aces≈0.028 → gamma 0.19. OK dark. Exposure 1.3 maybe. I'll set exposure 1.25 and multiply sky slightly.

**Camera bob code in main:**

```
    float tm = uTime;
    vec2 camXZ = vec2(1.8 * sin(tm * 0.071), 1.4 * sin(tm * 0.053 + 2.0));
    float ride = waveField(camXZ, tm, 2.0) * AMP;
    float heave = 0.16 * sin(tm * 1.31) + 0.10 * sin(tm * 2.17 + 1.4);
    vec3 ro = vec3(camXZ.x, 4.55 + ride * 0.26 + heave, camXZ.y);
    float yaw   = 0.255 + 0.045 * sin(tm * 0.21) + 0.018 * sin(tm * 0.43 + 1.0);
    float pitch = -0.105 + 0.028 * sin(tm * 0.83 + 0.5) + 0.014 * sin(tm * 1.57);
    float roll  = 0.055 * sin(tm * 0.61 + 0.7) + 0.02 * sin(tm * 1.13);
```
Note roll sign convention: rotate up/right around forward.

```
    float cy = cos(pitch), sy = sin(pitch);
    vec3 fw = vec3(sin(yaw) * cy, sy, -cos(yaw) * cy);
    vec3 rt0 = normalize(cross(fw, vec3(0.0, 1.0, 0.0)));
    vec3 up0 = cross(rt0, fw);
    float cr = cos(roll), sr = sin(roll);
    vec3 rt = cr * rt0 + sr * up0;
    vec3 up = -sr * rt0 + cr * up0;
    vec2 uv = (2.0 * gl_FragCoord.xy - uRes) / uRes.y;
    vec3 rd = normalize(uv.x * rt + uv.y * up + 1.35 * fw);
```

Sanity: cross(fw, up_world) with fw=(sin y,0,−cos y): (sy,0,−cy)×(0,1,0) = (0*0−(−cy)*1, (−cy)*0−sy*0, sy*1−0) = (cy, 0, sy) → normalize → (cos yaw... wait sin(yaw)=sy? I named sy = sin(pitch) — collision of names. Rename: cp/sp for pitch, and use sin(yaw) inline. Let me rename: 

```
    float cp = cos(pitch), sp = sin(pitch);
    vec3 fw = vec3(sin(yaw)*cp, sp, -cos(yaw)*cp);
    vec3 rt0 = normalize(cross(fw, vec3(0.0,1.0,0.0)));
    vec3 up0 = cross(rt0, fw);
```
Check up0: rt0×fw should = up: rt0=(cy?,0,sy?) as computed = normalize(cy,0,sin yaw)... For yaw=0.255, pitch=−0.105: fw=(0.252*0.994, −0.105, −0.967*0.994)=(0.2505,−0.105,−0.961). cross(fw,(0,1,0)) = (fw.y*0−fw.z*1, fw.z*0−fw.x*0, fw.x*1−fw.y*0) = (0.961, 0, 0.2505) → normalized ≈ (0.968,0,0.252) → pointing right ✓ (camera faces −z, right is +x). up0 = rt0×fw = |i j k; 0.968 0 0.252; 0.2505 −0.105 −0.961| = i(0*(−0.961) − 0.252*(−0.105)) − j(0.968*(−0.961) − 0.252*0.2505) + k(0.968*(−0.105) − 0) = i(0.02646) − j(−0.9303−0.0631) + k(−0.1016) = (0.0265, 0.9934, −0.1016). Wait j component: −(0.968*(−0.961) − 0.252*0.2505) = −(−0.9303 − 0.0631) = 0.9934 ✓ up points up and slightly tilted back (pitch down → up tilts forward −z? up0.z=−0.1016 tilts toward −z, consistent with looking down). Good.

uv.y up → up0 has +y ✓.

**Sun position vs camera forward:** yaw base 0.255 ≈ sun azimuth atan2(0.26,1.0)=0.255 ✓ → sun centered horizontally. With yaw sway ±0.06 sun drifts slightly — nice.

**Check overall brightness composition:** sky zenith dark (0.04,0.066,0.112)→ aces small → after gamma ~0.23,0.29,0.37 — dark stormy blue-grey ✓. Horizon haze warm; sun disc HDR → white-hot core. Clouds dark slate with orange underlit patches near sun ✓ dramatic.

Water: body deep (0.012–0.045) + fresnel reflection of dark sky → dark teal with warm path toward sun. Foam bright warm-lit ✓.

One risk: reflection of the dark sky might make water too dark overall mid-frame; the sun path (spec pow36 broad 0.30 + glow) warms the mid region. The broad glow pow(sd,28) in skyColor reflected: at grazing angles the reflected ray near horizon toward sun picks up strong glow → warm streak. Should look good.

**Check wave scale vs camera height:** base wavelength: p=world*0.045, noise cell in scaled domain = 1 → world wavelength 22.2 units for octave 1. After M2 (×2.05 + rotate), octave 2 wavelength ~10.8, etc. Amplitude octave1 = (c−0.3) mean... world height max ~3.1. Rolling waves of wavelength 22m amp 3m — steep dramatic swell ✓. Near camera (ro.y~4.5, clearance ~2–4), bottom of screen ray rd.y≈−0.5 hits water at t≈4–8 → one big wave fills lower foreground ✓.

Camera ride: waveField(camXZ, tm, 2.0) — note waveField includes warp which uses time ✓ consistent with rendering.

**Foam threshold vs wave heights:** p.y crest values: distribution of h = Σ(c_i − 0.30)a_i; c mean 0.5 → per octave mean contribution (0.2)a_i; mean h ≈ 0.2*2.04 = 0.41 → world mean 0.9. Hmm that's lower than my earlier estimate; std? c∈[0,1] each octave: variance contributions... crest values realistically: h max 1.43 → world 3.15. p.y > 2.05 happens only on big crests ✓ foam sparse-ish, broken by pattern → good (foam everywhere = fake). But risk: foam too rare → requirement "foam on crests" visible: threshold 2.05–2.95 with max 3.15 — top ~15% of crests. Let me lower a bit: smoothstep(1.85, 2.75, p.y). And trail band 1.0–2.0. Fine — will tune constants plausibly.

Also crest01 for body color: clamp(p.y/3.0) — mean 0.3 → body mix 0.17 → subtle greenish variation ✓.

**Fog & lod sanity at t=800:** lod = clamp(6−9.6,2,6)=2 → smooth distant swells ✓ fog=1−exp(−4.96)=0.993 ✓.

**Potential artifact:** banding/steps from LOD fade — amplitude fade is continuous (clamp(lod−i)) → no popping ✓.

**Bisection uses lod varying with m — continuous ✓.

**Cost estimate:** worst-case near-vertical rays: rd.y −0.5 hits in ~10 steps. Grazing: up to 120 steps each with ≤6-octave (usually 2–4 by then) → fine.

**Fragment shader overall length** — moderate. Compile time fine.

**Edge case: `rd.y > -0.0015` early-out but camera pitch sway could make top-of-screen rays rd.y up to +0.5 → sky ✓; rays near horizon −0.001..: march 120 steps × floor growth: floor at t: 0.05+0.012t; steps: t grows quadratically-ish: after n steps t ≈ sum ≈ 0.006 n² → n=120 → t≈86. So grazing rays return −1 at t≈86?! Wait — they exit loop after 120 iterations with t≈86 < TMAX → return −1 → sky at t≈86?? That's wrong: rays with rd.y=−0.002 would hit water at t≈1500 (never) fine as sky; but rays with rd.y=−0.02 hit at t≈ (clearance ~3.5)/0.02 = 175 — but steps: h stays ~3.5 for a long time (clearance decreases slowly: dh/dt = rd.y*(speed) ≈ −0.02*1 = −0.02/step?? h decreases 0.02 per unit t; step = max(0.42h, floor) ≈ max(1.3, floor). floor reaches 1.3 at t≈104. Cumulative descent by t=104: 2.08 → h≈1.4 → step max(0.6, 1.3)=1.3... by t≈170 descent 3.4 → hit around t≈170. Steps needed ≈ integral dt/step(t): step(t)=max(0.42h(t), 0.05+0.012t). With h≈3.5−0.02t: 0.42h ≈ 1.47−0.0084t vs floor 0.05+0.012t → cross at t≈71. Steps ≈ ∫0..71 dt/1.4 ≈ 51 + ∫71..170 dt/(0.05+0.012t) = (1/0.012)ln((0.05+2.04)/(0.05+0.85)) = 83.3*ln(2.09/0.90)=83.3*0.843≈70 → total ≈121. Just at the limit of 120! Risky — grazing rays near rd.y≈−0.02 might exhaust → return −1 → rendered as sky haze while neighbors hit water → possible horizon notch artifacts. Mitigations: raise iterations to 160, or make floor smaller early and larger later? The tension: near-horizon rays need many steps. Better approach: analytic assist — since distant field is lod-flattened, could intersect the ray with a bounding plane of max wave height first, then start marching from there?? But crests below that plane... Standard trick: start march at t where ray reaches min wave height? If ray can't hit before plane y=AMP*maxH... hmm rays hitting water must have p.y ≤ maxH at hit → t ≥ (ro.y − maxH)/|rd.y| for descending rays. So jump start: t0 = max(0.05, (ro.y − HMAX)/(−rd.y) ) where HMAX = 3.3 (max possible). Before that point, ray is above all water → no hit possible → skip ahead! Rays near horizon: rd.y=−0.002 → t0 = (4.5−3.3)/0.002 = 600 → instantly near horizon; then check from there: h = p.y − H: p.y ≈ 4.5−1.2=3.3 → h≈0+ → marching with small h → steps small... but we can also compute the plane for min height: if ray exits below y=HMIN=−1.5 without hitting, impossible: t1 = (ro.y − HMIN)/(−rd.y); if no hit by t1 → return −1. Combined: march between t0 and t1. This bounds steps for grazing rays: the interval where ray is between maxH and minH planes: length = (maxH−minH)/|rd.y|. For rd.y=−0.002: 4.8/0.002 = 2400 > TMAX → still capped by TMAX... but with floor steps t grows fast: from t0=600, floor = 0.05+7.2=7.25/step → reaches 800 in ~30 steps ✓. And mid-grazing rd.y=−0.02: t0 = (4.5−3.3)/0.02 = 60, interval until y<−1.5: t1 = 6/0.02=300; marching 60→~175 hit ✓ steps: h at t0 ≈ 0.05 small → step floor 0.05+0.72=0.77 grows; ~60 steps. OK. rd.y=−0.01: t0=120, hit t≈(4.5−1? descent to mean water 0.9: t=(4.5−0.9)/0.01=360; but crests up to 3.3 → could hit earlier where crest ~ p.y: p.y=4.5−0.01t; crest field world max 3.15 → hit when p.y≤3.15 → t≥135. Steps from 135 to ~360 (where p.y reaches mean 0.9... actually hit happens at first crest crossing): floor at 135 = 1.67, steps ≈ (360−135)/avg(1.7) ≈ 130... hmm plus bisections. Cap 200 iterations to be safe? Each iteration ~1 waveField(≤6 oct) + loop overhead. 200 × ~20 hash = 4000 hashes worst case per pixel only for the thin grazing band. With adaptive res, acceptable. Let me set MAXSTEPS=170 and TMAX=800, plus the plane-jump (t0). Also add early exit: if p.y > HMAX + |rd.y|*... no—once inside band just march.

Actually also improve: use "h*0.42" but when h small the floor dominates; fine.

Also don't forget tp initialization for bisection when t0 jump: tp = t0 (h>0 there guaranteed since p.y ≥ maxH... p.y at t0 = ro.y − |rd.y|*t0 = exactly HMAX when t0 computed from maxH: p.y = ro.y − (ro.y − HMAX) = HMAX ≥ H(x) ✓ h ≥ 0 ✓).

Edge: if ro.y < HMAX (possible? cam min 4.04 > 3.3 ✓ always above) so t0 ≥ 0 fine. Compute HMAX = 3.35.

Hmm wait — waveField max: I estimated max world ≈ 0.70*2.04*2.2 ≈ 3.14. Plus warp can add? Warp shifts domain, doesn't add height. So HMAX 3.2 safe; use 3.3.

But careful: lod at distance reduces amplitude (fades octaves) → actual max lower far away — using 3.3 constant is still safe (just less effective culling).

Also the min-plane early out: if ray descends below −1.4 without hit → impossible (min world = −0.30*2.04*2.2 = −1.35) → break return −1. Add per-step check: if (p.y < -1.5) return -1.0; — cheap and helps rays that pass through trough gaps... wait rays hitting water can't go below min water without crossing it — h<0 triggers first. p.y<−1.5 with no h<0 impossible; so this check is just safety. Skip? Keep cheap safety.

Let me now also handle the case where ray starts with h<0 (shouldn't): if h<0 at first sample → bisection between tp=0 and t → returns tiny t → water fills screen → degraded but bounded. Fine.

**Rewrite trace:**

```
float traceWater(vec3 ro, vec3 rd){
    if (rd.y > -0.0012) return -1.0;
    float inv = 1.0 / (-rd.y);
    float t = max(0.05, (ro.y - 3.3) * inv);
    if (t > TMAX) return -1.0;
    float tp = t;
    for (int i = 0; i < 200; i++){
        vec3 p = ro + rd * t;
        float lod = clamp(6.0 - t * 0.012, 2.0, 6.0);
        float h = p.y - waveField(p.xz, uTime, lod) * AMP;
        if (h < 0.0){
            float a = tp, b = t;
            for (int j = 0; j < 5; j++){
                float m = 0.5 * (a + b);
                vec3 pm = ro + rd * m;
                float hm = pm.y - waveField(pm.xz, uTime, clamp(6.0 - m * 0.012, 2.0, 6.0)) * AMP;
                if (hm < 0.0) b = m; else a = m;
            }
            return 0.5 * (a + b);
        }
        tp = t;
        t += max(h * 0.42, 0.05 + t * 0.011);
        if (t > TMAX) return -1.0;
    }
    return -1.0;
}
```

Wait, the plane jump: t = (ro.y − 3.3) * inv where inv = 1/(−rd.y) → t = (ro.y−3.3)/(−rd.y) ✓ positive since ro.y>3.3 and rd.y<0. At that t, p.y = 3.3 exactly. h = 3.3 − H ≤ 3.3 − (−1.4) = 4.7 possible big if trough below → step h*0.42 large ✓ fine.

Hmm but there's subtlety: for steep downward rays (rd.y=−0.7), (ro.y−3.3)/0.7 ≈ 1.7 — skips only 1.7 units, fine.

Grazing ray rd.y=−0.005: t0 = 1.2/0.005 = 240. March from 240: h = p.y−H where p.y=3.3: h ∈ [0, 4.7]; step up to ~2; progress to hit... TMAX 800: floor at 240 = 2.69 → ~80 steps to 800. OK within 200.

The 0.011 vs 0.012 floor — minor.

Also: rays with rd.y just below −0.0012: t0 = 1.2/0.0012 = 1000 > TMAX → −1 ✓ cheap.

**Now the fbm detail param for skyColor calls:** reflection detail 2.5 → n2 uses detail*0.75=1.9. Cloud density from 1-octave-ish fbm → blocky-ish but reflections are wobbly anyway ✓.

**Cloud coverage tuning:** fbm 5 octaves with a=0.5,0.55 gain... wait my fbm gain 0.55: amplitudes 0.5,0.275,0.151,0.083,0.046 sum=0.855. Mean vnoise 0.5 → mean ~0.43. dens = n1*0.72+n2*0.45 → mean ≈ 0.43*(1.17)=0.50. Range: n1∈[0.08,0.92] realistic → dens ∈ [0.13, 0.87]. cov = smoothstep(0.36,0.74,dens) → coverage maybe ~50% — dramatic broken storm clouds ✓. Maybe bias dens −0.03.

Cloud uv scale: cuv = rd.xz/(rd.y+0.14)*0.5; at rd.y=0.5: cuv ≈ rd.xz*0.77; fbm freq ×0.85 → feature scale ~1/(0.85*0.77) ≈ 1.5 rad → decent cloud sizes. Higher in sky rd.y→1: cuv≈0.44 → big features. OK.

Also add a third high haze layer? Keep two.

**Detail — clouds fade near horizon:** smoothstep(0.012,0.16,rd.y) — clouds vanish below y=0.012 → sky = pure gradient+haze there ✓ matches water fog region.

**Sun disc smoothstep(0.99930,0.99990):** edge0>edge1? smoothstep requires edge0<edge1; here 0.99930 < 0.99990 ✓ returns 1 when sd>0.99990 (angular radius acos(0.9999)=0.81°), 0 below 0.9993 (2.14°). Sun diameter ~1.6° — larger than real (0.5°) but looks better low on horizon. ✓

But wait: sun disc center el=0.045→0.135 rad (2.6°→7.7°). Disc radius 0.8° — bottom edge at el−0.014 rad ≈ 0.031 rad = 1.8° above horizon line ✓ never touches. At t=0 el 0.045 rad = 2.6°, disc bottom 1.8° — sun just hovering over horizon — dramatic ✓. And within 30s it climbs to 7.7° — visible change ✓. Hmm — actually should the sun descend (sunset) rather than rise? "low orange sun" — rising slightly reads as sunset continuing or just bobbing; a slow rise from near-horizon is fine and cinematic (like sun lifting out of storm squall). Either way within 30s it's low. OK.

Alternatively make it descend: el = 0.13 − 0.09*smoothstep(0,60,t)? Then it sets below horizon around t≈60 — after our 30s window the sun sinks — a nice narrative: sun slowly setting through the clip and beyond. Requirement: "show everything important within first 30 seconds" — at t=0 sun already low & orange ✓; over 30s it visibly sinks from 7.4°→ ~3.4°: subtle motion. I like the descend version: el(t) = 0.135 − 0.085*(t/60 clamped?) Let me do el = 0.13 − 0.09*smoothstep(0.0, 70.0, tm) → t=0: 0.13 (7.4°), t=30: 0.13−0.09*smoothstep(0,70,30)=0.13−0.09*0.588=0.077 (4.4°), t=70+: 0.04, then keep descending? After 70s it freezes at 0.04 — or continue: use smoothstep(0,90) → 0.04 at 90s, plus tiny sine wobble. Eh — simpler: el = 0.125 − 0.075*smoothstep(0.0, 80.0, tm) + 0.008*sin(tm*0.5). At t=30: 0.125−0.075*0.42+... ≈ 0.094. Sun visibly lowers over the record window ✓ and continues to settle. 

Let me finalize: `float el = 0.125 - 0.075*smoothstep(0.0, 80.0, uTime) + 0.01*sin(uTime*0.47);` min el at end ≈ 0.05−0.01=0.04 > 0 ✓ stays above horizon.

**Water sun-glitter alignment:** as sun lowers, glitter path lengthens — visible dynamics ✓.

**Now assemble the entire HTML.**

CSS:
```css
html, body { margin:0; height:100%; background:#0a0c10; overflow:hidden; }
#c { display:block; width:100vw; height:100vh; }
#err { position:fixed; inset:0; display:none; place-items:center; color:#c9d2dc; font:14px/1.6 system-ui? 
```
Hmm — I avoid system-ui as identity font but for an error message fallback it's fine contextually; actually to stay tasteful use a monospace stack for the fallback message. It's just an error path; keep it minimal.

JS structure with functions: createShader, createProgram, init, resize, frame.

Let me also guard uniform setting after context restore.

**Write vertex shader:**

```
#version 300 es
void main(){
    vec2 p = vec2(-1.0) + vec2( (gl_VertexID == 1) ? 3.0 : 0.0, (gl_VertexID == 2) ? 3.0 : 0.0 );
    gl_Position = vec4(p, 0.0, 1.0);
}
```
Hmm: verts: id0 (−1,−1), id1 (3,−1), id2 (−1,3) ✓ via conditional — simpler and avoids array indexing concerns.

**Precision in fragment:** highp float required; also `precision highp int;`? default int highp in ES3 fragment? Fragment default int is mediump in ES 3.0 — loops use ints small, fine.

**Uniform locations cached.**

**Adaptive resolution logic:**

```js
let resScale = 1.0, ema = 16.7, lastTs = 0, frames = 0, cooldown = 0;
function frame(ts){
    if (lastTs) { const dt = ts - lastTs; ema = ema*0.92 + dt*0.08; }
    lastTs = ts;
    frames++;
    if (--cooldown < 0 && frames % 40 === 0){
        if (ema > 26 && resScale > 0.55){ resScale = Math.max(0.55, resScale - 0.15); scheduleResize(); cooldown = 90; }
        else if (ema < 14 && resScale < 1.0){ resScale = Math.min(1.0, resScale + 0.1); scheduleResize(); cooldown = 90; }
    }
    ...
}
```
Note: rAF dt on 60Hz ≈ 16.7 — heavy shader may push to 30+; thresholds: down if ema>27 (i.e., <37fps), up if <15. First seconds include compile stall — cooldown starts high (e.g., 120) to skip initial jank. Also cap dpr at 2.

Hmm one nuance: ema starts 16.7; if actual 30fps (33ms) → ema rises → downscale ✓.

resize(): compute from innerWidth/innerHeight × min(dpr,2) × resScale.

Also `window.addEventListener('resize', resize)` plus visualViewport? innerWidth resize covers orientation changes. Also call resize() once at start before first frame.

**Time uniform:** seconds float; precision: after hours float32 time degrades — irrelevant for a recording; but mod time? Waves use uTime directly in noise offsets — large t → precision loss in sin/vnoise args (t*0.45 at t=3600 → 1620 + fract issues...). For a demo, fine. Could wrap time at large period but advection discontinuity. Leave it; note not needed.

Hmm, actually within first 30 s is what matters ✓.

**Fallback if no WebGL2:** show message div.

**Also handle context creation failure & shader compile errors → display overlay with log (helps debugging).**

Now, let me carefully write the fragment shader completely, watching for syntax errors.

Also — one more visual ingredient: subtle secondary light from sky on wave faces (ambient) — body color mixed with refl by fresnel handles it. And maybe slight color variation: water darker in troughs: crest01 handles.

Let me also add a subtle brightness boost to reflection when r aims near sun (already via skyColor glow) ✓.

Double-check `waveNormal` amp scaling: n = normalize(vec3(-(hx-h)*AMP/eps, 1.0, -(hz-h)*AMP/eps)). With eps=0.04 and typical local slope: waveField difference over 0.04 in world = derivative * 0.04. waveField derivative in scaled domain: octaves frequencies up to 0.045*2.05^5 ≈ 8.4 in world... gradient of vnoise ≤ ~1.5 per cell; contribution per octave: a_i * f_i (world) * 1.5... rough total slope (world units per world unit) can reach ~1.5–2 for chop. Then normal x-comp ≈ slope*AMP ≈ 3–4 → n.y ≈ 0.25 — steep faces ✓ good for drama. Central vs forward diff: forward fine.

But high octave derivatives at eps=0.04: octave 5 wavelength = 22/2.05^5 ≈ 0.61 world units; eps 0.04 ≈ 1/15 of that ✓ resolves.

eps grows with t: eps = max(0.04, t*0.008) → at t=200: 1.6 — smooths fine detail ✓ matches lod fade.

**Sparkle jitter frequencies:** vnoise(p.xz*5.0...) cell 0.2 world — near camera (t~5) footprint ~0.01 → many cells/pixel? Wait near camera footprint ~0.01 units vs cell 0.2 → smooth ✓; at t=200 footprint ~0.3 ~ cell → mild shimmer, amplitude faded to 0.02+... sparkle=smoothstep(500,60,200)=~0.63*... amp = 0.02+0.10*0.63=0.083 — could shimmer slightly; acceptable (glitter). Let me fade harder: smoothstep(400, 50, t) and amp 0.02+0.11*sp.

**Foam pattern scale:** fbm(p.xz*0.55): cell ≈ 1.8 world units — foam patches a few units ✓. Plus trail streaks anisotropic ✓.

**Sanity: foam on crest combined with fog fade** ✓.

**Sky reflection detail in `refl = skyColor(r, 2.5)` — includes disc: if reflected ray hits sun disc → bright streak ✓ (that's the main sun path!). Plus explicit spec term adds sparkle. Good.

Potential double-counting brightness — acceptable aesthetically.

**ACES function:**

```
vec3 aces(vec3 x){
    return clamp((x*(2.51*x+0.03))/(x*(2.43*x+0.59)+0.14), 0.0, 1.0);
}
```

**Vignette + gamma done in main.**

Now — write out everything. Also add subtle blue-ish ambient tint shift... keep as designed.

Let me also reconsider `pow(y,0.62)` gradient: at y=0.02 → 0.093 → mostly horizon color ✓ warm grey near horizon everywhere, darkening upward ✓ stormy.

Storm mood: maybe darken zenith more: (0.032, 0.05, 0.09).

One more addition for drama: a distant dark rain squall on one side? Skip — scope control.

**Write the JS shader sources as template literals; ensure `#version 300 es` is the first line — start the template literal immediately with `#version 300 es\n`.**

Full fragment shader:

```glsl
#version 300 es
precision highp float;

uniform float uTime;
uniform vec2  uRes;

out vec4 fragColor;

const float PI   = 3.14159265;
const float AMP  = 2.2;      // wave amplitude (world units)
const float TMAX = 800.0;    // max trace distance

const mat2 M2 = mat2(1.68, 1.18, -1.18, 1.68);

float hash12(vec2 p){
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

float vnoise(vec2 p){
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f*f*f*(f*(f*6.0 - 15.0) + 10.0);
    float a = hash12(i);
    float b = hash12(i + vec2(1.0, 0.0));
    float c = hash12(i + vec2(0.0, 1.0));
    float d = hash12(i + vec2(1.0, 1.0));
    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

float fbm(vec2 p, float detail){
    float v = 0.0, a = 0.5;
    for (int i = 0; i < 5; i++){
        float fade = clamp(detail - float(i), 0.0, 1.0);
        if (fade < 0.004) break;
        v += a * vnoise(p) * fade;
        p = M2 * p;
        a *= 0.55;
    }
    return v;
}

float waveField(vec2 pos, float t, float lod){
    vec2 p = pos * 0.045;
    vec2 warp = vec2(
        vnoise(p * 0.8 + vec2( t * 0.110, -t * 0.070)),
        vnoise(p * 0.8 + vec2(-t * 0.085,  t * 0.125) + 5.2));
    p += (warp - 0.5) * 0.9;
    vec2 d = vec2(0.95, 0.38) * (t * 0.45);
    float h = 0.0, a = 1.0;
    for (int i = 0; i < 6; i++){
        float fade = clamp(lod - float(i), 0.0, 1.0);
        if (fade < 0.004) break;
        float n = vnoise(p + d);
        float c = 1.0 - abs(n * 2.0 - 1.0);
        c *= c;
        h += (c - 0.30) * a * fade;
        p = M2 * p;
        d = M2 * d;
        a *= 0.52;
    }
    return h;
}

vec3 waveNormal(vec2 p, float t, float lod, float eps){
    float h  = waveField(p, t, lod);
    float hx = waveField(p + vec2(eps, 0.0), t, lod);
    float hz = waveField(p + vec2(0.0, eps), t, lod);
    vec2 g = vec2(hx - h, hz - h) * (AMP / eps);
    return normalize(vec3(-g.x, 1.0, -g.y));
}
```
careful: vec2 g = vec2(hx−h, hz−h)*(AMP/eps); return normalize(vec3(−g.x, 1.0, −g.y)); ✓

```glsl
vec3 sunDirection(){
    float el = 0.125 - 0.075 * smoothstep(0.0, 80.0, uTime) + 0.010 * sin(uTime * 0.47);
    return normalize(vec3(0.26, el, -1.0));
}

vec3 skyColor(vec3 rd, float detail){
    vec3 sun = sunDirection();
    float sd = clamp(dot(rd, sun), 0.0, 1.0);
    float y  = clamp(rd.y, 0.0, 1.0);

    vec3 col = mix(vec3(0.300, 0.205, 0.165), vec3(0.032, 0.052, 0.092), pow(y, 0.62));
    col += vec3(0.95, 0.34, 0.09) * pow(sd, 4.0)  * (1.0 - y * 0.55) * 0.55;
    col += vec3(1.15, 0.50, 0.15) * pow(sd, 28.0) * 0.85;

    float disc = smoothstep(0.99930, 0.99990, sd);
    float cov = 0.0;
    if (rd.y > 0.012){
        vec2 cuv = rd.xz / (rd.y + 0.14) * 0.5;
        vec2 w1 = vec2( uTime * 0.028,  uTime * 0.010);
        vec2 w2 = vec2(-uTime * 0.043,  uTime * 0.017);
        float n1 = fbm(cuv * 0.85 + w1 + 3.1, detail);
        float n2 = fbm(cuv * 2.10 + w2 + 17.7, detail * 0.75);
        float dens = n1 * 0.72 + n2 * 0.45;
        cov = smoothstep(0.35, 0.73, dens) * smoothstep(0.012, 0.16, rd.y);
        float lit = clamp(0.10 + pow(sd, 3.0) * 1.3, 0.0, 1.0);
        vec3 cCol = mix(vec3(0.040, 0.047, 0.062), vec3(0.90, 0.36, 0.13),
                        lit * clamp(1.15 - dens, 0.0, 1.0));
        cCol += vec3(1.00, 0.46, 0.16) * pow(sd, 5.0)
              * smoothstep(0.30, 0.52, dens) * (1.0 - smoothstep(0.52, 0.78, dens)) * 0.9;
        col = mix(col, cCol, cov);
    }
    col += vec3(6.5, 2.7, 0.95) * disc * (1.0 - cov * 0.85) * 2.6;
    col += vec3(1.10, 0.48, 0.16) * pow(sd, 60.0) * (1.0 - cov * 0.6);

    vec3 sunAz = normalize(vec3(sun.x, 0.0, sun.z));
    vec2 hxz = rd.xz / max(length(rd.xz), 1e-4);
    float hd = clamp(dot(hxz, sunAz), 0.0, 1.0);
    vec3 haze = mix(vec3(0.300, 0.215, 0.175), vec3(1.05, 0.45, 0.17), pow(hd, 3.0) * 0.9);
    col = mix(col, haze, smoothstep(0.18, 0.0, y) * 0.9);
    return col;
}
```
`+ 3.1` adding scalar to vec2 — GLSL allows vec2 + float ✓.

Trace:

```glsl
float traceWater(vec3 ro, vec3 rd){
    if (rd.y > -0.0012) return -1.0;
    float t = max(0.05, (ro.y - 3.3) / (-rd.y));
    if (t > TMAX) return -1.0;
    float tp = t;
    for (int i = 0; i < 200; i++){
        vec3 p = ro + rd * t;
        float lod = clamp(6.0 - t * 0.012, 2.0, 6.0);
        float h = p.y - waveField(p.xz, uTime, lod) * AMP;
        if (h < 0.0){
            float a = tp;
            float b = t;
            for (int j = 0; j < 5; j++){
                float m = 0.5 * (a + b);
                vec3 pm = ro + rd * m;
                float hm = pm.y - waveField(pm.xz, uTime, clamp(6.0 - m * 0.012, 2.0, 6.0)) * AMP;
                if (hm < 0.0) b = m; else a = m;
            }
            return 0.5 * (a + b);
        }
        tp = t;
        t += max(h * 0.42, 0.05 + t * 0.011);
        if (t > TMAX) return -1.0;
    }
    return -1.0;
}
```

Main:

```glsl
vec3 aces(vec3 x){
    return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0);
}

void main(){
    float tm = uTime;
    vec2 uv = (2.0 * gl_FragCoord.xy - uRes) / uRes.y;

    // --- boat camera: slow drift, heave, sway ---
    vec2 camXZ = vec2(1.8 * sin(tm * 0.071), 1.4 * sin(tm * 0.052 + 2.0));
    float ride  = waveField(camXZ, tm, 2.0) * AMP;
    float heave = 0.16 * sin(tm * 1.31) + 0.10 * sin(tm * 2.17 + 1.4);
    vec3 ro = vec3(camXZ.x, 4.55 + ride * 0.26 + heave, camXZ.y);

    float yaw   = 0.255 + 0.045 * sin(tm * 0.21) + 0.018 * sin(tm * 0.43 + 1.0);
    float pitch = -0.105 + 0.028 * sin(tm * 0.83 + 0.5) + 0.014 * sin(tm * 1.57);
    float roll  = 0.055 * sin(tm * 0.61 + 0.7) + 0.020 * sin(tm * 1.13);

    float cp = cos(pitch), sp = sin(pitch);
    vec3 fw  = vec3(sin(yaw) * cp, sp, -cos(yaw) * cp);
    vec3 rt0 = normalize(cross(fw, vec3(0.0, 1.0, 0.0)));
    vec3 up0 = cross(rt0, fw);
    float cr = cos(roll), sr = sin(roll);
    vec3 rt = cr * rt0 + sr * up0;
    vec3 up = -sr * rt0 + cr * up0;

    vec3 rd = normalize(uv.x * rt + uv.y * up + 1.35 * fw);
    vec3 sun = sunDirection();

    float tHit = traceWater(ro, rd);
    vec3 col;

    if (tHit < 0.0){
        col = skyColor(rd, 5.0);
    } else {
        vec3 p = ro + rd * tHit;

        float lodN = clamp(7.0 - tHit * 0.010, 3.0, 7.0);
        float eps  = max(0.04, tHit * 0.008);
        vec3 n = waveNormal(p.xz, tm, lodN, eps);
        float sparkle = smoothstep(400.0, 60.0, tHit);
        n.xz += (vec2(vnoise(p.xz * 5.0 + tm * 0.9),
                      vnoise(p.xz * 5.0 + 13.7 - tm * 0.8)) - 0.5)
                * (0.02 + 0.11 * sparkle);
        n = normalize(n);

        float cosT = clamp(dot(n, -rd), 0.0, 1.0);
        float fres = 0.022 + 0.978 * pow(1.0 - cosT, 5.0);

        vec3 r = reflect(rd, n);
        r.y = max(r.y, 0.015);
        r = normalize(r);
        vec3 refl = skyColor(r, 2.5);

        float crest01 = clamp(p.y * 0.33, 0.0, 1.0);
        vec3 body = mix(vec3(0.012, 0.052, 0.058), vec3(0.045, 0.200, 0.190), crest01 * 0.55);
        float towardSun = pow(clamp(dot(rd, sun), 0.0, 1.0), 3.0);
        body += vec3(0.03, 0.15, 0.12) * towardSun * crest01 * (1.0 - fres);

        col = mix(body, refl, fres);

        float rs = clamp(dot(r, sun), 0.0, 1.0);
        float spec = pow(rs, 340.0) * 2.4 + pow(rs, 36.0) * 0.30;
        col += vec3(1.25, 0.55, 0.22) * spec * (0.35 + 0.65 * fres);

        // foam: broken whitecaps on crests + elongated trailing wash
        float crest = smoothstep(1.85, 2.75, p.y);
        float fpat  = fbm(p.xz * 0.55 + vec2(-0.95, -0.38) * (tm * 0.22) + 7.7, 3.0);
        float foam  = crest * smoothstep(0.38, 0.75, fpat);
        vec2 fd = normalize(vec2(0.95, 0.38));
        vec2 st = vec2(dot(p.xz, fd), dot(p.xz, vec2(-fd.y, fd.x)));
        float trailN = fbm(vec2(st.x * 0.055 + tm * 0.16, st.y * 0.42) + 4.7, 3.0);
        float trail = smoothstep(1.05, 2.05, p.y) * smoothstep(0.46, 0.78, trailN) * 0.65;
        foam = clamp(foam + trail, 0.0, 1.0);
        foam *= 0.25 + 0.75 * smoothstep(650.0, 120.0, tHit);

        float nl = clamp(dot(n, sun) * 0.6 + 0.4, 0.0, 1.0);
        vec3 foamLit = vec3(0.93, 0.88, 0.80) * (vec3(0.20, 0.19, 0.185) + vec3(1.15, 0.62, 0.30) * nl * 1.1);
        col = mix(col, foamLit, foam * 0.88);

        // distance haze into the horizon
        vec3 hazeDir = normalize(vec3(rd.x, 0.02, rd.z));
        vec3 hazeC = skyColor(hazeDir, 1.0);
        float fog = 1.0 - exp(-tHit * 0.0062);
        col = mix(col, hazeC, fog);
    }

    col *= 1.25;   // exposure
    vec2 vuv = gl_FragCoord.xy / uRes - 0.5;
    col *= 1.0 - 0.30 * dot(vuv, vuv);
    col = aces(col);
    col = pow(col, vec3(1.0 / 2.2));
    fragColor = vec4(col, 1.0);
}
```

Wait — trail advection sign: waves/features move along −fd. st.x = dot(p,fd). A fixed world feature has fixed st.x. Trail pattern should translate with waves: sample fbm(vec2(st.x*k + tm*speed', ...)): sampling coordinate increases with time → feature at coordinate c appears where st.x*k + tm*s = c → st.x = (c − tm*s)/k → as tm↑, st.x decreases → features move along −fd ✓ same direction as waves ✓ (waves move −fd as established: sampling vnoise(p+d), d=+fd*t → features −fd ✓).

Foam patch advection: vec2(−0.95,−0.38)*(tm*0.22) added to p.xz*0.55... in fbm domain coordinate q = p.xz*0.55 + drift; feature at q=c → p.xz = (c − offset)/0.55 → offset = (−0.95,−0.38)*0.22tm → p.xz = (c + (0.95,0.38)*0.22tm)/0.55 → moves along +fd?! Waves move −fd. Foam should drift with waves-ish (slower). Fix: offset positive: + vec2(0.95,0.38)*(tm*0.22) → p = (c − (0.95,0.38)*0.22tm)/0.55 → moves −fd ✓. So use `+ vec2(0.95, 0.38) * (tm * 0.22)`. Speed in world = 0.22/0.55 = 0.4 u/s — slow residual drift; crest mask does main motion. OK.

Similarly check sparkle jitter time usage fine.

Sun glitter check near camera: rd pointing down at water, r = reflect → r points up toward sun region if surface faces sun... spec=0 mostly; near-grazing far water → path ✓.

Foam `smoothstep(650,120,tHit)`: smoothstep with edge0>edge1 — GLSL smoothstep undefined for edge0≥edge1? Spec: results undefined if edge0 ≥ edge1. Must use 1.0−smoothstep(120,650,t). I wrote smoothstep(650.0,120.0,...) — INVALID ordering. Replace with `(1.0 - smoothstep(120.0, 650.0, tHit))`. Similarly `smoothstep(400.0, 60.0, tHit)` → `1.0 - smoothstep(60.0, 400.0, tHit)`. And in skyColor: `smoothstep(0.18, 0.0, y)` → invalid! Replace: `(1.0 - smoothstep(0.0, 0.18, y))`. Also `smoothstep(0.99930, 0.99990, sd)` ✓ ascending fine. Many GPUs actually compute it anyway via clamp((x−e0)/(e1−e0)) which inverts gracefully, but per spec undefined — write it properly.

Also `mix(haze...)`: fine.

`vec2 hxz` name — I used `hxz` for the normalized horizontal vector and also `haze`... rename carefully:

```
vec2 hdir2 = rd.xz / max(length(rd.xz), 1e-4);
float hd = clamp(dot(hdir2, sunAz), 0.0, 1.0);
```

Also in water shading I use variable name `hazeDir`, `hazeC` fine.

Also `r.y = max(r.y, 0.015)` then normalize — r had |r|≈1 ✓.

Now, potential issue: pow(sd, 340.0) — high powers on some drivers with mediump? highp fine. Use max clamp done.

Another check — `waveField` warp uses uTime? I pass t param ✓ uses t.

fbm used with detail possibly 0 (skyColor detail 1.0 → n2 detail 0.75 → first octave fade=1 → ok; if detail <1 partial first octave ✓).

In skyColor, when detail = 1.0: n1 = 1 octave, n2 = 0.75 octave → dens coarse ✓ cheap.

**Cloud coverage at high altitudes:** cuv = rd.xz/(rd.y+0.14)*0.5 — at rd.y→1, cuv→rd.xz*0.44 (|rd.xz| small near zenith) → features stretch — fine (dome mapping standard artifact, mostly overhead stretching acceptable).

**One thing: the sky gradient + glow evaluated for rays below horizon (grazing miss) — y clamps 0 → haze — ✓ consistent with fog.

**Bisection when hit at first sample t=tp? If h<0 at i=0 (p already below at t0): a=tp=t → a==b → return t0 → p.y=3.3 point — renders water at plane-ish. Only if ro.y−... hmm t0 chosen s.t. p.y=3.3 ≥ H ✓ h≥0 always at t0 (since max field 3.14... wait lod fade reduces even more). Unless camXZ wave... no, field max independent of location ≤3.14 < 3.3 ✓. But is 3.14 truly the max? c max =1 per octave: h_max = Σ(c−0.3)a_i with all c=1: Σ0.7*a_i = 0.7*(1+0.52+0.2704+0.1406+0.0731+0.038) = 0.7*2.042 = 1.429 → ×2.2 = 3.14 ✓ < 3.3 ✓. And LOD only reduces. Good — t0 never inside water.

Also `(ro.y − 3.3)/(−rd.y)`: ro.y min ≈ 4.04 → numerator ≥ 0.74 ✓.

**Marching step `max(h*0.42, 0.05 + t*0.011)`:** early steps near t0 have h possibly large (4.7) → step 2 — could skip over a crest peeking? Between t0 and water the ray descends through crest band; step h*0.42 with h=clearance: sampling every 0.42×clearance vertically-ish → oversampling actually: vertical descent per step ≈ |rd.y|·step; skipping a crest requires crest height > clearance change... Standard concern; 0.42 factor is conservative-ish (Seascape uses ~0.5–0.6 with similar logic plus noise-based). Risk: occasional crest tip missed → tiny pinhole artifacts against sky at wave silhouettes — mitigated by bisection? No — bisection only if h<0 sampled. A missed thin crest shows sky where water should be — small artifacts at crest lines. To reduce, factor 0.35 and floor smaller near: floor 0.03+0.010t. Slightly more steps. Also LOD reduces far crest complexity making silhouettes smoother. I'll use 0.38 and accept.

Alternatively safer: also check midpoint? Doubling evals... 0.35 fine.

**Check reflection ray `skyColor(r, 2.5)` cost:** fbm calls: n1 5-oct (fade from 2.5 → octaves 0,1 full, 2 partial 0.5, rest 0) → ~3 evals; n2 detail 1.875 → ~3; total 6 vnoise ≈ 24 hash — fine.

**Total fragment cost per water pixel:** trace (~30–120 waveField evals × up to 6 vnoise) + shading (~25 vnoise). Should run 60fps at 1080p on discrete GPU; integrated may drop → adaptive res handles.

Hmm — 200 iterations × waveField(6 octaves) worst case = 1200 vnoise = 4800 hash12 — that's heavy worst case but only for near-horizon grazing rays; average much lower. Also the `break` keeps early octaves cheap at distance (lod=2 → 2 evals). Fine.

Wait, one bug risk: `for (int i = 0; i < 200; i++)` with early return inside nested loop — fine ES3.

**Cloud movement speeds:** w1 = tm*0.028 in cuv domain where cuv spans ~±0.5·(aspect...) rad-ish → drift 0.028/s across feature scale ~1 → clouds visibly crawl over ~30 s (0.84 of a feature) ✓ perceptible within window ✓.

**Sun within clouds:** cov ~0.5 average — sun disc punches through (×(1−0.85cov)) ✓ dramatic god-ish glow via pow(sd,60) term also ×(1−cov*0.6).

**Check pow(sd, 4.0)*(1.0 − y*0.55)*0.55 — at horizon near sun: 0.55*0.55*... plus haze overlay warm ✓.

Also, when shading water reflection with r near horizon pointing at sun azimuth: refl picks strong glow pow(sd,28) → the classic bright path ✓.

**Fresnel at bottom of screen (looking down):** cosT ~ dot(n,−rd): rd.y≈−0.75, n.y≈0.9 → cosT≈0.67 → fres = 0.022+0.978*(0.33)^5 ≈ 0.024 → mostly water body color, tiny reflection — dark teal foreground ✓ contrast with bright foam ✓.

Mid-distance grazing: cosT~0.2 → fres ≈ 0.022+0.978*0.32768 ≈ 0.34 → strong sky reflection ✓.

**Foreground darkness might be too black** — body deep (0.012,0.052,0.058)*1.25 exposure → aces ~0.02 → gamma ~0.17 — quite dark; plus subsurface term adds greenish on crests toward sun. Storm ocean at sunset is dark — acceptable, foam & path light it. Maybe lift deep slightly: (0.016, 0.06, 0.066). OK.

Also add subtle broad specular sheen even off-sun: skip.

**Now the sun path position:** sun azimuth 0.255 rad from −z; camera yaw base 0.255 → sun horizontally centered ✓ path leads from sun toward camera ✓.

**gl_FragCoord with resScale** — uRes = canvas.width/height (drawingbuffer) ✓ consistent.

**Now the JS.** Also handle `webglcontextlost/restored`. And guard: if compile fails show overlay with error text (monospace, small).

Let me write the complete file:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Grey Water — Stormy Ocean at Sunset</title>
<style>
  html, body { margin:0; padding:0; width:100%; height:100%; overflow:hidden; background:#0b0e12; }
  #glcanvas { display:block; width:100vw; height:100vh; }
  #fallback {
    position:fixed; inset:0; display:none; align-items:center; justify-content:center;
    color:#c8cfd6; font:13px/1.7 "SFMono-Regular", Menlo, Consolas, monospace;
    text-align:center; padding:2rem; letter-spacing:.02em;
  }
</style>
</head>
<body>
<canvas id="glcanvas"></canvas>
<div id="fallback"></div>
<script>
"use strict";
(function () {
  const canvas = document.getElementById("glcanvas");
  const fallback = document.getElementById("fallback");
  const gl = canvas.getContext("webgl2", {
    antialias: false, alpha: false, depth: false, stencil: false,
    powerPreference: "high-performance"
  });

  function fail(msg) {
    fallback.style.display = "flex";
    fallback.textContent = msg;
  }
  if (!gl) { fail("WebGL2 is not available in this browser."); return; }

  const VERT_SRC = `#version 300 es
  ...`;
  const FRAG_SRC = `#version 300 es
  ...`;

  let prog = null, uTime = null, uRes = null;

  function compile(type, src) {
    const sh = gl.createShader(type);
    gl.shaderSource(sh, src);
    gl.compileShader(sh);
    if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) {
      throw new Error(gl.getShaderInfoLog(sh) || "shader compile failed");
    }
    return sh;
  }

  function init() {
    const vs = compile(gl.VERTEX_SHADER, VERT_SRC);
    const fs = compile(FRAGMENT_SHADER?, FRAG_SRC);
    prog = gl.createProgram();
    gl.attachShader(prog, vs); gl.attachShader(prog, fs);
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
      throw new Error(gl.getProgramInfoLog(prog) || "link failed");
    }
    gl.useProgram(prog);
    uTime = gl.getUniformLocation(prog, "uTime");
    uRes  = gl.getUniformLocation(prog, "uRes");
  }

  try { init(); } catch (e) { fail("Shader error:\n" + e.message); return; }

  canvas.addEventListener("webglcontextlost", function (e) { e.preventDefault(); }, false);
  canvas.addEventListener("webglcontextrestored", function () {
    try { init(); } catch (e) { fail("Shader error:\n" + e.message); }
  }, false);

  const DPR_CAP = 2;
  let resScale = 1.0, emaMs = 16.7, lastTs = 0, cooldown = 120;

  function resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2) * resScale;
    const w = Math.max(1, Math.round(window.innerWidth  * dpr));
    const h = Math.max(1, Math.round(window.innerHeight * dpr));
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w; canvas.height = h;
      gl.viewport(0, 0, w, h);
    }
  }
  window.addEventListener("resize", resize);
  resize();

  let start = -1;
  function frame(ts) {
    if (start < 0) start = ts;
    const time = (ts - start) * 0.001;

    if (lastTs !== 0) emaMs = emaMs * 0.90 + (ts - lastTs) * 0.10;
    lastTs = ts;
    if (--cooldown < 0) {
      if (emaMs > 27 && resScale > 0.55) { resScale = Math.max(0.55, resScale - 0.15); resize(); cooldown = 120; }
      else if (emaMs < 14 && resScale < 1.0) { resScale = Math.min(1.0, resScale + 0.10); resize(); cooldown = 120; }
    } 

    resize(); // cheap guard (handles window resizes between events too)
    gl.uniform1f(uTime, time);
    gl.uniform2f(uRes, canvas.width, canvas.height);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
</script>
</body>
</html>
```

Hmm — calling resize() every frame plus on event: fine (early-out unless dims differ). Actually remove the event listener? Keep both harmless. Actually the per-frame resize guard alone covers everything including dpr changes (dpr read each call). Keep both, harmless.

One concern: `if (lastTs !== 0)` — first rAF ts could be small but nonzero; using a boolean flag `hasLast`. Use `let havePrev = false`.

Also — `#version 300 es` must be the very first token of the shader source: my template literal starts with `#version 300 es\n` — ensure no whitespace/newline before. I'll write:

```js
const VERT_SRC = `#version 300 es
void main(){...}`;
```
✓ (template literal content starts immediately after backtick).

But inside the file the template literal spans multiple lines with the GLSL — fine.

Note about `in`/`out`: vertex shader has no attributes; use gl_VertexID. Fragment: `out vec4 fragColor;` declared once ✓.

GLSL: constant mat2 at global scope: `const mat2 M2 = mat2(1.68, 1.18, -1.18, 1.68);` — const initialization with constant expression ✓ allowed in ES 3.00.

Wait: is `const mat2 M2 = mat2(...)` allowed at global scope in ES 3.0? Yes — const qualified global with constant initializer ✓.

Check `waveNormal` returns using uTime? passes t explicitly ✓.

In `traceWater` I reference `uTime` — fine (global uniform).

Now double-check `skyColor` usage of `uTime` ✓.

One more syntax check in fbm: `p = M2 * p;` mat2*vec2 ✓.

`vec2 w1 = vec2( uTime*0.028, uTime*0.010);` ✓.

`fbm(cuv * 0.85 + w1 + 3.1, detail)` — vec2 + float ✓ (component-wise).

`smoothstep(0.35, 0.73, dens) * smoothstep(0.012, 0.16, rd.y)` ✓.

In foam: `fbm(p.xz * 0.55 + vec2(0.95,0.38)*(tm*0.22) + 7.7, 3.0)` ✓.

`float nl = clamp(dot(n,sun)*0.6+0.4, 0.0, 1.0);` ✓.

`foamLit = foamCol*(vec3 + vec3*nl*1.1)` — vec3*(vec3) componentwise ✓.

Tonemap: exposure 1.25. Sun disc HDR ~ (6.5*2.6*1.25≈20) → aces→1 ✓ white core.

Check skyColor horizon haze applied even for water fog call with rd.y=0.02: factor smoothstep→ (1−smoothstep(0,0.18,0.02)) = 1−0.114 ≈ 0.886; ×0.9 = 0.797 → hazeC ≈ 0.886·0.9? wait col = mix(col, haze, 0.9*(1−ss)). At y=0.02: ss=smoothstep(0,0.18,0.02)= (0.02/0.18)=0.111→ss=3x²−2x³≈0.036 → mix factor 0.9*(1−0.036)=0.868. And disc/glow added after? Order: glow terms added before clouds; haze mixed last — so hazeC includes haze mix over glow... but the sun glow pow(sd,28) at horizon toward sun gets 87% replaced by haze(1.05,0.45,0.18) — haze itself is warm near sun (pow(hd,3)*0.9 mix) → fog near sun is warm ✓ good enough.

But the specular `spec` on water is added BEFORE fog → the sun path dims with distance — at t=300 fog 0.84 — the far end of the glitter path fades into warm haze; near sun region the haze color itself is bright warm (1.05,0.45,0.17) — reads as the path meeting the sun glow ✓.

Also the disc reflected: refl includes disc*(1−cov*0.85)*2.6 HDR — at grazing, reflected ray toward sun hits disc → bright elongated spot ✓.

Edge case: `r.y = max(r.y, 0.015)` after reflect with very steep normal could make r nearly horizontal → sd with sun el 0.05–0.12: dot could still reach disc when r.y ≈ el ✓ glitter path concentrated where reflected rays align with low sun — near-horizon water ✓ physical.

**Check pitch base −0.105 rad ≈ −6°: horizon (rd.y=0) sits slightly above screen center: screen y for rd.y=0: uv.y = (0 − sp·1.35... rd = uv.y*up + 1.35*fw; rd.y = uv.y*up0.y + 1.35*sp ≈ uv.y*0.995 − 0.1418. rd.y=0 → uv.y ≈ 0.1425 → horizon at ~14% above center → sky occupies ~36% of height, water 64% ✓ nice composition for big waves.

**Wave scale on screen:** base wavelength 22 world units; foreground wave crest at t≈6 → width on screen: 22 units at 6 distance with focal 1.35... angular size ≈ 22/6 ≈ 3.7 rad?? That's huge — waves at 6 units distance spanning multiple screen widths. Hmm wavelength 22 and camera height ~2–3 above local surface: the foreground shows maybe one big swell face — dramatic ✓. Mid-ground waves at t≈30–80 → several rollers visible ✓. Good.

Amplitude check vs camera clearance: local water mean world ≈ 0.9; camera 4.55±~1 → typical clearance 3–4.5; crests nearby up to 3.1 → sometimes nearly eye-level crests — dramatic moments when a big swell passes ✓ (clearance min ~0.9 computed earlier with ride correlation). 

Ride factor 0.26: ride∈[−1.4,3.1] → contribution ∈[−0.36, 0.81]; heave ±0.26 → camY ∈ [4.55−0.36−0.26, 4.55+0.81+0.26] = [3.93, 5.62]. Min clearance vs max nearby crest 3.14: 0.79 ✓ safe.

**Now think about whether the ridged noise actually reads as ocean waves rather than weird blobs.** Each octave: c = (1−|2n−1|)² — creates smooth roundish peaks at noise maxima lattice + valleys broad. Sum of rotated octaves with decreasing amp → organic rolling surface with sharper crests. With warp + advection, looks like swell. I believe it's decent. One improvement for "large rolling waves": increase first octave wavelength: p = pos*0.045 → cell 22u ✓ and amp weighting: first octave amplitude 1.0 dominates (later 0.52...) ✓ big rollers ✓.

Maybe also add a very-low-frequency swell (wavelength ~90u, amp ~1.2) to make sets of bigger waves — "sets" rolling through add boat-drama:

Add before octaves: `h += (vnoise(p*0.35 + d*0.3) − 0.5) * 1.6;`? A non-ridged low-freq component adds long undulation. Let me add: 

```
float swell = vnoise(p * 0.32 + d * 0.45) - 0.5;
h += swell * 1.35;
```
Wait h currently in units where world = ×2.2. Adding swell*(1.35) → world ±1.5 extra → max total 3.14+1.49 = 4.6 > plane 3.3! Must raise plane to 4.7 & recheck camera clearance: camY min 3.93 < 4.6 crest → camera could be under a crest! Hmm. Then reduce: swell*0.9 → ±0.99 world → max 4.13; plane 4.2; camY min 3.93 < 4.2 — trace t0 = (ro.y−4.2)/... negative → max(0.05, negative)=0.05 ✓ still fine (t0 just starts at 0.05; correctness: if ro.y < maxH, can't skip ahead — formula gives negative → clamp 0.05 ✓ safe). But camera below max crest → possible camera-inside-wave moments when a 4.1 crest passes under camera whose local ride raises cam: ride includes swell? waveField(camXZ, tm, 2.0) — lod 2 → includes swell? Swell added as separate term with its own lod? If I add swell inside waveField before octave loop with fade... include swell always (not faded): then ride includes swell → when swell high (+0.99) cam rises 0.26×(H includes...) hmm ride = waveField*AMP*0.26: swell world ±0.99 → ride contribution ±0.26 — not enough: crest 3.1+0.99=4.13 nearby while cam at trough-adjacent... Cam min 3.93 vs crest 4.13 → camera could dip 0.2 below a crest top → screen-filling wall of water momentarily — actually that's *dramatic and realistic* (boat in trough), but the renderer handles it: rays with rd.y≥0 from below-crest camera: early-out `rd.y > −0.0012 → sky` — wrong when camera below a wave that should block sky! Visual artifact: seeing sky through a wave that should occlude. Rare & brief... risky.

Safer: cap swell so total max stays < camY_min − margin. Let swell contribute ±0.7 world: `h += (vnoise(...)−0.5)*0.85` → wait ×AMP: (±0.5)*0.85... let me define swell term inside waveField: `h += (vnoise(p*0.32 + d*0.5) − 0.5) * 0.9;` — in field units ±0.45 → world ±0.99. Total max = 1.429+0.45 = 1.879 field → world 4.13. Min = −0.30*2.042−0.45 = −1.063 → world −2.34. Hmm deep troughs −2.3 while mean 0.9 — waves get very moody, fine.

Camera clearance worst: camY min = 4.55 − 0.26*1.4(ride min... ride min = −2.34? ride∈[−2.34, 4.13] → ride*0.26 ∈ [−0.61, +1.07]; heave ≥ −0.26 → camY ∈ [3.68, 5.88]. Crest max 4.13 > 3.68 → camera can be below crest → artifact risk again. 

Alternative: make ride stronger so camera follows local surface: camY = 2.9 + ride*0.55 + heave*0.5: ride∈[−2.34,4.13] → camY ∈ [2.9−1.29−0.13, 2.9+2.27+0.13] = [1.48, 5.30]. Camera 1.48 when in deep trough while max crest 4.13 elsewhere → definitely below crests → walls of water — realistic but the "sky above water" early-out breaks (camera below max surface). Hmm.

Decision: keep modest swell so camera ALWAYS above global max: require camY_min > H_max. Set: no extra swell term (field max 3.14), camY = 4.55 + ride*0.26 + heave → min 3.93 > 3.14 ✓ margin 0.79. To get "sets" feel (groups of bigger waves), I can shape the first octave's ridge distribution via warp — skip; amplitude variance from noise already varies crest heights naturally (some swells reach ~3, most ~2–2.5). The bobbing camera + varying sets will read as rolling seas. ✓ Keep single design; plane 3.3 constant → grazing skip works; camera always safe.

Hmm wait — but earlier I compute trace t0 with 3.3: if H_max 3.14 ✓.

Alright — but I want a bit more "large rolling" drama. Increase AMP to 2.5? max world = 1.429*2.5 = 3.57; plane 3.7; camY = 4.8 + ride*0.26 (ride ∈ [−1.6, 3.57] → ±) → camY ∈ [4.8−0.42−0.26, 4.8+0.93+0.26] = [4.28, 6.13] > 3.7 ✓ margin 0.58. Slightly tighter clearance in troughs (4.28 vs nearby crest 3.57 → 0.7). Fine. Let me adopt AMP=2.5, cam base 4.8, ride 0.24, plane 3.7. Mean water ≈ 0.2*2.042*2.5 ≈ 1.02; clearance typical 3.8. Foam thresholds scale: crest values up to 3.5 → foam smoothstep(2.15, 3.15, p.y); trail band smoothstep(1.2, 2.4, p.y). crest01 = clamp(p.y*0.30,0,1).

Also crest01 body mix etc. fine.

Recheck t0: (ro.y−3.7)/(−rd.y): ro.y min 4.28 → numerator 0.58 ✓.

Wavelength 22u amp 2.5 → very steep dramatic swell ✓. Waves also travel 10 u/s — a 22u wave passes in ~2.2s: lively sea ✓ maybe slightly fast; drift 0.45→0.38: speed = 0.38*|d̂|... d = vec2(0.95,0.38)*(t*0.45): velocity in scaled domain = 0.45*(0.95,0.38) → magnitude 0.45*1.023 = 0.46 /s; world speed = 0.46/0.045 = 10.2 u/s. With wavelength 22u → period 2.2s — a bit fast/stormy-choppy; rolling swell slower: use 0.30 → 6.8 u/s → period 3.2s ✓ better "rolling". Also warp time speeds ok.

Secondary octave drift: d multiplied by M2 each octave — consistent ✓.

Now, the drift direction: features move along −d̂ = −(0.93,0.37)... i.e. toward −x,−z. Camera looks −z: waves approach camera ✓ perfect (head-on swell, dramatic).

Foam advection direction should also be −fd (with waves): earlier fixed sign ✓ (offset +fd*t → features −fd ✓ wait recheck: q = p.xz*0.55 + fd*(tm*0.22): feature at q=c: p.xz*0.55 = c − fd*0.22tm → p.xz = (c−fd·0.22tm)/0.55 → p decreases along fd with time → features move −fd ✓).

Trail: st.x*0.055 + tm*0.16: coordinate increases with tm along fd → feature moves −fd ✓ speed = 0.16/0.055 = 2.9 u/s (slower than waves 6.8 — foam lags behind crests → trails ✓ nice).

Wait but trail mask is based on p.y (current crest position) while pattern drifts slower → pattern appears to slide backward relative to crest → looks like foam left behind in the wash ✓ 

**Foam pattern second octave for breakup:** fpat fbm 3 octaves — ok.

**Check normal eps at far:** tHit 600 → eps 4.8; waveField differences over 4.8 units with lod ~3: smooth ✓.

**LOD for normals:** lodN = clamp(7−0.010t, 3, 7): at t=0 → 7 (6 octaves ✓ i<6 so max index 5 → fade=lod−5 ≥2 → full ✓). at 400 → 3 → ~3 octaves ✓ consistent with geometry lod 6−4.8=1.2→clamp 2? Hmm geometry lod at 400 = clamp(6−4.8,2,6)=2; normals 3 → normals include an octave the geometry doesn't → normals of detail that doesn't exist geometrically — fine visually (micro-shading), though spec sparkle may suggest motion inconsistent... acceptable, actually helps shimmer. OK.

**gl_FragCoord with fractional?** fine.

**Precision of `(2.0*gl_FragCoord.xy − uRes)/uRes.y` ✓.**

**Alpha:** fragColor alpha 1, context alpha:false ✓.

**Dithering to prevent banding in dark sky:** add tiny hash noise before gamma: `col += (hash12(gl_FragCoord.xy + fract(tm)*13.7) − 0.5) * (1.5/255.0);` after tonemap before gamma — reduces banding in dark sky gradient ✓ nice craft touch. Place after aces, before pow gamma (add in linear-ish post-tonemap space — either fine). I'll add after aces.

Now — double check the vertex shader:

```glsl
#version 300 es
void main(){
    vec2 p = vec2(-1.0, -1.0);
    if (gl_VertexID == 1) p = vec2(3.0, -1.0);
    if (gl_VertexID == 2) p.x = 3.0;  // wait id2 should be (-1, 3)
```
Fix: id2 → (−1, 3): `if (gl_VertexID == 2) p.y = 3.0;` ✓. Triangle (−1,−1),(3,−1),(−1,3) covers screen ✓.

No VAO bound: WebGL2 default VAO — drawArrays with no enabled attributes is legal ✓.

**Now assemble the final fragment shader text fully, and re-verify every function name/usage:**

Functions: hash12, vnoise, fbm, waveField, waveNormal, sunDirection, skyColor, traceWater, aces, main. Order matters (define before use) — arrange: constants, hash, vnoise, fbm, waveField, waveNormal, sunDirection, skyColor, traceWater, aces, main. sunDirection uses uTime ✓ defined before skyColor/trace ✓.

Potential GLSL pitfall: `if (fade < 0.004) break;` inside for with dynamic condition — allowed in ES 3.00 ✓ (loops need not have constant bounds in ES 3).

Another: `vec2 warp` uses t param name `t` — shadowing none ✓. Inside waveField param named t; uTime global — consistent calls use uTime.

In waveNormal param list (p, t, lod, eps) — name p shadows nothing problematic ✓.

In traceWater: variable named `t` local; uTime used inside ✓.

In main: `float tm = uTime;` used for camera & foam; waveField calls pass tm ✓ (I wrote waveField(p.xz, tm, lodN...) ✓ consistent time). traceWater internally uses uTime — same value ✓.

skyColor uses uTime internally ✓.

Double-check `skyColor` early part executes for rays with rd.y<0 (grazing miss): clouds branch skipped (rd.y>0.012 false) ✓; haze mix full at y≈0 ✓.

**Check haze color used as fog for water:** hazeC = skyColor(normalize(vec3(rd.x,0.02,rd.z)),1.0) — includes disc term: if fog ray direction passes near sun → hazeC includes disc*(1−cov...)·2.6 with cov=0 (rd.y=0.02 < 0.012? 0.02>0.012 → cov computed with detail 1! smoothstep(0.012,0.16,0.02)≈0.0064 → cov≈0 ✓) and disc: sd at rd.y=0.02 toward sun azimuth: dot ≈ cos(el−0.02 ≈ 0.03..0.11) ≈ 0.9985–0.9995 < 0.9993 → disc=0 ✓ mostly; glow pow(sd,28) significant → warm fog toward sun ✓ and pow(sd,60)*1.2 — at sd 0.999 → 0.94 → adds (1.03,0.45,0.15)*... hmm pow(0.999,60)=0.94 → contributes vec3(1.1,0.48,0.16)*0.94*(1−0)≈(1.03,0.45,0.15) — bright warm spot in fog near sun direction at horizon — that's the sun-glow at horizon — actually desirable: fog brightens near sun ✓ and the water path blends into it ✓.

But wait: at rd.y=0.02 exactly horizontal, sd max = cos(el − 0.02) ≈ 1 − (el−0.02)²/2: el=0.07 → sd≈0.99955 → pow(sd,28)=0.987 → glow term full → haze near sun ≈ (0.3..)+0.55*0.95*(0.95,0.34,0.09)... plus 0.85*(1.15,0.50,0.15)*0.987 ≈ bright orange ✓ (≈1.4,0.85,0.5 pre-tonemap → nice glowing horizon) ✓.

**Water reflection at grazing picks glow → path bright ✓.**

**Sun visibility check:** disc requires sd≥0.9999 → angular offset ≤0.9°. Sun center at el 4–7.6° → disc fully visible above horizon (horizon at rd.y=0, disc bottom el−0.9° ≥ 1.7°) ✓ always above water line, may be partially veiled by clouds (cov up to ~0.85 reduction → disc still visible through gaps at 15% + strong glow) ✓ dramatic.

Hmm — clouds coverage: `cov = smoothstep(0.35,0.73,dens)*smoothstep(0.012,0.16,rd.y)`: near horizon clouds fade (smoothstep→0 at rd.y=0.012) so sun area near horizon mostly clear ✓ sun sits in a bright hazy gap under the cloud deck — classic storm-sunset ✓.

**Now the "sky occupies top ~36%"** with dark clouds — composition: bright low sun + orange horizon glow + dark cloud masses above + big dark rolling swells with foam + glitter path. 

**One more artistic touch — subtle color grade:** add slight teal-shadow / orange-highlight split? The palette already does this naturally. Add gentle blue-grey ambient in shadows via body color ✓ done.

**Bloom?** No post passes (single pass). The ACES on HDR glow gives soft rolloff — enough.

**Grain:** added dither ✓.

Let me also double check `pow(y, 0.62)` when y=0 → 0 ✓; mix yields horizon color ✓.

`smoothstep(0.99930, 0.99990, sd)` ✓ ascending.

**Numeric edge:** `normalize(vec3(rd.x, 0.02, rd.z))` when rd ≈ (0,0,0)? rd normalized never zero ✓; rd.xz could be ~0 for straight-up rays — fog call only for water hits where rd points down (rd.xz magnitude ≥ ... could be tiny if looking straight down? then water hit near camera; fog≈0; hazeC value irrelevant but computed — length(rd.xz) could be 0 → division guarded with max(,1e-4) ✓; but normalize(vec3(0,0.02,0)) → normalize(0-vector) undefined! rd.xz exactly 0 → vec3(0,0.02,0) → normalize → NaN risk. Guard: hazeDir = normalize(vec3(rd.x, 0.02, rd.z) ) — if rd.xz=0 exactly → NaN → col NaN → black pixel bottom-center when looking straight down... camera pitch −0.105±0.042 → rd straight down impossible (pitch max ~−0.05, focal 1.35 → min |rd.xz|/|rd.y| = tan? rd.xz magnitude ≥ sin? For rd.y=−1 need pitch ≤ −90° — impossible ✓). rd.xz ≈ cos(pitch)·... ≥ 0.99 ✓ safe.

Similarly skyColor hdir guard ✓.

**Check `sunAz` recomputed per skyColor call — fine.**

**Check horizon line quality:** rays rd.y from +0.001 (sky) to −0.001 (march, t0=(ro.y−3.7)/0.001 up to ~ (5−3.7)/0.001 = 1300 > TMAX → −1 → sky) → horizon transition happens across rd.y∈[−0.0016,0] band → sub-pixel ✓ smooth thanks to haze matching. Distant water at t0≈TMAX... rays hitting near TMAX: fog≈0.993 → water barely visible ✓ seam invisible.

Wait — rays with rd.y=−0.003: t0 = 1.3/0.003 ≈ 433 < 800 → march from 433: lod=clamp(6−5.2,2,6)=2; h = p.y − H*... p.y = 4.8−1.3=2.7 at t0? Hmm p.y at t0 = 3.7 (plane) — wait ro.y−3.7 over −rd.y: p.y(t0)=3.7 exactly; h = 3.7 − H(x) ∈ [0.56, 6.0] (H∈[−2.34? min −0.30*2.042*2.5 = −1.53] → h up to 5.2) — steps h*0.42 big (~1.5–2.5) or floor 5.3 → marches fast; water surface mean 1.0 → p.y descends 0.003/unit → reaches mean at t≈900 > TMAX → likely no hit → sky ✓. Rays rd.y=−0.01: p.y from 3.7 descends 0.01/u → reaches crest band 3.0 at t≈470, hits a crest (lod2 crest world up to 0.7*2.042... lod2 max ≈ (1+0.52)*0.7? With lod=2: octaves 0,1 full: max 0.7*1.52=1.064 → world 2.66 — hmm at lod2 crest heights max 2.66; p.y=3.7 at 433, descends to 2.66 at t≈773 → likely hit around t≈600–700 near TMAX, fog≈0.98 → fine ✓.

The visible horizon effectively = where fog≈1 — seamless ✓.

**Hmm wait, one issue:** with TMAX=800 and fog k=0.0062, at t=400 fog=0.916 — rays hitting at 400 show 8% water — distant crests barely visible as slightly darker band near horizon — good, subtle. Maybe increase fog density slightly for softer horizon: k=0.0075 → t=300 → 0.895. Let me use 0.0068.

Also LOD geometry fade means distant waves flatten → horizon is smooth plane ✓ no aliasing spike line ✓.

**Wave silhouettes against sun glow near horizon:** rays grazing crests at t≈100–300 → h*0.42 stepping might tunnel thin crests → occasional speckle. bisection won't catch (needs h<0 sample). Reduce with factor 0.35. At t=200, floor=0.05+2.2=2.25 dominates anyway when h>5... floor is the min step; h*0.35 < floor when h < 6.4 — floor dominates most of the time at distance! Floor steps of ~2+ units at t=200 with wavelength 22 → ~11 samples per wave ✓ adequate. Near camera floor small (0.05–0.3) ✓ h*0.35 governs ✓.

Wait floor at t=0: 0.05 — near field fine.

Actually hmm, floor growth 0.011*t: at t=50 → 0.6 — foreground-mid waves (t 10–50, wavelength 22): samples per wave: path through wave region... horizontal speed |rd.xz| ≈ 0.95; over one wavelength 22u → t span 23 → steps: floor from 0.16→0.30 (~ avg 0.23) + h*0.35 (h clearance typically 1–3 → 0.35–1.4) → step avg ~0.8 → ~28 samples per wavelength ✓ smooth.

**Foam aliasing:** foam pattern fbm freq 0.55, at t=300 footprint per pixel ~1.5u → sampling at 0.55*1.5 ≈ 0.8 cell/pixel → shimmer; foam distance fade (0.25 at 650, ~0.5 at 400...) partially hides ✓ acceptable.

**Sky cloud aliasing near horizon:** cuv = rd.xz/(rd.y+0.14)*0.5 — as rd.y→0.012, divisor 0.152 → cuv large → high freq → shimmer near horizon; mitigated by cov fade smoothstep(0.012,0.16,rd.y) → clouds fade exactly where freq explodes ✓ well-designed.

**Performance final:** fine with adaptive res.

**Now, is there anything in the brief unaddressed?** 
- large rolling waves several octaves ✓ (6 ridged octaves + warp + LOD)
- foam on crests ✓ (whitecaps + trailing wash)
- dramatic sky dark clouds + low orange sun ✓
- sun reflection ✓ (disc reflection + specular + glitter)
- fresnel ✓
- subtle fog near horizon ✓
- camera gently bobs like a boat ✓ (heave/sway/roll + swell ride)
- rAF timestamp ✓
- fills window, resize ✓
- auto-start ✓
- everything visible in first 30s ✓ (sun lowers slightly, clouds drift, waves roll, boat bobs continuously)
- single HTML, raw WebGL2, no libs ✓

Also "raymarching fragment shader on a full-screen quad" ✓ (full-screen triangle — even better; I'll mention it's a full-screen triangle covering the quad area — the requirement is effectively a fullscreen pass; a triangle is standard. To be safe with the letter of the request, I could emit a quad via 2 triangles / 6 vertices with gl_VertexID → trivial: verts for 6 ids. Let me just do the big-triangle but mention "full-screen triangle (cheaper than a quad, same coverage)". Hmm user said "full-screen quad" — I'll honor intent (covers screen); but to avoid any pedantic mismatch I can generate 6 vertices forming two triangles via gl_VertexID — cost-free. I'll do a proper 2-triangle quad to match the request exactly.

Vertex shader:
```glsl
#version 300 es
void main(){
    // full-screen quad from 6 vertices (two triangles), no buffers needed
    vec2 p = vec2(-1.0);
    if (gl_VertexID == 0) p = vec2(-1.0, -1.0);
    if (gl_VertexID == 1) p = vec2( 1.0, -1.0);
    if (gl_VertexID == 2) p = vec2(-1.0,  1.0);
    if (gl_VertexID == 3) p = vec2( 1.0, -1.0);
    if (gl_VertexID == 4) p = vec2( 1.0,  1.0);
    if (gl_VertexID == 5) p = vec2(-1.0,  1.0);
    gl_Position = vec4(p, 0.0, 1.0);
}
```
✓ drawArrays(TRIANGLES, 0, 6).

**Double-check GLSL reserved / typos in final write-out.** I'll write it carefully now, mentally compiling.

One more consideration: `const mat2 M2` at global scope with constructor of literals — constant expression ✓. But some drivers warn const mat2 in ES 3.0 fine.

`fbm` detail param float; loops i<5.

In waveField the loop `i<6`.

`uTime` float uniform — used in multiple functions ✓.

Precision: highp float declared ✓. Also `precision highp int;`? Not needed.

Let me now also reconsider the exposure & final look numbers once more:

- Sky zenith (0.032,0.052,0.092)*1.25 = (0.04,0.065,0.115) → aces ≈ x*(2.51x+0.03)/(x*(2.43x+0.59)+0.14): for 0.04: num=0.04*(0.1304)=0.00522? wait 2.51*0.04+0.03 = 0.1304 → num 0.005216; den: 0.04*(2.43*0.04+0.59)+0.14 = 0.04*0.6872+0.14=0.16749 → 0.0311 → gamma^(1/2.2) → 0.21. Dark blue-grey zenith ✓.
- Horizon haze away (0.30,0.215,0.175)*1.25=(0.375,0.269,0.219) → aces: for 0.375: num=0.375*(2.51*0.375+0.03)=0.375*0.971=0.364; den=0.375*(2.43*0.375+0.59)+0.14=0.375*1.501+0.14=0.703 → 0.518; g,b similar ~0.43,0.37 → gamma → ~0.74,0.67,0.62 → warm light grey horizon ✓ hazy.
- Near-sun haze (1.05,0.45,0.17)*1.25=(1.31,0.56,0.21) → aces(1.31): num=1.31*(3.29+0.03)=4.35; den=1.31*(3.18+0.59)+0.14=5.08 → 0.856 → gamma 0.93 bright ✓; g: aces(0.56)= (0.56*(1.406+0.03))/(0.56*(1.361+0.59)+0.14)= (0.56*1.436)/(0.56*1.951+0.14)=0.804/(1.232)=0.653→gamma 0.82; b: aces(0.21)=(0.21*(0.557))/(0.56*? compute: 2.51*0.21+0.03=0.557; num=0.117; den=0.21*(2.43*0.21+0.59)+0.14=0.21*1.10+0.14=0.371 → 0.315 → gamma 0.60 → near-sun horizon ≈ (0.93,0.82,0.60) warm cream-orange ✓.
- Water deep *1.25 → ~0.02 → ~0.15 after gamma → dark ✓.
- Specular path: refl glow + spec → bright ✓.

Clouds dark slate (0.040,0.047,0.062)*1.25 → ≈0.05 → aces≈0.045 → gamma 0.24 → dark blue-grey masses vs warm horizon ✓ dramatic contrast ✓.

Foam: (0.92*(0.20+1.15*nl*... )): nl~0.6 → (0.20+0.76*1.15≈?) let me: vec3(1.15,0.62,0.30)*0.6*1.1=(0.76,0.41,0.20)+amb(0.20,0.19,0.185)=(0.96,0.60,0.385)*0.92=(0.88,0.55,0.27)*1.25=(1.10,0.69,0.34) → aces → (0.80,0.60,0.37)→gamma (0.91,0.79,0.63) — warm sunlit foam ✓ but maybe too orange for foam; foam near camera on shadow side: nl uses dot(n,sun): faces toward sun lit warm, away darker: nl min = 0.4−0.6=... dot(n,sun) ∈ [−1,1] → nl∈[0.4−0.6, 0.4+0.6] = [−0.2,1] clamped [0,1] → shadow foam = (0.20,0.19,0.185)*0.92*1.25 ≈ (0.23,0.22,0.21) → gamma ~0.53 grey — good contrast.

Looks coherent.

**Sun reflection disc on water will be near the horizon slightly right?? sun azimuth aligned with camera → centered ✓.**

Now — is there a risk the water looks too uniformly dark in the lower half with sun behind clouds? The broad glow pow(sd,4)*0.55 reflected at grazing adds warm tint over the mid-water ✓; body subsurface towardSun term adds green-orange on crests facing camera when looking sunward ✓.

**Cloud darkness vs sun glow ordering:** glow added before clouds mix → clouds cover glow → glow re-added partially via pow(sd,60)*(1−cov*0.6) — but that's small radius only. Broad glow (pow(sd,4) & pow(sd,28)) fully occluded by clouds — realistic-ish (clouds block glow) but we lose warm bleeding through clouds. Add: after mixing clouds, re-add a fraction of broad glow scaled by (1−cov): 

```
col += vec3(0.95,0.34,0.09) * pow(sd,4.0) * (1.0-cov) * 0.25;
```
Hmm I already add the pow(sd,28) term before clouds; to let clouds glow through: after cloud mix add `col += vec3(1.15,0.50,0.15)*pow(sd,28.0)*cov*0.35;` — glow bleeding through cloud edges — subtle silver-lining bloom. I already have silver lining term in cCol. Enough; skip extra.

Alright. Also `disc` uses cov from branch — cov declared before branch ✓ (init 0).

**Write JS numbers:** dpr cap 2; resScale.

**Testing mentally for GLSL compile errors:**

- `vec2 warp = vec2(vnoise(p*0.8 + vec2(t*0.110, -t*0.085)), vnoise(p*0.8 + vec2(-t*0.075, t*0.130) + 5.2));` ✓ (adjust numbers as chosen)
- waveField: uses M2 ✓.
- `float c = 1.0 - abs(n*2.0−1.0); c*=c; h += (c−0.30)*a*fade;` ✓.

Wait — do I apply fade to the (c−0.30)*a term: yes.

- sunDirection: `float el = 0.125 − 0.075*smoothstep(0.0, 80.0, uTime) + 0.010*sin(uTime*0.47);` — at t large: el→0.05±0.01 ✓ >0 ✓.

- skyColor: all good; note `float hd` uses hdir2.

- traceWater: uses TMAX const ✓.

- main: uses gl_FragCoord ✓; note uRes as vec2 ✓.

One syntax check: `vec3 rt = cr*rt0 + sr*up0;` ✓.

`vec3 rd = normalize(uv.x*rt + uv.y*up + 1.35*fw);` — uv defined before ✓.

Order in main: compute uv first, camera second ✓ (uv independent).

**Potential issue: loop with `break` inside traceWater nested bisection — fine.**

**Mobile: highp support in fragment guaranteed in WebGL2 ✓.**

Now the explanation text after code: brief — cover architecture (fullscreen quad, raymarched heightfield with LOD, bisection, fog, fresnel, foam, sky, boat bob, adaptive resolution). Keep concise.

Let me also double check the fbm usage for `fpat` etc. with detail 3.0 — loop 5 with break at i≥3 ✓.

One more: `hash12` — standard Dave Hoskins hash; fine.

`vnoise` quintic — ✓.

Also guard `if (rd.y > -0.0012) return -1.0;` in traceWater — but for water shading rays only; sky rays handled by tHit<0 ✓.

Edge: camera pitch sway up → top pixels sky ✓.

I think there might be one subtle problem: the early plane-skip uses H_max=3.7 for AMP=2.5: max field 1.429*2.5 = 3.572 < 3.7 ✓.

And camY min: 4.8 + ride*0.24 min: ride min = −1.53*... field min = (−0.30*2.042)=−0.613 → world −1.53; ride*0.24 = −0.37; heave min −0.26 → camY ≥ 4.17 > 3.7 ✓ clearance above max crest = 4.17−3.57 = 0.60 ✓ OK.

Also `if (t > TMAX) return -1.0;` after t0 check ✓.

heave: 0.16*sin(1.31t)+0.10*sin(2.17t+1.4): amplitude 0.26 ✓ gentle; roll 0.075 max rad ≈ 4.3° ✓; pitch sway 0.042 ✓; yaw sway 0.063 ✓ — gentle boat.

Ride uses waveField(camXZ, tm, 2.0)*AMP*0.24 → range ±0.37 world — subtle heave synced with swell ✓.

Hmm — should the camera bob be more noticeable? "gently bobs as if on a boat" — heave ±0.26 + roll ±4° + swell-follow ±0.37 → total vertical ±0.6 — visible gentle motion ✓ plus pitch. Good.

**Also let me add slight forward drift? camXZ sway covers it; keep.**

Now write everything for real. Also include a tiny bit of sun-lit rim on wave crests facing camera? The spec handles.

Let me also make sure `uv` aspect: uv.x range ±aspect (≈±0.94 for 16:9... aspect = w/h ≈ 1.78 → uv.x ∈ ±1.78). focal 1.35 → hfov ≈ 2*atan(1.78/1.35) ≈ 106° wide ✓ immersive; vertical half-angle atan(1/1.35)=36.5° ✓.

Wait vertical: uv.y ∈ ±1 → tan(halfV)=1/1.35 → halfV 36.5° → vfov 73° ✓ good.

**Dither hash:** `hash12(gl_FragCoord.xy + vec2(fract(tm*13.7)*100.0))` — animate to average dither over frames ✓.

**Final check of adaptive logic units:** emaMs vs thresholds 27/14 ms ✓.

Also `powerPreference: 'high-performance'` ✓.

**Write final HTML now.** Also `<meta name="viewport">` for mobile ✓. Title.

Let me write the fragment shader as one template literal with careful formatting.

Additional last look at fbm used in skyColor for clouds — `fbm(cuv*0.85 + w1 + 3.1, detail)` — vec2+float+vec2 ✓ ok.

dens = n1*0.72 + n2*0.45; n1∈[0.09,0.91] typical → dens ∈ [0.13, 0.88] mean 0.43*1.17≈0.50; cov smoothstep(0.35,0.73): coverage ≈ 45% varying ✓.

`lit*(1.15−dens)`: dens 0.7 → 0.45; lit near sun 1.0 → mix 0.3→... lit*0.45=0.45 → clouds 45% warm near sun, darker away ✓.

Silver lining factor ✓.

OK also water `crest01 = clamp(p.y*0.30, 0.0, 1.0)` with p.y∈[−1.5,3.6].

Foam threshold with AMP 2.5: crest tops ~3.3–3.5; smoothstep(2.15, 3.15, p.y) → foam on top ~30% of highest crests, gated by fpat ✓. Trail smoothstep(1.1, 2.3, p.y).

Subsurface `towardSun*crest01*(1−fres)` — near camera looking down fres small, crest01 mid → adds green glow on crests toward sun ✓.

Let me also add faint sun-warm wrap on water: skip.

Also — `spec` uses r computed with jittered n ✓ sparkles.

Everything set. Write the code.

Actually one more numeric check on `float fog = 1.0 − exp(−tHit*0.0062);` near camera t=6 → 0.037 — slight haze even close (fine, atmospheric). 

And horizon: at t=700 fog=0.987 ✓.

Also make sure water at bottom edge (t≈2–4): fog≈0.01 ✓ crisp detail.

**JS init ordering:** compile fragment may take ~100ms — fine before first frame.

Let me also double check `gl.viewport` set on resize before first draw ✓.

**Write it.**

One more: I should double-check `smoothstep(0.99930, 0.99990, sd)` — highp float precision: sd computed from dot of normalized vectors ~1−1e-4 — float precision ~1e-7 relative — fine.

`pow(sd, 340.0)` — sd up to 1.0; pow(1.0,340)=1 ✓; sd slightly >1 impossible (clamped) ✓.

**Cloud temporal drift near t=0 vs 30:** w1 = tm*0.028 → 0.84 shift over 30s in cuv*0.85 domain — visible crawl ✓. Sun elevation drop from 0.125→~0.077 (13°→4.4°... compute: smoothstep(0,80,30)=t=30: x=0.375 → 3x²−2x³ = 3*0.1406−2*0.0527 = 0.4219−0.1055=0.316 → el=0.125−0.0282+0.010*sin(14.1 rad)= sin(14.1)= sin(14.1−4π=1.434)=0.990 → +0.0099 → el≈0.107? Hmm wait 0.125−0.075*0.4219 = 0.125−0.0316=0.0934 +0.0099 = 0.103. At t=0: 0.125+0=0.125... plus 0.010*sin(0)=0 → 0.125. So el goes 0.125→0.103 by t=30 — only a small dip then the sine wobbles. The smoothstep is slow; visually sun barely moves. Add a bit more motion: increase the sine amplitude/frequency? A slow visible descent: el = 0.135 − 0.10*smoothstep(0.0, 45.0, uTime) → t=0: 0.135 (7.7°), t=30: 0.135−0.085*0.87... smoothstep(0,45,30): x=0.667→3*0.444−2*0.296=1.333−0.593=0.741 → el = 0.135−0.0667=0.068 (3.9°) → t≥45: 0.06−? 0.135−0.075=0.06 → settles 3.4° — nice visible sunset descent within the 30s window ✓ then holds low + tiny sine wobble 0.008*sin(0.4t). After 45s sun stays low ✓ scene continues indefinitely (loop of waves). Adopt: `float el = 0.135 - 0.075*smoothstep(0.0, 45.0, uTime) + 0.008*sin(uTime*0.4);` min el ≈ 0.06−0.008=0.052 ✓ above horizon ✓.

Also as sun lowers, glitter path brightens/lengthens automatically ✓ dynamic within window ✓.

Cloud drift ✓ waves ✓ boat bob ✓ — the 30s window shows: dramatic descend of sun, rolling swell with whitecaps forming/breaking, drifting cloud shadows... cloud shadows on water? Not modeled (reflection only) — skip.

Done planning. Write final answer: single HTML block + short explanation. Also make sure no external anything. Comments in English (user language). 

Let me write the complete code now, being extra careful with GLSL syntax.

```glsl
#version 300 es
precision highp float;

uniform float uTime;
uniform vec2  uRes;

out vec4 fragColor;

const float AMP  = 2.5;    // wave amplitude in world units
const float TMAX = 800.0;  // far distance

const mat2 M2 = mat2(1.68, 1.18, -1.18, 1.68); // rotate + ~2.05x lacunarity

float hash12(vec2 p){
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

float vnoise(vec2 p){
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f*f*f*(f*(f*6.0 - 15.0) + 10.0);
    float a = hash12(i);
    float b = hash12(i + vec2(1.0, 0.0));
    float c = hash12(i + vec2(0.0, 1.0));
    float d = hash12(i + vec2(1.0, 1.0));
    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

float fbm(vec2 p, float detail){
    float v = 0.0;
    float a = 0.5;
    for (int i = 0; i < 5; i++){
        float fade = clamp(detail - float(i), 0.0, 1.0);
        if (fade < 0.004) break;
        v += a * vnoise(p) * fade;
        p = M2 * p;
        a *= 0.55;
    }
    return v;
}

// ridged multi-octave ocean heightfield; world height = AMP * result
float waveField(vec2 pos, float t, float lod){
    vec2 p = pos * 0.045;                       // base wavelength ~ 22 units
    vec2 warp = vec2(                            // slow domain warp
        vnoise(p * 0.8 + vec2( t * 0.110, -t * 0.085)),
        vnoise(p * 0.8 + vec2(-t * 0.075, t * 0.130) + 5.2));
    p += (warp - 0.5) * 0.9;
    vec2 d = vec2(0.95, 0.38) * (t * 0.30);      // swell drift
    float h = 0.0;
    float a = 1.0;
    for (int i = 0; i < 6; i++){
        float fade = clamp(lod - float(i), 0.0, 1.0);
        if (fade < 0.004) break;
        float n = vnoise(p + d);
        float c = 1.0 - abs(n * 2.0 - 1.0);      // sharp crests, broad troughs
        c *= c;
        h += (c - 0.30) * a * fade;
        p = M2 * p;
        d = M2 * d;
        a *= 0.52;
    }
    return h;
}

vec3 waveNormal(vec2 p, float t, float lod, float eps){
    float h  = waveField(p, t, lod);
    float hx = waveField(p + vec2(eps, 0.0), t, lod);
    float hz = waveField(p + vec2(0.0, eps), t, lod);
    vec2 g = vec2(hx - h, hz - h) * (AMP / eps);
    return normalize(vec3(-g.x, 1.0, -g.y));
}

vec3 sunDirection(){
    float el = 0.135 - 0.075 * smoothstep(0.0, 45.0, uTime) + 0.008 * sin(uTime * 0.4);
    return normalize(vec3(0.26, el, -1.0));
}

vec3 skyColor(vec3 rd, float detail){
    vec3 sun = sunDirection();
    float sd = clamp(dot(rd, sun), 0.0, 1.0);
    float y  = clamp(rd.y, 0.0, 1.0);

    // stormy gradient: dark slate zenith, warm haze at the horizon
    vec3 col = mix(vec3(0.300, 0.205, 0.165), vec3(0.032, 0.052, 0.092), pow(y, 0.62));
    col += vec3(0.95, 0.34, 0.09) * pow(sd, 4.0)  * (1.0 - y * 0.55) * 0.55;
    col += vec3(1.15, 0.50, 0.15) * pow(sd, 28.0) * 0.85;

    float disc = smoothstep(0.99930, 0.99990, sd);
    float cov = 0.0;
    if (rd.y > 0.012){
        vec2 cuv = rd.xz / (rd.y + 0.14) * 0.5;
        vec2 w1 = vec2( uTime * 0.028,  uTime * 0.010);
        vec2 w2 = vec2(-uTime * 0.043,  uTime * 0.017);
        float n1 = fbm(cuv * 0.85 + w1 + 3.1, detail);
        float n2 = fbm(cuv * 2.10 + w2 + 17.7, detail * 0.75);
        float dens = n1 * 0.72 + n2 * 0.45;
        cov = smoothstep(0.35, 0.73, dens) * smoothstep(0.012, 0.16, rd.y);
        float lit = clamp(0.10 + pow(sd, 3.0) * 1.3, 0.0, 1.0);
        vec3 cCol = mix(vec3(0.040, 0.047, 0.062), vec3(0.90, 0.36, 0.13),
                        lit * clamp(1.15 - dens, 0.0, 1.0));
        // sunward silver lining on the cloud edges
        cCol += vec3(1.00, 0.46, 0.16) * pow(sd, 5.0)
              * smoothstep(0.30, 0.52, dens) * (1.0 - smoothstep(0.52, 0.78, dens)) * 0.9;
        col = mix(col, cCol, cov);
    }
    col += vec3(6.5, 2.7, 0.95) * disc * (1.0 - cov * 0.85) * 2.6;
    col += vec3(1.10, 0.48, 0.16) * pow(sd, 60.0) * (1.0 - cov * 0.6);

    // haze band that hugs the horizon (also used as fog colour)
    vec3 sunAz = normalize(vec3(sun.x, 0.0, sun.z));
    vec2 hdir = rd.xz / max(length(rd.xz), 1e-4);
    float hd = clamp(dot(hdir, sunAz), 0.0, 1.0);
    vec3 haze = mix(vec3(0.300, 0.215, 0.175), vec3(1.05, 0.45, 0.18), pow(hd, 3.0) * 0.9);
    col = mix(col, haze, (1.0 - smoothstep(0.0, 0.18, y)) * 0.9);
    return col;
}

float traceWater(vec3 ro, vec3 rd){
    if (rd.y > -0.0012) return -1.0;             // camera always rides above the crests
    float t = max(0.05, (ro.y - 3.7) / (-rd.y)); // skip the empty band above the waves
    if (t > TMAX) return -1.0;
    float tp = t;
    for (int i = 0; i < 200; i++){
        vec3 p = ro + rd * t;
        float lod = clamp(6.0 - t * 0.012, 2.0, 6.0);
        float h = p.y - waveField(p.xz, uTime, lod) * AMP;
        if (h < 0.0){
            float a = tp;
            float b = t;
            for (int j = 0; j < 5; j++){
                float m = 0.5 * (a + b);
                vec3 pm = ro + rd * m;
                float hm = pm.y - waveField(pm.xz, uTime, clamp(6.0 - m * 0.012, 2.0, 6.0)) * AMP;
                if (hm < 0.0) b = m; else a = m;
            }
            return 0.5 * (a + b);
        }
        tp = t;
        t += max(h * 0.35, 0.05 + t * 0.011);
        if (t > TMAX) return -1.0;
    }
    return -1.0;
}

vec3 aces(vec3 x){
    return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0);
}

void main(){
    float tm = uTime;
    vec2 uv = (2.0 * gl_FragCoord.xy - uRes) / uRes.y;

    // --- boat camera: slow sway, swell-riding heave, gentle roll ---
    vec2 camXZ = vec2(1.8 * sin(tm * 0.071), 1.4 * sin(tm * 0.052 + 2.0));
    float ride  = waveField(camXZ, tm, 2.0) * AMP;
    float heave = 0.16 * sin(tm * 1.31) + 0.10 * sin(tm * 2.17 + 1.4);
    vec3 ro = vec3(camXZ.x, 4.8 + ride * 0.24 + heave, camXZ.y);

    float yaw   = 0.255 + 0.045 * sin(tm * 0.21) + 0.018 * sin(tm * 0.43 + 1.0);
    float pitch = -0.105 + 0.028 * sin(tm * 0.83 + 0.5) + 0.014 * sin(tm * 1.57);
    float roll  = 0.055 * sin(tm * 0.61 + 0.7) + 0.020 * sin(tm * 1.13);

    float cp = cos(pitch), sp = sin(pitch);
    vec3 fw  = vec3(sin(yaw) * cp, sp, -cos(yaw) * cp);
    vec3 rt0 = normalize(cross(fw, vec3(0.0, 1.0, 0.0)));
    vec3 up0 = cross(rt0, fw);
    float cr = cos(roll), sr = sin(roll);
    vec3 rt = cr * rt0 + sr * up0;
    vec3 up = -sr * rt0 + cr * up0;

    vec3 rd = normalize(uv.x * rt + uv.y * up + 1.35 * fw);
    vec3 sun = sunDirection();

    float tHit = traceWater(ro, rd);
    vec3 col;

    if (tHit < 0.0){
        col = skyColor(rd, 5.0);
    } else {
        vec3 p = ro + rd * tHit;

        // surface normal (finer detail near, smoothed far)
        float lodN = clamp(7.0 - tHit * 0.010, 3.0, 7.0);
        float eps  = max(0.04, tHit * 0.008);
        vec3 n = waveNormal(p.xz, tm, lodN, eps);
        float near = 1.0 - smoothstep(60.0, 400.0, tHit);
        n.xz += (vec2(vnoise(p.xz * 5.0 + tm * 0.9),
                      vnoise(p.xz * 5.0 + 13.7 - tm * 0.8)) - 0.5) * (0.02 + 0.11 * near);
        n = normalize(n);

        // fresnel + sky reflection
        float cosT = clamp(dot(n, -rd), 0.0, 1.0);
        float fres = 0.022 + 0.978 * pow(1.0 - cosT, 5.0);
        vec3 r = reflect(rd, n);
        r.y = max(r.y, 0.015);
        r = normalize(r);
        vec3 refl = skyColor(r, 2.5);

        // water body: deep teal, greener over the crests, sun-lit subsurface
        float crest01 = clamp(p.y * 0.30, 0.0, 1.0);
        vec3 body = mix(vec3(0.014, 0.056, 0.062), vec3(0.045, 0.200, 0.190), crest01 * 0.55);
        float towardSun = pow(clamp(dot(rd, sun), 0.0, 1.0), 3.0);
        body += vec3(0.030, 0.150, 0.125) * towardSun * crest01 * (1.0 - fres);

        col = mix(body, refl, fres);

        // specular sun path + glitter
        float rs = clamp(dot(r, sun), 0.0, 1.0);
        float spec = pow(rs, 340.0) * 2.4 + pow(rs, 36.0) * 0.30;
        col += vec3(1.25, 0.55, 0.22) * spec * (0.35 + 0.65 * fres);

        // foam: broken whitecaps on the crests + elongated trailing wash
        float crest = smoothstep(2.15, 3.15, p.y);
        float fpat = fbm(p.xz * 0.55 + vec2(0.95, 0.38) * (tm * 0.22) + 7.7, 3.0);
        float foam = crest * smoothstep(0.38, 0.75, fpat);
        vec2 fd = normalize(vec2(0.95, 0.38));
        vec2 st = vec2(dot(p.xz, fd), dot(p.xz, vec2(-fd.y, fd.x)));
        float trailN = fbm(vec2(st.x * 0.055 + tm * 0.16, st.y * 0.42) + 4.7, 3.0);
        float trail = smoothstep(1.10, 2.30, p.y) * smoothstep(0.46, 0.78, trailN) * 0.65;
        foam = clamp(foam + trail, 0.0, 1.0);
        foam *= 0.25 + 0.75 * (1.0 - smoothstep(120.0, 650.0, tHit));

        float nl = clamp(dot(n, sun) * 0.6 + 0.4, 0.0, 1.0);
        vec3 foamLit = vec3(0.92, 0.87, 0.80) * (vec3(0.20, 0.19, 0.185) + vec3(1.15, 0.62, 0.30) * nl * 1.1);
        col = mix(col, foamLit, foam * 0.88);

        // haze into the horizon
        vec3 hazeC = skyColor(normalize(vec3(rd.x, 0.02, rd.z)), 1.0);
        float fog = 1.0 - exp(-tHit * 0.0062);
        col = mix(col, hazeC, fog);
    }

    col *= 1.25;
    vec2 vuv = gl_FragCoord.xy / uRes - 0.5;
    col *= 1.0 - 0.30 * dot(vuv, vuv);
    col = aces(col);
    col += (hash12(gl_FragCoord.xy + fract(tm * 0.13) * 541.0) - 0.5) * (1.0 / 160.0);
    col = pow(max(col, 0.0), vec3(1.0 / 2.2));
    fragColor = vec4(col, 1.0);
}
```

Check: `near` variable name conflicts? fine. `hdir` vec2 in skyColor ✓.

Hmm — in main I declare `vec3 sun = sunDirection();` and also `sun` used in skyColor internally — no conflict (separate scopes) ✓.

One thing: `float near` — `near` isn't reserved ✓.

Check traceWater first iteration: tp = t (== t0). h at t0 ≥ 0 as proven (p.y=3.7 ≥ 3.57 max) ✓ bisection interval valid.

But wait — the max wave check used AMP=2.5: field max 1.429*2.5 = 3.572 < 3.7 ✓. And with lod<6 fade reduces ✓.

If ro.y−3.7 < 0 → t = max(0.05, negative) = 0.05 ✓ and tp=0.05; h at 0.05: p.y = ro.y−tiny... ro.y ≥ 4.17 always ✓ h>0 ✓.

Alright. Also confirm that at grazing angles with t0 large, tp initialized to t0 ✓.

Also potential: h*0.42→0.35 step factor used — I wrote 0.42 in final? I typed `t += max(h * 0.42, ...)` — keep 0.42? Earlier discussed 0.35 for safety. Use 0.40 compromise. Fine: 0.40.

Iteration count 200 might be heavy for the grazing band; estimated ~120 max typical — 200 cap rarely reached. OK.

**Now double-check the reflection call `skyColor(r, 2.5)` — inside, `disc` etc — fine. And `skyColor(hazeDir, 1.0)` — fbm detail 1.0/0.75 → 1 octave each ✓ cheap.

**Sun glare when looking directly at sun through gap:** disc HDR 6.5*2.6*1.25 ≈ 21 → aces → ~1 white core; edges glow ✓.

**Possible worry: the horizon line might show a bright seam because sky just above horizon includes cloud-branch at rd.y slightly >0.012 with cov fade — continuous ✓; below horizon fogged water → haze — colors: sky at y=0.013: gradient warm + haze mix 0.87 vs water fog hazeC at y=0.02 — nearly identical ✓.

**Check `smoothstep(0.012, 0.16, rd.y)` at rd.y=0.013 → ~0.0002 ✓ no pop.

**Check glitter aliasing:** pow(rs,340) with jittered normals — sparkles twinkle; temporal AA none — acceptable aesthetic (glitter naturally sparkles).

**Performance: sky pixels (top ~36%) do fbm 5+~4 octaves + gradient — cheap ✓.**

**Now the JS.** Also add `gl.useProgram` after link ✓. Draw.

Also `gl.disable(gl.DEPTH_TEST)` default off ✓; no clear needed (full-screen write) but do gl.clear? Not needed since fullscreen tri overwrites every pixel ✓ (alpha:false).

**Potential driver nuance:** `gl_VertexID` in vertex shader requires ES 3.00 — ✓ WebGL2.

Also — vertex shader needs `#version 300 es` first line ✓; no precision needed in vertex (default highp) ✓.

Let me finalize the whole document, also double-check template literal escaping — GLSL contains backticks? No. Contains `${`? No. ✓

Fallback: also catch shader compile errors and display.

Also handle initial `resize()` before program? Order: init GL → resize → rAF ✓.

`window.devicePixelRatio` read each resize ✓.

I'm also going to add `image-rendering` nothing. Canvas CSS width 100vw/100vh — but also `body{height:100%}`? Using fixed positioning via CSS: `#glcanvas{position:fixed; inset:0; width:100%; height:100%;}` — simplest: canvas absolutely fills. Then innerWidth/innerHeight = canvas CSS size ✓.

Wait — with `position:fixed; inset:0;` plus explicit width/height CSS 100% — fine.

Now write the final deliverable. Also brief explanation afterwards (per my practice of including a short implementation note).

Small extra flourish for the "signature moment": the sun slowly sinking while swell rolls — plus maybe a subtle god-ray-ish glow column? The specular path is that moment. Good.

Double-check the `resize` math when resScale changes — canvas.width changes → viewport updated ✓ uniform uRes updated every frame ✓.

Edge: `emaMs` init 16.7 → after compile jank first frames long → cooldown 120 frames ≈ 2s skip ✓ then if still slow → downscale ✓.

One more thing: `if (--cooldown < 0)` executes every frame decrementing — fine.

Let me also expose a `FAIL` overlay style with dark backdrop.

Also worth setting `gl.getExtension('EXT_color_buffer_float')`? Not needed.

**Write final answer.**

Also confirm: no external resources ✓; no fonts ✓; single file ✓; auto-start ✓.

For the explanation: concise bullet summary. Let me now produce the answer.

One last syntax sweep of the fragment shader for typos — I'll rewrite cleanly in the final answer, double-checking:
- All `float` literals with decimal points where mixed with ints in float ops (e.g., `float(i)`, `0.72`, etc.) ✓
- `mix(vec3, vec3, float)` ✓
- `smoothstep(float,float,float)` ✓
- No `#` extension needed.
- `pow(vec3? no — pow(y,0.62) float ✓; pow(sd,4.0) float ✓.
- `vec3 col += vec3 * float` ✓.
- ternaries none.

In fbm: `v += a * vnoise(p) * fade;` ✓.

In waveField: variable `n` float vs later `n` in main vec3 — different scopes ✓.

traceWater uses variable name `a` and `b` and also `a` reused... inside bisection `float a = tp;` shadows nothing ✓ (outer loop has no `a`).

In main: `float cr` vs `float crest01` etc ✓; `rt`, `up` ✓.

`vec2 fd`, `vec2 st` ✓.

`vec3 foamLit` ✓.

Also `hazeC` computed with `normalize(vec3(rd.x, 0.02, rd.z))` ✓.

OK, writing final response now. Also keep comments moderate.

Also one more consideration on the fade in fbm when detail high (5.0): clamp(5−i) all 1 ✓ full 5 octaves.

And `skyColor(rd, 5.0)` for main sky: detail 5 → n1 5 octaves, n2 detail 3.75 → 4 octaves ✓.

Double check `smoothstep(0.99930, 0.99990, sd)` — sd up to 1: at exact sun center disc=1 ✓ edge soft over 0.0006 in dot ≈ 1.4°→0.9°... wait cos 0.9993 = 2.14°, cos 0.9999 = 0.81° — soft edge band ~1.3° wide — quite soft/large; combined with glow looks like low hazy sun ✓.

Also ensure the sun disc is drawn even when cov>0 partially: `(1.0 − cov*0.85)` min 0.15 ✓.

Final: heave/rf checks done. Compose answer with the HTML then a concise explanation.

Actually — one more important review of the trace early-exit interplay with the horizon: rays with rd.y ∈ (−0.0012, 0): t0 = (ro.y−3.7)/0.0012 up to ~ (6−3.7)/0.0012 ≈ 1900 > TMAX → return −1 → sky. rd.y=−0.002 → t0=1150 > 800 → sky. rd.y=−0.005 → t0=460 <800: march: floor at 460 = 5.1/step → reaches 800 in ~65 steps ✓ then return −1 unless hit. Water at t≈500+ is fog 0.95+ — invisible difference ✓ no seam.

rd.y=−0.01: t0=230; descends: from p.y 3.7 at 230, drop 0.01/unit: reaches mean surface ~1.0 at t≈540; crest hits earlier ~ t 300–400 (p.y 2.7–3.0 vs lod-flattened field ~1.5–2.6 world) → hits → fog ~0.8–0.95 → hazy distant water ✓.

Great. Also the far water color = mix(waterCol, haze, 0.95) — 5% water → slightly darker than sky right at horizon → a faint horizon line — desirable ✓.

Also check `foam *= 0.25 + 0.75*(1−smoothstep(120,650,tHit))` — distant foam fades to 25% ✓.

Now finalize. For the recording window: everything's live from t=0 ✓.

Write the answer.