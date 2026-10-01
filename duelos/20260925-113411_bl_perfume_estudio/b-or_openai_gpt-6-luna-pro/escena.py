import bpy
import math
from mathutils import Vector

# Luxury perfume studio scene — Blender 4.5 LTS
# Everything is generated procedurally; no rendering or file saving is performed.

# -------------------------------------------------------------------
# Clear the factory scene
# -------------------------------------------------------------------

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                   bpy.data.cameras, bpy.data.lights):
    # Leave cleanup to Blender's normal orphan handling; the scene starts empty.
    pass

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 720
scene.render.fps = 24


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def principled_material(name, color, roughness=0.3, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def make_mesh_object(name, verts, faces, material=None):
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    if material:
        obj.data.materials.append(material)
    return obj


def lathe_mesh(name, profile, sides=16, material=None, close_profile=False,
               smooth=False, phase=0.0):
    """Create a rotational mesh from (radius, z) profile entries."""
    verts = []
    for radius, z in profile:
        for j in range(sides):
            a = 2.0 * math.pi * j / sides + phase
            verts.append((radius * math.cos(a), radius * math.sin(a), z))

    faces = []
    ring_count = len(profile)
    section_count = ring_count if close_profile else ring_count - 1
    for i in range(section_count):
        ni = (i + 1) % ring_count
        for j in range(sides):
            nj = (j + 1) % sides
            faces.append((
                i * sides + j,
                i * sides + nj,
                ni * sides + nj,
                ni * sides + j,
            ))

    obj = make_mesh_object(name, verts, faces, material)
    if smooth:
        for poly in obj.data.polygons:
            poly.use_smooth = True
    return obj


def capped_lathe(name, profile, sides=32, material=None, smooth=True):
    """A closed solid of revolution with polygon end caps."""
    verts = []
    for radius, z in profile:
        for j in range(sides):
            a = 2.0 * math.pi * j / sides
            verts.append((radius * math.cos(a), radius * math.sin(a), z))

    faces = []
    for i in range(len(profile) - 1):
        for j in range(sides):
            nj = (j + 1) % sides
            faces.append((
                i * sides + j,
                i * sides + nj,
                (i + 1) * sides + nj,
                (i + 1) * sides + j,
            ))

    faces.append(tuple(reversed(range(sides))))
    top = (len(profile) - 1) * sides
    faces.append(tuple(top + j for j in range(sides)))

    obj = make_mesh_object(name, verts, faces, material)
    if smooth:
        for poly in obj.data.polygons:
            poly.use_smooth = True
    return obj


def make_torus(name, major_radius, minor_radius, z, material,
               major_segments=96, minor_segments=12):
    verts = []
    faces = []
    for i in range(major_segments):
        a = 2.0 * math.pi * i / major_segments
        ca, sa = math.cos(a), math.sin(a)
        for j in range(minor_segments):
            b = 2.0 * math.pi * j / minor_segments
            r = major_radius + minor_radius * math.cos(b)
            verts.append((r * ca, r * sa, z + minor_radius * math.sin(b)))
    for i in range(major_segments):
        ni = (i + 1) % major_segments
        for j in range(minor_segments):
            nj = (j + 1) % minor_segments
            faces.append((
                i * minor_segments + j,
                ni * minor_segments + j,
                ni * minor_segments + nj,
                i * minor_segments + nj,
            ))
    obj = make_mesh_object(name, verts, faces, material)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def animate_linear(obj):
    """Set generated keyframes to linear interpolation where the API exposes curves."""
    try:
        action = obj.animation_data.action
        for curve in action.fcurves:
            for point in curve.keyframe_points:
                point.interpolation = 'LINEAR'
    except (AttributeError, TypeError):
        pass


def aim_at(obj, point):
    direction = Vector(point) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


# -------------------------------------------------------------------
# Materials
# -------------------------------------------------------------------

gold = principled_material("Polished warm gold", (0.72, 0.40, 0.105),
                           roughness=0.17, metallic=0.88)
gold_dark = principled_material("Deep gold detail", (0.28, 0.12, 0.025),
                                roughness=0.23, metallic=0.82)

glass = bpy.data.materials.new("Clear faceted crystal glass")
glass.diffuse_color = (0.80, 0.91, 1.0, 0.22)
glass.use_nodes = True
glass_nodes = glass.node_tree.nodes
glass_links = glass.node_tree.links
glass_bsdf = glass_nodes.get("Principled BSDF")
glass_bsdf.inputs["Base Color"].default_value = (0.82, 0.93, 1.0, 1.0)
glass_bsdf.inputs["Roughness"].default_value = 0.035
glass_bsdf.inputs["IOR"].default_value = 1.46
glass_bsdf.inputs["Transmission Weight"].default_value = 1.0
glass_absorb = glass_nodes.new("ShaderNodeVolumeAbsorption")
glass_absorb.inputs["Color"].default_value = (0.80, 0.91, 1.0, 1.0)
glass_absorb.inputs["Density"].default_value = 0.035
glass_links.new(glass_absorb.outputs["Volume"],
                glass_nodes.get("Material Output").inputs["Volume"])

amber = bpy.data.materials.new("Amber parfum")
amber.diffuse_color = (0.72, 0.22, 0.025, 1.0)
amber.use_nodes = True
amber_nodes = amber.node_tree.nodes
amber_links = amber.node_tree.links
amber_bsdf = amber_nodes.get("Principled BSDF")
amber_bsdf.inputs["Base Color"].default_value = (0.80, 0.28, 0.035, 1.0)
amber_bsdf.inputs["Roughness"].default_value = 0.10
amber_bsdf.inputs["IOR"].default_value = 1.335
amber_bsdf.inputs["Transmission Weight"].default_value = 0.72
amber_absorb = amber_nodes.new("ShaderNodeVolumeAbsorption")
amber_absorb.inputs["Color"].default_value = (0.94, 0.33, 0.045, 1.0)
amber_absorb.inputs["Density"].default_value = 0.50
amber_links.new(amber_absorb.outputs["Volume"],
                amber_nodes.get("Material Output").inputs["Volume"])

# Procedural black marble for the rotating display.
marble = bpy.data.materials.new("Black marble pedestal")
marble.use_nodes = True
mn = marble.node_tree.nodes
ml = marble.node_tree.links
mbsdf = mn.get("Principled BSDF")
mbsdf.inputs["Roughness"].default_value = 0.23
noise = mn.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 3.6
noise.inputs["Detail"].default_value = 5.0
noise.inputs["Roughness"].default_value = 0.72
noise.inputs["Distortion"].default_value = 2.0
ramp = mn.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.25
ramp.color_ramp.elements[0].color = (0.006, 0.008, 0.014, 1.0)
ramp.color_ramp.elements[1].position = 0.68
ramp.color_ramp.elements[1].color = (0.075, 0.085, 0.11, 1.0)
ml.new(noise.outputs["Fac"], ramp.inputs["Fac"])
ml.new(ramp.outputs["Color"], mbsdf.inputs["Base Color"])
bump = mn.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.12
bump.inputs["Distance"].default_value = 0.035
ml.new(noise.outputs["Fac"], bump.inputs["Height"])
ml.new(bump.outputs["Normal"], mbsdf.inputs["Normal"])

floor_mat = principled_material("Studio floor", (0.018, 0.022, 0.035),
                                roughness=0.32)

# A vertical procedural color gradient on the surrounding studio wall.
backdrop = bpy.data.materials.new("Midnight plum gradient backdrop")
backdrop.use_nodes = True
bn = backdrop.node_tree.nodes
bl = backdrop.node_tree.links
bbsdf = bn.get("Principled BSDF")
bbsdf.inputs["Roughness"].default_value = 0.72
texcoord = bn.new("ShaderNodeTexCoord")
separate = bn.new("ShaderNodeSeparateXYZ")
bl.new(texcoord.outputs["Generated"], separate.inputs["Vector"])
gradient = bn.new("ShaderNodeValToRGB")
gradient.color_ramp.elements[0].position = 0.0
gradient.color_ramp.elements[0].color = (0.012, 0.018, 0.045, 1.0)
gradient.color_ramp.elements[1].position = 1.0
gradient.color_ramp.elements[1].color = (0.11, 0.035, 0.095, 1.0)
mid = gradient.color_ramp.elements.new(0.48)
mid.color = (0.035, 0.045, 0.095, 1.0)
bl.new(separate.outputs["Z"], gradient.inputs["Fac"])
bl.new(gradient.outputs["Color"], bbsdf.inputs["Base Color"])


# -------------------------------------------------------------------
# Rotating black marble pedestal
# -------------------------------------------------------------------

pedestal_top = 0.34
pedestal = bpy.data.objects.new("Slowly rotating marble display", None)
bpy.context.collection.objects.link(pedestal)

bpy.ops.mesh.primitive_cylinder_add(
    vertices=96, radius=1.43, depth=0.34, location=(0.0, 0.0, 0.17))
plinth = bpy.context.object
plinth.name = "Round black marble plinth"
plinth.data.materials.append(marble)
bevel = plinth.modifiers.new("Soft machined edge", "BEVEL")
bevel.width = 0.055
bevel.segments = 4
normal = plinth.modifiers.new("Weighted reflections", "WEIGHTED_NORMAL")
normal.keep_sharp = True
plinth.parent = pedestal

inlay = make_torus("Fine gold perimeter inlay", 1.25, 0.012, pedestal_top + 0.006,
                   gold, major_segments=128, minor_segments=10)
inlay.parent = pedestal

pedestal.rotation_euler[2] = 0.0
pedestal.keyframe_insert(data_path="rotation_euler", frame=1, index=2)
pedestal.rotation_euler[2] = 2.0 * math.pi
pedestal.keyframe_insert(data_path="rotation_euler", frame=720, index=2)
animate_linear(pedestal)


# -------------------------------------------------------------------
# Crystal bottle body and amber liquid
# -------------------------------------------------------------------

bottle_base_z = pedestal_top

# One continuous faceted shell profile: outside rises to the mouth, then
# returns down the inside to form the thick rim and bottle cavity.
bottle_profile = [
    (0.66, 0.04),
    (0.77, 0.06),
    (0.84, 0.16),
    (0.86, 0.30),
    (0.86, 1.72),
    (0.83, 1.91),
    (0.68, 2.11),
    (0.44, 2.34),
    (0.37, 2.43),
    (0.37, 2.76),
    (0.35, 2.82),
    (0.29, 2.82),
    (0.28, 2.77),
    (0.28, 2.43),
    (0.38, 2.31),
    (0.59, 2.07),
    (0.71, 1.82),
    (0.71, 0.36),
    (0.66, 0.22),
]
bottle = lathe_mesh("Faceted crystal perfume bottle", bottle_profile,
                    sides=12, material=glass, close_profile=True,
                    smooth=False, phase=math.radians(15))
bottle.location.z = bottle_base_z

liquid_profile = [
    (0.62, 0.24),
    (0.67, 0.32),
    (0.67, 1.44),
    (0.66, 1.54),
    (0.60, 1.61),
    (0.43, 1.66),
    (0.20, 1.685),
    (0.02, 1.69),
]
liquid = capped_lathe("Glowing amber perfume fill", liquid_profile,
                      sides=48, material=amber, smooth=True)
liquid.location.z = bottle_base_z

# A precisely turned gold cap with small stepped details at its edges.
cap_profile = [
    (0.355, 2.70),
    (0.405, 2.73),
    (0.425, 2.77),
    (0.425, 2.82),
    (0.412, 2.84),
    (0.412, 3.34),
    (0.428, 3.37),
    (0.428, 3.41),
    (0.395, 3.47),
    (0.36, 3.49),
]
cap = capped_lathe("Polished gold perfume cap", cap_profile,
                   sides=48, material=gold, smooth=True)
cap.location.z = bottle_base_z

cap_band_a = make_torus("Cap lower gold pinstripe", 0.418, 0.009,
                        bottle_base_z + 2.86, gold_dark)
cap_band_a.parent = cap
cap_band_b = make_torus("Cap crown gold pinstripe", 0.417, 0.008,
                        bottle_base_z + 3.36, gold_dark)
cap_band_b.parent = cap


# -------------------------------------------------------------------
# Seamless studio cyclorama and floor
# -------------------------------------------------------------------

# Broad dark floor.
floor_verts = [
    (-18.0, -18.0, -0.015),
    ( 18.0, -18.0, -0.015),
    ( 18.0,  18.0, -0.015),
    (-18.0,  18.0, -0.015),
]
floor = make_mesh_object("Matte studio floor", floor_verts, [(0, 1, 2, 3)], floor_mat)

# 360-degree surrounding wall, large enough to stay in view during the orbit.
wall_profile = [(14.0, -0.02), (14.0, 9.0)]
wall = lathe_mesh("Curved studio backdrop", wall_profile, sides=128,
                  material=backdrop, close_profile=False, smooth=True)


# -------------------------------------------------------------------
# Studio lighting
# -------------------------------------------------------------------

def area_light(name, location, target, power, color, size, shape='DISK',
               size_y=None):
    data = bpy.data.lights.new(name, type='AREA')
    data.energy = power
    data.color = color
    data.shape = shape
    data.size = size
    if shape == 'RECTANGLE' and size_y is not None:
        data.size_y = size_y
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    aim_at(obj, target)
    return obj


area_light("Large soft key", (-4.2, -4.8, 6.3), (0.0, 0.0, 1.8),
           1050, (1.0, 0.82, 0.64), 4.2)
area_light("Cool glass rim light", (2.0, 3.3, 5.3), (0.0, 0.0, 1.9),
           1450, (0.48, 0.70, 1.0), 2.6)
area_light("Tall front reflection strip", (-3.4, -0.6, 3.5), (0.0, 0.0, 1.8),
           600, (1.0, 0.91, 0.76), 1.0, shape='RECTANGLE', size_y=4.5)
area_light("Soft frontal fill", (4.2, -3.2, 3.2), (0.0, 0.0, 1.8),
           420, (0.72, 0.80, 1.0), 3.0)
area_light("Top cap glint", (0.0, 0.2, 7.0), (0.0, 0.0, 2.2),
           500, (1.0, 0.78, 0.48), 2.1)

world = bpy.data.worlds.new("Deep blue studio ambience") if not bpy.data.worlds else bpy.data.worlds[0]
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.018, 0.025, 0.055, 1.0)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.22


# -------------------------------------------------------------------
# Animated camera: a slow orbit and continuous push-in to the cap
# -------------------------------------------------------------------

camera_data = bpy.data.cameras.new("Luxury product camera")
camera = bpy.data.objects.new("Luxury product camera", camera_data)
bpy.context.collection.objects.link(camera)
scene.camera = camera
camera_data.lens = 52.0
camera_data.clip_start = 0.05
camera_data.clip_end = 100.0

target = bpy.data.objects.new("Animated camera look target", None)
bpy.context.collection.objects.link(target)
target.empty_display_type = 'SPHERE'
target.empty_display_size = 0.08

# The path keeps changing all the way through frame 720. The changing
# target gradually raises the composition from the bottle to the cap.
camera_keys = [
    (1,   8.8, math.radians(-72), 1.82, 52.0),
    (145, 7.6, math.radians(-48), 1.96, 54.0),
    (289, 6.3, math.radians(-22), 2.20, 57.0),
    (433, 5.0, math.radians(  5), 2.62, 61.0),
    (577, 3.8, math.radians( 27), 3.08, 66.0),
    (720, 2.75, math.radians( 48), bottle_base_z + 3.47, 70.0),
]

for frame, distance, angle, target_z, lens in camera_keys:
    target.location = (0.0, 0.0, target_z)
    target.keyframe_insert(data_path="location", frame=frame)

    # Slightly elevated product-camera angle, orbiting around the bottle.
    camera.location = (
        distance * math.cos(angle),
        distance * math.sin(angle),
        target_z + 0.28 + 0.035 * distance,
    )
    camera.keyframe_insert(data_path="location", frame=frame)

    camera_data.lens = lens
    camera_data.keyframe_insert(data_path="lens", frame=frame)

track = camera.constraints.new(type='TRACK_TO')
track.name = "Keep the perfume in frame"
track.target = target
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'

animate_linear(camera)
animate_linear(camera_data)
animate_linear(target)

scene.frame_set(1)