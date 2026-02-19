## 2024-05-22 - Interactive Icon Accessibility
**Learning:** Interactive icon-only buttons (like in `ScriptEditor`) and links frequently lack `aria-label` attributes and explicit `focus-visible` styles, relying only on `title` or hover states which excludes keyboard and screen reader users.
**Action:** When touching any component with icon-only controls, systematically add `aria-label` matching the `title` and ensure `focus-visible` ring classes are applied to match the design system (e.g., `focus-visible:ring-2 focus-visible:ring-maya-500`).
