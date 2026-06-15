import textwrap
import unittest
from unittest.mock import MagicMock

from docutils import utils
from indurad_ci_sphinx_extensions.custom_rst_parser import CustomRstParser


class TestCustomRstParser(unittest.TestCase):
    html_parser: CustomRstParser
    pdf_parser: CustomRstParser

    def setUp(self) -> None:
        self.document = utils.new_document(source_path="some/path.rst")
        self.html_parser = CustomRstParser()
        html_config = MagicMock()
        html_config.__getitem__.side_effect = {
            "sphinx_build_config": {
                "output_format": "html",
                "build_tags": ["indurad", "html"],
            },
        }.__getitem__
        self.html_parser._config = html_config
        self.html_parser.init()
        self.pdf_parser = CustomRstParser()
        pdf_config = MagicMock()
        pdf_config.__getitem__.side_effect = {
            "sphinx_build_config": {
                "output_format": "pdf",
                "build_tags": ["indurad", "pdf"],
            },
        }.__getitem__
        self.pdf_parser._config = pdf_config
        self.pdf_parser.init()

    def test_width(self) -> None:
        input = textwrap.dedent(
            """
            some text
            :width=100%:
            other text
            """
        )
        expected_output = textwrap.dedent(
            """
            some text
            :width:`100%`
            other text
            """
        )
        output = self.html_parser._replace(input, self.document)
        self.assertEqual(expected_output, output)

    def test_image_conversion_html(self) -> None:
        input = textwrap.dedent(
            """
            some text
            .. figure:: path/to/image.gif
            some other text
            """
        )
        expected_output = textwrap.dedent(
            """
            some text
            .. figure:: path/to/image.gif
            some other text
            """
        )
        output = self.html_parser._replace(input, self.document)
        self.assertEqual(expected_output, output)

    def test_image_conversion_pdf(self) -> None:
        input = textwrap.dedent(
            """
            some text
            .. figure:: path/to/image.gif
            some other text
            """
        )
        expected_output = textwrap.dedent(
            """
            some text
            .. figure:: path/to/image.png
            some other text
            """
        )
        output = self.pdf_parser._replace(input, self.document)
        self.assertEqual(expected_output, output)

    def test_only(self) -> None:
        input = textwrap.dedent(
            """
            some text
            .. only:: html

               this text is
               only shown
               in html builds

            .. only:: pdf

               and this text
               will only be displayed
               when a pdf is built

            some other text
            """
        )
        expected_output = textwrap.dedent(
            """
            some text






            .. only:: pdf

               and this text
               will only be displayed
               when a pdf is built

            some other text
            """
        )
        output = self.pdf_parser._replace(input, self.document)
        self.assertEqual(expected_output, output)
