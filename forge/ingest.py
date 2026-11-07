"""Stage 1: inventory the user's markdown sources so the outliner can plan without reading everything."""
from __future__ import annotations

import hashlib
import json
import re

from .config import Book

FENCE = re.compile(r"^```.*?^```", re.S | re.M)


def strip_code(text: str) -> str:
    return FENCE.sub("", text)


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w[\w'-]*\b", strip_code(text)))


def describe(book: Book, sid: str) -> dict:
    path = book.path(book.source_path(sid))
    text = path.read_text(encoding="utf-8")
    body = strip_code(text)
    h1 = re.search(r"^# (.+)$", body, re.M)
    headings = re.findall(r"^(#{2,3}) (.+)$", body, re.M)
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip() and not p.lstrip().startswith(("#", "|", ">", "-", "*", "!"))]
    lead = " ".join(paras[0].split()[:60]) if paras else ""
    return {
        "id": sid,
        "path": book.source_path(sid),
        "title": h1.group(1).strip() if h1 else sid.split("/")[-1].replace("-", " ").title(),
        "words": word_count(text),
        "sha1": hashlib.sha1(text.encode("utf-8")).hexdigest(),
        "headings": [("  " if len(h) == 3 else "") + t.strip() for h, t in headings],
        "lead": lead,
    }


def run(book: Book) -> list[dict]:
    items = [describe(book, sid) for sid in book.source_ids()]
    out = book.path("build")
    out.mkdir(exist_ok=True)
    (out / "inventory.json").write_text(json.dumps(items, indent=2), encoding="utf-8")
    lines = [
        f"# Source Inventory: {book.data['title']}",
        "",
        f"{len(items)} source files, {sum(i['words'] for i in items):,} words total.",
        "Each entry lists the source id (use it in book.yaml `sources:`), title, size, outline, and opening text.",
        "",
    ]
    for i in items:
        lines += [f"## `{i['id']}`: {i['title']}", "", f"- Path: `{i['path']}`", f"- Words: {i['words']:,}"]
        if i["lead"]:
            lines.append(f"- Opening: {i['lead']}")
        if i["headings"]:
            lines.append("- Outline:")
            lines += [f"  - {h.strip()}" if not h.startswith("  ") else f"    - {h.strip()}" for h in i["headings"]]
        lines.append("")
    (out / "inventory.md").write_text("\n".join(lines), encoding="utf-8")
    return items
