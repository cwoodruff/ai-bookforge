"""Stage 3: render the manifest, style guide, and one writing brief per chapter and appendix.

Templates live in the profile folder and use {{dotted.name}} placeholders. An unknown
placeholder is an error, so a template can never silently ship a blank.
"""
from __future__ import annotations

import re

from .config import Book, Chapter, Appendix, TOOL_ROOT
from .ingest import source_images

PLACEHOLDER = re.compile(r"\{\{\s*([\w.]+)\s*\}\}")


def render(template: str, values: dict, name: str) -> str:
    def sub(m):
        key = m.group(1)
        if key not in values:
            raise KeyError(f"{name}: unknown placeholder {{{{{key}}}}}")
        return str(values[key])

    return PLACEHOLDER.sub(sub, template)


def bullets(items, empty="None.") -> str:
    items = list(items)
    return "\n".join(f"- {i}" for i in items) if items else empty


def book_flag(book: Book) -> str:
    """The --book argument agents must pass when the book is not at the repo root."""
    if book.root == TOOL_ROOT:
        return ""
    try:
        return f" --book {book.root.relative_to(TOOL_ROOT)}"
    except ValueError:
        return f" --book {book.root}"


def chapter_ref(book: Book, n: int) -> str:
    return f"Chapter {n}: {book.chapter(n).title}"


def book_values(book: Book) -> dict:
    d = book.data
    voice = d.get("voice") or {}
    terms = voice.get("terminology") or {}
    words = book.targets["words_per_chapter"]
    cp = d.get("companion_project") or {}
    return {
        "book.title": d["title"],
        "book.subtitle": d.get("subtitle", ""),
        "book.author": d["author"],
        "book.lang": d.get("lang", "en-US"),
        "book.description": (d.get("description") or "").strip(),
        "book.chapter_count": len(book.chapters),
        "voice.audience": voice.get("audience", "readers new to the subject"),
        "voice.person": {"second": "Second person (\"you\")", "first": "First person (\"I\" / \"we\")", "third": "Third person"}.get(
            voice.get("person", "second"), voice.get("person", "second")
        ),
        "voice.tone": voice.get("tone", "friendly and precise"),
        "voice.rules": bullets(voice.get("rules") or [], "No extra rules."),
        "voice.terminology": bullets([f"{k}: {v}" for k, v in terms.items()], "No fixed terminology."),
        "targets.words_min": words[0],
        "targets.words_max": words[1],
        "targets.min_diagrams": book.targets["min_diagrams"],
        "companion.name": cp.get("name", ""),
        "companion.path": cp.get("path", ""),
        "companion.description": (cp.get("description") or "No companion project. Hands-On sections use small, self-contained examples.").strip(),
        "paths.style_guide": "build/briefs/style-guide.md",
        "paths.manifest": "build/manifest.md",
        "paths.inventory": "build/inventory.md",
        "book_flag": book_flag(book),
    }


def manifest(book: Book) -> str:
    lines = [f"# Chapter Manifest: {book.data['title']}", "",
             "Chapters are numbered continuously across parts. Refer to them as \"Chapter N\" and to appendices as \"Appendix X\".", ""]
    for part in book.parts:
        lines += [f"## Part {part.number}: {part.title}", ""]
        if part.intro:
            lines += [part.intro, ""]
        lines += ["| # | Title | File | Sources | Summary |", "|---|---|---|---|---|"]
        for ch in part.chapters:
            srcs = ", ".join(f"`{s}`" for s in ch.sources) or "none"
            lines.append(f"| {ch.number} | {ch.title} | `{ch.path}` | {srcs} | {ch.summary or ''} |")
        lines.append("")
    if book.appendices:
        lines += ["## Appendices", "", "| ID | Title | File | How it is made |", "|---|---|---|---|"]
        for a in book.appendices:
            how = f"generated ({a.generate})" if a.generate else "written from a brief"
            lines.append(f"| {a.id} | {a.title} | `{a.path}` | {how} |")
        lines.append("")
    return "\n".join(lines)


def prereq_text(nums: list[int]) -> str:
    """[] -> 'None.', [2] -> 'Chapter 2.', [1, 2, 4] -> 'Chapters 1, 2, and 4.'"""
    nums = sorted(nums)
    if not nums:
        return "None."
    if len(nums) == 1:
        return f"Chapter {nums[0]}."
    if len(nums) == 2:
        return f"Chapters {nums[0]} and {nums[1]}."
    return "Chapters " + ", ".join(map(str, nums[:-1])) + f", and {nums[-1]}."


def chapter_images(book: Book, sids: list[str]) -> list[dict]:
    seen, out = set(), []
    for sid in sids:
        p = book.path(book.source_path(sid))
        if not p.exists():
            continue
        for img in source_images(book, sid, p.read_text(encoding="utf-8")):
            if img["exists"] and img["path"] not in seen:
                seen.add(img["path"])
                out.append({**img, "source": sid})
    return out


def image_list(book: Book, sids: list[str]) -> str:
    imgs = chapter_images(book, sids)
    return bullets((f"`{i['path']}` (from `{i['source']}`): {i['alt'] or 'no alt text; describe it from the surrounding source text'}"
                    for i in imgs), "None in the assigned sources. Use Mermaid diagrams only.")


def chapter_values(book: Book, ch: Chapter) -> dict:
    sections = book.rules["sections"][ch.template]
    prev = book.chapter(ch.number - 1) if ch.number > 1 else None
    nxt = book.chapter(ch.number + 1) if ch.number < len(book.chapters) else None
    prereq_line = prereq_text(ch.prereqs)
    return {
        "chapter.number": ch.number,
        "chapter.number2": f"{ch.number:02d}",
        "chapter.title": ch.title,
        "chapter.summary": ch.summary or "(No summary in book.yaml. Infer the scope from the title and the assigned sources.)",
        "chapter.path": ch.path,
        "chapter.solution_path": ch.solution_path,
        "chapter.template": ch.template,
        "chapter.sections": "\n".join(f"{i}. `## {s}`" for i, s in enumerate(sections, 1)),
        "chapter.prereqs": prereq_line,
        "chapter.sources": bullets(f"`{book.source_path(s)}`" for s in ch.sources),
        "chapter.images": image_list(book, ch.sources),
        "chapter.previous": chapter_ref(book, prev.number) if prev else "None (this is the first chapter).",
        "chapter.next": chapter_ref(book, nxt.number) if nxt else "None (this is the last chapter).",
        "part.number": ch.part.number,
        "part.title": ch.part.title,
    }


def appendix_values(book: Book, a: Appendix) -> dict:
    return {
        "appendix.id": a.id,
        "appendix.title": a.title,
        "appendix.path": a.path,
        "appendix.brief": a.brief or "Write a useful reference appendix that fits the title.",
        "appendix.images": image_list(book, a.sources),
        "appendix.sources": bullets((f"`{book.source_path(s)}`" for s in a.sources), "Use any source in the inventory, plus the written chapters."),
    }


def run(book: Book) -> list[str]:
    out = book.path("build/briefs")
    out.mkdir(parents=True, exist_ok=True)
    base = book_values(book)
    written = []

    def emit(rel: str, template_name: str, values: dict):
        tpl = (book.profile_dir / template_name).read_text(encoding="utf-8")
        book.path(rel).write_text(render(tpl, values, template_name), encoding="utf-8")
        written.append(rel)

    book.path("build/manifest.md").write_text(manifest(book), encoding="utf-8")
    written.append("build/manifest.md")
    emit("build/briefs/style-guide.md", "style-guide.md", base)
    for ch in book.chapters:
        emit(ch.brief_path, "writer-brief.md", {**base, **chapter_values(book, ch)})
    for a in book.appendices:
        if not a.generate:
            emit(a.brief_path, "appendix-brief.md", {**base, **appendix_values(book, a)})
    return written
