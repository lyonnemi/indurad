import pathlib
import unittest
from typing import Generator
from indurad_ci.build_sphinx_pages.private.repo_structure import GitRepo
from indurad_ci.build_sphinx_pages.private.sphinx_log_parser import SphinxLogParser
from indurad_ci.build_sphinx_pages.private.sphinx_build_config import (
    OutputFormat,
    SphinxBuildConfig,
    ChapterStart,
    PageNumberPosition,
)
from indurad_ci.codeclimate_conversion import (
    CodeClimateError,
    CodeClimateSeverity,
)

_CURRENT_PATH = pathlib.Path(__file__).parent


def generate_log() -> Generator[str, None, None]:
    for line in (_CURRENT_PATH / "example_codequality_report/warn.log").read_text().split("\n"):
        yield line + "\n"


class TestSphinxReport(unittest.TestCase):
    def test_generate_codequality_report(self) -> None:
        basic_config = SphinxBuildConfig(
            working_dir_path=pathlib.Path("/foo/bar/my_repo"),
            project_name="",
            output_format=OutputFormat.HTML,
            _build_tags=("indurad",),
            author="",
            email="",
            document_version="",
            watermark_text="",
            watermark_scale=1,
            source_path=pathlib.Path("/foo/bar/my_repo/source"),
            source_repo_path=pathlib.Path("/foo/bar/my_repo"),
            include_paths=(),
            exclude_paths=(),
            suppress_issues=(
                "this warning is suppressed",
                "this warning is also suppressed",
            ),
            warnings_as_errors=False,
            _custom_requirements=(),
            _autodoc_source_paths=(),
            build_target="default_target",
            config_path=pathlib.Path(),
            entry_point="",
            debug=False,
            kicker="",
            subheading="",
            logo_paths=(),
            insert_disclaimer=True,
            repo_structure=(
                GitRepo(
                    file_system_path=pathlib.Path("/foo/bar/my_repo"),
                    relative_file_system_path=pathlib.Path("."),
                    branch="master",
                    url="https://git.foo.bar/my_repo",
                    relative_url="",
                ),
                GitRepo(
                    file_system_path=pathlib.Path("/foo/bar/my_repo/source/my_submodule"),
                    relative_file_system_path=pathlib.Path("source/my_submodule"),
                    branch="master",
                    url="https://git.foo.bar/my_submodule",
                    relative_url="../my_submodule",
                ),
            ),
            document_date="",
            chapterstart=ChapterStart.OPENANY,
            even_page_num_pos=PageNumberPosition.R,
            odd_page_num_pos=PageNumberPosition.R,
        )

        with self.assertLogs():
            codeclimate_issues = (
                SphinxLogParser(config=basic_config, header_offset=0, tags_used=True).parse_log(generate_log()).errors
            )

        expected_issues = (
            CodeClimateError(
                description="[default_target] docstring of some_module.something: "
                "Inline emphasis start-string without end-string.",
                severity=CodeClimateSeverity.minor,
                filepath=pathlib.Path("/foo/bar/my_repo/baz/module.py"),
                line=1,
                fingerprint="022b9c932dad14e3464954e02e5dd0e73d8af60d74091f8313531959d22faa38",
            ),
            CodeClimateError(
                description="[default_target] duplicate label something",
                severity=CodeClimateSeverity.critical,
                filepath=pathlib.Path("some/dir/README.md"),
                line=772,
                fingerprint="65a2b985ab69e93de694352285b7ec397f163e49a190459138e7df5455ed2f23",
            ),
            CodeClimateError(
                description="[default_target] At least one body element must separate transitions; "
                "adjacent transitions are not allowed.",
                severity=CodeClimateSeverity.major,
                filepath=pathlib.Path("something.md"),
                line=10,
                fingerprint="bbb562a939d6de1941b92749f281d35f2f4eabc00bdb1f7965bd4541c202e267",
            ),
            CodeClimateError(
                description="[default_target] Document headings start at H3, not H1 [myst.header]",
                severity=CodeClimateSeverity.minor,
                filepath=pathlib.Path("../../../../my_submodule/-/tree/master/some/other/dir/README.md"),
                line=5,
                fingerprint="bd34998d04d053f6854935b81f9556641fe8ca38b610029f62bfc73d58d89bda",
            ),
            CodeClimateError(
                description="[default_target] Document may not end with a transition.",
                severity=CodeClimateSeverity.major,
                filepath=pathlib.Path("main.md"),
                line=107,
                fingerprint="11c2e9cf68d4f9c82851f2ee92c0c8ea55968b37f2e9fd9f1d263c88addedfbf",
            ),
            CodeClimateError(
                description='[default_target] Problems with "include" directive path',
                severity=CodeClimateSeverity.blocker,
                filepath=pathlib.Path("foobar/index.rst"),
                line=3,
                fingerprint="5bdccf77a303d132c4f6e3136553fe57e66a73713206cee4d16e8b2d766f3dcc",
            ),
            CodeClimateError(
                description="[default_target] InputError: [Errno 2] Datei oder Verzeichnis nicht gefunden: "
                "'foobar.rst'.",
                severity=CodeClimateSeverity.major,
                filepath=pathlib.Path("."),
                line=1,
                fingerprint="f197754b81116c60e7b8015cf40749b5bda86790d03c02c462b672202e81468a",
            ),
            CodeClimateError(
                description="[default_target] command 'mmdc' cannot be run (needed for mermaid output), "
                "check the mermaid_cmd setting",
                severity=CodeClimateSeverity.minor,
                filepath=pathlib.Path("."),
                line=1,
                fingerprint="8d259585048a4c9f973789551075def0fb2298d755836daef770e0c42c27ecfc",
            ),
            CodeClimateError(
                description="[default_target] this line : is not dropped",
                severity=CodeClimateSeverity.major,
                filepath=pathlib.Path("."),
                line=1,
                fingerprint="20d306663c32495ccaed91994c69ed2ff33b19884647755ebf50817d54880443",
            ),
            CodeClimateError(
                description="[default_target] Sphinx error",
                severity=CodeClimateSeverity.major,
                filepath=pathlib.Path("."),
                line=1,
                fingerprint="107aaf229bc21879c77d6ed349c448d9aaa12fd866165a1243b3463eda3758aa",
            ),
        )

        codeclimate_actual_str = (
            str(codeclimate_issues)
            .replace("<CodeClimateSeverity", "CodeClimateSeverity")
            .replace(": 'major'>", "")
            .replace(": 'minor'>", "")
            .replace(": 'blocker'>", "")
            .replace(": 'critical'>", "")
            .replace("PosixPath", "pathlib.Path")
        )
        self.assertTupleEqual(
            codeclimate_issues,
            expected_issues,
            f"The actual report is:\n{codeclimate_actual_str}",
        )
