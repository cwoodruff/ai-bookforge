---
description: Continuity edit across the book and apply grounding-review fixes
argument-hint: "[--book folder]"
---
Book folder: `--book <folder>` in "$ARGUMENTS", default `.`.

1. Run `python3 -m forge --book <book> check`. Every chapter must exist before editing; if any are missing, stop and suggest `/write-all`.
2. Split the chapters into contiguous groups of 3 to 5 (keep a part together when it fits). Launch one `book-editor` agent per group in parallel. Each prompt: the book folder and "You own Chapters A to B."
3. When all editors finish, run `check` and `diagrams`. If errors remain, relaunch the responsible editor once with the errors.
4. Report the editors' change lists, condensed, and any grounding fixes they rejected.
