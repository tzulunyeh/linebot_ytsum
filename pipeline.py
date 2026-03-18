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
    """在子進程中執行轉錄，並將結果放入 queue。

    必須是模組層級函式（不能是 method），才能被 multiprocessing pickle。
    子進程使用 spawn 啟動，會重新 import，藉此隔離 Whisper model 的記憶體。
    """
    from transcription import Transcriber
    transcriber = Transcriber()
    result = transcriber.transcribe(audio_path_str)
    result_queue.put(result)


class ProcessingPipeline:
    """串接下載、轉錄、摘要的完整處理流程。"""

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
        """執行完整流程，回傳 (result_text, error_message)"""
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
            logger.info(f"嘗試下載音檔 (第 {attempt + 1} 次)")
            audio_path = self._downloader.download(url)
            if audio_path:
                logger.info(f"下載成功: {audio_path}")
                return audio_path
            time.sleep(self.RETRY_DELAY)
        logger.error("下載失敗，已達重試上限")
        return None

    def _transcribe_in_subprocess(self, audio_path: Path) -> Optional[str]:
        """在子進程執行轉錄，避免 Whisper 佔用主進程記憶體"""
        logger.info(f"開始轉錄音檔: {audio_path}")
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
            logger.info("已刪除暫存音檔")
        except OSError as e:
            logger.warning(f"刪除音檔失敗: {e}")

        if process.exitcode != 0:
            logger.error("轉錄子進程異常結束")
            return None

        transcription = result_queue.get()
        if not transcription:
            logger.error("轉錄結果為空")
            return None

        return transcription

    def _summarize_with_retry(self, text: str) -> Optional[str]:
        for attempt in range(self.MAX_RETRIES):
            logger.info(f"嘗試生成摘要 (第 {attempt + 1} 次)")
            summary = self._summarizer.summarize(text)
            if summary:
                logger.info("摘要生成成功")
                return summary
            time.sleep(self.RETRY_DELAY)
        logger.error("摘要生成失敗，已達重試上限")
        return None
