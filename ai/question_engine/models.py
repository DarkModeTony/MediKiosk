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
