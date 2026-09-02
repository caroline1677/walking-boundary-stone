"""Build the 界碑爷爷 (Grandpa Boundary Stone) character GLB.

Run via Blender CLI:
  blender --background --python tools/build_grandpa.py

A friendly personified boundary marker: 7-sided standing stone slab body with
a flat face toward -Y, carved kind face, bamboo hat, red scarf, walking stick.
Origin at ground center, ~1.5 m tall, front faces -Y.
"""

from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

OUTPUT = Path(r"D:\HKU-ds\QCH\界碑智能体\assets\models\grandpa-boundary.glb")
PREVIEW_DIR = Path(r"D:\HKU-ds\QCH\界碑智能体\tools\renders")

STONE = (0.58, 0.62, 0.58, 1.0)
STONE_DARK = (0.4, 0.45, 0.41, 1.0)
STONE_LIGHT = (0.82, 0.82, 0.78, 1.0)
STRAW = (0.8, 0.66, 0.38, 1.0)
RED = (0.72, 0.16, 0.12, 1.0)
WOOD = (0.45, 0.32, 0.2, 1.0)
EYE = (0.12, 0.1, 0.09, 1.0)

# Heptagon: 7 sides. With rotation Z = 90°, a flat side faces -Y (270°).
SIDE_COUNT = 7
FACE_ROTATION_Z = 1.5707963
LEAD_X = 0.05  # slight forward lean
FACE_Y = -0.33


def make_material(name, color, roughness=0.85):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def link(obj):
    bpy.context.collection.objects.link(obj)
    return obj


def primitive(name, build, location, material, rotation=(0, 0, 0), scale=(1, 1, 1)):
    data = bpy.data.meshes.new(name)
    bm = bmesh.new()
    build(bm)
    bm.to_mesh(data)
    bm.free()
    obj = bpy.data.objects.new(name, data)
    obj.location = location
    obj.rotation_euler = rotation
    obj.scale = scale
    link(obj)
    data.materials.append(material)
    return obj


def cone(bm, radius1, radius2, depth, segments=24):
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=radius1, radius2=radius2, depth=depth)


def sphere(bm, radius, segments=20, rings=12):
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius)


def cube(bm, size):
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Diagonal((size[0], size[1], size[2], 1.0)))


def soften(obj, width=0.02, segments=3):
    modifier = obj.modifiers.new("Soften", "BEVEL")
    modifier.width = width
    modifier.segments = segments
    modifier.limit_method = "ANGLE"
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True


bpy.ops.wm.read_factory_settings(use_empty=True)

mat_stone = make_material("Stone", STONE)
mat_stone_dark = make_material("StoneDark", STONE_DARK)
mat_stone_light = make_material("StoneLight", STONE_LIGHT)
mat_straw = make_material("Straw", STRAW, roughness=0.7)
mat_red = make_material("ScarfRed", RED, roughness=0.65)
mat_wood = make_material("Wood", WOOD, roughness=0.8)
mat_eye = make_material("Eye", EYE, roughness=0.35)

parts = []
body_rotation = (LEAD_X, 0.0, FACE_ROTATION_Z)

# Grounding base rock.
base = primitive("Base", lambda bm: cone(bm, 0.4, 0.34, 0.14, SIDE_COUNT), (0, 0, 0.07), mat_stone_dark, body_rotation)
soften(base, width=0.03)
parts.append(base)

# Body: tapered 7-sided slab, bottom radius 0.38 at z=0.14, top 0.31 at z=1.24.
body = primitive("Body", lambda bm: cone(bm, 0.38, 0.31, 1.1, SIDE_COUNT), (0, 0, 0.69), mat_stone, body_rotation)
soften(body, width=0.05, segments=3)
parts.append(body)

# Light stone belt around the belly.
belt = primitive("Belt", lambda bm: cone(bm, 0.345, 0.35, 0.09, SIDE_COUNT), (0, 0, 0.38), mat_stone_light, body_rotation)
soften(belt, width=0.02)
parts.append(belt)

# Face on the flat -Y side.
for side in (-1, 1):
    eye = primitive(f"Eye{side}", lambda bm: sphere(bm, 0.05), (side * 0.13, FACE_Y + 0.02, 1.0), mat_eye)
    soften(eye, width=0.012, segments=2)
    parts.append(eye)
    glint = primitive(f"Glint{side}", lambda bm: sphere(bm, 0.014), (side * 0.13 + 0.014, FACE_Y - 0.026, 1.02), mat_stone_light)
    parts.append(glint)
    brow = primitive(f"Brow{side}", lambda bm: cube(bm, (0.15, 0.06, 0.04)), (side * 0.14, FACE_Y + 0.005, 1.1), mat_stone_light)
    brow.rotation_euler = (0, side * 0.3, side * 0.06)
    soften(brow, width=0.014)
    parts.append(brow)

nose = primitive("Nose", lambda bm: cone(bm, 0.045, 0.03, 0.1, 12), (0, FACE_Y - 0.02, 0.93), mat_stone_light)
nose.rotation_euler = (1.5707963, 0, 0)
soften(nose, width=0.015)
parts.append(nose)

smile = primitive("Smile", lambda bm: cube(bm, (0.17, 0.05, 0.026)), (0, FACE_Y, 0.83), mat_eye)
smile.rotation_euler = (0.14, 0, 0)
soften(smile, width=0.011)
parts.append(smile)

beard = primitive("Beard", lambda bm: cube(bm, (0.3, 0.16, 0.32)), (0, FACE_Y + 0.03, 0.62), mat_stone_light)
beard.rotation_euler = (0.12, 0, 0)
soften(beard, width=0.07, segments=4)
parts.append(beard)

# Red scarf band right under the face.
scarf = primitive("Scarf", lambda bm: cone(bm, 0.315, 0.33, 0.11, SIDE_COUNT), (0, 0, 1.16), mat_red, body_rotation)
soften(scarf, width=0.012)
parts.append(scarf)
scarf_tail = primitive("ScarfTail", lambda bm: cube(bm, (0.11, 0.035, 0.26)), (-0.2, 0.18, 1.02), mat_red)
scarf_tail.rotation_euler = (-0.12, 0, 0.5)
soften(scarf_tail, width=0.012)
parts.append(scarf_tail)

# Bamboo hat: wide shallow brim + pointed crown.
brim = primitive("HatBrim", lambda bm: cone(bm, 0.52, 0.3, 0.07, 24), (0, -0.02, 1.28), mat_straw)
soften(brim, width=0.012)
parts.append(brim)
crown = primitive("HatCrown", lambda bm: cone(bm, 0.29, 0.025, 0.24, 24), (0, -0.02, 1.42), mat_straw)
soften(crown, width=0.01)
parts.append(crown)

# Moss patches.
for index, (x, y, z, s) in enumerate([(0.27, 0.08, 1.1, 0.09), (-0.25, 0.1, 1.05, 0.075), (0.02, 0.28, 1.2, 0.065)]):
    moss = primitive(f"Moss{index}", lambda bm: sphere(bm, s, 12, 8), (x, y, z), mat_stone_dark, scale=(1, 1, 0.5))
    parts.append(moss)

# Walking stick leaning on the right side.
stick = primitive("Stick", lambda bm: cone(bm, 0.026, 0.026, 1.1, 12), (0.46, -0.24, 0.55), mat_wood, (0.12, 0.05, 0))
parts.append(stick)
knob = primitive("StickKnob", lambda bm: sphere(bm, 0.055), (0.42, -0.265, 1.16), mat_wood)
parts.append(knob)

# Join into one object with origin at ground center.
bpy.ops.object.select_all(action="DESELECT")
for part in parts:
    part.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
grandpa = bpy.context.active_object
grandpa.name = "GrandpaBoundary"
bpy.context.scene.cursor.location = (0, 0, 0)
bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUTPUT), export_format="GLB", export_materials="EXPORT")
print("GRANDPA_READY", {"faces": len(grandpa.data.polygons), "output": str(OUTPUT)})

# Preview renders.
ground_data = bpy.data.meshes.new("Ground")
ground_data.from_pydata([(-4, -4, 0), (4, -4, 0), (4, 4, 0), (-4, 4, 0)], [], [(0, 1, 2, 3)])
ground_data.update()
ground = link(bpy.data.objects.new("Ground", ground_data))
ground_mat = make_material("GroundGray", (0.55, 0.55, 0.55, 1.0))
ground_data.materials.append(ground_mat)

sun_data = bpy.data.lights.new("Sun", type="SUN")
sun_data.energy = 3.0
sun = link(bpy.data.objects.new("Sun", sun_data))
sun.rotation_euler = (0.9, 0.2, 0.6)
world = bpy.data.worlds.new("World")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.75, 0.78, 0.8, 1.0)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.8
bpy.context.scene.world = world

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 48
scene.render.resolution_x = 900
scene.render.resolution_y = 1100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "Standard"
for name, location in {
    "grandpa_front": (0.0, -2.6, 0.95),
    "grandpa_three_quarter": (-2.2, -1.9, 1.2),
}.items():
    cam_data = bpy.data.cameras.new(name)
    cam_data.lens = 40
    cam = link(bpy.data.objects.new(name, cam_data))
    direction = Vector((0, 0, 0.75)) - Vector(location)
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    cam.location = location
    scene.camera = cam
    scene.render.filepath = str(PREVIEW_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", name)
