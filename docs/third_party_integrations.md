# Third-Party Integrations

The IndMoney Weekly Product Pulse relies on a few external tools and services to fetch data, generate insights, and send reports.

## Services Used

1. **Google Play Scraper:**
   - **What it does:** Fetches raw user reviews directly from the Google Play Store.
   - **Why we use it:** It is lightweight and doesn't require a browser to work, making the data collection fast and simple.

2. **Large Language Models (OpenAI / Gemini / Grok):**
   - **What it does:** We use AI models to group reviews into "Themes" and to extract the most useful quotes. AI is also used to generate the final summary note and action points.
   - **Why we use it:** These models evaluate the reviews much faster than a human could and summarize the most important points with high accuracy. The exact provider (e.g. OpenAI `gpt-4o-mini`) can be switched depending on cost and performance needs.

3. **ReportLab (PDF Export):**
   - **What it does:** Generates the downloadable PDF version of the product pulse.
   - **Why we use it:** It gives us fine-grained control over exactly how the PDF looks, ensuring a professional layout.

4. **Gmail / SMTP (Email Output):**
   - **What it does:** Sends the final product pulse report to team members via email. The email body also includes a Fee Explainer section with exit load bullets when available.
   - **Why we use it:** Allows the user to easily distribute insights right from the application. It is set up to use a simple SMTP or Gmail App Password setup.

5. **Playwright (Fee Scraping):**
   - **What it does:** Uses a headless Chromium browser to scrape exit load data from IndMoney mutual fund pages.
   - **Why we use it:** IndMoney pages are JavaScript-rendered and block direct HTTP requests (403). Playwright enables reliable data extraction from these pages. Scraping runs on the 2nd Monday of each month and results are cached locally.

6. **Google Docs API (Record Overwrite):**
   - **What it does:** After each email send, overwrites the designated Google Doc with a structured report (date, pulse summary, fee scenario, bullets, sources).
   - **Why we use it:** Provides a persistent, shareable record of the latest pulse in a familiar Google Doc format. Overwriting ensures the doc reflects only the most recent analysis.
