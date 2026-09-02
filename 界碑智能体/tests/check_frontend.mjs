/**
 * 前端体检脚本 —— 每次修改 js/html/数据文件后运行：
 *   node tests/check_frontend.mjs
 * 附加 API 冒烟（需服务器已启动）：node tests/check_frontend.mjs --api
 *
 * 覆盖：①全部 JS 语法（ESM 解析级，含重复声明检测——即“改A坏B”事故的根因）
 *      ②import 指向的文件必须存在（防缓存版本号改丢文件）
 *      ③html 引用的本地脚本/样式/图片必须存在
 *      ④数据文件可导入且数量正确；布局 JSON 结构合法
 *      ⑤关键回归项（micButton 唯一声明等）
 * 任一项失败退出码 1。
 */

import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { pathToFileURL, fileURLToPath } from "node:url";

const ROOT = fileURLToPath(new URL("..", import.meta.url));
const TMP = path.join(ROOT, "tests", ".tmp");
fs.mkdirSync(TMP, { recursive: true });

let failures = 0;
const pass = (name) => console.log(`  PASS ${name}`);
const fail = (name, detail = "") => { failures += 1; console.log(`  FAIL ${name} ${detail}`); };

function checkModuleSyntax(file, label = file) {
  const tmp = path.join(TMP, path.basename(file).replace(/[?].*/, "") + ".mjs");
  fs.copyFileSync(file, tmp);
  const r = spawnSync(process.execPath, ["--check", tmp], { timeout: 20000 });
  if (r.status === 0) pass(`语法 ${label}`);
  else fail(`语法 ${label}`, "\n" + String(r.stderr).trim().slice(0, 600));
}

function rel(fromFile, target) {
  return path.resolve(path.dirname(fromFile), target.split("?")[0]);
}

// ---- 1. 全部 JS 语法 + import 目标存在 ----
const jsFiles = ["app.js", ...fs.readdirSync(path.join(ROOT, "js")).filter((f) => f.endsWith(".js")).map((f) => path.join("js", f))];
const importTargets = [];
for (const relPath of jsFiles) {
  const abs = path.join(ROOT, relPath);
  checkModuleSyntax(abs, relPath);
  const src = fs.readFileSync(abs, "utf-8");
  const re = /(?:from|import)\s+["']([^"']+)["']/g;
  let m;
  while ((m = re.exec(src))) {
    const target = m[1];
    if (!target.startsWith(".") && !target.startsWith("/")) continue; // CDN 包跳过
    importTargets.push([relPath, rel(abs, target)]);
  }
}
for (const [fromFile, target] of importTargets) {
  if (fs.existsSync(target)) pass(`引用存在 ${path.basename(fromFile)} → ${path.basename(target)}`);
  else fail(`引用存在 ${path.basename(fromFile)} → ${target}`, "文件不存在");
}

// ---- 2. html 引用的本地资源存在 ----
for (const htmlName of ["index.html", "world.html", "demo.html"]) {
  const htmlPath = path.join(ROOT, htmlName);
  if (!fs.existsSync(htmlPath)) continue;
  const src = fs.readFileSync(htmlPath, "utf-8");
  const re = /(?:src|href)=["']([^"']+)["']/g;
  let m;
  let allOk = true;
  let count = 0;
  while ((m = re.exec(src))) {
    const target = m[1];
    if (/^(https?:|#|mailto:|data:)/.test(target)) continue;
    count += 1;
    const abs = path.resolve(ROOT, target.split("?")[0]);
    if (!fs.existsSync(abs)) { allOk = false; fail(`${htmlName} 资源缺失`, target); }
  }
  if (allOk) pass(`资源完整 ${htmlName}（${count} 项）`);
}

// ---- 3. 数据文件可导入 + 数量断言 ----
const dataChecks = [
  ["data/friendship-pass-discoveries.js", "FRIENDSHIP_PASS_DISCOVERIES", 5],
  ["data/post-discoveries.js", "POST_DISCOVERIES", 6],
  ["data/friendship-pass-quests.js", "STUDY_POINTS", 3],
];
for (const [relPath, exportName, expectedLen] of dataChecks) {
  const tmp = path.join(TMP, path.basename(relPath) + ".mjs");
  fs.copyFileSync(path.join(ROOT, relPath), tmp);
  try {
    const mod = await import(pathToFileURL(tmp).href);
    const value = mod[exportName];
    if (!value) fail(`数据 ${relPath}`, `缺少导出 ${exportName}`);
    else if (value.length !== expectedLen) fail(`数据 ${relPath}`, `${exportName}.length=${value.length}，期望 ${expectedLen}`);
    else pass(`数据 ${relPath} ${exportName}=${value.length}`);
  } catch (err) {
    fail(`数据 ${relPath}`, String(err).slice(0, 200));
  }
}

// ---- 4. 布局 JSON 结构 ----
for (const relPath of ["data/friendship-pass-layout.json", "data/post-layout.json"]) {
  try {
    const json = JSON.parse(fs.readFileSync(path.join(ROOT, relPath), "utf-8"));
    const okPoints = Object.values(json.points).every((p) => [p.x, p.y, p.z].every((n) => Number.isFinite(n)));
    const okDisc = (json.discoveries || []).every((d) => d.id && d.position && Number.isFinite(d.position.x));
    if (okPoints && okDisc && json.version >= 1) pass(`布局 ${relPath} v${json.version}`);
    else fail(`布局 ${relPath}`, "points/discoveries 含非法数值");
  } catch (err) {
    fail(`布局 ${relPath}`, String(err).slice(0, 160));
  }
}

// ---- 5. 回归专项：micButton 唯一声明（防止重复插入事故复发）----
const appSrc = fs.readFileSync(path.join(ROOT, "app.js"), "utf-8");
const micCount = (appSrc.match(/const micButton/g) || []).length;
if (micCount === 1) pass("回归 micButton 唯一声明");
else fail("回归 micButton 唯一声明", `出现 ${micCount} 次`);

// 调试暴露只在 debug 页生效（world.js 在非 debug 时应移除 __player/__camera）
const worldSrc = fs.readFileSync(path.join(ROOT, "js", "world.js"), "utf-8");
if (/has\("debug"\)[\s\S]{0,200}delete window\.__player/.test(worldSrc) || !/window\.__player\s*=/.test(worldSrc)) {
  pass("回归 调试句柄不泄漏到正式页");
} else if (/new URLSearchParams\(location\.search\)\.has\("debug"\)/.test(worldSrc)) {
  fail("回归 调试句柄不泄漏到正式页", "world.js 无条件暴露 __player，请在非 debug 时移除");
} else {
  pass("回归 调试句柄不泄漏到正式页");
}

// ---- 6. API 冒烟（可选：--api）----
if (process.argv.includes("--api")) {
  const base = "http://127.0.0.1:8765";
  const tryFetch = async (p2, opts) => {
    try {
      const r = await fetch(base + p2, { signal: AbortSignal.timeout(8000), ...opts });
      return { status: r.status, json: await r.json().catch(() => null) };
    } catch { return null; }
  };
  const health = await tryFetch("/api/health");
  if (!health) {
    console.log("  SKIP API 冒烟（服务器未启动）");
  } else {
    if (health.json && health.json.ok) pass("API /api/health");
    else fail("API /api/health");
    const layout = await tryFetch("/api/layout");
    if (layout && layout.json && layout.json.ok) pass("API /api/layout");
    else fail("API /api/layout");
    const stt = await tryFetch("/api/stt", { method: "POST", body: Buffer.alloc(64) });
    if (stt && stt.json && stt.json.ok === false) pass("API /api/stt 路由存活（空音频按预期拒绝）");
    else fail("API /api/stt 路由存活");
  }
}

console.log(failures === 0 ? "\n全部检查通过 ✓" : `\n${failures} 项失败 ✗`);
process.exit(failures === 0 ? 0 : 1);
