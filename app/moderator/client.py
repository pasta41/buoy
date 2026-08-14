"""Anthropic SDK wrapper — the moderator's single structured decision call (T4).

`decide()` is the one API round-trip per participant message. It forces the
`Decision` schema via structured outputs (`messages.parse`), so the return value
is an already-validated `Decision` — no tool-result plumbing to unwrap.

Auth: a zero-arg `anthropic.Anthropic()` resolves `ANTHROPIC_API_KEY` from the
environment (Render env var; local `.env`). Do **not** pass
`settings.anthropic_api_key` into the constructor — when it defaults to the
empty string that would authenticate with an empty key instead of failing over
to the env / an `ant` profile. The client is built lazily so this module still
imports cleanly when no key is set.

Model: `settings.model` (default `claude-sonnet-5` for latency/cost on a call
that fires after every message; Opus 5 via `BUOY_MODEL` for a quality arm).

Latency tuning (deferred to T5, where it can be checked against a real key):
an `output_config={"effort": "low"}` or `thinking={"type": "disabled"}` pass
would trim latency, but is left off here to keep the T4 call plainly correct.
Note `temperature`/`top_p` are **rejected (400) on Sonnet 5 / Opus 5** — never
forward a `temperature` from `Moderator.config` to this call.
"""
from functools import lru_cache

import anthropic

from ..config import settings
from .schema import Decision


@lru_cache(maxsize=1)
def _client() -> anthropic.Anthropic:
    """Lazily construct (and cache) the SDK client so import stays keyless."""
    return anthropic.Anthropic()


def decide(system: str, transcript: str, state: str | None = None) -> Decision:
    """Run one moderator decision and return a validated `Decision`.

    `transcript` uses neutral labels (P1/P2), not display names — name-blinding
    by construction (DESIGN.md). `state` is the optional structured
    debate-state blob (Moderator `config.input_mode == "raw+state"`); omit it in
    `raw` mode.
    """
    user_content = transcript
    if state:
        user_content = f"{transcript}\n\n<debate_state>\n{state}\n</debate_state>"

    response = _client().messages.parse(
        model=settings.model,
        # Must cover adaptive thinking (on by default on Sonnet 5 / Opus 5) *plus*
        # the JSON Decision. 2048 truncated the output mid-string once thinking ran
        # — a correctness bug (silent error-no-op), distinct from cost/latency tuning.
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user_content}],
        output_format=Decision,
    )
    return response.parsed_output
