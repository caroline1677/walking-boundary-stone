import { FRIENDSHIP_PASS_QUEST } from "../data/friendship-pass-quests.js?v=20260830-quest1";

export class QuestManager extends EventTarget {
  constructor(ui, scene = "pass") {
    super();
    this.ui = ui;
    this.storageKey = scene === "post" ? "post-patrol-progress" : "friendship-pass-progress";
    this.quest = FRIENDSHIP_PASS_QUEST;
    this.state = "not-started";
    this.evidence = new Set();
    this.fragments = new Set();
    this.studentAnswer = "";
    this.startedAt = null;
    this.completedAt = null;
    this.restore();
    this.ui.renderQuest(this);
  }

  accept() {
    if (this.state !== "not-started") return;
    this.state = "active";
    this.startedAt = new Date().toISOString();
    this.save();
    this.ui.renderQuest(this);
    this.dispatchEvent(new CustomEvent("accepted"));
    this.ui.showToast("研学任务已开启：寻找三个线索");
  }

  addEvidence(id) {
    if (this.state !== "active") return false;
    if (this.evidence.has(id)) return false;
    this.evidence.add(id);
    if (this.evidence.size === this.quest.evidences.length) this.state = "return-to-npc";
    this.save();
    this.ui.renderQuest(this);
    this.dispatchEvent(new CustomEvent("evidence", { detail: { id, count: this.evidence.size } }));
    return true;
  }

  addFragment(id) {
    if (this.fragments.has(id)) return false;
    this.fragments.add(id);
    this.save();
    return true;
  }

  complete(answer = "") {
    this.state = "complete";
    this.studentAnswer = answer;
    this.completedAt = new Date().toISOString();
    this.save();
    this.ui.renderQuest(this);
  }

  save() {
    sessionStorage.setItem(this.storageKey, JSON.stringify({
      state: this.state,
      evidence: [...this.evidence],
      fragments: [...this.fragments],
      studentAnswer: this.studentAnswer,
      startedAt: this.startedAt,
      completedAt: this.completedAt,
    }));
  }

  restore() {
    try {
      const saved = JSON.parse(sessionStorage.getItem(this.storageKey));
      if (!saved) return;
      this.state = saved.state || "not-started";
      this.evidence = new Set(saved.evidence || []);
      this.fragments = new Set(saved.fragments || []);
      this.studentAnswer = saved.studentAnswer || "";
      this.startedAt = saved.startedAt || null;
      this.completedAt = saved.completedAt || null;
    } catch {
      sessionStorage.removeItem(this.storageKey);
    }
  }
}
