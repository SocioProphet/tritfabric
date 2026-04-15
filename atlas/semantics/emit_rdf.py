from __future__ import annotations

from typing import Any, Dict, Optional

from rdflib import Graph, Literal, Namespace, RDF, URIRef


def model_card_to_turtle(card: Dict[str, Any], ontology_ttl: Optional[str] = None) -> str:
    """Emit a minimal Turtle graph for a model card.

    We do *not* attempt to fully encode every field. The purpose is:
    - provide a graph surface for SHACL validation
    - enable provenance hooks
    """
    g = Graph()
    ATLAS = Namespace("https://socioprophet.dev/ont/atlas#")

    mid = str(card.get("model", {}).get("id", "unknown"))
    m = URIRef(f"urn:atlas:model:{mid}")
    g.add((m, RDF.type, ATLAS.Model))

    g.add((m, ATLAS.task, Literal(card.get("model", {}).get("task", ""))))
    g.add((m, ATLAS.family, Literal(card.get("model", {}).get("family", ""))))
    g.add((m, ATLAS.tenant, Literal(card.get("model", {}).get("tenant", "default"))))

    # dataset linkage
    ds_uri = str(card.get("data", {}).get("train_uri", ""))
    if ds_uri:
        d = URIRef(f"urn:atlas:dataset:{hash(ds_uri)}")
        g.add((d, RDF.type, ATLAS.Dataset))
        g.add((d, ATLAS.uri, Literal(ds_uri)))
        g.add((m, ATLAS.trainedOn, d))

    # metrics (flatten)
    metrics = card.get("metrics", {}) or {}
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
