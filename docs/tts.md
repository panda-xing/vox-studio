# TTS 语音合成 - 使用说明

基于 OpenBMB VoxCPM2（2B 参数 Tokenizer-Free TTS）的本地语音合成工具。

## 使用方式

### 方式一：修改脚本顶部参数

打开 `tts.py`，修改顶部默认参数后运行 `python tts.py`。

### 方式二：命令行参数

```bash
# 基础合成
python tts.py --text "你好世界" --output output/hello.wav

# Voice Design
python tts.py --text "(中年男性，沉稳有力)各位代表，现在开会。" --mode voice_design

# 英文
python tts.py --text "Hello world" --language en

# 声音克隆
python tts.py --text "欢迎来到直播间" --reference-wav "刘娜录音.wav" --mode clone

# 极致克隆
python tts.py --text "今天天气真好" \
  --prompt-audio "D:\codes\VoxCPM2\刘娜录音.wav" \
  --prompt-text "喜茶好好卖奶茶不行吗，非要塞点垃圾给我，花里胡哨的，搞不清楚在干啥" \
  --mode ultimate_clone

# 调整参数
python tts.py --text "你好" --cfg-value 3.0 --inference-timesteps 20 --seed 42
```

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--text` | 顶部 TEXT | 要合成的文本 |
| `--output` | `output/output.wav` | 输出 wav 文件路径 |
| `--mode` | `basic` | 模式：`basic` / `voice_design` / `clone` / `ultimate_clone` |
| `--language` | `zh` | 语种：`zh`/`en`/`ja`/`ko`/`fr`/`de` 等 |
| `--model-path` | `D:/models/VoxCPM2` | 模型路径 |
| `--reference-wav` | 刘娜录音.wav | 参考音频路径（clone 模式） |
| `--prompt-audio` | 刘娜录音.wav | 提示音频路径（ultimate_clone 模式） |
| `--prompt-text` | 刘娜录音文案 | 提示音频对应文本（ultimate_clone 模式） |
| `--cfg-value` | `2.0` | 引导强度，越大越贴近文本 |
| `--inference-timesteps` | `10` | 推理步数，越多质量越高 |
| `--max-len` | `4096` | 最大生成长度 |
| `--seed` | `-1` | 随机种子，`-1` 不固定 |

## 四种合成模式

### basic - 基础合成
直接将文本转为语音，无需参考音频。

### voice_design - 声音设计
用自然语言描述创建全新声音：
- 文本自带描述：`"(年轻女性，温柔)欢迎收听！"`
- 不带描述时根据 `--language` 自动添加默认描述

### clone - 可控声音克隆
从参考音频克隆音色，可叠加风格控制：
```bash
python tts.py --text "(语速稍快)克隆语音" --reference-wav "刘娜录音.wav" --mode clone
```

### ultimate_clone - 极致克隆
提供参考音频 + 对应文本，完整复刻音色、节奏、情绪、风格：
```bash
python tts.py --text "新文本" \
  --prompt-audio "D:\codes\VoxCPM2\刘娜录音.wav" \
  --prompt-text "喜茶好好卖奶茶不行吗，非要塞点垃圾给我，花里胡哨的，搞不清楚在干啥" \
  --mode ultimate_clone
```

### clone vs ultimate_clone

| 对比项 | clone | ultimate_clone |
|--------|-------|----------------|
| 所需输入 | 参考音频 | 参考音频 + 对应文案 |
| 音色还原 | ✅ | ✅ |
| 情绪/节奏 | ❌ | ✅ |
| 还原度 | 高 | 更高 |

## 内置参考音色

`刘娜录音.wav`（48kHz / 10s），文案：`喜茶好好卖奶茶不行吗，非要塞点垃圾给我，花里胡哨的，搞不清楚在干啥`

## Voice Design 描述示例

```python
"(A middle-aged man, deep and authoritative voice)各位代表，现在开始开会。"
"(A young woman, cheerful and energetic voice)今天天气真好，一起去散步吧！"
"(An elderly man, slow and gentle voice)孩子们，过来听爷爷讲故事。"
```

## 支持语种

30 种语言自动识别（中英日韩法德等），中文方言支持：四川话、粤语、吴语、东北话、河南话、陕西话、山东话、天津话、闽南话。

## 性能参考（RTX 5060 Ti 16GB）

| 模式 | 文本 | 耗时 | 音频时长 | RTF |
|------|------|------|----------|-----|
| basic | ~15字 | ~4s | ~5s | ~0.8 |
| clone | ~25字 | ~7.7s | ~6.2s | ~1.2 |
| ultimate_clone | ~25字 | ~7.2s | ~5.6s | ~1.3 |

## 常见问题

**生成结果不稳定？** 用 `--seed` 固定种子，或生成 1-3 次选最佳。

**显存不够？** VoxCPM2 需 ~8GB VRAM，可用 VoxCPM1.5（~6GB）或 VoxCPM-0.5B（~5GB）。

**调整质量/速度？** 提高：增大 `--inference-timesteps` 和 `--cfg-value`；加快：减小步数。

**参考音频要求？** 5-15秒，16kHz+，无噪声。ultimate_clone 的文案必须与音频内容一致。

**clone 和 ultimate_clone 怎么选？** 只需音色用 clone，需要复刻情绪风格用 ultimate_clone。
