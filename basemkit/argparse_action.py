"""
Created on 2025-08-29

@author: wf
"""

import argparse
from typing import Optional


class StoreDictKeyPair(argparse.Action):
    """
    Custom argparse action to store key-value pairs as a dictionary.

    This class implements an argparse action to parse and store command-line
    arguments in the form of key-value pairs. The pairs should be separated by
    a comma and each key-value pair should be separated by an equals sign.

    Example:
        --option key1=value1,key2=value2,key3=value3

    Reference:
        https://stackoverflow.com/a/42355279/1497139
    """

    def __call__(
        self,
        _parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str,
        _option_string: Optional[str] = None,
    ) -> None:
        """
        Parse key-value pairs and store them as a dictionary in the namespace.

        Args:
            parser (argparse.ArgumentParser): The argument parser object.
            namespace (argparse.Namespace): The namespace to store the parsed values.
            values (str): The string containing key-value pairs separated by commas.
            option_string (Optional[str]): The option string, if provided.
        """
        my_dict = {}
        for kv in values.split(","):
            k, v = kv.split("=")
            my_dict[k] = v
        setattr(namespace, self.dest, my_dict)
