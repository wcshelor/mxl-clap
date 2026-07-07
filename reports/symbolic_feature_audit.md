# Symbolic Feature Audit

Source CSV: `data/processed/symbolic_features_mozart_chopin.csv`
Near-constant threshold: coefficient of variation `< 0.05` or a single unique value.

- Numeric features audited: 163
- Near-constant features flagged: 26

## Most Stable Features

| feature_name | unique_values | coefficient_of_variation |
| --- | --- | --- |
| duration_bin_4_plus | 1 | 0.0 |
| harmony__common_name_augmented_fifth | 1 | 0.0 |
| harmony__common_name_diminished_minor_ninth_chord | 1 | 0.0 |
| harmony__common_name_incomplete_major_seventh_chord | 1 | 0.0 |
| harmony__common_name_incomplete_minor_seventh_chord | 1 | 0.0 |
| harmony__common_name_major_sixth | 1 | 0.0 |
| harmony__common_name_major_sixth_with_octave_doublings | 1 | 0.0 |
| harmony__common_name_major_third | 1 | 0.0 |
| harmony__common_name_major_thirteenth | 1 | 0.0 |
| harmony__common_name_minor_fourteenth | 1 | 0.0 |

## Most Variable Features

| feature_name | mean | std | coefficient_of_variation |
| --- | --- | --- | --- |
| interval_11 | 0.000478927203065125 | 0.0012671222754140519 | 2.6457513110645907 |
| pitch__melodic_interval_11 | 0.000478927203065125 | 0.0012671222754140519 | 2.6457513110645907 |
| pitch__pitch_class_10 | 0.0050527532112353245 | 0.008655066082679463 | 1.7129405931471222 |
| pitch_class_10 | 0.0050527532112353245 | 0.008655066082679463 | 1.7129405931471222 |
| duration_bin_2_4 | 0.022683526392667738 | 0.03837001111231855 | 1.6915364237511739 |
| rhythm__duration_bin_2_4 | 0.022683526392667738 | 0.03837001111231855 | 1.6915364237511739 |
| interval_10 | 0.010390161255581837 | 0.016850235764143875 | 1.6217492057778733 |
| pitch__melodic_interval_10 | 0.010390161255581837 | 0.016850235764143875 | 1.6217492057778733 |
| pitch__pitch_class_6 | 0.034505925501855085 | 0.05291889300163068 | 1.5336175521153808 |
| pitch_class_6 | 0.034505925501855085 | 0.05291889300163068 | 1.5336175521153808 |