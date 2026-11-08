"""Which source versions each chapter was written from, so chapters go stale when their sources change.

`.forge/state.json` (committed with the book) records, per chapter, the hash of every assigned source
at the moment the chapter was last written, revised, or edited, plus the chapter's own hash.
A chapter is stale when a source it was written from changed, or a source was added to or removed
from its list. Snapshots of each source version are cached in build/snapshots/ so a revision can be
handed an exact diff of what changed.
"""
from __future__ import annotations

import difflib
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .config import Book, Chapter

STATE_FILE = ".forge/state.json"


def sha1(path: Path) -> str | None:
    return hashlib.sha1(path.read_bytes()).hexdigest() if path.is_file() else None


def load(book: Book) -> dict:
    p = book.path(STATE_FILE)
    if not p.exists():
        return {"chapters": {}}
    return json.loads(p.read_text(encoding="utf-8"))


def save(book: Book, state: dict) -> None:
    p = book.path(STATE_FILE)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def key(ch: Chapter) -> str:
    return f"ch{ch.number:02d}"


def snapshot(book: Book, sid: str, digest: str) -> None:
    snap = book.path(f"build/snapshots/{digest}.md")
    if not snap.exists():
        snap.parent.mkdir(parents=True, exist_ok=True)
        snap.write_bytes(book.path(book.source_path(sid)).read_bytes())


def stamp(book: Book, numbers: list[int] | None = None) -> list[int]:
    """Record the current sources of each chapter that exists. Returns the chapter numbers stamped."""
    state = load(book)
    done = []
    for ch in book.chapters:
        if numbers is not None and ch.number not in numbers:
            continue
        chapter_hash = sha1(book.path(ch.path))
        if not chapter_hash:
            continue
        sources = {}
        for sid in ch.sources:
            digest = sha1(book.path(book.source_path(sid)))
            if digest:
                sources[sid] = digest
                snapshot(book, sid, digest)
        state["chapters"][key(ch)] = {
            "title": ch.title,
            "sources": sources,
            "chapter_sha1": chapter_hash,
            "stamped": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        done.append(ch.number)
    save(book, state)
    return done


def check(book: Book, ch: Chapter, state: dict | None = None) -> dict:
    """{'stamped': bool, 'stale': [reasons], 'changed': [...], 'added': [...], 'removed': [...], 'edited': bool}"""
    state = state or load(book)
    entry = state["chapters"].get(key(ch))
    result = {"stamped": entry is not None, "stale": [], "changed": [], "added": [], "removed": [], "edited": False}
    if not entry or not book.path(ch.path).exists():
        return result
    old = entry["sources"]
    for sid in ch.sources:
        now = sha1(book.path(book.source_path(sid)))
        if sid not in old:
            result["added"].append(sid)
            result["stale"].append(f"new source {sid}")
        elif now and now != old[sid]:
            result["changed"].append(sid)
            result["stale"].append(f"{sid} changed")
    for sid in old:
        if sid not in ch.sources:
            result["removed"].append(sid)
            result["stale"].append(f"{sid} no longer assigned")
    result["edited"] = sha1(book.path(ch.path)) != entry["chapter_sha1"]
    return result


def stale(book: Book) -> dict[int, dict]:
    state = load(book)
    out = {}
    for ch in book.chapters:
        r = check(book, ch, state)
        if r["stale"]:
            out[ch.number] = r
    return out


def write_changes(book: Book, ch: Chapter) -> Path | None:
    """Write build/changes/chNN.md describing exactly what changed in the chapter's sources."""
    state = load(book)
    r = check(book, ch, state)
    if not r["stale"]:
        return None
    old = state["chapters"][key(ch)]["sources"]
    lines = [f"# Source Changes: Chapter {ch.number}: {ch.title}", "",
             f"Chapter {ch.number} was last written from older versions of its sources. Update it to match "
             "the sources as they are now. Change only what these differences require.", ""]
    for sid in r["changed"]:
        path = book.source_path(sid)
        snap = book.path(f"build/snapshots/{old[sid]}.md")
        lines += [f"## Changed: `{path}`", ""]
        if snap.exists():
            diff = difflib.unified_diff(snap.read_text(encoding="utf-8").splitlines(),
                                        book.path(path).read_text(encoding="utf-8").splitlines(),
                                        fromfile=f"{path} (when last written)", tofile=f"{path} (now)", lineterm="")
            lines += ["```diff", *diff, "```", ""]
        else:
            lines += ["The previous version isn't cached on this machine. Reread the whole source and "
                      "compare it with what the chapter says.", ""]
    for sid in r["added"]:
        lines += [f"## New source: `{book.source_path(sid)}`", "",
                  "Read it in full and work its material into the chapter. If it answers questions the chapter "
                  "flagged with `> **Note:** The source material doesn't cover ...`, replace those notes with the answer.", ""]
    for sid in r["removed"]:
        lines += [f"## Removed source: `{book.source_path(sid)}`", "",
                  "This source is no longer assigned to the chapter. Remove material that came only from it, or "
                  "cut it down to a cross-reference to the chapter that now owns it.", ""]
    out = book.path(f"build/changes/ch{ch.number:02d}.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    return out
