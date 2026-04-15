from __future__ import annotations

from typing import Tuple


def validate_trial_graph_turtle(
    turtle: str,
    shapes_path: str,
    ontology_path: str | None = None,
) -> Tuple[bool, str]:
    """Validate a turtle graph against SHACL shapes.

    If `pyshacl` is not installed, we return (True, warning).

    Returns:
        (conforms, report_text)
    """
    try:
        from rdflib import Graph
        from pyshacl import validate  # type: ignore
    except Exception:
        return True, "pyshacl not installed; SHACL validation skipped."

    data_g = Graph()
    data_g.parse(data=turtle, format="turtle")

    shacl_g = Graph()
    shacl_g.parse(shapes_path, format="turtle")

    ont_g = None
    if ontology_path:
        ont_g = Graph()
        ont_g.parse(ontology_path, format="turtle")

    conforms, report_graph, report_text = validate(
        data_graph=data_g,
        shacl_graph=shacl_g,
        ont_graph=ont_g,
        inference="rdfs",
        meta_shacl=False,
        advanced=True,
        debug=False,
    )
    return bool(conforms), str(report_text)
