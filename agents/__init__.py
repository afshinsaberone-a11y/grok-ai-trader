"""ForexAI local missions + OpenAI Agents SDK compatibility package.

The repository historically used ``agents/`` for its own mission modules while
``openai-agents`` also installs a top-level package named ``agents``. A normal
local ``__init__.py`` therefore shadows the SDK and breaks imports such as
``from agents import Agent``.

This shim keeps local mission modules importable as ``agents.<module>`` while
executing the installed OpenAI Agents SDK package in this same namespace. The
SDK package directory is appended to ``__path__`` so its relative imports remain
resolvable without renaming the established mission files.
"""
from __future__ import annotations

import sys
from importlib.machinery import PathFinder
from pathlib import Path

_LOCAL_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _LOCAL_DIR.parent.resolve()
_THIS_FILE = Path(__file__).resolve()


def _find_external_agents_spec():
    """Find the installed OpenAI Agents SDK, excluding this repository path."""
    for entry in sys.path:
        base = Path(entry or ".").resolve()
        if base == _REPO_ROOT or base == _LOCAL_DIR:
            continue
        try:
            spec = PathFinder.find_spec("agents", [str(base)])
        except (ImportError, AttributeError, OSError):
            continue
        if spec is None or not spec.origin:
            continue
        try:
            origin = Path(spec.origin).resolve()
        except OSError:
            continue
        if origin != _THIS_FILE and spec.submodule_search_locations:
            return spec
    return None


_sdk_spec = _find_external_agents_spec()
if _sdk_spec is None:
    raise ImportError(
        "OpenAI Agents SDK package could not be located outside the local ForexAI agents directory"
    )

# Preserve both namespaces: local ForexAI modules first, SDK package second.
__path__ = [str(_LOCAL_DIR), *map(str, _sdk_spec.submodule_search_locations)]
__file__ = _sdk_spec.origin
__spec__ = _sdk_spec

# Execute the real SDK package initializer in this already-registered package
# object. Relative imports such as ``from .agent import Agent`` then resolve
# against the combined local+SDK __path__ above.
_sdk_source = Path(_sdk_spec.origin).read_text(encoding="utf-8")
exec(compile(_sdk_source, _sdk_spec.origin, "exec"), globals(), globals())
