 ```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Halo — Real‑Time Translation Glasses</title>
    <style>
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
            line-height: 1.5;
        }
        a {
            text-decoration: none;
            color: inherit;
        }
        img {
            max-width: 100%;
        }

        /* ----------------------------------
           Navigation
           ------------------------------------ */
        .nav {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 18px 40px;
            background: rgba(10, 10, 15, 0.6);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            transition: background 0.4s ease, border-color 0.4s ease;
        }
        .nav-logo {
            font-size: 22px;
            font-weight: 800;
            letter-spacing: -0.02em;
        }
        .nav-logo span {
            color: #00d9ff;
        }
        .nav-links a {
            color: #f5f5f7;
            font-size: 14px;
            margin: 0 18px;
            opacity: 0.85;
            transition: opacity 0.3s;
        }
        .nav-links a:hover {
            opacity: 1;
        }
        .nav-cta {
            background: #0071e3;
            color: #fff;
            border-radius: 980px;
            padding: 8px 18px;
            font-size: 14px;
            transition: background 0.3s;
        }
        .nav-cta:hover {
            background: #0077ed;
        }

        /* ----------------------------------
           Buttons
           ------------------------------------ */
        .btn {
            display: inline-block;
            padding: 12px 28px;
            border-radius: 980px;
            font-size: 17px;
            font-weight: 500;
            transition: all 0.3s ease;
            cursor: pointer;
            border: none;
        }
        .btn-primary {
            background: #0071e3;
            color: #fff;
        }
        .btn-primary:hover {
            background: #0077ed;
            transform: scale(1.02);
            box-shadow: 0 8px 30px rgba(0, 113, 227, 0.35);
        }
        .btn-secondary {
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        .btn-dark {
            background: #0a0a0f;
            color: #fff;
        }
        .btn-dark:hover {
            background: #1d1d1f;
        }

        /* ----------------------------------
           Hero
           ------------------------------------ */
        .hero {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            background: radial-gradient(ellipse at center, rgba(0, 217, 255, 0.1) 0%, transparent 60%), #0a0a0f;
            padding: 120px 24px 80px;
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
            margin-top: 10px;
            animation: fadeUp 1s 0.1s ease both;
        }
        .hero h1 .gradient {
            background: linear-gradient(90deg, #00d9ff, #0066ff);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            color: transparent;
        }
        .hero-sub {
            font-size: 21px;
            line-height: 1.5;
            color: #a1a1b5;
            max-width: 620px;
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
        .hero-product {
            width: min(90%, 700px);
            margin-top: 40px;
            filter: drop-shadow(0 20px 60px rgba(0, 0, 0, 0.5));
            animation: heroProduct 1s 0.4s cubic-bezier(0.2, 0.8, 0.2, 1) both;
        }
        .scroll-indicator {
            position: absolute;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            width: 1px;
            height: 44px;
            background: linear-gradient(to bottom, rgba(255, 255, 255, 0.5), transparent);
            animation: pulse 2s infinite;
        }

        /* ----------------------------------
           Intro (white section)
           ------------------------------------ */
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

        /* ----------------------------------
           Sticky Section (scroll‑driven rotation)
           ------------------------------------ */
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
            padding: 0 24px;
        }
        .sticky-label {
            font-size: 18px;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #00d9ff;
            margin-bottom: 12px;
        }
        .sticky-title {
            font-size: clamp(28px, 4vw, 44px);
            font-weight: 700;
            text-align: center;
            margin-bottom: 24px;
            max-width: 700px;
        }
        .sticky-product {
            width: min(80%, 600px);
        }

        /* ----------------------------------
           Features (white section)
           ------------------------------------ */
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
            background: #fff;
            border-radius: 24px;
            padding: 40px;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
            border: 1px solid #e5e5e5;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .feature-card:hover {
            transform: translateY(-6px);
            box-shadow: 0 12px 32px rgba(0, 0, 0, 0.08);
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
        .feature-icon svg {
            width: 24px;
            height: 24px;
            stroke: #fff;
            fill: none;
            stroke-width: 2;
            stroke-linecap: round;
            stroke-linejoin: round;
        }
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

        /* ----------------------------------
           Stats (dark)
           ------------------------------------ */
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
        .stat-number .accent {
            color: #00d9ff;
        }
        .stat-label {
            font-size: 16px;
            color: #a1a1b5;
            margin-top: 12px;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }

        /* ----------------------------------
           Compare (white)
           ------------------------------------ */
        .compare {
            background: #fff;
            color: #1d1d1f;
            padding: 120px 24px;
        }
        .compare-heading {
            text-align: center;
            font-size: clamp(32px, 5vw, 48px);
            font-weight: 700;
            margin-bottom: 80px;
        }
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
            color: #fff;
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
        .compare-card h3 {
            font-size: 28px;
            margin-top: 12px;
        }
        .compare-price {
            font-size: 48px;
            font-weight: 800;
            margin-top: 16px;
        }
        .compare-price span {
            font-size: 16px;
            color: #6e6e73;
        }
        .compare-card.pro .compare-price span {
            color: #a1a1b5;
        }
        .compare-features {
            list-style: none;
            margin: 32px 0 0;
            text-align: left;
        }
        .compare-features li {
            padding: 8px 0;
            font-size: 16px;
            border-bottom: 1px solid rgba(0, 0, 0, 0.06);
            display: flex;
            gap: 10px;
            align-items: center;
        }
        .compare-card.pro .compare-features li {
            border-color: rgba(255, 255, 255, 0.1);
        }
        .compare-features .check {
            color: #00d9ff;
            font-weight: 700;
        }
        .compare-features .muted {
            color: #b0b0b8;
        }
        .compare-card.pro .compare-features .muted {
            color: #6e6e73;
        }
        .compare-btn {
            margin-top: 32px;
            width: 100%;
            display: inline-block;
        }

        /* ----------------------------------
           CTA
           ------------------------------------ */
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
        .cta .btn {
            margin-top: 40px;
            font-size: 20px;
            padding: 16px 36px;
        }
        .cta-note {
            margin-top: 20px;
            color: #a1a1b5;
            font-size: 14px;
        }

        /* ----------------------------------
           Footer
           ------------------------------------ */
        footer {
            background: #050508;
            padding: 40px;
            text-align: center;
            color: #63636e;
            font-size: 13px;
        }

        /* ----------------------------------
           Reveal animations
           ------------------------------------ */
        .reveal {
            opacity: 0;
            transform: translateY(40px);
            transition: opacity 0.8s ease, transform 0.8s ease;
        }
        .reveal.visible {
            opacity: 1;
            transform: none;
        }
        .reveal-delay-1 {
            transition-delay: 0.1s;
        }
        .reveal-delay-2 {
            transition-delay: 0.2s;
        }
        .reveal-delay-3 {
            transition-delay: 0.3s;
        }

        @keyframes fadeUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: none;
            }
        }
        @keyframes heroProduct {
            from {
                opacity: 0;
                transform: scale(0.9) translateY(40px);
            }
            to {
                opacity: 1;
                transform: none;
            }
        }
        @keyframes pulse {
            0% {
                opacity: 0;
            }
            50% {
                opacity: 1;
            }
            100% {
                opacity: 0;
            }
        }

        /* ----------------------------------
           Responsive
           ------------------------------------ */
        @media (max-width: 768px) {
            .nav-links {
                display: none;
            }
            .features-grid {
                grid-template-columns: 1fr;
            }
            .stat-grid {
                grid-template-columns: 1fr 1fr;
            }
            .compare-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>

    <!-- =====================
         SVG Defs
         ====================== -->
    <svg width="0" height="0" style="position:absolute;width:0;height:0" aria-hidden="true">
        <defs>
            <linearGradient id="frameGrad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#4a4a5e"></stop>
                <stop offset="100%" stop-color="#181822"></stop>
            </linearGradient>
            <linearGradient id="lensGrad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#00d9ff" stop-opacity="0.75"></stop>
                <stop offset="100%" stop-color="#0055ff" stop-opacity="0.75"></stop>
            </linearGradient>
            <linearGradient id="haloGrad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#00d9ff" stop-opacity="0"></stop>
                <stop offset="50%" stop-color="#00d9ff" stop-opacity="1"></stop>
                <stop offset="100%" stop-color="#00d9ff" stop-opacity="0"></stop>
            </linearGradient>
            <radialGradient id="bgGlow" cx="0.5" cy="0.5" r="0.5">
                <stop offset="0%" stop-color="#00d9ff" stop-opacity="0.2"></stop>
                <stop offset="100%" stop-color="#00d9ff" stop-opacity="0"></stop>
            </radialGradient>
            <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="8" result="blur"></feGaussianBlur>
                <feComposite in="SourceGraphic" in2="blur" operator="over"></feComposite>
            </filter>
        </defs>

        <!-- =====================
             Halo Glasses Symbol
             ====================== -->
        <symbol id="glasses" viewBox="0 0 600 400">
            <ellipse cx="300" cy="210" rx="180" ry="90" fill="url(#bgGlow)"></ellipse>
            <!-- Temples -->
            <path d="M120 185 L30 170 C18 168 12 180 16 200 C20 220 24 230 16 240" fill="none" stroke="url(#frameGrad)" stroke-width="14" stroke-linecap="round"></path>
            <path d="M480 185 L570 170 C582 168 588 180 584 200 C580 220 576 230 584 240" fill="none" stroke="url(#frameGrad)" stroke-width="14" stroke-linecap="round"></path>
            <!-- Bridge -->
            <path d="M270 190 Q300 165 330 190" fill="none" stroke="url(#frameGrad)" stroke-width="16" stroke-linecap="round"></path>
            <!-- Frames -->
            <rect x="120" y="150" width="180" height="130" rx="45" fill="none" stroke="url(#frameGrad)" stroke-width="16"></rect>
            <rect x="300" y="150" width="180" height="130" rx="45" fill="none" stroke="url(#frameGrad)" stroke-width="16"></rect>
            <!-- Lenses -->
            <rect x="132" y="162" width="156" height="106" rx="36" fill="url(#lensGrad)"></rect>
            <rect x="312" y="162" width="156" height="106" rx="36" fill="url(#lensGrad)"></rect>
            <!-- Highlights -->
            <path d="M150 180 L200 168 L160 250 Z" fill="#fff" opacity="0.15"></path>
            <path d="M330 180 L380 168 L340 250 Z" fill="#fff" opacity="0.15"></path>
            <!-- Camera -->
            <circle cx="300" cy="190" r="6" fill="#101018" stroke="#4e4e66" stroke-width="2"></circle>
            <circle cx="300" cy="189" r="2" fill="#00d9ff" opacity="0.8"></circle>
            <!-- Halo -->
            <ellipse cx="300" cy="125" rx="70" ry="20" fill="none" stroke="url(#haloGrad)" stroke-width="4" filter="url(#glow)"></ellipse>
            <!-- Translation lines -->
            <g opacity="0.5">
                <rect x="145" y="245" width="50" height="4" rx="2" fill="#fff"></rect>
                <rect x="145" y="255" width="30" height="4" rx="2" fill="#fff" opacity="0.6"></rect>
                <rect x="325" y="245" width="50" height="4" rx="2" fill="#fff"></rect>
                <rect x="325" y="255" width="30" height="4" rx="2" fill="#fff" opacity="0.6"></rect>
            </g>
        </symbol>
    </svg>

    <!-- =====================
         Navigation
         ====================== -->
    <nav class="nav">
        <div class="nav-logo">Halo<span>.</span></div>
        <div class="nav-links">
            <a href="#tech">Technology</a>
            <a href="#stats">Stats</a>
            <a href="#compare">Models</a>
        </div>
        <a href="#cta" class="nav-cta">Order</a>
    </nav>

    <!-- =====================
         Hero
         ====================== -->
    <section class="hero">
        <div class="hero-eyebrow">Introducing Halo</div>
        <h1>Translate the<br><span class="gradient">world around you</span></h1>
        <p class="hero-sub">Halo glasses whisper every conversation straight to your ear. No phone, no screen — just the moment.</p>
        <div class="hero-ctas">
            <a href="#tech" class="btn btn-primary">Learn more</a>
            <a href="#cta" class="btn btn-secondary">Pre‑order now</a>
        </div>
        <svg class="hero-product" viewBox="0 0 600 400" role="img" aria-label="Halo smart glasses">
            <use href="#glasses"></use>
        </svg>
        <div class="scroll-indicator"></div>
    </section>

    <!-- =====================
         Intro
         ====================== -->
    <section class="intro">
        <h2>Real‑time translation,<br>zero <span class="accent">interruption</span>.</h2>
        <p>Halo combines a powerful neural engine with feather‑light frames. It translates 30+ languages as fast as you speak them — completely handled in the frame.</p>
    </section>

    <!-- =====================
         Sticky scroll section
         ====================== -->
    <section class="sticky-section" id="tech">
        <div class="sticky-inner">
            <span class="sticky-label" id="sticky-label">Meet Halo</span>
            <h2 class="sticky-title">A new dimension of conversation</h2>
            <svg class="sticky-product" viewBox="0 0 600 400">
                <use href="#glasses"></use>
            </svg>
        </div>
    </section>

    <!-- =====================
         Features
         ====================== -->
    <section class="features">
        <h2 class="features-heading">Everything matters.</h2>
        <div class="features-grid">
            <div class="feature-card reveal">
                <div class="feature-icon">
                    <svg><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                </div>
                <h3>Instant translation</h3>
                <p>0.3s average latency — faster than any other wearable.</p>
            </div>
            <div class="feature-card reveal reveal-delay-1">
                <div class="feature-icon">
                    <svg><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15 15 0 0 1 0 20a15 15 0 0 1 0-20z"/></svg>
                </div>
                <h3>30+ languages</h3>
                <p>From Spanish to Japanese — full bilingual conversations.</p>
            </div>
            <div class="feature-card reveal reveal-delay-2">
                <div class="feature-icon">
                    <svg><rect x="1" y="6" width="18" height="12" rx="2"/><line x1="23" y1="10" x2="23" y2="14"/></svg>
                </div>
                <h3>All‑day battery</h3>
                <p>12h battery, 24h with the case. The case fits in your pocket.</p>
            </div>
            <div class="feature-card reveal">
                <div class="feature-icon">
                    <svg><path d="M20.24 12.24a6 6 0 0 0-8.49-8.49L5 10.5V19h8.5z"/><line x1="16" y1="8" x2="2" y2="22"/><line x1="17.5" y1="15" x2="9" y2="15"/></svg>
                </div>
                <h3>Featherlight</h3>
                <p>65g — you’ll forget you’re wearing them. Truly all-day wear.</p>
            </div>
            <div class="feature-card reveal reveal-delay-1">
                <div class="feature-icon">
                    <svg><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                </div>
                <h3>Privacy by design</h3>
                <p>On‑device neural engine. Your conversations never leave the frame.</p>
            </div>
            <div class="feature-card reveal reveal-delay-2">
                <div class="feature-icon">
                    <svg><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
                </div>
                <h3>Spatial sound</h3>
                <p>Discreet open‑ear audio that keeps you in the moment.</p>
            </div>
        </div>
    </section>

    <!-- =====================
         Stats
         ====================== -->
    <section class="stats" id="stats">
        <div class="stat-grid">
            <div class="stat">
                <div class="stat-number"><span class="counter" data-target="0.3" data-decimals="1">0</span><span class="accent">s</span></div>
                <div class="stat-label">Latency</div>
            </div>
            <div class="stat">
                <div class="stat-number"><span class="counter" data-target="30">0</span><span class="accent">+</span></div>
                <div class="stat-label">Languages</div>
            </div>
            <div class="stat">
                <div class="stat-number"><span class="counter" data-target="24">0</span><span class="accent">h</span></div>
                <div class="stat-label">Battery with case</div>
            </div>
            <div class="stat">
                <div class="stat-number"><span class="counter" data-target="65">0</span><span class="accent">g</span></div>
                <div class="stat-label">Weight</div>
            </div>
        </div>
    </section>

    <!-- =====================
         Compare
         ====================== -->
    <section class="compare" id="compare">
        <h2 class="compare-heading">Which Halo is yours?</h2>
        <div class="compare-grid">
            <div class="compare-card reveal">
                <h3>Halo</h3>
                <div class="compare-price">$499<span> / pair</span></div>
                <ul class="compare-features">
                    <li><span class="check">✓</span>30 languages</li>
                    <li><span class="check">✓</span>0.3s translation latency</li>
                    <li class="muted">✗ No on‑lens display</li>
                    <li class="muted">✗ No 4G LTE</li>
                    <li class="muted">✗ No 3D camera</li>
                </ul>
                <a href="#cta" class="btn btn-dark compare-btn">Order</a>
            </div>
            <div class="compare-card pro reveal">
                <div class="badge">Most advanced</div>
                <h3>Halo Pro</h3>
                <div class="compare-price">$799<span> / pair</span></div>
                <ul class="compare-features">
                    <li><span class="check">✓</span>50+ languages</li>
                    <li><span class="check">✓</span>0.1s translation latency</li>
                    <li><span class="check">✓</span>On‑lens display</li>
                    <li><span class="check">✓</span>4G LTE</li>
                    <li><span class="check">✓</span>3D spatial camera</li>
                </ul>
                <a href="#cta" style="background:#00d9ff;border-color:#00d9ff;color:#0a0a0f" class="btn compare-btn">Order Pro</a>
            </div>
        </div>
    </section>

    <!-- =====================
         CTA
         ====================== -->
    <section class="cta" id="cta">
        <h2>Be ready for<b>every conversation.</b></h2>
        <a href="#" class="btn btn-primary">Pre‑order Halo now</a>
        <p class="cta-note">Free shipping · 30‑day returns · 2‑year warranty</p>
    </section>

    <!-- =====================
         Footer
         ====================== -->
    <footer>
        <p>&copy; 2024 Halo Labs. All rights reserved. <a href="#">Privacy</a> · <a href="#">Terms</a></p>
    </footer>

    <!-- =====================
         JavaScript
         ====================== -->
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            // Reveal on scroll
            const io = new IntersectionObserver((entries, obs) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('visible');
                        obs.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.15 });
            document.querySelectorAll('.reveal').forEach(el => io.observe(el));

            // Sticky scroll rotation
            const stickySection = document.querySelector('.sticky-section');
            const stickyProduct = document.querySelector('.sticky-product');
            const stickyLabel = document.getElementById('sticky-label');

            if (stickySection && stickyProduct) {
                const updateSticky = () => {
                    const rect = stickySection.getBoundingClientRect();
                    const vh = window.innerHeight;
                    const total = stickySection.offsetHeight - vh;
                    let progress = -rect.top / total;
                    progress = Math.max(0, Math.min(1, progress));
                    const rotate = progress * 360;
                    const scale = 0.7 + progress * 0.3;
                    stickyProduct.style.transform = `rotate(${rotate}deg) scale(${scale})`;

                    // Update label based on progress
                    if (progress < 0.25) stickyLabel.textContent = 'Meet Halo';
                    else if (progress < 0.5) stickyLabel.textContent = 'Listen';
                    else if (progress < 0.75) stickyLabel.textContent = 'Translate';
                    else stickyLabel.textContent = 'Any language, any moment';
                };
                updateSticky();
                window.addEventListener('scroll', updateSticky, { passive: true });
                window.addEventListener('resize', updateSticky);
            }

            // Animated counters
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

            // Nav background on scroll
            const nav = document.querySelector('.nav');
            window.addEventListener('scroll', () => {
                if (window.scrollY > 50) {
                    nav.style.background = 'rgba(10,10,15,0.85)';
                    nav.style.borderColor = 'rgba(255,255,255,0.1)';
                } else {
                    nav.style.background = 'rgba(10,10,15,0.6)';
                    nav.style.borderColor = 'rgba(255,255,255,0.08)';
                }
            });
        });
    </script>
</body>
</html>
```