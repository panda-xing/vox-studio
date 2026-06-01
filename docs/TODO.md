# Vox Studio - 后续完善计划

## 流式功能

### 流式 TTS 语音合成 (`tts_stream.py`)

- [ ] 基于 VoxCPM2 的 `streaming=True` 参数实现逐 chunk 生成
- [ ] 实时播放：每生成一个音频片段立即播放，无需等待全部完成
- [ ] 支持长文本分段合成，避免显存溢出
- [ ] CLI 模式：`python tts_stream.py --text "长文本..." --play`
- [ ] 保存模式：流式生成同时保存完整 wav
- [ ] WebSocket 服务：供其他应用实时调用

**参考接口：**
```python
model = VoxCPM.from_pretrained("D:/models/VoxCPM2", load_denoiser=False)
for chunk in model.generate(text="...", streaming=True):
    # chunk: numpy ndarray，逐片段返回
    play_audio(chunk)
```

### 流式 ASR 语音识别 (`asr_stream.py`)

- [ ] 基于 FunASR 的 `paraformer-zh-streaming` 模型实现实时识别
- [ ] 麦克风实时采集 + 逐句识别输出
- [ ] 长音频文件流式识别，边读边识别
- [ ] 支持中间结果展示（partial result）
- [ ] CLI 模式：`python asr_stream.py --mic`（麦克风实时识别）
- [ ] CLI 模式：`python asr_stream.py --input long.wav`（长音频流式）
- [ ] WebSocket 服务：供其他应用实时调用

**参考接口：**
```python
model = AutoModel(model="paraformer-zh-streaming", ...)
# 流式识别，逐 chunk 输出
```

## 其他待完善

- [ ] tts.py / asr.py 批量处理模式（读取文件列表批量合成/识别）
- [ ] Web UI 界面（Gradio）：TTS 合成 + ASR 识别一站式操作
- [ ] tts.py 支持 Nano-vLLM 加速（RTF 从 ~0.3 降至 ~0.13）
- [ ] asr.py 支持说话人分离（Speaker Diarization）
- [ ] Docker 部署方案
- [ ] 配置文件支持（YAML/JSON），避免频繁修改脚本参数
