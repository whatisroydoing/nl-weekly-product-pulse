import json
from pathlib import Path
from google_play_scraper import Sort, reviews
from models.schemas import RawReview
import yaml
from langdetect import detect

def load_config():
    """Load configuration from config.yaml."""
    config_path = Path("config.yaml")
    if not config_path.exists():
        # Return minimal default config if file is missing
        return {"app": {"app_id": "com.indmoney", "name": "IndMoney", "source": "Google Play Store"}, "ingestion": {"min_words_per_review": 5, "allowed_review_counts": [100, 200, 300, 400]}}
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def fetch_reviews(review_count: int) -> list[RawReview]:
    """
    Fetch reviews from Google Play Store and apply quality filters.
    
    Filters:
    1. Min 50 characters (configurable).
    2. No duplicates.
    3. No rating-only (empty/whitespace text).
    
    Saves the final resulting set to data/raw_reviews.json.

    Args:
        review_count: Number of reviews to return (200, 300, or 400).

    Returns:
        Filtered list of RawReview objects.
    """
    config = load_config()
    app_id = config["app"]["app_id"]
    min_words = config["ingestion"].get("min_words_per_review", 5)
    allowed_counts = config["ingestion"]["allowed_review_counts"]

    if review_count not in allowed_counts:
        raise ValueError(
            f"review_count must be one of {allowed_counts}, got {review_count}"
        )

    # To ensure we get enough quality reviews after filtering, we scrape 2.5x the count
    fetch_multiplier = 2.5
    scrape_count = int(review_count * fetch_multiplier)

    print(f"     Scraping {scrape_count} reviews to filter down to {review_count}...")
    result, _ = reviews(
        app_id,
        lang="en",
        country="in",
        sort=Sort.NEWEST,
        count=scrape_count,
    )

    filtered_reviews = []
    seen_texts = set()

    for r in result:
        text = r.get("content", "")
        if not text: # Ignore None or empty
            continue
            
        clean_text = text.strip()
        
        # Filter 1 & 3: Minimal words and rating-only (empty after strip)
        if not clean_text or len(clean_text.split()) < min_words:
            continue
            
        # Filter: Must be in English
        try:
            if detect(clean_text) != 'en':
                continue
        except:
            # Drop review if langdetect can't process it (e.g. only numbers)
            continue
            
        # Filter 2: Ignore duplicates
        if clean_text in seen_texts:
            continue
            
        seen_texts.add(clean_text)

        filtered_reviews.append(
            RawReview(
                text=clean_text,
                rating=r.get("score", 0),
                date=str(r.get("at", "")),
                source="Google Play Store",
            )
        )
        
        # Stop once we have reached the requested count
        if len(filtered_reviews) >= review_count:
            break

    # Save to data/raw_reviews.json
    output_path = Path("data/raw_reviews.json")
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([r.model_dump() for r in filtered_reviews], f, indent=2, ensure_ascii=False)
    
    print(f"     Saved {len(filtered_reviews)} quality reviews to {output_path}")

    return filtered_reviews
