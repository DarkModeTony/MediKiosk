import os
import pytest
from unittest.mock import MagicMock, patch
from ai.ocr.gemini_provider import GeminiOCRProvider
from ai.ocr.interface import OCRProvider, OCRResult
from ai.ocr.service import get_ocr_provider

# Test cases for GeminiOCRProvider

@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake_key")

@pytest.fixture
def mock_genai_client():
    with patch("ai.ocr.gemini_provider.genai.Client") as mock_client:
        yield mock_client

def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY environment variable is not set"):
        GeminiOCRProvider()

def test_successful_ocr(mock_env, mock_genai_client, tmp_path):
    # Setup mock file
    test_file = tmp_path / "test_doc.jpg"
    test_file.write_bytes(b"fake image data")
    
    # Setup mock response
    mock_instance = mock_genai_client.return_value
    mock_response = MagicMock()
    mock_response.text = "Patient: Raj Kumar\nDiagnosis: Hypertension"
    mock_instance.models.generate_content.return_value = mock_response
    
    provider = GeminiOCRProvider()
    results = provider.process(str(test_file))
    
    assert len(results) == 1
    assert isinstance(results[0], OCRResult)
    assert results[0].raw_text == "Patient: Raj Kumar\nDiagnosis: Hypertension"
    assert results[0].page_number == 1
    assert results[0].confidence is None
    assert results[0].bounding_boxes is None
    
    # Verify the prompt was passed correctly
    call_args = mock_instance.models.generate_content.call_args[1]
    assert call_args['model'] == "gemini-3.6-flash"
    assert "Transcribe only the text" in call_args['contents'][1]

def test_empty_response(mock_env, mock_genai_client, tmp_path):
    test_file = tmp_path / "test_doc.jpg"
    test_file.write_bytes(b"fake image data")
    
    mock_instance = mock_genai_client.return_value
    mock_response = MagicMock()
    mock_response.text = "   \n"
    mock_instance.models.generate_content.return_value = mock_response
    
    provider = GeminiOCRProvider()
    with pytest.raises(ValueError, match="Gemini returned an empty transcription"):
        provider.process(str(test_file))

def test_missing_file(mock_env):
    provider = GeminiOCRProvider()
    with pytest.raises(FileNotFoundError, match="File not found"):
        provider.process("nonexistent.jpg")

def test_unsupported_file_type(mock_env, tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello")
    
    provider = GeminiOCRProvider()
    with pytest.raises(ValueError, match="Unsupported file type for Gemini OCR"):
        provider.process(str(test_file))

def test_api_failure(mock_env, mock_genai_client, tmp_path):
    test_file = tmp_path / "test_doc.jpg"
    test_file.write_bytes(b"fake image data")
    
    mock_instance = mock_genai_client.return_value
    mock_instance.models.generate_content.side_effect = Exception("503 Service Unavailable")
    
    provider = GeminiOCRProvider()
    with pytest.raises(RuntimeError, match="Gemini API failure during OCR"):
        provider.process(str(test_file))

def test_provider_factory(monkeypatch):
    monkeypatch.setenv("OCR_MODE", "real")
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    provider = get_ocr_provider()
    assert isinstance(provider, GeminiOCRProvider)
    
    monkeypatch.setenv("OCR_MODE", "mock")
    provider = get_ocr_provider()
    assert type(provider).__name__ == "MockOCRProvider"
    
    monkeypatch.setenv("OCR_MODE", "invalid_mode")
    with pytest.raises(ValueError, match="Unknown OCR_MODE configuration"):
        get_ocr_provider()
