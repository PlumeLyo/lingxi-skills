#!/usr/bin/env python3
"""
image_gen.py — 统一图像生成脚本
支持 OpenRouter / 阿里云百炼(DashScope) / 火山方舟(ARK) / Google Gemini 直连
内置 API Key 加密管理：密文存 WPS 笔记，解密密钥由设备特征现场派生，本机无需存储任何额外文件

依赖：pip install httpx cryptography

用法示例
--------

━━━ OpenRouter（需代理；文生图 + 图生图均支持，本地文件垫图）━━━

# 文生图
python image_gen.py \
    --provider openrouter \
    --model "google/gemini-3.1-flash-image-preview" \
    --key "sk-or-xxx" \
    --prompt "A nano banana dish in a fancy restaurant, cinematic lighting" \
    --proxy http://127.0.0.1:7890 \
    --aspect 16:9 --size 4K

# 图生图 — 垫本地文件（支持 jpg/png/webp/gif）
python image_gen.py \
    --provider openrouter \
    --model "google/gemini-3.1-flash-image-preview" \
    --key "sk-or-xxx" \
    --prompt "Change the background to a snowy mountain" \
    --image ./reference.jpg \
    --proxy http://127.0.0.1:7890 \
    --aspect 1:1

━━━ 阿里云百炼（国内直连；仅文生图，不支持垫图）━━━

# 文生图
python image_gen.py \
    --provider dashscope \
    --model "qwen-image-2.0-pro" \
    --key "sk-xxx" \
    --prompt "冬日北京胡同街景，水彩风格，暖色调" \
    --aspect 4:3

━━━ 即梦 AI（火山方舟，国内直连；文生图 + 图生图，垫图须为公网 URL）━━━

# 文生图
python image_gen.py \
    --provider ark \
    --model "doubao-seedream-5-0-260128" \
    --key "env:ARK_API_KEY" \
    --prompt "生成狗狗趴在草地上的近景，写实风格" \
    --size 2K

# 图生图 — 垫公网 URL（本地文件不支持）
python image_gen.py \
    --provider ark \
    --model "doubao-seedream-5-0-260128" \
    --key "sk-xxx" \
    --prompt "将背景替换为星空，保持主体不变" \
    --image "https://example.com/ref.png" \
    --size 2K

━━━ Google Gemini 直连（需代理；文生图 + 图生图，本地文件垫图）━━━

# 文生图
python image_gen.py \
    --provider gemini \
    --model "gemini-3-pro-image-preview" \
    --key "env:GEMINI_API_KEY" \
    --prompt "A futuristic city at dusk, ultra-detailed" \
    --proxy http://127.0.0.1:7890 \
    --aspect 16:9 --size 4K

# 图生图 — 垫本地文件（支持 jpg/png/webp/gif；imageSize 必须大写 K）
python image_gen.py \
    --provider gemini \
    --model "gemini-3-pro-image-preview" \
    --key "sk-xxx" \
    --prompt "Add a wizard hat on the cat" \
    --image ./cat.jpg \
    --proxy http://127.0.0.1:7890 \
    --aspect 1:1 --size 2K

━━━ note 模式 — 从 WPS 笔记读取加密 Key（任意 provider 均可）━━━

# 先加密 Key，输出密文（由 AI 存入 WPS 笔记）
python image_gen.py encrypt-key \
    --note-id "NOTE_ID_HERE" \
    --provider openrouter \
    --key "sk-or-xxx"

# 生图时传入笔记 ID + 密文，脚本自动派生密钥解密
python image_gen.py \
    --provider openrouter \
    --model "google/gemini-3.1-flash-image-preview" \
    --key "note:NOTE_ID_HERE" \
    --ciphertext "BASE64_CIPHERTEXT==" \
    --prompt "A nano banana dish" \
    --proxy http://127.0.0.1:7890

Key 管理
--------
  --key 支持三种写法：
    直接传字符串 : --key "sk-or-xxx"
    读环境变量   : --key "env:OPENROUTER_API_KEY"
    从笔记解密   : --key "note:NOTE_ID" --ciphertext "BASE64=="

  note 模式原理：
    加密密钥 = SHA256(设备ID + note_id[:16] + provider) 现场派生
    密文存 WPS 笔记，本机无需存储任何额外文件
    同一台设备 + 同一笔记 + 同一 provider → 密钥唯一稳定

Key 获取地址
--------
  OpenRouter : https://openrouter.ai/workspaces/default/keys
  阿里云百炼  : https://bailian.console.aliyun.com/cn-beijing?tab=model#/api-key
  火山方舟(即梦) : https://console.volcengine.com/ark/
  Google      : https://aistudio.google.com/app/api-keys

各 Provider 能力对比
--------
  provider    文生图  图生图  垫图格式            国内直连  代理
  openrouter  ✓      ✓      本地文件(jpg/png)    ✗        需要
  dashscope   ✓      ✗      不支持               ✓        不需要
  ark（即梦）         ✓      ✓      公网 URL             ✓        不需要（即梦 AI）
  gemini      ✓      ✓      本地文件(jpg/png)    ✗        需要

注意事项
--------
  - 百炼接口不支持垫图，传 --image 会被忽略并警告
  - 火山方舟垫图须公网 URL，传本地路径会被忽略并警告
  - Google imageSize 必须大写 K（1K / 2K / 4K），小写会自动转换并警告
  - openrouter / gemini 国内访问需要 --proxy
  - 生成图片存入 --out 目录，文件名含时间戳防覆盖
"""

import argparse
import base64
import hashlib
import json
import os
import platform
import re
import struct
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import Optional
from urllib.request import urlretrieve

try:
    import httpx
except ImportError:
    print("[error] 缺少依赖：请先执行 pip install httpx cryptography", file=sys.stderr)
    sys.exit(1)

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding as sym_padding
except ImportError:
    print("[error] 缺少依赖：请先执行 pip install cryptography", file=sys.stderr)
    sys.exit(1)


# ──────────────────────────────────────────────
# 设备 ID
# ──────────────────────────────────────────────

def get_device_id() -> str:
    """获取稳定的硬件设备 UUID，跨平台实现。"""
    system = platform.system()
    try:
        if system == "Darwin":
            out = subprocess.check_output(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                stderr=subprocess.DEVNULL
            ).decode()
            for line in out.splitlines():
                if "IOPlatformUUID" in line:
                    return line.split('"')[-2]
        elif system == "Windows":
            out = subprocess.check_output(
                ["wmic", "csproduct", "get", "uuid"],
                stderr=subprocess.DEVNULL
            ).decode()
            lines = [l.strip() for l in out.splitlines()
                     if l.strip() and l.strip().upper() != "UUID"]
            if lines:
                return lines[0]
        else:
            mid = Path("/etc/machine-id")
            if mid.exists():
                return mid.read_text().strip()
    except Exception:
        pass
    fallback = f"{platform.node()}-{os.getlogin()}"
    return hashlib.sha256(fallback.encode()).hexdigest()


# ──────────────────────────────────────────────
# Key 加密 / 解密（AES-256-CBC，Fernet-like 简化版）
# ──────────────────────────────────────────────

def _derive_key(note_id: str, provider: str) -> bytes:
    """
    派生 32 字节 AES 密钥。
    材料：设备ID + note_id[:16] + provider
    本机无需存储任何额外文件，同设备同账号稳定可重现。
    """
    device = get_device_id()
    material = f"{device}|{note_id[:16]}|{provider}".encode()
    return hashlib.sha256(material).digest()  # 32 bytes → AES-256


def encrypt_api_key(api_key: str, note_id: str, provider: str) -> str:
    """
    用派生密钥加密 API Key，返回 base64 密文（IV 前缀 + 密文）。
    密文较短，适合存入笔记表格。
    """
    key = _derive_key(note_id, provider)
    iv = os.urandom(16)
    padder = sym_padding.PKCS7(128).padder()
    padded = padder.update(api_key.encode()) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    enc = cipher.encryptor()
    ciphertext = enc.update(padded) + enc.finalize()
    return base64.b64encode(iv + ciphertext).decode()


def decrypt_api_key(ciphertext_b64: str, note_id: str, provider: str) -> str:
    """用派生密钥解密，返回原始 API Key。"""
    key = _derive_key(note_id, provider)
    raw = base64.b64decode(ciphertext_b64)
    iv, ct = raw[:16], raw[16:]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    dec = cipher.decryptor()
    padded = dec.update(ct) + dec.finalize()
    unpadder = sym_padding.PKCS7(128).unpadder()
    return (unpadder.update(padded) + unpadder.finalize()).decode()


# ──────────────────────────────────────────────
# Key 解析（支持三种 --key 格式）
# ──────────────────────────────────────────────

def resolve_api_key(key_arg: str, provider: str,
                    ciphertext: Optional[str], note_id: Optional[str]) -> str:
    """
    解析 --key 参数，返回真实 API Key。
    支持：直接字符串 / env:变量名 / note:NOTE_ID
    """
    if key_arg.startswith("env:"):
        var = key_arg[4:].strip()
        val = os.environ.get(var, "")
        if not val:
            raise ValueError(f"环境变量 {var} 未设置，请先 export {var}=your_key")
        return val

    if key_arg.startswith("note:"):
        nid = key_arg[5:].strip() or note_id
        if not nid:
            raise ValueError("note 模式须通过 --key 'note:NOTE_ID' 或 --note-id 传入笔记 ID")
        if not ciphertext:
            raise ValueError("note 模式须同时传入 --ciphertext（从 Key 管理笔记中读取）")
        try:
            return decrypt_api_key(ciphertext, nid, provider)
        except Exception as e:
            raise ValueError(
                f"解密失败（设备或笔记 ID 不匹配）：{e}\n"
                "如果换了设备或笔记，请重新执行 encrypt-key 子命令并更新笔记中的密文。"
            )

    return key_arg  # 直接字符串


# ──────────────────────────────────────────────
# 图片工具函数
# ──────────────────────────────────────────────

def _load_image_b64(path: str) -> "tuple[str, str]":
    if not os.path.isfile(path):
        raise FileNotFoundError(f"垫图文件不存在：{path}")
    suffix = Path(path).suffix.lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".png": "image/png", ".webp": "image/webp", ".gif": "image/gif"}
    mime = mime_map.get(suffix, "image/jpeg")
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode(), mime


def _save_images(images: "list[str]", out_dir: str, prefix: str = "image") -> "list[str]":
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    saved = []
    for i, url in enumerate(images):
        ts = int(time.time() * 1000)
        fname_base = f"{prefix}_{ts}_{i + 1}"
        try:
            if url.startswith("data:"):
                m = re.match(r"data:([^;]+);base64,(.+)", url, re.DOTALL)
                if not m:
                    print(f"[warn] 第 {i+1} 张：无法解析 data URL，跳过", file=sys.stderr)
                    continue
                ext = m.group(1).split("/")[-1].replace("jpeg", "jpg")
                raw = base64.b64decode(m.group(2))
                out_path = os.path.join(out_dir, f"{fname_base}.{ext}")
                with open(out_path, "wb") as f:
                    f.write(raw)
            else:
                ext = url.split("?")[0].rsplit(".", 1)[-1] or "png"
                out_path = os.path.join(out_dir, f"{fname_base}.{ext}")
                urlretrieve(url, out_path)
        except Exception as e:
            print(f"[warn] 第 {i+1} 张保存失败：{e}", file=sys.stderr)
            continue
        print(f"[saved] {out_path}")
        saved.append(out_path)
    return saved


# ──────────────────────────────────────────────
# Provider 实现
# ──────────────────────────────────────────────

def _pure_image_model(model: str) -> bool:
    pure_prefixes = (
        "bytedance-seed/", "black-forest-labs/", "sourceful/",
        "stability-ai/", "ideogram-ai/", "recraft-ai/",
    )
    return any(model.startswith(p) for p in pure_prefixes)


def call_openrouter(model, key, prompt, image_path, proxy, aspect, size):
    """
    OpenRouter /api/v1/chat/completions
    图像返回位置：choices[0].message.images[].image_url.url（base64 data URL）
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://xsctbench.com",
        "X-Title": "XSCT Bench",
    }
    if image_path:
        b64, mime = _load_image_b64(image_path)
        content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
        ]
    else:
        content = prompt

    modalities = ["image"] if _pure_image_model(model) else ["image", "text"]
    image_config = {}
    if aspect:
        image_config["aspect_ratio"] = aspect
    if size:
        image_config["image_size"] = size

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "modalities": modalities,
    }
    if image_config:
        payload["image_config"] = image_config

    proxies = {"http://": proxy, "https://": proxy} if proxy else None
    with httpx.Client(timeout=180, proxies=proxies) as client:
        resp = client.post(url, headers=headers, json=payload)
        _raise_for_status(resp, "OpenRouter")
        data = resp.json()

    images = []
    for choice in data.get("choices", []):
        for img in choice.get("message", {}).get("images", []):
            images.append(img["image_url"]["url"])
    if not images:
        raise RuntimeError(
            f"OpenRouter 响应中未找到图片。finish_reason="
            f"{data.get('choices', [{}])[0].get('finish_reason')} | "
            f"响应片段：{str(data)[:400]}"
        )
    return images


def call_dashscope(model, key, prompt, image_path, proxy, aspect, size):
    """
    阿里云百炼 /api/v1/services/aigc/multimodal-generation/generation
    图像返回位置：output.choices[0].message.content[0].image（OSS URL，24h 有效）
    不支持垫图。
    """
    if image_path:
        print("[warn] 阿里云百炼文生图接口不支持垫图，已忽略 --image 参数", file=sys.stderr)

    ratio_to_size_v2  = {"16:9": "2688*1536", "9:16": "1536*2688",
                         "1:1": "2048*2048",  "4:3": "2368*1728", "3:4": "1728*2368"}
    ratio_to_size_old = {"16:9": "1664*928",  "9:16": "928*1664",
                         "1:1": "1328*1328",  "4:3": "1472*1104", "3:4": "1104*1472"}
    is_v2 = "2.0" in model
    resolved_size = size or (ratio_to_size_v2.get(aspect, "2048*2048") if is_v2
                              else ratio_to_size_old.get(aspect, "1664*928"))

    endpoint = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
    headers  = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload  = {
        "model": model,
        "input": {"messages": [{"role": "user", "content": [{"text": prompt}]}]},
        "parameters": {"size": resolved_size, "prompt_extend": True, "watermark": False},
    }
    with httpx.Client(timeout=180) as client:
        resp = client.post(endpoint, headers=headers, json=payload)
        _raise_for_status(resp, "阿里云百炼")
        data = resp.json()

    if data.get("code"):
        raise RuntimeError(f"百炼接口错误 code={data['code']} | message={data.get('message')}")

    images = []
    for choice in data.get("output", {}).get("choices", []):
        for item in choice.get("message", {}).get("content", []):
            if "image" in item:
                images.append(item["image"])
    if not images:
        raise RuntimeError(f"百炼响应中未找到图片，响应片段：{str(data)[:400]}")
    return images


def call_ark(model, key, prompt, image_path, proxy, aspect, size):
    """
    即梦 AI（火山方舟）/api/v3/images/generations
    垫图须为公网 URL（本地文件无效）。
    图像返回位置：data[].url 或 data[].b64_json
    """
    endpoint = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
    headers  = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload  = {
        "model": model,
        "prompt": prompt,
        "sequential_image_generation": "disabled",
        "response_format": "url",
        "size": size or "2K",
        "stream": False,
        "watermark": False,
    }
    if image_path:
        if image_path.startswith("http"):
            payload["image"] = image_path
        else:
            print(f"[warn] 火山方舟垫图须为公网 URL，本地路径 '{image_path}' 无效，已忽略",
                  file=sys.stderr)

    with httpx.Client(timeout=180) as client:
        resp = client.post(endpoint, headers=headers, json=payload)
        _raise_for_status(resp, "火山方舟")
        data = resp.json()

    if data.get("error"):
        err = data["error"]
        raise RuntimeError(f"火山方舟接口错误 code={err.get('code')} | message={err.get('message')}")

    images = []
    for item in data.get("data", []):
        if item.get("url"):
            images.append(item["url"])
        elif item.get("b64_json"):
            images.append(f"data:image/jpeg;base64,{item['b64_json']}")
    if not images:
        raise RuntimeError(f"火山方舟响应中未找到图片，响应片段：{str(data)[:400]}")
    return images


def call_gemini(model, key, prompt, image_path, proxy, aspect, size):
    """
    Google Gemini /v1beta/models/{model}:generateContent
    imageSize 必须大写 K（1K / 2K / 4K）。
    图像返回位置：candidates[0].content.parts[].inlineData（base64）
    """
    if size and re.fullmatch(r"\d+k", size):
        print(f"[warn] Gemini imageSize '{size}' 含小写 k，已自动转为大写 '{size.upper()}'",
              file=sys.stderr)
        size = size.upper()

    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers  = {"x-goog-api-key": key, "Content-Type": "application/json"}

    parts = [{"text": prompt}]
    if image_path:
        b64, mime = _load_image_b64(image_path)
        parts.append({"inline_data": {"mime_type": mime, "data": b64}})

    image_config = {}
    if aspect:
        image_config["aspectRatio"] = aspect
    if size:
        image_config["imageSize"] = size

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            **({"imageConfig": image_config} if image_config else {}),
        },
    }

    proxies = {"http://": proxy, "https://": proxy} if proxy else None
    with httpx.Client(timeout=180, proxies=proxies) as client:
        resp = client.post(endpoint, headers=headers, json=payload)
        _raise_for_status(resp, "Google Gemini")
        data = resp.json()

    if data.get("error"):
        err = data["error"]
        raise RuntimeError(f"Gemini 接口错误 code={err.get('code')} | message={err.get('message')}")

    for candidate in data.get("candidates", []):
        if candidate.get("finishReason") in ("SAFETY", "OTHER"):
            raise RuntimeError(
                f"Gemini 内容过滤拦截，finishReason={candidate['finishReason']} | "
                f"safetyRatings={candidate.get('safetyRatings')}"
            )

    images = []
    for candidate in data.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            inline = part.get("inlineData") or part.get("inline_data")
            if inline:
                mime = inline.get("mimeType", "image/png")
                images.append(f"data:{mime};base64,{inline['data']}")
    if not images:
        raise RuntimeError(f"Gemini 响应中未找到图片，响应片段：{str(data)[:400]}")
    return images


# ──────────────────────────────────────────────
# 统一 HTTP 错误处理
# ──────────────────────────────────────────────

KEY_URLS = {
    "openrouter": "https://openrouter.ai/workspaces/default/keys",
    "dashscope":  "https://bailian.console.aliyun.com/cn-beijing?tab=model#/api-key",
    "ark":        "https://console.volcengine.com/ark/",  # 即梦 AI（火山方舟）
    "gemini":     "https://aistudio.google.com/app/api-keys",
}

def _raise_for_status(resp: httpx.Response, provider: str) -> None:
    if resp.status_code < 400:
        return
    try:
        body = resp.json()
        detail = body.get("error", {})
        msg = f"code={detail.get('code')} message={detail.get('message')}" \
            if isinstance(detail, dict) else str(detail)[:300]
    except Exception:
        msg = resp.text[:300]

    hint = ""
    if resp.status_code in (401, 403):
        provider_key = {
            "OpenRouter": "openrouter", "阿里云百炼": "dashscope",
            "火山方舟(即梦)": "ark", "Google Gemini": "gemini",
        }.get(provider)
        url = KEY_URLS.get(provider_key, "")
        hint = f"\n         → API Key 无效或无权限，请到此处创建/查看 Key：{url}"

    raise RuntimeError(f"{provider} HTTP {resp.status_code}: {msg}{hint}")


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

PROVIDERS = {
    "openrouter": call_openrouter,
    "dashscope":  call_dashscope,
    "ark":        call_ark,
    "gemini":     call_gemini,
}

EPILOG = """\
provider 说明
  openrouter  OpenRouter 网关，走代理（国内），文生图 + 图生图（本地文件垫图）
              可用模型：google/gemini-3.1-flash-image-preview
  dashscope   阿里云百炼，国内直连，仅文生图，不支持垫图
              可用模型：qwen-image-2.0-pro
  ark         即梦 AI（火山方舟），国内直连，文生图 + 图生图（垫图须为公网 URL）
              可用模型：doubao-seedream-5-0-260128
  gemini      Google 直连，走代理（国内），文生图 + 图生图（本地文件垫图）
              可用模型：gemini-3-pro-image-preview

--key 支持三种写法
  直接传字符串 : --key "sk-or-xxx"
  读环境变量   : --key "env:OPENROUTER_API_KEY"
  从笔记解密   : --key "note:NOTE_ID" --ciphertext "BASE64=="

encrypt-key 子命令
  生成密文，供 AI 存入 WPS 笔记（每次重新加密，旧密文自动失效）
  python image_gen.py encrypt-key --note-id ID --provider openrouter --key "sk-xxx"

Key 安全说明
  note 模式：加密密钥由「设备 ID + 笔记 ID + provider」现场派生，本机无需存储额外文件。
  换设备后密钥不同，需重新执行 encrypt-key 并更新笔记中的密文。
  WPS 笔记不会获取你的 Key 内容，但第三方 MCP 插件可读取笔记，请在信任的 Agent 环境下使用。
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="image_gen.py",
        description="统一图像生成脚本 — OpenRouter / 阿里云百炼 / 火山方舟 / Google Gemini",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EPILOG,
    )
    sub = parser.add_subparsers(dest="subcmd")

    # ── 子命令：encrypt-key ──
    p_enc = sub.add_parser("encrypt-key", help="加密 API Key，输出密文（存入 WPS 笔记）")
    p_enc.add_argument("--note-id",  required=True, help="KEY 管理笔记的 note_id")
    p_enc.add_argument("--provider", required=True, choices=PROVIDERS, help="服务商")
    p_enc.add_argument("--key",      required=True, help="要加密的 API Key")

    # ── 主命令：生图 ──
    req = parser.add_argument_group("必填参数")
    req.add_argument("--provider", choices=PROVIDERS, metavar="PROVIDER",
                     help="服务商：openrouter | dashscope | ark | gemini")
    req.add_argument("--model",  help="模型名称 / ID")
    req.add_argument("--key",
                     help='API Key，支持：直接字符串 / env:变量名 / note:笔记ID')
    req.add_argument("--prompt", help="生图提示词")

    opt = parser.add_argument_group("可选参数")
    opt.add_argument("--ciphertext", default=None,
                     help="note 模式专用：从 Key 管理笔记中读取的 base64 密文")
    opt.add_argument("--note-id",    default=None,
                     help="note 模式专用：Key 管理笔记 ID（也可直接写在 --key 'note:ID' 中）")
    opt.add_argument("--image",  default=None,
                     help="垫图：本地文件路径（openrouter/gemini）或公网 URL（ark）")
    opt.add_argument("--proxy",  default=None,
                     help="HTTP 代理，例如 http://127.0.0.1:7890（openrouter/gemini 国内需要）")
    opt.add_argument("--aspect", default="1:1",
                     help="宽高比，例如 16:9 / 4:3 / 1:1（默认 1:1）")
    opt.add_argument("--size",   default=None,
                     help="分辨率，例如 2K / 4K / 2048*2048")
    opt.add_argument("--out",    default="./output",
                     help="图片输出目录（默认 ./output）")
    opt.add_argument("--verbose", action="store_true", help="打印完整异常堆栈（调试用）")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # ── encrypt-key 子命令 ──
    if args.subcmd == "encrypt-key":
        ct = encrypt_api_key(args.key, args.note_id, args.provider)
        result = {
            "ok": True,
            "ciphertext_b64": ct,
            "note_id": args.note_id,
            "provider": args.provider,
            "device_id_prefix": get_device_id()[:8] + "…",
            "tip": "将 ciphertext_b64 存入 WPS 笔记对应行，下次生图时传入 --ciphertext 即可自动解密",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # ── 生图主流程：参数校验 ──
    missing = [f"--{f}" for f in ("provider", "model", "key", "prompt")
               if not getattr(args, f.replace("-", "_"), None)]
    if missing:
        parser.error(f"生图模式缺少必填参数：{', '.join(missing)}")

    # ── 解析 API Key ──
    try:
        api_key = resolve_api_key(args.key, args.provider, args.ciphertext, args.note_id)
    except ValueError as e:
        print(f"[error] {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[info] provider={args.provider}  model={args.model}")
    print(f"[info] aspect={args.aspect}  size={args.size or '(auto)'}  out={args.out}")
    if args.proxy:
        print(f"[info] proxy={args.proxy}")
    if args.image:
        print(f"[info] 垫图={args.image}")
    print(f"[info] prompt={args.prompt[:80]}{'…' if len(args.prompt) > 80 else ''}")

    key_mode = "note（派生解密）" if args.key.startswith("note:") else \
               "env（环境变量）" if args.key.startswith("env:") else "直接传入"
    print(f"[info] Key 来源：{key_mode}")

    fn = PROVIDERS[args.provider]
    try:
        images = fn(
            model=args.model,
            key=api_key,
            prompt=args.prompt,
            image_path=args.image,
            proxy=args.proxy,
            aspect=args.aspect,
            size=args.size,
        )
    except FileNotFoundError as e:
        print(f"[error] {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"[error] {e}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)
    except httpx.ConnectError as e:
        print(f"[error] 连接失败：{e}", file=sys.stderr)
        if args.proxy:
            print(f"         请确认代理 {args.proxy} 已启动且可用", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)
    except httpx.TimeoutException:
        print("[error] 请求超时（>180s），网络或模型生成时间过长", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[error] 未预期异常 {type(e).__name__}: {e}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)

    print(f"[info] 获取到 {len(images)} 张图片，正在保存…")
    saved = _save_images(images, args.out)

    if not saved:
        print("[error] 所有图片保存均失败，请检查上方警告", file=sys.stderr)
        sys.exit(1)

    print(f"[done] 已保存 {len(saved)} / {len(images)} 张 → {os.path.abspath(args.out)}")


if __name__ == "__main__":
    main()
