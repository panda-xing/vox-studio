# HTTP 服务 - 使用说明

基于 FastAPI 的流式 TTS / ASR HTTP 服务，支持远程调用。

## 服务概览

| 服务 | 脚本 | 端口 | 说明 |
|------|------|------|------|
| TTS 服务 | 	ts_server.py | 8801 | 输入文本 → 流式生成语音 → 实时播放到音响 |
| ASR 服务 | sr_server.py | 8802 | 麦克风语音流 → 流式识别 → 控制台实时打印转录文本 |

## 依赖安装

``bash
pip install fastapi uvicorn sse-starlette sounddevice
``

## 启动服务

### 启动 TTS 服务

``bash
python tts_server.py
``

启动后输出：
`
正在加载 VoxCPM2 模型...
模型加载完成 (11.6s)  采样率: 48000
TTS 服务已启动: http://0.0.0.0:8801
``

### 启动 ASR 服务

``bash
python asr_server.py
``

启动后输出：
`
正在加载 FunASR 流式模型...
模型加载完成 (3.0s)
ASR 服务已启动: http://0.0.0.0:8802
``

> 两个服务独立运行，可同时启动，分别占用 8801 和 8802 端口。

---

## TTS 服务接口 (端口 8801)

### POST /tts

输入文本，流式生成语音并实时播放到音响，SSE 返回生成进度。

**请求体：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| 	ext | string | 必填 | 要合成的文本 |
| mode | string | asic | 模式：asic / oice_design / clone / ultimate_clone |
| language | string | zh | 语种 |
| eference_wav | string | null | 参考音频路径 (clone) |
| prompt_audio | string | null | 提示音频路径 (ultimate_clone) |
| prompt_text | string | null | 提示音频文本 (ultimate_clone) |
| cfg_value | float | 2.0 | 引导强度 |
| inference_timesteps | int | 10 | 推理步数 |
| max_len | int | 4096 | 最大生成长度 |

**请求示例：**

``bash
# 基础合成
curl -X POST http://localhost:8801/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "你好世界"}'

# Voice Design
curl -X POST http://localhost:8801/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "(年轻女性，温柔)欢迎收听！", "mode": "voice_design"}'

# 声音克隆
curl -X POST http://localhost:8801/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "欢迎来到直播间", "mode": "clone", "reference_wav": "刘娜录音.wav"}'
``

**SSE 响应事件：**

| 事件 | 说明 |
|------|------|
| segment_done | 一段文本生成完成，包含段号、块数、耗时 |
| done | 全部生成完成，包含总块数、总耗时 |

响应示例：
`
data: {"event": "segment_done", "segment_index": 1, "total_segments": 1, "segment_chunks": 21, "segment_time": 3.45}
data: {"event": "done", "total_chunks": 21, "total_time": 3.75, "sample_rate": 48000}
`

### GET /health

健康检查。

`json
{"status": "ok", "model_loaded": true, "sample_rate": 48000}
`

---

## ASR 服务接口 (端口 8802)

### POST /asr/start

启动麦克风实时采集 + 识别。识别结果实时打印到服务端控制台。

**请求体：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| chunk_ms | int | 600 | 每块时长毫秒数 |
| mic_device | int | null | 麦克风设备索引 |

``bash
curl -X POST http://localhost:8802/asr/start \
  -H "Content-Type: application/json" \
  -d '{"chunk_ms": 600}'
``

响应：
`json
{"status": "started", "chunk_ms": 600}
`

### POST /asr/stop

停止麦克风识别，返回最终结果。

``bash
curl -X POST http://localhost:8802/asr/stop \
  -H "Content-Type: application/json" \
  -d '{}'
``

响应：
`json
{"status": "stopped", "results": ["识别到的文本"]}
`

### GET /asr/stream

SSE 实时接收麦克风识别结果（需先调用 /asr/start）。

``bash
curl -N http://localhost:8802/asr/stream
``

SSE 事件：

| 事件 | 说明 |
|------|------|
| started | 麦克风已启动 |
| partial | 中间识别结果（累计文本） |
| stopped | 麦克风已停止，含最终文本 |

### POST /asr/file

从音频文件流式识别，SSE 返回进度。

**请求体：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| input | string | 必填 | 音频文件路径 |
| language | string | zh | 语种 |
| chunk_ms | int | 600 | 每块时长毫秒数 |

``bash
curl -X POST http://localhost:8802/asr/file \
  -H "Content-Type: application/json" \
  -d '{"input": "刘娜录音.wav", "language": "zh"}'
``

SSE 事件：

| 事件 | 说明 |
|------|------|
| info | 音频信息（时长、分块数） |
| partial | 中间识别结果 |
| waiting | 等待语音 |
| done | 识别完成 |

### GET /asr/status

查看当前状态。

`json
{"model_loaded": true, "mic_running": false, "chunk_count": 0, "last_text": "", "subscribers": 0}
`

### GET /health

健康检查。

`json
{"status": "ok", "model_loaded": true}
`

---

## 测试脚本

	est_servers.py 提供两个服务的端到端请求测试。

### 运行方式

``bash
# 前提：先启动两个服务
python tts_server.py    # 终端1
python asr_server.py    # 终端2

# 运行全部测试
python test_servers.py

# 仅测试 TTS
python test_servers.py --tts-only

# 仅测试 ASR
python test_servers.py --asr-only

# SSE 实时订阅演示
python test_servers.py --sse-demo

# 指定服务地址
python test_servers.py --tts-url http://192.168.1.10:8801 --asr-url http://192.168.1.10:8802
``

### 测试覆盖

**TTS 服务 (8801)：**

| 测试 | 接口 | 说明 |
|------|------|------|
| 1 | GET /health | 健康检查，验证模型已加载 |
| 2 | POST /tts | 基础合成，验证 SSE 事件流 |
| 3 | POST /tts | Voice Design 模式 |
| 4 | POST /tts | 错误参数（clone 缺 reference_wav → 400） |

**ASR 服务 (8802)：**

| 测试 | 接口 | 说明 |
|------|------|------|
| 1 | GET /health | 健康检查 |
| 2 | GET /asr/status | 状态查询，自动修复脏状态 |
| 3 | POST /asr/file | 文件流式识别（SSE） |
| 4 | POST /asr/start | 启动麦克风 |
| 5 | POST /asr/stop | 停止麦克风 |
| 6 | GET /asr/status | 最终状态验证 |

### 预期输出

`
============================================================
  VoxCPM2 TTS & ASR Service Test
  TTS: http://localhost:8801
  ASR: http://localhost:8802
============================================================

  TTS Service Test (port 8801)
  [1] GET /health          => model_loaded=true
  [2] POST /tts - basic    => 21 chunks, 3.75s
  [3] POST /tts - vdesign  => 9 chunks, 1.73s
  [4] POST /tts - bad params => HTTP 400

  ASR Service Test (port 8802)
  [1] GET /health          => model_loaded=true
  [2] GET /asr/status      => mic_running=False
  [3] POST /asr/file       => SSE partial + done
  [4] POST /asr/start      => started
  [5] POST /asr/stop       => stopped
  [6] GET /asr/status      => mic_running=False

============================================================
  Summary
  TTS: PASS
  ASR: PASS
============================================================
`

---

## Python 调用示例

### 调用 TTS 服务

``python
import requests, json

# 基础合成
resp = requests.post("http://localhost:8801/tts",
                     json={"text": "你好世界", "mode": "basic"},
                     headers={"Accept": "text/event-stream"})
for line in resp.iter_lines(decode_unicode=True):
    if line.startswith("data:"):
        evt = json.loads(line[5:])
        print(evt["event"], evt.get("total_chunks", ""))
``

### 调用 ASR 服务（文件识别）

``python
import requests, json

resp = requests.post("http://localhost:8802/asr/file",
                     json={"input": "audio.wav", "language": "zh"})
for line in resp.iter_lines(decode_unicode=True):
    if line.startswith("data:"):
        evt = json.loads(line[5:])
        if evt["event"] == "partial":
            print(f"[partial] {evt['text']}")
        elif evt["event"] == "done":
            print(f"[done] {evt['text']}")
``

### 调用 ASR 服务（麦克风 + SSE 实时接收）

``python
import requests, json, threading, time

# 启动麦克风
requests.post("http://localhost:8802/asr/start", json={"chunk_ms": 600})

# SSE 实时接收
def listen():
    resp = requests.get("http://localhost:8802/asr/stream", stream=True)
    for line in resp.iter_lines(decode_unicode=True):
        if line.startswith("data:"):
            evt = json.loads(line[5:])
            if evt["event"] == "partial":
                print(f"[live] {evt['text']}")
            elif evt["event"] == "stopped":
                print(f"[final] {evt.get('final_text', '')}")
                break

t = threading.Thread(target=listen, daemon=True)
t.start()

time.sleep(10)  # 录音 10 秒
requests.post("http://localhost:8802/asr/stop", json={})
t.join()
``

---

## 常见问题

**端口被占用？** 修改脚本顶部的 PORT 常量，或设置环境变量。

**TTS 没有声音输出？** 确认服务器所在机器有音响设备，sounddevice 可正常输出。

**ASR 麦克风无声音？** 检查麦克风设备，用 --mic-device 指定正确设备索引。

**SSE 连接超时？** 默认超时 30 秒，长文本 TTS 可适当增加客户端超时设置。

**CUDA OOM？** TTS 模型需约 8GB VRAM，ASR 模型较小。两个服务同时运行约需 10GB VRAM。

**tqdm 报错？** 脚本已内置 TQDM_DISABLE=1，若仍有问题请确认 os.environ["TQDM_DISABLE"] 在 import 前执行。