# Writer Brief: Appendix {{appendix.id}}: {{appendix.title}}

You are writing a reference appendix for **{{book.title}}** by {{book.author}}.

## Read first

1. `{{paths.style_guide}}` (voice, grounding, and formatting rules apply; the chapter section structure does not)
2. `{{paths.manifest}}`
3. The sources and chapters listed below

## What to write

{{appendix.brief}}

## Sources

{{appendix.sources}}

## Images you may use

{{appendix.images}}

## You own

- `{{appendix.path}}`, which must begin with `# Appendix {{appendix.id}}: {{appendix.title}}` and use H2/H3 below it.

Don't edit any other file.

## Rules

- Reference format: tables and short entries, organized for lookup. No exercises or quiz.
- Every entry must be traceable to a source or a chapter. Point readers to the chapter that teaches each item ("see Chapter 4").
- Finish by running `python3 -m forge{{book_flag}} check` and fixing any error that names Appendix {{appendix.id}}.
