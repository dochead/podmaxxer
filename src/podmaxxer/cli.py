from __future__ import annotations

import os
import sys
from pathlib import Path

import click

from podmaxxer.config import get_state_db_path, uses_default_openai
from podmaxxer.errors import PodmaxxerError
from podmaxxer.pipeline import process
from podmaxxer.sources.local_file import LocalFileSource
from podmaxxer.sources.remote_url import UrlSource
from podmaxxer.state.db import connect


@click.group()
def cli() -> None:
    """Podmaxxer: download and summarize podcasts, articles, and videos."""


@cli.command("file")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--template", type=click.Path(exists=True, path_type=Path), default=None)
def file_command(path: Path, template: Path | None) -> None:
    _run(LocalFileSource(path=path), template)


@cli.command("url")
@click.argument("url")
@click.option("--template", type=click.Path(exists=True, path_type=Path), default=None)
def url_command(url: str, template: Path | None) -> None:
    _run(UrlSource(url=url), template)


def _run(source, template: Path | None) -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key and uses_default_openai():
        click.echo(
            "Error: OPENAI_API_KEY is not set (or set PODMAXXER_OPENAI_BASE_URL for a local model).",
            err=True,
        )
        sys.exit(1)

    conn = connect(get_state_db_path())
    try:
        summary = process(source, conn, api_key, template_path=template)
    except PodmaxxerError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    finally:
        conn.close()

    click.echo(summary)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
