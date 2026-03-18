import logging
import time
from typing import Optional
from faster_whisper import WhisperModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Transcriber:
    """負責將音檔轉錄為文字。

    示範 OOP 概念：
    - 封裝 (Encapsulation)：model 存在 instance 內部，外部不需知道細節
    - 單一職責 (SRP)：只負責轉錄，不處理下載或摘要

    注意：模型與轉錄邏輯保持原樣不變。
    """

    def __init__(self, model_name: str = "deepdml/faster-whisper-large-v3-turbo-ct2") -> None:
        self._model = WhisperModel(model_name)

    def transcribe(self, audio_path: str) -> Optional[str]:
        """將音檔轉錄為文字，失敗時回傳 None"""
        try:
            logger.info(f"載入音檔: {audio_path}")
            start_time = time.time()

            logger.info("開始轉錄...")
            segments, info = self._model.transcribe(
                audio_path,
                task="transcribe",
                beam_size=5,
            )

            segments_list = list(segments)

            process_time = time.time() - start_time
            logger.info(f"轉錄完成，音檔長度: {info.duration:.2f}秒")
            logger.info(f"處理時間: {process_time:.2f}秒")
            logger.info(f"段落數量: {len(segments_list)}")

            text = " ".join([segment.text for segment in segments_list])
            logger.info(f"轉錄文字長度: {len(text)} 字")
            logger.info(text)

            return text

        except Exception as e:
            logger.error(f"轉錄失敗: {e}")
            return None
