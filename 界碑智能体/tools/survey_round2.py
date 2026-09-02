"""Round 2 survey: grid lines, labeled markers, and road-level cameras.

Run via Blender CLI:
  blender --background --python tools/survey_round2.py
"""

from pathlib import Path

import bpy
from mathutils import Vector

SOURCE = Path(r"D:\HKU-ds\QCH\友谊关材料\图片\友谊关资产\0f142ad8e27a7e7eb910baff2a832ba7.ply")
OUT_DIR = Path(r"D:\HKU-ds\QCH\界碑智能体\tools\renders")

MARKERS = {
    "spawn": ((6.0, -4.5, 4.20), (0.9, 0.2, 0.2)),
    "grandpa": ((4.4, -2.8, 2.94), (0.9, 0.6, 0.1)),
    "gate": ((-2.0, 0.0, -0.24), (0.2, 0.4, 0.9)),
    "boundary": ((7.2, 1.8, -2.71), (0.1, 0.8, 0.3)),
    "terrain": ((0.0, -3.0, 3.49), (0.5, 0.2, 0.7)),
}


def aim(camera, location, target):
    camera.location = location
    direction = Vector(target) - Vector(location)
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def add_camera(name, location, target, lens=28):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    aim(obj, location, target)
    return obj


def add_marker(name, location, color):
    data = bpy.data.meshes.new(f"{name}Sphere")
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=0.45)
    bm.to_mesh(data)
    bm.free()
    obj = bpy.data.objects.new(name, data)
    obj.location = location
    bpy.context.collection.objects.link(obj)
    mat = bpy.data.materials.new(f"{name}Mat")
    mat.diffuse_color = (*color, 1.0)
    data.materials.append(mat)
    return obj


def add_label(text, location, size=0.8):
    curve = bpy.data.curves.new(f"Label_{text}", type="FONT")
    curve.body = text
    curve.size = size
    curve.align_x = "CENTER"
    obj = bpy.data.objects.new(f"Label_{text}", curve)
    obj.location = location
    obj.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.collection.objects.link(obj)
    mat = bpy.data.materials.new(f"LabelMat_{text}")
    mat.diffuse_color = (1.0, 0.05, 0.05, 1.0)
    curve.materials.append(mat)
    return obj


def add_grid():
    mat = bpy.data.materials.new("GridMat")
    mat.diffuse_color = (0.9, 0.3, 0.1, 1.0)
    z = 11.2
    for x in range(-16, 20, 2):
        data = bpy.data.meshes.new(f"GridX{x}")
        data.from_pydata([(x, -10, z), (x, 10, z)], [], [])
        data.update()
        obj = bpy.data.objects.new(f"GridX{x}", data)
        obj.data.materials.append(mat)
        bpy.context.collection.objects.link(obj)
    for y in range(-10, 12, 2):
        data = bpy.data.meshes.new(f"GridY{y}")
        data.from_pydata([(-16, y, z), (20, y, z)], [], [])
        data.update()
        obj = bpy.data.objects.new(f"GridY{y}", data)
        obj.data.materials.append(mat)
        bpy.context.collection.objects.link(obj)
    for x in range(-16, 20, 4):
        add_label(str(x), (x, -9.2, z), size=0.7)
    for y in range(-10, 12, 4):
        add_label(str(y), (-15.2, y, z), size=0.7)


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.ply_import(filepath=str(SOURCE))
bpy.context.active_object.name = "Scan"

add_grid()
for name, (location, color) in MARKERS.items():
    add_marker(name, (location[0], location[1], location[2] + 1.2), color)
    add_label(name, (location[0], location[1] - 0.6, location[2] + 2.4), size=0.9)

scene = bpy.context.scene
scene.render.resolution_x = 1600
scene.render.resolution_y = 1000
scene.render.image_settings.file_format = "PNG"
scene.render.engine = "BLENDER_WORKBENCH"
shading = scene.display.shading
shading.light = "STUDIO"
shading.color_type = "SINGLE"
shading.show_cavity = True
shading.cavity_type = "BOTH"
shading.show_shadows = True
shading.shadow_intensity = 0.5

cameras = {
    "r2_top": add_camera("TopCam", (1.0, 0.5, 40), (1.0, 0.5, 0.0), lens=50),
    "r2_road_spawn_side": add_camera("RoadA", (8.5, -6.5, 7.5), (-3.0, 0.5, 0.5), lens=24),
    "r2_road_sw_side": add_camera("RoadB", (-7.0, -6.0, 6.0), (-1.0, 0.5, 0.0), lens=24),
    "r2_grandpa_to_gate": add_camera("RoadC", (4.4, -2.8, 4.4), (-2.5, 0.3, 0.8), lens=28),
    "r2_overview_south": add_camera("Overview", (1.0, -14.0, 13.0), (0.5, 0.5, 0.0), lens=35),
    "r2_gate_close": add_camera("GateClose", (1.5, -2.5, 2.2), (-2.2, 0.2, 0.5), lens=35),
    "r2_boundary_close": add_camera("BoundaryClose", (4.0, -1.5, 2.0), (7.6, 2.2, -1.8), lens=35),
    "r2_beyond_gate": add_camera("Beyond", (-2.0, 2.0, 2.0), (8.0, 3.0, -2.0), lens=28),
}
for name, camera in cameras.items():
    scene.camera = camera
    scene.render.filepath = str(OUT_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", name)
