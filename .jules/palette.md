## 2024-05-23 - Linking Headings to Custom Inputs
**Learning:** Custom form components (like `ScriptEditor`) often use headings as visual labels but lack programmatic association, making them inaccessible to screen readers.
**Action:** When encountering custom inputs with separate heading elements, always use `useId` to generate a unique ID and link them via `aria-labelledby` to ensure the label is correctly announced.
