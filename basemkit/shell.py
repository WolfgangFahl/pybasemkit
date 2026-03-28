"""
Created on 2025-05-14

@author: wf
"""

import io
import os
import subprocess
import sys
import threading
from argparse import Namespace
from pathlib import Path
from typing import Callable, Dict, List, Optional


class ShellResult:
    """
    result of a command line call
    """

    def __init__(self, proc, success: bool):
        self.proc = proc
        self.success = success

    def __str__(self):
        text = self.as_text()
        return text

    def as_text(self, debug: bool = False):
        if debug:
            text = (
                f"{self.proc.args} → rc={self.proc.returncode}, success={self.success}"
            )
        else:
            text = "✅" if self.success else f"❌ → rc={self.proc.returncode}"
        return text


class StreamTee:
    """
    Tees a single input stream to both a mirror and a capture buffer.
    An optional per-line callback is invoked for each line after buffering.
    """

    def __init__(
        self,
        source,
        mirror,
        buffer,
        tee=True,
        callback: Optional[Callable[[str], None]] = None,
    ):
        self.source = source
        self.mirror = mirror
        self.buffer = buffer
        self.tee = tee
        self.callback = callback
        self.thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        for line in iter(self.source.readline, ""):
            if self.tee:
                self.mirror.write(line)
                self.mirror.flush()
            self.buffer.write(line)
            if self.callback:
                self.callback(line)
        self.source.close()

    def start(self):
        self.thread.start()

    def join(self, timeout: Optional[float] = None):
        self.thread.join(timeout=timeout)


class SysTee:
    """
    Tee sys.stdout and sys.stderr to a logfile while preserving original output.
    """

    def __init__(self, log_path: str):
        self.logfile = open(log_path, "a")
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self

    def write(self, data):
        self.original_stdout.write(data)
        self.logfile.write(data)

    def flush(self):
        self.original_stdout.flush()
        self.logfile.flush()

    def close(self):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        self.logfile.close()


class StdTee:
    """
    Manages teeing for both stdout and stderr using StreamTee instances.
    Captures output in instance variables.
    Optional per-line callbacks are invoked for each stdout/stderr line.
    """

    def __init__(
        self,
        process,
        tee=True,
        stdout_callback: Optional[Callable[[str], None]] = None,
        stderr_callback: Optional[Callable[[str], None]] = None,
    ):
        self.stdout_buffer = io.StringIO()
        self.stderr_buffer = io.StringIO()
        self.out_tee = StreamTee(
            process.stdout,
            sys.stdout,
            self.stdout_buffer,
            tee,
            callback=stdout_callback,
        )
        self.err_tee = StreamTee(
            process.stderr,
            sys.stderr,
            self.stderr_buffer,
            tee,
            callback=stderr_callback,
        )

    def start(self):
        self.out_tee.start()
        self.err_tee.start()

    def join(self, timeout: Optional[float] = None):
        self.out_tee.join(timeout=timeout)
        self.err_tee.join(timeout=timeout)

    @classmethod
    def run(
        cls,
        process,
        tee=True,
        stdout_callback: Optional[Callable[[str], None]] = None,
        stderr_callback: Optional[Callable[[str], None]] = None,
    ):
        """
        Run teeing and capture for the given process.
        Returns a StdTee instance with stdout/stderr captured.
        """
        std_tee = cls(
            process,
            tee=tee,
            stdout_callback=stdout_callback,
            stderr_callback=stderr_callback,
        )
        std_tee.start()
        return std_tee


class Shell:
    """
    Runs commands with environment from profile
    """

    def __init__(self, profile: str = None, shell_path: str = None):
        """
        Initialize shell with optional profile

        Args:
            profile: Path to profile file to source e.g. ~/.zprofile
            shell_path: the shell_path e.g. /bin/zsh
        """
        self.profile = profile
        self.shell_path = shell_path
        self.tee_timeout = 2
        if self.shell_path is None:
            self.shell_path = os.environ.get("SHELL", "/bin/bash")
        self.shell_name = os.path.basename(self.shell_path)
        self.source_op = "source"
        if self.profile is None:
            self.profile = self.find_profile()
            if self.profile == ".profile":
                self.source_op = "."

    def find_profile(self) -> str:
        """
        Find the appropriate profile file for the current shell

        Searches for the profile file corresponding to the shell_name
        in the user's home directory.

        Returns:
            str: Path to the profile file or None if not found
        """
        profile = None
        home = os.path.expanduser("~")
        # Try common profile files
        profiles = {"zsh": ".zprofile", "bash": ".bash_profile", "sh": ".profile"}
        if self.shell_name in profiles:
            profile_name = profiles[self.shell_name]
            path = os.path.join(home, profile_name)
            if os.path.exists(path):
                profile = path
        return profile

    @classmethod
    def ofArgs(cls, args: Namespace) -> "Shell":
        """
        Create Shell from command line args

        Args:
            args: Arguments with optional profile

        Returns:
            Shell: Configured Shell
        """
        # Use explicit profile or detect
        profile = getattr(args, "profile", None)
        shell = cls(profile=profile)
        return shell

    def run(
        self,
        cmd: str,
        text: bool = True,
        encoding: str = "utf-8",
        errors: str = "replace",
        debug: bool = False,
        tee: bool = False,
        stdout_callback: Optional[Callable[[str], None]] = None,
        stderr_callback: Optional[Callable[[str], None]] = None,
        timeout: int = 60,
    ) -> subprocess.CompletedProcess:
        """
        Run command with profile, always capturing output and optionally teeing it.

        Args:
            cmd: Command to run
            text: Text mode for subprocess I/O
            encoding: Character encoding for subprocess I/O (default: utf-8)
            errors: Error handling for decoding (default: replace — bad bytes become U+FFFD
                instead of raising UnicodeDecodeError; pass 'strict' to restore old behaviour)
            debug: Print the command to be run
            tee: If True, also print output live while capturing
            stdout_callback: Optional callable invoked with each stdout line as it is produced
            stderr_callback: Optional callable invoked with each stderr line as it is produced
            timeout: Timeout in seconds for command execution (default: 60)

        Returns:
            subprocess.CompletedProcess

        Raises:
            subprocess.TimeoutExpired: If the command exceeds the timeout
        """
        shell_cmd = f"source {self.profile} && {cmd}" if self.profile else cmd

        if debug:
            print(f"Running: {shell_cmd}")

        popen_process = subprocess.Popen(
            [self.shell_path, "-c", shell_cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=text,
            encoding=encoding,
            errors=errors,
        )

        std_tee = StdTee.run(
            popen_process,
            tee=tee,
            stdout_callback=stdout_callback,
            stderr_callback=stderr_callback,
        )
        try:
            returncode = popen_process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            popen_process.kill()
            raise
        finally:
            std_tee.join(timeout=self.tee_timeout)

        process = subprocess.CompletedProcess(
            args=popen_process.args,
            returncode=returncode,
            stdout=std_tee.stdout_buffer.getvalue(),
            stderr=std_tee.stderr_buffer.getvalue(),
        )

        if process.returncode != 0:
            if debug:
                msg = f"""{process.args} failed:
  returncode: {process.returncode}
  stdout    : {process.stdout.strip()}
  stderr    : {process.stderr.strip()}
"""
                print(msg, file=sys.stderr)
            pass

        return process

    def proc_stats(
        self,
        title: str,
        procs: Dict[Path, subprocess.CompletedProcess],
        ignores: List[str] = [],
    ):
        """
        Show process statistics with checkmark/crossmark and success/failure summary.

        Args:
            title (str): A short title to label the output section.
            procs (Dict[Path, subprocess.CompletedProcess]): Mapping of input files to their process results.
            ignores (List[str], optional): List of substrings. If any is found in stderr, the error is ignored.
        """
        total = len(procs)
        failures = 0
        print(f"\n{total} {title}:")
        for idx, (path, result) in enumerate(procs.items(), start=1):
            stderr = result.stderr or ""
            stdout = result.stdout or ""
            ignored = any(ignore in stderr for ignore in ignores)
            has_error = (stderr and not ignored) or ("Error" in stdout)
            if has_error:
                symbol = "❌"
                failures += 1
            else:
                symbol = "✅"
            print(f"{symbol} {idx}/{total}: {path.name}")
        percent_ok = ((total - failures) / total) * 100 if total > 0 else 0
        print(
            f"\n✅ {total - failures}/{total} ({percent_ok:.1f}%), ❌ {failures}/{total} ({100 - percent_ok:.1f}%)"
        )
