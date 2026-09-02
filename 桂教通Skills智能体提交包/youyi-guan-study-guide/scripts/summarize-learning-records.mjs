#!/usr/bin/env node

import fs from "node:fs";

function parseArgs(argv) {
  const options = {};
  for (let i = 0; i < argv.length; i += 1) {
    const item = argv[i];
    if (item === "--help" || item === "-h") options.help = true;
    else if (item.startsWith("--")) {
      const key = item.slice(2);
      const value = argv[i + 1];
      if (!value || value.startsWith("--")) throw new Error(`${item} 缺少值`);
      options[key] = value;
      i += 1;
    } else throw new Error(`无法识别的参数：${item}`);
  }
  return options;
}

function summarize(records) {
  if (!Array.isArray(records)) throw new Error("输入必须是JSON数组");
  const groups = new Map();
  for (const record of records) {
    if (!record || typeof record !== "object") continue;
    const era = String(record.era || "未指定");
    const group = groups.get(era) ?? { era, questions: 0, observations: 0, understandings: 0, topics: new Map() };
    if (String(record.question || "").trim()) group.questions += 1;
    if (String(record.observation || "").trim()) group.observations += 1;
    if (String(record.understanding || "").trim()) group.understandings += 1;
    const topic = String(record.question || "").trim();
    if (topic) group.topics.set(topic, (group.topics.get(topic) || 0) + 1);
    groups.set(era, group);
  }
  const eras = [...groups.values()].map((group) => ({
    era: group.era,
    questions: group.questions,
    observations: group.observations,
    understandings: group.understandings,
    topQuestions: [...group.topics.entries()].sort((a, b) => b[1] - a[1]).slice(0, 3).map(([question, count]) => ({ question, count })),
  }));
  eras.sort((a, b) => b.questions - a.questions);
  return {
    totalRecords: records.length,
    coveredEras: eras.map((item) => item.era),
    mostInterestedEra: eras[0]?.era || null,
    eras,
    teachingSuggestions: eras.length
      ? [`优先回应${eras[0].era}的高频问题，再用图片或地形示意图进行证据解释。`, "下一次研学让学生把观察记录与时代背景连接起来。"]
      : ["先补充学生的时代、问题和观察记录，再生成班级小结。"],
  };
}

function toMarkdown(summary) {
  const lines = ["# 班级研学学情小结", "", `记录条数：${summary.totalRecords}`, `最感兴趣时代：${summary.mostInterestedEra || "暂无数据"}`, "", "## 分时代概览"];
  for (const item of summary.eras) {
    lines.push(`- ${item.era}：提问${item.questions}条，观察${item.observations}条，理解记录${item.understandings}条`);
    if (item.topQuestions.length) lines.push(`  - 高频问题：${item.topQuestions.map((q) => `${q.question}（${q.count}次）`).join("、")}`);
  }
  lines.push("", "## 教学建议", ...summary.teachingSuggestions.map((item) => `- ${item}`));
  return lines.join("\n");
}

try {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    console.log("node scripts/summarize-learning-records.mjs --input records.json --format markdown");
    process.exit(0);
  }
  if (!options.input) throw new Error("请提供 --input records.json");
  const records = JSON.parse(fs.readFileSync(options.input, "utf8"));
  const summary = summarize(records);
  console.log(options.format === "markdown" ? toMarkdown(summary) : JSON.stringify(summary, null, 2));
} catch (error) {
  console.error(`生成失败：${error.message}`);
  process.exit(1);
}

