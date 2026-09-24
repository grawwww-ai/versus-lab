# ⚔️ Duelo: Choque de galaxias

- **Reto ID:** `galaxy_collision`
- **Categoría:** `3d`
- **Fecha:** `20260919-040941`
- **Ganador:** 🏆 **or:deepseek/deepseek-v4-flash-0731:free**

---

### 📝 Prompt suministrado a ambos modelos:
> Using three.js, simulate two spiral galaxies colliding, as a cinematic scientific visualization. Requirements: two disk galaxies with visible spiral arms and a bright core, each with at least 20,000 stars rendered as glowing points (additive blending), colours going from warm yellow cores to blue-white arms; the galaxies approach each other and interact through gravity, so that during the encounter tidal tails and bridges of stars are pulled out; a slowly orbiting camera that frames the whole event; a dark starfield background; and a small on-screen label with the simulated time in millions of years. Use the requestAnimationFrame timestamp for animation time and run the physics on the GPU or with a cheap approximation so it stays smooth. Full-window canvas that handles resizing. Starts automatically, no interaction needed.

three.js (r186) is available as an ES module: use `import * as THREE from 'three'` and addons from 'three/addons/...' (e.g. 'three/addons/controls/OrbitControls.js') inside <script type="module">. An import map is provided for you: do not add your own import map or any CDN URL.

Requirements: deliver everything in ONE self-contained HTML file (inline CSS and JavaScript; no external resources, CDNs, fonts or images). Reply with the complete file in a single ```html code block.

---

### 📊 Resultados y Métricas:

| Modelo | Nota Juez | Tiempo | Tokens | Coste | Archivos |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **A · or:deepseek/deepseek-v4-flash-0731:free** | 100 / 100 | 790.723 s | 29619 | 0.0000 $ | [Ver código](a-or_deepseek_deepseek-v4-flash-0731_free/) |
| **B · or:nvidia/nemotron-3-ultra-550b-a55b:free** | 65 / 100 | 171.649 s | 8323 | 0.0000 $ | [Ver código](b-or_nvidia_nemotron-3-ultra-550b-a55b_free/) |

---

### 🎮 Cómo probarlo en local:
Puedes abrir directamente en tu navegador cualquiera de los archivos `index.html` dentro de cada carpeta de contendiente.

*Generado automáticamente por el pipeline de [VERSUS](https://github.com).*
