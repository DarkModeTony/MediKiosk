from ai.question_engine.models import Question, InputType, Option

def get_headache_pathway():
    return [
        Question(
            id="headache_onset",
            text="When did the headache begin?",
            category="HPI",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="onset",
            options=[
                Option(id="sudden", label="Suddenly (like a thunderclap)"),
                Option(id="gradual", label="Gradually over hours/days")
            ]
        )
    ]
