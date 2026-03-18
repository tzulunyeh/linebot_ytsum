import logging

from fastapi import FastAPI, Request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from config import AppConfig
from pipeline import ProcessingPipeline
from summarizer import GeminiSummarizer
from tasks import TaskWorker
from youtube_downloader import YouTubeDownloader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LineBotHandler:
    """處理 LINE Webhook 事件。"""

    _YOUTUBE_DOMAINS = ("youtube.com", "youtu.be")

    def __init__(self, line_bot_api: LineBotApi, worker: TaskWorker) -> None:
        self._line_bot_api = line_bot_api
        self._worker = worker

    def is_youtube_url(self, url: str) -> bool:
        """檢查是否為有效 YouTube 網址"""
        return any(domain in url for domain in self._YOUTUBE_DOMAINS)

    def handle_message(self, event: MessageEvent) -> None:
        """處理用戶傳入的文字訊息"""
        user_id = event.source.user_id
        text = event.message.text
        logger.info(f"收到訊息 - user: {user_id}, text: {text}")

        if self.is_youtube_url(text):
            self._line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="處理中，請稍候"),
            )
            self._worker.submit(user_id, text)
        else:
            self._line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="網址無效，請重試"),
            )


config = AppConfig.from_env()
config.ensure_temp_dir()

line_bot_api = LineBotApi(config.channel_access_token)
webhook_handler = WebhookHandler(config.channel_secret)

pipeline = ProcessingPipeline(
    downloader=YouTubeDownloader(config.temp_dir),
    summarizer=GeminiSummarizer(config.gemini_api_key),
)

worker = TaskWorker(pipeline=pipeline, line_bot_api=line_bot_api)
worker.start()

bot_handler = LineBotHandler(line_bot_api=line_bot_api, worker=worker)

app = FastAPI()


@webhook_handler.add(MessageEvent, message=TextMessage)
def handle_message(event: MessageEvent) -> None:
    bot_handler.handle_message(event)


@app.get("/")
async def root() -> dict:
    return {"message": "Line Bot is running"}


@app.post("/callback")
async def callback(request: Request) -> dict:
    """處理 LINE Webhook 回調"""
    signature = request.headers.get("X-Line-Signature")
    body = await request.body()
    try:
        webhook_handler.handle(body.decode(), signature)
    except InvalidSignatureError:
        return {"status": "Invalid signature"}, 400
    return {"status": "OK"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
