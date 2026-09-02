"""Student character v2 — chibi proportions, overlapping rounded forms.

Run via Blender CLI:
  blender --background --python tools/build_student_v2.py

Output: assets/models/student-girl-v2.glb (+ preview). ~1.32 m, front faces -Y.
"""

import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

ROOT = Path(r"D:\HKU-ds\QCH\界碑智能体")
OUT = ROOT / "assets/models/student-girl-v2.glb"

C_SKIN = (0.97, 0.82, 0.68)
C_BLUSH = (0.95, 0.62, 0.55)
C_HAIR = (0.14, 0.12, 0.11)
C_SHIRT = (0.95, 0.94, 0.89)
C_SCARF = (0.83, 0.16, 0.13)
C_SKIRT = (0.22, 0.28, 0.41)
C_SHOE = (0.86, 0.32, 0.25)
C_BAG = (0.90, 0.58, 0.20)
C_BAG_D = (0.72, 0.44, 0.14)

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


def box_core(b2, cx, cy, cz, sx, sy, sz):
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    v = [b2.verts.new(p) for p in (
        (cx - hx, cy - hy, cz - hz), (cx + hx, cy - hy, cz - hz), (cx + hx, cy + hy, cz - hz), (cx - hx, cy + hy, cz - hz),
        (cx - hx, cy - hy, cz + hz), (cx + hx, cy - hy, cz + hz), (cx + hx, cy + hy, cz + hz), (cx - hx, cy + hy, cz + hz))]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (3, 0, 4, 7)):
        b2.faces.new([v[i] for i in f])


# ---- body: skirt cone + torso sphere (blended) ----
emit(lambda b2: tube(b2, 0.0, 0.0, 0.34, 0.80, 0.28, 0.19, seg=10), C_SKIRT)
emit(lambda b2: sphere(b2, 0.0, 0.0, 0.80, 0.215, seg=10, ry=0.95), C_SHIRT)
emit(lambda b2: sphere(b2, 0.0, 0.0, 0.72, 0.26, seg=10, ry=0.7), C_SKIRT)

# arms: capsules from inside the torso to mitten hands (no gaps)
for sx in (-1, 1):
    def arm(b2, sx=sx):
        capsule(b2, (sx * 0.13, 0.0, 0.82), (sx * 0.37, -0.05, 0.55), 0.078)
    emit(arm, C_SCARF)
    emit(lambda b2, sx=sx: sphere(b2, sx * 0.38, -0.05, 0.505, 0.08, seg=8), C_SKIN)

# legs peeking under the skirt + shoes
for sx in (-1, 1):
    emit(lambda b2, sx=sx: tube(b2, sx * 0.105, 0.0, 0.14, 0.34, 0.068, 0.06, seg=8), C_SKIN)
    emit(lambda b2, sx=sx: sphere(b2, sx * 0.105, -0.015, 0.09, 0.085, seg=8, rz=0.75), C_SHOE)

# ---- head (big, chibi) ----
emit(lambda b2: sphere(b2, 0.0, 0.0, 1.08, 0.245, seg=12, ry=0.96), C_SKIN)
# hair: big cap sphere shifted back/up, blending over the crown
emit(lambda b2: sphere(b2, 0.0, 0.035, 1.115, 0.252, seg=12, ry=0.94), C_HAIR)
# bangs: three rounded lobes over the forehead
for bx, bz, by in ((-0.165, 1.175, -0.145), (-0.085, 1.215, -0.205), (0.0, 1.235, -0.215), (0.085, 1.215, -0.205), (0.165, 1.175, -0.145)):
    emit(lambda b2, bx=bx, bz=bz, by=by: sphere(b2, bx, by, bz, 0.058, seg=8), C_HAIR)
# ponytail buns + red ties
for sx in (-1, 1):
    emit(lambda b2, sx=sx: sphere(b2, sx * 0.215, 0.115, 1.085, 0.098, seg=8), C_HAIR)
    emit(lambda b2, sx=sx: tube(b2, sx * 0.21, 0.10, 1.155, 1.175, 0.052, 0.048, seg=6), C_SCARF)

# face: big eyes, blush, smile
for sx in (-1, 1):
    emit(lambda b2, sx=sx: sphere(b2, sx * 0.098, -0.222, 1.095, 0.036, seg=8, rz=1.25), C_HAIR)
    emit(lambda b2, sx=sx: sphere(b2, sx * 0.175, -0.205, 1.015, 0.038, seg=8, ry=0.6, rz=0.7), C_BLUSH)
emit(lambda b2: sphere(b2, 0.0, -0.235, 1.005, 0.022, seg=6, ry=1.6, rz=0.6), C_HAIR)

# ---- red scarf + knot ----
def prism_ribbon(b2, x0, x1, y0, y1, z0, rx0, rx1, z_apex):
    v = [b2.verts.new(p) for p in (
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (rx0, (y0 + y1) / 2, z_apex), (rx1, (y0 + y1) / 2, z_apex))]
    for f in ((0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5)):
        b2.faces.new([v[i] for i in f])


emit(lambda b2: tube(b2, 0.0, 0.0, 0.68, 0.79, 0.245, 0.205, seg=10), C_SCARF)
emit(lambda b2: sphere(b2, 0.0, -0.21, 0.66, 0.055, seg=8), C_SCARF)
emit(lambda b2: prism_ribbon(b2, -0.05, 0.05, -0.27, -0.17, 0.48, -0.008, 0.008, 0.65), C_SCARF)


# ---- backpack (rounded: core box + corner spheres) ----
emit(lambda b2: box_core(b2, 0.0, 0.21, 0.92, 0.34, 0.17, 0.42), C_BAG)
for (ox, oz) in ((-0.14, 1.10), (0.14, 1.10), (-0.14, 0.74), (0.14, 0.74)):
    emit(lambda b2, ox=ox, oz=oz: sphere(b2, ox, 0.21, oz, 0.085, seg=8), C_BAG)
emit(lambda b2: box_core(b2, 0.0, 0.30, 0.98, 0.22, 0.03, 0.15), C_BAG_D)
for sx in (-1, 1):
    emit(lambda b2, sx=sx: capsule(b2, (sx * 0.10, -0.06, 1.06), (sx * 0.115, 0.14, 0.86), 0.032, seg=6), C_BAG_D)

me = bpy.data.meshes.new("StudentGirlV2")
pmb.to_mesh(me)
pmb.free()
if me.color_attributes:
    me.color_attributes.active_color = me.color_attributes[0]
obj = bpy.data.objects.new("StudentGirlV2", me)
bpy.context.collection.objects.link(obj)
print("STUDENT_V2_TRIS", len(me.polygons))

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
loc = Vector((1.5, -2.4, 1.7))
direction = Vector((0.0, 0.0, 0.68)) - loc
cam.location = loc
cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
scene.camera = cam
scene.render.filepath = str(ROOT / "tools/renders/student_v2_preview.png")
bpy.ops.render.render(write_still=True)
print("RENDERED student_v2_preview")

bpy.ops.object.select_all(action="DESELECT")
obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, use_selection=True)
print("WROTE", OUT)
