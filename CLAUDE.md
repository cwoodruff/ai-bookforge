# AI Book Forge

This repo turns a folder of markdown source files into an AI-written book (EPUB, HTML, PDF). Claude Code runs the writing; Python scripts in `forge/` do everything deterministic. The scripts never call a model, and agents never touch the build.

## Layout

- `forge/`: the Python tool (`python3 -m forge --book <folder> <command>`). Commands: `init`, `ingest`, `briefs`, `check`, `status`, `diagrams`, `build`, `cover`, `links`.
- `profiles/technical-handson/`: chapter rules (`rules.yaml`) and the templates rendered into `build/briefs/`.
- `.claude/agents/`: `book-outliner`, `chapter-writer`, `grounding-reviewer`, `book-editor`.
- `.claude/commands/`: `/outline`, `/write`, `/write-all`, `/review`, `/edit`, `/build`.
- `examples/tiny-book/`: a complete small book, used as the test fixture.
- `tests/`: `python3 -m unittest discover -s tests`.

## A book folder

```
book.yaml            # settings + outline (parts/chapters/sources)
sources/**.md        # the author's material: the only authority for facts
book/front/*.md      # optional front matter (preface, foreword), built first
book/part-NN/chNN-*.md
book/appendices/app-X-*.md
solutions/chNN.md
build/               # generated: inventory, manifest, briefs, reports, diagrams
dist/                # generated: <slug>.epub / .html / .pdf
```

The book folder is the repo root by default; pass `--book examples/tiny-book` (or any folder) to work on another one.

## Workflow

`/outline` → the author reviews and edits book.yaml → `/write-all` → `/review` → `/edit` → `/build`.

## Rules when working on a book

- Treat `sources/` and the top of `book.yaml` as the author's canonical input. Never edit them unless the author asks.
- Facts come from the sources. Never invent commands, options, numbers, or APIs.
- Writing agents only write the files their brief says they own.
- Don't edit `build/` by hand; it is regenerated.

## Rules when working on the tool

- Keep it simple: standard library plus PyYAML. Pandoc, mermaid-cli (`mmdc`), and Chrome are the only external tools.
- Run `make test` and `make all BOOK=examples/tiny-book` before committing.
