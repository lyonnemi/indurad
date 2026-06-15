import os
import pathlib
import unittest

from indurad_ci.build_sphinx_pages import SphinxBuildConfig
from indurad_ci.build_sphinx_pages.private.sphinx_build_config import (
    OutputFormat,
    ChapterStart,
    PageNumberPosition,
)
from indurad_ci.build_sphinx_pages.private.latex_build import LatexOutputFilter
from indurad_ci.codeclimate_conversion import CodeClimateSeverity, CodeClimateError

_CURRENT_PATH = pathlib.Path(__file__).parent
_TEX_FILE_PATH = _CURRENT_PATH / ("latex_log_parser/example.tex")
_LOG_CONTENT = (_CURRENT_PATH / "latex_log_parser/example.log").read_text().split("\n")


class TestLatexOutputFilter(unittest.TestCase):
    basic_config = SphinxBuildConfig(
        working_dir_path=pathlib.Path("/foo/bar"),
        project_name="",
        output_format=OutputFormat.PDF,
        _build_tags=("indurad",),
        author="",
        email="",
        document_version="",
        watermark_text="",
        watermark_scale=1,
        source_path=pathlib.Path(),
        source_repo_path=pathlib.Path(),
        include_paths=(),
        exclude_paths=(),
        suppress_issues=(
            "Forbidden token `suppress_this` in Chapter `Third Chapter`, "
            "near the following lines: `line 78`, `line 79`, `line 80`, `line 81`, `line 82`",
        ),
        warnings_as_errors=False,
        _custom_requirements=(),
        _autodoc_source_paths=(),
        debug=False,
        build_target="my_doc",
        config_path=pathlib.Path(),
        entry_point="",
        kicker="",
        subheading="",
        logo_paths=(),
        repo_structure=(),
        insert_disclaimer=True,
        document_date="",
        chapterstart=ChapterStart.OPENANY,
        even_page_num_pos=PageNumberPosition.R,
        odd_page_num_pos=PageNumberPosition.R,
    )

    def test_generate_codequality_report(self) -> None:
        output_filter = LatexOutputFilter(tex_file_path=_TEX_FILE_PATH, config=self.basic_config, tags_used=True)
        with self.assertLogs():
            for line in _LOG_CONTENT:
                output_filter.process_stdout(line + "\n")
            output_filter.end_preprocessing()
            for line in _LOG_CONTENT:
                output_filter.process_stdout(line + "\n")

        job_id = os.environ.get("CI_JOB_ID", "<job_id>")

        expected_issues = [
            CodeClimateError(
                description="[my_doc] Unknown issue: `This issue is not yet known.` "
                "somewhere in Chapter `Second Chapter`. "
                "Please notify DevOps about this issue, for example in the `02 DevOps public` zulip channel.",
                severity=CodeClimateSeverity.minor,
                filepath=pathlib.Path(f"../../../-/jobs/{job_id}"),
                line=0,
                fingerprint="f6aca8ce269ca8ab081080481311e2dda1804fa2417dd6c5197e7c40955e4689",
            ),
            CodeClimateError(
                description="[my_doc] Empty link in Chapter `First Chapter`, "
                "near the following lines: `line 28`, `line 29`, `line 30`, `line 31`, `line 32`",
                severity=CodeClimateSeverity.minor,
                filepath=pathlib.Path(f"../../../-/jobs/{job_id}"),
                line=0,
                fingerprint="fbf116041ed52bea657c8012c57a9eb13beabf14600b5b100d76d5f69f78a2da",
            ),
            CodeClimateError(
                description="[my_doc] Unknown character `한` (U+D55C) (2x) somewhere in Chapter `Second Chapter`.",
                severity=CodeClimateSeverity.major,
                filepath=pathlib.Path(f"../../../-/jobs/{job_id}"),
                line=0,
                fingerprint="2f24fae2d70545f28b06d5f1d3eda95fb8e6664f0095adc4ffebfc693ff2e9bb",
            ),
            CodeClimateError(
                description="[my_doc] Unknown character `글` (U+AE00) (2x) somewhere in Chapter `Second Chapter`.",
                severity=CodeClimateSeverity.major,
                filepath=pathlib.Path(f"../../../-/jobs/{job_id}"),
                line=0,
                fingerprint="5245297a4bcbc8a291ddb0e9a2dab5c4b4e9a7ff30e804abf072b93cfed94474",
            ),
            CodeClimateError(
                description="[my_doc] Image img/wrong_indurad_logo.png not found in Chapter `First Chapter`, "
                "near the following lines: `line 40`, `line 41`, `line 42`, `line 43`, `line 44`",
                severity=CodeClimateSeverity.blocker,
                filepath=pathlib.Path(f"../../../-/jobs/{job_id}"),
                line=0,
                fingerprint="cde254977e56557262cad05a2554e36c90e7305c92f99991af18b52e6813291a",
            ),
            CodeClimateError(
                description="[my_doc] Unknown issue: `This issue is not yet known.` "
                "somewhere in Chapter `Second Chapter`. "
                "Please notify DevOps about this issue, for example in the `02 DevOps public` zulip channel.",
                severity=CodeClimateSeverity.minor,
                filepath=pathlib.Path(f"../../../-/jobs/{job_id}"),
                line=0,
                fingerprint="f6aca8ce269ca8ab081080481311e2dda1804fa2417dd6c5197e7c40955e4689",
            ),
            CodeClimateError(
                description="[my_doc] Horizontal Overflow (2x) (2.4845pt, 2.12345pt) in Chapter `Second Chapter`, "
                "near the following lines: `line 48`, `line 49`, `Second Chapter`, `line 51`, `line 52`",
                severity=CodeClimateSeverity.minor,
                filepath=pathlib.Path(f"../../../-/jobs/{job_id}"),
                line=0,
                fingerprint="939dc6ba71493965b2d56380b3e789b54ac2e44357014583a2c70efac4ddc758",
            ),
            CodeClimateError(
                description="[my_doc] Vertical Overflow (2.34567pt) in Chapter `Third Chapter`, "
                "near the following lines: `line 73`, `line 74`, `Third Chapter`, `line 76`, `line 77`",
                severity=CodeClimateSeverity.minor,
                filepath=pathlib.Path(f"../../../-/jobs/{job_id}"),
                line=0,
                fingerprint="aa5260efc5bba0cde7b1cc8c07a8c23832f4c817def3827c1779fe1417d223ce",
            ),
            CodeClimateError(
                description="[my_doc] Horizontal Overflow (3.14159pt) in Chapter `Fourth Chapter`, "
                "near the following lines: `line 112`, `line 113`, `line 114`, `line 115`, `line 116`",
                severity=CodeClimateSeverity.major,
                filepath=pathlib.Path(f"../../../-/jobs/{job_id}"),
                line=0,
                fingerprint="e80ad175e33315b7c8fce274c01c7fb2ed2b0041d1345a2616bbfec64386fbc6",
            ),
            CodeClimateError(
                description="[my_doc] Forbidden token `bad_token` in Chapter `Third Chapter`, "
                "near the following lines: `line 78`, `line 79`, `line 80`, `line 81`, `line 82`",
                severity=CodeClimateSeverity.minor,
                filepath=pathlib.Path(f"../../../-/jobs/{job_id}"),
                line=0,
                fingerprint="3e46f1a61ee24756cc76d949f15651ce52d93f36872ce9b636f57c3162a8eeed",
            ),
        ]

        codeclimate_actual_str = (
            str(output_filter.codeclimate_issues)
            .replace("<CodeClimateSeverity", "CodeClimateSeverity")
            .replace(": 'major'>", "")
            .replace(": 'minor'>", "")
            .replace(": 'blocker'>", "")
            .replace(": 'critial'>", "")
            .replace("PosixPath", "pathlib.Path")
            .replace("<job_id>", "{job_id}")
            .replace("'../", "f'../")
        )
        self.assertListEqual(
            output_filter.codeclimate_issues,
            expected_issues,
            f"The actual report is:\n{codeclimate_actual_str}",
        )
