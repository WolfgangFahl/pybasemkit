# AGENTS.md — pybasemkit

Coding agent instructions for the `pybasemkit` repository.
Package installs as `basemkit`; PyPI name is `pybasemkit`.

---

## Project Overview

- **Python:** `>=3.10` (CI runs 3.12; classifiers cover 3.10–3.13)
- **Build backend:** `hatchling` (configured entirely in `pyproject.toml`)
- **Runtime deps:** `dacite`, `dataclasses-json`, `PyYAML`, `shutup`
- **Test deps (optional):** `pytest`, `green`, `tox`
- **Dev deps (optional):** `black`, `isort`

---

## Build & Install

```bash
# Install from source (editable not required; plain install is the norm)
pip install .

# Install with test extras
pip install ".[test]"

# Install with dev extras
pip install ".[dev]"

# Build wheel + sdist
hatch build
```

---

## Formatting

Two tools are used together. Always run both before committing:

```bash
# Format all source and test files (isort then black)
scripts/blackisort
```

Under the hood this runs:
```bash
isort basemkit/*.py
black basemkit/*.py
isort tests/*.py
black tests/*.py
```

**Line length is 120 characters** (configured in `[tool.black]` in `pyproject.toml`).

No other linters (flake8, ruff, pylint, mypy) are configured.

---

## Running Tests

The default runner is `unittest discover`. All test classes inherit from
`basemkit.basetest.Basetest` (which subclasses `unittest.TestCase`).
`pytest` also works because it collects unittest-style classes.

```bash
# Run the full test suite (default)
python3 -m unittest discover

# Using the project script (same as above)
scripts/test

# Using green (colorful output, serial)
scripts/test -g
# or:
green tests/ -s 1

# Using tox
scripts/test -t
# or:
tox -e py

# Using pytest
python -m pytest tests/
```

### Running a Single Test

```bash
# Single test module
python -m unittest tests.test_yamlable

# Single test class
python -m unittest tests.test_yamlable.TestYamlAble

# Single test method  ← most common for targeted debugging
python -m unittest tests.test_yamlable.TestYamlAble.test_to_yaml

# With pytest
python -m pytest tests/test_yamlable.py
python -m pytest tests/test_yamlable.py::TestYamlAble::test_to_yaml

# With green
green tests/test_yamlable.py -s 1
```

---

## Code Style

### Imports

Follow PEP 8 import order, sorted by `isort` (default profile):

1. Standard library
2. Third-party packages
3. Local `basemkit.*` imports

```python
import sys
import traceback
from argparse import ArgumentParser, Namespace
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar

import yaml
from dacite import from_dict

from basemkit.yamlable import YamlAble
```

Do **not** use `from __future__ import annotations`. Use `from typing import ...` imports for all type hints.

### Type Annotations

Every function parameter and return type must be annotated.

```python
def load_from_yaml_file(cls: Type[T], filename: str) -> T: ...
def run(self, cmd: str, text: bool = True, debug: bool = False) -> subprocess.CompletedProcess: ...
def get_level_summary(self, level: str, limit: int = 7) -> Tuple[int, str]: ...
```

- Use `Optional[X]` (not `X | None`) — keeps 3.10 compatibility explicit
- Use `Union[str, Path]` (not `str | Path`)
- Use `TypeVar` for generic patterns: `T = TypeVar("T")`

### Naming Conventions

| Category | Convention | Examples |
|---|---|---|
| Classes | `PascalCase` | `YamlAble`, `BaseCmd`, `Basetest`, `ShellResult` |
| Functions / methods | `snake_case` | `to_yaml`, `load_from_yaml_file`, `handle_exception` |
| Instance / local variables | `snake_case` | `self.shell_path`, `self.do_log`, `result` |
| Module-level constants | `UPPER_SNAKE_CASE` | `BLUE`, `RED`, `GREEN`, `END_COLOR` |
| Private / internal | `_leading_underscore` | `_yaml_setup`, `_yaml_dumper`, `_run` |
| TypeVars | Single capital | `T = TypeVar("T")` |

Avoid introducing new `camelCase` method names; those that exist are legacy compatibility shims.

### Docstrings

Use **Google-style** docstrings (configured in `mkdocs.yml` as `docstring_style: google`).

```python
def to_yaml(
    self,
    ignore_none: bool = True,
    sort_keys: bool = False,
) -> str:
    """
    Convert this dataclass object to a YAML string.

    Args:
        ignore_none: Omit attributes whose value is None.
        sort_keys: Sort dictionary keys in the output.

    Returns:
        YAML string representation of the dataclass.

    Raises:
        ValueError: If the object is not a dataclass instance.
    """
```

- One-liner docstrings are acceptable for trivial methods.
- Module-level docstrings use the format:

```python
"""
Created on YYYY-MM-DD

@author: wf
"""
```

### Error Handling

```python
# Preferred: catch specific exceptions; use debug flag for traceback
try:
    result = self.shell.run(command, debug=self.debug)
except Exception as ex:
    self.handle_exception(f"command '{command}'", ex)

# Optional imports that may not be installed: guard with try/except ImportError
try:
    import pydevd
except ImportError:
    print("Error: 'pydevd' is required for remote debugging.", file=sys.stderr)
    return

# Silently ignore cleanup errors
try:
    os.unlink(tmp_path)
except Exception:
    pass

# Top-level entry points: catch BaseException and map to exit codes
try:
    args = self.parse_args(argv)
    self.handle_args(args)
except BaseException as e:
    exit_code = self.handle_exception(e)
```

### Module Organization

1. Module docstring (creation date + author)
2. Imports (stdlib → third-party → local)
3. Module-level constants
4. Class definitions (one primary class per module)
5. No `if __name__ == "__main__"` guard except in `basetest.py`

---

## Writing Tests

All test classes must subclass `Basetest`, not `unittest.TestCase` directly.

```python
from basemkit.basetest import Basetest

class TestMyFeature(Basetest):
    """Tests for my_feature."""

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        # additional setup here

    def test_something(self):
        # use self.debug for conditional diagnostic prints
        result = my_function()
        self.assertEqual(result, expected)
```

Key `Basetest` utilities:

```python
Basetest.inPublicCI()   # True when running under GitHub Actions / Travis / Jenkins
Basetest.isUser("wf")  # True if the current user matches
```

`Basetest.setUp` creates a `Profiler` that automatically times each test and prints
elapsed time in `tearDown`.

---

## CI / CD

- **CI:** `.github/workflows/build.yml` — runs `scripts/install && scripts/test` on every push/PR to `main` (Python 3.12, ubuntu-latest). Env var `GHACTIONS=ACTIVE` is set.
- **CD:** `.github/workflows/upload-to-pypi.yml` — runs `hatch build` and publishes to PyPI via OIDC trusted publishing on GitHub release creation.
- No coverage reporting, no linting step, and no multi-version matrix in CI currently.

---

## Repository Layout

```
basemkit/           # Main package (import as "basemkit")
tests/              # unittest-style tests; filenames match test_<module>.py
scripts/            # Shell scripts: blackisort, test, install, doc, release
docs/               # MkDocs source (material theme + mkdocstrings)
pyproject.toml      # All project metadata, build config, and tool settings
mkdocs.yml          # Documentation site config
```
