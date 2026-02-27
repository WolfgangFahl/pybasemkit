"""
Created on 2023-12-03

@author: wf, ChatGPT

Prompts:
- Implement a YAML conversion class for dataclasses with specific handling for multi-line strings and omission of None values.
- Create a test suite for the YAML conversion class, ensuring proper formatting and functionality.
"""

import os
import tempfile
from typing import Optional

from basemkit.basetest import Basetest
from basemkit.yamlable import lod_storable


@lod_storable
class MockDataClass:
    """
    Mock dataclass for testing YAML conversion.

    Attributes:
        name (str): The name attribute.
        id (int): The identifier attribute.
        description (str, optional): Description attribute. Defaults to None.
        url (str, optional): URL attribute. Defaults to None.
    """

    name: str
    id: int
    description: Optional[str] = None
    url: Optional[str] = None
    flag: bool = True
    # sample_tuple: tuple = (1, 2, 3)  # Add a tuple attribute for testing


class TestYamlAble(Basetest):
    """
    Test the Yaml handler for dataclass to YAML conversion.
    """

    def setUp(self, debug: bool = False, profile: bool = True) -> None:
        """
        Set up the test case environment.

        Args:
            debug (bool): Flag to enable debugging output. Defaults to True.
            profile (bool): Flag to enable profiling. Defaults to True.
        """
        Basetest.setUp(self, debug=debug, profile=profile)
        self.mock_data = MockDataClass(
            name="Example",
            id=123,
            description="This is an example description with\nmultiple lines to test block scalar style.",
            url="http://example.com",
        )

    def check_yaml(self) -> str:
        """
        Converts the mock dataclass to a YAML string and optionally prints it for debugging.

        Returns:
            str: The YAML string representation of the mock dataclass.
        """
        yaml_str = self.mock_data.to_yaml()
        if self.debug:
            print(yaml_str)
        return yaml_str

    def test_to_yaml(self) -> None:
        """
        Test converting a dataclass object to a YAML string.
        """
        yaml_str = self.check_yaml()
        self.assertIn("Example", yaml_str, "The name should be included in the YAML string.")
        self.assertIn("|", yaml_str, "Block scalar style should be used for multi-line strings.")
        self.assertNotIn("null", yaml_str, "None values should not be included in the YAML string.")
        self.assertIn("url: http", yaml_str, "url should be included")

    def test_omit_none(self) -> None:
        """
        Test that None values are omitted in the YAML output.
        """
        self.mock_data.url = None  # Explicitly set url to None to test omission
        yaml_str = self.check_yaml()
        self.assertNotIn("url", yaml_str, "Keys with None values should be omitted.")

    def test_block_scalar(self) -> None:
        """
        Test that multi-line strings use block scalar style.
        """
        yaml_str = self.check_yaml()
        expected_block_indicator = "|-"
        expected_first_line_of_description = "This is an example description with"
        self.assertIn(
            expected_block_indicator,
            yaml_str,
            "Block scalar style should be used for multi-line strings.",
        )
        self.assertIn(
            expected_first_line_of_description,
            yaml_str,
            "The description should be included as a block scalar.",
        )

    def test_save_to_yaml_file(self) -> None:
        """
        Test saving a dataclass instance to a YAML file.
        """
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            self.mock_data.save_to_yaml_file(temp_file.name)
            # Check if file is created
            self.assertTrue(os.path.exists(temp_file.name))
            # Optionally read back the file to check contents
            with open(temp_file.name, "r") as file:
                yaml_content = file.read()
                self.assertIn("Example", yaml_content)

    def test_load_from_yaml_file(self) -> None:
        """
        Test loading a dataclass instance from a YAML file.
        """
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            self.mock_data.save_to_yaml_file(temp_file.name)
            loaded_instance = MockDataClass.load_from_yaml_file(temp_file.name)
            # Check if the loaded instance matches the original
            self.assertEqual(loaded_instance.name, self.mock_data.name)
            self.assertEqual(loaded_instance.id, self.mock_data.id)
            # Clean up the temp file
            os.remove(temp_file.name)

    def test_header_comment_preserved(self) -> None:
        """
        Test that a leading YAML comment block survives a full file round-trip
        when with_header_comment=True is used on both load and save.
        """
        yaml_with_header = (
            "# This is a project config file\n"
            "# Generated by the system — do not edit manually\n"
            "\n"
            "name: Example\n"
            "id: 123\n"
            "flag: true\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
            src_path = f.name
            f.write(yaml_with_header)

        try:
            # Load with header preservation
            loaded = MockDataClass.load_from_yaml_file(src_path, with_header_comment=True)
            if self.debug:
                print(f"_yaml_header: {repr(loaded._yaml_header)}")
            self.assertIsNotNone(loaded._yaml_header, "_yaml_header should be set")
            self.assertIn("project config file", loaded._yaml_header)
            self.assertIn("do not edit manually", loaded._yaml_header)
            self.assertEqual(loaded.name, "Example")
            self.assertEqual(loaded.id, 123)

            # Modify a field and save back with header
            loaded.id = 999
            with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
                dst_path = f.name
            loaded.save_to_yaml_file(dst_path, with_header_comment=True)

            with open(dst_path, "r", encoding="utf-8") as f:
                result = f.read()
            if self.debug:
                print(result)

            # Header must be at the top
            self.assertTrue(
                result.startswith("# This is a project config file"),
                "Header must be first",
            )
            self.assertIn("do not edit manually", result)
            # Modified data must be present
            self.assertIn("id: 999", result)
            self.assertIn("name: Example", result)

            # Saving without flag must NOT include the header
            with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
                no_header_path = f.name
            loaded.save_to_yaml_file(no_header_path, with_header_comment=False)
            with open(no_header_path, "r", encoding="utf-8") as f:
                no_header_result = f.read()
            self.assertFalse(
                no_header_result.startswith("#"),
                "Header must not appear when with_header_comment=False",
            )
        finally:
            for path in [src_path, dst_path, no_header_path]:
                try:
                    os.remove(path)
                except Exception:
                    pass

    def test_load_with_none_optional_field(self) -> None:
        """
        Test that loading YAML with a None value for an Optional[str] field works without error.
        """
        yaml_with_none = """
name: TestName
id: 1
description: null
url: null
"""
        loaded = MockDataClass.from_yaml(yaml_with_none)
        self.assertEqual(loaded.name, "TestName")
        self.assertEqual(loaded.id, 1)
        self.assertIsNone(loaded.description)
        self.assertIsNone(loaded.url)
