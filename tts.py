# ============================================================
#  VoxCPM2 TTS 脚本 - 支持命令行调用 & 顶部参数调整
# ============================================================
# 使用方式一：修改下方默认参数后直接运行  python tts.py
# 使用方式二：命令行调用
#   python tts.py --text "你好世界" --output out.wav
#   python tts.py --text "(年轻女性，温柔)欢迎收听！" --mode voice_design
#   python tts.py --text "克隆语音" --reference ref.wav --mode clone
#   python tts.py --text "极致克隆" --prompt-audio ref.wav --prompt-text "参考文本" --mode ultimate_clone
# ============================================================

# ==================== 默认参数（直接修改这里即可） ====================

TEXT = "你好，欢迎使用VoxCPM2语音合成系统。"    # 要合成的文本
OUTPUT = "output/output.wav"                            # 输出文件路径
MODE = "basic"                                   # 模式: basic / voice_design / clone / ultimate_clone
LANGUAGE = "zh"                                  # 语种提示: zh / en / ja / ko / fr / de 等 (仅作参考注释)
MODEL_PATH = "D:/models/VoxCPM2"                 # 模型本地路径
REFERENCE_WAV = r"D:\codes\VoxCPM2\刘娜录音.wav"   # 参考音频路径 (clone 模式用)
PROMPT_WAV = r"D:\codes\VoxCPM2\刘娜录音.wav"    # 提示音频路径 (ultimate_clone 模式用)
PROMPT_TEXT = "喜茶好好卖奶茶不行吗，非要塞点垃圾给我，花里胡哨的，搞不清楚在干啥"  # 提示音频对应文本 (ultimate_clone 模式用)
CFG_VALUE = 2.0                                  # 引导强度，越大越贴近文本，越小越自由
INFERENCE_TIMESTEPS = 10                          # 推理步数，越多质量越高、速度越慢
MAX_LEN = 4096                                   # 最大生成长度
SEED = -1                                        # 随机种子，-1 为不固定

# ==================== 以下无需修改 ====================

import argparse
import os
import time
import numpy as np
import soundfile as sf
import torch


def parse_args():
    parser = argparse.ArgumentParser(description="VoxCPM2 TTS 语音合成")
    parser.add_argument("--text", type=str, default=None, help="要合成的文本")
    parser.add_argument("--output", type=str, default=None, help="输出 wav 文件路径")
    parser.add_argument("--mode", type=str, default=None,
                        choices=["basic", "voice_design", "clone", "ultimate_clone"],
                        help="合成模式")
    parser.add_argument("--language", type=str, default=None,
                        help="语种: zh/en/ja/ko/fr/de 等")
    parser.add_argument("--model-path", type=str, default=None,
                        help="模型本地路径或 HuggingFace ID")
    parser.add_argument("--reference-wav", type=str, default=None,
                        help="参考音频路径 (clone 模式)")
    parser.add_argument("--prompt-audio", type=str, default=None,
                        help="提示音频路径 (ultimate_clone 模式)")
    parser.add_argument("--prompt-text", type=str, default=None,
                        help="提示音频对应文本 (ultimate_clone 模式)")
    parser.add_argument("--cfg-value", type=float, default=None,
                        help="引导强度 (默认 2.0)")
    parser.add_argument("--inference-timesteps", type=int, default=None,
                        help="推理步数 (默认 10)")
    parser.add_argument("--max-len", type=int, default=None,
                        help="最大生成长度 (默认 4096)")
    parser.add_argument("--seed", type=int, default=None,
                        help="随机种子 (-1 不固定)")
    return parser.parse_args()


def apply_args(args):
    """命令行参数覆盖默认值"""
    mapping = {
        "text": "TEXT", "output": "OUTPUT", "mode": "MODE",
        "language": "LANGUAGE", "model_path": "MODEL_PATH",
        "reference_wav": "REFERENCE_WAV", "prompt_audio": "PROMPT_WAV",
        "prompt_text": "PROMPT_TEXT", "cfg_value": "CFG_VALUE",
        "inference_timesteps": "INFERENCE_TIMESTEPS", "max_len": "MAX_LEN",
        "seed": "SEED",
    }
    for arg_name, var_name in mapping.items():
        val = getattr(args, arg_name)
        if val is not None:
            globals()[var_name] = val


def main():
    args = parse_args()
    apply_args(args)

    # 固定随机种子
    if SEED >= 0:
        torch.manual_seed(SEED)
        np.random.seed(SEED)

    # 模式自动处理文本前缀
    text = TEXT
    if MODE == "voice_design" and not text.strip().startswith("("):
        # voice_design 模式下如果文本没有描述前缀，根据语种加默认描述
        voice_hints = {
            "zh": "(年轻女性，温柔甜美的声音)",
            "en": "(A young woman, gentle and sweet voice)",
            "ja": "(若い女性、優しく甘い声で)",
            "ko": "(젊은 여성, 부드럽고 달콤한 목소리)",
            "fr": "(Une jeune femme, voix douce et sucrée)",
            "de": "(Eine junge Frau, sanfte und süße Stimme)",
        }
        hint = voice_hints.get(LANGUAGE, voice_hints["zh"])
        text = f"{hint}{text}"

    print(f"模式: {MODE}")
    print(f"文本: {text}")
    print(f"语种: {LANGUAGE}")
    print(f"模型: {MODEL_PATH}")
    print(f"CFG: {CFG_VALUE}  步数: {INFERENCE_TIMESTEPS}  种子: {SEED}")

    # 加载模型
    print("正在加载模型...")
    from voxcpm import VoxCPM
    t0 = time.time()
    model = VoxCPM.from_pretrained(MODEL_PATH, load_denoiser=False)
    print(f"模型加载完成 ({time.time()-t0:.1f}s)")

    # 根据模式生成
    generate_kwargs = {
        "text": text,
        "cfg_value": CFG_VALUE,
        "inference_timesteps": INFERENCE_TIMESTEPS,
        "max_len": MAX_LEN,
    }

    if MODE == "clone":
        if not REFERENCE_WAV:
            raise ValueError("clone 模式需要指定 --reference-wav 参数")
        generate_kwargs["reference_wav_path"] = REFERENCE_WAV
        print(f"参考音频: {REFERENCE_WAV}")

    elif MODE == "ultimate_clone":
        if not PROMPT_WAV or not PROMPT_TEXT:
            raise ValueError("ultimate_clone 模式需要 --prompt-audio 和 --prompt-text")
        generate_kwargs["prompt_wav_path"] = PROMPT_WAV
        generate_kwargs["prompt_text"] = PROMPT_TEXT
        if REFERENCE_WAV:
            generate_kwargs["reference_wav_path"] = REFERENCE_WAV
        print(f"提示音频: {PROMPT_WAV}")
        print(f"提示文本: {PROMPT_TEXT}")

    print("正在生成语音...")
    t0 = time.time()
    wav = model.generate(**generate_kwargs)
    elapsed = time.time() - t0
    duration = len(wav) / model.tts_model.sample_rate
    rtf = elapsed / duration if duration > 0 else 0
    print(f"生成完成: 耗时 {elapsed:.1f}s, 音频时长 {duration:.1f}s, RTF {rtf:.3f}")

    # 保存
    os.makedirs(os.path.dirname(OUTPUT) or ".", exist_ok=True)
    sf.write(OUTPUT, wav, model.tts_model.sample_rate)
    print(f"已保存: {OUTPUT}")


if __name__ == "__main__":
    main()


