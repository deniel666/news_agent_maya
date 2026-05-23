## 2024-05-23 - Context-aware ARIA labels for repeated components
**Learning:** When identical controls (like 'Expand' or 'Reset' buttons) appear multiple times on the same page (e.g., inside repeated editor panels for different topics), a generic `aria-label="Expand"` is insufficient for screen readers because the context is lost.
**Action:** Always include specific contextual descriptive text in the `aria-label` (e.g., `aria-label="Expand editor for [Title]"`) or use `aria-labelledby` to ensure the context is clear for screen readers navigating these identical controls.
