from ai.question_engine.models import Question, InputType, Option

def get_general_pathway():
    """
    Comprehensive general clinical inquiry pathway for non-specific complaints (7 questions):
    1. Onset: When did the discomfort or symptoms begin
    2. Severity: Mild, moderate, severe impact
    3. Progression / Trajectory: Getting worse, same, improving, episodic
    4. Functional Impact: Ability to work, sleep, walk, or eat
    5. Constitutional Symptoms: Fever, chills, body pain, exhaustion
    6. Systemic Review: Cough, breathlessness, nausea, vomiting
    7. Red Flag Screening: Chest pain, severe dizziness, blacking out
    """
    return [
        Question(
            id="general_onset",
            text="When did these symptoms first begin?",
            category="HPI",
            domain="general",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="onset",
            clinical_dimension="onset",
            priority=1,
            required=True,
            options=[
                Option(id="today", label="Earlier today"),
                Option(id="yesterday", label="Yesterday"),
                Option(id="days_ago", label="A few days ago"),
                Option(id="weeks_ago", label="More than a week ago"),
            ],
        ),
        Question(
            id="general_severity",
            text="How severe is your discomfort right now?",
            category="HPI",
            domain="general",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="severity",
            clinical_dimension="severity",
            priority=2,
            required=True,
            options=[
                Option(id="mild", label="Mild — noticeable but manageable"),
                Option(id="moderate", label="Moderate — hard to carry out daily tasks"),
                Option(id="severe", label="Severe — unable to function normally"),
            ],
        ),
        Question(
            id="general_progression",
            text="Is the condition improving, staying the same, or getting worse?",
            category="HPI",
            domain="general",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="progression",
            clinical_dimension="timing",
            priority=3,
            required=False,
            options=[
                Option(id="getting_worse", label="Getting progressively worse"),
                Option(id="same", label="Staying about the same"),
                Option(id="improving", label="Gradually improving"),
                Option(id="comes_and_goes", label="Comes and goes in episodes"),
            ],
        ),
        Question(
            id="general_impact",
            text="Is this condition affecting your ability to eat, sleep, or walk normally?",
            category="HPI",
            domain="general",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="functional_impact",
            clinical_dimension="functional_impact",
            priority=4,
            required=False,
            options=[
                Option(id="unable_to_work", label="Unable to work or do daily chores"),
                Option(id="disturbed_sleep", label="Disturbing sleep at night"),
                Option(id="loss_of_appetite", label="Cannot eat / total loss of appetite"),
                Option(id="minimal_impact", label="Managing normal routine with effort"),
            ],
        ),
        Question(
            id="general_fever_pain",
            text="Are you having any fever, chills, or widespread body aches?",
            category="Associated Symptoms",
            domain="general",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="fever_aches",
            clinical_dimension="associated_fever",
            priority=5,
            required=False,
            options=[
                Option(id="fever_chills", label="Fever or feeling shivering cold"),
                Option(id="body_aches", label="Severe muscle or body ache"),
                Option(id="extreme_fatigue", label="Extreme fatigue or weakness"),
                Option(id="no_fever", label="No fever or body ache"),
            ],
        ),
        Question(
            id="general_gi_resp",
            text="Do you have any cough, difficulty breathing, nausea, or vomiting?",
            category="Associated Symptoms",
            domain="general",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="gi_resp",
            clinical_dimension="associated_systemic",
            priority=6,
            required=False,
            options=[
                Option(id="cough_breath", label="Cough or breathlessness"),
                Option(id="nausea_vomiting", label="Nausea, vomiting, or loose motions"),
                Option(id="none", label="No breathing or stomach symptoms"),
            ],
        ),
        Question(
            id="general_associated",
            text="Have you had any chest discomfort, severe dizziness, or fainting?",
            category="Associated Symptoms",
            domain="general",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="associated_symptoms",
            clinical_dimension="red_flag",
            priority=7,
            required=True,
            red_flag=True,
            options=[
                Option(id="chest_discomfort", label="Chest pain or pressure"),
                Option(id="severe_dizziness", label="Severe room-spinning dizziness"),
                Option(id="blackout_faint", label="Nearly fainted or blacked out"),
                Option(id="no_other", label="No critical symptoms like these"),
            ],
        ),
    ]
