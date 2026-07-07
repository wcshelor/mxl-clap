from __future__ import annotations

from bisect import bisect_right
from collections import Counter, defaultdict
from dataclasses import dataclass
from math import log
from statistics import mean, median

from music21 import chord, note

from .roman_numeral_backend import RomanNumeralAnalysisResult, analyze_roman_numerals
from .symbolic_features import _collect_note_events, _entropy_from_counts, _group_events_by_onset, _highest_time


@dataclass(slots=True)
class HarmonyLightAnalysis:
    features: dict[str, float]
    chordified_events: list[dict[str, object]]
    diatonic_pitch_classes: set[int]


def _safe_float(value, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return float(numerator) / float(denominator)


def _safe_variance(values: list[float]) -> float:
    if not values:
        return 0.0
    mean_value = float(mean(values))
    return float(mean((value - mean_value) ** 2 for value in values))


def _infer_diatonic_pitch_classes(score) -> set[int]:
    try:
        inferred_key = score.analyze("key")
    except Exception:
        return set()

    pitch_classes: set[int] = set()
    for source_name in ("getScale", "scale"):
        source = getattr(inferred_key, source_name, None)
        if callable(source):
            try:
                source = source()
            except Exception:
                source = None
        if source is None:
            continue
        pitch_from_degree = getattr(source, "pitchFromDegree", None)
        if not callable(pitch_from_degree):
            continue
        for degree in range(1, 8):
            try:
                pitch_obj = pitch_from_degree(degree)
            except Exception:
                continue
            pitch_class = getattr(pitch_obj, "pitchClass", None)
            if pitch_class is not None:
                pitch_classes.add(int(pitch_class))
        if pitch_classes:
            return pitch_classes

    tonic = getattr(inferred_key, "tonic", None)
    mode = str(getattr(inferred_key, "mode", "major")).lower()
    tonic_pitch_class = getattr(tonic, "pitchClass", None)
    if tonic_pitch_class is None:
        return set()

    if mode.startswith("minor"):
        intervals = (0, 2, 3, 5, 7, 8, 10)
    else:
        intervals = (0, 2, 4, 5, 7, 9, 11)
    return {(int(tonic_pitch_class) + interval) % 12 for interval in intervals}


def _measure_groups(events: list[dict]) -> dict[int, list[dict]]:
    grouped: dict[int, list[dict]] = defaultdict(list)
    for event in events:
        measure_number = event.get("measure_number")
        if measure_number is None:
            continue
        try:
            grouped[int(measure_number)].append(event)
        except (TypeError, ValueError):
            continue
    return grouped


def _ordered_measure_groups(events: list[dict]) -> list[tuple[int, list[dict]]]:
    grouped = _measure_groups(events)
    return [(measure_number, grouped[measure_number]) for measure_number in sorted(grouped)]


def _measure_density_values(events: list[dict]) -> list[float]:
    densities: list[float] = []
    for _, measure_events in _ordered_measure_groups(events):
        if not measure_events:
            continue
        densities.append(float(sum(int(event["pitch_count"]) for event in measure_events)))
    return densities


def _measure_rhythm_patterns(events: list[dict]) -> list[tuple[float, ...]]:
    patterns: list[tuple[float, ...]] = []
    for _, measure_events in _ordered_measure_groups(events):
        if not measure_events:
            continue
        ordered = sorted(
            measure_events,
            key=lambda event: (float(event.get("offset", 0.0)), float(event.get("duration", 0.0))),
        )
        pattern = tuple(round(float(event.get("duration", 0.0)), 3) for event in ordered)
        if pattern:
            patterns.append(pattern)
    return patterns


def _measure_rest_punctuation_ratio(score, measure_numbers: set[int]) -> float:
    if not measure_numbers:
        return 0.0

    rest_measure_numbers: set[int] = set()
    try:
        rest_stream = score.recurse().getElementsByClass(note.Rest)
    except Exception:
        rest_stream = []

    for rest in rest_stream:
        measure_number = getattr(rest, "measureNumber", None)
        if measure_number is None:
            continue
        try:
            rest_measure_numbers.add(int(measure_number))
        except (TypeError, ValueError):
            continue
    if not rest_measure_numbers:
        return 0.0
    return _safe_ratio(len(rest_measure_numbers & measure_numbers), len(measure_numbers))


def _measure_end_long_note_ratio(events: list[dict]) -> float:
    ordered_groups = _ordered_measure_groups(events)
    if not ordered_groups:
        return 0.0

    long_note_measures = 0
    for _, measure_events in ordered_groups:
        ordered = sorted(
            measure_events,
            key=lambda event: (float(event.get("offset", 0.0)), float(event.get("duration", 0.0))),
        )
        if not ordered:
            continue
        if float(ordered[-1].get("duration", 0.0)) >= 1.0:
            long_note_measures += 1
    return _safe_ratio(long_note_measures, len(ordered_groups))


def _partwise_note_events(score) -> list[list[dict]]:
    parts = list(getattr(score, "parts", []))
    if len(parts) < 2:
        return [_collect_note_events(score)]
    return [_collect_note_events(part) for part in parts]


def _pitch_values(events: list[dict]) -> list[int]:
    return [pitch for event in events for pitch in event.get("pitches", [])]


def _mean_pitch(events: list[dict]) -> float:
    values = _pitch_values(events)
    return float(mean(values)) if values else 0.0


def _selected_lower_material_events(score, events: list[dict]) -> list[dict]:
    part_events = _partwise_note_events(score)
    if len(part_events) >= 2:
        scored_parts = []
        for part in part_events:
            values = _pitch_values(part)
            if not values:
                continue
            scored_parts.append((_mean_pitch(part), part))
        if scored_parts:
            return min(scored_parts, key=lambda item: item[0])[1]

    if not events:
        return []

    melodic_values = [int(event["melodic_pitch"]) for event in events if event.get("melodic_pitch") is not None]
    if not melodic_values:
        return []
    threshold = float(median(melodic_values))
    return [event for event in events if event.get("melodic_pitch") is not None and float(event["melodic_pitch"]) <= threshold]


def _monotonic_arpeggiation_windows(events: list[dict]) -> float:
    ordered = sorted(
        [event for event in events if event.get("melodic_pitch") is not None],
        key=lambda event: (float(event.get("offset", 0.0)), float(event.get("melodic_pitch", 0.0))),
    )
    if len(ordered) < 3:
        return 0.0

    total_windows = 0
    matching_windows = 0
    for index in range(len(ordered) - 2):
        a, b, c = ordered[index : index + 3]
        offsets = [float(a.get("offset", 0.0)), float(b.get("offset", 0.0)), float(c.get("offset", 0.0))]
        pitches = [float(a["melodic_pitch"]), float(b["melodic_pitch"]), float(c["melodic_pitch"])]
        gap_one = offsets[1] - offsets[0]
        gap_two = offsets[2] - offsets[1]
        total_windows += 1
        if gap_one > 1.0 or gap_two > 1.0:
            continue
        if (pitches[0] < pitches[1] < pitches[2] or pitches[0] > pitches[1] > pitches[2]) and max(pitches) - min(pitches) >= 5:
            matching_windows += 1
    return _safe_ratio(matching_windows, total_windows)


def _is_strong_beat(event: dict) -> bool:
    beat_strength = event.get("beat_strength")
    if beat_strength is not None:
        try:
            if float(beat_strength) >= 0.5:
                return True
        except (TypeError, ValueError):
            pass

    beat = event.get("beat")
    try:
        beat_value = float(beat)
    except (TypeError, ValueError):
        return False

    rounded = int(round(beat_value))
    return abs(beat_value - rounded) <= 0.25 and 1 <= rounded <= 4


def _is_triad(chord_obj) -> bool:
    checker = getattr(chord_obj, "isTriad", None)
    if callable(checker):
        try:
            return bool(checker())
        except Exception:
            pass
    common_name = str(getattr(chord_obj, "commonName", "")).lower()
    return "triad" in common_name


def _is_seventh_chord(chord_obj) -> bool:
    checker = getattr(chord_obj, "isSeventh", None)
    if callable(checker):
        try:
            return bool(checker())
        except Exception:
            pass
    common_name = str(getattr(chord_obj, "commonName", "")).lower()
    return "seventh" in common_name


def _is_consonant_verticality(chord_obj) -> bool:
    checker = getattr(chord_obj, "isConsonant", None)
    if callable(checker):
        try:
            return bool(checker())
        except Exception:
            pass

    pitch_classes = sorted({int(p.pitchClass) for p in getattr(chord_obj, "pitches", [])})
    if len(pitch_classes) < 2:
        return True
    intervals = {
        (upper - lower) % 12
        for index, lower in enumerate(pitch_classes)
        for upper in pitch_classes[index + 1 :]
    }
    return 1 not in intervals and 6 not in intervals


def _harmonic_event_records(score) -> HarmonyLightAnalysis:
    diatonic_pitch_classes = _infer_diatonic_pitch_classes(score)
    try:
        chordified = score.chordify()
    except Exception:
        return HarmonyLightAnalysis(
            features={
                "experimental__harmony_light__chordified_event_count": 0.0,
                "experimental__harmony_light__triad_ratio": 0.0,
                "experimental__harmony_light__seventh_chord_ratio": 0.0,
                "experimental__harmony_light__dissonant_verticality_ratio": 0.0,
                "experimental__harmony_light__chord_common_name_entropy": 0.0,
                "experimental__harmony_light__harmonic_rhythm_mean": 0.0,
                "experimental__harmony_light__harmonic_rhythm_variance": 0.0,
                "experimental__harmony_light__vertical_chromaticity_ratio": 0.0,
            },
            chordified_events=[],
            diatonic_pitch_classes=diatonic_pitch_classes,
        )

    chordified_events: list[dict[str, object]] = []
    for element in chordified.recurse().getElementsByClass(chord.Chord):
        pitches = [int(p.midi) for p in getattr(element, "pitches", [])]
        if not pitches:
            continue
        pitch_classes = tuple(sorted({pitch % 12 for pitch in pitches}))
        chordified_events.append(
            {
                "offset": _safe_float(getattr(element, "offset", 0.0)),
                "duration": _safe_float(getattr(element, "quarterLength", 0.0)),
                "measure_number": getattr(element, "measureNumber", None),
                "pitches": pitches,
                "pitch_classes": pitch_classes,
                "common_name": str(getattr(element, "commonName", "") or "other"),
                "is_triad": _is_triad(element),
                "is_seventh": _is_seventh_chord(element),
                "is_consonant": _is_consonant_verticality(element),
            }
        )

    if not chordified_events:
        return HarmonyLightAnalysis(
            features={
                "experimental__harmony_light__chordified_event_count": 0.0,
                "experimental__harmony_light__triad_ratio": 0.0,
                "experimental__harmony_light__seventh_chord_ratio": 0.0,
                "experimental__harmony_light__dissonant_verticality_ratio": 0.0,
                "experimental__harmony_light__chord_common_name_entropy": 0.0,
                "experimental__harmony_light__harmonic_rhythm_mean": 0.0,
                "experimental__harmony_light__harmonic_rhythm_variance": 0.0,
                "experimental__harmony_light__vertical_chromaticity_ratio": 0.0,
            },
            chordified_events=[],
            diatonic_pitch_classes=diatonic_pitch_classes,
        )

    common_name_counts = Counter(str(event["common_name"]) for event in chordified_events)
    unique_offsets = sorted({round(float(event["offset"]), 6) for event in chordified_events})
    harmonic_iois = [round(b - a, 6) for a, b in zip(unique_offsets, unique_offsets[1:])]
    chromatic_count = 0
    for event in chordified_events:
        if diatonic_pitch_classes and any(int(pitch_class) not in diatonic_pitch_classes for pitch_class in event["pitch_classes"]):
            chromatic_count += 1

    event_count = len(chordified_events)
    features = {
        "experimental__harmony_light__chordified_event_count": float(event_count),
        "experimental__harmony_light__triad_ratio": _safe_ratio(sum(1 for event in chordified_events if event["is_triad"]), event_count),
        "experimental__harmony_light__seventh_chord_ratio": _safe_ratio(sum(1 for event in chordified_events if event["is_seventh"]), event_count),
        "experimental__harmony_light__dissonant_verticality_ratio": _safe_ratio(sum(1 for event in chordified_events if not event["is_consonant"]), event_count),
        "experimental__harmony_light__chord_common_name_entropy": float(_entropy_from_counts(common_name_counts)),
        "experimental__harmony_light__harmonic_rhythm_mean": float(mean(harmonic_iois)) if harmonic_iois else 0.0,
        "experimental__harmony_light__harmonic_rhythm_variance": _safe_variance(harmonic_iois),
        "experimental__harmony_light__vertical_chromaticity_ratio": _safe_ratio(chromatic_count, event_count),
    }

    return HarmonyLightAnalysis(
        features=features,
        chordified_events=chordified_events,
        diatonic_pitch_classes=diatonic_pitch_classes,
    )


def _chromaticism_features(score, events: list[dict]) -> dict[str, float]:
    pitch_values = [pitch for event in events for pitch in event["pitches"]]
    accidental_density = _safe_ratio(
        sum(int(event.get("accidental_count", 0)) for event in events),
        len(pitch_values),
    )

    diatonic_pitch_classes = _infer_diatonic_pitch_classes(score)
    if diatonic_pitch_classes:
        out_of_key_pitch_ratio = _safe_ratio(
            sum(1 for pitch in pitch_values if int(pitch) % 12 not in diatonic_pitch_classes),
            len(pitch_values),
        )
        non_diatonic_pitch_class_count = float(len({int(pitch) % 12 for pitch in pitch_values if int(pitch) % 12 not in diatonic_pitch_classes}))
    else:
        out_of_key_pitch_ratio = 0.0
        non_diatonic_pitch_class_count = 0.0

    melodic_sequence = [
        int(event["melodic_pitch"])
        for event in events
        if event.get("melodic_pitch") is not None
    ]
    if len(melodic_sequence) > 1:
        semitone_motion_count = sum(1 for a, b in zip(melodic_sequence, melodic_sequence[1:]) if abs(int(b) - int(a)) == 1)
        melodic_semitone_motion_ratio = _safe_ratio(semitone_motion_count, len(melodic_sequence) - 1)
    else:
        melodic_semitone_motion_ratio = 0.0

    pitch_class_entropy = _entropy_from_counts(Counter(int(pitch) % 12 for pitch in pitch_values))

    return {
        "experimental__chromaticism__accidental_density": float(accidental_density),
        "experimental__chromaticism__out_of_key_pitch_ratio": float(out_of_key_pitch_ratio),
        "experimental__chromaticism__chromatic_step_ratio": float(melodic_semitone_motion_ratio),
        "experimental__chromaticism__melodic_semitone_motion_ratio": float(melodic_semitone_motion_ratio),
        "experimental__chromaticism__pitch_class_entropy": float(pitch_class_entropy),
        "experimental__chromaticism__non_diatonic_pitch_class_count": float(non_diatonic_pitch_class_count),
    }


def _texture_features(score, events: list[dict], total_duration: float) -> dict[str, float]:
    grouped = _group_events_by_onset(events)
    if not grouped:
        return {
            "experimental__texture__mean_notes_per_onset": 0.0,
            "experimental__texture__max_notes_per_onset": 0.0,
            "experimental__texture__simultaneity_ratio": 0.0,
            "experimental__texture__single_note_event_ratio": 0.0,
            "experimental__texture__register_span_mean": 0.0,
            "experimental__texture__register_span_max": 0.0,
            "experimental__texture__onset_density_per_quarter": 0.0,
            "experimental__texture__left_right_register_gap_mean": 0.0,
            "experimental__texture__bass_motion_rate": 0.0,
            "experimental__texture__accompaniment_continuity_proxy": 0.0,
            "experimental__texture__arpeggiation_proxy": 0.0,
        }

    onset_note_counts: list[float] = []
    onset_spans: list[float] = []
    single_note_events = 0

    for _, onset_events in grouped:
        pitch_counts = [int(event["pitch_count"]) for event in onset_events]
        onset_note_counts.append(float(sum(pitch_counts)))
        single_note_events += sum(1 for event in onset_events if int(event["pitch_count"]) == 1)

        onset_pitches = sorted({pitch for event in onset_events for pitch in event["pitches"]})
        if onset_pitches:
            onset_spans.append(float(max(onset_pitches) - min(onset_pitches)))
        else:
            onset_spans.append(0.0)

    part_events = _partwise_note_events(score)
    scored_parts = []
    for part in part_events:
        values = _pitch_values(part)
        if values:
            scored_parts.append((_mean_pitch(part), part))
    lower_events = _selected_lower_material_events(score, events)

    left_right_register_gap_mean = 0.0
    if len(scored_parts) >= 2:
        lower_part = min(scored_parts, key=lambda item: item[0])[1]
        upper_part = max(scored_parts, key=lambda item: item[0])[1]
        lower_groups = _group_events_by_onset(lower_part)
        upper_groups = _group_events_by_onset(upper_part)
        lower_lookup = {round(offset, 6): group for offset, group in lower_groups}
        upper_lookup = {round(offset, 6): group for offset, group in upper_groups}
        shared_offsets = sorted(set(lower_lookup) & set(upper_lookup))
        gaps: list[float] = []
        for offset in shared_offsets:
            lower_group = lower_lookup[offset]
            upper_group = upper_lookup[offset]
            lower_pitches = [pitch for event in lower_group for pitch in event["pitches"]]
            upper_pitches = [pitch for event in upper_group for pitch in event["pitches"]]
            if lower_pitches and upper_pitches:
                gaps.append(float(mean(upper_pitches) - mean(lower_pitches)))
        if gaps:
            left_right_register_gap_mean = float(mean(gaps))
        else:
            lower_mean = _mean_pitch(lower_part)
            upper_mean = _mean_pitch(upper_part)
            left_right_register_gap_mean = float(upper_mean - lower_mean)
    else:
        left_right_register_gap_mean = float(mean(onset_spans)) if onset_spans else 0.0

    bass_line: list[float] = []
    bass_source = lower_events if lower_events else events
    for _, onset_events in _group_events_by_onset(bass_source):
        pitches = [pitch for event in onset_events for pitch in event["pitches"]]
        if pitches:
            bass_line.append(float(min(pitches)))
    bass_motion_rate = 0.0
    if len(bass_line) > 1:
        bass_motion_rate = sum(abs(b - a) for a, b in zip(bass_line, bass_line[1:])) / float(total_duration or 1.0)

    accompaniment_continuity_proxy = 0.0
    if lower_events:
        lower_durations = [float(event["duration"]) for event in lower_events]
        duration_threshold = max(1.0, float(median(lower_durations)) if lower_durations else 1.0)
        accompaniment_continuity_proxy = _safe_ratio(sum(1 for duration in lower_durations if duration >= duration_threshold), len(lower_durations))

    arpeggiation_proxy = _monotonic_arpeggiation_windows(events)

    return {
        "experimental__texture__mean_notes_per_onset": float(mean(onset_note_counts)) if onset_note_counts else 0.0,
        "experimental__texture__max_notes_per_onset": float(max(onset_note_counts)) if onset_note_counts else 0.0,
        "experimental__texture__simultaneity_ratio": _safe_ratio(sum(1 for count in onset_note_counts if count > 1), len(onset_note_counts)),
        "experimental__texture__single_note_event_ratio": _safe_ratio(single_note_events, len(events)),
        "experimental__texture__register_span_mean": float(mean(onset_spans)) if onset_spans else 0.0,
        "experimental__texture__register_span_max": float(max(onset_spans)) if onset_spans else 0.0,
        "experimental__texture__onset_density_per_quarter": _safe_ratio(len(grouped), total_duration or 1.0),
        "experimental__texture__left_right_register_gap_mean": float(left_right_register_gap_mean),
        "experimental__texture__bass_motion_rate": float(bass_motion_rate),
        "experimental__texture__accompaniment_continuity_proxy": float(accompaniment_continuity_proxy),
        "experimental__texture__arpeggiation_proxy": float(arpeggiation_proxy),
    }


def _rhythm_phrase_features(score, events: list[dict]) -> dict[str, float]:
    durations = [float(event["duration"]) for event in events]
    onsets = sorted({round(float(event["offset"]), 6) for event in events})
    iois = [round(b - a, 6) for a, b in zip(onsets, onsets[1:])]

    measure_density_values = _measure_density_values(events)
    if measure_density_values:
        mean_density = float(mean(measure_density_values))
        if mean_density == 0.0:
            measure_density_regularity = 0.0
        else:
            variance = _safe_variance(measure_density_values)
            measure_density_regularity = 1.0 / (1.0 + (variance ** 0.5) / abs(mean_density))
    else:
        variance = 0.0
        measure_density_regularity = 0.0

    patterns = _measure_rhythm_patterns(events)
    if patterns:
        pattern_counts = Counter(patterns)
        repeated_rhythm_pattern_ratio = _safe_ratio(sum(count for count in pattern_counts.values() if count > 1), len(patterns))
    else:
        repeated_rhythm_pattern_ratio = 0.0

    if len(measure_density_values) > 4:
        lagged_differences = [
            abs(current - previous)
            for previous, current in zip(measure_density_values[:-4], measure_density_values[4:])
        ]
        four_bar_density_periodicity_score = 1.0 / (1.0 + (sum(lagged_differences) / float(len(lagged_differences) or 1)) / float(mean(measure_density_values) or 1.0))
    else:
        four_bar_density_periodicity_score = 0.0

    measure_numbers = {int(number) for number in _measure_groups(events)}
    rest_punctuation_ratio = _measure_rest_punctuation_ratio(score, measure_numbers)
    end_of_measure_long_note_ratio = _measure_end_long_note_ratio(events)

    return {
        "experimental__rhythm_phrase__duration_entropy": float(_entropy_from_counts(Counter(durations))),
        "experimental__rhythm_phrase__ioi_entropy": float(_entropy_from_counts(Counter(iois))),
        "experimental__rhythm_phrase__short_note_ratio": _safe_ratio(sum(1 for duration in durations if duration <= 0.5), len(durations)),
        "experimental__rhythm_phrase__long_note_ratio": _safe_ratio(sum(1 for duration in durations if duration >= 1.0), len(durations)),
        "experimental__rhythm_phrase__measure_density_variance": float(variance),
        "experimental__rhythm_phrase__measure_density_regularity": float(measure_density_regularity),
        "experimental__rhythm_phrase__four_bar_density_periodicity_score": float(four_bar_density_periodicity_score),
        "experimental__rhythm_phrase__repeated_rhythm_pattern_ratio": float(repeated_rhythm_pattern_ratio),
        "experimental__rhythm_phrase__rest_punctuation_ratio": float(rest_punctuation_ratio),
        "experimental__rhythm_phrase__end_of_measure_long_note_ratio": float(end_of_measure_long_note_ratio),
    }


def _harmony_heavy_features(score, roman_result: RomanNumeralAnalysisResult) -> dict[str, float]:
    events = roman_result.events
    event_count = len(events)
    if event_count == 0:
        return {
            "experimental__harmony_heavy__tonic_ratio": 0.0,
            "experimental__harmony_heavy__dominant_ratio": 0.0,
            "experimental__harmony_heavy__predominant_ratio": 0.0,
            "experimental__harmony_heavy__applied_dominant_ratio": 0.0,
            "experimental__harmony_heavy__secondary_function_ratio": 0.0,
            "experimental__harmony_heavy__modal_mixture_ratio": 0.0,
            "experimental__harmony_heavy__chromatic_chord_ratio": 0.0,
            "experimental__harmony_heavy__diminished_chord_ratio": 0.0,
            "experimental__harmony_heavy__seventh_chord_ratio": 0.0,
            "experimental__harmony_heavy__non_diatonic_root_ratio": 0.0,
            "experimental__harmony_heavy__modulation_count": 0.0,
            "experimental__harmony_heavy__local_key_count": 0.0,
            "experimental__harmony_heavy__mean_harmonic_rhythm": 0.0,
            "experimental__harmony_heavy__harmonic_rhythm_variance": 0.0,
            "experimental__harmony_heavy__cadence_like_V_I_count": 0.0,
            "experimental__harmony_heavy__deceptive_motion_count": 0.0,
            "experimental__harmony_heavy__rn_backend_available": float(roman_result.backend_available),
            "experimental__harmony_heavy__rn_event_count": 0.0,
        }

    global_key_pitch_classes = set(roman_result.global_key_pitch_classes)
    tonic_count = sum(1 for event in events if event.function_category == "tonic")
    dominant_count = sum(1 for event in events if event.function_category == "dominant")
    predominant_count = sum(1 for event in events if event.function_category == "predominant")
    applied_dominant_count = sum(1 for event in events if event.is_applied_dominant)
    secondary_function_count = sum(1 for event in events if event.is_secondary)
    modal_mixture_count = sum(1 for event in events if event.is_modal_mixture)
    chromatic_chord_count = sum(1 for event in events if event.is_chromatic)
    diminished_chord_count = sum(1 for event in events if event.is_diminished)
    seventh_chord_count = sum(1 for event in events if event.is_seventh)
    non_diatonic_root_count = 0
    for event in events:
        if event.root_pitch_class is not None and global_key_pitch_classes and int(event.root_pitch_class) not in global_key_pitch_classes:
            non_diatonic_root_count += 1

    ordered_measure_labels = [roman_result.measure_key_labels[number] for number in sorted(roman_result.measure_key_labels)]
    local_key_labels = [label for label in ordered_measure_labels if label]
    local_key_count = float(len(set(local_key_labels))) if local_key_labels else 0.0
    modulation_count = 0.0
    if len(local_key_labels) > 1:
        modulation_count = float(sum(1 for previous, current in zip(local_key_labels, local_key_labels[1:]) if previous != current))

    ordered_events = sorted(events, key=lambda event: (float(event.offset), float(event.duration)))
    harmonic_offsets = sorted({round(float(event.offset), 6) for event in ordered_events})
    harmonic_iois = [round(b - a, 6) for a, b in zip(harmonic_offsets, harmonic_offsets[1:])]
    cadence_like_offsets: list[float] = []
    deceptive_motion_count = 0
    for previous, current in zip(ordered_events, ordered_events[1:]):
        if previous.function_category == "dominant" and current.function_category == "tonic" and previous.local_key_label == current.local_key_label:
            cadence_like_offsets.append(float(current.offset))
        previous_base = previous.figure.upper()
        current_base = current.figure.upper()
        if previous.function_category == "dominant" and current_base.startswith("VI") and not current_base.startswith("VII"):
            deceptive_motion_count += 1

    cadence_like_V_I_count = float(len(cadence_like_offsets))
    mean_harmonic_rhythm = float(mean(harmonic_iois)) if harmonic_iois else 0.0
    harmonic_rhythm_variance = _safe_variance(harmonic_iois)
    if len(cadence_like_offsets) > 1:
        cadence_spacings = [b - a for a, b in zip(cadence_like_offsets, cadence_like_offsets[1:])]
    else:
        cadence_spacings = []

    return {
        "experimental__harmony_heavy__tonic_ratio": _safe_ratio(tonic_count, event_count),
        "experimental__harmony_heavy__dominant_ratio": _safe_ratio(dominant_count, event_count),
        "experimental__harmony_heavy__predominant_ratio": _safe_ratio(predominant_count, event_count),
        "experimental__harmony_heavy__applied_dominant_ratio": _safe_ratio(applied_dominant_count, event_count),
        "experimental__harmony_heavy__secondary_function_ratio": _safe_ratio(secondary_function_count, event_count),
        "experimental__harmony_heavy__modal_mixture_ratio": _safe_ratio(modal_mixture_count, event_count),
        "experimental__harmony_heavy__chromatic_chord_ratio": _safe_ratio(chromatic_chord_count, event_count),
        "experimental__harmony_heavy__diminished_chord_ratio": _safe_ratio(diminished_chord_count, event_count),
        "experimental__harmony_heavy__seventh_chord_ratio": _safe_ratio(seventh_chord_count, event_count),
        "experimental__harmony_heavy__non_diatonic_root_ratio": _safe_ratio(non_diatonic_root_count, event_count),
        "experimental__harmony_heavy__modulation_count": float(modulation_count),
        "experimental__harmony_heavy__local_key_count": float(local_key_count),
        "experimental__harmony_heavy__mean_harmonic_rhythm": float(mean_harmonic_rhythm),
        "experimental__harmony_heavy__harmonic_rhythm_variance": float(harmonic_rhythm_variance),
        "experimental__harmony_heavy__cadence_like_V_I_count": float(cadence_like_V_I_count),
        "experimental__harmony_heavy__deceptive_motion_count": float(deceptive_motion_count),
        "experimental__harmony_heavy__rn_backend_available": float(roman_result.backend_available),
        "experimental__harmony_heavy__rn_event_count": float(event_count),
    }


def _syntax_interaction_features(
    score,
    note_events: list[dict],
    harmony_light: HarmonyLightAnalysis,
    roman_result: RomanNumeralAnalysisResult,
    total_duration: float,
) -> dict[str, float]:
    if not note_events:
        return {
            "experimental__syntax_interaction__non_chord_tone_ratio": 0.0,
            "experimental__syntax_interaction__accented_non_chord_tone_ratio": 0.0,
            "experimental__syntax_interaction__resolved_stepwise_ratio": 0.0,
            "experimental__syntax_interaction__mean_resolution_delay": 0.0,
            "experimental__syntax_interaction__unresolved_dissonance_ratio": 0.0,
            "experimental__syntax_interaction__cadence_spacing_mean": 0.0,
            "experimental__syntax_interaction__cadence_spacing_variance": 0.0,
            "experimental__syntax_interaction__dominant_arrival_density": 0.0,
            "experimental__syntax_interaction__dissonance_on_strong_beat_ratio": 0.0,
        }

    harmonic_events = harmony_light.chordified_events
    harmonic_offsets = sorted({round(float(event["offset"]), 6) for event in harmonic_events})
    harmonic_lookup: dict[float, set[int]] = {}
    for event in harmonic_events:
        offset = round(float(event["offset"]), 6)
        harmonic_lookup.setdefault(offset, set()).update(int(pitch_class) for pitch_class in event["pitch_classes"])

    sorted_harmonic_offsets = sorted(harmonic_lookup)

    def _harmony_pitch_classes_for_offset(offset: float) -> set[int]:
        if not sorted_harmonic_offsets:
            return set()
        search_index = bisect_right(sorted_harmonic_offsets, round(offset, 6)) - 1
        if search_index < 0:
            return set()
        return harmonic_lookup[sorted_harmonic_offsets[search_index]]

    sorted_note_events = sorted(note_events, key=lambda event: (float(event.get("offset", 0.0)), float(event.get("duration", 0.0))))
    non_chord_tones = 0
    accented_non_chord_tones = 0
    strong_beat_non_chord_tones = 0
    resolved_non_chord_tones = 0
    unresolved_non_chord_tones = 0
    resolution_delays: list[float] = []

    melodic_events = [event for event in sorted_note_events if event.get("melodic_pitch") is not None]
    for index, event in enumerate(sorted_note_events):
        pitch_classes = {int(pitch) % 12 for pitch in event["pitches"]}
        harmony_pitch_classes = _harmony_pitch_classes_for_offset(float(event["offset"]))
        if harmony_pitch_classes and not pitch_classes.issubset(harmony_pitch_classes):
            non_chord_tones += 1
            if _is_strong_beat(event):
                accented_non_chord_tones += 1
                strong_beat_non_chord_tones += 1

    for index, event in enumerate(melodic_events):
        pitch = int(event["melodic_pitch"])
        harmony_pitch_classes = _harmony_pitch_classes_for_offset(float(event["offset"]))
        if harmony_pitch_classes and {int(p) % 12 for p in event["pitches"]}.issubset(harmony_pitch_classes):
            continue
        next_event = None
        for candidate in melodic_events[index + 1 :]:
            if float(candidate["offset"]) > float(event["offset"]):
                next_event = candidate
                break
        if next_event is None:
            unresolved_non_chord_tones += 1
            continue
        next_pitch = int(next_event["melodic_pitch"])
        if abs(next_pitch - pitch) <= 2:
            resolved_non_chord_tones += 1
            resolution_delays.append(float(next_event["offset"]) - float(event["offset"]))
        else:
            unresolved_non_chord_tones += 1

    cadence_offsets: list[float] = []
    ordered_roman_events = sorted(roman_result.events, key=lambda event: (float(event.offset), float(event.duration)))
    for previous, current in zip(ordered_roman_events, ordered_roman_events[1:]):
        if previous.function_category == "dominant" and current.function_category == "tonic" and previous.local_key_label == current.local_key_label:
            cadence_offsets.append(float(current.offset))

    cadence_spacing_mean = 0.0
    cadence_spacing_variance = 0.0
    if len(cadence_offsets) > 1:
        cadence_spacings = [b - a for a, b in zip(cadence_offsets, cadence_offsets[1:])]
        cadence_spacing_mean = float(mean(cadence_spacings))
        cadence_spacing_variance = _safe_variance(cadence_spacings)

    dominant_arrival_density = _safe_ratio(len(cadence_offsets), total_duration or 1.0)
    non_chord_tone_ratio = _safe_ratio(non_chord_tones, len(note_events))
    accented_non_chord_tone_ratio = _safe_ratio(accented_non_chord_tones, len(note_events))
    resolved_stepwise_ratio = _safe_ratio(resolved_non_chord_tones, non_chord_tones)
    mean_resolution_delay = float(mean(resolution_delays)) if resolution_delays else 0.0
    unresolved_dissonance_ratio = _safe_ratio(unresolved_non_chord_tones, non_chord_tones)
    dissonance_on_strong_beat_ratio = _safe_ratio(strong_beat_non_chord_tones, non_chord_tones)

    return {
        "experimental__syntax_interaction__non_chord_tone_ratio": float(non_chord_tone_ratio),
        "experimental__syntax_interaction__accented_non_chord_tone_ratio": float(accented_non_chord_tone_ratio),
        "experimental__syntax_interaction__resolved_stepwise_ratio": float(resolved_stepwise_ratio),
        "experimental__syntax_interaction__mean_resolution_delay": float(mean_resolution_delay),
        "experimental__syntax_interaction__unresolved_dissonance_ratio": float(unresolved_dissonance_ratio),
        "experimental__syntax_interaction__cadence_spacing_mean": float(cadence_spacing_mean),
        "experimental__syntax_interaction__cadence_spacing_variance": float(cadence_spacing_variance),
        "experimental__syntax_interaction__dominant_arrival_density": float(dominant_arrival_density),
        "experimental__syntax_interaction__dissonance_on_strong_beat_ratio": float(dissonance_on_strong_beat_ratio),
    }


def extract_experimental_musicological_feature_families(score) -> dict[str, dict[str, float]]:
    events = _collect_note_events(score)
    total_duration = _highest_time(score)
    harmony_light = _harmonic_event_records(score)

    try:
        roman_result = analyze_roman_numerals(score)
    except Exception as exc:
        roman_result = RomanNumeralAnalysisResult(
            backend_name="music21",
            backend_available=False,
            warnings=(str(exc),),
        )

    return {
        "experimental_chromaticism": _chromaticism_features(score, events),
        "experimental_texture": _texture_features(score, events, total_duration),
        "experimental_rhythm_phrase": _rhythm_phrase_features(score, events),
        "experimental_harmony_light": harmony_light.features,
        "experimental_harmony_heavy": _harmony_heavy_features(score, roman_result),
        "experimental_syntax_interaction": _syntax_interaction_features(score, events, harmony_light, roman_result, total_duration),
    }


def extract_experimental_musicological_features(score) -> dict[str, float]:
    families = extract_experimental_musicological_feature_families(score)
    features: dict[str, float] = {}
    for family_features in families.values():
        features.update(family_features)
    return features
