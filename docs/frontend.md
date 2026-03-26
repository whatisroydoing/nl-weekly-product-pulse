# Frontend Documentation

The frontend of the IndMoney Weekly Product Pulse is the part of the application that users see and interact with.

## Key Technologies

- **React**: A popular library for building user interfaces. It helps us create interactive, reusable components.
- **Vite**: A fast build tool that helps our React code run quickly and smoothly during development and in production.
- **Tailwind CSS**: A styling tool that lets us design the application quickly without writing lots of custom CSS code. It makes the app look clean and modern.

## What It Does

1. **User Input:** It allows the user to select how many reviews to analyze (200, 300, or 400) and click a button to generate a pulse summary.
2. **Review Screen:** It displays the generated pulse, which includes the top themes, quotes, and an executive summary.
3. **Take Action:** It provides buttons for the user to approve the report and either download it as a PDF or send it via email to up to 5 people.
4. **History & Rehydration:** It lets users view their last 3 generated pulse reports and restores the full dashboard state (themes, quotes, actions) when a historical report is selected.

> **Note:** The Fee Explainer (Module F) is **email-only** — it is not displayed in the frontend UI or the PDF export. The fee section is appended to the HTML email body when sending reports. All timestamps displayed (e.g., in history or report headers) are shown in **24-hour IST format**.
