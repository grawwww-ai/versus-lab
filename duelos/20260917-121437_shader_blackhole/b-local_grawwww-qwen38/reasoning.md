Need to write a single HTML file with raw WebGL2, full-screen quad, and a fragment shader that simulates a black hole with raymarching / ray tracing. Classic approach: trace rays from camera, compute deflection by iterating Newtonian-style gravity (a = -1.5 h0^2 / r^4), and when the ray crosses the disk plane (z=0), accumulate disk color based on radius, Doppler-ish, and noise.

Let's design the shader.

Constants:
- BH is at origin.
- Event horizon radius: 1.0 (set rh=1.0, photon ring around ~1.5).
- Disk: from r=2.0 to r=8.0, plane z=0.
- Camera: slowly orbits, tilts.

Ray tracing:
```
vec3 ro (camera position), vec3 rd (ray direction)
vec3 pos = ro;
float t = 0.0;
h0sq = length(cross(rd, pos))^2;
for i in 0..300:
  r2 = dot(pos,pos); r = sqrt(r2);
  if r < 1.0: black hole (return black), break
  if r > escape radius (e.g., 40): starfield background, break
  a = -1.5*h0sq/r2/r2 * rd? Actually acceleration: a = -1.5*h0sq/r2^2 * normalize(pos)... standard trick: a = -1.5*h0sq/r2/r2 * pos (since pos has length r, so a = -1.5 h0^2/r^4 * (pos/r) → writing a = -1.5*h0sq/r2/r2 * pos gives magnitude 1.5 h0^2/r^3 * ... let's be careful.

Known from "Shadertoy black hole" (e.g. Inigo Quilez style):
a = -1.5*h0sq/r2/r2 * rd? No, the deflection is radial: a = -1.5*h0sq/r2/r2 * normalize(pos). Since |normalize(pos)|=1, and pos/r = normalize(pos). So a = -1.5*h0sq/r2/r2 * (pos/r) = -1.5*h0sq/r2/r2/r * pos. But many shadertoys do:

float r2 = dot(pos,pos);
float r = sqrt(r2);
vec3 a = -1.5*h0sq/r2/r2*rd?

Let me recall the actual famous "Black Hole" by tmr (shadertoy 4vrXuD?) or "The Black Hole" (mwKXWG). A common one:

```
vec3 p = ro + rd*t;
vec3 a = -1.5*h0sq/r2/r2*rd; // hmm
```

Actually in "Black Hole" by "iq"? The standard is:

```
float r = length(p);
vec3 a = -1.5*h0sq/r/r/r/r*r? 
```

Let's just do the math: acceleration direction = radial = -normalize(p). Magnitude = 1.5*h0sq/r2 (this is the standard effective formula, with a = -1.5 h0^2 / r^3 in direction units? whatever). So a = -1.5*h0sq/r2/r2 * (-p/r) → a = -1.5*h0sq/(r2*r) * (-p) = 1.5*h0sq/(r2*r)*p? No:

a = - (1.5*h0sq/r3) * normalize(p) = -1.5*h0sq/r3 * p/r = -1.5*h0sq/(r2*r)*p. Hmm, but common code writes: a = -1.5*h0sq/r2/r2 * (-rd)? Not that.

Let's just write it cleanly:

```
vec3 p = pos;
vec3 v = rd;
float t = 0.0;
float h0sq = length(cross(rd, pos))*length(...); // h0sq = dot(p,p) - dot(dot(p,v),v)
```

h0sq = dot(pos,pos) - dot(dot(pos,v),v).

Then in loop:
```
float r2 = dot(p,p);
float r = sqrt(r2);
if(r < 1.0){ ... black hole }
if(r > 30.0){ background }
vec3 a = -1.5*h0sq/(r2*r)*p; // magnitude 1.5 h0sq/r3, direction -p/r
p += v*dt;
v += a*dt;
t += dt;
```
dt is adaptive: maybe dt = clamp(0.15*r, 0.01, 0.5)? Small dt near hole, large far.

Disk crossing: track previous p; if p.z sign flipped and |z| small, and radius within disk range, add emission.

Better: each step, if p.z==0 crossing, compute:
```
if(p.z<0.0){ // crossed
  float frac = old_z/(old_z - new_z);
  vec3 ipos = mix(old, new, frac);
  float r = length(ipos.xy);
  if(r > inner && r < outer){
    // accumulate
  }
}}
```

Disk color: temperature gradient: hot white-orange at inner edge, red at outer edge. Turbulence: fbm noise rotating with angular velocity ~ r^(-1.5). Doppler beaming: brighten the approaching side.

Time rotation: noise sample coord: angle = atan(y,x) - omega(r)*t; use in polar coords for noise: vec2 pc = vec2(r, angle + t*omegar)... to avoid seam at angle wrap, use 3D noise with xy of point rotated around z-axis: rot = cos(omega t) etc. Simpler: rotate disk coord:
```
float rot = t * 1.5 / pow(r, 1.5) // Keplerian
vec2 q = rot2(rot)*ipos.xy;
fbm on q
```
That works, no seam.

Density: fade at inner and outer edges:
```
float dens = smoothstep(inner, inner+0.3, r) * (1.0 - smoothstep(outer-2.0, outer, r));
```

Color:
```
float heat = 1.0 - (r - inner)/(outer-inner);
vec3 col = mix(vec3(0.6,0.05,0.0), vec3(1.0,0.5,0.1), heat);
mix toward white: mix(col, vec3(1.0,0.95,0.9), pow(heat,4.)*?)
```

Brightness: ~ 1/pow(r,2) scaling, multiplied by noise (0.4+0.8*fbm).

Additive accumulation with alpha fade: col *= dens; also attenuate ray by disk (some absorption): att *= 0.5.

Doppler: direction of motion at ipos: tangential = normalize(vec3(-ipos.y, ipos.x, 0)); velocity factor = dot(normalize(camDir?), tangent) — approximate: doppler = 1.0 + k*dot(normalize(ro), tangent)? Actually approaching = dot(ray direction to camera, velocity)... simple: float dop = 1.0 + 0.8*dot(normalize(ro - ipos), tangent); col *= pow(dop, 3); clamp.

Photon ring: on hit, black, but if ray comes close to r~1.5, add thin ring: track minimum r during trace; at end if min r between 1.35 and 1.65, add ring glow: color += ringColor * smoothstep falloff. Simpler: after loop, if escaped or starfield, add ring based on minr:
```
float ring = 0.0;
float minr = 1e6;
// in loop: minr = min(minr, r);
// at end:
if(minr < 1.6 && minr > 1.25) { ring = exp(-pow((minr-1.5)*8.0,2.0)); col += vec3(1.0,0.8,0.5)*ring*1.5; }
```
Hmm, photon ring should be at 1.5 in the black area around horizon. Good enough — gives a thin bright arc.

Background stars: function starfield(vec3 rd): hash-based.
```
vec3 bg = 0;
vec3 p = rd * 300.0;
// grid cells
vec3 ip = floor(p);
hash cell, place a few stars per cell with random position, brightness.
```
Classic method:

```
float star(vec3 p){
 vec3 id = floor(p);
 vec3 f = fract(p)-0.5;
 vec3 h = hash3(id);
 float d = length(f - (h-0.5)*0.8);
 ...
}
```
Simple and cheap: 3 star layers:

```
vec3 stars(vec3 rd){
 vec3 col = 0;
 vec3 p = rd*40.0;
 for(int i=0;i<3;i++){
   float n = hash(floor(p));
   if(n > 0.995) { col += ... }
 }
}
```
Better to do cell-based point stars for sharper look. Let's just do:

```
vec3 bg(vec3 rd){
  // faint nebula
  float neb = fbm(rd*3.0);
  vec3 col = vec3(0.05,0.06,0.1)*neb; // subtle
  // stars
  vec3 p = rd*60.0;
  vec3 ip = floor(p);
  vec3 h = hash33(ip);
  float d = length(p - (ip + 0.5 + (h-0.5)*0.9));
  float star = smoothstep(0.15,0.0,d);
  if(h.z > 0.7){
     col += vec3(0.8,0.9,1.0)*star*pow(h.z,8.0)*...
  }
}
```
But cell size is large (1/60 in rd); stars will be big. p = rd*60, each cell contains 1 star; angular size ~1/60 rad ~ 1°, too big? A star dot of 0.15 within a 1-unit cell → radius 0.0025 in rd units ≈ tiny on screen. OK, fine.

Maybe 2 layers with different scales (60 and 180), and a few larger stars.

Colors: some bluish, some orangeish, based on hash.

Camera:
```
float t = uTime;
float camR = 8.0;
float ang = t*0.05;
// tilt
vec3 ro = vec3(cos(ang)*camR, 1.0 + 0.5*sin(t*0.03), sin(ang)*camR);
target = (0,0,0)
build lookAt.
```
fov: rd = normalize(fwd + u*right*tanHalfFov + v*up*tanHalfFov).

Add a slight roll? "slowly orbits and tilts": ro y varies, that's tilt.

Loop step: 200 iterations with adaptive dt:
dt = clamp(0.02 + 0.05*r, 0.01, 0.6)? near hole r~1 → dt≈0.07; far r=30 → 0.02+1.5 = 1.52 clamped to 0.6. 200*0.6 avg... enough to cover 30 units. 200 iterations, fine for full-screen.

Escape condition: r > 20 && t > 1.0? Or just r > 20.

Disk thickness: disk plane exactly at z=0. Ray can cross z=0 multiple times (multiple images) — naturally handled by loop, add emission each crossing.

Disk alpha: also modulate with a second noise layer.

Let's write the code.

```glsl
#version 300 es
precision highp float;
out vec4 O;
uniform vec2 uRes;
uniform float uTime;

vec3 hash3(vec3 p){
  p = vec3(dot(p,vec3(127.1,311.7,74.7)), dot(p,vec3(269.5,183.3,246.1)), dot(p,vec3(113.5,271.9,124.6)));
  return fract(sin(p)*43758.5453)*2.0-1.0;
}
float hash1(vec3 p){ return fract(sin(dot(p,vec3(12.9898,78.233,37.719)))*43758.5453); }

float noise(vec3 p){
  vec3 i = floor(p); vec3 f = fract(p);
  f = f*f*(3.0-2.0*f);
  // 8 corners
  float n = mix(
    mix(mix(hash1(i+vec3(0,0,0)),hash1(i+vec3(1,0,0)),f.x),
        mix(hash1(i+vec3(0,1,0)),hash1(i+vec3(1,1,0)),f.x),f.y),
    mix(mix(hash1(i+vec3(0,0,1)),hash1(i+vec3(1,0,1)),f.x),
        mix(hash1(i+vec3(0,1,1)),hash1(i+vec3(1,1,1)),f.x),f.y),
    f.z);
  return n;
}
float fbm(vec3 p){
  float a=0.5, s=0.0;
  for(int i=0;i<5;i++){ s+=a*noise(p); p*=2.03; a*=0.5; }
  return s;
}
```

Disk function:
```glsl
vec3 disk(vec3 p, float r, vec3 rd, vec3 ro, float t){
  float inner=1.8, outer=7.0;
  if(r<inner||r>outer) return vec3(0);
  // keplerian rotation
  float rot = 1.2/pow(r,1.5);
  float cs = cos(rot*t), sn = sin(rot*t);
  vec2 q = mat2(cs,-sn,sn,cs)*p.xy;
  float n = fbm(vec3(q*1.6, t*0.3));
  float n2 = fbm(vec3(q*4.0+7.7, t*0.5));
  float dens = 0.15 + 0.85*pow(n,1.5)*(0.5+0.5*n2);
  // edges
  float e = smoothstep(inner, inner+0.4, r)*(1.0-smoothstep(outer-1.5, outer, r));
  float heat = clamp(1.0-(r-inner)/(outer-inner),0.0,1.0);
  vec3 col = mix(vec3(0.55,0.06,0.02), vec3(1.0,0.45,0.10), heat);
  col = mix(col, vec3(1.0,0.95,0.85), pow(heat,5.0)*0.9);
  // doppler
  vec3 tang = normalize(vec3(-p.y,p.x,0.0));
  float dop = clamp(1.0+1.2*dot(normalize(ro-p), tang), 0.2, 2.2);
  col *= pow(dop,3.0);
  float bright = 6.0/pow(r,2.2);
  return col*dens*e*bright;
}
```
Hmm, doppler: dot(camDir, velocity) — light is boosted when source is moving toward observer: factor ~ (1 - v·n)^-3 where n = direction from source to camera... if velocity is toward camera, v·(cam - p) > 0. dot(normalize(ro-p), tang) > 0 → approaching. OK.

Also modulate brightness with noise so filaments: maybe col *= 0.3+ n.

Stars:
```glsl
vec3 stars(vec3 rd){
  vec3 col = vec3(0);
  // 2 layers
  for(int i=0;i<2;i++){
    float sc = i==0? 90.0 : 220.0;
    vec3 p = rd*sc;
    vec3 ip = floor(p);
    vec3 f = fract(p)-0.5;
    vec3 h = hash3(ip);
    if(h.z > (i==0?0.55:0.35)){
      vec3 c = f - h*0.8;
      float d = dot(c,c);
      float star = exp(-d*60.0)*smoothstep(0.5,0.0,length(h.xy));
      // color
      vec3 sc2 = mix(vec3(0.7,0.8,1.0), vec3(1.0,0.8,0.6), step(0.7,h.x));
      col += sc2*star*h.z;
    }
  }
  return col;
}
```
Hmm, exp(-d*60) — d is in cell units; cell is 1 unit in p space, on screen that's 1/90 rad ≈ 0.65°. d range within cell is up to ~0.75. exp(-d*60): d=0.01 → 0.55; d=0.05→0.046. So star radius in rd is ~0.03/90 ≈ 0.2°, ~3px at 1080p. OK.

Add tiny twinkle too? Skip or minimal: modulate by time hash — cheap: star *= 0.8+0.4*sin(uTime*3+h.x*50). Fine, add.

Also faint background nebula: use rd*3 fbm, subtle blue-purple.

Main:
```glsl
void main(){
  vec2 uv = (gl_FragCoord.xy - 0.5*uRes)/uRes.y;
  float t = uTime;
  float ang = t*0.06;
  float tilt = 0.25 + 0.15*sin(t*0.04);
  vec3 ro = vec3(cos(ang)*7.0, sin(ang*0.7)*1.5 + 0.8, sin(ang)*7.0);
```
Hmm, orbit and tilt: ro = vec3(cos(ang)*R, tiltY, sin(ang)*R), R=7, tiltY = 1.2+0.8*sin(t*0.03).

```glsl
  vec3 ta = vec3(0.0);
  vec3 fw = normalize(ta-ro);
  vec3 rt = normalize(cross(fw, vec3(0,1,0)));
  vec3 up = cross(rt,fw);
  float f = 0.8;
  vec3 rd = normalize(fw + f*(uv.x*rt+uv.y*up));
```

Trace:
```glsl
  vec3 p = ro;
  vec3 v = rd;
  float t0=0.0; // reuse name; rename time to uTime, path time to tp
```
Use `float tp = 0.0;`.

```glsl
  float h0sq = dot(p,p)-dot(dot(p,v),v);
  vec3 col = vec3(0);
  float minr = 1e6;
  float escaped = 0.0;
  for(int i=0;i<200;i++){
    float r2 = dot(p,p);
    float r = sqrt(r2);
    minr = min(minr,r);
    if(r < 1.0){ // horizon: black
      minr = r;
      escaped = -1.0;
      break;
    }
    if(r > 25.0){ escaped = 1.0; break; }
    float dt = clamp(0.03+r*0.06, 0.01, 0.5);
    vec3 prev = p;
    vec3 a = -1.5*h0sq/(r2*r)*p;
    p += v*dt;
    v += a*dt;
    // disk crossing
    if(prev.z*p.z < 0.0){
      float fr = prev.z/(prev.z-p.z);
      vec3 ip = mix(prev,p,fr);
      float ir = length(ip.xy);
      if(ir>1.8 && ir<7.0){
        col += disk(ip, ir);
      }
    }
  }
```
Wait: on horizon, minr = r <1 — no ring. OK.

After loop: if escaped==1: col += stars(rd)... but rd is no longer deflected direction; use current v (normalized):
```glsl
  if(escaped > 0.0){
    vec3 bd = normalize(v);
    col += stars(bd);
    // faint nebula
    col += vec3(0.04,0.05,0.09)*fbm(bd*4.0+3.0);
  }
```
Nebula fbm is 5 octaves — cost fine.

Photon ring:
```glsl
  float ring = exp(-pow((minr-1.5)*9.0,2.0));
  // only if not inside horizon
  if(minr > 1.0){ col += vec3(1.0,0.85,0.6)*ring*0.8; }
```
Hmm, but ray that ends in disk region with minr~1.5? If r>25 escape, or horizon, or 200 iterations done. Rays that stay in orbit (photon sphere) will accumulate. ring value: minr 1.5 → 1.0; minr 1.3 → exp(-(1.8)^2)= exp(-3.24)=0.04. OK thin ring. But ring also appears for rays that pass through disk and escape with minr~1.5 — fine, that's the lensed ring.

Tonemap and gamma:
```glsl
  col = col/(1.0+col); // Reinhard-ish
  col = pow(col, vec3(0.4545));
  // vignette
  vec2 q = gl_FragCoord.xy/uRes;
  float vig = smoothstep(1.2, 0.4, length(q-0.5)*1.6);
  col *= mix(0.6, 1.0, vig);
  // slight grain
  col += (hash1(vec3(gl_FragCoord.xy, mod(uTime,10.0)))-0.5)*0.015;
```
Grain hash: need 2D; use hash1(vec3) with uTime.

Maybe skip vignette to keep simple.

JS: boilerplate.

```js
const canvas = document.getElementById('c');
const gl = canvas.getContext('webgl2');
const vs = `#version 300 es
in vec2 a; void main(){ gl_Position = vec4(a,0.,1.); }`;
compile, fullscreen triangle (3 verts, no buffer issues): use triangle strip quad or big triangle.

resize: canvas.width = innerWidth * dpr (cap dpr to ~2 for perf), update uRes.

loop: gl.uniform1f(uTime, t/1000), drawArrays(TRIANGLE_STRIP,0,4).
```

Vertex data: [-1,-1, 1,-1, -1,1, 1,1].

Precision: highp float in fragment shader; some mobile GPUs lack highp in fragment — add `#ifdef GL_FRAGMENT_PRECISION_HIGH`. Keep simple with highp; requirement is desktop-ish.

Let's re-examine acceleration formula: a = -1.5*h0sq/(r2*r)*p, p has magnitude r, so |a| = 1.5*h0sq/r2/r * 1 = 1.5 h0sq/r^3, direction -p/r (radially inward). Good, standard.

Disk brightness: inner r=1.8: bright=6/(1.8^2.2)=6/3.4≈1.77, times col ~ (1,0.5,0.1), times doppler max 2.2^3≈10.6 → could blow to ~19 → Reinhard handles it, becomes white-hot. Good.

outer r=7: 6/7^2.2 = 6/62 ≈ 0.1, dark red. Good.

dt near hole: r=1.05 → dt = clamp(0.03+0.063, ...) = 0.093. Hmm, might be a bit large near photon orbit where curvature is strong; use 0.02+r*0.05: r=1 → 0.07. Use dt = clamp(0.01+r*0.05, 0.008, 0.4). r=25 → clamped 0.4 → 25/0.4 ≈ 63 steps just to escape — fine within 200.

Disk noise: fbm is 5 octaves of 3D value noise — a bit heavy, but once per ray-disk crossing, fine.

Stars: hash3 with sin — fine.

Another detail: "camera slowly orbits and tilts over time" — ro orbit ang = uTime*0.06, y tilt oscillates. Also maybe add slight roll rotation of camera basis — skip, tilt is enough.

Edge case: if ray passes exactly through z=0 (fr is NaN) — rare, fine.

Also want the disk to be slightly double-sided; handled by abs crossing.

Let's write final HTML.

Add subtle blue-shift tint too? Already have Doppler.

Also: multiple crossings accumulate col without alpha attenuation; acceptable (looks like glowing filaments).

Add small camera jitter? No.

Star twinkle uses uTime.

OK, code:

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
html,body{margin:0;padding:0;width:100%;height:100%;overflow:hidden;background:#000}
canvas{display:block;width:100vw;height:100vh}
</style>
</head>
<body>
<canvas id="c"></canvas>
<script>
const canvas=document.getElementById('c');
const gl=canvas.getContext('webgl2',{antialias:false});
if(!gl){document.body.innerHTML='<div style="color:#888;font-family:sans-serif;padding:2em">WebGL2 not supported</div>';throw new Error('no webgl2');}

const VSH=`#version 300 es
in vec2 a;
void main(){gl_Position=vec4(a,0.0,1.0);}`;

const FSH=`#version 300 es
precision highp float;
out vec4 O;
uniform vec2 uRes;
uniform float uTime;
...
`;
```

Compile/link helper.

```js
function make(type,src){const s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);
if(!gl.getShaderParameter(s,gl.COMPILE_STATUS)){console.error(gl.getShaderInfoLog(s));throw 'shader';}return s;}
const prog=gl.createProgram();
gl.attachShader(prog,make(gl.VERTEX_SHADER,VSH));
gl.attachShader(prog,make(gl.FRAGMENT_SHADER,FSH));
gl.linkProgram(prog);gl.useProgram(prog);
const vao=gl.createVertexArray();gl.bindVertexArray(vao);
const buf=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buf);
gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
const loc=gl.getAttribLocation(prog,'a');
gl.enableVertexAttribArray(loc);gl.vertexAttribPointer(loc,2,gl.FLOAT,false,0,0);
const uRes=gl.getUniformLocation(prog,'uRes');
const uTime=gl.getUniformLocation(prog,'uTime');

function resize(){
 const d=Math.min(window.devicePixelRatio||1,2);
 canvas.width=Math.max(1,Math.floor(innerWidth*d));
 canvas.height=Math.max(1,Math.floor(innerHeight*d));
 gl.viewport(0,0,canvas.width,canvas.height);
}
addEventListener('resize',resize);resize();

function frame(t){
 gl.uniform2f(uRes,canvas.width,canvas.height);
 gl.uniform1f(uTime,t*0.001);
 gl.drawArrays(gl.TRIANGLE_STRIP,0,4);
 requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
</script>
</body>
</html>
```

Now full FSH. Let's finalize the numbers.

Disk inner 1.9, outer 7.5.

fbm cost: 5 octaves × 3D noise (8 hashes) = 40 hashes per crossing; 1-3 crossings per ray. 3840×2160×2 ≈ 16M × avg 40 = 640M... fine on modern GPU.

Writing full fragment shader:

```glsl
float hash1(vec3 p){
  p=fract(p*0.3183099+vec3(0.1,0.2,0.3));
  p*=17.0;
  return fract(p.x*p.y*p.z*(p.x+p.y+p.z));
}
vec3 hash3(vec3 p){
  return vec3(hash1(p),hash1(p+19.19),hash1(p+37.71));
}
float noise(vec3 p){...}
float fbm(vec3 p){float a=0.5,s=0.0;for(int i=0;i<5;i++){s+=a*noise(p);p=p*2.03+11.3;a*=0.5;}return s;}
```

Stars:

```glsl
vec3 stars(vec3 rd,float t){
  vec3 col=vec3(0.0);
  for(int i=0;i<2;i++){
    float sc=(i==0)?70.0:180.0;
    vec3 p=rd*sc;
    vec3 ip=floor(p);
    vec3 f=fract(p)-0.5;
    vec3 h=hash3(ip);
    float thr=(i==0)?0.45:0.30;
    if(h.z>thr){
      vec3 c=f-h*0.7;
      float d=dot(c,c);
      float tw=0.85+0.3*sin(t*2.0+h.x*40.0);
      float star=exp(-d*70.0)*(h.z-thr);
      vec3 tint=mix(vec3(0.75,0.85,1.0),vec3(1.0,0.85,0.6),step(0.6,h.x));
      col+=tint*star*tw;
    }
  }
  return col;
}
```
star magnitude: h.z-thr ~ max 0.55; exp near center ~1; so ~0.5 brightness, OK.

Disk function as above.

Main trace as above, 180 iterations.

Camera:
```glsl
float camAng=uTime*0.05;
float R=7.5;
vec3 ro=vec3(cos(camAng)*R, 1.1+0.9*sin(uTime*0.033), sin(camAng)*R);
vec3 fw=normalize(-ro);
vec3 rt=normalize(cross(fw,vec3(0.0,1.0,0.0)));
vec3 up=cross(rt,fw);
float ff=0.9;
vec3 rd=normalize(fw+ff*(uv.x*rt+uv.y*up));
```
uv = (fragCoord - 0.5res)/res.y.

fov check: at r=7.5, horizon at r=1 is angle atan(1/7.5)=7.6°, fov half-angle atan(0.9)≈42°, half-width of screen 0.9 in uv units → hole will occupy maybe ~15% of height. Good.

Ring: also want thin photon ring to be visible in black disk — yes, additive.

Also maybe make disk slightly non-planar? No.

One more: add subtle lensing color: near hole, add orange glow from disk: already have ring.

OK let me also consider ray that goes straight to hole: r<1 → break, minr=r<1 → no ring, col stays 0 → black.

Ray that orbits and never escapes and doesn't hit horizon: 180 iterations, last p arbitrary — treat as escape? if not horizon, add stars(normalize(v)) with low weight? just add stars.

Tonemap: col=col/(1+col); then maybe add small blue ambient. gamma pow(col,vec3(1/2.2)) — use 0.4545.

Grain:
```glsl
float g=hash1(vec3(gl_FragCoord.xy,fract(uTime*7.0)*100.0))-0.5;
col+=g*0.012;
```

Final: gl_FragColor = O = vec4(clamp(col,0.,1.),1.).

Let's write the final answer.
