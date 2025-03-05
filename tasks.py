import os
import time
import logging
from queue import Queue
from threading import Thread
import multiprocessing as mp
from multiprocessing import Process, Queue as MPQueue

from youtube_downloader import download_audio
from transcription import transcribe_audio
from summarizer import summarize_text
from config import CHANNEL_ACCESS_TOKEN
from linebot import LineBotApi
from linebot.models import TextSendMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)

def transcribe_wrapper(audio_path, queue):
    """在獨立進程中執行轉錄，並將結果放入佇列"""
    result = transcribe_audio(audio_path)
    queue.put(result)

def process_task(user_id: str, url: str):
    """順序處理任務：下載、轉錄、總結"""
    try:
        logger.info(f"開始處理任務 - URL: {url}")

        # 下載音檔（最多重試 3 次）
        audio_path = None
        for attempt in range(3):
            logger.info(f"嘗試下載音檔 (第 {attempt + 1} 次)")
            audio_path = download_audio(url)
            if audio_path:
                logger.info(f"下載成功: {audio_path}")
                break
            time.sleep(2)
        if not audio_path:
            logger.error("下載失敗")
            try:
                line_bot_api.push_message(user_id, TextSendMessage(text="無法下載音檔"))
            except Exception as e:
                logger.error(f"推送訊息失敗: {e}")
            return

        # 轉錄音檔
        logger.info("開始轉錄音檔")
        logger.info("audio_path: " + audio_path)
        
        try:
            mp.set_start_method('spawn', force=True)
        except RuntimeError:
            pass
        
        mp_queue = MPQueue()
        p = Process(target=transcribe_wrapper, args=(audio_path, mp_queue))
        p.start()
        p.join()
        
        if p.exitcode != 0:
            logger.error("轉錄進程失敗")
            try:
                line_bot_api.push_message(user_id, TextSendMessage(text="轉錄失敗，請稍後再試"))
            except Exception as e:
                logger.error(f"推送訊息失敗: {e}")
            os.remove(audio_path)
            return
        
        transcription = mp_queue.get()
        if not transcription:
            logger.error("轉錄失敗")
            try:
                line_bot_api.push_message(user_id, TextSendMessage(text="轉錄失敗，請稍後再試"))
            except Exception as e:
                logger.error(f"推送訊息失敗: {e}")
            os.remove(audio_path)
            return

        # 刪除臨時音檔
        os.remove(audio_path)
        logger.info("已刪除臨時音檔")

        # 總結文字（最多重試 3 次）
        logger.info("開始生成摘要")
        summary = None
        for attempt in range(3):
            logger.info(f"嘗試生成摘要 (第 {attempt + 1} 次)")
            summary = summarize_text(transcription)
            if summary:
                logger.info("摘要生成成功")
                break
            time.sleep(2)
        
        text_to_send = summary if summary else transcription + "\n\n（無法總結）"
        try:
            logger.info("推送處理結果")
            line_bot_api.push_message(user_id, TextSendMessage(text=text_to_send))
            logger.info("推送完成訊息")
            line_bot_api.push_message(user_id, TextSendMessage(text="處理完成，感謝使用！"))
        except Exception as e:
            logger.error(f"推送訊息失敗: {e}")
    except Exception as exc:
        logger.error(f"任務處理失敗: {exc}")
        try:
            line_bot_api.push_message(user_id, TextSendMessage(text="處理失敗，請稍後再試"))
        except Exception as e:
            logger.error(f"推送錯誤訊息失敗: {e}")

# 建立任務佇列與工作執行緒（一次只處理一個任務）
task_queue = Queue()

def task_worker():
    while True:
        user_id, url = task_queue.get()
        process_task(user_id, url)
        task_queue.task_done()

worker_thread = Thread(target=task_worker, daemon=True)
worker_thread.start()

def submit_task(user_id: str, url: str):
    """提交任務至佇列"""
    task_queue.put((user_id, url))