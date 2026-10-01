# =====================================================================
#  LUXURY PERFUME COMMERCIAL  --  Blender 4.5 LTS
#  Run with:  blender -b --factory-startup --python this_script.py
# =====================================================================
import bpy
import math
from mathutils import Vector

# ---------------------------------------------------------------------
# 0.  WIPE THE FACTORY SCENE
# ---------------------------------------------------------------------
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
scene.frame_end   = 720
scene.render.fps  = 24

# ---------------------------------------------------------------------
# 1.  SMALL HELPERS
# ---------------------------------------------------------------------
def si(node, name, value):
    """Set a node input by name, silently ignoring missing sockets."""
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

# ---------------------------------------------------------------------
# 2.  MATERIALS
# ---------------------------------------------------------------------

# ---- faceted crystal glass ------------------------------------------
mat_glass, nt, b = new_material("CrystalGlass")
si(b, "Base Color",         (1.0, 1.0, 1.0, 1.0))
si(b, "Metallic",           0.0)
si(b, "Roughness",          0.015)
si(b, "IOR",                1.52)
si(b, "Transmission Weight", 1.0)
si(b, "Transmission",       1.0)          # pre-4.0 name fallback
si(b, "Specular IOR Level", 0.5)

# ---- amber perfume liquid -------------------------------------------
mat_liquid, nt, b = new_material("AmberLiquid")
si(b, "Base Color",         (0.72, 0.28, 0.030, 1.0))
si(b, "Metallic",           0.0)
si(b, "Roughness",          0.0)
si(b, "IOR",                1.45)
si(b, "Transmission Weight", 1.0)
si(b, "Transmission",       1.0)

# ---- polished gold ---------------------------------------------------
mat_gold, nt, b = new_material("PolishedGold")
si(b, "Base Color", (1.00, 0.72, 0.29, 1.0))
si(b, "Metallic",   1.0)
si(b, "Roughness",  0.09)

# ---- black marble (procedural veining) -------------------------------
mat_marble, nt, b = new_material("BlackMarble")
tc  = nt.nodes.new("ShaderNodeTexCoord")
mp  = nt.nodes.new("ShaderNodeMapping")
si(mp, "Scale", (1.0, 1.0, 2.6))
nz  = nt.nodes.new("ShaderNodeTexNoise")
si(nz, "Scale",      3.0)
si(nz, "Detail",     10.0)
si(nz, "Roughness",  0.62)
ramp = nt.nodes.new("ShaderNodeValToRGB")
cr = ramp.color_ramp
for i in range(len(cr.elements) - 1, 0, -1):
    cr.elements.remove(cr.elements[i])
cr.elements[0].position = 0.0
cr.elements[0].color    = (0.004, 0.004, 0.006, 1.0)
for pos, col in ((0.440, (0.004, 0.004, 0.006, 1.0)),
                 (0.487, (0.270, 0.280, 0.320, 1.0)),
                 (0.532, (0.004, 0.004, 0.006, 1.0)),
                 (1.000, (0.004, 0.004, 0.006, 1.0))):
    e = cr.elements.new(pos)
    e.color = col
nt.links.new(tc.outputs["Object"],  mp.inputs["Vector"])
nt.links.new(mp.outputs["Vector"],  nz.inputs["Vector"])
nt.links.new(nz.outputs["Fac"],     ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
si(b, "Metallic",   0.0)
si(b, "Roughness",  0.13)
si(b, "Specular IOR Level", 0.6)

# ---- studio floor ----------------------------------------------------
mat_floor, nt, b = new_material("StudioFloor")
si(b, "Base Color", (0.020, 0.021, 0.025, 1.0))
si(b, "Metallic",   0.0)
si(b, "Roughness",  0.38)

# ---- backdrop (emissive gradient) ------------------------------------
mat_backdrop, nt, b = new_material("BackdropGradient")
tc2 = nt.nodes.new("ShaderNodeTexCoord")
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
ramp2 = nt.nodes.new("ShaderNodeValToRGB")
cr2 = ramp2.color_ramp
for i in range(len(cr2.elements) - 1, 0, -1):
    cr2.elements.remove(cr2.elements[i])
cr2.elements[0].position = 0.0
cr2.elements[0].color    = (0.010, 0.025, 0.040, 1.0)
for pos, col in ((0.250, (0.040, 0.110, 0.160, 1.0)),
                 (0.340, (0.080, 0.180, 0.230, 1.0)),
                 (0.520, (0.130, 0.055, 0.130, 1.0)),
                 (1.000, (0.012, 0.008, 0.022, 1.0))):
    e = cr2.elements.new(pos)
    e.color = col
nt.links.new(tc2.outputs["Generated"], sep.inputs["Vector"])
nt.links.new(sep.outputs["Z"],         ramp2.inputs["Fac"])
si(b, "Base Color",       (0.0, 0.0, 0.0, 1.0))
si(b, "Roughness",        1.0)
si(b, "Metallic",         0.0)
si(b, "Emission Strength", 0.8)
# route the ramp into the emission colour (works for 4.x name & fallback)
if "Emission Color" in b.inputs:
    nt.links.new(ramp2.outputs["Color"], b.inputs["Emission Color"])
elif "Emission" in b.inputs:
    nt.links.new(ramp2.outputs["Color"], b.inputs["Emission"])

# ---------------------------------------------------------------------
# 3.  WORLD
# ---------------------------------------------------------------------
world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.014, 0.016, 0.021, 1.0)
    bg.inputs[1].default_value = 1.0

# ---------------------------------------------------------------------
# 4.  TURNTABLE (everything that spins sits under this empty)
# ---------------------------------------------------------------------
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0.0, 0.0, 0.0))
turntable = bpy.context.active_object
turntable.name = "Turntable"
turntable.rotation_mode = 'XYZ'

# ---- pedestal --------------------------------------------------------
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=0.60, depth=0.16,
                                    location=(0.0, 0.0, -0.08))
pedestal = bpy.context.active_object
pedestal.name = "Pedestal"
bev = pedestal.modifiers.new("Bevel", 'BEVEL')
bev.width = 0.008
bev.segments = 4
bev.limit_method = 'ANGLE'
assign(pedestal, mat_marble)
pedestal.parent = turntable

# ---------------------------------------------------------------------
# 5.  THE PERFUME BOTTLE
# ---------------------------------------------------------------------
# ---- faceted glass body ---------------------------------------------
bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.30, radius2=0.24,
                                depth=0.50, location=(0.0, 0.0, 0.25))
body = bpy.context.active_object
body.name = "Bottle_Body"
m = body.modifiers.new("Solidify", 'SOLIDIFY')
m.thickness = 0.022
m.offset = -1.0
m.use_even_offset = True
m.use_rim = True
m2 = body.modifiers.new("Bevel", 'BEVEL')
m2.width = 0.003
m2.segments = 2
m2.limit_method = 'ANGLE'
assign(body, mat_glass)
body.parent = turntable

# ---- shoulder --------------------------------------------------------
bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.24, radius2=0.085,
                                depth=0.06, location=(0.0, 0.0, 0.53))
shoulder = bpy.context.active_object
shoulder.name = "Bottle_Shoulder"
m = shoulder.modifiers.new("Solidify", 'SOLIDIFY')
m.thickness = 0.020
m.offset = -1.0
m.use_even_offset = True
assign(shoulder, mat_glass)
shoulder.parent = turntable

# ---- neck ------------------------------------------------------------
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.085, depth=0.08,
                                    location=(0.0, 0.0, 0.58))
neck = bpy.context.active_object
neck.name = "Bottle_Neck"
m = neck.modifiers.new("Solidify", 'SOLIDIFY')
m.thickness = 0.020
m.offset = -1.0
m.use_even_offset = True
assign(neck, mat_glass)
neck.parent = turntable

# ---- amber liquid ----------------------------------------------------
bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.265, radius2=0.205,
                                depth=0.36, location=(0.0, 0.0, 0.21))
liquid = bpy.context.active_object
liquid.name = "Bottle_Liquid"
assign(liquid, mat_liquid)
liquid.parent = turntable

# ---- gold cap --------------------------------------------------------
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.135, depth=0.11,
                                    location=(0.0, 0.0, 0.635))
cap = bpy.context.active_object
cap.name = "Bottle_Cap"
bev2 = cap.modifiers.new("Bevel", 'BEVEL')
bev2.width = 0.010
bev2.segments = 4
bev2.limit_method = 'ANGLE'
assign(cap, mat_gold)
cap.parent = turntable

# ---------------------------------------------------------------------
# 6.  STUDIO SHELL : floor + curved backdrop
# ---------------------------------------------------------------------
bpy.ops.mesh.primitive_plane_add(size=18.0, location=(0.0, 0.0, -0.16))
floor = bpy.context.active_object
floor.name = "Floor"
assign(floor, mat_floor)

bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=9.0, depth=16.0,
                                    location=(0.0, 0.0, 3.0),
                                    end_fill_type='NOTHING')
backdrop = bpy.context.active_object
backdrop.name = "Backdrop"
assign(backdrop, mat_backdrop)

# ---------------------------------------------------------------------
# 7.  LIGHTING RIG  (rotates with the camera -> consistent studio look)
# ---------------------------------------------------------------------
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0.0, 0.0, 0.0))
light_rig = bpy.context.active_object
light_rig.name = "LightRig"
light_rig.rotation_mode = 'XYZ'

bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0.0, 0.0, 0.35))
aim = bpy.context.active_object
aim.name = "AimTarget"

def make_area(name, loc, energy, size, color=(1.0, 1.0, 1.0)):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = energy
    ld.size   = size
    ld.color  = color
    ob = bpy.data.objects.new(name, ld)
    scene.collection.objects.link(ob)
    ob.location = loc
    ob.parent = light_rig
    con = ob.constraints.new('TRACK_TO')
    con.target      = aim
    con.track_axis  = 'TRACK_NEGATIVE_Z'
    con.up_axis     = 'UP_Y'
    return ob

# positions are given for camera azimuth = -80 deg (frame 1)
# key   -> +45 deg from camera, high and large (soft)
# fill  -> -55 deg from camera, large and dim
# rim   -> +165 deg from camera, tight and bright (etches the glass edges)
key  = make_area("KeyLight",  (-2.180, -3.113, 3.05), 800.0, 2.60, (1.00, 0.97, 0.93))
fill = make_area("FillLight", (-2.970,  2.970, 1.40), 140.0, 3.60, (0.82, 0.88, 1.00))
rim  = make_area("RimLight",  ( 4.483, -0.392, 1.85), 620.0, 1.20, (0.90, 0.95, 1.00))

# ---------------------------------------------------------------------
# 8.  CAMERA
# ---------------------------------------------------------------------
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50.0
cam = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
cam.rotation_mode = 'XYZ'

# ---------------------------------------------------------------------
# 9.  ANIMATION  (frames 1 .. 720, linear, fills the entire duration)
# ---------------------------------------------------------------------
FRAMES   = 720
AZ_START = -80.0        # degrees
AZ_END   = 120.0        # 200 deg orbit
R_START  = 2.90
R_END    = 0.75
Z_START  = 1.05
Z_END    = 0.72
TZ_START = 0.26         # look-at height
TZ_END   = 0.65         # ends on the gold cap

for f in range(1, FRAMES + 1):
    t = (f - 1) / float(FRAMES - 1)

    az_deg = AZ_START + (AZ_END - AZ_START) * t
    az     = math.radians(az_deg)
    radius = R_START + (R_END - R_START) * t
    cz     = Z_START + (Z_END - Z_START) * t
    tz     = TZ_START + (TZ_END - TZ_START) * t

    cx = radius * math.sin(az)
    cy = -radius * math.cos(az)
    cam.location = (cx, cy, cz)

    direction = Vector((0.0, 0.0, tz)) - Vector((cx, cy, cz))
    if direction.length > 1e-6:
        cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

    cam.keyframe_insert("location",       frame=f)
    cam.keyframe_insert("rotation_euler", frame=f)

    # lights follow the camera azimuth -> stable, repeatable studio look
    light_rig.rotation_euler = (0.0, 0.0, az - math.radians(AZ_START))
    light_rig.keyframe_insert("rotation_euler", frame=f)

    # pedestal + bottle drift slowly around: one full turn over 30 s
    turntable.rotation_euler = (0.0, 0.0, 2.0 * math.pi * t)
    turntable.keyframe_insert("rotation_euler", frame=f)

# make every curve perfectly linear so the motion never stalls or overshoots
for ob in (cam, light_rig, turntable):
    ad = ob.animation_data
    if not ad:
        continue
    act = ad.action
    if not act:
        continue
    fcurves = getattr(act, "fcurves", None)
    if fcurves is None:
        # Blender 4.4+ slotted actions
        fcurves = []
        for layer in getattr(act, "layers", []):
            for strip in getattr(layer, "strips", []):
                for cbag in getattr(strip, "channelbags", []):
                    fcurves.extend(cbag.fcurves)
    for fc in fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'

scene.frame_set(1)