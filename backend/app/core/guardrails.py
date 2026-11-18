"""Security Guardrails: PII Masking, Prompt Injection Screen, Canary Token, and Citation Validation.

Enforces security in CODE, not prompts (per AGENTS.md rule 8):
1. PII Masking: Redacts credit cards, emails, phone numbers before LLM and logs.
2. Prompt-Injection Screen: Rejects jailbreaks, prompt leaks, and instruction overrides in code.
3. Canary Token: Detects if the model leaked internal system instructions.
4. Citation Validity: Verifies that cited source indices [n] exist in the retrieved context.
"""

import re
from typing import List, Optional, Tuple

# Unique canary token embedded in system instructions
CANARY_TOKEN = "SHOPEASY_CANARY_SEC_74829"

# Common prompt injection, instruction override, and system leak regex patterns
INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts|rules|commands)",
    r"(?i)disregard\s+(all\s+)?(previous|above|prior)",
    r"(?i)(print|show|reveal|display|output|dump)\s+(your\s+)?(system\s+prompt|instructions|initial\s+prompt)",
    r"(?i)you\s+are\s+now\s+(in\s+)?(dan|developer\s+mode|unrestricted|jailbreak)",
    r"(?i)bypass\s+(safety|content)\s+filters",
    r"(?i)<\s*(system|instruction|prompt)\s*>",
    r"(?i)\[\s*INST\s*\]",
    r"(?i)<<\s*SYS\s*>>",
]

INJECTION_REGEXES = [re.compile(p) for p in INJECTION_PATTERNS]

# PII Regex Patterns
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
CARD_REGEX = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
# Indian mobile numbers: optional +91, starts with 6-9, followed by 9 digits
PHONE_REGEX = re.compile(r"\b(?:\+91[-\s]?)?[6-9]\d{9}\b")


def mask_pii(text: str) -> str:
    """Mask sensitive PII (emails, payment card numbers, phone numbers) before LLM or logging.

    Args:
        text: Raw customer message or log content.

    Returns:
        Sanitized string with PII replaced by redaction placeholders.
    """
    if not text:
        return ""

    masked = text

    # 1. Mask Payment Card Numbers (must run before phone regex to avoid partial matches)
    masked = CARD_REGEX.sub("[CARD_REDACTED]", masked)

    # 2. Mask Email Addresses
    masked = EMAIL_REGEX.sub("[EMAIL_REDACTED]", masked)

    # 3. Mask Phone Numbers
    masked = PHONE_REGEX.sub("[PHONE_REDACTED]", masked)

    return masked


def screen_prompt_injection(text: str) -> Tuple[bool, Optional[str]]:
    """Scan incoming user message for prompt injection or system instruction override attempts.

    Args:
        text: Customer's input message.

    Returns:
        Tuple of (is_flagged: bool, warning_message: Optional[str]).
    """
    if not text:
        return False, None

    for pattern in INJECTION_REGEXES:
        if pattern.search(text):
            return (
                True,
                "Your request could not be processed because it contains disallowed instruction overrides. How may I assist you with your ShopEasy orders or store policies?",
            )

    return False, None


def check_canary_leak(response: str) -> bool:
    """Check if the model's generated response contains the secret canary token.

    Returns:
        True if the canary was leaked (security breach detected), False otherwise.
    """
    if not response:
        return False
    return CANARY_TOKEN in response


def sanitize_response(response: str) -> str:
    """Intercept model response if a canary token leak or system dump is detected."""
    if check_canary_leak(response):
        return (
            "I apologize, but I cannot fulfill that request. "
            "How may I help you with your ShopEasy orders or store policies?"
        )
    return response


def validate_citations(answer: str, num_sources: int) -> Tuple[bool, str]:
    """Validate that citation references [n] in the answer exist in the provided sources.

    Args:
        answer: Model's generated answer text.
        num_sources: Total number of source documents provided in context.

    Returns:
        Tuple of (is_valid: bool, sanitized_answer: str).
        If an invalid citation index is found (e.g. [5] when only 2 sources exist),
        it strips the hallucinated citation.
    """
    if not answer or num_sources <= 0:
        return True, answer

    citation_pattern = re.compile(r"\[(\d+)\]")
    found_citations = citation_pattern.findall(answer)

    is_valid = True

    def replace_invalid(match: re.Match) -> str:
        nonlocal is_valid
        idx = int(match.group(1))
        # Valid source indices are 1..num_sources
        if 1 <= idx <= num_sources:
            return match.group(0)
        is_valid = False
        return ""  # Strip hallucinated citation

    sanitized = citation_pattern.sub(replace_invalid, answer)
    # Clean up any leftover double spaces from removed citations
    sanitized = re.sub(r" +", " ", sanitized).strip()

    return is_valid, sanitized
