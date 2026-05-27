from __future__ import annotations

from typing import Any, Dict, Optional

from rdflib import Graph, Literal, Namespace, RDF, URIRef


def model_card_to_turtle(card: Dict[str, Any], ontology_ttl: Optional[str] = None) -> str:
    """Emit a minimal Turtle graph for a model card.

    The graph carries the promotion-gate fields enforced by
    `api/shapes/model_shapes.ttl`: mathType, calcOps, ledgerRef, and artifactRef.
    """
    g = Graph()
    ATLAS = Namespace("https://socioprophet.dev/ont/atlas#")

    mid = str(card.get("model", {}).get("id", "unknown"))
    m = URIRef(f"urn:atlas:model:{mid}")
    mc = URIRef(f"urn:atlas:model-card:{mid}")
    g.add((m, RDF.type, ATLAS.Model))
    g.add((mc, RDF.type, ATLAS.ModelCard))
    g.add((mc, ATLAS.model, m))

    g.add((m, ATLAS.task, Literal(card.get("model", {}).get("task", ""))))
    g.add((m, ATLAS.family, Literal(card.get("model", {}).get("family", ""))))
    g.add((m, ATLAS.tenant, Literal(card.get("model", {}).get("tenant", "default"))))

    for value in card.get("mathType", []) or []:
        g.add((m, ATLAS.mathType, Literal(str(value))))
    for value in card.get("calcOps", []) or []:
        g.add((m, ATLAS.calcOps, Literal(str(value))))

    ledger_ref = str(card.get("ledgerRef") or "")
    if ledger_ref:
        ledger = URIRef(f"urn:atlas:ledger:{mid}")
        g.add((ledger, RDF.type, ATLAS.Ledger))
        g.add((ledger, ATLAS.path, Literal(ledger_ref)))
        g.add((m, ATLAS.ledgerRef, ledger))
        g.add((mc, ATLAS.ledger, ledger))

    artifact_ref = str(card.get("artifactRef") or "")
    if artifact_ref:
        artifact = URIRef(f"urn:atlas:artifact:{mid}")
        g.add((artifact, RDF.type, ATLAS.Artifact))
        g.add((artifact, ATLAS.path, Literal(artifact_ref)))
        g.add((m, ATLAS.artifactRef, artifact))

    # dataset linkage
    ds_uri = str(card.get("data", {}).get("train_uri", ""))
    if ds_uri:
        d = URIRef(f"urn:atlas:dataset:{mid}")
        g.add((d, RDF.type, ATLAS.Dataset))
        g.add((d, ATLAS.uri, Literal(ds_uri)))
        g.add((m, ATLAS.trainedOn, d))

    # metrics (flatten)
    metrics = card.get("metrics", {}) or {}
    if metrics:
        g.add((mc, ATLAS.metrics, Literal("present")))
    for k, v in metrics.items():
        try:
            g.add((m, ATLAS.metric, Literal(f"{k}={float(v)}")))
        except Exception:
            g.add((m, ATLAS.metric, Literal(f"{k}={v}")))

    if ontology_ttl:
        try:
            g.parse(ontology_ttl, format="turtle")
        except Exception:
            # Optional; ignore parse failures in minimal mode.
            pass

    return g.serialize(format="turtle")
