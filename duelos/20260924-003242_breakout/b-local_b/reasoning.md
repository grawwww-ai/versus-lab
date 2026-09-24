Build a single HTML file, a breakout game, an autoplay AI toggle that switches with the P key, auto-start, ball speed increase, score/lives, arrow keys, space to launch, a competent AI in autoplay mode (predicts the ball's y-position where it reaches the paddle, with smoothing). The game should loop — after clearing or game over, restart after a short delay.

AI: When the ball moves downward, compute the intersection with the paddle's y-coordinate, taking into account wall reflections. Add a bit of error and lerp the paddle toward the target.

Let's write the code.

Canvas 800x600. Block grid is 10 columns x 5 rows. Ball radius 8, paddle width 100, height 12.

Score: +10 per block. 3 lives. When the ball falls, life--, reset the ball on the paddle, wait for space (auto-launch in autoplay). Game over or all cleared → show a message, restart after about 2 seconds.

Speed: base speed 5, +0.1 per hit (paddle/block), max around 10.

Ball-paddle collision: reflect with an angle based on where it hits the paddle — a nice touch.

Keys: track left/right. P toggles autoplay.

Auto-start: at start, the ball sits on top of the paddle, and in autoplay it auto-launches after a short delay; otherwise, wait for space. Actually the "space to launch the ball in the initial state and to restart" part. For the auto-start requirement, let's make the initial ball auto-launch after 1 second so the viewer can see it moving.

Alright, let's write it.
