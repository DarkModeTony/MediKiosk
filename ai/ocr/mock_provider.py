import time
from typing import List
from .interface import OCRProvider, OCRResult

class MockOCRProvider(OCRProvider):
    def process(self, file_path: str) -> List[OCRResult]:
        # Simulate processing time
        time.sleep(1)
        
        lower_path = file_path.lower()
        
        file_content = ""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read().lower()
        except:
            try:
                with open(file_path, "rb") as f:
                    file_content = f.read().decode("utf-8").lower()
            except:
                pass
        
        if "prescription" in lower_path or "amlodipine" in file_content:
            text = """Patient: Raj Kumar
Date: 12/08/2026

Diagnosis:
Hypertension

Medicines:
Amlodipine 5 mg once daily

Investigation:
Blood Pressure: 150/95 mmHg"""
        elif "lab" in lower_path or "report" in lower_path:
            text = """Haemoglobin: 10.2 g/dL
Reference Range: 12-16 g/dL

WBC: 7,200 /uL
Reference Range: 4,000-11,000 /uL"""
        else:
            text = "Mock generic document text. No specific medical entities."

        return [
            OCRResult(
                raw_text=text,
                page_number=1,
                confidence=0.98
            )
        ]
