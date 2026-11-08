---
description: Revise existing chapters in place (author instructions, changed sources, or new interview material) without losing edits
argument-hint: "[chapter numbers, default all stale] [\"what to change\"] [--book folder]"
---
Parse "$ARGUMENTS": chapter numbers or ranges, an optional quoted instruction from the author, and `--book <folder>` (default `.`).

1. Run `python3 -m forge --book <book> briefs` and then `python3 -m forge --book <book> stale --diff`. That writes `build/changes/chNN.md` for every chapter whose sources changed since it was last written.
2. Targets: the chapters named, or every stale chapter if none were named. If there are no targets and no instruction, say the book is current and stop. A named chapter that isn't stale and has no instruction: ask the author what to change.
3. Skip any target that doesn't exist yet; tell the author to use `/write` for those.
4. Launch one `chapter-writer` agent per target, in parallel batches of at most 6. Each prompt:
   - "REVISE" and the book folder
   - the brief path, `<book>/build/briefs/chNN.md`
   - the changes file path, if the chapter is stale
   - the author's instruction, word for word, if there is one
5. When all finish, run `python3 -m forge --book <book> check` and `diagrams`. Relaunch a writer once with the errors if its chapter fails.
6. For each target that now passes, run `python3 -m forge --book <book> stamp --chapter N`.
7. Report what changed per chapter, plus anything the writers said affects other chapters. If changes cross chapters, suggest `/edit`.
