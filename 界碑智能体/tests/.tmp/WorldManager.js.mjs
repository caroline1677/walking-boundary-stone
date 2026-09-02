import * as THREE from "three";
import { SparkRenderer, SplatMesh } from "@sparkjsdev/spark";
import { acceleratedRaycast, computeBoundsTree, disposeBoundsTree } from "three-mesh-bvh";
import { ASSETS, WORLD_STYLE, WORLD_SCENE } from "./AssetManager.js?v=20260830-toon1";

THREE.BufferGeometry.prototype.computeBoundsTree = computeBoundsTree;
THREE.BufferGeometry.prototype.disposeBoundsTree = disposeBoundsTree;
THREE.Mesh.prototype.raycast = acceleratedRaycast;

const DOWN = new THREE.Vector3(0, -1, 0);

export class WorldManager {
  constructor({ scene, renderer, assets }) {
    this.scene = scene;
    this.renderer = renderer;
    this.assets = assets;
    this.root = new THREE.Group();
    this.root.name = "FriendshipPassScene";
    this.visualRoot = new THREE.Group();
    this.visualRoot.name = "WorldVisual";
    this.colliderRoot = new THREE.Group();
    this.colliderRoot.name = "WorldCollider";
    this.heroRoot = new THREE.Group();
    this.heroRoot.name = "HeroAssets";
    this.triggerRoot = new THREE.Group();
    this.triggerRoot.name = "QuestTriggers";
    this.root.add(this.visualRoot, this.colliderRoot, this.heroRoot, this.triggerRoot);
    this.scene.add(this.root);
    this.colliderMeshes = [];
    this.bounds = new THREE.Box3();
    this.raycaster = new THREE.Raycaster();
    this.raycaster.firstHitOnly = true;
    if (WORLD_STYLE === "splat") {
      this.spark = new SparkRenderer({ renderer });
      this.scene.add(this.spark);
    }
  }

  async loadFriendshipPass(onProgress = () => {}) {
    if (WORLD_STYLE === "toon") return this.loadToonWorld(onProgress);
    return this.loadSplatWorld(onProgress);
  }

  applyToonMaterial(root) {
    root.traverse((object) => {
      if (!object.isMesh) return;
      object.material = new THREE.MeshStandardMaterial({
        vertexColors: true,
        roughness: 0.95,
        metalness: 0,
      });
      object.castShadow = true;
      object.receiveShadow = true;
    });
  }

  async loadToonWorld(onProgress = () => {}) {
    const post = WORLD_SCENE === "post";
    const keys = post
      ? { terrain: "postTerrain", props: "postProps", gate: "postBuildings", flags: "postFlags" }
      : { terrain: "toonTerrain", props: "toonProps", gate: "toonGate", flags: "flags" };
    onProgress(post ? "正在前往边境哨所…" : "正在铺开友谊关的山谷…", 0.12);
    const terrain = await this.assets.loadModel(keys.terrain);
    terrain.name = "ToonTerrain";
    this.applyToonMaterial(terrain);
    terrain.traverse((object) => { object.castShadow = false; });
    this.visualRoot.add(terrain);

    onProgress("正在种下山林草木…", 0.38);
    const props = await this.assets.loadModel(keys.props);
    props.name = "ToonProps";
    this.applyToonMaterial(props);
    this.visualRoot.add(props);

    onProgress("正在立起关楼城台…", 0.62);
    const gate = await this.assets.loadModel(keys.gate);
    gate.name = "ToonGate";
    this.applyToonMaterial(gate);
    this.visualRoot.add(gate);

    onProgress("正在挂上红旗…", 0.74);
    this.flagCloths = [];
    try {
      const flags = await this.assets.loadModel(keys.flags);
      flags.traverse((object) => {
        if (!object.isMesh) return;
        if (object.name.startsWith("FlagCloth")) {
          object.material = new THREE.MeshStandardMaterial({
            vertexColors: true,
            roughness: 0.9,
            metalness: 0,
            side: THREE.DoubleSide,
          });
          object.castShadow = true;
          object.updateMatrixWorld(true);
          let maxZ = -Infinity;
          const arr = object.geometry.attributes.position.array;
          for (let i = 2; i < arr.length; i += 3) maxZ = Math.max(maxZ, arr[i]);
          this.flagCloths.push({
            mesh: object,
            base: arr.slice(),
            maxZ,
          });
        } else {
          this.applyToonMaterial(object);
        }
      });
      this.visualRoot.add(flags);
    } catch (error) {
      console.warn("旗帜加载失败，跳过飘旗动画", error);
    }

    onProgress("正在建立可行走碰撞层…", 0.82);
    const collider = await this.assets.loadModel(post ? "postCollider" : "worldCollider");
    collider.name = "FriendshipPassCollider";
    this.colliderRoot.add(collider);
    collider.updateMatrixWorld(true);
    collider.traverse((object) => {
      if (!object.isMesh) return;
      object.geometry.computeBoundsTree({ targetLeafSize: 20 });
      object.material = new THREE.MeshBasicMaterial({
        color: 0x52b788,
        wireframe: true,
        transparent: true,
        opacity: 0.18,
        depthWrite: false,
      });
      object.visible = false;
      this.colliderMeshes.push(object);
      this.bounds.expandByObject(object);
    });

    // 天空渐变 + 雾 + 暖阳光
    const sky = document.createElement("canvas");
    sky.width = 2;
    sky.height = 256;
    const ctx = sky.getContext("2d");
    const gradient = ctx.createLinearGradient(0, 0, 0, 256);
    gradient.addColorStop(0, "#6db7e8");
    gradient.addColorStop(0.55, "#aadcf2");
    gradient.addColorStop(0.8, "#e8f5ef");
    gradient.addColorStop(1, "#dcecd9");
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 2, 256);
    const skyTexture = new THREE.CanvasTexture(sky);
    skyTexture.colorSpace = THREE.SRGBColorSpace;
    this.scene.background = skyTexture;
    this.scene.fog = new THREE.Fog(0xdcecd9, 38, 130);

    const sun = this.scene.userData.sun;
    if (sun) {
      sun.intensity = 2.6;
      sun.castShadow = true;
      sun.shadow.mapSize.set(2048, 2048);
      sun.shadow.camera.left = -24;
      sun.shadow.camera.right = 24;
      sun.shadow.camera.top = 24;
      sun.shadow.camera.bottom = -24;
      sun.shadow.camera.near = 1;
      sun.shadow.camera.far = 90;
      sun.shadow.bias = -0.0006;
      sun.position.set(-18, 22, 26);
    }
    const hemi = this.scene.userData.hemisphere;
    if (hemi) {
      hemi.intensity = 1.4;
      hemi.color.set(0xdff1ff);
      hemi.groundColor.set(0x8f9779);
    }
    this.renderer.toneMappingExposure = 1.0;

    onProgress("研学世界已就绪", 1);
    return { terrain, props, gate, collider, bounds: this.bounds.clone() };
  }

  async loadSplatWorld(onProgress = () => {}) {
    onProgress("正在加载友谊关实景世界…", 0.08);
    const splat = new SplatMesh({
      url: ASSETS.worldVisual,
      onProgress: (event) => {
        if (event.lengthComputable) onProgress("正在加载友谊关实景世界…", 0.08 + (event.loaded / event.total) * 0.3);
      },
    });
    splat.name = "HunyuanFriendshipPass";
    // Hunyuan/Open3D exports use Z-up. Blender's glTF exporter converts the
    // collider to Y-up, so apply the equivalent -90° X rotation to the SPZ.
    splat.rotation.x = -Math.PI / 2;
    this.visualRoot.add(splat);
    await splat.initialized;

    onProgress("正在建立可行走碰撞层…", 0.42);
    const collider = await this.assets.loadModel("worldCollider");
    collider.name = "FriendshipPassCollider";
    this.colliderRoot.add(collider);
    collider.updateMatrixWorld(true);
    collider.traverse((object) => {
      if (!object.isMesh) return;
      object.geometry.computeBoundsTree({ targetLeafSize: 20 });
      object.material = new THREE.MeshBasicMaterial({
        color: 0x52b788,
        wireframe: true,
        transparent: true,
        opacity: 0.18,
        depthWrite: false,
      });
      object.visible = false;
      this.colliderMeshes.push(object);
      this.bounds.expandByObject(object);
    });
    onProgress("真实世界已就绪", 1);
    return { splat, collider, bounds: this.bounds.clone() };
  }

  updateFlags(time) {
    if (!this.flagCloths) return;
    for (const cloth of this.flagCloths) {
      const attr = cloth.mesh.geometry.attributes.position;
      const base = cloth.base;
      for (let i = 0; i < attr.count; i += 1) {
        const bx = base[i * 3];
        const stream = Math.min(1, (cloth.maxZ - base[i * 3 + 2]) / 1.15);
        attr.array[i * 3] = bx + Math.sin(stream * 4.2 - time * 6.5) * 0.10 * stream;
        attr.array[i * 3 + 1] = base[i * 3 + 1] - stream * stream * 0.08 + Math.sin(stream * 3.1 - time * 5.2) * 0.035 * stream;
        attr.array[i * 3 + 2] = base[i * 3 + 2];
      }
      attr.needsUpdate = true;
    }
    for (const cloth of this.flagCloths) cloth.mesh.geometry.computeVertexNormals();
  }

  setColliderVisible(visible) {
    this.colliderMeshes.forEach((mesh) => { mesh.visible = visible; });
  }

  groundAt(position, rayHeight = 18) {
    if (!this.colliderMeshes.length) return null;
    const origin = new THREE.Vector3(position.x, Math.max(position.y + rayHeight, this.bounds.max.y + 2), position.z);
    this.raycaster.set(origin, DOWN);
    this.raycaster.near = 0;
    this.raycaster.far = Math.max(50, this.bounds.getSize(new THREE.Vector3()).y + 10);
    const hits = this.raycaster.intersectObjects(this.colliderMeshes, false);
    if (!hits.length) return null;
    return hits[0];
  }

  placeOnGround(object, clearance = 0) {
    const hit = this.groundAt(object.position);
    if (hit) object.position.y = hit.point.y + clearance;
    return hit;
  }

  movePlayer(previous, proposed, radius = 0.32) {
    if (!this.bounds.containsPoint(new THREE.Vector3(proposed.x, this.bounds.getCenter(new THREE.Vector3()).y, proposed.z))) {
      return previous.clone();
    }
    const hit = this.groundAt(proposed);
    if (!hit) return previous.clone();
    const step = hit.point.y - previous.y;
    if (step > 0.65 || step < -1.1) return previous.clone();

    const horizontal = proposed.clone().sub(previous);
    horizontal.y = 0;
    const distance = horizontal.length();
    if (distance > 0.001) {
      this.raycaster.set(previous.clone().add(new THREE.Vector3(0, 0.75, 0)), horizontal.normalize());
      this.raycaster.near = 0.05;
      this.raycaster.far = distance + radius;
      const obstacle = this.raycaster.intersectObjects(this.colliderMeshes, false)[0];
      if (obstacle && obstacle.distance < distance + radius) return previous.clone();
    }
    proposed.y = THREE.MathUtils.lerp(previous.y, hit.point.y, 0.42);
    return proposed;
  }

  createDebugMarker(position, color, label) {
    const marker = new THREE.Mesh(
      new THREE.SphereGeometry(0.22, 16, 10),
      new THREE.MeshBasicMaterial({ color, depthTest: false }),
    );
    marker.name = label;
    marker.position.set(position.x, position.y, position.z);
    marker.renderOrder = 10;
    this.placeOnGround(marker, 0.22);
    this.triggerRoot.add(marker);
    return marker;
  }
}
