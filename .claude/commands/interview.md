---
description: Interview the author and save the answers as new source files (kickoff, chapter gaps, or a named topic)
argument-hint: "[kickoff | chapter numbers like 2 3 | a topic in quotes] [--book folder]"
---
You run this interview yourself, in this conversation. Don't delegate it to a subagent: subagents can't talk to the author.

Book folder: `--book <folder>` in "$ARGUMENTS", default `.`. Read `<book>/book.yaml` first for the title, audience, and outline.

## 1. Pick the mode

- **kickoff**: "$ARGUMENTS" says `kickoff`, or book.yaml has no chapters yet. Goal: get the author's knowledge into `sources/` before `/outline`.
- **gaps**: "$ARGUMENTS" has chapter numbers, or is empty and chapters exist. Run `python3 -m forge --book <book> gaps` (add `--chapter N` per chapter if numbers were given) and read `<book>/build/gaps.md`. Also skim `<book>/build/reports/chNN-grounding.md` for those chapters if present. Your questions come from those gaps, in chapter order. If there are no gaps, say so and offer a topic interview instead.
- **topic**: any other text. Interview about that topic.

Tell the author in one or two lines what you'll cover, roughly how many questions, and that they can answer "skip", "don't know", or "done" at any time. Mention that dictation works fine; you'll clean it up.

## 2. Ask

- One question at a time, in plain chat. Short questions: the author may be on a phone.
- Kickoff order: what the book is for and who it's for, then the main topics in the order a reader meets them. For each topic: what it is, why it matters, how to do it (exact commands, settings, steps), what goes wrong, and a real example or story. Topics come from the author; don't propose an outline.
- Gaps order: one gap at a time. Quote the gap briefly, then ask for the specific missing fact.
- Follow up once when an answer is vague and the book needs specifics: "What's the exact command?", "What's the default?", "Can you give an example from a real project?"
- You may offer a guess as a yes/no question ("Is the default 30 seconds?"). Record it only if the author confirms it.
- Every 5 or so answers, save what you have (step 3) so nothing is lost if the conversation ends.

## 3. Save

Write the answers to `<book>/sources/interviews/<slug>.md`: one file per kickoff topic, one per chapter for gaps (`chNN-<chapter-slug>.md`), or one for the topic. If the file exists, append to it.

```markdown
# Interview: <topic or "Chapter N: Title">

Source: interview with <author from book.yaml>, <today's date>. The author's own answers, lightly edited.

## <the question, rephrased as a short heading>

<the answer>
```

Rules for the answers:
- Record what the author said and nothing else. Fix typos, dictation errors, and fragments; keep their wording and voice where you can.
- Never add a fact, number, or command the author didn't say, even one you're sure of.
- Commands, code, config, and paths go in fenced code blocks, exactly as given. If dictation garbled one, ask the author to confirm the exact text.
- Leave skipped questions out.

## 4. Wire it in

1. Run `python3 -m forge --book <book> ingest`.
2. **gaps mode:** add the new source id (`interviews/chNN-<slug>`) to that chapter's `sources:` list in book.yaml. Change nothing else in book.yaml.
3. **topic mode with an existing outline:** ask the author which chapter the new file belongs to, then add it to that chapter's `sources:`.
4. **kickoff mode:** change nothing in book.yaml; the outliner places the files.
5. Run `python3 -m forge --book <book> check --coverage` and fix any error you caused.

## 5. Next step

Say which files you wrote and how many answers they hold, then suggest the next step: `/outline` after a kickoff, or `/write N` (then `/review N`) for the chapters whose gaps you filled.
