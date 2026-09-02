import * as THREE from "three";
import { makeMaterial } from "./AssetManager.js?v=20260830-toon1";

export class NPCManager {
  constructor({ world, assets, interactions, quest, ui, chat }) {
    this.world = world;
    this.assets = assets;
    this.interactions = interactions;
    this.quest = quest;
    this.ui = ui;
    this.chat = chat || null;
    this.group = new THREE.Group();
    this.group.name = "NPC";
    this.world.heroRoot.add(this.group);
  }

  async createGrandpa(position) {
    let model = await this.assets.loadModel("grandpa", { optional: true });
    if (!model) model = this.placeholder();
    model.name = "GrandpaBoundary";
    model.position.set(position.x, position.y, position.z);
    if (Number.isFinite(position.rotationY)) model.rotation.y = position.rotationY;
    this.world.placeOnGround(model);
    this.group.add(model);
    this.interactions.register({
      id: "grandpa",
      object: model,
      radius: 2.2,
      actionLabel: "和界碑爷爷聊聊",
      onInteract: () => this.talk(),
    });
    return model;
  }

  async grandpaComment(keywords, freeText = "") {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 25000);
    try {
      const own = freeText ? `他自己的结论是：“${freeText}”，关键词是：${keywords.join("、")}。` : `他总结的关键词是：${keywords.join("、")}。`;
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: `一个小朋友刚完成友谊关研学探索。${own}请以守着界碑多年的爷爷的口吻，用不超过50字给他的结论做一句亲切、鼓励式的点评，像爷爷对孙辈说话，不要出现引号和序号。`,
          era: "当代",
        }),
        signal: controller.signal,
      });
      const data = await response.json();
      return data && data.ok ? String(data.answer || "").trim() : "";
    } catch {
      return "";
    } finally {
      clearTimeout(timer);
    }
  }

  placeholder() {
    const group = new THREE.Group();
    const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.28, 0.64, 4, 10), makeMaterial(0x718879));
    body.position.y = 0.75;
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.22, 16, 12), makeMaterial(0xd8aa83));
    head.position.y = 1.35;
    const hat = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.36, 0.12, 16), makeMaterial(0x4f6257));
    hat.position.y = 1.58;
    group.add(body, head, hat);
    return group;
  }

  chatAction() {
    return this.chat ? { label: "🎤 和爷爷说话", onClick: () => this.chat.show() } : null;
  }

  talk() {
    if (this.quest.state === "return-to-npc") {
      this.ui.showSummaryDialog(async (keywords, freeText) => {
        const base = freeText || `友谊关建在${keywords.join("、")}相互联系的重要位置。`;
        this.ui.showToast("界碑爷爷正在琢磨你的结论…");
        const comment = await this.grandpaComment(keywords, freeText);
        this.quest.complete(base);
        this.ui.showStudyCard(this.quest, base, comment);
        window.submitStudentAnswer({ answer: base, keywords, grandpaComment: comment });
      });
      return;
    }
    if (this.quest.state === "complete") {
      this.ui.showStudyCard(this.quest, this.quest.studentAnswer);
      return;
    }
    if (this.quest.state === "active") {
      const missing = this.quest.quest.evidences.filter((item) => !this.quest.evidence.has(item.id));
      const hints = {
        gate: "沿着道路走到山谷最窄的地方，那里有一座高大的关楼，看看门洞、城墙和高处的楼。",
        terrain: "回到路口高一点的地方，看看道路是怎么从两座大山之间穿过去的。",
        boundary: "过了关楼往东走走，在安静的角落找一块刻着国家、编号和年份的石碑。",
      };
      this.ui.showDialog({
        eyebrow: "界碑爷爷 · 研学提示",
        title: `还差 ${missing.length} 个证据`,
        body: "我不会直接告诉你答案，但可以给你一个探索方向。",
        actions: [
          { label: "给我一个提示", primary: true, onClick: () => this.ui.showToast(hints[missing[0]?.id] || "把三个证据放在一起想一想。") },
          this.chatAction(),
          { label: "我继续找找", onClick: () => {} },
        ],
      });
      return;
    }
    this.ui.showDialog({
      eyebrow: "界碑爷爷",
      title: "为什么这里会建一座关？",
      body: "今天我先不告诉你答案。去友谊关里找三个线索，回来告诉我为什么这座关会建在这里。",
      actions: [
        { label: "接受任务", primary: true, onClick: () => this.quest.accept() },
        this.chatAction(),
        { label: "给我一点提示", onClick: () => this.ui.showToast("提示：看看关楼、界碑，以及道路两边的山。") },
        { label: "我先自己逛逛", onClick: () => {} },
      ],
    });
  }
}
