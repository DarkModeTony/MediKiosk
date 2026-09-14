import os
import mimetypes
from typing import List
from google import genai
from google.genai import types
from .interface import OCRProvider, OCRResult

class GeminiOCRProvider(OCRProvider):
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable is not set. GeminiOCRProvider requires this key.")
        
        try:
            self.client = genai.Client(api_key=self.api_key)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Gemini Client: {e}")
            
        self.model_name = "gemini-3.6-flash"
        
        self.prompt = (
            "Transcribe only the text that is visibly present in this document.\n\n"
            "Preserve wording, numbers, units, medication names, dates, and other visible text as accurately as possible.\n\n"
            "Do not summarize.\n"
            "Do not interpret.\n"
            "Do not diagnose.\n"
            "Do not infer missing information.\n"
            "Do not normalize medication names.\n"
            "Do not correct unclear handwriting.\n\n"
            "If text is genuinely unreadable, write [UNREADABLE].\n\n"
            "Return only the transcription."
        )

    def process(self, file_path: str) -> List[OCRResult]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "image/jpeg"
            
        if not mime_type.startswith("image/") and mime_type != "application/pdf":
            raise ValueError(f"Unsupported file type for Gemini OCR: {mime_type}")
            
        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()
        except Exception as e:
            raise IOError(f"Failed to read file: {e}")
            
        try:
            # Construct the Document Part
            image_part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[image_part, self.prompt],
                config=types.GenerateContentConfig(
                    temperature=0.0,
                )
            )
            
            extracted_text = response.text
            
            if not extracted_text or not extracted_text.strip():
                raise ValueError("Gemini returned an empty transcription.")
                
            return [
                OCRResult(
                    raw_text=extracted_text.strip(),
                    page_number=1,
                    confidence=None, # Gemini does not provide character-level OCR confidence
                    bounding_boxes=None
                )
            ]
        except ValueError as ve:
            # Raise value errors (empty text, unsupported type) directly
            raise ve
        except Exception as e:
            raise RuntimeError(f"Gemini API failure during OCR: {e}")
