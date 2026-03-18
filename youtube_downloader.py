import re
import logging
import yt_dlp
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class YouTubeDownloader:
    """負責從 YouTube 下載音檔。

    示範 OOP 概念：
    - 封裝 (Encapsulation)：output_dir 儲存在 instance 內，不從外部傳入每次呼叫
    - 單一職責 (SRP)：只負責下載，不處理轉錄或摘要
    - 私有屬性：_output_dir 以底線開頭，表示內部實作細節
    """

    _VIDEO_ID_PATTERN = re.compile(r"(?:v=|\/)([0-9A-Za-z_-]{11})")

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir

    def extract_video_id(self, url: str) -> Optional[str]:
        """從 URL 擷取 YouTube 影片 ID"""
        match = self._VIDEO_ID_PATTERN.search(url)
        return match.group(1) if match else None

    def download(self, url: str) -> Optional[Path]:
        """下載音檔並轉換為 WAV，回傳檔案路徑；失敗時回傳 None"""
        video_id = self.extract_video_id(url)
        if not video_id:
            logger.error(f"無效的 YouTube URL: {url}")
            return None

        output_path = self._output_dir / video_id
        options = {
            "format": "bestaudio",
            "outtmpl": str(output_path),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            }],
        }

        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([url])
            return output_path.with_suffix(".wav")
        except Exception as e:
            logger.error(f"下載失敗: {e}")
            return None
