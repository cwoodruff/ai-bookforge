"""Collect the places where writers said the sources fall short, so the author can fill them (/interview).

A gap is a `> **Note:**` callout that says the sources don't cover something. The style guide asks
writers to start those notes with "The source material doesn't cover", but writers paraphrase, so
any Note that mentions the sources together with a negation counts.
"""
from __future__ import annotations

import re

from .config import Book

MENTIONS_SOURCES = re.compile(r"\bsources?\b|source material", re.I)
NEGATION = re.compile(r"do(?:es)?n['’]t|do(?:es)? not|\bnot (?:cover|say|state|mention|specify|explain|show|give|list)|\bsilent\b|\bno source\b", re.I)


def blockquotes(text: str):
    """Yield (line number, joined text) for each blockquote outside code blocks."""
    lines = text.splitlines()
    in_code, start, buf = False, None, []
    for i, line in enumerate(lines + [""], start=1):
        if line.startswith("```"):
            in_code = not in_code
        if not in_code and line.startswith(">"):
            if start is None:
                start = i
            buf.append(line.lstrip(">").strip())
        elif start is not None:
            yield start, " ".join(b for b in buf if b)
            start, buf = None, []


def find(text: str) -> list[tuple[int, str]]:
    out = []
    for line, quote in blockquotes(text):
        if quote.startswith("**Note:**") and MENTIONS_SOURCES.search(quote) and NEGATION.search(quote):
            out.append((line, quote.removeprefix("**Note:**").strip()))
    return out


def collect(book: Book, chapter: int | None = None) -> dict:
    """{label: [(path, line, text), ...]} for chapters (and agent-written appendices) that exist."""
    targets = [(f"Chapter {c.number}: {c.title}", c.path) for c in book.chapters if chapter in (None, c.number)]
    if chapter is None:
        targets += [(f"Appendix {a.id}: {a.title}", a.path) for a in book.appendices if not a.generate]
    result = {}
    for label, rel in targets:
        p = book.path(rel)
        if p.exists():
            found = find(p.read_text(encoding="utf-8"))
            if found:
                result[label] = [(rel, line, text) for line, text in found]
    return result


def run(book: Book, chapter: int | None = None) -> dict:
    gaps = collect(book, chapter)
    total = sum(len(v) for v in gaps.values())
    lines = [f"# Source Gaps: {book.data['title']}", "",
             f"{total} place(s) where a writer said the sources fall short. Fill them with `/interview` "
             "(or by adding to `sources/`), then rewrite the chapter with `/write N`.", ""]
    for label, items in gaps.items():
        lines += [f"## {label}", ""]
        lines += [f"{n}. {text} (`{rel}`, line {line})" for n, (rel, line, text) in enumerate(items, 1)]
        lines.append("")
    out = book.path("build/gaps.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    return gaps
