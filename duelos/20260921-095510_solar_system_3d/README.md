# ⚔️ Duelo: Sistema solar en 3D

- **Reto ID:** `solar_system_3d`
- **Categoría:** `3d`
- **Fecha:** `20260921-095510`
- **Ganador:** 🏆 **or:deepseek/deepseek-v4.1-flash**

---

### 📝 Prompt suministrado a ambos modelos:
> Using three.js, build a beautiful 3D model of the Solar System with a cinematic tour. Requirements: the Sun glowing at the centre (emissive, with a halo) lighting the planets; the 8 planets in the correct order (Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, Neptune), with relative sizes that make sense (Jupiter the largest, Mercury the smallest), procedural textures on canvas (Jupiter's bands, Earth's oceans and continents, Mars red), Saturn with its rings, the Moon orbiting the Earth; faint orbit lines; planets orbiting at different speeds; a starfield background; a camera that travels from planet to planet showing each one close up with its name on screen. Use the requestAnimationFrame timestamp for animation time. Full-window canvas that handles resizing. Starts automatically, no interaction needed. The animation should show everything important within the first 30 seconds (that is the window we record); it may loop or continue after that.

three.js (r186) is available as an ES module: use `import * as THREE from 'three'` and addons from 'three/addons/...' (e.g. 'three/addons/controls/OrbitControls.js') inside <script type="module">. An import map is provided for you: do not add your own import map or any CDN URL.

Requirements: deliver everything in ONE self-contained HTML file (inline CSS and JavaScript; no external resources, CDNs, fonts or images). Reply with the complete file in a single ```html code block.

---

### 📊 Resultados y Métricas:

| Modelo | Nota Juez | Tiempo | Tokens | Coste | Archivos |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **A · or:deepseek/deepseek-v4.1-flash** | 100 / 100 | 345.099 s | 43305 | 0.0381 $ | [Ver código](a-or_deepseek_deepseek-v4.1-flash/) |
| **B · or:z-ai/glm-5.3-flash** | 25 / 100 | 175.408 s | 4750 | 0.0017 $ | [Ver código](b-or_z-ai_glm-5.3-flash/) |

---

### 🎮 Cómo probarlo en local:
Puedes abrir directamente en tu navegador cualquiera de los archivos `index.html` dentro de cada carpeta de contendiente.

*Generado automáticamente por el pipeline de [VERSUS](https://github.com).*
