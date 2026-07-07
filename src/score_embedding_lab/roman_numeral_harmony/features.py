from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from math import log2
from statistics import mean, median

try:  # pragma: no cover - optional dependency
    from music21 import note
except Exception:  # pragma: no cover - optional dependency
    note = None

from .models import RomanNumeralAnalysisResult, RomanNumeralEvent

PREFIX = "experimental__"


def _feature_name(family: str, slug: str) -> str:
    return f"{PREFIX}{family}__{slug}"


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return float(numerator) / float(denominator)


def _entropy(values: list[str | float | int]) -> float:
    if not values:
        return 0.0
    counts = Counter(values)
    total = float(sum(counts.values()))
    if total == 0:
        return 0.0
    return float(-sum((count / total) * log2(count / total) for count in counts.values() if count > 0))


def _std(values: list[float]) -> float:
    if not values:
        return 0.0
    mu = float(mean(values))
    return float(mean([(value - mu) ** 2 for value in values]) ** 0.5)


def _duration_stats(events: list[RomanNumeralEvent]) -> tuple[float, float, float, float, float, float]:
    durations = [float(event.duration_quarter) for event in events if event.duration_quarter is not None]
    if not durations:
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    return (
        float(mean(durations)),
        float(median(durations)),
        _std(durations),
        _entropy([round(duration, 3) for duration in durations]),
        _safe_ratio(sum(1 for duration in durations if duration < 1.0), len(durations)),
        _safe_ratio(sum(1 for duration in durations if duration >= 2.0), len(durations)),
    )


def _pitch_class_set_from_event(event: RomanNumeralEvent) -> set[int]:
    return {int(value) for value in event.pitch_classes if value is not None}


def _global_key_pitch_classes(label: str | None) -> set[int]:
    if not label:
        return set()
    name = str(label).strip().lower()
    if not name:
        return set()
    tonic_map = {
        "c": 0,
        "c#": 1,
        "db": 1,
        "d": 2,
        "d#": 3,
        "eb": 3,
        "e": 4,
        "f": 5,
        "f#": 6,
        "gb": 6,
        "g": 7,
        "g#": 8,
        "ab": 8,
        "a": 9,
        "a#": 10,
        "bb": 10,
        "b": 11,
    }
    tonic = tonic_map.get(name.split()[0])
    if tonic is None:
        return set()
    mode = "minor" if "minor" in name else "major"
    intervals = (0, 2, 3, 5, 7, 8, 10) if mode == "minor" else (0, 2, 4, 5, 7, 9, 11)
    return {(tonic + interval) % 12 for interval in intervals}


def _function_bucket(label: str | None) -> str:
    return str(label or "unknown").lower()


def _is_chromatic_event(event: RomanNumeralEvent) -> bool:
    text = " ".join(
        value.lower()
        for value in (
            event.figure,
            event.roman_numeral,
            event.raw_label,
            event.function_label,
        )
        if value
    )
    return any(token in text for token in ("secondary", "applied", "borrow", "chromatic", "ger", "fr", "it", "+6", "n6", "neap"))


def _is_dominant(event: RomanNumeralEvent) -> bool:
    bucket = _function_bucket(event.function_label)
    return bucket == "dominant" or bucket.startswith("dominant")


def _is_tonic(event: RomanNumeralEvent) -> bool:
    bucket = _function_bucket(event.function_label)
    return bucket == "tonic" or bucket.startswith("tonic")


def _is_predominant(event: RomanNumeralEvent) -> bool:
    bucket = _function_bucket(event.function_label)
    return bucket == "predominant" or bucket.startswith("predominant")


def _event_time_ranges(events: list[RomanNumeralEvent]) -> list[tuple[float, float, RomanNumeralEvent]]:
    return [(float(event.onset_quarter), float(event.onset_quarter) + float(event.duration_quarter), event) for event in events]


def _active_events_at_time(events: list[RomanNumeralEvent], time_point: float) -> list[RomanNumeralEvent]:
    active = []
    for start, end, event in _event_time_ranges(events):
        if start <= time_point < end or (event.duration_quarter == 0 and start == time_point):
            active.append(event)
    return active


def _group_note_events_by_onset(score) -> dict[float, list[dict[str, object]]]:
    grouped: dict[float, list[dict[str, object]]] = defaultdict(list)
    if score is None or note is None:
        return grouped
    try:
        notes = score.recurse().notes
    except Exception:
        notes = []
    for item in notes:
        if isinstance(item, note.Rest):
            continue
        pitch_source = [item] if isinstance(item, note.Note) else getattr(item, "pitches", [])
        if not pitch_source:
            continue
        onset = float(getattr(item, "offset", 0.0))
        duration = float(getattr(item, "quarterLength", 0.0))
        measure_number = getattr(item, "measureNumber", None)
        try:
            measure_number = int(measure_number) if measure_number is not None else None
        except Exception:
            measure_number = None
        beat = None
        try:
            beat = float(getattr(item, "beat", None))
        except Exception:
            beat = None
        pitches = [int(getattr(pitch, "pitchClass", getattr(item.pitch, "pitchClass", 0))) for pitch in pitch_source]
        midi_values = [int(getattr(pitch, "midi", getattr(item.pitch, "midi", 0))) for pitch in pitch_source]
        grouped[round(onset, 3)].append(
            {
                "onset": onset,
                "duration": duration,
                "measure_number": measure_number,
                "beat": beat,
                "pitch_classes": pitches,
                "midi_values": midi_values,
                "pitch_count": len(pitches),
                "note": item,
            }
        )
    return grouped


def _melody_track(score) -> list[dict[str, object]]:
    if score is None or note is None:
        return []
    grouped = _group_note_events_by_onset(score)
    melody_events: list[dict[str, object]] = []
    for onset in sorted(grouped):
        candidates = grouped[onset]
        if not candidates:
            continue
        pitches = [max(candidate["midi_values"]) for candidate in candidates if candidate["midi_values"]]
        if not pitches:
            continue
        chosen = max(candidates, key=lambda candidate: max(candidate["midi_values"]) if candidate["midi_values"] else -1)
        melody_events.append(chosen)
    return melody_events


def _strong_beat(beat: float | None) -> bool:
    if beat is None:
        return False
    try:
        beat_value = float(beat)
    except Exception:
        return False
    rounded = round(beat_value)
    return abs(beat_value - rounded) <= 0.25 and rounded in {1, 2, 3, 4}


def _root_motion_type(a: RomanNumeralEvent, b: RomanNumeralEvent) -> str:
    if a.root_pitch_class is None or b.root_pitch_class is None:
        return "unknown"
    interval = (int(b.root_pitch_class) - int(a.root_pitch_class)) % 12
    if interval in {1, 2, 10, 11}:
        return "step"
    if interval in {3, 4, 8, 9}:
        return "third"
    if interval in {5, 7}:
        return "fifth"
    return "other"


def _is_cadential_pair(a: RomanNumeralEvent, b: RomanNumeralEvent) -> bool:
    return _is_dominant(a) and _is_tonic(b)


def _is_plagal_cadence(a: RomanNumeralEvent, b: RomanNumeralEvent, c: RomanNumeralEvent | None = None) -> bool:
    if c is None:
        return _is_predominant(a) and _is_dominant(b) and _is_tonic(c) if c else False
    return _is_predominant(a) and _is_dominant(b) and _is_tonic(c)


def _rn_bigram_entropy(events: list[RomanNumeralEvent]) -> float:
    labels = [event.figure or event.roman_numeral or event.raw_label or "unknown" for event in events]
    bigrams = [f"{left}__{right}" for left, right in zip(labels, labels[1:])]
    return _entropy(bigrams)


def _root_motion_ratios(events: list[RomanNumeralEvent]) -> dict[str, float]:
    if len(events) < 2:
        return {"step": 0.0, "fifth": 0.0, "third": 0.0, "circle": 0.0}
    motions = [_root_motion_type(a, b) for a, b in zip(events, events[1:])]
    total = len(motions)
    return {
        "step": _safe_ratio(sum(1 for motion in motions if motion == "step"), total),
        "fifth": _safe_ratio(sum(1 for motion in motions if motion == "fifth"), total),
        "third": _safe_ratio(sum(1 for motion in motions if motion == "third"), total),
        "circle": _safe_ratio(sum(1 for motion in motions if motion == "fifth"), total),
    }


def _function_ratios(events: list[RomanNumeralEvent]) -> dict[str, float]:
    total = len(events)
    labels = [event.function_label or "unknown" for event in events]
    return {
        "tonic": _safe_ratio(sum(1 for label in labels if str(label).startswith("tonic")), total),
        "dominant": _safe_ratio(sum(1 for label in labels if str(label).startswith("dominant")), total),
        "predominant": _safe_ratio(sum(1 for label in labels if str(label).startswith("predominant")), total),
        "unknown": _safe_ratio(sum(1 for label in labels if str(label).startswith("unknown")), total),
    }


def _chromatic_ratios(events: list[RomanNumeralEvent]) -> dict[str, float]:
    total = len(events)
    chromatic_events = [event for event in events if _is_chromatic_event(event)]
    secondary_events = [event for event in events if "secondary" in str(event.function_label or "").lower() or "/" in str(event.figure or "")]
    modal_mixture_events = [event for event in events if any(token in str(event.figure or "").lower() for token in ("iv", "biii", "bvi", "bvii", "n6", "ger", "fr", "it"))]
    diminished_events = [event for event in events if "dim" in str(event.figure or "").lower() or "o" in str(event.figure or "").lower()]
    augmented_sixth_events = [event for event in events if any(token in str(event.figure or "").lower() for token in ("+6", "ger", "fr", "it"))]
    neapolitan_events = [event for event in events if any(token in str(event.figure or "").lower() for token in ("n6", "neap", "bii"))]
    non_diatonic_root_events = [event for event in events if event.root_pitch_class is not None and event.global_key is not None and int(event.root_pitch_class) % 12 not in _global_key_pitch_classes(event.global_key)]
    return {
        "applied_dominant": _safe_ratio(sum(1 for event in secondary_events if "/" in str(event.figure or "") or "applied" in str(event.raw_label or "").lower()), total),
        "secondary_function": _safe_ratio(len(secondary_events), total),
        "modal_mixture": _safe_ratio(len(modal_mixture_events), total),
        "chromatic_function": _safe_ratio(len(chromatic_events), total),
        "non_diatonic_root": _safe_ratio(len(non_diatonic_root_events), total),
        "diminished_chord": _safe_ratio(len(diminished_events), total),
        "augmented_sixth_like": _safe_ratio(len(augmented_sixth_events), total),
        "neapolitan_like": _safe_ratio(len(neapolitan_events), total),
    }


def _cadence_stats(events: list[RomanNumeralEvent]) -> dict[str, float]:
    if len(events) < 2:
        return {
            "cadence_like_V_I_density": 0.0,
            "cadence_like_iv_v_i_or_ii_v_i_density": 0.0,
            "deceptive_motion_density": 0.0,
            "dominant_prolongation_ratio": 0.0,
            "mean_cadence_spacing": 0.0,
            "cadence_spacing_variance": 0.0,
        }
    cadence_times: list[float] = []
    cadence_like = 0
    plagal_like = 0
    deceptive = 0
    dominant_pairs = 0
    for index, (a, b) in enumerate(zip(events, events[1:])):
        if _is_cadential_pair(a, b):
            cadence_like += 1
            cadence_times.append(float(b.onset_quarter))
        if _is_predominant(a) and _is_dominant(b) and index + 2 < len(events) and _is_tonic(events[index + 2]):
            plagal_like += 1
        if _is_dominant(a) and not _is_tonic(b):
            deceptive += 1
        if _is_dominant(a) and _is_dominant(b):
            dominant_pairs += 1
    spacings = [b - a for a, b in zip(cadence_times, cadence_times[1:])]
    cadence_spacing_variance = float(mean([(spacing - float(mean(spacings))) ** 2 for spacing in spacings])) if len(spacings) > 1 else 0.0
    return {
        "cadence_like_V_I_density": _safe_ratio(cadence_like, len(events)),
        "cadence_like_iv_v_i_or_ii_v_i_density": _safe_ratio(plagal_like, len(events)),
        "deceptive_motion_density": _safe_ratio(deceptive, len(events)),
        "dominant_prolongation_ratio": _safe_ratio(dominant_pairs, len(events)),
        "mean_cadence_spacing": float(mean(spacings)) if spacings else 0.0,
        "cadence_spacing_variance": cadence_spacing_variance,
    }


def _melody_features(score, events: list[RomanNumeralEvent], analysis_result: RomanNumeralAnalysisResult) -> dict[str, float]:
    if score is None or note is None:
        return {
            "melody_chord_tone_ratio": 0.0,
            "melody_non_chord_tone_ratio": 0.0,
            "accented_non_chord_tone_ratio": 0.0,
            "chromatic_non_chord_tone_ratio": 0.0,
            "stepwise_resolution_ratio": 0.0,
            "mean_resolution_delay": 0.0,
            "melody_on_chord_root_ratio": 0.0,
            "melody_on_third_ratio": 0.0,
            "melody_on_seventh_ratio": 0.0,
            "melodic_dissonance_on_strong_beat_ratio": 0.0,
        }
    melody_events = _melody_track(score)
    global_scale = set(int(value) for value in analysis_result.metadata.get("pitch_class_set", []) if isinstance(value, int))
    if not melody_events or not events:
        return {
            "melody_chord_tone_ratio": 0.0,
            "melody_non_chord_tone_ratio": 0.0,
            "accented_non_chord_tone_ratio": 0.0,
            "chromatic_non_chord_tone_ratio": 0.0,
            "stepwise_resolution_ratio": 0.0,
            "mean_resolution_delay": 0.0,
            "melody_on_chord_root_ratio": 0.0,
            "melody_on_third_ratio": 0.0,
            "melody_on_seventh_ratio": 0.0,
            "melodic_dissonance_on_strong_beat_ratio": 0.0,
        }
    total = len(melody_events)
    chord_tone = 0
    non_chord = 0
    accented_non_chord = 0
    chromatic_non_chord = 0
    resolved = 0
    resolution_delays: list[float] = []
    root_hits = 0
    third_hits = 0
    seventh_hits = 0
    strong_beat_dissonance = 0
    for index, melody in enumerate(melody_events):
        onset = float(melody["onset"])
        midi_values = melody["midi_values"]
        if not midi_values:
            continue
        pitch_class = int(max(midi_values)) % 12
        active_events = _active_events_at_time(events, onset)
        active_event = active_events[0] if active_events else None
        if active_event is None:
            continue
        pcs = _pitch_class_set_from_event(active_event)
        is_chord_tone = pitch_class in pcs if pcs else False
        if is_chord_tone:
            chord_tone += 1
        else:
            non_chord += 1
            if _strong_beat(melody.get("beat")):
                accented_non_chord += 1
            if global_scale and pitch_class not in global_scale:
                chromatic_non_chord += 1
            if _strong_beat(melody.get("beat")):
                strong_beat_dissonance += 1
            if index + 1 < len(melody_events):
                next_pitch = int(max(melody_events[index + 1]["midi_values"])) % 12
                if abs((next_pitch - pitch_class) % 12) in {1, 2, 10, 11}:
                    resolved += 1
                    resolution_delays.append(float(melody_events[index + 1]["onset"]) - onset)
        if active_event.root_pitch_class is not None and pitch_class == int(active_event.root_pitch_class) % 12:
            root_hits += 1
        if pcs and pitch_class in pcs:
            if active_event.root_pitch_class is not None:
                interval = (pitch_class - int(active_event.root_pitch_class)) % 12
                if interval in {3, 4}:
                    third_hits += 1
                elif interval in {10, 11}:
                    seventh_hits += 1
    return {
        "melody_chord_tone_ratio": _safe_ratio(chord_tone, total),
        "melody_non_chord_tone_ratio": _safe_ratio(non_chord, total),
        "accented_non_chord_tone_ratio": _safe_ratio(accented_non_chord, total),
        "chromatic_non_chord_tone_ratio": _safe_ratio(chromatic_non_chord, total),
        "stepwise_resolution_ratio": _safe_ratio(resolved, max(non_chord, 1)),
        "mean_resolution_delay": float(mean(resolution_delays)) if resolution_delays else 0.0,
        "melody_on_chord_root_ratio": _safe_ratio(root_hits, total),
        "melody_on_third_ratio": _safe_ratio(third_hits, total),
        "melody_on_seventh_ratio": _safe_ratio(seventh_hits, total),
        "melodic_dissonance_on_strong_beat_ratio": _safe_ratio(strong_beat_dissonance, max(non_chord, 1)),
    }


def _texture_features(score, events: list[RomanNumeralEvent]) -> dict[str, float]:
    if score is None or note is None:
        return {
            "mean_notes_per_onset_during_dominant": 0.0,
            "mean_notes_per_onset_during_tonic": 0.0,
            "register_span_during_chromatic_harmony": 0.0,
            "arpeggiation_during_chromatic_harmony": 0.0,
            "accompaniment_continuity_during_dominant": 0.0,
            "bass_motion_rate_during_chromatic_harmony": 0.0,
            "simultaneity_ratio_during_cadential_harmony": 0.0,
            "texture_change_at_harmonic_change_ratio": 0.0,
        }
    grouped = _group_note_events_by_onset(score)
    if not grouped or not events:
        return {
            "mean_notes_per_onset_during_dominant": 0.0,
            "mean_notes_per_onset_during_tonic": 0.0,
            "register_span_during_chromatic_harmony": 0.0,
            "arpeggiation_during_chromatic_harmony": 0.0,
            "accompaniment_continuity_during_dominant": 0.0,
            "bass_motion_rate_during_chromatic_harmony": 0.0,
            "simultaneity_ratio_during_cadential_harmony": 0.0,
            "texture_change_at_harmonic_change_ratio": 0.0,
        }
    dominant_note_counts: list[float] = []
    tonic_note_counts: list[float] = []
    chromatic_spans: list[float] = []
    chromatic_onset_sequences: list[tuple[float, int]] = []
    dominant_continuity: list[float] = []
    bass_changes = 0
    bass_observations = 0
    cadential_simultaneity = []
    texture_change_pairs = 0
    texture_change_total = 0
    onset_items = sorted(grouped.items())
    for onset, note_items in onset_items:
        active_events = _active_events_at_time(events, onset)
        active_event = active_events[0] if active_events else None
        count = float(len(note_items))
        span_values = [max(item["midi_values"]) for item in note_items] + [min(item["midi_values"]) for item in note_items]
        if active_event is None:
            continue
        if _is_dominant(active_event):
            dominant_note_counts.append(count)
            dominant_continuity.append(_safe_ratio(sum(1 for item in note_items if float(item["duration"]) >= 1.0), len(note_items)))
        if _is_tonic(active_event):
            tonic_note_counts.append(count)
        if _is_chromatic_event(active_event):
            if span_values:
                chromatic_spans.append(float(max(span_values) - min(span_values)))
            chromatic_onset_sequences.append((onset, len(note_items)))
            if note_items:
                bass_changes += 1 if len({min(item["midi_values"]) for item in note_items}) > 1 else 0
                bass_observations += 1
        if _is_dominant(active_event) or _is_tonic(active_event):
            cadential_simultaneity.append(_safe_ratio(sum(1 for item in note_items if len(item["midi_values"]) > 1), len(note_items)))
    for left, right in zip(events, events[1:]):
        if left.figure == right.figure:
            continue
        left_active = [items for onset, items in onset_items if float(onset) >= left.onset_quarter and float(onset) < left.onset_quarter + left.duration_quarter]
        right_active = [items for onset, items in onset_items if float(onset) >= right.onset_quarter and float(onset) < right.onset_quarter + right.duration_quarter]
        if not left_active or not right_active:
            continue
        left_mean = mean([len(items) for items in left_active])
        right_mean = mean([len(items) for items in right_active])
        texture_change_total += 1
        if abs(left_mean - right_mean) >= 1.0:
            texture_change_pairs += 1
    return {
        "mean_notes_per_onset_during_dominant": float(mean(dominant_note_counts)) if dominant_note_counts else 0.0,
        "mean_notes_per_onset_during_tonic": float(mean(tonic_note_counts)) if tonic_note_counts else 0.0,
        "register_span_during_chromatic_harmony": float(mean(chromatic_spans)) if chromatic_spans else 0.0,
        "arpeggiation_during_chromatic_harmony": _safe_ratio(sum(1 for _, count in chromatic_onset_sequences if count >= 3), len(chromatic_onset_sequences)),
        "accompaniment_continuity_during_dominant": float(mean(dominant_continuity)) if dominant_continuity else 0.0,
        "bass_motion_rate_during_chromatic_harmony": _safe_ratio(bass_changes, bass_observations),
        "simultaneity_ratio_during_cadential_harmony": float(mean(cadential_simultaneity)) if cadential_simultaneity else 0.0,
        "texture_change_at_harmonic_change_ratio": _safe_ratio(texture_change_pairs, texture_change_total),
    }


def _availability(result: RomanNumeralAnalysisResult) -> float:
    return 1.0 if result.backend_available else 0.0


def extract_rn_harmony_features(score, analysis_result: RomanNumeralAnalysisResult) -> dict[str, float]:
    events = list(analysis_result.events)
    total = len(events)
    labels = [event.figure or event.roman_numeral or event.raw_label or "unknown" for event in events]
    local_keys = [event.local_key for event in events if event.local_key]
    durations = [float(event.duration_quarter) for event in events]
    function_ratios = _function_ratios(events)
    chromatic_ratios = _chromatic_ratios(events)
    cadence_stats = _cadence_stats(events)
    rhythm_mean, rhythm_median, rhythm_variance, rhythm_entropy, short_ratio, long_ratio = _duration_stats(events)
    motion_ratios = _root_motion_ratios(events)
    rn_features = {
        _feature_name("rn_harmony", "backend_available"): _availability(analysis_result),
        _feature_name("rn_harmony", "analysis_success"): 1.0 if analysis_result.success else 0.0,
        _feature_name("rn_harmony", "rn_event_count"): float(total),
        _feature_name("rn_harmony", "rn_label_entropy"): _entropy(labels),
        _feature_name("rn_harmony", "local_key_count"): float(len(set(local_keys))),
        _feature_name("rn_harmony", "modulation_density"): _safe_ratio(max(len(set(local_keys)) - 1, 0), sum(durations) or 1.0),
        _feature_name("rn_harmony", "tonic_function_ratio"): function_ratios["tonic"],
        _feature_name("rn_harmony", "dominant_function_ratio"): function_ratios["dominant"],
        _feature_name("rn_harmony", "predominant_function_ratio"): function_ratios["predominant"],
        _feature_name("rn_harmony", "unknown_function_ratio"): function_ratios["unknown"],
        _feature_name("rn_harmony", "applied_dominant_ratio"): chromatic_ratios["applied_dominant"],
        _feature_name("rn_harmony", "secondary_function_ratio"): chromatic_ratios["secondary_function"],
        _feature_name("rn_harmony", "modal_mixture_ratio"): chromatic_ratios["modal_mixture"],
        _feature_name("rn_harmony", "chromatic_function_ratio"): chromatic_ratios["chromatic_function"],
        _feature_name("rn_harmony", "non_diatonic_root_ratio"): chromatic_ratios["non_diatonic_root"],
        _feature_name("rn_harmony", "diminished_chord_ratio"): chromatic_ratios["diminished_chord"],
        _feature_name("rn_harmony", "augmented_sixth_like_ratio"): chromatic_ratios["augmented_sixth_like"],
        _feature_name("rn_harmony", "neapolitan_like_ratio"): chromatic_ratios["neapolitan_like"],
        _feature_name("rn_harmony", "cadence_like_V_I_density"): cadence_stats["cadence_like_V_I_density"],
        _feature_name("rn_harmony", "cadence_like_iv_v_i_or_ii_v_i_density"): cadence_stats["cadence_like_iv_v_i_or_ii_v_i_density"],
        _feature_name("rn_harmony", "deceptive_motion_density"): cadence_stats["deceptive_motion_density"],
        _feature_name("rn_harmony", "dominant_prolongation_ratio"): cadence_stats["dominant_prolongation_ratio"],
        _feature_name("rn_harmony", "mean_cadence_spacing"): cadence_stats["mean_cadence_spacing"],
        _feature_name("rn_harmony", "cadence_spacing_variance"): cadence_stats["cadence_spacing_variance"],
        _feature_name("rn_harmony", "harmonic_rhythm_mean"): rhythm_mean,
        _feature_name("rn_harmony", "harmonic_rhythm_median"): rhythm_median,
        _feature_name("rn_harmony", "harmonic_rhythm_variance"): rhythm_variance,
        _feature_name("rn_harmony", "harmonic_rhythm_entropy"): rhythm_entropy,
        _feature_name("rn_harmony", "short_harmony_ratio"): short_ratio,
        _feature_name("rn_harmony", "long_harmony_ratio"): long_ratio,
        _feature_name("rn_harmony", "rn_bigram_entropy"): _rn_bigram_entropy(events),
        _feature_name("rn_harmony", "circle_of_fifths_motion_ratio"): motion_ratios["circle"],
        _feature_name("rn_harmony", "root_motion_step_ratio"): motion_ratios["step"],
        _feature_name("rn_harmony", "root_motion_fifth_ratio"): motion_ratios["fifth"],
        _feature_name("rn_harmony", "root_motion_third_ratio"): motion_ratios["third"],
    }
    texture_features = {
        _feature_name("harmony_texture", slug): value
        for slug, value in _texture_features(score, events).items()
    }
    melody_features = {
        _feature_name("harmony_melody", slug): value
        for slug, value in _melody_features(score, events, analysis_result).items()
    }
    return {**rn_features, **texture_features, **melody_features}


def extract_rn_harmony_feature_families(score, analysis_result: RomanNumeralAnalysisResult) -> dict[str, dict[str, float]]:
    features = extract_rn_harmony_features(score, analysis_result)
    families: dict[str, dict[str, float]] = {
        "experimental_rn_harmony": {},
        "experimental_harmony_texture": {},
        "experimental_harmony_melody": {},
    }
    for name, value in features.items():
        if name.startswith("experimental__rn_harmony__"):
            families["experimental_rn_harmony"][name] = value
        elif name.startswith("experimental__harmony_texture__"):
            families["experimental_harmony_texture"][name] = value
        elif name.startswith("experimental__harmony_melody__"):
            families["experimental_harmony_melody"][name] = value
    return families
