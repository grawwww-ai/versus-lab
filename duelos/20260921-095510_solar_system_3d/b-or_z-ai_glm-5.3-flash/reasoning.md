Plan: single HTML, module script, procedural canvas textures, cinematic camera tour with timestamps, starfield, sun glow sprite, orbit lines, moon, name overlay. ~30s tour: 8 planets × ~3.5s = 28s then loop.

Camera: move between planets using smooth interpolation; each segment ~3.5s: fly-in then hold. Use timestamp t from rAF. Keep planets orbiting (fast enough to see motion). Use relative sizes: sun 5, Mercury 0.38→ scale up for visibility: sizes like Mercury 0.5, Venus 0.9, Earth 1.0, Mars 0.7, Jupiter 2.8, Saturn 2.4, Uranus 1.6, Neptune 1.55. Distances: 10,14,19,24,34,44,54,63.

Camera path: for each planet, target planet world position (moving), camera offset relative to planet. Use smoothstep transition between previous planet and next over segment. Compute planet positions from time analytically so camera can target precisely.

Simple approach: tour segments of duration D=3.6s. During segment i, camera eases from viewpoint of planet i to planet i+1. Viewpoint: planet pos + offset scaled by planet radius. Interpolate camera pos and lookAt target between eased endpoints with smoothstep. Sun intro first 3s.

Write code.

Procedural textures: function makeTexture(w,h,drawFn). Earth: blue base, green blobs via random seeded; use simple noise via random circles. Jupiter bands: horizontal stripes with varying colors + noise. Mars: red with darker patches. Saturn rings: radial gradient ring texture on RingGeometry with proper UV mapping (adjust UVs or use canvas ring texture mapped — easier: create ring texture 256x8 with gradient, modify ring geometry UVs so u = radial). Standard trick: iterate positions, set uv.x based on radius.

Sun: MeshBasicMaterial emissive color + additive sprite halo (radial gradient canvas). PointLight at center.

Starfield: Points with 3000 random positions on sphere.

UI overlay: HTML div for planet name, fade via CSS opacity.

Orbit lines: THREE.LineLoop circles.

Moon: small sphere orbiting earth group.

Animate: time = timestamp/1000. Planet angle = t*speed + phase.

Tour timing: total = intro 2.5s + 8*3.6 = 31.3s, then loop back to sun.

Camera logic: define function viewOf(i, tt) returns {pos, target}: planet world pos; camera pos = planetPos + dir offset where dir rotates slightly; keep offset magnitude = radius*4 + 2. To avoid discontinuity, compute for continuous parameter: segIndex = floor((t-intro)/D), local = frac. If segIndex >= 8 → back to sun overview then loop. pos = lerp(view(i,local), view(i+1,local), smoothstep(local)). LookAt lerp similarly. During intro, camera pulls back from sun.

Handle when next is sun after Neptune (overview of whole system: pos (0, 60, 90), target origin).

Write it compactly.