# Style Guide: {{book.title}}

Every writer and editor follows this guide. It is rendered from `book.yaml` and the `technical-handson` profile, so change those, not this file.

## The book

- Title: {{book.title}}
- Subtitle: {{book.subtitle}}
- Author: {{book.author}}
- Description: {{book.description}}
- Chapters: {{book.chapter_count}} (see `{{paths.manifest}}` for titles, files, and source assignments)

## Voice and audience

- Audience: {{voice.audience}}. They progress from beginner to capable practitioner over the book.
- Person: {{voice.person}}. Active voice.
- Tone: {{voice.tone}}. Explain *why* as well as *how*.
- House rules:
{{voice.rules}}
- Terminology (use exactly as written):
{{voice.terminology}}

## Grounding: the sources are the authority

The book is written from the author's source material in `sources/`. The inventory is `{{paths.inventory}}`.

- Every specific fact (names, numbers, versions, commands, flags, file names, config keys, API names, dates, quotes) must come from your assigned sources. Never invent one.
- You may add general, widely known background a competent expert would not dispute (what HTTP is, what a loop does). Keep it brief.
- If the chapter needs something the sources do not cover, either leave it out or flag it in a callout that starts with these exact words: `> **Note:** The source material doesn't cover ...`. Never paper over a gap with a plausible guess. These notes are collected by `forge gaps` so the author can fill them (for example with `/interview`), so keep the wording exact and say precisely what is missing.
- If two sources disagree, say so in the text and follow the more specific or more recent one.
- Write original prose. Use the sources as research, not as text to paste. Reproduce commands, code, and config exactly; never paraphrase those.

## Files

- Chapter file: `book/part-NN/chNN-slug.md` (the exact path is in your brief). It begins with a single H1: `# Chapter N: Title`. Use H2 and H3 below it. No other H1.
- Immediately after the H1, a blank line and then the prerequisites callout: `> **Prerequisites:** Chapters 2 and 3.` or `> **Prerequisites:** None.`
- Solutions file: `solutions/chNN.md`, H1 `# Chapter N Solutions`, then `## Exercise Solutions` and `## Quiz Answers`. Quiz answers are collected into an appendix automatically.
- Refer to other chapters as "Chapter N" and to appendices as "Appendix X". Only use numbers that exist in the manifest.

## Chapter structure

Required H2 sections, in order (the brief lists the exact set for each chapter):

1. `## What You'll Learn`: 4 to 7 bullet learning objectives.
2. Concept sections (several H2s, your own headings): deep explanation with examples, tables, and diagrams.
3. `## Hands-On: <title>`: a guided exercise with exact commands or steps and the expected result.
4. `## Quick Reference`: tables of the commands, options, settings, or terms the chapter introduced, with defaults.
5. `## Under the Hood`: how it works internally, as far as the sources explain it. Short excerpts (25 lines or fewer) when the sources include code.
6. `## Pitfalls and Troubleshooting`: common mistakes, symptoms, and fixes.
7. `## Summary`: one or two paragraphs, then the key takeaways.
8. `## Exercises`: 3 to 6 numbered exercises.
9. `## Quiz`: 5 to 8 questions, multiple choice or short answer. No answers in the chapter.

The `light` template (for beginner chapters) drops Quick Reference, Under the Hood, and Pitfalls.

Optionally end with `## Further Reading` when the sources mention external links. Only list URLs that appear in the sources.

## Diagrams

- At least {{targets.min_diagrams}} diagrams per chapter, written inline as fenced `mermaid` blocks. The build renders them to images.
- Use `flowchart`, `sequenceDiagram`, `stateDiagram-v2`, or `classDiagram`. Quote labels that contain punctuation: `A["run the command"]`. No HTML in labels.
- Validate before you finish: `python3 -m forge{{book_flag}} diagrams --chapter N`.

## Images

- Only use images listed in your brief. They come from the author's sources, and paths are relative to the book folder (`sources/...`).
- Every image gets a caption (the alt text) that says what the reader should notice.
- Don't describe details in an image that its source doesn't explain; you can't verify them.
- An image doesn't count toward the diagram minimum; that is about Mermaid diagrams.

## Callouts

Pandoc blockquotes with a bold label:

- `> **Note:** ...`
- `> **Tip:** ...`
- `> **Warning:** ...`

## Formatting

- Every code block has a language tag (`bash`, `json`, `yaml`, `python`, `csharp`, `text`, ...).
- Prefer tables for reference material.
- Length: {{targets.words_min}} to {{targets.words_max}} words per chapter. Depth beats padding: cover every option and edge case in the sources, then stop.

## Companion project

{{companion.description}}

## One topic, one home

Each topic is taught in full in one chapter (see the manifest summaries). Other chapters summarize it in a sentence or two and cross-reference it.
