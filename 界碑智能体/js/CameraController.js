import * as THREE from "three";

export class CameraController {
  constructor(camera, canvas, world) {
    this.camera = camera;
    this.canvas = canvas;
    this.world = world;
    // 出生点在广场南端，正对中轴线尽头的关楼（gate 在 -Z 方向）
    this.yaw = 0.0;
    this.pitch = 0.30;
    this.distance = 6.4;
    this.target = new THREE.Vector3();
    this.dragging = false;
    this.lastPointer = { x: 0, y: 0 };
    this.observation = null;
    this.bindEvents();
    window.__camera = this;
  }

  bindEvents() {
    this.canvas.addEventListener("pointerdown", (event) => {
      this.dragging = true;
      this.lastPointer = { x: event.clientX, y: event.clientY };
      this.canvas.setPointerCapture(event.pointerId);
    });
    this.canvas.addEventListener("pointermove", (event) => {
      if (!this.dragging) return;
      this.yaw -= (event.clientX - this.lastPointer.x) * 0.006;
      this.pitch = THREE.MathUtils.clamp(this.pitch + (event.clientY - this.lastPointer.y) * 0.004, 0.12, 1.05);
      this.lastPointer = { x: event.clientX, y: event.clientY };
    });
    const end = () => { this.dragging = false; };
    this.canvas.addEventListener("pointerup", end);
    this.canvas.addEventListener("pointercancel", end);
    this.canvas.addEventListener("wheel", (event) => {
      event.preventDefault();
      this.distance = THREE.MathUtils.clamp(this.distance + event.deltaY * 0.004, 3.5, 8.5);
    }, { passive: false });
  }

  forward() {
    return new THREE.Vector3(-Math.sin(this.yaw), 0, -Math.cos(this.yaw));
  }

  right() {
    return new THREE.Vector3(Math.cos(this.yaw), 0, -Math.sin(this.yaw));
  }

  enterObservation(position, target, distance = 4.2) {
    this.observation = {
      position: new THREE.Vector3(position.x, position.y, position.z),
      target: new THREE.Vector3(target.x, target.y, target.z),
      distance,
    };
  }

  exitObservation() {
    this.observation = null;
  }

  update(dt, playerPosition) {
    if (this.observation) {
      this.camera.position.lerp(this.observation.position, 1 - Math.pow(0.002, dt));
      this.target.lerp(this.observation.target, 1 - Math.pow(0.002, dt));
      this.camera.lookAt(this.target);
      return;
    }
    const focus = playerPosition.clone().add(new THREE.Vector3(0, 1.15, 0));
    const horizontal = Math.cos(this.pitch) * this.distance;
    const offset = new THREE.Vector3(
      Math.sin(this.yaw) * horizontal,
      Math.sin(this.pitch) * this.distance + 0.8,
      Math.cos(this.yaw) * this.distance,
    );
    const desired = focus.clone().add(offset);
    // 若焦点与理想机位之间被地形挡住，把机位拉到障碍物前，避免镜头埋进山坡。
    const toCamera = desired.clone().sub(focus);
    const wanted = toCamera.length();
    if (wanted > 0.01 && this.world.colliderMeshes.length) {
      this.world.raycaster.set(focus, toCamera.normalize());
      this.world.raycaster.near = 0.1;
      this.world.raycaster.far = wanted;
      const blocker = this.world.raycaster.intersectObjects(this.world.colliderMeshes, false)[0];
      if (blocker) {
        const clear = Math.max(2.6, blocker.distance - 0.35);
        desired.copy(focus).addScaledVector(toCamera, clear);
        // 机位抬到遮挡坡顶之上，避免镜头贴地埋进植被。
        desired.y = Math.max(desired.y, blocker.point.y + 0.9);
      }
    }
    const cameraGround = this.world.groundAt(desired);
    if (cameraGround) desired.y = Math.max(desired.y, cameraGround.point.y + 0.65);
    this.camera.position.lerp(desired, 1 - Math.pow(0.004, dt));
    this.target.lerp(focus, 1 - Math.pow(0.002, dt));
    this.camera.lookAt(this.target);
  }
}
