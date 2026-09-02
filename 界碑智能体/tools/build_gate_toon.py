"""Stylized low-poly Friendship Pass gate + walls, matched to the toon look.

Run via Blender CLI:
  blender --background --python tools/build_gate_toon.py

The gate base straddles the measured arch at (-2, 0) with the passage along X;
wall segments climb north/south following ray-casted ground heights from the
source scan. Output:
  assets/models/friendship-gate-toon.glb (+ preview renders)
"""

import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

SOURCE = Path(r"D:\HKU-ds\QCH\友谊关材料\图片\友谊关资产\0f142ad8e27a7e7eb910baff2a832ba7.ply")
ROOT = Path(r"D:\HKU-ds\QCH\界碑智能体")
OUT = ROOT / "assets/models/friendship-gate-toon.glb"

GATE_X, GATE_Y = -2.0, 0.0
OPEN_HALF = 1.1          # passage half-width along X
PIER_W = 2.0             # pier thickness along X
PIER_LEN = 6.0           # wall length along Y
BASE_H = 3.2

C_STONE = (0.74, 0.70, 0.62)
C_STONE_D = (0.58, 0.55, 0.49)
C_RED = (0.72, 0.30, 0.23)
C_GREEN = (0.17, 0.42, 0.34)
C_ROOF = (0.26, 0.30, 0.37)
C_DARK = (0.10, 0.09, 0.08)
C_GOLD = (0.87, 0.70, 0.30)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.ply_import(filepath=str(SOURCE))
scan = bpy.context.selected_objects[0] if bpy.context.selected_objects else bpy.context.active_object
scene = bpy.context.scene
depsgraph = bpy.context.evaluated_depsgraph_get()


def ground_z(x, y):
    origin = Vector((x, y, 25.0))
    direction = Vector((0.0, 0.0, -1.0))
    for _ in range(6):
        hit, location, normal, *_ = scene.ray_cast(depsgraph, origin, direction, distance=80.0)
        if not hit:
            return None
        if normal.z >= 0.55:
            return location.z
        origin = location + direction * 0.05
    return location.z


parts = []  # (color, list of vertex tuples, list of face index tuples)


def add_box(color, cx, cy, cz, sx, sy, sz):
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    v = [(cx - hx, cy - hy, cz - hz), (cx + hx, cy - hy, cz - hz), (cx + hx, cy + hy, cz - hz), (cx - hx, cy + hy, cz - hz),
         (cx - hx, cy - hy, cz + hz), (cx + hx, cy - hy, cz + hz), (cx + hx, cy + hy, cz + hz), (cx - hx, cy + hy, cz + hz)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (3, 0, 4, 7)]
    parts.append((color, v, f))


def add_prism_roof(color, x0, x1, y0, y1, z0, ridge_x0, ridge_x1, z_apex):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (ridge_x0, (y0 + y1) / 2, z_apex), (ridge_x1, (y0 + y1) / 2, z_apex)]
    f = [(0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5)]
    parts.append((color, v, f))


# ---- gate base (rooted deep into the terrain so slopes never float it) ----
px = GATE_X
inner = OPEN_HALF
pier_c1 = px - inner - PIER_W / 2
pier_c2 = px + inner + PIER_W / 2
ROOT_Z = -3.0
for c in (pier_c1, pier_c2):
    add_box(C_STONE, c, GATE_Y, (BASE_H + ROOT_Z) / 2, PIER_W, PIER_LEN, BASE_H - ROOT_Z)
# lintel above the passage
add_box(C_STONE, px, GATE_Y, BASE_H + 0.35, inner * 2 + PIER_W + 0.4, PIER_LEN, 0.7)
# dark recessed frame around the passage
add_box(C_DARK, px - inner + 0.12, GATE_Y, BASE_H * 0.45, 0.25, PIER_LEN + 0.06, BASE_H * 0.9)
add_box(C_DARK, px + inner - 0.12, GATE_Y, BASE_H * 0.45, 0.25, PIER_LEN + 0.06, BASE_H * 0.9)
add_box(C_DARK, px, GATE_Y, BASE_H - 0.14, inner * 2, PIER_LEN + 0.06, 0.28)
# upper platform slab with overhang
add_box(C_STONE_D, px, GATE_Y, BASE_H + 0.9, inner * 2 + PIER_W + 1.2, PIER_LEN + 0.5, 0.42)
# crenellations on the slab edge
for k in range(-3, 4):
    if abs(k) < 1:
        continue
    add_box(C_STONE, px + k * 0.95, GATE_Y - PIER_LEN / 2 - 0.05, BASE_H + 1.35, 0.5, 0.42, 0.55)
    add_box(C_STONE, px + k * 0.95, GATE_Y + PIER_LEN / 2 + 0.05, BASE_H + 1.35, 0.5, 0.42, 0.55)
add_box(C_STONE, px - inner - PIER_W - 0.1, GATE_Y, BASE_H + 1.35, 0.42, 0.5, 0.55)
add_box(C_STONE, px + inner + PIER_W + 0.1, GATE_Y, BASE_H + 1.35, 0.42, 0.5, 0.55)

# ---- tower tiers ----
T0 = BASE_H + 1.1
add_box((0.88, 0.85, 0.78), px, GATE_Y, T0 + 0.14, 4.6, 3.6, 0.28)
add_box(C_RED, px, GATE_Y, T0 + 0.98, 4.2, 3.2, 1.7)
for sx in (-1, 1):
    for sy in (-1, 1):
        add_box(C_GREEN, px + sx * 2.0, GATE_Y + sy * 1.5, T0 + 0.98, 0.28, 0.28, 1.7)
for sy in (-0.95, 0.95):
    add_box(C_GREEN, px - 2.16, GATE_Y + sy, T0 + 1.15, 0.05, 0.9, 0.06)
    add_box(C_DARK, px - 2.18, GATE_Y + sy, T0 + 0.75, 0.06, 0.55, 0.62)
add_box(C_GREEN, px - 2.16, GATE_Y, T0 + 1.15, 0.05, 1.1, 0.06)
add_box(C_DARK, px - 2.18, GATE_Y, T0 + 0.72, 0.06, 0.7, 0.68)
add_prism_roof(C_ROOF, px - 2.85, px + 2.85, GATE_Y - 2.25, GATE_Y + 2.25, T0 + 1.83, px - 1.0, px + 1.0, T0 + 2.7)

T1 = T0 + 2.7
add_box(C_RED, px, GATE_Y, T1 + 0.62, 2.9, 2.3, 1.24)
for sx in (-1, 1):
    for sy in (-1, 1):
        add_box(C_GREEN, px + sx * 1.36, GATE_Y + sy * 1.06, T1 + 0.62, 0.24, 0.24, 1.24)
add_box(C_GREEN, px - 1.49, GATE_Y, T1 + 0.85, 0.05, 0.9, 0.05)
add_box(C_DARK, px - 1.51, GATE_Y, T1 + 0.55, 0.06, 0.55, 0.5)
add_prism_roof(C_ROOF, px - 2.15, px + 2.15, GATE_Y - 1.8, GATE_Y + 1.8, T1 + 1.24, px - 0.6, px + 0.6, T1 + 1.95)
add_box(C_GOLD, px, GATE_Y, T1 + 2.2, 0.14, 0.14, 0.5)

# ---- walls climbing north/south, following sampled ground ----
def add_wall_run(points, top_above=2.0, width=1.6):
    for k in range(len(points) - 1):
        ax, ay = points[k]
        bx, by = points[k + 1]
        za = ground_z(ax, ay)
        zb = ground_z(bx, by)
        if za is None or zb is None:
            continue
        zt = max(za, zb) + top_above
        cxm, cym = (ax + bx) / 2, (ay + by) / 2
        length = math.hypot(bx - ax, by - ay)
        base = min(za, zb) - 0.8
        h = zt - base
        add_box(C_STONE, cxm, cym, base + h / 2, width if abs(by - ay) >= abs(bx - ax) else length,
                length if abs(by - ay) >= abs(bx - ax) else width, h)
        # merlons along the top
        steps = max(1, int(length / 1.0))
        for s in range(steps):
            t = (s + 0.5) / steps
            mx, my = ax + (bx - ax) * t, ay + (by - ay) * t
            add_box(C_STONE_D, mx, my, base + h + 0.28, 0.55 if abs(by - ay) >= abs(bx - ax) else 0.45,
                    0.45 if abs(by - ay) >= abs(bx - ax) else 0.55, 0.55)


add_wall_run([(GATE_X, GATE_Y - 2.9), (GATE_X, -4.0), (GATE_X + 0.4, -5.2), (GATE_X + 1.2, -6.4)])
add_wall_run([(GATE_X, GATE_Y + 2.9), (GATE_X - 0.4, 4.2), (GATE_X - 1.0, 5.4)])
# short cheek walls hugging the gate on the valley floor
add_wall_run([(pier_c2 + PIER_W / 2, GATE_Y + 1.2), (pier_c2 + PIER_W / 2 + 0.2, GATE_Y + 2.9)], top_above=1.7, width=1.2)

# scan cloud only needed for ground sampling
bpy.data.objects.remove(scan, do_unlink=True)

# ---- build one vertex-colored mesh ----
bm = bmesh.new()
color_layer = bm.loops.layers.color.new("Col")
for color, verts, faces in parts:
    mapping = [bm.verts.new(v) for v in verts]
    for f in faces:
        face = bm.faces.new((mapping[i] for i in f))
        for loop in face.loops:
            loop[color_layer] = (*color, 1.0)

me = bpy.data.meshes.new("ToonGate")
bm.to_mesh(me)
bm.free()
if me.color_attributes:
    me.color_attributes.active_color = me.color_attributes[0]
obj = bpy.data.objects.new("ToonGate", me)
bpy.context.collection.objects.link(obj)

# ---- preview renders ----
scene.render.resolution_x = 1400
scene.render.resolution_y = 900
scene.render.image_settings.file_format = "PNG"
scene.render.engine = "BLENDER_WORKBENCH"
shading = scene.display.shading
shading.light = "STUDIO"
shading.color_type = "VERTEX"
shading.show_cavity = True
shading.cavity_type = "BOTH"
shading.show_shadows = True
shading.shadow_intensity = 0.35


def add_camera(name, location, target, lens=32):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    o = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(o)
    direction = Vector(target) - Vector(location)
    o.location = location
    o.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return o


for name, (loc, tgt, lens) in {
    "toon_gate_front": ((3.2, -2.6, 1.7), (GATE_X, GATE_Y, 3.2), 32),
    "toon_gate_close": ((1.2, -1.1, 1.5), (-2.4, 0.2, 2.2), 30),
    "toon_gate_north": ((1.5, 2.8, 1.3), (-2, 0, 3.0), 32),
    "toon_gate_high": ((5.0, -5.0, 8.0), (-2, 0, 3.0), 32),
}.items():
    scene.camera = add_camera(name, loc, tgt, lens)
    scene.render.filepath = str(ROOT / f"tools/renders/{name}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", name)

bpy.ops.object.select_all(action="DESELECT")
obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, use_selection=True)
print("WROTE", OUT)
