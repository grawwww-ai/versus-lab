The user wants a single HTML file with a WebGL2 raymarching shader for a stormy ocean at sunset. Let me write this carefully.

Key elements:
- Full-screen quad with WebGL2
- Raymarching fragment shader
- Multiple octaves of noise for waves
- Foam on crests
- Dark clouds + low orange sun
- Sun reflection + fresnel
- Fog near horizon
- Camera bobbing
- Auto-resize, fills window
- requestAnimationFrame timestamp

Let me design the shader:

Sky: gradient + clouds (noise based)
Ocean: raymarch with heightfield from noise octaves, foam based on height/slope, fresnel reflection of sky+sun
Camera: bobbing with sin waves on time

For the raymarching, I'll do a heightmap march. Use a 2D noise for the wave height function. Then march along the ray, sampling height.

Let me write the noise function. I'll use a hash-based value noise with FBM.

For waves, I want large rolling waves — directional. I'll use noise that's stretched in one direction or sum sines + noise.

Actually a common approach: height = sum of octaves of noise (with time animation), then compute normal via gradient.

For foam: where height is high (crest) or where slope is steep, add foam color.

Sun reflection: fresnel + specular highlight toward sun direction.

Let me write this:

```glsl
#version 300 es
precision highp float;
uniform vec2 uResolution;
uniform float uTime;
out vec4 fragColor;

float hash(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f*f*(3.0-2.0*f);
    float a = hash(i);
    float b = hash(i + vec2(1,0));
    float c = hash(i + vec2(0,1));
    float d = hash(i + vec2(1,1));
    return mix(mix(a,b,f.x), mix(c,d,f.x), f.y);
}

float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.5;
    for(int i=0;i<6;i++){
        v += a * noise(p);
        p *= 2.0;
        a *= 0.5;
    }
    return v;
}
```

For waves, I want time-animated fbm. Use multiple directional noise samples.

Wave height function:
```
float waveHeight(vec2 p, float t) {
    float h = 0.0;
    h += 1.0 * fbm(p*0.5 + vec2(t*0.1, 0.0));
    h += 0.5 * fbm(p*1.0 + vec2(-t*0.15, t*0.05));
    h += 0.25 * fbm(p*2.0 + vec2(t*0.2, -t*0.1));
    return h * 0.5;
}
```

Actually for stormy ocean, want bigger amplitude. Let me tune.

Camera: position bobbing
```
vec3 camPos = vec3(0.0, 2.0 + sin(t*0.5)*0.3, 0.0);
```

Ray direction from screen:
```
vec2 uv = (gl_FragCoord.xy - 0.5*uResolution)/uResolution.y;
vec3 rayDir = normalize(vec3(uv, -1.5));
```

Hmm, I want to look slightly downward toward horizon. Let me set up camera with pitch.

Let me think about coordinate system. Camera at some height, looking toward horizon (slightly down). Ocean at y=0.

```
vec3 camPos = vec3(0.0, 1.5 + sin(t*0.4)*0.25 + sin(t*0.27)*0.15, 0.0);
vec3 camTarget = vec3(0.0, 0.5, -10.0); // looking forward and slightly down
```

Build ray dir from camera basis.

For raymarching the ocean: march from camPos along rayDir, at each step compute current position, get ocean height, if pos.y < oceanHeight we hit.

Actually for height fields, a better approach: march in t, find when ray.y - heightField(ray.xz) crosses zero.

Let me do:
```
float t = 0.0;
float hit = -1.0;
for(int i=0;i<80;i++){
    vec3 p = camPos + rayDir * t;
    float h = waveHeight(p.xz, t_time);
    if(p.y < h) { hit = t; break; }
    t += 0.05 + t*0.02; // step size grows with distance
    if(t > 60.0) break;
}
```

Wait, p.y < h means we're below the water surface — but if camera is above and ray going down, p.y decreases over t. So we want to detect when p.y crosses h from above. Start t at small value to avoid immediate hit if camera is below height.

Actually since waves oscillate around 0, and camera is at y=1.5, fine.

For computing normal: gradient of height function.

```
vec3 getNormal(vec2 p, float t) {
    float e = 0.01;
    float h0 = waveHeight(p, t);
    float hx = waveHeight(p + vec2(e,0), t);
    float hz = waveHeight(p + vec2(0,e), t);
    return normalize(vec3(h0 - hx, e, h0 - hz));
}
```

Wait this gives normal pointing up. Correct: (h0-hx)/e in x, 1 in y, (h0-hz)/e in z. So normalize(vec3((h0-hx), e, (h0-hz))) — yes.

For sky: gradient from horizon orange to zenith dark blue/purple. Plus clouds via fbm.

Sun: a disk in sky at low angle, with glow.

Fog: blend distance to horizon color.

Foam: based on height threshold and slope.

Let me write the full shader:

```glsl
#version 300 es
precision highp float;
uniform vec2 uResolution;
uniform float uTime;
out vec4 fragColor;

float hash(vec2 p){
    p = fract(p*vec2(123.34, 456.21));
    p += dot(p, p+45.32);
    return fract(p.x*p.y);
}
float noise(vec2 p){
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f*f*(3.0-2.0*f);
    float a = hash(i), b = hash(i+vec2(1,0));
    float c = hash(i+vec2(0,1)), d = hash(i+vec2(1,1));
    return mix(mix(a,b,f.x), mix(c,d,f.x), f.y);
}
float fbm(vec2 p){
    float v=0.0, a=0.5;
    for(int i=0;i<6;i++){ v += a*noise(p); p = p*2.0 + vec2(1.7, -2.3); a*=0.5; }
    return v;
}
float fbmClouds(vec2 p){
    float v=0.0, a=0.5;
    for(int i=0;i<5;i++){ v += a*noise(p); p = p*2.1; a*=0.5; }
    return v;
}

float waveHeight(vec2 p, float t){
    float h = 0.0;
    h += 0.6 * fbm(p*0.15 + vec2(t*0.06, t*0.02));
    h += 0.3 * fbm(p*0.4 + vec2(-t*0.1, t*0.05));
    h += 0.15 * fbm(p*0.9 + vec2(t*0.15, -t*0.08));
    h += 0.07 * fbm(p*1.8 + vec2(t*0.2, t*0.1));
    return h - 0.3;
}

vec3 getNormal(vec2 p, float t){
    float e = 0.05;
    float h0 = waveHeight(p, t);
    float hx = waveHeight(p+vec2(e,0), t);
    float hz = waveHeight(p+vec2(0,e), t);
    return normalize(vec3(h0-hx, e*2.0, h0-hz));
}

vec3 skyColor(vec3 dir, float t){
    float y = clamp(dir.y, 0.0, 1.0);
    vec3 horizon = vec3(0.9, 0.4, 0.2); // orange horizon
    vec3 zenith = vec3(0.05, 0.06, 0.15); // dark blue
    vec3 col = mix(horizon, zenith, pow(y, 0.5));
    
    // clouds
    if(dir.y > 0.0){
        vec2 cloudUV = dir.xz / (dir.y + 0.1) * 0.5 + vec2(t*0.01, 0.0);
        float c = fbmClouds(cloudUV);
        c = smoothstep(0.4, 0.9, c);
        vec3 cloudCol = mix(vec3(0.15, 0.1, 0.12), vec3(0.8, 0.4, 0.25), pow(y, 0.3));
        col = mix(col, cloudCol, c * 0.8);
    }
    
    // sun
    vec3 sunDir = normalize(vec3(0.3, 0.05, -1.0));
    float sd = max(dot(dir, sunDir), 0.0);
    vec3 sunCol = vec3(1.5, 0.7, 0.3);
    col += sunCol * pow(sd, 200.0) * 1.0; // disk
    col += sunCol * pow(sd, 20.0) * 0.3; // glow
    col += sunCol * pow(sd, 4.0) * 0.1; // wide glow
    
    return col;
}

void main(){
    vec2 fragCoord = gl_FragCoord.xy;
    vec2 uv = (fragCoord - 0.5*uResolution.xy) / uResolution.y;
    
    float t = uTime * 0.001; // if uTime in ms
    
    // camera bob
    vec3 camPos = vec3(
        sin(t*0.3)*0.5,
        1.6 + sin(t*0.5)*0.25 + sin(t*0.37)*0.15,
        sin(t*0.21)*0.5
    );
    
    // camera basis looking toward -z, slightly down
    vec3 forward = normalize(vec3(0.0, -0.1, -1.0));
    vec3 right = normalize(cross(vec3(0,1,0), forward));
    vec3 up = cross(forward, right);
    
    // add camera roll/pitch bob
    float roll = sin(t*0.4)*0.03;
    right = normalize(right * cos(roll) + up * sin(roll));
    up = cross(forward, right);
    
    vec3 rayDir = normalize(forward + uv.x * right * 1.2 + uv.y * up * 1.0);
    
    vec3 sunDir = normalize(vec3(0.3, 0.05, -1.0));
    
    vec3 col;
    
    if(rayDir.y > -0.01){
        // sky
        col = skyColor(rayDir, t);
    } else {
        // raymarch ocean
        float tt = 0.0;
        float hit = -1.0;
        for(int i=0;i<100;i++){
            vec3 p = camPos + rayDir * tt;
            float h = waveHeight(p.xz, t);
            if(p.y < h){ hit = tt; break; }
            tt += max(0.02, (p.y - h) * 0.3);
            if(tt > 80.0) break;
        }
        
        if(hit < 0.0){
            col = skyColor(rayDir, t);
        } else {
            // refine
            vec3 p = camPos + rayDir * hit;
            vec3 n = getNormal(p.xz, t);
            
            vec3 viewDir = -rayDir;
            float fresnel = pow(1.0 - max(dot(n, viewDir), 0.0), 3.0);
            fresnel = clamp(fresnel, 0.0, 1.0);
            
            vec3 reflected = reflect(rayDir, n);
            vec3 skyRefl = skyColor(reflected, t);
            
            // sun specular
            float spec = pow(max(dot(reflected, sunDir), 0.0), 80.0);
            vec3 sunCol = vec3(1.5, 0.7, 0.3);
            
            // water base color
            vec3 deepWater = vec3(0.02, 0.05, 0.1);
            vec3 shallowWater = vec3(0.1, 0.2, 0.3);
            vec3 waterCol = mix(deepWater, shallowWater, clamp(p.y*0.5+0.5, 0.0, 1.0));
            
            col = mix(waterCol, skyRefl, fresnel);
            col += sunCol * spec * 2.0;
            
            // foam on crests
            float foam = smoothstep(0.15, 0.3, waveHeight(p.xz, t));
            float slope = 1.0 - n.y;
            foam = max(foam, smoothstep(0.15, 0.4, slope) * smoothstep(0.0, 0.2, waveHeight(p.xz,t)+0.3));
            foam = clamp(foam, 0.0, 1.0);
            // add noise to foam
            foam *= smoothstep(0.3, 0.7, noise(p.xz*3.0 + t));
            col = mix(col, vec3(0.9, 0.92, 0.95), foam * 0.8);
            
            // fog
            float fog = 1.0 - exp(-hit * 0.015);
            vec3 fogCol = skyColor(normalize(vec3(rayDir.x, 0.0, rayDir.z)), t);
            col = mix(col, fogCol, clamp(fog, 0.0, 1.0));
        }
    }
    
    // horizon blend near y=0
    // simple tone
    col = pow(col, vec3(0.9));
    col = col / (col + vec3(1.0)); // reinhard-ish
    col *= 1.2;
    
    fragColor = vec4(col, 1.0);
}
```

Hmm wait, the issue: when rayDir.y is exactly 0 or slightly positive we go to sky, but waves near horizon could be missed. Let me always raymarch but if no hit, fall back to sky. Actually the y > -0.01 check is problematic. Let me just always march if ray.y < some threshold (meaning it could hit water), and use sky if clearly above horizon.

Actually a better approach: march for everything. If the ray points up (y > 0), it will never hit water (since camera is above water and ray going up). So just check rayDir.y < 0 to march, else sky.

But near horizon (rayDir.y ≈ 0), we want the ocean to appear properly. Let me lower threshold.

Actually simpler: always attempt raymarch. If y > 0, the loop just won't find a hit (since p.y increases). Then fall back to sky. But that wastes 100 iterations. Let me check rayDir.y < 0.

Let me handle the uTime unit. requestAnimationFrame gives ms. I'll pass it directly as uTime in ms. So t = uTime * 0.001.

Let me also add some atmospheric scattering at horizon. And make sure colors are nice.

Actually I think the structure is good. Let me refine:

- Wave amplitude: waves are ~0.6+0.3+0.15+0.07 = 1.12 max, minus 0.3 offset = 0.82. Camera at 1.6. Good.
- Make waves more dramatic for stormy: increase amplitude a bit.

Let me also reduce the y threshold to be safe. I'll always do the raymarch loop but break early if y > 0 (no possible hit since camPos.y > 0 and ray going up means p.y always increases).

Actually let me just do: if rayDir.y < 0.0, march. Else sky. The threshold for sky vs ocean at horizon will be a sharp line but that's fine because the fog will blur it visually.

Hmm but a sharp horizon line is ugly. Let me always march, but with smart early exit.

Better: march with adaptive step. If rayDir.y >= 0, return sky immediately. For rayDir.y slightly negative, the march will reach far before hitting — that's where fog blends to horizon. Should be fine.

Let me write the JS:

```js
const canvas = document.getElementById('c');
const gl = canvas.getContext('webgl2');
function resize(){
    canvas.width = window.innerWidth * devicePixelRatio;
    canvas.height = window.innerHeight * devicePixelRatio;
    canvas.style.width = window.innerWidth + 'px';
    canvas.style.height = window.innerHeight + 'px';
    gl.viewport(0,0,canvas.width,canvas.height);
}
window.addEventListener('resize', resize);
resize();

const vs = `#version 300 es
in vec2 aPos;
void main(){ gl_Position = vec4(aPos, 0.0, 1.0); }`;

const fs = `...`; // above

function compile(type, src){
    const s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if(!gl.getShaderParameter(s, gl.COMPILE_STATUS)){
        console.error(gl.getShaderInfoLog(s));
    }
    return s;
}
const prog = gl.createProgram();
gl.attachShader(prog, compile(gl.VERTEX_SHADER, vs));
gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, fs));
gl.linkProgram(prog);
gl.useProgram(prog);

const vao = gl.createVertexArray();
gl.bindVertexArray(vao);
const buf = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, buf);
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 3,-1, -1,3]), gl.STATIC_DRAW);
const aPos = gl.getAttribLocation(prog, 'aPos');
gl.enableVertexAttribArray(aPos);
gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);

const uRes = gl.getUniformLocation(prog, 'uResolution');
const uTime = gl.getUniformLocation(prog, 'uTime');

function render(t){
    gl.uniform2f(uRes, canvas.width, canvas.height);
    gl.uniform1f(uTime, t);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    requestAnimationFrame(render);
}
requestAnimationFrame(render);
```

Let me refine the shader more for visual quality. The first 30 seconds should show "everything important" — camera bob, waves, sun, foam, fresnel, clouds, fog. All these are present continuously, so 30s is plenty.

Let me make sure sun is visible and reflects on water. Sun direction (0.3, 0.05, -1.0) — low on horizon, slightly to the right. Good.

Sun reflection on water: when reflected ray points toward sun, bright highlight. This works.

Let me also add some larger rolling wave structure for "large rolling waves". I'll add a couple of sine waves on top of fbm for big rolling motion:

```
h += 0.4 * sin(p.x*0.1 + t*0.5) * cos(p.y*0.08 - t*0.3);
```

Actually fbm should be enough. Let me keep it.

Let me finalize and write out the file. I want to make the colors really pop and stormy.

Sky during stormy sunset: dark purple-grey clouds, orange/red horizon, dim zenith.

Let me tweak colors:
- horizon: warm orange (0.95, 0.45, 0.18)
- zenith: dark (0.04, 0.05, 0.12)
- clouds: dark grey with orange tinges near horizon

Water: dark teal with sun reflection.

Foam: bright cream/white.

Let me write the final shader with care:

Actually one issue: in skyColor I compute clouds using dir.xz/dir.y. When dir.y is near 0, this blows up. Need to handle. Let me add max(dir.y, 0.05) or similar.

Also, the cloudUV direction. Since dir is normalized, dir.xz/dir.y gives the projection. Use this carefully.

For the sun glow to extend nicely, increase the exponent widths.

Let me also make the ocean march more efficient. Step size: use (p.y - h) * 0.5 for safety, with min step.

Let me also tune foam. Foam on crests: where waveHeight is high. Slope-based foam for breaking waves.

Final shader:

```glsl
#version 300 es
precision highp float;
uniform vec2 uResolution;
uniform float uTime;
out vec4 fragColor;

float hash(vec2 p){
    p = fract(p*vec2(123.34, 456.21));
    p += dot(p, p+45.32);
    return fract(p.x*p.y);
}
float noise(vec2 p){
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f*f*(3.0-2.0*f);
    float a = hash(i), b = hash(i+vec2(1.0,0.0));
    float c = hash(i+vec2(0.0,1.0)), d = hash(i+vec2(1.0,1.0));
    return mix(mix(a,b,f.x), mix(c,d,f.x), f.y);
}
float fbm(vec2 p){
    float v=0.0, a=0.5;
    mat2 m = mat2(1.6, 1.2, -1.2, 1.6);
    for(int i=0;i<6;i++){ v += a*noise(p); p = m*p; a*=0.5; }
    return v;
}
float fbmCloud(vec2 p){
    float v=0.0, a=0.5;
    for(int i=0;i<5;i++){ v += a*noise(p); p = p*2.0; a*=0.5; }
    return v;
}

const float WAVE_AMP = 0.7;

float waveHeight(vec2 p, float t){
    float h = 0.0;
    h += 0.55 * fbm(p*0.12 + vec2(t*0.05, t*0.02));
    h += 0.28 * fbm(p*0.35 + vec2(-t*0.09, t*0.04));
    h += 0.14 * fbm(p*0.8 + vec2(t*0.14, -t*0.07));
    h += 0.07 * fbm(p*1.6 + vec2(t*0.2, t*0.1));
    return h * WAVE_AMP * 1.6 - 0.25;
}

vec3 getNormal(vec2 p, float t){
    float e = 0.08;
    float h0 = waveHeight(p, t);
    float hx = waveHeight(p+vec2(e,0.0), t);
    float hz = waveHeight(p+vec2(0.0,e), t);
    return normalize(vec3((h0-hx), e, (h0-hz)));
}

vec3 sunDir = normalize(vec3(0.35, 0.06, -1.0));
vec3 sunCol = vec3(1.6, 0.75, 0.32);

vec3 skyColor(vec3 dir, float t){
    float y = clamp(dir.y, -0.1, 1.0);
    vec3 horizon = vec3(0.95, 0.42, 0.18);
    vec3 mid = vec3(0.25, 0.12, 0.18);
    vec3 zenith = vec3(0.03, 0.04, 0.10);
    vec3 col = mix(horizon, mid, smoothstep(0.0, 0.25, y));
    col = mix(col, zenith, smoothstep(0.25, 0.7, y));
    
    // clouds
    if(dir.y > 0.02){
        float scale = 1.0/max(dir.y, 0.05);
        vec2 cuv = dir.xz * scale * 0.4 + vec2(t*0.015, t*0.005);
        float c = fbmCloud(cuv);
        c = smoothstep(0.45, 0.85, c);
        // dark stormy clouds, lit at bottom near sun
        float sunAlign = max(dot(dir, sunDir), 0.0);
        vec3 dark = vec3(0.08, 0.06, 0.09);
        vec3 lit = vec3(0.7, 0.35, 0.2);
        vec3 cloudCol = mix(dark, lit, pow(sunAlign, 2.0) * smoothstep(0.0, 0.3, y));
        col = mix(col, cloudCol, c * 0.85);
    }
    
    // sun
    float sd = max(dot(dir, sunDir), 0.0);
    col += sunCol * pow(sd, 300.0) * 2.0;
    col += sunCol * pow(sd, 30.0) * 0.5;
    col += sunCol * pow(sd, 6.0) * 0.15;
    
    return col;
}

void main(){
    vec2 uv = (gl_FragCoord.xy - 0.5*uResolution.xy) / uResolution.y;
    float t = uTime * 0.001;
    
    // camera bob
    vec3 camPos = vec3(
        sin(t*0.27)*0.6,
        1.7 + sin(t*0.5)*0.28 + sin(t*0.37+1.3)*0.18,
        sin(t*0.19)*0.6
    );
    
    vec3 forward = normalize(vec3(0.0, -0.08, -1.0));
    vec3 right = normalize(cross(vec3(0.0,1.0,0.0), forward));
    vec3 up = cross(forward, right);
    
    float roll = sin(t*0.45)*0.04 + sin(t*0.2)*0.02;
    float pitch = sin(t*0.33)*0.02;
    right = normalize(right*cos(roll) + up*sin(roll));
    up = cross(forward, right);
    forward = normalize(forward*cos(pitch) + up*sin(pitch));
    up = cross(forward, right);
    
    vec3 rayDir = normalize(forward + uv.x*right*1.3 + uv.y*up*1.0);
    
    vec3 col;
    
    if(rayDir.y >= 0.0){
        col = skyColor(rayDir, t);
    } else {
        float tt = 0.5;
        float hit = -1.0;
        for(int i=0;i<120;i++){
            vec3 p = camPos + rayDir * tt;
            float h = waveHeight(p.xz, t);
            if(p.y < h){ hit = tt; break; }
            tt += max(0.03, (p.y - h) * 0.4);
            if(tt > 100.0) break;
        }
        
        if(hit < 0.0){
            col = skyColor(rayDir, t);
        } else {
            vec3 p = camPos + rayDir * hit;
            vec3 n = getNormal(p.xz, t);
            vec3 viewDir = -rayDir;
            float fresnel = pow(1.0 - max(dot(n, viewDir), 0.0), 4.0);
            fresnel = clamp(fresnel*1.2, 0.0, 1.0);
            
            vec3 reflected = reflect(rayDir, n);
            vec3 skyRefl = skyColor(reflected, t);
            
            float spec = pow(max(dot(reflected, sunDir), 0.0), 100.0);
            float spec2 = pow(max(dot(reflected, sunDir), 0.0), 20.0);
            
            vec3 deepWater = vec3(0.02, 0.05, 0.09);
            vec3 shallowWater = vec3(0.08, 0.18, 0.22);
            float depthFactor = clamp((p.y + 0.5)*0.8, 0.0, 1.0);
            vec3 waterCol = mix(deepWater, shallowWater, depthFactor);
            
            col = mix(waterCol, skyRefl, fresnel);
            col += sunCol * spec * 3.0;
            col += sunCol * spec2 * 0.4;
            
            // foam
            float wh = waveHeight(p.xz, t);
            float foam = smoothstep(0.4, 0.7, wh + 0.3);
            float slope = 1.0 - n.y;
            foam = max(foam, smoothstep(0.2, 0.5, slope) * smoothstep(0.1, 0.4, wh+0.3));
            float foamNoise = noise(p.xz*4.0 + t*0.5) * noise(p.xz*9.0 - t*0.3);
            foam *= smoothstep(0.2, 0.6, foamNoise);
            foam = clamp(foam, 0.0, 1.0);
            col = mix(col, vec3(0.92, 0.94, 0.96), foam * 0.85);
            
            // fog near horizon
            float fog = 1.0 - exp(-hit * 0.025);
            vec3 horizonDir = normalize(vec3(rayDir.x, -0.001, rayDir.z));
            vec3 fogCol = skyColor(horizonDir, t);
            col = mix(col, fogCol, clamp(fog, 0.0, 1.0));
        }
    }
    
    // tone
    col = col / (col + vec3(1.0));
    col = pow(col, vec3(0.85));
    col *= 1.1;
    
    fragColor = vec4(col, 1.0);
}
```

I think this should work. Let me double-check the raymarch approach. When camera is at y=1.7 and waves can reach 0.7-0.8 amplitude, camera should stay above. Good.

One concern: when rayDir.y is very close to 0 (negative), the march will go very far before hitting. The fog will blend it. But the step size grows so should terminate. Good.

Issue: initial tt=0.5 — if camera bob puts camPos below a wave, we'd hit immediately. With camPos.y minimum ~1.7 - 0.46 = 1.24, still above max wave ~0.8. Safe.

Let me also handle the case where rayDir.y >= 0 but very close to 0 — actually that's fine, sky gradient handles it.

I think this is good. Let me write the full HTML file.

Wait, one thing about the waveHeight: I subtract 0.25 which lowers the mean water level. So waves range roughly from -0.25-0.7*1.6 ≈ -1.37 to -0.25+0.7*1.6 ≈ 0.87. Hmm that's a 2.2 unit amplitude, quite big. Camera at 1.7 minimum 1.24. Could still be above max ~0.87. OK.

Actually let me reduce WAVE_AMP slightly. With WAVE_AMP=0.7 and multiplier 1.6, the fbm sum (max ~1.04) gives 1.04*0.7*1.6 = 1.16. Minus 0.25 offset = 0.91 max. Camera min 1.24. Phew, just barely. Let me reduce WAVE_AMP to 0.5 to be safe, giving max ~0.83, and lower camera bob amplitude. Actually 1.24 vs 0.91 leaves 0.33 buffer. Fine.

Hmm actually fbm max isn't 1.0 since it's sum of 0.5+0.25+0.125+...=0.99. With rotation matrix it could be slightly different but ~1. So 0.7*1.6*1 = 1.12. Minus 0.25 = 0.87. OK.

Let me reduce to be safer: WAVE_AMP = 0.55, multiplier 1.4. Max ≈ 0.77. Better.

Let me also make the foam more visible. Foam threshold based on wh: when wh > some value. wh max ~0.77, so smoothstep(0.3, 0.6, wh) gives foam at crests. 

Actually let me reconsider foam. foam = smoothstep(0.4, 0.7, wh + 0.3). wh+0.3 max = 1.07. So smoothstep(0.4, 0.7, 1.07) = 1. OK. At mean water (wh = -0.25), wh+0.3 = 0.05, smoothstep(0.4, 0.7, 0.05) = 0. Good. So foam only on crests. Good.

Alright, I think the shader is solid. Let me write the HTML.

For the JS, I'll set body margin 0, canvas display block, overflow hidden, background black.

Let me finalize.