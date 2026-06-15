import textwrap
import unittest
from unittest.mock import MagicMock

from docutils import utils
from indurad_ci_sphinx_extensions.custom_md_parser import CustomMdParser


class TestCustomMdParser(unittest.TestCase):
    html_parser: CustomMdParser
    pdf_parser: CustomMdParser

    def setUp(self) -> None:
        self.document = utils.new_document(source_path="some/path.md")
        self.html_parser = CustomMdParser()
        html_config = MagicMock()
        html_config.__getitem__.side_effect = {
            "sphinx_build_config": {
                "output_format": "html",
                "build_tags": ["indurad", "html"],
            },
        }.__getitem__
        self.html_parser._config = html_config
        self.html_parser.init()
        self.pdf_parser = CustomMdParser()
        pdf_config = MagicMock()
        pdf_config.__getitem__.side_effect = {
            "sphinx_build_config": {
                "output_format": "pdf",
                "build_tags": ["indurad", "pdf"],
            },
        }.__getitem__
        self.pdf_parser._config = pdf_config
        self.pdf_parser.init()

    def test_gitlab_toctree(self) -> None:
        input: str = "\n[[_TOC_]]\n"
        output: str = self.html_parser._replace(input, self.document)
        self.assertEqual("\n```{contents} Contents\n```", output)

    def test_gitlab_toctree_code_example(self) -> None:
        input: str = "this is an example of a toctree `[[_TOC_]]`, and this is not replaced by the parser"
        output: str = self.html_parser._replace(input, self.document)
        self.assertEqual(input, output)

    def test_hidden_toctree(self) -> None:
        input: str = textwrap.dedent(
            """\
            <!--
            ```{toctree}
            ---
            hidden: true
            titlesonly: true
            ---
            documentation_migration_guide
            style-templates
            ```
            -->
            """
        )
        expected_output: str = textwrap.dedent(
            """\

            ```{toctree}
            ---
            hidden: true
            titlesonly: true
            ---
            documentation_migration_guide
            style-templates
            ```

            """
        )
        output: str = self.html_parser._replace(input, self.document)
        self.assertEqual(expected_output, output)

    def test_width(self) -> None:
        input = textwrap.dedent(
            """
            some text
            [width=100%]
            some other text
            """
        )
        expected_output = textwrap.dedent(
            """
            some text
            {width}`100%`
            some other text
            """
        )
        output = self.html_parser._replace(input, self.document)
        self.assertEqual(expected_output, output)

    def test_hyphenation(self) -> None:
        input = textwrap.dedent(
            """
            some text
            ![hyphenation](foo-bar)
            some other text
            """
        )
        expected_output = textwrap.dedent(
            r"""
            some text
            {hyphenation}`foo-bar`
            some other text
            """
        )
        output = self.html_parser._replace(input, self.document)
        self.assertEqual(expected_output, output)

    def test_image_conversion_html(self) -> None:
        input = textwrap.dedent(
            """
            some text
            [my_image](path/to/image.gif)
            some other text
            """
        )
        expected_output = textwrap.dedent(
            """
            some text
            [my_image](path/to/image.gif)
            some other text
            """
        )
        output = self.html_parser._replace(input, self.document)
        self.assertEqual(expected_output, output)

    def test_image_conversion_pdf(self) -> None:
        input = textwrap.dedent(
            """
            some text
            ![my_image](path/to/image.gif)
            some other text
            """
        )
        expected_output = textwrap.dedent(
            """
            some text
            ![my_image](path/to/image.png)
            some other text
            """
        )
        output = self.pdf_parser._replace(input, self.document)
        self.assertEqual(expected_output, output)

    def test_html_econversion_html(self) -> None:
        input = textwrap.dedent(
            """
            <br>
            <br/>
            <dl>
                <dt>Definition Term</dt>
                <dd>This is the definition.</dd>
            </dl>
            <b>This text is bold.</b>
            <pre><code>This is a code block.</code></pre>
            <code>This is inline code.</code>
            <sub>This text is subscripted.</sub>
            <sup>This text is superscripted.</sup>
            <smb://my_url.com>
            """
        )
        expected_output = textwrap.dedent(
            """
            <br>
            <br/>
            <dl>
                <dt>Definition Term</dt>
                <dd>This is the definition.</dd>
            </dl>
            <b>This text is bold.</b>
            <pre><code>This is a code block.</code></pre>
            <code>This is inline code.</code>
            <sub>This text is subscripted.</sub>
            <sup>This text is superscripted.</sup>
            <smb://my_url.com>
            """
        )
        output = self.html_parser._replace(input, self.document)
        self.assertEqual(expected_output, output)

    def test_html_conversion_pdf(self) -> None:
        input = textwrap.dedent(
            """
            <br>
            <br/>
            <dl>
                <dt>Definition Term</dt>
                <dd>This is the definition.</dd>
            </dl>
            <b>This text is bold.</b>
            <pre><code>This is a code block.</code></pre>
            <code>This is inline code.</code>
            <sub>This text is subscripted.</sub>
            <sup>This text is superscripted.</sup>
            <smb://my_url.com>
            """
        )
        expected_output = textwrap.dedent(
            r"""
            {raw-latex}`\leavevmode\newline `
            {raw-latex}`\leavevmode\newline `

                {raw-latex}`\textbf{`Definition Term{raw-latex}`}\leavevmode\newline `
                {raw-latex}`\\\noindent\hspace*{1cm}`This is the definition.{raw-latex}`\leavevmode\newline `

            {raw-latex}`\textbf{`This text is bold.{raw-latex}`}`
            <pre><code>This is a code block.</code></pre>
            <code>This is inline code.</code>
            {raw-latex}`\textsubscript{`This text is subscripted.{raw-latex}`}`
            {raw-latex}`\textsuperscript{`This text is superscripted.{raw-latex}`}`
            {raw-latex}`\url{smb://my_url.com}`
            """
        )
        output = self.pdf_parser._replace(input, self.document)
        self.assertEqual(expected_output, output)

    def test_only(self) -> None:
        input = textwrap.dedent(
            """
            some text
            ```{only} html
            this text is
            only shown
            in html builds
            ```
            ```{only} pdf
            and this text
            will only be displayed
            when a pdf is built
            ```
            some other text
            """
        )
        expected_output = textwrap.dedent(
            """
            some text





            ```{only} pdf
            and this text
            will only be displayed
            when a pdf is built
            ```
            some other text
            """
        )
        output = self.pdf_parser._replace(input, self.document)
        self.assertEqual(expected_output, output)
