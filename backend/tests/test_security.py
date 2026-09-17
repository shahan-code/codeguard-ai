from app.analyzers.security import detect_security_issues

HARDCODED_SECRET = 'password = "hunter2ishardcoded"\n'
EVAL_USAGE = 'def run(x):\n    return eval(x)\n'
SQL_INJECTION = 'def q(name):\n    query = "SELECT * FROM users WHERE name = \'" + name + "\'"\n    return query\n'
WEAK_HASH = 'import hashlib\ndef h(x):\n    return hashlib.md5(x.encode()).hexdigest()\n'
CLEAN_CODE = 'def add(a, b):\n    return a + b\n'


def test_hardcoded_secret_detected():
    findings = detect_security_issues(HARDCODED_SECRET)
    assert any(f["issue"] == "Hardcoded Credential" for f in findings)


def test_secret_value_is_masked():
    findings = detect_security_issues(HARDCODED_SECRET)
    f = next(f for f in findings if f["issue"] == "Hardcoded Credential")
    assert "hunter2ishardcoded" not in f["explanation"]


def test_eval_usage_detected():
    findings = detect_security_issues(EVAL_USAGE)
    assert any("eval" in f["issue"].lower() for f in findings)


def test_sql_injection_pattern_detected():
    findings = detect_security_issues(SQL_INJECTION)
    assert any("SQL" in f["issue"] for f in findings)


def test_weak_hash_detected():
    findings = detect_security_issues(WEAK_HASH)
    assert any("md5" in f["issue"].lower() for f in findings)


def test_clean_code_has_no_findings():
    findings = detect_security_issues(CLEAN_CODE)
    assert findings == []
