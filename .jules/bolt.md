## 2024-06-11 - Debouncing search input to prevent unnecessary API calls
**Learning:** In the ContentLibrary page, the search input directly sets `searchQuery` state, which is used as a dependency in the `useQuery` hook for fetching stories. This causes an API call on every keystroke, which is an unnecessary performance bottleneck.
**Action:** Always debounce state variables tied to input fields before passing them as dependencies to Tanstack `useQuery` to prevent excessive API calls.
