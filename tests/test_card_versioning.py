"""Cache busting of the bundled Lovelace cards.

The card URL carried the manifest version, so a changed bundle under an
unchanged version kept the old URL and browsers served the cached JS. The
version is now derived from the file content. Stale `*.js.gz` siblings
(left by older installs) are removed: aiohttp serves the neighbouring .gz
to gzip-capable clients, so an old .gz shadowed a new .js.
"""

from __future__ import annotations

import os

from custom_components.librus_apix import _card_versions


def _write(path, data: str, mtime: float | None = None) -> None:
    path.write_text(data)
    if mtime is not None:
        os.utime(path, (mtime, mtime))


def test_version_follows_file_content(tmp_path):
    _write(tmp_path / "a.js", "one")
    first = _card_versions(tmp_path)["a.js"]
    _write(tmp_path / "a.js", "two")
    second = _card_versions(tmp_path)["a.js"]

    assert first != second
    assert len(first) == 10


def test_same_content_same_version(tmp_path):
    _write(tmp_path / "a.js", "same")
    _write(tmp_path / "b.js", "same")
    versions = _card_versions(tmp_path)
    assert versions["a.js"] == versions["b.js"]


def test_stale_gz_is_removed_fresh_kept(tmp_path):
    _write(tmp_path / "old.js", "new bundle", mtime=2_000_000)
    _write(tmp_path / "old.js.gz", "may bundle", mtime=1_000_000)
    _write(tmp_path / "fresh.js", "bundle", mtime=1_000_000)
    _write(tmp_path / "fresh.js.gz", "bundle gz", mtime=2_000_000)
    _write(tmp_path / "orphan.js.gz", "no source")

    _card_versions(tmp_path)

    assert not (tmp_path / "old.js.gz").exists()
    assert (tmp_path / "fresh.js.gz").exists()
    assert not (tmp_path / "orphan.js.gz").exists()


def test_missing_dir_gives_no_versions(tmp_path):
    assert _card_versions(tmp_path / "nope") == {}
