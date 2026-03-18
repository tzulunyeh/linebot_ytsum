import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv


@dataclass
class AppConfig:
    """應用程式設定，集中管理所有環境變數。"""
    gemini_api_key: str
    channel_access_token: str
    channel_secret: str
    temp_dir: Path = field(default_factory=lambda: Path("temp_audio"))

    @classmethod
    def from_env(cls) -> "AppConfig":
        """從環境變數建立設定物件（替代建構子）"""
        load_dotenv()
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        return cls(
            gemini_api_key=gemini_api_key,
            channel_access_token=os.getenv("CHANNEL_ACCESS_TOKEN", ""),
            channel_secret=os.getenv("CHANNEL_SECRET", ""),
        )

    def ensure_temp_dir(self) -> None:
        """確保暫存目錄存在"""
        self.temp_dir.mkdir(exist_ok=True)
