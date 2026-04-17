import os
from dotenv import load_dotenv

load_dotenv()

# ─── Database ────────────────────────────────────────────────────────────────
DB_TYPE      = os.getenv("DB_TYPE",      "sqlite")   # "sqlite" or "mysql"
DB_HOST      = os.getenv("DB_HOST",      "localhost")
DB_PORT      = int(os.getenv("DB_PORT",  "3306"))
DB_USER      = os.getenv("DB_USER",      "root")
DB_PASSWORD  = os.getenv("DB_PASSWORD",  "")
DB_NAME      = os.getenv("DB_NAME",      "medical_prescription")
SQLITE_PATH  = os.getenv("SQLITE_PATH",  "medical_prescription.db")

# ─── ML Model ────────────────────────────────────────────────────────────────
MODEL_DIR      = "models"
MODEL_PATH     = os.path.join(MODEL_DIR, "disease_model.pkl")
ENCODER_PATH   = os.path.join(MODEL_DIR, "label_encoder.pkl")
FEATURES_PATH  = os.path.join(MODEL_DIR, "feature_names.pkl")

# ─── App ─────────────────────────────────────────────────────────────────────
APP_TITLE      = "AI Medical Prescription Assistance System"
APP_ICON       = "💊"
DOCTOR_NAME    = os.getenv("DOCTOR_NAME",   "Dr. Jojo")
HOSPITAL_NAME  = os.getenv("HOSPITAL_NAME", "AI Hospital")
