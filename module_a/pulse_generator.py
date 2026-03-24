"""
A4 — Pulse Generation (OpenAI)
Generates the summary note (≤250 words) and 3 action points (≤400 words total).
Single API call for token optimization.
"""

import json
import os
from pathlib import Path
from datetime import datetime

from openai import OpenAI
from dotenv import load_dotenv

from models.schemas import ThemedAnalysis, PulsePayload, ActionItem

load_dotenv()


def _load_prompt() -> str:
    """Load the pulse generation system prompt."""
    prompt_path = Path(__file__).parent / "prompts" / "pulse.txt"
    return prompt_path.read_text(encoding="utf-8")


def _build_analysis_block(analysis: ThemedAnalysis) -> str:
    """Format themed analysis into a text block for the LLM."""
    lines = ["THEMES:"]
    for t in analysis.themes:
        marker = " ★ TOP 3" if t.is_top_3 else ""
        lines.append(f"- {t.label}: {t.description} ({t.review_count} reviews){marker}")

    lines.append("\nQUOTES:")
    for q in analysis.quotes:
        lines.append(f'- [{q.theme_label}] "{q.text}" (Rating: {q.rating}/5)')

    return "\n".join(lines)


def generate_pulse(
    analysis: ThemedAnalysis,
    app_name: str = "IndMoney",
    source: str = "Google Play Store",
    review_count: int = 200,
) -> PulsePayload:
    """
    Generate a complete Pulse Payload using a single OpenAI API call.

    Args:
        analysis: PII-masked ThemedAnalysis from Module A2+A3.
        app_name: Name of the app.
        source: Review source (e.g., "Google Play Store").
        review_count: Number of reviews analyzed.

    Returns:
        Complete PulsePayload ready for approval review.
    """
    # Standard OpenAI API
    client = OpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
    )

    system_prompt = _load_prompt()
    analysis_block = _build_analysis_block(analysis)

    import time
    retries = 0
    max_retries = 3
    data = {}

    while retries <= max_retries:
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": analysis_block},
                ],
                temperature=0.3,
                # Grok/OpenAI JSON mode
                response_format={"type": "json_object"},
            )
            data = json.loads(response.choices[0].message.content)
            break
        except Exception as e:
            error_str = str(e)
            if ("429" in error_str or "rate_limit" in error_str.lower()) and retries < max_retries:
                wait_time = 15 * (2 ** retries)  # 15s, 30s, 60s
                print(f"  - Rate limit hit in pulse generator. Waiting {wait_time}s before retrying...")
                time.sleep(wait_time)
                retries += 1
            else:
                print(f"  - Error in pulse generator: {e}")
                raise e

    now = datetime.now()
    generated_at = now.strftime("%d-%b-%Y %H:%M")
    footer = f"Report generated on {generated_at} for {source.lower()}"

    action_items = []
    for item in data.get("action_items", []):
        action_items.append(
            ActionItem(
                id=item["id"],
                title=item["title"],
                description=item["description"],
                linked_theme=item["linked_theme"],
            )
        )

    return PulsePayload(
        metadata={
            "app_name": app_name,
            "source": source,
            "review_count": review_count,
            "generated_at": generated_at,
        },
        themes=analysis.themes,
        quotes=analysis.quotes,
        summary_note=data.get("summary_note", ""),
        action_items=action_items,
        footer=footer,
        approval_status="PENDING",
    )
