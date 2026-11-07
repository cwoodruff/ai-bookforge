"""Unit tests for AI Book Forge. Run from the repo root: python3 -m unittest discover -s tests -v"""
from __future__ import annotations

import shutil
import tempfile
import textwrap
import unittest
from pathlib import Path

import yaml

from forge import briefs, build, checks, gaps, ingest
from forge.config import Book, ConfigError, TOOL_ROOT, slugify

EXAMPLE = TOOL_ROOT / "examples" / "tiny-book"

CHAPTER = """# Chapter 1: Intro

> **Prerequisites:** None.

## What You'll Learn

- one

## Concepts

```mermaid
flowchart LR
  A --> B
```

```mermaid
flowchart LR
  B --> C
```

## Hands-On: Try It

```bash
echo hi
```

## Summary

Done.

## Exercises

1. One.

## Quiz

1. Q?
"""

SOLUTION = "# Chapter 1 Solutions\n\n## Exercise Solutions\n\n1. A.\n\n## Quiz Answers\n\n1. Yes.\n"


def make_book(tmp: Path, chapters=None, sources=("intro",), extra=None) -> Path:
    data = {
        "title": "Test Book",
        "author": "Tester",
        "targets": {"words_per_chapter": [1, 100000], "min_diagrams": 2},
        "appendices": [{"id": "A", "title": "Quiz Answers", "generate": "quiz"}],
        "parts": [{"title": "One", "chapters": chapters if chapters is not None else [
            {"title": "Intro", "slug": "intro", "sources": ["intro"], "template": "light"}]}],
    }
    data.update(extra or {})
    (tmp / "book.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")
    (tmp / "sources").mkdir()
    for s in sources:
        (tmp / "sources" / f"{s}.md").parent.mkdir(parents=True, exist_ok=True)
        (tmp / "sources" / f"{s}.md").write_text(f"# {s.title()}\n\nSome words about {s}.\n\n## Part\n\ntext\n", encoding="utf-8")
    return tmp


def write_chapter(tmp: Path, text=CHAPTER, solution=SOLUTION):
    (tmp / "book/part-01").mkdir(parents=True, exist_ok=True)
    (tmp / "book/part-01/ch01-intro.md").write_text(text, encoding="utf-8")
    (tmp / "solutions").mkdir(exist_ok=True)
    (tmp / "solutions/ch01.md").write_text(solution, encoding="utf-8")


class TempBook(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)


class ConfigTests(TempBook):
    def test_slugify(self):
        self.assertEqual(slugify("Routing, Capability & Modes!"), "routing-capability-modes")
        self.assertEqual(slugify("???"), "chapter")

    def test_numbering_is_continuous_across_parts(self):
        make_book(self.tmp, chapters=[{"title": "A"}])
        data = yaml.safe_load((self.tmp / "book.yaml").read_text())
        data["parts"].append({"title": "Two", "chapters": [{"title": "B", "prereqs": [1]}]})
        (self.tmp / "book.yaml").write_text(yaml.safe_dump(data))
        book = Book(self.tmp)
        self.assertEqual([c.number for c in book.chapters], [1, 2])
        self.assertEqual(book.chapter(2).path, "book/part-02/ch02-b.md")

    def test_bad_prereq_rejected(self):
        make_book(self.tmp, chapters=[{"title": "A", "prereqs": [1]}])
        with self.assertRaises(ConfigError):
            Book(self.tmp)

    def test_missing_title_rejected(self):
        make_book(self.tmp, extra={"title": ""})
        with self.assertRaises(ConfigError):
            Book(self.tmp)

    def test_duplicate_slug_rejected(self):
        make_book(self.tmp, chapters=[{"title": "A", "slug": "x"}, {"title": "B", "slug": "x"}])
        with self.assertRaises(ConfigError):
            Book(self.tmp)


class IngestTests(TempBook):
    def test_inventory(self):
        make_book(self.tmp, sources=("intro", "nested/deep"))
        items = ingest.run(Book(self.tmp))
        self.assertEqual([i["id"] for i in items], ["intro", "nested/deep"])
        self.assertTrue((self.tmp / "build/inventory.md").exists())
        self.assertEqual(items[0]["title"], "Intro")

    def test_word_count_ignores_code(self):
        self.assertEqual(ingest.word_count("one two\n```bash\nthree four five\n```\n"), 2)


class CoverageTests(TempBook):
    def test_unassigned_source_is_an_error(self):
        make_book(self.tmp, sources=("intro", "orphan"))
        r = checks.run(Book(self.tmp), coverage_only=True)
        self.assertTrue(any("orphan" in e for e in r.errors))

    def test_excluded_source_is_fine(self):
        make_book(self.tmp, sources=("intro", "orphan"), extra={"exclude_sources": ["orphan"]})
        self.assertTrue(checks.run(Book(self.tmp), coverage_only=True).ok)

    def test_missing_source_is_an_error(self):
        make_book(self.tmp, chapters=[{"title": "Intro", "sources": ["intro", "ghost"], "template": "light"}])
        r = checks.run(Book(self.tmp), coverage_only=True)
        self.assertTrue(any("ghost" in e for e in r.errors))


class ChapterCheckTests(TempBook):
    def setUp(self):
        super().setUp()
        make_book(self.tmp)

    def errors(self):
        return checks.run(Book(self.tmp)).errors

    def test_valid_chapter_passes(self):
        write_chapter(self.tmp)
        self.assertEqual(self.errors(), [])

    def test_missing_section(self):
        write_chapter(self.tmp, CHAPTER.replace("## Summary\n", "## Wrap-up\n"))
        self.assertTrue(any("Summary" in e for e in self.errors()))

    def test_out_of_order_section(self):
        text = CHAPTER.replace("## Summary\n\nDone.\n\n", "").replace("## Hands-On", "## Summary\n\nDone.\n\n## Hands-On")
        write_chapter(self.tmp, text)
        self.assertTrue(any("out of order" in e for e in self.errors()))

    def test_too_few_diagrams(self):
        write_chapter(self.tmp, CHAPTER.replace("```mermaid", "```text", 1))
        self.assertTrue(any("diagram" in e for e in self.errors()))

    def test_missing_prerequisites(self):
        write_chapter(self.tmp, CHAPTER.replace("> **Prerequisites:** None.\n", ""))
        self.assertTrue(any("Prerequisites" in e for e in self.errors()))

    def test_wrong_title(self):
        write_chapter(self.tmp, CHAPTER.replace("# Chapter 1:", "# Chapter 2:"))
        self.assertTrue(any("first line" in e for e in self.errors()))

    def test_bad_cross_reference(self):
        write_chapter(self.tmp, CHAPTER.replace("Done.", "See Chapter 9 and Appendix Z."))
        errs = self.errors()
        self.assertTrue(any("Chapter 9" in e for e in errs))
        self.assertTrue(any("Appendix Z" in e for e in errs))

    def test_missing_quiz_answers(self):
        write_chapter(self.tmp, solution="# Chapter 1 Solutions\n\n## Exercise Solutions\n")
        self.assertTrue(any("Quiz Answers" in e for e in self.errors()))


class BriefTests(TempBook):
    def test_unknown_placeholder_fails(self):
        with self.assertRaises(KeyError):
            briefs.render("{{nope}}", {}, "t.md")

    def test_prereq_text(self):
        self.assertEqual(briefs.prereq_text([]), "None.")
        self.assertEqual(briefs.prereq_text([2]), "Chapter 2.")
        self.assertEqual(briefs.prereq_text([3, 1]), "Chapters 1 and 3.")
        self.assertEqual(briefs.prereq_text([1, 2, 4]), "Chapters 1, 2, and 4.")

    def test_profile_templates_render(self):
        make_book(self.tmp)
        written = briefs.run(Book(self.tmp))
        self.assertIn("build/briefs/ch01.md", written)
        brief = (self.tmp / "build/briefs/ch01.md").read_text()
        self.assertIn("sources/intro.md", brief)
        self.assertNotIn("{{", brief)


class GeneratedAppendixTests(TempBook):
    def test_quiz_appendix_collects_answers(self):
        make_book(self.tmp)
        write_chapter(self.tmp)
        book = Book(self.tmp)
        build.generate(book)
        text = (self.tmp / book.appendices[0].path).read_text()
        self.assertIn("## Chapter 1: Intro", text)
        self.assertIn("1. Yes.", text)


PNG = bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010806000000"
                    "1f15c4890000000d49444154789c6300010000000500010d0a2db40000000049454e44ae426082")


class ImageTests(TempBook):
    def setUp(self):
        super().setUp()
        make_book(self.tmp)
        (self.tmp / "sources/img").mkdir()
        (self.tmp / "sources/img/a.png").write_bytes(PNG)
        src = self.tmp / "sources/intro.md"
        src.write_text(src.read_text() + "\n![A diagram](img/a.png)\n\n```markdown\n![not real](img/none.png)\n```\n")

    def test_ingest_resolves_paths_and_skips_code(self):
        items = ingest.run(Book(self.tmp))
        self.assertEqual(items[0]["images"], [{"path": "sources/img/a.png", "alt": "A diagram", "exists": True}])

    def test_brief_lists_images(self):
        briefs.run(Book(self.tmp))
        self.assertIn("`sources/img/a.png`", (self.tmp / "build/briefs/ch01.md").read_text())

    def test_chapter_image_must_exist(self):
        write_chapter(self.tmp, CHAPTER.replace("Done.", "![Missing](sources/img/b.png)"))
        self.assertTrue(any("does not exist" in e for e in checks.run(Book(self.tmp)).errors))

    def test_chapter_image_from_sources_passes(self):
        write_chapter(self.tmp, CHAPTER.replace("Done.", "![A diagram](sources/img/a.png)"))
        r = checks.run(Book(self.tmp))
        self.assertEqual(r.errors, [])
        self.assertFalse(any("image" in w for w in r.warnings))

    def test_unreferenced_source_image_warns(self):
        (self.tmp / "sources/img/loose.png").write_bytes(PNG)
        r = checks.run(Book(self.tmp), coverage_only=True)
        self.assertTrue(any("loose.png" in w for w in r.warnings))


class GapTests(unittest.TestCase):
    def test_finds_source_gap_notes_only(self):
        text = textwrap.dedent("""\
            > **Note:** The source material doesn't cover the default port.

            > **Note:** This tool is fictional.

            > **Tip:** The sources don't say, but try it.

            > **Note:** The sources say "first run" but don't say
            > whether `--version` counts.

            ```markdown
            > **Note:** The source material doesn't cover code blocks.
            ```
            """)
        found = gaps.find(text)
        self.assertEqual([line for line, _ in found], [1, 7])
        self.assertIn("whether `--version` counts", found[1][1])

    def test_example_gaps_written(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            dest = tmp / "book"
            shutil.copytree(EXAMPLE, dest, ignore=shutil.ignore_patterns("build", "dist"))
            found = gaps.run(Book(dest))
            self.assertTrue(found)
            self.assertTrue((dest / "build/gaps.md").exists())
        finally:
            shutil.rmtree(tmp)


class ExampleBookTests(unittest.TestCase):
    """The committed example must always pass every deterministic check."""

    def test_example_passes_checks(self):
        r = checks.run(Book(EXAMPLE))
        self.assertEqual(r.errors, [])


@unittest.skipUnless(shutil.which("pandoc") and shutil.which("mmdc") and build.find_chrome(), "needs pandoc, mmdc, and Chrome")
class BuildTests(unittest.TestCase):
    def test_example_builds_all_formats(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            dest = tmp / "book"
            shutil.copytree(EXAMPLE, dest, ignore=shutil.ignore_patterns("build", "dist"))
            outs = build.run(Book(dest), list(build.FORMATS))
            for out in outs:
                self.assertGreater(out.stat().st_size, 1000, out)
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
