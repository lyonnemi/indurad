import dataclasses
import pathlib
import shutil
import subprocess
import tempfile
from typing import Optional


@dataclasses.dataclass(frozen=True)
class GitRevision:
    commit_sha: str
    commit_describe: Optional[str]


def _resolve_git_reference_sha(
    git_path: str,
    checkout_path: pathlib.Path,
    reference_path: str,
) -> Optional[str]:
    show_ref = subprocess.run(
        [git_path, "-C", str(checkout_path), "rev-parse", reference_path],
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )

    return show_ref.stdout.rstrip("\n") if show_ref.returncode == 0 else None


def _resolve_git_describe(
    git_path: str,
    checkout_path: pathlib.Path,
    commit_sha: str,
) -> Optional[str]:
    describe = subprocess.run(
        [
            git_path,
            "-C",
            str(checkout_path),
            "describe",
            "--match=v*.*",
            commit_sha,
        ],
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )

    return describe.stdout.rstrip("\n") if describe.returncode == 0 else None


def resolve_git_revision(
    git_url: str,
    git_revision: str,
) -> GitRevision:
    with tempfile.TemporaryDirectory() as temp_dir:
        checkout_path = pathlib.Path(temp_dir)

        git_path = shutil.which("git")

        if not git_path:
            raise FileNotFoundError("Could not find git in PATH")

        subprocess.check_call(
            [
                git_path,
                "clone",
                "--quiet",
                git_url,
                str(checkout_path),
            ]
        )

        resolved_branch_revision = _resolve_git_reference_sha(
            git_path=git_path, checkout_path=checkout_path, reference_path=f"refs/remotes/origin/{git_revision}"
        )

        resolved_tag_revision = _resolve_git_reference_sha(
            git_path=git_path, checkout_path=checkout_path, reference_path=f"refs/remotes/origin/{git_revision}"
        )

        commit_sha: str = resolved_branch_revision or resolved_tag_revision or git_revision

        commit_describe = _resolve_git_describe(
            git_path=git_path,
            checkout_path=checkout_path,
            commit_sha=commit_sha,
        )

    return GitRevision(
        commit_sha=commit_sha,
        commit_describe=commit_describe,
    )
