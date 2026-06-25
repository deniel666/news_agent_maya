## 2025-02-12 - Debounced Search Query Re-Renders
**Learning:** In the `ContentLibrary.tsx` component, tying a rapid-firing state like `searchQuery` directly to a `useQuery` hook dependency without debouncing results in excessive network calls on every keystroke, leading to degraded application performance and backend stress.
**Action:** Always implement a `useDebounce` hook (e.g., `frontend/src/hooks/useDebounce.ts`) for text input states that trigger network requests, and pass the debounced value into the `useQuery` dependency array.
