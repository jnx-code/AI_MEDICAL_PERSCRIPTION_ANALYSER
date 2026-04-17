"""
One-time setup script – run this before launching the app for the first time.
  python setup.py
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("=" * 60)
    print("  AI Medical Prescription Assistance System – Setup")
    print("=" * 60)

    # 1. Directories
    print("\n[1/3] Creating directories …")
    for d in ("models", "database", "ml_engine", "safety_engine", "prescription", "utils"):
        os.makedirs(d, exist_ok=True)
    print("      Done.")

    # 2. Database + seed data
    print("\n[2/3] Initialising database and seeding reference data …")
    from database.db_connection import DatabaseManager
    db = DatabaseManager()
    stats = db.stats()
    print(f"      Patients        : {stats['patients']}")
    print(f"      Drugs seeded    : {stats['drugs']}")
    print(f"      Interactions    : {stats['interactions']}")
    print("      Done.")

    # 3. ML model
    print("\n[3/3] Training ML model (this takes ~30 seconds) …")
    from ml_engine.train_model import train
    metrics = train(verbose=True)
    print(f"\n      Test accuracy : {metrics['accuracy']:.4f}")
    print(f"      CV  accuracy  : {metrics['cv_mean']:.4f} ± {metrics['cv_std']:.4f}")
    print("      Done.")

    print("\n" + "=" * 60)
    print("  Setup complete!")
    print("  Launch the app with:  streamlit run app.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
