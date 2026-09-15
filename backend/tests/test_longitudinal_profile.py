import pytest
from app.schemas.longitudinal_profile import LongitudinalProfileSchema, AnatomicalStatus, EyeDetail

USER_SAMPLE_PAYLOAD = {
  "schema_version": "1.0",

  "patient": {
    "patient_id": "patient_001",
    "name": "Raj Kumar",
    "date_of_birth": "1995-06-15",
    "age": 31,
    "gender": "male",
    "blood_group": "O+"
  },

  "medical_history": {
    "allergies": [
      {
        "allergen": "Penicillin",
        "reaction": "Skin rash",
        "severity": "moderate",
        "status": "active",
        "verified": True
      }
    ],

    "chronic_conditions": [
      {
        "condition": "Type 2 Diabetes",
        "status": "active",
        "diagnosed_date": "2022-03-10",
        "severity": "moderate",
        "verified": True
      }
    ],

    "previous_conditions": [
      {
        "condition": "Dengue fever",
        "status": "resolved",
        "year": 2020,
        "verified": True
      }
    ],

    "surgeries": [
      {
        "procedure": "Left knee surgery",
        "body_site": "left_knee",
        "date": "2023-05-20",
        "reason": "ACL injury",
        "outcome": "recovered",
        "verified": True
      }
    ],

    "hospitalizations": [
      {
        "reason": "Dengue fever",
        "date": "2020-08-12",
        "duration_days": 5,
        "outcome": "recovered"
      }
    ]
  },

  "medications": {
    "current": [
      {
        "name": "Metformin",
        "dose": "500 mg",
        "frequency": "twice_daily",
        "route": "oral",
        "reason": "Type 2 Diabetes",
        "start_date": "2022-03-10",
        "status": "active"
      }
    ],

    "previous": [
      {
        "name": "Paracetamol",
        "dose": "500 mg",
        "frequency": "as_needed",
        "reason": "Fever",
        "status": "discontinued"
      }
    ]
  },

  "anatomical_status": {

    "eyes": {
      "left": {
        "present": False,
        "status": "absent",
        "cause": "trauma",
        "date": "2018-04-12",
        "prosthetic": False,
        "verified": True
      },

      "right": {
        "present": True,
        "status": "present",
        "vision": "normal",
        "verified": False
      }
    },

    "arms": {
      "left": {
        "present": True,
        "status": "present"
      },

      "right": {
        "present": True,
        "status": "present"
      }
    },

    "legs": {
      "left": {
        "present": True,
        "status": "present",
        "prosthetic": False
      },

      "right": {
        "present": True,
        "status": "present",
        "prosthetic": False
      }
    },

    "hands": {
      "left": {
        "present": True,
        "status": "present"
      },

      "right": {
        "present": True,
        "status": "present"
      }
    },

    "feet": {
      "left": {
        "present": True,
        "status": "present"
      },

      "right": {
        "present": True,
        "status": "present"
      }
    },

    "other": []
  },

  "medical_devices": [
    {
      "type": "prosthetic",
      "name": None,
      "body_site": None,
      "status": "active",
      "since": None
    }
  ],

  "sensory_status": {
    "vision": {
      "left_eye": {
        "status": "absent",
        "visual_ability": "none"
      },
      "right_eye": {
        "status": "present",
        "visual_ability": "normal"
      }
    },

    "hearing": {
      "left_ear": {
        "status": "unknown"
      },
      "right_ear": {
        "status": "unknown"
      }
    },

    "speech": {
      "status": "normal"
    }
  },

  "functional_status": {
    "mobility": {
      "walking": "independent",
      "walking_aid": None,
      "wheelchair": False
    },

    "daily_activities": {
      "eating": "independent",
      "bathing": "independent",
      "dressing": "independent",
      "toileting": "independent"
    }
  },

  "family_history": [
    {
      "condition": "Diabetes",
      "relationship": "father",
      "status": "reported"
    }
  ],

  "social_history": {
    "smoking": {
      "status": "no",
      "verified": True
    },

    "alcohol": {
      "status": "occasional",
      "verified": False
    },

    "occupation": "Software Engineer",

    "living_situation": "With family"
  },

  "immunizations": [
    {
      "vaccine": "COVID-19",
      "doses": 2,
      "last_dose_date": "2023-01-15"
    }
  ],

  "vital_history": [
    {
      "date": "2026-08-20",
      "height_cm": 175,
      "weight_kg": 72,
      "blood_pressure": "128/82",
      "heart_rate": 76,
      "temperature_c": 36.7,
      "oxygen_saturation": 98
    }
  ],

  "mental_cognitive_status": {
    "cognitive_status": "normal",
    "known_conditions": [],
    "communication_needs": []
  },

  "reproductive_health": {
    "status": "unknown",
    "pregnancy_status": "not_applicable"
  },

  "current_symptoms": [],

  "red_flags": [],

  "previous_encounters": [
    {
      "encounter_id": "enc_001",
      "date": "2026-08-20",
      "chief_complaint": "Fever",
      "summary": "Patient presented with fever for two days.",
      "diagnosis": "Viral fever",
      "outcome": "Discharged"
    }
  ],

  "documents": [
    {
      "document_id": "doc_001",
      "type": "blood_test",
      "date": "2026-08-20",
      "summary": "Routine blood investigation"
    }
  ],

  "patient_preferences": {
    "preferred_language": "English",
    "communication_mode": "text",
    "accessibility_needs": []
  },

  "chatbot_memory": {
    "important_patient_statements": [
      {
        "statement": "I lost my left eye after an accident.",
        "date": "2026-09-15",
        "source": "patient",
        "verified": False
      }
    ],

    "recent_concerns": [],

    "pending_questions": []
  },

  "provenance": {
    "last_updated": "2026-09-15T10:30:00Z",
    "last_updated_by": "patient_statement",
    "profile_version": 1
  }
}

def test_pydantic_schema_validates_sample_payload():
    """Verify that the user's exact JSON payload validates without any errors."""
    profile = LongitudinalProfileSchema(**USER_SAMPLE_PAYLOAD)
    assert profile.schema_version == "1.0"
    assert profile.patient.name == "Raj Kumar"
    assert profile.medical_history.allergies[0].allergen == "Penicillin"
    assert profile.medical_history.allergies[0].verified is True
    assert profile.anatomical_status.eyes.left.status == "absent"
    assert profile.anatomical_status.eyes.left.present is False
    assert profile.anatomical_status.eyes.right.status == "present"
    assert profile.anatomical_status.eyes.right.present is True
    assert profile.medications.current[0].name == "Metformin"
    assert profile.social_history.occupation == "Software Engineer"
    assert profile.chatbot_memory.important_patient_statements[0].statement == "I lost my left eye after an accident."

def test_unknown_must_not_mean_no():
    """Verify that absent (present=False) is distinct from unknown (present=None)."""
    absent_eye = EyeDetail(present=False, status="absent")
    assert absent_eye.present is False
    assert absent_eye.status == "absent"

    unknown_eye = EyeDetail(present=None, status="unknown")
    assert unknown_eye.present is None
    assert unknown_eye.status == "unknown"

def test_api_longitudinal_endpoints(client=None):
    """Test full roundtrip via FastAPI test client."""
    from fastapi.testclient import TestClient
    from app.main import app
    test_client = TestClient(app)

    # 1. Register a test patient
    reg_res = test_client.post("/api/v1/patients/register", json={
        "demographic_data": {
            "name": "Ananya Roy",
            "gender": "female",
            "age": 28,
            "blood_group": "B+"
        },
        "consent": True
    })
    assert reg_res.status_code == 200
    patient_id = reg_res.json()["patient_id"]

    # 2. GET auto-generated default profile
    get_res = test_client.get(f"/api/v1/patients/{patient_id}/longitudinal-profile")
    assert get_res.status_code == 200
    profile = get_res.json()
    assert profile["schema_version"] == "1.0"
    assert profile["patient"]["name"] == "Ananya Roy"

    # 3. PUT user sample payload
    payload = dict(USER_SAMPLE_PAYLOAD)
    payload["patient"]["patient_id"] = patient_id
    payload["patient"]["name"] = "Ananya Roy"
    put_res = test_client.put(f"/api/v1/patients/{patient_id}/longitudinal-profile", json=payload)
    assert put_res.status_code == 200
    updated = put_res.json()
    assert updated["medical_history"]["allergies"][0]["allergen"] == "Penicillin"
    assert updated["provenance"]["profile_version"] == 2

    # 4. PATCH update an allergy
    patch_res = test_client.patch(f"/api/v1/patients/{patient_id}/longitudinal-profile", json={
        "medical_history": {
            "allergies": [
                {
                    "allergen": "Sulfa drugs",
                    "reaction": "Hives",
                    "severity": "severe",
                    "status": "active",
                    "verified": True
                }
            ]
        }
    })
    assert patch_res.status_code == 200
    patched = patch_res.json()
    assert patched["medical_history"]["allergies"][0]["allergen"] == "Sulfa drugs"
    assert patched["provenance"]["profile_version"] == 3

    # 5. POST an individual fact
    fact_res = test_client.post(f"/api/v1/patients/{patient_id}/facts", json={
        "category": "anatomy",
        "fact_type": "body_part_presence",
        "body_site": "left_eye",
        "laterality": "left",
        "value": {"present": False, "cause": "trauma"},
        "status": "absent",
        "source_type": "patient_statement",
        "verified": False
    })
    assert fact_res.status_code == 201
    fact_data = fact_res.json()
    assert fact_data["status"] == "absent"

    # 6. GET list of facts
    facts_list_res = test_client.get(f"/api/v1/patients/{patient_id}/facts?category=anatomy")
    assert facts_list_res.status_code == 200
    facts = facts_list_res.json()
    assert len(facts) >= 1
    assert facts[0]["body_site"] == "left_eye"
