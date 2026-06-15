import re

from docutils import nodes
from myst_parser.parsers.sphinx_ import MystParser
from typing import Any
from sphinx.application import Sphinx
from sphinx.util.tags import Tags

from indurad_ci_sphinx_extensions.util import (
    CustomSyntaxEntry,
    get_document_source,
    replace_in_non_code,
    embed_inline,
    MatchInfo,
)

__version__ = "1.0.0"


def setup_sphinx(app: Sphinx, load_parser: bool = False) -> None:
    """Initialize all settings and transforms in Sphinx.
    Ref: https://github.com/executablebooks/MyST-Parser/blob/master/myst_parser/sphinx_ext/main.py#L16
    """
    # we do this separately to setup,
    # so that it can be called by external packages like myst_nb
    from myst_parser.config.main import MdParserConfig
    from myst_parser.sphinx_ext.directives import (
        FigureMarkdown,
        SubstitutionReferenceRole,
    )
    from myst_parser.sphinx_ext.mathjax import override_mathjax
    from myst_parser.sphinx_ext.myst_refs import MystReferenceResolver

    if load_parser:
        app.add_source_suffix(".md", "markdown")
        # replaced MystParser with indurad CustomMdParser
        app.add_source_parser(CustomMdParser)

    app.add_role("sub-ref", SubstitutionReferenceRole())
    app.add_directive("figure-md", FigureMarkdown)

    app.add_post_transform(MystReferenceResolver)

    for name, default, field in MdParserConfig().as_triple():
        if not field.metadata.get("docutils_only", False):
            # TODO add types?
            app.add_config_value(f"myst_{name}", default, "env", types=Any)  # type: ignore

    app.connect("builder-inited", create_myst_config)
    app.connect("builder-inited", override_mathjax)


def create_myst_config(app: Sphinx) -> None:
    """Create the myst config object and add it to the sphinx environment.
    Ref: https://github.com/executablebooks/MyST-Parser/blob/master/myst_parser/sphinx_ext/main.py#L65
    """
    from sphinx.util import logging

    # Ignore type checkers because the attribute is dynamically assigned
    from sphinx.util.console import bold  # type: ignore[attr-defined]

    from myst_parser import __version__
    from myst_parser.config.main import MdParserConfig

    logger = logging.getLogger(__name__)

    values = {
        name: app.config[f"myst_{name}"]
        for name, _, field in MdParserConfig().as_triple()
        if not field.metadata.get("docutils_only", False)
    }

    # ignore that `app.env` doesn't have an attribute `myst_config`
    try:
        app.env.myst_config = MdParserConfig(**values)  # type: ignore
        logger.info(bold("myst v%s:") + " %s", __version__, app.env.myst_config)  # type: ignore
    except (TypeError, ValueError) as error:
        logger.error("myst configuration invalid: %s", error.args[0])
        app.env.myst_config = MdParserConfig()  # type: ignore


class CustomMdParser(MystParser):
    """Custom extension of the MystParser
    Ref: https://github.com/executablebooks/MyST-Parser/blob/master/myst_parser/parsers/sphinx_.py

    Parses custom syntax/features in .md files and changes it to a format compatible with MyST.
    Supported custom features are:
    * GitLab Markdown toctrees: [[_TOC_]]
    * GitLab MergeRequest "fully-qualified" references: master/monolith!1234
    * mermaid diagrams
    * (plant-)uml diagrams
    * md/latex math blocks
    * Redmine ticket references: #1234
    * Build system related issues like hidden MyST toctree directives
    """

    _output_format: str
    _replacements: list[CustomSyntaxEntry]
    """List of patterns that are to be replaced, and the corresponding method that is executed for each match"""
    _preformatted_section_regex = re.compile(
        r"("
        + r")|(".join(
            [
                r"(?<!`)``(`+)[^`].*?``\2",  # ``` ``` block
                r"(?<!~)~~(~+)[^~].*?~~\4",  # ~~~ ~~~ block
                r"<pre>.*?</pre>",  # <pre></pre> block
                r"<code>.*?</code>",  # <code></code> block
                r"`[^`\n]+?`",  # `inline code`
            ]
        )
        + r")",
        re.DOTALL,
    )
    """matches all types of code blocks"""
    _custom_header_regex = re.compile(r"\n\n\[//]: <> \(end_of_header\)\n\n", re.DOTALL)
    """matches header and body with custom header delimiter `.. end_of_header`"""
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
                # ```{only} indurad
                # Replace `only` blocks with empty lines if the tags don't match the build tags,
                # otherwise keep the block as it is.
                CustomSyntaxEntry(
                    regex=re.compile(
                        r"(?<!`)``(?P<border>`+)\{only} (?P<tags>.*)\n(?P<content>(.*\n)*?)``(?P=border)"
                    ),
                    replacement=lambda x: (
                        f'``{x.match["border"]}{{only}} {x.match["tags"]}\n'
                        f'{x.match["content"]}``{x.match["border"]}'
                        if self._tags_eval.eval_condition(x.match["tags"])
                        else "\n" * (len(x.match["content"].split("\n")))
                    ),
                ),
                # <html_tag>
                (
                    CustomSyntaxEntry(
                        regex=re.compile(r"(?<!\[//]: )<(?P<tag_content>.*?)>"),
                        replacement=_parse_html,
                    )
                    if self._output_format == "pdf"
                    else None
                ),
                # [_TOC_]
                CustomSyntaxEntry(
                    regex=re.compile(r"\n\[\[_TOC_]]\n"),
                    replacement=lambda x: "\n```{contents} Contents\n```",
                ),
                # [width=100%]
                CustomSyntaxEntry(
                    regex=re.compile(r"\[width=(.*)]"),
                    replacement=lambda x: f"{{width}}`{x.match[1]}`",
                ),
                # ```toctree
                CustomSyntaxEntry(
                    regex=re.compile(r"<!--(?P<toctree>\n*```{toctree}[\s\S]*```[\n]*)-->"),
                    replacement=lambda x: x.match["toctree"],
                ),
                # ![pdf, width=100%](path/to/file.pdf)
                CustomSyntaxEntry(
                    regex=re.compile(r"!\[pdf(?P<options>.*)?]\((?P<pdf_path>.*)\)"),
                    replacement=lambda x: f"{{pdf}}`{x.match['pdf_path']}{x.match['options']}`",
                ),
                # ![my_picture](images/2024-02-13_iLevel2d_architecture.svg)
                (
                    CustomSyntaxEntry(
                        regex=re.compile(r"!\[(?P<image_description>.*)]\((?P<filename>.*)\.(gif|svg)\)"),
                        replacement=(lambda x: f"![{x.match['image_description']}]({x.match['filename']}.png)"),
                    )
                    if self._output_format == "pdf"
                    else None
                ),
                # ![hyphenation](foo-bar)
                CustomSyntaxEntry(
                    regex=re.compile(r"!\[hyphenation]\((?P<word>.*?)\)"),
                    replacement=lambda x: f"{{hyphenation}}`{x.match['word']}`",
                ),
            ]
            if entry is not None
        ]

    def parse(self, input_string: str, document: nodes.document) -> None:
        """Parses custom syntax/features in source text and calls MystParser.parse(...) afterwards.

        :param input_string: The source string to parse
        :param document: The root docutils node to add AST elements to
        Ref: https://github.com/executablebooks/MyST-Parser/blob/master/myst_parser/parsers/sphinx_.py#L50
        """
        assert get_document_source(document).suffix == ".md"
        self._env = document.settings.env
        self._config = document.settings.env.config
        self.init()
        super().parse(self._replace(input_string, document), document)

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


def _parse_html(match_info: MatchInfo) -> str:
    """
    Replaces HTML code with LaTeX code
    """
    match tag_content := match_info.match["tag_content"]:
        case "br":
            return embed_inline(r"\leavevmode\newline ", ".md", "pdf")
        case "br/":
            return embed_inline(r"\leavevmode\newline ", ".md", "pdf")
        case "br /":
            return embed_inline(r"\leavevmode\newline ", ".md", "pdf")
        case "dl":
            return ""
        case "/dl":
            return ""
        case "dt":
            return embed_inline(r"\textbf{", ".md", "pdf")
        case "/dt":
            return embed_inline(r"}\leavevmode\newline ", ".md", "pdf")
        case "dd":
            return embed_inline(r"\\\noindent\hspace*{1cm}", ".md", "pdf")
        case "/dd":
            return embed_inline(r"\leavevmode\newline ", ".md", "pdf")
        case "em":
            return embed_inline(r"\textit{", ".md", "pdf")
        case "/em":
            return embed_inline(r"}", ".md", "pdf")
        case "b":
            return embed_inline(r"\textbf{", ".md", "pdf")
        case "/b":
            return embed_inline(r"}", ".md", "pdf")
        case "strong":
            return embed_inline(r"\textbf{", ".md", "pdf")
        case "/strong":
            return embed_inline(r"}", ".md", "pdf")
        case "p":
            return embed_inline(r"\leavevmode\newline\newline ", ".md", "pdf")
        case "/p":
            return embed_inline(r"\leavevmode\newline\newline ", ".md", "pdf")
        case "details":
            return ""
        case "summary":
            return ""
        case "/summary":
            return embed_inline(r"{\tiny ", ".md", "pdf")
        case "/details":
            return embed_inline(r"}", ".md", "pdf")
        case "pre":
            return "<pre>"
        case "code":
            return "<code>"
        case c if any(c.startswith(f"{prot}://") for prot in ("http", "https", "ftp", "smb", "irc")):
            return embed_inline(r"\url{" + c + r"}", ".md", "pdf")
        case "sub":
            return embed_inline(r"\textsubscript{", ".md", "pdf")
        case "/sub":
            return embed_inline(r"}", ".md", "pdf")
        case "sup":
            return embed_inline(r"\textsuperscript{", ".md", "pdf")
        case "/sup":
            return embed_inline(r"}", ".md", "pdf")
        case "ul":
            return r""
        case "/ul":
            return embed_inline(r"\newline", ".md", "pdf")
        case "li":
            return embed_inline(r"\leavevmode\newline \textbullet ", ".md", "pdf")
        case "/li":
            return r""

    match_info.document.reporter.warning(f"HTML tag <{tag_content}> could not be parsed!", line=match_info.line_number)
    return f"<{tag_content}>"


def setup(app: Sphinx) -> dict[str, str | bool]:
    """Initialize the Sphinx extension.
    Ref: https://github.com/executablebooks/MyST-Parser/blob/master/myst_parser/__init__.py
    """
    setup_sphinx(app, load_parser=True)
    return {"version": "1.0.0", "parallel_read_safe": True}
