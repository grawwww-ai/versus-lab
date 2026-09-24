Here is a self-contained HTML document that runs a WebGL2 path tracer in the browser, progressively refining a photorealistic interior as samples accumulate over time.
```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>WebGL2 Path Tracer — Interior</title>
<style>
  html,body{margin:0;padding:0;width:100%;height:100%;overflow:hidden;background:#000;}
  #gl{display:block;width:100vw;height:100vh;}
  #label{
    position:fixed;left:14px;bottom:14px;
    font:12px/1.5 ui-monospace,Menlo,Consolas,monospace;
    color:#e8e8e8;background:rgba(0,0,0,.45);
    padding:5px 9px;border-radius:5px;pointer-events:none;
    letter-spacing:.04em;text-shadow:0 1px 2px #000;
  }
</style>
</head>
<body>
<canvas id="gl"></canvas>
<div id="label">samples: 0</div>
<script>
(function(){
"use strict";

/* ------------------------------------------------------------------ */
/*  WebGL2 context                                                     */
/* ------------------------------------------------------------------ */
const canvas = document.getElementById('gl');
const gl = canvas.getContext('webgl2', {
  antialias:false, alpha:false, depth:false, stencil:false,
  preserveDrawingBuffer:false, powerPreference:'high-performance'
});
const labelEl = document.getElementById('label');
if(!gl){
  labelEl.textContent = 'WebGL2 is not available in this browser.';
  return;
}

let colorFormat = gl.RGBA16F, colorType = gl.HALF_FLOAT;
if(gl.getExtension('EXT_color_buffer_float')){
  colorFormat = gl.RGBA32F; colorType = gl.FLOAT;
}else{
  gl.getExtension('EXT_color_buffer_half_float');
}

/* ------------------------------------------------------------------ */
/*  Scene definition (built in JS, emitted as GLSL constants)          */
/* ------------------------------------------------------------------ */
const T_PLANE=0, T_BOX=1, T_CYL=3;
const K_DIFF=0, K_METAL=1, K_GLASS=2, K_EMIT=3;

const P = [];
function pPlane(n, d, col, kind, rough, tex){
  P.push({t:T_PLANE,k:(kind===undefined?K_DIFF:kind),a:n,b:[d,0,0],c:col,r:rough||0,x:tex||0});
}
function pBox(cx,cy,cz,hx,hy,hz, col, kind, rough, tex){
  P.push({t:T_BOX,k:(kind===undefined?K_DIFF:kind),a:[cx,cy,cz],b:[hx,hy,hz],c:col,r:rough||0,x:tex||0});
}
function pCyl(cx,cy,cz,r1,h,r2, col, kind, rough){
  P.push({t:T_CYL,k:(kind===undefined?K_DIFF:kind),a:[cx,cy,cz],b:[r1,h,r2],c:col,r:rough||0,x:0});
}

/* --- palette ------------------------------------------------------- */
const WALL    = [0.84, 0.80, 0.72];
const CEILC   = [0.90, 0.90, 0.88];
const FRAMEC  = [0.19, 0.11, 0.06];
const SOFAC   = [0.16, 0.26, 0.29];
const CUSHC   = [0.22, 0.33, 0.35];
const WOODC   = [0.34, 0.19, 0.10];
const BRASSC  = [0.86, 0.69, 0.42];
const MIRC    = [0.95, 0.96, 0.97];
const GLASSC  = [0.93, 0.97, 0.95];
const FLOORC  = [1.00, 1.00, 1.00];          // modulated by procedural wood
const EMITC   = [7.0, 6.58, 5.80];

/* --- room shell ---------------------------------------------------- */
pPlane([0, 1, 0], 0.0,  FLOORC, K_DIFF, 0, 1);   // floor  (wood)
pPlane([0,-1, 0], -2.9, CEILC);                  // ceiling
pPlane([1, 0, 0], -3.2, WALL);                   // left wall  x=-3.2
pPlane([-1,0, 0], -3.2, WALL);                   // right wall x=+3.2
pPlane([0, 0, 1], -4.2, WALL);                   // back wall  z=-4.2
pPlane([0, 0,-1], -4.2, WALL);                   // front wall z=+4.2

/* --- window (emissive) --------------------------------------------- */
const LIGHT_IDX = P.length;
pBox(-1.5, 1.65, -4.185, 1.30, 0.75, 0.015, EMITC, K_EMIT);
const LX0=-2.8, LX1=-0.2, LY0=0.9, LY1=2.4, LZ=-4.17;

/* --- window frame + mullions --------------------------------------- */
pBox(-1.50, 0.875, -4.150, 1.34, 0.030, 0.060, FRAMEC);
pBox(-1.50, 2.425, -4.150, 1.34, 0.030, 0.060, FRAMEC);
pBox(-2.82, 1.650, -4.150, 0.03, 0.790, 0.060, FRAMEC);
pBox(-0.18, 1.650, -4.150, 0.03, 0.790, 0.060, FRAMEC);
pBox(-1.50, 1.650, -4.140, 0.022, 0.760, 0.045, FRAMEC);
pBox(-1.50, 1.650, -4.140, 1.300, 0.022, 0.045, FRAMEC);

/* --- mirror on the left wall --------------------------------------- */
pBox(-3.18, 1.80, -1.40, 0.02, 0.70, 1.20, MIRC, K_METAL, 0.01);

/* --- sofa against the back wall ------------------------------------ */
pBox(1.10, 0.22, -3.75, 1.00, 0.22, 0.45, SOFAC);
pBox(1.10, 0.72, -4.05, 1.00, 0.50, 0.15, SOFAC);
pBox(0.25, 0.50, -3.75, 0.15, 0.28, 0.45, SOFAC);
pBox(1.95, 0.50, -3.75, 0.15, 0.28, 0.45, SOFAC);
pBox(0.68, 0.52, -3.65, 0.42, 0.09, 0.40, CUSHC);
pBox(1.52, 0.52, -3.65, 0.42, 0.09, 0.40, CUSHC);

/* --- table --------------------------------------------------------- */
pBox(1.00, 0.440, -2.40, 0.65, 0.030, 0.40, WOODC);
pBox(0.42, 0.205, -2.72, 0.035, 0.205, 0.035, WOODC);
pBox(1.58, 0.205, -2.72, 0.035, 0.205, 0.035, WOODC);
pBox(0.42, 0.205, -2.08, 0.035, 0.205, 0.035, WOODC);
pBox(1.58, 0.205, -2.08, 0.035, 0.205, 0.035, WOODC);

/* --- glass --------------------------------------------------------- */
pCyl(1.32, 0.470, -2.25, 0.045, 0.16, 0.045, GLASSC, K_GLASS, 0.0);

/* --- metal lamp ---------------------------------------------------- */
pCyl(0.72, 0.470, -2.50, 0.080, 0.025, 0.070, BRASSC, K_METAL, 0.28);
pCyl(0.72, 0.495, -2.50, 0.012, 0.300, 0.012, BRASSC, K_METAL, 0.22);
pCyl(0.72, 0.795, -2.50, 0.115, 0.170, 0.070, BRASSC, K_METAL, 0.17);

/* ------------------------------------------------------------------ */
/*  GLSL source generation                                             */
/* ------------------------------------------------------------------ */
const fx = v => (Math.abs(v)<1e-8?0:v).toFixed(5);
const V3 = a => 'vec3(' + fx(a[0]) + ',' + fx(a[1]) + ',' + fx(a[2]) + ')';

const NP = P.length;
const arrType  = P.map(p=>p.t).join(',');
const arrKind  = P.map(p=>p.k).join(',');
const arrA     = P.map(p=>V3(p.a)).join(',');
const arrB     = P.map(p=>V3(p.b)).join(',');
const arrAlb   = P.map(p=>V3(p.c)).join(',');
const arrRough = P.map(p=>fx(p.r)).join(',');
const arrTex   = P.map(p=>p.x).join(',');

const VS = `#version 300 es
void main(){
  vec2 p = vec2(float((gl_VertexID << 1) & 2), float(gl_VertexID & 2));
  gl_Position = vec4(p * 2.0 - 1.0, 0.0, 1.0);
}`;

const FS_RAY = `#version 300 es
precision highp float;
precision highp int;

out vec4 fragColor;

uniform vec2  uRes;
uniform float uKeep;
uniform float uInv;
uniform vec3  uCamPos;
uniform vec3  uCamRight;
uniform vec3  uCamUp;
uniform vec3  uCamFwd;
uniform float uTanHalf;
uniform float uLensR;
uniform float uFocus;
uniform float uFrameNo;
uniform sampler2D uPrev;

#define NP ${NP}
const int   P_TYPE[NP]  = int[NP](${arrType});
const int   P_KIND[NP]  = int[NP](${arrKind});
const vec3  P_A[NP]     = vec3[NP](${arrA});
const vec3  P_B[NP]     = vec3[NP](${arrB});
const vec3  P_ALB[NP]   = vec3[NP](${arrAlb});
const float P_ROUGH[NP] = float[NP](${arrRough});
const int   P_TEX[NP]   = int[NP](${arrTex});

const vec3  LIGHT_EMIT = vec3(${fx(EMITC[0])},${fx(EMITC[1])},${fx(EMITC[2])});
const float LX0 = ${fx(LX0)}, LX1 = ${fx(LX1)};
const float LY0 = ${fx(LY0)}, LY1 = ${fx(LY1)};
const float LZ  = ${fx(LZ)};

#define PI 3.14159265358979
#define INV_PI 0.31830988618379

/* ---------------- RNG ---------------- */
uint rngState;
uint rndu(){
  rngState = rngState * 747796405u + 2891336453u;
  uint w = ((rngState >> ((rngState >> 28u) + 4u)) ^ rngState) * 277803737u;
  return (w >> 22u) ^ w;
}
float rnd(){ return float(rndu() >> 8) * (1.0/16777216.0); }

/* ---------------- primitive intersection ---------------- */
bool hitPrim(int i, vec3 ro, vec3 rd, out float tOut, out vec3 nOut){
  tOut = 1e30;
  nOut = vec3(0.0, 1.0, 0.0);
  int ty = P_TYPE[i];
  vec3 a = P_A[i];
  vec3 b = P_B[i];

  if(ty == 0){                                   // infinite plane  dot(n,p)=d
    float dn = dot(a, rd);
    if(abs(dn) > 1e-7){
      float tt = (b.x - dot(a, ro)) / dn;
      if(tt > 1e-4){ tOut = tt; nOut = a; return true; }
    }
    return false;
  }

  if(ty == 1){                                   // axis aligned box
    vec3 inv = 1.0 / rd;
    vec3 t0 = (a - b - ro) * inv;
    vec3 t1 = (a + b - ro) * inv;
    vec3 tmn = min(t0, t1);
    vec3 tmx = max(t0, t1);
    float tn = max(max(tmn.x, tmn.y), tmn.z);
    float tf = min(min(tmx.x, tmx.y), tmx.z);
    if(tn > tf) return false;
    float tt = (tn > 1e-4) ? tn : tf;
    if(tt <= 1e-4) return false;
    vec3 p = ro + rd * tt;
    vec3 d = (p - a) / b;
    vec3 ad = abs(d);
    vec3 n;
    if(ad.x >= ad.y && ad.x >= ad.z)      n = vec3(sign(d.x), 0.0, 0.0);
    else if(ad.y >= ad.z)                 n = vec3(0.0, sign(d.y), 0.0);
    else                                  n = vec3(0.0, 0.0, sign(d.z));
    tOut = tt; nOut = n; return true;
  }

  if(ty == 2){                                   // ellipsoid
    vec3 oc = (ro - a) / b;
    vec3 rd2 = rd / b;
    float A = dot(rd2, rd2);
    float B = 2.0 * dot(oc, rd2);
    float C = dot(oc, oc) - 1.0;
    float disc = B*B - 4.0*A*C;
    if(disc <= 0.0 || A < 1e-9) return false;
    float sd = sqrt(disc);
    float tt = (-B - sd) / (2.0*A);
    if(tt <= 1e-4) tt = (-B + sd) / (2.0*A);
    if(tt <= 1e-4) return false;
    vec3 p = ro + rd * tt;
    tOut = tt;
    nOut = normalize((p - a) / (b*b));
    return true;
  }

  /* ty == 3 : cylinder / frustum along +Y, a = base centre, b = (r1, h, r2) */
  {
    float r1 = b.x, hh = b.y, r2 = b.z;
    vec3 o = ro - a;
    float k = (r2 - r1) / hh;
    float A = rd.x*rd.x + rd.z*rd.z - k*k*rd.y*rd.y;
    float B = 2.0 * (o.x*rd.x + o.z*rd.z - k*rd.y*(r1 + k*o.y));
    float C = o.x*o.x + o.z*o.z - (r1 + k*o.y)*(r1 + k*o.y);

    float bt = 1e30; vec3 bn = vec3(0.0,1.0,0.0); bool found = false;

    if(abs(A) > 1e-9){
      float disc = B*B - 4.0*A*C;
      if(disc >= 0.0){
        float sd = sqrt(disc);
        for(int s = 0; s < 2; s++){
          float tt = (s == 0) ? (-B - sd)/(2.0*A) : (-B + sd)/(2.0*A);
          if(tt > 1e-4){
            float y = o.y + tt*rd.y;
            if(y >= 0.0 && y <= hh && tt < bt){
              bt = tt;
              float rr = r1 + k*y;
              bn = normalize(vec3(o.x + tt*rd.x, -k*rr, o.z + tt*rd.z));
              found = true;
            }
          }
        }
      }
    }
    if(abs(rd.y) > 1e-9){
      for(int s = 0; s < 2; s++){
        float yc  = (s == 0) ? 0.0 : hh;
        float rad = (s == 0) ? r1 : r2;
        if(rad > 1e-6){
          float tt = (yc - o.y) / rd.y;
          if(tt > 1e-4 && tt < bt){
            float px = o.x + tt*rd.x;
            float pz = o.z + tt*rd.z;
            if(px*px + pz*pz <= rad*rad){
              bt = tt;
              bn = vec3(0.0, (s == 0) ? -1.0 : 1.0, 0.0);
              found = true;
            }
          }
        }
      }
    }
    if(found){ tOut = bt; nOut = bn; return true; }
    return false;
  }
}

bool intersectScene(vec3 ro, vec3 rd, out float tOut, out vec3 nOut, out int idxOut){
  tOut = 1e30;
  nOut = vec3(0.0, 1.0, 0.0);
  idxOut = -1;
  for(int i = 0; i < NP; i++){
    float tt; vec3 nn;
    if(hitPrim(i, ro, rd, tt, nn)){
      if(tt < tOut){ tOut = tt; nOut = nn; idxOut = i; }
    }
  }
  return idxOut >= 0;
}

bool occluded(vec3 ro, vec3 rd, float maxT){
  for(int i = 0; i < NP; i++){
    float tt; vec3 nn;
    if(hitPrim(i, ro, rd, tt, nn)){
      if(tt < maxT) return true;
    }
  }
  return false;
}

/* ---------------- procedural wood ---------------- */
float hash11(float p){
  p = fract(p * 0.1031);
  p *= p + 33.33;
  p *= p + p;
  return fract(p);
}
vec3 woodPattern(vec3 p){
  float pw = 0.175;
  float id = floor(p.x / pw);
  float f  = fract(p.x / pw);
  float g  = hash11(id * 1.37 + 0.5);
  vec3 c1 = vec3(0.54, 0.34, 0.18);
  vec3 c2 = vec3(0.33, 0.19, 0.09);
  vec3 c  = mix(c1, c2, g);
  float grain = sin(p.z * 17.0 + g * 61.0 + sin(p.x * 6.0) * 2.2) * 0.5 + 0.5;
  grain = mix(grain, 1.0, 0.35);
  float seam = smoothstep(0.0, 0.028, f) * smoothstep(0.0, 0.028, 1.0 - f);
  c *= (0.74 + 0.36 * grain);
  c *= mix(0.42, 1.0, seam);
  return c;
}

/* ---------------- sampling helpers ---------------- */
vec3 cosHemisphere(vec3 n){
  float r1 = rnd(), r2 = rnd();
  float phi = 2.0 * PI * r1;
  float sr  = sqrt(r2);
  vec3 up = abs(n.y) < 0.99 ? vec3(0.0,1.0,0.0) : vec3(1.0,0.0,0.0);
  vec3 tx = normalize(cross(up, n));
  vec3 ty = cross(n, tx);
  return normalize(tx * (sr * cos(phi)) + ty * (sr * sin(phi)) + n * sqrt(max(0.0, 1.0 - r2)));
}

vec3 sampleGGX(vec3 n, float rough){
  float a = max(rough * rough, 1e-3);
  float u1 = rnd(), u2 = rnd();
  float phi = 2.0 * PI * u1;
  float ct = sqrt((1.0 - u2) / (1.0 + (a*a - 1.0) * u2));
  float st = sqrt(max(0.0, 1.0 - ct*ct));
  vec3 up = abs(n.y) < 0.99 ? vec3(0.0,1.0,0.0) : vec3(1.0,0.0,0.0);
  vec3 tx = normalize(cross(up, n));
  vec3 ty = cross(n, tx);
  return normalize(tx * (st*cos(phi)) + ty * (st*sin(phi)) + n * ct);
}

vec3 fresnelSchlick(float c, vec3 F0){
  return F0 + (1.0 - F0) * pow(1.0 - c, 5.0);
}

float smithG(float NoV, float NoL, float a){
  float k  = a * 0.5;
  float gv = NoV / (NoV * (1.0 - k) + k);
  float gl = NoL / (NoL * (1.0 - k) + k);
  return gv * gl;
}

/* ---------------- next event estimation (window quad) ---------------- */
vec3 sampleLight(vec3 p, vec3 n, vec3 alb){
  vec3 q = vec3(mix(LX0, LX1, rnd()), mix(LY0, LY1, rnd()), LZ);
  vec3 dv = q - p;
  float d2 = dot(dv, dv);
  float d  = sqrt(d2);
  vec3 wi  = dv / d;
  float cs = dot(n, wi);
  if(cs <= 0.0) return vec3(0.0);
  float cl = -wi.z;                       // light normal = (0,0,1)
  if(cl <= 0.0) return vec3(0.0);
  if(occluded(p + n * 2.0e-3, wi, d - 3.0e-3)) return vec3(0.0);
  float area = (LX1 - LX0) * (LY1 - LY0);
  return alb * INV_PI * LIGHT_EMIT * (cs * cl / d2) * area;
}

/* ---------------- path tracer ---------------- */
vec3 tracePath(vec3 ro, vec3 rd){
  vec3 L = vec3(0.0);
  vec3 beta = vec3(1.0);
  bool spec = true;                      // camera ray is a delta path

  for(int depth = 0; depth < 6; depth++){
    float t; vec3 n; int idx;
    if(!intersectScene(ro, rd, t, n, idx)) break;

    vec3 p = ro + rd * t;
    int kind = P_KIND[idx];
    vec3 alb = P_ALB[idx];
    if(P_TEX[idx] == 1) alb *= woodPattern(p);

    if(kind == 3){                       // emissive
      if(spec) L += beta * alb;
      break;
    }

    if(kind == 0){                       // diffuse
      L += beta * sampleLight(p, n, alb);
      vec3 d = cosHemisphere(n);
      beta *= alb;
      ro = p + n * 1.5e-3;
      rd = d;
      spec = false;
    }
    else if(kind == 1){                  // metal (GGX)
      vec3 v = -rd;
      vec3 h = sampleGGX(n, P_ROUGH[idx]);
      vec3 l = 2.0 * dot(v, h) * h - v;
      float NoL = dot(n, l);
      if(NoL <= 0.0) break;
      float NoV = max(dot(n, v), 1e-4);
      float NoH = max(dot(n, h), 1e-4);
      float VoH = max(dot(v, h), 1e-4);
      float a   = max(P_ROUGH[idx] * P_ROUGH[idx], 1e-3);
      vec3  F   = fresnelSchlick(VoH, alb);
      float G   = smithG(NoV, NoL, a);
      beta *= F * (G * VoH / (NoV * NoH));
      ro = p + n * 1.5e-3;
      rd = l;
      spec = true;
    }
    else{                                // dielectric (glass)
      const float IOR = 1.5;
      float dn = dot(rd, n);
      vec3  nf = dn < 0.0 ? n : -n;
      float eta = dn < 0.0 ? (1.0 / IOR) : IOR;
      float ci = clamp(dot(-rd, nf), 0.0, 1.0);
      float k  = 1.0 - eta * eta * (1.0 - ci * ci);
      vec3 nd;
      if(k < 0.0){
        nd = reflect(rd, nf);            // total internal reflection
      }else{
        float r0 = (1.0 - IOR) / (1.0 + IOR); r0 *= r0;
        float fr = r0 + (1.0 - r0) * pow(1.0 - ci, 5.0);
        if(rnd() < fr){
          nd = reflect(rd, nf);
        }else{
          nd = normalize(eta * rd + (eta * ci - sqrt(k)) * nf);
          beta *= alb;
        }
      }
      ro = p + nd * 2.5e-3;
      rd = nd;
      spec = true;
    }

    /* russian roulette */
    if(depth >= 3){
      float q = clamp(max(beta.r, max(beta.g, beta.b)), 0.05, 1.0);
      if(rnd() > q) break;
      beta /= q;
    }
  }
  return L;
}

/* ---------------- main ---------------- */
void main(){
  ivec2 pix = ivec2(gl_FragCoord.xy);
  vec3 prev = texelFetch(uPrev, pix, 0).rgb;

  uint s = uint(pix.x) * 1973u + uint(pix.y) * 9277u + uint(uFrameNo) * 26699u + 1u;
  s ^= s >> 16; s *= 0x7feb352du;
  s ^= s >> 15; s *= 0x846ca68bu;
  s ^= s >> 16;
  rngState = s | 1u;

  /* camera ray with AA jitter + thin lens depth of field */
  vec2 uv = (gl_FragCoord.xy + vec2(rnd(), rnd()) - 0.5 * uRes) / uRes.y;
  vec3 dir = normalize(uCamFwd
                     + uCamRight * (uv.x * 2.0 * uTanHalf)
                     + uCamUp    * (uv.y * 2.0 * uTanHalf));
  float fdist = uFocus / max(dot(dir, uCamFwd), 1e-4);
  vec3 focal  = uCamPos + dir * fdist;

  float ang = 2.0 * PI * rnd();
  float rad = uLensR * sqrt(rnd());
  vec3 ro = uCamPos + uCamRight * (cos(ang) * rad) + uCamUp * (sin(ang) * rad);
  vec3 rd = normalize(focal - ro);

  vec3 col = tracePath(ro, rd);

  vec3 outc = prev * uKeep + col * uInv;
  fragColor = vec4(outc, 1.0);
}`;

const FS_DISPLAY = `#version 300 es
precision highp float;
out vec4 fragColor;
uniform sampler2D uTex;
uniform float uExposure;
vec3 aces(vec3 x){
  return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0);
}
void main(){
  vec3 c = texelFetch(uTex, ivec2(gl_FragCoord.xy), 0).rgb;
  c *= uExposure;
  c = aces(c);
  c = pow(c, vec3(1.0 / 2.2));
  fragColor = vec4(c, 1.0);
}`;

/* ------------------------------------------------------------------ */
/*  GL plumbing                                                        */
/* ------------------------------------------------------------------ */
function compile(type, src){
  const sh = gl.createShader(type);
  gl.shaderSource(sh, src);
  gl.compileShader(sh);
  if(!gl.getShaderParameter(sh, gl.COMPILE_STATUS)){
    console.error(gl.getShaderInfoLog(sh));
    console.error(src);
    throw new Error('shader compile failed');
  }
  return sh;
}
function program(vsSrc, fsSrc){
  const p = gl.createProgram();
  gl.attachShader(p, compile(gl.VERTEX_SHADER, vsSrc));
  gl.attachShader(p, compile(gl.FRAGMENT_SHADER, fsSrc));
  gl.linkProgram(p);
  if(!gl.getProgramParameter(p, gl.LINK_STATUS)){
    console.error(gl.getProgramInfoLog(p));
    throw new Error('link failed');
  }
  return p;
}

const progRay = program(VS, FS_RAY);
const progDisp = program(VS, FS_DISPLAY);

const rayU = {
  res:     gl.getUniformLocation(progRay, 'uRes'),
  keep:    gl.getUniformLocation(progRay, 'uKeep'),
  inv:     gl.getUniformLocation(progRay, 'uInv'),
  camPos:  gl.getUniformLocation(progRay, 'uCamPos'),
  camR:    gl.getUniformLocation(progRay, 'uCamRight'),
  camU:    gl.getUniformLocation(progRay, 'uCamUp'),
  camF:    gl.getUniformLocation(progRay, 'uCamFwd'),
  tanHalf: gl.getUniformLocation(progRay, 'uTanHalf'),
  lensR:   gl.getUniformLocation(progRay, 'uLensR'),
  focus:   gl.getUniformLocation(progRay, 'uFocus'),
  frameNo: gl.getUniformLocation(progRay, 'uFrameNo'),
  prev:    gl.getUniformLocation(progRay, 'uPrev')
};
const dispU = {
  tex:      gl.getUniformLocation(progDisp, 'uTex'),
  exposure: gl.getUniformLocation(progDisp, 'uExposure')
};

/* ------------------------------------------------------------------ */
/*  Render targets                                                     */
/* ------------------------------------------------------------------ */
let RW = 0, RH = 0;
let tex = [null, null];
let fbo = [null, null];
let pingpong = 0;
let sampleCount = 0;

function makeTargets(w, h){
  for(let i = 0; i < 2; i++){
    if(tex[i]) gl.deleteTexture(tex[i]);
    if(fbo[i]) gl.deleteFramebuffer(fbo[i]);
    const t = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, t);
    gl.texImage2D(gl.TEXTURE_2D, 0, colorFormat, w, h, 0, gl.RGBA, colorType, null);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    const f = gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER, f);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, t, 0);
    gl.clearColor(0, 0, 0, 1);
    gl.clear(gl.COLOR_BUFFER_BIT);
    tex[i] = t;
    fbo[i] = f;
  }
  gl.bindFramebuffer(gl.FRAMEBUFFER, null);
  pingpong = 0;
  sampleCount = 0;
}

function resize(){
  const cw = Math.max(1, Math.floor(window.innerWidth));
  const ch = Math.max(1, Math.floor(window.innerHeight));
  const MAXPIX = 640000;
  const s = Math.min(1, Math.sqrt(MAXPIX / (cw * ch)));
  RW = Math.max(160, Math.round(cw * s));
  RH = Math.max(120, Math.round(ch * s));
  canvas.width = RW;
  canvas.height = RH;
  makeTargets(RW, RH);
}
window.addEventListener('resize', resize);
resize();

/* ------------------------------------------------------------------ */
/*  Camera                                                             */
/* ------------------------------------------------------------------ */
const CAM_BASE = [0.20, 1.50, 2.20];
const TGT_BASE = [-1.40, 1.15, -2.40];
const FOV_Y = 48.0 * Math.PI / 180.0;
const TAN_HALF = Math.tan(FOV_Y * 0.5);
const LENS_R = 0.009;

function sub(a, b){ return [a[0]-b[0], a[1]-b[1], a[2]-b[2]]; }
function cross(a, b){
  return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
}
function norm(a){
  const l = Math.hypot(a[0], a[1], a[2]) || 1;
  return [a[0]/l, a[1]/l, a[2]/l];
}

const startTime = performance.now();
let lastLabelUpdate = 0;

function loop(now){
  requestAnimationFrame(loop);

  const t = (now - startTime) * 0.001;

  /* --- slow, gentle camera drift (loops every ~44s) --- */
  const ph = 2.0 * Math.PI * t / 44.0;
  const camPos = [
    CAM_BASE[0] + 0.040 * Math.sin(ph),
    CAM_BASE[1] + 0.018 * Math.sin(2.0 * ph + 0.7),
    CAM_BASE[2] + 0.030 * Math.sin(ph + 1.3)
  ];
  const camTgt = [
    TGT_BASE[0] + 0.038 * Math.sin(ph * 0.7 + 2.0),
    TGT_BASE[1] + 0.022 * Math.sin(ph * 1.1),
    TGT_BASE[2]
  ];

  const fwd   = norm(sub(camTgt, camPos));
  const right = norm(cross(fwd, [0, 1, 0]));
  const up    = cross(right, fwd);
  const focus = Math.hypot(camTgt[0]-camPos[0], camTgt[1]-camPos[1], camTgt[2]-camPos[2]);

  /* ---- path tracing pass (ping-pong accumulation) ---- */
  const src = pingpong;
  const dst = 1 - pingpong;

  gl.bindFramebuffer(gl.FRAMEBUFFER, fbo[dst]);
  gl.viewport(0, 0, RW, RH);
  gl.disable(gl.BLEND);
  gl.useProgram(progRay);

  gl.activeTexture(gl.TEXTURE0);
  gl.bindTexture(gl.TEXTURE_2D, tex[src]);
  gl.uniform1i(rayU.prev, 0);

  const n = sampleCount;
  gl.uniform1f(rayU.keep, n / (n + 1));
  gl.uniform1f(rayU.inv,  1 / (n + 1));
  gl.uniform2f(rayU.res, RW, RH);
  gl.uniform3f(rayU.camPos, camPos[0], camPos[1], camPos[2]);
  gl.uniform3f(rayU.camR, right[0], right[1], right[2]);
  gl.uniform3f(rayU.camU, up[0], up[1], up[2]);
  gl.uniform3f(rayU.camF, fwd[0], fwd[1], fwd[2]);
  gl.uniform1f(rayU.tanHalf, TAN_HALF);
  gl.uniform1f(rayU.lensR, LENS_R);
  gl.uniform1f(rayU.focus, focus);
  gl.uniform1f(rayU.frameNo, n);

  gl.drawArrays(gl.TRIANGLES, 0, 3);

  pingpong = dst;
  sampleCount++;

  /* ---- display pass (tone map) ---- */
  gl.bindFramebuffer(gl.FRAMEBUFFER, null);
  gl.viewport(0, 0, RW, RH);
  gl.useProgram(progDisp);
  gl.activeTexture(gl.TEXTURE0);
  gl.bindTexture(gl.TEXTURE_2D, tex[pingpong]);
  gl.uniform1i(dispU.tex, 0);
  gl.uniform1f(dispU.exposure, 1.15);
  gl.drawArrays(gl.TRIANGLES, 0, 3);

  /* ---- label ---- */
  if(now - lastLabelUpdate > 100){
    lastLabelUpdate = now;
    labelEl.textContent = 'samples: ' + sampleCount;
  }
}

requestAnimationFrame(loop);
})();
</script>
</body>
</html>
```
### How the Scene Renders and Evolves

- **Progressive accumulation:** Each frame adds one sample per pixel into a ping-pong pair of floating-point textures. The displayed image converges smoothly as more samples accumulate.
- **Unbiased lighting:** A full path tracer handles direct and indirect illumination, including color bleeding from walls, soft shadows from the area window, and physically based glossy/metal surfaces.
- **Camera and depth of field:** The camera drifts slowly in a loop, while a thin-lens model adds subtle depth of field. The sample counter in the bottom-left updates every 100 ms.
- **Self-contained rendering:** Everything runs in a single HTML file with no external assets, and the WebGL2 context is created when the page loads.
---

**Optimization Tip:** You can adjust `FOV_Y`, `LENS_R`, or the drift amplitudes to change the view. For faster convergence, lower the `MAXPIX` value in `resize()` or reduce the maximum path depth in `tracePath`.