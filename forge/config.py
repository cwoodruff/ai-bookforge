"""Load book.yaml and derive every path and number the rest of the tool needs."""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import yaml

TOOL_ROOT = Path(__file__).resolve().parent.parent


class ConfigError(Exception):
    pass


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:40].rstrip("-") or "chapter"


@dataclass
class Chapter:
    number: int
    title: str
    slug: str
    part: "Part"
    sources: list[str]
    prereqs: list[int]
    template: str
    summary: str

    @property
    def path(self) -> str:
        return f"book/part-{self.part.number:02d}/ch{self.number:02d}-{self.slug}.md"

    @property
    def solution_path(self) -> str:
        return f"solutions/ch{self.number:02d}.md"

    @property
    def brief_path(self) -> str:
        return f"build/briefs/ch{self.number:02d}.md"


@dataclass
class Part:
    number: int
    title: str
    intro: str
    chapters: list[Chapter] = field(default_factory=list)


@dataclass
class Appendix:
    id: str
    title: str
    generate: str | None  # "quiz", "glossary", or None (agent-written)
    brief: str
    sources: list[str]

    @property
    def slug(self) -> str:
        return slugify(self.title)

    @property
    def path(self) -> str:
        if self.generate:
            return f"build/gen/app-{self.id}-{self.slug}.md"
        return f"book/appendices/app-{self.id}-{self.slug}.md"

    @property
    def brief_path(self) -> str:
        return f"build/briefs/app-{self.id}.md"


class Book:
    def __init__(self, root: str | Path = "."):
        self.root = Path(root).resolve()
        cfg = self.root / "book.yaml"
        if not cfg.exists():
            raise ConfigError(f"no book.yaml in {self.root} (run `make init` or pass --book DIR)")
        self.data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
        for key in ("title", "author"):
            if not self.data.get(key):
                raise ConfigError(f"book.yaml: '{key}' is required")
        self.profile_name = self.data.get("profile", "technical-handson")
        self.profile_dir = self._find_profile(self.profile_name)
        self.rules = yaml.safe_load((self.profile_dir / "rules.yaml").read_text(encoding="utf-8")) or {}
        self.parts: list[Part] = []
        self.chapters: list[Chapter] = []
        self._load_parts()
        self.appendices = [
            Appendix(
                id=str(a["id"]),
                title=a["title"],
                generate=a.get("generate"),
                brief=a.get("brief", ""),
                sources=list(a.get("sources") or []),
            )
            for a in self.data.get("appendices") or []
        ]

    # ---------- helpers ----------
    def _find_profile(self, name: str) -> Path:
        for base in (self.root / "profiles", TOOL_ROOT / "profiles"):
            if (base / name / "rules.yaml").exists():
                return base / name
        raise ConfigError(f"profile '{name}' not found in profiles/")

    def _load_parts(self) -> None:
        n = 0
        seen_slugs = set()
        for pi, p in enumerate(self.data.get("parts") or [], start=1):
            if not p.get("title"):
                raise ConfigError(f"part {pi} needs a title")
            part = Part(number=pi, title=p["title"], intro=(p.get("intro") or "").strip())
            for c in p.get("chapters") or []:
                n += 1
                if not c.get("title"):
                    raise ConfigError(f"chapter {n} needs a title")
                slug = c.get("slug") or slugify(c["title"])
                if slug in seen_slugs:
                    raise ConfigError(f"duplicate chapter slug '{slug}'")
                seen_slugs.add(slug)
                prereqs = [int(x) for x in (c.get("prereqs") or [])]
                ch = Chapter(
                    number=n,
                    title=c["title"],
                    slug=slug,
                    part=part,
                    sources=[str(s) for s in (c.get("sources") or [])],
                    prereqs=prereqs,
                    template=c.get("template", "full"),
                    summary=(c.get("summary") or "").strip(),
                )
                part.chapters.append(ch)
                self.chapters.append(ch)
            self.parts.append(part)
        for ch in self.chapters:
            if ch.template not in self.rules.get("sections", {}):
                raise ConfigError(f"chapter {ch.number}: unknown template '{ch.template}'")
            for p in ch.prereqs:
                if not 1 <= p < ch.number:
                    raise ConfigError(f"chapter {ch.number}: prerequisite {p} must be an earlier chapter")

    def path(self, rel: str) -> Path:
        return self.root / rel

    def chapter(self, number: int) -> Chapter:
        for ch in self.chapters:
            if ch.number == number:
                return ch
        raise ConfigError(f"no chapter {number} in book.yaml")

    # ---------- derived settings ----------
    @property
    def slug(self) -> str:
        return self.data.get("slug") or slugify(self.data["title"])

    @property
    def targets(self) -> dict:
        t = dict(self.rules.get("targets") or {})
        t.update(self.data.get("targets") or {})
        t.setdefault("words_per_chapter", [3000, 6000])
        t.setdefault("min_diagrams", 2)
        return t

    @property
    def quiz_enabled(self) -> bool:
        return any("Quiz" in s for s in self.rules["sections"].get("full", []))

    @property
    def identifier(self) -> str:
        return self.data.get("identifier") or f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, 'ai-bookforge:' + self.data['title'] + ':' + self.data['author'])}"

    def source_ids(self) -> list[str]:
        """Every markdown file under sources/, as a path relative to sources/ without .md."""
        src = self.root / "sources"
        if not src.is_dir():
            return []
        return sorted(str(p.relative_to(src).with_suffix("")) for p in src.rglob("*.md"))

    def source_path(self, sid: str) -> str:
        return f"sources/{sid}.md"
