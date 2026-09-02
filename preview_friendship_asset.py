import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


# 用法: python preview_friendship_asset.py <ply文件路径> [输出目录]
ASSET = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("友谊关材料/图片/友谊关资产/0f142ad8e27a7e7eb910baff2a832ba7.ply")
OUTPUT_DIR = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("_preview_output")


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.ply_import(filepath=str(ASSET))
model = bpy.context.active_object

material = bpy.data.materials.new("Vertex Color")
material.use_nodes = True
nodes = material.node_tree.nodes
links = material.node_tree.links
shader = nodes.get("Principled BSDF")
color = nodes.new("ShaderNodeVertexColor")
color.layer_name = "Col"
links.new(color.outputs["Color"], shader.inputs["Base Color"])
shader.inputs["Roughness"].default_value = 0.78
model.data.materials.append(material)

corners = [model.matrix_world @ Vector(corner) for corner in model.bound_box]
center = sum(corners, Vector()) / 8
radius = max((corner - center).length for corner in corners)

bpy.ops.object.camera_add()
camera = bpy.context.active_object
camera.data.lens = 52
bpy.context.scene.camera = camera

for energy, size, offset in (
    (1700, radius * 1.4, (1.2, -1.0, 1.8)),
    (1050, radius * 1.0, (-1.5, -0.2, 0.8)),
    (1250, radius * 1.1, (0.2, 1.4, 1.3)),
):
    bpy.ops.object.light_add(type="AREA")
    light = bpy.context.active_object
    light.data.energy = energy
    light.data.shape = "DISK"
    light.data.size = size
    light.location = center + Vector(offset).normalized() * radius * 2
    look_at(light, center)

world = bpy.data.worlds.new("Preview World")
bpy.context.scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.055, 0.065, 0.08, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x = 1200
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.view_settings.look = "AgX - Medium High Contrast"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "VERTEX"
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "WORLD"
scene.display.shading.background_type = "VIEWPORT"
scene.display.shading.background_color = (0.055, 0.065, 0.08)

views = {
    "perspective": (1.55, -2.15, 1.05),
    "front": (0.0, -2.8, 0.15),
    "top": (0.0, 0.0, 2.8),
}
for name, direction in views.items():
    camera.location = center + Vector(direction).normalized() * radius * 2.45
    look_at(camera, center)
    output = OUTPUT_DIR / f"friendship-pass-{name}.png"
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)
    print(f"PREVIEW={output}")
