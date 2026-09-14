# Expose pathways
from .fever import get_fever_pathway
from .chest_pain import get_chest_pain_pathway
from .abdominal_pain import get_abdominal_pain_pathway
from .headache import get_headache_pathway
from .cough import get_cough_pathway
from .vomiting import get_vomiting_pathway

def get_pathway(pathway_name: str):
    pathways = {
        "fever": get_fever_pathway(),
        "chest_pain": get_chest_pain_pathway(),
        "abdominal_pain": get_abdominal_pain_pathway(),
        "headache": get_headache_pathway(),
        "cough": get_cough_pathway(),
        "vomiting": get_vomiting_pathway()
    }
    return pathways.get(pathway_name)
