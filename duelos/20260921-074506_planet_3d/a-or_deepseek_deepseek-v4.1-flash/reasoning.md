You need to produce a single self-contained HTML file using three.js r186 via import map (which is provided by the environment, so don't add your own). Let's write it.

Key elements:
- Planet with custom shader: 3D noise for terrain colors (oceans, continents, ice caps). Use GLSL simplex noise or value noise. I'll write a classic 3D simplex noise (Ashima) in the shader, or use fbm of a hash-based value noise. Simplex noise is long but fine.
- Cloud layer: slightly larger sphere, rotating slowly, transparent with noise-based alpha.
- Atmospheric rim: fresnel glow, additive blending, backside rendering maybe two layers.
- Ring system: RingGeometry with custom shader/transparency, tilted.
- Moon: small sphere orbiting, casting shadow? Shadow from moon onto planet via shadow map is tricky with custom shader — I'd need to include shadow in the planet shader. Simpler: make the moon "casts light and shadow interest" — maybe the moon is lit by sun with a directional light, and we can add a shadow map. Actually to keep it simpler and robust: use a directional light for the sun, and give the planet shader manual lighting. Moon can cast shadow onto the planet if we use THREE's shadow mapping — but custom ShaderMaterial doesn't receive shadows unless we add shadowmap code.

Alternative: implement a fake shadow in the planet shader: compute the moon's position in planet-local space and darken points near the moon's shadow ray. That's easy: pass moon position (in planet local space) and sun direction; compute the vector from the fragment to the moon projected along sun direction; if the perpendicular distance < moon radius and it's on the right side, darken. That gives an eclipse shadow. Nice "shadow interest".

Let's do that.

Also moon casting light: add a small point light? Not needed since shaders are custom. But "casts light and shadow interest" — I'll give the moon a slight emissive glow and it occludes the sun to produce eclipse shadow on planet. Also moon phases.

Camera slowly drifts around the planet — use OrbitControls? No interaction needed but auto rotate. Simpler: manually move camera on a slow path using time.

Use requestAnimationFrame timestamp for animation.

Scene setup:
- Renderer with antialias, setPixelRatio.
- Camera PerspectiveCamera, positioned at ~ (0, 2, 6) looking at origin.
- Planet radius 1.
- Sun: DirectionalLight not needed; we compute lighting in shader with sunDirection. Add a sprite/mesh for the sun with lens flare glow: a big plane with radial gradient shader (additive), plus a few smaller flare sprites along the vector from sun screen position through center? True lens flare requires screen-space. I can approximate: compute sun screen position and place a few additive quads in an orthographic overlay scene... That's complex. Simpler: a large additive billboard glow at the sun's 3D position plus a couple of smaller billboard glows at positions along the line between sun and planet center — visually like flare. Hmm, but requirement says "lens-flare-like glow". A billboard with radial falloff + streaks is acceptable. I'll make a shader plane facing camera with a radial glow + horizontal streak (anamorphic flare look). Good.

Actually a nicer trick: put the sun far away in a direction; render a big additive quad that always faces camera with radial glow. Plus ghost flares: place small quads at positions computed in world space along the line from camera-through-sun... Let's do a simple screen-space overlay: create a second scene with an OrthographicCamera and render after the main scene with autoClear false. Compute sun screen position by projecting world sun position... but sun is placed far away; I'll place a "sunLight" direction and put the sun billboard at direction * 60 world units. Then project to NDC, place ghost quads in overlay scene at NDC positions scaled, with size varying. That gives real lens flare ghosts. That's doable and cool.

Let me do the overlay approach: 
- overlayScene with ortho camera (-1..1 in x, -1..1 in y scaled by aspect... actually use ortho(-1,1,-1,1) with aspect handled by positioning; simpler: ortho with left=-aspect, right=aspect, top=1, bottom=-1, then NDC x*aspect).

Ghosts: quads with additive material, radial gradient texture via shader. Positions: for i in 0..5, ghostPos = -sunNDC * factor_i. Size varies. Color tint varies (warm/cool).

Also need sun visibility check (behind? no, sun is far, always in front). If sun NDC outside view, still fine (clipped).

OK.

- Starfield: BufferGeometry with ~8000 points on a large sphere, PointsMaterial with size attenuation false, small size, slight color variation via vertex colors. Dense.

Planet shader:
Vertex: pass vPos (position, object space), vNormal, vWorldPos? We compute lighting in object space using sun direction transformed to object space, since planet doesn't rotate (or rotates slowly). Actually let's keep the planet mesh not rotating (or rotate very slowly) so cloud rotation is visible relative to it. Let's have planet rotate slowly too (like real). For noise we use object-space position / normalized direction. If planet rotates, uSunDirection in object space changes — just pass sunDirectionObject uniform updated each frame from world sun dir.

Simplify: keep planet rotation fixed (tilt only), clouds rotate. That's fine and looks fine. Actually a slowly rotating planet is nicer. Let's rotate planet slowly around Y (0.02 rad/s) and compute sun direction in object space each frame: sunDirObj = mesh.worldToLocal-ish; easier: since only rotation about Y, just rotate the sun direction vector by inverse of planet's quaternion. Use `sunDirWorld.clone().applyQuaternion(planet.quaternion.clone().invert())`. Fine.

But moon shadow needs moon position in planet object space too. Do the same transform. Fine — do those math each frame in JS.

Noise: implement 3D simplex noise in GLSL (Ashima's snoise). Then fbm with 4-5 octaves.

Terrain: 
- h = fbm(p * 1.8)
- continents: land if h > 0.0 (some threshold).
- Add detail fbm for color variation.
- Ice caps: based on |latitude| = |normalized position y| combined with noise; ice when abs(y) > 0.72 - noise variation, plus maybe on land when high.
- Colors: deep ocean (dark blue), shallow ocean (teal), beach (tan), grass/forest greens, mountains brown/white, ice white.

Lighting: lambert + specular on ocean + rim.

Let's write shader:

```glsl
uniform vec3 uSunDirection; // object space, normalized
uniform float uTime;
uniform vec3 uMoonPosObj;
uniform float uMoonRadius;
varying vec3 vObjPos;
varying vec3 vNormal;
```

fragment:
```
vec3 p = normalize(vObjPos);
float n = fbm(p*2.0);
float detail = fbm(p*8.0);
float h = n;
float lat = abs(p.y);
float iceEdge = 0.68 + 0.12*fbm(p*3.0+vec3(11.0));
float ice = smoothstep(iceEdge, iceEdge+0.12, lat);
// ocean
float land = smoothstep(0.02, 0.06, h);
```
Hmm need to tune. Let's write fbm returning ~[-1,1] or [0,1]? Simplex snoise returns approx [-1,1]. fbm sum of octaves with amplitude halving → roughly [-1,1]. Normalize.

Let's define:
```
float fbm(vec3 p){ float a=0.5, s=0.0; for(int i=0;i<5;i++){ s += a*snoise(p); p*=2.03; a*=0.5;} return s; } // ~[-1,1]
```
Then h = fbm(p*1.6) + 0.3*fbm(p*4.0) → range maybe [-1.3,1.3]. Then:
```
float continent = h;
float landMask = smoothstep(0.0, 0.06, continent);
```

Ocean color: mix(deep, shallow, smoothstep(-0.15, 0.0, continent)).

Add land color based on continent value and detail:
```
vec3 landCol = mix(vec3(0.18,0.35,0.13), vec3(0.45,0.38,0.22), smoothstep(0.05,0.25,continent+detail*0.1));
// mountains
landCol = mix(landCol, vec3(0.5,0.42,0.35), smoothstep(0.3,0.45,continent));
```
Ice: mix everything to white where ice high; also ice over ocean.

Specular: ocean specular using reflected view dir.

Atmosphere rim on planet: add fresnel-ish blue glow at limb added to color.

Now the atmosphere sphere: radius 1.06, backside, additive, with fresnel based on view direction: intensity = pow(1.0 - dot(normal, viewDir), 3.0) plus sun-side modulation (scatter forward). Use `FrontSide`? For a glow around the planet, use backside rendering of a slightly larger sphere with additive blending and depthWrite false. Common approach: material with `side: THREE.BackSide`, alpha = pow(0.7 - dot(vNormal, viewDir), 4). Let's use the standard glow shader.

Actually with BackSide, normals point outward but we render inner faces. Compute fresnel with view direction: in vertex shader, vNormal = normalize(normalMatrix * normal); vViewDir = normalize(-mvPosition.xyz). intensity = pow(1.0 - abs(dot(vNormal, vViewDir)), power). Hmm for backside sphere around planet, the rim appears where the sphere's surface is tangent to view → dot ~ 0 → intensity high. Good. And the center is behind the planet → occluded by depth test if we keep depthTest true and planet drawn first. Yes: render planet first, then atmosphere with depthWrite false, depthTest true, blending additive. The center back faces are behind the planet → depth test fails → hidden. Rim shows around. 

Add sun modulation: multiply by (0.4 + 0.6*max(dot(vWorldNormal, sunDir),0)) something for a nice day-side glow.

Clouds: sphere radius 1.02, ShaderMaterial with noise-based alpha, lit by sun (lambert), transparent, depthWrite false. Rotate slowly.

Rings: RingGeometry(1.5, 2.6, 128) rotated -PI/2 on x then tilted. Custom shader: use uv? RingGeometry uv is mapped in a weird way; better to compute radial distance from center in object space. Use varying vPos local. Compute r = length(position.xy) before rotation (ring is in XY plane in geometry space). alpha = bands via noise(r) with gaps, plus fade at inner/outer edges. Lighting: rings should be lit by sun; also cast shadow on planet? Skip. But add planet shadow on rings? Skip; keep simple but add slight darkening on the side away from sun.

Ring must be double-sided, transparent, depthWrite false.

Moon: sphere radius 0.18 with a noise-shaded gray surface, lit by sun. Orbit radius ~2.2, inclined orbit. It should orbit within the 30s window nicely — period ~ 20 s means full orbit; let's use period 24s. Also moon casts shadow on the planet: eclipse shadow in planet shader.

Moon also "casts light" — maybe add a subtle moonlight fill on the planet's night side? Could add a small glow around moon. I'll add a small additive glow sprite around the moon and give the planet a faint moonlit terminator? Keep simple: add moon glow.

Also the moon's shadow: compute in planet object space.

In planet fragment shader:
```
vec3 toMoon = vObjPosObj - uMoonPosObj; // wait, positions are object space of planet with radius 1
// sun dir in object space uSunDirObj points from planet toward sun.
float t = dot(uMoonPosObj - vObjPos, uSunDirObj); // distance along sun dir to moon plane
```
If t>0, the moon is in the direction of the sun. Perp distance: `vec3 d = (uMoonPosObj - vObjPos) - t*uSunDirObj; float dist = length(d);` shadow = smoothstep(uMoonRadius, uMoonRadius*0.5, dist)? Then also multiply by t>0 factor. Also the shadow should only be soft penumbra.

Then multiply the lit color by (1 - 0.85*shadow).

Note: vObjPos is in planet object space, but we normalized for noise... careful to keep both. Use vObjPos raw (radius 1 planet, so raw = direction). Fine, keep `vObjPos` and use `p = normalize(vObjPos)`.

But wait: the moon position in planet object space must be transformed the same way. Since both planet and moon are in world space, moonPosObj = planet.worldToLocal(moonWorldPos). Since planet only rotates (and maybe has tilt applied at scene level), worldToLocal handles it. Actually if I apply tilt by rotating the planet mesh, then the "latitude" in object space differs from world Y. Better: create a group `planetGroup` with tilt rotation, and put planet, clouds, rings inside, and rotate the planet mesh itself around its local Y for spin. Then planet object space has Y = polar axis. Good. Moon orbits in world space around origin.

Hmm but then rings and clouds are in the group and get tilted. Clouds spin around local Y. Rings static in group (tilted).

planetMesh.rotation.y += spin. worldToLocal on planetMesh accounts for both group tilt and spin. Good.

Then sun direction in planet object space: `sunDirObj = sunDirWorld.clone().applyQuaternion(planetMesh.getWorldQuaternion(q).invert())`. Compute each frame.

Moon object space position: planetMesh.worldToLocal(moonMesh.position.clone()) — need moonMesh.updateMatrixWorld first; worldToLocal uses matrixWorld inverse. Fine.

Note worldToLocal on planet mesh: matrixWorld includes scale 1. Good.

Camera drift: slowly orbit around, e.g. camera position via spherical with slowly varying radius and polar angle:
```
const t = time;
const r = 4.6 + 0.6*Math.sin(t*0.07);
const theta = t*0.06;
const phi = 1.15 + 0.25*Math.sin(t*0.045);
camera.position.set(r*Math.sin(phi)*Math.sin(theta), r*Math.cos(phi), r*Math.sin(phi)*Math.cos(theta));
camera.lookAt(0,0,0);
```
With phi ~ 1.15 rad from Y-axis: y = r*cos(1.15)=~0.4r. Hmm, that's above the ring plane. Ring plane tilt: group rotation maybe x = -0.35 rad. Fine.

Should the camera see the rings nicely? Rings extend to 2.6. Camera at ~4.6 distance. Fine.

Sun direction: fixed, e.g. normalize(1, 0.35, -0.5)? Let's put sun at direction (0.6, 0.35, 0.7) normalized, and put the sun billboard at that direction * 60. But then it may be behind the camera depending on the camera drift. To ensure the sun is visible in the frame during the recording, we want it roughly in the direction the camera looks at. Since camera looks at origin, the sun at direction d from origin appears in view if the angle between camera direction and d is less than FOV... Camera looks from position to origin, i.e., view direction = -normalize(camPos). The sun at +d*60 is in view if angle between -camDir... hmm.

Alternative: make the sun position follow in a way it's usually visible: pick sun direction such that it's roughly perpendicular-ish to the camera's average position, giving nice terminator. Let's set camera path around the planet with theta slowly changing; sun fixed at (1, 0.4, 0.6) normalized... camera at theta = t*0.06 (very slow — 0.06 rad/s, in 30s only 1.8 rad). Hmm that's fairly fast actually: 103 degrees in 30 s. Good, we see different sides.

Let's choose sun direction = normalize(-0.7, 0.45, 0.9)? Let me think about what's visible: camera position p(t). The planet is at origin. The sun billboard at S = sunDir*60. It's visible when it's on the same side as... The camera looks at origin; the field of view is 50 degrees vertical (~half 25 deg). The sun at infinity in direction sunDir is visible if the angle between sunDir and (-camDir) < ~30 deg. -camDir is the unit vector from camera to origin = -normalize(p). So we need sunDir ≈ -normalize(p) roughly.

I could instead just orient the camera drift path so the sun is in frame: place camera roughly opposite of sun. E.g. camera position direction opposite to sun direction ± some spread. Let's set sunDir = (0.55, 0.4, 0.73) normalized; then camera base direction = -sunDir = (-0.55,-0.4,-0.73) normalized, and we drift around that base within ±35 degrees plus a polar oscillation. That guarantees the sun is likely in frame (nice lens flare) and the planet is fully lit toward camera (full phase, less terminator interest). Hmm, a full-lit planet looks flatter. A gibbous phase looks better: offset ~50-60 degrees from anti-sun so we see a terminator with sun still potentially in frame at the edge.

Compromise: drift amplitude ±45 degrees around a base 40 degrees off the anti-sun direction. Sun visible during part of the recording. Since the requirement says "distant sun with a lens-flare-like glow" and "show everything important within the first 30 seconds", it'd be nice if the sun shows up. Let's have the camera path oscillate such that the sun passes through the frame edge.

Simplest: define camera orbit angle θ(t) = θ0 + 0.05*t (slow), and set sun direction roughly perpendicular... Let me just directly compute: place camera at position p, and choose sunDir to be at an angle of ~65 degrees from -p̂, so the sun is outside the 25° half-FOV but the planet shows a nice crescent... Then no flare visible. Hmm.

Better approach: make the sun direction rotate slowly relative to camera? No—that's physically wrong but visually fine. Alternatively keep the sun mostly opposite the camera: put camera at angle θ, sun direction at angle θ + π + 0.5 (a ~30° offset). Then the sun is near frame edge (half-FOV 25° vertically, but horizontally wider since aspect > 1 — horizontal half-FOV ≈ atan(tan(25°)*aspect) ≈ 40° for aspect 1.7). So a 30° offset puts the sun just inside the horizontal edge. That's a classic composition. Then animate the offset oscillating between 0.3 and 0.9 rad so the sun moves in and out of view. Actually simpler: fix the offset at ~0.55 rad (31°) and let the camera drift slowly in polar angle.

But the sun direction changing over time is odd if the starfield is fixed... The starfield would need to rotate with it. Actually we could keep sunDir fixed in world and just define the camera orbit around it. The camera angle θ(t) can be anything: the sun is at fixed azimuth φ_s. The camera at azimuth φ_c(t) = φ_s + π + offset(t). That's fine — the camera drifts around and the sun stays fixed. 

So:
- sunDir (world, normalized) = (cos(a), sinY, sin(a)... let's just define: sunDir = normalize(0.4, 0.35, 1.0)? Something. Let's set sunDir = new THREE.Vector3(0.6, 0.35, 0.72).normalize().
- Camera: build a basis where "anti-sun" is the base direction. Let A = -sunDir. Define an orthonormal basis (A, U, V). Camera direction from origin: camDir = normalize( A*cos(offset) + side*sin(offset) ) where side is a vector perpendicular to A in the horizontal-ish plane. Then camera position = camDir * radius, with radius varying and a bit of elevation change.

Let's do this:
```
const A = sunDir.clone().negate(); // from origin toward camera base
const up = new THREE.Vector3(0,1,0);
const right = new THREE.Vector3().crossVectors(up, A).normalize(); // horizontal perpendicular
const upPerp = new THREE.Vector3().crossVectors(A, right).normalize();
// camera direction
const off = 0.55 + 0.35*Math.sin(time*0.13);
const elev = 0.18*Math.sin(time*0.09);
dir = A*cos(off)*cos(elev) + right*sin(off)*cos(elev) + upPerp*sin(elev)
camPos = dir * radius
```
Hmm careful: "right" is perpendicular to A and lies in the horizontal plane (cross(up, A) is horizontal). Good.

Then camera.lookAt(0,0,0) with slight target offset maybe. Fine.

The elevation changes and the sun stays near the frame edge. Good.

Actually with the offset oscillating between 0.2 and 0.9 rad, at 0.2 the sun is near the center of frame (behind the planet? no—if offset is 0 it's directly behind the planet, i.e., the camera is between the sun and the planet → sun behind the camera. Wait no.

Let's re-check: A = -sunDir is a direction from the planet's origin toward the anti-sun point. If the camera is at A*radius, then the camera is on the opposite side of the planet from the sun → the planet is fully lit (full phase) and the sun is directly behind the camera → not visible. If the camera is at right*radius (offset 90°), then the planet is at half phase and the sun is 90° off the view axis → not visible.

So the sun is visible only if the camera is roughly toward the sun (offset near 180°). Which means seeing the night side of the planet. Not good.

Conclusion: you can't have both a nicely lit planet and the sun in the same frame, unless the sun is just at the frame edge — meaning the camera offset from anti-sun is near the half-FOV, e.g., 35-40°. Then the sun is just outside/at the frame edge, and there'd be a lens flare partially visible at the edge... Meh.

Alternative: the sun can appear as a bright glow, and while it's off-screen, the lens flare ghosts can still be on screen — actually that's the classic lens flare behavior: ghosts spread across the screen even when... no, they're symmetric about the center, so if the sun is off-screen the ghosts are also off-screen.

OK, another approach: put the sun not "behind the camera" but in a direction such that the camera view includes the sun's glow at the frame edge, and the planet is a gibbous — that's the best composition. With FOV 50 and aspect ~1.78, the horizontal half-FOV is atan(tan(25°)*1.78) = atan(0.466*1.78)= atan(0.83)=39.7°. So put the sun at ~45° offset from the camera view axis so its bright glow (large, so it spills into the frame) is visible near the edge. Also the camera view axis direction is -camDir (pointing at the origin). The sun direction from the camera... roughly the sun direction sunDir means the sun is in direction sunDir from the camera too (infinitely far). Angle between sunDir and view axis (-camDir): if camDir = A*cos40 + right*sin40, then -camDir = -A cos40 - right sin40. sunDir = -A. Angle between sunDir(-A) and (-Acos40 - right sin40) is 40°. Yes so the offset angle = angle between the sun and the view axis.

So offset ~45-55° gives a gibbous planet with the sun's glow near the frame edge. Let's oscillate offset between 0.7 and 1.1 rad (40-63°). The sun glow is big (radius maybe 30° of the frame? a big glow blob) — it could be visible partly.

Hmm, honestly, maybe simpler and more visually satisfying: make the sun visible in-frame as a small bright disk with a big glow, and accept a crescent planet. Actually a crescent planet with an atmospheric rim glow is gorgeous, and the ring system catches light... But the terrain shader detail would be less visible.

Compromise: let the offset oscillate over a wide range: from 0.35 rad (20°, sun hidden behind the camera... no).

Alright, final decision: offset oscillates between ~0.5 and ~1.2 rad. Average ~0.85 rad = 49°, giving a gibbous-to-half planet with the sun near the frame edge. Its glow will be visible at the edge due to the large radius. Good enough. Also add lens flare ghosts that appear when it's on-screen.

Hmm, but "a distant sun with a lens-flare-like glow" — I want it to read clearly. Let me put a second consideration: the camera's FOV = 55, aspect = 1.78 → horizontal half FOV = atan(tan(27.5)*1.78)=atan(0.52*1.78)=atan(0.926)=42.8°. So sun offset up to ~45° is on-screen horizontally (when at the same elevation). Let's oscillate offset between 0.35 and 0.85 rad (20° to 49°). At 20° the planet is nearly full and the sun is on screen near the planet (bright glow behind/near the planet — cool!). At 49° the planet is a nice gibbous and the sun is just off the edge but its glow spills in. That's a good range. Let's do offset = 0.6 + 0.25*sin(t*0.11) → 0.35..0.85. 

But also the elevation oscillation changes the angle. Fine.

Now the sun's screen position: the projected position of the world point sunDir*60. That's in the scene; but I also want the flare overlay. Let's just compute the projection each frame in JS and use it for the ghosts.

Actually, do I need the overlay at all? Alternatively, put the flare in the 3D scene as additive billboards at the sun's world position, plus ghosts along the line from the sun's world position toward the camera... Lens ghosts are screen-space, but in 3D they can be approximated by placing small quads at points along the ray from the camera through the... Actually a decent approximation: ghosts lie along the line in screen space from the sun through the screen center. In 3D, the screen center corresponds to the camera's forward axis. So a ghost at screen-space position p = -k * sunNDC corresponds to a world direction d = normalize(camForward + ... ) — it's just unprojecting. Easier: do the overlay approach with an orthographic camera. I'll do the overlay.

Overlay implementation:
```js
const overlayScene = new THREE.Scene();
const overlayCam = new THREE.OrthographicCamera(-1,1,1,-1,0,1); // we'll handle aspect manually by scaling quads
```
Actually simpler: use an ortho camera with left=-aspect, right=aspect, top=1, bottom=-1, and place quads at (ndcX*aspect, ndcY). Then a quad of size s has half-width s and half-height s (since ortho y range is 2 units). Fine, just compute positions accordingly.

Then in render loop: after rendering the main scene (renderer.autoClear = true, render main), set `renderer.autoClear = false`, render overlayScene with overlayCam, then clear again next frame. Need `renderer.autoClear = true` at the start of each frame — set renderer.autoClear=true then render main, then set false and render overlay. Actually the standard: renderer.autoClear = false; then renderer.clear(); render(scene,camera); render(overlayScene, overlayCam).

Ghost quads: create a shared plane geometry and a shader material with uniforms for color and intensity; each ghost gets its own material instance (clone).

Now, if the sun is behind the center planet (occluded), the flares should ideally be dimmed. Skip.

Starfield: 6000-10000 points on a sphere of radius 300, with random sizes/colors. PointsMaterial with vertexColors, sizeAttenuation false? With size in pixels, sizeAttenuation false, size ~1.5. Use a mix: two Points systems, one with small stars, one with a few bigger ones. Also add a faint nebula? Not required.

Actually with PointsMaterial, size in pixels when sizeAttenuation is false — size 1.5-2.5 px looks good on a 2x DPR screen? RequestAnimationFrame — pixel ratio affects it. Use size 2.0 * pixelRatio? Just set size 1.8 and it's fine.

Let me also add a subtle galactic band? "dense starfield" — just make it dense.

Now the planet shader details.

Simplex noise GLSL (Ashima 3D):

```glsl
vec3 mod289(vec3 x){return x - floor(x*(1.0/289.0))*289.0;}
vec4 mod289(vec4 x){return x - floor(x*(1.0/289.0))*289.0;}
vec4 permute(vec4 x){return mod289(((x*34.0)+1.0)*x);}
vec4 taylorInvSqrt(vec4 r){return 1.79284291400159 - 0.85373472095314 * r;}

float snoise(vec3 v){
  const vec2 C = vec2(1.0/6.0, 1.0/3.0);
  const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
  vec3 i  = floor(v + dot(v, C.yyy));
  vec3 x0 = v - i + dot(i, C.xxx);
  vec3 g = step(x0.yzx, x0.xyz);
  vec3 l = 1.0 - g;
  vec3 i1 = min(g.xyz, l.zxy);
  vec3 i2 = max(g.xyz, l.zxy);
  vec3 x1 = x0 - i1 + C.xxx;
  vec3 x2 = x0 - i2 + C.yyy;
  vec3 x3 = x0 - D.yyy;
  i = mod289(i);
  vec4 p = permute(permute(permute(
             i.z + vec4(0.0, i1.z, i2.z, 1.0))
           + i.y + vec4(0.0, i1.y, i2.y, 1.0))
           + i.x + vec4(0.0, i1.x, i2.x, 1.0));
  float n_ = 0.142857142857;
  vec3 ns = n_ * D.wyz - D.xzx;
  vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
  vec4 x_ = floor(j * ns.z);
  vec4 y_ = floor(j - 7.0 * x_);
  vec4 x = x_ *ns.x + ns.yyyy;
  vec4 y = y_ *ns.x + ns.yyyy;
  vec4 h = 1.0 - abs(x) - abs(y);
  vec4 b0 = vec4( x.xy, y.xy );
  vec4 b1 = vec4( x.zw, y.zw );
  vec4 s0 = floor(b0)*2.0 + 1.0;
  vec4 s1 = floor(b1)*2.0 + 1.0;
  vec4 sh = -step(h, vec4(0.0));
  vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy;
  vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww;
  vec3 p0 = vec3(a0.xy,h.x);
  vec3 p1 = vec3(a0.zw,h.y);
  vec3 p2 = vec3(a1.xy,h.z);
  vec3 p3 = vec3(a1.zw,h.w);
  vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
  p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
  vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
  m = m * m;
  return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
}
```
That's the standard Ashima. Good.

Now the planet fragment shader:

```glsl
varying vec3 vObjPos;
varying vec3 vNormalW;
varying vec3 vViewDirW;

uniform vec3 uSunDirObj; // sun direction in object space
uniform vec3 uSunDirWorld;
uniform vec3 uMoonPosObj;
uniform float uMoonRadius;
uniform float uTime;
```

Hmm, I need lighting in object space consistently. Let's do all lighting in object space: transform the view direction into object space? Simpler: pass the world-space normal and world-space view direction, and compute the sun direction in world space; but the terrain noise uses object space. In the vertex shader I can output both: vObjPos (object space position) and vWorldNormal (world normal), vWorldPos.

Let's do that:
- vObjPos = position (object space, radius 1)
- vWorldNormal = normalize(mat3(modelMatrix) * normal) — for uniform scale it's fine.
- vWorldPos = (modelMatrix * vec4(position,1)).xyz

Fragment lighting:
- N = normalize(vWorldNormal)
- L = uSunDirWorld
- V = normalize(cameraPosition - vWorldPos)
- diff = max(dot(N,L), 0.0)

For the moon shadow, I need positions in object space: convert moon world position to planet object space on the CPU (uMoonPosObj) and also the sun direction in object space (uSunDirObj). Then compute in the fragment using vObjPos.

Since the geometry radius is 1 and vObjPos is the object-space position, I can compute:
```glsl
vec3 rel = uMoonPosObj - vObjPos;
float t = dot(rel, uSunDirObj);
float shadow = 0.0;
if (t > 0.0) {
  float d = length(rel - t*uSunDirObj);
  shadow = smoothstep(uMoonRadius*1.5, uMoonRadius*0.5, d) * smoothstep(0.0, 0.15, t);
}
```
Wait — uMoonPosObj is in planet object space, but the moon is much farther than the planet's surface, so rel has a large magnitude (like 2.5). The shadow should be a soft circle on the planet's surface. OK.

Also need the moon radius scaled: the moon's actual radius 0.18 → since the planet's object space is in the same units as world (planet radius 1, scale 1), the radius is 0.18. But the shadow of a sphere at distance t... using the perpendicular distance test with radius 0.18 gives a hard-edged shadow that matches the moon's radius. Fine.

Also the shadow needs the light to actually pass — if the sun is on the other side, t < 0 → no shadow. Correct.

Now, about softness: use smoothstep(uMoonRadius, uMoonRadius*0.2, d) for a soft penumbra.

Now the terrain colors:

```glsl
vec3 p = normalize(vObjPos);
float c1 = fbm(p*1.7);
float c2 = fbm(p*4.3 + 17.0);
float cont = c1 + 0.35*c2;
```
Hmm fbm returns roughly [-1,1] but with 5 octaves of simplex, the sum of amplitudes is ~0.97, and each value is in [-1,1], so the fbm is in [-1,1] typically smaller, around [-0.6,0.6]. Let's just normalize and tune by multiplying.

Let me define fbm with 6 octaves and multiply by 1.2 for the range. I'll just pick thresholds empirically-ish; can't test, so choose robust values.

Let me use a warp for interest: 
```
float cont = fbm(p*1.6 + vec3(0.0)) * 1.1;
```
Threshold at 0 for the coastline with a smoothstep(-0.04, 0.04, cont) for the land mask.

Ocean depth color: mix deep blue (0.02,0.06,0.22) with shallow (0.05,0.35,0.5) based on the continent value: shallow near the coast.

Land: elevation e = cont; 
- lowland green (0.12,0.32,0.12) 
- mid: (0.35,0.3,0.18) 
- high: (0.45,0.42,0.38)
- snow on high peaks: mix to white for e > 0.45.

Also add a slight noise-based color variation.

Ice caps: lat = abs(p.y) with noise warp:
```
float iceN = fbm(p*2.5 + 31.0)*0.12;
float ice = smoothstep(0.62 + iceN, 0.78 + iceN, abs(p.y));
```
That gives caps at the poles with irregular edges. Also mix into land/ocean color.

Also add small ice on high mountains.

Then a specular highlight on the ocean:
```
vec3 H = normalize(L+V);
float spec = pow(max(dot(N,H),0.0), 60.0) * (1.0 - landMask) * 0.8;
```

Then combine:
```
vec3 col = mix(oceanCol, landCol, landMask);
col = mix(col, vec3(0.92,0.95,1.0), ice);
float diff = max(dot(N,L),0.0);
float terminator = smoothstep(-0.15, 0.35, dot(N,L));
vec3 lit = col * (0.06 + 1.15*diff) ... 
```
Better: `float lightAmt = clamp(dot(N,L),0.0,1.0); vec3 finalCol = col * (0.03 + lightAmt) + spec;` Plus a night-side slight blue ambient.

Add fresnel rim on the planet itself: `float fres = pow(1.0 - max(dot(N,V),0.0), 3.0); finalCol += vec3(0.25,0.45,0.9) * fres * lightAmt * 0.8;`

Apply shadow: `finalCol *= (1.0 - 0.85*shadow);`

That's the planet.

Cloud shader: separate material with noise-based alpha:
```glsl
// vertex: pass vObjPos, vWorldNormal, vWorldPos
// fragment:
vec3 p = normalize(vObjPos);
float n = fbm(p*3.0 + uTime*0.02); // slight evolution
float n2 = fbm(p*7.0 - uTime*0.03);
float d = n*0.7 + n2*0.3;
float a = smoothstep(0.05, 0.35, d);
// density modulated by bands
float band = 0.6 + 0.4*sin(p.y*8.0);
a *= band... 
```
Keep it simple; maybe skip bands. Add latitudinal variation for realism: clouds are denser near the equator and mid-latitudes. `a *= 0.55 + 0.45*sin(p.y*6.0)`? Something subtle.

Lighting: diff = max(dot(N,L),0) with a soft terminator, `vec3 cloudCol = vec3(1.0) * (0.15 + 0.95*diff)`, alpha *= 0.85. Also fade the alpha near the limb? Not needed with depth testing since the planet occludes.

The clouds should also cast a shadow on the planet? Nice but requires texture-free ray marching through the cloud noise from the surface point toward the sun — actually that's doable in the planet shader: sample the same cloud noise along the ray. Costly but nice. Maybe skip; use a simpler approach: in the planet shader, sample the cloud fbm at a point offset toward the sun and darken. Hmm, that gives fake cloud shadows. Let's skip to keep it clean — actually a cheap version: `float cs = cloudDensity(p + L*0.03)` and multiply the light by (1 - 0.4*cs). Cheap, one extra fbm call (5 octaves). That's fine, but the fbm is 5-6 octaves × 2 for the two layers — the planet fragment shader is already heavy. Might be fine on modern GPUs. Let's include a single-octave-ish version for the cloud shadow: use fbm 3 octaves. Eh, I'll include it, low cost.

Actually let's keep the shader simpler to avoid perf issues: I'll include cloud shadows with a 3-octave fbm at the sun-offset point. Fine.

Atmosphere glow shader:
```glsl
// vertex
varying vec3 vNormalW;
varying vec3 vWorldPos;
varying vec3 vObjPos;
// fragment
vec3 N = normalize(vNormalW);
vec3 V = normalize(cameraPosition - vWorldPos);
float fres = pow(1.0 - abs(dot(N,V)), 3.5);
float sun = max(dot(N, uSunDirWorld), 0.0);
float sunFade = 0.15 + 0.85*pow(sun, 1.5);
// also forward scattering: when looking toward the sun through the atmosphere
float fwd = pow(max(dot(-V, uSunDirWorld), 0.0), 2.0); // hmm
vec3 col = mix(vec3(0.25,0.5,1.0), vec3(0.6,0.8,1.0), sun);
gl_FragColor = vec4(col * fres * sunFade * 1.6, 1.0); // additive
```
With blending additive and side BackSide.

Careful: for BackSide, the normal in the fragment shader is the geometry's normal (outward) but it's still the outward normal; abs(dot) handles it. Actually with BackSide rendering, three.js flips the normal in the shader? In the built-in materials yes, but for a raw ShaderMaterial the normal attribute is the outward normal. Using abs() is safe.

The planet's rim is at radius 1 and the atmosphere at 1.06 — the fresnel will be near 1 at the silhouette.

Rings shader:
```glsl
varying vec2 vUv;
varying vec3 vObjPos;
varying vec3 vWorldNormal;
varying vec3 vWorldPos;
// fragment
float r = length(vObjPos.xy); // ring in XY plane
float inner = 1.45, outer = 2.75;
float t = (r - inner)/(outer-inner); // 0..1
// bands
float bands = fbm(vec3(r*8.0, 0.0, 0.0)); // 1D noise
```
Better to use a hash-based 1D noise, or just use sin combos:
```
float b = 0.0;
b += 0.5*sin(r*38.0);
b += 0.3*sin(r*77.0+1.7);
b += 0.2*sin(r*13.0+0.4);
b = b*0.5+0.5;
float alpha = smoothstep(0.0,0.06,t) * (1.0 - smoothstep(0.85,1.0,t));
alpha *= mix(0.25, 0.85, b);
// gap (Cassini-like)
float gap = smoothstep(0.02, 0.05, abs(t-0.62));
alpha *= gap;
```
Colors: pale tan/white, brighter where the noise is high.

Lighting: the rings are lit by the sun; simple: `float light = 0.35 + 0.65*abs(dot(normalize(vWorldNormal), uSunDirWorld))`? The ring's normal is perpendicular to the ring plane, so it doesn't vary across the ring; it just tells us the sun angle relative to the ring plane. Fine, that's physically right for a flat ring: the illumination is proportional to |sin(sun angle above the ring plane)|. Use the world normal of the ring plane: since it's a flat ring, the surface normal is constant. Good, that gives uniform illumination. Add a shadow from the planet onto the rings? Nice but complex; skip. Add a slight radial brightness variation instead.

Should the rings be visible both above and below? DoubleSide.

The ring should also be occluded by the planet correctly — with depthTest true and depthWrite false, and double-side, it works.

Now, the moon:
- Sphere geometry radius 0.16, ShaderMaterial with simple crater-ish noise gray shading (use fbm to create albedo variation), lit by sun; also the moon should have a subtle emission when in the shadow? No.
- Orbit: radius 2.3, inclination ~0.35 rad, period ~26s. Moon casts a shadow on the planet when aligned — the moon's orbit plane vs the sun direction determines whether eclipses happen. To guarantee a nice shadow event within 30s, I should make the eclipse happen. Let's force it: compute the moon position so that at some time it lines up with the sun direction from the planet.

Simplest: put the moon's orbital plane containing the sun direction. If the orbit is in a plane that contains the sun direction vector, then every orbit the moon passes between the sun and the planet → eclipse once per orbit, and also behind the planet (planet's shadow on the moon). 

So: define the moon orbit plane spanned by the sun direction S and a perpendicular vector P. Moon position = R*(cos(θ)*P + sin(θ)*S). Then when θ = 90°, the moon is in the sun direction → eclipse of the planet. When θ = -90°, it's behind → eclipsed by the planet.

Add a slight offset so it's not exactly through the center — an impact parameter, so the shadow crosses the planet's disk and is visible. Let's add a small tilt: orbit plane normal tilted by ~0.15 rad from perpendicular... Actually, if the orbit plane is exactly spanned by S and P and the moon is at angle θ, the line planet→moon makes angle θ with... The moon at θ=90 is at S*R, directly between the sun and the planet → central eclipse. To make the shadow cross off-center, I can rotate the orbit plane slightly around the P axis. Let's just add a small inclination: use axis vectors P and S' where S' = S rotated by ~12° around P. Then at θ=90°, the moon is at R*S', which is 12° off the sun direction → the shadow lands off-center on the planet. 

Let's do that. Orbit period ~ 22 s so we get an eclipse in the first 30 s. Start the moon at θ = -30° so it reaches the eclipse (θ=90) at t = 120/360*22 = 7.3 s. Nice, an eclipse early on. Then at θ = -90+180... whatever. Let's start θ0 = -40°.

Hmm, but the shadow needs the moon to be between the planet and the sun in world space, and the planet's shader computes that. Fine.

Also "the moon casts light" — maybe I'll add a faint secondary light on the planet from the moon? That'd be moonlight — negligible. I'll interpret "casts light and shadow interest" as it being a lit body creating shadows. Also the moon could have a glow. I'll add a subtle glow sprite around the moon? It's just a rock. Maybe skip; keep it lit nicely.

Actually, let's add the moon's shadow AND the moon's own cast shadow on the rings? Skip.

I'll also ensure the moon passes in front of the planet visually (transit) — with the orbit plane containing the sun direction and the camera near the anti-sun... the transit happens near the eclipse, so the moon will be seen crossing in front of the planet. 

Now the moon's radius: 0.16, at distance 2.3. The angular size is small but visible.

Let's now write the code.

Structure:

```js
import * as THREE from 'three';

const canvas = document.getElementById('c');
const renderer = new THREE.WebGLRenderer({canvas, antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.autoClear = false; // manual

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(55, innerWidth/innerHeight, 0.1, 2000);
```

Sun direction: `const sunDir = new THREE.Vector3(0.55, 0.30, 0.78).normalize();`

Starfield:
```js
const starGeo = new THREE.BufferGeometry();
const N = 9000;
const pos = new Float32Array(N*3);
const col = new Float32Array(N*3);
const sizes = new Float32Array(N);
for (...) {
  // random on sphere
  const u = Math.random()*2-1, a = Math.random()*Math.PI*2;
  const s = Math.sqrt(1-u*u);
  const r = 700 + Math.random()*200;
  ...
}
starGeo.setAttribute('position', ...); setAttribute('color', ...)
const starMat = new THREE.PointsMaterial({size: 2.2, sizeAttenuation:false, vertexColors:true, transparent:true, depthWrite:false});
```
Star colors: bluish-white to warm. Set the material blending to Additive for brightness? With vertexColors and additive, bright stars pop. Use AdditiveBlending with opacity 1.

For the vertex color, use `new THREE.Color().setHSL(0.55 + (Math.random()-0.5)*0.2, 0.4, 0.7 + Math.random()*0.3)` — hmm, setHSL with lightness ~0.8 gives near white. Good.

Camera far = 2000, stars at 700-900. Sun billboard at ~600? Actually I'll not render the sun in 3D; I'll only do the overlay flare. But then nothing bright is in the 3D scene — the flare overlay handles it. The overlay ghosts' intensity fades based on the sun's NDC position; when off-screen, fade out. Also the main "sun disk" glow: I'll render it as an overlay quad at the sun NDC position with a big size, clipped by the screen edges (which is fine, since only the visible part shows). But wait: if the sun is behind the camera, its projected NDC is garbage. Need to handle: compute the camera-space position of the sun point; if z > 0 (behind), hide the flare.

Let me compute in JS:
```js
const sunPoint = new THREE.Vector3().copy(sunDir).multiplyScalar(500);
// transform to camera space
const camSpace = sunPoint.clone().applyMatrix4(camera.matrixWorldInverse);
const visible = camSpace.z < 0;
const ndc = sunPoint.clone().project(camera);
```
If not visible, hide the overlay (set opacity 0).

For the enclouded sun disk size, the glow should be large. Use multiple quads:
- Core: size 0.09 (in NDC-ish units), color warm white, bright.
- Halo: size 0.35, soft, warm.
- Streak: horizontal elongated, size (1.2, 0.03).
- Ghosts: 6 quads along the line from center: position = -ndc * k for k in [0.35, 0.6, 0.95, 1.3, 1.7, 2.1], sizes 0.03-0.12, colors: teal/orange/violet-ish, low intensity.

The overlay ortho camera: left=-aspect, right=aspect, top=1, bottom=-1. Positions: (ndc.x*aspect, ndc.y).

The quad geometry: PlaneGeometry(1,1), and each mesh scaled to the needed size. The glow shader:

```glsl
varying vec2 vUv;
uniform vec3 uColor;
uniform float uIntensity;
uniform float uPower;
void main(){
  float d = length(vUv - 0.5) * 2.0;
  float a = pow(max(0.0, 1.0 - d), uPower);
  // for the streak we scale the quad, so this is fine
  gl_FragColor = vec4(uColor * a * uIntensity, a * uIntensity);
}
```
With AdditiveBlending, depthTest false, depthWrite false, transparent true. The alpha doesn't matter for additive; keep it.

For the streak, I'd want a different falloff (elongated). Since the quad is scaled non-uniformly, `vUv` based falloff is in quad space → automatically elongated. 

Now the main render function.

Time: use the rAF timestamp: `function animate(now){ const t = now * 0.001; ... }`.

Let me now write everything.

```js
// ---------- Planet ----------
const planetGroup = new THREE.Group();
planetGroup.rotation.z = THREE.MathUtils.degToRad(23.5);
scene.add(planetGroup);

const planetUniforms = {
  uSunDirWorld: { value: sunDir },
  uSunDirObj: { value: new THREE.Vector3() },
  uMoonPosObj: { value: new THREE.Vector3() },
  uMoonRadius: { value: 0.16 },
  uTime: { value: 0 },
};
```

Wait, the planet's axial tilt: if I rotate the planetGroup around z by 23.5°, then the planet's local Y is the spin axis, tilted. Good, and the rings are in the group's XZ plane... The ring geometry is created in the XY plane and rotated -PI/2 about X to lie in the XZ plane. Then it's tilted with the group. Good, so the rings share the planet's equatorial plane — that's actually correct for ring systems.

Planet mesh with ShaderMaterial. Also, I need the world-space normal in the fragment shader. Use `vNormalW = normalize(mat3(modelMatrix) * normal)`.

Vertex shader for the planet:
```glsl
varying vec3 vObjPos;
varying vec3 vWorldNormal;
varying vec3 vWorldPos;
void main(){
  vObjPos = position;
  vWorldNormal = normalize(mat3(modelMatrix) * normal);
  vec4 wp = modelMatrix * vec4(position,1.0);
  vWorldPos = wp.xyz;
  gl_Position = projectionMatrix * viewMatrix * wp;
}
```

Note: modelMatrix for a mesh with rotation only — fine.

Fragment shader as designed.

Let me write out the fbm and colors carefully.

```glsl
float fbm(vec3 p){
  float s = 0.0, a = 0.5;
  for(int i=0;i<5;i++){ s += a*snoise(p); p *= 2.07; a *= 0.5; }
  return s / 0.969; // normalize by sum of amplitudes (0.5+0.25+0.125+0.0625+0.03125=0.96875)
}
```
So fbm is in ~[-1,1].

Continents:
```glsl
vec3 p = normalize(vObjPos);
// domain warp for more interesting coastlines
vec3 warp = vec3(fbm(p*3.1+vec3(1.7)), fbm(p*3.1+vec3(9.2)), fbm(p*3.1+vec3(4.4)));
float cont = fbm(p*1.5 + warp*0.35);
float detail = fbm(p*6.0);
float landH = cont + 0.12*detail;
float landMask = smoothstep(-0.03, 0.06, landH);
```
Hmm, the domain warp with 3 fbm calls (5 octaves each) plus another fbm... that's 25 snoise calls just for that. Too heavy? Each snoise is ~ 50 ops. 25*50 = 1250 ops per fragment. On a full-screen planet at 1080p that's ~2M fragments * 1250 = 2.5 GFLOP-ish per frame. Modern GPUs handle that, but integrated ones might struggle. Let's reduce: use 4 octaves and skip the 3-way warp; use a single warp vector:

```glsl
vec3 warp = vec3(fbm(p*2.0+vec3(1.3)), fbm(p*2.0+vec3(7.7)), fbm(p*2.0+vec3(3.9)));
```
That's still 3 fbm calls. Let's instead do a cheaper warp: use one fbm and derive 3 components from it? Meh. Alternatively skip the warp entirely and rely on the octaves. Simplest: `cont = fbm(p*1.6)`, and the coastlines will be fine (fbm continents look OK).

I'll do a single warp axis: `float w = fbm(p*2.5); vec3 pw = p + 0.15*w;` — hmm, warping along the normalized direction changes the length, but since we re-normalize for noise... Actually, we can just add the warp as a scalar offset to the noise input: `cont = fbm(p*1.6 + vec3(w)*0.6)`. That's a cheap warp and gives more organic shapes. OK.

Let's implement:
```glsl
float w = fbm(p*2.2 + 5.0);
float cont = fbm(p*1.6 + w*0.5);
float detail = fbm(p*7.0);
```
3 fbm calls (5 octaves each) = 15 snoise calls. Plus a cloud-shadow sample (3 octaves). Acceptable.

Land/sea:
```glsl
float sea = smoothstep(-0.05, 0.02, cont);
// ocean colors
vec3 deep = vec3(0.008, 0.045, 0.16);
vec3 shallow = vec3(0.03, 0.28, 0.42);
vec3 ocean = mix(deep, shallow, smoothstep(-0.25, 0.0, cont));
// land colors
float elev = cont + detail*0.15;
vec3 sand = vec3(0.55,0.5,0.35);
vec3 grass = vec3(0.15,0.35,0.13);
vec3 forest = vec3(0.08,0.22,0.10);
vec3 rock = vec3(0.35,0.30,0.24);
vec3 land = mix(sand, grass, smoothstep(0.0, 0.08, elev));
land = mix(land, forest, smoothstep(0.08, 0.25, elev));
land = mix(land, rock, smoothstep(0.30, 0.5, elev));
land = mix(land, vec3(0.95), smoothstep(0.55, 0.75, elev)); // snowy peaks
```
Eh, values need to be consistent with the cont range. Since fbm is roughly in [-0.7, 0.7] mostly, thresholds of 0.5 for peaks might be rarely reached. Let's scale: `cont *= 1.4` after computing to widen the range. Hmm. Let me just set the fbm to output a wider range by scaling: return s * 1.4 (clamped implicitly). Then the range is about [-1, 1] with typical values [-0.7, 0.7]. Thresholds: sea level at 0.0; land up to 0.7.

Set:
- sea level 0.0
- beaches 0.0-0.06
- grass 0.06-0.25
- forest 0.25-0.4
- rock 0.4-0.55
- snow 0.55+

And the ocean depth uses cont from -0.7 to 0.

Ice caps: `float iceLat = smoothstep(0.72 + iceN, 0.86 + iceN, abs(p.y));` with p.y the object-space latitude. Plus make the poles white and blend with the underlying color.

Also add polar sea ice: near the poles the ocean becomes white.

Let me now write the fragment main:

```glsl
void main(){
  vec3 p = normalize(vObjPos);
  vec3 N = normalize(vWorldNormal);
  vec3 V = normalize(cameraPosition - vWorldPos);

  // --- terrain ---
  float w = fbm(p*2.2 + 5.0);
  float cont = fbm(p*1.6 + w*0.6) * 1.35;
  float detail = fbm(p*7.0);

  float landMask = smoothstep(-0.02, 0.05, cont);

  vec3 deep = vec3(0.006,0.04,0.13);
  vec3 shallow = vec3(0.02,0.24,0.4);
  vec3 ocean = mix(deep, shallow, smoothstep(-0.6,-0.02,cont));

  float elev = cont + detail*0.12;
  vec3 sand = vec3(0.62,0.56,0.4);
  vec3 grass = vec3(0.16,0.36,0.14);
  vec3 forest = vec3(0.07,0.2,0.09);
  vec3 rock = vec3(0.34,0.29,0.24);
  vec3 land = mix(sand, grass, smoothstep(0.0,0.07,elev));
  land = mix(land, forest, smoothstep(0.07,0.25,elev));
  land = mix(land, rock, smoothstep(0.3,0.5,elev));
  land = mix(land, vec3(0.9,0.92,0.95), smoothstep(0.5,0.7,elev));

  vec3 albedo = mix(ocean, land, landMask);

  // ice caps
  float iceNoise = fbm(p*3.0 + 21.0)*0.1;
  float ice = smoothstep(0.66 + iceNoise, 0.80 + iceNoise, abs(p.y));
  albedo = mix(albedo, vec3(0.88,0.93,0.98), ice);
  ...
}
```
Careful with `p*2.2 + 5.0` — vec3 + float works in GLSL (converted to vec3(5.0)). Yes, scalar + vec3 is allowed.

The lighting:

```glsl
vec3 L = uSunDirWorld;
float ndl = dot(N, L);
float diff = max(ndl, 0.0);

// cloud shadow
vec3 pc = normalize(vObjPos + L*0.05); // hmm, this is object space vs world space mismatch
```
The cloud shadow needs consistent space. Let's compute the cloud density in object space: the offset toward the sun in world space must be converted to object space — I have uSunDirObj. So: `vec3 shadowSampleP = normalize(vObjPos + uSunDirObj*0.06);` then `float cd = fbm(shadowSampleP*3.5);` where fbm here should match the cloud shader's noise for correctness; use a similar one. Then `diff *= 1.0 - 0.45*smoothstep(0.05,0.4,cd)`.

Fine.

```glsl
vec3 col = albedo * (0.035 + 1.0*diff);
// specular on water
vec3 H = normalize(L+V);
float spec = pow(max(dot(N,H),0.0), 80.0) * (1.0-landMask) * (1.0-ice) * 0.9 * step(0.0, ndl);
col += vec3(spec);
// rim/atmospheric on planet
float fres = pow(1.0 - max(dot(N,V),0.0), 3.0);
col += vec3(0.2,0.45,0.95) * fres * (0.15 + 0.85*diff) * 0.7;
// night side ambient
col += albedo * 0.02 * vec3(0.4,0.6,1.0);
// moon shadow
...
col *= (1.0 - 0.88*shadow);
gl_FragColor = vec4(col, 1.0);
```
Note: applying the shadow after the specular/rim is fine.

Also tone: the output is in linear space? With three.js r186, the default output color space is sRGB and the renderer applies output color space conversion only for materials that... For raw ShaderMaterial, three.js does NOT automatically apply tone mapping / color space conversion to the fragment output — wait, it does: for ShaderMaterial, three.js appends nothing; the shader output goes directly to the framebuffer. But with `renderer.outputColorSpace = SRGBColorSpace`, three.js relies on the material's fragment shader to include the `colorspace_fragment` chunk. For raw ShaderMaterial, that isn't included unless we add it. So our colors will be treated as already sRGB-encoded... hmm, actually if outputColorSpace is sRGB and the render target is the default framebuffer, WebGL will just write the values as-is (no conversion) for raw shaders. So our color values are displayed directly as sRGB values. That means the linear-ish albedo values we choose will look darker than expected. So I should pick colors that look right as sRGB directly (i.e., treat them as display values). My chosen values like vec3(0.16,0.36,0.14) as sRGB display green is fine.

So basically treat all colors as final display values. The lighting multiplication in this pseudo-space is not physically correct but looks fine artistically. I'll just tune for looks.

Alternatively add `#include <tonemapping_fragment>` and `#include <colorspace_fragment>` in the shader. THREE.ShaderMaterial supports includes... it does process #include in the shader source. And the uniforms/defines needed (toneMappingExposure) are auto-injected? For ShaderMaterial, three.js doesn't inject tone mapping defines automatically... Actually it does add `#define TONE_MAPPING` etc. via the program's getToneMappingFunction... In WebGLProgram, for ShaderMaterial the prefixFragment includes tone mapping defines and the `toneMappingExposure` uniform is part of the common uniforms? Hmm, the uniform `toneMappingExposure` is set in WebGLRenderer.refreshUniforms for materials... I recall that using `#include <tonemapping_fragment>` with ShaderMaterial works and the exposure uniform is auto-provided. And `#include <colorspace_fragment>` requires `gl_FragColor` and works too. This is risky. Let's avoid it and just design the colors in display space. Simple and safe.

So I'll pick the final colors directly. Let's brighten the albedo values a bit since we multiply by the diffuse.

OK.

The cloud shader:

```glsl
varying vec3 vObjPos; varying vec3 vWorldNormal; varying vec3 vWorldPos;
uniform vec3 uSunDirWorld; uniform float uTime; uniform vec3 uSunDirObj;

void main(){
  vec3 p = normalize(vObjPos);
  float n1 = fbm(p*3.2 + uTime*0.01);
  float n2 = fbm(p*6.5 - uTime*0.015);
  float d = n1*0.65 + n2*0.35 + 0.06;
  float a = smoothstep(0.02, 0.4, d);
  // equatorial banding
  a *= 0.75 + 0.25*sin(p.y*7.0);
  vec3 N = normalize(vWorldNormal);
  vec3 V = normalize(cameraPosition - vWorldPos);
  float ndl = dot(N, uSunDirWorld);
  float light = smoothstep(-0.25, 0.35, ndl);
  vec3 cloudCol = mix(vec3(0.25,0.3,0.42), vec3(1.0,0.98,0.95), light);
  // limb fade
  float limb = pow(1.0 - abs(dot(N,V)), 1.0); // not needed
  gl_FragColor = vec4(cloudCol, a*0.9);
}
```
Blending: normal (transparent), depthWrite false, side FrontSide.

Note: the cloud layer must render after the planet (transparent objects render after opaque by default). Good.

Also the clouds only on the day side — the night-side clouds would be dark (mixing to vec3(0.25,0.3,0.42) with light 0 gives dark blue-gray). Fine.

Now: does the cloud sphere at radius 1.015 have its normals outward? Yes.

Atmosphere at radius 1.08, BackSide, additive, depthWrite false. But the clouds are inside the atmosphere sphere (1.015 < 1.08) — the atmosphere's back faces get depth-tested against the clouds... the clouds write no depth, so the atmosphere renders fine. But wait: the transparent rendering order — three.js sorts transparent objects by distance (back to front). The atmosphere (BackSide) at 1.08 and the clouds at 1.015 — the sorting is by the object's centroid distance from the camera, which is the same (origin) for both. So the order is arbitrary/stable by renderOrder. Set the atmosphere's renderOrder = 2 and the clouds' renderOrder = 1, and the ring's renderOrder = 0? Hmm, the rings need to be sorted with the planet: if the rings are behind the planet... the rings are opaque-ish transparent — they'll be drawn after the opaque planet (since transparent), and depth testing will hide the parts behind the planet. Good.

The atmosphere with additive blending drawn after the clouds is fine.

Ring renderOrder: 0, clouds: 1, atmosphere: 2.

Now the moon.

```js
const moonUniforms = { uSunDirWorld: {value: sunDir} };
const moonMat = new THREE.ShaderMaterial({vertexShader: moonVert, fragmentShader: moonFrag});
const moon = new THREE.Mesh(new THREE.SphereGeometry(0.16, 48, 32), moonMat);
scene.add(moon);
```
Moon fragment: fbm-based gray craters + lighting, plus a slight rim.

Moon orbit in JS:
```js
const orbitR = 2.35;
const orbitPeriod = 24; // seconds
// build orbit basis
const S = sunDir.clone();
const P = new THREE.Vector3().crossVectors(S, new THREE.Vector3(0,1,0)).normalize(); // perpendicular to S
// tilt S slightly around P to offset the eclipse
const axis = P.clone();
const S2 = S.clone().applyAxisAngle(axis, 0.30); // 17 degrees off
```
Hmm, rotating S around P: S is perpendicular to P, so rotating around P moves S within the plane perpendicular to P. Then the moon at angle θ=90 sits at S2*R, which is 17° off the sun direction, so the shadow lands off-center on the planet's disk, and the moon transits the planet's disk as seen from the camera (roughly). 

Moon position = orbitR * (cos θ * P + sin θ * S2) — wait, P and S2 are perpendicular unit vectors, so this is a circle in that plane. At θ=90°, the position is along S2 → near the sun direction. Good.

Also, since the camera is roughly on the anti-sun side, the moon near θ=90 is between the camera and the planet → visible transiting. 

Eclipse timing: θ(t) = θ0 + 2π t/period. Want θ=π/2 at t≈8s. θ0 = π/2 - 2π*8/24 = 1.5708 - 2.094 = -0.523 rad (-30°). Good.

Also, since θ goes through 90° at t=8, the shadow sweeps across the planet — very nice.

Now, the moon's position must be updated each frame and set as a uniform in the planet shader (in the planet's object space).

```js
moon.updateMatrixWorld();
const moonObj = planetMesh.worldToLocal(moon.position.clone());
planetUniforms.uMoonPosObj.value.copy(moonObj);
```
planetMesh.worldToLocal requires the matrixWorld to be up to date. Call planetGroup.updateMatrixWorld(true) first, or just compute manually since the transforms are simple. I'll call `planetMesh.updateWorldMatrix(true, false)` before worldToLocal. Actually `worldToLocal` uses `this.matrixWorld` inverse, so ensure it's updated: `scene.updateMatrixWorld()` at the start of the frame handles it. Then update the moon position, then updateMatrixWorld again? Order: update the moon's position → scene.updateMatrixWorld(true) → then compute the uniforms. Good.

But the planet's spin needs to be applied before that.

Similarly, the sun direction in planet object space:
```js
const q = planetMesh.getWorldQuaternion(new THREE.Quaternion()).invert();
uSunDirObj = sunDir.clone().applyQuaternion(q);
```
getWorldQuaternion also decomposes matrixWorld — fine after updateMatrixWorld.

Let's be careful: `getWorldQuaternion` requires the matrixWorld to be updated. Fine.

Now the animation loop:

```js
let last = 0;
function animate(now){
  requestAnimationFrame(animate);
  const t = now * 0.001;
  ...
  renderer.clear();
  renderer.render(scene, camera);
  renderer.render(overlayScene, overlayCam);
}
requestAnimationFrame(animate);
```
Note the timestamp `now` starts near 0 (the time origin is the page load), so t starts near 0. Good.

Wait: requestAnimationFrame's timestamp is the time since the time origin, which includes the module load time — fine.

Resize handler: update camera aspect, renderer size, overlay camera's left/right.

Let's write the code.

```js
const uniforms = {
  uSunDirWorld: { value: sunDir },
  ...
};
```
All planet materials share certain uniforms? Each material needs its own uniform objects unless shared. I'll create a shared uniforms object for the sun direction and time, and reuse it across materials — three.js allows sharing uniform objects across materials? Yes, if you pass the same uniform object reference, they share it. But it's cleaner to define per material and update each. I'll use a global `sharedUniforms` object and spread the values into each material's uniforms. Actually spreading `{...sharedUniforms}` copies the references to the uniform objects, so they're shared. That works — updating `sharedUniforms.uSunDirWorld.value` updates all. 

Careful: three.js mutates uniform objects? It reads `.value` only. Sharing is fine.

Let me now write all the shader strings.

Common GLSL header (noise) — I'll define a JS const string and prepend it to the fragment shaders that need it.

```js
const NOISE_GLSL = `
vec3 mod289(vec3 x){...}
...
float snoise(vec3 v){...}
float fbm(vec3 p){ float s=0.0,a=0.5; for(int i=0;i<5;i++){ s+=a*snoise(p); p*=2.07; a*=0.5;} return s*1.35; }
`;
```
Wait, s*1.35 where the max is ~1.0 (sum of amplitudes 0.969) → the range becomes ~[-1.35, 1.35]. Typical values would be around ±0.7. That's what I planned (cont*1.35). Let me instead not scale inside fbm, and scale at the call site for clarity. I'll keep fbm returning ~[-1,1] and multiply where needed.

Now writing everything out.

Ring geometry: `new THREE.RingGeometry(1.45, 2.75, 256, 8)`. Note RingGeometry's UVs and the fact that it's in the XY plane. In the vertex shader, `position.xy` gives the radial coordinates. Good.

Ring tilt: since it's inside the planetGroup (z-rotation of 23.5°), I additionally rotate the ring mesh by -PI/2 around X to put it in the XZ plane. Then its world normal is the group's Y axis.

The ring's fragment: compute r = length(vObjPos.xy). Lighting with the world normal (constant). Use the sun direction in world.

```glsl
float r = length(vObjPos.xy);
float t = (r - 1.45)/(2.75-1.45);
float bands = 0.5 + 0.5*sin(r*46.0)*0.5 + 0.5*sin(r*97.0+2.1)*0.3 + 0.5*sin(r*17.0+0.7)*0.2;
```
Hmm, let me write: 
```glsl
float b = 0.0;
b += 0.5*sin(r*43.0);
b += 0.3*sin(r*91.0 + 1.7);
b += 0.2*sin(r*19.0 + 0.4);
b = 0.5 + 0.5*b; // 0..1
```
alpha = edgeFade * mix(0.15, 0.75, b).
Add a gap: `alpha *= 1.0 - 0.85*exp(-pow((t-0.63)/0.03,2.0));`

Also add a subtle large-scale variation.

Color: `vec3(0.85,0.78,0.66)` tinted; brighter where b is high.

Lighting: 
```glsl
float sunAlt = abs(dot(normalize(vWorldNormal), uSunDirWorld)); // 0..1, how much the sun is out of the ring plane
float lightAmt = 0.25 + 0.75*sunAlt;
```
Hmm, but the ring's normal is fixed, so sunAlt is a constant across the ring — fine.

Also add a shadow of the planet on the rings? Skip.

Also the ring should be dimmer where it's on the far side? Skip.

Let's also add a fresnel-like fade at grazing angles? Skip.

Alright.

One more consideration: The rings should occlude/be occluded by the planet correctly for the far half of the ring — with depthTest true and depthWrite false, the far half behind the planet is hidden. Yes.

The near half of the ring in front of the planet: drawn after the planet, alpha blended, so it shows over the planet. Correct.

Now, the camera path.

```js
const camBase = sunDir.clone().negate(); // direction from origin toward camera base
const up = new THREE.Vector3(0,1,0);
const right = new THREE.Vector3().crossVectors(up, camBase).normalize();
const upPerp = new THREE.Vector3().crossVectors(camBase, right).normalize();
```
Note cross(up, camBase) gives a vector perpendicular to both → horizontal. Good. And upPerp = cross(camBase, right) — this is in the plane containing camBase and up. Good.

```js
const off = 0.62 + 0.28*Math.sin(t*0.11);
const elev = 0.22*Math.sin(t*0.077 + 1.0);
const dirToCam = camBase.clone().multiplyScalar(Math.cos(off)*Math.cos(elev))
  .add(right.clone().multiplyScalar(Math.sin(off)*Math.cos(elev)))
  .add(upPerp.clone().multiplyScalar(Math.sin(elev)));
dirToCam.normalize();
const dist = 4.5 + 0.5*Math.sin(t*0.053);
camera.position.copy(dirToCam.multiplyScalar(dist));
camera.lookAt(0,0,0);
```
Hmm, but the camera should maybe look slightly off-center for a nicer composition. Let's keep looking at the origin, maybe with a small offset toward the moon. Keep simple.

Wait: there's an issue with the ring tilt and the camera elevation — the rings might be seen edge-on or from a nice angle. The group is tilted 23.5° around Z, and the camera's elevation oscillates ±0.22 rad (12.6°), plus the offset angle of ~35° from the anti-sun... The ring plane's normal in world = the group's Y rotated by 23.5° about Z → the normal is tilted 23.5° from the world Y, in the XZ plane. The camera's elevation relative to the ring plane: dirToCam · ringNormal. The camera is at direction camBase (~ -sunDir = (-0.55,-0.30,-0.78) normalized) with a lateral offset. sunDir = (0.55,0.30,0.78) normalized → let's compute sunDir normalized: length = sqrt(0.3025+0.09+0.6084)= sqrt(1.0009)=1.0. Nice. So camBase = (-0.55,-0.30,-0.78). The ring normal ≈ (sin23.5°, cos23.5°, 0) rotated... The group rotation is around Z by 23.5°, so the Y axis becomes (-sin23.5, cos23.5, 0) = (-0.399, 0.917, 0). Dot with camBase = 0.219 - 0.275 = -0.056. That's nearly edge-on to the rings! Bad — the rings would be seen edge-on.

I need the camera to be well above or below the ring plane. Options: tilt the rings more, or change the sun direction, or add elevation to the camera.

Let's increase the camera's elevation: the camera at elevation ~+35° above the ring plane would give a nice view. Currently the elevation relative to the world Y is: camBase has y=-0.30 → -17.5° (below the equator). And the ring plane is tilted 23.5°.

Let me instead pick a sun direction with a higher y, e.g. sunDir = (0.55, 0.62, 0.56) normalized? That would put the camera below... Let's think again: the camera is roughly opposite the sun, so its y ≈ -sunDir.y. If sunDir.y = -0.35, then camBase.y = +0.35 → the camera is above the equator by 20°. And the ring plane is tilted by 23.5° around Z: its normal is (-sin23.5, cos23.5, 0). The camera direction (with the lateral offsets) — let's just pick sunDir = (0.62, -0.35, 0.70), normalized: length = sqrt(0.384+0.1225+0.49)= sqrt(0.9965)=0.998 ≈ 1. Good. So camBase = (-0.62, 0.35, -0.70) → normalized already.

Dot with the ring normal (-0.399, 0.917, 0) = 0.247 + 0.321 = 0.568 → 34.6° above the ring plane. 

But wait: the sun is now below the equator; the north pole faces... it's fine, it's an alien planet.

Also, the lateral offset (right vector) will change the elevation somewhat. right = cross(up, camBase).normalize(): up=(0,1,0), camBase=(-0.62,0.35,-0.70). cross(up, camBase) = (1*(-0.70) - 0*0.35, 0*(-0.62) - 0*(-0.70), 0*0.35 - 1*(-0.62)) = (-0.70, 0, 0.62). Normalized length = sqrt(0.49+0.3844)=0.935 → (-0.749, 0, 0.663). Dot with the ring normal (-0.399,0.917,0): 0.299. Hmm, the right vector also has a component along the ring normal, meaning rotating towards it changes the elevation somewhat. At off=0.62 rad, the camera dir = camBase*cos(0.62) + right*sin(0.62) = camBase*0.814 + right*0.581 → y = 0.35*0.814 + 0 = 0.285. And the ring-plane component: dot with the normal = 0.568*0.814 + 0.299*0.581 = 0.462+0.174=0.636 → 39.5° above the ring plane. Good, nice view.

Elevation oscillation ±0.22 rad adds upPerp = cross(camBase, right): camBase × right = |i j k; -0.62 0.35 -0.70; -0.749 0 0.663| = i(0.35*0.663 - (-0.70*0)) - j((-0.62*0.663) - (-0.70*-0.749)) + k(0 - 0.35*(-0.749)) = i(0.232) - j(-0.411 - 0.524) + k(0.262) = (0.232, 0.935, 0.262). Normalize: length = sqrt(0.054+0.874+0.069)=sqrt(0.997)=0.9985 → ≈ (0.232,0.936,0.262). That's mostly the world up. Good.

So the camera stays ~40° above the ring plane, oscillating ±12°. Good.

Sun direction final: `sunDir = new THREE.Vector3(0.62, -0.35, 0.70).normalize()`.

Hmm, but then the sun is at a negative y in the world, i.e., "below" the world's equator. It doesn't matter visually, but the overlay flare computed by projecting the sun point: sunDir*500 = (310, -175, 350) — it will appear in the frame when the camera is roughly facing it. OK.

Now, the camera is at camBase (anti-sun) + 35° offset — wait, off = 0.62 rad = 35.5°, and the FOV horizontal half-angle ~43° — so the sun (which is at exactly 180° from camBase, i.e., at the offset angle from the view axis) — let me recompute. camDir (from origin to camera) = normalized combination. The view axis direction = -camDir. The sun direction from the planet = sunDir = -camBase. The angle between the view axis (-camDir) and sunDir (-camBase) equals the angle between camDir and camBase, which is the lateral offset in the construction: cos(angle) = cos(off)*cos(elev) → the angle ≈ 35.5° (at elev=0). Half-FOV horizontal = 43° (for aspect 1.78) and vertical 27.5°. So the sun is 35.5° off-axis: within the horizontal FOV if it's roughly horizontal offset. The offset direction is along `right`, which is horizontal (y=0 for the right vector? we computed right = (-0.749, 0, 0.663), y=0 → yes horizontal in world, but is it horizontal in the camera's frame? The camera's up is roughly world up, so a horizontal offset is mostly a horizontal screen offset. Yes roughly. So the sun will be visible near the left/right edge of the frame. 

With off oscillating between 0.34 and 0.90 rad (19.5° to 51.6°), sometimes the sun is well inside the frame, sometimes just outside with the glow spilling in. 

Now the flare overlay: I'll compute the sun's NDC and place things.

One more: the starfield should be dense and visible everywhere, so make the stars not too dim.

Let's write the final code.

Additional detail: the moon's shadow should be visible. The camera is on the anti-sun side, so when the moon is between the planet and the sun, the shadow is on the far side of the planet as seen from... no wait. The sun is behind the camera (roughly), so the planet's lit face is toward the camera, and the moon crossing between the planet and the sun casts a shadow on the near face. But the moon itself would be between the camera and the planet (transit). Yes, visible. 

Hmm, but actually the moon at θ=90° is at position S2*2.35, which is in the direction of the sun from the planet — the sun direction is away from the camera, so the moon is on the far side of the planet. The moon would be behind the planet as seen from the camera. So we'd see the moon disappearing behind the planet, not a transit. And the shadow would be on the far side (invisible). 

Ugh. Right: the camera is on the anti-sun side, so the moon between the planet and the sun is behind the planet. So the eclipse shadow is not visible.

To see the moon transit and the shadow, the camera needs to be at a large angle from the anti-sun. Which conflicts with having a lit planet.

But we have the offset oscillating: at offset ~50°, the terminator region is visible, and the moon near the sun direction would be at the edge of the visible disk... Let's think geometrically: the moon is at the direction S2 (17° off the sun direction) from the planet. The camera is at direction camDir, which is off from the anti-sun by ~35-50°. The angle between camDir and S2 ≈ 180° - 40° ± 17° = 140° ± 17°. The moon at distance 2.35 from the planet: is it in front of or behind the planet's disk as seen from the camera? The angle between the moon's direction from the planet and the camera direction: if it's 140° (not 180°), the moon is off to the side, at an angular separation of 180-140 = 40° from the planet as seen from the camera... no wait.

Let me set up: the camera is at distance 4.5 in the direction camDir. The moon is at distance 2.35 in the direction S2. The angular separation between the moon and the planet as seen from the camera: compute the positions C = camDir*4.5, M = S2*2.35. The vector from the camera to the planet is -C; the vector from the camera to the moon is M - C. The angle between them: |M-C| = sqrt(2.35² + 4.5² - 2*2.35*4.5*cos(140°)) = sqrt(5.52+20.25 - 21.15*(-0.766)) = sqrt(25.77+16.2)= sqrt(41.97)=6.48. The angular separation: sin(angle) = |C × M| / (|C||M-C|) = (2.35*4.5*sin140°)/(4.5*6.48) = (2.35*0.643)/6.48 = 1.511/6.48 = 0.233 → 13.5°. So the moon appears 13.5° away from the planet's center. The planet's angular radius from the camera: the planet's radius 1 at a distance of ~4.5 → 12.8°. So the moon is just at the limb — around the edge of the planet's disk. Interesting.

But the moon's shadow: the shadow falls on the planet at the point where the line from the sun through the moon intersects the planet. Since the moon is 17° off the sun direction at distance 2.35, the shadow lands at a distance of about tan(17°)*2.35 ≈ 0.72 from the planet's center in the direction... yes, on the planet's disk, at 0.72 of the radius. And the sun direction is 180°-40° away from the camera, so the shadow is in the region of the planet facing the sun, which is toward the far limb from the camera. The planet's visible face is centered on the point closest to the camera. The shadow at 0.72 radius in the direction of the sun-lit... hmm. The sub-solar point is at 40° from the visible center. The shadow is 17° away from the sub-solar point (toward the moon's offset direction). So the shadow is at ~40±17° from the visible center → at the limb or slightly beyond. Hmm, marginal.

To make the shadow clearly visible, I want the camera to be more toward the anti-sun (smaller offset, e.g., 20°) so the sub-solar point is near the visible center, and the moon's shadow at 17° from it is well within the disk. But then the moon (at 13.5° from the planet's center as seen from the camera) would be in front of the planet — a transit! Great, but the transit becomes a transit only if the moon is between the camera and the planet.

Actually if the camera is at a 20° offset from the anti-sun, then the angle between camDir and S2 ≈ 180-20 = 160°. The moon's apparent offset from the planet = 2.35*sin(160°)/|M-C| ; |M-C| = sqrt(5.52+20.25-21.15*(-0.94)) = sqrt(25.77+19.88)=6.76. sin = 2.35*0.342/6.76 = 0.119 → 6.8°. The planet's angular radius is 12.8°, so the moon appears inside the planet's disk → transit! And the shadow is at ~17° from the sub-solar point which is 20° from the visible center → hmm, the shadow is at 20-17=3° to 37° from the center. Partially visible.

But wait — if the moon is in front of the planet (transit), the shadow on the planet is not visible because it's behind the moon... no, the shadow is at a different location on the planet than the moon's silhouette? The moon's silhouette as seen from the camera is at ~7° from the planet's center in one direction, and the shadow is at ~3-37° from the center. Actually if the moon is between the camera and the planet, its shadow is cast on the planet exactly where we see the moon's silhouette (approximately, since the camera-sun angle is 20° which is not negligible — parallax). Hmm, it's fine either way.

OK, I'm overthinking. The important things: a nice eclipse shadow effect visible on the planet during the recording, and a moon that looks good. Let me tune the camera offset so that at the eclipse time the shadow is visible. But the camera offset oscillates at its own rate, so the alignment varies.

Simplest robust approach: make the moon's orbital plane such that the shadow is well-placed, and accept whatever the geometry gives. The shadow will be visible for a portion of the orbit regardless, crossing the planet's surface.

Actually, let me reconsider: it'd be simpler and more reliable to have the moon orbit in a plane roughly perpendicular to the sun direction (like a "polar" orbit relative to the sun), so the moon passes in front of and behind the planet regularly... Hmm, no.

Let me think about what looks good: the moon orbiting around the planet, dipping in front of and behind the planet, with the eclipse shadow sweeping across the planet's surface. Given the camera is near the anti-sun, the moon at the sun direction side is behind the planet. The shadow falls on the far side (the lit side facing away from camera) — visible only near the limb. Hmm.

Alternative: make the eclipse happen when the moon is at the anti-sun position? No, that's not an eclipse.

Alternative approach: make the planet's shadow fall on the moon (the moon enters the planet's shadow and goes dark). That's also "shadow interest" and it's visible from the anti-sun side! When the moon is at the anti-sun direction (θ=-90°), it's behind the planet from the camera's viewpoint... no, at the anti-sun direction from the planet, the moon is on the same side as the camera (roughly), so it's between the camera and the planet → a transit, and the planet's shadow falls on the moon → we see the moon darkened during transit.

Hmm, that's nice too: the moon transits across the planet's disk and gets eclipsed (dark) as it crosses the planet's shadow. 

And that's achievable with an orbit plane containing the sun direction.

So: at θ=90° (moon toward the sun), the moon is behind the planet (hidden), and its shadow sweeps the far side of the planet. At θ=270° (moon toward the anti-sun), the moon is in front of the planet (transit) and gets eclipsed by the planet's shadow.

Given the camera offset is ~20-50° from the anti-sun, both are partially visible.

To make the shadow on the planet visible, I need the offset to be smallish at the eclipse time. Let me pick the timing: set the eclipse (θ=90°) to occur at t≈10s, and set the camera offset to be at its minimum around then. off = 0.62 + 0.28*sin(t*0.11) → the minimum (0.34 rad = 19.5°) occurs when sin = -1, i.e., t*0.11 = -π/2 + 2πk → t = 14.3, 71.4... So at t=10, off = 0.62+0.28*sin(1.1)=0.62+0.25=0.87 rad (50°). Bad.

Let me phase it: off = 0.62 + 0.28*sin(t*0.11 + φ), choose φ so that the minimum is at t=10: 1.1 + φ = -1.5708 → φ = -2.67. Then off(t) = 0.62 + 0.28*sin(0.11t - 2.67). At t=0: 0.62+0.28*sin(-2.67)=0.62+0.28*(-0.454)=0.49 rad. At t=10: 0.34 rad (19.5°) — the eclipse with the shadow near the disk center. 

Then the camera offset grows again: at t=20: 0.62+0.28*sin(2.2-2.67)=0.62+0.28*(-0.454)=0.49. At t=30: 0.62+0.28*sin(3.3-2.67)=0.62+0.28*0.589=0.78. OK.

So around t=10s we get the eclipse with a good viewing angle. The moon's shadow will sweep across the planet's disk around t=8-12s. 

Also the moon's transit with the planet's shadow around t = 10 + 12 = 22s (half period later at θ=270°). At t=22, off = 0.62+0.28*sin(2.42-2.67)=0.62+0.28*(-0.247)=0.55 rad (31.5°). The moon transiting in front of the planet at a 31° phase — the moon's apparent position vs the planet: the angle between camDir and the anti-sun direction S2' = -S2 → 180-31.5 = 148.5°, the moon at 2.35 → sin(148.5°)=0.522, |M-C| = sqrt(5.52+20.25-21.15*cos148.5°)= sqrt(25.77+18.03)=6.62. The moon's offset = 2.35*0.522/6.62 = 0.185 → 10.7° from the planet's center; the planet's angular radius is 12.8° → the moon is in front of the disk. Transit visible. 

But the eclipse of the moon by the planet's shadow: the moon at θ=270° is at -S2*2.35, which is 17° off the anti-sun direction; the planet's shadow is a cone along the sun direction behind the planet. For the moon to be in the shadow, the moon must be within the planet's shadow cylinder radius (1) at distance 2.35 behind the planet: the perpendicular distance from the sun axis = 2.35*sin(17°) = 0.687 < 1. Yes! So the moon is in the planet's shadow → dark. 

So the moon will be darkened while transiting in front of the planet. Nice, visible shadow interest.

Also at θ=90°, the moon is at 2.35*S2, perpendicular distance from the sun axis = 0.687 → the shadow it casts on the planet is at 0.687 from the center. With the camera at ~20° offset, the sub-solar point is 20° from the visible center → on the disk at a radius sin(20°)=0.34 in the direction of the sun. The shadow at 0.687 in the direction of S2's perpendicular component... the direction of the offset from the sun axis. Whatever, the shadow will be somewhere on the upper part of the disk. Visible. Good.

Great, this all works out.

Let me finalize sunDir = (0.62, -0.35, 0.70).normalized. Hmm wait, with sunDir.y negative, the north pole (tilted 23.5° about Z → toward -X) — the ice cap at the north pole would be facing away-ish from the sun. It's fine.

Actually, let me reconsider the sun's y to make the lighting prettier: the terminator and the ice caps. Sure.

Also I want to double check the camera elevation relative to the ring plane with camBase = -sunDir = (-0.62, 0.35, -0.70) (normalized already, since |sunDir|=1). We computed ~39° above the ring plane at off=0.62. Good.

Now let's write the final code. I'll be careful with the GLSL.

One thing about the overlay: since I use `renderer.autoClear = false` and manually clear, and the overlay renders after — need to make sure the depth buffer from the main scene doesn't block the overlay. I'll use `depthTest: false` on the overlay materials, and I'll set the overlay scene's meshes to render with depthTest false. Also, the overlay camera is ortho and the meshes are at z=0 with the camera at z=1 → within the near/far. With depthTest false, fine.

Let me write out the overlay ghost creation.

```js
const flareGroup = new THREE.Group();
overlayScene.add(flareGroup);

const quadGeo = new THREE.PlaneGeometry(1,1);
function makeFlare(color, power, intensity){
  const mat = new THREE.ShaderMaterial({
    uniforms: { uColor: {value: new THREE.Color(color)}, uIntensity: {value: intensity}, uPower: {value: power} },
    vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
    fragmentShader: `varying vec2 vUv; uniform vec3 uColor; uniform float uIntensity; uniform float uPower;
      void main(){ float d = length(vUv-0.5)*2.0; float a = pow(max(0.0,1.0-d), uPower); gl_FragColor = vec4(uColor*a*uIntensity, a); }`,
    transparent: true, blending: THREE.AdditiveBlending, depthTest: false, depthWrite: false
  });
  const m = new THREE.Mesh(quadGeo, mat);
  return m;
}
```
Then define the flare elements with their offsets/sizes/colors:
```js
const flareElements = [
  {k: 0, sx: 0.10, sy: 0.10, color: 0xfff4e0, power: 2.0, intensity: 1.6},   // core
  {k: 0, sx: 0.32, sy: 0.32, color: 0xffd9a0, power: 3.5, intensity: 0.9},   // halo
  {k: 0, sx: 1.6, sy: 0.012, color: 0xffe9c0, power: 1.6, intensity: 0.7},   // horizontal streak
  {k: 0, sx: 0.012, sy: 0.5, color: 0xcfe4ff, power: 1.6, intensity: 0.35},  // vertical streak
  // ghosts
  {k: 0.45, sx: 0.05, sy: 0.05, color: 0x88ffd0, power: 2.5, intensity: 0.5},
  {k: 0.72, sx: 0.09, sy: 0.09, color: 0xff8866, power: 2.0, intensity: 0.35},
  {k: 1.05, sx: 0.13, sy: 0.13, color: 0x66aaff, power: 2.5, intensity: 0.3},
  {k: 1.4, sx: 0.06, sy: 0.06, color: 0xffcc55, power: 2.0, intensity: 0.4},
  {k: 1.8, sx: 0.18, sy: 0.18, color: 0xaa77ff, power: 3.0, intensity: 0.22},
];
```
Where `k` is the ghost factor: position = -ndc * k (so k=0 means at the sun).

Wait, the core/halo/streak at k=0 are at the sun's position; the ghosts at k>0 are at -ndc*k.

Position in the overlay: x = ndcX*aspect, y = ndcY. Since the ortho camera has left=-aspect, right=aspect, top=1, bottom=-1, the world position corresponding to NDC (x,y) is (x*aspect, y). Good.

Sizes: the mesh scale in world units. The screen height is 2 world units, so a size of 0.10 = 5% of the screen height. The core at 0.10 is a small dot; that's good for a distant sun. The halo 0.32 is fairly big. OK.

The streak sx=1.6 spans 1.6 world units = 80% of the screen height... in world x, the screen width is 2*aspect ≈ 3.56, so 1.6 is 45% of the width. Fine.

Intensity: with additive blending, the color * a * intensity. The core at intensity 1.6 with a bright warm color → it'll blow out to white. Good.

Also need to make the whole flare group fade when the sun is off-screen or behind. Compute the sun's NDC; if camSpace.z > 0 (behind the camera), hide. Also fade based on... Actually if the sun is off-screen, the quads are off-screen too, which is automatic. But when the sun is far off-screen, the ghosts fly off-screen too. When the sun is just at the frame edge, the glow spills in. 

Let's also fade the overall intensity when the sun is near the center and behind the planet — overkill, skip.

Also handle: the projected position when the point is behind the camera gives garbage NDC — hide the group then.

Let's also add a subtle bloom-ish overall screen glow? No.

Now let's also double check the sun's position relative to the starfield: the stars are drawn in the main scene at radius 700-900; the sun isn't in the 3D scene. The flare overlay will show it. Fine.

Now, the renderer's clear color: black.

Let's write the code now.

Also, the planet's spin: planetMesh.rotation.y += dt*0.03? Use `planetMesh.rotation.y = t*0.035` for deterministic motion (nice for looping). And the clouds: clouds.rotation.y = t*0.05 (faster than the planet) — this makes the clouds drift relative to the surface. Good. Actually clouds usually move slightly faster than the surface; fine.

Use the absolute time for everything so it's deterministic.

The moon: θ = θ0 + 2π*t/period.

Now, careful: `planetMesh.rotation.y = t*0.035` — the planet's object space rotates. Since the noise is in object space, the terrain rotates with it. Good.

Now writing the vertex/fragment shaders.

Let me write the planet fragment shader fully:

```glsl
precision highp float;

varying vec3 vObjPos;
varying vec3 vWorldNormal;
varying vec3 vWorldPos;

uniform vec3 uSunDirWorld;
uniform vec3 uSunDirObj;
uniform vec3 uMoonPosObj;
uniform float uMoonRadius;
uniform float uTime;

// NOISE...

void main(){
  vec3 p = normalize(vObjPos);
  vec3 N = normalize(vWorldNormal);
  vec3 V = normalize(cameraPosition - vWorldPos);
  vec3 L = normalize(uSunDirWorld);

  // --- terrain height field ---
  float w = fbm(p*2.2 + 5.0);
  float cont = fbm(p*1.6 + w*0.7);
  float detail = fbm(p*7.0 + 11.0);
  cont *= 1.35;

  float landMask = smoothstep(-0.02, 0.06, cont);

  // ocean
  vec3 deep = vec3(0.01, 0.05, 0.15);
  vec3 shallow = vec3(0.03, 0.25, 0.42);
  vec3 ocean = mix(deep, shallow, smoothstep(-0.55, -0.02, cont));

  // land
  float elev = cont + detail*0.10;
  vec3 cSand  = vec3(0.60, 0.54, 0.37);
  vec3 cGrass = vec3(0.17, 0.36, 0.15);
  vec3 cForest= vec3(0.06, 0.19, 0.09);
  vec3 cRock  = vec3(0.34, 0.29, 0.25);
  vec3 cSnow  = vec3(0.90, 0.93, 0.97);
  vec3 land = mix(cSand, cGrass, smoothstep(0.0, 0.07, elev));
  land = mix(land, cForest, smoothstep(0.07, 0.24, elev));
  land = mix(land, cRock, smoothstep(0.26, 0.42, elev));
  land = mix(land, cSnow, smoothstep(0.42, 0.60, elev));

  vec3 albedo = mix(ocean, land, landMask);

  // ice caps
  float iceN = fbm(p*3.5 + 31.0)*0.12;
  float ice = smoothstep(0.62 + iceN, 0.78 + iceN, abs(p.y));
  albedo = mix(albedo, vec3(0.86, 0.92, 0.98), ice);

  // --- lighting ---
  float ndl = dot(N, L);
  float diff = max(ndl, 0.0);

  // cloud shadows
  vec3 csp = normalize(vObjPos + uSunDirObj*0.045);
  float cd = fbm(csp*3.0 + uTime*0.01);
  diff *= 1.0 - 0.45*smoothstep(0.05, 0.45, cd);

  vec3 col = albedo * (0.03 + 1.05*diff);

  // specular (ocean)
  vec3 H = normalize(L + V);
  float spec = pow(max(dot(N,H),0.0), 90.0) * (1.0-landMask) * (1.0-ice) * 1.2;
  spec *= smoothstep(0.0, 0.2, ndl);
  col += vec3(spec) * vec3(1.0, 0.97, 0.9);

  // atmospheric rim on the planet
  float fres = pow(1.0 - max(dot(N,V), 0.0), 3.0);
  col += vec3(0.25, 0.5, 1.0) * fres * (0.12 + 0.9*diff) * 0.65;

  // moon shadow (eclipse)
  vec3 rel = uMoonPosObj - vObjPos;
  float tAlong = dot(rel, uSunDirObj);
  float shadow = 0.0;
  if (tAlong > 0.0) {
    float dPerp = length(rel - tAlong*uSunDirObj);
    shadow = smoothstep(uMoonRadius*1.6, uMoonRadius*0.6, dPerp) * smoothstep(0.0, 0.3, tAlong);
  }
  col *= 1.0 - 0.85*shadow;

  gl_FragColor = vec4(col, 1.0);
}
```

Hmm, `cont *= 1.35` after computing detail — I use cont for the ocean depth. Fine.

Note: fbm(p*1.6 + w*0.7) — `w*0.7` is a float added to a vec3; in GLSL, `vec3 + float` is allowed. Yes.

But note that p*1.6 + w*0.7 shifts all components equally, which is a valid domain warp (the noise field is shifted). Good.

The `fbm(p*2.2 + 5.0)` → vec3 + float, fine.

Now the cloud shader:

```glsl
varying vec3 vObjPos; varying vec3 vWorldNormal; varying vec3 vWorldPos;
uniform vec3 uSunDirWorld; uniform float uTime;
void main(){
  vec3 p = normalize(vObjPos);
  float n1 = fbm(p*3.2 + vec3(uTime*0.015));
  float n2 = fbm(p*7.0 - vec3(uTime*0.02));
  float d = n1*0.65 + n2*0.35;
  float a = smoothstep(0.03, 0.42, d);
  a *= 0.7 + 0.3*sin(p.y*7.0 + 1.0);
  a *= 0.85;
  vec3 N = normalize(vWorldNormal);
  float ndl = dot(N, normalize(uSunDirWorld));
  float light = smoothstep(-0.3, 0.45, ndl);
  vec3 cloudCol = mix(vec3(0.16,0.22,0.35), vec3(1.0,0.99,0.97), light);
  gl_FragColor = vec4(cloudCol, a);
}
```
Hmm, `fbm(p*3.2 + vec3(uTime*0.015))` — adding time to all 3 components shifts the noise field. That's fine as an evolution. But it makes the clouds shift in a weird way (translating through the noise field). Better: use a 4D-ish approach or just let the rotation of the cloud layer provide the motion, and add a slow variation by offsetting a different axis. Simple: `fbm(p*3.2 + vec3(0.0, 0.0, uTime*0.01))` — a slow drift. Fine.

Actually, the cloud layer rotates, which provides the motion. The shader evolution is a bonus. Keep a small time offset.

Note `uTime` in the cloud shader must be shared and updated.

Now, the moon's shader: similar, with fbm for crater-ish gray and the same lighting, plus the planet's eclipse shadow on the moon! That's a nice touch: compute whether the moon is in the planet's shadow. Since the moon is a separate mesh centered at its own position, I can compute in world space: the moon's shadow test: the vector from the moon to the sun; if the moon is behind the planet along the sun direction, and the perpendicular distance < planetRadius, it's shadowed. Pass the moon's world position and the planet's world position (origin) and the planet's radius.

In the moon's fragment shader:
```glsl
vec3 relP = -vWorldPos; // from the moon surface point toward the planet... 
```
Simpler: do it in JS and pass a uniform `uEclipse` (0..1). That's cleanest! Compute in JS: 
```js
const moonToPlanet = moon.position.clone().negate(); // planet at origin
const along = moonToPlanet.dot(sunDir); // negative if the moon is behind the planet relative to the sun
```
We want: the moon is in shadow if the vector from the moon toward the sun (-sunDir) points roughly toward the planet and the perpendicular distance < planet radius.

Let m = moon.position. The sun direction is sunDir (from the planet toward the sun, from origin). The moon is in shadow if dot(m, sunDir) < 0 (the moon is on the far side) and the perpendicular distance from the sun axis = |m - dot(m,sunDir)*sunDir| < 1.0 (with a soft edge).

```js
const along = m.dot(sunDir);
const perp = m.clone().addScaledVector(sunDir, -along).length();
let eclipse = 0;
if (along < 0) eclipse = 1 - smoothstep(0.85, 1.15, perp);
```
Then pass `uEclipse` to the moon shader and multiply the light by (1-0.92*eclipse).

That's nice: the moon goes dark and reddish (a "blood moon") — I can tint it slightly red using the atmosphere refraction: mix the shadowed color toward dark red. Nice touch.

The moon's fragment:
```glsl
vec3 p = normalize(vObjPos);
float n = fbm(p*4.0);
float craters = fbm(p*9.0 + 3.0);
vec3 base = mix(vec3(0.32,0.31,0.30), vec3(0.62,0.60,0.56), 0.5+0.5*n);
base *= 0.85 + 0.3*(0.5+0.5*craters);
float ndl = dot(N, L);
float diff = max(ndl, 0.0);
vec3 col = base * (0.02 + 1.1*diff);
// eclipse
col = mix(col, col*vec3(0.35,0.08,0.04) + vec3(0.01,0.0,0.0), uEclipse);
gl_FragColor = vec4(col,1.0);
```
Something like that. The eclipse makes it dark red.

OK, and the moon needs its own uniforms: uSunDirWorld, uEclipse.

Now let's write the whole file.

Also: renderer.setClearColor(0x000000, 1).

Also, add a `renderer.toneMapping`? Not needed.

Resize:
```js
function onResize(){
  const w = innerWidth, h = innerHeight;
  renderer.setSize(w,h);
  camera.aspect = w/h;
  camera.updateProjectionMatrix();
  const aspect = w/h;
  overlayCam.left = -aspect; overlayCam.right = aspect; overlayCam.top = 1; overlayCam.bottom = -1;
  overlayCam.updateProjectionMatrix();
}
```

Now, the main loop:

```js
function frame(now){
  requestAnimationFrame(frame);
  const t = now * 0.001;

  // --- camera drift ---
  ...

  // --- planet spin ---
  planetMesh.rotation.y = t * 0.035;
  cloudMesh.rotation.y = t * 0.055;

  // --- moon orbit ---
  const theta = MOON_THETA0 + 2*Math.PI*t/MOON_PERIOD;
  moon.position.copy(P).multiplyScalar(Math.cos(theta)*orbitR).addScaledVector(S2, Math.sin(theta)*orbitR);
  // moon spin (tidal lock)
  moon.rotation.y = theta; // not important

  scene.updateMatrixWorld(true);

  // --- uniforms ---
  const q = planetMesh.getWorldQuaternion(_q).invert();
  shared.uSunDirObj.value.copy(sunDir).applyQuaternion(q);
  shared.uMoonPosObj.value.copy(planetMesh.worldToLocal(_v.copy(moon.position)));
  shared.uTime.value = t;

  // eclipse
  const along = moon.position.dot(sunDir);
  const perp = _v2.copy(moon.position).addScaledVector(sunDir, -along).length();
  let ec = 0;
  if (along < 0) ec = 1 - smoothstep(0.8, 1.2, perp);
  moonUniforms.uEclipse.value = ec;

  renderer.clear();
  renderer.render(scene, camera);
  updateFlare();
  renderer.render(overlayScene, overlayCam);
}
```

Careful: `planetMesh.worldToLocal` mutates and returns the vector; using _v which I then read from — fine.

Wait, there's an issue: `planetMesh.worldToLocal(_v.copy(moon.position))` — _v is reused later? I use _v2 for the eclipse. Fine.

updateFlare:
```js
function updateFlare(){
  const sunWorld = _sun.copy(sunDir).multiplyScalar(600);
  const camSpace = _cs.copy(sunWorld).applyMatrix4(camera.matrixWorldInverse);
  const behind = camSpace.z > 0;
  const ndc = _ndc.copy(sunWorld).project(camera);
  flareGroup.visible = !behind;
  if (behind) return;
  const aspect = innerWidth/innerHeight;
  const x = ndc.x * aspect, y = ndc.y;
  for (const el of flareElements){
    const px = x * (1 - el.k*2); // hmm
  }
}
```
Ghost positions: screen point p, center c=0. A ghost at factor k is at c + (c - p)*k = -p*k. So px = -x*k, py = -y*k. Yes: `px = -x*k`, `py = -y*k`.

For k=0 that's (0,0)?? No — k=0 gives (0,0) which is the center, but I want the core at the sun's position p! Let me redo: the position = p + (c - p)*k = p(1-k) + c*k. For k=0 → p (the sun). For k=1 → c (the center). For k=1.5 → beyond the center. So position = p*(1-k). Yes! That's the standard: pos = p*(1-k). With k=1.5, pos = -0.5p. Good.

So `px = x*(1-k)`. For k=0 it's the sun's position. 

The sizes: I also want to scale down the ghosts. The size is just the mesh scale.

Set:
```js
el.mesh.position.set(x*(1-el.k), y*(1-el.k), 0);
el.mesh.scale.set(el.sx, el.sy, 1);
```

Now, should the flare intensity fade when the sun is behind the planet? Skip.

Let me also handle the case where the sun is behind the camera: camSpace.z > 0. Note: in camera space, the camera looks down -Z, so a point in front has z < 0. Good.

Now, about the "distant sun with lens-flare-like glow" — the flare elements are only in the overlay, and they will be visible when the sun is in/near the frame. At the start (t=0), off=0.49 rad = 28°, and the horizontal half-FOV is ~43° for a wide window. So the sun is on-screen at the start. 

Let me now assemble everything and be careful with the shader code.

One concern: `precision highp float;` — three.js adds precision automatically for ShaderMaterial? Yes, WebGLProgram prepends precision. Adding it again might cause a duplicate precision error? Actually, redeclaring precision is legal in GLSL ES (you can set the default precision multiple times). It's fine, but I'll omit it since three.js adds it.

Also, three.js's ShaderMaterial prepends a prefix with `attribute vec3 position;` etc. for the vertex shader and `uniform mat4 viewMatrix; uniform vec3 cameraPosition;` for the fragment shader. So `cameraPosition` is available. Good. And `modelMatrix`, `viewMatrix`, `projectionMatrix`, `normalMatrix`, and attributes `position`, `normal`, `uv` are available in custom shaders (three.js includes them in the prefix for ShaderMaterial... let me recall: for the vertex shader, three.js prepends a big prefix containing `#define`s, `uniform mat4 modelMatrix; uniform mat4 modelViewMatrix; uniform mat4 projectionMatrix; uniform mat4 viewMatrix; uniform mat3 normalMatrix; uniform vec3 cameraPosition; uniform bool isOrthographic; attribute vec3 position; attribute vec3 normal; attribute vec2 uv;` — yes, this is the standard prefix for ShaderMaterial. Good.

Now writing the noise GLSL carefully (Ashima simplex 3D). I'll write it correctly.

```glsl
vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 permute(vec4 x) { return mod289(((x*34.0)+1.0)*x); }
vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }
```

The snoise function as above. Let me write it correctly from memory:

```glsl
float snoise(vec3 v) {
  const vec2 C = vec2(1.0/6.0, 1.0/3.0);
  const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);

  vec3 i  = floor(v + dot(v, C.yyy));
  vec3 x0 = v - i + dot(i, C.xxx);

  vec3 g = step(x0.yzx, x0.xyz);
  vec3 l = 1.0 - g;
  vec3 i1 = min(g.xyz, l.zxy);
  vec3 i2 = max(g.xyz, l.zxy);

  vec3 x1 = x0 - i1 + C.xxx;
  vec3 x2 = x0 - i2 + C.yyy;
  vec3 x3 = x0 - D.yyy;

  i = mod289(i);
  vec4 p = permute(permute(permute(
             i.z + vec4(0.0, i1.z, i2.z, 1.0))
           + i.y + vec4(0.0, i1.y, i2.y, 1.0))
           + i.x + vec4(0.0, i1.x, i2.x, 1.0));

  float n_ = 0.142857142857;
  vec3 ns = n_ * D.wyz - D.xzx;

  vec4 j = p - 49.0 * floor(p * ns.z * ns.z);

  vec4 x_ = floor(j * ns.z);
  vec4 y_ = floor(j - 7.0 * x_);

  vec4 x = x_ * ns.x + ns.yyyy;
  vec4 y = y_ * ns.x + ns.yyyy;
  vec4 h = 1.0 - abs(x) - abs(y);

  vec4 b0 = vec4(x.xy, y.xy);
  vec4 b1 = vec4(x.zw, y.zw);

  vec4 s0 = floor(b0)*2.0 + 1.0;
  vec4 s1 = floor(b1)*2.0 + 1.0;
  vec4 sh = -step(h, vec4(0.0));

  vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy;
  vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww;

  vec3 p0 = vec3(a0.xy, h.x);
  vec3 p1 = vec3(a0.zw, h.y);
  vec3 p2 = vec3(a1.xy, h.z);
  vec3 p3 = vec3(a1.zw, h.w);

  vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
  p0 *= norm.x;
  p1 *= norm.y;
  p2 *= norm.z;
  p3 *= norm.w;

  vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
  m = m * m;
  return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
}
```
Yes, this is correct.

Note: `mod289` overloaded for vec3 and vec4 — fine in GLSL.

Now, one issue: the planet shader uses `fbm` which uses snoise; the cloud shader and moon shader also. I'll just include NOISE_GLSL in each fragment shader that needs it.

Let's finalize the JS structure and write it out.

Also, I should double-check the `THREE.PointsMaterial` with `sizeAttenuation: false` and size in pixels — fine.

Star colors: I'll vary the color and brightness. Use additive blending for a nice glow against black.

Let me write:

```js
const starCount = 12000;
const sPos = new Float32Array(starCount*3);
const sCol = new Float32Array(starCount*3);
const c = new THREE.Color();
for (let i=0;i<starCount;i++){
  const u = Math.random()*2-1;
  const a = Math.random()*Math.PI*2;
  const s = Math.sqrt(1-u*u);
  const r = 600 + Math.random()*300;
  sPos[i*3] = Math.cos(a)*s*r;
  sPos[i*3+1] = u*r;
  sPos[i*3+2] = Math.sin(a)*s*r;
  const t = Math.random();
  const hue = 0.58 + (Math.random()-0.5)*0.22;
  const sat = 0.15 + Math.random()*0.5;
  const lum = 0.45 + Math.pow(Math.random(), 3.0)*0.55;
  c.setHSL(hue - Math.floor(hue), sat, lum);
  sCol[i*3]=c.r; sCol[i*3+1]=c.g; sCol[i*3+2]=c.b;
}
```
Hmm, `setHSL(hue, sat, lum)` with hue around 0.58 → blue. With sat 0.15-0.65. Lum 0.45-1.0.

Also, a few brighter stars: it's fine.

Star size: with additive blending, size 2.0px, and with DPR 2 it becomes 2 device px = 1 CSS px — small. Let me set size = 2.0 * renderer.getPixelRatio() so it looks consistent. Hmm, PointsMaterial with sizeAttenuation false: the size is in... For gl_PointSize, the size is in device pixels. So with DPR 2 and size 2, the star is 2 device pixels = 1 CSS px. To make it look the same across DPR, multiply by the pixel ratio. I'll do size: 2.0 * Math.min(devicePixelRatio, 2). Fine.

Also `alphaTest`? Not needed.

Now let's write the final code. I'll also add a subtle overall "sun glow" halo in the 3D scene? No.

Let me write out the whole file now.

For the vertex shaders, I'll define shared vertex shader strings.

planetVert:
```glsl
varying vec3 vObjPos;
varying vec3 vWorldNormal;
varying vec3 vWorldPos;
void main(){
  vObjPos = position;
  vec4 wp = modelMatrix * vec4(position, 1.0);
  vWorldPos = wp.xyz;
  vWorldNormal = normalize(mat3(modelMatrix) * normal);
  gl_Position = projectionMatrix * viewMatrix * wp;
}
```

Same for the clouds (a different mesh, same shader).

The moon: same vertex shader.

The ring: needs vObjPos and the world normal/pos. Same vertex shader works.

Now, the ring geometry: RingGeometry(1.45, 2.75, 256, 6) — the position.xy in the object space gives the radius. Good.

Also, the ring mesh's rotation: rotation.x = -Math.PI/2 makes the ring lie in the XZ plane; the ring's local +Y becomes the world -Z. The normal in the object space is (0,0,1) → after the rotation.x=-90°, the normal maps to (0,1,0) in the group's space. `mat3(modelMatrix)*normal` handles it. Good.

Now let me write out everything.

One more check on the camera: `camera.lookAt(0,0,0)` — but with the camera drifting, I want it to always look at the planet. Yes.

Actually, to add a bit more cinematic feel, I could offset the look-at point slightly toward the moon. Skip.

Potential issue: at t=0 the camera might be inside the rings? The camera distance is 4.5-5, the rings extend to 2.75. Fine.

Let me also double check the atmosphere's fresnel: for the BackSide sphere of radius 1.08, at the silhouette the normal is perpendicular to the view direction → dot(N,V) ≈ 0 → fres ≈ 1. At the center (facing the camera), the back faces we see are the ones on the far side of the sphere: at the center of the sphere's projection, the back face has a normal pointing away from the camera → dot(N,V) ≈ -1 → abs → 1 → fres = 0. Good, so the glow concentrates at the rim and is zero in the center. But in the center region, the planet occludes it anyway.

The additive color: col * fres * sunFade * 1.6.

Also, I want a slight extension of the glow beyond the planet's edge — yes, the atmosphere sphere is 8% larger, so the rim glow extends past the planet's silhouette. Good.

Let's write the final code.

One last thing: the `uTime` uniform for the cloud shader. And the cloud shadows in the planet shader use `fbm(csp*3.0 + uTime*0.01)` — since p is a vec3, `vec3 + float` works. Wait, in the planet shader I wrote `csp*3.0 + uTime*0.01`. Vec3 + float: allowed in GLSL ES 1.0? `vec3 + float` — yes, the scalar is promoted. Actually, GLSL allows binary operations between a vector and a scalar (the scalar is applied component-wise). Yes, that's valid.

Let me be careful about `fbm(p*2.2 + 5.0)` — vec3 + float is fine.

Alright, writing the file.

Also I should double check that `smoothstep` is used correctly with edges (edge0 < edge1). For `smoothstep(uMoonRadius*1.6, uMoonRadius*0.6, dPerp)` — edge0 > edge1, which is undefined behavior in GLSL spec? Actually, GLSL's smoothstep requires edge0 < edge1 for defined behavior; if edge0 > edge1, the result is undefined. Better to avoid: `1.0 - smoothstep(uMoonRadius*0.6, uMoonRadius*1.6, dPerp)`. Use that form.

Similarly, `smoothstep(0.78, 0.62, ...)` — avoid; use `1.0 - smoothstep(...)`.

Let me carefully write all smoothsteps with increasing edges.

Ice: `float ice = smoothstep(edge0, edge1, abs(p.y));` with edge0 = 0.62+iceN, edge1 = 0.78+iceN → increasing. Good.

Moon eclipse: `1.0 - smoothstep(0.8, 1.2, perp)`. Good.

Now writing.

Final code:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Alien Planet</title>
<style>
  html, body { margin:0; padding:0; width:100%; height:100%; overflow:hidden; background:#000; }
  canvas { display:block; width:100vw; height:100vh; }
</style>
<script type="importmap">
...
```
Wait — the prompt says "An import map is provided for you: do not add your own import map or any CDN URL." So I should NOT add an import map. The environment provides it. So I just use `import * as THREE from 'three'` and no import map in my file. Right — "do not add your own import map". So omit it. Good.

But then will `three/addons/...` work? I'm not using addons. Good.

Let me write the final file.

Actually, one thing: without an import map in my file, `import * as THREE from 'three'` relies on the provided import map. The instructions say it's provided. OK.

Writing it now.

```js
const shared = {
  uSunDirWorld: { value: sunDir },
  uSunDirObj: { value: new THREE.Vector3(0,0,1) },
  uMoonPosObj: { value: new THREE.Vector3(2,0,0) },
  uMoonRadius: { value: 0.16 },
  uTime: { value: 0 },
};
```
Then the planet material's uniforms: `{...shared}` — but careful: I want the planet material to have all of shared's uniforms; spreading gives the same uniform object references. Good.

For the clouds, sharing uSunDirWorld and uTime is fine (extra uniforms are harmless? Actually, unused uniforms in a material just don't get bound — no error). Fine, I'll spread shared into all.

Now the code for the moon material's uniforms: `{...shared, uEclipse: {value:0}}`.

Careful: `shared.uSunDirWorld.value` is the sunDir vector object; three.js uploads it as a vec3. Good.

Let me write everything out now, carefully.

Also `renderer.setAnimationLoop`? I'll use requestAnimationFrame directly since the requirement says to use the rAF timestamp.

Writing the final answer.

For the ghost flares, I need to store them in an array with the mesh and parameters.

```js
const flareDefs = [
  {k:0.0,  sx:0.085, sy:0.085, color:0xfff6e2, power:2.2, intensity:1.8},
  {k:0.0,  sx:0.30,  sy:0.30,  color:0xffdca8, power:4.0, intensity:0.55},
  {k:0.0,  sx:1.9,   sy:0.010, color:0xffeec8, power:1.8, intensity:0.55},
  {k:0.0,  sx:0.010, sy:0.55,  color:0xcfe0ff, power:1.8, intensity:0.28},
  {k:0.5,  sx:0.05,  sy:0.05,  color:0x7effc8, power:2.5, intensity:0.45},
  {k:0.78, sx:0.10,  sy:0.10,  color:0xff8a55, power:2.2, intensity:0.30},
  {k:1.12, sx:0.14,  sy:0.14,  color:0x5599ff, power:2.6, intensity:0.28},
  {k:1.5,  sx:0.06,  sy:0.06,  color:0xffcc55, power:2.0, intensity:0.35},
  {k:1.95, sx:0.20,  sy:0.20,  color:0xaa77ff, power:3.0, intensity:0.20},
];
```

Good.

Now, final assembly. Let me write it.

Also, need `const clock`? No, using the rAF timestamp.

Let me write the complete HTML.

One more detail: the moon's radius 0.16 with SphereGeometry(0.16, 48, 32) — fine.

The moon's `uEclipse` uniform.

For the moon's material, since it's a separate ShaderMaterial, I'll create it with its own uniforms object.

Let me write the moon's fragment:
```glsl
varying vec3 vObjPos; varying vec3 vWorldNormal; varying vec3 vWorldPos;
uniform vec3 uSunDirWorld; uniform float uEclipse; uniform float uTime;
// NOISE
void main(){
  vec3 p = normalize(vObjPos);
  vec3 N = normalize(vWorldNormal);
  vec3 V = normalize(cameraPosition - vWorldPos);
  vec3 L = normalize(uSunDirWorld);
  float n = fbm(p*3.5);
  float cr = fbm(p*11.0 + 7.0);
  vec3 base = mix(vec3(0.28,0.27,0.26), vec3(0.66,0.64,0.60), 0.5+0.5*n);
  base *= 0.85 + 0.3*(0.5+0.5*cr);
  float diff = max(dot(N,L), 0.0);
  vec3 col = base * (0.02 + 1.15*diff);
  float fres = pow(1.0 - max(dot(N,V),0.0), 4.0);
  col += vec3(0.4,0.6,1.0)*fres*0.08;
  // planet eclipse (blood moon)
  vec3 ec = col * vec3(0.5,0.12,0.06) + vec3(0.015,0.0,0.0);
  col = mix(col, ec, uEclipse);
  gl_FragColor = vec4(col, 1.0);
}
```

Good.

Now write it all out.

Let me double check the `planetMesh.worldToLocal` availability — Object3D.worldToLocal(vector) exists in three.js. Yes.

And `getWorldQuaternion(target)` exists. Yes.

Final: write the HTML.

Also, I should make sure the planet's terrain colors are visible: a diffuse of 1.05 * albedo.

Let me now also double check the initial camera position: at t=0, off = 0.62+0.28*sin(-2.67) = 0.62 - 0.127 = 0.493 rad. Good.

Writing now.

Wait, one thing about `uSunDirObj` for the cloud-shadow sampling in the planet shader: `normalize(vObjPos + uSunDirObj*0.045)` — vObjPos has length 1 (planet radius 1), and uSunDirObj is a unit vector in object space. Good.

Done thinking. Write the code.