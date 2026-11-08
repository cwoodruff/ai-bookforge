---
description: Write every chapter and agent-written appendix that is missing or failing checks
argument-hint: "[--book folder] [--force to rewrite everything]"
---
Book folder: `--book <folder>` in "$ARGUMENTS", default `.`.

1. Run `python3 -m forge --book <book> check --coverage`. If it fails, stop and tell the author to fix the outline (or run `/outline`).
2. Run `python3 -m forge --book <book> status`. Write targets: every chapter whose state is `missing` or `failing` (every chapter with `--force`, which overwrites all edits; confirm with the author first). Revise targets: every chapter whose state is `stale`.
3. Write the chapters exactly as `/write` does: run `briefs`, then one `chapter-writer` agent per chapter, launched in parallel batches of at most 6.
4. Then write each appendix that has no `generate:` and no file yet, the same way, using `build/briefs/app-X.md`. Appendices come after chapters because they reference them.
5. Revise the stale chapters exactly as `/revise` does (with their `build/changes/chNN.md`).
6. Run `check` and `diagrams`; relaunch writers once for chapters that still fail. Then `python3 -m forge --book <book> stamp --chapter N` for each chapter written or revised that passes.
7. Show the `status` table and suggest `/review`, then `/edit`.
