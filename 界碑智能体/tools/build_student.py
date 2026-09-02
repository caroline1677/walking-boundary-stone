"""Primary-school student character (girl, red scarf, backpack) for the player.

Run via Blender CLI:
  blender --background --python tools/build_student.py

~1.4 m tall, origin at ground center, face toward -Y (exports to +Z in three).
Vertex-colored, flat shaded. Output: assets/models/student-girl.glb
"""

import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector
from mathutils import Euler

ROOT = Path(r"D:\HKU-ds\QCH\界碑智能体")
OUT = ROOT / "assets/models/student-girl.glb"

C_SKIN = (0.96, 0.80, 0.66)
C_HAIR = (0.13, 0.11, 0.10)
C_SHIRT = (0.94, 0.93, 0.88)
C_SCARF = (0.82, 0.16, 0.13)
C_PANTS = (0.20, 0.26, 0.38)
C_SHOE = (0.85, 0.30, 0.24)
C_BAG = (0.88, 0.55, 0.18)
C_BAG_D = (0.70, 0.42, 0.13)

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
        p.use_smooth = False
    pmb.from_mesh(me)
    bpy.data.meshes.remove(me)


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


def ball(b2, cx, cy, cz, r, seg=8):
    top = b2.verts.new((cx, cy, cz + r))
    bot = b2.verts.new((cx, cy, cz - r))
    rings = []
    for lat in range(1, seg):
        phi = math.pi * lat / seg
        rr = r * math.sin(phi)
        z = cz + r * math.cos(phi)
        rings.append([b2.verts.new((cx + math.cos(k / seg * 2 * math.pi) * rr, cy + math.sin(k / seg * 2 * math.pi) * rr, z)) for k in range(seg)])
    for k in range(seg):
        b2.faces.new((rings[0][(k + 1) % seg], rings[0][k], top))
    for lat in range(len(rings) - 1):
        for k in range(seg):
            a = rings[lat]
            b2_, = (rings[lat + 1],)
            b2.faces.new((a[k], a[(k + 1) % seg], b2_[(k + 1) % seg], b2_[k]))
    for k in range(seg):
        b2.faces.new((rings[-1][k], rings[-1][(k + 1) % seg], bot))


def box(b2, cx, cy, cz, sx, sy, sz):
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    v = [b2.verts.new(p) for p in (
        (cx - hx, cy - hy, cz - hz), (cx + hx, cy - hy, cz - hz), (cx + hx, cy + hy, cz - hz), (cx - hx, cy + hy, cz - hz),
        (cx - hx, cy - hy, cz + hz), (cx + hx, cy - hy, cz + hz), (cx + hx, cy + hy, cz + hz), (cx - hx, cy + hy, cz + hz))]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (3, 0, 4, 7)):
        b2.faces.new([v[i] for i in f])


def prism(b2, x0, x1, y0, y1, z0, rx0, rx1, z_apex):
    v = [b2.verts.new(p) for p in (
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (rx0, (y0 + y1) / 2, z_apex), (rx1, (y0 + y1) / 2, z_apex))]
    for f in ((0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5)):
        b2.faces.new([v[i] for i in f])


# legs (navy trousers) + shoes
for sx in (-1, 1):
    emit(lambda b2, sx=sx: tube(b2, sx * 0.11, 0.0, 0.12, 0.62, 0.075, 0.07), C_PANTS)
    emit(lambda b2, sx=sx: box(b2, sx * 0.11, 0.02, 0.07, 0.15, 0.30, 0.14), C_SHOE)

# torso: white shirt
emit(lambda b2: box(b2, 0.0, 0.0, 0.86, 0.42, 0.26, 0.52), C_SHIRT)
# navy skirt flaring over the hips
emit(lambda b2: tube(b2, 0.0, 0.0, 0.50, 0.70, 0.36, 0.30, seg=8), C_PANTS)
# arms: white sleeves + skin hands
for sx in (-1, 1):
    emit(lambda b2, sx=sx: tube(b2, sx * 0.28, 0.0, 0.72, 1.14, 0.062, 0.05, seg=6), C_SHIRT)
    emit(lambda b2, sx=sx: ball(b2, sx * 0.28, 0.0, 1.20, 0.055), C_SKIN)

# head + face
emit(lambda b2: ball(b2, 0.0, 0.0, 1.42, 0.155, seg=10), C_SKIN)
# hair cap (upper hemisphere slightly bigger) + bangs
emit(lambda b2: ball(b2, 0.0, 0.01, 1.455, 0.163, seg=10), C_HAIR)
emit(lambda b2: box(b2, 0.0, -0.115, 1.505, 0.26, 0.09, 0.075), C_HAIR)
# ponytail buns with red ties
for sx in (-1, 1):
    emit(lambda b2, sx=sx: ball(b2, sx * 0.155, 0.06, 1.44, 0.075, seg=6), C_HAIR)
    emit(lambda b2, sx=sx: tube(b2, sx * 0.155, 0.06, 1.49, 1.505, 0.045, 0.045, seg=6), C_SCARF)
# eyes + smile (front is -Y)
emit(lambda b2: box(b2, -0.055, -0.148, 1.45, 0.032, 0.02, 0.045), C_HAIR)
emit(lambda b2: box(b2, 0.055, -0.148, 1.45, 0.032, 0.02, 0.045), C_HAIR)
emit(lambda b2: box(b2, 0.0, -0.15, 1.375, 0.06, 0.02, 0.012), C_HAIR)
# red scarf (红领巾) around the neck with a front triangle
emit(lambda b2: tube(b2, 0.0, 0.0, 1.24, 1.28, 0.115, 0.10, seg=8), C_SCARF)
emit(lambda b2: prism(b2, -0.09, 0.09, -0.16, -0.10, 1.05, 0.0, 0.0, 1.22), C_SCARF)

# schoolbag on the back (+Y)
emit(lambda b2: box(b2, 0.0, 0.19, 1.00, 0.34, 0.16, 0.44), C_BAG)
emit(lambda b2: box(b2, 0.0, 0.275, 1.06, 0.24, 0.03, 0.16), C_BAG_D)
for sx in (-1, 1):
    emit(lambda b2, sx=sx: box(b2, sx * 0.105, -0.145, 1.16, 0.055, 0.035, 0.36), C_BAG_D)

me = bpy.data.meshes.new("StudentGirl")
pmb.to_mesh(me)
pmb.free()
if me.color_attributes:
    me.color_attributes.active_color = me.color_attributes[0]
obj = bpy.data.objects.new("StudentGirl", me)
bpy.context.collection.objects.link(obj)
print("STUDENT_TRIS", len(me.polygons))

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
direction = Vector((0.0, 0.0, 0.75)) - Vector((1.6, -2.6, 1.95))
cam.location = (1.6, -2.6, 1.95)
cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
scene.camera = cam
scene.render.filepath = str(ROOT / "tools/renders/student_preview.png")
bpy.ops.render.render(write_still=True)
print("RENDERED student_preview")

bpy.ops.object.select_all(action="DESELECT")
obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, use_selection=True)
print("WROTE", OUT)
