from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from math import log2
from statistics import mean

try:  # pragma: no cover - optional dependency
    from music21 import chord, key as key_module, roman, stream
    MUSIC21_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    chord = None
    key_module = None
    roman = None
    stream = None
    MUSIC21_AVAILABLE = False

from ..models import RomanNumeralAnalysisResult, RomanNumeralEvent
from .base import RomanNumeralAnalyzer


def _safe_label(key_obj) -> str | None:
    if key_obj is None:
        return None
    try:
        tonic = getattr(key_obj, "tonic", None)
        tonic_name = getattr(tonic, "name", None) or str(tonic or "")
        mode = str(getattr(key_obj, "mode", "") or "").strip()
        if tonic_name and mode:
            return f"{tonic_name} {mode}"
        return tonic_name or mode or None
    except Exception:
        return None


def _safe_pitch_class_set(key_obj) -> set[int]:
    if key_obj is None:
        return set()
    tonic = getattr(key_obj, "tonic", None)
    tonic_pc = getattr(tonic, "pitchClass", None)
    if tonic_pc is None:
        return set()
    mode = str(getattr(key_obj, "mode", "major")).lower()
    intervals = (0, 2, 3, 5, 7, 8, 10) if mode.startswith("minor") else (0, 2, 4, 5, 7, 9, 11)
    return {(int(tonic_pc) + interval) % 12 for interval in intervals}


def _safe_key(stream_obj) -> object | None:
    try:
        return stream_obj.analyze("key")
    except Exception:
        try:
            return key_module.Key("C")
        except Exception:
            return None


def _measure_key_map(score, global_key) -> dict[int, object]:
    measure_key_map: dict[int, object] = {}
    try:
        measures = list(score.recurse().getElementsByClass(stream.Measure))
    except Exception:
        measures = []
    for measure in measures:
        number = getattr(measure, "number", None)
        try:
            number = int(number)
        except Exception:
            continue
        try:
            local_key = measure.analyze("key")
        except Exception:
            local_key = global_key
        if local_key is not None:
            measure_key_map[number] = local_key
    return measure_key_map


def _function_label(figure: str | None) -> str:
    if not figure:
        return "unknown"
    lowered = figure.lower()
    if any(token in lowered for token in ("ger", "fr", "it", "+6", "n6", "neap")):
        return "chromatic"
    if "/" in figure or "secondary" in lowered or "applied" in lowered:
        return "secondary"
    if lowered.startswith("v"):
        return "dominant"
    if lowered.startswith("ii") or lowered.startswith("iv") or lowered.startswith("vi"):
        return "predominant"
    if lowered.startswith("i"):
        return "tonic"
    return "other"


def _is_diminished(figure: str | None, rn) -> bool:
    if figure and ("dim" in figure.lower() or "o" in figure.lower()):
        return True
    for attr in ("isDiminishedTriad", "isDiminishedSeventh"):
        value = getattr(rn, attr, None)
        if callable(value):
            try:
                if bool(value()):
                    return True
            except Exception:
                pass
    return False


def _confidence(value: object | None, fallback: float = 0.75) -> float:
    if value is None:
        return fallback
    try:
        return float(value)
    except Exception:
        return fallback


class Music21LightRomanNumeralAnalyzer(RomanNumeralAnalyzer):
    name = "music21_light"
    version = "0.1"
    requires_external_model = False

    def is_available(self) -> bool:
        return MUSIC21_AVAILABLE

    def analyze_score(self, score, score_id: str, **kwargs) -> RomanNumeralAnalysisResult:
        if not MUSIC21_AVAILABLE:
            return RomanNumeralAnalysisResult(
                score_id=score_id,
                backend_name=self.name,
                backend_version=self.version,
                success=False,
                warnings=["music21 is not installed; the lightweight Roman numeral backend is unavailable."],
                events=[],
                backend_available=False,
                global_key=None,
                local_key_labels=[],
                metadata={"analysis_method": "unavailable_missing_music21"},
            )
        warnings: list[str] = []
        global_key = _safe_key(score)
        if global_key is None:
            warnings.append("Failed to infer a global key; defaulted to C major.")
            global_key = key_module.Key("C")
        global_key_label = _safe_label(global_key)
        measure_key_map = _measure_key_map(score, global_key)
        try:
            chordified = score.chordify()
        except Exception as exc:
            return RomanNumeralAnalysisResult(
                score_id=score_id,
                backend_name=self.name,
                backend_version=self.version,
                success=False,
                warnings=[f"Chordification failed: {exc}"],
                events=[],
                backend_available=False,
                global_key=global_key_label,
                local_key_labels=sorted({_safe_label(key_obj) for key_obj in measure_key_map.values() if _safe_label(key_obj)}),
            )

        events: list[RomanNumeralEvent] = []
        local_key_labels: set[str] = set()
        for element in chordified.recurse().getElementsByClass(chord.Chord):
            pitches = tuple(sorted({int(p.pitchClass) for p in getattr(element, "pitches", [])}))
            if not pitches:
                continue
            onset = float(getattr(element, "offset", 0.0))
            duration = float(getattr(element, "quarterLength", 0.0))
            measure_number = getattr(element, "measureNumber", None)
            try:
                measure_number = int(measure_number) if measure_number is not None else None
            except Exception:
                measure_number = None
            beat = None
            try:
                beat = float(getattr(element, "beat", None))
            except Exception:
                beat = None
            local_key = measure_key_map.get(measure_number, global_key)
            local_key_label = _safe_label(local_key)
            if local_key_label:
                local_key_labels.add(local_key_label)
            try:
                rn = roman.romanNumeralFromChord(element, local_key)
                figure = getattr(rn, "figure", None) or str(rn)
                root = getattr(rn, "root", None)
                bass = getattr(rn, "bass", None)
                chord_root = getattr(root, "name", None) if root is not None else None
                bass_note = getattr(bass, "name", None) if bass is not None else None
                root_pc = getattr(root, "pitchClass", None) if root is not None else None
                bass_pc = getattr(bass, "pitchClass", None) if bass is not None else None
                inversion = None
                try:
                    inversion = str(rn.inversion())
                except Exception:
                    inversion = None
                raw_label = str(rn)
                confidence = _confidence(getattr(rn, "confidence", None), fallback=0.9)
            except Exception as exc:
                warnings.append(f"Roman numeral analysis failed at offset {onset:.3f}: {exc}")
                figure = getattr(element, "commonName", None) or "unknown"
                chord_root_obj = getattr(element, "root", None)
                bass_obj = getattr(element, "bass", None)
                chord_root = getattr(chord_root_obj, "name", None) if chord_root_obj is not None else None
                bass_note = getattr(bass_obj, "name", None) if bass_obj is not None else None
                root_pc = getattr(chord_root_obj, "pitchClass", None) if chord_root_obj is not None else None
                bass_pc = getattr(bass_obj, "pitchClass", None) if bass_obj is not None else None
                inversion = None
                raw_label = figure
                confidence = 0.25
            events.append(
                RomanNumeralEvent(
                    score_id=score_id,
                    backend_name=self.name,
                    backend_version=self.version,
                    onset_quarter=onset,
                    duration_quarter=duration,
                    measure_number=measure_number,
                    beat=beat,
                    local_key=local_key_label,
                    global_key=global_key_label,
                    roman_numeral=figure,
                    figure=figure,
                    chord_root=chord_root,
                    bass_note=bass_note,
                    inversion=inversion,
                    function_label=_function_label(figure),
                    confidence=confidence,
                    raw_label=raw_label,
                    warning_flags=("approximate_music21_light",) + (("analysis_fallback",) if confidence < 0.5 else ()),
                    pitch_classes=pitches,
                    root_pitch_class=root_pc if isinstance(root_pc, int) else None,
                    bass_pitch_class=bass_pc if isinstance(bass_pc, int) else None,
                    is_approximate=True,
                )
            )

        return RomanNumeralAnalysisResult(
            score_id=score_id,
            backend_name=self.name,
            backend_version=self.version,
            success=bool(events),
            warnings=warnings,
            events=events,
            backend_available=True,
            global_key=global_key_label,
            local_key_labels=sorted(label for label in local_key_labels if label),
            metadata={
                "analysis_method": "music21.chordify + romanNumeralFromChord",
                "approximate": True,
                "pitch_class_set": sorted(_safe_pitch_class_set(global_key)),
            },
        )
