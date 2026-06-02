# 流式 TTS 语音合成 - 使用说明

基于 OpenBMB VoxCPM2 的流式语音合成工具，支持边生成边播放，降低用户等待感。

## 使用方式

### 方式一：修改脚本顶部参数

打开 	ts_stream.py，修改顶部默认参数后运行 python tts_stream.py。

### 方式二：命令行参数

``bash
# 基础流式合成 + 实时播放
python tts_stream.py --text "你好世界" --play

# 流式合成 + 保存到文件
python tts_stream.py --text "你好世界" --output output/stream_out.wav

# 流式合成 + 播放 + 保存
python tts_stream.py --text "很长的文本内容..." --play --output output/stream.wav

# Voice Design 流式
python tts_stream.py --text "(中年男性，沉稳有力)各位代表，现在开会。" --mode voice_design --play

# 声音克隆流式
python tts_stream.py --text "欢迎来到直播间" --reference-wav 刘娜录音.wav --mode clone --play

# 极致克隆流式
python tts_stream.py --text "今天天气真好" --prompt-audio 刘娜录音.wav --prompt-text "喜茶好好卖奶茶不行吗" --mode ultimate_clone --play
``

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| --text | 顶部 TEXT | 要合成的文本 |
| --output | 无 | 输出 wav 文件路径（留空不保存） |
| --play / --no-play | 播放 | 是否实时播放音频 |
| --mode | asic | 模式：asic / oice_design / clone / ultimate_clone |
| --language | zh | 语种：zh/en/ja/ko 等 |
| --model-path | D:/models/VoxCPM2 | 模型路径 |
| --reference-wav | 刘娜录音.wav | 参考音频路径（clone 模式） |
| --prompt-audio | 刘娜录音.wav | 提示音频路径（ultimate_clone 模式） |
| --prompt-text | 刘娜录音文案 | 提示音频对应文本（ultimate_clone 模式） |
| --cfg-value | 2.0 | 引导强度 |
| --inference-timesteps | 10 | 推理步数 |
| --max-len | 4096 | 最大生成长度 |
| --seed | -1 | 随机种子 |
| --max-chars | 80 | 长文本分段每段最大字符数 |

## 流式工作原理

### 边生成边播放

VoxCPM2 的 _generate(streaming=True) 会逐步产出音频块，每生成一块即刻送入播放线程，用户无需等待全部生成完毕。

### 长文本分段

文本超过 --max-chars（默认 80 字）时，自动按标点分段，逐段流式合成，避免显存/内存峰值过高。

### 播放线程

AudioPlayer 类在独立线程中运行 sounddevice 播放流，与生成线程通过队列解耦，互不阻塞。

## 与 tts.py 的区别

| 对比项 | tts.py | tts_stream.py |
|--------|--------|---------------|
| 生成方式 | 一次性生成完整音频 | 逐块流式生成 |
| 播放时机 | 生成完毕后播放 | 边生成边播放 |
| 长文本 | 需手动分段 | 自动分段合成 |
| 内存占用 | 全量音频驻留 | 增量式，峰值更低 |
| 保存文件 | 必须保存 | 可选保存 |

## 依赖

除 	ts.py 的依赖外，还需安装：

``bash
pip install sounddevice
``

## 常见问题

**播放有延迟？** 流式模式首块延迟约 3-5s（模型初始化 + 首块生成），后续块实时跟进。

**播放卡顿？** 减小 --inference-timesteps 或降低 --max-len，加快生成速度。

**不需要播放？** 使用 --no-play 仅保存文件，或 --output 指定保存路径。

**分段效果不好？** 调整 --max-chars，默认 80 字，可增大到 120-200。