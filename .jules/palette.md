## 2026-02-26 - Icon-only Buttons & Form Labels
**Learning:** Icon-only buttons (like delete/edit) are completely inaccessible to screen readers without `aria-label`. Similarly, form inputs in modals often get disconnected from their labels if `htmlFor` and `id` are not explicitly set.
**Action:** Always add `aria-label` to buttons that only contain an icon. Always link `label` to `input` using `htmlFor` and `id` in forms, especially in dynamic contexts like modals.
