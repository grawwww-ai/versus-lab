The user wants a premium Apple-style landing page for "Halo" smart glasses. Everything inline — no external resources. Let me plan this carefully because this needs to be genuinely impressive.

Let me think about the design direction:

**Product**: "Halo" — smart glasses that translate conversations in real time. This is an audio/wearable product, so my signature visual will be glasses drawn in SVG — side profile (temples/arms visible) and front view. I can draw elegant thin-frame glasses with a subtle tech accent.

**Visual language**: Apple-style means: huge type, lots of white space, black/white with one accent. I'll avoid default blue/purple. For Halo, I'll pick a warm amber/gold accent — evokes "halo" (light, ring of light) and feels premium against black. Something like #E8A33D or a warmer #F0B254... Actually a refined warm gold: `#D9A05B` or `#E4A94F`. Let me go with a warm amber `#E8A855`-ish, tuned for contrast on both dark and light. Maybe `#D97B29`? Too orange. Let me pick `#E0A83E`... I'll fine-tune: dark sections get `#E8B458`, light sections could use a slightly deeper `#B07820` for text contrast. Actually I can use one accent `--accent: #E5A94D` on dark, and on light sections use a darker variant via CSS variable override.

**Typography**: system fonts required (no external fonts). I'll use the system stack but craft it well: `-apple-system, "SF Pro Display", "Helvetica Neue", "Segoe UI", Roboto...`. The user explicitly says "Elegant typography using system fonts" — so system-ui stack is what's asked. I'll make it feel designed through weight/size/letter-spacing discipline. Big display headline with tight tracking (-0.03em), light weights for large sizes, semibold for emphasis.

**Structure**:
1. **Nav** — slim, frosted glass (backdrop-filter blur), appears on scroll.
2. **Hero** — full screen, dark (near-black `#0a0a0b`), huge headline "Halo" + tagline "Any language. Heard as your own." Product illustration: SVG glasses front view floating, with an animated "halo" ring behind it — a thin ring of light that slowly rotates/dashes. Live translation caption ticker at the bottom — like the Live Captions idea: words appear cycling through languages. That's a nice "alive" element: a line that types out "Bonjour → Hello" style translations continuously. This could be my signature moment: an ambient live-translation caption line under the glasses that cycles phrases in different languages with language labels.
3. **Sticky scroll section (light)** — product rotates/transforms as you scroll. I'll implement: a tall section (300vh), sticky inner viewport; an SVG of the glasses in 3/4 side view that rotates (rotateY illusion via scale/skew, or actual CSS 3D rotateY on an SVG built with layered sides). Building a convincing 3D glasses model in SVG is hard. Better approach: draw the glasses in a 3/4 perspective with SVG, and as you scroll, morph between front view and side view by cross-fading/interpolating two SVG paths? Morphing paths requires same point count — doable if I design both paths with matched command counts. That's ambitious but very doable if I carefully construct both the front view and side view with the same number of path segments.

Simpler but still impressive: use CSS 3D — construct the glasses from several SVG faces (front rim, lenses, temples) positioned in 3D space with `transform-style: preserve-3d`, and rotate the whole assembly with rotateY driven by scroll progress. That's genuinely 3D and would look great. Let me think: 
- Front frame: an SVG rounded shape (two lens rims + bridge) as a flat plane.
- Lenses: slightly inset planes with translucent fill.
- Temples (arms): long thin planes hinged at the sides, angled back (rotateY ~90° minus fold angle). Two temples, each a plane with some length.
- Nose pads: tiny planes.
- A "temple tip" thickness: duplicate plane offset in Z to give arms thickness.

With preserve-3d and scroll-driven rotateY from like -35° to 35° (or full rotation 0→360 partially), plus subtle rotateX, this could look genuinely premium. Add a soft elliptical shadow below that scales with rotation. The accent: a thin light strip on the temple (the "Halo beam" — speaker/haptic strip) that glows amber.

Hmm, but glowing elements... I want to avoid meaningless glow. A subtle emissive strip on a tech product is a product feature (translation indicator), not decoration — I'll keep it restrained: a thin amber line on the temple that "speaks" (animated dashes/level bars) during the translation caption moments. Keep it minimal.

Actually, let me reconsider the sticky section content: as you scroll through, the glasses rotate ~120° (front → three-quarter → side), and stage captions change: "Titanium frame. 24 grams." → "Beam-array speakers, hidden in the temples." → "A halo of microphones — six, all around." Each caption fades in/out tied to scroll progress. That's very Apple ("Design" scroll sections).

Building the 3D glasses in CSS planes: 
- Frame front: I'll draw with SVG: two rounded-rectangle-ish lens openings with a bridge, in a thin metal stroke. Actually the front rim as a single path (like classic wayfarer-ish but rounder, more premium panto shape). Fill: none, stroke: gradient? No decorative gradients... a metallic rim kind of needs shading. A subtle two-stop metallic gradient on the frame stroke is a *material representation*, not decorative ornament — I think that's justified craft (titanium looks like titanium). I'll keep it very subtle: light gray → slightly darker gray. That's material realism, fine.

Let me design the front shape: panto/round frames. Two circles-ish lens rims (slightly rounded squares or perfect circles look classy — panto is slightly flattened bottom). I'll do near-circles with slight keyhole bridge. SVG path for one continuous rim: M left lens outer... simpler: two `<path>` lens rims + bridge path + hinge blocks.

For the 3D assembly:
- Group `glasses3d` with perspective on parent.
- `.face-front` plane at z=+depth/2 containing rims (stroke), lens glass (semi-transparent fill with slight tint), and a subtle top bar? 
- `.face-back` at z=-depth/2: the same rim shape but darker (this gives the frame thickness when viewed at angle — the back face mirrored). When rotated, you see the rim edge... Actually true extrusion of an arbitrary shape needs many side faces. Approximation: front face + back face + the lenses as translucent volume + temples give enough 3D read. The rim thickness gap will show as empty space between front and back rims at oblique angles — which actually reads okay as a thin frame? Hmm, empty between would look hollow. Alternative: make depth small (like 6px) so the gap is minor; plus add a few connecting "edge" planes at top/bottom of rims? 

Simpler robust alternative: skip true extrusion. Render the glasses as ONE SVG that I redraw per rotation using a parameter t (0..1) — i.e., code-generated morph: I compute lens rim ellipses projected at angle θ (rotateY): a circle at x-offset d rotated by θ becomes an ellipse with rx = r·cosθ shifted... Actually rotating a 3D torus-like rim: each lens rim is a circle in the x-y plane at z=0; rotating about Y: it projects to an ellipse with horizontal radius r·cosθ, vertical r. The rim has thickness (tube), giving two nested ellipses. Temples are lines going back in z: project to lines from hinge point going... when rotated by θ, a point (x,y,z) maps to screenX = x·cosθ + z·sinθ, screenY = y, with perspective scaling by 1/(1 - z·sinθ/perspective) roughly. I can compute all this in JS and update SVG path `d` attributes per scroll frame. That gives a genuinely smooth, correct 3D rotation of glasses with proper occlusion ordering (temples behind front when facing front, in front when facing back).

That's very appealing: a JS-driven procedural SVG renderer for the glasses, animating rotation with scroll. Points:
- Lens rims: N=48 points around circle, left center (-34, -2, 0), right center (34,-2,0), radius 30 (slightly squashed: ry 32? keep circle; panto: scale y 1.02 fine). Rim = outer radius 30, inner 26.5 → two paths, or one path ring via two subpaths with fill-rule evenodd, filled metallic. Stroke not needed then.
- Bridge: curve connecting inner edges at top: from left rim inner top area to right rim inner top. I can compute bridge as a path between points on the rims, maybe a simple arc: from (leftCx + r·cos(215°)... easier: bridge from angle -50° on left lens? Let me define: keyhole bridge spanning between lenses at y ≈ top region. Points: left bridge anchor at angle 40° above horizontal toward center: P1 = (leftCx + 30·cos(-40°)... Let me just compute in code with angles like 210°..? I'll fine tune visually in my head: circle center (±34, 0). Inner edge toward center is at angle 180° (pointing to center) → (±(34-30),0)=(±4,0). Top inner at angle 135°? Let's param angle measured standard: point = (cx + r·cosA, cy - r·sinA). Inner-top of left lens: A=45° → (34-21.2, -21.2)=(12.8,-21.2)... that's toward center-top. Right lens inner-top: A=135° → (34-21.2? no: cx=34, cos135=-0.707 → 34-21.2=12.8, sin135=0.707 → -21.2). So bridge connects (12.8,-21.2)?? Wait both compute to (12.8,-21.2) — that means the lenses overlap? r=30, centers ±34 → gap between inner edges = 68-60=8. So inner-top points at x=12.8 vs 12.8... no: left lens center -34: inner-top A=45°: x=-34+21.2=-12.8. Right lens inner-top A=135°: x=12.8. Good, bridge from (-12.8,-21.2) to (12.8,-21.2) — but that's a straight chord across the top gap; a keyhole bridge arcs upward: quadratic control at (0, -30). Fine.
- Lenses: filled inner circles with translucent blue-gray? Avoid blue... a cool neutral smoke tint: rgba(180,190,200,0.18) with slight highlight. Actually lens tint smoke `rgba(140,150,160,.2)` plus a specular sweep? Keep simple: fill with subtle radial? Avoid fancy. A flat translucent fill reads as glass fine, maybe with a lighter arc on upper area (a crescent path) for glint — that's material realism.
- Temples: hinge at outer edge of each rim at (±64, -6, 0), temple extends back in -z: length 130, slight inward angle and downward curve at the ear. Projected: hinge point H=(±64, -8, 0); tip T=(±58, 2, -130) (slight taper in). Also thickness: two parallel lines offset ~4 in y. Draw as filled quad: H, T, T+(0,4.5), H+(0,5) — a tapered arm. Add the accent strip: small quad near tip in amber. Also ear bend: last 25px curves down: T then bend point B=(±56, 16, -155)? Projection: z=-155 sinθ... fine.
- Nose pads: two small ellipses at (±10, 8, -4).
- Ordering/painting: compute depth of each element (average z after rotation) and sort painter's algorithm: draw farthest first. Each element gets an approximate depth key. Also shading: brightness factor based on face normal vs light — e.g., rim fill lightness varies with cos(θ), temples darker when pointing away. This gives a truly 3D feel.

Rotate θ from about 25° (slight three-quarter) at section start to -115°? Or 0 (front) → 90 (pure side) → maybe continue to 150 (seeing temple from outside-back)? Apple-style: start front, rotate to near-profile. I'll do θ: -30° → 100°? Hmm — with temples folding back, at θ=90° you see pure side profile: one lens rim edge-on (thin vertical line), temple extending toward viewer? Temples go back in -z; at θ=90° (rotate about Y), screen x = z·sinθ, so temple projects to horizontal line from hinge at x=±64·cos90=0... wait hinge x projects to x·cosθ = 0, and z=-130 → screenX = -130·sinθ·(direction). Sign conventions: I'll define rotation: screenX = x·cosθ + z·sinθ? Let's test θ=0: screenX = x ✓. θ=90°: screenX = z. Temple z=-130 → screenX=-130 (extends left). Hinge at (64,-8,0) → screenX=0. So right temple extends from x=0 to x=-130 — toward the left and toward viewer depth-wise... with perspective, the tip (z=-130) is farther → smaller. Looks like a side view where the temple goes off to the left. Good — but the left temple hinge (-64,-8,0) also projects to screenX=0, tip also -130 — both temples overlap (they're at same depth ±?). Left temple tip z=-130 too → they overlap exactly. That's fine (real glasses from the side show one temple; the other is hidden behind). Slight y offsets will differ? Both temples same y — they'd perfectly overlap. I can give tiny offsets (left temple z=-126) so it peeks 1px — realistic.

Perspective: use a projection with eye distance D=900: scale = D/(D - z·?) hmm. After rotation, depth dimension = ... Let me define rotation about Y by θ: x' = x·cosθ + z·sinθ; z' = -x·sinθ + z·cosθ (screen depth toward viewer negative or positive — pick z' positive = toward viewer). Then perspective: px = x'·D/(D - z'), py = y·D/(D - z'), with D=1000. When temple goes back z=-130: at θ=0, z'=-130 → scale = 1000/1130 = 0.885 — tip appears smaller ✓. At θ=90°: temple z'= x·... for hinge x=64: z' = -64·1·? with formula z' = -x·sinθ + z·cosθ = -64 → toward viewer (if positive toward viewer then -64 is away...). Ugh, signs. I'll just implement and trust painter sorting by z' and correct signs by construction; I'll define: rotateY(θ): x' = x·cosθ - z·sinθ; z' = x·sinθ + z·cosθ. θ=0 identity. Increasing θ turns the right side toward viewer? Point (1,0,0) → (cosθ, 0, sinθ): as θ grows, right edge comes toward viewer (z'>0). OK.

Also animate translateY slight float and a ground shadow ellipse (width varies with θ: widest at side view? shadow of glasses ~ elongated along temple direction; approximate: scaleX = |cosθ|·w + |sinθ|·w2...). Keep shadow as an ellipse whose rx/ry interpolate and opacity soft.

This procedural renderer is genuinely a "signature" — glasses that truly rotate in pseudo-3D, drawn live. I'm fairly confident I can code it correctly. Let me also reuse the same engine for the HERO (front view, θ≈-14° slight angle, gentle idle sway via requestAnimationFrame — floats + tiny rotation oscillation) — one renderer, two instances (hero: idle animation; scroll section: scroll-driven with captions). That unifies the design. The hero glasses could even show the amber "speaking" strip animation synced with the caption ticker.

Also HERO: big headline. "Halo" wordmark? Product name is Halo; headline like:
- Eyebrow: "Introducing Halo"
- H1: "Any language. / Spoken yours." Hmm. Better: "Speak anything. / Hear everything." or "Every language, / in your ear." Apple style: short. Maybe: "The conversation, translated. As it happens." Or headline "Understood. Everywhere." Let me craft: H1: "Any two people. One conversation." Tagline: "Halo translates speech in real time — into your ear, in your voice, in your language." I like: big line 1: "Every word," line 2: "in every language." Then sub: "Halo listens, translates and whispers it back to you in real time. 41 languages. No phone in hand. No pause in the conversation."
- CTAs: "Pre-order — $349" (amber pill, solid — solid color pill is fine, not a gradient) and "Watch the film ›" link (no film, but link can scroll to features — must be wired: scroll to #design). "Watch the film" would be fake... I'll make secondary link "Explore the design ↓" scrolling to sticky section. Good, real behavior.
- Below headline: the glasses SVG floating with the halo ring: a thin elliptical ring around/behind glasses (like an orbit ring) — the "halo" motif: one thin 1px ring, mostly faint, with a small bright arc segment that travels along it (stroke-dashoffset animation). Restrained, meaningful (it's the product name). Plus the caption ticker beneath: `[fr] « On y va ? » → "Shall we go?"` cycling. Live region styling like captions: small caps language tag + text. This ticker is the alive element.

Scroll indicator: thin "Scroll" with animated line.

**Nav**: fixed top, blur, logo mark (small SVG halo ring + wordmark "Halo"), links: Overview, Design, Features, Specs(→numbers), Compare, right side "Pre-order" pill. Smooth scrolling via CSS scroll-behavior or JS. On scroll > threshold, nav gains background. Hide/show? Keep simple: always visible, transparent → frosted on scroll.

**Features grid**: I must avoid uniform equal-width card rows. So: an editorial asymmetric layout. Ideas: a 12-col grid with varied spans and heights, some cells text-only, one cell containing a small animated SVG demo (e.g., waveform → translated text), one with the mic array diagram, etc. 6 features:
1. Real-time translation (43 languages) — with a tiny inline live transcript animation.
2. Whispers in your voice? Feature: "Bone-conduction audio — private, only you hear" — small ear diagram? Keep: temple speaker cross-section mini SVG.
3. Six-mic beamforming — mic dots arranged in arc, animated pulsing in sequence picking the active speaker.
4. Offline mode — "No signal? 12 languages work on-device." maybe a small globe/plane icon... icon library required — but no external resources allowed! The user says no external resources, so I can't use an icon CDN. I need inline SVG icons — I'll hand-draw a small consistent icon set inline (stroke-based, 24px grid): wave/audio, mic, battery/bolt, globe, feather(weight), wifi-off, shield, music note. Hand-drawn inline SVG icons count as proper icons (not emoji) — good.
5. 12-hour battery + case charge — tiny battery SVG that fills.
6. All-day comfort 24g — feather icon.

To avoid uniformity: layout like: full-width intro statement, then grid where feature 1 spans 7 cols with the animated transcript demo, feature 2 spans 5, then row of 4/4/4? No — avoid equal thirds. Do rows: [7|5], [5|7], then a wide 12 strip? Or [4|8],[8|4]... I'll do: row1: span7 (translatable demo) + span5 (privacy audio); row2: span4 (mics) + span4 (offline) + span4 (battery)? That's the equal-3 I dislike. Instead: row2: span5 (six-mic diagram) + span7 (battery + weight combined stat mini-row?) Hmm the big numbers section already covers battery/languages/weight. So features: 
1. Instant translation (span 7, with transcript demo)
2. Private bone audio (span 5)
3. Six-mic array (span 5, arc diagram)
4. Works offline (span 7, with map-ish dots? or a toggle demo: airplane toggle switching language count)
Maybe that's enough — 4 substantial features with 2 visuals. Or add 5th full-width statement: "And music. Pure Halo sound." skip. 4 features, asymmetric, each with inline icon + heading + copy; two have live mini-demos. Grid with divider lines (1px hairlines) rather than card boxes — Apple-ish "tech spec" grid with hairline borders, generous padding. Hairline borders in a grid look editorial, not card-y. 

**Big animated numbers section** (dark): counters animate on scroll into view: 43 languages, 24 grams, 36-hour battery (with case), 0.08s? Latency "<0.3 s". Layout: big numerals (like 120px light weight) with count-up animation + small labels, arranged as a horizontal row? A row of 3-4 big numbers separated by hairlines is classic Apple spec style — but is that "evenly-tiled modules"? It's a stat strip; I'll make it feel intentional: baseline-aligned huge numerals with different widths, left-aligned labels, hairline verticals — that's a classic editorial spec band, fine. Count-up with easing, triggered by IntersectionObserver once. Maybe include units that count too (e.g., "24 g" counts 0→24; "43" counts; "36 h"; plus "0.28 s" counts decimals). Add a supporting line under each. Dark section, amber accents on the numeral? Keep numerals white, units amber.

**Comparison of two models**: Halo and Halo Pro (or "Halo" / "Halo Pro"). Avoid uniform card row: do a two-column comparison table with hairlines: left column feature names, two model columns; header row shows mini product render (same renderer! small size, front view vs pro with... maybe Pro has different accent strip color/size — render both with the engine, Pro with darker lenses + gold ring?). Differences: battery 30h vs 36h, languages 32 cloud / 43 offline?, titanium vs aluminum, mics 4 vs 6, price $349 / $499. Table rows with checkmark icons vs values. Highlight recommended column with a subtle "Most popular" tag. Also could add toggle? Keep table. Add per-column CTA buttons (select) that trigger the pre-order action — wire buttons to pre-order section anchor or to a toast ("Added to pre-order list") — no alert(); I'll implement a toast system. Actually better: model select buttons set a state (chosen model shown in final CTA: "Pre-order Halo Pro — $499") and smooth-scroll to pre-order. Real interactivity ✓.

**Pre-order CTA section** (light or dark?): sequence of sections: hero dark → sticky design light → features light? Alternate: hero dark, design sticky light, numbers dark, features light, compare light-ish? Need both dark and light sections ✓ (hero dark + numbers dark; design + features light; CTA maybe dark for finale — bookends dark, middle light: elegant rhythm: DARK hero → LIGHT design → LIGHT features (could be same light run but different bg tint, e.g., #fafafa vs white) → DARK numbers → LIGHT compare → DARK CTA/footer. Hmm alternating too much. Plan:
1. Hero — dark (#0B0B0C)
2. Design sticky — light (#F5F4F1 warm off-white)
3. Features — white (#FCFCFB)? Or keep light continuous: design+features both light with a divider statement between.
4. Numbers — dark (#0B0B0C)
5. Compare — light (#F5F4F1)
6. Pre-order + footer — dark (#0B0B0C) finale with glasses render dim + big "Be first in line." + email input + button + toast on submit (validate email, success message inline). Footer links (real hover behavior, they can be href="#section" anchors where applicable; non-applicable ones... every interactive element should do something real — footer links can point to sections or show a toast "Coming soon"? A toast "Opens at launch" is a bit fake but it's honest feedback. I'll keep footer minimal: few anchor links + legal text. Fine.)

**Pre-order section**: email capture with inline validation + success state (button morphs to "You're on the list ✓" — no emoji, use SVG check), plus model picker pills reflecting earlier choice. Also fake counter? No fake stats. Show "Pre-order opens March 2025"? It's an invented product; fine to say "Ships this spring." Keep copy plausible.

**Scroll animations**: IntersectionObserver adding `.in` class → transitions (opacity, translateY, scale, blur?). Use `transition` with cubic-bezier and staggered delays via CSS custom property `--d`. Also parallax touches: hero glasses subtle translate on scroll; section headings reveal with clip? Keep to fade+rise+scale per spec. Also a scroll progress bar? Not needed.

**Sticky section details**: container height 320vh; inner position sticky top 0 height 100vh; canvas (SVG) centered; progress p = scrolled fraction; θ = lerp(-28°, 96°, easeInOut(p)) maybe with slight overshoot? Use easing on p. Captions: 3 captions at p bands [0-0.33],[0.33-0.66],[0.66-1] cross-fading: opacity computed in JS from p. Caption position: left side on desktop (glasses right?) Actually center glasses, captions below-left overlaid? Apple puts text beside. Layout: glasses center-right, caption block left-center; on mobile stacked (caption bottom). Also a progress indicator: thin vertical line with dot? Or "01 / 03"? A small horizontal progress hairline under captions. Also the big background word? Apple does huge word behind product ("Titanium"). Idea: huge ghost word behind glasses changing with stage: "TITANIUM" → "ACOUSTICS" → "SIX MICS" — big, very low contrast... careful with low-contrast gray on dark; this is on LIGHT background so huge light-gray outline text is fine (contrast issue applies to dark bg). Light bg #F5F4F1 with word in rgba(0,0,0,0.05) huge — subtle depth, tasteful. Word crossfades per stage.

Also transform: glasses scale slightly up mid-scroll (1 → 1.15 → 1). And translateY.

**Hero SVG halo ring**: ellipse around glasses, rotate slowly (CSS animation on a group with transform-box: fill-box; transform-origin center; rotate). Ring: stroke rgba(255,255,255,0.12) full ellipse + a brighter amber arc (strokeDasharray small portion) animating dashoffset linearly — a "satellite" light orbiting. Subtle. Also I could add tiny star dots? No, keep clean.

**Caption ticker (hero)**: array of {lang, native, english}: 
- {ja: 「そちらはいかがですか？」} → "How about on your side?"
- fr: « On y va ? » → "Shall we go?"
- es: ¿Ya terminaste? → "Are you done yet?"
- de: "Ich verstehe." → I understand.
- it: "Ci vediamo dopo." → "See you later."
- ko, pt, ar? Arabic text renders via system fonts fine. Maybe include to show breadth: ar: «أنا أفهمك» → "I understand you."
Cycle: fade out, swap, fade in; language tag in amber small caps; native phrase + arrow + translation. Also a tiny "LIVE" dot pulsing. Also maybe show which ear? Keep simple. Position under glasses within hero; on small screens keep.

Also hero bottom: quick spec strip? Maybe three small stats under ticker? That duplicates numbers section; skip — keep hero pure: headline top-left? Apple heroes are centered. Centered: eyebrow, H1, sub, CTAs, then glasses large with halo ring, ticker below glasses, scroll cue at bottom. Full-screen: use min-height 100vh, glasses maybe partially below fold — that's good, invites scroll. Actually "full-screen hero": make it exactly 100vh with glasses sized to fit; glasses can bleed slightly. I'll allow hero to be 100svh with content arranged: top 55% text, bottom 45% glasses+ticker, overlapping slightly.

**Renderer engine** (shared function): 

```js
function drawGlasses(svg, opts) // opts: {theta, rx(pitch), scale, tint colors, accent, speaking}
```
Builds string of SVG elements with computed attributes, sets svg.innerHTML. Points computed as described. Elements list with depth for sorting:
- far temple (the one on far side) — actually each temple's depth = z' of its midpoint; sort all elements by depth ascending (far first). Elements: [templeL, templeR, rimFront(group: rims+lenses+bridge as one path set — but lens glass is translucent so order matters: lens behind rim stroke? rim is ring fill (evenodd) and lens circle inside; draw lens first then rim ring), nosePads]. Since rims are at z≈0 both lenses same plane; temples start at z=0 going back. For simplicity, treat: rimGroup depth = 0-ish (its z'=small), lensGroup same, templeL/R computed, nosePads z=-6. Painter sort by z' ascending (far = negative z' first? define z' positive toward viewer → draw ascending z' so near last). Rim group at z'= varies with rotation: rim center (0,0,0) → z'=0; temples mid z' negative (behind) at θ small, at θ near 90° temples' z' = -x·sinθ + z·cosθ: for right temple (x=64,z=-65avg): θ=90 → z'=-64 (far behind) — correct, temples behind head... but wait at θ=90° (side view), temples should be between viewer and the far lens? Real side view: nearest thing is the near temple, then near lens rim edge, then far temple. Our near temple at θ=90: right temple hinge x=64: z' = 64·sin90 + (-65)·cos90 = 64 → toward viewer ✓ (positive toward viewer). Left temple: -64·1 + 0 = -64 → far ✓. Rim: z'=0 between ✓. Painter: draw left temple, rim, right temple. 

At θ=0: right temple z' = 64·0 + (-65)·1 = -65 (behind rim ✓), left same. Both behind. ✓.

At θ=-28° (hero, slight angle): fine.

Shading: temple brightness depends on angle between temple face normal and light. Temple plane normal ~ ±x direction rotated: normalN = (cosθ_dir...). Simpler: brightness for right temple = 0.55 + 0.45·max(0, cos(θ)) for outer face visible when θ<... I'll compute per temple: visibleFace = (temple on right, θ>0 shows its outer face? ). Honestly, simpler shading: temple fill lightness = base ± k·sin(θ) sign-dependent: light source top-left-front. rim front fill lightness varies with |cosθ| (facing viewer). Lens opacity increases at oblique angles. Also when θ beyond 90°, we see the back of rims (lenses still visible, rim ring same). Also flip: when |θ|>90 the temples' near/far swap automatically via z' math ✓.

Edge case θ=90 exactly: rim ring edge-on becomes thin vertical sliver — with evenodd ring it becomes a thin ellipse of width r·cos90=0 → invisible; plus thickness? Our rim ring is 2D extrusion-less: at 90° it vanishes. To keep a visible edge, draw a "rim edge" — hmm. Mitigate: add small z-extrusion: draw rim twice (z=+3 and z=-3, the frame front and back) plus connect visually via... At θ=90 the two copies are offset horizontally by 6·sinθ=6px apart, each nearly edge-on thin ellipse — combined they read as the frame edge seen from side (a 6px band) — actually two thin ellipses side by side with gap. Meh. Better: draw a filled "edge" shape: the union silhouette? Alternative trick: draw the ring with a fat stroke instead of evenodd fill: stroke-width 4 → at edge-on, stroke of the ellipse path still renders (stroke has width even when path is thin) → a 4px vertical band ✓. So rims: two ellipse paths (outer rx, ry) stroked 4px? Ring thickness via stroke: outer circle r=30 stroked 4 → ring from 28-32 ✓. At edge-on, ellipse rx→~0 but stroke-width 4 keeps a 4px wide sliver — vertical line of height 2r ✓. 

Bridge: stroke path width 5. Temples: filled quads + edge case fine (they're long in z so never vanish). Nose pads small ellipses vanish edge-on at 90 — acceptable (hidden behind rim edge band anyway near center? nose pads at z=-4, x=±10: at θ=90, x' = x·cosθ - z·sinθ = 4?? x'=10·0 - (-4)·1 = 4. They'd appear slightly right — tiny; okay, or fade them by |cosθ|.) I'll fade nose pads opacity with |cosθ|.

Also add a subtle "temple accent strip": on each temple near the tip, a small amber quad — the Halo indicator; animate (speaking equalizer: 4 tiny bars?) In side view this reads as the glowing strip ✓. During hero, animate its opacity/bars with the caption ticker (when "translation arrives", strip pulses). Implement as small rects whose heights animate via JS time-based (in the rAF loop for hero). In scroll section, static strip lit.

Also top bar? Many smart glasses have a camera dot: add a tiny circle at rim outer top corner — dark dot with amber ring? A small 2.5px circle at outer top of each rim (like camera). Subtle.

Lens glint: an arc highlight: path along upper-left of lens, stroke white 0.35 opacity 1.5px, only when facing (|θ|<60 fade). Cheap and effective.

**Ground shadow** in scroll section: separate SVG/ellipse under glasses, JS-updated rx: rx = base·(|cosθ|·0.9+|sinθ|·1.4)? Temple extends back so shadow longer at side view. opacity ~0.15 blur via feGaussianBlur filter or just radial soft: use CSS filter: blur(14px) on an ellipse div — simpler: an absolutely positioned div with border-radius 50%, background radial? Radial gradient for shadow softness — it's a shadow, fine, or use box-shadow? An ellipse div with background: radial-gradient(closest-side, rgba(0,0,0,.28), transparent 70%) + blur. That's a shadow, acceptable use of radial gradient (functional). Or SVG filter blur. I'll use a div with radial gradient — it's rendering a soft shadow, not decoration.

**Numbers count-up**: IO trigger; animate with rAF, easeOutExpo, format decimals (0.28 s needs 2 decimals; 43, 24, 36 integers). Number strip: 4 stats: 43 languages (offline+cloud?), "24 g — lighter than a mechanical pencil"? copy: "24 grams. You'll forget it's on." ; "36 h total with case" ; "0.28 s translation latency". Layout: flex row, wrap on mobile, each stat: huge numeral (clamp(64px,10vw,140px), font-weight 200, letter-spacing -0.04em), unit smaller amber, label + line below in muted. Hairline separators via border-left except first. Dark bg #0B0B0C, numerals #F5F5F4, muted #9C9C97 (that's mid-gray on dark — ensure contrast ok: #A1A1A6 on #0B0B0C is ~7:1? #A1A1A6 luminance ~0.36 vs 0.005 → contrast ≈ (0.41)/(0.055)≈7.4 ✓ fine, not "large low-contrast area", it's small text with adequate contrast).

**Features demos**:
Demo A (real-time translation): a chat-like transcript: two speakers "Her (日本語)" and "You (English)" lines appearing sequentially with typewriter, loop. Implementation: small JS loop appending lines (max 4, then clear), each line: speaker tag + text; fade/slide in. Lines:
- Aya · 日本語: 「会議は何時からですか？」
- You · English: "What time does the meeting start?"
Then:
- Aya: 「三時です。二階の会議室です。」
- You: "At three. Conference room, second floor."
Nice — shows both directions! Glasses translate both ways (they hear the other language and whisper translation to you; and your speech can be shown/subtitled to them via phone? Or Halo's speaker? For pair of Halos). Copy: "Halo works both ways — you hear them; on their phone, they read you." Good.
Demo B (mics): SVG arc of 6 dots; animation: a "sound source" dot moving; nearest mic dots illuminate sequentially — simpler: dots pulse in a wave, with a directional cone? Implement: 6 dots along the top arc of a glasses-outline mini; a small moving dot (speaker) travels left→right along an arc below; nearest 2 mics glow amber with a line (beam) connecting — JS anim positions. Moderate effort, do a simplified version: a sine-driven sweep highlighting mics with beams. I'll implement: container SVG 300x140; mics fixed positions; speaker dot moves along path param t; compute nearest mic index; draw beam line from that mic to speaker with amber stroke, mic dot enlarges. Runs on rAF only when visible (IO to pause). Nice "alive" detail.
Demo C (offline): toggle "Airplane mode" switch: flipping toggles list "On-device: 12 languages" vs "Via Halo Cloud: 43 languages" with count flip animation. Interactive toggle ✓.
Demo D (bone audio): static small SVG cross-section of temple + skull curve with sound waves? Might skip visual; instead a nice copy + icon. To keep balance: features layout:

Row 1: [span 7: Real-time translation + Demo A] [span 5: Private by design — bone conduction, icon ear/wave, copy]
Row 2: [span 5: Six mics + Demo B] [span 7: Offline + Demo C]?? Then where battery/weight/comfort? Numbers section covers battery/weight/languages. Feature list: translation, privacy, mics, offline, + maybe "All-day" comfort merges into numbers. Also "Music & calls" — add a slim full-width strip: "And it's simply great headphones." with music icon — one-line banner. Hmm keep 4 features + strip. Good asymmetry: 7/5 then 5/7 ✓ not uniform.

Hairline grid: use CSS grid with 1px gaps over background acting as lines? Use borders: container with grid, cells with border-top/left pattern... simplest: grid gap: 1px; background: hairline color; cells background: section bg → crisp hairlines between cells, Apple-style. Outer border too. On light bg hairline rgba(0,0,0,.12).

**Compare section**: two models. Layout: heading "Two models. One halo." Toggle? Table: grid columns: [label 1fr][Halo 1fr][Halo Pro 1fr]. Header cells: mini glasses render (SVG via engine, static front view, small 200px wide; Pro version: slight differences — pro gets titanium darker rim + amber ring around lens? I can pass opts: pro → rim darker, lens tint darker, accent thicker, plus "Pro" etched?). Rows: Price ($349/$499 — pre-order pricing), Weight 24g/26g, Battery (w/ case) 30h/36h, Languages offline 12/26, Languages total 43/43? Differ: "Translation engine: Standard / Elite (on-device neural)", Mics 4/6, Frame finish: Aluminum / Grade-5 titanium, Water resistance IPX4/IPX5? Keep ~7 rows. Checkmarks/dashes: values textual. Recommended: Halo Pro column header has small amber tag "Most capable". Row hover highlight. Buttons under each column: "Pre-order Halo" / "Pre-order Halo Pro" → sets selected model + scrolls to CTA + updates CTA. Mobile: table scrolls horizontally or becomes stacked per-model blocks (media query: each row becomes... simpler: allow horizontal scroll with min-width). I'll implement responsive: below 720px, the label column shrinks and font sizes reduce; or switch to two stacked cards? Stacked cards = two model blocks each with list — that's fine and avoids scroll. Use CSS: at small widths, grid becomes 2 cols (models) and labels become inline small text above each value (need data-label duplication — use CSS ::before with attr(data-label)). I'll do that: each value cell gets data-label, on mobile grid-template-columns: 1fr 1fr; label cells hidden; value cells show ::before attr(data-label). Header cells keep renders. Workable.

**Pre-order section (dark finale)**: big statement "Be first in line." sub "Halo ships this spring. Reserve yours with an email — pay when it ships." Model pills (Halo — $349 / Halo Pro — $499) reflecting state, email input + button "Reserve". On submit: validate (regex); error inline shake+message; success: replace form with confirmation block (check icon in amber circle + "You're in line for Halo Pro. We'll email you when pre-orders open — position #48,211"? A queue number is fake-ish but it's an invented product demo — playful but might read as fake stat. Instead: "Reservation saved. We'll email {email} when Halo Pro ships." Clean. Toast also appears bottom: "Reservation saved". Button micro-interaction: press scale.

Also maybe small print: "No charge until shipping. Cancel anytime."

**Footer**: hairline top, columns: logo+tag, nav links (anchors), small print "© 2025 Halo Audio Inc. Halo is a concept."? Keep "© 2025 Halo. Designed in Copenhagen." (playful). Links: Overview/Design/Features/Compare anchors + "Press kit" → toast "Press kit available at launch"? I'd rather avoid stub; make footer links all anchors to real sections + maybe "Privacy" → toast? Just anchors; add "Back to top" link. Fine.

**Toast system**: fixed bottom center, slides up, auto-dismiss 3.5s, with icon. Used for reservation success maybe + form errors use inline. Keep toasts minimal (maybe only for compare "Halo Pro selected — taking you to pre-order"? That could be noisy; inline is enough. I'll still build toast for reservation success since form transforms anyway... redundant. Use toast for footer "Press" links? Avoid stubs entirely: skip press links. Toast used when clicking "Notify" vs? OK: toasts used for: successful reserve (in addition to inline confirm — good reinforcement), and when trying to pre-order before... nah. Keep toast for reserve success only. Fine — it's wired, real.)

**Scroll reveal system**: 
```js
const io = new IntersectionObserver(entries=>{entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in'); io.unobserve(e.target);}})},{threshold:0.18, rootMargin:'0px 0px -8% 0px'});
document.querySelectorAll('[data-reveal]').forEach(el=>io.observe(el));
```
CSS: `[data-reveal]{opacity:0; transform:translateY(28px) scale(.98); transition: opacity .9s var(--ease), transform .9s var(--ease); transition-delay: var(--d,0s)} .in{opacity:1; transform:none}`. Respect prefers-reduced-motion: media query disables transitions/animations & reveals become visible (set opacity 1 in the media query), and JS checks to skip count-up animation (set final). Also for the sticky rotation with reduced motion: set θ mid value static.

**Sticky section math**: 
```js
const wrap = qs('#design'); const sticky = wrap.firstElementChild;
onScroll: rect = wrap.getBoundingClientRect(); total = wrap.height - vh; p = clamp(-rect.top/total,0,1);
theta = lerp(-30, 98, easeInOutCubic(p)); scale = 1 + 0.12·sin(p·π); y = ...
captions: for each stage i: c = band center; opacity = smooth falloff.
```
Also drive ghost word opacity/letter-spacing? Word crossfade via same opacity calc. Also progress bar width = p.

Perf: update via rAF loop tied to scroll (flag needsUpdate), and hero has its own rAF (idle bob). Combine: single rAF always running; hero updates only when hero in view; design updates when section near viewport. Fine.

Now let me carefully build the glasses renderer. Coordinate system: SVG viewBox "0 0 400 300" (design section larger "0 0 480 340"? Use same 400x300 and scale via CSS). Units: glasses total width ~ front 150 (rims r=30 at ±38? let me size: lens radius R=33, centers x=±40 → outer width = 2·(40+33)=146. Temples length L=120 going back. In side view, extent: hinge x'=0? hinge (±(40+33)=±73? Hinge should be at outer edge: (±73, -6). Temple tip z=-120: at θ=90: x' = x·0 - z·1 = 120 → extends 120 to one side +? Let me define rotation precisely:

rotateY by θ: 
x' = x·cosθ - z·sinθ
z' = x·sinθ + z·cosθ
Screen: sx = cx + x'·s·D/(D - z')·? with perspective factor pf = D/(D - z') where D=900 (z' toward viewer positive → pf>1 magnifies near points ✓).
sy = cy + y·s·pf.

Check right temple at θ=+90°: hinge (73,-6,0): x' = 73·0 - 0·1 = 0; z' = 73·1 + 0 = 73 (near viewer ✓ — right side rotated toward viewer for positive θ ✓ consistent with x'= x cosθ - z sinθ: point (1,0,0)→(cosθ,0,sinθ) z'>0 near ✓).
Temple tip (say (66, 4, -120)): x' = 66·0 - (-120)·1 = 120; z' = 66·1 + (-120)·0 = 66 → near?? z'=66 also near. Hmm at θ=90 both hinge and tip z'≈ hinge 73, tip 66 — temple nearly parallel to screen, extending to x'=120 (right side? x'=+120 → screen right). So at θ=90 we see: rims edge-on at center (x'= z·? rims at z=0: x' = x·0 - 0 = 0 → vertical sliver at center), temple from hinge (x'=0) extending right to x'=120 — wait hinge at (73,...) projects to x'=0? That's weird: hinge is at the outer edge of right lens; lens center (40,0,0) → x' = 40·cos90 - 0 = 0 too. All rim points x' = x·0 - 0·1 = 0 → entire rim plane collapses to x'=0 line ✓ edge-on. Temple spans x' 0→120 to the right — but physically the temple extends backward (−z), and after rotating 90°, backward (−z) maps to... x' = −z·sinθ = +120 → to the right. But we rotated the right side toward viewer, so the back of the glasses now points right. Temple from x'=0 to 120 on right, rim sliver at 0, viewer sees side profile ✓. Left temple (hinge (−73,−6,0)): x' = −73·0 − 0 = 0, z' = −73 (far). Tip (−66,4,−120): x' = 0 −(−120)=120, z' = −66. So left temple also spans x' 0→120 but far → hidden behind right temple ✓ overlapping exactly if same y — I'll offset left temple y slightly (+2) and it'll peek below — realistic (both temples nearly aligned). Painter order: left (z' −70) drawn first, rim (z' 0), right (z' 70) last ✓.

At θ=0: temples: tip z' = −120 → far; drawn behind rims ✓.

θ range −30 → 98: at −30°, we see slight left side? θ=−30: right side away. For hero maybe θ = +16° (right temple slightly toward viewer)? Whichever; param.

Temple geometry: hinge H=(hs·73, −10, 2), runs back: control points for slight curve down at ear: I'll build temple as polyline in 3D: P0 hinge (73, −10, 4); P1 (70, −7, −60); P2 (66, 2, −112); P3 ear bend (64, 26, −122); P4 tip end (62, 44, −118)? Ear hook goes down. Thickness ~5 tapering to 3.5. Render as two paths offset perpendicular in screen space? Proper: compute projected polyline, then build a ribbon with width w(t) using screen-space normals — 2D ribbon; looks fine (width in screen space constant 5·avgScale). Build ribbon polygon: for each point compute tangent, normal, offset ±w/2; path: down one side, back the other. Plus round cap via stroke-linejoin? Simple polygon ok; add slight rounding by using stroke on a centerline path with varying?? Can't vary stroke width. Ribbon polygon fine; ear bend with offsets can self-intersect slightly at sharp bend — use gentle bend angles.

Accent strip: segment of the ribbon between t=0.55..0.75 near hinge? "Halo beam" near the hinge/mid — place at t 0.15–0.45 (near hinge, visible in front-side views): draw as sub-ribbon along same centerline portion with amber fill, plus 3-4 tiny notch bars? For "speaking" animation in hero, vary amber segment opacity + a few dash marks. Simplify: accent = ribbon sub-segment amber; plus in hero, a small equalizer (4 bars) rendered near right temple tip? Overcomplex. I'll do: amber strip along mid-temple, with opacity animated by speech state (hero: pulses when caption "translates"; scroll: steady 0.9). Plus a tiny 2px LED dot at hinge? ok skip.

Microphone dots: 3 tiny dots along temple top edge + 2 on rim? skip (too small).

Rim rendering: for each lens (centers ±40, R=33): projected ellipse: center projects via formula; but rotation of a circle about Y through... the circle lies in plane z=0 centered (±40, 2). Rotating about Y-axis through origin: the circle maps to ellipse centered at projected center with rx = R·|cosθ_eff|... not exactly — the plane z=0 rotated by θ: circle in that plane projects (orthographically) to ellipse rx=R·cosθ? The circle's points (cx + R cosα, cy + R sinα, 0) → x' = (cx + Rcosα)cosθ - 0 = cx·cosθ + R cosα cosθ. So ellipse centered at cx·cosθ with semi-axes R·|cosθ| (x) and R (y) ✓ orthographic. With perspective pf varying per point (z'= (cx+Rcosα)·sinθ ≠ const) → ellipse slightly distorted. For fidelity, compute per-point: sample N=40 points around each rim, project each, build path with smooth curve (just polyline with many points looks smooth at N=40; or use path with L segments — at 40+ points it's smooth). I'll sample N=48 and use `L` — fine.

Rim as stroked ellipse-path: stroke width 4·pf-ish (use 4.2, maybe scale slightly with average pf). Fill none. Stroke color: metallic — use two strokes? A single path can have one stroke; to suggest metal: draw rim twice: outer stroke width 4.6 in darker tone, inner stroke width 2.6 in lighter tone (same path) → beveled edge look. Cheap, effective.

Top bar (brow): many smart glasses have a thicker top rim. Optional: draw second arc along top of each rim stroke-width 7 from angle 20°..160° → gives a brow-bar silhouette, more "tech glasses" and reads better at profile angles (brow edge visible). I'll add brow arcs: arc path (sampled angles −40°..220°? top half: angles from 200°..340°? define screen angles: top of lens is −90°... I'll param α from 0..2π with point (cx + R cosα, cy + R sinα); top = α = −90° (sin negative up if y down). Brow arc α ∈ [180+35? Let me just take α ∈ [195°, 345°] (through −90°). Compute via sampling same projection, path stroke width 7.5, round caps.

Lens glass: filled polygon of inner ellipse (sampled R−3), fill rgba tint, plus glint arc.

Bridge: sampled quadratic in 3D: points along from left rim point at α=−38°?? Bridge anchors: on each rim at angle pointing up-inward: α_bridge = −60°? Point on left rim: (cx + R cos(−60°)?) Let me define α measured standard math but y-axis downward in screen: to avoid confusion, define point(α) = (cx + R·cosα, cy + R·sinα) with screen y down. Top of lens = α = −90° (sin=−1 → y up ✓). Inner side of left lens = α=0 (cos=+1 → x toward center ✓). So bridge anchors: left α=−35° → (−40+33·0.82, 2−33·0.57)=(−13, −16.8); right α=−145° → (40−27, 2−19)=(13,−17). Bridge path: cubic from (−13,−17,0) with control points raised: C1 (−6,−26,−1), C2 (6,−26,−1) to (13,−17,0) → arch. Stroke width 5. Round caps. Keyhole: also small second arc below? Keep single arch + nose pads below: pads at (±11, 10, −5): small ellipse rx3 ry5 rotated ±20°, fill lighter.

Camera dot: at outer-top of each rim: α: left α=−125° (outer-top: cos negative → x more left ✓ sin −0.82 up): point (−40−19, 2−27) = (−59,−25). Draw circle r=2.2 fill #1a1a1c stroke amber 0.8? Amber ring indicates camera — meaningful accent. Small.

Lens glint: arc α ∈ [−140°,−70°] on left lens, radius R−6, stroke rgba(255,255,255,.5) 1.4px — but glint should be on the lit side consistent with light top-left: put on both lenses upper area α ∈ [−150°,−95°]. Fade with rotation.

Now shading values:
- θ in degrees. rimLight = clamp(cosθ): front stroke color = mix(#3a3a3e → #6b6b70?) Titanium on dark hero: strokes lightish gray #8E8E93-ish? On light section, rim darker? Renderer takes palette param: {rim, rimHi, lens, temple, templeHi, accent, line}. Hero (dark bg): rim #B9BCC2? Metal bright against dark ✓. Light section: rim #4A4A4F darker for contrast. Pass theme.
- temple fill: base temple color darkened by orientation: tLight = 0.62 + 0.38·clamp(sinθ_signed?) For right temple outer face visible when θ>0? The ribbon is screen-space; shading fake: brightness = 0.55+0.45·|cos(θ)| for front-facing-ness + slight difference per temple (near temple lighter). I'll do: near temple (higher z') gets +0.12 lightness.

Colors: titanium: temple #7A7D83 base; compute lightness via helper that lerps between #595B60 (shadow) and #A6A9AE (lit) by factor. Rim similar family. Lens tint: dark sections rgba(190,205,215,0.16)? On light: rgba(60,70,80,0.10) + slight amber? Smoke gray fine. Accent amber #E2A44E / on light #C98A2E.

Sorting painter: elements with depth = avg z': temples computed; rimFront group depth: use z' of rim centers (0)… but brow arcs same plane. Lens glass slightly transparent: draw after far temple but before near temple — group order: [farTemple, nosePads, rimGroup(rim strokes, lens fill, glint, bridge, camera), nearTemple]? But at θ near 0, both temples far (z'≈−65·cosθ...) both behind rim ✓ both drawn first. At θ=98: left temple far ✓ first; rim middle; right temple near last ✓. But nosePads at z=−5: when θ=98, z' = x·sinθ = ±11 → one near one far; minor—draw pads inside rimGroup; slight incorrectness invisible.

But wait: at θ>90, the viewer sees the BACK of the glasses: rim drawn same (symmetric), bridge behind lenses?? At back view, bridge is on far side (bridge z=0 plane same). Symmetric enough — fine. Camera dots: they're on front face (z=+2?). If I put them at z=+2.5, at back view they should be hidden behind lenses: add to depth sort? Simpler: keep at z=0 within group; when |θ|>90 they'd incorrectly show — meh, they're 2px. Alternatively fade camera dots out for |θ|>75. Easy: opacity = smoothstep(|θ|, 60→85 →1→0). ✓.

Also the right-temple at θ>90: we see left temple near... symmetric ✓.

Halo ring behind glasses (hero): separate static SVG ellipse, CSS-rotated ring group: an ellipse rx 260 ry 60? Positioned behind glasses tilted like an orbit: draw ellipse with rotation transform rotate(-8°). Ring: full ellipse stroke rgba(255,255,255,.10) 1px + progress arc: stroke amber gradient?? — avoid gradients: solid amber rgba(226,164,78,.9) arc via dasharray (len 90 of total) with CSS animation dashoffset orbiting. Since it's an ellipse, pathLength trick: set pathLength="100" then dasharray="12 88" and animate stroke-dashoffset 0→−100 linear infinite → arc travels around ellipse ✓ elegant. Second fainter arc offset. Slow: 14s. Also rotate whole ring slowly? The dash movement suffices. This ring sits behind the glasses — the halo ✓. In scroll section, ring appears faintly too? Maybe only hero + final CTA. Keep hero + CTA.

Ghost words in design section behind glasses: absolutely positioned huge text (font-size ~ clamp(120px, 22vw, 300px), font-weight 700? Apple uses huge bold). Color rgba(17,17,17,0.045) on light bg. Three words crossfading via JS opacity from stage bands. Words: "TITANIUM", "24 g"?? Words: stage1 "TITANIUM" (frame), stage2 "SOUND" (beam array), stage3 "SIX MICS"? Use "TITANIUM" / "ACOUSTICS" / "AWARENESS"? Copy captions:
1. "Grade-5 titanium. 24 grams." — "The full frame — rims, bridge, hinges — machined from a single billet. You notice it the first minute. Then never again."
2. "Sound that points at you." — "A beam of ultrasonic sound, aimed from the temple to your ear. Everyone around hears silence."
3. "Six microphones. One voice." — "An array of six mics isolates the person in front of you from everything else — then Halo translates them as they speak."
Stage word: "TITANIUM" / "DIRECTED SOUND"? words as single: "TITANIUM" / "BEAM" / "SIX". Hmm: 1 "TITANIUM", 2 "SOUNDBEAM"? "BEAMFORMED"? I'll use: "TITANIUM", "DIRECTIONAL", "SIX MICS"? Two words ok. Keep font-size responsive so it doesn't overflow: white-space nowrap, centered, overflow hidden on section.

Stage captions band functions: for stage i centers p_i = (i+0.5)/3, width 0.33: opacity = clamp(1 − |p−p_i|·6, 0, 1)·? with easing: use cos falloff: o = max(0, cos(π·|p−p_i|/0.42))^1.5? I'll compute o = clamp(1−(|p−p_i|/0.30), 0,1) then smoothstep. Also captions translateY slight (o drives transform translateY((1−o)·14px)).

Sticky section background: light #F4F2EE. Glasses palette darker. Ground shadow div under glasses.

Also small "Design" kicker at top of sticky viewport: "Design" small caps + progress hairline. Place top-left with stage index "01 — 03"? I'll add kicker top-center: "DESIGN" letterspaced, plus right side "0i/03" updated. Nice detail.

**Numbers section triggers**: IO once, animate each stat with rAF over 1400ms easeOutCubic; values: 43 (languages, "understood offline + cloud"? label "languages. spoken, signed, alive."), Let me define stats:
- 43 — "languages translated live"
- 24 — "grams on your face"  (unit g)
- 36 — "hours of translation, case included" (unit h)
- 0.28 — "seconds from speech to whisper" (unit s)
Format decimals: for 0.28 use toFixed(2) with counting.

Also a heading for the section: "The numbers / quietly absurd." Apple-esque: kicker "BY THE NUMBERS" + line "Small numbers. Big ones." Keep heading: "Obsessive, measured." with sub. I'll write: kicker "SPECIFICATIONS", H2 "Numbers we're / quietly proud of."

**Copy for features**:
Feature 1 (span7) "Instant, both ways": icon: arrows-left-right with wave. Copy: "Halo listens to the person in front of you, translates in 0.28 s and whispers it in your ear — in a voice that sounds like yours. When you answer, it speaks for you, in their language, out loud." Demo: transcript loop.
Feature 2 (span5) "Private by physics": icon ear/lock? icon: sound waves into ear. Copy: "Sound is beamed to your ear canal — nowhere else. The person beside you hears nothing; even you barely do. No earbuds, no seals, no 'can you hear me?'."
Feature 3 (span5) "Six microphones, one voice": icon mic. Copy about beamforming + wind. Demo: mic array animation.
Feature 4 (span7) "Works when the signal doesn't": icon wifi-off/globe. Copy: "A neural engine in each temple runs translation on-device in 26 languages. Airplane mode, mountain cabins, metro dead zones — the conversation doesn't care." Demo: toggle airplane → list count changes 26↔43? Wait offline 26, total 43. Toggle: OFF→"43 languages · Halo Cloud", ON→"26 languages · on device". Numbers flip animation (count between 26/43).

Banner strip after grid: "And under it all — Halo is simply a beautiful pair of headphones. Music, calls, podcasts. 40 hours of it." with music icon. Full width hairline strip, italic? Keep as slim centered statement with icon. Maybe skip to reduce clutter? It adds warmth; keep, small.

**Compare rows**:
| | Halo | Halo Pro |
Price: $349 / $499 (pre-order)
Weight: 24 g / 26 g
Battery (with case): 30 h / 36 h
On-device languages: 12 / 26
Total languages: 43 / 61?? Hmm earlier hero says "41 languages"? Pick consistent: total languages 43 both? Make Pro have more: Halo 43, Pro 43? Differentiator: "Live captions on lens"? No display in our design (no AR display mentioned—our glasses have no display; keep audio-only translator. So rows: Price, Frame (Anodized aluminum / Grade-5 titanium), Weight (24g/26g), Battery (30h/36h), Microphones (4/6), On-device languages (12/26), Speaker (Beam array / Beam array ×2 directional?), Water resistance (IPX4 / IPX4 + IP68 case?), Finish colors (Graphite, Bone / Graphite, Bone, Titanium raw?). Keep 7 rows: Price, Weight, Battery w/ case, Mics, On-device languages, Frame, Finishes. Tag on Pro: "For the polyglot" vs Halo "For everyone"? Header small sub: Halo — "The essential Halo"; Pro — "Everything, everywhere." Recommended middle: highlight Pro column with subtle bg rgba accent 0.05 + tag "Most popular".

Buttons: "Pre-order — $349" ghost style; Pro: solid amber. Click → set model, update CTA section pills, smooth scroll, maybe toast "Halo Pro selected". I'll include toast on selection — nice feedback ✓ (justifying toast system).

**Pre-order finale**: dark; layout centered: small halo ring motif again (small SVG ring above heading), H2 "Be first in line.", sub copy, model segmented control (two pills, selected state amber), email form (input + button), inline error, success state, microcopy "No payment now. We'll email you the moment your size ships. Cancel anytime." Plus mini row of trust items? skip.

Footer inside dark area bottom: hairline, left: halo mark + "Halo © 2025", middle links anchors, right "Designed in Copenhagen · Worn everywhere". 

**Nav details**: left: mark (SVG: two arcs forming halo + wordmark "Halo" in 600). Center links (hide on mobile): Design, Features, Specs, Compare. Right: "Pre-order" small pill (amber solid). Blur bg after 40px scroll: class toggled. Also nav text color must adapt over dark & light sections: tricky. Options: mix-blend-mode: difference (hacky), or: keep nav always dark-glass (dark translucent bg) — over light sections a dark frosted bar looks fine (Apple uses dark bars on light pages sometimes? They adapt). I'll make nav pill-style: nav content in a floating rounded capsule with dark translucent bg + blur — works on both. Actually full-width bar with background rgba(10,10,11,0.7) + blur always (not just after scroll) — consistent, readable everywhere. Add hairline bottom border rgba(255,255,255,.08). On load over hero (also dark) seamless ✓. I'll do always-frosted dark — simple & robust. Hmm, over the light sticky section a dark bar is heavy... Apple's approach: the product page nav is translucent white with blur and adapts text via... they switch per theme with JS scroll detection. I can do theme detection: observe which section under nav via IO with rootMargin top band; toggle `nav.light` → background rgba(250,250,248,.65), text dark. That's a nice craft detail. Implement: IO on sections with rootMargin "-0% 0px -100% 0px"? Standard trick: rootMargin: '0px 0px -92% 0px' threshold 0 → fires when section top crosses top band. I'll compute in scroll handler instead: check element under point (document.elementFromPoint? costly). Simpler: sections have data-theme; on scroll find current section via offsets (cached). Use scroll listener with binary/linear scan (few sections, cheap). Set nav class accordingly + smooth transition of colors (transition background .4s). ✓.

Anchor smooth scroll: CSS `html{scroll-behavior:smooth}` + scroll-padding-top: 70px.

**Fonts**: stack: `font-family: "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Helvetica, Arial, sans-serif;` fine — system fonts per user's request (user explicitly asked system fonts, so the no-system-ui-as-primary instinct yields to the explicit request; I'll still add character via tracking/weights). Numerals: font-variant-numeric: tabular-nums for counters.

Letter-spacing: h1 -0.035em; eyebrows 0.22em uppercase 11px; body 17px/1.6.

**Colors**:
- Dark bg: #0A0A0B (near black), section-2 dark slightly different #101013? Keep same; separators hairlines.
- Light bg: #F4F2ED (warm paper), cards/cells white #FBFAF8? cells same bg with hairlines.
- Text dark sections: #F2F1EC primary; muted #A6A29A (warm gray, contrast on #0A0A0B ≈ 6.8 ✓).
- Text light: #1B1A17 primary; muted #6E6A61.
- Accent amber: #E4A94F (dark bg), light sections #B07A24 for text-accent (contrast), fill accents #D99A3A. Define per theme via CSS vars on .dark/.light containers. Amber pill button on dark: solid #E4A94F with near-black text ✓ strong. On light: solid #171717? Hmm buttons: primary CTA = amber solid w/ dark text (both themes, amber works on light too with dark text). Secondary = ghost hairline.

This amber-on-black + warm paper palette feels premium (Leica-ish), definitely not default blue/purple ✓.

**Hero details**: 
- top padding for nav; content column centered, text-align center.
- eyebrow: "INTRODUCING HALO" with small ring icon inline.
- H1: two lines: "Every word." / "Every language." Hmm "Every word, in every language." then amber italic? Let me refine: H1: "Speak / anything." too terse. Apple pattern: "_____________. ____________." e.g. "Hear the world. In your language." I'll go: line1 "Every language." line2 "In your ear." — punchy, product-true. Sub: "Halo translates live conversations as they happen and whispers them to you — naturally, instantly, in a voice like your own. No phone. No pauses. No awkward nodding."  That last bit has personality ✓.
- CTAs: [Pre-order — $349] [See how it works ↓] (anchor #design; label "Explore the design").
- Glasses visual with halo ring + reflection floor? subtle shadow ellipse.
- Ticker below glasses; scroll cue at bottom center: "Scroll" + animated line growing.

Hero entrance animation on load: headline lines rise with stagger (CSS animation on load, class added after DOMContentLoaded), glasses fade/scale in, ring draws (stroke-dashoffset animation on the base ellipse too? base full ellipse can draw in via dashoffset once). Nice.

Ticker implementation: div.live: [LIVE dot] [lang tag] [native text] [→] [english text]; cycle via JS: build items array; every 3.2s: add .out (fade/slide down), after 350ms swap content + .in. Also sync amber strip pulse on glasses: when item switches, set speechPulse=1 decaying — hero renderer reads it. 

Hero glasses idle: rAF: θ = base + sin(t·0.5)·2.5°, y float sin(t·0.8)·6, speech pulse. Redraw each frame — renderer builds ~200 path points; fine perf-wise (string building 60fps ok for one SVG).

Reduced motion: skip rAF idle (render once at base θ).

**Design sticky sizing**: glasses SVG width min(78vw, 640px). viewBox 400×300 scaled — ensure temples extend within: at θ=90 temple x' spans 0..120 + hinge y — but perspective pf for tip z'=66: pf=900/(900−66)=1.079 → x'·pf: 120·1.08=130 from center → viewBox half-width 200 ✓ fits. Rim outer 73·1=73 ✓. Vertical: temple ear hook down to y=44+? sy = cy + 44·pf ✓ within 150 half-height. At θ=−30: rim ellipse rx 33·cos30=28.6, temple tip x' = 66·cos(−30) −(−120)·sin(−30) = 57.2 −(−120·−0.5)=57.2−60= −2.8; z' = 66·(−0.5)+(−120)(0.866) = −33−103.9=−137 → pf=900/1037=0.868 → x≈−2.4, y tip 4·0.868. Temple behind ✓. Rim front center x' = ±40·0.866=±34.6 pf=1 ✓.

Bridge stroke 5 → fine.

Also draw subtle hinge blocks: small rect at hinge points (projected), width 6 height 9, rounded — connects rim to temple ✓ realistic. Add as part of temple path start (a quad). I'll add small circles r=3.5 at hinge projected points, fill rim color — hinges ✓.

**Now the mic demo SVG**: viewBox 0 0 320 150. Draw: stylized glasses front outline (reuse simple path: two arcs + bridge, stroke #999 thin) at bottom center; 6 mic dots along top edge positions: xs = [70,100,130,190,220,250]? Symmetric around 160: [64, 96, 128, 192, 224, 256] y = 108 (along brow) + two on temples? Place 6 dots on brow arc: y varies: [112, 104, 100, 100, 104, 112]. Speaker: moving dot along path below: x from 40→280 sinusoidal y 40+... speaker at (sx, 46 + 10·sin(t)). Active mic = argmin distance; beam: line from active mic to speaker, amber, opacity .8; mic dots: near ones (dist<70) scale/glow amber. Loop t; also faint "wavefront" arcs from speaker: 2 expanding circles (radius animates) — nice. Pause when off-screen (IO).

**Transcript demo**: container fixed height (~190px) lines list; JS loop: script = [ [Aya·日本語, 「…」], [You·English, "…"], ... ] Actually both directions: pair lines: Aya speaks Japanese → shows Japanese line (what Aya said, small) + below it? The glasses whisper English — show as "Halo → you: …"? Design: two-party transcript: left-aligned lines = them (original), right-aligned = you. Each line chip: bg hairline bubble? bubbles feel chat-app; Apple transcript style: rows with speaker label small caps colored dot + text. Sequence: line appears (translateY fade). After 4 lines, pause, clear, restart. Also a mini "wave" indicator at bottom? Keep 4 lines loop:
1. THEM · 日本語 — 「会議、何時からだっけ？」
2. YOU · English — "What time did we say the meeting was?" (this is what you HEAR: as your line? You speaking English shown as-is)
Better narrative: show original + translation stacked: THEM: 「会議…」 → immediately a second row styled amber-tinted: "What time did we say the meeting was?" Then YOU: "Three o'clock — room 2." → THEM· 日本語 translation row: 「三点。二階の会議室。」 — wait you spoke English; Halo speaks Japanese aloud to them; the transcript shows your English + their view translation. Rows: [flag-less lang tag] text. 6 rows cycle. Loop with clearing. Height fixed to avoid layout shift ✓.

Implementation: setInterval-ish via rAF timer or chained timeouts; only run when visible (IO). Append rows with class .row.in; keep max 6 then after delay fade all, empty, restart.

**Offline toggle demo**: a styled switch (button role switch aria-checked) + two stat texts: big number 26/43 with animated flip (count transition via JS quick count) + label "languages · on device" / "languages · with Halo Cloud". Small print under: "Neural engine: 11 TOPS, both temples." Toggle animates knob. Default ON? Default OFF (cloud 43), toggle to airplane → 26. Icons: cloud / airplane inline SVGs.

Now, code size: substantial but fine. Let me be careful with correctness — everything must work. Let me write the renderer pseudocode concretely:

```js
const P = { D: 950 };
function proj(p, th, cy, s){ // p:[x,y,z], th radians
  const c=Math.cos(th), sn=Math.sin(th);
  const x = p[0]*c - p[2]*sn;
  const z = p[0]*sn + p[2]*c;
  const pf = P.D/(P.D - z);
  return [200 + x*pf*s, cy + p[1]*pf*s, z];
}
```
viewBox 400×300, cx=200, cy configurable (~132 so glasses sit slightly high; temples hook down). scale s=1 (design coordinates already sized). For smaller render (compare header), same svg scaled via CSS width ✓ (vector).

Color helpers:
```js
function mix(a,b,t){...} hex to rgb lerp.
```
Palette passed: {rim:'#C7C9CE', rim2:'#8E9095', brow:'#B4B6BB', temple:'#83868C', temple2:'#5E6066', lens:'rgba(...)', glint, accent:'#E8B45A', cam:'#...', pad}
I'll compute shaded variants in renderer using light factors.

Elements builder:
- rim(cx) samples: for a in 0..48: ang=a/48*2π; pt=[cx+33cos, 2+33sin, 0] — but add slight panto: scale y by 1.04 below center? keep circle.
- two strokes: path outer (stroke rimDark 4.8) then same path stroke rimLight 2.4 → bevel.
- brow: ang from π+0.55 to 2π−0.55? Top semicircle-ish: angles where sin<... top means y small: sin(ang) negative → ang∈(π, 2π). Take ang ∈ [π+0.45, 2π−0.45] i.e. 180°+26°..360°−26° → covers top excluding near horizontal ends? Ends at horizontal-ish (26° below horizontal on each side)... Actually I want brow covering top from left-horizontal to right-horizontal: ang from π to 2π exactly (through 3π/2 top). Slight extension: [π−0.15, 2π+0.15]. Stroke width 7, round caps, color browDark mix. Also brow bevel: second pass width 3 lighter.
- lens: inner radius 29 sampled, fill lensFill; glint arc ang [π+0.5? upper-left of left lens: upper = ang∈(π,2π); left part for left lens means ang near π..3π/2? For LEFT lens, outer side is left (ang π). Glint upper-left: ang ∈ [π+0.25, 3π/2−0.25]?? 3π/2 is top. Upper-left arc: ang from π+0.2 to 3π/2+... hmm for left lens glint on upper area spanning inward: ang ∈ [π+0.2, 2π−0.6]?? that's most of top. Fine: glint arc ang ∈ [π+0.35, 3π/2+0.35]... I'll simply use top arc slightly biased: start 200° end 300° (in 0..360 with top=270°): ang from 3.6 to 5.4 rad (206°..309°) — covers upper arc ✓. For right lens mirror: 3.0 to 4.9? keep same range for both, symmetric-ish is fine (light from above).
- bridge: pts cubic sampled 12: P0(−12.5,−16.5,0) C1(−5,−27,−1.5) C2(5,−27,−1.5) P1(12.5,−16.5,0). Stroke 5 round cap + lighter 2.
- pads: ellipse at (±10.5, 11, −5), rx3.2 ry5.4, rotate ∓18°, fill padColor opacity ~0.9·cosFade.
- camera dots: left at ang 215°? outer-top of LEFT lens: outer = left = ang π side; top=270°: 235°→ point (−40+33cos235, 2+33 sin235) = (−40−18.9, 2−27) = (−58.9, −25). Right: ang 305°: (40+18.9, 2−27)=(58.9,−25) ✓ symmetric. circle r2.3 fill #14140f stroke accent .9 width .8, opacity camFade.
- temples: right temple 3D centerline: 
  pts = [[73,−9,3],[71,−7,−38],[68,−1,−86],[65,10,−114],[63,30,−124],[60,46,−118]] (ear hook). widths along: [7,6.4,5.6,5,4.4,3.6] (half-widths? full). Build ribbon: project pts; for each i compute dir = normalize(p[i+1]−p[i]) (screen), normal = (−dy,dx)/len; offset ±w/2·(pf avg?). Path: M left side pts then reversed right side, Z. Fill templeShade. Plus accent strip: sub-ribbon between indices 1..3 offset slight outward (draw after base, fill accent with opacity speech). Also hinge cap: circle at pts[0] r 4 fill rimDark? Temple hinge behind rim: draw before rim? Depth sort handles: temple depth = avg z' of pts ≈ (3−38−86−114−124−118)/6 ≈ −79.6 (θ=0) → far behind rim(0) ✓ drawn earlier. At θ=90: pts z' = x·sin90 = 73,71,68,65,63,60 → avg 66.7 near ✓ last.
  Left temple mirrored x → −x, with y +1.5 offset, z shifted −3 (peek). Its accent same.
  
  Ribbon widths: multiply by avg pf of segment? Screen-space constant fine.

- Also temple inner edge line: stroke along centerline 1px darker for definition.

Shading factors:
- faceLight = 0.5+0.5·max(0,cos θ) for rim front brightness? At θ=0 lit fully; θ=90 edge — rim strokes shrink anyway; brow similar.
- Right temple lit factor: lr = 0.55+0.45·clamp(sin θ?, ) — when right temple faces viewer (θ>0) its outer face is lit? Light from front-top-left: outer face of right temple normal +x rotated: n=(cosθ,0,sinθ); light dir L=(−0.4,0.7,0.6) normalized-ish; lum = max(0, n·L)= (−0.4cosθ + 0.6 sinθ). For θ=90: 0.6 lit ✓ (right temple toward viewer lit). θ=0: −0.4 → 0 → dark: at front view temples point away, we see inner faces? n·L with n=(cosθ..)... inner face normal −x: lum=0.4 → mid. I'll compute per temple: near-side face lum via |component| mix. Simplify: temple lum = 0.45 + 0.55·clamp01(0.5+0.5·sin(θ)·side)+... I'll just do: right temple: f = clamp01(0.35 + 0.35·Math.sin(th) + 0.3·Math.cos(th)) hmm ensure θ=0 → 0.65, θ=90 → 0.65... I want front view temples slightly dark (they're behind), side view near temple bright: f_right = 0.45+0.5·max(0,sin θ) + 0.15·max(0,cosθ). θ=0 → 0.6; θ=90 → 0.95 ✓; θ=−30 → 0.45−0+0.13=0.58. Left temple mirrored: f_left = 0.45+0.5·max(0,−sinθ)+0.15·max(0,cosθ). Then templeColor = mix(templeDark, templeLit, f). Fine.

Rim color: mix(rimDark, rimLit, 0.55+0.45·cosθ·?) front-facing brightness: f=0.5+0.5·|cosθ| → θ=0 1.0, θ=90 0.5 (edges darker ✓).

Lens opacity: base 0.16 + 0.10·|sinθ|? At edge-on lens nearly invisible anyway (fills collapse) ✓ keep constant.

OK. Also overall rotation sign in design section: I want temples to sweep nicely: from θ=−24 (slight left-cheek view? shows right temple going away-left?) Let me sanity check θ=−24: right temple tip: x' = 66·0.913 − (−120)(−0.407) = 60.3 − 48.8 = 11.5; z' = 66·(−0.407) + (−120)(0.913) = −26.9 − 109.6 = −136 (far). So right temple mostly hidden behind rim, tip poking slightly right — looks like glasses slightly turned with left side toward viewer: left temple: tip x' = −60.3 − 48.8 = −109?? wait left temple tip x=−66: x' = −66·0.913 − (−120)(−0.407) = −60.3 − 48.8 = −109.1, z' = −66·(−0.407)? z' = x sinθ + z cosθ = (−66)(−0.407) + (−120)(0.913) = 26.9 − 109.6 = −82.7 (far, less far). Left temple extends to screen-left ✓ visible going back-left. Looks like 3/4 view from left ✓. Good: θ=−24 shows left side; θ=+90 pure right-profile... sweep from −24 → +98 passes front (0) → right 3/4 → profile. Motion: starts slightly left-turned, rotates through front to right profile — nice long arc ✓. Actually direction check θ increasing: at −24 left temple visible left; at +24 right temple visible right; at 98 profile. Great sweep ~120°.

Ease: apply easeInOut on p for theta but keep captions on raw p bands (so captions sync with visual roughly—use eased p for both, fine).

Also add slight rotateX over scroll: tilt = sin(p·π)·4° → pitch: implement pitch as y-scale? Proper pitch rotation: rotate about X: y' = y·cosφ − z·sinφ; z2 = y·sinφ + z·cosφ. Add φ small (−3°..+5°). I'll include φ in proj: compute after Y-rotation: y' = y·cosφ − z·sinφ etc. Add param.

Now hero renderer variant: opts {theta: 14°+sway, phi: −6°, speech} palette dark. cy maybe 150 within its own viewBox 400×280? Use same viewBox 400×300 for consistency, CSS sizes differ.

The compare header minis: static: drawGlasses(svg, {theta: 10°, palette}) once. Pro: palette rim darker gunmetal + accent ring? Pro distinguishing at a glance: add thin accent ring around lenses? I'll add opt `proRing`: draw thin amber ellipse ring (radius R+6) around each lens — a signature "halo etched ring" on Pro. Tasteful ✓. Also Pro brow slightly wider? fine just ring + darker titanium.

**Nav mark SVG**: circle arc: `<circle r="7" stroke amber dasharray>` simple ring with gap + dot. Wordmark text "Halo" font-weight 600 letter-spacing −0.01em.

**Now let me also handle the "features" and other sections' reveal attributes** with staggered `--d`.

**Potential pitfalls**:
- Sticky section on mobile: 320vh + big SVG — ensure captions overlay bottom on small screens (position absolute bottom, text center). Ghost words smaller (18vw). Overflow-x hidden globally to prevent stray overflow (huge ghost text!) → html,body overflow-x:hidden? body overflow-x clip. Ghost text centered with white-space nowrap and font-size in vw scaled to fit: "TITANIUM" 8 chars ~ 0.62em/char → width ≈ 5em → font-size ≤ 100vw/5 ≈ 20vw. Use 16vw. "DIRECTIONAL" 11 chars → 12vw. "SIX MICS" 8ch → 15vw? Set per-word size via inline style. OK.
- iOS 100vh: use min-height:100svh where supported, fallback 100vh.
- scroll-behavior smooth + JS scrollTo for buttons with behavior smooth ✓.
- The design section height 320vh on mobile maybe 260vh.
- Performance: single rAF; in each frame update: hero (if within viewport ±), design (if in range), mic demo (if visible), ticker handled by timeouts. Counters run on their own temporary rAFs.
- innerHTML rebuilding SVG per frame: hero svg + design svg — string ~4-6KB each, fine.
- text rendering: use `shape-rendering` default; geometricPrecision ok.

**Copy polish** — write with restraint and wit, Apple-ish cadence. Avoid em-dash overuse? I'll use sparingly. (No constraint given about em dashes; just write well.)

Headings per section:
- Design sticky kicker: "DESIGN"
- Features: kicker "CAPABILITIES", H2: "Fluent is the / default setting."? Better: "It doesn't feel like / technology." sub: "No screen to stare at. Nothing to unlock. Halo disappears into the conversation." 
- Numbers: kicker "BY THE NUMBERS", H2 "Obsession, / quantified."
- Compare: kicker "TWO MODELS", H2 "Which halo / is yours?" Hmm — "Halo, or Halo Pro." as H2: "Halo. Or Halo Pro." clean ✓.
- CTA: H2 "Be first / in line." sub: "Reserve now with just an email. Pay when it ships — spring 2026."

Wait: invented product, "Ships spring 2026" fine.

Hero H1 final: line1 "Every language." line2 "In your ear." — I like it. Eyebrow "INTRODUCING HALO". Sub as before. Stats mini-row under sub? skip.

**Section order & ids**: hero #top, design #design (sticky), features #features, numbers #numbers, compare #compare, preorder #preorder, footer.

Nav links: Design, Features, Numbers? "Specs", Compare. 

**Light/dark mapping**: hero dark; design light; features light (bg slightly different: design #F4F2ED, features #FBFAF7 to delineate? Both light but distinct surfaces ✓); numbers dark (#0B0B0C); compare light (#F4F2ED); preorder dark (#0A0A0B). Nav theme flips accordingly.

**Buttons**: pill radius 999. Primary: bg amber, color #1A130A, hover: brightness up + translateY(-1px), active scale .98. Ghost: 1px hairline border, text primary, hover bg subtle. Focus-visible outlines ✓ accessibility.

**Form**: input dark bg #17171A, hairline border, radius 12, padding; button attached right (flex). Error text amber-red? Use #E5766B? On dark. Shake animation on error.

**Toast**: bottom center card: dark elevated #1C1C1F, hairline, icon check amber, slide-up; role="status".

Let me now also plan the numbers formatting and layout responsiveness: stats flex with wrap; each stat min-width ~200px; separators via border-left hairline (skip on wrapped — acceptable, or use gap and borders always: on wrap it looks odd; use column layout on mobile with border-top hairlines). Manage with media query.

**Comparison table implementation**: 
```html
<div class="cmp">
  <div class="cmp-head"> (3 cells: empty, halo render+name+sub+btn, pro render+name+tag+btn)
  <div class="cmp-row"> label / value / value (×7)
```
Grid: grid-template-columns: 1.1fr 1fr 1fr; hairline via gap:1px background technique? For header spanning: I'll build as CSS grid with all cells in one container, gap 1px, container bg hairline color, cells bg surface → grid lines everywhere including header ✓. Column highlight: Pro column cells get class bg tint rgba(217,154,58,0.06). Rows hover: cell brightness? subtle: on row hover, label+values bg shift — implement with JS? Use CSS :has? `cmp-row:hover .cmp-cell` if rows are subgrids... If I use single grid with row wrappers (display:contents), hover works: .cmp-row{display:contents} .cmp-row:hover .cell{background:...} — display:contents removes the row box but hover on children still triggers via row wrapper? Hover on wrapper with display:contents — pointer events pass to children; :hover on display:contents element: spec says it doesn't generate boxes; browsers... :hover generally doesn't apply (no box). Instead make each row its own grid with 3 cols and container stacks rows with 1px gaps via borders: rows border-top hairline. Simpler: each row `display:grid; grid-template-columns: 1.1fr 1fr 1fr; border-top:1px solid hairline`. Header also grid with same cols (so columns align — fr units same → aligned ✓ as long as same column definition and table width equal). Highlight column: apply class to value cells `.is-pro` background tint + on hover row `.row:hover .cell{background:var(--hover)}` ✓ works.

Mobile (<720px): header grid: 2 cols (hide label spacer); rows: grid-template-columns:1fr 1fr; label cell becomes full-width spanning 2 (order?) Hmm: label should appear above the pair: make label cell grid-column: 1/−1 as small heading, values side by side with ::before data-label? If label spans full width we don't need data-labels ✓ simpler: label cell becomes a small section heading row. So each row: label (span 2, small caps muted) + value + value ✓ nice mobile pattern.

**Success/check icon**: inline SVG circle+check.

**Airplane toggle** default: I'll set initial OFF (cloud, 43). Toggling ON: airplane mode → number counts down 43→26 and label swaps; OFF: back up. Count animation 500ms.

Number flip: simple textContent update with quick rAF count.

**Wave/pulse in transcript**: rows appear with width? no—fade+translate. Speaker dot colors: THEM = gray, YOU = amber. Language tags small caps.

Alright — also "no images" ✓ all SVG/CSS. No external anything ✓. 

**Let me now write out the actual geometry constants and double-check projections numerically for a few key values** (viewBox 400×300, cx=200):

Constants: R=33, lensCx=±40, lensCy=2, temple pts as above. cy param: I'll set cy=138 for design (glasses slightly above center, room for ear hooks at bottom), hero cy=150.

θ=0, φ=0: rim left center → (200−40, 140) pf=1 ✓. rim ellipse rx33 ry33 → spans x 127..273? left lens 127..? left lens x: 200−40−33=127 to 200−40+33=193; right 207..273 ✓ total width 146 ✓ centered. Temple hinge right (73,−9,3): x'=73, z'=3, pf=950/947=1.003 → (273.2, 129) ✓ at outer top-ish (y=−9 → 138−9=129, hinge slightly above center ✓ realistic hinge at top outer). Tip (60,46,−118): z'=−118 pf=950/1068=0.890 → x=200+53.4=253.4, y=138+40.9=178.9 ✓ ear hook ends down-inward ✓ looks right.

θ=90°, φ=0: right hinge: x' = 73·0 − 3·1 = −3; z' = 73 → pf = 950/877=1.083 → x=196.7, y=128.2. Rim right lens center (40,2,0): x'=0−0=0? x' = x cosθ − z sinθ = 0; z' = 40 → pf 1.044 → x=200, y=140. Rim collapses to vertical band at x≈200 ✓. Temple tip (60,46,−118): x' = 0 −(−118)(1) = 118; z' = 60 → pf 950/890 = 1.067 → x = 200+125.9 = 325.9 ✓ within 400 ✓. y=138+49=187. Left temple tip (−60,46,−118): x' = 0 +118 = 118; z' = −60 → pf 950/1010=0.941 → x = 311, y ~181 — overlaps right temple (drawn under) ✓ profile view: temple extends right?? Hmm — profile facing right: at θ=90 we rotated right side toward viewer, so we're looking at the right temple from outside, glasses facing... the face direction: front (−z? or +z?) Front of glasses = toward viewer at θ=0 (z=0 plane faces +z viewer). At θ=90, front faces right (x' direction?) The front normal (0,0,1) → x' = −sinθ·1? x' = 0·cos − 1·sin = −1 → front faces LEFT (−x). So at θ=90 the glasses face left, temple extends right. Visually: facing-left profile. From θ=−24 (facing slightly... at θ=−24 front normal x' = −sin(−24)=+0.4 → faces slightly right) to θ=98 (front faces left past 90). Sweep: face starts slightly right-turned → rotates left through front → to left profile. Fine ✓.

But wait at θ=90 temple extends right while glasses face left — temples on the right side of image ✓ natural profile like looking at someone's head from their right? Eh — looks fine.

θ=98: cos=−0.139, sin=0.990. Rim: rx=33·|cos|≈4.6 → thin ellipse still visible (not zero, since 98≠90) ✓ slight open angle showing back? front normal x' = −sin98 = −0.99 (facing left). Right lens center x' = 40·(−0.139) = −5.6 (left of center), z' = 40·0.99 = 39.6 near. So we see the right lens slightly from behind-ish... right rim at x −5.6, left rim at +5.6: mirrored ✓. Temples: right tip: x' = 60·(−0.139) −(−118)(0.99) = −8.3+116.8=108.5; z' = 60·0.99 + (−118)(−0.139) = 59.4+16.4=75.8 → pf=950/874=1.087 → x≈317. Left temple: hinge x' = −73·(−0.139) − 3·0.99 = 10.1−3=7.2... fine, overlap as before ✓.

At θ=−24 with pitch φ=−4°: adds subtle life ✓.

Bridge at θ=90: bridge points z≈−1..0, x ±: x' = −z·1 ≈ 1 → collapses near center behind rim band — hidden ✓ good.

Nose pads at θ=90: (10.5,11,−5): x' = 0 −(−5)=5, z'=10.5 → visible slightly right of rim band — tiny pads floating; opacity fade via cosθ → at 90 →0 ✓ I planned padOpacity = clamp(|cosθ|·1.6). ✓

Camera dots fade |θ|>75° ✓ (at 98 hidden anyway since we see back).

**Ordering with brow/rim vs lens**: lens fill drawn first inside rimGroup, then rim strokes over ✓.

**Ghost words + captions overlap**: ghost word centered behind glasses (z-index 0), glasses z1, captions absolute left (z2). Desktop: caption block left ~8%, width 320px; glasses centered but shifted right slightly (translateX(6%))? Apple style: product center, text left. I'll center glasses, captions left overlay. Mobile: captions bottom center, glasses center up.

**Kicker/progress in sticky**: top center "DESIGN — 01/03" small; progress hairline 120px with fill width p·100%.

**Now write the code.** It'll be long (~1100+ lines). Let me structure:

```
<!DOCTYPE html><html lang="en"><head><meta charset><meta viewport><title>Halo — Every language. In your ear.</title><style>...</style></head>
<body>
  <div id="toast" ...>
  <nav>...
  <header id="top" class="sec dark hero">...
  <section id="design" class="sec light design"> tall wrapper > sticky stage: ghost words ×3, svg #gDesign, shadow, captions ×3, kicker+progress
  <section id="features" class="sec light features"> heading + grid (4 cells + demos) + banner
  <section id="numbers" class="sec dark numbers"> heading + stats
  <section id="compare" class="sec light compare"> heading + table
  <section id="preorder" class="sec dark preorder"> ring svg, h2, pills, form, success
  <footer class="dark">
  <script>...</script>
</body></html>
```

CSS variables:
```css
:root{
  --ease: cubic-bezier(.22,.61,.2,1); /* easeOut-ish */
  --dark:#0A0A0B; --dark2:#101013;
  --light:#F4F2ED; --light2:#FBFAF7;
  --ink:#1B1A17; --mut-l:#6F6A60;
  --paper:#F2F1EC; --mut-d:#A39F96;
  --amber:#E2A44E; --amber-d:#B37B26; /* for light bg text accent */
  --hair-d: rgba(255,255,255,.09); --hair-l: rgba(20,18,12,.12);
}
.sec.dark{ --bg:var(--dark); --fg:var(--paper); --mut:var(--mut-d); --hair:var(--hair-d); --acc:var(--amber);}
.sec.light{ --bg:var(--light); --fg:var(--ink); --mut:var(--mut-l); --hair:var(--hair-l); --acc:var(--amber-d);}
```
Sections use var(--bg) etc. features uses --bg light2 (override).

Typography:
- .eyebrow: 11px, ls .24em, uppercase, color var(--acc) w/ 600.
- h1: clamp(44px, 7.4vw, 96px), weight 640? system font weight 700 heavy; Apple uses 600-700. Use 650 via font-variation? System SF supports variable? Use 700 with tight ls −0.035em, line-height 1.03.
- h2 section: clamp(34px,5vw,60px) weight 700 ls −0.03em.
- body: 17/1.65.

Reveal CSS + reduced motion.

Hero layout: display flex column; center; padding-top 92px; min-height 100svh; hero-art container position relative height ~ min(46vh, 420px)? Let glasses SVG width clamp(320px, 44vw, 560px), halo ring svg absolutely centered larger. Ticker below.

Actually to guarantee full-screen composition: hero grid: rows [auto text][1fr art][auto ticker]; art svg centered with ring behind; ticker margin-top -something to tuck near glasses bottom. Keep simple stacked with negative margins.

The halo ring: absolutely positioned svg width 150% of glasses, top offset; behind glasses (z-index). It's an ellipse (perspective ring) around glasses: rx 46% ry 12%? Draw ellipse cx200 cy150 rx170 ry44 in 400×220 viewBox, positioned so it wraps glasses mid-height, slightly rotated −6°. Ring behind → glasses occlude bottom part? Ring should pass behind glasses fully (drawn behind) — a ring around would have front arc overlapping glasses bottom... simpler: ring entirely behind ✓ reads as halo ✓.

Also add tiny orbiting "signal" dot on ring? The dash arc suffices.

Ticker markup:
```html
<div class="ticker" id="ticker"><span class="live"><i class="dot"></i>LIVE</span><span class="tl" id="tLang">JA</span><span class="t-native" id="tNat">…</span><svg arrow>…</svg><span class="t-en" id="tEn">…</span></div>
```
Arrow inline svg small →.

Hero bottom scroll cue: absolute bottom center: "Scroll" 11px caps + 36px vertical line with scaleY anim.

Sticky design markup:
```html
<section id="design" class="design light">
 <div class="pin">
   <div class="ghosts"><span>…</span>×3</div>
   <svg id="gDesign" viewBox="0 0 400 300">
   <div class="shadow" id="dShadow">
   <aside class="stages"> 3 .stage blocks
   <div class="pin-top"> DESIGN · progress bar · counter
 </div>
</section>
```

Features grid markup with .fgrid gap 1px bg hair; cells .fcell bg var(--bg) padding clamp(28px,4vw,52px).

Demo A transcript:
```html
<div class="demo transcript" id="transcript"></div>
```
rows built by JS. Height 210px, overflow hidden, mask fade top? add mask-image linear-gradient — mask gradient functional ok.

Demo C toggle:
```html
<div class="demo air">
 <button class="switch" id="airSwitch" role="switch" aria-checked="false"><i></i></button>
 <div><span class="big" id="airNum">43</span> <span class="air-label" id="airLabel">languages · with Halo Cloud</span></div>
 <p class="fine">Neural engine: 2×11 TOPS, one in each temple. 26 languages fully offline.</p>
```
Wait numbers: cloud 43, offline 26. ✓

Demo B mic svg static parts + JS animated parts (ids).

Numbers markup: .stats > .stat ×4 each: .n (span num + unit), .label, hairline.

Compare markup as planned; renders: two inline SVGs #cmpHalo #cmpPro drawn once.

Preorder: ring svg small animated (same dash orbit), pills (two buttons .pill-model with aria-pressed), form.

Footer.

JS sections:
1. helpers (qs, clamp, lerp, mix colors, easing)
2. Glasses renderer
3. Instances: hero (rAF idle), design (scroll), compares (static)
4. Ticker
5. Scroll: nav theme + bg, design progress, parallax? reveal IO
6. Counters IO
7. Transcript demo, mic demo, air toggle
8. Compare buttons + model state + pills
9. Form validate/submit + toast
10. Reduced motion guards.

Let me carefully write the renderer function now in full detail (this is the crux):

```js
const GL = (()=> {
  const D = 950, N = 48;
  const R = 33, RC = 40, RCY = 2;
  // temple centerline (right side)
  const TPTS = [[73,-9,3],[71,-7,-38],[68,-1,-86],[65,10,-114],[63,30,-124],[60,47,-117]];
  const TW   = [7.4,6.6,5.8,5.2,4.6,3.8];
  
  function make(th, phi, cy, pal, opt={}){
    const c=Math.cos(th), s=Math.sin(th), cp=Math.cos(phi), sp=Math.sin(phi);
    const pr = p => {
      const x = p[0]*c - p[2]*s;
      let z = p[0]*s + p[2]*c;
      const y0 = p[1]*cp - z*sp;   // pitch
      z = p[1]*sp + z*cp;
      const f = D/(D - z);
      return [200 + x*f, cy + y0*f, z];
    };
    ...
  }
})
```
Wait pitch: rotate about X axis: y' = y cosφ − z sinφ; z' = y sinφ + z cosφ ✓ as written (applied after Y-rot). φ small.

Then builder collects shapes as {d, fill, stroke, w, op, z} and sorts by z ascending, then string.

Rim path (per side, side=±1):
```js
function ringPath(cx){ let d=''; for(let i=0;i<=N;i++){const a=i/N*2*Math.PI; const p=pr([cx+R*Math.cos(a), RCY+R*Math.sin(a),0]); d+=(i?'L':'M')+p[0].toFixed(1)+' '+p[1].toFixed(1);} return d+'Z';}
```
Lens path radius R−3.4 same loop (N=40).

Brow: arc a from (π+0.12) to (2π−0.12): sample 20 pts, radius R (same as rim center? brow sits on rim: radius R so stroke covers 28.7..33.3 +... rim stroke 4.6 covers R±2.3; brow stroke 7 at radius R−1.2? put brow radius R−1.5, width 7 → covers R−5..R+2 overlapping rim ✓ integrated look.
Brow light stroke radius R−1.5 width 2.6 lighter on top.

Bridge: cubic pts sampled:
```js
const b0=pr([-12.5,-16.5,0]), b1=pr([-5,-27.5,-1.2]), b2=pr([5,-27.5,-1.2]), b3=pr([12.5,-16.5,0]);
path M b0 C b1 b2 b3 (control points projected individually — approximate, fine for small curvature).
```
Stroke 5.2 dark + 2.2 light overlay? overlay light on top center — bevel ✓.

Pads: `ellipse` needs rotation transform: build as path? use <ellipse ... transform="rotate(a x y)"> with projected center; rx 3.4 ry 5.6, rotate ±22.

Camera dots: computed pt; `<circle r="2.4" fill="#101014" stroke="${pal.accent}" stroke-width=".9" opacity="${camOp}">`.

Lens glint: arc sampled radius R−7, angles 3.55..5.45 (≈203°..312°) — top arc ✓ stroke pal.glint w1.5 opacity glintOp (0.5·clamp(cosθ)+...). Add for each lens.

Temple ribbon:
```js
function ribbon(pts, w, mul=1){
  const P = pts.map(pr);
  let L='',Rr='';
  for(let i=0;i<P.length;i++){
    const a = P[Math.max(0,i-1)], b = P[Math.min(P.length-1,i+1)];
    let dx=b[0]-a[0], dy=b[1]-a[1]; const len=Math.hypot(dx,dy)||1;
    const nx=-dy/len, ny=dx/len, hw=w[i]*mul/2;
    L += (i?'L':'M')+(P[i][0]+nx*hw).toFixed(1)+' '+(P[i][1]+ny*hw).toFixed(1);
    Rr = 'L'+(P[i][0]-nx*hw).toFixed(1)+' '+(P[i][1]-ny*hw).toFixed(1)+Rr;
  }
  return L+Rr+'Z';
}
```
Temple mirrored: map pts x→−x (and for left also y+2, z−2). widths same.

Accent strip: indices 1..3 of centerline (between pts 1 and 3, near-hinge section): build ribbon from sub-array pts.slice(1,4) with widths slightly larger +0.8, drawn on top with accent fill, opacity speech·? Also rounder: fine.

Also temple outline stroke: draw centerline path stroke 1 darker over ribbon for edge definition, opacity .5.

Hinge: circle at pr(pts[0]) r4.2 fill rimDark? plus smaller lighter — draw within temple group before ribbon? hinge at same z as temple start → include in temple group (sort key same).

Group sorting: shapes array entries {z, str}; temples z = avg of projected z's; rimGroup z=0; nosePads z=−5 (they're near rim; keep inside rimGroup — hmm when θ>90 pads... negligible). Push order: farTemple → rimGroup → nearTemple via sort ✓.

Compose: `svg.setAttribute('viewBox','0 0 400 300')` static in markup; renderer sets innerHTML = shapes.sort((a,b)=>a.z-b.z).map(o=>o.str).join('').

Colors util:
```js
const hx=(h)=>[parseInt(h.slice(1,3),16),...];
function mixc(a,b,t){...returns rgb string}
```
Palette input as hexes; renderer computes shades:
- rimLit = pal.rim, rimDark = mix(pal.rim, '#000', 0.45)?? Provide pal {rim:'#C2C4CA', lens:'rgba...', temple:'#7F828A', accent:'#E5A850', glint:'rgba(255,255,255,.55)', pad:'#A7A9AE'}
Then computed:
- fR = 0.5+0.5*|c| → rimOuter = mix(shade(pal.rim,0.55), pal.rim, fR) where shade darkens toward black 40%.
- inner bevel lighter: mix(pal.rim, '#FFFFFF', 0.25·fR+0.15).
- brow = mix(dark, lit, fR) darker base: use mix(pal.rim,'#0c0c0e',0.35) as lit? Let me define: browLit = mix(pal.rim,'#141416',0.30), browDark = mix(pal.rim,'#0A0A0C',0.62); browCol = mix(browDark,browLit,fR).
- temple f as derived: fRt (right), fLt; templeCol = mix(mix(pal.temple,'#0A0A0C',0.55), mix(pal.temple,'#FFFFFF',0.18), f).
- lens fill pal.lens constant + opacity maybe modulated.

Light-section palette: {rim:'#6E7076', temple:'#5E6066'...} darker metals ✓; dark-section: {rim:'#C6C8CE', temple:'#8B8E95'}.

Pro ring: after rimGroup, add ellipse ring radius R+7 around each lens center: sampled circle → stroke pal.accent width 1.3 opacity .85, plus maybe dashed? Solid thin ✓. z same as rim (inside group). Only opt.proRing.

opt.stripGlow? skip.

Shadow: not in svg (separate div) ✓ but hero could include its own ellipse div too.

Alright, the compare mini renders: drawGlasses(el,{th:deg(12), phi:deg(-4), cy:150, pal:lightPal, proRing:bool}) once each at load. Widths ~200px.

For the design section, cy: 132.

**Ticker data**:
```js
const PHRASES=[
 {l:'JA', n:'「すみません、もう一度お願いします。」', e:'Sorry — once more, please.'},
 {l:'FR', n:'« Vous avez tout ce qu’il nous faut ? »', e:'Do you have everything we need?'},
 {l:'ES', n:'¿Cuánto queda hasta la cumbre?', e:'How much farther to the summit?'},
 {l:'DE', n:'Ich hätte fast vergessen zu fragen…', e:'I almost forgot to ask…'},
 {l:'IT', n:'Ci vediamo allo stesso posto domani.', e:'Same place tomorrow?'},
 {l:'AR', n:'لا مشكلة، خذ وقتك.', e:'No problem — take your time.'},
 {l:'KO', n:'여기가 처음이에요?', e:'Is this your first time here?'},
 {l:'PT', n:'A conta, por favor. Vamos dividir?', e:'The check, please — shall we split it?'},
];
```
Good, real conversational snippets ✓.

Cycle: show 3.4s; transition: .t-swap class → opacity 0, translateY(6px), blur? 300ms out, swap, in. Sync stripPulse = 1.

**Transcript script**:
```js
const SCRIPT=[
 {who:'them', lang:'日本語', text:'「すみません、この席、空いていますか？」', tr:'Excuse me — is this seat taken?'},
 {who:'you', lang:'English', text:'Please, sit! Are you here for the expo?'},
 {who:'them', lang:'日本語', text:'「はい、初めて来ました。」', tr:'Yes — it’s my first time here.'},
 {who:'you', lang:'English', text:'Then you can’t miss the keynote hall. I’ll walk you over.'},
];
```
Rows: them rows show lang tag + original + translation (translation styled amber, prefixed with small halo glyph?); you rows just text right-aligned. Sequence timing: them original appears (600ms), its translation appears (900ms later), you row appears... loop with 1.6s steps. Manage with async loop + visible flag.

Row markup: div.t-row.them/.you > span.tag + span.txt (+ div.sub for translation). CSS: them align left, you align right; you rows: amber dot? Give you rows color var(--acc) tag.

**Mic demo**: SVG viewBox 0 0 320 150:
- glasses outline: path: two circles r 26 at (128,104)&(192,104)? centers ±32 around 160: (128,104),(192,104), bridge arc between tops. stroke var hair-ish rgba(0,0,0,.25) w1.5 fill none.
- 6 mic dots ON brow: positions [(94,84),(112,79),(130,76),(190,76),(208,79),(226,84)].
- speaker dot: moves x 30→290 ping-pong, y = 34 + 14·sin(t·2.1).
- wavefronts: 2 circles centered speaker r = (t·90)%70, opacity (1−r/70)·0.25 stroke amber.
- beam: line from nearest mic to speaker stroke amber w1.2 dasharray 3 3? plus active mic r 4.5 fill amber; others r2.2 fill #B9B3A6? light section colors: idle dot #8A857A.
- update via rAF when visible.

Also label inside demo? tiny caption "beamforming · live" maybe not needed.

**Air toggle colors**: light section: switch track #D8D4CB → active amber; knob white shadow.

**Numbers copy**:
- 43 unit '' label "languages, translated the moment they're spoken"
- 24 unit 'g' label "on your face. A wristwatch weighs more."  (a watch ~40g+ ✓ true-ish)
- 36 unit 'h' label "of translation per charge — charging case included"
- 0.28 unit 's' label "from their lips to your ear. Faster than a blink." (blink 0.3s? blink ~100-400ms ✓ fine "about a blink")

Heading: kicker BY THE NUMBERS / h2 "Obsession, quantified." sub small.

**Compare rows** final:
- Price (pre-order): $349 / $499
- Frame: Anodized aluminum / Grade-5 titanium
- Weight: 24 g / 26 g
- Battery · with case: 30 h / 36 h
- Microphones: 4 / 6
- Languages · on device: 12 / 26
- Languages · total: 43 / 43
- Finishes: Graphite · Bone / Graphite · Bone · Raw titanium
Pro tag: "MOST CAPABLE" or "MOST POPULAR" — use "MOST POPULAR".
Buttons under columns inside header cells: ghost "Pre-order Halo" / solid "Pre-order Halo Pro".

Column highlight on Pro cells: subtle amber-tinted bg + on header a tag. ✓

**Preorder pills**: buttons "Halo · $349", "Halo Pro · $499" aria-pressed states; clicking updates state; default from compare selection or Halo.

Form: on submit: validate /.+@.+\..+/; error: .err text + input shake + aria-live; success: hide form (fade), show .done block with check svg + "You're in line for {model}." + "We'll write to {email} the moment pre-orders open — nothing to pay until then." + toast "Reservation saved".

**Footer**: top hairline; grid: brand block (mark + "Halo" + one-liner), links col (Explore: anchors), fine print bottom row: "© 2025 Halo Audio ApS · Designed in Copenhagen" + "A concept, rendered entirely in code." honest ✓ nice touch.

**Nav behavior code**:
```js
const themeSecs=[...document.querySelectorAll('[data-theme]')];
onScroll: find last sec with top<=64 → theme; nav.classList.toggle('on-light', theme==='light')
```
CSS: nav default dark frost; .on-light → bg rgba(250,250,247,.72), color ink, hairline dark, links colors adapt via variables on nav.

**Design pin scroll code**:
```js
function updateDesign(){
 const r=desWrap.getBoundingClientRect();
 const total=r.height - innerHeight;
 const p=clamp(-r.top/total,0,1);
 const pe=easeInOut(p);
 th = lerp(-24, 98, pe); phi = lerp(-5, 4, pe); scl = 1+0.14*Math.sin(Math.PI*p);
 draw(svg, {th, phi, cy:132, pal:light, scale via svg style transform: scale(scl) translateY?})
```
Apply scale via CSS transform on svg element (transform-origin center) + translateY float: ty = (0.5-p)*30px? small drift.
Captions: stages.forEach: o = clamp(1 - Math.abs(p - cen)/0.32,0,1); o=smooth(o); el.style.opacity=o; el.style.transform=`translateY(${(1-o)*16}px)`; pointer-events none. Also stage counter text 01→0i+1.
Ghost words same opacity mapping (offset centers slightly earlier? same).
Progress bar: fill.style.transform=`scaleX(${p})`.
Shadow: shadowEl.style: width base 300px → 380px as |sin(th)| grows: w = 300+90·|sin|; opacity .35−?; transform translateX slight toward temple side at profile: tx = sin(th)·40px? At θ=90 shadow shifts right (temple extends right) ✓ tx = s·46. Blur constant.
```
Run inside main rAF only when section within extended viewport (r.top < vh && r.bottom > 0).

Also `will-change` hints sparingly.

**Reveal attributes**: add data-reveal to headings, cells (with --d staggers), stats, rows, etc.

**Hero load animation**: body.loaded class after rAF; CSS .hero [data-hero] transitions from opacity0/translateY(26px)/scale? Use keyframes with delays. Glasses: opacity 0 scale .92 → in 1.1s delay .35s. Ring ellipse: stroke-dash draw via CSS animation (dasharray=len? pathLength trick: pathLength=100, dasharray 100, dashoffset 100→0, 1.4s). ✓

**Now sizes/spacing**: sections padding: clamp(90px, 12vw, 160px) vertical; container max-width 1120px margin auto padding-inline clamp(20px,4vw,40px).

**Check contrast on amber**: amber #E2A44E on dark #0A0A0B: luminance ~0.42 → contrast ~9 ✓. Amber text on light #F4F2ED: use --amber-d #A96F1F (lum ~0.21 → contrast vs 0.9ish ≈ (0.95)/(0.26)≈3.7 — for small text borderline; darken to #8F5E14 (~lum .14 → contrast ≈ 5.9 ✓). Use #96610F. For big eyebrow text fine anyway. Buttons amber bg with #201307 text: contrast high ✓.

**Hairlines on light**: rgba(25,20,10,.14).

Let me also add subtle grain? No, keep clean.

**One more idea for signature cohesion**: section numbers like "01 Design" markers? The kicker style covers it.

Edge: `overflow-x: clip` on body; sticky works with that ✓ (overflow clip on body doesn't break sticky since not scroll container... html overflow-x clip? Use `html,body{overflow-x:clip}` — sticky unaffected ✓ (unlike overflow:hidden on body which also fine for sticky when html scrolls).

**Fonts for huge ghost words**: weight 800 ls -0.04em.

**Write final HTML now.** I'll be systematic and thorough; target ~1200 lines. Let me draft mentally key CSS then write it out directly in the answer. I must be careful that the JS has no bugs — walk through critical functions once more while writing.

A few more details to lock:

drawGlasses signature:
```js
function drawGlasses(svg, o){
  // o: {th(rad), phi(rad), cy, pal, proRing, speech(0..1), camFade? auto}
  const pal=o.pal;
  ...
  const S=[]; // {z, s}
  const add=(z,str)=>S.push({z,str});
  ...
  S.sort((a,b)=>a.z-b.z);
  svg.innerHTML = S.map(x=>x.s).join('');
}
```
Number formatting with toFixed(1).

Compute lens rim & lens & brow & glint & camera & bridge into ONE group string with z=0? Bridge z 0; but at θ>90 bridge physically in front of lenses when viewed from back? bridge at z=0 plane, lenses z=0 — same plane, whatever.

Actually subtle: temples attach at hinge OUTSIDE rims; at front view temples behind → their ribbons start at hinge (x=±73) — visible portions stick out beyond rims at edges? At θ=0 temple pts x' ~73→? tip x' = 60·1 −(−118)·0 = 60 → tip projects INSIDE rim horizontally (60 < 73) and far → hidden behind lens region mostly (pf smaller pulls inward) → at front view temples nearly fully hidden behind rims/lenses? Real glasses front view: temples hidden behind rims ✓ correct! Only hinge caps peek at outer edges ✓.

At θ=24°: tip x' = 60·0.914 −(−118)(0.407) = 54.8+48.0 = 102.8, z' = 60·0.407 + (−118)(0.914) = 24.4−107.9=−83.5 → pf=950/1033.5=0.919 → x=200+94.5=294.5 → extends beyond rim (273) to the right, slightly above? y tip = 138+(46·0.919·cp...)≈ 138+42=180 → temple emerges from behind right rim toward lower-right ✓ perfect 3/4 view.

Left temple at θ=24: hinge x' = −73·0.914 −3·0.407 = −66.7−1.2=−67.9 (z' = −73·0.407+3·0.914 = −29.7+2.7=−27 → pf 0.972 → x=200−66=134, y=138−9·0.97≈129) → visible sticking left of left rim (rim outer edge at x=127−? left rim spans 127..193; hinge at x=134 is INSIDE rim area — hidden behind rim? z'=−27 → far → drawn before rim → hidden by lens fill (translucent! 0.16 opacity → temple shows through lens faintly ✓ actually realistic—temples visible through translucent lenses? Lenses translucent smoke: slight see-through ✓ nice).
Left tip: x' = −60·0.914 − (−118)(0.407)·? left tip pts mirrored: (−60,47,−117): x' = −54.8 − (−117)(0.407)→ careful: x' = x·c − z·s = −54.8 − (−117·0.407) = −54.8 + 47.6 = −7.2?? That's wrong-looking: left temple tip projects near center-left, z' = x·s + z·c = (−60)(0.407) + (−117)(0.914) = −24.4−106.9 = −131.3 → pf 0.880 → x = 200−6.3=193.7, y = 138+47·0.88·cp ≈ 178 → left temple tip lands at x≈194 hidden behind right lens area?? Hmm: at θ=+24 we look from the right side; left temple goes back-left in 3D but perspective: back-left... x' = −7 means near center — because z·sinθ term: temple going back (−z) projects toward +x direction when θ>0 (since −z·sinθ>0). So left temple appears going back and to the RIGHT (toward viewer's right) — correct for a 3/4 view from right! Both temples converge backward. Right temple (near side) sweeps right; left temple (far side) goes back appearing to angle right behind the lenses — mostly occluded by lenses/rims. ✓ realistic.

Ear hook y down to 47 ✓.

Also must ensure temple ribbon doesn't visually detach from hinge: hinge circle r4.2 covers joint ✓.

**drawGlasses sorting detail**: bridge + rims in one group with z=0; camera dots inside group; pads inside group; glints inside. Groups: templeL {z}, templeR {z}, core {0}. If both temples z<0 → both behind ✓. At θ=90: templeL z≈−60 → behind core ✓; templeR z≈+66 front ✓.

Compute temple z as average of projected z of centerline pts.

**Speech strip**: accent ribbon opacity = 0.35+0.65·speech (speech from pulse). In design section pass speech = 0.85 steady? Make it respond to stage: stage2 (sound) speech=1 else 0.35 — cute: during "Sound" caption the strip lights fully ✓ tie to stage opacities: speech = 0.3 + 0.7·stage2Opacity.

**Numbers count decimals**: value 0.28: animate v = target·ease; text = v.toFixed(2). Others toFixed(0). Store config on element data attrs: data-n="43" data-dec="0" data-unit etc.

**Reduced motion**: 
```js
const RM = matchMedia('(prefers-reduced-motion: reduce)').matches;
```
If RM: skip rAF idle (single static draw), reveals instantly (CSS handles via media query forcing opacity 1/no transition), counters set instantly, design section: still allow scroll-driven? Scroll-driven is user-controlled (not vestibular automatic) — but rotation is fine; keep but no easing bounce. Ticker: still cycles but without motion? Keep simple: if RM, ticker swaps without animation classes (just swap). Transcript/mic demos: render one static frame, no loop.

CSS media query:
```css
@media (prefers-reduced-motion: reduce){ *{animation:none!important; transition:none!important} [data-reveal]{opacity:1!important; transform:none!important} }
```

**Anchor offset**: html{scroll-padding-top:76px}.

**Nav "Pre-order" button** scrolls to #preorder ✓.

**Hero CTA "Explore the design"** anchor #design ✓.

Now — potential issue: sticky pin content uses 100svh; ghost words absolute centered; svg centered absolute too. Captions left area may overlap glasses on narrow desktop — glasses width min(72vw,560px) centered; captions width 300px at left: max(4vw, calc(50% - 460px))? Position: left: clamp(16px, 7vw, 120px); top 50% translateY(-50%). Glasses center — on 1200px screen glasses 528px wide → from 336..864; captions at left 84..384 → slight overlap with glasses left edge (336 vs 384) — captions have bg? no bg; overlap 48px onto halo ring area maybe; shift glasses right: left offset via transform translateX(6vw) on art container at >900px. Or captions max-width 280 and left 6vw → 72..352 vs glasses start ~336+66=402 (after shift) ✓. I'll shift art container right by 5vw on ≥1000px, and captions vertical center. Mobile: captions bottom.

Also the sticky top kicker centered top: "DESIGN" + progress centered.

**Compare table static renders**: draw after DOM ready; also redraw on nothing (static). Size: svg width 190 height 130 viewBox 400×300 scaled — text? Name below.

Alright, also add `lang` attributes for foreign phrases? Not necessary.

**Icons set** (hand-drawn 24px stroke icons, stroke=currentColor, width 1.7, round caps):
- translate: two speech bubbles / or "あA"? draw: bubble with "A" path hard; use arrows-swap + wave: I'll draw: left-to-right arrows (⇄) style: path M4 8h13l-3-3 M20 16H7l3 3 — swap arrows ✓ simple readable.
- ear/private: arc shapes: ear: M... complex; use "sound waves to ear": dot + arcs: circle r2 + arcs. I'll draw waves: three arcs increasing + dot ✓ (like wi-fi rotated toward a dot).
- mic: standard mic: rect rx rounded (x9 y3 w6 h10 rx3) + path M5 11a7 7 0 0 0 14 0 + line 12 18v3 + line 9 21h6.
- offline/globe: circle + meridians: circle r8 + ellipse rx3.2 ry8 + line horizontal.
- bolt (battery): path M13 2L5 13h5l-1 9 8-11h-5l1-9z ✓.
- feather: path M20 4c-6 0-12 5-13 12l-3 4 M9 15h6? approximate feather: use leaf: M4 20C4 10 12 4 20 4c0 8-6 16-16 16z + stem line M4 20L20 4? leaf ✓ reads "light".
- music: note: M9 18a2.. circle cx7 cy17 r2.4 + circle cx17 cy15 r2.4 + path M9.4 17V6l10-2v9? standard double note ✓.
- check: M5 13l4 4L19 7.
- plane (airplane mode): M10.5 21l1.5-6-4.5... simplified paper-plane: M3 12l18-8-6 18-3-7-7-2z? that's send icon ✓ use as "flight" is off... use plane glyph: complex; send-style ok labeled "Airplane mode".
- arrow →: M5 12h14 M13 6l6 6-6 6.
- chevron down: M6 9l6 6 6-6.

Store as JS template? Just inline where needed.

**Headline kerning**: h1 uses two spans display block. Amber second line? Apple: white both, maybe muted first line. Style: line1 color var(--mut)? I'll do line1 primary, line2 with amber word? "In your ear." — amber on "your"? Keep: line1 #F2F1EC, line2: "In your ear." with "ear." amber? Subtle: make entire line2 amber-tinted? Too loud. I'll amber only the period? Cute detail: periods in amber. `.dot-accent{color:var(--acc)}` on final periods of headlines — subtle signature ✓ (typographic, not glow). Apply to section h2s too.

Okay, also remember: no `alert`; ✓ none. All buttons wired ✓. No lorem ✓. No emoji ✓ (foreign-language punctuation 「」« » fine — not emoji).

**Now writing everything.** I'll write carefully, mentally validating JS syntax. Given length limits, be efficient but complete. Let me draft the full code.

Structure plan for CSS (ordered): reset, vars, base type, nav, buttons, hero, ticker, sections common, design pin, features, demos, numbers, compare, preorder, footer, toast, reveal, media queries, reduced motion.

Let me pre-compute a few SVG static bits: halo ring svg:
```html
<svg class="halo-ring" viewBox="0 0 600 240" fill="none" aria-hidden="true">
  <g transform="rotate(-7 300 120)">
    <ellipse cx="300" cy="120" rx="252" ry="66" pathLength="100" class="ring-base"/>
    <ellipse cx="300" cy="120" rx="252" ry="66" pathLength="100" class="ring-orb"/>
    <ellipse cx="300" cy="120" rx="252" ry="66" pathLength="100" class="ring-orb o2"/>
  </g>
</svg>
```
CSS: .ring-base{stroke:rgba(255,255,255,.14); stroke-width:1; stroke-dasharray:100; animation: ringDraw 1.6s var(--ease) .5s both}
.ring-orb{stroke:var(--amber); stroke-width:1.5; stroke-linecap:round; stroke-dasharray:10 90; animation: orbit 13s linear infinite; opacity:.9; filter: drop-shadow? no glow — skip filter.}
.o2{stroke-dasharray:3 97; opacity:.45; animation-duration:13s; animation-delay:-6.5s}
@keyframes orbit{to{stroke-dashoffset:-100}} from 0.
@keyframes ringDraw{from{stroke-dashoffset:100}to{stroke-dashoffset:0}}
Note: negative dashoffset direction fine.

Preorder mini ring: same smaller.

**Hero art container**:
```html
<div class="hero-art" data-hero="3">
  <svg class="halo-ring" ...>
  <svg id="gHero" viewBox="0 0 400 300"></svg>
  <div class="hero-shadow"></div>
</div>
```
hero-shadow: ellipse div below glasses: width 46%, height 26px, radial-gradient(closest-side, rgba(0,0,0,.55), transparent 72%), blur 6px? radial alone is smooth ✓ opacity .5. On dark bg shadow subtle rgba(0,0,0,.6) — visible? On near-black bg shadows invisible — instead a faint amber reflection? Skip shadow on hero (dark bg) — instead a faint floor reflection? Skip; ring suffices. Design section (light) uses shadow ✓. Preorder dark: skip.

Ticker under hero-art.

**Sticky pin HTML**:
```html
<section id="design" class="design" data-theme="light">
  <div class="pin">
    <div class="pin-top"><span class="kicker">Design</span><span class="pin-count" id="pinCount">01 / 03</span></div>
    <div class="pin-progress"><i id="pinBar"></i></div>
    <div class="ghost" id="ghost0" style="font-size:clamp(90px,17vw,280px)">TITANIUM</div>
    <div class="ghost" id="ghost1" style="font-size:clamp(80px,13vw,220px)">SOUND</div>  // words: TITANIUM / BEAMARRAY? "SOUND" short; maybe "DIRECTED" no. Stage words: TITANIUM / WHISPER / SIX. Hmm: stage2 sound → "WHISPER" evocative ✓ stage3 mics → "SIX MICS"? one word "ARRAY"? Use: TITANIUM, WHISPER, AWARE? "AWARE" odd. Words: "TITANIUM" / "WHISPER" / "SIGNAL". Signal ties to mics ✓.
    <div class="stage-copy">
      <div class="stage" id="st0"><h3>...</h3><p>...</p></div> ×3
    </div>
    <div class="pin-art">
      <div class="pin-shadow" id="pinShadow"></div>
      <svg id="gDesign" viewBox="0 0 400 300"></svg>
    </div>
  </div>
</section>
```
Stage h3 small-ish (28px) bold; p muted 16px width 300px.

**Features HTML**:
```html
<section id="features" class="features" data-theme="light">
 <div class="wrap">
  <header class="sec-head" data-reveal>
    <p class="kicker">Capabilities</p>
    <h2>Technology that<br>gets out of the way<span class="dot-a">.</span></h2>
    <p class="lead">No screen to stare at. Nothing to pair, unlock, or charge mid-sentence...</p>
  </header>
  <div class="fgrid">
    <article class="fcell c7" data-reveal>
      <div class="fic">icon</div><h3>Fluent, both ways</h3><p>...</p>
      <div class="demo t-demo" id="tDemo"><div class="trows" id="tRows"></div></div>
    </article>
    <article class="fcell c5" data-reveal style="--d:.12s"> private...
    <article class="fcell c5"> mics demo svg
    <article class="fcell c7"> offline toggle
  </div>
  <p class="ftr-note" data-reveal>music icon + And beneath it all, Halo is simply a beautiful pair of headphones...</p>
 </div>
</section>
```

Grid: .fgrid{display:grid;grid-template-columns:repeat(12,1fr);gap:1px;background:var(--hair);border:1px solid var(--hair)} .fcell{background:var(--bg);padding:...} .c7{grid-column:span 7}.c5{span 5}. Mobile: all span 12.

Wait gap 1px + background shows through as lines ✓ but border also 1px ✓.

**Numbers HTML**: .stats{display:grid;grid-template-columns:repeat(4,1fr)} cells with border-left except first; each .stat padding; .n{font-size:clamp(64px,9vw,132px);font-weight:200;letter-spacing:-.04em; tabular} .unit amber 0.4em raised. Mobile: 2 cols then 1? 2 cols with borders top. I'll do: 4→2 (media 900) →1 (520)? 2 cols fine at small with smaller font; keep 2 min then 1 col below 480? Simplify: repeat(auto-fit,minmax(210px,1fr)) — flexible, avoids manual queries, but border logic: give each cell border-top hairline + padding — top hairlines read as editorial rows ✓ regardless of columns. Use that: border-top on all stat cells, generous padding-top. ✓ clean.

**Compare HTML**:
```html
<div class="cmp" data-reveal>
  <div class="cmp-row cmp-head">
    <div class="c-lab"></div>
    <div class="c-val c-halo">
       <svg id="gC1" viewBox="0 0 400 300"></svg>
       <h3>Halo</h3><p class="csub">The essential pair.</p>
       <button class="btn ghost" data-model="halo">Pre-order · $349</button>
    </div>
    <div class="c-val c-pro">
       <span class="tag">Most popular</span>
       <svg id="gC2"></svg>
       <h3>Halo Pro</h3><p class="csub">Everything, everywhere.</p>
       <button class="btn solid" data-model="pro">Pre-order · $499</button>
    </div>
  </div>
  rows...
</div>
```
Rows generated in HTML directly (7 rows). Each: `<div class="cmp-row"><div class="c-lab">Price</div><div class="c-val">$349</div><div class="c-val pro">$499</div></div>` with data? No mobile data-labels since label spans full width (mobile CSS: .cmp-row{grid-template-columns:1fr 1fr} .c-lab{grid-column:1/-1}). ✓

Grid template must match header: .cmp-head uses same columns; but header cells contain buttons etc. Align: both `grid-template-columns: 1.05fr 1fr 1fr` ✓.

**Preorder HTML**:
```html
<section id="preorder" class="preorder" data-theme="dark">
 <div class="wrap narrow">
  <svg class="mini-ring" ...> (ring with orbit anim)
  <h2 data-reveal>Be first in line<span class="dot-a">.</span></h2>
  <p class="lead" data-reveal>Reserve with an email alone...</p>
  <div class="model-pick" data-reveal>
    <button class="mpill" data-model="halo" aria-pressed="true">Halo <span>$349</span></button>
    <button class="mpill" data-model="pro" aria-pressed="false">Halo Pro <span>$499</span></button>
  </div>
  <form id="resForm" data-reveal novalidate>
    <input type="email" id="email" placeholder="you@example.com" aria-label="Email" autocomplete="email">
    <button class="btn solid" type="submit">Reserve yours</button>
  </form>
  <p class="ferr" id="ferr" role="alert" hidden>Enter a valid email...</p>
  <div class="done" id="done" hidden> check svg <h3>You're in line.</h3><p id="doneTxt"></p></div>
  <p class="fine" data-reveal>No charge today. We'll email you before anything ships, and you can cancel with one click.</p>
 </div>
</section>
```

Footer as planned.

**Toast**: `<div class="toast" id="toast" role="status"><svg check><span id="toastTxt"></span></div>` .show class.

Now JS full write-through (I'll finalize in the answer; key checks done above). One more: easeInOutCubic = t<.5?4t³:1−(−2t+2)³/2.

Counter easing: easeOutExpo = 1−2^(−10t).

IO for counters: once → animate 1500ms.

Design captions text final:
1. h3 "One billet of titanium." p "Rims, bridge and hinges machined from a single piece of Grade-5 titanium, then trimmed to 24 grams. You notice it in the first minute — and never again."
2. h3 "Sound with a direction." p "A beam-array in each temple aims audio into your ear canal and nowhere else. The person beside you hears a whisper of nothing."
3. h3 "Six ears, always open." p "Six microphones form a beam toward whoever is speaking, ignoring the rest. From the second they start talking, translation is already underway."

Stage ghost words: TITANIUM / WHISPER / SIGNAL ✓.

Features copy final:
1. "Fluent, both ways" — "Halo listens to the person in front of you, translates in 0.28 s, and whispers it into your ear in a voice that sounds like yours. When you answer, it speaks for you — out loud, in their language."
2. "Private by physics" — "Sound is focused into your ear canal; no seal, no earbud, no leak. To everyone else, your conversations are silent."
3. "Six microphones, one voice" — "A beamforming array finds the person speaking and follows them — through wind, a busy café, or a train platform."
4. "Fluent when the signal isn't" — "Each temple carries a neural engine that translates on-device. Airplane mode, basements, mountain trails — the conversation doesn't notice."

Banner: music icon "Underneath it all, Halo is a beautiful pair of headphones — music, calls and podcasts for 40 hours, with the case." Keep simple: "And when nobody's talking, Halo is simply a lovely pair of headphones. Music, calls, podcasts — 40 hours with the case."

Compare section heading: kicker "Two models" h2 "Halo<span>.</span> Or Halo Pro<span>.</span>" lead "The same fit, the same translations. Pro adds titanium, two more ears, and more of everything offline."

Hero sub final: "Halo translates the conversation in front of you — as it happens — and whispers it into your ear in a voice like your own. No phone in your hand. No pauses. No more smiling and nodding."

Great, that last phrase has charm.

Now write it all. Also careful: JS uses `Math.PI`. Draw functions produce strings; use template literals.

Also nav HTML:
```html
<nav id="nav">
 <a class="brand" href="#top"><svg mark>...</svg> Halo</a>
 <div class="nlinks"><a href="#design">Design</a><a href="#features">Features</a><a href="#numbers">Specs</a><a href="#compare">Compare</a></div>
 <a class="btn solid small" href="#preorder">Pre-order</a>
</nav>
```
Nav fixed; on-light class toggles colors.

Brand mark: `<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="7.5" stroke amber sw2 dasharray="30 17"? pathLength 100 dasharray 78 22 rotate -90 → open ring + small dot circle cx at gap end? Simpler: open arc + dot at right: circle r7.5 pathLength 100 dasharray "80 20" transform rotate(115 12 12) + circle cx17.8 cy7 r1.8 fill amber. Looks like halo+satellite ✓.

Time to write the final file. I'll be meticulous with syntax. Also ensure IDs referenced exist. Also the mic demo and transcript gated by IO visibility flags.

Also add `document.documentElement.classList.add('js')`? Not needed.

Ticker element sized fixed height to avoid jumping: .ticker{height:56px} content absolutely centered.

For hero glasses sizing within 100svh: hero-art svg width clamp(340px,46vw,600px); ring width clamp(420px,58vw,760px) positioned centered with top offset ~28%? Ring center should align glasses center: ring viewBox 600×240 centered on art container; glasses svg centered too; ring vertical center at glasses middle (~55% of glasses svg height). Position ring absolute left 50% top 50% translate(-50%,-56%) width 128% of glasses box? Set art container position relative with fixed aspect: container width W=clamp(...), height = W*0.75 (viewBox ratio 400:300). Ring width = W*1.55, height auto (ratio 600:240), centered at top 52%. ✓

Hero grid: hero{display:flex;flex-direction:column;align-items:center;justify-content:flex-start;padding:110px 20px 64px; min-height:100svh}. Text block margin-bottom clamp(8px,3vh,28px). Art flex none. Ticker margin-top: -2% (overlap ring bottom?) ring bottom extends below glasses center by 66/240 of ring height... fine, no overlap needed; ticker margin-top clamp(4px,1.5vh,16px). Scroll cue absolute bottom 22px.

Total hero height: nav 64 + eyebrow/h1/sub/cta ≈ 320-420px + art (min(46vh…)) hmm on 800px viewport: text ~360 + art 340 + ticker 56 = 756 ✓ tight but ok; reduce art on short screens via media (max-height 820px) art width 40vw. Use clamp with vh: width clamp(320px, min(46vw, 52vh), 600px)? CSS min() inside clamp ✓ modern browsers fine.

Ticker arrow svg inline `<svg width="14" height="14" viewBox="0 0 24 24"><path d="M5 12h13M13 6l6 6-6 6" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>`.

Now — writing answer. Also include brief explanation after the code block, per my practice. Language: English (user's language).

Let me also double check the `ribbon` for accent strip slice: pts.slice(1,4) → indices 1,2,3 with widths TW.slice(1,4) — need widths array aligned; accent width = w+1.6 each. Build separate ribbon fn call with widths arr.

Hinge circle: at pr(TPTS[0]) — draw r4.4 fill rimMid? plus r2 lighter. In temple group before ribbon.

Left temple construction: mirror pts: pts.map(p=>[-p[0], p[1]+1.6, p[2]-2]); widths same.

Temple z for sort: avg projected z.

Camera fade: camOp = clamp(1.4*(1-|th|/1.35),0,1)? θ up to ~1.7rad(98°): op = clamp(1.3 - Math.abs(th)/1.2, 0, 1)·0.95.

Glint op: clamp(Math.cos(th),0,1)*0.55 + 0.08.

Pad op: clamp(Math.abs(Math.cos(th))*1.5,0,1).

Core group string assemble: lens fills (2), glints (2), rim outer strokes (2), rim inner (2), brow dark (2), brow light (2), bridge dark, bridge light, pads (2), cams (2), proRing? (2).

Order within core: lens fill → glint → rim strokes (over lens edges) → brow over rim → bridge → pads → cams → proRing.

Hmm lens fill under rim stroke: rim stroke centered on R=33 covers 30.7..35.3; lens fill radius 29.6 → 3.4 gap? Rim inner edge at 30.7 vs lens 29.6: 1.1px gap shows background → set lens radius 31.5 (under rim stroke ✓ overlap).

Lens fill per lens: sampled polygon path fill pal.lens.

proRing: radius R+7=40 centered lens center — sampled circle path stroke accent 1.4 opacity .8.

Everything in one `<g>` per temple with fill etc.

**Ghost + caption z-order & pointer-events:none for stage/ghost** ✓.

**pin layout CSS**:
.pin{position:sticky;top:0;height:100svh;overflow:hidden;display:flex;align-items:center;justify-content:center}
.pin-art{position:relative;width:min(76vw,600px)} svg width 100% display block.
.pin-art{transform:translateX(0)} media ≥1080px translateX(7vw)? Use left offset: .pin-art{left:...}? It's flex-centered; add media transform:translateX(6vw) — but JS also transforms svg (scale) — apply JS transform to svg only, CSS shift on container ✓.
.stage-copy{position:absolute;left:clamp(20px,7vw,110px);top:50%;transform:translateY(-50%);width:min(320px,80vw);z-index:3}
.stage{position:absolute;inset? stack: .stage{position:absolute;top:50%;left:0;transform:translateY(-50%);opacity:0;width:100%} container height 0? Container .stage-copy{height:280px?} make .stage-copy{position:absolute; width:320px; height:300px; top:50%; margin-top:-150px; left:...} stages absolute within ✓.
Mobile (<860px): .stage-copy{left:50%;top:auto;bottom:5vh;transform:translateX(-50%);width:min(88vw,420px);text-align:center} stages absolute top 0.
.pin-top{position:absolute;top:26px;left:0;right:0;display:flex;justify-content:center;gap:18px;align-items:center;z-index:3} progress width 120px hairline; bar amber scaleX origin left.
.ghost{position:absolute;left:50%;top:50%;transform:translate(-50%,-52%);font-weight:800;letter-spacing:-.05em;color:rgba(24,20,10,.05);opacity:0;white-space:nowrap;z-index:0;pointer-events:none;user-select:none}
pinShadow: position absolute; bottom:-7%? place under art: .pin-shadow{position:absolute;left:50%;bottom:-4%;width:64%;height:34px;transform:translateX(-50%);background:radial-gradient(closest-side,rgba(20,16,8,.32),rgba(20,16,8,0) 72%);z-index:-1}? JS updates width & translateX combined: I'll set left in JS via style.transform = `translateX(calc(-50% + ${tx}px))`; width via style.width. ✓ z-index -1 relative to pin-art (art z1).

**Numbers hairlines**: .stat{border-top:1px solid var(--hair);padding:34px 26px 8px} inside .stats grid gap 0? add column gap 28px? With auto-fit minmax columns and border-top each, plus padding-inline. Looks editorial ✓.

unit span: font-size .38em; color var(--acc); font-weight 500; margin-left .06em; vertical-align: super? baseline tweak: position relative top -0.9em? Use <sup>-like: .unit{font-size:.36em;vertical-align:.9em}? Simpler: .n{display:flex;align-items:baseline}.n .u{font-size:.34em;color:var(--acc);font-weight:600;margin-left:8px;letter-spacing:0} ✓ label p below muted 15px max-width 26ch.

Label: also small amber index? no.

**Buttons CSS**:
.btn{display:inline-flex;align-items:center;gap:8px;border-radius:999px;padding:13px 26px;font-size:15px;font-weight:600;letter-spacing:-.01em;cursor:pointer;border:1px solid transparent;transition:transform .35s var(--ease), background .35s var(--ease), color .35s, border-color .35s;text-decoration:none}
.btn.solid{background:var(--acc-btn, var(--amber));color:#221608} hover: transform:translateY(-2px); filter brightness 1.06? use background #EEB263 hover.
.btn.ghost{border-color:var(--hair2);color:var(--fg)} hover border-color fg/40 bg subtle.
Define --amber per theme? Button amber same both; on light bg amber solid + dark text ✓.
.btn.small{padding:8px 16px;font-size:13px}
.btn:active{transform:scale(.97)}

**Form CSS**: form{display:flex;gap:10px;max-width:520px;margin:26px auto 10px} input flex1 bg #151517;border:1px solid var(--hair);border-radius:14px;padding:15px 18px;color:#F2F1EC;font-size:16px; focus border-color amber outline none + subtle shadow ring rgba amber .25. error shake keyframes translateX. .ferr color #E07A6B font 14 margin.

.mpill{border:1px solid var(--hair);border-radius:999px;padding:12px 22px;background:transparent;color:var(--fg);cursor:pointer;font-weight:600;font-size:15px; display:inline-flex;gap:10px;transition:...} .mpill span{color:var(--mut);font-weight:500} .mpill[aria-pressed=true]{background:var(--amber);border-color:var(--amber);color:#221608} .mpill[aria-pressed=true] span{color:#5A3E15}

**Toast CSS**: position:fixed;left:50%;bottom:26px;transform:translate(-50%,80px);opacity:0;transition:.5s var(--ease);background:#1D1D20;color:#F2F1EC;border:1px solid rgba(255,255,255,.12);padding:13px 20px;border-radius:14px;display:flex;gap:10px;align-items:center;z-index:99; .toast.show{transform:translate(-50%,0);opacity:1} svg amber.

**Reveal CSS**:
[data-reveal]{opacity:0;transform:translateY(30px) scale(.985);transition:opacity 1s var(--ease),transform 1s var(--ease);transition-delay:var(--d,0s);will-change:opacity,transform}
[data-reveal].in{opacity:1;transform:none}
Hero load: [data-hero] similar with keyframes:
@keyframes rise{from{opacity:0;transform:translateY(26px)}to{opacity:1;transform:none}}
.hero [data-hero]{animation:rise 1s var(--ease) both}
delays via inline style/nth: define classes d1..d4 delays .05/.15/.25/.4; art d3 .5s + scale: hero-art animation includes scale(.94)→1: separate keyframes riseArt.

**Scroll cue**: .cue{position:absolute;bottom:20px;left:50%;transform:translateX(-50%);display:flex;flex-direction:column;align-items:center;gap:8px;color:var(--mut);font-size:11px;letter-spacing:.22em;text-transform:uppercase} .cue i{width:1px;height:34px;background:var(--hair2);position:relative;overflow:hidden} .cue i::after{content:"";position:absolute;left:0;top:-100%;width:100%;height:100%;background:var(--amber);animation:cue 2.2s var(--ease) infinite} @keyframes cue{0%{top:-100%}55%{top:100%}100%{top:100%}}

Hmm hair2 var define: --hair2: rgba(255,255,255,.16) dark / rgba(20,18,12,.28) light (stronger hairline for controls).

**Ticker CSS**: .ticker{display:flex;align-items:center;gap:12px;font-size:15px;height:30px;position:relative;justify-content:center} inner .twrap{display:flex;gap:12px;align-items:center;transition:opacity .35s ease, transform .35s ease} .twrap.out{opacity:0;transform:translateY(8px)}
.live{display:inline-flex;align-items:center;gap:6px;font-size:10px;letter-spacing:.18em;color:var(--acc);font-weight:700} .live i{width:6px;height:6px;border-radius:50%;background:var(--acc);animation:blink 1.6s ease infinite} @keyframes blink{50%{opacity:.25}}
.tl{font-size:10px;letter-spacing:.16em;font-weight:700;color:var(--mut);border:1px solid var(--hair2);padding:3px 7px;border-radius:6px}
.t-native{font-weight:600} .t-en{color:var(--mut)} arrow color var(--acc).
Mobile: hide .t-en? wrap; allow smaller font 13px, maybe hide arrow on <380.

Native phrases include CJK — system fonts render ✓.

**Transcript CSS**: .t-demo{margin-top:26px;background:rgba(255,255,255,.5)?} Light cell bg is same as section (white-ish). Give demo a subtle inset panel: background:var(--light2)? Section features bg = --light2 (#FBFAF7); cells bg same → hairlines only. Demo panel: background:#F1EEE7? Actually put demos on slightly darker inset: rgba(24,20,10,.035) radius 16 padding 18 height 216 overflow hidden. mask-image:linear-gradient(180deg,transparent 0,#000 18px,#000 calc(100% - 12px),transparent). ✓
.t-row{display:flex;flex-direction:column;gap:3px;margin:10px 0;opacity:0;transform:translateY(10px);transition:.6s var(--ease)} .t-row.show{opacity:1;transform:none}
.t-row .who{font-size:10px;letter-spacing:.18em;font-weight:700;color:var(--mut)} them who color mut; you who color amber-d.
them text 15px; .t-sub{color:var(--acc2, amber-d)? } translation line: color:#8A5B10? Use var(--mut) italic? Make translation amber-dark to pop: color:var(--acc). Prefix with tiny halo dot? fine plain.
.you{text-align:right;align-items:flex-end}

Mic demo: svg block margin-top 26px; colors inline in JS using light palette constants.

Air demo: .air{margin-top:26px;display:flex;flex-direction:column;gap:14px} switch row: display flex align-center gap 14. .switch{width:52px;height:30px;border-radius:999px;background:#D9D5CC;position:relative;border:none;cursor:pointer;transition:background .3s} .switch i{position:absolute;top:3px;left:3px;width:24px;height:24px;border-radius:50%;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,.25);transition:transform .3s var(--ease)} [aria-checked=true]{background:var(--amber)} [aria-checked=true] i{transform:translateX(22px)}
.air-num{font-size:44px;font-weight:250? use 200;letter-spacing:-.03em} .air-lab{color:var(--mut);font-size:14px}
Plane icon near label when on? add small plane svg shown when checked with .in transition. Keep simple: label text changes + small caption.

Fine print .fine{font-size:13px;color:var(--mut)}

**Feature cell**: .fic{width:40px;height:40px;border-radius:12px;display:grid;place-items:center;color:var(--acc);background:rgba(226,164,78,.12);margin-bottom:18px} icon svg 22. h3 22px 700 ls-.02; p 15.5px muted.

Banner note: margin-top 26px; display flex center gap 12; color mut; icon amber; text 15px; border? none, just centered.

**sec-head**: max-width 720px; margin-bottom clamp(48px,7vw,84px); h2 margin 14px 0 18px; lead 18px muted max-width 560px. Some heads centered (compare? numbers left?) Numbers: left-aligned head then stats full width. Compare centered? Keep left for editorial consistency except hero & preorder centered. Compare left. OK.

**Wrap**: .wrap{max-width:1140px;margin:0 auto;padding:0 clamp(20px,4.5vw,44px)} section padding-block clamp(96px,11vw,150px).

**Compare specifics**: .cmp{border-top:1px solid var(--hair)} rows border-bottom. Head cells padding 30px 18px 26px; text-align center? Columns center for values? Apple spec tables: values left? I'll center model columns for symmetry: .c-val{text-align:center} labels left. Hmm mixed alignment—label left, values center ✓ fine.
Head svgs width 200 margin auto. .tag{font-size:10px;letter-spacing:.16em;font-weight:700;color:var(--amber-d-light?) on light bg use amber-d; background:rgba(226,164,78,.15);padding:4px 10px;border-radius:999px} 
Pro cells tint: .pro{background:rgba(226,164,78,.055)}? With row hover override. Row hover: .cmp-row:not(.cmp-head):hover .c-val{background:rgba(226,164,78,.09)}? Simpler: hover row cells background var(--hovi). Define .cmp-row .c-lab,.c-val{padding:18px;border-top:1px solid var(--hair)} first row (after head) keep border ✓ all rows have border-top; head row border-bottom via its cells border-top? Use: all cells border-bottom except? Manage: .cmp-row{display:grid;...} .cmp-row + .cmp-row .c-lab, etc border-top... Easiest: every cell border-top:1px solid var(--hair); head row cells border-top none (:first-child row) → .cmp-head .c-*{border-top:none}. ✓
Mobile: .cmp-head{grid-template-columns:1fr 1fr} .cmp-head .c-lab{display:none} rows: grid-template-columns:1fr 1fr; .c-lab{grid-column:1/-1;padding-bottom:0;border-top... keep;font-size 11 caps mut}. values keep center. ✓

Pro tag placement: in head cell top. Head cell layout column flex center gap 8.

Buttons in head: margin-top 10.

**Preorder ring**: mini svg 200×80 ellipse rx80 ry22 reuse classes; margin-bottom 18px.

**Footer**: .footer{background:var(--dark);color:var(--mut-d);padding:56px 0 40px;border-top:1px solid var(--hair-d)} inside wrap grid: brand + links; bottom row flex space-between font 12px; links hover color paper. Footer is part of dark finale; put inside preorder section? Separate footer element data-theme dark ✓ nav theme detection includes footer.

**Theme detection list**: sections with data-theme: hero(dark), design(light), features(light), numbers(dark), compare(light), preorder(dark), footer(dark). Nav switches when section top < navBottom(64) → pick last passing. Compute on scroll (throttle rAF flag). Also nav gets .scrolled? Always frosted — but at top over hero dark it blends; keep constant.

Nav CSS: position:fixed;inset:0 0 auto;z-index:50;display:flex;align-items:center;justify-content:space-between;padding:0 clamp(16px,3vw,32px);height:64px; background:rgba(12,12,13,.72);backdrop-filter:blur(16px) saturate(1.2);border-bottom:1px solid rgba(255,255,255,.07); transition: background .45s, border-color .45s, color...; color:#F2F1EC.
nav.on-light{background:rgba(249,248,244,.75);border-bottom-color:rgba(24,20,10,.08);color:#1B1A17}
links: color inherit opacity .8 hover 1 + underline offset? Use color var. brand font-weight 700 display flex gap 9 align-center. nlinks gap 26 font 14; hide <760px.
Preorder btn small solid ✓ amber.

Backdrop-filter needs -webkit prefix for Safari ✓ add.

**Compare renders drawn at load**: drawGlasses(gC1, {th: 0.21rad(12°), phi:-0.07, cy:150, pal:PAL.light}) and pro with proRing:true, th:-10° for variety? Both same angle better for compare: same 12°. Pro ring differentiates ✓ plus pro palette rim darker: PAL.pro rim '#9A9CA3' temple darker.

**Static initial draws**: design svg initial draw before scroll (p=0) ✓ call update once.

**main rAF loop**:
```js
let tick=0;
function loop(t){
  tick=t;
  // hero
  if(heroVis) { speech decay; draw hero }
  // design
  if(desVis) updateDesign();
  // mic demo
  if(micVis) micFrame(t);
  requestAnimationFrame(loop);
}
```
heroVis/desVis/micVis updated via IO with rootMargin '120px'.
Hero draw every frame (idle motion) ✓.
Speech pulse: speechP = max(0, speechP - dt*1.4); on ticker swap set 1. Also small continuous shimmer: speech = speechP*0.9+0.08+... baseline 0.15 so strip slightly lit ✓ plus pulse.

Ticker uses setInterval? Use recursive setTimeout chain with visibility check (skip updates when hidden — but keep simple: still run; cheap). RM: no animation classes.

**updateDesign details**: 
```js
const r=desWrap.getBoundingClientRect();
if(r.bottom<0||r.top>vh) return;
const total=r.height-vh; const p=clamp(-r.top/total,0,1);
const pe=ease(p);
th=lerp(-0.42,1.71,pe) rad (-24°→98°)
phi=lerp(-0.09,0.06,pe)
scale=1+0.13*Math.sin(Math.PI*p)
ty=(0.5-p)*26
svg.style.transform=`translateY(${ty}px) scale(${scale})`
drawGlasses(gDesign,{th,phi,cy:128,pal:PAL.light2? use light, speech: 0.25+0.75*stageOps[1]})
stages & ghosts opacity...
pinBar.style.transform=`scaleX(${p})`
pinCount.textContent = '0'+(1+Math.min(2,Math.floor(p*3)))+' / 03'
shadow: sw=0.62+0.5*|sin(th)| (fraction of art width); tx = Math.sin(th)*36; sh.style.width=(sw*100)+'%'; sh.style.transform=`translateX(calc(-50% + ${tx}px))`; opacity .8? constant.
```
stageOps[i] = smooth01(1-|p-c_i|/0.34) where c = [0.18,0.5,0.82]; apply also translateY((1-o)*14px).

Wait captions band: with ease applied to theta but captions from raw p ✓ ok.

**Counters**:
```js
function animCount(el){ const t=+el.dataset.n, dec=+el.dataset.dec||0; const t0=performance.now(), dur=1600;
 (function f(now){ const k=RM?1:easeOutExpo(min(1,(now-t0)/dur)); el.textContent=(t*k).toFixed(dec); if(k<1) requestAnimationFrame(f); else el.textContent=t.toFixed(dec);})(t0);}
```
IO trigger once at threshold .4.

Units static in markup.

**Form logic** ✓ straightforward.

**Model state**:
```js
let model='halo';
function setModel(m){model=m; document.querySelectorAll('.mpill').forEach(b=>b.setAttribute('aria-pressed', String(b.dataset.model===m)));}
compare buttons: click → setModel; toast(`${name} selected — reserving your pair`); scrollTo preorder.
mpill click → setModel (no toast).
```
Compare button labels static ✓.

doneTxt: `Reservation saved for Halo ${model==='pro'?'Pro':''} — we'll write to ${email} before pre-orders open.`

**Toast fn**:
```js
let toastT; function toast(msg){ toastTxt.textContent=msg; toastEl.classList.add('show'); clearTimeout(toastT); toastT=setTimeout(()=>toastEl.classList.remove('show'),3200);}
```

**Reveal IO** as planned; also for .stat trigger? counters separate IO.

**Transcript loop**:
```js
const SCRIPT=[...6 rows: {who,lang,text,sub?}]
let ti=0;
function nextLine(){
 if(!transVis){ setTimeout(nextLine,800); return; }
 const s=SCRIPT[ti%SCRIPT.length]; ti++;
 const row=document.createElement('div'); row.className='t-row '+s.who;
 row.innerHTML=`<span class="who">${s.who==='them'?'They · ':'You · '}${s.lang}</span><span class="txt">${s.text}</span>${s.sub?`<span class="tsub">${s.sub}</span>`:''}`;
 tRows.appendChild(row);
 requestAnimationFrame(()=>row.classList.add('show'));
 while(tRows.children.length>4) tRows.removeChild(tRows.firstChild);
 setTimeout(nextLine, s.sub?2600:2000);
 if(ti%SCRIPT.length===0){ setTimeout(()=>{ if(transVis) tRows.innerHTML=''; }, 5200);}
}
```
Hmm clearing timing: when loop wraps, wait then clear. With overlapping timeouts risk clearing newly added — wrap point: after last item shown, delay clear 5s while next first line appears at 2s → would be cleared! Fix: clear BEFORE appending first item when ti%len===1 && rows>=len: i.e., at start of cycle: if(ti%SCRIPT.length===0) clear. Do: when starting new cycle, fade out existing (add .show removal?) simply tRows.innerHTML='' before first append ✓ synchronous clean. Rewrite:
```js
function nextLine(){
  if(ti%SCRIPT.length===0) tRows.innerHTML='';
  ...
}
```
✓ neat. RM: no transitions anyway (CSS kills) rows appear instantly, fine.

Mic frame:
```js
function micFrame(t){
 const T=t*0.001;
 const u=(T*0.35)%2; const k=u<1?u:2-u; // ping-pong 0..1
 const sx=34+k*252, sy=44+12*Math.sin(T*2.0);
 // nearest mic
 let bi=0,bd=1e9; MICS.forEach((m,i)=>{const d=(m[0]-sx)**2+(m[1]-sy)**2; if(d<bd){bd=d;bi=i}});
 beam.setAttribute('x1',MICS[bi][0]);... x2 sx y2 sy; beam opacity .85
 micDots.forEach((c,i)=>{const near=(MICS[i][0]-sx)**2+(MICS[i][1]-sy)**2<95**2; c.setAttribute('r',i===bi?4.5:near?3.2:2.2); c.setAttribute('fill', i===bi?'#C98A2E': near?'#B7B0A2':'#CFC9BD')})
 spk.setAttribute('cx',sx); spk.setAttribute('cy',sy);
 waves: r=(T*55)%64; two circles r and (r+32)%64: w1.setAttribute('r',r) opacity (1-r/64)*0.3 ...
}
```
Static SVG parts: mic dots `<circle>` ×6 id-less but select via class .mdot; beam `<line id="beamM">`; speaker `<circle id="spkM" r="3.5" fill="#1B1A17">`; wave circles `<circle class="wv">` ×2 stroke amber fill none.
Glasses outline path: `M96 96 a34 34 0 1 0 64 0 a34...` write two circles + bridge arc: `<circle cx="126" cy="104" r="30">` `<circle cx="194" cy="104" r="30">` `<path d="M148 86 Q160 78 172 86">` stroke.
MICS positions on brows: left lens brow: angles 200°..280°: pts: (126+30cos, 104+30sin): 205°:(98.8,91.3); 245°:(113.3,76.8)? cos245=−0.423→113.3? 126−12.7=113.3; sin245=−0.906→104−27.2=76.8 ✓; 280°: (131.2,74.5). Right mirrored: (228.8? cos for right outer top: mirror xs about 160: (221.2? let me compute right lens center 194: 340−x_left? mirror: xm = 320−x. So (320−98.8)=221.2, (320−113.3)=206.7, (320−131.2)=188.8 ✓.
MICS=[[98.8,91.3],[113.3,76.8],[131.2,74.5],[188.8,74.5],[206.7,76.8],[221.2,91.3]] ✓ symmetric.

Caption under demo? skip.

**Hero draw call**:
```js
function drawHero(t){
 const T=t*0.001;
 const th=0.26+Math.sin(T*0.5)*0.045; // ~15°
 const phi=-0.10+Math.sin(T*0.33)*0.02;
 const speech=Math.min(1,0.16+speechP);
 drawGlasses(gHero,{th,phi,cy:146,pal:PAL.dark,speech});
 gHero.style.transform=`translateY(${Math.sin(T*0.9)*7}px)`;
}
```
0.26 rad ≈ 15°: shows right 3/4 ✓ (temple tip at th=.26: computed similar to θ=24 sample ✓ nice).

**PAL definitions**:
```js
const PAL={
 dark:{rim:'#C9CBD1', temple:'#8D9097', lens:'rgba(168,182,192,0.16)', glint:'rgba(255,255,255,.6)', accent:'#E7B45C', pad:'#B9BBC1', camRing:'#E7B45C'},
 light:{rim:'#7E8087', temple:'#6A6C72', lens:'rgba(38,36,30,0.10)', glint:'rgba(255,255,255,.85)', accent:'#B0781F', pad:'#8E9096', camRing:'#B0781F'},
 pro:{...light, rim:'#5D5F66', temple:'#4E5057', accent:'#B0781F', proRing:true}
};
```
drawGlasses reads o.pal & o.proRing.

mixc helper with hex; shading:
```js
function shade(hex,t){ return mix(hex,'#0B0B0D',t) }
```
rim outer: mix(shade(rim,.55), rim, fR); rim inner: mix(shade(rim,.25), mix(rim,'#FFFFFF',.35), fR)?? compute: inner = mix(rim, '#FFFFFF', 0.30*fR+0.1)? Let me: innerCol = mix(shade(rim,.35), lift(rim,.4), fR) where lift mixes toward white 0.4. OK implement mix(hexA,hexB,t) generic with hex inputs; define lift(h,t)=mix(h,'#FFFFFF',t).

Temple: templeCol = mix(shade(p.temple,.5), lift(p.temple,.25), fTemple). accent strip uses pal.accent (maybe lift with speech: opacity handles).

Brow: browCol=mix(shade(p.rim,.6), lift(p.rim,.15), fR).

Hinge fill: rim outer color darker: shade(rim,.3).

Core also draws a thin lower rim? no.

Also add inner shadow line under brow? skip.

**drawGlasses code sketch (final)** — I'll write it fully in the file. One concern: string concat with toFixed everywhere; N samples: rim 44, lens 36, brow 16, glint 12, proRing 32, temple 6 pts. Total per frame ≈ 250 points → fine.

Also `shape-rendering="geometricPrecision"` on svg? default fine.

**Design svg transform**: applying CSS transform scale to svg element with viewBox — scales rendered content ✓ (transform on svg element itself, CSS). transform-origin center; add transition none (JS-driven per frame) ✓.

**One more check — sticky + rAF initial**: updateDesign uses getBoundingClientRect each frame while visible — fine.

**Ghost words fonts**: system heavy 800. ok.

**Accessibility**: aria-labels on demos minimal; role switches ✓; focus-visible: :focus-visible{outline:2px solid var(--amber);outline-offset:3px}.

**Meta**: title, description meta, theme-color #0A0A0B.

Let me also ensure the halo ring ellipse & glasses relative placement in hero: art container width W; svg height W*0.75; ring width W*1.5 centered top 50% — ring ry small (66/240 → height 0.4 of ring width = 0.6·W·? ring height = W*1.5*0.4=0.6W → its vertical span 0.6W centered → extends ±0.3W around middle — glasses vertical extent 0.75W ±? glasses content vertical ~ rims at cy 146/300 → 0.37..0.75 of height. Ring center at 50% of container = 0.5·0.75W=0.375W from top... container height H=0.75W; ring centered at H*0.52 with height 0.6W=0.8H → spans 0.12H..0.92H ✓ wraps glasses nicely. Ring horizontally 1.5W centered → wider ✓.

Z-order: ring z0 behind glasses svg z1 ✓ ring bottom arc passes behind glasses bottom — since entirely behind ✓ halo effect ok.

Also slight ring rotation −7° gives tilt ✓.

**Preorder mini ring**: width 190px centered.

Alright — also nav CTA & compare buttons trigger scroll: use href="#preorder" anchors (native smooth) for nav; compare buttons are <button> → JS scrollIntoView({behavior:'smooth'}) (RM: auto).

**Potential Safari sticky + overflow clip**: body overflow-x clip ok.

**Compare mini svg height**: viewBox 400×300 → at width 200 height 150; head cells height consistent ✓.

Also draw compare once AFTER fonts? immediate fine.

**Initial reveal of above-fold?** Hero uses data-hero animations (load), not IO ✓. design pin content: stages hidden initially by JS opacity anyway; pin-top visible.

I think the plan is solid. Also double-check `drawGlasses` shapes for **bridge control points projection**: projecting control points independently then using C is geometrically approximate ✓ fine.

**Ear hook self-intersection**: pts 4→5→6 turn downward with normals flipping — ribbon around sharp-ish bend: angle between segments ~35° fine, no flip.

Let me also add subtle **reflection of glasses on "floor"** in design? Skip — shadow enough.

**Ghost word color**: rgba(28,22,10,.055) on #F4F2ED ✓ subtle.

Edge: TITANIUM at 17vw ~ 290px on 1700px screen — width ≈ 8 chars ×0.58em ≈ 4.6em ≈ 1350px < 1700 ✓; WHISPER 7ch fine; SIGNAL fine.

**Numbers section extra**: small footnote row: "Measured with production firmware, September 2025." adds authenticity ✓ muted 12px.

**Preorder heading**: "Be first in line." lead: "Halo ships this spring. Reserve with an email — we'll only charge you when your pair is on its way."

Footer links: Overview(#top) Design Features Specs Compare + Back to top. Brand line: "Halo — every language, in your ear." Bottom: "© 2025 Halo Audio ApS" · "Designed in Copenhagen. Worn everywhere." plus right "A concept page — rendered entirely in code." nice honest.

Time to write final code. I'll write it in one continuous block, carefully. Also include short explanation after. Let me now write, keeping the JS tight but readable with comments in English.

For drawGlasses, final concrete implementation:

```js
function drawGlasses(svg,o){
  const th=o.th, ph=o.phi||0, cy=o.cy, pal=o.pal, D=950;
  const c=Math.cos(th), s=Math.sin(th), cp=Math.cos(ph), sp=Math.sin(ph);
  const pr=p=>{
    const x=p[0]*c-p[2]*s;
    let z=p[0]*s+p[2]*c;
    const y=p[1]*cp-z*sp;
    z=p[1]*sp+z*cp;
    const f=D/(D-z);
    return [200+x*f, cy+y*f, z];
  };
  const F1=n=>n.toFixed(1);
  const poly=(pts,r)=>{let d='';pts.forEach((p,i)=>{const q=pr([p[0]+r*Math.cos(p[3]),p[1]+r*Math.sin(p[3]),p[2]]);d+=(i?'L':'M')+F1(q[0])+' '+F1(q[1]);});return d+'Z';};
```
Hmm cleaner: sample circle helper:
```js
  const circ=(cx,cy3,r,a0,a1,n)=>{let d='';for(let i=0;i<=n;i++){const a=a0+(a1-a0)*i/n;const q=pr([cx+r*Math.cos(a),cy3+r*Math.sin(a),0]);d+=(i?'L':'M')+F1(q[0])+' '+F1(q[1]);}return d;};
  const TAU=Math.PI*2;
  const shapes=[];
  const add=(z,str)=>shapes.push({z,str});
  // facets
  const fR=0.5+0.5*Math.abs(c);
  const rimOut=mixc(mixc(pal.rim,'#0B0B0D',0.55),pal.rim,fR);
  const rimIn =mixc(mixc(pal.rim,'#0B0B0D',0.30),mixc(pal.rim,'#FFFFFF',0.38),fR);
  const browC =mixc(mixc(pal.rim,'#0A0A0C',0.62),mixc(pal.rim,'#0B0B0D',0.25),fR);
  const browL =mixc(mixc(pal.rim,'#0A0A0C',0.35),mixc(pal.rim,'#FFFFFF',0.30),fR);
  ...
  // core
  let core='';
  [ -40, 40 ].forEach(lcx=>{
    core+=`<path d="${circ(lcx,2,31.5,0,TAU,40)}Z" fill="${pal.lens}"/>`;
    const gOp=(0.15+0.5*Math.max(0,c)).toFixed(2);
    core+=`<path d="${circ(lcx,2,26,3.55,5.35,12)}" fill="none" stroke="${pal.glint}" stroke-width="1.6" stroke-linecap="round" opacity="${gOp}"/>`;
    const rimD=circ(lcx,2,33,0,TAU,44)+'Z';
    core+=`<path d="${rimD}" fill="none" stroke="${rimOut}" stroke-width="4.8" stroke-linejoin="round"/>`;
    core+=`<path d="${rimD}" fill="none" stroke="${rimIn}" stroke-width="2.1" stroke-linejoin="round"/>`;
    core+=`<path d="${circ(lcx,1.5? use cy 2, 31.5? brow radius R-1.5=31.5 conflicts lens? brow radius 31.5 covers 28..35 overlapping rim stroke covering 30.6..35.4 hmm brow should be thicker top bar: radius 31.5 width 7 → 28..35 ✓ overlapping rim ✓ good (lens fill radius 31.5 too — brow over lens ok).
    core+=`<path d="${circ(lcx,2,31.5,Math.PI+0.12,TAU-0.12,18)}" fill="none" stroke="${browC}" stroke-width="7" stroke-linecap="round"/>`;
    core+=`<path d="${circ(lcx,2,31.5,Math.PI+0.18,TAU-0.18,18)}" fill="none" stroke="${browL}" stroke-width="2.2" stroke-linecap="round" opacity=".8"/>`;
    // camera dot
    const ca=lcx<0? 3.9 : 5.52; // ~223.5° / 316°... left outer-top: angle π+0.85? compute: 235°=4.10rad; right 305°=5.32rad
    const cq=pr([lcx+R*... wait R=33: cam pos: lcx + 33*cos(a), 2+33*sin(a). For left (lcx=-40): a=4.05 → cos=-0.78? cos(4.05)= -0.79? 4.05rad=232°: cos232=-0.616, sin=-0.788 → (-40-20.3, 2-26)=(-60.3,-24) ✓. right: a=5.38 (308°): cos=0.616,sin=-0.788 → (60.3,-24) ✓ so a = lcx<0?4.05:5.38? For lcx=40: need cos positive: 2π-4.05=2.23? cos(2.23)=-0.61 no. right outer top: angle = TAU-4.05 → cos(5.38? TAU-4.05=2.233; hmm: mirror of angle a across y-axis is π−a? Left point (-60.3,-24) relative left center: cos a=-0.616. Right outer top point relative right center (+20.3,-26): angle with cos=+0.616, sin=-0.788 → a=TAU-0.90? sin negative, cos positive → a=2π-0.903=5.38 ✓ (0.903=asin(0.788)). And left: cos neg sin neg → a=π+0.903=4.045 ✓. So aL=4.045, aR=5.38.
    const cpj=pr([lcx+33*Math.cos(aA),2+33*Math.sin(aA),0]);
    core+=`<circle cx="${F1(cpj[0])}" cy="${F1(cpj[1])}" r="2.3" fill="#131316" stroke="${pal.camRing}" stroke-width=".8" opacity="${camOp}"/>`;
  });
  // bridge
  const b0=pr([-12.5,-16.5,0]),b1=pr([-5,-27.5,-1.2]),b2=pr([5,-27.5,-1.2]),b3=pr([12.5,-16.5,0]);
  const bd=`M${F1(b0[0])} ${F1(b0[1])}C${F1(b1[0])} ${F1(b1[1])} ${F1(b2[0])} ${F1(b2[1])} ${F1(b3[0])} ${F1(b3[1])}`;
  core+=`<path d="${bd}" fill="none" stroke="${browC}" stroke-width="5.4" stroke-linecap="round"/>`;
  core+=`<path d="${bd}" fill="none" stroke="${browL}" stroke-width="1.8" stroke-linecap="round" opacity=".85"/>`;
  // pads
  const padOp=Math.min(1,Math.abs(c)*1.6).toFixed(2);
  [[-10.5,1],[10.5,-1]].forEach(([px,sg])=>{const q=pr([px,11,-5]);core+=`<ellipse cx="${F1(q[0])}" cy="${F1(q[1])}" rx="3.3" ry="5.4" fill="${pal.pad}" opacity="${padOp}" transform="rotate(${18*sg} ${F1(q[0])} ${F1(q[1])})"/>`;});
  if(o.proRing){[-40,40].forEach(lcx=>{core+=`<path d="${circ(lcx,2,41,0,TAU,40)}Z" fill="none" stroke="${pal.accent}" stroke-width="1.4" opacity=".75"/>`;});}
  add(0,`<g>${core}</g>`);
  // temples
  const mkTemple=(mirror)=>{
    const pts=(mirror? [[-73,-7.4,1],[-71,-5.4,-40],[-68,0.6,-88],[-65,11.6,-116],[-63,31.6,-126],[-60,48.6,-119]] : [[73,-9,3],[71,-7,-38],[68,-1,-86],[65,10,-114],[63,30,-124],[60,47,-117]]).map(p=>pr(p));
    const W=[7.4,6.6,5.8,5.2,4.6,3.8];
    const z=pts.reduce((a,p)=>a+p[2],0)/pts.length;
    let g='';
    // ribbon
    const rib=(P,ws)=>{let L='',Rr='';P.forEach((p,i)=>{const a=P[Math.max(0,i-1)],b=P[Math.min(P.length-1,i+1)];let dx=b[0]-a[0],dy=b[1]-a[1];const l=Math.hypot(dx,dy)||1;const nx=-dy/l,ny=dx/l,hw=ws[i]/2;L+=(i?'L':'M')+F1(p[0]+nx*hw)+' '+F1(p[1]+ny*hw);Rr='L'+F1(p[0]-nx*hw)+' '+F1(p[1]-ny*hw)+Rr;});return L+Rr+'Z';};
    const fT=0.5+0.5*(mirror? Math.max(0,-s):Math.max(0,s))*0.9+0.15*Math.max(0,c); clamp to 1: Math.min(1,...)
    const tcol=mixc(mixc(pal.temple,'#0A0A0C',0.5),mixc(pal.temple,'#FFFFFF',0.22),Math.min(1,fT));
    // hinge
    g+=`<circle cx="${F1(pts[0][0])}" cy="${F1(pts[0][1])}" r="4.6" fill="${rimOut}"/>`;
    g+=`<path d="${rib(pts,W)}" fill="${tcol}"/>`;
    g+=`<path d="${rib(pts.slice(1,4),W.slice(1,4).map(w=>w+2.2))}" fill="${pal.accent}" opacity="${(0.25+0.75*(o.speech||0)).toFixed(2)}"/>`;
    // centerline definition
    let cl='';pts.forEach((p,i)=>cl+=(i?'L':'M')+F1(p[0])+' '+F1(p[1]));
    g+=`<path d="${cl}" fill="none" stroke="rgba(10,10,12,.28)" stroke-width="1"/>`;
    add(z,g);
  };
  mkTemple(true); mkTemple(false);
  shapes.sort((a,b)=>a.z-b.z);
  svg.innerHTML=shapes.map(x=>x.str).join('');
}
```
Wait accent strip slice(1,4) → pts indices 1..3 (3 points) ribbons need ≥2 ✓ 3 ok.

Also when mirrored, fT uses -s ✓.

Check hinge circle color rimOut at z computed includes hinge point z (3·c≈3) fine.

Also design svg: cy=128; hero cy=146; compare cy=150.

Note ear hook bottom y: 48.6·pf + cy: cy146 → 146+48.6·0.9≈190 <300 ✓; cy128 → 176 ✓. Top: rim top y=2−33=−31 → cy−31·pf: hero 146−31=115 ✓ within; with phi tilt small shifts fine. Ring positioning computed earlier assumed glasses center ~ cy/300 fraction: hero glasses vertical center ≈ (115+190)/2≈152/300=0.51 ✓ container middle-ish good.

Wait hero art container height = W·0.75 and svg fills it; ring centered at 52% — ok.

**Pitch phi effect on hero**: -0.10 rad ≈ -5.7°: y' = y·cp − z·sp: for rim z=0: y'=y·0.995 ✓ slight; temples z −100: y' = y·0.995 − (−100)(−0.0998)= y·0.995 − 10 → temple tips rise ~10px toward level — subtle perspective ✓.

**Speech pulse**: baseline 0.16 in hero via speech calc ✓; design: pass speech=0.3+0.7·stageOps[1].

**camOp**: `Math.max(0,Math.min(1,1.35-Math.abs(th)/1.15))` → θ=0 →1(cap), θ=90(1.57)→ 1.35−1.366<0 →0 ✓.

Alright, also add slight **drop shadow filter on svg?** No.

**CSS for svgs**: #gHero,#gDesign{display:block;width:100%;height:auto;overflow:visible}.

Also compare svgs overflow visible.

I'm confident. Also compute easeInOut: 
```js
const easeIO=t=>t<0.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;
const easeO=t=>1-Math.pow(1-t,3);
```

**Ticker swap code**:
```js
const tw=document.getElementById('tWrap');
let pi=0;
function setPhrase(){const p=PHRASES[pi%PHRASES.length];tLang.textContent=p.l;tNat.textContent=p.n;tEn.textContent=p.e;speechP=1;}
function tick(){ 
 setTimeout(()=>{
   if(RM){pi++;setPhrase();tick();return;}
   tw.classList.add('out');
   setTimeout(()=>{pi++;setPhrase();tw.classList.remove('out');},380);
   tick();
 },3600);
}
setPhrase();tick();
```
speechP decays in loop: speechP=Math.max(0,speechP-dt*0.9) with dt from rAF timestamps (clamp dt 0..0.05).

RM: still swaps text but no anim ✓.

**Nav theme scan**:
```js
const themed=[...document.querySelectorAll('[data-theme]')];
function navTheme(){
 let cur='dark';
 for(const s of themed){ if(s.getBoundingClientRect().top<=70) cur=s.dataset.theme; }
 nav.classList.toggle('on-light',cur==='light');
}
```
Call within scroll rAF tick (every frame cheap enough with few sections; throttle: run in main loop when scrolled flag). I'll just run in loop every frame — 7 getBoundingClientRect calls/frame ~fine, but can throttle to when scrollY changed. Track lastY.

Also design pin update needs desWrap rect — same loop.

**Set loop**:
```js
let lastY=-1;
function loop(ts){
 const dt=Math.min(0.05,(ts-(pt||ts))/1000); pt=ts;
 speechP=Math.max(0,speechP-dt*0.85);
 if(heroVis) drawHero(ts);
 // design
 const dr=desWrap.getBoundingClientRect();
 if(dr.bottom>-80&&dr.top<vh+80) updateDesign(dr);
 // nav theme only when y changed
 if(window.scrollY!==lastY){lastY=window.scrollY;navTheme();}
 requestAnimationFrame(loop);
}
```
vh=innerHeight update on resize.

heroVis via IO on hero art; if not visible skip draw (also skip when scrolled past). Simplify: compute heroRect in loop? Use IO flag ✓.

RM: loop still needed for design scroll rotation? RM users: rotation on scroll is scroll-linked (ok), but I'll freeze hero idle: drawHero once static. In loop: if(RM) hero drawn only once outside. Keep loop for design + demos gated: if RM, mic demo static (draw one frame with fixed position), transcript fine.

Now, finally write out. Also add `<noscript>` fallback? minor: reveals hidden without JS — add noscript style [data-reveal]{opacity:1}. ✓ good touch.

Also ensure `#gDesign` initial paint before JS loop start: loop starts immediately ✓.

Also compare draw at init ✓.

Double-check the fgrid cell content — demos inside cells; transcript demo height fixed 216px; mic svg height auto.

Let me write the features heading: h2 "Technology that gets out of the way." ✓ with amber period.

Section heads left-aligned; preorder centered; hero centered.

Compare lead: "The same fit and the same fluent ears — Pro adds titanium, two more microphones and a bigger offline brain."

Numbers heading: "Obsession, quantified." lead: "Four numbers we'd put on a poster."? cheesy; lead: "Measured on production hardware. No rounding up." ✓ nice.

Hero eyebrow: "Introducing Halo" with tiny ring svg before text? Text only, letterspaced amber.

Write final copy for design stages (done above).

Also I should double check contrast of ghost words and general aesthetics... fine.

One more consideration — **overall page length**: hero 100svh + design 320vh + features ~ + numbers + compare + preorder + footer ≈ good.

Mobile pin: art width 92vw, cy fine; stage copy bottom; ghost smaller; shadow ok.

Also: on very short landscape phones sticky may cram — acceptable.

**Potential bug**: `circ()` with a0=0,a1=TAU, n=44 then +'Z' — I append 'Z' at call sites where needed (paths that need close: rim (stroke closed), lens fill, proRing). Glint/brow open arcs no Z ✓.

In rimD I appended 'Z' — stroke closed path joins ends ✓ smooth since first==last point anyway (a=0 & TAU same point) → duplicate point; closing fine.

Now, HTML for stats:
```html
<div class="stats">
 <div class="stat" data-reveal><div class="n"><span class="cnt" data-n="43" data-dec="0">0</span></div><p>languages, translated the instant they're spoken</p></div>
 <div class="stat" data-reveal style="--d:.08s"><div class="n"><span class="cnt" data-n="24" data-dec="0">0</span><span class="u">g</span></div><p>on your face — a mechanical watch weighs more</p></div>
 <div class="stat" ... 36 u h ... "of translation per charge, charging case included"
 <div class="stat" ... 0.28 dec 2 u s ... "from their lips to your ear — about one blink"
</div>
```

Counter IO separate targeting .cnt.

OK, and **compare rows content** finalize:
1. Price · pre-order — $349 / $499
2. Frame — Anodized aluminum / Grade-5 titanium
3. Weight — 24 g / 26 g
4. Battery, with case — 30 h / 36 h
5. Microphones — 4 / 6
6. Languages on device — 12 / 26
7. Languages total — 43 / 43
8. Finishes — Graphite · Bone / Graphite · Bone · Raw Ti

Values some with unit spans normal text ✓.

Also add row "Beam-array speakers — ✓ / ✓ (×2)"? checkmarks: use inline svg check in both — fine adds texture: row "Beam-array speakers": check / check + "×2"? Keep textual: "Standard / Dual, adaptive". Eh — keep 8 rows listed.

Air demo default state: unchecked → cloud mode 43. aria-checked false. On check: 26 on device + label "languages · on device". Count animates via quick tween:
```js
function tweenNum(el,to){const from=parseInt(el.textContent)||0;const t0=performance.now();(function f(n){const k=Math.min(1,(n-t0)/600);el.textContent=Math.round(from+(to-from)*easeO(k));if(k<1)requestAnimationFrame(f)})(t0)}
```
RM: set directly.

Also little icons beside air label: cloud / plane swap? Add two tiny svgs toggled by class. Keep: label text only + caption.

**Demo cells ordering in grid**: c7 (transcript), c5 (private), c5 (mics), c7 (offline) — rows: 7+5, 5+7 ✓ stagger reveals --d.

Music banner icons: note svg.

I believe I've covered all requirements: full-screen hero ✓ SVG product illustration ✓ scroll-driven reveals ✓ sticky rotate section ✓ features grid ✓ big animated numbers ✓ two-model comparison ✓ pre-order CTA ✓ system fonts ✓ white space ✓ dark+light ✓ single file, zero external ✓ no alert ✓ real interactions ✓.

Now write the whole thing. I'll aim for clean, consistent code. Given the size, I'll be efficient in CSS but complete.

Also: the reveal for elements inside sticky pin shouldn't use data-reveal (JS-controlled). ✓

Write time. I'll also sanity check a couple of tricky JS spots as I write (template literals inside template literals — avoid nesting issues by simple concatenation where needed).

One subtle thing: in `rib`, widths array must match pts length: accent slice(1,4) widths slice(1,4) length 3 ✓.

For left temple pts (mirror), hinge circle drawn at pts[0] which is (-73,-7.4,1) → projected... ✓.

Also `mixc` hex parse: support '#RRGGBB' only ✓ all palette colors hex except lens (rgba string passed straight through, never mixed) ✓ glint rgba straight ✓.

fT formula: `Math.min(1, 0.42 + 0.48*Math.max(0, side*s) + 0.18*Math.max(0,c))` where side=+1 right, −1 left. θ=0: 0.42+0.18=0.60; θ=90 right: 0.42+0.48+0=0.90 ✓; θ=−24 right: 0.42−0+0.16=0.58, left: 0.42+0.48·0.407+0.16=0.78 (left temple lit at −24 since it faces viewer? at θ=−24, left side toward viewer ✓ correct!).

Great.

Also add tiny **temple tip cap**: skip.

Also for design section I want glasses a touch larger relative to hero — container sizes handle.

Let me also compute pin art translate: `.pin-art{transform:translateX(6vw)}` at ≥1000px — but JS sets style.transform on the svg child, not container ✓ no conflict.

Stage copy width 300px; heading 24px; ghost z0; art z1; copy z2.

The pin-progress: absolute top 30px center: display flex gap 14 align center; count text 11px muted tabular.

Everything set — writing final answer now. The explanation after the code: brief, covering architecture (renderer, scroll system, interactions) and design choices. Keep explanation concise (~10 lines).

Also remember: don't start response with a heading; start talking directly.

Let me write out the complete file mentally-checked piece by piece as I go.

Additional check — CSS var names used consistently: --amber defined in :root; per-theme --acc; buttons use fixed --amber for solid bg (works both themes). .fic uses color:var(--acc) + bg rgba amber. Tag colors var(--acc).

Ticker colors: --acc amber for live; on dark hero ✓.

Input focus ring rgba(231,180,92,.30).

OK writing.

During writing, careful with: `innerHTML` strings quoting; use double quotes in HTML attrs inside JS template literals with backticks — fine.

Also, IDs list: nav, gHero, tWrap,tLang,tNat,tEn, design, gDesign, pinBar, pinCount, pinShadow, ghosts g0..g2, stages s0..s2, tRows, micSvg (beam, spk, w1, w2, mdot class), airSwitch, airNum, airLab, cmp gC1,gC2, resForm, email, ferr, done, doneTxt, toast, toastTxt, mpills class, compare buttons class .js-model.

Counter elements .cnt.

Reveal IO also applied to .fcell etc.

Also compare buttons: `document.querySelectorAll('[data-model]')` — includes mpills; behavior differs by context: compare header buttons also scroll; mpills don't. Give compare buttons extra class .jump. Handler: if btn.classList.contains('jump'){setModel; toast; scroll} else setModel.

Form submit handler with preventDefault ✓.

Edge: scrollIntoView block:'start' with scroll-padding handled by CSS scroll-padding-top on html ✓ (scroll-padding applies to scrollIntoView too ✓).

Final check on hero headline sizes: h1 clamp(42px,7.2vw,92px) two lines; sub 17-19px muted max 560px center.

Write it.

Actually one more nuance: hero `min-height:100svh` + fallback: `min-height:100vh; min-height:100svh;` ✓.

For design wrapper: `.design{height:340vh}` with `.pin{position:sticky;top:0;height:100vh;height:100svh}`. Mobile: height 300vh.

Footer data-theme="dark" ✓ included in nav scan.

Now produce final answer. Code length ~ 900-1000 lines. Go.

Also — subtle: `.cnt` initial textContent "0" — counters run when visible; numbers section below fold ✓.

For `.n` layout: `display:flex;align-items:baseline;justify-content:flex-start` numbers left aligned; stats grid auto-fit minmax(220px,1fr) → on wide 4 cols ✓ borders top each ✓ gap: 0? padding within cell; add column-gap 34px? With auto-fit and gap, border-top lines have gaps — use gap 0 and inner padding 30px 28px 6px 0? cells adjacent borders merge visually fine (single line each). Use gap:0; .stat{padding:36px 30px 10px 0}. Last column extra right space fine.

Media 560px: .n font smaller via clamp already ✓.

OK writing final.

While writing the compare head: put svg then h3 etc; mobile: head cells shrink; buttons wrap.

Let me also make sure JS runs after DOM: script at end of body ✓.

Potential syntax landmine: in template strings I use `${...}` a lot — ensure no stray backticks.

Also `document.fonts`? not needed.

Alright — final write.