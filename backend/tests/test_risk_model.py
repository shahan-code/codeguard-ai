from app.analyzers.metrics import compute_metrics
from app.analyzers.smells import detect_smells
from app.analyzers.security import detect_security_issues
from app.ml.risk_model import get_risk_model

GOOD_CODE = "def add(a, b):\n    return a + b\n"


def _predict(code):
    m = compute_metrics(code)
    s = detect_smells(code, m)
    sec = detect_security_issues(code)
    return get_risk_model().predict(m, s, sec)


def test_risk_level_is_valid_category():
    pred = _predict(GOOD_CODE)
    assert pred.risk_level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")


def test_risk_score_bounds():
    pred = _predict(GOOD_CODE)
    assert 0 <= pred.risk_score <= 100


def test_contributions_reference_known_features():
    pred = _predict(GOOD_CODE)
    from app.ml.risk_model import FEATURE_NAMES
    names = {c["feature"] for c in pred.contributions}
    assert names.issubset(set(FEATURE_NAMES))


def test_model_holdout_accuracy_is_reasonable():
    model = get_risk_model()
    acc = model.evaluate_synthetic_holdout()
    # Documented as synthetic-data accuracy only, not a real-world benchmark.
    assert acc > 0.7
