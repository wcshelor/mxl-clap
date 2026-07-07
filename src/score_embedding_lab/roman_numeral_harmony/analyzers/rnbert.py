from __future__ import annotations

from importlib.util import find_spec

from ..models import RomanNumeralAnalysisResult
from .base import RomanNumeralAnalyzer


class RNBertRomanNumeralAnalyzer(RomanNumeralAnalyzer):
    name = "rnbert"
    version = "0.0-stub"
    requires_external_model = True

    def __init__(self, model_name: str | None = None, checkpoint_path: str | None = None) -> None:
        self.model_name = model_name
        self.checkpoint_path = checkpoint_path

    def is_available(self) -> bool:
        return find_spec("transformers") is not None or find_spec("torch") is not None

    def analyze_score(self, score, score_id: str, **kwargs) -> RomanNumeralAnalysisResult:
        warnings = [
            "RNBert backend is a stub in this repository.",
            "Install the optional model stack and implement tokenization/inference before relying on this backend.",
        ]
        if self.model_name:
            warnings.append(f"Configured model_name={self.model_name}")
        if self.checkpoint_path:
            warnings.append(f"Configured checkpoint_path={self.checkpoint_path}")
        return RomanNumeralAnalysisResult(
            score_id=score_id,
            backend_name=self.name,
            backend_version=self.version,
            success=False,
            warnings=warnings,
            events=[],
            backend_available=self.is_available(),
            metadata={
                "analysis_method": "unavailable_stub",
                "model_name": self.model_name,
                "checkpoint_path": self.checkpoint_path,
                "next_step": "implement MusicBERT/RNBert inference and map logits to Roman numeral events",
            },
        )
