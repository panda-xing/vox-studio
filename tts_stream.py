# ============================================================
#  VoxCPM2 流式 TTS 脚本 - 边生成边播放，降低等待感
# ============================================================
# 使用方式：
#   python tts_stream.py --text "你好世界" --play
#   python tts_stream.py --text "你好世界" --output out.wav
#   python tts_stream.py --text "很长的文本..." --play --output out.wav
#   python tts_stream.py --text "克隆语音" --reference ref.wav --mode clone --play
#   python tts_stream.py --text "极致克隆" --prompt-audio ref.wav --prompt-text "参考文本" --mode ultimate_clone --play
# ============================================================

# ==================== 默认参数（直接修改这里即可） ====================

TEXT = "你好，欢迎使用VoxCPM2流式语音合成系统。边生成边播放，降低等待感。"
OUTPUT = ""                                         # 输出文件路径，留空则不保存
PLAY = True                                         # 是否实时播放
MODE = "basic"                                      # 模式: basic / voice_design / clone / ultimate_clone
LANGUAGE = "zh"                                     # 语种提示
MODEL_PATH = "D:/models/VoxCPM2"                    # 模型本地路径
REFERENCE_WAV = r"D:\codes\VoxCPM2\刘娜录音.wav"    # 参考音频路径 (clone 模式用)
PROMPT_WAV = r"D:\codes\VoxCPM2\刘娜录音.wav"      # 提示音频路径 (ultimate_clone 模式用)
PROMPT_TEXT = "喜茶好好卖奶茶不行吗，非要塞点垃圾给我，花里胡哨的，搞不清楚在干啥"
CFG_VALUE = 2.0                                     # 引导强度
INFERENCE_TIMESTEPS = 10                            # 推理步数
MAX_LEN = 4096                                      # 最大生成长度
SEED = -1                                           # 随机种子
MAX_CHARS_PER_SEGMENT = 80                          # 长文本分段：每段最大字符数

# ==================== 以下无需修改 ====================

import argparse
import os
import re
import sys
import time
import queue
import threading
import numpy as np
import soundfile as sf
import torch


def parse_args():
    parser = argparse.ArgumentParser(description="VoxCPM2 流式 TTS 语音合成")
    parser.add_argument("--text", type=str, default=None, help="要合成的文本")
    parser.add_argument("--output", type=str, default=None, help="输出 wav 文件路径（留空不保存）")
    parser.add_argument("--play", action="store_true", default=None, help="实时播放音频")
    parser.add_argument("--no-play", action="store_true", help="不播放音频")
    parser.add_argument("--mode", type=str, default=None,
                        choices=["basic", "voice_design", "clone", "ultimate_clone"],
                        help="合成模式")
    parser.add_argument("--language", type=str, default=None, help="语种: zh/en/ja/ko 等")
    parser.add_argument("--model-path", type=str, default=None, help="模型本地路径")
    parser.add_argument("--reference-wav", type=str, default=None, help="参考音频路径 (clone)")
    parser.add_argument("--prompt-audio", type=str, default=None, help="提示音频路径 (ultimate_clone)")
    parser.add_argument("--prompt-text", type=str, default=None, help="提示音频文本 (ultimate_clone)")
    parser.add_argument("--cfg-value", type=float, default=None, help="引导强度 (默认 2.0)")
    parser.add_argument("--inference-timesteps", type=int, default=None, help="推理步数 (默认 10)")
    parser.add_argument("--max-len", type=int, default=None, help="最大生成长度 (默认 4096)")
    parser.add_argument("--seed", type=int, default=None, help="随机种子 (-1 不固定)")
    parser.add_argument("--max-chars", type=int, default=None, help="长文本分段每段最大字符数 (默认 80)")
    return parser.parse_args()


def apply_args(args):
    mapping = {
        "text": "TEXT", "output": "OUTPUT", "mode": "MODE",
        "language": "LANGUAGE", "model_path": "MODEL_PATH",
        "reference_wav": "REFERENCE_WAV", "prompt_audio": "PROMPT_WAV",
        "prompt_text": "PROMPT_TEXT", "cfg_value": "CFG_VALUE",
        "inference_timesteps": "INFERENCE_TIMESTEPS", "max_len": "MAX_LEN",
        "seed": "SEED", "max_chars": "MAX_CHARS_PER_SEGMENT",
    }
    for arg_name, var_name in mapping.items():
        val = getattr(args, arg_name)
        if val is not None:
            globals()[var_name] = val
    if args.no_play:
        globals()["PLAY"] = False
    elif args.play:
        globals()["PLAY"] = True


def split_text(text, max_chars=80):
    """按标点分段，每段不超过 max_chars 字符"""
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
    """独立线程播放音频块，避免阻塞生成"""

    def __init__(self, sample_rate):
        self.sample_rate = sample_rate
        self.chunk_queue = queue.Queue()
        self.all_chunks = []
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._playback_loop, daemon=True)
        self._thread.start()

    def put(self, chunk):
        self.all_chunks.append(chunk)
        self.chunk_queue.put(chunk)

    def signal_end(self):
        self.chunk_queue.put(None)

    def wait(self):
        if self._thread:
            self._thread.join()

    def get_full_wav(self):
        if not self.all_chunks:
            return np.array([], dtype=np.float32)
        return np.concatenate(self.all_chunks)

    def _playback_loop(self):
        import sounddevice as sd
        stream = sd.OutputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
        )
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


def stream_segment(model, text, sample_rate, player=None, file_chunks=None,
                   cfg_value=2.0, inference_timesteps=10, max_len=4096,
                   reference_wav_path=None, prompt_wav_path=None, prompt_text=None):
    """流式生成单个文本段的音频，边生成边播放/收集"""
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

    gen = model._generate(text=text, **gen_kwargs)
    chunk_count = 0
    for wav_chunk in gen:
        chunk_count += 1
        if player:
            player.put(wav_chunk)
        if file_chunks is not None:
            file_chunks.append(wav_chunk)
        sys.stdout.write(".")
        sys.stdout.flush()
    return chunk_count


def main():
    args = parse_args()
    apply_args(args)

    if SEED >= 0:
        torch.manual_seed(SEED)
        np.random.seed(SEED)

    # voice_design 模式自动处理
    text = TEXT
    if MODE == "voice_design" and not text.strip().startswith("("):
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

    # 长文本分段
    segments = split_text(text, MAX_CHARS_PER_SEGMENT)
    print(f"模式: {MODE}  语种: {LANGUAGE}  播放: {PLAY}  保存: {OUTPUT or '无'}")
    print(f"文本: {text}")
    if len(segments) > 1:
        seg_preview = [s[:20] + "..." if len(s) > 20 else s for s in segments]
        print(f"分为 {len(segments)} 段: {seg_preview}")
    print(f"模型: {MODEL_PATH}  CFG: {CFG_VALUE}  步数: {INFERENCE_TIMESTEPS}  种子: {SEED}")

    # 加载模型
    print("正在加载模型...")
    from voxcpm import VoxCPM
    t0 = time.time()
    model = VoxCPM.from_pretrained(MODEL_PATH, load_denoiser=False)
    sample_rate = model.tts_model.sample_rate
    print(f"模型加载完成 ({time.time()-t0:.1f}s)  采样率: {sample_rate}")

    # clone / ultimate_clone 参数
    ref_wav = REFERENCE_WAV if MODE == "clone" else None
    prompt_wav = PROMPT_WAV if MODE == "ultimate_clone" else None
    prompt_text = PROMPT_TEXT if MODE == "ultimate_clone" else None
    if MODE == "ultimate_clone" and REFERENCE_WAV:
        ref_wav = REFERENCE_WAV

    if MODE == "clone":
        if not REFERENCE_WAV:
            raise ValueError("clone 模式需要指定 --reference-wav")
        print(f"参考音频: {REFERENCE_WAV}")
    elif MODE == "ultimate_clone":
        if not PROMPT_WAV or not PROMPT_TEXT:
            raise ValueError("ultimate_clone 模式需要 --prompt-audio 和 --prompt-text")
        print(f"提示音频: {PROMPT_WAV}")
        print(f"提示文本: {PROMPT_TEXT}")

    # 初始化播放器
    player = None
    if PLAY:
        player = AudioPlayer(sample_rate)
        player.start()

    file_chunks = [] if OUTPUT else None
    total_t0 = time.time()
    total_chunks = 0

    # 逐段流式生成
    for i, seg in enumerate(segments):
        print(f"\n[段 {i+1}/{len(segments)}] ", end="")
        seg_t0 = time.time()
        chunk_count = stream_segment(
            model, seg, sample_rate, player=player, file_chunks=file_chunks,
            cfg_value=CFG_VALUE, inference_timesteps=INFERENCE_TIMESTEPS,
            max_len=MAX_LEN, reference_wav_path=ref_wav,
            prompt_wav_path=prompt_wav, prompt_text=prompt_text,
        )
        seg_elapsed = time.time() - seg_t0
        print(f" {chunk_count} 块, {seg_elapsed:.1f}s")
        total_chunks += chunk_count

    # 通知播放器结束
    if player:
        player.signal_end()

    total_elapsed = time.time() - total_t0

    # 保存完整 WAV
    if OUTPUT and file_chunks:
        full_wav = np.concatenate(file_chunks)
        os.makedirs(os.path.dirname(OUTPUT) or ".", exist_ok=True)
        sf.write(OUTPUT, full_wav, sample_rate)
        duration = len(full_wav) / sample_rate
        print(f"\n保存: {OUTPUT}  时长: {duration:.1f}s  块数: {total_chunks}")

    if player:
        player.wait()
        print("播放完成")

    print(f"总耗时: {total_elapsed:.1f}s  总块数: {total_chunks}")


if __name__ == "__main__":
    main()
