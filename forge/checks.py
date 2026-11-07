"""Stage 5: deterministic checks. Errors fail the run; warnings are printed and ignored."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .config import Book, Chapter
from .ingest import strip_code, word_count

CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def err(self, where: str, msg: str):
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str):
        self.warnings.append(f"{where}: {msg}")

    @property
    def ok(self) -> bool:
        return not self.errors


def norm(s: str) -> str:
    return s.replace("’", "'").replace("‘", "'").strip().lower()


def check_coverage(book: Book, r: Report) -> None:
    inventory = set(book.source_ids())
    excluded = set(book.data.get("exclude_sources") or [])
    used = set()
    for ch in book.chapters:
        if not ch.sources:
            r.warn(f"ch{ch.number:02d}", "no sources assigned (the chapter will not be grounded in your material)")
        for s in ch.sources:
            used.add(s)
            if s not in inventory:
                r.err(f"ch{ch.number:02d}", f"source '{s}' not found at {book.source_path(s)}")
    for a in book.appendices:
        for s in a.sources:
            used.add(s)
            if s not in inventory:
                r.err(f"appendix {a.id}", f"source '{s}' not found")
    if book.chapters:
        for s in sorted(inventory - used - excluded):
            r.err("coverage", f"source '{s}' is not assigned to any chapter (assign it or list it under exclude_sources)")
    for s in sorted(excluded - inventory):
        r.warn("coverage", f"exclude_sources lists '{s}', which does not exist")


def check_chapter(book: Book, ch: Chapter, r: Report) -> None:
    where = f"ch{ch.number:02d}"
    path = book.path(ch.path)
    if not path.exists():
        r.err(where, f"missing {ch.path}")
        return
    text = path.read_text(encoding="utf-8")
    rules = book.rules
    body = strip_code(text)
    first = text.splitlines()[0] if text else ""
    expected = f"# Chapter {ch.number}: {ch.title}"
    if not first.startswith(f"# Chapter {ch.number}:"):
        r.err(where, f"first line must be '{expected}'")
    elif norm(first) != norm(expected):
        r.warn(where, f"title differs from book.yaml ('{first[2:]}' vs '{expected[2:]}')")
    if len(re.findall(r"^# ", body, re.M)) > 1:
        r.err(where, "only the chapter title may be an H1")
    if rules.get("prerequisites", True) and "> **Prerequisites:**" not in "\n".join(text.splitlines()[:6]):
        r.err(where, "missing '> **Prerequisites:**' callout right after the title")
    headings = [norm(h) for h in re.findall(r"^## (.+)$", body, re.M)]
    last = -1
    for sec in rules["sections"][ch.template]:
        idx = next((i for i, h in enumerate(headings) if h.startswith(norm(sec))), None)
        if idx is None:
            r.err(where, f"missing required section '## {sec}'")
        elif idx < last:
            r.err(where, f"section '## {sec}' is out of order")
        else:
            last = idx
    diagrams = text.count("```mermaid")
    if diagrams < book.targets["min_diagrams"]:
        r.err(where, f"{diagrams} mermaid diagram(s); at least {book.targets['min_diagrams']} required")
    lo, hi = book.targets["words_per_chapter"]
    words = word_count(text)
    if not lo <= words <= hi:
        r.warn(where, f"{words} words; target is {lo}-{hi}")
    if CONTROL.search(text):
        r.err(where, "contains an invalid XML control character")
    for fence in re.findall(r"^```(\S*)", text, re.M)[::2]:
        if not fence:
            r.warn(where, "a code block has no language tag")
            break
    if rules.get("solutions", True):
        sol = book.path(ch.solution_path)
        if not sol.exists():
            r.err(where, f"missing {ch.solution_path}")
        else:
            st = sol.read_text(encoding="utf-8")
            if not st.startswith(f"# Chapter {ch.number} Solutions"):
                r.err(where, f"{ch.solution_path} must start with '# Chapter {ch.number} Solutions'")
            if "Quiz" in " ".join(rules["sections"][ch.template]) and "## Quiz Answers" not in st:
                r.err(where, f"{ch.solution_path} has no '## Quiz Answers' section")
    check_refs(book, where, body, r)


def check_refs(book: Book, where: str, body: str, r: Report) -> None:
    max_ch = len(book.chapters)
    for n in sorted({int(n) for n in re.findall(r"\bChapters? (\d+)", body)}):
        if not 1 <= n <= max_ch:
            r.err(where, f"refers to Chapter {n}, but the book has {max_ch} chapters")
    ids = {a.id for a in book.appendices}
    for a in sorted(set(re.findall(r"\bAppendix ([A-Z])\b", body))):
        if a not in ids:
            r.err(where, f"refers to Appendix {a}, which book.yaml does not define")


def check_appendices(book: Book, r: Report) -> None:
    for a in book.appendices:
        if a.generate:
            if a.generate not in ("quiz", "glossary"):
                r.err(f"appendix {a.id}", f"unknown generator '{a.generate}'")
            continue
        p = book.path(a.path)
        if not p.exists():
            r.err(f"appendix {a.id}", f"missing {a.path}")
            continue
        text = p.read_text(encoding="utf-8")
        if not text.startswith(f"# Appendix {a.id}:"):
            r.err(f"appendix {a.id}", f"first line must be '# Appendix {a.id}: {a.title}'")
        check_refs(book, f"appendix {a.id}", strip_code(text), r)


def check_strays(book: Book, r: Report) -> None:
    expected = {ch.path for ch in book.chapters} | {a.path for a in book.appendices}
    for p in sorted(book.path("book").glob("**/*.md")) if book.path("book").is_dir() else []:
        rel = str(p.relative_to(book.root))
        if rel.startswith("book/front/"):
            continue
        if rel not in expected:
            r.warn("layout", f"{rel} is not in book.yaml and will not be built")


def run(book: Book, chapter: int | None = None, coverage_only: bool = False) -> Report:
    r = Report()
    if not book.chapters:
        r.err("book.yaml", "no parts or chapters yet (run the outliner first)")
    if chapter is None:
        check_coverage(book, r)
    if coverage_only:
        return r
    targets = [book.chapter(chapter)] if chapter else book.chapters
    for ch in targets:
        check_chapter(book, ch, r)
    if not chapter:
        check_appendices(book, r)
        check_strays(book, r)
    return r
