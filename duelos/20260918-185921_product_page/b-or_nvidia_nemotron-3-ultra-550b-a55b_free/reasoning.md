The user wants a premium product landing page for "Halo" smart glasses, styled like Apple's product pages. Key requirements:

1. Full-screen hero with large headline and inline SVG product illustration (no images)
2. Scroll-driven animations (fade, slide, scale) using IntersectionObserver or scroll events
3. Sticky section with product rotation/transformation on scroll
4. Features grid
5. Animated numbers section (battery life, languages, weight)
6. Comparison of two models
7. Pre-order CTA
8. Elegant typography with system fonts, generous whitespace, smooth transitions
9. Dark and light sections
10. Everything inline in ONE HTML file (no external resources)

Let me design this carefully:

**Color scheme**: Apple-like - clean whites, blacks, grays, with a premium accent color (maybe a subtle blue or gold)
**Typography**: System fonts (-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif)
**Animations**: Smooth, performant, using CSS transforms and opacity with IntersectionObserver

**SVG Illustration**: Need to create a smart glasses SVG that looks premium and detailed enough for a hero

**Sections structure**:
1. Hero (full screen) - headline, subheadline, SVG illustration, scroll indicator
2. Sticky product showcase - glasses rotate/transform as you scroll through this section
3. Features grid - 3-4 features with icons
4. Animated numbers - battery, languages, weight
5. Model comparison - two models side by side
6. Pre-order CTA - dark section with form/button

Let me code this all inline.

For the SVG glasses, I'll create a detailed side/profile view that can rotate.

For scroll animations, I'll use IntersectionObserver for entrance animations, and for the sticky section, I'll track scroll progress within that section to drive the rotation.

Let me write the complete HTML file.