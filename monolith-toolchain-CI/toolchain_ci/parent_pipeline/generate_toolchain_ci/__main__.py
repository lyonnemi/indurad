import dataclasses
import os
import pathlib
import textwrap
from typing import List, Optional, Tuple
import jinja2

from indurad_ci.toolchain.rootfs_toolchain import (
    find_toolchains,
    RootfsToolchain,
    filter_toolchains_by_latest_by_major,
)

from toolchain_ci.shared import last_built_revision

_CURRENT_FILE_PATH = pathlib.Path(__file__).parent
_TEMPLATE_PATH = _CURRENT_FILE_PATH / "templates" / "gitlab-ci.yml"
_OUTPUT_PATH = pathlib.Path("toolchain_ci.yml")


@dataclasses.dataclass(frozen=True)
class ToolchainCiJob:
    platform: str
    cmake_cxx_standard: str
    distro: Optional[str] = None
    toolchain_version: Optional[str] = None
    custom_platform_name: Optional[str] = None
    custom_build_image: Optional[str] = None

    def gitlab_job_name(self) -> str:
        return ", ".join(
            ((self.toolchain_version,) if self.toolchain_version else tuple())
            + (self.custom_platform_name or self.platform, f"C++{self.cmake_cxx_standard}")
        )


def _toolchain_version_or_none(env_text: Optional[str]) -> Optional[RootfsToolchain]:
    if not env_text:
        return None

    return RootfsToolchain.from_string(env_text)


def _main():
    minimum_toolchain_version = _toolchain_version_or_none(os.environ["TOOLCHAIN_CI_MIN_TOOLCHAIN_VERSION"])
    maximum_toolchain_version = _toolchain_version_or_none(os.environ["TOOLCHAIN_CI_MAX_TOOLCHAIN_VERSION"])
    platforms_to_build: Tuple[str, ...] = tuple(os.environ["TOOLCHAIN_CI_PLATFORMS_TO_BUILD"].split())
    monolith_project = os.environ["TOOLCHAIN_CI_MONOLITH_PROJECT"]
    monolith_revision = os.environ["TOOLCHAIN_CI_MONOLITH_REVISION"]
    monolith_commit_sha = os.environ["MONOLITH_COMMIT_SHA"]
    monolith_commit_describe = os.environ["MONOLITH_COMMIT_DESCRIBE"]
    cmake_cxx_standards: Tuple[str, ...] = tuple(os.environ["TOOLCHAIN_CI_CXX_VERSIONS"].split())

    print(
        "\u001b[33m",  # yellow text
        "\u001b[1m",  # bold text
        textwrap.dedent(
            f"""
            TOOLCHAIN_CI_MONOLITH_PROJECT      {monolith_project}
            TOOLCHAIN_CI_MONOLITH_REVISION     {monolith_revision}
            MONOLITH_COMMIT_SHA                {monolith_commit_sha}
            MONOLITH_COMMIT_DESCRIBE           {monolith_commit_describe}
            TOOLCHAIN_CI_MIN_TOOLCHAIN_VERSION {minimum_toolchain_version}
            TOOLCHAIN_CI_MAX_TOOLCHAIN_VERSION {maximum_toolchain_version}
            TOOLCHAIN_CI_PLATFORMS_TO_BUILD    {", ".join(platforms_to_build)}
            TOOLCHAIN_CI_CXX_VERSIONS          {", ".join(cmake_cxx_standards)}
            """
        ),
        "\u001b[0m",  # reset text color
        sep="",
    )

    already_built = last_built_revision.was_revision_already_built()
    if already_built:
        print(
            f"Revision {monolith_commit_sha} from the configured remote was "
            "already built with this revision of the toolchain CI.\n"
            "Skipping this build.\n"
            "Find details on the last successful pipline here:\n"
            "\u001b[33m"  # yellow text
            f"{last_built_revision.get_last_successful_pipeline_url()}"
            "\u001b[1m"  # bold text
            "\u001b[0m"  # reset text color
        )

    ci_template = jinja2.Template(
        source=_TEMPLATE_PATH.read_text(encoding="utf-8"),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    toolchain_ci_jobs: List[ToolchainCiJob] = []

    for platform in platforms_to_build:
        if platform == "local":
            # default build environment (currently Debian 12)
            for cmake_cxx_standard in cmake_cxx_standards:
                toolchain_ci_jobs.append(
                    ToolchainCiJob(
                        platform="local",
                        custom_platform_name="Debian 12",
                        cmake_cxx_standard=cmake_cxx_standard,
                    )
                )
            continue

        rootfs_toolchains: List[RootfsToolchain] = find_toolchains(
            platform=platform,
            min_version=minimum_toolchain_version,
            max_version=maximum_toolchain_version,
        )
        filtered_toolchains: List[RootfsToolchain] = filter_toolchains_by_latest_by_major(rootfs_toolchains)
        for rootfs_toolchain in filtered_toolchains:
            for cmake_cxx_standard in cmake_cxx_standards:
                toolchain_ci_jobs.append(
                    ToolchainCiJob(
                        distro="icharlie",
                        platform=platform,
                        toolchain_version=rootfs_toolchain.version,
                        cmake_cxx_standard=cmake_cxx_standard,
                    )
                )

    reduce_toolchain_ci_jobs = os.environ["CI_PIPELINE_SOURCE"] in {
        "push",
        "merge_request_event",
    }
    _OUTPUT_PATH.write_text(
        ci_template.render(
            monolith_revision=monolith_commit_sha,
            monolith_describe=monolith_commit_describe,
            monolith_project=monolith_project,
            toolchain_ci_jobs=(
                # Only build two jobs for merge-request- and push-events.
                # Select the first and last job for maximum variety.
                [toolchain_ci_jobs[0], toolchain_ci_jobs[-1]]
                if reduce_toolchain_ci_jobs
                else toolchain_ci_jobs
            ),
            already_built=already_built,
            platforms_to_build=" ".join(platforms_to_build),
            min_toolchain_version=minimum_toolchain_version or "",
            max_toolchain_version=maximum_toolchain_version or "",
            cxx_versions=" ".join(cmake_cxx_standards),
        )
    )


if __name__ == "__main__":
    _main()
