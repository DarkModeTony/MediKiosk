from ai.question_engine.models import Question, InputType, Option

def get_fever_pathway():
    return [
        Question(
            id="fever_onset",
            text="When did the fever start?",
            category="HPI",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="onset",
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
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="severity",
            options=[
                Option(id="mild", label="Mild"),
                Option(id="high", label="High"),
                Option(id="very_high", label="Very High (over 103F / 39.5C)"),
                Option(id="dont_know", label="I haven't measured it")
            ]
        ),
        Question(
            id="fever_chills",
            text="Are you experiencing chills or shivering?",
            category="Associated Symptoms",
            input_type=InputType.VOICE_OR_OPTIONS,
            clinical_field="chills",
            options=[
                Option(id="yes", label="Yes"),
                Option(id="no", label="No")
            ]
        )
    ]
