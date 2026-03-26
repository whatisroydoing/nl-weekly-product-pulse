# Deployment Strategy

This document outlines the final deployment strategy for the IndMoney Weekly Product Pulse application.

## Strategy: Docker-based Containerization (Railway / Fly.io)

We have containerized the entire stack using Docker to ensure consistency, handle browser dependencies for scraping (Playwright), and maintain persistent report history.

### Components
1. **[Backend](file:///d:/Product%20Management/Upskilling/2026/Git%20Projects/nl-weekly-product-pulse/Dockerfile.backend)**: FastAPI + Playwright/Chromium.
2. **[Frontend](file:///d:/Product%20Management/Upskilling/2026/Git%20Projects/nl-weekly-product-pulse/module_e/frontend/Dockerfile.frontend)**: React/Vite served via Nginx (multi-stage build).
3. **[Orchestration](file:///d:/Product%20Management/Upskilling/2026/Git%20Projects/nl-weekly-product-pulse/docker-compose.yml)**: Docker Compose for local development and shared environment configuration.

---

## ✅ Implementation Status

- [x] Create `Dockerfile` for the FastAPI backend (Python/Uvicorn).
- [x] Create `Dockerfile` (multi-stage) for the React/Vite frontend using Nginx.
- [x] Set up `docker-compose.yml` for local orchestration.
- [x] Configure persistent volume mapping for `reports.db`.
- [x] Include Playwright Chromium binaries in the Docker image.
- [x] Securely manage environment variables (`.env`) for API keys.
- [x] Implement Gmail API OAuth2 flow for restricted cloud environments.

## 🚀 Final Deployment Steps (Railway)

1. **Connect GitHub**: Import the repository into [Railway](https://railway.app/).
2. **Add Volume**: In the Railway dashboard, add a **Volume** for the backend service and mount it to `/app/reports.db`.
3. **Configure Environment**: Add all keys from your `.env` (OPENAI_API_KEY, GMAIL_USER, etc.) to the Railway environment variables.
4. **Deploy**: Railway will automatically detect the `docker-compose.yml` and deploy both services.

---

## 🏗️ Option B: Pro-Split (Vercel + Railway)

This is the recommended "Zero-Cost Forever" approach.

### 1. Backend (Railway)
- Import repo to [Railway](https://railway.app/).
- Add a **Volume** for `/app/reports.db`.
- **Environment Variables**:
    - `ALLOWED_ORIGINS`: Set to your Vercel URL (e.g., `https://pulse.vercel.app`).
    - Standard keys: `OPENAI_API_KEY`, `GMAIL_USER`, etc.

### 2. Frontend (Vercel)
- Import repo to [Vercel](https://vercel.com/).
- **Root Directory**: Select `module_e/frontend`.
- **Environment Variables**:
    - `VITE_API_URL`: Set to your Railway backend URL (e.g., `https://pulse-backend.up.railway.app`).

---

## ⚠️ Security Checklist
- [x] Restrict CORS origins in `module_e/api.py`.
- [x] Use `ALLOWED_ORIGINS` to keep your backend private.
- [ ] Store `.env` securely (never commit to version control).
- [x] Maintain GitHub Actions for automated testing before deployment.
