"""Friendship Pass v2 — authored diorama world built from the reference photos.

Run via Blender CLI:
  blender --background --python tools/build_world_v2.py

Composition (Blender Z-up, gate at origin, axis along -Y):
  stone plaza (y -26..-2) -> gate citadel at y 0 -> pass floor rising north,
  mountain masses flanking the axis and behind the gate, east wall-walk ridge
  climbing from the citadel, boundary-stone courtyard east of the plaza.

Outputs (all vertex-colored, flat shaded):
  assets/worlds/pass-v2-terrain.glb    walkable visual terrain
  assets/worlds/pass-v2-collider.glb   terrain + blocker boxes (invisible)
  assets/worlds/pass-v2-props.glb      trees, lamps, banners, signpost, boxes
  tools/renders/v2_overview.png / v2_axis.png
  prints V2_* diagnostics; quest reachability is ASSERTED
"""

import json
import math
from pathlib import Path

import bmesh
import numpy as np
import bpy
from mathutils import Vector

ROOT = Path(r"D:\HKU-ds\QCH\界碑智能体")
OUT_TERRAIN = ROOT / "assets/worlds/pass-v2-terrain.glb"
OUT_COLLIDER = ROOT / "assets/worlds/pass-v2-collider.glb"
OUT_PROPS = ROOT / "assets/worlds/pass-v2-props.glb"

X_MIN, X_MAX = -42.0, 42.0
Y_MIN, Y_MAX = -52.0, 32.0
CELL = 0.5

C_PLAZA_A = (0.82, 0.78, 0.68)
C_PLAZA_B = (0.74, 0.70, 0.60)
C_STREET = (0.66, 0.62, 0.53)
C_COURT = (0.78, 0.73, 0.62)
C_GRASS_A = (0.42, 0.67, 0.30)
C_GRASS_B = (0.53, 0.74, 0.35)
C_GRASS_DARK = (0.36, 0.59, 0.31)
C_ROCK = (0.56, 0.52, 0.45)
C_CLIFF = (0.40, 0.37, 0.32)
C_PATH_EDGE = (0.62, 0.58, 0.47)
C_TRUNK = (0.44, 0.31, 0.21)
C_PINE_A = (0.26, 0.52, 0.30)
C_PINE_B = (0.33, 0.60, 0.33)
C_LEAF_A = (0.43, 0.66, 0.27)
C_LEAF_B = (0.60, 0.71, 0.29)
C_LEAF_C = (0.82, 0.62, 0.25)
C_BANNER = (0.85, 0.68, 0.22)
C_WOOD = (0.48, 0.35, 0.23)
C_LAMP = (0.58, 0.55, 0.50)

# ---- authored height field -------------------------------------------------

def smoothstep(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3.0 - 2.0 * t)


def rise(d, a, b, h):
    return smoothstep((d - a) / (b - a)) * h


def mountain_noise(x, y):
    return (math.sin(x * 0.34 + 1.7) * math.sin(y * 0.29 + 0.6) * 0.5
            + math.sin(x * 0.13 + 0.3) * math.sin(y * 0.17 + 2.1) * 0.5)


def wall_walk_z(x, y):
    """East (sign=1) and west (sign=-1) wall-walk ridge lines from the citadel."""
    best = None
    for sign in (1.0, -1.0):
        ax, ay = sign * 10.5, 0.5
        bx, by = sign * 16.5, 7.0
        abx, aby = bx - ax, by - ay
        t = ((x - ax) * abx + (y - ay) * aby) / (abx * abx + aby * aby)
        tt = min(1.0, max(0.0, t))
        px, py = ax + abx * tt, ay + aby * tt
        d = math.hypot(x - px, y - py)
        z = 7.6 + tt * 1.6
        if best is None or d < best[0]:
            best = (d, z, tt)
    return best  # (distance, ridge z, t along ridge)


def height_at(x, y):
    # flat stone plaza & street axis with a gentle southward fall
    if y <= -2:
        t = min(1.0, (-y - 2) / 44.0)
        z = -1.4 * smoothstep(t)
    else:
        z = 0.0

    # citadel footprint is flat at 0 (the gate mesh itself provides the mass)
    if -4.2 <= y <= 4.2 and abs(x) <= 10.2:
        z = 0.0

    # east citadel stair hump: rises onto the wall-walk
    if -4.5 <= y <= 4.5 and 10.0 <= x <= 14.0:
        z = max(z, smoothstep((x - 10.0) / 3.6) * 7.6)

    # mountain masses: flank the axis and close the north view
    if y > -2:
        d = max(0.0, abs(x) - 7.5)
        m = rise(d, 4.0, 16.0, 16.5)
        if y > 5:
            m = max(m, rise(y - 5, 5.0, 20.0, 21.0))
        if y < -4:
            m *= smoothstep((y + 4) / -6.0 + 1.0)
        z = max(z, m)
    else:
        if y >= -26:
            hw = 14.5
        else:
            hw = max(10.0, 14.5 - (-y - 26) * 0.18)
        d = max(0.0, abs(x) - hw)
        m = rise(d, 5.0, 17.0, 14.5) * (1.0 + 0.25 * mountain_noise(x, y))
        if y < -34:
            fade = smoothstep((abs(x) - (hw - 3.0)) / 5.0)
            m = max(m, rise(-y - 34, 4.0, 14.0, 12.0) * fade)
        z = max(z, m)

    # wall-walk ridges (both flanks), blended into the flank slope
    d, rz, _tt = wall_walk_z(x, y)
    if d < 2.6:
        w = smoothstep((2.6 - d) / 1.4)
        z = z * (1.0 - w) + rz * w

    # boundary courtyard: flat pocket east of the plaza
    if -18 <= y <= -10 and 5.5 <= x <= 15.5:
        cw = smoothstep(min(y + 18, -10 - y, x - 5.5, 15.5 - x) / 1.6)
        z = z * (1.0 - cw) + 0.0 * cw

    # keep the axis corridor clean of noise
    axis = (y <= -2 and abs(x) < (15.0 if y >= -26 else 10.0)) or (-4.2 <= y <= 4.2)
    if not axis:
        n = mountain_noise(x, y)
        if z > 0.6:
            z += n * 0.9
        elif z > -0.2:
            z += n * 0.10
    return z


nx = int(round((X_MAX - X_MIN) / CELL)) + 1
ny = int(round((Y_MAX - Y_MIN) / CELL)) + 1
xs = X_MIN + np.arange(nx) * CELL
ys = Y_MIN + np.arange(ny) * CELL
H = np.array([[height_at(x, y) for y in ys] for x in xs], dtype=np.float64)
print("V2_GRID", nx, ny, "z", round(float(H.min()), 2), round(float(H.max()), 2))

# ---- walkability: BFS from spawn with the game's step limits ---------------

def idx(x, y):
    return (int(round((x - X_MIN) / CELL)), int(round((y - Y_MIN) / CELL)))


SPAWN = (0.0, -44.0)
start = idx(*SPAWN)
reach = {start: H[start]}
frontier = [start]
STEP_UP, STEP_DOWN = 0.75, 1.2
while frontier:
    nxt = []
    for (i, j) in frontier:
        z0 = reach[(i, j)]
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            i2, j2 = i + di, j + dj
            if not (0 <= i2 < nx and 0 <= j2 < ny) or (i2, j2) in reach:
                continue
            dz = H[i2, j2] - z0
            if dz > STEP_UP or dz < -STEP_DOWN:
                continue
            reach[(i2, j2)] = H[i2, j2]
            nxt.append((i2, j2))
    frontier = nxt
print("V2_REACHABLE", len(reach), "of", nx * ny)

QUESTS = {
    "spawn": SPAWN,
    "grandpa": (3.0, -30.0),
    "gate": (0.0, -6.0),
    "terrain": (12.6, 3.0),
    "boundary": (10.5, -14.0),
    "d_steps": (11.6, -3.4),
    "d_wall": (14.6, 5.4),
    "d_cannon": (-6.0, -5.6),
    "d_banners": (0.0, -21.0),
    "d_view": (-14.4, 4.8),
}
for name, (qx, qy) in QUESTS.items():
    i, j = idx(qx, qy)
    ok = (i, j) in reach
    print(f"V2_QUEST {name} {'OK' if ok else 'UNREACHABLE'} z={H[i, j]:.2f}")
    assert ok, f"quest point unreachable: {name}"

# ---- classification / colors ----------------------------------------------

gy, gx = np.gradient(H, CELL, CELL)
slope = np.hypot(gx, gy)

ii, jj = np.meshgrid(np.arange(nx), np.arange(ny), indexing="ij")
cx = X_MIN + ii * CELL
cy = Y_MIN + jj * CELL
reach_mask = np.zeros((nx, ny), dtype=bool)
for (i, j) in reach:
    reach_mask[i, j] = True


def plaza_zone(x, y):
    return -26 <= y <= -2 and abs(x) <= 14.0

def street_zone(x, y):
    return y < -26 and abs(x) <= 9.0

def court_zone(x, y):
    return -18 <= y <= -10 and 5.5 <= x <= 15.5

def stair_zone(x, y):
    return -4.5 <= y <= 4.5 and 10.0 <= x <= 14.0


def color_with_noise(base, x, y, amount=0.05):
    k = abs((math.sin(x * 12.9898 + y * 78.233) * 43758.5453) % 1.0)
    f = 1.0 + (k - 0.5) * 2 * amount
    return tuple(min(1.0, c * f) for c in base)


def cell_color(x, y, z, sl):
    if plaza_zone(x, y) and sl < 0.8:
        checker = (math.floor(x / 2.0) + math.floor(y / 2.0)) % 2 == 0
        return color_with_noise(C_PLAZA_A if checker else C_PLAZA_B, x, y, 0.04)
    if street_zone(x, y) and sl < 0.8:
        return color_with_noise(C_STREET, x, y, 0.06)
    if court_zone(x, y) and sl < 0.8:
        return color_with_noise(C_COURT, x, y, 0.05)
    if stair_zone(x, y):
        return color_with_noise(C_PLAZA_B, x, y, 0.04)
    if sl > 1.75:
        return color_with_noise(C_ROCK, x, y)
    if z > 3.2:
        return color_with_noise(C_GRASS_DARK, x, y, 0.08)
    if reach_mask[idx(x, y)]:
        edge = plaza_zone(x, y + 0.8) or plaza_zone(x, y - 0.8)
        if edge:
            return color_with_noise(C_PATH_EDGE, x, y, 0.06)
        return color_with_noise(C_GRASS_A if (math.sin(x * 12.9898 + y * 78.233) * 43758.5453) % 1.0 > 0.45 else C_GRASS_B, x, y)
    return color_with_noise(C_GRASS_DARK, x, y, 0.08)


# ---- build terrain mesh ----------------------------------------------------

bm = bmesh.new()
for i in range(nx - 1):
    for j in range(ny - 1):
        x0, y0 = xs[i], ys[j]
        x1, y1 = xs[i + 1], ys[j + 1]
        v0 = bm.verts.new((x0, y0, H[i, j]))
        v1 = bm.verts.new((x1, y0, H[i + 1, j]))
        v2 = bm.verts.new((x1, y1, H[i + 1, j + 1]))
        v3 = bm.verts.new((x0, y1, H[i, j + 1]))
        bm.faces.new((v0, v1, v2, v3))

SKIRT_Z = -8.0
for i in range(nx - 1):
    j = 0
    x0, y0 = xs[i], ys[j]
    x1 = xs[i + 1]
    v0 = bm.verts.new((x0, y0, H[i, j]))
    v1 = bm.verts.new((x1, y0, H[i + 1, j]))
    v2 = bm.verts.new((x1, y0, SKIRT_Z))
    v3 = bm.verts.new((x0, y0, SKIRT_Z))
    bm.faces.new((v0, v1, v2, v3))
for j in range(ny - 1):
    for i in (0, nx - 2):
        x0, y0 = xs[i], ys[j]
        x1, y1 = xs[i], ys[j + 1]
        v0 = bm.verts.new((x0, y0, H[i, j]))
        v1 = bm.verts.new((x0, y1, H[i, j + 1]))
        v2 = bm.verts.new((x0, y1, SKIRT_Z))
        v3 = bm.verts.new((x0, y0, SKIRT_Z))
        bm.faces.new((v0, v1, v2, v3))
# south edge skirt (y = Y_MIN row) and north edge handled above via j loop ends
for i in range(nx - 1):
    j = ny - 2
    x0, y0 = xs[i], ys[j]
    x1, y1 = xs[i + 1], ys[j + 1]
    v0 = bm.verts.new((x0, y0, H[i, j]))
    v1 = bm.verts.new((x1, y0, H[i + 1, j]))
    v2 = bm.verts.new((x1, y0, SKIRT_Z))
    v3 = bm.verts.new((x0, y0, SKIRT_Z))
    bm.faces.new((v0, v1, v2, v3))

color_layer = bm.loops.layers.color.new("Col")
bm.faces.ensure_lookup_table()
for face in bm.faces:
    if any(v.co.z <= SKIRT_Z + 1e-3 for v in face.verts):
        col = C_CLIFF
    else:
        mx = sum(v.co.x for v in face.verts) / 4
        my = sum(v.co.y for v in face.verts) / 4
        mz = sum(v.co.z for v in face.verts) / 4
        i = min(max(int(round((mx - X_MIN) / CELL)), 0), nx - 1)
        j = min(max(int(round((my - Y_MIN) / CELL)), 0), ny - 1)
        col = cell_color(mx, my, mz, slope[i, j])
    for loop in face.loops:
        loop[color_layer] = (*col, 1.0)

terrain_me = bpy.data.meshes.new("V2Terrain")
bm.to_mesh(terrain_me)
bm.free()
if terrain_me.color_attributes:
    terrain_me.color_attributes.active_color = terrain_me.color_attributes[0]
terrain_obj = bpy.data.objects.new("V2Terrain", terrain_me)
bpy.context.collection.objects.link(terrain_obj)
print("V2_TERRAIN_TRIS", len(terrain_me.polygons))

# ---- collider: terrain + blocker boxes -------------------------------------

house_spots = ((11.5, -12.0, 0.0, 1.0), (11.5, -19.0, 0.0, 1.12), (-11.5, -12.0, math.pi, 1.0), (-11.5, -19.0, math.pi, 1.12))
cbm = bmesh.new()
# the walkable terrain itself is the primary collider
for i in range(nx - 1):
    for j in range(ny - 1):
        x0, y0 = xs[i], ys[j]
        x1, y1 = xs[i + 1], ys[j + 1]
        v0 = cbm.verts.new((x0, y0, H[i, j]))
        v1 = cbm.verts.new((x1, y0, H[i + 1, j]))
        v2 = cbm.verts.new((x1, y1, H[i + 1, j + 1]))
        v3 = cbm.verts.new((x0, y1, H[i, j + 1]))
        cbm.faces.new((v0, v1, v2, v3))

def add_blocker_box(cx, cy, cz, sx, sy, sz):
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    v = [(cx - hx, cy - hy, cz - hz), (cx + hx, cy - hy, cz - hz), (cx + hx, cy + hy, cz - hz), (cx - hx, cy + hy, cz - hz),
         (cx - hx, cy - hy, cz + hz), (cx + hx, cy - hy, cz + hz), (cx + hx, cy + hy, cz + hz), (cx - hx, cy + hy, cz + hz)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (3, 0, 4, 7)]
    mapping = [cbm.verts.new(p) for p in v]
    for face in f:
        cbm.faces.new([mapping[i] for i in face])

# gate citadel: two piers + lintel (passage stays open along Y)
for c in (-6.25, 6.25):
    add_blocker_box(c, 0.0, 3.5, 7.5, 8.4, 9.0)
add_blocker_box(0.0, 0.0, 7.0, 5.0, 8.4, 2.0)
# plaza houses + courtyard table blockers
for (hx, hy, hrot, hs) in house_spots:
    add_blocker_box(hx, hy, 1.5, 3.9 * hs, 3.1 * hs, 3.0)
add_blocker_box(12.6, -15.6, 0.4, 1.3, 1.3, 0.8)
# wall-walk parapets: low walls on both sides of each ridge
for sign in (1.0, -1.0):
    steps = 12
    for k in range(steps):
        t0 = k / steps
        t1 = (k + 1) / steps
        ax = sign * (10.5 + (16.5 - 10.5) * t0)
        ay = 0.5 + (7.0 - 0.5) * t0
        bx = sign * (10.5 + (16.5 - 10.5) * t1)
        by = 0.5 + (7.0 - 0.5) * t1
        zt = 7.6 + t1 * 1.6 + 0.55
        add_blocker_box((ax + bx) / 2, (ay + by) / 2, zt, 0.7, 0.7, 1.2)

collider_me = bpy.data.meshes.new("V2Collider")
cbm.to_mesh(collider_me)
cbm.free()
if collider_me.color_attributes:
    collider_me.color_attributes.active_color = collider_me.color_attributes[0]
collider_obj = bpy.data.objects.new("V2Collider", collider_me)
bpy.context.collection.objects.link(collider_obj)
print("V2_COLLIDER_TRIS", len(collider_me.polygons))

# ---- props -----------------------------------------------------------------

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
    me = bpy.data.meshes.new("part")
    tmp.to_mesh(me)
    tmp.free()
    for p in me.polygons:
        p.use_smooth = False
    pmb.from_mesh(me)
    bpy.data.meshes.remove(me)


def noise2(a, b):
    return abs((math.sin(a * 3.1 + b * 7.7) * 24681.37) % 1.0)


def trunk_only(b2, sc, tall=0.95):
    seg = 5
    r0, r1 = 0.12 * sc, 0.09 * sc
    pts0 = [(math.cos(k / seg * 2 * math.pi) * r0, math.sin(k / seg * 2 * math.pi) * r0, 0.0) for k in range(seg)]
    pts1 = [(math.cos(k / seg * 2 * math.pi) * r1, math.sin(k / seg * 2 * math.pi) * r1, tall * sc) for k in range(seg)]
    v0 = [b2.verts.new(p) for p in pts0]
    v1 = [b2.verts.new(p) for p in pts1]
    for k in range(seg):
        b2.faces.new((v0[k], v0[(k + 1) % seg], v1[(k + 1) % seg], v1[k]))
    b2.faces.new(v0)


def pine_canopy(b2, sc):
    rot = noise2(sc, 7) * 6.28
    for z0, z1, r0 in ((0.32 * sc, 1.55 * sc, 0.95 * sc), (0.9 * sc, 1.95 * sc, 0.66 * sc)):
        seg = 6
        pts = [(math.cos(rot + k / seg * 2 * math.pi) * r0, math.sin(rot + k / seg * 2 * math.pi) * r0, z0) for k in range(seg)]
        v0 = [b2.verts.new(p) for p in pts]
        tip = b2.verts.new((0, 0, z1))
        base = b2.verts.new((0, 0, z0))
        for k in range(seg):
            b2.faces.new((v0[k], v0[(k + 1) % seg], tip))
            b2.faces.new((v0[(k + 1) % seg], v0[k], base))


def leaf_ball(b2, sc, r=0.72):
    cz = 1.42 * sc
    r = r * sc
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


def lamp_post(b2, sc):
    seg = 6
    r = 0.10 * sc
    pts0 = [(math.cos(k / seg * 2 * math.pi) * r, math.sin(k / seg * 2 * math.pi) * r, 0.0) for k in range(seg)]
    pts1 = [(math.cos(k / seg * 2 * math.pi) * r * 0.8, math.sin(k / seg * 2 * math.pi) * r * 0.8, 2.4 * sc) for k in range(seg)]
    v0 = [b2.verts.new(p) for p in pts0]
    v1 = [b2.verts.new(p) for p in pts1]
    for k in range(seg):
        b2.faces.new((v0[k], v0[(k + 1) % seg], v1[(k + 1) % seg], v1[k]))
    cap = b2.verts.new((0, 0, 2.85 * sc))
    ring = [b2.verts.new((math.cos(k / seg * 2 * math.pi) * 0.3 * sc, math.sin(k / seg * 2 * math.pi) * 0.3 * sc, 2.5 * sc)) for k in range(seg)]
    for k in range(seg):
        b2.faces.new((ring[k], ring[(k + 1) % seg], cap))
    b2.faces.new(ring[::-1])


def banner(b2, sc):
    # pole + long yellow cloth with red hem
    seg = 5
    r = 0.06 * sc
    pts0 = [(math.cos(k / seg * 2 * math.pi) * r, math.sin(k / seg * 2 * math.pi) * r, 0.0) for k in range(seg)]
    pts1 = [(math.cos(k / seg * 2 * math.pi) * r, math.sin(k / seg * 2 * math.pi) * r, 5.2 * sc) for k in range(seg)]
    v0 = [b2.verts.new(p) for p in pts0]
    v1 = [b2.verts.new(p) for p in pts1]
    for k in range(seg):
        b2.faces.new((v0[k], v0[(k + 1) % seg], v1[(k + 1) % seg], v1[k]))
    w, h, z0 = 0.55 * sc, 2.3 * sc, 2.6 * sc
    c = [(0, 0, z0), (0, 0, z0 + h)]
    pts_a = [b2.verts.new((c[0][0], c[0][1], c[0][2] + k / 4 * h)) for k in range(5)]
    pts_b = [b2.verts.new((w, 0, z0 + k / 4 * h + (0.08 * sc if k in (0, 4) else 0))) for k in range(5)]
    for k in range(4):
        b2.faces.new((pts_a[k], pts_b[k], pts_b[k + 1], pts_a[k + 1]))


def signpost(b2, sc):
    trunk_only(b2, 1.3 * sc)
    for (dx, dz, rot) in ((0.4, 2.1, 0.5), (-0.45, 1.7, -0.6), (0.35, 1.3, 2.4)):
        w, h, t = 0.9 * sc, 0.24 * sc, 0.06 * sc
        ca, sa = math.cos(rot), math.sin(rot)
        v = []
        for (px, py, pz) in ((0, -t, 0), (w, -t, 0), (w, t, 0), (0, t, 0), (0, -t, h), (w, -t, h), (w, t, h), (0, t, h)):
            x = dx + px * ca
            y = px * sa + py * ca
            v.append(b2.verts.new((x, y, dz + pz)))
        for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (3, 0, 4, 7)):
            b2.faces.new([v[i] for i in f])


def crate(b2, sc):
    hx = 0.45 * sc
    v = [b2.verts.new((x * hx, y * hx, z * hx)) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    order = [0, 1, 3, 2], [4, 6, 7, 5], [0, 2, 6, 4], [1, 3, 7, 5], [0, 4, 5, 1], [2, 3, 7, 6]
    for f in order:
        b2.faces.new([v[i] for i in f])


def rock_shape(b2, sc):
    seg = 6
    zz = 0.30 * sc
    v_lo = [b2.verts.new((math.cos(k / seg * 2 * math.pi) * 0.55 * sc, math.sin(k / seg * 2 * math.pi) * 0.42 * sc, 0.0)) for k in range(seg)]
    v_hi = [b2.verts.new((math.cos(k / seg * 2 * math.pi + 0.5) * 0.36 * sc, math.sin(k / seg * 2 * math.pi + 0.5) * 0.32 * sc, zz)) for k in range(seg)]
    v_top = b2.verts.new((0.05 * sc, 0, zz + 0.24 * sc))
    for k in range(seg):
        b2.faces.new((v_lo[k], v_lo[(k + 1) % seg], v_hi[(k + 1) % seg], v_hi[k]))
        b2.faces.new((v_hi[k], v_hi[(k + 1) % seg], v_top))
    b2.faces.new(v_lo)


def z_at(x, y):
    i, j = idx(x, y)
    return H[i, j]


# trees on the flanks (keep plaza/street/courtyard clear)
placed = []
count = 0
x = X_MIN + 2
while x < X_MAX - 2:
    y = Y_MIN + 2
    while y < Y_MAX - 2:
        i, j = idx(x, y)
        on_axis = (plaza_zone(x, y) or street_zone(x, y) or court_zone(x, y) or stair_zone(x, y)
                   or (abs(x) < 10.5 and -4.5 <= y <= 4.5) or wall_walk_z(x, y)[0] < 4.5)
        if (not on_axis) and H[i, j] > 1.2 and slope[i, j] < 1.9 and noise2(x, y) > 0.5:
            if any((x - px) ** 2 + (y - py) ** 2 < 7.0 for px, py in placed):
                y += CELL * 2
                continue
            s = 1.7 + noise2(y, x) * 1.9
            if noise2(y * 2, x) > 0.5:
                emit_part(trunk_only, C_TRUNK, (x, y, H[i, j] - 0.2), s)
                emit_part(pine_canopy, C_PINE_A if noise2(x * 3, y) > 0.5 else C_PINE_B, (x, y, H[i, j] - 0.2), s)
            else:
                tone = C_LEAF_A if noise2(x, y * 2) > 0.66 else (C_LEAF_B if noise2(x, y * 2) > 0.33 else C_LEAF_C)
                emit_part(trunk_only, C_TRUNK, (x, y, H[i, j] - 0.2), s)
                emit_part(leaf_ball, tone, (x, y, H[i, j] - 0.2), s)
            placed.append((x, y))
            count += 1
        y += CELL * 2
    x += CELL * 2
print("V2_TREES", count)

# landmark trees framing the street entrance + one in the courtyard
for (tx, ty, ts) in ((-6.5, -43.0, 2.3), (6.8, -42.2, 2.1), (14.2, -16.4, 1.9)):
    emit_part(trunk_only, C_TRUNK, (tx, ty, z_at(tx, ty) - 0.2), ts)
    emit_part(leaf_ball, C_LEAF_A if tx < 0 else C_LEAF_B, (tx, ty, z_at(tx, ty) - 0.2), ts)

# lamp posts along the plaza axis
for k, (lx, ly) in enumerate(((-6.0, -12.0), (6.0, -12.0), (-6.0, -22.0), (6.0, -22.0), (-5.0, -32.0), (5.0, -32.0), (-4.2, -40.0), (4.2, -40.0))):
    emit_part(lamp_post, C_LAMP, (lx, ly, z_at(lx, ly)), 1.0 + 0.1 * (k % 2))

# banner pair mid-plaza + banner pair at the entrance
for (bx, by) in ((-3.4, -21.0), (3.4, -21.0), (-2.8, -36.0), (2.8, -36.0)):
    emit_part(banner, C_BANNER, (bx, by, z_at(bx, by)), 1.0, rot=noise2(bx, by) * 0.3)

# signpost cluster and crates near the street
emit_part(signpost, C_WOOD, (-4.6, -38.5, z_at(-4.6, -38.5)), 1.0, rot=0.6)
for k, (bx, by) in enumerate(((4.6, -9.0), (5.5, -9.4), (5.0, -9.2))):
    emit_part(crate, C_WOOD, (bx, by, z_at(bx, by) + 0.45 * (1 if k == 2 else 0)), 1.0 - 0.12 * k, rot=k * 0.7)

# ---- border-town houses flanking the plaza ----
C_WALL = (0.88, 0.84, 0.73)
C_TILE = (0.30, 0.33, 0.37)
C_DOOR = (0.40, 0.22, 0.16)
C_STONE_L = (0.70, 0.67, 0.60)


def house_walls(b2, sc=1.0):
    box(b2, -1.8, 1.8, -1.4, 1.4, 0.0, 2.6)

def box(b2, x0, x1, y0, y1, z0, z1):
    v = [b2.verts.new(p) for p in (
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (3, 0, 4, 7)):
        b2.faces.new([v[i] for i in f])


def prism(b2, x0, x1, y0, y1, z0, rx0, rx1, z_apex):
    v = [b2.verts.new(p) for p in (
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (rx0, (y0 + y1) / 2, z_apex), (rx1, (y0 + y1) / 2, z_apex))]
    for f in ((0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5)):
        b2.faces.new([v[i] for i in f])


def tube(b2, x, y, z0, z1, r0, r1, seg=8):
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


def house_base(b2, sc=1.0):
    box(b2, -1.9, 1.9, -1.5, 1.5, 0.0, 0.32)

def house_roof(b2, sc=1.0):
    prism(b2, -2.3, 2.3, -1.9, 1.9, 2.6, -0.5, 0.5, 3.6)

def house_door(b2, sc=1.0):
    box(b2, -1.88, -1.72, -0.45, 0.45, 0.05, 1.9)

def house_windows(b2, sc=1.0):
    for wy in (-0.95, 0.55):
        box(b2, -1.87, -1.77, wy - 0.35, wy + 0.35, 1.15, 1.8)

def stone_table(b2, sc=1.0):
    tube(b2, 0.0, 0.0, 0.0, 0.58, 0.10, 0.09)
    tube(b2, 0.0, 0.0, 0.58, 0.66, 0.56, 0.52)

def stone_stool(b2, sc=1.0):
    tube(b2, 0.0, 0.0, 0.0, 0.34, 0.21, 0.18)


for (hx, hy, hrot, hs) in house_spots:
    hz = z_at(hx, hy)
    emit_part(house_base, C_GRANITE_D if False else (0.56, 0.53, 0.47), (hx, hy, hz), hs, rot=hrot)
    emit_part(house_walls, C_WALL, (hx, hy, hz), hs, rot=hrot)
    emit_part(house_roof, C_TILE, (hx, hy, hz), hs, rot=hrot)
    emit_part(house_door, C_DOOR, (hx, hy, hz), hs, rot=hrot)
    emit_part(house_windows, (0.15, 0.19, 0.23), (hx, hy, hz), hs, rot=hrot)
print("V2_HOUSES", len(house_spots))

# ---- boundary courtyard: stone table, stools, pines ----
tx, ty = 12.6, -15.6
tz = z_at(tx, ty)
emit_part(stone_table, C_STONE_L, (tx, ty, tz), 1.0)
for (sx, sy) in ((-0.95, 0.1), (0.95, 0.1), (0.0, -1.0), (0.0, 1.05)):
    emit_part(stone_stool, C_STONE_L, (tx + sx, ty + sy, z_at(tx + sx, ty + sy)), 1.0)
for (px_, py_) in ((6.6, -11.0), (14.8, -10.6)):
    i2, j2 = idx(px_, py_)
    ss = 1.25
    emit_part(trunk_only, C_TRUNK, (px_, py_, H[i2, j2] - 0.2), ss)
    emit_part(pine_canopy, C_PINE_A, (px_, py_, H[i2, j2] - 0.2), ss)
print("V2_COURTYARD_OK")

# rocks on the slopes
rcount = 0
for (rx, ry) in ((-16.0, 2.0), (17.5, -6.0), (-19.0, -12.0), (19.0, 8.0), (-13.0, 14.0), (12.0, 16.5)):
    i, j = idx(rx, ry)
    emit_part(rock_shape, C_ROCK, (rx, ry, H[i, j] - 0.15), 1.3 + noise2(rx, ry) * 1.2, rot=noise2(ry, rx) * 3.0)
    rcount += 1
print("V2_ROCKS", rcount)

props_me = bpy.data.meshes.new("V2Props")
pmb.to_mesh(props_me)
pmb.free()
if props_me.color_attributes:
    props_me.color_attributes.active_color = props_me.color_attributes[0]
props_obj = bpy.data.objects.new("V2Props", props_me)
bpy.context.collection.objects.link(props_obj)

# ---- preview renders -------------------------------------------------------

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
shading.shadow_intensity = 0.35


def add_camera(name, location, target, lens=30):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    direction = Vector(target) - Vector(location)
    obj.location = location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return obj


scene.camera = add_camera("Overview", (0.0, -78.0, 52.0), (0.0, -6.0, 2.0), lens=38)
scene.render.filepath = str(ROOT / "tools/renders/v2_overview.png")
bpy.ops.render.render(write_still=True)
print("RENDERED v2_overview")

scene.camera = add_camera("Axis", (2.5, -48.0, 5.5), (0.0, 0.0, 6.0), lens=30)
scene.render.filepath = str(ROOT / "tools/renders/v2_axis.png")
bpy.ops.render.render(write_still=True)
print("RENDERED v2_axis")

shading.light = "FLAT"
shading.show_shadows = False
shading.show_cavity = False
map_data = bpy.data.cameras.new("MiniMap")
map_data.type = "ORTHO"
map_data.ortho_scale = 92.0
map_cam = bpy.data.objects.new("MiniMap", map_data)
bpy.context.collection.objects.link(map_cam)
map_cam.location = (0.0, -10.0, 60.0)
map_cam.rotation_euler = (0.0, 0.0, 0.0)
scene.camera = map_cam
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.filepath = str(ROOT / "assets/ui/pass-minimap.png")
bpy.ops.render.render(write_still=True)
print("RENDERED pass_minimap")


# ---- exports ---------------------------------------------------------------

def export(obj, path):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", export_yup=True, use_selection=True)


export(terrain_obj, OUT_TERRAIN)
export(collider_obj, OUT_COLLIDER)
export(props_obj, OUT_PROPS)
print("WROTE", OUT_TERRAIN)
print("WROTE", OUT_COLLIDER)
print("WROTE", OUT_PROPS)
