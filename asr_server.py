# ============================================================
#  FunASR 流式 ASR HTTP 服务 - 麦克风语音流 → 实时控制台打印转录文本
# ============================================================
# 启动：python asr_server.py
# 调用：curl http://localhost:8802/asr/start  → 开始麦克风录音识别
#       curl http://localhost:8802/asr/stop   → 停止识别
#       curl http://localhost:8802/asr/status → 查看状态
#       SSE:  curl -N http://localhost:8802/asr/stream  → 实时接收识别结果
# ============================================================

import os
os.environ["TQDM_DISABLE"] = "1"



import sys
import time
import json
import threading
import numpy as np
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from sse_starlette.sse import EventSourceResponse

# ==================== 默认参数 ====================

HOST = "0.0.0.0"
PORT = 8802
CHUNK_MS = 600
SAMPLE_RATE = 16000

# ==================== 全局状态 ====================

asr_model = None
mic_state = {
    "running": False,
    "results": [],
    "last_text": "",
    "lock": threading.Lock(),
    "stop_event": threading.Event(),
    "thread": None,
    "chunk_count": 0,
}
# SSE 订阅者队列列表
_subscribers: list = []


def get_streaming_model(language="zh"):
    """加载流式 ASR 模型"""
    from funasr import AutoModel
    model_name = "paraformer-zh-streaming" if language == "zh" else "paraformer-en-streaming"
    print(f"正在加载流式模型: {model_name} ...")
    t0 = time.time()
    m = AutoModel(model=model_name, disable_update=True)
    print(f"模型加载完成 ({time.time()-t0:.1f}s)")
    return m


def process_chunk(chunk, cache, is_final):
    """处理一个音频块"""
    res = asr_model.generate(input=chunk, cache=cache, is_final=is_final)
    if res and len(res) > 0:
        text = res[0].get("text", "").replace(" ", "")
        if text:
            return text, True
    return None, False


def broadcast_event(event: dict):
    """向所有 SSE 订阅者广播事件"""
    data = json.dumps(event, ensure_ascii=False)
    dead = []
    for i, q in enumerate(_subscribers):
        try:
            q.put_nowait(data)
        except Exception:
            dead.append(i)
    for i in reversed(dead):
        _subscribers.pop(i)


def mic_loop(chunk_ms=600, mic_device=None):
    """麦克风采集循环：采集 → 识别 → 控制台打印 + SSE 广播"""
    import sounddevice as sd

    sr = SAMPLE_RATE
    chunk_samples = int(sr * chunk_ms / 1000)
    cache = {}
    chunk_count = 0

    print(f"[MIC] 开始录音 采样率:{sr}Hz 块:{chunk_ms}ms")
    broadcast_event({"event": "started", "chunk_ms": chunk_ms, "sample_rate": sr})

    while not mic_state["stop_event"].is_set():
        try:
            recording = sd.rec(chunk_samples, samplerate=sr, channels=1,
                               dtype="float32", device=mic_device)
            sd.wait()
            chunk = recording.flatten()
            chunk_count += 1

            with mic_state["lock"]:
                mic_state["chunk_count"] = chunk_count

            text, has_output = process_chunk(chunk, cache, False)

            if has_output and text:
                with mic_state["lock"]:
                    mic_state["last_text"] = text

                # 控制台实时打印
                print(f"\r[MIC 块 {chunk_count}] {text}", end="", flush=True)

                # SSE 广播中间结果
                broadcast_event({
                    "event": "partial",
                    "chunk": chunk_count,
                    "text": text,
                })

        except Exception as e:
            print(f"\n[MIC] 采集错误: {e}")
            break

    # 停止后发送 is_final
    with mic_state["lock"]:
        last_text = mic_state["last_text"]

    if last_text:
        with mic_state["lock"]:
            mic_state["results"].append(last_text)

    print(f"\n[MIC] 录音停止  最终文本: {last_text}")
    broadcast_event({"event": "stopped", "final_text": last_text, "chunks": chunk_count})

    with mic_state["lock"]:
        mic_state["running"] = False


# ==================== 文件流式识别 ====================

class FileASRRequest(BaseModel):
    input: str = Field(..., description="输入音频文件路径")
    language: str = Field("zh", description="语种: zh/en")
    chunk_ms: int = Field(600, description="每块时长毫秒数")


def stream_file_asr(audio_path, chunk_ms=600):
    """从音频文件边读边识别，yield 事件"""
    import soundfile as sf

    data, sr = sf.read(audio_path)
    if data.ndim > 1:
        data = data.mean(axis=1)
    if sr != 16000:
        data = np.interp(np.arange(0, len(data), sr / 16000), np.arange(len(data)), data)
        sr = 16000

    chunk_samples = int(sr * chunk_ms / 1000)
    cache = {}
    last_text = ""
    total_chunks = (len(data) + chunk_samples - 1) // chunk_samples

    yield {"event": "info", "duration": round(len(data)/sr, 2),
           "total_chunks": total_chunks, "chunk_ms": chunk_ms}

    for i in range(0, len(data), chunk_samples):
        chunk = data[i:i+chunk_samples]
        is_final = (i + chunk_samples >= len(data))
        chunk_idx = i // chunk_samples + 1

        text, has_output = process_chunk(chunk, cache, is_final)

        if has_output and text:
            last_text = text
            yield {"event": "partial", "chunk": chunk_idx, "text": text}
        else:
            yield {"event": "waiting", "chunk": chunk_idx}

    if last_text:
        yield {"event": "done", "text": last_text}
    else:
        yield {"event": "done", "text": ""}


# ==================== FastAPI ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    global asr_model
    print("正在加载 FunASR 流式模型...")
    asr_model = get_streaming_model("zh")
    print(f"ASR 服务已启动: http://{HOST}:{PORT}")
    yield
    # 停止麦克风
    if mic_state["running"]:
        mic_state["stop_event"].set()
        if mic_state["thread"]:
            mic_state["thread"].join(timeout=5)
    print("ASR 服务关闭")


app = FastAPI(title="FunASR 流式 ASR 服务", lifespan=lifespan)


@app.post("/asr/start")
async def asr_start(chunk_ms: int = CHUNK_MS, mic_device: Optional[int] = None):
    """启动麦克风实时识别"""
    if asr_model is None:
        raise HTTPException(503, "模型尚未加载完成")
    with mic_state["lock"]:
        if mic_state["running"]:
            raise HTTPException(409, "麦克风识别已在运行中")
        mic_state["running"] = True
        mic_state["stop_event"].clear()
        mic_state["chunk_count"] = 0
        mic_state["last_text"] = ""

    t = threading.Thread(target=mic_loop, args=(chunk_ms, mic_device), daemon=True)
    with mic_state["lock"]:
        mic_state["thread"] = t
    t.start()
    return {"status": "started", "chunk_ms": chunk_ms}


@app.post("/asr/stop")
async def asr_stop():
    """停止麦克风识别"""
    with mic_state["lock"]:
        if not mic_state["running"]:
            raise HTTPException(409, "麦克风识别未在运行")
        mic_state["stop_event"].set()

    # 等待线程结束
    if mic_state["thread"]:
        mic_state["thread"].join(timeout=5)

    with mic_state["lock"]:
        results = list(mic_state["results"])
        mic_state["results"] = []

    return {"status": "stopped", "results": results}


@app.get("/asr/stream")
async def asr_stream():
    """SSE 实时接收麦克风识别结果"""
    import queue
    q = queue.Queue()
    _subscribers.append(q)

    def event_generator():
        try:
            while True:
                try:
                    data = q.get(timeout=30)
                    yield {"data": data}
                    # 如果收到 stopped 事件，结束 SSE
                    parsed = json.loads(data)
                    if parsed.get("event") == "stopped":
                        break
                except queue.Empty:
                    yield {"event": "ping", "data": ""}
        finally:
            if q in _subscribers:
                _subscribers.remove(q)

    return EventSourceResponse(event_generator())


@app.post("/asr/file")
async def asr_file(req: FileASRRequest):
    """从音频文件流式识别，SSE 返回进度"""
    if asr_model is None:
        raise HTTPException(503, "模型尚未加载完成")
    if not os.path.exists(req.input):
        raise HTTPException(400, f"音频文件不存在: {req.input}")

    def event_generator():
        for evt in stream_file_asr(req.input, req.chunk_ms):
            yield {"data": json.dumps(evt, ensure_ascii=False)}

    return EventSourceResponse(event_generator())


@app.get("/asr/status")
async def asr_status():
    """查看当前状态"""
    with mic_state["lock"]:
        return {
            "model_loaded": asr_model is not None,
            "mic_running": mic_state["running"],
            "chunk_count": mic_state["chunk_count"],
            "last_text": mic_state["last_text"],
            "subscribers": len(_subscribers),
        }


@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": asr_model is not None}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)