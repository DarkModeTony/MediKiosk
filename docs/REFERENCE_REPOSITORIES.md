# Reference Repositories

## A. PreConsult Chat
- **Purpose**: Conversational medical intake.
- **Learn**: Patient symptom collection, context handling, validation.
- **Informs**: Kiosk conversation state, symptom extraction.
- **Note**: Reference only. Do NOT copy its zero-persistence architecture.

## B. LangDoc
- **Purpose**: Anamnesis / history-taking workflow.
- **Learn**: Dynamic clinical questioning, question sequencing.
- **Informs**: Adaptive Question Engine.
- **Note**: Reference only.

## C. AI4Bharat IndicConformerASR
- **Purpose**: Indian-language speech recognition.
- **Learn/Use**: Hindi voice input, ASR processing.
- **Informs**: `ai/asr` module.
- **Note**: DIRECT integration behind an interface.

## D. PaddleOCR
- **Purpose**: Document OCR.
- **Learn/Use**: Prescriptions, lab reports, discharge summaries processing.
- **Informs**: `ai/ocr` module.
- **Note**: DIRECT integration behind an interface.

## E. Medplum
- **Purpose**: FHIR-first architecture.
- **Learn**: Healthcare resource modeling, API patterns.
- **Informs**: General API design and FHIR architecture.
- **Note**: Reference only. Do not import.

## F. fhir.resources
- **Purpose**: Python FHIR validation.
- **Learn/Use**: Patient, Encounter, Condition modeling.
- **Informs**: `fhir/` mapping layer.
- **Note**: DIRECT dependency candidate.

## G. Synthea
- **Purpose**: Synthetic data generation.
- **Learn/Use**: Generating realistic test patients/encounters.
- **Informs**: Testing and development environments.
- **Note**: Do not use in runtime.

## H. OpenMRS Core
- **Purpose**: EMR architecture.
- **Learn**: Patient/Encounter/Provider modeling.
- **Informs**: Database schemas.
- **Note**: Reference only.

## I. OpenMRS Patient Management
- **Purpose**: UI/UX for hospital workflows.
- **Learn**: Patient search, queues.
- **Informs**: Doctor dashboard frontend.
- **Note**: Reference only.

## J. UHIS LF Mobile
- **Purpose**: Field usability, offline concepts.
- **Learn**: Healthcare worker workflow.
- **Informs**: Kiosk usability.
- **Note**: Reference only. No Flutter.

## K. SMART on FHIR Starter Kit
- **Purpose**: React + FHIR architecture.
- **Learn**: Identity integration, SMART-on-FHIR.
- **Informs**: Future integration planning.
- **Note**: Reference only.

## L. Medical Triage System
- **Purpose**: Clinical triage rules.
- **Learn**: Deterministic clinical rules, human-in-the-loop.
- **Informs**: Red-flag engine (`ai/red_flags`).
- **Note**: REFERENCE FOR LOGIC ONLY. Beware of GPL license.
