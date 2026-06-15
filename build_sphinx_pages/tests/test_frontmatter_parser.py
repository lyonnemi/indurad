#!/usr/bin/env python3
import unittest
from textwrap import dedent
from indurad_ci.build_sphinx_pages.private.frontmatter_parser import (
    parse,
)


class TestFrontmatterParser(unittest.TestCase):
    def test_parse_yaml1(self) -> None:
        text = dedent(
            """\
            ---
            comment: This is the frontmatter header
            value: 1
            ---

            Text text.
            ---
            """
        )

        result = parse(text)

        self.assertIsNotNone(result)
        assert result is not None

        self.assertEqual(result.header["comment"], "This is the frontmatter header")
        self.assertEqual(result.header["value"], 1)
        self.assertEqual(result.body, "\nText text.\n---\n")

    def test_parse_yaml2(self) -> None:
        text = dedent(
            """\
            ---
            comment: This is the frontmatter header
            value: 2
            ...

            Text text.
            ---
            ...
            """
        )

        result = parse(text)

        self.assertIsNotNone(result)
        assert result is not None

        self.assertEqual(result.header["comment"], "This is the frontmatter header")
        self.assertEqual(result.header["value"], 2)
        self.assertEqual(result.body, "\nText text.\n---\n...\n")

    def test_parse_no_header(self) -> None:
        text = dedent(
            """\
            ---
            Text text.
            """
        )

        result = parse(text).header

        self.assertTrue(result == {})


if __name__ == "__main__":
    unittest.main()
