💡 What: Added ARIA labels, `aria-hidden` attributes for decorative SVG icons, dynamic `aria-expanded` attributes, and explicit keyboard focus indicators (`focus-visible:ring-2 focus-visible:ring-maya-500 focus:outline-none`) to the Reset, Save, and Expand/Minimize buttons inside the `ScriptEditor.tsx` component. Added a journal entry to `.jules/palette.md` noting the importance of contextual screen-reader labeling.

🎯 Why: To improve the accessibility and micro-UX for keyboard-only and screen reader users interacting with script segments. Because the script editor is instantiated multiple times on a single page, generic labels (like "Save" or "Expand") lose context. Passing the component's `title` into the labels provides crucial disambiguation.

📸 Before/After:
- **Before:** Buttons lacked clear active keyboard focus indicators, screen readers read out SVGs without descriptive names, and duplicate generic buttons lacked differentiation.
- **After:** Buttons have a bold `maya-500` ring on focus. Screen readers announce clear, context-specific labels like "Expand script editor for Local News" or "Save script changes for Business News" while skipping the purely decorative icons.

♿ Accessibility:
- Explicit `focus-visible:ring-2` allows keyboard navigators to clearly see what element has focus.
- `aria-hidden="true"` applied to SVG tags prevents repetitive noise.
- Contextual `aria-label` text utilizes the `title` prop.
- The expand button dynamically updates its `aria-expanded` and `aria-label` based on state.
