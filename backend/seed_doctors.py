"""
seed_doctors.py — Seeds verified doctors across multiple specialisations, hospitals, and locations.

Run from backend/ directory:
    python seed_doctors.py

Doctors created:
1. Dr. Priya Sharma      — Internal Medicine (Apollo Hospitals Delhi)
2. Dr. Rajesh Sengupta   — Cardiology (Fortis Memorial Research Institute Gurugram)
3. Dr. Ananya Iyer       — Neurology (Manipal Hospital Bengaluru)
4. Dr. Vikramaditya Mehta — Pulmonology (Max Super Speciality Hospital Saket, New Delhi)
5. Dr. Farah Siddiqui    — Gastroenterology (Kokilaben Dhirubhai Ambani Hospital Mumbai)
6. Dr. Karthik Sundaram  — Nephrology (Apollo Hospitals Greams Road, Chennai)
7. Dr. Sunita Banerjee   — Endocrinology (Medica Superspecialty Hospital Kolkata)
8. Dr. Rohan Kulkarni    — Orthopedics (Ruby Hall Clinic Pune)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.models import Hospital, User
from app.core.security import hash_password

DOCTORS_TO_SEED = [
    {
        "username": "dr.sharma",
        "display_name": "Dr. Priya Sharma",
        "specialty": "Internal Medicine",
        "sub_specialty": "Preventative & Metabolic Care",
        "qualification": "MBBS, MD (General Medicine)",
        "hospital_name": "Apollo Hospitals Delhi",
        "availability_status": "ONLINE",
        "doctalk_enabled": True,
        "is_verified": True,
        "role": "DOCTOR",
    },
    {
        "username": "dr.sengupta",
        "display_name": "Dr. Rajesh Sengupta",
        "specialty": "Cardiology",
        "sub_specialty": "Interventional Cardiology & Coronary Angioplasty",
        "qualification": "MBBS, MD (Medicine), DM (Cardiology), FACC",
        "hospital_name": "Fortis Memorial Research Institute Gurugram",
        "availability_status": "ONLINE",
        "doctalk_enabled": True,
        "is_verified": True,
        "role": "DOCTOR",
    },
    {
        "username": "dr.iyer",
        "display_name": "Dr. Ananya Iyer",
        "specialty": "Neurology",
        "sub_specialty": "Acute Stroke & Comprehensive Epilepsy Care",
        "qualification": "MBBS, MD, DM (Neurology), FINR",
        "hospital_name": "Manipal Hospital Bengaluru",
        "availability_status": "ONLINE",
        "doctalk_enabled": True,
        "is_verified": True,
        "role": "DOCTOR",
    },
    {
        "username": "dr.mehta",
        "display_name": "Dr. Vikramaditya Mehta",
        "specialty": "Pulmonology",
        "sub_specialty": "Interventional Pulmonology & Sleep Medicine",
        "qualification": "MBBS, MD (Pulmonary Medicine), FCCP",
        "hospital_name": "Max Super Speciality Hospital Saket, New Delhi",
        "availability_status": "ONLINE",
        "doctalk_enabled": True,
        "is_verified": True,
        "role": "DOCTOR",
    },
    {
        "username": "dr.siddiqui",
        "display_name": "Dr. Farah Siddiqui",
        "specialty": "Gastroenterology",
        "sub_specialty": "Hepatology, Therapeutic Endoscopy & IBD",
        "qualification": "MBBS, MD, DM (Gastroenterology)",
        "hospital_name": "Kokilaben Dhirubhai Ambani Hospital Mumbai",
        "availability_status": "ONLINE",
        "doctalk_enabled": True,
        "is_verified": True,
        "role": "DOCTOR",
    },
    {
        "username": "dr.sundaram",
        "display_name": "Dr. Karthik Sundaram",
        "specialty": "Nephrology",
        "sub_specialty": "Renal Transplantation & Hemodialysis",
        "qualification": "MBBS, MD, DNB (Nephrology), MNAMS",
        "hospital_name": "Apollo Hospitals Greams Road, Chennai",
        "availability_status": "ONLINE",
        "doctalk_enabled": True,
        "is_verified": True,
        "role": "DOCTOR",
    },
    {
        "username": "dr.banerjee",
        "display_name": "Dr. Sunita Banerjee",
        "specialty": "Endocrinology",
        "sub_specialty": "Advanced Diabetes Care & Thyroid Disorders",
        "qualification": "MBBS, MD, DM (Endocrinology)",
        "hospital_name": "Medica Superspecialty Hospital Kolkata",
        "availability_status": "ONLINE",
        "doctalk_enabled": True,
        "is_verified": True,
        "role": "DOCTOR",
    },
    {
        "username": "dr.kulkarni",
        "display_name": "Dr. Rohan Kulkarni",
        "specialty": "Orthopedics",
        "sub_specialty": "Robotic Joint Replacement & Sports Trauma",
        "qualification": "MBBS, MS (Orthopaedics), MCh (Ortho)",
        "hospital_name": "Ruby Hall Clinic Pune",
        "availability_status": "BUSY",
        "doctalk_enabled": True,
        "is_verified": True,
        "role": "DOCTOR",
    },
]

def seed_doctors():
    db = SessionLocal()
    try:
        print("=== Seeding Multi-Specialty Network Doctors ===")
        created_count = 0
        updated_count = 0

        for item in DOCTORS_TO_SEED:
            # 1. Ensure Hospital exists
            hosp_name = item["hospital_name"]
            hospital = db.query(Hospital).filter(Hospital.name == hosp_name).first()
            if not hospital:
                hospital = Hospital(name=hosp_name)
                db.add(hospital)
                db.commit()
                db.refresh(hospital)
                print(f"[+] Hospital created: {hospital.name} ({hospital.id})")

            # 2. Ensure Doctor User exists
            username = item["username"]
            user = db.query(User).filter(User.username == username).first()

            if not user:
                user = User(
                    username=username,
                    password_hash=hash_password("demo1234"),
                    role=item["role"],
                    hospital_id=hospital.id,
                    display_name=item["display_name"],
                    specialty=item["specialty"],
                    sub_specialty=item["sub_specialty"],
                    qualification=item["qualification"],
                    doctalk_enabled=item["doctalk_enabled"],
                    availability_status=item["availability_status"],
                    is_verified=item["is_verified"],
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                created_count += 1
                print(f"[+] Doctor created: {user.display_name} ({username}) — {user.specialty} @ {hosp_name}")
            else:
                user.password_hash = hash_password("demo1234")
                user.role = item["role"]
                user.hospital_id = hospital.id
                user.display_name = item["display_name"]
                user.specialty = item["specialty"]
                user.sub_specialty = item["sub_specialty"]
                user.qualification = item["qualification"]
                user.doctalk_enabled = item["doctalk_enabled"]
                user.availability_status = item["availability_status"]
                user.is_verified = item["is_verified"]
                db.commit()
                db.refresh(user)
                updated_count += 1
                print(f"[=] Doctor updated: {user.display_name} ({username}) — {user.specialty} @ {hosp_name}")

        print(f"\nSuccessfully seeded doctors! Created: {created_count}, Updated: {updated_count}")
        print("All doctors have password: 'demo1234'")
    finally:
        db.close()

if __name__ == "__main__":
    seed_doctors()
