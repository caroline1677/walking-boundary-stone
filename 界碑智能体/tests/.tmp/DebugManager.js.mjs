import * as THREE from "three";

export class DebugManager {
  constructor({ world, player, ui, questMarkers, discoveryManager, teleportTargets, layoutManager, targetObjects }) {
    this.world = world;
    this.player = player;
    this.ui = ui;
    this.questMarkers = questMarkers;
    this.discoveryManager = discoveryManager;
    this.teleportTargets = teleportTargets;
    this.layoutManager = layoutManager;
    this.targetObjects = targetObjects;
    this.enabled = new URLSearchParams(location.search).has("debug");
    this.frames = 0;
    this.elapsed = 0;
    this.fps = 0;
    this.saved = [];
    this.ui.setupDebug({
      enabled: this.enabled,
      onToggleCollider: (visible) => this.world.setColliderVisible(visible),
      onTogglePoints: (visible) => this.setPointsVisible(visible),
      onRecord: () => this.record(),
      onTeleport: (id) => this.teleport(id),
      onSetPoint: (id) => this.setCurrentAs(id),
      onAddDiscovery: () => this.addDiscovery(),
    });
    this.setPointsVisible(this.enabled);
  }

  teleport(id) {
    const target = this.teleportTargets[id];
    if (!target) return;
    this.player.group.position.copy(target);
    this.world.placeOnGround(this.player.group, 0.02);
  }

  async setCurrentAs(id) {
    const position = this.player.group.position.clone();
    await this.layoutManager.setPoint(id, position);
    this.teleportTargets[id] = position.clone();
    const target = this.targetObjects[id];
    if (target) {
      target.object.position.copy(position);
      this.world.placeOnGround(target.object, target.clearance || 0);
      for (const companion of target.object.userData.companions || []) {
        companion.object.position.copy(target.object.position).add(companion.offset);
      }
    }
    this.ui.showToast(`已把当前位置保存为：${id}`);
  }

  async addDiscovery() {
    const saved = await this.layoutManager.addDiscovery(this.player.group.position);
    const definition = {
      id: saved.id,
      title: "新发现点",
      text: "这是通过 Study Debug Mode 记录的自由发现位置，可在配置中补充正式内容。",
      radius: 2,
      position: saved.position,
    };
    const marker = this.discoveryManager.addOne(definition);
    marker.visible = true;
    this.ui.showToast("已新增自由发现点并保存布局");
  }

  setPointsVisible(visible) {
    this.questMarkers.forEach((marker) => { marker.visible = visible; });
    this.discoveryManager.setDebugVisible(visible);
  }

  record() {
    const p = this.player.group.position;
    const value = `{ x: ${p.x.toFixed(2)}, y: ${p.y.toFixed(2)}, z: ${p.z.toFixed(2)} }`;
    this.saved.push(value);
    this.ui.setDebugRecord(value);
    console.info("[FriendshipPass coordinate]", value);
  }

  update(dt) {
    if (!this.enabled) return;
    this.frames += 1;
    this.elapsed += dt;
    if (this.elapsed >= 0.5) {
      this.fps = Math.round(this.frames / this.elapsed);
      this.frames = 0;
      this.elapsed = 0;
    }
    const p = this.player.group.position;
    this.ui.updateDebug({ x: p.x, y: p.y, z: p.z, fps: this.fps });
  }
}
