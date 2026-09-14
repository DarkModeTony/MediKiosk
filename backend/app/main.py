from fastapi import FastAPI
from app.database import engine, Base
from app.api.endpoints import patients, kiosk, clinical, documents, summaries, encounters

app = FastAPI(
    title="MediPlatform API",
    description="AI-powered clinical intake platform",
    version="0.1.0",
)

app.include_router(patients.router, prefix="/api/v1/patients", tags=["Patients"])
app.include_router(kiosk.router, prefix="/api/v1/kiosk", tags=["Kiosk"])
app.include_router(clinical.router, prefix="/api/v1/clinical", tags=["Clinical"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(summaries.router, prefix="/api/v1/summaries", tags=["Summaries"])
app.include_router(encounters.router, prefix="/api/v1/encounters", tags=["Encounters"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
