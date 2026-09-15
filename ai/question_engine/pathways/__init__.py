from ..models import Question, InputType
from .fever import get_fever_pathway
from .chest_pain import get_chest_pain_pathway
from .abdominal_pain import get_abdominal_pain_pathway
from .headache import get_headache_pathway
from .cough import get_cough_pathway
from .vomiting import get_vomiting_pathway

def get_chief_complaint_pathway():
    return [
        Question(
            id="chief_complaint_initial",
            text="What brings you here today?",
            category="HPI",
            input_type=InputType.VOICE_ONLY,
            clinical_field="chief_complaint",
            options=None,
            required=True
        )
    ]

def get_pathway(pathway_name: str):
    pathways = {
        "chief_complaint": get_chief_complaint_pathway(),
        "fever": get_fever_pathway(),
        "chest_pain": get_chest_pain_pathway(),
        "abdominal_pain": get_abdominal_pain_pathway(),
        "headache": get_headache_pathway(),
        "cough": get_cough_pathway(),
        "vomiting": get_vomiting_pathway()
    }
    return pathways.get(pathway_name)

