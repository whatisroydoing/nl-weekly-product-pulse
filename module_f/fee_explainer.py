"""
F2 — Fee Explainer
Template-based bullet generator (no LLM, zero cost).
Generates 5 bullets explaining exit load with both funds cited as examples in a single bullet.
"""

from models.schemas import FeeExplainerResult

def generate_fee_explanation(scrape_data: dict) -> FeeExplainerResult:
    """
    Generate the 5-bullet structured explanation based on scraped data.
    `scrape_data` is the expected output from F1's get_fee_data().
    """
    
    last_checked = scrape_data.get("last_scraped", "Unknown date")
    funds = scrape_data.get("funds", {})
    
    value_fund_name = "ICICI Prudential Value Fund"
    value_fund_data = funds.get(value_fund_name, {})
    value_exit_load = value_fund_data.get("exit_load", "1% if redeemed within 12 months (0-365 days) from the date of allotment.")
    
    bond_fund_name = "ICICI Prudential Corporate Bond Fund"
    bond_fund_data = funds.get(bond_fund_name, {})
    bond_exit_load = bond_fund_data.get("exit_load", "0% (Nil).")
    
    # 5-bullet template
    bullets = [
        "Exit load is a fee charged by mutual funds when units are redeemed before a specified holding period.",
        f"For example, {value_fund_name} charges {value_exit_load}, while {bond_fund_name} charges {bond_exit_load}",
        "Exit load is deducted from the redemption NAV at the time of payout.",
        "Exit load percentages and applicable periods vary across fund categories and schemes.",
        "Investors can verify current exit load details on the fund's official page or scheme information document."
    ]
    
    # Extract source links from the data
    source_links = [
        value_fund_data.get("url", "https://www.indmoney.com/mutual-funds/icici-prudential-value-fund-direct-plan-growth-3625"),
        bond_fund_data.get("url", "https://www.indmoney.com/mutual-funds/icici-prudential-corporate-bond-fund-direct-plan-growth-234")
    ]
    
    return FeeExplainerResult(
        scenario="Exit Load",
        bullets=bullets,
        source_links=source_links,
        last_checked=last_checked
    )

if __name__ == "__main__":
    # Test script iteration
    dummy_data = {
        "last_scraped": "2026-03-24",
        "funds": {
            "ICICI Prudential Value Fund": {
                "exit_load": "1%",
                "url": "https://url1"
            },
            "ICICI Prudential Corporate Bond Fund": {
                "exit_load": "Nil",
                "url": "https://url2"
            }
        }
    }
    result = generate_fee_explanation(dummy_data)
    print(result.model_dump_json(indent=2))
