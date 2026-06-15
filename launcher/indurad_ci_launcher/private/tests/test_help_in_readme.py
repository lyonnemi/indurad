import os
import pathlib
import unittest

from indurad_ci_launcher.private.launcher import _make_argument_parser


_TESTS_PATH = pathlib.Path(__file__).parent
_README_PATH = _TESTS_PATH.parent.parent.parent / "README.md"


class TestHelpInReadme(unittest.TestCase):
    def test_readme_contains_help_text(self) -> None:
        if not _README_PATH.is_file():
            self.skipTest(f"{_README_PATH} does not exist")

        readme_text = _README_PATH.read_text(encoding="utf-8")

        # ensure deterministic output as argparse formats its help text
        # according to the current terminal dimensions
        os.environ["COLUMNS"] = "80"
        os.environ["LINES"] = "24"

        help_text = _make_argument_parser().format_help()

        self.assertIn(help_text, readme_text)
