import { WORLD_SCENE } from "./AssetManager.js?v=20260830-toon1";
import { POST_DISCOVERIES } from "../data/post-discoveries.js?v=p1";
export class UIManager {
  constructor() {
    this.questPanel = document.querySelector("#quest-panel");
    this.tip = document.querySelector("#interaction-tip");
    this.toast = document.querySelector("#toast");
    this.overlay = document.querySelector("#overlay-panel");
    this.intro = document.querySelector("#intro-panel");
    this.loading = document.querySelector("#loading-screen");
    this.loadingText = document.querySelector("#loading-text");
    this.loadingBar = document.querySelector("#loading-bar");
    this.debugPanel = document.querySelector("#debug-panel");
    this.onModalChange = () => {};
  }

  setLoading(text, progress = 0) {
    this.loadingText.textContent = text;
    this.loadingBar.style.width = `${Math.round(progress * 100)}%`;
  }

  hideLoading() {
    this.loading.classList.add("hidden");
  }

  showIntro(onStart) {
    this.intro.hidden = false;
    this.onModalChange(true);
    this.intro.querySelector("[data-start]").onclick = () => {
      this.intro.hidden = true;
      this.onModalChange(false);
      onStart();
    };
  }

  showTip(html) {
    this.tip.innerHTML = html;
    this.tip.hidden = false;
  }

  hideTip() {
    this.tip.hidden = true;
  }

  showToast(text) {
    this.toast.textContent = text;
    this.toast.hidden = false;
    clearTimeout(this.toastTimer);
    this.toastTimer = setTimeout(() => { this.toast.hidden = true; }, 2600);
  }

  renderQuest(manager) {
    const total = manager.quest.evidences.length;
    const count = manager.evidence.size;
    const rows = manager.quest.evidences.map((evidence) => `
      <li class="${manager.evidence.has(evidence.id) ? "done" : ""}">
        <span>${manager.evidence.has(evidence.id) ? "✓" : "○"}</span>${evidence.label}
      </li>`).join("");
    const status = manager.state === "not-started"
      ? "任务未开启：先找到界碑爷爷，按 E 和他聊聊。"
      : manager.state === "return-to-npc"
        ? "三个证据已经找到！回去找界碑爷爷聊聊。"
        : manager.state === "complete"
          ? "研学任务完成，可以继续自由探索。"
          : "三个任务可以按任意顺序完成。";
    const counter = manager.state === "not-started" ? "" : `<p class="quest-counter">证据 ${count} / ${total}</p>`;
    this.questPanel.innerHTML = `
      <span class="eyebrow">友谊关研学</span>
      <h2>${manager.quest.question}</h2>
      <ul>${rows}</ul>
      ${counter}
      <p class="quest-status">${status}</p>`;
  }

  showDialog({ eyebrow = "研学发现", title, body, actions = [], content = "" }) {
    this.overlay.innerHTML = `
      <button class="modal-close" type="button" aria-label="关闭">×</button>
      <span class="eyebrow">${eyebrow}</span>
      <h2>${title}</h2>
      <p>${body}</p>
      ${content}
      <div class="modal-actions"></div>`;
    const actionRoot = this.overlay.querySelector(".modal-actions");
    actions.forEach((action) => {
      const button = document.createElement("button");
      button.className = action.primary ? "primary" : "secondary";
      button.textContent = action.label;
      button.addEventListener("click", () => {
        action.onClick?.();
        if (action.keepOpen !== true) this.closeOverlay();
      });
      actionRoot.appendChild(button);
    });
    this.overlay.querySelector(".modal-close").onclick = () => this.closeOverlay();
    this.overlay.hidden = false;
    this.onModalChange(true);
  }

  closeOverlay() {
    this.overlay.hidden = true;
    this.onModalChange(false);
  }

  showGateObservation(onComplete) {
    const insights = {
      gate: "所有的人、马、货物，都要从这一个门洞里通过——关楼在这里控制着「通行」。",
      wall: "又厚又高的城墙连着两侧大山，让关口易守难攻——它在负责「防守」。",
      tower: "关楼建在城台最高处，站得高、望得远，能提前发现沿着道路走来的人马——它在帮忙「观察」。",
    };
    const observations = new Set();
    const content = `
      <div class="observation-grid">
        <button data-hotspot="gate">城门洞<small>为什么重要道路要从这里穿过去？</small></button>
        <button data-hotspot="wall">厚重城墙<small>它为什么比普通房屋的墙厚得多？</small></button>
        <button data-hotspot="tower">高处关楼<small>站得更高，对观察周围有什么帮助？</small></button>
      </div>
      <p class="observation-insight" data-insight></p>
      <p class="observation-progress">三个观察点都看过，才能拿到证据。</p>`;
    this.showDialog({ eyebrow: "任务一 · 建筑侦探", title: "关楼为什么长这样？", body: "依次观察城门洞、城墙和高处关楼，想一想它怎样控制山间通道。", content });
    this.overlay.querySelectorAll("[data-hotspot]").forEach((button) => {
      button.onclick = () => {
        observations.add(button.dataset.hotspot);
        button.classList.add("observed");
        this.overlay.querySelector("[data-insight]").textContent = insights[button.dataset.hotspot] || "";
        this.overlay.querySelector(".observation-progress").textContent = `${observations.size} / 3 个观察点`;
        if (observations.size >= 3) {
          onComplete();
          this.showEvidenceCard("证据卡 01 · 关隘建筑", "关楼不是普通建筑：一个门洞控制通行，厚墙负责防守，高处负责观察。", "通行 / 防守 / 观察");
        }
      };
    });
  }

  showBoundaryObservation(onComplete) {
    const details = {
      中国: "石碑上刻着国家的名字——站在界碑这一边，就是中国的土地。",
      界碑编号: "1117 是这块界碑的编号。国与国边界上的每一块界碑，都有自己的号码。",
      年份: "2001 是这块界碑设立的年份，它一直在安静地守护着今天的边境。",
    };
    const content = `
      <div class="boundary-details">
        <button data-detail>中国</button><button data-detail>界碑编号</button><button data-detail>年份</button>
      </div>
      <p class="observation-insight" data-insight></p>
      <blockquote>为什么边境上需要这样的界碑？</blockquote>`;
    this.showDialog({
      eyebrow: "任务三 · 边界侦探",
      title: "这块石头在告诉我们什么？",
      body: "走近看一看界碑上记录的三个信息。",
      content,
      actions: [{ label: "完成观察", primary: true, keepOpen: true, onClick: () => {
        const viewed = this.overlay.querySelectorAll("[data-detail].observed").length;
        if (viewed < 3) return this.showToast("再看看界碑上的三个信息吧。");
        onComplete();
        this.showEvidenceCard("证据卡 03 · 边界", "友谊关不仅是一座历史关隘，也站在祖国边境线上，界碑标记着国家与边界。", "国家 / 边界 / 标志");
      } }],
    });
    this.overlay.querySelectorAll("[data-detail]").forEach((button) => {
      button.onclick = () => {
        button.classList.add("observed");
        this.overlay.querySelector("[data-insight]").textContent = details[button.textContent.trim()] || "";
      };
    });
  }

  showTerrainQuestion(onComplete) {
    this.showDialog({
      eyebrow: "任务二 · 地形侦探",
      title: "为什么偏偏建在这里？",
      body: "看看脚下的道路和两侧的大山，再作出选择。",
      actions: [
        { label: "A. 完全开阔的平地", keepOpen: true, onClick: () => {
          this.overlay.querySelector("p").textContent = "再看看道路。两侧的山会不会限制人们通行的方向？";
        } },
        { label: "B. 山地之间的重要通道", primary: true, keepOpen: true, onClick: () => {
          this.showDialog({
            eyebrow: "Lookout Mode",
            title: "沿着道路再看一遍",
            body: "先别急着看答案。找一找：道路是不是被两侧的山集中到这处通道？",
            actions: [{ label: "我看到了：道路从山间穿过", primary: true, keepOpen: true, onClick: () => {
              onComplete();
              this.showEvidenceCard("证据卡 02 · 山地通道", "地形把人们的通行集中到有限的道路，因此这里适合设置关隘。", "山口 / 道路 / 地形");
            } }],
          });
        } },
        { label: "C. 山顶最陡的地方", keepOpen: true, onClick: () => {
          this.overlay.querySelector("p").textContent = "最陡的地方不方便道路通行。再看看关楼和道路在哪里相遇。";
        } },
      ],
    });
  }

  showEvidenceCard(title, body, keywords = "") {
    this.showDialog({
      eyebrow: "获得研学证据",
      title: `【${title}】`,
      body,
      content: keywords ? `<p class="evidence-keywords"><b>关键词</b>　${keywords}</p>` : "",
      actions: [{ label: "继续探索", primary: true }],
    });
  }

  showDiscovery(definition, count, total, isNew) {
    this.showDialog({
      eyebrow: isNew ? "发现历史碎片" : "再次观察",
      title: definition.title,
      body: definition.text,
      content: `<p class="fragment-count">历史碎片 ${count} / ${total}</p>`,
      actions: [{ label: "收进研学手册", primary: true }],
    });
  }

  showSummaryDialog(onSubmit) {
    const selected = new Set();
    const content = `
      <div class="keyword-picks">${["山地", "道路", "边境", "通行", "观察", "守护"].map((word) => `<button data-keyword="${word}">${word}</button>`).join("")}</div>
      <textarea class="summary-answer" data-answer rows="3" maxlength="120" placeholder="再用你自己的话，写一句你的结论吧（可以不写）"></textarea>`;
    this.showDialog({
      eyebrow: "界碑爷爷",
      title: "为什么这里会建一座关？",
      body: "你已经看过关楼、界碑和周围的山。选出你发现的关键词，说出你自己的结论。",
      content,
      actions: [{ label: "说出我的结论", primary: true, keepOpen: true, onClick: () => {
        const answer = this.overlay.querySelector("[data-answer]").value.trim();
        if (!selected.size && !answer) return this.showToast("先选一个关键词，或者写一句你的想法。");
        this.closeOverlay();
        onSubmit([...selected], answer);
      } }],
    });
    this.overlay.querySelectorAll("[data-keyword]").forEach((button) => {
      button.onclick = () => {
        const word = button.dataset.keyword;
        if (selected.has(word)) selected.delete(word); else selected.add(word);
        button.classList.toggle("selected", selected.has(word));
      };
    });
  }

  showStudyCard(manager, answer, grandpaComment = "") {
    const conclusion = answer || "友谊关建在山地之间的通道上，控制着通行，也守望着边境。";
    this.showDialog({
      eyebrow: "研学完成 · 经验 +100",
      title: "我的友谊关研学卡",
      body: "为什么这里会建一座关？",
      content: `
        <div class="study-card-result">
          <p><b>我发现了</b><br>✓ 关楼　✓ 山地与道路　✓ 界碑</p>
          <p><b>我的结论</b><br>${conclusion}</p>
          ${grandpaComment ? `<p><b>界碑爷爷说</b><br>${grandpaComment}</p>` : ""}
          <p><b>历史碎片</b>　${manager.fragments.size} / 5</p>
          <p><b>完成时间</b>　${manager.completedAt ? new Date(manager.completedAt).toLocaleString("zh-CN") : "—"}</p>
        </div>`,
      actions: [
        { label: "继续自由探索", primary: true },
        { label: "前往下一站：边境哨所", onClick: () => { location.href = "world.html?scene=post"; } },
      ],
    });
  }

  showHandbook(manager) {
    if (WORLD_SCENE === "post") {
      const rows = POST_DISCOVERIES.map((item) => {
        const found = manager.fragments.has(item.id);
        return `<li>${found ? "✓" : "○"} ${item.title}${found ? `<small>　${item.text}</small>` : ""}</li>`;
      }).join("");
      this.showDialog({
        eyebrow: "巡逻手册",
        title: "我的哨所巡逻记录",
        body: "巡逻任务：找到哨所里的 6 处巡逻点。",
        content: `<div class="study-card-result"><ul>${rows}</ul><p><b>巡逻碎片</b>　${manager.fragments.size} / ${POST_DISCOVERIES.length}</p></div>`,
        actions: [{ label: "继续巡逻", primary: true }],
      });
      return;
    }
    const evidenceRows = manager.quest.evidences.map((item) => `<li>${manager.evidence.has(item.id) ? "✓" : "○"} ${item.label}</li>`).join("");
    this.showDialog({
      eyebrow: "研学手册",
      title: "我的友谊关发现",
      body: manager.quest.question,
      content: `<div class="study-card-result"><ul>${evidenceRows}</ul><p><b>历史碎片</b>　${manager.fragments.size} / 5</p><p><b>我的回答</b><br>${manager.studentAnswer || "完成三个证据后，再回来写下你的结论。"}</p></div>`,
      actions: [{ label: "继续探索", primary: true }],
    });
  }

  setupDebug({ enabled, onToggleCollider, onTogglePoints, onRecord, onTeleport, onSetPoint, onAddDiscovery }) {
    this.debugPanel.hidden = !enabled;
    if (!enabled) return;
    this.debugPanel.querySelector("[data-debug-collider]").onchange = (event) => onToggleCollider(event.target.checked);
    this.debugPanel.querySelector("[data-debug-points]").onchange = (event) => onTogglePoints(event.target.checked);
    this.debugPanel.querySelector("[data-debug-record]").onclick = onRecord;
    this.debugPanel.querySelector("[data-debug-teleport]").onclick = () => {
      onTeleport(this.debugPanel.querySelector("[data-debug-target]").value);
    };
    this.debugPanel.querySelectorAll("[data-set-layout]").forEach((button) => {
      button.onclick = () => onSetPoint(button.dataset.setLayout);
    });
    this.debugPanel.querySelector("[data-add-discovery]").onclick = onAddDiscovery;
  }

  updateDebug({ x, y, z, fps }) {
    this.debugPanel.querySelector("[data-debug-position]").textContent = `XYZ ${x.toFixed(2)} / ${y.toFixed(2)} / ${z.toFixed(2)}`;
    this.debugPanel.querySelector("[data-debug-fps]").textContent = `${fps} FPS`;
  }

  setDebugRecord(value) {
    this.debugPanel.querySelector("[data-debug-last]").textContent = value;
  }
}
