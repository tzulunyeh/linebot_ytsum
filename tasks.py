import logging
from queue import Queue
from threading import Thread
from typing import Optional

from linebot import LineBotApi
from linebot.models import TextSendMessage

from pipeline import ProcessingPipeline

logger = logging.getLogger(__name__)


class TaskWorker:
    """管理任務佇列與背景工作執行緒，一次處理一個任務。"""

    def __init__(self, pipeline: ProcessingPipeline, line_bot_api: LineBotApi) -> None:
        self._pipeline = pipeline
        self._line_bot_api = line_bot_api
        self._queue: Queue = Queue()
        self._thread = Thread(target=self._worker_loop, daemon=True)

    def start(self) -> None:
        """啟動背景工作執行緒"""
        self._thread.start()

    def submit(self, user_id: str, url: str) -> None:
        """提交任務到佇列（非阻塞）"""
        self._queue.put((user_id, url))

    def _worker_loop(self) -> None:
        """背景執行緒持續消費佇列中的任務"""
        while True:
            user_id, url = self._queue.get()
            self._process(user_id, url)
            self._queue.task_done()

    def _process(self, user_id: str, url: str) -> None:
        """執行單一任務並將結果推送給用戶"""
        logger.info(f"開始處理任務 - URL: {url}")
        try:
            result, error = self._pipeline.process(url)
            if error:
                self._push(user_id, error)
                return
            self._push(user_id, result)
            self._push(user_id, "處理完成，感謝使用！")
        except Exception as e:
            logger.error(f"任務處理失敗: {e}")
            self._push(user_id, "處理失敗，請稍後再試")

    def _push(self, user_id: str, text: Optional[str]) -> None:
        """推送訊息給 LINE 用戶，失敗時只記錄 log"""
        if not text:
            return
        try:
            self._line_bot_api.push_message(user_id, TextSendMessage(text=text))
        except Exception as e:
            logger.error(f"推送訊息失敗: {e}")
