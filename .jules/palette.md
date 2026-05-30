## 2024-05-30 - Contextual ARIA labels for repeated controls
**Learning:** When identical controls like 'Expand' or 'Reset' appear multiple times on the same page inside repeated panels, generic ARIA labels are insufficient for screen readers as they lack context about which panel the control affects.
**Action:** Always include specific contextual data (like the panel's title) in the aria-label (e.g., `aria-label="Expand script editor for ${title}"`) to ensure the purpose of the button is unambiguous to assistive technologies.
