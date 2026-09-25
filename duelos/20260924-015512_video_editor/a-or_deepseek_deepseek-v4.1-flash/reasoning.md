Let me build a single-file video editor demo. Key features:

- Dark professional UI: toolbar, preview canvas, timeline with 3+ tracks, timecode, zoom control.
- Clips: procedurally generated animated scenes (canvas 2D rendering per clip with different "scenes").
- Audio track drawn as waveform.
- Playhead advancing.
- In/out points.
- Transitions: crossfade, wipe between clips.
- Text title track.
- Auto demo: playhead runs, clip trimmed, another moved, everything automatic, loop.

Let me design.

Data model:
- Timeline duration ~ 24 seconds. Tracks: Video (V1), Text (T1), Audio (A1).
- Video clips: list of {id, start, dur, sceneFn, color, transitionIn: {type, dur}}.
- Text clips: {id, start, dur, text}.
- Audio clip: {start, dur} with waveform.

Rendering the preview:
- Determine current time t.
- Find topmost video clip covering t (or two, during a transition).
- If transition, blend: for crossfade, draw A then draw B with alpha; for wipe, draw A then clip B to a rect region.
- Text overlay: draw text clip covering t with fade in/out alpha.

Scene rendering: procedural animated scenes on canvas. Each scene gets (ctx, w, h, localTime, clip).

Scenes:
1. "Grid Neon": moving grid with pulsing lines.
2. "Orbiting circles": particles orbiting.
3. "Waveform bars": audio-reactive-looking bars.
4. "Sunset gradient with sun and mountains" moving.

Each has base color.

Audio waveform: generate a fake audio signal array, draw on the audio clip in timeline. Also draw as bars.

Timeline UI: use DOM for tracks and clips (divs) — easier for dragging and styling. Playhead as absolutely positioned div. Ruler with tick marks.

Zoom control: scale pixels per second. Slider changes zoom, re-renders clip positions.

Dragging: implement pointer drag on clips (mousedown/mousemove), snapping to 0.1s. During auto-demo, we programmatically animate a clip's position (move) and another's trim (out point).

Demo script (timeline of events in demo time, ~28s loop):
- 0–continuous: playhead runs from 0 to timeline end and loops.
- At ~6s of demo: trim clip 2 (its in/out) — animate trimming its right edge (duration shrink) from 6s to 3.5s.
- At ~12s: move clip 3 (drag from x to new position) — animate start change.
- Titles appear at set times.
- Show badge/toast messages: "Trimming clip…", "Moving clip…", "Adding crossfade…".

Actually "a clip is trimmed and another is moved" — good.

Also need in and out points: in/out markers on the timeline (work area). Show them as markers; perhaps demo sets in/out too. I'll add in/out point markers on the ruler that can be dragged, and display in/out timecodes in the toolbar.

Timecode display: format HH:MM:SS:FF at 30fps.

Let me plan the scene render functions carefully — must be visually decent.

Canvas preview: 16:9, e.g. 640x360 internal resolution, scaled via CSS.

Scene functions signature: drawScene(ctx, w, h, t, clip) where t is local time in seconds.

Scene A "Aurora Grid":
- Dark background gradient, horizontal moving grid lines with perspective, glow.

Simpler: use several scenes each doing something distinct:

1. Neon Grid (cyan/magenta): horizon grid scrolling toward viewer with perspective, sun.
2. Particles (orange/pink): many dots orbiting center with trails.
3. Bars (green): vertical bars animated like spectrum.
4. Rings (blue/purple): concentric rotating rings.

Implement each ~20 lines.

For blending transitions I need to render each scene to main canvas with a clip region. For crossfade: draw sceneA fully, then globalAlpha = p, draw sceneB fully. For wipe: draw sceneA, then save, clip rect from left with width p*w, draw sceneB, restore.

Problem: scenes draw their own background (fillRect), which is fine with globalAlpha for crossfade (alpha-blended over the previous). Actually with globalAlpha, the fillRect of scene B will blend with A. Good.

For wipe, clipping works.

Also need a "dip to black"? Not required. Crossfade + wipe suffice.

Transitions are defined on incoming clip: {type: 'crossfade'|'wipe', dur: 0.6}. During the transition window, the incoming clip overlaps the outgoing? Simplest: clips are adjacent (outgoing ends where incoming starts) and transition happens around the cut point: during [cut - dur/2, cut + dur/2]? Hmm, that requires both clips present. Simplest approach: overlap clips slightly in time — the outgoing clip extends past its visual end? Let's instead define transition duration and have the transition occupy the last `dur` of the previous clip and the first `dur` of the incoming clip... but the clips are sequential, so at time t during [cut, cut+dur], only the incoming clip covers t. To blend, we need the outgoing clip's content to render too.

Option: keep clips sequential, and do the transition in the window [cut - dur, cut] i.e., the last `dur` seconds of the outgoing clip: blend outgoing with incoming at progress p = (t-(cut-dur))/dur. That works: at t during that window, we render clip A (which covers t) and clip B (which starts at cut, not covering t, but we can render B with local time t - cut (negative)). Negative local time might break scenes, but scenes are procedural with sin/cos — negative time is fine mostly. Let's shift: render B at local time 0..dur -> use max(0, t - cut). Fine.

Alternatively easier: define renderTime for B as (t - cut + dur)? Nah, use max(0,t-cut).

Actually cleaner: allow the renderer to compute local time as t - clip.start, and for the incoming clip in a transition, local = t - cut, clamps to >= 0.

I'll define for each video clip: transitionIn = {type, dur} or null. Transition window = [clip.start - dur, clip.start]. During this window, if a previous clip covers time t, blend.

Wait but the previous clip covers t only if it spans [.., clip.start]. If clips are butted together, prev ends at clip.start, so yes prev covers t in that window (assuming prev.start <= t). Good. If the previous clip was moved/shortened leaving a gap, then during transition window there's no prev clip; then just render clip B fading in from black maybe. Handle: if no prev clip at t, render B with alpha p (fade from black).

Hmm, but when we move a clip around, gaps appear. Let's handle gaps: background black.

Demo manipulation: trimming clip 2 — clip 2 is a middle clip. If I trim it shorter, later clips stay in place, leaving a gap. Better: trim from the left edge? "a clip is trimmed" — trimming the out point (right edge) shortens it, leaving a gap before the next clip. That's visually clear. But then the gap. Hmm. Alternatively trim the in point (left edge) so it shifts... Actually let's just trim the out point and have the next clip start there — no. In a real editor trimming creates a gap, then you'd ripple-delete. For a demo the gap is fine visually (shows the timeline change), though it makes the montage have a black gap. Better: after trimming, the demo also could... nah.

Alternative: trim the *first* clip's out point and keep everything else. Hmm, gap again.

Let's just do: trim clip 2's right edge inward (shorten by 1.5s), creating a gap, and then at the "move" step, move clip 3 leftward to fill the gap? That's neat: two demo actions that visibly interact. Actually the requirement says "a clip is trimmed and another is moved" — perfect: trim clip 2 shorter (gap), then move clip 3 to close the gap.

Hmm, but move includes horizontal drag; clip 3 moving left by 1.5s. Good, visible.

But careful with transitions: clip 3's transitionIn uses the previous clip's end. Fine.

Also we need to keep in/out points meaningful. Let's set in/out: in = 0.0 at start, out = timeline end. Demo could animate them: set in point at 2s and out at 20s, showing the region shaded. Then playback loops within in/out? Nice touch: playhead plays range [in,out] and loops.

Actually simpler: playhead runs over the whole timeline and loops. In/out markers shown as draggable flags in the ruler; demo can move them at some point. Let's have demo set in point at ~1.5s early on with a toast "Set In point". Fine.

Let me now think about the loop: total timeline duration = 22s. Demo script:

demoTime-driven events:
- t=0.0: start playing, playhead at 0.
- t=0.3: toast "▶ Playing demo"
- At playhead reaching certain times, we trigger editing actions. Simpler: a separate script timeline in wall-clock seconds since demo start.

Let's define script events (wall clock):
- 0.5: toast "Auto-demo started"
- 1.0: set in point at 1.0 → animate in marker to 1.0s.
- 4.0: toast "Trim: shorten clip 2 out point" and animate clip2 dur from 6→4.2 over 2s. Then gap = 1.8s.
- 8.0: toast "Move clip 3 to close the gap" and animate clip3 start from its value → value - 1.8 over 2s. Also its transitionIn still fine.
- 12.0: toast "Crossfade between clip 1 & 2" — maybe toggle transition on clip 2 from 'wipe' to 'crossfade'? Let's have clip2's transition be crossfade already, clip3's be wipe. Just show it.
- 14: set out point to 20s (animate).
- 20: toast "Looping" and reset? Reset edits back to original and loop the demo after ~28s.

The playhead loops over [0, timelineEnd] continuously; edits happen at wall-clock times. Fine.

Total demo cycle 30s: after 30s, reset everything (clip durations, transition types, in/out) and restart script. Since recording window is 30s, the first playthrough shows everything.

Let me make the cycle 29s: at 29s reset and loop.

Now UI layout:

```
<div class="app">
  <header class="toolbar"> logo, buttons (Play, Pause, Stop, < >), timecode display, in/out, zoom slider, </header>
  <main class="stage">
     <section class="preview-wrap"><canvas id="preview"></canvas><div class="preview-overlay">...</div></section>
     <aside class="inspector">? maybe skip to keep simpler — could show properties</aside>
  </main>
  <section class="timeline">
     <div class="ruler"></div>
     <div class="tracks"></div>
     <div class="playhead"></div>
  </section>
</div>
```

Layout: preview on top area, timeline at bottom. Maybe preview left and a small info panel right. Let's do: main stage = preview centered with a right sidebar showing "clip info"/status log. Sidebar might be nice for toasts. Keep it moderate.

I'll do: top toolbar (with timecode, transport buttons, zoom slider, in/out display). Middle: preview (canvas 16:9) + right panel (properties: current clip, transition, and a log of actions). Bottom: timeline with ruler, track headers, tracks.

Timeline implementation details:
- pixelsPerSecond = base * zoom.
- Scroll container horizontally.
- Track headers fixed on left (width 120px), tracks area scrolls.

Simpler: the whole timeline is a flex row: left headers column (fixed), right side scrollable container with ruler + tracks. Playhead positioned inside the scrollable content.

Let me write DOM:

```html
<div class="timeline">
  <div class="tl-headers">
     <div class="ruler-spacer"></div>
     <div class="track-head">V1</div> ...
  </div>
  <div class="tl-scroll" id="tlScroll">
     <div class="tl-content" id="tlContent">
        <div class="ruler" id="ruler"></div>
        <div class="track" data-track="video" id="trackVideo"></div>
        <div class="track" data-track="text"></div>
        <div class="track" data-track="audio"></div>
        <div class="playhead" id="playhead"></div>
     </div>
  </div>
</div>
```

Headers need matching heights: ruler 24px, tracks 56px each (video 64, text 40, audio 48). Use CSS variables to keep aligned.

Clip element: absolute positioned, left = start*pps, width = dur*pps, top 4, height calc(100% - 8). Contains a label and maybe a mini thumbnail. For video clips, draw a tiny canvas? Could be heavy but fine — actually let's render a small canvas inside each video clip showing a preview frame? Simpler: CSS gradient + label + colored border. Keep it simple with a gradient using the clip color.

Audio clip: draw waveform in a canvas sized to the clip width. Redraw on zoom. Do it: canvas element inside audio clip, width = dur*pps, height = track height. Draw sampled waveform.

For simplicity: audio track has one clip spanning the timeline with a waveform canvas.

Dragging clips: pointer events on clip elements. On pointerdown, record startX, clip.start. On pointermove, delta = (x - startX)/pps; newStart = clamp(origStart + delta, 0, timelineEnd - dur). Update clip.start, re-render its style and any transitions. Text clips too? Only video clips need to be draggable per requirement ("draggable clips"), but let's allow video and text. Audio dragging is possible too; allow all.

Trimming by dragging edges: add left/right handles on video clips. Implement pointerdown on handle → adjust start/dur. That gives "in/out" trimming on clips too. Nice extra, and the demo can animate trimming programmatically using the same setters.

Now, the auto-demo needs to "trim a clip" — I'll animate clip2.dur from 6 to 4.2 and show a toast + highlight. Also actually simulate the drag: maybe show a fake cursor? Could add a little circle cursor that moves to the clip edge and drags. That's a nice touch: an animated "ghost cursor" div. Let's do it — a small dot with a ring that moves to positions. Might be complex but doable: position cursor based on clip element's screen rect. Let's include a simple version: during trim, cursor is placed at clip2's right edge and moves left; during move, cursor at clip3 center and moves left. Use fixed positioning computed from getBoundingClientRect.

OK. Let's implement.

Now the rendering loop:

```js
let playing = true;
let playhead = 0; // seconds
let lastTs = performance.now();
let demoClock = 0;

function frame(ts){
  const dt = Math.min(0.05, (ts - lastTs)/1000);
  lastTs = ts;
  if(playing){ playhead += dt; if(playhead > DURATION) playhead -= DURATION; }
  demoClock += dt;
  updateDemo(dt);
  renderPreview(playhead);
  updatePlayheadUI();
  requestAnimationFrame(frame);
}
```

Hmm: playhead loops at DURATION. Demo clock runs continuous; reset at cycle end.

FPS/timecode: use 30fps for display: frames = Math.floor(t*30)%30.

Preview rendering:

```js
function renderPreview(t){
  const ctx = pctx, W = 640, H = 360;
  ctx.clearRect...
  // find video clips covering t
  const vids = videoClips;
  let active = vids.filter(c => t >= c.start && t < c.start + c.dur);
  // background black
  ctx.fillStyle = '#000'; fillRect
  // Check for transitions: for each clip with transitionIn, window [start-dur, start]
  ...
}
```

Simplest robust approach: build a list of "layers" to draw in order:
- For each video clip, if it covers t (start<=t<start+dur) → base layer.
- If a clip has transitionIn and t in [start-d, start] and the previous clip also covers t → we need to draw prev then current with blend.

Let me write:

```js
function drawFrame(ctx, W, H, t){
  // find clips covering t
  const covering = videoClips.filter(c=> t>=c.start && t < c.start+c.dur).sort((a,b)=>a.start-b.start);
  // also clips whose transition window covers t (they start after t)
  const incoming = videoClips.filter(c=> c.transIn && t >= c.start - c.transIn.dur && t < c.start && covering.length);
  ...
}
```

Hmm let's restructure: the "current" clip = the one whose start <= t < start+dur (last one if multiple overlapping). Then check if current.transIn active: t < current.start + transIn.dur? No — my transition is defined in the incoming clip but occurs before its start in the outgoing clip's territory. Hmm, that means at t in [cur.start-dur, cur.start), the covering clip is prev. So:

For time t, covering = clips with start<=t<start+dur. Take the last one as `cur`. Then look for the next clip after cur (the one with smallest start > cur.start) that has a transition whose window covers t: t >= next.start - next.transIn.dur. If yes → blend cur with next, p = (t - (next.start - d))/d.

That's clean. Edge: if no covering clip (gap), look for next clip with transIn window covering t → fade from black p, and if t >= next.start it will be covering anyway.

Let me code:

```js
function drawFrame(ctx,W,H,t){
  ctx.setTransform(1,0,0,1,0,0);
  ctx.globalAlpha = 1;
  ctx.fillStyle = '#05070b'; ctx.fillRect(0,0,W,H);

  const covering = videoClips.filter(c=> t >= c.start && t < c.start + c.dur).sort((a,b)=> a.start - b.start);
  const cur = covering.length ? covering[covering.length-1] : null;

  if (cur){
    drawScene(ctx,W,H,t,cur,1);
    // find next clip for transition
    const next = videoClips.filter(c=> c.start > cur.start && c.transIn).sort((a,b)=>a.start-b.start)[0];
    if (next){
      const d = next.transIn.dur;
      if (t >= next.start - d){
        const p = clamp((t - (next.start - d))/d, 0, 1);
        applyTransition(ctx, W,H,t, next, next.transIn.type, p);
      }
    }
  } else {
    // gap: check for incoming fade
    const next = videoClips.filter(c=> c.transIn && t >= c.start - c.transIn.dur && t < c.start).sort((a,b)=>a.start-b.start)[0];
    if (next){
      const d = next.transIn.dur;
      const p = clamp((t-(next.start-d))/d,0,1);
      ctx.globalAlpha = p;
      drawScene(ctx,W,H,t,next,1);
      ctx.globalAlpha = 1;
    }
  }
  // text overlays
  ...
}
```

Wait: `next` search should find the clip immediately following cur in timeline order; using filter c.start > cur.start is ok.

applyTransition:
```js
function applyTransition(ctx,W,H,t,clip,type,p){
  if(type==='crossfade'){
    ctx.globalAlpha = p;
    drawScene(ctx,W,H,t,clip,1);
    ctx.globalAlpha = 1;
  } else { // wipe
    ctx.save();
    const w = W*p;
    ctx.beginPath(); ctx.rect(0,0,w,H); ctx.clip();
    drawScene(ctx,W,H,t,clip,1);
    ctx.restore();
    // wipe edge line
    ctx.save();
    ctx.fillStyle='rgba(120,220,255,0.8)';
    ctx.fillRect(w-1.5,0,3,H);
    ctx.restore();
  }
}
```

drawScene(ctx,W,H,t,clip): local = t - clip.start; if local < 0, local = 0. Call scene function by clip.scene name with color.

Scenes:

```js
const SCENES = {
  grid(ctx,W,H,lt,col){
    // dark bg with gradient
    const g = ctx.createLinearGradient(0,0,0,H);
    g.addColorStop(0, '#0a0f1e'); g.addColorStop(1, '#1a0a20');
    ...
  }
}
```

Let me write 4 scenes:

1. **grid** — perspective grid with scrolling horizontal lines + sun circle pulsing.
```js
grid(ctx,W,H,t,c){
  const g=ctx.createLinearGradient(0,0,0,H);
  g.addColorStop(0,'#060a18'); g.addColorStop(0.55,'#0d1030'); g.addColorStop(1,'#1b0a2a');
  ctx.fillStyle=g; ctx.fillRect(0,0,W,H);
  const hz=H*0.55;
  // sun
  const sunY = hz - 20 + Math.sin(t*1.2)*6;
  const rg = ctx.createRadialGradient(W/2, sunY, 5, W/2, sunY, 140);
  rg.addColorStop(0,'rgba(255,120,200,0.95)');
  rg.addColorStop(0.4,'rgba(255,60,160,0.35)');
  rg.addColorStop(1,'rgba(255,0,120,0)');
  ctx.fillStyle=rg; ctx.beginPath(); ctx.arc(W/2,sunY,140,0,7); ctx.fill();
  ctx.fillStyle='rgba(255,190,230,0.9)'; ctx.beginPath(); ctx.arc(W/2,sunY,32,0,7); ctx.fill();
  // grid lines
  ctx.strokeStyle='rgba(0,230,255,0.55)'; ctx.lineWidth=1;
  const n=14;
  for(let i=0;i<=n;i++){
    const p = ((i + (t*0.35)%1)/n);
    const y = hz + Math.pow(p,2.4)*(H-hz)*1.4;
    if(y>H) continue;
    ctx.globalAlpha = 0.25+0.6*p;
    ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(W,y); ctx.stroke();
  }
  ctx.globalAlpha=1;
  for(let i=-10;i<=10;i++){
    ctx.beginPath();
    ctx.moveTo(W/2 + i*(W/9), hz);
    ctx.lineTo(W/2 + i*(W/1.4), H+40);
    ctx.stroke();
  }
  // horizon glow
}
```
Careful with alpha reset.

2. **orbit** — particles orbiting.
```js
orbit(ctx,W,H,t,c){
  bg radial gradient dark blue
  const cx=W/2, cy=H/2;
  for(let i=0;i<60;i++){
    const a = i*0.37 + t*(0.3+ (i%5)*0.08);
    const r = 40 + (i%9)*22 + Math.sin(t*1.5+i)*10;
    const x = cx + Math.cos(a)*r*1.4, y = cy + Math.sin(a)*r*0.8;
    const s = 2 + (i%4);
    ctx.fillStyle = `hsla(${200 + i*3},90%,${55+ (i%3)*8}%,0.9)`;
    ctx.beginPath(); ctx.arc(x,y,s,0,7); ctx.fill();
  }
}
```
Add trails via fading rect? Keep simple.

3. **bars** — spectrum bars.
```js
bars(ctx,W,H,t,c){
  bg gradient dark green/teal
  const n=48;
  for(let i=0;i<n;i++){
    const v = Math.abs(Math.sin(t*3 + i*0.4))*0.5 + Math.abs(Math.sin(t*1.3 + i*0.17))*0.5;
    const h = 20 + v*(H*0.7);
    ctx.fillStyle = `hsla(${150 + i*2}, 85%, 55%, 0.9)`;
    ctx.fillRect(i*(W/n)+2, H-h, W/n-4, h);
  }
}
```
Add a reflection.

4. **rings** — concentric rotating arcs.
```js
rings(ctx,W,H,t,c){
  bg dark purple
  translate to center, rotate
  for(i=0..7){ arc with varying radius, strokeStyle hsl, lineWidth }
}
```

Maybe 4 scenes and 4 clips. Clips: 
- clip1: grid, start 0, dur 5.5
- clip2: orbit, start 5.5, dur 5.0, transIn crossfade 0.7
- clip3: bars, start 10.5, dur 5.0, transIn wipe 0.8
- clip4: rings, start 15.5, dur 5.0, transIn crossfade 0.7

Total duration 20.5s. Timeline shown duration 22s.

Then trim clip2 dur 5.0→3.6 (gap 1.4), then move clip3 left by 1.4 to 9.1 (closing gap). Then transitions still fine since clip3.start changes and previous clip2 ends at 9.1 exactly. 

Wait clip3's transIn window = [start-0.8, start] = [8.3, 9.1], and clip2 spans [5.5, 9.1]. Good.

Clip4 start 15.5; clip3 ends at 9.1+5.0=14.1 leaving a gap of 1.4 from 14.1 to 15.5. Hmm. Moving clip3 left creates a gap before clip4. To avoid weirdness, move clip4 too? Or move clip3 right instead... Let's just also nudge clip4 left by 1.4 at the same time? The requirement says "another is moved" — moving clip3 (and its neighbor shifts). Hmm, moving only clip3 leaves gap between 14.1 and 15.5.

Alternative: don't trim from the out point; trim the in point of clip2? Trimming clip2's in point (left edge) moves its start right and shortens dur, creating a gap between clip1 (ends 5.5) and clip2 (starts 6.9). Then "move clip 2" left to close → back to original. Hmm same issue but between clip1 and clip2 the gap is closed by moving clip2. And clip2's end stays at 10.5, so clip3 unaffected! That works nicely.

So: trim clip2's left edge: start 5.5→6.9, dur 5.0→3.6 (ends at 10.5 unchanged). Gap between clip1 end (5.5) and clip2 start (6.9). Then move clip2 left by 1.4 → back to 5.5, dur 3.6, ends at 9.1. Now gap between clip2 end (9.1) and clip3 start (10.5). Hmm, again gap.

OK, any trim creates a gap somewhere unless we ripple. Let's just accept a gap and make it look intentional... Actually, better: keep gap small-ish (1.2s) and let the preview show black — but that looks like a bug in the montage.

Alternative approach: instead of trimming clip duration, the trim adjusts the in-point *within* the source clip while keeping timeline duration the same? That's not visible as a length change though. But it is a real "trim" — changing in/out points of the source. Visually the clip would get a "source in" line. Hmm, not as visually obvious.

Alternative: trim clip 4 (the last clip) — trimming its out point shortens it; no gap created (it just ends earlier). Then move clip 3 (the third clip) — moving it right creates a gap; moving it left overlaps clip 2. Hmm.

What if moving clip3 left to overlap... no, overlapping video clips would need track compositing.

Let's do: trim the LAST clip's out point (shortens the timeline, no gap), and move the SECOND clip slightly later (creating a small gap that then... hmm).

Or: move a clip and then the demo "ripples" — actually let's do this: trim clip 4's out (dur 5.0 → 3.4, ends 18.9 instead of 20.5), then move clip 3 right by 0.8 → gap between clip2 end and clip3 start of 0.8s... still a gap.

Honestly, a gap filled by black is a normal editing state. But for the recorded demo showing a montage, gaps look unpolished. Solution: during the gap, show black with a subtle "no signal" — nah.

Simplest: move a clip that is adjacent into the gap created by the trim. Do it as one demo step: trim clip2's out point by 1.2s (gap [9.3,10.5]), then move clip3 left by 1.2 (start 10.5→9.3, so clip3 ends at 14.3), and ALSO move clip4 left by 1.2 in the same animation? That's "a clip is moved" plus a ripple. Actually I could animate all subsequent clips moving left (ripple) — that's what a real "ripple edit" does. But the spec says "another is moved". Let's just move clip3 and clip4 together as part of the same "move" animation? Eh.

Alternative clean solution: trim clip 3's out point (5.0 → 3.6): clip3 then spans [10.5, 14.1], gap [14.1, 15.5] before clip4. Then move clip4 left to close the gap: 15.5 → 14.1. Then clip4 spans [14.1,19.1]. No gaps! And the timeline end becomes 19.1.

That's elegant: trim clip 3 (creating a gap), then move clip 4 to close it. Both actions do exactly what's required and the result is gap-free.

But wait: moving clip4 left changes its transitionIn window relative to clip3's end: clip3 ends at 14.1, clip4 starts at 14.1. Transition window = [13.3, 14.1] which lies inside clip3. Good.

And after the trim of clip3's out point, during [10.5,14.1] clip3 plays; between 14.1 and 15.5 → gap (black), then clip4. Then move closes it.

Great. Demo sequence with times:
- t=0: play starts. Playhead at 0.
- t=1.0: toast "▶ Auto demo — playing timeline"
- t=3.0: set in point at 0.5? Let's animate in-point marker to 1.0s with toast "Mark In".
- t=6.5: toast "Trim clip 3 (out point)"; animate clip3.dur 5.0→3.6 over 2.0s. Ghost cursor at clip3 right edge moving left.
- t=10.0: set out point to 19.0? maybe skip.
- t=11.0: toast "Move clip 4 to close the gap"; animate clip4.start 15.5→14.1 over 2.0s; cursor at clip4 center.
- t=15.0: toast "Transitions: crossfade & wipe active" 
- t=18: toast "Titles animate on the text track"
- t=24: toast "Loop restarting"; reset at 28s.

Hmm, total 28s cycle. Good, within 30s.

The playhead loops at DURATION = 22s constantly, which is fine.

Actually maybe playhead should loop over the timeline duration (22s) continuously; when it hits, restart. Yes.

Now let's handle in/out markers: In=0, Out=22 initial. Demo sets In to 1.0 at 3s (animate). Maybe also Out to 19.5 at 20s. Show in/out region shading on ruler. Also playback could be restricted... no, keep playhead looping whole.

Text track clips:
- "NEON DREAMS" from 0.8 to 4.5 (fade in/out)
- "AUTO EDIT DEMO" from 6.0 to 10.0
- "CROSSFADE →" ... let's do 3 titles:
  - t1: "NEON DREAMS", start 1.0, dur 3.0
  - t2: "SHOT 02 — ORBIT", start 6.2, dur 3.2
  - t3: "SPECTRUM", start 11.0, dur 3.0
  - t4: "RINGS // END", start 15.5, dur 3.5

Hmm, clip4 moves to 14.1, so title at 15.5 is fine.

Text rendering in preview: with fade in/out over 0.4s, positioned lower third with a colored bar. Maybe subtitle style at bottom center, plus a title at top for the first.

Let's render title text: big bold, letter-spaced, with glow, centered at ~78% height. Use ctx font "bold 34px system-ui, sans-serif". Letter spacing isn't supported in all canvas? `ctx.letterSpacing` is supported in Chrome. I'll just draw manually with spaces or use letterSpacing with fallback.

Simpler: ctx.font = 'bold 36px sans-serif'; fillText centered.

OK.

Audio: a single audio clip [0, 22] with waveform. Also draw a moving playhead in the waveform? The timeline playhead covers it.

Waveform generation: array of 600 samples using layered sines + noise envelope. Draw in canvas of width = duration*pps, height = trackHeight. Rebuild on zoom.

Also "audio element" in preview: maybe show a small audio meter. Skip; instead show a level meter bars in the corner. Nice touch: draw a small audio level indicator on the preview bottom-left. Optional. I'll add a subtle "level" bar in the preview corner driven by the waveform value at playhead. Cute.

Now the toolbar:
- Buttons: ⏮ (skip to start), ▶/⏸ (play/pause), ⏭, and maybe "✂" etc. Transport works with clicks too (nice: user can interact but demo is automatic).
- Timecode big: `00:00:05:12`.
- In/Out display: `IN 00:00:01:00  OUT 00:00:22:00`.
- Zoom slider: range 20..200, default 60 px/s.

Also add tool buttons like "Select", "Razor", "Text" — decorative.

Now let's write the CSS for a professional dark look: background #0b0d12, panels #12151c, borders #232833, accent #3ba7ff or #22d3ee. Font: system-ui.

Let me write the code.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>NovaCut — Timeline Demo</title>
<style>
  :root{
    --bg:#0a0c11; --panel:#12151d; --panel2:#171b25; --line:#242a37;
    --txt:#c9d1de; --dim:#7b869a; --accent:#38bdf8; --accent2:#f472b6;
    --video:#2b6cb0; --text:#b7791f; --audio:#2f855a;
  }
  *{box-sizing:border-box}
  html,body{height:100%}
  body{margin:0;background:var(--bg);color:var(--txt);font:13px/1.4 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;overflow:hidden}
  .app{display:flex;flex-direction:column;height:100vh}
  ...
</style>
```

Layout heights: toolbar 52px, stage flex:1 (min-height 0), timeline ~290px.

Stage: display flex; preview area flex:1 with canvas centered; side panel 280px.

Preview canvas: aspect-ratio 16/9, max-width 100%, max-height 100%.

Let me write:

```css
.stage{flex:1;display:flex;min-height:0;gap:10px;padding:10px}
.preview-panel{flex:1;min-width:0;background:var(--panel);border:1px solid var(--line);border-radius:8px;display:flex;align-items:center;justify-content:center;position:relative;padding:10px}
canvas#preview{width:100%;height:100%;object-fit:contain;background:#000;border-radius:4px}
```
Hmm, canvas with width:100%;height:100% will stretch. Use aspect-ratio and max sizing:

```css
#preview{aspect-ratio:16/9;max-width:100%;max-height:100%;width:100%;object-fit:contain;background:#000;border-radius:4px}
```
With width 100% and max-height 100% and aspect-ratio, it should letterbox properly. Actually setting both width:100% and max-height:100% with aspect-ratio: the browser computes height from width, but max-height clamps it, and then width... it may distort. Safer: use a wrapper with `display:grid;place-items:center` and canvas `max-width:100%;max-height:100%;width:auto;height:auto;` but then canvas needs intrinsic size — canvas has width/height attributes 640x360, so it has intrinsic size. With max-width/max-height 100% it scales preserving aspect ratio. 

So: `<canvas id="preview" width="640" height="360"></canvas>` with CSS `max-width:100%;max-height:100%;` and it will scale down preserving aspect. But it might not scale up beyond 640. Use `width:100%;height:auto` — with a container that's wide, it would be 640 max... Let's set the canvas attribute size to 960x540 (bigger) and let CSS max-width:100% scale it down. Good enough. Actually for sharpness, render at 960x540. Fine.

Let me use width=960 height=540 for the canvas backing store and CSS max-width:100%; max-height:100%.

Timeline:

```css
.timeline{height:300px;background:var(--panel);border-top:1px solid var(--line);display:flex;flex-direction:column}
.tl-toolbar{height:34px;display:flex;align-items:center;gap:8px;padding:0 10px;border-bottom:1px solid var(--line)}
.tl-body{flex:1;display:flex;min-height:0}
.tl-headers{width:110px;flex:none;border-right:1px solid var(--line);background:var(--panel2)}
.tl-scroll{flex:1;overflow-x:auto;overflow-y:hidden;position:relative}
.tl-content{position:relative;height:100%}
.ruler{height:26px;position:relative;border-bottom:1px solid var(--line)}
.track{height:64px;border-bottom:1px solid var(--line);position:relative}
.track.text{height:44px}
.track.audio{height:66px}
```

Headers must align: header spacer 26px, then track headers with same heights: 64, 44, 66. Use classes.

But vertical scroll: if content taller than container, we get mismatch. Set timeline height enough: 26+64+44+66 = 200 + ruler. Plus toolbar 34 → 234. Set timeline height 300 to be safe, and add a 4th header? No — just let heights match; if space extra it's fine.

Hmm, but the tracks area height 200 and container ~266, leaving empty space below — fine, background dark.

Let's compute: `.timeline{height:300px}` minus tl-toolbar 34 = 266 for tl-body. Content: ruler 26 + tracks 200 = 226. Fine, 40px spare (maybe add a horizontal scrollbar area). OK.

Actually to avoid vertical mismatch, keep overflow hidden on tl-scroll vertically. If vertical scrollbar appears it'd desync. Set `overflow-y:hidden`.

Clip styles:

```css
.clip{position:absolute;top:3px;bottom:3px;border-radius:5px;overflow:hidden;cursor:grab;user-select:none;
  border:1px solid rgba(255,255,255,.18); box-shadow:0 2px 6px rgba(0,0,0,.4)}
.clip.video{background:linear-gradient(180deg,#2f6fbd,#1d3f70)}
.clip .label{position:absolute;top:2px;left:6px;font-size:11px;font-weight:600;color:#eaf2ff;text-shadow:0 1px 2px #000;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;right:6px;pointer-events:none}
.clip .thumb{position:absolute;left:0;right:0;top:16px;bottom:0;opacity:.55;background:repeating-linear-gradient(...)}
.handle{position:absolute;top:0;bottom:0;width:7px;cursor:ew-resize;background:rgba(255,255,255,.12)}
.handle.l{left:0} .handle.r{right:0}
.clip.hot{outline:2px solid var(--accent); box-shadow:0 0 12px rgba(56,189,248,.6)}
```

Text clips: gradient amber/purple, centered text label.

Audio clip: green with canvas waveform.

Transitions visualization: a small badge at the clip's left indicating type, e.g. "✕" for crossfade, "▤" for wipe; plus a triangle region overlay. Let's add a `.trans` div positioned at clip left, width = dur*pps, with diagonal stripes, and a tooltip label.

Playhead: absolute, width 1px, background #ff5252, with a triangle head at the top.

Ruler ticks: generate marks every 1s with labels every 1s if zoom enough else every 5s. Redraw on zoom.

Now the JS structure:

```js
const DUR = 22; // timeline seconds
let pps = 60; // pixels per second base (zoom multiplies)
```

Let me define state:

```js
const state = {
  playhead: 0,
  playing: true,
  zoom: 1,
  inPoint: 0,
  outPoint: DUR,
  demoClock: 0,
  cycle: 0
};

const videoClips = [
  {id:'v1', name:'Grid', scene:'grid', start:0, dur:5.5, transIn:null},
  {id:'v2', name:'Orbit', scene:'orbit', start:5.5, dur:5.0, transIn:{type:'crossfade',dur:0.7}},
  {id:'v3', name:'Spectrum', scene:'bars', start:10.5, dur:5.0, transIn:{type:'wipe',dur:0.8}},
  {id:'v4', name:'Rings', scene:'rings', start:15.5, dur:5.0, transIn:{type:'crossfade',dur:0.7}},
];
```

Wait: earliest start 0, latest end 20.5. DUR 22.

Text clips:
```js
const textClips = [
  {id:'t1', text:'NEON DREAMS', start:1.0, dur:3.2},
  {id:'t2', text:'ORBIT / SHOT 02', start:6.3, dur:3.0},
  {id:'t3', text:'SPECTRUM BARS', start:11.2, dur:3.0},
  {id:'t4', text:'RINGS // FINAL', start:16.0, dur:3.5},
];
```

Audio: one clip start 0 dur DUR.

Rendering clips to DOM: build elements once, then update positions in `layoutClips()`.

I'll create clip objects with a reference to their DOM element.

Let me write functions:

```js
function buildTimeline(){
  trackVideoEl.innerHTML=''; ... create clip divs
}
function layout(){
  for each clip: el.style.left = (c.start*ppsPx)+'px'; el.style.width = (c.dur*ppsPx)+'px';
  also transition divs
  playhead position
  ruler ticks
  audio waveform canvas resize/redraw
}
```

ppsPx = basePps * zoom where basePps = 60.

Zoom slider: 0.5..2.5 → pps 30..150. Default 1 → 60px/s → 22s = 1320px, wider than container (~ viewport-110). So horizontal scroll exists. Good, but the playhead must be scrolled into view automatically (auto-scroll follow). Let's implement auto-scroll: if playhead x is outside the visible area, scroll the container. That's nice and professional.

Let me set base pps to 46 so 22s = 1012px, roughly fits on a 1200px screen minus headers (110) and panel. Hmm, depends on viewport. Auto-follow scroll handles it. Let's use 50 base.

Now dragging: implement with pointer events on clip elements.

```js
el.addEventListener('pointerdown', e=>{
  if(e.target.classList.contains('handle')) return; // handled separately
  ...
});
```

Actually handles: pointerdown on `.handle.l` → trim left; `.handle.r` → trim right.

Drag logic:

```js
function beginDrag(e, clip, mode){
  e.preventDefault(); e.stopPropagation();
  const startX = e.clientX;
  const s0 = clip.start, d0 = clip.dur;
  const el = clip.el;
  el.setPointerCapture(e.pointerId);
  const move = ev=>{
    const dx = (ev.clientX - startX)/ppsPx;
    if(mode==='move'){
      clip.start = clamp(s0+dx, 0, DUR - clip.dur);
    } else if(mode==='l'){
      let ns = clamp(s0+dx, 0, s0+d0-0.3);
      clip.start = ns; clip.dur = d0 + (s0-ns);
    } else {
      clip.dur = clamp(d0+dx, 0.3, DUR - clip.start);
    }
    layout();
  };
  ...
}
```

Careful: `ppsPx` is a global updated on zoom.

Also snapping to 0.05s: round.

OK.

Now the demo script. I'll implement as a list of steps with start times:

```js
const script = [
  {at:0.3, fn:()=>toast('Auto demo started — timeline playback')},
  {at:2.5, fn:()=>{ markIn(1.0); toast('Mark In point @ 00:00:01:00'); }},
  ...
];
```

But animations need continuous updates. I'll implement tweens:

```js
let tweens = [];
function tween(from, to, duration, onUpdate, onDone){...}
```

Tween object: {t:0, dur, from, to, ease, onUpdate, onDone}. Updated each frame in `updateDemo(dt)`.

Demo script executed with a flag per step.

Let me code:

```js
const demo = {
  clock: 0,
  fired: new Set(),
  cycle: 0,
  events: [
    {t:0.2, f:()=>{ toast('▶ Auto-demo running — no interaction needed'); }},
    {t:2.0, f:()=>{ toast('Setting IN point'); tween(state.inPoint, 1.0, 1.2, v=>{state.inPoint=v; layout();}); }},
    {t:5.5, f:()=>{ toast('Trimming clip “Spectrum” — dragging out point'); flash(v3); tween(5.0, 3.6, 2.0, v=>{v3.dur=v; layout();}); }},
    {t:10.0, f:()=>{ toast('Moving clip “Rings” to close the gap'); flash(v4); tween(15.5, 14.1, 2.0, v=>{v4.start=v; layout();}); }},
    {t:14.5, f:()=>{ toast('Transitions: crossfade + wipe between scenes'); }},
    {t:18.0, f:()=>{ toast('Titles fade in/out on the text track'); }},
    {t:22.0, f:()=>{ toast('Setting OUT point'); tween(state.outPoint, 19.0, 1.2, v=>{state.outPoint=v; layout();}); }},
    {t:26.0, f:()=>{ resetAll(); toast('Looping demo…'); }},
  ]
};
```

Hmm, resetAll at 26 then cycle restarts at clock 0? Let's set: when demo.clock > 28 → reset clock to 0, clear fired, reset state and clips.

Also tween conflict: at reset, cancel tweens.

Careful with the trim tween: if the user drags mid-tween, whatever.

Ghost cursor: I'll implement a `.ghost-cursor` div positioned fixed, showing during tweens. Let's attach cursor movement to the tween: optional. Simpler: during trim tween, position ghost at the right edge of clip v3 (computed from element rect), during move tween at clip v4 center. Compute each frame — easier: give tween a `cursor: 'right'|'center'` and target clip, and update in the frame loop while active.

Let's do: `demo.grab = {clip, mode:'right'|'center'}` while tween active; hide after.

I'll implement ghost cursor positioning in the frame loop:

```js
function updateCursor(){
  if(!grabClip){ ghost.style.opacity=0; return; }
  const r = grabClip.el.getBoundingClientRect();
  const x = grabMode==='right' ? r.right : r.left + r.width/2;
  const y = r.top + r.height/2;
  ghost.style.opacity=1;
  ghost.style.transform = `translate(${x}px,${y}px)`;
}
```
CSS: `.ghost{position:fixed;left:0;top:0;width:18px;height:18px;margin:-9px 0 0 -9px;border-radius:50%;border:2px solid #fff;background:rgba(56,189,248,.4);pointer-events:none;z-index:999;transition:opacity .2s}` — the transform translate positions it.

Now the preview text overlay & audio meter.

Let me write drawFrame fully.

```js
function drawFrame(t){
  const W=preview.width, H=preview.height;
  const ctx=pctx;
  ctx.setTransform(1,0,0,1,0,0); ctx.globalAlpha=1;
  ctx.fillStyle='#04060a'; ctx.fillRect(0,0,W,H);

  const covering = videoClips.filter(c=>t>=c.start && t<c.start+c.dur).sort((a,b)=>a.start-b.start);
  const cur = covering.length?covering[covering.length-1]:null;

  if(cur){
    drawScene(ctx,W,H,t,cur);
    const nxt = videoClips.filter(c=>c.transIn && c.start>cur.start).sort((a,b)=>a.start-b.start)[0];
    if(nxt){
      const d=nxt.transIn.dur;
      if(t>=nxt.start-d){
        const p=clamp((t-(nxt.start-d))/d,0,1);
        if(nxt.transIn.type==='crossfade'){
          ctx.globalAlpha=p; drawScene(ctx,W,H,t,nxt); ctx.globalAlpha=1;
        } else {
          ctx.save(); ctx.beginPath(); ctx.rect(0,0,W*p,H); ctx.clip(); drawScene(ctx,W,H,t,nxt); ctx.restore();
          // wipe edge
          ctx.save(); const g=ctx.createLinearGradient(W*p-24,0,W*p+2,0);
          g.addColorStop(0,'rgba(120,220,255,0)'); g.addColorStop(1,'rgba(160,240,255,.85)');
          ctx.fillStyle=g; ctx.fillRect(W*p-24,0,26,H); ctx.restore();
        }
        // label
        drawTransLabel(ctx, W, H, nxt.transIn.type, p);
      }
    }
  } else {
    // gap
    const nxt = videoClips.filter(c=> c.transIn && t>=c.start-c.transIn.dur && t<c.start).sort((a,b)=>a.start-b.start)[0];
    if(nxt){
      const d=nxt.transIn.dur, p=clamp((t-(nxt.start-d))/d,0,1);
      ctx.globalAlpha=p; drawScene(ctx,W,H,t,nxt); ctx.globalAlpha=1;
    }
  }

  // text overlays
  for(const tc of textClips){
    if(t>=tc.start && t<tc.start+tc.dur){
      const lt=t-tc.start;
      const fade=0.45;
      let a = Math.min(1, lt/fade, (tc.dur-lt)/fade);
      a = clamp(a,0,1);
      drawTitle(ctx,W,H,tc.text,a);
    }
  }

  // audio meter bottom-left
  drawMeter(ctx,W,H,t);

  // safe frame / vignette
}
```

drawScene(ctx,W,H,t,clip): compute local = max(0, t-clip.start) but if t < clip.start (transition window), local = t - clip.start (negative) → use localTime = t - clip.start; scenes handle negatives fine. Actually for the wipe/crossfade incoming clip, using negative time gives a "frozen at negative" look which is fine and continuous. Let's use lt = t - clip.start (may be slightly negative), scenes use sin/cos so fine.

Hmm, for `bars` scene with abs(sin) it's fine.

drawTitle: draw a bar and text.

```js
function drawTitle(ctx,W,H,text,a){
  ctx.save();
  ctx.globalAlpha=a;
  const y=H*0.8;
  ctx.textAlign='center'; ctx.textBaseline='middle';
  ctx.font='600 '+Math.round(H*0.075)+'px system-ui, sans-serif';
  const w=ctx.measureText(text).width;
  // backdrop
  const bx=W/2-w/2-26, by=y-30, bw=w+52, bh=60;
  const g=ctx.createLinearGradient(bx,0,bx+bw,0);
  g.addColorStop(0,'rgba(56,189,248,0)'); g.addColorStop(.5,'rgba(56,189,248,.25)'); g.addColorStop(1,'rgba(56,189,248,0)');
  ctx.fillStyle=g; ctx.fillRect(bx,by,bw,bh);
  ctx.shadowColor='rgba(120,220,255,.9)'; ctx.shadowBlur=18;
  ctx.fillStyle='#eaf6ff';
  ctx.fillText(text, W/2, y);
  ctx.restore();
}
```

Also a small "T" indicator maybe. Fine.

drawMeter: 
```js
function drawMeter(ctx,W,H,t){
  const v = audioLevel(t);
  ctx.save();
  ctx.fillStyle='rgba(0,0,0,.45)'; ctx.fillRect(20,H-46,160,22);
  for(let i=0;i<24;i++){
    const on = i/24 < v;
    ctx.fillStyle = on ? (i>18?'#f87171': i>14?'#fbbf24':'#4ade80') : 'rgba(255,255,255,.08)';
    ctx.fillRect(26+i*6, H-41, 4, 12);
  }
  ctx.restore();
}
```
audioLevel(t) = amplitude from the generated waveform.

Waveform data: generate an array of N=1600 samples over [0,DUR]:

```js
function makeAudio(n){
  const arr=[];
  for(let i=0;i<n;i++){
    const t=i/n*DUR;
    let a = 0.35*Math.abs(Math.sin(t*3.1)) + 0.3*Math.abs(Math.sin(t*7.7+1)) + 0.25*Math.abs(Math.sin(t*1.3+2));
    a *= 0.5+0.5*Math.sin(t*0.8);
    a = Math.min(1, a*1.2);
    arr.push(a);
  }
  return arr;
}
```

For the audio clip in the timeline, draw a canvas with mirrored bars.

Draw waveform canvas: width = clip.dur*pps (in CSS px); set canvas.width = that * dpr maybe. Keep simple: canvas.width = Math.max(1, Math.round(w)), canvas.height = trackH. Then draw bars: for x in 0..width step 3, sample the waveform at time (x/width*dur + start).

Now, the timeline layout and zoom.

```js
function layout(){
  const px = BASE_PPS * state.zoom;
  ppsPx = px;
  tlContent.style.width = (DUR*px)+'px';
  // clips
  ...
  // ruler
  drawRuler();
  // in/out shading
  // playhead
}
```

Ruler: create ticks. I'll clear and rebuild each layout (zoom changes). Number of seconds = 22; at 150px/s that's 3300px → 22 major ticks, minor every 0.5s. Fine.

Ruler labels: format `0:05` style, i.e., mm:ss.

In/out region: a div overlay in ruler showing shaded regions outside in/out, and markers.

Playhead update each frame: `playheadEl.style.transform = translateX(px)`. Use left style — fine.

Auto-scroll: 
```js
const scroller = tlScroll;
const px = state.playhead*ppsPx;
const viewL = scroller.scrollLeft, viewR = viewL + scroller.clientWidth;
if(px > viewR - 120) scroller.scrollLeft = px - scroller.clientWidth + 160;
else if(px < viewL + 60) scroller.scrollLeft = Math.max(0, px-100);
```
Smooth-ish.

Also clicking on the ruler seeks.

Now let me write the whole thing carefully.

HTML skeleton:

```html
<div class="app">
  <header class="toolbar">
    <div class="brand"><span class="dot"></span>NOVACUT<span class="sub">timeline demo</span></div>
    <div class="tools">
      <button class="tbtn active" title="Select">⬉</button>
      <button class="tbtn" title="Razor">✂</button>
      <button class="tbtn" title="Text">T</button>
      <button class="tbtn" title="Transition">⇄</button>
    </div>
    <div class="spacer"></div>
    <div class="transport">
      <button id="btnStart">⏮</button>
      <button id="btnPlay">▶</button>
      <button id="btnEnd">⏭</button>
    </div>
    <div class="timecode" id="tc">00:00:00:00</div>
    <div class="io">
      <span class="chip">IN <b id="inTc">00:00:00:00</b></span>
      <span class="chip">OUT <b id="outTc">00:00:22:00</b></span>
    </div>
    <div class="zoom">
      <span>ZOOM</span>
      <input type="range" id="zoom" min="0.5" max="2.6" step="0.01" value="1">
    </div>
  </header>
  <div class="stage">
    <div class="preview-panel">
      <div class="preview-inner"><canvas id="preview" width="960" height="540"></canvas></div>
      <div class="badge" id="transBadge"></div>
      <div class="hud" id="hud">V1 · Grid</div>
    </div>
    <aside class="side">
      <h3>Inspector</h3>
      <div class="row"><span>Clip</span><b id="inspClip">—</b></div>
      ...
      <h3>Activity</h3>
      <div class="log" id="log"></div>
    </aside>
  </div>
  <div class="timeline">...</div>
  <div class="ghost" id="ghost"></div>
</div>
```

Hmm the `.ghost` fixed positioned.

The "Activity" log will hold toast messages. Good for showing what's happening.

Let me now write CSS carefully.

Now writing the JS in full.

```js
(function(){
'use strict';

const DUR = 22;
const BASE_PPS = 50;

// ---------- utilities
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const easeInOut = t => t<0.5 ? 2*t*t : 1-Math.pow(-2*t+2,2)/2;

// ---------- audio waveform
const AUDIO_N = 2000;
const audioData = (()=>{ ... })();
function audioLevel(t){
  const i = clamp(Math.floor(t/DUR*AUDIO_N),0,AUDIO_N-1);
  return audioData[i];
}
```

Scenes object.

Let me write scenes with good visuals:

```js
const TAU = Math.PI*2;

const SCENES = {
  grid(ctx,W,H,t,c){
    const g=ctx.createLinearGradient(0,0,0,H);
    g.addColorStop(0,'#05060f'); g.addColorStop(.5,'#0b0f2c'); g.addColorStop(1,'#1a0722');
    ctx.fillStyle=g; ctx.fillRect(0,0,W,H);
    const hz=H*0.58;
    // stars
    for(let i=0;i<70;i++){
      const x=((i*137.5)%W), y=((i*79.3)%hz);
      const tw=0.4+0.6*Math.abs(Math.sin(t*2+i));
      ctx.fillStyle=`rgba(200,230,255,${0.15+0.5*tw})`;
      ctx.fillRect(x,y,1.6,1.6);
    }
    // sun
    const sy=hz-46+Math.sin(t*0.9)*8;
    const rg=ctx.createRadialGradient(W/2,sy,4,W/2,sy,H*0.45);
    rg.addColorStop(0,'rgba(255,150,220,0.95)');
    rg.addColorStop(.35,'rgba(255,60,150,0.35)');
    rg.addColorStop(1,'rgba(255,0,110,0)');
    ctx.fillStyle=rg; ctx.beginPath(); ctx.arc(W/2,sy,H*0.45,0,TAU); ctx.fill();
    ctx.fillStyle='rgba(255,215,240,0.95)';
    ctx.beginPath(); ctx.arc(W/2,sy,H*0.075,0,TAU); ctx.fill();
    // horizontal lines
    ctx.lineWidth=Math.max(1,H/540*1.6);
    for(let i=0;i<16;i++){
      const p=((i/16)+(t*0.22)%(1/16));
      const y=hz+Math.pow(p,2.2)*(H-hz)*1.6;
      if(y>H+2)continue;
      ctx.strokeStyle=`rgba(0,230,255,${0.15+0.55*p})`;
      ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(W,y); ctx.stroke();
    }
    // vertical perspective lines
    for(let i=-12;i<=12;i++){
      ctx.strokeStyle='rgba(0,200,255,0.28)';
      ctx.beginPath(); ctx.moveTo(W/2+i*(W/16),hz); ctx.lineTo(W/2+i*(W/1.1),H+30); ctx.stroke();
    }
    // horizon glow
    const hg=ctx.createLinearGradient(0,hz-14,0,hz+14);
    hg.addColorStop(0,'rgba(0,255,255,0)'); hg.addColorStop(.5,'rgba(120,255,255,.5)'); hg.addColorStop(1,'rgba(0,255,255,0)');
    ctx.fillStyle=hg; ctx.fillRect(0,hz-14,W,28);
  },
  ...
}
```

Wait: `(t*0.22)%(1/16)` — the horizontal lines should scroll toward the viewer. p goes 0..1 with wrap. Using `const p = ((i/16) + (t*0.22)) % 1;` then y = hz + p^2.2*(H-hz)*1.6. That makes lines move downward (toward viewer). Good.

Scene orbit:

```js
orbit(ctx,W,H,t,c){
  const g=ctx.createRadialGradient(W/2,H/2,10,W/2,H/2,H*0.9);
  g.addColorStop(0,'#101a3a'); g.addColorStop(1,'#03040a');
  ctx.fillStyle=g; ctx.fillRect(0,0,W,H);
  const cx=W/2, cy=H/2;
  // core
  const core=ctx.createRadialGradient(cx,cy,2,cx,cy,H*0.22);
  core.addColorStop(0,'rgba(255,220,160,1)'); core.addColorStop(.4,'rgba(255,140,60,.5)'); core.addColorStop(1,'rgba(255,80,0,0)');
  ctx.fillStyle=core; ctx.beginPath(); ctx.arc(cx,cy,H*0.22,0,TAU); ctx.fill();
  // orbits trails
  for(let ring=0;ring<4;ring++){
    const rr = H*(0.14+ring*0.09);
    ctx.strokeStyle=`rgba(120,180,255,${0.12-ring*0.02})`;
    ctx.lineWidth=1;
    ctx.beginPath(); ctx.ellipse(cx,cy,rr*1.35,rr*0.6,0,0,TAU); ctx.stroke();
  }
  for(let i=0;i<48;i++){
    const ring = i%4;
    const a = i*0.62 + t*(0.5+ring*0.25);
    const r = H*(0.14+ring*0.09);
    const x = cx + Math.cos(a)*r*1.35;
    const y = cy + Math.sin(a)*r*0.6;
    const s = 3.4 - ring*0.5;
    ctx.fillStyle = `hsla(${28+i*2},95%,${62-ring*4}%,0.95)`;
    ctx.beginPath(); ctx.arc(x,y,Math.max(1.2,s),0,TAU); ctx.fill();
    // glow
    ctx.fillStyle = `hsla(${28+i*2},95%,60%,0.18)`;
    ctx.beginPath(); ctx.arc(x,y,s*3,0,TAU); ctx.fill();
  }
}
```

Scene bars:

```js
bars(ctx,W,H,t,c){
  const g=ctx.createLinearGradient(0,0,0,H);
  g.addColorStop(0,'#04140f'); g.addColorStop(1,'#061a2a');
  ctx.fillStyle=g; ctx.fillRect(0,0,W,H);
  const n=40, bw=W/n;
  for(let i=0;i<n;i++){
    const v = 0.5+0.5*Math.sin(t*3.2+i*0.5)*Math.sin(t*1.1+i*0.13);
    const vv = Math.abs(v);
    const h = H*0.08 + vv*H*0.62;
    const x = i*bw+bw*0.16, w=bw*0.68;
    const grd = ctx.createLinearGradient(0,H-h,0,H);
    grd.addColorStop(0,`hsla(${160+i*3},90%,65%,0.95)`);
    grd.addColorStop(1,`hsla(${190+i*3},90%,45%,0.9)`);
    ctx.fillStyle=grd;
    ctx.fillRect(x,H*0.78-h,w,h);
    // reflection
    ctx.globalAlpha=0.18;
    ctx.fillRect(x,H*0.78,w,h*0.5);
    ctx.globalAlpha=1;
  }
  // baseline
  ctx.fillStyle='rgba(0,255,200,0.35)'; ctx.fillRect(0,H*0.78,W,2);
}
```

Hmm careful with globalAlpha reset. Ok.

Scene rings:

```js
rings(ctx,W,H,t,c){
  const g=ctx.createRadialGradient(W/2,H/2,20,W/2,H/2,H);
  g.addColorStop(0,'#1a0f33'); g.addColorStop(1,'#05030c');
  ctx.fillStyle=g; ctx.fillRect(0,0,W,H);
  ctx.save();
  ctx.translate(W/2,H/2);
  ctx.rotate(t*0.25);
  for(let i=0;i<9;i++){
    const r = H*(0.08+i*0.055) + Math.sin(t*1.4+i*0.6)*8;
    ctx.beginPath();
    ctx.arc(0,0,r, i*0.7 + t*0.6, i*0.7 + t*0.6 + 1.6 + (i%3)*0.6);
    ctx.strokeStyle = `hsla(${270+i*12},85%,${60+ (i%3)*6}%,0.85)`;
    ctx.lineWidth = 2 + (i%4);
    ctx.lineCap='round';
    ctx.stroke();
  }
  ctx.restore();
  // center dot
  ctx.fillStyle='rgba(240,220,255,.9)';
  ctx.beginPath(); ctx.arc(W/2,H/2,5+Math.sin(t*4)*1.5,0,TAU); ctx.fill();
}
```

Good.

Now the app code. Let me write it linearly.

```js
const preview = document.getElementById('preview');
const pctx = preview.getContext('2d');
```

State & clips creation.

```js
const videoClips = [
  {id:'v1', name:'Neon Grid', scene:'grid', start:0, dur:5.5, transIn:null, color:'#3b82f6'},
  {id:'v2', name:'Orbit', scene:'orbit', start:5.5, dur:5.0, transIn:{type:'crossfade',dur:0.7}, color:'#f59e0b'},
  {id:'v3', name:'Spectrum', scene:'bars', start:10.5, dur:5.0, transIn:{type:'wipe',dur:0.8}, color:'#10b981'},
  {id:'v4', name:'Rings', scene:'rings', start:15.5, dur:5.0, transIn:{type:'crossfade',dur:0.7}, color:'#a855f7'},
];
```

Initial state copy for reset: store JSON deep copy.

Text clips and audio clip.

DOM building:

```js
const trackVideo = document.getElementById('trackVideo');
const trackText = document.getElementById('trackText');
const trackAudio = document.getElementById('trackAudio');

function makeClipEl(clip, kind){
  const el = document.createElement('div');
  el.className = 'clip ' + kind;
  el.innerHTML = `<div class="label">${clip.name||clip.text}</div>`;
  ...
}
```

For video clips: add `.thumb` decorative and handles.

For transitions: a child div `.trans` with class type, plus a label.

Actually, let me render transition as a separate absolutely-positioned overlay inside the clip's parent track. Simpler: append inside clip element at left with width = transDur*pps. But that region is in the previous clip's time — outside this clip's element. So it must be a sibling in the track. I'll create a separate element per clip transition, appended to the track.

Let's maintain a list of transition elements created once and positioned in layout().

```js
const transEls = videoClips.map(c=>{
  if(!c.transIn) return null;
  const el=document.createElement('div');
  el.className='trans '+(c.transIn.type);
  el.innerHTML=`<span>${c.transIn.type==='crossfade'?'✕ fade':'▤ wipe'}</span>`;
  trackVideo.appendChild(el);
  return el;
});
```

Position in layout: left = (c.start - c.transIn.dur)*pps, width = c.transIn.dur*pps. top:0;bottom:0 with pointer-events none and a striped bg.

Hmm the transition overlay sits over the previous clip's tail. With a translucent stripe pattern + label, it looks like a transition region. Good.

Ruler drawing:

```js
function drawRuler(){
  const px=ppsPx;
  rulerEl.innerHTML='';
  const step = px>90?0.5:1;   // minor step
  ...
}
```
I'll create tick divs. For major ticks every second (or 2s if px<40). Labels: format seconds as `0:05`.

Since DUR=22, ticks = 22 majors * 2 minors. Fine.

Positions: left = t*px.

Add in/out markers as separate elements in the ruler (not rebuilt each layout, just positioned).

Let me just rebuild everything in layout() — simpler, and 22s * few elements is cheap. But rebuilding every frame would be bad; layout() is called only on zoom/edit changes, and playhead moves separately. In/out marker positions also change during tween → call layout() during tween along with layout updates. That's per-frame during tweens (2s). Rebuilding ~90 DOM nodes per frame for 2 seconds... acceptable but let's avoid: separate `positionInOut()` function for markers, and only rebuild ruler on zoom change.

Plan:
- `buildRuler()` — called on zoom change (creates tick divs).
- `layout()` — positions clips, transitions, in/out markers, playhead; called on edits/zoom.
- `updatePlayhead()` — per frame.

In/out shading: two divs (before in, after out) in the ruler area extending over tracks? Let's shade the whole timeline: a `div.shade` in tlContent with left/width. I'll add two shade divs spanning the full track height (position absolute top:0 bottom:0). With background rgba(0,0,0,.35), pointer-events none. And in/out markers as small flags in the ruler.

OK.

Let me write final code now, being careful.

```js
// ===== Element refs
const preview=document.getElementById('preview'), pctx=preview.getContext('2d');
const tlScroll=document.getElementById('tlScroll');
const tlContent=document.getElementById('tlContent');
const rulerEl=document.getElementById('ruler');
const playheadEl=document.getElementById('playhead');
const trackVideo=document.getElementById('trackVideo');
const trackText=document.getElementById('trackText');
const trackAudio=document.getElementById('trackAudio');
const tcEl=document.getElementById('tc'), inTcEl=document.getElementById('inTc'), outTcEl=document.getElementById('outTc');
const logEl=document.getElementById('log');
const ghost=document.getElementById('ghost');
const badge=document.getElementById('transBadge');
const hud=document.getElementById('hud');
```

Now build clips.

```js
let ppsPx = BASE_PPS; // updated by zoom
```

Create video clip elements:

```js
videoClips.forEach((c,i)=>{
  const el=document.createElement('div');
  el.className='clip video';
  el.style.background = `linear-gradient(180deg, ${c.color}cc, ${c.color}55)`;
  el.innerHTML = `<div class="label">${c.name}</div><div class="accent" style="background:${c.color}"></div>
     <div class="handle l"></div><div class="handle r"></div>`;
  c.el = el;
  trackVideo.appendChild(el);
  attachDrag(el, c);
});
```

Hmm `.accent` — maybe skip. Keep the label and handles.

Thumbnails: add a strip of small canvases? Nah, use CSS stripes:

```css
.clip.video::after{content:'';position:absolute;left:0;right:0;bottom:0;height:calc(100% - 18px);background-image:repeating-linear-gradient(90deg, rgba(255,255,255,.07) 0 2px, transparent 2px 8px);}
```
Good enough. Maybe better: draw a tiny canvas per clip showing a frame? It'd be nice, but let's keep the stripes for performance/simplicity. Actually a mini preview render would look pro... but 4 canvases at maybe 100x40 each, rendered once, static. Let's do it! On layout, if zoom changes, we could redraw. Simple: create a canvas inside each clip, draw the scene at a representative time, but width varies with zoom. Just redraw at build (fixed size, CSS 100% width) — scale it. Let's create the canvas with fixed backing size 160x64 and CSS width:100%;height:100%;object-fit:cover. Draw once at build with a mid-time. Cheap and looks good.

Yes! Do that. `renderThumb(canvas, clip, tLocal)`.

```js
function makeThumb(clip){
  const cv=document.createElement('canvas');
  cv.width=160; cv.height=72;
  const cx=cv.getContext('2d');
  const scene=SCENES[clip.scene];
  scene(cx,160,72,1.2,clip);
  cv.style.cssText='position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.75';
  return cv;
}
```
And the label sits above with a gradient overlay.

Nice.

For the text clips, similar but with a text preview.

Now attach drag handlers.

```js
function attachDrag(el, clip, kind){
  el.addEventListener('pointerdown', e=>{
    if(e.button!==0) return;
    const handle = e.target.classList.contains('handle') ? (e.target.classList.contains('l')?'l':'r') : null;
    startDrag(e, clip, handle||'move');
  });
}

function startDrag(e, clip, mode){
  e.preventDefault();
  const startX=e.clientX;
  const s0=clip.start, d0=clip.dur;
  el.setPointerCapture? // capture on the element
  ...
  const onMove=ev=>{
    const dx=(ev.clientX-startX)/ppsPx;
    if(mode==='move') clip.start = clamp(round(s0+dx),0,DUR-clip.dur);
    else if(mode==='l'){
      const ns=clamp(round(s0+dx),0,s0+d0-0.3);
      clip.start=ns; clip.dur=round(d0+(s0-ns));
    } else {
      clip.dur=clamp(round(d0+dx),0.3,DUR-clip.start);
    }
    layout();
  };
  const onUp=ev=>{
    window.removeEventListener('pointermove',onMove);
    window.removeEventListener('pointerup',onUp);
    el.classList.remove('dragging');
  };
  window.addEventListener('pointermove',onMove);
  window.addEventListener('pointerup',onUp);
  el.classList.add('dragging');
}
function round(v){ return Math.round(v*20)/20; }
```

Careful: when trimming left, the dur must stay within DUR.

Also the clip's el needs `touch-action:none`.

Now layout():

```js
function layout(){
  ppsPx = BASE_PPS*state.zoom;
  const totalW = DUR*ppsPx;
  tlContent.style.width = totalW+'px';

  videoClips.forEach((c,i)=>{
    c.el.style.left = (c.start*ppsPx)+'px';
    c.el.style.width = Math.max(6,c.dur*ppsPx)+'px';
    const te = transEls[i];
    if(te){
      te.style.left = ((c.start-c.transIn.dur)*ppsPx)+'px';
      te.style.width = (c.transIn.dur*ppsPx)+'px';
      te.style.display = c.start-c.transIn.dur >= 0 ? 'block':'none';
    }
  });
  textClips.forEach(c=>{ c.el.style.left=(c.start*ppsPx)+'px'; c.el.style.width=Math.max(6,c.dur*ppsPx)+'px'; });
  audioClip.el.style.left=(audioClip.start*ppsPx)+'px';
  audioClip.el.style.width=(audioClip.dur*ppsPx)+'px';

  // in/out shading & markers
  shadeL.style.left='0px'; shadeL.style.width=(state.inPoint*ppsPx)+'px';
  shadeR.style.left=(state.outPoint*ppsPx)+'px'; shadeR.style.width=Math.max(0,(DUR-state.outPoint)*ppsPx)+'px';
  inMarker.style.left=(state.inPoint*ppsPx)+'px';
  outMarker.style.left=(state.outPoint*ppsPx)+'px';

  if(needRuler) buildRuler();
  updatePlayhead();
  drawWaveform();
}
```

drawWaveform depends on ppsPx → called in layout. Fine (22s*50px = 1100px canvas width, redraw on zoom only → ok).

buildRuler on zoom change only; set flag when zoom changes.

Actually simpler: rebuild ruler in layout() but layout() isn't called every frame (only on edits/tweens/zoom). During tweens it's called per frame for 2s → rebuilding ~70 divs per frame for 2 seconds. Hmm, risky but probably fine. Let's guard it with a `lastRulerZoom` check.

```js
let rulerZoom=-1;
function buildRulerIfNeeded(){
  if(rulerZoom===state.zoom) return;
  rulerZoom=state.zoom;
  ... build
}
```

Good.

Playhead:

```js
function updatePlayhead(){
  playheadEl.style.transform = `translateX(${state.playhead*ppsPx}px)`;
}
```
With `left:0; top:0; bottom:0; width:2px` and transform translateX. Good.

Auto-scroll in the frame loop.

Timecode:

```js
function fmt(t){
  t=Math.max(0,t);
  const total = Math.floor(t*30);
  const f = total%30, s=Math.floor(total/30)%60, m=Math.floor(total/1800)%60, h=Math.floor(t/3600);
  return `${pad(h)}:${pad(m)}:${pad(s)}:${pad(f)}`;
}
```

Now the main loop.

```js
let last=performance.now();
function frame(now){
  let dt=(now-last)/1000; last=now;
  dt=Math.min(dt,0.05);
  if(state.playing){
    state.playhead += dt;
    if(state.playhead>=DUR) state.playhead-=DUR;
  }
  updateDemo(dt);
  drawFrame(state.playhead);
  updatePlayhead();
  autoScroll();
  updateHud();
  requestAnimationFrame(frame);
}
```

updateDemo:

```js
function updateDemo(dt){
  demo.clock += dt;
  for(const ev of demo.events){
    if(!ev.done && demo.clock>=ev.t){ ev.done=true; ev.f(); }
  }
  if(demo.clock > 28){
    resetDemo();
  }
  // tweens
  for(let i=tweens.length-1;i>=0;i--){
    const tw=tweens[i];
    tw.t+=dt;
    const p=clamp(tw.t/tw.dur,0,1);
    tw.update(tw.from+(tw.to-tw.from)*easeInOut(p));
    if(p>=1){ tweens.splice(i,1); if(tw.done) tw.done(); }
  }
  updateGhost();
}
```

resetDemo: reset clock=0, events done=false, restore clips (deep copy of initial), in/out, clear log, hide ghost.

But note: resetDemo happens while tweens might be running — clear tweens too.

Also `demo.clock` restart. Good, loops every 28s.

Also, since the recording is the first 30 seconds, we want the demo to loop nicely. 28s cycle works.

Now, the "trim" tween modifies v3.dur from 5.0 → 3.6. But wait: at 5.5s demo time, is clip 3 playing? The playhead loops every 22s independently of the demo clock. Doesn't matter.

Hmm, one issue: the trimmed clip's duration change happens at demo t=5.5 while the playhead might be at, say, 5.5s of timeline (since demo clock and playhead both start at 0 at the same time and both advance in real time; the playhead loops at 22s so for the first 22 seconds playhead time == demo clock). So at demo t=5.5, the playhead is at 5.5s — right at the crossfade between clip1 and clip2! Nice.

Demo t=10.0: playhead at 10.0s → clip3 (Spectrum) starts at 10.5 with a wipe at [9.7,10.5]. So at t=10 we're mid-wipe, and we start moving clip 4 — not visible in the preview at that moment, but the timeline shows it. Fine. Actually, the trim tween runs 5.5→7.5 and the move runs 10→12. Meanwhile the playhead goes 5.5→12 through clips 2, 3. Good.

But careful: trimming clip3's duration while the playhead is around 7-8s doesn't affect the preview. Then at playhead ~10.5-14 we see clip3 shortened and a gap 14.1-15.5, then clip4 moved. Playhead reaches 14.1 at t=14.1 demo time, gap [14.1,15.5] is BEFORE the move tween finishes (move runs 10→12, so by 14.1 the move is done and clip4 starts at 14.1). Good — no gap visible in the preview, since by the time the playhead arrives, the gap is closed. 

So the preview stays continuous. Nice.

But wait: after the trim, clip3 spans [10.5, 14.1]; the gap [14.1,15.5] exists between demo times 7.5 and 12. Playhead is at 7.5..12 during that window, never inside the gap. 

Now, does the playhead hit clip4's area? clip4 now starts at 14.1 and ends at 19.1. Playhead reaches 19.1 at demo t=19.1 and 22 at t=22 → then loops. During demo t 22..28 the playhead runs 0..6 with everything static. Fine.

Great.

Also the IN point tween at demo 2.0 → inPoint becomes 1.0. OUT at demo 22 → 19.0. Hmm out at 19.0 while clip4 ends at 19.1 — fine.

Let me reconsider the events list to make sure everything important shows in 30s:

- 0.2: toast "Auto demo — playback"
- 2.0: mark IN (toast)
- 5.5: trim clip 3 (toast + ghost cursor drag) — visible in timeline
- 10.0: move clip 4 (toast + ghost cursor)
- 14.5: toast about transitions (badge shows "CROSSFADE"/"WIPE" in preview when active)
- 18.0: toast titles
- 22.0: mark OUT
- 26.0: toast "Looping demo…"
- 28.0: reset

Good.

Transition badge in the preview: show when a transition is active. In drawFrame I can set a DOM element. Let's just do it in updateHud: check if any transition is active at playhead, set badge text/opacity.

```js
function activeTransition(t){
  const covering = videoClips.filter(c=>t>=c.start&&t<c.start+c.dur).sort((a,b)=>a.start-b.start);
  const cur = covering.length?covering[covering.length-1]:null;
  if(!cur) return null;
  const nxt = videoClips.filter(c=>c.transIn && c.start>cur.start).sort((a,b)=>a.start-b.start)[0];
  if(!nxt) return null;
  const d=nxt.transIn.dur;
  if(t>=nxt.start-d) return {type:nxt.transIn.type, p:(t-(nxt.start-d))/d};
  return null;
}
```

Use in both drawFrame and HUD.

HUD bottom-left shows current clip name; badge top-right shows transition.

OK, write it.

Now the resize handling for the preview canvas: fixed 960x540 backing store. CSS max-width/max-height 100%. Fine.

Let's also handle devicePixelRatio? Not needed for a canvas scaled by CSS; 960x540 scaled is fine.

Now writing CSS in detail.

```css
*{box-sizing:border-box}
html,body{margin:0;height:100%;overflow:hidden;background:#080a0e;color:#c7d0dd;
  font-family:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;font-size:13px}
.app{display:flex;flex-direction:column;height:100vh}

/* toolbar */
.toolbar{height:50px;flex:none;display:flex;align-items:center;gap:14px;padding:0 14px;
  background:linear-gradient(180deg,#151922,#10131a);border-bottom:1px solid #232936;position:relative;z-index:5}
.brand{display:flex;align-items:center;gap:8px;font-weight:700;letter-spacing:.14em;font-size:12px;color:#e8eefc}
.brand i{width:10px;height:10px;border-radius:3px;background:linear-gradient(135deg,#38bdf8,#a855f7);display:block;box-shadow:0 0 10px #38bdf8aa}
.brand small{font-weight:400;color:#5f6b80;letter-spacing:.06em;margin-left:2px}
...
```

Buttons:

```css
button{font:inherit;color:#c7d0dd;background:#1a1f2b;border:1px solid #2b3342;border-radius:6px;height:28px;min-width:32px;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;transition:.15s}
button:hover{background:#232a38;border-color:#3a4557}
button.active{background:#1d3a52;border-color:#38bdf8;color:#dff2ff}
```

Timecode:

```css
.timecode{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:16px;font-weight:600;color:#eaf6ff;
  background:#0b0e14;border:1px solid #2b3342;border-radius:6px;padding:3px 10px;letter-spacing:.06em;
  box-shadow:inset 0 0 12px rgba(56,189,248,.08)}
```

Now the timeline section CSS, including track headers.

Let me write the full HTML now. I'll be thorough.

One thing: the `.tl-headers` heights must match `.ruler` (26px) + track heights. I'll define:

```css
.ruler{height:26px}
.track{height:62px}
.track.text-track{height:42px}
.track.audio-track{height:64px}
```

Headers: `.h-spacer{height:26px}` `.h-track{height:62px;...}` etc.

Total body height: 26+62+42+64 = 194. Plus maybe a bottom filler.

Timeline container height: 34 (tl-toolbar) + 194 + padding = ~250. Set `.timeline{height:262px}`.

Let's finalize: timeline height 264px.

Now the preview panel: stage flex:1 min-height:0.

Let's write it.

For the side panel, width 260px.

```css
.side{width:262px;flex:none;background:#10131a;border:1px solid #232936;border-radius:8px;padding:10px;display:flex;flex-direction:column;gap:8px;overflow:hidden}
.side h3{margin:0;font-size:10px;letter-spacing:.16em;color:#5f6b80;text-transform:uppercase;font-weight:600}
.kv{display:flex;justify-content:space-between;font-size:12px;padding:4px 0;border-bottom:1px solid #1a1f29}
.kv span{color:#77839a}
.kv b{color:#dbe6f5;font-weight:600}
.log{flex:1;overflow:hidden;display:flex;flex-direction:column;gap:4px;font-size:11.5px;justify-content:flex-end}
.log div{color:#9fb0c6;background:#151a24;border-left:2px solid #38bdf8;padding:4px 7px;border-radius:4px;animation:slide .3s ease}
```

@keyframes slide { from{opacity:0;transform:translateX(8px)} to{opacity:1;transform:none} }

Keep max 6 entries.

Now write drawFrame and the rest.

Also need `drawScene`:

```js
function drawScene(ctx,W,H,t,clip){
  const lt = t - clip.start;
  const fn = SCENES[clip.scene] || SCENES.grid;
  ctx.save();
  fn(ctx,W,H,lt,clip);
  ctx.restore();
  ctx.globalAlpha = 1;
}
```

Scenes set globalAlpha sometimes — wrap in save/restore, and reset globalAlpha after.

Now let's write the final file.

Also handle `pointerdown` on the ruler to seek.

Also the play button toggles state.playing and updates the icon.

Let me write everything out.

For the audio clip waveform canvas:

```js
const audioClip = {id:'a1', name:'Ambient Pad', start:0, dur:DUR};
const audioEl = document.createElement('div');
audioEl.className='clip audio';
const wf = document.createElement('canvas');
wf.className='wave';
audioEl.appendChild(wf);
audioEl.innerHTML += '<div class="label">Ambient Pad</div>';
```
Careful: innerHTML += would destroy the canvas. Build with createElement and append in order.

drawWaveform():
```js
function drawWaveform(){
  const w = Math.max(10, Math.round(audioClip.dur*ppsPx));
  const h = 56;
  wf.width = w; wf.height = h;
  const c = wf.getContext('2d');
  c.clearRect(0,0,w,h);
  c.fillStyle='rgba(74,222,128,0.85)';
  const mid=h/2;
  for(let x=0;x<w;x+=2){
    const t = x/w*DUR;
    const a = audioLevel(t);
    const amp = a*mid*0.92;
    c.fillRect(x, mid-amp, 1.4, amp*2);
  }
  // center line
  c.fillStyle='rgba(255,255,255,0.18)'; c.fillRect(0,mid-0.5,w,1);
}
```
wf CSS: position absolute inset 0, width 100%, height 100%.

Since the canvas backing store is w x 56 and CSS is 100% x 100%, it stretches slightly; fine.

Label on the audio clip should be on top.

OK, writing now for real. I'll produce the final code.

One more: `updateHud()`:

```js
function updateHud(){
  const t=state.playhead;
  const covering = videoClips.filter(c=>t>=c.start&&t<c.start+c.dur).sort((a,b)=>a.start-b.start);
  const cur = covering.length?covering[covering.length-1]:null;
  hud.textContent = cur ? `V1 · ${cur.name}` : 'V1 · —';
  const tr = activeTransition(t);
  if(tr){
    badge.style.opacity=1;
    badge.textContent = (tr.type==='crossfade'?'✕ CROSSFADE':'▤ WIPE') + ' ' + Math.round(clamp(tr.p,0,1)*100)+'%';
  } else badge.style.opacity=0;
}
```

Also update the timecode element each frame: `tcEl.textContent = fmt(t)`.

Fine, do it in the frame loop.

Let me write the final code.

Also, the inspector should show live info: current clip, transition, in/out. Let's update a few fields per frame cheaply.

I'll write the inspector with elements: inspClip, inspTrans, inspPos.

Now writing.

Also: `autoScroll` — need to only scroll when the playhead goes out of view, and not fight the user. Fine.

Let's write out everything.

Regarding the audio clip intersection with DUR: ok.

Final detail: `transEls` created after video clips elements. Order in the DOM affects stacking: transitions appended after clips → they'd be on top. Good, with pointer-events:none.

Let me write out the code.

```js
const state = { playhead: 0, playing: true, zoom: 1, inPoint: 0, outPoint: DUR };
```

Reset: state.inPoint=0, state.outPoint=DUR, zoom keep.

Initial clip snapshot: `const INIT = JSON.parse(JSON.stringify(videoClips.map(c=>({start:c.start,dur:c.dur}))))`.

Write resetDemo:

```js
function resetDemo(){
  demo.clock=0;
  demo.events.forEach(e=>e.done=false);
  tweens.length=0;
  grabClip=null;
  videoClips.forEach((c,i)=>{ c.start=INIT[i].start; c.dur=INIT[i].dur; });
  state.inPoint=0; state.outPoint=DUR;
  state.playhead=0;
  logEl.innerHTML='';
  layout();
}
```

Careful: INIT computed after clips are defined.

Now the events array references videoClips[2] and videoClips[3].

Let me write the events with proper indices.

Alright — writing the final answer now.

One more consideration on `drawTitle` positioning: place at y = H*0.78, and the audio meter at bottom-left. Fine.

Also add a subtle vignette/scanlines over the preview for a "pro" look? A slight vignette. Optional — skip.

Time to write it all.

Let me write the HTML body structure fully:

```html
<div class="app">
  <header class="toolbar">
    <div class="brand"><i></i>NOVACUT<small>v1.4</small></div>
    <div class="tools">
      <button class="tbtn active" title="Select">⬉</button>
      <button class="tbtn" title="Razor">✂</button>
      <button class="tbtn" title="Text">T</button>
      <button class="tbtn" title="Transitions">⇄</button>
    </div>
    <div class="spacer"></div>
    <div class="transport">
      <button id="btnStart" title="Go to start">⏮</button>
      <button id="btnPlay" class="play" title="Play/Pause">❚❚</button>
      <button id="btnEnd" title="Go to end">⏭</button>
    </div>
    <div class="timecode" id="tc">00:00:00:00</div>
    <div class="io">
      <div class="chip">IN <b id="inTc">00:00:00:00</b></div>
      <div class="chip">OUT <b id="outTc">00:00:22:00</b></div>
    </div>
    <div class="zoomwrap">
      <span>ZOOM</span>
      <input id="zoom" type="range" min="0.55" max="2.6" step="0.01" value="1">
    </div>
  </header>
  <div class="stage">
    <div class="preview-panel">
      <canvas id="preview" width="960" height="540"></canvas>
      <div class="badge" id="transBadge">CROSSFADE</div>
      <div class="hud" id="hud">V1 · —</div>
    </div>
    <aside class="side">
      <h3>Inspector</h3>
      <div class="kv"><span>Clip</span><b id="inspClip">—</b></div>
      <div class="kv"><span>Transition</span><b id="inspTrans">—</b></div>
      <div class="kv"><span>Position</span><b id="inspPos">00:00:00:00</b></div>
      <div class="kv"><span>Duration</span><b id="inspDur">00:00:22:00</b></div>
      <h3>Activity</h3>
      <div class="log" id="log"></div>
    </aside>
  </div>
  <div class="timeline">
    <div class="tl-toolbar">
      <span class="tl-title">TIMELINE</span>
      <div class="tl-legend"><i class="lc v"></i>Video<i class="lc t"></i>Text<i class="lc a"></i>Audio</div>
      <div class="spacer"></div>
      <span class="tl-hint">drag clips & edges • click ruler to seek</span>
    </div>
    <div class="tl-body">
      <div class="tl-headers">
        <div class="h-spacer"></div>
        <div class="h-track h-video">V1<span>VIDEO</span></div>
        <div class="h-track h-text">T1<span>TITLES</span></div>
        <div class="h-track h-audio">A1<span>AUDIO</span></div>
      </div>
      <div class="tl-scroll" id="tlScroll">
        <div class="tl-content" id="tlContent">
          <div class="ruler" id="ruler"></div>
          <div class="track track-video" id="trackVideo"></div>
          <div class="track track-text" id="trackText"></div>
          <div class="track track-audio" id="trackAudio"></div>
          <div class="shade" id="shadeL"></div>
          <div class="shade" id="shadeR"></div>
          <div class="marker in" id="inMarker"><span>IN</span></div>
          <div class="marker out" id="outMarker"><span>OUT</span></div>
          <div class="playhead" id="playhead"></div>
        </div>
      </div>
    </div>
  </div>
  <div class="ghost" id="ghost"></div>
</div>
```

The shade divs should span from the ruler top to the bottom of the tracks. Since tl-content contains ruler+tracks, shade with position absolute top:0;bottom:0 works.

Note z-index ordering: shades under clips (shade z-index 1, clips z-index 2), markers on top, playhead topmost.

Playhead: `position:absolute;top:0;bottom:0;width:2px;background:#ff5d5d;z-index:20;pointer-events:none;box-shadow:0 0 8px rgba(255,80,80,.8)` with a head triangle via ::before.

Marker: `position:absolute;top:0;height:100%;width:0;border-left:1px dashed`? Let's do a flag at the ruler top: a small div with a label, positioned at left = inPoint*px, with `top:0;height:26px` and a downward line? Simpler: a small triangle+label at the ruler, plus a 1px vertical line across the tracks. Use `::after` for the line.

Let's do:
```css
.marker{position:absolute;top:0;bottom:0;width:0;z-index:15;pointer-events:none}
.marker span{position:absolute;top:1px;font-size:9px;font-weight:700;letter-spacing:.08em;padding:1px 4px;border-radius:3px;transform:translateX(-50%);white-space:nowrap}
.marker.in{border-left:1px solid #4ade80}
.marker.out{border-left:1px solid #fbbf24}
.marker.in span{background:#166534;color:#bbf7d0;border:1px solid #22c55e}
.marker.out span{background:#78350f;color:#fde68a;border:1px solid #f59e0b}
```
Hmm, the line covers the whole height — that's fine, subtle.

But the span at translateX(-50%) — for the IN marker at left:0, the label would be half off-screen. It's fine.

Now the ruler: I'll draw ticks as divs with labels.

```js
function buildRulerIfNeeded(){
  if(rulerZoom===state.zoom) return;
  rulerZoom=state.zoom;
  rulerEl.innerHTML='';
  const px=ppsPx;
  const majorStep = px>=110?1:px>=55?2:5;
  for(let s=0;s<=DUR;s+=0.5){
    const isMajor = Math.abs(s/Mj - Math.round(s/Mj))<1e-6;
  }
}
```
Simpler loop:
```js
for(let i=0;i<=DUR*2;i++){
  const t=i/2;
  const major = (t%  majorStep)==0 → floating point, use integer check.
}
```
Use: `const total = Math.round(DUR*2); for(let i=0;i<=total;i++){ const t=i/2; const isMajor = i%2===0 && (t % majorStep === 0); }` — t is a multiple of 0.5 so t%1 and t%2 are exact enough.

Let me use `Math.abs(t - Math.round(t/majorStep)*majorStep) < 1e-6`.

Tick div: `position:absolute;left:t*px;bottom:0;width:1px;height:8px;background:#3a4557`.

Label: `position:absolute;left:t*px+4;top:3px;font-size:10px;color:#66738a`. Format: `0:05`.

Also add a "0:00" label.

Fine.

Now let me write the final JS in order:

1. Constants & utils
2. Audio data
3. Scenes
4. State & clips
5. DOM refs
6. Build timeline DOM (clips, transitions, text, audio)
7. Layout & ruler
8. Waveform
9. Drag
10. Demo script & tweens
11. Frame loop & render
12. Events (buttons, zoom, ruler click)

Let's write it.

For the text clips' elements:

```js
textClips.forEach(c=>{
  const el=document.createElement('div');
  el.className='clip textclip';
  el.innerHTML=`<div class="label">${c.text}</div>`;
  c.el=el;
  trackText.appendChild(el);
  attachDrag(el,c);
});
```

Text clip CSS: background linear-gradient(#b7791f... ) hmm use a purple/amber. Let's use `linear-gradient(180deg,#8b5cf6aa,#6d28d955)` with a left accent bar.

Actually make text clips visually distinct: amber.

OK, writing final.

Also, `attachDrag` for text clips: mode 'move' only. The handles aren't present so `e.target.classList.contains('handle')` is false → 'move'. Good.

Final code writing time. I'll be careful about syntax.

For `activeTransition`, I need it consistent between drawFrame and HUD.

Let me write drawFrame using a helper that returns layers.

```js
function computeLayers(t){
  const covering = videoClips.filter(c=> t>=c.start && t<c.start+c.dur).sort((a,b)=>a.start-b.start);
  const cur = covering.length ? covering[covering.length-1] : null;
  let next=null, p=0;
  if(cur){
    const cand = videoClips.filter(c=> c.transIn && c.start > cur.start).sort((a,b)=>a.start-b.start)[0];
    if(cand){
      const d=cand.transIn.dur;
      if(t >= cand.start - d){ next=cand; p=clamp((t-(cand.start-d))/d,0,1); }
    }
  } else {
    const cand = videoClips.filter(c=> c.transIn && t>=c.start-c.transIn.dur && t<c.start).sort((a,b)=>a.start-b.start)[0];
    if(cand){ next=cand; p=clamp((t-(cand.start-cand.transIn.dur))/cand.transIn.dur,0,1); }
  }
  return {cur,next,p};
}
```

Then drawFrame uses it.

Note: when cur is null and next exists, we draw next with alpha p over black.

Alright.

Writing everything out now.

Also make sure `SCENES` functions don't leave globalAlpha modified: each does ctx.save()/restore() internally? I call them within save/restore in drawScene, so fine as long as they don't set globalAlpha and rely... they can set it, restore fixes it.

Let me finalize `drawScene`:
```js
function drawScene(ctx,W,H,t,clip){
  ctx.save();
  (SCENES[clip.scene]||SCENES.grid)(ctx,W,H,t-clip.start,clip);
  ctx.restore();
  ctx.globalAlpha=1;
}
```

Good.

Now write it.

For the ghost cursor animation during tweens, I'll set `grabClip` and `grabMode` when starting a tween, and clear on completion.

```js
function tween(from,to,dur,update,done){ tweens.push({t:0,dur,from,to,update,done}); }
```

In updateGhost: if grabClip && grabClip.el → position ghost at edge.

Alright. Writing the final answer.

Double-check the demo trim tween modifies `videoClips[2].dur` from 5.0 to 3.6 and the move tween modifies `videoClips[3].start` from 15.5 to 14.1.

After the reset, they go back.

Also `layout()` must be called when these change — yes, inside the tween update.

Let me also ensure that during the trim, the transition element for clip 3 (wipe at [9.7,10.5]) stays valid — clip3.start unchanged, so yes.

But careful: after the move, clip4.start = 14.1 and clip3 ends at 10.5+3.6 = 14.1. Good.

Wait, the trim reduces clip3.dur from 5.0 to 3.6, so clip3 spans [10.5, 14.1]. Yes.

Now writing.

One more: the initial `state.outPoint = DUR = 22`, and after reset it's restored.

Also the OUT tween at demo t=22 goes 22→19.0.

Fine.

Let me write the code.

Regarding the canvas preview being letterboxed: `#preview{max-width:100%;max-height:100%;display:block;border-radius:6px;background:#000;box-shadow:0 0 0 1px #232936, 0 18px 40px rgba(0,0,0,.6)}`. With intrinsic size 960x540 and max constraints, it scales down maintaining aspect. Good.

Now write.

I'll also add a small "REC ●" style indicator to look pro. Maybe not needed.

Writing final answer now.