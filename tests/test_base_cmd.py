"""
Created on 2025-06-16

@author: wf
"""

from argparse import Namespace

from basemkit.base_cmd import BaseCmd
from basemkit.basetest import Basetest


class DummyVersion:
    name = "dummy"
    version = "0.0.1"
    description = "Dummy CLI"
    doc_url = "https://example.org"


class TestBaseCmd(Basetest):
    """
    test BaseCmd functionality
    """

    def setUp(self, debug=False, profile=True):
        super().setUp(debug=debug, profile=profile)

    def test_exit_code(self):
        """
        test that run returns the exit_code a subclass sets in handle_args
        """

        class ExitCodeCmd(BaseCmd):
            """
            command setting an exit code depending on --force
            """

            def handle_args(self, args: Namespace) -> bool:
                if args.force:
                    self.exit_code = 1
                return True

        for argv, expected in [([], 0), (["--force"], 1)]:
            with self.subTest(argv=argv):
                cmd = ExitCodeCmd(version=DummyVersion)
                self.assertEqual(expected, cmd.run(argv))

    def test_arg_parsing(self):
        """
        test standard argument parsing and flags
        """
        base_cmd = BaseCmd(version=DummyVersion)
        args = base_cmd.parse_args(["--debug", "--verbose", "--force"])
        self.assertTrue(args.debug)
        self.assertTrue(args.verbose)
        self.assertTrue(args.force)
