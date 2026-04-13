## 2024-04-13 - Added ARIA labels and focus states to ScriptEditor icon buttons
**Learning:** Icon-only utility buttons (like Reset/Minimize in floating editor panels) frequently lack both screen reader context and keyboard focus visibility, breaking accessibility for non-mouse users navigating dense toolbars.
**Action:** Always verify `aria-label` and `focus-visible:ring-2 focus-visible:ring-maya-500 focus:outline-none` on standard `<button>` elements containing only icons (like Lucide `RotateCcw` or `Maximize2`).
