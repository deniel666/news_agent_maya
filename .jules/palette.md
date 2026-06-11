## 2024-05-24 - Contextual ARIA labels for repeated components
**Learning:** Generic ARIA labels like "Expand" or "Reset" become confusing for screen reader users when a component like `ScriptEditor` is rendered multiple times on the same page.
**Action:** Always append the component's unique context (e.g., its `title` prop) to ARIA labels (e.g., `"Reset changes for " + title`) to provide clear differentiation between instances.
