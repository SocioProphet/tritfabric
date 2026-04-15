from __future__ import annotations

from typing import Any, Dict, List


class RebelRelationExtractor:
    """REBEL relation extraction scaffold.

    REBEL is commonly served via Hugging Face Transformers (seq2seq).
    This wrapper is intentionally light; production deployments should use batching + caching.
    """

    def __init__(self, model_id: str = "Babelscape/rebel-large"):
        self.model_id = model_id
        self._pipe = None

    def _load(self):
        try:
            from transformers import pipeline  # type: ignore
        except Exception as e:
            raise RuntimeError("transformers not installed") from e
        self._pipe = pipeline("text2text-generation", model=self.model_id)

    def extract(self, text: str, max_length: int = 256) -> List[Dict[str, Any]]:
        if self._pipe is None:
            self._load()
        assert self._pipe is not None
        out = self._pipe(text, max_length=max_length)
        return list(out)
