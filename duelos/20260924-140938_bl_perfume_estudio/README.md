# ⚔️ Duelo: Anuncio de perfume

- **Reto ID:** `bl_perfume_estudio`
- **Categoría:** `blender`
- **Fecha:** `20260924-140938`
- **Ganador:** 🏆 **or:openai/gpt-6-luna-pro**

---

### 📸 Capturas del Resultado:

| **A · or:deepseek/deepseek-v4.1-flash** | **B · or:openai/gpt-6-luna-pro** |
| :---: | :---: |
| *(Sin captura visual)* | <a href="b-or_openai_gpt-6-luna-pro/shot_end.png"><img src="b-or_openai_gpt-6-luna-pro/shot_end.png" alt="or:openai/gpt-6-luna-pro" width="420" /></a> |
| ⭐ **Nota:** 17/100 · ⏱️ 285.735s | ⭐ **Nota:** 100/100 · ⏱️ 242.037s |

---

### 📝 Prompt suministrado a ambos modelos:
> Create a luxury perfume commercial shot in a photo studio. A faceted crystal-glass perfume bottle filled with amber liquid, with a polished gold cap, stands on a slowly rotating round black marble pedestal. Studio lighting like a real product shoot: a large soft key light, a rim light that outlines the glass edges and a subtle coloured backdrop gradient. The glass must refract and the liquid must glow where the light passes through it; the gold must reflect the studio. Over the 5 seconds the camera slowly orbits and gently pushes in towards the bottle, ending on a close-up of the cap.

Requirements: write ONE Python script for Blender 4.5 LTS (bpy) that builds the whole scene from scratch when run in background mode (blender -b --factory-startup --python script.py): delete the default objects and create every object, material, light, the world and a camera (set it as scene.camera), animated over frames 1 to 120 at 24 fps (5 seconds). Do NOT render, do not set the render engine, resolution, samples or output path, and do not save any file: we render your scene ourselves with Cycles on a GPU (1280x720, 128 samples, denoised, at most 3 seconds per frame), with exactly the same settings for both contestants. Use only bpy, mathutils, math and the Python standard library: no add-ons, no external files, images, textures or downloads (build materials procedurally with shader nodes). Reply with the complete script in a single ```python code block.

---

### 📊 Resultados y Métricas:

| Modelo | Nota Juez | Tiempo | Tokens | Coste | Archivos |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **A · or:deepseek/deepseek-v4.1-flash** | 17 / 100 | 285.735 s | 48995 | 0.0324 $ | [Ver código](a-or_deepseek_deepseek-v4.1-flash/) |
| **B · or:openai/gpt-6-luna-pro** | 100 / 100 | 242.037 s | 29494 | 0.0174 $ | [Ver código](b-or_openai_gpt-6-luna-pro/) |

---

### 🎮 Cómo probarlo en local:
Puedes abrir directamente en tu navegador cualquiera de los archivos `index.html` dentro de cada carpeta de contendiente.

*Generado automáticamente por el pipeline de [VERSUS](https://github.com/grawwww-ai/versus-lab).*
