import logging
import pathlib
import tempfile
import unittest
from ..private.report import generate_compatibility_report

_ASSETS_PATH = pathlib.Path(__file__).parent / "assets"

logger = logging.getLogger("compatibility_report")

_FAILED_JOB_URL = "https://gitlab.example.test/monolith/-/jobs/failed-job-a"
_FAILED_JOB_B_URL = "https://gitlab.example.test/monolith/-/jobs/failed-job-b"


class TestCompatibilityReport(unittest.TestCase):
    def test_write_report(self):
        input_files = [_ASSETS_PATH / "wrong-revision-a.json"]
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            generate_compatibility_report(
                git_url="https://git.indurad.x/master/test",
                output_path=temp_path,
                output_name="output_name",
                input_files=input_files,
                commit_link_label="v10.x-commit-hash",
            )

    def test_wrong_version(self):
        input_files = [_ASSETS_PATH / "wrong-revision-a.json", _ASSETS_PATH / "wrong-revision-b.json"]
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            with self.assertRaises(RuntimeError) as context:
                generate_compatibility_report(
                    git_url="git_url",
                    output_path=temp_path,
                    output_name="output_name",
                    input_files=input_files,
                    commit_link_label="v10.x-commit-hash",
                )
        self.assertEqual(
            f'File "{input_files[1]}" reports revision '
            '"not-the-same-revision". '
            f'But other input files reported revision "0a123fd12c".',
            context.exception.args[0],
        )

    def test_error_message(self):
        input_files = [
            _ASSETS_PATH / "failed-job.json",
            _ASSETS_PATH / "wrong-revision-a.json",
            _ASSETS_PATH / "failed-job-b.json",
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = pathlib.Path(temp_dir)
            with self.assertLogs(logger, logging.ERROR) as context:
                pipeline_success = generate_compatibility_report(
                    git_url="git_url",
                    output_path=temp_path,
                    output_name="output_name",
                    input_files=input_files,
                    commit_link_label="v10.x-commit-hash",
                )

            self.assertFalse(pipeline_success)

            expected_log_lines = [
                "ERROR:compatibility_report:Failed builds: 2",
                "ERROR:compatibility_report:Toolchain Version: 12.0.1",
                "ERROR:compatibility_report:Platform: ct20",
                "ERROR:compatibility_report:CXX: 98",
                f"ERROR:compatibility_report:URL: {_FAILED_JOB_URL}",
                "ERROR:compatibility_report:Build status:FAILURE",
                "ERROR:compatibility_report:------------------------------------",
                "ERROR:compatibility_report:Toolchain Version: 12.0.1",
                "ERROR:compatibility_report:Platform: ct20",
                "ERROR:compatibility_report:CXX: 98",
                f"ERROR:compatibility_report:URL: {_FAILED_JOB_B_URL}",
                "ERROR:compatibility_report:Build status:FAILURE",
                "ERROR:compatibility_report:------------------------------------",
            ]
            self.assertEqual(expected_log_lines, context.output)
