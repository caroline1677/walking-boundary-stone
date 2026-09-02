#!/usr/bin/env python3
"""Serve the site and proxy Fish Audio TTS without exposing the API key."""

from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
import uuid
import redis
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"
CACHE_DIR = ROOT / "assets" / "audio" / "cache"
LAYOUT_FILE = ROOT / "data" / "friendship-pass-layout.json"
WHISPER_DIR = str(Path(__file__).parent / "tools" / "whisper-model-small")
WHISPER_PROMPT = "小朋友和界碑爷爷在友谊关的对话。守卫边境，界碑爷爷，文化交流。"
STT_FIXES = {"有一关": "友谊关", "一流关": "友谊关", "尤谊关": "友谊关", "畀碑": "界碑", "碑爷爷": "界碑爷爷"}

_whisper_model = None


def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        _whisper_model = WhisperModel(WHISPER_DIR, device="cpu", compute_type="int8")
    return _whisper_model


def transcribe_audio(audio_bytes: bytes, suffix: str = ".webm") -> str:
    import tempfile
    model = get_whisper_model()
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    try:
        tmp.write(audio_bytes)
        tmp.close()
        segments, _info = model.transcribe(tmp.name, language="zh", initial_prompt=WHISPER_PROMPT)
        return "".join(seg.text for seg in segments).strip()
    finally:
        Path(tmp.name).unlink(missing_ok=True)
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
chat_redis = redis.Redis.from_url(REDIS_URL, decode_responses=True, protocol=2)


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file(ENV_FILE)

# 大陆服务器直连 api.fish.audio 被墙时可经 Cloudflare Worker 中转：
# FISH_TTS_URL 指向 Worker 地址，FISH_PROXY_TOKEN 与 Worker 的 PROXY_TOKEN 配对
FISH_TTS_URL = (os.environ.get("FISH_TTS_URL") or "https://api.fish.audio/v1/tts").strip()
FISH_PROXY_TOKEN = os.environ.get("FISH_PROXY_TOKEN", "").strip()


class SiteHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/layout":
            try:
                payload = json.loads(LAYOUT_FILE.read_text(encoding="utf-8"))
                self.send_json({"ok": True, "layout": payload})
            except (OSError, json.JSONDecodeError) as exc:
                self.send_json({"ok": False, "error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        if self.path == "/api/health":
            self.send_json(
                {
                    "ok": True,
                    "fishConfigured": bool(os.environ.get("FISH_API_KEY")),
                    "model": os.environ.get("FISH_TTS_MODEL", "s2.1-pro-free"),
                }
            )
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/api/layout":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > 65_536:
                    raise ValueError("布局配置长度不正确")
                layout = json.loads(self.rfile.read(length).decode("utf-8"))
                validate_layout(layout)
                temp_path = LAYOUT_FILE.with_suffix(".tmp")
                temp_path.write_text(
                    json.dumps(layout, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                temp_path.replace(LAYOUT_FILE)
                self.send_json({"ok": True})
            except (ValueError, json.JSONDecodeError) as exc:
                self.send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
            except OSError as exc:
                self.send_json({"ok": False, "error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        if self.path == "/api/chat":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                prompt = str(body.get("prompt", "")).strip()
                era = str(body.get("era", "当代")).strip()
                if not prompt:
                    raise ValueError("缺少问题文本")
                session_id = self.get_session_id()
                history = load_history(session_id)
                context = "\n".join(f"{m['role']}: {m['content']}" for m in history[-20:])
                coze_prompt = f"你是界碑研学讲解员。当前页面朝代是【{era}】。回答必须优先依据这个朝代的历史背景，不要把其他朝代的事件当作当前朝代事实。参考以下历史保持上下文，但只回答用户最后一个问题，不要复述历史问题或历史答案：\n{context}\n用户：{prompt}" if context else f"你是界碑研学讲解员。当前页面朝代是【{era}】。请只依据这个朝代的历史背景回答，不要混淆其他朝代。用户问题：{prompt}"
                answer = ask_coze(coze_prompt)
                print(f"[chat] answer={len(answer)}ch session={session_id[:8]}", flush=True)
                history.extend([{"role": "user", "content": prompt}, {"role": "assistant", "content": answer}])
                save_history(session_id, history)
                self.send_json({"ok": True, "answer": answer, "sessionId": session_id, "history": history[-200:]}, session_id=session_id)
            except ValueError as exc:
                self.send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
            except RuntimeError as exc:
                self.send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_GATEWAY)
            return
        if self.path == "/api/stt":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > 8 * 1024 * 1024:
                    raise ValueError("录音数据为空或过大")
                audio_bytes = self.rfile.read(length)
                content_type = self.headers.get("Content-Type") or ""
                suffix = ".mp3" if "mpeg" in content_type else ".webm"
                text = transcribe_audio(audio_bytes, suffix=suffix)
                for wrong, right in STT_FIXES.items():
                    if wrong in text and right not in text:
                        text = text.replace(wrong, right)
                print(f"[stt] text={len(text)}ch -> {text[:40]}", flush=True)
                self.send_json({"ok": True, "text": text})
            except ValueError as exc:
                self.send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
            except Exception as exc:
                print(f"[stt] failed: {exc}", flush=True)
                self.send_json({"ok": False, "error": f"语音识别失败：{exc}"}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        if self.path == "/api/client-log":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > 16_384:
                    raise ValueError("日志内容长度不正确")
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                print(f"[client-log] {json.dumps(payload, ensure_ascii=False)}", flush=True)
                self.send_json({"ok": True})
            except (ValueError, json.JSONDecodeError) as exc:
                self.send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        if self.path != "/api/tts":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 16_384:
                raise ValueError("请求内容长度不正确")
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            text = str(body.get("text", "")).strip()
            if not text:
                raise ValueError("缺少朗读文本")
            if len(text) > 500:
                raise ValueError("单次朗读不能超过 500 个字符")
            audio_url = synthesize_and_cache(text)
            self.send_json({"ok": True, "audioUrl": audio_url})
        except ValueError as exc:
            self.send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except RuntimeError as exc:
            self.send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_GATEWAY)

    def get_session_id(self) -> str:
        cookie = self.headers.get("Cookie", "")
        for item in cookie.split(";"):
            if item.strip().startswith("QCH_SESSION_ID="):
                return item.split("=", 1)[1].strip()
        return uuid.uuid4().hex

    def send_json(self, payload: dict[str, object], status: HTTPStatus = HTTPStatus.OK, session_id: str | None = None) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        if session_id:
            self.send_header("Set-Cookie", f"QCH_SESSION_ID={session_id}; Path=/; SameSite=Lax")
        self.end_headers()
        self.wfile.write(encoded)


def load_history(session_id: str) -> list[dict[str, str]]:
    try:
        raw = chat_redis.get(f"qch:chat:{session_id}")
        return json.loads(raw) if raw else []
    except (redis.RedisError, json.JSONDecodeError):
        return []


def validate_layout(layout: object) -> None:
    if not isinstance(layout, dict):
        raise ValueError("布局必须是对象")
    points = layout.get("points")
    if not isinstance(points, dict):
        raise ValueError("布局缺少 points")
    required = {"spawn", "grandpa", "gate", "boundary", "terrain"}
    if not required.issubset(points):
        raise ValueError("布局缺少必要研学点")
    for point in points.values():
        if not isinstance(point, dict) or not all(
            isinstance(point.get(axis), (int, float)) for axis in ("x", "y", "z")
        ):
            raise ValueError("布局坐标格式不正确")
    discoveries = layout.get("discoveries", [])
    if not isinstance(discoveries, list) or len(discoveries) > 32:
        raise ValueError("自由发现点格式不正确")
    for item in discoveries:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise ValueError("自由发现点缺少 id")
        position = item.get("position")
        if not isinstance(position, dict) or not all(
            isinstance(position.get(axis), (int, float)) for axis in ("x", "y", "z")
        ):
            raise ValueError("自由发现点坐标格式不正确")


def save_history(session_id: str, history: list[dict[str, str]]) -> None:
    try:
        chat_redis.setex(f"qch:chat:{session_id}", 30 * 24 * 3600, json.dumps(history[-200:], ensure_ascii=False))
    except redis.RedisError as exc:
        raise RuntimeError(f"Redis 保存会话失败：{exc}") from exc


def synthesize_and_cache(text: str) -> str:
    api_key = os.environ.get("FISH_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("服务器尚未配置 FISH_API_KEY")

    model = os.environ.get("FISH_TTS_MODEL", "s2.1-pro-free").strip()
    voice_id = os.environ.get(
        "FISH_VOICE_ID", "f4eb5b3708f14d7cb510dd5f74c350cc"
    ).strip()
    delivery_text = text if text.startswith("[") else f"[温和而沉稳地] {text}"
    cache_key = hashlib.sha256(
        f"{model}\0{voice_id}\0{delivery_text}".encode("utf-8")
    ).hexdigest()[:24]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    output_path = CACHE_DIR / f"{cache_key}.mp3"
    if output_path.exists() and output_path.stat().st_size > 1024:
        return f"/assets/audio/cache/{output_path.name}"

    payload = {
        "text": delivery_text,
        "reference_id": voice_id,
        "format": "mp3",
        "sample_rate": 44100,
        "mp3_bitrate": 128,
        "temperature": 0.8,
        "top_p": 0.8,
        "prosody": {"speed": 0.92, "volume": 0, "normalize_loudness": True},
        "normalize": True,
        "latency": "normal",
        "chunk_length": 200,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "model": model,
        # CF 的 Bot 作战模式会拦截 Python-urllib 之类的程序 UA，用浏览器 UA 过边缘
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    }
    if FISH_PROXY_TOKEN:
        headers["X-Proxy-Token"] = FISH_PROXY_TOKEN
    request = urllib.request.Request(
        FISH_TTS_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers=headers,
    )
    temp_path = output_path.with_suffix(".tmp")
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            audio = response.read()
        if len(audio) < 1024:
            raise RuntimeError("Fish Audio 返回的音频内容无效")
        temp_path.write_bytes(audio)
        temp_path.replace(output_path)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"Fish Audio 请求失败（HTTP {exc.code}）：{detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"无法连接 Fish Audio：{exc.reason}") from exc
    finally:
        temp_path.unlink(missing_ok=True)
    return f"/assets/audio/cache/{output_path.name}"


def ask_coze(prompt: str) -> str:
    token = os.environ.get("COZE_API_TOKEN", "").strip()
    if not token:
        raise RuntimeError("服务器尚未配置 COZE_API_TOKEN")
    coze_run_url = os.environ.get("COZE_RUN_URL", "").strip()
    if not coze_run_url:
        raise RuntimeError("服务器尚未配置 COZE_RUN_URL")
    payload = {
        "content": {"query": {"prompt": [{"type": "text", "content": {"text": prompt}}]}},
        "type": "query",
        "session_id": os.environ.get("COZE_SESSION_ID", ""),
        "project_id": int(os.environ.get("COZE_PROJECT_ID", "0")),
    }
    request = urllib.request.Request(
        coze_run_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except (urllib.error.HTTPError, urllib.error.URLError) as exc:
        raise RuntimeError(f"Coze 请求失败：{exc}") from exc
    texts = []
    for line in raw.splitlines():
        if line.startswith("data:"):
            line = line[5:].strip()
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        candidates = []
        if isinstance(item, dict):
            candidates.extend(item.get(key) for key in ("text", "answer"))
            nested = item.get("content")
            if isinstance(nested, dict):
                candidates.extend(nested.get(key) for key in ("text", "answer"))
            elif isinstance(nested, str):
                candidates.append(nested)
        for value in candidates:
            if isinstance(value, str) and value.strip():
                texts.append(value)
                break
    answer = "".join(texts).strip()
    if not answer:
        raise RuntimeError("Coze 未返回可识别的文本答案")
    return answer


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    server = ThreadingHTTPServer((host, 8765), SiteHandler)
    print(f"界碑智能体：http://{host}:8765/")
    server.serve_forever()
