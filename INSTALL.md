# VoxCPM2 安装部署指南

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
| Windows | 10 / 11 64 位 |

> ⚠️ RTX 50 系列显卡（Blackwell 架构）需要 PyTorch ≥ 2.9.0 + CUDA 12.8，否则会报 `no kernel image is available` 错误。

## 第一步：检查 GPU 和 CUDA

```bash
nvidia-smi
```

确认显示 CUDA Version ≥ 12.0。记下 CUDA 版本号，后续安装 PyTorch 需要用到。

## 第二步：创建 Python 环境

推荐使用 conda 创建独立环境：

```bash
conda create -n py312 python=3.12 -y
conda activate py312
```

也可以用其他方式管理 Python 3.10-3.12 的环境，只要版本在范围内即可。

## 第三步：安装 PyTorch

根据 CUDA 版本选择对应的安装命令：

### CUDA 12.8（RTX 50 系列）

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
```

### CUDA 12.4

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

### CUDA 12.1

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

验证安装：

```bash
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

应输出版本号和 `True`。

## 第四步：安装 VoxCPM

```bash
pip install voxcpm
```

> 如果安装报错，尝试：
> ```bash
> pip install voxcpm --no-build-isolation
> ```

## 第五步：下载模型权重

### 方式一：ModelScope（国内推荐）

```bash
pip install modelscope
```

```python
from modelscope import snapshot_download
snapshot_download("OpenBMB/VoxCPM2", local_dir="D:/models/VoxCPM2")
```

### 方式二：HuggingFace 自动下载

首次运行时自动拉取，国内网络可能较慢：

```python
from voxcpm import VoxCPM
model = VoxCPM.from_pretrained("openbmb/VoxCPM2")
```

### 方式三：手动下载

- HuggingFace：https://huggingface.co/openbmb/VoxCPM2
- ModelScope：https://modelscope.cn/models/OpenBMB/VoxCPM2

下载后放到本地目录（如 `D:\models\VoxCPM2\`）。

## 第六步：验证安装

```bash
python -c "
from voxcpm import VoxCPM
import soundfile as sf
model = VoxCPM.from_pretrained('D:/models/VoxCPM2', load_denoiser=False)
wav = model.generate(text='安装验证成功', cfg_value=2.0, inference_timesteps=10)
sf.write('test.wav', wav, model.tts_model.sample_rate)
print('安装成功！')
"
```

看到 `安装成功！` 并生成 `test.wav` 即表示部署完成。

## 常见安装问题

### Q: `no kernel image is available for execution on the device`

PyTorch 版本不支持当前 GPU 架构。RTX 50 系列（Blackwell）需要：

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
```

### Q: `Could not load this library: _torchaudio.pyd`

torchaudio 版本与 torch 不匹配，需要安装同一 CUDA 版本的 torchaudio：

```bash
pip install --force-reinstall torchaudio --index-url https://download.pytorch.org/whl/cu128
```

将 `cu128` 替换为你实际的 CUDA 版本。

### Q: `ModuleNotFoundError: No module named 'soundfile'`

当前不在正确的 conda 环境，先激活：

```bash
conda activate py312
```

### Q: Python 3.13 安装 VoxCPM 报错

VoxCPM 不支持 Python 3.13，请使用 3.10-3.12：

```bash
conda create -n py312 python=3.12 -y
conda activate py312
```

### Q: 国内下载模型太慢

使用 ModelScope 下载，参见第五步方式一。

### Q: Windows 上编译依赖报错

确保安装了 Visual C++ Build Tools：
- 下载地址：https://visualstudio.microsoft.com/visual-cpp-build-tools/
- 安装时勾选"使用 C++ 的桌面开发"工作负载
