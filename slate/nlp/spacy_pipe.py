from __future__ import annotations

from typing import Iterable, List, Optional


def make_spacy(model: str = "en_core_web_sm", enable: Optional[Iterable[str]] = None):
    """Create a spaCy pipeline.

    This is an optional dependency. The default `en_core_web_sm` model must be installed separately.
    """
    try:
        import spacy  # type: ignore
    except Exception as e:
        raise RuntimeError("spacy not installed") from e

    nlp = spacy.load(model)
    if enable is not None:
        # disable everything except enable
        enable = set(enable)
        for pipe in list(nlp.pipe_names):
            if pipe not in enable:
                nlp.disable_pipe(pipe)
    return nlp
