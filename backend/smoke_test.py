import os
from dotenv import load_dotenv
load_dotenv()

from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, SessionLocal
from app.models.models import Encounter

# Force real mode with Gemini
os.environ["AI_MODE"] = "real"
os.environ["LLM_PROVIDER"] = "gemini"

client = TestClient(app)

def run_smoke_test():
    print("Starting Gemini Smoke Test...")
    
    # Check env
    if not os.environ.get("GEMINI_API_KEY"):
        print("FAILURE: GEMINI_API_KEY is missing from environment.")
        return
        
    print("GEMINI_API_KEY is present.")

    # Get a demo encounter from the DB
    db = SessionLocal()
    try:
        encounter = db.query(Encounter).first()
        if not encounter:
            print("FAILURE: No encounter found in the database. Please seed the database first.")
            return
            
        print(f"Using Encounter ID: {encounter.id}")
        
        print("Calling POST /api/v1/summaries/generate...")
        response = client.post("/api/v1/summaries/generate", json={"encounter_id": str(encounter.id)})
        
        if response.status_code != 200:
            print(f"FAILURE: HTTP {response.status_code}")
            print(f"Details: {response.text}")
            return
            
        data = response.json()
        summary_id = data.get('summary_id')
        print("SUCCESS: Summary generated.")
        print(f"Status: {data.get('status')}")
        print(f"Summary ID: {summary_id}")
        
        print("\nCalling GET /api/v1/summaries/encounters/{encounter_id}/summary...")
        get_response = client.get(f"/api/v1/summaries/encounters/{encounter.id}/summary")
        if get_response.status_code == 200:
            get_data = get_response.json()
            print("SUCCESS: Summary retrieved.")
            draft_content = get_data.get('original_draft', {})
            print(f"Provider: {draft_content.get('provider')}")
            print(f"Status: {get_data.get('status')}")
            
            # Print Red Flags to verify preservation
            sections = draft_content.get('structured_sections', [])
            red_flag_section = next((s for s in sections if s.get('title', '').lower() == 'red flags'), None)
            if red_flag_section:
                print("Red Flags PRESERVED.")
            else:
                print("Red Flags missing.")
        else:
            print("FAILURE: Could not retrieve summary.")
        
    finally:
        db.close()

if __name__ == "__main__":
    run_smoke_test()
