"""Toon-style terrain + vegetation rebuilt from the real scan.

Run via Blender CLI:
  blender --background --python tools/build_world_toon.py

Keeps the measured quest space (corridor heights stay pinned to the walkable
grid) but replaces the noisy point-cloud look with flat-shaded, vertex-colored
low-poly: sandy road, picture-book grass, rock cliffs, skirt walls, stylized
trees and rocks. Outputs:
  assets/worlds/friendship-pass-toon-terrain.glb
  assets/worlds/friendship-pass-toon-props.glb
  tools/renders/toon_terrain_preview.png
"""

import json
import math
from pathlib import Path

import bmesh
import numpy as np
import bpy
from mathutils import Vector

SOURCE = Path(r"D:\HKU-ds\QCH\友谊关材料\图片\友谊关资产\0f142ad8e27a7e7eb910baff2a832ba7.ply")
ROOT = Path(r"D:\HKU-ds\QCH\界碑智能体")
WALKABLE = ROOT / "tools/renders/walkable.json"
LAYOUT = ROOT / "data/friendship-pass-layout.json"
OUT_TERRAIN = ROOT / "assets/worlds/friendship-pass-toon-terrain.glb"
OUT_PROPS = ROOT / "assets/worlds/friendship-pass-toon-props.glb"
PREVIEW = ROOT / "tools/renders/toon_terrain_preview.png"

X_MIN, X_MAX = -15.0, 13.0
Y_MIN, Y_MAX = -10.0, 7.0
CELL = 0.5
SKIRT_Z = -6.0

C_GRASS_A = (0.42, 0.66, 0.31)
C_GRASS_B = (0.55, 0.74, 0.36)
C_GRASS_DARK = (0.36, 0.58, 0.31)
C_PATH = (0.86, 0.75, 0.53)
C_PATH_B = (0.78, 0.66, 0.45)
C_ROCK = (0.58, 0.53, 0.46)
C_CLIFF = (0.42, 0.38, 0.33)
C_SOIL = (0.60, 0.52, 0.40)
C_TRUNK = (0.46, 0.33, 0.22)
C_PINE_A = (0.28, 0.53, 0.31)
C_PINE_B = (0.34, 0.61, 0.34)
C_LEAF_A = (0.45, 0.68, 0.28)
C_LEAF_B = (0.62, 0.72, 0.30)
C_LEAF_C = (0.85, 0.64, 0.26)

bpy.ops.wm.read_factory_settings(use_empty=True)

walkable = json.loads(WALKABLE.read_text(encoding="utf-8"))
layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
reach = {}
for x, y, levels in walkable["reachableCells"]:
    reach[(round(x, 2), round(y, 2))] = min(levels)

nx = int(round((X_MAX - X_MIN) / CELL)) + 1
ny = int(round((Y_MAX - Y_MIN) / CELL)) + 1
ii, jj = np.meshgrid(np.arange(nx), np.arange(ny), indexing="ij")
cx = X_MIN + ii * CELL
cy = Y_MIN + jj * CELL


def cell_center(i, j):
    return X_MIN + i * CELL, Y_MIN + j * CELL


def cell_key(x, y):
    return (round(round((x - X_MIN) / CELL) * CELL + X_MIN, 2),
            round(round((y - Y_MIN) / CELL) * CELL + Y_MIN, 2))


H = np.full((nx, ny), np.nan, dtype=np.float64)
for (x, y), z in reach.items():
    i = int(round((x - X_MIN) / CELL))
    j = int(round((y - Y_MIN) / CELL))
    if 0 <= i < nx and 0 <= j < ny:
        H[i, j] = z

for _ in range(80):
    missing = np.isnan(H)
    if not missing.any():
        break
    acc = np.zeros_like(H)
    cnt = np.zeros_like(H)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        shifted_h = np.roll(H, (dx, dy), axis=(0, 1))
        known = ~np.isnan(shifted_h)
        use = missing & known
        acc[use] += shifted_h[use]
        cnt[use] += 1
    fill = missing & (cnt > 0)
    H[fill] = acc[fill] / cnt[fill]
H[np.isnan(H)] = np.nanmin(H) - 0.6

corridor = np.vectorize(lambda i, j: reach.get(cell_key(*cell_center(i, j))) is not None)(ii, jj)
orig = H.copy()
for _ in range(2):
    smooth = H.copy()
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        smooth += np.roll(H, (dx, dy), axis=(0, 1))
    smooth /= 5.0
    H = np.where(corridor, orig, smooth)

for _ in range(2):
    med = H.copy()
    stack = []
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        stack.append(np.roll(H, (dx, dy), axis=(0, 1)))
    stack = np.stack(stack)
    med = (stack[1] * 0.6 + stack[2] * 0.4)
    H = np.where((~corridor) & (np.abs(H - med) > 2.5), med, H)

gy, gx = np.gradient(H, CELL, CELL)
slope = np.hypot(gx, gy)

road_pts = [
    (8.4, -4.5), (7.0, -3.5), (7.5, -2.5), (6.5, -1.5), (5.5, -0.8),
    (2.0, -0.5), (-2.0, 0.0), (-2.0, 1.2), (0.0, 2.0), (3.0, 2.3), (6.0, 2.5),
]


def dist_to_polyline(px, py):
    best = np.full(px.shape, 1e9)
    for k in range(len(road_pts) - 1):
        ax, ay = road_pts[k]
        bx, by = road_pts[k + 1]
        abx, aby = bx - ax, by - ay
        t = np.clip(((px - ax) * abx + (py - ay) * aby) / (abx * abx + aby * aby), 0.0, 1.0)
        dx = px - (ax + t * abx)
        dy = py - (ay + t * aby)
        best = np.minimum(best, np.hypot(dx, dy))
    return best


noise = np.vectorize(lambda a, b: abs((math.sin(a * 12.9898 + b * 78.233) * 43758.5453) % 1.0))(ii, jj)
reachable_mask = np.vectorize(lambda i, j: reach.get(cell_key(*cell_center(i, j))) is not None)(ii, jj)
path_mask = reachable_mask & (slope < 0.55) & (dist_to_polyline(cx, cy) < 1.3)
tree_mask = reachable_mask & (slope < 0.9) & (dist_to_polyline(cx, cy) >= 2.2)

clearings = [layout["points"][k] for k in ("spawn", "grandpa", "gate", "boundary", "terrain")]
clearings += [d["position"] for d in layout["discoveries"]]
for p in clearings:
    zx, zy = p["x"], -p["z"]
    tree_mask &= ~(np.hypot(cx - zx, cy - zy) < 2.6)

# ---- read PLY point cloud for canopy detection ----
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.ply_import(filepath=str(SOURCE))
scan = bpy.context.selected_objects[0] if bpy.context.selected_objects else bpy.context.active_object
mesh = scan.data
n = len(mesh.vertices)
coords = np.empty(n * 3, dtype=np.float64)
mesh.vertices.foreach_get("co", coords)
coords = coords.reshape((n, 3))
colors = None
if mesh.color_attributes:
    attr = mesh.color_attributes[0]
    raw = np.empty(n * 4, dtype=np.float32)
    attr.data.foreach_get("color", raw)
    colors = raw.reshape((n, 4))[:, :3]
print("PLY_POINTS", n, "colors", "yes" if colors is not None else "no")

gi = np.clip(((coords[:, 0] - X_MIN) / CELL).astype(int), 0, nx - 1)
gj = np.clip(((coords[:, 1] - Y_MIN) / CELL).astype(int), 0, ny - 1)
above = coords[:, 2] > H[gi, gj] + 2.2
canopy = above.copy()
if colors is not None:
    canopy &= (colors[:, 1] > colors[:, 0] * 0.9) & (colors[:, 1] > colors[:, 2] * 0.85)

canopy_count = np.zeros((nx, ny), dtype=np.int32)
np.add.at(canopy_count, (gi[canopy], gj[canopy]), 1)

road_dist = dist_to_polyline(cx, cy)
gate_dist = np.hypot(cx + 2.0, cy)
clearings = [layout["points"][k] for k in ("spawn", "grandpa", "gate", "boundary", "terrain")]
clearings += [d["position"] for d in layout["discoveries"]]
clear_xy = []
for p in clearings:
    radius = 5.0 if p is layout["points"]["spawn"] or p is layout["points"]["grandpa"] else 6.5
    clear_xy.append((p["x"], -p["z"], radius))
tree_cells = []
for i in range(nx):
    for j in range(ny):
        if slope[i, j] > 2.4 or road_dist[i, j] < 2.8 or gate_dist[i, j] < 4.5:
            continue
        if any((cx[i, j] - zx) ** 2 + (cy[i, j] - zy) ** 2 < radius ** 2 for zx, zy, radius in clear_xy):
            continue
        scan_tree = canopy_count[i, j] >= 3
        filler = noise[i, j] > 0.26
        if scan_tree or filler:
            tree_cells.append((i, j, int(canopy_count[i, j]) + int(filler) * 4))
tree_cells.sort(key=lambda t: -t[2])
placed = []
for i, j, _cnt in tree_cells:
    if len(placed) >= 150:
        break
    x, y = cell_center(i, j)
    if any((x - px) ** 2 + (y - py) ** 2 < 2.0 ** 2 for px, py in placed):
        continue
    placed.append((x, y))
print("TREES", len(placed))

rock_cells = [(i, j) for i in range(1, nx - 1) for j in range(1, ny - 1)
              if slope[i, j] > 1.15 and not reachable_mask[i, j] and noise[i, j] > 0.75][:60]

# ---- terrain mesh with vertex colors ----
def color_with_noise(base, i, j, amount=0.06):
    f = 1.0 + (noise[i, j] - 0.5) * 2 * amount
    return tuple(min(1.0, c * f) for c in base)


def cell_color(i, j):
    if path_mask[i, j]:
        return color_with_noise(C_PATH if noise[i, j] > 0.5 else C_PATH_B, i, j)
    if slope[i, j] > 1.15:
        return color_with_noise(C_ROCK, i, j)
    if reachable_mask[i, j] or slope[i, j] < 0.7:
        return color_with_noise(C_GRASS_A if noise[i, j] > 0.45 else C_GRASS_B, i, j)
    return color_with_noise(C_GRASS_DARK, i, j, 0.08)


bm = bmesh.new()
for i in range(nx - 1):
    for j in range(ny - 1):
        x0, y0 = cell_center(i, j)
        x1, y1 = x0 + CELL, y0 + CELL
        v0 = bm.verts.new((x0, y0, H[i, j]))
        v1 = bm.verts.new((x1, y0, H[i + 1, j]))
        v2 = bm.verts.new((x1, y1, H[i + 1, j + 1]))
        v3 = bm.verts.new((x0, y1, H[i, j + 1]))
        bm.faces.new((v0, v1, v2, v3))

# skirt walls around the region border
for i in range(nx - 1):
    for (a, b) in (((i, 0), (i + 1, 0)), ((i, ny - 1), (i + 1, ny - 1))):
        x0, y0 = cell_center(*a)
        x1, y1 = cell_center(*b)
        v0 = bm.verts.new((x0, y0, H[a[0], a[1]]))
        v1 = bm.verts.new((x1, y1, H[b[0], b[1]]))
        v2 = bm.verts.new((x1, y1, SKIRT_Z))
        v3 = bm.verts.new((x0, y0, SKIRT_Z))
        bm.faces.new((v0, v1, v2, v3))
for j in range(ny - 1):
    for (a, b) in (((0, j), (0, j + 1)), ((nx - 1, j), (nx - 1, j + 1))):
        x0, y0 = cell_center(*a)
        x1, y1 = cell_center(*b)
        v0 = bm.verts.new((x0, y0, H[a[0], a[1]]))
        v1 = bm.verts.new((x1, y1, H[b[0], b[1]]))
        v2 = bm.verts.new((x1, y1, SKIRT_Z))
        v3 = bm.verts.new((x0, y0, SKIRT_Z))
        bm.faces.new((v0, v1, v2, v3))

color_layer = bm.loops.layers.color.new("Col")
bm.faces.ensure_lookup_table()
for face in bm.faces:
    xs = [v.co.x for v in face.verts]
    ys = [v.co.y for v in face.verts]
    if any(v.co.z <= SKIRT_Z + 1e-3 for v in face.verts):
        col = C_CLIFF
    else:
        i = min(max(int(round((sum(xs) / 4 - X_MIN) / CELL)), 0), nx - 2)
        j = min(max(int(round((sum(ys) / 4 - Y_MIN) / CELL)), 0), ny - 2)
        col = cell_color(i, j)
    for loop in face.loops:
        loop[color_layer] = (*col, 1.0)

terrain_me = bpy.data.meshes.new("ToonTerrain")
bm.to_mesh(terrain_me)
bm.free()
if terrain_me.color_attributes:
    terrain_me.color_attributes.active_color = terrain_me.color_attributes[0]
terrain_obj = bpy.data.objects.new("ToonTerrain", terrain_me)
bpy.context.collection.objects.link(terrain_obj)

# scan point cloud no longer needed in the scene
bpy.data.objects.remove(scan, do_unlink=True)

# ---- props (trees + rocks) ----
pmb = bmesh.new()


def emit_part(builder, color, offset, scale=1.0):
    tmp = bmesh.new()
    builder(tmp, scale)
    layer = tmp.loops.layers.color.new("Col")
    for f in tmp.faces:
        for l in f.loops:
            l[layer] = (*color, 1.0)
    for v in tmp.verts:
        v.co += Vector(offset)
    me = bpy.data.meshes.new("part")
    tmp.to_mesh(me)
    tmp.free()
    for p in me.polygons:
        p.use_smooth = False
    pmb.from_mesh(me)
    bpy.data.meshes.remove(me)


def noise2(a, b):
    return abs((math.sin(a * 3.1 + b * 7.7) * 24681.37) % 1.0)


def trunk_only(b2, sc):
    seg = 5
    pts0 = [(math.cos(k / seg * 2 * math.pi) * 0.11 * sc, math.sin(k / seg * 2 * math.pi) * 0.11 * sc, 0.0) for k in range(seg)]
    pts1 = [(math.cos(k / seg * 2 * math.pi) * 0.08 * sc, math.sin(k / seg * 2 * math.pi) * 0.08 * sc, 0.95 * sc) for k in range(seg)]
    v0 = [b2.verts.new(p) for p in pts0]
    v1 = [b2.verts.new(p) for p in pts1]
    for k in range(seg):
        b2.faces.new((v0[k], v0[(k + 1) % seg], v1[(k + 1) % seg], v1[k]))
    b2.faces.new(v0)


def pine_canopy(b2, sc):
    rot = noise2(sc, 7) * 6.28
    for z0, z1, r0 in ((0.30 * sc, 1.50 * sc, 0.90 * sc), (0.85 * sc, 1.85 * sc, 0.62 * sc)):
        seg = 6
        pts = [(math.cos(rot + k / seg * 2 * math.pi) * r0, math.sin(rot + k / seg * 2 * math.pi) * r0, z0) for k in range(seg)]
        v0 = [b2.verts.new(p) for p in pts]
        tip = b2.verts.new((0, 0, z1))
        base = b2.verts.new((0, 0, z0))
        for k in range(seg):
            b2.faces.new((v0[k], v0[(k + 1) % seg], tip))
            b2.faces.new((v0[(k + 1) % seg], v0[k], base))


def leaf_ball(b2, sc):
    cz = 1.40 * sc
    r = 0.70 * sc
    seg = 7
    v_top = b2.verts.new((0, 0, cz + r * 0.95))
    ring_hi = [b2.verts.new((math.cos(k / seg * 2 * math.pi) * r * 0.8, math.sin(k / seg * 2 * math.pi) * r * 0.8, cz + r * 0.35)) for k in range(seg)]
    ring_lo = [b2.verts.new((math.cos(k / seg * 2 * math.pi) * r, math.sin(k / seg * 2 * math.pi) * r, cz - r * 0.3)) for k in range(seg)]
    v_bot = b2.verts.new((0, 0, cz - r * 0.7))
    for k in range(seg):
        b2.faces.new((ring_hi[k], ring_hi[(k + 1) % seg], v_top))
        b2.faces.new((ring_lo[k], v_bot, ring_lo[(k + 1) % seg]))
        b2.faces.new((ring_hi[k], ring_lo[k], ring_hi[(k + 1) % seg]))
        b2.faces.new((ring_lo[(k + 1) % seg], ring_lo[k], ring_hi[(k + 1) % seg]))


def rock_shape(b2, sc):
    seg = 6
    zz = 0.28 * sc
    v_lo = [b2.verts.new((math.cos(k / seg * 2 * math.pi) * 0.5 * sc, math.sin(k / seg * 2 * math.pi) * 0.38 * sc, 0.0)) for k in range(seg)]
    v_hi = [b2.verts.new((math.cos(k / seg * 2 * math.pi + 0.5) * 0.34 * sc, math.sin(k / seg * 2 * math.pi + 0.5) * 0.30 * sc, zz)) for k in range(seg)]
    v_top = b2.verts.new((0.05 * sc, 0, zz + 0.22 * sc))
    for k in range(seg):
        b2.faces.new((v_lo[k], v_lo[(k + 1) % seg], v_hi[(k + 1) % seg], v_hi[k]))
        b2.faces.new((v_hi[k], v_hi[(k + 1) % seg], v_top))
    b2.faces.new(v_lo)


for x, y in placed:
    i = int(round((x - X_MIN) / CELL))
    j = int(round((y - Y_MIN) / CELL))
    z = H[i, j] - 0.15
    s = 0.85 + noise2(x, y) * 0.5
    if noise2(y, x) > 0.45:
        tone = C_PINE_A if noise2(x * 3, y) > 0.5 else C_PINE_B
        emit_part(trunk_only, C_TRUNK, (x, y, z), s * 0.9)
        emit_part(pine_canopy, tone, (x, y, z), s)
    else:
        tone = C_LEAF_A if noise2(x, y * 2) > 0.66 else (C_LEAF_B if noise2(x, y * 2) > 0.33 else C_LEAF_C)
        emit_part(trunk_only, C_TRUNK, (x, y, z), s)
        emit_part(leaf_ball, tone, (x, y, z), s)

for i, j in rock_cells:
    x, y = cell_center(i, j)
    z = H[i, j] - 0.1
    s = 0.5 + noise2(x, y) * 0.7
    emit_part(rock_shape, color_with_noise(C_ROCK, i, j, 0.1), (x, y, z), s)

props_me = bpy.data.meshes.new("ToonProps")
pmb.to_mesh(props_me)
pmb.free()
if props_me.color_attributes:
    props_me.color_attributes.active_color = props_me.color_attributes[0]
props_obj = bpy.data.objects.new("ToonProps", props_me)
bpy.context.collection.objects.link(props_obj)

# ---- preview render ----
scene = bpy.context.scene
scene.render.resolution_x = 1600
scene.render.resolution_y = 1000
scene.render.image_settings.file_format = "PNG"
scene.render.engine = "BLENDER_WORKBENCH"
shading = scene.display.shading
shading.light = "STUDIO"
shading.color_type = "VERTEX"
shading.show_cavity = True
shading.cavity_type = "BOTH"
shading.show_shadows = True
shading.shadow_intensity = 0.4


def add_camera(name, location, target, lens=28):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    direction = Vector(target) - Vector(location)
    obj.location = location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return obj


scene.camera = add_camera("Preview", (16.0, -20.0, 18.0), (-2.0, -0.5, 0.0), lens=35)
scene.render.filepath = str(PREVIEW)
bpy.ops.render.render(write_still=True)
print("RENDERED preview")

scene.camera = add_camera("PreviewValley", (8.4, -4.5, 6.1), (-2.0, 0.0, 1.5), lens=30)
scene.render.filepath = str(ROOT / "tools/renders/toon_valley_preview.png")
bpy.ops.render.render(write_still=True)
print("RENDERED valley preview")


def export(obj, path):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", export_yup=True, use_selection=True)


export(terrain_obj, OUT_TERRAIN)
export(props_obj, OUT_PROPS)
print("WROTE", OUT_TERRAIN)
print("WROTE", OUT_PROPS)
