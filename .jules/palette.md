## 2026-04-26 - Accessible Icon Toggle Groups
**Learning:** When implementing icon-only toggle button groups, standard ARIA labels aren't enough. The container needs role="group" and aria-label to define the relationship, and individual buttons must communicate their active state semantically via aria-pressed, while maintaining clear focus-visible styling for keyboard users.
**Action:** Always use aria-pressed for toggle button states instead of relying purely on visual active styles, and wrap related toggles in a role="group" container with an appropriate aria-label.
