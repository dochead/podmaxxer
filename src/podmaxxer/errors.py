class PodmaxxerError(Exception):
    """Base class for all podmaxxer-specific errors."""


class UnsupportedContentError(PodmaxxerError):
    """Raised when the kind of content at a source cannot be determined or handled."""


class FetchError(PodmaxxerError):
    """Raised when downloading or reading a source fails."""


class TranscriptionError(PodmaxxerError):
    """Raised when obtaining a transcript (existing or via Whisper) fails."""


class SummarizationError(PodmaxxerError):
    """Raised when calling the summarization backend fails."""
