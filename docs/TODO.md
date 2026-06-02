# Vox Studio - 后续完善计划

## 当前状态

- [x] 	ts.py 已实现基础 TTS、Voice Design、clone、ultimate_clone 四种模式
- [x] sr.py 已实现 FunASR 语音识别，支持中文/英文、自动标点、VAD、	ext/json/srt 输出
- [x] 文档已补齐：docs/tts.md、docs/asr.md、docs/tts_install.md、docs/asr_install.md
- [x] README 已概述项目结构、快速使用和依赖要求
- [x] 	ts_stream.py 已实现流式 TTS：边生成边播放、长文本分段、CLI 完整
- [x] sr_stream.py 已实现流式 ASR：麦克风实时采集、长音频边读边识别、中间结果显示

## 优先开发任务

### 1. 任务化与批量处理
- [ ] 为 	ts.py 添加批量输入模式，支持 --input-list list.txt 或目录批量合成
- [ ] 为 sr.py 添加批量识别模式，支持 --input-list list.txt 或目录批量识别
- [ ] 支持 --device 参数，明确 GPU/CPU 选择
- [ ] 支持配置文件（YAML/JSON）方式加载参数，避免频繁修改脚本顶部常量

### 2. 流式功能

#### 流式 TTS 语音合成
- [x] 新增 	ts_stream.py，支持基于 VoxCPM2 的流式生成接口
- [x] 实现边生成边播放，降低用户等待感
- [x] 支持长文本分段合成，避免显存/内存峰值过高
- [x] 添加 CLI：python tts_stream.py --text "..." --play --output out.wav
- [x] 支持流式输出写入完整 WAV 文件
- [x] HTTP 服务接口已实现（tts_server.py / asr_server.py）
- [ ] 评估并补充 WebSocket 服务接口

#### 流式 ASR 语音识别
- [x] 新增 sr_stream.py，支持 paraformer-zh-streaming 流式模型
- [x] 实现麦克风实时采集 + 逐句识别输出
- [x] 支持长音频文件边读边识别
- [x] 显示中间结果（partial result）
- [x] 添加 CLI：python asr_stream.py --mic / python asr_stream.py --input long.wav
- [x] HTTP 服务接口已实现（asr_server.py）
- [ ] 评估 WebSocket 服务接口

### 3. Web UI 与用户体验
- [ ] 基于 Gradio 打通 TTS / ASR 一站式 Web UI
- [ ] 在 Web UI 中支持：文本合成、参考音频克隆、实时录音识别、结果下载
- [ ] 补充使用示例和常见问题说明

## 性能与加速

- [ ] 研究并接入 Nano-vLLM 加速 	ts.py，目标将 RTF 降低到 ~0.13
- [ ] 优化 ASR 预处理与临时文件策略，减少磁盘 I/O
- [ ] 增加显存不足时的自动降级方案或警告提示

## 进阶功能

- [ ] ASR 说话人分离 / Speaker Diarization 支持
- [ ] 语音识别实时字幕输出（SRT/TXT）
- [ ] TTS 支持更多语言/方言样本和自定义音色配置
- [ ] 增加 	ts.py / sr.py 的单测脚本与自动化验证流程

## 部署与交付

- [ ] 编写 Dockerfile 和部署说明，支持一键容器化运行
- [ ] 补充环境准备脚本或 Anaconda 环境导出文件
- [ ] 提供常见环境错误排查和修复方案

## 文档完善

- [ ] 补充 README.md 的"功能对比"和"快速开始"示例
- [ ] 将 docs 中的命令行示例与实际脚本参数对齐
- [ ] 添加 docs/CHANGELOG.md 或版本迭代日志
- [ ] 优化 docs 中的"常见问题"内容，覆盖更多运行时问题