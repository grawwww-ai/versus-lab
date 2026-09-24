```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Singularity</title>
<style>
  html, body { margin:0; padding:0; width:100%; height:100%; overflow:hidden; background:#000; }
  canvas { display:block; width:100vw; height:100vh; }
</style>
</head>
<body>
<canvas id="c"></canvas>
<script>
"use strict";
const canvas = document.getElementById('c');
const gl = canvas.getContext('webgl2', { antialias:false, depth:false });
if (!gl) {
  document.body.innerHTML = '<div style="color:#999;font-family:sans-serif;padding:2em">WebGL2 is not available in this browser.</div>';
  throw new Error('WebGL2 not supported');
}

const VSH = `#version 300 es
in vec2 a;
void main(){ gl_Position = vec4(a, 0.0, 1.0); }`;

const FSH = `#version 300 es
precision highp float;
out vec4 O;
uniform vec2  uRes;
uniform float uTime;

#define INNER 1.9
#define OUTER 7.5
#define STEPS 190

/* ---------------- hashing & noise ---------------- */
float hash1(vec3 p){
  p = fract(p * 0.3183099 + vec3(0.1,0.2,0.3));
  p *= 17.0;
  return fract(p.x*p.y*p.z*(p.x+p.y+p.z));
}
vec3 hash3(vec3 p){
  return vec3(hash1(p), hash1(p + 19.19), hash1(p + 37.71));
}
float noise(vec3 p){
  vec3 i = floor(p);
  vec3 f = fract(p);
  f = f*f*(3.0 - 2.0*f);
  return mix(
    mix( mix(hash1(i+vec3(0,0,0)), hash1(i+vec3(1,0,0)), f.x),
         mix(hash1(i+vec3(0,1,0)), hash1(i+vec3(1,1,0)), f.x), f.y),
    mix( mix(hash1(i+vec3(0,0,1)), hash1(i+vec3(1,0,1)), f.x),
         mix(hash1(i+vec3(0,1,1)), hash1(i+vec3(1,1,1)), f.x), f.y),
    f.z);
}
float fbm(vec3 p){
  float a = 0.5, s = 0.0;
  for(int i = 0; i < 5; i++){
    s += a * noise(p);
    p = p * 2.03 + 11.3;
    a *= 0.5;
  }
  return s;
}

/* ---------------- starfield ---------------- */
vec3 stars(vec3 rd, float t){
  vec3 col = vec3(0.0);
  for(int i = 0; i < 2; i++){
    float sc = (i == 0) ? 70.0 : 180.0;
    vec3 p  = rd * sc;
    vec3 ip = floor(p);
    vec3 f  = fract(p) - 0.5;
    vec3 h  = hash3(ip);
    float thr = (i == 0) ? 0.45 : 0.30;
    if(h.z > thr){
      vec3  c    = f - h * 0.7;
      float d    = dot(c, c);
      float tw   = 0.85 + 0.3 * sin(t * 2.0 + h.x * 40.0);
      float star = exp(-d * 70.0) * (h.z - thr);
      vec3  tint = mix(vec3(0.75,0.85,1.0), vec3(1.0,0.85,0.6), step(0.6, h.x));
      col += tint * star * tw;
    }
  }
  return col;
}

/* ---------------- accretion disk ---------------- */
vec3 disk(vec3 p, float r, vec3 ro){
  if(r < INNER || r > OUTER) return vec3(0.0);
  // Keplerian rotation: inner parts spin faster
  float rot = 1.2 / pow(r, 1.5) * uTime;
  float cs = cos(rot), sn = sin(rot);
  vec2 q = mat2(cs,-sn,sn,cs) * p.xy;
  // turbulent filaments
  float n1 = fbm(vec3(q * 1.6,          uTime * 0.30));
  float n2 = fbm(vec3(q * 4.0 + 7.7,    uTime * 0.50));
  float dens = 0.10 + 0.90 * pow(n1, 1.5) * (0.45 + 0.55 * n2);
  // fade at the inner & outer edge
  float e = smoothstep(INNER, INNER + 0.45, r) * (1.0 - smoothstep(OUTER - 1.6, OUTER, r));
  // temperature gradient: white-hot inside, deep red outside
  float heat = clamp(1.0 - (r - INNER) / (OUTER - INNER), 0.0, 1.0);
  vec3  col  = mix(vec3(0.55, 0.06, 0.02), vec3(1.0, 0.45, 0.10), heat);
       col   = mix(col, vec3(1.0, 0.95, 0.85), pow(heat, 5.0) * 0.9);
  // Doppler beaming: brighten the side sweeping toward the camera
  vec3  tang = normalize(vec3(-p.y, p.x, 0.0));
  float dop  = clamp(1.0 + 1.2 * dot(normalize(ro - p), tang), 0.2, 2.2);
  col *= pow(dop, 3.0);
  float bright = 6.0 / pow(r, 2.2);
  return col * dens * e * bright;
}

/* ---------------- main ---------------- */
void main(){
  vec2 uv = (gl_FragCoord.xy - 0.5 * uRes) / uRes.y;

  // slow orbital camera with a breathing tilt
  float camAng = uTime * 0.05;
  float R = 7.5;
  vec3 ro = vec3(cos(camAng)*R, 1.1 + 0.9*sin(uTime*0.033), sin(camAng)*R);
  vec3 fw = normalize(-ro);
  vec3 rt = normalize(cross(fw, vec3(0.0,1.0,0.0)));
  vec3 up = cross(rt, fw);
  vec3 rd = normalize(fw + 0.9 * (uv.x*rt + uv.y*up));

  // ---- integrate geodesic (Newtonian-approx lensing) ----
  vec3  p   = ro;
  vec3  v   = rd;
  float h0sq = dot(p,p) - dot(dot(p,v), v);
  float minr = 1e6;
  float ended = 0.0;   // 0 running, 1 escaped, -1 horizon
  vec3  col = vec3(0.0);

  for(int i = 0; i < STEPS; i++){
    float r2 = dot(p,p);
    float r  = sqrt(r2);
    minr = min(minr, r);
    if(r < 1.0){ ended = -1.0; break; }          // event horizon
    if(r > 25.0){ ended =  1.0; break; }         // escaped

    float dt  = clamp(0.01 + r*0.05, 0.008, 0.4);
    vec3  prev = p;
    vec3  a    = -1.5 * h0sq / (r2*r) * p;       // inward radial deflection
    p += v * dt;
    v += a * dt;

    // disk plane crossing (handles multiple lensed images)
    if(prev.z * p.z < 0.0){
      float fr = prev.z / (prev.z - p.z);
      vec3  ip = mix(prev, p, fr);
      float ir = length(ip.xy);
      if(ir > INNER && ir < OUTER) col += disk(ip, ir, ro);
    }
  }

  if(ended > 0.0 || ended == 0.0){
    vec3 bd = normalize(v);
    // faint nebular haze + starfield, deflected by the accumulated path
    col += vec3(0.045, 0.055, 0.10) * fbm(bd*4.0 + 3.0);
    col += stars(bd, uTime);
  }

  // thin photon ring hugging the horizon
  if(minr > 1.0){
    float ring = exp(-pow((minr - 1.5) * 9.0, 2.0));
    col += vec3(1.0, 0.85, 0.6) * ring * 0.9;
  }

  // tonemap + gamma
  col = col / (1.0 + col);
  col = pow(max(col, vec3(0.0)), vec3(0.4545));
  // film grain to hide banding in the darks
  float g = hash1(vec3(gl_FragCoord.xy, fract(uTime*7.0)*100.0)) - 0.5;
  col += g * 0.012;

  O = vec4(clamp(col, 0.0, 1.0), 1.0);
}`;

function makeShader(type, src){
  const s = gl.createShader(type);
  gl.shaderSource(s, src);
  gl.compileShader(s);
  if(!gl.getShaderParameter(s, gl.COMPILE_STATUS)){
    console.error(gl.getShaderInfoLog(s));
    throw new Error('Shader compile failed');
  }
  return s;
}

const prog = gl.createProgram();
gl.attachShader(prog, makeShader(gl.VERTEX_SHADER, VSH));
gl.attachShader(prog, makeShader(gl.FRAGMENT_SHADER, FSH));
gl.linkProgram(prog);
if(!gl.getProgramParameter(prog, gl.LINK_STATUS)){
  console.error(gl.getProgramInfoLog(prog));
  throw new Error('Program link failed');
}
gl.useProgram(prog);

const vao = gl.createVertexArray();
gl.bindVertexArray(vao);
const buf = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, buf);
gl.bufferData(gl.ARRAY_BUFFER,
  new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW);
const locA = gl.getAttribLocation(prog, 'a');
gl.enableVertexAttribArray(locA);
gl.vertexAttribPointer(locA, 2, gl.FLOAT, false, 0, 0);

const uRes  = gl.getUniformLocation(prog, 'uRes');
const uTime = gl.getUniformLocation(prog, 'uTime');

function resize(){
  const d = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width  = Math.max(1, Math.floor(window.innerWidth  * d));
  canvas.height = Math.max(1, Math.floor(window.innerHeight * d));
  gl.viewport(0, 0, canvas.width, canvas.height);
}
window.addEventListener('resize', resize);
resize();

function frame(t){
  gl.uniform2f(uRes, canvas.width, canvas.height);
  gl.uniform1f(uTime, t * 0.001);
  gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
</script>
</body>
</html>
```