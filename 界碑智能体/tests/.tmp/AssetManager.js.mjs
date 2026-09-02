import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

export const ASSETS = {
  worldVisual: "assets/worlds/friendship-pass.spz",
  worldCollider: "assets/worlds/pass-v2-collider.glb?v=v2b",
  toonTerrain: "assets/worlds/pass-v2-terrain.glb?v=v2a",
  toonProps: "assets/worlds/pass-v2-props.glb?v=v2b",
  toonGate: "assets/models/pass-v2-gate.glb?v=v2a",
  flags: "assets/models/pass-v2-flags.glb?v=v2a",
  postTerrain: "assets/worlds/post-terrain.glb?v=p2",
  postProps: "assets/worlds/post-props.glb?v=p2",
  postBuildings: "assets/models/post-buildings.glb?v=p2",
  postFlags: "assets/models/post-flags.glb?v=p2",
  postCollider: "assets/worlds/post-collider.glb?v=p2",
  player: "assets/models/student-girl-v2.glb?v=s2",
  friendshipGate: "assets/models/friendship-gate.glb",
  boundaryStone: "assets/models/boundary-stone.glb",
  grandpa: "assets/models/grandpa-v2.glb?v=g2",
};

// "toon"：低模绘本风（默认）·"splat"：真实点云扫描（回退）
export const WORLD_STYLE = "toon";
// "pass"：友谊关关楼场景（默认）·"post"：边境哨所场景（研学下一站）
export const WORLD_SCENE = new URLSearchParams(location.search).get("scene") === "post" ? "post" : "pass";

export class AssetManager {
  constructor() {
    this.gltfLoader = new GLTFLoader();
    this.cache = new Map();
  }

  async loadModel(key, { optional = false } = {}) {
    if (this.cache.has(key)) return this.cache.get(key).clone(true);
    try {
      const gltf = await this.gltfLoader.loadAsync(ASSETS[key]);
      this.cache.set(key, gltf.scene);
      return gltf.scene.clone(true);
    } catch (error) {
      if (!optional) throw error;
      return null;
    }
  }
}

export function makeMaterial(color, options = {}) {
  return new THREE.MeshStandardMaterial({ color, roughness: 0.82, ...options });
}
