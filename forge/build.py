"""Stage 7: generated files (metadata, part intros, appendices, cover) and the Pandoc/Chrome build."""
from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import yaml

from . import gaps
from .config import Book, TOOL_ROOT

FORMATS = ("epub", "html", "pdf")


class BuildError(Exception):
    pass


# ---------- tools ----------
def find_chrome() -> str | None:
    env = os.environ.get("CHROME")
    if env:
        return env
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        p = shutil.which(name)
        if p:
            return p
    for p in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Chromium.app/Contents/MacOS/Chromium"):
        if Path(p).exists():
            return p
    return None


def chrome_args() -> list[str]:
    return ["--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars"]


def puppeteer_config(book: Book) -> Path:
    """mmdc needs Chrome flags that work in containers and CI; write a config unless the user set one."""
    env = os.environ.get("PUPPETEER_CONFIG")
    if env:
        return Path(env)
    cfg = {"args": ["--no-sandbox"]}
    chrome = find_chrome()
    if chrome:
        cfg["executablePath"] = chrome
    p = book.path("build/puppeteer.json")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(cfg), encoding="utf-8")
    return p


# ---------- generated sources ----------
def metadata(book: Book, cover: Path | None) -> Path:
    d = book.data
    meta = {
        "title": d["title"],
        "author": d["author"],
        "lang": d.get("lang", "en-US"),
        "identifier": [{"scheme": "UUID", "text": book.identifier}] if book.identifier.startswith("urn:uuid:") else book.identifier,
        "toc-depth": 1,
        "toc-title": d.get("toc_title", "Contents"),
    }
    for key in ("subtitle", "description", "subject", "publisher", "date"):
        if d.get(key):
            meta[key] = str(d[key]).strip()
    if d.get("license") or d.get("rights"):
        meta["rights"] = d.get("rights") or f"Text © {d['author']}, {d['license']}."
    if cover:
        meta["cover-image"] = str(cover.relative_to(book.root))
    p = book.path("build/gen/metadata.yaml")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(meta, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return p


def part_intro(book: Book, part) -> Path:
    p = book.path(f"build/gen/part-{part.number:02d}.md")
    p.parent.mkdir(parents=True, exist_ok=True)
    body = f"# Part {part.number}: {part.title} {{.unnumbered}}\n\n{part.intro}\n" if part.intro else f"# Part {part.number}: {part.title} {{.unnumbered}}\n"
    p.write_text(body, encoding="utf-8")
    return p


def quiz_appendix(book: Book, app) -> None:
    out = [f"# Appendix {app.id}: {app.title}", "",
           "Answers to the quiz at the end of each chapter. Worked exercise solutions live in the book repository under `solutions/`.", ""]
    for ch in book.chapters:
        sol = book.path(ch.solution_path)
        if not sol.exists():
            continue
        m = re.search(r"^## Quiz Answers\s*\n(.*?)(?=^## |\Z)", sol.read_text(encoding="utf-8"), re.S | re.M)
        if not m:
            continue
        body = re.sub(r"^(#{3,5}) ", lambda h: "#" + h.group(1) + " ", m.group(1).strip(), flags=re.M)
        out += [f"## Chapter {ch.number}: {ch.title}", "", body, ""]
    book.path(app.path).write_text("\n".join(out), encoding="utf-8")


def glossary_appendix(book: Book, app) -> None:
    terms = book.data.get("glossary") or {}
    out = [f"# Appendix {app.id}: {app.title}", ""]
    if not terms:
        out.append("No glossary terms are defined in book.yaml yet.")
    for term in sorted(terms, key=str.lower):
        out += [f"**{term}**", f": {str(terms[term]).strip()}", ""]
    book.path(app.path).write_text("\n".join(out), encoding="utf-8")


def generate(book: Book) -> None:
    book.path("build/gen").mkdir(parents=True, exist_ok=True)
    for app in book.appendices:
        if app.generate == "quiz":
            quiz_appendix(book, app)
        elif app.generate == "glossary":
            glossary_appendix(book, app)


# ---------- cover ----------
def cover(book: Book, required: bool = False) -> Path | None:
    c = book.data.get("cover") or {}
    if c.get("image"):
        p = book.path(c["image"])
        if not p.exists():
            raise BuildError(f"cover.image {c['image']} does not exist")
        return p
    out = book.path("build/cover.png")
    tpl_path = book.path(c["template"]) if c.get("template") else TOOL_ROOT / "templates/cover.html"
    colors = (c.get("colors") or ["#1e1b4b", "#7c3aed"]) + ["#7c3aed"]
    values = {
        "TITLE": html.escape(book.data["title"]),
        "SUBTITLE": html.escape(book.data.get("subtitle", "")),
        "AUTHOR": html.escape(book.data["author"]),
        "TAGLINE": html.escape(c.get("tagline", "")),
        "COLOR1": colors[0],
        "COLOR2": colors[1],
    }
    page = tpl_path.read_text(encoding="utf-8")
    for k, v in values.items():
        page = page.replace("{{" + k + "}}", v)
    src = book.path("build/gen/cover.html")
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text(page, encoding="utf-8")
    # Reuse the last render if nothing changed.
    stamp = book.path("build/gen/cover.stamp")
    if out.exists() and stamp.exists() and stamp.read_text(encoding="utf-8") == page:
        return out
    chrome = find_chrome()
    if not chrome:
        if required:
            raise BuildError("Chrome not found; set CHROME or set cover.image in book.yaml")
        print("note: Chrome not found, building without a cover")
        return None
    subprocess.run([chrome, *chrome_args(), "--window-size=1600,2400", f"--screenshot={out}", src.as_uri()],
                   check=True, capture_output=True, timeout=120)
    stamp.write_text(page, encoding="utf-8")
    return out


# ---------- pandoc ----------
def input_files(book: Book) -> list[str]:
    files = sorted(str(p.relative_to(book.root)) for p in book.path("book/front").glob("*.md")) if book.path("book/front").is_dir() else []
    for part in book.parts:
        files.append(str(part_intro(book, part).relative_to(book.root)))
        files += [ch.path for ch in part.chapters]
    files += [a.path for a in book.appendices]
    missing = [f for f in files if not book.path(f).exists()]
    if missing:
        raise BuildError("missing files (run `python3 -m forge check`):\n  " + "\n  ".join(missing))
    return files


def styles(book: Book, name: str) -> Path:
    local = book.path(f"styles/{name}")
    return local if local.exists() else TOOL_ROOT / "styles" / name


def pandoc(book: Book, args: list[str]) -> None:
    if not shutil.which("pandoc"):
        raise BuildError("pandoc not found (install Pandoc 3.x)")
    env = dict(os.environ, PUPPETEER_CONFIG=str(puppeteer_config(book)))
    proc = subprocess.run(["pandoc", *args], cwd=book.root, env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        raise BuildError(proc.stderr.strip() or "pandoc failed")
    if proc.stderr.strip():
        print(proc.stderr.strip())


GAP_MODES = ("keep", "strip", "fail")


def apply_gap_mode(book: Book, files: list[str], mode: str) -> list[str]:
    """keep: build as written. fail: refuse while gap notes remain. strip: build from copies without them."""
    if mode not in GAP_MODES:
        raise BuildError(f"unknown gaps mode '{mode}' (choose from {', '.join(GAP_MODES)})")
    if mode == "keep":
        return files
    if mode == "fail":
        found = gaps.collect(book)
        if found:
            total = sum(len(v) for v in found.values())
            where = ", ".join(f"{label.split(':')[0]} ({len(v)})" for label, v in found.items())
            raise BuildError(f"{total} source gap note(s) remain: {where}. Fill them (/interview, then /revise), "
                             "or build with --gaps strip to leave them out. Details: python3 -m forge gaps")
        return files
    out, stripped = [], 0
    for rel in files:
        text = book.path(rel).read_text(encoding="utf-8")
        cleaned, n = gaps.strip(text)
        if n:
            dest = book.path(f"build/final/{rel}")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(cleaned, encoding="utf-8")
            rel = str(dest.relative_to(book.root))
            stripped += n
        out.append(rel)
    print(f"left out {stripped} source gap note(s)")
    return out


def run(book: Book, formats: list[str], gap_mode: str = "keep") -> list[Path]:
    for f in formats:
        if f not in FORMATS:
            raise BuildError(f"unknown format '{f}' (choose from {', '.join(FORMATS)})")
    generate(book)
    files = apply_gap_mode(book, input_files(book), gap_mode)
    cov = cover(book)
    meta = metadata(book, cov)
    dist = book.path("dist")
    dist.mkdir(exist_ok=True)
    common = [
        "--from=markdown+smart+pipe_tables+fenced_divs-raw_html",
        "--resource-path=.:book:sources",
        "--toc", "--toc-depth=1",
        f"--metadata-file={meta}",
        f"--lua-filter={TOOL_ROOT / 'scripts/mermaid.lua'}",
    ]
    outputs = []
    for fmt in formats:
        out = dist / f"{book.slug}.{fmt}"
        if fmt == "epub":
            pandoc(book, [*common, "--to=epub3", "--split-level=1", f"--css={styles(book, 'epub.css')}", "-o", str(out), *files])
        elif fmt == "html":
            pandoc(book, [*common, "--to=html5", "--standalone", "--embed-resources", f"--css={styles(book, 'epub.css')}", "-o", str(out), *files])
        elif fmt == "pdf":
            pdf(book, common, files, cov, out)
        outputs.append(out)
        print(f"built {out.relative_to(book.root)}")
    return outputs


def pdf(book: Book, common: list[str], files: list[str], cov: Path | None, out: Path) -> None:
    chrome = find_chrome()
    if not chrome:
        raise BuildError("PDF output needs Chrome or Chromium (set CHROME=/path/to/chrome)")
    before = book.path("build/gen/print-cover.html")
    before.write_text(f'<div class="cover-page"><img src="{cov.relative_to(book.root)}" alt="Cover"></div>\n' if cov else "", encoding="utf-8")
    page = book.path("build/print.html")
    pandoc(book, [*common, "--to=html5", "--standalone", "--embed-resources",
                  f"--css={styles(book, 'epub.css')}", f"--css={styles(book, 'print.css')}",
                  f"--include-before-body={before}", "-o", str(page), *files])
    subprocess.run([chrome, *chrome_args(), "--no-pdf-header-footer", "--virtual-time-budget=10000",
                    f"--print-to-pdf={out}", page.as_uri()], check=True, capture_output=True, timeout=300)
    if not out.exists() or out.stat().st_size == 0:
        raise BuildError("Chrome did not produce a PDF")


# ---------- diagram validation ----------
MERMAID = re.compile(r"^```mermaid[^\n]*\n(.*?)^```", re.S | re.M)


def validate_diagrams(book: Book, files: list[str]) -> list[str]:
    """Render every mermaid block in the given files with mmdc. Returns a list of failure messages."""
    mmdc = os.environ.get("MMDC") or shutil.which("mmdc")
    if not mmdc:
        raise BuildError("mmdc not found (npm install -g @mermaid-js/mermaid-cli)")
    cfg = puppeteer_config(book)
    work = book.path("build/diagrams/check")
    work.mkdir(parents=True, exist_ok=True)
    failures = []
    for rel in files:
        text = book.path(rel).read_text(encoding="utf-8")
        for i, m in enumerate(MERMAID.finditer(text), start=1):
            line = text.count("\n", 0, m.start()) + 1
            src = work / f"{Path(rel).stem}-{i}.mmd"
            out = src.with_suffix(".png")
            src.write_text(m.group(1), encoding="utf-8")
            proc = subprocess.run([mmdc, "-p", str(cfg), "-q", "-i", str(src), "-o", str(out)],
                                  capture_output=True, text=True, timeout=120)
            if proc.returncode != 0 or not out.exists():
                err = (proc.stderr or proc.stdout).strip().splitlines()
                detail = next((l for l in err if "Error" in l or "Parse" in l), err[-1] if err else "unknown error")
                failures.append(f"{rel}:{line}: diagram {i} failed: {detail.strip()}")
            else:
                print(f"ok  {rel}:{line} diagram {i}")
    return failures
