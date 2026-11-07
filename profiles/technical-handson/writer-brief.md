# Writer Brief: Chapter {{chapter.number}}: {{chapter.title}}

You are writing one chapter of **{{book.title}}** by {{book.author}}. Other writers are working on other chapters at the same time, so stay inside the files listed under "You own".

## Read first, in this order

1. `{{paths.style_guide}}`: follow it exactly.
2. `{{paths.manifest}}`: the whole book, so you know what other chapters cover and can cross-reference them.
3. Every assigned source below, in full. These are the only authority for specific facts.

## Your chapter

- Part {{part.number}}: {{part.title}}
- Chapter {{chapter.number}}: {{chapter.title}}
- Scope: {{chapter.summary}}
- Template: `{{chapter.template}}`
- Prerequisites line: `> **Prerequisites:** {{chapter.prereqs}}`
- Previous chapter: {{chapter.previous}}
- Next chapter: {{chapter.next}}

## Assigned sources

{{chapter.sources}}

## Images you may use

{{chapter.images}}

Use an image where it teaches better than words, with a caption that says what to notice: `![The journal folder after the first run](sources/images/folder.png)`. Use these paths exactly. Never reference an image that isn't listed here.

Use other files in `sources/` only to check consistency, not as material for this chapter (they belong to other chapters).

## Required H2 sections, in this order

{{chapter.sections}}

Add your own concept H2 sections between the first section and the Hands-On section.

## You own

- `{{chapter.path}}`
- `{{chapter.solution_path}}` (H1 `# Chapter {{chapter.number}} Solutions`, then `## Exercise Solutions` and `## Quiz Answers`)

Don't edit any other file: not `book.yaml`, not other chapters, not `sources/`, not anything under `build/` or the tool code.

## Before you finish

1. `python3 -m forge{{book_flag}} check --chapter {{chapter.number}}` reports 0 errors. Treat a word-count warning as a prompt to check depth, not a reason to pad.
2. `python3 -m forge{{book_flag}} diagrams --chapter {{chapter.number}}` renders every diagram.
3. Reread the chapter against the sources once. Remove or flag (with a `> **Note:**`) any specific claim you can't point to in a source.

## Reply with

- Files written and approximate word count
- Any gaps in the sources you flagged, and any source contradictions you found
- Anything you would want the editor to reconcile with other chapters
