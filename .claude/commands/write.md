---
description: Write (or rewrite) specific chapters or appendices from their briefs, one agent each, in parallel
argument-hint: "<chapter numbers or appendix ids, e.g. 3 5-7 C> [--book folder]"
---
Parse "$ARGUMENTS": chapter numbers, ranges like `5-7`, appendix ids like `C`, and an optional `--book <folder>` (default `.`).

1. Run `python3 -m forge --book <book> briefs`.
2. If a target chapter already exists, writing replaces it from scratch and loses every edit made since (editor fixes, review fixes, hand edits). Unless the author explicitly asked to rewrite it, stop and suggest `/revise N` instead. When rewriting, if `build/reports/chNN-grounding.md` exists, tell the writer to read it and avoid repeating its issues.
3. Launch one `chapter-writer` agent per target, all in a single message so they run in parallel (at most 6 at a time; batch the rest). Each prompt is: the book folder, the brief path (`<book>/build/briefs/chNN.md` or `<book>/build/briefs/app-X.md`), and "Follow the brief exactly."
4. After all writers finish, run `python3 -m forge --book <book> check` and `python3 -m forge --book <book> diagrams`. For any target chapter that still has errors, relaunch its writer once with the error list. Don't fix chapters yourself.
5. For each target that now passes, run `python3 -m forge --book <book> stamp --chapter N` so changes to its sources are tracked from here.
6. Report per target: words, check status, and any source gaps the writer flagged.
