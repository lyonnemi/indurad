"""Determines which monolith commit hash to build ("master" → commit hash)."""
import os
import pathlib
from .private.resolve_revision import resolve_git_revision, GitRevision

_DOTENV_PATH = pathlib.Path(__file__).parent.parent.parent.parent / "resolved_monolith_revision.env"


def _main():
    revision: GitRevision = resolve_git_revision(
        git_url=(f'git@{os.environ["CI_SERVER_HOST"]}:' f'{os.environ["TOOLCHAIN_CI_MONOLITH_PROJECT"]}.git'),
        git_revision=os.environ["TOOLCHAIN_CI_MONOLITH_REVISION"],
    )

    _DOTENV_PATH.write_text(
        f"MONOLITH_COMMIT_SHA="
        f"{revision.commit_sha}\n"
        f"MONOLITH_COMMIT_DESCRIBE="
        f"{revision.commit_describe or revision.commit_sha}"
    )


if __name__ == "__main__":
    _main()
