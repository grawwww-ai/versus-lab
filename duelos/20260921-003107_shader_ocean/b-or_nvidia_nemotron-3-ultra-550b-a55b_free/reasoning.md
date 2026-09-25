The user wants a full-window WebGL2 animation of a stormy ocean at sunset using a single raymarching fragment shader. Let me break down the requirements:

1. **Large rolling waves** - multiple octaves of noise
2. **Foam on crests** - based on wave height/slope
3. **Dramatic sky** - dark clouds, low orange sun
4. **Sun reflection and fresnel** on water
5. **Subtle fog near horizon**
6. **Camera gently bobs** like on a boat
7. **RequestAnimationFrame timestamp** for time
8. **Canvas fills window, handles resizing**
9. **Starts automatically, no interaction**
10. **Shows everything important within first 30 seconds**
11. **Single self-contained HTML file**

This is a complex raymarching scene. I'll need to write:
- A vertex shader for full-screen quad
- A fragment shader with raymarching for ocean + sky
- WebGL2 boilerplate in JavaScript
- Proper resize handling

Let me design the shader:

**Scene structure:**
- Sky: gradient + clouds + sun
- Ocean: heightfield with Gerstner waves or noise-based displacement
- Raymarching: march rays through scene, intersection with ocean surface

For the ocean, I'll use a noise-based approach with multiple octaves for rolling waves. The classic approach is to use a height function h(x,z,t) and raymarch against it.

**Raymarching approach:**
- Camera position with bobbing motion
- For each pixel, cast ray from camera
- March until hit ocean surface or sky
- Ocean surface defined by height function
- Use sphere tracing or linear stepping with binary search for intersection

**Height function for ocean:**
Multiple octaves of noise (simplex or perlin-like) with different frequencies/amplitudes
Add Gerstner-style trochoidal waves for realistic rolling

**Sky:**
- Gradient based on y direction
- Sun disk low on horizon
- Cloud layers with noise
- Fog near horizon

**Lighting:**
- Sun direction
- Fresnel on water
- Specular reflection of sun
- Foam on steep crests

**Camera bobbing:**
- Slow sine/cosine motion in x,y,z
- Slight rotation

Let me write this carefully. I'll use a hash-based noise function for GPU efficiency.

Important: WebGL2 requires `#version 300 es` and proper precision declarations.

I'll structure the HTML with:
- Canvas element
- Inline CSS for full-window
- JavaScript for WebGL2 setup, resize handling, render loop
- Shaders as template strings

Let me code this step by step...