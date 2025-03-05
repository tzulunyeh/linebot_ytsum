# YouTube 影片轉摘要機器人

這是一個基於 FastAPI 開發的 LINE Bot 機器人，能夠自動轉錄 YouTube 影片內容並生成摘要。當用戶傳送 YouTube 連結給機器人，它會下載影片的音訊，轉錄成文字，然後生成摘要並回傳給用戶。

## 功能特色

- 基於 LINE 平台，使用方便
- 使用 yt-dlp 下載 YouTube 影片音訊
- 採用 Whisper (faster-whisper) 進行高品質語音轉文字
- 利用 Gemini AI 生成摘要
- 能處理長達 60 分鐘的影片，生成摘要只需約 3 分鐘
- 多工處理，效能優化
- 錯誤處理與重試機制

## 系統需求

- Python 3.8 或更高版本
- FFmpeg（用於音訊處理）
- 可連接網際網路的伺服器或雲端服務

## 安裝方式

1. 克隆此專案：

```bash
git clone <repository-url>
cd youtube-video-summarizer
```

2. 安裝所需套件：

```bash
pip install -r requirements.txt
```

3. 設定環境變數：

在專案根目錄建立 `.env` 檔案，並設定以下環境變數：

```
GEMINI_API_KEY=<您的 Gemini API 金鑰>
CHANNEL_ACCESS_TOKEN=<您的 LINE 頻道存取權杖>
CHANNEL_SECRET=<您的 LINE 頻道密鑰>
```

## 使用說明

1. 啟動伺服器：

```bash
python main.py
```

或者使用 uvicorn：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

2. 設定 LINE Webhook URL：
   - 在 LINE Developer Console 中設定 Webhook URL 為 `https://<您的域名>/callback`

3. 掃描 QR 碼將機器人加為好友

4. 傳送 YouTube 網址給機器人

## 工作流程

1. 用戶傳送 YouTube 網址
2. 機器人驗證網址並回覆「處理中」
3. 下載影片音訊（WAV 格式）
4. 使用 Whisper 模型轉錄音訊內容
5. 使用 Gemini 模型生成摘要
6. 將摘要傳送給用戶
7. 刪除暫存檔案

## 檔案結構

- `main.py` - FastAPI 應用程式主入口
- `config.py` - 配置文件與環境變數管理
- `youtube_downloader.py` - 處理 YouTube 影片下載
- `transcription.py` - 音訊轉文字處理
- `summarizer.py` - 文字摘要生成
- `tasks.py` - 任務處理與隊列管理
- `requirements.txt` - 相依套件清單

## 技術架構

- **FastAPI**：用於建立 Web 服務
- **LINE Bot SDK**：與 LINE 平台整合
- **yt-dlp**：下載 YouTube 影片
- **faster-whisper**：高效音訊轉文字
- **Gemini AI**：生成高品質摘要
- **多執行緒與多處理程序**：實現並行處理

## 效能最佳化

- 使用多處理程序進行轉錄工作，避免阻塞主線程
- 實作任務佇列系統，確保穩定處理
- 錯誤處理與重試機制，提高可靠性

## 注意事項

- 請確保您已取得 Gemini API 與 LINE Messaging API 的使用授權
- 此機器人僅供學習和非商業用途
- 長影片處理可能需要較長時間和較多資源
- 請遵守 YouTube 使用條款
