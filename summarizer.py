import google.generativeai as genai
from google.generativeai import GenerativeModel
from config import GEMINI_API_KEY
from typing import Optional

# 設定 API 金鑰
genai.configure(api_key=GEMINI_API_KEY)

model = GenerativeModel("gemini-2.0-flash")

def summarize_text(text: str) -> Optional[str]:
    """總結文字為繁體中文，字數不超過5000。
    
    若摘要超過限制，會嘗試在最後一個換行符處截斷，避免破壞 Markdown 語法。
    """
    try:
        prompt = f"請將以下文字做總結整理，使用繁體中文（台灣用法），字數不超過5000字，使用Markdown格式：{text}"
        response = model.generate_content(prompt)
        summary = response.text
        if len(summary) <= 5000:
            return summary

        cut_pos = summary.rfind('\n', 0, 5000)
        return summary[:cut_pos] if cut_pos != -1 else summary[:5000]
    except Exception as e:
        print(f"總結失敗: {e}")
        return None