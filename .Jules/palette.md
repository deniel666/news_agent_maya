## 2024-04-23 - View Mode Icon Toggle Accessibility
**Learning:** Icon-only toggle button groups in the Content Library lacked ARIA labels and focus visibility, relying solely on active state styling. This pattern is common but makes the interface inaccessible to screen readers and keyboard users.
**Action:** Always add explicit `aria-label`, `title`, and `focus-visible:ring-2` to icon-only buttons, especially in toggle groups.
