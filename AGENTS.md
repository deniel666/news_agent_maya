# Repository Agent Instructions

## Jules Guardrails

Before creating a PR, inspect the current open pull requests and the current
`main` branch. If an equivalent fix already exists or has already landed, stop
and report that instead of creating another branch.

Do not create recurring daily PRs for the same pattern. If a task discovers a
repeated issue across the codebase, make one consolidated PR or ask for the
desired scope.

Do not commit PR body scratch files such as `pr_body.txt` or
`pr_description.txt`. Put PR text in the GitHub PR body only.

For accessibility work, prefer one focused PR per surface or component family.
For performance work, include the specific bottleneck, the expected request or
complexity reduction, and the verification command that was run.

For Supabase `.in_()` queries or updates, chunk lists to avoid PostgREST URL
length limits.
