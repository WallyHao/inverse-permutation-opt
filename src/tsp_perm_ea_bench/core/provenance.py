"""Runtime and source provenance recorded with each experiment run."""

from __future__ import annotations

import hashlib
import platform
import subprocess
import sys
from pathlib import Path


def collect_provenance(repository_root: str | Path) -> dict[str, str | bool]:
    """Collect stable source identity and basic execution environment details."""

    root = Path(repository_root)
    commit = _git(root, "rev-parse", "HEAD")
    status = _git(root, "status", "--porcelain")
    tracked_files = _git(root, "ls-files", "-z")
    file_list_hash = hashlib.sha256(tracked_files.encode("utf-8")).hexdigest()
    source_hash = hashlib.sha256()
    for filename in filter(None, tracked_files.split("\0")):
        source_hash.update(filename.encode("utf-8"))
        source_hash.update(b"\0")
        try:
            source_hash.update((root / filename).read_bytes())
        except OSError:
            source_hash.update(b"<unreadable>")
    return {
        "code_commit": commit,
        "working_tree_dirty": bool(status),
        "tracked_file_list_sha256": file_list_hash,
        "source_snapshot_sha256": source_hash.hexdigest(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "thread_setting": "single-process-runner",
    }


def _git(root: Path, *arguments: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *arguments], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"
