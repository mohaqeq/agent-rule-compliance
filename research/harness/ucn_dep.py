"""Locate the ucn tool, which this repository installs as a dependency, and make its modules importable.

Import this module before `import ucn_validate` or `import ucn_project`. Install the dependency with `pip install .`
from the repository root (see pyproject.toml: it pins the tag of the ucn repository).
"""
import os
import sys

try:
    import ucn
except ImportError as exc:  # a clear message is more useful than a traceback three imports deep
    raise SystemExit("The ucn package is not installed. From the repository root, run: pip install .") from exc

DIR = os.path.dirname(os.path.abspath(ucn.__file__))
if DIR not in sys.path:
    sys.path.insert(0, DIR)


def resolve(path):
    """A spec may name a tool file as 'ucn/ucn_validate.py' (the old layout): map it to the installed package."""
    if os.path.exists(path):
        return os.path.abspath(path)
    inside = os.path.join(DIR, os.path.basename(path))
    return inside if os.path.exists(inside) else os.path.abspath(path)
