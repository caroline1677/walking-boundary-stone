"""Plan walkable layout points against the real scan geometry.

Run via Blender CLI:
  blender --background --python tools/plan_walkable.py

Builds a multi-layer ground grid (so stairs, the arch tunnel and the valley
floor all survive), flood-fills walkable cells from the spawn column with the
same step limits as PlayerController/WorldManager, then scores candidate
points for each layout slot. Prints PLAN_* JSON lines for grep.
"""

import json
from pathlib import Path

import bpy
from mathutils import Vector

SOURCE = Path(r"D:\HKU-ds\QCH\友谊关材料\图片\友谊关资产\0f142ad8e27a7e7eb910baff2a832ba7.ply")
OUT = Path(r"D:\HKU-ds\QCH\界碑智能体\tools\renders\walkable.json")

SPAWN = (8.4, -4.5)
SPAWN_Z_HINT = 4.35
GATE = Vector((-2.0, 0.0))
STEP_UP = 0.75
STEP_DOWN = 1.2
MIN_NZ = 0.55
EYE = 1.6

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.ply_import(filepath=str(SOURCE))
scene = bpy.context.scene
depsgraph = bpy.context.evaluated_depsgraph_get()


def column_layers(x, y, max_layers=10, z_top=25.0):
    origin = Vector((x, y, z_top))
    direction = Vector((0.0, 0.0, -1.0))
    layers = []
    for _ in range(max_layers):
        hit, location, normal, *_ = scene.ray_cast(depsgraph, origin, direction, distance=80.0)
        if not hit:
            break
        layers.append({
            "z": round(location.z, 2),
            "nz": round(normal.z, 2),
        })
        origin = location + direction * 0.02
    return layers


X_MIN, X_MAX, Y_MIN, Y_MAX = -14.0, 12.0, -9.0, 6.0
STEP = 0.5
grid = {}
x = X_MIN
while x <= X_MAX + 1e-6:
    y = Y_MIN
    while y <= Y_MAX + 1e-6:
        walk = [item["z"] for item in column_layers(x, y) if item["nz"] >= MIN_NZ]
        if walk:
            grid[(round(x, 2), round(y, 2))] = walk
        y += STEP
    x += STEP
print("GRID_CELLS", len(grid))


def nearest_cell(point):
    key = (round(round(point[0] / STEP) * STEP, 2), round(round(point[1] / STEP) * STEP, 2))
    return key if key in grid else None


def seed_spawn():
    cell = nearest_cell(SPAWN)
    if cell is None:
        raise SystemExit("spawn column has no walkable layer")
    levels = grid[cell]
    best = min(levels, key=lambda z: abs(z - SPAWN_Z_HINT))
    return cell, best


start_cell, start_z = seed_spawn()
print("SPAWN_SEED", start_cell, start_z)

# Flood fill over (cell, level) nodes so stairs/tunnels keep working.
nodes = {}
start_node = (start_cell, start_z)
nodes[start_node] = True
frontier = [start_node]
while frontier:
    next_frontier = []
    for (cell, z) in frontier:
        cx, cy = cell
        for dx, dy in ((STEP, 0), (-STEP, 0), (0, STEP), (0, -STEP)):
            neighbour = (round(cx + dx, 2), round(cy + dy, 2))
            for nz in grid.get(neighbour, []):
                delta = nz - z
                if delta > STEP_UP or delta < -STEP_DOWN:
                    continue
                node = (neighbour, nz)
                if node not in nodes:
                    nodes[node] = True
                    next_frontier.append(node)
    frontier = next_frontier
print("REACHABLE_NODES", len(nodes))

reachable = {}
for (cell, z) in nodes:
    reachable.setdefault(cell, []).append(z)
print("REACHABLE_CELLS", len(reachable))


def gate_visibility(x, y, z):
    eye = Vector((x, y, z + EYE))
    best = 0.0
    for target_z in (0.5, 1.5, 2.5, 3.5, 4.5, 5.5):
        target = Vector((GATE.x, GATE.y, target_z))
        direction = target - eye
        distance = direction.length
        if distance < 3.0:
            continue
        hit, location, *_ = scene.ray_cast(depsgraph, eye, direction.normalized(), distance=distance)
        ratio = 1.0 if not hit else (Vector(location) - eye).length / distance
        best = max(best, ratio)
    return round(best, 3)


def flatness(cell):
    cx, cy = cell
    levels = []
    for dx, dy in ((STEP, 0), (-STEP, 0), (0, STEP), (0, -STEP), (0.0, 0.0)):
        neighbour = (round(cx + dx, 2), round(cy + dy, 2))
        for z in reachable.get(neighbour, []):
            levels.append(z)
    if len(levels) < 5:
        return 0.0
    return round(1.0 - min(1.0, (max(levels) - min(levels)) / 1.6), 3)


def dist(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def pick(name, scorer, limit=8):
    scored = []
    for cell, levels in reachable.items():
        for z in levels:
            score = scorer(cell, z)
            if score is None:
                continue
            scored.append((score, cell, z))
    scored.sort(key=lambda item: -item[0])
    picks = []
    for score, cell, z in scored[:limit]:
        picks.append({
            "score": round(score, 3),
            "x": cell[0], "y": cell[1], "z": z,
            "vis": gate_visibility(cell[0], cell[1], z),
            "flat": flatness(cell),
            "gate_dist": round(dist(cell, (GATE.x, GATE.y)), 1),
            "spawn_dist": round(dist(cell, SPAWN), 1),
        })
    print(f"PLAN_{name.upper()}", json.dumps(picks, ensure_ascii=False))
    return picks


def flat_min(score_min):
    def wrapper(cell, z):
        inner = score_min(cell, z)
        if inner is None:
            return None
        flat = flatness(cell)
        if flat < 0.72:
            return None
        return inner + flat * 0.5
    return wrapper


suggestions = {}
suggestions["grandpa"] = pick("grandpa", flat_min(lambda cell, z: (
    2.0 - abs(dist(cell, SPAWN) - 4.2) * 0.3 if 2.5 <= dist(cell, SPAWN) <= 7.0 else None
)))

suggestions["gate"] = pick("gate", flat_min(lambda cell, z: (
    (3.5 - dist(cell, (GATE.x, GATE.y))) * 0.8 + (0.6 - abs(z + 0.24)) * 0.5
    if dist(cell, (GATE.x, GATE.y)) <= 3.5 and abs(z + 0.24) <= 0.7 else None
)))

suggestions["boundary"] = pick("boundary", flat_min(lambda cell, z: (
    3.0 - dist(cell, (7.2, 1.8)) * 0.5 + (1.5 if cell[1] >= 0.5 else -2.0)
    if dist(cell, (7.2, 1.8)) <= 5.0 else None
)))

suggestions["terrain"] = pick("terrain", lambda cell, z: (
    (0.35 + 0.65 * min(1.0, z / 4.0)) * (1.6 if dist(cell, (GATE.x, GATE.y)) <= 12.0 else 0.4)
    if z >= 1.4 and dist(cell, (GATE.x, GATE.y)) >= 3.5 else None
))

for slot, anchor in {"road": (4.0, -2.2), "steps": (-2.8, -1.8), "wall": (-4.1, 1.1), "sign": (5.5, 0.2), "view": (0.0, -3.0)}.items():
    suggestions[slot] = pick(slot, flat_min(lambda cell, z, a=anchor: (
        2.5 - dist(cell, a) * 0.6 if dist(cell, a) <= 3.0 else None
    )), limit=5)

OUT.write_text(json.dumps({
    "spawnSeed": {"cell": list(start_cell), "z": start_z},
    "reachableCells": [[cell[0], cell[1], levels] for cell, levels in sorted(reachable.items())],
    "suggestions": suggestions,
}, ensure_ascii=False), encoding="utf-8")
print("WROTE", OUT)
