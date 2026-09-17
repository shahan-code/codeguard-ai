import time

GOOD_CODE = "def add(a, b):\n    return a + b\n"


def _wait_for_completion(client, headers, analysis_id, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        resp = client.get(f"/api/analysis/{analysis_id}/status", headers=headers)
        assert resp.status_code == 200
        status = resp.json()["status"]
        if status in ("COMPLETED", "FAILED"):
            return status
        time.sleep(0.2)
    raise TimeoutError("Analysis did not complete in time")


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_register_and_login(client):
    email = "flow_user@example.com"
    resp = client.post("/api/auth/register", json={"email": email, "password": "password123"})
    assert resp.status_code == 201
    assert "access_token" in resp.json()

    resp2 = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert resp2.status_code == 200

    resp3 = client.post("/api/auth/login", json={"email": email, "password": "wrongpass"})
    assert resp3.status_code == 401


def test_duplicate_registration_rejected(client):
    email = "dup_user@example.com"
    client.post("/api/auth/register", json={"email": email, "password": "password123"})
    resp = client.post("/api/auth/register", json={"email": email, "password": "password123"})
    assert resp.status_code == 400


def test_analysis_requires_auth(client):
    resp = client.post("/api/analysis", json={"code": GOOD_CODE})
    assert resp.status_code == 401


def test_full_analysis_lifecycle(client, auth_headers):
    resp = client.post("/api/analysis", json={"code": GOOD_CODE, "filename": "good.py"}, headers=auth_headers)
    assert resp.status_code == 202
    analysis_id = resp.json()["id"]

    final_status = _wait_for_completion(client, auth_headers, analysis_id)
    assert final_status == "COMPLETED"

    detail = client.get(f"/api/analysis/{analysis_id}", headers=auth_headers).json()
    assert detail["quality_score"] is not None
    assert detail["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert detail["ai_explanation"]  # deterministic fallback always present


def test_empty_code_rejected(client, auth_headers):
    resp = client.post("/api/analysis", json={"code": "   "}, headers=auth_headers)
    assert resp.status_code == 422


def test_invalid_syntax_marks_failed(client, auth_headers):
    resp = client.post("/api/analysis", json={"code": "def broken(:\n  pass"}, headers=auth_headers)
    assert resp.status_code == 202
    analysis_id = resp.json()["id"]
    final_status = _wait_for_completion(client, auth_headers, analysis_id)
    assert final_status == "FAILED"

    detail = client.get(f"/api/analysis/{analysis_id}", headers=auth_headers).json()
    assert detail["error_message"] is not None


def test_oversized_code_rejected(client, auth_headers):
    huge_code = "x = 1\n" * 20000
    resp = client.post("/api/analysis", json={"code": huge_code}, headers=auth_headers)
    assert resp.status_code == 422


def test_unsupported_language_rejected(client, auth_headers):
    resp = client.post("/api/analysis", json={"code": GOOD_CODE, "language": "java"}, headers=auth_headers)
    assert resp.status_code == 422


def test_cache_hit_on_identical_code(client, auth_headers):
    code = "def unique_fn_for_cache_test():\n    return 42\n"
    resp1 = client.post("/api/analysis", json={"code": code}, headers=auth_headers)
    id1 = resp1.json()["id"]
    _wait_for_completion(client, auth_headers, id1)

    resp2 = client.post("/api/analysis", json={"code": code}, headers=auth_headers)
    assert resp2.status_code == 202
    assert resp2.json()["from_cache"] is True
    assert resp2.json()["status"] == "COMPLETED"


def test_history_isolated_per_user(client):
    email_a = "user_a@example.com"
    email_b = "user_b@example.com"
    token_a = client.post("/api/auth/register", json={"email": email_a, "password": "password123"}).json()["access_token"]
    token_b = client.post("/api/auth/register", json={"email": email_b, "password": "password123"}).json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    resp = client.post("/api/analysis", json={"code": GOOD_CODE}, headers=headers_a)
    analysis_id = resp.json()["id"]
    _wait_for_completion(client, headers_a, analysis_id)

    # User B should not see User A's analysis
    resp_b = client.get(f"/api/analysis/{analysis_id}", headers=headers_b)
    assert resp_b.status_code == 404

    history_b = client.get("/api/analysis", headers=headers_b).json()
    assert all(item["id"] != analysis_id for item in history_b)


def test_pdf_report_generation(client, auth_headers):
    resp = client.post("/api/analysis", json={"code": GOOD_CODE}, headers=auth_headers)
    analysis_id = resp.json()["id"]
    _wait_for_completion(client, auth_headers, analysis_id)

    pdf_resp = client.get(f"/api/analysis/{analysis_id}/report", headers=auth_headers)
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content[:4] == b"%PDF"


def test_pdf_report_requires_completed_analysis(client, auth_headers):
    resp = client.post("/api/analysis", json={"code": "def broken(:\n  pass"}, headers=auth_headers)
    analysis_id = resp.json()["id"]
    _wait_for_completion(client, auth_headers, analysis_id)

    pdf_resp = client.get(f"/api/analysis/{analysis_id}/report", headers=auth_headers)
    assert pdf_resp.status_code == 400


def test_llm_fallback_when_no_api_key(client, auth_headers):
    # OPENAI_API_KEY is forced empty in conftest, so this must use the
    # deterministic fallback and must not crash or block.
    code = 'password = "hardcoded123"\ndef run(x):\n    return eval(x)\n'
    resp = client.post("/api/analysis", json={"code": code}, headers=auth_headers)
    analysis_id = resp.json()["id"]
    _wait_for_completion(client, auth_headers, analysis_id)

    detail = client.get(f"/api/analysis/{analysis_id}", headers=auth_headers).json()
    assert detail["ai_explanation"]
    assert detail["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
