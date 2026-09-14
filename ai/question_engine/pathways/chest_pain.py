from ai.question_engine.models import Question, InputType, Option

def get_chest_pain_pathway():
    return [
        Question(
            id="chest_pain_onset",
            text="When did the chest pain start?",
            category="HPI",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="onset",
            options=[
                Option(id="just_now", label="Just now / Suddenly"),
                Option(id="today", label="Earlier today"),
                Option(id="yesterday", label="Yesterday"),
                Option(id="days_ago", label="A few days ago")
            ]
        ),
        Question(
            id="chest_pain_character",
            text="What does the pain feel like?",
            category="HPI",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="character",
            options=[
                Option(id="heavy", label="Heavy / Pressure / Squeezing"),
                Option(id="sharp", label="Sharp / Stabbing"),
                Option(id="burning", label="Burning"),
                Option(id="aching", label="Aching / Dull")
            ]
        ),
        Question(
            id="chest_pain_radiation",
            text="Does the pain spread anywhere else, like your arm, neck, or jaw?",
            category="HPI",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="radiation",
            options=[
                Option(id="left_arm", label="Left arm"),
                Option(id="neck_jaw", label="Neck or Jaw"),
                Option(id="back", label="Back"),
                Option(id="no_radiation", label="No, it stays in my chest")
            ]
        ),
        Question(
            id="chest_pain_sob",
            text="Are you experiencing shortness of breath?",
            category="Associated Symptoms",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="shortness_of_breath",
            options=[
                Option(id="yes_severe", label="Yes, severely"),
                Option(id="yes_mild", label="Yes, a little bit"),
                Option(id="no", label="No")
            ]
        )
    ]
