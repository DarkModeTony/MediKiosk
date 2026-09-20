from ai.question_engine.models import Question, InputType, Option

def get_vomiting_pathway():
    """
    Comprehensive vomiting pathway (7 clinical questions):
    1. Frequency: Episodes today (1-2, 3-5, >5)
    2. Onset: When did the nausea/vomiting start
    3. Contents / Appearance: Undigested food, clear watery/bile, blood/coffee-grounds
    4. Oral Fluid Tolerance (Red flag for dehydration): Able to drink water vs vomiting everything
    5. Food history: Suspicion of food poisoning, outside food, illness in family
    6. Associated Diarrhea: Concurrent gastroenteritis symptoms
    7. Red Flags: Severe unremitting abdominal pain, high fever, hematemesis
    """
    return [
        Question(
            id="vomiting_frequency",
            text="How many times have you vomited today?",
            category="HPI",
            domain="vomiting",
            symptom="vomiting",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="frequency",
            clinical_dimension="severity",
            priority=1,
            required=True,
            options=[
                Option(id="once_twice", label="1 to 2 times"),
                Option(id="several", label="3 to 5 times"),
                Option(id="many", label="More than 5 times (frequent / uncontrollable)"),
            ]
        ),
        Question(
            id="vomiting_onset",
            text="When did the vomiting start?",
            category="HPI",
            domain="vomiting",
            symptom="vomiting",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="onset",
            clinical_dimension="onset",
            priority=2,
            required=True,
            options=[
                Option(id="today", label="Earlier today"),
                Option(id="yesterday", label="Yesterday"),
                Option(id="days_ago", label="A few days ago"),
            ]
        ),
        Question(
            id="vomiting_contents",
            text="What does the vomit look like?",
            category="HPI",
            domain="vomiting",
            symptom="vomiting",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="character",
            clinical_dimension="character",
            priority=3,
            required=False,
            options=[
                Option(id="food_particles", label="Undigested food and saliva"),
                Option(id="green_yellow_bile", label="Clear fluid or bitter greenish/yellow bile"),
                Option(id="coffee_ground_blood", label="Red blood or dark coffee-ground granules"),
            ]
        ),
        Question(
            id="vomiting_hydration",
            text="Are you able to keep water or fluids down without vomiting?",
            category="Associated Symptoms",
            domain="vomiting",
            symptom="vomiting",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="oral_intake",
            clinical_dimension="red_flag",
            priority=4,
            required=True,
            red_flag=True,
            options=[
                Option(id="yes_can_drink", label="Yes, can drink and retain water"),
                Option(id="vomiting_everything", label="No, vomiting immediately after drinking any water"),
                Option(id="excessive_thirst", label="Extreme thirst and dry tongue"),
            ]
        ),
        Question(
            id="vomiting_food_history",
            text="Did the symptoms begin after eating outside food, street food, or unusual meal?",
            category="HPI",
            domain="vomiting",
            symptom="vomiting",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="food_history",
            clinical_dimension="triggers",
            priority=5,
            required=False,
            options=[
                Option(id="outside_food", label="Yes, ate outside/street food within 24 hours"),
                Option(id="family_ill", label="Others who ate the same food are also sick"),
                Option(id="home_food", label="No, ate normal home-cooked food"),
            ]
        ),
        Question(
            id="vomiting_diarrhea",
            text="Are you also experiencing loose motions or watery diarrhea?",
            category="Associated Symptoms",
            domain="vomiting",
            symptom="vomiting",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="diarrhea",
            clinical_dimension="associated_gi",
            priority=6,
            required=False,
            options=[
                Option(id="frequent_loose_stools", label="Yes, frequent watery motions"),
                Option(id="mild_loose_stools", label="1-2 loose stools only"),
                Option(id="no_diarrhea", label="No loose motions at all"),
            ]
        ),
        Question(
            id="vomiting_associated",
            text="Do you have severe abdominal pain, high fever, or dizziness when standing?",
            category="Associated Symptoms",
            domain="vomiting",
            symptom="vomiting",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="associated_symptoms",
            clinical_dimension="red_flag",
            priority=7,
            required=True,
            red_flag=True,
            options=[
                Option(id="severe_pain", label="Severe unbearable stomach cramping"),
                Option(id="fever", label="High fever and shivering"),
                Option(id="postural_dizziness", label="Dizziness or fainting when standing up"),
                Option(id="none", label="None of these"),
            ]
        ),
    ]
