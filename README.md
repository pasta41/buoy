# Buoy

A deployed prototype where two people who genuinely disagree debate a contested question — *should cities adopt congestion pricing?* — with Claude as a **neutral moderator** (not a judge).

**Live prototype:** https://buoy-2ejg.onrender.com

---

## 👉 Start here: [`WRITE-UP.md`](WRITE-UP.md)

**[`WRITE-UP.md`](WRITE-UP.md) is the design rationale the assignment asked for — that's the document to read.** Everything else in the repo root is supporting material that shows the work behind it.

## Supporting artifacts

- [`bias-eval-v0.1.md`](bias-eval-v0.1.md) — full results of the Part-4 bias evaluation (harness in [`eval/`](eval/)).
- [`transcripts/`](transcripts/) — real debate transcripts exported from the **deployed** prototype: each is the full P1/P2 message thread plus the moderator's decision log, **including the silent no-ops**. Start at [`transcripts/index.md`](transcripts/index.md); regenerate with [`scripts/export_transcripts.py`](scripts/export_transcripts.py). (Distinct from `claude_transcript.md`, which is the Claude Code build session.)
- [`CONSTITUTIONv0.1.md`](CONSTITUTIONv0.1.md) — the moderator's constitution (the neutrality mechanism: model-facing clauses + harness-enforced commitments).
- [`DESIGN.md`](DESIGN.md) — living design notebook: every decision and why, the intervention taxonomy, deliberate cuts.
- [`SPEC.md`](SPEC.md) — technical spec (data model, routes, concurrency).
- [`my-notes.md`](my-notes.md) — my original brain-dump on first reading the assignment (the provenance of the write-up's framings).
- [`REQUIREMENTS.md`](REQUIREMENTS.md) — assignment-requirements checklist.
- [`claude_transcript.md`](claude_transcript.md) — the full Claude Code session transcript (this project, start to finish).
- [`transcript_to_md.py`](transcript_to_md.py) — the small converter used to produce `claude_transcript.md` from Claude Code's raw JSONL session log.
- [`app/`](app/) — application code; [`tests/`](tests/) — tests.

**🎥 Design-rationale video (screenshare walkthrough, 7:58):** [`buoy-walkthrough.mp4`](buoy-walkthrough.mp4)

## Testing with two participants on one machine

Buoy ties each participant's seat to a **per-browser cookie**, so two participants need two separate cookie jars. On a single machine, open the session link in your **normal browser window** for one participant and a **private / incognito window** (or a different browser) for the other — that lets one person set up and drive both P1 and P2 at once. Using the same non-private window for both just reclaims the same seat.
