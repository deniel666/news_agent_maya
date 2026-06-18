## 2024-06-18 - Repeated Interactive Controls Needs Context
**Learning:** When using repeated icon-only buttons (e.g. 'Expand', 'Reset', 'Save') across multiple identical panels like `ScriptEditor`, simple standard tooltips/labels aren't sufficient. Screen reader users get stuck not knowing *which* panel they are modifying.
**Action:** Always append the unique contextual identifier (e.g., `aria-label={\`Reset \${title} script\`}`) rather than generic static labels to avoid repetitive uninformative screen reader experiences.
