```python
# =============================================================================
#  Luxury Perfume Commercial  -  100% procedural studio scene
#  Target : Blender 4.5 LTS  (bpy / bmesh / mathutils / math only)
#  Run    : blender -b --factory-startup --python this_script.py
#
#  Builds : rotating black-marble pedestal, faceted crystal flacon with amber
#           elixir + polished gold cap, studio key + rim lights, gradient
#           backdrop, camera orbit + dolly-in over frames 1..120 @ 24 fps.
#  Does NOT touch render engine / resolution / samples / output path.
# =============================================================================

import bpy
import bmesh
import math
from mathutils import Vector

# -----------------------------------------------------------------------------
# 1. WIPE THE FACTORY SCENE
# -----------------------------------------------------------------------------
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.lights,
             bpy.data.cameras, bpy.data.curves, bpy.data.node_groups):
    for block in list(coll):
        if block.users == 0:
            coll.remove(block)

for w in list(bpy.data.worlds):
    bpy.data.worlds.remove(w)

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 120
scene.render.fps = 24
scene.render.fps_base = 1.0

COL = scene.collection

# -----------------------------------------------------------------------------
# 2. SMALL HELPERS
# -----------------------------------------------------------------------------
def link(ob):
    COL.objects.link(ob)
    return ob


def lathe(name, profile, sides=8, caps=True, smooth_sides=False):
    """Revolve a (radius, z) profile around Z.  Low 'sides' => faceted solid."""
    bm = bmesh.new()
    rings = []
    for (r, z) in profile:
        ring = []
        for i in range(sides):
            a = 2.0 * math.pi * i / sides
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        rings.append(ring)

    for j in range(len(rings) - 1):
        for i in range(sides):
            k = (i + 1) % sides
            bm.faces.new((rings[j][i], rings[j][k],
                          rings[j + 1][k], rings[j + 1][i]))

    if caps:
        cb = bm.verts.new((0.0, 0.0, profile[0][1]))
        for i in range(sides):
            k = (i + 1) % sides
            bm.faces.new((cb, rings[0][k], rings[0][i]))
        ct = bm.verts.new((0.0, 0.0, profile[-1][1]))
        for i in range(sides):
            k = (i + 1) % sides
            bm.faces.new((ct, rings[-1][i], rings[-1][k]))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.update()

    ob = link(bpy.data.objects.new(name, me))
    if smooth_sides:
        for p in me.polygons:
            if len(p.vertices) == 4:
                p.use_smooth = True
    return ob


def make_material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (520, 0)
    return mat, nt, out


def sset(node, names, value):
    if isinstance(names, str):
        names = [names]
    for n in names:
        if n in node.inputs:
            node.inputs[n].default_value = value
            return True
    return False


def point_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


# -----------------------------------------------------------------------------
# 3. MATERIALS  (all procedural, no textures / no external data)
# -----------------------------------------------------------------------------

# --- 3a. Faceted crystal glass -------------------------------------------------
glass_mat, nt, out = make_material("CrystalGlass")
b = nt.nodes.new("ShaderNodeBsdfPrincipled")
nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
sset(b, "Base Color", (0.94, 0.975, 1.0, 1.0))
sset(b, "Metallic", 0.0)
sset(b, "Roughness", 0.015)
sset(b, "IOR", 1.52)
sset(b, ["Transmission Weight", "Transmission"], 1.0)
sset(b, "Specular IOR Level", 0.5)

# --- 3b. Amber elixir (dielectric + volumetric absorption -> inner glow) -------
liq_mat, nt, out = make_material("AmberElixir")
b = nt.nodes.new("ShaderNodeBsdfPrincipled")
nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
sset(b, "Base Color", (1.0, 0.60, 0.16, 1.0))
sset(b, "Metallic", 0.0)
sset(b, "Roughness", 0.02)
sset(b, "IOR", 1.36)
sset(b, ["Transmission Weight", "Transmission"], 1.0)
vabs = nt.nodes.new("ShaderNodeVolumeAbsorption")
vabs.location = (-200, -260)
vabs.inputs["Color"].default_value = (1.0, 0.52, 0.14, 1.0)
vabs.inputs["Density"].default_value = 4.5
nt.links.new(vabs.outputs["Volume"], out.inputs["Volume"])

# --- 3c. Polished gold ---------------------------------------------------------
gold_mat, nt, out = make_material("PolishedGold")
b = nt.nodes.new("ShaderNodeBsdfPrincipled")
nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
sset(b, "Base Color", (1.0, 0.766, 0.336, 1.0))
sset(b, "Metallic", 1.0)
sset(b, "Roughness", 0.13)
sset(b, "IOR", 1.45)

# --- 3d. Black marble ----------------------------------------------------------
marble_mat, nt, out = make_material("BlackMarble")
b = nt.nodes.new("ShaderNodeBsdfPrincipled")
b.location = (150, 0)
nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
sset(b, "Metallic", 0.0)
sset(b, "Roughness", 0.11)
sset(b, "IOR", 1.5)

tc = nt.nodes.new("ShaderNodeTexCoord");        tc.location = (-950, 0)
nz = nt.nodes.new("ShaderNodeTexNoise");        nz.location = (-700, 0)
nz.inputs["Scale"].default_value = 2.5
nz.inputs["Detail"].default_value = 12.0
nz.inputs["Roughness"].default_value = 0.62
nz.inputs["Distortion"].default_value = 1.7
nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])

ramp = nt.nodes.new("ShaderNodeValToRGB");      ramp.location = (-430, 0)
cr = ramp.color_ramp
cr.interpolation = 'LINEAR'
cr.elements[0].position = 0.30
cr.elements[0].color = (0.008, 0.008, 0.010, 1.0)
cr.elements[1].position = 0.70
cr.elements[1].color = (0.008, 0.008, 0.010, 1.0)
mid = cr.elements.new(0.500)
mid.color = (0.320, 0.300, 0.280, 1.0)
nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])

# --- 3e. Studio floor ----------------------------------------------------------
floor_mat, nt, out = make_material("StudioFloor")
b = nt.nodes.new("ShaderNodeBsdfPrincipled")
nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
sset(b, "Base Color", (0.012, 0.012, 0.014, 1.0))
sset(b, "Metallic", 0.0)
sset(b, "Roughness", 0.09)
sset(b, "IOR", 1.5)

# --- 3f. Gradient backdrop -----------------------------------------------------
back_mat, nt, out = make_material("BackdropGradient")
tcb = nt.nodes.new("ShaderNodeTexCoord");        tcb.location = (-900, 0)
sep = nt.nodes.new("ShaderNodeSeparateXYZ");     sep.location = (-700, 0)
nt.links.new(tcb.outputs["Object"], sep.inputs["Vector"])

mr = nt.nodes.new("ShaderNodeMapRange");         mr.location = (-500, 0)
mr.inputs["From Min"].default_value = -1.0
mr.inputs["From Max"].default_value = 3.0
mr.inputs["To Min"].default_value = 0.0
mr.inputs["To Max"].default_value = 1.0
mr.clamp = True
nt.links.new(sep.outputs["Z"], mr.inputs["Value"])

grmp = nt.nodes.new("ShaderNodeValToRGB");       grmp.location = (-290, 0)
gc = grmp.color_ramp
gc.interpolation = 'LINEAR'
gc.elements[0].position = 0.0
gc.elements[0].color = (0.110, 0.048, 0.016, 1.0)     # warm glow low down
gc.elements[1].position = 1.0
gc.elements[1].color = (0.008, 0.018, 0.050, 1.0)     # deep blue up high
gmid = gc.elements.new(0.45)
gmid.color = (0.045, 0.020, 0.058, 1.0)               # violet mid band
nt.links.new(mr.outputs["Result"], grmp.inputs["Fac"])

emi = nt.nodes.new("ShaderNodeEmission")
emi.location = (-60, 0)
emi.inputs["Strength"].default_value = 1.4
nt.links.new(grmp.outputs["Color"], emi.inputs["Color"])
nt.links.new(emi.outputs["Emission"], out.inputs["Surface"])

# -----------------------------------------------------------------------------
# 4. GEOMETRY
# -----------------------------------------------------------------------------
SIDES = 8          # faceted (cut-crystal) silhouette

# --- 4a. glass body (closed outer shell, solidified inwards) -------------------
glass_profile = [
    (0.420, 0.000),   # base rim
    (0.460, 0.060),   # foot
    (0.460, 0.850),   # straight body
    (0.340, 1.000),   # shoulder
    (0.170, 1.120),   # neck
    (0.170, 1.450),   # neck mouth
]
glass = lathe("Flacon_Glass", glass_profile, sides=SIDES)

bev = glass.modifiers.new("Bevel", 'BEVEL')
bev.width = 0.008
bev.segments = 2
bev.limit_method = 'ANGLE'
bev.angle_limit = math.radians(25.0)

sol = glass.modifiers.new("Solidify", 'SOLIDIFY')
sol.thickness = 0.030
sol.offset = -1.0
sol.use_rim = True
glass.data.materials.append(glass_mat)

# --- 4b. amber liquid ----------------------------------------------------------
liquid_profile = [
    (0.330, 0.038),
    (0.413, 0.100),
    (0.413, 0.680),
    (0.395, 0.760),
    (0.350, 0.790),   # meniscus / flat top surface
]
liquid = lathe("Flacon_Liquid", liquid_profile, sides=SIDES)
liquid.data.materials.append(liq_mat)

# --- 4c. gold cap --------------------------------------------------------------
cap_profile = [
    (0.205, 1.395),
    (0.238, 1.440),
    (0.238, 1.660),
    (0.215, 1.705),
]
cap = lathe("Flacon_Cap", cap_profile, sides=SIDES)
bev2 = cap.modifiers.new("Bevel", 'BEVEL')
bev2.width = 0.006
bev2.segments = 2
bev2.limit_method = 'ANGLE'
bev2.angle_limit = math.radians(25.0)
cap.data.materials.append(gold_mat)

# --- 4d. marble pedestal -------------------------------------------------------
pedestal = lathe("Pedestal", [(0.95, -0.170), (0.95, 0.0)],
                 sides=96, smooth_sides=True)
pedestal.data.materials.append(marble_mat)

# --- 4e. floor -----------------------------------------------------------------
def make_plane(name, size, z):
    s = size * 0.5
    verts = [(-s, -s, z), (s, -s, z), (s, s, z), (-s, s, z)]
    faces = [(0, 1, 2, 3)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    return link(bpy.data.objects.new(name, me))

floor = make_plane("StudioFloor", 40.0, -0.170)
floor.data.materials.append(floor_mat)

# --- 4f. cyclorama backdrop ----------------------------------------------------
backdrop = lathe("Backdrop", [(7.0, -6.0), (7.0, 10.0)],
                 sides=64, caps=False)
backdrop.data.materials.append(back_mat)

# -----------------------------------------------------------------------------
# 5. TURNTABLE (pedestal + flacon rotate slowly together)
# -----------------------------------------------------------------------------
turntable = link(bpy.data.objects.new("Turntable", None))
turntable.location = (0.0, 0.0, 0.0)
turntable.empty_display_size = 0.6

for ob in (pedestal, glass, liquid, cap):
    ob.parent = turntable

turntable.rotation_euler = (0.0, 0.0, 0.0)
turntable.keyframe_insert("rotation_euler", frame=1)
turntable.rotation_euler = (0.0, 0.0, math.radians(24.0))
turntable.keyframe_insert("rotation_euler", frame=120)

# -----------------------------------------------------------------------------
# 6. LIGHTING  (large soft key + slim rim strip, both invisible to camera)
# -----------------------------------------------------------------------------
key_data = bpy.data.lights.new("KeyLight", type='AREA')
key_data.shape = 'RECTANGLE'
key_data.size = 3.2
key_data.size_y = 2.4
key_data.energy = 1400.0
key_data.color = (1.0, 0.965, 0.925)
key = link(bpy.data.objects.new("KeyLight", key_data))
key.location = (-2.8, -3.0, 3.4)
point_at(key, (0.0, 0.0, 0.90))

rim_data = bpy.data.lights.new("RimLight", type='AREA')
rim_data.shape = 'RECTANGLE'
rim_data.size = 0.35
rim_data.size_y = 2.6
rim_data.energy = 700.0
rim_data.color = (0.88, 0.93, 1.0)
rim = link(bpy.data.objects.new("RimLight", rim_data))
rim.location = (2.8, 2.6, 2.4)
point_at(rim, (0.0, 0.0, 1.05))

for lt in (key, rim):
    if hasattr(lt, "visible_camera"):
        lt.visible_camera = False

# -----------------------------------------------------------------------------
# 7. WORLD
# -----------------------------------------------------------------------------
world = bpy.data.worlds.new("StudioWorld")
world.use_nodes = True
scene.world = world
bg = world.node_tree.nodes.get("Background")
if bg is not None:
    bg.inputs[0].default_value = (0.010, 0.011, 0.014, 1.0)
    bg.inputs[1].default_value = 1.0

# -----------------------------------------------------------------------------
# 8. CAMERA  (orbit + gentle dolly-in, lands on the gold cap)
# -----------------------------------------------------------------------------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50.0
cam_data.sensor_fit = 'AUTO'
cam_data.sensor_width = 36.0
cam_data.clip_start = 0.05
cam_data.clip_end = 200.0
cam_data.dof.use_dof = True
cam_data.dof.aperture_f = 16.0
cam_data.dof.aperture_blades = 9
cam_data.dof.aperture_rotation = 0.0

cam = link(bpy.data.objects.new("Camera", cam_data))
cam.rotation_mode = 'XYZ'
scene.camera = cam

focus_target = link(bpy.data.objects.new("FocusTarget", None))
focus_target.empty_display_size = 0.3
cam_data.dof.focus_object = focus_target

# (frame, azimuth deg, radius, height, aim point)
CAM_KEYS = [
    (1,   -32.0, 4.60, 1.05, (0.0, 0.0, 0.83)),
    (60,   -8.0, 2.60, 1.30, (0.0, 0.0, 1.15)),
    (120,  14.0, 1.15, 1.56, (0.0, 0.0, 1.54)),
]

for f, ang_deg, radius, height, tgt in CAM_KEYS:
    a = math.radians(ang_deg)
    cam.location = (radius * math.sin(a), -radius * math.cos(a), height)
    aim = Vector(tgt)
    cam.rotation_euler = (aim - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.keyframe_insert(data_path="location", frame=f)
    cam.keyframe_insert(data_path="rotation_euler", frame=f)

    focus_target.location = aim
    focus_target.keyframe_insert(data_path="location", frame=f)

# -----------------------------------------------------------------------------
# 9. PARK ON FRAME 1
# -----------------------------------------------------------------------------
scene.frame_set(1)
bpy.context.view_layer.update()
```