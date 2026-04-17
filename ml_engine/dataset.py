"""
Synthetic training dataset generator for disease prediction.
Each disease has weighted symptom probabilities; 1 000 samples per disease
= 15 000 rows total.
"""
import numpy as np
import pandas as pd

# ─── Master symptom list (30 features) ───────────────────────────────────────
SYMPTOMS = [
    'fever', 'cough', 'fatigue', 'body_ache', 'headache',
    'sore_throat', 'runny_nose', 'sneezing', 'congestion',
    'difficulty_breathing', 'chest_pain', 'nausea', 'vomiting',
    'diarrhea', 'abdominal_pain', 'frequent_urination', 'excessive_thirst',
    'blurred_vision', 'weight_loss', 'dizziness', 'joint_pain',
    'joint_swelling', 'stiffness', 'rash', 'chills',
    'loss_of_taste', 'loss_of_smell', 'pale_skin', 'wheezing',
    'indigestion',
]

# ─── Symptom probability per disease ─────────────────────────────────────────
DISEASE_SYMPTOM_PROBS: dict[str, dict[str, float]] = {
    'Influenza': {
        'fever': 0.90, 'cough': 0.85, 'fatigue': 0.85, 'body_ache': 0.80,
        'headache': 0.75, 'sore_throat': 0.60, 'chills': 0.70,
        'nausea': 0.40, 'congestion': 0.45, 'dizziness': 0.30,
    },
    'Common Cold': {
        'runny_nose': 0.90, 'sneezing': 0.88, 'sore_throat': 0.75,
        'congestion': 0.82, 'cough': 0.65, 'fatigue': 0.50,
        'headache': 0.45, 'fever': 0.20, 'body_ache': 0.25,
    },
    'Pneumonia': {
        'fever': 0.85, 'cough': 0.92, 'difficulty_breathing': 0.82,
        'chest_pain': 0.72, 'fatigue': 0.80, 'chills': 0.65,
        'nausea': 0.45, 'vomiting': 0.35,
    },
    'Type 2 Diabetes': {
        'frequent_urination': 0.90, 'excessive_thirst': 0.88,
        'fatigue': 0.80, 'blurred_vision': 0.65, 'weight_loss': 0.60,
        'dizziness': 0.40, 'headache': 0.35, 'nausea': 0.30,
    },
    'Hypertension': {
        'headache': 0.75, 'dizziness': 0.72, 'chest_pain': 0.55,
        'difficulty_breathing': 0.45, 'fatigue': 0.50,
        'blurred_vision': 0.35, 'nausea': 0.30,
    },
    'Malaria': {
        'fever': 0.95, 'chills': 0.90, 'headache': 0.80, 'nausea': 0.72,
        'vomiting': 0.65, 'fatigue': 0.80, 'body_ache': 0.65,
        'dizziness': 0.50,
    },
    'Typhoid Fever': {
        'fever': 0.95, 'headache': 0.80, 'abdominal_pain': 0.75,
        'fatigue': 0.80, 'nausea': 0.65, 'diarrhea': 0.55,
        'rash': 0.40, 'vomiting': 0.50, 'weight_loss': 0.45,
    },
    'Dengue Fever': {
        'fever': 0.95, 'headache': 0.85, 'joint_pain': 0.80,
        'rash': 0.70, 'nausea': 0.70, 'vomiting': 0.60,
        'fatigue': 0.80, 'body_ache': 0.75, 'chills': 0.55,
    },
    'Asthma': {
        'wheezing': 0.92, 'difficulty_breathing': 0.90, 'chest_pain': 0.65,
        'cough': 0.82, 'fatigue': 0.55,
    },
    'Urinary Tract Infection': {
        'frequent_urination': 0.90, 'abdominal_pain': 0.70,
        'fever': 0.60, 'fatigue': 0.55, 'nausea': 0.45, 'dizziness': 0.30,
    },
    'Migraine': {
        'headache': 0.95, 'nausea': 0.75, 'dizziness': 0.70,
        'vomiting': 0.55, 'fatigue': 0.65, 'blurred_vision': 0.50,
    },
    'Gastritis': {
        'abdominal_pain': 0.92, 'nausea': 0.85, 'indigestion': 0.82,
        'vomiting': 0.65, 'fatigue': 0.50, 'dizziness': 0.35,
    },
    'Anemia': {
        'fatigue': 0.90, 'pale_skin': 0.87, 'dizziness': 0.75,
        'difficulty_breathing': 0.60, 'headache': 0.55,
        'weight_loss': 0.40, 'chest_pain': 0.35,
    },
    'Rheumatoid Arthritis': {
        'joint_pain': 0.92, 'joint_swelling': 0.88, 'stiffness': 0.87,
        'fatigue': 0.75, 'fever': 0.40, 'weight_loss': 0.35,
        'body_ache': 0.60,
    },
    'COVID-19': {
        'fever': 0.80, 'cough': 0.75, 'fatigue': 0.80,
        'loss_of_taste': 0.72, 'loss_of_smell': 0.72,
        'difficulty_breathing': 0.60, 'body_ache': 0.65,
        'headache': 0.60, 'diarrhea': 0.35, 'nausea': 0.40,
    },
}

DISEASES = list(DISEASE_SYMPTOM_PROBS.keys())


def generate_dataset(samples_per_disease: int = 1000, seed: int = 42) -> pd.DataFrame:
    """Return a DataFrame with binary symptom columns + 'disease' label."""
    rng = np.random.default_rng(seed)
    rows = []
    for disease, symptom_probs in DISEASE_SYMPTOM_PROBS.items():
        for _ in range(samples_per_disease):
            row = {s: 0 for s in SYMPTOMS}
            for symptom, prob in symptom_probs.items():
                if symptom in row:
                    row[symptom] = int(rng.random() < prob)
            row['disease'] = disease
            rows.append(row)
    df = pd.DataFrame(rows)
    return df.sample(frac=1, random_state=seed).reset_index(drop=True)


if __name__ == '__main__':
    df = generate_dataset()
    print(f"Dataset shape: {df.shape}")
    print(df['disease'].value_counts())
