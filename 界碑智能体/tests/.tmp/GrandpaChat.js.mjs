import * as THREE from "three";

/**
 * 界碑爷爷实时对话：语音识别（浏览器 STT）→ /api/chat（Coze 扮演爷爷）→
 * /api/tts（Fish Audio，与"行走的界碑"页同款音色）→ 播放 + 模型说话动画。
 * 语音不可用时自动降级为打字/点选问题。
 */
export class GrandpaChat {
  constructor({ model, quest, world }) {
    this.model = model;          // 爷爷模型（说话时轻微摆动）
    this.quest = quest;
    this.world = world;
    this.baseY = model ? model.position.y : 0;
    this.talking = false;
    this.open = false;
    this.recognizing = false;
    this.buildDom();
    this.attachModel = (model) => {
      this.model = model;
      this.baseY = model.position.y;
    };
  }

  buildDom() {
    const root = document.createElement("div");
    root.className = "grandpa-chat";
    root.hidden = true;
    root.innerHTML = `
      <div class="gc-head">
        <span class="gc-dot"></span><b>界碑爷爷 · 实时对话</b>
        <button class="gc-close" type="button" aria-label="关闭">×</button>
      </div>
      <div class="gc-log"></div>
      <div class="gc-chips">
        <button type="button" data-q="爷爷，你好呀！你是谁呀？">爷爷你好</button>
        <button type="button" data-q="为什么友谊关会建在这里呀？">为什么建在这里</button>
        <button type="button" data-q="这块界碑有什么故事呀？">界碑的故事</button>
      </div>
      <div class="gc-input">
        <button class="gc-mic" type="button" title="说话提问">🎤</button>
        <input type="text" placeholder="点麦克风说话，或者打字问爷爷…" maxlength="120">
        <button class="gc-send" type="button">发送</button>
      </div>`;
    document.body.appendChild(root);
    this.root = root;
    this.log = root.querySelector(".gc-log");
    this.input = root.querySelector("input");
    root.querySelector(".gc-close").onclick = () => this.close();
    root.querySelector(".gc-send").onclick = () => {
      const text = this.input.value.trim();
      if (text) { this.input.value = ""; this.ask(text); }
    };
    this.input.addEventListener("keydown", (e) => {
      if (e.code === "Enter") {
        const text = this.input.value.trim();
        if (text) { this.input.value = ""; this.ask(text); }
      }
    });
    root.querySelectorAll(".gc-chips button").forEach((b) => {
      b.onclick = () => this.ask(b.dataset.q);
    });
    const mic = root.querySelector(".gc-mic");
    mic.addEventListener("click", () => {
      if (!window.SpeechInput) return;
      window.SpeechInput.toggle({
        onState: (state) => {
          if (state === "listening") this.push("bubble-user", "（我在听，请讲…）");
        },
        onText: (text) => this.ask(text),
        onError: (message) => this.push("bubble-grandpa", message),
      });
    });
  }

  show() {
    this.root.hidden = false;
    this.open = true;
    if (!this.log.childElementCount) {
      this.push("bubble-grandpa", "小朋友，你来啦？有什么想问爷爷的，尽管说！");
      this.speak("小朋友，你来啦？有什么想问爷爷的，尽管说！");
    }
    this.input.focus();
  }

  hide() {
    this.root.hidden = true;
    this.open = false;
    this.stopTalkAnim();
  }

  toggle() { this.open ? this.hide() : this.show(); }

  push(kind, text) {
    const div = document.createElement("div");
    div.className = kind;
    div.textContent = text;
    this.log.appendChild(div);
    this.log.scrollTop = this.log.scrollHeight;
    return div;
  }

  contextLine() {
    const evidence = this.quest ? this.quest.evidence.size : 0;
    const fragments = this.quest ? this.quest.fragments.size : 0;
    return `小朋友已找到证据 ${evidence}/3、历史碎片 ${fragments} 条。`;
  }

  async ask(text) {
    if (this.asking) return;
    this.asking = true;
    this.push("bubble-user", text);
    const replyEl = this.push("bubble-grandpa", "…");
    let answer = "";
    try {
      const persona = `现在请扮演"界碑爷爷"：守着友谊关界碑几十年的慈祥老爷爷，戴竹帽、白胡子、拄拐杖，称呼小朋友，不要用"乖娃子"等称呼。${this.contextLine()}请用不超过60字的口语化中文、温暖地回答小朋友的话。`;
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: `${persona}\n小朋友说：${text}`, era: "当代" }),
      });
      const data = await response.json();
      answer = data && data.ok ? String(data.answer || "").trim() : "";
    } catch { answer = ""; }
    if (!answer) answer = this.localReply(text);
    replyEl.textContent = answer;
    this.log.scrollTop = this.log.scrollHeight;
    this.speak(answer);
    this.asking = false;
  }

  localReply(text) {
    const t = text || "";
    if (/你好|你是谁|爷爷/.test(t)) return "爷爷在这儿守了几十年界碑喽，小朋友你想问什么尽管说！";
    if (/为什么|建在|这里/.test(t)) return "你看，大山把路挤成了一条道，关口卡在正中间——守在这里就守住了整条路呀。";
    if (/界碑|故事/.test(t)) return "这块界碑上刻着国家和编号，它站在哪儿，哪儿的山河就是咱们的家。";
    if (/越南|边境|对面/.test(t)) return "界线那边就是邻国越南喽，两边的娃娃抬头看的可是同一片天哟。";
    return "爷爷年纪大啦，没听太清。你再说一遍，或者沿着路走走看看，答案就在眼前喽。";
  }

  async speak(text) {
    this.startTalkAnim();
    try {
      const response = await fetch("/api/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: String(text).slice(0, 480) }),
      });
      const data = await response.json();
      if (!data || !data.ok || !data.audioUrl) throw new Error("tts");
      if (!this.audio) this.audio = new Audio();
      this.audio.src = data.audioUrl;
      this.audio.onended = () => this.stopTalkAnim();
      await this.audio.play();
      return true;
    } catch {
      this.stopTalkAnim();
      return false;
    }
  }

  startTalkAnim() {
    if (!this.model || this.talking) return;
    this.talking = true;
    const baseY = this.model.position.y;
    const baseRot = this.model.rotation.y;
    const step = () => {
      if (!this.talking) return;
      const t = performance.now() / 1000;
      this.model.position.y = baseY + Math.abs(Math.sin(t * 5.5)) * 0.035;
      this.model.rotation.y = baseRot + Math.sin(t * 2.2) * 0.08;
      requestAnimationFrame(step);
    };
    step();
  }

  stopTalkAnim() {
    this.talking = false;
    if (this.model) {
      this.model.position.y = this.baseY;
    }
  }
}
