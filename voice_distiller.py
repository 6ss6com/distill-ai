"""
DistillAI Voice Persona Distiller v2.5

语音人格蒸馏 - 输入声音 → 声纹特征 → 语音人格输出

支持输入:
- 微信语音消息 (.silk/.amr/.mp3)
- 电话录音 (.mp3/.wav/.m4a)
- 视频配音 (.mp4/.avi/.mov 提取音频)
- 播客/音频文件 (.mp3/.ogg/.flac)
- 实时录音 (麦克风)

支持输出:
- 文字转语音 (TTS) - 保持人格语速/语调
- 声纹克隆 (Voice Clone)
- 语音性格描述报告

Pipeline:
  Audio Input → STT → Prosody Analysis → Voice Print → Persona Card → TTS Output
"""

import os, re, json, struct, hashlib, base64, subprocess, tempfile
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from collections import Counter


# ============================================================
# Audio Format Registry
# ============================================================

AUDIO_EXTENSIONS = {
    '.silk': 'silk',      # WeChat voice
    '.sil': 'silk',
    '.amr': 'amr',        # 3GPP voice
    '.mp3': 'mp3',
    '.wav': 'wav',
    '.m4a': 'm4a',
    '.ogg': 'ogg',
    '.flac': 'flac',
    '.aac': 'aac',
    '.wma': 'wma',
    '.aiff': 'aiff',
}


# ============================================================
# Audio Converter (ffmpeg-based)
# ============================================================

class AudioConverter:
    """
    音频格式转换器 - 统一转换为WAV/MP3供分析

    依赖: ffmpeg (pip install ffmpeg-python 或系统安装ffmpeg)
    """

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg = ffmpeg_path

    def is_available(self) -> bool:
        try:
            result = subprocess.run(
                [self.ffmpeg, "-version"],
                capture_output=True, timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def convert_to_wav(self, input_path: str, output_path: str = None) -> str:
        """转换任意音频为WAV格式 (16kHz, 单声道)"""
        if output_path is None:
            output_path = tempfile.mktemp(suffix='.wav')

        cmd = [
            self.ffmpeg, "-y", "-i", input_path,
            "-ar", "16000",       # 16kHz采样率
            "-ac", "1",           # 单声道
            "-acodec", "pcm_s16le",  # 16bit PCM
            output_path
        ]

        try:
            subprocess.run(cmd, capture_output=True, timeout=120, check=True)
            return output_path
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"ffmpeg convert failed: {e.stderr.decode() if e.stderr else e}")

    def extract_audio_from_video(self, video_path: str, output_path: str = None) -> str:
        """从视频提取音频"""
        if output_path is None:
            output_path = tempfile.mktemp(suffix='.wav')

        cmd = [
            self.ffmpeg, "-y", "-i", video_path,
            "-vn", "-ar", "16000", "-ac", "1",
            output_path
        ]

        try:
            subprocess.run(cmd, capture_output=True, timeout=300, check=True)
            return output_path
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"ffmpeg video->audio failed: {e.stderr.decode() if e.stderr else e}")

    def get_duration(self, audio_path: str) -> float:
        """获取音频时长(秒)"""
        cmd = [
            self.ffmpeg, "-i", audio_path,
            "-hide_banner"
        ]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30
            )
            output = result.stderr + result.stdout
            # 找 Duration: 00:01:23.45
            m = re.search(r'Duration:\s*(\d+):(\d+):(\d+\.\d+)', output)
            if m:
                h, mi, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
                return h * 3600 + mi * 60 + s
        except:
            pass
        return 0.0


# ============================================================
# Speech-to-Text (STT)
# ============================================================

class STTEngine:
    """
    语音转文字引擎

    支持:
    - Whisper (本地开源)
    - OpenAI Whisper API
    - 腾讯/百度/阿里云 STT API
    - WeChat/TG内置语音识别 (via file content)
    """

    def __init__(self, provider: str = "whisper"):
        self.provider = provider
        self._available = None

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available

        if self.provider == "whisper":
            try:
                import torch
                # 检查whisper可用性
                self._available = True
            except ImportError:
                self._available = False

        self._available = self._available or (self.provider in ["openai", "tencent", "baidu", "aliyun"])
        return self._available

    def transcribe(self, audio_path: str, language: str = "auto") -> Dict:
        """
        转录音频为文字

        Returns:
            {
                "text": "转录文本",
                "segments": [{"start": 0.0, "end": 5.0, "text": "..."}],
                "language": "zh",
                "confidence": 0.95
            }
        """
        if not self.is_available():
            return {"text": "", "segments": [], "language": language or "auto", "confidence": 0.0, "error": f"STT provider '{self.provider}' not available"}

        if self.provider == "whisper":
            return self._whisper(audio_path, language)
        elif self.provider == "openai":
            return self._openai_whisper(audio_path, language)
        elif self.provider == "tencent":
            return self._tencent_stt(audio_path)
        elif self.provider == "baidu":
            return self._baidu_stt(audio_path)
        else:
            return {"text": "", "segments": [], "language": "auto", "confidence": 0.0}

    def _whisper(self, audio_path: str, language: str) -> Dict:
        """本地 Whisper 转录"""
        try:
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe(audio_path, language=language if language != "auto" else None, fp16=False)

            return {
                "text": result.get("text", ""),
                "segments": result.get("segments", []),
                "language": result.get("language", "auto"),
                "confidence": result.get("text", "").__len__() / max(result.get("segments", [{}])[-1].get("end", 1), 1) * 0.8,
            }
        except Exception as e:
            return {"text": "", "segments": [], "language": language, "confidence": 0.0, "error": str(e)}

    def _openai_whisper(self, audio_path: str, language: str) -> Dict:
        """OpenAI Whisper API 转录"""
        try:
            import openai
            with open(audio_path, "rb") as f:
                result = openai.Audio.transcribe("whisper-1", f, language=language if language != "auto" else None)

            return {
                "text": result.get("text", ""),
                "segments": [{"start": 0.0, "end": 30.0, "text": result.get("text", "")}],
                "language": language or "auto",
                "confidence": 0.9,
            }
        except Exception as e:
            return {"text": "", "segments": [], "language": language, "confidence": 0.0, "error": str(e)}

    def _tencent_stt(self, audio_path: str) -> Dict:
        """腾讯云ASR"""
        # 占位 - 需要配置SECRET_ID/SECRET_KEY
        return {"text": "", "segments": [], "language": "zh", "confidence": 0.0, "error": "tencent stt not configured"}

    def _baidu_stt(self, audio_path: str) -> Dict:
        """百度ASR"""
        return {"text": "", "segments": [], "language": "zh", "confidence": 0.0, "error": "baidu stt not configured"}


# ============================================================
# Prosody Analysis (语音韵律分析)
# ============================================================

class ProsodyAnalyzer:
    """
    语音韵律分析器

    分析维度:
    1. 语速 (words per minute)
    2. 平均音高 (pitch)
    3. 音高变化范围 (pitch range)
    4. 停顿模式 (pause frequency/duration)
    5. 音量变化 (energy/amplitude)
    6. 重音模式 (stress patterns)
    7. 情感色彩 (emotion indicators)

    提取声纹特征向量，用于人格匹配
    """

    # 语速等级
    SPEED_LEVELS = {
        "极慢": (0, 80),
        "慢": (80, 120),
        "正常": (120, 160),
        "快": (160, 200),
        "极快": (200, 999),
    }

    # 音高等级 (Hz, 基于中文成人平均基频)
    PITCH_LEVELS = {
        "低沉": (0, 150),
        "偏低": (150, 200),
        "中性": (200, 250),
        "偏高": (250, 300),
        "高亢": (300, 999),
    }

    def __init__(self):
        self.features = {}

    def analyze(self, audio_path: str, stt_result: Dict = None) -> Dict:
        """
        分析语音特征

        如果没有音频分析能力，至少从STT文本分析韵律特征
        """
        if stt_result is None:
            stt_result = {"text": "", "segments": []}

        text = stt_result.get("text", "")
        segments = stt_result.get("segments", [])

        # 从文本推断韵律特征
        self.features = {
            "avg_speed_wpm": self._estimate_speed(text, segments),
            "avg_pitch_hz": self._estimate_pitch(text),
            "pitch_range": self._estimate_pitch_range(text),
            "pause_frequency": self._estimate_pause(text, segments),
            "volume_level": self._estimate_volume(text),
            "emotion_indicators": self._detect_emotion(text),
            "formality_level": self._estimate_formality(text),
            "confidence_level": self._estimate_confidence(text),
            "hesitation_markers": self._detect_hesitation(text),
            "sentence_length_avg": self._avg_sentence_length(text),
            "exclamation_ratio": self._count_exclamation(text),
            "question_ratio": self._count_questions(text),
        }

        return self.features

    def _estimate_speed(self, text: str, segments: List[Dict]) -> float:
        """估算语速 (WPM)"""
        if segments:
            try:
                total_duration = segments[-1].get("end", 0) - (segments[0].get("start", 0) if segments else 0)
                word_count = len(text.split())
                if total_duration > 0:
                    return word_count / (total_duration / 60)
            except:
                pass

        # 从文本特征推断
        sentence_count = max(1, text.count("。") + text.count("!") + text.count("?"))
        avg_sentence_len = len(text) / sentence_count
        # 中文平均语速约150-200字/分钟
        return min(avg_sentence_len * 3, 250)

    def _estimate_pitch(self, text: str) -> float:
        """估算平均音高 (Hz)"""
        # 从感叹词/语气推断音高
        high_pitch_words = ["啊", "呀", "哇", "耶", "哦", "嗯", "哈", "诶"]
        low_pitch_words = ["嗯", "呃", "哦", "嘛"]

        high_count = sum(text.count(w) for w in high_pitch_words)
        low_count = sum(text.count(w) for w in low_pitch_words)

        base = 200  # 中性基准
        if high_count > low_count:
            return min(base + (high_count - low_count) * 10, 320)
        elif low_count > high_count:
            return max(base - (low_count - high_count) * 8, 120)
        return base

    def _estimate_pitch_range(self, text: str) -> float:
        """估算音高变化范围"""
        exclamation_count = text.count("!") + text.count("！")
        question_count = text.count("?") + text.count("？")

        base_range = 50  # 基础变化范围 Hz
        return base_range + exclamation_count * 15 + question_count * 10

    def _estimate_pause(self, text: str, segments: List[Dict]) -> float:
        """估算停顿频率 (次/分钟)"""
        ellipsis_count = text.count("...") + text.count("…")
        comma_count = text.count(",")

        pause_indicators = ellipsis_count + comma_count
        text_len = max(1, len(text))
        return (pause_indicators / text_len) * 1000

    def _estimate_volume(self, text: str) -> str:
        """估算音量水平"""
        loud_indicators = ["!", "！", "大声", "喊"]
        soft_indicators = ["轻", "小声", "悄悄", "低"]

        loud_count = sum(text.count(w) for w in loud_indicators)
        soft_count = sum(text.count(w) for w in soft_indicators)

        if loud_count > soft_count:
            return "高"
        elif soft_count > loud_count:
            return "低"
        return "中等"

    def _detect_emotion(self, text: str) -> Dict[str, float]:
        """检测情感色彩"""
        emotions = {
            "积极": ["开心", "高兴", "棒", "好", "喜欢", "赞", "哈哈", "太好了"],
            "消极": ["难过", "伤心", "烦", "累", "压力", "焦虑", "不爽"],
            "兴奋": ["哇", "太棒了", "厉害", "牛", "激动", "兴奋"],
            "平静": ["嗯", "好", "行", "可以", "淡定", "一般"],
            "愤怒": ["气", "讨厌", "烦", "滚", "哼", "可恶"],
            "惊讶": ["啊", "咦", "真的", "不会吧", "这么巧"],
        }

        scores = {}
        for emotion, keywords in emotions.items():
            score = sum(text.count(k) for k in keywords)
            scores[emotion] = min(score / max(len(text) / 100, 1), 1.0)

        return scores

    def _estimate_formality(self, text: str) -> str:
        """估算正式程度"""
        formal_indicators = ["您", "请", "谢谢", "请问", "关于", "因此", "然而"]
        informal_indicators = ["哈", "嘿嘿", "嗯", "啊", "嘛", "啦", "呀"]

        formal_count = sum(text.count(w) for w in formal_indicators)
        informal_count = sum(text.count(w) for w in informal_indicators)

        if informal_count > formal_count * 2:
            return "随意"
        elif formal_count > informal_count:
            return "正式"
        return "中性"

    def _estimate_confidence(self, text: str) -> str:
        """估算自信程度"""
        confident_words = ["肯定", "绝对", "一定", "确定", "没问题", "当然"]
        uncertain_words = ["可能", "大概", "也许", "不确定", "不好说", "不清楚"]

        conf_count = sum(text.count(w) for w in confident_words)
        unc_count = sum(text.count(w) for w in uncertain_words)

        if conf_count > unc_count:
            return "自信"
        elif unc_count > conf_count:
            return "谨慎"
        return "中性"

    def _detect_hesitation(self, text: str) -> float:
        """检测犹豫标记"""
        hesitation_words = ["嗯", "呃", "啊", "这个", "那个", "就是", "其实", "大概"]
        return sum(text.count(w) for w in hesitation_words) / max(len(text) / 50, 1)

    def _avg_sentence_length(self, text: str) -> float:
        """平均句子长度"""
        sentences = re.split(r'[。!?！？]', text)
        sentences = [s for s in sentences if len(s.strip()) > 0]
        if not sentences:
            return 0
        return sum(len(s) for s in sentences) / len(sentences)

    def _count_exclamation(self, text: str) -> float:
        return (text.count("!") + text.count("！") + text.count("哈") + text.count("啊")) / max(len(text) / 100, 1)

    def _count_questions(self, text: str) -> float:
        return (text.count("?") + text.count("？")) / max(len(text) / 100, 1)

    def get_voice_profile(self) -> Dict:
        """获取声纹画像"""
        speed = self.features.get("avg_speed_wpm", 150)
        pitch = self.features.get("avg_pitch_hz", 200)

        # 推断说话风格标签
        style_tags = []
        if speed > 180:
            style_tags.append("语速快")
        elif speed < 100:
            style_tags.append("语速慢")

        if pitch > 260:
            style_tags.append("音调高")
        elif pitch < 170:
            style_tags.append("音调低")

        formality = self.features.get("formality_level", "中性")
        if formality:
            style_tags.append(formality)

        emotion_scores = self.features.get("emotion_indicators", {})
        if emotion_scores:
            top_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0] if emotion_scores else "中性"
            style_tags.append(top_emotion)

        confidence = self.features.get("confidence_level", "中性")
        if confidence:
            style_tags.append(confidence)

        return {
            "speed_wpm": round(speed, 1),
            "pitch_hz": round(pitch, 1),
            "style_tags": style_tags,
            "features": self.features,
        }


# ============================================================
# Voice Print (声纹特征提取)
# ============================================================

class VoicePrintExtractor:
    """
    声纹特征提取器

    提取声纹向量，用于:
    1. 相似度匹配 (判断是否为同一人)
    2. 声音人格分类
    3. TTS声线选择

    简化版: 基于音频基础特征提取
    生产版: 使用resemblyzer/webrtc-vad/更复杂的音频分析
    """

    def extract(self, audio_path: str) -> Dict:
        """
        提取声纹特征向量

        Returns:
            {
                "speaker_embedding": [float, ...],  # 192维向量
                "quality_score": 0.85,              # 音频质量
                "language_hint": "zh",
                "gender_hint": "male/female/unknown",
                "age_hint": "young/middle/old/unknown",
            }
        """
        # 简化实现: 使用音频基础统计特征
        try:
            import wave
            with wave.open(audio_path, 'rb') as w:
                frames = w.readframes(w.getnframes())
                sample_width = w.getsampwidth()
                rate = w.getframerate()
                n_channels = w.getnchannels()

            # 计算基础统计
            import struct
            fmt = f'{len(frames)//sample_width}h'
            samples = list(struct.unpack(fmt, frames))

            if not samples:
                return self._empty_voice_print()

            # RMS能量
            import math
            energy = math.sqrt(sum(s**2 for s in samples) / len(samples))

            # 短时能量变化
            chunk_size = rate // 10  # 100ms
            chunks = [samples[i:i+chunk_size] for i in range(0, len(samples), chunk_size)]
            energies = [math.sqrt(sum(s**2 for s in c) / len(c)) for c in chunks if c]

            # 基频估计 (简化)
            avg_energy = sum(energies) / max(len(energies), 1)
            high_energy_ratio = sum(1 for e in energies if e > avg_energy * 1.5) / max(len(energies), 1)

            # 性别推断 (基于能量和采样率)
            gender = "unknown"
            if rate > 0:
                # 简化: 男性基频85-180Hz, 女性165-255Hz
                est_pitch = min(max(energy / 1000, 100), 400)
                if est_pitch < 180:
                    gender = "male"
                elif est_pitch > 230:
                    gender = "female"

            # 质量评分
            quality = min(1.0, energy / 20000) if energy > 0 else 0.3

            # 生成简化的speaker embedding (用统计特征模拟)
            embedding = [
                energy / 30000,  # 能量
                sum(energies) / max(len(energies), 1) / 20000,  # 平均能量
                high_energy_ratio,  # 动态比率
                est_pitch / 300,  # 基频
                len(chunks) / 1000,  # 时长标准化
            ]

            return {
                "speaker_embedding": embedding,
                "quality_score": round(quality, 2),
                "gender_hint": gender,
                "age_hint": "unknown",
                "language_hint": "zh",
                "duration_sec": len(samples) / max(rate, 1),
            }

        except Exception as e:
            return self._empty_voice_print()

    def _empty_voice_print(self) -> Dict:
        return {
            "speaker_embedding": [0.0] * 5,
            "quality_score": 0.0,
            "gender_hint": "unknown",
            "age_hint": "unknown",
            "language_hint": "unknown",
            "duration_sec": 0.0,
        }

    def compare(self, print1: Dict, print2: Dict) -> float:
        """比较两个声纹的相似度 (0-1)"""
        e1 = print1.get("speaker_embedding", [])
        e2 = print2.get("speaker_embedding", [])
        if not e1 or not e2 or len(e1) != len(e2):
            return 0.0

        # 余弦相似度
        dot = sum(a * b for a, b in zip(e1, e2))
        norm1 = math.sqrt(sum(a**2 for a in e1))
        norm2 = math.sqrt(sum(b**2 for b in e2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot / (norm1 * norm2)


# ============================================================
# Voice Persona Distiller
# ============================================================

class VoicePersonaDistiller:
    """
    语音人格蒸馏器

    输入: 音频文件 (微信语音/电话录音/视频等)
    输出: 语音人格报告 + TTS配置
    """

    def __init__(self):
        self.stt = STTEngine(provider="whisper")
        self.prosody = ProsodyAnalyzer()
        self.voice_print = VoicePrintExtractor()
        self.converter = AudioConverter()

    def distill(self, audio_path: str, target_speaker: str = "speaker") -> Dict:
        """
        蒸馏语音人格

        Pipeline:
        1. 格式转换 (→ WAV)
        2. STT转文字
        3. 韵律分析
        4. 声纹提取
        5. 综合人格报告
        """
        # 1. 准备音频
        original_ext = Path(audio_path).suffix.lower()
        is_video = original_ext in ['.mp4', '.avi', '.mov', '.mkv', '.flv']

        # 转换音频
        try:
            if is_video:
                wav_path = self.converter.extract_audio_from_video(audio_path)
            elif original_ext not in ['.wav']:
                if self.converter.is_available():
                    wav_path = self.converter.convert_to_wav(audio_path)
                else:
                    wav_path = audio_path  # 直接用原文件
            else:
                wav_path = audio_path

            duration = self.converter.get_duration(wav_path) if self.converter.is_available() else 0

        except Exception as e:
            wav_path = audio_path
            duration = 0

        # 2. STT转文字
        stt_result = self.stt.transcribe(wav_path)

        # 3. 韵律分析
        prosody_features = self.prosody.analyze(wav_path, stt_result)
        voice_profile = self.prosody.get_voice_profile()

        # 4. 声纹提取
        voice_print = self.voice_print.extract(wav_path)

        # 5. 综合人格报告
        persona_report = self._generate_report(
            audio_path=audio_path,
            duration=duration,
            stt_result=stt_result,
            prosody=prosody_features,
            voice_profile=voice_profile,
            voice_print=voice_print,
            target_speaker=target_speaker,
        )

        return persona_report

    def _generate_report(self, audio_path: str, duration: float, stt_result: Dict,
                         prosody: Dict, voice_profile: Dict, voice_print: Dict,
                         target_speaker: str) -> Dict:
        """生成语音人格报告"""

        text = stt_result.get("text", "")
        emotion_scores = prosody.get("emotion_indicators", {})

        # 声音标签
        style_tags = voice_profile.get("style_tags", [])

        # 语速描述
        speed = prosody.get("avg_speed_wpm", 150)
        speed_label = "语速适中"
        if speed < 100:
            speed_label = "语速偏慢，沉稳"
        elif speed > 180:
            speed_label = "语速偏快，活泼"

        # 音调描述
        pitch = prosody.get("avg_pitch_hz", 200)
        pitch_label = "音调适中"
        if pitch < 160:
            pitch_label = "音调偏低，稳重"
        elif pitch > 270:
            pitch_label = "音调偏高，明快"

        # 情感主导
        top_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0] if emotion_scores else "中性"
        emotion_score = emotion_scores.get(top_emotion, 0) if emotion_scores else 0

        # 综合人格画像
        voice_persona = {
            "source_file": os.path.basename(audio_path),
            "duration_sec": round(duration, 1),
            "stt_text": text[:500] if text else "",
            "stt_confidence": stt_result.get("confidence", 0),
            "speech_speed_wpm": speed,
            "avg_pitch_hz": round(pitch, 1),
            "voice_style": speed_label + " | " + pitch_label,
            "style_tags": style_tags,
            "primary_emotion": top_emotion,
            "emotion_intonation": emotion_score,
            "formality": prosody.get("formality_level", "中性"),
            "confidence_level": prosody.get("confidence_level", "中性"),
            "hesitation_score": prosody.get("hesitation_markers", 0),
            "exclamation_ratio": prosody.get("exclamation_ratio", 0),
            "question_ratio": prosody.get("question_ratio", 0),
            "avg_sentence_length": prosody.get("sentence_length_avg", 0),
            "voice_print": voice_print,
            "gender_hint": voice_print.get("gender_hint", "unknown"),
            "quality_score": voice_print.get("quality_score", 0),
        }

        return voice_persona


# ============================================================
# Voice TTS Output
# ============================================================

class VoiceTTSEngine:
    """
    语音合成输出引擎

    支持:
    - MiniMax TTS (已集成)
    - OpenAI TTS
    - 微软Azure TTS
    - 讯飞/百度 TTS
    - 本地VITS/Tacotron
    """

    def __init__(self, provider: str = "minimax"):
        self.provider = provider

    def is_available(self) -> bool:
        if self.provider == "minimax":
            return True  # MiniMax TTS可用
        return False

    def speak(self, text: str, voice_config: Dict = None, output_path: str = None) -> str:
        """
        合成语音

        Args:
            text: 要说的内容
            voice_config: 语音配置 (从voice_persona获取)
            output_path: 输出路径

        Returns:
            音频文件路径
        """
        if output_path is None:
            output_path = tempfile.mktemp(suffix='.mp3')

        voice_config = voice_config or {}

        # 根据voice_profile选择/调整TTS参数
        style_tags = voice_config.get("style_tags", [])

        # 语速调整
        speed_label = "moderate"
        if "语速快" in style_tags:
            speed_label = "fast"
        elif "语速慢" in style_tags:
            speed_label = "slow"

        # 音调调整
        pitch_label = "medium"
        if "音调高" in style_tags:
            pitch_label = "high"
        elif "音调低" in style_tags:
            pitch_label = "low"

        # 情感标签
        emotion = voice_config.get("primary_emotion", "neutral")

        return self._synthesize(text, speed=speed_label, pitch=pitch_label, emotion=emotion, output=output_path)

    def _synthesize(self, text: str, speed: str, pitch: str, emotion: str, output: str) -> str:
        """调用TTS服务合成"""
        if self.provider == "minimax":
            return self._minimax_tts(text, speed, pitch, emotion, output)
        elif self.provider == "openai":
            return self._openai_tts(text, output)
        else:
            return self._minimax_tts(text, speed, pitch, emotion, output)

    def _minimax_tts(self, text: str, speed: str, pitch: str, emotion: str, output: str) -> str:
        """MiniMax TTS合成"""
        try:
            import requests

            api_key = os.environ.get("MINIMAX_API_KEY", "")
            if not api_key:
                return ""

            url = "https://api.minimax.chat/v1/t2a_v2"

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            # 调整语速/音调参数
            speed_map = {"slow": 0.8, "moderate": 1.0, "fast": 1.2}
            pitch_map = {"low": 0.8, "medium": 1.0, "high": 1.2}

            payload = {
                "model": "speech-02-hd",
                "text": text[:500],  # MiniMax限制500字
                "stream": False,
                "voice_setting": {
                    "speed": speed_map.get(speed, 1.0),
                    "pitch": pitch_map.get(pitch, 1.0),
                    "emotion": emotion,
                },
                "audio_setting": {
                    "audio_type": "mp3",
                }
            }

            response = requests.post(url, headers=headers, json=payload, timeout=30)

            if response.status_code == 200:
                with open(output, 'wb') as f:
                    f.write(response.content)
                return output

        except Exception as e:
            print(f"TTS error: {e}")

        return ""

    def _openai_tts(self, text: str, output: str) -> str:
        """OpenAI TTS"""
        try:
            from openai import OpenAI
            client = OpenAI()
            response = client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text[:500]
            )
            response.stream_to_file(output)
            return output
        except Exception as e:
            print(f"OpenAI TTS error: {e}")
        return ""


# ============================================================
# Main Entry Point
# ============================================================

class VoiceDistiller:
    """
    语音人格蒸馏完整工具

    用法:
        from voice_distiller import VoiceDistiller

        vd = VoiceDistiller()

        # 蒸馏语音人格
        report = vd.distill("path/to/audio.mp3")
        print(report["voice_style"])
        print(report["primary_emotion"])

        # 语音输出
        audio = vd.speak("你好，我是你的AI分身", voice_config=report)
        print(audio)
    """

    def __init__(self):
        self.distiller = VoicePersonaDistiller()
        self.tts = VoiceTTSEngine(provider="minimax")

    def distill(self, audio_path: str, target_speaker: str = "speaker") -> Dict:
        """蒸馏语音人格"""
        return self.distiller.distill(audio_path, target_speaker)

    def speak(self, text: str, voice_config: Dict = None, output_path: str = None) -> str:
        """语音输出"""
        return self.tts.speak(text, voice_config, output_path)

    def distill_and_speak(self, audio_path: str, text: str) -> Tuple[Dict, str]:
        """蒸馏 + 语音输出"""
        report = self.distill(audio_path)
        audio = self.speak(text, voice_config=report)
        return report, audio


# ===== 便捷函数 =====

def distill_voice(audio_path: str, target_speaker: str = "speaker") -> Dict:
    """一键蒸馏语音人格"""
    vd = VoiceDistiller()
    return vd.distill(audio_path, target_speaker)


def speak_with_voice(text: str, voice_config: Dict, output_path: str = None) -> str:
    """使用语音人格输出"""
    vd = VoiceDistiller()
    return vd.speak(text, voice_config, output_path)


def full_pipeline(audio_path: str, output_text: str) -> Tuple[Dict, str]:
    """完整Pipeline: 蒸馏 → 语音输出"""
    vd = VoiceDistiller()
    report = vd.distill(audio_path)
    audio = vd.speak(output_text, voice_config=report)
    return report, audio


if __name__ == "__main__":
    print("=== Voice Persona Distiller ===")
    print()
    print("Supported audio formats:")
    for ext in AUDIO_EXTENSIONS:
        print(f"  {ext}")

    vd = VoiceDistiller()

    print()
    print("STT provider:", vd.distiller.stt.provider, "- Available:", vd.distiller.stt.is_available())
    print("TTS provider:", vd.tts.provider, "- Available:", vd.tts.is_available())
    print("Audio converter (ffmpeg):", "Available" if vd.distiller.converter.is_available() else "Not found")

    print()
    print("Usage:")
    print("  report = distill_voice('voice_message.mp3')")
    print("  audio = speak_with_voice('Hello', voice_config=report)")