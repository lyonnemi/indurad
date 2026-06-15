"""Generates a target compatibility report"""
import dataclasses
import functools
import json
import logging
import pathlib
import sys
from typing import Tuple, List, Optional, Dict, Set

import jinja2

from toolchain_ci.downstream_pipeline.target_list import ToolchainBuild, BuildTarget

logger = logging.getLogger("compatibility_report")
logger.setLevel(logging.DEBUG)  # creating consistent error messages
handler = logging.StreamHandler(sys.stderr)
handler.setLevel(logging.DEBUG)  # ensure consistency between handler and logger
logger.addHandler(handler)


_TEMPLATES_PATH = pathlib.Path(__file__).parent.parent / "templates"
_BOOTSTRAP_PATH = _TEMPLATES_PATH / "bootstrap.min.css"
_REPORT_TEMPLATE_PATH = _TEMPLATES_PATH / "report_template.html"


@dataclasses.dataclass(frozen=True, order=True)
class ToolchainBuildTarget(BuildTarget):
    target_path: Optional[str] = None

    def as_dict(self) -> Dict:
        base_dict = super().as_dict()
        return base_dict | {"target_path": str(self.target_path)}


@dataclasses.dataclass(frozen=True)
class ToolchainCiConfiguration:
    distro: str
    toolchain_version: str
    platform: str
    cxx: str
    build_state: str
    targets: Tuple[int, ...]

    def as_dict(self) -> Dict:
        return {
            "distro": self.distro,
            "toolchain_version": self.toolchain_version,
            "platform": self.platform,
            "cxx": self.cxx,
            "build_state": self.build_state,
            "targets": self.targets,
        }


@dataclasses.dataclass(frozen=True)
class ToolchainCiReport:
    version: int
    targets: Tuple[ToolchainBuildTarget, ...]
    revision: str
    configurations: Tuple[ToolchainCiConfiguration, ...]

    def as_dict(self) -> Dict:
        return {
            "version": self.version,
            "targets": tuple([target.as_dict() for target in self.targets]),
            "revision": self.revision,
            "configurations": tuple([config.as_dict() for config in self.configurations]),
        }

    def write_json(self, path: pathlib.Path) -> None:
        with path.open("w", encoding="utf-8") as output_file:
            json.dump(self.as_dict(), output_file)


def _toolchain_build_sort_key(toolchain_build: ToolchainBuild) -> Tuple[str, str, str]:
    if toolchain_build.platform == "local":
        return "z", toolchain_build.cxx, toolchain_build.toolchain_version

    return (toolchain_build.platform, toolchain_build.cxx, toolchain_build.toolchain_version)


def _should_include_target_in_report(target: ToolchainBuildTarget) -> bool:
    return target.target_type != "OTHER"


def generate_compatibility_report(
    input_files: List[pathlib.Path],
    output_path: pathlib.Path,
    output_name: str,
    git_url: str,
    commit_link_label: str,
) -> bool:
    revision: Optional[str] = None
    toolchain_builds: List[ToolchainBuild] = []
    failed_builds: List[ToolchainBuild] = []

    for file_path in input_files:
        toolchain_build = ToolchainBuild.read_json(file_path)

        if not revision:
            revision = toolchain_build.revision
        elif revision != toolchain_build.revision:
            raise RuntimeError(
                f'File "{file_path}" reports revision '
                f'"{toolchain_build.revision}". '
                f'But other input files reported revision "{revision}".'
            )

        if toolchain_build.build_state != "SUCCESS":
            failed_builds.append(toolchain_build)

        toolchain_builds.append(toolchain_build)

    sorted_toolchain_builds = sorted(toolchain_builds, key=_toolchain_build_sort_key)

    targets: Set[ToolchainBuildTarget] = functools.reduce(
        lambda x, y: x.union(y),
        [
            set(
                ToolchainBuildTarget(
                    target_path=key,
                    target_type=target.target_type,
                    target_language=target.target_language,
                    library_type=target.library_type,
                )
                for key, target in config.targets.items()
            )
            for config in sorted_toolchain_builds
        ],
        set(),
    )

    def target_sort_key(target: ToolchainBuildTarget) -> str:
        return str(target.target_path)

    sorted_targets = tuple(sorted(filter(_should_include_target_in_report, targets), key=target_sort_key))

    target_index_mapping: Dict[str, int] = {target.target_path: index for index, target in enumerate(sorted_targets)}

    report = ToolchainCiReport(
        version=2,
        targets=sorted_targets,
        revision=revision,
        configurations=tuple(
            ToolchainCiConfiguration(
                distro=build.distro,
                toolchain_version=build.toolchain_version,
                platform=build.platform,
                cxx=build.cxx,
                build_state=build.build_state,
                targets=tuple(
                    target_index_mapping[target] for target in build.targets.keys() if target in target_index_mapping
                ),
            )
            for build in sorted_toolchain_builds
        ),
    )

    report.write_json(output_path / f"{output_name}.json")

    def strip_monolith_prefix(path: str) -> pathlib.Path:
        input_path = pathlib.Path(path)
        monolith_path = pathlib.Path("monolith")
        return input_path.relative_to(monolith_path) if input_path.is_relative_to(monolith_path) else input_path

    html_output_path = output_path / f"{output_name}.html"
    with html_output_path.open("w", encoding="utf-8") as output_file:
        template = jinja2.Template(
            source=_REPORT_TEMPLATE_PATH.read_text(encoding="utf-8"),
            lstrip_blocks=True,
            trim_blocks=True,
            undefined=jinja2.StrictUndefined,
        )

        output_file.write(
            template.render(
                report=report,
                git_url=git_url,
                commit_link_label=commit_link_label,
                strip_monolith_prefix=strip_monolith_prefix,
                bootstrap_css=_BOOTSTRAP_PATH.read_text(encoding="utf-8"),
            )
        )

    if len(failed_builds) > 0:
        logger.error(f"Failed builds: {len(failed_builds)}")
        for failed_build in failed_builds:
            logger.error(f"Toolchain Version: {failed_build.toolchain_version}")
            logger.error(f"Platform: {failed_build.platform}")
            logger.error(f"CXX: {failed_build.cxx}")
            logger.error(f"URL: {failed_build.job_url}")
            logger.error(f"Build status:{failed_build.build_state}")
            logger.error("------------------------------------")
        return False
    else:
        return True

    # return all(build.build_state == "SUCCESS" for build in toolchain_builds)
