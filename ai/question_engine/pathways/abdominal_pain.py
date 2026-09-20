from ai.question_engine.models import Question, InputType, Option

def get_abdominal_pain_pathway():
    """
    Comprehensive abdominal pain pathway (7 clinical questions):
    1. Onset: Sudden vs gradual
    2. Location: Upper right, lower right, upper middle (epigastric), diffuse
    3. Character: Cramping, burning/acidity, sharp stabbing, dull ache
    4. Severity: Mild, moderate, severe
    5. Relation to food: Worsens with food, improves with food, unaffected
    6. Bowel / GI habits: Nausea, vomiting, diarrhea, constipation
    7. Red flags: Blood in vomit/stool, high fever, abdominal rigidity
    """
    return [
        Question(
            id="abd_pain_onset",
            text="When did the stomach pain begin?",
            category="HPI",
            domain="abdominal_pain",
            symptom="abdominal pain",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="onset",
            clinical_dimension="onset",
            priority=1,
            required=True,
            options=[
                Option(id="sudden", label="Suddenly within a few minutes"),
                Option(id="gradual", label="Gradually over hours or days"),
                Option(id="recurrent", label="Has been recurring on and off for weeks"),
            ]
        ),
        Question(
            id="abd_pain_location",
            text="Where exactly is the pain located?",
            category="HPI",
            domain="abdominal_pain",
            symptom="abdominal pain",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="location",
            clinical_dimension="location",
            priority=2,
            required=True,
            options=[
                Option(id="upper_middle", label="Upper middle / below ribs (acidity area)"),
                Option(id="lower_right", label="Lower right side (near appendix)"),
                Option(id="upper_right", label="Upper right side (near liver/gallbladder)"),
                Option(id="lower_abdomen", label="Lower abdomen (pelvis/bladder area)"),
                Option(id="diffuse", label="All over the entire abdomen"),
            ]
        ),
        Question(
            id="abd_pain_character",
            text="What does the stomach pain feel like?",
            category="HPI",
            domain="abdominal_pain",
            symptom="abdominal pain",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="character",
            clinical_dimension="character",
            priority=3,
            required=False,
            options=[
                Option(id="cramping", label="Colicky or cramping waves"),
                Option(id="burning", label="Burning or churning acidity"),
                Option(id="sharp", label="Constant sharp or stabbing pain"),
                Option(id="dull_ache", label="Heavy dull aching pressure"),
            ]
        ),
        Question(
            id="abd_pain_severity",
            text="How severe is the pain right now?",
            category="HPI",
            domain="abdominal_pain",
            symptom="abdominal pain",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="severity",
            clinical_dimension="severity",
            priority=4,
            required=True,
            options=[
                Option(id="mild", label="Mild — bearable, can go about day"),
                Option(id="moderate", label="Moderate — painful, holding stomach"),
                Option(id="severe", label="Severe — doubled over, unbearable agony"),
            ]
        ),
        Question(
            id="abd_pain_food_relation",
            text="Does eating food or drinking make the stomach pain better or worse?",
            category="HPI",
            domain="abdominal_pain",
            symptom="abdominal pain",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="food_relation",
            clinical_dimension="triggers",
            priority=5,
            required=False,
            options=[
                Option(id="worse_after_eating", label="Pain gets worse right after eating"),
                Option(id="better_after_eating", label="Pain feels better when eating food"),
                Option(id="spicy_triggers", label="Worse only after spicy or oily food"),
                Option(id="no_relation", label="No difference with food or eating"),
            ]
        ),
        Question(
            id="abd_pain_bowel",
            text="Are you having any vomiting, loose stools (diarrhea), or constipation?",
            category="Associated Symptoms",
            domain="abdominal_pain",
            symptom="abdominal pain",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="bowel_symptoms",
            clinical_dimension="associated_gi",
            priority=6,
            required=False,
            options=[
                Option(id="vomiting", label="Vomiting or nausea"),
                Option(id="diarrhea", label="Watery or loose stools (diarrhea)"),
                Option(id="constipation", label="Severe constipation (not passed stool for days)"),
                Option(id="normal_bowel", label="Normal bowel movements"),
            ]
        ),
        Question(
            id="abd_pain_associated",
            text="Do you have high fever, blood in stool, or black-colored stools?",
            category="Associated Symptoms",
            domain="abdominal_pain",
            symptom="abdominal pain",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="associated_symptoms",
            clinical_dimension="red_flag",
            priority=7,
            required=True,
            red_flag=True,
            options=[
                Option(id="fever", label="High fever or chills"),
                Option(id="blood_stool", label="Red blood in stool or dark black tarry stool"),
                Option(id="severe_distension", label="Severe abdominal swelling and hardness"),
                Option(id="none", label="None of these warning signs"),
            ]
        ),
    ]
