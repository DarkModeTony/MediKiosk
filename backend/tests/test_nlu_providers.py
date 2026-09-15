"""
Tests for Clinical NLU Providers.

Covers:
- MockNLUProvider: keyword-based extraction
- GeminiNLUProvider: mocked API response parsing
- Factory: NLU_MODE switching
- Safety invariants: no diagnosis, no prescription, provenance required
"""
import os
import json
import pytest
from unittest.mock import patch, MagicMock

from ai.clinical_nlu.models import ExtractedFacts, CandidateFact, FactConfidence
from ai.clinical_nlu.mock_provider import MockNLUProvider
from ai.clinical_nlu.interface import NLUProvider


# ─── MockNLUProvider Tests ───

class TestMockNLUProvider:
    def setup_method(self):
        self.provider = MockNLUProvider()

    def test_implements_interface(self):
        """MockNLUProvider must implement NLUProvider interface."""
        assert isinstance(self.provider, NLUProvider)

    def test_empty_transcript_returns_empty_facts(self):
        result = self.provider.extract_candidate_facts("")
        assert len(result.facts) == 0

    def test_chief_complaint_extraction(self):
        """Should extract chief_complaint when question_id is chief_complaint_initial."""
        result = self.provider.extract_candidate_facts(
            "I have been having chest pain",
            question_id="chief_complaint_initial",
        )
        cc_facts = [f for f in result.facts if f.category == "chief_complaint"]
        assert len(cc_facts) >= 1
        assert "chest pain" in cc_facts[0].value.get("complaint", "").lower()

    def test_symptom_detection_hindi(self):
        """Should detect Hindi symptom keywords."""
        result = self.provider.extract_candidate_facts("मुझे बुखार है")
        symptom_facts = [f for f in result.facts if f.category == "symptom"]
        assert len(symptom_facts) >= 1
        assert "fever" in symptom_facts[0].value.get("name", "").lower()

    def test_onset_extraction(self):
        """Should extract onset timing."""
        result = self.provider.extract_candidate_facts("It started 3 days ago")
        onset_facts = [f for f in result.facts if f.category == "onset"]
        assert len(onset_facts) >= 1
        assert "3 days" in onset_facts[0].value.get("onset", "")

    def test_severity_extraction_severe(self):
        result = self.provider.extract_candidate_facts("The pain is very severe")
        sev_facts = [f for f in result.facts if f.category == "severity"]
        assert len(sev_facts) >= 1
        assert sev_facts[0].value.get("severity") == "severe"

    def test_severity_extraction_mild(self):
        result = self.provider.extract_candidate_facts("It is a mild cough")
        sev_facts = [f for f in result.facts if f.category == "severity"]
        assert len(sev_facts) >= 1
        assert sev_facts[0].value.get("severity") == "mild"

    def test_allergy_extraction(self):
        result = self.provider.extract_candidate_facts("I am allergic to penicillin")
        allergy_facts = [f for f in result.facts if f.category == "allergy"]
        assert len(allergy_facts) >= 1
        assert allergy_facts[0].value.get("allergen", "").lower() == "penicillin"
        assert allergy_facts[0].is_negation is False

    def test_chronic_condition_reported(self):
        result = self.provider.extract_candidate_facts("I have diabetes")
        cond_facts = [f for f in result.facts if f.category == "chronic_condition"]
        assert len(cond_facts) >= 1
        assert cond_facts[0].is_negation is False

    def test_chronic_condition_denied(self):
        result = self.provider.extract_candidate_facts("No, I don't have asthma")
        cond_facts = [f for f in result.facts if f.category == "chronic_condition"]
        assert len(cond_facts) >= 1
        assert cond_facts[0].is_negation is True

    def test_metadata_contains_provider_name(self):
        result = self.provider.extract_candidate_facts("test")
        assert result.metadata.get("provider") == "mock"

    def test_all_facts_have_source_text(self):
        """SAFETY: Every extracted fact must have source provenance."""
        result = self.provider.extract_candidate_facts(
            "I have fever and I am allergic to aspirin since yesterday"
        )
        for fact in result.facts:
            assert fact.source_text is not None
            assert len(fact.source_text.strip()) > 0

    def test_no_diagnosis_category(self):
        """SAFETY: NLU must never output a 'diagnosis' category."""
        result = self.provider.extract_candidate_facts(
            "I think I have malaria or dengue"
        )
        for fact in result.facts:
            assert fact.category != "diagnosis"

    def test_no_prescription_category(self):
        """SAFETY: NLU must never output a 'prescription' category."""
        result = self.provider.extract_candidate_facts(
            "I need some antibiotics, maybe amoxicillin"
        )
        for fact in result.facts:
            assert fact.category != "prescription"


# ─── GeminiNLUProvider Tests (Mocked API) ───

class TestGeminiNLUProvider:
    """Tests GeminiNLUProvider with mocked Gemini API responses."""

    def _make_mock_response(self, facts_data):
        """Create a mock Gemini API response object."""
        mock_response = MagicMock()
        mock_response.text = json.dumps({"facts": facts_data})
        return mock_response

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key-123", "GEMINI_MODEL": "gemini-3.6-flash"})
    @patch("ai.clinical_nlu.gemini_provider.genai")
    def test_successful_extraction(self, mock_genai):
        """Should parse a valid Gemini API response into ExtractedFacts."""
        from ai.clinical_nlu.gemini_provider import GeminiNLUProvider

        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_client.models.generate_content.return_value = self._make_mock_response([
            {
                "category": "symptom",
                "fact_type": "reported_symptom",
                "value": {"name": "chest pain", "location": "left side"},
                "source_text": "I have chest pain on my left side",
                "confidence": "HIGH",
                "confidence_score": 0.95,
                "is_negation": False,
            }
        ])

        provider = GeminiNLUProvider()
        result = provider.extract_candidate_facts("I have chest pain on my left side")
        assert len(result.facts) == 1
        assert result.facts[0].category == "symptom"
        assert result.facts[0].confidence == FactConfidence.HIGH
        assert result.metadata.get("provider") == "gemini"

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key-123"})
    @patch("ai.clinical_nlu.gemini_provider.genai")
    def test_empty_transcript_returns_empty(self, mock_genai):
        """Empty transcript should bypass API call and return empty facts."""
        from ai.clinical_nlu.gemini_provider import GeminiNLUProvider

        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client

        provider = GeminiNLUProvider()
        result = provider.extract_candidate_facts("")
        assert len(result.facts) == 0
        mock_client.models.generate_content.assert_not_called()

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key-123"})
    @patch("ai.clinical_nlu.gemini_provider.genai")
    def test_api_error_falls_back_to_mock(self, mock_genai):
        """API errors should gracefully fall back to MockNLUProvider."""
        from ai.clinical_nlu.gemini_provider import GeminiNLUProvider

        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_client.models.generate_content.side_effect = Exception("API quota exhausted")

        provider = GeminiNLUProvider()
        result = provider.extract_candidate_facts("I have fever", question_id="chief_complaint_initial")
        # Should fall back to mock — mock detects "fever"
        assert len(result.facts) > 0
        assert "fallback_from_error" in result.metadata

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key-123"})
    @patch("ai.clinical_nlu.gemini_provider.genai")
    def test_negation_parsing(self, mock_genai):
        """Should correctly parse is_negation from Gemini response."""
        from ai.clinical_nlu.gemini_provider import GeminiNLUProvider

        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_client.models.generate_content.return_value = self._make_mock_response([
            {
                "category": "allergy",
                "fact_type": "denied_allergy",
                "value": {"allergen": "penicillin"},
                "source_text": "No, I am not allergic to penicillin",
                "confidence": "HIGH",
                "confidence_score": 0.9,
                "is_negation": True,
            }
        ])

        provider = GeminiNLUProvider()
        result = provider.extract_candidate_facts("No, I am not allergic to penicillin")
        assert result.facts[0].is_negation is True
        assert result.facts[0].fact_type == "denied_allergy"


# ─── Factory Tests ───

class TestNLUFactory:
    """Tests for the get_nlu_provider factory function."""

    @patch.dict(os.environ, {"NLU_MODE": "mock"})
    def test_mock_mode_returns_mock_provider(self):
        from ai.clinical_nlu.service import get_nlu_provider
        provider = get_nlu_provider()
        assert isinstance(provider, MockNLUProvider)

    @patch.dict(os.environ, {}, clear=True)
    def test_default_mode_returns_mock_provider(self):
        """Default (no NLU_MODE set) should return MockNLUProvider."""
        from ai.clinical_nlu.service import get_nlu_provider
        # Remove NLU_MODE from env entirely
        os.environ.pop("NLU_MODE", None)
        provider = get_nlu_provider()
        assert isinstance(provider, MockNLUProvider)

    @patch.dict(os.environ, {"NLU_MODE": "gemini"})
    def test_gemini_mode_without_key_falls_back(self):
        """Missing GEMINI_API_KEY should fall back to MockNLUProvider."""
        os.environ.pop("GEMINI_API_KEY", None)
        from ai.clinical_nlu.service import get_nlu_provider
        provider = get_nlu_provider()
        # Should fall back to mock because GeminiNLUProvider requires API key
        assert isinstance(provider, MockNLUProvider)


# ─── ClinicalNLUService Adapter Tests ───

class TestClinicalNLUServiceAdapter:
    """Tests for the backward-compatible ClinicalNLUService adapter."""

    def test_extract_facts_returns_dict(self):
        """Legacy extract_facts method should return a dictionary."""
        from ai.clinical_nlu.service import ClinicalNLUService
        service = ClinicalNLUService(provider=MockNLUProvider())
        result = service.extract_facts("I have chest pain", "chief_complaint_initial")
        assert isinstance(result, dict)
        assert "chief_complaint" in result

    def test_extract_candidate_facts_returns_model(self):
        """New extract_candidate_facts should return ExtractedFacts model."""
        from ai.clinical_nlu.service import ClinicalNLUService
        service = ClinicalNLUService(provider=MockNLUProvider())
        result = service.extract_candidate_facts("I have fever")
        assert isinstance(result, ExtractedFacts)
