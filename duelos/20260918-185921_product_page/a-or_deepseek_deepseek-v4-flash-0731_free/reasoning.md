The user wants a self-contained HTML file for a premium product landing page for "Halo" smart glasses, styled like Apple. I need inline SVG for product illustrations, scroll-driven animations using IntersectionObserver, a sticky rotation section, features grid, animated stats, model comparison, and pre-order CTA. Dark and light sections. System fonts only. No external resources.

Let me plan the sections:

1.  **Nav bar** - minimal, transparent to solid.
2.  **Hero** - full screen, large headline, SVG glasses illustration, subtle fade/scale on load.
3.  **Sticky Product Transform** - sticky container, glasses rotate or transform as you scroll (change transform based on scroll progress).
4.  **Features Grid** - grid of feature cards, fade/slide in on scroll.
5.  **Animated Numbers** - big numbers counting up when in view.
6.  **Comparison** - two models side by side.
7.  **Pre-order CTA** - large button, final section.
8.  **Footer** - simple.

Let me design the SVG for smart glasses. I'll make a front-facing pair of glasses with a sleek design. Inside the hero, I can also have the SVG.

For scroll-driven animations, I'll use IntersectionObserver to add a class when in view, triggering CSS transitions.

For the sticky section, I'll make a container with `position: sticky; top: 0; height: 100vh;` and use JavaScript to calculate scroll progress within a parent wrapper, applying rotation/scale to the SVG.

Let me think about the SVG: Halo glasses. Front view. Sleek frame, maybe an oval lens shape, with a glowing LED strip on the arms or front. Since it's "Halo", maybe a circular element. Let's draw a frame:

- Oval left lens, oval right lens.
- Bridge connecting them.
- Arms extending outwards.
- A glowing circuit line on the frame.

I'll use gradients and strokes.

For the animated numbers: battery life (e.g., 24 hours), languages (30), weight (65g). I'll use data attributes and animate with requestAnimationFrame.

Let me write the JS:

```javascript
// IntersectionObserver for .reveal
// Sticky section: compute progress and rotate .sticky-product
// Counter animation
```

Let me structure the HTML carefully.

Dark hero: background black, white text.
Then a white section for features.
Then dark section for sticky rotation? Or white? Let me alternate.

1. Hero (dark)
2. Marquee / intro (white) - short sentence with gradient text? No external gradients okay.
3. Sticky rotation (dark) - product rotates as you scroll. The parent has high height (e.g., 200vh), the child is sticky and inside the SVG rotates.
4. Features grid (white)
5. Animated Numbers (dark)
6. Comparison (white)
7. Pre-order CTA (dark or gradient)
8. Footer (black)

Let me think about the sticky rotation. I'll make a wrapper:

```html
<section id="sticky-section">
  <div class="sticky-inner">
     <div class="sticky-svg"> ... </div>
  </div>
</section>
```

CSS:
```css
#sticky-section { height: 300vh; }
.sticky-inner { position: sticky; top: 0; height: 100vh; display: flex; align-items: center; justify-content: center; overflow: hidden; }
```

JS on scroll: get bounding rect of #sticky-section. progress = (top + viewport height) / (section height + viewport height). Then rotate = progress * 360 maybe.

Now let me craft the SVG for glasses. This is important. I'll create a front-facing smart glasses SVG. Let me use viewBox="0 0 600 400".

Features:
- Left lens: a rounded rectangle or an ellipse. Let's do a futuristic hexagonal/pill shape.
- Right lens.
- Temple arms.
- Camera dot on the side.
- A glowing thin line across the front.

Actually, let's make it look like an Apple-esque glasses with spatial computing. Since it's "Halo", perhaps a circular ring around each lens? Let me try.

Let me draw:

```
<defs>
  <linearGradient id="lensGrad" ...>
  <filter id="glow"> ... </filter>
</defs>
```

Lens shape: A futuristic pill shape: `<path d="M...">`. Or use `<rect rx="40" />`.

Let me define the frame:

Outer frame: path around both eyes and bridge.

Let me use two rounded rectangles for lenses, connected by a bridge.

Center of left lens: x=200, y=200. Width=180, height=140, rx=40.
Center of right lens: x=400, y=200.

So left lens rect: x=110, y=130, width=180, height=140.
Right lens rect: x=310, y=130, width=180, height=140.

Bridge: from x=290 to 310, y=200.

Arms: extending from outer edges at x=110 and x=490, going left and right.

Let me add the temple arms in perspective? Keep it flat but with a gradient.

Also, since it's "smart" glasses with translate in real time, maybe an animated waveform/translating text appearing on the lens. I can overlay a small light-blue glowing line or dots on the lens.

Let me add a camera dot at the top center of the frame.

Let me add a "halo" ring around the rim or floating above the glasses to tie in the name.

Let me write the SVG:

```svg
<svg viewBox="0 0 600 400" xmlns="...">
  <defs>
    <linearGradient id="frameGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#3a3a4a"/>
      <stop offset="100%" stop-color="#1a1a2a"/>
    </linearGradient>
    <linearGradient id="lensGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0ff3" />
      <stop offset="100%" stop-color="#00f3" />
    </linearGradient>
    <linearGradient id="haloGrad" ...>
  </defs>
  <!-- Glow filter -->
  <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
    <feGaussianBlur stdDeviation="8" result="blur" />
    <feComposite in="SourceGraphic" in2="blur" operator="over" />
  </filter>

  <!-- Temples/arms -->
  <path d="M110 200 L30 180 L30 200 Z" ... fill="url(#frameGrad)" />
  <path d="M490 200 L570 180 L570 200 Z" ... />

  <!-- Frame -->
  <rect x="110" y="130" width="180" height="140" rx="40" fill="none" stroke="url(#frameGrad)" stroke-width="12" />
  <rect x="310" y="130" width="180" height="140" rx="40" fill="none" stroke="url(#frameGrad)" stroke-width="12" />
  <path d="M290 200 Q300 180 310 200" stroke="url(#frameGrad)" stroke-width="12" />

  <!-- Lenses' actual fill -->
  <rect x="118" y="138" width="164" height="124" rx="34" fill="url(#lensGrad)" opacity="0.6" />
  <rect x="318" y="138" width="164" height="124" rx="34" fill="url(#lensGrad)" opacity="0.6" />

  <!-- Halo ring effect -->
  <circle cx="600" cy="50" r="40" fill="none" stroke="url(#haloGrad)" stroke-width="4" filter="url(#glow)" />
  
  <!-- Translating text effect on lenses: maybe a glowing line -->
  <line class="scanline" x1="130" y1="200" x2="270" y2="200" stroke="#fff" stroke-width="2" opacity="0.8" />
  <line class="scanline-delay" x1="330" y1="200" x2="470" y2="200" stroke="#fff" stroke-width="2" opacity="0.8" />
</svg>
```

Hmm, let me refine. I want it to look premium. Let me use thin bezels. Use a single path for the two lenses and bridge? Actually, I can use a `path` to create the outer frame.

Let me create a more Apple-like design: continuous rounded bezel.

Path for left lens: M120 170 C120 148 148 130 200 130 C252 130 280 148 280 170 L280 230 C280 252 252 270 200 270 C148 270 120 252 120 230 Z. No, this is complex. Let me use two rects.

Actually, I can use a single `rect` with rx for the whole front including bridge? That would make a "visor" style. But smart glasses typically have two separate lenses. Let me stick with two lenses.

Let me make the frame slightly curved. I'll draw the lens using `<path d="M ...">` to get a nice shape.

Maybe use a "D" or a shield shape. A shield shape would look stylish:

Left lens: M130 160 L270 160 L270 230 A70 70 0 0 1 200 290 A70 70 0 0 1 130 220 Z. Hmm.

Let me keep it simple. Use rounded rect for lenses.

Let me focus on the animations and overall page structure, since the SVG just needs to look decent.

For the sticky section, I'll rotate the glasses 360 degrees based on scroll, and maybe scale it down. While scrolling, it rotates and translates.

Let me write the JS for sticky:

```javascript
const stickySection = document.querySelector('.sticky-container');
const stickyInner = document.querySelector('.sticky-inner');
const product = document.querySelector('.sticky-product');

let stickyHeight = stickySection.offsetHeight;
let currentProgress = 0;

function updateSticky() {
  const rect = stickySection.getBoundingClientRect();
  const viewportHeight = window.innerHeight;
  const visibleStart = Math.max(0, -rect.top);
  const total = stickyHeight + viewportHeight; // Wait, if section height is 300vh...
  
  // Actually, because section is 300vh, and sticky inner is 100vh.
  // When section top hits viewport top, progress=0.
  // When section bottom hits viewport bottom, progress=1.
  let progress = (-rect.top) / (rect.height - viewportHeight);
  progress = Math.max(0, Math.min(1, progress));
  
  // Stop progress at 0 and 1
  // When section starts entering from bottom: rect.top = viewportHeight, then -rect.top = -viewportHeight... hmm.
  
  // Better: progress = (-rect.top) / (rect.height - viewportHeight) gives 0 when section top is at viewport top, and 1 when section bottom is at viewport bottom.
  
  // But if section is 300vh, rect.height = 300vh, viewport=100vh, so progress goes from 0 to 1 as -rect.top goes from 0 to 200vh. That works.
  
  // Wait: rect.top = viewportHeight -> section top is below viewport. -rect.top = -viewportHeight. Not right.
  
  // Let me use:
  // const offset = rect.top; // when section starts entering from bottom, offset = viewportHeight
  // We want progress=0 when offset = viewportHeight (section top below viewport), and progress=1 when section bottom reaches viewport bottom, i.e., offset = - (rect.height - viewportHeight).
  
  // Actually, standard:
  // progress = (viewportHeight - rect.top) / (rect.height - viewportHeight);
  
  let progress = (viewportHeight - rect.top) / (rect.height - viewportHeight);
  progress = Math.max(0, Math.min(1, progress));
  
  if (progress >= 0 && progress <= 1) {
    const rotate = progress * 360;
    const scale = 1 + progress * 0.2;
    product.style.transform = `rotateY(${rotate}deg) scale(${scale})`;
    // adjust opacity?
  }
}
```

Since the product is 2D SVG, rotating it on the Y axis would make it look like a flat object rotating. That would be a nice effect: as you scroll, it rotates in 3D. I'll add `perspective` to the parent. The SVG will rotate on Y, giving a nice 3D flip effect. Let me do that. But since the SVG is flat, rotateY will show the backside, which disappears unless we set backface-visibility. It might look like a card flipping. To make it nice, maybe I should have two elements, front and back? Or just rotate in X? Rotating in Y is classic for glasses. But because the SVG is a single flat image, rotating in Y would make it narrow, then show mirrored, and then come back. We could add a second SVG on the back with mirrored text? Or simply use rotateY and let the backface be visible. Actually, if we rotate a flat element by 90deg, it shows its edge. At >90, it would show the backface mirrored. To avoid that, we can set `backface-visibility: hidden`, so it disappears at 90-270 degrees. But maybe we want continuous rotation. Alternatively, rotate only from 0 to 360, but with `backface-visibility: hidden`, the element disappears during half the scroll. That might be okay, it gives a spinning effect.

But wait, Apple's product pages often have the product stay prominent while the background and text animate. "A sticky section where the product rotates or transforms as you scroll" - rotating the flat SVG in 3D is fine. I'll add a second gradient "back" or a glow so it still looks intentional when turned. Maybe I'll add a background color or a glowing ring behind it. Let me not overcomplicate.

Alternatively, use a continuous 2D rotation (rotateZ). That would be visible from all angles. Glasses spinning in 2D. But Y rotation is more "pro". Let me do a Y rotation with `transform-style: preserve-3d` and place two copies of the SVG back-to-back? That would be cool: front faces out, back faces out. But it's a lot of SVG duplication. Simpler: rotateX? Hmm.

Let me do a Y rotation and accept it flips. I'll also animate scale and opacity.

Actually, let's make it a "Tilt to reveal" effect: as you scroll, the glasses rotate from 0 to 40 degrees, and a glow sweeps across. But the requirement says "rotates or transforms". Let me make it do a full 360-degree Y rotation for dramatic effect.

Let me proceed.

For the counters:

```javascript
function animateCounter(el) {
  const target = +el.dataset.target;
  const duration = 2000;
  const start = performance.now();
  function update(time) {
    const elapsed = time - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(target * eased);
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}
```

Observe the stats section to trigger counters.

For reveal animations:

```javascript
const io = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      if (entry.target.classList.contains('stat-number')) animateCounter(...);
    }
  });
}, { threshold: 0.2 });
```

For `data-target` values: battery 24 hours, languages 30, weight 65 grams.

Let me plan sections with classes and colors:

- `<nav>`: fixed, mix-blend-difference? Or simple.
- `<header class="hero">` dark gradient bg.
- `<section class="intro">` white.
- `<section class="sticky-section">` dark.
- `<section class="features">` white.
- `<section class="stats">` dark.
- `<section class="compare">` white.
- `<section class="cta">` black.
- `<footer>`.

Typography: system font stack `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`.

Buttons: white pill for dark backgrounds, black pill for light.

Let me write the HTML content.

Detailed section design:

**Nav**
- Logo "Halo"
- Nav links: Features, Technology, Compare, Order
- Right: "Order Now" button

**Hero**
- Eyebrow: "Introducing Halo"
- H1: "Translate any conversation. Instantly." Maybe with a span gradient.
- Subhead: "The first pair of smart glasses with real-time translation in the palm of your eye." Hmm.
- CTA buttons: "Order Now" and "Watch the film"
- SVG illustration below, maybe with a glow.
- Scroll indicator.

**Intro** (white)
- A big statement: "Break the chains of language forever." with fade in.

**Sticky section** (dark)
- Sticky inner with product SVG that rotates on scroll.
- Overlay text that changes? Maybe at the start, "Meet Halo", at the end "Translates in real time". But maybe just the product.

**Features grid** (white)
- 6 feature cards with small SVG icons:
  - Real-time Translation: "In 0.3 seconds, Halo translates speech effortlessly."
  - 30 Languages
  - 12-hour battery with charging case up to 24h
  - 65g featherlight
  - Privacy-by-design: no LED lights / lens indicator.
  - Immersive sound: built-in directional speakers.

**Stats** (dark)
- Big animated numbers: 0.3s, 30+, 3.0g? Let's do:
  - 30 Languages
  - 24 Hours battery
  - 65g weight
  - 0.3s latency

**Comparison** (white)
- Two models: "Halo" and "Halo Pro"
- Feature rows: Languages (30 vs 50), Battery (24h vs 36h), Weight (65g vs 68g), Camera (No vs Yes), 4G (No vs Yes), Price ($499 vs $799)
- Highlight the Pro as popular.

**Pre-order CTA** (black)
- Big headline "The future speaks your language."
- Order button
- Fine print: "Orders ship Summer 2025"

**Footer**
- Small links.

Now, let me write the whole thing carefully. I need to include SVG for the product in hero and in sticky section. I can reuse the same SVG or have variations. To keep file size down, I'll define the SVG in a `<template>`? But we can't use external resources; inline SVG can be replicated. Or I can use a `<symbol>` and `<use>`. That's smart. Define the glasses symbol once and reuse multiple places. However, if I use `<use>`, I can't easily apply different effects like gradient fills with `currentColor` in older browsers, but modern browsers handle it. Let me use a `<svg><symbol id="glasses">...</symbol></svg>` at the top of body, and then `<svg viewBox="0 0 600 400"><use href="#glasses" /></svg>` in each place. That is elegant and avoids duplication.

But Browser support for `<use href="#...">` is fine. `href` is supported as `xlink:href` fallback? Modern browsers support plain `href`. I'll use both.

Wait: inside a `symbol`, the `viewBox` is defined on the outer `<svg>`, and the `<use>` will use the symbol's contents. I'll put `viewBox` on the `<use>`? No, on the outer SVG and use the symbol. Actually:

```html
<svg xmlns="http://www.w3.org/2000/svg" style="display:none">
  <symbol id="glasses-icon" viewBox="0 0 600 400">
    ...
  </symbol>
</svg>
```

Then to use:

```html
<svg class="product" viewBox="0 0 600 400">
  <use href="#glasses-icon"></use>
</svg>
```

This should work. The symbol's viewBox will be used? The viewBox on symbol is used when referenced? It's safer to define the viewBox on the symbol and then use `<svg><use href="#glasses-icon"/></svg>` with the symbol having viewBox. Yes, that works.

Let me design the glasses symbol:

I want a modern headset. Let me create:

- Two lenses: rounded rectangles, perhaps with an inner gradient.
- A bridge.
- Temples side arms.
- A small camera dot on the top center.
- A glowing line on the outer edge of each lens.

Let me write a clean SVG.

```svg
<symbol id="glasses" viewBox="0 0 600 400">
  <defs>
    <linearGradient id="frameGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#4a4a5a"/>
      <stop offset="100%" stop-color="#1a1a2a"/>
    </linearGradient>
    <linearGradient id="lensGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#00d9ff" stop-opacity="0.9"/>
      <stop offset="100%" stop-color="#0066ff" stop-opacity="0.9"/>
    </linearGradient>
    <linearGradient id="haloGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#00d9ff" stop-opacity="0"/>
      <stop offset="50%" stop-color="#00d9ff" stop-opacity="1"/>
      <stop offset="100%" stop-color="#00d9ff" stop-opacity="0"/>
    </linearGradient>
    <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="6" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
    <filter id="lensBlur" x="-10%" y="-10%" width="120%" height="120%">
      <feGaussianBlur stdDeviation="2"/>
    </filter>
  </defs>
  
  <!-- Temple arms -->
  <path d="M110 200 L30 170 C25 200 25 230 30 260 Z" fill="url(#frameGrad)" />
  <path d="M490 200 L570 170 C575 200 575 230 570 260 Z" fill="url(#frameGrad)" />
  
  <!-- Small ear pieces -->
  <path d="M30 170 C20 180 15 200 20 220" stroke="url(#frameGrad)" stroke-width="12" fill="none" stroke-linecap="round"/>
  <path d="M570 170 C580 180 585 200 580 220" stroke="url(#frameGrad)" stroke-width="12" fill="none" stroke-linecap="round"/>
  
  <!-- Frame outer -->
  <path d="M300 190 Q290 165 265 165 L235 165 Q210 165 200 190 Q190 215 165 215 L155 215 Q130 215 115 195 Q150 140 200 130 Q250 140 285 195 Z" fill="url(#frameGrad)" />
  
  <!-- Hmm, this is getting messy. -->
```

Maybe simpler: Use a single path for the front frame.

Actually, let me use straightforward shapes:

Frame:

- Left lens outer: rect x=125 y=135 width=170 height=130 rx=35
- Right lens outer: rect x=305 y=135 width=170 height=130 rx=35
- Bridge: rect x=295 y=185 width=10 height=30 rx=5

But drawing with rects is easy:

```svg
<rect x="105" y="125" width="180" height="140" rx="36" fill="none" stroke="url(#frameGrad)" stroke-width="14"/>
<rect x="315" y="125" width="180" height="140" rx="36" fill="none" stroke="url(#frameGrad)" stroke-width="14"/>
<path d="M285 195 L315 195" stroke="url(#frameGrad)" stroke-width="14"/>
```

Temples:

```svg
<path d="M105 165 L25 150" stroke="url(#frameGrad)" stroke-width="14" stroke-linecap="round"/>
<path d="M495 165 L575 150" stroke="url(#frameGrad)" stroke-width="14" stroke-linecap="round"/>
```

Lenses:

```svg
<rect x="116" y="136" width="158" height="118" rx="28" fill="url(#lensGrad)" opacity="0.7"/>
<rect x="326" y="136" width="158" height="118" rx="28" fill="url(#lensGrad)" opacity="0.7"/>
```

Add reflections:

```svg
<path d="M130 150 L200 145 L130 210 Z" fill="#fff" opacity="0.1"/>
<path d="M340 150 L410 145 L340 210 Z" fill="#fff" opacity="0.1"/>
```

Add a Halo ring (circular) above the bridge:

```svg
<circle cx="300" cy="105" r="32" fill="none" stroke="url(#haloGrad)" stroke-width="4"/>
<circle cx="300" cy="105" r="20" fill="url(#lensGrad)" opacity="0.6"/>
```

Actually, maybe the Halo name implies a glowing circle behind the lenses. Let me make a glowing ring around the entire front frame? Or simply a glowing line across the top. I'll add a thin glowing arc above the lenses.

Camera: small circle at top center.

Let me move the front at a slight angle? No, front facing is fine.

For the hero, I'll scale it up.

Let me also add a "digital layer" effect: small text lines or a waveform in the lens to represent translation. I can animate a line with CSS? Since the SVG is in a `<use>`, CSS animations on internal SVG elements require the elements to be in the same document; with `<use>`, the shadow tree styles are a bit tricky. Better to avoid animations inside `<use>` for the symbol if not necessary. I can just put static lines. Or I can define the glasses as a regular inline SVG (not use) for the sections that need animation and use `<use>` for repeat. Actually, since the requirement is scroll-driven, not CSS animations within the SVG, it's fine.

But for the "translate" effect, scanlines moving across the lens would be cool. That could be done with CSS on an overlay div rather than inside the SVG. I'll place a div with a gradient on top of the glass lenses? But the lenses are part of the SVG, so an overlay div positioned absolutely over the SVG would be misaligned. I'll skip the moving scanline inside the SVG, or add a static "transcription" text: small white bars representing subtitles.

Let me add 3 small lines at the bottom of each lens to represent text:

```svg
<rect x="130" y="250" width="60" height="4" rx="2" fill="#fff" opacity="0.6"/>
<rect x="140" y="260" width="50" height="4" rx="2" fill="#fff" opacity="0.3"/>
```

But that might not fit. Let me adjust lens size and position.

Since I'm doing the SVG manually, I'll make the lenses 200x140. Let me just go with a clean, simple design and trust it looks okay.

Actually, let me try using an online mental model of Apple's Vision Pro style. The front looks like a curved glass visor. Maybe I should draw a visor instead of two separate lenses. But the product description says "smart glasses", so two lenses are more recognizable.

Let me find a middle ground: rectangular frames with rounded corners, a uniform dark glass front, with small camera cutouts. Very sleek.

I'll draw:

- Outer continuous frame: a path that goes around both lenses. You can create this by drawing a path:

```
<path d="M105 160 C105 140, 115 125, 135 125 L185 125 C210 125, 225 140, 230 160 L230 230 C230 250, 215 265, 185 265 L135 265 C115 265, 105 250, 105 230 Z" ...>
```

That's too complex. Let's use two rects and a bridge. It'll be fine.

Given time, I'll write a clean SVG with two lenses, a bridge, and arms. Decent aesthetic.

Now the sticky section: I'll place the `<svg class="sticky-glasses">` with the image scaled.

Let me design the reveal animations.

CSS:

```css
.reveal {
  opacity: 0;
  transform: translateY(32px) scale(0.95);
  transition: opacity 0.8s cubic-bezier(0.2, 0.8, 0.2, 1), transform 0.8s cubic-bezier(0.2, 0.8, 0.2, 1);
}
.reveal.visible {
  opacity: 1;
  transform: none;
}
```

The sticky product:

```css
.sticky-glasses {
  width: 80%;
  max-width: 600px;
  transition: transform 0.1s linear;
}
```

Actually, JS sets the transform, so no CSS transition.

Let me build the sections.

I also need a "scroll-driven animation" for the hero: fade/slide in on load. That can be via CSS animations on load.

Let me consider the overall layout height. Sticky section: height: 300vh. Inside, sticky-inner. The JS calculates progress and applies rotateY.

Let me also add a text overlay in the sticky section: "The all-day translator" when progress < 0.5, and "Speak beyond words" when >= 0.5. Could be nice.

Actually, let's include step numbers: "01 / Meet", "02 / Listen", "03 / Translate". As you scroll, it changes. But maybe overkill.

I'll add a headline inside the sticky inner, and the product. The headline fades out as the product rotates. That's good.

Let me define JS:

```javascript
const stickySection = document.querySelector('.sticky-section');
const stickyProduct = document.querySelector('.sticky-product');

function onScroll() {
  const rect = stickySection.getBoundingClientRect();
  const viewportH = window.innerHeight;
  const totalScroll = stickySection.offsetHeight - viewportH;
  let progress = Math.min(Math.max(-rect.top / totalScroll, 0), 1);
  // If section is below, progress = 0?
  // When section top is at viewport bottom, rect.top = viewportH, -rect.top = -viewportH, progress negative => 0.
  // When section top is at viewport top, rect.top = 0, progress = 0.
  // When section bottom is at viewport top, progress = 1. Correct? 
  // scrollable distance: section height - viewport height. If section height = 300vh, viewport=100vh, total=200vh.
  // As we scroll from section top entering viewport until section top exits viewport top? Actually rect.top goes from viewportH to -sectionHeight + viewportH = -200vh. But sticky stops at rect.top = 0? Wait the sticky element remains sticky until the section's bottom reaches the viewport's bottom. So as the section is scrolled through, rect.top goes from viewportH (if below) to -200vh (section height - viewport height = 200vh). So progress = -rect.top / 200vh gives:
  // rect.top = viewportH (100vh) -> progress = -100vh/200vh = -0.5. Not good.
  // We want progress 0 when rect.top = 0? Or when section bottom hits viewport bottom? Let's use:
  // progress = (-rect.top) / (sectionHeight - viewportH)
  // At start (rect.top = viewportH): progress = -viewportH / (300vh - 100vh) = -100/200 = -0.5 => max(0,..)=0.
  // When the section top hits viewport top (rect.top = 0): progress = 0. That means no rotation yet.
  // When the section bottom hits viewport bottom: rect.top = -(300vh-100vh) = -200vh; progress = 200/200 = 1. Good.
  // So progress = clamp(-rect.top / (sectionHeight - viewportH), 0, 1)
  const progress = Math.min(Math.max(-rect.top / totalScroll, 0), 1);
  
  // rotateY 0 to 360
  const rotate = progress * 360;
  const scale = 0.8 + progress * 0.2;
  stickyProduct.style.transform = `perspective(1000px) rotateY(${rotate}deg) scale(${scale})`;
}
window.addEventListener('scroll', onScroll, { passive: true });
```

Wait, but if the section height is 300vh, the sticky element is fixed inside and stays for the whole 200vh scroll. During those 200vh, rect.top goes from 100vh (when section top hits viewport bottom) to -200vh (when section bottom hits viewport top). Wait no: the section is 300vh tall. When you scroll such that section top is at viewport bottom, rect.top = 100vh. When section top reaches viewport top, rect.top = 0. When you scroll further, the section's bottom reaches the viewport's bottom when rect.top = -(300vh - 100vh) = -200vh. But the sticky element will stop sticking when its containing block (the section) exits the viewport. The sticky element is height:100vh. It will stick at top:0 once it hits top, and unstick when the bottom of the section passes the bottom of the sticky element? Actually, the sticky element is inside the section. It sticks while its parent is in view. The parent is 300vh, sticky is 100vh. It will "stick" from when the section top reaches viewport top (rect.top = 0) until the section bottom reaches viewport bottom (rect.top = -200vh). So during that time, progress goes from 0 to 1. That matches. Before that, section is below and sticky hasn't started sticking? Actually, the sticky element with top:0 will be at top:0 only when the parent is scrolled enough. Before the parent reaches, it's not stuck and will move up normally. Wait, sticky element's initial position is in normal flow. The section is 300vh. The sticky element is at the top of the section. As you scroll down, the sticky element moves up with the section until top:0 triggers? Actually, in CSS sticky, with top:0, the element is offset relative to the nearest scrollport. As its containing block (parent) scrolls past, it becomes sticky when its top reaches the viewport top, and remains sticky until the bottom of its parent reaches its bottom. So yes, progress 0 when sticky becomes fixed? Actually, at that moment rect.top = 0, progress = 0. And progress = 1 when it stops sticking (parent bottom reaches viewport bottom). So the formula progress = -rect.top / totalScroll works, but need to account for the fact that at rect.top=0, progress=0. Since -rect.top = 0. At the end, rect.top = -(sectionHeight - vh) = -(300-100) = -200vh. -rect.top = 200vh, totalScroll = 200vh, progress=1. Great.

So the formula works.

However, if the section starts below the viewport (rect.top > 0), -rect.top is negative => progress negative => clamp to 0. Good.

Now, let me create the stats counters.

For the stats, I'll use data attributes and an Observer. Each element with `.counter` gets animated when it enters the viewport.

Let me write the full HTML document now.

I need to be careful with syntax. Let me write the SVG symbol first.

Here's my plan for the SVG symbol `#glasses`:

- viewBox="0 0 600 400"
- defs with gradients and glows
- Shadow on the ground? A subtle ellipse under the glass that scales as if floating.

Let me draw:

```svg
<symbol id="glasses" viewBox="0 0 600 400">
  <defs>
    <linearGradient id="frameGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#4e4e66"/>
      <stop offset="100%" stop-color="#181825"/>
    </linearGradient>
    <linearGradient id="lensGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#00d9ff" stop-opacity="0.75"/>
      <stop offset="100%" stop-color="#0055ff" stop-opacity="0.75"/>
    </linearGradient>
    <linearGradient id="haloGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#00d9ff" stop-opacity="0"/>
      <stop offset="50%" stop-color="#00d9ff" stop-opacity="1"/>
      <stop offset="100%" stop-color="#00d9ff" stop-opacity="0"/>
    </linearGradient>
    <radialGradient id="bgGlow" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0%" stop-color="#00d9ff" stop-opacity="0.2"/>
      <stop offset="100%" stop-color="#00d9ff" stop-opacity="0"/>
    </radialGradient>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="8" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
    <filter id="lensGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  
  <!-- Glow behind -->
  <ellipse cx="300" cy="210" rx="180" ry="90" fill="url(#bgGlow)" />
  
  <!-- Temples -->
  <path d="M120 185 L30 170 C18 168 12 180 16 200 C20 220 24 230 16 240" fill="none" stroke="url(#frameGrad)" stroke-width="14" stroke-linecap="round"/>
  <path d="M480 185 L570 170 C582 168 588 180 584 200 C580 220 576 230 584 240" fill="none" stroke="url(#frameGrad)" stroke-width="14" stroke-linecap="round"/>
  
  <!-- Bridge -->
  <path d="M270 190 Q300 165 330 190" fill="none" stroke="url(#frameGrad)" stroke-width="16" stroke-linecap="round"/>
  
  <!-- Frame lenses with rounded corners -->
  <rect x="120" y="150" width="180" height="130" rx="45" fill="none" stroke="url(#frameGrad)" stroke-width="16"/>
  <rect x="300" y="150" width="180" height="130" rx="45" fill="none" stroke="url(#frameGrad)" stroke-width="16"/>
  
  <!-- Lenses -->
  <rect x="132" y="162" width="156" height="106" rx="36" fill="url(#lensGrad)"/>
  <rect x="312" y="162" width="156" height="106" rx="36" fill="url(#lensGrad)"/>
  
  <!-- Highlight reflection on lenses -->
  <path d="M150 180 L200 168 L160 250 Z" fill="#fff" opacity="0.15"/>
  <path d="M330 180 L380 168 L340 250 Z" fill="#fff" opacity="0.15"/>
  
  <!-- Camera on front top bridge -->
  <circle cx="300" cy="190" r="6" fill="#101018" stroke="#4e4e66" stroke-width="2"/>
  <circle cx="300" cy="189" r="2" fill="#00d9ff" opacity="0.8"/>
  
  <!-- Halo ring -->
  <ellipse cx="300" cy="125" rx="70" ry="20" fill="none" stroke="url(#haloGrad)" stroke-width="4" filter="url(#glow)"/>
  
  <!-- Digital translation lines on the lens (static) -->
  <g opacity="0.5">
    <rect x="145" y="245" width="50" height="4" rx="2" fill="#fff"/>
    <rect x="145" y="255" width="30" height="4" rx="2" fill="#fff" opacity="0.6"/>
    <rect x="325" y="245" width="50" height="4" rx="2" fill="#fff"/>
    <rect x="325" y="255" width="30" height="4" rx="2" fill="#fff" opacity="0.6"/>
  </g>
</symbol>
```

That looks pretty detailed. Let me make sure the frame and lenses line up. Since the frame is at x=120, width=180 => center=210. Right frame: x=300, width=180 => center=390. Overall width 180+180+spacing (300-120-180? Wait, 120+180=300). So frames are adjacent at x=300. The bridge path goes from 270 to 330. Good.

But the right lens is at x=300, not 315. I adjusted. Let me update the lens rects: left inner at x=132 (120+12), right at x=312. Total width: (132+156)=288, leaving frame right border at 288, while frame is at 300-12=288. Perfect.

Actually, with stroke-width=16, the stroke is centered on the rect boundary, so outer edge is at x=120-8=112 and inner at 128. The lens inset is 12 px if lens margin is 12. That's fine.

I need to ensure the frame's r=45 and lens r=36, okay.

Now, let me write the entire HTML.

I'll use no external resources. System fonts.

Let me structure CSS carefully. Use CSS variables maybe.

Color palette:
- Dark bg: #0a0a0f
- Card bg: #14141d
- Text primary: #f5f5f7 (Apple's)
- Text secondary: #aeaec2
- Accent: #00d9ff (cyan)
- Light bg: #ffffff
- Light text: #1d1d1f
- Light secondary: #6e6e73

Buttons:
- Apple style blue? Maybe use gradient cyan to blue for CTA.

Typography sizes:
- Hero h1: clamp(42px, 8vw, 88px), weight 700, letter-spacing: -0.02em
- Section h2: clamp(32px, 5vw, 56px), weight 700
- Body: 18px, line-height 1.5

Spacing: 80px sections, padding 120px.

Let me write the sections now.

I realize I should ensure the full file is self-contained and all inline. Let me draft it in my head, then write.

I'll include a "notification" bar at top? "Introducing Halo — order your pair today." Nice touch.

Let me now write the complete document. I'll be careful with apostrophes and quotes.

For the comparison table, I'll use grid instead of table for responsiveness.

Let me also ensure the scroll-driven animation "product rotates as you scroll" is JS-driven. I'll test the math.

One issue: the glasses symbol uses gradients named "haloGrad", "lensGrad". These IDs are inside the symbol, but when referenced via `<use>`, the DOM is cloned into the SVG root, so IDs should still work. But if there are multiple `<use>` instances, there will be duplicate IDs in the document? Actually, `<use>` clones instances, so IDs may collide, which can cause rendering issues. To avoid this, I can use CSS `currentColor` or avoid repeated `use`. Alternatively, define the SVG in each place (copy-paste). That's safer for ID collisions. Since the file is self-contained, duplication is okay. But that's a lot of duplicated SVG. Alternatively, use a single `<svg>` hidden at the body top with `<defs>` and then each `<svg>` for the product just uses the elements from the defs? Actually, if I put the defs in the top-level hidden SVG, and then use the elements via `<use>`, that's exactly what I'll do. However, duplicate IDs across multiple uses of the same symbol can cause issues if the IDs are not unique. But if each use is a separate instance in a different `<svg>` root, the IDs might still clash. Hmm.

In modern browsers, IDs in SVG symbols are scoped to the symbol's cloned shadow DOM? Actually, marking the symbol definition with `id` attributes inside a `<symbol>` creates IDs in the symbol's "shadow" realm. When duplicated, they might not conflict if referenced within the same SVG root? I'm not entirely sure. To be safe, I'll inline the SVG code twice (hero and sticky). That ensures no ID conflicts. I'll just use the exact same SVG markup. It's some extra bytes but safe.

But wait, in the hero I may want a different scale or class. Inline is fine.

Let me copy the SVG markup into both places. I'll define the SVG inline in each section. For the sticky, I'll also use the same SVG but maybe with a different filter or class.

Alright.

Now, let me write the final code. This will be long. Let me ensure the JS at the bottom handles:

1. IntersectionObserver for `.reveal` elements.
2. Sticky scroll progress rotation.
3. Counter animation for `.counter` elements.

Let me also add a smooth scroll for nav links, and a small progress bar? Not required.

Let me build the comparison. Two cards side by side. Use CSS grid.

Model comparison table with checkmarks and em-dashes instead of X. Use a simple table.

Let me write "Halo" vs "Halo Pro":

- Price: $499 / $799
- Translation latency: 0.3s / 0.1s
- Languages: 30 / 50+
- Battery: 12h / 24h
- Charging case: 24h / 36h
- Weight: 65g / 68g
- 4G LTE: No / Yes
- On-lens display: No / Yes

Highlight Halo Pro with "Most advanced" badge.

Now, the stats section: I'll have 4 numbers:
- 0.3s latency
- 30+ languages
- 24h battery with case
- 65g weight

But the counters should count to these values. For 0.3, I'll store data-target="0.3" and handle decimals. For 65, integer. For 24, integer. For 30, integer.

Let me modify counter to support decimals via data-decimal attribute:

```html
<div class="counter" data-target="0.3" data-decimals="1">0</div>
```

```javascript
const decimalPlaces = +el.dataset.decimals || 0;
el.textContent = (target * eased).toFixed(decimalPlaces);
```

That works.

For the suffix, I'll add a separate span in the HTML: `<span class="suffix">h</span>`.

Let me now write the JS.

Also, ensure the sticky section works: the sticky element must be `position: sticky; top: 0; height: 100vh;` and the wrapper `height: 300vh`. The product rotates based on scroll. But as the section is 300vh, the sticky element stays at top. The JS computes progress using the wrapper's rect.

One caveat: on mobile, `100vh` can be finicky. I'll use `100vh` and also `100lvh` as fallback? Not necessary, but I can use `height: 100vh` on sticky. For the sticky child, `align-items: center` and `justify-content: center`.

Let me also include a "scroll progress" for this sticky: maybe a small progress bar at top of the sticky section? Not needed.

Now, let's write the HTML. I'll be thorough.

Potential issues:
- Ensure the SVG doesn't overflow on mobile. Set max-width: 100% and height: auto.
- For hero SVG, limit width to 800px and center.

Let me start coding.

Given the complexity, I'll write section by section mentally. I'll produce the final file.

I need to make sure there are no external fonts. System fonts only. Use font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif.

Let me choose not to use `xlink:href` because modern browsers support href. I'll use `<svg class="product-svg" viewBox="0 0 600 400"><use href="#glasses"/></svg>`. But I decided to inline the SVG twice. Wait, if I inline it twice, I have to duplicate a big block. That's fine. But for cleanliness, maybe I can use `<svg class="..."><defs>...` in each? No.

Actually, we can define the symbol once and use it twice. Let me test if duplicate IDs from `<use>` cause problems in practice. They usually don't because the gradients are referenced within the same SVG root, and all instances share the same definition? Actually, each `<use>` clone contains its own elements, and its IDs point to the symbol's definitions, but the definitions are inside the `symbol`. Hmm, the `symbol` element has children like `<linearGradient>` with IDs. When `<use>` references the symbol, the gradient element is inside the symbol, and its ID is "lensGrad". When the clone is inserted into the DOM, does it keep the gradient ID? I think yes, but if two clones are both in the DOM, the IDs are duplicated. However, gradient references within the clone use URL(#lensGrad), which resolves to the first element with that ID in the document. Since both are identical, it's fine. So actually, it's safe. Many SVG sprites use this pattern. Good, I'll use `<use>`. That reduces file size.

Let me define the hidden svg with symbol right after `<body>`.

Then in hero:

```html
<svg class="hero-product" viewBox="0 0 600 400" role="img" aria-label="Halo smart glasses">
  <use href="#glasses"></use>
</svg>
```

And sticky:

```html
<svg class="sticky-product" viewBox="0 0 600 400">
  <use href="#glasses"></use>
</svg>
```

This is clean.

Now, in the CSS, `.hero-product` and `.sticky-product` need width. Also, `.hero-product` has a drop-shadow.

Let me make sure the symbol includes the background glow, so it looks nice on dark backgrounds. Since the hero and sticky are dark, and features/compare are white, if I use the same symbol in a white section, the glow might look bad. But I'll only use the SVG in dark sections (hero and sticky). For the comparison, I might use a small static SVG? No, not necessary.

Let me write the page now. I'll be mindful of the overall length but aim for high quality.

Let me draft the HTML:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Halo — Real-Time Translation Glasses</title>
<style>
  /* CSS here */
</style>
</head>
<body>
<svg width="0" height="0" style="position:absolute; width:0; height:0;" aria-hidden="true">
  <defs>
    <linearGradient id="frameGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#4a4a5e"></stop>
      <stop offset="100%" stop-color="#181822"></stop>
    </linearGradient>
    ...
  </defs>
  <symbol id="glasses" viewBox="0 0 600 400">
    ...
  </symbol>
</svg>
...
```

Wait, the `symbol` itself can contain `defs`? Yes, symbol can contain defs. But the defs inside symbol with IDs - when cloned, will those IDs work? I believe yes. But to be safest, I'll put shared defs in the top-level hidden svg's defs, not inside the symbol. Then the symbol references them. Since the symbol is in the same hidden svg, it can reference them. When cloned via `<use>`, the clones are in the same document and reference the top-level defs, so IDs resolve correctly. That solves the ID duplication issue.

So:

```html
<svg width="0" height="0" style="position:absolute;width:0;height:0" aria-hidden="true">
  <defs>
    <linearGradient id="frameGrad" ...>...</linearGradient>
    ...
  </defs>
  <symbol id="glasses" viewBox="0 0 600 400">
    <!-- reference the defs above -->
  </symbol>
</svg>
```

But wait, `symbol` is display:none by default, and defs inside the hidden svg are fine. When `<use>` references the symbol, it clones the symbol's content into the target SVG. The cloned elements can reference IDs in the hidden defs. Good.

Alternatively, keep defs inside symbol; each clone will get its own defs, but the IDs within the clone might clash. But using top-level defs is clean.

However, when using `<use>`, the SVG standard treats the symbol contents as if they were inside the referencing svg, so they can reference global defs. Yes.

Let me implement this.

Now, the CSS.

I'll write a reset:

```css
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
html {
  scroll-behavior: smooth;
}
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  background: #0a0a0f;
  color: #f5f5f7;
  overflow-x: hidden;
}
```

Because the body has dark background initially, but light sections exist. I'll set section backgrounds explicitly.

Nav:

```css
.nav {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 40px;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  background: rgba(10, 10, 15, 0.6);
  border-bottom: 1px solid rgba(255,255,255,0.08);
  transition: background 0.4s ease;
}
.nav-links a {
  color: #f5f5f7;
  text-decoration: none;
  margin: 0 18px;
  font-size: 14px;
}
.nav-cta {
  background: #0071e3;
  border-radius: 980px;
  padding: 8px 16px;
  color: white;
  text-decoration: none;
  font-size: 14px;
}
```

Hero:

```css
.hero {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  background: radial-gradient(ellipse at center, rgba(0, 217, 255, 0.12) 0%, transparent 60%), #0a0a0f;
  padding: 120px 24px 60px;
  position: relative;
  overflow: hidden;
}
.hero-eyebrow {
  color: #00d9ff;
  font-size: 17px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  animation: fadeUp 1s ease both;
}
.hero h1 {
  font-size: clamp(48px, 9vw, 96px);
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1.05;
  max-width: 950px;
  animation: fadeUp 1s 0.1s ease both;
}
.hero h1 .gradient {
  background: linear-gradient(90deg, #00d9ff, #0066ff);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  color: transparent;
}
```

Hmm, `background-clip: text` with `color: transparent` is fine. I'll use `-webkit-text-fill-color: transparent` for Safari.

Continue hero:

```css
.hero-sub {
  font-size: 21px;
  line-height: 1.5;
  color: #a1a1b5;
  max-width: 600px;
  margin: 24px auto 40px;
  animation: fadeUp 1s 0.2s ease both;
}
.hero-ctas {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  justify-content: center;
  animation: fadeUp 1s 0.3s ease both;
}
.btn {
  padding: 12px 28px;
  border-radius: 980px;
  font-size: 17px;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.3s ease;
}
.btn-primary {
  background: #0071e3;
  color: white;
}
.btn-primary:hover { background: #0077ed; transform: scale(1.02); box-shadow: 0 8px 30px rgba(0, 113, 227, 0.4); }
.btn-secondary {
  background: rgba(255,255,255,0.1);
  color: white;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.2);
}
.btn-secondary:hover { background: rgba(255,255,255,0.2); }
```

Hero product:

```css
.hero-product {
  width: min(90%, 700px);
  margin: 40px auto 0;
  filter: drop-shadow(0 20px 60px rgba(0, 0, 0, 0.5));
  animation: heroProduct 1s 0.4s cubic-bezier(0.2, 0.8, 0.2, 1) both;
}
@keyframes heroProduct {
  from { opacity: 0; transform: scale(0.9) translateY(40px); }
  to { opacity: 1; transform: none; }
}
```

Scroll indicator:

```css
.scroll-indicator {
  position: absolute;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  width: 1px;
  height: 40px;
  background: linear-gradient(to bottom, rgba(255,255,255,0.5), transparent);
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0% { transform: translateX(-50%) scaleY(0); opacity: 0; }
  50% { opacity: 1; }
  100% { transform: translateX(-50%) scaleY(1); opacity: 0; }
}
```

Intro / statement (white):

```css
.intro {
  background: #fff;
  color: #1d1d1f;
  padding: 120px 24px;
  text-align: center;
}
.intro h2 {
  font-size: clamp(34px, 6vw, 56px);
  font-weight: 700;
  letter-spacing: -0.02em;
  max-width: 900px;
  margin: 0 auto;
  line-height: 1.1;
}
.intro h2 .accent {
  color: #0071e3;
}
.intro p {
  font-size: 19px;
  color: #6e6e73;
  max-width: 640px;
  margin: 24px auto 0;
  line-height: 1.6;
}
```

Sticky section (dark):

```css
.sticky-section {
  height: 300vh;
  background: #0a0a0f;
  position: relative;
}
.sticky-inner {
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.sticky-label {
  font-size: 18px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #00d9ff;
  margin-bottom: 16px;
}
.sticky-title {
  font-size: clamp(32px, 5vw, 48px);
  font-weight: 700;
  margin-bottom: 32px;
  text-align: center;
}
.sticky-product {
  width: min(80%, 600px);
  transform-style: preserve-3d;
}
```

Reduced motion? Not required, but I can add `@media (prefers-reduced-motion: reduce) { ... }`. It's a nice touch but not necessary. I'll skip for brevity.

Features grid (white):

```css
.features {
  background: #fbfbfd;
  color: #1d1d1f;
  padding: 120px 24px;
}
.features-heading {
  text-align: center;
  font-size: clamp(32px, 5vw, 48px);
  font-weight: 700;
  margin-bottom: 80px;
}
.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 40px;
  max-width: 1100px;
  margin: 0 auto;
}
.feature-card {
  background: white;
  border-radius: 24px;
  padding: 40px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.04);
  border: 1px solid #e5e5e5;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.feature-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 32px rgba(0,0,0,0.08);
}
.feature-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #00d9ff, #0066ff);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}
.feature-icon svg { width: 24px; height: 24px; stroke: white; fill: none; stroke-width: 2; }
.feature-card h3 {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 10px;
}
.feature-card p {
  font-size: 16px;
  color: #6e6e73;
  line-height: 1.5;
}
```

Stats (dark):

```css
.stats {
  background: #0a0a0f;
  padding: 120px 24px;
  text-align: center;
}
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 40px;
  max-width: 1000px;
  margin: 0 auto;
}
.stat-number {
  font-size: clamp(48px, 8vw, 72px);
  font-weight: 800;
  letter-spacing: -0.03em;
  color: #fff;
  line-height: 1;
}
.stat-number .accent { color: #00d9ff; }
.stat-label {
  font-size: 16px;
  color: #a1a1b5;
  margin-top: 12px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
```

Comparison (white):

```css
.compare {
  background: #fff;
  color: #1d1d1f;
  padding: 120px 24px;
}
.compare-heading { text-align: center; font-size: 42px; margin-bottom: 80px; }
.compare-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 32px;
  max-width: 900px;
  margin: 0 auto;
}
.compare-card {
  background: #fbfbfd;
  border-radius: 28px;
  padding: 48px;
  border: 1px solid #ededed;
  position: relative;
  text-align: center;
}
.compare-card.pro {
  background: #0a0a0f;
  color: white;
  border: 1px solid #00d9ff;
}
.compare-card .badge {
  position: absolute;
  top: -14px;
  left: 50%;
  transform: translateX(-50%);
  background: #00d9ff;
  color: #0a0a0f;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 4px 14px;
  border-radius: 980px;
}
.compare-card h3 { font-size: 28px; margin-top: 12px; }
.compare-price { font-size: 48px; font-weight: 800; margin-top: 16px; }
.compare-price span { font-size: 16px; color: #6e6e73; }
.compare-card.pro .compare-price span { color: #a1a1b5; }
.compare-features { list-style: none; margin-top: 32px; text-align: left; }
.compare-features li { padding: 8px 0; font-size: 16px; border-bottom: 1px solid rgba(0,0,0,0.06); display: flex; gap: 10px; align-items: center; }
.compare-card.pro .compare-features li { border-color: rgba(255,255,255,0.1); }
.compare-features .check { color: #00d9ff; }
.compare-features .muted { color: #6e6e73; }
.compare-btn { margin-top: 32px; }
```

CTA (dark):

```css
.cta {
  background: linear-gradient(135deg, #0a0a0f 0%, #00121a 50%, #0a0a0f 100%);
  padding: 160px 24px;
  text-align: center;
  position: relative;
  overflow: hidden;
}
.cta h2 {
  font-size: clamp(40px, 7vw, 72px);
  font-weight: 800;
  letter-spacing: -0.02em;
  max-width: 800px;
  margin: 0 auto;
}
.cta .btn { margin-top: 40px; font-size: 20px; padding: 16px 36px; }
.cta-note { margin-top: 20px; color: #a1a1b5; font-size: 14px; }
```

Footer:

```css
footer {
  background: #050508;
  padding: 40px;
  text-align: center;
  color: #63636e;
  font-size: 13px;
}
```

Reveal classes:

```css
.reveal {
  opacity: 0;
  transform: translateY(40px);
  transition: opacity 0.8s ease, transform 0.8s ease;
}
.reveal.visible {
  opacity: 1;
  transform: none;
}
.reveal-delay-1 { transition-delay: 0.1s; }
.reveal-delay-2 { transition-delay: 0.2s; }
.reveal-delay-3 { transition-delay: 0.3s; }
```

Media queries:

```css
@media (max-width: 768px) {
  .features-grid { grid-template-columns: 1fr; }
  .stat-grid { grid-template-columns: 1fr 1fr; }
  .compare-grid { grid-template-columns: 1fr; }
  .nav-links { display: none; }
}
```

Now for the SVGs/icons in feature cards, I'll use simple inline SVG stroke icons. Use `<path>` for a "globe", "bolt", "battery", "chip", "shield", "sound".

I can use simple SVG paths. Let me keep them simple.

Examples:
- Globe: circle + lines.
- Bolt: polygon.
- Battery: rect + line.
- Chip: rect + pins.
- Shield: path.
- Sound: speaker.

I'll hardcode them.

Now, JavaScript:

```javascript
document.addEventListener('DOMContentLoaded', () => {
  // IntersectionObserver for .reveal
  const io = new IntersectionObserver((entries, obs) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        obs.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });
  document.querySelectorAll('.reveal').forEach(el => io.observe(el));

  // Sticky section product rotation
  const stickySection = document.querySelector('.sticky-section');
  const stickyProduct = document.querySelector('.sticky-product');
  
  if (stickySection && stickyProduct) {
    const updateSticky = () => {
      const rect = stickySection.getBoundingClientRect();
      const vh = window.innerHeight;
      const total = stickySection.offsetHeight - vh;
      let progress = -rect.top / total;
      progress = Math.max(0, Math.min(1, progress));
      const rotate = progress * 360;
      const scale = 0.8 + progress * 0.2;
      stickyProduct.style.transform = `perspective(1000px) rotateX(${progress * 10}deg) rotateY(${rotate}deg) scale(${scale})`;
    };
    updateSticky();
    window.addEventListener('scroll', updateSticky, { passive: true });
    window.addEventListener('resize', updateSticky);
  }

  // Counter animation
  const statSection = document.querySelector('.stats');
  if (statSection) {
    const counters = statSection.querySelectorAll('.counter');
    const animateCounter = (el) => {
      if (el.dataset.animated) return;
      el.dataset.animated = true;
      const target = parseFloat(el.dataset.target);
      const decimals = parseInt(el.dataset.decimals || '0', 10);
      const duration = 2000;
      const start = performance.now();
      const tick = (now) => {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        el.textContent = (target * eased).toFixed(decimals);
        if (progress < 1) requestAnimationFrame(tick);
        else el.textContent = target.toFixed(decimals);
      };
      requestAnimationFrame(tick);
    };
    const statIO = new IntersectionObserver((entries, obs) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          statSection.querySelectorAll('.counter').forEach(el => animateCounter(el));
          obs.disconnect();
        }
      });
    }, { threshold: 0.3 });
    statIO.observe(statSection);
  }

  // Nav background change on scroll
  const nav = document.querySelector('.nav');
  window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
      nav.style.background = 'rgba(10,10,15,0.8)';
      nav.style.borderColor = 'rgba(255,255,255,0.1)';
    } else {
      nav.style.background = 'rgba(10,10,15,0.6)';
      nav.style.borderColor = 'rgba(255,255,255,0.08)';
    }
  });
});
```

Wait, the sticky rotation: `rotateX(${progress * 10}deg)` adds a slight tilt for style. `preserve-3d` is on the sticky product? I set transform-style: preserve-3d in CSS. But for the product itself, when we set transform with perspective and rotateY, we need the parent to have perspective, or use `perspective()` transform function. I used `perspective(1000px)` in the transform, which applies perspective to this element. That's fine.

But note: setting `transform-style: preserve-3d` on the element is useful for its children, not needed because the SVG is flat. It might cause the element to not flatten? Not an issue.

Also, the CSS for `.sticky-product` has `transform-style: preserve-3d;` and no transition. That's okay.

One issue: when the sticky product rotates on Y, because the SVG is flat (no backface), at 90deg and 270deg it will be edge-on, and then show the same image mirrored when >90deg. To avoid looking weird with mirrored text, we can set `backface-visibility: hidden` so it disappears between 90 and 270 degrees. But then the product would disappear for half of the scroll. That might actually be a nice effect if combined with another element or if the background has something. Alternatively, set `backface-visibility: hidden` and then duplicate the SVG with the backface? Too complex.

Let me keep it simple: rotateY(progress * 360). Since the SVG has a background glow and round lenses, when rotated beyond 90 deg, it's mirrored. But because it's a symmetric-ish design, it might still look okay. Actually the "halo ring" and camera dot break symmetry, so after 180 deg, they'll be mirrored (camera on left). Hmm. Maybe rotate only from 0 to 180 degrees? That would be a half turn, product ends at mirrored. Not ideal.

Alternative: rotate on Z? 2D spin. That always looks symmetrical-ish. But Apple-style product rotations are usually in 3D. Let me do rotateZ? Hmm.

I can do `progress * 360` with `rotateY` and also `scale` to keep it interesting, but also add a "back-face" layer. Or, instead of rotating in 3D, I can use a 2D transformation like `translate`/`scale`/`rotate` to create an interesting effect: the glasses move from left to right, scale down, and rotate slightly. The requirement says "rotates or transforms". So I can combine both: rotateZ 0 to 360 would look like the glasses spinning in a plane. That's always visible and doesn't have the backface issue. Let's do rotateZ for the sticky product. So as you scroll, it rotates continuously and scales/fades. That is a satisfying effect.

Let me use `rotateZ` (2D rotate) and scale. Because the SVG is flat, rotating 360 degrees in 2D means it always faces forward. That's cleaner.

JS:

```javascript
const rotate = progress * 360;
const scale = 0.7 + progress * 0.3;
stickyProduct.style.transform = `rotate(${rotate}deg) scale(${scale})`;
```

But if the product is a circle in rotation? No, the element rotates entirely; because it's a rectangular image with transparent background, rotating it 45 degrees will tilt everything. A 360 rotation makes it fully spin. This is a classic effect. Let's do that.

However, we lose the "3D" wow factor. But it's safe.

Alternatively, use `rotateY(progress * 180)` and update the camera/halo dot to remain on top? No.

I'll use rotateZ. Good.

Also, for the sticky overlay text, I can have the label change based on progress. I'll add a span with id `sticky-label` and update its textContent based on progress. Like:

```javascript
const stickyLabel = document.querySelector('.sticky-label');
if (progress < 0.25) stickyLabel.textContent = 'Meet Halo';
else if (progress < 0.5) stickyLabel.textContent = 'Listen';
else if (progress < 0.75) stickyLabel.textContent = 'Translate';
else stickyLabel.textContent = 'The future speaks your language';
```

That adds a nice scroll-driven storytelling element. I'll do that.

Also, the sticky title can fade out as the product rotates? I can set opacity = 1 - progress*2? Let's keep title visible.

Let me fine-tune the sticky structure:

```html
<section class="sticky-section">
  <div class="sticky-inner">
    <span class="sticky-label" id="sticky-label">Meet Halo</span>
    <h2 class="sticky-title">Translates the world around you</h2>
    <svg class="sticky-product" viewBox="0 0 600 400"><use href="#glasses"/></svg>
  </div>
</section>
```

In the JS, update the label based on progress.

Now, let me also add a small parallax to hero product? Not needed.

Let me write the complete code now. I need to be very careful to match all opening/closing tags and ensure no syntax errors.

Given the file is long, I'll structure it well.

Also, note that `<use>` needs to reference `#glasses` which is in a hidden SVG. I'll put the hidden SVG at the top of body.

Let me write the icons for features. I'll create simple SVGs inline in HTML for each card.

For the bolt (fast), globe (languages), battery, feather (weight), shield (privacy), sound (audio). I'll use minimal stroke icons.

Feature card icons:

1. Translation/latency: bolt
2. Languages: globe
3. Battery: battery
4. Weight: feather? hard; use "feather" if we have path. Maybe a "sparkle" (star) instead. I'll use a simple weight icon: circle with two lines.
5. Privacy: shield.
6. Sound: speaker.

Let me define paths:

- Globe: `<circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15 15 0 0 1 0 20a15 15 0 0 1 0-20z"/>` (Actually, the standard globe icon uses ellipse for horizontal line and path for vertical). I'll use a known simple set from Feather icons (open source) — these are easy:
  - Globe: `<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15 15 0 0 1 0 20a15 15 0 0 1 0-20z"/>`
  - Zap: `<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>`
  - Battery: `<rect x="1" y="6" width="18" height="12" rx="2"/><line x1="23" y1="10" x2="23" y2="14"/>`
  - Shield: `<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>`
  - Feather: `<path d="M20.24 12.24a6 6 0 0 0-8.49-8.49L5 10.5V19h8.5z"/><line x1="16" y1="8" x2="2" y2="22"/><line x1="17.5" y1="15" x2="9" y2="15"/>`
  - Volume/Audio: `<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/>`

I'll use these with `fill="none" stroke="white" stroke-width="2"`.

Now, let me write the final code.

I'll make the stats section have 4 counters:
- 0.3s (decimal: 1)
- 30+ (target 30, suffix +)
- 24h (target 24, suffix h)
- 65g (target 65, suffix g)

For the `30+`, I'll wrap the plus in a span outside the counter.

The stat HTML:

```html
<div class="stat">
  <div class="stat-number">
    <span class="counter" data-target="0.3" data-decimals="1">0</span>s
  </div>
  <div class="stat-label">Latency</div>
</div>
<div class="stat">
  <div class="stat-number"><span class="counter" data-target="30">0</span>+</div>
  <div class="stat-label">Languages</div>
</div>
...
```

In the JS counter, `el.textContent = (target * eased).toFixed(decimals);` will set e.g. "0.0" then eventually "0.3". Good.

Now the comparison table. I'll use CSS grid rows.

Let me code the compare section:

```html
<div class="compare-grid">
  <div class="compare-card reveal">
    <h3>Halo</h3>
    <div class="compare-price">$499<span> / pair</span></div>
    <ul class="compare-features">
      <li><span class="check">✓</span> 30 languages</li>
      <li><span class="check">✓</span> 0.3s translation latency</li>
      <li class="muted">✗ No on-lens display</li>
      <li class="muted">✗ No 4G LTE</li>
      <li class="muted">✗ No cinema camera</li>
    </ul>
    <a href="#" class="btn btn-dark compare-btn">Order</a>
  </div>
  <div class="compare-card pro reveal">
    <div class="badge">Most advanced</div>
    <h3>Halo Pro</h3>
    <div class="compare-price">$799<span> / pair</span></div>
    <ul class="compare-features">
      <li><span class="check">✓</span> 50+ languages</li>
      <li><span class="check">✓</span> 0.1s translation latency</li>
      <li><span class="check">✓</span> On-lens display</li>
      <li><span class="check">✓</span> 4G LTE</li>
      <li><span class="check">✓</span> 3D spatial camera</li>
    </ul>
    <a href="#" style="background:#00d9ff; border-color:#00d9ff; color:#0a0a0f;" class="btn compare-btn">Order Pro</a>
  </div>
</div>
```

For the features list, I'll use `border-bottom` for separation.

Now, writing everything. Let me also add `scroll-margin-top` to sections if using anchors. Not necessary.

Let me now ensure that the SVG hidden at top will not occupy space: `width:0;height:0;position:absolute;`.

I also need to include `xmlns` attributes for the hidden SVG? Since it's inline, not strictly necessary, but I'll include it.

Let me write the final document now. I'll be careful with quotes and special characters.

I'll include the CSS in the head.

This is a long file, I'll produce it now.