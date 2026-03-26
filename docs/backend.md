# Backend Documentation

The backend of the IndMoney Weekly Product Pulse handles all the behind-the-scenes logic. It listens for requests from the frontend, runs the AI analysis, and sends the results back.

## Key Technologies

- **Python**: The main programming language used for the backend logic.
- **FastAPI**: A fast and lightweight framework for building the backend 'server'. It helps connect the frontend to our AI logic.
- **SQLite**: A simple, file-based database used to store the last 3 reports so users can view their history without needing a complex database setup.

## What It Does

1. **API Endpoints:** It provides specific "URLs" (endpoints) that the frontend calls, such as:
   - Generating a new pulse.
   - Fetching history.
   - Triggering PDF generation or email sending.
   - Manually triggering a fee data re-scrape.
2. **Analysis Pipeline:** When asked to generate a report, the backend runs the multi-step AI pipeline (fetching reviews, clustering, masking sensitive data, and summarizing).
3. **Data Formatting:** It formats all the AI-generated data into a clean structure that the frontend can easily read and display.
4. **Email Delivery (Gmail API):**
   - Primarily uses the **Gmail API** (via `googleapiclient`) for reliability in cloud environments.
   - Supports **OAuth2** (Personal accounts with refresh tokens) and **Service Accounts** (Workspace delegation).
   - Automatically fallbacks to SMTP if configured for local development.
5. **Fee Explainer (Module F):** When an email is sent, the backend:
   - Scrapes exit load data from IndMoney fund pages using `playwright` (cached monthly, on the 2nd Monday).
   - Generates 5 template-based bullets explaining exit load (neutral, facts-only).
   - Appends the fee section to the HTML email body.
   - Overwrites the Google Doc with a structured record (date, pulse summary, fee scenario, bullets, sources).
