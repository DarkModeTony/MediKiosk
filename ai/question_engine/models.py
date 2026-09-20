from enum import Enum
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ClinicalStateEnum(str, Enum):
    COLLECTED = "COLLECTED"
    NOT_ASKED = "NOT_ASKED"
    DENIED = "DENIED"
    UNKNOWN = "UNKNOWN"

class InputType(str, Enum):
    VOICE_OR_OPTIONS = "VOICE_OR_OPTIONS"
    VOICE_ONLY = "VOICE_ONLY"

class Option(BaseModel):
    id: str
    label: str

class Question(BaseModel):
    id: str
    text: str
    category: str
    input_type: InputType
    clinical_field: str
    options: Optional[List[Option]] = None
    required: bool = True
    domain: Optional[str] = None  # e.g., 'headache', 'chest_pain', 'fever', 'cough', 'abdominal_pain', 'dizziness'
    symptom: Optional[str] = None  # primary clinical symptom target
    clinical_dimension: Optional[str] = None  # 'onset', 'duration', 'character', 'location', 'radiation', 'severity', 'associated', 'red_flag'
    dimension: Optional[str] = None  # legacy / shorthand alias
    priority: int = 10  # Lower number = higher priority
    depends_on: Optional[str] = None  # prerequisite field or symptom required before asking
    dependency_value: Optional[Any] = None  # specific expected value or list of values for depends_on
    red_flag: bool = False  # indicates question is a safety/red-flag screening question
    applicable_to: Optional[List[str]] = None  # list of symptoms or contexts where question is applicable

    def __init__(self, **data: Any):
        if "question_id" in data and "id" not in data:
            data["id"] = data["question_id"]
        if "clinical_dimension" in data and "dimension" not in data:
            data["dimension"] = data["clinical_dimension"]
        elif "dimension" in data and "clinical_dimension" not in data:
            data["clinical_dimension"] = data["dimension"]
        super().__init__(**data)

    @property
    def question_id(self) -> str:
        return self.id

class Answer(BaseModel):
    question_id: str
    raw_transcript: Optional[str] = None
    selected_option_id: Optional[str] = None
    structured_facts: Dict[str, Any] = {}

class Fact(BaseModel):
    field: str
    value: Any
    state: ClinicalStateEnum = ClinicalStateEnum.COLLECTED

class ClinicalState(BaseModel):
    encounter_id: str
    status: str = "IN_PROGRESS"
    current_pathway: Optional[str] = None
    current_question_id: Optional[str] = None
    facts: Dict[str, Fact] = {}
    new_red_flags: List[Any] = []
    completed: bool = False
    primary_symptom: Optional[str] = None
    secondary_symptoms: List[str] = []
    dimensions_explored: Dict[str, bool] = {}
    conversation_turns: List[Dict[str, Any]] = []

    # Structured context-aware clinical conversation state
    chief_complaint: Optional[str] = None
    active_symptoms: List[str] = []
    symptom_attributes: Dict[str, Any] = {}
    duration: Optional[str] = None
    severity: Optional[str] = None
    location: Optional[str] = None
    associated_symptoms: List[str] = []
    medications: List[str] = []
    allergies: List[str] = []
    chronic_conditions: List[str] = []
    relevant_history: Dict[str, Any] = {}
    questions_answered: List[str] = []
    questions_still_required: List[str] = []
    red_flags_assessed: List[str] = []
    conversation_phase: str = "CHIEF_COMPLAINT"
