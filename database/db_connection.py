"""
DatabaseManager – SQLite (default) or MySQL backend.
All table creation, seeding, and CRUD operations live here.
"""
import os
import sys
import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_TYPE, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, SQLITE_PATH

# ─── Static reference data ────────────────────────────────────────────────────
DRUGS_SEED = [
    # (name, category, dosage_form, standard_dose, max_daily_dose, description)
    ('Paracetamol',        'Analgesic/Antipyretic',        'Tablet/Syrup',    '500–1000 mg',        '4000 mg',    'Fever and mild-to-moderate pain'),
    ('Ibuprofen',          'NSAID',                        'Tablet',          '200–400 mg',         '1200 mg',    'Anti-inflammatory, analgesic, antipyretic'),
    ('Amoxicillin',        'Antibiotic – Penicillin',      'Capsule/Syrup',   '250–500 mg',         '3000 mg',    'Broad-spectrum penicillin antibiotic'),
    ('Azithromycin',       'Antibiotic – Macrolide',       'Tablet',          '250–500 mg',         '500 mg',     'Macrolide antibiotic for respiratory infections'),
    ('Ciprofloxacin',      'Antibiotic – Fluoroquinolone', 'Tablet',          '250–500 mg',         '1500 mg',    'Fluoroquinolone antibiotic for UTI and typhoid'),
    ('Metformin',          'Antidiabetic – Biguanide',     'Tablet',          '500–1000 mg',        '3000 mg',    'First-line treatment for Type 2 Diabetes'),
    ('Glipizide',          'Antidiabetic – Sulfonylurea',  'Tablet',          '5–10 mg',            '40 mg',      'Stimulates insulin release for Type 2 Diabetes'),
    ('Sitagliptin',        'Antidiabetic – DPP-4',         'Tablet',          '100 mg',             '100 mg',     'DPP-4 inhibitor for Type 2 Diabetes'),
    ('Amlodipine',         'Antihypertensive – CCB',       'Tablet',          '5–10 mg',            '10 mg',      'Calcium channel blocker for hypertension'),
    ('Lisinopril',         'Antihypertensive – ACE',       'Tablet',          '5–40 mg',            '80 mg',      'ACE inhibitor for hypertension and heart failure'),
    ('Atenolol',           'Antihypertensive – Beta',      'Tablet',          '25–100 mg',          '200 mg',     'Beta-blocker for hypertension and angina'),
    ('Hydrochlorothiazide','Antihypertensive – Diuretic',  'Tablet',          '12.5–25 mg',         '50 mg',      'Thiazide diuretic for hypertension'),
    ('Chloroquine',        'Antimalarial',                 'Tablet',          '500 mg',             '1500 mg',    'Treatment and prevention of malaria'),
    ('Artemether',         'Antimalarial',                 'Tablet',          '20 mg',              '80 mg',      'Artemisinin-based antimalarial'),
    ('Lumefantrine',       'Antimalarial',                 'Tablet',          '120 mg',             '480 mg',     'Combined with artemether for malaria'),
    ('Salbutamol',         'Bronchodilator',               'Inhaler/Tablet',  '2–4 mg oral',        '16 mg oral', 'Short-acting beta-2 agonist for asthma relief'),
    ('Budesonide',         'Corticosteroid – Inhaled',     'Inhaler',         '200–400 mcg',        '1600 mcg',   'Inhaled corticosteroid for asthma maintenance'),
    ('Montelukast',        'Leukotriene Antagonist',       'Tablet',          '10 mg',              '10 mg',      'Leukotriene receptor antagonist for asthma'),
    ('Ipratropium',        'Anticholinergic',              'Inhaler',         '20–40 mcg',          '320 mcg',    'Short-acting anticholinergic for COPD/asthma'),
    ('Nitrofurantoin',     'Antibiotic',                   'Capsule',         '50–100 mg',          '400 mg',     'Antibiotic specifically for UTI'),
    ('Trimethoprim',       'Antibiotic',                   'Tablet',          '100–200 mg',         '400 mg',     'Antibiotic for UTI and respiratory infections'),
    ('Sumatriptan',        'Antimigraine – Triptan',       'Tablet',          '50–100 mg',          '300 mg',     'Serotonin receptor agonist for acute migraine'),
    ('Propranolol',        'Beta-blocker',                 'Tablet',          '40–80 mg',           '320 mg',     'Beta-blocker for migraine prevention and hypertension'),
    ('Omeprazole',         'Proton Pump Inhibitor',        'Capsule',         '20–40 mg',           '80 mg',      'Reduces stomach acid for gastritis and GERD'),
    ('Pantoprazole',       'Proton Pump Inhibitor',        'Tablet',          '20–40 mg',           '80 mg',      'Proton pump inhibitor for acid-related disorders'),
    ('Metronidazole',      'Antibiotic – Antiprotozoal',   'Tablet',          '400–500 mg',         '2000 mg',    'Antibiotic/antiprotozoal for GI and other infections'),
    ('Ferrous Sulfate',    'Iron Supplement',              'Tablet',          '200 mg',             '600 mg',     'Iron supplementation for iron-deficiency anaemia'),
    ('Folic Acid',         'Vitamin B9 Supplement',        'Tablet',          '400 mcg – 5 mg',     '5 mg',       'Folic acid for anaemia and neural tube defect prevention'),
    ('Vitamin B12',        'Vitamin Supplement',           'Tablet/Injection','1000 mcg',           '2000 mcg',   'B12 supplementation for anaemia and neurological health'),
    ('Hydroxychloroquine', 'DMARD/Antimalarial',           'Tablet',          '200–400 mg',         '600 mg',     'Disease-modifying drug for rheumatoid arthritis'),
    ('Methotrexate',       'DMARD/Antimetabolite',         'Tablet',          '7.5–25 mg/week',     '25 mg/week', 'Disease-modifying drug for rheumatoid arthritis'),
    ('Prednisolone',       'Corticosteroid',               'Tablet',          '5–60 mg',            '60 mg',      'Corticosteroid for inflammatory conditions'),
    ('Favipiravir',        'Antiviral',                    'Tablet',          '1600 mg (day 1)',     '3200 mg',    'Antiviral for COVID-19 treatment'),
    ('Dexamethasone',      'Corticosteroid',               'Tablet/Injection','6 mg',               '40 mg',      'Corticosteroid for severe COVID-19 and inflammation'),
    ('Oseltamivir',        'Antiviral',                    'Capsule',         '75 mg',              '150 mg',     'Antiviral for influenza treatment'),
    ('Loratadine',         'Antihistamine',                'Tablet',          '10 mg',              '10 mg',      'Non-sedating antihistamine for allergic symptoms'),
    ('Dextromethorphan',   'Cough Suppressant',            'Syrup/Tablet',    '10–30 mg',           '120 mg',     'Cough suppressant for dry cough'),
    ('Guaifenesin',        'Expectorant',                  'Syrup/Tablet',    '200–400 mg',         '2400 mg',    'Expectorant to loosen productive cough'),
    ('ORS',                'Oral Rehydration Salts',       'Powder/Sachet',   '1 sachet / 1 L',     'As needed',  'Oral rehydration for dehydration'),
    ('Vitamin C',          'Vitamin Supplement',           'Tablet',          '500–1000 mg',        '2000 mg',    'Antioxidant vitamin for immune support'),
    ('Zinc',               'Mineral Supplement',           'Tablet',          '20–50 mg',           '40 mg',      'Zinc supplementation for immune support'),
    ('Warfarin',           'Anticoagulant',                'Tablet',          '2–10 mg',            '10 mg',      'Blood thinner for thrombosis prevention'),
    ('Aspirin',            'NSAID/Antiplatelet',           'Tablet',          '75–325 mg',          '4000 mg',    'Antiplatelet for cardiovascular prevention'),
    ('Atorvastatin',       'Statin',                       'Tablet',          '10–80 mg',           '80 mg',      'Statin for cholesterol reduction'),
]

INTERACTIONS_SEED = [
    # (drug1, drug2, severity, description)
    ('Ibuprofen',          'Warfarin',          'HIGH',     'Increased bleeding risk due to combined anticoagulant effects'),
    ('Aspirin',            'Warfarin',          'HIGH',     'Significant increased bleeding risk'),
    ('Methotrexate',       'Ibuprofen',         'HIGH',     'NSAIDs can increase methotrexate toxicity to dangerous levels'),
    ('Methotrexate',       'Aspirin',           'HIGH',     'NSAIDs can increase methotrexate toxicity to dangerous levels'),
    ('Chloroquine',        'Hydroxychloroquine','HIGH',     'Risk of QT interval prolongation and cardiac arrhythmia'),
    ('Azithromycin',       'Hydroxychloroquine','HIGH',     'Significant QT prolongation risk – potential fatal arrhythmia'),
    ('Sumatriptan',        'Propranolol',       'MODERATE', 'Propranolol may increase sumatriptan plasma levels'),
    ('Ciprofloxacin',      'Metronidazole',     'MODERATE', 'Both can prolong QT interval; monitor ECG'),
    ('Prednisolone',       'Ibuprofen',         'MODERATE', 'Increased risk of GI ulceration and bleeding'),
    ('Prednisolone',       'Aspirin',           'MODERATE', 'Increased risk of gastrointestinal bleeding'),
    ('Prednisolone',       'Metformin',         'MODERATE', 'Steroids can raise blood glucose, counteracting metformin'),
    ('Dexamethasone',      'Metformin',         'MODERATE', 'Corticosteroids can increase blood glucose levels'),
    ('Amlodipine',         'Atorvastatin',      'MODERATE', 'Amlodipine can increase atorvastatin levels; monitor for myopathy'),
    ('Propranolol',        'Amlodipine',        'MODERATE', 'Combined use may cause excessive blood-pressure lowering'),
    ('Omeprazole',         'Methotrexate',      'MODERATE', 'Omeprazole may increase methotrexate levels'),
    ('Warfarin',           'Azithromycin',      'MODERATE', 'Azithromycin may enhance anticoagulant effect of warfarin'),
    ('Ciprofloxacin',      'Atorvastatin',      'MODERATE', 'Ciprofloxacin may inhibit statin metabolism'),
    ('Atenolol',           'Amlodipine',        'LOW',      'Generally safe; monitor blood pressure'),
    ('Lisinopril',         'Atorvastatin',      'LOW',      'Generally safe; monitor renal function'),
    ('Metformin',          'Alcohol',           'HIGH',     'Risk of lactic acidosis when combined with significant alcohol intake'),
]

# ─── Disease → recommended drugs mapping ─────────────────────────────────────
DISEASE_DRUGS: dict[str, list[str]] = {
    'Influenza':              ['Oseltamivir', 'Paracetamol', 'Ibuprofen', 'Loratadine', 'Dextromethorphan'],
    'Common Cold':            ['Paracetamol', 'Loratadine', 'Dextromethorphan', 'Guaifenesin'],
    'Pneumonia':              ['Amoxicillin', 'Azithromycin', 'Paracetamol', 'Guaifenesin'],
    'Type 2 Diabetes':        ['Metformin', 'Glipizide', 'Sitagliptin'],
    'Hypertension':           ['Amlodipine', 'Lisinopril', 'Atenolol', 'Hydrochlorothiazide'],
    'Malaria':                ['Artemether', 'Lumefantrine', 'Chloroquine', 'Paracetamol'],
    'Typhoid Fever':          ['Ciprofloxacin', 'Azithromycin', 'Paracetamol', 'ORS'],
    'Dengue Fever':           ['Paracetamol', 'ORS', 'Vitamin C'],
    'Asthma':                 ['Salbutamol', 'Budesonide', 'Montelukast', 'Ipratropium'],
    'Urinary Tract Infection':['Ciprofloxacin', 'Nitrofurantoin', 'Trimethoprim', 'Paracetamol'],
    'Migraine':               ['Sumatriptan', 'Paracetamol', 'Ibuprofen', 'Propranolol'],
    'Gastritis':              ['Omeprazole', 'Pantoprazole', 'Metronidazole'],
    'Anemia':                 ['Ferrous Sulfate', 'Folic Acid', 'Vitamin B12', 'Vitamin C'],
    'Rheumatoid Arthritis':   ['Hydroxychloroquine', 'Methotrexate', 'Ibuprofen', 'Prednisolone'],
    'COVID-19':               ['Paracetamol', 'Favipiravir', 'Dexamethasone', 'Vitamin C', 'Zinc'],
}


# ─── DatabaseManager ──────────────────────────────────────────────────────────
class DatabaseManager:
    def __init__(self):
        self._type = DB_TYPE
        self._create_tables()
        self._seed_drugs()

    # ── Connection helpers ────────────────────────────────────────────────────
    @contextmanager
    def _conn(self):
        if self._type == "mysql":
            import mysql.connector
            conn = mysql.connector.connect(
                host=DB_HOST, port=DB_PORT,
                user=DB_USER, password=DB_PASSWORD,
                database=DB_NAME
            )
        else:
            conn = sqlite3.connect(SQLITE_PATH)
            conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _execute(self, sql: str, params: tuple = ()):
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            return cur.lastrowid

    def _fetchall(self, sql: str, params: tuple = ()) -> list:
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    def _fetchone(self, sql: str, params: tuple = ()) -> dict | None:
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None

    # ── Schema ────────────────────────────────────────────────────────────────
    def _create_tables(self):
        ddl = """
        CREATE TABLE IF NOT EXISTS patients (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL,
            age           INTEGER,
            gender        TEXT,
            weight        REAL,
            blood_group   TEXT,
            phone         TEXT,
            email         TEXT,
            created_at    TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS medical_history (
            id                     INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id             INTEGER NOT NULL,
            allergies              TEXT,
            chronic_conditions     TEXT,
            current_medications    TEXT,
            notes                  TEXT,
            created_at             TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );

        CREATE TABLE IF NOT EXISTS drugs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL UNIQUE,
            category        TEXT,
            dosage_form     TEXT,
            standard_dose   TEXT,
            max_daily_dose  TEXT,
            description     TEXT
        );

        CREATE TABLE IF NOT EXISTS drug_interactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            drug1_name  TEXT NOT NULL,
            drug2_name  TEXT NOT NULL,
            severity    TEXT,
            description TEXT
        );

        CREATE TABLE IF NOT EXISTS prescriptions (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            prescription_id     TEXT UNIQUE,
            patient_id          INTEGER,
            doctor_name         TEXT,
            predicted_disease   TEXT,
            confidence          REAL,
            symptoms_json       TEXT,
            medications_json    TEXT,
            notes               TEXT,
            created_at          TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );
        """
        with self._conn() as conn:
            for stmt in ddl.strip().split(";"):
                stmt = stmt.strip()
                if stmt:
                    conn.cursor().execute(stmt)

    def _seed_drugs(self):
        existing = self._fetchall("SELECT name FROM drugs")
        if existing:
            return
        sql = """INSERT OR IGNORE INTO drugs
                 (name, category, dosage_form, standard_dose, max_daily_dose, description)
                 VALUES (?,?,?,?,?,?)"""
        with self._conn() as conn:
            cur = conn.cursor()
            cur.executemany(sql, DRUGS_SEED)
        sql_i = """INSERT INTO drug_interactions
                   (drug1_name, drug2_name, severity, description)
                   VALUES (?,?,?,?)"""
        with self._conn() as conn:
            cur = conn.cursor()
            cur.executemany(sql_i, INTERACTIONS_SEED)

    # ── Patients ──────────────────────────────────────────────────────────────
    def add_patient(self, name, age, gender, weight, blood_group, phone="", email="") -> int:
        sql = """INSERT INTO patients (name,age,gender,weight,blood_group,phone,email)
                 VALUES (?,?,?,?,?,?,?)"""
        return self._execute(sql, (name, age, gender, weight, blood_group, phone, email))

    def get_patient(self, patient_id: int) -> dict | None:
        return self._fetchone("SELECT * FROM patients WHERE id=?", (patient_id,))

    def search_patients(self, query: str) -> list:
        q = f"%{query}%"
        return self._fetchall("SELECT * FROM patients WHERE name LIKE ? OR phone LIKE ?", (q, q))

    def all_patients(self) -> list:
        return self._fetchall("SELECT * FROM patients ORDER BY created_at DESC")

    # ── Medical history ───────────────────────────────────────────────────────
    def add_medical_history(self, patient_id, allergies="", chronic="", current_meds="", notes=""):
        sql = """INSERT INTO medical_history
                 (patient_id, allergies, chronic_conditions, current_medications, notes)
                 VALUES (?,?,?,?,?)"""
        return self._execute(sql, (patient_id, allergies, chronic, current_meds, notes))

    def get_medical_history(self, patient_id: int) -> dict | None:
        return self._fetchone(
            "SELECT * FROM medical_history WHERE patient_id=? ORDER BY id DESC LIMIT 1",
            (patient_id,)
        )

    # ── Prescriptions ─────────────────────────────────────────────────────────
    def save_prescription(self, rx_id, patient_id, doctor, disease, confidence,
                          symptoms, medications, notes="") -> int:
        sql = """INSERT INTO prescriptions
                 (prescription_id, patient_id, doctor_name, predicted_disease,
                  confidence, symptoms_json, medications_json, notes)
                 VALUES (?,?,?,?,?,?,?,?)"""
        return self._execute(sql, (
            rx_id, patient_id, doctor, disease, confidence,
            json.dumps(symptoms), json.dumps(medications), notes
        ))

    def get_patient_prescriptions(self, patient_id: int) -> list:
        rows = self._fetchall(
            "SELECT * FROM prescriptions WHERE patient_id=? ORDER BY created_at DESC",
            (patient_id,)
        )
        for r in rows:
            r['symptoms']    = json.loads(r.get('symptoms_json',    '[]'))
            r['medications'] = json.loads(r.get('medications_json', '[]'))
        return rows

    def all_prescriptions(self, limit: int = 50) -> list:
        return self._fetchall(
            "SELECT p.*, pt.name AS patient_name "
            "FROM prescriptions p LEFT JOIN patients pt ON p.patient_id=pt.id "
            "ORDER BY p.created_at DESC LIMIT ?",
            (limit,)
        )

    def prescription_count_today(self) -> int:
        today = datetime.now().strftime("%Y-%m-%d")
        rows  = self._fetchall(
            "SELECT COUNT(*) AS cnt FROM prescriptions WHERE created_at LIKE ?",
            (f"{today}%",)
        )
        return rows[0]['cnt'] if rows else 0

    # ── Drugs ─────────────────────────────────────────────────────────────────
    def get_drug(self, name: str) -> dict | None:
        return self._fetchone("SELECT * FROM drugs WHERE name=?", (name,))

    def all_drugs(self) -> list:
        return self._fetchall("SELECT * FROM drugs ORDER BY name")

    def search_drugs(self, query: str) -> list:
        q = f"%{query}%"
        return self._fetchall(
            "SELECT * FROM drugs WHERE name LIKE ? OR category LIKE ? OR description LIKE ?",
            (q, q, q)
        )

    def get_interactions_for_drug(self, drug_name: str) -> list:
        return self._fetchall(
            "SELECT * FROM drug_interactions WHERE drug1_name=? OR drug2_name=?",
            (drug_name, drug_name)
        )

    def check_pair_interaction(self, d1: str, d2: str) -> dict | None:
        return self._fetchone(
            "SELECT * FROM drug_interactions "
            "WHERE (drug1_name=? AND drug2_name=?) OR (drug1_name=? AND drug2_name=?)",
            (d1, d2, d2, d1)
        )

    # ── Stats ─────────────────────────────────────────────────────────────────
    def stats(self) -> dict:
        patients_total      = self._fetchone("SELECT COUNT(*) AS n FROM patients")['n']
        prescriptions_total = self._fetchone("SELECT COUNT(*) AS n FROM prescriptions")['n']
        drugs_total         = self._fetchone("SELECT COUNT(*) AS n FROM drugs")['n']
        interactions_total  = self._fetchone("SELECT COUNT(*) AS n FROM drug_interactions")['n']
        return {
            "patients":     patients_total,
            "prescriptions":prescriptions_total,
            "drugs":        drugs_total,
            "interactions": interactions_total,
            "today":        self.prescription_count_today(),
        }

    # ── Recommended drugs for a disease ──────────────────────────────────────
    @staticmethod
    def recommended_drugs(disease: str) -> list[str]:
        return DISEASE_DRUGS.get(disease, [])
