"""
gemini_helper.py
-----------------
Single point of contact with Google's Gemini API.

Why centralize this?
  - Every module (chatbot, location score, SOS generator, journal) needs an LLM call.
  - We only want to configure the API key ONCE.
  - If the API key is missing or the request fails (e.g. no internet during judging),
    we fall back to a rule-based canned response so the demo NEVER crashes on stage.
"""

import config

_model = None
_configured = False


def _get_model():
    """Lazily configure and cache the Gemini model object."""
    global _model, _configured
    if _configured:
        return _model

    _configured = True
    if config.GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=config.GEMINI_API_KEY)
            _model = genai.GenerativeModel(config.GEMINI_MODEL_NAME)
        except Exception:
            _model = None
    return _model


def ask_gemini(prompt: str, system_instruction: str = "", temperature: float = 0.7) -> str:
    """
    Send a prompt to Gemini and return plain text.
    Falls back to a friendly offline message if the API is unavailable --
    the individual modules layer their OWN smarter fallbacks on top of this
    when they need guaranteed structured output (see modules/*.py).
    """
    model = _get_model()
    if model is None:
        raise RuntimeError("GEMINI_UNAVAILABLE")

    full_prompt = f"{system_instruction}\n\n{prompt}" if system_instruction else prompt
    response = model.generate_content(
        full_prompt,
        generation_config={"temperature": temperature, "max_output_tokens": 800},
    )
    return response.text.strip()


def is_live() -> bool:
    """Returns True if a real Gemini connection is configured."""
    return _get_model() is not None
