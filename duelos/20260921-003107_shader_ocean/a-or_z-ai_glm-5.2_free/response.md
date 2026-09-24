```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Stormy Ocean at Sunset</title>
<style>
  html, body { margin: 0; padding: 0; height: 100%; overflow: hidden; background: #000; }
  canvas { display: block; width: 100vw; height: 100vh; }
</style>
</head>
<body>
<canvas id="c"></canvas>
<script>
const canvas = document.getElementById('c');
const gl = canvas.getContext('webgl2', { antialias: false, powerPreference: 'high-performance' });

function resize() {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width  = Math.floor(window.innerWidth  * dpr);
  canvas.height = Math.floor(window.innerHeight * dpr);
  gl.viewport(0, 0, canvas.width, canvas.height);
}
window.addEventListener('resize', resize);
resize();

const vs = `#version 300 es
in vec2 aPos;
void main(){ gl_Position = vec4(aPos, 0.0, 1.0); }`;

const fs = `#version 300 es
precision highp float;
uniform vec2 uResolution;
uniform float uTime;
out vec4 fragColor;

float hash(vec2 p){
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}
float noise(vec2 p){
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f*f*(3.0 - 2.0*f);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    return mix(mix(a,b,f.x), mix(c,d,f.x), f.y);
}
float fbm(vec2 p){
    float v = 0.0, a = 0.5;
    mat2 m = mat2(1.6, 1.2, -1.2, 1.6);
    for(int i = 0; i < 6; i++){
        v += a * noise(p);
        p = m * p;
        a *= 0.5;
    }
    return v;
}
float fbmCloud(vec2 p){
    float v = 0.0, a = 0.55;
    for(int i = 0; i < 5; i++){
        v += a * noise(p);
        p = p * 2.02;
        a *= 0.5;
    }
    return v;
}

const float WAVE_AMP = 0.55;

float waveHeight(vec2 p, float t){
    float h = 0.0;
    h += 0.55 * fbm(p * 0.12 + vec2(t * 0.05,  t * 0.02));
    h += 0.28 * fbm(p * 0.35 + vec2(-t * 0.09, t * 0.04));
    h += 0.14 * fbm(p * 0.80 + vec2(t * 0.14, -t * 0.07));
    h += 0.07 * fbm(p * 1.60 + vec2(t * 0.20,  t * 0.10));
    return h * WAVE_AMP * 1.5 - 0.20;
}

vec3 getNormal(vec2 p, float t){
    float e = 0.10;
    float h0 = waveHeight(p, t);
    float hx = waveHeight(p + vec2(e, 0.0), t);
    float hz = waveHeight(p + vec2(0.0, e), t);
    return normalize(vec3(h0 - hx, e, h0 - hz));
}

const vec3 SUN_DIR = normalize(vec3(0.35, 0.06, -1.0));
const vec3 SUN_COL = vec3(1.65, 0.78, 0.34);

vec3 skyColor(vec3 dir, float t){
    float y = clamp(dir.y, -0.05, 1.0);
    vec3 horizon = vec3(0.98, 0.45, 0.20);
    vec3 mid     = vec3(0.30, 0.14, 0.20);
    vec3 zenith  = vec3(0.03, 0.04, 0.11);
    vec3 col = mix(horizon, mid, smoothstep(0.0, 0.22, y));
    col = mix(col, zenith, smoothstep(0.22, 0.75, y));

    // dark stormy clouds
    if(dir.y > 0.02){
        float scale = 1.0 / max(dir.y, 0.06);
        vec2 cuv = dir.xz * scale * 0.45 + vec2(t * 0.018, t * 0.006);
        float c = fbmCloud(cuv);
        c = smoothstep(0.42, 0.85, c);
        float sunAlign = max(dot(dir, SUN_DIR), 0.0);
        vec3 dark = vec3(0.07, 0.06, 0.09);
        vec3 lit  = vec3(0.75, 0.38, 0.22);
        vec3 cloudCol = mix(dark, lit, pow(sunAlign, 2.0) * smoothstep(0.0, 0.35, y));
        col = mix(col, cloudCol, c * 0.88);
    }

    // sun disk + glow
    float sd = max(dot(dir, SUN_DIR), 0.0);
    col += SUN_COL * pow(sd, 350.0) * 2.2;
    col += SUN_COL * pow(sd, 35.0)  * 0.55;
    col += SUN_COL * pow(sd, 6.0)   * 0.18;

    return col;
}

void main(){
    vec2 uv = (gl_FragCoord.xy - 0.5 * uResolution.xy) / uResolution.y;
    float t = uTime * 0.001;

    // camera bobbing as if on a boat
    vec3 camPos = vec3(
        sin(t * 0.27) * 0.6,
        1.75 + sin(t * 0.50) * 0.28 + sin(t * 0.37 + 1.3) * 0.18,
        sin(t * 0.19) * 0.6
    );

    vec3 forward = normalize(vec3(0.0, -0.08, -1.0));
    vec3 right   = normalize(cross(vec3(0.0, 1.0, 0.0), forward));
    vec3 up      = cross(forward, right);

    // gentle roll + pitch bob
    float roll  = sin(t * 0.45) * 0.045 + sin(t * 0.21) * 0.022;
    float pitch = sin(t * 0.33) * 0.025;
    right   = normalize(right * cos(roll) + up * sin(roll));
    up      = cross(forward, right);
    forward = normalize(forward * cos(pitch) + up * sin(pitch));
    up      = cross(forward, right);

    vec3 rayDir = normalize(forward + uv.x * right * 1.3 + uv.y * up * 1.0);

    vec3 col;

    if(rayDir.y >= 0.0){
        col = skyColor(rayDir, t);
    } else {
        // raymarch the ocean heightfield
        float tt = 0.4;
        float hit = -1.0;
        for(int i = 0; i < 140; i++){
            vec3 p = camPos + rayDir * tt;
            float h = waveHeight(p.xz, t);
            if(p.y < h){ hit = tt; break; }
            tt += max(0.025, (p.y - h) * 0.35);
            if(tt > 120.0) break;
        }

        if(hit < 0.0){
            col = skyColor(rayDir, t);
        } else {
            vec3 p = camPos + rayDir * hit;
            vec3 n = getNormal(p.xz, t);
            vec3 viewDir = -rayDir;

            float fresnel = pow(1.0 - max(dot(n, viewDir), 0.0), 4.0);
            fresnel = clamp(fresnel * 1.25, 0.0, 1.0);

            vec3 reflected = reflect(rayDir, n);
            vec3 skyRefl = skyColor(reflected, t);

            float spec  = pow(max(dot(reflected, SUN_DIR), 0.0), 110.0);
            float spec2 = pow(max(dot(reflected, SUN_DIR), 0.0), 22.0);

            vec3 deepWater    = vec3(0.02, 0.05, 0.09);
            vec3 shallowWater = vec3(0.08, 0.18, 0.22);
            float depthFactor = clamp((p.y + 0.5) * 0.8, 0.0, 1.0);
            vec3 waterCol = mix(deepWater, shallowWater, depthFactor);

            col = mix(waterCol, skyRefl, fresnel);
            col += SUN_COL * spec  * 3.2;
            col += SUN_COL * spec2 * 0.45;

            // foam on crests and breaking slopes
            float wh = waveHeight(p.xz, t);
            float foam = smoothstep(0.35, 0.65, wh + 0.30);
            float slope = 1.0 - n.y;
            foam = max(foam, smoothstep(0.22, 0.55, slope) * smoothstep(0.10, 0.40, wh + 0.30));
            float foamNoise = noise(p.xz * 4.0 + t * 0.5) * noise(p.xz * 9.0 - t * 0.3);
            foam *= smoothstep(0.20, 0.60, foamNoise);
            foam = clamp(foam, 0.0, 1.0);
            col = mix(col, vec3(0.93, 0.95, 0.97), foam * 0.85);

            // fog near horizon
            float fog = 1.0 - exp(-hit * 0.028);
            vec3 horizonDir = normalize(vec3(rayDir.x, -0.001, rayDir.z));
            vec3 fogCol = skyColor(horizonDir, t);
            col = mix(col, fogCol, clamp(fog, 0.0, 1.0));
        }
    }

    // tonemap + slight grade
    col = col / (col + vec3(1.0));
    col = pow(col, vec3(0.85));
    col *= 1.12;

    fragColor = vec4(col, 1.0);
}`;

function compile(type, src){
    const s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if(!gl.getShaderParameter(s, gl.COMPILE_STATUS)){
        console.error(gl.getShaderInfoLog(s));
        throw new Error('shader compile failed');
    }
    return s;
}

const prog = gl.createProgram();
gl.attachShader(prog, compile(gl.VERTEX_SHADER, vs));
gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, fs));
gl.linkProgram(prog);
if(!gl.getProgramParameter(prog, gl.LINK_STATUS)){
    console.error(gl.getProgramInfoLog(prog));
    throw new Error('program link failed');
}
gl.useProgram(prog);

const vao = gl.createVertexArray();
gl.bindVertexArray(vao);
const buf = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, buf);
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 3,-1, -1,3]), gl.STATIC_DRAW);
const aPos = gl.getAttribLocation(prog, 'aPos');
gl.enableVertexAttribArray(aPos);
gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);

const uRes  = gl.getUniformLocation(prog, 'uResolution');
const uTime = gl.getUniformLocation(prog, 'uTime');

function render(t){
    gl.uniform2f(uRes, canvas.width, canvas.height);
    gl.uniform1f(uTime, t);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    requestAnimationFrame(render);
}
requestAnimationFrame(render);
</script>
</body>
</html>
```