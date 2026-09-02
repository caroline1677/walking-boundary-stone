#!/usr/bin/env node

const ERA_DATA = {
  "汉代": {
    defaultTopic: "雍鸡关与南疆古道",
    evidence: ["山地隘口", "南北通道", "早期关隘名称"],
    inquiry: "天然地形为什么会决定古代道路和关隘的位置？",
  },
  "明代": {
    defaultTopic: "镇南关与关防格局",
    evidence: ["友谊关关楼", "依山势延伸的城墙", "穿关道路"],
    inquiry: "古人如何把天然山势与人工建筑结合起来守护通道？",
  },
  "清代": {
    defaultTopic: "1885年镇南关大捷",
    evidence: ["冯子材抗法战斗史料", "镇南关地形", "守土报国的历史记忆"],
    inquiry: "镇南关大捷为什么能成为守土报国精神的重要象征？",
  },
  "当代": {
    defaultTopic: "从边关到开放国门",
    evidence: ["中国1117号界碑", "今日友谊关口岸", "人员、贸易与文化交流"],
    inquiry: "一座历史上的防御性关隘，今天如何成为连接与开放的国门？",
  },
};

function parseArgs(argv) {
  const result = {};
  for (let index = 0; index < argv.length; index += 1) {
    const item = argv[index];
    if (item === "--help" || item === "-h") result.help = true;
    else if (item.startsWith("--")) {
      const key = item.slice(2);
      const value = argv[index + 1];
      if (!value || value.startsWith("--")) throw new Error(`参数 ${item} 缺少值`);
      result[key] = value;
      index += 1;
    } else {
      throw new Error(`无法识别的参数：${item}`);
    }
  }
  return result;
}

function helpText() {
  return [
    "用法：",
    "  node scripts/generate-study-plan.mjs --era 清代 --topic 镇南关大捷 --grade 五年级 --minutes 40 --format markdown",
    "",
    "--era     汉代|明代|清代|当代",
    "--topic   可选，研学主题",
    "--grade   可选，默认小学高年级",
    "--minutes 可选，20-120，默认40",
    "--format  json|markdown，默认json",
  ].join("\n");
}

function buildPlan(options) {
  const era = options.era ?? "当代";
  const eraData = ERA_DATA[era];
  if (!eraData) throw new Error(`不支持的时代：${era}。请使用汉代、明代、清代或当代。`);

  const minutes = Number(options.minutes ?? 40);
  if (!Number.isInteger(minutes) || minutes < 20 || minutes > 120) {
    throw new Error("--minutes 必须是20到120之间的整数");
  }

  const topic = options.topic ?? eraData.defaultTopic;
  const grade = options.grade ?? "小学高年级";
  const opening = Math.max(5, Math.round(minutes * 0.15));
  const inquiry = Math.max(10, Math.round(minutes * 0.55));
  const sharing = minutes - opening - inquiry;

  return {
    title: `一块行走的界碑：${topic}`,
    era,
    grade,
    durationMinutes: minutes,
    learningObjectives: [
      `说出${era}友谊关地区的一项核心历史特征`,
      "通过建筑、地形或史料寻找支持观点的证据",
      "理解守土报国、和平友好与开放交流的时代意义",
    ],
    schedule: [
      { minutes: opening, activity: "界碑第一人称导入，提出核心问题" },
      { minutes: inquiry, activity: "小组观察证据、记录发现并完成探究任务" },
      { minutes: sharing, activity: "分享证据链，完成一句话研学结论" },
    ],
    evidenceToObserve: eraData.evidence,
    inquiryQuestion: eraData.inquiry,
    studentTasks: [
      "选择一项现场或图像证据，记录“我看到了什么”",
      "将证据与时代背景连接，说明“它能证明什么”",
      "小组用“观点+证据+解释”回答核心问题",
    ],
    assessment: {
      evidence: "能指出至少一项具体证据",
      reasoning: "能说明证据与历史或地理特征的关系",
      expression: "结论清楚，不混淆时代",
    },
    safety: [
      "全程听从教师和现场管理人员安排",
      "不攀爬关楼、城墙、界碑或边境设施",
      "不离队，不进入未开放区域，不拍摄禁止拍摄的设施",
    ],
  };
}

function toMarkdown(plan) {
  const lines = [
    `# ${plan.title}`,
    "",
    `- 时代：${plan.era}`,
    `- 学段：${plan.grade}`,
    `- 时长：${plan.durationMinutes}分钟`,
    "",
    "## 学习目标",
    ...plan.learningObjectives.map((item) => `- ${item}`),
    "",
    "## 活动流程",
    ...plan.schedule.map((item) => `- ${item.minutes}分钟：${item.activity}`),
    "",
    "## 观察证据",
    ...plan.evidenceToObserve.map((item) => `- ${item}`),
    "",
    "## 核心问题",
    plan.inquiryQuestion,
    "",
    "## 学生任务",
    ...plan.studentTasks.map((item, index) => `${index + 1}. ${item}`),
    "",
    "## 安全提示",
    ...plan.safety.map((item) => `- ${item}`),
  ];
  return lines.join("\n");
}

try {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    console.log(helpText());
    process.exit(0);
  }
  const format = options.format ?? "json";
  if (!["json", "markdown"].includes(format)) throw new Error("--format 只能是 json 或 markdown");
  const plan = buildPlan(options);
  console.log(format === "markdown" ? toMarkdown(plan) : JSON.stringify(plan, null, 2));
} catch (error) {
  console.error(`生成失败：${error.message}`);
  process.exit(1);
}

