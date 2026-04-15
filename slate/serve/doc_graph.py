from __future__ import annotations

from typing import Any, Dict, Optional

# Optional Ray Serve graph builder for doc-AI pipeline.
# This is a scaffold; the production version would add batching, caching, and artifact emission.

try:
    from ray import serve  # type: ignore
except Exception:  # pragma: no cover
    serve = None

from slate.ingest.tika_reader import read_to_text
from slate.ocr.ocr_ensemble import OCREnsemble
from slate.nlp.spacy_pipe import make_spacy


def build_local_doc_pipeline(ocr_engines=None, spacy_model: str = "en_core_web_sm"):
    """Return a callable that processes a document path into structured text.

    Local mode (no Ray) is useful for unit tests and debugging.
    """
    ocr = OCREnsemble(engines=ocr_engines or ["tesseract"])
    nlp = make_spacy(spacy_model)

    def run(path: str) -> Dict[str, Any]:
        # Best-effort: if tika fails, we fall back to OCR only.
        text = ""
        try:
            text = read_to_text(path)
        except Exception:
            text = ""

        ocr_text = ""
        try:
            ocr_text = ocr.run(path).text  # NOTE: expects image; for PDFs, integrate a renderer first.
        except Exception:
            ocr_text = ""

        merged = (text + "\n" + ocr_text).strip()
        doc = nlp(merged) if merged else None

        return {
            "text": merged,
            "spacy": {
                "ents": [{"text": e.text, "label": e.label_, "start": e.start_char, "end": e.end_char} for e in (doc.ents if doc else [])]
            },
        }

    return run


def build_serve_deployment():
    """Create a Ray Serve deployment for doc processing."""
    if not serve:
        raise RuntimeError("ray[serve] not installed")

    @serve.deployment(name="DocAI", num_replicas=1, route_prefix="/docai")
    class DocAI:
        def __init__(self):
            self.pipe = build_local_doc_pipeline()

        async def __call__(self, request):
            body = await request.json()
            path = body.get("path", "")
            return self.pipe(path)

    return DocAI
