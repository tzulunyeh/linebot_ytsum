import logging
from typing import Optional

import google.generativeai as genai

logger = logging.getLogger(__name__)

_MAX_LENGTH = 5000


class GeminiSummarizer:
    """Summarizes text into Traditional Chinese using the Gemini API."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash") -> None:
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model_name)

    def summarize(self, text: str) -> Optional[str]:
        """Return a summary string, or None on failure."""
        try:
            prompt = (
                "請將以下文字做總結整理，"
                "使用繁體中文（台灣用法），"
                f"字數不超過{_MAX_LENGTH}字，使用Markdown格式：{text}"
            )
            response = self._model.generate_content(prompt)
            return self._truncate(response.text)
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return None

    def _truncate(self, text: str) -> str:
        """Truncate at the last newline within the limit to preserve Markdown."""
        if len(text) <= _MAX_LENGTH:
            return text
        cut_pos = text.rfind("\n", 0, _MAX_LENGTH)
        return text[:cut_pos] if cut_pos != -1 else text[:_MAX_LENGTH]
