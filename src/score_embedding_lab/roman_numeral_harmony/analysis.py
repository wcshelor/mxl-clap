from __future__ import annotations

from .analyzers import Music21LightRomanNumeralAnalyzer, RNBertRomanNumeralAnalyzer, RomanNumeralAnalyzer
from .models import RomanNumeralAnalysisResult


def analyzer_for_name(name: str, *, model_name: str | None = None, checkpoint_path: str | None = None) -> RomanNumeralAnalyzer:
    normalized = (name or "").strip().lower()
    if normalized in {"music21", "music21_light", "light", ""}:
        return Music21LightRomanNumeralAnalyzer()
    if normalized in {"rnbert", "musicbert", "huggingface"}:
        return RNBertRomanNumeralAnalyzer(model_name=model_name, checkpoint_path=checkpoint_path)
    raise ValueError(f"Unknown Roman numeral analyzer backend: {name}")


def run_score_analysis(score, score_id: str, backend: str = "music21_light", **kwargs) -> RomanNumeralAnalysisResult:
    analyzer = analyzer_for_name(
        backend,
        model_name=kwargs.get("model_name"),
        checkpoint_path=kwargs.get("checkpoint_path"),
    )
    return analyzer.analyze_score(score, score_id=score_id, **kwargs)
