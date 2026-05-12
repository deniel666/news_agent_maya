## 2024-05-12 - [Focus Indicators and ARIA Labels on Icon-Only Buttons]
**Learning:** Found a missing accessibility pattern where icon-only buttons lacked proper `aria-label` and `aria-hidden` attributes for screen readers, as well as clear `focus-visible` states for keyboard navigation.
**Action:** Applied standard ARIA attributes (`aria-label`, `aria-hidden="true"`, `aria-expanded`) and explicit focus styling (`focus-visible:ring-2 focus-visible:ring-maya-500 focus:outline-none`) to ensure components are inclusive for keyboard and screen reader users.
