## 2024-06-14 - Repeated Generic Controls Require Specific Aria Labels
**Learning:** When UI components like editor toolbars (`ScriptEditor.tsx`) contain identical icon-only buttons (like "Reset" or "Expand") and these components are repeated multiple times on the same page, basic generic `aria-label`s (like "Expand") create ambiguity for screen reader users because they cannot tell *which* panel they are expanding.
**Action:** Always inject specific context (e.g., the panel's title prop) into the `aria-label` string (e.g., `Expand ${title}`) for generic controls inside reusable components.
