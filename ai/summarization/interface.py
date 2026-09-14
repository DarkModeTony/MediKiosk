from abc import ABC, abstractmethod
from .models import ClinicalSummaryInput, ClinicalSummaryDraft

class SummaryProvider(ABC):
    @abstractmethod
    def generate(self, input_data: ClinicalSummaryInput) -> ClinicalSummaryDraft:
        """
        Generates an AI Draft summary deterministically based on structured input.
        """
        pass
