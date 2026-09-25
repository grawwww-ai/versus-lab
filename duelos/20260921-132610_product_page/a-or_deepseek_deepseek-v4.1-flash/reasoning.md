We need to create a single HTML file, premium Apple-style landing page for "Halo" smart glasses. Inline SVG illustration, CSS animations, IntersectionObserver scroll animations, sticky scroll section where product rotates/transforms, features grid, animated big numbers, comparison of two models, pre-order CTA.

Let me design carefully.

Structure:
1. Nav (fixed, blurred, thin)
2. Hero: full screen, big headline "Halo", subtitle, SVG glasses illustration animated. Light section? Apple usually light for hero. Let's do dark hero for drama, or light. Requirement: a dark and a light section. Let's do: Hero light → sticky showcase dark → features light → numbers dark → comparison light → CTA dark. That gives both.

Actually let's make hero dark for elegance with glowing accents, then light sections, then dark.

Let me plan the SVG glasses: front view of glasses — two rounded lens frames, bridge, temples hint. Draw with strokes and gradients. Add a subtle glow behind lenses. Animate lens highlight scan.

For the sticky section: sticky container with height ~300vh, inside a sticky viewport with the SVG that rotates in 3D (perspective rotateY) and scales, plus text captions that change. Use scroll progress to drive transforms.

Actually, "product rotates or transforms as you scroll" — I'll do rotateY rotation from 0 to 360? Or a sequence: rotate from -30deg to 30deg and scale, plus lens scanning animation. Let's do rotateY(-40deg) → 0 → 40deg and a slight scale, plus a linear-gradient sweep. And different captions fading in.

Big animated numbers: count up when in view. "18 hours battery", "40+ languages", "38 g weight".

Comparison: two model cards — Halo and Halo Pro. Feature rows with check marks.

Pre-order CTA: big, dark, with price and button.

Typography: system fonts: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Helvetica Neue", Helvetica, Arial, sans-serif.

Let me write the CSS carefully.

Key details:
- Smooth scroll behavior.
- IntersectionObserver reveal: `.reveal` with translateY(40px) opacity 0, → in-view.
- Add stagger via transition-delay set inline or via CSS nth-child.

Let's write.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Halo — Real-time translation glasses</title>
<style>...</style>
</head>
<body>
...
</body>
</html>
```

CSS variables:
```
:root{
  --bg:#000;
  --fg:#f5f5f7;
  --ink:#1d1d1f;
  --muted:#86868b;
  --accent:#0a84ff;  /* blue */
  ...
}
```

Apple style: light sections use #fbfbfd background, dark #000.

Let me write nav: fixed top, height 48px, backdrop-filter blur(20px), background rgba(251,251,253,0.72), border-bottom subtle. But over dark hero it changes... Simplify: nav is fixed with mix-blend? Let's just make it dark-translucent at top and add a class when scrolled past hero? Simpler: nav uses `backdrop-filter: blur(20px)` and background rgba(0,0,0,0.4), text white — but on light sections it'd look wrong.

Alternative: make nav background transparent and use color that works... Hmm. Simplest robust approach: nav has a solid-ish dark translucent always: `background: rgba(20,20,22,0.6); backdrop-filter: blur(20px); color: #f5f5f7;` — over the light sections it will appear as a dark translucent bar. That's acceptable and looks intentional. Actually a dark bar over light content looks a bit odd but Apple does have translucent dark nav on some pages. Hmm.

Better: use JS to toggle nav theme based on which section is under it. That's more work but doable: observe sections with a sentinel. Let's do a simple approach: on scroll, check the element at point (window.innerWidth/2, 24) via document.elementFromPoint and read data-theme attribute of closest section. Actually simpler: keep an array of sections with data-theme and their offsetTop/height; on scroll determine which section contains scrollY + 24. Set nav class.

Let's do that — it's a nice touch.

Now hero:
- Full viewport height, dark background with radial gradient glow.
- H1 "Halo" huge — maybe "Halo" as the product name, plus tagline "Hear the world in your language."
- Actually headline: "Translation, worn." Hmm. Let's do: eyebrow "Halo" small, then big headline "Every conversation, in your language." Then subtext and two buttons.

Apple-ish: Big headline, then product illustration below. Let's do hero as: centered content, h1 with clamp font size ~ 80px, then SVG glasses below, then scroll indicator.

Hero layout: min-height 100vh, flex column center, padding top 120px.

SVG glasses design:

Front view: 
- Two lens shapes: rounded rects with rx. Left lens x=60,y=70,w=170,h=110,rx=45. Right lens x=270... 

Let me set viewBox "0 0 500 220".
- Left lens: rect x=40 y=60 width=180 height=120 rx=54
- Right lens: rect x=280 y=60 width=180 height=120 rx=54
- Bridge: path from (220,100) curve to (280,100): M220 105 C 240 88, 260 88, 280 105
- Temples: lines from x=40,y=80 going left off-canvas: M40 85 L 8 70 ; M460 85 L 492 70

Lens fill: gradient with low opacity + stroke rgba(255,255,255,0.55) width 2.5.
Add inner glow: radial gradient.

Add specular highlight: a small rotated ellipse clipped in lens? Use clipPath.

Also a scanning line inside lenses that animates (translateY) — represents translation. Use CSS animation on a `<g>` with clip-path to lenses. But the sticky section rotates the whole SVG — the scan animation can live inside.

Hmm, but if the same SVG is used in hero and sticky, that's fine — I can reuse by duplicating markup. Let's define the glasses SVG once and copy-paste with different ids for gradients. Or define gradients with ids and reuse across two SVGs — duplicate ids across SVGs in the same document is technically invalid but works... Actually referencing a gradient defined in another SVG in the document works in most browsers if the id is in the DOM. But safer to just duplicate with unique ids (g1/g2).

Let me write a helper: create the SVG markup with a prefix. I'll just write it twice manually with different ids.

Actually simpler: use CSS-only styling inside SVG (fill via CSS classes) so no gradient defs needed... but gradients need defs. I can use `fill: url(#lensA)`.

I'll write two copies. Keep them identical except id prefix. Fine.

Let me design the glasses SVG markup:

```html
<svg class="glasses" viewBox="0 0 520 240" role="img" aria-label="Halo smart glasses">
  <defs>
    <linearGradient id="frameA" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#e8ecf4"/>
      <stop offset="0.45" stop-color="#9aa4b8"/>
      <stop offset="1" stop-color="#5b6478"/>
    </linearGradient>
    <linearGradient id="lensA" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#7fd3ff" stop-opacity="0.30"/>
      <stop offset="0.5" stop-color="#4f8cff" stop-opacity="0.14"/>
      <stop offset="1" stop-color="#c86bff" stop-opacity="0.24"/>
    </linearGradient>
    <linearGradient id="sheenA" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/>
      <stop offset="0.5" stop-color="#fff" stop-opacity="0.5"/>
      <stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="clipL"><rect x="44" y="62" width="184" height="118" rx="52"/></clipPath>
    <clipPath id="clipR"><rect x="292" y="62" width="184" height="118" rx="52"/></clipPath>
  </defs>
  ...
</svg>
```

Hmm coordinates: viewBox 0 0 520 240. Left lens x 44..228, right lens 292..476. Bridge between 228 and 292 at y ~ 100. Temples: from left edge x=44,y=~85 extending to x=6,y=68; mirrored right.

Bridge path: M 228 104 C 244 86, 276 86, 292 104 — that's a downward-ish arc. Actually bridge should arc upward between the lenses: from (228,104) curve up to (292,104) with control points at y=82. Path: `M228 106 C 246 84, 274 84, 292 106`. Good.

Temples: `M44 88 L 10 70` and `M476 88 L 510 70`. Stroke width 8, round cap, gradient stroke.

Frame stroke: rect with stroke url(#frameA), stroke-width 7, fill none. Plus the lens fill rect underneath.

Order: lens fill rects (fill url(#lensA)), then sheen group clipped, then frame strokes, then bridge/temples.

Sheen: within clipL, a rotated rect that animates x from -200 to 400? Use CSS animation on `<g class="sheen">` with transform translateX. Since clipPath is in user space (userSpaceOnUse default is objectBoundingBox for clipPathUnits? Default clipPathUnits="userSpaceOnUse"). Yes default is userSpaceOnUse, so rect coords are in the SVG user space. Good, but if the group is transformed, clip remains in user space — fine.

Animation: 
```
@keyframes sweep { 0%{transform:translateX(-160px)} 100%{transform:translateX(420px)} }
.sheen { animation: sweep 4s ease-in-out infinite; }
```
Hmm translateX in SVG user units via CSS transform works in modern browsers.

Also add a subtle float animation to the whole glasses: translateY.

Add "translation ticker" text? Maybe too much. Could add small floating text pills in HTML around the glasses ("¿Dónde está…?" → "Where is…"). That's cute. Maybe in the sticky section captions instead.

Let's keep hero with glasses + glow behind.

Add a big radial glow div behind (CSS radial-gradient).

Now sticky section (dark):
```html
<section class="sticky-section" id="design">
  <div class="sticky-wrap">
    <div class="sticky-stage">
      <div class="stage-inner">
        <svg .../>
      </div>
      <div class="stage-copy">
        <p class="caption" data-i="0">...</p>
        ...
      </div>
    </div>
  </div>
</section>
```

Simpler: `.sticky-wrap { height: 300vh; }` and `.sticky-stage { position: sticky; top:0; height:100vh; display:grid; place-items:center; }`.

The product transforms based on scroll progress: 
```
const p = (scrollY - sectionTop) / (sectionHeight - innerHeight) // 0..1
rotateY = -35 + p*70  (from -35 to 35)
scale = 0.85 + p*0.25
rotateX = 12 - p*24
```
Plus maybe opacity.

Also change captions: 3 captions, each fades in during its third.

I'll apply transform to `.stage-inner` with `transform: perspective(1200px) rotateX() rotateY() scale()`.

Hmm, "rotates" — rotateY on a flat SVG gives a 3D-ish flip. Good enough and looks nice with perspective.

Actually with a flat front-view SVG, rotating Y makes it thin at 90°. Going from -35 to 35 keeps it visible. Good.

Captions: positioned below or beside. Let's do the stage as a grid: SVG centered, and caption text overlaid at bottom. Each caption absolutely positioned, opacity based on progress.

Let's do 3 captions:
1. "Two lenses. One conversation." / "Live translation appears as subtitles, right where you're looking."
2. "Real-time speech engine" ...
3. "18 hours. All day."

Hmm, but numbers section covers battery. Let's use:
1. "Look. Listen. Understand."
2. "On-device neural translation"
3. "Nothing in your hands"

Progress mapping: caption index = min(2, floor(p*3)). Set active class. Use CSS transitions on opacity/transform.

Then features grid (light section): 6 cards with icon SVGs (simple inline svg strokes), title, text. Grid with border radius 24px, background #f5f5f7 or white with subtle shadow. Apple-ish: use light gray cards.

Big numbers section (dark): 3 stats, count-up animation.

Comparison (light): two cards, Halo and Halo Pro, with specs list, price, "Pre-order" buttons. Highlight Pro with "New" badge.

CTA (dark): big headline "Halo. Available Spring 2026." + price + pre-order button + fine print.

Footer: minimal, small text.

Let's write CSS with care for elegance.

Base:
```css
*{box-sizing:border-box}
html{scroll-behavior:smooth; -webkit-text-size-adjust:100%}
body{margin:0; font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display","SF Pro Text","Helvetica Neue",Helvetica,Arial,sans-serif; background:#000; color:#f5f5f7; -webkit-font-smoothing:antialiased; overflow-x:hidden;}
```

Typography scale with clamp.

Sections: `section{position:relative}`.

Container: max-width 1080px, margin auto, padding 0 24px.

Reveal:
```css
.reveal{opacity:0; transform:translateY(34px); transition: opacity .9s cubic-bezier(.22,1,.36,1), transform .9s cubic-bezier(.22,1,.36,1); will-change:opacity,transform}
.reveal.in{opacity:1; transform:none}
```
Stagger: `.reveal[data-d="1"]{transition-delay:.08s}` etc. Or use inline style transition-delay. I'll set via JS: index within parent * 80ms. Simpler: add data-delay attribute.

Actually let's handle in JS: when observing, set `el.style.transitionDelay = (el.dataset.delay||0)+'ms'`.

Also a scale variant: `.reveal-scale{transform:translateY(34px) scale(.94)}`.

For headline text, maybe do per-word reveal? Keep simpler: whole element.

Let me write the pieces.

Hero:

```html
<section class="hero" data-theme="dark">
  <div class="hero-glow"></div>
  <div class="nav-spacer"></div>
  <div class="hero-inner">
    <p class="eyebrow reveal">Halo</p>
    <h1 class="reveal">Every conversation,<br>in your language.</h1>
    <p class="lede reveal">Smart glasses that translate speech in real time — subtitles in your line of sight, sound in your ears.</p>
    <div class="cta-row reveal">
      <a href="#preorder" class="btn btn-primary">Pre-order</a>
      <a href="#design" class="btn btn-ghost">Learn more</a>
    </div>
    <div class="hero-product reveal reveal-scale">
      <svg .../>
    </div>
  </div>
  <div class="scroll-hint">...</div>
</section>
```

Wait — nav is fixed on top; hero needs padding-top.

Hero height: min-height 100svh, use flex column, justify center, padding: 140px 24px 60px. But with the product below it might exceed. Use min-height 100vh with content that fits. On small screens the SVG scales.

Let me be careful about heights. Hero content: eyebrow (~20px), h1 (2 lines of clamp 40-84px → up to ~170px), lede (~60px), buttons (~50px), product svg (max-width 720px, aspect 520:240 → height ~330px). Total ~ 700px + padding 200 = 900px. On a 800px viewport it overflows → hero taller than viewport. That's OK-ish but "full-screen hero" should be ~100vh. Let me reduce: make SVG max-width 620px → height 286. And h1 clamp max 72px. Total maybe 750px. Fine with padding.

Actually I'll let the hero be min-height 100vh and just let it grow if needed.

Let me now write the numbers section with count-up.

```html
<section class="stats" data-theme="dark">
  <div class="container">
    <h2 class="reveal">Numbers that matter.</h2>
    <div class="stats-grid">
      <div class="stat reveal"><div class="stat-num"><span class="count" data-target="18">0</span><span class="unit">h</span></div><p>Battery life...</p></div>
      ...
    </div>
  </div>
</section>
```

Count-up: on intersect, animate from 0 to target over 1400ms with easeOutExpo.

Targets: 18 (hours), 42 (languages), 38 (grams). Also maybe 0.6 (latency)? Use "9 ms" latency? Let's use decimals: data-target="0.8" data-decimals="1" for "0.8s" latency. Keep 3 stats: 18h, 42 languages, 38g. Maybe add a 4th: 0.4s translation latency. Let's do 4 stats in a row on desktop, 2x2 on mobile. Hmm, 3 is cleaner. I'll do 4: 18h, 42, 38g, 0.4s. Actually the requirement says "big animated numbers (battery life, languages, weight)" — 3 required. I'll do 4 including latency for richness. Eh, let's do 3 for cleanliness and generous whitespace. Hmm, 4 in a row with big numbers looks good. I'll do 4.

Actually with generous white space, 3 is more elegant. Let's do 3: 18 hours, 42 languages, 38 grams.

Comparison section: two cards.

Model A "Halo" — $499. Features: real-time subtitles, 18h battery, 42 languages, titanium frame, IPX4.
Model B "Halo Pro" — $749. Everything in Halo plus: 3D spatial audio, 8 camera-free sensors, live voice dubbing, 36h with case, prescription-ready.

I'll do a proper comparison layout: two columns with a list of rows. Maybe simpler: two cards side by side, each with a title, price, and bullet list with checkmarks. Plus a highlighted "Pro" card.

For "Apple style" comparison, often a table. But with only 2 models, cards are fine. Let's add a feature row list inside each card with checkmarks and some dimmed "—" for missing features. Actually both have most features. Let's structure:

Rows:
- Real-time subtitles: ✓ / ✓
- Live voice dubbing: — / ✓
- Spatial audio: — / ✓
- Battery: 18 h / 36 h (with case)
- Languages: 42 / 42
- Weight: 38 g / 44 g
- Prescription lenses: — / ✓

A table is actually cleaner. Let's do a comparison table with two model columns and feature rows on the left. Styled Apple-like with borders. Responsive: on mobile it might be tight but with small font ok. Hmm, table on mobile is risky.

Let's do two cards, each with a spec list. It's simpler and responsive. And I'll add "checkmark vs dash" rows.

Ok.

CTA section (dark, or maybe the last is dark and comparison light). Order:

1. Hero — dark
2. Sticky showcase — dark (continuous with hero? maybe hero dark, then sticky dark too). Hmm, I want a light section in between for contrast.

Let's do:
1. Hero — dark (#000)
2. Sticky showcase — dark (#000) — continues, then transitions
3. Features — light (#fbfbfd)
4. Stats — dark (#000)
5. Comparison — light (#fbfbfd)
6. Pre-order CTA — dark (#000)
7. Footer — dark

That's good alternation.

Hmm, but hero + sticky both dark makes a long dark stretch. That's actually fine and Apple-like (they do long dark stretches). But maybe make sticky section a slightly different dark, like #060607 with a gradient. OK.

Now, nav theme switching: sections have data-theme. Nav gets class "light" when over a light section: text #1d1d1f, background rgba(251,251,253,0.72).

Let me write JS for that.

```js
const themedSections = [...document.querySelectorAll('[data-theme]')];
function updateNav(){
  const y = 26; // nav center
  let theme = 'dark';
  for (const s of themedSections){
    const r = s.getBoundingClientRect();
    if (r.top <= y && r.bottom > y) { theme = s.dataset.theme; break; }
  }
  nav.classList.toggle('nav-light', theme === 'light');
}
```
Call on scroll (rAF throttled) and on resize.

Reveal observer:
```js
const io = new IntersectionObserver((entries)=>{
  entries.forEach(e=>{
    if(e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target);}
  })
},{threshold:0.15, rootMargin:'0px 0px -8% 0px'});
```
Careful: for tall elements threshold 0.15 may never trigger. Use threshold 0.1 with rootMargin. Elements are small mostly. Fine. Actually for the big stats etc. ok.

Hmm, but for elements taller than viewport, threshold 0.15 could fail. Use `threshold: 0.12`. Our reveals are small. Fine.

Sticky scroll handler with rAF:
```js
function onScroll(){ ... requestAnimationFrame }
```

Let me write the sticky logic:

```js
const stickySection = document.querySelector('.sticky-section');
const stageInner = document.querySelector('.stage-inner');
const captions = [...document.querySelectorAll('.stage-caption')];

function updateSticky(){
  const rect = stickySection.getBoundingClientRect();
  const total = stickySection.offsetHeight - window.innerHeight;
  const p = clamp(-rect.top / total, 0, 1);
  const rotY = -32 + p * 64;
  const rotX = 10 - p * 18;
  const scale = 0.82 + p * 0.32;
  stageInner.style.transform = `perspective(1400px) rotateX(${rotX}deg) rotateY(${rotY}deg) scale(${scale})`;
  // captions
  const idx = Math.min(captions.length-1, Math.floor(p * captions.length));
  captions.forEach((c,i)=> c.classList.toggle('active', i === idx));
}
```

Hmm, with rotateY going -32 → 32, at p=0.5 it's flat. The captions change 0→1→2. Good.

Maybe also add a "glow" hue shift. Keep simple.

Also make the stage-inner have a smooth transition? No — direct scroll mapping, no transition (would lag). Fine.

But `perspective(1400px)` in transform on the same element as rotate — that works in CSS transform functions list: `perspective(1400px) rotateX() rotateY()`. Yes.

Also, add `transform-style: preserve-3d`? Not needed.

Let's also handle the case where the sticky section is out of view — the transform still applies, no big deal.

Now, potential issue: `sticky-section` height 320vh; `offsetHeight - innerHeight` = 220vh of scroll driving the animation. Good.

Captions positioned in the stage: absolutely positioned at bottom center. Let me place the SVG in the center and captions at the bottom. Actually on a phone the SVG + captions may collide. Let's use a grid: `.sticky-stage { display:grid; grid-template-rows: 1fr auto; }` with the product in row 1 and captions in row 2 (fixed height ~ 140px). Captions absolutely positioned within their container, stacked.

Ok.

Let me now write the actual code.

```html
<section class="sticky-section" data-theme="dark" id="design">
  <div class="sticky-stage">
    <div class="stage-product">
      <div class="stage-inner">
        <div class="stage-glow"></div>
        <svg class="glasses" viewBox="0 0 520 240">...</svg>
      </div>
    </div>
    <div class="stage-captions">
      <div class="stage-caption active">
        <h3>Look. Listen. Understand.</h3>
        <p>Subtitles appear at the edge of your vision — never in your way.</p>
      </div>
      ...
    </div>
  </div>
</section>
```

Hmm, the glow inside stage-inner will rotate too — fine, put it outside as a separate absolutely positioned div in stage-product.

Actually the glow should be behind; give stage-product position relative, glow absolute with radial gradient blur.

Let me finalize CSS sizes for the glasses in the sticky stage: max-width 760px, width 90%.

Now writing everything out.

Let me be careful with the SVG sheen animation and reuse in two places (hero and sticky). Two SVGs = two sets of defs with unique ids: `h-` and `s-`.

Actually, I could avoid duplication by using `<use>` with a `<symbol>`? Symbols with gradients... gradient refs inside symbol resolve against the document. It should work: define `<svg style="display:none">` with defs and a symbol, then `<use href="#halo-glasses">` in two places. Gradient ids defined once. That's cleaner! But `display:none` on the defs SVG can break gradient rendering in some browsers... Actually gradients referenced from a hidden SVG (display:none) generally still work in modern browsers, but there have been issues. Safer: `<svg width="0" height="0" style="position:absolute">` — not display:none. That works.

Hmm, but with `<use>` and CSS animations inside the symbol... the sheen animation would be defined in CSS targeting `.sheen` class, which would apply in both instances. But animations inside `<use>` shadow DOM — CSS from the document does apply to shadow content? Actually `<use>` creates a shadow tree; document styles do apply to it in SVG (unlike HTML shadow DOM, SVG use shadow trees inherit styles from the referencing document... hmm, actually no — CSS selectors do not match inside the shadow tree of `<use>` in most implementations).

Safer to duplicate. I'll just write the SVG twice with prefixed ids. It's more verbose but reliable.

Alternatively, avoid animation inside the SVG entirely: do the sheen with a CSS overlay div positioned over the glasses. Hmm, that doesn't align to lens shapes.

OK, duplicate. Let me just write it.

Actually, one more idea to reduce duplication: use a tiny JS function that returns the SVG string with a prefix, and inject into both containers. That's clean and keeps the file shorter. Since everything is inline JS anyway. Let's do that — but then if JS fails, no glasses. Acceptable? It's a demo. Hmm, I'd rather have the hero SVG in HTML. But duplication is ~40 lines twice. It's fine, I'll duplicate for robustness. Actually let me use JS injection — it's elegant, and the whole page relies on JS for animations anyway. Hmm, but "no external resources" — inline JS is fine.

Decision: I'll write the SVG inline twice. More robust, and the reviewer can see the SVG. Actually 80 lines of SVG... it's fine.

Hmm, let me reconsider — I'll do it with a JS template literal and a function `glassesSVG(id)`. It'll be maybe 45 lines of JS and produces both. Cleaner overall and shows good craftsmanship. But if someone disables JS... The page still works because animations are progressive enhancement? No — reveal elements start at opacity 0 and need JS. So JS is required anyway. OK, JS injection it is... 

Hmm, but a reveal element hidden without JS = blank page. Let me add a `<noscript>` fallback? Overkill. But I could make the reveal styles apply only when JS is on: add `document.documentElement.classList.add('js')` at the top of head via inline script, and scope `.js .reveal{opacity:0}`. That's a nice touch. Let's do it.

OK, then SVG injection is fine too. But then with JS disabled there's no product at all. Meh. Let me just duplicate the SVG in HTML. Final decision: duplicate. It's safest and simplest to reason about.

Fine. Let's write.

SVG markup (for hero, prefix "h"):

```html
<svg class="glasses" viewBox="0 0 520 240" aria-hidden="true">
  <defs>
    <linearGradient id="hFrame" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#f2f5fa"/>
      <stop offset=".45" stop-color="#a9b3c6"/>
      <stop offset="1" stop-color="#6b7488"/>
    </linearGradient>
    <linearGradient id="hLens" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#8ad8ff" stop-opacity=".34"/>
      <stop offset=".55" stop-color="#4d7bff" stop-opacity=".16"/>
      <stop offset="1" stop-color="#c07bff" stop-opacity=".26"/>
    </linearGradient>
    <linearGradient id="hSheen" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/>
      <stop offset=".5" stop-color="#fff" stop-opacity=".55"/>
      <stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="hClipL"><rect x="44" y="62" width="184" height="118" rx="54"/></clipPath>
    <clipPath id="hClipR"><rect x="292" y="62" width="184" height="118" rx="54"/></clipPath>
  </defs>

  <!-- lenses -->
  <g>
    <rect x="44" y="62" width="184" height="118" rx="54" fill="url(#hLens)"/>
    <rect x="292" y="62" width="184" height="118" rx="54" fill="url(#hLens)"/>
  </g>

  <!-- sheen sweep -->
  <g clip-path="url(#hClipL)"><rect class="sheen" x="-140" y="40" width="120" height="170" fill="url(#hSheen)" transform="rotate(14 0 0)"/></g>
  <g clip-path="url(#hClipR)"><rect class="sheen" x="-140" y="40" width="120" height="170" fill="url(#hSheen)" transform="rotate(14 0 0)"/></g>
  ...
```

Hmm, animating `transform` via CSS on an element that already has a `transform` attribute — CSS transform overrides the attribute. So the rotate(14) would be lost when CSS animates. Solution: wrap in a `<g>` with the attribute transform, and animate the inner rect with CSS.

Let me restructure: 
```html
<g clip-path="url(#hClipL)">
  <g transform="rotate(14 110 120)">
    <rect class="sheen" x="-160" y="20" width="130" height="220" fill="url(#hSheen)"/>
  </g>
</g>
```
CSS: `.sheen{ animation: sweep 5s cubic-bezier(.5,0,.2,1) infinite; }` with `@keyframes sweep{ 0%{transform:translateX(0)} 55%{transform:translateX(560px)} 100%{transform:translateX(560px)} }`.

Hmm the rect starts at x=-160 and translates to +560 → ends at x=400 which is past the right lens. Each lens has its own copy, each with its own clip. Both sweep simultaneously. Good.

Wait, but the right lens clip is at x 292-476; a rect moving from -160 to 400 will pass through it. Good.

But `translateX` in SVG user units — CSS transforms on SVG elements use user units for translate. Yes (px = user units).

Animation delay so it repeats. With 5s cycle and 55% travel, the sweep takes 2.75s and then pauses 2.25s. Nice.

Let's also make the animation only run... it's fine to always run.

Then frame strokes:

```html
<rect x="44" y="62" width="184" height="118" rx="54" fill="none" stroke="url(#hFrame)" stroke-width="6"/>
<rect x="292" y="62" width="184" height="118" rx="54" fill="none" stroke="url(#hFrame)" stroke-width="6"/>
<path d="M228 106 C 246 82, 274 82, 292 106" fill="none" stroke="url(#hFrame)" stroke-width="6" stroke-linecap="round"/>
<path d="M44 88 L 8 66" stroke="url(#hFrame)" stroke-width="7" stroke-linecap="round"/>
<path d="M476 88 L 512 66" stroke="url(#hFrame)" stroke-width="7" stroke-linecap="round"/>
<!-- temple tips -->
```

Hmm the temples should look like they go back. Add small rounded ends. Fine.

Also add a small camera/sensor dot on the bridge: `<circle cx="260" cy="92" r="4" fill="#0a84ff"/>` maybe with a glow. Actually put a tiny indicator light: `<circle cx="260" cy="86" r="3.5" fill="#4ea1ff"/>` with CSS pulse.

Also add hinge details at (44,88) etc.

Let's also make the frame gradient look metallic. Good.

Wait, the bridge path starts at 228,106 — that's the right edge of the left lens at y=106 (lens vertical center is 62+59=121). At y=106, the rect's edge... the rect spans x 44-228, y 62-180, rx=54. At y=106 (44 above bottom, 44 below top... no, y=106 - 62 = 44 from top; ry=54, so at 44 from top we're within the rounded corner region (corner spans 0-54). So the left edge at y=106 isn't at x=44; the actual edge x = 44 + 54 - sqrt(54² - (54-44)²) = 44 + 54 - sqrt(2916-100)=44+54-53.07=44.93. Hmm so at y=106 the boundary is at x≈44.93 on the left and x≈227.07 on the right. Close enough to 228. Fine, the bridge will visually connect.

Actually let me just put the bridge endpoints at the vertical center-ish, y=110, and start at x=226 → 294. Let's use `M226 112 C 244 84, 276 84, 294 112`. At y=112 (50 from top), corner region: sqrt(54²-46²)=sqrt(2916-2116)=sqrt(800)=28.3, so edge x = 44+54-28.3 = 69.7. Hmm that's way inside. So at y=112 the lens left boundary is at x=69.7 — meaning the lens is quite rounded. So connecting at y=112 to x=226 would attach inside the lens.

Better to connect near the vertical center y=121: at y=121, that's 59 from top, ry=54, so it's in the straight part (since 59>54). Edge at x=44 and x=228. So the bridge should attach at y≈121... but the bridge usually arcs above the center. Let's just attach at y=118 and x=228/292 — at y=118, 56 from top, straight part. And the bridge arc goes up to y≈96 in the middle.

Path: `M228 118 C 248 92, 272 92, 292 118`. Midpoint y at t=0.5: (118 + 3*92 + 3*92 + 118)/8 = (236+552)/8 = 98.5. Good, arcs up to ~98.

Hmm but wait, the arc goes from y=118 up to 98 and back — that's a shallow arc. Fine.

Temples at y=... attach at the outer edge near the straight part: left lens outer edge is x=44, straight from y=116 to y=126 (center 121 ± ... actually the straight part is from y=62+54=116 to y=180-54=126). So only a 10px band! That's a very rounded rect (rx=54, height 118 → nearly pill-shaped). So temple attachment at y=121 only. 

Let me change rx to 40 so the lenses are less extreme. rect x=44 y=62 w=184 h=118 rx=40. Straight part on left/right edges: y from 102 to 140. Better.

Recompute bridge attach: at y=110, 48 from top, ry=40 → corner region (48>40 so straight part). Edge at x=44. Good. So bridge from (228,110) to (292,110), arc up to ~86: `M228 110 C 248 82, 272 82, 292 110`.

Temples: from (44, 100) going left-up to (8, 78). At y=100 that's 38 from top — in the corner region (38<40). Edge x = 44+40-sqrt(1600-4)=44+40-39.95=44.05. Essentially 44. Fine.

Use `M44 100 L 6 76`.

Right: `M476 100 L 514 76`.

Good.

Update clip paths: `<rect x="44" y="62" width="184" height="118" rx="40"/>`.

Now, the sheen rect should cover the lens. Lens is 184x118 at (44,62). A rect with height 220 at y=20 covers y 20-240. Good. Width 130, sweeping from x=-160 to x=400. With rotate(14, 160, 120) applied around... whatever, it'll look fine.

Hmm, actually the rotation around a fixed point with translateX might cause the sheen to not stay parallel. It's fine.

Let me simplify: skip rotation, just a vertical sheen rect. Add a skew via CSS transform? The animation uses transform, so I can't also have a static skew unless I include it in the keyframes. I can: `@keyframes sweep{0%{transform:translateX(0) skewX(-12deg)} ...}`. Sure, but skewX on a rect is fine.

Let's do: `.sheen{ animation: sweep 5.5s ease-in-out infinite; }` and keyframes with `transform: translateX(...) skewX(-14deg)`.

Hmm, actually the `transform` attribute rotate would be overridden by CSS transform on the rect. So use the keyframe approach with skew. Good — no wrapper needed.

Now let's write the full CSS.

```css
:root{
  --dark-bg:#000;
  --dark-fg:#f5f5f7;
  --light-bg:#fbfbfd;
  --light-fg:#1d1d1f;
  --muted-dark:#86868b;
  --muted-light:#6e6e73;
  --blue:#0a84ff;
  --radius:22px;
  --ease:cubic-bezier(.22,1,.36,1);
}
```

Nav:
```css
.nav{
  position:fixed; top:0; left:0; right:0; height:52px; z-index:100;
  display:flex; align-items:center; justify-content:center;
  backdrop-filter:saturate(180%) blur(20px);
  -webkit-backdrop-filter:saturate(180%) blur(20px);
  background:rgba(10,10,12,.55);
  border-bottom:1px solid rgba(255,255,255,.08);
  transition: background .5s var(--ease), border-color .5s var(--ease), color .5s var(--ease);
  color:#f5f5f7;
}
.nav.nav-light{ background:rgba(251,251,253,.72); border-bottom-color:rgba(0,0,0,.08); color:#1d1d1f;}
```

Wait — the nav is fixed at the top over the hero. Initially over dark hero → dark theme. Then over the light features section → light. Good.

Nav content: a small "Halo" wordmark left, links center/right, and a "Pre-order" pill.

```html
<nav class="nav" id="nav">
  <div class="nav-inner">
    <a class="nav-logo" href="#top">Halo</a>
    <div class="nav-links">
      <a href="#design">Design</a>
      <a href="#features">Features</a>
      <a href="#models">Models</a>
    </div>
    <a class="nav-cta" href="#preorder">Pre-order</a>
  </div>
</nav>
```
Hide links on small screens.

Container: `.container{max-width:1100px;margin:0 auto;padding:0 24px}`.

Hero:

```css
.hero{
  min-height:100vh; min-height:100svh;
  display:flex; flex-direction:column; align-items:center; justify-content:center;
  text-align:center; padding: 130px 24px 80px;
  position:relative; overflow:hidden;
  background:#000;
}
.hero-glow{
  position:absolute; inset:-20% -10% auto -10%; height:110%;
  background:
    radial-gradient(50% 45% at 50% 58%, rgba(60,120,255,.28), transparent 70%),
    radial-gradient(40% 40% at 22% 30%, rgba(150,80,255,.18), transparent 70%),
    radial-gradient(40% 40% at 78% 26%, rgba(0,200,255,.14), transparent 70%);
  filter: blur(10px);
  pointer-events:none;
}
```

`.hero h1{ font-size:clamp(40px,7.2vw,84px); line-height:1.04; letter-spacing:-.03em; font-weight:600; margin:14px 0 0; }`

Apple headline weight ~600 with tight tracking.

`.eyebrow{ color:#a1a1a6; font-size:14px; letter-spacing:.28em; text-transform:uppercase; }` — hmm, for the product name "Halo" as an eyebrow with wide tracking looks premium.

`.lede{ max-width:640px; margin:22px auto 0; font-size:clamp(17px,2vw,21px); line-height:1.5; color:#a1a1a6; }`

Buttons:
```css
.btn{ display:inline-flex; align-items:center; gap:8px; padding:14px 28px; border-radius:980px; font-size:17px; font-weight:500; text-decoration:none; transition:transform .35s var(--ease), background .35s, color .35s, box-shadow .35s; }
.btn-primary{ background:#f5f5f7; color:#0a0a0a; }
.btn-primary:hover{ transform:translateY(-2px) scale(1.02); background:#fff; }
.btn-ghost{ color:#f5f5f7; border:1px solid rgba(255,255,255,.28); }
```

Hero product:
```css
.hero-product{ margin-top: 54px; width:100%; max-width:660px; }
.hero-product .glasses{ width:100%; height:auto; display:block; filter: drop-shadow(0 30px 60px rgba(0,80,255,.28)); animation: float 7s ease-in-out infinite; }
```
`.glasses` class used in both places. In the sticky stage, I'll override.

`@keyframes float{ 0%,100%{transform:translateY(0)} 50%{transform:translateY(-14px)} }`

Careful: the SVG has a CSS animation transform AND is inside `.stage-inner` which gets a transform from JS. That's fine (different elements).

Scroll hint: a small chevron or "Scroll" text with a subtle bounce. Optional. I'll add a thin vertical line that pulses. Keep it subtle, positioned at the bottom.

Now sticky section:

```css
.sticky-section{
  position:relative;
  height: 320vh;
  background: linear-gradient(180deg,#000 0%, #05060a 40%, #000 100%);
  color: var(--dark-fg);
}
.sticky-stage{
  position:sticky; top:0; height:100vh; height:100svh;
  display:flex; flex-direction:column; align-items:center; justify-content:center;
  padding: 70px 24px 40px;
  overflow:hidden;
}
.stage-product{ position:relative; width:min(90vw,780px); display:grid; place-items:center; }
.stage-inner{ width:100%; transform-style:preserve-3d; will-change:transform; }
.stage-inner .glasses{ width:100%; height:auto; display:block; filter: drop-shadow(0 40px 80px rgba(0,90,255,.3)); }
```

Wait — `.stage-inner` gets `transform` with perspective from JS. But the glasses inside have `animation:float`? No, only `.hero-product .glasses` has float. Good.

Glow behind: `.stage-glow{position:absolute; width:90%; height:90%; border-radius:50%; background:radial-gradient(circle, rgba(50,110,255,.28), rgba(120,60,255,.12) 45%, transparent 70%); filter:blur(40px);}`

Captions:
```css
.stage-captions{ position:relative; height:120px; width:min(90vw,680px); margin-top:10px; }
.stage-caption{ position:absolute; inset:0; text-align:center; opacity:0; transform:translateY(14px); transition: opacity .6s var(--ease), transform .6s var(--ease); }
.stage-caption.active{ opacity:1; transform:none; }
.stage-caption h3{ font-size:clamp(22px,3vw,32px); font-weight:600; letter-spacing:-.02em; margin:0 0 8px;}
.stage-caption p{ color:#86868b; margin:0; font-size:clamp(15px,1.6vw,17px); line-height:1.5;}
```

Hmm, with the stage as flex column and captions below, total height: product (up to 780px wide → 360px tall) + captions 120 + padding 110 = ~590. Fits in 100vh usually. On short/wide screens the width min(90vw,780) could make it big. Add max-height to stage-product: `max-width: min(90vw, 780px); ` and for short viewports use `@media (max-height:700px){ .stage-product{width:min(70vw,540px)} }`. Eh, I'll just cap the SVG height via `max-height: 46vh` on the glasses and `width:auto`? Hmm, SVG with width auto... Let's set `.stage-inner .glasses{ max-height:48vh; width:100%; height:auto; object-fit:contain }` — doesn't work for SVG the same way. Actually for an inline SVG with viewBox and CSS width:100%, height auto → aspect ratio preserved. If I set max-height, the browser will constrain height and width becomes... with `width:100%` and `max-height`, the SVG gets squished (aspect preserved? no). Hmm.

Simplest: `.stage-product{ width: min(90vw, 780px, 100vh) }`? Can't use vh in min() mixed with vw... actually you can: `min(90vw, 780px, 92vh)` — but the SVG aspect is 520:240 ≈ 2.17, so width W gives height W/2.17. To keep height ≤ 55vh: W ≤ 119vh. So `width: min(90vw, 780px, 110vh)`. That works! min() accepts mixed units.

I'll use `width: min(90vw, 760px, 100vh)`. Then height ≤ 46vh. Good.

Similarly for the hero: `.hero-product{ width: min(88vw, 640px, 90vh) }` — hero also has text above. Maybe `min(88vw, 620px, 55vh)`. Let's use that... hmm on a laptop 800px tall, 55vh = 440px, and 620px width → height 286. So the min picks 440 → width 440 → height 203. That shrinks the glasses a lot. Hmm, 55vh constraint is too aggressive. Let's use `min(88vw, 640px, 100vh)` → height ≤ 46vh. On 800px tall: 46vh=368px... no wait, width min gives height = width/2.17. If width = 640, height = 295 = 37vh. Fine. 100vh only kicks in on very wide-short screens. OK good.

Now features section (light).

```css
.light-section{ background:var(--light-bg); color:var(--light-fg); }
.section-pad{ padding: 140px 0; }
```

Features:
```html
<section class="light-section section-pad" id="features" data-theme="light">
  <div class="container">
    <p class="section-eyebrow reveal">Features</p>
    <h2 class="section-title reveal">Everything you need,<br>nothing you don't.</h2>
    <div class="features-grid">
      <article class="feature reveal">
        <div class="feature-icon">svg</div>
        <h3>Live subtitles</h3>
        <p>...</p>
      </article>
      ...
    </div>
  </div>
</section>
```

Grid: `grid-template-columns: repeat(3, 1fr); gap: 20px;` with responsive.

Feature cards: `background:#fff; border-radius:24px; padding:34px 30px; box-shadow: 0 1px 2px rgba(0,0,0,.04), 0 12px 30px rgba(0,0,0,.05); transition: transform .5s var(--ease), box-shadow .5s;` hover: `translateY(-4px)` and stronger shadow.

Hmm, on a #fbfbfd background, white cards with subtle shadow is nice.

Icons: simple inline SVGs, 28px, stroke currentColor... but color should be the blue accent. Use `stroke:#0a84ff`. Actually Apple uses monochrome. Let's use a subtle gradient-less accent: stroke `#0071e3`.

6 features:
1. Real-time translation — "Speech is translated in under half a second."
2. 42 languages — "From Japanese to Portuguese, on the fly."
3. On-device privacy — "Audio never leaves your frames."
4. Open-ear audio — "Directional speakers keep you present."
5. All-day battery — "18 hours of continuous translation."
6. Featherweight — "38 grams. You'll forget you're wearing them."

Icons: I'll craft simple stroke SVGs: a speech bubble, a globe, a shield, a sound wave, a battery, a feather... Let me do simple ones:
- Bubble: `<path d="M4 6h16v10H8l-4 4z"/>` roughly
- Globe: circle + ellipse + line
- Shield: path
- Wave: three arcs/vertical bars
- Battery: rect + tip
- Feather/weight: a small circle with lines? Use a "leaf"? Let's use a simple "drop"/"diamond". Or use an arrow-down icon. I'll do a simple "scale" glyph... Let's use a small feather-ish shape: path with a curve.

I'll just do decent geometric icons.

Now stats section (dark):

```html
<section class="dark-section section-pad stats" data-theme="dark">
  <div class="container">
    <h2 class="section-title reveal">Small numbers.<br>Big difference.</h2>
    <div class="stats-grid">
      <div class="stat reveal">
        <div class="stat-value"><span class="count" data-to="18" data-dur="1500">0</span><span class="stat-unit">h</span></div>
        <p class="stat-label">Battery life with continuous translation</p>
      </div>
      ...
    </div>
  </div>
</section>
```

`.stat-value{ font-size:clamp(56px,9vw,110px); font-weight:600; letter-spacing:-.04em; line-height:1; background:linear-gradient(180deg,#fff,#8e8e93); -webkit-background-clip:text; background-clip:text; color:transparent; }`

Nice gradient text.

Careful: with `background-clip:text; color:transparent`, the span inside also needs it. Since the parent has it, the child span's text will be transparent too? The gradient is painted on the parent's background clipped to text of the parent including descendants. Yes, that works — the child text is transparent and the parent's clipped background shows through. Actually, the background-clip:text applies to the element's own background, and text of descendants is painted... hmm. The clipped background paints where the text glyphs are (including descendants' glyphs, since the background is behind everything). And the descendant's `color:transparent`? It inherits transparent from parent. But then the descendant creates no new background. So yes, it works — a common technique.

But the counter span will change text — fine.

Stats grid: 3 columns, big numbers, thin dividers.

Now the comparison section (light):

```html
<section class="light-section section-pad" id="models" data-theme="light">
  <div class="container">
    <h2 class="section-title reveal">Two ways to Halo.</h2>
    <div class="models">
      <article class="model reveal">...</article>
      <article class="model model-pro reveal">...</article>
    </div>
  </div>
</section>
```

Model card:
- name, price, subtitle
- list of specs with ✓ / —
- button

`.models{ display:grid; grid-template-columns:1fr 1fr; gap:24px; max-width:900px; margin:0 auto; }`

Pro card highlighted: `border: 2px solid #0071e3` or a dark card. Let's make the Pro card dark (#1d1d1f) with light text — nice contrast within a light section. And a "New" pill.

Spec rows: `display:flex; justify-content:space-between; padding:14px 0; border-bottom:1px solid rgba(0,0,0,.08);` For the dark card, border-bottom rgba(255,255,255,.1).

Checkmark: use a small svg or the character "✓". Use inline SVG for crispness. Meh, use a CSS-drawn check? I'll use a small SVG check icon repeated. Actually simpler: use text "✓" with color green/blue. Fine.

Hmm, let me do rows as: label on the left, value on the right (e.g., "Battery — 18 h"). And a "—" for unavailable.

Rows:
- Real-time subtitles: ✓ / ✓
- Live voice dubbing: — / ✓
- Spatial audio: — / ✓
- Battery life: 18 h / 36 h
- Languages: 42 / 42
- Weight: 38 g / 44 g
- Prescription ready: — / ✓

For ✓ rows the value is "Included". Hmm, keep it clean:

Left column label, right column value.

Let me implement: `<li><span>Real-time subtitles</span><b>Included</b></li>`.

Then price + CTA button at the bottom of each card.

Pre-order section (dark):

```html
<section class="dark-section preorder" id="preorder" data-theme="dark">
  <div class="container preorder-inner">
    <p class="section-eyebrow reveal">Pre-order</p>
    <h2 class="preorder-title reveal">Halo.</h2>  <!-- huge -->
    <p class="lede reveal">From $499. Ships Spring 2026.</p>
    <div class="cta-row reveal">
      <a class="btn btn-primary">Pre-order now</a>
      <a class="btn btn-ghost">Notify me</a>
    </div>
    <p class="fineprint reveal">Free returns within 30 days. Financing available.</p>
  </div>
</section>
```

With a big glow behind.

Footer: dark, small links, copyright.

Now, JS.

```js
document.documentElement.classList.add('js');
```
Put this in a small inline script in <head> so `.js .reveal{opacity:0}` scoping works. Actually simpler: put `.reveal{opacity:0;...}` and add the class immediately at the top of body via a script — but the CSS would apply before the script runs... The script in head runs before body renders, so `document.documentElement.classList.add('js')` in head is safe.

Then CSS: `.js .reveal{ opacity:0; transform:translateY(34px); transition:...}` and `.js .reveal.in{opacity:1; transform:none}`.

Careful with specificity — `.js .reveal.in` (0,3,0) beats `.js .reveal` (0,2,0). Good.

Now, `.reveal-scale` variant: `.js .reveal-scale{ transform: translateY(34px) scale(.94); }` — but `.js .reveal` also sets transform. Order matters: put `.reveal-scale` after. And `.js .reveal-scale.in` needs higher specificity: `.js .reveal.in` is (0,3,0), `.js .reveal-scale` is (0,2,0) — the .in rule wins for transform? `.js .reveal.in { transform:none }` — yes since it's more specific. But for the non-in state, `.js .reveal-scale` (0,2,0) vs `.js .reveal` (0,2,0) — later one wins. So put `.js .reveal-scale` after `.js .reveal`. Good.

Now counting animation function:

```js
function animateCount(el){
  const to = parseFloat(el.dataset.to);
  const dec = parseInt(el.dataset.decimals||'0',10);
  const dur = parseInt(el.dataset.dur||'1600',10);
  const start = performance.now();
  const ease = t => 1 - Math.pow(1-t, 4);
  function frame(now){
    const t = Math.min(1,(now-start)/dur);
    el.textContent = (to*ease(t)).toFixed(dec);
    if(t<1) requestAnimationFrame(frame); else el.textContent = to.toFixed(dec);
  }
  requestAnimationFrame(frame);
}
```

Observe counts separately, or trigger from the same reveal observer. I'll add a separate observer for `[data-to]`.

Now the sticky scroll + nav + everything in one scroll listener with rAF.

```js
let ticking = false;
function onScroll(){
  if(ticking) return;
  ticking = true;
  requestAnimationFrame(()=>{
    updateSticky();
    updateNav();
    ticking = false;
  });
}
window.addEventListener('scroll', onScroll, {passive:true});
window.addEventListener('resize', onScroll);
```

Also call once on load.

updateSticky:
```js
const stickySection = document.querySelector('.sticky-section');
const stageInner = document.getElementById('stageInner');
const captions = [...document.querySelectorAll('.stage-caption')];

function updateSticky(){
  if(!stickySection) return;
  const rect = stickySection.getBoundingClientRect();
  const vh = window.innerHeight;
  const total = stickySection.offsetHeight - vh;
  if(total <= 0) return;
  let p = -rect.top / total;
  p = Math.max(0, Math.min(1, p));
  const rotY = -30 + p*60;
  const rotX = 12 - p*22;
  const sc = 0.84 + p*0.28;
  const ty = (0.5 - p) * 30;  // hmm
  stageInner.style.transform = `perspective(1500px) rotateX(${rotX.toFixed(2)}deg) rotateY(${rotY.toFixed(2)}deg) scale(${sc.toFixed(3)})`;
  const idx = Math.min(captions.length-1, Math.floor(p*captions.length*0.999));
  captions.forEach((c,i)=>c.classList.toggle('active', i===idx));
}
```

Hmm, at p=0, rotY=-30; at p=1, rotY=30; at p=0.5, rotY=0. The captions: 0 for p<0.33, 1 for 0.33-0.66, 2 for >0.66. Good.

But there's a problem: when the sticky section is above the viewport (rect.top > 0), p = negative → clamped to 0. Fine.

Also, when the user first arrives at the sticky section, the glasses appear rotated. That's fine — it's a reveal.

Maybe add opacity for the first 10% to fade in. Keep it.

Also I should account for the fact that p might be exactly 1 at the end. Fine.

Now the nav update. Also handle the nav CTA link colors.

Let's write the final HTML.

One more: smooth scrolling for anchor links — `html{scroll-behavior:smooth}`.

Also for the sticky section — clicking "Learn more" in hero scrolls to #design. Good.

Let me now write everything out properly.

I'll write the SVG icons for features:

1. Translate/subtitles: a speech bubble with lines.
```html
<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
  <path d="M6 8h14a3 3 0 0 1 3 3v8a3 3 0 0 1-3 3h-7l-5 4v-4H6a3 3 0 0 1-3-3v-8a3 3 0 0 1 3-3z"/>
  <path d="M9 14h8M9 18h5"/>
</svg>
```
Hmm the path might be malformed. Let me simplify: use a rounded rect + tail.

```
<path d="M5 6h22a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H14l-6 5v-5H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2z"/>
```
That's a bubble with a tail at the bottom-left of the right part. OK.

Lines inside: `M9 13h14M9 18h9`.

2. Globe:
```html
<circle cx="16" cy="16" r="11"/>
<path d="M5 16h22"/>
<path d="M16 5c3.5 3 3.5 19 0 22M16 5c-3.5 3-3.5 19 0 22"/>
```
Ellipse via path: `M16 5c4 4 4 18 0 22` — good.

3. Shield:
```html
<path d="M16 4l10 4v8c0 6-4.5 10.5-10 12-5.5-1.5-10-6-10-12V8z"/>
<path d="M11.5 16l3 3 6-6"/>
```

4. Sound waves (open-ear audio):
```html
<path d="M7 12v8M12 8v16M17 11v10M22 6v20" />  -- too much
```
Let's do: a speaker + waves.
```html
<path d="M5 13h5l6-5v16l-6-5H5z"/>
<path d="M21 12a6 6 0 0 1 0 8M24.5 9a10 10 0 0 1 0 14"/>
```
Good.

5. Battery:
```html
<rect x="3" y="10" width="22" height="12" rx="3.5"/>
<path d="M28 14v4"/>
<rect x="6" y="13" width="14" height="6" rx="2" fill="currentColor" stroke="none"/>
```
Hmm the fill bar should be shorter. Fine.

6. Feather/weight:
```html
<path d="M25 7c0 8-5 14-13 14H7l-3 3"/>
```
Let's do a simple "feather":
```html
<path d="M26 6c0 9-6 15-15 15H7l-3 3"/>
<path d="M26 6c-9 0-15 6-15 15"/>
```
Meh. Let's use a different icon for weight — a "scales" or just a simple circle-with-arrow-down? I'll use a "layers/diamond":

Actually let's use a droplet-free approach: a "weight" icon as a small filled shape... I'll use a simple "feather"-ish:

```html
<path d="M27 5C15 5 7 13 5 27c14-2 22-10 22-22z"/>
<path d="M5 27L20 12"/>
```
That's a leaf. Good enough for "featherweight". 

Now the check icon for model rows:
```html
<svg class="tick" viewBox="0 0 18 18" ...><path d="M4 9.5l3.5 3.5L14 5.5"/></svg>
```
I'll use CSS to style, or just use text. Let's use inline SVG in each row — that's a lot of repetition. Alternative: use a CSS ::before with a border-drawn checkmark:

```css
.spec-yes::before{
  content:"";
  display:inline-block; width:6px; height:11px;
  border-right:2px solid currentColor; border-bottom:2px solid currentColor;
  transform: rotate(45deg) translate(-1px,-2px);
  margin-right: 8px;
}
```
Hmm, need vertical alignment. Let me use a different approach — a small span with the checkmark drawn.

Actually simplest: value text "Yes"/"No"? Not elegant.

Let me use: `.spec b.val::before{content:"✓ ";}` with color. Simple and works. Use `content:"✓"` styled. Or use "·". I'll do:

```html
<li><span>Real-time subtitles</span><b class="yes">Included</b></li>
<li><span>Live voice dubbing</span><b class="no">—</b></li>
```
And style `.yes{color:#0071e3}`. Clean, no icons needed. Hmm but a checkmark is nicer. Let's do `<b class="yes">✓</b>` with an aria-label? Keep "Included"/"—". Simple. Actually for battery/weight/languages it's a value, so the same slot shows "18 h", "38 g", "42". Consistent: right column shows value or "—".

Good, clean table-like list.

Now let me write everything.

One concern: the `.section-title` reveal has opacity 0 and won't show without JS. We handle with `.js` scoping.

Let me write the code now.

Also add `scroll-margin-top` for anchor targets.

Let me write.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#000000">
<title>Halo — Real-time translation glasses</title>
<script>document.documentElement.classList.add('js');</script>
<style> ... </style>
</head>
<body>
...
<script> ... </script>
</body>
</html>
```

Now the CSS in full.

```css
*,*::before,*::after{box-sizing:border-box}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{
  margin:0;
  background:#000;
  color:#f5f5f7;
  font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  -webkit-font-smoothing:antialiased;
  -moz-osx-font-smoothing:grayscale;
  overflow-x:hidden;
  line-height:1.4;
}
```

Add `font-feature-settings: "ss01"`? no.

Images/SVG: `svg{display:block}`.

Container etc.

Let me now write out the sections with attention to spacing.

Section title style:
```css
.section-title{
  font-size:clamp(32px,5.2vw,60px);
  line-height:1.06;
  letter-spacing:-.025em;
  font-weight:600;
  margin:0 0 18px;
}
```

Section eyebrow:
```css
.eyebrow{
  font-size:13px;
  letter-spacing:.22em;
  text-transform:uppercase;
  font-weight:500;
  color:#0071e3;
  margin:0 0 16px;
}
```
For dark sections, color #6ea8ff.

`.centered{text-align:center}`

Features grid heading centered.

Let me write the features section:

```html
<section class="light-section section-pad" id="features" data-theme="light">
  <div class="container centered">
    <p class="eyebrow reveal">Features</p>
    <h2 class="section-title reveal">See it. Hear it.<br>Understand it.</h2>
    <p class="section-sub reveal">Halo listens to the world around you and quietly hands you the meaning.</p>
    <div class="features-grid">
      ...
    </div>
  </div>
</section>
```

`.section-sub{max-width:620px;margin:0 auto 64px;color:#6e6e73;font-size:clamp(17px,2vw,21px);line-height:1.5;}`

Features grid: `margin-top:64px` instead of section-sub margin. Fine.

Now, the sticky section — one more thought. Since it's 320vh tall and the stage is sticky, the reveal observer doesn't apply. Fine.

Let me also add a small "Halo" label or a progress indicator in the sticky stage? Not needed.

Let me write the stat section:

```html
<section class="dark-section section-pad" data-theme="dark">
  <div class="container centered">
    <p class="eyebrow eyebrow-dark reveal">By the numbers</p>
    <h2 class="section-title reveal">Astonishingly small.<br>Impressively capable.</h2>
    <div class="stats-grid">
      <div class="stat reveal" data-delay="0">
        <div class="stat-value"><span class="count" data-to="18">0</span><span class="stat-unit">h</span></div>
        <p class="stat-label">Battery life with live translation</p>
      </div>
      <div class="stat reveal" data-delay="120">
        <div class="stat-value"><span class="count" data-to="42">0</span><span class="stat-unit">+</span></div>
        <p class="stat-label">Languages and dialects</p>
      </div>
      <div class="stat reveal" data-delay="240">
        <div class="stat-value"><span class="count" data-to="38">0</span><span class="stat-unit">g</span></div>
        <p class="stat-label">Total weight, frame included</p>
      </div>
    </div>
  </div>
</section>
```

`.stats-grid{ display:grid; grid-template-columns:repeat(3,1fr); gap:24px; margin-top:72px; }`

Divider lines between: use border-left on 2nd and 3rd at desktop. Or no dividers, just spacing. Apple uses dividers. I'll add `border-left:1px solid rgba(255,255,255,.1)` on children except the first, only in the desktop media query.

Now: dark section background. `.dark-section{background:#000;color:#f5f5f7}` and `.light-section{background:#fbfbfd;color:#1d1d1f}`.

Section padding: `padding: 150px 0`.

Add a subtle gradient at the boundary? Apple does that. Not needed.

Model cards.

```html
<div class="models">
  <article class="model reveal">
    <h3>Halo</h3>
    <p class="model-tag">The essential pair.</p>
    <p class="model-price"><span>$499</span></p>
    <ul class="specs">
      <li><span>Real-time subtitles</span><b>Included</b></li>
      ...
    </ul>
    <a href="#preorder" class="btn btn-dark">Pre-order</a>
  </article>
  <article class="model model-pro reveal" data-delay="120">
    <span class="badge">New</span>
    ...
  </article>
</div>
```

`.model{background:#fff;border-radius:28px;padding:40px 34px;box-shadow:0 2px 6px rgba(0,0,0,.05),0 24px 48px -24px rgba(0,0,0,.12); display:flex;flex-direction:column;}`
`.model-pro{background:#1d1d1f;color:#f5f5f7;box-shadow:0 30px 60px -20px rgba(0,0,0,.4);}`

`.specs{list-style:none;padding:0;margin:28px 0 32px;flex:1}`
`.specs li{display:flex;justify-content:space-between;gap:12px;padding:13px 0;border-bottom:1px solid rgba(0,0,0,.08);font-size:15px}`
`.model-pro .specs li{border-bottom-color:rgba(255,255,255,.12)}`
`.specs span{color:#6e6e73}` `.model-pro .specs span{color:#a1a1a6}`

`.specs b{font-weight:500}`

Buttons in the model cards: `btn btn-dark` = background #1d1d1f, color white. `btn btn-light` = background #f5f5f7, color #1d1d1f... for the dark card, use white button.

`.btn-dark{background:#1d1d1f;color:#fff}` `.model-pro .btn{background:#f5f5f7;color:#000}`

Hmm, use classes: `.btn-solid-dark` and `.btn-solid-light`. I'll handle with `.model .btn` base and overrides.

Let's just write inline-ish classes.

OK, and the pre-order section.

Alright, writing it all now. I'll be thorough.

For the badges: `.badge{position:absolute;top:24px;right:24px;...}` — need `.model{position:relative}`.

Let me write final code.

One thing about the `sheen` animation and `prefers-reduced-motion`. Add:

```css
@media (prefers-reduced-motion: reduce){
  *{animation-duration:.001ms !important;animation-iteration-count:1 !important;transition-duration:.001ms !important}
  html{scroll-behavior:auto}
}
```
But that would break the reveal transitions (they'd be instant — which is fine, elements still appear). And the count-up is JS; add a check there too. OK.

Careful: this would also make `.sheen` animation instant, fine.

Now, writing.

Also: the hero has `padding-top:130px` to clear the nav.

Let me write out the full file.

For the sticky stage positioning, `overflow:hidden` on sticky-stage might cause issues with sticky? No, overflow on the sticky element itself is fine.

Hmm, actually `overflow:hidden` on the parent of a sticky element breaks sticky. Here sticky-stage IS the sticky element (position:sticky), and its parent is sticky-section. Giving sticky-stage `overflow:hidden` is fine.

Let me write the code.

Final check on the glasses SVG reusability — I'll write it with hero prefix `h` and stage prefix `s`.

Let me write the sheen keyframes:

```css
@keyframes sheen{
  0%   { transform: translateX(0) skewX(-16deg); }
  55%  { transform: translateX(600px) skewX(-16deg); }
  100% { transform: translateX(600px) skewX(-16deg); }
}
.sheen{ animation: sheen 5.5s cubic-bezier(.45,0,.55,1) infinite; }
```

The rect is at x=-160 width 130 → covers -160..-30 at start. Translating 600 → -440.. no wait, translateX(600) moves it to 440..570. Lenses are at 44..228 and 292..476. So the sweep passes through both. 

Add a small stagger between left and right lens sheen? They'd both be identical since both rects are at the same x. That's fine — a single light sweep across both lenses.

OK. Also, the sheen rect has `fill="url(#hSheen)"` which is a horizontal gradient white transparent→white→transparent. With skew it looks like a light bar.

But the gradient uses objectBoundingBox units by default for linearGradient — gradientUnits default is objectBoundingBox. x1=0,y1=0,x2=1,y2=0 → horizontal across the rect. Good.

Now writing the file for real.

Also, for the hero product drop-shadow, `filter: drop-shadow(...)` on the SVG, plus `animation: float`. Both are fine (filter and transform are separate).

Let me write it.

Regarding the responsive features grid:
```css
.features-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:22px;margin-top:70px;text-align:left}
@media(max-width:900px){.features-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:600px){.features-grid{grid-template-columns:1fr}}
```

Stats grid: `@media(max-width:760px){.stats-grid{grid-template-columns:1fr;gap:48px}}`

Models: `@media(max-width:820px){.models{grid-template-columns:1fr}}`

Nav links hidden below 720px.

Also `hero h1` `br` on mobile — fine.

Writing now. I'll produce the final answer.

For the reveal delays, I'll use `data-delay` and JS:

```js
document.querySelectorAll('.reveal').forEach(el=>{
  if(el.dataset.delay) el.style.transitionDelay = el.dataset.delay + 'ms';
});
```

OK.

Let me finalize.

Also add `#top` anchor at the body start for the logo link.

Let me write it all out.

One more consideration for the caption container height: on narrow screens, the captions might wrap to 3 lines. Set min-height 130px. And use `position:absolute` with top:0. Fine.

Actually, since captions are absolutely positioned within a fixed-height container, long captions could overflow. Set the container height to `clamp(120px, 18vh, 160px)`. Good enough.

Writing.

Final code:

I need to double check the `min()` in width with mixed units: `width: min(90vw, 760px, 100vh)`. CSS min() supports mixed units. Yes.

Let me write it.