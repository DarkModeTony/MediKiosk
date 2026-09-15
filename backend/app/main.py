import sys
from pathlib import Path

# Ensure MediKiosk root is in sys.path for ai package imports
_root_dir = str(Path(__file__).resolve().parent.parent.parent)
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.api.endpoints import (
    patients, kiosk, clinical, documents, summaries,
    encounters, longitudinal, voice, prescriptions,
    auth, assessments, investigations
)

app = FastAPI(
    title="MediPlatform API",
    description="AI-powered clinical intake platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(patients.router, prefix="/api/v1/patients", tags=["Patients"])
app.include_router(longitudinal.router, prefix="/api/v1/patients", tags=["Longitudinal Profile"])
app.include_router(kiosk.router, prefix="/api/v1/kiosk", tags=["Kiosk"])
app.include_router(clinical.router, prefix="/api/v1/clinical", tags=["Clinical"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(summaries.router, prefix="/api/v1/summaries", tags=["Summaries"])
app.include_router(encounters.router, prefix="/api/v1/encounters", tags=["Encounters"])
app.include_router(assessments.router, prefix="/api/v1", tags=["Clinical Assessments"])
app.include_router(investigations.router, prefix="/api/v1", tags=["Investigations"])
app.include_router(voice.router, prefix="/api/v1/voice", tags=["Voice / ASR"])
app.include_router(prescriptions.router, prefix="/api/v1", tags=["Prescriptions"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
