import os
from fastapi import FastAPI, Request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from config import CHANNEL_ACCESS_TOKEN, CHANNEL_SECRET
from tasks import submit_task  # 改為引入 submit_task

# 初始化 Line Bot
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# FastAPI 應用程式
app = FastAPI()

def is_youtube_url(url: str) -> bool:
    """檢查是否為有效 YouTube 網址"""
    return "youtube.com" in url or "youtu.be" in url

@app.get("/")
async def root():
    return {"message": "Line Bot is running"}

@app.post("/callback")
async def callback(request: Request) -> dict:
    """處理 Line Webhook 回調"""
    signature = request.headers.get('X-Line-Signature')
    body = await request.body()
    try:
        handler.handle(body.decode(), signature)
    except InvalidSignatureError:
        return {"status": "Invalid signature"}, 400
    return {"status": "OK"}

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """處理用戶訊息"""
    print("handle_message triggered:", event.message.text)
    user_id = event.source.user_id
    message_text = event.message.text
    if is_youtube_url(message_text):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="處理中，請稍候")
        )
        # 提交任務到佇列
        submit_task(user_id, message_text)
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="網址無效，請重試")
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)