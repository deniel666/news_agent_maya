
## 2025-02-17 - Accessible Icon-Only Buttons in Lists
**Learning:** When using icon-only buttons in lists (like in `StoryRow` or `StoryCard`), standard aria-labels are insufficient for screen readers as they do not provide context. For example, a simple "Delete" label is confusing when there are multiple delete buttons in a list. Also visible focus states (e.g., `focus-visible:ring-2`) are necessary for keyboard navigation.
**Action:** Always append the item's name or title to the `aria-label` for icon-only list action buttons (e.g., `aria-label={"Delete " + story.title}`), and ensure explicit visible focus styles (like `focus:outline-none focus-visible:ring-2`) are applied.
