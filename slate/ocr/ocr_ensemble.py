from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class OCRResult:
    text: str
    engine: str
    confidence: float = 0.0


class OCREnsemble:
    """OCR ensemble scaffold.

    Intended design:
    - try multiple engines
    - choose best by confidence/heuristics
    - optionally return per-block text with coordinates

    Current implementation:
    - sequentially tries engines until one succeeds
    """

    def __init__(self, engines: Optional[List[str]] = None, lang: str = "en"):
        self.engines = engines or ["tesseract"]
        self.lang = lang

    def run(self, image_path: str) -> OCRResult:
        last_err: Optional[Exception] = None
        for engine in self.engines:
            try:
                if engine == "tesseract":
                    return self._tesseract(image_path)
                if engine == "easyocr":
                    return self._easyocr(image_path)
                raise ValueError(f"unknown engine: {engine}")
            except Exception as e:
                last_err = e
                continue
        raise RuntimeError(f"all OCR engines failed; last error: {last_err}")

    def _tesseract(self, image_path: str) -> OCRResult:
        try:
            from PIL import Image  # type: ignore
            import pytesseract  # type: ignore
        except Exception as e:
            raise RuntimeError("pytesseract + pillow required for tesseract OCR") from e

        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang=self.lang)
        return OCRResult(text=text.strip(), engine="tesseract", confidence=0.0)

    def _easyocr(self, image_path: str) -> OCRResult:
        try:
            import easyocr  # type: ignore
        except Exception as e:
            raise RuntimeError("easyocr required for easyocr OCR") from e

        reader = easyocr.Reader([self.lang])
        results = reader.readtext(image_path)
        # results: [(bbox, text, conf), ...]
        text = "\n".join([r[1] for r in results])
        conf = float(sum([r[2] for r in results]) / max(1, len(results)))
        return OCRResult(text=text.strip(), engine="easyocr", confidence=conf)
