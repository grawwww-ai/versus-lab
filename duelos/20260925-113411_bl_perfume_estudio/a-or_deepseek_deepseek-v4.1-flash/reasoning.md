Let me design a luxury perfume commercial scene in Blender 4.5 LTS.

Key requirements:
- Delete default objects
- Faceted crystal-glass perfume bottle with amber liquid, gold cap
- Black marble rotating pedestal
- Studio lighting setup
- Camera orbit + push-in over 720 frames
- Procedural materials only
- No render settings
- One script, single code block

Let me plan:

**Camera motion**: orbit around the bottle while pushing in. Start wide, end close on cap. Use a curve or math to compute camera position each frame. Orbit e.g. 180 degrees, radius from 3m to 1m.

**Bottle geometry**:
- Body: faceted crystal glass - use a cylinder with low vertex count (e.g., 8 sides) and smooth shading off for facets, or use a cube with beveled edges. Let's make a hexagonal/octagonal prism body.
- Neck: smaller cylinder
- Cap: gold cylinder on top
- Liquid inside: slightly smaller than the bottle interior

Actually, for glass with refraction, we need actual geometry. Let's build:
- Bottle outer: octagonal prism, maybe 12 sides for facets.
- Inner cavity: small offset
- Liquid: amber cylinder filling bottom portion

Simpler approach: make the bottle shell as a solid with solidify or use two nested meshes. Actually for Cycles glass, just making a solid glass shape works.

Let me use:
- Outer bottle: create with bmesh or primitives. Use a cylinder with 8 sides, height 0.6, radius 0.3, with a bevel.
- Liquid: cylinder radius 0.26, height 0.4, inside the bottle.

To get proper refraction, make glass solid (Ior, transmission). The liquid is inside — but if the glass is solid, we can't have liquid inside. Better: make glass shell using Solidify modifier or two concentric cylinders with boolean.

Simplest: make the bottle as a "tube" shape — outer cylinder wall with thickness via solidify modifier. Then add liquid cylinder inside.

Let me build with bmesh or with primitives + modifier:

```python
bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.3, depth=0.6, location=(0,0,0.3))
```
This gives an 8-sided prism. Add solidify modifier with thickness 0.02. That creates the glass shell.

Liquid: cylinder radius 0.27, depth 0.4, location (0,0,0.2).

Cap: cylinder vertices=8, radius 0.15, depth 0.07, location (0,0,0.65). Gold material.

Neck: thin cylinder between body and cap. Actually let's just have the cap sit directly on a short neck.

Hmm, let me define more carefully:
- Pedestal: cylinder radius 0.6, depth 0.15, at z=0. Actually top of pedestal at z=0.
- Bottle bottom at z=0.02 (small gap for realism? no, on pedestal).

Let me set:
- Pedestal: center at z = -0.075, depth 0.15, so top at z=0.
- Bottle body: bottom at z=0, height 0.5, center at 0.25, radius 0.28.
- Neck: small cylinder radius 0.1, height 0.05, on top of body, center at 0.525.
- Cap: radius 0.14, height 0.08, bottom at 0.55, center at 0.59.

Liquid: radius 0.25, height 0.35, bottom at 0.03, center at 0.205.

Facets: use 8-sided cylinders. For the body, add bevel modifier for soft edges? Actually faceted crystal means flat faces. Keep 8 sides with flat shading.

Actually, let's make the body with bevel on the vertical edges to look like cut crystal. Hmm, 8-sided prism already gives 8 facets. Good enough.

Let me also add more facets by making the body two stacked segments (like a tapered shape). Simple is fine.

**Rotation**: pedestal rotates slowly. Actually the bottle sits on the pedestal, so bottle+cap+liquid should rotate with it. Better to parent bottle objects to pedestal, or just rotate all with the same driver. Actually camera orbits, so we don't strictly need bottle rotation. But "slowly rotating round black marble pedestal" — let's rotate the pedestal and the bottle together.

Set rotation on all bottle parts + cap + liquid + pedestal.

**Camera motion** (frames 1-720):
- Orbit: start at angle -60°, end at angle +120° (180° total)
- Radius: start 3.5, end 1.2
- Height: start 1.2, end 0.7 (aiming at cap which is at ~0.6)
- Target: start looking at center (0.3 height), end at cap (0.6)

Use smooth easing (ease in/out or linear). Let's use smootherstep or just linear.

Actually to avoid finishing early, keep it linear or slightly eased. Linear is safest.

Camera at position computed each frame, track to target using a constraint or manual rotation. Manual is better for the final render — use a Track To constraint to an empty. But then baking... Actually constraints evaluate at render time fine.

Let me just compute look-at manually with mathutils.

```python
from mathutils import Vector
def look_at(cam, target):
    direction = target - cam.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam.rotation_euler = rot_quat.to_euler()
```

Set camera location and rotation each frame via keyframes.

**Lighting**:
- Key: large area light, soft
- Rim: area light behind, colored slightly
- Fill: maybe
- Backdrop: use a large curved plane with gradient emission/shader

Backdrop gradient: use a large plane with gradient texture mapped to world or object coordinates. Subtle colored — let's do dark teal to dark purple.

**World**: dark, subtle.

**Materials**:

1. Glass (crystal):
   - Principled BSDF, Transmission 1.0, IOR 1.5, Roughness 0.0
   - Or use Glass BSDF. In Blender 4.x, Principled with transmission=1 works.
   
2. Liquid (amber):
   - Principled with transmission 0.9, base color amber (0.6, 0.25, 0.02), IOR 1.4
   - Volume absorption would be nicer but let's keep it surface-based.
   - Actually use Principled with transmission and a colored base — light passing through will be tinted.

3. Gold:
   - Principled, metallic 1.0, roughness 0.1, base color (1.0, 0.766, 0.336)

4. Marble (black):
   - Procedural noise texture for veining
   - Base color dark, mixed with lighter veins

5. Backdrop:
   - Emission or Principled with gradient

Let me now write it.

For the pedestal marble: use Noise Texture → ColorRamp for veins, mixed with dark base.

Let me write the script.

```python
import bpy
import math
from mathutils import Vector, Euler

# ---- Clean scene ----
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
# also purge orphan data
for block in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.images):
    for b in list(block):
        if b.users == 0:
            block.remove(b)
```

Careful: deleting objects from default scene. In background with --factory-startup, default has Cube, Light, Camera.

Now build.

Let me write a helper for creating cylinders with location:

```python
def make_cylinder(verts, radius, depth, location, name):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=location)
    obj = bpy.context.active_object
    obj.name = name
    return obj
```

Glass shell: solid cylinder + solidify.

```python
bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.28, depth=0.5, location=(0,0,0.25))
glass = bpy.context.active_object
glass.name = "Bottle_Glass"
sol = glass.modifiers.new("Solidify", 'SOLIDIFY')
sol.thickness = 0.02
sol.offset = -1  # inward
```

Wait, offset -1 means the surface goes inward, keeping outer radius. Good.

Add bevel to edges for realism? Maybe.

Actually solidify creates a closed shell with open top and bottom (cylinder caps stay). Hmm, a cylinder with solidify will produce inner and outer walls including caps. That's fine — a hollow glass vessel.

But the top has a hole where the neck goes? Actually the cylinder is capped on top, so we get a closed shell with top and bottom walls. Real bottle has an opening at neck, but for our purposes this is fine visually.

Actually let's just make the glass a solid piece (no solidify). Real glass blocks refract nicely. But then the liquid inside won't be visible. Hmm.

Alternative: make the glass a hollow shell. Then inside it, place amber liquid. Light passing through glass and liquid will refract properly.

Let me use solidify with offset 0 (centered) so thickness splits between inner and outer.

Actually let's think: with solidify inward, outer surface at radius 0.28, inner at 0.26. Liquid at radius 0.25 fits inside.

But solidify also creates inner top/bottom caps. So we have a closed glass box. Liquid inside. Fine.

Actually wait — if the glass is fully closed (includes top cap), then liquid inside is enclosed. That's OK for rendering — light refracts through.

Hmm but visually, a bottle with no opening looks weird. Let's add a neck from the top.

Actually, let's simplify: glass shell from solidify, and a neck cylinder on top that connects. The neck opening isn't visible from outside anyway since the cap covers it.

Let me make the neck: a small cylinder radius 0.08, height 0.08, at z=0.54.

Hmm, but the glass shell is closed at top with a flat cap at z=0.5. Adding a neck on top would be weird but hidden by the cap.

Alternative: Just make the bottle without an opening — the cap sits directly on top. Like many perfume bottles where the cap is a decorative stopper on the shoulder. Fine.

Let's go:
- Body: 8-sided prism, radius 0.28, height 0.5, z from 0 to 0.5
- Shoulder: cone/tapered to neck (optional, skip)
- Neck: cylinder radius 0.09, height 0.06, z 0.5 to 0.56
- Cap: cylinder radius 0.13, height 0.09, z 0.54 to 0.63

The cap overlaps the neck a bit, that's fine.

Liquid: 8-sided prism, radius 0.25, height 0.32, z 0.03 to 0.35. Inside the glass shell.

Wait, the glass shell from solidify with inward offset has inner radius 0.26. Liquid at 0.25 works.

Hmm — the liquid should not intersect the neck or extend up there. Keep it in the body.

OK.

For the camera view: to end on the cap, the camera at frame 720 should be close and aimed at the cap. Cap at z ≈ 0.585.

Let's define camera path:
- t = (f-1)/719 ∈ [0,1]
- angle = -80° + t * 200°  (start at -80, end at 120)
- radius = 3.2 - t * 2.0 (start 3.2, end 1.2)
- height = 1.1 - t * 0.45 (start 1.1, end 0.65)
- target height = 0.28 + t * 0.30 (start looking at body center, end at cap)

Add a slight ease? Linear is fine and fills whole duration.

Actually let's make it slight ease-in-out for luxury feel using smoothstep — but that could look "frozen" at ends. Linear orbit with smoothstep feels elegant. Let's use a mild ease: t_eased = t*t*(3-2*t). Hmm, at t=0 slope is 0 — that's fine for a slow start but might look static. Let's just use linear or very mild easing.

I'll use linear for reliability.

Camera FOV: 50mm lens on default 36mm sensor ≈ 39° FOV. Fine.

Let's add look-at.

```python
cam_data = bpy.data.cameras.new("Camera")
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.scene.collection.objects.link(cam)
cam_data.lens = 50
bpy.context.scene.camera = cam
```

Then animate per frame.

For animation, I'll set keyframes on location and rotation_euler for each frame. Or use frame_handler. Keyframes are more robust. Let's key every frame from 1 to 720? That's a lot but fine. Or key every 5 frames and use interpolation. Actually to be exact, key every frame.

720 keyframes × 6 channels = manageable.

Actually, let's key every frame for accuracy. Blender handles it.

Also the pedestal rotation: rotate 360° over 720 frames? Or just a slow rotation — maybe 180°.

Let's do pedestal rotates continuously by 180° over the duration.

Actually, if camera orbits, adding pedestal rotation compounds. Maybe rotate the pedestal just slightly (like 60°) for a subtle effect. Or rotate it faster than the camera so we see different facets. Let's rotate the platter fully 720°? Hmm.

Actually a slowly rotating pedestal means the bottle rotates with it. Since the bottle is 8-sided with facets, rotation shows different facets. Let's do 90° over the duration — slow.

Hmm, actually let me just do a clean 180° over the sequence.

Wait — but if the camera also orbits, the relative motion is faster. Let's do pedestal rotate 120° over 720 frames (slow).

Actually, I'll rotate the pedestal by -60° to +60°? No, continuous rotation is simpler. Let's do 0 to 150°.

Hmm, actually to make the pedestal "slowly rotating" — 720 frames at 24fps = 30 seconds. One rotation per 30s is slow. Let's do 1 full rotation per duration (360°). Combined with camera orbiting opposite or same direction.

Camera orbits +200°, pedestal rotates +360°. Together the bottle appears to orbit -160° relative to camera. Fine, that's a nice motion.

Actually let's keep it simple: pedestal rotates 360°, camera orbits 180°. 

Hmm, but then at the end the camera pushes in close to the cap — we want the cap visible. It's a cylinder, so fine.

Let me reduce pedestal rotation to 180° for a subtler look. I'll go with 180°.

Actually, on reflection: "slowly rotating" → 360° over 30s = 12°/s. That's slow. Good. Let's do it.

**Materials setup**:

Glass material:
```python
mat_glass = bpy.data.materials.new("CrystalGlass")
mat_glass.use_nodes = True
bsdf = mat_glass.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (1,1,1,1)
bsdf.inputs["Transmission Weight"].default_value = 1.0
bsdf.inputs["Roughness"].default_value = 0.02
bsdf.inputs["IOR"].default_value = 1.55
bsdf.inputs["Metallic"].default_value = 0.0
```

In Blender 4.x, the Principled BSDF input names: "Base Color", "Metallic", "Roughness", "IOR", "Alpha", "Transmission Weight" (4.0+), "Coat Weight", etc.

Let me confirm: Blender 4.0+ uses "Transmission Weight". Yes.

Also might want to add slight dispersion. In 4.x there's "Coat" etc. There's no built-in dispersion in Principled until 4.1 or so? Actually Blender 4.1 added a dispersion setting? Hmm, I don't think Principled has dispersion. Skip.

Amber liquid:
```python
mat_liquid = bpy.data.materials.new("AmberLiquid")
...
bsdf.inputs["Base Color"].default_value = (0.7, 0.28, 0.03, 1)
bsdf.inputs["Transmission Weight"].default_value = 1.0
bsdf.inputs["Roughness"].default_value = 0.0
bsdf.inputs["IOR"].default_value = 1.45
```

With transmission, base color tints the transmitted light. Good, gives amber glow.

Gold:
```python
bsdf.inputs["Base Color"].default_value = (1.0, 0.72, 0.29, 1)
bsdf.inputs["Metallic"].default_value = 1.0
bsdf.inputs["Roughness"].default_value = 0.12
```

Marble:
Nodes: Texture Coordinate (Object) → Mapping (scale) → Noise Texture (detail high) → ColorRamp → mix into base color.

Let me write:
```python
texco = nodes.new("ShaderNodeTexCoord")
map = nodes.new("ShaderNodeMapping")
noise = nodes.new("ShaderNodeTexNoise")
ramp = nodes.new("ShaderNodeValToRGB")
```

Noise scale 4-8, detail 8, roughness 0.6.

Ramp: pos 0.45 → dark (0.01,0.01,0.012), pos 0.55 → light gray (0.25,0.25,0.28).

Actually for black marble with white veining, use color ramp with narrow bright band.

Set ramp color stops: (0.0, black), (0.42, black), (0.48, light gray), (0.52, black). Hmm, to get veins use ramp on noise around mid value.

Let's do:
- stop 0: pos 0.35, color black
- stop 1: pos 0.5, color (0.4,0.4,0.42)
- stop 2: pos 0.65, color black

That gives veiny bands. Good.

Then plug into BSDF Base Color. Roughness ~0.15 (polished), metallic 0.

Backdrop: large curved plane. Let's make a big plane behind and a curved cyclorama.

Simplest: use a plane at z=0 (floor) and a large plane behind. Or use a single big curved mesh.

Let's create a cyclorama with a curve: use a large plane + cylinder segment. Or just use two planes.

Actually easier: create a big UV sphere with only the top half visible from inside? Or just a large plane behind tilted.

Let's do: floor plane 20x20 at z=0, and backdrop plane 20x15 vertical at y=+6 (or wherever). With a gradient shader.

Actually let's use a smooth cove: create a mesh with bmesh. Or use a large plane and rotate.

Simpler: I'll create a plane, then use Simple Deform to bend it into a curve. Or just use two perpendicular planes and accept the seam (mostly hidden).

Let me create a curved backdrop using a cylinder segment via bmesh — actually easiest to just use a big scaled UV sphere and set the shader to be visible from inside (backface culling off, but shading on inside is fine).

Hmm. Let's just make a plane behind with a gradient material, and a floor plane with dark material. The pedestal sits on the floor.

Backdrop gradient: use Generated texture coordinate or Object coordinate mapped to vertical (z) → ColorRamp → Emission or Principled.

Let's do this for the backdrop:
- Texture Coordinate (Window or Generated) → Separate XYZ → Z → ColorRamp → emission color

Wait, for a plane, Generated coords map to 0-1 across. If I use Generated Z, the vertical axis of the plane gives 0-1 bottom-to-top. 

Then ColorRamp with stops: dark teal at 0, dark purple at 1. Subtle.

Emission strength 1.0. But that adds light. Let's make it a Principled with base color and low emission, or use pure emission with strength ~0.5 to keep it subtle. Actually if it's a light source it might get too bright. Let's use Principled with the gradient as base color and roughness 1.0, diffuse. The lights will illuminate it.

Hmm, but with dim lighting the backdrop might be too dark. Let's add mild emission (0.3).

Actually, for "subtle coloured backdrop gradient" — a subtle color gradient behind the bottle. Let's use emission at strength 0.5-1.0 with muted colors. That would make it a visible colored background. Let's do it.

Colors: dark teal (0.02, 0.06, 0.08) to dark plum (0.08, 0.02, 0.06). Very subtle in a dark scene.

Hmm, might be too dark to see. Let's brighten a bit: (0.05, 0.12, 0.15) and (0.15, 0.05, 0.12). With emission strength 1.0.

Actually the gradient should be "subtle" — a soft glow behind the bottle. Let's use a radial gradient centered behind the bottle. But we can do a linear one. Fine.

**Lights**:

Key light: Area, large (1.5m), positioned to the front-left above, aiming at the bottle. Energy ~300W. Size matters for softness.

At distance ~3m with size 1.5m — soft.

Actually let's set energy high since it will fall off. Use size 1.5, energy 400.

Rim light: Area, smaller (0.5), behind the bottle, aimed at the bottle. Colored slightly warm or white. Energy 200.

Fill light: large area, dimmer, opposite side, energy 50.

Let me position lights relative to the bottle at origin (0,0,0.3).

Key at (-2, -2, 2.5), aimed at (0,0,0.3).
Rim at (2.5, 1.5, 1.5), aimed at (0,0,0.4).
Fill at (2.5, -2, 1.2), energy lower.

Use track-to via rotation computation, or use constraints. I'll compute rotation via to_track_quat.

Actually I'll create a helper `point_at(obj, target)`.

Let's write it.

**Camera animation per frame**:

```python
for f in range(1, 721):
    t = (f-1)/719.0
    angle = math.radians(-80 + t*200)
    radius = 3.2 - 2.0*t
    height = 1.15 - 0.5*t
    cx = radius*math.sin(angle)  # hmm let's define
    cy = -radius*math.cos(angle)
    cam.location = (cx, cy, height)
    target = Vector((0, 0, 0.28 + 0.32*t))
    direction = target - cam.location
    rot = direction.to_track_quat('-Z','Y').to_euler()
    cam.rotation_euler = rot
    cam.keyframe_insert("location", frame=f)
    cam.keyframe_insert("rotation_euler", frame=f)
```

Wait, radius goes from 3.2 to 1.2. At radius 1.2 and height 0.65, looking at cap at z=0.6... that's close. Camera at 1.2m from the object. With 50mm lens, the cap (0.26m diameter) would fill a good portion. Good close-up.

Actually at radius 1.2 the camera is at distance ~1.2m horizontally and 0.05m above cap. The cap has radius 0.13, so diameter 0.26. FOV at 1.2m with 50mm lens on 36mm sensor: horizontal FOV width = 2*1.2*18/50 = 0.864m. Cap fills 0.26/0.864 = 30% of width. Hmm, that's not a super close-up.

Let's push in more: end radius 0.7, height 0.65 (target 0.6). Then width = 2*0.7*18/50 = 0.504m. Cap fills 52%. Better.

Actually let's use radius ending at 0.65. Width = 0.47m, cap fills 55%. Good close-up.

But at 0.65m horizontal, with a camera height of 0.65 and target at 0.6 the angle is nearly horizontal — fine.

Hmm but the floor and pedestal might clip. Camera at z=0.65, pedestal top at z=0. Fine.

Let's go: radius 3.4 → 0.65. Height 1.2 → 0.68. Target z 0.28 → 0.60.

Wait, but at the end the camera is 0.65m from the cap horizontally, and the cap is at radius 0.13. Camera at angle... fine.

Also we should make sure the camera doesn't go below the floor or into the pedestal. At end height 0.68, that's above the pedestal top (0). Fine.

Now the whole motion: over 720 frames, camera orbits 200° while pulling in from 3.4 to 0.65. That's a significant push-in. The lighting changes as the camera moves — good.

Let's also add a slight vertical arc: height goes 1.2 → 0.68, monotonic. Fine.

**Rendering the gold reflection**: gold should reflect the studio. With area lights and a bright backdrop, it should. Add roughness 0.15 for soft reflection.

**Glass refraction**: need enough light. Cycles should handle it.

Let's also make sure the glass object is smooth-shaded on the round parts? No, faceted is flat. Keep flat shading.

But the cap should be smooth-shaded maybe. It's a cylinder with 8 sides — faceted will look OK but for gold, let's use 32 sides and smooth shading. Actually, for a luxury perfume bottle, the cap could also be faceted. Let's use 24 sides with smooth shading + auto smooth? In 4.5 auto smooth is a modifier. Let's just use flat shading with 32 verts — nearly smooth but picks up facet highlights. Or use shade_smooth.

Actually let's just use shade_smooth for the cap and 32 verts. The top and bottom edges will look rounded which is a bit odd. Use shade_auto_smooth? In Blender 4.1+ there's `bpy.ops.object.shade_auto_smooth()`.

Let's keep it simple: 32-sided cylinder with flat shading. It'll look like a finely faceted cap. That's fine for luxury.

Hmm, actually let's go with 16 sides for the cap and 8 for the body — distinct facet character.

Let me now also think: should the bottle body be an octagonal prism? That's very "faceted crystal". Yes.

Let's add a slight taper — use a cone with two radii.

`bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.30, radius2=0.26, depth=0.5, location=(0,0,0.25))`

That gives a tapered octagonal body. Nice.

Wait, primitive_cone with radius2 != 0 gives a truncated cone (frustum). Good.

The solidify will work on it.

Liquid: matching cone, radius1=0.27, radius2=0.24, depth 0.30, at z 0.03.

Hmm, the taper makes the liquid radius at bottom 0.27 which is inside the glass inner radius 0.28 (if solidify thickness 0.02 and outer 0.30). Outer at bottom 0.30, inner at bottom 0.28. Liquid at 0.27. OK good.

Actually solidify with offset -1 pushes inward, so inner surface = outer - thickness. Yes.

Let me set solidify thickness = 0.025, offset = -1.

Outer bottom radius 0.30, inner 0.275. Liquid bottom radius 0.26.

Hmm, let's just keep it simple:
- Glass: cone vertices=8, r1=0.30, r2=0.25, depth=0.55, at z=0.275 (bottom at 0, top at 0.55)

Wait, cap needs to sit on top at ~0.55. Let's have the body top at 0.5 and neck 0.5-0.58, cap 0.56-0.66.

Body: cone r1=0.30, r2=0.24, depth=0.5, center z=0.25 (0 to 0.5)
Neck: cylinder r=0.08, depth=0.10, center z=0.55 (0.50 to 0.60)
Cap: cylinder r=0.13, depth=0.10, center z=0.63 (0.58 to 0.68)

Hmm the neck sticks out 0.02 above body top before cap starts at 0.58. Fine.

Actually make neck 0.50 to 0.60, cap 0.57 to 0.67. Cap overlaps neck.

Hmm, the glass shell's top cap is at z=0.5 (flat). Then neck sits on top. Actually the glass shell is closed so the neck is a separate solid piece. Fine.

Actually — a real bottle: body, shoulder tapering to a neck, then cap. The taper from 0.24 to 0.08 should be smooth. Let's add a shoulder cone: r1=0.24 (matching body top), r2=0.08, depth=0.06, at z=0.53.

Hmm, this is getting complex. Let's simplify: body top radius 0.24, then a short shoulder cone from 0.24 to 0.09 over 0.05 height, then neck.

Body: 0 to 0.5
Shoulder: 0.5 to 0.56, r 0.24→0.09
Neck: 0.56 to 0.62, r 0.09
Cap: 0.60 to 0.70, r 0.14

Glass parts: body (with solidify), shoulder (with solidify), neck (with solidify), cap (gold, solid).

Liquid: inside body only, from 0.03 to 0.40, r1 0.27, r2 0.22 (matching inner taper).

Inner radius of body at bottom: 0.30 - 0.025 = 0.275. At top: 0.24 - 0.025 = 0.215. Liquid slightly smaller.

Liquid: cone r1=0.265, r2=0.21, depth=0.37, center 0.215. Bottom 0.03, top 0.40.

OK.

Now, we need the "gold cap" to reflect the studio. Good.

Let me also add a small gold collar/band at the neck base for luxury. Optional. Skip.

**Now the cam target**: 
Start target at z=0.28 (body center), end at z=0.65 (cap center).

Radius 3.4 → 0.85. Actually let's compute: at final, camera at radius 0.85 from axis, height 0.70, target z 0.65. Distance = sqrt(0.85² + 0.05²) ≈ 0.85. FOV width at 0.85m = 2*0.85*18/50 = 0.61m. Cap diameter 0.28 → 46% of frame. Good close-up.

Actually let's go to radius 0.75. Width = 0.54, cap 52%. 

Let's use radius 3.4 → 0.75.

Height: 1.2 → 0.72.

Hmm, at height 0.72 and target 0.65, camera is slightly above looking slightly down. But the camera height is measured at the camera position, and the camera axis is the same. OK.

But careful: at the end, the camera is at z=0.72 and the bottle cap top is at z=0.70. So we're looking just above the cap. Good.

Actually, the camera at height 0.72, radius 0.75, looking at (0,0,0.65). The direction is (0-0.75*sin, ...). The look direction has a slight downward component. Fine.

**Floor**: a large plane at z=0 with dark reflective material? Or just the pedestal. Let's add a floor plane with a dark material (like the marble but matte) to catch shadows.

Actually, a glossy dark floor would look luxurious. Let's make it dark charcoal, roughness 0.3.

Hmm, but the camera at the end is at z=0.72 looking at the cap — the floor won't be visible much. Fine.

Let's add it anyway.

**Backdrop**: large plane at y = +4, from z=0 to z=6, width 20. Wait, with camera orbiting from -80° to +120°, the camera goes around. At angle 120°, the camera is at (radius*sin(120°), -radius*cos(120°)) = (0.87r, +0.5r). So positive y. The backdrop at y=+4 might be behind the camera.

Hmm. Let's use a cylindrical backdrop (cyclorama) so it's always behind the bottle.

Create a cylinder of radius 8, open top/bottom, with normals flipped so we see the inside. Or just use a big cylinder and disable backface culling (which is default in Cycles — Cycles renders both sides).

Actually a cylinder mesh with proper normals pointing outward — Cycles will still show the inside. So a cylinder radius 8, depth 12, centered at (0,0,3), with the material applied. From inside, we see the gradient.

Let's use a cylinder with 64 vertices.

For the gradient: use Texture Coordinate → Generated → Z → ColorRamp. But Generated coords on a cylinder: they're normalized to the bounding box, so Z goes 0 to 1 bottom to top. 

Hmm, but the gradient would just be horizontal bands. That's fine for a "backdrop gradient".

Actually I want the brightest part behind the bottle around the middle. Let's use a ColorRamp that goes dark at bottom, brighter in the middle, dark at top. Or just dark→bright→dark.

Let's do: 0 → (0.01, 0.02, 0.03), 0.35 → (0.06, 0.10, 0.14), 0.5 → (0.08, 0.10, 0.12), 1 → (0.02, 0.01, 0.03). Emission strength ~1.5.

Hmm. Actually for a "subtle coloured backdrop gradient" — teal at bottom to plum at top maybe.

I'll go: bottom dark blue-teal, mid slightly brighter teal, top dark plum.

Let's also add radial falloff so it's brighter behind the bottle. That requires more nodes. Keep it simple.

OK, also the floor shouldn't be visible through the backdrop. The backdrop cylinder goes from z=-1 to z=11, so it covers.

Wait — the cylinder bottom cap. If we add a cap, we can't see inside from the top. Let's not cap it, or cap it at the bottom (below floor).

Actually let's create the cylinder with `end_fill_type='NOTHING'`? `bpy.ops.mesh.primitive_cylinder_add(..., end_fill_type='NGON')` default caps both ends. For our purposes having caps is fine since the camera stays inside. But the top cap would block light? Not an issue with area lights inside.

Hmm, but light from outside wouldn't reach. All our lights are inside the cylinder. Fine.

Let's just make it with caps. Or better, no caps so we don't have weird geometry. Let's use end_fill_type='NOTHING'. Actually caps don't matter. I'll use default.

Hmm, actually if the cylinder has a top cap at z=9, and lights are inside, it's fine. Let's keep it simple with caps.

Let me set cylinder: radius 9, depth 14, location (0,0,3). So z from -4 to 10.

But then the top cap at z=10 might catch light weirdly. Whatever.

Let's remove caps: use `end_fill_type='NOTHING'`.

Actually there is no such option in `primitive_cylinder_add`... Let me check. Yes there is: `end_fill_type` in ('NOTHING', 'NGON', 'TRIFAN'). Default 'NGON'.

OK, use 'NOTHING'. Then it's an open tube. 

Now materials assignment.

Let me write the full script.

```python
import bpy
import math
from mathutils import Vector

# ---------------------------------------------------------------
# Clean the scene
# ---------------------------------------------------------------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

for coll in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
             bpy.data.lights, bpy.data.cameras, bpy.data.worlds,
             bpy.data.node_groups):
    for block in list(coll):
        if block.users == 0:
            coll.remove(block)
```

Careful: removing worlds might break the current world reference. Let's not remove worlds. Actually after factory startup there's "World". Let's just reuse it.

Actually, `bpy.data.worlds` removal with users==0 — the scene's world has users>=1 so it won't be removed. Fine.

Helper functions:

```python
def new_principled(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    return mat, nt, bsdf
```

Also `set_input(bsdf, name, value)` with try/except in case the name differs.

```python
def si(node, name, value):
    if name in node.inputs:
        node.inputs[name].default_value = value
```

Now the objects.

Let me write out the code.

```python
# ---------------- Glass bottles parts ----------------
def add_cone(verts, r1, r2, depth, loc, name):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2,
                                    depth=depth, location=loc)
    o = bpy.context.active_object
    o.name = name
    return o

def add_cyl(verts, r, depth, loc, name):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth,
                                        location=loc)
    o = bpy.context.active_object
    o.name = name
    return o
```

Body:
```python
body = add_cone(8, 0.30, 0.24, 0.50, (0,0,0.25), "Bottle_Body")
sol = body.modifiers.new("Solidify", 'SOLIDIFY')
sol.thickness = 0.025
sol.offset = -1.0
sol.use_even_offset = True
```

Shoulder:
```python
shoulder = add_cone(8, 0.24, 0.085, 0.06, (0,0,0.53), "Bottle_Shoulder")
sol2 = shoulder.modifiers.new("Solidify", 'SOLIDIFY')
sol2.thickness = 0.02
sol2.offset = -1.0
```

Hmm the shoulder top at z=0.56 with radius 0.085, inner radius 0.065. Neck radius 0.08.

Neck:
```python
neck = add_cyl(16, 0.085, 0.08, (0,0,0.58), "Bottle_Neck")
sol3 = neck.modifiers.new("Solidify", 'SOLIDIFY')
sol3.thickness = 0.02
sol3.offset = -1.0
```
Neck spans 0.54 to 0.62.

Cap:
```python
cap = add_cyl(16, 0.135, 0.11, (0,0,0.635), "Bottle_Cap")
```
Cap spans 0.58 to 0.69.

Cap covers neck top (0.62). Good.

Liquid:
```python
liquid = add_cone(8, 0.265, 0.215, 0.37, (0,0,0.215), "Bottle_Liquid")
```
Bottom 0.03, top 0.40. Radius bottom 0.265 vs glass inner 0.275 ✓.

Actually the cone inside also tapers. The glass inner radius at z=0.03 vs z=0.40 — the body cone from 0.30@0 to 0.24@0.5, so at z=0.03 r=0.2964, inner 0.2714. At z=0.40, r=0.252, inner 0.227. Liquid r at 0.03 = 0.265 (inside 0.2714 ✓), at 0.40 = 0.215 (inside 0.227 ✓). 

Pedestal:
```python
ped = add_cyl(64, 0.62, 0.16, (0,0,-0.08), "Pedestal")
```
Top at z=0.

Add a bevel to the pedestal edges.

```python
bev = ped.modifiers.new("Bevel", 'BEVEL')
bev.width = 0.01
bev.segments = 3
```

Floor:
```python
bpy.ops.mesh.primitive_plane_add(size=40, location=(0,0,0))
floor = bpy.context.active_object
floor.name = "Floor"
```
But the pedestal top is at z=0 and the floor is at z=0 too. The pedestal would be half-buried. Let's put the floor at z=-0.16 (bottom of pedestal) — actually the pedestal bottom is at -0.16. Let's put the floor at z=-0.16.

Hmm, or make the pedestal taller and the floor lower. Let's put the floor at z = -0.16 so the pedestal sits on it.

Actually, better: raise everything so the floor is at 0. Let's keep floor at z=0 and pedestal from 0 to 0.16, bottle on top of the pedestal from 0.16 to ...

Hmm, that complicates. Let's just set the floor at z = -0.16 and keep the pedestal from -0.16 to 0. That's simplest.

Actually even simpler: floor at z=-0.16, size 40.

Wait, but the camera at z=1.2 looking at the bottle — the floor will be visible far away. With the backdrop cylinder radius 9, the floor plane of size 40 extends beyond. Let's make the floor size 18 (radius 9), matching the backdrop.

OK.

**Now the marble material for the pedestal.**

Nodes:
- TexCoord (Object) → Mapping (scale 1) → Noise (scale 5, detail 8) → ColorRamp

Actually let's use the Object coordinates of the pedestal.

```python
mat_m, nt, bsdf = new_principled("BlackMarble")
tc = nt.nodes.new("ShaderNodeTexCoord")
mp = nt.nodes.new("ShaderNodeMapping")
mp.inputs["Scale"].default_value = (1.0, 1.0, 3.0)
nz = nt.nodes.new("ShaderNodeTexNoise")
nz.inputs["Scale"].default_value = 4.0
nz.inputs["Detail"].default_value = 8.0
nz.inputs["Roughness"].default_value = 0.6
ramp = nt.nodes.new("ShaderNodeValToRGB")
# edit color ramp
```

ColorRamp elements: default 2 elements at 0 and 1. Add more.

```python
cr = ramp.color_ramp
cr.elements[0].position = 0.40
cr.elements[0].color = (0.004, 0.004, 0.006, 1)
cr.elements[1].position = 0.62
cr.elements[1].color = (0.004, 0.004, 0.006, 1)
e2 = cr.elements.new(0.50)
e2.color = (0.35, 0.36, 0.40, 1)
e3 = cr.elements.new(0.54)
e3.color = (0.001, 0.001, 0.002, 1)
```

Hmm, this gives a thin bright vein at 0.50 and dark above 0.54. Let's simplify:

elements:
- 0.0 → dark
- 0.42 → dark
- 0.50 → light gray (vein)
- 0.56 → dark
- 1.0 → dark

Set default 2 elements to position 0.42 and 0.56 with dark colors, then add two more at 0.0 (dark) and 0.50 (light).

Wait, positions must be distinct and sorted. Default elements are at 0.0 and 1.0. I'll set element[0] to 0.42 and element[1] to 0.56... then add 0.50 and 1.0.

Actually I can just set the two defaults and add two.

Let's do:
```python
cr.elements[0].position = 0.0
cr.elements[0].color = dark
cr.elements[1].position = 1.0
cr.elements[1].color = dark
vein = cr.elements.new(0.48)
vein.color = (0.35,0.36,0.4,1)
vein2 = cr.elements.new(0.52)
vein2.color = (0.05, 0.05, 0.06, 1)
```

Hmm, that gives a bright band from 0.48 to 0.52... Actually the ramp interpolates. With dark at 0 and 1, and bright at 0.48 and slightly less bright at 0.52, we get a spike.

Better: 
- pos 0.46 → dark
- pos 0.49 → bright gray
- pos 0.51 → dark

That's a thin vein.

Let's use default elements as dark at 0.46 and 0.51, and add a bright one at 0.49. Then set element[1] (originally at 1.0) to 0.51... but then positions 0.51 and 0.49 need the third at... hmm.

Simplest: delete all, then add three elements.

```python
cr = ramp.color_ramp
# clear
while len(cr.elements) > 1:
    cr.elements.remove(cr.elements[-1])
cr.elements[0].position = 0.0
cr.elements[0].color = (0.003, 0.003, 0.004, 1)
e = cr.elements.new(0.47); e.color = (0.003,0.003,0.004,1)
e = cr.elements.new(0.50); e.color = (0.30,0.31,0.34,1)
e = cr.elements.new(0.53); e.color = (0.003,0.003,0.004,1)
e = cr.elements.new(1.0); e.color = (0.003,0.003,0.004,1)
```

Wait element[0] is at 0.0 and there's a default element at 1.0. Let me just do it carefully — after removing all but one, there's one at 0.0. Then I add new ones.

OK, good.

Set roughness to 0.12, specular high. Metallic 0.

**Now lights.**

Helper:
```python
def point_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat('-Z','Y').to_euler()
```

Key light:
```python
ld = bpy.data.lights.new("Key", 'AREA')
ld.energy = 600
ld.size = 2.0
ld.shape = 'SQUARE'
key = bpy.data.objects.new("Key", ld)
bpy.context.scene.collection.objects.link(key)
key.location = (-2.4, -2.6, 2.8)
point_at(key, (0,0,0.35))
```

Rim light:
```python
ld2 = bpy.data.lights.new("Rim", 'AREA')
ld2.energy = 350
ld2.size = 1.0
ld2.color = (0.85, 0.92, 1.0)   # cool rim
rim = ...
rim.location = (2.6, 1.8, 1.6)
point_at(rim, (0,0,0.45))
```

Fill:
```python
ld3 energy 80, size 3.0, color warm
fill.location = (3.0, -2.4, 1.0)
```

Hmm, but the camera orbits. At the end position, the camera is at angle 120°, which is (r*sin120, -r*cos120) = (0.866r, 0.5r). So positive y. The rim light is at (2.6, 1.8, ...) — also positive y. So at the end, the rim is between the camera and the bottle? No — the rim is at radius sqrt(2.6²+1.8²)=3.16, the camera ends at 0.75. So the rim light is far behind the bottle from the camera's view? Not exactly.

Let's think. At the end, the camera is at (0.65, 0.375, 0.72) roughly (angle 120°). Looking at the bottle. The rim at (2.6, 1.8, 1.6) is roughly in the same direction from the origin (angle atan2(2.6, -1.8)... hmm let me compute angles properly.

My camera position: (radius*sin(angle), -radius*cos(angle)).
- angle=-80°: (r*sin(-80), -r*cos(-80)) = (-0.985r, -0.174r). So negative x, negative y.
- angle=120°: (r*sin120, -r*cos120) = (0.866r, 0.5r). Positive x, positive y.

Rim at (2.6, 1.8): direction angle atan2(2.6, 1.8)... using the same convention, angle such that sin = 2.6/3.16=0.822, cos = -1.8/3.16=-0.5696. So angle = 124.7°. Close to the camera's final angle of 120°. So at the end, the rim light would be behind the camera... no wait.

The camera is at angle 120° at radius 0.75. The rim is at angle 124.7° at radius 3.16. So the rim is behind the camera (further out in the same direction). That means at the end, the rim light is behind the camera, not behind the bottle. That's bad — no rim light on the bottle.

Hmm. Since the camera orbits 200°, no static light will stay in the right relative position. 

Options:
1. Also animate the lights to follow the camera (like a real product shoot with lights on a rig).
2. Accept that lighting changes.

For a real commercial look, we'd want consistent lighting. Let's rig the lights relative to the camera: place them at fixed angles relative to the camera direction. That way as the camera orbits, the lights orbit too. This is like a "turntable" setup where the object rotates instead. Actually in a real studio shoot, you'd rotate the object and keep the lights fixed — which is exactly equivalent to rotating the camera and lights together while keeping the object fixed!

But we're also rotating the pedestal. Hmm.

Simplest: parent the lights to an empty that rotates with the camera's angle. Or just compute the light positions each frame from the camera angle.

Let's do: lights are positioned in a frame that rotates with the camera azimuth. Key at angle offset -50° from the camera, rim at +160°, fill at +100°.

Actually, let's keep it simpler: make the "studio" rotate with the camera. So define light positions relative to a rotating azimuth.

Let me define:
- cam_azimuth = angle of the camera
- Key light at azimuth (cam_azimuth - 55°), elevation 45°, distance 4
- Rim at azimuth (cam_azimuth + 150°), elevation 20°, distance 4.5
- Fill at azimuth (cam_azimuth + 70°), elevation 15°, distance 4.5

Hmm, rim at cam+150° means it's behind the object. Good.

Then keyframe the light positions each frame too.

Hmm, but that adds a lot of keyframes. Alternatively, parent the lights to an Empty and rotate the Empty. That's cleaner!

Yes: create an Empty "LightRig" at the origin. Parent key, rim, fill to it. Then keyframe the empty's rotation_euler.z.

But the initial positions of the lights need to be in the empty's local space. Since the empty is at the origin with no rotation initially, world = local. Then rotating the empty rotates the lights around the origin. 

But the camera's azimuth changes over time. The empty rotation should match. Let's just set:
- At frame 1, camera azimuth = -80°. Lights placed at their positions relative to azimuth -80°.
- The empty rotates with the camera so lights maintain their relative angles.

Empty rotation = cam_azimuth - (-80°) = cam_azimuth + 80°. So from 0 to 200°.

Let me place the lights at their frame-1 positions (camera azimuth -80°):

Key: at camera azimuth -80° - 55° = -135°. 
- Position: (d*sin(az), -d*cos(az), h) where d = 3.5, h = 2.8.
- sin(-135°) = -0.707, cos(-135°) = -0.707.
- So x = 3.5*(-0.707) = -2.47, y = -3.5*(-0.707) = 2.47. Wait, my formula was (r*sin(a), -r*cos(a)). So y = -r*cos(-135°) = -3.5*(-0.707) = +2.47.

Hmm, that gives y positive. But at camera azimuth -80°, the camera is at (-0.985r, -0.174r), so y negative. And the key light at azimuth -135° would be at (-0.707*3.5, +0.707*3.5) = (-2.47, +2.47). That's on the opposite side in y! That's wrong.

Let me recheck. My formula: position = (r*sin(a), -r*cos(a)).
- a = -80°: sin = -0.985, cos = 0.174. Position = (-0.985r, -0.174r). ✓.
- a = -135°: sin = -0.707, cos = -0.707. Position = (-0.707r, +0.707r).

So the key light at azimuth -135° is at (-2.47, +2.47). The camera at azimuth -80° is at (-3.4, -0.6). These are far apart. Hmm, that means the key light is at the "back-left" while the camera is at the "left-slightly-front".

Wait, I think my angle convention is off. Let's define azimuth such that the camera position is (r*sin(a), -r*cos(a)). Then a=0 means (0, -r), i.e., camera in front (−y). a=90° means (r, 0), camera at +x. a=180° means (0, r). So azimuth increases counterclockwise viewed from above... let's see. From a=0 at -y, to a=90 at +x. Going from -y to +x, that's counterclockwise when viewed from +z? -y → +x: rotating counterclockwise (from south to east... hmm, viewed from above with x right and y up: -y is down, +x is right. Down → right is counterclockwise? No, down→right is counterclockwise if we go down→right→up→left. Yes that's counterclockwise. Hmm actually down(-y) → right(+x) → up(+y) → left(-x) is counterclockwise. Yes.

OK so the convention: azimuth 0 = front (camera at -y), increasing counterclockwise.

Camera starts at -80° (which is (sin(-80), -cos(-80)) = (-0.985, -0.174), so slightly right... no, x negative means left). So the camera starts at the front-left. Ends at 120° which is (0.866, 0.5) — right-back. Hmm, that's a 200° sweep going front-left → front → right → right-back. 

Wait, from -80° to 120°: passing through 0 (front) at t=0.4, through 90 (right) at t=0.85.

Hmm OK.

Now for lights relative to the camera: a standard 3-point setup has the key at ~45° to one side of the camera and elevated, and the rim opposite (behind the subject relative to the camera).

In my azimuth convention, "behind the subject relative to the camera" means azimuth = cam_azimuth + 180°.

So:
- Key at cam_azimuth - 40° (40° to the camera's left... or right depending on sign)
- Fill at cam_azimuth + 50°
- Rim at cam_azimuth + 180° ± 30°

Let's use:
- Key: az = cam_az - 45°, elev high, dist 4, size 2.5
- Fill: az = cam_az + 60°, elev low, dist 4, size 3, energy low
- Rim: az = cam_az + 165°, elev 25°, dist 4.5, size 1.2, energy high

Hmm wait, if the rim is at cam_az+165, it's nearly behind. Good.

So at frame 1, cam_az = -80:
- Key az = -125°, position = (4*sin(-125), -4*cos(-125), h) = (4*(-0.819), -4*(-0.574), h) = (-3.28, 2.29, h). Hmm, y positive.

That means the key is at +y, i.e., behind the subject (since the camera at az=-80 is at -y-ish). That's wrong — I want the key in front.

Wait. Let me reconsider. The key at az = cam_az - 45 = -125. Position = (r sin(-125), -r cos(-125)).
sin(-125°) = -sin(125°) = -0.819
cos(-125°) = cos(125°) = -0.574
So position = (-0.819r, -(-0.574)r) = (-0.819r, +0.574r). Yes, +y.

The camera at az=-80: (-0.985r, +0.174r)... wait, cos(-80°) = 0.174, so y = -0.174r. So camera y = -0.174r (negative-ish).

So the camera is at y ≈ -0.17r and the key at y = +0.57r. Different sides. So the key is indeed behind. Something's off with my sign convention understanding.

Let me recompute. Position formula: (r sin(a), -r cos(a)).
- a = 0: (0, -r). So a=0 puts the object at -y. Good, "front" = -y.
- a = 90°: (r, 0). +x.
- a = 180°: (0, r). +y = back.

So increasing a goes from front → right → back → left. In the xy plane viewed from +z with x right and y up: front is (0,-r) at the bottom, right is (r,0), back is (0,r) at the top, left is (-r,0). Bottom → right → top → left. That's counterclockwise viewed from above. Yes, same as before. OK.

Now camera at a=-80°: (r sin(-80), -r cos(-80)) = (-0.985r, -0.174r). So x negative, y slightly negative. That's front-left. OK good.

Key at a = -125°: (r sin(-125), -r cos(-125)) = (-0.819r, +0.574r). That's x negative, y positive = back-left.

Hmm. From -80° to -125°, going negative means going clockwise in azimuth. From front-left at -80, going to -125 means rotating clockwise (toward left/back-left).

Ugh, I want the key light in front of the subject (on the camera's side) but offset. Let me use key az = cam_az + 40°. That gives -40°, position = (r sin(-40), -r cos(-40)) = (-0.643r, -0.766r). x negative, y negative = front-left. 

And the camera at -80°: (-0.985, -0.174). So the key at -40° is more toward the front. Good.

Hmm, but I want the key to be off to the side of the camera axis by ~30-45°. The camera is at -80°, so the key at -40° is 40° away. In the direction of +azimuth, which is counterclockwise = toward the right side of the frame... hmm, actually with the camera looking at the origin from -80°, the key at -40° is to the camera's... let's see. Camera at (-0.985, -0.174)*r looking toward the origin. Its "right" direction (in world) would be... camera forward = (0.985, 0.174) normalized. Camera up = +z. Camera right = forward × up? For a camera looking along -Z with +Y up, the right vector in world = ... Let's just say: looking from (-0.985,-0.174) toward (0,0), the forward is (0.985, 0.174, 0). Right = forward × up_world... Right = normalize(cross(forward, (0,0,1))) = (0.174*1 - 0, 0 - 0.985*1, 0) = (0.174, -0.985, 0). So the camera's right points toward +x, -y.

The key at azimuth -40° is at (-0.643r, -0.766r). Relative to the camera at (-0.985r, -0.174r), the direction to the key is (0.342r, -0.592r) normalized ≈ (0.5, -0.866). Dot with camera right (0.174, -0.985) = 0.087 + 0.853 = 0.94. So the key is to the camera's right in frame. Good — a standard key from the right side of frame.

Actually hold on, we're evaluating at frame 1 where the key is at azimuth -40 and the camera at -80. But the lights rotate with the camera via the empty. So at every frame, the key stays at cam_az + 40. Good, consistent.

Hmm wait, but that means the key light moves around with the camera, which is unusual (normally the subject rotates and the lights stay). It's equivalent though.

But it means the lighting is always identical relative to the camera → looks consistent. Good.

However — this also means the reflections in the gold cap will always look the same relative to the camera. That's actually what we want for a "product shot".

Hmm, but the requirement says "the gold must reflect the studio" and "rim light that outlines the glass edges" — consistent rim light is good.

OK, let's do the light rig empty approach.

Actually — simpler alternative: instead of parenting to an empty, just keyframe the light positions directly using the same azimuth formula. But parenting to an empty with an animated rotation is cleaner.

Let's do the empty.

But wait — there's a subtlety. The output says "camera slowly orbits and gently pushes in". If the lights follow the camera exactly, the lighting is static relative to the camera, and the background (which is static) would rotate. That's fine.

Hmm, but actually, since the backdrop is a cylinder with a gradient that's constant in Z, rotating doesn't matter.

OK. Let's do it.

Alternative: keep the lights fixed and just accept the changing light. Actually a rotating studio setup looks more like a real commercial. I'll go with the light rig.

Hmm, but actually — a real commercial with an orbiting camera would have fixed lights, and the object rotating. The visual result: as the camera orbits, the highlights sweep across the object. That's the classic look.

With my setup (lights rotate with the camera), the highlights stay fixed relative to the camera. That's more like a "hero shot" but less dynamic.

Hmm. Let me think about which looks better. Actually for a 30-second luxury commercial, having the highlights sweep is more cinematic. But having the camera orbit into the dark side could look bad.

Compromise: parent the lights to the empty but rotate the empty at a different (slower) rate than the camera. E.g., the light rig rotates 100° while the camera orbits 200°. Then the relative lighting changes over the shot.

I like that. Let's do:
- Empty rotation: 0 → 100° over the animation.

Then at frame 1, put the lights at their "ideal" positions relative to a camera azimuth of -80°. As the animation progresses, the camera goes to 120° (a change of 200°), but the lights only move 100°. So the relative angle shifts by 100°, meaning the key goes from the front-right to the back-left. Hmm, that might be too much.

Let's do the empty rotation: 0 → 60°. Then the relative shift is 140°. The key ends up 140° away from where it started relative to the camera.

Hmm. At the start, key at cam-relative +40° (front right). After the camera moves 200° and the lights move 60°, the key is at cam-relative +40 - 140 = -100°. That's behind. Bad.

OK let's do the lights rotate 150°. Then the relative shift is -50°. Key ends at cam-relative +40-50 = -10°. That's fine — the key moves from right-of-camera to center-of-camera. Slight change.

Hmm, I think I'm overcomplicating. Let me just have the lights follow the camera at the same rate for consistent lighting, and rely on the pedestal's rotation to create changing highlights. Actually no — if the lights and camera rotate together, the object's highlights (from the object's perspective) rotate, meaning the highlights sweep across the object! Because the object is stationary (well, the pedestal rotates).

Wait: lights + camera rotate together around the object. From the object's frame, the lights rotate. So highlights sweep across the object as seen from the camera... but the camera also rotates, so it looks the same. Hmm, no.

If both the camera and lights rotate by the same amount around the object, the rendered image is identical except for the object's own rotation. So the highlights would be static. That's boring.

So: to get sweeping highlights, the lights must rotate at a different rate than the camera.

Let's make the light rig rotate by 200° - 70° = 130°... Actually, let's think about what looks good:

Frame 1: key at cam-relative +45°.
Frame 720: key at cam-relative -45°? That would be a shift of 90°.

Camera rotates 200°, lights rotate 200° + 90° = 290°? Or 200° - 90° = 110°.

Let's have the lights rotate 110° over the sequence. Then the relative key angle goes from +45° to -45°. Symmetric. 

But wait — the rim light is at cam-relative +165° at the start, going to +75° at the end. That means at the end the rim is only 75° from the camera, which is more like a side light. Hmm, still OK.

Actually let's reduce the relative shift: lights rotate 140°, so the relative shift is -60°. Key from +45 to -15. Rim from +165 to +105. Still fine — the rim at +105° is still behind-side.

OK, let's just go with lights rotating 150°. Relative shift = -50°.

Hmm, honestly, let me simplify further and just accept it. Let me pick: the light rig rotates 120° over the sequence. Relative shift -80°. Key: +45 → -35. Rim: +165 → +85. Hmm, rim at +85 is directly to the side. Not ideal at the end.

Alright, let me just have the lights follow the camera exactly (rig rotates 200°). Consistent, safe lighting. The motion in the image comes from the camera orbiting and pushing in, plus the pedestal rotating and the liquid/glass refraction changing. It'll look good.

Actually — hmm. With the pedestal rotating 360°, the bottle's facets rotate, so the refractions change. Good enough.

Hmm, but wait. If the lights rotate with the camera, we're effectively rotating the entire studio. But the backdrop cylinder is static and its gradient is uniform in azimuth, so no visual difference. Good.

OK, decision: light rig rotates exactly with the camera. Consistent lighting throughout.

Hmm, but actually... you know what, let me use a middle ground that's simple: I'll parent the lights to the camera itself (not an empty). Then they always maintain the same position relative to the camera. Then I only need to keyframe the camera. 

But lights parented to the camera would be in the camera's local space. The camera's local axes: -Z is forward, +Y is up, +X is right. So I can position lights in camera space.

Key light: place it at camera-space ~(-1.5, 2.0, -2.0) meaning left... hmm, but the camera rotates and the light would inherit that rotation, which is what we want (the light stays in the same relative position).

Hmm, but the light also needs to point at the bottle. If the light is parented to the camera, its rotation is in camera space too. I can set its rotation so it points at the object... but that changes as the camera moves. Hmm, no — if everything is rigidly attached to the camera, then the light's direction relative to the object changes. Actually no: if the light maintains a fixed position and orientation in camera space, and the object is at the origin, then as the camera orbits the object, the light's direction to the object changes.

Hmm, that's not what we want. Wait. Let's see: the camera orbits the object at a varying radius. If the light is at a fixed camera-space position, its world position relative to the object changes as the camera's distance changes. And the required pointing direction also changes.

Better: use a Track-To constraint on the lights pointing at an empty at the bottle. Then the light always points at the bottle regardless.

Yes! Use Track To constraints for the lights, targeting an empty at (0,0,0.35). Then parent the lights to an empty that rotates with the camera.

Actually, if the lights are parented to a rotating empty and have Track To constraints targeting a fixed empty at the bottle, then everything works.

Let me do that:
1. Create an Empty "LightRig" at origin, no parent.
2. Create lights, parent them to the rig, position them in world coords (which equal local coords since the rig is at origin with identity rotation at frame 1).
3. Add Track To constraints targeting a "Aim" empty at (0, 0, 0.35).
4. Animate the rig's rotation_euler.z.

Wait, but with parenting, the child's location is in the parent's local space. When I set `light.location = (-3, -2, 3)`, that's in parent space. Since the parent is at the origin with no rotation, world = local. Fine.

Then the Track To constraint will keep the light aimed at the target regardless of the parent rotation.

Hmm, but Track To with a parented object — the constraint operates in world space after the parent transform. Blender evaluates: parent transform → then constraints. So the Track To overrides the local rotation to point at the target in world space. 

Let's use `bpy.ops.object.constraint_add(type='TRACK_TO')` or create directly.

```python
c = light.constraints.new('TRACK_TO')
c.target = aim
c.track_axis = 'TRACK_NEGATIVE_Z'
c.up_axis = 'UP_Y'
```

Good.

Now for the rig rotation: it should equal cam_azimuth - (-80°) = cam_azimuth + 80°.

Since cam_azimuth = -80 + 200t, rig rotation = 200t degrees.

Great.

Now, the lights are positioned at their frame-1 world positions given cam_azimuth = -80°:
- Key: relative az +45 → absolute az = -35°. Position: (r sin(-35), -r cos(-35), z) = (4*(-0.574), -4*(0.819), 3.0) = (-2.29, -3.28, 3.0). Hmm, r=4 at az=-35.

Hmm wait, is az=-35 in front? az=0 is front (-y). az=-35 has y = -r cos(-35) = -0.819r < 0. Yes, front. And x = -0.574r < 0 = left. So the key is front-left, camera-relative +45°... 

Hmm, back up. Camera az = -80. Key az = -35. Difference = +45. So the key is at a larger azimuth than the camera, which in my convention is counterclockwise from the camera. Earlier I determined that the camera's "right" points toward increasing azimuth... let me recheck.

Camera at az=-80, at position (-0.985r, -0.174r). Camera right vector (computed earlier for a similar case): forward = normalize(0 - pos) = (0.985, 0.174, 0). right = normalize(cross(forward, up)) where up = (0,0,1). cross((0.985,0.174,0),(0,0,1)) = (0.174*1 - 0*0, 0*0 - 0.985*1, 0) = (0.174, -0.985, 0). Yes, right ≈ (0.174, -0.985).

Now the key at az=-35 is at (-0.574r, -0.819r). The direction from the camera to the key is (-0.574+0.985, -0.819+0.174) = (0.411, -0.645) normalized = (0.537, -0.843). Dot with right (0.174, -0.985) = 0.093 + 0.830 = 0.923. Positive → the key is to the right in frame. Good.

So: key at cam_az + 45°.

Fill: cam_az - 55° (to the left). Position at az = -135°, r=4.5, z=1.2.
- (4.5*sin(-135), -4.5*cos(-135), 1.2) = (-3.18, 3.18, 1.2). Hmm, y positive = back. Hmm.

Wait, az=-135: sin=-0.707, cos=-0.707. Position = (r*(-0.707), -r*(-0.707)) = (-0.707r, +0.707r). So back-left. Hmm, but the camera at az=-80 is at front-left. So the fill at back-left... that's behind the subject.

Hmm. I need to be careful: cam_az - 55 = -135. And -135 is "back-left" in my convention. But the camera is at -80 = "front-left". So the fill is 55° further clockwise... 

Wait, az=-80 → position (-0.985, -0.174) — mostly -x, slightly -y. az=-135 → (-0.707, +0.707) — equal -x and +y. So going from az -80 to az -135 rotates from "left" to "back-left". Yes, so the fill is at back-left. That's not what I want for a fill.

Hmm. It seems like the camera at az=-80 is at the "front-left", moving to az=-135 goes toward the back. So negative azimuth from -80 heads to the back-left, and positive azimuth heads to the front then right.

So: to place the fill at cam_az - 55 (which would be on the other side from the key), it ends up behind. That's wrong. Because the camera is at -80 which is already quite far in the -az direction from the "front" (0).

Hmm. Let's reconsider. Camera is at az = -80. Anything with az between -80 and something...

Camera right = increasing az. Camera left = decreasing az.
- az = -80 - 55 = -135 → this is to the camera's left. Position (-0.707r, +0.707r). Relative to the camera at (-0.985r, -0.174r), direction = (0.278r, 0.881r) → normalized (0.301, 0.954). Dot with camera right (0.174,-0.985) = 0.052 - 0.940 = -0.888. So yes, to the left. ✓.

And relative to the object at origin, az=-135 means the light is at back-left. So it's behind the subject, to the left of the camera. That's a "rim/back-left" position.

For a fill light, I want it on the opposite side of the camera from the key, but still in front of the subject. So cam_az - 55 = -135 puts it behind. Because the camera is already at -80, and the "front" is at 0.

Hmm, this is confusing because the camera is at az=-80, which means it's viewing the object from the front-left, and the +az direction is toward the front. So the camera's "left" in azimuth terms is toward the back.

OK. The relationship: the camera's right = +az. Camera's left = -az. The "front of the subject relative to camera" is at the camera's azimuth.

The key at cam_az + 45 = -35 → in front-left of the subject, camera's right. ✓
The fill at cam_az - 55 = -135 → behind-left. Not a fill.

Instead, for a fill I'd want cam_az - 55... hmm.

Wait, no. Let's think in terms of angles relative to the camera. The subject is at distance d in front of the camera. Lights at various angles around the subject.

Key at 45° to the camera's right (in azimuth). Fill at 50° to the camera's left → az = cam_az - 50. But that's -130, which is behind the subject.

Hmm, but relative to the camera, the light at cam_az - 50... the light is at azimuth cam_az - 50 around the subject. From the camera's perspective (which is at cam_az around the subject, at distance ~3), the light is at a direction... yes it's to the camera's left and behind the subject.

Hmm. OK so for a fill light, I actually want it at cam_az - 50 but at a small azimuth offset ... no.

Let me reconsider. For a light to be "on the camera's left but in front of the subject", it needs azimuth between cam_az - 90 and cam_az. But "in front of the subject" — the subject's front, relative to the camera, is the side facing the camera, i.e., azimuths within ±90° of cam_az. So cam_az - 50 is within ±90 and thus in front-of-subject... 

Hmm, but I computed y = +0.707r for az=-135, meaning the position is at back (+y). But the camera at az=-80 is at (-0.985, -0.174). Angle from camera to subject... 

Ugh, let's just think geometrically. The camera is at position P = (r sin a, -r cos a). The subject is at O = (0,0). The line from the camera to the subject. A light at position L is "in front of the subject from the camera's view" if the angle between (L - O) and (P - O) is < 90°.

P - O direction: (sin a, -cos a) with a = -80: (-0.985, -0.174).
L - O direction for az = -135: (sin(-135), -cos(-135)) = (-0.707, 0.707).
Dot: (-0.985)(-0.707) + (-0.174)(0.707) = 0.696 - 0.123 = 0.573. Angle = 55°. So yes, less than 90° — the light is on the camera's side of the subject. 

Oh, I made an error before. The light at az=-135 IS in front of the subject from the camera's view. Because "in front" means on the same side as the camera, which is the dot product criterion.

But wait, earlier I said az=-135 is "back-left" of the subject. In absolute terms, az=180 is +y which I called "back". But the camera defines what "front" is. Since the camera is at az=-80 (which is "left"), the subject's "back" (az=180, +y) is 100° away from the camera. So az=-135 is 55° from the camera direction — it's between the camera and the subject's back... no wait.

Hmm, az=-135 is 55° from the camera at az=-80. Az=180 is 260° from the camera. So az=-135 is on the camera's side. OK, I confused myself. It's fine.

So the fill at az = cam_az - 55 = -135 is at 55° to the camera's left, on the camera's side of the subject. 

And the key at az = cam_az + 45 = -35 is at 45° to the camera's right. ✓

Rim: az = cam_az + 180 ± offset = -80 + 180 = 100, plus a small offset, say +20 → 120. Or -80 + 180 - 20 = 80 (which is +y and slightly +x). Position for az=100: (sin100, -cos100) = (0.985, 0.174). So the rim is at +x, slightly +y. That's behind the camera? No — the camera is at (-0.985, -0.174)*r. The rim is at (0.985, 0.174)*R. Opposite direction. So the rim is on the opposite side of the subject from the camera. That's exactly behind the subject. ✓

Good, so rim az = cam_az + 180 = 100°.

Let me add a slight offset so the rim isn't perfectly centered: az = cam_az + 165 = 85°.

Position at az=85, r=4.5: (4.5*sin85, -4.5*cos85) = (4.483, -0.392). So +x, slightly -y.

OK. And elevation z = 1.6.

Great. Now let me finalize the light positions at frame 1 (cam_az = -80):

Key: az = -35, r = 3.8, z = 3.0
  pos = (3.8*sin(-35), -3.8*cos(-35), 3.0) = (3.8*(-0.5736), -3.8*(0.8192), 3.0) = (-2.180, -3.113, 3.0)

Fill: az = -135, r = 4.2, z = 1.4
  pos = (4.2*(-0.7071), -4.2*(-0.7071), 1.4) = (-2.970, 2.970, 1.4)

Rim: az = 85, r = 4.5, z = 1.8
  pos = (4.5*0.9962, -4.5*0.0872, 1.8) = (4.483, -0.392, 1.8)

Hmm, the fill is at y=+2.97 which is behind the subject's origin, but on the camera's side (as computed). OK.

Now sizes and energies:
- Key: size 2.5 (big soft), energy 500
- Fill: size 3.5, energy 120, slightly warm
- Rim: size 1.2, energy 400, slightly cool

These energies are in Watts for area lights. At distance ~4m with size 2.5m... Let's think. A 500W area light at 4m gives irradiance ≈ P/(4πd²) = 500/(4π*16) = 2.5 W/m². Hmm, for a diffuse white surface the radiance would be ~0.8. That's reasonable-ish. Actually Blender's area light energy is in watts, and the resulting brightness... Let's just pick values and it'll be fine. Typical: 100-1000W for studio scenes.

Actually, for Blender with a scene at 1 unit = 1 meter, an area light of 500W at 3m distance gives decent exposure. Let's go.

Let me also add the backdrop emission so it's visible.

And I should set the world to a dark color so the glass has something to refract. Set world background to a dark gray (0.02).

OK. Let's also consider the film exposure — but we can't set render settings. So the default exposure is fine.

Now let's write the whole script.

One more consideration: the camera should not be inside the backdrop cylinder. The cylinder radius is 9, camera max radius 3.4. ✓

Let me also double check the camera doesn't clip the floor at the end: camera z=0.72, floor at z=-0.16. ✓

Let me write the code now.

```python
import bpy
import math
from mathutils import Vector

# =========================================================
# 0. CLEAN SCENE
# =========================================================
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.lights,
             bpy.data.cameras, bpy.data.curves, bpy.data.images):
    for block in list(coll):
        if block.users == 0:
            coll.remove(block)
```

Note: deleting objects when in background mode with `--factory-startup` — the context should have a valid view layer. `bpy.ops.object.select_all` requires an active object context? In background mode, ops usually work. Let's be safe and use a try/except, or directly remove objects:

```python
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
```

That's safer. Let's use that.

```python
# =========================================================
# 1. HELPERS
# =========================================================
def si(node, name, value):
    if name in node.inputs:
        try:
            node.inputs[name].default_value = value
        except Exception:
            pass

def make_principled(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = None
    for n in nt.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            bsdf = n
            break
    if bsdf is None:
        bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
        out = None
        for n in nt.nodes:
            if n.type == 'OUTPUT_MATERIAL':
                out = n
        nt.links.new(bsdf.outputs[0], out.inputs['Surface'])
    return mat, nt, bsdf

def point_at(obj, target):
    d = Vector(target) - obj.location
    if d.length > 1e-6:
        obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
```

Now materials:

```python
# ---- Crystal glass ----
mat_glass, nt, b = make_principled("CrystalGlass")
si(b, "Base Color", (1.0, 1.0, 1.0, 1.0))
si(b, "Metallic", 0.0)
si(b, "Roughness", 0.02)
si(b, "IOR", 1.52)
si(b, "Transmission Weight", 1.0)
si(b, "Transmission", 1.0)  # older name fallback
si(b, "Specular IOR Level", 0.5)
```

Hmm, "Transmission Weight" is the 4.x name. In 4.5 it should be that. I'll set both with the helper which ignores missing.

Wait — `si` checks `if name in node.inputs`. For a Principled node, `node.inputs` supports `in` with a string? Yes, `node.inputs` is a bpy_prop_collection and supports string key lookup in `in` checks. Actually, `"Foo" in collection` — for bpy collections, `in` checks names. Yes, that works.

Amber liquid:

```python
mat_liq, nt, b = make_principled("AmberLiquid")
si(b, "Base Color", (0.75, 0.30, 0.035, 1.0))
si(b, "Metallic", 0.0)
si(b, "Roughness", 0.0)
si(b, "IOR", 1.45)
si(b, "Transmission Weight", 1.0)
```

Gold:

```python
mat_gold, nt, b = make_principled("PolishedGold")
si(b, "Base Color", (1.0, 0.72, 0.29, 1.0))
si(b, "Metallic", 1.0)
si(b, "Roughness", 0.10)
```

Marble with procedural veining.

Backdrop:

```python
mat_bd, nt, b = make_principled("Backdrop")
tc = nt.nodes.new("ShaderNodeTexCoord")
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
ramp = nt.nodes.new("ShaderNodeValToRGB")
nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
si(b, "Roughness", 1.0)
si(b, "Metallic", 0.0)
# emission for the backdrop glow
si(b, "Emission Color", (1,1,1,1))
si(b, "Emission Strength", 0.0)
```

Hmm, but the emission needs the ramp color too. Let's link the ramp to both Base Color and Emission Color, and set strength ~1.0? That would double the brightness. Let's just link to Emission Color and set Base Color to black, with Emission Strength 1.0. Then the backdrop is purely emissive — consistent and won't be affected by the lights.

Actually, that's clean for a studio backdrop. Let's do that.

Set Base Color to (0,0,0,1), Emission Color from ramp, Emission Strength 1.0.

Ramp for the backdrop:
- pos 0.0: (0.004, 0.010, 0.016)
- pos 0.35: (0.020, 0.055, 0.075)
- pos 0.55: (0.045, 0.030, 0.055)
- pos 1.0: (0.004, 0.002, 0.008)

Hmm, these are quite dark. With emission strength 1.0 they render as those exact colors. In a dark scene they'll be visible. Let me brighten a bit:
- 0.0: (0.008, 0.020, 0.030)
- 0.35: (0.030, 0.080, 0.110)
- 0.55: (0.070, 0.030, 0.070)
- 1.0: (0.006, 0.004, 0.012)

That should read as a subtle teal-to-plum gradient.

But wait — the Generated coordinate on a cylinder. The cylinder's bounding box: X from -9 to 9, Y from -9 to 9, Z from -4 to 10. Generated Z maps 0→1 over that range. So Z=0 at world z=-4 and Z=1 at world z=10. The bottle is at z=0-0.7, which maps to (0-(-4))/14 = 0.286 to (0.7+4)/14 = 0.336. So the bottle sits at Generated Z ≈ 0.29-0.34. My ramp has a bright region at 0.35. Good, that's right behind the bottle. 

Actually let me shift: bright at 0.30. Let's use:
- 0.0: dark
- 0.20: (0.010, 0.030, 0.045)
- 0.31: (0.040, 0.095, 0.130)
- 0.45: (0.060, 0.030, 0.070)
- 1.0: dark

Hmm, the camera looks roughly horizontally at the bottle, so the visible backdrop is around z=0.3-2 in world = Generated Z 0.31-0.43. Let's make the gradient span that.

Actually let's just use a simple two-color gradient and not worry too much:
- 0.0: (0.008, 0.018, 0.028)
- 0.30: (0.035, 0.085, 0.115)
- 0.55: (0.075, 0.032, 0.070)
- 1.0: (0.010, 0.006, 0.016)

OK.

Floor material: dark charcoal, roughness 0.35.

Marble material for the pedestal: as described.

Let me now write out everything.

Also: should I add a "glow" to the emission? No.

Let me now write the object creation code.

```python
# =========================================================
# 3. PEDESTAL
# =========================================================
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=0.60, depth=0.16,
                                    location=(0.0, 0.0, -0.08))
pedestal = bpy.context.active_object
pedestal.name = "Pedestal"
bev = pedestal.modifiers.new("Bevel", 'BEVEL')
bev.width = 0.008
bev.segments = 4
bev.limit_method = 'ANGLE'
```

Assign marble material.

Then a small inlay ring? Skip.

Now the bottle parts. I need to create them and assign materials.

```python
def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
```

Glass body:
```python
bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.30, radius2=0.24,
                                depth=0.50, location=(0,0,0.25))
body = bpy.context.active_object
body.name = "Bottle_Body"
m = body.modifiers.new("Solidify", 'SOLIDIFY')
m.thickness = 0.022
m.offset = -1.0
m.use_even_offset = True
m.use_rim = True
assign(body, mat_glass)
```

Hmm, the solidify with a cone (frustum) — the caps will be solidified too. Good.

Shoulder:
```python
bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.24, radius2=0.085,
                                depth=0.06, location=(0,0,0.53))
```
z from 0.50 to 0.56.

Neck:
```python
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.085, depth=0.08,
                                    location=(0,0,0.58))
```
z from 0.54 to 0.62.

Cap:
```python
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.135, depth=0.11,
                                    location=(0,0,0.635))
```
z from 0.58 to 0.69.

Add a bevel to the cap.

Also add a gold "collar" ring at the base of the neck? Actually, let's add a thin gold band around the shoulder-neck junction for luxury. Position at z=0.545, radius 0.095, depth 0.02. Hmm, might interfere. Skip for simplicity. Or add it — it's a nice detail.

Let's add: gold collar cylinder radius 0.10, depth 0.025, at z=0.545. Hmm, but the shoulder at z=0.53+0.03=0.56 top. At z=0.545, the shoulder radius is 0.24 + (0.085-0.24)*(0.545-0.50)/0.06 = 0.24 - 0.155*0.75 = 0.124. So a collar of radius 0.10 would be inside the shoulder. Not visible.

Skip the collar.

Liquid:
```python
bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.265, radius2=0.205,
                                depth=0.36, location=(0,0,0.21))
```
z from 0.03 to 0.39.

Check inner radius at z=0.03: body outer r at z=0.03 = 0.30 + (0.24-0.30)*(0.03/0.50) = 0.30 - 0.06*0.06 = 0.2964. Inner = 0.2964 - 0.022 = 0.2744. Liquid 0.265 ✓.

At z=0.39: body outer r = 0.30 - 0.06*0.78 = 0.2532. Inner = 0.2312. Liquid r = 0.265 + (0.205-0.265)*(0.39-0.03)/0.36 = 0.265 - 0.06*1.0 = 0.205. Inner 0.2312 > 0.205 ✓.

Good.

Hmm, but the cone's radius2 is at the top. `primitive_cone_add(radius1=R1, radius2=R2)` — radius1 is the bottom, radius2 is the top. ✓

Now, the liquid should also be capped (it's a solid cone). Fine.

Now, all these objects should rotate with the pedestal. Let's parent them to the pedestal? Or just apply the same rotation to all.

Easier: parent them all to an empty at the origin, or to the pedestal. Since the pedestal rotates around its own Z axis at the origin, and the bottle objects are also centered on the Z axis, parenting to the pedestal works.

Hmm, but the pedestal has a bevel modifier and is at z=-0.08. Parenting to it means the child's location is relative to the pedestal's origin, which is at (0,0,-0.08) world. So the child's location would need adjustment.

Let's instead create a new Empty "Turntable" at the origin, parent the pedestal and bottle objects to it, and rotate the empty.

Wait, but parenting with keep_transform... In Python:
```python
obj.parent = turntable
```
This sets the parent but the child's location becomes relative to the parent. Since the parent is at the origin with identity transform, the world positions are preserved. 

So: create an Empty "Turntable" at (0,0,0). Parent pedestal, body, shoulder, neck, cap, liquid to it. Then animate turntable.rotation_euler.z.

Actually, the pedestal's own location is (0,0,-0.08), which stays local. The empty is at the origin with no rotation, so world = local. ✓

Good.

Now the camera. Create it and set scene.camera.

Animation:

```python
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 720

FRAMES = 720
for f in range(1, FRAMES+1):
    t = (f-1)/(FRAMES-1)
    az = math.radians(-80.0 + 200.0*t)
    radius = 3.4 - 2.65*t   # 3.4 -> 0.75
    cz = 1.20 - 0.48*t      # 1.20 -> 0.72
    cx = radius*math.sin(az)
    cy = -radius*math.cos(az)
    cam.location = (cx, cy, cz)
    tz = 0.28 + 0.37*t      # 0.28 -> 0.65
    d = Vector((0,0,tz)) - Vector((cx,cy,cz))
    cam.rotation_euler = d.to_track_quat('-Z','Y').to_euler()
    cam.keyframe_insert("location", frame=f)
    cam.keyframe_insert("rotation_euler", frame=f)
    rig.rotation_euler.z = az + math.radians(80.0)
    rig.keyframe_insert("rotation_euler", frame=f)
    turntable.rotation_euler.z = math.radians(360.0*t)   # hmm
    turntable.keyframe_insert("rotation_euler", frame=f)
```

Wait, the turntable rotating 360° — at the end it snaps back to the start orientation. That's fine since it's a full revolution. But the keyframes: rotation_euler.z goes from 0 to 2π linearly. That interpolates fine.

Hmm, but actually a 360° rotation over 30 seconds might be too fast combined with the camera orbit. Let's reduce to 240°. Actually, "slowly rotating" — 360° over 30s = 12°/s. That's one revolution per 30s. It's slow. OK, keep it.

Hmm, actually, since the camera orbits 200° in the other direction relative... let me compute relative rotation. Camera azimuth goes -80 → 120. Turntable goes 0 → 360. Combined relative motion = camera relative to bottle: the bottle rotates +360 relative to the world, and the camera moves +200. So the bottle appears to rotate 360 - 200 = 160° relative to the camera. Hmm, that's a modest relative rotation.

Actually let's set the turntable to 360° — fine.

Wait, actually I realize I should double check: the turntable rotation direction. rotation_euler.z positive = counterclockwise viewed from +z. The camera azimuth also increases counterclockwise. So the bottle rotates in the same direction as the camera. Relative motion = 160°. Hmm, the visible facets change by 160°, which is decent.

Actually let me make the turntable rotate the other way, so relative rotation is 360+200 = 560°? That'd be fast. Hmm.

Let's just do turntable = -360° * t (clockwise). Then relative = 360 + 200 = 560° which is 1.5 revolutions. Might be too fast.

Let me use turntable = +360*t. Relative 160°. Slow and elegant. Good.

Hmm, wait, but actually the requirement mentions "slowly rotating round black marble pedestal". A slow rotation. Let's keep 360° over 30s.

Hmm, one issue: the liquid inside the bottle is a solid cone that rotates with the bottle. Since it's a solid of revolution-ish (octagonal), the facets rotate. Fine.

Now, keyframing 720 frames × (camera 6 + rig 3 + turntable 3) = 720*12 = 8640 keyframes. That's fine but a bit slow. Let's reduce: keyframe the camera every frame (needed for the smooth orbit), but the rig and turntable can be keyframed at fewer points since their motion is linear.

Actually, keyframe the camera every frame, and the rig/turntable every 12 frames with linear interpolation. Since their motion is linear, that's exact.

Hmm, but rotation_euler interpolation with linear is exact for linear motion. Let's use LINEAR interpolation for those.

Actually the camera keys also should use linear interpolation between frames — but since we key every frame, it doesn't matter.

Let me set the keyframe interpolation to LINEAR globally for safety? Bezier with keys every frame is fine (no overshoot since adjacent keys constrain). Actually Bezier auto handles can overshoot. Let's set the camera's fcurve interpolation to LINEAR.

Let's do:
```python
if cam.animation_data and cam.animation_data.action:
    for fc in cam.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
```

Similarly for the rig and turntable.

Hmm, in Blender 4.4+, actions have "slots" and layers. `action.fcurves` might still work for legacy actions. In 4.5, `action.fcurves` is deprecated but still accessible? Let me use a safer approach:

Actually, in Blender 4.4, there's the new slotted actions system. `action.fcurves` may still work via the legacy API... Hmm, risky.

Alternative: don't worry about interpolation. With keys on every frame, Bezier auto-clamped won't overshoot much. Actually, Blender's default keyframe interpolation is BEZIER with auto-clamped handles, which doesn't overshoot for monotonic sequences. So it's fine.

Actually the default handle type is 'AUTO_CLAMPED' which prevents overshoot. Good. So no need to change.

But for the rig and turntable with sparse keys, auto-clamped on a linear sequence gives a straight line (since it's monotonic and evenly spaced... actually auto-clamped gives ease at the ends). Hmm.

Let's just key them every frame too. Simpler. 720 extra keys is nothing.

OK.

Hmm, actually let's reduce total work: key the camera every frame, and the rig/turntable every frame too. 8640 keys total. Blender handles that fine.

Now let's also make sure `scene.frame_end = 720`.

Also set `scene.render.fps = 24`. That's a render setting... The requirement says don't set render engine, resolution, samples, or output path. Setting fps is fine and needed for the "24 fps" requirement. Let's set it.

Hmm, "do not set the render engine, resolution, samples or output path". fps is not in that list. I'll set fps=24.

Let's finalize and write.

One more thing: the empty for the light rig and the aim empty. Let's create them.

```python
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0,0,0))
rig = bpy.context.active_object
rig.name = "LightRig"

bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0,0,0.35))
aim = bpy.context.active_object
aim.name = "AimTarget"
```

Lights:

```python
def make_area(name, loc, energy, size, color=(1,1,1)):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = energy
    ld.size = size
    ld.color = color
    ob = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.parent = rig
    c = ob.constraints.new('TRACK_TO')
    c.target = aim
    c.track_axis = 'TRACK_NEGATIVE_Z'
    c.up_axis = 'UP_Y'
    return ob
```

Wait, when I set `ob.parent = rig`, the location becomes the local offset. Since the rig is at the origin, it's fine. But I set the location before parenting — Blender doesn't auto-adjust, it just uses the local value. Since the rig has an identity transform at the time of creation, that's the same. Good.

Now let's write it all out.

Actually one concern: `bpy.context.scene.collection.objects.link(ob)` — need to make sure the object is in the view layer. Yes.

Let me also double-check the Track To constraint: `track_axis = 'TRACK_NEGATIVE_Z'` means the object's -Z axis points at the target. Area lights emit along their -Z. ✓ `up_axis = 'UP_Y'`. ✓

Now, the world:

```python
world = bpy.data.worlds.get("World")
if world is None:
    world = bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.015, 0.017, 0.022, 1.0)
    bg.inputs[1].default_value = 1.0
```

Now the floor:

```python
bpy.ops.mesh.primitive_plane_add(size=18, location=(0,0,-0.16))
floor = bpy.context.active_object
floor.name = "Floor"
assign(floor, mat_floor)
```

Hmm, the floor at z=-0.16 with size 18 (so radius 9). But the backdrop cylinder has radius 9. So the floor edge meets the backdrop. Good.

But the camera at max radius 3.4 and height 1.2 looking at the bottle — the floor extends to radius 9. Fine.

Backdrop cylinder:
```python
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=9.0, depth=16.0,
                                    location=(0,0,3.0), end_fill_type='NOTHING')
backdrop = bpy.context.active_object
backdrop.name = "Backdrop"
assign(backdrop, mat_backdrop)
```

Cylinder from z=-5 to z=11. Generated Z: 0 at -5, 1 at 11. Bottle at z 0-0.7 → Generated Z = 5/16=0.3125 to 5.7/16=0.356. Good.

Hmm, our ramp has the bright spot at 0.30-0.35. Let me adjust to 0.33.

Actually let's just recompute. I'll set:
- 0.0: (0.006, 0.014, 0.022)
- 0.25: (0.020, 0.055, 0.080)
- 0.34: (0.045, 0.100, 0.130)
- 0.50: (0.070, 0.030, 0.070)
- 1.0: (0.008, 0.005, 0.014)

Good.

Hmm — but wait, emission with these dark colors will be barely visible. In an sRGB view transform (Filmic/AgX in Blender 4.x default), dark values get lifted. AgX is the default in 4.x. It should be fine.

Actually, the default view transform in Blender 4.x is AgX. It desaturates and lowers contrast. The colors might look muted. That's fine for "subtle".

But we can't set the view transform (it's a render setting... well, it's a color management setting). The instructions say don't set render engine, resolution, samples, output path. Color management isn't listed but let's not touch it to be safe.

Hmm, actually, with AgX the emission at 0.13 would look fairly dim. Let me boost the emission strength to ~3-4 for the backdrop. Actually let's set the emission strength to 2.5 and darken the colors slightly. Or keep the colors and use strength 3.

Let's use strength 2.0.

Hmm, then it becomes a light source, illuminating the bottle. Which could be nice for the rim. Actually, the backdrop cylinder surrounds the scene, so emission from it lights everything. At 0.13 * 2.0 = 0.26 radiance, spread over a huge area — it would add a soft ambient. That's fine.

Actually, it'd probably wash out. Let's use strength 1.0 but boost the colors:

- 0.0: (0.010, 0.025, 0.040)
- 0.25: (0.040, 0.110, 0.160)
- 0.34: (0.080, 0.180, 0.230)
- 0.50: (0.130, 0.055, 0.130)
- 1.0: (0.012, 0.008, 0.022)

With strength 1.0. These are brighter, giving a visible colored gradient. As emission-only surfaces, they'd also act as a soft light source. Radiance 0.2 over a hemisphere → irradiance ~0.6. Comparable to the area lights. Could be fine, adds ambient.

Hmm, it might make the scene too bright and flat. Let's use strength 0.7.

I'll go with strength 0.8 and the colors above. Good enough — I can't preview, so let's just make reasonable choices.

Now, let's think about whether the glass will look right. The glass cone with solidify, IOR 1.52, transmission 1.0. With a background of 0.01-0.2 and lights at 500W, the glass should show nice refractions and highlights.

The liquid at IOR 1.45 with amber base color and transmission — light passing through gets tinted amber. 

Now — an important detail: for the glass to look good, we should enable "Caustics" — but that's a render setting (Cycles). The requirement says don't set render engine settings... Actually, "do not set the render engine, resolution, samples or output path". Light path settings aren't mentioned but let's not touch them.

Hmm, but caustics in Cycles are off by default, which means the light through the glass won't produce caustics on the floor. That's fine.

Actually, the refraction through the glass will still show the background refracted. Good.

Let me also think about whether to add a slight "bevel" to the glass edges so they catch light. A small bevel would help. But with an 8-sided prism and solidify, adding a bevel might create artifacts. Let's skip.

Actually, let's add a subsurf? No.

Let me instead just add a small bevel modifier with width 0.003, segments 2, limit angle 30°. Should be safe.

Hmm, the solidify + bevel order: bevel should come after solidify. Modifier order in the stack is as added. Add solidify first, then bevel. ✓

Let me add it.

Actually, the glass is very thin (0.022). A bevel of 0.003 on the outer edges is fine.

Hmm, bevels on the inner shell too. Should be OK.

Let me include it. Actually, to reduce risk of weird geometry, let me use a small bevel with clamp_overlap=True (default). OK.

Let me now write the final script.

Also: `bpy.context.view_layer.update()` might be needed. Not really.

One more: assigning materials to objects with modifiers — the material goes on the base mesh, and the modifier inherits it. ✓

Let's write.

```python
import bpy
import math
from mathutils import Vector

# =====================================================================
#  LUXURY PERFUME COMMERCIAL  -  Blender 4.5 LTS
# =====================================================================

# ---------------------------------------------------------------
# 0.  Wipe the factory scene
# ---------------------------------------------------------------
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.lights,
             bpy.data.cameras, bpy.data.curves, bpy.data.images,
             bpy.data.node_groups):
    for blk in list(coll):
        if blk.users == 0:
            coll.remove(blk)

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 720
scene.render.fps = 24

# ---------------------------------------------------------------
# helpers
# ---------------------------------------------------------------
def si(node, name, value):
    if name in node.inputs:
        try:
            node.inputs[name].default_value = value
        except Exception:
            pass

def new_material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf is None:
        bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
        out = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'), None)
        if out:
            nt.links.new(bsdf.outputs[0], out.inputs['Surface'])
    return mat, nt, bsdf

def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
```

OK now let's continue.

I'm going to write the whole thing now, carefully.

For the marble ColorRamp manipulation:

```python
cr = ramp.color_ramp
# keep only one element, reposition
while len(cr.elements) > 1:
    cr.elements.remove(cr.elements[-1])
cr.elements[0].position = 0.0
cr.elements[0].color = (0.004, 0.004, 0.006, 1.0)
e = cr.elements.new(0.44); e.color = (0.004, 0.004, 0.006, 1.0)
e = cr.elements.new(0.485); e.color = (0.28, 0.29, 0.33, 1.0)
e = cr.elements.new(0.53); e.color = (0.004, 0.004, 0.006, 1.0)
e = cr.elements.new(1.0); e.color = (0.004, 0.004, 0.006, 1.0)
```

Hmm, `cr.elements.new(pos)` returns the new element. And after adding at 0.44, then 0.485, etc. — they should stay sorted automatically. Let's just add them in increasing order.

Actually, when you remove elements, the remaining one might not be at index 0... Let's be careful.

```python
els = cr.elements
# remove all but the first
for i in range(len(els)-1, 0, -1):
    els.remove(els[i])
els[0].position = 0.0
els[0].color = dark
```

Then add new ones. OK.

Now, mapping the noise: I'll use Object coordinates so the marble pattern is stable in object space.

```python
tc = nt.nodes.new("ShaderNodeTexCoord")
mp = nt.nodes.new("ShaderNodeMapping")
mp.inputs["Scale"].default_value = (1.0, 1.0, 2.5)
nz = nt.nodes.new("ShaderNodeTexNoise")
nz.inputs["Scale"].default_value = 3.0
nz.inputs["Detail"].default_value = 10.0
nz.inputs["Roughness"].default_value = 0.62
```

Links: tc.Object → mp.Vector; mp.Vector → nz.Vector; nz.Fac → ramp.Fac; ramp.Color → bsdf.Base Color.

Also set bsdf Roughness = 0.13, Metallic = 0.0, and "Specular IOR Level" = 0.6.

Actually, marble should have some subsurface/translucency, but keep it simple.

OK. Writing the final script now.

One last thing about the camera keyframes — I should make sure the camera object has `rotation_mode = 'XYZ'` (default) so rotation_euler works.

Also, for the Empty's rotation, default rotation_mode is 'XYZ'. ✓

Let me write.

Also, I need to be careful: `ob.parent = rig` — but the parent's transform is identity at creation. However, `matrix_parent_inverse` defaults to identity, so the child keeps its local transform as world. ✓

Let me write the final code.

Regarding the "aim" empty — I'll place it at (0,0,0.35). The lights track it.

Let me write out the whole thing.

Final check on the camera path:
- t=0: az=-80°, r=3.4, z=1.20, target z=0.28
- t=1: az=120°, r=0.75, z=0.72, target z=0.65

Distance at t=0: sqrt(3.4² + (1.20-0.28)²) = sqrt(11.56+0.846) = 3.52. FOV width = 2*3.52*18/50 = 2.53m. The bottle (0.6m wide) fills 24%. Reasonable for a wide shot... maybe a bit small. Let's reduce the start radius to 2.8.

Distance = sqrt(7.84+0.85) = 2.95. Width = 2.12m. Bottle 28%. Better.

End: r=0.75, z=0.72, target 0.65. Distance = sqrt(0.5625 + 0.0049) = 0.753. Width = 0.542m. Cap diameter 0.27 → 50%. Good.

So radius: 2.8 → 0.75. z: 1.20 → 0.72.

Hmm, at t=0 with r=2.8, z=1.2 — the camera is at a 45° elevation. That's a high angle. For a product shot, a lower angle is more heroic. Let's use z=0.95 at the start. 

Elevation angle = atan((0.95-0.28)/2.8) = atan(0.239) = 13.5°. That's a nice slightly-above angle.

At the end: z=0.72, target 0.65, r=0.75. Elevation = atan(0.07/0.75) = 5.3°. Nearly level. Good for a close-up of the cap.

Hmm, but at the start with the camera at z=0.95 and radius 2.8, the pedestal (radius 0.6, height 0.16) will be visible. Fine.

Let's use z: 0.95 → 0.72.

Actually for the wide shot, showing the pedestal and floor is good. Let's make the start a bit higher: z=1.05, r=2.9. Elevation = atan(0.77/2.9) = 14.9°. Fine.

OK final: r 2.9 → 0.75, z 1.05 → 0.72, target z 0.26 → 0.65.

Alright, writing it.

Let me double check the liquid top: 0.39. The camera looks at z=0.26 at the start. Fine.

Writing now.

def point_at is used for... actually I'm using Track To constraints, so I don't need point_at for lights. I still need it for nothing... Actually the camera uses to_track_quat directly. OK, no point_at needed. I'll keep it anyway or remove it.

Let me remove it to keep things clean. Actually I'll keep a small utility.

OK writing the final answer.

Wait, one more: the requirement says "animated over frames 1 to 720 at 24 fps (30 seconds): the motion must fill the whole duration, not finish early and freeze." My linear motion fills the whole duration. ✓

Also "ending on a close-up of the cap" ✓.

Let me write.

Also I should double-check `end_fill_type='NOTHING'` is a valid argument for `primitive_cylinder_add`. Yes: `end_fill_type` enum in ['NOTHING', 'NGON', 'TRIFAN'].

Writing the code now.

For the light energies, let me reconsider. Blender area light energy in Watts. For a 2.5m square light at 4m distance: radiant intensity... The irradiance at the subject ≈ P / (4π d²) for a point-like approximation = 500/(4π*16) = 2.5 W/m². For a Lambertian white surface, radiance = irradiance * albedo/π = 2.5*0.8/3.14 = 0.64. That's a well-exposed value. Good.

Rim at 400W, 4.5m: 400/(4π*20.25) = 1.57. Reflected ~0.4. Good for a rim.

Fill at 120W, 4.2m: 120/(4π*17.6) = 0.54. Reflected ~0.14. Good, subtle.

Backdrop emission adds a bit.

OK, let's go.

Actually, hmm, the key at 500W with size 2.5 at 4m gives a fairly soft, medium exposure. With AgX view transform it will look a bit flat but cinematic. Fine.

Let me bump the key to 800W for more punch. And the rim to 600W.

Alright, final.

One more consideration for the "gold must reflect the studio": with roughness 0.10 and metallic 1, the gold cap will mirror the environment — the area lights will appear as bright rectangles, and the backdrop as a colored gradient. Good.

Let me write it.

Also — I want to make sure the cap doesn't have a hard shadow edge. With an area light of size 2.5, it'll be soft. ✓

Writing.

Actually, one thought on the octagonal body and the "faceted crystal" look: 8 sides gives large flat facets. That's classic. But maybe 10 or 12 would look more like cut crystal. Let's use 10. Hmm, 8 is fine. Let's use 8 for a bold facet look... Actually 6 might be too few. I'll use 8.

Hmm, actually for a perfume bottle, a hexagonal or octagonal shape is common. 8 it is.

Let me finalize.

For the liquid, the cone with 8 vertices — it needs to fit inside the glass with the same facet alignment. Since both are created with default rotation, the facets align. ✓ But the liquid's facets are at the same angle as the glass's. Since the liquid is smaller, it sits inside. Fine.

Actually, the liquid is rotated 22.5° relative to the glass would be better to avoid z-fighting-like coincident facets? No, they're at different radii. Fine.

OK, writing the final script.

Let me handle the `mat_floor` material too.

Final code:

I'll write it out now.

Wait — I should double-check the glass solidify with the cone. A cone primitive with radius1=0.30, radius2=0.24 has an elliptical... no, circular cross-section with 8 vertices → octagon. Solidify offset=-1 pushes inward. Good.

The top and bottom caps: the cone has an ngon top and bottom (8-gon). Solidify will create inner copies. Good.

Alright.

One more: the shoulder cone from 0.24 to 0.085 over 0.06 height. Solidify thickness 0.022 with offset -1. The inner radius at the top would be 0.085-0.022=0.063. OK.

And the neck: cylinder r=0.085, solidify 0.022 → inner 0.063. The neck's top is at 0.62, covered by the cap (0.58-0.69). ✓

Alright, writing.

Let me now produce the final code.

Actually — regarding the empty "LightRig" being rotated: the lights are parented to it. But the Track To constraint targets the "aim" empty which is NOT parented. So the lights will always point at the world position (0,0,0.35). ✓

Good.

Final write-up.

Oh, also: I should make sure the turntable empty and the light rig empty and the aim empty don't render. Empties don't render in Cycles. ✓

OK. Writing the final answer now.