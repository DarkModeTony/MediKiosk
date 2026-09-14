from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

class OCRResult(BaseModel):
    raw_text: str
    page_number: int
    confidence: Optional[float] = None
    bounding_boxes: Optional[List[Dict[str, Any]]] = None

class OCRProvider(ABC):
    @abstractmethod
    def process(self, file_path: str) -> List[OCRResult]:
        """
        Process a document and return OCR results per page.
        """
        pass
