# ASR 语音识别 - 使用说明

基于阿里达摩院 FunASR（Paraformer）的本地语音识别工具，支持 50+ 语言、自动标点、VAD 语音活动检测。

## 使用方式

### 方式一：修改脚本顶部参数

打开 `asr.py`，修改顶部默认参数后运行 `python asr.py`。

### 方式二：命令行参数

```bash
# 中文识别（默认带标点 + VAD）
python asr.py --input 刘娜录音.wav

# 识别并保存到文件
python asr.py --input audio.wav --output output/result.txt

# 不带标点
python asr.py --input audio.wav --no-punc

# 禁用 VAD
python asr.py --input audio.wav --no-vad

# 英文识别
python asr.py --input audio.wav --language en

# JSON 格式输出
python asr.py --input audio.wav --format json

# SRT 字幕格式
python asr.py --input audio.wav --format srt

# 不自动重采样（保持原采样率）
python asr.py --input audio.wav --no-resample
```

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--input` | 顶部 INPUT | 输入音频文件路径 |
| `--output` | 无（仅打印） | 输出文件路径 |
| `--language` | `zh` | 语种：`zh`/`en` 等 |
| `--model` | `paraformer-zh` | ASR 模型名称 |
| `--punc` / `--no-punc` | 启用 | 是否添加标点 |
| `--vad` / `--no-vad` | 启用 | 是否启用 VAD |
| `--format` | `text` | 输出格式：`text` / `srt` / `json` |
| `--no-resample` | 自动重采样 | 不自动重采样为 16kHz |

## 识别模式

### 中文识别（默认）

使用 `paraformer-zh` 模型，自动标点 + VAD：
```bash
python asr.py --input audio.wav
```

输出示例：
```
喜茶，好好卖奶茶不行吗？非要塞点垃圾，给我花里胡哨的，搞不清楚在干啥。
```

### 英文识别

使用 `paraformer-en` 模型：
```bash
python asr.py --input audio.wav --language en
```

### 输出格式

| 格式 | 说明 | 示例 |
|------|------|------|
| `text` | 纯文本（默认） | `喜茶，好好卖奶茶不行吗？` |
| `json` | JSON 结构化 | `{"text": "...", "timestamp": [...]}` |
| `srt` | SRT 字幕格式 | `1\n00:00:00,000 --> 00:00:03,500\n喜茶...` |

## 音频预处理

脚本自动处理：
- 双声道 → 单声道
- 任意采样率 → 16kHz（FunASR 要求）
- 无需手动转换

## 内置测试

```bash
python asr.py --input 刘娜录音.wav --output output/asr_liuna.txt
```

识别结果：`喜茶，好好卖奶茶不行吗？非要塞点垃圾，给我花里胡哨的，搞不清楚在干啥。`

## 性能参考（RTX 5060 Ti 16GB）

| 音频时长 | 识别耗时 | RTF |
|----------|----------|-----|
| 10s | ~0.6s | 0.045 |

## 常见问题

**识别结果乱码？** 终端编码问题，使用 `--output` 保存到文件即可正常显示。

**双声道音频识别不正确？** 脚本会自动转单声道，无需手动处理。

**音频格式不支持？** 支持 wav/flac 等格式，mp3 需安装 ffmpeg。

**英文识别效果不好？** 使用 `--language en` 切换英文模型。

**VAD 是什么？** Voice Activity Detection（语音活动检测），自动分割长音频中的语音段，长音频建议开启。

**标点不准确？** 标点由独立模型 `ct-punc` 生成，短句可能不够准确，可用 `--no-punc` 关闭。
