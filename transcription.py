import logging
import time
from typing import Optional
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)


class Transcriber:
    """Transcribes audio files to text using faster-whisper."""

    def __init__(self, model_name: str = "deepdml/faster-whisper-large-v3-turbo-ct2") -> None:
        self._model = WhisperModel(model_name)

    def transcribe(self, audio_path: str) -> Optional[str]:
        """Transcribe an audio file and return the full text, or None on failure."""
        try:
            logger.info(f"Loading audio: {audio_path}")
            start_time = time.time()

            logger.info("Starting transcription...")
            segments, info = self._model.transcribe(
                audio_path,
                task="transcribe",
                beam_size=5,
            )

            segments_list = list(segments)

            process_time = time.time() - start_time
            logger.info(f"Transcription done. Audio length: {info.duration:.2f}s")
            logger.info(f"Processing time: {process_time:.2f}s")
            logger.info(f"Segments: {len(segments_list)}")

            text = " ".join([segment.text for segment in segments_list])
            logger.info(f"Transcription length: {len(text)} chars")
            logger.info(text)

            return text

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None
