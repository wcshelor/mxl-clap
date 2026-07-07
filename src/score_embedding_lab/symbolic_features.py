from __future__ import annotations

from collections import Counter, defaultdict
from math import log
from statistics import mean

from music21 import chord, note

from .feature_registry import (
    experimental_families_for_feature_sets,
    normalize_feature_sets,
)


PITCH_CLASS_COUNT = 12
MELODIC_INTERVAL_BINS = list(range(PITCH_CLASS_COUNT)) + ["12_plus"]
DURATION_BINS = [
    (0.0, 0.25, "duration_bin_lt_0_25"),
    (0.25, 0.5, "duration_bin_0_25_0_5"),
    (0.5, 1.0, "duration_bin_0_5_1"),
    (1.0, 2.0, "duration_bin_1_2"),
    (2.0, 4.0, "duration_bin_2_4"),
    (4.0, float("inf"), "duration_bin_4_plus"),
]
IOI_BINS = DURATION_BINS
VERTICAL_INTERVAL_BINS = list(range(PITCH_CLASS_COUNT)) + ["12_plus"]
COMMON_NAME_TOP_K = 8


def _iter_notes_and_chords(score):
    for element in score.recurse().notes:
        if isinstance(element, note.Note):
            yield element
        elif isinstance(element, chord.Chord):
            yield element


def _pitch_midi_values(element) -> list[int]:
    if isinstance(element, note.Note):
        return [int(element.pitch.midi)]
    if isinstance(element, chord.Chord):
        return [int(p.midi) for p in element.pitches]
    return []


def _representative_pitch_midi(element) -> int | None:
    values = _pitch_midi_values(element)
    if not values:
        return None
    return max(values)


def _safe_float(value, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _entropy_from_counts(counts: Counter) -> float:
    total = float(sum(counts.values()))
    if total <= 0:
        return 0.0

    entropy = 0.0
    for count in counts.values():
        if count <= 0:
            continue
        probability = float(count) / total
        entropy -= probability * log(probability)
    return float(entropy)


def _normalized_histogram(values: list[int | float], bins: list[int | str], prefix: str) -> dict[str, float]:
    if not values:
        return {f"{prefix}{bin_name}": 0.0 for bin_name in bins}

    counts = Counter(values)
    total = float(sum(counts.values())) or 1.0
    return {f"{prefix}{bin_name}": float(counts.get(bin_name, 0)) / total for bin_name in bins}


def _pitch_class_histogram(pitch_values: list[int], prefix: str) -> dict[str, float]:
    pitch_classes = [pitch % PITCH_CLASS_COUNT for pitch in pitch_values]
    return _normalized_histogram(pitch_classes, list(range(PITCH_CLASS_COUNT)), prefix)


def _interval_histogram(melodic_sequence: list[int], prefix: str) -> dict[str, float]:
    bins = {str(i): 0 for i in range(PITCH_CLASS_COUNT)}
    bins["12_plus"] = 0
    if len(melodic_sequence) < 2:
        return {f"{prefix}{name}": 0.0 for name in bins}

    intervals = [abs(b - a) for a, b in zip(melodic_sequence, melodic_sequence[1:])]
    for interval in intervals:
        key = str(interval) if interval < PITCH_CLASS_COUNT else "12_plus"
        bins[key] += 1

    total = float(len(intervals)) or 1.0
    return {f"{prefix}{name}": float(count) / total for name, count in bins.items()}


def _duration_histogram(durations: list[float], prefix: str) -> dict[str, float]:
    if not durations:
        return {f"{prefix}{name}": 0.0 for _, _, name in DURATION_BINS}

    counts = {name: 0 for _, _, name in DURATION_BINS}
    for duration in durations:
        for lower, upper, name in DURATION_BINS:
            if lower < duration <= upper or (lower == 0.0 and duration == 0.0):
                counts[name] += 1
                break

    total = float(len(durations)) or 1.0
    return {f"{prefix}{name}": float(count) / total for name, count in counts.items()}


def _ioi_histogram(iois: list[float], prefix: str) -> dict[str, float]:
    if not iois:
        return {f"{prefix}{name}": 0.0 for _, _, name in IOI_BINS}

    counts = {name: 0 for _, _, name in IOI_BINS}
    for ioi in iois:
        for lower, upper, name in IOI_BINS:
            if lower < ioi <= upper or (lower == 0.0 and ioi == 0.0):
                counts[name] += 1
                break

    total = float(len(iois)) or 1.0
    return {f"{prefix}{name}": float(count) / total for name, count in counts.items()}


def _unique_sorted_offsets(events: list[dict]) -> list[float]:
    return sorted({round(float(event["offset"]), 6) for event in events})


def _group_events_by_onset(events: list[dict]) -> list[tuple[float, list[dict]]]:
    grouped: dict[float, list[dict]] = defaultdict(list)
    for event in events:
        grouped[round(float(event["offset"]), 6)].append(event)
    return sorted(grouped.items(), key=lambda item: item[0])


def _collect_note_events(score) -> list[dict]:
    events: list[dict] = []
    for element in _iter_notes_and_chords(score):
        pitches = _pitch_midi_values(element)
        if not pitches:
            continue

        accidental_count = 0
        for pitch_obj in getattr(element, "pitches", [getattr(element, "pitch", None)]):
            if pitch_obj is None:
                continue
            accidental = getattr(pitch_obj, "accidental", None)
            alter = getattr(accidental, "alter", 0) if accidental is not None else 0
            if alter not in (None, 0):
                accidental_count += 1

        events.append(
            {
                "offset": _safe_float(getattr(element, "offset", 0.0)),
                "duration": _safe_float(getattr(element, "quarterLength", 0.0)),
                "pitches": pitches,
                "pitch_count": len(pitches),
                "melodic_pitch": _representative_pitch_midi(element),
                "is_chord": isinstance(element, chord.Chord),
                "accidental_count": accidental_count,
                "beat": getattr(element, "beat", None),
                "beat_strength": _safe_float(getattr(element, "beatStrength", 0.0), 0.0),
                "measure_number": getattr(element, "measureNumber", None),
            }
        )
    return events


def _highest_time(score) -> float:
    value = getattr(score, "highestTime", None)
    if value is not None:
        try:
            return float(value)
        except (TypeError, ValueError):
            pass

    end_times = []
    for element in score.recurse().notesAndRests:
        offset = _safe_float(getattr(element, "offset", 0.0))
        duration = _safe_float(getattr(element, "quarterLength", 0.0))
        end_times.append(offset + duration)
    return max(end_times, default=0.0)


def _compute_pitch_features(events: list[dict]) -> tuple[dict[str, float], dict[str, float]]:
    pitch_values = [pitch for event in events for pitch in event["pitches"]]
    melodic_sequence = [int(event["melodic_pitch"]) for event in events if event["melodic_pitch"] is not None]
    pitch_class_counts = Counter(pitch % PITCH_CLASS_COUNT for pitch in pitch_values)
    interval_counts = Counter(
        abs(b - a)
        for a, b in zip(melodic_sequence, melodic_sequence[1:])
    )
    total_pitches = float(len(pitch_values)) or 1.0
    accidental_count = float(sum(event["accidental_count"] for event in events))
    pitch_range = (max(pitch_values) - min(pitch_values)) if pitch_values else 0.0

    prefixed = {
        "pitch__note_count": float(len(pitch_values)),
        "pitch__mean_midi": float(mean(pitch_values)) if pitch_values else 0.0,
        "pitch__ambitus_semitones": float(pitch_range),
        "pitch__range_semitones": float(pitch_range),
        "pitch__pitch_class_entropy": _entropy_from_counts(pitch_class_counts),
        "pitch__melodic_interval_entropy": _entropy_from_counts(interval_counts),
        "pitch__chromatic_pitch_ratio": accidental_count / total_pitches,
        "pitch__accidental_density": accidental_count / total_pitches,
    }
    prefixed.update(_pitch_class_histogram(pitch_values, "pitch__pitch_class_"))
    prefixed.update(_interval_histogram(melodic_sequence, "pitch__melodic_interval_"))

    legacy = {
        "note_count": prefixed["pitch__note_count"],
        "ambitus_semitones": prefixed["pitch__ambitus_semitones"],
        "pitch_range_semitones": prefixed["pitch__range_semitones"],
        "mean_pitch": prefixed["pitch__mean_midi"],
    }
    legacy.update(
        {
            key.removeprefix("pitch__"): value
            for key, value in prefixed.items()
            if key.startswith("pitch__pitch_class_") and key.removeprefix("pitch__pitch_class_").isdigit()
        }
    )
    legacy.update(
        {
            f"interval_{key.removeprefix('pitch__melodic_interval_')}": value
            for key, value in prefixed.items()
            if key.startswith("pitch__melodic_interval_")
            and (
                key.removeprefix("pitch__melodic_interval_").isdigit()
                or key.removeprefix("pitch__melodic_interval_") == "12_plus"
            )
        }
    )
    return prefixed, legacy


def _compute_rhythm_features(events: list[dict]) -> tuple[dict[str, float], dict[str, float]]:
    durations = [float(event["duration"]) for event in events]
    onsets = _unique_sorted_offsets(events)
    iois = [round(b - a, 6) for a, b in zip(onsets, onsets[1:])]
    duration_counts = Counter(durations)
    ioi_counts = Counter(iois)
    short_count = sum(1 for duration in durations if duration <= 0.5)
    long_count = sum(1 for duration in durations if duration >= 1.0)
    beat_values = []
    for event in events:
        beat = event.get("beat")
        try:
            beat_values.append(float(beat))
        except (TypeError, ValueError):
            continue

    def _beat_bin(value: float) -> str:
        rounded = int(round(value))
        if abs(value - rounded) <= 0.25 and 1 <= rounded <= 4:
            return f"beat_position_{rounded}"
        return "beat_position_other"

    beat_counts = Counter(_beat_bin(value) for value in beat_values)
    prefixed = {
        "rhythm__duration_entropy": _entropy_from_counts(duration_counts),
        "rhythm__ioi_entropy": _entropy_from_counts(ioi_counts),
        "rhythm__short_note_ratio": short_count / float(len(durations) or 1),
        "rhythm__long_note_ratio": long_count / float(len(durations) or 1),
        "rhythm__rhythmic_diversity": (len(duration_counts) / float(len(durations) or 1)),
    }
    prefixed.update(_duration_histogram(durations, "rhythm__"))
    prefixed.update(_ioi_histogram(iois, "rhythm__ioi_bin_"))
    if beat_counts:
        beat_total = float(sum(beat_counts.values())) or 1.0
        prefixed.update({f"rhythm__{key}": float(value) / beat_total for key, value in beat_counts.items()})

    legacy = {
        "rhythmic_diversity": prefixed["rhythm__rhythmic_diversity"],
    }
    legacy.update({key.removeprefix("rhythm__"): value for key, value in prefixed.items() if key.startswith("rhythm__duration_bin_")})
    return prefixed, legacy


def _compute_texture_features(events: list[dict], total_duration: float) -> dict[str, float]:
    grouped = _group_events_by_onset(events)
    if not grouped:
        return {
            "texture__mean_notes_per_onset": 0.0,
            "texture__max_notes_per_onset": 0.0,
            "texture__simultaneity_ratio": 0.0,
            "texture__chord_event_ratio": 0.0,
            "texture__single_note_event_ratio": 0.0,
            "texture__onset_density_per_quarter": 0.0,
            "texture__mean_active_notes": 0.0,
            "texture__register_span_mean": 0.0,
            "texture__register_span_max": 0.0,
            "texture__bass_motion_rate": 0.0,
            **{f"texture__vertical_interval_{bin_name}": 0.0 for bin_name in VERTICAL_INTERVAL_BINS},
        }

    onset_note_counts: list[float] = []
    onset_spans: list[float] = []
    bass_pitches: list[float] = []
    vertical_interval_values: list[int | str] = []
    chord_events = 0
    single_note_events = 0

    for _, onset_events in grouped:
        pitch_counts = [int(event["pitch_count"]) for event in onset_events]
        onset_note_counts.append(float(sum(pitch_counts)))

        chord_events += sum(1 for event in onset_events if event["is_chord"])
        single_note_events += sum(1 for event in onset_events if not event["is_chord"])

        onset_pitches = sorted({pitch for event in onset_events for pitch in event["pitches"]})
        if onset_pitches:
            onset_spans.append(float(max(onset_pitches) - min(onset_pitches)))
            bass_pitches.append(float(min(onset_pitches)))
            for i, pitch_a in enumerate(onset_pitches):
                for pitch_b in onset_pitches[i + 1 :]:
                    interval = abs(int(pitch_b) - int(pitch_a))
                    vertical_interval_values.append(interval if interval < PITCH_CLASS_COUNT else "12_plus")
        else:
            onset_spans.append(0.0)

    active_sample_times = sorted({round(event["offset"], 6) for event in events} | {round(event["offset"] + event["duration"], 6) for event in events})
    active_counts = []
    for start, end in zip(active_sample_times, active_sample_times[1:]):
        if end <= start:
            continue
        active_count = 0
        for event in events:
            event_start = round(event["offset"], 6)
            event_end = round(event["offset"] + event["duration"], 6)
            if event_start <= start < event_end:
                active_count += int(event["pitch_count"])
        active_counts.append((active_count, end - start))

    total_weight = sum(span for _, span in active_counts)
    mean_active_notes = sum(count * span for count, span in active_counts) / total_weight if total_weight else 0.0
    bass_motion = 0.0
    if len(bass_pitches) > 1:
        bass_motion = sum(abs(b - a) for a, b in zip(bass_pitches, bass_pitches[1:])) / float(total_duration or 1.0)

    prefixed = {
        "texture__mean_notes_per_onset": float(mean(onset_note_counts)) if onset_note_counts else 0.0,
        "texture__max_notes_per_onset": float(max(onset_note_counts)) if onset_note_counts else 0.0,
        "texture__simultaneity_ratio": (sum(1 for count in onset_note_counts if count > 1) / float(len(onset_note_counts) or 1)),
        "texture__chord_event_ratio": chord_events / float(len(events) or 1),
        "texture__single_note_event_ratio": single_note_events / float(len(events) or 1),
        "texture__onset_density_per_quarter": float(len(grouped)) / float(total_duration or 1.0),
        "texture__mean_active_notes": float(mean_active_notes),
        "texture__register_span_mean": float(mean(onset_spans)) if onset_spans else 0.0,
        "texture__register_span_max": float(max(onset_spans)) if onset_spans else 0.0,
        "texture__bass_motion_rate": float(bass_motion),
    }
    prefixed.update(_normalized_histogram(vertical_interval_values, VERTICAL_INTERVAL_BINS, "texture__vertical_interval_"))
    return prefixed


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
        (upper - lower) % PITCH_CLASS_COUNT
        for index, lower in enumerate(pitch_classes)
        for upper in pitch_classes[index + 1 :]
    }
    return 1 not in intervals and 6 not in intervals


def _slugify_feature_token(value: str) -> str:
    token = "".join(character if character.isalnum() else "_" for character in value.strip().lower())
    token = "_".join(part for part in token.split("_") if part)
    return token or "other"


def _compute_harmony_features(score) -> dict[str, float]:
    try:
        chordified = score.chordify()
    except Exception:
        chordified = None

    if chordified is None:
        return {
            "harmony__chordified_event_count": 0.0,
            "harmony__triad_ratio": 0.0,
            "harmony__seventh_chord_ratio": 0.0,
            "harmony__dissonant_verticality_ratio": 0.0,
        }

    chordified_events = []
    for element in chordified.recurse().getElementsByClass(chord.Chord):
        pitches = _pitch_midi_values(element)
        if not pitches:
            continue
        chordified_events.append(element)

    harmonic_events = [event for event in chordified_events if len(getattr(event, "pitches", [])) >= 2]
    if not harmonic_events:
        common_name_features = {"harmony__chordified_event_count": float(len(chordified_events)), "harmony__triad_ratio": 0.0, "harmony__seventh_chord_ratio": 0.0, "harmony__dissonant_verticality_ratio": 0.0}
        return common_name_features

    triad_count = sum(1 for event in harmonic_events if _is_triad(event))
    seventh_count = sum(1 for event in harmonic_events if _is_seventh_chord(event))
    dissonant_count = sum(1 for event in harmonic_events if not _is_consonant_verticality(event))
    common_name_counts = Counter(str(getattr(event, "commonName", "other")) or "other" for event in harmonic_events)
    top_common_names = [name for name, _ in common_name_counts.most_common(COMMON_NAME_TOP_K)]
    common_name_features = {
        f"harmony__common_name_{_slugify_feature_token(name)}": float(common_name_counts.get(name, 0)) / float(len(harmonic_events) or 1)
        for name in top_common_names
    }
    if len(common_name_counts) > len(top_common_names):
        common_name_features["harmony__common_name_other"] = float(
            sum(count for name, count in common_name_counts.items() if name not in top_common_names)
        ) / float(len(harmonic_events) or 1)

    harmony_features = {
        "harmony__chordified_event_count": float(len(chordified_events)),
        "harmony__triad_ratio": triad_count / float(len(harmonic_events) or 1),
        "harmony__seventh_chord_ratio": seventh_count / float(len(harmonic_events) or 1),
        "harmony__dissonant_verticality_ratio": dissonant_count / float(len(harmonic_events) or 1),
    }
    harmony_features.update(common_name_features)
    return harmony_features


def _compute_metadata_features(score, total_duration: float) -> dict[str, float]:
    metadata = getattr(score, "metadata", None)
    title = getattr(metadata, "title", "") if metadata is not None else ""
    composer = getattr(metadata, "composer", "") if metadata is not None else ""
    parts = list(getattr(score, "parts", []))
    return {
        "metadata__has_metadata": 1.0 if metadata is not None else 0.0,
        "metadata__part_count": float(len(parts)),
        "metadata__highest_time_quarter_lengths": float(total_duration),
        "metadata__title_length": float(len(title or "")),
        "metadata__composer_length": float(len(composer or "")),
    }


def extract_symbolic_feature_families(
    score,
    feature_sets: str | list[str] | tuple[str, ...] | None = None,
) -> dict[str, dict[str, float]]:
    """Return grouped symbolic features keyed by family prefix."""
    events = _collect_note_events(score)
    total_duration = _highest_time(score)
    pitch_features, legacy_pitch = _compute_pitch_features(events)
    rhythm_features, legacy_rhythm = _compute_rhythm_features(events)
    texture_features = _compute_texture_features(events, total_duration)
    harmony_features = _compute_harmony_features(score)
    metadata_features = _compute_metadata_features(score, total_duration)

    families = {
        "metadata": metadata_features,
        "pitch": pitch_features,
        "rhythm": rhythm_features,
        "texture": texture_features,
        "harmony": harmony_features,
        "_legacy_pitch": legacy_pitch,
        "_legacy_rhythm": legacy_rhythm,
    }

    requested_feature_sets = normalize_feature_sets(feature_sets)
    requested_experimental_families = experimental_families_for_feature_sets(requested_feature_sets)
    if requested_experimental_families:
        from .experimental_musicological import extract_experimental_musicological_feature_families

        experimental_families = extract_experimental_musicological_feature_families(score)
        for family_name in requested_experimental_families:
            family_features = experimental_families.get(family_name, {})
            if family_features:
                families[family_name] = family_features

    return families


def extract_symbolic_features(score, feature_sets: str | list[str] | tuple[str, ...] | None = None) -> dict[str, float]:
    """Extract a flat, CSV-friendly symbolic feature dictionary."""
    families = extract_symbolic_feature_families(score, feature_sets=feature_sets)
    pitch = families["pitch"]
    rhythm = families["rhythm"]
    texture = families["texture"]
    harmony = families["harmony"]
    metadata = families["metadata"]

    features: dict[str, float] = {
        "note_count": float(pitch["pitch__note_count"]),
        "total_duration_quarter_lengths": float(metadata["metadata__highest_time_quarter_lengths"]),
        "note_density": float(pitch["pitch__note_count"]) / float(metadata["metadata__highest_time_quarter_lengths"] or 1.0),
        "ambitus_semitones": float(pitch["pitch__ambitus_semitones"]),
        "pitch_range_semitones": float(pitch["pitch__range_semitones"]),
        "mean_pitch": float(pitch["pitch__mean_midi"]),
        "rhythmic_diversity": float(rhythm["rhythm__rhythmic_diversity"]),
        "chordified_chord_count": float(harmony["harmony__chordified_event_count"]),
    }

    for key, value in pitch.items():
        if key.startswith("pitch__pitch_class_") and key.removeprefix("pitch__pitch_class_").isdigit():
            features[key.removeprefix("pitch__")] = value
        elif key.startswith("pitch__melodic_interval_") and (
            key.removeprefix("pitch__melodic_interval_").isdigit()
            or key.removeprefix("pitch__melodic_interval_") == "12_plus"
        ):
            features[f"interval_{key.removeprefix('pitch__melodic_interval_')}"] = value

    for key, value in rhythm.items():
        if key.startswith("rhythm__duration_bin_"):
            features[key.removeprefix("rhythm__")] = value

    for family_name in ("metadata", "pitch", "rhythm", "texture", "harmony"):
        for key, value in families[family_name].items():
            features[key] = value

    for family_name in experimental_families_for_feature_sets(feature_sets):
        for key, value in families.get(family_name, {}).items():
            features[key] = value

    return features
