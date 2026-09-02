"""Build the Friendship Pass boundary marker GLB (中国 1117 / 2001).

Run via Blender CLI:
  blender --background --python tools/build_boundary_stone.py

Real marker reference (assets/友谊关界碑.jpg): granite pillar, red engraved
中国 / 1117 / 2001, national emblem on top, red granite plinth.
"""

from pathlib import Path

import bpy
from mathutils import Vector

OUTPUT = Path(r"D:\HKU-ds\QCH\界碑智能体\assets\models\boundary-stone.glb")
PREVIEW_DIR = Path(r"D:\HKU-ds\QCH\界碑智能体\tools\renders")
FONT_PATH = r"C:\Windows\Fonts\simhei.ttf"

GRANITE = (0.72, 0.72, 0.74, 1.0)
RED = (0.72, 0.12, 0.09, 1.0)
GOLD = (0.83, 0.66, 0.24, 1.0)
RED_STONE = (0.62, 0.18, 0.13, 1.0)

PILLAR_W = 0.52
PILLAR_D = 0.34
PILLAR_H = 1.42
PLINTH_W = 0.86
PLINTH_H = 0.12


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


def box(name, size, location, material):
    data = bpy.data.meshes.new(name)
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(data)
    bm.free()
    obj = bpy.data.objects.new(name, data)
    obj.scale = size
    obj.location = location
    link(obj)
    data.materials.append(material)
    return obj


def bevel_smooth(obj, width=0.012, segments=2):
    modifier = obj.modifiers.new("Soften", "BEVEL")
    modifier.width = width
    modifier.segments = segments
    modifier.limit_method = "ANGLE"
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True


def add_text(name, body, size, location, material, extrude=0.006):
    curve = bpy.data.curves.new(name, type="FONT")
    curve.body = body
    curve.size = size
    curve.extrude = extrude
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.resolution_u = 2
    obj = bpy.data.objects.new(name, curve)
    obj.location = location
    link(obj)
    curve.materials.append(material)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    return bpy.context.active_object


bpy.ops.wm.read_factory_settings(use_empty=True)
fonts = bpy.data.fonts
font = fonts.load(FONT_PATH, check_existing=True)

mat_granite = make_material("Granite", GRANITE)
mat_red = make_material("EngraveRed", RED, roughness=0.6)
mat_gold = make_material("EmblemGold", GOLD, roughness=0.45)
mat_red_stone = make_material("PlinthRed", RED_STONE)

parts = []

# Red granite plinth + granite pillar.
plinth = box("Plinth", (PLINTH_W, PLINTH_W, PLINTH_H), (0, 0, PLINTH_H / 2), mat_red_stone)
bevel_smooth(plinth, width=0.02)
parts.append(plinth)

pillar = box(
    "Pillar",
    (PILLAR_W, PILLAR_D, PILLAR_H),
    (0, 0, PLINTH_H + PILLAR_H / 2),
    mat_granite,
)
bevel_smooth(pillar, width=0.018)
parts.append(pillar)
# slight chamfer cap
cap = box("Cap", (PILLAR_W * 1.04, PILLAR_D * 1.04, 0.05), (0, 0, PLINTH_H + PILLAR_H + 0.02), mat_granite)
bevel_smooth(cap, width=0.015)
parts.append(cap)

# Front face is -Y (upright text: rotate the XY font plane up about X by 90°).
front_y = -PILLAR_D / 2
text_tilt = (1.5707963, 0.0, 0.0)
top_of_stone = PLINTH_H + PILLAR_H

emblem_center = (0.0, front_y - 0.006, top_of_stone - 0.24)
china = add_text("TextChina", "中国", 0.15, (0.0, front_y - 0.006, top_of_stone - 0.52), mat_red)
china.rotation_euler = text_tilt
number = add_text("TextNumber", "1117", 0.13, (0.0, front_y - 0.006, top_of_stone - 0.80), mat_red)
number.rotation_euler = text_tilt
year = add_text("TextYear", "2001", 0.09, (0.0, front_y - 0.006, 0.34), mat_red)
year.rotation_euler = text_tilt
parts += [china, number, year]

# Simplified national emblem: gold disc + red core + gold star.
disc_gold = bpy.data.meshes.new("EmblemGoldDisc")
import bmesh
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.105, radius2=0.105, depth=0.016)
bm.to_mesh(disc_gold)
bm.free()
emblem_gold = bpy.data.objects.new("EmblemGoldDisc", disc_gold)
emblem_gold.location = emblem_center
emblem_gold.rotation_euler = (1.5707963, 0, 0)
link(emblem_gold)
disc_gold.materials.append(mat_gold)
parts.append(emblem_gold)

disc_red = bpy.data.meshes.new("EmblemRedDisc")
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.088, radius2=0.088, depth=0.018)
bm.to_mesh(disc_red)
bm.free()
emblem_red = bpy.data.objects.new("EmblemRedDisc", disc_red)
emblem_red.location = emblem_center
emblem_red.rotation_euler = (1.5707963, 0, 0)
link(emblem_red)
disc_red.materials.append(mat_red)
parts.append(emblem_red)

star_size_outer = 0.052
star_size_inner = 0.021
star_vertices = []
for index in range(10):
    radius = star_size_outer if index % 2 == 0 else star_size_inner
    angle = 1.5707963 + index * 3.14159265 / 5
    star_vertices.append((radius * __import__("math").cos(angle), radius * __import__("math").sin(angle), 0.0))
star_data = bpy.data.meshes.new("EmblemStar")
star_data.from_pydata(star_vertices, [], [tuple(range(10))])
star_data.update()
star_obj = bpy.data.objects.new("EmblemStar", star_data)
star_obj.location = (emblem_center[0], emblem_center[1] - 0.013, emblem_center[2])
star_obj.rotation_euler = text_tilt
link(star_obj)
solidify = star_obj.modifiers.new("Thicken", "SOLIDIFY")
solidify.thickness = 0.008
bpy.context.view_layer.objects.active = star_obj
star_obj.select_set(True)
bpy.ops.object.modifier_apply(modifier="Thicken")
star_mat = make_material("EmblemStarGold", GOLD, roughness=0.4)
star_data.materials.append(star_mat)
parts.append(star_obj)

# Join into a single object with origin at ground center.
bpy.ops.object.select_all(action="DESELECT")
for part in parts:
    part.select_set(True)
bpy.context.view_layer.objects.active = pillar
bpy.ops.object.join()
stone = bpy.context.active_object
stone.name = "BoundaryStone1117"
bpy.context.scene.cursor.location = (0, 0, 0)
bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUTPUT), export_format="GLB", export_materials="EXPORT")
print("STONE_READY", {"faces": len(stone.data.polygons), "output": str(OUTPUT)})

# Quick preview renders on a neutral ground.
ground_data = bpy.data.meshes.new("Ground")
ground_data.from_pydata([(-4, -4, 0), (4, -4, 0), (4, 4, 0), (-4, 4, 0)], [], [(0, 1, 2, 3)])
ground_data.update()
ground = bpy.data.objects.new("Ground", ground_data)
ground.location = (0, 0, 0)
bpy.context.collection.objects.link(ground)
ground_mat = make_material("GroundGray", (0.55, 0.55, 0.55, 1.0))
ground_data.materials.append(ground_mat)

sun_data = bpy.data.lights.new("Sun", type="SUN")
sun_data.energy = 3.0
sun = bpy.data.objects.new("Sun", sun_data)
sun.rotation_euler = (0.9, 0.2, 0.6)
bpy.context.collection.objects.link(sun)
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
import math
for name, location in {
    "stone_front": (0.0, -2.8, 1.1),
    "stone_three_quarter": (2.2, -2.0, 1.4),
}.items():
    cam_data = bpy.data.cameras.new(name)
    cam_data.lens = 40
    cam = bpy.data.objects.new(name, cam_data)
    bpy.context.collection.objects.link(cam)
    direction = Vector((0, 0, 0.8)) - Vector(location)
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    cam.location = location
    scene.camera = cam
    scene.render.filepath = str(PREVIEW_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", name)
