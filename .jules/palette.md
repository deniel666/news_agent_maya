## 2025-02-12 - Reusable Component Accessibility Needs Context

**Learning:** When adding ARIA labels to identical controls (like 'Expand' or 'Reset' buttons) that appear multiple times on the same page (e.g., inside repeated `ScriptEditor` panels), generic labels are insufficient. A screen reader user would just hear "Expand, Expand, Expand" without knowing which script they are interacting with.

**Action:** Always inject contextual properties (like the `title` prop in a generic component) into `aria-label`s or use `aria-labelledby` to ensure the accessible name uniquely identifies the element's specific context (e.g., "Expand script editor for Local News").
