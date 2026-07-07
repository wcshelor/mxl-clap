from __future__ import annotations

import re
from dataclasses import dataclass, field

from music21 import chord, key as key_module, roman, stream


_ROMAN_BASE_RE = re.compile(r"^[#b+-]*([IViv]+)")


@dataclass(slots=True)
class RomanNumeralEvent:
    offset: float
    duration: float
    measure_number: int | None
    figure: str
    common_name: str
    local_key_label: str
    function_category: str
    pitch_classes: tuple[int, ...]
    root_pitch_class: int | None
    is_secondary: bool
    is_applied_dominant: bool
    is_modal_mixture: bool
    is_diminished: bool
    is_seventh: bool
    is_chromatic: bool


@dataclass(slots=True)
class RomanNumeralAnalysisResult:
    backend_name: str
    backend_available: bool
    events: list[RomanNumeralEvent] = field(default_factory=list)
    global_key_label: str = ""
    global_key_pitch_classes: tuple[int, ...] = ()
    measure_key_labels: dict[int, str] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()


def _bool_value(value) -> bool:
    if callable(value):
        try:
            return bool(value())
        except Exception:
            return False
    if value is None:
        return False
    return bool(value)


def _safe_key_label(key_obj) -> str:
    if key_obj is None:
        return ""
    tonic = getattr(key_obj, "tonic", None)
    tonic_name = getattr(tonic, "name", None) or getattr(tonic, "nameWithOctave", None) or str(tonic or "")
    mode = str(getattr(key_obj, "mode", "") or "").strip()
    if tonic_name and mode:
        return f"{tonic_name} {mode}"
    return tonic_name or mode


def _safe_key_pitch_classes(key_obj) -> set[int]:
    pitch_classes: set[int] = set()
    if key_obj is None:
        return pitch_classes

    tonic = getattr(key_obj, "tonic", None)
    tonic_pitch_class = getattr(tonic, "pitchClass", None)
    if tonic_pitch_class is None:
        try:
            tonic_pitch_class = int(getattr(key_obj, "tonicPitchClass"))
        except Exception:
            tonic_pitch_class = None
    if tonic_pitch_class is None:
        return pitch_classes

    mode = str(getattr(key_obj, "mode", "major")).lower()
    if mode.startswith("minor"):
        intervals = (0, 2, 3, 5, 7, 8, 10)
    else:
        intervals = (0, 2, 4, 5, 7, 9, 11)
    return {(int(tonic_pitch_class) + interval) % 12 for interval in intervals}


def _analyze_key(stream_obj):
    try:
        key_obj = stream_obj.analyze("key")
    except Exception:
        key_obj = None
    if key_obj is None:
        try:
            key_obj = key_module.Key("C")
        except Exception:
            return None
    return key_obj


def _score_analysis_source(score):
    parts = list(getattr(score, "parts", []))
    if parts:
        return parts[0]
    return score


def _measure_key_map(analysis_source, global_key) -> dict[int, object]:
    measure_key_map: dict[int, object] = {}
    try:
        measures = list(analysis_source.getElementsByClass(stream.Measure))
    except Exception:
        measures = []

    for measure in measures:
        measure_number = getattr(measure, "number", None)
        if measure_number is None:
            continue
        try:
            local_key = measure.analyze("key")
        except Exception:
            local_key = global_key
        if local_key is None:
            local_key = global_key
        if local_key is not None:
            try:
                measure_key_map[int(measure_number)] = local_key
            except (TypeError, ValueError):
                continue
    return measure_key_map


def _roman_base(figure: str) -> str:
    match = _ROMAN_BASE_RE.match(figure.replace(" ", ""))
    if not match:
        return ""
    return match.group(1)


def _function_category(figure: str) -> str:
    base = _roman_base(figure).upper()
    if not base:
        return "other"
    if base.startswith("V") and not base.startswith("VI") and not base.startswith("VII"):
        return "dominant"
    if base.startswith("II") or base.startswith("IV"):
        return "predominant"
    if base.startswith("I") and not base.startswith("II") and not base.startswith("IV") and not base.startswith("VI") and not base.startswith("VII"):
        return "tonic"
    return "other"


def _roman_to_bool(value) -> bool:
    if callable(value):
        try:
            return bool(value())
        except Exception:
            return False
    if value is None:
        return False
    return bool(value)


def _is_modal_mixture(rn, figure: str, key_obj) -> bool:
    borrowed = getattr(rn, "isBorrowed", None)
    if borrowed is not None:
        return _roman_to_bool(borrowed)

    mode = str(getattr(key_obj, "mode", "major")).lower()
    lower = figure.lower()
    if mode.startswith("major"):
        return any(token in lower for token in ("iv", "biii", "bvi", "bvii"))
    return any(token in lower for token in ("iv", "vi", "vii"))


def _is_diminished(rn, figure: str) -> bool:
    if _bool_value(getattr(rn, "isDiminishedTriad", None)):
        return True
    if _bool_value(getattr(rn, "isDiminishedSeventh", None)):
        return True
    lower = figure.lower()
    return "dim" in lower or "o" in lower


def _is_seventh(rn, figure: str, pitches) -> bool:
    if _bool_value(getattr(rn, "isSeventh", None)):
        return True
    if len(getattr(rn, "pitches", pitches)) >= 4:
        return True
    return "7" in figure


def analyze_roman_numerals(score) -> RomanNumeralAnalysisResult:
    warnings: list[str] = []
    analysis_source = _score_analysis_source(score)
    global_key = _analyze_key(score)
    if global_key is None:
        warnings.append("Failed to infer a global key; falling back to C major.")
        try:
            global_key = key_module.Key("C")
        except Exception:
            return RomanNumeralAnalysisResult(
                backend_name="music21",
                backend_available=False,
                global_key_label="",
                global_key_pitch_classes=(),
                warnings=tuple(warnings),
            )

    measure_key_map = _measure_key_map(analysis_source, global_key)
    try:
        chordified = score.chordify()
    except Exception as exc:
        warnings.append(f"Chordification failed: {exc}")
        return RomanNumeralAnalysisResult(
            backend_name="music21",
            backend_available=False,
            global_key_label=_safe_key_label(global_key),
            global_key_pitch_classes=tuple(sorted(_safe_key_pitch_classes(global_key))),
            measure_key_labels={measure_number: _safe_key_label(key_obj) for measure_number, key_obj in measure_key_map.items()},
            warnings=tuple(warnings),
        )

    events: list[RomanNumeralEvent] = []
    for element in chordified.recurse().getElementsByClass(chord.Chord):
        pitch_classes = tuple(sorted({int(p.pitchClass) for p in getattr(element, "pitches", [])}))
        if not pitch_classes:
            continue

        measure_number = getattr(element, "measureNumber", None)
        try:
            measure_number = int(measure_number) if measure_number is not None else None
        except (TypeError, ValueError):
            measure_number = None
        local_key = measure_key_map.get(measure_number, global_key)
        if local_key is None:
            local_key = global_key
        try:
            rn = roman.romanNumeralFromChord(element, local_key)
        except Exception as exc:
            warnings.append(f"Roman numeral analysis failed at offset {getattr(element, 'offset', 0.0)}: {exc}")
            continue

        figure = str(getattr(rn, "figure", "") or "")
        common_name = str(getattr(element, "commonName", "") or "")
        root_pitch_class = None
        try:
            root_obj = rn.root()
            root_pitch_class = getattr(root_obj, "pitchClass", None)
        except Exception:
            root_pitch_class = None

        local_key_pitch_classes = _safe_key_pitch_classes(local_key)
        is_chromatic = any(pitch_class not in local_key_pitch_classes for pitch_class in pitch_classes) if local_key_pitch_classes else False
        is_secondary = "/" in figure or getattr(rn, "secondaryRomanNumeral", None) is not None
        is_applied_dominant = is_secondary and _function_category(figure) == "dominant"
        is_modal_mixture = _is_modal_mixture(rn, figure, local_key)
        is_diminished = _is_diminished(rn, figure)
        is_seventh = _is_seventh(rn, figure, getattr(element, "pitches", ()))

        events.append(
            RomanNumeralEvent(
                offset=float(getattr(element, "offset", 0.0) or 0.0),
                duration=float(getattr(element, "quarterLength", 0.0) or 0.0),
                measure_number=measure_number,
                figure=figure,
                common_name=common_name,
                local_key_label=_safe_key_label(local_key),
                function_category=_function_category(figure),
                pitch_classes=pitch_classes,
                root_pitch_class=root_pitch_class,
                is_secondary=is_secondary,
                is_applied_dominant=is_applied_dominant,
                is_modal_mixture=is_modal_mixture,
                is_diminished=is_diminished,
                is_seventh=is_seventh,
                is_chromatic=is_chromatic,
            )
        )

    return RomanNumeralAnalysisResult(
        backend_name="music21",
        backend_available=True,
        events=events,
        global_key_label=_safe_key_label(global_key),
        global_key_pitch_classes=tuple(sorted(_safe_key_pitch_classes(global_key))),
        measure_key_labels={measure_number: _safe_key_label(key_obj) for measure_number, key_obj in measure_key_map.items()},
        warnings=tuple(warnings),
    )
