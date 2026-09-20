from ai.question_engine.models import Question, InputType, Option

def get_cough_pathway():
    """
    Comprehensive cough pathway (7 clinical questions):
    1. Duration / Onset: How long the cough has been present
    2. Character: Dry vs wet / productive
    3. Phlegm Color & Nature: Clear, yellow/green, rusty, blood-streaked
    4. Timing: Night-time, morning, post-nasal, continuous
    5. Triggers: Cold air, lying flat, allergens, exertion
    6. Associated Constitutional: Fever, chills, weight loss, night sweats
    7. Red Flags: Hemoptysis (blood in cough), shortness of breath, chest pain
    """
    return [
        Question(
            id="cough_duration",
            text="How long have you had this cough?",
            category="HPI",
            domain="cough",
            symptom="cough",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="onset",
            clinical_dimension="onset",
            priority=1,
            required=True,
            options=[
                Option(id="few_days", label="A few days"),
                Option(id="weeks", label="1 to 2 weeks"),
                Option(id="more_than_month", label="More than 3 to 4 weeks"),
            ]
        ),
        Question(
            id="cough_type",
            text="Is the cough dry, or are you bringing up phlegm or mucus?",
            category="HPI",
            domain="cough",
            symptom="cough",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="cough_type",
            clinical_dimension="character",
            priority=2,
            required=True,
            options=[
                Option(id="dry", label="Dry hacking cough (no phlegm)"),
                Option(id="productive_clear", label="Wet with clear or white phlegm"),
                Option(id="productive_yellow_green", label="Wet with thick yellow or green phlegm"),
            ]
        ),
        Question(
            id="cough_phlegm_color",
            text="If you have phlegm, what does it look like?",
            category="HPI",
            domain="cough",
            symptom="cough",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="phlegm_color",
            clinical_dimension="phlegm_nature",
            priority=3,
            required=False,
            options=[
                Option(id="clear_white", label="Clear or whitish"),
                Option(id="yellow_green", label="Thick yellowish or greenish"),
                Option(id="blood_streaked", label="Reddish or blood-tinged"),
                Option(id="no_phlegm", label="No phlegm at all (completely dry)"),
            ]
        ),
        Question(
            id="cough_timing",
            text="When is your cough at its worst?",
            category="HPI",
            domain="cough",
            symptom="cough",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="timing",
            clinical_dimension="timing",
            priority=4,
            required=False,
            options=[
                Option(id="night_lying", label="At night or when lying flat in bed"),
                Option(id="morning", label="First thing upon waking in the morning"),
                Option(id="exertion", label="During or after walking/exercise"),
                Option(id="constant", label="All throughout the day and night"),
            ]
        ),
        Question(
            id="cough_triggers",
            text="Does anything specific trigger the cough, such as dust, cold drinks, or lying down?",
            category="HPI",
            domain="cough",
            symptom="cough",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="triggers",
            clinical_dimension="triggers",
            priority=5,
            required=False,
            options=[
                Option(id="cold_dust", label="Cold air, cold food, or dust"),
                Option(id="lying_down", label="Lying down flat on back"),
                Option(id="talking_eating", label="Eating, swallowing, or talking"),
                Option(id="no_trigger", label="No specific trigger identified"),
            ]
        ),
        Question(
            id="cough_fever_sweats",
            text="Are you having any fever, chills, or night sweats along with the cough?",
            category="Associated Symptoms",
            domain="cough",
            symptom="cough",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="fever_sweats",
            clinical_dimension="associated_fever",
            priority=6,
            required=False,
            options=[
                Option(id="high_fever", label="High fever and shivering"),
                Option(id="mild_fever", label="Mild low-grade fever"),
                Option(id="night_sweats", label="Soaking night sweats or unexplained weight loss"),
                Option(id="no_fever", label="No fever or sweats"),
            ]
        ),
        Question(
            id="cough_associated",
            text="Do you have shortness of breath, wheezing, or blood in your cough?",
            category="Associated Symptoms",
            domain="cough",
            symptom="cough",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="associated_symptoms",
            clinical_dimension="red_flag",
            priority=7,
            required=True,
            red_flag=True,
            options=[
                Option(id="shortness_of_breath", label="Shortness of breath or gasping for air"),
                Option(id="wheezing", label="Whistling sound when breathing (wheezing)"),
                Option(id="blood_in_sputum", label="Coughing up fresh blood or clots"),
                Option(id="chest_pain", label="Sharp chest pain when taking a deep breath"),
                Option(id="none", label="None of these"),
            ]
        ),
    ]
