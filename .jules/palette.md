## 2026-02-12 - Icon-only Button Accessibility
**Learning:** The application uses icon-only buttons extensively (e.g., in ScriptEditor) but lacks consistent ARIA labeling and focus indicators, making them inaccessible to keyboard and screen reader users. The design system uses `maya-500` for focus rings (`focus-visible:ring-2 focus-visible:ring-maya-500`).
**Action:** When adding or modifying icon-only interactive elements, always include `aria-label` and the specific `focus-visible` utility classes to ensure accessibility compliance and visual consistency.
