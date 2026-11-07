# Plan: Generic AI Book Builder (from squad-book)

Name: **AI Book Forge** (`cwoodruff/ai-bookforge`). This is the original design plan; the README describes what shipped.

## 1. What squad-book actually is today

I went through the whole repo. It has three layers, and only one of them is code:

| Layer | What's there | Generic? |
|---|---|---|
| Build pipeline | `scripts/build.sh` (Pandoc), `mermaid.lua` (diagrams to PNG, cached by hash), `styles/epub.css`, `render-cover.sh` + `cover.html`, `gen-quiz-appendix.py`, `check-manuscript.py`, `check-coverage.py`, `check-links.sh`, CI workflow, Makefile | Mostly yes, but hardcoded to Squad (2 volumes, chapters 1 to 21 and 1 to 25, appendix letters A to J, macOS Chrome path, `mastering-squad-*` file names) |
| Writing process | `research/WRITER-BRIEF*.md`, `STYLE-GUIDE.md`, `CHAPTERS.md`, `RESTRUCTURE-BRIEF.md`, `coverage.csv`, `sources.txt` | The *pattern* is generic. The *content* is all Squad |
| Content | `book/`, `exercises/`, `sample/` (Tasktrack) | No |

The key gap: **the repo has no orchestration.** The briefs were handed to agents by hand ("Other agents are writing the other Part X chapters at the same time"). The pipeline that made the book lives in prompts and in your head, not in code. The generic product has to capture that part, not just copy the build scripts.

## 2. Product goal

A user drops markdown files into `sources/`, fills in a short `book.yaml`, and runs a few commands to get:

1. An AI-proposed outline and a source-to-chapter map, which they approve or edit
2. AI-written chapters grounded in their sources, written in parallel
3. Automated checks (structure, coverage, diagrams, grounding)
4. An editorial continuity pass
5. EPUB, single-page HTML, and PDF, with a generated cover

## 3. Pipeline (the stages)

```
sources/*.md
   |
   v
[1 ingest]   -> build/inventory.json   (id, path, title, headings, word count, hash)
   |
   v
[2 outline]  -> book.yaml: parts/chapters + coverage map     <-- HUMAN GATE
   |
   v
[3 brief]    -> build/briefs/chNN.md   (rendered from templates + book.yaml + assigned sources)
   |
   v
[4 write]    -> book/part-NN/chNN-slug.md + exercises/solutions/chNN.md   (parallel, one agent per chapter)
   |
   v
[5 check]    -> structure, coverage, mermaid render, links, grounding report
   |           (failures loop back to 4 for that chapter only)
   v
[6 edit]     -> continuity pass: cross-refs, "previous chapter" language, dedupe, terminology
   |
   v
[7 build]    -> dist/<slug>.epub / .html / .pdf
```

Stages 1, 3, 5, 7 are deterministic scripts. Stages 2, 4, 6 are AI. Keeping that split clean is the main design rule: the AI never touches the build, and scripts never call a model.

## 4. The one config file: `book.yaml`

Everything that's hardcoded in squad-book moves here. Example:

```yaml
title: "Mastering Widgets"
subtitle: "From First Steps to Production"
author: "Jane Doe"
lang: en-US
license: "CC BY 4.0"
profile: technical-handson        # selects chapter template + checks
volumes: false                    # true enables the vol1/vol2 layout
voice:
  person: second                  # you / we / third
  audience: "developers new to widgets"
  rules: [ "No emoji", "American English" ]
  terminology: { widget: "widget (lowercase)", WidgetCtl: "`widgetctl`" }
targets:
  words_per_chapter: [3000, 6000]
  min_diagrams: 2
companion_project: null           # optional path, like sample/ in squad-book
cover: { template: default, colors: ["#1e1b4b", "#7c3aed"] }
appendices:
  - { id: A, title: "Glossary", generate: glossary }
  - { id: B, title: "Quiz Answers", generate: quiz }
parts:                            # filled by stage 2, edited by the human
  - title: "Getting Started"
    chapters:
      - { slug: intro, title: "What Widgets Are", sources: [overview, faq], prereqs: [] }
```

Generated from it: Pandoc metadata, the chapter manifest, checker rules, quiz appendix, cover. That replaces `metadata-vol*.yaml`, `CHAPTERS.md`, `coverage.csv`, and the hardcoded numbers in the checkers.

## 5. Profiles (chapter templates)

The squad-book chapter template (What You'll Learn, Hands-On, Configuration Reference, Under the Hood, Pitfalls, Summary, Exercises, Quiz, Further Reading) becomes one profile. Each profile is a folder:

```
profiles/technical-handson/
  style-guide.md        # templated from research/STYLE-GUIDE.md, Squad specifics stripped
  writer-brief.md       # templated from WRITER-BRIEF.md
  editor-brief.md       # templated from RESTRUCTURE-BRIEF.md
  rules.yaml            # required H2s, min diagrams, exercises/quiz on/off
```

v1 ships one profile: `technical-handson` (squad-book style). The folder structure leaves room for `narrative` or `reference` later without code changes.

## 6. Engine: how the AI stages run

This is the big decision. Two options:

**A. Claude Code-native template (recommended).** The product is a template repo with `.claude/agents/` (outliner, writer, editor, grounding-reviewer) and slash commands (`/outline`, `/write ch03`, `/write-all`, `/edit`, `/review`). Claude Code runs the agents; the briefs are the prompts. This is how squad-book was actually produced, so it's proven. No API client code, no key handling, no retry logic to maintain. Downside: it requires Claude Code.

**B. Standalone CLI calling the API.** A Python (or .NET) CLI: `bookforge outline`, `bookforge write --parallel 6`. Runs headless in CI, works without Claude Code. Downside: I have to build concurrency, retries, rate limits, token budgeting, and cost tracking. That's a lot more code to own.

**Decision: A.** The briefs stay plain templates, so a CLI could wrap them later if it's ever needed.

## 7. Grounding: replacing "coverage"

squad-book's coverage check confirms each upstream doc URL is *cited* in its chapter. With user markdown there are no URLs, so I'd do it in two layers:

1. **Map coverage (deterministic):** every source in the inventory is assigned to at least one chapter, and no chapter points at a missing source. This is a straight port of `check-coverage.py`.
2. **Grounding review (AI):** a reviewer agent reads each chapter next to its assigned sources and flags claims not supported by them. Output is `build/reports/chNN-grounding.md`. It doesn't fail the build by default; it's a report you read. This replaces the manual verification work behind `VALIDATION.md`.

The writer brief will also tell the writer to mark anything it adds beyond the sources with an `> **Note:**` callout, the same way squad-book used `> **Preview:**`.

## 8. Repo layout of the product

```
bookforge/
  book.yaml.example
  sources/                  # user markdown goes here
  profiles/<name>/          # style guide, briefs, rules
  templates/cover.html
  styles/epub.css
  scripts/
    ingest.py               # stage 1
    render_briefs.py        # stage 3
    check_structure.py      # generalized check-manuscript.py
    check_coverage.py       # generalized map check
    gen_appendices.py       # quiz, glossary
    build.sh                # generalized, reads book.yaml
    mermaid.lua             # unchanged
    render_cover.sh         # Chrome path auto-detected (Linux/macOS/env)
  .claude/agents/           # outliner, writer, editor, grounding-reviewer
  .claude/commands/         # /outline /write /write-all /edit /review /build
  .github/workflows/build.yml
  examples/tiny-book/       # 3 source files -> 3 chapters, used as the test fixture
  Makefile
  README.md
```

Python stays as the script language since every existing script is already Python, bash, or Lua. Only dependency added: PyYAML.

## 9. Implementation phases

| Phase | Work | Done when |
|---|---|---|
| 0 | New repo (decided), port build scripts, strip Squad specifics, `book.yaml` loader | `examples/tiny-book` (hand-written chapters) builds to a valid EPUB |
| 1 | Generalize checkers (structure, coverage, quiz appendix) to read `book.yaml` + profile rules | `make check` passes on tiny-book; fails correctly on a broken fixture |
| 2 | `ingest.py` + `render_briefs.py` + `technical-handson` profile templated from squad-book briefs | Briefs render for every chapter of tiny-book |
| 3 | Agents and slash commands (outliner, writer, editor, reviewer) | From 3 raw markdown files: `/outline`, approve, `/write-all`, `/edit`, `make epub` produces a book with zero manual edits |
| 4 | Cover template parameterized, PDF output, CI workflow, README | CI green on tiny-book; EPUB, HTML, and PDF all produced |
| 5 (optional) | Rebuild squad-book on bookforge as the real-world proof | Mastering Squad builds from bookforge with no diff in structure |

## 10. PDF output

Chrome is already a dependency (Mermaid rendering and the cover), so PDF comes from printing the single-page HTML with headless Chrome (`--print-to-pdf`) plus a print stylesheet (`styles/print.css`: page size, margins, page breaks before each chapter, running headers). That avoids a LaTeX install. If you later want typeset-quality PDF, Pandoc + a LaTeX engine can slot in behind the same `make pdf` target.

## 11. Risks and open issues

- **Source size.** Big source sets won't fit in one writer's context. The coverage map handles this, since each writer only reads its assigned sources, but the outliner has to see everything. Plan: the outliner reads `inventory.json` (headings + summaries), not the full text.
- **Consistency across parallel writers.** This is what `RESTRUCTURE-BRIEF.md` was fixing after the fact. The editor pass (stage 6) is required, not optional.
- **Licensing.** The product should carry only MIT code. None of the Squad book text (CC BY 4.0) or Tasktrack should ship in it.
- **Pushing.** This session can read `cwoodruff/squad-book` but can't push to it. A new repo needs to be created and attached before I can push.
- **Pandoc version drift.** CI pins 3.6.4 and the local build used 3.12.1. I'll pin one version in both.
