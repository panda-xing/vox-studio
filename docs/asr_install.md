# ASR 语音识别 - 安装指南

## 前提条件

ASR 依赖与 TTS 共享同一 Python 环境，如果你已安装 TTS，只需额外安装 FunASR。

> 如果你还未搭建基础环境，请先参考 [TTS 安装指南](tts_install.md)。

## 安装 FunASR

```bash
conda activate py312
pip install funasr
```

FunASR 依赖的 `modelscope` 和 `torch` 已随 VoxCPM 安装，无需重复安装。

## 模型下载

模型会在首次运行时自动从 ModelScope 下载（国内源，速度较快）：

| 模型 | 用途 | 大小 |
|------|------|------|
| `paraformer-zh` | 中文语音识别 | ~950MB |
| `paraformer-en` | 英文语音识别 | ~950MB |
| `fsmn-vad` | VAD 语音活动检测 | 较小 |
| `ct-punc` | 自动标点 | ~1GB |

模型缓存路径：`C:\Users\<用户名>\.cache\modelscope\hub\`

## 单独安装（从零开始）

如果你只需要 ASR 功能：

### 1. 创建环境

```bash
conda create -n py312 python=3.12 -y
conda activate py312
```

### 2. 安装 PyTorch

```bash
# CUDA 12.8（RTX 50 系列）
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128

# CUDA 12.4
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124
```

### 3. 安装 FunASR

```bash
pip install funasr modelscope soundfile
```

### 4. 验证

```bash
python asr.py --input 刘娜录音.wav
```

看到识别结果即安装成功。

## 常见问题

**`ModuleNotFoundError: No module named 'funasr'`** — 未在正确环境，先 `conda activate py312`。

**模型下载失败？** 检查网络连接，ModelScope 国内源通常稳定。

**CUDA out of memory？** ASR 模型较小，一般不会出现。如遇问题，关闭 VAD 可减少显存：`--no-vad`。

**CPU 推理？** FunASR 默认使用 GPU，如需 CPU：
```python
model = AutoModel(model="paraformer-zh", device="cpu")
```

