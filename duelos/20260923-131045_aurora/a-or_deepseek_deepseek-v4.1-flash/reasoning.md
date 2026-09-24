Let me write a full-screen WebGL2 fragment shader with an aurora scene.

Plan:
- HTML with canvas full screen, WebGL2 context, resize handling.
- Vertex shader: full-screen triangle.
- Fragment shader: 
  - Sky gradient (dark blue/purple to near black at top).
  - Starfield: hash-based stars with a few brighter ones, twinkling subtly.
  - Aurora: layered curtains computed in screen space with domain warping. Use several layers: each layer has a horizontal position offset based on time and noise; curtain shape = height function based on x with folding. Vertical rays = high-frequency modulation in x combined with vertical falloff.
  - Mountains: silhouette via a few sine/noise-based ridge lines, dark.
  - Lake: bottom portion; reflect aurora by mirroring y coordinate about the horizon, with ripple distortion, and darken + desaturate slightly.

Let me carefully design.

Coordinates: uv in [0,1] with aspect correction: p = (uv*2-1) * vec2(aspect, 1.0)? Actually for a landscape, let's use p.x = (uv.x - 0.5) * aspect, p.y = uv.y (0 at bottom, 1 at top). Set aspect = resolution.x/resolution.y.

Horizon at y = 0.30 maybe. Lake from 0 to 0.30. Mountains silhouette around 0.28-0.40.

Actually let's set p.y = uv.y so 0 bottom, 1 top. Sky above horizon ~0.32.

Aurora: typically appears as curtains rising from horizon-ish upward. We'll compute aurora intensity field A(p) for sky region.

Aurora technique:
For each of N layers (say 4):
- offset phase
- Given world x = p.x, define a folded curtain: 
  Let's compute a "curtain coordinate" using noise-driven x displacement to create folds: 
  cx = p.x * 1.0 + noise(p.x*..., time)*0.5 etc. Folding means multiple curtain sheets overlapping — can be achieved with function like `f = fract(cx*scale + phase)` producing repeating sheets, but better: use a sine-based fold: `sheet = abs(sin(cx * k + t))` giving periodic bright ridges.

Common approach: aurora intensity = vertical falloff * (rays) where rays = pow(0.5+0.5*sin(x*freq + noise), power).

Let me structure:

```
float hash(vec2 p)
float noise(vec2 p)  // value noise
float fbm(vec2 p)
```

Aurora function:

```
vec3 aurora(vec2 p, float t) {
  vec3 col = vec3(0.0);
  // vertical mask: aurora occupies y from ~0.28 to 0.95
  float y = p.y;
  if (y < 0.25) return col; // early out? better keep smooth
  for (int i=0;i<3;i++){
     float fi = float(i);
     // curtain horizontal position shifts slowly with time
     float speed = 0.15 + fi*0.07;
     float x = p.x * (0.9 + fi*0.25) + t*speed + fi*7.3;
     // fold: displace by fbm
     float fold = fbm(vec2(x*0.6, t*0.12 + fi)) ;
     float xx = x + fold*1.6;
     // curtain envelope in x: broad gaussian-ish bands
     ...
  }
}
```

Hmm, maybe simpler and visually convincing: aurora drawn in screen space with ray structure.

Let me define per layer i:
- A center x curve: cx = centerX_i + amp * fbm(...) — the curtain wanders horizontally over time.
- Vertical extent: bottom at yb = horizon + something, top at yt.
- Brightness in x: gaussian around cx with width w. But curtains are extended horizontally, not blobs. So use a "band" that's broad but modulated by rays.

Alternative well-known approach: compute the aurora in a warped coordinate space where the curtain is vertical stripes.

Let's think of a curtain: for each x, there's a bottom y and top y; brightness strongest near bottom (or near a "grade line"). The curtain's vertical rays: brightness varies with x with high-frequency noise, elongated vertically (so noise is sampled with y scaled small: n(x*freq, y*0.1) → vertical streaks).

So:
```
float rays = fbm(vec2(warpx*3.0, y*0.4 + t*0.1));
```
Hmm, value noise with small y scaling gives vertical structures.

Let me write:

```
vec3 auroraLayer(vec2 p, float t, float seed, float scaleX, float speed) {
    float y = p.y;
    // warp x by low-frequency noise for folds
    float wx = p.x * scaleX + seed*13.0;
    float warp = fbm(vec2(wx*0.5 + seed, t*0.06));
    float fold = sin(wx*1.3 + warp*3.0 + t*speed)  ... 
}
```

Honestly, let me just build something and reason about visual quality.

Approach: define a function that returns aurora color for a sky point.

```
float auroraField(vec2 p, float t) {
    // p in aspect-corrected coords, y from 0 (bottom)
    float inten = 0.0;
    for (int i = 0; i < 4; i++) {
        float fi = float(i);
        float ph = fi * 17.31;
        // horizontal coordinate with drift and folding
        float x = p.x + fbm(vec2(p.x*0.8 + ph, t*0.05 + ph))*0.9 - 0.4;
        // curtain position: periodic sheets
        float sheets = 0.0;
        // multiple folds: use sin with noise-modulated phase
        float phase = x*2.2 + fbm(vec2(x*1.7 + ph, t*0.09))*3.0 + t*0.25;
        float s = sin(phase);
        // sheet brightness peaks near s = 1
        sheets = pow(max(s, 0.0), 6.0);
        // vertical profile: rises from bottom yb, fades toward top
        float yb = 0.20 + 0.05*sin(x*1.3 + t*0.2) ;  // curtain bottom height
        float yt = 0.95;
        float v = smoothstep(yb, yb+0.06, p.y) * (1.0 - smoothstep(yt-0.45, yt, p.y));
        // vertical rays: high freq in x, low variation in y
        float rays = 0.5 + 0.5*sin(x*40.0 + fbm(vec2(x*6.0, p.y*0.5))/1.0*6.0 + t*1.2);
        rays = pow(rays, 2.0);
        ...
    }
}
```

Rays: to make them vertical streaks, use noise: `float rays = fbm(vec2(x*18.0, p.y*1.2 - t*0.2));` with high x frequency and low y frequency gives vertical streaks that drift. Good.

Also add a bright bottom edge near yb.

Let's define ensure aurora is above the mountains mostly (y > 0.3).

Color: green (0.15, 1.0, 0.45) at bottom, violet (0.55, 0.25, 0.95) at higher altitude / in some regions. Mix based on y and noise.

Total: accumulate layers with different scales/speeds/seeds, additive.

Then background sky: gradient from dark blue at horizon to black at top, plus a subtle dark purple.

Stars: use a grid-based star function: for each cell, hash to get random position and brightness; star = smooth falloff. Twinkle with time.

```
vec3 stars(vec2 p, float t) {
  vec2 sp = p * 40.0; // grid
  vec2 id = floor(sp);
  vec2 f = fract(sp) - 0.5;
  vec3 c = vec3(0.0);
  for (int i=-1;i<=1;i++) for(int j=-1;j<=1;j++) {
     vec2 o = vec2(float(i), float(j));
     vec2 gid = id + o;
     float h = hash(gid);
     if (h > 0.94) { ... }
  }
}
```
But loop over 9 cells with per-pixel cost fine. Actually a single cell hash is enough if star is small; but stars near cell borders get clipped. Use 2x2 neighborhood maybe. Simpler: single cell, star radius small (0.06 in cell space), position randomized within cell 0.1..0.9 so it doesn't clip. Good.

Bright stars: a few with larger radius and cross flare.

Mountains: silhouette. Compute for x: mountain height h(x) = base + sum of ridge noise. Use fbm based on x with sharp peaks: `m = 0.30 + 0.06*fbm(vec2(p.x*1.5, 3.7))` etc. Also maybe two ranges with different colors (far range lighter/darker). Since night, mountains are near-black with slight blue. Far range slightly lighter (haze).

Snow: add a little snow highlight on top edges? "snowy mountains silhouetted" — silhouette implies dark. Maybe a faint rim light. Keep it dark with subtle blue and slight snow glints on the highest faces. Keep simple: silhouette near-black #0a0d18 with faint top rim from aurora glow.

Lake: below horizon y < horizonY. Reflection: mirror the sky point: reflected point pr = vec2(p.x + ripple, 2*horizonY - p.y). Compute the sky color at pr (aurora + stars + sky) and multiply by ~0.55, and darken/blue-tint. Ripples: distort x and y with noise based on time, magnitude increasing with distance from horizon? Actually water ripples: horizontal stretching.

For simplicity: in lake region, compute reflected coordinate y' = horizonY - (p.y - horizonY)... wait p.y < horizonY; reflection of the point at height p.y in the water corresponds to sky point at y = 2*horizonY - p.y, which is > horizonY. Good.

Add ripple: pr.x += 0.02*sin(p.y*120 + time) etc, and modulate amplitude. Actually vertical ripple distortion of y' gives the streaky look: y' += 0.005*noise(...). Horizontal displacement gives wobble.

Then combine: final color = lakeColor = reflection * 0.5 + deep water color (very dark blue) with fresnel-ish blend.

Also mountains should be reflected? That gets complex; we could just also compute the "scene" color function for the reflected point including mountains. Let's define a function `sceneColor(vec2 p, float t)` returning sky+mountains color, and use it for reflection. Mountains included → they'd reflect too, fine.

But careful about recursion: sceneColor doesn't call reflection. Good.

Actually clouds? Not required.

Let's structure code:

```
vec3 skyAndMountains(vec2 p, float t) {
   vec3 col = skyGradient(p);
   col += stars(p,t);
   col += aurora(p,t);
   // mountains: if p.y < mountainHeight -> mountain color
   float mh = mountainHeight(p.x);
   if (p.y < mh) col = mountainColor(p, mh, t);
   return col;
}
```

Then main:
```
if (p.y > horizon) col = skyAndMountains(p, t);
else {
   vec2 rp = vec2(p.x, 2.0*horizon - p.y);
   // ripple
   float d = (horizon - p.y);
   rp.x += ... ; rp.y += ...;
   vec3 refl = skyAndMountains(rp, t);
   col = mix(deepWater, refl * 0.6, ...);
}
```

Hmm but reflection should be attenuated and the aurora reflection brighter. Multiply by 0.7 and add slight blur by sampling multiple? To keep cost low, sample once, maybe 3 samples for a soft look. Let's do 3 samples with slightly offset ripple → gives shimmer. Cheap enough.

Also add a specular streak of aurora light on water near horizon.

Time budget: shader with fbm loops could be heavy. Let's keep fbm at 4 octaves and aurora layers at 3-4. Reflection samples scene 3 times → 3x cost. Might be heavy at 4K. Let's limit: do 2 samples for reflection. Or compute reflection with the aurora only (cheaper) plus sky. Hmm, simplest: 2 samples.

Actually, let's reduce: do 1 sample with ripple distortion — looks fine with added noise. I'll do 2 samples offset for slight blur, weighted.

Let's write noise functions:

```
float hash11(float p){ p = fract(p*0.1031); p *= p+33.33; p *= p+p; return fract(p); }
float hash21(vec2 p){ vec3 p3 = fract(vec3(p.xyx)*0.1031); p3 += dot(p3, p3.yzx+33.33); return fract((p3.x+p3.y)*p3.z); }
float hash22(vec2 p){...}
float vnoise(vec2 p){
  vec2 i = floor(p); vec2 f = fract(p);
  vec2 u = f*f*(3.0-2.0*f);
  float a = hash21(i), b = hash21(i+vec2(1,0)), c = hash21(i+vec2(0,1)), d = hash21(i+vec2(1,1));
  return mix(mix(a,b,u.x), mix(c,d,u.x), u.y);
}
float fbm(vec2 p){ float s=0.0, a=0.5; for(int i=0;i<5;i++){ s+=a*vnoise(p); p*=2.03; a*=0.5;} return s; }
```
5 octaves fbm called many times might be expensive. Use 4.

Now, aurora implementation details.

Let me write an aurora function producing both intensity and color:

```
vec3 aurora(vec2 p, float t) {
  vec3 col = vec3(0.0);
  float y = p.y;
  float horizonGlow = 0.0;
  for (int i=0;i<4;i++){
    float fi = float(i);
    float seed = fi*23.17;
    // drift & fold
    float x = p.x;
    float drift = t*(0.05 + 0.02*fi);
    // large scale warp creates the folded curtain shape
    float warp = fbm(vec2(x*0.7 + seed, t*0.07 + seed*0.3)) - 0.5; // -0.5..0.5
    float xw = x + warp*0.8;
    // curtain sheets: periodic in xw
    float k = 2.0 + 0.7*fi;
    float ph = xw*k + drift*2.0 + fbm(vec2(xw*1.3, t*0.13+seed))*2.5;
    float sheet = 0.5 + 0.5*sin(ph);
    sheet = pow(sheet, 5.0);
    // bottom edge of the curtain ~ y0, top fade
    float y0 = 0.30 + 0.10*(fbm(vec2(xw*1.1 + seed*2.0, t*0.1)) ) + 0.02*sin(ph);
    float top = 0.95;
    float v = smoothstep(y0, y0+0.02, y) * (1.0 - smoothstep(top-0.35, top, y));
    // vertical rays
    float rayCoord = xw*16.0 + fbm(vec2(xw*5.0, y*1.5 + t*0.3)) * 4.0;
    float rays = 0.5 + 0.5*sin(rayCoord + t*1.5);
    rays = pow(rays, 2.5);
    // combine
    float bright = sheet * v * (0.45 + 0.85*rays);
    // color: green low, violet high
    float h = clamp((y - y0) / 0.5, 0.0, 1.0);
    vec3 gcol = mix(vec3(0.15, 1.0, 0.42), vec3(0.35, 0.85, 0.75), h*0.6);
    vec3 vcol = vec3(0.65, 0.25, 1.0);
    vec3 c = mix(gcol, vcol, smoothstep(0.35, 0.9, h) * (0.55 + 0.45*sin(seed)));
    col += c * bright * (0.55/(1.0+fi*0.35));
    horizonGlow += bright * 0.04;
  }
  return col;
}
```

Hmm, many fbm calls per layer: warp (1 fbm), ph fbm (1), y0 fbm (1), rays fbm (1) = 4 fbm × 4 octaves × 4 layers = 64 noise evaluations per sky pixel. That's heavy but maybe okay at 1080p with GPU... could be slow. Let's reduce: 3 layers, fewer fbm calls.

Optimization: compute warp once outside the layer loop using fbm of (x, t) — shared. And compute per-layer cheaper things.

Let me restructure:

```
vec3 aurora(vec2 p, float t) {
  float y = p.y;
  float warp = fbm(vec2(p.x*0.6, t*0.06)) - 0.5;  // shared large-scale warp (1 fbm)
  vec3 col = vec3(0.0);
  for (int i=0;i<3;i++){
    float fi = float(i);
    float x = p.x + warp*(1.0 + fi*0.5) + fi*3.7;
    float sp = 0.15 + 0.06*fi;
    // sheet phase: uses sine + low-freq noise
    float n = vnoise(vec2(x*1.5 + fi*5.0, t*0.15));  // cheap: 1 noise
    float ph = x*(1.6+0.5*fi) + n*3.0 + t*sp*3.0;
    float sheet = pow(0.5+0.5*sin(ph), 6.0);
    ...
  }
}
```
Cost: per layer 1 vnoise + maybe 1 more for rays. Total ~2 noise per layer + 1 fbm(4 oct) shared. That's fine.

Rays: need high frequency in x, low frequency in y. `vnoise(vec2(x*20.0, y*1.0 - t*0.5))` — but vnoise with x*20 and y*1 gives stretched noise: features small in x, large in y → vertical streaks. Yes good.

rays = 0.4 + 0.9 * vnoise(vec2(x*18.0 + fi*3.0, y*1.2 - t*0.4));

Hmm, actually we want rays to be sharp vertical lines: use the noise as multiplier, plus another layer of fine sine.

Let me define:
```
float rn = vnoise(vec2(x*22.0, y*1.5 - t*0.6));
float rays = 0.35 + 1.3*pow(rn, 1.5);
```
Range 0.35..1.65ish. Fine.

Also the "sheet" gives horizontal bands which is not really right — aurora curtains viewed from the side have a bright lower edge and fade upward, and multiple folds create overlapping brightness. The folding comes from the warp. Additional periodic structure in x creates multiple curtains in the horizontal direction. Let's make sheet period larger: x*1.6 gives about 4 lobes across the screen width (since p.x ranges -aspect..aspect, ~4 units wide, so ~6 lobes at 1.6 rad/unit... sin period 2π/1.6 ≈ 3.9 units → about 1 lobe). Hmm: p.x range for aspect 1.78 is [-1.78, 1.78] = 3.56 units. With k=1.6, phase range = 5.7 rad → less than one full period. So we get one bank. Maybe k around 0.6 → phase range 2.1 → still less than a period. To get several folds, use k ≈ 3-5: phase range 11-18 rad → 2-3 folds. Good: k = 2.5 + fi.

Rather than pow(sin) which makes narrow bright bands separated by dark gaps — that's actually good for multiple curtain sheets.

Hmm, but sheets should be more like curtains with soft falloff. pow(sin, 6) gives sharp bright ridges. Aurora often has multiple parallel bright bands, so ok.

Let's also add a base glow: a broad envelope for the whole aurora zone so it isn't only narrow bands. E.g., an additional term: `glow = exp(-pow((y - 0.5)*3,2)) * 0.15 * (0.6+0.4*n)`.

Vertical falloff: for each layer, bottom y0 varies along x (curtain bottom edge drapes). Use y0 = 0.28 + 0.12*n2 where n2 = vnoise(vec2(x*1.2, t*0.08+fi)). And top fade: aurora fades at high y: fade = 1 - smoothstep(0.75, 1.0, y).

Then v = smoothstep(y0, y0+0.05, y) * fade.

Also, intensity should be strongest near the bottom edge: use exp(-(y-y0)*2.5) maybe. Combine: v = smoothstep(y0, y0+0.03, y) * exp(-(y-y0)*2.2) * fade.

Hmm, exp decay with the smoothstep gives bright bottom edge and vertical fade. Good — that plus rays gives the classic look.

Actually with rays modulated by y-dependent noise, the streaks will extend upward nicely.

Let's do:
```
float vprof = smoothstep(y0, y0 + 0.04, y) * exp(-max(y - y0, 0.0) * 2.0) * (1.0 - smoothstep(0.8, 1.05, y));
```
At y = y0+0.2: exp(-0.4)=0.67. At y0+0.5: exp(-1)=0.37. Decent.

Then brightness = vprof * sheet * rays * layerStrength.

Colors: green at bottom, violet higher: mix based on (y-y0).

Also add a slight teal/cyan.

Additionally, a big soft violet band higher up (some auroras have violet/purple diffuse).

Now the sky gradient:
```
vec3 sky = mix(vec3(0.02,0.03,0.07), vec3(0.01,0.012,0.03), smoothstep(0.3,1.0,y));
```
Plus horizon glow: a greenish glow near horizon from aurora: `sky += vec3(0.02,0.06,0.04)*exp(-(y-0.3)*6.0)` — that's near the horizon line.

Stars only above some y and fading near horizon.

Star function:
```
vec3 stars(vec2 p, float t) {
  vec3 c = vec3(0.0);
  vec2 sp = p * 26.0;   // scale so cells are ~1/26 in p units; p.x in -1.78..1.78, so ~92 cells across → many stars
  vec2 id = floor(sp);
  vec2 gv = fract(sp) - 0.5;
  float h = hash21(id);
  // star present if h > 0.9
  float rnd = hash21(id + 7.3);
  if (h > 0.88) {
     vec2 off = (vec2(hash21(id+1.1), hash21(id+3.7)) - 0.5)*0.7;
     float d = length(gv - off);
     float br = pow(hash21(id+5.5), 3.0);  // brightness distribution
     float tw = 0.8 + 0.2*sin(t*3.0 + h*50.0);
     float star = smoothstep(0.06, 0.0, d) * br;
     c += vec3(star) * tw;
  }
  return c;
}
```
Bright stars: separate pass with larger cells? Add a few bright ones by using a second grid with scale 6 and threshold >0.85, with cross flare.

Let's include a bright-star function:
```
vec3 brightStars(vec2 p, float t) {
  vec2 sp = p*5.0;
  vec2 id = floor(sp); vec2 gv = fract(sp)-0.5;
  float h = hash21(id+11.0);
  if (h > 0.9) {
     vec2 off = (vec2(hash21(id+1.0), hash21(id+2.0))-0.5)*0.6;
     vec2 d = gv - off;
     float dist = length(d);
     float tw = 0.75+0.25*sin(t*2.0 + h*100.0);
     float core = smoothstep(0.05,0.0,dist);
     float flare = smoothstep(0.35,0.0,abs(d.x))*smoothstep(0.02,0.0,abs(d.y))*0.5 + smoothstep(0.35,0.0,abs(d.y))*smoothstep(0.02,0.0,abs(d.x))*0.5;
     c += vec3(core + flare)*tw;
  }
}
```
Careful: 5.0 grid over p.x range 3.56 → ~18 cells, times 6 rows. ~100 cells with 10% → 10 bright stars. Fine. But conditionals with derivatives is fine here (no texture).

Note: `if (h > 0.9)` inside a shader is fine.

Mountains:

```
float mountainHeight(float x) {
  float h = 0.0;
  h += 0.06*fbm(vec2(x*0.9 + 3.0, 1.0));
  h += 0.05*fbm(vec2(x*2.5 + 10.0, 5.0));
  return 0.30 + h;  // horizon at 0.30
}
```
Wait, need peaks. fbm gives 0..1 roughly (sum a=0.5+0.25+... ≈ 0.94 for 4 octaves with amplitude halving: 0.5+0.25+0.125+0.0625=0.9375). Value noise returns 0..1, means 0.5. So fbm centered ~0.47.

Mountain: height above horizon = 0.03 + 0.09*fbm(...) + sharpness. Let's define:

```
float ridge(vec2 q) { ... }
float mh = horizon + 0.02 + 0.10*pow(fbm(vec2(p.x*0.8, 2.7)), 1.5) ... 
```

Simpler: 
```
float mount(vec2 p, float scale, float seed, float base, float amp) {
  float n = fbm(vec2(p.x*scale + seed, seed*3.0));
  return base + amp*n*n;  // peaks
}
```
Two ranges: far (lighter, lower) and near (darker, higher). Also add small variations.

For a nice silhouette I'll use:
```
float farH = 0.30 + 0.05 + 0.06*fbm(vec2(p.x*0.7 + 12.0, 3.0));  // gentle
float nearH = 0.28 + 0.10*pow(fbm(vec2(p.x*1.3 + 40.0, 8.0)), 1.3);
```
Hmm, both layered: draw far range first, then near range in front (darker). If p.y < nearH, use near color; else if p.y < farH, use far color. Since near is drawn in front, nearH should generally be lower on screen (smaller y) but with peaks can overlap. Just do: if (y < farH) col = farColor; if (y < nearH) col = nearColor. Near color darker.

Wait — silhouette means mountains are darker than sky. Since sky is dark too, mountains must be nearly black (0.01,0.015,0.03) to be seen against the aurora glow. When aurora is behind them, they'll be silhouetted. Good. And near range darker than far range. Add slight rim lighting from aurora: near the top of the mountain, add a faint glow.

Actually for "snowy mountains silhouetted", maybe hint snow patches: add a slight brightening at the very top edge: `col += vec3(0.1,0.12,0.16) * smoothstep(...)` for a snow rim. Might look nice. Let's add subtle: on far range, top edge slightly lighter (snow catching aurora light). Keep it subtle.

Also mountains must be below/at the horizon line (y=0.30) and the lake occupies y < 0.30.

Hmm, but the lake reflects mountains; if mountains rise above 0.30 and lake is below 0.30, reflection of mountains appears in water. Our sceneColor(rp) handles it.

But wait — the reflection plane: the water surface at y=0.30 reflects the sky above. Mountains at y between 0.30 and 0.40 would reflect to y between 0.20 and 0.30. Fine.

Lake details:
- Base color: very dark blue (0.01,0.02,0.04).
- Reflection: sky color at mirrored point, multiplied by 0.55 and desaturated slightly.
- Ripples: distort reflected coords.

```
vec3 lake(vec2 p, float t) {
  float d = horizon - p.y;   // >0
  vec2 rp;
  rp.y = horizon + d;  // mirrored
  // horizontal wobble increasing with distance? Actually ripples compress far away
  float rippleAmt = 0.02 * smoothstep(0.0, 0.15, d) ... 
  rp.x += 0.03*sin(d*60.0 + t*1.5 + p.x*3.0)*0.5;
  rp.y += 0.006*sin(p.x*40.0 + t*2.0)*smoothstep(0.0,0.1,d);
  ...
}
```
Ripple should be small near the horizon (far away) and larger near the bottom (close). Actually in a perspective view, waves far away compress. So amplitude increases with d (closer to viewer = lower on screen). Yes: amplitude ∝ d.

Also stretch the reflection: near the bottom, the reflected image covers a larger vertical range... Automatic from mirroring.

To make it look like water, add horizontal streaks: multiply reflection by a factor depending on a noise that's stretched horizontally.

Let's compute:
```
float w = fbm(vec2(p.x*8.0, p.y*40.0 + t*0.5));  // horizontal streaks
```
Hmm, fine.

Let's do 3 tap reflection with offsets for shimmer:
```
vec3 refl = vec3(0.0);
for (int i=0;i<3;i++){
  float di = float(i)-1.0;
  vec2 q = rp + vec2(di*0.012*(0.3+d*3.0), 0.0);
  refl += skyAndMountains(q, t);
}
refl /= 3.0;
```
Cost: 3× scene. Might be acceptable. Let's use 2 taps maybe. I'll go with 3 for quality but reduce aurora layers... Let's see: skyAndMountains includes aurora (3 layers, ~2 noise each + fbm shared) + stars (2 hash-grids) + sky. 3 taps → still fine on modern GPU at 1080p. Risky at 4K but let's not worry too much; could reduce taps to 2. I'll do 3 for the shimmer but let's compute aurora with the same shared warp — unavoidable cost.

Alternatively, I can reduce reflection taps to 2 and add procedural shimmer. Let me use 3; if slow, whatever, it's a demo.

Hmm, actually, a concern: recording window suggests performance matters. Let's use 2 taps and cheap extras. I'll go with 2.

Also brighten the water with a specular band near the horizon (the aurora reflected brightest just below horizon).

Let me also add: the water reflects the aurora more strongly than the sky (since aurora is bright). Just linear reflection works.

Fresnel: at grazing angles (near horizon) the reflection is stronger; near the viewer, the water is darker. So multiply reflection by smoothstep: `float refStrength = mix(0.85, 0.25, smoothstep(0.0,0.28,d))` — near horizon (d small) strong, at bottom weak. Actually d small = far = grazing = strong reflection. Yes.

Hmm wait, d = horizon - p.y; at p.y just below horizon, d≈0 → far away → grazing → strong reflection. At bottom of screen, d = 0.3 → near → weak. So refStrength = mix(0.9, 0.3, smoothstep(0.0, 0.3, d)). Good.

Now the overall composition: horizon at y=0.30 in normalized p.y where p.y = uv.y (0..1). Sky occupies 0..1 with mountains peaking around 0.30-0.45 and aurora between 0.35 and 0.95. That leaves a good chunk of sky. Good.

Wait, is the aurora visible enough? The curtain bottom y0 around 0.35-0.45, fading up to 1.0. Good.

Camera view: aspect correction only on x, so vertical FOV fixed. On a wide screen we see more horizontally — good.

Let's now write it.

Additional: subtle color grading, vignette, and slight tone mapping (col = 1 - exp(-col*1.2)) or pow. Let's use simple ACES-ish or just clamp with gamma. Since we're outputting linear-ish, apply `col = pow(col, vec3(0.85))`? Let's apply a soft tonemap: `col = col/(1+col)` might wash out. I'll do `col = 1.0 - exp(-col*1.35);` then gamma correct `pow(col, 1/2.2)`? That could brighten too much. Aurora values are around 1-2; tonemapping to 1-exp(-1.35*1)=0.74; then gamma → 0.87. Fine.

Actually careful: with the additive aurora the values won't be huge. Let's just do a mild filmic and keep it.

Let me write the code.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Aurora</title>
<style>
  html,body{margin:0;padding:0;height:100%;background:#000;overflow:hidden;}
  canvas{display:block;width:100vw;height:100vh;}
</style>
</head>
<body>
<canvas id="c"></canvas>
<script>
const canvas = document.getElementById('c');
const gl = canvas.getContext('webgl2', {antialias:false, alpha:false});
...
</script>
</body>
</html>
```

Vertex shader:
```glsl
#version 300 es
in vec2 aPos;
void main(){ gl_Position = vec4(aPos,0.0,1.0); }
```
Full-screen triangle: positions (-1,-1),(3,-1),(-1,3).

Fragment shader with `precision highp float;`.

Now write the fragment shader carefully.

```glsl
#version 300 es
precision highp float;

uniform vec2 uRes;
uniform float uTime;

out vec4 fragColor;

#define HORIZON 0.30

float hash21(vec2 p){
  p = fract(p * vec2(123.34, 456.21));
  p += dot(p, p + 45.32);
  return fract(p.x * p.y);
}

float vnoise(vec2 p){
  vec2 i = floor(p);
  vec2 f = fract(p);
  vec2 u = f*f*(3.0-2.0*f);
  float a = hash21(i);
  float b = hash21(i + vec2(1.0,0.0));
  float c = hash21(i + vec2(0.0,1.0));
  float d = hash21(i + vec2(1.0,1.0));
  return mix(mix(a,b,u.x), mix(c,d,u.x), u.y);
}

float fbm(vec2 p){
  float s = 0.0;
  float a = 0.5;
  for(int i=0;i<4;i++){
    s += a*vnoise(p);
    p = p*2.03 + 11.7;
    a *= 0.5;
  }
  return s;  // ~0..0.94
}
```

Aurora:

```glsl
vec3 aurora(vec2 p, float t){
  vec3 col = vec3(0.0);
  float y = p.y;
  float env = smoothstep(0.26, 0.40, y) * (1.0 - smoothstep(0.72, 1.05, y));
  // shared large-scale fold
  float warp = (fbm(vec2(p.x*0.55, t*0.05)) - 0.45) * 1.6;

  for(int i=0;i<3;i++){
    float fi = float(i);
    float x = p.x*1.0 + warp*(1.0 + fi*0.35) + fi*2.3;
    float sp = 0.5 + 0.35*fi;

    float n1 = vnoise(vec2(x*1.1 + fi*7.0, t*0.10 + fi*3.0));
    float n2 = vnoise(vec2(x*2.2 - fi*4.0, t*0.17 + fi*9.0));
    float n = n1*0.65 + n2*0.35;

    // curtain bottom edge
    float y0 = 0.33 + 0.13*n + 0.02*sin(x*3.0 + t*0.4);
    // vertical profile
    float vprof = smoothstep(y0, y0 + 0.03, y) * exp(-max(y-y0,0.0)*1.9);
    vprof *= (1.0 - smoothstep(0.80, 1.10, y));

    // multiple sheets/folds
    float ph = x*(2.0 + 1.3*fi) + n*3.6 + t*sp;
    float sheet = pow(0.5 + 0.5*sin(ph), 4.0);

    // vertical rays
    float rn = vnoise(vec2(x*14.0 + fi*5.0, y*1.6 - t*0.45));
    float rays = 0.30 + 1.6*pow(rn, 1.4);

    float bright = vprof * sheet * rays * (0.55/(1.0+fi*0.45));

    // color mixing
    float hh = clamp((y - y0)*2.2, 0.0, 1.0);
    vec3 green = vec3(0.12, 1.0, 0.38);
    vec3 teal  = vec3(0.25, 0.85, 0.70);
    vec3 viol  = vec3(0.55, 0.22, 1.0);
    vec3 c = mix(green, teal, smoothstep(0.15,0.55,hh));
    c = mix(c, viol, smoothstep(0.45,1.0,hh)*(0.55+0.45*sin(fi*2.1+0.7)));

    col += c * bright;
  }
  return col;
}
```

Wait: the ripple/fold should also affect the x-position, I do that via warp. But the sheets should look like they're waving across the sky. The `sheet` term uses sin(x*...) with the noise phase n. OK.

The rays: `vnoise(vec2(x*14.0, y*1.6 - t*0.45))` — with x scaled 14, features in x have period ~1/14 = 0.07 in p.x, and in y period ~0.6. So streaks 0.07 wide and long in y. Good.

But note: I should make rays coherent with the fold displacement — x here already includes warp, so yes.

Hmm, one problem: `sheet = pow(0.5+0.5*sin(ph), 4.0)` — with ph including t*sp, the sheets sweep. Good.

Also I want a bright lower edge to the curtain — vprof with smoothstep(y0, y0+0.03) gives a fairly quick rise but exp decay from y0. Combined, the max is right at y0+0.03. Reasonable.

Also add a broad diffuse glow:
```
float glow = exp(-pow((y-0.55)*2.6, 2.0)) * 0.10 * (0.5+0.5*vnoise(vec2(p.x*1.5, t*0.08)));
col += vec3(0.15,0.6,0.4)*glow;
```
Maybe add for a hazier overall sky.

Now the stars:

```glsl
vec3 starField(vec2 p, float t){
  vec3 c = vec3(0.0);
  // small stars
  vec2 sp = p*24.0;
  vec2 id = floor(sp);
  vec2 gv = fract(sp) - 0.5;
  float h = hash21(id + 3.1);
  if(h > 0.90){
    vec2 off = (vec2(hash21(id+1.7), hash21(id+8.3)) - 0.5)*0.72;
    float d = length(gv - off);
    float br = 0.35 + 0.65*hash21(id+4.9);
    float tw = 0.75 + 0.25*sin(t*2.5 + h*90.0);
    c += vec3(0.85,0.9,1.0) * smoothstep(0.055, 0.0, d) * br * tw;
  }
  // bright stars
  vec2 sp2 = p*4.5;
  vec2 id2 = floor(sp2);
  vec2 gv2 = fract(sp2) - 0.5;
  float h2 = hash21(id2 + 19.0);
  if(h2 > 0.92){
    vec2 off = (vec2(hash21(id2+2.3), hash21(id2+6.1)) - 0.5)*0.55;
    vec2 d = gv2 - off;
    float dist = length(d);
    float tw = 0.7 + 0.3*sin(t*1.7 + h2*60.0);
    float core = smoothstep(0.045, 0.0, dist);
    float fl = (smoothstep(0.30,0.0,abs(d.x))*smoothstep(0.012,0.0,abs(d.y))
              + smoothstep(0.30,0.0,abs(d.y))*smoothstep(0.012,0.0,abs(d.x)))*0.45;
    c += vec3(1.0,0.95,0.88)*(core+fl)*tw*1.2;
  }
  return c;
}
```
Then fade stars near horizon: multiply by smoothstep(HORIZON, HORIZON+0.15, p.y). And maybe reduce where aurora is bright (they'd be washed out) — optional; add a bit later maybe.

Mountains:

```glsl
float mountains(vec2 p, out float farH, out float nearH){
  farH = HORIZON + 0.015 + 0.075*fbm(vec2(p.x*0.65 + 21.0, 4.0));
  float n = fbm(vec2(p.x*1.35 + 61.0, 9.0));
  nearH = HORIZON - 0.01 + 0.085*n*n;
  ...
}
```
Hmm let's just compute inline in sceneColor.

```glsl
vec3 sceneColor(vec2 p, float t){
  vec3 col = skyGradient(p.y);
  // stars
  col += starField(p, t) * smoothstep(HORIZON-0.02, HORIZON+0.18, p.y);
  // aurora
  col += aurora(p, t);
  // mountains
  float farH  = HORIZON + 0.02 + 0.075*fbm(vec2(p.x*0.7 + 21.0, 3.0));
  float nearH = HORIZON - 0.005 + 0.10*pow(fbm(vec2(p.x*1.6 + 61.0, 9.0)), 1.6);
  if(p.y < farH){
     // far ridge
     float rim = smoothstep(farH - 0.012, farH, p.y);
     vec3 mc = vec3(0.020,0.028,0.048) + vec3(0.10,0.16,0.22)*rim*0.35;
     col = mc;
  }
  if(p.y < nearH){
     float rim = smoothstep(nearH - 0.010, nearH, p.y);
     vec3 mc = vec3(0.008,0.011,0.022) + vec3(0.06,0.10,0.16)*rim*0.25;
     col = mc;
  }
  return col;
}
```

Hmm, `col = mc` fully replaces including the aurora — that's what silhouetting means. Good.

Wait, but nearH can dip below HORIZON, meaning the near range is partially below the waterline — that's fine, it appears to be behind the lake, and the lake will cover it. Actually the lake region (p.y < HORIZON) uses reflection, so the mountains below HORIZON won't show except via reflection. Fine.

Actually, hold on: should the mountain base be exactly at horizon? A shoreline. Yes, nearH base at HORIZON means the near ridge starts at the waterline. I set nearH = HORIZON - 0.005 + 0.10*n^1.6, so min ~ -0.005 above... it can go slightly below horizon at the lowest, fine.

Now for snow: "snowy mountains silhouetted" — I'll add subtle rim light on the far range which reads as snow under aurora light.

Sky gradient:
```glsl
vec3 skyGradient(float y){
  vec3 top = vec3(0.004,0.006,0.020);
  vec3 bot = vec3(0.018,0.030,0.060);
  vec3 c = mix(bot, top, smoothstep(HORIZON, 1.0, y));
  // horizon glow (aurora light scatter)
  c += vec3(0.02,0.05,0.045)*exp(-max(y-HORIZON,0.0)*7.0);
  return c;
}
```

Water:

```glsl
vec3 water(vec2 p, float t){
  float d = HORIZON - p.y;      // 0 at horizon
  float depth = clamp(d/0.30, 0.0, 1.0);
  // reflection coords
  vec2 rp = vec2(p.x, HORIZON + d);
  float amp = mix(0.002, 0.030, depth);
  rp.x += amp*3.0*sin(d*45.0 + t*1.3 + p.x*4.0);
  rp.y += amp*1.2*sin(p.x*30.0 + t*2.1);
  vec3 refl = vec3(0.0);
  refl += sceneColor(rp + vec2(0.006*depth*8.0, 0.0), t);
  refl += sceneColor(rp - vec2(0.006*depth*8.0, 0.0), t);
  refl *= 0.5;

  float fres = mix(0.85, 0.35, smoothstep(0.0, 0.9, depth));
  vec3 deep = vec3(0.006,0.012,0.026);
  vec3 col = deep + refl * fres * 0.85;
  // horizontal shimmer streaks
  float sh = vnoise(vec2(p.x*22.0, p.y*90.0 + t*0.6));
  col += vec3(0.02,0.06,0.05)*sh*depth*0.35;
  // fade into the horizon (haze)
  col = mix(col, skyGradient(HORIZON)*0.9, smoothstep(0.06,0.0,d));
  return col;
}
```

Hmm, `mix(col, ..., smoothstep(0.06,0.0,d))` blends water into a haze right at the horizon line — avoids a hard aliased line. Maybe better to blend to the reflection brightness. Let's keep small.

Actually a hard horizon line is fine visually, but aliasing may occur. Use a slight smoothing: at d<0.004, blend toward the sky color at horizon. Let's do less: `smoothstep(0.012, 0.0, d)`.

Careful about reflection coordinates reaching above p.y>1? rp.y = HORIZON + d where d max 0.30 → rp.y max 0.60. Fine, no wrapping issues.

The lake region p.y from ~0.0 to 0.30 and mirrored to 0.30–0.60. Good, this includes the mountains reflection.

Now main:

```glsl
void main(){
  vec2 uv = gl_FragCoord.xy / uRes;
  float aspect = uRes.x / uRes.y;
  vec2 p = vec2((uv.x - 0.5)*aspect, uv.y);

  float t = uTime;

  vec3 col;
  if(p.y > HORIZON){
    col = sceneColor(p, t);
  } else {
    col = water(p, t);
  }

  // subtle vignette
  vec2 q = uv - 0.5;
  col *= 1.0 - 0.35*dot(q,q);

  // tonemap
  col = vec3(1.0) - exp(-col*1.25);
  col = pow(col, vec3(0.92));

  fragColor = vec4(col, 1.0);
}
```

Branching on p.y > HORIZON: in a fragment shader this is fine (uniform-ish branch, no derivatives used). But careful: I use `if (h > 0.90)` in starField which is fine.

Hmm, wait: p.x range is (uv.x-0.5)*aspect → [-aspect/2, aspect/2]. For aspect 1.78 → [-0.89, 0.89]. That's a narrow range; my noise scales assumed a wider range. Let me instead use p.x = (uv.x-0.5)*aspect*2.0 → [-1.78, 1.78]. Or just use uv.x-0.5 scaled. Let's use `vec2 p = vec2((uv.x-0.5)*aspect*2.0, uv.y);` giving p.x in roughly [-1.8, 1.8]. That's a total width of 3.56 units, so noise frequencies: x*14 for rays → 14*3.56 = 50 streaks across. Good, that's a lot... maybe too many. Actually rays at 14 rad per unit... noise period is 1 unit in the noise input, so x*14 means features every 1/14 = 0.071 p-units → across 3.56 units → 50 features. That's fine for fine rays.

Sheet: `x*(2.0+1.3i)` → for i=0, 2 rad/unit → period 2π/2 = 3.14 units → about 1 fold across the screen. Hmm, that's not many folds. Let's increase to 4-6. Use x*(3.5 + 1.5*fi) → period 2π/3.5 = 1.8 units → 2 folds. Hmm. Actually with all layers different, we get overlapping bands. Let's use k = 3.0 + 2.0*fi giving periods 2.1, 1.26, 0.9 → 1.7, 2.8, 4 folds respectively. Combined it looks rich. OK.

Also the fold warp gives the wavy shape.

Vertical profile: y0 between 0.33 and 0.48 (0.33 + 0.13*n), the curtain bottom edge waves along x. Good.

Let me reconsider exp decay: exp(-(y-y0)*1.9). At the top of the screen (y=1) with y0=0.4: exp(-1.14)=0.32. That's still substantial. Multiply by the top fade: (1-smoothstep(0.80,1.10,y)) which at y=1 is 1-smoothstep→ 1 - 0.74 = 0.26. Combined 0.08. OK, dims at the very top.

Overall brightness: need to tune. Let's set layer strength factors around 0.6-1.0 and see. Since I can't test, I'll make a reasonable guess and add a global scale.

Since I can't run it, I should be careful with parameters and use conservative values.

Let me estimate the aurora brightness: bright = vprof * sheet * rays * strength. At the brightest: vprof ≈ 1 (near y0+0.03), sheet ≈ 1 (at the peak of the sine), rays ≈ 0.3+1.6*~0.8 = 1.58. strength for layer 0 = 0.55. So bright ≈ 0.87. Color green (0.12,1.0,0.38) → contribution (0.10, 0.87, 0.33). That's already quite bright; after tonemapping (1-exp(-1.25*x)): green channel → 1-exp(-1.09)=0.66. Summing 3 layers could saturate to near white-ish green. Probably fine, aurora bright bands do saturate.

But average brightness matters — sheet^4 means only near the peaks. Point: good.

Hmm, but the visible curtain structure: pow(sin,4) gives bands of width... sin^4 > 0.5 when |sin| > 0.84, i.e., phase within ±0.57 rad of π/2 → band width 1.14 rad out of 2π = 18% duty. With period 2.1 units → band width 0.38 units. Reasonable.

Actually, I realize the "sheet" modulation with x and the rays with x create a mix. Fine.

Let me also make sure the aurora doesn't look like it's "under" the horizon — env smoothstep(0.26,0.40,y) kills it below y=0.26, and mountains cover up to ~0.4 anyway. OK, so the aurora only shows above the mountains. Good.

Now let's think about whether the aurora will be too dim against the sky. The sky is (0.018,0.030,0.060) near horizon. Aurora green 0.87 → very visible. Good.

One more thing: the requirement "brightening and fading" — the aurora should pulse over time. Add a global intensity modulation per layer: `pulse = 0.65 + 0.35*sin(t*0.23 + fi*2.0)`, and maybe a slow global drift. Also make the whole thing drift horizontally: add `t*0.05` to x? The warp already moves with t somewhat. Let's add explicit drift: x = p.x + t*(0.03 + 0.02*fi) + ...

Yes, add that.

Let me now also handle the time so that everything important happens within 30 s. The animation is continuous and shapes change over ~20-40s cycles. Fine.

Also I should make the aurora shape change noticeably. The warp fbm at t*0.05 → changes over ~20 s. Reasonable.

Let me write the final shader carefully now.

Also for `vnoise(vec2(x*1.1 + fi*7.0, t*0.10 + fi*3.0))` — the noise's y input is just time, so as t increases, the noise pattern shifts vertically — that's like a scrolling 1D noise → gives the n varying over time. Good.

Now code the JS:

```js
const canvas = document.getElementById('c');
const gl = canvas.getContext('webgl2', { antialias: false, alpha: false, powerPreference: 'high-performance' });
if (!gl) { document.body.innerHTML = '<p style="color:#fff">WebGL2 not supported</p>'; }

const vsSrc = `#version 300 es
in vec2 aPos;
void main(){ gl_Position = vec4(aPos, 0.0, 1.0); }`;

const fsSrc = `...`;

function compile(type, src){...}

const prog = ...
```

Use a VAO or just bind the buffer with vertexAttribPointer.

```js
const vbo = gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 3,-1, -1,3]), gl.STATIC_DRAW);
const loc = gl.getAttribLocation(prog, 'aPos');
gl.enableVertexAttribArray(loc);
gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
```

Note: in WebGL2 without VAO, default VAO works.

Resize:
```js
function resize(){
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const w = Math.floor(canvas.clientWidth * dpr);
  const h = Math.floor(canvas.clientHeight * dpr);
  if (canvas.width !== w || canvas.height !== h){
    canvas.width = w; canvas.height = h;
    gl.viewport(0,0,w,h);
  }
}
```
Call resize on load and on window resize (and in the render loop for safety).

Render loop with requestAnimationFrame, time in seconds from performance.now().

Let's use a uniform for time and resolution.

I'll use `gl.uniform2f(uResLoc, canvas.width, canvas.height)` each frame and `gl.uniform1f(uTimeLoc, t)`.

Note about precision: uTime growing large over time could cause precision problems in the noise (float precision). Use `t = (performance.now() - start)/1000` and wrap with modulo e.g. 3600? Since the animation is continuous and we use t in sin/noise, wrapping mod some period like 1000 s could cause a jump. Just leave it; over an hour, t=3600, with highp float (24-bit mantissa) precision at 3600 is ~0.0002 — fine.

Now let me write the final fragment shader fully, double checking syntax.

```glsl
#version 300 es
precision highp float;

uniform vec2 uRes;
uniform float uTime;

out vec4 fragColor;

const float HORIZON = 0.30;

float hash21(vec2 p){
  p = fract(p * vec2(127.1, 311.7));
  p += dot(p, p + 34.56);
  return fract(p.x * p.y);
}
```
Hmm, the common hash: 
```
float hash21(vec2 p){
  vec3 p3 = fract(vec3(p.xyx) * 0.1031);
  p3 += dot(p3, p3.yzx + 33.33);
  return fract((p3.x + p3.y) * p3.z);
}
```
This is a well-known good hash. I'll use that.

vnoise with smoothstep interpolation.

fbm 4 octaves.

OK writing everything out.

One concern: `if (h > 0.90)` in the star function — with derivative-free code, fine.

Another: loops with `for(int i=0;i<3;i++)` — constant bounds, fine in GLSL ES 3.0.

Let me write out the shader in full:

```glsl
#version 300 es
precision highp float;

uniform vec2  uRes;
uniform float uTime;

out vec4 fragColor;

const float HORIZON = 0.30;

// ---------- noise ----------
float hash21(vec2 p){
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

float vnoise(vec2 p){
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f*f*(3.0 - 2.0*f);
    float a = hash21(i);
    float b = hash21(i + vec2(1.0, 0.0));
    float c = hash21(i + vec2(0.0, 1.0));
    float d = hash21(i + vec2(1.0, 1.0));
    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

float fbm(vec2 p){
    float s = 0.0;
    float a = 0.5;
    for(int i = 0; i < 4; i++){
        s += a * vnoise(p);
        p = p * 2.03 + vec2(13.7, 7.3);
        a *= 0.5;
    }
    return s;
}

// ---------- sky ----------
vec3 skyGradient(float y){
    vec3 top = vec3(0.004, 0.007, 0.021);
    vec3 bot = vec3(0.020, 0.034, 0.066);
    vec3 c = mix(bot, top, smoothstep(HORIZON, 1.0, y));
    c += vec3(0.020, 0.055, 0.050) * exp(-max(y - HORIZON, 0.0) * 6.0);
    return c;
}

// ---------- stars ----------
vec3 starField(vec2 p, float t){
    vec3 c = vec3(0.0);

    // dense small stars
    vec2 sp = p * 24.0;
    vec2 id = floor(sp);
    vec2 gv = fract(sp) - 0.5;
    float h = hash21(id + 3.13);
    if(h > 0.90){
        vec2 off = (vec2(hash21(id + 1.7), hash21(id + 8.3)) - 0.5) * 0.72;
        float d = length(gv - off);
        float br = 0.30 + 0.70 * hash21(id + 4.9);
        float tw = 0.80 + 0.20 * sin(t * 2.7 + h * 91.0);
        c += vec3(0.80, 0.88, 1.0) * smoothstep(0.06, 0.0, d) * br * tw;
    }

    // few bright stars with cross flare
    vec2 sp2 = p * 4.2;
    vec2 id2 = floor(sp2);
    vec2 gv2 = fract(sp2) - 0.5;
    float h2 = hash21(id2 + 19.7);
    if(h2 > 0.93){
        vec2 off = (vec2(hash21(id2 + 2.3), hash21(id2 + 6.1)) - 0.5) * 0.6;
        vec2 d = gv2 - off;
        float dist = length(d);
        float tw = 0.70 + 0.30 * sin(t * 1.9 + h2 * 60.0);
        float core = smoothstep(0.05, 0.0, dist);
        float fl = (smoothstep(0.30, 0.0, abs(d.x)) * smoothstep(0.012, 0.0, abs(d.y))
                  + smoothstep(0.30, 0.0, abs(d.y)) * smoothstep(0.012, 0.0, abs(d.x))) * 0.5;
        c += vec3(1.0, 0.96, 0.88) * (core + fl) * tw * 1.3;
    }
    return c;
}

// ---------- aurora ----------
vec3 aurora(vec2 p, float t){
    vec3 col = vec3(0.0);
    float y = p.y;

    float warp = (fbm(vec2(p.x * 0.55 + 4.0, t * 0.045)) - 0.47) * 2.0;

    for(int i = 0; i < 3; i++){
        float fi = float(i);
        float drift = t * (0.045 + 0.025 * fi);
        float x = p.x + warp * (1.0 + 0.4 * fi) + drift + fi * 2.7;

        float n1 = vnoise(vec2(x * 1.1 + fi * 7.0, t * 0.10 + fi * 3.0));
        float n2 = vnoise(vec2(x * 2.4 - fi * 4.0, t * 0.17 + fi * 9.0));
        float n  = n1 * 0.62 + n2 * 0.38;

        float y0 = 0.32 + 0.14 * n + 0.02 * sin(x * 3.0 + t * 0.4 * (1.0 + fi));

        float vprof = smoothstep(y0 - 0.005, y0 + 0.035, y)
                    * exp(-max(y - y0, 0.0) * 1.9)
                    * (1.0 - smoothstep(0.80, 1.10, y));
        vprof *= smoothstep(0.24, 0.36, y);   // keep it above mountains

        float ph = x * (3.0 + 2.0 * fi) + n * 3.6 + t * (0.5 + 0.35 * fi);
        float sheet = pow(0.5 + 0.5 * sin(ph), 4.0);

        float rn = vnoise(vec2(x * 13.0 + fi * 5.0, y * 1.5 - t * 0.45));
        float rays = 0.30 + 1.7 * pow(rn, 1.35);

        float pulse = 0.62 + 0.38 * sin(t * 0.21 + fi * 2.1);
        float bright = vprof * sheet * rays * pulse * (0.62 / (1.0 + fi * 0.5));

        float hh = clamp((y - y0) * 2.0, 0.0, 1.0);
        vec3 green = vec3(0.10, 1.00, 0.36);
        vec3 teal  = vec3(0.28, 0.90, 0.72);
        vec3 viol  = vec3(0.58, 0.24, 1.00);
        vec3 cc = mix(green, teal, smoothstep(0.10, 0.55, hh));
        cc = mix(cc, viol, smoothstep(0.40, 1.0, hh) * (0.55 + 0.45 * sin(fi * 2.3 + 1.1)));

        col += cc * bright;
    }

    // soft diffuse haze
    float haze = exp(-pow((y - 0.55) * 2.4, 2.0));
    haze *= 0.5 + 0.5 * vnoise(vec2(p.x * 1.4, t * 0.07));
    col += vec3(0.10, 0.45, 0.34) * haze * 0.11;

    return col;
}
```

Wait: there's an issue with vprof *= smoothstep(0.24,0.36,y) — combined with the earlier smoothstep(y0-0.005, y0+0.035, y) where y0 is at least 0.32-0.14 = 0.18. Hmm y0 ranges 0.32±0.14 → 0.18 to 0.46. If y0 = 0.18, the curtain bottom is below the horizon — but the mountain region covers it (mountains go up to ~0.42 in places). Hmm, the smoothstep(0.24,0.36,y) will cut the curtain bottom for low y0 values. That's ok, it just makes that curtain fade in near the horizon.

Actually let me raise the minimum: y0 = 0.34 + 0.12*n → range 0.34–0.46. Plus a bit of sine. Then the vprof top fade. Fine. Let me use 0.33 + 0.13*n.

And keep smoothstep(0.22,0.34,y) for masking above mountains.

Mountains in sceneColor:

```glsl
vec3 sceneColor(vec2 p, float t){
    vec3 col = skyGradient(p.y);

    float starFade = smoothstep(HORIZON - 0.02, HORIZON + 0.20, p.y);
    col += starField(p, t) * starFade;

    col += aurora(p, t);

    // mountains
    float farH  = HORIZON + 0.018 + 0.080 * fbm(vec2(p.x * 0.70 + 21.0, 3.0));
    float nearH = HORIZON - 0.010 + 0.105 * pow(fbm(vec2(p.x * 1.55 + 61.0, 9.0)), 1.5);

    if(p.y < farH){
        float rim = smoothstep(farH - 0.014, farH, p.y);
        vec3 mc = vec3(0.022, 0.030, 0.052) + vec3(0.10, 0.16, 0.20) * rim * 0.30;
        col = mc;
    }
    if(p.y < nearH){
        float rim = smoothstep(nearH - 0.010, nearH, p.y);
        vec3 mc = vec3(0.007, 0.011, 0.022) + vec3(0.05, 0.09, 0.13) * rim * 0.22;
        col = mc;
    }
    return col;
}
```

Hmm, the far range's fbm at scale 0.7 across x range 3.56 → about 2.5 features. That's a broad ridge. The near range at 1.55 → ~5.5 features. Plus pow 1.5 sharpens valleys. Good.

But wait: `if(p.y < farH)` then `col = mc` — but the far range is behind near range; if nearH > farH somewhere, the near range covers. Fine.

Issue: the mountains at the very base near the horizon: below the horizon we don't compute them (water instead). Fine.

Water function as described.

One thing: in `water`, I call sceneColor twice → each calls aurora + stars + fbm's. Cost doubles. Plus the main sky call. So ~3 scene evaluations per pixel in the water area (which is 30% of the screen). Acceptable.

Actually, since the water region is only the bottom 30%, total cost is roughly 1 + 2*0.3 = 1.6 scene evaluations on average.

Let me write water:

```glsl
vec3 water(vec2 p, float t){
    float d = HORIZON - p.y;
    float depth = clamp(d / 0.30, 0.0, 1.0);

    vec2 rp = vec2(p.x, HORIZON + d);

    // ripples: stronger closer to viewer
    float amp = mix(0.0015, 0.022, depth * depth);
    rp.x += amp * 2.2 * sin(d * 42.0 + t * 1.4 + p.x * 5.0);
    rp.y += amp * 0.9 * sin(p.x * 26.0 + t * 2.0 + d * 20.0);

    vec3 refl = vec3(0.0);
    float blur = 0.004 + 0.020 * depth;
    refl += sceneColor(rp + vec2(blur, 0.0), t);
    refl += sceneColor(rp - vec2(blur, 0.0), t);
    refl *= 0.5;

    float fres = mix(0.92, 0.34, smoothstep(0.0, 1.0, depth));
    vec3 deep = vec3(0.005, 0.011, 0.025);
    vec3 col = deep + refl * fres * 0.90;

    // horizontal shimmer
    float sh = vnoise(vec2(p.x * 20.0, p.y * 110.0 + t * 0.7));
    col += vec3(0.02, 0.07, 0.06) * sh * depth * 0.30;

    // soften horizon line
    col = mix(col, skyGradient(HORIZON) * 0.55 + refl * 0.25, smoothstep(0.010, 0.0, d));
    return col;
}
```

Hmm, the last mix: with d→0 it goes to a mix of sky and refl — that's roughly what it already is near the horizon; it just softens. Fine.

But note the `rp` reflection taps: at d small, blur is 0.004, which in p units is 0.004 → in pixels at 1080p with p.x range 3.56 over 1920 px → 0.004 p-units = ~2 px. OK.

One more consideration: the reflection's vertical mirror means the aurora appears mirrored in the lake — good.

Now main():

```glsl
void main(){
    vec2 uv = gl_FragCoord.xy / uRes;
    float aspect = uRes.x / uRes.y;
    vec2 p = vec2((uv.x - 0.5) * aspect * 2.0, uv.y);

    float t = uTime;

    vec3 col;
    if(p.y > HORIZON){
        col = sceneColor(p, t);
    } else {
        col = water(p, t);
    }

    // slight vignette
    vec2 q = uv - 0.5;
    col *= 1.0 - 0.45 * dot(q, q);

    col = vec3(1.0) - exp(-col * 1.30);
    col = pow(max(col, 0.0), vec3(0.92));

    fragColor = vec4(col, 1.0);
}
```

Note: `pow(col, vec3(0.92))` slightly brightens midtones. Hmm, with the tonemap 1-exp(-1.3x), dark areas stay dark. Fine.

Wait, there's a subtlety: the mountains are set with `col = mc` inside sceneColor which is called for both sky and water. Good.

Another consideration: on the water, `sceneColor` includes the mountains, so the mountains reflect. But the reflected mountains are below y=HORIZON in the reflection coordinate (rp.y = HORIZON + d, which is above the horizon) — right, the mirrored point is above the horizon, so we sample the sky/mountains there. Correct.

Now, potential visual issue: the aurora reflection in the water would be a mirror image. Since aurora is mostly above y=0.35 and the water reflects y up to 0.60, we see the lower part of the aurora reflected. Good.

Let me double check the aurora `vprof` top fade uses `(1.0 - smoothstep(0.80, 1.10, y))` — at y=1 it's 1-smoothstep(0.8,1.1,1.0)=1-0.74=0.26. Combined with exp(-(1-0.4)*1.9)=0.32 → 0.08. Dim at the top; good.

Now the aspect: p.x = (uv.x-0.5)*aspect*2 → for a portrait window, aspect < 1, x range shrinks. Fine.

Also, on ultra-wide, we see more aurora. Good.

Let me reconsider the "vertical rays" requirement — we have `rays` with high x frequency. Good.

"curtains rippling and folding" — warp + sheet. Good.

Let me reconsider: is the sheet term going to look like parallel vertical bands? The sheet multiplies vprof which is a horizontal-ish band... Actually vprof varies along x too (through y0), creating the draping. The combination of sheet (vertical bands in x) and the vertical profile creates curtain folds. And rays add fine vertical striations. Should look decent.

Hmm, one thing: `sheet` uses pow(sin,4) which gives bands but the widths are determined by x-frequency, so they're vertical stripes across the whole sky, which might look more like "barcode" than curtain if too regular. The n modulation in the phase (n*3.6) breaks regularity, and the pulse. I think it'll look fine.

Let me also add a slow horizontal displacement to n so the folds travel: already have drift in x.

I think there might be an issue with the aurora appearing as full-height vertical stripes going all the way down. The vprof handles that.

Let me now assemble the whole file.

Also need to handle the case where the browser doesn't support WebGL2 — display a message.

Let me write the JS:

```js
(function(){
  const canvas = document.getElementById('c');
  const gl = canvas.getContext('webgl2', { antialias: false, alpha: false, depth: false, stencil: false, powerPreference: 'high-performance' });
  if(!gl){ document.body.innerHTML = '<div style="color:#9cf;font:16px sans-serif;padding:2rem">WebGL2 is not supported in this browser.</div>'; return; }

  const vert = `#version 300 es
  in vec2 aPos;
  void main(){ gl_Position = vec4(aPos, 0.0, 1.0); }`;

  const frag = `...`;

  function compileShader(type, src){
    const s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if(!gl.getShaderParameter(s, gl.COMPILE_STATUS)){
      console.error(gl.getShaderInfoLog(s));
      gl.deleteShader(s);
      return null;
    }
    return s;
  }
  const vs = compileShader(gl.VERTEX_SHADER, vert);
  const fs = compileShader(gl.FRAGMENT_SHADER, frag);
  const prog = gl.createProgram();
  gl.attachShader(prog, vs);
  gl.attachShader(prog, fs);
  gl.linkProgram(prog);
  if(!gl.getProgramParameter(prog, gl.LINK_STATUS)) console.error(gl.getProgramInfoLog(prog));
  gl.useProgram(prog);

  const buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 3,-1, -1,3]), gl.STATIC_DRAW);
  const aPos = gl.getAttribLocation(prog, 'aPos');
  gl.enableVertexAttribArray(aPos);
  gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);

  const uRes = gl.getUniformLocation(prog, 'uRes');
  const uTime = gl.getUniformLocation(prog, 'uTime');

  function resize(){
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = Math.max(1, Math.floor(canvas.clientWidth * dpr));
    const h = Math.max(1, Math.floor(canvas.clientHeight * dpr));
    if(canvas.width !== w || canvas.height !== h){
      canvas.width = w;
      canvas.height = h;
      gl.viewport(0, 0, w, h);
    }
  }
  window.addEventListener('resize', resize);
  resize();

  const start = performance.now();
  function frame(){
    resize();
    const t = (performance.now() - start) * 0.001;
    gl.uniform2f(uRes, canvas.width, canvas.height);
    gl.uniform1f(uTime, t);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
```

Canvas CSS: width:100vw; height:100vh; display:block. And clientWidth will be the CSS size. Good.

One issue: I set `depth: false` etc. — fine.

Now let me finalize the fragment shader text. I need to be careful with GLSL ES 3.0 syntax: `const float HORIZON = 0.30;` at global scope — fine.

The `if(p.y > HORIZON)` branch in main — fine.

Also, potential issue: in the water, I call `sceneColor` which calls `starField` twice, etc. OK.

Let me double check `pow(fbm(...), 1.5)` — fbm returns ≥ 0, fine.

`exp(-max(y-y0,0.0)*1.9)` fine.

Let me also double check the smoothstep args: `smoothstep(y0 - 0.005, y0 + 0.035, y)` — if y0+0.035 > y0-0.005, fine.

Let me now reconsider the brightness of the aurora relative to the tonemap. Concentrated bright bands ~0.6-1.0 in green plus 3 layers overlapping may reach 1.5-2 → tonemapped to ~0.9. Good.

The stars: contribution ~1.3 * (core+fl) — core is 1 in the center → after tonemapping ~0.7. Bright stars will be visible. Small stars: br up to 1.0, smoothstep peak 1 → 1.0 → tonemapped 0.72. Hmm, that's quite bright for a "small star" but they're 1-2 pixels, so it's fine (they'll look like stars).

Actually, small stars: `smoothstep(0.06, 0.0, d)` with d in cell-space where the cell is 1/24 p-units ≈ 1/(24) of p... p.x spans 3.56 → the cell is 0.0417 p-units wide. At 1920 px wide with p.x spanning 3.56 over the full width, 1 p-unit = 540 px, so a cell = 22.5 px. A star radius of 0.06 cell = 1.35 px. Good.

Bright stars: sp2 = p*4.2 → cell = 0.238 p-units = 128 px, radius 0.05 → 6.4 px core. That's a big bright star. And flare extending 0.30 → 38 px. Nice.

The number of bright stars: threshold h2>0.93 → 7% of cells. Cells spanning x: 3.56*4.2 = 15 columns, y: 1.0*4.2 = 4.2 rows → 63 cells → ~4 bright stars. Good. But we also want them only in the sky (above the mountains). We multiply by starFade which fades near the horizon. Also aurora region may wash them out. Fine.

Maybe increase p scale a bit: use 5.0 → 75 cells → 5 stars. Fine, keep 4.2.

Hmm, one thing: the starField is computed for the full p, including below the horizon (in the water reflection where rp.y > HORIZON, so it's fine).

Now, `starFade = smoothstep(HORIZON - 0.02, HORIZON + 0.20, p.y)` — in the reflection, p.y is rp.y (above horizon), so stars fade similarly. Fine.

Now let me write the final complete file.

One more check on the aurora color: for hh near 0 (bottom of curtain), green (0.10, 1.00, 0.36). At hh=1 (well above y0, i.e., y = y0 + 0.5), mix to violet with factor `smoothstep(0.40,1.0,hh)*(0.55+0.45*sin(...))`. sin(fi*2.3+1.1): for fi=0 → sin(1.1)=0.89 → factor 0.95; fi=1 → sin(3.4)=-0.26 → 0.43; fi=2 → sin(5.7)=-0.55 → 0.30. So layer 0 is mostly violet at height, layers 1,2 more green. Since violet appears higher up, this gives violet tops on one layer. Good — "violet light".

But note: vprof decays with height so the violet part is dim. Maybe boost violet: since the violet appears at hh>0.4 → (y-y0)>0.2 → exp(-0.38)=0.68. Still visible. OK.

Maybe also add a separate violet diffuse band across the upper sky, which is characteristic. The haze term is greenish; let me make the haze a mix of teal and violet:
```
vec3 hazecol = mix(vec3(0.10,0.45,0.34), vec3(0.35,0.15,0.70), smoothstep(0.55,0.95,y));
col += hazecol * haze * 0.12;
```
Good.

Let me write everything now.

Final check on the HTML/CSS: body margin 0, canvas 100vw/100vh. Also `overflow:hidden`.

One thing: `canvas.clientWidth` requires the canvas to be laid out; with CSS width:100vw it's fine.

Let me write the code block.

Also double-check: `#version 300 es` must be the very first line of the shader source — no leading newline. I'll write the template literal starting immediately.

Actually, in JS template literals, if I write:
```js
const frag = `#version 300 es
precision highp float;
...`;
```
then the first line is `#version 300 es` — correct.

Let me produce the final answer.

Wait — one more thought on `if(h > 0.90)` blocks inside a loop-free function: fine.

Also I should double check `hash21(id + 3.13)` where id is a vec2 — adding a scalar to a vec2 is allowed in GLSL? Yes, `vec2 + float` broadcasts. Yes that's valid.

`hash21(id2 + 19.7)` also fine.

Also `p3 += dot(p3, p3.yzx + 33.33);` — dot returns float, adding float to vec3 broadcasts. Valid.

Alright.

Let me also double check the water "shimmer": `vnoise(vec2(p.x * 20.0, p.y * 110.0 + t * 0.7))` — p.y range 0..0.3 → 0..33 in noise, p.x range ±1.8*20 = ±36. So features compressed in y → horizontal streaks. Good.

Final concern: performance of 3 sceneColor calls (2 in water) — acceptable.

Writing the final file now.

Actually, let me reconsider the aurora's vertical placement relative to the mountain tops. Mountains peak at farH max = 0.30+0.018+0.080*0.94 ≈ 0.393. nearH max = 0.30-0.010+0.105 = 0.395. So mountains top out at ~0.4. The aurora curtain bottom y0 ranges 0.33-0.46 — so the curtain base is around/behind the mountain tops. Good, typical.

The vprof *= smoothstep(0.22, 0.34, y) is mostly redundant given the mountains, but it prevents the aurora from bleeding below in the reflection... actually no, the reflection samples sceneColor at rp.y above the horizon, where the mountains are. Fine.

Hmm, actually wait. Something important: the mountains are drawn as solid color replacing everything, including stars and aurora. In the water reflection, the mirrored mountain silhouettes appear. Good.

Done. Writing it out.

One last: the `ripple` on the reflected y: `rp.y += amp*0.9*sin(p.x*26.0 + t*2.0 + d*20.0);` — this moves the sample point vertically, which for a mirrored image creates vertical wobble. Also, since amp varies with depth, the reflection gets distorted progressively. Good.

Let me finalize with a bit more careful tuning of `fres`: mix(0.92, 0.34, smoothstep(0,1,depth)) — near horizon reflectivity 0.92, at bottom 0.34. Multiplied by refl*0.90. Plus deep color. Good.

Writing it.