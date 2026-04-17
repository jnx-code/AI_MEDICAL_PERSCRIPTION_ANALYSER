"""
AI-Powered Medical Prescription Assistance System
Main Streamlit Application
"""
import os, sys, json, io
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import APP_TITLE, APP_ICON, DOCTOR_NAME, HOSPITAL_NAME
from database.db_connection import DatabaseManager
from ml_engine.predict import PredictionEngine
from safety_engine.drug_checker import DrugSafetyChecker
from prescription.generator import PrescriptionGenerator
from utils.helpers import (
    generate_prescription_id, validate_patient_data, symptom_display_name
)

# ─── Page config (MUST be first Streamlit call) ───────────────────────────────
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.2rem; border-radius: 12px; color: white;
        text-align: center; margin-bottom: 1rem;
    }
    .metric-value { font-size: 2.2rem; font-weight: 700; }
    .metric-label { font-size: 0.85rem; opacity: 0.85; margin-top: 0.2rem; }
    .alert-high     { background:#fee2e2; border-left:4px solid #dc2626;
                      padding:0.8rem; border-radius:6px; margin:0.4rem 0; }
    .alert-moderate { background:#fef9c3; border-left:4px solid #ca8a04;
                      padding:0.8rem; border-radius:6px; margin:0.4rem 0; }
    .alert-low      { background:#dcfce7; border-left:4px solid #16a34a;
                      padding:0.8rem; border-radius:6px; margin:0.4rem 0; }
    .rx-preview     { background:#f8fafc; border:1px solid #e2e8f0;
                      border-radius:8px; padding:1rem; font-family:monospace;
                      font-size:0.82rem; white-space:pre-wrap; }
    .section-header { font-size:1.15rem; font-weight:600; color:#1e3a5f;
                      border-bottom:2px solid #e2e8f0; padding-bottom:0.4rem;
                      margin-bottom:1rem; }
    .stButton>button { border-radius:8px; font-weight:600; }
</style>
""", unsafe_allow_html=True)


# ─── Cached resource initialisation ──────────────────────────────────────────
@st.cache_resource(show_spinner="Initialising AI engine…")
def init_components():
    db        = DatabaseManager()
    predictor = PredictionEngine()
    checker   = DrugSafetyChecker(db)
    generator = PrescriptionGenerator()
    return db, predictor, checker, generator


db, predictor, checker, generator = init_components()


# ─── Session state defaults ───────────────────────────────────────────────────
def _ss(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

_ss("page",             "Dashboard")
_ss("rx_step",          1)
_ss("rx_patient",       {})
_ss("rx_history",       {})
_ss("rx_symptoms",      [])
_ss("rx_predictions",   [])
_ss("rx_disease",       "")
_ss("rx_medications",   [])
_ss("rx_safety",        {})
_ss("rx_notes",         "")
_ss("saved_patient_id", None)


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"## {APP_ICON} {HOSPITAL_NAME}")
    st.markdown(f"*{DOCTOR_NAME}*")
    st.divider()

    nav_options = [
        "Dashboard",
        "New Prescription",
        "Patient Records",
        "Drug Database",
        "About",
    ]
    page = st.radio("Navigation", nav_options, index=nav_options.index(st.session_state.page))
    st.session_state.page = page

    st.divider()
    stats = db.stats()
    st.markdown("**System Status**")
    st.success("AI Engine: Online")
    st.success("Database: Connected")
    st.caption(f"Drugs in DB: {stats['drugs']}  |  Interactions: {stats['interactions']}")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: Dashboard
# ═══════════════════════════════════════════════════════════════════════════════
def page_dashboard():
    st.title("Clinical Dashboard")
    stats = db.stats()

    # KPI cards
    c1, c2, c3, c4 = st.columns(4)
    for col, label, value, icon in [
        (c1, "Total Patients",        stats["patients"],      "👥"),
        (c2, "Total Prescriptions",   stats["prescriptions"], "📋"),
        (c3, "Prescriptions Today",   stats["today"],         "📅"),
        (c4, "Drug Interactions DB",  stats["interactions"],  "⚠️"),
    ]:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size:2rem">{icon}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
            </div>""", unsafe_allow_html=True)

    st.divider()

    col_left, col_right = st.columns([2, 1])

    # Recent prescriptions table
    with col_left:
        st.markdown('<p class="section-header">Recent Prescriptions</p>', unsafe_allow_html=True)
        recent = db.all_prescriptions(limit=10)
        if recent:
            rows = []
            for r in recent:
                rows.append({
                    "ID":        r.get("prescription_id", "—"),
                    "Patient":   r.get("patient_name", "—"),
                    "Diagnosis": r.get("predicted_disease", "—"),
                    "Confidence":f"{r.get('confidence',0):.1f}%",
                    "Date":      r.get("created_at", "—")[:16],
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("No prescriptions yet. Create one using New Prescription.")

    # Disease distribution chart
    with col_right:
        st.markdown('<p class="section-header">Disease Distribution</p>', unsafe_allow_html=True)
        all_rx = db.all_prescriptions(limit=500)
        if all_rx:
            diseases = [r.get("predicted_disease", "Unknown") for r in all_rx]
            df_pie   = pd.Series(diseases).value_counts().reset_index()
            df_pie.columns = ["Disease", "Count"]
            fig = px.pie(df_pie, names="Disease", values="Count",
                         color_discrete_sequence=px.colors.qualitative.Set3)
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=True,
                              legend=dict(font=dict(size=9)))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Chart will populate after first prescription.")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: New Prescription (multi-step wizard)
# ═══════════════════════════════════════════════════════════════════════════════
def page_new_prescription():
    st.title("New Prescription")

    # ── Step indicator ──────────────────────────────────────────────────────
    steps  = ["Patient Info", "Symptoms", "AI Analysis", "Prescription"]
    step   = st.session_state.rx_step
    cols   = st.columns(4)
    for i, (col, label) in enumerate(zip(cols, steps), start=1):
        with col:
            active = "🔵" if i == step else ("✅" if i < step else "⚪")
            st.markdown(f"**{active} {i}. {label}**")
    st.divider()

    # ── STEP 1: Patient Info ────────────────────────────────────────────────
    if step == 1:
        st.markdown('<p class="section-header">Patient Information</p>', unsafe_allow_html=True)

        # Existing patient lookup
        with st.expander("🔍 Load Existing Patient (optional)"):
            search_q = st.text_input("Search by name or phone", key="lookup_q")
            if search_q:
                found = db.search_patients(search_q)
                if found:
                    opts = {f"{p['name']} (ID {p['id']}, Age {p['age']})": p for p in found}
                    sel  = st.selectbox("Select patient", list(opts.keys()))
                    if st.button("Load Patient"):
                        pt = opts[sel]
                        st.session_state.rx_patient = {
                            "id": pt["id"], "name": pt["name"], "age": pt["age"],
                            "gender": pt["gender"], "weight": pt["weight"],
                            "blood_group": pt.get("blood_group", ""),
                            "phone": pt.get("phone", ""),
                        }
                        hist = db.get_medical_history(pt["id"])
                        st.session_state.rx_history = hist or {}
                        st.success(f"Loaded: {pt['name']}")
                        st.rerun()
                else:
                    st.warning("No patients found.")

        pt  = st.session_state.rx_patient
        his = st.session_state.rx_history

        c1, c2 = st.columns(2)
        with c1:
            name   = st.text_input("Full Name *", value=pt.get("name", ""))
            gender = st.selectbox("Gender *", ["Male", "Female", "Other"],
                                  index=["Male","Female","Other"].index(pt.get("gender","Male")))
            bg     = st.selectbox("Blood Group",
                                  ["Unknown","A+","A-","B+","B-","AB+","AB-","O+","O-"],
                                  index=0)
        with c2:
            age    = st.number_input("Age (years) *", 1, 120, int(pt.get("age", 30)))
            weight = st.number_input("Weight (kg) *", 1.0, 300.0,
                                     float(pt.get("weight", 70.0)), step=0.5)
            phone  = st.text_input("Phone", value=pt.get("phone", ""))

        st.markdown("**Medical History**")
        c3, c4 = st.columns(2)
        with c3:
            allergies = st.text_area(
                "Known Allergies (comma-separated)",
                value=his.get("allergies", ""),
                placeholder="e.g. Penicillins, Ibuprofen",
                height=80
            )
        with c4:
            chronic = st.text_area(
                "Chronic Conditions",
                value=his.get("chronic_conditions", ""),
                placeholder="e.g. Hypertension, Diabetes",
                height=80
            )
        current_meds = st.text_input(
            "Current Medications",
            value=his.get("current_medications", ""),
            placeholder="e.g. Metformin 500 mg OD"
        )

        if st.button("Continue →", type="primary"):
            errors = validate_patient_data({"name": name, "age": age,
                                            "weight": weight, "gender": gender})
            if errors:
                for e in errors:
                    st.error(e)
            else:
                st.session_state.rx_patient = {
                    "name": name, "age": age, "gender": gender,
                    "weight": weight, "blood_group": bg, "phone": phone,
                }
                st.session_state.rx_history = {
                    "allergies": allergies,
                    "chronic_conditions": chronic,
                    "current_medications": current_meds,
                }
                st.session_state.rx_step = 2
                st.rerun()

    # ── STEP 2: Symptoms ────────────────────────────────────────────────────
    elif step == 2:
        st.markdown('<p class="section-header">Select Presenting Symptoms</p>',
                    unsafe_allow_html=True)
        st.caption("Select all symptoms currently observed in the patient.")

        all_symptoms = predictor.all_symptoms
        display_map  = {symptom_display_name(s): s for s in all_symptoms}

        # Group symptoms into categories for better UX
        groups = {
            "General":        ["Fever","Fatigue","Weight Loss","Chills","Body Ache"],
            "Respiratory":    ["Cough","Difficulty Breathing","Wheezing","Congestion",
                               "Chest Pain","Sore Throat","Runny Nose","Sneezing"],
            "Neurological":   ["Headache","Dizziness","Blurred Vision"],
            "Gastrointestinal":["Nausea","Vomiting","Diarrhea","Abdominal Pain","Indigestion"],
            "Musculoskeletal":["Joint Pain","Joint Swelling","Stiffness"],
            "Urological":     ["Frequent Urination","Excessive Thirst"],
            "Dermatological": ["Rash","Pale Skin"],
            "COVID Specific": ["Loss Of Taste","Loss Of Smell"],
        }

        selected_display: list[str] = []
        for grp_name, symp_list in groups.items():
            with st.expander(f"**{grp_name}**", expanded=(grp_name in ("General","Respiratory"))):
                # Only show symptoms that exist in the model
                valid = [s for s in symp_list if s in display_map]
                if valid:
                    chosen = st.multiselect(grp_name, valid, label_visibility="collapsed")
                    selected_display.extend(chosen)

        selected_keys = [display_map[d] for d in selected_display if d in display_map]

        st.divider()
        if selected_keys:
            st.info(f"**{len(selected_keys)} symptom(s) selected:** "
                    + ", ".join(selected_display))
        else:
            st.warning("Please select at least one symptom.")

        c1, c2 = st.columns([1, 5])
        with c1:
            if st.button("← Back"):
                st.session_state.rx_step = 1
                st.rerun()
        with c2:
            if st.button("Run AI Analysis →", type="primary", disabled=len(selected_keys) == 0):
                st.session_state.rx_symptoms    = selected_keys
                st.session_state.rx_predictions = predictor.predict(selected_keys, top_k=3)
                st.session_state.rx_disease     = st.session_state.rx_predictions[0]["disease"]
                recs = db.recommended_drugs(st.session_state.rx_disease)
                st.session_state.rx_medications = recs[:4]
                st.session_state.rx_safety      = checker.check(
                    st.session_state.rx_medications,
                    st.session_state.rx_history.get("allergies", "")
                )
                st.session_state.rx_step = 3
                st.rerun()

    # ── STEP 3: AI Analysis & Recommendations ──────────────────────────────
    elif step == 3:
        st.markdown('<p class="section-header">AI Analysis Results</p>', unsafe_allow_html=True)

        preds = st.session_state.rx_predictions

        # Disease predictions
        col_pred, col_med = st.columns([1, 1])
        with col_pred:
            st.markdown("**Disease Predictions (Top 3)**")
            for pred in preds:
                conf = pred["confidence"]
                color = "#22c55e" if conf >= 60 else ("#f59e0b" if conf >= 35 else "#94a3b8")
                st.markdown(f"**{pred['disease']}**")
                st.progress(int(conf), text=f"{conf:.1f}%")

            st.markdown("**Confirm / Override Diagnosis**")
            all_diseases = predictor.all_diseases
            default_idx  = all_diseases.index(st.session_state.rx_disease) \
                           if st.session_state.rx_disease in all_diseases else 0
            selected_disease = st.selectbox(
                "Diagnosed Condition", all_diseases, index=default_idx
            )
            if selected_disease != st.session_state.rx_disease:
                st.session_state.rx_disease    = selected_disease
                recs = db.recommended_drugs(selected_disease)
                st.session_state.rx_medications = recs[:4]

        with col_med:
            st.markdown("**Recommended Medications**")
            all_drug_names = [d["name"] for d in db.all_drugs()]
            selected_meds  = st.multiselect(
                "Select medications to prescribe",
                options=all_drug_names,
                default=st.session_state.rx_medications,
            )
            st.session_state.rx_medications = selected_meds

            # Run safety check on current selection
            if selected_meds:
                safety = checker.check(
                    selected_meds,
                    st.session_state.rx_history.get("allergies", "")
                )
                st.session_state.rx_safety = safety

        st.divider()
        st.markdown("**Safety Check Results**")
        safety = st.session_state.rx_safety

        if safety.get("safe"):
            st.success("All clear – no interactions or allergy alerts detected.")
        else:
            if safety.get("allergy_alerts"):
                st.markdown("**Allergy Alerts**")
                for alert in safety["allergy_alerts"]:
                    st.markdown(
                        f'<div class="alert-high">🚨 <b>{alert["drug"]}</b> – {alert["reason"]}</div>',
                        unsafe_allow_html=True
                    )

            if safety.get("interactions"):
                st.markdown("**Drug Interactions**")
                for inter in safety["interactions"]:
                    cls = ("alert-high"     if inter["severity"] == "HIGH"     else
                           "alert-moderate" if inter["severity"] == "MODERATE" else
                           "alert-low")
                    icon = DrugSafetyChecker.severity_color(inter["severity"])
                    st.markdown(
                        f'<div class="{cls}">{icon} <b>{" + ".join(inter["drugs"])}</b>'
                        f' [{inter["severity"]}] — {inter["description"]}</div>',
                        unsafe_allow_html=True
                    )

        st.session_state.rx_notes = st.text_area(
            "Doctor Notes / Instructions",
            value=st.session_state.rx_notes,
            placeholder="Dosage instructions, dietary advice, follow-up date …",
            height=90,
        )

        c1, c2 = st.columns([1, 5])
        with c1:
            if st.button("← Back"):
                st.session_state.rx_step = 2
                st.rerun()
        with c2:
            if st.button("Generate Prescription →", type="primary",
                         disabled=len(selected_meds) == 0):
                if safety.get("high_risk"):
                    st.warning("⚠️ High-risk interactions detected. Proceeding requires "
                               "explicit doctor override.")
                st.session_state.rx_step = 4
                st.rerun()

    # ── STEP 4: Prescription Preview & Save ────────────────────────────────
    elif step == 4:
        st.markdown('<p class="section-header">Prescription Preview</p>',
                    unsafe_allow_html=True)

        rx_id = generate_prescription_id()

        rx_text = generator.generate_text(
            rx_id      = rx_id,
            patient    = st.session_state.rx_patient,
            disease    = st.session_state.rx_disease,
            confidence = st.session_state.rx_predictions[0]["confidence"]
                         if st.session_state.rx_predictions else 0.0,
            symptoms   = st.session_state.rx_symptoms,
            medications= st.session_state.rx_medications,
            notes      = st.session_state.rx_notes,
        )

        st.markdown(f'<div class="rx-preview">{rx_text}</div>', unsafe_allow_html=True)

        st.divider()
        col_back, col_dl, col_save = st.columns([1, 2, 2])

        with col_back:
            if st.button("← Back"):
                st.session_state.rx_step = 3
                st.rerun()

        with col_dl:
            st.download_button(
                "⬇️ Download Text",
                data=rx_text,
                file_name=f"{rx_id}.txt",
                mime="text/plain",
            )

        with col_save:
            if st.button("💾 Save Prescription", type="primary"):
                pt   = st.session_state.rx_patient
                hist = st.session_state.rx_history

                # Upsert patient
                pid = pt.get("id")
                if not pid:
                    pid = db.add_patient(
                        pt["name"], pt["age"], pt["gender"],
                        pt["weight"], pt.get("blood_group",""),
                        pt.get("phone","")
                    )
                    db.add_medical_history(
                        pid,
                        hist.get("allergies",""),
                        hist.get("chronic_conditions",""),
                        hist.get("current_medications",""),
                    )

                conf = st.session_state.rx_predictions[0]["confidence"] \
                       if st.session_state.rx_predictions else 0.0
                db.save_prescription(
                    rx_id      = rx_id,
                    patient_id = pid,
                    doctor     = DOCTOR_NAME,
                    disease    = st.session_state.rx_disease,
                    confidence = conf,
                    symptoms   = st.session_state.rx_symptoms,
                    medications= st.session_state.rx_medications,
                    notes      = st.session_state.rx_notes,
                )
                st.success(f"Prescription {rx_id} saved successfully!")

                # Reset wizard
                for key in ("rx_step","rx_patient","rx_history","rx_symptoms",
                            "rx_predictions","rx_disease","rx_medications",
                            "rx_safety","rx_notes"):
                    if key == "rx_step":
                        st.session_state[key] = 1
                    else:
                        st.session_state[key] = {} if key in ("rx_patient","rx_history","rx_safety") \
                                                else [] if key in ("rx_symptoms","rx_predictions","rx_medications") \
                                                else ""


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: Patient Records
# ═══════════════════════════════════════════════════════════════════════════════
def page_patient_records():
    st.title("Patient Records")

    search_q = st.text_input("Search patients by name or phone", placeholder="Type to search …")
    if search_q:
        patients = db.search_patients(search_q)
    else:
        patients = db.all_patients()

    if not patients:
        st.info("No patients found.")
        return

    st.markdown(f"**{len(patients)} patient(s) found**")

    # Patient list
    df = pd.DataFrame([{
        "ID": p["id"], "Name": p["name"], "Age": p["age"],
        "Gender": p["gender"], "Blood Group": p.get("blood_group","—"),
        "Phone": p.get("phone","—"), "Registered": str(p.get("created_at",""))[:10],
    } for p in patients])
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Detail view
    st.divider()
    st.markdown("**View Patient Details**")
    pt_ids   = [p["id"] for p in patients]
    pt_names = [f"{p['name']} (ID {p['id']})" for p in patients]
    sel_idx  = st.selectbox("Select patient", range(len(pt_names)),
                             format_func=lambda i: pt_names[i])
    sel_pid  = pt_ids[sel_idx]

    with st.expander("Medical History", expanded=True):
        hist = db.get_medical_history(sel_pid)
        if hist:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Allergies:** {hist.get('allergies','None recorded')}")
                st.markdown(f"**Chronic Conditions:** {hist.get('chronic_conditions','None recorded')}")
            with c2:
                st.markdown(f"**Current Medications:** {hist.get('current_medications','None recorded')}")
                st.markdown(f"**Notes:** {hist.get('notes','—')}")
        else:
            st.info("No medical history on file.")

    with st.expander("Prescription History", expanded=True):
        rxs = db.get_patient_prescriptions(sel_pid)
        if rxs:
            for rx in rxs:
                meds = rx.get("medications") or json.loads(rx.get("medications_json","[]"))
                st.markdown(
                    f"**{rx.get('prescription_id','—')}** — {rx.get('predicted_disease','—')} "
                    f"({rx.get('confidence',0):.1f}%) — *{str(rx.get('created_at',''))[:16]}*"
                )
                st.caption("Medications: " + ", ".join(meds) if meds else "None")
                st.divider()
        else:
            st.info("No prescriptions on file.")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: Drug Database
# ═══════════════════════════════════════════════════════════════════════════════
def page_drug_database():
    st.title("Drug Database")

    tab_browse, tab_interact = st.tabs(["Browse Drugs", "Check Interaction"])

    with tab_browse:
        search_q = st.text_input("Search drugs by name, category, or description",
                                 placeholder="e.g. antibiotic, metformin …")
        drugs = db.search_drugs(search_q) if search_q else db.all_drugs()
        st.caption(f"{len(drugs)} drug(s) found")

        if drugs:
            df = pd.DataFrame([{
                "Name":           d["name"],
                "Category":       d["category"],
                "Dosage Form":    d["dosage_form"],
                "Standard Dose":  d["standard_dose"],
                "Max Daily Dose": d["max_daily_dose"],
            } for d in drugs])
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Detail card
            sel_drug = st.selectbox("Drug Details", [d["name"] for d in drugs])
            drug_info = db.get_drug(sel_drug)
            if drug_info:
                with st.expander(f"Details – {sel_drug}", expanded=True):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"**Category:** {drug_info['category']}")
                        st.markdown(f"**Dosage Form:** {drug_info['dosage_form']}")
                        st.markdown(f"**Standard Dose:** {drug_info['standard_dose']}")
                    with c2:
                        st.markdown(f"**Max Daily Dose:** {drug_info['max_daily_dose']}")
                        st.markdown(f"**Description:** {drug_info['description']}")

                    # Interactions for this drug
                    inters = db.get_interactions_for_drug(sel_drug)
                    if inters:
                        st.markdown("**Known Interactions:**")
                        for i in inters:
                            other = i["drug2_name"] if i["drug1_name"] == sel_drug else i["drug1_name"]
                            icon  = DrugSafetyChecker.severity_color(i["severity"])
                            cls   = ("alert-high"     if i["severity"] == "HIGH"     else
                                     "alert-moderate" if i["severity"] == "MODERATE" else
                                     "alert-low")
                            st.markdown(
                                f'<div class="{cls}">{icon} <b>With {other}</b> [{i["severity"]}]'
                                f' — {i["description"]}</div>',
                                unsafe_allow_html=True
                            )

    with tab_interact:
        st.markdown("**Check Interaction Between Two Drugs**")
        all_drug_names = [d["name"] for d in db.all_drugs()]
        c1, c2 = st.columns(2)
        with c1:
            d1 = st.selectbox("Drug 1", all_drug_names, key="inter_d1")
        with c2:
            d2 = st.selectbox("Drug 2",
                              [d for d in all_drug_names if d != d1],
                              key="inter_d2")

        if st.button("Check", type="primary"):
            result = db.check_pair_interaction(d1, d2)
            if result:
                icon = DrugSafetyChecker.severity_color(result["severity"])
                cls  = ("alert-high"     if result["severity"] == "HIGH"     else
                        "alert-moderate" if result["severity"] == "MODERATE" else
                        "alert-low")
                st.markdown(
                    f'<div class="{cls}">{icon} <b>{d1} + {d2}</b>'
                    f' [{result["severity"]}]<br>{result["description"]}</div>',
                    unsafe_allow_html=True
                )
            else:
                st.success(f"No known interaction between **{d1}** and **{d2}**.")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: About
# ═══════════════════════════════════════════════════════════════════════════════
def page_about():
    st.title("About – AI Medical Prescription Assistance System")
    st.markdown("""
### Clinical Decision Support System (CDSS)

This system assists healthcare professionals in generating safe and accurate prescriptions
using Artificial Intelligence and a rule-based medical safety engine.

---

#### System Architecture

| Component | Technology |
|---|---|
| Frontend | Streamlit |
| ML Engine | Scikit-learn (Random Forest) |
| Safety Engine | Rule-based + Database |
| Database | SQLite (MySQL optional) |
| PDF Generation | ReportLab |
| Visualisation | Plotly |

---

#### ML Model
- **Algorithm:** Random Forest Classifier (200 trees)
- **Features:** 30 binary symptom indicators
- **Diseases:** 15 categories
- **Training:** 15 000 synthetic samples (1 000/disease)

---

#### Disease Coverage
Influenza · Common Cold · Pneumonia · Type 2 Diabetes · Hypertension ·
Malaria · Typhoid Fever · Dengue Fever · Asthma · Urinary Tract Infection ·
Migraine · Gastritis · Anemia · Rheumatoid Arthritis · COVID-19

---

#### Drug Database
**45 drugs** across 15+ pharmacological categories with **20+ interaction pairs** classified
as HIGH / MODERATE / LOW risk.

---

> **Disclaimer:** This system is AI-assisted and intended to **support**, not replace,
> qualified medical professionals. All prescriptions must be reviewed and authorised by
> a licensed physician before dispensing.
""")


# ─── Router ────────────────────────────────────────────────────────────────────
page_map = {
    "Dashboard":        page_dashboard,
    "New Prescription": page_new_prescription,
    "Patient Records":  page_patient_records,
    "Drug Database":    page_drug_database,
    "About":            page_about,
}
page_map[st.session_state.page]()
