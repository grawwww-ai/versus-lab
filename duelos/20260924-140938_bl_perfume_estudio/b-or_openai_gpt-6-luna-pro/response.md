```python
import bpy
import math
from mathutils import Vector

# Luxury perfume product studio — Blender 4.5+
# This script builds and animates the scene but deliberately does not render or save.

# ---------------------------------------------------------------------------
# Clean scene
# ---------------------------------------------------------------------------

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.cameras,
                   bpy.data.lights, bpy.data.materials):
    # Remove orphaned data left by the factory scene.
    for datablock in list(datablocks):
        if datablock.users == 0:
            datablocks.remove(datablock)

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 120
scene.render.fps = 24
scene.frame_set(1)

try:
    scene.view_settings.view_transform = 'AgX'
except Exception:
    pass

# ---------------------------------------------------------------------------
# General helpers
# ---------------------------------------------------------------------------

def aim_at(obj, point):
    direction = Vector(point) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

def set_socket(node, names, value):
    for name in names:
        socket = node.inputs.get(name)
        if socket is not None:
            socket.default_value = value
            return

def principled_material(name, base_color, roughness=0.3, metallic=0.0,
                        transmission=0.0, ior=1.45):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = base_color
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()

    output = nodes.new('ShaderNodeOutputMaterial')
    shader = nodes.new('ShaderNodeBsdfPrincipled')
    shader.location = (-240, 0)
    output.location = (40, 0)

    set_socket(shader, ['Base Color'], base_color)
    set_socket(shader, ['Roughness'], roughness)
    set_socket(shader, ['Metallic'], metallic)
    set_socket(shader, ['Transmission Weight', 'Transmission'], transmission)
    set_socket(shader, ['IOR'], ior)
    mat.node_tree.links.new(shader.outputs['BSDF'], output.inputs['Surface'])
    return mat, shader

def add_bevel(obj, width, segments=3, angle_limit=0.1):
    bevel = obj.modifiers.new('Soft precision highlights', 'BEVEL')
    bevel.width = width
    bevel.segments = segments
    bevel.limit_method = 'ANGLE'
    bevel.angle_limit = angle_limit
    bevel.harden_normals = True
    return bevel

def make_cube(name, location, dimensions, material, bevel_width=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if bevel_width:
        add_bevel(obj, bevel_width, 4, 0.12)
    return obj

def add_area_light(name, location, target, power, color, shape='DISK',
                   size=2.0, size_y=None):
    data = bpy.data.lights.new(name, 'AREA')
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

# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------

glass_mat, glass_shader = principled_material(
    'Optical crystal glass', (0.91, 0.97, 1.0, 1.0),
    roughness=0.025, transmission=1.0, ior=1.46
)
set_socket(glass_shader, ['Coat Weight', 'Clearcoat'], 0.18)
set_socket(glass_shader, ['Coat Roughness', 'Clearcoat Roughness'], 0.035)

# A restrained absorption tint gives the glass thickness and edge color.
glass_nodes = glass_mat.node_tree.nodes
glass_links = glass_mat.node_tree.links
glass_output = next(n for n in glass_nodes if n.type == 'OUTPUT_MATERIAL')
absorption = glass_nodes.new('ShaderNodeVolumeAbsorption')
absorption.name = 'Very subtle glass absorption'
absorption.inputs['Color'].default_value = (0.73, 0.88, 0.98, 1.0)
absorption.inputs['Density'].default_value = 0.035
glass_links.new(absorption.outputs['Volume'], glass_output.inputs['Volume'])

gold_mat, gold_shader = principled_material(
    'Polished warm gold', (0.83, 0.48, 0.12, 1.0),
    roughness=0.16, metallic=0.92
)
set_socket(gold_shader, ['Coat Weight', 'Clearcoat'], 0.24)
set_socket(gold_shader, ['Coat Roughness', 'Clearcoat Roughness'], 0.12)

label_mat, _ = principled_material(
    'Midnight enamel label', (0.012, 0.018, 0.027, 1.0),
    roughness=0.24, metallic=0.25
)
ink_gold_mat, _ = principled_material(
    'Lettering gold', (0.92, 0.66, 0.28, 1.0),
    roughness=0.23, metallic=0.82
)

liquid_mat, liquid_shader = principled_material(
    'Amber eau de parfum', (0.8, 0.24, 0.035, 1.0),
    roughness=0.055, transmission=0.78, ior=1.335
)
set_socket(liquid_shader, ['Coat Weight', 'Clearcoat'], 0.12)
set_socket(liquid_shader, ['Emission Color', 'Emission'], (0.55, 0.12, 0.012, 1.0))
set_socket(liquid_shader, ['Emission Strength'], 0.12)
liquid_nodes = liquid_mat.node_tree.nodes
liquid_links = liquid_mat.node_tree.links
liquid_output = next(n for n in liquid_nodes if n.type == 'OUTPUT_MATERIAL')
amber_absorption = liquid_nodes.new('ShaderNodeVolumeAbsorption')
amber_absorption.name = 'Amber depth'
amber_absorption.inputs['Color'].default_value = (0.95, 0.30, 0.045, 1.0)
amber_absorption.inputs['Density'].default_value = 0.48
liquid_links.new(amber_absorption.outputs['Volume'], liquid_output.inputs['Volume'])

# Procedural dark marble with fine, irregular mineral veining.
marble_mat = bpy.data.materials.new('Black marble — procedural veins')
marble_mat.diffuse_color = (0.018, 0.022, 0.029, 1.0)
marble_mat.use_nodes = True
mn = marble_mat.node_tree.nodes
ml = marble_mat.node_tree.links
mn.clear()

marble_out = mn.new('ShaderNodeOutputMaterial')
marble_out.location = (720, 40)
marble_bsdf = mn.new('ShaderNodeBsdfPrincipled')
marble_bsdf.location = (470, 40)
marble_bsdf.inputs['Roughness'].default_value = 0.24
marble_bsdf.inputs['Metallic'].default_value = 0.18
ml.new(marble_bsdf.outputs['BSDF'], marble_out.inputs['Surface'])

texcoord = mn.new('ShaderNodeTexCoord')
texcoord.location = (-800, 100)
noise = mn.new('ShaderNodeTexNoise')
noise.location = (-570, 230)
noise.inputs['Scale'].default_value = 3.2
noise.inputs['Detail'].default_value = 5.0
noise.inputs['Roughness'].default_value = 0.72
noise.inputs['Distortion'].default_value = 2.8
ml.new(texcoord.outputs['Generated'], noise.inputs['Vector'])

base_ramp = mn.new('ShaderNodeValToRGB')
base_ramp.location = (-310, 250)
base_ramp.color_ramp.elements[0].position = 0.22
base_ramp.color_ramp.elements[0].color = (0.004, 0.006, 0.009, 1.0)
base_ramp.color_ramp.elements[1].position = 0.78
base_ramp.color_ramp.elements[1].color = (0.055, 0.068, 0.085, 1.0)
ml.new(noise.outputs['Fac'], base_ramp.inputs['Fac'])

vor = mn.new('ShaderNodeTexVoronoi')
vor.location = (-570, -100)
vor.feature = 'DISTANCE_TO_EDGE'
vor.inputs['Scale'].default_value = 5.0
ml.new(texcoord.outputs['Generated'], vor.inputs['Vector'])

vein_ramp = mn.new('ShaderNodeValToRGB')
vein_ramp.location = (-300, -80)
vein_ramp.color_ramp.elements[0].position = 0.006
vein_ramp.color_ramp.elements[0].color = (0.20, 0.23, 0.27, 1.0)
vein_ramp.color_ramp.elements[1].position = 0.055
vein_ramp.color_ramp.elements[1].color = (0.006, 0.008, 0.011, 1.0)
ml.new(vor.outputs['Distance'], vein_ramp.inputs['Fac'])

marble_mix = mn.new('ShaderNodeMixRGB')
marble_mix.location = (170, 90)
marble_mix.blend_type = 'MULTIPLY'
marble_mix.inputs[0].default_value = 0.65
ml.new(base_ramp.outputs['Color'], marble_mix.inputs[1])
ml.new(vein_ramp.outputs['Color'], marble_mix.inputs[2])
ml.new(marble_mix.outputs['Color'], marble_bsdf.inputs['Base Color'])

# Subtle vertical colored studio gradient, driven by world-space height.
backdrop_mat = bpy.data.materials.new('Studio backdrop — colored gradient')
backdrop_mat.use_nodes = True
bn = backdrop_mat.node_tree.nodes
bl = backdrop_mat.node_tree.links
bn.clear()
back_out = bn.new('ShaderNodeOutputMaterial')
back_out.location = (650, 0)
back_bsdf = bn.new('ShaderNodeBsdfPrincipled')
back_bsdf.location = (400, 0)
back_bsdf.inputs['Roughness'].default_value = 0.92
back_geo = bn.new('ShaderNodeNewGeometry')
back_geo.location = (-650, 0)
back_sep = bn.new('ShaderNodeSeparateXYZ')
back_sep.location = (-440, 0)
bl.new(back_geo.outputs['Position'], back_sep.inputs['Vector'])
back_map = bn.new('ShaderNodeMapRange')
back_map.location = (-240, 0)
back_map.inputs['From Min'].default_value = 0.0
back_map.inputs['From Max'].default_value = 8.0
back_map.inputs['To Min'].default_value = 0.0
back_map.inputs['To Max'].default_value = 1.0
back_map.clamp = True
bl.new(back_sep.outputs['Z'], back_map.inputs['Value'])
back_ramp = bn.new('ShaderNodeValToRGB')
back_ramp.location = (-20, 0)
back_ramp.color_ramp.elements.remove(back_ramp.color_ramp.elements[1])
e0 = back_ramp.color_ramp.elements[0]
e0.position = 0.0
e0.color = (0.018, 0.022, 0.055, 1.0)
e1 = back_ramp.color_ramp.elements.new(0.48)
e1.color = (0.055, 0.032, 0.095, 1.0)
e2 = back_ramp.color_ramp.elements.new(1.0)
e2.color = (0.018, 0.105, 0.13, 1.0)
bl.new(back_map.outputs['Result'], back_ramp.inputs['Fac'])
bl.new(back_ramp.outputs['Color'], back_bsdf.inputs['Base Color'])
set_socket(back_bsdf, ['Emission Color', 'Emission'], (0.025, 0.03, 0.055, 1.0))
set_socket(back_bsdf, ['Emission Strength'], 0.12)
bl.new(back_bsdf.outputs['BSDF'], back_out.inputs['Surface'])

ground_mat, _ = principled_material(
    'Studio floor — charcoal', (0.018, 0.022, 0.031, 1.0),
    roughness=0.52, metallic=0.08
)

# ---------------------------------------------------------------------------
# Seamless studio floor and gradient background
# ---------------------------------------------------------------------------

bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.16))
floor = bpy.context.object
floor.name = 'Matte studio floor'
floor.data.materials.append(ground_mat)

bpy.ops.mesh.primitive_plane_add(
    size=2, location=(0, 5.5, 20), rotation=(math.radians(90), 0, 0)
)
backdrop = bpy.context.object
backdrop.name = 'Large gradient studio backdrop'
backdrop.scale = (100, 20, 1)
backdrop.data.materials.append(backdrop_mat)

# ---------------------------------------------------------------------------
# Animated product turntable and pedestal
# ---------------------------------------------------------------------------

turntable = bpy.data.objects.new('Slow rotating product turntable', None)
bpy.context.collection.objects.link(turntable)
turntable.empty_display_type = 'CIRCLE'
turntable.empty_display_size = 0.4

bpy.ops.mesh.primitive_cylinder_add(
    vertices=128, radius=1.52, depth=0.27, location=(0, 0, -0.015)
)
pedestal = bpy.context.object
pedestal.name = 'Round black marble display pedestal'
pedestal.data.materials.append(marble_mat)
add_bevel(pedestal, 0.065, 5, 0.08)

# Fine gold pinstripe near the pedestal perimeter.
bpy.ops.mesh.primitive_torus_add(
    major_radius=1.435, minor_radius=0.012,
    major_segments=128, minor_segments=12,
    location=(0, 0, 0.092)
)
pedestal_trim = bpy.context.object
pedestal_trim.name = 'Pedestal gold pinstripe'
pedestal_trim.data.materials.append(gold_mat)

# ---------------------------------------------------------------------------
# Faceted, hollow glass bottle shell
# ---------------------------------------------------------------------------

# Clipped-square cross section: broad planar faces with cut crystal corners.
outline = [
    (-0.72, -1.0), (0.72, -1.0), (1.0, -0.72), (1.0, 0.72),
    (0.72, 1.0), (-0.72, 1.0), (-1.0, 0.72), (-1.0, -0.72)
]

def make_shell_mesh(name, outer_rings, inner_rings):
    verts = []
    faces = []
    n = len(outline)

    def append_ring(z, half_x, half_y):
        indices = []
        for x, y in outline:
            indices.append(len(verts))
            verts.append((x * half_x, y * half_y, z))
        return indices

    outer = [append_ring(*r) for r in outer_rings]
    inner = [append_ring(*r) for r in inner_rings]

    # Exterior walls, oriented outward.
    for lower, upper in zip(outer[:-1], outer[1:]):
        for i in range(n):
            j = (i + 1) % n
            faces.append((lower[i], lower[j], upper[j], upper[i]))

    # Interior cavity walls, oriented toward the liquid cavity.
    for lower, upper in zip(inner[:-1], inner[1:]):
        for i in range(n):
            j = (i + 1) % n
            faces.append((lower[i], upper[i], upper[j], lower[j]))

    # Bottle base exterior faces down; cavity bottom faces up.
    faces.append(tuple(reversed(outer[0])))
    faces.append(tuple(inner[0]))

    # Open neck rim bridges the outside and inside walls.
    for i in range(n):
        j = (i + 1) % n
        faces.append((outer[-1][i], outer[-1][j], inner[-1][j], inner[-1][i]))

    mesh = bpy.data.meshes.new(name + ' precision mesh')
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(glass_mat)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    add_bevel(obj, 0.008, 2, 0.18)
    return obj

outer_profile = [
    (0.13, 0.75, 0.43),
    (0.19, 0.75, 0.43),
    (2.02, 0.75, 0.43),
    (2.25, 0.68, 0.39),
    (2.51, 0.34, 0.30),
    (2.59, 0.34, 0.30),
]
inner_profile = [
    (0.25, 0.68, 0.36),
    (0.28, 0.68, 0.36),
    (1.99, 0.68, 0.36),
    (2.20, 0.61, 0.32),
    (2.45, 0.27, 0.23),
    (2.49, 0.27, 0.23),
]
bottle = make_shell_mesh('Faceted hollow crystal-glass bottle',
                         outer_profile, inner_profile)

# ---------------------------------------------------------------------------
# Amber liquid volume, closed at its flat meniscus
# ---------------------------------------------------------------------------

def make_liquid_mesh():
    verts = []
    faces = []
    rings = [
        (0.265, 0.665, 0.345),
        (0.32, 0.665, 0.345),
        (1.68, 0.665, 0.345),
        (1.76, 0.665, 0.345),
    ]
    ring_indices = []
    for z, hx, hy in rings:
        indices = []
        for x, y in outline:
            indices.append(len(verts))
            verts.append((x * hx, y * hy, z))
        ring_indices.append(indices)

    n = len(outline)
    # Closed bottom; side walls; flat top surface.
    faces.append(tuple(reversed(ring_indices[0])))
    for lower, upper in zip(ring_indices[:-1], ring_indices[1:]):
        for i in range(n):
            j = (i + 1) % n
            faces.append((lower[i], lower[j], upper[j], upper[i]))
    faces.append(tuple(ring_indices[-1]))

    mesh = bpy.data.meshes.new('Amber liquid volume mesh')
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(liquid_mat)
    mesh.update()
    obj = bpy.data.objects.new('Glowing amber perfume liquid', mesh)
    bpy.context.collection.objects.link(obj)
    add_bevel(obj, 0.018, 3, 0.15)
    return obj

liquid = make_liquid_mesh()

# ---------------------------------------------------------------------------
# Gold cap and details
# ---------------------------------------------------------------------------

bpy.ops.mesh.primitive_cylinder_add(
    vertices=96, radius=0.375, depth=0.66, location=(0, 0, 2.92)
)
cap = bpy.context.object
cap.name = 'Polished gold cylindrical cap'
cap.data.materials.append(gold_mat)
add_bevel(cap, 0.055, 6, 0.08)

bpy.ops.mesh.primitive_cylinder_add(
    vertices=96, radius=0.386, depth=0.035, location=(0, 0, 2.615)
)
cap_band = bpy.context.object
cap_band.name = 'Gold cap lower collar'
cap_band.data.materials.append(gold_mat)
add_bevel(cap_band, 0.012, 3, 0.08)

bpy.ops.mesh.primitive_cylinder_add(
    vertices=96, radius=0.305, depth=0.018, location=(0, 0, 3.257)
)
cap_top = bpy.context.object
cap_top.name = 'Gold cap top inset'
cap_top.data.materials.append(gold_mat)
add_bevel(cap_top, 0.008, 3, 0.08)

# ---------------------------------------------------------------------------
# Front plaque and understated typography
# ---------------------------------------------------------------------------

plaque_z = 1.26
plaque_back = make_cube(
    'Fine gold plaque surround', (0, -0.438, plaque_z),
    (0.79, 0.034, 0.60), gold_mat, 0.045
)
plaque = make_cube(
    'Midnight enamel front plaque', (0, -0.462, plaque_z),
    (0.725, 0.024, 0.535), label_mat, 0.034
)

def add_front_text(name, body, size, z, material):
    curve = bpy.data.curves.new(name, 'FONT')
    curve.body = body
    curve.align_x = 'CENTER'
    curve.align_y = 'CENTER'
    curve.size = size
    curve.extrude = 0.0008
    curve.bevel_depth = 0.00025
    curve.bevel_resolution = 2
    text = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(text)
    text.location = (0, -0.479, z)
    text.rotation_euler = (math.radians(90), 0, 0)
    text.data.materials.append(material)
    return text

brand = add_front_text('NOCTURNE wordmark', 'NOCTURNE', 0.112, 1.32, ink_gold_mat)
subtitle = add_front_text('PARFUM subtitle', 'PARFUM  •  01', 0.052, 1.19, ink_gold_mat)

# ---------------------------------------------------------------------------
# Parent all rotating product components to the animated turntable
# ---------------------------------------------------------------------------

product_objects = [
    pedestal, pedestal_trim, bottle, liquid, cap, cap_band, cap_top,
    plaque_back, plaque, brand, subtitle
]
for obj in product_objects:
    obj.parent = turntable

for frame, degrees in ((1, 0.0), (120, 22.0)):
    turntable.rotation_euler.z = math.radians(degrees)
    turntable.keyframe_insert(data_path='rotation_euler', frame=frame)

if turntable.animation_data and turntable.animation_data.action:
    for fcurve in turntable.animation_data.action.fcurves:
        for key in fcurve.keyframe_points:
            key.interpolation = 'LINEAR'

# ---------------------------------------------------------------------------
# Studio lighting: soft key, bright glass rims, warm fill and top reflection
# ---------------------------------------------------------------------------

add_area_light(
    'Large soft key — warm white', (-3.8, -4.5, 6.0), (0, 0, 1.55),
    850, (1.0, 0.83, 0.67), 'DISK', 4.0
)
add_area_light(
    'Left crystal rim strip', (-2.6, 1.4, 3.25), (0, 0, 1.55),
    950, (0.58, 0.77, 1.0), 'RECTANGLE', 0.65, 3.8
)
add_area_light(
    'Right crystal rim strip', (2.6, 1.1, 4.1), (0, 0, 1.7),
    1150, (0.60, 0.91, 1.0), 'RECTANGLE', 0.7, 4.0
)
add_area_light(
    'Soft frontal fill', (3.8, -3.0, 2.7), (0, 0, 1.5),
    330, (1.0, 0.73, 0.46), 'DISK', 2.5
)
add_area_light(
    'Overhead cap highlight', (0.2, -0.2, 7.0), (0, 0, 1.8),
    520, (1.0, 0.89, 0.70), 'RECTANGLE', 2.6, 1.4
)

# ---------------------------------------------------------------------------
# World illumination
# ---------------------------------------------------------------------------

world = bpy.data.worlds.new('Dim blue studio world')
scene.world = world
world.use_nodes = True
world_nodes = world.node_tree.nodes
world_links = world.node_tree.links
world_nodes.clear()
world_bg = world_nodes.new('ShaderNodeBackground')
world_bg.inputs['Color'].default_value = (0.055, 0.075, 0.12, 1.0)
world_bg.inputs['Strength'].default_value = 0.22
world_output = world_nodes.new('ShaderNodeOutputWorld')
world_links.new(world_bg.outputs['Background'], world_output.inputs['Surface'])

# ---------------------------------------------------------------------------
# Animated orbiting camera and cap-focused ending
# ---------------------------------------------------------------------------

aim = bpy.data.objects.new('Animated camera look target', None)
bpy.context.collection.objects.link(aim)
aim.empty_display_type = 'SPHERE'
aim.empty_display_size = 0.08

camera_data = bpy.data.cameras.new('Product camera')
camera = bpy.data.objects.new('Orbiting product camera', camera_data)
bpy.context.collection.objects.link(camera)
scene.camera = camera
camera_data.lens = 55
camera_data.sensor_width = 36
camera_data.dof.use_dof = True
camera_data.dof.focus_object = aim
camera_data.dof.aperture_fstop = 8.0

# A wide opening composition eases into a close-up of the cap.
camera_keys = [
    (1,   8.8, math.radians(19.0), 3.55, 1.62),
    (60,  5.6, math.radians(2.0),  3.80, 2.25),
    (120, 2.62, math.radians(-23.0), 3.65, 3.12),
]
for frame, radius, angle, camera_z, target_z in camera_keys:
    camera.location = (radius * math.sin(angle),
                       -radius * math.cos(angle),
                       camera_z)
    camera.keyframe_insert(data_path='location', frame=frame)
    aim.location = (0, 0, target_z)
    aim.keyframe_insert(data_path='location', frame=frame)

track = camera.constraints.new(type='TRACK_TO')
track.name = 'Keep the fragrance in frame'
track.target = aim
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'

for animated_obj in (camera, aim):
    if animated_obj.animation_data and animated_obj.animation_data.action:
        for fcurve in animated_obj.animation_data.action.fcurves:
            for key in fcurve.keyframe_points:
                key.interpolation = 'BEZIER'
                key.handle_left_type = 'AUTO'
                key.handle_right_type = 'AUTO'

scene.frame_set(1)
```