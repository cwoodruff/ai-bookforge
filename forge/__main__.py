"""AI Book Forge command line. Run from the repo root: python3 -m forge <command> [--book DIR]."""
from __future__ import annotations

import argparse
import re
import shutil
import sys
import urllib.request

from . import briefs, build, checks, gaps, ingest, state
from .config import Book, ConfigError, TOOL_ROOT
from .ingest import word_count


def cmd_init(args):
    root = TOOL_ROOT if args.book == "." else __import__("pathlib").Path(args.book).resolve()
    target = root / "book.yaml"
    if target.exists():
        print(f"{target} already exists; leaving it alone")
    else:
        root.mkdir(parents=True, exist_ok=True)
        shutil.copy(TOOL_ROOT / "book.yaml.example", target)
        print(f"created {target}")
    (root / "sources").mkdir(exist_ok=True)
    print(f"put your markdown files in {root / 'sources'}/ and fill in book.yaml")
    return 0


def cmd_ingest(args):
    book = Book(args.book)
    items = ingest.run(book)
    print(f"inventoried {len(items)} sources ({sum(i['words'] for i in items):,} words) -> build/inventory.md")
    return 0 if items else 1


def cmd_briefs(args):
    book = Book(args.book)
    ingest.run(book)
    written = briefs.run(book)
    print(f"rendered {len(written)} files into build/ (manifest, style guide, {len(book.chapters)} chapter briefs)")
    return 0


def print_report(r: checks.Report) -> int:
    for w in r.warnings:
        print(f"warning  {w}")
    for e in r.errors:
        print(f"ERROR    {e}")
    print(f"{len(r.errors)} error(s), {len(r.warnings)} warning(s)")
    return 0 if r.ok else 1


def cmd_check(args):
    book = Book(args.book)
    return print_report(checks.run(book, chapter=args.chapter, coverage_only=args.coverage))


def cmd_status(args):
    book = Book(args.book)
    print(f"{book.data['title']}: {len(book.parts)} parts, {len(book.chapters)} chapters, {len(book.source_ids())} sources\n")
    found = gaps.collect(book)
    saved = state.load(book)
    unstamped = edited = 0
    print(f"{'#':>3}  {'state':<9} {'words':>6}  {'issues':>6}  {'gaps':>4}  {'review':<6}  title")
    for ch in book.chapters:
        p = book.path(ch.path)
        r = checks.Report()
        checks.check_chapter(book, ch, r)
        words = word_count(p.read_text(encoding="utf-8")) if p.exists() else 0
        st = state.check(book, ch, saved)
        if not p.exists():
            status = "missing"
        elif not r.ok:
            status = "failing"
        elif st["stale"]:
            status = "stale"
        else:
            status = "ok"
        unstamped += p.exists() and not st["stamped"]
        edited += st["edited"]
        review = "yes" if book.path(f"build/reports/ch{ch.number:02d}-grounding.md").exists() else "-"
        ngaps = len(found.get(f"Chapter {ch.number}: {ch.title}", []))
        print(f"{ch.number:>3}  {status:<9} {words:>6}  {len(r.errors):>6}  {ngaps:>4}  {review:<6}  {ch.title}")
    for a in book.appendices:
        astate = "generated" if a.generate else ("ok" if book.path(a.path).exists() else "missing")
        print(f"  {a.id}  {astate:<9} {'':>6}  {'':>6}  {'':>4}  {'':<6}  Appendix {a.id}: {a.title}")
    stale = state.stale(book)
    if stale:
        print("\nstale (sources changed since the chapter was written; run /revise):")
        for n, r in stale.items():
            print(f"  Chapter {n}: {', '.join(r['stale'])}")
    if edited:
        print(f"\n{edited} chapter(s) edited since they were last stamped; /write would overwrite those edits, /revise keeps them")
    if unstamped:
        print(f"\n{unstamped} chapter(s) have never been stamped, so staleness can't be tracked: python3 -m forge stamp --all")
    return 0


def cmd_build(args):
    book = Book(args.book)
    if not args.skip_check:
        r = checks.run(book)
        if not r.ok:
            print_report(r)
            print("fix the errors above or pass --skip-check")
            return 1
    build.run(book, args.formats or list(build.FORMATS), args.gaps)
    return 0


def cmd_stamp(args):
    book = Book(args.book)
    if not args.all and not args.chapter:
        print("pass --chapter N (repeatable) or --all")
        return 2
    done = state.stamp(book, None if args.all else args.chapter)
    print(f"stamped chapter(s) {', '.join(map(str, done)) or 'none'} -> {state.STATE_FILE}")
    return 0


def cmd_stale(args):
    book = Book(args.book)
    found = state.stale(book)
    for n, r in found.items():
        line = f"Chapter {n}: {', '.join(r['stale'])}"
        if args.diff:
            out = state.write_changes(book, book.chapter(n))
            line += f" -> {out.relative_to(book.root)}"
        print(line)
    print(f"{len(found)} stale chapter(s)")
    return 0


def cmd_gaps(args):
    book = Book(args.book)
    found = gaps.run(book, args.chapter)
    for label, items in found.items():
        print(label)
        for rel, line, text in items:
            print(f"  {rel}:{line}: {text[:110]}{'...' if len(text) > 110 else ''}")
    print(f"{sum(len(v) for v in found.values())} gap(s) -> build/gaps.md")
    return 0


def cmd_diagrams(args):
    book = Book(args.book)
    if args.chapter:
        files = [book.chapter(args.chapter).path]
    else:
        files = [ch.path for ch in book.chapters] + [a.path for a in book.appendices if not a.generate]
    files = [f for f in files if book.path(f).exists()]
    failures = build.validate_diagrams(book, files)
    for f in failures:
        print(f"ERROR    {f}")
    print(f"{len(failures)} diagram failure(s) in {len(files)} file(s)")
    return 1 if failures else 0


def cmd_cover(args):
    book = Book(args.book)
    p = build.cover(book, required=True)
    print(f"cover: {p.relative_to(book.root)}")
    return 0


def cmd_links(args):
    book = Book(args.book)
    urls = set()
    for p in book.path("book").glob("**/*.md"):
        urls |= {u.rstrip(".,;:") for u in re.findall(r"https?://[^\s)>\"`\]]+", p.read_text(encoding="utf-8"))}
    bad = 0
    for u in sorted(urls):
        try:
            req = urllib.request.Request(u, method="HEAD", headers={"User-Agent": "ai-bookforge-linkcheck"})
            code = urllib.request.urlopen(req, timeout=15).status
        except urllib.error.HTTPError as e:
            code = e.code
        except Exception:
            code = 0
        if code == 0 or code >= 400:
            bad += 1
            print(f"BROKEN {code} {u}")
    print(f"checked {len(urls)} links, {bad} broken")
    return 1 if bad else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="forge", description="AI Book Forge: build AI-written books from markdown sources")
    ap.add_argument("--book", default=".", help="folder that holds book.yaml (default: current folder)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init", help="create book.yaml and sources/ from the example")
    sub.add_parser("ingest", help="inventory sources/ into build/inventory.md")
    sub.add_parser("briefs", help="render the manifest, style guide, and writing briefs")
    c = sub.add_parser("check", help="structure, coverage, and cross-reference checks")
    c.add_argument("--chapter", type=int)
    c.add_argument("--coverage", action="store_true", help="only check the source-to-chapter map")
    sub.add_parser("status", help="per-chapter progress table")
    b = sub.add_parser("build", help="build epub, html, and/or pdf into dist/")
    b.add_argument("formats", nargs="*", help="epub html pdf (default: all)")
    b.add_argument("--skip-check", action="store_true")
    b.add_argument("--gaps", choices=build.GAP_MODES, default="keep",
                   help="source gap notes: keep (drafts), strip (leave them out), fail (refuse to build)")
    st = sub.add_parser("stamp", help="record the sources a chapter was written from (after write, revise, edit)")
    st.add_argument("--chapter", type=int, action="append")
    st.add_argument("--all", action="store_true")
    sl = sub.add_parser("stale", help="list chapters whose sources changed since they were written")
    sl.add_argument("--diff", action="store_true", help="write build/changes/chNN.md for each stale chapter")
    g = sub.add_parser("gaps", help="list the places writers said the sources fall short (build/gaps.md)")
    g.add_argument("--chapter", type=int)
    d = sub.add_parser("diagrams", help="render every mermaid diagram to catch syntax errors early")
    d.add_argument("--chapter", type=int)
    sub.add_parser("cover", help="render the cover image")
    sub.add_parser("links", help="check external links in the manuscript")
    # allow --book after the subcommand too
    for p in sub.choices.values():
        p.add_argument("--book", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    try:
        return globals()[f"cmd_{args.cmd}"](args)
    except (ConfigError, build.BuildError, KeyError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
