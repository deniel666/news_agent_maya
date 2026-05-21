## 2024-05-21 - Added Accessibility to ScriptEditor
**Learning:** Icon-only buttons and bare textareas in the `ScriptEditor` component lack semantic context for screen readers and miss dedicated keyboard focus states.
**Action:** Always wrap inner SVGs with `aria-hidden="true"`, supply descriptive `aria-label`s on the parent buttons, and add explicit `focus-visible:ring-2 focus-visible:ring-maya-500 focus:outline-none` classes to ensure visible keyboard navigation.
