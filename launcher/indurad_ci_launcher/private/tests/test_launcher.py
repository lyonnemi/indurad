import io
import pathlib
import shutil
import tempfile
import unittest
from unittest.mock import patch

from indurad_ci_launcher.private import launcher

_CURRENT_PATH = pathlib.Path(__file__).parent
_TEST_GITLAB_CI_PATH = _CURRENT_PATH / "assets" / "gitlab-ci-template.yml"
_BUILDJOB_PATH = _CURRENT_PATH / "fake_buildjob.py"


def _create_empty_commit(
    checkout_path: pathlib.Path,
) -> str:
    launcher.run_git(
        [
            "-C",
            str(checkout_path),
            "commit",
            "--message",
            "test",
            "--allow-empty",
            "--no-verify",
        ]
    )
    return _checked_out_revision(checkout_path=checkout_path)


def _checked_out_revision(checkout_path: pathlib.Path) -> str:
    return launcher.run_git(
        [
            "-C",
            str(checkout_path),
            "rev-parse",
            "HEAD",
        ]
    ).stdout.rstrip("\n")


def _checkout_branch(checkout_path: pathlib.Path, branch_name: str) -> None:
    launcher.run_git(
        [
            "-C",
            str(checkout_path),
            "checkout",
            "-b",
            branch_name,
        ]
    )


def _setup_fake_git_remote(remote_path: pathlib.Path) -> str:
    for command in (
        [
            "init",
            "--initial-branch=master",
            str(remote_path),
        ],
        [
            "-C",
            str(remote_path),
            "commit",
            "--message",
            "initial commit",
            "--allow-empty",
        ],
    ):
        launcher.run_git(command_line=command, check=True)

    return launcher.run_git(
        [
            "-C",
            str(remote_path),
            "rev-parse",
            "HEAD",
        ]
    ).stdout.rstrip("\n")


class TestLauncher(unittest.TestCase):
    remote_repo_temp_dir: tempfile.TemporaryDirectory[str]
    local_checkout_temp_dir: tempfile.TemporaryDirectory[str]
    local_checkout_path: pathlib.Path

    def setUp(self) -> None:
        self.remote_repo_temp_dir = tempfile.TemporaryDirectory()
        self.local_checkout_temp_dir = tempfile.TemporaryDirectory()
        self.local_checkout_path = pathlib.Path(self.local_checkout_temp_dir.name)
        self.remote_url = self.remote_repo_temp_dir.name
        self.remote_checkout_path = pathlib.Path(self.remote_url)

        self.remote_revision = _setup_fake_git_remote(remote_path=self.remote_checkout_path)
        self._generate_gitlab_ci_yml(indurad_ci_revision=self.remote_revision)
        shutil.copy(
            src=_BUILDJOB_PATH,
            dst=self.local_checkout_path / _BUILDJOB_PATH.name,
        )

    def _generate_gitlab_ci_yml(self, indurad_ci_revision: str) -> None:
        (self.local_checkout_path / ".gitlab-ci.yml").write_bytes(
            _TEST_GITLAB_CI_PATH.read_bytes().replace(
                b"$INDURAD_CI_LAUNCHER_TEST_SHA",
                indurad_ci_revision.encode("utf-8"),
            )
        )

    def tearDown(self) -> None:
        self.remote_repo_temp_dir.cleanup()
        self.local_checkout_temp_dir.cleanup()

    def _run_launcher(self, command_line: list[str]) -> None:
        exit_code = launcher.entry_point(
            arguments=command_line,
            working_directory=self.local_checkout_path,
            clone_remote_override=self.remote_url,
        )
        self.assertEqual(0, exit_code)

    @patch("sys.stdout", new=io.StringIO)
    def test_clone(self) -> None:
        exit_code = launcher.entry_point(
            arguments=["--clone"],
            working_directory=self.local_checkout_path,
            clone_remote_override=self.remote_url,
        )
        self.assertEqual(0, exit_code)

        checkout_path = self.local_checkout_path / ".indurad-ci"
        self.assertTrue(checkout_path.is_dir())
        self.assertEqual(
            _checked_out_revision(
                checkout_path=checkout_path,
            ),
            self.remote_revision,
        )

        remote_revision = _checked_out_revision(
            checkout_path=self.remote_checkout_path,
        )
        local_revision = _checked_out_revision(
            checkout_path=self.remote_checkout_path,
        )
        self.assertEqual(remote_revision, local_revision)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_source(self, stdout: io.StringIO) -> None:
        self._run_launcher(["--source"])
        output = stdout.getvalue()
        self.assertIn("export PYTHONPATH=", output)
        self.assertIn(str(self.local_checkout_path), output)

    @patch("sys.stdout", new=io.StringIO())
    def test_default_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = pathlib.Path(temp_dir) / "output"
            self._run_launcher(["fake_buildjob", str(output_file)])

            python_path = output_file.read_text(encoding="utf-8")
            self.assertIn(str(self.local_checkout_path), python_path)

    @patch("sys.stdout", new=io.StringIO())
    def test_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = pathlib.Path(temp_dir) / "output"
            self._run_launcher(["--run", f"python3 -m fake_buildjob {output_file}"])

            python_path = output_file.read_text(encoding="utf-8")
            self.assertIn(str(self.local_checkout_path), python_path)

    @patch("sys.stdout", new=io.StringIO())
    def test_change_revision_sha(self) -> None:
        self._run_launcher(["--clone"])

        launcher.run_git(
            [
                "-C",
                str(self.remote_checkout_path),
                "commit",
                "--message",
                "test",
                "--allow-empty",
                "--no-verify",
            ]
        )
        self.remote_revision = _checked_out_revision(
            checkout_path=self.remote_checkout_path,
        )
        self._generate_gitlab_ci_yml(indurad_ci_revision=self.remote_revision)

        self._run_launcher(["--clone"])

        local_revision = _checked_out_revision(
            checkout_path=self.local_checkout_path / ".indurad-ci",
        )
        self.assertEqual(self.remote_revision, local_revision)

    @patch("sys.stdout", new=io.StringIO())
    def test_branch_reference(self) -> None:
        _checkout_branch(
            self.remote_checkout_path,
            branch_name="test_branch",
        )
        self._generate_gitlab_ci_yml(indurad_ci_revision="test_branch")
        self._run_launcher(["--clone"])

        local_revision = _checked_out_revision(
            checkout_path=self.local_checkout_path / ".indurad-ci",
        )
        self.assertEqual(self.remote_revision, local_revision)

        # now we change the remote branch revision to test
        # if the launcher updates the local branch revision automatically

        self.remote_revision = _create_empty_commit(checkout_path=self.remote_checkout_path)
        self._run_launcher(["--clone"])

        local_revision = _checked_out_revision(
            checkout_path=self.local_checkout_path / ".indurad-ci",
        )
        self.assertEqual(self.remote_revision, local_revision)
