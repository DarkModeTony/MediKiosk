"""
seed_patients.py — Seeds 6 diverse Indian demo patients into MediPlatform database.

Patients:
1. Anita Desai (58F, Mumbai) - Rheumatoid Arthritis, Osteopenia, Sulfa allergy
2. Mohan Lal Verma (66M, Lucknow) - COPD GOLD II, CAD (stent 2019), Aspirin/NSAID allergy
3. Priya Swaminathan (29F, Chennai) - Hashimoto's Thyroiditis, Asthma, Peanut & Amoxicillin allergy
4. Arjun Patel (34M, Ahmedabad) - CKD Stage 3a (IgA Nephropathy), Secondary HTN, Radiocontrast allergy
5. Sunita Roy (52F, Kolkata) - Chronic Hepatitis B carrier, GERD, Ciprofloxacin allergy
6. Harpreet Singh (48M, Amritsar) - Uncontrolled T2DM, Diabetic Neuropathy, Gout, Allopurinol allergy

Run from backend/ directory:
    python seed_patients.py
"""
import sys
import os
import uuid
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.models import (
    Hospital, User, Patient, Encounter, ClinicalHistory,
    Symptom, ClinicalSummary, RedFlag,
    PatientLongitudinalProfile, PatientFact,
    Prescription, PrescriptionItem, Document
)

def utcnow():
    return datetime.now(timezone.utc)

PATIENTS_DATA = [
    {
        "key": "patient_002",
        "name": "Anita Desai",
        "demographics": {
            "name": "Anita Desai",
            "age": 58,
            "gender": "Female",
            "dob": "1968-04-12",
            "phone": "9000000002",
            "email": "anita.desai@example.com",
            "blood_group": "A+",
            "city": "Mumbai",
            "address": "402 Sea View Apts, Worli, Mumbai, Maharashtra - 400018",
            "emergency_contact": {
                "name": "Rohit Desai (Son)",
                "phone": "9820011223",
                "relation": "Son"
            },
            "preferred_language": "English",
            "communication_mode": "Text",
        },
        "encounter": {
            "chief_complaint": "Bilateral knee swelling and early morning hand stiffness",
            "duration": "2 weeks",
            "symptoms": ["Bilateral knee swelling", "Hand stiffness > 1 hour", "Fatigue"],
            "severity": "Moderate to Severe",
            "vitals": {
                "temperature": "98.8 F",
                "blood_pressure": "134/84 mmHg",
                "heart_rate": "82 bpm",
                "spo2": "99%"
            },
            "family_history": {"mother": "Osteoarthritis", "sister": "Hypothyroidism"},
            "social_history": {"smoking": "Never", "alcohol": "Never", "occupation": "Retired High School Principal"}
        },
        "profile": {
            "medical_history": {
                "chronic_conditions": [
                    {"condition": "Rheumatoid Arthritis (Seropositive)", "icd10": "M05", "since": "2018", "status": "active"},
                    {"condition": "Osteopenia", "icd10": "M85.8", "since": "2021", "status": "active"}
                ],
                "surgeries": [
                    {"procedure": "Right Total Knee Replacement (TKR)", "year": 2021, "indication": "Severe joint destruction secondary to RA", "status": "completed"}
                ],
                "hospitalizations": [
                    {"reason": "TKR Surgery - Lilavati Hospital", "year": 2021}
                ]
            },
            "allergies": {
                "known": [
                    {"substance": "Sulfonamides (Bactrim / Septran)", "reaction": "Maculopapular rash & facial erythema", "severity": "moderate", "confirmed": True}
                ]
            },
            "current_medications": [
                {"name": "Methotrexate", "dose": "15 mg", "frequency": "Once weekly (Sundays)", "status": "active"},
                {"name": "Folic Acid", "dose": "5 mg", "frequency": "Once daily (except Sunday)", "status": "active"},
                {"name": "Hydroxychloroquine", "dose": "200 mg", "frequency": "Once daily", "status": "active"},
                {"name": "Calcium Carbonate + Vit D3", "dose": "500 mg / 400 IU", "frequency": "Once daily", "status": "active"}
            ],
            "family_history": {"mother": "Osteoarthritis", "sister": "Hypothyroidism"},
            "social_history": {"smoking": "Never", "alcohol": "Never", "occupation": "Retired High School Principal"}
        },
        "facts": [
            {"category": "allergy", "fact_type": "drug_allergy", "value": {"substance": "Sulfonamides", "reaction": "Rash & facial erythema", "severity": "moderate"}, "confidence": 0.96},
            {"category": "condition", "fact_type": "chronic", "value": {"condition": "Rheumatoid Arthritis", "icd10": "M05", "since": "2018"}, "confidence": 0.95},
            {"category": "condition", "fact_type": "chronic", "value": {"condition": "Osteopenia", "icd10": "M85.8", "since": "2021"}, "confidence": 0.90},
            {"category": "procedure", "fact_type": "surgery", "value": {"procedure": "Right Total Knee Replacement", "year": 2021}, "confidence": 0.95},
            {"category": "medication", "fact_type": "current_med", "value": {"name": "Methotrexate", "dose": "15 mg", "frequency": "Once weekly"}, "confidence": 0.95},
            {"category": "medication", "fact_type": "current_med", "value": {"name": "Hydroxychloroquine", "dose": "200 mg", "frequency": "Once daily"}, "confidence": 0.95},
        ],
        "prescription": [
            {"name": "Methotrexate 15mg Tab", "dose": "15 mg", "frequency": "Weekly", "instructions": "Take after dinner on Sundays"},
            {"name": "Folic Acid 5mg Tab", "dose": "5 mg", "frequency": "Daily", "instructions": "Take in morning, skip on Sunday"},
            {"name": "Paracetamol 650mg", "dose": "650 mg", "frequency": "SOS", "instructions": "As needed for joint pain, max 3 times daily"}
        ]
    },
    {
        "key": "patient_003",
        "name": "Mohan Lal Verma",
        "demographics": {
            "name": "Mohan Lal Verma",
            "age": 66,
            "gender": "Male",
            "dob": "1960-01-20",
            "phone": "9000000003",
            "email": "mlverma.lucknow@example.com",
            "blood_group": "O+",
            "city": "Lucknow",
            "address": "12/A Gomti Nagar Extension, Lucknow, Uttar Pradesh - 226010",
            "emergency_contact": {
                "name": "Kavita Verma (Wife)",
                "phone": "9415099881",
                "relation": "Spouse"
            },
            "preferred_language": "Hindi",
            "communication_mode": "Voice",
        },
        "encounter": {
            "chief_complaint": "Productive cough with yellowish phlegm and breathlessness on exertion",
            "duration": "5 days",
            "symptoms": ["Productive cough", "Wheezing", "Shortness of breath on walking", "Chest tightness"],
            "severity": "Moderate",
            "vitals": {
                "temperature": "99.4 F",
                "blood_pressure": "142/88 mmHg",
                "heart_rate": "90 bpm",
                "spo2": "93%"
            },
            "family_history": {"father": "Stroke at age 72", "mother": "Hypertension"},
            "social_history": {"smoking": "Ex-smoker (30 pack-years, quit 2019)", "alcohol": "None", "occupation": "Retired Railway Engineer"}
        },
        "profile": {
            "medical_history": {
                "chronic_conditions": [
                    {"condition": "COPD (GOLD Group B)", "icd10": "J44", "since": "2017", "status": "active"},
                    {"condition": "Coronary Artery Disease (CAD)", "icd10": "I25.1", "since": "2019", "status": "active"}
                ],
                "surgeries": [
                    {"procedure": "Percutaneous Coronary Intervention (DES Stent to LAD)", "year": 2019, "indication": "NSTEMI", "status": "completed"}
                ],
                "hospitalizations": [
                    {"reason": "Acute NSTEMI - SGPGI Lucknow", "year": 2019},
                    {"reason": "COPD Exacerbation", "year": 2023}
                ]
            },
            "allergies": {
                "known": [
                    {"substance": "Aspirin & Non-Steroidal Anti-Inflammatory Drugs (NSAIDs)", "reaction": "Severe bronchospasm & dyspnea", "severity": "severe", "confirmed": True}
                ]
            },
            "current_medications": [
                {"name": "Clopidogrel", "dose": "75 mg", "frequency": "Once daily", "status": "active"},
                {"name": "Atorvastatin", "dose": "40 mg", "frequency": "Once daily at bedtime", "status": "active"},
                {"name": "Tiotropium Respimat Inhaler", "dose": "2.5 mcg (2 puffs)", "frequency": "Once daily", "status": "active"},
                {"name": "Formoterol + Budesonide MDI", "dose": "400/12 mcg", "frequency": "Twice daily", "status": "active"}
            ],
            "family_history": {"father": "Stroke at age 72", "mother": "Hypertension"},
            "social_history": {"smoking": "Ex-smoker (quit 2019)", "alcohol": "None", "occupation": "Retired Railway Engineer"}
        },
        "facts": [
            {"category": "allergy", "fact_type": "drug_allergy", "value": {"substance": "Aspirin/NSAIDs", "reaction": "Bronchospasm", "severity": "severe"}, "confidence": 0.98},
            {"category": "condition", "fact_type": "chronic", "value": {"condition": "COPD", "icd10": "J44", "since": "2017"}, "confidence": 0.95},
            {"category": "condition", "fact_type": "chronic", "value": {"condition": "Coronary Artery Disease (CAD)", "icd10": "I25.1", "since": "2019"}, "confidence": 0.95},
            {"category": "procedure", "fact_type": "surgery", "value": {"procedure": "PCI Stent to LAD", "year": 2019}, "confidence": 0.95},
            {"category": "medication", "fact_type": "current_med", "value": {"name": "Clopidogrel", "dose": "75 mg", "frequency": "Once daily"}, "confidence": 0.95},
            {"category": "medication", "fact_type": "current_med", "value": {"name": "Atorvastatin", "dose": "40 mg", "frequency": "Bedtime"}, "confidence": 0.95},
        ],
        "prescription": [
            {"name": "Clopidogrel 75mg Tab", "dose": "75 mg", "frequency": "Daily", "instructions": "Take with breakfast"},
            {"name": "Atorvastatin 40mg Tab", "dose": "40 mg", "frequency": "Daily", "instructions": "Take at night"},
            {"name": "Levocetirizine 5mg", "dose": "5 mg", "frequency": "OD", "instructions": "Take at bedtime for allergy relief"}
        ]
    },
    {
        "key": "patient_004",
        "name": "Priya Swaminathan",
        "demographics": {
            "name": "Priya Swaminathan",
            "age": 29,
            "gender": "Female",
            "dob": "1997-08-05",
            "phone": "9000000004",
            "email": "priya.swami97@example.com",
            "blood_group": "B-",
            "city": "Chennai",
            "address": "78 TTK Road, Alwarpet, Chennai, Tamil Nadu - 600018",
            "emergency_contact": {
                "name": "Karthik Swaminathan (Husband)",
                "phone": "9841054321",
                "relation": "Spouse"
            },
            "preferred_language": "English",
            "communication_mode": "Text",
        },
        "encounter": {
            "chief_complaint": "Persistent extreme lethargy, dry skin, and unexpected weight gain",
            "duration": "1 month",
            "symptoms": ["Lethargy", "Cold intolerance", "Dry skin", "Mild wheeze in cold weather"],
            "severity": "Mild to Moderate",
            "vitals": {
                "temperature": "98.2 F",
                "blood_pressure": "112/70 mmHg",
                "heart_rate": "62 bpm",
                "spo2": "99%"
            },
            "family_history": {"mother": "Thyroid nodule", "grandmother": "Type 2 Diabetes"},
            "social_history": {"smoking": "Never", "alcohol": "Social (rare)", "occupation": "Senior Software Architect"}
        },
        "profile": {
            "medical_history": {
                "chronic_conditions": [
                    {"condition": "Hashimoto's Autoimmune Thyroiditis", "icd10": "E06.3", "since": "2022", "status": "active"},
                    {"condition": "Mild Intermittent Asthma", "icd10": "J45.2", "since": "Childhood", "status": "active"}
                ],
                "surgeries": [],
                "hospitalizations": []
            },
            "allergies": {
                "known": [
                    {"substance": "Peanuts & Tree Nuts", "reaction": "Anaphylaxis (laryngeal edema, urticaria)", "severity": "life_threatening", "confirmed": True},
                    {"substance": "Amoxicillin / Penicillin derivatives", "reaction": "Generalized pruritic rash", "severity": "moderate", "confirmed": True}
                ]
            },
            "current_medications": [
                {"name": "Levothyroxine Sodium", "dose": "75 mcg", "frequency": "Once daily (fasting morning)", "status": "active"},
                {"name": "Salbutamol Inhaler (Asthalin)", "dose": "100 mcg (2 puffs)", "frequency": "PRN (SOS)", "status": "active"}
            ],
            "family_history": {"mother": "Thyroid nodule", "grandmother": "Type 2 Diabetes"},
            "social_history": {"smoking": "Never", "alcohol": "Social (rare)", "occupation": "Senior Software Architect"}
        },
        "facts": [
            {"category": "allergy", "fact_type": "food_allergy", "value": {"substance": "Peanuts", "reaction": "Anaphylaxis", "severity": "severe"}, "confidence": 0.99},
            {"category": "allergy", "fact_type": "drug_allergy", "value": {"substance": "Amoxicillin", "reaction": "Generalized rash", "severity": "moderate"}, "confidence": 0.96},
            {"category": "condition", "fact_type": "chronic", "value": {"condition": "Hashimoto's Thyroiditis", "icd10": "E06.3", "since": "2022"}, "confidence": 0.95},
            {"category": "condition", "fact_type": "chronic", "value": {"condition": "Asthma", "icd10": "J45.2", "since": "Childhood"}, "confidence": 0.90},
            {"category": "medication", "fact_type": "current_med", "value": {"name": "Levothyroxine", "dose": "75 mcg", "frequency": "Fasting morning"}, "confidence": 0.95},
        ],
        "prescription": [
            {"name": "Thyronorm 75mcg Tab", "dose": "75 mcg", "frequency": "Fasting OD", "instructions": "Take empty stomach with water 30 mins before tea/breakfast"},
            {"name": "Asthalin 100mcg Inhaler", "dose": "100 mcg", "frequency": "PRN", "instructions": "Inhale 2 puffs when breathless or wheezing"}
        ]
    },
    {
        "key": "patient_005",
        "name": "Arjun Patel",
        "demographics": {
            "name": "Arjun Patel",
            "age": 34,
            "gender": "Male",
            "dob": "1992-06-18",
            "phone": "9000000005",
            "email": "arjun.patel@gujarattextiles.example.com",
            "blood_group": "AB+",
            "city": "Ahmedabad",
            "address": "15 Navrangpura Heights, CG Road, Ahmedabad, Gujarat - 380009",
            "emergency_contact": {
                "name": "Pooja Patel (Wife)",
                "phone": "9898012345",
                "relation": "Spouse"
            },
            "preferred_language": "Gujarati",
            "communication_mode": "Voice",
        },
        "encounter": {
            "chief_complaint": "Bilateral pedal edema and frothy urine for past 10 days",
            "duration": "10 days",
            "symptoms": ["Bilateral ankle swelling", "Foamy urine", "Occasional morning facial puffiness", "Headache"],
            "severity": "Moderate",
            "vitals": {
                "temperature": "98.6 F",
                "blood_pressure": "154/96 mmHg",
                "heart_rate": "78 bpm",
                "spo2": "98%"
            },
            "family_history": {"father": "Chronic Kidney Disease", "paternal_uncle": "Hypertension"},
            "social_history": {"smoking": "Never", "alcohol": "Never (Teetotaler)", "occupation": "Textile Business Owner"}
        },
        "profile": {
            "medical_history": {
                "chronic_conditions": [
                    {"condition": "Chronic Kidney Disease Stage 3a (IgA Nephropathy)", "icd10": "N18.3", "since": "2023", "status": "active"},
                    {"condition": "Renal Secondary Hypertension", "icd10": "I15.1", "since": "2023", "status": "active"}
                ],
                "surgeries": [
                    {"procedure": "Renal Biopsy (Ultrasound-guided)", "year": 2023, "indication": "Proteinuria evaluation - confirmed IgA Nephropathy", "status": "completed"}
                ],
                "hospitalizations": [
                    {"reason": "Renal Biopsy Day Care - IKDRC Ahmedabad", "year": 2023}
                ]
            },
            "allergies": {
                "known": [
                    {"substance": "Iodinated Radiocontrast Media", "reaction": "Contrast-induced acute urticaria & respiratory distress", "severity": "severe", "confirmed": True}
                ]
            },
            "current_medications": [
                {"name": "Telmisartan", "dose": "40 mg", "frequency": "Once daily morning", "status": "active"},
                {"name": "Torsemide", "dose": "10 mg", "frequency": "Once daily morning", "status": "active"},
                {"name": "Sodium Bicarbonate", "dose": "500 mg", "frequency": "Twice daily after meals", "status": "active"}
            ],
            "family_history": {"father": "Chronic Kidney Disease", "paternal_uncle": "Hypertension"},
            "social_history": {"smoking": "Never", "alcohol": "Never", "occupation": "Textile Business Owner"}
        },
        "facts": [
            {"category": "allergy", "fact_type": "drug_allergy", "value": {"substance": "Iodinated Contrast Media", "reaction": "Urticaria & distress", "severity": "severe"}, "confidence": 0.98},
            {"category": "condition", "fact_type": "chronic", "value": {"condition": "CKD Stage 3a (IgA Nephropathy)", "icd10": "N18.3", "since": "2023"}, "confidence": 0.95},
            {"category": "condition", "fact_type": "chronic", "value": {"condition": "Secondary Hypertension", "icd10": "I15.1", "since": "2023"}, "confidence": 0.95},
            {"category": "procedure", "fact_type": "surgery", "value": {"procedure": "Renal Biopsy", "year": 2023}, "confidence": 0.92},
            {"category": "medication", "fact_type": "current_med", "value": {"name": "Telmisartan", "dose": "40 mg", "frequency": "Daily"}, "confidence": 0.95},
            {"category": "medication", "fact_type": "current_med", "value": {"name": "Torsemide", "dose": "10 mg", "frequency": "Daily"}, "confidence": 0.95},
        ],
        "prescription": [
            {"name": "Telmisartan 40mg Tab", "dose": "40 mg", "frequency": "Daily", "instructions": "Take every morning, check BP regularly"},
            {"name": "Torsemide 10mg Tab", "dose": "10 mg", "frequency": "Daily", "instructions": "Take in the morning with water"}
        ]
    },
    {
        "key": "patient_006",
        "name": "Sunita Roy",
        "demographics": {
            "name": "Sunita Roy",
            "age": 52,
            "gender": "Female",
            "dob": "1974-11-23",
            "phone": "9000000006",
            "email": "sunita.roy.kol@example.com",
            "blood_group": "O-",
            "city": "Kolkata",
            "address": "24B Southern Avenue, Kolkata, West Bengal - 700029",
            "emergency_contact": {
                "name": "Debashis Roy (Husband)",
                "phone": "9830023456",
                "relation": "Spouse"
            },
            "preferred_language": "Bengali",
            "communication_mode": "Voice",
        },
        "encounter": {
            "chief_complaint": "Severe retrosternal burning sensation (heartburn) and acid regurgitation",
            "duration": "1 week",
            "symptoms": ["Heartburn", "Acid reflux", "Postprandial bloating", "Sour taste in mouth"],
            "severity": "Moderate",
            "vitals": {
                "temperature": "98.4 F",
                "blood_pressure": "126/80 mmHg",
                "heart_rate": "74 bpm",
                "spo2": "99%"
            },
            "family_history": {"father": "Colorectal Carcinoma", "mother": "Hypertension"},
            "social_history": {"smoking": "Never", "alcohol": "Never", "occupation": "Government College Professor"}
        },
        "profile": {
            "medical_history": {
                "chronic_conditions": [
                    {"condition": "Chronic Hepatitis B Virus Carrier (Inactive)", "icd10": "B18.1", "since": "2015", "status": "active"},
                    {"condition": "Gastroesophageal Reflux Disease (GERD - Los Angeles Grade B)", "icd10": "K21.0", "since": "2020", "status": "active"}
                ],
                "surgeries": [
                    {"procedure": "Laparoscopic Cholecystectomy", "year": 2017, "indication": "Symptomatic cholelithiasis (gallstones)", "status": "completed"}
                ],
                "hospitalizations": [
                    {"reason": "Gallbladder surgery - AMRI Dhakuria", "year": 2017}
                ]
            },
            "allergies": {
                "known": [
                    {"substance": "Fluoroquinolones (Ciprofloxacin / Levofloxacin)", "reaction": "Achilles tendon pain & arthropathy", "severity": "moderate", "confirmed": True}
                ]
            },
            "current_medications": [
                {"name": "Tenofovir Disoproxil Fumarate", "dose": "300 mg", "frequency": "Once daily with meal", "status": "active"},
                {"name": "Pantoprazole", "dose": "40 mg", "frequency": "Once daily (fasting 30 mins before breakfast)", "status": "active"}
            ],
            "family_history": {"father": "Colorectal Carcinoma", "mother": "Hypertension"},
            "social_history": {"smoking": "Never", "alcohol": "Never", "occupation": "Government College Professor"}
        },
        "facts": [
            {"category": "allergy", "fact_type": "drug_allergy", "value": {"substance": "Fluoroquinolones", "reaction": "Tendon pain / arthropathy", "severity": "moderate"}, "confidence": 0.95},
            {"category": "condition", "fact_type": "chronic", "value": {"condition": "Hepatitis B Carrier", "icd10": "B18.1", "since": "2015"}, "confidence": 0.95},
            {"category": "condition", "fact_type": "chronic", "value": {"condition": "GERD Grade B", "icd10": "K21.0", "since": "2020"}, "confidence": 0.92},
            {"category": "procedure", "fact_type": "surgery", "value": {"procedure": "Laparoscopic Cholecystectomy", "year": 2017}, "confidence": 0.96},
            {"category": "medication", "fact_type": "current_med", "value": {"name": "Tenofovir", "dose": "300 mg", "frequency": "Daily"}, "confidence": 0.95},
            {"category": "medication", "fact_type": "current_med", "value": {"name": "Pantoprazole", "dose": "40 mg", "frequency": "Fasting morning"}, "confidence": 0.95},
        ],
        "prescription": [
            {"name": "Tenofovir 300mg Tab", "dose": "300 mg", "frequency": "Daily", "instructions": "Take with lunch daily"},
            {"name": "Pantoprazole 40mg Tab", "dose": "40 mg", "frequency": "Fasting OD", "instructions": "Take empty stomach 30 mins before breakfast"}
        ]
    },
    {
        "key": "patient_007",
        "name": "Harpreet Singh",
        "demographics": {
            "name": "Harpreet Singh",
            "age": 48,
            "gender": "Male",
            "dob": "1978-02-14",
            "phone": "9000000007",
            "email": "harpreet.singh78@example.com",
            "blood_group": "B+",
            "city": "Amritsar",
            "address": "88 Mall Road, Near Golden Temple, Amritsar, Punjab - 143001",
            "emergency_contact": {
                "name": "Gurmeet Kaur (Wife)",
                "phone": "9872034567",
                "relation": "Spouse"
            },
            "preferred_language": "Punjabi",
            "communication_mode": "Voice",
        },
        "encounter": {
            "chief_complaint": "Excruciating pain and redness in right first metatarsophalangeal (big toe) joint with burning in feet",
            "duration": "2 days",
            "symptoms": ["Severe right big toe pain & redness", "Burning sensation in soles of feet (neuropathy)", "High blood glucose (240 mg/dL self-monitored)"],
            "severity": "Severe",
            "vitals": {
                "temperature": "99.1 F",
                "blood_pressure": "146/90 mmHg",
                "heart_rate": "86 bpm",
                "spo2": "98%"
            },
            "family_history": {"father": "Type 2 Diabetes & Gout", "mother": "Hypertension"},
            "social_history": {"smoking": "Never", "alcohol": "Occasional social", "occupation": "Logistics & Transport Director"}
        },
        "profile": {
            "medical_history": {
                "chronic_conditions": [
                    {"condition": "Type 2 Diabetes Mellitus (Uncontrolled, HbA1c 9.1%)", "icd10": "E11.69", "since": "2016", "status": "active"},
                    {"condition": "Diabetic Peripheral Neuropathy", "icd10": "E11.40", "since": "2021", "status": "active"},
                    {"condition": "Chronic Primary Hyperuricemia / Tophaceous Gout", "icd10": "M10.0", "since": "2019", "status": "active"}
                ],
                "surgeries": [],
                "hospitalizations": [
                    {"reason": "Severe Gout flare with cellulitis rule-out - Fortis Amritsar", "year": 2022}
                ]
            },
            "allergies": {
                "known": [
                    {"substance": "Allopurinol (Severe Cutaneous Adverse Reaction / DRESS warning)", "reaction": "High fever, toxic exfoliation rash, eosinophilia", "severity": "life_threatening", "confirmed": True}
                ]
            },
            "current_medications": [
                {"name": "Insulin Glargine (Lantus)", "dose": "22 units", "frequency": "Subcutaneous at 10 PM daily", "status": "active"},
                {"name": "Metformin + Glimepiride", "dose": "1000 mg / 2 mg", "frequency": "Twice daily with meals", "status": "active"},
                {"name": "Febuxostat", "dose": "40 mg", "frequency": "Once daily morning", "status": "active"},
                {"name": "Pregabalin", "dose": "75 mg", "frequency": "Once daily at bedtime", "status": "active"}
            ],
            "family_history": {"father": "Type 2 Diabetes & Gout", "mother": "Hypertension"},
            "social_history": {"smoking": "Never", "alcohol": "Occasional social", "occupation": "Logistics Director"}
        },
        "facts": [
            {"category": "allergy", "fact_type": "drug_allergy", "value": {"substance": "Allopurinol", "reaction": "Severe cutaneous rash / DRESS", "severity": "severe"}, "confidence": 0.99},
            {"category": "condition", "fact_type": "chronic", "value": {"condition": "Uncontrolled T2DM", "icd10": "E11", "since": "2016"}, "confidence": 0.96},
            {"category": "condition", "fact_type": "chronic", "value": {"condition": "Diabetic Neuropathy", "icd10": "E11.4", "since": "2021"}, "confidence": 0.94},
            {"category": "condition", "fact_type": "chronic", "value": {"condition": "Chronic Gout", "icd10": "M10", "since": "2019"}, "confidence": 0.95},
            {"category": "medication", "fact_type": "current_med", "value": {"name": "Insulin Glargine", "dose": "22 units", "frequency": "Bedtime"}, "confidence": 0.95},
            {"category": "medication", "fact_type": "current_med", "value": {"name": "Febuxostat", "dose": "40 mg", "frequency": "Daily"}, "confidence": 0.95},
            {"category": "medication", "fact_type": "current_med", "value": {"name": "Pregabalin", "dose": "75 mg", "frequency": "Bedtime"}, "confidence": 0.95},
        ],
        "prescription": [
            {"name": "Lantus Insulin 100IU/ml Cartridge", "dose": "22 units", "frequency": "SC Bedtime", "instructions": "Inject subcutaneously at 10 PM"},
            {"name": "Febuxostat 40mg Tab", "dose": "40 mg", "frequency": "Daily", "instructions": "Take in the morning with water"},
            {"name": "Pregabalin 75mg Cap", "dose": "75 mg", "frequency": "Bedtime", "instructions": "Take at night for burning feet"}
        ]
    }
]

def seed_six_patients():
    db = SessionLocal()
    try:
        print("=== Seeding 6 Diverse Indian Patients ===")
        hospital = db.query(Hospital).filter(Hospital.name == "Apollo Hospitals Delhi").first()
        if not hospital:
            hospital = Hospital(name="Apollo Hospitals Delhi")
            db.add(hospital)
            db.commit()
            db.refresh(hospital)

        doctor = db.query(User).filter(User.username == "dr.sharma").first()

        for pat_data in PATIENTS_DATA:
            name = pat_data["name"]
            phone = pat_data["demographics"]["phone"]

            # 1. Check if patient exists
            patient = None
            for p in db.query(Patient).filter(Patient.hospital_id == hospital.id).all():
                demo = p.demographic_data or {}
                if demo.get("phone") == phone or demo.get("name") == name:
                    patient = p
                    break

            if not patient:
                patient = Patient(
                    hospital_id=hospital.id,
                    demographic_data=pat_data["demographics"]
                )
                db.add(patient)
                db.commit()
                db.refresh(patient)
                print(f"[+] Patient created: {name} (Phone: {phone}, ID: {patient.id})")
            else:
                # Update demographic data with latest structured details
                patient.demographic_data = pat_data["demographics"]
                db.commit()
                print(f"[=] Patient updated: {name} (ID: {patient.id})")

            # 2. Encounter
            encounter = db.query(Encounter).filter(
                Encounter.patient_id == patient.id,
                Encounter.status == "WAITING_FOR_DOCTOR"
            ).first()

            if not encounter:
                encounter = Encounter(
                    patient_id=patient.id,
                    status="WAITING_FOR_DOCTOR",
                    start_time=utcnow()
                )
                db.add(encounter)
                db.commit()
                db.refresh(encounter)
                print(f"    [+] Active Encounter created ({encounter.id})")
            else:
                print(f"    [=] Active Encounter exists ({encounter.id})")

            # 3. Clinical History
            history = db.query(ClinicalHistory).filter(ClinicalHistory.encounter_id == encounter.id).first()
            if not history:
                history = ClinicalHistory(
                    encounter_id=encounter.id,
                    history_data=pat_data["encounter"]
                )
                db.add(history)
                db.commit()
                print(f"    [+] Clinical history added.")

            # 4. Symptoms
            if db.query(Symptom).filter(Symptom.encounter_id == encounter.id).count() == 0:
                for sym in pat_data["encounter"]["symptoms"]:
                    db.add(Symptom(encounter_id=encounter.id, symptom_name=sym, details={}))
                db.commit()
                print(f"    [+] Symptoms added.")

            # 5. Longitudinal Profile
            profile = db.query(PatientLongitudinalProfile).filter(
                PatientLongitudinalProfile.patient_id == patient.id
            ).first()

            profile_dict = {
                "schema_version": "1.0",
                "last_updated": utcnow().isoformat(),
                **pat_data["profile"],
                "vitals_last": {
                    **pat_data["encounter"]["vitals"],
                    "recorded_at": utcnow().isoformat()
                }
            }

            if not profile:
                profile = PatientLongitudinalProfile(
                    patient_id=patient.id,
                    schema_version="1.0",
                    profile=profile_dict
                )
                db.add(profile)
                db.commit()
                print(f"    [+] Longitudinal profile created.")
            else:
                profile.profile = profile_dict
                db.commit()
                print(f"    [=] Longitudinal profile updated.")

            # 6. Patient Facts
            for fact_info in pat_data["facts"]:
                existing = db.query(PatientFact).filter(
                    PatientFact.patient_id == patient.id,
                    PatientFact.category == fact_info["category"],
                    PatientFact.fact_type == fact_info["fact_type"]
                ).first()
                if not existing:
                    db.add(PatientFact(
                        patient_id=patient.id,
                        category=fact_info["category"],
                        fact_type=fact_info["fact_type"],
                        value=fact_info["value"],
                        source_type="DOCTOR_VERIFIED",
                        confidence=fact_info["confidence"],
                        verified=True,
                        valid_from=utcnow()
                    ))
            db.commit()
            print(f"    [+] Facts synchronized.")

            # 7. Past Prescription Record (if any)
            existing_rx = db.query(Prescription).filter(
                Prescription.patient_id == patient.id
            ).first()
            if not existing_rx and pat_data.get("prescription"):
                rx = Prescription(
                    patient_id=patient.id,
                    encounter_id=encounter.id,
                    doctor_id=doctor.id if doctor else None,
                    status="FINALIZED",
                    notes=f"Active maintenance regimen for {name}",
                    finalized_at=utcnow() - timedelta(days=14),
                    created_at=utcnow() - timedelta(days=14)
                )
                db.add(rx)
                db.commit()
                db.refresh(rx)

                for item in pat_data["prescription"]:
                    db.add(PrescriptionItem(
                        prescription_id=rx.id,
                        medication_name=item["name"],
                        dose=item["dose"],
                        frequency=item["frequency"],
                        instructions=item.get("instructions", ""),
                        status="active"
                    ))
                db.commit()
                print(f"    [+] Prior finalized prescription seeded.")

        print("\n=== All 6 Patients Successfully Seeded ===")
        print("Cohort ready for testing:")
        print("  1. Raj Kumar          - Phone: 9000000001 / patient_001")
        print("  2. Anita Desai        - Phone: 9000000002 / patient_002")
        print("  3. Mohan Lal Verma    - Phone: 9000000003 / patient_003")
        print("  4. Priya Swaminathan  - Phone: 9000000004 / patient_004")
        print("  5. Arjun Patel        - Phone: 9000000005 / patient_005")
        print("  6. Sunita Roy         - Phone: 9000000006 / patient_006")
        print("  7. Harpreet Singh     - Phone: 9000000007 / patient_007")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Seeding failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_six_patients()
