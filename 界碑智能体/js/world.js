import * as THREE from "three";
import { AssetManager } from "./AssetManager.js?v=v2b";
import { CameraController } from "./CameraController.js?v=v2a";
import { DebugManager } from "./DebugManager.js?v=20260828-playable9";
import { DiscoveryManager } from "./DiscoveryManager.js?v=20260831-labels";
import { InteractionManager } from "./InteractionManager.js?v=20260828-playable4";
import { LayoutManager } from "./LayoutManager.js?v=20260828-route1";
import { NPCManager } from "./NPCManager.js?v=20260831-chat2";
import { GrandpaChat } from "./GrandpaChat.js?v=chat2";
import { PlayerController } from "./PlayerController.js?v=20260901-walk1";
import { QuestManager } from "./QuestManager.js?v=20260831-hb1";
import { UIManager } from "./UIManager.js?v=20260901-eta1";
import { WorldManager } from "./WorldManager.js?v=v2b";
import { FRIENDSHIP_PASS_DISCOVERIES } from "../data/friendship-pass-discoveries.js?v=20260831-labels";
import { STUDY_POINTS } from "../data/friendship-pass-quests.js?v=20260830-quest1";
import { POST_DISCOVERIES } from "../data/post-discoveries.js?v=p1";

// "pass"：友谊关关楼场景 · "post"：边境哨所场景（研学下一站）
const SCENE = new URLSearchParams(location.search).get("scene") === "post" ? "post" : "pass";
const MAP_BOUNDS = SCENE === "post"
  ? { img: "assets/ui/post-minimap.png?v=p2", x0: -22, x1: 22, z0: -21, z1: 23 }
  : { img: "assets/ui/pass-minimap.png?v=p2", x0: -46, x1: 46, z0: -36, z1: 56 };
const minimapPoints = [];

const canvas = document.querySelector("#three-canvas");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.75));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.88;
renderer.shadowMap.enabled = true;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xb8c4bd);
const camera = new THREE.PerspectiveCamera(58, 1, 0.04, 300);
const hemisphere = new THREE.HemisphereLight(0xf5f0e6, 0x52685b, 2.2);
scene.add(hemisphere);
scene.userData.hemisphere = hemisphere;
const sun = new THREE.DirectionalLight(0xfff2d4, 2.4);
sun.position.set(-14, 25, 12);
sun.castShadow = true;
scene.add(sun);
scene.userData.sun = sun;

const ui = new UIManager();
const assets = new AssetManager();
const world = new WorldManager({ scene, renderer, assets });
const cameraController = new CameraController(camera, canvas, world);
const player = new PlayerController({ world, cameraController, assets });
world.root.add(player.group);
const quest = new QuestManager(ui, SCENE);
const interactions = new InteractionManager({ player, ui });
const grandpaChat = new GrandpaChat({ model: null, quest });
const npc = new NPCManager({ world, assets, interactions, quest, ui, chat: grandpaChat });
const discoveries = new DiscoveryManager({ world, interactions, quest, ui });
const questMarkers = [];
const layoutManager = new LayoutManager(SCENE === "post" ? "data/post-layout.json" : "data/friendship-pass-layout.json");

window.submitStudentAnswer = (text) => {
  console.info("[submitStudentAnswer placeholder]", text);
  return Promise.resolve({ ok: true, text });
};

function resize() {
  const width = innerWidth;
  const height = innerHeight;
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height, false);
}

// 界碑正面朝向关楼方向（玩家从门洞方向走近时读到"中国 1117"）。
const BOUNDARY_STONE_YAW = -1.38;

function addStudyPoints() {
  const colors = { gate: 0xb54f42, boundary: 0xd5ad55, terrain: 0x4d8061 };
  const studyItems = [];
  STUDY_POINTS.forEach((point) => {
    const position = layoutManager.vector(point.layoutKey);
    const marker = world.createDebugMarker(position, colors[point.id], `Quest:${point.id}`);
    if (point.id === "boundary") addBoundaryStone(marker);
    questMarkers.push(marker);
    // 接任务前锁定三个研学点：玩家需要先找到界碑爷爷。
    const item = interactions.register({
      ...point,
      enabled: quest.state !== "not-started",
      object: marker,
      onInteract: () => startStudyPoint(point, marker),
    });
    studyItems.push(item);
  });
  quest.addEventListener("accepted", () => {
    studyItems.forEach((item) => { item.enabled = true; });
  });
}

async function addBoundaryStone(marker) {
  try {
    const stone = await assets.loadModel("boundaryStone");
    stone.name = "BoundaryStone";
    stone.position.copy(marker.position);
    stone.rotation.y = BOUNDARY_STONE_YAW;
    world.placeOnGround(stone, 0);
    world.heroRoot.add(stone);
    marker.userData.companions = [{ object: stone, offset: new THREE.Vector3() }];
  } catch (error) {
    console.error("界碑模型加载失败，退回图片占位", error);
    const placeholder = addBoundaryPlaceholder(marker.position);
    marker.userData.companions = [{ object: placeholder, offset: new THREE.Vector3(0, 1.05, 0) }];
  }
}

function addBoundaryPlaceholder(position) {
  const texture = new THREE.TextureLoader().load("assets/界碑写实.png");
  texture.colorSpace = THREE.SRGBColorSpace;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({
    map: texture,
    transparent: true,
    alphaTest: 0.04,
    depthWrite: false,
  }));
  sprite.name = "BoundaryStonePlaceholder";
  sprite.position.copy(position).add(new THREE.Vector3(0, 1.05, 0));
  sprite.scale.set(1.15, 2.15, 1);
  world.heroRoot.add(sprite);
  return sprite;
}

function startStudyPoint(point, marker) {
  ui.showToast(`发现研学地点：${point.title}`);
  const target = marker.position.clone().add(new THREE.Vector3(0, 1, 0));
  if (point.id === "gate") {
    cameraController.enterObservation(
      marker.position.clone().add(new THREE.Vector3(3.6, 2.5, 4.2)),
      target,
    );
    ui.showGateObservation(() => quest.addEvidence("gate"));
  } else if (point.id === "boundary") {
    cameraController.enterObservation(
      marker.position.clone().add(new THREE.Vector3(1.5, 1.35, 2.1)),
      target,
    );
    ui.showBoundaryObservation(() => quest.addEvidence("boundary"));
  } else {
    cameraController.enterObservation(
      marker.position.clone().add(new THREE.Vector3(0.8, 5.8, 7.5)),
      target.clone().add(new THREE.Vector3(0, 0.7, 0)),
    );
    ui.showTerrainQuestion(() => quest.addEvidence("terrain"));
  }
}

function bindUI() {
  ui.onModalChange = (open) => {
    player.enabled = !open;
    interactions.enabled = !open;
    if (!open) cameraController.exitObservation();
  };
  const help = document.querySelector("#help-card");
  const closeHelp = () => {
    help.hidden = true;
    ui.onModalChange(false);
  };
  document.querySelector("#help-button").onclick = () => {
    help.hidden = false;
    ui.onModalChange(true);
  };
  help.querySelectorAll("[data-close-help]").forEach((button) => { button.onclick = closeHelp; });

  document.querySelector(".handbook-button").onclick = () => ui.showHandbook(quest);
  window.__touchInteract = () => interactions.interact();
  window.addEventListener("keydown", (event) => {
    if (event.code === "KeyE" && !event.repeat) interactions.interact();
    if (event.code === "Escape") {
      ui.closeOverlay();
      closeHelp();
    }
  });
}

async function start() {
  bindUI();
  resize();
  window.addEventListener("resize", resize);
  try {
    const layout = await layoutManager.load();
    await world.loadFriendshipPass((text, progress) => ui.setLoading(text, progress));
    player.spawn(layout.points.spawn);
    let grandpa = null;
    if (SCENE === "pass") {
      grandpa = await npc.createGrandpa(layout.points.grandpa);
      grandpaChat.attachModel(grandpa);
      addStudyPoints();
    } else {
      document.querySelector("#quest-panel").style.display = "none";
      const introCopy = document.querySelector("#intro-panel p");
      if (introCopy) introCopy.textContent = "这里是祖国的边境哨所。巡逻开始：找到哨所里的 6 处巡逻点，读懂哨兵的一天。";
      const introH1 = document.querySelector("#intro-panel h1");
      if (introH1) introH1.textContent = "哨所的一天";
      const introQuote = document.querySelector("#intro-panel blockquote");
      if (introQuote) introQuote.textContent = "“哨兵是怎样守卫祖国南大门的？”";
    }
    const discoveryList = SCENE === "post" ? POST_DISCOVERIES : FRIENDSHIP_PASS_DISCOVERIES;
    const discoveryLayouts = new Map(layout.discoveries.map((item) => [item.id, item.position]));
    discoveries.addAll(discoveryList.map((definition) => ({
      ...definition,
      position: discoveryLayouts.get(definition.id),
    })).filter((definition) => definition.position));
    const debugTargets = { spawn: layoutManager.vector("spawn") };
    if (SCENE === "pass") {
      debugTargets.grandpa = grandpa.position;
      debugTargets.gate = questMarkers[0].position;
      debugTargets.boundary = questMarkers[1].position;
      debugTargets.terrain = questMarkers[2].position;
    }
    const debug = new DebugManager({
      world,
      player,
      ui,
      questMarkers,
      discoveryManager: discoveries,
      teleportTargets: debugTargets,
      layoutManager,
      targetObjects: SCENE === "pass" ? {
        grandpa: { object: grandpa, clearance: 0 },
        gate: { object: questMarkers[0], clearance: 0.22 },
        boundary: { object: questMarkers[1], clearance: 0.22 },
        terrain: { object: questMarkers[2], clearance: 0.22 },
      } : {},
    });
    if (SCENE === "pass") {
      const markerColors = { gate: "#b54f42", boundary: "#d5ad55", terrain: "#4d8061" };
      STUDY_POINTS.forEach((pt) => {
        const p3 = layoutManager.vector(pt.layoutKey);
        minimapPoints.push({ x: p3.x, z: p3.z, color: markerColors[pt.id] });
      });
      minimapPoints.push({ x: layout.points.grandpa.x, z: layout.points.grandpa.z, color: "#6a4fb0" });
    } else {
      POST_DISCOVERIES.forEach((d) => {
        const p3 = discoveryLayouts.get(d.id);
        if (p3) minimapPoints.push({ x: p3.x, z: p3.z, color: "#e0a53f" });
      });
    }
    if (SCENE === "post") {
      const backMarker = world.createDebugMarker(layoutManager.vector("back"), 0x6fae5f, "Back:sign");
      interactions.register({
        id: "back",
        radius: 2.4,
        actionLabel: "返回友谊关",
        object: backMarker,
        onInteract: () => { location.href = "world.html"; },
      });
    }
    world.dayBackground = scene.background;
    if (SCENE === "post") {
      world.lampLights = [];
      for (const [lx, lz] of [[-5, 8], [5, 8], [-5, 1], [5, 4.5], [-4.5, 3.5]]) {
        const light = new THREE.PointLight(0xffc873, 0, 10, 2);
        light.position.set(lx, 2.5, lz);
        scene.add(light);
        world.lampLights.push(light);
      }
      const doorLight = new THREE.PointLight(0xffd9a0, 0, 7, 2);
      doorLight.position.set(0, 1.7, 4.6);
      scene.add(doorLight);
      world.lampLights.push(doorLight);
    }
    ui.setLoading("正在唤醒研学小伙伴…", 0.94);
    await player.formalModelPromise;
    // 非调试页不暴露自动化句柄
    if (!new URLSearchParams(location.search).has("debug")) {
      delete window.__player;
      delete window.__camera;
    }
    ui.hideLoading();
    ui.showIntro(() => {
      player.enabled = true;
      ui.showToast(SCENE === "post" ? "巡逻开始：找到 6 处巡逻点，读懂哨兵的一天。" : "先找到界碑爷爷，听听他的研学邀请。");
    });
    const sceneButton = document.querySelector("#scene-button");
    sceneButton.textContent = SCENE === "post" ? "返回友谊关" : "前往边境哨所";
    sceneButton.onclick = () => { location.href = SCENE === "post" ? "world.html" : "world.html?scene=post"; };
    const nightButton = document.querySelector("#night-button");
    if (SCENE === "post") {
      nightButton.hidden = false;
      nightButton.onclick = () => {
        world.night = !world.night;
        nightButton.textContent = world.night ? "白天模式" : "夜巡模式";
        if (world.night) {
          scene.background = new THREE.Color(0x0b1226);
          scene.fog.color.set(0x0e1830);
          scene.fog.near = 12;
          scene.fog.far = 70;
          hemisphere.intensity = 0.32;
          sun.intensity = 0.22;
          sun.color.set(0x9db8ff);
          renderer.toneMappingExposure = 1.3;
          (world.lampLights || []).forEach((l) => { l.intensity = 24; });
        } else {
          scene.background = world.dayBackground;
          scene.fog.color.set(0xdcecd9);
          scene.fog.near = 38;
          scene.fog.far = 130;
          hemisphere.intensity = 1.4;
          sun.intensity = 2.6;
          sun.color.set(0xfff2d4);
          renderer.toneMappingExposure = 1.0;
          (world.lampLights || []).forEach((l) => { l.intensity = 0; });
        }
      };
    }
    const mapButton = document.querySelector(".map-button");
    const mapPanel = document.querySelector("#minimap-panel");
    mapButton.onclick = () => { mapPanel.hidden = !mapPanel.hidden; drawMinimap(); };
    const mapImage = new Image();
    mapImage.src = MAP_BOUNDS.img;
    window.drawMinimap = drawMinimap;
    function drawMinimap() {
      if (mapPanel.hidden) return;
      const canvas2 = document.querySelector("#minimap-canvas");
      const ctx = canvas2.getContext("2d");
      ctx.clearRect(0, 0, 280, 280);
      if (mapImage.complete && mapImage.naturalWidth) ctx.drawImage(mapImage, 0, 0, 280, 280);
      else { ctx.fillStyle = "#dfe8d8"; ctx.fillRect(0, 0, 280, 280); }
      const toPx = (x, z) => [
        (x - MAP_BOUNDS.x0) / (MAP_BOUNDS.x1 - MAP_BOUNDS.x0) * 280,
        (z - MAP_BOUNDS.z0) / (MAP_BOUNDS.z1 - MAP_BOUNDS.z0) * 280,
      ];
      for (const pt of minimapPoints) {
        const [px, py] = toPx(pt.x, pt.z);
        ctx.fillStyle = pt.color;
        ctx.beginPath();
        ctx.arc(px, py, 5.5, 0, 7);
        ctx.fill();
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 1.6;
        ctx.stroke();
      }
      const pp = player.group.position;
      const [px, py] = toPx(pp.x, pp.z);
      ctx.fillStyle = "#2b6cb0";
      ctx.beginPath();
      ctx.arc(px, py, 6.5, 0, 7);
      ctx.fill();
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 2;
      ctx.stroke();
    }
    mapImage.onload = () => drawMinimap();

    // Study Debug 模式下暴露场景句柄，供自动化测试读取交互项状态。
    if (new URLSearchParams(location.search).has("debug")) {
      window.__study = {
        player,
        interactions,
        npc,
        quest,
        cameraController,
        items: () => interactions.items.map((item) => {
          const raw = item.object?.position ?? item.position;
          const position = raw.toJSON ? raw.toJSON() : { x: raw.x, y: raw.y, z: raw.z };
          return { id: item.id, enabled: item.enabled !== false, position, label: item.actionLabel };
        }),
        current: () => interactions.current?.id || null,
        // 手动推帧：浏览器面板隐藏时 rAF 暂停，测试用 step 驱动游戏逻辑。
        step: (times = 1, dt = 0.016) => {
          for (let index = 0; index < times; index += 1) tick(dt);
        },
      };
    }

    const tick = (dt) => {
      player.update(dt);
      cameraController.update(dt, player.group.position);
      world.updateFlags(performance.now() / 1000);
      if (typeof window.drawMinimap === "function" && !document.querySelector("#minimap-panel").hidden) window.drawMinimap();
      interactions.update();
      debug.update(dt);
      renderer.render(scene, camera);
    };
    let previous = performance.now();
    renderer.setAnimationLoop((now) => {
      const dt = Math.min((now - previous) / 1000, 0.05);
      previous = now;
      tick(dt);
    });
  } catch (error) {
    console.error("友谊关世界加载失败", error);
    ui.setLoading("世界加载失败，请检查网络与资产文件。", 0);
  }
}

start();
