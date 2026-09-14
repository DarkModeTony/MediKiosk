from ai.question_engine.models import Question, InputType, Option

def get_abdominal_pain_pathway():
    return [
        Question(
            id="abd_pain_onset",
            text="When did the stomach pain begin?",
            category="HPI",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="onset",
            options=[
                Option(id="sudden", label="Suddenly"),
                Option(id="gradual", label="Gradually over time")
            ]
        ),
        Question(
            id="abd_pain_location",
            text="Where exactly is the pain?",
            category="HPI",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="location",
            options=[
                Option(id="upper_right", label="Upper Right"),
                Option(id="lower_right", label="Lower Right"),
                Option(id="diffuse", label="All over"),
                Option(id="upper_middle", label="Upper Middle")
            ]
        )
    ]
