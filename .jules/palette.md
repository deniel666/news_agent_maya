## 2024-05-27 - Contextual ARIA labels for Repeated Components
**Learning:** Generic labels like "Expand" or "Reset" fail screen reader users when multiple instances of the same component (like ScriptEditors) exist on the same page.
**Action:** Always include context in ARIA labels (e.g., `aria-label={\`Reset \${title} script\`}`) for repeated UI components.
