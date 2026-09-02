"""Grandpa v2 — rounded, blended bell-robe elder with straw hat and cane.

Run via Blender CLI:
  blender --background --python tools/build_grandpa_v2.py

Output: assets/models/grandpa-v2.glb (+ preview). ~1.6 m, front faces -Y.
"""

import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

ROOT = Path(r"D:\HKU-ds\QCH\界碑智能体")
OUT = ROOT / "assets/models/grandpa-v2.glb"

C_SKIN = (0.93, 0.76, 0.60)
C_ROBE = (0.26, 0.40, 0.36)
C_ROBE_D = (0.20, 0.32, 0.29)
C_TRIM = (0.85, 0.79, 0.62)
C_SASH = (0.55, 0.26, 0.18)
C_WHITE = (0.97, 0.96, 0.93)
C_HAT = (0.79, 0.63, 0.30)
C_HAT_D = (0.62, 0.48, 0.22)
C_WOOD = (0.42, 0.30, 0.20)

bpy.ops.wm.read_homefile(use_empty=True)
pmb = bmesh.new()


def emit(builder, color):
    tmp = bmesh.new()
    builder(tmp)
    layer = tmp.loops.layers.color.new("Col")
    for f in tmp.faces:
        for l in f.loops:
            l[layer] = (*color, 1.0)
    me = bpy.data.meshes.new("part")
    tmp.to_mesh(me)
    tmp.free()
    for p in me.polygons:
        p.use_smooth = True
    pmb.from_mesh(me)
    bpy.data.meshes.remove(me)


def sphere(b2, cx, cy, cz, r, seg=10, ry=1.0, rz=1.0):
    top = b2.verts.new((cx, cy, cz + r * rz))
    bot = b2.verts.new((cx, cy, cz - r * rz))
    rings = []
    for lat in range(1, seg):
        phi = math.pi * lat / seg
        rr = r * math.sin(phi)
        z = cz + r * math.cos(phi) * rz
        rings.append([b2.verts.new((cx + math.cos(k / seg * 2 * math.pi) * rr, cy + math.sin(k / seg * 2 * math.pi) * rr * ry, z)) for k in range(seg)])
    for k in range(seg):
        b2.faces.new((rings[0][(k + 1) % seg], rings[0][k], top))
    for lat in range(len(rings) - 1):
        a, b = rings[lat], rings[lat + 1]
        for k in range(seg):
            b2.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    for k in range(seg):
        b2.faces.new((rings[-1][k], rings[-1][(k + 1) % seg], bot))


def capsule(b2, p0, p1, r, seg=8):
    d = Vector(p1) - Vector(p0)
    d.normalize()
    side = Vector((0, 0, 1)).cross(d)
    if side.length < 1e-3:
        side = Vector((1, 0, 0))
    side.normalize()
    up = d.cross(side).normalized()
    rings = []
    steps = 4
    for lat in range(steps + 1):
        phi = math.pi * lat / steps
        off = d * (r * math.cos(phi))
        rr = r * math.sin(phi)
        ring = []
        for k in range(seg):
            ang = k / seg * 2 * math.pi
            v = Vector(p0) + off + side * (math.cos(ang) * rr) + up * (math.sin(ang) * rr)
            ring.append(b2.verts.new(v))
        rings.append(ring)
    for lat in range(steps):
        a, b = rings[lat], rings[lat + 1]
        for k in range(seg):
            b2.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    cap0 = b2.verts.new(Vector(p0) - d * r)
    cap1 = b2.verts.new(Vector(p1) + d * r)
    for k in range(seg):
        b2.faces.new((rings[0][(k + 1) % seg], rings[0][k], cap0))
        b2.faces.new((rings[-1][k], rings[-1][(k + 1) % seg], cap1))


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


# ---- bell robe (single blended mass down to the ground) ----
emit(lambda b2: tube(b2, 0.0, 0.0, 0.0, 1.02, 0.46, 0.24, seg=12), C_ROBE)
emit(lambda b2: tube(b2, 0.0, 0.0, 0.0, 0.14, 0.475, 0.45, seg=12), C_TRIM)
# shoulders blend into the robe
emit(lambda b2: sphere(b2, 0.0, 0.0, 1.08, 0.295, seg=12, ry=0.9), C_ROBE)
# sash
emit(lambda b2: tube(b2, 0.0, 0.0, 0.70, 0.80, 0.315, 0.30, seg=12), C_SASH)

# ---- head + face ----
emit(lambda b2: sphere(b2, 0.0, 0.0, 1.42, 0.19, seg=12, ry=0.95), C_SKIN)
# long white beard: wide teardrop from chin to the chest
emit(lambda b2: tube(b2, 0.0, -0.125, 0.94, 1.31, 0.025, 0.16, seg=10), C_WHITE)
emit(lambda b2: sphere(b2, 0.0, -0.105, 1.31, 0.115, seg=10, ry=0.75, rz=1.15), C_WHITE)
# mustache
for sx in (-1, 1):
    emit(lambda b2, sx=sx: sphere(b2, sx * 0.05, -0.185, 1.35, 0.038, seg=8, ry=1.5, rz=0.5), C_WHITE)
# brows
for sx in (-1, 1):
    emit(lambda b2, sx=sx: sphere(b2, sx * 0.075, -0.165, 1.475, 0.042, seg=8, ry=1.4, rz=0.55), C_WHITE)
# eyes + nose + cheeks
for sx in (-1, 1):
    emit(lambda b2, sx=sx: sphere(b2, sx * 0.07, -0.168, 1.435, 0.026, seg=8, rz=1.3), C_HAIR_D := (0.14, 0.12, 0.11))
emit(lambda b2: sphere(b2, 0.0, -0.185, 1.40, 0.035, seg=8), C_SKIN)
for sx in (-1, 1):
    emit(lambda b2, sx=sx: sphere(b2, sx * 0.135, -0.15, 1.375, 0.035, seg=8, ry=0.6, rz=0.7), (0.90, 0.60, 0.52))

# ---- straw hat: wide brim + dome, red band ----
emit(lambda b2: tube(b2, 0.0, 0.0, 1.505, 1.575, 0.45, 0.10, seg=12), C_HAT)
emit(lambda b2: sphere(b2, 0.0, 0.0, 1.575, 0.235, seg=12, rz=0.8), C_HAT)
emit(lambda b2: tube(b2, 0.0, 0.0, 1.565, 1.615, 0.235, 0.22, seg=12), C_HAT_D)
emit(lambda b2: tube(b2, 0.0, 0.0, 1.515, 1.555, 0.275, 0.26, seg=12), (0.62, 0.18, 0.14))

# ---- arms: sleeves folded to the front, one hand on the cane ----
for sx in (-1, 1):
    def sleeve(b2, sx=sx):
        capsule(b2, (sx * 0.22, 0.02, 1.10), (sx * 0.30 if sx > 0 else sx * 0.20, -0.16, 0.82), 0.088)
    emit(sleeve, C_ROBE_D)
emit(lambda b2: sphere(b2, 0.30, -0.20, 0.76, 0.066, seg=8), C_SKIN)
# cane in the right hand, clear of the robe
emit(lambda b2: tube(b2, 0.335, -0.265, 0.0, 0.86, 0.036, 0.044, seg=8), C_WOOD)
emit(lambda b2: sphere(b2, 0.335, -0.265, 0.90, 0.058, seg=8), C_WOOD)

me = bpy.data.meshes.new("GrandpaV2")
pmb.to_mesh(me)
pmb.free()
if me.color_attributes:
    me.color_attributes.active_color = me.color_attributes[0]
obj = bpy.data.objects.new("GrandpaV2", me)
bpy.context.collection.objects.link(obj)
print("GRANDPA_V2_TRIS", len(me.polygons))

scene = bpy.context.scene
scene.render.resolution_x = 800
scene.render.resolution_y = 1000
scene.render.image_settings.file_format = "PNG"
scene.render.engine = "BLENDER_WORKBENCH"
shading = scene.display.shading
shading.light = "STUDIO"
shading.color_type = "VERTEX"
shading.show_cavity = True
shading.cavity_type = "BOTH"

cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.collection.objects.link(cam)
loc = Vector((1.5, -2.5, 1.85))
direction = Vector((0.0, 0.0, 0.85)) - loc
cam.location = loc
cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
scene.camera = cam
scene.render.filepath = str(ROOT / "tools/renders/grandpa_v2_preview.png")
bpy.ops.render.render(write_still=True)
print("RENDERED grandpa_v2_preview")

bpy.ops.object.select_all(action="DESELECT")
obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, use_selection=True)
print("WROTE", OUT)
