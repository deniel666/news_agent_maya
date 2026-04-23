## 2024-04-23 - Frontend Vite Bundling vs TypeScript Checking
**Learning:** In this specific codebase configuration, the frontend `pnpm build` script performs both a TypeScript check (`tsc`) and bundles the code (`vite build`). Pre-existing TypeScript errors across the repository currently cause `pnpm build` (and thus `tsc`) to fail with an exit code 2. However, these are strictly type-checking failures, and the actual build process via `npx vite build` can still succeed independently for production deployment if the codebase is functionally correct.
**Action:** When verifying frontend code changes and `pnpm build` fails due to unrelated TypeScript errors, manually run `npx vite build` to confirm whether the compilation step is viable despite the type issues.

## 2024-04-23 - Unintended Lockfile Generation
**Learning:** Running `pnpm install` natively generates an updated `pnpm-lock.yaml` file. Committing this automatically without intent clutters the repository with irrelevant dependency changes and can conflict with the intended scope of specific PRs (like a targeted performance patch).
**Action:** Always verify git status after running `pnpm` installation or script commands and discard unintended modifications to `pnpm-lock.yaml` using `rm frontend/pnpm-lock.yaml` or `git checkout -- pnpm-lock.yaml` before pushing.
