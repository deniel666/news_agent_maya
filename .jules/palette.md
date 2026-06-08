## 2024-06-08 - Contextual ARIA labels for repeated components
**Learning:** When identical controls like "Expand" or "Reset" appear multiple times on the same page (e.g., inside repeated editor panels), screen reader users lose context if the labels are generic.
**Action:** Always include specific descriptive text in the ARIA label (e.g., `Expand script editor for [Title]`) to provide clear context for repeated UI components.
