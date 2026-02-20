## 2024-05-22 - ScriptEditor Accessibility
**Learning:** Icon-only buttons (Reset, Expand) in `ScriptEditor` lacked accessible names and keyboard focus indicators. This pattern of "icon button with tooltip but no aria-label" seems prevalent.
**Action:** When using icon-only buttons, always pair `title` (for mouse users) with `aria-label` (for screen readers) and ensure `focus-visible` styles are applied for keyboard navigation.
