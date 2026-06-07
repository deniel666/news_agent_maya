## 2025-06-07 - Contextual ARIA labels for repeated editor panels
**Learning:** When adding ARIA labels to identical controls (e.g., 'Expand' or 'Reset' buttons) that appear multiple times on the same page (like inside repeated editor panels), ensure context is clear for screen readers by adding specific descriptive text (e.g., 'Expand script editor for [Title]') rather than generic labels.
**Action:** Always append contextual identifiers like titles or headings to `aria-label` for repeated icon-only buttons.
