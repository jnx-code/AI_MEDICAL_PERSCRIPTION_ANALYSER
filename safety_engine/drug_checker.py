"""
DrugSafetyChecker – validates a proposed medication list against:
  • drug–drug interactions (from the database)
  • patient allergy classes
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Drug-class → drug name mapping for class-level allergy alerts
DRUG_ALLERGY_CLASSES: dict[str, list[str]] = {
    'Penicillins':       ['Amoxicillin'],
    'NSAIDs':            ['Ibuprofen', 'Aspirin'],
    'Fluoroquinolones':  ['Ciprofloxacin'],
    'Macrolides':        ['Azithromycin'],
    'Sulfonamides':      ['Trimethoprim'],
    'Corticosteroids':   ['Prednisolone', 'Dexamethasone', 'Budesonide'],
    'Statins':           ['Atorvastatin'],
    'Beta-blockers':     ['Atenolol', 'Propranolol'],
    'Triptans':          ['Sumatriptan'],
    'Antimalarials':     ['Chloroquine', 'Hydroxychloroquine', 'Artemether'],
    'Antihistamines':    ['Loratadine'],
    'Antivirals':        ['Oseltamivir', 'Favipiravir'],
    'Anticoagulants':    ['Warfarin'],
}


class DrugSafetyChecker:
    def __init__(self, db):
        self._db = db

    # ── Public API ────────────────────────────────────────────────────────────
    def check(self, drug_names: list[str], patient_allergies: str = "") -> dict:
        """
        Run all safety checks and return a structured result:
        {
          "interactions": [{"drugs": [d1,d2], "severity": str, "description": str}, …],
          "allergy_alerts": [{"drug": str, "reason": str}, …],
          "safe": bool,
          "high_risk": bool,
        }
        """
        interactions  = self._check_interactions(drug_names)
        allergy_alerts = self._check_allergies(drug_names, patient_allergies)

        high_risk = any(i["severity"] == "HIGH" for i in interactions) or bool(allergy_alerts)
        safe      = len(interactions) == 0 and len(allergy_alerts) == 0

        return {
            "interactions":   interactions,
            "allergy_alerts": allergy_alerts,
            "safe":           safe,
            "high_risk":      high_risk,
        }

    # ── Internal helpers ──────────────────────────────────────────────────────
    def _check_interactions(self, drug_names: list[str]) -> list[dict]:
        results = []
        checked = set()
        for i, d1 in enumerate(drug_names):
            for d2 in drug_names[i + 1:]:
                pair = tuple(sorted([d1, d2]))
                if pair in checked:
                    continue
                checked.add(pair)
                interaction = self._db.check_pair_interaction(d1, d2)
                if interaction:
                    results.append({
                        "drugs":       [d1, d2],
                        "severity":    interaction["severity"],
                        "description": interaction["description"],
                    })
        return results

    def _check_allergies(self, drug_names: list[str], allergies_str: str) -> list[dict]:
        if not allergies_str.strip():
            return []

        # Tokenise: split on comma/semicolon/newline and lowercase
        allergy_tokens = {
            t.strip().lower()
            for t in allergies_str.replace(";", ",").replace("\n", ",").split(",")
            if t.strip()
        }

        alerts = []
        for drug in drug_names:
            drug_lower = drug.lower()

            # Direct name match
            if drug_lower in allergy_tokens:
                alerts.append({"drug": drug, "reason": f"Patient is allergic to {drug}"})
                continue

            # Class-based match
            for cls, members in DRUG_ALLERGY_CLASSES.items():
                if any(m.lower() == drug_lower for m in members):
                    if cls.lower() in allergy_tokens:
                        alerts.append({
                            "drug":   drug,
                            "reason": f"Patient is allergic to {cls} (class allergy covers {drug})",
                        })

        return alerts

    # ── Convenience ───────────────────────────────────────────────────────────
    @staticmethod
    def severity_color(severity: str) -> str:
        return {"HIGH": "🔴", "MODERATE": "🟡", "LOW": "🟢"}.get(severity, "⚪")
