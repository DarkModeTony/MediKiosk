from ai.question_engine.models import Question, InputType, Option

def get_chest_pain_pathway():
    """
    Comprehensive chest pain pathway (7 clinical questions):
    1. Onset: When did the pain begin (sudden vs gradual)
    2. Character: Heavy pressure, crushing, sharp, burning, dull ache
    3. Location: Substernal (center), left side, right side, diffuse
    4. Radiation: Left arm, neck, jaw, back, shoulder
    5. Severity: Mild, moderate, severe
    6. Shortness of Breath (Red Flag): Dyspnea, inability to finish sentences
    7. Autonomic / Associated (Red Flag): Cold sweating, presyncope, nausea
    """
    return [
        Question(
            id="chest_pain_onset",
            text="When did the chest pain start?",
            category="HPI",
            domain="chest_pain",
            symptom="chest pain",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="onset",
            clinical_dimension="onset",
            priority=1,
            required=True,
            options=[
                Option(id="just_now", label="Just now / Suddenly within minutes"),
                Option(id="today", label="Earlier today"),
                Option(id="yesterday", label="Yesterday"),
                Option(id="days_ago", label="A few days ago")
            ]
        ),
        Question(
            id="chest_pain_character",
            text="What does the pain feel like?",
            category="HPI",
            domain="chest_pain",
            symptom="chest pain",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="character",
            clinical_dimension="character",
            priority=2,
            required=True,
            options=[
                Option(id="heavy", label="Heavy pressure, tightness, or crushing"),
                Option(id="sharp", label="Sharp, stabbing, or piercing"),
                Option(id="burning", label="Burning like acid reflux or heartburn"),
                Option(id="aching", label="Dull constant ache"),
            ]
        ),
        Question(
            id="chest_pain_location",
            text="Where is the pain mostly centered?",
            category="HPI",
            domain="chest_pain",
            symptom="chest pain",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="location",
            clinical_dimension="location",
            priority=3,
            required=False,
            options=[
                Option(id="center_substernal", label="Center of chest (behind breastbone)"),
                Option(id="left_side", label="Left side of chest"),
                Option(id="right_side", label="Right side of chest"),
                Option(id="both_sides", label="Spread across the entire chest"),
            ]
        ),
        Question(
            id="chest_pain_radiation",
            text="Does the pain spread anywhere else, like your left arm, neck, or jaw?",
            category="HPI",
            domain="chest_pain",
            symptom="chest pain",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="radiation",
            clinical_dimension="radiation",
            priority=4,
            required=False,
            options=[
                Option(id="left_arm", label="Left arm or shoulder"),
                Option(id="neck_jaw", label="Neck or Jaw"),
                Option(id="back", label="Between the shoulder blades in the back"),
                Option(id="no_radiation", label="No, it stays strictly in my chest")
            ]
        ),
        Question(
            id="chest_pain_severity",
            text="How severe is the chest pain right now?",
            category="HPI",
            domain="chest_pain",
            symptom="chest pain",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="severity",
            clinical_dimension="severity",
            priority=5,
            required=True,
            options=[
                Option(id="mild", label="Mild discomfort"),
                Option(id="moderate", label="Moderate — quite uncomfortable"),
                Option(id="severe", label="Severe — intense, frightening pain"),
            ]
        ),
        Question(
            id="chest_pain_sob",
            text="Are you experiencing shortness of breath?",
            category="Associated Symptoms",
            domain="chest_pain",
            symptom="chest pain",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="shortness_of_breath",
            clinical_dimension="red_flag",
            priority=6,
            required=True,
            red_flag=True,
            options=[
                Option(id="yes_severe", label="Yes, severely short of breath"),
                Option(id="yes_mild", label="Yes, a little bit out of breath"),
                Option(id="no", label="No difficulty breathing")
            ]
        ),
        Question(
            id="chest_pain_sweating",
            text="Are you having cold sweating, lightheadedness, or nausea?",
            category="Associated Symptoms",
            domain="chest_pain",
            symptom="chest pain",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="diaphoresis",
            clinical_dimension="associated",
            priority=7,
            required=False,
            options=[
                Option(id="yes_sweating", label="Yes, drenching cold sweats or feeling faint"),
                Option(id="nausea_only", label="Feeling sick to stomach / nausea only"),
                Option(id="no", label="No sweating, dizziness, or nausea")
            ]
        ),
    ]
