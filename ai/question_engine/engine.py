from typing import Dict, Any, List
from .models import ClinicalState, Answer, Fact, ClinicalStateEnum
from .pathways import get_pathway

class QuestionEngine:
    def __init__(self, red_flag_engine, nlu_service):
        self.red_flag_engine = red_flag_engine
        self.nlu_service = nlu_service

    def start_interview(self, encounter_id: str) -> ClinicalState:
        # The first question is always identifying the chief complaint
        return ClinicalState(
            encounter_id=encounter_id,
            current_pathway="chief_complaint",
            current_question_id="chief_complaint_initial",
            facts={},
            status="IN_PROGRESS"
        )

    def process_answer(self, state: ClinicalState, answer: Answer) -> ClinicalState:
        """
        The central state machine for the clinical interview.
        """
        # 1. Normalize / Extract Facts via NLU
        if answer.raw_transcript:
            structured_facts = self.nlu_service.extract_facts(answer.raw_transcript, answer.question_id)
        elif answer.selected_option_id:
            # Simple touch input to fact mapping: need to map question_id to clinical_field
            clinical_field = answer.question_id # default
            if state.current_pathway:
                pathway = get_pathway(state.current_pathway)
                if pathway:
                    for q in pathway:
                        if q.id == answer.question_id:
                            clinical_field = q.clinical_field
                            break
            structured_facts = {clinical_field: answer.selected_option_id}
        else:
            structured_facts = {}

        # 2. Update Clinical State (Facts)
        for field, value in structured_facts.items():
            state.facts[field] = Fact(field=field, value=value, state=ClinicalStateEnum.COLLECTED)

        # 3. Determine Pathway if this was the chief complaint question
        if state.current_question_id == "chief_complaint_initial":
            complaint = structured_facts.get("chief_complaint", "").lower()
            # simple mock routing
            if "chest" in complaint or "सीने" in complaint:
                state.current_pathway = "chest_pain"
            elif "fever" in complaint:
                state.current_pathway = "fever"
            elif "stomach" in complaint or "abdomen" in complaint:
                state.current_pathway = "abdominal_pain"
            elif "headache" in complaint:
                state.current_pathway = "headache"
            elif "cough" in complaint:
                state.current_pathway = "cough"
            elif "vomit" in complaint:
                state.current_pathway = "vomiting"
            else:
                # Default fallback
                state.current_pathway = "fever"

        # 4. Red Flag Evaluation
        red_flags = self.red_flag_engine.evaluate(state.facts)
        # Store red flags on state for easy retrieval (FastAPI layer will persist them)
        if not hasattr(state, "new_red_flags"):
            state.new_red_flags = []
        state.new_red_flags.extend(red_flags)

        # 5. Determine Next Question
        pathway_questions = get_pathway(state.current_pathway)
        if not pathway_questions:
            state.completed = True
            state.current_question_id = None
            return state

        # Find the next unanswered question in the pathway
        next_q_id = None
        for q in pathway_questions:
            if q.clinical_field not in state.facts:
                next_q_id = q.id
                break

        # 6. Check Completion
        if next_q_id:
            state.current_question_id = next_q_id
        else:
            state.completed = True
            state.current_question_id = None
            state.status = "COMPLETED"

        return state
