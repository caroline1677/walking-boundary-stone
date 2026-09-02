"""Print vertical PLY intersections for candidate Study Debug points."""

import bpy
from mathutils import Vector


SOURCE = r"D:\HKU-ds\QCH\友谊关材料\图片\友谊关资产\0f142ad8e27a7e7eb910baff2a832ba7.ply"
POINTS = {
    "spawn": (6.0, -4.5),
    "grandpa": (4.4, -2.8),
    "gate": (-1.0, 0.5),
    "boundary": (7.2, 1.8),
    "terrain": (-6.0, 4.0),
}


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.ply_import(filepath=SOURCE)
depsgraph = bpy.context.evaluated_depsgraph_get()

for name, (x, y) in POINTS.items():
    intersections = []
    origin = Vector((x, y, 15.0))
    direction = Vector((0.0, 0.0, -1.0))
    for _ in range(16):
        hit, location, normal, *_ = bpy.context.scene.ray_cast(
            depsgraph, origin, direction, distance=40.0
        )
        if not hit:
            break
        intersections.append((round(location.z, 3), round(normal.z, 3)))
        origin = location + direction * 0.01
    print("LAYOUT_POINT", name, intersections)

print("GATE_WALKABLE_CANDIDATES")
for x in range(-4, 4):
    for y in range(-3, 4):
        hit, location, normal, *_ = bpy.context.scene.ray_cast(
            depsgraph, Vector((x, y, 15.0)), Vector((0.0, 0.0, -1.0)), distance=40.0
        )
        if hit and normal.z >= 0.72:
            print("GATE_CANDIDATE", x, y, round(location.z, 3), round(normal.z, 3))
