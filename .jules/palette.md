## 2024-05-23 - ScriptEditor Accessibility
**Learning:** Interactive components like icon-only buttons often lack accessible names (`aria-label`) and visible focus states, making them unusable for keyboard and screen reader users. Also, `textarea` elements without visible labels need `aria-label` for context.
**Action:** Always verify `aria-label` presence on icon buttons and ensure `focus-visible` styles are applied. Use `role="status"` for dynamic status updates like "Unsaved changes".
