import os
from typing import Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

class LLMClient:
    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None):
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        self.model = model
        self.client = None
        
        if OpenAI:
            # Try to get key from arg or env
            key = api_key or os.getenv("OPENAI_API_KEY")
            if key:
                self.client = OpenAI(api_key=key)
            else:
                # If no key is found, we can still try to instantiate, 
                # but it might fail later or rely on other config. 
                # However, usually OpenAI() raises error if no key.
                # Let's try to instantiate safely.
                try:
                    self.client = OpenAI()
                except Exception:
                    self.client = None

    def correct_grammar(self, text: str) -> str:
        if not self.client:
            # No openai client - return original
            return text
        prompt = (
            "Correct the grammar, punctuation, and phrasing of the text below. "
            "Preserve meaning and named entities. "
            "Do NOT output any conversational text like 'Sure', 'Here is', or 'Please'. "
            "Output ONLY the corrected text.\n\n"
            f"Text:\n{text}"
        )
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a strict grammar correcting assistant. You output ONLY the corrected text with no preamble or explanation."},
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
