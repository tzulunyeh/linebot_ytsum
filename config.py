import os
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

#print("CHANNEL_ACCESS_TOKEN:", os.getenv('CHANNEL_ACCESS_TOKEN'))

# Gemini API 金鑰
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

# Line Bot 設定
CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')

# 臨時音檔儲存目錄
TEMP_DIR = 'temp_audio'

# 確保臨時目錄存在
os.makedirs(TEMP_DIR, exist_ok=True)