from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from google.cloud import vision


@dataclass
class OcrLine:
    text: str
    confidence: float
    bounding_box: list[tuple[int, int]]


@dataclass
class OcrResult:
    full_text: str
    lines: list[OcrLine]
    engine: str
    elapsed_ms: int


def _points(vertices) -> list[tuple[int, int]]:
    return [(vertex.x or 0, vertex.y or 0) for vertex in vertices]


def document_ocr(image_path: str | Path) -> OcrResult:
    started = time.perf_counter()

    image_bytes = Path(image_path).read_bytes()
    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=image_bytes)

    response = client.document_text_detection(
        image=image,
        image_context=vision.ImageContext(language_hints=["en"]),
    )

    if response.error.message:
        raise RuntimeError(
            f"Google Vision OCR failed: {response.error.message}"
        )

    annotation = response.full_text_annotation
    full_text = annotation.text or ""
    lines: list[OcrLine] = []

    for page in annotation.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                words: list[str] = []
                confidences: list[float] = []
                vertices: list[tuple[int, int]] = []

                for word in paragraph.words:
                    word_text = "".join(
                        symbol.text for symbol in word.symbols
                    ).strip()

                    if word_text:
                        words.append(word_text)

                    if word.confidence is not None:
                        confidences.append(float(word.confidence))

                    vertices.extend(_points(word.bounding_box.vertices))

                line = " ".join(words).strip()

                if line:
                    lines.append(
                        OcrLine(
                            text=line,
                            confidence=(
                                sum(confidences) / len(confidences)
                                if confidences
                                else 0.0
                            ),
                            bounding_box=vertices,
                        )
                    )

    elapsed_ms = int((time.perf_counter() - started) * 1000)

    return OcrResult(
        full_text=full_text,
        lines=lines,
        engine="google_vision",
        elapsed_ms=elapsed_ms,
    )