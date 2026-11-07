---
description: Write every chapter and agent-written appendix that is missing or failing checks
argument-hint: "[--book folder] [--force to rewrite everything]"
---
Book folder: `--book <folder>` in "$ARGUMENTS", default `.`.

1. Run `python3 -m forge --book <book> check --coverage`. If it fails, stop and tell the author to fix the outline (or run `/outline`).
2. Run `python3 -m forge --book <book> status`. Targets are every chapter whose state is `missing` or `failing`, or every chapter with `--force`.
3. Write the chapters exactly as `/write` does: run `briefs`, then one `chapter-writer` agent per chapter, launched in parallel batches of at most 6.
4. Then write each appendix that has no `generate:` and no file yet, the same way, using `build/briefs/app-X.md`. Appendices come after chapters because they reference them.
5. Run `check` and `diagrams`; relaunch writers once for chapters that still fail.
6. Show the `status` table and suggest `/review`, then `/edit`.
