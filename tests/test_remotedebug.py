"""
Created on 2025-112-29

@author: wf
"""

from argparse import Namespace

from basemkit.basetest import Basetest

from basemkit.remotedebug import RemoteDebugSetup, PathMappings, PathMapping


class TestRemoteDebugSetup(Basetest):
    """
    test the remote Debugger handling
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def test_debug_info(self):
        """
        test debug info
        """
        args = Namespace(
            debugServer="127.0.0.1",
            debugPort=5678,
            debugRemotePath="/remote/app",
            debugLocalPath="/local/app",
            debug=True # Enable internal logging
        )

        debug_setup=RemoteDebugSetup(args=args)
        debug_setup.get_path_mappings()
        debug_setup.print_debug_info()

    def test_path_mappings_parsing(self):
        """
        Test that comma-separated path strings are parsed into PathMapping objects correctly.
        """
        remote_str = "/app/src,/app/lib"
        local_str = "C:\\Users\\Src,C:\\Users\\Lib"

        pm = PathMappings.from_args(remote_str, local_str)

        self.assertEqual(2, len(pm.mappings))

        # Check first mapping
        self.assertEqual("/app/src", pm.mappings[0].remote)
        self.assertEqual("C:\\Users\\Src", pm.mappings[0].local)

        # Check second mapping
        self.assertEqual("/app/lib", pm.mappings[1].remote)
        self.assertEqual("C:\\Users\\Lib", pm.mappings[1].local)


    def test_path_mappings_mismatch(self):
        """
        Test that unequal list lengths raise an error.
        """
        remote_str = "/app/src"
        local_str = "C:\\src,C:\\lib" # Two locals, one remote

        with self.assertRaises(ValueError):
            PathMappings.from_args(remote_str, local_str)


    def test_tuple_conversion(self):
        """
        Test conversion to list of tuples for pydevd.
        """
        pm = PathMappings(mappings=[
            PathMapping(remote="/r", local="/l")
        ])
        expected = [("/r", "/l")]
        self.assertEqual(expected, pm.as_tuple_list())
