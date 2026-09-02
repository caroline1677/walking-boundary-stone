/**
 * 录音 → /api/stt（本地 Whisper）→ 文字。
 * 经典脚本（非 module），供 world.html 的 GrandpaChat 与 index.html 的 app.js 共用。
 *
 * 用法：
 *   SpeechInput.toggle({
 *     onState: (state) => {},   // "listening" | "recognizing" | "idle"
 *     onText: (text) => {},     // 识别成功
 *     onError: (message) => {}, // 失败（权限/网络/无声）
 *   });
 * 再调一次 toggle 即停止录音并进入识别。
 */
window.SpeechInput = {
  recording: false,
  _timer: null,

  available() {
    return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder);
  },

  async toggle(handlers) {
    handlers = handlers || {};
    if (this.recording) {
      this._stop();
      return "stopped";
    }
    if (!this.available()) {
      if (handlers.onError) handlers.onError("当前浏览器不支持录音");
      return;
    }
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      if (handlers.onError) handlers.onError("需要允许使用麦克风才能说话哦");
      return;
    }
    this._handlers = handlers;
    this._chunks = [];
    this.recorder = new MediaRecorder(stream);
    this.recorder.ondataavailable = (event) => {
      if (event.data && event.data.size) this._chunks.push(event.data);
    };
    this.recorder.onstop = () => {
      this.recording = false;
      clearTimeout(this._timer);
      if (this.stream) {
        this.stream.getTracks().forEach((track) => track.stop());
        this.stream = null;
      }
      if (handlers.onState) handlers.onState("recognizing");
      const blob = new Blob(this._chunks, { type: this.recorder.mimeType || "audio/webm" });
      this._recognize(blob, handlers);
    };
    this.recorder.start();
    this.recording = true;
    if (handlers.onState) handlers.onState("listening");
    this._timer = setTimeout(() => {
      if (this.recording) this._stop();
    }, 12000);
  },

  _stop() {
    if (this.recorder && this.recorder.state !== "inactive") this.recorder.stop();
  },

  async _recognize(blob, handlers) {
    try {
      const response = await fetch("/api/stt", { method: "POST", body: blob });
      const data = await response.json();
      const text = data && data.ok ? String(data.text || "").trim() : "";
      if (text) {
        if (handlers.onText) handlers.onText(text);
      } else if (handlers.onError) {
        handlers.onError((data && data.error) || "没有听清，再试一次好吗");
      }
    } catch {
      if (handlers.onError) handlers.onError("语音识别服务不可用");
    }
  },
};
