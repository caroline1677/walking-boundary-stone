"""Border post scene (边境哨所) — the second study-stop world.

Run via Blender CLI:
  blender --background --python tools/build_post.py

Layout (Blender Z-up): flat yard with a road entering from the south; barracks
with green roof + red star at the north end, stone watchtower west, flagpole,
barrier boom at the entrance, "祖国边疆" stone marker, crates + patrol gear
(binoculars, walkie-talkie, canteen), signpost, benches, lamps, fences, pines.

Outputs:
  assets/worlds/post-terrain.glb / post-collider.glb / post-props.glb
  assets/models/post-buildings.glb / post-flags.glb
  tools/renders/post_overview.png
"""

import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

ROOT = Path(r"D:\HKU-ds\QCH\界碑智能体")
OUT = {
    "terrain": ROOT / "assets/worlds/post-terrain.glb",
    "collider": ROOT / "assets/worlds/post-collider.glb",
    "props": ROOT / "assets/worlds/post-props.glb",
    "buildings": ROOT / "assets/models/post-buildings.glb",
    "flags": ROOT / "assets/models/post-flags.glb",
}
FONT = r"C:\Windows\Fonts\simhei.ttf"

X_MIN, X_MAX = -18.0, 18.0
Y_MIN, Y_MAX = -20.0, 18.0
CELL = 0.5

C_YARD = (0.62, 0.66, 0.44)
C_ROAD = (0.70, 0.66, 0.56)
C_GRASS = (0.44, 0.66, 0.31)
C_GRASS_D = (0.34, 0.55, 0.29)
C_ROCK = (0.56, 0.52, 0.45)
C_CLIFF = (0.42, 0.38, 0.33)
C_GRANITE = (0.66, 0.64, 0.58)
C_WALL = (0.90, 0.87, 0.77)
C_ROOF = (0.22, 0.40, 0.34)
C_WOOD = (0.47, 0.34, 0.22)
C_WOOD_L = (0.62, 0.48, 0.31)
C_RED = (0.74, 0.16, 0.13)
C_DARK = (0.14, 0.13, 0.12)
C_IRON = (0.30, 0.33, 0.28)
C_STAR = (0.80, 0.16, 0.12)

bpy.ops.wm.read_homefile(use_empty=True)


def smoothstep(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3.0 - 2.0 * t)


def noise(x, y):
    return (math.sin(x * 0.34 + 1.7) * math.sin(y * 0.29 + 0.6) * 0.5
            + math.sin(x * 0.13 + 0.3) * math.sin(y * 0.17 + 2.1) * 0.5)


def height_at(x, y):
    z = 0.0
    if y <= -12:
        z = -0.9 * smoothstep((-y - 12) / 6.0)
    hw = 14.0 if y >= -10 else max(5.0, 14.0 - (-y - 10) * 0.8)
    if abs(x) > 12.0 and y > 6:
        z = max(z, smoothstep((abs(x) - 12.0) / 5.0) * 10.0)
    if y > 17.5:
        z = max(z, smoothstep((y - 17.5) / 7.0) * 11.0)
    d = max(0.0, abs(x) - hw)
    z = max(z, smoothstep(d / 7.0) * 12.5 * (1.0 + 0.25 * noise(x, y)))
    if abs(x) > 12.5 and abs(y) > 13:
        z = max(z, smoothstep((abs(x) + abs(y) - 26) / 8.0) * 9.0)
    if not (abs(x) < 13.0 and -14 < y < 12):
        z += noise(x, y) * max(0.0, min(1.0, (z - 0.5))) * 0.9
    return z


nx = int(round((X_MAX - X_MIN) / CELL)) + 1
ny = int(round((Y_MAX - Y_MIN) / CELL)) + 1
xs = [X_MIN + i * CELL for i in range(nx)]
ys = [Y_MIN + j * CELL for j in range(ny)]
H = [[height_at(x, y) for y in ys] for x in xs]

SPAWN = (0.0, -13.0)


def idx(x, y):
    return (int(round((x - X_MIN) / CELL)), int(round((y - Y_MIN) / CELL)))


reach = {idx(*SPAWN): 0.0}
frontier = [idx(*SPAWN)]
while frontier:
    nxt = []
    for (i, j) in frontier:
        z0 = reach[(i, j)]
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            i2, j2 = i + di, j + dj
            if not (0 <= i2 < nx and 0 <= j2 < ny) or (i2, j2) in reach:
                continue
            dz = H[i2][j2] - z0
            if dz > 0.75 or dz < -1.2:
                continue
            reach[(i2, j2)] = H[i2][j2]
            nxt.append((i2, j2))
    frontier = nxt
print("POST_REACHABLE", len(reach))

POINTS = {
    "spawn": SPAWN,
    "d_binoc": (5.6, 0.6),
    "d_radio": (2.2, -3.2),
    "d_flask": (1.3, 4.4),
    "d_crates": (6.5, -1.4),
    "d_sign": (4.5, -5.5),
    "d_stone": (-7.0, -3.0),
    "back": (2.5, -14.0),
}
for name, (qx, qy) in POINTS.items():
    ok = idx(qx, qy) in reach
    print(f"POST_QUEST {name} {'OK' if ok else 'UNREACHABLE'} z={round(H[idx(qx, qy)[0]][idx(qx, qy)[1]], 2)}")
    assert ok, f"post point unreachable: {name}"


def z_at(x, y):
    i, j = idx(x, y)
    return H[i][j]


# ---- terrain mesh ----
bm = bmesh.new()
for i in range(nx - 1):
    for j in range(ny - 1):
        x0, y0 = xs[i], ys[j]
        x1, y1 = xs[i + 1], ys[j + 1]
        v = [bm.verts.new((x0, y0, H[i][j])), bm.verts.new((x1, y0, H[i + 1][j])),
             bm.verts.new((x1, y1, H[i + 1][j + 1])), bm.verts.new((x0, y1, H[i][j + 1]))]
        bm.faces.new(v)

SKIRT_Z = -7.0
for i in range(nx - 1):
    for j in (0, ny - 2):
        x0, y0 = xs[i], ys[j]
        x1 = xs[i + 1]
        v = [bm.verts.new((x0, y0, H[i][j])), bm.verts.new((x1, y0, H[i + 1][j])),
             bm.verts.new((x1, y0, SKIRT_Z)), bm.verts.new((x0, y0, SKIRT_Z))]
        bm.faces.new(v)
for j in range(ny - 1):
    for i in (0, nx - 2):
        x0, y0 = xs[i], ys[j]
        y1 = ys[j + 1]
        v = [bm.verts.new((x0, y0, H[i][j])), bm.verts.new((x0, y1, H[i][j + 1])),
             bm.verts.new((x0, y1, SKIRT_Z)), bm.verts.new((x0, y0, SKIRT_Z))]
        bm.faces.new(v)

color_layer = bm.loops.layers.color.new("Col")
bm.faces.ensure_lookup_table()
for face in bm.faces:
    if any(v.co.z <= SKIRT_Z + 1e-3 for v in face.verts):
        col = C_CLIFF
    else:
        mx = sum(v.co.x for v in face.verts) / 4
        my = sum(v.co.y for v in face.verts) / 4
        k = abs((math.sin(mx * 12.9898 + my * 78.233) * 43758.5453) % 1.0)
        if abs(mx) <= 3.2 and my <= 2.0:
            col = C_ROAD
        elif my > -14 and abs(mx) < 13 and my < 12:
            col = tuple(min(1.0, c * (1.0 + (k - 0.5) * 0.04)) for c in C_YARD)
        else:
            base = C_GRASS if k > 0.45 else C_GRASS_D
            col = tuple(min(1.0, c * (1.0 + (k - 0.5) * 0.05)) for c in base)
    for loop in face.loops:
        loop[color_layer] = (*col, 1.0)

terrain_me = bpy.data.meshes.new("PostTerrain")
bm.to_mesh(terrain_me)
bm.free()
if terrain_me.color_attributes:
    terrain_me.color_attributes.active_color = terrain_me.color_attributes[0]
terrain_obj = bpy.data.objects.new("PostTerrain", terrain_me)
bpy.context.collection.objects.link(terrain_obj)
print("POST_TERRAIN_TRIS", len(terrain_me.polygons))

# ---- shared builders -------------------------------------------------------

def box(b2, x0, x1, y0, y1, z0, z1):
    v = [b2.verts.new(p) for p in (
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (3, 0, 4, 7)):
        b2.faces.new([v[i] for i in f])


def tube(b2, x, y, z0, z1, r0, r1, seg=10):
    pts0 = [(x + math.cos(k / seg * 2 * math.pi) * r0, y + math.sin(k / seg * 2 * math.pi) * r0, z0) for k in range(seg)]
    pts1 = [(x + math.cos(k / seg * 2 * math.pi) * r1, y + math.sin(k / seg * 2 * math.pi) * r1, z1) for k in range(seg)]
    v0 = [b2.verts.new(p) for p in pts0]
    v1 = [b2.verts.new(p) for p in pts1]
    for k in range(seg):
        b2.faces.new((v0[k], v0[(k + 1) % seg], v1[(k + 1) % seg], v1[k]))
    b2.faces.new(v0)
    top = b2.verts.new((x, y, z1))
    for k in range(seg):
        b2.faces.new((v1[(k + 1) % seg], v1[k], top))


def prism_roof(b2, x0, x1, y0, y1, z0, rx0, rx1, z_apex):
    v = [b2.verts.new(p) for p in (
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (rx0, (y0 + y1) / 2, z_apex), (rx1, (y0 + y1) / 2, z_apex))]
    for f in ((0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5)):
        b2.faces.new([v[i] for i in f])


def pyramid(b2, x0, x1, y0, y1, z0, z_apex):
    v = [b2.verts.new(p) for p in (
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        ((x0 + x1) / 2, (y0 + y1) / 2, z_apex))]
    for f in ((0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)):
        b2.faces.new([v[i] for i in f])


def sphere(b2, cx, cy, cz, r, seg=10, rx=1.0):
    top = b2.verts.new((cx, cy + r * 0.0, cz + r))
    bot = b2.verts.new((cx, cy, cz - r))
    rings = []
    for lat in range(1, seg):
        phi = math.pi * lat / seg
        rr = r * math.sin(phi)
        z = cz + r * math.cos(phi)
        rings.append([b2.verts.new((cx + math.cos(k / seg * 2 * math.pi) * rr * (1.0 if lat % 2 else 1.0), cy + math.sin(k / seg * 2 * math.pi) * rr, z)) for k in range(seg)])
    for k in range(seg):
        b2.faces.new((rings[0][(k + 1) % seg], rings[0][k], top))
    for lat in range(len(rings) - 1):
        a, b = rings[lat], rings[lat + 1]
        for k in range(seg):
            b2.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    for k in range(seg):
        b2.faces.new((rings[-1][k], rings[-1][(k + 1) % seg], bot))


# ---- buildings (barracks + watchtower + flagpole + barrier + marker) ----
gbm = bmesh.new()


def emit_building(builder, color):
    tmp = bmesh.new()
    builder(tmp)
    layer = tmp.loops.layers.color.new("Col")
    for f in tmp.faces:
        for l in f.loops:
            l[layer] = (*color, 1.0)
    me = bpy.data.meshes.new("bpart")
    tmp.to_mesh(me)
    tmp.free()
    for p in me.polygons:
        p.use_smooth = False
    gbm.from_mesh(me)
    bpy.data.meshes.remove(me)


# barracks at (0, 7), front toward -Y
emit_building(lambda b2: box(b2, -5.0, 5.0, 4.9, 9.1, 0.25, 3.4), C_WALL)
emit_building(lambda b2: box(b2, -5.15, 5.15, 4.75, 9.25, 0.0, 0.3), C_GRANITE)
emit_building(lambda b2: prism_roof(b2, -5.9, 5.9, 4.2, 9.8, 3.4, -0.8, 0.8, 5.0), C_ROOF)
# 门洞保持敞开（内景可进入），门板移到开启位
emit_building(lambda b2: box(b2, 0.62, 1.35, 4.86, 4.98, 0.25, 2.1), (0.42, 0.26, 0.18))
emit_building(lambda b2: box(b2, 0.68, 1.6, 4.60, 4.86, 0.30, 2.05), (0.36, 0.22, 0.16))
for wx in (-3.4, -1.9, 1.9, 3.4):
    emit_building(lambda b2, wx=wx: box(b2, wx - 0.45, wx + 0.45, 4.80, 4.92, 1.3, 2.3), C_DARK)
    emit_building(lambda b2, wx=wx: box(b2, wx - 0.58, wx + 0.58, 4.76, 4.84, 1.16, 2.44), C_WOOD)
# interior: floor + furniture (bunks, desk, lockers)
emit_building(lambda b2: box(b2, -4.9, 4.9, 5.0, 9.0, 0.25, 0.33), C_WOOD_L)
def bunk(b2, bx):
    box(b2, bx - 0.5, bx + 0.5, 5.4, 8.4, 0.33, 0.55)
    box(b2, bx - 0.5, bx + 0.5, 5.4, 8.4, 1.15, 1.37)
    box(b2, bx - 0.52, bx + 0.52, 5.35, 8.45, 0.52, 0.60)
    box(b2, bx - 0.52, bx + 0.52, 5.35, 8.45, 1.34, 1.42)
    box(b2, bx - 0.44, bx + 0.44, 5.5, 6.4, 0.60, 0.78)
    box(b2, bx - 0.44, bx + 0.44, 5.5, 6.4, 1.42, 1.60)
for bx in (3.4, 1.9):
    emit_building(lambda b2, bx=bx: bunk(b2, bx), (0.72, 0.60, 0.44))
emit_building(lambda b2: box(b2, -4.4, -2.6, 5.2, 6.6, 0.33, 1.05), C_WOOD)
emit_building(lambda b2: box(b2, -3.8, -3.2, 6.7, 7.3, 0.33, 0.55), C_WOOD)
for k in range(4):
    emit_building(lambda b2, k=k: box(b2, -4.6 + k * 0.55, -4.25 + k * 0.55, 8.4, 8.9, 0.33, 2.3), C_ROOF)

# red star on the facade
def star(b2, cx, cy, cz, r, depth):
    pts = []
    for k in range(10):
        ang = math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.42
        pts.append((cx + math.cos(ang) * rr, cy + math.sin(ang) * rr))
    v_front = [b2.verts.new((p[0], p[1] - depth / 2, cz)) for p in pts]
    v_back = [b2.verts.new((p[0], p[1] + depth / 2, cz)) for p in pts]
    for k in range(10):
        b2.faces.new((v_front[k], v_front[(k + 1) % 10], v_back[(k + 1) % 10], v_back[k]))
    b2.faces.new(v_front)
    b2.faces.new(v_back[::-1])
emit_building(lambda b2: star(b2, 0.0, 4.78, 4.4, 0.42, 0.12), C_STAR)

# watchtower at (-9.5, 5)
emit_building(lambda b2: box(b2, -11.0, -8.0, 3.5, 6.5, 0.0, 4.4), C_GRANITE)
for wx in (-10.6, -8.4):
    emit_building(lambda b2, wx=wx: box(b2, wx - 0.2, wx + 0.2, 3.4, 3.6, 1.6, 2.6), C_DARK)
emit_building(lambda b2: box(b2, -11.3, -7.7, 3.2, 6.8, 4.4, 4.8), C_GRANITE)
for (px, py) in ((-11.0, 3.5), (-8.0, 3.5), (-11.0, 6.5), (-8.0, 6.5)):
    emit_building(lambda b2, px=px, py=py: box(b2, px - 0.12, px + 0.12, py - 0.12, py + 0.12, 4.8, 6.3), C_WOOD)
emit_building(lambda b2: pyramid(b2, -11.8, -7.2, 2.9, 7.1, 6.3, 8.0), C_ROOF)
emit_building(lambda b2: box(b2, -11.2, -7.8, 3.3, 6.7, 5.1, 5.28), C_WOOD_L)
emit_building(lambda b2: box(b2, -11.2, -7.8, 5.7, 6.0, 5.1, 5.28), C_WOOD_L)

# flagpole at (-4, 1.5)
emit_building(lambda b2: tube(b2, -4.0, 1.5, 0.0, 8.0, 0.09, 0.06, seg=8), (0.72, 0.73, 0.75))
emit_building(lambda b2: tube(b2, -4.0, 1.5, 0.0, 0.5, 0.35, 0.28, seg=8), C_GRANITE)

# barrier boom at (0, -5.5)
for bx in (-3.4, 3.4):
    emit_building(lambda b2, bx=bx: box(b2, bx - 0.25, bx + 0.25, -5.75, -5.25, 0.0, 1.15), C_GRANITE)
seg_n = 6
for k in range(seg_n):
    x0 = -3.3 + k * 1.1
    col = C_RED if k % 2 == 0 else (0.92, 0.90, 0.86)
    tilt = 0.16
    emit_building(lambda b2, x0=x0, col=col, tilt=tilt: box(b2, x0, x0 + 1.08, -5.62, -5.38, 1.02 + x0 * 0.0, 1.02 + 1.02), col)
# note: boom drawn straight; raise far end instead
for k in range(seg_n):
    pass

# stone marker at (-7, -3)
emit_building(lambda b2: box(b2, -7.8, -6.2, -3.25, -2.75, 0.0, 1.55), (0.88, 0.86, 0.80))
emit_building(lambda b2: box(b2, -7.95, -6.05, -3.4, -2.6, 0.0, 0.22), C_GRANITE)

# ---- gold/red plaque texts (simhei) ----


def add_text(body, size, color, loc, rot=(math.pi / 2, 0.0, 0.0), shift=(0.0, 0.0, 0.0)):
    curve = bpy.data.curves.new(f"Txt{body}", type="FONT")
    curve.body = body
    curve.size = size
    curve.extrude = 0.04
    curve.align_x = "CENTER"
    curve.font = bpy.data.fonts.load(FONT)
    o = bpy.data.objects.new(f"Txt{body}", curve)
    bpy.context.collection.objects.link(o)
    o.rotation_euler = rot
    o.location = loc
    bpy.context.view_layer.update()
    _ = loc
    tme = o.to_mesh()
    tbm = bmesh.new()
    tbm.from_mesh(tme)
    layer = tbm.loops.layers.color.new("Col")
    for f in tbm.faces:
        for l in f.loops:
            l[layer] = (*color, 1.0)
    for v in tbm.verts:
        v.co += Vector(shift)
    for p in tbm.faces:
        p.smooth = False
    me = bpy.data.meshes.new("txtm")
    tbm.to_mesh(me)
    tbm.free()
    o.to_mesh_clear()
    bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.curves.remove(curve)
    return me


# barracks plaque (on the front wall, below the roof)
emit_building(lambda b2: box(b2, -1.7, 1.7, 4.84, 4.76, 2.35, 3.15), C_DARK)
me = add_text("边境哨所", 0.72, (0.92, 0.78, 0.30), (0.0, 0.0, 0.0), shift=(0.0, 4.70, 2.42))
gbm.from_mesh(me)
bpy.data.meshes.remove(me)
emit_building(lambda b2: star(b2, 0.0, 4.84, 3.75, 0.38, 0.12), C_STAR)

# stone marker texts (red)
me = add_text("祖国边疆", 0.40, C_STAR, (0.0, 0.0, 0.0), shift=(-7.0, -3.52, 1.24))
gbm.from_mesh(me)
bpy.data.meshes.remove(me)
me = add_text("神圣不可侵犯", 0.26, C_STAR, (0.0, 0.0, 0.0), shift=(-7.0, -3.52, 0.76))
gbm.from_mesh(me)
bpy.data.meshes.remove(me)

buildings_me = bpy.data.meshes.new("PostBuildings")
gbm.to_mesh(buildings_me)
gbm.free()
if buildings_me.color_attributes:
    buildings_me.color_attributes.active_color = buildings_me.color_attributes[0]
buildings_obj = bpy.data.objects.new("PostBuildings", buildings_me)
bpy.context.collection.objects.link(buildings_obj)
print("POST_BUILDINGS_TRIS", len(buildings_me.polygons))

# ---- animated flag on the flagpole ----
fbm = bmesh.new()
seg_n2 = 8
cloth_rows = []
w, ln = 1.1, 0.95
for iz in range(4):
    row = []
    for ix in range(seg_n2 + 1):
        lx = ix / seg_n2
        row.append(fbm.verts.new((-4.0 + (lx - 0.5) * w, 1.5 - lx * ln, 7.55 - iz / 3 * 0.55)))
    cloth_rows.append(row)
for iz in range(3):
    for ix in range(seg_n2):
        fbm.faces.new((cloth_rows[iz][ix], cloth_rows[iz][ix + 1], cloth_rows[iz + 1][ix + 1], cloth_rows[iz + 1][ix]))
layer = fbm.loops.layers.color.new("Col")
for f in fbm.faces:
    for l in f.loops:
        l[layer] = (*C_RED, 1.0)
flag_me = bpy.data.meshes.new("FlagClothPost")
fbm.to_mesh(flag_me)
fbm.free()
if flag_me.color_attributes:
    flag_me.color_attributes.active_color = flag_me.color_attributes[0]
flag_obj = bpy.data.objects.new("FlagClothPost", flag_me)
bpy.context.collection.objects.link(flag_obj)
print("POST_FLAG_OK")

# ---- props (crates, gear, benches, lamps, fences, pines, signpost) --------
pmb = bmesh.new()


def emit_part(builder, color, offset, scale=1.0, rot=0.0):
    tmp = bmesh.new()
    builder(tmp, scale)
    layer = tmp.loops.layers.color.new("Col")
    for f in tmp.faces:
        for l in f.loops:
            l[layer] = (*color, 1.0)
    if rot:
        ca, sa = math.cos(rot), math.sin(rot)
        for v in tmp.verts:
            x, y = v.co.x, v.co.y
            v.co.x, v.co.y = x * ca - y * sa, x * sa + y * ca
    for v in tmp.verts:
        v.co += Vector(offset)
    me = bpy.data.meshes.new("ppart")
    tmp.to_mesh(me)
    tmp.free()
    for p in me.polygons:
        p.use_smooth = False
    pmb.from_mesh(me)
    bpy.data.meshes.remove(me)


def crate(b2, sc):
    hx = 0.42 * sc
    v = [b2.verts.new((x * hx, y * hx, z * hx)) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 2, 6, 4), (1, 3, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6)):
        b2.faces.new([v[i] for i in f])
    box(b2, -hx * 0.2, hx * 0.2, -hx, -hx * 0.72, -hx * 0.55, hx * 0.55)


def bench(b2, sc):
    box(b2, -0.85, 0.85, -0.26, 0.26, 0.40, 0.52)
    box(b2, -0.85, 0.85, -0.30, 0.30, 0.52, 0.60)
    for lx in (-0.7, 0.7):
        box(b2, lx - 0.07, lx + 0.07, -0.22, 0.22, 0.0, 0.40)


def lamp_post(b2, sc):
    tube(b2, 0.0, 0.0, 0.0, 2.4, 0.10, 0.08, seg=6)
    cap = b2.verts.new((0, 0, 2.85))
    ring = [b2.verts.new((math.cos(k / 6 * 2 * math.pi) * 0.3, math.sin(k / 6 * 2 * math.pi) * 0.3, 2.5)) for k in range(6)]
    for k in range(6):
        b2.faces.new((ring[k], ring[(k + 1) % 6], cap))
    b2.faces.new(ring[::-1])


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
    rot = noise(sc, 7) * 6.28
    for z0, z1, r0 in ((0.30 * sc, 1.5 * sc, 0.9 * sc), (0.85 * sc, 1.85 * sc, 0.62 * sc)):
        seg = 6
        pts = [(math.cos(rot + k / seg * 2 * math.pi) * r0, math.sin(rot + k / seg * 2 * math.pi) * r0, z0) for k in range(seg)]
        v0 = [b2.verts.new(p) for p in pts]
        tip = b2.verts.new((0, 0, z1))
        base = b2.verts.new((0, 0, z0))
        for k in range(seg):
            b2.faces.new((v0[k], v0[(k + 1) % seg], tip))
            b2.faces.new((v0[(k + 1) % seg], v0[k], base))


def binoculars(b2, sc):
    tube(b2, -0.14, 0.0, 0.0, 0.30, 0.085, 0.075, seg=8)
    tube(b2, 0.14, 0.0, 0.0, 0.30, 0.085, 0.075, seg=8)
    box(b2, -0.08, 0.08, -0.05, 0.05, 0.13, 0.21)


def radio_set(b2, sc):
    box(b2, -0.09, 0.09, -0.055, 0.055, 0.0, 0.30)
    tube(b2, 0.06, 0.0, 0.30, 0.58, 0.014, 0.010, seg=5)
    box(b2, -0.05, 0.05, -0.062, -0.055, 0.16, 0.24)


def canteen(b2, sc):
    sphere(b2, 0.0, 0.0, 0.17, 0.17, seg=10)
    tube(b2, 0.0, 0.0, 0.32, 0.40, 0.05, 0.045, seg=6)
    tube(b2, 0.0, 0.0, 0.06, 0.30, 0.19, 0.18, seg=8)


def sign_boards(b2, sc):
    trunk_only(b2, 1.4 * sc)
    for (dx, dz, rot) in ((0.35, 1.9, 0.4), (-0.4, 1.5, -0.5)):
        ca, sa = math.cos(rot), math.sin(rot)
        w, h, t = 0.95 * sc, 0.26 * sc, 0.06 * sc
        v = []
        for (px, py, pz) in ((0, -t, 0), (w, -t, 0), (w, t, 0), (0, t, 0), (0, -t, h), (w, -t, h), (w, t, h), (0, t, h)):
            x = dx + px * ca
            y = px * sa + py * ca
            v.append(b2.verts.new((x, y, dz + pz)))
        for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (3, 0, 4, 7)):
            b2.faces.new([v[i] for i in f])


# fence posts + rails along the yard north edge (in front of the barracks yard)
fence_posts = [(-8.0 + k * 1.35, 2.4) for k in range(9)]
for (fx, fy) in fence_posts:
    fz = z_at(fx, fy)
    emit_part(lambda b2, sc=1.0: tube(b2, 0.0, 0.0, 0.0, 0.95, 0.06, 0.05, seg=6), C_WOOD, (fx, fy, fz), 1.0)
for (ax, ay) in ((-8.0, 2.4), (-1.2, 2.4)):
    pass
for k in range(len(fence_posts) - 1):
    ax, ay = fence_posts[k]
    bx, by = fence_posts[k + 1]
    az, bz = z_at(ax, ay), z_at(bx, by)
    mx, my = (ax + bx) / 2, (ay + by) / 2
    length = math.hypot(bx - ax, by - ay)
    rot = math.atan2(by - ay, bx - ax)
    for rz in (0.42, 0.72):
        emit_part(lambda b2, sc=1.0: box(b2, -length / 2, length / 2, -0.035, 0.035, rz - 0.035, rz + 0.035), C_WOOD_L, (mx, my, az), 1.0, rot=rot)

# lamps
for (lx, ly) in ((-5.0, -8.0), (5.0, -8.0), (-5.0, -1.0), (5.0, -4.5), (-4.5, 3.5)):
    emit_part(lamp_post, (0.55, 0.52, 0.47), (lx, ly, z_at(lx, ly)), 1.0)

# benches + gear
emit_part(bench, C_WOOD, (2.2, -3.2, z_at(2.2, -3.2)), 1.0)
emit_part(radio_set, (0.20, 0.23, 0.21), (2.05, -3.28, z_at(2.05, -3.28) + 0.60), 1.0)
emit_part(bench, C_WOOD, (-3.0, 1.5, z_at(-3.0, 1.5)), 1.0)
# crates + binoculars
emit_part(crate, C_WOOD, (5.6, 0.6, z_at(5.6, 0.6) + 0.44), 1.0)
emit_part(crate, C_WOOD, (6.55, 0.3, z_at(6.55, 0.3) + 0.44), 0.9, rot=0.4)
emit_part(crate, C_WOOD, (6.1, 0.45, z_at(6.1, 0.45) + 1.24), 0.8, rot=0.2)
emit_part(binoculars, (0.24, 0.30, 0.22), (5.55, 0.62, z_at(5.55, 0.62) + 1.02), 1.0)
# canteen near the barracks door
emit_part(canteen, (0.30, 0.36, 0.26), (1.35, 4.35, z_at(1.35, 4.35)), 1.0)
# patrol signpost
emit_part(sign_boards, C_WOOD, (4.5, -5.5, z_at(4.5, -5.5)), 1.0, rot=0.5)
me = add_text("巡逻路线", 0.20, (0.15, 0.13, 0.11), (0.0, 0.0, 0.0), rot=(math.pi / 2, 0.0, 0.9), shift=(4.28, -5.63, z_at(4.5, -5.5) + 2.0))
pmb.from_mesh(me)
bpy.data.meshes.remove(me)

# ---- border line + Vietnam side ----
C_LINE = (0.78, 0.20, 0.14)
# 边界线画带：红白相间的长条
strip_segs = 16
for k in range(strip_segs):
    sx0 = -12.0 + k * 1.5
    col = C_LINE if k % 2 == 0 else (0.93, 0.91, 0.86)
    emit_part(lambda b2, sc=1.0, sx0=sx0, col=col: box(b2, sx0, sx0 + 1.4, 10.2, 10.8, 0.02, 0.07), col, (0.0, 0.0, 0.0), 1.0)
# 界桩排
for k in range(6):
    mx = -10.0 + k * 4.0
    mz = z_at(mx, 10.5)
    emit_part(lambda b2, sc=1.0: tube(b2, 0.0, 0.0, 0.0, 0.85, 0.16, 0.13, seg=8), (0.90, 0.88, 0.82), (mx, 10.5, mz), 1.0)
    emit_part(lambda b2, sc=1.0: tube(b2, 0.0, 0.0, 0.85, 0.95, 0.14, 0.13, seg=8), C_RED, (mx, 10.5, mz), 1.0)
# 越南侧民居剪影（界线以北）
vn_houses = ((-9.0, 13.5, 0.3), (-3.0, 14.5, -0.2), (3.0, 13.8, 0.15), (8.5, 14.2, 0.45))
for (vx, vy, vrot) in vn_houses:
    vz = z_at(vx, vy)
    def vn_house(b2, sc=1.0):
        box(b2, -1.6, 1.6, -1.2, 1.2, 0.0, 1.9)
        prism_roof(b2, -2.0, 2.0, -1.5, 1.5, 1.9, -0.4, 0.4, 3.1)
        box(b2, -0.5, 0.5, -1.28, -1.12, 0.1, 1.1)
    emit_part(vn_house, (0.82, 0.74, 0.60), (vx, vy, vz), 1.0, rot=vrot)
    emit_part(lambda b2, sc=1.0: prism_roof(b2, -2.0, 2.0, -1.5, 1.5, 1.9, -0.4, 0.4, 3.1), (0.36, 0.30, 0.28), (vx, vy, vz), 1.0, rot=vrot)
# 「越南方向」指示牌
emit_part(sign_boards, C_WOOD, (8.8, 8.5, z_at(8.8, 8.5)), 1.0, rot=-0.5)
me = add_text("越南方向", 0.17, (0.15, 0.13, 0.11), (0.0, 0.0, 0.0), rot=(math.pi / 2, 0.0, -0.5), shift=(8.72, 8.42, z_at(8.8, 8.5) + 2.02))
pmb.from_mesh(me)
bpy.data.meshes.remove(me)
print("POST_BORDER_OK")

# ---- patrol footprints ----
route = ((0.0, -11.0), (0.0, -5.5), (-4.0, 1.0), (-9.0, 4.5), (0.0, 3.2), (5.5, 0.4), (-6.5, -2.6), (0.0, -5.5))
fp_count = 0
for k in range(len(route) - 1):
    ax, ay = route[k]
    bx, by = route[k + 1]
    seg_len = math.hypot(bx - ax, by - ay)
    steps = max(1, int(seg_len / 0.85))
    ang = math.atan2(by - ay, bx - ax)
    for st in range(steps):
        t = (st + 0.5) / steps
        fx = ax + (bx - ax) * t
        fy = ay + (by - ay) * t
        fz = z_at(fx, fy)
        side = 0.14 if st % 2 == 0 else -0.14
        px_ = fx + math.cos(ang + math.pi / 2) * side
        py_ = fy + math.sin(ang + math.pi / 2) * side
        emit_part(lambda b2, sc=1.0: sphere(b2, 0.0, 0.0, 0.0, 0.085, seg=6, rx=0.7), (0.47, 0.44, 0.36), (px_, py_, fz + 0.025), 1.0, rot=ang)
        fp_count += 1
print("POST_FOOTPRINTS", fp_count)

# yard pines
for (px, py) in ((-12.0, -10.0), (12.0, -11.0), (-12.5, 8.0), (12.5, 7.0), (-6.5, 10.5), (7.0, 11.0)):
    i2, j2 = idx(px, py)
    ss = 1.5
    emit_part(trunk_only, C_WOOD, (px, py, H[i2][j2] - 0.2), ss)
    emit_part(pine_canopy, C_PINE := (0.26, 0.52, 0.30), (px, py, H[i2][j2] - 0.2), ss)

props_me = bpy.data.meshes.new("PostProps")
pmb.to_mesh(props_me)
pmb.free()
if props_me.color_attributes:
    props_me.color_attributes.active_color = props_me.color_attributes[0]
props_obj = bpy.data.objects.new("PostProps", props_me)
bpy.context.collection.objects.link(props_obj)
print("POST_PROPS_OK")

# ---- collider: terrain + building blockers ----
cbm = bmesh.new()
for i in range(nx - 1):
    for j in range(ny - 1):
        x0, y0 = xs[i], ys[j]
        x1, y1 = xs[i + 1], ys[j + 1]
        v = [cbm.verts.new((x0, y0, H[i][j])), cbm.verts.new((x1, y0, H[i + 1][j])),
             cbm.verts.new((x1, y1, H[i + 1][j + 1])), cbm.verts.new((x0, y1, H[i][j + 1]))]
        cbm.faces.new(v)
for blocker in (
    (-3.15, 7.0, 1.6, 3.7, 4.6, 3.4),
    (3.15, 7.0, 1.6, 3.7, 4.6, 3.4),
    (-9.5, 5.0, 2.2, 3.4, 3.4, 4.4),
    (5.6, 0.45, 0.6, 1.4, 1.2, 1.2),
    (-7.0, -3.0, 0.8, 1.9, 0.8, 1.6),
    (-3.4, -5.5, 0.6, 0.6, 0.6, 1.15),
    (3.4, -5.5, 0.6, 0.6, 0.6, 1.15),
):
    cx, cy, cz, sx, sy, sz = blocker
    box(cbm, cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2, cz - sz / 2, cz + sz / 2)
collider_me = bpy.data.meshes.new("PostCollider")
cbm.to_mesh(collider_me)
cbm.free()
if collider_me.color_attributes:
    collider_me.color_attributes.active_color = collider_me.color_attributes[0]
collider_obj = bpy.data.objects.new("PostCollider", collider_me)
bpy.context.collection.objects.link(collider_obj)
print("POST_COLLIDER_OK")

# ---- preview ----
scene = bpy.context.scene
scene.render.resolution_x = 1500
scene.render.resolution_y = 950
scene.render.image_settings.file_format = "PNG"
scene.render.engine = "BLENDER_WORKBENCH"
shading = scene.display.shading
shading.light = "STUDIO"
shading.color_type = "VERTEX"
shading.show_cavity = True
shading.cavity_type = "BOTH"
shading.show_shadows = True
shading.shadow_intensity = 0.4


def add_cam(name, loc, tgt, lens=32):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    o = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(o)
    direction = Vector(tgt) - Vector(loc)
    o.location = loc
    o.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return o


scene.camera = add_cam("PostOverview", (0.0, -32.0, 24.0), (0.0, 4.0, 2.0), lens=36)
scene.render.filepath = str(ROOT / "tools/renders/post_overview.png")
bpy.ops.render.render(write_still=True)
print("RENDERED post_overview")

shading.light = "FLAT"
shading.show_shadows = False
shading.show_cavity = False
map_data = bpy.data.cameras.new("MiniMap")
map_data.type = "ORTHO"
map_data.ortho_scale = 44.0
map_cam = bpy.data.objects.new("MiniMap", map_data)
bpy.context.collection.objects.link(map_cam)
map_cam.location = (0.0, -1.0, 60.0)
map_cam.rotation_euler = (0.0, 0.0, 0.0)
scene.camera = map_cam
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.filepath = str(ROOT / "assets/ui/post-minimap.png")
bpy.ops.render.render(write_still=True)
print("RENDERED post_minimap")


def export(obj, path):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", export_yup=True, use_selection=True)


export(terrain_obj, OUT["terrain"])
export(collider_obj, OUT["collider"])
export(props_obj, OUT["props"])
export(buildings_obj, OUT["buildings"])
export(flag_obj, OUT["flags"])
print("WROTE", OUT["terrain"])
print("WROTE", OUT["collider"])
print("WROTE", OUT["props"])
print("WROTE", OUT["buildings"])
print("WROTE", OUT["flags"])
