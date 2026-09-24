# ⚔️ Duelo: Interior fotorrealista

- **Reto ID:** `photoreal_room`
- **Categoría:** `shader`
- **Fecha:** `20260924-134121`
- **Ganador:** 🏆 **or:deepseek/deepseek-v4.1-flash**

---

### 📝 Prompt suministrado a ambos modelos:
> Write a WebGL2 path tracer (or an accumulating raymarcher) in one HTML file that renders a photorealistic interior: a room with a window letting in sunlight, a wooden floor, a sofa, a table with a glass and a metal lamp, and a mirror on the wall. It must show real global illumination (colour bleeding from walls), soft shadows, glossy and mirror reflections, refraction through the glass, and a slight depth of field. The camera must be moving the WHOLE time, never stopping: a slow, smooth dolly or orbit that walks through the room and reveals it from different angles, and the sunlight must move across the floor as the sun changes position. Keep it real-time: progressive accumulation is welcome, but the view must never freeze into a still image while it cleans up. Include a small label with the number of accumulated samples. It renders on its own from the first frame.

The animation should show everything important within the first 30 seconds (that is the window we record); it may loop or continue after that.

Requirements: deliver everything in ONE self-contained HTML file (inline CSS and JavaScript; no external resources, CDNs, fonts or images). Reply with the complete file in a single ```html code block.

---

### 📊 Resultados y Métricas:

| Modelo | Nota Juez | Tiempo | Tokens | Coste | Archivos |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **A · or:deepseek/deepseek-v4.1-flash** | 100 / 100 | 368.584 s | 62611 | 0.0752 $ | [Ver código](a-or_deepseek_deepseek-v4.1-flash/) |
| **B · or:openai/gpt-6-luna-pro** | 100 / 100 | 203.608 s | 25826 | 0.0152 $ | [Ver código](b-or_openai_gpt-6-luna-pro/) |

---

### 🎮 Cómo probarlo en local:
Puedes abrir directamente en tu navegador cualquiera de los archivos `index.html` dentro de cada carpeta de contendiente.

*Generado automáticamente por el pipeline de [VERSUS](https://github.com).*
