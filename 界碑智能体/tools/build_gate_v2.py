"""Friendship Pass v2 gate — granite citadel modeled on the reference photos.

Run via Blender CLI:
  blender --background --python tools/build_gate_v2.py

Gray granite 城台 with a round arch passage (along Y), gold 友谊关 plaque,
two-tier cream pavilion with red columns and dark-green hip roofs, red flags,
and an old iron cannon by the gate. Front faces -Y (plaza side).

Output: assets/models/pass-v2-gate.glb + preview renders.
"""

import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

ROOT = Path(r"D:\HKU-ds\QCH\界碑智能体")
OUT = ROOT / "assets/models/pass-v2-gate.glb"
FONT = r"C:\Windows\Fonts\simhei.ttf"

C_GRANITE = (0.64, 0.62, 0.57)
C_GRANITE_D = (0.53, 0.51, 0.47)
C_DARK = (0.13, 0.12, 0.11)
C_CREAM = (0.91, 0.87, 0.77)
C_RED = (0.64, 0.21, 0.17)
C_ROOF = (0.17, 0.37, 0.31)
C_GOLD = (0.85, 0.68, 0.25)
C_IRON = (0.24, 0.24, 0.27)
C_WOOD = (0.44, 0.32, 0.21)

bpy.ops.wm.read_homefile(use_empty=True)

pmb = bmesh.new()


def emit(builder, color, offset=(0.0, 0.0, 0.0)):
    tmp = bmesh.new()
    builder(tmp)
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


def box(b2, x0, x1, y0, y1, z0, z1):
    v = [b2.verts.new(p) for p in (
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (3, 0, 4, 7)):
        b2.faces.new([v[i] for i in f])


def emit_box(color, x0, x1, y0, y1, z0, z1):
    emit(lambda b2: box(b2, x0, x1, y0, y1, z0, z1), color)


def emit_prism_roof(color, x0, x1, y0, y1, z0, rx0, rx1, z_apex):
    def build(b2):
        v = [b2.verts.new(p) for p in (
            (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
            (rx0, (y0 + y1) / 2, z_apex), (rx1, (y0 + y1) / 2, z_apex))]
        for f in ((0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5)):
            b2.faces.new([v[i] for i in f])
    emit(build, color)


# ---- citadel body (piers + spandrel), passage along Y ----------------------
Z_TOP = 8.0
for x0, x1 in ((-10.0, -2.5), (2.5, 10.0)):
    emit_box(C_GRANITE, x0, x1, -4.2, 4.2, -1.4, Z_TOP)
    emit_box(C_GRANITE_D, x0, x1, -4.2, 4.2, -1.4, 0.3)
emit_box(C_GRANITE, -2.5, 2.5, -4.2, 4.2, 6.1, Z_TOP)
# round-arch trim rings on the front face (passage itself stays open)


def emit_arch_fan(color, cy, r_in, r_out, z_center, y):
    def build(b2):
        seg = 10
        v_outer = [b2.verts.new((math.cos(math.pi * k / seg) * r_out, y, z_center + math.sin(math.pi * k / seg) * r_out)) for k in range(seg + 1)]
        v_inner = [b2.verts.new((math.cos(math.pi * k / seg) * r_in, y, z_center + math.sin(math.pi * k / seg) * r_in)) for k in range(seg + 1)]
        for k in range(seg):
            b2.faces.new([v_outer[k], v_outer[k + 1], v_inner[k + 1], v_inner[k]])
    emit(build, color)


emit_arch_fan(C_DARK, 0.0, 2.55, 3.35, 3.3, -4.36)
emit_arch_fan(C_GRANITE_D, 0.0, 3.35, 3.75, 3.3, -4.3)
# chamfer blocks softening the arch shoulders
for sx in (-1, 1):
    def wedge(b2, s=sx):
        v = [b2.verts.new(p) for p in (
            (s * 2.5, -4.2, 4.4), (s * 2.5, 4.2, 4.4), (s * 2.5, 4.2, 6.1), (s * 2.5, -4.2, 6.1),
            (s * 3.6, -4.2, 6.1), (s * 3.6, 4.2, 6.1))]
        for f in ((0, 1, 2, 3), (0, 3, 2, 4), (1, 5, 2), (3, 4, 5, 2), (0, 4, 5, 1)):
            b2.faces.new([v[i] for i in f])
    emit(wedge, C_GRANITE_D)

# plaque (dark board, gold text appended later)
emit_box(C_DARK, -2.1, 2.1, -4.5, -4.28, 6.6, 7.7)

for cz in (1.6, 3.4, 5.2):
    emit_box(C_GRANITE_D, -10.0, -2.5, -4.28, -4.18, cz, cz + 0.22)
    emit_box(C_GRANITE_D, 2.5, 10.0, -4.28, -4.18, cz, cz + 0.22)

# parapet with merlons around the citadel top
for (x0, x1, y0, y1) in ((-10.0, 10.0, -4.2, -3.4), (-10.0, 10.0, 3.4, 4.2),
                         (-10.0, -9.2, -4.2, 4.2), (9.2, 10.0, -4.2, 4.2)):
    emit_box(C_GRANITE, x0, x1, y0, y1, Z_TOP, Z_TOP + 0.5)
k = -9
while k <= 9:
    if abs(k) > 2:
        emit_box(C_GRANITE_D, k - 0.32, k + 0.32, -4.05, -3.55, Z_TOP + 0.5, Z_TOP + 1.25)
        emit_box(C_GRANITE_D, k - 0.32, k + 0.32, 3.55, 4.05, Z_TOP + 0.5, Z_TOP + 1.25)
    k += 1.1

# ---- pavilion tiers --------------------------------------------------------
emit_box(C_GRANITE_D, -7.0, 7.0, -3.5, 3.5, Z_TOP + 0.5, Z_TOP + 0.9)
T0 = Z_TOP + 0.9
emit_box(C_CREAM, -6.5, 6.5, -3.0, 3.0, T0, T0 + 4.2)
for sx in (-1, 0, 1):
    for sy in (-1, 1):
        cx = sx * 6.1 if sx else 0.0
        emit_box(C_RED, cx - (0.28 if sx else 0.14), cx + (0.28 if sx else 0.14),
                 sy * 2.85 - 0.16, sy * 2.85 + 0.16, T0, T0 + 4.2)
for sx in (-1, 1):
    emit_box(C_RED, sx * 6.2 - 0.16, sx * 6.2 + 0.16, -3.0, 3.0, T0, T0 + 4.2)
# windows on the front (-Y) face
for wx in (-4.2, 0.0, 4.2):
    emit_box(C_CREAM, wx - 1.05, wx + 1.05, -3.1, -3.02, T0 + 1.0, T0 + 3.2)
    emit_box(C_ROOF, wx - 0.85, wx + 0.85, -3.22, -3.08, T0 + 1.25, T0 + 2.95)
# balcony slab
emit_box(C_GRANITE_D, -7.4, 7.4, -3.9, 3.9, T0 + 4.2, T0 + 4.55)
for k in range(-7, 8):
    if abs(k) > 1:
        emit_box(C_GRANITE, k - 0.22, k + 0.22, -3.95, -3.6, T0 + 4.55, T0 + 5.15)
        emit_box(C_GRANITE, k - 0.22, k + 0.22, 3.6, 3.95, T0 + 4.55, T0 + 5.15)
emit_prism_roof(C_ROOF, -7.9, 7.9, -4.4, 4.4, T0 + 4.55, -2.0, 2.0, T0 + 6.6)

T1 = T0 + 6.6
emit_box(C_CREAM, -4.6, 4.6, -2.3, 2.3, T1, T1 + 3.3)
for sx in (-1, 0, 1):
    for sy in (-1, 1):
        cx = sx * 4.3 if sx else 0.0
        emit_box(C_RED, cx - (0.24 if sx else 0.12), cx + (0.24 if sx else 0.12),
                 sy * 2.2 - 0.14, sy * 2.2 + 0.14, T1, T1 + 3.3)
for sx in (-1, 1):
    emit_box(C_RED, sx * 4.4 - 0.14, sx * 4.4 + 0.14, -2.3, 2.3, T1, T1 + 3.3)
emit_box(C_ROOF, -1.0, 1.0, -2.42, -2.3, T1 + 1.0, T1 + 2.3)
emit_box(C_GRANITE_D, -5.4, 5.4, -3.1, 3.1, T1 + 3.3, T1 + 3.6)
emit_prism_roof(C_ROOF, -6.3, 6.3, -3.9, 3.9, T1 + 3.6, -1.4, 1.4, T1 + 5.5)

# flag pole + red flag on the ridge
emit_box(C_GRANITE_D, -0.1, 0.1, -0.1, 0.1, T1 + 5.5, T1 + 7.6)
emit_box(C_RED, 0.1, 1.35, -0.03, 0.03, T1 + 6.8, T1 + 7.4)
# red lantern pair under the first eave
for lx in (-5.2, 5.2):
    emit_box(C_RED, lx - 0.35, lx + 0.35, -3.55, -3.05, T0 + 3.4, T0 + 4.1)

# ---- old iron cannon by the gate -------------------------------------------


def emit_cannon():
    cx, cy = -6.4, -6.8

    def barrel(b2):
        seg = 8
        r = 0.30
        y0, y1 = cy - 1.5, cy + 1.1
        ring0 = [b2.verts.new((cx + math.cos(k / seg * 2 * math.pi) * r, y0, 1.35 + math.sin(k / seg * 2 * math.pi) * r)) for k in range(seg)]
        ring1 = [b2.verts.new((cx + math.cos(k / seg * 2 * math.pi) * r * 0.75, y1, 1.35 + math.sin(k / seg * 2 * math.pi) * r * 0.75)) for k in range(seg)]
        for k in range(seg):
            b2.faces.new([ring0[k], ring0[(k + 1) % seg], ring1[(k + 1) % seg], ring1[k]])
        b2.faces.new(ring1)
        b2.faces.new(ring0[::-1])

    def wheel(b2, wx):
        seg = 8
        r = 0.62
        v0 = [b2.verts.new((wx + math.cos(k / seg * 2 * math.pi) * r, cy + 0.55 + math.sin(k / seg * 2 * math.pi) * r, 0.75)) for k in range(seg)]
        v1 = [b2.verts.new((wx + math.cos(k / seg * 2 * math.pi) * r, cy + 0.75 + math.sin(k / seg * 2 * math.pi) * r, 0.75)) for k in range(seg)]
        for k in range(seg):
            b2.faces.new([v0[k], v0[(k + 1) % seg], v1[(k + 1) % seg], v1[k]])
        b2.faces.new(v0)
        b2.faces.new(v1[::-1])

    emit(barrel, C_IRON)
    emit(lambda b2: wheel(b2, cx - 0.5), C_WOOD)
    emit(lambda b2: wheel(b2, cx + 0.5), C_WOOD)
    emit_box(C_WOOD, cx - 0.55, cx + 0.55, cy - 1.2, cy + 1.0, 0.55, 1.0)


emit_cannon()

# ---- gold 友谊关 plaque text -------------------------------------------------

curve = bpy.data.curves.new("PlaqueText", type="FONT")
curve.body = "友谊关"
curve.size = 1.45
curve.extrude = 0.09
curve.align_x = "CENTER"
curve.font = bpy.data.fonts.load(FONT)
text_obj = bpy.data.objects.new("PlaqueText", curve)
bpy.context.collection.objects.link(text_obj)
text_obj.location = (0.0, -4.62, 6.85)
text_obj.rotation_euler = (math.pi / 2, 0.0, 0.0)
bpy.context.view_layer.update()
tme = text_obj.to_mesh()
tbm = bmesh.new()
tbm.from_mesh(tme)
layer = tbm.loops.layers.color.new("Col")
for f in tbm.faces:
    for l in f.loops:
        l[layer] = (*C_GOLD, 1.0)
for v in tbm.verts:
    pass
# shift text mesh into place (local coords are around origin at z baseline)
shift = Vector((0.0, -4.6, 6.35))
for v in tbm.verts:
    v.co += shift
for p in tbm.faces:
    p.smooth = False
tme2 = bpy.data.meshes.new("PlaqueTextMesh")
tbm.to_mesh(tme2)
tbm.free()
for p in tme2.polygons:
    p.use_smooth = False
pmb.from_mesh(tme2)
bpy.data.meshes.remove(tme2)
text_obj.to_mesh_clear()
bpy.data.objects.remove(text_obj, do_unlink=True)
bpy.data.curves.remove(curve)


# ---- finalize ---------------------------------------------------------------

me = bpy.data.meshes.new("V2Gate")
pmb.to_mesh(me)
pmb.free()
if me.color_attributes:
    me.color_attributes.active_color = me.color_attributes[0]
obj = bpy.data.objects.new("V2Gate", me)
bpy.context.collection.objects.link(obj)
print("V2_GATE_TRIS", len(me.polygons))

scene = bpy.context.scene
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
    "v2_gate_front": ((0.0, -34.0, 5.0), (0.0, 0.0, 7.0), 35),
    "v2_gate_quarter": ((16.0, -26.0, 10.0), (0.0, 0.0, 7.5), 35),
    "v2_gate_arch": ((0.0, -12.0, 2.2), (0.0, 0.0, 3.4), 32),
}.items():
    scene.camera = add_camera(name, loc, tgt, lens)
    scene.render.filepath = str(ROOT / f"tools/renders/{name}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", name)

bpy.ops.object.select_all(action="DESELECT")
obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, use_selection=True)
print("WROTE", OUT)
