import re
import logging
import yt_dlp
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class YouTubeDownloader:
    """Downloads audio from YouTube and converts it to WAV."""

    _VIDEO_ID_PATTERN = re.compile(r"(?:v=|\/)([0-9A-Za-z_-]{11})")

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir

    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract the 11-character video ID from a YouTube URL."""
        match = self._VIDEO_ID_PATTERN.search(url)
        return match.group(1) if match else None

    def download(self, url: str) -> Optional[Path]:
        """Download audio and return the WAV file path, or None on failure."""
        video_id = self.extract_video_id(url)
        if not video_id:
            logger.error(f"Invalid YouTube URL: {url}")
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
            logger.error(f"Download failed: {e}")
            return None
