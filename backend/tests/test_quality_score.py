from app.analyzers.metrics import compute_metrics
from app.analyzers.smells import detect_smells
from app.analyzers.security import detect_security_issues
from app.services.quality_score import compute_quality_score

GOOD_CODE = "def add(a, b):\n    return a + b\n"
RISKY_CODE = 'password = "supersecret1"\ndef run(x):\n    return eval(x)\n'


def _analyze(code):
    m = compute_metrics(code)
    s = detect_smells(code, m)
    sec = detect_security_issues(code)
    return compute_quality_score(m, s, sec)


def test_quality_score_is_deterministic():
    r1 = _analyze(GOOD_CODE)
    r2 = _analyze(GOOD_CODE)
    assert r1 == r2


def test_good_code_scores_higher_than_risky_code():
    good = _analyze(GOOD_CODE)
    risky = _analyze(RISKY_CODE)
    assert good["overall"] > risky["overall"]


def test_score_bounds():
    result = _analyze(RISKY_CODE)
    assert 0 <= result["overall"] <= 100
    for v in result["sub_scores"].values():
        assert 0 <= v <= 100


def test_sub_scores_present():
    result = _analyze(GOOD_CODE)
    expected_keys = {"maintainability", "complexity", "security", "readability", "structure"}
    assert set(result["sub_scores"].keys()) == expected_keys
