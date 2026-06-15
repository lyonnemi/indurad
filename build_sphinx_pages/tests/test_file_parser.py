import pathlib
import unittest
from indurad_ci.build_sphinx_pages.private.file_parser import FileParser
from indurad_ci.build_sphinx_pages.private.sphinx_error import BuildSphinxPagesError

_EXAMPLE_FS = pathlib.Path("indurad_ci/build_sphinx_pages/tests/example_tags")


class TestFileParser(unittest.TestCase):
    def test_no_header(self) -> None:
        file_parser = FileParser(("indurad",))
        match_result = file_parser.analyze_file(_EXAMPLE_FS / "no_header.md")
        self.assertTrue(match_result.matches_build_tags)

        file_parser = FileParser(("customer", "indurad"))
        file_detils = file_parser.analyze_file(_EXAMPLE_FS / "no_header.md")
        self.assertTrue(file_detils.matches_build_tags)

        file_parser = FileParser(("customer",))
        file_detils = file_parser.analyze_file(_EXAMPLE_FS / "no_header.md")
        self.assertFalse(file_detils.matches_build_tags)

        self.assertEqual("indurad", file_detils.build_condition)

    def test_single_tag(self) -> None:
        file_parser = FileParser(("customer",))
        file_detils = file_parser.analyze_file(_EXAMPLE_FS / "single_tag.md")
        self.assertTrue(file_detils.matches_build_tags)

        file_parser = FileParser(("customer", "indurad"))
        file_detils = file_parser.analyze_file(_EXAMPLE_FS / "single_tag.md")
        self.assertTrue(file_detils.matches_build_tags)

        file_parser = FileParser(("indurad",))
        file_detils = file_parser.analyze_file(_EXAMPLE_FS / "single_tag.md")
        self.assertFalse(file_detils.matches_build_tags)

        self.assertEqual("customer", file_detils.build_condition)

    def test_multiple_tags(self) -> None:
        file_parser = FileParser(("indurad",))
        file_detils = file_parser.analyze_file(_EXAMPLE_FS / "multiple_tags.md")
        self.assertFalse(file_detils.matches_build_tags)

        file_parser = FileParser(("developer",))
        file_detils = file_parser.analyze_file(_EXAMPLE_FS / "multiple_tags.md")
        self.assertTrue(file_detils.matches_build_tags)

        file_parser = FileParser(("indurad", "commissioning"))
        file_detils = file_parser.analyze_file(_EXAMPLE_FS / "multiple_tags.md")
        self.assertFalse(file_detils.matches_build_tags)

        file_parser = FileParser(("commissioning", "customer"))
        file_detils = file_parser.analyze_file(_EXAMPLE_FS / "multiple_tags.md")
        self.assertTrue(file_detils.matches_build_tags)

        file_parser = FileParser(("customer",))
        file_detils = file_parser.analyze_file(_EXAMPLE_FS / "multiple_tags.md")
        self.assertFalse(file_detils.matches_build_tags)

        self.assertEqual(
            "(indurad or commissioning) and customer or developer",
            file_detils.build_condition,
        )

    def test_wrong_tags(self) -> None:
        file_parser = FileParser(("indurad",))
        with self.assertRaises(BuildSphinxPagesError):
            file_parser.analyze_file(_EXAMPLE_FS / "wrong_tags.md")

    def test_invalid_header_format(self) -> None:
        file_parser = FileParser(("indurad",))
        with self.assertRaises(BuildSphinxPagesError):
            file_parser.analyze_file(_EXAMPLE_FS / "invalid_header_format.md"),
