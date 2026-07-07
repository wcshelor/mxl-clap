from __future__ import annotations

import pandas as pd

from score_embedding_lab.feature_audit import audit_numeric_features


def test_audit_numeric_features_flags_constant_columns():
    frame = pd.DataFrame(
        {
            "varying": [0.0, 1.0, 2.0, 3.0],
            "constant": [5.0, 5.0, 5.0, 5.0],
            "mixed": [1.0, 1.0, 2.0, 2.0],
        }
    )

    audit = audit_numeric_features(frame, cv_threshold=0.1).set_index("feature_name")

    assert bool(audit.loc["constant", "near_constant"]) is True
    assert bool(audit.loc["varying", "near_constant"]) is False
    assert audit.loc["constant", "unique_values"] == 1
    assert audit.loc["constant", "missing_values"] == 0
