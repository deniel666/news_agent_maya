## 2024-07-02 - Accessible Icon Buttons in Lists
**Learning:** When using repetitive icon-only buttons in lists (like in a Content Library), they must not only have an `aria-label`, but the label must include context (e.g., "Delete [Story Title]") so screen reader users can distinguish between them.
**Action:** Always include the item's title in the `aria-label` for list actions, add `aria-hidden="true"` to the SVG to prevent redundant reading, and explicitly define focus styles using `focus-visible`.
