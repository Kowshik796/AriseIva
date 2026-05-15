"""
arise-iva | predictor.py — Final Clean Version
Uses label_names from the bundle (stored during training).
predict_proba returns float array indexed 0..N → mapped to label_names[idx].
"""
from __future__ import annotations
import numpy as np


class GesturePredictor:
    CONFIDENCE_THRESHOLD = 0.35

    def __init__(self, model, scaler=None, labels: list[str] = None) -> None:
        self._model  = model
        self._scaler = scaler
        # labels come from the bundle — always real gesture names
        self._labels = labels or []
        print(f"[Predictor] {len(self._labels)} gestures : {self._labels}")

    def predict(self, vector: list[float]) -> tuple[str, float]:
        if not vector:
            return "Unknown", 0.0

        x = np.array(vector, dtype=np.float32).reshape(1, -1)

        # apply scaler (mandatory for MLP)
        if self._scaler is not None:
            x = self._scaler.transform(x)

        proba = self._model.predict_proba(x)[0]   # shape: (n_classes,)
        idx   = int(np.argmax(proba))
        conf  = float(proba[idx])

        # map integer index → gesture name using our bundle labels
        if idx < len(self._labels):
            label = self._labels[idx]
        else:
            label = "Unknown"

        return (label, conf) if conf >= self.CONFIDENCE_THRESHOLD else ("Unknown", conf)

    @property
    def labels(self) -> list[str]:
        return list(self._labels)