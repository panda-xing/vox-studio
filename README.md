# VoxCPM2 语音合成项目

基于 OpenBMB VoxCPM2（2B 参数 Tokenizer-Free TTS）的本地语音合成工具，支持 30 种语言、Voice Design、声音克隆等功能。

## 环境要求

| 项目 | 要求 |
|------|------|
| GPU | NVIDIA GPU，VRAM ≥ 8GB |
| Python | 3.10 - 3.12 |
| PyTorch | ≥ 2.5.0 (CUDA) |
| CUDA | ≥ 12.0 |

### 快速激活环境

```bash
conda activate py312
cd D:\codes\VoxCPM2
```

## 模型位置

模型已下载到 `D:\models\VoxCPM2\`，脚本默认读取该路径。

## 项目文件

| 文件 | 说明 | 路径 |
|------|------|
| `tts.py` | 语音合成脚本（支持命令行 + 顶部参数） | 根目录 |
| `README.md` | 本使用说明 | 根目录 |
| `刘娜录音.wav` | 参考音色样本（48kHz / 10s，文案见下方） | 根目录 |
| `clone_liuna_1.wav` | clone 模式 - 克隆刘娜音色（直播间话术） | output/ |
| `clone_liuna_2.wav` | clone 模式 - 克隆刘娜音色（新闻播报） | output/ |
| `clone_liuna_3.wav` | clone 模式 - 克隆刘娜音色（结束语） | output/ |
| `ultimate_clone_liuna.wav` | ultimate_clone 模式 - 极致克隆刘娜音色 | output/ |

## 使用方式

### 方式一：修改脚本顶部参数后运行

打开 `tts.py`，修改顶部默认参数：

```python
TEXT = "你好，欢迎使用VoxCPM2语音合成系统。"    # 要合成的文本
OUTPUT = "output.wav"                            # 输出文件路径
MODE = "basic"                                   # 模式
LANGUAGE = "zh"                                  # 语种
REFERENCE_WAV = "刘娜录音.wav"                    # 参考音频（clone 模式）
PROMPT_WAV = "刘娜录音.wav"                       # 提示音频（ultimate_clone 模式）
PROMPT_TEXT = "喜茶好好卖奶茶不行吗，非要塞点垃圾给我，花里胡哨的，搞不清楚在干啥"  # 提示音频文案
CFG_VALUE = 2.0                                  # 引导强度
INFERENCE_TIMESTEPS = 10                          # 推理步数
```

然后运行：

```bash
python tts.py
```

### 方式二：命令行参数调用

```bash
# 基础中文合成
python tts.py --text "你好世界" --output out.wav

# Voice Design - 用自然语言描述声音
python tts.py --text "欢迎收听今天的节目" --mode voice_design

# Voice Design - 自定义描述（括号内为声音描述）
python tts.py --text "(中年男性，沉稳有力)各位代表，现在开会。" --mode voice_design

# 英文合成
python tts.py --text "Hello, this is a demo." --language en

# 日文合成
python tts.py --text "こんにちは、音声合成のデモです。" --language ja

# 声音克隆（需提供参考音频）
python tts.py --text "这是克隆语音。" --reference ref.wav --mode clone

# 极致克隆（需提供音频+对应文本）
python tts.py --text "极致克隆演示" --prompt-audio ref.wav --prompt-text "参考音频文本" --mode ultimate_clone

# 调整生成参数
python tts.py --text "你好" --cfg-value 3.0 --inference-timesteps 20 --output hq.wav

# 固定随机种子（可复现结果）
python tts.py --text "你好" --seed 42
```

## 声音克隆 - 使用参考音色

项目内置了 `刘娜录音.wav` 作为参考音色样本，文案为：

> 喜茶好好卖奶茶不行吗，非要塞点垃圾给我，花里胡哨的，搞不清楚在干啥

### clone 模式（克隆音色）

只需提供参考音频，模型会克隆其音色：

```bash
# 用刘娜的音色合成新文本
python tts.py --text "大家好，欢迎来到我们的直播间。" --reference-wav "刘娜录音.wav" --mode clone --output clone_demo.wav

# 克隆 + 风格控制（括号内描述风格）
python tts.py --text "(语速稍快，语气愉快)感谢大家的关注和支持！" --reference-wav "刘娜录音.wav" --mode clone
```

### ultimate_clone 模式（极致克隆）

提供参考音频 + 对应文案，完整复刻音色、节奏、情绪、风格，比 clone 模式还原度更高：

```bash
python tts.py --text "今天天气真好，一起出去走走吧。" \
  --prompt-audio "D:\codes\VoxCPM2\刘娜录音.wav" \
  --prompt-text "喜茶好好卖奶茶不行吗，非要塞点垃圾给我，花里胡哨的，搞不清楚在干啥" \
  --mode ultimate_clone \
  --output ultimate_demo.wav
```

> ⚠️ `--prompt-audio` 建议使用绝对路径，避免中文文件名编码问题。

### clone vs ultimate_clone 区别

| 对比项 | clone | ultimate_clone |
|--------|-------|----------------|
| 所需输入 | 参考音频 | 参考音频 + 对应文案 |
| 音色还原 | 克隆音色 | 克隆音色 |
| 情绪/节奏 | 不复刻 | 完整复刻 |
| 还原度 | 高 | 更高 |
| 适用场景 | 只需音色即可 | 需要复刻说话风格和情绪 |

### 自定义参考音频

你也可以使用自己的音频作为参考音色：

```bash
# clone 模式
python tts.py --text "你想合成的文本" --reference-wav "你的音频.wav" --mode clone --output out.wav

# ultimate_clone 模式
python tts.py --text "你想合成的文本" \
  --prompt-audio "D:\codes\你的音频.wav" \
  --prompt-text "你音频里说的那句话的文字" \
  --mode ultimate_clone \
  --output out.wav
```

参考音频建议：
- 时长 5-15 秒效果最佳
- 采样率 16kHz 以上均可，VoxCPM2 会自动处理
- 尽量干净、无背景噪声
- 说话人声音清晰、自然
- ultimate_clone 的 `--prompt-text` 必须与音频内容一致

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--text` | 顶部 TEXT | 要合成的文本 |
| `--output` | `output.wav` | 输出 wav 文件路径 |
| `--mode` | `basic` | 合成模式：`basic` / `voice_design` / `clone` / `ultimate_clone` |
| `--language` | `zh` | 语种提示：`zh`/`en`/`ja`/`ko`/`fr`/`de` 等 |
| `--model-path` | `D:/models/VoxCPM2` | 模型路径 |
| `--reference-wav` | 无 | 参考音频路径（clone 模式） |
| `--prompt-audio` | 无 | 提示音频路径（ultimate_clone 模式） |
| `--prompt-text` | 无 | 提示音频对应文本（ultimate_clone 模式） |
| `--cfg-value` | `2.0` | 引导强度，越大越贴近文本，越小越自由 |
| `--inference-timesteps` | `10` | 推理步数，越多质量越高但越慢 |
| `--max-len` | `4096` | 最大生成长度 |
| `--seed` | `-1` | 随机种子，`-1` 不固定 |

## 四种合成模式

### basic - 基础合成
直接将文本转为语音，无需参考音频。适合快速生成。

### voice_design - 声音设计
用自然语言描述创建全新声音。两种写法：
- 文本自带描述：`"(年轻女性，温柔)欢迎收听！"`
- 不带描述时根据 `--language` 自动添加默认声音描述

### clone - 可控声音克隆
从参考音频克隆音色，可叠加风格控制：
```bash
python tts.py --text "(语速稍快)克隆语音" --reference "刘娜录音.wav" --mode clone
```

### ultimate_clone - 极致克隆
提供参考音频 + 对应文本，完整复刻音色、节奏、情绪、风格：
```bash
python tts.py --text "今天天气真好，一起出去走走吧。" \
  --prompt-audio "D:\codes\VoxCPM2\刘娜录音.wav" \
  --prompt-text "喜茶好好卖奶茶不行吗，非要塞点垃圾给我，花里胡哨的，搞不清楚在干啥" \
  --mode ultimate_clone
```

## 支持的语种

中文、英语、日语、韩语、法语、德语等 30 种语言，无需语言标签即可自动识别。

中文方言：四川话、粤语、吴语、东北话、河南话、陕西话、山东话、天津话、闽南话。

## Voice Design 描述示例

```python
# 中年男性，沉稳有力
"(A middle-aged man, deep and authoritative voice)各位代表，现在开始开会。"

# 年轻女性，活泼开朗
"(A young woman, cheerful and energetic voice)今天天气真好，一起去散步吧！"

# 老年男性，缓慢温和
"(An elderly man, slow and gentle voice)孩子们，过来听爷爷讲故事。"
```

## 性能参考（RTX 5060 Ti 16GB）

| 场景 | 文本 | 生成耗时 | 音频时长 | RTF |
|------|------|----------|----------|-----|
| basic | ~15字 | ~4s | ~5s | ~0.8 |
| basic | ~30字 | ~4.5s | ~5s | ~0.9 |
| clone（刘娜） | ~25字 | ~7.7s | ~6.2s | ~1.2 |
| clone（刘娜） | ~15字 | ~3.8s | ~4.2s | ~0.9 |
| clone（刘娜） | ~15字 | ~4.3s | ~4.6s | ~0.9 |
| ultimate_clone（刘娜） | ~25字 | ~7.2s | ~5.6s | ~1.3 |

## 常见问题

**Q: 生成结果不稳定？**
Voice Design 和可控克隆结果可能因运行次数不同而变化，建议生成 1-3 次选取最佳，或用 `--seed` 固定种子。

**Q: 显存不够？**
VoxCPM2 需要 ~8GB VRAM，可用 VoxCPM1.5（~6GB）或 VoxCPM-0.5B（~5GB）替代。

**Q: 国内下载模型慢？**
使用 ModelScope 下载：
```python
from modelscope import snapshot_download
snapshot_download("OpenBMB/VoxCPM2", local_dir="./VoxCPM2")
```

**Q: 调整语音质量和速度的权衡？**
- 提高质量：增大 `--inference-timesteps`（如 20）和 `--cfg-value`（如 3.0）
- 加快速度：减小 `--inference-timesteps`（如 5）

**Q: 参考音频有什么要求？**
- 时长 5-15 秒效果最佳
- 采样率 16kHz 以上均可
- 尽量干净、无背景噪声
- 说话人声音清晰、自然
- ultimate_clone 的 `--prompt-text` 必须与音频内容一致

**Q: clone 和 ultimate_clone 怎么选？**
- 只需要音色 → 用 clone
- 需要复刻情绪、节奏、说话风格 → 用 ultimate_clone
- ultimate_clone 必须提供音频对应的文案，文案不准会影响效果


