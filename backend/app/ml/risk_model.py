"""
Explainable defect-risk model.

Design note (see README "Limitations"): there is no real-world labeled
defect dataset bundled with this project. Training on a real dataset (e.g.
mined from GitHub issue trackers) is future work. To still demonstrate a
genuine, reproducible ML pipeline rather than a pure lookup table, we:

  1. Generate a synthetic dataset where the "ground truth" defect label is
     produced by a documented weighted-risk formula over normalized code
     features, plus random noise (so the model has to genuinely learn
     the relationship rather than memorize it).
  2. Train a scikit-learn LogisticRegression classifier on that dataset.
  3. Use the trained model's predicted probability as the ML-based risk
     signal, and report per-feature contributions (coefficient * value)
     for explainability.

This is clearly labeled as a heuristic/ML hybrid, per project requirements.
No fake accuracy numbers are invented — train.py reports real held-out
accuracy on the synthetic set only, and this is documented as synthetic,
not a real-world benchmark.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
from sklearn.linear_model import LogisticRegression

FEATURE_NAMES = [
    "avg_complexity",
    "max_complexity",
    "avg_function_length",
    "max_function_length",
    "max_nesting_depth",
    "avg_params",
    "smell_severity_score",
    "security_severity_score",
]

# Normalization caps used to squash raw metrics into a 0-1 range before
# feeding them to the model. These are documented, fixed constants.
FEATURE_CAPS = {
    "avg_complexity": 20.0,
    "max_complexity": 40.0,
    "avg_function_length": 100.0,
    "max_function_length": 200.0,
    "max_nesting_depth": 8.0,
    "avg_params": 10.0,
    "smell_severity_score": 20.0,
    "security_severity_score": 20.0,
}

SEVERITY_WEIGHTS = {"LOW": 1, "MEDIUM": 2, "HIGH": 4, "CRITICAL": 7}


def severity_score(findings: List[dict], key: str = "severity") -> float:
    return float(sum(SEVERITY_WEIGHTS.get(f.get(key, "LOW"), 1) for f in findings))


def build_feature_vector(metrics: dict, smells: List[dict], security: List[dict]) -> Dict[str, float]:
    raw = {
        "avg_complexity": metrics.get("avg_complexity", 0),
        "max_complexity": metrics.get("max_complexity", 0),
        "avg_function_length": metrics.get("avg_function_length", 0),
        "max_function_length": metrics.get("max_function_length", 0),
        "max_nesting_depth": metrics.get("max_nesting_depth", 0),
        "avg_params": metrics.get("avg_params", 0),
        "smell_severity_score": severity_score(smells),
        "security_severity_score": severity_score(security),
    }
    normalized = {}
    for k in FEATURE_NAMES:
        cap = FEATURE_CAPS[k]
        normalized[k] = max(0.0, min(1.0, raw[k] / cap))
    return normalized


def _synthetic_label(features: Dict[str, float], noise: float) -> int:
    """Weighted heuristic ground truth used only to generate training labels."""
    weights = {
        "avg_complexity": 0.20,
        "max_complexity": 0.15,
        "avg_function_length": 0.10,
        "max_function_length": 0.10,
        "max_nesting_depth": 0.15,
        "avg_params": 0.05,
        "smell_severity_score": 0.15,
        "security_severity_score": 0.10,
    }
    score = sum(features[k] * w for k, w in weights.items()) + noise
    return 1 if score > 0.45 else 0


def generate_synthetic_dataset(n_samples: int = 2000, seed: int = 42) -> Tuple[np.ndarray, np.ndarray]:
    rng = random.Random(seed)
    X, y = [], []
    for _ in range(n_samples):
        features = {k: rng.random() for k in FEATURE_NAMES}
        noise = rng.gauss(0, 0.08)
        label = _synthetic_label(features, noise)
        X.append([features[k] for k in FEATURE_NAMES])
        y.append(label)
    return np.array(X), np.array(y)


@dataclass
class RiskPrediction:
    risk_score: float  # 0-100
    risk_level: str
    contributions: List[Dict[str, float]]


class RiskModel:
    def __init__(self):
        self.model: LogisticRegression | None = None
        self._train()

    def _train(self):
        X, y = generate_synthetic_dataset()
        self.model = LogisticRegression(max_iter=1000)
        self.model.fit(X, y)

    def evaluate_synthetic_holdout(self, n_samples: int = 500, seed: int = 7) -> float:
        """Returns real accuracy on a *synthetic* holdout set (documented as such)."""
        X, y = generate_synthetic_dataset(n_samples=n_samples, seed=seed)
        preds = self.model.predict(X)
        return float((preds == y).mean())

    def predict(self, metrics: dict, smells: List[dict], security: List[dict]) -> RiskPrediction:
        features = build_feature_vector(metrics, smells, security)
        x = np.array([[features[k] for k in FEATURE_NAMES]])
        proba = float(self.model.predict_proba(x)[0][1])
        risk_score = round(proba * 100, 1)

        if risk_score >= 75:
            level = "CRITICAL"
        elif risk_score >= 50:
            level = "HIGH"
        elif risk_score >= 25:
            level = "MEDIUM"
        else:
            level = "LOW"

        coefs = self.model.coef_[0]
        contributions = []
        for i, name in enumerate(FEATURE_NAMES):
            contributions.append({
                "feature": name,
                "value": round(features[name], 3),
                "contribution": round(float(coefs[i] * features[name]), 4),
            })
        contributions.sort(key=lambda c: abs(c["contribution"]), reverse=True)

        return RiskPrediction(risk_score=risk_score, risk_level=level, contributions=contributions)


# Singleton instance — trained once per process.
_risk_model_instance: RiskModel | None = None


def get_risk_model() -> RiskModel:
    global _risk_model_instance
    if _risk_model_instance is None:
        _risk_model_instance = RiskModel()
    return _risk_model_instance
