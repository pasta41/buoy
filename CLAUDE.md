# How We Work Together

Durable rules for this collaboration. This file is auto-loaded into Claude's
context each session. Keep it about *how* we work; assignment substance lives in
`TASKS.md`.

## Ground rules

1. **Nothing is "done" until Cooper says so.** Claude proposes completion
   ("I believe this satisfies X — ready for review"); Cooper decides. Claude
   never unilaterally marks a task done.

2. **Hand-off is explicit.** After reviewing, Cooper says **"done, next"** or
   **"still working"**. No ambiguity about whether we've moved on.

3. **Cooper is an active participant.** When Claude hits a genuine fork
   (ambiguous requirement, design trade-off with no obvious default, unclear
   intent), Claude stops and asks rather than guessing. Claude flags which kind
   of question it is: *"I can't decide this for you"* vs *"I want your buy-in."*

4. **No silent scope changes or file edits.** Claude shows proposed changes to
   shared files (`CLAUDE.md`, `TASKS.md`, code) before/as it makes them, and
   does not expand scope beyond the agreed task.

5. **Don't rush.** Deliberate over fast. A task called "done" prematurely wastes
   time and causes confusion. Better to under-claim and let Cooper confirm.

## Task tracking

- Open/closed tasks live in `TASKS.md`.
- When Cooper marks something done, it moves Open → Closed, and *then* we pick
  the next task together — deliberately, not automatically.

## Working patterns (added as they emerge)

- **Deliverable outputs go in `tmp-outputs/`** in the repo (not the system
  scratchpad), so they're easily accessible and can be committed to git history
  if we choose. Scratch/intermediate working files may still use the system
  scratchpad; finished outputs Cooper might want to keep or commit go here.
