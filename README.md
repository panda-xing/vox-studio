# Vox Studio - 语音工坊

本地 TTS 语音合成 & ASR 语音识别工具集。

## 功能

| 功能 | 引擎 | 说明 |
|------|------|------|
| TTS 语音合成 | VoxCPM2 (2B) | 30 种语言、Voice Design、声音克隆、极致克隆 |
| ASR 语音识别 | FunASR (Paraformer) | 50+ 语言、自动标点、VAD、实时识别 |

## 快速开始

```bash
conda activate py312
cd D:\codes\VoxCPM2

# TTS 语音合成
python tts.py --text "你好世界" --output output/hello.wav

# ASR 语音识别
python asr.py --input 刘娜录音.wav --output output/result.txt
```

## 项目结构

```
vox-studio/
├── tts.py              # TTS 语音合成脚本
├── asr.py              # ASR 语音识别脚本
├── 刘娜录音.wav         # 参考音色样本
├── output/             # 生成音频和识别结果（不入库）
└── docs/
    ├── tts.md          # TTS 使用说明
    ├── tts_install.md  # TTS 安装指南
    ├── asr.md          # ASR 使用说明
    └── asr_install.md  # ASR 安装指南
```

## 文档

- [TTS 使用说明](docs/tts.md)
- [TTS 安装指南](docs/tts_install.md)
- [ASR 使用说明](docs/asr.md)
- [ASR 安装指南](docs/asr_install.md)

## 环境要求

| 项目 | 要求 |
|------|------|
| GPU | NVIDIA GPU，VRAM ≥ 8GB |
| Python | 3.10 - 3.12 |
| PyTorch | ≥ 2.5.0 (CUDA) |
| CUDA | ≥ 12.0 |

## 参考项目

| 项目 | Stars | 说明 |
|------|-------|------|
| [OpenBMB/VoxCPM](https://github.com/OpenBMB/VoxCPM) | 23.7k | TTS 语音合成引擎，2B 参数 Tokenizer-Free |
| [modelscope/FunASR](https://github.com/modelscope/FunASR) | 16.7k | 阿里达摩院 ASR 工具集，工业级语音识别 |
| [FunAudioLLM/SenseVoice](https://github.com/FunAudioLLM/SenseVoice) | 8.4k | 轻量级 ASR，15x faster than Whisper |
| [m-bain/whisperX](https://github.com/m-bain/whisperX) | 22.1k | Whisper 增强版，词级时间戳 + 说话人分离 |

## 许可

- VoxCPM2: Apache-2.0
- FunASR: MIT
