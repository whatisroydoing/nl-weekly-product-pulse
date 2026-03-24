"""
Full Module A pipeline test — runs A1 → A2 → A3 → A4 via pipeline.py
"""
import asyncio
from dotenv import load_dotenv
from module_a.pipeline import run_pipeline

load_dotenv()

async def test_full_pipeline():
    print("Testing full Module A pipeline via pipeline.py...\n")
    try:
        pulse = run_pipeline(review_count=100)
        
        print("\n--- RESULT ---")
        print(f"App: {pulse.metadata.get('app_name')}")
        print(f"Reviews: {pulse.metadata.get('review_count')}")
        print(f"Generated: {pulse.metadata.get('generated_at')}")
        print(f"\nThemes ({len(pulse.themes)}):")
        for t in pulse.themes:
            star = " [TOP 3]" if t.is_top_3 else ""
            print(f"  - {t.label} ({t.review_count} reviews){star}")
        
        print(f"\nSummary Note ({len(pulse.summary_note.split())} words):")
        print(f"  {pulse.summary_note[:200]}...")
        
        print(f"\nAction Items ({len(pulse.action_items)}):")
        for item in pulse.action_items:
            print(f"  [{item.id}] {item.title}")
        
        print(f"\nApproval Status: {pulse.approval_status}")
        print("\nSUCCESS: Full Module A pipeline complete!")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
