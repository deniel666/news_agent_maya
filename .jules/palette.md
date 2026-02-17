## 2025-02-17 - Consistent Loading States
**Learning:** Users perceive the application as "broken" or "empty" when async data loads without visual feedback (e.g., showing 0 stats or empty lists). Replacing these with a consistent spinner improves perceived performance and trust.
**Action:** Use the new `LoadingSpinner` component for all `useQuery` loading states instead of custom text or null rendering.
