"""Reserved extension point for a future validated dosage model.

The current product intentionally predicts fertilizer category only.
"""


def calculate_dosage(*_args, **_kwargs):
    """Fail explicitly until validated agronomic prescription data exists."""
    raise NotImplementedError("Validated fertilizer dosage data is not available in this prototype.")