from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import RomanNumeralAnalysisResult


class RomanNumeralAnalyzer(ABC):
    name: str = "base"
    version: str = "0.0"
    requires_external_model: bool = False

    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def analyze_score(self, score, score_id: str, **kwargs) -> RomanNumeralAnalysisResult:
        raise NotImplementedError
