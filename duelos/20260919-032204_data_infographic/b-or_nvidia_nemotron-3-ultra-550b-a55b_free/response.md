```html
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>La Molienda — Ventas 2026</title>
<style>
:root{
  --bg:#1a120b;
  --bg-deep:#0f0804;
  --cream:#f5e6d3;
  --cream-dim:#e8d4bc;
  --coffee-dark:#2c1810;
  --coffee-med:#4a3728;
  --coffee-light:#8b6914;
  --amber:#d4a574;
  --gold:#e8c56d;
  --gold-bright:#f0d48a;
  --steam:#fff8f0;
  --steam-dim:#ddd0c0;
  --accent:#c97b2a;
  --shadow:rgba(0,0,0,0.45);
  --radius:14px;
  --max-val:4210;
  --chart-h:420px;
  --bar-w:52px;
  --gap:28px;
  --font-display:'Georgia', 'Times New Roman', serif;
  --font-ui:'system-ui', -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
}
*{box-sizing:border-box;margin:0;padding:0}
@media (prefers-reduced-motion: reduce){
  *,*::before,*::after{animation-duration:0.01ms !important;animation-iteration-count:1 !important;transition-duration:0.01ms !important}
}
html,body{height:100%;width:100%;background:var(--bg);color:var(--cream);font-family:var(--font-ui);overflow:hidden}
.stage{position:relative;width:100%;height:100%;display:grid;grid-template-rows:auto 1fr auto;background:
  radial-gradient(ellipse 80% 60% at 50% 0%, rgba(139,105,20,0.12) 0%, transparent 60%),
  radial-gradient(ellipse 60% 50% at 50% 100%, rgba(212,165,116,0.08) 0%, transparent 50%),
  linear-gradient(180deg, var(--bg-deep) 0%, var(--bg) 40%, var(--coffee-dark) 100%);
  overflow:hidden
}
.stage::before{content:"";position:absolute;inset:0;background-image:url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E");pointer-events:none;z-index:0}
.stage::after{content:"";position:absolute;top:0;left:0;right:0;height:180px;background:linear-gradient(180deg, rgba(212,165,116,0.06) 0%, transparent 100%);pointer-events:none;z-index:0}

/* Steam decorative */
.steam{position:absolute;bottom:10%;width:100%;display:flex;justify-content:center;gap:120px;pointer-events:none;z-index:1;opacity:0.6}
.steam span{position:absolute;bottom:0;width:6px;height:60px;background:linear-gradient(180deg, var(--steam) 0%, transparent 100%);border-radius:3px;animation:steamRise 6s ease-in-out infinite}
.steam span:nth-child(1){left:20%;animation-delay:0s;transform:scaleX(0.8)}
.steam span:nth-child(2){left:35%;animation-delay:1.2s;transform:scaleX(1.2)}
.steam span:nth-child(3){left:50%;animation-delay:2.4s;transform:scaleX(0.9)}
.steam span:nth-child(4){left:65%;animation-delay:3.6s;transform:scaleX(1.1)}
.steam span:nth-child(5){left:80%;animation-delay:4.8s;transform:scaleX(0.7)}
@keyframes steamRise{0%{transform:translateY(0) scale(1);opacity:0}15%{opacity:0.5}100%{transform:translateY(-300px) scale(1.5);opacity:0}}

/* Header */
.header{position:relative;z-index:2;padding:48px 60px 24px;text-align:center;animation:fadeDown 1s cubic-bezier(0.22,1,0.36,1) forwards;opacity:0}
@keyframes fadeDown{from{opacity:0;transform:translateY(-30px)}to{opacity:1;transform:translateY(0)}}
.title{font-family:var(--font-display);font-size:clamp(2.8rem,5vw,4.5rem);font-weight:400;letter-spacing:0.04em;color:var(--cream);text-shadow:0 4px 24px rgba(0,0,0,0.5), 0 0 2px var(--gold);margin-bottom:8px;line-height:1.1}
.title em{font-style:italic;color:var(--gold);font-weight:400}
.subtitle{font-size:clamp(1rem,1.8vw,1.35rem);color:var(--cream-dim);font-weight:300;letter-spacing:0.02em;max-width:700px;margin:0 auto}

/* Chart Area */
.chart-wrap{position:relative;z-index:2;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:0 40px 20px;min-height:0}
.chart-title{font-family:var(--font-display);font-size:clamp(1.2rem,2.2vw,1.6rem);color:var(--gold);margin-bottom:16px;letter-spacing:0.02em;opacity:0;animation:fadeUp 0.8s 0.3s cubic-bezier(0.22,1,0.36,1) forwards}
@keyframes fadeUp{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}

.chart{position:relative;width:100%;max-width:1320px;height:var(--chart-h);display:flex;align-items:flex-end;justify-content:center;gap:var(--gap);padding:0 20px 30px}
.chart::before{content:"";position:absolute;left:20px;right:20px;bottom:30px;height:1px;background:linear-gradient(90deg, transparent, rgba(212,165,116,0.25), transparent);z-index:1}
.y-axis{position:absolute;left:20px;bottom:30px;top:20px;display:flex;flex-direction:column;justify-content:space-between;pointer-events:none;z-index:2}
.y-axis span{font-size:0.7rem;color:var(--cream-dim);text-align:right;width:50px;margin-right:10px;transform:translateY(50%);font-family:var(--font-ui);font-weight:400;opacity:0;animation:fadeIn 0.6s 0.5s cubic-bezier(0.22,1,0.36,1) forwards}
.y-axis span:nth-child(1){animation-delay:0.5s}
.y-axis span:nth-child(2){animation-delay:0.55s}
.y-axis span:nth-child(3){animation-delay:0.6s}
.y-axis span:nth-child(4){animation-delay:0.65s}
.y-axis span:nth-child(5){animation-delay:0.7s}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}

.bar-group{position:relative;flex:0 0 var(--bar-w);display:flex;flex-direction:column;align-items:center;cursor:default;transition:transform 0.2s ease}
.bar-group:hover{transform:translateY(-4px)}
.bar-group:focus-visible{outline:2px solid var(--gold);outline-offset:4px;border-radius:4px}

.bar-wrap{position:relative;width:100%;height:calc(var(--chart-h) - 30px);display:flex;align-items:flex-end}
.bar{position:relative;width:100%;background:linear-gradient(180deg, var(--gold-bright) 0%, var(--amber) 40%, var(--coffee-light) 100%);border-radius:var(--radius) var(--radius) 0 0;box-shadow:
  0 -2px 0 rgba(255,255,255,0.1) inset,
  0 2px 0 rgba(0,0,0,0.2) inset,
  0 8px 24px var(--shadow),
  0 0 0 1px rgba(212,165,116,0.15);
transform-origin:bottom center;transform:scaleY(0);animation:growBar 1.2s cubic-bezier(0.22,1,0.36,1) forwards;opacity:0}
@keyframes growBar{from{transform:scaleY(0);opacity:0}to{transform:scaleY(1);opacity:1}}

.bar-group:nth-child(1) .bar{animation-delay:0.3s}
.bar-group:nth-child(2) .bar{animation-delay:0.38s}
.bar-group:nth-child(3) .bar{animation-delay:0.46s}
.bar-group:nth-child(4) .bar{animation-delay:0.54s}
.bar-group:nth-child(5) .bar{animation-delay:0.62s}
.bar-group:nth-child(6) .bar{animation-delay:0.7s}
.bar-group:nth-child(7) .bar{animation-delay:0.78s}
.bar-group:nth-child(8) .bar{animation-delay:0.86s}
.bar-group:nth-child(9) .bar{animation-delay:0.94s}
.bar-group:nth-child(10) .bar{animation-delay:1.02s}
.bar-group:nth-child(11) .bar{animation-delay:1.1s}
.bar-group:nth-child(12) .bar{animation-delay:1.18s}

/* Best month highlight */
.bar-group.best .bar{background:linear-gradient(180deg, #fff8e0 0%, var(--gold-bright) 20%, var(--gold) 50%, var(--amber) 100%);box-shadow:
  0 -2px 0 rgba(255,255,255,0.2) inset,
  0 2px 0 rgba(0,0,0,0.15) inset,
  0 0 32px 8px rgba(232,197,109,0.4),
  0 12px 32px var(--shadow),
  0 0 0 1px rgba(232,197,109,0.3)}
.bar-group.best::after{content:"★ MEJOR MES";position:absolute;top:-28px;left:50%;transform:translateX(-50%);font-size:0.6rem;font-weight:700;color:var(--gold-bright);letter-spacing:0.08em;white-space:nowrap;animation:badgePop 0.6s 1.3s cubic-bezier(0.34,1.56,0.64,1) forwards;opacity:0;text-shadow:0 0 8px rgba(232,197,109,0.6)}
@keyframes badgePop{from{opacity:0;transform:translateX(-50%) scale(0.5)}to{opacity:1;transform:translateX(-50%) scale(1)}}

/* Value label on bar */
.bar-value{position:absolute;bottom:100%;left:50%;transform:translateX(-50%) translateY(-8px);font-size:0.75rem;font-weight:600;color:var(--cream);white-space:nowrap;opacity:0;animation:fadeUpSmall 0.4s 1.4s cubic-bezier(0.22,1,0.36,1) forwards;font-family:var(--font-ui);text-shadow:0 2px 8px var(--shadow)}
.bar-group.best .bar-value{color:var(--gold-bright)}
@keyframes fadeUpSmall{from{opacity:0;transform:translateX(-50%) translateY(0)}to{opacity:1;transform:translateX(-50%) translateY(-8px)}}

/* Month label */
.month-label{margin-top:10px;font-size:0.7rem;color:var(--cream-dim);font-weight:500;letter-spacing:0.02em;text-transform:uppercase;opacity:0;animation:fadeIn 0.5s 1.2s cubic-bezier(0.22,1,0.36,1) forwards;text-align:center;line-height:1.2}
.bar-group.best .month-label{color:var(--gold);font-weight:700}

/* KPI Section */
.kpi-section{position:relative;z-index:2;display:grid;grid-template-columns:repeat(3,1fr);gap:24px;padding:0 60px 48px;max-width:1320px;margin:0 auto;width:100%}
.kpi-card{background:linear-gradient(145deg, rgba(74,55,40,0.9) 0%, rgba(44,24,16,0.95) 100%);border:1px solid rgba(212,165,116,0.15);border-radius:var(--radius);padding:28px 24px;display:flex;flex-direction:column;align-items:center;text-align:center;position:relative;overflow:hidden;box-shadow:0 12px 40px var(--shadow);opacity:0;animation:kpiEnter 0.8s cubic-bezier(0.22,1,0.36,1) forwards}
.kpi-card::before{content:"";position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg, var(--amber), var(--gold), var(--amber));opacity:0.8}
.kpi-card:nth-child(1){animation-delay:1.4s}
.kpi-card:nth-child(2){animation-delay:1.55s}
.kpi-card:nth-child(3){animation-delay:1.7s}
@keyframes kpiEnter{from{opacity:0;transform:translateY(30px) scale(0.95)}to{opacity:1;transform:translateY(0) scale(1)}}
.kpi-label{font-size:0.7rem;text-transform:uppercase;letter-spacing:0.12em;color:var(--cream-dim);font-weight:600;margin-bottom:10px}
.kpi-value{font-family:var(--font-display);font-size:clamp(2.2rem,4vw,3.2rem);font-weight:400;color:var(--cream);line-height:1;letter-spacing:0.01em;text-shadow:0 2px 12px var(--shadow)}
.kpi-card:nth-child(1) .kpi-value{color:var(--gold-bright)}
.kpi-card:nth-child(2) .kpi-value{color:var(--amber)}
.kpi-card:nth-child(3) .kpi-value{color:var(--gold)}
.kpi-sublabel{font-size:0.65rem;color:var(--steam-dim);margin-top:6px;font-weight:400}

/* Reduced motion fallbacks */
@media (prefers-reduced-motion: reduce){
  .header,.chart-title,.y-axis span,.bar,.bar-value,.month-label,.kpi-card{animation:none !important;opacity:1 !important;transform:none !important}
  .steam{display:none}
}

/* Responsive */
@media (max-width:1024px){
  :root{--chart-h:340px;--bar-w:40px;--gap:18px}
  .header{padding:32px 30px 16px}
  .kpi-section{padding:0 30px 36px;gap:16px}
  .kpi-card{padding:22px 18px}
  .y-axis{left:10px}
  .chart{padding:0 10px 20px}
}
@media (max-width:640px){
  :root{--chart-h:280px;--bar-w:32px;--gap:12px}
  .header{padding:24px 20px 12px}
  .kpi-section{grid-template-columns:1fr;gap:14px;padding:0 20px 28px}
  .chart{padding:0 5px 15px}
  .y-axis{display:none}
  .bar-value{font-size:0.65rem}
  .month-label{font-size:0.6rem}
}
@media (max-height:700px) and (orientation:landscape){
  :root{--chart-h:260px}
  .header{padding:20px 40px 10px}
  .kpi-section{padding:0 40px 24px}
}

/* High contrast mode */
@media (prefers-contrast: high){
  :root{--cream:#fff;--cream-dim:#ddd;--gold:#ffd700;--gold-bright:#fff8a0;--amber:#ffb800;--coffee-light:#cd853f}
  .bar{border:2px solid #fff}
  .kpi-card{border:2px solid #fff}
}
</style>
</head>
<body>
<div class="stage" role="img" aria-label="Infografía animada de ventas 2026 de La Molienda. Gráfico de barras mensual con KPIs totales.">
  <div class="steam" aria-hidden="true"><span></span><span></span><span></span><span></span><span></span></div>

  <header class="header">
    <h1 class="title">La Molienda <em>•</em> 2026</h1>
    <p class="subtitle">Tazas de café servidas mes a mes — Un año de aroma y crecimiento</p>
  </header>

  <main class="chart-wrap">
    <h2 class="chart-title">Ventas Mensuales — Tazas Servidas</h2>
    <div class="chart" role="graphics-document" aria-roledescription="gráfico de barras" aria-label="Ventas mensuales de 2026, de Enero a Diciembre. El mejor mes fue Julio con 4210 tazas.">
      <div class="y-axis" aria-hidden="true">
        <span>4200</span><span>3360</span><span>2520</span><span>1680</span><span>840</span>
      </div>
      <!-- Bars generated by JS -->
    </div>
  </main>

  <section class="kpi-section" aria-label="Indicadores clave del año 2026">
    <article class="kpi-card">
      <div class="kpi-label">Total Anual</div>
      <div class="kpi-value" id="kpi-total" data-target="37764">0</div>
      <div class="kpi-sublabel">tazas servidas en 2026</div>
    </article>
    <article class="kpi-card">
      <div class="kpi-label">Promedio Mensual</div>
      <div class="kpi-value" id="kpi-avg" data-target="3147">0</div>
      <div class="kpi-sublabel">tazas por mes en promedio</div>
    </article>
    <article class="kpi-card">
      <div class="kpi-label">Mejor Mes</div>
      <div class="kpi-value" id="kpi-best" data-target="4210">0</div>
      <div class="kpi-sublabel">Julio — 4.210 tazas</div>
    </article>
  </section>
</div>

<script>
(function(){
  'use strict';

  // Data
  const months = [
    {name:'Enero', val:2140},
    {name:'Febrero', val:2380},
    {name:'Marzo', val:2915},
    {name:'Abril', val:3060},
    {name:'Mayo', val:3475},
    {name:'Junio', val:3890},
    {name:'Julio', val:4210},
    {name:'Agosto', val:4035},
    {name:'Septiembre', val:3380},
    {name:'Octubre', val:2890},
    {name:'Noviembre', val:2520},
    {name:'Diciembre', val:2869}
  ];

  const maxVal = 4210;
  const chartH = 420; // CSS var --chart-h in px
  const chart = document.querySelector('.chart');
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Build bars
  months.forEach((m, i) => {
    const group = document.createElement('div');
    group.className = 'bar-group' + (m.val === maxVal ? ' best' : '');
    group.setAttribute('role', 'graphics-symbol');
    group.setAttribute('aria-roledescription', 'barra');
    group.setAttribute('aria-label', `${m.name}: ${m.val.toLocaleString('es-ES')} tazas`);

    const wrap = document.createElement('div');
    wrap.className = 'bar-wrap';

    const bar = document.createElement('div');
    bar.className = 'bar';
    bar.setAttribute('data-value', m.val);
    // Height proportional: (val / maxVal) * (chartH - 30) where 30px is bottom padding for axis
    const h = (m.val / maxVal) * (chartH - 30);
    bar.style.height = h + 'px';
    bar.style.setProperty('--bar-height', h + 'px'); // for potential CSS use

    wrap.appendChild(bar);
    group.appendChild(wrap);

    const valLabel = document.createElement('div');
    valLabel.className = 'bar-value';
    valLabel.textContent = m.val.toLocaleString('es-ES');
    group.appendChild(valLabel);

    const monthLabel = document.createElement('div');
    monthLabel.className = 'month-label';
    monthLabel.textContent = m.name;
    group.appendChild(monthLabel);

    chart.appendChild(group);
  });

  // Animate KPI counters
  function animateCounter(el, target, duration, delay, formatter) {
    if (prefersReduced) {
      el.textContent = formatter(target);
      return;
    }
    setTimeout(() => {
      const start = 0;
      const startTime = performance.now();
      function tick(now) {
        const progress = Math.min((now - startTime) / duration, 1);
        // Ease out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(start + (target - start) * eased);
        el.textContent = formatter(current);
        if (progress < 1) requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    }, delay);
  }

  const fmt = n => n.toLocaleString('es-ES');
  animateCounter(document.getElementById('kpi-total'), 37764, 1400, 1600, fmt);
  animateCounter(document.getElementById('kpi-avg'), 3147, 1200, 1800, fmt);
  animateCounter(document.getElementById('kpi-best'), 4210, 1000, 2000, fmt);

  // Optional: subtle parallax on mouse move for depth
  if (!prefersReduced) {
    const stage = document.querySelector('.stage');
    let raf = null;
    stage.addEventListener('mousemove', e => {
      if (raf) cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const cx = (e.clientX / window.innerWidth - 0.5) * 20;
        const cy = (e.clientY / window.innerHeight - 0.5) * 10;
        document.querySelector('.chart').style.transform = `translate(${cx * 0.3}px, ${cy * 0.2}px)`;
        document.querySelector('.kpi-section').style.transform = `translate(${cx * 0.15}px, ${cy * 0.1}px)`;
      });
    });
    stage.addEventListener('mouseleave', () => {
      if (raf) cancelAnimationFrame(raf);
      document.querySelector('.chart').style.transform = 'translate(0,0)';
      document.querySelector('.kpi-section').style.transform = 'translate(0,0)';
    });
  }
})();
</script>
</body>
</html>
```