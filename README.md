# pybasemkit
Python base module kit: YAML/JSON I/O, structured logging, CLI tooling, shell execution, and remote pydevd debug support.

| | |
| :--- | :--- |
| **PyPi** | [![PyPI Status](https://img.shields.io/pypi/v/pybasemkit.svg)](https://pypi.python.org/pypi/pybasemkit/) [![License](https://img.shields.io/github/license/WolfgangFahl/pybasemkit.svg)](https://www.apache.org/licenses/LICENSE-2.0) [![pypi](https://img.shields.io/pypi/pyversions/pybasemkit)](https://pypi.org/project/pybasemkit/) [![format](https://img.shields.io/pypi/format/pybasemkit)](https://pypi.org/project/pybasemkit/) [![downloads](https://img.shields.io/pypi/dd/pybasemkit)](https://pypi.org/project/pybasemkit/) |
| **GitHub** | [![Github Actions Build](https://github.com/WolfgangFahl/pybasemkit/actions/workflows/build.yml/badge.svg)](https://github.com/WolfgangFahl/pybasemkit/actions/workflows/build.yml) [![Release](https://img.shields.io/github/v/release/WolfgangFahl/pybasemkit)](https://github.com/WolfgangFahl/pybasemkit/releases) [![Contributors](https://img.shields.io/github/contributors/WolfgangFahl/pybasemkit)](https://github.com/WolfgangFahl/pybasemkit/graphs/contributors) [![Last Commit](https://img.shields.io/github/last-commit/WolfgangFahl/pybasemkit)](https://github.com/WolfgangFahl/pybasemkit/commits/) [![GitHub issues](https://img.shields.io/github/issues/WolfgangFahl/pybasemkit.svg)](https://github.com/WolfgangFahl/pybasemkit/issues) [![GitHub closed issues](https://img.shields.io/github/issues-closed/WolfgangFahl/pybasemkit.svg)](https://github.com/WolfgangFahl/pybasemkit/issues/?q=is%3Aissue+is%3Aclosed) |
| **Code** | [![style-black](https://img.shields.io/badge/%20style-black-000000.svg)](https://github.com/psf/black) [![imports-isort](https://img.shields.io/badge/%20imports-isort-%231674b1)](https://pycqa.github.io/isort/) |
| **Docs** | [![API Docs](https://img.shields.io/badge/API-Documentation-blue)](https://WolfgangFahl.github.io/pybasemkit/) [![formatter-docformatter](https://img.shields.io/badge/%20formatter-docformatter-fedcba.svg)](https://github.com/PyCQA/docformatter) [![style-google](https://img.shields.io/badge/%20style-google-3666d6.svg)](https://google.github.io/styleguide/pyguide.html#s3.8-comments-and-docstrings) |

## Docs and Tutorials
[Wiki](https://wiki.bitplan.com/index.php/pybasemkit)

## CLI Tooling

`basemkit.base_cmd.BaseCmd` is the standard base class for every BITPlan
command line interface. It provides the house-standard options
`-a/--about`, `-d/--debug`, `--debugServer/--debugPort` (remote pydevd),
`-f/--force`, `-q/--quiet`, `-v/--verbose` and `-V/--version` plus
consistent exit codes (0 = OK, 1 = KeyboardInterrupt, 2 = Exception).
Downstream projects must subclass it instead of using plain `argparse`.

The canonical pattern - a `Version` dataclass and a `BaseCmd` subclass:

```python
from dataclasses import dataclass

from basemkit.base_cmd import BaseCmd

import mytool


@dataclass
class Version:
    """Version information for mytool."""

    name: str = "mytool"
    version: str = mytool.__version__
    date: str = "2026-08-02"
    updated: str = "2026-08-02"
    description: str = "what mytool does"
    authors: str = "Wolfgang Fahl"
    doc_url: str = "https://wiki.bitplan.com/index.php/Mytool"
    chat_url: str = "https://github.com/WolfgangFahl/mytool/discussions"
    cm_url: str = "https://github.com/WolfgangFahl/mytool"


class MytoolCmd(BaseCmd):
    """mytool command line interface."""

    def __init__(self):
        super().__init__(Version())

    def add_arguments(self, parser):
        """Add tool arguments to the given parser."""
        super().add_arguments(parser)
        parser.add_argument("--input", help="input file")

    def handle_args(self, args) -> bool:
        """Handle parsed arguments."""
        handled = super().handle_args(args)
        if not handled and args.input:
            # tool logic here
            handled = True
        return handled


def main(argv=None) -> int:
    """CLI entry point."""
    cmd = MytoolCmd()
    exit_code = cmd.run(argv)
    return exit_code
```

Register the entry point in `pyproject.toml`:

```toml
[project.scripts]
mytool = "mytool.mytool_cmd:main"
```

Live examples: [gov-service](https://github.com/WolfgangFahl/gov-service),
[ProfiWiki](https://github.com/WolfgangFahl/ProfiWiki),
[djvu-viewer](https://github.com/WolfgangFahl/djvu-viewer),
[ngwidgets](https://github.com/WolfgangFahl/nicegui_widgets).
