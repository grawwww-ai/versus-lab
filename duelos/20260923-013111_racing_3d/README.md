# ⚔️ Duelo: Carreras 3D

- **Reto ID:** `racing_3d`
- **Categoría:** `3d`
- **Fecha:** `20260923-013111`
- **Ganador:** 🏆 **or:deepseek/deepseek-v4.1-flash**

---

### 📝 Prompt suministrado a ambos modelos:
> Using three.js, create a 3D racing scene that drives itself, in the style of an arcade racing game. Requirements: a closed race track with curves, kerbs and a start/finish line, built procedurally, on a landscape with grass, trees or buildings and a sky; a detailed player car modelled from primitives (body, wheels that spin, lights) and at least three rival cars in different colours; all cars are driven by an AI that follows the racing line around the track, overtaking each other; a chase camera behind the player car with a sense of speed; a HUD with speed, lap counter (Lap 1/3) and race position (e.g. 2nd). Use the requestAnimationFrame timestamp for animation time. Full-window canvas that handles resizing. Starts automatically, no interaction needed.

three.js (r186) is available as an ES module: use `import * as THREE from 'three'` and addons from 'three/addons/...' (e.g. 'three/addons/controls/OrbitControls.js') inside <script type="module">. An import map is provided for you: do not add your own import map or any CDN URL.

The animation should show everything important within the first 30 seconds (that is the window we record); it may loop or continue after that.

Requirements: deliver everything in ONE self-contained HTML file (inline CSS and JavaScript; no external resources, CDNs, fonts or images). Reply with the complete file in a single ```html code block.

---

### 📊 Resultados y Métricas:

| Modelo | Nota Juez | Tiempo | Tokens | Coste | Archivos |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **A · or:deepseek/deepseek-v4.1-flash** | 100 / 100 | 125.6 s | 31333 | 0.0188 $ | [Ver código](a-or_deepseek_deepseek-v4.1-flash/) |
| **B · or:~openai/gpt-luna-latest** | 100 / 100 | 81.072 s | 10989 | 0.0055 $ | [Ver código](b-or__openai_gpt-luna-latest/) |

---

### 🎮 Cómo probarlo en local:
Puedes abrir directamente en tu navegador cualquiera de los archivos `index.html` dentro de cada carpeta de contendiente.

*Generado automáticamente por el pipeline de [VERSUS](https://github.com).*
