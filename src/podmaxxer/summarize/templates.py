from __future__ import annotations

from pathlib import Path

from podmaxxer.content import hash_text

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent  # src/podmaxxer/
DEFAULT_TEMPLATE_PATH = _PACKAGE_ROOT / "templates" / "default.txt"


def load_template(path: Path | None) -> tuple[str, str]:
    template_path = Path(path) if path is not None else DEFAULT_TEMPLATE_PATH
    text = template_path.read_text(encoding="utf-8")
    return text, hash_text(text)
