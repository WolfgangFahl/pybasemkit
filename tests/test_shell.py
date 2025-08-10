"""
Created on 2025-05-14

@author: wf
"""

from basemkit.basetest import Basetest
from basemkit.shell import Shell


class TestShell(Basetest):
    """
    test shell commands
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def testShell(self):
        """
        test the shell handling
        """
        shell = Shell()
        for cmd, expected in [
            # ("pwd", "test"),
            # ("which git", "git"),
            ("echo $PATH", "bin"),
            # ("docker ps", "CONTAINER ID"),
            # ("which soffice", "soffice"),
        ]:
            p = shell.run(cmd, tee=self.debug)
            if self.debug:
                print(p)
                print(p.stdout)
            self.assertEqual(0, p.returncode)
            self.assertIn(expected, p.stdout)
