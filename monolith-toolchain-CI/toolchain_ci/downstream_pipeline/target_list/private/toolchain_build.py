import dataclasses
import json
import os
import pathlib
from typing import Dict, Optional

from .build_target import BuildTarget


@dataclasses.dataclass(frozen=True)
class ToolchainBuild:
    """Result of a single toolchain build"""

    version: int
    distro: str
    toolchain_version: str
    revision: str
    platform: str
    cxx: str
    build_state: str
    targets: Dict[str, BuildTarget]
    job_url: str

    def as_dict(self) -> Dict:
        result = self.__dict__
        result["targets"] = [
            [key, target.target_type]
            + ([target.library_type] if target.target_type == "LIBRARY" else [])
            + ([target.target_language] if target.target_type in ["LIBRARY", "EXECUTABLE"] else [])
            for key, target in self.targets.items()
        ]
        return result

    @staticmethod
    def from_dict(data: Dict) -> "ToolchainBuild":
        return ToolchainBuild(
            version=data["version"],
            distro=data["distro"],
            toolchain_version=data["toolchain_version"],
            revision=data["revision"],
            platform=data["platform"],
            cxx=data["cxx"],
            build_state=data["build_state"],
            targets={
                target[0]: BuildTarget(
                    target_type=target[1],
                    target_language=target[2] if len(target) > 2 else "OTHER",
                    library_type=target[3] if len(target) > 3 else None,
                )
                for target in data["targets"]
            },
            job_url=os.environ.get("CI_JOB_URL"),
        )

    def write_json(self, path: pathlib.Path) -> None:
        with path.open("w", encoding="utf-8") as output_file:
            json.dump(self.as_dict(), output_file)

    @staticmethod
    def read_json(path: pathlib.Path) -> Optional["ToolchainBuild"]:
        with path.open("r", encoding="utf-8") as input_file:
            return ToolchainBuild.from_dict(json.load(input_file))
