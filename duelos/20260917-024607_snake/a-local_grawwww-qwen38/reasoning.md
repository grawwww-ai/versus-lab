Create a single HTML file containing a canvas snake game with an AI demo mode. Use a fixed timestep or requestAnimationFrame with an accumulator. AI: BFS or greedy method with safety check. Implement a decent AI: BFS to the food, with tail-follow fallback if needed.

Keep the code reasonably compact and robust.

Canvas is 400x400, grid 20px → 20x20 cells. Speed is about 8 cells/sec? Smooth 60fps animation — for smoothness, could also interpolate between grid positions. For smoothness, use an accumulator with a fixed step, and interpolate rendering positions.

Implementation:

- state: snake array of {x,y}, dir, nextDir, food, score, dead, autoplay
- step(): apply nextDir, check collision, move head, if it ate food then grow, spawn food.
- AI: on each step, if autoplay: choose direction with BFS to food; if no safe path, follow the tail (BFS to tail); if neither works, any direction that doesn't immediately collide; prefer to maintain length.

Simple and solid: for each candidate direction (excluding reverse), simulate a move: check collision with the body (excluding the tail cell if not eating). Then BFS from the new head position to the food, on a grid that excludes the body (excluding the tail if the tail moves). If a path exists and (path length is finite), it's a safe candidate. Score the candidates: prefer shortest path to food, prefer longer body, prefer path to tail. If no candidate leads to a BFS path to the food, prefer a candidate that has a BFS path to the tail (tail chase), otherwise any non-colliding candidate, otherwise die.

Keep the snake body array, head is the front.

Rendering: interpolation: hold prev positions and t = acc/stepTime, lerp each segment from the previous position to the current position. Easier: just draw with a lerp between the previous snake and the current snake.

Save prevSnake before the step, and after the step compute t = acc/STEP.

Food is a circle, snake is a rounded rectangle.

Game over text + "Press Space to restart". Toggle label with P key.

Score is at the top center.

Write the file.
