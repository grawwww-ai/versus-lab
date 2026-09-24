The user wants a complete, self-contained HTML file with a Three.js racing game. Let me break down the requirements:

1. **Closed race track** - procedurally generated with curves, kerbs, start/finish line
2. **Landscape** - grass, trees/buildings, sky
3. **Player car** - detailed, from primitives (body, spinning wheels, lights)
4. **3+ rival cars** - different colors, AI-driven
5. **AI driving** - follows racing line, overtaking
6. **Chase camera** - behind player car with speed sense
7. **HUD** - speed, lap counter (Lap 1/3), race position
8. **Animation** - requestAnimationFrame timestamp
9. **Full-window canvas** - handles resizing
10. **Auto-start** - no interaction needed

Let me design this step by step:

### Track Generation
- Create a spline-based track using Catmull-Rom curves
- Generate track geometry with lanes, kerbs, grass
- Add start/finish line

### Cars
- Build cars from primitives (boxes, cylinders, spheres)
- Player car: distinct color (red)
- Rival cars: different colors (blue, green, yellow, etc.)
- Wheels that spin based on speed
- Lights (headlights, taillights)

### AI System
- Racing line following using spline parameter
- Speed variation for overtaking
- Simple collision avoidance

### Camera
- Chase camera with smoothing
- FOV change for speed sense
- Camera shake at high speeds

### HUD
- Speedometer
- Lap counter (1/3)
- Position (1st, 2nd, 3rd, 4th)

### Environment
- Skybox or gradient sky
- Ground plane with grass texture (procedural)
- Trees/buildings as simple primitives

Let me write the complete code now.