"""Read cheap first; pay for a second opinion only where a cheap answer is dangerous.

The bake-off (docs/MODEL-BAKEOFF.md) says the cheap models do not miss escalations, but they buy
their discount two ways: they invent escalations that are not there, and — worse — `gpt-5-nano`
read three *critical* tickets as high. An over-escalated ticket costs a person a minute. An
under-called critical ticket sits. So the trigger for a second read is not "the cheap model was
unsure": that would miss exactly the failure that matters, because nano was confident and wrong.

The trigger is **stakes plus doubt**. A ticket gets re-read on the expensive model when the cheap
reader says it is high-stakes (it escalates, or it is high/critical urgency) or when it says it is
unsure (category confidence under the routing threshold). Everything else ships on the cheap answer.

That deliberately re-reads more tickets than a confidence-only rule would. The saving is smaller and
the failure mode it protects against is the one that actually hurts.
"""
from __future__ import annotations

import os

from .models import Extraction, Urgency, URGENCY_RANK

# Urgency at or above this is treated as high-stakes and always gets the expensive read.
STAKES_FLOOR = Urgency.high


def enabled() -> bool:
    return os.environ.get("LLM_CASCADE", "").lower() in {"1", "true", "yes"}


def draft_model() -> str:
    return os.environ.get("CASCADE_DRAFT_MODEL", "gpt-5-mini")


def threshold() -> float:
    """Doubt threshold. Defaults to the routing threshold, so one number means one thing."""
    from . import routing
    return float(os.environ.get("CASCADE_CONFIDENCE", routing.low_confidence_threshold()))


def triage_mode() -> str:
    """`draft` re-reads after a cheap model. `rules` decides before paying anything.

    Measured (docs/CASCADE.md): the draft cascade *lost* money. It selects for exactly the hard
    tickets, and a hard ticket costs nearly twice the average on the expensive model, so the draft
    becomes pure overhead on the 58% that get re-read. The keyword layer already reads every ticket
    for free — using it as the triage step removes the overhead entirely.
    """
    return os.environ.get("CASCADE_TRIAGE", "draft").lower()


def triage_by_rules(text: str) -> tuple[bool, str]:
    """Decide which reader a ticket needs, before spending anything. One model call either way."""
    from . import rules
    base = rules.rules_only_extraction(text)
    final, hits, _ = rules.apply_escalation_rules(text, base)
    if hits:
        topics = ", ".join(sorted({h.rule.split(".")[0] for h in hits}))
        return True, f"a keyword rule matched ({topics}), so this is worth the expensive reader"
    if URGENCY_RANK[final.urgency] >= URGENCY_RANK[STAKES_FLOOR]:
        return True, f"keyword urgency read as {final.urgency.value} before any model ran"
    return False, "no escalation keyword and no urgency signal, so the cheap reader is enough"


def needs_second_read(x: Extraction) -> tuple[bool, str]:
    """Should this draft be re-read by the expensive model, and why?"""
    if x.escalate:
        return True, "the draft escalated it, and a wrong escalation call is expensive either way"
    if URGENCY_RANK[x.urgency] >= URGENCY_RANK[STAKES_FLOOR]:
        return True, f"the draft called it {x.urgency.value}, which is high-stakes enough to confirm"
    if x.category_confidence < threshold():
        return True, f"the draft was unsure about the category ({x.category_confidence:.2f})"
    return False, "low stakes and confident, so the draft stands"
