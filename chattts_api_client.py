#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调用本地 ChatTTS 服务 /tts API，批量生成并合并音频。

需要先把本目录下的 .env.example 复制为 .env，并启动服务：
    _run_app_py.bat
或  call venv\Scripts\activate.bat && python app.py

默认使用 speaker/3798.csv 对应的音色（voice=3798）。
"""
import json
import os
import re
import sys
import time
import wave
from pathlib import Path

import requests

BASE_URL = os.getenv("CHATTTS_BASE_URL", "http://127.0.0.1:9966")
SPEAKER_DIR = Path(__file__).resolve().parent / "speaker"
OUT_DIR = Path(__file__).resolve().parent / "output"

# 默认参数对应 workbench 中卷卷姐音色 3798
BASE_DATA = {
    "prompt": "[break_3]",
    "voice": os.getenv("CHATTTS_VOICE", "3798"),
    "temperature": float(os.getenv("CHATTTS_TEMPERATURE", "0.00001")),
    "top_p": float(os.getenv("CHATTTS_TOP_P", "0.6")),
    "top_k": int(os.getenv("CHATTTS_TOP_K", "20")),
    "refine_max_new_token": 384,
    "infer_max_new_token": 2048,
    "skip_refine": 0,
    "is_split": 1,
}


def split_text(text: str, max_len: int = 140):
    """按句子边界切分文本，每段不超过 max_len 字。"""
    sentences = re.split(r"([。！？\n]+)", text.strip())
    chunks = []
    current = ""
    for i in range(0, len(sentences), 2):
        s = sentences[i]
        sep = sentences[i + 1] if i + 1 < len(sentences) else ""
        fragment = s + sep
        if not fragment.strip():
            continue
        if len(current) + len(fragment) > max_len and current:
            chunks.append(current.strip())
            current = fragment
        else:
            current += fragment
    if current.strip():
        chunks.append(current.strip())
    return chunks


def generate(text: str):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    chunks = split_text(text)
    print(f"[INFO] 文本已切分为 {len(chunks)} 段")
    files = []
    for idx, chunk in enumerate(chunks, 1):
        print(f"[INFO] 正在生成第 {idx}/{len(chunks)} 段音频...")
        data = {**BASE_DATA, "text": chunk}
        resp = requests.post(f"{BASE_URL}/tts", data=data, timeout=3600)
        resp.raise_for_status()
        result = resp.json()
        if result.get("code") != 0:
            raise RuntimeError(f"TTS API 错误: {result.get('msg')}")
        for af in result.get("audio_files", []):
            url = af["url"]
            if url.startswith("/"):
                url = BASE_URL + url
            audio_resp = requests.get(url, timeout=60)
            audio_resp.raise_for_status()
            ts = time.strftime("%H%M%S")
            filename = f"{ts}_chunk{idx}_voice{BASE_DATA['voice']}_textlen{len(chunk)}.wav"
            out_path = OUT_DIR / filename
            out_path.write_bytes(audio_resp.content)
            files.append(str(out_path))
            print(f"[OK] {out_path} ({len(audio_resp.content)} bytes, {af.get('audio_duration', 0):.2f}s)")
    return files


def merge_wavs(wav_paths: list, out_path: Path):
    """将多个 wav 文件合并，中间插入 0.5 秒静音。"""
    if not wav_paths:
        return
    params = None
    frames = []
    for p in wav_paths:
        with wave.open(p, "rb") as wf:
            if params is None:
                params = wf.getparams()
            frames.append(wf.readframes(wf.getnframes()))
            silence = bytes(params.nchannels * params.sampwidth * int(params.framerate * 0.5))
            frames.append(silence)
    frames = frames[:-1]
    with wave.open(str(out_path), "wb") as wf:
        wf.setparams(params)
        for f in frames:
            wf.writeframes(f)
    print(f"[OK] 合并音频: {out_path}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        text = sys.argv[1]
    else:
        text = sys.stdin.read()
    if not text.strip():
        print("[ERROR] 请输入文本，例如：python chattts_api_client.py '你好，这是测试。'")
        sys.exit(1)
    files = generate(text)
    if len(files) > 1:
        merged = OUT_DIR / f"merged_{time.strftime('%Y-%m-%d-%H%M%S')}_voice{BASE_DATA['voice']}.wav"
        merge_wavs(files, merged)
    else:
        print(f"[INFO] 生成的音频: {files[0] if files else '无'}")
