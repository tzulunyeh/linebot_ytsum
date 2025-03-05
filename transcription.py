import logging
from faster_whisper import WhisperModel
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

model = WhisperModel("deepdml/faster-whisper-large-v3-turbo-ct2")

def transcribe_audio(audio_path: str) -> str:
    """將音檔轉錄為文字"""
    try:
        logger.info(f"載入音檔: {audio_path}")
        start_time = time.time()
        
        # 開始轉錄
        logger.info("開始轉錄...")
        segments, info = model.transcribe(
            audio_path,
            task="transcribe",
            beam_size=5 
        )
        
        # 轉換為列表以獲取所有段落
        segments_list = list(segments)
        
        # 計算處理時間
        process_time = time.time() - start_time
        logger.info(f"轉錄完成，音檔長度: {info.duration:.2f}秒")
        logger.info(f"處理時間: {process_time:.2f}秒")
        logger.info(f"段落數量: {len(segments_list)}")
        
        # 組合所有段落
        text = " ".join([segment.text for segment in segments_list])
        logger.info(f"轉錄文字長度: {len(text)} 字")
        logger.info(text)
        
        return text

    except Exception as e:
        logger.error(f"轉錄失敗: {str(e)}")
        return None