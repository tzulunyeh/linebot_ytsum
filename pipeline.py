import logging
import multiprocessing as mp
import os
import time
from multiprocessing import Process
from multiprocessing import Queue as MPQueue
from pathlib import Path
from typing import Optional, Tuple

from summarizer import GeminiSummarizer
from youtube_downloader import YouTubeDownloader

logger = logging.getLogger(__name__)


def _transcription_subprocess_target(audio_path_str: str, result_queue: MPQueue) -> None:
    """Run transcription in a child process and put the result into the queue.

    Must be a module-level function (not a method) to be picklable by multiprocessing.
    The spawn start method gives the child a clean slate, isolating Whisper's memory usage.
    """
    from transcription import Transcriber
    transcriber = Transcriber()
    result = transcriber.transcribe(audio_path_str)
    result_queue.put(result)


class ProcessingPipeline:
    """Orchestrates the download → transcribe → summarize workflow."""

    MAX_RETRIES = 3
    RETRY_DELAY = 2

    def __init__(
        self,
        downloader: YouTubeDownloader,
        summarizer: GeminiSummarizer,
    ) -> None:
        self._downloader = downloader
        self._summarizer = summarizer

    def process(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Run the full pipeline. Returns (result_text, error_message)."""
        audio_path = self._download_with_retry(url)
        if not audio_path:
            return None, "無法下載音檔"

        transcription = self._transcribe_in_subprocess(audio_path)
        if not transcription:
            return None, "轉錄失敗，請稍後再試"

        summary = self._summarize_with_retry(transcription)
        result = summary if summary else transcription + "\n\n（無法總結）"
        return result, None

    def _download_with_retry(self, url: str) -> Optional[Path]:
        for attempt in range(self.MAX_RETRIES):
            logger.info(f"Download attempt {attempt + 1}")
            audio_path = self._downloader.download(url)
            if audio_path:
                logger.info(f"Download succeeded: {audio_path}")
                return audio_path
            time.sleep(self.RETRY_DELAY)
        logger.error("Download failed after max retries")
        return None

    def _transcribe_in_subprocess(self, audio_path: Path) -> Optional[str]:
        """Spawn a child process for transcription to keep Whisper out of the main process."""
        logger.info(f"Transcribing: {audio_path}")
        try:
            mp.set_start_method("spawn", force=True)
        except RuntimeError:
            pass

        result_queue: MPQueue = MPQueue()
        process = Process(
            target=_transcription_subprocess_target,
            args=(str(audio_path), result_queue),
        )
        process.start()
        process.join()

        try:
            os.remove(audio_path)
            logger.info("Temp audio file removed")
        except OSError as e:
            logger.warning(f"Failed to remove audio file: {e}")

        if process.exitcode != 0:
            logger.error("Transcription subprocess exited with error")
            return None

        transcription = result_queue.get()
        if not transcription:
            logger.error("Transcription result is empty")
            return None

        return transcription

    def _summarize_with_retry(self, text: str) -> Optional[str]:
        for attempt in range(self.MAX_RETRIES):
            logger.info(f"Summarization attempt {attempt + 1}")
            summary = self._summarizer.summarize(text)
            if summary:
                logger.info("Summarization succeeded")
                return summary
            time.sleep(self.RETRY_DELAY)
        logger.error("Summarization failed after max retries")
        return None
