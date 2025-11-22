# llm_client.py
import os
from typing import Optional

try:
    import openai
except Exception:
    openai = None

class LLMClient:
    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None):
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        self.model = model
        if openai:
            openai.api_key = os.getenv("OPENAI_API_KEY")

    def correct_grammar(self, text: str) -> str:
        if not openai:
            # No openai client - return original
            return text
        prompt = (
            "You are a careful editor. Correct grammar, punctuation, and phrasing in the following text "
            "while preserving meaning and named entities.\n\n"
            f"Text:\n{text}\n\nReturn only the corrected text."
        )
        try:
            resp = self.chat.completion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a grammar correcting assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=max(256, len(text) // 2 + 50)
            )
            corrected = resp.choices[0].message.content.strip()
            return corrected
        except Exception as e:
            print("LLM call failed:", e)
            return text
