## 2025-05-15 - Icon-only Button Accessibility
**Learning:** Icon-only buttons in `ScriptEditor.tsx` (and potentially other components) lack `aria-label` attributes and visible focus states, making them inaccessible to screen readers and keyboard users.
**Action:** Always add `aria-label` and `focus-visible:ring-2` (or similar focus styles) to icon-only buttons. Use the `cn` utility to merge these classes.
