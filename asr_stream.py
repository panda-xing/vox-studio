# ============================================================
#  FunASR 流式语音识别脚本 - 麦克风实时识别 & 长音频边读边识别
# ============================================================
# 使用方式：
#   python asr_stream.py --mic                          # 麦克风实时采集 + 逐句识别
#   python asr_stream.py --input long.wav               # 长音频边读边识别
#   python asr_stream.py --input long.wav --output out.txt
#   python asr_stream.py --mic --chunk-ms 600           # 调整麦克风每块时长
#   python asr_stream.py --mic --language en            # 英文流式识别
# ============================================================

# ==================== 默认参数（直接修改这里即可） ====================

INPUT = ""                                         # 输入音频路径，留空则用麦克风
OUTPUT = ""                                         # 输出文件路径，留空则仅打印
LANGUAGE = "zh"                                     # 语种: zh / en
CHUNK_MS = 600                                      # 每块时长（毫秒）
MIC_DEVICE = None                                   # 麦克风设备索引，None 为默认
SHOW_PARTIAL = True                                 # 是否显示中间结果（partial result）
FORMAT = "text"                                     # 输出格式: text / json

# ==================== 以下无需修改 ====================

import argparse
import os
import sys
import time
import numpy as np
import soundfile as sf


def parse_args():
    parser = argparse.ArgumentParser(description="FunASR 流式语音识别")
    parser.add_argument("--input", type=str, default=None, help="输入音频文件路径（长音频边读边识别）")
    parser.add_argument("--output", type=str, default=None, help="输出文件路径（留空仅打印）")
    parser.add_argument("--mic", action="store_true", default=None, help="麦克风实时采集模式")
    parser.add_argument("--language", type=str, default=None, help="语种: zh/en")
    parser.add_argument("--chunk-ms", type=int, default=None, help="每块时长毫秒数 (默认 600)")
    parser.add_argument("--mic-device", type=int, default=None, help="麦克风设备索引")
    parser.add_argument("--no-partial", action="store_true", help="不显示中间结果")
    parser.add_argument("--format", type=str, default=None, choices=["text", "json"], help="输出格式")
    return parser.parse_args()


def apply_args(args):
    mapping = {
        "input": "INPUT", "output": "OUTPUT", "language": "LANGUAGE",
        "chunk_ms": "CHUNK_MS", "mic_device": "MIC_DEVICE",
        "format": "FORMAT",
    }
    for arg_name, var_name in mapping.items():
        val = getattr(args, arg_name)
        if val is not None:
            globals()[var_name] = val
    if args.no_partial:
        globals()["SHOW_PARTIAL"] = False
    if args.mic:
        globals()["_USE_MIC"] = True
    else:
        globals()["_USE_MIC"] = False


def get_streaming_model(language="zh"):
    """加载流式 ASR 模型"""
    from funasr import AutoModel
    model_name = "paraformer-zh-streaming" if language == "zh" else "paraformer-en-streaming"
    print(f"正在加载流式模型: {model_name} ...")
    t0 = time.time()
    model = AutoModel(model=model_name, disable_update=True)
    print(f"模型加载完成 ({time.time()-t0:.1f}s)")
    return model


def process_chunk(model, chunk, cache, is_final):
    """处理一个音频块，返回 (文本, 是否有输出)

    流式模式下，中间结果为累计文本，最终结果时 text 可能为空。
    返回值: (text, has_output)
      - has_output=True 表示有识别文本可供显示
      - is_final=True 且无文本时，text=None 表示流结束
    """
    res = model.generate(input=chunk, cache=cache, is_final=is_final)
    if res and len(res) > 0:
        text = res[0].get("text", "").replace(" ", "")
        if text:
            return text, True
    if is_final:
        return None, False
    return None, False


def stream_from_file(model, audio_path, chunk_ms=600, show_partial=True):
    """从音频文件边读边识别"""
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

    print(f"音频时长: {len(data)/sr:.1f}s  分块: {total_chunks} 块 ({chunk_ms}ms/块)")

    for i in range(0, len(data), chunk_samples):
        chunk = data[i:i+chunk_samples]
        is_final = (i + chunk_samples >= len(data))
        chunk_idx = i // chunk_samples + 1

        text, has_output = process_chunk(model, chunk, cache, is_final)

        if has_output and text:
            last_text = text
            if is_final:
                print(f"\r[块 {chunk_idx}/{total_chunks}] 最终: {text}")
            else:
                if show_partial:
                    print(f"\r[块 {chunk_idx}/{total_chunks}] 中间: {text}", end="", flush=True)
        else:
            if show_partial:
                print(f"\r[块 {chunk_idx}/{total_chunks}] 等待语音...", end="", flush=True)

    print()
    # 返回最后一次有效文本
    return [last_text] if last_text else []


def stream_from_mic(model, chunk_ms=600, mic_device=None, show_partial=True):
    """麦克风实时采集 + 逐句识别"""
    import sounddevice as sd

    sr = 16000
    chunk_samples = int(sr * chunk_ms / 1000)
    cache = {}
    results = []
    last_text = ""

    print(f"麦克风采样率: {sr}Hz  每块: {chunk_ms}ms ({chunk_samples} 采样点)")
    print("开始录音... (按 Ctrl+C 停止)")

    try:
        chunk_count = 0
        while True:
            recording = sd.rec(chunk_samples, samplerate=sr, channels=1, dtype="float32",
                               device=mic_device)
            sd.wait()
            chunk = recording.flatten()
            chunk_count += 1

            text, has_output = process_chunk(model, chunk, cache, False)

            if has_output and text:
                last_text = text
                if show_partial:
                    print(f"\r[块 {chunk_count}] 中间: {text}", end="", flush=True)
            else:
                if show_partial:
                    print(f"\r[块 {chunk_count}] 等待语音...", end="", flush=True)

    except KeyboardInterrupt:
        print("\n停止录音")
        # 发送 is_final=True 刷新最后结果
        text, has_output = process_chunk(model, chunk, cache, True)
        if has_output and text:
            last_text = text
            results.append(text)
            print(f"最终: {text}")
        elif last_text:
            results.append(last_text)
            print(f"最终: {last_text}")

    return results


def main():
    args = parse_args()
    apply_args(args)

    use_mic = globals().get("_USE_MIC", False)
    if not INPUT and not use_mic:
        use_mic = True

    if use_mic:
        print("模式: 麦克风实时识别")
    else:
        if not os.path.exists(INPUT):
            print(f"错误: 音频文件不存在: {INPUT}")
            sys.exit(1)
        print(f"模式: 长音频流式识别  输入: {INPUT}")

    print(f"语种: {LANGUAGE}  块时长: {CHUNK_MS}ms  显示中间结果: {SHOW_PARTIAL}")

    model = get_streaming_model(LANGUAGE)

    t0 = time.time()
    if use_mic:
        results = stream_from_mic(model, chunk_ms=CHUNK_MS, mic_device=MIC_DEVICE,
                                  show_partial=SHOW_PARTIAL)
    else:
        results = stream_from_file(model, INPUT, chunk_ms=CHUNK_MS, show_partial=SHOW_PARTIAL)

    elapsed = time.time() - t0

    if FORMAT == "json":
        import json
        output_text = json.dumps(results, ensure_ascii=False, indent=2)
    else:
        output_text = "\n".join(results)

    print(f"\n识别完成 (耗时 {elapsed:.1f}s):")
    print(output_text)

    if OUTPUT:
        os.makedirs(os.path.dirname(OUTPUT) or ".", exist_ok=True)
        with open(OUTPUT, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f"已保存: {OUTPUT}")


if __name__ == "__main__":
    main()