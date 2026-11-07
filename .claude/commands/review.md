---
description: Fact-check chapters against their sources and write grounding reports
argument-hint: "[chapter numbers, default all] [--book folder]"
---
Parse "$ARGUMENTS" for chapter numbers or ranges (default: every chapter that exists) and `--book <folder>` (default `.`).

1. Run `python3 -m forge --book <book> briefs` so the manifest is current.
2. Launch one `grounding-reviewer` agent per chapter, in parallel batches of at most 6. Each prompt: the book folder and the chapter number.
3. Collect the verdicts into a table (chapter, verdict, high, medium, low) and list the paths of the reports in `<book>/build/reports/`.
4. Suggest `/edit` to apply the fixes, or `/write N` for any chapter with many high-severity issues.
