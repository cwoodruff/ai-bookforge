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
| 3b | `/interview 2 5` | Optional: answers the gaps the writers flagged, then `/revise` folds the answers in. |
| 4 | `/review` | A fact-checker agent compares each chapter against its sources and writes `build/reports/chNN-grounding.md`. |
| 5 | `/edit` | Editor agents reconcile cross-references, terminology, and duplicated teaching, and apply the review fixes. |
| 6 | `/build` | Runs every check, then writes `dist/<slug>.epub`, `.html`, and `.pdf`. Say "final" for a release build (see Publishing). |

`make status` shows progress at any point.

## Changing a chapter after it's written

Use `/revise`, not `/write`. `/write 3` rewrites Chapter 3 from scratch and loses every edit made since (the editor's fixes, review fixes, and your own). `/revise` edits the chapter in place:

- `/revise 3 "shorten Under the Hood and add an example of retries"` applies your instruction.
- `/revise` with no arguments updates every **stale** chapter.

A chapter goes stale when a source it was written from changes, or when a source is added to or removed from its list (for example by `/interview`). Each time a chapter is written, revised, or edited, `forge stamp` records the hash of every source it used in `.forge/state.json`; commit that file with your book. `make stale` lists stale chapters, and `/revise` hands each writer an exact diff of what changed in its sources, so it updates every affected value and leaves the rest alone. `make status` also tells you which chapters were edited by hand since they were last stamped.

## How you give it information

You never paste content into the chat. Everything lives in files in the book folder:

| Where | What goes there |
|---|---|
| `sources/**.md` | The facts: notes, docs, specs, transcripts, drafts. The only place writers may take specific facts from. |
| `sources/**` images | Screenshots and figures (`.png`, `.jpg`, `.svg`, `.gif`, `.webp`). Reference each one from the source it belongs with, e.g. `![The settings page](images/settings.png)`. Writers can then use it in that source's chapter. |
| `book.yaml` (top) | Audience, voice, house rules, terminology, glossary, running example, cover |
| `book.yaml` (`parts:`) | The outline, proposed by `/outline` and edited by you |
| `book/front/*.md` | A preface or foreword in your own words |

Other formats need converting first, for example `pandoc notes.docx -o sources/notes.md`.

### When your knowledge isn't written down

`/interview` asks you questions and saves your answers, lightly edited, as new source files under `sources/interviews/`. Answering by dictation works fine. It has three modes:

- `/interview kickoff`: before outlining, walks you through the book's topics to create source material from scratch.
- `/interview 4 7`: after a draft, asks about the gaps the writers flagged in Chapters 4 and 7, adds the answers to those chapters' sources, and suggests `/write 4 7`.
- `/interview "deployment to Azure"`: one topic, filed with the chapter you choose.

Writers flag missing material with `> **Note:** The source material doesn't cover ...`. `make gaps` collects every one of those into `build/gaps.md`, and `make status` shows a gap count per chapter. That gap list is what the interview works from.

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
.forge/state.json       which source versions each chapter was written from (commit it)
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
- An image path in a chapter that doesn't exist
- Required sections missing or out of order (from the profile's `rules.yaml`)
- A missing prerequisites callout
- Fewer diagrams than `targets.min_diagrams`, or a diagram that won't render
- References to chapters or appendices that don't exist
- Invalid XML control characters that would break the EPUB

Word counts outside the target and code blocks without a language tag are warnings.

## Grounding

Writers are told that every specific fact (commands, options, numbers, versions, APIs) must come from their assigned sources, and that anything beyond them gets a `> **Note:**` callout. The `/review` step checks that independently and grades each chapter PASS, MINOR, or FAIL. Reviews are reports, not build failures. Read them before you publish.

## Publishing

While drafting, writers leave `> **Note:** The source material doesn't cover ...` callouts wherever your sources fall short. Those are useful to you and odd for readers, so release builds handle them explicitly:

| Command | Gap notes |
|---|---|
| `make all` | Kept (draft) |
| `make final` | The build fails while any remain, and lists where they are |
| `make final GAPS=strip` | Left out of the published files; the manuscript keeps them |

The usual route is to fill them: `make gaps`, then `/interview N`, then `/revise`, then `make final`. Also run `make stale` before a release.

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
| `make gaps` | `gaps [--chapter N]` | List every place a writer said the sources fall short |
| `make stale` | `stale [--diff]` | List chapters whose sources changed; `--diff` writes `build/changes/chNN.md` |
| `make stamp` | `stamp --all` or `--chapter N` | Record the sources each chapter was written from |
| `make final` | `build --gaps fail` (or `strip`) | Release build that won't ship gap notes |
| `make diagrams` | `diagrams [--chapter N]` | Render every Mermaid diagram to catch errors |
| `make epub` / `html` / `pdf` / `all` | `build [formats] [--skip-check] [--gaps keep\|strip\|fail]` | Build into `dist/` |
| `make cover` | `cover` | Render the cover only |
| `make links` | `links` | Check external links |
| `make test` | | Run the unit tests |

All make targets accept `BOOK=<folder>`.

## License

The code is MIT (see [LICENSE](LICENSE)). Books you make with it are yours, under whatever license you choose.
