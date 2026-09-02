"""Prepare the Hunyuan Friendship Pass mesh for browser collision queries.

The SPZ remains untouched and is used as the visual world. This script only
creates a reduced GLB copy of the matching PLY mesh for ground and obstacle
collision in Three.js.
"""

from pathlib import Path

import bpy
from mathutils import Vector


SOURCE = Path(r"D:\HKU-ds\QCH\友谊关材料\图片\友谊关资产\0f142ad8e27a7e7eb910baff2a832ba7.ply")
OUTPUT = Path(r"D:\HKU-ds\QCH\界碑智能体\assets\worlds\friendship-pass-collider.glb")
TARGET_FACES = 90_000
ROUTE_LIFT = 0.09
ROUTE_WIDTH = 1.25

# Blender is Z-up. The browser converts these to Three.js Y-up when loading.
# These points were ray-cast against the original PLY and follow real visible
# ground; the added strips only make that route reliably walkable.
# Design flow: outer entrance -> grandpa node -> junction -> road -> gate -> boundary.
ROUTE_POINTS = {
    "entrance": (8.4, -4.5, 4.30),
    "waypoint": (6.0, -4.5, 4.20),
    "grandpa": (4.4, -2.8, 2.94),
    "terrain": (0.0, -3.0, 3.49),
    "terrain_mid_1": (1.0, -2.0, 1.92),
    "terrain_mid_2": (1.0, -1.0, 1.10),
    "terrain_mid_3": (1.0, 0.0, -0.49),
    "gate": (-2.0, 0.0, -0.24),
    "boundary_mid": (3.0, 1.0, -1.86),
    "boundary": (7.2, 1.8, -2.71),
}
ROUTES = (
    ("entrance", "waypoint"),
    ("waypoint", "grandpa"),
    ("grandpa", "terrain"),
    ("terrain", "terrain_mid_1", "terrain_mid_2", "terrain_mid_3", "gate"),
    ("gate", "boundary_mid", "boundary"),
)
PAD_POINTS = ("entrance", "grandpa", "terrain", "gate", "boundary")


def create_route_segment(name, start, end, width=ROUTE_WIDTH):
    """Create a thin, upward-facing quad corridor between two sampled points."""
    start = Vector(start)
    end = Vector(end)
    direction = Vector((end.x - start.x, end.y - start.y, 0.0))
    side = Vector((-direction.y, direction.x, 0.0)).normalized() * (width / 2)
    lift = Vector((0.0, 0.0, ROUTE_LIFT))
    vertices = [start - side + lift, end - side + lift, end + side + lift, start + side + lift]
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    mesh.from_pydata(vertices, [], [(0, 1, 2, 3)])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def create_route_colliders():
    route_objects = []
    for route_index, route in enumerate(ROUTES):
        for segment_index, (start_id, end_id) in enumerate(zip(route, route[1:])):
            route_objects.append(
                create_route_segment(
                    f"WalkRoute_{route_index}_{segment_index}",
                    ROUTE_POINTS[start_id],
                    ROUTE_POINTS[end_id],
                )
            )
    for point_id in PAD_POINTS:
        center = Vector(ROUTE_POINTS[point_id])
        half = 0.9
        route_objects.append(
            create_route_segment(
                f"WalkPad_{point_id}",
                center + Vector((-half, 0.0, 0.0)),
                center + Vector((half, 0.0, 0.0)),
                width=half * 2,
            )
        )
    return route_objects


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.ply_import(filepath=str(SOURCE))
collider = bpy.context.active_object
collider.name = "WorldCollider"

source_faces = len(collider.data.polygons)
if source_faces > TARGET_FACES:
    modifier = collider.modifiers.new(name="BrowserColliderDecimate", type="DECIMATE")
    modifier.decimate_type = "COLLAPSE"
    modifier.ratio = TARGET_FACES / source_faces
    modifier.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = collider
    bpy.ops.object.modifier_apply(modifier=modifier.name)

for attribute in list(collider.data.color_attributes):
    collider.data.color_attributes.remove(attribute)
collider.data.materials.clear()
route_colliders = create_route_colliders()

bpy.ops.object.select_all(action="DESELECT")
collider.select_set(True)
for route_collider in route_colliders:
    route_collider.select_set(True)
bpy.context.view_layer.objects.active = collider
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(
    filepath=str(OUTPUT),
    export_format="GLB",
    use_selection=True,
    export_materials="NONE",
    export_attributes=False,
)

print(
    "COLLIDER_READY",
    {
        "source_faces": source_faces,
        "output_faces": len(collider.data.polygons),
        "vertices": len(collider.data.vertices),
        "route_colliders": len(route_colliders),
        "dimensions": [round(value, 3) for value in collider.dimensions],
        "output": str(OUTPUT),
    },
)
