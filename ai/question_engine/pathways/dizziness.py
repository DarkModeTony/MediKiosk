from ai.question_engine.models import Question, InputType, Option

def get_dizziness_pathway():
    """
    Comprehensive structured clinical pathway for dizziness and vertigo (7 questions):
    1. Character: Spinning / vertigo vs lightheadedness / presyncope vs unsteadiness vs floating
    2. Onset & Timing: Sudden vs gradual
    3. Episode Duration & Frequency: Seconds, minutes, hours, or constant
    4. Triggers: Positional changes (rolling over in bed, standing up, head turning)
    5. Severity & Function: Ability to stand, walk, or perform daily activities
    6. Ear & Auditory Symptoms: Hearing loss, ear fullness, or ringing (tinnitus)
    7. Associated Red Flags: Fainting (syncope), chest pain, palpitations, focal weakness/slurred speech
    """
    return [
        Question(
            id="dizziness_character",
            text="What does the dizziness feel like?",
            category="HPI",
            domain="dizziness",
            symptom="dizziness",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="character",
            clinical_dimension="character",
            priority=1,
            required=True,
            options=[
                Option(id="spinning_vertigo", label="Room or self is spinning (vertigo)"),
                Option(id="lightheaded", label="Feeling faint or lightheaded (presyncope)"),
                Option(id="unsteady", label="Feeling off-balance or unsteady while walking"),
                Option(id="floating", label="Vague floating, disoriented, or foggy feeling"),
            ],
        ),
        Question(
            id="dizziness_onset",
            text="When did the dizziness begin, and did it start suddenly?",
            category="HPI",
            domain="dizziness",
            symptom="dizziness",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="onset",
            clinical_dimension="onset",
            priority=2,
            required=True,
            options=[
                Option(id="sudden", label="Suddenly within seconds or minutes"),
                Option(id="gradual", label="Gradually over hours or days"),
                Option(id="waking_up", label="Started upon waking in the morning"),
            ],
        ),
        Question(
            id="dizziness_timing",
            text="Does the dizziness come in brief episodes, or is it constant throughout the day?",
            category="HPI",
            domain="dizziness",
            symptom="dizziness",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="timing",
            clinical_dimension="timing",
            priority=3,
            required=True,
            options=[
                Option(id="seconds", label="Brief bursts lasting seconds"),
                Option(id="minutes_hours", label="Episodes lasting minutes to hours"),
                Option(id="constant", label="Constant all day without stopping"),
            ],
        ),
        Question(
            id="dizziness_triggers",
            text="Does the dizziness happen when you stand up, roll over in bed, or move your head?",
            category="HPI",
            domain="dizziness",
            symptom="dizziness",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="triggers",
            clinical_dimension="triggers",
            priority=4,
            required=False,
            options=[
                Option(id="standing_up", label="When standing up from sitting or lying down"),
                Option(id="bed_head_turn", label="When rolling over in bed or tilting head"),
                Option(id="no_movement_trigger", label="Happens even when resting quietly"),
            ],
        ),
        Question(
            id="dizziness_severity",
            text="How severely is this dizziness affecting you?",
            category="HPI",
            domain="dizziness",
            symptom="dizziness",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="severity",
            clinical_dimension="severity",
            priority=5,
            required=True,
            options=[
                Option(id="mild", label="Mild — noticeable but able to walk and work"),
                Option(id="moderate", label="Moderate — unsteady, need support or wall to walk"),
                Option(id="severe", label="Severe — unable to stand, bedridden or vomiting"),
            ],
        ),
        Question(
            id="dizziness_ear_symptoms",
            text="Are you having any ringing in the ears (tinnitus), ear fullness, or decreased hearing?",
            category="Associated Symptoms",
            domain="dizziness",
            symptom="dizziness",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="ear_symptoms",
            clinical_dimension="associated_ear",
            priority=6,
            required=False,
            options=[
                Option(id="tinnitus", label="Ringing or buzzing in one or both ears"),
                Option(id="ear_fullness", label="Feeling of blockage or fullness in ear"),
                Option(id="hearing_loss", label="Decreased or muffled hearing"),
                Option(id="none", label="No ear symptoms"),
            ],
        ),
        Question(
            id="dizziness_associated",
            text="Have you had any fainting, chest pain, palpitations, or arm/leg weakness?",
            category="Associated Symptoms",
            domain="dizziness",
            symptom="dizziness",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="associated_symptoms",
            clinical_dimension="red_flag",
            priority=7,
            required=True,
            red_flag=True,
            options=[
                Option(id="fainting", label="Fainted or blacked out completely"),
                Option(id="chest_palpitations", label="Chest pain, pressure, or fluttering heartbeat"),
                Option(id="weakness_numbness", label="Arm/leg weakness, numbness, or slurred speech"),
                Option(id="nausea_only", label="Nausea or vomiting only"),
                Option(id="none", label="None of these"),
            ],
        ),
    ]
