import argparse
import logging
import os
import pathlib
import sys
from toolchain_ci.shared import last_built_revision
from .private.report import generate_compatibility_report

logger = logging.getLogger("compatibility_report")


def _main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generates a compatibility report "
            "from the output of target_list.py."
            "Outputs a JSON file for archival purposes "
            "and a human readable HTML report."
        )
    )
    parser.parse_args()

    input_files = list(pathlib.Path().glob("target-list.*.json"))
    monolith_revision = os.environ["TOOLCHAIN_CI_MONOLITH_REVISION"]
    commit_link_label = os.environ["TOOLCHAIN_CI_MONOLITH_DESCRIBE"]
    monolith_project = os.environ["TOOLCHAIN_CI_MONOLITH_PROJECT"]
    git_url = f'{os.environ["CI_SERVER_URL"]}/' f"{monolith_project}/-/commit/" f"{monolith_revision}"
    pipeline_success = generate_compatibility_report(
        input_files=input_files,
        output_name="TargetCompatibility",
        output_path=pathlib.Path(),
        git_url=git_url,
        commit_link_label=commit_link_label,
    )

    if not pipeline_success:
        logger.error(
            "ERROR: Failed to generate compatibility report: Some jobs failed"
        )  # log the error directly into console
        sys.exit(1)

    last_built_revision.mark_as_already_built()


if __name__ == "__main__":
    _main()
