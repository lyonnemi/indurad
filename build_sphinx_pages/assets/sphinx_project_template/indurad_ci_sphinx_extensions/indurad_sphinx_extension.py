import dataclasses
import hashlib
import logging
import os
import re
import subprocess
from itertools import chain
from pathlib import Path
from typing import Any, Callable

import docutils.nodes
from docutils import nodes
from docutils.parsers.rst import directives
from docutils.statemachine import StringList
from docutils.transforms import Transform
from docutils.utils import Reporter
from docutils.parsers.rst import roles

from sphinx.application import Sphinx
from sphinx.directives.patches import MathDirective
from sphinx.transforms import SphinxTransform
from sphinx.util.docutils import SphinxDirective, SphinxRole
from sphinx.writers.html import HTMLTranslator
from sphinx.writers.latex import LaTeXTranslator

from sphinxcontrib.mermaid import Mermaid  # type: ignore
from sphinxcontrib.plantuml import UmlDirective  # type: ignore

from indurad_ci_latex_template.latex_style import Colors

logger = logging.getLogger(__name__)

MERGE_REQUEST_PATTERN = re.compile(r"(?P<path>([a-zA-Z0-9.-]+/)+)(?P<project>[a-zA-Z0-9.-]+)!(?P<mr_number>[0-9]+)")
REDMINE_TICKET_PATTERN = re.compile(r"(?<!\b)#(?P<id>\d{1,7})(?!=\w)")


@dataclasses.dataclass(frozen=True, kw_only=True)
class CustomSyntaxEntry:
    """
    Replaces all sub-strings that match a given ``regex`` with a given ``replacement``.
    """

    regex: re.Pattern[str]
    """Pattern that is to be matched"""
    replacement: Callable[[re.Match[str]], Any]
    """
    Hook function
    @param match: Information about the current match
    @return: The replacement string
    """


class CustomTransform(Transform):
    """
    Supported syntax:

    md/rst::

        #1234
        101/commissioning!42
    """

    document: docutils.nodes.document
    default_priority = 799  # Run after most transforms
    # (https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx.application.Sphinx.add_transform)

    syntax_entries: list[CustomSyntaxEntry] = [
        # 101/commissioning!42
        CustomSyntaxEntry(
            regex=MERGE_REQUEST_PATTERN,
            replacement=lambda x: nodes.reference(
                text=f"{x['path']}{x['project']}!{x['mr_number']}",
                refuri=f"https://git.indurad.x/{x['path']}{x['project']}" f"/-/merge_requests/{x['mr_number']}",
            ),
        ),
        # #42
        CustomSyntaxEntry(
            regex=REDMINE_TICKET_PATTERN,
            replacement=lambda x: nodes.reference(
                text=f"#{x['id']}",
                refuri=f"https://redmine.indurad.x/issues/{x['id']}",
            ),
        ),
    ]

    def apply(self) -> None:
        """The function that is called by Sphinx.
        Search for patterns and replace with new nodes
        """
        for syntax_entry in self.syntax_entries:
            # after replacing, we need to read the current state again
            for text_node in self.document.findall(nodes.Text):
                if self._is_in_code_block(text_node):
                    continue
                self._replace_nodes(text_node, syntax_entry)

    def _is_in_code_block(self, node: nodes.Text) -> bool:
        """Check if the node is inside a code block or literal node."""
        if isinstance(node.parent, nodes.literal):
            return True
        return False

    def _replace_nodes(self, text_node: nodes.Text, syntax_entry: CustomSyntaxEntry) -> None:
        """Replaces text node with the custom replacement."""

        text = text_node.astext()
        if not (matches := list(syntax_entry.regex.finditer(text))):
            return

        new_nodes: list[nodes.Node] = []
        pos = 0
        for match in matches:
            start, end = match.span()
            no_match_content = text[pos:start]
            if no_match_content:
                new_nodes.append(nodes.Text(no_match_content))
            match_content = syntax_entry.replacement(match)
            if match_content:
                if isinstance(match_content, list):
                    new_nodes += match_content
                else:
                    new_nodes.append(match_content)
            pos = end

        no_match_content = text[pos:]
        if no_match_content:
            new_nodes.append(nodes.Text(no_match_content))
        parent = text_node.parent
        if not isinstance(parent, nodes.Element):
            raise TypeError(
                f"Parent `{parent}` of `{text_node}` is `{type(parent)}`, expected `{nodes.Element}`. "
                f"Please contact DevOps about this issue."
            )
        parent.replace(text_node, new_nodes)


class WidthRole(SphinxRole):
    """
    Supported syntax:

    rst::

        :width:`100%`
        :width=100%: (legacy)

    md::

        {width}`100%`
        [width=100%] (legacy)
    """

    def run(self) -> tuple[list[nodes.Node], list[nodes.system_message]]:
        """The function that is called by Sphinx"""
        return [
            nodes.raw(
                "",
                f"<style>.wy-nav-content {{max-width: {self.text};}}</style>",
                format="html",
            )
        ], []


class ColorNode(nodes.inline):
    """
    Class for colored text.

    This Node is used to add a new Color Node to Sphinx.
    When adding this Color Node to Sphinx (for example in the setup) you can add
    custom functions when visiting and departing elements of this Node.
    """

    pass


def visit_color_html(translator: HTMLTranslator, node: ColorNode) -> None:
    """Adds an HTML color tag to the start of the Node start

    :param translator: HTMLTranslator instance
    :param node: The Node instance
    """
    translator.body.append(translator.starttag(node, "span", CLASS=node["color_class"]))  # Set color class in html


def depart_color_html(translator: HTMLTranslator, node: ColorNode) -> None:
    """Ends the HTML Node

    :param translator: HTMLTranslator
    :param node: The Node instance
    """
    translator.body.append("</span>")  # end color class


def visit_color_latex(translator: LaTeXTranslator, node: ColorNode) -> None:
    """Adds a latex color to the start of the Node in the latex translator

    :param translator: LaTeXTranslator
    :param node: The Node instance
    """
    translator.body.append(r"\textcolor{%s}{" % node["color_class"])  # Set textcolor in latex


def depart_color_latex(translator: LaTeXTranslator, node: ColorNode) -> None:
    """Ends the node in the latex translator

    :param translator: LaTeXTranslator
    :param node: The Node instance
    """
    translator.body.append("}")  # End of textcolor command


def handle_pdfs(
    pdf_path_str: str,
    location: str,
    width: str,
    nup: str,
    scale: str,
    pages: str,
) -> list[nodes.Node]:
    """Process all PDF files that match

    :param pdf_path_str: Path to the PDF
    :param location: path and line number of the currently processed file
    :param width: width of the PDF in HTML format
    :param nup: layout of the PDF pages when shown inside PDF documents
    :param scale: size of the PDF pages when shown inside PDF documents
    :param pages: what pages should be displayed inside PDF documents
    :return: the new document nodes
    """
    document_path_str, line_no = location.split(":")
    document_path = Path(document_path_str)

    if pdf_path_str == "":
        return [nodes.Text("")]
    pdf_path_with_wildcard = document_path.parent / pdf_path_str
    matching_pdfs = list(sorted(pdf_path_with_wildcard.parent.glob(pdf_path_with_wildcard.name)))

    if not matching_pdfs:
        logger.warning(f"{location}: PDF file not found: {pdf_path_str}")

    def handle_pdf(pdf_path: Path) -> list[nodes.raw]:
        """Copy PDF to _static and return html replacement string

        @param pdf_path: path to pdf
        @return: corresponding html code that can be embedded into the document
        """
        # copy pdf to _static
        new_dir = Path("_static/pdf") / str(
            hashlib.sha256(str(pdf_path.relative_to(Path().absolute())).encode()).hexdigest()
        )
        new_dir.mkdir(parents=True, exist_ok=True)
        new_pdf_path = new_dir / pdf_path.name
        new_pdf_path.write_bytes(pdf_path.read_bytes())
        new_pdf_rel_path = os.path.relpath(new_pdf_path, document_path.parent)

        # create replacement string
        pdf_content = (subprocess.check_output(["pdftotext", new_pdf_path, "-"]).decode().replace("\n", " "),)

        return [
            nodes.raw(
                "",
                f"<style>.wy-nav-content {{max-width: {width};}}</style>"
                f'<object data="{new_pdf_rel_path}" type="application/pdf" style="min-height:70vh;width:100%">'
                f'</object><a href="{new_pdf_rel_path}">Open {pdf_path.name} in full screen</a>'
                "<!-- "
                f"{pdf_content}"
                " -->",
                format="html",
            ),
            nodes.raw(
                "",
                r"\includepdf["
                f"pages={pages},scale={scale},nup={nup}"
                r",pagecommand={\pagestyle{fancy}}]{" + str(new_pdf_path.absolute()) + r"}",
                format="latex",
            ),
        ]

    return list(chain(*[handle_pdf(pdf_path) for pdf_path in matching_pdfs]))


class PDFDirective(SphinxDirective):
    """
    Supported syntax:

    rst::

        .. pdf:: path/to/file.pdf
           :width: 100%

    md::

        ````{pdf} pdf_file.pdf
        :width: 100%
        ````
    """

    required_arguments = 1
    optional_arguments = 0
    has_content = False

    option_spec = {
        "width": directives.unchanged,
        "nup": directives.unchanged,
        "scale": directives.unchanged,
        "pages": directives.unchanged,
    }

    def run(self) -> list[nodes.Node]:
        """The function that is called by Sphinx"""
        return handle_pdfs(
            pdf_path_str=self.arguments[0] if self.arguments else "",
            location=self.get_location(),
            width=self.options.get("width", "100%"),
            nup=self.options.get("nup", "1x2"),
            scale=self.options.get("scale", "0.75"),
            pages=self.options.get("pages", "{1-}"),
        )


class PDFRole(SphinxRole):
    """
    Supported syntax:

    rst::

        :pdf:`path/to/file.pdf, width=100%`
        :pdf, width=100%:`path/to/file.pdf` (legacy)

    md::

        {pdf}`path/to/file.pdf, width=100%`
        ![pdf, width=100%](path/to/file.pdf) (legacy)
    """

    def run(self) -> tuple[list[nodes.Node], list[nodes.system_message]]:
        """The function that is called by Sphinx"""
        options = dict(option.split("=") for option in self.text.split(", ")[1:])
        return (
            handle_pdfs(
                pdf_path_str=self.text.split(", ")[0],
                location=self.get_location(),
                width=options["width"] if "width" in options else "100%",
                nup=options["nup"] if "nup" in options else "1x2",
                scale=options["scale"] if "scale" in options else "0.75",
                pages=options["pages"] if "pages" in options else "{1-}",
            ),
            [],
        )


class HyphenationRole(SphinxRole):
    """
    Supported syntax:

    rst::

        :hyphenation:`foo-bar`

    md::

        {hyphenation}`foo-bar`
        ![hyphenation](foo-bar) (legacy)
    """

    def run(self) -> tuple[list[nodes.Node], list[nodes.system_message]]:
        """The function that is called by Sphinx"""
        return [nodes.raw("", f"\\hyphenation{{{self.text}}}", format="latex")], []


class _DummyState:
    """Mimics the bare minimum functionality of a State object.
    We use this to call Directives similarly like Sphinx would do it.
    This may break with a future update of either Sphinx or the used directives.
    In that case, we need to implement more functionality or change the implementation.
    It is to be noted, that THIS IS NOT THE INTENDED WAY to call these directives.
    If something breaks, HERE MAY LIKELY BE THE PLACE TO LOOK FOR THE ISSUE.
    The same applies for _DummyStateMachine.
    """

    document: nodes.document
    """Property of the State. The current document. Includes the current parsing state, and much more."""

    def __init__(self, document: nodes.document) -> None:
        self.document = document


class _DummyStateMachine:
    """Mimics the bare minimum functionality of a StateMachine object
    For information on risks and side-effects please read the docstring
    for _DummyState and ask your doctor or pharmacist.
    """

    document: nodes.document
    """Property of the StateMachine. The current document. Includes the current parsing state, and much more."""
    reporter: Reporter
    """Property of the StateMachine. Used for reporting incidents."""
    line: int | None
    """Property of the StateMachine. The current line number."""
    source: str | None
    """Property of the _DummyStateMachine. The path to the current document."""

    def __init__(self, document: nodes.document, node: nodes.Node) -> None:
        self.document = document
        self.reporter = document.reporter
        self.line = node.line
        self.source = node.source

    def get_source_and_line(self, lineno: int) -> tuple[str | None, int | None]:
        """Return the source document path and current line number
        The original implementation does more advanced things,
        but we just return what is given in the current node.
        """
        return self.source, self.line


class CodeBlockTransform(SphinxTransform):
    """Replaces a code block of type mermaid, plantuml or math
    The goal is to support code-block syntax in Markdown documents, like GitLab does.
    MyST would usually only support this syntax::

        ```{mermaid}
        some code
        ```

    With this Transform, we support::

        ```mermaid
        some code
        ```
    """

    default_priority = 500  # selected by lucky dice roll

    def mermaid(self, block: nodes.literal_block) -> list[nodes.Node]:
        """Defines the ``mermaid`` lexer"""
        directive = Mermaid(
            name="mermaid",
            arguments=[],
            options={},
            content=block.astext().split("\n"),
            lineno=block.line or 0,
            content_offset=0,
            block_text=block.astext(),
            state=_DummyState(self.document),
            state_machine=_DummyStateMachine(self.document, block),
        )

        new_nodes: list[nodes.Node] = directive.run()
        return new_nodes

    def plantuml(self, block: nodes.literal_block) -> list[nodes.Node]:
        """Defines the ``plantuml`` lexer"""
        directive = UmlDirective(
            name="uml",
            arguments=[],
            options={},
            content=block.astext().split("\n"),
            lineno=block.line or 0,
            content_offset=0,
            block_text=block.astext(),
            state=_DummyState(self.document),
            state_machine=_DummyStateMachine(self.document, block),
        )

        new_nodes: list[nodes.Node] = directive.run()
        return new_nodes

    def math(self, block: nodes.literal_block) -> list[nodes.Node]:
        """Defines the ``math`` lexer"""
        directive = MathDirective(
            name="math",
            arguments=[],
            options={},
            content=StringList(block.astext().split("\n")),
            lineno=block.line or 0,
            content_offset=0,
            block_text=block.astext(),
            state=_DummyState(self.document),  # type: ignore
            state_machine=_DummyStateMachine(self.document, block),  # type: ignore
        )

        new_nodes = directive.run()
        return new_nodes

    def apply(self) -> None:
        """The function that is called by Sphinx
        Iterate all code blocks in document and replace blocks that have specific languages
        with the result of their corresponding directive
        """
        for block in self.document.traverse(nodes.literal_block):
            match block.get("language"):
                case "mermaid":
                    block.parent.replace(block, self.mermaid(block))
                case "plantuml":
                    block.parent.replace(block, self.plantuml(block))
                case "math":
                    block.parent.replace(block, self.math(block))


def color_role(
    class_name: str,
) -> Callable[
    [str, str, str, int, Any, dict[str, Any], list[str]],
    tuple[list[nodes.Node], list[nodes.system_message]],
]:
    """
    Factory-function, for role function
    """

    def role_func(
        name: str,
        rawtext: str,
        text: str,
        lineno: int,
        inliner: Any,
        options: dict[str, Any] = {},
        content: list[str] = [],
    ) -> tuple[list[nodes.Node], list[nodes.system_message]]:
        """
        Adds the correct color to the role
        """
        node = ColorNode(text, text)
        node["color_class"] = class_name
        return [node], []

    return role_func


def bold_color_role(
    class_name: str,
) -> Callable[
    [str, str, str, int, Any, dict[str, Any], list[str]],
    tuple[list[nodes.Node], list[nodes.system_message]],
]:
    """
    Factory-function, for role function
    """

    def role_func(
        name: str,
        rawtext: str,
        text: str,
        lineno: int,
        inliner: Any,
        options: dict[str, Any] = {},
        content: list[str] = [],
    ) -> tuple[list[nodes.Node], list[nodes.system_message]]:
        """
        Adds the correct bold color to the role
        """
        color_node = ColorNode(text, text)
        color_node["color_class"] = class_name

        strong_node = nodes.strong()
        strong_node += color_node
        return [strong_node], []

    return role_func


def setup(app: Sphinx) -> dict[str, str | bool]:
    """The function that is called by Sphinx"""
    app.add_transform(CustomTransform)
    app.add_role("width", WidthRole())
    app.add_role("pdf", PDFRole())
    app.add_role("hyphenation", HyphenationRole())
    app.add_directive("pdf", PDFDirective)
    app.add_transform(CodeBlockTransform)
    app.add_node(  # Add custom ColorNode to Sphinx and add node visitor functions
        ColorNode,
        html=(  # Add visit and depart functions for html
            visit_color_html,
            depart_color_html,
        ),
        latex=(  # Add visit and depart functions for latex
            visit_color_latex,
            depart_color_latex,
        ),
    )

    for color in Colors:
        roles.register_local_role(color.name, color_role(color.name))  # type: ignore[arg-type]
        roles.register_local_role(color.name + "-bold", bold_color_role(color.name))  # type: ignore[arg-type]

    return {
        "version": "1.0",
        "parallel_read_safe": True,
    }
