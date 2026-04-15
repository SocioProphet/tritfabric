from __future__ import annotations

from typing import Dict, List


class GLiNERNER:
    """GLiNER NER scaffold.

    GLiNER is a promptable NER model; we keep this wrapper here as a hook point.
    """

    def __init__(self, model_id: str = "urchade/gliner_small-v2.1"):
        self.model_id = model_id
        self._model = None

    def _load(self):
        try:
            from gliner import GLiNER  # type: ignore
        except Exception as e:
            raise RuntimeError("gliner not installed; pip install gliner") from e
        self._model = GLiNER.from_pretrained(self.model_id)

    def predict(self, text: str, labels: List[str]) -> List[Dict]:
        if self._model is None:
            self._load()
        assert self._model is not None
        ents = self._model.predict_entities(text, labels)
        return list(ents)
