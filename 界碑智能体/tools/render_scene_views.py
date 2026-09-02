"""Render survey views of the Friendship Pass PLY and dump a walkability grid.

Run via Blender CLI:
  blender --background --python tools/render_scene_views.py

Outputs PNG renders into tools/renders/ and a ground-grid JSON used to pick
quest point coordinates against the real scanned geometry.
"""

import json
from pathlib import Path

import bpy
from mathutils import Vector

SOURCE = Path(r"D:\HKU-ds\QCH\友谊关材料\图片\友谊关资产\0f142ad8e27a7e7eb910baff2a832ba7.ply")
OUT_DIR = Path(r"D:\HKU-ds\QCH\界碑智能体\tools\renders")
GRID_FILE = OUT_DIR / "ground-grid.json"

# Existing calibration points in Blender Z-up, drawn as empties for reference.
KNOWN_POINTS = {
    "spawn": (6.0, -4.5, 4.20),
    "grandpa": (4.4, -2.8, 2.94),
    "gate": (-2.0, 0.0, -0.24),
    "boundary": (7.2, 1.8, -2.71),
    "terrain": (0.0, -3.0, 3.49),
}


def aim(camera, location, target):
    camera.location = location
    direction = Vector(target) - Vector(location)
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def add_camera(name, location, target, ortho_scale=None):
    data = bpy.data.cameras.new(name)
    if ortho_scale:
        data.type = "ORTHO"
        data.ortho_scale = ortho_scale
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    aim(obj, location, target)
    return obj


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.ply_import(filepath=str(SOURCE))
mesh_obj = bpy.context.active_object
mesh_obj.name = "FriendshipPassScan"

bbox = [Vector(corner) for corner in mesh_obj.bound_box]
mins = Vector((min(v.x for v in bbox), min(v.y for v in bbox), min(v.z for v in bbox)))
maxs = Vector((max(v.x for v in bbox), max(v.y for v in bbox), max(v.z for v in bbox)))
center = (mins + maxs) / 2
size = maxs - mins
print("BBOX", {
    "min": [round(v, 2) for v in mins],
    "max": [round(v, 2) for v in maxs],
    "size": [round(v, 2) for v in size],
})

for point_id, location in KNOWN_POINTS.items():
    empty = bpy.data.objects.new(f"Ref_{point_id}", None)
    empty.location = location
    empty.empty_display_size = 0.6
    bpy.context.collection.objects.link(empty)

scene = bpy.context.scene
scene.render.resolution_x = 1600
scene.render.resolution_y = 1000
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "Standard"

try:
    scene.render.engine = "BLENDER_WORKBENCH"
    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.color_type = "SINGLE"
    shading.show_cavity = True
    shading.cavity_type = "BOTH"
    shading.show_shadows = True
    print("ENGINE workbench")
except Exception as error:  # pragma: no cover - GPU-less fallback
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 24
    scene.cycles.use_denoising = False
    world = bpy.data.worlds.new("SurveyWorld")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.7, 0.72, 0.75, 1.0)
    world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    scene.world = world
    print("ENGINE cycles-cpu", error)

OUT_DIR.mkdir(parents=True, exist_ok=True)
cameras = {
    "top": add_camera("TopCam", (center.x, center.y, maxs.z + 35), (center.x, center.y, center.z), ortho_scale=max(size.x, size.y) * 1.08),
    "overview": add_camera("OverviewCam", (center.x + size.x * 0.35, center.y - size.y * 1.1, center.z + size.z * 0.75), (center.x, center.y + size.y * 0.1, center.z)),
    "from_spawn": add_camera("FromSpawnCam", (7.5, -7.5, 7.0), (-2.5, 0.5, 0.0)),
    "from_gate": add_camera("FromGateCam", (-2.0, 1.0, 1.6), (7.0, -4.5, 4.0)),
    "boundary_area": add_camera("BoundaryCam", (3.0, -3.5, 4.5), (7.5, 2.0, -1.5)),
}
for name, camera in cameras.items():
    scene.camera = camera
    scene.render.filepath = str(OUT_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", name)

# Walkability grid: ray-cast straight down, keep upward-facing hits.
depsgraph = bpy.context.evaluated_depsgraph_get()
grid = []
x = -14.0
while x <= 16.0:
    y = -8.0
    while y <= 8.0:
        origin = Vector((x, y, 20.0))
        direction = Vector((0.0, 0.0, -1.0))
        layers = []
        for _ in range(8):
            hit, location, normal, *_ = scene.ray_cast(depsgraph, origin, direction, distance=60.0)
            if not hit:
                break
            layers.append({
                "z": round(location.z, 2),
                "nz": round(normal.z, 2),
            })
            origin = location + direction * 0.02
        if layers:
            grid.append({"x": round(x, 1), "y": round(y, 1), "layers": layers})
        y += 1.0
    x += 1.0
GRID_FILE.write_text(json.dumps(grid, ensure_ascii=False), encoding="utf-8")
print("GRID", {"samples": len(grid), "output": str(GRID_FILE)})
