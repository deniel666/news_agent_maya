## 2025-05-05 - ScriptEditor IconButton Accessibility
**Learning:** Icon-only buttons using lucide-react components lack inherent screen-reader accessibility and keyboard focus indicators by default in this component. Adding `aria-label` to the button and `aria-hidden="true"` to the internal SVG, along with `focus-visible` ring styling is necessary.
**Action:** Always wrap icon-only buttons with `aria-label` and `focus-visible` styles, and hide the inner icon using `aria-hidden="true"` to prevent redundant screen reader announcements.
