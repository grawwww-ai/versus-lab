Let me create a single HTML file that includes a Breakout game, with an auto-play demo mode (toggled by P key), auto-start, and everything needs to be displayed within 30 seconds. So the game should be reasonably fast — maybe speed up the block destruction, or have the AI be competent and play fast. Let me have the auto-start be in demo mode, and maybe start with a smaller grid or a faster ball.

Requirements:
- Paddle at the bottom of the screen, moves horizontally
- Ball bounces off walls/paddle/blocks
- Blocks in a grid at the top
- Ball speed increases with each hit
- Game ends when all blocks are cleared, or when the ball falls below the paddle
- Display of score and lives
- Arrow keys left/right, space to launch/restart
- Auto-start
- Vanilla JS
- P key toggles auto-play demo where AI competently controls the player
- Within the first 30 seconds, display everything important; may loop afterwards

Let me start in auto-play demo mode, make the game fast (maybe fewer rows), and make the AI very good so that lives are barely lost. Once the blocks are cleared, the level resets with more blocks and the loop continues.

Let me design:
- Canvas 800x600
- Paddle width ~100, height 14, y at ~560
- Ball radius 7, base speed ~6, increases by ~0.35 per block hit, with a cap
- Blocks: 8 columns, 5 rows, with colors; block width ~90 with spacing, top margin
- 3 lives
- Space: launch ball (initially ball is stuck on paddle), also restart when game over
- P: toggle auto-play

AI: target x = predicted ball x position when reaching paddle y (simple: just the ball's x, with some lead added; maybe include a simple prediction with reflection). Simply: when the ball is moving toward the paddle, paddle x = ball x (+ a slight offset based on the ball's relative velocity). The AI is competent — occasionally aim to break more blocks? Keep it simple: track the ball's x with a maximum velocity limit to make it look natural. Also, on the first launch, the AI auto-launches.

Game over: if a life is lost and lives > 0, reset the ball on the paddle (waiting state); if lives == 0, game over screen, space to restart. In demo mode, auto-restart after a brief pause.

Loop within 30 seconds: with 5 rows × 8 columns = 40 blocks, ball speed 6px/frame at 60fps = 360px/s. Each hit adds speed. At an average of 200px/frame, the time per block is… roughly. The ball crosses the ~550px height in under 1 second, hits several blocks per round trip. 40 blocks might take ~30-60 seconds. To fit in 30 seconds, speed up: base speed 7, +0.4 per hit, max 16. Or fewer rows: 4 rows × 8 columns = 32. Let me calculate: average speed ~9px/frame = 540px/s, ball travels ~150-300px between blocks (vertical distance ~550/… actually the ball mostly travels vertically). Each block hit interval: ball travels ~40px vertically on average? No — block height is ~20, spacing ~4px; a single vertical pass can break 4-5 blocks. So per round trip (600px) ~8 blocks, at 540px/s that's ~1.1 sec → ~7 blocks/sec → 40 blocks in ~6 sec?? That's too optimistic, but the ball's angle varies. In any case, ~30 seconds should be fine. Let me make the demo start with a smaller grid (4 rows), and after clearing, add rows and regenerate the level with a max of 6 rows, to maintain loop pacing.

Also, the ball can be stuck on the paddle and bounce at a random-ish angle; in demo, auto-launch.

Add a slight AI imperfection? "Plays competently" — keep lives at max, or occasionally lose one life to show the lives UI. Maybe give a small random error that occasionally causes a miss. Simpler: make it perfect, and occasionally intentionally… let me add a small random offset; with speed up, occasionally lose a life, but probably survive. That's good for the demo (shows the lives UI changing). Keep the offset small.

Score: +10 per block, maybe +life bonus on clear.

Implementation details:
- requestAnimationFrame loop, roughly fixed step (just per frame).
- Collision with blocks: circle vs AABB, with side detection for bounce direction.
- Paddle bounce: angle based on hit position: angle = (hitPos - 0.5) * maxAngle; velocity preserved, direction upward.
- Cap the minimum vertical component so the ball doesn't travel horizontally forever.

Key handling: keydown/keyup to track left/right; space for launch/restart; 'p' for demo toggle.

Demo mode: variable demo=true, initial state true. When in demo, the paddle is controlled by the AI; arrow keys ignored (or do they still work? spec: AI controls the player; so in demo, arrows are ignored).

Ball-paddle collision: if ball is moving down and intersects paddle rectangle: rel = (ball.x - paddle.x - pw/2)/(pw/2), angle = rel * 60 degrees, vy = -speed*cos, vx = speed*sin.

Wall collision: reflect.

Speed cap: min(18, base + hits*0.35)? With a fast loop, no problem.

Restart: if lives>0 and ball lost: lives--, ball in stuck state on paddle; in demo, auto-launch after 500ms.

Game over: overlay text "GAME OVER — SPACE TO RESTART"; in demo, auto-restart after 1.5 sec.

Level clear: score bonus, regenerate blocks (row count min(3 + level, 6)), ball in stuck state, auto-launch in demo.

HUD: score, lives (draw paddle icons or text), maybe demo indicator, "P to toggle demo".

Draw blocks in row colors, with a slight gradient.

Let me write the code.

const W=800,H=600; canvas full window with CSS scaling? Just center a fixed canvas.

Block grid: cols=8, spacing 6, margin: total width 800; bw=(800-9*6)/8 ≈ 93. Top offset 60. bh=22, vertical spacing 6.

Colors: array per row: red, orange, yellow, green, cyan, blue.

AI: if ball.vy>0: target = ball.x (maybe add prediction: t=(paddleY-ball.y)/vy; x=ball.x+vx*t; reflect into [r, W-r]). Then paddle.x += clamp(target - paddle.x - pw/2, -maxSpeed, maxSpeed), with maxSpeed ~12. Error: occasionally (per ball state, e.g., on each hit a random probability of 8%), offset the error by ±18px. Actually, make the error deterministic per "shot": at launch or on paddle hit, aiErr = (rand<0.1)? rand±(20-35): small jitter ±3.

Ball stuck on paddle: ball.x = paddle.x, y = paddle.y - r - 1.

Frame rate: rAF; maybe use dt scaling, but simple per-frame is enough.

Demo toggle: just flip the flag; when off, if the ball is stuck, wait for space.

Make sure to "show everything important within the first 30 seconds": start in demo, ball is stuck on paddle, auto-launch after ~600ms, fast pace, clear the level and loop.

Also, arrow keys are also usable by the player (manual mode). In demo, display "DEMO" in the HUD.

Let me write the HTML.

Edge cases: ball-block collision — iterate blocks, find first hit, resolve with side detection:
Overlap: nx = clamp(ball.x, bx, bx+bw), ny = clamp(ball.y, by, by+bh); dx, dy; if dx*dx+dy*dy < r*r: if |dx|>|dy|, vx=-vx, else vy=-vy (with tie-break handling). Mark the block destroyed, score, speed up.

Guarantee that after a paddle bounce, |vy| >= 0.35*speed.

Speed up: per paddle hit, speed += 0.15; per block +0.25; with a cap.

Let me write the final code carefully.

let speed variable; function setBallSpeed(){ const s=Math.min(maxSpeed, baseSpeed + hits*inc); ... } more simply: on hit, speed += inc; vx,vy scaled proportionally.

Implementation: keep a scalar `speed`; on paddle bounce, set vx/vy from angle; on wall, flip sign; on block, flip component; on speed up: vx*=factor, vy*=factor (factor=newSpeed/speed).

Game over overlay, space keydown: if state==='over' → resetGame().

State: 'serve' (ball stuck), 'play', 'over'.

Demo auto-launch: on 'serve', if demo, launch after 40 frames.

Let me write it.
