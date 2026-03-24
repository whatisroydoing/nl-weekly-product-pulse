"""
Module A — Pipeline Orchestrator
Chains A1 (Ingestion) → A2 (Clustering) → A3 (PII Masking) → A4 (Pulse Generation)
into a single run_pipeline() call.
"""

import yaml
from models.schemas import PulsePayload
from module_a.ingestion import fetch_reviews
from module_a.clustering import cluster_themes
from module_a.pii_masker import mask_analysis
from module_a.pulse_generator import generate_pulse


def load_config():
    """Load configuration from config.yaml."""
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)


def run_pipeline(review_count: int) -> PulsePayload:
    """
    Run the full Module A pipeline end-to-end.

    Steps:
        A1 — Fetch reviews from Google Play Store
        A2 — Cluster reviews into themes (OpenAI)
        A3 — Mask PII in quotes (regex)
        A4 — Generate summary + action points (OpenAI)

    Args:
        review_count: Number of reviews to fetch (100, 200, or 300).

    Returns:
        A complete PulsePayload with approval_status="PENDING".
    """
    config = load_config()
    app_name = config["app"]["name"]
    source = config["app"]["source"]

    # A1 — Ingestion
    print(f"[A1] Fetching {review_count} reviews from {source}...")
    raw_reviews = fetch_reviews(review_count)
    print(f"     Fetched {len(raw_reviews)} reviews.")

    # A2 — Clustering
    print("[A2] Clustering themes...")
    analysis = cluster_themes(raw_reviews)
    print(f"     Found {len(analysis.themes)} themes.")

    # A3 — PII Masking
    print("[A3] Masking PII in quotes...")
    masked_analysis = mask_analysis(analysis)
    print(f"     Masked {len(masked_analysis.quotes)} quotes.")

    # A4 — Pulse Generation
    print("[A4] Generating pulse summary and action points...")
    pulse = generate_pulse(
        analysis=masked_analysis,
        app_name=app_name,
        source=source,
        review_count=review_count,
    )
    print("     Pulse generated.")

    return pulse
