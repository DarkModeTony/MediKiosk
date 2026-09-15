import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from ai.asr.provider import MockASRProvider, SarvamASRProvider, get_asr_provider

client = TestClient(app)

def test_mock_asr_provider():
    provider = MockASRProvider()
    result = provider.transcribe(b"fake audio bytes", language_code="hi-IN")
    assert "transcript" in result
    assert result["transcript"] == "Mock transcribed text"
    assert result["detected_language"] == "en-IN"

def test_get_asr_provider_mock(monkeypatch):
    monkeypatch.setenv("ASR_MODE", "mock")
    provider = get_asr_provider()
    assert isinstance(provider, MockASRProvider)

def test_get_asr_provider_sarvam(monkeypatch):
    monkeypatch.setenv("ASR_MODE", "sarvam")
    monkeypatch.setenv("SARVAM_API_KEY", "test_key")
    provider = get_asr_provider()
    assert isinstance(provider, SarvamASRProvider)

def test_voice_transcribe_endpoint():
    with patch("backend.app.api.endpoints.voice.get_asr_provider") as mock_get_prov:
        mock_instance = MagicMock()
        mock_instance.transcribe.return_value = {
            "transcript": "Mujhe do din se bukhar hai",
            "detected_language": "hi-IN"
        }
        mock_get_prov.return_value = mock_instance

        # Also patch if imported directly in voice.py
        with patch("app.api.endpoints.voice.get_asr_provider", return_value=mock_instance):
            fake_audio = b"RIFF....WAVEfmt ...."
            response = client.post(
                "/api/v1/voice/transcribe",
                files={"audio": ("speech.wav", fake_audio, "audio/wav")},
                data={"language_code": "hi-IN"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["transcript"] == "Mujhe do din se bukhar hai"
            assert data["detected_language"] == "hi-IN"
