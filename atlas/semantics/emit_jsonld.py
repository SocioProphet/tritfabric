from __future__ import annotations

from typing import Any, Dict, Optional


def model_card_to_jsonld(card: Dict[str, Any], context_url: Optional[str] = None) -> Dict[str, Any]:
    """Convert a plain JSON model card dict into a JSON-LD object.

    This is intentionally conservative: we wrap without trying to invent a full ontology.
    The ontology work typically lives in dedicated repos (e.g., ontogenesis) and we pin contexts by ID.
    """
    obj: Dict[str, Any] = {"@context": context_url or "api/jsonld/math_context.jsonld"}
    # Keep type tags minimal; downstream can refine.
    obj["@type"] = "ModelCard"
    obj.update(card)
    return obj
