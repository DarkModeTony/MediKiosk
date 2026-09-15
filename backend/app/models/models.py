import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base

class Hospital(Base):
    __tablename__ = "hospitals"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    users = relationship("User", back_populates="hospital")
    patients = relationship("Patient", back_populates="hospital")

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id"))
    role = Column(String)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    hospital = relationship("Hospital", back_populates="users")

class Patient(Base):
    __tablename__ = "patients"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id"))
    demographic_data = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    hospital = relationship("Hospital", back_populates="patients")
    encounters = relationship("Encounter", back_populates="patient")
    longitudinal_profile = relationship("PatientLongitudinalProfile", back_populates="patient", uselist=False)
    facts = relationship("PatientFact", back_populates="patient")
    investigations = relationship("InvestigationOrder", back_populates="patient")

class Encounter(Base):
    __tablename__ = "encounters"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    status = Column(String)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    
    patient = relationship("Patient", back_populates="encounters")
    history = relationship("ClinicalHistory", back_populates="encounter", uselist=False)
    symptoms = relationship("Symptom", back_populates="encounter")
    observations = relationship("Observation", back_populates="encounter")
    documents = relationship("Document", back_populates="encounter")
    summary = relationship("ClinicalSummary", back_populates="encounter", uselist=False)
    red_flags = relationship("RedFlag", back_populates="encounter")
    prescriptions = relationship("Prescription", back_populates="encounter")
    assessment = relationship("ClinicalAssessment", back_populates="encounter", uselist=False)
    investigations = relationship("InvestigationOrder", back_populates="encounter")

class ClinicalHistory(Base):
    __tablename__ = "clinical_histories"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"))
    history_data = Column(JSONB)
    ayush_data = Column(JSONB)
    
    encounter = relationship("Encounter", back_populates="history")

class Symptom(Base):
    __tablename__ = "symptoms"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"))
    symptom_name = Column(String)
    details = Column(JSONB)
    
    encounter = relationship("Encounter", back_populates="symptoms")

class Observation(Base):
    __tablename__ = "observations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"))
    category = Column(String)
    value = Column(JSONB)
    
    encounter = relationship("Encounter", back_populates="observations")

class Document(Base):
    __tablename__ = "documents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"))
    file_path = Column(String)
    doc_type = Column(String)
    status = Column(String)
    document_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    encounter = relationship("Encounter", back_populates="documents")
    ocr = relationship("DocumentOCR", back_populates="document", uselist=False)
    entities = relationship("DocumentEntity", back_populates="document")

class DocumentOCR(Base):
    __tablename__ = "document_ocr"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    raw_text = Column(Text)
    engine_used = Column(String)
    page_number = Column(Integer, default=1)
    confidence = Column(Float, nullable=True)
    bounding_boxes = Column(JSONB, nullable=True)
    status = Column(String, default="COMPLETED")
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    document = relationship("Document", back_populates="ocr")

class DocumentEntity(Base):
    __tablename__ = "document_entities"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    entity_type = Column(String)
    value = Column(JSONB)
    confidence = Column(Float)
    source_text = Column(Text, nullable=True)
    page_number = Column(Integer, nullable=True)
    status = Column(String, default="AI_EXTRACTED")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    document = relationship("Document", back_populates="entities")

class Medication(Base):
    __tablename__ = "medications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    name = Column(String)
    dosage = Column(String)
    status = Column(String)

class ClinicalSummary(Base):
    __tablename__ = "clinical_summaries"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"))
    draft_content = Column(JSONB)
    model_info = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    encounter = relationship("Encounter", back_populates="summary")
    verifications = relationship("SummaryVerification", back_populates="summary")

class SummaryVerification(Base):
    __tablename__ = "summary_verifications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    summary_id = Column(UUID(as_uuid=True), ForeignKey("clinical_summaries.id"))
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    final_content = Column(JSONB)
    status = Column(String)
    verified_at = Column(DateTime, default=datetime.utcnow)
    
    summary = relationship("ClinicalSummary", back_populates="verifications")

class RedFlag(Base):
    __tablename__ = "red_flags"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"))
    rule_name = Column(String)
    input_evidence = Column(JSONB)
    severity = Column(String)
    status = Column(String)
    
    encounter = relationship("Encounter", back_populates="red_flags")

class Prescription(Base):
    __tablename__ = "prescriptions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=True)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"))
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status = Column(String, default="DRAFT") # DRAFT, FINALIZED, AMENDED, CANCELLED
    notes = Column(Text, nullable=True)
    finalized_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    encounter = relationship("Encounter", back_populates="prescriptions")
    patient = relationship("Patient")
    items = relationship("PrescriptionItem", back_populates="prescription", cascade="all, delete-orphan")

class PrescriptionItem(Base):
    __tablename__ = "prescription_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prescription_id = Column(UUID(as_uuid=True), ForeignKey("prescriptions.id"))
    medicine_id = Column(Integer, nullable=True)
    medication_name = Column(String)
    generic_name = Column(String, nullable=True)
    strength = Column(String, nullable=True)
    dosage_form = Column(String, nullable=True)
    dose = Column(String, nullable=True)
    dose_unit = Column(String, nullable=True)
    route = Column(String, nullable=True)
    frequency = Column(String, nullable=True)
    timing = Column(String, nullable=True)
    duration_value = Column(Integer, nullable=True)
    duration_unit = Column(String, nullable=True)
    quantity = Column(Integer, nullable=True)
    indication = Column(String, nullable=True)
    instructions = Column(String, nullable=True)
    is_prn = Column(Boolean, default=False)
    min_interval = Column(String, nullable=True)
    max_daily_dose = Column(String, nullable=True)
    status = Column(String, default="active")
    item_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    prescription = relationship("Prescription", back_populates="items")

class Consent(Base):
    __tablename__ = "consents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"))
    consent_type = Column(String)
    granted_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = Column(String)
    target_resource = Column(String)
    details = Column(JSONB)
    timestamp = Column(DateTime, default=datetime.utcnow)

class KioskSession(Base):
    __tablename__ = "kiosk_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_token = Column(String, index=True)
    data = Column(JSONB)
    expires_at = Column(DateTime)

class FHIRResource(Base):
    __tablename__ = "fhir_resources"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resource_type = Column(String)
    internal_id = Column(String)
    fhir_data = Column(JSONB)

class PatientLongitudinalProfile(Base):
    __tablename__ = "patient_longitudinal_profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), unique=True, index=True, nullable=False)
    schema_version = Column(String, default="1.0")
    profile = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = relationship("Patient", back_populates="longitudinal_profile")

class PatientFact(Base):
    __tablename__ = "patient_facts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), index=True, nullable=False)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"), nullable=True)
    category = Column(String, index=True) # allergy, chronic_condition, surgery, medication, anatomy, etc.
    fact_type = Column(String)
    body_site = Column(String, nullable=True)
    laterality = Column(String, nullable=True)
    value = Column(JSONB)
    status = Column(String, default="active")
    source_type = Column(String, default="patient_statement")
    source_id = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    verified = Column(Boolean, default=False)
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = relationship("Patient", back_populates="facts")
 
 
class ClinicalAssessment(Base):
    __tablename__ = "clinical_assessments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"), unique=True, index=True)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    hpi = Column(Text, nullable=True) # History of Present Illness
    vitals_examination = Column(JSONB, nullable=True) # {bp, pulse, temp, spo2, respiratory_rate, exam_notes, systems_examined}
    allergies_confirmed = Column(JSONB, nullable=True) # List of confirmed allergies
    medications_confirmed = Column(JSONB, nullable=True) # List of confirmed active medications
    diagnosis = Column(JSONB, nullable=True) # List of provisional & confirmed diagnoses [{condition, type, icd10, confidence, notes}]
    clinical_plan = Column(Text, nullable=True) # Management plan / advice / follow-up
    status = Column(String, default="DRAFT") # DRAFT, FINALIZED, AMENDED
    finalized_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    encounter = relationship("Encounter", back_populates="assessment")
    doctor = relationship("User")


class InvestigationOrder(Base):
    __tablename__ = "investigation_orders"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("encounters.id"), index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), index=True)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    test_name = Column(String, index=True)
    test_type = Column(String, default="LAB") # LAB, RADIOLOGY, PATHOLOGY, CARDIOLOGY, OTHER
    urgency = Column(String, default="ROUTINE") # ROUTINE, URGENT, STAT
    clinical_notes = Column(Text, nullable=True)
    status = Column(String, default="ORDERED") # ORDERED, PENDING, COMPLETED, REVIEWED, CANCELLED
    ordered_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    encounter = relationship("Encounter", back_populates="investigations")
    patient = relationship("Patient", back_populates="investigations")
    doctor = relationship("User", foreign_keys=[doctor_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    results = relationship("InvestigationResult", back_populates="order", cascade="all, delete-orphan")


class InvestigationResult(Base):
    __tablename__ = "investigation_results"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("investigation_orders.id"), index=True)
    parameter_name = Column(String)
    value = Column(String)
    unit = Column(String, nullable=True)
    reference_range = Column(String, nullable=True)
    abnormal_flag = Column(String, default="NORMAL") # NORMAL, LOW, HIGH, CRITICAL, ABNORMAL
    result_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("InvestigationOrder", back_populates="results")

