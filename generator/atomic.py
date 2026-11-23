"""Atomic directory and file replacement primitives.

Builds the full versioned fixture set (12 HTML pages + index.html + needles.json)
inside a staging directory on the same filesystem, runs strict validation, fsyncs
every file and directory, and atomically swaps the directory into place.

On Linux, uses renameat2(RENAME_EXCHANGE) so existing pages and the new build swap
in a single kernel syscall without any window where the target directory is missing.
"""

from __future__ import annotations

import ctypes
import errno
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Callable

AT_FDCWD = -100
RENAME_EXCHANGE = 2


def _fsync_path(path: Path) -> None:
    """Best-effort fsync for a file or directory."""
    flags = os.O_RDONLY
    if path.is_dir() and hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    try:
        fd = os.open(path, flags)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def _fsync_tree(root: Path) -> None:
    for dirpath, _dirnames, filenames in os.walk(root):
        dpath = Path(dirpath)
        for fname in filenames:
            _fsync_path(dpath / fname)
        _fsync_path(dpath)


def _renameat2_exchange(src: Path, dst: Path) -> bool:
    """Atomically exchange two directories on Linux via renameat2(RENAME_EXCHANGE).

    Returns True if exchange succeeded, or False if renameat2 is unavailable on this platform.
    """
    if not sys.platform.startswith("linux"):
        return False

    try:
        libc = ctypes.CDLL("libc.so.6", use_errno=True)
        renameat2 = libc.renameat2
    except (OSError, AttributeError):
        return False

    renameat2.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    renameat2.restype = ctypes.c_int

    res = renameat2(
        AT_FDCWD,
        os.fsencode(str(src)),
        AT_FDCWD,
        os.fsencode(str(dst)),
        RENAME_EXCHANGE,
    )
    if res == 0:
        return True

    err = ctypes.get_errno()
    if err in (errno.ENOSYS, errno.EINVAL, errno.EOPNOTSUPP):
        return False
    raise OSError(err, os.strerror(err), str(src), None, str(dst))


def atomic_swap_directory(
    target_dir: Path,
    build_fn: Callable[[Path], None],
    validate_fn: Callable[[Path], None] | None = None,
) -> None:
    """Atomically build and swap target_dir.

    If build_fn or validate_fn raises, target_dir is completely untouched and the
    staging directory is removed.
    """
    target_dir = target_dir.resolve()
    parent_dir = target_dir.parent
    parent_dir.mkdir(parents=True, exist_ok=True)

    staging_dir = Path(
        tempfile.mkdtemp(prefix=f".staging-{target_dir.name}-", dir=parent_dir)
    )
    swapped = False
    try:
        build_fn(staging_dir)
        if validate_fn is not None:
            validate_fn(staging_dir)

        # Ensure directories are world-readable like normal static assets (0755)
        os.chmod(staging_dir, 0o755)
        _fsync_tree(staging_dir)

        if not target_dir.exists():
            os.rename(staging_dir, target_dir)
            swapped = True
        elif _renameat2_exchange(staging_dir, target_dir):
            # Single-syscall atomic exchange succeeded: staging_dir now holds the old build.
            swapped = True
            shutil.rmtree(staging_dir, ignore_errors=True)
        else:
            # Non-Linux fallback with rollback protection.
            backup_dir = Path(
                tempfile.mkdtemp(prefix=f".backup-{target_dir.name}-", dir=parent_dir)
            )
            os.rmdir(backup_dir)
            os.rename(target_dir, backup_dir)
            try:
                os.rename(staging_dir, target_dir)
                swapped = True
            except BaseException:
                if not target_dir.exists() and backup_dir.exists():
                    os.rename(backup_dir, target_dir)
                raise
            finally:
                if swapped and backup_dir.exists():
                    shutil.rmtree(backup_dir, ignore_errors=True)

        _fsync_path(parent_dir)
    finally:
        if not swapped and staging_dir.exists():
            shutil.rmtree(staging_dir, ignore_errors=True)


def atomic_write_file(target_path: Path, content: str, encoding: str = "utf-8") -> None:
    """Atomically write a single file via temp file in same directory + os.replace."""
    target_path = target_path.resolve()
    parent_dir = target_path.parent
    parent_dir.mkdir(parents=True, exist_ok=True)

    fd, tmp_name = tempfile.mkstemp(
        prefix=f".tmp-{target_path.name}-", dir=parent_dir
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding=encoding) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp_path, 0o644)
        os.replace(tmp_path, target_path)
        _fsync_path(parent_dir)
    except BaseException:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise
