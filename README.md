# Vox Studio - 语音工坊

TTS 语音合成 & ASR 语音识别本地工具集，基于 VoxCPM2 和 FunASR 构建。

## 功能

| 功能 | 引擎 | 说明 |
|------|------|------|
| TTS 语音合成 | VoxCPM2 (2B) | 30 种语言、Voice Design、声音克隆、极致克隆 |
| ASR 语音识别 | FunASR (Paraformer) | 50+ 语言、自动标点、VAD、实时识别 |

## 项目结构

```
vox-studio/
├── tts.py              # TTS 语音合成脚本
├── asr.py              # ASR 语音识别脚本
├── 刘娜录音.wav         # 参考音色样本
├── output/             # 生成音频和识别结果（已屏蔽入库）
├── docs/
│   ├── tts.md          # TTS 使用说明
│   ├── tts_install.md  # TTS 安装指南
│   ├── asr.md          # ASR 使用说明
│   └── asr_install.md  # ASR 安装指南
└── INSTALL.md          # 完整安装指南（含 TTS + ASR）
```

## 快速开始

```bash
conda activate py312
cd D:\codes\VoxCPM2

# TTS 语音合成
python tts.py --text "你好世界" --output output/hello.wav

# ASR 语音识别
python asr.py --input 刘娜录音.wav --output output/result.txt
```

## 详细文档

- [TTS 使用说明](docs/tts.md)
- [TTS 安装指南](docs/tts_install.md)
- [ASR 使用说明](docs/asr.md)
- [ASR 安装指南](docs/asr_install.md)
- [完整安装指南](INSTALL.md)（TTS + ASR）

## 环境

| 项目 | 要求 |
|------|------|
| GPU | NVIDIA GPU，VRAM ≥ 8GB |
| Python | 3.10 - 3.12 |
| PyTorch | ≥ 2.5.0 (CUDA) |
| CUDA | ≥ 12.0 |

## 许可

- VoxCPM2: Apache-2.0
- FunASR: MIT
