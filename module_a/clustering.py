"""
A2 — Theme Clustering (OpenAI)
Groups reviews into ≤5 themes, identifies top 3, extracts 3 quotes per top theme.
Processes reviews in configurable batches and aggregates results.
"""

import json
import os
import time
from pathlib import Path
from collections import defaultdict

from openai import OpenAI
from dotenv import load_dotenv

from models.schemas import RawReview, ThemedAnalysis, Theme, Quote
import yaml

load_dotenv()


def load_config():
    """Load configuration from config.yaml."""
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)


def _load_prompt() -> str:
    """Load the clustering system prompt."""
    prompt_path = Path(__file__).parent / "prompts" / "clustering.txt"
    return prompt_path.read_text(encoding="utf-8")


def _build_review_block(raw_reviews: list[RawReview]) -> str:
    """Format reviews into a text block for the LLM."""
    lines = []
    for i, r in enumerate(raw_reviews, 1):
        lines.append(f"[Review {i}] Rating: {r.rating}/5 | {r.text}")
    return "\n".join(lines)


def cluster_themes(raw_reviews: list[RawReview]) -> ThemedAnalysis:
    """
    Cluster reviews into themes using the Grok API, processing in batches.

    Args:
        raw_reviews: List of RawReview objects from ingestion.

    Returns:
        ThemedAnalysis with aggregated themes (≤5), top 3 flagged, and 9 quotes.
    """
    config = load_config()
    batch_size = config["llm"]["clustering"].get("batch_size", 50)
    max_themes = config["llm"]["clustering"].get("max_themes", 5)
    model = config["llm"]["clustering"].get("model", "grok-3")
    temperature = config["llm"]["clustering"].get("temperature", 0.2)

    # Standard OpenAI API
    client = OpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
    )

    system_prompt = _load_prompt()

    # Split reviews into chunks
    chunks = [raw_reviews[i:i + batch_size] for i in range(0, len(raw_reviews), batch_size)]

    all_themes: dict = defaultdict(lambda: {"description": "", "review_count": 0})
    all_quotes: list[Quote] = []

    print(f"Processing {len(raw_reviews)} reviews in {len(chunks)} batches of {batch_size}...")

    # 1. Process each chunk
    for idx, chunk in enumerate(chunks, 1):
        print(f"  - Clustering batch {idx}/{len(chunks)}...")
        review_block = _build_review_block(chunk)

        retries = 0
        max_retries = 3

        while retries <= max_retries:
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"REVIEWS:\n{review_block}"},
                    ],
                    temperature=temperature,
                    response_format={"type": "json_object"},
                )

                data = json.loads(response.choices[0].message.content)

                # Aggregate themes
                for t in data.get("themes", []):
                    label = t["label"].strip()
                    # Keep the longest description available
                    if len(t["description"]) > len(all_themes[label]["description"]):
                        all_themes[label]["description"] = t["description"]
                    all_themes[label]["review_count"] += t["review_count"]

                # Collect quotes
                for q in data.get("quotes", []):
                    all_quotes.append(
                        Quote(
                            text=q["text"],
                            theme_label=q["theme_label"].strip(),
                            rating=q.get("rating", 0),
                        )
                    )
                break  # Success, exit retry loop

            except Exception as e:
                error_str = str(e)
                if ("429" in error_str or "rate_limit" in error_str.lower()) and retries < max_retries:
                    wait_time = 15 * (2 ** retries)  # 15s, 30s, 60s
                    print(f"  - Rate limit hit. Waiting {wait_time}s before retrying...")
                    time.sleep(wait_time)
                    retries += 1
                else:
                    print(f"  - Error in batch {idx}: {e}")
                    raise e

    # 2. Consolidate and sort top themes
    consolidated_themes = []
    for label, data in all_themes.items():
        consolidated_themes.append(
            Theme(
                label=label,
                description=data["description"],
                review_count=data["review_count"],
                is_top_3=False,
            )
        )

    # Sort themes by review count descending and take max_themes (e.g., 5)
    consolidated_themes.sort(key=lambda x: x.review_count, reverse=True)
    final_themes = consolidated_themes[:max_themes]

    # Identify top 3
    top_theme_labels = []
    for i, t in enumerate(final_themes):
        if i < 3:
            t.is_top_3 = True
            top_theme_labels.append(t.label)

    # 3. Filter quotes to only include those from the top 3 themes (up to 3 per theme)
    final_quotes: list[Quote] = []
    quotes_per_theme: dict[str, int] = defaultdict(int)
    max_quotes_per_theme = config["llm"]["clustering"].get("quotes_per_theme", 3)

    # Sort quotes by rating ascending to surface critical feedback
    all_quotes.sort(key=lambda x: x.rating)

    for q in all_quotes:
        if q.theme_label in top_theme_labels and quotes_per_theme[q.theme_label] < max_quotes_per_theme:
            final_quotes.append(q)
            quotes_per_theme[q.theme_label] += 1

    return ThemedAnalysis(themes=final_themes, quotes=final_quotes)
