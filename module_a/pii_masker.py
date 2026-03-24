"""
A3 — PII Masking (Regex)
Scans quotes for personally identifiable information and replaces with [REDACTED].
No LLM tokens spent — pure regex.
"""

import re
from models.schemas import ThemedAnalysis


# PII patterns
_PATTERNS = {
    "email": re.compile(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", re.IGNORECASE
    ),
    "phone": re.compile(
        r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}"
    ),
    "account_number": re.compile(
        r"\b\d{8,16}\b"  # 8-16 digit sequences likely to be account/ID numbers
    ),
    "name_near_context": re.compile(
        # Capitalized words near PII-context keywords (prefix is case-insensitive, name is case-sensitive)
        r"(?i:my name is|i am|i'm|called|contact)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)"
    ),
}

PLACEHOLDER = "[REDACTED]"


def mask_text(text: str) -> str:
    """
    Replace PII patterns in a text string with [REDACTED].

    Args:
        text: Raw text potentially containing PII.

    Returns:
        Text with PII replaced by [REDACTED].
    """
    for pattern_name, pattern in _PATTERNS.items():
        if pattern_name == "name_near_context":
            # Replace just the captured name group
            text = pattern.sub(
                lambda m: m.group(0).replace(m.group(1), PLACEHOLDER)
                if m.group(1)
                else m.group(0),
                text,
            )
        else:
            text = pattern.sub(PLACEHOLDER, text)
    return text


def mask_analysis(analysis: ThemedAnalysis) -> ThemedAnalysis:
    """
    Apply PII masking to all quotes in a ThemedAnalysis.

    Args:
        analysis: ThemedAnalysis with potentially PII-containing quotes.

    Returns:
        ThemedAnalysis with all quote texts PII-masked.
    """
    for quote in analysis.quotes:
        quote.text = mask_text(quote.text)
    return analysis
