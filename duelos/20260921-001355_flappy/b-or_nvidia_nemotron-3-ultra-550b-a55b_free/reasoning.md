The user wants a complete Flappy Bird clone in a single HTML file with Canvas API. Let me break down the requirements:

1. Bird controlled by player with Space key
2. Physics: constant gravity, upward impulse on jump
3. Vertical pipes with random gaps
4. Precise collision detection
5. Score increases when passing pipes
6. Game over on collision with pipes or ground
7. Display score prominently
8. Auto-start on load
9. No external assets - all drawn via Canvas
10. Autoplay demo mode toggled with P key (AI plays competently)
11. Single HTML file with inline CSS/JS

Let me design this carefully:

- Canvas size: 400x600 (portrait, like mobile)
- Bird: small circle/ellipse with simple animation
- Pipes: green rectangles with caps
- Ground: scrolling ground
- Background: sky gradient
- AI: simple heuristic - jump when bird is below gap center minus some offset

I'll make it visually polished with:
- Sky gradient background
- Clouds (parallax)
- Ground with grass detail
- Pipes with 3D effect (darker edges)
- Bird with wing flap animation
- Score with outline for visibility
- Game over screen with restart instruction
- Demo mode indicator

Let me write the complete code.