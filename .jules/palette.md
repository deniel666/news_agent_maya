## 2024-06-01 - Context-Aware ARIA Labels for Repeated Components
**Learning:** Generic labels like "Expand" or "Reset" fail screen reader users when a component like `ScriptEditor` appears multiple times on the same page. Without contextual clues, users cannot distinguish which script they are manipulating.
**Action:** Always inject unique properties (e.g., `title`) into `aria-label` values (e.g., `aria-label={\`Reset changes for ${title}\`}`) when building reusable editor panels or repeated interactive elements.
