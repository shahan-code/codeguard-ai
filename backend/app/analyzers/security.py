"""
Basic Security Pattern Analysis.

This is intentionally NOT a complete security scanner — it detects a small
set of obvious, high-confidence dangerous patterns via AST inspection and
regex on string literals. Any detected secret value is masked before it is
ever stored, logged, or returned in an API response.
"""
import ast
import re
from typing import Any, Dict, List

SECRET_KEYWORDS = ("password", "passwd", "secret", "api_key", "apikey", "token", "auth_key")
SECRET_LITERAL_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9]{10,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS access key pattern
]

DANGEROUS_CALLS = {
    "eval": "Use of eval() can execute arbitrary code and is a common injection vector.",
    "exec": "Use of exec() can execute arbitrary code and is a common injection vector.",
    "pickle.loads": "Unpickling untrusted data can lead to arbitrary code execution.",
    "os.system": "os.system() with unsanitized input can lead to command injection.",
    "subprocess.call": "subprocess calls with shell=True or unsanitized input risk command injection.",
    "subprocess.Popen": "subprocess.Popen with shell=True or unsanitized input risks command injection.",
}


def _mask(value: str) -> str:
    if len(value) <= 4:
        return "*" * len(value)
    return value[:2] + "*" * (len(value) - 2)


def _call_full_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parts = []
        cur = func
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        return ".".join(reversed(parts))
    return ""


def detect_security_issues(source_code: str) -> List[Dict[str, Any]]:
    tree = ast.parse(source_code)
    findings: List[Dict[str, Any]] = []

    # 1. Hardcoded secrets via assignment to suspicious variable names
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and any(k in target.id.lower() for k in SECRET_KEYWORDS):
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str) and node.value.value:
                        masked = _mask(node.value.value)
                        findings.append({
                            "severity": "CRITICAL",
                            "line": node.lineno,
                            "issue": "Hardcoded Credential",
                            "explanation": f"Variable '{target.id}' is assigned a hardcoded value ({masked}).",
                            "recommendation": "Move secrets to environment variables or a secrets manager. Never commit credentials to source control.",
                        })

    # 2. Known secret-shaped string literals anywhere in the source
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            for pattern in SECRET_LITERAL_PATTERNS:
                if pattern.search(node.value):
                    findings.append({
                        "severity": "CRITICAL",
                        "line": node.lineno,
                        "issue": "Possible API Key / Secret Literal",
                        "explanation": f"A string literal matches a known secret pattern ({_mask(node.value)}).",
                        "recommendation": "Remove the secret from source code and rotate it immediately if it was ever committed.",
                    })
                    break

    # 3. Dangerous function calls
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _call_full_name(node)
            if name in DANGEROUS_CALLS:
                findings.append({
                    "severity": "HIGH",
                    "line": node.lineno,
                    "issue": f"Dangerous Call: {name}()",
                    "explanation": DANGEROUS_CALLS[name],
                    "recommendation": f"Avoid {name}() with untrusted input, or replace it with a safer, purpose-built alternative.",
                })
            # shell=True detection for subprocess calls
            if name.startswith("subprocess."):
                for kw in node.keywords:
                    if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        findings.append({
                            "severity": "HIGH",
                            "line": node.lineno,
                            "issue": "subprocess shell=True",
                            "explanation": "shell=True combined with untrusted input allows command injection.",
                            "recommendation": "Use shell=False and pass arguments as a list instead.",
                        })

    # 4. Weak crypto (hashlib.md5 / hashlib.sha1 used for security purposes)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _call_full_name(node)
            if name in ("hashlib.md5", "hashlib.sha1"):
                findings.append({
                    "severity": "MEDIUM",
                    "line": node.lineno,
                    "issue": f"Weak Hash Algorithm: {name}()",
                    "explanation": f"{name}() is cryptographically broken and unsuitable for passwords or signatures.",
                    "recommendation": "Use hashlib.sha256 or a dedicated password-hashing algorithm (e.g. bcrypt, PBKDF2, Argon2).",
                })

    # 5. String-formatted SQL construction pattern (heuristic)
    src_lines = source_code.splitlines()
    sql_kw = re.compile(r"(select|insert|update|delete)\s.+\s(from|into|set)\s", re.IGNORECASE)
    for i, line in enumerate(src_lines, start=1):
        if sql_kw.search(line) and ("%" in line or "+" in line or ".format(" in line or "f\"" in line or "f'" in line):
            findings.append({
                "severity": "HIGH",
                "line": i,
                "issue": "Possible SQL Injection Pattern",
                "explanation": "SQL query appears to be built via string concatenation/formatting instead of parameters.",
                "recommendation": "Use parameterized queries or an ORM instead of building SQL via string interpolation.",
            })

    return findings
