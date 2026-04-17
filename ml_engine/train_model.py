"""
Train and persist the disease-prediction model.
Run directly:  python ml_engine/train_model.py
"""
import os
import sys
import joblib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
from sklearn.pipeline import Pipeline

from ml_engine.dataset import generate_dataset, SYMPTOMS
from config import MODEL_DIR, MODEL_PATH, ENCODER_PATH, FEATURES_PATH


def train(samples_per_disease: int = 1000, verbose: bool = True) -> dict:
    """Train model, save artefacts, return evaluation metrics."""
    os.makedirs(MODEL_DIR, exist_ok=True)

    # ── Data ──────────────────────────────────────────────────────────────────
    if verbose:
        print("Generating training data …")
    df = generate_dataset(samples_per_disease)

    X = df[SYMPTOMS].values
    y = df["disease"].values

    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=0.20, random_state=42, stratify=y_enc
    )

    # ── Model ─────────────────────────────────────────────────────────────────
    if verbose:
        print("Training Random Forest classifier …")
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=20,
        min_samples_split=4,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # ── Evaluation ────────────────────────────────────────────────────────────
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    cv_scores = cross_val_score(model, X, y_enc, cv=5, scoring="accuracy")

    if verbose:
        print(f"\nTest accuracy : {acc:.4f}")
        print(f"CV  accuracy  : {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred, target_names=le.classes_))

    # ── Persist ───────────────────────────────────────────────────────────────
    joblib.dump(model,   MODEL_PATH)
    joblib.dump(le,      ENCODER_PATH)
    joblib.dump(SYMPTOMS, FEATURES_PATH)

    if verbose:
        print(f"\nSaved model to: {MODEL_PATH}")

    return {
        "accuracy":    round(acc, 4),
        "cv_mean":     round(float(cv_scores.mean()), 4),
        "cv_std":      round(float(cv_scores.std()),  4),
        "classes":     list(le.classes_),
    }


if __name__ == "__main__":
    train(verbose=True)
