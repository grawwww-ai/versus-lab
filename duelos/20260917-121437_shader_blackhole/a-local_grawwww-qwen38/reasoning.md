The user wants a single HTML file that includes a WebGL2 fragment shader that renders a black hole. Need to write a ray-marching style lensing shader.

Approach: full-screen quad, per-pixel ray direction (camera orbits/tilts with time). Use simple geodesic approximation: iterative ray bending — at each step, pull ray direction toward the black hole (Newtonian-like force ~ -1.5 r_s * h2 / r^3, the photon orbit approximation). Common trick: iterate position += dir * dt, bend dir with force = -1.5 * r_s * h2 / r^3. If r < r_s, it's the event horizon (black). Track when the ray crosses the equatorial plane to sample the accretion disk: use signed distance of y to 0; if it crosses, sample the disk color as a function of radius and angle (with Doppler-like brightness asymmetry, noise for turbulence, inner edge white-hot, outer red).

Stars: if the ray escapes (r > large, or max iteration count), sample a hash-based starfield from the final direction.

Photon ring: thin bright ring at r ~ 1.5 r_s — add a glow based on distance from the photon sphere radius.

Time: performance.now from rAF.

Resize: canvas width/height = window inner size, gl.viewport.

Let's write the shader.

```glsl
#version 300 es
precision highp float;
uniform vec2 u_res; uniform float u_time; out vec4 fragColor;

float hash(vec3 p){ p = fract(p*0.3183099 + 0.1); p *= 17.0; return fract(p.x*p.y*p.z*(p.x+p.y+p.z)); }
float noise(vec3 p){ ... trilinear ... }
float fbm(vec3 p){ fbm of a few octaves; }
```

Disk function: given the crossing point (x,z, y=0 plane, sign of crossing), radius r = length(vec2), angle a. Temperature gradient: t = smoothstep(outer, inner, r). Color: mix(red, orange-white, t). Turbulence: fbm of (angle * something, radius, time * rotSpeed) — make it streaks: sample noise at (atan + time*omega(r), r), omega is a Kepler-like 1/r^1.5.

Brightness asymmetry: Doppler — dot product of disk tangent velocity and ray direction; but the ray is bent; approximation: brightness *= 0.5 + 0.5*cos(a - camAngle) or so. Simpler: brightness *= mix(0.35,1.6, 0.5+0.5*sin(a + camAz)).

Photon ring: after the loop, if closest approach r_min is near 1.5, add a glow: ring = exp(-abs(r_min - 1.5)*k) — but this also includes the horizon; horizon is pitch black. So: if captured (r < 1.0), return black (maybe with a tiny photon ring contribution if r_min is near 1.5? The photon ring is at r=1.5, the captured ray orbits near there; add a small additive term).

Let's set r_s = 1.0 (horizon). Photon sphere 1.5. Disk from about 1.5 to 6.0 (inner edge 2.0, ISCO is 3 r_s = 1.5 in units of r_s; inner 1.5, outer 6).

Ray stepping: N=200 steps? adaptive dt = 0.05 * ... use dt = 0.03, max ~200 iterations; escape if r > 20.

Force: dir += (-1.5 * h2 / r^3) * rhat * dt, where h2 = length(cross(dir, rvec))^2 (angular momentum per unit mass squared). This is the standard photon geodesic integrator.

Camera: position orbits: ang = u_time * 0.05; radius ~9; tilt: pitch = 0.15 + 0.1*sin(time*0.07). Ray direction from a view matrix.

Crossing of the y=0 plane: track previous y; if prevY*y<0 and r is between r_inner and r_outer and the ray hasn't been captured yet, sample the disk. Accumulate color with alpha? The ray may cross multiple times (upper image, lower image) — add a dimmer contribution per crossing with an attenuation factor (e.g., first crossing is full, later crossings are 0.35). Use a count.

Also the disk has some vertical thickness — no problem.

Stars: final dir d; starfield: cell hash, star = pow(hash, ...) threshold, plus faint nebula fbm. Also lensing: since d is the bent direction, this is handled automatically.

Background: dim red/blue nebula fbm, stars: hash on a cell of d * scale; star brightness spikes.

Color: gamma/correction: pow(color, 1/2.2), tonemap like 1-exp(-c*k).

Camera matrix:
```
float ca = u_time*0.06;
vec3 camPos = vec3(cos(ca)*10.0, 0.0, sin(ca)*10.0);
float pitch = 0.18 + 0.10*sin(u_time*0.05);
vec3 target = vec3(0);
vec3 fwd = normalize(target - camPos);
vec3 right = normalize(cross(fwd, vec3(0,1,0)));
vec3 up = cross(right, getting fwd);
```
up = normalize(cross(right, fwd))? right = normalize(cross(fwd, up0)); up = cross(right, fwd)? Actually up = cross(right, fwd) points to… let's compute: right = normalize(cross(fwd, vec3(0,1,0))) is horizontal. up = cross(right, fwd)? cross(right, fwd): if fwd is -z, right is -x… let's verify: standard lookAt: f = normalize(target - eye); s = normalize(cross(f, up_world)); u = cross(s, f). So u = cross(s, f). Good.

Ray: d = normalize(fwd + (uv.x + tan(pitch)*uv.y… simpler: d = normalize(fwd + right*uv.x*tanfov + up*uv.y*tanfov). The tilt is already baked into fwd because we set camPos y? Let camPos.y = sin(pitch)*dist, and also add a small extra tilt via the up coefficient. Simpler: camPos = (cos ca * R, sin(pitch)*R, sin ca * R), target is the origin → fwd has a pitch component. This gives orbit + tilt.

Aspect: uv = (2*(gl_FragCoord.xy)/res -1); uv.x *= res.x/res.y.

fov: tanHalf = 1.2 or so (wide).

Disk sampling at the crossing point:
```
float r = length(pos.xz); // y≈0
float a = atan(pos.z, pos.x);
float ro = 6.0, ri = 1.6;
// radius gradient
float t = clamp((ro - r)/(ro - ri), 0.,1.);
// temperature
vec3 hot = vec3(1.0,0.98,0.92); // white-hot
vec3 warm = vec3(1.0,0.45,0.1); // orange
vec3 cool = vec3(0.5,0.05,0.02); // deep red
vec3 col = mix(cool, warm, smoothstep(0.0,0.5,t));
col = mix(col, hot, smoothstep(0.55,1.0,t));
// streak turbulence
float omega = 0.6 / pow(r, 1.5); // Kepler
float ang2 = a + u_time * omega;
float streak = fbm(vec3(cos(ang2), sin(ang2), r) * 3.0 ... 
```
Hmm — to make streaks rotating with angular speed, sample noise in a rotating frame: n = fbm(vec3(a*2.0 + time*omega, r*1.5, 0)?) but a has a seam at ±π. Better: use vec2(cos a, sin a) in rotating coordinates: p = a rotation matrix by time*omega applied to (cos a, sin a)? That is, angle' = a - time*omega; use (cos(angle'), sin(angle'), r).

fbm(vec3(cos(angle'), sin(angle'), r)*2.5). Streak pattern: amplify in the angular direction: fbm(vec3(cos a' * 3.0, sin a' * 3.0, r*4.0)).

Brightness: base = pow(t, 1.5) or so; multiply by (0.4 + 0.6*streak), plus fine turbulence: another fbm at high frequency.

Doppler: velocity direction at the crossing: tangent = vec2(-sin a, cos a) (prograde, same sign as time*omega? omega is positive, and a + time*omega is constant → material moves in +a direction). dot product with the ray's horizontal direction: dop = dot(normalize(vec2(raydir.x, raydir.z)), tangent). brightness *= 0.6 + 0.9*dop, and color is slightly blueshifted/redshifted: col *= mix(vec3(1.05,0.9,0.75), vec3(0.8,0.9,1.1), 0.5+0.5*dop)? Keep it subtle.

Edge fade: alpha near ri and ro: fade = smoothstep(ri, ri+0.15, r) * (1-smoothstep(ro-0.8, ro, r)).

Multiple crossings: dim factor per crossing: first is 1.0, then 0.3, 0.1. Use int crossCount; atten = pow(0.35, crossCount).

Add diskCol += atten * col * brightness.

Escape: r > 25 → sample sky using the current dir (normalized).

Capture: r < 0.95 → break, black.

Photon ring: track rmin = min(rmin, r). After the loop, if captured, or always: ring contribution = exp(-(abs(rmin - 1.5)) / 0.06)? Rays that orbit near 1.5 and escape or get captured → thin ring. Add to color: ringCol = vec3(1.0,0.7,0.4) * ring * 0.8, but only when the ray actually comes close: the magnitude of rmin-1.5. exp(-abs(rmin-1.5)*25). If rmin > 10, the ring term is ~0 anyway, but exp(-8.5)*… is small but nonzero; clamp: only if rmin < 3.

Star function:
```
vec3 sky(vec3 d){
  vec3 col = vec3(0);
  // nebula
  float neb = fbm(d*3.0 + 5.0);
  col += vec3(0.02,0.03,0.05)*pow(neb,2.0)*2.0;
  // stars: two layers
  vec3 p = d*90.0;
  vec3 id = floor(p);
  float h = hash(id);
  if(h > 0.995){
     // star inside a cell; position is fract
     ... 
  }
```
Simplest star: brightness = pow(hash, something) — typical:
```
float stars(vec3 d, float scale){
  vec3 p = d*scale;
  vec3 i = floor(p);
  float h = hash3(i);
  // radial falloff
  ... 
```
Alternative classic: star = pow(hash, 300) * step threshold; but point-like. Do it this way: h = hash; star = smoothstep(0.997, 1.0, h) — that's a random per-cell value, not a point. Better: put the point at the cell center: distance to the point: f = fract(p)-0.5; star = h * exp(-dot(f,f)*400); then col += star * color varying with h2. Two layers of different scale, plus a tiny time twinkle? not needed.

hash3: use hash(vec3) with a float return.

Tonemap: col = col/(1+col)? or 1-exp(-col*1.5); then pow(1/2.2).

Performance: 200 steps × 2 fbm (5 octaves) each at the crossing (rare) + sky fbm at the end — no problem.

JS: standard boilerplate, check for webgl2 context existence, full-screen triangle or quad.

Let's write the final code.

fbm:
```
float fbm(vec3 p){
  float f=0.; float a=0.5;
  for(int i=0;i<4;i++){ f+=a*noise3(p); p*=2.03; a*=0.5;}
  return f;
}
```
noise3 is trilinear with hash12/hashes.

Loop details:
```
vec3 ro_ = camPos; // start slightly outside
vec3 rd = raydir;
float rmin = 1e9;
vec3 col = vec3(0);
bool hit=false;
int cross = 0;
float prevY = ro_.y;
for(int i=0;i<240;i++){
  ro_ += rd * 0.06;
  float r = length(ro_);
  rmin = min(rmin, r);
  if(r < 0.95){ hit=true; break; }
  // plane crossing
  if(prevY*ro_.y < 0.0 && r > 1.55 && r < 6.2){
     float rr = r;
     float a = atan(ro_.z, ro_.x);
     vec3 dc = disk(rr, a, rd);
     col += dc * pow(0.3, float(cross));
     cross++;
  }
  prevY = ro_.y;
  if(r > 22.0){ break; }
  // bend
  vec3 rv = ro_;
  float h2 = dot(cross(rd, rv), cross(rd, rv)); // careful with scale: |r x d| with d roughly unit; fine
  rd -= 1.5*h2/(r*r*r) * rv * 0.06; // wait: force direction: toward center: -1.5 h2/r^3 rhat = -1.5 h2/r^5 * rvec
```
Force: a = -1.5 h2 / r^5 * rvec (since rhat = rvec/r, so -1.5 h2/r^3 * rhat = -1.5 h2/r^4 * rvec / r… let me redo: F = -1.5 h2 r / r^5 = -1.5 h2 rvec / r^5). rd += F*dt.

```
rd -= (1.5*h2/(r*r*r*r*r)) * rv * dt;
rd = normalize(rd); // renormalize
```
dt = 0.06; 240 iterations → 14.4 in straight travel, plus the camera at distance 10, so enough to reach r=22.

Disk function:
```
vec3 disk(float r, float a, vec3 rd){
  float ri=1.6, ro=6.0;
  float t = clamp((ro - r)/(ro - ri), 0.,1.);
  vec3 cool = vec3(0.45,0.04,0.01);
  vec3 warm = vec3(1.0,0.42,0.08);
  vec3 hot  = vec3(1.35,1.25,1.05);
  vec3 col = mix(cool, warm, smoothstep(0.15,0.55,t));
  col = mix(col, hot, smoothstep(0.55,0.95,t));
  float om = 0.9/pow(r,1.5);
  float aa = a - u_time*om; // co-rotating frame
  vec3 sp = vec3(cos(aa), sin(aa), r);
  float turb = fbm(sp*vec3(6.0,6.0,2.0) + 10.0);
  float streak = fbm(sp*vec3(14.0,14.0,4.0) + 30.0);
  float lum = (0.35 + 0.9*turb)*(0.4+1.6*streak*streak);
  lum *= pow(t, 1.4); // hotter near the center
  // doppler
  float tang = dot(normalize(vec2(rd.x, rd.z)), vec2(-sin(a), cos(a)));
  lum *= (1.0 + 1.2*tang);
  col *= (1.0 + 0.35*tang);
  float fade = smoothstep(ri, ri+0.25, r) * (1.0 - smoothstep(ro-0.9, ro, r));
  return col * lum * fade;
}
```

lum *= pow(t,1.4) — t is near 1 at the inner edge → brighter inside. Good, but the outer edge is already dark from color; no problem.

Photon ring: after the loop:
```
float ring = exp(-abs(rmin-1.5)*30.0) * (rmin < 3.0 ? 1.0 : 0.0);
col += vec3(1.0,0.75,0.45)*ring*0.9;
```
Also add a thin bright inner ring for escaping rays.

Sky:
```
vec3 sky(vec3 d){
  float neb = fbm(d*2.5 + vec3(3.7));
  vec3 c = vec3(0.015,0.02,0.035) * neb*neb*6.0;
  c += vec3(0.05,0.04,0.06)*pow(max(fbm(d*4.0+8.0),0.0),3.0)*0.5;
  // stars
  for two layers:
  c += stars(d, 80.0); c += stars(d, 150.0);
}
stars(vec3 d, float s){
  vec3 p = d*s;
  vec3 i = floor(p);
  vec3 f = fract(p)-0.5;
  float h = hash3(i);
  float star = h * exp(-dot(f,f)*350.0);
  float b = smoothstep(0.75,1.0,h)*40.0;
  star = max(star, b*exp(-dot(f,f)*900.0));
  vec3 tint = mix(vec3(0.8,0.9,1.0), vec3(1.0,0.85,0.7), hash3(i+7.0));
  return star*tint;
}
```
Hmm, fract(p)-0.5 is per-axis; the point is at the center of the cell, but the star should be at a random position inside the cell. Random offset: f += (vec3(hash3(i+1.0),hash3(i+2.0),hash3(i+3.0))-0.5)*0.8. Good.

But stars on a spherical direction: no problem.

Tonemap:
```
col = 1.0 - exp(-col*2.0);
col = pow(max(col,0.0), vec3(1.0/2.2));
```
Maybe add a slight vignette.

JS is standard.

Let's write the final HTML.
