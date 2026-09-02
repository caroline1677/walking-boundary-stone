"""Probe ground heights and gate line-of-sight across the scan.

Run via Blender CLI:
  blender --background --python tools/probe_visibility.py

Prints gate column layer stacks and a JSON of candidate viewpoints that can
actually see the gate tower, so layout points are chosen against real geometry.
"""

import json
from pathlib import Path

import bpy
from mathutils import Vector

SOURCE = Path(r"D:\HKU-ds\QCH\友谊关材料\图片\友谊关资产\0f142ad8e27a7e7eb910baff2a832ba7.ply")
OUT = Path(r"D:\HKU-ds\QCH\界碑智能体\tools\renders\visibility.json")

EYE = 1.6

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.ply_import(filepath=str(SOURCE))
scene = bpy.context.scene
depsgraph = bpy.context.evaluated_depsgraph_get()


def column_layers(x, y, max_layers=16, z_top=25.0):
    origin = Vector((x, y, z_top))
    direction = Vector((0.0, 0.0, -1.0))
    layers = []
    for _ in range(max_layers):
        hit, location, normal, *_ = scene.ray_cast(depsgraph, origin, direction, distance=80.0)
        if not hit:
            break
        layers.append({
            "z": round(location.z, 2),
            "nz": round(normal.z, 2),
        })
        origin = location + direction * 0.02
    return layers


print("=== GATE COLUMNS (find tower top + arch opening) ===")
for x in (-3.0, -2.5, -2.0, -1.5, -1.0):
    for y in (-1.0, -0.5, 0.0, 0.5, 1.0):
        layers = column_layers(x, y)
        if layers:
            tops = [item["z"] for item in layers]
            print("GATECOL", x, y, "z:", tops[:8])

print("=== VIEWPOINT SCAN ===")
gate_targets = {}
for key, (gx, gy) in {"arch": (-2.0, 0.0), "tower": (-2.0, 0.0)}.items():
    pass

# Filled after reading gate column output manually is not possible here, so
# probe tower top from the tallest structure near the notch directly.
notch_layers = column_layers(-2.0, 0.0, max_layers=20)
road_z = None
tower_top = None
for index, item in enumerate(notch_layers):
    pass

candidates = []
x = -11.0
while x <= 9.01:
    y = -8.0
    while y <= 4.01:
        layers = column_layers(x, y, max_layers=4)
        if layers:
            ground = layers[0]
            if ground["nz"] < 0.55 or ground["z"] > 8.0:
                x_local = x
                y_local = y
            else:
                eye = Vector((x, y, ground["z"] + EYE))
                # line of sight to the tallest visible structure in the notch
                best_ratio = 0.0
                for target_z in (0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5):
                    target = Vector((-2.0, 0.0, target_z))
                    direction = target - eye
                    distance = direction.length
                    if distance < 3.0:
                        continue
                    hit, location, *_ = scene.ray_cast(depsgraph, eye, direction.normalized(), distance=distance)
                    if not hit:
                        ratio = 1.0
                    else:
                        hit_distance = (Vector(location) - eye).length
                        ratio = hit_distance / distance
                    best_ratio = max(best_ratio, ratio)
                candidates.append({
                    "x": round(x, 1),
                    "y": round(y, 1),
                    "z": ground["z"],
                    "visibility": round(best_ratio, 3),
                    "dist": round(eye.length, 1),
                })
        y += 0.5
    x += 0.5

OUT.write_text(json.dumps(candidates, ensure_ascii=False), encoding="utf-8")
visible = [item for item in candidates if item["visibility"] > 0.92]
visible.sort(key=lambda item: -item["dist"])
print("VISIBLE_FAR", json.dumps(visible[:25], ensure_ascii=False))
print("CANDIDATES", len(candidates), "->", str(OUT))
