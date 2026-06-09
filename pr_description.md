**💡 What:**
Implemented a `useDebounce` custom React hook and applied it to the `searchQuery` state in the `ContentLibrary` component.

**🎯 Why:**
The `ContentLibrary` component was re-fetching data from the backend via TanStack's `useQuery` on every single keystroke in the search bar. This caused unnecessary network requests and backend load, which degrades performance as the dataset scales.

**📊 Impact:**
By debouncing the search query state by 300ms, we drastically reduce the number of API calls made to `listStories` when a user types, improving both frontend responsiveness and backend efficiency.

**🔬 Measurement:**
1. Open the Network tab in DevTools.
2. Navigate to the Content Library.
3. Type a multi-character string in the search bar.
4. Verify that only a single API request is dispatched after typing pauses (instead of a request for every letter).
