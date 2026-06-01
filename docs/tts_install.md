# TTS 语音合成 - 安装指南

## 硬件要求

| 项目 | 最低要求 | 推荐 |
|------|----------|------|
| GPU | NVIDIA GPU，VRAM ≥ 8GB | RTX 4090 / RTX 3090 |
| 内存 | 16 GB | 32 GB |
| 硬盘 | 20 GB 可用空间 | SSD |

## 软件要求

| 项目 | 版本要求 |
|------|----------|
| Python | ≥ 3.10 且 < 3.13 |
| PyTorch | ≥ 2.5.0（CUDA 版本） |
| CUDA | ≥ 12.0 |

> ⚠️ RTX 50 系列（Blackwell 架构）需要 PyTorch ≥ 2.9.0 + CUDA 12.8。

## 安装步骤

### 1. 检查 GPU 和 CUDA

```bash
nvidia-smi
```

### 2. 创建 Python 环境

```bash
conda create -n py312 python=3.12 -y
conda activate py312
```

### 3. 安装 PyTorch

```bash
# CUDA 12.8（RTX 50 系列）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# CUDA 12.4
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

验证：`python -c "import torch; print(torch.cuda.is_available())"`

### 4. 安装 VoxCPM

```bash
pip install voxcpm
```

> 报错时尝试：`pip install voxcpm --no-build-isolation`

### 5. 下载模型

```python
# ModelScope（国内推荐）
from modelscope import snapshot_download
snapshot_download("OpenBMB/VoxCPM2", local_dir="D:/models/VoxCPM2")
```

也可从 HuggingFace 下载：https://huggingface.co/openbmb/VoxCPM2

### 6. 验证

```bash
python tts.py --text "安装验证成功" --output test.wav
```

## 常见问题

**`no kernel image is available`** — PyTorch 版本不支持 GPU 架构，RTX 50 系列需 cu128。

**`Could not load _torchaudio.pyd`** — torchaudio 与 torch 版本不匹配：
```bash
pip install --force-reinstall torchaudio --index-url https://download.pytorch.org/whl/cu128
```

**Python 3.13 不兼容** — VoxCPM 不支持 3.13，请用 3.10-3.12。
