# Experimental Musicological Feature Report

Feature sets: `core,experimental_texture_v0`
Feature rows: `20`
Experimental features audited: `11`

## Overview

- Dataset size: 20 excerpts
- experimental_texture has the largest average variance among the experimental families (average variance 297.398116).
- experimental__texture__single_note_event_ratio is the strongest CLAP-aligned feature if you look at pairwise feature similarity.
- experimental__texture__onset_density_per_quarter has the largest CLAP-minus-core gap signal.
- experimental__texture__accompaniment_continuity_proxy is the strongest Mozart/Chopin separator in the row-level label check.

## Included Pieces

| excerpt_id | title | composer | measure_start | measure_end |
| --- | --- | --- | --- | --- |
| chopin-nocturne-e-flat-major-op-9-2-mvt1_m001_m032 | Nocturne No. 2. | Chopin, Fryderyk | 1 | 32 |
| chopin-nocturne-e-flat-major-op-9-2-mvt1_m001_m035_req064 | Nocturne No. 2. | Chopin, Fryderyk | 1 | 35 |
| chopin-prelude-a-major-op-28-7-mvt1_m001_m032 | Preludium No. 1 | Chopin, Fryderyk | 1 | 32 |
| chopin-prelude-a-major-op-28-7-mvt1_m001_m034_req064 | Preludium No. 1 | Chopin, Fryderyk | 1 | 34 |
| chopin-prelude-b-minor-op-28-6-mvt1_m001_m026_req032 | Preludium No. 6 | Chopin, Fryderyk | 1 | 26 |
| chopin-prelude-b-minor-op-28-6-mvt1_m001_m026_req064 | Preludium No. 6 | Chopin, Fryderyk | 1 | 26 |
| chopin-prelude-e-minor-op-28-4-mvt1_m001_m026_req032 | Prelude no. 4 | Chopin, Fryderyk | 1 | 26 |
| chopin-prelude-e-minor-op-28-4-mvt1_m001_m026_req064 | Prelude no. 4 | Chopin, Fryderyk | 1 | 26 |
| chopin-prelude-raindrop-d-flat-major-op-28-15-mvt1_m001_m032 | Prelude No. 15. | Chopin, Fryderyk | 1 | 32 |
| chopin-prelude-raindrop-d-flat-major-op-28-15-mvt1_m001_m064 | Prelude No. 15. | Chopin, Fryderyk | 1 | 64 |
| mozart-1st-movement-allegro-from-piano-sonata-facile-c-major-kv-545-mvt1_m001_m032 | Piano Sonata No. 15 in C major | Mozart, Wolfgang Amadeus | 1 | 32 |
| mozart-1st-movement-allegro-from-piano-sonata-facile-c-major-kv-545-mvt1_m001_m064 | Piano Sonata No. 15 in C major | Mozart, Wolfgang Amadeus | 1 | 64 |
| mozart-fantasy-d-minor-kv-397-385g-mvt1_m001_m032 | Fantasy in D minor | Wolfgang Amadeus Mozart (1756-1791) | 1 | 32 |
| mozart-fantasy-d-minor-kv-397-385g-mvt1_m001_m064 | Fantasy in D minor | Wolfgang Amadeus Mozart (1756-1791) | 1 | 64 |
| mozart-piano-sonata-a-minor-kv-310-300d-mvt1_m001_m032 | Piano Sonata No. 8 in A minor | Mozart, Wolfgang Amadeus | 1 | 32 |
| mozart-piano-sonata-a-minor-kv-310-300d-mvt1_m001_m064 | Piano Sonata No. 8 in A minor | Mozart, Wolfgang Amadeus | 1 | 64 |
| mozart-piano-sonata-f-major-kv-332-300k-mvt1_m001_m032 | Piano Sonata No. 12 in F major | Mozart, Wolfgang Amadeus | 1 | 32 |
| mozart-piano-sonata-f-major-kv-332-300k-mvt1_m001_m064 | Piano Sonata No. 12 in F major | Mozart, Wolfgang Amadeus | 1 | 64 |
| mozart-rondo-a-minor-kv-511-mvt1_m001_m032 | mozart_rondo-a-minor-kv-511-mvt1.musicxml | Music21 | 1 | 32 |
| mozart-rondo-a-minor-kv-511-mvt1_m001_m064 | mozart_rondo-a-minor-kv-511-mvt1.musicxml | Music21 | 1 | 64 |

## Audit Snapshot

| feature_name | family | min | max | mean | std | unique_values | missing_values | coefficient_of_variation | near_constant |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| experimental__texture__register_span_max | experimental_texture | 41.0 | 64.0 | 49.1 | 6.941901756723442 | 13 | 0 | 0.141382927835508 | False |
| experimental__texture__simultaneity_ratio | experimental_texture | 0.41509433962264153 | 1.0 | 0.848755274680147 | 0.17690570836414962 | 11 | 0 | 0.2084295834636391 | False |
| experimental__texture__left_right_register_gap_mean | experimental_texture | 12.40362607633499 | 28.456521739130434 | 16.001088517901056 | 3.5924656730021276 | 18 | 0 | 0.22451383035492198 | False |
| experimental__texture__single_note_event_ratio | experimental_texture | 0.3110236220472441 | 0.9893899204244032 | 0.752968989598328 | 0.18086430589185037 | 18 | 0 | 0.24020153338364253 | False |
| experimental__texture__register_span_mean | experimental_texture | 9.35897435897436 | 42.05555555555556 | 22.873735450467834 | 8.567109884777404 | 18 | 0 | 0.3745391697534117 | False |
| experimental__texture__max_notes_per_onset | experimental_texture | 62.0 | 243.0 | 127.85 | 53.2618766098229 | 18 | 0 | 0.4165966101667806 | False |
| experimental__texture__onset_density_per_quarter | experimental_texture | 0.0703125 | 0.3229166666666667 | 0.17763627310605745 | 0.07863442028279106 | 16 | 0 | 0.4426709641439196 | False |
| experimental__texture__mean_notes_per_onset | experimental_texture | 12.743589743589743 | 91.38888888888889 | 36.58726341600901 | 17.313024131543376 | 18 | 0 | 0.47319811636876735 | False |
| experimental__texture__arpeggiation_proxy | experimental_texture | 0.01073345259391771 | 0.1079607415485278 | 0.05206785936336243 | 0.025883274162423052 | 18 | 0 | 0.4971065543869051 | False |
| experimental__texture__bass_motion_rate | experimental_texture | 0.21875 | 2.28125 | 0.8605453846338789 | 0.48021743448616283 | 18 | 0 | 0.558038475437844 | False |
| experimental__texture__accompaniment_continuity_proxy | experimental_texture | 0.0 | 0.40821917808219177 | 0.18129787074538875 | 0.13534741263851585 | 18 | 0 | 0.7465471716906987 | False |

## Near-Constant Features

_No rows available._

## Feature-To-Embedding Correlations

| feature_name | family | composer_label_correlation | same_composer_correlation | clap_similarity_correlation | symbolic_core_similarity_correlation | clap_minus_core_similarity_correlation | pairwise_similarity_mean | pairwise_similarity_std | pairwise_sample_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| experimental__texture__single_note_event_ratio | experimental_texture | -0.3432604675843228 | 0.03183624190812891 | 0.35319224174209873 | 0.3824152985992743 | 0.2859000877795466 | 0.8509333716172557 | 0.10981561465805566 | 190 |
| experimental__texture__onset_density_per_quarter | experimental_texture | 0.368312382512131 | 0.13508535596305857 | 0.29063096464967064 | -0.03380574380786348 | 0.2974808622342641 | 0.9198627066427363 | 0.05633847579300409 | 190 |
| experimental__texture__accompaniment_continuity_proxy | experimental_texture | -0.4745939454312433 | 0.14413379378164398 | 0.2082063806434174 | 0.17138487960823034 | 0.17818821785544728 | 0.8694373061054977 | 0.08229410807649527 | 190 |
| experimental__texture__simultaneity_ratio | experimental_texture | -0.13125979318231276 | 0.010013079296665166 | 0.07346713040069294 | 0.12368560936847228 | 0.05158849571694589 | 0.8528646756544569 | 0.11069593822270875 | 190 |
| experimental__texture__max_notes_per_onset | experimental_texture | -0.1943228563991526 | 0.14792688688142558 | 0.07035873502219804 | 0.21897721286964342 | 0.03145685993372587 | 0.054256217357427146 | 0.11506737448815088 | 190 |
| experimental__texture__left_right_register_gap_mean | experimental_texture | -0.177754168539225 | 0.012051145333085668 | 0.023493542808663344 | -0.017459488106272233 | 0.02667675975982587 | 0.35208451612496255 | 0.22345491607462745 | 190 |
| experimental__texture__register_span_mean | experimental_texture | -0.4104634216980084 | 0.06932184720882288 | 0.022299771627858175 | 0.1726665017781943 | -0.008467789960266718 | 0.15548165063951652 | 0.1571548743887152 | 190 |
| experimental__texture__arpeggiation_proxy | experimental_texture | -0.07233180577120539 | 0.079439955263675 | 0.012462886228707662 | 0.056029344999759485 | 0.0024936145838480315 | 0.9706907105672736 | 0.02016073949139548 | 190 |
| experimental__texture__register_span_max | experimental_texture | -0.18726856783026505 | 0.1986111535456954 | -0.11118302614055577 | 0.011789552809018066 | -0.1135994047394771 | 0.2153528786193273 | 0.245645090410004 | 190 |
| experimental__texture__mean_notes_per_onset | experimental_texture | -0.22721516989867202 | 0.13048094856926828 | -0.12954622907406563 | 0.2120217106198366 | -0.16776594249816268 | 0.12606561858613538 | 0.16397633222924354 | 190 |
| experimental__texture__bass_motion_rate | experimental_texture | -0.0895300993279203 | 0.0824918985986634 | -0.1890543920953213 | -0.10741146039037812 | -0.1704052034635999 | 0.6963269546286558 | 0.1679829059788924 | 190 |

## Family Summary

| family | feature_count | non_constant_feature_count | average_variance | strongest_clap_positive_feature | strongest_clap_positive_correlation | strongest_clap_negative_feature | strongest_clap_negative_correlation | strongest_composer_feature | strongest_composer_label_correlation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| experimental_texture | 11 | 11 | 297.3981158652888 | experimental__texture__single_note_event_ratio | 0.35319224174209873 | experimental__texture__bass_motion_rate | -0.1890543920953213 | experimental__texture__accompaniment_continuity_proxy | -0.4745939454312433 |

## Metadata Snapshot

| name | family | feature_set | status | expected_direction_mozart_vs_chopin | risk_level |
| --- | --- | --- | --- | --- | --- |
| experimental__chromaticism__accidental_density | chromaticism | experimental_chromaticism_v0 | experimental | higher_in_chopin | medium |
| experimental__chromaticism__out_of_key_pitch_ratio | chromaticism | experimental_chromaticism_v0 | experimental | higher_in_chopin | medium |
| experimental__chromaticism__chromatic_step_ratio | chromaticism | experimental_chromaticism_v0 | experimental | higher_in_chopin | medium |
| experimental__chromaticism__melodic_semitone_motion_ratio | chromaticism | experimental_chromaticism_v0 | experimental | higher_in_chopin | medium |
| experimental__chromaticism__pitch_class_entropy | chromaticism | experimental_chromaticism_v0 | experimental | higher_in_chopin | medium |
| experimental__chromaticism__non_diatonic_pitch_class_count | chromaticism | experimental_chromaticism_v0 | experimental | higher_in_chopin | medium |
| experimental__texture__mean_notes_per_onset | texture | experimental_texture_v0 | experimental | higher_in_chopin | medium |
| experimental__texture__max_notes_per_onset | texture | experimental_texture_v0 | experimental | higher_in_chopin | medium |
| experimental__texture__simultaneity_ratio | texture | experimental_texture_v0 | experimental | higher_in_chopin | medium |
| experimental__texture__single_note_event_ratio | texture | experimental_texture_v0 | experimental | higher_in_mozart | medium |
| experimental__texture__register_span_mean | texture | experimental_texture_v0 | experimental | higher_in_chopin | medium |
| experimental__texture__register_span_max | texture | experimental_texture_v0 | experimental | higher_in_chopin | medium |
| experimental__texture__onset_density_per_quarter | texture | experimental_texture_v0 | experimental | higher_in_chopin | medium |
| experimental__texture__left_right_register_gap_mean | texture | experimental_texture_v0 | experimental | higher_in_chopin | high |
| experimental__texture__bass_motion_rate | texture | experimental_texture_v0 | experimental | higher_in_chopin | medium |
| experimental__texture__accompaniment_continuity_proxy | texture | experimental_texture_v0 | experimental | higher_in_chopin | high |
| experimental__texture__arpeggiation_proxy | texture | experimental_texture_v0 | experimental | higher_in_chopin | high |
| experimental__rhythm_phrase__duration_entropy | rhythm_phrase | experimental_rhythm_phrase_v0 | experimental | higher_in_chopin | medium |
| experimental__rhythm_phrase__ioi_entropy | rhythm_phrase | experimental_rhythm_phrase_v0 | experimental | higher_in_chopin | medium |
| experimental__rhythm_phrase__short_note_ratio | rhythm_phrase | experimental_rhythm_phrase_v0 | experimental | higher_in_chopin | medium |
| experimental__rhythm_phrase__long_note_ratio | rhythm_phrase | experimental_rhythm_phrase_v0 | experimental | higher_in_mozart | medium |
| experimental__rhythm_phrase__measure_density_variance | rhythm_phrase | experimental_rhythm_phrase_v0 | experimental | higher_in_chopin | medium |
| experimental__rhythm_phrase__measure_density_regularity | rhythm_phrase | experimental_rhythm_phrase_v0 | experimental | higher_in_mozart | medium |
| experimental__rhythm_phrase__four_bar_density_periodicity_score | rhythm_phrase | experimental_rhythm_phrase_v0 | experimental | higher_in_mozart | medium |
| experimental__rhythm_phrase__repeated_rhythm_pattern_ratio | rhythm_phrase | experimental_rhythm_phrase_v0 | experimental | higher_in_mozart | medium |
| experimental__rhythm_phrase__rest_punctuation_ratio | rhythm_phrase | experimental_rhythm_phrase_v0 | experimental | higher_in_mozart | medium |
| experimental__rhythm_phrase__end_of_measure_long_note_ratio | rhythm_phrase | experimental_rhythm_phrase_v0 | experimental | higher_in_mozart | medium |
| experimental__harmony_light__chordified_event_count | harmony_light | experimental_harmony_light_v0 | experimental | unclear | medium |
| experimental__harmony_light__triad_ratio | harmony_light | experimental_harmony_light_v0 | experimental | higher_in_mozart | medium |
| experimental__harmony_light__seventh_chord_ratio | harmony_light | experimental_harmony_light_v0 | experimental | higher_in_chopin | medium |
| experimental__harmony_light__dissonant_verticality_ratio | harmony_light | experimental_harmony_light_v0 | experimental | higher_in_chopin | medium |
| experimental__harmony_light__chord_common_name_entropy | harmony_light | experimental_harmony_light_v0 | experimental | higher_in_chopin | medium |
| experimental__harmony_light__harmonic_rhythm_mean | harmony_light | experimental_harmony_light_v0 | experimental | higher_in_mozart | medium |
| experimental__harmony_light__harmonic_rhythm_variance | harmony_light | experimental_harmony_light_v0 | experimental | higher_in_chopin | medium |
| experimental__harmony_light__vertical_chromaticity_ratio | harmony_light | experimental_harmony_light_v0 | experimental | higher_in_chopin | medium |
| experimental__harmony_heavy__tonic_ratio | harmony_heavy | experimental_harmony_heavy_v0 | experimental | higher_in_mozart | high |
| experimental__harmony_heavy__dominant_ratio | harmony_heavy | experimental_harmony_heavy_v0 | experimental | higher_in_mozart | high |
| experimental__harmony_heavy__predominant_ratio | harmony_heavy | experimental_harmony_heavy_v0 | experimental | higher_in_mozart | high |
| experimental__harmony_heavy__applied_dominant_ratio | harmony_heavy | experimental_harmony_heavy_v0 | experimental | higher_in_chopin | high |
| experimental__harmony_heavy__secondary_function_ratio | harmony_heavy | experimental_harmony_heavy_v0 | experimental | higher_in_chopin | high |
| experimental__harmony_heavy__modal_mixture_ratio | harmony_heavy | experimental_harmony_heavy_v0 | experimental | higher_in_chopin | high |
| experimental__harmony_heavy__chromatic_chord_ratio | harmony_heavy | experimental_harmony_heavy_v0 | experimental | higher_in_chopin | high |
| experimental__harmony_heavy__diminished_chord_ratio | harmony_heavy | experimental_harmony_heavy_v0 | experimental | higher_in_chopin | high |
| experimental__harmony_heavy__seventh_chord_ratio | harmony_heavy | experimental_harmony_heavy_v0 | experimental | higher_in_chopin | high |
| experimental__harmony_heavy__non_diatonic_root_ratio | harmony_heavy | experimental_harmony_heavy_v0 | experimental | higher_in_chopin | high |
| experimental__harmony_heavy__modulation_count | harmony_heavy | experimental_harmony_heavy_v0 | experimental | higher_in_chopin | high |
| experimental__harmony_heavy__local_key_count | harmony_heavy | experimental_harmony_heavy_v0 | experimental | higher_in_chopin | high |
| experimental__harmony_heavy__mean_harmonic_rhythm | harmony_heavy | experimental_harmony_heavy_v0 | experimental | higher_in_mozart | high |
| experimental__harmony_heavy__harmonic_rhythm_variance | harmony_heavy | experimental_harmony_heavy_v0 | experimental | higher_in_chopin | high |
| experimental__harmony_heavy__cadence_like_V_I_count | harmony_heavy | experimental_harmony_heavy_v0 | experimental | higher_in_mozart | high |
| experimental__harmony_heavy__deceptive_motion_count | harmony_heavy | experimental_harmony_heavy_v0 | experimental | higher_in_chopin | high |
| experimental__harmony_heavy__rn_backend_available | harmony_heavy | experimental_harmony_heavy_v0 | experimental | unclear | low |
| experimental__harmony_heavy__rn_event_count | harmony_heavy | experimental_harmony_heavy_v0 | experimental | unclear | low |
| experimental__syntax_interaction__non_chord_tone_ratio | syntax_interaction | experimental_syntax_interaction_v0 | experimental | higher_in_chopin | high |
| experimental__syntax_interaction__accented_non_chord_tone_ratio | syntax_interaction | experimental_syntax_interaction_v0 | experimental | higher_in_chopin | high |
| experimental__syntax_interaction__resolved_stepwise_ratio | syntax_interaction | experimental_syntax_interaction_v0 | experimental | higher_in_mozart | high |
| experimental__syntax_interaction__mean_resolution_delay | syntax_interaction | experimental_syntax_interaction_v0 | experimental | unclear | high |
| experimental__syntax_interaction__unresolved_dissonance_ratio | syntax_interaction | experimental_syntax_interaction_v0 | experimental | higher_in_chopin | high |
| experimental__syntax_interaction__cadence_spacing_mean | syntax_interaction | experimental_syntax_interaction_v0 | experimental | unclear | high |
| experimental__syntax_interaction__cadence_spacing_variance | syntax_interaction | experimental_syntax_interaction_v0 | experimental | unclear | high |
| experimental__syntax_interaction__dominant_arrival_density | syntax_interaction | experimental_syntax_interaction_v0 | experimental | higher_in_mozart | high |
| experimental__syntax_interaction__dissonance_on_strong_beat_ratio | syntax_interaction | experimental_syntax_interaction_v0 | experimental | higher_in_chopin | high |

## Caveats

- These are musicologically motivated proxies, not definitive analytical labels.
- Pairwise correlations use a simple similarity transform based on absolute feature differences.
- The tiny Mozart/Chopin demo set is hypothesis-generating only.