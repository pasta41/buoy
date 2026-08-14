"""Structured-output contract for the moderator's decision (T4).

`Decision` is the single object the moderator model returns for every
participant message. It maps onto the `ModeratorAction` columns in `models.py`,
so the decision is machine-readable and loggable — including no-ops, which carry
`intervene=False` / `intervention_type="none"` and produce no `Message`.

Fields are **required (no Python defaults)** on purpose: strict structured
outputs then force the model to fill every slot, so each decision is fully
explicit in the log rather than leaning on client-side defaults. Optional slots
are expressed as nullable (`X | None`) — present but possibly null.

The `intervention_type` set is the provisional taxonomy from DESIGN.md; the
final cull to a minimal, well-separated enum is deferred to T5 (the schema
stores it as a plain string, so the enum isn't frozen).
"""
from typing import Literal, Optional

from pydantic import BaseModel, model_validator

# Provisional intervention taxonomy (DESIGN.md — final cull @ T5).
InterventionType = Literal[
    # engagement
    "note_talking_past", "surface_neglected_claim", "note_unanswered_challenge",
    "note_misread", "prompt_engagement_with_strongest",
    # meaning / structure
    "clarify_term", "invite_clarification", "mark_agreement", "summarize_state",
    "identify_crux",
    # epistemic
    "request_justification", "supply_evidence", "correct_factual_error",
    "flag_uncertainty",
    # conduct
    "check_tone",
    # no-op
    "none",
]


class Decision(BaseModel):
    """The moderator's whole decision for one participant message.

    `intervention_type` is the single source of truth — `"none"` means no-op.
    `intervene` is *derived*, not a field the model can contradict (item 1b). A
    post-parse validator normalizes the dependent fields to stay consistent —
    it **coerces, never rejects**, since a rejected structured-output parse would
    waste the API call.
    """

    intervention_type: InterventionType
    # Neutral participant label the intervention addresses, or None = both.
    # Schema-constrained to P1/P2 so the model can't leak a real name. The T5
    # cycle maps P1/P2 → the seat's real user_id when writing ModeratorAction.
    target_participant: Optional[Literal["P1", "P2"]]
    # Only meaningful when intervention_type == "identify_crux".
    crux_type: Optional[Literal["empirical", "value", "mixed"]]
    # Why the moderator decided this. Always logged; not necessarily shown.
    rationale: str
    # Shown to participants; present only when intervening.
    intervention_text: Optional[str]

    @property
    def intervene(self) -> bool:
        """Derived: any type other than 'none' is an intervention."""
        return self.intervention_type != "none"

    @model_validator(mode="after")
    def _normalize(self) -> "Decision":
        if self.intervention_type == "none":
            # A no-op carries no target, crux, or text.
            self.target_participant = None
            self.crux_type = None
            self.intervention_text = None
        if self.intervention_type != "identify_crux":
            self.crux_type = None
        return self
