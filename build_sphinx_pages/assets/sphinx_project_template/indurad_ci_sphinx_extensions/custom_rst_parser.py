import re
from sphinx.parsers import RSTParser
from typing import Any
from docutils.statemachine import StringList
from docutils import nodes
from sphinx.application import Sphinx
from sphinx.util.tags import Tags
from indurad_ci_sphinx_extensions.util import (
    CustomSyntaxEntry,
    get_document_source,
    replace_in_non_code,
    MatchInfo,
)

__version__ = "1.0.0"


class CustomRstParser(RSTParser):
    """Custom extension of the RSTParser
    Ref: https://www.sphinx-doc.org/en/master/extdev/parserapi.html

    Parses custom syntax/features in .rst files and changes it to a format compatible with Sphinx.
    Supported custom features are:
    * GitLab MergeRequest "fully-qualified" references: master/monolith!1234
    * Redmine ticket references: #1234
    """

    _output_format: str
    """The document type that is built, e.g. html or pdf"""
    _replacements: list[CustomSyntaxEntry]
    """List of patterns that are to be replaced, and the corresponding method that is executed for each match"""
    _preformatted_section_regex = re.compile(
        r"("
        + r")|(".join(
            [
                r"\.\. code(-block)?::.*?\n(( *|( {3,4}[^\n]*))\n)+",  # multiline code block
                r"\.\. raw:: html\n(( *|( {3,4}[^\n]*))\n)+",  # multiline html block
                r"``[^\n]*``",  # inline code
            ]
        )
        + r")",
        re.DOTALL,
    )
    """matches all types of code blocks"""
    _custom_header_regex = re.compile(r".*\n:custom_header: (?P<header_length>.*?)\n", re.DOTALL)
    """matches specification of custom header length"""
    _tags_eval: Tags
    """used to determine whether an only section matches the build tags"""

    def init(self) -> None:
        """
        Initialize the class. We can't do this in `__init__`
        because we need the initialized instance of `Sphinx` to read the config.
        """
        sphinx_build_config = self._config["sphinx_build_config"]
        self._output_format = sphinx_build_config["output_format"]
        self._tags_eval = Tags(sphinx_build_config["build_tags"])

        self._replacements = [
            entry
            for entry in [
                # .. only:: indurad
                # Replace `only` blocks with empty lines if the tags don't match the build tags,
                # otherwise keep the block as it is.
                CustomSyntaxEntry(
                    regex=re.compile(r"\.\. only:: (?P<tags>.+?)\n(?P<content>(( *|( {3,4}[^\n]*))\n)+)"),
                    replacement=lambda x: (
                        f".. only:: {x.match['tags']}\n{x.match['content']}"
                        if self._tags_eval.eval_condition(x.match["tags"])
                        else "\n" * (len(x.match["content"].split("\n")))
                    ),
                ),
                # :width=100%:
                CustomSyntaxEntry(
                    regex=re.compile(r":width=(.*):"),
                    replacement=lambda x: f":width:`{x.match[1]}`",
                ),
                # :pdf, width=100%:`path/to/file.pdf`
                CustomSyntaxEntry(
                    regex=re.compile(r":pdf(?P<options>.*)?:`(?P<pdf_path>.*)`"),
                    replacement=lambda x: f":pdf:`{x.match['pdf_path']}{x.match['options']}`",
                ),
                # .. include: path/to/file.rst
                CustomSyntaxEntry(
                    regex=re.compile(r"\.\. include:: (\n {3,4})?(?P<file>\S*)"),
                    replacement=self._remove_custom_header_from_included_file,
                ),
                # .. figure:: images/2024-02-13_iLevel2d_architecture.svg
                (
                    CustomSyntaxEntry(
                        regex=re.compile(r"\.\. figure:: (?P<filename>.*)\.(gif|svg)"),
                        replacement=lambda x: f".. figure:: {x.match['filename']}.png",
                    )
                    if self._output_format == "pdf"
                    else None
                ),
            ]
            if entry is not None
        ]

    def parse(self, input_string: str | StringList, document: nodes.document) -> None:
        """Parses custom syntax/features in source text and calls RSTParser.parse(...) afterwards.

        :param input_string: The source string to parse
        :param document: The root docutils node to add AST elements to
        Ref: https://www.sphinx-doc.org/en/master/extdev/parserapi.html
        """
        assert get_document_source(document).suffix == ".rst"
        self._env = document.settings.env
        self._config = document.settings.env.config
        self.init()
        super().parse(self._replace(str(input_string), document), document)

    def _replace(self, input_string: str, document: nodes.document) -> str:
        """
        Do the actual replacing
        @param input_string: The source string to parse
        @param document: The root docutils node
        @return: input string with replacements
        """
        return replace_in_non_code(
            input_string,
            self._replacements,
            self._preformatted_section_regex,
            document,
            self._output_format,
        )

    def _remove_custom_header_from_included_file(self, match_info: MatchInfo) -> str:
        """
        Removes the custom header from each included file.
        This is necessary because the Sphinx parser does not use the `parse` function for included files.
        """
        included_file_path_str = match_info.match["file"]
        included_file_path = match_info.document_path.parent / included_file_path_str
        try:
            included_file_text = included_file_path.read_text()
            match = self._custom_header_regex.match(included_file_text)
            if match:
                included_file_path.write_text(
                    "\n".join(included_file_path.read_text().split("\n")[int(match["header_length"]) :])
                )
            return f".. include:: {included_file_path_str}"
        except FileNotFoundError:
            match_info.document.reporter.error(
                f"Included file not found: {included_file_path}",
                line=match_info.line_number,
            )
            return ""


def setup(app: "Sphinx") -> dict[str, Any]:
    app.add_source_parser(CustomRstParser, True)
    app.add_config_value(name="sphinx_build_config", default={}, rebuild="env")

    return {
        "version": "1.0.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
