# AI Book Forge

Turn a folder of your own markdown notes into an AI-written, fact-checked technical book, published as EPUB, HTML, and PDF.

AI Book Forge grew out of [Mastering Squad](https://github.com/cwoodruff/squad-book), a two-volume book written by AI agents working from briefs. This repo packages that process so it works for any subject. You supply the source material and approve the outline. Claude Code agents write, fact-check, and edit the chapters. Plain Python scripts check the manuscript and build the book.

```
sources/*.md ─► ingest ─► outline ─► (you approve) ─► briefs ─► write ─► check ─► review ─► edit ─► build
                           AI                                    AI                 AI       AI
```

The design rule: **the scripts never call a model, and the agents never touch the build.** Every AI step is driven by a rendered brief you can read, and every AI output is checked by deterministic code.

## What you need

- [Claude Code](https://claude.com/claude-code) for the writing steps
- Python 3.10+ with PyYAML (`pip install pyyaml`)
- [Pandoc](https://pandoc.org) 3.x
- [mermaid-cli](https://github.com/mermaid-js/mermaid-cli) (`npm install -g @mermaid-js/mermaid-cli`) for diagrams
- Google Chrome or Chromium, for diagrams, the cover, and the PDF (set `CHROME=/path/to/chrome` if it isn't found)
- Optional: [epubcheck](https://www.w3.org/publishing/epubcheck/) to validate the EPUB

On macOS: `brew install pandoc epubcheck && npm install -g @mermaid-js/mermaid-cli`.

## Quick start

```bash
git clone https://github.com/cwoodruff/ai-bookforge my-book && cd my-book
make init                     # creates book.yaml and sources/
cp ~/notes/*.md sources/      # your material: docs, notes, transcripts, specs
$EDITOR book.yaml             # title, author, audience, voice rules
claude                        # start Claude Code in the repo
```

Then, inside Claude Code:

| Step | Command | What happens |
|---|---|---|
| 1 | `/outline` | Inventories `sources/` and proposes parts, chapters, and which sources feed each chapter. **Stops for your review.** |
| 2 | (you) | Edit the `parts:` section of `book.yaml` until the outline is right. |
| 3 | `/write-all` | One writer agent per chapter, in parallel, each following its brief. Failing chapters are retried once. |
| 4 | `/review` | A fact-checker agent compares each chapter against its sources and writes `build/reports/chNN-grounding.md`. |
| 5 | `/edit` | Editor agents reconcile cross-references, terminology, and duplicated teaching, and apply the review fixes. |
| 6 | `/build` | Runs every check, then writes `dist/<slug>.epub`, `.html`, and `.pdf`. |

`/write 3 5-7` rewrites specific chapters. `make status` shows progress at any point.

To see a finished result first, build the example: `make all BOOK=examples/tiny-book`.

## Keeping a book outside this repo

Every command takes a book folder. Keep the tool in one place and your books anywhere:

```bash
make init BOOK=~/books/widgets
python3 -m forge --book ~/books/widgets status
```

In Claude Code, pass it to the commands: `/outline ~/books/widgets`, `/write-all --book ~/books/widgets`.

## The book folder

```
book.yaml               settings and outline
sources/**.md           your material, the only authority for facts
book/front/*.md         optional preface or foreword, placed before Chapter 1
book/part-NN/chNN-*.md  chapters (written by agents)
book/appendices/        agent-written appendices
solutions/chNN.md       exercise solutions and quiz answers
build/                  generated: inventory, manifest, briefs, reports, diagrams
dist/                   the finished book
```

## book.yaml

`book.yaml.example` documents every key. The important ones:

| Key | Purpose |
|---|---|
| `title`, `subtitle`, `author`, `description`, `license` | Book metadata and the cover |
| `profile` | Chapter template and briefs (`technical-handson`) |
| `voice` | Audience, person, tone, house rules, and terminology. All of it goes into every brief. |
| `targets` | Words per chapter (a warning) and minimum diagrams per chapter (an error) |
| `companion_project` | An optional running example that each Hands-On section builds on |
| `cover` | Gradient colors and tagline for the generated cover, or `image:` for your own |
| `glossary` | Terms for a generated glossary appendix |
| `appendices` | Generated (`quiz`, `glossary`) or agent-written from a `brief:` |
| `exclude_sources` | Sources you deliberately leave out (otherwise every source must be used) |
| `parts` | The outline: chapters with `title`, `slug`, `summary`, `sources`, `prereqs`, `template` |

Chapters are numbered continuously across parts. Change the outline and run `make briefs` before rewriting chapters.

## What the checks enforce

`make check` (and every build) fails on:

- A source that isn't assigned to any chapter, or a chapter that names a missing source
- A missing chapter or solutions file, or the wrong chapter title
- Required sections missing or out of order (from the profile's `rules.yaml`)
- A missing prerequisites callout
- Fewer diagrams than `targets.min_diagrams`, or a diagram that won't render
- References to chapters or appendices that don't exist
- Invalid XML control characters that would break the EPUB

Word counts outside the target and code blocks without a language tag are warnings.

## Grounding

Writers are told that every specific fact (commands, options, numbers, versions, APIs) must come from their assigned sources, and that anything beyond them gets a `> **Note:**` callout. The `/review` step checks that independently and grades each chapter PASS, MINOR, or FAIL. Reviews are reports, not build failures. Read them before you publish.

## The technical-handson profile

Each chapter has: What You'll Learn, concept sections, Hands-On, Quick Reference, Under the Hood, Pitfalls and Troubleshooting, Summary, Exercises, and Quiz. Opening chapters can use the `light` template, which drops the reference sections. Quiz answers are collected into an appendix automatically.

To customize, copy `profiles/technical-handson/` to `profiles/<name>/` (in this repo or inside your book folder), edit `rules.yaml` and the templates, and set `profile: <name>`. Templates use `{{placeholders}}`; an unknown placeholder is an error, so a brief never ships with a blank.

## Styling

`styles/epub.css` styles all three editions; `styles/print.css` adds page size, margins, page numbers, and page breaks for the PDF. Put your own copies in `<book>/styles/` to override them. The cover comes from `templates/cover.html` (1600x2400); set `cover.template` to use your own.

## Commands

| Make | `python3 -m forge ...` | Does |
|---|---|---|
| `make init` | `init` | Create `book.yaml` and `sources/` |
| `make ingest` | `ingest` | Write `build/inventory.md` |
| `make briefs` | `briefs` | Render the manifest, style guide, and briefs |
| `make check` | `check [--chapter N] [--coverage]` | Run the deterministic checks |
| `make status` | `status` | Show per-chapter state, word count, issues, and review status |
| `make diagrams` | `diagrams [--chapter N]` | Render every Mermaid diagram to catch errors |
| `make epub` / `html` / `pdf` / `all` | `build [formats] [--skip-check]` | Build into `dist/` |
| `make cover` | `cover` | Render the cover only |
| `make links` | `links` | Check external links |
| `make test` | | Run the unit tests |

All make targets accept `BOOK=<folder>`.

## License

The code is MIT (see [LICENSE](LICENSE)). Books you make with it are yours, under whatever license you choose.
