# ============================================================
#  VoxCPM2 流式 TTS HTTP 服务 - 输入文本，实时播放到音响
# ============================================================
# 启动：python tts_server.py
# 调用：curl -X POST http://localhost:8801/tts -H "Content-Type: application/json" \
#        -d '{"text": "你好世界"}'
#       curl -X POST http://localhost:8801/tts -H "Content-Type: application/json" \
#        -d '{"text": "你好世界", "mode": "clone", "reference_wav": "刘娜录音.wav"}'
# ============================================================

import os
# 在导入任何其他模块前禁用 tqdm 进度条，避免在 FastAPI 线程中写 stderr 出错
os.environ["TQDM_DISABLE"] = "1"

import re
import sys
import time
import queue
import threading
import numpy as np
import torch
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from sse_starlette.sse import EventSourceResponse

# ==================== 默认参数 ====================

MODEL_PATH = "D:/models/VoxCPM2"
HOST = "0.0.0.0"
PORT = 8801
DEFAULT_CFG_VALUE = 2.0
DEFAULT_INFERENCE_TIMESTEPS = 10
DEFAULT_MAX_LEN = 4096
MAX_CHARS_PER_SEGMENT = 80

# ==================== 全局模型 ====================

model = None
sample_rate = None


def split_text(text, max_chars=80):
    """按标点分段"""
    sentences = re.split(r"(?<=[。！？；\n])", text)
    segments, cur = [], ''
    for s in sentences:
        if not s.strip():
            continue
        if len(cur) + len(s) > max_chars and cur:
            segments.append(cur)
            cur = s
        else:
            cur += s
    if cur.strip():
        segments.append(cur)
    return segments if segments else [text]


class AudioPlayer:
    """独立线程播放音频块"""

    def __init__(self, sr):
        self.sr = sr
        self.chunk_queue = queue.Queue()
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._playback_loop, daemon=True)
        self._thread.start()

    def put(self, chunk):
        self.chunk_queue.put(chunk)

    def signal_end(self):
        self.chunk_queue.put(None)

    def wait(self):
        if self._thread:
            self._thread.join(timeout=120)

    def _playback_loop(self):
        import sounddevice as sd
        stream = sd.OutputStream(samplerate=self.sr, channels=1, dtype="float32")
        stream.start()
        try:
            while not self._stop.is_set():
                chunk = self.chunk_queue.get()
                if chunk is None:
                    break
                stream.write(chunk.reshape(-1, 1))
        finally:
            stream.stop()
            stream.close()


def stream_tts_to_speaker(text, mode="basic", language="zh",
                          reference_wav_path=None, prompt_wav_path=None,
                          prompt_text=None, cfg_value=2.0,
                          inference_timesteps=10, max_len=4096):
    """流式生成 TTS 音频并实时播放到音响，同时 yield 进度事件"""
    global model, sample_rate

    # voice_design 模式处理
    if mode == "voice_design" and not text.strip().startswith("("):
        voice_hints = {
            "zh": "(年轻女性，温柔甜美的声音)",
            "en": "(A young woman, gentle and sweet voice)",
            "ja": "(若い女性、優しく甘い声で)",
        }
        hint = voice_hints.get(language, voice_hints["zh"])
        text = f"{hint}{text}"

    segments = split_text(text, MAX_CHARS_PER_SEGMENT)

    player = AudioPlayer(sample_rate)
    player.start()

    total_chunks = 0
    total_t0 = time.time()

    try:
        for i, seg in enumerate(segments):
            gen_kwargs = {
                "cfg_value": cfg_value,
                "inference_timesteps": inference_timesteps,
                "max_len": max_len,
                "streaming": True,
            }
            if reference_wav_path:
                gen_kwargs["reference_wav_path"] = reference_wav_path
            if prompt_wav_path:
                gen_kwargs["prompt_wav_path"] = prompt_wav_path
            if prompt_text:
                gen_kwargs["prompt_text"] = prompt_text

            seg_t0 = time.time()
            seg_chunks = 0

            gen = model._generate(text=seg, **gen_kwargs)
            for wav_chunk in gen:
                seg_chunks += 1
                total_chunks += 1
                player.put(wav_chunk)

            seg_elapsed = time.time() - seg_t0
            yield {
                "event": "segment_done",
                "segment_index": i + 1,
                "total_segments": len(segments),
                "segment_text": seg[:50],
                "segment_chunks": seg_chunks,
                "segment_time": round(seg_elapsed, 2),
            }

    finally:
        player.signal_end()
        player.wait()

    total_elapsed = time.time() - total_t0
    yield {
        "event": "done",
        "total_chunks": total_chunks,
        "total_time": round(total_elapsed, 2),
        "sample_rate": sample_rate,
    }


# ==================== FastAPI ====================

class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, description="要合成的文本")
    mode: str = Field("basic", description="模式: basic / voice_design / clone / ultimate_clone")
    language: str = Field("zh", description="语种: zh/en/ja/ko 等")
    reference_wav: Optional[str] = Field(None, description="参考音频路径 (clone)")
    prompt_audio: Optional[str] = Field(None, description="提示音频路径 (ultimate_clone)")
    prompt_text: Optional[str] = Field(None, description="提示音频文本 (ultimate_clone)")
    cfg_value: float = Field(DEFAULT_CFG_VALUE, description="引导强度")
    inference_timesteps: int = Field(DEFAULT_INFERENCE_TIMESTEPS, description="推理步数")
    max_len: int = Field(DEFAULT_MAX_LEN, description="最大生成长度")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, sample_rate
    print("正在加载 VoxCPM2 模型...")
    from voxcpm import VoxCPM
    t0 = time.time()
    model = VoxCPM.from_pretrained(MODEL_PATH, load_denoiser=False)
    sample_rate = model.tts_model.sample_rate
    print(f"模型加载完成 ({time.time()-t0:.1f}s)  采样率: {sample_rate}")
    print(f"TTS 服务已启动: http://{HOST}:{PORT}")
    yield
    print("TTS 服务关闭")


app = FastAPI(title="VoxCPM2 流式 TTS 服务", lifespan=lifespan)


@app.post("/tts")
async def tts_endpoint(req: TTSRequest):
    """流式 TTS：输入文本 → 生成语音 → 实时播放到音响，SSE 返回进度"""
    if model is None:
        raise HTTPException(503, "模型尚未加载完成")

    # 参数校验
    if req.mode == "clone" and not req.reference_wav:
        raise HTTPException(400, "clone 模式需要 reference_wav")
    if req.mode == "ultimate_clone" and (not req.prompt_audio or not req.prompt_text):
        raise HTTPException(400, "ultimate_clone 模式需要 prompt_audio 和 prompt_text")

    # 文件存在性校验
    for label, path in [("reference_wav", req.reference_wav),
                         ("prompt_audio", req.prompt_audio)]:
        if path and not os.path.exists(path):
            raise HTTPException(400, f"{label} 文件不存在: {path}")

    def event_generator():
        for evt in stream_tts_to_speaker(
            text=req.text,
            mode=req.mode,
            language=req.language,
            reference_wav_path=req.reference_wav,
            prompt_wav_path=req.prompt_audio,
            prompt_text=req.prompt_text,
            cfg_value=req.cfg_value,
            inference_timesteps=req.inference_timesteps,
            max_len=req.max_len,
        ):
            yield {"data": __import__("json").dumps(evt, ensure_ascii=False)}

    return EventSourceResponse(event_generator())


@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": model is not None, "sample_rate": sample_rate}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)