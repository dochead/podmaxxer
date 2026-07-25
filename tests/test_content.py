import pytest

from podmaxxer.content import (
    ContentKind,
    detect_kind_from_content_type,
    detect_kind_from_suffix,
    hash_bytes,
    hash_text,
)
from podmaxxer.errors import UnsupportedContentError


def test_detect_kind_from_suffix_audio_video():
    assert detect_kind_from_suffix(".mp3") == ContentKind.AUDIO_VIDEO
    assert detect_kind_from_suffix(".MP4") == ContentKind.AUDIO_VIDEO


def test_detect_kind_from_suffix_text():
    assert detect_kind_from_suffix(".txt") == ContentKind.TEXT
    assert detect_kind_from_suffix(".html") == ContentKind.TEXT


def test_detect_kind_from_suffix_unknown_raises():
    with pytest.raises(UnsupportedContentError):
        detect_kind_from_suffix(".exe")


def test_detect_kind_from_content_type_audio_video():
    assert detect_kind_from_content_type("audio/mpeg") == ContentKind.AUDIO_VIDEO
    assert detect_kind_from_content_type("video/mp4; charset=binary") == ContentKind.AUDIO_VIDEO


def test_detect_kind_from_content_type_text():
    assert detect_kind_from_content_type("text/html; charset=utf-8") == ContentKind.TEXT
    assert detect_kind_from_content_type("text/plain") == ContentKind.TEXT


def test_detect_kind_from_content_type_unknown_raises():
    with pytest.raises(UnsupportedContentError):
        detect_kind_from_content_type("application/json")


def test_hash_bytes_is_deterministic():
    assert hash_bytes(b"hello") == hash_bytes(b"hello")
    assert hash_bytes(b"hello") != hash_bytes(b"world")


def test_hash_text_matches_hash_bytes_utf8():
    assert hash_text("hello") == hash_bytes("hello".encode("utf-8"))
