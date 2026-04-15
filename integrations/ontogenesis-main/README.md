# Ontogenesis — Human Digital Twin Ontology
Base IRI: `https://socioprophet.dev/ont/ontogenesis#`, Version IRI: `https://socioprophet.dev/ont/ontogenesis#v0.3.0`, Generated: 2025-08-28T22:28:24.218856Z

Contents: OWL (`ontogenesis.ttl`), SKOS (`skos/*.ttl`), SHACL (`shapes/*.ttl`), mappings, JSON-LD context, examples, tests, CapD.

## Quickstart

Install validation deps (local dev):
```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
```

Validate ontology + examples:
```bash
make validate
```

## Repo layout

- `ontogenesis.ttl` — core ontology (Turtle)
- `skos/*.ttl` — SKOS concept schemes/vocab
- `shapes/*.ttl` — SHACL shapes (constraints)
- `mappings/*.ttl` — interoperability mappings (e.g., PROV, FHIR, IEML)
- `context.jsonld` — JSON-LD context
- `examples/*.ttl` — example datasets
- `tests/*.rq` — SPARQL invariant tests (should return 0 rows)
- `capd/*.json` — CapD descriptor for capability packaging

## Diagrams

![Agentic Flow Architecture](docs/diagrams/agentic-flow-architecture.png)

![Agentic Flow Architecture — Human Twin](docs/diagrams/agentic-flow-architecture-body.png)
