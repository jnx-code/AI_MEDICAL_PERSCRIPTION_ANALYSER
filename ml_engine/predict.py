"""
PredictionEngine – loads the trained model and exposes a prediction interface.
The model is auto-trained on first use if artefacts are missing.
"""
import os
import sys
import numpy as np
import joblib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MODEL_PATH, ENCODER_PATH, FEATURES_PATH


class PredictionEngine:
    def __init__(self):
        self._model   = None
        self._encoder = None
        self._features: list[str] = []
        self._load()

    # ── Internal ──────────────────────────────────────────────────────────────
    def _load(self):
        if not (os.path.exists(MODEL_PATH) and
                os.path.exists(ENCODER_PATH) and
                os.path.exists(FEATURES_PATH)):
            self._train()
        self._model    = joblib.load(MODEL_PATH)
        self._encoder  = joblib.load(ENCODER_PATH)
        self._features = joblib.load(FEATURES_PATH)

    def _train(self):
        from ml_engine.train_model import train
        train(verbose=False)

    # ── Public API ────────────────────────────────────────────────────────────
    def predict(self, symptoms: list[str], top_k: int = 3) -> list[dict]:
        """
        Parameters
        ----------
        symptoms : list of symptom key strings present in the patient
        top_k    : number of top predictions to return

        Returns
        -------
        list of dicts  [{"disease": str, "confidence": float}, …]  (sorted desc)
        """
        vec = np.array([[1 if f in symptoms else 0 for f in self._features]])
        proba = self._model.predict_proba(vec)[0]
        top_idx = np.argsort(proba)[::-1][:top_k]
        return [
            {
                "disease":    self._encoder.inverse_transform([i])[0],
                "confidence": round(float(proba[i]) * 100, 1),
            }
            for i in top_idx
        ]

    @property
    def all_diseases(self) -> list[str]:
        return list(self._encoder.classes_)

    @property
    def all_symptoms(self) -> list[str]:
        return list(self._features)

    def retrain(self):
        """Force a retrain (useful from the UI)."""
        self._train()
        self._load()
