
## 2024-05-18 - [Accessible Icon Toggle Buttons]
**Learning:** When using icon-only toggle buttons (like View Mode switches for grid/list), visual styling isn't enough for screen readers. Using `role="group"`, `aria-label`, and dynamic `aria-pressed` attributes ensures semantic meaning, and specific focus styles (`focus-visible`) enable keyboard accessibility.
**Action:** Always ensure icon-only interactive elements in groups are wrapped in a container with `role="group"`, have explicit `aria-label`s, communicate state via `aria-pressed` or `aria-expanded`, and include clear keyboard focus indicators.
