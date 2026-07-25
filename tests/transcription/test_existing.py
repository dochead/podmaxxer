from podmaxxer.transcription.existing import find_sidecar_transcript


def test_returns_none_when_no_sidecar(tmp_path):
    media = tmp_path / "episode.mp3"
    media.write_bytes(b"audio")
    assert find_sidecar_transcript(media) is None


def test_finds_txt_sidecar(tmp_path):
    media = tmp_path / "episode.mp3"
    media.write_bytes(b"audio")
    (tmp_path / "episode.txt").write_text("  hello transcript  ", encoding="utf-8")
    assert find_sidecar_transcript(media) == "hello transcript"


def test_finds_and_cleans_vtt_sidecar(tmp_path):
    media = tmp_path / "episode.mp3"
    media.write_bytes(b"audio")
    (tmp_path / "episode.vtt").write_text(
        "WEBVTT\n\n1\n00:00:00.000 --> 00:00:02.000\nHello there.\n\n"
        "2\n00:00:02.000 --> 00:00:04.000\nWelcome back.\n",
        encoding="utf-8",
    )
    assert find_sidecar_transcript(media) == "Hello there. Welcome back."
