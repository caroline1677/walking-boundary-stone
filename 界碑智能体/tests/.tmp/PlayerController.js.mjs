import * as THREE from "three";
import { makeMaterial } from "./AssetManager.js?v=20260830-toon1";

export class PlayerController {
  constructor({ world, cameraController, assets }) {
    this.world = world;
    this.cameraController = cameraController;
    this.assets = assets;
    this.group = this.createPlaceholder();
    this.group.name = "Player";
    this.keys = new Set();
    this.walkSpeed = 3.1;
    this.runSpeed = 4.4;
    this.enabled = false;
    this.radius = 0.3;
    this.bindEvents();
    this.loadFormalModel();
    window.__player = this;
  }

  bindEvents() {
    window.addEventListener("keydown", (event) => {
      if (["KeyW", "KeyA", "KeyS", "KeyD", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "ShiftLeft", "ShiftRight"].includes(event.code)) {
        event.preventDefault();
        this.keys.add(event.code);
      }
    });
    window.addEventListener("keyup", (event) => this.keys.delete(event.code));
    window.addEventListener("blur", () => this.keys.clear());
  }

  async loadFormalModel() {
    const model = await this.assets.loadModel("player", { optional: true });
    if (!model) return;
    this.group.clear();
    model.scale.setScalar(1.0);
    model.traverse((object) => {
      if (object.isMesh) object.castShadow = true;
    });
    this.group.add(model);
  }

  createPlaceholder() {
    const group = new THREE.Group();
    const shirt = new THREE.Mesh(new THREE.CapsuleGeometry(0.22, 0.48, 4, 8), makeMaterial(0xd89545));
    shirt.position.y = 0.72;
    shirt.castShadow = true;
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.2, 16, 12), makeMaterial(0xf0be92));
    head.position.y = 1.25;
    head.castShadow = true;
    const hair = new THREE.Mesh(new THREE.SphereGeometry(0.21, 16, 8, 0, Math.PI * 2, 0, Math.PI * 0.55), makeMaterial(0x322820));
    hair.position.y = 1.31;
    group.add(shirt, head, hair);
    return group;
  }

  spawn(position) {
    this.group.position.set(position.x, position.y, position.z);
    this.world.placeOnGround(this.group, 0.02);
  }

  update(dt) {
    if (!this.enabled) return;
    const x = (this.keys.has("KeyD") || this.keys.has("ArrowRight") ? 1 : 0) - (this.keys.has("KeyA") || this.keys.has("ArrowLeft") ? 1 : 0);
    const z = (this.keys.has("KeyW") || this.keys.has("ArrowUp") ? 1 : 0) - (this.keys.has("KeyS") || this.keys.has("ArrowDown") ? 1 : 0);
    if (!x && !z) return;
    const direction = this.cameraController.forward().multiplyScalar(z).add(this.cameraController.right().multiplyScalar(x)).normalize();
    const running = this.keys.has("ShiftLeft") || this.keys.has("ShiftRight");
    const proposed = this.group.position.clone().addScaledVector(direction, (running ? this.runSpeed : this.walkSpeed) * dt);
    const resolved = this.world.movePlayer(this.group.position, proposed, this.radius);
    this.group.position.copy(resolved);
    this.group.rotation.y = Math.atan2(direction.x, direction.z);
  }
}
