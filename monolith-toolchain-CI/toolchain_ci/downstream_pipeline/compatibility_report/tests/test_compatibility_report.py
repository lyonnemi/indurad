import pathlib
import tempfile
import unittest
import logging
from ..private.report import generate_compatibility_report

_ASSETS_PATH = pathlib.Path(__file__).parent / "assets"

logger = logging.getLogger("compatibility_report")


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
            with self.assertLogs(logger, logging.INFO) as context:
                generate_compatibility_report(
                    git_url="git_url",
                    output_path=temp_path,
                    output_name="output_name",
                    input_files=input_files,
                    commit_link_label="v10.x-commit-hash",
                )

            full_log = "\n".join(context.output)

            pattern = r".*Toolchain Version: .+\n" r".*Platform: .+\n" r".*CXX: .+\n" r".*URL: .+\n"

            self.assertRegex(full_log, pattern)
