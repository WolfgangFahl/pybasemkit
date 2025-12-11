"""
Created on 29.08.2025

@author: wf
"""

import argparse

from basemkit.argparse_action import StoreDictKeyPair
from basemkit.basetest import Basetest


class TestStoreDictKeyPair(Basetest):
    """
    Test the StoreDictKeyPair argparse action
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.debug = debug

    def test_single_pair(self):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--set",
            action=StoreDictKeyPair,
            metavar="PAGE=NAME[,PAGE=NAME...]",
        )
        args = parser.parse_args(["--set", "3=Keynote"])
        self.assertTrue("3" in args.set)
        self.assertEqual(args.set["3"], "Keynote")
        if self.debug:
            print(args.set)

    def test_multiple_pairs(self):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--set",
            action=StoreDictKeyPair,
            metavar="PAGE=NAME[,PAGE=NAME...]",
        )
        args = parser.parse_args(["--set", "3=Keynote,5=Overview,7=Appendix"])
        self.assertEqual(args.set["3"], "Keynote")
        self.assertEqual(args.set["5"], "Overview")
        self.assertEqual(args.set["7"], "Appendix")
        if self.debug:
            print(args.set)
