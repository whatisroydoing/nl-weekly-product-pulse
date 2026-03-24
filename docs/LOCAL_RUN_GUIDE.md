# Local Development Guide: IndMoney Weekly Product Pulse

This guide will teach you how to set up, run, and test the entire project on your local machine from scratch.

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed:
1.  **Python 3.9+**: [Download here](https://www.python.org/downloads/)
2.  **Node.js 18+**: [Download here](https://nodejs.org/) (Includes `npm`)
3.  **Git**: [Download here](https://git-scm.com/)

---

## 🛠️ Step 1: Clone and Environment Setup

Open your terminal (PowerShell or Command Prompt) and follow these steps:

1.  **Clone the Repository**:
    ```bash
    # (In your upskilling folder)
    cd nl-weekly-product-pulse
    ```

2.  **Create a Python Virtual Environment**:
    *This keeps your project dependencies isolated.*
    ```bash
    python -m venv venv
    .\venv\Scripts\activate  # Windows
    # source venv/bin/activate # Mac/Linux
    ```

3.  **Install Backend Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install Playwright Browsers**:
    *Required for the Fee Explainer scraper.*
    ```bash
    playwright install chromium
    ```

5.  **Install Frontend Dependencies**:
    ```bash
    cd module_e/frontend
    npm install
    cd ../.. # Go back to root
    ```

---

## ⚙️ Step 2: Configuration (.env)

The project relies on API keys and credentials. 

1.  **Create your `.env` file**:
    ```bash
    cp .env.example .env
    ```

2.  **Open `.env` and fill in the following**:
    -   `GEMINI_API_KEY`: Get from [Google AI Studio](https://aistudio.google.com/).
    -   `GROK_API_KEY`: Get from [xAI Console](https://console.x.ai/).
    -   `GMAIL_USER`: Your Gmail address.
    -   `GMAIL_APP_PASSWORD`: Generate an [App Password](https://myaccount.google.com/apppasswords) (Do not use your regular password).
    -   `GOOGLE_SERVICE_ACCOUNT_JSON`: Path to your JSON key (e.g., `./docs/google-service-account.json`).
    -   `GOOGLE_DOC_ID`: The alphanumeric ID from your Google Doc URL.

---

## 🚀 Step 3: Running the Application

You need **two separate terminal windows** running at the same time.

### Terminal 1: The Backend (FastAPI)
This handles the logic, AI, and database.
```bash
# Ensure venv is activated
uvicorn module_e.api:app --reload
```
*Your backend is now at http://localhost:8000*

### Terminal 2: The Frontend (React/Vite)
This provides the visual interface.
```bash
cd module_e.api:frontend
npm run dev
```
*Your app is now at http://localhost:5173*

---

## 🧪 Step 4: Testing Your Setup

1.  **Open your browser** to `http://localhost:5173`.
2.  **Click "Generate New Pulse"**: This tests Modules A (AI) and D (History).
3.  **Wait for completion**: Once done, you'll see a summary and action items.
4.  **Click "Send Email"**: This tests Modules B (Email), F1 (Scraper), and F3 (Google Docs).
5.  **Check your Email and Google Doc**: If the data appears in both, your integration is perfect!

---

## 📝 Common Commands & Troubleshooting

| Goal | Command |
|---|---|
| **Run All Tests** | `pytest` |
| **Manual Scrape** | `POST http://localhost:8000/api/fee-explainer/scrape` (via Postman/Curl) |
| **Reset Database** | Delete `reports.db` |
| **Port Conflict** | If `8000` is busy, use `uvicorn module_e.api:app --reload --port 8001` |

### Stale Scrape Data?
If the Fee Scraper isn't fetching fresh data, it's because it only scrapes on the **2nd Monday of the month** by default. You can force a re-scrape by calling the manual trigger endpoint above or deleting `data/fee_cache.json`.
