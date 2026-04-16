
## 2024-04-16 - ScriptEditor Accessibility Polish
**Learning:** Adding explicit focus-visible rings (`focus-visible:ring-2 focus-visible:ring-maya-500 focus:outline-none`) and dynamic ARIA labels (e.g., toggling between "Expand editor" and "Minimize editor") to custom icon-only UI components significantly improves keyboard navigation context without relying on default browser styling, which can be inconsistent against custom dark backgrounds.
**Action:** Consistently apply explicit `focus-visible` ring styling to all custom interactive controls and utilize state-driven ARIA labels for toggleable actions.
