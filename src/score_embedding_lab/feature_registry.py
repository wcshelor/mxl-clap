from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Final


CORE_FEATURE_SET: Final[str] = "core"
EXPERIMENTAL_CHROMATICISM_FEATURE_SET: Final[str] = "experimental_chromaticism_v0"
EXPERIMENTAL_TEXTURE_FEATURE_SET: Final[str] = "experimental_texture_v0"
EXPERIMENTAL_RHYTHM_PHRASE_FEATURE_SET: Final[str] = "experimental_rhythm_phrase_v0"
EXPERIMENTAL_HARMONY_LIGHT_FEATURE_SET: Final[str] = "experimental_harmony_light_v0"
EXPERIMENTAL_HARMONY_HEAVY_FEATURE_SET: Final[str] = "experimental_harmony_heavy_v0"
EXPERIMENTAL_SYNTAX_INTERACTION_FEATURE_SET: Final[str] = "experimental_syntax_interaction_v0"
EXPERIMENTAL_MUSICOLOGICAL_ALL_FEATURE_SET: Final[str] = "experimental_musicological_all_v0"

LEGACY_EXPERIMENTAL_RHYTHM_FEATURE_SET: Final[str] = "experimental_rhythm_v0"
LEGACY_EXPERIMENTAL_PHRASE_FEATURE_SET: Final[str] = "experimental_phrase_v0"
LEGACY_EXPERIMENTAL_MUSICOLOGICAL_FEATURE_SET: Final[str] = "experimental_musicological_v0"

EXPERIMENTAL_FEATURE_SETS: Final[tuple[str, ...]] = (
    EXPERIMENTAL_CHROMATICISM_FEATURE_SET,
    EXPERIMENTAL_TEXTURE_FEATURE_SET,
    EXPERIMENTAL_RHYTHM_PHRASE_FEATURE_SET,
    EXPERIMENTAL_HARMONY_LIGHT_FEATURE_SET,
    EXPERIMENTAL_HARMONY_HEAVY_FEATURE_SET,
    EXPERIMENTAL_SYNTAX_INTERACTION_FEATURE_SET,
    EXPERIMENTAL_MUSICOLOGICAL_ALL_FEATURE_SET,
)

FEATURE_SET_TO_FAMILIES: Final[dict[str, tuple[str, ...]]] = {
    CORE_FEATURE_SET: (),
    EXPERIMENTAL_CHROMATICISM_FEATURE_SET: ("experimental_chromaticism",),
    EXPERIMENTAL_TEXTURE_FEATURE_SET: ("experimental_texture",),
    EXPERIMENTAL_RHYTHM_PHRASE_FEATURE_SET: ("experimental_rhythm_phrase",),
    EXPERIMENTAL_HARMONY_LIGHT_FEATURE_SET: ("experimental_harmony_light",),
    EXPERIMENTAL_HARMONY_HEAVY_FEATURE_SET: ("experimental_harmony_heavy",),
    EXPERIMENTAL_SYNTAX_INTERACTION_FEATURE_SET: ("experimental_syntax_interaction",),
    EXPERIMENTAL_MUSICOLOGICAL_ALL_FEATURE_SET: (
        "experimental_chromaticism",
        "experimental_texture",
        "experimental_rhythm_phrase",
        "experimental_harmony_light",
        "experimental_harmony_heavy",
        "experimental_syntax_interaction",
    ),
    LEGACY_EXPERIMENTAL_RHYTHM_FEATURE_SET: ("experimental_rhythm_phrase",),
    LEGACY_EXPERIMENTAL_PHRASE_FEATURE_SET: ("experimental_rhythm_phrase",),
    LEGACY_EXPERIMENTAL_MUSICOLOGICAL_FEATURE_SET: (
        "experimental_chromaticism",
        "experimental_texture",
        "experimental_rhythm_phrase",
        "experimental_harmony_light",
        "experimental_harmony_heavy",
        "experimental_syntax_interaction",
    ),
}

FEATURE_FAMILY_PREFIXES: Final[dict[str, tuple[str, ...]]] = {
    "metadata": ("metadata__",),
    "pitch": ("pitch__",),
    "rhythm": ("rhythm__",),
    "texture": ("texture__",),
    "harmony": ("harmony__",),
    "experimental_chromaticism": ("experimental__chromaticism__",),
    "experimental_texture": ("experimental__texture__",),
    "experimental_rhythm_phrase": ("experimental__rhythm_phrase__",),
    "experimental_harmony_light": ("experimental__harmony_light__",),
    "experimental_harmony_heavy": ("experimental__harmony_heavy__",),
    "experimental_syntax_interaction": ("experimental__syntax_interaction__",),
}

CORE_GLOBAL_PREFIXES: Final[tuple[str, ...]] = (
    "metadata__",
    "pitch__",
    "rhythm__",
    "texture__",
    "harmony__",
)

SIMILARITY_FAMILY_PREFIXES: Final[dict[str, tuple[str, ...]]] = {
    "pitch_similarity": FEATURE_FAMILY_PREFIXES["pitch"],
    "rhythm_similarity": FEATURE_FAMILY_PREFIXES["rhythm"],
    "texture_similarity": FEATURE_FAMILY_PREFIXES["texture"],
    "harmony_similarity": FEATURE_FAMILY_PREFIXES["harmony"],
    "experimental_chromaticism_similarity": FEATURE_FAMILY_PREFIXES["experimental_chromaticism"],
    "experimental_texture_similarity": FEATURE_FAMILY_PREFIXES["experimental_texture"],
    "experimental_rhythm_phrase_similarity": FEATURE_FAMILY_PREFIXES["experimental_rhythm_phrase"],
    "experimental_harmony_light_similarity": FEATURE_FAMILY_PREFIXES["experimental_harmony_light"],
    "experimental_harmony_heavy_similarity": FEATURE_FAMILY_PREFIXES["experimental_harmony_heavy"],
    "experimental_syntax_interaction_similarity": FEATURE_FAMILY_PREFIXES["experimental_syntax_interaction"],
    "experimental_musicological_all_similarity": (
        *FEATURE_FAMILY_PREFIXES["experimental_chromaticism"],
        *FEATURE_FAMILY_PREFIXES["experimental_texture"],
        *FEATURE_FAMILY_PREFIXES["experimental_rhythm_phrase"],
        *FEATURE_FAMILY_PREFIXES["experimental_harmony_light"],
        *FEATURE_FAMILY_PREFIXES["experimental_harmony_heavy"],
        *FEATURE_FAMILY_PREFIXES["experimental_syntax_interaction"],
    ),
}


def _feature_name(family: str, slug: str) -> str:
    return f"experimental__{family}__{slug}"


def _humanize_slug(slug: str) -> str:
    return slug.replace("_", " ")


def _make_metadata(
    *,
    name: str,
    family: str,
    feature_set: str,
    description: str,
    musicological_claim: str,
    known_limits: str,
    requires_key_estimation: bool,
    requires_chordify: bool,
    requires_roman_numeral_backend: bool,
    expected_direction_mozart_vs_chopin: str,
    risk_level: str,
) -> dict[str, object]:
    return {
        "name": name,
        "family": family,
        "feature_set": feature_set,
        "status": "experimental",
        "description": description,
        "musicological_claim": musicological_claim,
        "known_limits": known_limits,
        "requires_key_estimation": requires_key_estimation,
        "requires_chordify": requires_chordify,
        "requires_roman_numeral_backend": requires_roman_numeral_backend,
        "expected_direction_mozart_vs_chopin": expected_direction_mozart_vs_chopin,
        "risk_level": risk_level,
    }


_FAMILY_DEFAULTS: Final[dict[str, dict[str, object]]] = {
    "chromaticism": {
        "feature_set": EXPERIMENTAL_CHROMATICISM_FEATURE_SET,
        "musicological_claim": "May capture chromatic pitch inflection and key-relative pitch color.",
        "known_limits": "Key-relative measures depend on inferred tonal context and can be noisy in dense or modulatory excerpts.",
        "requires_key_estimation": False,
        "requires_chordify": False,
        "requires_roman_numeral_backend": False,
        "expected_direction_mozart_vs_chopin": "higher_in_chopin",
        "risk_level": "medium",
    },
    "texture": {
        "feature_set": EXPERIMENTAL_TEXTURE_FEATURE_SET,
        "musicological_claim": "May capture piano texture thickness, hand separation, and accompanimental activity.",
        "known_limits": "These are broad score-level proxies and are not a substitute for true voice separation.",
        "requires_key_estimation": False,
        "requires_chordify": False,
        "requires_roman_numeral_backend": False,
        "expected_direction_mozart_vs_chopin": "higher_in_chopin",
        "risk_level": "medium",
    },
    "rhythm_phrase": {
        "feature_set": EXPERIMENTAL_RHYTHM_PHRASE_FEATURE_SET,
        "musicological_claim": "May capture rhythmic regularity, density cycles, and phrase-like periodicity proxies.",
        "known_limits": "These measures are coarse and should be treated as hypothesis-generating rather than true phrase detection.",
        "requires_key_estimation": False,
        "requires_chordify": False,
        "requires_roman_numeral_backend": False,
        "expected_direction_mozart_vs_chopin": "unclear",
        "risk_level": "medium",
    },
    "harmony_light": {
        "feature_set": EXPERIMENTAL_HARMONY_LIGHT_FEATURE_SET,
        "musicological_claim": "May capture coarse vertical sonority and harmonic rhythm behavior from chordified score slices.",
        "known_limits": "Chordify-based verticalities collapse many contrapuntal details and can over-simplify short piano excerpts.",
        "requires_key_estimation": False,
        "requires_chordify": True,
        "requires_roman_numeral_backend": False,
        "expected_direction_mozart_vs_chopin": "higher_in_chopin",
        "risk_level": "medium",
    },
    "harmony_heavy": {
        "feature_set": EXPERIMENTAL_HARMONY_HEAVY_FEATURE_SET,
        "musicological_claim": "May capture a functional-harmony proxy based on automatic Roman numeral analysis.",
        "known_limits": "Roman numeral analysis is backend-dependent and can be unstable on fragments, chromatic passages, or non-idiomatic textures.",
        "requires_key_estimation": True,
        "requires_chordify": True,
        "requires_roman_numeral_backend": True,
        "expected_direction_mozart_vs_chopin": "higher_in_chopin",
        "risk_level": "high",
    },
    "syntax_interaction": {
        "feature_set": EXPERIMENTAL_SYNTAX_INTERACTION_FEATURE_SET,
        "musicological_claim": "May capture approximate dissonance preparation, resolution, and cadence-like motion.",
        "known_limits": "These are heuristic interaction proxies and do not claim to detect syntax in a strict theoretical sense.",
        "requires_key_estimation": False,
        "requires_chordify": True,
        "requires_roman_numeral_backend": False,
        "expected_direction_mozart_vs_chopin": "higher_in_chopin",
        "risk_level": "high",
    },
}


_FEATURE_OVERRIDES: Final[dict[str, dict[str, dict[str, object]]]] = {
    "chromaticism": {
        "accidental_density": {
            "musicological_claim": "May reflect denser notated chromatic inflection.",
            "known_limits": "Counts written accidentals only and can be distorted by enharmonic spelling or dense textures.",
        },
        "out_of_key_pitch_ratio": {
            "requires_key_estimation": True,
            "musicological_claim": "May indicate more non-diatonic pitch content relative to an inferred key.",
            "known_limits": "Depends on key inference and can be unstable in modulatory or fragmentary excerpts.",
        },
        "melodic_semitone_motion_ratio": {
            "musicological_claim": "May reflect more semitone motion in the extracted melodic stream.",
            "known_limits": "Uses a single representative pitch per event and can miss inner-voice or accompaniment chromaticism.",
        },
        "pitch_class_entropy": {
            "musicological_claim": "May reflect a broader spread of pitch classes.",
            "known_limits": "Pitch-class entropy is a coarse distribution proxy and does not distinguish function from ornament.",
        },
        "non_diatonic_pitch_class_count": {
            "requires_key_estimation": True,
            "musicological_claim": "May reflect how many pitch classes fall outside an inferred diatonic collection.",
            "known_limits": "A single wrong key estimate can shift the count substantially.",
        },
    },
    "texture": {
        "single_note_event_ratio": {
            "expected_direction_mozart_vs_chopin": "higher_in_mozart",
            "musicological_claim": "May reflect more monophonic or lightly textured writing.",
            "known_limits": "Event-based counts can miss contrapuntal layering when multiple lines align on the same onset.",
        },
        "left_right_register_gap_mean": {
            "risk_level": "high",
            "musicological_claim": "May reflect separation between upper and lower piano material.",
            "known_limits": "Depends on whether parts/staves can be separated cleanly; otherwise it falls back to a coarse register-gap proxy.",
        },
        "bass_motion_rate": {
            "musicological_claim": "May reflect how actively the bass line moves through the excerpt.",
            "known_limits": "Bass extraction is heuristic when the score does not encode separate staves or voices.",
        },
        "accompaniment_continuity_proxy": {
            "risk_level": "high",
            "musicological_claim": "May reflect sustained accompanimental support under the melody.",
            "known_limits": "This is a coarse lower-register sustain proxy, not a true accompaniment tracker.",
        },
        "arpeggiation_proxy": {
            "risk_level": "high",
            "musicological_claim": "May reflect broken-chord or arpeggiated piano figuration.",
            "known_limits": "Monotonic contour heuristics are only a loose proxy for idiomatic arpeggiation.",
        },
    },
    "rhythm_phrase": {
        "duration_entropy": {
            "expected_direction_mozart_vs_chopin": "higher_in_chopin",
            "musicological_claim": "May reflect a more varied duration palette.",
            "known_limits": "Short excerpts can look artificially simple or complex depending on segmentation.",
        },
        "ioi_entropy": {
            "expected_direction_mozart_vs_chopin": "higher_in_chopin",
            "musicological_claim": "May reflect less regular inter-onset spacing.",
            "known_limits": "Depends on notated onset grouping and ignores expressive timing not encoded in score form.",
        },
        "short_note_ratio": {
            "expected_direction_mozart_vs_chopin": "higher_in_chopin",
            "musicological_claim": "May reflect more surface-level short-duration activity.",
            "known_limits": "Thresholding is heuristic and may not map cleanly to style across tempi or meters.",
        },
        "long_note_ratio": {
            "expected_direction_mozart_vs_chopin": "higher_in_mozart",
            "musicological_claim": "May reflect more sustained notation or longer-valued gestures.",
            "known_limits": "Thresholding is heuristic and can be inflated by held accompaniment tones.",
        },
        "measure_density_variance": {
            "expected_direction_mozart_vs_chopin": "higher_in_chopin",
            "musicological_claim": "May reflect more uneven rhythmic density across measures.",
            "known_limits": "Needs stable measure annotation and is sensitive to pickup measures and segmentation.",
        },
        "measure_density_regularity": {
            "expected_direction_mozart_vs_chopin": "higher_in_mozart",
            "musicological_claim": "May reflect more even density across measures and clearer surface regularity.",
            "known_limits": "Derived from the same measure-density counts as variance and shares their segmentation sensitivity.",
        },
        "four_bar_density_periodicity_score": {
            "expected_direction_mozart_vs_chopin": "higher_in_mozart",
            "musicological_claim": "May reflect recurring density patterns at a four-bar horizon.",
            "known_limits": "This is a coarse proxy and is unreliable when excerpt boundaries do not align with phrase structure.",
        },
        "repeated_rhythm_pattern_ratio": {
            "expected_direction_mozart_vs_chopin": "higher_in_mozart",
            "musicological_claim": "May reflect repeated notated rhythm patterns across measures.",
            "known_limits": "Requires enough repeated measures to be meaningful and does not distinguish exact repetition from near repetition.",
        },
        "rest_punctuation_ratio": {
            "expected_direction_mozart_vs_chopin": "higher_in_mozart",
            "musicological_claim": "May reflect rhetorical punctuation by rests or brief gaps.",
            "known_limits": "Score-level rest encoding varies, so the measure is only a coarse punctuation proxy.",
        },
        "end_of_measure_long_note_ratio": {
            "expected_direction_mozart_vs_chopin": "higher_in_mozart",
            "musicological_claim": "May reflect long notes near the end of measures, which can function like cadential lengthening.",
            "known_limits": "The proxy depends on measure annotation and only approximates phrase endings.",
        },
    },
    "harmony_light": {
        "chordified_event_count": {
            "expected_direction_mozart_vs_chopin": "unclear",
            "musicological_claim": "May reflect the amount of chordified vertical activity in the excerpt.",
            "known_limits": "Chordification depends on score encoding and can collapse texture in different ways across scores.",
        },
        "triad_ratio": {
            "expected_direction_mozart_vs_chopin": "higher_in_mozart",
            "musicological_claim": "May reflect a higher share of simple triadic verticalities.",
            "known_limits": "Triad detection is coarse and can miss inversional or incomplete triads.",
        },
        "seventh_chord_ratio": {
            "expected_direction_mozart_vs_chopin": "higher_in_chopin",
            "musicological_claim": "May reflect a higher share of seventh-chord sonorities.",
            "known_limits": "The ratio depends on chordify behavior and simple chord-quality heuristics.",
        },
        "dissonant_verticality_ratio": {
            "expected_direction_mozart_vs_chopin": "higher_in_chopin",
            "musicological_claim": "May reflect a higher share of dissonant vertical sonorities.",
            "known_limits": "Vertical dissonance is approximated with simple interval checks and may overcount sparse textures.",
        },
        "chord_common_name_entropy": {
            "expected_direction_mozart_vs_chopin": "higher_in_chopin",
            "musicological_claim": "May reflect more varied vertical sonority types.",
            "known_limits": "Common-name labels are implementation-dependent and should not be treated as ground truth harmony labels.",
        },
        "harmonic_rhythm_mean": {
            "expected_direction_mozart_vs_chopin": "higher_in_mozart",
            "musicological_claim": "May reflect slower average harmonic change.",
            "known_limits": "Harmonic rhythm is based on chordified event spacing and is only a coarse score-level proxy.",
        },
        "harmonic_rhythm_variance": {
            "expected_direction_mozart_vs_chopin": "higher_in_chopin",
            "musicological_claim": "May reflect more irregular harmonic change rates.",
            "known_limits": "Short excerpts can make harmonic-rhythm variance unstable.",
        },
        "vertical_chromaticity_ratio": {
            "requires_key_estimation": True,
            "expected_direction_mozart_vs_chopin": "higher_in_chopin",
            "musicological_claim": "May reflect more chordified pitches outside an inferred diatonic collection.",
            "known_limits": "Depends on key inference and collapses all vertical chromatic detail into a single ratio.",
        },
    },
    "harmony_heavy": {
        "tonic_ratio": {
            "expected_direction_mozart_vs_chopin": "higher_in_mozart",
            "musicological_claim": "May reflect a higher share of tonic-function sonorities.",
            "known_limits": "Roman numeral labels are backend-dependent and fragments can distort function tallies.",
        },
        "dominant_ratio": {
            "expected_direction_mozart_vs_chopin": "higher_in_mozart",
            "musicological_claim": "May reflect a higher share of dominant-function sonorities.",
            "known_limits": "Dominant classification is approximate when the backend struggles with inversion or mixture.",
        },
        "predominant_ratio": {
            "expected_direction_mozart_vs_chopin": "higher_in_mozart",
            "musicological_claim": "May reflect a higher share of predominant-function sonorities.",
            "known_limits": "Function labels are a coarse reduction of the Roman numeral output.",
        },
        "applied_dominant_ratio": {
            "expected_direction_mozart_vs_chopin": "higher_in_chopin",
            "musicological_claim": "May reflect more tonicizations and applied dominant motion.",
            "known_limits": "Secondary-function parsing is backend-dependent and can overcount chromatic sequences.",
        },
        "secondary_function_ratio": {
            "expected_direction_mozart_vs_chopin": "higher_in_chopin",
            "musicological_claim": "May reflect more secondary-function harmony.",
            "known_limits": "This is sensitive to how the backend encodes slash-chord figures.",
        },
        "modal_mixture_ratio": {
            "expected_direction_mozart_vs_chopin": "higher_in_chopin",
            "musicological_claim": "May reflect more borrowed or mixture harmony.",
            "known_limits": "Mixture detection is heuristic unless the backend marks borrowed chords explicitly.",
        },
        "chromatic_chord_ratio": {
            "expected_direction_mozart_vs_chopin": "higher_in_chopin",
            "musicological_claim": "May reflect more chromatic vertical sonorities.",
            "known_limits": "The proxy collapses several different chromatic behaviors into one count.",
        },
        "diminished_chord_ratio": {
            "expected_direction_mozart_vs_chopin": "higher_in_chopin",
            "musicological_claim": "May reflect more diminished-sonority usage.",
            "known_limits": "Diminished-chord detection is backend-dependent and can be label-sensitive.",
        },
        "seventh_chord_ratio": {
            "expected_direction_mozart_vs_chopin": "higher_in_chopin",
            "musicological_claim": "May reflect more seventh-chord sonorities in the Roman numeral output.",
            "known_limits": "This count reflects the backend's labeling choices as much as the score itself.",
        },
        "non_diatonic_root_ratio": {
            "requires_key_estimation": True,
            "expected_direction_mozart_vs_chopin": "higher_in_chopin",
            "musicological_claim": "May reflect more chord roots outside the inferred diatonic collection.",
            "known_limits": "Relies on both key inference and root identification from the backend.",
        },
        "modulation_count": {
            "requires_key_estimation": True,
            "expected_direction_mozart_vs_chopin": "higher_in_chopin",
            "musicological_claim": "May reflect more local key changes.",
            "known_limits": "Measure-level key tracking is a rough proxy and can overcount brief tonicizations.",
        },
        "local_key_count": {
            "requires_key_estimation": True,
            "expected_direction_mozart_vs_chopin": "higher_in_chopin",
            "musicological_claim": "May reflect a larger set of inferred local keys.",
            "known_limits": "Short fragments can inflate or suppress local-key diversity depending on the backend.",
        },
        "mean_harmonic_rhythm": {
            "expected_direction_mozart_vs_chopin": "higher_in_mozart",
            "musicological_claim": "May reflect slower average Roman numeral change.",
            "known_limits": "Harmonic rhythm is only as stable as the backend chord segmentation.",
        },
        "harmonic_rhythm_variance": {
            "expected_direction_mozart_vs_chopin": "higher_in_chopin",
            "musicological_claim": "May reflect more irregular Roman numeral change.",
            "known_limits": "Variance can be dominated by a few unusually long or short harmonic spans.",
        },
        "cadence_like_V_I_count": {
            "expected_direction_mozart_vs_chopin": "higher_in_mozart",
            "musicological_claim": "May reflect more cadence-like dominant-to-tonic motion.",
            "known_limits": "Cadence recognition is approximate and should not be read as formal cadence detection.",
        },
        "deceptive_motion_count": {
            "expected_direction_mozart_vs_chopin": "higher_in_chopin",
            "musicological_claim": "May reflect more deceptive dominant motion.",
            "known_limits": "Deceptive-motion heuristics are backend-sensitive and can miss many non-canonical resolutions.",
        },
        "rn_backend_available": {
            "expected_direction_mozart_vs_chopin": "unclear",
            "risk_level": "low",
            "requires_key_estimation": False,
            "requires_chordify": False,
            "requires_roman_numeral_backend": False,
            "musicological_claim": "Indicates whether the Roman numeral backend returned usable analysis results.",
            "known_limits": "This is an infrastructure flag, not a musicological measurement.",
            "description": "Availability flag for the Roman numeral backend.",
        },
        "rn_event_count": {
            "expected_direction_mozart_vs_chopin": "unclear",
            "risk_level": "low",
            "requires_key_estimation": False,
            "requires_chordify": False,
            "requires_roman_numeral_backend": False,
            "musicological_claim": "Reports how many Roman numeral events the backend returned.",
            "known_limits": "Event counts reflect backend behavior and excerpt length as much as harmony.",
            "description": "Count of Roman numeral events returned by the backend.",
        },
    },
    "syntax_interaction": {
        "non_chord_tone_ratio": {
            "expected_direction_mozart_vs_chopin": "higher_in_chopin",
            "musicological_claim": "May reflect more dissonant surface notes relative to the chordified harmony.",
            "known_limits": "Chord-tone classification is approximate and depends on the chordification.",
        },
        "accented_non_chord_tone_ratio": {
            "expected_direction_mozart_vs_chopin": "higher_in_chopin",
            "musicological_claim": "May reflect more dissonant notes on stronger metric positions.",
            "known_limits": "Metric accent is approximated from score beat strength and can be unreliable when meter is sparse.",
        },
        "resolved_stepwise_ratio": {
            "expected_direction_mozart_vs_chopin": "higher_in_mozart",
            "musicological_claim": "May reflect a higher share of non-chord tones resolving by step.",
            "known_limits": "Resolution is approximated from the next melodic event and can miss true multi-voice resolution.",
        },
        "mean_resolution_delay": {
            "expected_direction_mozart_vs_chopin": "unclear",
            "risk_level": "high",
            "musicological_claim": "May reflect how quickly dissonances resolve when they do resolve.",
            "known_limits": "Resolution timing is heuristic and sensitive to note ordering and voice overlap.",
        },
        "unresolved_dissonance_ratio": {
            "expected_direction_mozart_vs_chopin": "higher_in_chopin",
            "musicological_claim": "May reflect more non-chord tones that do not resolve stepwise immediately.",
            "known_limits": "This is a local proxy and should not be treated as a strict dissonance-resolution analysis.",
        },
        "cadence_spacing_mean": {
            "expected_direction_mozart_vs_chopin": "unclear",
            "risk_level": "high",
            "musicological_claim": "May reflect the average distance between cadence-like events.",
            "known_limits": "Cadence spacing is based on heuristic dominant-to-tonic motion and is not a formal phrase detector.",
        },
        "cadence_spacing_variance": {
            "expected_direction_mozart_vs_chopin": "unclear",
            "risk_level": "high",
            "musicological_claim": "May reflect the regularity of cadence-like spacing.",
            "known_limits": "The variance can be unstable when only a few cadence-like events are detected.",
        },
        "dominant_arrival_density": {
            "expected_direction_mozart_vs_chopin": "higher_in_mozart",
            "musicological_claim": "May reflect how often dominant-like arrivals occur per unit duration.",
            "known_limits": "Dominant arrival detection is only a rough proxy for cadential tension.",
        },
        "dissonance_on_strong_beat_ratio": {
            "expected_direction_mozart_vs_chopin": "higher_in_chopin",
            "musicological_claim": "May reflect a higher share of dissonance landing on stronger beats.",
            "known_limits": "Strong-beat detection is approximated from beat strength and can be noisy in excerpted scores.",
        },
    },
}


def _build_family_metadata(family: str, family_defaults: dict[str, object], feature_slugs: Sequence[str]) -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    overrides = _FEATURE_OVERRIDES.get(family, {})
    for slug in feature_slugs:
        row_defaults = dict(family_defaults)
        row_defaults.update(overrides.get(slug, {}))
        description = str(row_defaults.pop("description", f"Experimental proxy for {_humanize_slug(slug)}."))
        rows[_feature_name(family, slug)] = _make_metadata(
            name=_feature_name(family, slug),
            family=family,
            feature_set=str(row_defaults["feature_set"]),
            description=description,
            musicological_claim=str(row_defaults["musicological_claim"]),
            known_limits=str(row_defaults["known_limits"]),
            requires_key_estimation=bool(row_defaults["requires_key_estimation"]),
            requires_chordify=bool(row_defaults["requires_chordify"]),
            requires_roman_numeral_backend=bool(row_defaults["requires_roman_numeral_backend"]),
            expected_direction_mozart_vs_chopin=str(row_defaults["expected_direction_mozart_vs_chopin"]),
            risk_level=str(row_defaults["risk_level"]),
        )
    return rows


_FEATURE_SLUGS: Final[dict[str, tuple[str, ...]]] = {
    "chromaticism": (
        "accidental_density",
        "out_of_key_pitch_ratio",
        "chromatic_step_ratio",
        "melodic_semitone_motion_ratio",
        "pitch_class_entropy",
        "non_diatonic_pitch_class_count",
    ),
    "texture": (
        "mean_notes_per_onset",
        "max_notes_per_onset",
        "simultaneity_ratio",
        "single_note_event_ratio",
        "register_span_mean",
        "register_span_max",
        "onset_density_per_quarter",
        "left_right_register_gap_mean",
        "bass_motion_rate",
        "accompaniment_continuity_proxy",
        "arpeggiation_proxy",
    ),
    "rhythm_phrase": (
        "duration_entropy",
        "ioi_entropy",
        "short_note_ratio",
        "long_note_ratio",
        "measure_density_variance",
        "measure_density_regularity",
        "four_bar_density_periodicity_score",
        "repeated_rhythm_pattern_ratio",
        "rest_punctuation_ratio",
        "end_of_measure_long_note_ratio",
    ),
    "harmony_light": (
        "chordified_event_count",
        "triad_ratio",
        "seventh_chord_ratio",
        "dissonant_verticality_ratio",
        "chord_common_name_entropy",
        "harmonic_rhythm_mean",
        "harmonic_rhythm_variance",
        "vertical_chromaticity_ratio",
    ),
    "harmony_heavy": (
        "tonic_ratio",
        "dominant_ratio",
        "predominant_ratio",
        "applied_dominant_ratio",
        "secondary_function_ratio",
        "modal_mixture_ratio",
        "chromatic_chord_ratio",
        "diminished_chord_ratio",
        "seventh_chord_ratio",
        "non_diatonic_root_ratio",
        "modulation_count",
        "local_key_count",
        "mean_harmonic_rhythm",
        "harmonic_rhythm_variance",
        "cadence_like_V_I_count",
        "deceptive_motion_count",
        "rn_backend_available",
        "rn_event_count",
    ),
    "syntax_interaction": (
        "non_chord_tone_ratio",
        "accented_non_chord_tone_ratio",
        "resolved_stepwise_ratio",
        "mean_resolution_delay",
        "unresolved_dissonance_ratio",
        "cadence_spacing_mean",
        "cadence_spacing_variance",
        "dominant_arrival_density",
        "dissonance_on_strong_beat_ratio",
    ),
}


EXPERIMENTAL_FEATURE_METADATA: Final[dict[str, dict[str, object]]] = {}
for family_name, family_defaults in _FAMILY_DEFAULTS.items():
    EXPERIMENTAL_FEATURE_METADATA.update(_build_family_metadata(family_name, family_defaults, _FEATURE_SLUGS[family_name]))


def normalize_feature_sets(feature_sets: Sequence[str] | str | None) -> tuple[str, ...]:
    if feature_sets is None:
        return (CORE_FEATURE_SET,)

    if isinstance(feature_sets, str):
        raw_items = [item.strip() for item in feature_sets.split(",")]
    else:
        raw_items = [str(item).strip() for item in feature_sets]

    normalized: list[str] = []
    for item in raw_items:
        if not item:
            continue
        if item == "all":
            normalized.append(CORE_FEATURE_SET)
            normalized.extend(EXPERIMENTAL_FEATURE_SETS)
            continue
        if item == CORE_FEATURE_SET or item in FEATURE_SET_TO_FAMILIES:
            normalized.append(item)
            continue
        raise ValueError(f"Unknown feature set: {item}")

    if not normalized:
        return (CORE_FEATURE_SET,)

    ordered: list[str] = []
    for item in normalized:
        if item not in ordered:
            ordered.append(item)
    return tuple(ordered)


def experimental_families_for_feature_sets(feature_sets: Sequence[str] | str | None) -> tuple[str, ...]:
    normalized = normalize_feature_sets(feature_sets)
    families: list[str] = []
    for feature_set in normalized:
        families.extend(FEATURE_SET_TO_FAMILIES.get(feature_set, ()))

    ordered: list[str] = []
    for family in families:
        if family not in ordered:
            ordered.append(family)
    return tuple(ordered)


def feature_family_for_column(column: str) -> str:
    for family, prefixes in FEATURE_FAMILY_PREFIXES.items():
        if any(column.startswith(prefix) for prefix in prefixes):
            return family
    return ""


def feature_metadata_for_columns(columns: Iterable[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for column in columns:
        metadata = EXPERIMENTAL_FEATURE_METADATA.get(column)
        if metadata is None:
            continue
        rows.append(metadata.copy())
    return rows
