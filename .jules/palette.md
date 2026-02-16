## 2026-02-16 - Script Editor Accessibility Pattern
**Learning:** Custom editor components like `ScriptEditor` often use disconnected titles and inputs, leading to accessibility gaps.
**Action:** Use `React.useId()` to programmatically link titles (via `id`) to inputs (via `aria-labelledby`) when visual layout prevents standard `<label>` wrapping.
