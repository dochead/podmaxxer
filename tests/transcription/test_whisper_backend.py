from dataclasses import dataclass

import pytest

from podmaxxer.errors import TranscriptionError
from podmaxxer.transcription import whisper_backend


@dataclass
class FakeSegment:
    text: str


class FakeModel:
    def __init__(self, segments):
        self._segments = segments

    def transcribe(self, path):
        return self._segments, None


def test_transcribe_joins_segment_text(monkeypatch, tmp_path):
    audio = tmp_path / "episode.mp3"
    audio.write_bytes(b"fake-audio")

    fake_model = FakeModel([FakeSegment(" Hello "), FakeSegment("world. ")])
    monkeypatch.setattr(whisper_backend, "_get_model", lambda model_size: fake_model)

    result = whisper_backend.transcribe(audio, model_size="base")

    assert result == "Hello world."


def test_get_model_is_cached(monkeypatch):
    calls = []

    class DummyWhisperModel:
        def __init__(self, model_size, device, compute_type):
            calls.append(model_size)

    monkeypatch.setattr(whisper_backend, "WhisperModel", DummyWhisperModel)
    whisper_backend._MODEL_CACHE.clear()

    whisper_backend._get_model("base")
    whisper_backend._get_model("base")

    assert calls == ["base"]


def test_transcribe_wraps_model_failure(monkeypatch, tmp_path):
    audio = tmp_path / "episode.mp3"
    audio.write_bytes(b"fake-audio")

    def _raise_model_size(model_size):
        raise RuntimeError("model load failed")

    monkeypatch.setattr(whisper_backend, "_get_model", _raise_model_size)

    with pytest.raises(TranscriptionError):
        whisper_backend.transcribe(audio, model_size="base")
