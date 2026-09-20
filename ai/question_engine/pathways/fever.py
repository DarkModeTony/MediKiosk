from ai.question_engine.models import Question, InputType, Option

def get_fever_pathway():
    """
    Comprehensive fever pathway (7 clinical questions):
    1. Onset: When did the fever begin
    2. Severity: Temperature severity (mild, high, very high)
    3. Pattern & Timing: Continuous vs evening spikes vs alternating days
    4. Chills & Rigors: Shivering, rigors, drenching sweats
    5. Respiratory: Cough, sore throat, runny nose
    6. Abdominal & Urinary: Burning urination, stomach ache, loose motions
    7. Red Flags: Severe joint pain, skin rash, neck stiffness, extreme lethargy
    """
    return [
        Question(
            id="fever_onset",
            text="When did the fever start?",
            category="HPI",
            domain="fever",
            symptom="fever",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="onset",
            clinical_dimension="onset",
            priority=1,
            required=True,
            options=[
                Option(id="today", label="Today"),
                Option(id="yesterday", label="Yesterday"),
                Option(id="days_ago", label="A few days ago"),
                Option(id="weeks_ago", label="More than a week ago")
            ]
        ),
        Question(
            id="fever_severity",
            text="How high is the fever?",
            category="HPI",
            domain="fever",
            symptom="fever",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="severity",
            clinical_dimension="severity",
            priority=2,
            required=True,
            red_flag=True,
            options=[
                Option(id="mild", label="Mild (around 99-100°F)"),
                Option(id="high", label="High (101-103°F)"),
                Option(id="very_high", label="Very High (over 103°F / 39.5°C)"),
                Option(id="dont_know", label="I haven't measured it with a thermometer")
            ]
        ),
        Question(
            id="fever_pattern",
            text="Is the fever continuous throughout the day, or does it spike at certain times?",
            category="HPI",
            domain="fever",
            symptom="fever",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="timing",
            clinical_dimension="timing",
            priority=3,
            required=False,
            options=[
                Option(id="continuous", label="Continuous all day and night"),
                Option(id="evening_spikes", label="Spikes mostly in the evening or night"),
                Option(id="comes_and_goes", label="Breaks with medication and returns"),
            ]
        ),
        Question(
            id="fever_chills",
            text="Are you experiencing chills, shivering, or drenching sweats?",
            category="Associated Symptoms",
            domain="fever",
            symptom="fever",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="chills",
            clinical_dimension="associated_chills",
            priority=4,
            required=False,
            options=[
                Option(id="severe_rigors", label="Severe shivering / shaking (rigors)"),
                Option(id="mild_chills", label="Mild feeling cold or shivering"),
                Option(id="night_sweats", label="Heavy night sweating"),
                Option(id="no_chills", label="No chills or shivering"),
            ]
        ),
        Question(
            id="fever_respiratory",
            text="Do you have any cough, sore throat, or runny nose?",
            category="Associated Symptoms",
            domain="fever",
            symptom="fever",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="resp_symptoms",
            clinical_dimension="associated_resp",
            priority=5,
            required=False,
            options=[
                Option(id="cough", label="Cough with or without phlegm"),
                Option(id="sore_throat", label="Sore throat or pain swallowing"),
                Option(id="runny_nose", label="Runny nose / congestion"),
                Option(id="none", label="No cough or throat symptoms"),
            ]
        ),
        Question(
            id="fever_urinary_gi",
            text="Do you have burning when urinating, stomach pain, or loose motions?",
            category="Associated Symptoms",
            domain="fever",
            symptom="fever",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="urinary_gi",
            clinical_dimension="associated_gi_gu",
            priority=6,
            required=False,
            options=[
                Option(id="burning_urine", label="Burning or painful urination"),
                Option(id="loose_motions", label="Diarrhea or loose stools"),
                Option(id="stomach_cramps", label="Stomach ache or vomiting"),
                Option(id="none", label="No urinary or stomach symptoms"),
            ]
        ),
        Question(
            id="fever_associated",
            text="Do you have a rash, severe body ache, joint pain, or neck stiffness?",
            category="Associated Symptoms",
            domain="fever",
            symptom="fever",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="localizing_symptoms",
            clinical_dimension="red_flag",
            priority=7,
            required=True,
            red_flag=True,
            options=[
                Option(id="severe_joint_body", label="Severe bone or joint pain (break-bone pain)"),
                Option(id="skin_rash", label="Skin rash or red spots"),
                Option(id="neck_stiffness", label="Stiff neck or severe headache"),
                Option(id="none", label="No other symptoms"),
            ]
        ),
    ]
