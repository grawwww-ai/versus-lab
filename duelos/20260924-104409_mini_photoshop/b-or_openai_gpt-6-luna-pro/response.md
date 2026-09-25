```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Canvas — Mini Image Editor</title>
<style>
  :root {
    color-scheme: dark;
    --bg: #111318;
    --panel: #191c23;
    --panel-2: #20242d;
    --line: #2c303a;
    --muted: #8c93a3;
    --text: #edf0f6;
    --accent: #a78bfa;
    --accent-bright: #c2aaff;
    --green: #6fdbb0;
    --font: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    min-width: 760px;
    height: 100vh;
    overflow: hidden;
    background: var(--bg);
    color: var(--text);
    font: 13px/1.4 var(--font);
  }
  button, input, select { font: inherit; }
  button { color: inherit; }
  .app {
    display: grid;
    grid-template-rows: 56px 48px minmax(0, 1fr) 30px;
    height: 100vh;
  }
  .topbar {
    display: flex;
    align-items: center;
    gap: 18px;
    padding: 0 17px;
    background: #17191f;
    border-bottom: 1px solid var(--line);
  }
  .brand { display: flex; align-items: center; gap: 10px; min-width: 185px; }
  .brand-mark {
    display: grid;
    place-items: center;
    width: 31px;
    height: 31px;
    border-radius: 9px;
    color: #171321;
    background: linear-gradient(145deg, #d2bfff, #9a78ef);
    box-shadow: 0 4px 14px #9a78ef35;
  }
  .brand-name { font-size: 14px; font-weight: 700; letter-spacing: -.3px; }
  .brand-sub { margin-top: 1px; color: var(--muted); font-size: 10px; }
  .top-divider { height: 25px; width: 1px; background: var(--line); }
  .document-name { display: flex; align-items: center; gap: 8px; font-weight: 600; }
  .saved-dot { width: 6px; height: 6px; background: var(--green); border-radius: 50%; }
  .top-spacer { flex: 1; }
  .demo-pill {
    display: flex; align-items: center; gap: 7px;
    padding: 6px 10px; color: #d4c7ff; background: #a78bfa12;
    border: 1px solid #a78bfa35; border-radius: 20px;
    font-size: 10px; font-weight: 700; letter-spacing: .08em;
  }
  .live-dot { width: 6px; height: 6px; border-radius: 50%; background: #b59aff; box-shadow: 0 0 9px #b59aff; animation: pulse 1.5s infinite; }
  @keyframes pulse { 50% { opacity: .4; } }
  .top-button {
    display: flex; align-items: center; gap: 7px;
    padding: 7px 12px; border: 1px solid #3a344b; border-radius: 7px;
    color: #e5dcff; background: #292332; cursor: pointer;
  }
  .top-button:hover { background: #342b43; }
  .optionsbar {
    display: flex; align-items: center; gap: 17px;
    padding: 0 14px; background: #1b1e25; border-bottom: 1px solid var(--line);
  }
  .options-title { color: #d6caff; font-weight: 650; min-width: 61px; }
  .option-divider { width: 1px; height: 23px; background: var(--line); }
  .option-group { display: flex; align-items: center; gap: 8px; color: var(--muted); font-size: 11px; }
  .option-group b { color: #c8cbd4; font-weight: 500; }
  input[type="range"] { accent-color: var(--accent); width: 88px; height: 4px; }
  .range-value { width: 30px; color: #c5c8d1; text-align: right; font-variant-numeric: tabular-nums; }
  .color-wrap { position: relative; width: 25px; height: 25px; border: 1px solid #555965; border-radius: 6px; overflow: hidden; }
  input[type="color"] { position: absolute; inset: -5px; width: 35px; height: 35px; border: 0; padding: 0; cursor: pointer; }
  .text-input {
    width: 132px; padding: 5px 8px; border: 1px solid #343844; border-radius: 5px;
    color: var(--text); background: #14161c; outline: none;
  }
  .text-input:focus { border-color: var(--accent); }
  .workspace { display: grid; grid-template-columns: 58px minmax(0, 1fr) 282px; min-height: 0; }
  .toolrail {
    display: flex; flex-direction: column; align-items: center; gap: 5px;
    padding: 12px 7px; background: #191c23; border-right: 1px solid var(--line);
  }
  .tool-btn {
    position: relative; display: grid; place-items: center; width: 39px; height: 39px;
    color: #989eac; background: transparent; border: 1px solid transparent; border-radius: 8px;
    cursor: pointer; transition: .16s;
  }
  .tool-btn:hover { color: #e8e3f6; background: #272a33; }
  .tool-btn.active { color: #d4c4ff; background: #a78bfa20; border-color: #a78bfa4b; }
  .tool-btn.active::before { content: ""; position: absolute; left: -8px; height: 18px; width: 2px; border-radius: 2px; background: var(--accent); }
  .tool-separator { width: 27px; height: 1px; margin: 5px 0; background: var(--line); }
  svg { display: block; }
  .stage {
    position: relative; min-width: 0; min-height: 0; overflow: hidden;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    padding: 27px 28px 34px;
    background:
      radial-gradient(ellipse at 50% 42%, #242630 0%, #1b1d25 47%, #181a20 100%);
  }
  .stage-topline {
    position: absolute; top: 12px; left: 18px; right: 18px;
    display: flex; align-items: center; justify-content: space-between;
    color: #777e8d; font-size: 10px; letter-spacing: .04em;
  }
  .stage-topline strong { color: #aaaebb; font-weight: 500; }
  .canvas-shell {
    position: relative; display: grid; place-items: center;
    max-width: 100%; max-height: 100%;
    border: 1px solid #444752; border-radius: 3px; overflow: hidden;
    box-shadow: 0 18px 58px #0008, 0 0 0 1px #090a0d;
    background-color: #2a2d35;
    background-image: linear-gradient(45deg,#343740 25%,transparent 25%),linear-gradient(-45deg,#343740 25%,transparent 25%),linear-gradient(45deg,transparent 75%,#343740 75%),linear-gradient(-45deg,transparent 75%,#343740 75%);
    background-size: 18px 18px;
    background-position: 0 0,0 9px,9px -9px,-9px 0;
  }
  #mainCanvas {
    display: block; width: min(100%, 1000px); height: auto; max-height: 100%;
    cursor: none;
  }
  .art-cursor {
    position: absolute; z-index: 3; left: 0; top: 0; width: 24px; height: 24px;
    display: none; pointer-events: none; transform: translate(-50%, -50%);
    filter: drop-shadow(0 1px 2px #000);
  }
  .art-cursor.visible { display: block; }
  .art-cursor::before, .art-cursor::after { content: ""; position: absolute; background: #fff; opacity: .9; }
  .art-cursor::before { width: 1px; height: 24px; left: 11px; top: 0; }
  .art-cursor::after { height: 1px; width: 24px; top: 11px; left: 0; }
  .cursor-ring { position: absolute; inset: 3px; border: 1px solid white; border-radius: 50%; }
  .zoom-badge {
    position: absolute; right: 17px; bottom: 12px; color: #9096a4;
    font-size: 10px; padding: 4px 7px; border: 1px solid #30333c; border-radius: 5px;
    background: #191b21c9;
  }
  .right-panel {
    display: flex; flex-direction: column; min-height: 0; overflow-y: auto;
    background: #191c23; border-left: 1px solid var(--line);
  }
  .panel-section { padding: 14px 13px 12px; border-bottom: 1px solid var(--line); }
  .panel-heading { display: flex; align-items: center; justify-content: space-between; margin-bottom: 11px; }
  .panel-title { color: #e1e3ea; font-size: 11px; font-weight: 700; letter-spacing: .07em; text-transform: uppercase; }
  .subtle { color: var(--muted); font-size: 10px; }
  .icon-button {
    display: grid; place-items: center; width: 25px; height: 25px; padding: 0;
    border: 1px solid transparent; border-radius: 5px; background: transparent; color: #a1a7b4; cursor: pointer;
  }
  .icon-button:hover { background: #2a2d36; color: white; }
  .layer-list { display: flex; flex-direction: column; gap: 5px; }
  .layer-row {
    display: flex; align-items: center; gap: 7px; min-height: 49px; padding: 5px 6px;
    border: 1px solid transparent; border-radius: 7px; background: #20232b; cursor: pointer;
  }
  .layer-row:hover { background: #252832; }
  .layer-row.selected { background: #29243a; border-color: #8d71d34f; box-shadow: inset 2px 0 #a78bfa; }
  .eye-button { display: grid; place-items: center; flex: 0 0 20px; width: 20px; height: 24px; padding: 0; color: #a6adbb; background: none; border: 0; cursor: pointer; }
  .eye-button.hidden { color: #505561; }
  .thumb {
    display: block; flex: 0 0 43px; width: 43px; height: 32px;
    border: 1px solid #414550; border-radius: 3px; background: #30333a;
  }
  .layer-name { overflow: hidden; white-space: nowrap; text-overflow: ellipsis; color: #d7d9e0; font-size: 10px; }
  .layer-kind { margin-top: 2px; color: #777e8b; font-size: 9px; }
  .layer-order { display: flex; flex-direction: column; gap: 0; margin-left: auto; }
  .layer-order button { padding: 1px 3px; border: 0; color: #707786; background: transparent; cursor: pointer; line-height: 1; }
  .layer-order button:hover { color: #e2d8ff; }
  .layer-controls { display: flex; align-items: center; gap: 8px; margin-top: 11px; }
  .control-label { color: #9ba1af; font-size: 10px; white-space: nowrap; }
  .layer-controls input[type="range"] { flex: 1; width: auto; }
  select {
    min-width: 0; flex: 1; padding: 5px 7px; color: #cdd0d9;
    background: #22252d; border: 1px solid #343844; border-radius: 5px; outline: none; font-size: 10px;
  }
  select:focus { border-color: #8d71d3; }
  .blend-line { display: flex; align-items: center; gap: 8px; margin-top: 8px; }
  .filter-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; }
  .filter-btn {
    padding: 7px 4px; color: #aeb3bf; background: #22252d;
    border: 1px solid #323641; border-radius: 6px; cursor: pointer; font-size: 10px;
    transition: .15s;
  }
  .filter-btn:hover { color: #ede8fa; border-color: #66588b; background: #292633; }
  .filter-btn.active { color: #d7c9ff; border-color: #987bdc; background: #a78bfa1c; }
  .filter-note { margin-top: 9px; color: #787f8e; font-size: 9px; line-height: 1.5; }
  .activity {
    margin: 12px 13px 14px; padding: 10px;
    border: 1px solid #31313a; border-radius: 7px; background: #1d2027;
  }
  .activity-kicker { color: #a78bfa; font-size: 9px; font-weight: 700; letter-spacing: .09em; text-transform: uppercase; }
  .activity-text { margin-top: 4px; color: #aeb3bf; font-size: 10px; line-height: 1.5; }
  .statusbar {
    display: flex; align-items: center; gap: 14px; padding: 0 13px;
    background: #17191f; border-top: 1px solid var(--line); color: #838a98; font-size: 10px;
  }
  .status-tool { display: flex; align-items: center; gap: 6px; color: #cec0ff; }
  .status-spacer { flex: 1; }
  .status-sep { width: 1px; height: 12px; background: #363943; }
  @media (max-width: 980px) {
    .workspace { grid-template-columns: 54px minmax(0, 1fr) 245px; }
    .stage { padding-left: 14px; padding-right: 14px; }
    .brand { min-width: 160px; }
  }
</style>
</head>
<body>
<div class="app">
  <header class="topbar">
    <div class="brand">
      <div class="brand-mark" aria-hidden="true">
        <svg width="19" height="19" viewBox="0 0 24 24" fill="none">
          <path d="M4 17.5 9.3 11l3.1 3.5 2.4-2.8L20 18H4Z" fill="currentColor" opacity=".85"/>
          <circle cx="16.5" cy="7.5" r="2.4" fill="currentColor"/>
          <path d="M4 4.5h16v15H4z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
        </svg>
      </div>
      <div><div class="brand-name">Canvas</div><div class="brand-sub">CREATIVE STUDIO</div></div>
    </div>
    <div class="top-divider"></div>
    <div class="document-name"><span>Quiet morning.psd</span><span class="saved-dot"></span></div>
    <div class="top-spacer"></div>
    <div class="demo-pill"><span class="live-dot"></span> LIVE DEMO</div>
    <button class="top-button" id="exportButton" title="Download the composite as a PNG">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M12 3v11m0 0 4-4m-4 4-4-4M5 16v4h14v-4" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>
      Export
    </button>
  </header>

  <div class="optionsbar">
    <div class="options-title" id="toolName">Brush</div>
    <div class="option-divider"></div>
    <div class="option-group"><span>Color</span><span class="color-wrap"><input id="brushColor" type="color" value="#f5c879" aria-label="Brush color"></span></div>
    <div class="option-group"><span>Size</span><input id="brushSize" type="range" min="2" max="90" value="18"><span class="range-value" id="sizeValue">18 px</span></div>
    <div class="option-group"><span>Flow</span><input id="brushFlow" type="range" min="5" max="100" value="82"><span class="range-value" id="flowValue">82%</span></div>
    <div class="option-divider"></div>
    <div class="option-group"><span>Text</span><input class="text-input" id="textInput" value="Your text" aria-label="Text to add"></div>
    <div class="top-spacer"></div>
    <span class="subtle" id="toolHint">Drag to paint</span>
  </div>

  <main class="workspace">
    <nav class="toolrail" aria-label="Tools">
      <button class="tool-btn active" data-tool="brush" title="Brush (B)" aria-label="Brush">
        <svg width="19" height="19" viewBox="0 0 24 24" fill="none"><path d="m14.5 5.5 4 4M4.5 19.5c3.4-.2 5-.9 7.1-3l7-7a2.83 2.83 0 0 0-4-4l-7 7c-2.1 2.1-2.8 3.7-3.1 7Z" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/><path d="M4.5 19.5c1.8-1.4 3.2-1.4 4.2-.4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
      </button>
      <button class="tool-btn" data-tool="eraser" title="Eraser (E)" aria-label="Eraser">
        <svg width="19" height="19" viewBox="0 0 24 24" fill="none"><path d="m7.5 19-4-4a2.1 2.1 0 0 1 0-3l7.8-7.8a2.1 2.1 0 0 1 3 0l6.2 6.2a2.1 2.1 0 0 1 0 3L14 20H8.5L5 16.5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/><path d="m9 9 7 7" stroke="currentColor" stroke-width="1.5"/></svg>
      </button>
      <button class="tool-btn" data-tool="shape" title="Ellipse shape" aria-label="Shape">
        <svg width="19" height="19" viewBox="0 0 24 24" fill="none"><ellipse cx="12" cy="12" rx="8.5" ry="6.5" stroke="currentColor" stroke-width="1.7"/><path d="M5.5 12h13" stroke="currentColor" stroke-width="1" stroke-dasharray="2 2" opacity=".7"/></svg>
      </button>
      <button class="tool-btn" data-tool="text" title="Text" aria-label="Text">
        <svg width="19" height="19" viewBox="0 0 24 24" fill="none"><path d="M4.5 6V4.5h15V6M12 4.5v15M8.5 19.5h7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </button>
      <div class="tool-separator"></div>
      <button class="tool-btn" id="addLayerTool" title="Add a new layer" aria-label="Add layer">
        <svg width="19" height="19" viewBox="0 0 24 24" fill="none"><path d="m12 3 8 4.5-8 4.5-8-4.5L12 3Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/><path d="m4 12 8 4.5 8-4.5M4 16.5 12 21l8-4.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </button>
    </nav>

    <section class="stage" id="stage" aria-label="Image canvas">
      <div class="stage-topline"><span>DOCUMENT <strong>· 1000 × 620 px</strong></span><span id="stageLayerName">3 LAYERS</span></div>
      <div class="canvas-shell" id="canvasShell">
        <canvas id="mainCanvas" width="1000" height="620" aria-label="Editable image"></canvas>
        <div class="art-cursor" id="artCursor"><span class="cursor-ring"></span></div>
      </div>
      <div class="zoom-badge">100%</div>
    </section>

    <aside class="right-panel">
      <section class="panel-section">
        <div class="panel-heading">
          <span class="panel-title">Layers</span>
          <div style="display:flex;align-items:center;gap:5px">
            <span class="subtle" id="layerCount">3 layers</span>
            <button class="icon-button" id="addLayerButton" title="Add layer" aria-label="Add layer">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none"><path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
            </button>
          </div>
        </div>
        <div class="layer-list" id="layerList"></div>
        <div class="layer-controls">
          <span class="control-label">Opacity</span>
          <input id="layerOpacity" type="range" min="0" max="100" value="100" aria-label="Layer opacity">
          <span class="range-value" id="layerOpacityValue">100%</span>
        </div>
        <div class="blend-line">
          <span class="control-label">Blend mode</span>
          <select id="blendMode" aria-label="Blend mode">
            <option value="source-over">Normal</option>
            <option value="multiply">Multiply</option>
            <option value="screen">Screen</option>
            <option value="overlay">Overlay</option>
            <option value="soft-light">Soft light</option>
            <option value="darken">Darken</option>
            <option value="lighten">Lighten</option>
          </select>
        </div>
      </section>

      <section class="panel-section">
        <div class="panel-heading"><span class="panel-title">Live adjustments</span><span class="subtle">Preview</span></div>
        <div class="filter-grid">
          <button class="filter-btn" data-filter="blur">Blur</button>
          <button class="filter-btn" data-filter="brightness">Bright</button>
          <button class="filter-btn" data-filter="contrast">Contrast</button>
          <button class="filter-btn" data-filter="sepia">Sepia</button>
          <button class="filter-btn" data-filter="invert">Invert</button>
          <button class="filter-btn" id="resetFilters">Reset</button>
        </div>
        <div class="filter-note" id="filterNote">Choose an adjustment to preview it on the full composite.</div>
      </section>

      <div class="activity">
        <div class="activity-kicker">Studio activity</div>
        <div class="activity-text" id="activityText">Setting up the canvas…</div>
      </div>
    </aside>
  </main>

  <footer class="statusbar">
    <span class="status-tool"><span id="statusToolIcon">✦</span><span id="statusTool">Brush</span></span>
    <span class="status-sep"></span>
    <span id="statusMessage">Ready</span>
    <span class="status-spacer"></span>
    <span id="pointerPosition">X: — &nbsp; Y: —</span>
    <span class="status-sep"></span>
    <span>RGB / 8</span>
    <span class="status-sep"></span>
    <span>100%</span>
  </footer>
</div>

<script>
(() => {
  "use strict";

  const W = 1000, H = 620;
  const mainCanvas = document.getElementById("mainCanvas");
  const mainCtx = mainCanvas.getContext("2d");
  const stage = document.getElementById("stage");
  const canvasShell = document.getElementById("canvasShell");
  const cursorEl = document.getElementById("artCursor");
  const layerListEl = document.getElementById("layerList");
  const activityEl = document.getElementById("activityText");
  const colorInput = document.getElementById("brushColor");
  const sizeInput = document.getElementById("brushSize");
  const flowInput = document.getElementById("brushFlow");
  const filterValues = { blur: 0, brightness: 1, contrast: 1, sepia: 0, invert: 0 };
  const filterLabels = { blur: "Blur", brightness: "Brightness", contrast: "Contrast", sepia: "Sepia", invert: "Invert" };

  let layers = [];
  let selectedId = null;
  let activeTool = "brush";
  let drawing = false;
  let lastPoint = null;
  let shapeStart = null;
  let shapePreview = null;
  let brushOpacity = Number(flowInput.value) / 100;
  let demoRunning = true;
  let layerCounter = 0;

  const makeLayer = (name, kind = "Pixel layer") => {
    const canvas = document.createElement("canvas");
    canvas.width = W; canvas.height = H;
    return { id: "layer-" + (++layerCounter), name, kind, canvas, visible: true, opacity: 1, blend: "source-over" };
  };

  function paintLandscape() {
    const base = makeLayer("Landscape · base", "Background");
    const b = base.canvas.getContext("2d");

    // Sky
    let sky = b.createLinearGradient(0, 0, 0, 430);
    sky.addColorStop(0, "#293f62");
    sky.addColorStop(.48, "#71849a");
    sky.addColorStop(1, "#f1b77e");
    b.fillStyle = sky;
    b.fillRect(0, 0, W, H);

    // Warm horizon glow
    const glow = b.createRadialGradient(700, 290, 8, 700, 290, 430);
    glow.addColorStop(0, "rgba(255,219,160,.68)");
    glow.addColorStop(.35, "rgba(248,181,135,.25)");
    glow.addColorStop(1, "rgba(248,181,135,0)");
    b.fillStyle = glow; b.fillRect(180, 0, 820, 560);

    // Sun
    const sunGlow = b.createRadialGradient(705, 242, 15, 705, 242, 95);
    sunGlow.addColorStop(0, "rgba(255,238,191,.95)");
    sunGlow.addColorStop(.38, "rgba(255,219,165,.44)");
    sunGlow.addColorStop(1, "rgba(255,219,165,0)");
    b.fillStyle = sunGlow; b.fillRect(590, 125, 230, 230);
    b.beginPath(); b.arc(705, 242, 36, 0, Math.PI * 2); b.fillStyle = "#ffedc6"; b.fill();

    // Distant ridge
    b.beginPath(); b.moveTo(0, 365);
    [[0,330],[90,285],[175,326],[260,257],[344,314],[430,270],[510,315],[610,250],[710,310],[790,270],[885,319],[1000,267],[1000,420],[0,420]].forEach(p => b.lineTo(p[0],p[1]));
    b.closePath();
    const ridge = b.createLinearGradient(0, 245, 0, 430);
    ridge.addColorStop(0, "#596c7e"); ridge.addColorStop(1, "#35485a");
    b.fillStyle = ridge; b.fill();

    // Water plane
    const water = b.createLinearGradient(0, 370, 0, H);
    water.addColorStop(0, "#536e7b"); water.addColorStop(.22, "#405e6e"); water.addColorStop(1, "#203c4c");
    b.fillStyle = water; b.fillRect(0, 375, W, H - 375);

    // Far shore silhouette
    b.beginPath(); b.moveTo(0, 405);
    [[0,393],[130,386],[240,397],[355,379],[470,392],[590,380],[710,397],[830,381],[1000,394],[1000,423],[0,423]].forEach(p => b.lineTo(p[0],p[1]));
    b.closePath(); b.fillStyle = "#314a51"; b.fill();

    // Small distant tree silhouettes
    for (let i = 0; i < 32; i++) {
      const x = 20 + i * 31 + Math.sin(i * 12.4) * 10;
      const y = 393 + Math.sin(i * 3.1) * 5;
      const h = 18 + (i * 13 % 24);
      b.fillStyle = i % 3 ? "#304950" : "#3b5558";
      b.beginPath(); b.moveTo(x, y - h); b.lineTo(x - 9, y + 2); b.lineTo(x + 8, y + 2); b.closePath(); b.fill();
    }

    // Soft atmospheric streaks in sky
    b.globalAlpha = .12;
    for (let i = 0; i < 9; i++) {
      b.beginPath(); b.ellipse(110 + i * 103, 150 + (i % 3) * 35, 80 + (i % 4) * 12, 2, -.04, 0, Math.PI * 2);
      b.fillStyle = "#fff0d8"; b.fill();
    }
    b.globalAlpha = 1;

    // Middle atmosphere / reflection layer
    const mid = makeLayer("Atmosphere & reflections", "Atmosphere");
    const m = mid.canvas.getContext("2d");

    // Painterly clouds
    const cloud = (x, y, sx, sy, alpha) => {
      m.save(); m.globalAlpha = alpha;
      const g = m.createLinearGradient(x, y - sy, x, y + sy);
      g.addColorStop(0, "#f2dfc8"); g.addColorStop(1, "#b8b4b5");
      m.fillStyle = g;
      m.beginPath();
      m.ellipse(x, y, sx, sy, 0, 0, Math.PI * 2);
      m.ellipse(x - sx * .5, y + sy * .1, sx * .52, sy * .68, 0, 0, Math.PI * 2);
      m.ellipse(x + sx * .45, y + sy * .12, sx * .48, sy * .65, 0, 0, Math.PI * 2);
      m.fill(); m.restore();
    };
    cloud(185, 123, 98, 14, .25);
    cloud(426, 177, 85, 10, .19);
    cloud(850, 116, 112, 13, .22);

    // Sunlit water reflection
    const reflection = m.createLinearGradient(0, 390, 0, 590);
    reflection.addColorStop(0, "rgba(255,212,157,.46)");
    reflection.addColorStop(1, "rgba(255,196,140,0)");
    m.fillStyle = reflection;
    m.beginPath(); m.moveTo(661, 390); m.lineTo(748, 390); m.lineTo(830, 590); m.lineTo(586, 590); m.closePath(); m.fill();

    for (let i = 0; i < 33; i++) {
      const y = 412 + i * 5.2;
      const spread = 14 + i * 2.1;
      const x = 704 + Math.sin(i * 1.7) * (7 + i * .9);
      m.globalAlpha = .12 + ((i * 7) % 8) / 55;
      m.fillStyle = i % 3 ? "#f7d5a7" : "#d5b9a0";
      m.fillRect(x - spread / 2, y, spread, i % 4 === 0 ? 2 : 1);
    }
    m.globalAlpha = 1;

    // Foreground details layer
    const fore = makeLayer("Pine shore · foreground", "Details");
    const f = fore.canvas.getContext("2d");

    // Dark banks on both edges
    f.beginPath(); f.moveTo(0, 388); f.lineTo(98, 391); f.lineTo(155, 414); f.lineTo(235, 426); f.lineTo(285, 620); f.lineTo(0, 620); f.closePath();
    const bankL = f.createLinearGradient(0, 400, 260, 590); bankL.addColorStop(0, "#283f3e"); bankL.addColorStop(1, "#182e30");
    f.fillStyle = bankL; f.fill();
    f.beginPath(); f.moveTo(1000, 384); f.lineTo(922, 393); f.lineTo(865, 420); f.lineTo(800, 435); f.lineTo(753, 620); f.lineTo(1000, 620); f.closePath();
    const bankR = f.createLinearGradient(1000, 390, 770, 600); bankR.addColorStop(0, "#2d4540"); bankR.addColorStop(1, "#182f30");
    f.fillStyle = bankR; f.fill();

    // Pine trees, layered silhouettes
    function pine(x, baseY, h, color, width) {
      f.fillStyle = color;
      f.fillRect(x - width * .07, baseY - h * .18, width * .14, h * .2);
      for (let j = 0; j < 4; j++) {
        const yy = baseY - h + j * h * .21;
        const ww = width * (0.38 + j * .17);
        f.beginPath(); f.moveTo(x, yy); f.lineTo(x - ww, yy + h * .35); f.lineTo(x + ww, yy + h * .35); f.closePath(); f.fill();
      }
    }
    pine(74, 445, 156, "#233a37", 84);
    pine(143, 431, 112, "#29413b", 67);
    pine(915, 440, 170, "#203835", 91);
    pine(852, 429, 112, "#2b433c", 66);
    pine(972, 452, 115, "#29413a", 65);

    // Foreground grasses and warm flecks
    for (let i = 0; i < 150; i++) {
      const left = i < 83;
      const x = left ? 6 + (i * 37 % 260) : 760 + (i * 41 % 235);
      const y = 470 + (i * 23 % 170);
      f.strokeStyle = i % 4 === 0 ? "#bc9a69" : (i % 3 === 0 ? "#6d8466" : "#3e5a4d");
      f.globalAlpha = .28 + (i % 5) * .08;
      f.lineWidth = i % 5 === 0 ? 2 : 1;
      f.beginPath(); f.moveTo(x, y); f.lineTo(x + (left ? 1 : -1) * (3 + i % 8), y - 7 - i % 13); f.stroke();
    }
    f.globalAlpha = 1;

    layers = [base, mid, fore];
    selectedId = fore.id;
    renderAll();
  }

  function selectedLayer() { return layers.find(l => l.id === selectedId); }
  function getContext(layer) { return layer.canvas.getContext("2d"); }

  function renderComposite() {
    mainCtx.clearRect(0, 0, W, H);
    for (const layer of layers) {
      if (!layer.visible) continue;
      mainCtx.save();
      mainCtx.globalAlpha = layer.opacity;
      mainCtx.globalCompositeOperation = layer.blend;
      mainCtx.drawImage(layer.canvas, 0, 0);
      mainCtx.restore();
    }
  }

  function updateFilterPreview() {
    const f = filterValues;
    mainCanvas.style.filter = `blur(${f.blur}px) brightness(${f.brightness}) contrast(${f.contrast}) sepia(${f.sepia}) invert(${f.invert})`;
    document.querySelectorAll("[data-filter]").forEach(btn => {
      const key = btn.dataset.filter;
      btn.classList.toggle("active", key === "blur" ? f.blur > 0 : key === "brightness" ? f.brightness !== 1 : key === "contrast" ? f.contrast !== 1 : f[key] > 0);
    });
  }

  function renderLayers() {
    layerListEl.innerHTML = "";
    [...layers].reverse().forEach((layer, reverseIndex) => {
      const actualIndex = layers.length - 1 - reverseIndex;
      const row = document.createElement("div");
      row.className = "layer-row" + (layer.id === selectedId ? " selected" : "");
      row.dataset.id = layer.id;
      row.innerHTML = `
        <button class="eye-button ${layer.visible ? "" : "hidden"}" data-action="visibility" title="${layer.visible ? "Hide" : "Show"} layer" aria-label="${layer.visible ? "Hide" : "Show"} layer">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none"><path d="M2.5 12s3.4-6 9.5-6 9.5 6 9.5 6-3.4 6-9.5 6-9.5-6-9.5-6Z" stroke="currentColor" stroke-width="1.6"/><circle cx="12" cy="12" r="2.7" stroke="currentColor" stroke-width="1.6"/></svg>
        </button>
        <canvas class="thumb" width="86" height="64"></canvas>
        <div style="min-width:0;flex:1"><div class="layer-name">${escapeHTML(layer.name)}</div><div class="layer-kind">${escapeHTML(layer.kind)}</div></div>
        <div class="layer-order">
          <button data-action="up" title="Move layer up" aria-label="Move layer up">⌃</button>
          <button data-action="down" title="Move layer down" aria-label="Move layer down">⌄</button>
        </div>`;
      layerListEl.appendChild(row);
      const thumb = row.querySelector("canvas");
      const t = thumb.getContext("2d");
      t.fillStyle = "#252831"; t.fillRect(0,0,86,64);
      t.globalAlpha = layer.visible ? 1 : .25;
      t.drawImage(layer.canvas, 0, 0, 86, 64);
    });
    document.getElementById("layerCount").textContent = `${layers.length} layer${layers.length === 1 ? "" : "s"}`;
    document.getElementById("stageLayerName").textContent = `${layers.length} LAYERS`;
    const sel = selectedLayer();
    document.getElementById("layerOpacity").value = sel ? Math.round(sel.opacity * 100) : 100;
    document.getElementById("layerOpacityValue").textContent = `${sel ? Math.round(sel.opacity * 100) : 100}%`;
    document.getElementById("blendMode").value = sel ? sel.blend : "source-over";
  }

  function renderAll() {
    renderComposite();
    renderLayers();
    updateFilterPreview();
  }

  function escapeHTML(str) {
    return String(str).replace(/[&<>"']/g, ch => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[ch]));
  }

  const toolInfo = {
    brush: ["Brush", "Drag to paint", "✦"],
    eraser: ["Eraser", "Drag to erase on the active layer", "⌫"],
    shape: ["Ellipse", "Drag to draw an ellipse", "◯"],
    text: ["Text", "Click the canvas to place your text", "T"]
  };
  function setTool(tool) {
    activeTool = tool;
    document.querySelectorAll(".tool-btn[data-tool]").forEach(b => b.classList.toggle("active", b.dataset.tool === tool));
    const info = toolInfo[tool];
    document.getElementById("toolName").textContent = info[0];
    document.getElementById("toolHint").textContent = info[1];
    document.getElementById("statusTool").textContent = info[0];
    document.getElementById("statusToolIcon").textContent = info[2];
    setStatus(`${info[0]} tool selected`);
  }
  function setStatus(message) { document.getElementById("statusMessage").textContent = message; }
  function setActivity(message) { activityEl.textContent = message; }

  document.querySelectorAll(".tool-btn[data-tool]").forEach(btn => btn.addEventListener("click", () => setTool(btn.dataset.tool)));
  document.addEventListener("keydown", e => {
    if (e.target.matches("input, textarea, select")) return;
    const key = e.key.toLowerCase();
    if (key === "b") setTool("brush");
    if (key === "e") setTool("eraser");
    if (key === "t") setTool("text");
  });

  function addLayer(name) {
    const layer = makeLayer(name || `Layer ${layers.length + 1}`);
    layers.push(layer);
    selectedId = layer.id;
    renderAll();
    setStatus(`Added ${layer.name}`);
    return layer;
  }

  document.getElementById("addLayerButton").addEventListener("click", () => addLayer());
  document.getElementById("addLayerTool").addEventListener("click", () => addLayer());

  layerListEl.addEventListener("click", e => {
    const row = e.target.closest(".layer-row");
    if (!row) return;
    const layer = layers.find(l => l.id === row.dataset.id);
    if (!layer) return;
    const action = e.target.closest("[data-action]")?.dataset.action;
    if (!action) {
      selectedId = layer.id;
      renderLayers();
      setStatus(`Selected ${layer.name}`);
      return;
    }
    if (action === "visibility") {
      layer.visible = !layer.visible;
      setStatus(`${layer.visible ? "Showing" : "Hiding"} ${layer.name}`);
      renderAll();
      return;
    }
    const index = layers.indexOf(layer);
    const next = action === "up" ? index + 1 : index - 1;
    if (next < 0 || next >= layers.length) return;
    [layers[index], layers[next]] = [layers[next], layers[index]];
    renderAll();
    setStatus(`Reordered ${layer.name}`);
  });

  document.getElementById("layerOpacity").addEventListener("input", e => {
    const layer = selectedLayer(); if (!layer) return;
    layer.opacity = Number(e.target.value) / 100;
    document.getElementById("layerOpacityValue").textContent = `${e.target.value}%`;
    renderComposite();
  });
  document.getElementById("layerOpacity").addEventListener("change", renderLayers);
  document.getElementById("blendMode").addEventListener("change", e => {
    const layer = selectedLayer(); if (!layer) return;
    layer.blend = e.target.value; renderComposite(); setStatus(`${layer.name}: ${e.target.options[e.target.selectedIndex].text}`);
  });

  document.querySelectorAll("[data-filter]").forEach(btn => btn.addEventListener("click", () => {
    Object.keys(filterValues).forEach(k => filterValues[k] = k === "brightness" || k === "contrast" ? 1 : 0);
    const key = btn.dataset.filter;
    if (key === "blur") filterValues.blur = 2.2;
    if (key === "brightness") filterValues.brightness = 1.23;
    if (key === "contrast") filterValues.contrast = 1.28;
    if (key === "sepia") filterValues.sepia = .72;
    if (key === "invert") filterValues.invert = 1;
    updateFilterPreview();
    document.getElementById("filterNote").textContent = `${filterLabels[key]} preview is live on the composite.`;
    setStatus(`Live ${filterLabels[key].toLowerCase()} adjustment applied`);
    setActivity(`Previewing a live ${filterLabels[key].toLowerCase()} adjustment on the full image.`);
  }));
  document.getElementById("resetFilters").addEventListener("click", () => {
    Object.keys(filterValues).forEach(k => filterValues[k] = k === "brightness" || k === "contrast" ? 1 : 0);
    updateFilterPreview();
    document.getElementById("filterNote").textContent = "Choose an adjustment to preview it on the full composite.";
    setStatus("Adjustments reset");
  });

  sizeInput.addEventListener("input", () => document.getElementById("sizeValue").textContent = `${sizeInput.value} px`);
  flowInput.addEventListener("input", () => {
    brushOpacity = Number(flowInput.value) / 100;
    document.getElementById("flowValue").textContent = `${flowInput.value}%`;
  });

  function canvasPoint(event) {
    const rect = mainCanvas.getBoundingClientRect();
    return { x: (event.clientX - rect.left) * W / rect.width, y: (event.clientY - rect.top) * H / rect.height };
  }
  function moveCursor(x, y, visible = true) {
    const cRect = mainCanvas.getBoundingClientRect();
    const shellRect = canvasShell.getBoundingClientRect();
    cursorEl.style.left = `${cRect.left - shellRect.left + (x / W) * cRect.width}px`;
    cursorEl.style.top = `${cRect.top - shellRect.top + (y / H) * cRect.height}px`;
    cursorEl.classList.toggle("visible", visible);
  }
  function paintLine(layer, from, to, erasing = false, demo = false) {
    const ctx = getContext(layer);
    ctx.save();
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.lineWidth = Number(sizeInput.value);
    ctx.globalAlpha = brushOpacity;
    if (erasing) ctx.globalCompositeOperation = "destination-out";
    else { ctx.globalCompositeOperation = "source-over"; ctx.strokeStyle = colorInput.value; }
    ctx.beginPath(); ctx.moveTo(from.x, from.y); ctx.lineTo(to.x, to.y); ctx.stroke();
    ctx.restore();
    if (!demo) { renderComposite(); refreshSelectedThumbnail(layer.id); }
  }
  function paintDot(layer, p) {
    const ctx = getContext(layer);
    ctx.save(); ctx.fillStyle = colorInput.value; ctx.globalAlpha = brushOpacity;
    ctx.beginPath(); ctx.arc(p.x, p.y, Math.max(1, Number(sizeInput.value) / 2), 0, Math.PI * 2); ctx.fill(); ctx.restore();
  }
  function refreshSelectedThumbnail(id) {
    const row = layerListEl.querySelector(`.layer-row[data-id="${id}"]`);
    if (!row) return;
    const layer = layers.find(l => l.id === id);
    const t = row.querySelector("canvas").getContext("2d");
    t.clearRect(0,0,86,64); t.fillStyle = "#252831"; t.fillRect(0,0,86,64); t.drawImage(layer.canvas,0,0,86,64);
  }

  mainCanvas.addEventListener("pointerdown", e => {
    e.preventDefault();
    mainCanvas.setPointerCapture(e.pointerId);
    const p = canvasPoint(e);
    moveCursor(p.x, p.y);
    document.getElementById("pointerPosition").textContent = `X: ${Math.round(p.x)}  Y: ${Math.round(p.y)}`;
    if (activeTool === "text") { placeText(p, document.getElementById("textInput").value); return; }
    const layer = selectedLayer(); if (!layer) return;
    if (activeTool === "shape") { drawing = true; shapeStart = p; shapePreview = null; return; }
    drawing = true; lastPoint = p;
    if (activeTool === "brush") paintDot(layer, p);
    else if (activeTool === "eraser") paintLine(layer, p, {x:p.x+.01,y:p.y+.01}, true);
    renderComposite();
  });
  mainCanvas.addEventListener("pointermove", e => {
    const p = canvasPoint(e);
    moveCursor(p.x, p.y);
    document.getElementById("pointerPosition").textContent = `X: ${Math.round(p.x)}  Y: ${Math.round(p.y)}`;
    if (!drawing || !lastPoint) return;
    const layer = selectedLayer(); if (!layer) return;
    if (activeTool === "brush") paintLine(layer, lastPoint, p);
    if (activeTool === "eraser") paintLine(layer, lastPoint, p, true);
    if (activeTool === "shape") { shapePreview = p; renderComposite(); drawShapePreview(layer, shapeStart, p); }
    lastPoint = p;
  });
  function finishDrawing(e) {
    if (!drawing) return;
    const layer = selectedLayer();
    if (activeTool === "shape" && layer && shapeStart) {
      const p = canvasPoint(e);
      drawEllipse(layer, shapeStart, p);
      renderComposite(); refreshSelectedThumbnail(layer.id);
      setStatus("Ellipse added to active layer");
    }
    drawing = false; lastPoint = null; shapeStart = null; shapePreview = null;
  }
  mainCanvas.addEventListener("pointerup", finishDrawing);
  mainCanvas.addEventListener("pointercancel", finishDrawing);
  mainCanvas.addEventListener("pointerleave", () => { if (!drawing) cursorEl.classList.remove("visible"); });
  mainCanvas.addEventListener("pointerenter", e => { const p = canvasPoint(e); moveCursor(p.x,p.y); });

  function drawEllipse(layer, start, end) {
    const ctx = getContext(layer);
    ctx.save(); ctx.globalAlpha = brushOpacity; ctx.strokeStyle = colorInput.value;
    ctx.lineWidth = Math.max(2, Number(sizeInput.value) / 3);
    ctx.beginPath(); ctx.ellipse((start.x+end.x)/2,(start.y+end.y)/2,Math.max(1,Math.abs(end.x-start.x)/2),Math.max(1,Math.abs(end.y-start.y)/2),0,0,Math.PI*2); ctx.stroke(); ctx.restore();
  }
  function drawShapePreview(layer, start, end) {
    const ctx = mainCtx;
    ctx.save(); ctx.strokeStyle = colorInput.value; ctx.globalAlpha = .8;
    ctx.lineWidth = Math.max(2, Number(sizeInput.value) / 3);
    ctx.beginPath(); ctx.ellipse((start.x+end.x)/2,(start.y+end.y)/2,Math.max(1,Math.abs(end.x-start.x)/2),Math.max(1,Math.abs(end.y-start.y)/2),0,0,Math.PI*2); ctx.stroke(); ctx.restore();
  }

  function placeText(point, text) {
    const layer = selectedLayer(); if (!layer || !text.trim()) return;
    const ctx = getContext(layer);
    ctx.save();
    const fontSize = Math.max(18, Number(sizeInput.value) * 2);
    ctx.font = `600 ${fontSize}px ${getComputedStyle(document.body).fontFamily}`;
    ctx.textBaseline = "top";
    ctx.shadowColor = "rgba(15,25,35,.7)"; ctx.shadowBlur = 8; ctx.shadowOffsetY = 2;
    ctx.fillStyle = colorInput.value; ctx.globalAlpha = brushOpacity;
    ctx.fillText(text, point.x, point.y);
    ctx.restore();
    renderComposite(); refreshSelectedThumbnail(layer.id);
    setStatus(`Added text to ${layer.name}`);
  }

  document.getElementById("exportButton").addEventListener("click", () => {
    const output = document.createElement("canvas"); output.width = W; output.height = H;
    const ctx = output.getContext("2d");
    layers.forEach(layer => {
      if (!layer.visible) return;
      ctx.save(); ctx.globalAlpha = layer.opacity; ctx.globalCompositeOperation = layer.blend; ctx.drawImage(layer.canvas,0,0); ctx.restore();
    });
    const link = document.createElement("a"); link.download = "quiet-morning.png"; link.href = output.toDataURL("image/png"); link.click();
    setStatus("Composite exported as PNG");
  });

  // A small self-running tour: paint, create a layer, add a label, preview a filter,
  // toggle a layer, then demonstrate layer ordering. All actions remain editable.
  const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
  function setDemoBrush(color, size, flow = 82) {
    colorInput.value = color; sizeInput.value = size; flowInput.value = flow;
    brushOpacity = flow / 100;
    document.getElementById("sizeValue").textContent = `${size} px`;
    document.getElementById("flowValue").textContent = `${flow}%`;
  }
  function animateDemoStroke(points, duration = 850) {
    return new Promise(resolve => {
      const layer = selectedLayer();
      if (!layer) return resolve();
      let segment = 0, segmentStart = performance.now(), prior = points[0];
      moveCursor(prior.x, prior.y);
      paintDot(layer, prior);
      const step = now => {
        const target = points[segment + 1];
        const elapsed = now - segmentStart;
        const t = Math.min(1, elapsed / duration);
        const eased = t * (2 - t);
        const current = { x: points[segment].x + (target.x - points[segment].x) * eased, y: points[segment].y + (target.y - points[segment].y) * eased };
        moveCursor(current.x, current.y);
        paintLine(layer, prior, current, false, true);
        prior = current;
        if (t >= 1) {
          segment++;
          if (segment >= points.length - 1) {
            renderComposite(); refreshSelectedThumbnail(layer.id);
            resolve(); return;
          }
          segmentStart = now; prior = points[segment];
        }
        requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    });
  }
  function demoTextLabel(layer) {
    const ctx = getContext(layer);
    ctx.save();
    // Fine translucent title plate gives the label a polished editorial treatment.
    ctx.fillStyle = "rgba(23,31,39,.48)";
    ctx.beginPath(); ctx.roundRect(526, 306, 286, 72, 5); ctx.fill();
    ctx.fillStyle = "#f8e8ce";
    ctx.font = "600 23px Inter, system-ui, sans-serif";
    ctx.textBaseline = "top"; ctx.letterSpacing = "3px";
    ctx.fillText("GOLDEN HOUR", 545, 319);
    ctx.fillStyle = "rgba(248,232,206,.72)";
    ctx.font = "500 10px Inter, system-ui, sans-serif"; ctx.letterSpacing = "2px";
    ctx.fillText("FIELD NOTES  /  04", 547, 352);
    ctx.restore();
  }

  async function runDemo() {
    await wait(900);
    setActivity("Painting warm light across the shoreline with the brush tool.");
    setStatus("Demo · painting on the foreground layer");
    setTool("brush"); setDemoBrush("#ffd48e", 17, 76);
    await animateDemoStroke([{x:336,y:431},{x:383,y:421},{x:428,y:424},{x:477,y:414},{x:526,y:419}], 720);
    await wait(180);
    setDemoBrush("#f5a978", 9, 58);
    await animateDemoStroke([{x:404,y:447},{x:446,y:441},{x:482,y:445},{x:521,y:437}], 620);

    await wait(550);
    const fresh = addLayer("Light accents · demo");
    setActivity("A fresh paint layer is added above the artwork, ready for non-destructive edits.");
    setStatus("Demo · new transparent layer added");
    setTool("brush"); setDemoBrush("#ffe2a3", 22, 68);
    await animateDemoStroke([{x:365,y:400},{x:419,y:395},{x:472,y:402},{x:521,y:396},{x:560,y:400}], 850);
    setDemoBrush("#c6d9cf", 8, 65);
    await animateDemoStroke([{x:336,y:460},{x:379,y:457},{x:416,y:462}], 550);

    await wait(450);
    setTool("text");
    document.getElementById("textInput").value = "GOLDEN HOUR";
    colorInput.value = "#f8e8ce";
    moveCursor(545, 320);
    setActivity("Adding an editorial text label directly onto the new layer.");
    setStatus("Demo · placing a text label");
    await wait(450);
    demoTextLabel(fresh);
    renderComposite(); refreshSelectedThumbnail(fresh.id);
    setStatus("Text label added to Light accents · demo");

    await wait(1100);
    document.querySelector('[data-filter="sepia"]').click();
    setActivity("A live sepia preview is applied to the complete composite.");
    await wait(1700);

    const atmosphere = layers.find(l => l.name === "Atmosphere & reflections");
    if (atmosphere) {
      selectedId = atmosphere.id; renderLayers();
      setActivity("Toggling the atmosphere layer to compare the image with and without its soft reflections.");
      atmosphere.visible = false; renderAll();
      setStatus("Demo · atmosphere layer hidden");
      await wait(1450);
      atmosphere.visible = true; renderAll();
      setStatus("Atmosphere layer restored");
    }

    await wait(850);
    const freshIndex = layers.indexOf(fresh);
    if (freshIndex > 0) {
      selectedId = fresh.id;
      [layers[freshIndex], layers[freshIndex - 1]] = [layers[freshIndex - 1], layers[freshIndex]];
      renderAll();
      setActivity("Layer order adjusted; use the up/down controls to move any layer in the stack.");
      setStatus("Demo · reordered the paint layer");
      await wait(800);
      const now = layers.indexOf(fresh);
      if (now < layers.length - 1) [layers[now], layers[now + 1]] = [layers[now + 1], layers[now]];
      selectedId = fresh.id; renderAll();
    }
    setTool("brush");
    moveCursor(915, 535);
    setActivity("Demo complete — choose a tool, paint, reorder layers, or try another live adjustment.");
    setStatus("Ready · the canvas is yours");
    // Keep the cursor gently alive so the recording still feels like an active workspace.
    demoRunning = false;
    setTimeout(() => cursorEl.classList.remove("visible"), 2600);
  }

  paintLandscape();
  runDemo();
})();
</script>
</body>
</html>
```