---
description: Propose the book's parts, chapters, and source map in book.yaml from the files in sources/
argument-hint: "[book folder] [notes for the outliner]"
---
Book folder: the first argument if it is a folder containing book.yaml, otherwise the repo root (`.`). Any remaining text in "$ARGUMENTS" is guidance from the author for the outliner.

1. Run `python3 -m forge --book <book> ingest` and report the source count and total words.
2. If book.yaml already has chapters, ask the author whether to replace the outline or revise it, and pass the answer to the outliner.
3. Launch the `book-outliner` agent with the book folder, the author's guidance, and the instruction to replace `parts:` in `<book>/book.yaml`.
4. When it finishes, run `python3 -m forge --book <book> check --coverage`.
5. Show the author the outline table and the outliner's open questions. Stop here: the author approves or edits book.yaml before `/write-all`. Don't start writing.
