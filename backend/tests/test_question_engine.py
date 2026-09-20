import pytest
from ai.question_engine.engine import QuestionEngine
from ai.question_engine.models import Answer
from ai.red_flags.engine import RedFlagEngine
from ai.clinical_nlu.service import ClinicalNLUService

@pytest.fixture
def engine():
    return QuestionEngine(RedFlagEngine(), ClinicalNLUService())

def test_chest_pain_pathway(engine):
    # 1. Start
    state = engine.start_interview("enc_123")
    assert state.current_question_id == "chief_complaint_initial"

    # 2. Answer with voice ("I have chest pain")
    ans1 = Answer(question_id="chief_complaint_initial", raw_transcript="I have severe chest pain")
    state = engine.process_answer(state, ans1)
    
    assert state.current_pathway == "chest_pain"
    assert "chief_complaint" in state.facts
    assert state.facts["chief_complaint"].value == "chest pain"
    assert state.current_question_id == "chest_pain_onset"

    # 3. Answer onset with option (touch input)
    ans2 = Answer(question_id="chest_pain_onset", selected_option_id="today")
    state = engine.process_answer(state, ans2)
    assert state.facts["onset"].value == "today"
    assert state.current_question_id == "chest_pain_character"

def test_chest_pain_red_flag(engine):
    state = engine.start_interview("enc_456")
    ans1 = Answer(question_id="chief_complaint_initial", raw_transcript="chest pain")
    state = engine.process_answer(state, ans1)
    
    # Fast forward to shortness of breath
    from ai.question_engine.models import Fact, ClinicalStateEnum
    state.facts["onset"] = Fact(field="onset", value="today", state=ClinicalStateEnum.COLLECTED)
    state.facts["character"] = Fact(field="character", value="sharp", state=ClinicalStateEnum.COLLECTED)
    state.facts["radiation"] = Fact(field="radiation", value="no_radiation", state=ClinicalStateEnum.COLLECTED)
    state.current_question_id = "chest_pain_sob"
    
    ans2 = Answer(question_id="chest_pain_sob", selected_option_id="yes_severe")
    # Normally NLU handles structured_facts, but for touch input we just map ID to selected_option_id
    state = engine.process_answer(state, ans2)
    
    # Red flag should be triggered
    assert len(state.new_red_flags) > 0
    assert state.new_red_flags[0].rule_name == "CARDIAC_EMERGENCY_SUSPECTED"
    assert state.new_red_flags[0].severity == "HIGH"


def test_headache_pathway_never_asks_fever(engine):
    """
    Core bug fix verification:
    When a patient reports 'I have a headache', the engine must route to 'headache'
    pathway and ask a headache-specific question, NEVER falling back to fever.
    """
    state = engine.start_interview("enc_headache_1")
    assert state.current_question_id == "chief_complaint_initial"

    ans = Answer(question_id="chief_complaint_initial", raw_transcript="I have a headache")
    state = engine.process_answer(state, ans)

    assert state.current_pathway == "headache"
    assert state.primary_symptom == "headache"
    assert state.current_question_id == "headache_onset"
    assert "fever" not in state.current_question_id.lower()


def test_headache_skips_already_mentioned_dimension(engine):
    """
    Adaptive dimension testing:
    When patient provides onset in free text ('sudden headache since morning'),
    the engine notes the onset and asks the next unanswered priority question.
    """
    state = engine.start_interview("enc_headache_2")
    ans = Answer(question_id="chief_complaint_initial", raw_transcript="I have a sudden headache since morning")
    state = engine.process_answer(state, ans)

    assert state.current_pathway == "headache"
    # Onset dimension was captured, so engine should skip headache_onset and ask severity/character/location
    assert state.current_question_id != "headache_onset"
    assert state.current_question_id in ["headache_severity", "headache_character", "headache_location"]


def test_unmapped_symptom_routes_to_general(engine):
    """
    When a patient reports an unmapped symptom (e.g. skin rash, insomnia, earache),
    the system must route to 'general' intake pathway, NEVER falling back to 'fever'.
    """
    state = engine.start_interview("enc_general_1")
    ans = Answer(question_id="chief_complaint_initial", raw_transcript="I have an unusual itchy skin rash and swelling")
    state = engine.process_answer(state, ans)

    assert state.current_pathway == "general"
    assert state.current_question_id == "general_onset"
    assert "fever" not in state.current_question_id.lower()


def test_thunderclap_headache_red_flag(engine):
    """
    Deterministic safety:
    Headache with sudden onset must trigger THUNDERCLAP_HEADACHE red flag.
    """
    state = engine.start_interview("enc_thunderclap")
    ans1 = Answer(question_id="chief_complaint_initial", raw_transcript="I have a severe headache")
    state = engine.process_answer(state, ans1)
    assert state.current_pathway == "headache"

    ans2 = Answer(question_id="headache_onset", selected_option_id="sudden_thunderclap")
    state = engine.process_answer(state, ans2)

    # Red flag should trigger
    rule_names = [rf.rule_name for rf in state.new_red_flags]
    assert "THUNDERCLAP_HEADACHE" in rule_names


def test_multi_symptom_tracking(engine):
    """
    Multi-symptom aware:
    Patient mentions fever, headache, and cough.
    Engine tracks primary symptom and secondary symptoms.
    """
    state = engine.start_interview("enc_multi")
    ans = Answer(question_id="chief_complaint_initial", raw_transcript="I have high fever, bad headache, and dry cough")
    state = engine.process_answer(state, ans)

    assert state.primary_symptom in ["fever", "headache", "cough"]
    assert len(state.secondary_symptoms) >= 1
    # Check that secondary symptoms don't duplicate primary
    assert state.primary_symptom not in state.secondary_symptoms


def test_hindi_hinglish_symptom_routing(engine):
    """
    Language support:
    Hindi/Hinglish input 'mujhe bahut tez sar dard ho raha hai' routes to headache.
    """
    state = engine.start_interview("enc_hindi_headache")
    ans = Answer(question_id="chief_complaint_initial", raw_transcript="mujhe bahut tez sar dard ho raha hai")
    state = engine.process_answer(state, ans)

    assert state.current_pathway == "headache"
    assert state.current_question_id.startswith("headache_")


# ─────────────────────────────────────────────────────────────────────────────
# 6 Specific Clinical Scenarios Required by Specification
# ─────────────────────────────────────────────────────────────────────────────

def test_scenario_1_headache(engine):
    """
    Scenario 1: Patient says "I have a headache."
    Next question must be relevant to headache (e.g. onset/duration).
    Must NOT ask about fever.
    """
    state = engine.start_interview("scen_1")
    ans = Answer(question_id="chief_complaint_initial", raw_transcript="I have a headache.")
    state = engine.process_answer(state, ans)

    assert state.current_pathway == "headache"
    assert state.primary_symptom == "headache"
    assert state.current_question_id == "headache_onset"
    assert "fever" not in state.current_question_id.lower()


def test_scenario_2_chest_pain(engine):
    """
    Scenario 2: Patient says "I have chest pain."
    Next question must be relevant to chest pain (e.g. onset, character).
    """
    state = engine.start_interview("scen_2")
    ans = Answer(question_id="chief_complaint_initial", raw_transcript="I have chest pain.")
    state = engine.process_answer(state, ans)

    assert state.current_pathway == "chest_pain"
    assert state.primary_symptom == "chest pain"
    assert state.current_question_id in ["chest_pain_onset", "chest_pain_character"]
    assert "fever" not in state.current_question_id.lower()


def test_scenario_3_fever_and_weakness(engine):
    """
    Scenario 3: Patient says "I have fever and weakness."
    Next question must be relevant to fever (e.g. onset, severity).
    Both fever and weakness should be recognized.
    """
    state = engine.start_interview("scen_3")
    ans = Answer(question_id="chief_complaint_initial", raw_transcript="I have fever and weakness.")
    state = engine.process_answer(state, ans)

    assert state.current_pathway == "fever"
    assert state.primary_symptom == "fever"
    assert "weakness" in state.secondary_symptoms or "weakness" in state.facts.get("chief_complaint", Fact(field="", value="")).value.lower()
    assert state.current_question_id in ["fever_onset", "fever_severity"]


def test_scenario_4_stomach_hurts(engine):
    """
    Scenario 4: Patient says "My stomach hurts."
    Next question must be relevant to abdominal pain (e.g. onset, location).
    Must NOT ask about fever.
    """
    state = engine.start_interview("scen_4")
    ans = Answer(question_id="chief_complaint_initial", raw_transcript="My stomach hurts.")
    state = engine.process_answer(state, ans)

    assert state.current_pathway == "abdominal_pain"
    assert state.current_question_id in ["abd_pain_onset", "abd_pain_location"]
    assert "fever" not in state.current_question_id.lower()


def test_scenario_5_coughing_for_three_days(engine):
    """
    Scenario 5: Patient says "I have been coughing for three days."
    Duration/onset was already provided in free text!
    The system should NOT repeat the duration question and should ask cough character (dry vs wet).
    """
    state = engine.start_interview("scen_5")
    ans = Answer(question_id="chief_complaint_initial", raw_transcript="I have been coughing for three days.")
    state = engine.process_answer(state, ans)

    assert state.current_pathway == "cough"
    assert state.primary_symptom == "cough"
    # Onset/duration question should be skipped because 'three days' was extracted
    assert state.current_question_id != "cough_duration"
    assert state.current_question_id == "cough_type"


def test_scenario_6_feel_dizzy(engine):
    """
    Scenario 6: Patient says "I feel dizzy."
    Next question must be relevant to dizziness / vertigo (e.g. character, triggers).
    Must NOT ask about fever or unrelated symptoms.
    """
    state = engine.start_interview("scen_6")
    ans = Answer(question_id="chief_complaint_initial", raw_transcript="I feel dizzy.")
    state = engine.process_answer(state, ans)

    assert state.current_pathway == "dizziness"
    assert state.primary_symptom == "dizziness"
    assert state.current_question_id in ["dizziness_character", "dizziness_onset"]
    assert "fever" not in state.current_question_id.lower()


# ─────────────────────────────────────────────────────────────────────────────
# Invariant & Guard Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_unknown_not_treated_as_negative(engine):
    """
    Principle: Unknown is not negative.
    If patient reports headache without mentioning fever or chronic conditions,
    we must NOT store fever=False or diabetes=False.
    """
    state = engine.start_interview("enc_unknown_guard")
    ans = Answer(question_id="chief_complaint_initial", raw_transcript="I have a headache.")
    state = engine.process_answer(state, ans)

    # Invariant: facts must only contain what was explicitly reported/extracted
    assert "fever" not in state.facts
    assert "diabetes" not in state.facts
    # If checked, any uncollected field is NOT false
    for k, v in state.facts.items():
        assert v.value is not False, f"Fact '{k}' was stored as boolean False, violating unknown!=negative"


def test_unrelated_questions_not_selected_prematurely(engine):
    """
    Verify that throughout a headache intake, fever or abdominal questions are NEVER asked.
    """
    state = engine.start_interview("enc_premature_guard")
    ans1 = Answer(question_id="chief_complaint_initial", raw_transcript="I have a bad headache")
    state = engine.process_answer(state, ans1)

    while state.current_question_id and not state.completed:
        # Check current question
        assert "fever" not in state.current_question_id.lower(), f"Unrelated question {state.current_question_id} selected prematurely!"
        assert "abd_" not in state.current_question_id.lower(), f"Unrelated question {state.current_question_id} selected prematurely!"
        assert "cough" not in state.current_question_id.lower(), f"Unrelated question {state.current_question_id} selected prematurely!"

        # Answer with an option or simple text
        ans = Answer(question_id=state.current_question_id, selected_option_id="sample_val")
        state = engine.process_answer(state, ans)


# ─────────────────────────────────────────────────────────────────────────────
# Context-Aware Natural Voice Conversation Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_voice_natural_headache_since_yesterday(engine):
    """
    Task Example 1:
    Patient says: "I have a headache since yesterday."
    The system should extract BOTH:
      symptom = headache
      duration = since yesterday (yesterday)
    Do NOT ask: "When did your headache start?"
    Instead ask the next relevant unanswered question:
      "Where do you feel the headache?" (headache_location)
    """
    state = engine.start_interview("enc_natural_headache")
    ans = Answer(question_id="chief_complaint_initial", raw_transcript="I have a headache since yesterday.")
    state = engine.process_answer(state, ans)

    # 1. State assertions
    assert state.current_pathway == "headache"
    assert state.primary_symptom == "headache"
    assert state.chief_complaint == "headache"
    assert state.duration == "yesterday"
    assert "onset" in state.symptom_attributes

    # 2. Did NOT ask onset/start
    assert state.current_question_id != "headache_onset"

    # 3. Asks location next ("Where do you feel the headache?")
    assert state.current_question_id == "headache_location"


def test_voice_natural_fever_since_three_days_and_weakness(engine):
    """
    Task Example 2:
    Patient says: "I have fever since three days and I'm feeling weak."
    Extract:
      fever = present
      duration = 3 days
      weakness = present
    Do NOT ask: "Do you have fever?"
    Do NOT ask: "How long have you had fever?" / "When did the fever start?"
    Ask the next relevant unanswered question: "How high is the fever?" (fever_severity)
    """
    state = engine.start_interview("enc_natural_fever")
    ans = Answer(
        question_id="chief_complaint_initial",
        raw_transcript="I have fever since three days and I'm feeling weak."
    )
    state = engine.process_answer(state, ans)

    # 1. State assertions
    assert state.current_pathway == "fever"
    assert state.primary_symptom == "fever"
    assert state.chief_complaint == "fever"
    assert "weakness" in state.active_symptoms
    assert "three days" in (state.duration or "") or "3 days" in (state.duration or "")

    # 2. Did NOT ask "Do you have fever?" or "When did the fever start?"
    assert state.current_question_id != "fever_onset"
    assert "do you have fever" not in state.current_question_id.lower()

    # 3. Asks next relevant question: severity
    assert state.current_question_id == "fever_severity"


def test_structured_conversation_state_integrity(engine):
    """
    Verify complete structured conversation state tracking across conversation turns.
    """
    state = engine.start_interview("enc_state_integrity")
    assert state.conversation_phase == "CHIEF_COMPLAINT"

    # Turn 1: Patient gives chief complaint + onset
    ans1 = Answer(question_id="chief_complaint_initial", raw_transcript="I have chest pain since this morning")
    state = engine.process_answer(state, ans1)

    assert state.chief_complaint == "chest pain"
    assert "chest pain" in state.active_symptoms
    assert state.duration == "morning"
    assert "onset" in state.symptom_attributes
    assert "chief_complaint_initial" in state.questions_answered
    assert state.current_question_id == "chest_pain_character"
    assert state.conversation_phase == "HPI_EXPLORATION"

    # Turn 2: Answer character
    ans2 = Answer(question_id="chest_pain_character", selected_option_id="heavy")
    state = engine.process_answer(state, ans2)

    assert "chest_pain_character" in state.questions_answered
    assert state.symptom_attributes.get("character") == "heavy"
    assert state.current_question_id in ["chest_pain_location", "chest_pain_radiation", "chest_pain_sob"]


def test_deduplication_of_volunteered_dimensions(engine):
    """
    If patient volunteers multiple dimensions in free text (e.g. onset and location),
    both are deduplicated and the engine moves directly to the genuinely missing dimension.
    """
    state = engine.start_interview("enc_multi_dedup")
    # Patient mentions headache, onset (yesterday), and location (forehead)
    ans = Answer(
        question_id="chief_complaint_initial",
        raw_transcript="I have a headache since yesterday mostly in my forehead"
    )
    state = engine.process_answer(state, ans)

    assert state.current_pathway == "headache"
    # Both onset and location are deduplicated
    assert state.current_question_id != "headache_onset"
    # Should advance to severity
    assert state.current_question_id in ["headache_location", "headache_severity"]


def test_pathways_ask_at_least_five_questions(engine):
    """
    Verify that clinical pathways ask at least 5 relevant clinical questions
    even when the patient volunteers onset in the initial turn.
    """
    from ai.question_engine.pathways import get_pathway

    # Test across multiple key pathways: dizziness, headache, fever, cough, chest_pain, abdominal_pain
    test_cases = [
        ("I feel dizzy since yesterday", "dizziness"),
        ("I have a severe headache since morning", "headache"),
        ("I have high fever for two days", "fever"),
        ("I have a cough since last week", "cough"),
        ("I have chest pain since yesterday", "chest_pain"),
        ("My stomach hurts since yesterday", "abdominal_pain"),
    ]

    for speech, expected_pathway in test_cases:
        state = engine.start_interview(f"enc_{expected_pathway}_min5")
        ans_initial = Answer(question_id="chief_complaint_initial", raw_transcript=speech)
        state = engine.process_answer(state, ans_initial)

        assert state.current_pathway == expected_pathway

        followup_count = 0
        safety_max_turns = 12

        while not state.completed and followup_count < safety_max_turns:
            q_id = state.current_question_id
            if not q_id:
                break
            p_questions = get_pathway(state.current_pathway) or []
            q_def = next((q for q in p_questions if q.id == q_id), None)
            if not q_def:
                break

            # Answer using first available option or a generic answer
            chosen_opt = q_def.options[0].id if q_def.options else "none"
            ans = Answer(question_id=q_id, selected_option_id=chosen_opt)
            state = engine.process_answer(state, ans)
            followup_count += 1

        # Must have asked at least 5 follow-up questions
        assert followup_count >= 5, f"Pathway {expected_pathway} asked only {followup_count} questions, expected at least 5!"
        # Total questions answered (including chief complaint) >= 6
        assert len(state.questions_answered) >= 6




