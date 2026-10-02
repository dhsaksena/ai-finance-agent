from google import genai
from google.genai import types
from google.genai import errors
import time

from stock_research.config import Config


class GeminiClient:

    def __init__(self, model: str = None, temperature: float = None):
        self.client = genai.Client()
        self.model = model or Config.GEMINI_MODEL
        self.temperature = temperature or Config.RESEARCH_TEMPERATURE

    def research(self, prompt: str, use_search: bool = False, max_retries: int = 3) -> str:
        """
        Run a research query.

        Args:
            prompt: The research question / prompt
            use_search: If True → use live Google Search grounding
                        If False → use only Gemini model knowledge
            max_retries: Number of retries on rate-limit (429) errors
        """
        tools = []
        if use_search:
            tools = [types.Tool(google_search=types.GoogleSearch())]

        config = types.GenerateContentConfig(
            tools=tools,
            temperature=self.temperature
        )

        last_error = None

        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=config,
                )

                if not response.text:
                    raise RuntimeError("Gemini returned an empty response")

                return response.text

            except errors.ClientError as e:
                last_error = e

                # Handle rate limit (429)
                if getattr(e, "code", None) == 429 or "RESOURCE_EXHAUSTED" in str(e):
                    if attempt < max_retries - 1:
                        wait_seconds = 30 * (attempt + 1)  # 30s → 60s → 90s
                        print(f"Rate limited (429). Waiting {wait_seconds}s before retry {attempt + 2}/{max_retries}...")
                        time.sleep(wait_seconds)
                        continue
                    else:
                        raise RuntimeError(
                            "Gemini rate limit exceeded after retries. "
                            "Check https://aistudio.google.com/rate-limit or wait for daily reset."
                        ) from e
                else:
                    # Other client errors → fail immediately
                    raise

        raise last_error