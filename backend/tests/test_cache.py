from app.services.cache_service import compute_code_hash


def test_same_code_same_hash():
    h1 = compute_code_hash("print(1)", "python")
    h2 = compute_code_hash("print(1)", "python")
    assert h1 == h2


def test_different_code_different_hash():
    h1 = compute_code_hash("print(1)", "python")
    h2 = compute_code_hash("print(2)", "python")
    assert h1 != h2


def test_hash_is_sha256_length():
    h = compute_code_hash("print(1)", "python")
    assert len(h) == 64
