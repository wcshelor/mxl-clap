from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class RomanNumeralEvent:
    score_id: str
    backend_name: str
    backend_version: str
    onset_quarter: float
    duration_quarter: float
    measure_number: int | None = None
    beat: float | None = None
    local_key: str | None = None
    global_key: str | None = None
    roman_numeral: str | None = None
    figure: str | None = None
    chord_root: str | None = None
    bass_note: str | None = None
    inversion: str | None = None
    function_label: str | None = None
    confidence: float | None = None
    raw_label: str | None = None
    warning_flags: tuple[str, ...] = ()
    pitch_classes: tuple[int, ...] = ()
    root_pitch_class: int | None = None
    bass_pitch_class: int | None = None
    is_approximate: bool = True

    def to_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["warning_flags"] = ";".join(self.warning_flags)
        row["pitch_classes"] = ";".join(str(value) for value in self.pitch_classes)
        return row


@dataclass(slots=True)
class RomanNumeralAnalysisResult:
    score_id: str
    backend_name: str
    backend_version: str
    success: bool
    warnings: list[str] = field(default_factory=list)
    events: list[RomanNumeralEvent] = field(default_factory=list)
    backend_available: bool = True
    global_key: str | None = None
    local_key_labels: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_event_rows(self) -> list[dict[str, Any]]:
        return [event.to_row() for event in self.events]
