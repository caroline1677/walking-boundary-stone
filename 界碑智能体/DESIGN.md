# 友谊关研学空间 · 设计纲领（DESIGN.md）

> 2026-08-30 定稿。所有改动（UI、NPC、Collider、GLB、任务流）以此文件为统一目标。
> 核心场景逻辑一句话：**远观关楼产生好奇 → 界碑爷爷提出问题 → 孩子自由寻找建筑/地理/边界三个证据 → 回来自己形成答案。**

## 一、体验设计（10–15 分钟自由探索）

- 玩家从**友谊关外围入口**出生（上道东端，八号岗一带），远看关楼产生好奇，沿道路向核心探索。
- **界碑爷爷**是任务发起人：不直接讲历史，只说「今天我先不告诉你答案。去友谊关里找三个线索，回来告诉我为什么这座关会建在这里。」
- 接任务前，三个研学点**锁定**（E 不触发）；接任务后三线自由探索，无强制顺序。
- 三个研学区域：
  1. **关楼（任务一·建筑侦探）**：城门洞→通行、城墙→防守、高处关楼→观察，三点全看才给「关隘建筑」证据卡。
  2. **山地/道路观察点（任务二·地形侦探）**：站在路口高处看道路从山间穿过，选择题主答「山地之间的重要通道」→「山地通道」证据卡。
  3. **界碑（任务三·边界侦探）**：安静角落的独立界碑模型（中国 / 1117 / 2001，国徽），逐项观察 → 「边界」证据卡。
- 集齐三证回访爷爷：孩子**选关键词 + 用自己的话写结论**，Coze 智能体以爷爷口吻点评一句，生成《我的友谊关研学卡》。
- 道路/城墙/石阶等处散布 5 个**自由发现点**（可选历史碎片，不占主线）。
- UI 三件套：右上任务面板、中央 E 提示、手册/对话浮层。3D 世界占主画面，不做 Dashboard；儿童友好但不卡通幼稚。

## 二、技术架构

- **视觉层**：`WORLD_STYLE`（js/AssetManager.js）= `"toon"`（Blender 低模绘本风：toon-terrain / toon-props / toon-gate）；`"splat"` 为混元 3D 实景扫描回退（SPZ + SparkRenderer）。
- **碰撞层**：`assets/worlds/friendship-pass-collider.glb` = 抽稀 PLY（9 万面）+ 步道带（WalkRoute/WalkPad），由 Blender CLI 生成。
- **任务层**：QuestManager（not-started → active → return-to-npc → complete）+ InteractionManager（`item.enabled` 门控）+ UIManager（对话/证据卡/研学卡）。
- **智能体**：`/api/chat`（server.py 代理 Coze），终局爷爷点评用，前端失败自动降级为无点评研学卡。**注意：本机 Redis 为老版本，server.py 已固定 `protocol=2`，勿改回。**
- **坐标换算**：Blender Z-up `(x,y,z)` → Three.js `(x, z, -y)`。layout JSON 存 Three.js 坐标。

## 三、标定基线（layout v7 = 规范版本）

| 点 | Three.js 坐标 | 依据 |
|---|---|---|
| spawn 出生点 | (8.4, 4.35, 4.5) | 上道东端，步道带起点，视关楼 vis=1.0（probe_visibility.py） |
| grandpa 爷爷 | (5.5, 4.14, 4.0, rotY 1.4) | 入口→道路的自然节点，plan_walkable.py 实测，位于步道带 |
| gate 关楼 | (-2.0, -0.24, 0) | 城门洞南口，塔顶 z≈5.5（Blender PLY 柱测） |
| terrain 地形点 | (0.0, 3.49, 3.0) | 路口高地，同见山/路/关（视线检测确认） |
| boundary 界碑 | (7.2, -2.71, -1.8) | 关内东侧安静角落，步道带终点，石碑 GLB 朝向 rotY -1.38 |

改点位必须：Blender 对源 PLY 射线实测 + 确认步道带覆盖 + layout JSON 版本 +1，不要凭空猜坐标。

## 四、Blender 工具链（全部无头 CLI）

`"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --python tools/<脚本>.py`

| 脚本 | 作用 |
|---|---|
| `prepare_hunyuan_world.py` | PLY→碰撞 GLB + 步道带（entrance→waypoint→grandpa→terrain→mids→gate→boundary） |
| `build_boundary_stone.py` | 界碑 GLB（中国 1117 / 2001 / 国徽，实物照片 assets/友谊关界碑.jpg 为准） |
| `build_grandpa.py` | 界碑爷爷 GLB（7 棱石身、斗笠、红头巾、拐杖，正面 -Y/导入后 +Z） |
| `probe_visibility.py` | 关楼视线/地面网格检测（选点依据） |
| `plan_walkable.py` | 可达性 BFS（Codex 建，spawn 步高 0.75/0.5） |
| `build_gate_toon.py` / `build_world_toon.py` | toon 关楼 / toon 地形草木（Codex 建） |
| `render_scene_views.py` / `survey_round2.py` / `inspect_layout.py` | 勘测渲染 / 标高查询 |

## 五、自动化测试钩子（?debug 模式）

`window.__study`：`player / interactions / quest / npc / cameraController`、`items()`（交互项+距离）、`current()`、
`step(times, dt)`（**手动推帧**——IAB 面板隐藏时 rAF 会暂停，自动化测试必须用 step 驱动，Playwright click 会超时，DOM 用原生 `.click()`）。

## 六、已知问题 / 待办

1. **toon 地形与碰撞体高度不完全一致**：发现点/标记可能悬空或入地（标记按碰撞体落地）。归属：toon 侧对齐 toon-terrain，或统一用碰撞体高度差值。
2. 小地图按钮仍为占位；`player-girl.glb` 缺失（玩家为橙色占位小人）。
3. sessionStorage 保存任务进度：改任务流后联调记得 `sessionStorage.clear()`。
4. 下一步候选：小地图、研学卡导出图片、自由发现点扩充、语音（Fish TTS 已配好）。
