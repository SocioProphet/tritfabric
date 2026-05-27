from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from atlas.trit_status import TRIT_FALSE, TRIT_TRUE, status_reply

router = APIRouter(prefix="/v1/community", tags=["community"])


def _missing_hf_event_fields(event: Dict[str, Any]) -> List[str]:
    missing: List[str] = []
    if not event.get("consent") is True:
        missing.append("consent=true")
    if not event.get("license"):
        missing.append("license")
    if not event.get("lineage"):
        missing.append("lineage")
    if not event.get("rubric"):
        missing.append("rubric")
    if "score" not in event:
        missing.append("score")
    return missing


def _accepted_response(kind: str, event_id: str, extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
    payload = {"event_id": event_id, "kind": kind, "accepted": True, "mutates_model": False, "promotes_artifact": False}
    if extra:
        payload.update(extra)
    return status_reply(
        code=TRIT_TRUE,
        reason="COMMUNITY_EVENT_ACCEPTED",
        state="ACCEPTED",
        info={"event_id": event_id, "kind": kind},
        payload=payload,
    )


@router.post("/feedback")
def submit_feedback(event: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and accept a human-feedback event without training or promotion side effects."""
    missing = _missing_hf_event_fields(event)
    event_id = str(event.get("event_id") or event.get("id") or "")
    if missing:
        return status_reply(
            code=TRIT_FALSE,
            reason="COMMUNITY_EVENT_REJECTED",
            state="REJECTED",
            info={"event_id": event_id, "kind": "HFEvent", "missing": ",".join(missing)},
        )
    return _accepted_response("HFEvent", event_id)


@router.post("/curation")
def submit_curation(record: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and accept a curation record without moving it into training automatically."""
    missing: List[str] = []
    if not record.get("consent") is True:
        missing.append("consent=true")
    for field in ("record_id", "artifact_uri", "checksum", "license", "lineage"):
        if not record.get(field):
            missing.append(field)
    record_id = str(record.get("record_id") or record.get("id") or "")
    if missing:
        return status_reply(
            code=TRIT_FALSE,
            reason="COMMUNITY_EVENT_REJECTED",
            state="REJECTED",
            info={"event_id": record_id, "kind": "CurationRecord", "missing": ",".join(missing)},
        )
    return _accepted_response("CurationRecord", record_id)


@router.post("/eval")
def submit_eval(record: Dict[str, Any]) -> Dict[str, Any]:
    """Accept an evaluation report stub. Promotion remains a separate manual/reviewed path."""
    event_id = str(record.get("event_id") or record.get("eval_id") or record.get("id") or "")
    if not record.get("rubric") or "score" not in record:
        return status_reply(
            code=TRIT_FALSE,
            reason="COMMUNITY_EVENT_REJECTED",
            state="REJECTED",
            info={"event_id": event_id, "kind": "EvalRecord", "missing": "rubric,score"},
        )
    return _accepted_response("EvalRecord", event_id)


@router.post("/proposals")
def submit_proposal(record: Dict[str, Any]) -> Dict[str, Any]:
    """Accept a community proposal for review queueing only."""
    proposal_id = str(record.get("proposal_id") or record.get("id") or "")
    if not record.get("title") or not record.get("lineage"):
        return status_reply(
            code=TRIT_FALSE,
            reason="COMMUNITY_EVENT_REJECTED",
            state="REJECTED",
            info={"event_id": proposal_id, "kind": "Proposal", "missing": "title,lineage"},
        )
    return _accepted_response("Proposal", proposal_id, {"requires_manual_review": True})


@router.get("/reputation/{contributor_id}")
def get_reputation(contributor_id: str) -> Dict[str, Any]:
    """Return an explicit non-economic reputation placeholder."""
    if not contributor_id:
        raise HTTPException(status_code=400, detail="contributor_id required")
    return status_reply(
        code=TRIT_TRUE,
        reason="REPUTATION_PLACEHOLDER",
        state="READ_ONLY",
        info={"contributor_id": contributor_id},
        payload={
            "contributor_id": contributor_id,
            "credit": 0.0,
            "non_transferable": True,
            "economic_obligation": False,
        },
    )
