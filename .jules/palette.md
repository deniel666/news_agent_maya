## 2024-05-25 - Contextual ARIA labels for repeated interactive elements
**Learning:** When identical interactive controls (like 'Expand' or 'Reset' buttons) appear multiple times on the same page (e.g., inside repeated editor panels), generic ARIA labels like "Reset" create ambiguity for screen reader users. They need context to know *which* item is being reset or expanded.
**Action:** Always inject contextual props (like the panel `title`) into the `aria-label` (e.g., \`Reset changes for \${title}\`) for repeated UI controls to ensure full accessibility and clear context.
