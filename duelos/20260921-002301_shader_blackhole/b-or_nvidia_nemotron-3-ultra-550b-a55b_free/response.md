```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Black Hole - Gravitational Lensing</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { overflow: hidden; background: #000; }
canvas { display: block; width: 100vw; height: 100vh; }
</style>
</head>
<body>
<canvas id="glcanvas"></canvas>
<script>
const canvas = document.getElementById('glcanvas');
const gl = canvas.getContext('webgl2', { antialias: false, alpha: false, preserveDrawingBuffer: false });

const vsSource = `#version 300 es
precision highp float;
in vec2 a_pos;
out vec2 v_uv;
void main() {
    v_uv = a_pos * 0.5 + 0.5;
    gl_Position = vec4(a_pos, 0.0, 1.0);
}`;

const fsSource = `#version 300 es
precision highp float;
in vec2 v_uv;
out vec4 fragColor;

uniform float u_time;
uniform vec2 u_resolution;
uniform float u_pixelRatio;

#define PI 3.14159265359
#define TAU 6.28318530718
#define RS 1.0           // Schwarzschild radius = 2M (we use units where Rs=1)
#define PHOTON_SPHERE 1.5 // 3M/2M = 1.5 Rs
#define ISCO 3.0         // Innermost stable circular orbit = 3 Rs

// Schwarzschild metric constants
#define G 1.0
#define C 1.0

// Hash for stars
uint hash_uint(uint x) {
    x ^= x >> 16;
    x *= 0x7feb352d;
    x ^= x >> 15;
    x *= 0x846ca68b;
    x ^= x >> 16;
    return x;
}

float hash_float(vec2 p) {
    uint h = hash_uint(uint(p.x * 1000.0) ^ (uint(p.y * 1000.0) << 16));
    return float(h) / 4294967295.0;
}

float hash_float3(vec3 p) {
    uint h = hash_uint(uint(p.x * 1000.0) ^ (uint(p.y * 1000.0) << 16) ^ (uint(p.z * 1000.0) << 8));
    return float(h) / 4294967295.0;
}

// Starfield
vec3 starfield(vec3 dir) {
    vec3 col = vec3(0.0);
    // Multiple layers of stars at different distances
    for (int layer = 0; layer < 3; layer++) {
        float scale = 50.0 + float(layer) * 200.0;
        vec3 p = dir * scale;
        vec3 cell = floor(p);
        vec3 fp = fract(p) - 0.5;
        
        for (int x = -1; x <= 1; x++) {
            for (int y = -1; y <= 1; y++) {
                for (int z = -1; z <= 1; z++) {
                    vec3 neighbor = cell + vec3(float(x), float(y), float(z));
                    float h = hash_float3(neighbor);
                    if (h < 0.0008) { // star density
                        vec3 starPos = neighbor + vec3(hash_float3(neighbor + 1.0), 
                                                        hash_float3(neighbor + 2.0), 
                                                        hash_float3(neighbor + 3.0)) - 0.5;
                        vec3 toStar = normalize(starPos - fp);
                        float dist = length(starPos - fp);
                        float brightness = hash_float3(neighbor + 4.0) * 0.5 + 0.5;
                        float size = hash_float3(neighbor + 5.0) * 0.003 + 0.001;
                        float ang = dot(dir, toStar);
                        if (ang > 1.0 - size / dist) {
                            float intensity = brightness * (1.0 / (dist * dist)) * smoothstep(1.0, 1.0 - size/dist, ang);
                            vec3 starColor = mix(vec3(1.0, 0.9, 0.7), vec3(0.7, 0.8, 1.0), hash_float3(neighbor + 6.0));
                            col += starColor * intensity * (0.5 + 0.5 * float(layer));
                        }
                    }
                }
            }
        }
    }
    return col;
}

// Blackbody approximation for accretion disk temperature
vec3 blackbody(float T) {
    // T in units where T=1 at ISCO, roughly 10^7 K
    // Simplified: map temperature to color
    // Cool red (1000K) -> Orange -> Yellow -> White -> Blue-white
    vec3 c;
    if (T < 0.3) {
        c = mix(vec3(1.0, 0.1, 0.0), vec3(1.0, 0.4, 0.0), T / 0.3);
    } else if (T < 0.6) {
        c = mix(vec3(1.0, 0.4, 0.0), vec3(1.0, 0.8, 0.2), (T - 0.3) / 0.3);
    } else if (T < 0.85) {
        c = mix(vec3(1.0, 0.8, 0.2), vec3(1.0, 1.0, 0.6), (T - 0.6) / 0.25);
    } else {
        c = mix(vec3(1.0, 1.0, 0.6), vec3(0.9, 0.95, 1.0), (T - 0.85) / 0.15);
    }
    return c * pow(T, 4.0); // Stefan-Boltzmann-ish brightness
}

// Accretion disk emission
vec3 disk_emission(float r, float phi, float time) {
    // Temperature profile: T ~ r^(-3/4) for Novikov-Thorne disk
    // Inner edge at ISCO (3 Rs), outer at ~20 Rs
    if (r < ISCO || r > 20.0) return vec3(0.0);
    
    float T = pow(ISCO / r, 0.75); // Normalized temperature
    
    // Turbulence and structure
    float spiral = sin(8.0 * phi - 20.0 * log(r) + time * 0.3);
    float turbulence = 0.0;
    for (int i = 0; i < 4; i++) {
        float f = pow(2.0, float(i));
        turbulence += sin(r * f * 0.5 + phi * f * 2.0 + time * 0.2 * f) / f;
    }
    turbulence *= 0.15;
    
    float density = 1.0 + 0.4 * spiral + 0.3 * turbulence;
    density *= smoothstep(ISCO, ISCO + 0.3, r) * smoothstep(20.0, 18.0, r);
    
    // Doppler boosting from rotation (Keplerian velocity ~ r^(-1/2))
    // Viewing angle dependent - simplified
    float v_phi = 1.0 / sqrt(r); // orbital velocity
    float doppler = 1.0 + 0.3 * v_phi; // approximate
    
    vec3 color = blackbody(T) * density * doppler;
    return color;
}

// Photon ring emission
float photon_ring(float r, float impact_param) {
    // Peak at photon sphere r=1.5
    float dr = abs(r - PHOTON_SPHERE);
    float width = 0.02;
    float ring = exp(-dr * dr / (2.0 * width * width));
    
    // Also depends on impact parameter proximity to critical
    float b_crit = 3.0 * sqrt(3.0) / 2.0; // ~2.598 in Rs units
    float db = abs(impact_param - b_crit);
    ring *= exp(-db * db / 0.01);
    
    return ring;
}

// Geodesic integration for light ray in Schwarzschild metric
// Returns: hit type (0=miss/escape, 1=horizon, 2=disk, 3=photon ring), final position info
struct RayResult {
    int hitType;
    float r;
    float theta;
    float phi;
    float impactParam;
    float redshift;
};

RayResult trace_ray(vec3 rayDir, vec3 camPos, float time) {
    // Camera position in spherical coords
    float camR = length(camPos);
    float camTheta = acos(clamp(camPos.y / camR, -1.0, 1.0));
    float camPhi = atan(camPos.z, camPos.x);
    
    // Initial conditions for geodesic
    // Using conserved quantities: E (energy), L (angular momentum)
    // For photon: ds^2 = 0
    // Impact parameter b = L/E
    
    // Initial 4-momentum in local orthonormal frame at camera
    // Transform rayDir to spherical basis
    vec3 e_r = normalize(camPos);
    vec3 e_theta = normalize(vec3(camPos.x * camPos.y, camPos.y * camPos.y - camR * camR, camPos.z * camPos.y));
    vec3 e_phi = normalize(cross(e_r, e_theta));
    
    float pr = dot(rayDir, e_r);
    float ptheta = dot(rayDir, e_theta) * camR;
    float pphi = dot(rayDir, e_phi) * camR * sin(camTheta);
    
    // Impact parameter
    float b = sqrt(ptheta * ptheta + pphi * pphi) / abs(pr + 1e-6);
    if (abs(pr) < 1e-6) b = 100.0;
    
    // Energy (can set E=1 for affine parameter)
    float E = 1.0;
    float L = b;
    
    // Initialize integration
    float r = camR;
    float theta = camTheta;
    float phi = camPhi;
    
    // Initial derivatives (dr/dlambda, dtheta/dlambda, dphi/dlambda)
    // Using Hamiltonian formulation
    float dr_dl = pr;
    float dtheta_dl = ptheta / (r * r);
    float dphi_dl = pphi / (r * r * sin(theta) * sin(theta));
    
    // Adaptive step size
    float lambda = 0.0;
    float maxLambda = 200.0;
    
    int hitType = 0;
    float finalRedshift = 1.0;
    
    for (int i = 0; i < 2000; i++) {
        if (lambda > maxLambda) break;
        
        float rs_over_r = RS / r;
        float one_minus_rs_r = 1.0 - rs_over_r;
        
        // Check for horizon crossing
        if (r <= RS * 1.001) {
            hitType = 1; // Event horizon
            finalRedshift = 0.0;
            break;
        }
        
        // Check for disk intersection (equatorial plane theta = PI/2)
        // Disk exists between ISCO and 20 Rs
        float prevTheta = theta;
        float dtheta_sign = dtheta_dl;
        
        // Step size adaptive based on curvature
        float step = 0.02 * min(r, 10.0) * sqrt(one_minus_rs_r + 0.01);
        step = max(step, 0.001);
        
        // Leapfrog / Verlet integration for geodesics
        // dr/dlambda = +/- sqrt(E^2 - (1-rs/r)(L^2/r^2))
        float V_eff = one_minus_rs_r * L * L / (r * r);
        float dr2 = E * E - V_eff;
        
        if (dr2 < 0.0) {
            // Turning point - ray goes back out
            dr_dl = -dr_dl;
            dr2 = 0.0;
        }
        dr_dl = (dr_dl > 0.0 ? 1.0 : -1.0) * sqrt(max(dr2, 0.0));
        
        // Update position
        r += dr_dl * step;
        theta += dtheta_dl * step;
        phi += dphi_dl * step;
        lambda += step;
        
        // Normalize theta
        if (theta < 0.0) { theta = -theta; phi += PI; dtheta_dl = -dtheta_dl; }
        if (theta > PI) { theta = 2.0 * PI - theta; phi += PI; dtheta_dl = -dtheta_dl; }
        phi = mod(phi, TAU);
        
        // Recompute derivatives at new position
        rs_over_r = RS / r;
        one_minus_rs_r = 1.0 - rs_over_r;
        
        // Angular momentum conservation gives dphi/dlambda
        dphi_dl = L / (r * r * sin(theta) * sin(theta) + 1e-6);
        
        // Theta equation: d^2theta/dlambda^2 = sin(theta)cos(theta) (dphi/dlambda)^2
        // Simplified: assume near equatorial or use conserved Carter constant
        // For simplicity, use Carter constant Q = p_theta^2 + cos^2(theta) * (L^2/sin^2(theta) - a^2 E^2)
        // For Schwarzschild a=0: Q = p_theta^2 + L^2 / tan^2(theta)
        // At camera: Q = ptheta^2 + L^2 / tan^2(camTheta)
        // But we'll use simpler approach: integrate theta directly
        
        // Disk crossing check (crossing equatorial plane going downward)
        if (prevTheta < PI/2.0 && theta >= PI/2.0 && r > ISCO && r < 20.0) {
            hitType = 2; // Hit disk
            break;
        }
        if (prevTheta > PI/2.0 && theta <= PI/2.0 && r > ISCO && r < 20.0) {
            hitType = 2; // Hit disk from below
            break;
        }
        
        // Photon ring proximity
        if (r < PHOTON_SPHERE + 0.1 && r > PHOTON_SPHERE - 0.1 && abs(dr_dl) < 0.1) {
            // Orbiting near photon sphere
            hitType = 3;
            // Don't break immediately, let it accumulate
        }
        
        // Escape to infinity
        if (r > 100.0) {
            hitType = 0;
            break;
        }
    }
    
    RayResult result;
    result.hitType = hitType;
    result.r = r;
    result.theta = theta;
    result.phi = phi;
    result.impactParam = b;
    result.redshift = finalRedshift;
    return result;
}

// Simpler but more robust: analytic light bending + ray marching
// Use the fact that for Schwarzschild, we can compute deflection angle analytically
// But for full image including disk behind BH, need numerical integration

// Let's use a more practical approach: backward ray tracing with effective potential
vec3 render_pixel(vec2 uv, float time) {
    // Camera setup
    float aspect = u_resolution.x / u_resolution.y;
    float fov = 0.8; // ~45 degrees
    
    // Camera orbit
    float orbitRadius = 12.0;
    float orbitSpeed = 0.15;
    float orbitAngle = time * orbitSpeed;
    float tilt = 0.3 * sin(time * 0.07) + 0.4; // Tilt oscillation
    
    vec3 camPos = vec3(
        orbitRadius * cos(orbitAngle) * cos(tilt),
        orbitRadius * sin(tilt),
        orbitRadius * sin(orbitAngle) * cos(tilt)
    );
    
    // Camera basis
    vec3 forward = normalize(-camPos);
    vec3 up = vec3(0.0, 1.0, 0.0);
    vec3 right = normalize(cross(forward, up));
    up = normalize(cross(right, forward));
    
    // Ray direction
    vec3 rayDir = normalize(forward + right * (uv.x - 0.5) * 2.0 * fov * aspect + up * (uv.y - 0.5) * 2.0 * fov);
    
    // Use numerical geodesic integration (simpler Hamiltonian approach)
    // Constants of motion
    vec3 e_r = normalize(camPos);
    vec3 e_theta = normalize(vec3(camPos.x * camPos.y, camPos.y * camPos.y - length(camPos) * length(camPos), camPos.z * camPos.y));
    vec3 e_phi = normalize(cross(e_r, e_theta));
    
    float pr = dot(rayDir, e_r);
    float ptheta = dot(rayDir, e_theta) * length(camPos);
    float pphi = dot(rayDir, e_phi) * length(camPos) * sin(acos(clamp(camPos.y / length(camPos), -1.0, 1.0)));
    
    float E = 1.0;
    float Lz = pphi;
    float Q = ptheta * ptheta + Lz * Lz / (tan(acos(clamp(camPos.y / length(camPos), -1.0, 1.0))) * tan(acos(clamp(camPos.y / length(camPos), -1.0, 1.0))) + 1e-6);
    
    // Impact parameter
    float b = sqrt(Lz * Lz + Q) / E;
    
    // Integration
    float r = length(camPos);
    float theta = acos(clamp(camPos.y / r, -1.0, 1.0));
    float phi = atan(camPos.z, camPos.x);
    
    float dr_dl = pr;
    float dtheta_dl = ptheta / (r * r);
    float dphi_dl = pphi / (r * r * sin(theta) * sin(theta) + 1e-6);
    
    vec3 accretionColor = vec3(0.0);
    float photonRingAccum = 0.0;
    bool hitHorizon = false;
    bool hitDisk = false;
    float diskR = 0.0, diskPhi = 0.0;
    
    // Adaptive integration
    for (int i = 0; i < 1500; i++) {
        float rs_r = RS / r;
        float f = 1.0 - rs_r;
        
        if (r <= RS * 1.001) {
            hitHorizon = true;
            break;
        }
        
        if (r > 150.0) break;
        
        // Check disk crossing (theta = PI/2)
        float prevTheta = theta;
        
        // Step size
        float step = 0.015 * min(r, 8.0) * sqrt(f + 0.01);
        step = clamp(step, 0.0005, 0.1);
        
        // Effective potential for radial motion
        float V_r = f * (Lz * Lz + Q) / (r * r);
        float dr2 = E * E - V_r;
        
        if (dr2 < 0.0) {
            dr_dl = -dr_dl;
            dr2 = 0.0;
        }
        dr_dl = (dr_dl >= 0.0 ? 1.0 : -1.0) * sqrt(dr2);
        
        // Update
        r += dr_dl * step;
        theta += dtheta_dl * step;
        phi += dphi_dl * step;
        
        // Theta equation from Carter constant
        // (dtheta/dlambda)^2 = Q - cos^2(theta) * (Lz^2/sin^2(theta))
        float cot2 = cos(theta) * cos(theta) / (sin(theta) * sin(theta) + 1e-6);
        float dtheta2 = Q - Lz * Lz * cot2;
        if (dtheta2 < 0.0) {
            dtheta_dl = -dtheta_dl;
            dtheta2 = 0.0;
        }
        dtheta_dl = (dtheta_dl >= 0.0 ? 1.0 : -1.0) * sqrt(dtheta2);
        
        // Phi equation
        dphi_dl = Lz / (r * r * sin(theta) * sin(theta) + 1e-6);
        
        // Normalize
        if (theta < 0.0) { theta = -theta; phi += PI; dtheta_dl = -dtheta_dl; }
        if (theta > PI) { theta = 2.0 * PI - theta; phi += PI; dtheta_dl = -dtheta_dl; }
        phi = mod(phi, TAU);
        
        // Disk hit (crossing equatorial plane)
        if (!hitDisk && ((prevTheta < PI/2.0 && theta >= PI/2.0) || (prevTheta > PI/2.0 && theta <= PI/2.0))) {
            if (r > ISCO && r < 20.0) {
                hitDisk = true;
                diskR = r;
                diskPhi = phi;
            }
        }
        
        // Photon ring accumulation (near r=1.5, near turning points)
        if (r < PHOTON_SPHERE + 0.08 && r > PHOTON_SPHERE - 0.08 && abs(dr_dl) < 0.05) {
            float weight = exp(-abs(r - PHOTON_SPHERE) * 50.0) * step * 0.5;
            photonRingAccum += weight;
        }
    }
    
    vec3 color = vec3(0.0);
    
    // Starfield background (lensed)
    if (!hitHorizon) {
        // Compute final direction at infinity for starfield lookup
        // For rays that escape, trace backward to get apparent direction
        // Simplified: use impact parameter to deflect starfield
        vec3 starDir = rayDir;
        if (b < 5.0) {
            // Gravitational lensing deflection angle ~ 2Rs/b for large b
            // More accurate: alpha = 2 * arcsin(Rs/b) for photon sphere grazing
            float deflection = 2.0 * asin(clamp(RS / b, 0.0, 1.0));
            // Apply deflection toward black hole center
            vec3 toBH = normalize(-camPos);
            float bend = deflection * 0.5; // approximate
            starDir = normalize(mix(rayDir, toBH, bend));
        }
        color += starfield(starDir) * 0.8;
    }
    
    // Accretion disk
    if (hitDisk) {
        // Disk rotation
        float diskTime = time * 0.5;
        float rotAngle = diskTime / sqrt(diskR * diskR * diskR); // Keplerian
        float emissivePhi = diskPhi + rotAngle;
        
        vec3 diskCol = disk_emission(diskR, emissivePhi, time);
        
        // Gravitational redshift
        float z = 1.0 / sqrt(1.0 - RS / diskR) - 1.0;
        float redshiftFactor = 1.0 / (1.0 + z);
        
        // Doppler shift from orbital motion
        float v_orb = 1.0 / sqrt(diskR); // in units of c
        // Viewing angle
        vec3 diskNormal = vec3(0.0, 1.0, 0.0);
        vec3 obsDir = normalize(camPos - vec3(diskR * cos(diskPhi), 0.0, diskR * sin(diskPhi)));
        float cosInclination = dot(diskNormal, obsDir);
        float doppler = 1.0 / (1.0 - v_orb * sin(acos(cosInclination)) * cos(emissivePhi - atan(camPos.z, camPos.x)));
        
        diskCol *= redshiftFactor * redshiftFactor * redshiftFactor * doppler * doppler * doppler; // flux ~ nu^3
        
        // Lensing magnification near black hole
        float mag = 1.0 + 0.5 * exp(-(diskR - 4.0) * 0.5);
        diskCol *= mag;
        
        color += diskCol;
    }
    
    // Photon ring (bright ring at 1.5 Rs)
    if (photonRingAccum > 0.001) {
        vec3 ringColor = vec3(1.0, 0.95, 0.8) * photonRingAccum * 15.0;
        // Add some structure
        ringColor *= 1.0 + 0.3 * sin(phi * 20.0 + time * 2.0);
        color += ringColor;
    }
    
    // Event horizon - pitch black
    if (hitHorizon) {
        color = vec3(0.0);
    }
    
    // Subtle glow around horizon (numerical artifact cleanup)
    float horizonDist = length(camPos) - RS;
    if (hitHorizon && horizonDist < 0.5) {
        color = vec3(0.0);
    }
    
    // Tone mapping (ACES filmic)
    color = color / (color + vec3(0.15, 0.15, 0.15)) * 1.05;
    color = pow(color, vec3(1.0 / 2.2));
    
    return color;
}

void main() {
    vec2 uv = v_uv;
    // Fix aspect ratio
    vec2 centered = (gl_FragCoord.xy - 0.5 * u_resolution) / min(u_resolution.x, u_resolution.y);
    
    vec3 col = render_pixel(centered, u_time);
    
    // Vignette
    float vig = 1.0 - 0.15 * length(centered * vec2(1.0, u_resolution.y / u_resolution.x));
    col *= vig;
    
    fragColor = vec4(col, 1.0);
}`;

function createShader(gl, type, source) {
    const shader = gl.createShader(type);
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
        console.error('Shader compile error:', gl.getShaderInfoLog(shader));
        gl.deleteShader(shader);
        return null;
    }
    return shader;
}

function createProgram(gl, vs, fs) {
    const program = gl.createProgram();
    gl.attachShader(program, vs);
    gl.attachShader(program, fs);
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
        console.error('Program link error:', gl.getProgramInfoLog(program));
        return null;
    }
    return program;
}

const vs = createShader(gl, gl.VERTEX_SHADER, vsSource);
const fs = createShader(gl, gl.FRAGMENT_SHADER, fsSource);
const program = createProgram(gl, vs, fs);

const posBuffer = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, posBuffer);
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([
    -1, -1,  1, -1,  -1, 1,
    -1,  1,  1, -1,   1, 1
]), gl.STATIC_DRAW);

const posLoc = gl.getAttribLocation(program, 'a_pos');
const timeLoc = gl.getUniformLocation(program, 'u_time');
const resLoc = gl.getUniformLocation(program, 'u_resolution');
const prLoc = gl.getUniformLocation(program, 'u_pixelRatio');

function resize() {
    const dpr = Math.min(window.devicePixelRatio, 2);
    canvas.width = window.innerWidth * dpr;
    canvas.height = window.innerHeight * dpr;
    canvas.style.width = window.innerWidth + 'px';
    canvas.style.height = window.innerHeight + 'px';
    gl.viewport(0, 0, canvas.width, canvas.height);
}

let startTime = performance.now();
function render(now) {
    const time = (now - startTime) * 0.001;
    
    gl.useProgram(program);
    gl.bindBuffer(gl.ARRAY_BUFFER, posBuffer);
    gl.enableVertexAttribArray(posLoc);
    gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);
    
    gl.uniform1f(timeLoc, time);
    gl.uniform2f(resLoc, canvas.width, canvas.height);
    gl.uniform1f(prLoc, window.devicePixelRatio);
    
    gl.drawArrays(gl.TRIANGLES, 0, 6);
    
    requestAnimationFrame(render);
}

window.addEventListener('resize', resize);
resize();
requestAnimationFrame(render);
</script>
</body>
</html>
```