The user wants a canvas-based particle system editor. Let me plan this carefully to make it feel authored and memorable, not like a generic demo.

**Requirements checklist:**
1. Single self-contained HTML file — inline CSS & JS, no external resources at all (no CDNs, no fonts, no images)
2. Central canvas with particles emitting from a source point
3. Sliders: emission rate, particle speed, lifetime
4. Color picker for particle color
5. Button to toggle gravity on/off
6. Particles fade out over time
7. FPS counter
8. CSS-styled UI
9. Vanilla JS only
10. Auto-start with default values

**Design direction:**

I want this to feel like a piece of studio instrument software — a "particle lab" console. My taste says: avoid the generic dashboard feel, avoid default blue/purple, avoid gradients as decoration, avoid emoji. So I'll build something with a distinctive visual identity:

- **Color scheme**: I'll go dark, but not generic. A deep near-black with a warm amber/ember accent? Or a phosphor-green oscilloscope vibe? Let me think... A particle editor begs for the canvas to be the hero. I'll do a very dark warm charcoal (#0e0d0b-ish) with an "ember" orange-amber accent (#ff7a1a / #ffb35c) — feels like sparks/fireworks lab. Monochromatic + one accent. The user can change particle color with the picker, but the UI chrome stays in the ember/neutral family.

Actually, since the user picks the particle color, the UI accent should stay neutral enough to not clash. Hmm — but I want the UI to have character. Option: make the UI accent *follow* the particle color? That's a nice signature detail — when you change the particle color, the UI accent hue shifts to match. That's a memorable "alive" moment: the whole console reacts to your color choice. I can derive accent from the picked color's hue, with careful saturation/lightness so text stays readable. That's my signature moment #1.

- **Typography**: no external fonts allowed. System fonts only... I dislike using Inter/Roboto/Arial/system-ui as the identity font. Without external resources, my options are limited to system font stacks. I can craft a stack with character: use a monospace-forward identity — `"JetBrains Mono", "SFMono-Regular", "SF Mono", Menlo, Consolas, "Liberation Mono", monospace` — a mono-driven lab/terminal aesthetic is very fitting for a "particle console" and it's a deliberate choice, not a lazy default. For big display numerals I can use a condensed feel via letter-spacing tricks, or use `Georgia`/`"Iowan Old Style"` for a serif counterpoint? Hmm, mixing serif labels with mono values could look editorial. Actually let me keep it strictly mono — one typeface family, used with discipline: tiny uppercase letterspaced labels, larger tabular numerals for values. That reads as instrument-panel and is fully offline-safe.

- **Layout**: Not a generic sidebar-dashboard... but a control rail is honestly the right ergonomics for an editor. I'll avoid it feeling generic by:
  - Making the canvas full-bleed behind everything? Or canvas central with a floating control strip?
  - Idea: full-viewport canvas as the stage; controls live in a slim left rail that reads like a hardware rack — each control is a "channel strip" with its own inline readout. A top hairline header with the title, a live particle count, and FPS as a big numeral. Bottom edge: a status line.
  - Actually a distinctive composition: header strip across the top (title left, FPS + particle count right in big mono numerals), a vertical rail on the left with the channel strips (RATE / SPEED / LIFE), gravity toggle as a chunky physical-feeling switch, and the color picker as a custom swatch + hue strips. The canvas fills the rest. Asymmetric, instrument-like.

- **Signature moment #2**: the emission source. Instead of a static point, I could make the emitter draggable on the canvas — grab the source point and drag it anywhere. That's real interactivity beyond the checkboxes. Also emit direction could be aimed... The spec says "emitting from a source point" — I'll make the source point visible (a small crosshair/reticle that pulses with each emission) and draggable. Also: click-drag on canvas could aim? Keep it simple: drag the reticle to move the source; maybe drag creates a temporary burst. Also mouse move could attract? No — keep scope tight but polished.

  Another nice touch: gravity toggle isn't just a checkbox — a chunky toggle switch with a small tick animation, and when gravity turns on, existing particles' behavior changes immediately (visible in the plume bending). I can also show a subtle "g" indicator.

- **Extra flourishes that serve the function** (not decoration):
  - A live mini "sparkline" of emission? Maybe too much. 
  - FPS counter as requested — I'll show it prominently with a tiny frame-time history graph? A small sparkline canvas for FPS could be nice but adds an element... Actually a tiny inline canvas sparkline in the header next to the FPS numeral is genuinely useful (shows jank) and cheap. I'll do a 60px-wide micro-sparkline drawn each frame in the same main canvas? No — separate tiny canvas in header, or draw it in the main canvas top-right corner. Hmm, header has the FPS numeral; I could put a 70×18 sparkline canvas next to it. That's real craft.
  
  Wait — "no external images" — an inline `<canvas>` element is fine, it's not an image resource. Good.

  - Particles: soft round sprites with additive-ish blending (`globalCompositeOperation = 'lighter'`) so overlaps glow naturally — that's earned glow from the physics, not a CSS glow ornament. Fade over lifetime via alpha, and also shrink slightly. Some size variance. Slight velocity spread cone from the source (emission cone pointing up by default, like a fountain). With gravity off, fountain rises and fades; with gravity on, it arcs beautifully. Actually maybe emission direction should be upward with spread — a fountain is the classic and most legible demo. Let me do: emission direction = up (−90°) with a spread angle ±~35°... but then dragging the source matters less. Could also add slight turbulence/drag for life. I'll add a tiny bit of air drag so motion feels natural.

  Hmm, what about making direction controllable? The spec lists specific controls only; I shouldn't bloat, but a draggable emitter that also sets *aim* (drag to reposition; the fountain could tilt away... no, keep it a pure position drag). Actually, here's a neat idea: the source has a direction handle — drag the reticle body to move, and the emission cone... too fiddly. Keep: draggable source, upward fountain cone. Plus click anywhere = one-shot burst? A click (not drag) on empty canvas could fire a burst from that point — fun feedback. Let me include: pointer down on empty canvas = spawn a 30-particle burst at that point (independent of the source), pointer down on the reticle = drag source. That makes the canvas feel alive. And it's real wired behavior.

- **Stats**: particle count (live), FPS. Both in header. The FPS numeral color could go amber→red at low FPS? Subtle.

**Custom slider styling**: I'll style `input[type=range]` heavily — thin track hairline, rectangular thumb like a fader cap. Show the numeric value in mono at the right of the label, updating live. Track fill up to thumb position via a background gradient... hmm, gradients — a linear-gradient used to render the *fill state of a track* is functional, not decorative chrome. It's the standard technique (`background: linear-gradient(to right, accent 0 X%, track X% 100%)`). That's fine — it's a solid two-color hard stop, not a decorative gradient. I'll keep it as a hard-stop fill.

**Color picker**: `input[type=color]` is native and works offline. Styling native color inputs is awkward cross-browser but doable: I'll wrap it — show a custom swatch button that reflects current color + hex readout, with the native input hidden on top (opacity 0) for accessibility. On change: update particle color, derive UI accent (hue) from it, update swatch, hex text. Also maybe preset swatches? A row of 5 tiny preset dots (ember, gold, mint, ice, magenta) for quick picks — wired to set the color. That adds usability without bloat. Keep it to a compact row.

Careful: if user picks a dark/low-sat color, deriving UI accent could make text unreadable. Derivation: convert hex → HSL, clamp s to ≥ 0.5? Actually for UI accent, take the hue, set s = clamp(original s, 45%..75%), l = 60% for text usage, and a dimmer version for fills. If the picked color is gray (s < 8%), fall back to neutral accent. I'll implement `hsl` strings. Use CSS custom properties `--acc`, `--acc-dim`, `--acc-glow`(no glow) — set via `document.documentElement.style.setProperty`.

**Physics model:**
- `rate` (particles/sec): 10–600, default 160.
- `speed` (px/s initial): 40–500, default 220.
- `lifetime` (s): 0.4–6, default 2.2.
- gravity: 0 or ~520 px/s² when on. Default off? "toggle gravity" — I'll default OFF so the fountain rises outward, then user flips it and sees the arc — a nice moment. Actually gravity ON by default gives a prettier classic fountain immediately (first impression!). Hmm. With gravity on and upward emission, particles arc over and fall — very satisfying first impression, and shows fading. Let me default gravity ON. The toggle then lets you turn it off to see the starburst. Either is fine; I'll go gravity ON default for the wow opening. Wait, but requirement says "a button to toggle gravity on/off" — starting on is fine.

  Actually reconsider: with speed 220 up and gravity 520, apex t = v/g ≈ 0.42s, apex height ≈ v²/2g ≈ 46px — small arc. Let me tune: speed default 260, gravity ~420, lifetime 2.4 → falls nicely. Spread cone ±30°. Particles also get per-particle speed variance ×(0.55..1.0) and slight size variance. Drag: v *= exp(-k·dt) with k≈0.12? Light drag keeps it lively. Maybe drag only when gravity on? Keep uniform small drag.

- Emission: accumulator `emitAcc += rate*dt; n = floor(emitAcc); emitAcc -= n;` spawn n per frame (cap per-frame spawn to avoid spiral of death, e.g. ≤ 60 per frame? At 600/s and 60fps that's 10/frame, fine; if tab throttled, dt could spike — clamp dt to ≤ 0.05s and cap spawns per frame at like 40, dropping the rest by resetting accumulator if n too big: `if (n > 40) n = 40, emitAcc = 0`).

- Max particle cap: 4000 (safety). Pool via array with swap-remove.

- Rendering: additive `lighter` over dark bg. Each particle: `alpha = (1 - age/life)^? ` — fade: use a curve so it stays bright then fades: alpha = pow(1-t, 1.5)? "Fade out over time" — linear-ish is fine but ease makes it nicer. I'll do alpha = (1-t)² × something? (1-t)^1.6. Size = base × (1 - 0.5t). Draw as circles: `ctx.arc` per particle could be slow at 3000 particles. Alternative: draw with `fillRect` of small squares — but I dislike plain square particles. Better: pre-render a soft sprite (radial gradient on offscreen canvas, 32×32) per… but color changes; I can tint via globalAlpha and drawing colored circles. Performance approach: render soft sprite in white, then use `ctx.globalCompositeOperation='lighter'` won't tint white to arbitrary color... Options:
  1. Rebuild sprite when color changes (only on change) — sprite is the current color with radial falloff. Cache it. Great: one offscreen canvas, redraw only when color changes. Then each particle = one `drawImage` with scaling. drawImage 3000×/frame is fine.
  2. Arc fill per particle — fine up to ~1500 but slower.
  
  I'll do the sprite approach: radial gradient from solid center → transparent, in current particle color. On color change, regenerate. That gives soft glowing sparks, additive blending, high perf. Also the burst/click particles use same sprite.

  Also a faint trail effect? Motion blur via drawing a translucent black rect each frame instead of clear (`ctx.fillStyle='rgba(bg,0.35)'`) gives trails — pretty, but "fade out" is already handled; trails add mood. With additive blending + fade rect, trails look great (spark trails). But clearing partially can leave color residue tinting background — with pure dark bg and dark fill matching, it's fine. Risk: `lighter` accumulation + partial clear can leave permanent residue if alpha fade rect isn't enough — residue decays geometrically; with 0.35 alpha per frame it's fine. But background must be uniform: I'll fill canvas bg in CSS too. Hmm, trails could muddy the crispness. Let me make trails subtle: clear with bg color at alpha 0.45. Actually I'll draw bg as solid each frame but keep a second pass? Simplest robust: per frame, `ctx.globalCompositeOperation='source-over'; ctx.fillStyle = 'rgba(14,13,11,0.5)'; fillRect` then draw particles with 'lighter'. That yields short elegant trails. But careful: the reticle/crosshair drawn on canvas would smear — draw reticle last with source-over full alpha, and it moves only when dragged, so slight smear only during drag — acceptable, or redraw reticle area? Simpler: draw reticle via DOM? I'll draw the reticle on canvas each frame after the fade fill; when stationary, previous frame's reticle gets faded toward bg then redrawn — reaching an equilibrium slightly brighter than faded bg — it'll look like a slight halo. To avoid mess: keep reticle drawn every frame with 'source-over' at full opacity — equilibrium image is reticle color composited repeatedly... since it redraws over the faded remnant of itself, it converges to stable color = its own color roughly. Fine.

  Actually, cleaner: use two-layer approach — trails via fade rect, reticle drawn crisply. It'll be fine visually. Alternatively skip trails; solid clear + sprite glow already looks good. I'll include mild trails (fade alpha ~0.45) because sparks + trails = the memorable look. And when gravity toggles, the plume visibly bends — great feedback.

- Resize handling: canvas sized to container × devicePixelRatio, capped dpr at 2 for perf.

**FPS**: measure via rAF delta EMA. Display rounded. Sparkline: keep last ~48 frame dts, draw in tiny header canvas — normalize to 0–120fps scale. Update every frame (cheap). Color the line with accent.

**Header copy** (in English, matching user language): Title like "EMBER — particle bench" hmm. Name it something like "SPARKBENCH" or "Particle Bench". I'll go with a small wordmark: "SPARK/LAB" or "ember·console". Let me pick: `PARTICLE BENCH` with an index "v1.0"? Keep restrained: left: small accent dot + "PARTICLE BENCH" letterspaced mono; right: FPS big numeral + "FPS" label + sparkline + divider + "PARTICLES" count. Also maybe a status line at bottom-left of rail: "drag the emitter · click canvas to burst".

**Control rail layout** (left, width ~272px, dark panel, hairline border):
- Section: EMISSION — "RATE" slider + value "160 /s"; "SPEED" + "260 px/s"; "LIFETIME" + "2.4 s".
- Section: FORCES — gravity toggle: a custom switch (button role=switch) with label "GRAVITY" and ON/OFF state; plus maybe a "gravity strength"? Not requested; skip to keep focused. Maybe add "WIND"? No — stick to spec, polish what's there.
- Section: COLOR — swatch + hex + preset dots row.
- Footer of rail: hint text.

Actually order per spec: sliders, color, gravity button. I'll arrange: EMISSION (3 sliders), COLOR, FORCES (gravity) — visual grouping beats literal order. Fine.

Slider styling details: 
- track height 2px, background via hard-stop linear-gradient using `--val` percentage updated in JS (or compute in JS string). I'll update `--p` custom property per input.
- thumb: 4px wide × 16px tall rect, accent color, slight radius. Firefox needs `-moz-range-thumb` too. Use `appearance:none`.
- Hover: thumb grows to 6px wide. Focus-visible outline.

Numbers: displayed in accent, tabular-nums.

**Gravity toggle design**: full-width row: label "GRAVITY" left, right a switch: 40×22 track with 16px knob; ON = accent track; text state "ON"/"OFF" beside. Also make the whole row clickable. aria-pressed. When toggled, tiny physics feedback: maybe give existing particles a small impulse? Nice touch: flipping gravity ON instantly is felt by particles naturally (they start accelerating down) — inherent feedback. Good enough.

Also, maybe a small readout "g = 520 px/s²" appears when on. Nice detail.

**Interactions summary:**
- Drag reticle on canvas → move source. Cursor: grab/grabbing via hit test on pointermove.
- Click (pointerdown not on reticle, quick) → burst of ~40 particles at click point, radially random + upward bias? Radial burst all directions looks great with additive glow. I'll do radial.
- Sliders live-update (values apply to new emissions instantly; lifetime change also affects existing via their stored life — keep stored per-particle, new value applies to new ones).
- Color change → sprite regen + accent theme shift + swatch/hex update.
- Gravity toggle.
- FPS + count always live.
- Pause when tab hidden automatically (rAF handles), clamp dt.

Should I add a "burst on color change"? No.

Also maybe keyboard: Space toggles gravity? Small extra: yes, keydown space toggles gravity (when not focused on input). And arrow keys? Skip. Add hint text mentioning space. Actually keep hints minimal: "drag emitter · click canvas to burst · space toggles gravity". 

**Accent derivation math:**
```js
function hexToRgb(h){...}
rgbToHsl -> h,s,l
if (s*100 < 10) => neutral accent: use warm gray? If user picks pure gray particles, UI accent could be desaturated warm: h=36,s=20%,l=62%? Hmm, or just clamp s to min 30 with original hue. Gray has undefined hue; fall back to hue 36 (ember) with s 25%. 
accentText = hsl(h, clamp(s,0.55,0.85), 0.62)
accentFill = hsl(h, clamp(s,0.5,0.8), 0.5) for swatch borders? Keep two vars: --acc (bright, for values/thumbs), --acc-deep (darker for track fills when inactive? track inactive is neutral anyway).
```
Also set slider fill colors to accent automatically via CSS var — since gradient uses `var(--acc)`. 

Default particle color: warm ember `#ffb347`? Additive blending with bright orange on dark = lovely sparks. Let me default `#ffae42`-ish. I'll pick `#ffb454`. Hmm or `#ff9e2c`. Sprite center should be near-white-hot for spark realism: radial gradient from `rgba(255,255,255-ish tint)` center to color to transparent. Center: mix color toward white 70%. That makes sparks look hot at birth — and as they fade (alpha down), they dim through color. 

Sprite build: 48×48 offscreen, radial gradient stops:
- 0: white-mixed color, alpha 1
- 0.25: color alpha .85? Let me: stops [0, cL], [0.3, c], [1, transparent]. Where cL = lighten(color, .75). Actually to keep it punchy: center solid near-white, mid = pure color, edge transparent. Since additive, overlaps bloom.

Particle render: size s (6..14 base px sprite scale), alpha per life. `ctx.globalAlpha = a; ctx.drawImage(sprite, x-s/2, y-s/2, s, s)`. Cap globalAlpha at min 0? skip tiny alphas.

Also update loop: substep? Not needed; dt clamp 0.033? Clamp 0.05.

Physics per particle: `vx *= drag; vy = vy*drag + g*dt; x+=vx*dt; y+=vy*dt`. drag factor per second k=0.15 → v *= Math.exp(-k*dt) ≈ 1-0.15dt. Fine. Add tiny jitter/wiggle? A small sinusoidal wander for aliveness: `vx += (rand-0.5)*wander*dt*...`? Sparks with turbulence: add per-particle phase and apply lateral force = sin(t*f + phase)*amp when gravity off? Could be nice "ember drift". Keep subtle: lateral force amp 30 px/s², freq ~3 rad/s, per-particle phase. Actually simpler: tiny random acceleration each frame: vx += (Math.random()-0.5)*40*dt; makes shimmer. Keep it — makes plume feel alive. Small value so it doesn't look noisy: 60*dt on vy too? Only lateral. I'll do both tiny (like flicker). Hmm, random walk on velocity each frame at 60fps: sum ~ sqrt(n)*0.5*60*... it accumulates; keep amp small (≈ ±25*dt per frame → velocity stddev grows ~ 25*sqrt(t)) — acceptable drift. Let me instead use deterministic per-particle flicker: precomputed phase, apply `vx += Math.sin(now*5+phase)*20*dt`. Deterministic, no random-walk blowup. Good.

Click burst: 36 particles, speed = speed-slider × rand(0.4..1.1), radial angle random 0..2π but biased upward? Full radial reads as "poof" — full radial. Lifetime × rand(0.5..0.9). Nice.

Count display: format with thin space? Just number, e.g. "1 284"? Use toLocaleString('en-US')? Use plain grouping via regex, or just show raw. I'll format with commas — fine in en.

**HTML structure:**

```
<body>
  <header> wordmark | stats (fps big, sparkline canvas, count) </header>
  <main>
    <aside id="rail"> ... controls ... </aside>
    <div id="stage"> <canvas id="view"></canvas> <div class="stage-hint">…</div> </div>
  </main>
</body>
```

Grid: body grid rows auto 1fr; main grid columns 280px 1fr. Canvas absolute fill of stage. Hint bottom-left of stage, subtle mono uppercase.

Rail sections separated by hairlines, labels 10px letterspaced uppercase, values right-aligned accent.

Let me also consider a subtle scanline/grain? No — keep clean.

One more compositional idea to avoid generic feel: give the rail a slightly different surface tone and a right hairline; header hairline bottom. Use pure flat colors + hairlines (1px rgba white 6-8%). Precise, instrument-like. Corner ticks on the stage? A small crosshair-corner detail (like camera viewfinder corners) drawn in CSS at stage corners — nice authored touch, cheap: four L-shaped corners via pseudo-elements or 4 spans. I'll add subtle viewfinder corners on the stage. That's the kind of detail that makes it feel crafted.

Reticle (emitter) drawing: small crosshair: circle radius 9, tick marks, plus accent color; pulse ring emitted on spawn? A subtle expanding ring each ~0.5s? Might be noisy. Instead: reticle brightness scales with recent emission (flickers with rate). Simple: draw ring with alpha pulsing at emission events... simplest: static crisp reticle + when dragging, slightly larger ring. Also label "SOURCE" tiny next to it? Draw text "SOURCE" mono 9px next to reticle in 40% white — helpful affordance. Yes, with a leader line? Keep: text at offset (14, -14). Nice.

Default source position: center-ish, slightly below middle so fountain has headroom: x = stage.width*0.5, y = stage.height*0.62.

**Canvas sizing**: observe stage resize (ResizeObserver or window resize). Set canvas.width = clientWidth*dpr etc; keep ctx scale via setTransform(dpr,0,0,dpr,0,0). On resize, re-ctx size (resets transform → reapply), keep particles (they may be out of bounds — fine, they'll fall out; clamp spawn positions).

When dpr changes… fine.

Trails + resize: fillRect fade covers full canvas each frame — ok.

Note: with fade-rect trails, after resize the canvas clears to transparent → CSS bg shows (dark) — matches fade color, fine. But fade rect uses rgba of bg color (opaque-ish accumulation): background CSS color should equal the fade color's target: bg #0d0c0a. Fade fill 'rgba(13,12,10,0.45)'. Hmm — repeated alpha compositing over transparent initially: first frame fill 45% over transparent → effectively #0d0c0a at 45% over the CSS bg which is same color → converges to exact bg. Good, no residue shift. Residue of particles: decays but with additive bright values can tint — alpha .45 per frame → after 10 frames ~0.3% remains, negligible; slight warm cast could linger behind plume which actually looks like smoke/heat haze — kind of beautiful. OK.

Wait, one issue: 'lighter' composite with alpha particles over the faded bg — the canvas is fully opaque after first frames (alpha accumulates to 1). Fine.

Also I should set `ctx.globalCompositeOperation='lighter'` for particles then back to 'source-over' for fade fill and reticle text.

**FPS sparkline**: tiny canvas 64×20 CSS px (dpr-scaled). Keep ring buffer of last 64 fps samples (updated per frame). Draw: clear, path across, map fps 0..90 → y. Stroke accent at 1px, plus baseline hairline at 60fps? A tick at 60 fps line (dim). Draw every frame — trivial. Actually draw every other frame to save — fine every frame.

FPS value: EMA of 1/dt with alpha 0.08; display Math.round. Color shifts: if fps < 30 → use a warning tone? Use accent always; maybe dim. Keep accent; add class when < 30 → color shifts to a red-ish? I'll set data-low attr and CSS handles color (muted red #e05252). Careful about "meaningless colored accents" — a low-FPS warning is meaningful. Keep.

**Slider config:**
- RATE: min 10, max 600, step 5, default 160. Unit "/s".
- SPEED: min 20, max 500, step 5, default 260. "px/s".
- LIFETIME: min 0.4, max 6, step 0.1, default 2.4. "s".

Show value formatted (lifetime one decimal).

**Preset swatches**: ember `#ffb454`, gold `#ffe14d`? careful contrast; mint `#5ce8b8`? ice `#7ad7ff`, rose `#ff6f91`, violet? I avoid default blue/purple as UI chrome, but particle *content* presets are user content — still, I'd rather avoid purple entirely. Presets: EMBER #ffb454, FLARE #ff5c3a? hmm red-orange, LIME #d7ff5c? MINT #6fe3c1, ICE #7cd6ff, WHITE #f5f1e8. Five dots. Clicking sets color input value + applies. Active preset highlighted with ring. If custom color picked, no preset active. Nice detail.

Preset dots: 14px circles, border hairline, hover scale. These are functional (wired), tiny, not "filler chips". OK.

**Gravity switch markup:**
```html
<div class="ctl force-row">
  <span class="lab">GRAVITY</span>
  <button id="gravBtn" role="switch" aria-checked="true" class="switch on"><span class="knob"></span></button>
</div>
<div class="force-meta" id="gravMeta">g = 520 px/s² · downward</div>
```
Meta hidden/dimmed when off: text becomes "g = 0 · free float". Always show, dim when off — good feedback.

**Space key**: toggles gravity; ensure not when focus on button (space on button also triggers click → double toggle). So: if e.target is button/input, skip. Or preventDefault when handling. I'll check `if (e.code==='Space' && !['BUTTON','INPUT'].includes(e.target.tagName))`. But after clicking the switch, focus stays on button → space would toggle via button default; that's actually consistent behavior. To avoid confusion, blur the button after click. Then space works globally. Good.

Also prevent page scroll on space: preventDefault when we handle.

**Color input overlay**: 
```html
<label class="swatch-wrap">
  <input type="color" id="colorPick" value="#ffb454">
  <span class="swatch" id="swatch"></span>
</label>
<span class="hex" id="hex">#FFB454</span>
```
input positioned absolute inset-0 opacity 0 cursor pointer. Clicking opens native picker. Firefox/Chrome both fine. Also the swatch shows current color with a hairline border.

Actually careful: hidden input inside label — clicking label triggers input → opens picker. Works. Keyboard: input focusable? opacity 0 still focusable; focus-visible → show ring on swatch via `:focus-visible + .swatch { outline }`. 

**Now the CSS theme:**

Colors:
- bg: #0d0c0a (warm near-black)
- panel: #12100d / rail bg #100e0b
- hairline: rgba(255, 240, 220, 0.08)
- text: #e8e2d6 (warm off-white)
- text-dim: #8a8378
- accent: derived (default from #ffb454 → hue ~35)

Derived default: from #ffb454: RGB(255,180,84) → HSL: h≈35.5°, s=100%, l=66.6%. Clamp s to 0.8 → accent text = hsl(35, 80%, 64%) ≈ vivid amber. 

Set vars in JS on load too (so presets/custom can update): `setAccent(color)`.

CSS uses:
```
--acc: hsl(35 80% 64%);
--acc-dim: hsl(35 80% 64% / .35);
```
I'll set `--acc` and compute dim variants with `color-mix`? color-mix widely supported now, but to be safe just set three vars in JS: `--acc`, `--acc-soft` (alpha .4), `--acc-faint` (alpha .16). Use hsl with slash alpha string.

Also slider fill uses `--acc`; inactive track #2a261f-ish rgba(255,240,220,.12).

Header height ~56px; wordmark: dot (accent) + "PARTICLE BENCH" 12px ls .2em + sub "canvas emitter · v1" dim? Keep: "PARTICLE BENCH" and dim suffix "/ console". 

Stats right: 
```
FPS  <big>60</big> [sparkline] | PARTICLES <big>0</big>
```
Big numerals: 22px mono, accent for FPS, text for count? Both accent? FPS accent, count text color. Labels 9px dim above or beside. I'll do label above-right? Layout: two stat blocks, each: label (9px dim, ls .18em) top, value below. Sparkline sits beside FPS value. Divider hairline vertical between stats.

Rail width 264px. Padding 18px 18px. Sections with 20px gaps, hairline separators.

Slider rows: label row (name left, value right) then track below (full width). Track height area 24px hit area with 2px visual line centered. Use padding on input.

CSS for range:
```css
input[type=range]{ -webkit-appearance:none; appearance:none; width:100%; height:22px; background:transparent; cursor:ew-resize; }
input[type=range]::-webkit-slider-runnable-track{ height:2px; background:linear-gradient(90deg, var(--acc) var(--p,50%), rgba(232,226,214,.14) var(--p,50%)); }
input[type=range]::-webkit-slider-thumb{ -webkit-appearance:none; width:5px; height:16px; margin-top:-7px; background:var(--acc); border-radius:1px; ... transition:width .15s; }
input[type=range]:hover::-webkit-slider-thumb{ width:7px }
input[type=range]::-moz-range-track{...} ::-moz-range-thumb{...} ::-moz-range-progress{ background:var(--acc); height:2px }
```
For Firefox use `-moz-range-progress` for fill (no gradient needed) and plain track bg.

JS updates `--p` on input: `el.style.setProperty('--p', pct+'%')`. pct=(v-min)/(max-min)*100.

Thumb glow? No.

**Viewfinder corners**: `.stage::before/::after` can only give 2; use 4 spans `.corner.tl` etc: 14×14 with border-top/left etc, rgba accent? Neutral hairline with accent tick? Use dim warm: `border-color: rgba(232,226,214,.22)`. Positioned inset 10px. Subtle.

**Hint bar**: bottom-left inside stage: mono 9.5px dim uppercase: "DRAG SOURCE TO MOVE · CLICK CANVAS TO BURST · SPACE = GRAVITY". Positioned absolute; pointer-events none. But it overlaps canvas clicks visually — pointer-events:none so fine.

**Cursor on canvas**: default crosshair; over reticle → grab; dragging → grabbing. Manage via JS setting `canvas.style.cursor`.

**Pointer logic:**
- pointerdown: hit test reticle (dist < 16/care dpr — use CSS px coords) → dragging=true, offset; else → burst at point + remember downPos/time to distinguish? Simplest: non-reticle pointerdown fires burst immediately (fun, immediate). Drag after click would spawn more bursts? Only on down, not move — so press-drag from empty area does nothing more. Acceptable and simple: down anywhere (not reticle) = burst. Also pointermove with drag reticle updates source. Use setPointerCapture.

Coordinates: rect-based CSS px, physics in CSS px, ctx scaled by dpr — all good.

**Particle struct**: plain object pool: array `parts`, objects {x,y,vx,vy,life,age,size,phase,alive}. Swap-remove dead. Preallocate? Just create objects; GC ok for few hundred/sec. To be safer use pool of objects reused. I'll keep simple with pool: freelist array. Eh — simple array + swap remove is fine; allocation churn at 600/s is trivial for modern JS.

**Emission details**: at spawn: 
```
ang = -PI/2 + (rand-0.5)*cone  // cone ~ 1.15 rad total (±33°)
sp = speed * (0.5 + rand*0.6)  // wait: speed*(0.55..1.15)? use 0.55+rand*0.6 → .55–1.15
vx = cos(ang)*sp, vy = sin(ang)*sp
life = lifetime * (0.7+rand*0.5)
size = 7 + rand*7  (CSS px sprite width)
phase = rand*2π
```
When gravity OFF, pure cone fountain rises and dissipates — with wander shimmer. Good.

Gravity g=520 when on. Drag k=0.10.

Update:
```
p.age+=dt; if age>=life kill.
dragF = Math.exp(-0.10*dt)
p.vx*=dragF
p.vy = p.vy*dragF + g*dt
p.vx += Math.sin(t*4+p.phase)*14*dt  // lateral shimmer
p.x+=p.vx*dt; p.y+=p.vy*dt
```
Kill also if far off-canvas (y > h+80 or x out ±120) to save fill even if lifetime long. Yes — kill offscreen beyond margin. But with gravity off, particles fly up and off; lifetime still bounds. Kill when outside margin bounds — fine.

Alpha: `t = age/life; a = 1-t; a = a*a*(3-2a)`? smoothstep gives slow start fade... fade-out over time: I want ease-in fade (stays bright, then fades): a = (1-t)^1.7. Also early-life ramp? At spawn alpha jumps to 1 immediately — with additive glow it's fine (spark). Use a = pow(1-t, 1.6). Size shrink: s = size*(1 - 0.35*t).

Draw loop:
```
ctx.globalCompositeOperation='source-over';
ctx.fillStyle='rgba(13,12,10,0.45)'; ctx.fillRect(0,0,W,H);
ctx.globalCompositeOperation='lighter';
for(...){ ctx.globalAlpha=a; ctx.drawImage(sprite, x-hs, y-hs, s, s); }
ctx.globalAlpha=1;
drawReticle();
```
At high counts this is the main cost; drawImage with float coords fine.

Reticle draw:
```
const r = dragging?12:9;
ctx.globalCompositeOperation='source-over';
ctx.strokeStyle = accentCss; ctx.lineWidth=1.25;
circle + 4 ticks outside (at 0,90,180,270 from r+2 to r+6);
center dot 1.5px fill;
label 'SOURCE' font '9px' mono fillStyle rgba(text,.55) at (14,-12); small leader? skip leader.
```
Also faint crosshair lines through point (12px long, dim) — like alignment marks. Keep: horizontal & vertical hairlines 20px long, alpha .25.

Pulse: when emitting, ring radius oscillates? Subtle: `r + Math.sin(now*6)*1`? Skip; crisp is fine. Actually a nice alive detail: emission makes the center dot flicker: dot alpha = 0.5 + 0.5*sin(now*rateish)? Cheap and alive: dotAlpha = 0.6+0.4*Math.sin(now*8). OK subtle.

**Burst particles**: same spawn but radial: ang=rand*2π, sp=speed*(0.5+rand*0.8), life=lifetime*(0.4+rand*0.5), size similar. Count 40.

**Init**: default gravity true → aria-checked true, meta shows g value. Auto-start: loop begins immediately, emission accumulator runs. Header values update. Accent set from default color. Sliders `--p` initialized on load for all.

**Numbers formatting**: rate shows "160 /s" — value element contains number only, unit in dim span. e.g. `<b id="vRate">160</b><i> /s</i>` with i styled dim, not italic (font-style normal).

**Fonts stack**: `--mono: "SF Mono", "Cascadia Code", "JetBrains Mono", Menlo, Consolas, "DejaVu Sans Mono", monospace;` Use everywhere. Letter-spacing on labels .18em; numerals `font-variant-numeric: tabular-nums`.

**Accessibility**: labels via `<label>`? Ranges with aria-label. Switch aria. Buttons real buttons.

**Edge**: prefers-reduced-motion? Could respect by lowering trail? Skip — it's an explicitly interactive tool; but I could honor reduced motion by... skip, keep scope.

**Title**: `<title>Particle Bench — Canvas Emitter</title>`

Let me now also think about the *first impression*: page loads → dark stage, amber fountain already erupting from a reticle, additive glow with fading trails, FPS pinned at 60, big tabular numerals. Rail with amber accents matching. That's the moment. Good.

One more: maybe particle count should also render in a big numeral; updating textContent each frame — throttle count/fps DOM updates to ~4×/sec (every 250ms) to avoid layout churn; fps EMA displayed rounded changes rarely anyway. Sparkline updates per frame (canvas only).

Let me write the code.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Particle Bench — Canvas Emitter</title>
<style>
  :root{
    --bg:#0d0c0a;
    --panel:#121009;  /* rail */
    --line:rgba(236,227,208,.08);
    --line-strong:rgba(236,227,208,.16);
    --txt:#e9e2d4;
    --dim:#877f70;
    --faint:#57503f;
    --acc:hsl(36 80% 64%);
    --acc-soft:hsl(36 80% 64% / .45);
    --acc-faint:hsl(36 80% 64% / .14);
    --warn:#e0524f;
    --mono:"SF Mono","Cascadia Code","JetBrains Mono",Menlo,Consolas,"DejaVu Sans Mono","Liberation Mono",monospace;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  html,body{height:100%}
  body{
    background:var(--bg); color:var(--txt);
    font-family:var(--mono); font-size:12px;
    display:grid; grid-template-rows:56px 1fr; overflow:hidden;
  }
  ...
</style>
```

Header:
```html
<header>
  <div class="brand">
    <span class="pip"></span>
    <span class="name">PARTICLE&nbsp;BENCH</span>
    <span class="sub">/ canvas emitter</span>
  </div>
  <div class="stats">
    <div class="stat">
      <span class="slab">FPS</span>
      <span class="sval" id="fpsVal">—</span>
      <canvas id="spark" width="64" height="20"></canvas>
    </div>
    <div class="vdiv"></div>
    <div class="stat">
      <span class="slab">PARTICLES</span>
      <span class="sval" id="cntVal">0</span>
    </div>
  </div>
</header>
```
Canvas spark width attr set with dpr in JS; CSS size 64×20.

Layout `.stat{display:flex;align-items:baseline;gap:8px}` slab 9px dim ls .18em; sval 20px tabular. Spark canvas align: center vertically — set align-items:flex-end? Let me align-items:center on stat, slab baseline issues… I'll do: stat is flex column? Simpler: header stats as row of blocks each `display:grid; grid-template-columns:auto auto; column-gap:8px; row-gap:2px` label top-left small, value below. Sparkline spans? Put sparkline to the right of FPS value aligned bottom. Use flex with align-items:flex-end and label above via wrapping each stat as column:

```css
.stat{display:flex; flex-direction:column; align-items:flex-end; gap:3px}
.srow{display:flex; align-items:flex-end; gap:8px}
```
Meh — simpler markup: each stat: `<div class="stat"><span class="slab">FPS</span><div class="srow"><span class="sval" id="fpsVal">60</span><canvas id="spark"></canvas></div></div>`. Stat column: label on top (right-aligned), row below. align-items:flex-start? Right aligned all: flex-end. OK.

Rail:

```html
<aside id="rail">
  <section class="grp">
    <h2>EMISSION</h2>
    <div class="ctl">
      <div class="crow"><label for="rate" class="lab">RATE</label><span class="val"><b id="vRate">160</b><i>/s</i></span></div>
      <input type="range" id="rate" min="10" max="600" step="5" value="160" aria-label="Emission rate">
    </div>
    ... speed, lifetime ...
  </section>
  <section class="grp">
    <h2>COLOR</h2>
    <div class="colorrow">
      <label class="swatch-wrap" title="Pick particle color">
        <input type="color" id="colorPick" value="#ffb454" aria-label="Particle color">
        <span class="swatch" id="swatch"></span>
      </label>
      <span class="hex" id="hex">#FFB454</span>
    </div>
    <div class="presets" id="presets"></div>  <!-- built in JS -->
  </section>
  <section class="grp">
    <h2>FORCES</h2>
    <button id="gravBtn" class="forcerow" role="switch" aria-checked="true">
      <span class="lab">GRAVITY</span>
      <span class="state" id="gravState">ON</span>
      <span class="switch"><span class="knob"></span></span>
    </button>
    <div class="meta" id="gravMeta">g = 520 px/s² · downward</div>
  </section>
  <footer class="railfoot">
    <span>DRAG SOURCE TO MOVE</span>
    <span>CLICK CANVAS TO BURST</span>
    <span>SPACE — GRAVITY</span>
  </footer>
</aside>
<div id="stage">
  <canvas id="view"></canvas>
  <i class="corner tl"></i><i class="corner tr"></i><i class="corner bl"></i><i class="corner br"></i>
  <div class="hint">LIVE · EMITTER ACTIVE</div>  ?
</div>
```

Hmm hint about interactions better placed in rail footer (done). Stage corner ticks + maybe a tiny status bottom-left inside stage: "SOURCE x,y" readout updating while dragging? Nice instrument touch: bottom-left shows `SRC 512,384` mono dim. I'll add `#srcReadout` absolute bottom-left, updated on move. Cheap, alive. But pointer-events none.

Rail footer: stacked hints, 9px dim, separated by thin rules? Use column gap; each hint prefixed with an index "01 /" style? Cute: 
```
01 DRAG SOURCE TO MOVE
02 CLICK CANVAS TO BURST
03 SPACE TOGGLES GRAVITY
```
With index in faint. Push to bottom via rail flex column, footer margin-top:auto.

Group headers h2: 9px dim ls .22em with a short accent tick before? `h2::before{content:"";width:10px;height:1px;background:var(--acc)}` inline-block. Subtle. Or `border-left`? I'll do small dash before text: display:flex;align-items:center;gap:8px; ::before 10px×1px accent-faint. Fine.

Now full CSS:

```css
header{
  display:flex; align-items:center; justify-content:space-between;
  padding:0 20px; border-bottom:1px solid var(--line);
  background:var(--panel);
}
.brand{display:flex; align-items:baseline; gap:10px}
.pip{width:7px;height:7px;background:var(--acc);align-self:center; }
```
pip square (not gradient) — accent square 7px. Baseline vs center conflict: set align-self:center. name: 12px, ls .22em, weight 600? mono bold. sub: 10px dim ls .08em.

.stats{display:flex;align-items:center;gap:20px}
.vdiv{width:1px;height:24px;background:var(--line-strong)}
.stat{display:flex;flex-direction:column;align-items:flex-end;gap:3px}
.slab{font-size:9px;letter-spacing:.2em;color:var(--dim)}
.srow{display:flex;align-items:center;gap:8px}
.sval{font-size:20px;line-height:1;font-variant-numeric:tabular-nums;color:var(--txt); min-width:2ch; text-align:right}
#fpsVal{color:var(--acc)}
#fpsVal.low{color:var(--warn)}
#spark{width:64px;height:20px; opacity:.9}

main{display:grid;grid-template-columns:264px 1fr;min-height:0}
#rail{border-right:1px solid var(--line);background:var(--panel);padding:18px 18px 14px;display:flex;flex-direction:column;gap:22px;overflow-y:auto}
.grp{display:flex;flex-direction:column;gap:14px}
.grp h2{font-size:9px;font-weight:600;letter-spacing:.24em;color:var(--dim);display:flex;align-items:center;gap:8px}
.grp h2::before{content:"";width:12px;height:1px;background:var(--acc-soft)}
.ctl{display:flex;flex-direction:column;gap:6px}
.crow{display:flex;justify-content:space-between;align-items:baseline}
.lab{font-size:10px;letter-spacing:.14em;color:var(--dim)}
.val{font-size:12px;color:var(--txt);font-variant-numeric:tabular-nums}
.val b{font-weight:600;color:var(--acc)}
.val i{font-style:normal;color:var(--faint);margin-left:3px;font-size:10px}
```

Range styling (webkit + moz):
```css
input[type=range]{
  -webkit-appearance:none;appearance:none;
  width:100%;height:22px;background:transparent;cursor:ew-resize;--p:50%;
}
input[type=range]:focus{outline:none}
input[type=range]::-webkit-slider-runnable-track{
  height:2px;border-radius:1px;
  background:linear-gradient(90deg,var(--acc) var(--p),var(--line-strong) var(--p));
}
input[type=range]::-webkit-slider-thumb{
  -webkit-appearance:none;width:5px;height:16px;border-radius:1px;
  background:var(--acc);margin-top:-7px;
  box-shadow:none; transition:width .12s ease;
  border:none;
}
input[type=range]:hover::-webkit-slider-thumb,
input[type=range]:active::-webkit-slider-thumb{width:8px}
input[type=range]:focus-visible::-webkit-slider-thumb{outline:1px solid var(--acc-soft); outline-offset:2px}
```
Hmm outline on thumb pseudo may not work everywhere; alternative: focus-visible on input → show ring via track? Keep simple: `input[type=range]:focus-visible{outline:1px dashed var(--acc-soft); outline-offset:4px}` on the input itself. That works.

Firefox:
```css
input[type=range]::-moz-range-track{height:2px;background:var(--line-strong)}
input[type=range]::-moz-range-progress{height:2px;background:var(--acc)}
input[type=range]::-moz-range-thumb{width:5px;height:16px;border:none;border-radius:1px;background:var(--acc)}
input[type=range]:hover::-moz-range-thumb{width:8px}
```

Color row:
```css
.colorrow{display:flex;align-items:center;gap:10px}
.swatch-wrap{position:relative;width:34px;height:34px;cursor:pointer;display:block}
.swatch-wrap input{position:absolute;inset:0;opacity:0;cursor:pointer}
.swatch{position:absolute;inset:0;background:var(--pick,#ffb454);border:1px solid var(--line-strong);border-radius:3px}
.swatch::after{content:"";position:absolute;inset:3px;border:1px solid rgba(0,0,0,.25);border-radius:2px} 
```
Inner border gives physical swatch feel. Focus-visible: `.swatch-wrap:has(input:focus-visible) .swatch{outline:1px dashed var(--acc-soft);outline-offset:3px}` — :has support fine in modern browsers; fallback harmless.

.hex{font-size:12px;color:var(--txt);letter-spacing:.06em}

.presets{display:flex;gap:8px}
.preset{width:16px;height:16px;border-radius:50%;border:1px solid rgba(0,0,0,.4);cursor:pointer;position:relative; transition:transform .12s ease; padding:0; background:var(--c)}
.preset:hover{transform:scale(1.25)}
.preset.on::after{content:"";position:absolute;inset:-4px;border:1px solid var(--acc-soft);border-radius:50%}

Gravity row:
```css
.forcerow{display:flex;align-items:center;gap:10px;width:100%;background:transparent;border:none;color:inherit;font:inherit;cursor:pointer;padding:2px 0;text-align:left}
.forcerow .lab{flex:1}
.state{font-size:10px;letter-spacing:.14em;color:var(--faint); min-width:3ch;text-align:right}
.switch{width:38px;height:20px;border:1px solid var(--line-strong);border-radius:11px;position:relative;background:rgba(236,227,208,.04);transition:background .18s,border-color .18s;flex:none}
.knob{position:absolute;top:3px;left:3px;width:12px;height:12px;border-radius:50%;background:var(--dim);transition:transform .18s ease,background .18s}
.forcerow[aria-checked="true"] .switch{background:var(--acc-faint);border-color:var(--acc-soft)}
.forcerow[aria-checked="true"] .knob{transform:translateX(18px);background:var(--acc)}
.forcerow[aria-checked="true"] .state{color:var(--acc)}
.meta{font-size:10px;color:var(--faint);letter-spacing:.06em;padding-left:0}
.meta.off{opacity:.55}
```
Wait knob travel: width 38, knob 12 + left3 + right3 → travel = 38-6-12=20. translateX(20px). And top: (20-2border*? height20 incl border? box-sizing border-box → inner 18; knob top = (18-12)/2=3 relative to border-box? position absolute relative to padding box (inside border): top:2px? height 20 with 1px borders → content box 18px tall. top:3px would overflow? absolute positioning is relative to padding box: available 18px, knob 12 → top 3px fits. left:3px similarly inside. translate 20px: 3+12+20=35 ≤ inner width 36 → ok (inner width = 38-2=36; 3+20+12=35, 1px slack). Set translateX(20px).

Hover on switch: border-color brighter.

.railfoot{margin-top:auto;display:flex;flex-direction:column;gap:7px;padding-top:16px;border-top:1px solid var(--line)}
.railfoot span{font-size:9px;letter-spacing:.14em;color:var(--faint)}
.railfoot span b{color:var(--dim);font-weight:400;margin-right:8px} → index numbers as `<b>01</b>DRAG SOURCE TO MOVE`.

Stage:
```css
#stage{position:relative;min-width:0;min-height:0}
#view{position:absolute;inset:0;width:100%;height:100%;display:block;cursor:crosshair}
.corner{position:absolute;width:12px;height:12px;pointer-events:none;opacity:.6}
.tl{top:10px;left:10px;border-top:1px solid var(--line-strong);border-left:1px solid var(--line-strong)}
... tr br bl ...
.srcinfo{position:absolute;left:26px;bottom:16px;font-size:9px;letter-spacing:.16em;color:var(--faint);pointer-events:none;font-variant-numeric:tabular-nums}
```
Corners inset 10px; srcinfo at left 26 bottom 14 to clear corner.

Also stage needs overflow hidden.

Responsive: below ~760px, rail could go bottom? Simplify: media query → main becomes rows: canvas 1fr + rail horizontal-scroll? Keep simple: `@media (max-width:720px){ main{grid-template-columns:1fr; grid-template-rows:1fr auto} #rail{border-right:none;border-top:1px solid var(--line); flex-direction:row; flex-wrap:wrap; gap:16px; max-height:200px} .grp{flex:1;min-width:140px} .railfoot{display:none} }` — decent.

Scrollbar styling for rail: thin, dark.

Now the JS.

```js
(() => {
'use strict';

/* ---------- state ---------- */
const S = {
  rate: 160, speed: 260, life: 2.4,
  gravity: true, g: 520, drag: 0.10,
  color: '#ffb454',
  src: { x: 0, y: 0 },   // CSS px; set after sizing
};

const canvas = document.getElementById('view');
const ctx = canvas.getContext('2d');
const stage = document.getElementById('stage');

let W = 0, H = 0, dpr = 1;

/* particles */
const parts = [];
const MAX = 4500;

/* sprite */
let sprite = document.createElement('canvas');
const SPR = 48;
sprite.width = sprite.height = SPR;

function buildSprite(hex){
  const c = sprite.getContext('2d');
  c.clearRect(0,0,SPR,SPR);
  const {h,s,l} = hexToHsl(hex);
  const core = `hsl(${h} ${s}% ${Math.min(96, l + (96-l)*0.78)}%)`;  // near-white-hot
  const mid  = `hsl(${h} ${s}% ${l}%)`;
  const edge = `hsla(${h} ${s}% ${l}% / 0)`;
  const g = c.createRadialGradient(SPR/2,SPR/2,0,SPR/2,SPR/2,SPR/2);
  g.addColorStop(0, core);
  g.addColorStop(0.22, mid);
  g.addColorStop(1, edge);
  c.fillStyle = g;
  c.fillRect(0,0,SPR,SPR);
}
```

Hmm hsl percent formatting: `${h}` number ok; s and l as percents numbers. `hsla(h s% l% / 0)` — space-separated with slash works in canvas? Canvas fillStyle accepts CSS color syntax — modern browsers support `hsl(120 50% 50% / 0)`. To be safe use comma syntax: `hsla(${h},${s}%,${l}%,0)`. Comma syntax universally safe. I'll produce comma syntax everywhere in canvas. For CSS vars, modern syntax fine, but I'll just also use comma syntax in JS-set vars: `hsl(36,80%,64%)` — valid CSS too. Alpha: `hsla(36,80%,64%,0.45)`.

Color conversion helpers:

```js
function hexToRgb(hex){
  const n = parseInt(hex.slice(1), 16);
  return [(n>>16)&255, (n>>8)&255, n&255];
}
function rgbToHsl(r,g,b){
  r/=255;g/=255;b/=255;
  const mx=Math.max(r,g,b), mn=Math.min(r,g,b), l=(mx+mn)/2;
  if(mx===mn) return {h:36,s:0,l:l*100};   // achromatic → fallback hue
  const d=mx-mn, s=l>0.5 ? d/(2-mx-mn) : d/(mx+mn);
  let h;
  if(mx===r) h=((g-b)/d + (g<b?6:0));
  else if(mx===g) h=(b-r)/d+2;
  else h=(r-g)/d+4;
  return {h:h*60, s:s*100, l:l*100};
}
```

Accent derivation:
```js
function setAccent(hex){
  let {h,s,l} = rgbToHsl(...hexToRgb(hex));
  const sat = Math.max(38, Math.min(85, s));
  if (s < 8) { h = 36; }           // gray picks keep a warm ember chrome
  const acc = `hsl(${h.toFixed(0)},${sat.toFixed(0)}%,64%)`;
  const r = document.documentElement.style;
  r.setProperty('--acc', acc);
  r.setProperty('--acc-soft', `hsla(${h.toFixed(0)},${sat.toFixed(0)}%,64%,0.45)`);
  r.setProperty('--acc-faint', `hsla(${h.toFixed(0)},${sat.toFixed(0)}%,64%,0.13)`);
}
```
Also lightness clamp: if l very low (near-black particle) accent at 64% still fine.

resize:
```js
function resize(){
  dpr = Math.min(2, window.devicePixelRatio || 1);
  const r = stage.getBoundingClientRect();
  W = Math.max(1, Math.round(r.width));
  H = Math.max(1, Math.round(r.height));
  canvas.width = Math.round(W*dpr);
  canvas.height = Math.round(H*dpr);
  ctx.setTransform(dpr,0,0,dpr,0,0);
  if(!srcInit){ S.src.x = W*0.5; S.src.y = H*0.60; srcInit=true; }
  // clamp source into view
  S.src.x = Math.min(Math.max(S.src.x, 20), W-20);
  S.src.y = Math.min(Math.max(S.src.y, 20), H-20);
}
```
Use ResizeObserver on stage → resize(). Also initial call. srcInit flag.

Spark canvas sizing: fixed 64×20 CSS; set attr = 64*dpr etc. once (dpr known at init). If dpr changes on zoom... recompute in resize too. Simple: in resize set spark.width=64*dpr etc and sctx.setTransform.

Spawn:
```js
function spawn(x,y,burst){
  if(parts.length >= MAX) return;
  const a = burst ? Math.random()*Math.PI*2
                  : -Math.PI/2 + (Math.random()-0.5)*1.15;
  const spMul = burst ? (0.45+Math.random()*0.85) : (0.55+Math.random()*0.6);
  const sp = S.speed * spMul;
  parts.push({
    x, y,
    vx: Math.cos(a)*sp, vy: Math.sin(a)*sp,
    life: S.life * (burst ? 0.45+Math.random()*0.5 : 0.7+Math.random()*0.55),
    age: 0,
    size: (burst? 6:7) + Math.random()*7,
    ph: Math.random()*Math.PI*2,
  });
}
```
Note: object literals inline — ok.

Update+draw:
```js
let emitAcc = 0, last = performance.now();
let fpsEma = 60;
const fpsHist = new Float32Array(64); let fpsIdx = 0;
let lowFPS = false;

function frame(now){
  requestAnimationFrame(frame);
  let dt = (now - last)/1000; last = now;
  if(dt > 0.05) dt = 0.05;       // clamp after tab switches
  if(dt <= 0) return;

  /* fps */
  const inst = 1/dt;
  fpsEma += (inst - fpsEma) * (inst > fpsEma ? 0.06 : 0.12);  // hmm just 0.08
  fpsHist[fpsIdx] = Math.min(inst, 120); fpsIdx = (fpsIdx+1)%fpsHist.length;

  /* emit */
  emitAcc += S.rate*dt;
  let n = Math.floor(emitAcc);
  if(n > 60){ n = 60; emitAcc = 0; } else emitAcc -= n;
  for(let i=0;i<n;i++) spawn(S.src.x, S.src.y, false);

  /* physics */
  const g = S.gravity ? S.g : 0;
  const dr = Math.exp(-S.drag*dt);
  const t = now/1000;
  for(let i=parts.length-1;i>=0;i--){
    const p = parts[i];
    p.age += dt;
    if(p.age >= p.life){ parts[i]=parts[parts.length-1]; parts.pop(); continue; }
    p.vx *= dr;
    p.vy = p.vy*dr + g*dt;
    p.vx += Math.sin(t*4.2 + p.ph)*15*dt;
    p.x += p.vx*dt; p.y += p.vy*dt;
    if(p.x < -90 || p.x > W+90 || p.y > H+90 || p.y < -160){
      parts[i]=parts[parts.length-1]; parts.pop();
    }
  }

  /* draw */
  ctx.globalCompositeOperation = 'source-over';
  ctx.fillStyle = 'rgba(13,12,10,0.42)';
  ctx.fillRect(0,0,W,H);
  ctx.globalCompositeOperation = 'lighter';
  const sp2 = sprite;
  for(let i=0;i<parts.length;i++){
    const p = parts[i];
    const k = p.age/p.life;
    const a = Math.pow(1-k, 1.6);
    if(a < 0.02) continue;
    const s = p.size * (1 - 0.35*k);
    ctx.globalAlpha = a;
    ctx.drawImage(sp2, p.x - s/2, p.y - s/2, s, s);
  }
  ctx.globalAlpha = 1;
  ctx.globalCompositeOperation = 'source-over';
  drawReticle(now/1000);
  drawSpark();
}
```

Wait — trail fade with 'lighter' accumulation issue: fade alpha 0.42 might be too light for trails smear when many particles? fine.

Edge case: with alpha fade fill over fully opaque previous frame — canvas retains alpha 1 always. But first frame canvas is transparent; fillRect with rgba .42 → premultiplied issues? Canvas stores straight alpha; repeated fills converge; additive lighter adds alpha too. Eventually opaque. Since CSS bg identical, no flash.

Reticle:
```js
function drawReticle(t){
  const x=S.src.x, y=S.src.y;
  const r = dragging ? 11 : 8.5;
  ctx.strokeStyle = getComputedStyle? — no; keep accent string cached: ACC var value cached in JS var `accCss`. Update on setAccent.
  ctx.globalAlpha = 0.9;
  ctx.lineWidth = 1;
  ctx.beginPath(); ctx.arc(x,y,r,0,6.2832); ctx.stroke();
  // ticks
  ctx.beginPath();
  for(let i=0;i<4;i++){
    const a = i*Math.PI/2;
    ctx.moveTo(x+Math.cos(a)*(r+2), y+Math.sin(a)*(r+2));
    ctx.lineTo(x+Math.cos(a)*(r+7), y+Math.sin(a)*(r+7));
  }
  ctx.stroke();
  // hairline cross
  ctx.globalAlpha = 0.3;
  ctx.beginPath();
  ctx.moveTo(x-16,y); ctx.lineTo(x- r-8, y);
  ctx.moveTo(x+r+8,y); ctx.lineTo(x+16, y);
  ...
```
Hmm simpler: just two short lines left/right and up/down between r+8 and 16? That's what ticks do... skip crosshair, ticks suffice. Center dot:
```js
  ctx.globalAlpha = 0.55 + 0.45*Math.sin(t*7);
  ctx.fillStyle = accCss;
  ctx.beginPath(); ctx.arc(x,y,1.8,0,6.2832); ctx.fill();
  ctx.globalAlpha = 1;
  // label
  ctx.font = '9px ' + MONO;  // careful: canvas font with fallback list ok: '9px "SF Mono", Menlo, monospace'
  ctx.fillStyle = 'rgba(233,226,212,0.5)';
  ctx.fillText('SOURCE', x + 16, y - 12);
```
fillStyle set before dot; label uses dim. Order fine.

drawSpark:
```js
const sctx = spark.getContext('2d');
function drawSpark(){
  const w = spark.width, h = spark.height; // device px
  sctx.clearRect(0,0,w,h);
  // 60fps reference line
  const y60 = h - (60/120)*(h-2) - 1;
  sctx.strokeStyle = 'rgba(233,226,212,0.12)';
  sctx.beginPath(); sctx.moveTo(0, y60); sctx.lineTo(w, y60); sctx.stroke();
  sctx.strokeStyle = accCss;
  sctx.lineWidth = Math.max(1, dpr);
  sctx.beginPath();
  for(let i=0;i<fpsHist.length;i++){
    const v = fpsHist[(fpsIdx+i)%fpsHist.length];
    const x = (i/(fpsHist.length-1))*w;
    const y = h - 1 - (Math.min(v,120)/120)*(h-3);
    i? sctx.lineTo(x,y) : sctx.moveTo(x,y);
  }
  sctx.stroke();
}
```
Set spark canvas width/height in resize: `spark.width=Math.round(64*dpr); spark.height=Math.round(20*dpr);` and sctx.setTransform(dpr,0,0,dpr,0,0) then use CSS-px coords 64×20. Adjust drawSpark accordingly (w=64,h=20).

DOM updates throttled:
```js
let uiT = 0;
in frame: uiT += dt; if(uiT > 0.25){ uiT = 0; 
  fpsVal.textContent = Math.round(fpsEma);
  fpsVal.classList.toggle('low', fpsEma < 30);
  cntVal.textContent = parts.length.toLocaleString('en-US');
  srcInfo.textContent = `SRC ${Math.round(S.src.x)} · ${Math.round(S.src.y)}`;
}
```
toLocaleString fine.

Pointer:
```js
let dragging = false, overSrc = false;
function pt(e){ const r = canvas.getBoundingClientRect(); return {x:e.clientX-r.left, y:e.clientY-r.top}; }
canvas.addEventListener('pointerdown', e => {
  const p = pt(e);
  const d = Math.hypot(p.x-S.src.x, p.y-S.src.y);
  if(d < 18){ dragging = true; canvas.setPointerCapture(e.pointerId); canvas.style.cursor='grabbing'; }
  else { for(let i=0;i<42;i++) spawn(p.x,p.y,true); }
});
window.addEventListener('pointermove', e => {
  const p = pt(e);
  if(dragging){ S.src.x = clamp(p.x,14,W-14); S.src.y = clamp(p.y,14,H-14); }
  else {
    const d = Math.hypot(p.x-S.src.x,p.y-S.src.y);
    const over = d < 18;
    if(over !== overSrc){ overSrc = over; canvas.style.cursor = over? 'grab':'crosshair'; }
  }
});
window.addEventListener('pointerup', ()=>{ if(dragging){dragging=false; canvas.style.cursor = overSrc?'grab':'crosshair';} });
```
pointermove on window covers capture; using canvas with capture also fine. If pointer leaves canvas, pt gives coords outside — clamped. OK. Also pointermove when pointer outside canvas entirely — hit test gives weird cursor sets on window... guard: only if e.target === canvas or dragging. Cursor style on canvas only affects over canvas anyway. Keep as is but cheap.

Controls wiring:

```js
function bindRange(id, key, valEl, fmt){
  const el = document.getElementById(id);
  const set = () => {
    S[key] = parseFloat(el.value);
    valEl.textContent = fmt(S[key]);
    const p = (el.value - el.min)/(el.max - el.min)*100;
    el.style.setProperty('--p', p + '%');
  };
  el.addEventListener('input', set);
  set();
}
bindRange('rate','rate',vRate, v=>Math.round(v));
bindRange('speed','speed',vSpeed, v=>Math.round(v));
bindRange('life','life',vLife, v=>v.toFixed(1));
```
Wait key names: S.rate etc. ids: rate, speed, life.

Color:
```js
const colorPick = ..., swatch = ..., hex = ...;
function applyColor(c){
  S.color = c;
  swatch.style.setProperty('--pick', c);  // or style.background
  hex.textContent = c.toUpperCase();
  buildSprite(c);
  setAccent(c);
  // presets active state
  document.querySelectorAll('.preset').forEach(b => b.classList.toggle('on', b.dataset.c === c.toLowerCase()));
}
colorPick.addEventListener('input', ()=> applyColor(colorPick.value));
```
Presets built:
```js
const PRESETS = ['#ffb454','#ff5c38','#ffe08a','#8de0b8','#7cc9ff','#f2ede2'];
```
Six dots. Hmm #7cc9ff is light blue — as a particle preset that's user content, acceptable. Build buttons with dataset.c, style background via inline style. Click → colorPick.value = c; applyColor(c).

Gravity:
```js
const gravBtn = ...;
function setGrav(on){
  S.gravity = on;
  gravBtn.setAttribute('aria-checked', String(on));
  gravState.textContent = on ? 'ON' : 'OFF';
  gravMeta.textContent = on ? 'g = 520 px/s² · downward' : 'g = 0 · free float';
  gravMeta.classList.toggle('off', !on);
}
gravBtn.addEventListener('click', ()=>{ setGrav(!S.gravity); gravBtn.blur(); });
window.addEventListener('keydown', e=>{
  if(e.code==='Space' && !e.repeat){
    const t = e.target.tagName;
    if(t==='INPUT' || t==='BUTTON') return;
    e.preventDefault(); setGrav(!S.gravity);
  }
});
```
Blur after click so space works globally. But if user clicked slider (range input focused), space does nothing — that's fine; arrows still adjust range.

Note: I blur the switch button; keyboard users tabbing: button reachable, Enter/Space triggers click natively — but our global handler skips BUTTON targets so no double-fire; after native activation focus remains and space keeps working on the button itself. Good, but then global space won't fire while focused — consistent enough.

Init order: setGrav(true) default state matches markup aria-checked="true" — call anyway. applyColor(default). resize(); requestAnimationFrame(frame). Also observe resize.

Mono font string for canvas: `const FONT = '"SF Mono","Cascadia Code",Menlo,Consolas,monospace'; ctx.font = '9px ' + FONT;` — canvas accepts comma lists fine.

Also set `letterSpacing` on canvas? ctx.letterSpacing = '1px' supported in Chrome; guard with try. Skip — fine without.

One more consideration — the fade fill `rgba(13,12,10,0.42)` vs CSS var bg #0d0c0a = rgb(13,12,10). Match. Good.

MAX cap: if parts.length >= MAX skip spawn — with rate 600 & life 6 & gravity off, particles fly off screen quickly; cap 4500 might hit with long lifetime + no gravity + off-screen kill helps (they leave upward within ~2s at speed ≥... they get killed when y < -160). With drag, slow ones linger. Cap fine; also visual saturation is natural.

Perf: drawImage count up to ~4500 — ok on desktop. Fine.

Also `cntVal` — id.

Hint indices: `<span><b>01</b>DRAG THE SOURCE TO MOVE</span>` etc.

Let me also double check the `--p` gradient hard stop: `linear-gradient(90deg, var(--acc) var(--p), var(--line-strong) var(--p))` — needs both stops; with only two color stops sharing position it's a hard edge. Yes valid.

But wait: CSS custom property with `%` set inline via el.style.setProperty works, and used in pseudo-element track (inherited from input). Yes, pseudo inherits custom props from originating element. Good. Firefox uses range-progress instead — no need for --p there.

Edge: `input[type=range]` height 22px — thumb margin-top for webkit: (2-16)/2 = -7. ✓.

Rail overflow-y auto with margin-top:auto footer — works in flex column.

Header responsiveness: at narrow widths stats might collide with brand — allow header wrap? Add `flex-wrap:wrap` + row-gap. Fine.

Let me also handle `document.hidden` visibility: rAF pauses automatically; on resume dt clamped 0.05 — good, and emitAcc reset if n>60.

Sparkline: on hidden→resume, dt clamp prevents garbage.

Double-check accent pip: `.pip` — background var(--acc) square. When accent changes, pip follows. Nice cohesive touch: whole chrome hue follows particle color.

Now, is there any "glow" violation? The canvas additive glow is the medium itself (particles), earned. UI chrome has no glows/shadows. Good. No gradients except the functional slider fill (hard stop) — and the particle sprite radial gradient (that's rendering, not decoration). Fonts: mono stack, deliberate. No emoji. All controls wired. FPS counter ✓. Auto-start ✓. Fade ✓. Color picker ✓. Gravity toggle ✓. Sliders ✓. Single file ✓. No external anything ✓.

One more polish: `user-select:none` on UI to avoid text selection during drags; `-webkit-tap-highlight-color: transparent`.

Also initial `#fpsVal` text '—' replaced quickly.

Sparkline id conflicts: I used variable names spark etc.

Let me now also handle the case where user drags slider thumb then presses space — target is INPUT → skipped. Good.

Write srcinfo: also show current rate? Just SRC coords.

Let me finalize markup ids: vRate, vSpeed, vLife, rate, speed, life, colorPick, swatch, hex, presets, gravBtn, gravState, gravMeta, fpsVal, cntVal, spark, view, srcInfo.

Val elements: `<span class="val"><b id="vRate">160</b><i>/s</i></span>`.

For speed unit "px/s", life "s".

Preset buttons need type="button" (no form anyway) and aria-label with color name? Add title attr.

Now writing final CSS polish numbers:

- header 54px.
- `.sval` 21px.

Check `.stat` alignment right — brand left. Good contrast hierarchy: FPS in accent color pops.

Rail h2 margin? gap covers.

Media query mobile: also header sub hide.

Let me write everything out now carefully, ensuring valid JS (no stray refs). Also define clamp helper.

Potential issue: `spark` canvas CSS width/height 64/20 but attribute set in resize with dpr; initial attribute default 300×150 until resize() runs at init — fine since resize called immediately.

ResizeObserver fallback: also `window.addEventListener('resize', resize)`.

srcInit variable declare.

Also on resize, trails fine.

drawReticle uses accCss — set in setAccent: `accCss = ...` also store accSoftCss maybe not needed.

Also draw a subtle ring "burst flash" on click? The burst itself is feedback enough.

Font for hex/val: default 12px body.

Final check of the `input[type=color]` default value `#ffb454` and S.color default same; applyColor called on init → builds sprite before first frame. rAF starts after. Also ensure buildSprite called before first draw — yes in init.

Also `parts` reuses plain objects; ok.

Kill margin when gravity off & speed high: y < -160 kills — they're gone quickly; lifetime slider up to 6s with cap fine.

Count formatting `toLocaleString('en-US')`.

One subtle thing: `fpsEma += (inst-fpsEma)*0.08`.

Also cap displayed hist value ≤120.

Sparkline ref line at 60fps: y = h*(1 - 60/120) = h/2 → 10px line in 20px canvas — half line. good.

`sparkline stroke color = accCss`.

Also add `aria-hidden` on decorative corners.

Now write the final file. I'll be careful with CSS/JS syntax. Also include brief explanation after the code block.

Let me also double check `input[type=range]` cursor: ew-resize on whole input; thumb same.

Also disable text selection on rail: `.rail, header {user-select:none}` but hex text maybe selectable? Keep none for cleanliness.

Also `.preset` uses CSS var `--c`: set inline `style="--c:#ffb454"` and CSS `background:var(--c)`.

The `.swatch` background uses `var(--pick)` set on wrapper? I set swatch.style.background directly — simpler: `swatch.style.background = c`.

Small detail: inner bevel `.swatch::after` inset border dark — okay.

Rail width 264 might be tight with "GRAVITY" + state + switch: 10px lab (~60px) + state (~24) + switch 38 + gaps 20 → ~150 fine.

Media query small: keep.

Write it.

Also — scrollbar: `#rail::-webkit-scrollbar{width:0}` or thin. Use `scrollbar-width:none`? Rail content ~ fits 600px height; allow overflow hidden? If window short, overflow-y auto with `scrollbar-width:thin`.

Final: `main{min-height:0}` needed for grid child overflow. body overflow hidden already.

Compose the code fully now.

Also I should double check gravity default ON and requirement "button to toggle gravity on/off" — a switch-button is fine ("button"). role=switch on <button> good.

Explanation after code: brief — architecture, physics, sprite caching, accent derivation, interactions.

Also `e.preventDefault()` on pointerdown for canvas? To prevent text selection drag — canvas has user-select none anyway; also prevents touch scroll: add `touch-action:none` on canvas — important for mobile dragging. Add CSS `#view{touch-action:none}`.

Also for keydown space when target is range — arrows work; space ignored; good.

Write out:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Particle Bench · Canvas Emitter</title>
<style>
:root{
  --bg:#0d0c0a;
  --panel:#12100c;
  --line:rgba(236,227,208,.08);
  --line2:rgba(236,227,208,.17);
  --txt:#e9e2d4;
  --dim:#8a8272;
  --faint:#5b5443;
  --acc:hsl(36,80%,64%);
  --acc-soft:hsla(36,80%,64%,.45);
  --acc-faint:hsla(36,80%,64%,.13);
  --warn:#e0524f;
  --mono:"SF Mono","Cascadia Code","JetBrains Mono",Menlo,Consolas,"DejaVu Sans Mono","Liberation Mono",monospace;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{
  background:var(--bg);color:var(--txt);
  font-family:var(--mono);font-size:12px;
  display:grid;grid-template-rows:54px 1fr;
  overflow:hidden;-webkit-tap-highlight-color:transparent;
}
button,input{font-family:inherit}
header{
  display:flex;align-items:center;justify-content:space-between;
  padding:0 20px;border-bottom:1px solid var(--line);background:var(--panel);
  user-select:none;gap:12px;flex-wrap:wrap;
}
.brand{display:flex;align-items:center;gap:10px}
.pip{width:7px;height:7px;background:var(--acc);flex:none}
.name{font-size:12px;font-weight:700;letter-spacing:.24em}
.sub{font-size:10px;color:var(--faint);letter-spacing:.08em}
.stats{display:flex;align-items:center;gap:18px}
.vdiv{width:1px;height:26px;background:var(--line2)}
.stat{display:flex;flex-direction:column;align-items:flex-end;gap:3px}
.slab{font-size:9px;letter-spacing:.22em;color:var(--dim)}
.srow{display:flex;align-items:center;gap:9px}
.sval{font-size:21px;line-height:1;font-variant-numeric:tabular-nums;min-width:2ch;text-align:right}
#fpsVal{color:var(--acc)}
#fpsVal.low{color:var(--warn)}
#spark{width:64px;height:20px}

main{display:grid;grid-template-columns:266px 1fr;min-height:0}
#rail{
  border-right:1px solid var(--line);background:var(--panel);
  padding:20px 18px 14px;display:flex;flex-direction:column;gap:24px;
  overflow-y:auto;user-select:none;scrollbar-width:thin;scrollbar-color:#2a251c transparent;
}
#rail::-webkit-scrollbar{width:4px}
#rail::-webkit-scrollbar-thumb{background:#2a251c}
.grp{display:flex;flex-direction:column;gap:14px;flex:none}
.grp h2{
  font-size:9px;font-weight:600;letter-spacing:.26em;color:var(--dim);
  display:flex;align-items:center;gap:8px;
}
.grp h2::before{content:"";width:14px;height:1px;background:var(--acc-soft)}
.ctl{display:flex;flex-direction:column;gap:5px}
.crow{display:flex;justify-content:space-between;align-items:baseline}
.lab{font-size:10px;letter-spacing:.16em;color:var(--dim)}
.val{font-size:12px;font-variant-numeric:tabular-nums}
.val b{font-weight:600;color:var(--acc)}
.val i{font-style:normal;color:var(--faint);font-size:10px;margin-left:3px}

input[type=range]{
  -webkit-appearance:none;appearance:none;
  width:100%;height:22px;background:transparent;cursor:ew-resize;--p:50%;
}
input[type=range]:focus{outline:none}
input[type=range]:focus-visible{outline:1px dashed var(--acc-soft);outline-offset:3px}
input[type=range]::-webkit-slider-runnable-track{
  height:2px;border-radius:1px;
  background:linear-gradient(90deg,var(--acc) var(--p),var(--line2) var(--p));
}
input[type=range]::-webkit-slider-thumb{
  -webkit-appearance:none;appearance:none;
  width:5px;height:16px;border-radius:1px;border:none;
  background:var(--acc);margin-top:-7px;transition:width .12s ease;
}
input[type=range]:hover::-webkit-slider-thumb,
input[type=range]:active::-webkit-slider-thumb{width:9px}
input[type=range]::-moz-range-track{height:2px;background:var(--line2);border-radius:1px}
input[type=range]::-moz-range-progress{height:2px;background:var(--acc);border-radius:1px}
input[type=range]::-moz-range-thumb{width:5px;height:16px;border:none;border-radius:1px;background:var(--acc);transition:width .12s ease}
input[type=range]:hover::-moz-range-thumb{width:9px}

.colorrow{display:flex;align-items:center;gap:12px}
.swatch-wrap{position:relative;width:34px;height:34px;cursor:pointer;flex:none;display:block}
.swatch-wrap input{position:absolute;inset:0;opacity:0;cursor:pointer}
.swatch{
  position:absolute;inset:0;border-radius:3px;border:1px solid var(--line2);
  background:var(--pick,#ffb454);pointer-events:none;
}
.swatch::after{content:"";position:absolute;inset:3px;border-radius:2px;border:1px solid rgba(0,0,0,.3)}
.swatch-wrap:has(input:focus-visible) .swatch{outline:1px dashed var(--acc-soft);outline-offset:3px}
.hex{font-size:12px;letter-spacing:.08em;color:var(--txt)}
.presets{display:flex;gap:9px}
.preset{
  width:15px;height:15px;border-radius:50%;border:1px solid rgba(0,0,0,.45);
  background:var(--c);cursor:pointer;position:relative;padding:0;
  transition:transform .12s ease;flex:none;
}
.preset:hover{transform:scale(1.3)}
.preset.on::after{content:"";position:absolute;inset:-4px;border-radius:50%;border:1px solid var(--acc-soft)}

.forcerow{
  display:flex;align-items:center;gap:12px;width:100%;
  background:none;border:none;color:inherit;cursor:pointer;
  padding:3px 0;text-align:left;
}
.forcerow .lab{flex:1}
.state{font-size:10px;letter-spacing:.16em;color:var(--faint);min-width:3ch;text-align:right}
.switch{
  width:38px;height:20px;flex:none;border-radius:11px;position:relative;
  border:1px solid var(--line2);background:rgba(236,227,208,.04);
  transition:background .18s ease,border-color .18s ease;
}
.knob{
  position:absolute;top:3px;left:3px;width:12px;height:12px;border-radius:50%;
  background:var(--dim);transition:transform .18s ease,background .18s ease;
}
.forcerow:hover .switch{border-color:rgba(236,227,208,.3)}
.forcerow[aria-checked="true"] .switch{background:var(--acc-faint);border-color:var(--acc-soft)}
.forcerow[aria-checked="true"] .knob{transform:translateX(18px);background:var(--acc)}
```
Wait recompute translate: inner width = 38 - 2 = 36; knob 12; left 3; to right-align with 3px margin: translate = 36 - 3 - 12 - 3 = 18. ✓ (I earlier said 20 with different margin; 18 correct.)

```css
.forcerow[aria-checked="true"] .state{color:var(--acc)}
.forcerow:focus-visible{outline:1px dashed var(--acc-soft);outline-offset:3px}
.meta{font-size:10px;color:var(--faint);letter-spacing:.08em}
.meta.off{color:#3f3a2f}
```
Hmm .off color darker than faint — use opacity instead: `.meta.off{opacity:.6}`.

```css
.railfoot{
  margin-top:auto;padding-top:16px;border-top:1px solid var(--line);
  display:flex;flex-direction:column;gap:8px;flex:none;
}
.railfoot span{font-size:9px;letter-spacing:.14em;color:var(--faint)}
.railfoot b{font-weight:400;color:var(--dim);margin-right:9px}

#stage{position:relative;min-width:0;min-height:0;overflow:hidden}
#view{position:absolute;inset:0;width:100%;height:100%;display:block;cursor:crosshair;touch-action:none}
.corner{position:absolute;width:12px;height:12px;pointer-events:none;z-index:2}
.corner.tl{top:10px;left:10px;border-top:1px solid var(--line2);border-left:1px solid var(--line2)}
.corner.tr{top:10px;right:10px;border-top:1px solid var(--line2);border-right:1px solid var(--line2)}
.corner.bl{bottom:10px;left:10px;border-bottom:1px solid var(--line2);border-left:1px solid var(--line2)}
.corner.br{bottom:10px;right:10px;border-bottom:1px solid var(--line2);border-right:1px solid var(--line2)}
.srcinfo{
  position:absolute;left:30px;bottom:18px;pointer-events:none;z-index:2;
  font-size:9px;letter-spacing:.18em;color:var(--faint);font-variant-numeric:tabular-nums;
}
@media (max-width:760px){
  main{grid-template-columns:1fr;grid-template-rows:1fr auto}
  #rail{border-right:none;border-top:1px solid var(--line);flex-direction:row;flex-wrap:wrap;gap:18px;max-height:190px}
  .grp{flex:1;min-width:150px;gap:10px}
  .railfoot,.sub{display:none}
  .srcinfo{bottom:auto;top:30px}
}
</style>
</head>
```

Body markup:

```html
<body>
<header>
  <div class="brand">
    <span class="pip"></span>
    <span class="name">PARTICLE BENCH</span>
    <span class="sub">/ canvas emitter console</span>
  </div>
  <div class="stats">
    <div class="stat">
      <span class="slab">FPS</span>
      <div class="srow">
        <span class="sval" id="fpsVal">—</span>
        <canvas id="spark" width="64" height="20"></canvas>
      </div>
    </div>
    <div class="vdiv"></div>
    <div class="stat">
      <span class="slab">PARTICLES</span>
      <div class="srow"><span class="sval" id="cntVal">0</span></div>
    </div>
  </div>
</header>
<main>
  <aside id="rail">
    <section class="grp">
      <h2>EMISSION</h2>
      <div class="ctl">
        <div class="crow"><label class="lab" for="rate">RATE</label>
          <span class="val"><b id="vRate">160</b><i>/s</i></span></div>
        <input type="range" id="rate" min="10" max="600" step="5" value="160" aria-label="Emission rate">
      </div>
      <div class="ctl">
        <div class="crow"><label class="lab" for="speed">SPEED</label>
          <span class="val"><b id="vSpeed">260</b><i>px/s</i></span></div>
        <input type="range" id="speed" min="20" max="500" step="5" value="260" aria-label="Particle speed">
      </div>
      <div class="ctl">
        <div class="crow"><label class="lab" for="life">LIFETIME</label>
          <span class="val"><b id="vLife">2.4</b><i>s</i></span></div>
        <input type="range" id="life" min="0.4" max="6" step="0.1" value="2.4" aria-label="Particle lifetime">
      </div>
    </section>

    <section class="grp">
      <h2>COLOR</h2>
      <div class="colorrow">
        <label class="swatch-wrap">
          <input type="color" id="colorPick" value="#ffb454" aria-label="Particle color">
          <span class="swatch" id="swatch"></span>
        </label>
        <span class="hex" id="hex">#FFB454</span>
      </div>
      <div class="presets" id="presets"></div>
    </section>

    <section class="grp">
      <h2>FORCES</h2>
      <button class="forcerow" id="gravBtn" role="switch" aria-checked="true">
        <span class="lab">GRAVITY</span>
        <span class="state" id="gravState">ON</span>
        <span class="switch"><span class="knob"></span></span>
      </button>
      <div class="meta" id="gravMeta">g = 520 px/s² · downward</div>
    </section>

    <footer class="railfoot">
      <span><b>01</b>DRAG THE SOURCE TO MOVE IT</span>
      <span><b>02</b>CLICK THE CANVAS FOR A BURST</span>
      <span><b>03</b>SPACE TOGGLES GRAVITY</span>
    </footer>
  </aside>

  <div id="stage">
    <canvas id="view"></canvas>
    <i class="corner tl" aria-hidden="true"></i>
    <i class="corner tr" aria-hidden="true"></i>
    <i class="corner bl" aria-hidden="true"></i>
    <i class="corner br" aria-hidden="true"></i>
    <div class="srcinfo" id="srcInfo">SRC — · —</div>
  </div>
</main>
<script>
...
</script>
</body>
</html>
```

`px/s²` superscript char ² fine.

Now JS full:

```js
(() => {
'use strict';

const $ = id => document.getElementById(id);
const canvas = $('view'), stage = $('stage'), spark = $('spark');
const ctx = canvas.getContext('2d');
const sctx = spark.getContext('2d');
const fpsVal = $('fpsVal'), cntVal = $('cntVal'), srcInfo = $('srcInfo');
const gravBtn = $('gravBtn'), gravState = $('gravState'), gravMeta = $('gravMeta');
const colorPick = $('colorPick'), swatch = $('swatch'), hexEl = $('hex');

const FONT = '"SF Mono","Cascadia Code","JetBrains Mono",Menlo,Consolas,monospace';
const BG_FADE = 'rgba(13,12,10,0.42)';

const S = { rate:160, speed:260, life:2.4, gravity:true, g:520, src:{x:200,y:200} };
let accCss = 'hsl(36,80%,64%)';
let W = 0, H = 0, dpr = 1, srcInit = false;

/* ---------- color helpers ---------- */
const hexToRgb = h => { const n = parseInt(h.slice(1),16); return [(n>>16)&255,(n>>8)&255,n&255]; };
function rgbToHsl(r,g,b){
  r/=255; g/=255; b/=255;
  const mx=Math.max(r,g,b), mn=Math.min(r,g,b), l=(mx+mn)/2;
  if(mx===mn) return {h:36,s:0,l:l*100};
  const d=mx-mn, s=l>0.5? d/(2-mx-mn) : d/(mx+mn);
  let h;
  if(mx===r) h=(g-b)/d + (g<b?6:0);
  else if(mx===g) h=(b-r)/d + 2;
  else h=(r-g)/d + 4;
  return {h:h*60, s:s*100, l:l*100};
}
function setAccent(hex){
  let {h,s} = rgbToHsl(...hexToRgb(hex));
  if(s < 8) h = 36;
  s = Math.min(85, Math.max(40, s));
  const H0 = Math.round(h), S0 = Math.round(s);
  accCss = `hsl(${H0},${S0}%,64%)`;
  const rs = document.documentElement.style;
  rs.setProperty('--acc', accCss);
  rs.setProperty('--acc-soft', `hsla(${H0},${S0}%,64%,0.45)`);
  rs.setProperty('--acc-faint', `hsla(${H0},${S0}%,64%,0.13)`);
}

/* ---------- particle sprite (cached, rebuilt on color change) ---------- */
const SPR = 48;
const sprite = document.createElement('canvas');
sprite.width = sprite.height = SPR;
function buildSprite(hex){
  const c = sprite.getContext('2d');
  c.clearRect(0,0,SPR,SPR);
  const {h,s,l} = rgbToHsl(...hexToRgb(hex));
  const core = `hsla(${h},${s}%,${Math.min(97, l + (97-l)*0.8)}%,1)`;
  const mid  = `hsla(${h},${s}%,${l}%,0.9)`;
  const edge = `hsla(${h},${s}%,${l}%,0)`;
  const g = c.createRadialGradient(SPR/2,SPR/2,0,SPR/2,SPR/2,SPR/2);
  g.addColorStop(0,core); g.addColorStop(0.22,mid); g.addColorStop(1,edge);
  c.fillStyle = g;
  c.fillRect(0,0,SPR,SPR);
}
```
Hmm if s is 0 (white particle) hsla(36,0%,...) = gray — fine.

```js
/* ---------- particles ---------- */
const parts = [];
const MAX = 4500;
const TAU = Math.PI*2;
const clamp = (v,a,b) => v<a?a:(v>b?b:v);

function spawn(x, y, burst){
  if(parts.length >= MAX) return;
  const a = burst ? Math.random()*TAU
                  : -Math.PI/2 + (Math.random()-0.5)*1.15;
  const mul = burst ? 0.45+Math.random()*0.85 : 0.55+Math.random()*0.6;
  const sp = S.speed*mul;
  parts.push({
    x, y, vx:Math.cos(a)*sp, vy:Math.sin(a)*sp,
    life: S.life*(burst ? 0.45+Math.random()*0.5 : 0.7+Math.random()*0.55),
    age:0, size:(burst?6:7)+Math.random()*7, ph:Math.random()*TAU
  });
}

/* ---------- sizing ---------- */
function resize(){
  dpr = Math.min(2, window.devicePixelRatio||1);
  const r = stage.getBoundingClientRect();
  W = Math.max(1, Math.round(r.width));
  H = Math.max(1, Math.round(r.height));
  canvas.width = Math.round(W*dpr);
  canvas.height = Math.round(H*dpr);
  ctx.setTransform(dpr,0,0,dpr,0,0);
  if(!srcInit){ S.src.x = W*0.5; S.src.y = H*0.6; srcInit = true; }
  S.src.x = clamp(S.src.x, 14, W-14);
  S.src.y = clamp(S.src.y, 14, H-14);
  spark.width = Math.round(64*dpr);
  spark.height = Math.round(20*dpr);
  sctx.setTransform(dpr,0,0,dpr,0,0);
}

/* ---------- reticle ---------- */
let dragging = false;
function drawReticle(t){
  const x=S.src.x, y=S.src.y, r = dragging ? 11.5 : 8.5;
  ctx.globalCompositeOperation = 'source-over';
  ctx.strokeStyle = accCss;
  ctx.lineWidth = 1;
  ctx.globalAlpha = 0.95;
  ctx.beginPath(); ctx.arc(x,y,r,0,TAU); ctx.stroke();
  ctx.beginPath();
  for(let i=0;i<4;i++){
    const a = i*Math.PI/2, c=Math.cos(a), s2=Math.sin(a);
    ctx.moveTo(x+c*(r+2.5), y+s2*(r+2.5));
    ctx.lineTo(x+c*(r+7.5), y+s2*(r+7.5));
  }
  ctx.stroke();
  ctx.globalAlpha = 0.55+0.45*Math.sin(t*7);
  ctx.fillStyle = accCss;
  ctx.beginPath(); ctx.arc(x,y,1.8,0,TAU); ctx.fill();
  ctx.globalAlpha = 1;
  ctx.font = '9px ' + FONT;
  ctx.fillStyle = 'rgba(233,226,212,0.45)';
  ctx.fillText('SOURCE', x+17, y-13);
}
```
ctx.globalCompositeOperation set inside drawReticle — I set it back before calling. Fine either way.

fps history + spark draw:

```js
const fpsHist = new Float32Array(56);
let fpsIdx = 0, fpsEma = 60;
function drawSpark(){
  const w=64, h=20;
  sctx.clearRect(0,0,w,h);
  sctx.strokeStyle = 'rgba(233,226,212,0.13)';
  sctx.lineWidth = 1;
  sctx.beginPath(); sctx.moveTo(0,h/2+0.5); sctx.lineTo(w,h/2+0.5); sctx.stroke();
  sctx.strokeStyle = accCss;
  sctx.beginPath();
  for(let i=0;i<fpsHist.length;i++){
    const v = fpsHist[(fpsIdx+i)%fpsHist.length];
    const x = (i/(fpsHist.length-1))*(w-1)+0.5;
    const y = h-1.5 - clamp(v,0,120)/120*(h-4);
    i ? sctx.lineTo(x,y) : sctx.moveTo(x,y);
  }
  sctx.stroke();
}
```

Main loop:

```js
let last = performance.now(), emitAcc = 0, uiT = 1;
function frame(now){
  requestAnimationFrame(frame);
  let dt = (now-last)/1000; last = now;
  if(dt <= 0) return;
  if(dt > 0.05) dt = 0.05;

  const inst = 1/dt;
  fpsEma += (inst - fpsEma)*0.08;
  fpsHist[fpsIdx] = inst; fpsIdx = (fpsIdx+1)%fpsHist.length;

  /* emit */
  emitAcc += S.rate*dt;
  let n = Math.floor(emitAcc);
  if(n > 60){ n = 60; emitAcc = 0; } else emitAcc -= n;
  for(let i=0;i<n;i++) spawn(S.src.x, S.src.y, false);

  /* physics */
  const g = S.gravity ? S.g : 0;
  const dr = Math.exp(-0.1*dt);
  const t = now/1000;
  for(let i=parts.length-1;i>=0;i--){
    const p = parts[i];
    p.age += dt;
    if(p.age >= p.life){ parts[i]=parts[parts.length-1]; parts.pop(); continue; }
    p.vx = p.vx*dr + Math.sin(t*4.2+p.ph)*15*dt;
    p.vy = p.vy*dr + g*dt;
    p.x += p.vx*dt; p.y += p.vy*dt;
    if(p.x<-90||p.x>W+90||p.y>H+90||p.y<-170){
      parts[i]=parts[parts.length-1]; parts.pop();
    }
  }

  /* draw: fade pass (trails) + additive particles */
  ctx.globalCompositeOperation = 'source-over';
  ctx.fillStyle = BG_FADE;
  ctx.fillRect(0,0,W,H);
  ctx.globalCompositeOperation = 'lighter';
  for(let i=0;i<parts.length;i++){
    const p = parts[i], k = p.age/p.life;
    const a = Math.pow(1-k,1.6);
    if(a < 0.02) continue;
    const s = p.size*(1-0.35*k);
    ctx.globalAlpha = a;
    ctx.drawImage(sprite, p.x-s/2, p.y-s/2, s, s);
  }
  ctx.globalAlpha = 1;
  drawReticle(t);
  drawSpark();

  /* throttled DOM readouts */
  uiT += dt;
  if(uiT > 0.25){
    uiT = 0;
    fpsVal.textContent = String(Math.round(fpsEma));
    fpsVal.classList.toggle('low', fpsEma < 30);
    cntVal.textContent = parts.length.toLocaleString('en-US');
    srcInfo.textContent = 'SRC ' + Math.round(S.src.x) + ' · ' + Math.round(S.src.y);
  }
}
```

Pointer:

```js
let overSrc = false;
const evPt = e => {
  const r = canvas.getBoundingClientRect();
  return {x:e.clientX-r.left, y:e.clientY-r.top};
};
canvas.addEventListener('pointerdown', e => {
  const p = evPt(e);
  if(Math.hypot(p.x-S.src.x, p.y-S.src.y) < 18){
    dragging = true;
    canvas.setPointerCapture(e.pointerId);
    canvas.style.cursor = 'grabbing';
  } else {
    for(let i=0;i<42;i++) spawn(p.x, p.y, true);
  }
});
canvas.addEventListener('pointermove', e => {
  const p = evPt(e);
  if(dragging){
    S.src.x = clamp(p.x, 14, W-14);
    S.src.y = clamp(p.y, 14, H-14);
  } else {
    const over = Math.hypot(p.x-S.src.x, p.y-S.src.y) < 18;
    if(over !== overSrc){
      overSrc = over;
      canvas.style.cursor = over ? 'grab' : 'crosshair';
    }
  }
});
window.addEventListener('pointerup', () => {
  if(dragging){ dragging = false; canvas.style.cursor = overSrc ? 'grab' : 'crosshair'; }
});
```
With pointer capture, pointermove goes to canvas even outside — good.

Controls:

```js
function bindRange(id, key, out, fmt){
  const el = $(id), val = $(out);
  const apply = () => {
    S[key] = parseFloat(el.value);
    val.textContent = fmt(S[key]);
    el.style.setProperty('--p', ((el.value-el.min)/(el.max-el.min)*100)+'%');
  };
  el.addEventListener('input', apply);
  apply();
}
bindRange('rate','rate','vRate', v=>String(Math.round(v)));
bindRange('speed','speed','vSpeed', v=>String(Math.round(v)));
bindRange('life','life','vLife', v=>v.toFixed(1));

function setGrav(on){
  S.gravity = on;
  gravBtn.setAttribute('aria-checked', String(on));
  gravState.textContent = on ? 'ON' : 'OFF';
  gravMeta.textContent = on ? 'g = 520 px/s² · downward' : 'g = 0 · free float';
  gravMeta.classList.toggle('off', !on);
}
gravBtn.addEventListener('click', () => { setGrav(!S.gravity); gravBtn.blur(); });
window.addEventListener('keydown', e => {
  if(e.code !== 'Space' || e.repeat) return;
  const tag = e.target.tagName;
  if(tag === 'INPUT' || tag === 'BUTTON') return;
  e.preventDefault();
  setGrav(!S.gravity);
});

/* color */
const PRESETS = ['#ffb454','#ff5c38','#ffe08a','#8de0b8','#7cc9ff','#f2ede2'];
const presetWrap = $('presets');
PRESETS.forEach(c => {
  const b = document.createElement('button');
  b.type = 'button';
  b.className = 'preset';
  b.style.setProperty('--c', c);
  b.dataset.c = c;
  b.setAttribute('aria-label', 'Use color ' + c);
  b.title = c.toUpperCase();
  b.addEventListener('click', () => { colorPick.value = c; applyColor(c); });
  presetWrap.appendChild(b);
});
function applyColor(c){
  S.color = c;   // (S.color not used elsewhere but kept for clarity)
  swatch.style.background = c;
  hexEl.textContent = c.toUpperCase();
  buildSprite(c);
  setAccent(c);
  presetWrap.querySelectorAll('.preset').forEach(b =>
    b.classList.toggle('on', b.dataset.c === c.toLowerCase()));
}
colorPick.addEventListener('input', () => applyColor(colorPick.value));
```

Init:

```js
const ro = new ResizeObserver(resize);
ro.observe(stage);
window.addEventListener('resize', resize);

resize();
setGrav(true);
applyColor('#ffb454');
requestAnimationFrame(frame);
})();
```

applyColor toggles preset 'on' for #ffb454 — matches first preset ✓.

S.color — I never read it; keep or drop. Drop to avoid dead code? Small; keep minimal: remove S.color. Actually harmless; but cleaner to remove. I'll remove.

Note: `.preset` background uses `var(--c)` — set. 

One concern: on `pointerdown` burst while clicking near corners/srcInfo — those have pointer-events:none ✓.

Another: `canvas.setPointerCapture` inside pointerdown try/catch not needed (valid pointerId).

Check `bindRange` uses el.min/el.max as strings — arithmetic coerces ✓. `(el.value-el.min)` numeric coercion via subtraction ✓.

fmt for life: v.toFixed(1) — S.life set from parseFloat ✓.

Gravity default true matches markup; setGrav(true) at init sets text consistently ✓.

Potential visual check: default color #ffb454 → h≈35,s=100 → accent hsl(35,80%,64%) — warm amber. Slider fills amber. 

Header FPS numeral amber; count warm white. 

I think it's solid. Also add `title` on canvas? no.

Also `aria-hidden` on spark canvas? It conveys info; give aria-label "frame time history"? Add role img aria-label. Minor; add.

Body font smoothing: `-webkit-font-smoothing:antialiased`.

Let me also double-check no emoji anywhere ✓; no alert ✓; no external resources ✓; single file ✓.

Also check: `swatch.style.background = c` — c like '#ffb454' ✓.

Meta viewport ✓.

Explanation paragraph after code: cover structure, physics (accumulator emission, semi-implicit Euler, drag, shimmer), cached radial-gradient sprite + additive blending + fade-rect trails, accent derivation from color, controls wiring, FPS EMA + sparkline, interactions (drag source, click burst, space). Keep concise.

One more check — the `lighter` composite over the fade-rect: because fade-rect leaves residual warm haze behind dense plumes, the "smoke" reads naturally. Good.

Also make sure the fade doesn't wipe sparkline — separate canvas ✓.

Edge: `dt<=0` return before updating last? last already set to now before check — ok.

When tab hidden then visible: rAF resumes; dt clamped 0.05; emitAcc might have accumulated rate*0.05 only (we clamp) ✓.

Write final answer.