## 2024-05-31 - Context-Specific ARIA Labels for Repeated Controls
**Learning:** When adding ARIA labels to identical controls (e.g., 'Expand' or 'Reset' buttons) that appear multiple times on the same page (like inside repeated editor panels), generic labels create confusion for screen reader users. Context must be clear.
**Action:** Always use specific descriptive text incorporating the context (e.g., `aria-label={"Reset changes for " + title}`) rather than generic labels like "Reset changes".
