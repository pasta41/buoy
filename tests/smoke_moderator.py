"""T4 smoke test — one real moderator decision against the live Claude API.

Run from anywhere:

    python tests/smoke_moderator.py

Exit codes:
  0  PASS (a valid `Decision` came back) — or SKIP when a prerequisite is
     missing (no ANTHROPIC_API_KEY, or the `anthropic` SDK isn't installed)
  1  the call ran but failed (bad response / validation error)

Kept as a plain script (no pytest dependency) so it runs with the app's
existing environment. Lift into a pytest case later if we add a test runner.
"""
import os
import sys

# Make `app` importable no matter where this script is launched from.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("SKIP: ANTHROPIC_API_KEY not set — this smoke test hits the real API.")
        return 0
    try:
        import anthropic  # noqa: F401
    except ModuleNotFoundError:
        print("SKIP: `anthropic` not installed (pip install anthropic).")
        return 0

    # Imported here so the module still loads when `anthropic` is absent.
    from app.config import settings
    from app.moderator.client import decide
    from app.moderator.schema import Decision

    system = (
        "You are Buoy, a neutral moderator for a two-person debate about whether "
        "cities should adopt congestion pricing. The participants are labelled P1 "
        "and P2. After reading the exchange so far, decide whether a light-touch "
        "process intervention would help the two reason with each other. Most of "
        "the time the right choice is NOT to intervene (intervene=false, "
        "intervention_type='none'). Be restrained and never take a side."
    )
    transcript = (
        "P1: Congestion pricing is just a tax on working people who have no choice "
        "but to drive into the city.\n"
        "P2: It reduces traffic and funds transit, so it actually helps commuters."
    )

    print(f"Calling {settings.model} (one real API request)...")
    decision = decide(system, transcript)

    assert isinstance(decision, Decision), f"expected Decision, got {type(decision)}"
    assert isinstance(decision.intervene, bool)
    assert decision.rationale, "rationale should be non-empty"

    print("PASS — Decision returned and validated:")
    print(f"  intervene         = {decision.intervene}")
    print(f"  intervention_type = {decision.intervention_type}")
    print(f"  target_participant= {decision.target_participant}")
    print(f"  crux_type         = {decision.crux_type}")
    print(f"  rationale         = {decision.rationale}")
    print(f"  intervention_text = {decision.intervention_text}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
