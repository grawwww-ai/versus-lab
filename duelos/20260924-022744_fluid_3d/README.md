# ⚔️ Duelo: Agua en 3D de verdad

- **Reto ID:** `fluid_3d`
- **Categoría:** `sim`
- **Fecha:** `20260924-022744`
- **Ganador:** 🏆 **or:deepseek/deepseek-v4.1-flash**

---

### 📝 Prompt suministrado a ambos modelos:
> Build a real-time 3D fluid simulation in one HTML file (WebGL2 compute-style with textures, SPH or FLIP, your choice): a tank where a wave of water is released and splashes against obstacles, with at least 30,000 particles or a grid of equivalent resolution. The water must have a rendered surface (not just dots): refraction, specular highlights, foam on impacts and droplets flying off. A slowly orbiting camera shows the tank; the simulation restarts with a new splash every few seconds. Show the particle count and the frame rate. Runs alone.

The animation should show everything important within the first 30 seconds (that is the window we record); it may loop or continue after that.

Requirements: deliver everything in ONE self-contained HTML file (inline CSS and JavaScript; no external resources, CDNs, fonts or images). Reply with the complete file in a single ```html code block.

---

### 📊 Resultados y Métricas:

| Modelo | Nota Juez | Tiempo | Tokens | Coste | Archivos |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **A · or:deepseek/deepseek-v4.1-flash** | 100 / 100 | 1102.454 s | 64292 | 0.0270 $ | [Ver código](a-or_deepseek_deepseek-v4.1-flash/) |
| **B · or:openai/gpt-6-luna-pro** | 65 / 100 | 148.302 s | 26907 | 0.0160 $ | [Ver código](b-or_openai_gpt-6-luna-pro/) |

---

### 🎮 Cómo probarlo en local:
Puedes abrir directamente en tu navegador cualquiera de los archivos `index.html` dentro de cada carpeta de contendiente.

*Generado automáticamente por el pipeline de [VERSUS](https://github.com).*
