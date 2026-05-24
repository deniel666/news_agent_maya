## 2024-05-24 - Contextual ARIA labels and SVG hiding
**Learning:** When icon-only buttons appear multiple times on a page (like inside repeated editors), generic ARIA labels lack context. Also, SVGs in icon-only buttons need `aria-hidden="true"` to prevent screen reader confusion.
**Action:** Always append the component's title or context to ARIA labels (e.g., `aria-label={\`Reset changes for ${title}\`}`) and apply `aria-hidden="true"` to the inner SVG icons. Ensure focus styles (`focus-visible:ring-2 focus-visible:ring-maya-500 focus:outline-none`) are present.
