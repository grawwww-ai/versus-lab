Here's a complete, self-contained HTML file that renders a full-window WebGL2 black hole animation with a turbulent accretion disk, gravitational lensing, and a starfield background.
```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Black Hole — WebGL2</title>
<style>
  html, body { margin:0; padding:0; width:100%; height:100%; background:#000; overflow:hidden; }
  canvas { display:block; width:100vw; height:100vh; background:#000; }
</style>
</head>
<body>
<canvas id="glcanvas"></canvas>
<script>
(function () {
  "use strict";

  const canvas = document.getElementById("glcanvas");
  const gl = canvas.getContext("webgl2", {
    antialias: false,
    alpha: false,
    depth: false,
    stencil: false,
    premultipliedAlpha: false,
    powerPreference: "high-performance"
  });

  if (!gl) {
    document.body.innerHTML =
      '<div style="color:#888;font:14px system-ui,sans-serif;padding:24px">WebGL2 is not available in this browser.</div>';
    return;
  }

  /* ------------------------------------------------------------------ */
  /*  Shaders                                                            */
  /* ------------------------------------------------------------------ */

  const VS_SRC = `#version 300 es
in vec2 aPos;
void main() {
  gl_Position = vec4(aPos, 0.0, 1.0);
}
`;

  const FS_SRC = `#version 300 es
precision highp float;

out vec4 fragColor;

uniform vec2  uRes;
uniform float uTime;

const float DISK_IN  = 2.60;
const float DISK_OUT = 10.50;

/* ------------------------------------------------------------------ */
/*  Hash / noise                                                       */
/* ------------------------------------------------------------------ */
float hash13(vec3 p3) {
  p3 = fract(p3 * 0.1031);
  p3 += dot(p3, p3.zyx + 31.32);
  return fract((p3.x + p3.y) * p3.z);
}

vec2 hash22(vec2 p) {
  vec3 p3 = fract(vec3(p.xyx) * vec3(0.1031, 0.1030, 0.0973));
  p3 += dot(p3, p3.yzx + 33.33);
  return fract((p3.xx + p3.yz) * p3.zy);
}

float vnoise(vec3 x) {
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

float fbm(vec3 p) {
  float s = 0.0;
  float a = 0.5;
  for (int i = 0; i < 4; i++) {
    s += a * vnoise(p);
    p = p * 2.03 + vec3(13.7, 7.3, 5.1);
    a *= 0.5;
  }
  return s * 1.0666667; /* normalize by 0.9375 */
}

/* ------------------------------------------------------------------ */
/*  Starfield (cube-face mapped, so no polar seams)                    */
/* ------------------------------------------------------------------ */
vec3 dirToFace(vec3 d) {
  vec3 a = abs(d);
  if (a.x >= a.y && a.x >= a.z) return vec3(d.z / a.x, d.y / a.x, d.x > 0.0 ? 0.0 : 1.0);
  if (a.y >= a.z)               return vec3(d.x / a.y, d.z / a.y, d.y > 0.0 ? 2.0 : 3.0);
  return vec3(d.x / a.z, d.y / a.z, d.z > 0.0 ? 4.0 : 5.0);
}

float starLayer(vec2 uv, float scale, float density, float size, float seed) {
  vec2 p  = uv * scale;
  vec2 id = floor(p);
  vec2 gv = fract(p) - 0.5;
  float acc = 0.0;
  for (int j = -1; j <= 1; j++) {
    for (int i = -1; i <= 1; i++) {
      vec2 o = vec2(float(i), float(j));
      vec2 h = hash22(id + o + seed);
      if (h.x > density) continue;
      vec2 sp = o + (h - 0.5) * 0.85;
      float dd = length(gv - sp);
      float b  = smoothstep(size, 0.0, dd);
      acc += b * b * (0.15 + 0.85 * h.y);
    }
  }
  return acc;
}

vec3 skyColor(vec3 d) {
  vec3  f    = dirToFace(d);
  vec2  uv   = f.xy;
  float seed = f.z * 37.0;

  float s1 = starLayer(uv,  5.0, 0.30, 0.020, seed +  1.7);
  float s2 = starLayer(uv, 11.0, 0.22, 0.035, seed +  9.3);
  float s3 = starLayer(uv, 24.0, 0.18, 0.055, seed + 21.1);

  vec3 col = vec3(0.0);
  col += vec3(1.00, 0.93, 0.82) * s1 * 1.05;
  col += vec3(0.82, 0.89, 1.00) * s2 * 0.60;
  col += vec3(1.00, 1.00, 1.00) * s3 * 0.32;

  /* very faint galactic haze */
  float h = fbm(d * 6.0 + 4.3);
  col += vec3(0.030, 0.040, 0.070) * pow(h, 3.0) * 1.2;

  return col;
}

/* ------------------------------------------------------------------ */
/*  Disk colour ramp                                                   */
/* ------------------------------------------------------------------ */
vec3 diskColor(float x) {
  vec3 c = mix(vec3(1.00, 0.96, 0.88), vec3(1.00, 0.55, 0.15), smoothstep(0.00, 0.28, x));
  c = mix(c, vec3(0.88, 0.21, 0.05), smoothstep(0.28, 0.72, x));
  c = mix(c, vec3(0.42, 0.06, 0.02), smoothstep(0.72, 1.00, x));
  return c;
}

vec3 aces(vec3 x) {
  return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0);
}

/* ------------------------------------------------------------------ */
/*  Main                                                               */
/* ------------------------------------------------------------------ */
void main() {
  vec2  uv = (gl_FragCoord.xy - 0.5 * uRes) / uRes.y;
  float t  = uTime;

  /* ---------------- camera ---------------- */
  float camDist = 20.0;
  float az = t * 0.065;
  float el = 0.20 + 0.07 * sin(t * 0.037);

  vec3 camPos = vec3(cos(el) * cos(az), sin(el), cos(el) * sin(az)) * camDist;
  vec3 fwd    = -normalize(camPos);
  vec3 right  = normalize(cross(fwd, vec3(0.0, 1.0, 0.0)));
  vec3 up     = cross(right, fwd);

  vec3 rayDir = normalize(uv.x * right + uv.y * up + 1.55 * fwd);

  /* ---------------- geodesic integration ---------------- */
  /*  d2x/dl2 = -1.5 * h^2 * x / r^5   (Schwarzschild, rs = 1)          */

  vec3  pos = camPos;
  vec3  dir = rayDir;
  vec3  Lv  = cross(pos, dir);
  float h2  = dot(Lv, Lv);

  vec3  col   = vec3(0.0);
  float trans = 1.0;
  float rMin  = 1e5;
  bool  captured = false;
  bool  escaped  = false;

  for (int i = 0; i < 300; i++) {
    float r = length(pos);
    rMin = min(rMin, r);

    if (r < 1.0) { captured = true; break; }
    if (r > 24.0 && dot(pos, dir) > 0.0) { escaped = true; break; }

    vec3 prevPos = pos;
    vec3 prevDir = dir;

    float dt  = clamp(0.05 * r, 0.030, 0.85);
    vec3  acc = -1.5 * h2 * pos / (r * r * r * r * r);
    dir += acc * dt;
    pos += dir * dt;

    /* ---- equatorial plane crossing => accretion disk sample ---- */
    if (prevPos.y * pos.y < 0.0) {
      float k   = prevPos.y / (prevPos.y - pos.y);
      vec3  hit = mix(prevPos, pos, k);
      float rr  = length(hit.xz);

      if (rr > DISK_IN && rr < DISK_OUT) {
        float dY = abs(mix(prevDir.y, dir.y, k));
        float pf = clamp(0.30 / max(dY, 0.02), 0.4, 4.5);   /* grazing path length */

        /* differential (Keplerian) rotation of the turbulence */
        float om = 1.9 / pow(rr, 1.5);
        float a  = om * t;
        float ca = cos(a), sa = sin(a);
        vec3  pr = vec3(ca * hit.x - sa * hit.z, 0.0, sa * hit.x + ca * hit.z);

        float n = fbm(pr * 0.55);
        n = smoothstep(0.22, 0.88, n);

        float x       = (rr - DISK_IN) / (DISK_OUT - DISK_IN);
        float radial  = pow(DISK_IN / rr, 1.3) * (1.0 + 1.8 * exp(-(rr - DISK_IN) * 1.6));
        float edgeIn  = smoothstep(DISK_IN, DISK_IN + 0.30, rr);
        float edgeOut = 1.0 - smoothstep(DISK_OUT * 0.72, DISK_OUT, rr);
        float shape   = radial * edgeIn * edgeOut;

        float dens  = shape * (0.15 + 1.55 * n) * pf;
        float alpha = 1.0 - exp(-dens * 1.6);

        col   += trans * diskColor(x) * dens * 0.95;
        trans *= (1.0 - alpha);

        if (trans < 0.003) break;
      }
    }
  }

  /* ---------------- photon ring + halo ---------------- */
  if (!captured) {
    float ring = exp(-pow((rMin - 1.53) / 0.075, 2.0));
    float halo = exp(-pow((rMin - 1.53) / 0.32,  2.0));
    col += trans * vec3(1.00, 0.86, 0.62) * ring * 0.85;
    col += trans * vec3(1.00, 0.55, 0.26) * halo * 0.055;
  }

  /* ---------------- background (lensed starfield) ---------------- */
  if (!captured && (escaped || length(pos) > 6.0)) {
    col += trans * skyColor(normalize(dir));
  }

  /* ---------------- tonemap ---------------- */
  col *= 1.10;
  col  = aces(col);
  col  = pow(col, vec3(1.0 / 2.2));

  fragColor = vec4(col, 1.0);
}
`;

  /* ------------------------------------------------------------------ */
  /*  WebGL setup                                                        */
  /* ------------------------------------------------------------------ */

  function compile(type, src) {
    const s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
      console.error(gl.getShaderInfoLog(s));
      throw new Error("Shader compile failed");
    }
    return s;
  }

  const prog = gl.createProgram();
  gl.attachShader(prog, compile(gl.VERTEX_SHADER, VS_SRC));
  gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, FS_SRC));
  gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
    console.error(gl.getProgramInfoLog(prog));
    throw new Error("Program link failed");
  }
  gl.useProgram(prog);

  const uRes  = gl.getUniformLocation(prog, "uRes");
  const uTime = gl.getUniformLocation(prog, "uTime");

  /* one big triangle covers the whole clip-space quad */
  const vao = gl.createVertexArray();
  gl.bindVertexArray(vao);
  const vbo = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);

  const aPos = gl.getAttribLocation(prog, "aPos");
  gl.enableVertexAttribArray(aPos);
  gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);

  /* ------------------------------------------------------------------ */
  /*  Resize handling                                                    */
  /* ------------------------------------------------------------------ */

  let W = 0, H = 0;

  function resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    let w = Math.max(1, Math.floor(window.innerWidth  * dpr));
    let h = Math.max(1, Math.floor(window.innerHeight * dpr));

    const MAX_PIX = 2300000;
    if (w * h > MAX_PIX) {
      const s = Math.sqrt(MAX_PIX / (w * h));
      w = Math.max(1, Math.floor(w * s));
      h = Math.max(1, Math.floor(h * s));
    }

    if (w !== W || h !== H) {
      W = w; H = h;
      canvas.width  = w;
      canvas.height = h;
      gl.viewport(0, 0, w, h);
    }
  }

  window.addEventListener("resize", resize, { passive: true });
  window.addEventListener("orientationchange", resize, { passive: true });
  resize();

  /* ------------------------------------------------------------------ */
  /*  Render loop                                                        */
  /* ------------------------------------------------------------------ */

  let startTime = null;

  function frame(ts) {
    if (startTime === null) startTime = ts;
    const t = (ts - startTime) * 0.001;

    resize();

    gl.uniform2f(uRes, W, H);
    gl.uniform1f(uTime, t);
    gl.drawArrays(gl.TRIANGLES, 0, 3);

    requestAnimationFrame(frame);
  }

  requestAnimationFrame(frame);
})();
</script>
</body>
</html>
```
### Black Hole Simulation: Rendering, Motion & Controls

The page runs entirely in the fragment shader, so every pixel is computed in real time.

- **Gravitational lensing** – Ray directions are bent using a Schwarzschild geodesic approximation, making the far side of the disk arc over and under the event horizon. The starfield background is distorted by the same light-bending math.
- **Accretion disk** – A hot orange-white inner edge fades into cooler red outer regions. Turbulence is generated with fractal noise and sheared by a Keplerian rotation speed, so the disk appears to spin.
- **Event horizon & photon ring** – Rays that fall below radius 1.0 are captured as pitch black. A thin bright ring and subtle halo are added around the photon sphere at about 1.5 Schwarzschild radii.
- **Camera & time** – The camera slowly orbits and tilts using the `requestAnimationFrame` timestamp. The animation starts automatically, fills the window, and handles resizing without any interaction.
---

**Optimization Tip:** You can adjust `DISK_IN` and `DISK_OUT` in the fragment shader to change the disk's inner and outer radii, or modify the camera orbit speed by changing `0.065` inside the `az` calculation.