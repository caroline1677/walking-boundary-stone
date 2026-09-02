const sceneData = {
  pass: {
    eyebrow: "01 · 国门之下",
    title: "走进友谊关",
    body: "拖动视角，沿着国门道路寻找会说话的历史见证者。"
  },
  post: {
    eyebrow: "02 · 山脊之上",
    title: "抵达戍边哨所",
    body: "沿巡逻步道登上山巅，听哨所讲述今天的边关守护。"
  }
};

const agentData = {
  monument: {
    avatar: "碑", name: "会说话的界碑",
    intro: "我见证的不只是一条国界，也是一条连接历史、家国与友谊的时间线。",
    prompts: ["你为什么立在这里？", "介绍友谊关的历史", "今天的国界意味着什么？"],
    answers: ["我立在这里，为往来的人标记国土的边界，也提醒每一位研学者：和平的通道来自一代代人的守护。", "从古代关隘到今天的友谊关，这里既经历过战争，也见证了边贸、交往与友谊。"]
  },
  gate: {
    avatar: "关", name: "镇南关城楼",
    intro: "我的砖石里藏着边关的回声。你可以问我关隘、战争、建筑或今天的国门。",
    prompts: ["你经历过哪些时代？", "城楼为什么建在这里？", "友谊关和镇南关是什么关系？"],
    answers: ["我扼守山谷通道，地形让我成为南疆重要关隘。名字变过，守望与连接的使命一直延续。", "镇南关是友谊关曾使用的重要历史名称，今天的名称更强调和平交往与中越友谊。"]
  },
  lion: {
    avatar: "狮", name: "守关石狮",
    intro: "别看我沉默，我每天都看着人们穿过国门。关于关楼和守护的故事，尽管问我。",
    prompts: ["石狮为什么守在门前？", "你每天看见什么？", "给我一个观察任务"],
    answers: ["传统建筑常用石狮表达守护、庄严与吉祥。在这个场景里，我也是你的研学向导。", "试着观察关楼屋顶、城墙材料和道路方向，想一想地形怎样决定了关隘的位置。"]
  },
  flag: {
    avatar: "旗", name: "山巅国旗",
    intro: "风从山谷升起时，我让这座哨所的方向变得清晰。",
    prompts: ["国旗在哨所意味着什么？", "山上的天气怎样？", "讲讲守边人的一天"],
    answers: ["对守边人而言，国旗既是国家主权的象征，也是每天履职时最明确的精神坐标。", "山地天气变化很快，巡查需要应对大雾、强风和湿滑路面，也要保持通信畅通。"]
  },
  tower: {
    avatar: "哨", name: "山脊瞭望哨",
    intro: "我是现代边境观察与联络节点。我的视野覆盖山谷、道路与远处的山脊。",
    prompts: ["你有哪些现代设备？", "哨所怎样开展巡逻？", "这里最难的工作是什么？"],
    answers: ["现代哨所会使用光学观察、通信、气象和信息化设备协同值守；这个原型预留了接入实时讲解智能体的位置。", "巡逻需要按路线观察界标、道路和周边环境，并及时记录、报告异常情况。"]
  },
  marker: {
    avatar: "界", name: "边境界桩",
    intro: "我站在山脊上，把抽象的边界变成可以辨认、记录和守护的坐标。",
    prompts: ["界桩和界碑有什么不同？", "谁来维护你？", "为什么不能随意移动？"],
    answers: ["界桩通常用于标示边界线上的具体位置，界碑也可承担类似功能；不同场合的形制和称呼会有所区别。", "边界标志涉及国家领土与双方协议，必须依照规范维护，不能擅自移动或破坏。"]
  }
};

const viewport = document.getElementById("viewport");
const sceneStack = document.getElementById("sceneStack");
const switchButtons = [...document.querySelectorAll(".scene-switcher button")];
const scenes = [...document.querySelectorAll(".scene")];
const panel = document.getElementById("agentPanel");
const chat = document.getElementById("agentChat");
const input = document.getElementById("agentInput");
const dragHint = document.getElementById("dragHint");
const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;

let activeScene = "pass";
let activeAgent = null;
let dragging = false;
let moved = false;
let startX = 0;
let startY = 0;
let startPanX = 0;
let startPanY = 0;
let panX = 0;
let panY = 0;
let targetX = 0;
let targetY = 0;
let zoom = 1.04;

function renderCamera() {
  panX += (targetX - panX) * .09;
  panY += (targetY - panY) * .09;
  const active = document.querySelector(".scene.is-active .scene-image");
  if (active) {
    active.style.setProperty("--pan-x", `${panX}px`);
    active.style.setProperty("--pan-y", `${panY}px`);
    active.style.setProperty("--zoom", zoom.toFixed(3));
  }
  const activeSceneElement = document.querySelector(".scene.is-active");
  if (activeSceneElement) {
    activeSceneElement.style.setProperty("--hotspot-shift-x", `${panX * .62}px`);
    activeSceneElement.style.setProperty("--hotspot-shift-y", `${panY * .62}px`);
  }
  document.getElementById("compassNeedle").style.transform = `rotate(${panX * -.18}deg)`;
  if (!reduceMotion) requestAnimationFrame(renderCamera);
}

function setScene(id) {
  if (id === activeScene) return;
  activeScene = id;
  targetX = targetY = panX = panY = 0;
  zoom = 1.04;
  scenes.forEach(scene => {
    const selected = scene.dataset.scene === id;
    scene.classList.toggle("is-active", selected);
    scene.toggleAttribute("inert", !selected);
  });
  switchButtons.forEach(button => {
    const selected = button.dataset.target === id;
    button.classList.toggle("active", selected);
    button.setAttribute("aria-selected", String(selected));
  });
  const data = sceneData[id];
  document.getElementById("sceneEyebrow").textContent = data.eyebrow;
  document.getElementById("sceneTitle").textContent = data.title;
  document.getElementById("sceneBody").textContent = data.body;
  closeAgent();
}

function addMessage(text, role) {
  const message = document.createElement("div");
  message.className = `message ${role}`;
  message.textContent = text;
  chat.append(message);
  chat.scrollTop = chat.scrollHeight;
}

function openAgent(id) {
  const data = agentData[id];
  if (!data) return;
  activeAgent = id;
  document.getElementById("agentAvatar").textContent = data.avatar;
  document.getElementById("agentName").textContent = data.name;
  document.getElementById("agentIntro").textContent = data.intro;
  const tags = document.getElementById("agentTags");
  tags.replaceChildren(...data.prompts.map(prompt => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = prompt;
    button.addEventListener("click", () => sendQuestion(prompt));
    return button;
  }));
  chat.replaceChildren();
  addMessage(`你好，我是${data.name}。${data.intro}`, "agent");
  panel.classList.add("open");
  panel.setAttribute("aria-hidden", "false");
  dragHint.style.opacity = "0";
}

function closeAgent() {
  panel.classList.remove("open");
  panel.setAttribute("aria-hidden", "true");
  activeAgent = null;
}

function sendQuestion(question) {
  if (!activeAgent || !question.trim()) return;
  const data = agentData[activeAgent];
  addMessage(question.trim(), "user");
  input.value = "";
  const answer = data.answers[Math.abs(question.length) % data.answers.length];
  window.setTimeout(() => addMessage(answer, "agent"), 320);
}

switchButtons.forEach(button => button.addEventListener("click", () => setScene(button.dataset.target)));
document.querySelectorAll(".hotspot").forEach(button => button.addEventListener("click", event => {
  if (!moved) openAgent(event.currentTarget.dataset.agent);
}));
document.getElementById("agentClose").addEventListener("click", closeAgent);
document.getElementById("agentForm").addEventListener("submit", event => {
  event.preventDefault();
  sendQuestion(input.value);
});

viewport.addEventListener("pointerdown", event => {
  if (event.target.closest("button, input, .agent-panel, .scene-switcher")) return;
  dragging = true;
  moved = false;
  startX = event.clientX;
  startY = event.clientY;
  startPanX = targetX;
  startPanY = targetY;
  viewport.classList.add("is-dragging");
  viewport.setPointerCapture(event.pointerId);
});
viewport.addEventListener("pointermove", event => {
  if (!dragging) return;
  const dx = event.clientX - startX;
  const dy = event.clientY - startY;
  moved = Math.abs(dx) + Math.abs(dy) > 5;
  targetX = Math.max(-90, Math.min(90, startPanX + dx * .28));
  targetY = Math.max(-28, Math.min(28, startPanY + dy * .12));
});
viewport.addEventListener("pointerup", event => {
  dragging = false;
  startX = event.clientX;
  startY = event.clientY;
  viewport.classList.remove("is-dragging");
  dragHint.style.opacity = "0";
});
viewport.addEventListener("wheel", event => {
  if (event.target.closest(".agent-panel")) return;
  event.preventDefault();
  zoom = Math.max(1.01, Math.min(1.19, zoom - event.deltaY * .00018));
  if (Math.abs(event.deltaY) > 110 && !panel.classList.contains("open")) {
    setScene(event.deltaY > 0 ? "post" : "pass");
  }
}, { passive: false });

const helpCard = document.getElementById("helpCard");
document.getElementById("helpButton").addEventListener("click", () => { helpCard.hidden = false; });
document.getElementById("helpClose").addEventListener("click", () => { helpCard.hidden = true; });
document.addEventListener("keydown", event => {
  if (event.key === "Escape") { closeAgent(); helpCard.hidden = true; }
  if (event.key === "ArrowRight") setScene("post");
  if (event.key === "ArrowLeft") setScene("pass");
});

if (!reduceMotion) requestAnimationFrame(renderCamera);
else renderCamera();
