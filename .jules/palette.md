## 2024-05-24 - Interactive Element Accessibility
**Learning:** Icon-only buttons lacking `aria-label`s are a common accessibility gap in the existing React components (e.g., `ScriptEditor.tsx`). Furthermore, interactive elements often lack clear focus visibility styles, making keyboard navigation difficult.
**Action:** When creating or reviewing icon-only buttons, systematically ensure an `aria-label` is present and explicit focus styling (e.g., `focus-visible:ring-2 focus-visible:ring-maya-500 focus:outline-none`) is applied to aid screen readers and keyboard users.
