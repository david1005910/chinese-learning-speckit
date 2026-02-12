"""
음성 합성/인식 모듈 (TTS / STT)
edge-tts (남성 음성) 우선, gTTS 폴백
"""

import asyncio
import io
import os
from typing import Optional

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False

try:
    from gtts import gTTS
except ImportError:
    gTTS = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None

# 남성 중국어 음성 (Microsoft Edge Neural TTS)
EDGE_VOICE_MALE_ZH = "zh-CN-YunxiNeural"


class SpeechHandler:
    """텍스트 음성 변환 핸들러"""

    def __init__(self, audio_dir: str = 'audio_cache'):
        """
        Args:
            audio_dir: 음성 파일 캐시 디렉토리
        """
        self.audio_dir = audio_dir
        os.makedirs(self.audio_dir, exist_ok=True)
        self.tts_enabled = HAS_EDGE_TTS or (gTTS is not None)

    def tts_bytes(self, text: str, lang: str = 'zh-cn', slow: bool = False, rate: str = "") -> Optional[bytes]:
        """텍스트를 MP3 바이트로 변환 (남성 음성 우선)

        Args:
            rate: edge-tts 속도 조절 (예: "-25%" → 0.75x)
        """
        if not self.tts_enabled or not text.strip():
            return None

        # edge-tts 남성 음성 우선
        if HAS_EDGE_TTS:
            try:
                data = self._edge_tts_bytes(text, rate=rate)
                if data and len(data) > 0:
                    return data
            except Exception as e:
                print(f"edge-tts error, falling back to gTTS: {e}", flush=True)

        # gTTS 폴백
        if gTTS is not None:
            try:
                tts = gTTS(text=text, lang=lang, slow=slow)
                buf = io.BytesIO()
                tts.write_to_fp(buf)
                return buf.getvalue()
            except Exception as e:
                print(f"gTTS error: {e}", flush=True)
        return None

    def _edge_tts_bytes(self, text: str, rate: str = "") -> bytes:
        """edge-tts로 남성 음성 MP3 바이트 생성 (subprocess로 완전 격리)

        Args:
            rate: 속도 조절 (예: "-25%" → 0.75x, "+0%" → 1x)
        """
        import subprocess
        import tempfile
        import sys

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            cmd = [sys.executable, "-m", "edge_tts",
                   "--voice", EDGE_VOICE_MALE_ZH,
                   "--text", text,
                   "--write-media", tmp_path]
            if rate:
                cmd.append(f"--rate={rate}")
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode != 0:
                raise RuntimeError(f"edge-tts CLI failed: {result.stderr}")
            with open(tmp_path, "rb") as f:
                data = f.read()
            if not data:
                raise RuntimeError("edge-tts produced empty file")
            return data
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    def stt_from_bytes(self, audio_bytes: bytes, language: str = "zh-CN") -> Optional[str]:
        """
        오디오 바이트를 텍스트로 변환 (STT).
        st.audio_input()이 반환하는 WAV bytes를 받아 처리.
        """
        if sr is None:
            return None
        try:
            recognizer = sr.Recognizer()
            audio_file = io.BytesIO(audio_bytes)
            with sr.AudioFile(audio_file) as source:
                audio_data = recognizer.record(source)
            return recognizer.recognize_google(audio_data, language=language)
        except sr.UnknownValueError:
            return ""          # 인식 불가 (무음 등)
        except Exception as e:
            print(f"STT error: {e}")
            return None

    def text_to_speech(self, text: str, lang: str = 'zh-cn', slow: bool = False) -> Optional[str]:
        """
        텍스트를 음성으로 변환
        
        Args:
            text: 중국어 텍스트
            lang: 언어 코드 (zh-cn: 간체자, zh-tw: 번체자)
            slow: 느린 발음 여부
            
        Returns:
            음성 파일 경로 또는 None
        """
        if not self.tts_enabled:
            print("TTS is disabled. Please install gtts package.")
            return None
        
        # 파일명: 해시값으로 생성하여 중복 방지
        filename = f"{self.audio_dir}/{hash(text)}_{lang}.mp3"
        
        # 이미 캐시된 파일이 있으면 재사용
        if os.path.exists(filename):
            return filename
        
        try:
            tts = gTTS(text=text, lang=lang, slow=slow)
            tts.save(filename)
            return filename
        except Exception as e:
            print(f"TTS Error: {e}")
            return None
    
    def play_audio(self, filename: str):
        """
        음성 파일 재생
        
        Args:
            filename: 음성 파일 경로
        """
        if not os.path.exists(filename):
            print(f"Audio file not found: {filename}")
            return
        
        try:
            # playsound로 재생 시도
            from playsound import playsound
            playsound(filename)
        except ImportError:
            print("playsound not installed. Cannot play audio.")
        except Exception as e:
            print(f"Audio playback error: {e}")
    
    def batch_generate(self, texts: list, lang: str = 'zh-cn') -> list:
        """
        여러 텍스트를 한번에 음성으로 변환
        
        Args:
            texts: 텍스트 리스트
            lang: 언어 코드
            
        Returns:
            음성 파일 경로 리스트
        """
        audio_files = []
        
        for text in texts:
            filename = self.text_to_speech(text, lang)
            if filename:
                audio_files.append(filename)
        
        return audio_files
    
    def clear_cache(self, max_age_days: int = 30):
        """
        오래된 캐시 파일 삭제
        
        Args:
            max_age_days: 최대 보관 일수
        """
        import time
        
        now = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        for filename in os.listdir(self.audio_dir):
            filepath = os.path.join(self.audio_dir, filename)
            
            if os.path.isfile(filepath):
                file_age = now - os.path.getmtime(filepath)
                
                if file_age > max_age_seconds:
                    try:
                        os.remove(filepath)
                        print(f"Removed old cache file: {filename}")
                    except Exception as e:
                        print(f"Error removing file {filename}: {e}")
    
    def get_cache_size(self) -> float:
        """
        캐시 크기 조회 (MB)
        
        Returns:
            캐시 크기 (MB)
        """
        total_size = 0
        
        for filename in os.listdir(self.audio_dir):
            filepath = os.path.join(self.audio_dir, filename)
            if os.path.isfile(filepath):
                total_size += os.path.getsize(filepath)
        
        return total_size / (1024 * 1024)  # Convert to MB


if __name__ == "__main__":
    # 테스트
    handler = SpeechHandler()
    
    if handler.tts_enabled:
        print("Testing TTS...")
        
        # 중국어 텍스트 생성
        texts = ["你好", "谢谢", "再见"]
        
        for text in texts:
            print(f"\nGenerating audio for: {text}")
            audio_file = handler.text_to_speech(text)
            
            if audio_file:
                print(f"  Saved to: {audio_file}")
                # 재생은 선택적
                # handler.play_audio(audio_file)
        
        # 캐시 정보
        cache_size = handler.get_cache_size()
        print(f"\nCache size: {cache_size:.2f} MB")
        
        # 배치 생성 테스트
        print("\nBatch generation test:")
        batch_texts = ["早上好", "晚安", "对不起"]
        audio_files = handler.batch_generate(batch_texts)
        print(f"Generated {len(audio_files)} audio files")
    else:
        print("TTS disabled. Install gtts to enable.")
