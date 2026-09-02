# 行走的界碑｜友谊关边关研学智能体

这是一个面向友谊关历史研学的本地网页体验。用户可以选择历史时期，阅读“界碑”的第一人称讲述、播放语音、查看史料图片，并进入可拖拽缩放的 3D 边关漫游场景。

## 功能概览

- **历史讲解首页**：`index.html` + `app.js` + `styles.css`
  - 汉、明、清、现代四个时期切换。
  - 同步更新年代、碑文、故事、史料图片和研学进度。
  - 支持预置 MP3、Fish Audio 在线合成、浏览器语音三种讲述方式。
  - 支持预设问题和输入问题；当前问答内容由前端内置规则生成，不连接大模型。
- **3D 边关漫游**：`world.html` + `world.js` + `world.css`
  - 在友谊关、边境哨所等场景之间切换。
  - 鼠标或触摸拖拽平移，滚轮或双指缩放。
  - 点击场景中的智能体打开对话面板；对话为前端内置内容。
- **本地语音服务**：`server.py`
  - 提供静态文件服务。
  - `GET /api/health` 检查服务状态和 Fish Audio 配置。
  - `POST /api/tts` 调用 Fish Audio 生成 MP3，并按文本、模型和音色缓存。

## 目录结构

```text
界碑智能体/
├── index.html                 # 首页
├── app.js                     # 首页时期切换、问答和语音逻辑
├── styles.css                 # 首页样式
├── world.html                 # 3D 漫游页
├── world.js                   # 漫游交互和场景智能体
├── world.css                  # 漫游页样式
├── server.py                  # 本地静态服务器和 Fish Audio 代理
├── generate-local-voice.ps1   # 本地语音生成辅助脚本
├── assets/
│   ├── *.jpg, *.png           # 场景和史料图片
│   ├── audio/*.mp3            # 预置讲解音频
│   └── audio/cache/           # Fish Audio 生成缓存（不纳入版本控制）
├── .env                       # 本地密钥配置，不应提交
└── .gitignore
```

## 启动方式

### 仅查看网页

可以直接打开 `index.html`，但浏览器可能限制本地文件的 API 请求和部分资源加载。推荐使用下面的本地服务器方式。

### 使用 Python 本地服务

在本目录执行：

```powershell
python server.py
```

然后访问：<http://127.0.0.1:8765/>

3D 漫游页也可以直接访问：<http://127.0.0.1:8765/world.html>

服务监听地址固定为 `127.0.0.1:8765`，只供本机访问。

## Fish Audio 配置

在 `界碑智能体/.env` 中配置以下变量：

```dotenv
FISH_API_KEY=你的 Fish Audio API Key
FISH_TTS_MODEL=s2.1-pro-free
FISH_VOICE_ID=f4eb5b3708f14d7cb510dd5f74c350cc
```

不要把真实 API Key 写入 README、前端 JavaScript 或提交到仓库。服务端会从 `.env` 读取密钥，浏览器只请求本地的 `/api/tts`。

### 语音回退顺序

1. 选择时期的预置 MP3 存在时，优先播放 `assets/audio/*.mp3`。
2. 需要动态朗读时，前端请求 `/api/tts`，由 `server.py` 调用 Fish Audio。
3. Fish Audio 未配置或请求失败时，回退到浏览器 `speechSynthesis`。

Fish Audio 生成的文件会写入 `assets/audio/cache/`，相同文本和配置会复用缓存。缓存目录已在 `.gitignore` 中排除。

## 接口

### `GET /api/health`

返回服务是否运行、是否配置 Fish Audio，以及当前模型，例如：

```json
{"ok": true, "fishConfigured": false, "model": "s2.1-pro-free"}
```

### `POST /api/tts`

请求体：

```json
{"text": "请介绍友谊关的历史。"}
```

文本不能为空，单次最多 500 个字符；成功时返回缓存音频的相对 URL。

## 基础检查

启动服务后可执行：

```powershell
Invoke-WebRequest http://127.0.0.1:8765/api/health
python -m py_compile server.py
```

项目当前没有自动化测试或依赖清单；前端为原生 HTML、CSS 和 JavaScript，不需要安装 npm 依赖。若修改了前端逻辑，建议在浏览器中检查：时期切换、播放按钮、静音按钮、问题提交、3D 拖拽缩放和移动端布局。

## 注意事项

- 这是本地展示型项目，首页问答和 3D 智能体对话目前是静态规则，不是实时 AI 对话。
- `server.py` 使用 `ThreadingHTTPServer`，语音请求会访问外部 Fish Audio 服务；没有网络或 API Key 时应使用本地音频或浏览器语音回退。
- 修改 `server.py` 后应重新启动服务；修改前端静态文件后刷新浏览器即可。
- 项目根目录还包含证书压缩包、友谊关材料和图片资料，它们是素材归档，不属于网页运行必需文件。
