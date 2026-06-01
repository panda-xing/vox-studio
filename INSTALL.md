# Vox Studio 安装部署指南

## 硬件要求

| 项目 | 最低要求 | 推荐 |
|------|----------|------|
| GPU | NVIDIA GPU，VRAM ≥ 8GB | RTX 4090 / RTX 3090 |
| 内存 | 16 GB | 32 GB |
| 硬盘 | 25 GB 可用空间 | SSD |

## 软件要求

| 项目 | 版本要求 |
|------|----------|
| Python | ≥ 3.10 且 < 3.13 |
| PyTorch | ≥ 2.5.0（CUDA 版本） |
| CUDA | ≥ 12.0 |
| Windows | 10 / 11 64 位 |

> ⚠️ RTX 50 系列显卡（Blackwell 架构）需要 PyTorch ≥ 2.9.0 + CUDA 12.8。

## 第一步：检查 GPU 和 CUDA

```bash
nvidia-smi
```

确认 CUDA Version ≥ 12.0。

## 第二步：创建 Python 环境

```bash
conda create -n py312 python=3.12 -y
conda activate py312
```

## 第三步：安装 PyTorch

| CUDA 版本 | 安装命令 |
|-----------|----------|
| 12.8（RTX 50 系列） | `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128` |
| 12.4 | `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124` |
| 12.1 | `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121` |

验证：`python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"`

## 第四步：安装依赖

```bash
# TTS 语音合成
pip install voxcpm

# ASR 语音识别
pip install funasr

# 共同依赖（通常已自动安装）
pip install modelscope soundfile
```

## 第五步：下载模型

### TTS 模型（VoxCPM2，~4.6GB）

```python
from modelscope import snapshot_download
snapshot_download("OpenBMB/VoxCPM2", local_dir="D:/models/VoxCPM2")
```

### ASR 模型（FunASR，首次运行自动下载）

| 模型 | 用途 | 大小 |
|------|------|------|
| `paraformer-zh` | 中文识别 | ~950MB |
| `fsmn-vad` | VAD | 较小 |
| `ct-punc` | 自动标点 | ~1GB |

缓存路径：`C:\Users\<用户名>\.cache\modelscope\hub\`

## 第六步：验证安装

```bash
# 验证 TTS
python tts.py --text "安装验证成功" --output output/test_tts.wav

# 验证 ASR
python asr.py --input 刘娜录音.wav --output output/test_asr.txt
```

TTS 生成音频文件、ASR 输出识别文本即表示安装成功。

## 常见问题

**`no kernel image is available`** — RTX 50 系列需 PyTorch cu128：
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
```

**`Could not load _torchaudio.pyd`** — torchaudio 版本不匹配：
```bash
pip install --force-reinstall torchaudio --index-url https://download.pytorch.org/whl/cu128
```

**Python 3.13 不兼容** — VoxCPM 不支持 3.13，请用 3.10-3.12。

**国内下载模型慢** — 使用 ModelScope 下载（已在上文使用）。

**Windows 编译报错** — 安装 [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)，勾选"使用 C++ 的桌面开发"。
