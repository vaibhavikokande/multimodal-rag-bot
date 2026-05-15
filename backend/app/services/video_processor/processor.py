"""
Video & Audio Processing Engine
Extracts audio, transcribes with Whisper, extracts keyframes
"""
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger

from app.core.config import settings


class VideoProcessor:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    async def process(self, video_path: str) -> Dict:
        """Full video processing pipeline"""
        logger.info(f"Processing video: {video_path}")

        result = {
            "text": "",
            "transcript": "",
            "tables": [],
            "metadata": {},
            "has_tables": False,
            "has_images": True,
            "keyframes": [],
        }

        try:
            # Extract metadata
            result["metadata"] = await self._extract_metadata(video_path)

            # Extract and transcribe audio
            audio_path = await self._extract_audio(video_path)
            if audio_path:
                transcript = await self.transcribe_audio(audio_path)
                result["transcript"] = transcript
                result["text"] = f"[VIDEO TRANSCRIPT]\n{transcript}"

                # Clean up temp audio
                if os.path.exists(audio_path):
                    os.remove(audio_path)

            # Extract keyframes for visual analysis
            keyframes = await self._extract_keyframes(video_path)
            result["keyframes"] = keyframes

            if keyframes:
                frame_descriptions = await self._analyze_keyframes(keyframes)
                if frame_descriptions:
                    result["text"] += f"\n\n[VIDEO VISUAL CONTENT]\n{frame_descriptions}"

        except Exception as e:
            logger.error(f"Video processing error: {e}")
            result["text"] = f"Video processing failed: {str(e)}"

        return result

    async def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio using OpenAI Whisper API"""
        try:
            file_size = os.path.getsize(audio_path)
            max_size = 25 * 1024 * 1024  # 25MB Whisper limit

            if file_size > max_size:
                return await self._transcribe_large_audio(audio_path)

            with open(audio_path, "rb") as audio_file:
                transcript = await self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text",
                    language="en",
                )
            return transcript

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return f"Audio transcription failed: {str(e)}"

    async def _transcribe_large_audio(self, audio_path: str) -> str:
        """Split and transcribe large audio files"""
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(audio_path)

            chunk_length_ms = 20 * 60 * 1000  # 20 min chunks
            chunks = [audio[i:i+chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]
            transcripts = []

            for i, chunk in enumerate(chunks):
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    chunk.export(tmp.name, format="mp3")
                    with open(tmp.name, "rb") as f:
                        result = await self.client.audio.transcriptions.create(
                            model="whisper-1",
                            file=f,
                            response_format="text",
                        )
                    transcripts.append(f"[Part {i+1}] {result}")
                    os.unlink(tmp.name)

            return "\n\n".join(transcripts)
        except Exception as e:
            logger.error(f"Large audio transcription failed: {e}")
            return ""

    async def _extract_audio(self, video_path: str) -> Optional[str]:
        """Extract audio from video using moviepy"""
        try:
            from moviepy.editor import VideoFileClip
            tmp_audio = tempfile.mktemp(suffix=".mp3")
            clip = VideoFileClip(video_path)
            if clip.audio:
                clip.audio.write_audiofile(tmp_audio, verbose=False, logger=None)
                clip.close()
                return tmp_audio
            clip.close()
        except Exception as e:
            logger.warning(f"Audio extraction failed: {e}")
        return None

    async def _extract_keyframes(self, video_path: str, num_frames: int = 5) -> List[str]:
        """Extract representative keyframes from video"""
        keyframe_paths = []
        try:
            import cv2
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            if total_frames == 0:
                cap.release()
                return []

            interval = max(1, total_frames // num_frames)
            frames_extracted = 0

            for i in range(0, total_frames, interval):
                if frames_extracted >= num_frames:
                    break
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                if ret:
                    tmp_path = tempfile.mktemp(suffix=".jpg")
                    cv2.imwrite(tmp_path, frame)
                    keyframe_paths.append(tmp_path)
                    frames_extracted += 1

            cap.release()
        except Exception as e:
            logger.warning(f"Keyframe extraction failed: {e}")

        return keyframe_paths

    async def _analyze_keyframes(self, keyframe_paths: List[str]) -> str:
        """Analyze keyframes with GPT-4 Vision"""
        from app.services.image_analyzer.analyzer import ImageAnalyzer
        analyzer = ImageAnalyzer()
        descriptions = []

        for i, frame_path in enumerate(keyframe_paths):
            try:
                result = await analyzer.analyze(frame_path)
                descriptions.append(f"Frame {i+1}: {result['description']}")
                os.unlink(frame_path)  # cleanup
            except Exception as e:
                logger.warning(f"Frame analysis failed: {e}")

        return "\n\n".join(descriptions)

    async def _extract_metadata(self, video_path: str) -> Dict:
        """Extract video metadata"""
        try:
            import cv2
            cap = cv2.VideoCapture(video_path)
            metadata = {
                "duration_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                "fps": cap.get(cv2.CAP_PROP_FPS),
                "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            }
            fps = metadata["fps"]
            if fps > 0:
                metadata["duration_seconds"] = metadata["duration_frames"] / fps
            cap.release()
            return metadata
        except Exception:
            return {}
