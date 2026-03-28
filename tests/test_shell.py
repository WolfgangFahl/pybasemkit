"""
Created on 2025-05-14

@author: wf
"""

from typing import List

from basemkit.basetest import Basetest
from basemkit.shell import Shell


class TestShell(Basetest):
    """
    test shell commands
    """

    def setUp(self, debug=False, profile=True):
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

    def test_encoding_errors(self):
        """
        Test that non-UTF-8 bytes in subprocess output do not raise UnicodeDecodeError.
        With errors='replace' (the new default) bad bytes are replaced by U+FFFD.
        """
        shell = Shell()
        # printf emits a raw 0xdf byte which is invalid UTF-8 (it is valid Latin-1: ß)
        p = shell.run("printf '\\xdf'")
        if self.debug:
            print(repr(p.stdout))
        # Must not raise; returncode must be 0
        self.assertEqual(0, p.returncode)
        # The replacement character U+FFFD must appear in the decoded output
        self.assertIn("\ufffd", p.stdout)

    def test_callbacks(self):
        """
        Test that stdout_callback and stderr_callback are invoked for each line.
        """
        shell = Shell()
        stdout_lines: List[str] = []
        stderr_lines: List[str] = []

        p = shell.run(
            "printf 'line1\\nline2\\nline3\\n' && printf 'err1\\nerr2\\n' >&2",
            stdout_callback=lambda line: stdout_lines.append(line),
            stderr_callback=lambda line: stderr_lines.append(line),
        )
        if self.debug:
            print("stdout_lines:", stdout_lines)
            print("stderr_lines:", stderr_lines)

        self.assertEqual(0, p.returncode)
        # Callbacks receive lines including the trailing newline from readline()
        self.assertEqual(["line1\n", "line2\n", "line3\n"], stdout_lines)
        self.assertEqual(["err1\n", "err2\n"], stderr_lines)
        # Captured buffers must also be consistent
        self.assertEqual("line1\nline2\nline3\n", p.stdout)
        self.assertEqual("err1\nerr2\n", p.stderr)
