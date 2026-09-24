Here's a single-file HTML code for your Halo smart glasses landing page, featuring inline SVG, scroll-driven animations, a sticky rotating showcase, and both dark and light sections.
```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#000000">
<title>Halo — Real-time translation glasses</title>
<script>document.documentElement.classList.add('js');</script>
<style>
/* ============ RESET / BASE ============ */
*,*::before,*::after{box-sizing:border-box}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{
  margin:0;
  background:#000;
  color:#f5f5f7;
  font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text","Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  -webkit-font-smoothing:antialiased;
  -moz-osx-font-smoothing:grayscale;
  line-height:1.4;
  overflow-x:hidden;
}
svg{display:block}
a{color:inherit}
::selection{background:#0a84ff;color:#fff}

:root{
  --blue:#0071e3;
  --blue-soft:#6ea8ff;
  --light-bg:#fbfbfd;
  --light-fg:#1d1d1f;
  --muted-light:#6e6e73;
  --muted-dark:#86868b;
  --ease:cubic-bezier(.22,1,.36,1);
}

/* ============ LAYOUT ============ */
.container{max-width:1120px;margin:0 auto;padding:0 24px}
.centered{text-align:center}
.section-pad{padding:150px 0}
.light-section{background:var(--light-bg);color:var(--light-fg)}
.dark-section{background:#000;color:#f5f5f7}
section{position:relative}
[id]{scroll-margin-top:70px}

/* ============ TYPE ============ */
.eyebrow{
  font-size:13px;letter-spacing:.22em;text-transform:uppercase;
  font-weight:600;color:var(--blue);margin:0 0 18px;
}
.eyebrow-dark{color:var(--blue-soft)}
.section-title{
  font-size:clamp(32px,5.2vw,60px);
  line-height:1.06;letter-spacing:-.025em;font-weight:600;
  margin:0 0 20px;
}
.section-sub{
  max-width:640px;margin:0 auto;
  color:var(--muted-light);font-size:clamp(17px,1.9vw,21px);line-height:1.5;
}
.lede{
  max-width:660px;margin:22px auto 0;
  color:var(--muted-dark);font-size:clamp(17px,1.9vw,21px);line-height:1.5;
}
.fineprint{color:#6e6e73;font-size:13px;margin:34px 0 0;letter-spacing:.01em}

/* ============ BUTTONS ============ */
.btn{
  display:inline-flex;align-items:center;justify-content:center;
  padding:14px 30px;border-radius:980px;
  font-size:16px;font-weight:500;text-decoration:none;letter-spacing:-.01em;
  transition:transform .4s var(--ease),background .4s var(--ease),color .4s var(--ease),box-shadow .4s var(--ease),opacity .4s var(--ease);
  will-change:transform;
}
.btn:hover{transform:translateY(-2px)}
.btn:active{transform:translateY(0) scale(.98)}
.btn-primary{background:#f5f5f7;color:#0a0a0a}
.btn-primary:hover{background:#fff;box-shadow:0 12px 30px -10px rgba(255,255,255,.4)}
.btn-ghost{color:#f5f5f7;border:1px solid rgba(255,255,255,.28)}
.btn-ghost:hover{background:rgba(255,255,255,.1);border-color:rgba(255,255,255,.5)}
.btn-dark{background:#1d1d1f;color:#fff}
.btn-dark:hover{background:#000;box-shadow:0 16px 34px -14px rgba(0,0,0,.5)}
.btn-light{background:#f5f5f7;color:#0a0a0a}
.btn-light:hover{background:#fff}

.cta-row{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;margin-top:36px}

/* ============ NAV ============ */
.nav{
  position:fixed;top:0;left:0;right:0;height:54px;z-index:100;
  display:flex;align-items:center;
  backdrop-filter:saturate(180%) blur(22px);
  -webkit-backdrop-filter:saturate(180%) blur(22px);
  background:rgba(12,12,14,.55);
  border-bottom:1px solid rgba(255,255,255,.08);
  color:#f5f5f7;
  transition:background .55s var(--ease),border-color .55s var(--ease),color .55s var(--ease);
}
.nav.nav-light{
  background:rgba(251,251,253,.72);
  border-bottom-color:rgba(0,0,0,.09);
  color:#1d1d1f;
}
.nav-inner{
  width:100%;max-width:1120px;margin:0 auto;padding:0 24px;
  display:flex;align-items:center;justify-content:space-between;gap:24px;
}
.nav-logo{
  font-size:17px;font-weight:600;letter-spacing:-.02em;text-decoration:none;
}
.nav-links{display:flex;gap:32px;font-size:13.5px}
.nav-links a{
  text-decoration:none;opacity:.72;transition:opacity .3s var(--ease);
}
.nav-links a:hover{opacity:1}
.nav-cta{
  font-size:13px;text-decoration:none;padding:7px 16px;border-radius:980px;
  background:currentColor;position:relative;transition:opacity .3s var(--ease);
}
.nav-cta span{position:relative;mix-blend-mode:difference;color:#fff}
.nav-light .nav-cta span{mix-blend-mode:normal;color:#1d1d1f}
.nav-cta:hover{opacity:.82}
@media(max-width:760px){.nav-links{display:none}}

/* ============ HERO ============ */
.hero{
  min-height:100vh;min-height:100svh;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  text-align:center;
  padding:132px 24px 90px;
  position:relative;overflow:hidden;
  background:#000;
}
.hero-glow{
  position:absolute;left:-10%;right:-10%;top:-25%;height:130%;
  pointer-events:none;
  background:
    radial-gradient(48% 42% at 50% 62%, rgba(48,110,255,.30), transparent 72%),
    radial-gradient(40% 38% at 20% 28%, rgba(150,80,255,.20), transparent 72%),
    radial-gradient(38% 38% at 82% 24%, rgba(0,190,255,.16), transparent 72%);
  filter:blur(6px);
  opacity:0;
  animation:glowIn 2.2s var(--ease) .1s forwards;
}
@keyframes glowIn{to{opacity:1}}

.hero h1{
  font-size:clamp(38px,7.2vw,84px);
  line-height:1.03;
  letter-spacing:-.035em;
  font-weight:600;
  margin:16px 0 0;
  background:linear-gradient(180deg,#ffffff 30%,#a4a4ad 100%);
  -webkit-background-clip:text;background-clip:text;color:transparent;
}
.hero-product{
  margin-top:58px;
  width:min(88vw,640px,100vh);
  position:relative;
}
.hero-product .glasses{
  width:100%;height:auto;
  filter:drop-shadow(0 36px 70px rgba(0,90,255,.34));
  animation:float 7.5s ease-in-out infinite;
}
@keyframes float{
  0%,100%{transform:translateY(0)}
  50%{transform:translateY(-14px)}
}
.scroll-hint{
  position:absolute;bottom:32px;left:50%;transform:translateX(-50%);
  display:flex;flex-direction:column;align-items:center;gap:10px;
  font-size:11px;letter-spacing:.24em;text-transform:uppercase;color:#6e6e73;
}
.scroll-hint i{
  display:block;width:1px;height:36px;
  background:linear-gradient(180deg,rgba(255,255,255,.5),rgba(255,255,255,0));
  animation:hintPulse 2.6s ease-in-out infinite;
}
@keyframes hintPulse{
  0%,100%{opacity:.25;transform:scaleY(.6)}
  50%{opacity:1;transform:scaleY(1)}
}
@media(max-width:600px){.scroll-hint{display:none}}

/* ============ GLASSES SVG ============ */
.sheen{animation:sheen 5.6s cubic-bezier(.45,0,.55,1) infinite}
@keyframes sheen{
  0%{transform:translateX(0) skewX(-16deg)}
  55%{transform:translateX(620px) skewX(-16deg)}
  100%{transform:translateX(620px) skewX(-16deg)}
}
.sensor{animation:sensorPulse 3.4s ease-in-out infinite}
@keyframes sensorPulse{
  0%,100%{opacity:.45}
  50%{opacity:1}
}

/* ============ STICKY SHOWCASE ============ */
.sticky-section{
  height:320vh;
  background:linear-gradient(180deg,#000 0%,#05060b 38%,#05060b 62%,#000 100%);
  color:#f5f5f7;
}
.sticky-stage{
  position:sticky;top:0;
  height:100vh;height:100svh;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  padding:78px 24px 34px;
  overflow:hidden;
}
.stage-product{
  position:relative;
  width:min(90vw,760px,100vh);
  display:grid;place-items:center;
}
.stage-glow{
  position:absolute;width:86%;aspect-ratio:1.6/1;border-radius:50%;
  background:radial-gradient(circle at 50% 55%,rgba(52,110,255,.34),rgba(130,60,255,.16) 46%,transparent 72%);
  filter:blur(46px);pointer-events:none;
}
.stage-inner{
  width:100%;position:relative;
  transform-style:preserve-3d;
  will-change:transform;
}
.stage-inner .glasses{
  width:100%;height:auto;
  filter:drop-shadow(0 44px 80px rgba(0,95,255,.34));
}
.stage-captions{
  position:relative;
  width:min(92vw,660px);
  height:clamp(118px,17vh,158px);
  margin-top:6px;
  flex:none;
}
.stage-caption{
  position:absolute;inset:0;text-align:center;
  opacity:0;transform:translateY(16px);
  transition:opacity .7s var(--ease),transform .7s var(--ease);
}
.stage-caption.active{opacity:1;transform:none}
.stage-caption h3{
  font-size:clamp(21px,3vw,32px);font-weight:600;letter-spacing:-.022em;
  margin:0 0 10px;
}
.stage-caption p{
  margin:0;color:var(--muted-dark);
  font-size:clamp(15px,1.6vw,17px);line-height:1.55;
  max-width:520px;margin-inline:auto;
}

/* ============ FEATURES ============ */
.features-grid{
  display:grid;grid-template-columns:repeat(3,1fr);
  gap:22px;margin-top:76px;text-align:left;
}
.feature{
  background:#fff;
  border-radius:26px;
  padding:36px 32px 40px;
  box-shadow:0 1px 2px rgba(0,0,0,.04),0 18px 40px -26px rgba(0,0,0,.28);
  transition:transform .55s var(--ease),box-shadow .55s var(--ease);
}
.feature:hover{
  transform:translateY(-6px);
  box-shadow:0 2px 4px rgba(0,0,0,.05),0 34px 60px -28px rgba(0,0,0,.32);
}
.feature-icon{
  width:46px;height:46px;border-radius:14px;
  display:grid;place-items:center;
  background:linear-gradient(160deg,#eef4ff,#e5ecff);
  color:var(--blue);
  margin-bottom:22px;
}
.feature-icon svg{width:26px;height:26px}
.feature h3{
  font-size:19px;font-weight:600;letter-spacing:-.015em;margin:0 0 10px;
}
.feature p{
  margin:0;color:var(--muted-light);font-size:15px;line-height:1.55;
}
@media(max-width:920px){.features-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:620px){.features-grid{grid-template-columns:1fr}}

/* ============ STATS ============ */
.stats-grid{
  display:grid;grid-template-columns:repeat(3,1fr);
  gap:24px;margin-top:84px;
}
.stat{padding:0 18px}
.stat + .stat{border-left:1px solid rgba(255,255,255,.1)}
.stat-value{
  display:flex;align-items:baseline;justify-content:center;gap:4px;
  font-size:clamp(56px,9vw,112px);
  font-weight:600;letter-spacing:-.05em;line-height:1;
  background:linear-gradient(180deg,#ffffff 20%,#8e8e93 115%);
  -webkit-background-clip:text;background-clip:text;color:transparent;
  font-variant-numeric:tabular-nums;
}
.stat-unit{
  font-size:clamp(22px,3.4vw,42px);
  letter-spacing:-.02em;font-weight:500;
}
.stat-label{
  margin:18px auto 0;max-width:230px;
  color:var(--muted-dark);font-size:15px;line-height:1.5;
}
@media(max-width:780px){
  .stats-grid{grid-template-columns:1fr;gap:56px;margin-top:60px}
  .stat + .stat{border-left:0;border-top:1px solid rgba(255,255,255,.1);padding-top:56px}
}

/* ============ MODELS ============ */
.models{
  display:grid;grid-template-columns:1fr 1fr;gap:26px;
  max-width:940px;margin:76px auto 0;text-align:left;
}
.model{
  position:relative;
  display:flex;flex-direction:column;
  background:#fff;border-radius:30px;
  padding:42px 36px 38px;
  box-shadow:0 2px 6px rgba(0,0,0,.04),0 30px 60px -34px rgba(0,0,0,.3);
  transition:transform .6s var(--ease),box-shadow .6s var(--ease);
}
.model:hover{transform:translateY(-5px);box-shadow:0 3px 8px rgba(0,0,0,.05),0 40px 74px -34px rgba(0,0,0,.34)}
.model-pro{
  background:#1d1d1f;color:#f5f5f7;
  box-shadow:0 40px 80px -34px rgba(0,0,0,.6);
}
.model h3{font-size:27px;font-weight:600;letter-spacing:-.025em;margin:0 0 6px}
.model-tag{margin:0;color:var(--muted-light);font-size:15px}
.model-pro .model-tag{color:#a1a1a6}
.model-price{
  margin:24px 0 0;font-size:20px;font-weight:500;letter-spacing:-.02em;
}
.model-price span{font-size:34px;font-weight:600;letter-spacing:-.03em}
.badge{
  position:absolute;top:24px;right:24px;
  font-size:11px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;
  padding:5px 11px;border-radius:980px;
  background:#0a84ff;color:#fff;
}
.specs{list-style:none;padding:0;margin:30px 0 34px;flex:1}
.specs li{
  display:flex;justify-content:space-between;gap:14px;
  padding:13px 0;font-size:15px;
  border-bottom:1px solid rgba(0,0,0,.08);
}
.specs li:last-child{border-bottom:0}
.specs span{color:var(--muted-light)}
.specs b{font-weight:500;letter-spacing:-.01em}
.model-pro .specs li{border-bottom-color:rgba(255,255,255,.12)}
.model-pro .specs span{color:#a1a1a6}
.model .btn{width:100%}
@media(max-width:860px){.models{grid-template-columns:1fr;gap:22px}}

/* ============ PREORDER ============ */
.preorder{
  position:relative;overflow:hidden;
  padding:170px 0 150px;
  text-align:center;
  background:#000;
}
.preorder-glow{
  position:absolute;left:50%;top:44%;transform:translate(-50%,-50%);
  width:min(1150px,150vw);aspect-ratio:1.5/1;border-radius:50%;
  background:radial-gradient(circle,rgba(48,110,255,.30),rgba(140,60,255,.14) 44%,transparent 70%);
  filter:blur(58px);pointer-events:none;
}
.preorder-inner{position:relative}
.preorder-title{
  font-size:clamp(52px,11vw,132px);
  font-weight:600;letter-spacing:-.055em;line-height:.95;
  margin:0;
  background:linear-gradient(180deg,#ffffff 25%,#8a8a92 115%);
  -webkit-background-clip:text;background-clip:text;color:transparent;
}
.preorder .lede{color:#a1a1a6}

/* ============ FOOTER ============ */
.footer{
  background:#000;color:#6e6e73;
  border-top:1px solid rgba(255,255,255,.09);
  padding:44px 0 60px;font-size:13px;
}
.footer-inner{
  display:flex;justify-content:space-between;align-items:center;
  gap:20px;flex-wrap:wrap;
}
.footer-links{display:flex;gap:24px;flex-wrap:wrap}
.footer-links a{text-decoration:none;color:#86868b;transition:color .3s var(--ease)}
.footer-links a:hover{color:#f5f5f7}

/* ============ REVEAL ANIMATIONS ============ */
.js .reveal{
  opacity:0;
  transform:translateY(36px);
  transition:opacity 1s var(--ease),transform 1s var(--ease);
  will-change:opacity,transform;
}
.js .reveal-scale{
  transform:translateY(36px) scale(.94);
}
.js .reveal.in{opacity:1;transform:none}

@media (prefers-reduced-motion: reduce){
  html{scroll-behavior:auto}
  *,*::before,*::after{
    animation-duration:.001ms !important;
    animation-iteration-count:1 !important;
    transition-duration:.001ms !important;
  }
}
</style>
</head>
<body id="top">

<!-- ================= NAV ================= -->
<nav class="nav" id="nav">
  <div class="nav-inner">
    <a class="nav-logo" href="#top">Halo</a>
    <div class="nav-links">
      <a href="#design">Design</a>
      <a href="#features">Features</a>
      <a href="#models">Models</a>
    </div>
    <a class="nav-cta" href="#preorder"><span>Pre-order</span></a>
  </div>
</nav>

<!-- ================= HERO ================= -->
<section class="hero" data-theme="dark">
  <div class="hero-glow"></div>

  <p class="eyebrow eyebrow-dark reveal" data-delay="80">Halo</p>
  <h1 class="reveal" data-delay="160">Every conversation,<br>in your language.</h1>
  <p class="lede reveal" data-delay="260">
    Smart glasses that translate speech in real time — subtitles at the edge of your
    vision, translation in your ears, nothing in your hands.
  </p>

  <div class="cta-row reveal" data-delay="360">
    <a href="#preorder" class="btn btn-primary">Pre-order — from $499</a>
    <a href="#design" class="btn btn-ghost">Learn more</a>
  </div>

  <div class="hero-product reveal reveal-scale" data-delay="460">
    <svg class="glasses" viewBox="0 0 520 240" aria-label="Halo smart glasses" role="img">
      <defs>
        <linearGradient id="hFrame" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#f4f7fb"/>
          <stop offset=".42" stop-color="#aab4c7"/>
          <stop offset="1" stop-color="#6a7388"/>
        </linearGradient>
        <linearGradient id="hLens" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="#8ad8ff" stop-opacity=".34"/>
          <stop offset=".55" stop-color="#4d7bff" stop-opacity=".15"/>
          <stop offset="1" stop-color="#c07bff" stop-opacity=".26"/>
        </linearGradient>
        <linearGradient id="hSheen" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stop-color="#ffffff" stop-opacity="0"/>
          <stop offset=".5" stop-color="#ffffff" stop-opacity=".55"/>
          <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
        </linearGradient>
        <clipPath id="hClipL"><rect x="44" y="62" width="184" height="118" rx="40"/></clipPath>
        <clipPath id="hClipR"><rect x="292" y="62" width="184" height="118" rx="40"/></clipPath>
      </defs>

      <!-- lens glass -->
      <rect x="44" y="62" width="184" height="118" rx="40" fill="url(#hLens)"/>
      <rect x="292" y="62" width="184" height="118" rx="40" fill="url(#hLens)"/>

      <!-- light sweep -->
      <g clip-path="url(#hClipL)">
        <rect class="sheen" x="-170" y="10" width="130" height="230" fill="url(#hSheen)"/>
      </g>
      <g clip-path="url(#hClipR)">
        <rect class="sheen" x="-170" y="10" width="130" height="230" fill="url(#hSheen)"/>
      </g>

      <!-- frame -->
      <rect x="44" y="62" width="184" height="118" rx="40" fill="none" stroke="url(#hFrame)" stroke-width="6"/>
      <rect x="292" y="62" width="184" height="118" rx="40" fill="none" stroke="url(#hFrame)" stroke-width="6"/>

      <!-- bridge -->
      <path d="M228 110 C 248 82, 272 82, 292 110"
            fill="none" stroke="url(#hFrame)" stroke-width="6" stroke-linecap="round"/>

      <!-- temples -->
      <path d="M44 100 L 6 76" fill="none" stroke="url(#hFrame)" stroke-width="7" stroke-linecap="round"/>
      <path d="M476 100 L 514 76" fill="none" stroke="url(#hFrame)" stroke-width="7" stroke-linecap="round"/>

      <!-- sensor indicator -->
      <circle class="sensor" cx="260" cy="92" r="3.6" fill="#4ea1ff"/>
    </svg>
  </div>

  <div class="scroll-hint" aria-hidden="true">
    <span>Scroll</span>
    <i></i>
  </div>
</section>

<!-- ================= STICKY SHOWCASE ================= -->
<section class="sticky-section" id="design" data-theme="dark">
  <div class="sticky-stage">
    <div class="stage-product">
      <div class="stage-glow" aria-hidden="true"></div>
      <div class="stage-inner" id="stageInner">
        <svg class="glasses" viewBox="0 0 520 240" aria-hidden="true">
          <defs>
            <linearGradient id="sFrame" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stop-color="#f4f7fb"/>
              <stop offset=".42" stop-color="#aab4c7"/>
              <stop offset="1" stop-color="#6a7388"/>
            </linearGradient>
            <linearGradient id="sLens" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stop-color="#8ad8ff" stop-opacity=".36"/>
              <stop offset=".55" stop-color="#4d7bff" stop-opacity=".16"/>
              <stop offset="1" stop-color="#c07bff" stop-opacity=".28"/>
            </linearGradient>
            <linearGradient id="sSheen" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0" stop-color="#ffffff" stop-opacity="0"/>
              <stop offset=".5" stop-color="#ffffff" stop-opacity=".6"/>
              <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
            </linearGradient>
            <clipPath id="sClipL"><rect x="44" y="62" width="184" height="118" rx="40"/></clipPath>
            <clipPath id="sClipR"><rect x="292" y="62" width="184" height="118" rx="40"/></clipPath>
          </defs>

          <rect x="44" y="62" width="184" height="118" rx="40" fill="url(#sLens)"/>
          <rect x="292" y="62" width="184" height="118" rx="40" fill="url(#sLens)"/>

          <g clip-path="url(#sClipL)">
            <rect class="sheen" x="-170" y="10" width="130" height="230" fill="url(#sSheen)"/>
          </g>
          <g clip-path="url(#sClipR)">
            <rect class="sheen" x="-170" y="10" width="130" height="230" fill="url(#sSheen)"/>
          </g>

          <rect x="44" y="62" width="184" height="118" rx="40" fill="none" stroke="url(#sFrame)" stroke-width="6"/>
          <rect x="292" y="62" width="184" height="118" rx="40" fill="none" stroke="url(#sFrame)" stroke-width="6"/>

          <path d="M228 110 C 248 82, 272 82, 292 110"
                fill="none" stroke="url(#sFrame)" stroke-width="6" stroke-linecap="round"/>

          <path d="M44 100 L 6 76" fill="none" stroke="url(#sFrame)" stroke-width="7" stroke-linecap="round"/>
          <path d="M476 100 L 514 76" fill="none" stroke="url(#sFrame)" stroke-width="7" stroke-linecap="round"/>

          <circle class="sensor" cx="260" cy="92" r="3.6" fill="#4ea1ff"/>
        </svg>
      </div>
    </div>

    <div class="stage-captions" id="stageCaptions">
      <div class="stage-caption">
        <h3>Look. Listen. Understand.</h3>
        <p>Halo reads the room around you and shows a quiet stream of translated subtitles, positioned exactly where you're looking.</p>
      </div>
      <div class="stage-caption">
        <h3>Translation, on device.</h3>
        <p>A dedicated neural engine turns speech into text and text into meaning in under half a second. Nothing is uploaded. Nothing is stored.</p>
      </div>
      <div class="stage-caption">
        <h3>Open-ear, always present.</h3>
        <p>Directional micro-speakers deliver the translated voice to you alone, while your ears stay open to the world.</p>
      </div>
    </div>
  </div>
</section>

<!-- ================= FEATURES ================= -->
<section class="light-section section-pad" id="features" data-theme="light">
  <div class="container centered">
    <p class="eyebrow reveal">Features</p>
    <h2 class="section-title reveal" data-delay="80">See it. Hear it.<br>Understand it.</h2>
    <p class="section-sub reveal" data-delay="160">
      Halo was built around a single idea: language should never be the reason a
      conversation ends.
    </p>

    <div class="features-grid">
      <article class="feature reveal" data-delay="0">
        <div class="feature-icon">
          <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="M5 6h22a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H14l-6 5v-5H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2z"/>
            <path d="M9 13h14M9 18h9"/>
          </svg>
        </div>
        <h3>Live subtitles</h3>
        <p>Translated text appears at the edge of your vision, aligned to the person speaking. No app, no screen, no pause.</p>
      </article>

      <article class="feature reveal" data-delay="90">
        <div class="feature-icon">
          <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="16" cy="16" r="11"/>
            <path d="M5 16h22"/>
            <path d="M16 5c4 4 4 18 0 22M16 5c-4 4-4 18 0 22"/>
          </svg>
        </div>
        <h3>42 languages</h3>
        <p>From Japanese to Portuguese to Swahili — with regional dialects and idioms handled the way people actually speak.</p>
      </article>

      <article class="feature reveal" data-delay="180">
        <div class="feature-icon">
          <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="M16 4l10 4v8c0 6-4.4 10.4-10 12-5.6-1.6-10-6-10-12V8z"/>
            <path d="M11.5 16.2l3 3 6-6.2"/>
          </svg>
        </div>
        <h3>Private by design</h3>
        <p>All audio is processed on-device by the Halo N1 chip. Conversations are never transmitted or retained.</p>
      </article>

      <article class="feature reveal" data-delay="0">
        <div class="feature-icon">
          <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="M5 13h5l6-5v16l-6-5H5z"/>
            <path d="M21 12.5a5.5 5.5 0 0 1 0 7M24.5 9a10 10 0 0 1 0 14"/>
          </svg>
        </div>
        <h3>Open-ear audio</h3>
        <p>Twin directional speakers keep the translation yours alone, while the room stays fully audible.</p>
      </article>

      <article class="feature reveal" data-delay="90">
        <div class="feature-icon">
          <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="10" width="22" height="12" rx="3.6"/>
            <path d="M28 13.5v5"/>
            <rect x="6.5" y="13.5" width="13" height="5" rx="2" fill="currentColor" stroke="none"/>
          </svg>
        </div>
        <h3>18-hour battery</h3>
        <p>A full day of continuous translation on one charge, with a 12-minute top-up for three more hours.</p>
      </article>

      <article class="feature reveal" data-delay="180">
        <div class="feature-icon">
          <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="M27 5C15 5 7 13 5 27c14-2 22-10 22-22z"/>
            <path d="M5 27L20 12"/>
          </svg>
        </div>
        <h3>38 grams</h3>
        <p>A titanium-grade frame that weighs less than a pair of sunglasses. You'll forget you're wearing them.</p>
      </article>
    </div>
  </div>
</section>

<!-- ================= STATS ================= -->
<section class="dark-section section-pad" data-theme="dark">
  <div class="container centered">
    <p class="eyebrow eyebrow-dark reveal">By the numbers</p>
    <h2 class="section-title reveal" data-delay="80">Astonishingly small.<br>Impressively capable.</h2>

    <div class="stats-grid">
      <div class="stat reveal" data-delay="0">
        <div class="stat-value"><span class="count" data-to="18">0</span><span class="stat-unit">h</span></div>
        <p class="stat-label">Battery life with live translation running</p>
      </div>
      <div class="stat reveal" data-delay="120">
        <div class="stat-value"><span class="count" data-to="42">0</span><span class="stat-unit">+</span></div>
        <p class="stat-label">Languages and regional dialects supported</p>
      </div>
      <div class="stat reveal" data-delay="240">
        <div class="stat-value"><span class="count" data-to="38">0</span><span class="stat-unit">g</span></div>
        <p class="stat-label">Total weight, frame and lenses included</p>
      </div>
    </div>
  </div>
</section>

<!-- ================= MODELS ================= -->
<section class="light-section section-pad" id="models" data-theme="light">
  <div class="container centered">
    <p class="eyebrow reveal">Models</p>
    <h2 class="section-title reveal" data-delay="80">Two ways to Halo.</h2>
    <p class="section-sub reveal" data-delay="160">
      Both translate in real time. One does a little more.
    </p>

    <div class="models">
      <article class="model reveal" data-delay="0">
        <h3>Halo</h3>
        <p class="model-tag">The essential pair.</p>
        <p class="model-price"><span>$499</span></p>
        <ul class="specs">
          <li><span>Real-time subtitles</span><b>Included</b></li>
          <li><span>Live voice dubbing</span><b>—</b></li>
          <li><span>Spatial audio</span><b>—</b></li>
          <li><span>Battery life</span><b>18 h</b></li>
          <li><span>Languages</span><b>42+</b></li>
          <li><span>Weight</span><b>38 g</b></li>
          <li><span>Prescription ready</span><b>—</b></li>
        </ul>
        <a href="#preorder" class="btn btn-dark">Pre-order</a>
      </article>

      <article class="model model-pro reveal" data-delay="120">
        <span class="badge">New</span>
        <h3>Halo Pro</h3>
        <p class="model-tag">For people who travel for a living.</p>
        <p class="model-price"><span>$749</span></p>
        <ul class="specs">
          <li><span>Real-time subtitles</span><b>Included</b></li>
          <li><span>Live voice dubbing</span><b>Included</b></li>
          <li><span>Spatial audio</span><b>Included</b></li>
          <li><span>Battery life</span><b>36 h</b></li>
          <li><span>Languages</span><b>42+</b></li>
          <li><span>Weight</span><b>44 g</b></li>
          <li><span>Prescription ready</span><b>Included</b></li>
        </ul>
        <a href="#preorder" class="btn btn-light">Pre-order</a>
      </article>
    </div>
  </div>
</section>

<!-- ================= PRE-ORDER ================= -->
<section class="preorder" id="preorder" data-theme="dark">
  <div class="preorder-glow" aria-hidden="true"></div>
  <div class="container preorder-inner">
    <p class="eyebrow eyebrow-dark reveal">Pre-order</p>
    <h2 class="preorder-title reveal" data-delay="80">Halo.</h2>
    <p class="lede reveal" data-delay="180">
      From $499. Reserve yours today and be among the first to hear the world
      in your own language.
    </p>
    <div class="cta-row reveal" data-delay="280">
      <a href="#top" class="btn btn-primary">Pre-order now</a>
      <a href="#top" class="btn btn-ghost">Notify me</a>
    </div>
    <p class="fineprint reveal" data-delay="360">
      Ships Spring 2026. Free returns within 30 days. Monthly financing available.
    </p>
  </div>
</section>

<!-- ================= FOOTER ================= -->
<footer class="footer">
  <div class="container footer-inner">
    <span>© 2025 Halo Optics. A fictional product, beautifully imagined.</span>
    <div class="footer-links">
      <a href="#design">Design</a>
      <a href="#features">Features</a>
      <a href="#models">Models</a>
      <a href="#preorder">Pre-order</a>
    </div>
  </div>
</footer>

<script>
(function () {
  'use strict';

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- Element refs ---------- */
  var nav = document.getElementById('nav');
  var stickySection = document.querySelector('.sticky-section');
  var stageInner = document.getElementById('stageInner');
  var captions = Array.prototype.slice.call(document.querySelectorAll('.stage-caption'));
  var themedSections = Array.prototype.slice.call(document.querySelectorAll('[data-theme]'));

  /* ---------- Reveal on scroll ---------- */
  var revealEls = Array.prototype.slice.call(document.querySelectorAll('.reveal'));

  revealEls.forEach(function (el) {
    var d = el.getAttribute('data-delay');
    if (d) el.style.transitionDelay = d + 'ms';
  });

  if ('IntersectionObserver' in window) {
    var revealObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('in');
          revealObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -6% 0px' });

    revealEls.forEach(function (el) { revealObserver.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add('in'); });
  }

  /* ---------- Animated numbers ---------- */
  function easeOutQuart(t) { return 1 - Math.pow(1 - t, 4); }

  function animateCount(el) {
    var target = parseFloat(el.getAttribute('data-to')) || 0;
    var decimals = parseInt(el.getAttribute('data-decimals') || '0', 10);
    var duration = reduceMotion ? 0 : 1700;
    var start = null;

    if (duration === 0) {
      el.textContent = target.toFixed(decimals);
      return;
    }

    function step(now) {
      if (start === null) start = now;
      var t = Math.min(1, (now - start) / duration);
      el.textContent = (target * easeOutQuart(t)).toFixed(decimals);
      if (t < 1) {
        requestAnimationFrame(step);
      } else {
        el.textContent = target.toFixed(decimals);
      }
    }
    requestAnimationFrame(step);
  }

  var counters = Array.prototype.slice.call(document.querySelectorAll('.count'));
  if ('IntersectionObserver' in window) {
    var countObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          animateCount(entry.target);
          countObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });
    counters.forEach(function (el) { countObserver.observe(el); });
  } else {
    counters.forEach(function (el) {
      el.textContent = el.getAttribute('data-to');
    });
  }

  /* ---------- Sticky showcase transform ---------- */
  function clamp(v, min, max) { return v < min ? min : (v > max ? max : v); }

  function updateStage() {
    if (!stickySection || !stageInner) return;

    var rect = stickySection.getBoundingClientRect();
    var vh = window.innerHeight;
    var scrollable = stickySection.offsetHeight - vh;

    if (scrollable <= 0) return;

    var p = clamp(-rect.top / scrollable, 0, 1);

    /* Rotation: -30deg -> +30deg, with a gentle tilt and scale */
    var rotY = -30 + p * 60;
    var rotX = 11 - p * 21;
    var scale = 0.83 + p * 0.30;
    var lift = (0.5 - p) * 26;

    stageInner.style.transform =
      'perspective(1500px) ' +
      'translate3d(0,' + lift.toFixed(2) + 'px,0) ' +
      'rotateX(' + rotX.toFixed(2) + 'deg) ' +
      'rotateY(' + rotY.toFixed(2) + 'deg) ' +
      'scale(' + scale.toFixed(3) + ')';

    /* Captions */
    if (captions.length) {
      var idx = clamp(Math.floor(p * captions.length * 0.9999), 0, captions.length - 1);
      for (var i = 0; i < captions.length; i++) {
        captions[i].classList.toggle('active', i === idx);
      }
    }
  }

  /* ---------- Nav theme switching ---------- */
  function updateNavTheme() {
    if (!nav) return;
    var probe = 27;
    var theme = 'dark';

    for (var i = 0; i < themedSections.length; i++) {
      var r = themedSections[i].getBoundingClientRect();
      if (r.top <= probe && r.bottom > probe) {
        theme = themedSections[i].getAttribute('data-theme');
        break;
      }
    }
    nav.classList.toggle('nav-light', theme === 'light');
  }

  /* ---------- Scroll loop ---------- */
  var ticking = false;

  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      updateStage();
      updateNavTheme();
      ticking = false;
    });
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  window.addEventListener('orientationchange', onScroll);

  /* ---------- Initial paint ---------- */
  updateStage();
  updateNavTheme();

  /* Make sure captions start visible if already in position */
  if (captions.length && !captions[0].classList.contains('active')) {
    var first = true;
    for (var k = 0; k < captions.length; k++) {
      if (captions[k].classList.contains('active')) first = false;
    }
    if (first) captions[0].classList.add('active');
  }
})();
</script>
</body>
</html>
```
### Scroll-driven Visual Storytelling
The page uses a sticky product showcase, scroll-triggered reveals, and animated counters to create a smooth, premium browsing experience.

- **Sticky rotation** – As you scroll through the showcase section, the glasses rotate from -30° to +30° with a subtle lift and scale, while three captions fade in and out to match the motion.
- **Scroll-triggered reveals** – Every major block fades and slides into view via IntersectionObserver, with optional per-element delays for a staggered entrance.
- **Animated stats** – The large numbers in the dark section count up when they enter the viewport, using an ease-out curve for a natural feel.
- **Adaptive navigation** – The fixed top bar automatically switches between dark and light themes based on which section is currently under it, keeping contrast comfortable.
---

**Optimization Tip:** You can adjust the sticky section's scroll length by changing `.sticky-section { height: 320vh; }`, and fine-tune the rotation range in `updateStage()` (currently -30° to +30°). The animation duration for the count-up numbers is set to 1700ms — feel free to tweak it.