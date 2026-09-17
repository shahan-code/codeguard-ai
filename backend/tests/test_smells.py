from app.analyzers.metrics import compute_metrics
from app.analyzers.smells import detect_smells

LONG_FN = "def long_fn():\n" + "\n".join(f"    x{i} = {i}" for i in range(60)) + "\n    return 1\n"

TOO_MANY_PARAMS = "def many(a, b, c, d, e, f, g):\n    return a\n"

DUPLICATE_LOGIC = '''
def calc_one(a, b):
    total = a + b
    total = total * 2
    return total

def calc_two(a, b):
    total = a + b
    total = total * 2
    return total
'''


def test_long_function_detected():
    m = compute_metrics(LONG_FN)
    smells = detect_smells(LONG_FN, m)
    assert any(s["title"] == "Long Function" for s in smells)


def test_too_many_params_detected():
    m = compute_metrics(TOO_MANY_PARAMS)
    smells = detect_smells(TOO_MANY_PARAMS, m)
    assert any(s["title"] == "Too Many Parameters" for s in smells)


def test_duplicate_logic_detected():
    m = compute_metrics(DUPLICATE_LOGIC)
    smells = detect_smells(DUPLICATE_LOGIC, m)
    assert any(s["title"] == "Duplicate Logic" for s in smells)


def test_findings_have_no_fake_line_numbers():
    m = compute_metrics(LONG_FN)
    smells = detect_smells(LONG_FN, m)
    for s in smells:
        assert s["line"] is None or isinstance(s["line"], int)


def test_clean_code_has_few_smells():
    code = "def add(a, b):\n    return a + b\n"
    m = compute_metrics(code)
    smells = detect_smells(code, m)
    assert len(smells) == 0
