"""Universal LLM service supporting Anthropic, Google Gemini, and OpenAI.

Auto-detects the provider from the key format in .env:
- sk-ant-... -> Anthropic (Claude)
- AQ... or AIzaSy... -> Google Gemini
- sk-... -> OpenAI
Just changing the key in .env automatically switches the provider!
"""

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config import settings


def detect_provider(key: str) -> str:
    """Detect LLM provider from the API key format."""
    k = key.strip()
    if k.startswith("sk-ant-"):
        return "anthropic"
    if k.startswith("AQ.") or k.startswith("AIzaSy"):
        return "gemini"
    if k.startswith("sk-"):
        return "openai"
    return "gemini"  # default to gemini if unrecognized


def _generate_anthropic(
    prompt: str, system_prompt: Optional[str], key: str, max_tokens: int
) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=key)
    kwargs = {
        "model": "claude-3-5-haiku-20241022",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system_prompt:
        kwargs["system"] = system_prompt
    response = client.messages.create(**kwargs)
    return response.content[0].text.strip()


def _generate_gemini(
    prompt: str, system_prompt: Optional[str], key: str, max_tokens: int
) -> str:
    models_to_try = ["gemini-3.1-flash-lite", "gemini-3.8-flash", "gemini-3.5-flash"]
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": max_tokens},
    }
    if system_prompt:
        payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

    data = json.dumps(payload).encode("utf-8")
    last_error = None

    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res["candidates"][0]["content"]["parts"][0]["text"].strip()
        except urllib.error.HTTPError as e:
            last_error = e
            continue
        except Exception as e:
            last_error = e
            continue

    if last_error:
        raise last_error
    raise RuntimeError("All Gemini model endpoints failed.")


def generate_completion(
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = 1024,
) -> str:
    """Unified completion interface.

    Auto-detects the provider (Anthropic or Gemini) from the key format in .env.
    """
    key = settings.anthropic_api_key.strip()
    if not key:
        raise ValueError("No API key configured in .env.")

    provider = detect_provider(key)

    if provider == "anthropic":
        return _generate_anthropic(prompt, system_prompt, key, max_tokens)
    else:
        return _generate_gemini(prompt, system_prompt, key, max_tokens)
