const eras = [
  {
    id: "han", name: "汉代", subtitle: "雍鸡关 · 南疆初定", glyph: "雍",
    year: "前 111", yearUnit: "公元", badge: "汉 · 元鼎六年", seal: "汉",
    top: "雍鸡关", bottom: "南疆古道",
    kicker: "岭南初定 · 关隘初现",
    title: "我最早的名字，<br>叫作雍鸡关。",
    body: "两千多年前，我守在左弼山与右辅山之间。南来北往的脚步穿过狭长隘口，边地交通与守备的故事，也从这里开始。",
    speech: "孩子，你现在看到的友谊关，在汉代被称作雍鸡关。那时的我还没有今天的关楼，却已守望着南疆古道。山风送来马蹄声，也送来不同地域最早的相遇。",
    audio: "assets/audio/han.mp3",
    image: "assets/友谊关关楼.jpg",
    caption: "古关依山势而建。今天的关楼虽经重建，仍延续着这处隘口跨越两千年的守望。",
    questions: ["为什么建在这里？", "雍鸡关是什么意思？"]
  },
  {
    id: "ming", name: "明代", subtitle: "镇南关 · 雄关立名", glyph: "镇",
    year: "1427", yearUnit: "明宣德二年", badge: "明 · 宣德年间", seal: "明",
    top: "镇南关", bottom: "南疆雄关",
    kicker: "关楼重筑 · 镇守南疆",
    title: "镇南关之名，<br>在山谷间回响。",
    body: "明代，关隘逐渐以“镇南关”闻名。关墙、关楼与山势相连，构成南疆门户。名字的变化，记录着边防格局与国家治理的演进。",
    speech: "到了明代，人们称我镇南关。城墙依山蜿蜒，关楼扼守隘口。每一块石砖，都记下了戍卒的脚步，也记下了边疆从险阻走向通途的漫长变化。",
    audio: "assets/audio/ming.mp3",
    image: "assets/友谊关关楼.jpg",
    caption: "关楼位于两山之间，古城墙顺山势延伸，形成“一夫当关”的边关格局。",
    questions: ["镇南关何时得名？", "古城墙如何防守？"]
  },
  {
    id: "qing", name: "清代", subtitle: "镇南关大捷 · 1885", glyph: "捷",
    year: "1885", yearUnit: "清光绪十一年", badge: "清 · 镇南关大捷", seal: "捷",
    top: "镇南关", bottom: "寸土不让",
    kicker: "边关烽火 · 浴血守土",
    title: "那一年，炮火震山，<br>我见证了镇南关大捷。",
    body: "1885 年，冯子材率军在镇南关抗击法国侵略军，取得震动中外的胜利。古关成为中华民族不屈精神的重要见证。",
    speech: "光绪十一年，炮火照亮群山。老将冯子材率军奋勇抗敌，冲锋的呐喊越过关墙。镇南关大捷告诉后来的人：脚下的每一寸土地，都值得用勇气守护。",
    audio: "assets/audio/qing.mp3",
    image: "assets/冯子材抗法战斗群像.jpg",
    caption: "冯子材抗法战斗群像，再现了镇南关大捷中军民奋勇抗敌的历史场景。",
    questions: ["冯子材是谁？", "大捷为什么重要？"]
  },
  {
    id: "modern", name: "当代", subtitle: "友谊关 · 开放国门", glyph: "友",
    year: "1965", yearUnit: "更名至今", badge: "当代 · 友谊关", seal: "中",
    top: "中国", bottom: "1117 · 友谊关",
    kicker: "从边关到国门 · 连接与开放",
    title: "我有了一个温暖的名字：<br>友谊关。",
    body: "1965 年，睦南关更名为友谊关。今天，这里既保存着厚重的边关记忆，也仍在履行口岸职能，让游客、商贸与文化在国门间流动。",
    speech: "一九六五年，我有了今天的名字，友谊关。曾经的屏障，如今成为开放的国门。货车、游客与年轻研学者从我身边经过。我依然坚定地守在这里，也温暖地迎接八方来风。",
    audio: "assets/audio/modern.mp3",
    image: "assets/友谊关界碑.jpg",
    caption: "中国 1117 号界碑。研学者描红“中国”二字，在真实边境理解国家、边界与开放。",
    questions: ["为什么改名友谊关？", "今天口岸做什么？"]
  }
];

const refs = {
  eraList: document.querySelector("#eraList"), monument: document.querySelector("#monument"),
  seal: document.querySelector("#seal"), top: document.querySelector("#inscriptionTop"),
  bottom: document.querySelector("#inscriptionBottom"), badge: document.querySelector("#eraBadge"),
  year: document.querySelector("#year"), yearUnit: document.querySelector("#yearUnit"),
  kicker: document.querySelector("#storyKicker"), title: document.querySelector("#storyTitle"),
  body: document.querySelector("#storyBody"), speech: document.querySelector("#speechText"),
  image: document.querySelector("#evidenceImage"), caption: document.querySelector("#evidenceCaption"),
  suggestions: document.querySelector("#suggestions"), speak: document.querySelector("#speakButton"),
  answerCard: document.querySelector("#answerCard"), answerText: document.querySelector("#answerText"),
  chatHistory: document.querySelector("#chatHistory"),
  status: document.querySelector("#speechStatus"), progress: document.querySelector("#progressBar"),
  progressText: document.querySelector("#progressText"), question: document.querySelector("#questionInput"),
  ask: document.querySelector("#askButton"), sound: document.querySelector("#soundToggle")
};

let current = 0;
let muted = false;
let utterance;
let narrationAudio;
let audioLoadTimer;
let ttsRequestController;

function renderEraButtons() {
  refs.eraList.innerHTML = eras.map((era, i) => `
    <button class="era-button ${i === current ? "active" : ""}" data-era="${i}">
      <span class="num">0${i + 1}</span>
      <span><b>${era.name}</b><small>${era.subtitle}</small></span>
      <span class="glyph">${era.glyph}</span>
    </button>`).join("");
  refs.eraList.querySelectorAll("button").forEach(button => {
    button.addEventListener("click", () => setEra(Number(button.dataset.era)));
  });
}

function setEra(index) {
  stopSpeech();
  current = index;
  const era = eras[index];
  refs.monument.className = `monument era-${era.id}`;
  refs.seal.textContent = era.seal;
  refs.top.textContent = era.top;
  refs.bottom.textContent = era.bottom;
  refs.badge.textContent = era.badge;
  refs.year.textContent = era.year;
  refs.yearUnit.textContent = era.yearUnit;
  refs.kicker.textContent = era.kicker;
  refs.title.innerHTML = era.title;
  refs.body.textContent = era.body;
  refs.speech.textContent = era.speech;
  refs.image.src = era.image;
  refs.caption.textContent = era.caption;
  refs.progress.style.width = `${(index + 1) / eras.length * 100}%`;
  refs.progressText.textContent = `${index + 1} / ${eras.length}`;
  refs.suggestions.innerHTML = era.questions.map(q => `<button>${q}</button>`).join("");
  refs.suggestions.querySelectorAll("button").forEach(btn => btn.addEventListener("click", () => askQuestion(btn.textContent)));
  renderEraButtons();
}

function speak(text = eras[current].speech) {
  if (muted) {
    refs.status.textContent = "声音已关闭";
    return;
  }
  stopSpeech();
  const era = eras[current];
  if (text === era.speech && era.audio) {
    narrationAudio = new Audio(era.audio);
    narrationAudio.preload = "auto";
    let audioStarted = false;
    const startRemoteAudio = () => {
      if (audioStarted || !narrationAudio) return;
      audioStarted = true;
      clearTimeout(audioLoadTimer);
      narrationAudio.play().then(() => {
        setSpeakingState(true, "Fish Audio 老者正在讲述…");
      }).catch(() => {
        playLocalMaleVoice(text);
      });
    };
    narrationAudio.oncanplay = startRemoteAudio;
    narrationAudio.oncanplaythrough = startRemoteAudio;
    narrationAudio.onended = () => stopSpeech(false);
    narrationAudio.onerror = () => {
      clearTimeout(audioLoadTimer);
      narrationAudio = null;
      playLocalMaleVoice(text);
    };
    refs.status.textContent = "正在加载 Fish Audio 老者声音…";
    narrationAudio.load();
    audioLoadTimer = setTimeout(() => {
      if (!audioStarted) {
        if (narrationAudio) narrationAudio.pause();
        narrationAudio = null;
        playLocalMaleVoice(text);
      }
    }, 2500);
    return;
  }
  playFishVoice(text);
}

async function playFishVoice(text) {
  ttsRequestController = new AbortController();
  refs.status.textContent = "正在生成 Fish Audio 老者回答…";
  try {
    const response = await fetch("/api/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
      signal: ttsRequestController.signal
    });
    const result = await response.json();
    if (!response.ok || !result.audioUrl) {
      throw new Error(result.error || "语音生成失败");
    }
    narrationAudio = new Audio(result.audioUrl);
    narrationAudio.onended = () => stopSpeech(false);
    narrationAudio.onerror = () => playLocalMaleVoice(text);
    await narrationAudio.play();
    setSpeakingState(true, "Fish Audio 老者正在回答…");
  } catch (error) {
    if (error.name === "AbortError") return;
    console.warn("Fish Audio TTS failed:", error.message);
    playLocalMaleVoice(text);
  } finally {
    ttsRequestController = null;
  }
}

function playLocalMaleVoice(text) {
  if (!("speechSynthesis" in window)) {
    refs.status.textContent = "当前浏览器不支持语音朗读";
    return;
  }
  utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "zh-CN";
  utterance.rate = .76;
  utterance.pitch = .62;
  utterance.volume = 1;
  const voices = speechSynthesis.getVoices();
  const rankedNames = [/康康|Kangkang/i, /云健|Yunjian/i, /云扬|Yunyang/i, /云枫|Yunfeng/i];
  utterance.voice = rankedNames
    .map(pattern => voices.find(v => /zh-CN|Chinese/i.test(`${v.lang} ${v.name}`) && pattern.test(v.name)))
    .find(Boolean) || null;
  if (!utterance.voice) {
    refs.status.textContent = "未检测到中文男声，请安装“Microsoft Kangkang”";
    return;
  }
  const isNarration = text === eras[current].speech;
  utterance.onstart = () => setSpeakingState(
    true,
    isNarration ? "本机康康男声正在讲述…" : "本机康康男声正在回答…"
  );
  utterance.onend = utterance.onerror = () => stopSpeech(false);
  speechSynthesis.speak(utterance);
}

function setSpeakingState(active, message) {
  refs.monument.classList.toggle("speaking", active);
  refs.speak.classList.toggle("playing", active);
  refs.speak.querySelector("span").textContent = active ? "暂停讲述" : "听界碑讲述";
  refs.status.textContent = message;
}

function stopSpeech(cancel = true) {
  clearTimeout(audioLoadTimer);
  if (ttsRequestController) {
    ttsRequestController.abort();
    ttsRequestController = null;
  }
  if (cancel && "speechSynthesis" in window) speechSynthesis.cancel();
  if (narrationAudio) {
    narrationAudio.pause();
    narrationAudio.currentTime = 0;
    narrationAudio = null;
  }
  setSpeakingState(false, "点击播放 · 约 20 秒");
  refs.status.textContent = "点击播放 · 约 20 秒";
}

async function askQuestion(question) {
  const era = eras[current];
  const knowledge = {
    "为什么建在这里？": "因为这里位于左弼山与右辅山之间，是连接中原与岭南、通往越南方向的天然隘口，易守也便于通行。",
    "雍鸡关是什么意思？": "雍鸡关是友谊关在汉代的早期称呼之一。名称随着朝代、疆域治理和边防功能变化而多次更迭。",
    "镇南关何时得名？": "材料记载，明代以后“镇南关”成为这座关隘延续数百年的重要名称。",
    "古城墙如何防守？": "城墙依山势修筑，与两侧山体相接，把天然隘口与人工防御结合起来。",
    "冯子材是谁？": "冯子材是清末爱国将领。1885 年，他率军在镇南关抗击法国侵略军并取得大捷。",
    "大捷为什么重要？": "镇南关大捷沉重打击了法国侵略军，振奋民族精神，也让这座关成为守土报国的重要历史象征。",
    "为什么改名友谊关？": "1965 年，这座关隘被命名为友谊关，表达从长期对峙走向和平、友好与开放的时代愿望。",
    "今天口岸做什么？": "今天的友谊关仍履行口岸职能，承担人员往来、跨境贸易和文化交流，也是重要的爱国主义与边关研学基地。"
  };
  let answer = knowledge[question];
  if (!answer) {
    refs.status.textContent = "正在询问研学智能体…";
    try {
      const response = await fetch("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ prompt: question, era: era.name }) });
      const result = await response.json();
      if (!response.ok || !result.answer) throw new Error(result.error || "Coze 未返回答案");
      answer = result.answer;
    } catch (error) {
      console.warn("Coze request failed:", error);
      answer = "暂时无法获得界碑回答，请稍后再试。";
    }
  }
  renderChatMessage(question, answer);
  refs.speech.textContent = cleanNarrationText(answer);
  refs.answerText.textContent = answer;
  refs.answerCard.hidden = false;
  refs.question.value = "";
  speak(answer);
}

function renderChatMessage(question, answer) {
  refs.chatHistory.insertAdjacentHTML("beforeend", `<div class="chat-message user"><small>你</small>${escapeHtml(question)}</div><div class="chat-message assistant"><small>界碑</small>${renderAgentContent(answer)}</div>`);
  refs.chatHistory.scrollTop = refs.chatHistory.scrollHeight;
}

function escapeHtml(value) { return value.replace(/[&<>\"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'\"':"&quot;","'":"&#039;"}[char])); }
function renderAgentContent(value) {
  const images = [];
  let plain = value.replace(/!\[([^\]]*)\]\((https?:\/\/[^\s)]+)\)/g, (_, alt, url) => { images.push({alt, url}); return ""; });
  let html = escapeHtml(plain).replace(/\n/g, "<br>");
  html += images.map(({alt, url}) => `<span class="agent-media"><a href="${url}" target="_blank" rel="noopener"><img class="agent-image" src="${url}" alt="${escapeHtml(alt)}" loading="lazy"></a><a class="agent-download" href="${url}" download target="_blank" rel="noopener">下载图片</a></span>`).join("");
  html = html.replace(/(https?:\/\/[^\s<]+\.(?:mp4|webm)(?:\?[^\s<]+)?)/gi, (_, url) => `<video class="agent-video" controls preload="metadata" src="${url}"></video>`);
  html = html.replace(/(https?:\/\/[^\s<]+\.(?:mp3|wav|m4a)(?:\?[^\s<]+)?)/gi, (_, url) => `<audio class="agent-audio" controls src="${url}"></audio>`);
  html = html.replace(/(https?:\/\/[^\s<]+\.(?:pdf|docx|pptx)(?:\?[^\s<]+)?)/gi, (_, url) => `<a class="agent-file" href="${url}" target="_blank" rel="noopener">📥 下载文件</a>`);
  return html;
}
function cleanNarrationText(value) { return value.replace(/!\[[^\]]*\]\(https?:\/\/[^\s)]+\)/g, "").replace(/https?:\/\/\S+/g, "").replace(/\n{3,}/g, "\n\n").trim(); }

refs.speak.addEventListener("click", () => {
  if ((narrationAudio && !narrationAudio.paused) || speechSynthesis.speaking) stopSpeech();
  else speak();
});
refs.ask.addEventListener("click", () => refs.question.value.trim() && askQuestion(refs.question.value.trim()));
refs.question.addEventListener("keydown", e => {
  if (e.key === "Enter" && refs.question.value.trim()) askQuestion(refs.question.value.trim());
});
refs.sound.addEventListener("click", () => {
  muted = !muted;
  refs.sound.textContent = muted ? "静" : "声";
  refs.sound.setAttribute("aria-label", muted ? "开启声音" : "关闭声音");
  if (muted) stopSpeech();
});

// 麦克风语音提问：点击说话 → 录音上传本地识别 → 自动送入问答管线。
const micButton = document.querySelector("#micButton");
if (micButton) {
  micButton.addEventListener("click", () => {
    if (!window.SpeechInput) return;
    window.SpeechInput.toggle({
      onState: (state) => {
        if (state === "listening") refs.status.textContent = "正在听你说话…";
        else if (state === "recognizing") refs.status.textContent = "正在识别…";
      },
      onText: (text) => {
        refs.question.value = text;
        refs.ask.click();
      },
      onError: (message) => {
        refs.status.textContent = message;
      },
    });
  });
}

setEra(0);
