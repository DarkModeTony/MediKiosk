import logging
from typing import Dict, Any, List, Optional
from .models import ClinicalState, Answer, Fact, ClinicalStateEnum, Question
from .pathways import get_pathway

logger = logging.getLogger("question_engine")

class QuestionEngine:
    """
    Adaptive Clinical Conversation Engine for Patient Intake.
    
    Key Features:
    - Multi-symptom aware: Identifies primary chief complaint and secondary symptoms.
    - Eliminates blind 'fever' fallback: Unmapped complaints route to 'general' intake pathway.
    - Clinical Dimension Exploration: Tracks Onset, Character, Location, Radiation, Severity, Associated Symptoms.
    - Red-Flag Prioritization: Probes red-flag indicators first (e.g. thunderclap headache, shortness of breath).
    - Intelligent Question Skipping: Automatically skips asking dimensions already volunteered by patient.
    """

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
            status="IN_PROGRESS",
            primary_symptom=None,
            secondary_symptoms=[],
            dimensions_explored={},
            conversation_turns=[],
        )

    def _determine_pathway(self, complaint: str, all_symptoms: List[str], transcript: str) -> tuple[str, str]:
        """
        Determines the clinical pathway and normalized primary symptom from the complaint text
        and extracted symptom entities.
        
        Returns:
            (pathway_name, primary_symptom_name)
        """
        text = f"{complaint} {' '.join(all_symptoms)} {transcript}".lower()

        # 1. Headache (migraine, cephalalgia, head pain)
        headache_kw = [
            "headache", "head pain", "head hurts", "sar dard", "sir dard", 
            "sar me dard", "sir me dard", "migraine", "matha", "माथा", 
            "सिर दर्द", "सर दर्द", "सिर में दर्द", "सर में दर्द"
        ]
        if any(kw in text for kw in headache_kw):
            return "headache", "headache"

        # 2. Chest pain / Cardiac (pressure, angina, chhati me dard)
        chest_kw = [
            "chest pain", "chest", "सीने में दर्द", "सीने", "छाती", 
            "heart pain", "chhati", "angina", "chest discomfort"
        ]
        if any(kw in text for kw in chest_kw):
            return "chest_pain", "chest pain"

        # 3. Abdominal / Stomach (gastric, pet dard, acidity, cramping)
        abdominal_kw = [
            "stomach pain", "stomach ache", "abdominal pain", "stomach", 
            "abdominal", "pet dard", "pet me dard", "पेट में दर्द", 
            "पेट दर्द", "पेट", "belly pain", "tummy ache", "cramps"
        ]
        if any(kw in text for kw in abdominal_kw):
            return "abdominal_pain", "abdominal pain"

        # 4. Cough / Respiratory (khansi, phlegm, bronchitis)
        cough_kw = ["cough", "खांसी", "khansi", "balgham", "phlegm", "coughing"]
        if any(kw in text for kw in cough_kw):
            return "cough", "cough"

        # 5. Vomiting / Gastrointestinal (ulti, nausea, puking)
        vomit_kw = ["vomit", "vomiting", "उल्टी", "nausea", "जी मिचलाना", "ulti", "throwing up", "puking"]
        if any(kw in text for kw in vomit_kw):
            return "vomiting", "vomiting"

        # 6. Dizziness / Vertigo (chakkar, lightheaded, faint)
        dizzy_kw = ["dizzy", "dizziness", "chakkar", "चक्कर", "lightheaded", "faint", "vertigo", "सिर चकराना"]
        if any(kw in text for kw in dizzy_kw):
            return "dizziness", "dizziness"

        # 7. Fever / Pyrexia (bukhar, chills, high temperature)
        fever_kw = ["fever", "high fever", "बुखार", "ताप", "temperature", "bukhar", "tez bukhar", "तेज बुखार"]
        if any(kw in text for kw in fever_kw):
            return "fever", "fever"

        # 8. General Symptom Fallback (NEVER default blindly to fever!)
        clean_complaint = complaint.strip() or transcript.strip() or "general discomfort"
        return "general", clean_complaint

    def process_answer(self, state: ClinicalState, answer: Answer) -> ClinicalState:
        """
        Adaptive central state machine for the clinical interview.
        Context-aware selection based on chief complaint, extracted symptoms,
        answered dimensions, dependencies, and safety requirements.
        """
        # 1. Normalize / Extract Facts via NLU or Touch Input
        structured_facts: Dict[str, Any] = {}
        candidate_facts: List[Any] = []

        if answer.raw_transcript:
            structured_facts = self.nlu_service.extract_facts(answer.raw_transcript, answer.question_id)
            candidate_facts = structured_facts.pop("_candidate_facts", [])
        elif answer.selected_option_id:
            # Map question_id to clinical_field
            clinical_field = answer.question_id
            if state.current_pathway:
                pathway = get_pathway(state.current_pathway)
                if pathway:
                    for q in pathway:
                        if q.id == answer.question_id:
                            clinical_field = q.clinical_field
                            break
            structured_facts = {clinical_field: answer.selected_option_id}

        # Record conversation turn and answered questions
        turn_entry = {
            "question_id": answer.question_id,
            "pathway": state.current_pathway,
            "transcript": answer.raw_transcript,
            "selected_option": answer.selected_option_id,
        }
        if not hasattr(state, "conversation_turns") or state.conversation_turns is None:
            state.conversation_turns = []
        state.conversation_turns.append(turn_entry)

        if not hasattr(state, "questions_answered") or state.questions_answered is None:
            state.questions_answered = []
        if answer.question_id and answer.question_id not in state.questions_answered:
            state.questions_answered.append(answer.question_id)

        # 2. Update Clinical State Facts
        all_symptoms_extracted = structured_facts.pop("all_symptoms", [])

        for field, value in structured_facts.items():
            if value is not None and field != "":
                # Invariant: Unknown is not negative. If value is explicitly None or unknown, keep UNKNOWN.
                fact_state = ClinicalStateEnum.COLLECTED
                if value in [None, "unknown", "not_assessed"]:
                    fact_state = ClinicalStateEnum.UNKNOWN
                state.facts[field] = Fact(field=field, value=value, state=fact_state)
                if not hasattr(state, "dimensions_explored") or state.dimensions_explored is None:
                    state.dimensions_explored = {}
                state.dimensions_explored[field] = True

        # 3. Determine Pathway if this was the chief complaint question
        is_chief_complaint_turn = (
            state.current_question_id == "chief_complaint_initial" 
            or not state.current_pathway 
            or state.current_pathway == "chief_complaint"
        )

        if is_chief_complaint_turn:
            complaint = structured_facts.get("chief_complaint", "")
            raw_text = answer.raw_transcript or ""
            pathway, primary_symp = self._determine_pathway(complaint, all_symptoms_extracted, raw_text)

            state.current_pathway = pathway
            state.primary_symptom = primary_symp
            state.secondary_symptoms = [s for s in all_symptoms_extracted if s != primary_symp]

            # Guarantee that 'chief_complaint' fact is always recorded in state.facts
            state.facts["chief_complaint"] = Fact(
                field="chief_complaint",
                value=primary_symp or complaint or "Unspecified",
                state=ClinicalStateEnum.COLLECTED
            )

        # Synchronize structured conversation state attributes
        state.chief_complaint = state.primary_symptom or (state.facts.get("chief_complaint").value if "chief_complaint" in state.facts else None)
        symp_list = [state.primary_symptom] + state.secondary_symptoms
        state.active_symptoms = [s for s in dict.fromkeys(symp_list) if s]

        onset_fact = state.facts.get("onset") or state.facts.get("duration")
        state.duration = str(onset_fact.value) if onset_fact and onset_fact.value else None

        sev_fact = state.facts.get("severity")
        state.severity = str(sev_fact.value) if sev_fact and sev_fact.value else None

        loc_fact = state.facts.get("location")
        state.location = str(loc_fact.value) if loc_fact and loc_fact.value else None

        # Build symptom_attributes dictionary
        state.symptom_attributes = {
            k: v.value for k, v in state.facts.items() 
            if k in ["onset", "duration", "severity", "character", "location", "radiation", "progression", "triggers"]
        }

        # 4. Red Flag Evaluation (Deterministic Engine)
        red_flags = self.red_flag_engine.evaluate(state.facts)
        if not hasattr(state, "new_red_flags") or state.new_red_flags is None:
            state.new_red_flags = []
        state.new_red_flags.extend(red_flags)
        state.red_flags_assessed = [rf.rule_name for rf in red_flags]

        # 5. Determine Next Question Adaptively
        pathway_questions = get_pathway(state.current_pathway)
        if not pathway_questions:
            state.completed = True
            state.current_question_id = None
            state.status = "COMPLETED"
            state.conversation_phase = "COMPLETED"
            return state

        # Filter candidate questions using:
        # a) Questions already answered (by question_id, clinical_field, or clinical_dimension)
        # b) Dependency prerequisites (depends_on and dependency_value)
        # c) Context applicability (applicable_to)
        candidate_questions = []
        for q in pathway_questions:
            # Check if question ID already answered
            if q.id in state.questions_answered:
                continue

            # Check if field already answered
            field_answered = q.clinical_field in state.facts
            dim = q.clinical_dimension or q.dimension
            dim_answered = dim and dim in state.dimensions_explored
            
            # Special dimension checks for volunteered natural language facts
            if dim == "onset" and state.duration is not None:
                dim_answered = True
            if dim == "severity" and state.severity is not None:
                dim_answered = True
            if dim == "location" and state.location is not None:
                dim_answered = True

            if field_answered or dim_answered:
                continue

            # Check dependency requirement
            if q.depends_on:
                if q.depends_on not in state.facts:
                    # Prerequisite fact has not been collected yet
                    continue
                if q.dependency_value is not None:
                    dep_fact_val = str(state.facts[q.depends_on].value).lower()
                    if isinstance(q.dependency_value, (list, tuple, set)):
                        valid_vals = [str(v).lower() for v in q.dependency_value]
                        if dep_fact_val not in valid_vals:
                            continue
                    elif dep_fact_val != str(q.dependency_value).lower():
                        continue

            # Check applicability requirement
            if q.applicable_to:
                all_known_symptoms = [state.primary_symptom] + state.secondary_symptoms
                applicable = any(s in q.applicable_to for s in all_known_symptoms if s)
                if not applicable:
                    continue

            candidate_questions.append(q)

        # Sort candidate questions by priority:
        # 1. Red-flag screening questions with priority 1
        # 2. General clinical priority (lower number = higher priority)
        def sort_key(q: Question):
            base_priority = q.priority if hasattr(q, "priority") and q.priority is not None else 10
            return (0 if getattr(q, "red_flag", False) and base_priority == 1 else 1, base_priority)

        candidate_questions.sort(key=sort_key)
        state.questions_still_required = [q.id for q in candidate_questions]

        # 6. Check Completion & Phase Transition
        if candidate_questions:
            next_q = candidate_questions[0]
            state.current_question_id = next_q.id
            if next_q.red_flag and next_q.priority <= 2:
                state.conversation_phase = "RED_FLAGS"
            elif next_q.category == "Associated Symptoms":
                state.conversation_phase = "ASSOCIATED_SYMPTOMS"
            else:
                state.conversation_phase = "HPI_EXPLORATION"
        else:
            state.completed = True
            state.current_question_id = None
            state.status = "COMPLETED"
            state.conversation_phase = "COMPLETED"

        return state
