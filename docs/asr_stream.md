# 流式 ASR 语音识别 - 使用说明

基于阿里达摩院 FunASR（Paraformer Streaming）的流式语音识别工具，支持麦克风实时采集和长音频边读边识别。

## 使用方式

### 麦克风实时识别

``bash
# 默认中文流式识别
python asr_stream.py --mic

# 英文流式识别
python asr_stream.py --mic --language en

# 调整每块时长
python asr_stream.py --mic --chunk-ms 400

# 不显示中间结果
python asr_stream.py --mic --no-partial
``

### 长音频边读边识别

``bash
# 边读边识别
python asr_stream.py --input long.wav

# 保存识别结果
python asr_stream.py --input long.wav --output output/stream_result.txt

# JSON 格式输出
python asr_stream.py --input long.wav --format json --output output/result.json
``

### 无参数默认麦克风

``bash
# 不带任何参数默认进入麦克风模式
python asr_stream.py
``

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| --input | 无 | 输入音频文件路径（长音频边读边识别） |
| --output | 无 | 输出文件路径（留空仅打印） |
| --mic | 默认启用 | 麦克风实时采集模式 |
| --language | zh | 语种：zh/en |
| --chunk-ms | 600 | 每块时长毫秒数 |
| --mic-device | 默认设备 | 麦克风设备索引 |
| --no-partial | 显示 | 不显示中间结果 |
| --format | 	ext | 输出格式：	ext / json |

## 流式工作原理

### 麦克风模式

1. 以 16kHz 采样率实时采集音频
2. 每 --chunk-ms 毫秒送入流式模型
3. 模型返回累计识别文本（中间结果）
4. 按 Ctrl+C 停止录音，发送 is_final 获取最终结果

### 文件模式

1. 读取音频文件并预处理为 16kHz 单声道
2. 按固定块大小逐块送入流式模型
3. 每块返回当前累计识别文本
4. 最后一块 is_final=True 结束识别

### 中间结果与最终结果

- **中间结果**：流式模型持续输出累计文本，随着更多音频输入逐步修正
- **最终结果**：is_final=True 后模型完成当前识别段，输出最终文本

## 与 asr.py 的区别

| 对比项 | asr.py | asr_stream.py |
|--------|--------|---------------|
| 模型 | paraformer-zh | paraformer-zh-streaming |
| 输入方式 | 完整音频文件 | 逐块流式输入 |
| 麦克风 | 不支持 | 实时采集 + 识别 |
| 中间结果 | 无 | 显示累计文本 |
| 实时性 | 离线处理 | 实时逐句输出 |
| 准确度 | 更高（非流式模型更准） | 略低（流式模型折衷） |

## 依赖

除 sr.py 的依赖外，还需安装：

``bash
pip install sounddevice
``

## 常见问题

**麦克风无声音？** 检查麦克风设备索引，使用 --mic-device 指定正确设备。

**识别速度慢？** 减小 --chunk-ms（如 400ms），但太短可能影响准确度。

**中间结果闪烁？** 使用 --no-partial 只显示最终结果。

**比 asr.py 准确度低？** 流式模型天然折衷了准确度换取实时性，对准确度要求高的场景请使用 sr.py。

**英文识别？** 使用 --language en 切换到英文流式模型。