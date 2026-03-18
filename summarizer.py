import logging
from abc import ABC, abstractmethod
from typing import Optional

import google.generativeai as genai

logger = logging.getLogger(__name__)


class BaseSummarizer(ABC):
    """摘要器的抽象介面。

    示範 OOP 概念：
    - 抽象 (Abstraction)：定義「要做什麼」，不定義「怎麼做」
    - ABC (Abstract Base Class)：強制子類別實作 summarize()
    - 多型 (Polymorphism)：可以替換不同的摘要實作（Gemini、OpenAI 等）

    未來若要換成 OpenAI，只需建立 OpenAISummarizer(BaseSummarizer) 即可，
    不需修改任何呼叫端的程式碼。
    """

    MAX_LENGTH = 5000

    @abstractmethod
    def summarize(self, text: str) -> Optional[str]:
        """將文字摘要，失敗時回傳 None"""
        ...

    def _truncate(self, text: str) -> str:
        """若超過字數限制，在最後換行處截斷，避免破壞 Markdown 語法"""
        if len(text) <= self.MAX_LENGTH:
            return text
        cut_pos = text.rfind("\n", 0, self.MAX_LENGTH)
        return text[:cut_pos] if cut_pos != -1 else text[:self.MAX_LENGTH]


class GeminiSummarizer(BaseSummarizer):
    """使用 Google Gemini API 進行摘要。

    示範 OOP 概念：
    - 繼承 (Inheritance)：繼承 BaseSummarizer 的介面與輔助方法
    - 封裝 (Encapsulation)：API 金鑰和 model 隱藏在 instance 內部
    - 依賴注入 (DI)：api_key 從外部傳入，不在內部讀取環境變數
    """

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash") -> None:
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model_name)

    def summarize(self, text: str) -> Optional[str]:
        try:
            prompt = (
                "請將以下文字做總結整理，"
                "使用繁體中文（台灣用法），"
                f"字數不超過{self.MAX_LENGTH}字，使用Markdown格式：{text}"
            )
            response = self._model.generate_content(prompt)
            return self._truncate(response.text)
        except Exception as e:
            logger.error(f"總結失敗: {e}")
            return None
