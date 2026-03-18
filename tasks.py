import logging
from queue import Queue
from threading import Thread
from typing import Optional

from linebot import LineBotApi
from linebot.models import TextSendMessage

from pipeline import ProcessingPipeline

logger = logging.getLogger(__name__)


class TaskWorker:
    """Manages a task queue and a background worker thread, processing one task at a time."""

    def __init__(self, pipeline: ProcessingPipeline, line_bot_api: LineBotApi) -> None:
        self._pipeline = pipeline
        self._line_bot_api = line_bot_api
        self._queue: Queue = Queue()
        self._thread = Thread(target=self._worker_loop, daemon=True)

    def start(self) -> None:
        """Start the background worker thread."""
        self._thread.start()

    def submit(self, user_id: str, url: str) -> None:
        """Enqueue a task (non-blocking)."""
        self._queue.put((user_id, url))

    def _worker_loop(self) -> None:
        while True:
            user_id, url = self._queue.get()
            self._process(user_id, url)
            self._queue.task_done()

    def _process(self, user_id: str, url: str) -> None:
        logger.info(f"Processing task - URL: {url}")
        try:
            result, error = self._pipeline.process(url)
            if error:
                self._push(user_id, error)
                return
            self._push(user_id, result)
            self._push(user_id, "處理完成，感謝使用！")
        except Exception as e:
            logger.error(f"Task failed: {e}")
            self._push(user_id, "處理失敗，請稍後再試")

    def _push(self, user_id: str, text: Optional[str]) -> None:
        """Push a LINE message; log and continue on failure."""
        if not text:
            return
        try:
            self._line_bot_api.push_message(user_id, TextSendMessage(text=text))
        except Exception as e:
            logger.error(f"Failed to push message: {e}")
