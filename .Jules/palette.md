## 2024-04-22 - Empty State Empty States
**Learning:** For frontend applications mostly driven by backend API states, Playwright tests checking visual regressions will hang on loading states unless API requests are mocked with the correct mock JSON structure.
**Action:** Always intercept API routes like `api/v1` and mock their exact expected JSON response (e.g. `{"stories": [], "tags": [], "stats": {}}`) to enable full UI rendering in Playwright, preventing Timeout errors on missing elements.
