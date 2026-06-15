import dataclasses
import pathlib
import re
from typing import Callable

from docutils import nodes


@dataclasses.dataclass(frozen=True, kw_only=True)
class MatchInfo:
    match: re.Match[str]
    """
    The regex match
    """
    line_number: int
    """
    Line number in the document
    """
    document: nodes.document
    """
    The current nodes document
    """
    document_path: pathlib.Path
    """
    Path to the current document
    """
    output_format: str
    """
    Output format of the build (e.g. html, pdf, ...)
    """


@dataclasses.dataclass(frozen=True, kw_only=True)
class CustomSyntaxEntry:
    """Utilized by CustomMdParser and CustomRstParser to
    replace parts of a strings that match with "regex" with "replacement".
    """

    regex: re.Pattern[str]
    """Pattern that is to be matched"""
    replacement: Callable[[MatchInfo], str]
    """
    Hook function
    @param match_info: Information about the current match
    @return: The replacement string
    """


@dataclasses.dataclass(frozen=True)
class Line:
    number: int
    start_position: int


def get_document_source(doc: nodes.document) -> pathlib.Path:
    """Returns the source of the document object."""
    return pathlib.Path(doc.attributes["source"])


def embed_inline(content: str, document_type: str, output_format: str) -> str:
    """
    Embeds a single line of code into a document.
    @param content: The code that is to be embedded
    @param document_type: e.g. ".md", ".rst", ...
    @param output_format: e.g. "html", "pdf", ...
    @return: The html so that it can be used inside the document
    """
    if content == "":
        return ""
    output_format = "latex" if output_format == "pdf" else output_format
    match document_type:
        case ".rst":
            return f":raw-{output_format}:`{content}`"
        case ".md":
            return f"{{raw-{output_format}}}`{content}`"
        case _:
            raise NotImplementedError(f"Support for {document_type} is not implemented yet!")


def replace_in_non_code(
    input_string: str,
    syntax_entries: list[CustomSyntaxEntry],
    preformatted_section_regex: re.Pattern[str],
    document: nodes.document,
    output_format: str,
) -> str:
    """
    Replace all occurrences of `replacements` in input_string,
    but ignore everything that matches `preformatted_section_regex`
    @param input_string: Input text where matches are replaced
    @param syntax_entries: Syntax entries containing regex and replacement
    @param preformatted_section_regex: Pattern that matches sections that are not to be replaced, like <pre></pre>.
    @param document: Current nodes document
    @param output_format: The type of document that is built (e.g. html, pdf, ...)
    @return: Text with replaced matches
    """
    newlines = [
        Line(*x)
        for x in enumerate(
            [0] + [x.end() + 1 for x in _newline_pattern.finditer(input_string)],
            start=1,
        )
    ]
    for replacement in syntax_entries:
        # we need to do this after each replacement because we might insert a different number of characters
        preformatted_sections = [
            # We don't want to blacklist the position where ```mermaid etc. matches
            # Therefore we do +1
            range(x.start() + 1, x.end())
            for x in preformatted_section_regex.finditer(input_string)
        ]
        input_string = replace_all(
            input_string,
            replacement,
            preformatted_sections,
            newlines,
            document,
            output_format,
        )
    return input_string


def replace_all(
    input_string: str,
    syntax_entry: CustomSyntaxEntry,
    preformatted_sections: list[range],
    newlines: list[Line],
    document: nodes.document,
    output_format: str,
) -> str:
    """
    Call `replace` for each occurrence of `regex` in `text`, and replace it with the return value.
    @param input_string: Input text where matches are replaced
    @param syntax_entry: Syntax entry containing regex and replacement
    @param preformatted_sections: List of ranges that are not to be replaced, like <pre></pre>.
    @param newlines: List with the position of new lines
    @param document: Current nodes document
    @param output_format: The type of document that is built (e.g. html, pdf, ...)
    @return: Text with replaced matches
    """
    pos = 0
    out = ""
    document_path = get_document_source(document)
    for match in syntax_entry.regex.finditer(input_string):
        start = match.start()
        end = match.end()
        if all(start not in section for section in preformatted_sections):
            line_number = [line for line in newlines if line.start_position <= start][-1].number + 1
            out += input_string[pos:start] + syntax_entry.replacement(
                MatchInfo(
                    match=match,
                    line_number=line_number,
                    document=document,
                    document_path=document_path,
                    output_format=output_format,
                )
            )
            pos = end
        else:
            out += input_string[pos:end]
            pos = end
    return out + input_string[pos:]


_newline_pattern = re.compile(r"\n")
