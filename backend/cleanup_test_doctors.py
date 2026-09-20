import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.models import User, Hospital, DocTalkConsultation, DocTalkConsultationNote, DocTalkNotification

OFFICIAL_USERNAMES = {
    "dr.sharma",
    "dr.sengupta",
    "dr.iyer",
    "dr.mehta",
    "dr.siddiqui",
    "dr.sundaram",
    "dr.banerjee",
    "dr.kulkarni",
}

def clean_database():
    db = SessionLocal()
    try:
        # 1. Clean all consultations and notifications for Raj Kumar
        raj_consults = db.query(DocTalkConsultation).filter(
            DocTalkConsultation.encounter_id == "7c245014-b38e-42e6-a421-dbfb1f2a6398"
        ).all()
        raj_consult_ids = [c.id for c in raj_consults]
        
        if raj_consult_ids:
            db.query(DocTalkConsultationNote).filter(
                DocTalkConsultationNote.consultation_id.in_(raj_consult_ids)
            ).delete(synchronize_session=False)
            db.query(DocTalkNotification).filter(
                DocTalkNotification.consultation_id.in_(raj_consult_ids)
            ).delete(synchronize_session=False)
            db.query(DocTalkConsultation).filter(
                DocTalkConsultation.id.in_(raj_consult_ids)
            ).delete(synchronize_session=False)
            print(f"Removed {len(raj_consult_ids)} active/stale consultations for Raj Kumar.")

        # 2. Find and remove dummy test doctors not in OFFICIAL_USERNAMES
        dummy_doctors = db.query(User).filter(
            User.role.in_(["DOCTOR", "PHYSICIAN"]),
            ~User.username.in_(OFFICIAL_USERNAMES)
        ).all()
        
        dummy_ids = [d.id for d in dummy_doctors]
        print(f"Found {len(dummy_doctors)} test/dummy doctors to remove: {[d.display_name for d in dummy_doctors]}")
        
        if dummy_ids:
            # Remove notifications for these doctors
            db.query(DocTalkNotification).filter(
                DocTalkNotification.user_id.in_(dummy_ids)
            ).delete(synchronize_session=False)
            
            # Remove consultations where they are requesting or specialist
            dummy_consults = db.query(DocTalkConsultation).filter(
                (DocTalkConsultation.requesting_doctor_id.in_(dummy_ids)) |
                (DocTalkConsultation.specialist_id.in_(dummy_ids))
            ).all()
            dummy_c_ids = [c.id for c in dummy_consults]
            if dummy_c_ids:
                db.query(DocTalkConsultationNote).filter(
                    DocTalkConsultationNote.consultation_id.in_(dummy_c_ids)
                ).delete(synchronize_session=False)
                db.query(DocTalkNotification).filter(
                    DocTalkNotification.consultation_id.in_(dummy_c_ids)
                ).delete(synchronize_session=False)
                db.query(DocTalkConsultation).filter(
                    DocTalkConsultation.id.in_(dummy_c_ids)
                ).delete(synchronize_session=False)

            # Delete the dummy doctors
            for doc in dummy_doctors:
                db.delete(doc)

        # 3. Clean up test hospitals with hex suffixes
        test_hospitals = db.query(Hospital).filter(
            Hospital.name.ilike("% % %") # test hospitals like 'Fortis Escorts Heart Institute b6e2e2'
        ).all()
        for h in test_hospitals:
            # check if any official user uses it
            official_users = db.query(User).filter(User.hospital_id == h.id).count()
            if official_users == 0:
                db.delete(h)

        db.commit()
        print("Database cleanup completed successfully!")

        # Verify remaining official doctors
        remaining = db.query(User).filter(User.role.in_(["DOCTOR", "PHYSICIAN"])).all()
        print(f"Remaining active doctors in network ({len(remaining)}):")
        for r in remaining:
            print(f" - {r.display_name} ({r.specialty}) · {r.hospital.name if r.hospital else 'No Hospital'}")

    finally:
        db.close()

if __name__ == "__main__":
    clean_database()
