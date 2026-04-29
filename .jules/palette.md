## 2026-04-29 - [Accessible View Toggles]
 **Learning:** Standard `aria-pressed` combined with `role="group"` is crucial for conveying the state of multi-button toggle controls. Ensure that visual focus states like `focus-visible:ring-2` are accompanied by `focus:outline-none` to override default browser outlines in Tailwind.
 **Action:** Always wrap toggle button sets in a container with `role="group"` and explicitly define `aria-pressed` on individual buttons to indicate active state.
