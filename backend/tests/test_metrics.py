from app.analyzers.metrics import compute_metrics

SIMPLE_CODE = '''
def add(a, b):
    return a + b

class Foo:
    def bar(self):
        return 1
'''

NESTED_CODE = '''
def deep(a):
    if a:
        if a:
            if a:
                if a:
                    if a:
                        return 1
    return 0
'''


def test_basic_metrics_counts():
    m = compute_metrics(SIMPLE_CODE)
    assert m["function_count"] == 2
    assert m["class_count"] == 1
    assert m["loc"] > 0


def test_complexity_is_computed():
    m = compute_metrics(SIMPLE_CODE)
    assert m["avg_complexity"] >= 1

def test_deep_nesting_detected():
    m = compute_metrics(NESTED_CODE)
    assert m["max_nesting_depth"] >= 5


def test_function_params_counted():
    code = "def f(a, b, c):\n    return a + b + c\n"
    m = compute_metrics(code)
    fn = m["functions"][0]
    assert fn["params"] == 3


def test_syntax_error_raises():
    import pytest
    with pytest.raises(SyntaxError):
        compute_metrics("def broken(:\n  pass")
