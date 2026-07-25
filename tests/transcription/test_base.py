from pathlib import Path

from podmaxxer.content import Content, ContentKind
from podmaxxer.transcription import base as transcription_base


def test_text_content_returns_its_own_text():
    content = Content(kind=ContentKind.TEXT, source_uri="x", content_hash="h", text="already text")
    text, source = transcription_base.get_transcript(content)
    assert text == "already text"
    assert source == "existing"


def test_audio_content_uses_sidecar_when_present(monkeypatch, tmp_path):
    media = tmp_path / "episode.mp3"
    media.write_bytes(b"audio")
    content = Content(kind=ContentKind.AUDIO_VIDEO, source_uri="x", content_hash="h", path=media)

    monkeypatch.setattr(transcription_base, "find_sidecar_transcript", lambda path: "sidecar text")
    monkeypatch.setattr(transcription_base, "whisper_transcribe", lambda path: (_ for _ in ()).throw(AssertionError("should not be called")))

    text, source = transcription_base.get_transcript(content)
    assert text == "sidecar text"
    assert source == "existing"


def test_audio_content_falls_back_to_whisper(monkeypatch, tmp_path):
    media = tmp_path / "episode.mp3"
    media.write_bytes(b"audio")
    content = Content(kind=ContentKind.AUDIO_VIDEO, source_uri="x", content_hash="h", path=media)

    monkeypatch.setattr(transcription_base, "find_sidecar_transcript", lambda path: None)
    monkeypatch.setattr(transcription_base, "whisper_transcribe", lambda path: "whispered text")

    text, source = transcription_base.get_transcript(content)
    assert text == "whispered text"
    assert source == "whisper"
