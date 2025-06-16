"""
Created on 2025-06-16

Minimal reusable command line base class with standard options.

@author: wf
"""

from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
import sys
import traceback
from typing import Any, Optional, List
import webbrowser
import shutup
# avoid ugly deprecation messages see
# https://stackoverflow.com/questions/879173/how-to-ignore-deprecation-warnings-in-python
shutup.please()

class BaseCmd:
    """
    Minimal reusable command line base class with standard options:
    --about, --debug, --force, --quiet, --verbose, --version.

    Intended to be subclassed by tools requiring consistent CLI behavior.
    """

    def __init__(self, version: Any, description: Optional[str] = None):
        """
        Initialize the BaseCmd instance.

        Args:
            version: An object with .name, .version, .description, and .doc_url attributes.
            description (str): Optional CLI description. Defaults to version.description.
        """
        self.version = version
        self.description = description or self.version.description
        self.version_msg = f"{self.version.name} {self.version.version}"
        self.program_version_message = self.version_msg
        self.debug = False
        self.quiet = False
        self.verbose = False
        self.force = False
        self.parser = None
        self.exit_code = 0
        self.args = None

    def add_arguments(self, parser: ArgumentParser):
        """
        Add standard CLI arguments to the parser, sorted by long option name.

        Args:
            parser (ArgumentParser): The parser to add arguments to.
        """
        parser.add_argument("-a", "--about", action="store_true", help="show version info and open documentation")
        parser.add_argument("-d", "--debug", action="store_true", help="enable debug output")
        parser.add_argument(
            "--debugLocalPath", help="remote debug Server path mapping - localPath - path on machine where python runs"
        )
        parser.add_argument("--debugPort", type=int, default=5678, help="remote debug Port [default: %(default)s]")
        parser.add_argument(
            "--debugRemotePath", help="remote debug Server path mapping - remotePath - path on debug server"
        )
        parser.add_argument("--debugServer", help="remote debug Server")
        parser.add_argument("-f", "--force", action="store_true", help="force overwrite or unsafe actions")
        parser.add_argument("-q", "--quiet", action="store_true", help="suppress all output")
        parser.add_argument("-v", "--verbose", action="store_true", help="increase output verbosity")
        parser.add_argument("-V", "--version", action="version", version=self.program_version_message)


    def getArgParser(self, description: str, version_msg: str) -> ArgumentParser:
        """
        Compatibility layer for legacy camelCase contract.
        Calls get_arg_parser with overridden description and version_msg.
        """
        self.description = description
        self.program_version_message = version_msg
        parser = ArgumentParser(description=description, formatter_class=RawDescriptionHelpFormatter)
        self.add_arguments(parser)
        return parser


    def get_arg_parser(self) -> ArgumentParser:
        """
        Create and configure the argument parser.

        Returns:
            ArgumentParser: The configured argument parser.
        """
        parser = self.getArgParser(self.description, self.version_msg)
        return parser

    def parse_args(self, argv=None) -> Namespace:
        """
        Parse command line arguments.

        Args:
            argv (list): Optional list of command line arguments. Defaults to sys.argv.

        Returns:
            Namespace: Parsed argument values.
        """
        if self.parser is None:
            self.parser = self.get_arg_parser()
        self.args = self.parser.parse_args(argv)
        args = self.args
        return args

    def cmd_parse(self, argv: List[str]) -> Namespace:
        """delegate method"""
        args= self.parse_args(argv)
        return args


    def optional_debug(self, args: Namespace):
        """
        Optionally start remote debugging if debugServer is specified.

        Args:
            args (Namespace): Parsed CLI arguments
        """
        if args.debugServer:
            import pydevd
            import pydevd_file_utils

            remote_path = args.debugRemotePath
            local_path = args.debugLocalPath

            if remote_path and local_path:
                pydevd_file_utils.setup_client_server_paths([(remote_path, local_path)])

            pydevd.settrace(
                args.debugServer,
                port=args.debugPort,
                stdoutToServer=True,
                stderrToServer=True,
            )
            print("Remote debugger attached.")

    def handle_args(self, args: Namespace) -> bool:
        """
        Handle parsed arguments. Intended to be overridden in subclasses.

        Args:
            args (Namespace): Parsed argument namespace.

        Returns:
            bool: True if argument was handled and no further processing is required.
        """
        self.args = args
        self.debug = args.debug
        self.quiet = args.quiet
        self.verbose = args.verbose
        self.force = args.force
        self.optional_debug(args)
        if args.about:
            print(self.program_version_message)
            print(f"see {self.version.doc_url}")
            webbrowser.open(self.version.doc_url)
            return True

        return False

    def run(self, argv=None) -> int:
        """
        Execute the command line logic.

        Args:
            argv (list): Optional command line arguments.

        Returns:
            int: Exit code: 0 = OK, 1 = KeyboardInterrupt, 2 = Exception.
        """
        try:
            args = self.parse_args(argv)
            handled = self.handle_args(args)
            exit_code = 0
            if not handled:
                exit_code = 0
        except KeyboardInterrupt:
            exit_code = 1
        except Exception as e:
            if self.debug:
                raise
            sys.stderr.write(f"{self.version.name}: {e}\n")
            if getattr(self, "args", None) and self.args.debug:
                sys.stderr.write(traceback.format_exc())
            exit_code = 2
        return exit_code

    @classmethod
    def main(cls, version: Any, argv=None) -> int:
        """
        Entry point for scripts using this command line interface.

        Args:
            version: Version metadata object passed to constructor.
            argv (list): Optional command line arguments.

        Returns:
            int: Exit code from `run()`.
        """
        instance = cls(version)
        exit_code = instance.run(argv)
        return exit_code
