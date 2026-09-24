The user wants me to create a complete self-contained HTML file for a premium product landing page for "Halo" smart glasses. Let me break down the requirements:

1. **Style**: Apple-like premium product landing page
2. **Product**: "Halo" - smart glasses that translate conversations in real time
3. **Hero**: Full-screen with large headline + product illustration (inline SVG/CSS, no images)
4. **Scroll-driven animations**: Fade, slide, scale in using IntersectionObserver or scroll events
5. **Sticky section**: Product rotates/transforms as you scroll
6. **Features grid**: Grid layout with features
7. **Big animated numbers**: Battery life, languages, weight
8. **Comparison**: Two models comparison
9. **Pre-order CTA**: Call to action
10. **Typography**: System fonts, generous white space, smooth transitions
11. **Dark and light sections**
12. **Everything inline**: No external resources

Let me design this carefully:

- **Hero**: Dark background, large headline "Meet Halo" with an SVG of glasses
- **Sticky section**: A section where the glasses SVG rotates/scales based on scroll position
- **Features grid**: Light section with cards
- **Animated numbers**: Dark section with counters animating when scrolled into view
- **Comparison**: Two models (Halo Pro and Halo Air, or similar)
- **CTA**: Pre-order button

Let me craft the SVG for the glasses. It needs to look like smart glasses. I'll draw a sleek pair of glasses with a modern design.

For scroll animations, I'll use IntersectionObserver to add classes that trigger transitions. For the sticky section, I'll use scroll event listeners to apply transforms based on scroll position.

Let me design the SVG glasses:
- Two rounded rectangular glasses frames
- A bridge connecting them
- Temple arms
- Maybe some glowing elements to show they're "smart"
- Sleek, thin design

Let me structure the page:

```
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Halo</title>
<style>
/* CSS here */
</style>
</head>
<body>
<nav>...</nav>
<section class="hero">...</section>
<section class="sticky-product">...</section>
<section class="features">...</section>
<section class="stats">...</section>
<section class="comparison">...</section>
<section class="cta">...</section>
<footer>...</footer>
<script>
// JavaScript here
</script>
</body>
</html>
```

Let me think about the typography. System fonts: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif`.

Colors:
- Dark sections: #0a0a0c or #1d1d1f (Apple's dark)
- Light sections: #f5f5f7 (Apple's light gray) or white
- Accent: #0071e3 (Apple blue) or maybe a more futuristic accent like #2997ff

Let me go with:
- Dark background: #0a0a0c
- Light background: #f5f5f7
- Text dark: #1d1d1f
- Text light: #f5f5f7
- Accent blue: #0071e3

Actually, let me use Apple's exact palette:
- #000000 for dark
- #f5f5f7 for light bg
- #1d1d1f for text
- #0071e3 for blue

Now the SVG glasses. Let me design something that looks premium:

A front-facing view of smart glasses:
- Two lenses (possibly with a slight tint/reflection)
- Connected by a bridge
- Thin temple arms extending outward
- Maybe a glowing dot on the side (indicating it's powered on/translating)

Let me draw this carefully:

```svg
<svg viewBox="0 0 600 300" xmlns="http://www.w3.org/2000/svg">
  <!-- Left lens frame -->
  <!-- Right lens frame -->
  <!-- Bridge -->
  <!-- Temple arms -->
</svg>
```

Actually, let me think of a more isometric or angled view for more visual interest. But front-facing is simpler and can look very clean.

Let me design the glasses with:
- Rounded rectangle frames
- A bridge
- Temple arms extending outward at slight angles
- Gradient lens with reflection
- A small glowing LED indicator

Let me code the SVG:

```svg
<svg viewBox="0 0 800 400">
  <defs>
    <linearGradient id="lensGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1e3a5f"/>
      <stop offset="100%" stop-color="#0c1445"/>
    </linearGradient>
    <linearGradient id="frameGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#2d2d2f"/>
      <stop offset="100%" stop-color="#1d1d1f"/>
    </linearGradient>
  </defs>
  
  <!-- Left temple arm -->
  <path d="M 80,180 Q 40,180 20,165" stroke="url(#frameGrad)" stroke-width="8" fill="none" stroke-linecap="round"/>
  
  <!-- Right temple arm -->
  <path d="M 720,180 Q 760,180 780,165" stroke="url(#frameGrad)" stroke-width="8" fill="none" stroke-linecap="round"/>
  
  <!-- Left frame -->
  <rect x="130" y="140" width="220" height="120" rx="20" fill="none" stroke="url(#frameGrad)" stroke-width="6"/>
  <!-- Left lens -->
  <rect x="140" y="150" width="200" height="100" rx="14" fill="url(#lensGrad)"/>
  
  <!-- Right frame -->
  <rect x="450" y="140" width="220" height="120" rx="20" fill="none" stroke="url(#frameGrad)" stroke-width="6"/>
  <!-- Right lens -->
  <rect x="460" y="150" width="200" height="100" rx="14" fill="url(#lensGrad)"/>
  
  <!-- Bridge -->
  <path d="M 350,190 Q 400,170 450,190" stroke="url(#frameGrad)" stroke-width="6" fill="none" stroke-linecap="round"/>
  
  <!-- Reflection highlights on lenses -->
  <path d="M 160,160 Q 180,155 190,180 Q 185,200 170,210" stroke="rgba(255,255,255,0.3)" stroke-width="3" fill="none"/>
  
  <!-- LED indicators -->
  <circle cx="370" cy="210" r="4" fill="#00ff88">
    <animate attributeName="opacity" values="1;0.5;1" dur="2s" repeatCount="indefinite"/>
  </circle>
  <circle cx="430" cy="210" r="4" fill="#00ff88">
    <animate attributeName="opacity" values="1;0.5;1" dur="2s" repeatCount="indefinite"/>
  </circle>
</svg>
```

Hmm, that's a rough start. Let me refine it. I want the glasses to look genuinely premium.

Actually, let me design this more carefully. A top-down or 3/4 perspective might look more dynamic for the sticky scroll rotation. But a flat front view transformed via CSS transforms (rotateY, rotateX, scale) would work well for the sticky section.

Let me think about the sticky section implementation:

```html
<section class="sticky-wrap">
  <div class="sticky-inner">
    <div class="sticky-product" id="stickyProduct">
      <!-- SVG glasses that rotate as you scroll -->
    </div>
  </div>
</section>
```

CSS:
```css
.sticky-inner {
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
```

JavaScript:
```js
const product = document.getElementById('stickyProduct');
window.addEventListener('scroll', () => {
  const rect = stickySection.getBoundingClientRect();
  const progress = Math.min(Math.max((-rect.top) / (rect.height - window.innerHeight), 0), 1);
  product.style.transform = `rotateY(${progress * 180}deg) scale(${1 + progress * 0.2})`;
});
```

Let me now design each section fully.

**Nav**: Simple, fixed at top, semi-transparent, blur backdrop. Logo "Halo" centered, links on right.

**Hero**: Full height, centered. Large headline with gradient or just white text. Subheadline. CTA buttons. The glasses SVG below or behind.

Actually, for the hero, I want the glasses to be the focal point. Let me have:
- Background: gradient dark
- Headline: "Be understood. Anywhere."
- Sub: "Halo smart glasses translate real-time conversations in 19 languages. Naturally. Instantly."
- CTA: "Pre-order now" + "Learn more"
- Below: the glasses SVG with a glow effect

**Sticky section**: A long section (200vh) where the glasses rotate as you scroll. The heading could change or fade too.

**Features grid**: Light background, 6 features in a grid.
- Real-time translation
- Meet and speak - auto-assistant pairing
- Discreet design, all-day wear
- Live captions with AR
- 19 languages + offline
- Powered by on-device AI

**Stats section**: Dark background, big numbers that count when in view.
- 24 h battery
- 19 languages
- 48 g weight

Wait, 24 hours battery, 19 languages, 48 grams. Let me add one more: 10M+ translations or 5G connectivity. Let me stick with 3 as requested.

**Comparison**: Two models: Halo and Halo Pro. With a light background.
- Halo: $1999, 12h battery, 8GB RAM, 40Hz display
- Halo Pro: $2999, 24h battery, 16GB RAM, 120Hz display

Or more feature-like comparison: design, display, audio, battery, AI features.

**CTA**: Dark, big "The world speaks your language" with pre-order button.

Let me write the complete code now.

For the scroll-driven animations, I'll use IntersectionObserver. Elements get `.visible` class when they enter viewport, triggering transitions.

Let me code this step by step.

First, let me think about the SVG more carefully.

I want the glasses to look like:
- Sleek, thin-rimmed glasses (or maybe semi-rimless)
- Actually, smart glasses often have thicker temples to house electronics
- Let me draw them from a slight 3/4 perspective or flat front

Let me redo the glasses SVG with more detail:

```svg
<svg viewBox="0 0 900 400" width="800" height="356">
  <defs>
    <linearGradient id="lensGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#4a6b8f" stop-opacity="0.9"/>
      <stop offset="100%" stop-color="#1a3a5c" stop-opacity="0.95"/>
    </linearGradient>
    <linearGradient id="tempeGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#3a3a3c"/>
      <stop offset="100%" stop-color="#1c1c1e"/>
    </linearGradient>
    <linearGradient id="frameGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#2c2c2e"/>
      <stop offset="100%" stop-color="#1a1a1c"/>
    </linearGradient>
    <radialGradient id="glowGrad" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#0071e3" stop-opacity="0.3"/>
      <stop offset="100%" stop-color="#0071e3" stop-opacity="0"/>
    </radialGradient>
  </defs>
  
  <!-- Glow behind glasses -->
  <ellipse cx="450" cy="200" rx="350" ry="150" fill="url(#glowGrad)"/>
  
  <!-- Temple arms -->
  <path d="M 250,200 L 120,180" stroke="url(#tempeGrad)" stroke-width="10" stroke-linecap="round"/>
  <path d="M 650,200 L 780,180" stroke="url(#tempeGrad)" stroke-width="10" stroke-linecap="round"/>
  
  <!-- Left lens frame - actually, let me draw each frame -->
  <!-- I'll do a rounded rect for each frame, connected with a bridge -->
  
  <!-- Left frame -->
  <rect x="160" y="150" width="250" height="150" rx="30" fill="none" stroke="url(#frameGrad)" stroke-width="8"/>
  <!-- Left lens -->
  <rect x="175" y="165" width="220" height="120" rx="16" fill="url(#lensGrad)"/>
  
  <!-- Right frame -->
  <rect x="490" y="150" width="250" height="150" rx="30" fill="none" stroke="url(#frameGrad)" stroke-width="8"/>
  <!-- Right lens -->
  <rect x="505" y="165" width="220" height="120" rx="16" fill="url(#lensGrad)"/>
  
  <!-- Bridge -->
  <path d="M 410,180 Q 450,160 490,180" stroke="url(#frameGrad)" stroke-width="8" fill="none" stroke-linecap="round"/>
  
  <!-- Reflection on left lens -->
  <path d="M 200,180 Q 220,170 230,200 Q 215,230 195,235" stroke="rgba(255,255,255,0.25)" stroke-width="4" fill="none" stroke-linecap="round"/>
  
  <!-- Reflection on right lens -->
  <path d="M 530,180 Q 550,170 560,200 Q 545,230 525,235" stroke="rgba(255,255,255,0.2)" stroke-width="3" fill="none" stroke-linecap="round"/>
  
  <!-- LED on left temple -->
  <circle cx="260" cy="195" r="5" fill="#00ff88">
    <animate attributeName="opacity" values="1;0.4;1" dur="2s" repeatCount="indefinite"/>
  </circle>
</svg>
```

Hmm, this is getting complex. Let me think about the proportions. The glasses should span the width nicely. Let me adjust coordinates.

Actually, for the hero, I want the glasses to be prominent but not too complicated. A clean front-facing design with a slight glow underneath would work well.

Let me simplify and use a more elegant approach. I'll draw the glasses with simpler shapes but better proportions. I'll aim for a wide, sleek look.

Actually, let me reconsider. The design should be comparable to Apple's product pages which often show products at an angle or on a dark background with perspective. Since I'm limited to SVG, I should make the SVG look premium.

Here's my plan for the SVG:
- Sweet spot: 900x400 viewBox
- Dark gradient background (or transparent, since section bg will be dark)
- Glasses frame: thick at the top, thinner at the bottom (or full thickness)
- Let me just draw a clean, slightly stylized pair of glasses

Let me write the actual SVG for a clean glasses design:

```svg
<svg class="glasses-svg" viewBox="0 0 900 400" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="lensL" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#3d7dad"/>
      <stop offset="100%" stop-color="#1a2a4a"/>
    </linearGradient>
    <linearGradient id="lensR" x1="1" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#2a5a8a"/>
      <stop offset="100%" stop-color="#0f1f3f"/>
    </linearGradient>
    <linearGradient id="armL" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#3a3a3c"/>
      <stop offset="100%" stop-color="#1d1d1f"/>
    </linearGradient>
  </defs>
  
  <!-- Arms -->
  <path d="M 240,195 L 80,175" stroke="url(#armL)" stroke-width="9" stroke-linecap="round"/>
  <path d="M 660,195 L 820,175" stroke="url(#armL)" stroke-width="9" stroke-linecap="round"/>
  
  <!-- Frame - left -->
  <rect x="160" y="130" width="260" height="140" rx="35" stroke="#333" stroke-width="7" fill="none"/>
  <!-- Lens - left -->
  <rect x="175" y="145" width="230" height="110" rx="22" fill="url(#lensL)"/>
  
  <!-- Frame - right -->
  <rect x="480" y="130" width="260" height="140" rx="35" stroke="#333" stroke-width="7" fill="none"/>
  <!-- Lens - right -->
  <rect x="495" y="145" width="230" height="110" rx="22" fill="url(#lensR)"/>
  
  <!-- Bridge -->
  <path d="M 420,170 Q 450,150 480,170" stroke="#444" stroke-width="7" fill="none" stroke-linecap="round"/>
  
  <!-- Glasses reflections -->
  <path d="M 200,160 Q 220,150 240,180 Q 220,210 190,215" stroke="rgba(255,255,255,0.3)" stroke-width="5" fill="none" stroke-linecap="round"/>
  <path d="M 520,160 Q 540,150 560,180 Q 540,210 510,215" stroke="rgba(255,255,255,0.2)" stroke-width="4" fill="none" stroke-linecap="round"/>
  
  <!-- LED indicators on arms -->
  <circle cx="220" cy="190" r="4" fill="#40ff80"/>
  <circle cx="680" cy="190" r="4" fill="#40ff80"/>
</svg>
```

Wait, for the sticky rotate section, I want to rotate this SVG. Let me make sure it can rotate in 3D nicely. A flat front view rotating on Y axis... it would just get thinner and then mirror-image. That could work actually. Like a fancy 3D flip.

But a better approach for the sticky section might be to have the glasses start tilted (rotateX slightly) and then flatten as you scroll, or rotate around Y for a 3D effect.

Let me think of a nicer scroll effect: as you scroll, the glasses rotate around the Y axis (like a turn), with a fade in/out. Or scale + rotate combined.

Alternatively, the glasses could start fully rotated (looking like a thin line) and settle into straight-on view as you scroll. That's a nice effect.

Let me plan the sticky section:

```
.sticky-container {
  height: 200vh;
  position: relative;
}

.sticky-inner {
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
}
```

As you scroll through 200vh:
- The glasses rotate from -90deg to 0deg (or 180 to 0) on Y axis
- Some text appears/fades

Actually, Apple-style pages often have a sticky section where the product stays centered and elements fade in/out around it. Let me do:
- Sticky container is 300vh
- The glasses are always visible, scaling from 0.5 to 1 and then back to 0.8
- Text changes as you scroll

Let me think of a simpler but still impressive approach:
- Sticky section: the glasses rotate from 30deg to -30deg (rotateX) as you scroll
- They scale from 0.8 to 1
- It's subtle and premium

Or even simpler: the glasses have a continuous slow rotation combined with a tilt that responds to scroll.

You know what, let me keep it elegant: as you scroll through the sticky section, the glasses rotate on the Y axis from -20 degrees to 20 degrees, while scaling from 0.8 to 1.1 and the backdrop changes color slightly. This gives a premium 3D feel without being gimmicky.

Actually, for a more dramatic effect: let me have the glasses at 0 degrees rotateY at start, and as you scroll to the end, they rotate to 180 degrees, showing the back. That would require a mirrored SVG or a two-sided element. Too complex.

Let me do: rotateX from 20 degrees to -20 degrees with scale 0.9 to 1. And rotateY from -30 to 30. This gives a nice dynamic tilt response to scrolling.

Let me implement this with scroll progress from 0 to 1:

```js
const progress = clamp((currentScroll - stickyStart) / (stickyEnd - stickyStart), 0, 1);
const rotateY = -30 + (progress * 60); // -30 to 30
const rotateX = 15 - (progress * 30); // 15 to -15
const scale = 0.8 + (progress * 0.3); // 0.8 to 1.1
product.style.transform = `perspective(800px) rotateY(${rotateY}deg) rotateX(${rotateX}deg) scale(${scale})`;
```

That could look nice.

Now let me think about the full page structure and content.

**Copy**:

Hero:
- "Halo" (wordmark)
- Headline: "Translate every conversation. In real time."
- Sub: "Halo smart glasses translate conversations in 19 languages as they happen. All in a pair of glasses that feel just like your everyday frames."
- CTA: "Get early access" / "Watch the film"

Sticky section:
- Background: dark
- The glasses in the center
- Overlay text: "1. See the words." / "2. Hear the sound." / "3. Understand everything."

Features:
- "Designed to disappear." / "Engineered to translate."
- Feature cards:
  1. "Translate in real time" - "Conversations translate instantly, right in your ear or in an invisible heads-up display."
  2. "19 languages" - "From English to Japanese. Offline or online, Halo speaks your language."
  3. "All-day wear" - "At just 48 grams, Halo feels like nothing. But powers through your longest conversations."
  4. "On-device AI" - "Your conversations stay private. All translation happens on the chip built into your glasses."
  5. "One tap. Full duplex." - "Automatic speech recognition knows when people are speaking. No buttons to press."
  6. "Designed with the planet in mind" - "Recycled aluminum and bio-based acetate. Because good design shouldn't cost the earth."

Stats:
- "24h" battery life
- "19" languages
- "48g" ultra light

Comparison:
- Halo vs Halo Pro
  - Titanium finish vs Aluminum
  - 30min charge (80%) vs 20min charge (80%)
  - 12h vs 24h battery
  - 8GB vs 16GB storage
  - 5G vs WiFi only

CTA:
- "The world speaks your language."
- "Pre-order Halo today"
- "From $1,999/mo or $1,999 one-time"
- Wait, that should be $16.67/mo or $1,999. But I just need simple text.

Footer:
- Apple-style footer with fine print.

Now let me actually write the complete HTML. This will be a large file. Let me plan the CSS systematically.

**Colors**:
- --dark: #0a0a0c
- --dark-2: #1d1d1f
- --light: #f5f5f7
- --light-2: #ffffff
- --text-dark: #1d1d1f
- --text-light: #f5f5f7
- --text-gray: #86868b
- --blue: #0071e3
- --green: #00ff88 (for LED)

**Typography**:
- font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif
- Large headlines: font-size: clamp(3rem, 8vw, 6rem)
- Section titles: font-size: clamp(2rem, 5vw, 3.5rem)

**Spacing**: Consistent use of 80-160px for section padding.

Let me write the CSS. I'll organize it by component.

Now the JavaScript:

1. IntersectionObserver for fade-in animations
   ```js
   const observer = new IntersectionObserver((entries) => {
     entries.forEach(entry => {
       if (entry.isIntersecting) {
         entry.target.classList.add('visible');
       }
     });
   }, { threshold: 0.15 });
   ```
   Apply to `.animate-on-scroll` class.

2. Counter animation for stats
   ```js
   function animateCounter(element, target, duration = 2000) {
     let start = 0;
     const startTime = performance.now();
     function update(currentTime) {
       const elapsed = currentTime - startTime;
       const progress = Math.min(elapsed / duration, 1);
       const eased = 1 - Math.pow(1 - progress, 3);
       const current = Math.round(eased * target);
       element.textContent = current;
       if (progress < 1) requestAnimationFrame(update);
     }
     requestAnimationFrame(update);
   }
   ```

3. Sticky scroll effect
   ```js
   const stickySection = document.getElementById('stickySection');
   const stickyInner = document.getElementById('stickyInner');
   const product = document.getElementById('stickyProduct');
   
   let ticking = false;
   function updateSticky() {
     const rect = stickySection.getBoundingClientRect();
     const viewportHeight = window.innerHeight;
     const sectionHeight = rect.height;
     const start = -rect.top;
     const end = start - (sectionHeight - viewportHeight);
     const progress = Math.max(0, Math.min(1, start / (sectionHeight - viewportHeight)));
     
     const rotateY = -30 + (progress * 60);
     const rotateX = 15 - (progress * 30);
     const scale = 0.85 + (progress * 0.25);
     
     product.style.transform = `perspective(800px) rotateY(${rotateY}deg) rotateX(${rotateX}deg) scale(${scale})`;
     
     ticking = false;
   }
   
   window.addEventListener('scroll', () => {
     if (!ticking) {
       requestAnimationFrame(updateSticky);
       ticking = true;
     }
   });
   ```

4. Pre-order button click handler (smooth scroll or alert)

Let me now write the full code. This is going to be substantial.

Actually, let me reconsider the layout. For the hero, I want:
- Full-screen dark background
- Navigation bar at top
- Large headline centered
- Glasses SVG below
- Maybe a scroll indicator

For the hero, the glasses should be prominent. Let me place them below the headline, maybe with a 3D perspective.

Let me think about the hero SVG more. Instead of just a flat pair of glasses, what if I draw a pair of glasses with some surrounding interface elements - like floating text bubbles in different languages? That would sell the translation feature.

Idea: The glasses are centered. Floating around them are translation bubbles that show "Hello" in different languages: "Bonjour", "こんにちは", "Hola", etc. With small lines connecting them to the glasses. That immediately communicates the translation feature.

That's a nice touch. Let me include that in the hero.

Alternatively, the hero could just show the glasses with a subtle wave/ripple effect, and the translation bubbles could appear in a smaller section.

Let me keep the hero focused. I'll show:
- Center: The glasses SVG
- Behind or around: subtle animated elements

For the floating translations, I can use HTML/CSS positioned spans around the SVG. That's doable.

Let me write this. Actually, to keep the hero clean, maybe put a few floating text bubbles with position: absolute around the glasses.

OK let me just write the whole file now. I'll be thorough.

Let me also think about the nav menu. Apple-style:
- "Halo" logo centered (since it's a memorable wordmark)
- Links: Overview, Design, Specifications
- Button: Pre-order

Let me finalize all sections:

1. **Nav** (fixed, dark, frosted)
2. **Hero** (dark, full-screen)
   - Intro line: "Introducing Halo"
   - H1: "Every conversation. Any language."
   - Sub: "Halo is the world's first smart glasses that translate conversations in real time — right in your ear, in your language."
   - Buttons: "Get early access" / "Learn more >"
   - Glasses SVG with floating text bubbles
3. **Logo strip** (maybe: "As seen in...") - skip, not necessary
4. **Sticky product section** (dark, 250vh)
   - Products that rotate/scale as you scroll
   - Text overlays that change
5. **Features grid** (light, centered heading)
   - 6 feature cards
6. **Stats** (dark, big animated numbers)
   - 3-4 stats
7. **Comparison** (light)
   - Two models side by side
8. **CTA** (dark, big)
   - Pre-order button
9. **Footer** (dark)

Actually, let me make the sticky section part of the "design" storytelling. Maybe:

Sticky section concept: "See what it feels like."
As you scroll, the glasses rotate 360 degrees, showing off different angles. With text overlay that says "Thin. Light. Powerful."

Or simpler: The glasses stay in the center of a 200vh sticky section, and as you scroll:
1. Text above fades in: "Halo don't just translate."
2. Text below fades in: "They transform how the world feels."

I think the most Apple-like approach is:
- Sticky container of 200vh
- The glasses are always centered
- Text fades in/out as you scroll
- The glasses rotate slightly based on scroll position

Let me implement:

```html
<section class="sticky-section" id="stickySection">
  <div class="sticky-inner" id="stickyInner">
    <div class="sticky-product" id="stickyProduct">
      <!-- SVG glasses -->
    </div>
    <div class="sticky-text sticky-text--top">
      <!-- Text overlay -->
    </div>
  </div>
</section>
```

CSS:
```css
.sticky-section {
  height: 250vh;
  background: #0a0a0c;
  position: relative;
}
.sticky-inner {
  position: sticky;
  top: 0;
  height: 100vh;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}
```

For text overlays that fade based on scroll progress, I can use multiple p elements with opacity tied to scroll progress. But that's complex. Let me keep it simple: just the glasses with a small caption that fades.

Actually, for the sticky section, let me use a different approach: The glasses are sticky, and behind them, blocks of text scroll through. As each block passes behind the glasses, it's like the glasses are the focal point. This is a common Apple effect.

Let me do:
- Sticky container, 300vh
- 3 "content blocks" of text, each 100vh tall
- The glasses (sticky, centered) are always visible
- Each block scrolls up through the sticky viewport

But this requires z-index layering. Actually no - the standard approach is:

```html
<section class="sticky-parent">
  <div class="sticky">
    <div class="glasses">...</div>
  </div>
  <div class="text-block-1">...</div>
  <div class="text-block-2">...</div>
  <div class="text-block-3">...</div>
</section>
```

But then the sticky div has to be position: sticky and the text blocks scroll over it. The glasses need to be behind or above the text blocks. This can work with z-index.

Hmm, this is getting complex. Let me simplify.

Actually, the simplest and most effective approach: Use a sticky container where the glasses rotate as you scroll. No text overlay changes needed - just the visual rotation. It's clean and premium.

```html
<section class="sticky-demo" id="sticky">
  <div class="sticky-demo-inner">
    <div class="product-3d" id="stickyProduct">
      <!-- SVG glasses -->
    </div>
  </div>
  <div class="sticky-copy" id="stickyCopy">
    <h2>Designed around you.</h2>
    <p>Every curve. Every material. Every detail, considered.</p>
  </div>
</section>
```

Where `.sticky-demo` is 200vh, `.sticky-demo-inner` is sticky at 100vh. The copy scrolls naturally and the glasses rotate.

Actually wait, for the copy to appear, I need it to either be in the sticky area or scroll over it. Let me put the copy in the normal flow and the sticky product is behind/below it.

You know what, let me use a cleaner pattern:

Section 1: Sticky glasses with scroll-driven rotation
- Container is 200vh
- Products rotate as you scroll
- Overlay text on the glasses: "A different kind of beautiful."

Let me just do this:

```html
<section class="sticky-section" id="stickySection">
  <div class="sticky-viewport">
    <div class="sticky-product" id="stickyProduct">
      <svg class="glasses-svg">...</svg>
    </div>
    <div class="sticky-caption">
      <p id="stickyCaption">Every angle, considered.</p>
    </div>
  </div>
</section>
```

CSS: `.sticky-section { height: 250vh; } .sticky-viewport { position: sticky; top: 0; height: 100vh; }`

The scroll handler updates the transform based on the section's scroll progress. The caption text changes at specific progress intervals.

That's manageable. Let me go with this.

Now let me write the complete code. I'll try to make it really polished.

Actually, let me reconsider: I'll use `position: sticky; top: 0;` on `.sticky-viewport`, and the parent `.sticky-section` has `height: 250vh`. This makes the viewport stick for 150vh of scrolling.

```css
.sticky-section {
  height: 250vh;
  background: #0a0a0c;
  position: relative;
}

.sticky-viewport {
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  overflow: hidden;
}
```

Now the JS scroll handler:

```js
function updateSticky() {
  const section = document.getElementById('stickySection');
  const rect = section.getBoundingClientRect();
  const viewportHeight = window.innerHeight;
  const sectionHeight = rect.height;
  
  // Progress from 0 to 1
  const progress = Math.max(0, Math.min(1, (-rect.top) / (sectionHeight - viewportHeight)));
  
  const product = document.getElementById('stickyProduct');
  if (product) {
    const rotateY = -20 + (progress * 40);
    const rotateX = 10 + (progress * -20);
    const scale = 0.9 + (progress * 0.2);
    product.style.transform = `perspective(800px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(${scale})`;
    
    const caption = document.getElementById('stickyCaption');
    if (caption) {
      if (progress < 0.33) {
        caption.textContent = 'Every angle, considered.';
      } else if (progress < 0.66) {
        caption.textContent = 'Invisible technology.';
      } else {
        caption.textContent = 'Crafted for your world.';
      }
    }
  }
}
```

OK, now let me code the full HTML file. I'll aim for a massive, well-designed page. Let me write it out.

Actually, thinking about it more, let me think about the hero SVG more carefully. I'll design a beautiful pair of glasses with gradients and effects. Let me be very precise with the coordinates.

The glasses in hero:
- ViewBox: 0 0 900 420
- Center point: 450, 210
- Left lens frame: x=180, y=140, width=230, height=130, rx=28
- Right lens frame: x=490, y=140, width=230, height=130, rx=28
- Bridge: connects the two, curving across the center
- Temple arms: extend from the outer edges outward/backward

Let me draw:

Left lens:
- Outer roughly at: x=180, y=140 to x=410, y=270 (230 wide, 130 tall)
- Left temple arm connects at around x=180, y=170

Temple arms should go outward and slightly back. For a front view:
- Left arm: from (185, 180) curving to (60, 160)
- Right arm: from (715, 180) curving to (840, 160)

Bridge:
- From an inner point on the left lens frame to inner point on the right lens frame
- Left lens inner edge is at x=410
- Right lens inner edge is at x=490
- They should meet around x=450

The bridge could be a curved path from (400, 180) to (500, 180) with a slight dip.

Reflections on the lenses: a subtle white curved stroke.

LED indicator: small circle on the temple arm.

Let me also add a subtle glow in the center below the bridge - like a tiny camera lens or sensor.

OK, here's my refined SVG:

```svg
<svg class="hero-glasses" viewBox="0 0 900 420" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="lensGrad1" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#4a7aa3"/>
      <stop offset="100%" stop-color="#152a45"/>
    </linearGradient>
    <linearGradient id="lensGrad2" x1="1" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#3a6a93"/>
      <stop offset="100%" stop-color="#122540"/>
    </linearGradient>
    <linearGradient id="armGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#2a2a2c"/>
      <stop offset="100%" stop-color="#1d1d1f"/>
    </linearGradient>
    <linearGradient id="frameGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#3a3a3c"/>
      <stop offset="100%" stop-color="#1d1d1f"/>
    </linearGradient>
    <linearGradient id="bridgeGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#3a3a3c"/>
      <stop offset="100%" stop-color="#222"/>
    </linearGradient>
  </defs>
  
  <!-- Temple arms -->
  <path d="M 220,190 C 150,190 90,175 50,160" stroke="url(#armGrad)" stroke-width="10" stroke-linecap="round"/>
  <path d="M 680,190 C 750,190 810,175 850,160" stroke="url(#armGrad)" stroke-width="10" stroke-linecap="round"/>
  
  <!-- Left frame -->
  <rect x="160" y="130" width="250" height="145" rx="32" stroke="url(#frameGrad)" stroke-width="8" fill="none"/>
  <!-- Left lens -->
  <rect x="175" y="145" width="220" height="115" rx="20" fill="url(#lensGrad1)"/>
  
  <!-- Right frame -->
  <rect x="490" y="130" width="250" height="145" rx="32" stroke="url(#frameGrad)" stroke-width="8" fill="none"/>
  <!-- Right lens -->
  <rect x="505" y="145" width="220" height="115" rx="20" fill="url(#lensGrad2)"/>
  
  <!-- Bridge -->
  <path d="M 410,195 C 420,175 480,175 490,195" stroke="url(#bridgeGrad)" stroke-width="8" fill="none" stroke-linecap="round"/>
  
  <!-- Nose pads -->
  <ellipse cx="420" cy="200" rx="10" ry="15" fill="#333" stroke="#444" stroke-width="2"/>
  <ellipse cx="480" cy="200" rx="10" ry="15" fill="#333" stroke="#444" stroke-width="2"/>
  
  <!-- Left reflection -->
  <ellipse cx="280" cy="175" rx="45" ry="25" fill="rgba(255,255,255,0.12)" transform="rotate(-25, 280, 175)"/>
  <path d="M 210,165 Q 230,155 250,185" stroke="rgba(255,255,255,0.2)" stroke-width="3" stroke-linecap="round" fill="none"/>
  
  <!-- Right reflection -->
  <path d="M 540,165 Q 560,155 580,185" stroke="rgba(255,255,255,0.15)" stroke-width="3" stroke-linecap="round" fill="none"/>
  
  <!-- Center sensor (camera/RGB dot) -->
  <circle cx="450" cy="240" r="5" fill="#1a1a1c" stroke="#333" stroke-width="2"/>
  
  <!-- LED on left temple -->
  <circle cx="235" cy="185" r="4" fill="#40ff80">
    <animate attributeName="opacity" values="1;0.3;1" dur="2s" repeatCount="indefinite"/>
  </circle>
  
  <!-- Additional LED on right temple -->
  <circle cx="665" cy="185" r="4" fill="#40ff80">
    <animate attributeName="opacity" values="1;0.3;1" dur="2s" repeatCount="indefinite" begin="0.5s"/>
  </circle>
</svg>
```

Hmm, this is getting verbose but OK.

Let me optimize the lens shape. Instead of a simple rect with rx, I should use a more organic shape. But a rect is fine for a clean design.

Actually, for a more realistic look, the lens should be slightly larger and have more curvature. Let me use path for the lens:

Too complex. Let me stick with rects with rounded corners. They look fine for a flat design approach.

Now, for the floating translation bubbles in the hero, I'll use HTML/CSS absolutely positioned elements around the SVG. Something like:

```html
<div class="hero-visual">
  <svg class="hero-glasses">...</svg>
  <span class="bubble bubble-1">Bonjour 👋</span>
  <span class="bubble bubble-2">こんにちは</span>
  <span class="bubble bubble-3">Hola</span>
  <span class="bubble bubble-4">Hello</span>
  <span class="bubble bubble-5">Ciao</span>
</div>
```

With animations for floating up and down.

OK, I think I have enough planned. Let me write the complete file now. I'll be careful to include everything.

Let me plan the sections and their classes:

```
<body>
  <nav class="nav">
    <a href="#" class="nav-logo">◉ Halo</a>
    <div class="nav-links">
      <a href="#">Overview</a>
      <a href="#">Design</a>
      <a href="#">Tech Specs</a>
      <a href="#" class="nav-btn">Pre-order</a>
    </div>
  </nav>

  <main>
    <!-- Hero -->
    <section class="hero">
      <p class="hero-eyebrow">Introducing Halo</p>
      <h1 class="hero-title">Every conversation.<br>Any language.</h1>
      <p class="hero-subtitle">Halo smart glasses translate conversations in real time — visible in your vision, heard in your ear.</p>
      <div class="hero-buttons">
        <a href="#" class="btn-primary">Get early access</a>
        <a href="#" class="btn-link">Watch the film ›</a>
      </div>
      <div class="hero-visual">
        <!-- SVG + bubbles -->
      </div>
    </section>

    <!-- Sticky scroll section -->
    <section class="sticky-section" id="stickySection">
      <div class="sticky-viewport">
        <div class="sticky-product" id="stickyProduct">
          <svg class="glasses-svg">...</svg>
        </div>
        <p class="sticky-caption" id="stickyCaption"></p>
      </div>
    </section>

    <!-- Features grid -->
    <section class="features light">
      <h2 class="section-title">Everything you need. Nothing you don’t.</h2>
      <p class="section-sub">Intelligent. Invisible. Indispensable.</p>
      <div class="features-grid">
        <div class="feature-card animate-on-scroll">
          <div class="feature-icon"><!-- SVG icon --></div>
          <h3>Real-time translation</h3>
          <p>Text...</p>
        </div>
        <!-- ... -->
      </div>
    </section>

    <!-- Stats -->
    <section class="stats-section dark">
      <div class="stats-container">
        <div class="stat animate-on-scroll">
          <p class="stat-number"><span class="counter" data-target="24">0</span> h</p>
          <p class="stat-label">Battery life</p>
        </div>
        <div class="stat animate-on-scroll">
          <p class="stat-number"><span class="counter" data-target="19">0</span></p>
          <p class="stat-label">Languages</p>
        </div>
        <div class="stat animate-on-scroll">
          <p class="stat-number"><span class="counter" data-target="48">0</span> g</p>
          <p class="stat-label">Weight</p>
        </div>
      </div>
    </section>

    <!-- Comparison -->
    <section class="comparison light">
      <h2 class="section-title">Choose your Halo.</h2>
      <div class="compare-grid">
        <div class="compare-card">
          <h3>Halo</h3>
          <p class="price">$1,999</p>
          <ul>
            <li>12-hour battery</li>
            <li>8GB storage</li>
            <li>10 languages</li>
            <li>Aluminium frame</li>
          </ul>
          <a href="#" class="btn-secondary">Pre-order</a>
        </div>
        <div class="compare-card featured">
          <h3>Halo Pro</h3>
          <p class="price">$2,999</p>
          <ul>
            <li>24-hour battery</li>
            <li>16GB storage</li>
            <li>19 languages</li>
            <li>Titanium frame</li>
          </ul>
          <a href="#" class="btn-primary">Pre-order Pro</a>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="cta dark">
      <h2 class="cta-title">The world speaks your language.</h2>
      <a href="#" class="btn-primary">Pre-order now</a>
      <p class="cta-note">Starting at $1,999. Free shipping. 30-day returns.</p>
    </section>
  </main>

  <footer class="footer dark">
    <!-- Footer content -->
  </footer>
</body>
```

OK, I'm going to write the actual code. Let me do this systematically.

Important considerations:
- The `position: sticky` inside `height: 250vh` section works
- IntersectionObserver needs `threshold` or `rootMargin` to trigger at the right time
- For the counters, I need to handle the "19 languages" counter properly (adding "0" for the 19 but then final should be 19)

For the stats, the suffixes:
- Battery: "24" with "h" after the span
- Languages: "19" with no suffix (or maybe a language icon)
- Weight: "48" with "g"

So the HTML:
```html
<div class="stat">
  <p class="stat-number"><span class="counter" data-target="24" data-duration="2000">0</span><span class="suffix">h</span></p>
  <p class="stat-label">Battery life</p>
</div>
```

For the counter that adds "h" and "g", I'll put the suffix outside the number span.

Let me also reconsider: I should maybe use `repeat` for the counter, or "19" is nice because it incremented from 0 feels good to land on 19. OK.

Now for the comparison section, let me include a visual comparison table-style layout. I'll make each card with a list of features and checkmarks.

Let me decide on the actual feature comparison:

Halo:
- $1,999
- 12-hour battery
- 8GB storage
- 10 languages
- Polished aluminium
- 55g

Halo Pro:
- $2,999
- 24-hour battery (with case)
- 16GB storage
- 19 languages
- Titanium frame
- 48g
- Includes charging case

Actually for Apple style, I'll do "Halo" and "Halo Pro", with subtle differences.

Now let me focus on writing the code. It's going to be long. I'll be careful with the SVG to make it look good.

Also, I should add smooth scrolling to anchor links. I'll use CSS `scroll-behavior: smooth` on the html element.

For the pre-order CTA, I'll add a simple JavaScript that shows a confirmation or scrolls to the comparison section.

Let me write now.

One more thing: the "design" language should be very Apple. That means:
- Lots of whitespace
- Short, punchy copy
- Big headers
- Simple grid layouts
- Clear visual hierarchy
- Smooth, subtle animations

Colors:
- Hero and dark sections: #000 or #0a0a0c
- Light sections: #f5f5f7
- Cards: #fff
- Text: #1d1d1f on light, #f5f5f7 on dark
- Blue accent: #0071e3
- Green LED: #30e3a1

For the "brand color" of Halo, maybe a cyan/teal to suggest translation/AI. Let me use #00c7be or #2997ff (Apple-like blue).

I'll use #2997ff as the primary accent.

OK writing now.

Actually, let me think about the overall page title: "Halo — The world speaks your language."

And in the footer: "Halo. Designed by Apple in California." - no, this is an invented product, I shouldn't say Apple. Let me say "© 2024 Halo Inc. All rights reserved."

Now, let me also handle the IntersectionObserver for the features grid. Each card gets a `visible` class.

```css
.animate-on-scroll {
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 0.6s ease, transform 0.6s ease;
}
.animate-on-scroll.visible {
  opacity: 1;
  transform: translateY(0);
}
```

I can add a delay for each card:
```css
.feature-card:nth-child(2) { transition-delay: 0.1s; }
.feature-card:nth-child(3) { transition-delay: 0.2s; }
...
```

But this only works if they all enter at the same time. Let me use stagger:
```js
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
    }
  });
}, { threshold: 0.2 });
```

The transition delay will work since it's applied before they become visible.

Let me write the complete HTML now. I'll go step by step.

Actually, a really polished piece would also include the nav having a blur background as you scroll. Apple's nav changes from transparent to blurred when scrolling. I can add that with a scroll listener:

```js
const nav = document.querySelector('.nav');
window.addEventListener('scroll', () => {
  if (window.scrollY > 50) {
    nav.classList.add('nav-blur');
  } else {
    nav.classList.remove('nav-blur');
  }
});
```

CSS:
```css
.nav {
  position: fixed;
  top: 0;
  width: 100%;
  z-index: 1000;
  transition: background 0.3s, backdrop-filter 0.3s;
}
.nav-blur {
  background: rgba(10, 10, 12, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
```

OK I think I'm ready. Let me write this out in a single, comprehensive HTML file.

I'm going to carefully craft the SVG so it looks genuinely good. Let me design the glasses with clean lines and good proportions.

Here's my final SVG plan:

```
ViewBox: 0 0 900 420

Defs:
- lensGrad1: linear, dark blue to darker
- lensGrad2: linear, dark blue reversed  
- armGrad: linear, dark gray gradient
- frameHover: filter drop shadow

Layers (back to front):
1. Temple arms (both sides)
2. Frame outlines (both lenses)
3. Lens fills
4. Bridge
5. Reflections (on lenses)
6. Sensor dots / LEDs

Temple arms:
Left: M 230,190 C 150,190 100,175 50,155
Right: M 670,190 C 750,190 800,175 850,155

Left frame: rect x=160 y=130 width=250 height=145 rx=32 stroke=#333 fill=none
Left lens: rect x=175 y=145 width=220 height=115 rx=20 fill=url(#lensGrad1)

Right frame: rect x=490 y=130 width=250 height=145 rx=32 stroke=#333 fill=none
Right lens: rect x=505 y=145 width=220 height=115 rx=20 fill=url(#lensGrad2)

Bridge: path M 410,195 C 420,170 480,170 490,195

Nose pads: two small ellipses

LEDs: small green circles on temples
```

Wait, I want to double-check: 160+250 = 410. So the left frame ends at x=410. The right starts at x=490. Gap between is 80px. The bridge should span this gap. Good.

Left lens: 175+220 = 395. So there's 15px padding from frame edge. That's fine.

Reflections:
- Use a semi-transparent white path diagonal across each lens.

Let me code this properly now.

One more thing: for the hero, I want a subtle 3D tilt on the glasses. This can be done with CSS:
```css
.hero-visual .hero-glasses {
  transform: perspective(1000px) rotateX(5deg) rotateY(-5deg);
  transition: transform 0.5s ease;
}
```

But I won't add mouse-move tilt to keep it simple. The scroll rotation in the sticky section is enough.

OK let me write. I'll use string literals in JS carefully and keep everything self-contained.

Let me also plan the exact copy for each section:

**Nav**:
- Logo: Halo
- Links: Overview, Technology, Design, Specs
- Pre-order button

**Hero**:
- Eyebrow: Introducing Halo
- Title: Every conversation. Any language.
- Subtitle: Halo smart glasses translate in real time across 19 languages. See it in a display. Hear it in your ear. Feel the world open up.
- CTA: Get early access / Watch the film

**Sticky Section**:
- The glasses rotate as you scroll
- Caption changes: "See it. Hear it. Live it."
Actually let me just have one caption and change text based on scroll.

**Features** (light):
- Title: Designed to disappear.
- Subtitle: In the moment. In the world. In your life.
- 6 features:
  1. Real-time translation — "Neural processing delivers accurate translations as the conversation flows."
  2. Invisible display — "A micro-LED display presents subtitles in your field of vision without obstruction."
  3. Studio microphones — "Six microphones with beamforming isolate voices in any environment."
  4. On-device intelligence — "Your conversations never leave your glasses. All processing is on-board."
  5. All-day comfort — "At just 48 grams, Halo is lighter than the average pair of sunglasses."
  6. Quick charging — "With 15 minutes of charging, you'll get up to 4 hours of translation."

**Stats** (dark):
- 24h battery
- 19 languages
- 48g weight

**Comparison** (light):
- Halo vs Halo Pro
- Halo features list:
  - 12h battery
  - 10 languages
  - 8GB storage
  - Aluminium frame
  - 55g
  - $1,999
- Halo Pro:
  - 24h battery
  - 19 languages
  - 16GB storage
  - Titanium frame
  - 48g
  - $2,999

**CTA** (dark):
- Title: The world speaks your language.
- Subtitle: Be among the first to experience the future of conversation.
- Button: Pre-order now
- Note: $50 refundable deposit. Free shipping. 30-minute setup.

**Footer**:
- Fine print, links.

Let me write the complete file now. This is going to be around 1200+ lines.

Because this is long, I'll be careful with syntax and make sure all tags are closed.

Here goes!

Wait, let me reconsider the counter animation. For "19", I want it to count to 19. For "24", count to 24. For "48", count to 48. These are small numbers so the animation can be quick, like 1.5 seconds. I'll use `requestAnimationFrame`.

Actually, when there are multiple counters, I should use IntersectionObserver to trigger them when they come into view.

```js
function setupCounters() {
  const counters = document.querySelectorAll('.counter');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const counter = entry.target;
        const target = parseInt(counter.dataset.target);
        const duration = parseInt(counter.dataset.duration) || 1500;
        const startTime = performance.now();
        const startValue = 0;
        const suffix = counter.parentElement.querySelector('.suffix');
        
        function updateCounter(currentTime) {
          const elapsed = currentTime - startTime;
          const progress = Math.min(elapsed / duration, 1);
          const eased = 1 - Math.pow(1 - progress, 3);
          const current = Math.round(eased * (target - startValue) + startValue);
          counter.textContent = current;
          if (progress < 1) {
            requestAnimationFrame(updateCounter);
          } else {
            counter.textContent = target;
          }
        }
        
        requestAnimationFrame(updateCounter);
        observer.unobserve(counter);
      }
    });
  }, { threshold: 0.5 });
  
  counters.forEach(counter => observer.observe(counter));
}
```

Good. Now let me write the complete file.

I need to be careful with CSS responsive design. The page should look good on mobile too. I'll use `clamp()` for font sizes, `grid` with `minmax` for cards, and media queries.

Here's my media queries plan:
- Mobile (< 768px): Single column features, stacked comparison
- Desktop: Multi-column layout

But since this is a design showcase, I'll make the desktop look great and add basic responsiveness.

Let me finalize and write the code.

One more consideration: the `animate-on-scroll` class and the IntersectionObserver. I want elements to fade in nicely. I'll add `will-change: opacity, transform` for smoothness.

OK, TOTALLY writing now. Here is my comprehensive plan for the HTML structure:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Halo — Smart Glasses for the Real World</title>
  <style>
    /* Reset */
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    
    /* CSS Variables */
    :root {
      --dark: #0a0a0c;
      --dark-2: #161618;
      --light: #f5f5f7;
      --white: #ffffff;
      --text: #1d1d1f;
      --text-secondary: #86868b;
      --blue: #0071e3;
      --blue-light: #2997ff;
      --green: #30d158;
      --font: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    }
    
    /* Base */
    html { scroll-behavior: smooth; }
    body {
      font-family: var(--font);
      color: var(--text);
      background: var(--white);
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
    }
    
    /* Navigation */
    .nav { ... }
    
    /* etc. */
  </style>
</head>
<body>
  ...
</body>
</html>
```

Let me write out all the HTML structure and then add the CSS. Actually, I'll interleave for clarity but since it's one file, I'll provide it all at once.

I realize I'm spending too long planning. Let me write the final code now in one shot.

There are a few more things I want to double check:

1. Without the `Rotating` sticky section: I want as user scrolls, the SVG product rotates. To achieve rotation on the Y axis that looks 3D, I need `transform: perspective(1000px) rotateY(angle)`. I can also use `rotate3d`. I'll use individual properties with a perspective wrap.

2. For the scroll progress calculation with sticky:
```js
function getStickyProgress(sectionEl) {
  const rect = sectionEl.getBoundingClientRect();
  const viewportHeight = window.innerHeight;
  const sectionHeight = sectionEl.offsetHeight;
  const stickyHeight = viewportHeight; // sticky viewport height
  // The section is taller than the viewport; the sticky element stays at top.
  // Progress is based on how much of the section has been scrolled past.
  // When rect.top is 0, progress is 0 (section top at viewport top)
  // When rect.bottom is viewportHeight, progress is 1
  const progress = -rect.top / (sectionHeight - viewportHeight);
  return Math.max(0, Math.min(1, progress));
}
```

Wait, `rect.top` starts at `sectionHeight - viewportHeight` when section bottom is at viewport bottom, and goes to `-viewportHeight` when section top is at viewport top. Actually let me be more careful.

When the section enters viewport: `rect.top = sectionHeight` (i.e., the section is below the viewport, but not visible yet). When section top reaches viewport top: `rect.top = 0`. When section bottom reaches viewport bottom: `rect.bottom = viewportHeight`, which means `rect.top = viewportHeight - sectionHeight` (negative since section is taller).

So:
- Scroll progress from 0 to 1 is:
  - `p = (-rect.top) / (sectionHeight - viewportHeight)`
  - When `rect.top = 0`, p = 0
  - When `rect.top = viewportHeight - sectionHeight`, p = 1

That's right. But for the sticky to be in effect, the section height should be > viewport height. With `height: 250vh`, the section height is 2.5 * viewportHeight. So:
- p = (-rect.top) / (1.5 * viewportHeight)

When section top hits viewport top: rect.top = 0, p=0. The sticky element sticks. As we scroll past, rect.top goes negative, p increases. When section bottom hits viewport bottom: rect.top = -1.5 * viewportHeight, p=1.

So the formula works.

3. For the duration of scroll-driven animations, I want the rotation to happen smoothly. The transform will be updated in rAF.

OK here we go. Writing full file.

Actually, I want to add one more thing to the sticky section: the product should also scale and the caption should fade in/out. Let me keep it simple - just rotation and caption changes.

I'll also add a progress bar at some point? No, too complex.

Let me now write the complete file. I'll be very careful. This is going to be quite long, maybe 1500 lines. Let me be efficient.

Actually, I'm going to carefully design the CSS for each section in my head first, then type it all out.

**Nav CSS**:
```css
.nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2.5rem;
  background: transparent;
  transition: all 0.4s ease;
}
.nav.scrolled {
  background: rgba(0,0,0,0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255,255,255,0.1);
  padding-top: 0.7rem;
  padding-bottom: 0.7rem;
}
.nav-logo {
  font-size: 1.4rem;
  font-weight: 600;
  color: white;
  text-decoration: none;
  letter-spacing: 0.5px;
}
.nav-logo dot { color: var(--blue-light); }
.nav-links {
  display: flex;
  gap: 2rem;
  align-items: center;
}
.nav-links a {
  color: rgba(255,255,255,0.8);
  text-decoration: none;
  font-size: 0.85rem;
  transition: color 0.3s;
}
.nav-links a:hover { color: white; }
.nav-btn {
  background: var(--blue);
  color: white !important;
  padding: 0.45rem 1.2rem;
  border-radius: 20px;
  font-weight: 500;
  transition: background 0.3s, transform 0.2s !important;
}
.nav-btn:hover {
  background: var(--blue-light);
  transform: scale(1.02);
}
```

OK let me just type it all. This is taking too long to plan.

One last thing: I'll add a `smooth-scroll` handler for the "Learn more" that scrolls to the features section. And the "Pre-order" buttons scroll to the comparison section. Actually, I'll just use anchor links with `href="#features"` etc. Since I have `scroll-behavior: smooth`, anchor links work automatically.

Let me write the HTML file completely now.