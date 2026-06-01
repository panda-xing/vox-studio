# ============================================================
#  FunASR 语音识别脚本 - 支持命令行调用 & 顶部参数调整
# ============================================================
# 使用方式一：修改下方默认参数后直接运行  python asr.py
# 使用方式二：命令行调用
#   python asr.py --input audio.wav
#   python asr.py --input audio.wav --punc --output result.txt
#   python asr.py --input audio.wav --language en
# ============================================================

# ==================== 默认参数（直接修改这里即可） ====================

INPUT = r"D:\codes\VoxCPM2\刘娜录音.wav"           # 输入音频路径
OUTPUT = ""                                         # 输出文件路径，留空则仅打印
LANGUAGE = "zh"                                     # 语种: zh / en / ja / ko 等
MODEL = "paraformer-zh"                             # ASR 模型名称
PUNC = True                                         # 是否添加标点
VAD = True                                          # 是否启用 VAD（语音活动检测）
FORMAT = "text"                                     # 输出格式: text / srt / json
RESAMPLE_16K = True                                 # 自动重采样为 16kHz（FunASR 要求）

# ==================== 以下无需修改 ====================

import argparse
import os
import sys
import time
import numpy as np
import soundfile as sf


def parse_args():
    parser = argparse.ArgumentParser(description="FunASR 语音识别")
    parser.add_argument("--input", type=str, default=None, help="输入音频文件路径")
    parser.add_argument("--output", type=str, default=None, help="输出文件路径（留空仅打印）")
    parser.add_argument("--language", type=str, default=None, help="语种: zh/en/ja/ko 等")
    parser.add_argument("--model", type=str, default=None, help="ASR 模型名称")
    parser.add_argument("--punc", action="store_true", default=None, help="添加标点")
    parser.add_argument("--no-punc", action="store_true", help="不添加标点")
    parser.add_argument("--vad", action="store_true", default=None, help="启用 VAD")
    parser.add_argument("--no-vad", action="store_true", help="禁用 VAD")
    parser.add_argument("--format", type=str, default=None, choices=["text", "srt", "json"], help="输出格式")
    parser.add_argument("--no-resample", action="store_true", help="不自动重采样（保持原采样率）")
    return parser.parse_args()


def apply_args(args):
    mapping = {
        "input": "INPUT", "output": "OUTPUT", "language": "LANGUAGE",
        "model": "MODEL", "format": "FORMAT",
    }
    for arg_name, var_name in mapping.items():
        val = getattr(args, arg_name)
        if val is not None:
            globals()[var_name] = val
    if args.no_punc:
        globals()["PUNC"] = False
    elif args.punc:
        globals()["PUNC"] = True
    if args.no_vad:
        globals()["VAD"] = False
    elif args.vad:
        globals()["VAD"] = True
    if args.no_resample:
        globals()["RESAMPLE_16K"] = False


def preprocess_audio(audio_path):
    """读取音频并转为单声道 16kHz（FunASR 要求）"""
    data, sr = sf.read(audio_path)
    # 双声道转单声道
    if data.ndim > 1:
        data = data.mean(axis=1)
    # 重采样到 16kHz
    if sr != 16000 and RESAMPLE_16K:
        data = np.interp(np.arange(0, len(data), sr / 16000), np.arange(len(data)), data)
        sr = 16000
    return data, sr


def main():
    args = parse_args()
    apply_args(args)

    if not os.path.exists(INPUT):
        print(f"错误: 音频文件不存在: {INPUT}")
        sys.exit(1)

    print(f"输入: {INPUT}")
    print(f"语种: {LANGUAGE}")
    print(f"模型: {MODEL}")
    print(f"标点: {PUNC}  VAD: {VAD}  格式: {FORMAT}")

    # 音频预处理
    print("正在预处理音频...")
    data, sr = preprocess_audio(INPUT)

    # 保存临时 16kHz 单声道文件
    tmp_path = None
    if sr == 16000:
        # 检查原始文件是否已经是 16kHz 单声道
        info = sf.info(INPUT)
        if info.samplerate == 16000 and info.channels == 1:
            asr_input = INPUT
        else:
            tmp_path = os.path.join(os.path.dirname(INPUT), "_asr_tmp_16k.wav")
            sf.write(tmp_path, data, 16000)
            asr_input = tmp_path
    else:
        tmp_path = os.path.join(os.path.dirname(INPUT), "_asr_tmp_16k.wav")
        sf.write(tmp_path, data, 16000)
        asr_input = tmp_path

    # 加载模型
    print("正在加载模型...")
    from funasr import AutoModel

    model_kwargs = {"model": MODEL, "disable_update": True}
    if PUNC:
        model_kwargs["punc_model"] = "ct-punc"
        model_kwargs["punc_model_revision"] = "v2.0.4"
    if VAD:
        model_kwargs["vad_model"] = "fsmn-vad"
        model_kwargs["vad_model_revision"] = "v2.0.4"
    if LANGUAGE == "en":
        model_kwargs["model"] = "paraformer-en"

    model = AutoModel(**model_kwargs)

    # 识别
    print("正在识别...")
    t0 = time.time()
    result = model.generate(input=asr_input)
    elapsed = time.time() - t0

    # 清理临时文件
    if tmp_path and os.path.exists(tmp_path):
        os.remove(tmp_path)

    # 格式化输出
    if FORMAT == "text":
        texts = []
        for res in result:
            text = res["text"].replace(" ", "")  # 去掉逐字空格
            texts.append(text)
        output_text = "\n".join(texts)
    elif FORMAT == "json":
        import json
        output_text = json.dumps(result, ensure_ascii=False, indent=2)
    elif FORMAT == "srt":
        lines = []
        for i, res in enumerate(result):
            text = res["text"].replace(" ", "")
            start = res.get("timestamp", [[0, 0]])[0][0] / 1000.0 if "timestamp" in res else 0.0
            end = res.get("timestamp", [[0, 0]])[-1][1] / 1000.0 if "timestamp" in res else 0.0
            lines.append(f"{i+1}")
            lines.append(f"{format_srt_time(start)} --> {format_srt_time(end)}")
            lines.append(text)
            lines.append("")
        output_text = "\n".join(lines)
    else:
        texts = []
        for res in result:
            texts.append(res["text"].replace(" ", ""))
        output_text = "\n".join(texts)

    print(f"\n识别完成 (耗时 {elapsed:.1f}s):")
    print(output_text)

    # 保存到文件
    if OUTPUT:
        os.makedirs(os.path.dirname(OUTPUT) or ".", exist_ok=True)
        with open(OUTPUT, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f"已保存: {OUTPUT}")


def format_srt_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


if __name__ == "__main__":
    main()
