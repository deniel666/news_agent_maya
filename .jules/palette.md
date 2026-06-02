## 2024-06-02 - Contextual ARIA labels for repeated components
**Learning:** When creating identical controls (like Expand or Reset buttons) that appear multiple times on the same page (like inside repeated editor panels), screen readers announce generic labels.
**Action:** Use contextual aria-labels using specific descriptive text (e.g., `Expand script editor for ${title}`) to ensure screen reader users understand the specific target of the action.
