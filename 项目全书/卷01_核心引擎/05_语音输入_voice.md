## 第五章 · 语音输入（voice.py） — 355行

### 三级降级架构

voice.py 实现了完整的离线语音识别链，按优先级自动降级：

| 优先级 | 后端 | 特点 | 依赖 |
|--------|------|------|------|
| 1 | faster-whisper | 离线/中文优/速度快4倍 | CTranslate2, ~300MB small模型 |
| 2 | openai-whisper | 离线/精度最高 | PyTorch, ~500MB |
| 3 | speech_recognition | Google API在线 | 需网络 |

检测流程：`_detect_backend()` 依次 `import` 尝试，第一个可用的为默认后端。

### faster-whisper 识别流水线

1. `_record_audio(duration=6, sample_rate=16000)` — pyaudio 录制 6 秒单声道音频，写入临时 WAV
2. `WhisperModel("small", device="cpu", compute_type="int8")` — 模块级单例缓存，避免重复加载
3. `model.transcribe(wav_path, language="zh", beam_size=5, vad_filter=True)` — VAD 过滤+beam search
4. 合并 segments 文本 → 清理临时 WAV

### 文字输入回退（TextFallbackDialog）

语音识别失败时不会让用户干等，自动弹出 `TextFallbackDialog`：

- 紫色主题对话框，`text_submitted` 信号回传文本
- 集成在 `_on_voice_status("fallback")` 和 `_on_voice_status("error")` 中
- dashboard 层 `_show_text_fallback()` 统一调度

### TTS 语音播报

`speak(text, voice="Tingting", rate=200)` 封装 macOS `say` 命令，可直接在舰桥中调用 AI 回复的语音播报。

### VoiceListener 信号

| 信号 | 参数 | 描述 |
|------|------|------|
| result_ready | str | 最终识别结果文本 |
| status_changed | (str, str) | (状态, 细节)，状态: recording/transcribing/done/fallback/error |

### VoiceListener 状态机

`idle → recording → transcribing → done`（成功路径）
`idle → recording → fallback → TextFallbackDialog`（无声回退）
`idle → ... → error → TextFallbackDialog`（异常回退）
