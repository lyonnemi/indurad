import dataclasses
import shutil
import subprocess
import tempfile
import unittest

from ..private.resolve_revision import resolve_git_revision

_GIT_PATH = shutil.which("git")


@dataclasses.dataclass(frozen=True)
class GitRepository:
    def cleanup(self):
        self.repo_directory.cleanup()

    repo_directory: tempfile.TemporaryDirectory

    def git(self, *command_line: str) -> str:
        return subprocess.check_output(
            (
                str(_GIT_PATH),
                "-C",
                str(self.repo_directory.name),
            )
            + command_line,
            encoding="utf-8",
        ).rstrip("\n")

    def add_commit(self):
        subprocess.check_call(
            [
                str(_GIT_PATH),
                "-C",
                str(self.repo_directory.name),
                "commit",
                "--allow-empty",
                "-m",
                "test",
            ]
        )

    @staticmethod
    def init() -> "GitRepository":
        repo_directory = tempfile.TemporaryDirectory()
        subprocess.check_call([str(_GIT_PATH), "init", str(repo_directory.name)])
        subprocess.check_call(
            [
                str(_GIT_PATH),
                "-C",
                str(repo_directory.name),
                "commit",
                "--allow-empty",
                "-m",
                "test",
            ]
        )
        return GitRepository(
            repo_directory=repo_directory,
        )


class TestResolveRevision(unittest.TestCase):
    upstream_repo: GitRepository

    def setUp(self) -> None:
        self.assertIsNotNone(_GIT_PATH)

        # suppress hints emitted by git
        subprocess.check_call(
            [
                str(_GIT_PATH),
                "config",
                "--global",
                "init.defaultBranch",
                "master",
            ]
        )

        self.upstream_repo = GitRepository.init()

    def tearDown(self) -> None:
        self.upstream_repo.cleanup()

    def test_branch_no_prior_tags(self):
        expected_revision = self.upstream_repo.git("rev-parse", "HEAD")
        self.upstream_repo.git("checkout", "-b", "branch-name", "--quiet")

        revision = resolve_git_revision(git_url=self.upstream_repo.repo_directory.name, git_revision="branch-name")

        self.assertEqual(expected_revision, revision.commit_sha)
        self.assertIsNone(revision.commit_describe)

    def test_commit_no_prior_tags(self):
        expected_revision = self.upstream_repo.git("rev-parse", "HEAD")

        revision = resolve_git_revision(git_url=self.upstream_repo.repo_directory.name, git_revision=expected_revision)

        self.assertEqual(expected_revision, revision.commit_sha)
        self.assertIsNone(revision.commit_describe)

    def test_commit_tagged(self):
        self.upstream_repo.git("tag", "--annotate", "v0.0-test", "-m", "test")
        self.upstream_repo.add_commit()
        expected_revision = self.upstream_repo.git("rev-parse", "HEAD")

        revision = resolve_git_revision(git_url=self.upstream_repo.repo_directory.name, git_revision=expected_revision)

        self.assertEqual(expected_revision, revision.commit_sha)
        self.assertEqual(f"v0.0-test-1-g{expected_revision[0:7]}", revision.commit_describe)

    def test_branch_tagged(self):
        self.upstream_repo.git("tag", "--annotate", "v0.1-test", "-m", "test")
        self.upstream_repo.add_commit()
        self.upstream_repo.git("checkout", "-b", "branch-name", "--quiet")
        expected_revision = self.upstream_repo.git("rev-parse", "HEAD")

        revision = resolve_git_revision(git_url=self.upstream_repo.repo_directory.name, git_revision="branch-name")

        self.assertEqual(expected_revision, revision.commit_sha)
        self.assertEqual(f"v0.1-test-1-g{expected_revision[0:7]}", revision.commit_describe)
