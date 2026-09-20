import pytest
import uuid
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.models.models import (
    Hospital, User, Patient, Encounter, PatientFact,
    ClinicalAssessment, RedFlag, ClinicalHistory, ClinicalSummary,
    Prescription, PrescriptionItem, Document, DocumentEntity,
    DocTalkConsultation, DocTalkConsultationNote, AuditLog
)
from app.core.security import create_access_token, hash_password
from app.database import Base, engine, SessionLocal

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _uid():
    return uuid.uuid4().hex[:6]


def create_hospital(db, name=None):
    h = Hospital(name=name or ("Hospital " + _uid()))
    db.add(h)
    db.commit()
    db.refresh(h)
    return h


def create_doctor(db, hospital_id, specialty="General Medicine",
                  availability_status="ONLINE", doctalk_enabled=True,
                  is_verified=True, role="DOCTOR", display_name=None):
    username = "doc_" + _uid()
    doc = User(
        hospital_id=hospital_id,
        role=role,
        username=username,
        display_name=display_name or ("Dr. " + username.capitalize()),
        specialty=specialty,
        qualification="MBBS, MD",
        doctalk_enabled=doctalk_enabled,
        availability_status=availability_status,
        is_verified=is_verified,
        password_hash=hash_password("password123"),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def auth_header(user):
    token = create_access_token({
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "hospital_id": str(user.hospital_id) if user.hospital_id else None,
    })
    return {"Authorization": "Bearer " + token}


@pytest.fixture(scope="module")
def phase9_env(db_session):
    db = db_session
    hosp_a = create_hospital(db, "Apollo Hospital Delhi " + _uid())
    hosp_b = create_hospital(db, "Fortis Escorts Heart Institute " + _uid())
    hosp_c = create_hospital(db, "Max Healthcare Gurgaon " + _uid())

    doc_a = create_doctor(db, hosp_a.id, specialty="General Medicine", display_name="Dr. Rajesh Sharma")
    spec_b = create_doctor(db, hosp_b.id, specialty="Cardiology", display_name="Dr. Ananya Sen")
    doc_c = create_doctor(db, hosp_c.id, specialty="Neurology", display_name="Dr. Vikram Rao")

    # Patient at Hospital A
    pat_a = Patient(
        hospital_id=hosp_a.id,
        demographic_data={"name": "Ramesh Gupta", "age": 62, "gender": "male", "city": "Delhi"}
    )
    db.add(pat_a)
    db.commit()
    db.refresh(pat_a)

    enc_a = Encounter(patient_id=pat_a.id, status="IN_PROGRESS")
    db.add(enc_a)
    db.commit()
    db.refresh(enc_a)

    # Initial clinical data on Encounter & Patient (Baseline)
    fact1 = PatientFact(
        patient_id=pat_a.id,
        category="allergy",
        fact_type="medication_allergy",
        value="Penicillin",
        status="active",
        verified=True,
    )
    fact2 = PatientFact(
        patient_id=pat_a.id,
        category="condition",
        fact_type="chronic_disease",
        value="Type 2 Diabetes Mellitus",
        status="active",
        verified=True,
    )
    db.add_all([fact1, fact2])

    summary_a = ClinicalSummary(
        encounter_id=enc_a.id,
        draft_content={"chief_complaint": "Retrosternal chest tightness on exertion", "plan": "Pending specialist review"},
    )
    db.add(summary_a)

    rx_a = Prescription(
        encounter_id=enc_a.id,
        patient_id=pat_a.id,
        doctor_id=doc_a.id,
        status="DRAFT",
    )
    db.add(rx_a)
    db.flush()

    rx_item = PrescriptionItem(
        prescription_id=rx_a.id,
        medication_name="Metformin 500mg",
        dose="500mg",
        frequency="Twice daily",
        duration_value=30,
        duration_unit="days",
    )
    db.add(rx_item)

    assessment_a = ClinicalAssessment(
        encounter_id=enc_a.id,
        doctor_id=doc_a.id,
        hpi="62y male with 3-day history of exertional angina",
        vitals_examination={"bp": "140/90", "pulse": "84"},
        diagnosis=[{"condition": "Angina pectoris", "type": "provisional"}],
        clinical_plan="Consult cardiologist via DocTalk",
        status="DRAFT",
    )
    db.add(assessment_a)
    db.commit()

    return {
        "hosp_a": hosp_a,
        "hosp_b": hosp_b,
        "hosp_c": hosp_c,
        "doc_a": doc_a,
        "spec_b": spec_b,
        "doc_c": doc_c,
        "pat_a": pat_a,
        "enc_a": enc_a,
        "assessment_a": assessment_a,
        "summary_a": summary_a,
        "rx_a": rx_a,
    }


class TestSpecialistOpinionAndEncounterTimeline:

    def test_specialist_opinion_saved_with_attribution_and_encounter(self, phase9_env, db_session):
        """Verify specialist opinion is saved with specialist, specialist hospital, consultation ID, encounter ID, and timestamp."""
        doc_a = phase9_env["doc_a"]
        spec_b = phase9_env["spec_b"]
        hosp_b = phase9_env["hosp_b"]
        enc_a = phase9_env["enc_a"]

        # 1. Request consultation
        req_res = client.post(
            "/api/v1/doctalk/requests",
            headers=auth_header(doc_a),
            json={
                "encounter_id": str(enc_a.id),
                "specialist_id": str(spec_b.id),
                "specialty": "Cardiology",
                "reason": "Expert opinion on exertional chest pain",
                "urgency": "URGENT",
                "requested_duration_minutes": 5,
            },
        )
        assert req_res.status_code == 201
        consult_id = req_res.json()["id"]

        # 2. Accept
        acc_res = client.post(
            f"/api/v1/doctalk/requests/{consult_id}/accept",
            headers=auth_header(spec_b),
        )
        assert acc_res.status_code == 200

        # 3. Start
        start_res = client.post(
            f"/api/v1/doctalk/requests/{consult_id}/start",
            headers=auth_header(spec_b),
        )
        assert start_res.status_code == 200

        # 4. Complete
        comp_res = client.post(
            f"/api/v1/doctalk/requests/{consult_id}/complete",
            headers=auth_header(spec_b),
        )
        assert comp_res.status_code == 200

        # 5. Specialist submits formal clinical opinion
        note_payload = {
            "clinical_opinion": "High probability of coronary artery disease. Recommend immediate 12-lead ECG and Troponin-I.",
            "recommendations": [
                "12-lead ECG resting",
                "Serum Troponin-I STAT",
                "Sublingual Nitroglycerin 0.5mg PRN for chest pain",
                "Cardiology OPD follow-up in 1 week"
            ],
            "further_evaluation": "Stress echocardiography or CT coronary angiogram if ECG normal and troponin negative.",
            "follow_up": "Review in Cardiology clinic after 7 days.",
        }

        note_res = client.post(
            f"/api/v1/doctalk/requests/{consult_id}/notes",
            headers=auth_header(spec_b),
            json=note_payload,
        )
        assert note_res.status_code == 201
        data = note_res.json()

        # Verify saved attributes
        assert data["consultation_id"] == consult_id
        assert data["encounter_id"] == str(enc_a.id)
        assert data["specialist_id"] == str(spec_b.id)
        assert data["specialist_name"] == spec_b.display_name
        assert data["specialist_hospital_id"] == str(hosp_b.id)
        assert data["specialist_hospital_name"] == hosp_b.name
        assert data["clinical_opinion"] == note_payload["clinical_opinion"]
        assert data["recommendations"] == note_payload["recommendations"]
        assert data["further_evaluation"] == note_payload["further_evaluation"]
        assert data["follow_up"] == note_payload["follow_up"]
        assert data["created_at"] is not None

        # Treating doctor can view note
        doc_get_notes = client.get(
            f"/api/v1/doctalk/requests/{consult_id}/notes",
            headers=auth_header(doc_a),
        )
        assert doc_get_notes.status_code == 200
        notes_list = doc_get_notes.json()
        assert len(notes_list) >= 1
        found = next((n for n in notes_list if n["id"] == data["id"]), None)
        assert found is not None
        assert found["specialist_name"] == spec_b.display_name
        assert found["specialist_hospital_name"] == hosp_b.name
        assert found["encounter_id"] == str(enc_a.id)

    def test_encounter_timeline_contains_all_five_milestones(self, phase9_env, db_session):
        """Verify timeline events contain: DocTalk requested, Specialist accepted, Consultation started, Consultation completed, Specialist opinion added."""
        doc_a = phase9_env["doc_a"]
        pat_a = phase9_env["pat_a"]
        enc_a = phase9_env["enc_a"]

        # Fetch timeline for patient with encounter filter
        tl_res = client.get(
            f"/api/v1/documents/patients/{pat_a.id}/timeline?encounter_id={enc_a.id}",
            headers=auth_header(doc_a),
        )
        assert tl_res.status_code == 200
        events = tl_res.json()["events"]

        event_types = [e["type"] for e in events]
        assert "DOCTALK_REQUESTED" in event_types
        assert "DOCTALK_ACCEPTED" in event_types
        assert "DOCTALK_STARTED" in event_types
        assert "DOCTALK_COMPLETED" in event_types
        assert "DOCTALK_OPINION" in event_types

        # Verify title & formatting match user requirements
        req_event = next(e for e in events if e["type"] == "DOCTALK_REQUESTED")
        assert req_event["title"] == "🩺 DocTalk requested"
        assert req_event["specialty"] == "Cardiology"

        acc_event = next(e for e in events if e["type"] == "DOCTALK_ACCEPTED")
        assert acc_event["title"] == "✓ Specialist accepted"
        assert acc_event["specialist_name"] == phase9_env["spec_b"].display_name

        start_event = next(e for e in events if e["type"] == "DOCTALK_STARTED")
        assert start_event["title"] == "🟢 Consultation started"

        comp_event = next(e for e in events if e["type"] == "DOCTALK_COMPLETED")
        assert comp_event["title"] == "✓ Consultation completed"

        opinion_event = next(e for e in events if e["type"] == "DOCTALK_OPINION")
        assert opinion_event["title"] == "📄 Specialist opinion added"
        assert "clinical_opinion" in opinion_event
        assert "recommendations" in opinion_event
        assert opinion_event["specialist_name"] == phase9_env["spec_b"].display_name
        assert opinion_event["specialist_hospital"] == phase9_env["hosp_b"].name

        # Also test via encounter timeline endpoint
        enc_tl_res = client.get(
            f"/api/v1/encounters/{enc_a.id}/timeline",
            headers=auth_header(doc_a),
        )
        assert enc_tl_res.status_code == 200
        enc_events = enc_tl_res.json()["events"]
        assert len(enc_events) == len(events)

    def test_audit_trail_captures_all_required_attributes(self, phase9_env, db_session):
        """Verify audit log records requester, requesting hospital, specialist, specialist hospital, patient, encounter, timestamps, actions."""
        db = db_session
        doc_a = phase9_env["doc_a"]
        spec_b = phase9_env["spec_b"]
        hosp_a = phase9_env["hosp_a"]
        hosp_b = phase9_env["hosp_b"]
        pat_a = phase9_env["pat_a"]
        enc_a = phase9_env["enc_a"]

        # Find audit logs for this encounter / patient
        logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()
        enc_logs = [l for l in logs if l.details and l.details.get("encounter") == str(enc_a.id)]

        assert len(enc_logs) >= 4

        # Verify opinion added audit record
        opinion_log = next((l for l in enc_logs if l.action in ("DOCTALK_NOTE_CREATED", "DOCTALK_OPINION_ADDED")), None)
        assert opinion_log is not None
        d = opinion_log.details

        # User-specified required audit fields:
        assert d.get("requester") == str(doc_a.id)
        assert d.get("requesting_hospital") == str(hosp_a.id)
        assert d.get("specialist") == str(spec_b.id)
        assert d.get("specialist_hospital") == str(hosp_b.id)
        assert d.get("patient") == str(pat_a.id)
        assert d.get("encounter") == str(enc_a.id)
        assert d.get("timestamps") is not None
        assert d.get("actions") == "DOCTALK_OPINION_ADDED"

    def test_critical_safety_no_existing_clinical_data_overwritten(self, phase9_env, db_session):
        """
        CRITICAL SAFETY TEST:
        DocTalk specialist opinion must NOT automatically overwrite:
        - patient facts
        - diagnosis
        - prescription
        - investigation orders
        - clinical summary
        The treating doctor retains sole clinical authority.
        """
        db = db_session
        doc_a = phase9_env["doc_a"]
        spec_b = phase9_env["spec_b"]
        enc_a = phase9_env["enc_a"]
        pat_a = phase9_env["pat_a"]

        # Baseline snapshots before adding another opinion note
        pre_facts = db.query(PatientFact).filter(PatientFact.patient_id == pat_a.id).all()
        pre_fact_values = sorted([f.value for f in pre_facts])
        pre_fact_count = len(pre_facts)

        pre_assessment = db.query(ClinicalAssessment).filter(ClinicalAssessment.encounter_id == enc_a.id).first()
        pre_diagnosis = pre_assessment.diagnosis
        pre_plan = pre_assessment.clinical_plan

        pre_summary = db.query(ClinicalSummary).filter(ClinicalSummary.encounter_id == enc_a.id).first()
        pre_summary_draft = pre_summary.draft_content

        pre_rx = db.query(Prescription).filter(Prescription.encounter_id == enc_a.id).first()
        pre_rx_items = [it.medication_name for it in pre_rx.items]

        # Get active consultation
        consult = db.query(DocTalkConsultation).filter(DocTalkConsultation.encounter_id == enc_a.id).first()

        # Submit a second opinion with strong recommendations
        res = client.post(
            f"/api/v1/doctalk/requests/{consult.id}/notes",
            headers=auth_header(spec_b),
            json={
                "clinical_opinion": "Add Statin Atorvastatin 40mg immediately and consider Aspirin 75mg daily.",
                "recommendations": ["Atorvastatin 40mg OD", "Aspirin 75mg OD"],
                "further_evaluation": "Coronary angiogram",
                "follow_up": "Check lipid profile in 4 weeks",
            }
        )
        assert res.status_code == 201

        # Re-query all clinical datasets from database
        db.expire_all()

        post_facts = db.query(PatientFact).filter(PatientFact.patient_id == pat_a.id).all()
        post_fact_values = sorted([f.value for f in post_facts])
        post_assessment = db.query(ClinicalAssessment).filter(ClinicalAssessment.encounter_id == enc_a.id).first()
        post_summary = db.query(ClinicalSummary).filter(ClinicalSummary.encounter_id == enc_a.id).first()
        post_rx = db.query(Prescription).filter(Prescription.encounter_id == enc_a.id).first()
        post_rx_items = [it.medication_name for it in post_rx.items]

        # Invariant 1: patient facts are completely untouched
        assert len(post_facts) == pre_fact_count
        assert post_fact_values == pre_fact_values
        assert "Atorvastatin" not in "".join(post_fact_values)

        # Invariant 2: provisional diagnosis and plan are completely untouched
        assert post_assessment.diagnosis == pre_diagnosis
        assert post_assessment.clinical_plan == pre_plan

        # Invariant 3: clinical summary draft is completely untouched
        assert post_summary.draft_content == pre_summary_draft

        # Invariant 4: prescriptions are completely untouched
        assert post_rx_items == pre_rx_items
        assert "Atorvastatin" not in "".join(post_rx_items)

    def test_non_specialist_cannot_add_opinion_notes(self, phase9_env, db_session):
        """Verify that requesting doctor or unassigned doctor cannot submit opinion notes."""
        doc_a = phase9_env["doc_a"]
        doc_c = phase9_env["doc_c"]
        enc_a = phase9_env["enc_a"]

        consult = db_session.query(DocTalkConsultation).filter(DocTalkConsultation.encounter_id == enc_a.id).first()

        # Requesting doctor cannot submit opinion notes
        res_a = client.post(
            f"/api/v1/doctalk/requests/{consult.id}/notes",
            headers=auth_header(doc_a),
            json={"clinical_opinion": "Self note"}
        )
        assert res_a.status_code == 403

        # Third-party doctor cannot submit opinion notes
        res_c = client.post(
            f"/api/v1/doctalk/requests/{consult.id}/notes",
            headers=auth_header(doc_c),
            json={"clinical_opinion": "Third party note"}
        )
        assert res_c.status_code == 403
