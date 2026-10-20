"""Client-side helpers for the signed generated-file URLs returned by the API."""
from pathlib import Path

from app.core import file_urls


def generated_file(root: Path, url: str) -> Path:
    """Verify the response signature and map the generated file onto the isolated test directory."""
    path, _, query = url.partition("?")
    assert path.startswith("/static/generated/"), path
    assert file_urls.verify(path, query), f"generated file URL is not signed: {url}"
    return root / path.rsplit("/", 1)[-1]


def bare(value):
    """Strip response signatures so two reads of the same record compare equal."""
    if isinstance(value, dict):
        return {key: bare(item) for key, item in value.items()}
    if isinstance(value, list):
        return [bare(item) for item in value]
    if isinstance(value, str) and value.startswith("/static/generated/"):
        return file_urls.split_signature(value)[0]
    return value
