## 2024-05-28 - Context-Aware ARIA Labels for List Items
**Learning:** When dealing with lists or tables that have repeated action buttons (e.g., View, Feature, Archive, Delete), using generic ARIA labels like "View" is insufficient and confusing for screen reader users. The context of which item is being interacted with is lost.
**Action:** Always include a unique identifier from the item (e.g., `story.title`) in the ARIA label for repeated action buttons to provide clear context (e.g., `aria-label={\`View ${story.title}\`}`).
