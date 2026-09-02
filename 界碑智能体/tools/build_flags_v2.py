"""Animated waving flags for the v2 gate (cloth built as a segmented grid).

Run via Blender CLI:
  blender --background --python tools/build_flags_v2.py

Output: assets/models/pass-v2-flags.glb — contains FlagPoles (static) plus
FlagCloth0..3 meshes; the frontend waves their vertices every frame.
Cloth streams toward -Y (over the plaza), flutter axis is X.
"""

import math
from pathlib import Path

import bmesh
import bpy

ROOT = Path(r"D:\HKU-ds\QCH\界碑智能体")
OUT = ROOT / "assets/models/pass-v2-flags.glb"

C_POLE = (0.30, 0.28, 0.26)
C_GOLD = (0.85, 0.68, 0.25)
C_FLAG = (0.76, 0.13, 0.11)

bpy.ops.wm.read_homefile(use_empty=True)

FLAGS = (
    (-8.6, -3.8, 8.0, 2.3),
    (8.6, -3.8, 8.0, 2.3),
    (-3.4, -2.4, 19.2, 1.8),
    (3.4, -2.4, 19.2, 1.8),
)

poles = bmesh.new()
cloth_meshes = []


def emit_pole(pmb, px, py, z0, h):
    tmp = bmesh.new()
    seg = 6
    r = 0.055
    pts0 = [(px + math.cos(k / seg * 2 * math.pi) * r, py + math.sin(k / seg * 2 * math.pi) * r, z0) for k in range(seg)]
    pts1 = [(px + math.cos(k / seg * 2 * math.pi) * r * 0.7, py + math.sin(k / seg * 2 * math.pi) * r * 0.7, z0 + h) for k in range(seg)]
    v0 = [tmp.verts.new(p) for p in pts0]
    v1 = [tmp.verts.new(p) for p in pts1]
    for k in range(seg):
        tmp.faces.new((v0[k], v0[(k + 1) % seg], v1[(k + 1) % seg], v1[k]))
    tip = tmp.verts.new((px, py, z0 + h + 0.12))
    for k in range(seg):
        tmp.faces.new((v1[k], v1[(k + 1) % seg], tip))
    layer = tmp.loops.layers.color.new("Col")
    for f in tmp.faces:
        for l in f.loops:
            l[layer] = (*C_POLE, 1.0)
    me = bpy.data.meshes.new("pole")
    tmp.to_mesh(me)
    tmp.free()
    pmb.from_mesh(me)
    bpy.data.meshes.remove(me)


def emit_cloth(px, py, z_top, length):
    tmp = bmesh.new()
    nx, nz = 8, 3
    w, h = 1.15, 0.62
    grid = []
    for iz in range(nz + 1):
        row = []
        for ix in range(nx + 1):
            lx = ix / nx
            lz = iz / nz
            row.append(tmp.verts.new((px + (lx - 0.5) * w, py - lx * length, z_top - lz * h)))
        grid.append(row)
    for iz in range(nz):
        for ix in range(nx):
            tmp.faces.new((grid[iz][ix], grid[iz][ix + 1], grid[iz + 1][ix + 1], grid[iz + 1][ix]))
    layer = tmp.loops.layers.color.new("Col")
    for f in tmp.faces:
        for l in f.loops:
            l[layer] = (*C_FLAG, 1.0)
    me = bpy.data.meshes.new(f"FlagCloth{len(cloth_meshes)}")
    tmp.to_mesh(me)
    tmp.free()
    cloth_meshes.append(me)


for (px, py, z0, h) in FLAGS:
    emit_pole(poles, px, py, z0, h)
    emit_cloth(px, py, z0 + h - 0.05, 1.15)

# gold finials on the pole tops
for (px, py, z0, h) in FLAGS:
    tmp = bmesh.new()
    seg = 6
    r = 0.09
    v0 = [tmp.verts.new((px + math.cos(k / seg * 2 * math.pi) * r, py + math.sin(k / seg * 2 * math.pi) * r, z0 + h + 0.12)) for k in range(seg)]
    v1 = [tmp.verts.new((px + math.cos(k / seg * 2 * math.pi) * r, py + math.sin(k / seg * 2 * math.pi) * r, z0 + h + 0.26)) for k in range(seg)]
    for k in range(seg):
        tmp.faces.new((v0[k], v0[(k + 1) % seg], v1[(k + 1) % seg], v1[k]))
    top = tmp.verts.new((px, py, z0 + h + 0.34))
    for k in range(seg):
        tmp.faces.new((v1[(k + 1) % seg], v1[k], top))
    layer = tmp.loops.layers.color.new("Col")
    for f in tmp.faces:
        for l in f.loops:
            l[layer] = (*C_GOLD, 1.0)
    me = bpy.data.meshes.new("finial")
    tmp.to_mesh(me)
    tmp.free()
    poles.from_mesh(me)
    bpy.data.meshes.remove(me)

poles_me = bpy.data.meshes.new("FlagPoles")
poles.to_mesh(poles_me)
poles.free()
if poles_me.color_attributes:
    poles_me.color_attributes.active_color = poles_me.color_attributes[0]
poles_obj = bpy.data.objects.new("FlagPoles", poles_me)
bpy.context.collection.objects.link(poles_obj)

cloth_objs = []
for me in cloth_meshes:
    if me.color_attributes:
        me.color_attributes.active_color = me.color_attributes[0]
    o = bpy.data.objects.new(me.name, me)
    bpy.context.collection.objects.link(o)
    cloth_objs.append(o)
print("V2_FLAGS", len(cloth_objs))

scene = bpy.context.scene
scene.render.resolution_x = 1000
scene.render.resolution_y = 700
scene.render.image_settings.file_format = "PNG"
scene.render.engine = "BLENDER_WORKBENCH"
shading = scene.display.shading
shading.light = "STUDIO"
shading.color_type = "VERTEX"
from mathutils import Vector
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.collection.objects.link(cam)
loc = Vector((6.0, -10.0, 13.5))
direction = Vector((0.0, -3.0, 10.0)) - loc
cam.location = loc
cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
scene.camera = cam
scene.render.filepath = str(ROOT / "tools/renders/v2_flags_preview.png")
bpy.ops.render.render(write_still=True)
print("RENDERED flags preview")

bpy.ops.object.select_all(action="DESELECT")
poles_obj.select_set(True)
for o in cloth_objs:
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, use_selection=True)
print("WROTE", OUT)
