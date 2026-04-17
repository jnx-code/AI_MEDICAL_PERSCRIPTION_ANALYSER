# 🧠 AI Medical Prescription Assistance System

### *(Clinical Decision Support System - CDSS)*

## 📌 Overview

The **AI Medical Prescription Assistance System** is a Clinical Decision Support System (CDSS) designed to assist healthcare professionals in generating safe, accurate, and efficient prescriptions.

This system leverages **Machine Learning, rule-based logic, and a medical safety engine** to reduce prescription errors, detect drug interactions, and improve overall healthcare workflow.

> ⚠️ Note: This system is intended to assist doctors, not replace them.

---

## 🚀 Features

* ✅ Disease prediction using Machine Learning
* ✅ AI-assisted prescription recommendations
* ✅ Drug interaction and allergy detection
* ✅ Patient medical history tracking
* ✅ Digital prescription generation
* ✅ Explainable AI (reason behind predictions)
* ✅ Doctor override functionality
* ✅ Streamlit-based interactive UI

---

## 🏗️ System Architecture

```
Streamlit UI → Python Backend → ML Model → Rule-Based Engine → MySQL Database
```

---

## 🛠️ Tech Stack

| Component        | Technology Used |
| ---------------- | --------------- |
| Frontend         | Streamlit       |
| Backend          | Python          |
| Machine Learning | Scikit-learn    |
| Database         | MySQL           |
| NLP (Optional)   | spaCy           |

---

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/ai-medical-system.git
cd ai-medical-system
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🗄️ Database Setup (MySQL)

1. Create a database:

```sql
CREATE DATABASE medical_system;
```

2. Update credentials in:

```
database/db_config.py
```

3. Create tables:

* Patients
* Medical_History
* Drugs
* Interactions
* Prescriptions

---

## ▶️ Run the Application

```bash
streamlit run app.py
```

---

## 🔄 Workflow

1. Doctor enters patient details and symptoms
2. ML model predicts possible disease
3. System suggests medications
4. Safety engine checks:

   * Drug interactions
   * Allergies
   * Dosage
5. Final prescription is generated
6. Data is stored in MySQL

---

## 🧪 Machine Learning Model

* Algorithms Used:

  * Logistic Regression
  * Random Forest

* Input: Symptoms

* Output: Predicted Disease

---

## 🔐 Safety Engine

The system includes a rule-based safety module that:

* Detects harmful drug combinations
* Prevents allergic prescriptions
* Reduces risk of Adverse Drug Reactions (ADRs)

---

## 📊 Evaluation Metrics

* Accuracy
* Precision
* Recall
* Safety validation accuracy

---

## ⚠️ Limitations

* Not a replacement for medical professionals
* Requires high-quality datasets
* Needs regulatory compliance for real-world deployment

---

## 🔮 Future Enhancements

* Voice-based input for doctors
* Integration with Electronic Health Records (EHR)
* Advanced NLP for clinical notes
* Personalized medicine recommendations
* Cloud deployment

---

## 🤝 Contributing

Contributions are welcome!
Feel free to fork this repository and submit pull requests.

---

## 📄 License

This project is for educational and research purposes only.

---

## 💡 Author

**JUNED**

* AI/ML Enthusiast
* Python Developer

---

## ⭐ Support

If you found this project helpful, please give it a ⭐ on GitHub!
