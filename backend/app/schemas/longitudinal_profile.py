from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import date, datetime

# --- 1. Patient Demographics Sub-schema ---
class PatientProfileDemographics(BaseModel):
    patient_id: Optional[str] = None
    name: Optional[str] = None
    date_of_birth: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None

# --- 2. Medical History Sub-schemas ---
class Allergy(BaseModel):
    allergen: str
    reaction: Optional[str] = None
    severity: Optional[str] = "moderate" # mild, moderate, severe
    status: Optional[str] = "active"     # active, resolved, unknown
    verified: Optional[bool] = False

class ChronicCondition(BaseModel):
    condition: str
    status: Optional[str] = "active"
    diagnosed_date: Optional[str] = None
    severity: Optional[str] = None
    verified: Optional[bool] = False

class PreviousCondition(BaseModel):
    condition: str
    status: Optional[str] = "resolved"
    year: Optional[Union[int, str]] = None
    verified: Optional[bool] = False

class Surgery(BaseModel):
    procedure: str
    body_site: Optional[str] = None
    date: Optional[str] = None
    reason: Optional[str] = None
    outcome: Optional[str] = None
    verified: Optional[bool] = False

class Hospitalization(BaseModel):
    reason: str
    date: Optional[str] = None
    duration_days: Optional[int] = None
    outcome: Optional[str] = None

class MedicalHistory(BaseModel):
    allergies: List[Allergy] = Field(default_factory=list)
    chronic_conditions: List[ChronicCondition] = Field(default_factory=list)
    previous_conditions: List[PreviousCondition] = Field(default_factory=list)
    surgeries: List[Surgery] = Field(default_factory=list)
    hospitalizations: List[Hospitalization] = Field(default_factory=list)

# --- 3. Medications Sub-schemas ---
class CurrentMedication(BaseModel):
    name: str
    dose: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    reason: Optional[str] = None
    start_date: Optional[str] = None
    status: Optional[str] = "active"

class PreviousMedication(BaseModel):
    name: str
    dose: Optional[str] = None
    frequency: Optional[str] = None
    reason: Optional[str] = None
    status: Optional[str] = "discontinued"

class Medications(BaseModel):
    current: List[CurrentMedication] = Field(default_factory=list)
    previous: List[PreviousMedication] = Field(default_factory=list)

# --- 4. Anatomical Status Sub-schemas (Unknown Must Not Mean No) ---
class EyeDetail(BaseModel):
    present: Optional[bool] = None # None means unknown, False means absent, True means present
    status: str = "unknown"        # unknown, present, absent
    cause: Optional[str] = None
    date: Optional[str] = None
    prosthetic: Optional[bool] = None
    vision: Optional[str] = None
    verified: Optional[bool] = False

class EyesStatus(BaseModel):
    left: EyeDetail = Field(default_factory=EyeDetail)
    right: EyeDetail = Field(default_factory=EyeDetail)

class LimbDetail(BaseModel):
    present: Optional[bool] = None
    status: str = "unknown"        # unknown, present, absent
    prosthetic: Optional[bool] = None
    verified: Optional[bool] = False

class BilateralLimbStatus(BaseModel):
    left: LimbDetail = Field(default_factory=LimbDetail)
    right: LimbDetail = Field(default_factory=LimbDetail)

class AnatomicalStatus(BaseModel):
    eyes: EyesStatus = Field(default_factory=EyesStatus)
    arms: BilateralLimbStatus = Field(default_factory=BilateralLimbStatus)
    legs: BilateralLimbStatus = Field(default_factory=BilateralLimbStatus)
    hands: BilateralLimbStatus = Field(default_factory=BilateralLimbStatus)
    feet: BilateralLimbStatus = Field(default_factory=BilateralLimbStatus)
    other: List[Dict[str, Any]] = Field(default_factory=list)

# --- 5. Medical Devices Sub-schemas ---
class MedicalDevice(BaseModel):
    type: Optional[str] = None # prosthetic, implant, hearing_aid, pacemaker, etc.
    name: Optional[str] = None
    body_site: Optional[str] = None
    status: Optional[str] = "active"
    since: Optional[str] = None

# --- 6. Sensory Status Sub-schemas ---
class VisionSense(BaseModel):
    left_eye: Optional[Dict[str, Any]] = Field(default_factory=lambda: {"status": "unknown"})
    right_eye: Optional[Dict[str, Any]] = Field(default_factory=lambda: {"status": "unknown"})

class HearingSense(BaseModel):
    left_ear: Optional[Dict[str, Any]] = Field(default_factory=lambda: {"status": "unknown"})
    right_ear: Optional[Dict[str, Any]] = Field(default_factory=lambda: {"status": "unknown"})

class SpeechSense(BaseModel):
    status: Optional[str] = "normal"

class SensoryStatus(BaseModel):
    vision: VisionSense = Field(default_factory=VisionSense)
    hearing: HearingSense = Field(default_factory=HearingSense)
    speech: SpeechSense = Field(default_factory=SpeechSense)

# --- 7. Functional Status Sub-schemas ---
class MobilityStatus(BaseModel):
    walking: Optional[str] = "independent" # independent, assisted, wheelchair, bedbound
    walking_aid: Optional[str] = None
    wheelchair: Optional[bool] = False

class DailyActivities(BaseModel):
    eating: Optional[str] = "independent"
    bathing: Optional[str] = "independent"
    dressing: Optional[str] = "independent"
    toileting: Optional[str] = "independent"

class FunctionalStatus(BaseModel):
    mobility: MobilityStatus = Field(default_factory=MobilityStatus)
    daily_activities: DailyActivities = Field(default_factory=DailyActivities)

# --- 8. Family & Social History ---
class FamilyHistoryItem(BaseModel):
    condition: str
    relationship: str
    status: Optional[str] = "reported"

class SmokingHistory(BaseModel):
    status: Optional[str] = "no" # yes, no, former
    verified: Optional[bool] = False

class AlcoholHistory(BaseModel):
    status: Optional[str] = "no" # no, occasional, moderate, heavy
    verified: Optional[bool] = False

class SocialHistory(BaseModel):
    smoking: SmokingHistory = Field(default_factory=SmokingHistory)
    alcohol: AlcoholHistory = Field(default_factory=AlcoholHistory)
    occupation: Optional[str] = None
    living_situation: Optional[str] = None

# --- 9. Immunizations & Vitals ---
class ImmunizationItem(BaseModel):
    vaccine: str
    doses: Optional[int] = 1
    last_dose_date: Optional[str] = None

class VitalRecord(BaseModel):
    date: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    blood_pressure: Optional[str] = None
    heart_rate: Optional[int] = None
    temperature_c: Optional[float] = None
    oxygen_saturation: Optional[int] = None

# --- 10. Cognitive, Reproductive, Preferences ---
class MentalCognitiveStatus(BaseModel):
    cognitive_status: Optional[str] = "normal"
    known_conditions: List[str] = Field(default_factory=list)
    communication_needs: List[str] = Field(default_factory=list)

class ReproductiveHealth(BaseModel):
    status: Optional[str] = "unknown"
    pregnancy_status: Optional[str] = "not_applicable"

class PreviousEncounterRecord(BaseModel):
    encounter_id: Optional[str] = None
    date: Optional[str] = None
    chief_complaint: Optional[str] = None
    summary: Optional[str] = None
    diagnosis: Optional[str] = None
    outcome: Optional[str] = None

class DocumentRecord(BaseModel):
    document_id: Optional[str] = None
    type: Optional[str] = None
    date: Optional[str] = None
    summary: Optional[str] = None

class PatientPreferences(BaseModel):
    preferred_language: Optional[str] = "English"
    communication_mode: Optional[str] = "text"
    accessibility_needs: List[str] = Field(default_factory=list)

class StatementMemory(BaseModel):
    statement: str
    date: Optional[str] = None
    source: Optional[str] = "patient"
    verified: Optional[bool] = False

class ChatbotMemory(BaseModel):
    important_patient_statements: List[StatementMemory] = Field(default_factory=list)
    recent_concerns: List[Dict[str, Any]] = Field(default_factory=list)
    pending_questions: List[Dict[str, Any]] = Field(default_factory=list)

class Provenance(BaseModel):
    last_updated: Optional[str] = None
    last_updated_by: Optional[str] = "system"
    profile_version: Optional[int] = 1

# --- Root Longitudinal Profile Schema (Version 1.0) ---
class LongitudinalProfileSchema(BaseModel):
    schema_version: str = "1.0"
    patient: PatientProfileDemographics = Field(default_factory=PatientProfileDemographics)
    medical_history: MedicalHistory = Field(default_factory=MedicalHistory)
    medications: Medications = Field(default_factory=Medications)
    anatomical_status: AnatomicalStatus = Field(default_factory=AnatomicalStatus)
    medical_devices: List[MedicalDevice] = Field(default_factory=list)
    sensory_status: SensoryStatus = Field(default_factory=SensoryStatus)
    functional_status: FunctionalStatus = Field(default_factory=FunctionalStatus)
    family_history: List[FamilyHistoryItem] = Field(default_factory=list)
    social_history: SocialHistory = Field(default_factory=SocialHistory)
    immunizations: List[ImmunizationItem] = Field(default_factory=list)
    vital_history: List[VitalRecord] = Field(default_factory=list)
    mental_cognitive_status: MentalCognitiveStatus = Field(default_factory=MentalCognitiveStatus)
    reproductive_health: ReproductiveHealth = Field(default_factory=ReproductiveHealth)
    current_symptoms: List[Any] = Field(default_factory=list)
    red_flags: List[Any] = Field(default_factory=list)
    previous_encounters: List[PreviousEncounterRecord] = Field(default_factory=list)
    documents: List[DocumentRecord] = Field(default_factory=list)
    patient_preferences: PatientPreferences = Field(default_factory=PatientPreferences)
    chatbot_memory: ChatbotMemory = Field(default_factory=ChatbotMemory)
    provenance: Provenance = Field(default_factory=Provenance)
