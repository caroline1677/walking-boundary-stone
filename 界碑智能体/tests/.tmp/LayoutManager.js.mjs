import * as THREE from "three";

const STORAGE_KEY = "friendship-pass-layout-draft";

export class LayoutManager {
  constructor(url = "data/friendship-pass-layout.json") {
    this.url = url;
    this.data = null;
  }

  async load() {
    const response = await fetch(this.url, { cache: "no-store" });
    if (!response.ok) throw new Error(`Layout 加载失败：${response.status}`);
    const fileLayout = await response.json();
    try {
      const draft = JSON.parse(localStorage.getItem(STORAGE_KEY));
      this.data = draft?.version >= fileLayout.version ? draft : fileLayout;
    } catch {
      this.data = fileLayout;
    }
    return this.data;
  }

  vector(id) {
    const value = this.data.points[id];
    return new THREE.Vector3(value.x, value.y, value.z);
  }

  async setPoint(id, position) {
    this.data.points[id] = this.serialize(position);
    await this.persist();
  }

  async addDiscovery(position) {
    const id = `custom-${Date.now()}`;
    const item = { id, position: this.serialize(position) };
    this.data.discoveries.push(item);
    await this.persist();
    return item;
  }

  serialize(position) {
    return {
      x: Number(position.x.toFixed(2)),
      y: Number(position.y.toFixed(2)),
      z: Number(position.z.toFixed(2)),
    };
  }

  async persist() {
    this.data.updatedAt = new Date().toISOString();
    localStorage.setItem(STORAGE_KEY, JSON.stringify(this.data));
    try {
      const response = await fetch("/api/layout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(this.data),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return true;
    } catch (error) {
      console.info("Layout 已保存在浏览器草稿；重启新版 server.py 后会同步到 JSON。", error.message);
      return false;
    }
  }
}
