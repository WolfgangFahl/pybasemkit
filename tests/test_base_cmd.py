"""
Created on 2025-06-16

@author: wf
"""

from basemkit.basetest import Basetest
from basemkit.base_cmd import BaseCmd
from argparse import Namespace


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

    def test_arg_parsing(self):
        """
        test standard argument parsing and flags
        """
        base_cmd = BaseCmd(version=DummyVersion)
        args = base_cmd.parse_args(["--debug", "--verbose", "--force"])
        self.assertTrue(args.debug)
        self.assertTrue(args.verbose)
        self.assertTrue(args.force)
