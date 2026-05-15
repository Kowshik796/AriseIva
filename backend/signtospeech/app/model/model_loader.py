"""
arise-iva | model_loader.py — Final Clean Version
Reads the bundle { model, scaler, labels, n_features }.
Labels come from the bundle — never from model.classes_ (which stores ints).
"""
from __future__ import annotations
import os, pickle
from typing import Any


class ModelLoader:
    def __init__(self, model_path: str, labels_path: str) -> None:
        self.model_path  = model_path
        self.labels_path = labels_path

    def load(self) -> tuple[Any, Any, list[str], int]:
        """Returns (model, scaler, label_names, n_features)."""

        if not os.path.isfile(self.model_path):
            raise FileNotFoundError(
                f"Model not found: {self.model_path}\n"
                "Run: python scripts/train_model.py"
            )

        with open(self.model_path, "rb") as f:
            raw = pickle.load(f)

        # ── New bundle format ──────────────────────────────────────────────────
        if isinstance(raw, dict) and "labels" in raw:
            model      = raw["model"]
            scaler     = raw.get("scaler")
            labels     = [str(l) for l in raw["labels"]]
            n_features = int(raw.get("n_features", 0))

        # ── Old bare-model format (no labels inside) ───────────────────────────
        else:
            print("[ModelLoader] ⚠  Old model format — no labels in bundle.")
            print("[ModelLoader]    Retrain: python scripts/train_model.py")
            model  = raw if not isinstance(raw, dict) else raw.get("model", raw)
            scaler = raw.get("scaler") if isinstance(raw, dict) else None

            # fall back to label_classes.pkl
            if os.path.isfile(self.labels_path):
                with open(self.labels_path, "rb") as f:
                    lraw = pickle.load(f)
                labels = [str(l) for l in (lraw.tolist() if hasattr(lraw, "tolist") else lraw)]
            else:
                labels = [str(c) for c in model.classes_]

            n_features = getattr(model, "n_features_in_", 0)

        # ── Validate labels look like real names ───────────────────────────────
        if all(l.isdigit() for l in labels):
            print("[ModelLoader] ✗  Labels are integers, not gesture names!")
            print("[ModelLoader]    Retrain: python scripts/train_model.py")

        print(f"[ModelLoader] Algorithm  : {type(model).__name__}")
        print(f"[ModelLoader] Features   : {n_features}")
        print(f"[ModelLoader] Scaler     : {'yes ✓' if scaler else 'no'}")
        print(f"[ModelLoader] Labels ({len(labels)}) : {labels}")

        return model, scaler, labels, n_features