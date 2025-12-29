"""
Created on 2025-12-29

PyDev Remote Debugging utility

The intention to hide the complexity of PyDev Remote debugging as explained at

https://www.pydev.org/manual_adv_remote_debugger.html

The Path mapping is notoriously complex as e.g. outlined in:

https://stackoverflow.com/questions/79856091/pydev-path-mapping-with-virtual-env
and
https://github.com/WolfgangFahl/pybasemkit/issues/15

Relevant sources:
https://github.com/fabioz/PyDev.Debugger/blob/main/pydevd.py
https://github.com/fabioz/PyDev.Debugger/blob/main/pydevd_file_utils.py

@author: wf
"""
import os
import socket
import sys
from argparse import Namespace
from dataclasses import dataclass, field
from typing import List, Tuple

@dataclass
class PathMapping:
    """
    Represents a single path mapping

    local / python - The Execution Environment:
        This is "Here" it is the target of your remote debugging activity but
        local to where you start your code to be debugged

        It is where your Python script is currently running
        (e.g., a Docker container, a remote Linux server, or a virtual environment).
        When your code runs os.path.exists(m.local),
        is checking the filesystem of the machine executing the code.

        args.debugLocalPath represents the path where the .py files
        sit inside the server/container.

    remote / eclipse / vscode / pycharm - the IDE / Developer Environment:

        This is "There". On the IDE your start Pydev/Start Debug Server
        and "Debug Server at port: 5678" is displayed

        This is where the keyboard and monitor are (e.g., your Windows or Mac
        laptop running PyDev/Eclipse/VSCode).

        From the perspective of the running script, the IDE is a "Remote Server"
        listening for a connection.

        args.debugRemotePath represents the path where
        the source code sits on your physical laptop.

    """
    remote: str # eclipse / vscode/ pycharm
    local: str  # python execution environment path to be remotely debugged

@dataclass
class PathMappings:
    """
    Represents a collection of path mappings.
    """
    mappings: List[PathMapping] = field(default_factory=list)

    @classmethod
    def from_args(cls, remote_str: str, local_str: str) -> 'PathMappings':
        """
        Parses comma-separated remote
        and local path strings into a PathMappings object.
        """
        remote_paths = [r.strip() for r in remote_str.split(",")]
        local_paths = [l.strip() for l in local_str.split(",")]

        if len(remote_paths) != len(local_paths):
            raise ValueError("debugRemotePath and debugLocalPath must have the same number of entries")

        mapping_list = [PathMapping(remote=r, local=l) for r, l in zip(remote_paths, local_paths)]
        path_mappings= cls(mappings=mapping_list)
        return path_mappings

    def as_tuple_list(self) -> List[Tuple[str, str]]:
        """
        Returns the mappings in the format required by pydevd (list of tuples).
        """
        tuple_list= [(m.remote, m.local) for m in self.mappings]
        return tuple_list

class RemoteDebugSetup:
    """
    Handles initialization and connection for pydevd remote debugging.
    """

    def __init__(self, args: Namespace):
        """
        Initialize the RemoteDebugger with command line arguments.

        Args:
            args (Namespace): Parsed CLI arguments containing debug flags.
        """
        self.args = args
        self.path_mappings=None

    def get_path_mappings(self):
        """
        get my path mappings
        """
        remote_path = getattr(self.args, "debugRemotePath", "")
        local_path = getattr(self.args, "debugLocalPath", "")

        self.log(f"remote_path = {repr(remote_path)}")
        self.log(f"local_path = {repr(local_path)}")

        # note the complexity of https://stackoverflow.com/a/41765551/1497139
        if remote_path and local_path:
            self.path_mappings = PathMappings.from_args(remote_path, local_path)


    def log(self, msg: str):
        """
        Print debug message to stderr if debug mode is enabled.
        """
        if getattr(self.args, "debug", False):
            print(f"DEBUG: {msg}", file=sys.stderr)

    def start(self):
        """
        Optionally start pydevd remote debugging if debugServer is specified.
        See https://www.pydev.org/manual_adv_remote_debugger.html
        """
        if not getattr(self.args, "debugServer", None):
            return

        # Lazy import to avoid dependency requirement if not debugging
        try:
            import pydevd
            import pydevd_file_utils
        except ImportError:
            print("Error: 'pydevd' module is required for remote debugging but is not installed.", file=sys.stderr)
            print("PyDev is available via https://pypi.org/project/pydevd/")
            print("Try: pip install pydevd", file=sys.stderr)
            return

        self.log(f"Server pydevd version: {pydevd.__version__}")
        self.log(f"pydevd_file_utils is at: {os.path.abspath(pydevd_file_utils.__file__)}")

        self.get_path_mappings()
        self.setup_path_mappings(pydevd_file_utils)

        # Initialize a remote debug session see
        # https://www.pydev.org/manual_adv_remote_debugger.html
        # suspend is True by default
        pydevd.settrace(
            self.args.debugServer,
            port=self.args.debugPort,
            stdoutToServer=True,
            stderrToServer=True,
        )
        print("Remote debugger attached.")

    def setup_path_mappings(self, pydevd_file_utils):
        """
        Configures the path mappings between local machine and remote debug server.
        """
        self.print_debug_info()

        # Monkey patch for https://stackoverflow.com/questions/79856091/pydev-path-mapping-with-virtual-env
        original_setup = pydevd_file_utils.setup_client_server_paths

        def fixed_setup(paths: List[Tuple[str, str]]):
            """
            protect setup_client_server_paths to be
            called a second time with bad argumens
            """
            # Check if this is the bad call (single tuple with comma-separated strings)
            if len(paths) == 1 and isinstance(paths[0], tuple):
                remote, local = paths[0]
                if ',' in remote and ',' in local:
                    self.log("IGNORING bad setup_client_server_paths call with comma-separated strings")
                    self.log(f"remote='{remote}'")
                    self.log(f"local='{local}'")
                    # Return without calling original - our good mappings are already set
                    return

            self.log(f"setup_client_server_paths called with {len(paths)} paths:")
            for i, p in enumerate(paths):
                self.log(f"  [{i}] {p}")
            # only call original_setup once
            return original_setup(paths)

        # monkey patch the setup_client_server_paths
        pydevd_file_utils.setup_client_server_paths = fixed_setup

        # https://github.com/fabioz/PyDev.Debugger/blob/main/pydevd_file_utils.py
        tuple_list=self.path_mappings.as_tuple_list()
        pydevd_file_utils.setup_client_server_paths(tuple_list)

    def print_debug_info(self):
        """
        Prints detailed debug info about paths.
        """
        fqdn = socket.getfqdn()
        self.log(f"Local Hostname={fqdn}")
        self.log(f"Remote Server={self.args.debugServer}")
        self.log(f"I am running in: {os.getcwd()}")
        # Note: __file__ here refers to remotedebug.py, not the caller
        self.log(f"This file is at: {os.path.abspath(__file__)}")

        if self.path_mappings:
            for m in self.path_mappings.mappings:
                marker = "✅" if os.path.exists(m.local) else "❌"
                self.log(f"PATH MAP: Remote (IDE)='{m.remote}' <-> Local='{m.local}' {marker}")