# AI Book Forge

This repo turns a folder of markdown source files into an AI-written book (EPUB, HTML, PDF). Claude Code runs the writing; Python scripts in `forge/` do everything deterministic. The scripts never call a model, and agents never touch the build.

## Layout

- `forge/`: the Python tool (`python3 -m forge --book <folder> <command>`). Commands: `init`, `ingest`, `briefs`, `check`, `status`, `gaps`, `stale`, `stamp`, `diagrams`, `build`, `cover`, `links`.
- `profiles/technical-handson/`: chapter rules (`rules.yaml`) and the templates rendered into `build/briefs/`.
- `.claude/agents/`: `book-outliner`, `chapter-writer`, `grounding-reviewer`, `book-editor`.
- `.claude/commands/`: `/interview`, `/outline`, `/write`, `/write-all`, `/revise`, `/review`, `/edit`, `/build`. `/interview` runs in the main conversation, never in a subagent.
- `examples/tiny-book/`: a complete small book, used as the test fixture.
- `tests/`: `python3 -m unittest discover -s tests`.

## A book folder

```
book.yaml            # settings + outline (parts/chapters/sources)
sources/**.md        # the author's material: the only authority for facts
sources/**/*.png|svg # images, usable once a source references them
sources/interviews/  # answers captured by /interview
book/front/*.md      # optional front matter (preface, foreword), built first
book/part-NN/chNN-*.md
book/appendices/app-X-*.md
solutions/chNN.md
.forge/state.json    # source hashes per chapter at last write/revise/edit (committed)
build/               # generated: inventory, manifest, briefs, reports, diagrams
dist/                # generated: <slug>.epub / .html / .pdf
```

The book folder is the repo root by default; pass `--book examples/tiny-book` (or any folder) to work on another one.

## Workflow

(`/interview kickoff` if there are no notes yet) → `/outline` → the author reviews and edits book.yaml → `/write-all` → (`/interview N` for flagged gaps, then `/revise`) → `/review` → `/edit` → `/build`.

## Rules when working on a book

- Treat `sources/` and the top of `book.yaml` as the author's canonical input. Never edit them unless the author asks.
- Facts come from the sources. Never invent commands, options, numbers, or APIs.
- In an interview, record only what the author says; offer guesses only as questions they confirm.
- Writing agents only write the files their brief says they own.
- Don't edit `build/` by hand; it is regenerated.
- Change existing chapters with `/revise`, never `/write`, unless the author asks for a rewrite. Stamp chapters after writing, revising, or editing them.
- Release builds use `--gaps fail` (or `strip` if the author chooses).

## Rules when working on the tool

- Keep it simple: standard library plus PyYAML. Pandoc, mermaid-cli (`mmdc`), and Chrome are the only external tools.
- Run `make test` and `make all BOOK=examples/tiny-book` before committing.
