## 2024-05-24 - Accessible Icon-Only Buttons
**Learning:** Interactive icon-only buttons in this application's design system frequently lack both screen reader context (`aria-label`) and keyboard navigation visibility.
**Action:** Always add explicit `aria-label` attributes and `focus-visible:ring-2 focus-visible:ring-maya-500` classes to icon-only buttons to ensure full accessibility.
