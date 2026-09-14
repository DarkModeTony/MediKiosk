from abc import ABC, abstractmethod
from typing import List
from .models import ExtractedEntities

class ExtractionProvider(ABC):
    @abstractmethod
    def extract(self, text: str, page_number: int) -> ExtractedEntities:
        """
        Extracts medical entities deterministically from text.
        """
        pass
