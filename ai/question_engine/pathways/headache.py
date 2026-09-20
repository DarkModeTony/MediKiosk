from ai.question_engine.models import Question, InputType, Option

def get_headache_pathway():
    """
    Comprehensive headache pathway (7 clinical questions):
    1. Onset: When and how did it start (sudden thunderclap vs gradual)
    2. Location: Unilateral, bilateral, forehead, occipital
    3. Severity: Mild, moderate, severe
    4. Character: Throbbing, tight band, sharp, pressure
    5. Timing & Pattern: Constant vs throbbing waves vs episodic
    6. Triggers & Aggravating: Bright light, bending forward, stress, exertion
    7. Associated Red Flags: Nausea, photophobia, neck stiffness, visual aura
    """
    return [
        Question(
            id="headache_onset",
            text="When did your headache start?",
            category="HPI",
            domain="headache",
            symptom="headache",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="onset",
            clinical_dimension="onset",
            priority=1,
            required=True,
            red_flag=True,
            options=[
                Option(id="sudden", label="Suddenly (like a thunderclap / split-second)"),
                Option(id="gradual", label="Gradually over hours or days"),
                Option(id="waking_up", label="Present when waking up in the morning"),
            ]
        ),
        Question(
            id="headache_location",
            text="Where do you feel the headache?",
            category="HPI",
            domain="headache",
            symptom="headache",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="location",
            clinical_dimension="location",
            priority=2,
            required=False,
            options=[
                Option(id="one_side", label="One side of head (left or right)"),
                Option(id="forehead", label="Forehead and around eyes"),
                Option(id="back_of_head", label="Back of head and upper neck"),
                Option(id="all_over", label="All over the entire head"),
            ]
        ),
        Question(
            id="headache_severity",
            text="How severe is the pain?",
            category="HPI",
            domain="headache",
            symptom="headache",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="severity",
            clinical_dimension="severity",
            priority=3,
            required=True,
            options=[
                Option(id="mild", label="Mild — noticeable but able to work"),
                Option(id="moderate", label="Moderate — hard to concentrate"),
                Option(id="severe", label="Severe / Worst headache of life"),
            ]
        ),
        Question(
            id="headache_character",
            text="What does the pain feel like?",
            category="HPI",
            domain="headache",
            symptom="headache",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="character",
            clinical_dimension="character",
            priority=4,
            required=False,
            options=[
                Option(id="throbbing", label="Throbbing or pulsing (like a heartbeat)"),
                Option(id="tight_band", label="Dull tightness like a tight band around head"),
                Option(id="sharp", label="Sharp, stabbing, or electric-like"),
                Option(id="heavy_pressure", label="Heavy pressure behind eyes or forehead"),
            ]
        ),
        Question(
            id="headache_timing",
            text="Is the headache constant, or does it come and go in throbbing waves?",
            category="HPI",
            domain="headache",
            symptom="headache",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="timing",
            clinical_dimension="timing",
            priority=5,
            required=False,
            options=[
                Option(id="constant_unbroken", label="Continuous and steady without break"),
                Option(id="pulsing_waves", label="Pulsing waves that worsen with activity"),
                Option(id="episodic_attacks", label="Distinct attacks lasting a few hours"),
            ]
        ),
        Question(
            id="headache_triggers",
            text="Does anything trigger or worsen the pain, like bright light, sound, or bending over?",
            category="HPI",
            domain="headache",
            symptom="headache",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="triggers",
            clinical_dimension="triggers",
            priority=6,
            required=False,
            options=[
                Option(id="light_sound", label="Bright light or loud noises"),
                Option(id="cough_bend", label="Coughing, straining, or bending forward"),
                Option(id="stress_lack_sleep", label="Stress or lack of sleep"),
                Option(id="none_spontaneous", label="No clear trigger"),
            ]
        ),
        Question(
            id="headache_associated",
            text="Are you experiencing any other symptoms, like nausea, sensitivity to light, or neck stiffness?",
            category="Associated Symptoms",
            domain="headache",
            symptom="headache",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="associated_symptoms",
            clinical_dimension="red_flag",
            priority=7,
            required=True,
            red_flag=True,
            options=[
                Option(id="nausea_vomiting", label="Nausea or vomiting"),
                Option(id="light_sound_sensitivity", label="Sensitivity to light or sound"),
                Option(id="neck_stiffness", label="Stiff neck or difficulty bending chin to chest"),
                Option(id="visual_aura", label="Visual changes (blurriness, flashing lights, blind spots)"),
                Option(id="none", label="No other symptoms"),
            ]
        ),
    ]
