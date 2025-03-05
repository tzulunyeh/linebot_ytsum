import re
import yt_dlp
from config import TEMP_DIR
import os
from typing import Optional

def download_audio(url: str) -> Optional[str]:
    """從 YouTube 下載音檔並轉換為 WAV 格式"""
    try:
        # 使用正規表達式提取影片 ID
        pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11})"
        match = re.search(pattern, url)
        if not match:
            print(f"無效的 YouTube URL: {url}")
            return None
        video_id = match.group(1)
        
        output_path = os.path.join(TEMP_DIR, f"{video_id}")
        
        options = {
            "format": "bestaudio",
            "outtmpl": output_path,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            }],
        }
        
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])
        
        # 返回帶引號的完整路徑
        return f"{output_path}.wav"  # 會自動處理字串引號
        
    except Exception as e:
        print(f"下載失敗: {str(e)}")
        return None