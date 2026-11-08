---
description: Check the manuscript and build EPUB, HTML, and PDF into dist/
argument-hint: "[epub html pdf] [--book folder]"
---
Parse "$ARGUMENTS" for formats (default all three) and `--book <folder>` (default `.`).

1. Run `python3 -m forge --book <book> build <formats>`. It runs every check first and stops on errors. For a release (the author says final, publish, or release), add `--gaps fail` so the build refuses while source gap notes remain; if the author wants to publish anyway, use `--gaps strip`, which leaves the notes out of the published files without touching the manuscript. Drafts keep the notes (`--gaps keep`, the default).
   Also run `python3 -m forge --book <book> stale`; if anything is stale, tell the author before building a release.
2. If checks fail, show the errors and suggest the command that fixes them (`/write N`, `/edit`). Don't edit the manuscript yourself.
3. If epubcheck is installed, run `epubcheck <book>/dist/<slug>.epub` and report the result.
4. Report the output files and their sizes.
