```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Room in Moving Light — WebGL2 Path Tracer</title>
<style>
  html, body { margin: 0; width: 100%; height: 100%; overflow: hidden; background: #121416; }
  canvas { display: block; width: 100%; height: 100%; }
  #label {
    position: fixed; left: 16px; top: 15px; z-index: 2;
    color: #f4eee2; background: rgba(15, 17, 18, .68);
    border: 1px solid rgba(255,255,255,.16); border-radius: 5px;
    padding: 8px 11px; font: 12px/1.2 system-ui, sans-serif;
    letter-spacing: .035em; pointer-events: none;
    box-shadow: 0 2px 12px rgba(0,0,0,.2);
  }
  #label span { color: #e6c78b; }
  #error {
    display: none; position: fixed; inset: 0; padding: 24px;
    color: white; background: #161616; font: 14px/1.5 monospace;
    white-space: pre-wrap; z-index: 3;
  }
</style>
</head>
<body>
<canvas id="view"></canvas>
<div id="label"><span>LIVE PATH TRACE</span> &nbsp;·&nbsp; <b id="samples">0</b> samples</div>
<div id="error"></div>

<script>
(() => {
  const canvas = document.getElementById('view');
  const sampleLabel = document.getElementById('samples');
  const errorBox = document.getElementById('error');
  const gl = canvas.getContext('webgl2', {
    alpha: false, antialias: false, depth: false, stencil: false,
    preserveDrawingBuffer: false, powerPreference: 'high-performance'
  });

  if (!gl) {
    errorBox.style.display = 'block';
    errorBox.textContent = 'This scene needs a browser with WebGL2 enabled.';
    return;
  }

  const vertexSource = `#version 300 es
  precision highp float;
  out vec2 vUv;
  void main() {
    vec2 p = vec2(float((gl_VertexID << 1) & 2), float(gl_VertexID & 2));
    vUv = p * 0.5;
    gl_Position = vec4(p * 2.0 - 1.0, 0.0, 1.0);
  }`;

  const traceSource = `#version 300 es
  precision highp float;
  precision highp int;

  in vec2 vUv;
  out vec4 outColor;

  uniform vec2 uResolution;
  uniform float uTime;
  uniform float uFrame;
  uniform sampler2D uPrevious;
  uniform vec3 uCamPos;
  uniform vec3 uCamRight;
  uniform vec3 uCamUp;
  uniform vec3 uCamForward;

  #define PI 3.14159265359

  uint rngState;
  float randomFloat() {
    rngState ^= rngState << 13;
    rngState ^= rngState >> 17;
    rngState ^= rngState << 5;
    return float(rngState) * (1.0 / 4294967296.0);
  }

  float sdBox(vec3 p, vec3 b) {
    vec3 q = abs(p) - b;
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0);
  }

  float sdRoundBox(vec3 p, vec3 b, float r) {
    vec3 q = abs(p) - b;
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0) - r;
  }

  float sdCappedCylinder(vec3 p, float h, float r) {
    vec2 d = abs(vec2(length(p.xz), p.y)) - vec2(r, h);
    return min(max(d.x, d.y), 0.0) + length(max(d, 0.0));
  }

  float sdCappedCone(vec3 p, float h, float r1, float r2) {
    vec2 q = vec2(length(p.xz), p.y);
    vec2 k1 = vec2(r2, h);
    vec2 k2 = vec2(r2-r1, 2.0*h);
    vec2 ca = vec2(q.x-min(q.x, q.y < 0.0 ? r1 : r2), abs(q.y)-h);
    vec2 cb = q-k1+k2*clamp(dot(k1-q,k2)/dot(k2,k2), 0.0, 1.0);
    float s = (cb.x < 0.0 && ca.y < 0.0) ? -1.0 : 1.0;
    return s*sqrt(min(dot(ca,ca), dot(cb,cb)));
  }

  vec2 choose(vec2 a, vec2 b) { return a.x < b.x ? a : b; }
  vec2 boxObj(vec3 p, vec3 c, vec3 b, float id) {
    return vec2(sdBox(p-c,b), id);
  }
  vec2 roundObj(vec3 p, vec3 c, vec3 b, float r, float id) {
    return vec2(sdRoundBox(p-c,b,r), id);
  }

  // Material IDs: floor 1, ceiling 2, plaster 3, wood 4, sofa 5,
  // glass 6, metal 7, mirror 8, window trim 9, lamp shade 10.
  vec2 scene(vec3 p) {
    vec2 h = vec2(1e4, 0.0);

    // Enclosed room, with a large opening in the far wall for the window.
    h = choose(h, boxObj(p, vec3(0.0,-0.13,-0.5), vec3(5.0,0.13,5.55), 1.0));
    h = choose(h, boxObj(p, vec3(0.0,5.18,-0.5), vec3(5.0,0.18,5.55), 2.0));
    h = choose(h, boxObj(p, vec3(-5.08,2.5,-0.5), vec3(0.12,2.5,5.55), 3.0));
    h = choose(h, boxObj(p, vec3( 5.08,2.5,-0.5), vec3(0.12,2.5,5.55), 3.0));
    // Back wall segments leave a window from x=-2.15..2.15, y=1.35..4.15.
    h = choose(h, boxObj(p, vec3(-3.62,2.55,-6.08), vec3(1.46,2.55,0.14), 3.0));
    h = choose(h, boxObj(p, vec3( 3.62,2.55,-6.08), vec3(1.46,2.55,0.14), 3.0));
    h = choose(h, boxObj(p, vec3(0.0,0.67,-6.08), vec3(2.16,0.67,0.14), 3.0));
    h = choose(h, boxObj(p, vec3(0.0,4.67,-6.08), vec3(2.16,0.51,0.14), 3.0));

    // Window frame and a narrow central mullion.
    h = choose(h, boxObj(p, vec3(-2.12,2.75,-5.86), vec3(0.055,1.48,0.075), 9.0));
    h = choose(h, boxObj(p, vec3( 2.12,2.75,-5.86), vec3(0.055,1.48,0.075), 9.0));
    h = choose(h, boxObj(p, vec3(0.0,1.37,-5.86), vec3(2.16,0.055,0.075), 9.0));
    h = choose(h, boxObj(p, vec3(0.0,4.12,-5.86), vec3(2.16,0.055,0.075), 9.0));
    h = choose(h, boxObj(p, vec3(0.0,2.75,-5.91), vec3(0.035,1.32,0.045), 9.0));

    // Large framed wall mirror on the right-hand wall.
    h = choose(h, boxObj(p, vec3(4.82,2.8,-1.55), vec3(0.045,1.18,1.27), 8.0));
    h = choose(h, boxObj(p, vec3(4.755,2.8,-1.55), vec3(0.025,1.27,1.36), 4.0));

    // Sofa: plump seat, back, arms, and two soft cushions.
    h = choose(h, roundObj(p, vec3(-1.48,0.64,-0.43), vec3(1.12,0.28,0.78), 0.10, 5.0));
    h = choose(h, roundObj(p, vec3(-1.48,1.27,-1.08), vec3(1.10,0.72,0.23), 0.10, 5.0));
    h = choose(h, roundObj(p, vec3(-2.48,0.92,-0.40), vec3(0.22,0.52,0.81), 0.10, 5.0));
    h = choose(h, roundObj(p, vec3(-0.48,0.92,-0.40), vec3(0.22,0.52,0.81), 0.10, 5.0));
    h = choose(h, roundObj(p, vec3(-1.99,1.08,-0.43), vec3(0.42,0.33,0.18), 0.10, 5.0));
    h = choose(h, roundObj(p, vec3(-0.98,1.08,-0.43), vec3(0.42,0.33,0.18), 0.10, 5.0));
    // Short, dark timber feet.
    h = choose(h, boxObj(p, vec3(-2.30,0.18, 0.18), vec3(0.09,0.18,0.09), 4.0));
    h = choose(h, boxObj(p, vec3(-0.66,0.18, 0.18), vec3(0.09,0.18,0.09), 4.0));
    h = choose(h, boxObj(p, vec3(-2.30,0.18,-0.98), vec3(0.09,0.18,0.09), 4.0));
    h = choose(h, boxObj(p, vec3(-0.66,0.18,-0.98), vec3(0.09,0.18,0.09), 4.0));

    // Solid walnut coffee table and four legs.
    h = choose(h, boxObj(p, vec3(0.92,0.96,-1.05), vec3(1.16,0.09,0.76), 4.0));
    h = choose(h, boxObj(p, vec3(0.08,0.48,-1.58), vec3(0.065,0.40,0.065), 4.0));
    h = choose(h, boxObj(p, vec3(1.76,0.48,-1.58), vec3(0.065,0.40,0.065), 4.0));
    h = choose(h, boxObj(p, vec3(0.08,0.48,-0.52), vec3(0.065,0.40,0.065), 4.0));
    h = choose(h, boxObj(p, vec3(1.76,0.48,-0.52), vec3(0.065,0.40,0.065), 4.0));

    // Open-sided drinking glass: outer wall minus inner cavity, plus its base.
    float outerGlass = sdCappedCylinder(p-vec3(0.45,1.34,-0.94), 0.30, 0.145);
    float innerGlass = sdCappedCylinder(p-vec3(0.45,1.40,-0.94), 0.25, 0.119);
    h = choose(h, vec2(max(outerGlass,-innerGlass), 6.0));

    // Small articulated metal lamp on the table.
    h = choose(h, vec2(sdCappedCylinder(p-vec3(1.52,1.105,-1.12),0.045,0.22),7.0));
    h = choose(h, vec2(sdCappedCylinder(p-vec3(1.52,1.34,-1.12),0.20,0.035),7.0));
    h = choose(h, vec2(sdCappedCone(p-vec3(1.52,1.67,-1.12),0.22,0.25,0.135),10.0));
    h = choose(h, vec2(sdCappedCylinder(p-vec3(1.52,1.435,-1.12),0.025,0.11),7.0));

    return h;
  }

  vec3 getNormal(vec3 p) {
    float e = 0.0015;
    return normalize(vec3(
      scene(p+vec3(e,0,0)).x-scene(p-vec3(e,0,0)).x,
      scene(p+vec3(0,e,0)).x-scene(p-vec3(0,e,0)).x,
      scene(p+vec3(0,0,e)).x-scene(p-vec3(0,0,e)).x
    ));
  }

  vec2 march(vec3 ro, vec3 rd) {
    float t = 0.0;
    float id = 0.0;
    for (int i=0; i<96; i++) {
      vec2 h = scene(ro+rd*t);
      if (h.x < 0.0025) { id = h.y; return vec2(t,id); }
      t += max(h.x*0.82, 0.004);
      if (t > 36.0) break;
    }
    return vec2(-1.0,0.0);
  }

  bool sunVisible(vec3 p, vec3 n, vec3 lightDir) {
    vec3 ro = p + n*0.018;
    float t = 0.0;
    for (int i=0; i<48; i++) {
      float d = scene(ro+lightDir*t).x;
      if (d < 0.012) return false;
      t += max(d*0.85,0.012);
      if (t > 22.0) return true;
    }
    return true;
  }

  vec3 hemisphereDirection(vec3 n) {
    float r1 = 2.0*PI*randomFloat();
    float r2 = randomFloat();
    float r2s = sqrt(r2);
    vec3 w = n;
    vec3 a = abs(w.y) < 0.999 ? vec3(0,1,0) : vec3(1,0,0);
    vec3 u = normalize(cross(a,w));
    vec3 v = cross(w,u);
    return normalize(u*cos(r1)*r2s + v*sin(r1)*r2s + w*sqrt(1.0-r2));
  }

  vec3 environment(vec3 d) {
    float sky = clamp(d.y*0.5+0.5,0.0,1.0);
    return mix(vec3(0.18,0.16,0.13), vec3(0.50,0.66,0.86), sky);
  }

  vec3 materialColor(float id, vec3 p) {
    if (id < 1.5) {
      // Individual oak planks, staggered end joints, subtle grain and knots.
      float row = floor(p.x/0.58);
      float x = p.x/0.58;
      float z = (p.z + mod(row,2.0)*0.68)/1.36;
      vec2 f = abs(fract(vec2(x,z))-0.5);
      float seams = smoothstep(0.465,0.495,max(f.x,f.y));
      float grain = 0.91 + 0.055*sin(p.z*29.0 + sin(p.x*13.0)*2.0)
                         + 0.025*sin(p.z*83.0+p.x*7.0);
      float board = 0.88 + 0.12*sin(row*17.13+3.0);
      vec3 wood = vec3(0.43,0.235,0.105)*grain*board;
      wood *= mix(1.0,0.22,seams);
      float knot = smoothstep(0.18,0.0,length(vec2(fract(p.x*2.2)-0.5,fract(p.z*1.1)-0.5)));
      wood *= 1.0-0.14*knot;
      return wood;
    }
    if (id < 2.5) return vec3(0.68,0.66,0.61);
    if (id < 3.5) {
      float plaster = 0.985 + 0.012*sin(p.x*31.0+p.y*21.0)*sin(p.z*18.0);
      return vec3(0.70,0.68,0.62)*plaster;
    }
    if (id < 4.5) {
      float grain = 0.92+0.08*sin(p.z*40.0+sin(p.x*19.0)*1.6);
      return vec3(0.29,0.145,0.065)*grain;
    }
    if (id < 5.5) {
      float weave = 0.97 + 0.025*sin(p.x*145.0)*sin(p.y*155.0);
      return vec3(0.28,0.38,0.39)*weave;
    }
    if (id < 6.5) return vec3(0.82,0.94,0.98);
    if (id < 7.5) return vec3(0.72,0.74,0.76);
    if (id < 8.5) return vec3(0.96,0.98,1.0);
    if (id < 9.5) return vec3(0.24,0.13,0.055);
    return vec3(0.48,0.29,0.12);
  }

  vec3 tracePath(vec3 ro, vec3 rd) {
    vec3 throughput = vec3(1.0);
    vec3 radiance = vec3(0.0);

    // The light vector slowly tracks a changing sun outside the window.
    float sunAngle = uTime*0.105 - 0.7;
    vec3 lightDir = normalize(vec3(0.48*sin(sunAngle), 0.68, -0.73));
    vec3 sunColor = vec3(1.0,0.84,0.64);

    for (int bounce=0; bounce<4; bounce++) {
      vec2 hit = march(ro,rd);
      if (hit.x < 0.0) {
        radiance += throughput*environment(rd);
        break;
      }

      vec3 p = ro + rd*hit.x;
      vec3 n = getNormal(p);
      if (dot(n,rd)>0.0) n = -n;
      float id = hit.y;
      vec3 base = materialColor(id,p);

      if (id > 9.5) {
        radiance += throughput*vec3(0.78,0.43,0.17)*0.65;
        // A warm lampshade, but not a dominant fake fill light.
      }

      if (id > 7.5 && id < 8.5) {
        // A clean, nearly perfect wall mirror.
        throughput *= vec3(0.94,0.95,0.97);
        rd = reflect(rd,n);
        ro = p+n*0.012;
        continue;
      }

      if (id > 6.5 && id < 7.5) {
        // Brushed metal: sharp reflection with a restrained roughness.
        vec3 reflected = reflect(rd,n);
        vec3 fuzz = normalize(vec3(randomFloat()-0.5,randomFloat()-0.5,randomFloat()-0.5));
        rd = normalize(reflected + 0.055*fuzz);
        throughput *= base;
        ro = p+n*0.012;
        continue;
      }

      if (id > 5.5 && id < 6.5) {
        // Fresnel reflection/refraction through the hollow glass walls.
        bool entering = dot(rd,n) < 0.0;
        vec3 normal = entering ? n : -n;
        float eta = entering ? (1.0/1.46) : 1.46;
        float cosTheta = clamp(dot(-rd,normal),0.0,1.0);
        float r0 = (1.0-1.46)/(1.0+1.46);
        r0 *= r0;
        float fresnel = r0+(1.0-r0)*pow(1.0-cosTheta,5.0);
        vec3 refracted = refract(rd,normal,eta);
        if (dot(refracted,refracted)<0.0001 || randomFloat()<fresnel) {
          rd = reflect(rd,normal);
          ro = p+normal*0.012;
        } else {
          rd = normalize(refracted);
          throughput *= vec3(0.985,0.995,1.0);
          ro = p-rd*0.012;
        }
        continue;
      }

      // Direct sunlight with real visibility through the window and soft-ish
      // penumbrae from the finite march tolerance.
      float ndl = max(dot(n,lightDir),0.0);
      if (ndl>0.0 && sunVisible(p,n,lightDir)) {
        float sunStrength = 2.6 + 0.35*sin(uTime*0.07);
        radiance += throughput*base*sunColor*ndl*sunStrength;
      }

      // Diffuse continuation gives the room multi-bounce colour bleeding.
      throughput *= base;
      if (bounce >= 2) {
        float survive = clamp(max(throughput.r,max(throughput.g,throughput.b)),0.12,0.88);
        if (randomFloat()>survive) break;
        throughput /= survive;
      }
      rd = hemisphereDirection(n);
      ro = p+n*0.012;
    }
    return radiance;
  }

  void main() {
    ivec2 pixel = ivec2(gl_FragCoord.xy);
    uint seed = uint(pixel.x)*1973u + uint(pixel.y)*9277u
              + uint(uFrame)*26699u + 911u;
    rngState = seed | 1u;

    vec3 current = vec3(0.0);
    const int SPP = 2;
    for (int s=0; s<SPP; s++) {
      vec2 jitter = vec2(randomFloat(),randomFloat());
      vec2 screen = ((gl_FragCoord.xy + jitter)/uResolution)*2.0-1.0;
      screen.x *= uResolution.x/uResolution.y;

      vec3 rd = normalize(uCamForward + uCamRight*screen.x*0.64 + uCamUp*screen.y*0.64);
      // A small aperture and a gently defocused focal plane.
      float focalDistance = 5.0;
      vec3 focusPoint = uCamPos + rd*focalDistance;
      float lensAngle = 2.0*PI*randomFloat();
      float lensRadius = 0.018*sqrt(randomFloat());
      vec3 lensOffset = (uCamRight*cos(lensAngle)+uCamUp*sin(lensAngle))*lensRadius;
      vec3 rayOrigin = uCamPos+lensOffset;
      rd = normalize(focusPoint-rayOrigin);
      current += tracePath(rayOrigin,rd);
    }
    current /= float(SPP);

    // A rolling temporal accumulation stays responsive while the camera and
    // sunlight continue moving; it never settles into a frozen still.
    vec3 oldColor = texture(uPrevious,vUv).rgb;
    float blend = uFrame < 1.0 ? 1.0 : 0.14;
    vec3 accumulated = mix(oldColor,current,blend);
    outColor = vec4(accumulated,1.0);
  }`;

  const displaySource = `#version 300 es
  precision highp float;
  in vec2 vUv;
  out vec4 outColor;
  uniform sampler2D uImage;
  void main() {
    vec3 c = texture(uImage,vUv).rgb;
    c = vec3(1.0)-exp(-c*1.06);
    c = pow(max(c,vec3(0.0)),vec3(1.0/2.2));
    float vignette = smoothstep(1.45,0.30,length(vUv-0.5));
    c *= mix(0.82,1.0,vignette);
    outColor = vec4(c,1.0);
  }`;

  function makeShader(type, source) {
    const shader = gl.createShader(type);
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      throw new Error(gl.getShaderInfoLog(shader) || 'Shader compilation failed');
    }
    return shader;
  }

  function makeProgram(fsSource) {
    const program = gl.createProgram();
    gl.attachShader(program, makeShader(gl.VERTEX_SHADER, vertexSource));
    gl.attachShader(program, makeShader(gl.FRAGMENT_SHADER, fsSource));
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      throw new Error(gl.getProgramInfoLog(program) || 'Program link failed');
    }
    return program;
  }

  let traceProgram, displayProgram;
  try {
    traceProgram = makeProgram(traceSource);
    displayProgram = makeProgram(displaySource);
  } catch (e) {
    errorBox.style.display = 'block';
    errorBox.textContent = String(e);
    return;
  }

  const traceUniforms = {};
  for (const name of ['uResolution','uTime','uFrame','uPrevious',
                       'uCamPos','uCamRight','uCamUp','uCamForward']) {
    traceUniforms[name] = gl.getUniformLocation(traceProgram,name);
  }
  const displayImageLoc = gl.getUniformLocation(displayProgram,'uImage');
  const vao = gl.createVertexArray();
  gl.bindVertexArray(vao);

  const floatTarget = !!gl.getExtension('EXT_color_buffer_float');
  const texInternal = floatTarget ? gl.RGBA16F : gl.RGBA8;
  const texType = floatTarget ? gl.HALF_FLOAT : gl.UNSIGNED_BYTE;
  let targets = [];
  let width = 0, height = 0, frame = 0;

  function makeTarget() {
    const texture = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D,texture);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
    gl.texImage2D(gl.TEXTURE_2D,0,texInternal,width,height,0,gl.RGBA,texType,null);
    const fbo = gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER,fbo);
    gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.COLOR_ATTACHMENT0,gl.TEXTURE_2D,texture,0);
    if (gl.checkFramebufferStatus(gl.FRAMEBUFFER)!==gl.FRAMEBUFFER_COMPLETE) {
      throw new Error('Could not create the path-tracing accumulation buffer.');
    }
    return {texture,fbo};
  }

  function resize() {
    const scale = Math.min(1.0, 960/Math.max(1,innerWidth), 640/Math.max(1,innerHeight));
    const w = Math.max(1,Math.floor(innerWidth*scale));
    const h = Math.max(1,Math.floor(innerHeight*scale));
    if (w===width && h===height) return;
    width=w; height=h;
    canvas.width=w; canvas.height=h;
    gl.viewport(0,0,w,h);
    for (const t of targets) {
      gl.deleteTexture(t.texture);
      gl.deleteFramebuffer(t.fbo);
    }
    targets=[];
    try {
      targets=[makeTarget(),makeTarget()];
      for (const t of targets) {
        gl.bindFramebuffer(gl.FRAMEBUFFER,t.fbo);
        gl.clearColor(0,0,0,1);
        gl.clear(gl.COLOR_BUFFER_BIT);
      }
      gl.bindFramebuffer(gl.FRAMEBUFFER,null);
      frame=0;
    } catch(e) {
      errorBox.style.display='block';
      errorBox.textContent=String(e);
    }
  }
  addEventListener('resize',resize);
  resize();

  function normalize(v) {
    const l=Math.hypot(v[0],v[1],v[2])||1;
    return [v[0]/l,v[1]/l,v[2]/l];
  }
  function cross(a,b) {
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
  }

  const start = performance.now();
  let lastLabel = 0;

  function render(now) {
    if (!targets.length) { requestAnimationFrame(render); return; }
    const time=(now-start)*0.001;

    // A continuous, slow orbit reveals the sofa, window, table, and mirror.
    const angle=time*(Math.PI*2/48.0)+0.10;
    const camPos=[3.25*Math.sin(angle),1.67,-0.65+3.25*Math.cos(angle)];
    const target=[0.05,1.48,-1.25];
    const forward=normalize([target[0]-camPos[0],target[1]-camPos[1],target[2]-camPos[2]]);
    const right=normalize(cross(forward,[0,1,0]));
    const up=normalize(cross(right,forward));

    const writeIndex=frame%2;
    const readIndex=1-writeIndex;
    const dst=targets[writeIndex];
    const src=targets[readIndex];

    gl.bindFramebuffer(gl.FRAMEBUFFER,dst.fbo);
    gl.viewport(0,0,width,height);
    gl.useProgram(traceProgram);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D,src.texture);
    gl.uniform1i(traceUniforms.uPrevious,0);
    gl.uniform2f(traceUniforms.uResolution,width,height);
    gl.uniform1f(traceUniforms.uTime,time);
    gl.uniform1f(traceUniforms.uFrame,frame);
    gl.uniform3f(traceUniforms.uCamPos,...camPos);
    gl.uniform3f(traceUniforms.uCamRight,...right);
    gl.uniform3f(traceUniforms.uCamUp,...up);
    gl.uniform3f(traceUniforms.uCamForward,...forward);
    gl.drawArrays(gl.TRIANGLES,0,3);

    gl.bindFramebuffer(gl.FRAMEBUFFER,null);
    gl.viewport(0,0,width,height);
    gl.useProgram(displayProgram);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D,dst.texture);
    gl.uniform1i(displayImageLoc,0);
    gl.drawArrays(gl.TRIANGLES,0,3);

    frame++;
    if (now-lastLabel>120) {
      sampleLabel.textContent=(frame*2).toLocaleString();
      lastLabel=now;
    }
    requestAnimationFrame(render);
  }
  requestAnimationFrame(render);
})();
</script>
</body>
</html>
```