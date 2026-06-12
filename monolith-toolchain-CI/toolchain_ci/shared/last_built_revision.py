"""
1. Marks the current monolith revision as already built
2. Checks if the current monolith revision was already built

The monolith revision check can be overridden by setting the environment
variable TOOLCHAIN_CI_FORCE_REBUILD = true.

Creates/reads ./monolith_already_built_flag, which is cached by GitLab CI
"""
import os
import pathlib

_ROOT_PATH = pathlib.Path(__file__).parent.parent.parent
_LAST_BUILT_PATH = _ROOT_PATH / "monolith_already_built_flag"


def was_revision_already_built() -> bool:
    if os.environ.get("TOOLCHAIN_CI_FORCE_REBUILD", "false") == "true":
        return False

    return _LAST_BUILT_PATH.exists()


def get_last_successful_pipeline_url() -> str:
    with open(_LAST_BUILT_PATH, "r") as f:
        return f.read()


def mark_as_already_built() -> None:
    # mark current pipeline as being a successful build by creating a flag
    # file that we can store in a GitLab cache
    # we also use this file to store a link to the pipeline which can be
    # printed in every successive pipeline run, so we can browse the results
    # of the original pipeline
    with open(_LAST_BUILT_PATH, "w") as f:
        f.write(os.environ.get("CI_PIPELINE_URL", ""))
