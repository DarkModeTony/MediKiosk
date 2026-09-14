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
