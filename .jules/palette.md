## 2026-06-16 - Contextualizing Identical Icon Buttons
**Learning:** When a component like `ScriptEditor` is rendered multiple times on a page (e.g., Local, Business, Tech news), generic `aria-label`s on icon-only buttons (like "Expand" or "Reset") create confusing, indistinguishable announcements for screen reader users.
**Action:** Always interpolate contextual properties (like the section `title`) into the `aria-label` (e.g., `aria-label={"Expand script editor for " + title}`) when identical controls are grouped or mapped, to ensure clear, specific context.
